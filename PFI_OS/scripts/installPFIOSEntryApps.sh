#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_APP="$ROOT_DIR/macos/PFI_OS.app"
LAUNCHER_SOURCE="$ROOT_DIR/macos/PFI_OS_launcher.c"
LAUNCHER_BINARY="$SOURCE_APP/Contents/MacOS/PFI_OS"
DESKTOP_APP="$HOME/Desktop/PFI_OS.app"
DOWNLOADS_APP="$HOME/Downloads/PFI_OS.app"
APPLICATIONS_APP="/Applications/PFI_OS.app"

if [[ ! -d "$SOURCE_APP" ]]; then
  echo "PFI_OS_ENTRY_APPS: source app missing: $SOURCE_APP" >&2
  exit 1
fi
if [[ ! -f "$LAUNCHER_SOURCE" ]]; then
  echo "PFI_OS_ENTRY_APPS: launcher source missing: $LAUNCHER_SOURCE" >&2
  exit 1
fi
if ! command -v clang >/dev/null 2>&1; then
  echo "PFI_OS_ENTRY_APPS: clang is required to build the native launcher" >&2
  exit 1
fi

clang -O2 -Wall -Wextra -o "$LAUNCHER_BINARY" "$LAUNCHER_SOURCE"
chmod +x "$LAUNCHER_BINARY"

install_app() {
  local target="$1"
  local staging
  staging="$(mktemp -d "${TMPDIR:-/tmp}/pfi_os_app.XXXXXX")"
  trap 'rm -rf "$staging"' RETURN
  /usr/bin/ditto --norsrc --noextattr --noacl "$SOURCE_APP" "$staging/PFI_OS.app"
  mkdir -p "$staging/PFI_OS.app/Contents/Resources"
  printf "%s\n" "$ROOT_DIR" > "$staging/PFI_OS.app/Contents/Resources/PFI_OS_PROJECT_ROOT"
  chmod +x "$staging/PFI_OS.app/Contents/MacOS/PFI_OS"
  xattr -cr "$staging/PFI_OS.app" >/dev/null 2>&1 || true
  /usr/bin/codesign --force --deep --sign - "$staging/PFI_OS.app"
  /usr/bin/codesign --verify --deep --strict "$staging/PFI_OS.app"
  rm -rf "$target"
  /usr/bin/ditto --norsrc --noextattr --noacl "$staging/PFI_OS.app" "$target"
  chmod +x "$target/Contents/MacOS/PFI_OS"
  /usr/bin/codesign --verify --deep --strict "$target"
  rm -rf "$staging"
  trap - RETURN
}

install_app "$DESKTOP_APP"
install_app "$DOWNLOADS_APP"
install_app "$APPLICATIONS_APP"

echo "PFI_OS_ENTRY_APPS: installed"
echo "desktop=$DESKTOP_APP"
echo "downloads=$DOWNLOADS_APP"
echo "applications=$APPLICATIONS_APP"
