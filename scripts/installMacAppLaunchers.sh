#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Backward-compatible entry point. The old generated launcher/icon workflow has
# been retired; all app installs now use the maintained EVA_OS bundle.
exec "$ROOT_DIR/scripts/installEVAOSEntryApps.sh" "$@"
