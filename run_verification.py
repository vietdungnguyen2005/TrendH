"""
Verification pipeline for Trend Hunter
Verifies keywords with Google Trends and saves time series metrics
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

from verification.pytrends_wrapper import PyTrendsWrapper, PYTRENDS_AVAILABLE
from utils.db_utils import get_db
from utils.config_loader import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class VerificationPipeline:
    """Pipeline for verifying keywords with Google Trends"""
    
    def __init__(self):
        self.config = get_config()
        self.db = get_db()
        
        # Check if pytrends is available
        if not PYTRENDS_AVAILABLE:
            logger.error("pytrends not available. Install with: pip install pytrends")
            self.wrapper = None
        else:
            self.wrapper = PyTrendsWrapper()
        
        self.stats = {
            'keywords_processed': 0,
            'keywords_verified': 0,
            'keywords_failed': 0,
            'cache_hits': 0,
            'api_calls': 0
        }
        
        logger.info("Verification pipeline initialized")
    
    def fetch_keywords_to_verify(self, limit: int = 100) -> List[Dict]:
        """
        Fetch keywords from database that need verification
        Prioritize keywords with highest mentions that haven't been verified recently
        """
        query = """
            SELECT k.id, k.canonical_term, k.total_mentions, k.last_seen
            FROM keywords k
            LEFT JOIN time_series_metrics t ON k.id = t.term_id
            WHERE k.is_active = 1
            GROUP BY k.id
            HAVING MAX(t.created_at) IS NULL 
                OR MAX(t.created_at) < datetime('now', '-1 day')
            ORDER BY k.total_mentions DESC, k.last_seen DESC
            LIMIT ?
        """
        
        keywords = self.db.execute_query(query, (limit,))
        keywords_list = [dict(kw) for kw in keywords]
        
        logger.info(f"Fetched {len(keywords_list)} keywords to verify")
        return keywords_list
    
    def save_time_series_metrics(self, keyword_id: int, term: str, verification_result: Dict):
        """Save verification results to time_series_metrics table"""
        try:
            if 'error' in verification_result:
                logger.warning(f"Skipping save for {term} due to error")
                return False
            
            median_iot = verification_result.get('median_iot', {})
            samples = verification_result.get('samples', [])
            
            if not median_iot:
                logger.warning(f"No IOT data for {term}")
                return False
            
            # Calculate platform mentions (from keywords table context)
            # For now, we'll use placeholder values since we're only verifying Google Trends
            mentions_reddit = 0
            mentions_tiktok = 0
            
            # Save each time point
            for date_str, iot_value in median_iot.items():
                # Convert date string to datetime
                try:
                    date_time = datetime.fromisoformat(date_str)
                except:
                    # Try parsing pandas timestamp string
                    from datetime import datetime as dt
                    date_time = dt.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                
                data = {
                    'term_id': keyword_id,
                    'date_time': date_time.isoformat(),
                    'iot_value': float(iot_value),
                    'mentions_reddit': mentions_reddit,
                    'mentions_tiktok': mentions_tiktok,
                    'mentions_total': mentions_reddit + mentions_tiktok,
                    'platform_count': 1,  # Google Trends
                    'raw_samples_json': json.dumps([s.get('data', {}) for s in samples]),
                    'created_at': datetime.now().isoformat()
                }
                
                # Check if record exists
                existing = self.db.execute_query(
                    "SELECT id FROM time_series_metrics WHERE term_id = ? AND date_time = ?",
                    (keyword_id, date_time.isoformat())
                )
                
                if existing:
                    # Update existing
                    update_query = """
                        UPDATE time_series_metrics 
                        SET iot_value = ?, raw_samples_json = ?
                        WHERE id = ?
                    """
                    self.db.execute_query(
                        update_query,
                        (float(iot_value), data['raw_samples_json'], existing[0]['id'])
                    )
                else:
                    # Insert new
                    self.db.insert('time_series_metrics', data)
            
            logger.debug(f"Saved {len(median_iot)} time series points for {term}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metrics for {term}: {e}")
            return False
    
    def verify_keywords(self, keywords: List[Dict]) -> Dict[str, Any]:
        """
        Verify keywords with Google Trends
        """
        if not self.wrapper:
            logger.error("PyTrends wrapper not available")
            return {
                'success': False,
                'error': 'PyTrends not available'
            }
        
        logger.info(f"Verifying {len(keywords)} keywords...")
        
        for i, keyword in enumerate(keywords, 1):
            term = keyword['canonical_term']
            keyword_id = keyword['id']
            
            logger.info(f"[{i}/{len(keywords)}] Verifying: {term}")
            
            try:
                # Verify with Google Trends
                result = self.wrapper.fetch_with_replication(term)
                
                # Save to database
                if self.save_time_series_metrics(keyword_id, term, result):
                    self.stats['keywords_verified'] += 1
                else:
                    self.stats['keywords_failed'] += 1
                
                self.stats['keywords_processed'] += 1
                
            except Exception as e:
                logger.error(f"Failed to verify {term}: {e}")
                self.stats['keywords_failed'] += 1
        
        return {
            'success': True,
            'stats': self.stats
        }
    
    def run(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Run verification pipeline
        """
        start_time = datetime.now()
        logger.info("Starting Verification Pipeline")
        logger.info("=" * 60)
        
        try:
            # Ensure logs directory exists
            Path('logs').mkdir(exist_ok=True)
            
            # Check if pytrends available
            if not PYTRENDS_AVAILABLE:
                logger.error("pytrends not installed")
                return {
                    'success': False,
                    'error': 'pytrends not installed. Run: pip install pytrends'
                }
            
            # Fetch keywords to verify
            keywords = self.fetch_keywords_to_verify(limit=batch_size)
            
            if not keywords:
                logger.info("No keywords to verify")
                return {
                    'success': True,
                    'message': 'No keywords to verify',
                    'stats': self.stats
                }
            
            # Verify keywords
            result = self.verify_keywords(keywords)
            
            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Print summary
            logger.info("=" * 60)
            logger.info("VERIFICATION PIPELINE SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Keywords processed: {self.stats['keywords_processed']}")
            logger.info(f"Keywords verified: {self.stats['keywords_verified']}")
            logger.info(f"Keywords failed: {self.stats['keywords_failed']}")
            logger.info("=" * 60)
            logger.info("Verification pipeline completed")
            
            return {
                'success': True,
                'duration_seconds': duration,
                'stats': self.stats
            }
            
        except Exception as e:
            logger.error(f"Verification pipeline failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }


def main():
    """Main entry point"""
    try:
        pipeline = VerificationPipeline()
        result = pipeline.run(batch_size=10)  # Small batch for testing
        
        if result['success']:
            return 0
        else:
            logger.error(f"Pipeline failed: {result.get('error')}")
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
