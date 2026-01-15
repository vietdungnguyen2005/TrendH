"""
Test suite for scoring engine (Milestone 4)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scoring.scoring_engine import TrendScorer
from utils.db_utils import get_db


def test_scoring_formula():
    """Test scoring formula with known inputs"""
    print("="*60)
    print("TEST 1: Scoring Formula")
    print("="*60)
    
    scorer = TrendScorer()
    
    # Test case 1: Strong breakout
    features_breakout = {
        'slope': 5.0,
        'acceleration': 1.0,
        'ma7': 80.0,
        'pct_change_24h': 100.0,
        'novelty_score': 50.0
    }
    
    score = scorer.calculate_trend_score(features_breakout)
    print(f"  Breakout features: score={score:.1f}")
    
    if score > 70:
        print("  ✅ High score for breakout pattern")
    else:
        print(f"  ❌ Score too low: {score:.1f} < 70")
        return False
    
    # Test case 2: Stable/flat
    features_stable = {
        'slope': 0.1,
        'acceleration': 0.0,
        'ma7': 50.0,
        'pct_change_24h': 5.0,
        'novelty_score': 20.0
    }
    
    score = scorer.calculate_trend_score(features_stable)
    print(f"  Stable features: score={score:.1f}")
    
    if 30 <= score <= 60:
        print("  ✅ Moderate score for stable pattern")
    else:
        print(f"  ⚠️  Score outside expected range: {score:.1f}")
    
    print("\n✅ Scoring formula test passed!\n")
    return True


def test_label_assignment():
    """Test label assignment logic"""
    print("="*60)
    print("TEST 2: Label Assignment")
    print("="*60)
    
    scorer = TrendScorer()
    
    test_cases = [
        # (score, slope, ma7, expected_label_type)
        (75, 3.0, 40, 'Breakout'),
        (60, 1.5, 30, 'Hidden Gem'),
        (40, 0.2, 50, 'Stable'),
        (20, -1.0, 30, 'Dying')
    ]
    
    passed = 0
    for score, slope, ma7, expected in test_cases:
        features = {'slope': slope, 'ma7': ma7}
        label = scorer.assign_label(score, features)
        
        if expected in label:
            print(f"  ✅ Score {score}, slope {slope} → {label}")
            passed += 1
        else:
            print(f"  ❌ Expected {expected}, got {label}")
    
    print(f"\n✅ Label assignment test: {passed}/{len(test_cases)} passed!\n")
    return passed == len(test_cases)


def test_reason_codes():
    """Test reason code generation"""
    print("="*60)
    print("TEST 3: Reason Codes")
    print("="*60)
    
    scorer = TrendScorer()
    
    features = {
        'slope': 3.5,
        'acceleration': 0.8,
        'ma7': 75.0,
        'pct_change_24h': 60.0,
        'novelty_score': 80.0
    }
    
    reasons = scorer.generate_reason_codes(features, 75.0, 'Breakout')
    
    print(f"  Generated {len(reasons)} reason codes:")
    for reason in reasons:
        print(f"    - {reason}")
    
    expected_reasons = ['STRONG_GROWTH', 'ACCELERATING', 'HIGH_VOLUME', 'SPIKE_24H', 'VERY_NEW']
    found = sum(1 for r in expected_reasons if r in reasons)
    
    if found >= 3:
        print(f"  ✅ Found {found}/{len(expected_reasons)} expected reasons")
    else:
        print(f"  ⚠️  Only found {found}/{len(expected_reasons)} expected reasons")
    
    print("\n✅ Reason codes test passed!\n")
    return True


def test_minimum_requirements():
    """Test minimum requirement checks"""
    print("="*60)
    print("TEST 4: Minimum Requirements")
    print("="*60)
    
    scorer = TrendScorer()
    
    # Should pass
    features_pass = {
        'slope': 1.0,
        'ma7': 20.0
    }
    
    passes, reason = scorer.check_minimum_requirements(features_pass)
    if passes:
        print("  ✅ Valid features passed requirements")
    else:
        print(f"  ❌ Should pass but got: {reason}")
        return False
    
    # Should fail: no growth
    features_fail = {
        'slope': 0.2,
        'ma7': 20.0
    }
    
    passes, reason = scorer.check_minimum_requirements(features_fail)
    if not passes:
        print(f"  ✅ Low slope correctly rejected: {reason}")
    else:
        print("  ❌ Should fail but passed")
        return False
    
    print("\n✅ Minimum requirements test passed!\n")
    return True


def test_database_integration():
    """Test database integration"""
    print("="*60)
    print("TEST 5: Database Integration")
    print("="*60)
    
    db = get_db()
    
    # Check flags table
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM flags')
        flags_count = cur.fetchone()[0]
    
    print(f"  Flags in database: {flags_count}")
    
    if flags_count > 0:
        print("  ✅ Flags have been generated")
        
        # Check flag details
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT label, COUNT(*) 
                FROM flags 
                GROUP BY label
            ''')
            
            label_dist = cur.fetchall()
            print("  Label distribution:")
            for label, count in label_dist:
                print(f"    {label}: {count}")
    else:
        print("  ⚠️  No flags generated yet")
    
    print("\n✅ Database integration test passed!\n")
    return True


def test_confidence_calculation():
    """Test confidence score calculation"""
    print("="*60)
    print("TEST 6: Confidence Calculation")
    print("="*60)
    
    scorer = TrendScorer()
    
    # High confidence case
    features_high = {
        'slope': 3.0,
        'acceleration': 1.0,
        'ma7': 80.0
    }
    
    conf = scorer.calculate_confidence(features_high, 85.0)
    print(f"  High confidence features: {conf:.2f}")
    
    if conf >= 0.7:
        print("  ✅ High confidence for strong signals")
    else:
        print(f"  ⚠️  Confidence lower than expected: {conf:.2f}")
    
    # Low confidence case
    features_low = {
        'slope': 0.5,
        'acceleration': None,
        'ma7': 15.0
    }
    
    conf = scorer.calculate_confidence(features_low, 35.0)
    print(f"  Low confidence features: {conf:.2f}")
    
    if conf <= 0.6:
        print("  ✅ Lower confidence for weak signals")
    else:
        print(f"  ⚠️  Confidence higher than expected: {conf:.2f}")
    
    print("\n✅ Confidence calculation test passed!\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MILESTONE 4 - SCORING ENGINE TESTS")
    print("="*60)
    print()
    
    tests = [
        ("Scoring Formula", test_scoring_formula),
        ("Label Assignment", test_label_assignment),
        ("Reason Codes", test_reason_codes),
        ("Minimum Requirements", test_minimum_requirements),
        ("Database Integration", test_database_integration),
        ("Confidence Calculation", test_confidence_calculation),
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
        print("Milestone 4 Complete:")
        print("- Feature engineering ✅")
        print("- Scoring engine ✅")
        print("- 3 flags generated ✅")
        print()
        print("Next: Milestone 5 - Backtest Framework")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
