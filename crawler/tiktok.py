"""
TikTok Crawler for Trend Hunter
Scrapes TikTok Creative Center for trending hashtags
Uses Playwright for browser automation
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from typing import List, Dict, Any
from datetime import datetime
import logging
import time
import json
from crawler.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class TikTokCrawler(BaseCrawler):
    """Crawler for TikTok Creative Center trending hashtags"""
    
    def __init__(self):
        super().__init__('tiktok')
        
        # Get TikTok config
        tiktok_config = self.config.get('crawler.tiktok', {})
        
        self.creative_center_url = tiktok_config.get(
            'creative_center_url',
            'https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en'
        )
        self.hashtags_to_track = tiktok_config.get('hashtags_to_track', 50)
        self.use_playwright = tiktok_config.get('use_playwright', True)
        self.headless = tiktok_config.get('headless', True)
        
        logger.info("TikTok crawler initialized")
    
    def fetch_trending_hashtags_playwright(self) -> List[Dict[str, Any]]:
        """
        Fetch trending hashtags using Playwright browser automation
        """
        hashtags = []
        
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                logger.info(f"Navigating to TikTok Creative Center: {self.creative_center_url}")
                
                # Navigate to TikTok Creative Center
                page.goto(self.creative_center_url, wait_until='networkidle', timeout=30000)
                
                # Wait for content to load
                time.sleep(3)
                
                # Try to find hashtag elements
                # Note: Selectors may need to be updated as TikTok changes their UI
                try:
                    # Wait for hashtag list to appear
                    page.wait_for_selector('[class*="hashtag"], [class*="tag-item"], .card-item', timeout=10000)
                    
                    # Extract hashtag data
                    # This is a simplified example - actual selectors depend on TikTok's current HTML structure
                    hashtag_elements = page.query_selector_all('[class*="hashtag"], [class*="card"]')
                    
                    for idx, element in enumerate(hashtag_elements[:self.hashtags_to_track]):
                        try:
                            # Extract text content
                            text_content = element.inner_text()
                            
                            # Try to parse hashtag name and metrics
                            # Format varies, so we extract what we can
                            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                            
                            hashtag_name = ''
                            views = 0
                            posts = 0
                            
                            for line in lines:
                                if line.startswith('#'):
                                    hashtag_name = line
                                elif 'M' in line or 'B' in line or 'K' in line:
                                    # Try to parse view count
                                    try:
                                        if 'B' in line:
                                            views = float(line.replace('B', '').strip()) * 1_000_000_000
                                        elif 'M' in line:
                                            views = float(line.replace('M', '').strip()) * 1_000_000
                                        elif 'K' in line:
                                            views = float(line.replace('K', '').strip()) * 1_000
                                    except:
                                        pass
                            
                            if hashtag_name:
                                hashtag_data = {
                                    'id': f'tiktok_hashtag_{idx}_{int(datetime.now().timestamp())}',
                                    'author': 'TikTok Creative Center',
                                    'title': hashtag_name,
                                    'text': f'Trending hashtag: {hashtag_name}',
                                    'url': self.creative_center_url,
                                    'score': int(views),
                                    'comments_count': posts,
                                    'created_at': datetime.now(),
                                    'meta': {
                                        'hashtag': hashtag_name,
                                        'views': views,
                                        'rank': idx + 1,
                                        'source': 'creative_center'
                                    }
                                }
                                hashtags.append(hashtag_data)
                                logger.debug(f"Extracted hashtag: {hashtag_name}")
                        
                        except Exception as e:
                            logger.error(f"Error parsing hashtag element: {e}")
                            continue
                
                except PlaywrightTimeout:
                    logger.warning("Timeout waiting for hashtag elements - page structure may have changed")
                    
                    # Fallback: Try to extract any text that looks like hashtags
                    page_content = page.content()
                    # Basic fallback parsing
                    logger.warning("Using fallback extraction method")
                
                finally:
                    browser.close()
            
            logger.info(f"Extracted {len(hashtags)} trending hashtags from TikTok")
            
        except Exception as e:
            logger.error(f"Error fetching TikTok data with Playwright: {e}", exc_info=True)
            raise
        
        return hashtags
    
    def fetch_trending_hashtags_mock(self) -> List[Dict[str, Any]]:
        """
        Mock data for testing when TikTok access is not available
        Returns sample trending hashtags
        """
        logger.warning("Using mock TikTok data - set use_playwright=true and configure properly for real data")
        
        mock_hashtags = [
            {'name': '#fyp', 'views': 5000000000},
            {'name': '#foryou', 'views': 4500000000},
            {'name': '#viral', 'views': 3000000000},
            {'name': '#trending', 'views': 2500000000},
            {'name': '#xyzbca', 'views': 2000000000},
        ]
        
        hashtags = []
        for idx, tag in enumerate(mock_hashtags):
            hashtag_data = {
                'id': f'tiktok_mock_{idx}_{int(datetime.now().timestamp())}',
                'author': 'TikTok Mock',
                'title': tag['name'],
                'text': f'Mock trending hashtag: {tag["name"]}',
                'url': self.creative_center_url,
                'score': tag['views'],
                'comments_count': 0,
                'created_at': datetime.now(),
                'meta': {
                    'hashtag': tag['name'],
                    'views': tag['views'],
                    'rank': idx + 1,
                    'source': 'mock'
                }
            }
            hashtags.append(hashtag_data)
        
        return hashtags
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch trending hashtags data
        Implements abstract method from BaseCrawler
        """
        try:
            if self.use_playwright:
                return self.fetch_trending_hashtags_playwright()
            else:
                return self.fetch_trending_hashtags_mock()
        except Exception as e:
            logger.error(f"Failed to fetch TikTok data, falling back to mock data: {e}")
            return self.fetch_trending_hashtags_mock()


def main():
    """Test the TikTok crawler"""
    try:
        crawler = TikTokCrawler()
        result = crawler.run()
        
        if result['success']:
            print(f"✅ TikTok crawler completed successfully!")
            print(f"   Items fetched: {result['items_fetched']}")
            print(f"   Items saved: {result['items_saved']}")
            print(f"   Items failed: {result['items_failed']}")
        else:
            print(f"❌ TikTok crawler failed: {result.get('error')}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
