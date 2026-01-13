"""
Main crawler runner script
Executes all configured crawlers and reports results
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from crawler.reddit import RedditCrawler
from crawler.tiktok import TikTokCrawler
from utils.config_loader import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/crawler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class CrawlerManager:
    """Manages and executes all crawlers"""
    
    def __init__(self):
        self.config = get_config()
        self.results = []
        
    def run_reddit_crawler(self):
        """Run Reddit crawler"""
        try:
            reddit_config = self.config.get('crawler.reddit', {})
            if not reddit_config.get('enabled', True):
                logger.info("Reddit crawler is disabled in config")
                return None
            
            logger.info("=" * 60)
            logger.info("Starting Reddit Crawler")
            logger.info("=" * 60)
            
            crawler = RedditCrawler()
            result = crawler.run()
            self.results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Reddit crawler failed: {e}", exc_info=True)
            return {'success': False, 'source': 'reddit', 'error': str(e)}
    
    def run_tiktok_crawler(self):
        """Run TikTok crawler"""
        try:
            tiktok_config = self.config.get('crawler.tiktok', {})
            if not tiktok_config.get('enabled', True):
                logger.info("TikTok crawler is disabled in config")
                return None
            
            logger.info("=" * 60)
            logger.info("Starting TikTok Crawler")
            logger.info("=" * 60)
            
            crawler = TikTokCrawler()
            result = crawler.run()
            self.results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"TikTok crawler failed: {e}", exc_info=True)
            return {'success': False, 'source': 'tiktok', 'error': str(e)}
    
    def run_all(self):
        """Run all enabled crawlers"""
        start_time = datetime.now()
        logger.info("🚀 Starting Trend Hunter Crawler Pipeline")
        logger.info(f"Start time: {start_time}")
        
        # Ensure logs directory exists
        Path('logs').mkdir(exist_ok=True)
        
        # Run crawlers
        reddit_result = self.run_reddit_crawler()
        tiktok_result = self.run_tiktok_crawler()
        
        # Calculate statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        total_fetched = sum(r.get('items_fetched', 0) for r in self.results if r)
        total_saved = sum(r.get('items_saved', 0) for r in self.results if r)
        total_failed = sum(r.get('items_failed', 0) for r in self.results if r)
        
        successful_crawlers = sum(1 for r in self.results if r and r.get('success'))
        total_crawlers = len([r for r in self.results if r])
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 CRAWLER PIPELINE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Successful crawlers: {successful_crawlers}/{total_crawlers}")
        logger.info(f"Total items fetched: {total_fetched}")
        logger.info(f"Total items saved: {total_saved}")
        logger.info(f"Total items failed: {total_failed}")
        logger.info("=" * 60)
        
        # Print individual results
        for result in self.results:
            if result:
                source = result.get('source', 'unknown')
                success = result.get('success', False)
                status = "✅ SUCCESS" if success else "❌ FAILED"
                
                logger.info(f"{status} - {source.upper()}")
                if success:
                    logger.info(f"   Fetched: {result.get('items_fetched', 0)}")
                    logger.info(f"   Saved: {result.get('items_saved', 0)}")
                    logger.info(f"   Failed: {result.get('items_failed', 0)}")
                else:
                    logger.info(f"   Error: {result.get('error', 'Unknown error')}")
        
        logger.info("=" * 60)
        logger.info("✅ Crawler pipeline completed")
        
        return {
            'success': successful_crawlers > 0,
            'duration_seconds': duration,
            'total_fetched': total_fetched,
            'total_saved': total_saved,
            'results': self.results
        }


def main():
    """Main entry point"""
    try:
        manager = CrawlerManager()
        summary = manager.run_all()
        
        # Exit with appropriate code
        if summary['success']:
            return 0
        else:
            logger.error("All crawlers failed")
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error in crawler pipeline: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
