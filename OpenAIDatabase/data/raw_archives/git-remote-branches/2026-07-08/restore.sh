#!/usr/bin/env bash
set -euo pipefail

expected_sha="ec03e395898169ff1a625732bb1cb1582c5576e0f611c1be91d7ffad78f928e6"
output="codexproject_remote_non_main_branches_20260708.bundle"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

cat parts/codexproject_remote_non_main_branches_20260708.bundle.part-* > "$output"
actual_sha="$(shasum -a 256 "$output" | awk '{print $1}')"
if [[ "$actual_sha" != "$expected_sha" ]]; then
  echo "SHA256 mismatch: expected $expected_sha got $actual_sha" >&2
  exit 1
fi

git bundle verify "$output"
echo "$actual_sha  $output"
