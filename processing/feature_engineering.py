"""
Feature Engineering for Trend Hunter (Milestone 4)
Calculates features from time series data and metadata
"""

import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db_utils import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Calculate features for trend detection"""
    
    def __init__(self):
        self.db = get_db()
    
    def calculate_slope(self, dates: List[str], values: List[float]) -> Optional[float]:
        """
        Calculate linear regression slope on IOT time series
        
        Args:
            dates: List of date strings (YYYY-MM-DD)
            values: List of IOT values (0-100)
        
        Returns:
            Slope coefficient (positive = upward trend)
        """
        if len(dates) < 2 or len(values) < 2:
            return None
        
        try:
            # Convert dates to numeric (days since first date)
            # Handle both date and datetime formats
            date_objects = []
            for d in dates:
                try:
                    # Try datetime format first
                    date_objects.append(datetime.strptime(d, '%Y-%m-%d %H:%M:%S'))
                except ValueError:
                    # Fall back to date-only format
                    date_objects.append(datetime.strptime(d, '%Y-%m-%d'))
            
            first_date = min(date_objects)
            x = np.array([(d - first_date).days for d in date_objects])
            y = np.array(values)
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            return float(slope)
            
        except Exception as e:
            logger.error(f"Error calculating slope: {e}")
            return None
    
    def calculate_acceleration(self, dates: List[str], values: List[float]) -> Optional[float]:
        """
        Calculate acceleration (second derivative)
        Measures rate of change of the slope
        
        Args:
            dates: List of date strings
            values: List of IOT values
        
        Returns:
            Acceleration coefficient (positive = accelerating growth)
        """
        if len(dates) < 3 or len(values) < 3:
            return None
        
        try:
            # Convert to numeric
            # Handle both date and datetime formats
            date_objects = []
            for d in dates:
                try:
                    date_objects.append(datetime.strptime(d, '%Y-%m-%d %H:%M:%S'))
                except ValueError:
                    date_objects.append(datetime.strptime(d, '%Y-%m-%d'))
            
            first_date = min(date_objects)
            x = np.array([(d - first_date).days for d in date_objects])
            y = np.array(values)
            
            # Fit quadratic: y = ax^2 + bx + c
            # Acceleration = 2a
            coeffs = np.polyfit(x, y, 2)
            acceleration = 2 * coeffs[0]
            
            return float(acceleration)
            
        except Exception as e:
            logger.error(f"Error calculating acceleration: {e}")
            return None
    
    def calculate_moving_averages(self, values: List[float]) -> Dict[str, Optional[float]]:
        """
        Calculate moving averages (MA3, MA7)
        
        Args:
            values: List of IOT values (chronologically ordered)
        
        Returns:
            Dict with ma3, ma7 keys
        """
        result = {'ma3': None, 'ma7': None}
        
        if not values:
            return result
        
        try:
            arr = np.array(values)
            
            # MA3 (3-day moving average)
            if len(arr) >= 3:
                result['ma3'] = float(np.mean(arr[-3:]))
            
            # MA7 (7-day moving average)
            if len(arr) >= 7:
                result['ma7'] = float(np.mean(arr[-7:]))
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return result
    
    def calculate_percent_changes(self, dates: List[str], values: List[float]) -> Dict[str, Optional[float]]:
        """
        Calculate percent changes over different windows
        
        Args:
            dates: List of date strings
            values: List of IOT values
        
        Returns:
            Dict with pct_change_24h, pct_change_7d keys
        """
        result = {
            'pct_change_24h': None,
            'pct_change_7d': None
        }
        
        if len(dates) < 2 or len(values) < 2:
            return result
        
        try:
            # Create DataFrame for easier date-based operations
            df = pd.DataFrame({
                'date': pd.to_datetime(dates),
                'value': values
            })
            df = df.sort_values('date')
            
            # Get most recent value and date
            latest_value = df.iloc[-1]['value']
            latest_date = df.iloc[-1]['date']
            
            # 24h change
            date_24h_ago = latest_date - timedelta(hours=24)
            df_24h = df[df['date'] >= date_24h_ago]
            if len(df_24h) >= 2:
                old_value = df_24h.iloc[0]['value']
                if old_value > 0:
                    result['pct_change_24h'] = float(((latest_value - old_value) / old_value) * 100)
            
            # 7d change
            date_7d_ago = latest_date - timedelta(days=7)
            df_7d = df[df['date'] >= date_7d_ago]
            if len(df_7d) >= 2:
                old_value = df_7d.iloc[0]['value']
                if old_value > 0:
                    result['pct_change_7d'] = float(((latest_value - old_value) / old_value) * 100)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating percent changes: {e}")
            return result
    
    def calculate_platform_count(self, keyword_id: int) -> int:
        """
        Calculate number of platforms where keyword appears
        
        Args:
            keyword_id: Keyword ID
        
        Returns:
            Count of unique platforms (1-2+)
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                # Count distinct source types for this keyword
                # Note: This requires joining with sources_raw through content matching
                # For now, we'll estimate based on total_mentions distribution
                cur.execute('''
                    SELECT total_mentions FROM keywords
                    WHERE id = ?
                ''', (keyword_id,))
                
                row = cur.fetchone()
                if not row:
                    return 0
                
                total_mentions = row[0]
                
                # Simple heuristic: if mentioned multiple times, likely from 2+ platforms
                # TODO: Improve by tracking platform in keyword extraction phase
                if total_mentions >= 3:
                    return 2
                else:
                    return 1
            
        except Exception as e:
            logger.error(f"Error calculating platform count: {e}")
            return 0
    
    def calculate_novelty_score(self, first_seen: str, total_mentions: int) -> float:
        """
        Calculate novelty score (inverse of term age/frequency)
        Higher score = newer/less common term
        
        Args:
            first_seen: Timestamp of first appearance
            total_mentions: Number of mentions
        
        Returns:
            Novelty score (0-100)
        """
        try:
            # Parse first_seen timestamp - handle both formats
            try:
                first_seen_dt = datetime.strptime(first_seen, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    first_seen_dt = datetime.strptime(first_seen, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    first_seen_dt = datetime.strptime(first_seen, '%Y-%m-%d')
            
            now = datetime.now()
            
            # Calculate age in hours
            age_hours = (now - first_seen_dt).total_seconds() / 3600
            
            # Newer = higher score (decay with age)
            # Use exponential decay: score = 100 * e^(-age/48)
            # After 48h, score drops to ~37
            age_factor = np.exp(-age_hours / 48.0)
            
            # Rarity factor: less common = higher score
            # Inverse of log(total_mentions + 1)
            rarity_factor = 1.0 / np.log10(total_mentions + 10)
            
            # Combined novelty score (0-100)
            novelty = 100 * age_factor * rarity_factor
            novelty = min(100.0, max(0.0, novelty))
            
            return float(novelty)
            
        except Exception as e:
            logger.error(f"Error calculating novelty score: {e}")
            return 0.0
    
    def get_time_series_data(self, keyword_id: int) -> Tuple[List[str], List[float]]:
        """
        Fetch time series data for a keyword
        
        Args:
            keyword_id: Keyword ID
        
        Returns:
            Tuple of (dates, values)
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT date_time, iot_value
                    FROM time_series_metrics
                    WHERE term_id = ?
                    ORDER BY date_time ASC
                ''', (keyword_id,))
                
                rows = cur.fetchall()
                
                dates = [row[0] for row in rows]
                values = [row[1] for row in rows]
                
                return dates, values
            
        except Exception as e:
            logger.error(f"Error fetching time series data: {e}")
            return [], []
    
    def get_keyword_metadata(self, keyword_id: int) -> Optional[Dict]:
        """
        Fetch keyword metadata
        
        Args:
            keyword_id: Keyword ID
        
        Returns:
            Dict with term, first_seen, mention_count, etc.
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT id, canonical_term, first_seen, 
                           last_seen, total_mentions, is_active
                    FROM keywords
                    WHERE id = ?
                ''', (keyword_id,))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return {
                    'id': row[0],
                    'canonical_term': row[1],
                    'first_seen': row[2],
                    'last_seen': row[3],
                    'total_mentions': row[4],
                    'is_active': row[5]
                }
            
        except Exception as e:
            logger.error(f"Error fetching keyword metadata: {e}")
            return None
    
    def calculate_all_features(self, keyword_id: int) -> Optional[Dict]:
        """
        Calculate all features for a keyword
        
        Args:
            keyword_id: Keyword ID
        
        Returns:
            Dict with all features, or None if insufficient data
        """
        # Get metadata
        metadata = self.get_keyword_metadata(keyword_id)
        if not metadata:
            logger.warning(f"No metadata found for keyword_id={keyword_id}")
            return None
        
        # Get time series
        dates, values = self.get_time_series_data(keyword_id)
        
        if len(dates) < 2 or len(values) < 2:
            logger.warning(f"Insufficient time series data for keyword_id={keyword_id} (term='{metadata['canonical_term']}')")
            return None
        
        logger.info(f"Calculating features for: {metadata['canonical_term']} ({len(dates)} data points)")
        
        # Calculate all features
        features = {
            'keyword_id': keyword_id,
            'computed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # Time series features
            'slope': self.calculate_slope(dates, values),
            'acceleration': self.calculate_acceleration(dates, values),
            
            # Moving averages
            **self.calculate_moving_averages(values),
            
            # Percent changes
            **self.calculate_percent_changes(dates, values),
            
            # Platform & novelty
            'platform_count': self.calculate_platform_count(keyword_id),
            'novelty_score': self.calculate_novelty_score(metadata['first_seen'], metadata['total_mentions']),
            
            # Latest IOT value (for reference)
            'latest_iot': float(values[-1]) if values else None
        }
        
        return features
    
    def save_features(self, features: Dict) -> bool:
        """
        Save features to database
        
        Args:
            features: Dict with all feature values
        
        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                cur.execute('''
                    INSERT OR REPLACE INTO features (
                        term_id, date_time,
                        slope, acceleration,
                        ma3, ma7,
                        pct_change_24h,
                        novelty_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    features['keyword_id'],
                    features['computed_at'],
                    features['slope'],
                    features['acceleration'],
                    features['ma3'],
                    features['ma7'],
                    features['pct_change_24h'],
                    features['novelty_score']
                ))
                
                conn.commit()
                logger.info(f"Saved features for keyword_id={features['keyword_id']}")
                logger.info(f"Saved features for keyword_id={features['keyword_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving features: {e}")
            return False
    
    def process_all_keywords(self) -> Dict[str, int]:
        """
        Process all verified keywords
        
        Returns:
            Dict with success/failed counts
        """
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            # Get all active keywords with time series data
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT DISTINCT k.id
                    FROM keywords k
                    INNER JOIN time_series_metrics t ON k.id = t.term_id
                    WHERE k.is_active = 1
                    ORDER BY k.id
                ''')
                
                keyword_ids = [row[0] for row in cur.fetchall()]
                stats['total'] = len(keyword_ids)
            
            logger.info(f"Processing {stats['total']} keywords...")
            
            for keyword_id in keyword_ids:
                # Calculate features
                features = self.calculate_all_features(keyword_id)
                
                if features is None:
                    stats['skipped'] += 1
                    continue
                
                # Save to database
                if self.save_features(features):
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
            
            logger.info(f"Feature engineering complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing keywords: {e}")
            return stats


def main():
    """Run feature engineering pipeline"""
    print("\n" + "="*60)
    print("FEATURE ENGINEERING PIPELINE")
    print("="*60)
    print()
    
    engineer = FeatureEngineer()
    stats = engineer.process_all_keywords()
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Total keywords:    {stats['total']}")
    print(f"Success:           {stats['success']}")
    print(f"Skipped:           {stats['skipped']} (insufficient data)")
    print(f"Failed:            {stats['failed']}")
    print()
    
    if stats['success'] > 0:
        print("Next steps:")
        print("1. Review features table")
        print("2. Build scoring engine (scoring_engine.py)")
        print("3. Generate flags with trend scores")
        print()


if __name__ == "__main__":
    main()
