"""
Simple pipeline runner - executes current pipeline state
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from utils.db_utils import get_db

def main():
    """Show current database status"""
    print("\n" + "="*60)
    print("TREND HUNTER - PIPELINE STATUS")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    db = get_db()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        print("Database Status:")
        print()
        
        cur.execute('SELECT COUNT(*) FROM sources_raw')
        print(f"  Raw Posts:        {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM keywords')
        print(f"  Keywords:         {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM time_series_metrics')
        print(f"  Time Series:      {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM features')
        print(f"  Features:         {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM flags')
        flags_count = cur.fetchone()[0]
        print(f"  Flags:            {flags_count}")
        
        if flags_count > 0:
            print()
            print("Recent Flags:")
            cur.execute('''
                SELECT k.canonical_term, f.trend_score, f.label, f.confidence
                FROM flags f
                JOIN keywords k ON f.term_id = k.id
                ORDER BY f.date_time DESC
                LIMIT 5
            ''')
            
            for row in cur.fetchall():
                term, score, label, conf = row
                print(f"    • {term}: {score:.1f} ({label}, {conf:.0%})")
        
        cur.execute('SELECT COUNT(*) FROM ground_truth')
        print(f"  Ground Truth:     {cur.fetchone()[0]}")
    
    print()
    print("="*60)
    print()
    print("Pipeline Components:")
    print("  ✓ Crawlers:        run_crawler.py")
    print("  ✓ Processing:      run_processing.py")
    print("  ✓ Verification:    run_verification.py")
    print("  ✓ Features:        run_features.py")
    print("  ✓ Scoring:         run_scoring.py")
    print("  ✓ Labeling:        run_labeling.py")
    print("  ✓ Backtest:        run_backtest.py")
    print("  ✓ Alerts:          run_alerts.py")
    print("  ✓ Dashboard:       run_dashboard.py")
    print()
    print("Automation:")
    print("  • Scheduler:       production_scheduler.py")
    print()
    print("="*60)

if __name__ == "__main__":
    main()
