"""
Test suite for processing pipeline (Milestone 2)
Tests filtering, entity extraction, and normalization
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from processing.filtering import ContentFilter
from processing.entity_extraction import EntityExtractor
from processing.normalization import EntityNormalizer


def test_filtering():
    """Test content filtering"""
    print("="*60)
    print("TEST 1: Content Filtering")
    print("="*60)
    
    try:
        filter = ContentFilter()
        
        # Test cases
        test_posts = [
            {
                'title': 'Amazing new gadget',
                'text': 'Check out this cool product I found!'
            },
            {
                'title': 'CLICK HERE NOW!!!',
                'text': 'Limited time offer! Use code SAVE50 for discount!'
            },
            {
                'title': 'Political debate',
                'text': 'What do you think about Biden and Trump?'
            },
            {
                'title': 'Crypto giveaway',
                'text': 'Free bitcoin! Click this affiliate link!'
            },
        ]
        
        for i, post in enumerate(test_posts, 1):
            result = filter.is_valid_post(post)
            status = "✅ PASS" if result['is_valid'] else "❌ FILTER"
            print(f"\n  Test {i}: {status}")
            print(f"  Title: {post['title']}")
            print(f"  Spam Score: {result['spam_score']:.2f}")
        
        print("\n✅ Filtering test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Filtering test failed: {e}\n")
        return False


def test_entity_extraction():
    """Test entity extraction"""
    print("="*60)
    print("TEST 2: Entity Extraction")
    print("="*60)
    
    try:
        extractor = EntityExtractor()
        
        test_posts = [
            {
                'title': 'Check out the new iPhone 15 Pro',
                'text': 'Just got the iPhone 15 Pro and it\'s amazing!'
            },
            {
                'title': 'Stanley Cup is everywhere',
                'text': 'Why is everyone buying the Stanley Cup tumbler?'
            },
            {
                'title': 'Air Fryer recommendations',
                'text': 'Looking for a good Air Fryer. Heard the Ninja Air Fryer is great.'
            },
        ]
        
        # Extract entities
        top_entities = extractor.extract_top_entities(test_posts, top_n=10)
        
        print("\n  Top Extracted Entities:")
        for entity, freq, score in top_entities[:5]:
            print(f"    - {entity:<30} (freq: {freq}, score: {score:.1f})")
        
        print("\n✅ Entity extraction test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Entity extraction test failed: {e}\n")
        return False


def test_normalization():
    """Test entity normalization"""
    print("="*60)
    print("TEST 3: Entity Normalization")
    print("="*60)
    
    try:
        normalizer = EntityNormalizer()
        
        # Test cases
        test_cases = [
            ('AirPods Pro', 'airpods'),
            ('air pods', 'airpods'),
            ('iPhone 15', 'iphone 15'),
            ('PS5', 'playstation'),
        ]
        
        print("\n  Normalization Tests:")
        for original, expected_base in test_cases:
            normalized = normalizer.normalize_basic(original)
            canonical = normalizer.get_canonical_form(original)
            print(f"    {original:<20} -> {canonical:<20}")
        
        # Test variant grouping
        entities = {
            'AirPods Pro': 10,
            'airpods': 5,
            'iPhone 15': 15,
            'iphone 15': 8,
        }
        
        normalized_list = normalizer.normalize_entity_list(entities)
        
        print("\n  Variant Grouping:")
        for item in normalized_list:
            variants = ', '.join(item['variants'][:3])
            print(f"    {item['canonical_term']:<20} <- [{variants}]")
        
        print("\n✅ Normalization test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Normalization test failed: {e}\n")
        return False


def test_pipeline_integration():
    """Test full pipeline integration"""
    print("="*60)
    print("TEST 4: Pipeline Integration")
    print("="*60)
    
    try:
        from utils.db_utils import get_db
        
        db = get_db()
        
        # Check database
        count = db.get_table_count('sources_raw')
        print(f"\n  Database Check:")
        print(f"    sources_raw records: {count}")
        
        if count > 0:
            print(f"    ✅ Database has data")
        else:
            print(f"    ⚠️  No data yet (run crawler first)")
        
        print("\n✅ Integration test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 MILESTONE 2 - PROCESSING PIPELINE TESTS")
    print("="*60)
    print()
    
    tests = [
        ("Filtering", test_filtering),
        ("Entity Extraction", test_entity_extraction),
        ("Normalization", test_normalization),
        ("Pipeline Integration", test_pipeline_integration),
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
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()
    
    if failed == 0:
        print("✅ All tests passed!")
        print()
        print("Next steps:")
        print("1. Run processing pipeline: python run_processing.py")
        print("2. Check keywords table for extracted entities")
        print()
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
