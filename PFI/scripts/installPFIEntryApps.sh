#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_APP="$ROOT_DIR/macos/PFI.app"
LAUNCHER_SOURCE="$ROOT_DIR/macos/PFI_launcher.c"
LAUNCHER_BINARY="$SOURCE_APP/Contents/MacOS/PFI"
DESKTOP_APP="$HOME/Desktop/PFI.app"
DOWNLOADS_APP="$HOME/Downloads/PFI.app"
APPLICATIONS_APP="/Applications/PFI.app"

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

clang -O2 -Wall -Wextra -o "$LAUNCHER_BINARY" "$LAUNCHER_SOURCE"
chmod +x "$LAUNCHER_BINARY"

install_app() {
  local target="$1"
  local staging
  staging="$(mktemp -d "${TMPDIR:-/tmp}/pfi_app.XXXXXX")"
  trap 'rm -rf "$staging"' RETURN
  /usr/bin/ditto --norsrc --noextattr --noacl "$SOURCE_APP" "$staging/PFI.app"
  mkdir -p "$staging/PFI.app/Contents/Resources"
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
  rm -rf "$DESKTOP_APP"
  ln -s "$APPLICATIONS_APP" "$DESKTOP_APP"
  echo "optional=$DESKTOP_APP status=linked_to_applications"
}

install_required_app "$DOWNLOADS_APP"
install_required_app "$APPLICATIONS_APP"
install_desktop_link

echo "PFI_ENTRY_APPS: installed"
echo "desktop=$DESKTOP_APP"
echo "downloads=$DOWNLOADS_APP"
echo "applications=$APPLICATIONS_APP"
