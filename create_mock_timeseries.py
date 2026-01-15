"""Create mock time series data for testing"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent))
from utils.db_utils import get_db

def create_mock_time_series():
    db = get_db()
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, canonical_term FROM keywords LIMIT 5")
        keywords = cur.fetchall()
        
        if not keywords:
            print("No keywords found")
            return
        
        print(f"Creating mock data for {len(keywords)} keywords...")
        
        for keyword_id, term in keywords:
            print(f"\\nKeyword: {term}")
            base_date = datetime.now() - timedelta(days=7)
            pattern = random.choice(['upward', 'breakout', 'stable', 'declining'])
            base_iot = random.randint(20, 50)
            
            for day in range(8):
                date = base_date + timedelta(days=day)
                date_str = date.strftime('%Y-%m-%d %H:%M:%S')
                
                if pattern == 'upward':
                    iot = base_iot + (day * 5) + random.randint(-3, 3)
                elif pattern == 'breakout':
                    iot = base_iot + int(day ** 1.5 * 3) + random.randint(-2, 2)
                elif pattern == 'stable':
                    iot = base_iot + random.randint(-5, 5)
                else:
                    iot = base_iot - (day * 3) + random.randint(-2, 2)
                
                iot = max(0, min(100, iot))
                samples = [max(0, min(100, iot + random.randint(-2, 2))) for _ in range(3)]
                
                cur.execute('''
                    INSERT OR REPLACE INTO time_series_metrics 
                    (term_id, date_time, iot_value, raw_samples_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (keyword_id, date_str, iot, str(samples), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
                print(f"  {date_str[:10]}: {iot} ({pattern})")
        
        conn.commit()
        print(f"\\nCreated time series data for {len(keywords)} keywords")

if __name__ == "__main__":
    create_mock_time_series()
