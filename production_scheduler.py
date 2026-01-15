"""
Production Scheduler for Trend Hunter (Milestone 7)
Automated pipeline execution with APScheduler
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import traceback

sys.path.insert(0, str(Path(__file__).parent))

from crawler.reddit_crawler import RedditCrawler
from crawler.tiktok_crawler import TikTokCrawler
from processing.keyword_extractor import KeywordExtractor
from processing.keyword_normalizer import KeywordNormalizer
from verification.pytrends_wrapper import PyTrendsWrapper
from processing.feature_engineering import FeatureEngineer
from scoring.scoring_engine import TrendScorer
from backtest.labeling import GroundTruthLabeler
from ui.alert_service import AlertService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrendHunterScheduler:
    """Main scheduler coordinating all pipeline tasks"""
    
    def __init__(self, config: dict = None):
        """
        Initialize scheduler
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()
        self.scheduler = BlockingScheduler()
        
        # Track job statistics
        self.stats = {
            'crawl': {'total': 0, 'success': 0, 'failed': 0},
            'process': {'total': 0, 'success': 0, 'failed': 0},
            'verify': {'total': 0, 'success': 0, 'failed': 0},
            'features': {'total': 0, 'success': 0, 'failed': 0},
            'scoring': {'total': 0, 'success': 0, 'failed': 0},
            'alerts': {'total': 0, 'success': 0, 'failed': 0}
        }
        
        logger.info("Scheduler initialized")
    
    def _default_config(self) -> dict:
        """Default configuration"""
        return {
            # Crawling schedule (every 6 hours)
            'crawl_interval_hours': 6,
            
            # Processing schedule (every 2 hours)
            'process_interval_hours': 2,
            
            # Verification schedule (every 4 hours)
            'verify_interval_hours': 4,
            
            # Feature engineering schedule (every 4 hours)
            'features_interval_hours': 4,
            
            # Scoring schedule (every 4 hours)
            'scoring_interval_hours': 4,
            
            # Alerts schedule (every 1 hour)
            'alerts_interval_hours': 1,
            
            # Backtest schedule (daily at 3 AM)
            'backtest_cron': '0 3 * * *',
            
            # Retry configuration
            'max_retries': 3,
            'retry_delay_seconds': 60
        }
    
    def _safe_execute(self, job_name: str, func, *args, **kwargs):
        """
        Execute job with error handling and statistics
        
        Args:
            job_name: Name of the job for logging
            func: Function to execute
            *args, **kwargs: Arguments for function
        """
        self.stats[job_name]['total'] += 1
        
        try:
            logger.info(f"Starting job: {job_name}")
            result = func(*args, **kwargs)
            self.stats[job_name]['success'] += 1
            logger.info(f"Job completed: {job_name}")
            return result
        
        except Exception as e:
            self.stats[job_name]['failed'] += 1
            logger.error(f"Job failed: {job_name} - {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def job_crawl_reddit(self):
        """Crawl Reddit for new posts"""
        def _crawl():
            crawler = RedditCrawler()
            subreddits = ['smallbusiness', 'Entrepreneur']
            total = 0
            
            for subreddit in subreddits:
                count = crawler.crawl_subreddit(subreddit, limit=100)
                total += count
                logger.info(f"Crawled {count} posts from r/{subreddit}")
            
            return total
        
        return self._safe_execute('crawl', _crawl)
    
    def job_crawl_tiktok(self):
        """Crawl TikTok for trending data"""
        def _crawl():
            crawler = TikTokCrawler(headless=True)
            hashtags = ['smallbusiness', 'trending', 'viral']
            total = 0
            
            for hashtag in hashtags:
                count = crawler.crawl_hashtag(hashtag, limit=50)
                total += count
                logger.info(f"Crawled {count} posts from #{hashtag}")
            
            return total
        
        return self._safe_execute('crawl', _crawl)
    
    def job_process_keywords(self):
        """Extract and normalize keywords"""
        def _process():
            # Extract keywords
            extractor = KeywordExtractor()
            keywords = extractor.extract_from_recent_posts(days=7)
            logger.info(f"Extracted {len(keywords)} candidate keywords")
            
            # Normalize variants
            normalizer = KeywordNormalizer()
            normalized = normalizer.normalize_all()
            logger.info(f"Normalized {normalized} keyword groups")
            
            return len(keywords)
        
        return self._safe_execute('process', _process)
    
    def job_verify_trends(self):
        """Verify keywords with Google Trends"""
        def _verify():
            wrapper = PyTrendsWrapper()
            keywords = wrapper.get_unverified_keywords(limit=50)
            
            verified = 0
            for keyword in keywords:
                try:
                    success = wrapper.sample_keyword(keyword, n_samples=3)
                    if success:
                        verified += 1
                except Exception as e:
                    logger.warning(f"Verification failed for {keyword}: {e}")
            
            logger.info(f"Verified {verified}/{len(keywords)} keywords")
            return verified
        
        return self._safe_execute('verify', _verify)
    
    def job_calculate_features(self):
        """Calculate features for keywords"""
        def _calculate():
            engineer = FeatureEngineer()
            keywords = engineer.get_keywords_needing_features()
            
            computed = 0
            for keyword_id, term in keywords:
                try:
                    features = engineer.compute_features_for_keyword(keyword_id)
                    if features:
                        engineer.save_features(keyword_id, features)
                        computed += 1
                except Exception as e:
                    logger.warning(f"Feature calculation failed for {term}: {e}")
            
            logger.info(f"Computed features for {computed} keywords")
            return computed
        
        return self._safe_execute('features', _calculate)
    
    def job_score_trends(self):
        """Score keywords and generate flags"""
        def _score():
            scorer = TrendScorer()
            keywords = scorer.get_keywords_needing_scoring()
            
            flagged = 0
            for keyword_id, term in keywords:
                try:
                    result = scorer.score_keyword(keyword_id)
                    if result and result['should_flag']:
                        scorer.save_flag(keyword_id, result)
                        flagged += 1
                except Exception as e:
                    logger.warning(f"Scoring failed for {term}: {e}")
            
            logger.info(f"Generated {flagged} new flags")
            return flagged
        
        return self._safe_execute('scoring', _score)
    
    def job_send_alerts(self):
        """Send alerts for new flags"""
        def _alert():
            service = AlertService(
                confidence_threshold=0.7,
                score_threshold=70.0
            )
            
            stats = service.process_alerts()
            logger.info(f"Alerts: {stats['sent']} sent, {stats['failed']} failed")
            
            return stats['sent']
        
        return self._safe_execute('alerts', _alert)
    
    def job_run_backtest(self):
        """Run backtest and update ground truth"""
        def _backtest():
            labeler = GroundTruthLabeler()
            stats = labeler.label_all_flags()
            logger.info(f"Backtest: {stats['confirmed']} confirmed, {stats['false_positive']} false positives")
            
            return stats['confirmed']
        
        return self._safe_execute('backtest', _backtest)
    
    def job_health_check(self):
        """Periodic health check"""
        logger.info("=== HEALTH CHECK ===")
        logger.info(f"Job Statistics:")
        
        for job_name, stats in self.stats.items():
            total = stats['total']
            success = stats['success']
            failed = stats['failed']
            
            if total > 0:
                success_rate = (success / total) * 100
                logger.info(f"  {job_name}: {success}/{total} ({success_rate:.1f}% success)")
        
        logger.info("====================")
    
    def setup_jobs(self):
        """Configure all scheduled jobs"""
        config = self.config
        
        # Crawling jobs
        self.scheduler.add_job(
            self.job_crawl_reddit,
            IntervalTrigger(hours=config['crawl_interval_hours']),
            id='crawl_reddit',
            name='Crawl Reddit',
            max_instances=1
        )
        
        self.scheduler.add_job(
            self.job_crawl_tiktok,
            IntervalTrigger(hours=config['crawl_interval_hours']),
            id='crawl_tiktok',
            name='Crawl TikTok',
            max_instances=1
        )
        
        # Processing job
        self.scheduler.add_job(
            self.job_process_keywords,
            IntervalTrigger(hours=config['process_interval_hours']),
            id='process_keywords',
            name='Process Keywords',
            max_instances=1
        )
        
        # Verification job
        self.scheduler.add_job(
            self.job_verify_trends,
            IntervalTrigger(hours=config['verify_interval_hours']),
            id='verify_trends',
            name='Verify with Google Trends',
            max_instances=1
        )
        
        # Feature engineering job
        self.scheduler.add_job(
            self.job_calculate_features,
            IntervalTrigger(hours=config['features_interval_hours']),
            id='calculate_features',
            name='Calculate Features',
            max_instances=1
        )
        
        # Scoring job
        self.scheduler.add_job(
            self.job_score_trends,
            IntervalTrigger(hours=config['scoring_interval_hours']),
            id='score_trends',
            name='Score Trends',
            max_instances=1
        )
        
        # Alerts job
        self.scheduler.add_job(
            self.job_send_alerts,
            IntervalTrigger(hours=config['alerts_interval_hours']),
            id='send_alerts',
            name='Send Alerts',
            max_instances=1
        )
        
        # Backtest job (daily)
        self.scheduler.add_job(
            self.job_run_backtest,
            CronTrigger.from_crontab(config['backtest_cron']),
            id='run_backtest',
            name='Run Backtest',
            max_instances=1
        )
        
        # Health check (every 12 hours)
        self.scheduler.add_job(
            self.job_health_check,
            IntervalTrigger(hours=12),
            id='health_check',
            name='Health Check',
            max_instances=1
        )
        
        logger.info("All jobs configured")
    
    def start(self):
        """Start the scheduler"""
        logger.info("=" * 60)
        logger.info("TREND HUNTER SCHEDULER STARTING")
        logger.info("=" * 60)
        logger.info(f"Configuration:")
        logger.info(f"  Crawl interval: {self.config['crawl_interval_hours']}h")
        logger.info(f"  Process interval: {self.config['process_interval_hours']}h")
        logger.info(f"  Verify interval: {self.config['verify_interval_hours']}h")
        logger.info(f"  Features interval: {self.config['features_interval_hours']}h")
        logger.info(f"  Scoring interval: {self.config['scoring_interval_hours']}h")
        logger.info(f"  Alerts interval: {self.config['alerts_interval_hours']}h")
        logger.info(f"  Backtest schedule: {self.config['backtest_cron']}")
        logger.info("=" * 60)
        
        self.setup_jobs()
        
        # Print scheduled jobs
        logger.info("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (ID: {job.id})")
            logger.info(f"    Next run: {job.next_run_time}")
        
        logger.info("=" * 60)
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        logger.info("=" * 60)
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped by user")
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")
        
        # Print final statistics
        logger.info("=" * 60)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 60)
        
        for job_name, stats in self.stats.items():
            if stats['total'] > 0:
                success_rate = (stats['success'] / stats['total']) * 100
                logger.info(f"{job_name}:")
                logger.info(f"  Total: {stats['total']}")
                logger.info(f"  Success: {stats['success']}")
                logger.info(f"  Failed: {stats['failed']}")
                logger.info(f"  Success Rate: {success_rate:.1f}%")
        
        logger.info("=" * 60)


def main():
    """Run production scheduler"""
    # Custom configuration
    config = {
        'crawl_interval_hours': 6,
        'process_interval_hours': 2,
        'verify_interval_hours': 4,
        'features_interval_hours': 4,
        'scoring_interval_hours': 4,
        'alerts_interval_hours': 1,
        'backtest_cron': '0 3 * * *',  # 3 AM daily
        'max_retries': 3,
        'retry_delay_seconds': 60
    }
    
    scheduler = TrendHunterScheduler(config)
    scheduler.start()


if __name__ == "__main__":
    main()
