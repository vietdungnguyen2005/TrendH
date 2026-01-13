"""
Reddit Crawler for Trend Hunter
Uses PRAW (Python Reddit API Wrapper) to collect posts from specified subreddits
"""

import praw
from typing import List, Dict, Any
from datetime import datetime
import logging
from crawler.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class RedditCrawler(BaseCrawler):
    """Crawler for Reddit data"""
    
    def __init__(self):
        super().__init__('reddit')
        
        # Get Reddit credentials from config
        reddit_config = self.config.get('crawler.reddit', {})
        
        self.client_id = reddit_config.get('client_id', '')
        self.client_secret = reddit_config.get('client_secret', '')
        self.user_agent = reddit_config.get('user_agent', 'TrendHunter/0.1')
        self.subreddits = reddit_config.get('subreddits', [])
        self.fetch_limit = reddit_config.get('fetch_limit', 100)
        self.time_filter = reddit_config.get('time_filter', 'day')
        
        # Validate credentials
        if not self.client_id or not self.client_secret:
            raise ValueError("Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
        
        # Initialize Reddit API
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
        
        logger.info(f"Reddit crawler initialized for subreddits: {self.subreddits}")
    
    def fetch_subreddit_posts(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Fetch posts from a single subreddit
        """
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Fetch hot posts (can be changed to 'new', 'top', etc.)
            for submission in subreddit.hot(limit=self.fetch_limit):
                try:
                    post_data = {
                        'id': submission.id,
                        'author': str(submission.author) if submission.author else '[deleted]',
                        'title': submission.title,
                        'text': submission.selftext,
                        'url': submission.url,
                        'score': submission.score,
                        'comments_count': submission.num_comments,
                        'created_at': datetime.fromtimestamp(submission.created_utc),
                        'meta': {
                            'subreddit': subreddit_name,
                            'permalink': submission.permalink,
                            'upvote_ratio': submission.upvote_ratio,
                            'is_self': submission.is_self,
                            'link_flair_text': submission.link_flair_text,
                            'over_18': submission.over_18,
                            'spoiler': submission.spoiler,
                            'stickied': submission.stickied
                        }
                    }
                    posts.append(post_data)
                    
                except Exception as e:
                    logger.error(f"Error processing submission {submission.id}: {e}")
                    self.items_failed += 1
            
            logger.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
            
        except Exception as e:
            logger.error(f"Error fetching from r/{subreddit_name}: {e}")
            raise
        
        return posts
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch data from all configured subreddits
        Implements abstract method from BaseCrawler
        """
        all_posts = []
        
        for subreddit_name in self.subreddits:
            try:
                posts = self.fetch_subreddit_posts(subreddit_name)
                all_posts.extend(posts)
            except Exception as e:
                logger.error(f"Failed to fetch from r/{subreddit_name}: {e}")
                # Continue with other subreddits even if one fails
                continue
        
        return all_posts
    
    def fetch_top_posts(self, time_filter: str = 'day', limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch top posts from all subreddits for a specific time period
        
        Args:
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
            limit: Number of posts per subreddit
        """
        all_posts = []
        
        for subreddit_name in self.subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for submission in subreddit.top(time_filter=time_filter, limit=limit):
                    try:
                        post_data = {
                            'id': submission.id,
                            'author': str(submission.author) if submission.author else '[deleted]',
                            'title': submission.title,
                            'text': submission.selftext,
                            'url': submission.url,
                            'score': submission.score,
                            'comments_count': submission.num_comments,
                            'created_at': datetime.fromtimestamp(submission.created_utc),
                            'meta': {
                                'subreddit': subreddit_name,
                                'permalink': submission.permalink,
                                'upvote_ratio': submission.upvote_ratio,
                                'time_filter': time_filter
                            }
                        }
                        all_posts.append(post_data)
                    except Exception as e:
                        logger.error(f"Error processing submission: {e}")
                        continue
                
                logger.info(f"Fetched {len(all_posts)} top posts from r/{subreddit_name}")
                
            except Exception as e:
                logger.error(f"Failed to fetch top posts from r/{subreddit_name}: {e}")
                continue
        
        return all_posts


def main():
    """Test the Reddit crawler"""
    try:
        crawler = RedditCrawler()
        result = crawler.run()
        
        if result['success']:
            print(f"✅ Reddit crawler completed successfully!")
            print(f"   Items fetched: {result['items_fetched']}")
            print(f"   Items saved: {result['items_saved']}")
            print(f"   Items failed: {result['items_failed']}")
        else:
            print(f"❌ Reddit crawler failed: {result.get('error')}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
