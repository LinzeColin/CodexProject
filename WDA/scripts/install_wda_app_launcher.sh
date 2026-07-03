#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_SCRIPT="$SCRIPT_DIR/wda_app_start.sh"
DOWNLOADS_DIR="${WDA_DOWNLOADS_DIR:-/Users/linzezhang/Downloads}"
COMMAND_PATH="$DOWNLOADS_DIR/WDA.command"
APP_DIR="$DOWNLOADS_DIR/WDA.app"
APP_EXEC="$APP_DIR/Contents/MacOS/WDA"

mkdir -p "$DOWNLOADS_DIR" "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"

cat > "$COMMAND_PATH" <<EOF
#!/usr/bin/env bash
exec "$START_SCRIPT"
EOF
chmod +x "$COMMAND_PATH"

cat > "$APP_EXEC" <<EOF
#!/usr/bin/env bash
exec "$START_SCRIPT"
EOF
chmod +x "$APP_EXEC"

cat > "$APP_DIR/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>WDA</string>
  <key>CFBundleIdentifier</key>
  <string>com.linze.wda.v0-2-r3</string>
  <key>CFBundleName</key>
  <string>WDA</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleVersion</key>
  <string>0.2-r3</string>
</dict>
</plist>
EOF

echo "Installed WDA launcher:"
echo "- $COMMAND_PATH"
echo "- $APP_DIR"
