"""Compatibility Streamlit entrypoint for Procfile and existing operators.

The Streamlit implementation lives in ``src/whkm_salary/streamlit_app.py``.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

runpy.run_module("whkm_salary.streamlit_app", run_name="__main__")
