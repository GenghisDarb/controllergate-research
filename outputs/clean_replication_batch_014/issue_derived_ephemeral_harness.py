from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

workspace = Path(os.environ['DARKER_SOURCE_WORKSPACE'])
env = os.environ.copy()
env['GIT_DIR'] = '.git'
completed = subprocess.run([sys.executable, '-m', 'darker', '--check', 'src'], cwd=workspace, env=env, text=True, capture_output=True)
if completed.stdout:
    print(completed.stdout, end='')
if completed.stderr:
    print(completed.stderr, end='', file=sys.stderr)
raise SystemExit(completed.returncode)
