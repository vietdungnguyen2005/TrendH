"""
Run Alert Service
Wrapper script for ui/alert_service.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.alert_service import main

if __name__ == "__main__":
    main()
