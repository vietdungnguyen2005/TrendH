"""
Run ground truth labeling
Wrapper script for backtest/labeling.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backtest.labeling import main

if __name__ == "__main__":
    main()
