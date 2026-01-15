"""
Run backtest framework
Wrapper script for backtest/backtest_runner.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backtest.backtest_runner import main

if __name__ == "__main__":
    main()
