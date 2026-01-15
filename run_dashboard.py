"""
Run Streamlit Dashboard
Wrapper script for ui/app.py
"""

import subprocess
import sys
from pathlib import Path

# Get the path to the app
app_path = Path(__file__).parent / 'ui' / 'app.py'

# Run streamlit
subprocess.run([
    sys.executable, '-m', 'streamlit', 'run', str(app_path),
    '--server.port', '8501',
    '--server.headless', 'true'
])
