#!/usr/bin/env zsh

_pfi_stage1_candidate_fail() {
  printf "PFI Stage 1 isolated candidate rejected: %s\n" "$1" >&2
  return 1
}

_pfi_stage1_candidate_owned() {
  local path="$1"
  [[ -e "$path" && -O "$path" ]]
}

_pfi_stage1_candidate_port_is_free() {
  local port="$1"
  ! lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

_pfi_stage1_candidate_sha256_text() {
  local output digest
  output="$(printf "%s" "$1" | LC_ALL=C LANG=C shasum -a 256)" || return 1
  digest="${output%% *}"
  [[ ${#digest} -eq 64 && "$digest" != *[^0-9a-f]* ]] || return 1
  printf "%s\n" "$digest"
}

_pfi_stage1_candidate_sha256_file() {
  local file="$1"
  [[ -f "$file" && ! -L "$file" && -O "$file" ]] || return 1
  local output digest
  output="$(LC_ALL=C LANG=C shasum -a 256 "$file")" || return 1
  digest="${output%% *}"
  [[ ${#digest} -eq 64 && "$digest" != *[^0-9a-f]* ]] || return 1
  printf "%s\n" "$digest"
}

_pfi_stage1_candidate_read_marker() {
  local file="$1"
  [[ -f "$file" && ! -L "$file" && -O "$file" ]] || return 1
  local size line_count final_byte
  size="$(stat -f %z "$file" 2>/dev/null || true)"
  line_count="$(wc -l < "$file" | tr -d '[:space:]')"
  final_byte="$(tail -c 1 "$file" | od -An -tuC | tr -d '[:space:]')"
  [[ "$size" == <-> && "$size" -ge 2 && "$size" -le 4096 ]] || return 1
  [[ "$line_count" == "1" && "$final_byte" == "10" ]] || return 1
  if LC_ALL=C tr -d '\12\40-\176' < "$file" | grep -q .; then
    return 1
  fi
  REPLY="$(sed -n '1p' "$file")"
  [[ -n "$REPLY" ]]
}

_pfi_stage1_candidate_bundle_sha256() {
  local app_path="$1"
  local relative file file_hash records=""
  local -a identity_files=(
    "Contents/MacOS/PFI"
    "Contents/Info.plist"
    "Contents/_CodeSignature/CodeResources"
    "Contents/Resources/PFI_PROJECT_ROOT"
    "Contents/Resources/PFI_STAGE1_ISOLATED_ROOT"
    "Contents/Resources/PFI_STAGE1_STREAMLIT_PORT"
    "Contents/Resources/PFI_STAGE1_HEARTBEAT_PORT"
  )
  for relative in "${identity_files[@]}"; do
    file="$app_path/$relative"
    file_hash="$(_pfi_stage1_candidate_sha256_file "$file")" || return 1
    records+="${relative}=${file_hash}"$'\n'
  done
  _pfi_stage1_candidate_sha256_text "$records"
}

_pfi_stage1_active_marker_value() {
  local marker_file="$1"
  local key="$2"
  awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "$marker_file"
}

pfi_stage1_candidate_active_marker_matches() {
  local marker_file="$1"
  [[ -f "$marker_file" && ! -L "$marker_file" ]] || return 1
  local current_mode="${PFI_STAGE1_CANDIDATE_MODE:-0}"
  local marker_mode="$(_pfi_stage1_active_marker_value "$marker_file" PFI_ACTIVE_CANDIDATE_MODE)"
  [[ -n "$marker_mode" ]] || marker_mode=0
  [[ "$marker_mode" == "$current_mode" ]] || return 1
  [[ "$current_mode" == "1" ]] || return 0

  local marker_path_hash marker_executable_hash marker_bundle_hash
  marker_path_hash="$(_pfi_stage1_active_marker_value "$marker_file" PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256)"
  marker_executable_hash="$(_pfi_stage1_active_marker_value "$marker_file" PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256)"
  marker_bundle_hash="$(_pfi_stage1_active_marker_value "$marker_file" PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256)"
  [[ "$marker_path_hash" == "${PFI_CANDIDATE_APP_PATH_SHA256:-}" ]] || return 1
  [[ "$marker_executable_hash" == "${PFI_CANDIDATE_EXECUTABLE_SHA256:-}" ]] || return 1
  [[ "$marker_bundle_hash" == "${PFI_CANDIDATE_BUNDLE_SHA256:-}" ]] || return 1
  [[ ${#marker_path_hash} -eq 64 && "$marker_path_hash" != *[^0-9a-f]* ]] || return 1
  [[ ${#marker_executable_hash} -eq 64 && "$marker_executable_hash" != *[^0-9a-f]* ]] || return 1
  [[ ${#marker_bundle_hash} -eq 64 && "$marker_bundle_hash" != *[^0-9a-f]* ]] || return 1
}

pfi_stage1_candidate_configure() {
  local project_dir="$1"
  typeset -gx PFI_STAGE1_CANDIDATE_MODE=0

  local app_path="${PFI_LAUNCHER_APP_PATH:-}"
  local marker="$app_path/Contents/Resources/PFI_STAGE1_ISOLATED_ROOT"
  [[ -f "$marker" ]] || return 0

  local resolved_project="${project_dir:A}"
  local resolved_app="${app_path:A}"
  local isolated_root="${resolved_app:h}"
  local resources="$resolved_app/Contents/Resources"
  local project_marker="$resources/PFI_PROJECT_ROOT"
  local app_port_marker="$resources/PFI_STAGE1_STREAMLIT_PORT"
  local heartbeat_port_marker="$resources/PFI_STAGE1_HEARTBEAT_PORT"
  local finalizing_file="$isolated_root/PFI_STAGE1_FINALIZING"

  [[ -d "$resolved_project" && "$project_dir" == "$resolved_project" ]] || {
    _pfi_stage1_candidate_fail "project root must be an existing resolved directory"
    return 1
  }
  [[ "$app_path" == "$resolved_app" && -d "$resolved_app" && ! -L "$app_path" ]] || {
    _pfi_stage1_candidate_fail "launcher App path must be resolved and must not be a symlink"
    return 1
  }
  [[ "${isolated_root:h}" == "/private/tmp" && "${isolated_root:t}" =~ '^pfi-v025-s1p13-[A-Za-z0-9._-]+$' && "${resolved_app:t}" == "PFI.app" ]] || {
    _pfi_stage1_candidate_fail "launcher App must be an exact /private/tmp/pfi-v025-s1p13-*/PFI.app candidate"
    return 1
  }
  [[ "$(stat -f %Lp "$isolated_root" 2>/dev/null || true)" == "700" ]] || {
    _pfi_stage1_candidate_fail "candidate root must have private mode 0700"
    return 1
  }
  [[ ! -e "$finalizing_file" && ! -L "$finalizing_file" ]] || {
    _pfi_stage1_candidate_fail "candidate finalization is in progress"
    return 1
  }
  [[ "$resources" == "${resources:A}" && -d "$resources" && ! -L "$resources" ]] || {
    _pfi_stage1_candidate_fail "candidate Resources directory must be resolved"
    return 1
  }

  local required_file
  for required_file in "$marker" "$project_marker" "$app_port_marker" "$heartbeat_port_marker"; do
    _pfi_stage1_candidate_read_marker "$required_file" || {
      _pfi_stage1_candidate_fail "candidate marker must be owned, printable and exactly one newline-terminated line"
      return 1
    }
  done

  _pfi_stage1_candidate_read_marker "$marker" || return 1
  local declared_root="$REPLY"
  _pfi_stage1_candidate_read_marker "$project_marker" || return 1
  local declared_project="$REPLY"
  _pfi_stage1_candidate_read_marker "$app_port_marker" || return 1
  local app_port="$REPLY"
  _pfi_stage1_candidate_read_marker "$heartbeat_port_marker" || return 1
  local heartbeat_port="$REPLY"
  [[ "$declared_root" == "$isolated_root" && "$declared_root" == "${declared_root:A}" && ! -L "$declared_root" ]] || {
    _pfi_stage1_candidate_fail "declared isolated root does not match the resolved candidate root"
    return 1
  }
  [[ "$declared_project" == "$resolved_project" && "$declared_project" == "${declared_project:A}" ]] || {
    _pfi_stage1_candidate_fail "candidate project root does not match the launcher project"
    return 1
  }
  _pfi_stage1_candidate_owned "$isolated_root" &&
    _pfi_stage1_candidate_owned "$resolved_app" &&
    _pfi_stage1_candidate_owned "$resources" || {
      _pfi_stage1_candidate_fail "candidate root and App must be owned by the current user"
      return 1
    }

  [[ "$app_port" == <-> && "$heartbeat_port" == <-> ]] || {
    _pfi_stage1_candidate_fail "candidate ports must be numeric"
    return 1
  }
  (( app_port >= 1024 && app_port <= 65535 && heartbeat_port >= 1024 && heartbeat_port <= 65535 )) || {
    _pfi_stage1_candidate_fail "candidate ports must be in the unprivileged TCP range"
    return 1
  }
  [[ "$app_port" != "$heartbeat_port" && "$app_port" != "8501" && "$app_port" != "8502" && "$heartbeat_port" != "8501" && "$heartbeat_port" != "8502" ]] || {
    _pfi_stage1_candidate_fail "candidate ports must be distinct and must not use protected ports"
    return 1
  }
  _pfi_stage1_candidate_port_is_free "$app_port" && _pfi_stage1_candidate_port_is_free "$heartbeat_port" || {
    _pfi_stage1_candidate_fail "candidate ports must be free before launch"
    return 1
  }

  local candidate_home="$isolated_root/home"
  local data_home="$isolated_root/data"
  local runtime_dir="$isolated_root/runtime"
  local temp_dir="$isolated_root/tmp"
  local cache_home="$isolated_root/cache"
  local browser_profile="$isolated_root/browser-profile"
  local python_pycache="$isolated_root/python-pycache"
  local -a isolated_dirs=(
    "$candidate_home"
    "$data_home"
    "$runtime_dir"
    "$temp_dir"
    "$cache_home"
    "$browser_profile"
    "$python_pycache"
  )
  local mutable_dir
  for mutable_dir in "${isolated_dirs[@]}"; do
    if [[ -e "$mutable_dir" || -L "$mutable_dir" ]]; then
      [[ -d "$mutable_dir" && ! -L "$mutable_dir" && "$mutable_dir" == "${mutable_dir:A}" ]] || {
        _pfi_stage1_candidate_fail "isolated mutable path is not a resolved directory"
        return 1
      }
    fi
  done
  umask 077
  mkdir -p "${isolated_dirs[@]}" || {
    _pfi_stage1_candidate_fail "could not create isolated mutable directories"
    return 1
  }
  chmod 700 "${isolated_dirs[@]}" || {
    _pfi_stage1_candidate_fail "could not make isolated mutable directories private"
    return 1
  }
  for mutable_dir in "${isolated_dirs[@]}"; do
    [[ "$mutable_dir" == "$isolated_root"/* && "$mutable_dir" == "${mutable_dir:A}" && "$(stat -f %Lp "$mutable_dir")" == "700" ]] && _pfi_stage1_candidate_owned "$mutable_dir" || {
      _pfi_stage1_candidate_fail "mutable directory escaped the isolated root"
      return 1
    }
  done

  local candidate_path_hash candidate_executable_hash candidate_bundle_hash
  candidate_path_hash="$(_pfi_stage1_candidate_sha256_text "$resolved_app")" || {
    _pfi_stage1_candidate_fail "candidate path identity is unavailable"
    return 1
  }
  candidate_executable_hash="$(_pfi_stage1_candidate_sha256_file "$resolved_app/Contents/MacOS/PFI")" || {
    _pfi_stage1_candidate_fail "candidate executable identity is unavailable"
    return 1
  }
  candidate_bundle_hash="$(_pfi_stage1_candidate_bundle_sha256 "$resolved_app")" || {
    _pfi_stage1_candidate_fail "candidate bundle identity is unavailable"
    return 1
  }

  typeset -gx PFI_STAGE1_CANDIDATE_MODE=1
  typeset -gx PFI_STAGE1_ISOLATED_ROOT="$isolated_root"
  typeset -gx HOME="$candidate_home"
  typeset -gx PFI_DATA_HOME="$data_home"
  typeset -gx PFI_RUNTIME_DIR="$runtime_dir"
  typeset -gx TMPDIR="$temp_dir"
  typeset -gx XDG_CACHE_HOME="$cache_home"
  typeset -gx PFI_BROWSER_PROFILE_DIR="$browser_profile"
  typeset -gx PYTHONPYCACHEPREFIX="$python_pycache"
  typeset -gx PYTHONDONTWRITEBYTECODE=1
  typeset -gx PFI_STREAMLIT_PORT="$app_port"
  typeset -gx PFI_HEARTBEAT_PORT="$heartbeat_port"
  typeset -gx PFI_START_OPEN_BROWSER=0
  typeset -gx PFI_CANDIDATE_APP_PATH_SHA256="$candidate_path_hash"
  typeset -gx PFI_CANDIDATE_EXECUTABLE_SHA256="$candidate_executable_hash"
  typeset -gx PFI_CANDIDATE_BUNDLE_SHA256="$candidate_bundle_hash"
  typeset -gx PFI_STAGE1_FINALIZING_FILE="$finalizing_file"
  export PFI_STAGE1_CANDIDATE_MODE PFI_STAGE1_ISOLATED_ROOT HOME PFI_DATA_HOME PFI_RUNTIME_DIR TMPDIR
  export XDG_CACHE_HOME PFI_BROWSER_PROFILE_DIR PYTHONPYCACHEPREFIX PYTHONDONTWRITEBYTECODE
  export PFI_STREAMLIT_PORT PFI_HEARTBEAT_PORT PFI_START_OPEN_BROWSER
  export PFI_CANDIDATE_APP_PATH_SHA256 PFI_CANDIDATE_EXECUTABLE_SHA256 PFI_CANDIDATE_BUNDLE_SHA256
  export PFI_STAGE1_FINALIZING_FILE
}
