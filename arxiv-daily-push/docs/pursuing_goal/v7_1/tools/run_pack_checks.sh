#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
python "$ROOT/tools/validate_task_pack.py" --root "$ROOT"
python -m unittest discover -s "$ROOT/tests" -p "test_*.py" -v
