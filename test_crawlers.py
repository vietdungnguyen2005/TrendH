"""
Test script for crawlers
Tests crawlers without Reddit API credentials using mock data
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.db_utils import get_db


def test_database():
    """Test database connection and tables"""
    print("Testing database connection...")
    
    try:
        db = get_db()
        
        # Check tables exist
        tables = ['sources_raw', 'keywords', 'time_series_metrics', 'features', 'flags']
        for table in tables:
            if db.table_exists(table):
                count = db.get_table_count(table)
                print(f"   ✅ Table '{table}' exists ({count} rows)")
            else:
                print(f"   ❌ Table '{table}' missing!")
                return False
        
        print("✅ Database test passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}\n")
        return False


def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    
    try:
        from utils.config_loader import get_config
        
        config = get_config()
        
        # Test reading some config values
        project_name = config.get('project.name')
        print(f"   Project name: {project_name}")
        
        reddit_enabled = config.get('crawler.reddit.enabled')
        print(f"   Reddit crawler enabled: {reddit_enabled}")
        
        tiktok_enabled = config.get('crawler.tiktok.enabled')
        print(f"   TikTok crawler enabled: {tiktok_enabled}")
        
        print("✅ Config test passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}\n")
        return False


def test_tiktok_crawler_mock():
    """Test TikTok crawler with mock data"""
    print("Testing TikTok crawler (mock mode)...")
    
    try:
        from crawler.tiktok import TikTokCrawler
        
        # Create crawler (will use mock data if Playwright not configured)
        crawler = TikTokCrawler()
        
        # Fetch mock data
        items = crawler.fetch_trending_hashtags_mock()
        print(f"   Fetched {len(items)} mock hashtags")
        
        # Test saving to DB
        saved = crawler.save_to_db(items)
        print(f"   Saved {saved} items to database")
        
        print("✅ TikTok crawler test passed\n")
        return True
        
    except Exception as e:
        print(f"❌ TikTok crawler test failed: {e}\n")
        return False


def test_data_in_db():
    """Verify data was saved to database"""
    print("Verifying data in database...")
    
    try:
        db = get_db()
        
        # Check sources_raw table
        count = db.get_table_count('sources_raw')
        print(f"   Total records in sources_raw: {count}")
        
        if count > 0:
            # Get sample records
            query = "SELECT source, COUNT(*) as count FROM sources_raw GROUP BY source"
            results = db.execute_query(query)
            
            for row in results:
                print(f"   - {row['source']}: {row['count']} records")
            
            print("✅ Data verification passed\n")
            return True
        else:
            print("   ⚠️  No data found (this is OK if crawlers haven't run yet)\n")
            return True
        
    except Exception as e:
        print(f"❌ Data verification failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 TREND HUNTER - CRAWLER TESTS")
    print("=" * 60)
    print()
    
    tests = [
        ("Database Connection", test_database),
        ("Configuration", test_config),
        ("TikTok Crawler (Mock)", test_tiktok_crawler_mock),
        ("Data Verification", test_data_in_db),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}\n")
            failed += 1
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()
    
    if failed == 0:
        print("✅ All tests passed!")
        print()
        print("Next steps:")
        print("1. Configure Reddit API credentials in .env file")
        print("2. Run: python run_crawler.py")
        print()
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
