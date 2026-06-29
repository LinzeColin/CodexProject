#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_APP="$ROOT_DIR/macos/PFI.app"
LAUNCHER_SOURCE="$ROOT_DIR/macos/PFI_launcher.c"
DESKTOP_APP="$HOME/Desktop/PFI.app"
DOWNLOADS_APP="$HOME/Downloads/PFI.app"
APPLICATIONS_APP="/Applications/PFI.app"
INSTALL_SCOPE="all"

for arg in "$@"; do
  case "$arg" in
    --downloads-only)
      INSTALL_SCOPE="downloads"
      ;;
    --all)
      INSTALL_SCOPE="all"
      ;;
    *)
      echo "Usage: $0 [--downloads-only|--all]" >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "$SOURCE_APP" ]]; then
  echo "PFI_ENTRY_APPS: source app missing: $SOURCE_APP" >&2
  exit 1
fi
if [[ ! -f "$LAUNCHER_SOURCE" ]]; then
  echo "PFI_ENTRY_APPS: launcher source missing: $LAUNCHER_SOURCE" >&2
  exit 1
fi
if ! command -v clang >/dev/null 2>&1; then
  echo "PFI_ENTRY_APPS: clang is required to build the native launcher" >&2
  exit 1
fi

BUILT_LAUNCHER_BINARY="$(mktemp "${TMPDIR:-/tmp}/pfi_launcher.XXXXXX")"
trap 'rm -f "$BUILT_LAUNCHER_BINARY"' EXIT
clang -O2 -Wall -Wextra -o "$BUILT_LAUNCHER_BINARY" "$LAUNCHER_SOURCE"
chmod +x "$BUILT_LAUNCHER_BINARY"

install_app() {
  local target="$1"
  local staging
  staging="$(mktemp -d "${TMPDIR:-/tmp}/pfi_app.XXXXXX")"
  trap 'rm -rf "$staging"' RETURN
  /usr/bin/ditto --norsrc --noextattr --noacl "$SOURCE_APP" "$staging/PFI.app"
  mkdir -p "$staging/PFI.app/Contents/Resources"
  install -m 755 "$BUILT_LAUNCHER_BINARY" "$staging/PFI.app/Contents/MacOS/PFI"
  printf "%s\n" "$ROOT_DIR" > "$staging/PFI.app/Contents/Resources/PFI_PROJECT_ROOT"
  chmod +x "$staging/PFI.app/Contents/MacOS/PFI"
  xattr -cr "$staging/PFI.app" >/dev/null 2>&1 || true
  /usr/bin/codesign --force --deep --sign - "$staging/PFI.app"
  /usr/bin/codesign --verify --deep --strict "$staging/PFI.app"
  rm -rf "$target"
  /usr/bin/ditto --norsrc --noextattr --noacl "$staging/PFI.app" "$target"
  chmod +x "$target/Contents/MacOS/PFI"
  xattr -cr "$target" >/dev/null 2>&1 || true
  /usr/bin/codesign --verify --deep --strict "$target"
  rm -rf "$staging"
  trap - RETURN
}

install_required_app() {
  local target="$1"
  install_app "$target"
}

install_optional_app() {
  local target="$1"
  if install_app "$target"; then
    echo "optional=$target status=installed"
  else
    echo "optional=$target status=warning codesign_or_metadata_cleanup_failed" >&2
  fi
}

install_desktop_link() {
  if [[ -L "$DESKTOP_APP" && "$(readlink "$DESKTOP_APP")" == "$APPLICATIONS_APP" ]]; then
    echo "optional=$DESKTOP_APP status=already_linked_to_applications"
    return 0
  fi
  if rm -rf "$DESKTOP_APP" 2>/dev/null && ln -s "$APPLICATIONS_APP" "$DESKTOP_APP" 2>/dev/null; then
    echo "optional=$DESKTOP_APP status=linked_to_applications"
  else
    echo "optional=$DESKTOP_APP status=warning desktop_link_not_changed" >&2
    if [[ -e "$DESKTOP_APP" || -L "$DESKTOP_APP" ]]; then
      echo "optional=$DESKTOP_APP existing_target=$(readlink "$DESKTOP_APP" 2>/dev/null || printf existing_non_symlink)" >&2
    fi
  fi
}

install_required_app "$DOWNLOADS_APP"
if [[ "$INSTALL_SCOPE" == "all" ]]; then
  install_required_app "$APPLICATIONS_APP"
  install_desktop_link
fi

echo "PFI_ENTRY_APPS: installed"
echo "scope=$INSTALL_SCOPE"
if [[ "$INSTALL_SCOPE" == "all" ]]; then
  echo "desktop=$DESKTOP_APP"
fi
echo "downloads=$DOWNLOADS_APP"
if [[ "$INSTALL_SCOPE" == "all" ]]; then
  echo "applications=$APPLICATIONS_APP"
fi
