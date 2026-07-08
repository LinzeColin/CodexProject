#!/usr/bin/env bash
set -euo pipefail
# Thin wrapper retained for agents that look for a sync script.
"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install_to_kmfa_main.sh"
