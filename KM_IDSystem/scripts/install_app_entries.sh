#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="IDS Industrial Data System.app"
COMMAND_NAME="IDS Industrial Data System.command"
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
    echo "Warning: unable to sign $path; macOS may require manual approval for the app." >&2
  fi
}

rm -rf "$DOWNLOADS_APP"
cp -R "$SOURCE_APP" "$DOWNLOADS_APP"

rm -rf "$APPLICATIONS_APP"
cp -R "$SOURCE_APP" "$APPLICATIONS_APP"

cat > "$DOWNLOADS_COMMAND" <<EOF
#!/usr/bin/env bash
cd "$ROOT_DIR"
exec "$ROOT_DIR/scripts/run_local_services.sh"
EOF
chmod +x "$DOWNLOADS_COMMAND"

cp "$DOWNLOADS_COMMAND" "$APPLICATIONS_COMMAND"
chmod +x "$APPLICATIONS_COMMAND"

clear_bundle_xattrs "$SOURCE_APP"
clear_bundle_xattrs "$DOWNLOADS_APP"
clear_bundle_xattrs "$APPLICATIONS_APP"
clear_bundle_xattrs "$DOWNLOADS_COMMAND"
clear_bundle_xattrs "$APPLICATIONS_COMMAND"
sign_app_best_effort "$DOWNLOADS_APP"
sign_app_best_effort "$APPLICATIONS_APP"

if [ -x "$LSREGISTER" ]; then
  "$LSREGISTER" -f "$DOWNLOADS_APP" >/dev/null 2>&1 || true
  "$LSREGISTER" -f "$APPLICATIONS_APP" >/dev/null 2>&1 || true
fi

echo "Installed:"
echo "$DOWNLOADS_APP"
echo "$APPLICATIONS_APP"
echo "$DOWNLOADS_COMMAND"
echo "$APPLICATIONS_COMMAND"
