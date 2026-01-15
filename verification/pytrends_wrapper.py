"""
Google Trends Verification Wrapper for Trend Hunter
Uses pytrends with replicate sampling, caching, and rate limiting
"""

import time
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logging.warning("pytrends not installed. Install with: pip install pytrends")

from utils.db_utils import get_db
from utils.config_loader import get_config

logger = logging.getLogger(__name__)


class TrendsCache:
    """Cache for Google Trends data"""
    
    def __init__(self, ttl_hours: int = 24):
        self.db = get_db()
        self.ttl_hours = ttl_hours
    
    def get(self, key: str) -> Optional[str]:
        """Get cached value if not expired"""
        query = "SELECT value, expires_at FROM cache WHERE key = ?"
        result = self.db.execute_query(query, (key,))
        
        if result:
            value, expires_at = result[0]['value'], result[0]['expires_at']
            
            # Check if expired
            expires_datetime = datetime.fromisoformat(expires_at)
            if datetime.now() < expires_datetime:
                logger.debug(f"Cache HIT: {key}")
                return value
            else:
                # Delete expired entry
                self.delete(key)
                logger.debug(f"Cache EXPIRED: {key}")
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(self, key: str, value: str):
        """Set cache value with TTL"""
        expires_at = datetime.now() + timedelta(hours=self.ttl_hours)
        
        # Delete existing entry
        self.delete(key)
        
        # Insert new entry
        data = {
            'key': key,
            'value': value,
            'expires_at': expires_at.isoformat(),
            'created_at': datetime.now().isoformat()
        }
        self.db.insert('cache', data)
        logger.debug(f"Cache SET: {key}")
    
    def delete(self, key: str):
        """Delete cache entry"""
        query = "DELETE FROM cache WHERE key = ?"
        self.db.execute_query(query, (key,))
    
    def clear_expired(self):
        """Clear all expired cache entries"""
        query = "DELETE FROM cache WHERE expires_at < ?"
        self.db.execute_query(query, (datetime.now().isoformat(),))


class PyTrendsWrapper:
    """Wrapper for pytrends with replicate sampling and caching"""
    
    def __init__(self):
        if not PYTRENDS_AVAILABLE:
            raise ImportError("pytrends is not installed. Run: pip install pytrends")
        
        self.config = get_config()
        self.db = get_db()
        
        # Configuration
        self.replicate_samples = self.config.get('pytrends.replicate_samples', 3)
        self.batch_size = self.config.get('pytrends.batch_size', 5)
        self.cache_ttl = self.config.get('pytrends.cache_ttl_hours', 24)
        self.rate_limit = self.config.get('pytrends.rate_limit.requests_per_minute', 10)
        self.delay = self.config.get('pytrends.rate_limit.delay_between_requests', 6)
        self.geo = self.config.get('pytrends.geo', '')
        self.timeframe = self.config.get('pytrends.timeframe', 'now 7-d')
        
        # Initialize cache
        self.cache = TrendsCache(ttl_hours=self.cache_ttl)
        
        # Initialize pytrends
        self.pytrends = None
        self.init_pytrends()
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()
        
        logger.info("PyTrends wrapper initialized")
    
    def init_pytrends(self):
        """Initialize or reinitialize pytrends client"""
        try:
            # Note: urllib3 2.0+ renamed method_whitelist to allowed_methods
            # TrendReq will handle this internally in newer pytrends versions
            self.pytrends = TrendReq(
                hl='en-US',
                tz=360,
                timeout=(10, 25),
                retries=2,
                backoff_factor=0.5,
                requests_args={'verify': True}  # Ensure SSL verification
            )
            logger.debug("PyTrends client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pytrends: {e}")
            self.pytrends = None
    
    def rate_limit_check(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Reset counter if window expired (1 minute)
        if current_time - self.request_window_start > 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # Check if exceeded rate limit
        if self.request_count >= self.rate_limit:
            sleep_time = 60 - (current_time - self.request_window_start)
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = time.time()
        
        # Enforce delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def get_cached_or_fetch(self, term: str) -> Optional[Dict]:
        """Get from cache or fetch new data"""
        cache_key = f"trends_{term}_{self.timeframe}_{self.geo}"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode cached data for {term}")
        
        # Fetch new data
        data = self.fetch_interest_over_time_single(term)
        
        if data:
            # Cache the result
            self.cache.set(cache_key, json.dumps(data))
        
        return data
    
    def fetch_interest_over_time_single(self, term: str, retry_count: int = 0) -> Optional[Dict]:
        """
        Fetch interest over time for a single term
        Returns dict with dates and values
        """
        if not self.pytrends:
            logger.error("PyTrends client not initialized")
            return None
        
        try:
            # Rate limiting
            self.rate_limit_check()
            
            # Build payload
            self.pytrends.build_payload(
                [term],
                cat=0,
                timeframe=self.timeframe,
                geo=self.geo,
                gprop=''
            )
            
            # Get interest over time
            df = self.pytrends.interest_over_time()
            
            if df.empty or term not in df.columns:
                logger.warning(f"No data returned for term: {term}")
                return None
            
            # Convert to dict
            data = {
                'term': term,
                'timeframe': self.timeframe,
                'geo': self.geo,
                'data': df[term].to_dict()
            }
            
            logger.debug(f"Fetched data for: {term}")
            return data
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle 429 (Too Many Requests)
            if '429' in error_msg or 'quota' in error_msg.lower():
                logger.error(f"Rate limit exceeded (429). Backing off...")
                
                if retry_count < 3:
                    backoff_time = (2 ** retry_count) * 60  # Exponential backoff
                    logger.info(f"Retrying after {backoff_time}s...")
                    time.sleep(backoff_time)
                    return self.fetch_interest_over_time_single(term, retry_count + 1)
                else:
                    logger.error(f"Max retries reached for {term}")
                    return None
            
            logger.error(f"Error fetching data for {term}: {e}")
            return None
    
    def fetch_with_replication(self, term: str) -> Dict[str, Any]:
        """
        Fetch data with replicate sampling (n times)
        Returns median IOT series and raw samples
        """
        samples = []
        
        for i in range(self.replicate_samples):
            logger.debug(f"Replicate {i+1}/{self.replicate_samples} for {term}")
            
            data = self.get_cached_or_fetch(term)
            
            if data:
                samples.append(data)
            
            # Add small random jitter between replicates
            if i < self.replicate_samples - 1:
                time.sleep(random.uniform(1, 3))
        
        if not samples:
            logger.warning(f"No samples collected for {term}")
            return {
                'term': term,
                'samples': [],
                'median_iot': {},
                'sample_count': 0
            }
        
        # Calculate median IOT
        median_iot = self.calculate_median_iot(samples)
        
        return {
            'term': term,
            'samples': samples,
            'median_iot': median_iot,
            'sample_count': len(samples)
        }
    
    def calculate_median_iot(self, samples: List[Dict]) -> Dict:
        """Calculate median IOT from multiple samples"""
        if not samples:
            return {}
        
        # Collect all dates
        all_dates = set()
        for sample in samples:
            all_dates.update(sample['data'].keys())
        
        # Calculate median for each date
        median_iot = {}
        for date in sorted(all_dates):
            values = []
            for sample in samples:
                if date in sample['data']:
                    values.append(sample['data'][date])
            
            if values:
                # Calculate median
                values.sorted = sorted(values)
                n = len(values)
                if n % 2 == 0:
                    median = (values.sorted[n//2-1] + values.sorted[n//2]) / 2
                else:
                    median = values.sorted[n//2]
                
                median_iot[date] = median
        
        return median_iot
    
    def verify_terms(self, terms: List[str]) -> List[Dict]:
        """
        Verify multiple terms with Google Trends
        Returns list of verification results
        """
        results = []
        
        logger.info(f"Verifying {len(terms)} terms with Google Trends...")
        
        for i, term in enumerate(terms, 1):
            logger.info(f"Processing term {i}/{len(terms)}: {term}")
            
            try:
                result = self.fetch_with_replication(term)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to verify term {term}: {e}")
                results.append({
                    'term': term,
                    'error': str(e)
                })
        
        return results


def main():
    """Test the PyTrends wrapper"""
    print("Testing PyTrends Wrapper...")
    
    if not PYTRENDS_AVAILABLE:
        print("❌ pytrends not installed. Run: pip install pytrends")
        return 1
    
    try:
        wrapper = PyTrendsWrapper()
        
        # Test single term
        print("\nTesting single term: 'iPhone'")
        result = wrapper.fetch_with_replication('iPhone')
        
        print(f"  Samples collected: {result['sample_count']}")
        print(f"  Median IOT data points: {len(result['median_iot'])}")
        
        if result['median_iot']:
            # Show first few data points
            items = list(result['median_iot'].items())[:3]
            print("  Sample data:")
            for date, value in items:
                print(f"    {date}: {value}")
        
        print("\n✅ PyTrends wrapper test completed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
