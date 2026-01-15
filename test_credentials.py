"""
Test script to verify API credentials
Run this before deploying to production
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_reddit_credentials():
    """Test Reddit API connection"""
    print("\n🔍 Testing Reddit API...")
    
    try:
        import praw
        from dotenv import load_dotenv
        
        load_dotenv()
        
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'TrendHunter/1.0')
        
        if not client_id or not client_secret:
            print("❌ Missing Reddit credentials in .env file")
            return False
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Test by fetching user info
        reddit.user.me()
        print("✅ Reddit API connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Reddit API connection failed: {e}")
        return False


def test_telegram_credentials():
    """Test Telegram Bot connection"""
    print("\n🔍 Testing Telegram Bot...")
    
    try:
        import requests
        from dotenv import load_dotenv
        
        load_dotenv()
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token:
            print("❌ Missing TELEGRAM_BOT_TOKEN in .env file")
            return False
        
        if not chat_id:
            print("❌ Missing TELEGRAM_CHAT_ID in .env file")
            return False
        
        # Test bot connection
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Telegram bot authentication failed: {response.text}")
            return False
        
        bot_info = response.json()
        if bot_info.get('ok'):
            bot_name = bot_info['result']['username']
            print(f"✅ Telegram bot connected: @{bot_name}")
            
            # Test send message
            test_message = "🔥 TrendHunter bot test message"
            send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': test_message,
                'parse_mode': 'HTML'
            }
            
            send_response = requests.post(send_url, json=payload, timeout=10)
            if send_response.status_code == 200:
                print(f"✅ Test message sent to chat_id: {chat_id}")
                return True
            else:
                print(f"❌ Failed to send test message: {send_response.text}")
                return False
        else:
            print("❌ Telegram bot verification failed")
            return False
        
    except Exception as e:
        print(f"❌ Telegram connection failed: {e}")
        return False


def test_database():
    """Test database connection"""
    print("\n🔍 Testing Database...")
    
    try:
        from utils.db_utils import DatabaseManager
        
        db = DatabaseManager()
        
        # Test query
        result = db.execute_query("SELECT COUNT(*) as count FROM keywords")
        
        if result:
            count = result[0]['count']
            print(f"✅ Database connected successfully!")
            print(f"   Current keywords count: {count}")
            return True
        else:
            print("❌ Database query failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_google_trends():
    """Test Google Trends connection"""
    print("\n🔍 Testing Google Trends...")
    
    try:
        from pytrends.request import TrendReq
        import time
        
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        
        # Test query
        pytrends.build_payload(['python'], timeframe='now 7-d')
        data = pytrends.interest_over_time()
        
        if not data.empty:
            print("✅ Google Trends connection successful!")
            print(f"   Retrieved {len(data)} data points")
            return True
        else:
            print("⚠️  Google Trends returned empty data (might be rate limited)")
            return False
            
    except Exception as e:
        print(f"❌ Google Trends connection failed: {e}")
        return False


def main():
    """Run all credential tests"""
    print("="*60)
    print("TREND HUNTER - CREDENTIALS TEST")
    print("="*60)
    
    results = {
        'Reddit API': test_reddit_credentials(),
        'Telegram Bot': test_telegram_credentials(),
        'Database': test_database(),
        'Google Trends': test_google_trends()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for service, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{service:20s} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! System ready for production.")
    else:
        print("⚠️  SOME TESTS FAILED. Please fix issues before deploying.")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
