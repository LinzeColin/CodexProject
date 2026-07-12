#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target_dir=${1:-"$PWD"}
roadmap_name='v1.2_四线14Stage升级_Roadmap.md'
archive_name='Memory_Atlas_v1.2_四线14Stage升级_TaskPack.zip'
roadmap_sha='699a8fe5f99a5edc88fec1f8940c4339f7b9b291bd31830f946f521f80904a71'
archive_sha='38e21ae3e94d860e6a40c70a629c8f7048f889164358df7b184bd8caf7bf2472'

mkdir -p "$target_dir"
cp "$script_dir/$roadmap_name" "$target_dir/$roadmap_name"
cp "$script_dir/$archive_name.part" "$target_dir/$archive_name"

actual_roadmap_sha=$(shasum -a 256 "$target_dir/$roadmap_name" | awk '{print $1}')
actual_archive_sha=$(shasum -a 256 "$target_dir/$archive_name" | awk '{print $1}')

if [ "$actual_roadmap_sha" != "$roadmap_sha" ]; then
  echo "Roadmap SHA-256 mismatch" >&2
  exit 1
fi
if [ "$actual_archive_sha" != "$archive_sha" ]; then
  echo "TaskPack SHA-256 mismatch" >&2
  exit 1
fi

printf '%s\n' "Restored and verified: $target_dir/$roadmap_name"
printf '%s\n' "Restored and verified: $target_dir/$archive_name"
