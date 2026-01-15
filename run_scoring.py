"""
Run scoring engine pipeline
Wrapper script for scoring/scoring_engine.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.scoring_engine import main

if __name__ == "__main__":
    main()
