"""
Configuration loader for Trend Hunter
Loads config.yaml and environment variables
"""

import yaml
import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager"""
    
    def __init__(self, config_path="config/config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.load_config()
        self.load_env()
    
    def load_config(self):
        """Load YAML configuration"""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def load_env(self):
        """Load environment variables from .env file"""
        load_dotenv()
        
        # Override config with environment variables if they exist
        if 'crawler' in self.config and 'reddit' in self.config['crawler']:
            self.config['crawler']['reddit']['client_id'] = os.getenv('REDDIT_CLIENT_ID', '')
            self.config['crawler']['reddit']['client_secret'] = os.getenv('REDDIT_CLIENT_SECRET', '')
        
        if 'alerts' in self.config:
            if 'telegram' in self.config['alerts']:
                self.config['alerts']['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN', '')
                self.config['alerts']['telegram']['chat_id'] = os.getenv('TELEGRAM_CHAT_ID', '')
            
            if 'email' in self.config['alerts']:
                self.config['alerts']['email']['sender_email'] = os.getenv('EMAIL_SENDER', '')
                self.config['alerts']['email']['sender_password'] = os.getenv('EMAIL_PASSWORD', '')
    
    def get(self, key_path, default=None):
        """
        Get config value using dot notation
        Example: config.get('crawler.reddit.client_id')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def __getitem__(self, key):
        """Allow dictionary-style access"""
        return self.config[key]
    
    def __contains__(self, key):
        """Check if key exists"""
        return key in self.config


# Global config instance
_config = None


def get_config(config_path="config/config.yaml"):
    """Get global config instance"""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
