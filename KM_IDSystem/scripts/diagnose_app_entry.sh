#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PATHS=(
  "$ROOT_DIR/app_bundle/IDS Industrial Data System.app"
  "$HOME/Downloads/IDS Industrial Data System.app"
  "/Applications/IDS Industrial Data System.app"
)
COMMAND_PATHS=(
  "$HOME/Downloads/IDS Industrial Data System.command"
  "/Applications/IDS Industrial Data System.command"
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

for command_path in "${COMMAND_PATHS[@]}"; do
  echo "== $command_path =="
  if [ -f "$command_path" ]; then
    if [ -x "$command_path" ]; then
      echo "command launcher executable"
    else
      echo "command launcher exists but is not executable"
    fi
    xattr -l "$command_path" 2>/dev/null || true
    sed -n '1,20p' "$command_path"
  else
    echo "missing"
  fi
done
