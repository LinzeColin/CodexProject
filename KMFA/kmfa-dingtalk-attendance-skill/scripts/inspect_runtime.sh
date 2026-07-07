#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${KMFA_REPO_ROOT:-/Users/linzezhang/CodexProject/KMFA}"
PRIVATE_RUNTIME="${KMFA_PRIVATE_RUNTIME:-$REPO_ROOT/metadata/dingtalk_attendance/private_runtime}"
ENV_FILE="${KMFA_ENV_FILE:-$PRIVATE_RUNTIME/.env.local}"
TARGETS_FILE="${KMFA_TARGETS_FILE:-$PRIVATE_RUNTIME/notification_targets.local.json}"
CONFIG_FILE="${KMFA_CONFIG_FILE:-$PRIVATE_RUNTIME/kmfa.attendance.config.json}"
OUT="${KMFA_RUNTIME_INSPECT_OUT:-$PRIVATE_RUNTIME/runtime_capability_manifest.json}"

mkdir -p "$PRIVATE_RUNTIME"
python3 - "$ENV_FILE" "$TARGETS_FILE" "$CONFIG_FILE" "$OUT" <<'PY'
import json, os, sys

env_file, targets_file, config_file, out = sys.argv[1:5]

def exists_nonempty(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0

def has_key(path, key):
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            return any(line.strip().startswith(key + "=") for line in f)
    except Exception:
        return False

manifest = {
    "env_file_present": exists_nonempty(env_file),
    "targets_file_present": exists_nonempty(targets_file),
    "config_file_present": exists_nonempty(config_file),
    "dws_app_key_configured": has_key(env_file, "DINGTALK_APP_KEY"),
    "dws_app_credential_configured": has_key(env_file, "DINGTALK_APP_CREDENTIAL"),
    "database_url_configured": has_key(env_file, "KMFA_DATABASE_URL"),
    "live_acquisition_capable": False,
    "database_ingest_capable": False,
    "notes": []
}
manifest["live_acquisition_capable"] = manifest["env_file_present"] and manifest["dws_app_key_configured"] and manifest["dws_app_credential_configured"]
manifest["database_ingest_capable"] = manifest["env_file_present"] and manifest["database_url_configured"]
if not manifest["live_acquisition_capable"]:
    manifest["notes"].append("live acquisition unavailable until DingTalk app credentials are configured locally")
if not manifest["database_ingest_capable"]:
    manifest["notes"].append("database ingestion unavailable until KMFA_DATABASE_URL is configured locally")

os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
PY
