"""Test bootstrap for the recon suite.

Puts backend/ on sys.path so `import app.recon...` resolves whether pytest is run
from the repo root or from backend/.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
