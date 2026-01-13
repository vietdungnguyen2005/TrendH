"""
Base crawler class for Trend Hunter
Provides common functionality for all crawlers
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
import logging
from utils.db_utils import get_db
from utils.config_loader import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """Abstract base class for all crawlers"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.db = get_db()
        self.config = get_config()
        self.items_collected = 0
        self.items_failed = 0
        
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch data from source
        Must be implemented by subclasses
        Returns list of raw data dictionaries
        """
        pass
    
    def normalize_data(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw data to standard format
        Can be overridden by subclasses if needed
        """
        return {
            'timestamp': datetime.now(),
            'source': self.source_name,
            'platform_id': raw_item.get('id', ''),
            'author': raw_item.get('author', ''),
            'title': raw_item.get('title', ''),
            'text': raw_item.get('text', ''),
            'url': raw_item.get('url', ''),
            'score': raw_item.get('score', 0),
            'comments_count': raw_item.get('comments_count', 0),
            'meta_json': str(raw_item.get('meta', {})),
            'created_at': raw_item.get('created_at', datetime.now())
        }
    
    def save_to_db(self, items: List[Dict[str, Any]]) -> int:
        """
        Save normalized items to database
        Returns number of items saved
        """
        if not items:
            return 0
        
        saved_count = 0
        
        for item in items:
            try:
                normalized = self.normalize_data(item)
                
                # Check if item already exists (avoid duplicates)
                existing = self.db.execute_query(
                    "SELECT id FROM sources_raw WHERE source = ? AND platform_id = ?",
                    (normalized['source'], normalized['platform_id'])
                )
                
                if existing:
                    logger.debug(f"Item {normalized['platform_id']} already exists, skipping")
                    continue
                
                # Insert new item
                self.db.insert('sources_raw', normalized)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Failed to save item: {e}")
                self.items_failed += 1
        
        return saved_count
    
    def log_job(self, status: str, error_message: str = None):
        """Log job execution to jobs_log table"""
        job_data = {
            'job_name': f'{self.source_name}_crawler',
            'job_type': 'crawler',
            'status': status,
            'start_time': self.start_time if hasattr(self, 'start_time') else datetime.now(),
            'end_time': datetime.now() if status in ['completed', 'failed'] else None,
            'items_processed': self.items_collected,
            'error_message': error_message
        }
        
        if job_data['end_time'] and job_data['start_time']:
            duration = (job_data['end_time'] - job_data['start_time']).total_seconds()
            job_data['duration_seconds'] = duration
        
        self.db.insert('jobs_log', job_data)
    
    def run(self) -> Dict[str, Any]:
        """
        Main execution method
        Fetches data, saves to DB, and logs results
        """
        self.start_time = datetime.now()
        logger.info(f"Starting {self.source_name} crawler...")
        
        try:
            # Fetch data
            raw_items = self.fetch_data()
            logger.info(f"Fetched {len(raw_items)} items from {self.source_name}")
            
            # Save to database
            saved_count = self.save_to_db(raw_items)
            self.items_collected = saved_count
            
            logger.info(f"Saved {saved_count} new items to database")
            
            # Log success
            self.log_job('completed')
            
            return {
                'success': True,
                'source': self.source_name,
                'items_fetched': len(raw_items),
                'items_saved': saved_count,
                'items_failed': self.items_failed
            }
            
        except Exception as e:
            logger.error(f"Crawler failed: {e}", exc_info=True)
            self.log_job('failed', str(e))
            
            return {
                'success': False,
                'source': self.source_name,
                'error': str(e)
            }
