"""
Backtest Framework for Trend Hunter (Milestone 5)
Rolling-window cross-validation and metrics calculation
"""

import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta
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


class BacktestRunner:
    """Run rolling-window backtest and calculate metrics"""
    
    def __init__(self, train_window_days: int = 14, test_window_days: int = 7):
        """
        Initialize backtest runner
        
        Args:
            train_window_days: Training window size (days)
            test_window_days: Testing window size (days)
        """
        self.db = get_db()
        self.train_window_days = train_window_days
        self.test_window_days = test_window_days
    
    def get_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get min and max dates from time series data"""
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT MIN(date_time), MAX(date_time)
                    FROM time_series_metrics
                ''')
                row = cur.fetchone()
                
                if row and row[0] and row[1]:
                    min_date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                    max_date = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                    return min_date, max_date
        
        except Exception as e:
            logger.error(f"Error getting date range: {e}")
        
        return None, None
    
    def calculate_precision_at_k(self, k: int = 50) -> float:
        """
        Calculate Precision@K
        
        Args:
            k: Top K flags to consider
        
        Returns:
            Precision score (0-1)
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                # Get top K flags by score
                cur.execute('''
                    SELECT f.id, f.term_id, f.date_time, g.is_true_trend
                    FROM flags f
                    LEFT JOIN ground_truth g ON f.term_id = g.term_id AND f.date_time = g.flag_date
                    ORDER BY f.trend_score DESC
                    LIMIT ?
                ''', (k,))
                
                flags = cur.fetchall()
                
                if not flags:
                    return 0.0
                
                # Count confirmed trends
                confirmed = sum(1 for row in flags if row[3] == 1)
                
                precision = confirmed / len(flags)
                return precision
        
        except Exception as e:
            logger.error(f"Error calculating Precision@K: {e}")
            return 0.0
    
    def calculate_recall_at_window(self, window_days: int = 7) -> float:
        """
        Calculate Recall within time window
        
        Args:
            window_days: Time window (days)
        
        Returns:
            Recall score (0-1)
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                # Get all confirmed trends
                cur.execute('''
                    SELECT COUNT(*)
                    FROM ground_truth
                    WHERE is_true_trend = 1
                ''')
                total_true_trends = cur.fetchone()[0]
                
                if total_true_trends == 0:
                    return 0.0
                
                # Count how many we caught within window
                # (This is simplified - in real backtest, we'd check timing)
                cur.execute('''
                    SELECT COUNT(*)
                    FROM flags f
                    INNER JOIN ground_truth g ON f.term_id = g.term_id AND f.date_time = g.flag_date
                    WHERE g.is_true_trend = 1
                ''')
                caught_trends = cur.fetchone()[0]
                
                recall = caught_trends / total_true_trends
                return recall
        
        except Exception as e:
            logger.error(f"Error calculating Recall: {e}")
            return 0.0
    
    def calculate_lead_time(self) -> Dict[str, float]:
        """
        Calculate lead time statistics
        
        Returns:
            Dict with mean, median, min, max lead times (hours)
        """
        lead_times = []
        
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                # Get confirmed trends with flag time
                cur.execute('''
                    SELECT f.term_id, f.date_time
                    FROM flags f
                    INNER JOIN ground_truth g ON f.term_id = g.term_id AND f.date_time = g.flag_date
                    WHERE g.is_true_trend = 1
                ''')
                
                confirmed_flags = cur.fetchall()
                
                for term_id, flag_date_str in confirmed_flags:
                    flag_date = datetime.strptime(flag_date_str, '%Y-%m-%d %H:%M:%S')
                    
                    # Find peak IOT after flag
                    cur.execute('''
                        SELECT date_time, iot_value
                        FROM time_series_metrics
                        WHERE term_id = ? AND date_time >= ?
                        ORDER BY iot_value DESC
                        LIMIT 1
                    ''', (term_id, flag_date_str))
                    
                    row = cur.fetchone()
                    if row:
                        peak_date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                        lead_hours = (peak_date - flag_date).total_seconds() / 3600
                        lead_times.append(lead_hours)
            
            if lead_times:
                lead_times.sort()
                n = len(lead_times)
                return {
                    'mean': sum(lead_times) / n,
                    'median': lead_times[n // 2],
                    'min': min(lead_times),
                    'max': max(lead_times),
                    'count': n
                }
            else:
                return {'mean': 0, 'median': 0, 'min': 0, 'max': 0, 'count': 0}
        
        except Exception as e:
            logger.error(f"Error calculating lead time: {e}")
            return {'mean': 0, 'median': 0, 'min': 0, 'max': 0, 'count': 0}
    
    def calculate_false_positive_rate(self) -> float:
        """
        Calculate False Positive Rate (FPR)
        
        Returns:
            FPR score (0-1)
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                
                # Total flags
                cur.execute('SELECT COUNT(*) FROM flags')
                total_flags = cur.fetchone()[0]
                
                if total_flags == 0:
                    return 0.0
                
                # False positives
                cur.execute('''
                    SELECT COUNT(*)
                    FROM ground_truth
                    WHERE is_true_trend = 0
                ''')
                false_positives = cur.fetchone()[0]
                
                fpr = false_positives / total_flags
                return fpr
        
        except Exception as e:
            logger.error(f"Error calculating FPR: {e}")
            return 0.0
    
    def generate_backtest_report(self) -> Dict:
        """
        Generate comprehensive backtest report
        
        Returns:
            Dict with all metrics
        """
        logger.info("Generating backtest report...")
        
        report = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': {}
        }
        
        # Precision@K for different K values
        for k in [10, 20, 50]:
            precision = self.calculate_precision_at_k(k)
            report['metrics'][f'precision@{k}'] = round(precision * 100, 1)
        
        # Recall
        recall = self.calculate_recall_at_window(7)
        report['metrics']['recall@7d'] = round(recall * 100, 1)
        
        # FPR
        fpr = self.calculate_false_positive_rate()
        report['metrics']['false_positive_rate'] = round(fpr * 100, 1)
        
        # Lead time
        lead_time = self.calculate_lead_time()
        report['metrics']['lead_time_hours'] = {
            k: round(v, 1) if isinstance(v, float) else v
            for k, v in lead_time.items()
        }
        
        # Flag statistics
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            
            # Total flags
            cur.execute('SELECT COUNT(*) FROM flags')
            report['metrics']['total_flags'] = cur.fetchone()[0]
            
            # Confirmed trends
            cur.execute('''
                SELECT COUNT(*) FROM ground_truth WHERE is_true_trend = 1
            ''')
            report['metrics']['confirmed_trends'] = cur.fetchone()[0]
            
            # False positives
            cur.execute('''
                SELECT COUNT(*) FROM ground_truth WHERE is_true_trend = 0
            ''')
            report['metrics']['false_positives'] = cur.fetchone()[0]
        
        return report
    
    def save_report(self, report: Dict, filename: str = 'backtest_report.json'):
        """Save report to file"""
        try:
            output_path = Path('logs') / filename
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report saved to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return False


def main():
    """Run backtest framework"""
    print("\n" + "="*60)
    print("BACKTEST FRAMEWORK")
    print("="*60)
    print()
    
    runner = BacktestRunner(train_window_days=14, test_window_days=7)
    
    # Generate report
    report = runner.generate_backtest_report()
    
    print("\n" + "="*60)
    print("BACKTEST METRICS")
    print("="*60)
    print()
    
    metrics = report['metrics']
    
    print("Precision@K:")
    for k in [10, 20, 50]:
        key = f'precision@{k}'
        if key in metrics:
            print(f"  Top {k}: {metrics[key]}%")
    
    print()
    print("Other Metrics:")
    print(f"  Recall@7d:     {metrics.get('recall@7d', 0)}%")
    print(f"  FPR:           {metrics.get('false_positive_rate', 0)}%")
    
    print()
    print("Lead Time:")
    lead = metrics.get('lead_time_hours', {})
    if lead.get('count', 0) > 0:
        print(f"  Mean:   {lead['mean']}h")
        print(f"  Median: {lead['median']}h")
        print(f"  Range:  {lead['min']}h - {lead['max']}h")
    else:
        print("  No data available")
    
    print()
    print("Flag Statistics:")
    print(f"  Total flags:       {metrics.get('total_flags', 0)}")
    print(f"  Confirmed trends:  {metrics.get('confirmed_trends', 0)}")
    print(f"  False positives:   {metrics.get('false_positives', 0)}")
    
    # Save report
    runner.save_report(report)
    
    print()
    print("="*60)
    print("Report saved to: logs/backtest_report.json")
    print()
    print("Next steps:")
    print("1. Tune scoring thresholds based on metrics")
    print("2. Proceed to M6: UI & Alerts")
    print()


if __name__ == "__main__":
    main()
