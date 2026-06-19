#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
ENV_FILE="$PROJECT_DIR/.env"
EXAMPLE_FILE="$PROJECT_DIR/.env.example"

if [[ -f "$ENV_FILE" ]]; then
  echo ".env already exists: $ENV_FILE"
  echo "No changes made."
  exit 0
fi

cp "$EXAMPLE_FILE" "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo "Created: $ENV_FILE"
echo "Edit this file locally and fill only the API keys you have."
