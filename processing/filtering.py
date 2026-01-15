"""
Filtering module for Trend Hunter
Rule-based filtering to remove spam, ads, political content
"""

import re
import logging
from typing import Dict, List, Any
from utils.config_loader import get_config
from utils.db_utils import get_db
import yaml

logger = logging.getLogger(__name__)


class ContentFilter:
    """Filter spam, ads, and unwanted content"""
    
    def __init__(self):
        self.config = get_config()
        self.db = get_db()
        
        # Load blacklist
        self.load_blacklist()
        
        # Compile regex patterns
        self.compile_patterns()
        
        logger.info("Content filter initialized")
    
    def load_blacklist(self):
        """Load blacklist from YAML file"""
        blacklist_file = self.config.get('processing.filtering.blacklist_file', 'config/blacklist.yaml')
        
        try:
            with open(blacklist_file, 'r', encoding='utf-8') as f:
                blacklist_data = yaml.safe_load(f)
            
            # Combine all blacklist categories
            self.spam_keywords = set(blacklist_data.get('spam_keywords', []))
            self.advertising_keywords = set(blacklist_data.get('advertising_keywords', []))
            self.political_keywords = set(blacklist_data.get('political_keywords', []))
            self.generic_terms = set(blacklist_data.get('generic_terms', []))
            self.crypto_spam = set(blacklist_data.get('crypto_spam', []))
            self.adult_content = set(blacklist_data.get('adult_content', []))
            
            # Combine all for quick lookup
            self.all_blacklisted = (
                self.spam_keywords | 
                self.advertising_keywords | 
                self.political_keywords | 
                self.generic_terms |
                self.crypto_spam |
                self.adult_content
            )
            
            logger.info(f"Loaded {len(self.all_blacklisted)} blacklisted terms")
            
        except FileNotFoundError:
            logger.warning(f"Blacklist file not found: {blacklist_file}")
            self.all_blacklisted = set()
    
    def compile_patterns(self):
        """Compile regex patterns for spam detection"""
        self.patterns = {
            # Promo codes: CODE123, SAVE20, etc.
            'promo_code': re.compile(r'\b[A-Z0-9]{4,10}\b(?=.*(?:code|promo|discount|save|off))', re.IGNORECASE),
            
            # Affiliate links
            'affiliate': re.compile(r'(?:amzn\.to|bit\.ly|goo\.gl|tinyurl|affiliate|ref=|tag=)', re.IGNORECASE),
            
            # Excessive caps (SPAM!!!!)
            'excessive_caps': re.compile(r'\b[A-Z]{5,}\b'),
            
            # Multiple exclamation marks
            'excessive_punctuation': re.compile(r'[!?]{3,}'),
            
            # Common spam phrases
            'spam_phrase': re.compile(r'(?:click here|limited time|act now|free shipping|order now)', re.IGNORECASE),
            
            # Emojis spam (simplified - checks for multiple emoji-like patterns)
            'emoji_spam': re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]{3,}'),
            
            # URLs with tracking parameters
            'tracking_url': re.compile(r'utm_|fbclid=|gclid='),
        }
    
    def check_blacklist(self, text: str) -> bool:
        """
        Check if text contains blacklisted terms
        Returns True if blacklisted (should filter out)
        """
        text_lower = text.lower()
        
        for term in self.all_blacklisted:
            if term.lower() in text_lower:
                logger.debug(f"Blacklisted term found: {term}")
                return True
        
        return False
    
    def check_spam_patterns(self, text: str) -> Dict[str, bool]:
        """
        Check text against spam patterns
        Returns dict of pattern matches
        """
        matches = {}
        
        for pattern_name, pattern in self.patterns.items():
            matches[pattern_name] = bool(pattern.search(text))
        
        return matches
    
    def calculate_spam_score(self, text: str, title: str = "") -> float:
        """
        Calculate spam score (0.0 - 1.0)
        Higher score = more likely spam
        """
        score = 0.0
        
        combined_text = f"{title} {text}".lower()
        
        # Check blacklist (heavy weight)
        if self.check_blacklist(combined_text):
            score += 0.4
        
        # Check spam patterns
        pattern_matches = self.check_spam_patterns(combined_text)
        
        # Weight each pattern
        weights = {
            'promo_code': 0.3,
            'affiliate': 0.25,
            'excessive_caps': 0.1,
            'excessive_punctuation': 0.05,
            'spam_phrase': 0.2,
            'emoji_spam': 0.1,
            'tracking_url': 0.15
        }
        
        for pattern, matched in pattern_matches.items():
            if matched:
                score += weights.get(pattern, 0.1)
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def check_length(self, text: str) -> bool:
        """
        Check if text length is within acceptable range
        Returns True if acceptable, False if too short/long
        """
        min_length = self.config.get('processing.filtering.min_post_length', 10)
        max_length = self.config.get('processing.filtering.max_post_length', 5000)
        
        text_length = len(text.strip())
        
        return min_length <= text_length <= max_length
    
    def is_valid_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if post should be kept or filtered
        
        Returns dict with:
        - is_valid: bool
        - reason: str (if filtered)
        - spam_score: float
        """
        title = post_data.get('title', '')
        text = post_data.get('text', '')
        combined = f"{title} {text}"
        
        # Check length
        if not self.check_length(combined):
            return {
                'is_valid': False,
                'reason': 'invalid_length',
                'spam_score': 0.0
            }
        
        # Calculate spam score
        spam_score = self.calculate_spam_score(text, title)
        spam_threshold = self.config.get('processing.filtering.spam_threshold', 0.7)
        
        if spam_score >= spam_threshold:
            return {
                'is_valid': False,
                'reason': 'spam_detected',
                'spam_score': spam_score
            }
        
        return {
            'is_valid': True,
            'reason': None,
            'spam_score': spam_score
        }
    
    def filter_posts(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Filter a batch of posts
        
        Returns:
        - valid_posts: list of posts that passed filter
        - filtered_count: number of filtered posts
        - stats: filtering statistics
        """
        valid_posts = []
        filtered_by_reason = {}
        spam_scores = []
        
        for post in posts:
            result = self.is_valid_post(post)
            spam_scores.append(result['spam_score'])
            
            if result['is_valid']:
                valid_posts.append(post)
            else:
                reason = result['reason']
                filtered_by_reason[reason] = filtered_by_reason.get(reason, 0) + 1
        
        stats = {
            'total_posts': len(posts),
            'valid_posts': len(valid_posts),
            'filtered_posts': len(posts) - len(valid_posts),
            'filtered_by_reason': filtered_by_reason,
            'avg_spam_score': sum(spam_scores) / len(spam_scores) if spam_scores else 0,
            'filter_rate': (len(posts) - len(valid_posts)) / len(posts) if posts else 0
        }
        
        logger.info(f"Filtered {stats['filtered_posts']}/{stats['total_posts']} posts ({stats['filter_rate']:.1%})")
        
        return {
            'valid_posts': valid_posts,
            'filtered_count': stats['filtered_posts'],
            'stats': stats
        }
    
    def filter_from_db(self, limit: int = 1000) -> Dict[str, Any]:
        """
        Filter posts from database sources_raw table
        Returns filtering results
        """
        # Get unprocessed posts from DB
        query = """
            SELECT id, source, title, text, author, score, created_at
            FROM sources_raw
            WHERE id NOT IN (SELECT DISTINCT source_id FROM keywords WHERE source_id IS NOT NULL)
            LIMIT ?
        """
        
        posts = self.db.execute_query(query, (limit,))
        
        if not posts:
            logger.info("No unprocessed posts found")
            return {
                'valid_posts': [],
                'filtered_count': 0,
                'stats': {}
            }
        
        # Convert to list of dicts
        posts_list = [dict(post) for post in posts]
        
        # Filter
        result = self.filter_posts(posts_list)
        
        return result


def main():
    """Test the content filter"""
    print("Testing Content Filter...")
    
    # Create filter
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
        {
            'title': 'Check my bio',
            'text': 'Link in bio for promo code!'
        }
    ]
    
    print("\n" + "="*60)
    for i, post in enumerate(test_posts, 1):
        result = filter.is_valid_post(post)
        status = "✅ VALID" if result['is_valid'] else "❌ FILTERED"
        print(f"\nTest {i}: {status}")
        print(f"Title: {post['title']}")
        print(f"Spam Score: {result['spam_score']:.2f}")
        if not result['is_valid']:
            print(f"Reason: {result['reason']}")
    
    print("\n" + "="*60)
    
    # Test batch filtering
    batch_result = filter.filter_posts(test_posts)
    print(f"\n📊 Batch Filtering Stats:")
    print(f"Total: {batch_result['stats']['total_posts']}")
    print(f"Valid: {batch_result['stats']['valid_posts']}")
    print(f"Filtered: {batch_result['stats']['filtered_posts']}")
    print(f"Filter Rate: {batch_result['stats']['filter_rate']:.1%}")
    
    print("\n✅ Filter test completed!")


if __name__ == "__main__":
    main()
