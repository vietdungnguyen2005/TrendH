"""
Scoring Engine for Trend Hunter (Milestone 4)
Rule-based scoring to identify trending keywords
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db_utils import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrendScorer:
    """Calculate trend scores and assign labels"""
    
    # Scoring weights (configurable)
    WEIGHTS = {
        'slope': 3.0,          # Most important: growth direction
        'acceleration': 2.5,   # Second: rate of change
        'ma7': 1.5,            # Sustained interest level
        'pct_change_24h': 2.0, # Recent momentum
        'novelty_score': 1.0,  # Newness bonus
    }
    
    # Thresholds for labels
    THRESHOLDS = {
        'breakout': 70,    # Score >= 70: Explosive growth
        'hidden_gem': 50,  # Score 50-70: Early stage trend
        'stable': 30,      # Score 30-50: Established but flat
        'dying': 0         # Score < 30: Declining
    }
    
    # Minimum requirements for flagging
    MIN_REQUIREMENTS = {
        'min_slope': 0.5,      # Must have positive slope
        'min_ma7': 10,         # Must have some baseline interest
        'min_data_points': 3   # Need enough history
    }
    
    def __init__(self):
        self.db = get_db()
    
    def calculate_trend_score(self, features: Dict) -> float:
        """
        Calculate overall trend score (0-100)
        
        Args:
            features: Dict with slope, acceleration, ma7, etc.
        
        Returns:
            Trend score (0-100)
        """
        score = 0.0
        
        # Component 1: Slope (normalized to 0-25 range)
        if features.get('slope') is not None:
            slope = features['slope']
            # Positive slope contributes, negative doesn't
            slope_score = max(0, min(25, slope * 5))
            score += slope_score * self.WEIGHTS['slope']
        
        # Component 2: Acceleration (normalized to 0-25 range)
        if features.get('acceleration') is not None:
            accel = features['acceleration']
            # Acceleration can be positive or negative
            accel_score = max(0, min(25, accel * 10 + 12.5))
            score += accel_score * self.WEIGHTS['acceleration']
        
        # Component 3: MA7 (normalized to 0-25 range, capped at 100 IOT)
        if features.get('ma7') is not None:
            ma7 = features['ma7']
            ma7_score = min(25, ma7 / 4)
            score += ma7_score * self.WEIGHTS['ma7']
        
        # Component 4: 24h percent change (normalized to 0-25 range)
        if features.get('pct_change_24h') is not None:
            pct_24h = features['pct_change_24h']
            # 100% change = 25 points
            pct_score = max(0, min(25, pct_24h / 4))
            score += pct_score * self.WEIGHTS['pct_change_24h']
        
        # Component 5: Novelty bonus (0-25 range)
        if features.get('novelty_score') is not None:
            novelty = features['novelty_score']
            novelty_score = novelty / 4  # 100 novelty = 25 points
            score += novelty_score * self.WEIGHTS['novelty_score']
        
        # Normalize to 0-100 scale
        total_weight = sum(self.WEIGHTS.values())
        normalized_score = (score / (25 * total_weight)) * 100
        
        return min(100, max(0, normalized_score))
    
    def assign_label(self, score: float, features: Dict) -> str:
        """
        Assign trend label based on score and features
        
        Args:
            score: Trend score
            features: Feature dict for additional checks
        
        Returns:
            Label string
        """
        slope = features.get('slope', 0)
        ma7 = features.get('ma7', 0)
        
        # Breakout: High score + strong growth
        if score >= self.THRESHOLDS['breakout'] and slope > 2.0:
            return 'Breakout'
        
        # Hidden Gem: Good score + positive growth + relatively unknown
        elif score >= self.THRESHOLDS['hidden_gem']:
            if slope > 1.0 and ma7 < 50:
                return 'Hidden Gem'
            else:
                return 'Rising'
        
        # Stable: Moderate score but flat growth
        elif score >= self.THRESHOLDS['stable']:
            if abs(slope) < 0.5:
                return 'Stable'
            else:
                return 'Moderate Growth'
        
        # Dying: Low score or negative slope
        else:
            if slope < -0.5:
                return 'Dying'
            else:
                return 'Low Interest'
    
    def generate_reason_codes(self, features: Dict, score: float, label: str) -> List[str]:
        """
        Generate reason codes explaining why term was flagged
        
        Args:
            features: Feature dict
            score: Trend score
            label: Assigned label
        
        Returns:
            List of reason codes
        """
        reasons = []
        
        slope = features.get('slope', 0)
        accel = features.get('acceleration', 0)
        ma7 = features.get('ma7', 0)
        pct_24h = features.get('pct_change_24h', 0)
        novelty = features.get('novelty_score', 0)
        
        # Growth reasons
        if slope > 3.0:
            reasons.append('STRONG_GROWTH')
        elif slope > 1.0:
            reasons.append('POSITIVE_GROWTH')
        elif slope < -1.0:
            reasons.append('DECLINING')
        
        # Acceleration reasons
        if accel > 0.5:
            reasons.append('ACCELERATING')
        elif accel < -0.5:
            reasons.append('DECELERATING')
        
        # Volume reasons
        if ma7 > 70:
            reasons.append('HIGH_VOLUME')
        elif ma7 < 20:
            reasons.append('LOW_VOLUME')
        
        # Momentum reasons
        if pct_24h > 50:
            reasons.append('SPIKE_24H')
        elif pct_24h > 20:
            reasons.append('GROWING_24H')
        elif pct_24h < -20:
            reasons.append('DROPPING_24H')
        
        # Novelty reasons
        if novelty > 70:
            reasons.append('VERY_NEW')
        elif novelty > 40:
            reasons.append('RELATIVELY_NEW')
        
        # Label-specific reasons
        if label == 'Breakout':
            reasons.append('BREAKOUT_PATTERN')
        elif label == 'Hidden Gem':
            reasons.append('EARLY_STAGE_TREND')
        elif label == 'Dying':
            reasons.append('LOSING_INTEREST')
        
        return reasons
    
    def check_minimum_requirements(self, features: Dict) -> Tuple[bool, str]:
        """
        Check if keyword meets minimum requirements for flagging
        
        Args:
            features: Feature dict
        
        Returns:
            (passes, reason) tuple
        """
        slope = features.get('slope')
        ma7 = features.get('ma7')
        
        # Must have slope data
        if slope is None:
            return False, 'NO_SLOPE_DATA'
        
        # Must have baseline interest
        if ma7 is not None and ma7 < self.MIN_REQUIREMENTS['min_ma7']:
            return False, 'INSUFFICIENT_INTEREST'
        
        # For positive flags, need positive slope
        if slope < self.MIN_REQUIREMENTS['min_slope']:
            return False, 'NO_GROWTH'
        
        return True, 'OK'
    
    def get_features_for_keyword(self, keyword_id: int) -> Optional[Dict]:
        """
        Fetch latest features for a keyword
        
        Args:
            keyword_id: Keyword ID
        
        Returns:
            Feature dict or None
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT 
                        term_id, date_time,
                        slope, acceleration,
                        ma3, ma7,
                        pct_change_24h,
                        novelty_score
                    FROM features
                    WHERE term_id = ?
                    ORDER BY date_time DESC
                    LIMIT 1
                ''', (keyword_id,))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return {
                    'keyword_id': row[0],
                    'date_time': row[1],
                    'slope': row[2],
                    'acceleration': row[3],
                    'ma3': row[4],
                    'ma7': row[5],
                    'pct_change_24h': row[6],
                    'novelty_score': row[7]
                }
        
        except Exception as e:
            logger.error(f"Error fetching features: {e}")
            return None
    
    def get_keyword_term(self, keyword_id: int) -> Optional[str]:
        """Get canonical term for keyword"""
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT canonical_term FROM keywords WHERE id = ?', (keyword_id,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error fetching keyword: {e}")
            return None
    
    def save_flag(self, keyword_id: int, score: float, label: str, 
                  confidence: float, reasons: List[str]) -> bool:
        """
        Save flag to database
        
        Args:
            keyword_id: Keyword ID
            score: Trend score
            label: Trend label
            confidence: Confidence score (0-1)
            reasons: List of reason codes
        
        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                reason_json = json.dumps(reasons)
                
                cur.execute('''
                    INSERT OR REPLACE INTO flags (
                        term_id, date_time,
                        trend_score, label,
                        confidence, reason_codes,
                        alert_sent, is_verified
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, NULL)
                ''', (
                    keyword_id,
                    now,
                    score,
                    label,
                    confidence,
                    reason_json
                ))
                
                conn.commit()
                logger.info(f"Saved flag for keyword_id={keyword_id}: {label} (score={score:.1f})")
                return True
        
        except Exception as e:
            logger.error(f"Error saving flag: {e}")
            return False
    
    def calculate_confidence(self, features: Dict, score: float) -> float:
        """
        Calculate confidence score (0-1)
        
        Args:
            features: Feature dict
            score: Trend score
        
        Returns:
            Confidence score
        """
        confidence = 0.5  # Base confidence
        
        # More data points = higher confidence
        # (We don't track this yet, so assume medium confidence)
        
        # Consistent features = higher confidence
        if features.get('slope') is not None and features.get('acceleration') is not None:
            if features['slope'] > 0 and features['acceleration'] > 0:
                confidence += 0.2  # Both positive
        
        # High MA7 = more reliable signal
        if features.get('ma7', 0) > 30:
            confidence += 0.1
        
        # Very high or very low scores = higher confidence
        if score > 80 or score < 20:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def score_all_keywords(self) -> Dict[str, int]:
        """
        Score all keywords with features
        
        Returns:
            Dict with stats
        """
        stats = {
            'total': 0,
            'flagged': 0,
            'skipped': 0,
            'failed': 0
        }
        
        try:
            # Get all keywords with features
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT DISTINCT term_id
                    FROM features
                    ORDER BY term_id
                ''')
                
                keyword_ids = [row[0] for row in cur.fetchall()]
                stats['total'] = len(keyword_ids)
            
            logger.info(f"Scoring {stats['total']} keywords...")
            
            for keyword_id in keyword_ids:
                # Get features
                features = self.get_features_for_keyword(keyword_id)
                if not features:
                    stats['skipped'] += 1
                    continue
                
                # Check requirements
                passes, reason = self.check_minimum_requirements(features)
                if not passes:
                    logger.debug(f"Keyword {keyword_id} skipped: {reason}")
                    stats['skipped'] += 1
                    continue
                
                # Calculate score
                score = self.calculate_trend_score(features)
                
                # Assign label
                label = self.assign_label(score, features)
                
                # Generate reasons
                reasons = self.generate_reason_codes(features, score, label)
                
                # Calculate confidence
                confidence = self.calculate_confidence(features, score)
                
                # Get term name for logging
                term = self.get_keyword_term(keyword_id)
                logger.info(f"  {term}: {label} (score={score:.1f}, conf={confidence:.2f})")
                
                # Save flag
                if self.save_flag(keyword_id, score, label, confidence, reasons):
                    stats['flagged'] += 1
                else:
                    stats['failed'] += 1
            
            logger.info(f"Scoring complete: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error scoring keywords: {e}")
            return stats


def main():
    """Run scoring engine"""
    print("\n" + "="*60)
    print("TREND SCORING ENGINE")
    print("="*60)
    print()
    
    scorer = TrendScorer()
    stats = scorer.score_all_keywords()
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Total keywords:    {stats['total']}")
    print(f"Flagged:           {stats['flagged']}")
    print(f"Skipped:           {stats['skipped']} (insufficient data/growth)")
    print(f"Failed:            {stats['failed']}")
    print()
    
    if stats['flagged'] > 0:
        print("Next steps:")
        print("1. Review flags table")
        print("2. Check trend_score and label distribution")
        print("3. Proceed to M5: Backtest framework")
        print()


if __name__ == "__main__":
    main()
