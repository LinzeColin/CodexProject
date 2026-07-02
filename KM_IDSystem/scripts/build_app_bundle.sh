#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="IDS Industrial Data System.app"
APP_SOURCE="$ROOT_DIR/app_bundle/native_launcher.c"
APP_DIR="$ROOT_DIR/app_bundle/$APP_NAME"
EXECUTABLE="IDSIndustrialDataSystem"
ICON_FILE="OpMeIcon.icns"
ICON_SOURCE="$ROOT_DIR/app_bundle/assets/$ICON_FILE"

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

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"
if [ ! -f "$ICON_SOURCE" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    "$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/scripts/generate_app_icon.py" >/dev/null
  else
    echo "Warning: $ICON_SOURCE is missing and .venv/bin/python is unavailable." >&2
  fi
fi
compile_flags=(
  "-DIDS_PROJECT_DIR=\"$ROOT_DIR\""
  "-DIDS_RUN_SCRIPT=\"$ROOT_DIR/scripts/run_local_services.sh\""
  "-DIDS_LOG_FILE=\"$ROOT_DIR/data/app_entry.log\""
)
/usr/bin/clang "${compile_flags[@]}" "$APP_SOURCE" -o "$APP_DIR/Contents/MacOS/$EXECUTABLE"
chmod +x "$APP_DIR/Contents/MacOS/$EXECUTABLE"
if [ -f "$ICON_SOURCE" ]; then
  cp "$ICON_SOURCE" "$APP_DIR/Contents/Resources/$ICON_FILE"
fi
cat > "$APP_DIR/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>$EXECUTABLE</string>
  <key>CFBundleIconFile</key>
  <string>OpMeIcon</string>
  <key>CFBundleIdentifier</key>
  <string>com.linze.ids.industrial-data-system.native</string>
  <key>CFBundleName</key>
  <string>IDS Industrial Data System</string>
  <key>CFBundleDisplayName</key>
  <string>IDS Industrial Data System</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0.1</string>
  <key>CFBundleVersion</key>
  <string>2</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
EOF
printf 'APPL????' > "$APP_DIR/Contents/PkgInfo"
clear_bundle_xattrs "$APP_DIR"
if /usr/bin/codesign --force --deep --sign - "$APP_DIR" >/dev/null; then
  clear_bundle_xattrs "$APP_DIR"
else
  echo "Warning: app bundle signing failed; installing .command launcher remains supported." >&2
fi
echo "$APP_DIR"
