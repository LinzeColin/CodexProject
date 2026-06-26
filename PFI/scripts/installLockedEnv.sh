#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

source "$PROJECT_DIR/scripts/pfiRuntime.sh"

LOCK_FILE="${PFI_LOCK_FILE:-$PROJECT_DIR/requirements.lock}"
VENV_DIR="${PFI_VENV_DIR:-$PROJECT_DIR/.venv}"
if [[ ! -f "$LOCK_FILE" ]]; then
  echo "Missing lock file: $LOCK_FILE" >&2
  exit 66
fi

BASE_PYTHON="$(pfi_os_choose_venv_python "$PROJECT_DIR")"
echo "Creating locked PFI environment with $BASE_PYTHON"
"$BASE_PYTHON" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$LOCK_FILE"
"$VENV_DIR/bin/python" -m pip install --no-deps -e "$PROJECT_DIR"

if ! pfi_os_python_has_app_deps "$VENV_DIR/bin/python" "$PROJECT_DIR"; then
  echo "Locked environment is missing required app dependencies." >&2
  exit 67
fi
if ! "$VENV_DIR/bin/python" -m pytest --version >/dev/null 2>&1; then
  echo "Locked environment is missing pytest." >&2
  exit 67
fi

date -u +"%Y-%m-%dT%H:%M:%SZ" > "$VENV_DIR/.pfi_os_app_ready"
echo "PFI locked environment is ready: $VENV_DIR"
