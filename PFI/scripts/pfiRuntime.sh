#!/usr/bin/env zsh

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="${PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION:-python}"

pfi_os_resolve_command() {
  local candidate="$1"
  if [[ -z "$candidate" ]]; then
    return 1
  fi
  if [[ "$candidate" == */* ]]; then
    if [[ -x "$candidate" ]]; then
      printf "%s\n" "$candidate"
      return 0
    fi
    return 1
  fi
  command -v "$candidate" 2>/dev/null
}

pfi_os_python_has_app_deps() {
  local python_bin="$1"
  local project_dir="${2:-}"
  PYTHONPATH="$project_dir/src${PYTHONPATH:+:$PYTHONPATH}" "$python_bin" - <<'PY' >/dev/null 2>&1
import importlib
import importlib.util

for module_name in ("streamlit", "plotly", "pandas", "docx", "pypdf", "matplotlib", "pyarrow"):
    if importlib.util.find_spec(module_name) is None:
        raise ModuleNotFoundError(module_name)
for module_name in ("streamlit", "pandas", "pyarrow"):
    importlib.import_module(module_name)
PY
}

pfi_os_python_can_create_venv() {
  local python_bin="$1"
  "$python_bin" - <<'PY' >/dev/null 2>&1
import sys
import venv  # noqa: F401

raise SystemExit(0 if (3, 11) <= sys.version_info < (3, 14) else 1)
PY
}

pfi_os_choose_app_python() {
  local project_dir="$1"
  local ready_marker="$project_dir/.venv/.pfi_os_app_ready"
  local resolved_override
  if [[ -n "${PFI_PYTHON:-}" ]]; then
    resolved_override="$(pfi_os_resolve_command "$PFI_PYTHON" || true)"
    if [[ -n "$resolved_override" ]]; then
      if pfi_os_python_has_app_deps "$resolved_override" "$project_dir"; then
        printf "%s\n" "$resolved_override"
        return 0
      fi
    fi
  fi
  if [[ -x "$project_dir/.venv/bin/python" && -f "$ready_marker" ]]; then
    printf "%s\n" "$project_dir/.venv/bin/python"
    return 0
  fi
  local candidates=(
    "$project_dir/.venv/bin/python"
    "/opt/anaconda3/bin/python3.12"
    "/opt/anaconda3/bin/python3"
    "/opt/homebrew/bin/python3.12"
    "/opt/homebrew/bin/python3.11"
    "python3"
  )
  local candidate resolved
  for candidate in "${candidates[@]}"; do
    resolved="$(pfi_os_resolve_command "$candidate" || true)"
    if [[ -n "$resolved" ]] && pfi_os_python_has_app_deps "$resolved" "$project_dir"; then
      printf "%s\n" "$resolved"
      return 0
    fi
  done
  return 1
}

pfi_os_choose_venv_python() {
  local project_dir="$1"
  local candidates=(
    "${PFI_PYTHON:-}"
    "${PFI_PYTHON:-}"
    "python3"
    "/opt/homebrew/bin/python3.12"
    "/opt/homebrew/bin/python3.11"
    "/opt/anaconda3/bin/python3.12"
    "/opt/anaconda3/bin/python3"
  )
  local candidate resolved
  for candidate in "${candidates[@]}"; do
    resolved="$(pfi_os_resolve_command "$candidate" || true)"
    if [[ -n "$resolved" ]] && pfi_os_python_can_create_venv "$resolved"; then
      printf "%s\n" "$resolved"
      return 0
    fi
  done
  return 1
}

pfi_os_ensure_app_python() {
  local project_dir="$1"
  local python_bin
  python_bin="$(pfi_os_choose_app_python "$project_dir" || true)"
  if [[ -n "$python_bin" ]]; then
    printf "%s\n" "$python_bin"
    return 0
  fi

  echo "PFI app dependencies are not ready." >&2
  echo "Run scripts/installLockedEnv.sh once, then retry this runtime command." >&2
  echo "Runtime commands do not install or upgrade dependencies." >&2
  return 1
}
