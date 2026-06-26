#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pfi-ci-injected-failure.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

git -C "$TMP_DIR" init -q
FAKE_KEY_PREFIX="s""k-"
FAKE_KEY_BODY="pfiInjectedFailureProof000000000000"
cat > "$TMP_DIR/injected_secret.txt" <<'EOF'
This tracked file intentionally contains a fake key for PFI CI failure injection:
EOF
printf '%s%s\n' "$FAKE_KEY_PREFIX" "$FAKE_KEY_BODY" >> "$TMP_DIR/injected_secret.txt"
git -C "$TMP_DIR" add injected_secret.txt

set +e
PFI_SECRET_SCAN_ROOT="$TMP_DIR" scripts/secretScan.sh > "$TMP_DIR/secret_scan.out" 2>&1
STATUS="$?"
set -e

if [[ "$STATUS" == "0" ]]; then
  echo "PFI CI injected-failure proof failed: secretScan accepted the injected fake secret." >&2
  exit 1
fi

if ! grep -q "Secret scan failed" "$TMP_DIR/secret_scan.out"; then
  echo "PFI CI injected-failure proof failed: secretScan did not emit the expected failure marker." >&2
  sed -n '1,80p' "$TMP_DIR/secret_scan.out" >&2
  exit 1
fi

if ! grep -q "injected_secret.txt:openai_key" "$TMP_DIR/secret_scan.out"; then
  echo "PFI CI injected-failure proof failed: injected fake key was not classified as openai_key." >&2
  sed -n '1,80p' "$TMP_DIR/secret_scan.out" >&2
  exit 1
fi

echo "PFI CI injected-failure proof passed: secretScan rejected the injected fake key."
