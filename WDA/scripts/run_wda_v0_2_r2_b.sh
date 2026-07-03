#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}"

REQUESTED_BUNDLE="${WDA_V0_2_R2_BUNDLE:-/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/input_full_export/wda_v0_2_r2_full_export_transfer_bundle.zip}"
OUTPUT_ROOT="${WDA_V0_2_R2_OUTPUT_ROOT:-/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace}"
REPO_DOCS_ROOT="${WDA_V0_2_R2_REPO_DOCS_ROOT:-$SCRIPT_DIR/../docs/v0_2_r2_full_auto_workspace}"

"$PYTHON_BIN" -B "$SCRIPT_DIR/wda_v0_2_r2_import_full_bundle.py" \
  --bundle "$REQUESTED_BUNDLE" \
  --output-root "$OUTPUT_ROOT" \
  --repo-docs-root "$REPO_DOCS_ROOT"
