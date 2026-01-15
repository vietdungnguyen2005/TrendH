"""
One-time full pipeline execution for Trend Hunter
Runs all steps sequentially for testing/manual execution
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Import actual module names (not class names)
import importlib


def run_full_pipeline(crawl=True, process=True, verify=True, 
                      features=True, score=True, alert=True):
    """
    Execute full pipeline
    
    Args:
        crawl: Run crawlers
        process: Run processing
        verify: Run verification
        features: Calculate features
        score: Run scoring
        alert: Send alerts
    """
    print("\n" + "="*60)
    print("TREND HUNTER - FULL PIPELINE EXECUTION")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    results = {}
    
    # Import modules as needed
    from utils.db_utils import get_db
    
    # Step 1: Crawl (skipped - would need actual API keys)
    if crawl:
        print("STEP 1: CRAWLING")
        print("-" * 60)
        print("⚠ Skipped (requires API credentials)")
        print("  Run: python run_crawler.py")
        print()
        results['reddit_posts'] = 0
        results['tiktok_posts'] = 0
    
    # Step 2: Process
    if process:
        print("STEP 2: PROCESSING")
        print("-" * 60)
        
        try:
            from processing.keyword_extractor import KeywordExtractor
            from processing.keyword_normalizer import KeywordNormalizer
            
            # Extract keywords
            logger.info("Extracting keywords...")
            extractor = KeywordExtractor()
            keywords = extractor.extract_from_recent_posts(days=7)
            results['keywords_extracted'] = len(keywords)
            logger.info(f"  Extracted {len(keywords)} keywords")
            
            # Normalize
            logger.info("Normalizing variants...")
            normalizer = KeywordNormalizer()
            normalized = normalizer.normalize_all()
            results['keywords_normalized'] = normalized
            logger.info(f"  Normalized {normalized} keyword groups")
            
            print(f"✓ Processed {len(keywords)} keywords → {normalized} groups")
            print()
        
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            results['process_error'] = str(e)
    
    # Step 3: Verify
    if verify:
        print("STEP 3: VERIFICATION")
        print("-" * 60)
        
        try:
            from verification.pytrends_wrapper import PyTrendsWrapper
            
            logger.info("Verifying with Google Trends...")
            wrapper = PyTrendsWrapper()
            keywords = wrapper.get_unverified_keywords(limit=50)
            
            verified = 0
            for keyword in keywords[:10]:  # Limit for demo
                try:
                    success = wrapper.sample_keyword(keyword, n_samples=3)
                    if success:
                        verified += 1
                        logger.info(f"  ✓ {keyword}")
                except Exception as e:
                    logger.warning(f"  ✗ {keyword}: {e}")
            
            results['keywords_verified'] = verified
            print(f"✓ Verified {verified} keywords")
            print()
        
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            results['verify_error'] = str(e)
    
    # Step 4: Features
    if features:
        print("STEP 4: FEATURE ENGINEERING")
        print("-" * 60)
        from processing.feature_engineering import FeatureEngineer
            
            
        try:
            logger.info("Calculating features...")
            engineer = FeatureEngineer()
            keywords = engineer.get_keywords_needing_features()
            
            computed = 0
            for keyword_id, term in keywords[:20]:  # Limit for demo
                try:
                    features = engineer.compute_features_for_keyword(keyword_id)
                    if features:
                        engineer.save_features(keyword_id, features)
                        computed += 1
                        logger.info(f"  ✓ {term}")
                except Exception as e:
                    logger.warning(f"  ✗ {term}: {e}")
            
            results['features_computed'] = computed
            print(f"✓ Computed features for {computed} keywords")
            print()
        
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            results['features_error'] = str(e)
    
    # Step 5: Score
    if score:
        print("STEP 5: SCORING")
        print("-" * 60)
        from scoring.scoring_engine import TrendScorer
            
            
        try:
            logger.info("Scoring trends...")
            scorer = TrendScorer()
            keywords = scorer.get_keywords_needing_scoring()
            
            flagged = 0
            for keyword_id, term in keywords[:20]:  # Limit for demo
                try:
                    result = scorer.score_keyword(keyword_id)
                    if result and result['should_flag']:
                        scorer.save_flag(keyword_id, result)
                        flagged += 1
                        logger.info(f"  🔥 {term}: {result['score']:.1f} ({result['label']})")
                except Exception as e:
                    logger.warning(f"  ✗ {term}: {e}")
            
            results['flags_generated'] = flagged
            print(f"✓ Generated {flagged} flags")
            print()
        
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            results['scoring_error'] = str(e)
    
    # Step 6: Alert
    if alert:
        print("STEP 6: ALERTS")
        print("-" * 60)
        
        try:
            from ui.alert_service import AlertService
            
            logger.info("Sending alerts...")
            service = AlertService(confidence_threshold=0.7, score_threshold=70.0)
            stats = service.process_alerts()
            
            results['alerts_sent'] = stats['sent']
            results['alerts_failed'] = stats['failed']
            
            print(f"✓ Sent {stats['sent']} alerts ({stats['failed']} failed)")
            print()
        
        except Exception as e:
            logger.error(f"Alerts failed: {e}")
            results['alert_error'] = str(e)
    
    # Summary
    print("="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    
    if 'reddit_posts' in results:
        print(f"Crawled:    {results.get('reddit_posts', 0)} Reddit + {results.get('tiktok_posts', 0)} TikTok posts")
    
    if 'keywords_extracted' in results:
        print(f"Extracted:  {results['keywords_extracted']} keywords")
    
    if 'keywords_normalized' in results:
        print(f"Normalized: {results['keywords_normalized']} groups")
    
    if 'keywords_verified' in results:
        print(f"Verified:   {results['keywords_verified']} keywords")
    
    if 'features_computed' in results:
        print(f"Features:   {results['features_computed']} computed")
    
    if 'flags_generated' in results:
        print(f"Flags:      {results['flags_generated']} generated")
    
    if 'alerts_sent' in results:
        print(f"Alerts:     {results['alerts_sent']} sent")
    
    # Database stats
    from utils.db_utils import get_db
    db = get_db()
    print()
    print("Database Status:")
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        cur.execute('SELECT COUNT(*) FROM sources_raw')
        print(f"  Posts:       {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM keywords')
        print(f"  Keywords:    {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM time_series_metrics')
        print(f"  Time series: {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM features')
        print(f"  Features:    {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM flags')
        print(f"  Flags:  ECT COUNT(*) FROM features')
        print(f"  Features:  {cur.fetchone()[0]}")
        
        cur.execute('SELECT COUNT(*) FROM flags')
        print(f"  Flags:     {cur.fetchone()[0]}")
    
    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    return results


def main():
    """Run full pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Trend Hunter pipeline')
    parser.add_argument('--skip-crawl', action='store_true', help='Skip crawling')
    parser.add_argument('--skip-process', action='store_true', help='Skip processing')
    parser.add_argument('--skip-verify', action='store_true', help='Skip verification')
    parser.add_argument('--skip-features', action='store_true', help='Skip features')
    parser.add_argument('--skip-score', action='store_true', help='Skip scoring')
    parser.add_argument('--skip-alert', action='store_true', help='Skip alerts')
    
    args = parser.parse_args()
    
    run_full_pipeline(
        crawl=not args.skip_crawl,
        process=not args.skip_process,
        verify=not args.skip_verify,
        features=not args.skip_features,
        score=not args.skip_score,
        alert=not args.skip_alert
    )


if __name__ == "__main__":
    main()
