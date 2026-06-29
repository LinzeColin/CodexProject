#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"
source "$PROJECT_DIR/scripts/pfiRuntime.sh"

process_cwd() {
  local pid="$1"
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | awk '/^n/ {sub(/^n/, ""); print; exit}'
}

pfi_os_is_running() {
  local port pids pid command cwd_path
  for port in {8501..8510}; do
    pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [[ -z "$pids" ]]; then
      continue
    fi
    for pid in ${(f)pids}; do
      command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
      cwd_path="$(process_cwd "$pid")"
      if [[ "$command" == *"src/pfi_os/app/streamlit_app.py"* && ( "$command" == *"$PROJECT_DIR"* || "$cwd_path" == "$PROJECT_DIR" ) ]]; then
        return 0
      fi
    done
  done
  return 1
}

DRY_RUN=0
JSON_OUTPUT=0
for ARG in "$@"; do
  case "$ARG" in
    --dry-run)
      DRY_RUN=1
      ;;
    --json)
      JSON_OUTPUT=1
      ;;
    *)
      echo "Unknown cleanCache argument: $ARG" >&2
      exit 64
      ;;
  esac
done

if [[ "$DRY_RUN" == "0" ]] && pfi_os_is_running; then
  echo "PFI appears to be running. Stop it before cleaning cache."
  exit 2
fi

if [[ -n "${PFI_CLEANUP_PYTHON:-}" ]]; then
  PYTHON_BIN="$PFI_CLEANUP_PYTHON"
else
  PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"
fi
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/pfi_os-pycache}"
ARGS=(--root "$PROJECT_DIR")
if [[ "$DRY_RUN" == "1" ]]; then
  ARGS+=(--dry-run)
fi
if [[ "$JSON_OUTPUT" == "1" ]]; then
  ARGS+=(--json)
fi

PYTHONPATH="$PROJECT_DIR/src" "$PYTHON_BIN" -m pfi_os.system.cache_cleanup "${ARGS[@]}"
