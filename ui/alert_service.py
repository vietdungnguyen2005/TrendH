"""
Alert Service for Trend Hunter (Milestone 6)
Send alerts via Telegram for high-confidence flags
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Optional
import requests
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db_utils import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramAlerter:
    """Send alerts via Telegram Bot"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram alerter
        
        Args:
            bot_token: Telegram bot token (or read from .env)
            chat_id: Telegram chat ID (or read from .env)
        """
        self.bot_token = bot_token or self._load_from_env('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or self._load_from_env('TELEGRAM_CHAT_ID')
        
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram alerts disabled: bot_token or chat_id not configured")
    
    def _load_from_env(self, key: str) -> Optional[str]:
        """Load value from .env file"""
        try:
            env_path = Path('.env')
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith(key):
                            return line.split('=', 1)[1].strip()
        except Exception as e:
            logger.error(f"Error loading {key} from .env: {e}")
        
        return None
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Send message via Telegram
        
        Args:
            text: Message text (supports HTML formatting)
            parse_mode: Telegram parse mode (HTML, Markdown)
        
        Returns:
            True if successful
        """
        if not self.enabled:
            logger.info(f"[MOCK] Telegram alert: {text}")
            return True
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram alert sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def format_flag_alert(self, flag: Dict) -> str:
        """
        Format flag data as alert message
        
        Args:
            flag: Flag dictionary
        
        Returns:
            Formatted HTML message
        """
        # Emoji for labels
        label_emoji = {
            'Breakout': '🔥',
            'Hidden Gem': '💎',
            'Rising': '📈',
            'Stable': '⚖️',
            'Dying': '📉'
        }
        
        emoji = label_emoji.get(flag['label'], '🎯')
        
        message = f"""
<b>{emoji} TREND ALERT: {flag['term']}</b>

<b>Label:</b> {flag['label']}
<b>Score:</b> {flag['score']:.1f}/100
<b>Confidence:</b> {flag['confidence']:.0%}

<b>Reasons:</b>
{flag['reason_codes']}

<b>First Seen:</b> {flag['first_seen']}
<b>Flagged:</b> {flag['flagged_at']}

🔗 Check dashboard for details
        """.strip()
        
        return message


class AlertService:
    """Main alert service coordinating different alert channels"""
    
    def __init__(self, 
                 confidence_threshold: float = 0.7,
                 score_threshold: float = 70.0):
        """
        Initialize alert service
        
        Args:
            confidence_threshold: Minimum confidence to trigger alert
            score_threshold: Minimum score to trigger alert
        """
        self.db = get_db()
        self.confidence_threshold = confidence_threshold
        self.score_threshold = score_threshold
        
        # Initialize alerters
        self.telegram = TelegramAlerter()
        
        logger.info(f"Alert service initialized (conf≥{confidence_threshold}, score≥{score_threshold})")
    
    def get_unsent_flags(self) -> List[Dict]:
        """
        Get flags that haven't been alerted yet
        
        Returns:
            List of flag dictionaries
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                # Get flags meeting thresholds that haven't been alerted
                cur.execute('''
                    SELECT 
                        f.id,
                        f.term_id,
                        k.canonical_term,
                        f.trend_score,
                        f.label,
                        f.confidence,
                        f.reason_codes,
                        f.date_time as flagged_at,
                        k.first_seen,
                        f.alert_sent
                    FROM flags f
                    JOIN keywords k ON f.term_id = k.id
                    WHERE f.confidence >= ?
                        AND f.trend_score >= ?
                        AND (f.alert_sent IS NULL OR f.alert_sent = 0)
                    ORDER BY f.trend_score DESC
                ''', (self.confidence_threshold, self.score_threshold))
                
                flags = []
                for row in cur.fetchall():
                    flags.append({
                        'id': row[0],
                        'term_id': row[1],
                        'term': row[2],
                        'score': row[3],
                        'label': row[4],
                        'confidence': row[5],
                        'reason_codes': row[6],
                        'flagged_at': row[7],
                        'first_seen': row[8]
                    })
                
                return flags
        
        except Exception as e:
            logger.error(f"Error getting unsent flags: {e}")
            return []
    
    def mark_as_alerted(self, flag_id: int) -> bool:
        """Mark flag as alerted"""
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                    UPDATE flags 
                    SET alert_sent = 1, 
                        alert_sent_at = ?
                    WHERE id = ?
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), flag_id))
                conn.commit()
            
            return True
        
        except Exception as e:
            logger.error(f"Error marking flag as alerted: {e}")
            return False
    
    def send_alert(self, flag: Dict) -> bool:
        """
        Send alert for a flag
        
        Args:
            flag: Flag dictionary
        
        Returns:
            True if alert sent successfully
        """
        logger.info(f"Sending alert for: {flag['term']} (score={flag['score']:.1f})")
        
        # Format and send Telegram alert
        message = self.telegram.format_flag_alert(flag)
        success = self.telegram.send_message(message)
        
        if success:
            # Mark as alerted
            self.mark_as_alerted(flag['id'])
        
        return success
    
    def process_alerts(self) -> Dict[str, int]:
        """
        Process all pending alerts
        
        Returns:
            Stats dictionary
        """
        stats = {
            'total': 0,
            'sent': 0,
            'failed': 0
        }
        
        # Get unsent flags
        flags = self.get_unsent_flags()
        stats['total'] = len(flags)
        
        if not flags:
            logger.info("No pending alerts")
            return stats
        
        logger.info(f"Processing {stats['total']} pending alerts...")
        
        for flag in flags:
            if self.send_alert(flag):
                stats['sent'] += 1
            else:
                stats['failed'] += 1
        
        logger.info(f"Alerts processed: {stats['sent']} sent, {stats['failed']} failed")
        
        return stats


def main():
    """Run alert service"""
    print("\n" + "="*60)
    print("ALERT SERVICE")
    print("="*60)
    print()
    
    # Initialize service
    service = AlertService(
        confidence_threshold=0.7,
        score_threshold=70.0
    )
    
    print(f"Configuration:")
    print(f"  Confidence threshold: ≥{service.confidence_threshold}")
    print(f"  Score threshold: ≥{service.score_threshold}")
    print(f"  Telegram enabled: {service.telegram.enabled}")
    print()
    
    # Process alerts
    stats = service.process_alerts()
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Total pending:  {stats['total']}")
    print(f"Sent:           {stats['sent']}")
    print(f"Failed:         {stats['failed']}")
    print()
    
    if stats['total'] == 0:
        print("No flags meeting alert criteria.")
        print()
        print("To trigger alerts:")
        print("1. Run scoring pipeline: python run_scoring.py")
        print("2. Ensure flags have confidence ≥0.7 and score ≥70")
        print("3. Run this script again")
        print()


if __name__ == "__main__":
    main()
