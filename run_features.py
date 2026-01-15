"""
Run feature engineering pipeline
Wrapper script for processing/feature_engineering.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from processing.feature_engineering import main

if __name__ == "__main__":
    main()
