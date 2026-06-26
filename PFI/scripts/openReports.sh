#!/usr/bin/env zsh
set -euo pipefail

REPORT_DIR="${PFI_REPORT_DIR:-$HOME/Downloads/量化回测分析}"
mkdir -p "$REPORT_DIR"
open "$REPORT_DIR"
