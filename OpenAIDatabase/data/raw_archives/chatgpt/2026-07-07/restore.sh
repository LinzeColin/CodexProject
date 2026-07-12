#!/usr/bin/env bash
set -euo pipefail

expected_sha="52f204dd8d78b76a79c6fc37e3e09987d3ab682c87098da017b894dd88c3a868"
output="6c7acaff424d50d929d3779259c2c0eccd140d4afdf99ae1816dc673988dcd83-2026-07-07-04-49-46-53d01542c71941e199f8cdac3bbda0ce.zip"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

cat parts/chatgpt_raw_export_2026-07-07.zip.part-* > "$output"
actual_sha="$(shasum -a 256 "$output" | awk '{print $1}')"

if [[ "$actual_sha" != "$expected_sha" ]]; then
  echo "SHA256 mismatch: expected $expected_sha got $actual_sha" >&2
  exit 1
fi

echo "$actual_sha  $output"
