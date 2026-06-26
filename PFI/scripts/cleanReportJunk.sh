#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

export PYTHONPATH="$PROJECT_DIR/src"
.venv/bin/python - <<'PY'
from pfi_os.reports.catalog import cleanup_report_junk

removed = cleanup_report_junk(dry_run=False)
print(f"Cleaned report junk files: {len(removed)}")
for path in removed:
    print(path)
PY
