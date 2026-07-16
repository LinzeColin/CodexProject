#!/bin/zsh

# Shared, read-only v0.2.5 release identity loader for both local launchers.

pfi_release_manifest_value() {
  local key="$1"
  /usr/bin/plutil -extract "$key" raw -o - "$PFI_RELEASE_MANIFEST_FILE" 2>/dev/null
}

pfi_release_plist_value() {
  local key="$1"
  /usr/bin/plutil -extract "$key" raw -o - "$PFI_RELEASE_APP_PLIST" 2>/dev/null
}

pfi_release_require_hex() {
  local value="$1"
  local length="$2"
  local label="$3"
  if ! printf '%s' "$value" | /usr/bin/grep -Eq "^[0-9a-f]{$length}$"; then
    echo "PFI 发布身份无效：$label 必须是 $length 位小写 SHA-256/commit 值。" >&2
    return 1
  fi
}

pfi_release_show_conflict_dialog() {
  local osascript_bin="${PFI_OSASCRIPT_BIN:-/usr/bin/osascript}"
  "$osascript_bin" -e 'display dialog "PFI 版本冲突或发布身份无效。请重新启动 PFI；仍不一致时从受信任的本地 checkout 重新安装 PFI.app，并清除缓存后重试。" buttons {"好"} default button "好" with icon caution' >/dev/null 2>&1 || true
}

pfi_release_identity_init() {
  local project_dir="$1"
  local app_bundle="${PFI_LAUNCHER_APP_PATH:-$project_dir/macos/PFI.app}"

  typeset -g PFI_RELEASE_MANIFEST_FILE="$project_dir/config/release_manifest.json"
  typeset -g PFI_RELEASE_APP_BUNDLE="$app_bundle"
  typeset -g PFI_RELEASE_APP_PLIST="$app_bundle/Contents/Info.plist"

  if [[ ! -f "$PFI_RELEASE_MANIFEST_FILE" ]]; then
    echo "PFI 发布身份缺失：请从受信任的本地 checkout 重新安装 PFI.app。" >&2
    return 1
  fi
  if [[ ! -f "$PFI_RELEASE_APP_PLIST" ]]; then
    echo "PFI App 身份缺失：找不到 $PFI_RELEASE_APP_PLIST。" >&2
    return 1
  fi

  typeset -g PFI_ACTIVE_PRODUCT="$(pfi_release_manifest_value product)"
  typeset -g PFI_ACTIVE_VERSION="$(pfi_release_manifest_value version)"
  typeset -g PFI_ACTIVE_BUILD_ID="$(pfi_release_manifest_value build_id)"
  typeset -g PFI_ACTIVE_GIT_COMMIT="$(pfi_release_manifest_value git_commit)"
  typeset -g PFI_ACTIVE_FRONTEND_HASH="$(pfi_release_manifest_value frontend_bundle_hash)"
  typeset -g PFI_ACTIVE_BACKEND_HASH="$(pfi_release_manifest_value backend_build_hash)"
  typeset -g PFI_ACTIVE_APP_SHORT_VERSION="$(pfi_release_manifest_value app_short_version)"
  typeset -g PFI_ACTIVE_APP_BUILD_VERSION="$(pfi_release_manifest_value app_build_version)"
  typeset -g PFI_ACTIVE_UI_CONTRACT="PFI-V025-RELEASE-IDENTITY"
  typeset -g PFI_RELEASE_MANIFEST_SHA256="$(/usr/bin/openssl dgst -sha256 "$PFI_RELEASE_MANIFEST_FILE" | /usr/bin/awk '{print $NF}')"

  local required_value
  for required_value in \
    "$PFI_ACTIVE_PRODUCT" \
    "$PFI_ACTIVE_VERSION" \
    "$PFI_ACTIVE_BUILD_ID" \
    "$PFI_ACTIVE_GIT_COMMIT" \
    "$PFI_ACTIVE_FRONTEND_HASH" \
    "$PFI_ACTIVE_BACKEND_HASH" \
    "$PFI_ACTIVE_APP_SHORT_VERSION" \
    "$PFI_ACTIVE_APP_BUILD_VERSION"; do
    if [[ -z "$required_value" ]]; then
      echo "PFI 发布身份字段不完整，已停止启动。" >&2
      return 1
    fi
  done

  [[ "$PFI_ACTIVE_PRODUCT" == "PFI" ]] || {
    echo "PFI 发布身份冲突：manifest product 不是 PFI。" >&2
    return 1
  }
  [[ "$(<"$project_dir/VERSION")" == "$PFI_ACTIVE_VERSION" ]] || {
    echo "PFI 发布身份冲突：VERSION 与 manifest 不一致。" >&2
    return 1
  }
  [[ "$(pfi_release_plist_value CFBundleShortVersionString)" == "$PFI_ACTIVE_APP_SHORT_VERSION" ]] || {
    echo "PFI 发布身份冲突：App short version 与 manifest 不一致。" >&2
    return 1
  }
  [[ "$(pfi_release_plist_value CFBundleVersion)" == "$PFI_ACTIVE_APP_BUILD_VERSION" ]] || {
    echo "PFI 发布身份冲突：App build version 与 manifest 不一致。" >&2
    return 1
  }
  pfi_release_require_hex "$PFI_ACTIVE_GIT_COMMIT" 40 git_commit || return 1
  pfi_release_require_hex "$PFI_ACTIVE_FRONTEND_HASH" 64 frontend_bundle_hash || return 1
  pfi_release_require_hex "$PFI_ACTIVE_BACKEND_HASH" 64 backend_build_hash || return 1
  pfi_release_require_hex "$PFI_RELEASE_MANIFEST_SHA256" 64 manifest_sha256 || return 1

  typeset -g PFI_VERSION_QUERY="pfi_app_version=$PFI_ACTIVE_APP_SHORT_VERSION&pfi_app_build=$PFI_ACTIVE_APP_BUILD_VERSION&pfi_build=$PFI_ACTIVE_BUILD_ID&pfi_commit=$PFI_ACTIVE_GIT_COMMIT&pfi_frontend_hash=$PFI_ACTIVE_FRONTEND_HASH&pfi_backend_hash=$PFI_ACTIVE_BACKEND_HASH&pfi_manifest_sha256=$PFI_RELEASE_MANIFEST_SHA256"
  export PFI_ACTIVE_PRODUCT PFI_ACTIVE_VERSION PFI_ACTIVE_BUILD_ID
  export PFI_ACTIVE_GIT_COMMIT PFI_ACTIVE_FRONTEND_HASH PFI_ACTIVE_BACKEND_HASH
  export PFI_ACTIVE_APP_SHORT_VERSION PFI_ACTIVE_APP_BUILD_VERSION
  export PFI_ACTIVE_UI_CONTRACT PFI_RELEASE_MANIFEST_SHA256 PFI_VERSION_QUERY
}

pfi_release_cache_key_init() {
  local project_dir="$1"
  local python_bin="$2"
  local contract_cli="$project_dir/scripts/v025/release_cache_contract.py"
  if [[ ! -x "$python_bin" || ! -f "$contract_cli" ]]; then
    echo "PFI 发布缓存契约缺失，已停止启动。" >&2
    return 1
  fi
  local cache_key
  cache_key="$("$python_bin" "$contract_cli" --project-root "$project_dir" --key-only)" || {
    echo "PFI 发布缓存契约无法生成，已停止启动。" >&2
    return 1
  }
  typeset -g PFI_STREAMLIT_CACHE_KEY="$cache_key"
  if [[ -z "$PFI_STREAMLIT_CACHE_KEY" ]]; then
    echo "PFI 发布缓存契约无法生成，已停止启动。" >&2
    return 1
  fi
  pfi_release_require_hex "$PFI_STREAMLIT_CACHE_KEY" 64 streamlit_cache_key || return 1
  export PFI_STREAMLIT_CACHE_KEY
}

pfi_release_marker_value() {
  local marker_file="$1"
  local key="$2"
  [[ -f "$marker_file" ]] || return 1
  /usr/bin/awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "$marker_file"
}

pfi_release_identity_marker_matches() {
  local marker_file="$1"
  [[ "$(pfi_release_marker_value "$marker_file" PFI_ACTIVE_BUILD_ID || true)" == "$PFI_ACTIVE_BUILD_ID" ]] || return 1
  [[ "$(pfi_release_marker_value "$marker_file" PFI_ACTIVE_GIT_COMMIT || true)" == "$PFI_ACTIVE_GIT_COMMIT" ]] || return 1
  [[ "$(pfi_release_marker_value "$marker_file" PFI_ACTIVE_FRONTEND_HASH || true)" == "$PFI_ACTIVE_FRONTEND_HASH" ]] || return 1
  [[ "$(pfi_release_marker_value "$marker_file" PFI_ACTIVE_BACKEND_HASH || true)" == "$PFI_ACTIVE_BACKEND_HASH" ]] || return 1
  [[ "$(pfi_release_marker_value "$marker_file" PFI_RELEASE_MANIFEST_SHA256 || true)" == "$PFI_RELEASE_MANIFEST_SHA256" ]] || return 1
  [[ "$(pfi_release_marker_value "$marker_file" PFI_STREAMLIT_CACHE_KEY || true)" == "$PFI_STREAMLIT_CACHE_KEY" ]] || return 1
}

pfi_release_identity_marker_lines() {
  printf "PFI_ACTIVE_VERSION=%s\n" "$PFI_ACTIVE_VERSION"
  printf "PFI_ACTIVE_BUILD_ID=%s\n" "$PFI_ACTIVE_BUILD_ID"
  printf "PFI_ACTIVE_GIT_COMMIT=%s\n" "$PFI_ACTIVE_GIT_COMMIT"
  printf "PFI_ACTIVE_FRONTEND_HASH=%s\n" "$PFI_ACTIVE_FRONTEND_HASH"
  printf "PFI_ACTIVE_BACKEND_HASH=%s\n" "$PFI_ACTIVE_BACKEND_HASH"
  printf "PFI_RELEASE_MANIFEST_SHA256=%s\n" "$PFI_RELEASE_MANIFEST_SHA256"
  printf "PFI_STREAMLIT_CACHE_KEY=%s\n" "$PFI_STREAMLIT_CACHE_KEY"
  printf "PFI_ACTIVE_UI_CONTRACT=%s\n" "$PFI_ACTIVE_UI_CONTRACT"
}
