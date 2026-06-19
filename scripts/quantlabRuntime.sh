#!/usr/bin/env zsh

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="${PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION:-python}"

quantlab_resolve_command() {
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

quantlab_python_has_app_deps() {
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

quantlab_python_can_create_venv() {
  local python_bin="$1"
  "$python_bin" - <<'PY' >/dev/null 2>&1
import sys
import venv  # noqa: F401

raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
}

quantlab_choose_app_python() {
  local project_dir="$1"
  local ready_marker="$project_dir/.venv/.quantlab_app_ready"
  if [[ -x "$project_dir/.venv/bin/python" && -f "$ready_marker" ]]; then
    printf "%s\n" "$project_dir/.venv/bin/python"
    return 0
  fi
  local candidates=(
    "${QUANTLAB_PYTHON:-}"
    "${EVA_PYTHON:-}"
    "$project_dir/.venv/bin/python"
    "/opt/anaconda3/bin/python3.12"
    "/opt/anaconda3/bin/python3"
    "/opt/homebrew/bin/python3.12"
    "/opt/homebrew/bin/python3.11"
    "python3"
  )
  local candidate resolved
  for candidate in "${candidates[@]}"; do
    resolved="$(quantlab_resolve_command "$candidate" || true)"
    if [[ -n "$resolved" ]] && quantlab_python_has_app_deps "$resolved" "$project_dir"; then
      printf "%s\n" "$resolved"
      return 0
    fi
  done
  return 1
}

quantlab_choose_venv_python() {
  local project_dir="$1"
  local candidates=(
    "${QUANTLAB_PYTHON:-}"
    "${EVA_PYTHON:-}"
    "python3"
    "/opt/homebrew/bin/python3.12"
    "/opt/homebrew/bin/python3.11"
    "/opt/anaconda3/bin/python3.12"
    "/opt/anaconda3/bin/python3"
  )
  local candidate resolved
  for candidate in "${candidates[@]}"; do
    resolved="$(quantlab_resolve_command "$candidate" || true)"
    if [[ -n "$resolved" ]] && quantlab_python_can_create_venv "$resolved"; then
      printf "%s\n" "$resolved"
      return 0
    fi
  done
  return 1
}

quantlab_ensure_app_python() {
  local project_dir="$1"
  local python_bin base_python
  python_bin="$(quantlab_choose_app_python "$project_dir" || true)"
  if [[ -n "$python_bin" ]]; then
    if [[ "$python_bin" == "$project_dir/.venv/bin/python" ]]; then
      date -u +"%Y-%m-%dT%H:%M:%SZ" > "$project_dir/.venv/.quantlab_app_ready"
    fi
    printf "%s\n" "$python_bin"
    return 0
  fi

  base_python="$(quantlab_choose_venv_python "$project_dir" || true)"
  if [[ -z "$base_python" ]]; then
    echo "No Python >= 3.10 runtime with venv support was found." >&2
    echo "Set QUANTLAB_PYTHON to a valid Python binary and retry." >&2
    return 1
  fi

  echo "QuantLab app dependencies are not ready. Creating .venv with $base_python..." >&2
  "$base_python" -m venv "$project_dir/.venv"
  "$project_dir/.venv/bin/python" -m pip install --upgrade pip >&2
  "$project_dir/.venv/bin/python" -m pip install -e "${project_dir}[app]" >&2

  if ! quantlab_python_has_app_deps "$project_dir/.venv/bin/python" "$project_dir"; then
    echo "QuantLab app dependencies are still incomplete after installation." >&2
    return 1
  fi
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "$project_dir/.venv/.quantlab_app_ready"
  printf "%s\n" "$project_dir/.venv/bin/python"
}
