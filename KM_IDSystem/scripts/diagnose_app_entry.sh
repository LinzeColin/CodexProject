#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PATHS=(
  "$ROOT_DIR/app_bundle/IDS Industrial Data System.app"
  "$HOME/Downloads/IDS Industrial Data System.app"
  "/Applications/IDS Industrial Data System.app"
)

for app in "${APP_PATHS[@]}"; do
  echo "== $app =="
  if [ -d "$app" ]; then
    plutil -lint "$app/Contents/Info.plist"
    executable=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$app/Contents/Info.plist" 2>/dev/null || true)
    if [ -n "$executable" ] && [ -x "$app/Contents/MacOS/$executable" ]; then
      echo "launcher executable: $executable"
    else
      echo "launcher executable missing"
    fi
    xattr -lr "$app" 2>/dev/null | sed -n '1,20p' || true
  else
    echo "missing"
  fi
done
