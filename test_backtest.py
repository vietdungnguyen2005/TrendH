"""
Test suite for Backtest Framework (Milestone 5)
Tests ground truth labeling and backtest metrics
"""

import sys
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).parent))

from backtest.labeling import GroundTruthLabeler
from backtest.backtest_runner import BacktestRunner
from utils.db_utils import get_db


def test_ground_truth_criteria():
    """Test 1: Ground truth criteria work correctly"""
    print("\nTest 1: Ground Truth Criteria")
    print("-" * 50)
    
    labeler = GroundTruthLabeler()
    
    # Test with mock time series data
    time_series = [
        ('2026-01-01 00:00:00', 10),
        ('2026-01-02 00:00:00', 15),
        ('2026-01-03 00:00:00', 30),  # 200% growth from day 1
        ('2026-01-04 00:00:00', 45),
        ('2026-01-05 00:00:00', 50),
    ]
    
    # Check IOT growth criterion
    growth_met, max_growth = labeler.check_iot_growth_criterion(time_series)
    
    print(f"Time series: {[(t.split()[0], v) for t, v in time_series]}")
    print(f"IOT Growth: {max_growth:.1f}%")
    print(f"Meets IOT Growth criterion (≥100%): {growth_met}")
    
    assert growth_met, "Should detect 200% growth"
    assert max_growth >= 200, f"Expected ≥200% growth, got {max_growth:.1f}%"
    
    # Test sustained interest
    time_series_sustained = [
        ('2026-01-01 00:00:00', 75),
        ('2026-01-02 00:00:00', 80),
        ('2026-01-03 00:00:00', 85),  # 3 consecutive days ≥70
        ('2026-01-04 00:00:00', 60),
    ]
    
    sustained_met, max_consecutive = labeler.check_sustained_interest_criterion(time_series_sustained)
    
    print(f"\nSustained IOT: {max_consecutive} consecutive days ≥70")
    print(f"Meets Sustained Interest criterion (≥3 days): {sustained_met}")
    
    assert sustained_met, "Should detect 3 consecutive days ≥70"
    assert max_consecutive >= 3, f"Expected ≥3 days, got {max_consecutive}"
    
    print("✓ Test 1 PASSED\n")


def test_labeling_process():
    """Test 2: Labeling process works correctly"""
    print("\nTest 2: Labeling Process")
    print("-" * 50)
    
    labeler = GroundTruthLabeler()
    db = get_db()
    
    # Get existing flags count
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM flags')
        flags_count = cur.fetchone()[0]
    
    print(f"Total flags in database: {flags_count}")
    
    # Label all flags
    stats = labeler.label_all_flags()
    
    print(f"Labeling results:")
    print(f"  Total: {stats['total']}")
    print(f"  Confirmed: {stats['confirmed']}")
    print(f"  False Positives: {stats['false_positive']}")
    print(f"  Failed: {stats['failed']}")
    
    assert stats['total'] == flags_count, "Should label all flags"
    assert stats['failed'] == 0, "No labeling should fail"
    assert stats['confirmed'] + stats['false_positive'] == stats['total'], "All flags should be labeled"
    
    # Verify ground_truth table populated
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM ground_truth')
        gt_count = cur.fetchone()[0]
    
    print(f"Ground truth records: {gt_count}")
    
    assert gt_count > 0, "Ground truth table should have records"
    
    print("✓ Test 2 PASSED\n")


def test_precision_at_k():
    """Test 3: Precision@K calculation"""
    print("\nTest 3: Precision@K Calculation")
    print("-" * 50)
    
    runner = BacktestRunner()
    
    # Calculate for different K values
    for k in [10, 20, 50]:
        precision = runner.calculate_precision_at_k(k)
        print(f"Precision@{k}: {precision * 100:.1f}%")
        
        assert 0 <= precision <= 1, f"Precision should be 0-1, got {precision}"
    
    print("✓ Test 3 PASSED\n")


def test_recall_calculation():
    """Test 4: Recall calculation"""
    print("\nTest 4: Recall Calculation")
    print("-" * 50)
    
    runner = BacktestRunner()
    
    recall = runner.calculate_recall_at_window(7)
    print(f"Recall@7d: {recall * 100:.1f}%")
    
    assert 0 <= recall <= 1, f"Recall should be 0-1, got {recall}"
    
    print("✓ Test 4 PASSED\n")


def test_lead_time_calculation():
    """Test 5: Lead time calculation"""
    print("\nTest 5: Lead Time Calculation")
    print("-" * 50)
    
    runner = BacktestRunner()
    
    lead_time = runner.calculate_lead_time()
    
    print(f"Lead time statistics:")
    print(f"  Count: {lead_time['count']}")
    print(f"  Mean: {lead_time['mean']:.1f}h")
    print(f"  Median: {lead_time['median']:.1f}h")
    print(f"  Range: {lead_time['min']:.1f}h - {lead_time['max']:.1f}h")
    
    assert lead_time['count'] >= 0, "Count should be non-negative"
    
    if lead_time['count'] > 0:
        assert lead_time['mean'] >= 0, "Mean lead time should be non-negative"
        assert lead_time['median'] >= 0, "Median lead time should be non-negative"
    
    print("✓ Test 5 PASSED\n")


def test_backtest_report():
    """Test 6: Backtest report generation"""
    print("\nTest 6: Backtest Report Generation")
    print("-" * 50)
    
    runner = BacktestRunner()
    
    # Generate report
    report = runner.generate_backtest_report()
    
    print(f"Report generated at: {report['generated_at']}")
    print(f"Metrics included:")
    
    required_metrics = [
        'precision@10', 'precision@20', 'precision@50',
        'recall@7d', 'false_positive_rate',
        'lead_time_hours', 'total_flags',
        'confirmed_trends', 'false_positives'
    ]
    
    for metric in required_metrics:
        assert metric in report['metrics'], f"Missing metric: {metric}"
        print(f"  ✓ {metric}")
    
    # Save report
    success = runner.save_report(report, 'test_backtest_report.json')
    assert success, "Report should save successfully"
    
    print("\n✓ Test 6 PASSED\n")


def test_database_integrity():
    """Test 7: Database integrity after backtest"""
    print("\nTest 7: Database Integrity")
    print("-" * 50)
    
    db = get_db()
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Check flags table
        cur.execute('SELECT COUNT(*) FROM flags')
        flags_count = cur.fetchone()[0]
        print(f"Flags: {flags_count}")
        
        # Check ground_truth table
        cur.execute('SELECT COUNT(*) FROM ground_truth')
        gt_count = cur.fetchone()[0]
        print(f"Ground truth: {gt_count}")
        
        # Check for orphaned records
        cur.execute('''
            SELECT COUNT(*)
            FROM ground_truth g
            LEFT JOIN flags f ON g.term_id = f.term_id AND g.flag_date = f.date_time
            WHERE f.id IS NULL
        ''')
        orphaned = cur.fetchone()[0]
        print(f"Orphaned ground truth: {orphaned}")
        
        # Check for NULL values
        cur.execute('''
            SELECT COUNT(*) FROM ground_truth
            WHERE term_id IS NULL OR flag_date IS NULL
        ''')
        nulls = cur.fetchone()[0]
        print(f"NULL values: {nulls}")
    
    assert flags_count > 0, "Should have flags"
    assert orphaned == 0, "Should have no orphaned records"
    assert nulls == 0, "Should have no NULL values"
    
    print("✓ Test 7 PASSED\n")


def main():
    """Run all backtest tests"""
    print("\n" + "="*60)
    print("BACKTEST FRAMEWORK TEST SUITE")
    print("="*60)
    
    tests = [
        test_ground_truth_criteria,
        test_labeling_process,
        test_precision_at_k,
        test_recall_calculation,
        test_lead_time_calculation,
        test_backtest_report,
        test_database_integrity,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ TEST FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ TEST ERROR: {e}\n")
            failed += 1
    
    print("="*60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"         {failed} tests failed")
    print("="*60)
    print()
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
