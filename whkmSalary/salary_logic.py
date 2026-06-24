"""Compatibility import for existing tests and external callers.

The implementation lives in ``src/whkm_salary/salary_logic.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from whkm_salary.salary_logic import *  # noqa: F401,F403,E402
