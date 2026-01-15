"""
Main processing pipeline for Trend Hunter
Orchestrates filtering, entity extraction, and normalization
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from processing.filtering import ContentFilter
from processing.entity_extraction import EntityExtractor
from processing.normalization import EntityNormalizer
from utils.db_utils import get_db
from utils.config_loader import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Main processing pipeline"""
    
    def __init__(self):
        self.config = get_config()
        self.db = get_db()
        
        # Initialize components
        self.filter = ContentFilter()
        self.extractor = EntityExtractor()
        self.normalizer = EntityNormalizer()
        
        self.stats = {
            'posts_processed': 0,
            'posts_filtered': 0,
            'entities_extracted': 0,
            'keywords_created': 0
        }
        
        logger.info("Processing pipeline initialized")
    
    def fetch_unprocessed_posts(self, limit: int = 1000) -> List[Dict]:
        """
        Fetch unprocessed posts from sources_raw table
        Returns list of post dicts
        """
        # Simple query: get all recent posts
        query = """
            SELECT 
                id, source, platform_id, author, title, text, 
                url, score, comments_count, created_at
            FROM sources_raw
            ORDER BY id DESC
            LIMIT ?
        """
        
        posts = self.db.execute_query(query, (limit,))
        posts_list = [dict(post) for post in posts]
        
        logger.info(f"Fetched {len(posts_list)} unprocessed posts")
        return posts_list
    
    def step1_filter_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Step 1: Filter out spam and invalid posts
        """
        logger.info(f"Step 1: Filtering {len(posts)} posts...")
        
        result = self.filter.filter_posts(posts)
        valid_posts = result['valid_posts']
        
        self.stats['posts_processed'] = result['stats']['total_posts']
        self.stats['posts_filtered'] = result['stats']['filtered_posts']
        
        logger.info(f"Filtered: {self.stats['posts_filtered']}/{self.stats['posts_processed']} posts")
        logger.info(f"Valid posts: {len(valid_posts)}")
        
        return valid_posts
    
    def step2_extract_entities(self, posts: List[Dict]) -> Dict[str, int]:
        """
        Step 2: Extract entities (keywords/products) from posts
        """
        logger.info(f"Step 2: Extracting entities from {len(posts)} posts...")
        
        entity_counts = self.extractor.extract_entities_from_posts(posts)
        
        self.stats['entities_extracted'] = len(entity_counts)
        
        logger.info(f"Extracted {self.stats['entities_extracted']} unique entities")
        
        # Log top entities
        top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        logger.info("Top 10 entities:")
        for entity, count in top_entities:
            logger.info(f"  {entity}: {count}")
        
        return entity_counts
    
    def step3_normalize_entities(self, entity_counts: Dict[str, int]) -> List[Dict]:
        """
        Step 3: Normalize entities and group variants
        """
        logger.info(f"Step 3: Normalizing {len(entity_counts)} entities...")
        
        normalized_entities = self.normalizer.normalize_entity_list(entity_counts)
        
        logger.info(f"Normalized to {len(normalized_entities)} canonical terms")
        
        # Log top normalized
        logger.info("Top 10 canonical terms:")
        for item in normalized_entities[:10]:
            logger.info(f"  {item['canonical_term']}: {item['total_mentions']} mentions")
        
        return normalized_entities
    
    def step4_save_keywords(self, normalized_entities: List[Dict]) -> int:
        """
        Step 4: Save normalized entities to keywords table
        """
        logger.info(f"Step 4: Saving {len(normalized_entities)} keywords to database...")
        
        saved_count = 0
        
        for entity_data in normalized_entities:
            try:
                # Check if keyword already exists
                existing = self.db.execute_query(
                    "SELECT id, total_mentions FROM keywords WHERE canonical_term = ?",
                    (entity_data['canonical_term'],)
                )
                
                if existing:
                    # Update existing keyword
                    keyword_id = existing[0]['id']
                    old_mentions = existing[0]['total_mentions']
                    new_mentions = old_mentions + entity_data['total_mentions']
                    
                    update_query = """
                        UPDATE keywords 
                        SET total_mentions = ?, 
                            last_seen = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP,
                            variants_json = ?
                        WHERE id = ?
                    """
                    self.db.execute_query(
                        update_query, 
                        (new_mentions, entity_data['variants_json'], keyword_id)
                    )
                    logger.debug(f"Updated keyword: {entity_data['canonical_term']}")
                else:
                    # Insert new keyword
                    insert_data = {
                        'canonical_term': entity_data['canonical_term'],
                        'variants_json': entity_data['variants_json'],
                        'total_mentions': entity_data['total_mentions'],
                        'first_seen': datetime.now(),
                        'last_seen': datetime.now(),
                        'is_active': 1
                    }
                    self.db.insert('keywords', insert_data)
                    saved_count += 1
                    logger.debug(f"Inserted keyword: {entity_data['canonical_term']}")
                
            except Exception as e:
                logger.error(f"Error saving keyword {entity_data['canonical_term']}: {e}")
                continue
        
        self.stats['keywords_created'] = saved_count
        logger.info(f"Saved {saved_count} new keywords")
        
        return saved_count
    
    def run(self, batch_size: int = 1000) -> Dict[str, Any]:
        """
        Run the complete processing pipeline
        """
        start_time = datetime.now()
        logger.info("Starting Processing Pipeline")
        logger.info("=" * 60)
        
        try:
            # Ensure logs directory exists
            Path('logs').mkdir(exist_ok=True)
            
            # Fetch unprocessed posts
            posts = self.fetch_unprocessed_posts(limit=batch_size)
            
            if not posts:
                logger.info("No unprocessed posts found")
                return {
                    'success': True,
                    'message': 'No posts to process',
                    'stats': self.stats
                }
            
            # Step 1: Filter
            valid_posts = self.step1_filter_posts(posts)
            
            if not valid_posts:
                logger.warning("All posts were filtered out")
                return {
                    'success': True,
                    'message': 'All posts filtered',
                    'stats': self.stats
                }
            
            # Step 2: Extract entities
            entity_counts = self.step2_extract_entities(valid_posts)
            
            if not entity_counts:
                logger.warning("No entities extracted")
                return {
                    'success': True,
                    'message': 'No entities found',
                    'stats': self.stats
                }
            
            # Step 3: Normalize
            normalized_entities = self.step3_normalize_entities(entity_counts)
            
            # Step 4: Save to database
            self.step4_save_keywords(normalized_entities)
            
            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Print summary
            logger.info("=" * 60)
            logger.info("PROCESSING PIPELINE SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Posts processed: {self.stats['posts_processed']}")
            logger.info(f"Posts filtered: {self.stats['posts_filtered']}")
            logger.info(f"Valid posts: {self.stats['posts_processed'] - self.stats['posts_filtered']}")
            logger.info(f"Entities extracted: {self.stats['entities_extracted']}")
            logger.info(f"Keywords created: {self.stats['keywords_created']}")
            logger.info("=" * 60)
            logger.info("Processing pipeline completed")
            
            return {
                'success': True,
                'duration_seconds': duration,
                'stats': self.stats
            }
            
        except Exception as e:
            logger.error(f"Processing pipeline failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }


def main():
    """Main entry point"""
    try:
        pipeline = ProcessingPipeline()
        result = pipeline.run()
        
        if result['success']:
            return 0
        else:
            logger.error(f"Pipeline failed: {result.get('error')}")
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
