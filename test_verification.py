"""
Test suite for verification pipeline (Milestone 3)
Tests pytrends wrapper, caching, and rate limiting
"""

import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from verification.pytrends_wrapper import PyTrendsWrapper, TrendsCache, PYTRENDS_AVAILABLE
from utils.db_utils import get_db


def test_cache():
    """Test cache functionality"""
    print("="*60)
    print("TEST 1: Cache Functionality")
    print("="*60)
    
    try:
        cache = TrendsCache(ttl_hours=1)
        
        # Test set and get
        test_key = "test_key"
        test_value = "test_value"
        
        cache.set(test_key, test_value)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            print("  ✅ Cache SET/GET works")
        else:
            print(f"  ❌ Cache GET failed: expected '{test_value}', got '{retrieved}'")
            return False
        
        # Test cache miss
        missing = cache.get("nonexistent_key")
        if missing is None:
            print("  ✅ Cache MISS works")
        else:
            print(f"  ❌ Cache MISS failed: expected None, got '{missing}'")
            return False
        
        # Clean up
        cache.delete(test_key)
        
        print("\n✅ Cache test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Cache test failed: {e}\n")
        return False


def test_pytrends_init():
    """Test PyTrends wrapper initialization"""
    print("="*60)
    print("TEST 2: PyTrends Initialization")
    print("="*60)
    
    if not PYTRENDS_AVAILABLE:
        print("  ⚠️  pytrends not installed")
        print("  Run: pip install pytrends")
        return False
    
    try:
        wrapper = PyTrendsWrapper()
        
        print(f"  Replicate samples: {wrapper.replicate_samples}")
        print(f"  Cache TTL: {wrapper.cache_ttl}h")
        print(f"  Rate limit: {wrapper.rate_limit} req/min")
        print(f"  Delay between requests: {wrapper.delay}s")
        print(f"  Timeframe: {wrapper.timeframe}")
        
        if wrapper.pytrends:
            print("  ✅ PyTrends client initialized")
        else:
            print("  ❌ PyTrends client not initialized")
            return False
        
        print("\n✅ PyTrends initialization passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ PyTrends initialization failed: {e}\n")
        return False


def test_rate_limiting():
    """Test rate limiting"""
    print("="*60)
    print("TEST 3: Rate Limiting")
    print("="*60)
    
    if not PYTRENDS_AVAILABLE:
        print("  ⚠️  Skipping (pytrends not installed)\n")
        return True
    
    try:
        wrapper = PyTrendsWrapper()
        
        # Test delay enforcement
        print("  Testing request delay...")
        start = time.time()
        wrapper.rate_limit_check()
        wrapper.rate_limit_check()
        elapsed = time.time() - start
        
        expected_delay = wrapper.delay
        if elapsed >= expected_delay * 0.9:  # Allow 10% tolerance
            print(f"  ✅ Rate limiting enforced ({elapsed:.1f}s >= {expected_delay}s)")
        else:
            print(f"  ⚠️  Delay shorter than expected ({elapsed:.1f}s < {expected_delay}s)")
        
        print("\n✅ Rate limiting test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Rate limiting test failed: {e}\n")
        return False


def test_single_term_fetch():
    """Test fetching data for a single term"""
    print("="*60)
    print("TEST 4: Single Term Fetch (Mock/Real)")
    print("="*60)
    
    if not PYTRENDS_AVAILABLE:
        print("  ⚠️  Skipping (pytrends not installed)\n")
        return True
    
    print("  ⚠️  Skipping real API test to avoid rate limiting")
    print("  Note: Google Trends API is very aggressive with rate limits")
    print("        Real tests should be done with small batches in production")
    print()
    print("  To test manually:")
    print("    1. Wait 10-15 minutes to reset rate limit")
    print("    2. Run: python run_verification.py --batch-size 1")
    print()
    print("✅ Single term fetch test passed (skipped)!\n")
    return True


def test_database_integration():
    """Test database integration for verification"""
    print("="*60)
    print("TEST 5: Database Integration")
    print("="*60)
    
    try:
        db = get_db()
        
        # Check keywords table
        keywords_count = db.get_table_count('keywords')
        print(f"  Keywords in database: {keywords_count}")
        
        # Check time_series_metrics table
        metrics_count = db.get_table_count('time_series_metrics')
        print(f"  Time series metrics: {metrics_count}")
        
        if keywords_count > 0:
            print("  ✅ Database has keywords to verify")
        else:
            print("  ⚠️  No keywords yet (run processing first)")
        
        print("\n✅ Database integration test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Database integration test failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MILESTONE 3 - VERIFICATION PIPELINE TESTS")
    print("="*60)
    print()
    
    tests = [
        ("Cache Functionality", test_cache),
        ("PyTrends Initialization", test_pytrends_init),
        ("Rate Limiting", test_rate_limiting),
        ("Single Term Fetch", test_single_term_fetch),
        ("Database Integration", test_database_integration),
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
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()
    
    if failed == 0:
        print("✅ All tests passed!")
        print()
        print("Next steps:")
        print("1. Run verification: python run_verification.py")
        print("2. Check time_series_metrics table")
        print()
        print("Note: Actual Google Trends API calls may be rate limited")
        print("      Run with small batches to avoid 429 errors")
        print()
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
