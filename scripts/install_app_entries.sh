#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="Wuhan Kaiming OpMe.app"
COMMAND_NAME="Wuhan Kaiming OpMe.command"
BUILD_SCRIPT="$ROOT_DIR/scripts/build_app_bundle.sh"
SOURCE_APP="$ROOT_DIR/app_bundle/$APP_NAME"
DOWNLOADS_APP="$HOME/Downloads/$APP_NAME"
APPLICATIONS_APP="/Applications/$APP_NAME"
DOWNLOADS_COMMAND="$HOME/Downloads/$COMMAND_NAME"
APPLICATIONS_COMMAND="/Applications/$COMMAND_NAME"
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"

chmod +x "$BUILD_SCRIPT"
chmod +x "$ROOT_DIR/scripts/run_local_services.sh"
"$BUILD_SCRIPT" >/dev/null

clear_bundle_xattrs() {
  local path="$1"
  xattr -cr "$path" 2>/dev/null || true
  while IFS= read -r item; do
    xattr -d com.apple.FinderInfo "$item" 2>/dev/null || true
    xattr -d com.apple.ResourceFork "$item" 2>/dev/null || true
    xattr -d 'com.apple.fileprovider.fpfs#P' "$item" 2>/dev/null || true
  done < <(find "$path" -print)
  xattr -d com.apple.FinderInfo "$path" 2>/dev/null || true
  xattr -d com.apple.ResourceFork "$path" 2>/dev/null || true
  xattr -d 'com.apple.fileprovider.fpfs#P' "$path" 2>/dev/null || true
}

sign_app_best_effort() {
  local path="$1"
  clear_bundle_xattrs "$path"
  if /usr/bin/codesign --force --deep --sign - "$path" >/dev/null 2>&1; then
    clear_bundle_xattrs "$path"
  else
    echo "Warning: unable to sign $path; use $COMMAND_NAME if macOS blocks the .app." >&2
  fi
}

write_command_launcher() {
  local target="$1"
  cat > "$target" <<EOF
#!/bin/bash
set -euo pipefail

ROOT_DIR="$ROOT_DIR"
LOG_DIR="\$ROOT_DIR/data"
mkdir -p "\$LOG_DIR"
printf '[%s] Command launcher invoked\\n' "\$(date '+%Y-%m-%d %H:%M:%S')" >> "\$LOG_DIR/app_entry.log"

echo "Starting Wuhan Kaiming OpMe..."
cd "\$ROOT_DIR"
KEEP_TERMINAL_OPEN="\${KEEP_TERMINAL_OPEN:-1}" "\$ROOT_DIR/scripts/run_local_services.sh"

frontend_port="\$(cat "\$LOG_DIR/frontend_port" 2>/dev/null || true)"
if [ -n "\$frontend_port" ]; then
  echo
  echo "Wuhan Kaiming OpMe is running: http://127.0.0.1:\$frontend_port/"
fi
EOF
  chmod +x "$target"
  xattr -cr "$target" 2>/dev/null || true
  xattr -d com.apple.quarantine "$target" 2>/dev/null || true
}

rm -rf "$DOWNLOADS_APP"
cp -R "$SOURCE_APP" "$DOWNLOADS_APP"

rm -rf "$APPLICATIONS_APP"
cp -R "$SOURCE_APP" "$APPLICATIONS_APP"

clear_bundle_xattrs "$SOURCE_APP"
clear_bundle_xattrs "$DOWNLOADS_APP"
clear_bundle_xattrs "$APPLICATIONS_APP"
sign_app_best_effort "$DOWNLOADS_APP"
sign_app_best_effort "$APPLICATIONS_APP"

write_command_launcher "$DOWNLOADS_COMMAND"
write_command_launcher "$APPLICATIONS_COMMAND"

if [ -x "$LSREGISTER" ]; then
  "$LSREGISTER" -f "$DOWNLOADS_APP" >/dev/null 2>&1 || true
  "$LSREGISTER" -f "$APPLICATIONS_APP" >/dev/null 2>&1 || true
fi

echo "Installed:"
echo "$DOWNLOADS_APP"
echo "$APPLICATIONS_APP"
echo "$DOWNLOADS_COMMAND"
echo "$APPLICATIONS_COMMAND"
