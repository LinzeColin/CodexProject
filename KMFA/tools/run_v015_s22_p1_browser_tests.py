#!/usr/bin/env python3
"""Run S22-P1 browser acceptance with the bundled browser runtime."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_PYTHON = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
TEST_MODULE = "KMFA.tests.test_v015_s22_p1_notifications_browser"


def main() -> int:
    if not BUNDLED_PYTHON.is_file():
        print("FAIL: bundled browser-test runtime is unavailable", file=sys.stderr)
        return 1
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    return subprocess.run([str(BUNDLED_PYTHON), "-B", "-m", "unittest", TEST_MODULE], cwd=REPO_ROOT, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
