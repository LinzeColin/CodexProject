#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}"

DB_PATH="${WDA_V0_2_R1_DB:-/Users/linzezhang/Downloads/WDA_MetaData/v0_1/data_core_seed/wda_v0_1_seed.sqlite}"
ANALYSIS_ROOT="${WDA_V0_2_R1_ANALYSIS_ROOT:-/Users/linzezhang/Downloads/WDA_MetaData/v0_1/analysis_layer}"
OUTPUT_ROOT="${WDA_V0_2_R1_OUTPUT_ROOT:-/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r1}"
REPO_DOCS_ROOT="${WDA_V0_2_R1_REPO_DOCS_ROOT:-$SCRIPT_DIR/../docs/v0_2_r1_full_auto_human_readable_workspace}"

"$PYTHON_BIN" -B "$SCRIPT_DIR/wda_v0_2_r1_generate_workspace.py" \
  --db "$DB_PATH" \
  --analysis-root "$ANALYSIS_ROOT" \
  --output-root "$OUTPUT_ROOT" \
  --repo-docs-root "$REPO_DOCS_ROOT"
