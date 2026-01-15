"""
Ground Truth Labeling for Trend Hunter (Milestone 5)
Auto-label historical data based on ground-truth criteria
"""

import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db_utils import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GroundTruthLabeler:
    """Label keywords as true trends or false positives"""
    
    # Ground truth criteria
    CRITERIA = {
        # Criterion 1: IOT doubled within 7 days
        'iot_growth_threshold': 100,  # 100% increase
        'iot_growth_window_days': 7,
        
        # Criterion 2: Reached top percentile
        'top_percentile_threshold': 90,  # Top 10%
        
        # Criterion 3: Sustained high interest
        'sustained_iot_threshold': 70,  # IOT >= 70
        'sustained_days': 3,  # For 3+ consecutive days
    }
    
    def __init__(self):
        self.db = get_db()
    
    def get_time_series_for_keyword(self, keyword_id: int, 
                                     start_date: Optional[str] = None,
                                     end_date: Optional[str] = None) -> List[Tuple]:
        """
        Get time series data for a keyword
        
        Args:
            keyword_id: Keyword ID
            start_date: Start date (YYYY-MM-DD HH:MM:SS)
            end_date: End date (YYYY-MM-DD HH:MM:SS)
        
        Returns:
            List of (date, iot_value) tuples
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                query = '''
                    SELECT date_time, iot_value
                    FROM time_series_metrics
                    WHERE term_id = ?
                '''
                params = [keyword_id]
                
                if start_date:
                    query += ' AND date_time >= ?'
                    params.append(start_date)
                
                if end_date:
                    query += ' AND date_time <= ?'
                    params.append(end_date)
                
                query += ' ORDER BY date_time ASC'
                
                cur.execute(query, params)
                return cur.fetchall()
        
        except Exception as e:
            logger.error(f"Error fetching time series: {e}")
            return []
    
    def check_iot_growth_criterion(self, time_series: List[Tuple]) -> Tuple[bool, float]:
        """
        Check if IOT doubled within window
        
        Args:
            time_series: List of (date, iot) tuples
        
        Returns:
            (meets_criterion, max_growth_pct) tuple
        """
        if len(time_series) < 2:
            return False, 0.0
        
        max_growth = 0.0
        window_days = self.CRITERIA['iot_growth_window_days']
        
        for i in range(len(time_series)):
            date_start = datetime.strptime(time_series[i][0], '%Y-%m-%d %H:%M:%S')
            iot_start = time_series[i][1]
            
            if iot_start == 0:
                continue
            
            # Check all points within window
            for j in range(i + 1, len(time_series)):
                date_end = datetime.strptime(time_series[j][0], '%Y-%m-%d %H:%M:%S')
                
                if (date_end - date_start).days > window_days:
                    break
                
                iot_end = time_series[j][1]
                growth = ((iot_end - iot_start) / iot_start) * 100
                max_growth = max(max_growth, growth)
        
        meets_criterion = max_growth >= self.CRITERIA['iot_growth_threshold']
        return meets_criterion, max_growth
    
    def check_top_percentile_criterion(self, keyword_id: int, 
                                        time_series: List[Tuple]) -> Tuple[bool, float]:
        """
        Check if keyword reached top percentile
        
        Args:
            keyword_id: Keyword ID
            time_series: List of (date, iot) tuples
        
        Returns:
            (meets_criterion, percentile) tuple
        """
        if not time_series:
            return False, 0.0
        
        max_iot = max(iot for _, iot in time_series)
        
        try:
            # Get all IOT values for percentile calculation
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT iot_value FROM time_series_metrics')
                all_iots = [row[0] for row in cur.fetchall()]
            
            if not all_iots:
                return False, 0.0
            
            # Calculate percentile
            all_iots.sort()
            position = sum(1 for iot in all_iots if iot <= max_iot)
            percentile = (position / len(all_iots)) * 100
            
            meets_criterion = percentile >= self.CRITERIA['top_percentile_threshold']
            return meets_criterion, percentile
        
        except Exception as e:
            logger.error(f"Error calculating percentile: {e}")
            return False, 0.0
    
    def check_sustained_interest_criterion(self, time_series: List[Tuple]) -> Tuple[bool, int]:
        """
        Check if keyword had sustained high interest
        
        Args:
            time_series: List of (date, iot) tuples
        
        Returns:
            (meets_criterion, max_consecutive_days) tuple
        """
        if not time_series:
            return False, 0
        
        threshold = self.CRITERIA['sustained_iot_threshold']
        required_days = self.CRITERIA['sustained_days']
        
        consecutive_days = 0
        max_consecutive = 0
        
        for _, iot in time_series:
            if iot >= threshold:
                consecutive_days += 1
                max_consecutive = max(max_consecutive, consecutive_days)
            else:
                consecutive_days = 0
        
        meets_criterion = max_consecutive >= required_days
        return meets_criterion, max_consecutive
    
    def evaluate_keyword(self, keyword_id: int, 
                         flag_date: Optional[str] = None) -> Dict:
        """
        Evaluate if keyword is a true trend
        
        Args:
            keyword_id: Keyword ID
            flag_date: Date when keyword was flagged (for forward-looking eval)
        
        Returns:
            Dict with evaluation results
        """
        # Get time series
        if flag_date:
            # For backtest: only look at data AFTER flag date
            start_date = flag_date
            end_date = None
        else:
            # For retrospective: look at all data
            start_date = None
            end_date = None
        
        time_series = self.get_time_series_for_keyword(keyword_id, start_date, end_date)
        
        if not time_series:
            return {
                'keyword_id': keyword_id,
                'is_true_trend': False,
                'criteria_met': [],
                'details': {},
                'reason': 'NO_DATA'
            }
        
        # Check all criteria
        criteria_met = []
        details = {}
        
        # Criterion 1: IOT growth
        growth_met, max_growth = self.check_iot_growth_criterion(time_series)
        if growth_met:
            criteria_met.append('IOT_GROWTH')
        details['max_growth_pct'] = round(max_growth, 1)
        
        # Criterion 2: Top percentile
        percentile_met, percentile = self.check_top_percentile_criterion(keyword_id, time_series)
        if percentile_met:
            criteria_met.append('TOP_PERCENTILE')
        details['percentile'] = round(percentile, 1)
        
        # Criterion 3: Sustained interest
        sustained_met, max_consecutive = self.check_sustained_interest_criterion(time_series)
        if sustained_met:
            criteria_met.append('SUSTAINED_INTEREST')
        details['max_consecutive_days'] = max_consecutive
        
        # Overall verdict: true trend if ANY criterion met
        is_true_trend = len(criteria_met) > 0
        
        return {
            'keyword_id': keyword_id,
            'is_true_trend': is_true_trend,
            'criteria_met': criteria_met,
            'details': details,
            'reason': ', '.join(criteria_met) if criteria_met else 'NO_CRITERIA_MET'
        }
    
    def label_flag(self, flag_id: int) -> bool:
        """
        Label a specific flag as true/false positive
        
        Args:
            flag_id: Flag ID
        
        Returns:
            True if successful
        """
        try:
            # Get flag details
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT term_id, date_time
                    FROM flags
                    WHERE id = ?
                ''', (flag_id,))
                
                row = cur.fetchone()
                if not row:
                    logger.warning(f"Flag {flag_id} not found")
                    return False
                
                keyword_id, flag_date = row
            
            # Evaluate keyword
            evaluation = self.evaluate_keyword(keyword_id, flag_date)
            
            # Save to ground_truth table
            # Schema: term_id, flag_date, outcome_date, is_true_trend, peak_iot, peak_date, lead_time_hours, notes
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                is_true_trend = 1 if evaluation['is_true_trend'] else 0
                notes = f"{evaluation['reason']} | {evaluation['details']}"
                
                # Check if entry exists
                cur.execute('''
                    SELECT id FROM ground_truth
                    WHERE term_id = ? AND flag_date = ?
                ''', (keyword_id, flag_date))
                
                existing = cur.fetchone()
                
                if existing:
                    # Update existing
                    cur.execute('''
                        UPDATE ground_truth
                        SET is_true_trend = ?,
                            outcome_date = ?,
                            notes = ?,
                            updated_at = ?
                        WHERE term_id = ? AND flag_date = ?
                    ''', (
                        is_true_trend,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        notes,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        keyword_id,
                        flag_date
                    ))
                else:
                    # Insert new
                    cur.execute('''
                        INSERT INTO ground_truth (
                            term_id, flag_date, outcome_date, is_true_trend, notes
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        keyword_id,
                        flag_date,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        is_true_trend,
                        notes
                    ))
                
                conn.commit()
            
            label = 'confirmed' if is_true_trend else 'false_positive'
            logger.info(f"Labeled flag {flag_id} (term_id={keyword_id}) as {label}")
            return True
        
        except Exception as e:
            logger.error(f"Error labeling flag: {e}")
            return False
    
    def label_all_flags(self) -> Dict[str, int]:
        """
        Label all flags in database
        
        Returns:
            Dict with stats
        """
        stats = {
            'total': 0,
            'confirmed': 0,
            'false_positive': 0,
            'failed': 0
        }
        
        try:
            # Get all flags
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT id FROM flags ORDER BY id')
                flag_ids = [row[0] for row in cur.fetchall()]
                stats['total'] = len(flag_ids)
            
            logger.info(f"Labeling {stats['total']} flags...")
            
            for flag_id in flag_ids:
                if self.label_flag(flag_id):
                    # Check label by getting term_id and flag_date
                    with self.db.get_connection() as conn:
                        cur = conn.cursor()
                        cur.execute('''
                            SELECT term_id, date_time FROM flags WHERE id = ?
                        ''', (flag_id,))
                        flag_row = cur.fetchone()
                        
                        if flag_row:
                            cur.execute('''
                                SELECT is_true_trend FROM ground_truth 
                                WHERE term_id = ? AND flag_date = ?
                            ''', (flag_row[0], flag_row[1]))
                            row = cur.fetchone()
                            
                            if row:
                                if row[0]:  # is_true_trend = 1
                                    stats['confirmed'] += 1
                                else:
                                    stats['false_positive'] += 1
                else:
                    stats['failed'] += 1
            
            logger.info(f"Labeling complete: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error labeling flags: {e}")
            return stats


def main():
    """Run ground truth labeling"""
    print("\n" + "="*60)
    print("GROUND TRUTH LABELING")
    print("="*60)
    print()
    
    labeler = GroundTruthLabeler()
    
    print("Criteria:")
    print(f"  1. IOT growth ≥100% in 7 days")
    print(f"  2. Reached top 10% percentile")
    print(f"  3. Sustained IOT ≥70 for 3+ days")
    print()
    
    stats = labeler.label_all_flags()
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Total flags:       {stats['total']}")
    print(f"True trends:       {stats['confirmed']}")
    print(f"False positives:   {stats['false_positive']}")
    print(f"Failed:            {stats['failed']}")
    print()
    
    if stats['total'] > 0:
        precision = (stats['confirmed'] / stats['total']) * 100
        print(f"Precision: {precision:.1f}%")
        print()
        print("Next steps:")
        print("1. Review ground_truth table")
        print("2. Run backtest with rolling CV")
        print("3. Calculate Precision@K, Recall, Lead Time")
        print()


if __name__ == "__main__":
    main()
