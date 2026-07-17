#!/usr/bin/env python3
"""使用本地随附浏览器运行 S16-P2 指标下钻验收。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_PYTHON = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
TEST_MODULE = "KMFA.tests.test_v015_s16_p2_drilldown_explanation_browser"


def main() -> int:
    if not BUNDLED_PYTHON.is_file():
        print("FAIL: bundled browser-test runtime is unavailable", file=sys.stderr)
        return 1
    environment = dict(os.environ)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
    result = subprocess.run(
        [str(BUNDLED_PYTHON), "-B", "-m", "unittest", TEST_MODULE],
        cwd=REPO_ROOT,
        env=environment,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
