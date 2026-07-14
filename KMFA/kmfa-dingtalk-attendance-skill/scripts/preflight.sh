#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${KMFA_REPO_ROOT:-/Users/linzezhang/CodexProject/KMFA}"
TARGET_MONTH="${KMFA_TARGET_MONTH:-}"
ONEDRIVE_ROOT="${KMFA_ONEDRIVE_ROOT:-/Users/linzezhang/OneDrive/dingtalk_attendance}"
PRIVATE_RUNTIME="${KMFA_PRIVATE_RUNTIME:-$REPO_ROOT/metadata/dingtalk_attendance/private_runtime}"
REQUIRED_BRANCH="${KMFA_REQUIRED_BRANCH:-main}"
OUT_JSON="${KMFA_PREFLIGHT_OUT:-}"
TMP_JSON="${OUT_JSON:-/tmp/kmfa_preflight_$$.json}"

python3 - "$REPO_ROOT" "$ONEDRIVE_ROOT" "$PRIVATE_RUNTIME" "$REQUIRED_BRANCH" "$TARGET_MONTH" "$TMP_JSON" <<'PY'
import json, os, subprocess, sys
repo, onedrive, runtime, required_branch, target_month, out_json = sys.argv[1:7]
failures = []
warnings = []

def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def exists_cmd(name):
    return run(["bash", "-lc", f"command -v {name}"]).returncode == 0

if not os.path.isdir(repo):
    failures.append(f"repo_root_missing:{repo}")
else:
    inside = run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo)
    if inside.returncode != 0:
        failures.append(f"not_git_repo:{repo}")
    else:
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo).stdout.strip()
        if branch != required_branch:
            warnings.append(f"branch_is_{branch}_expected_{required_branch}")
        if run(["git", "diff", "--quiet"], cwd=repo).returncode != 0 or run(["git", "diff", "--cached", "--quiet"], cwd=repo).returncode != 0:
            warnings.append("working_tree_has_changes")
        if run(["git", "rev-parse", "--verify", f"origin/{required_branch}"], cwd=repo).returncode == 0:
            head = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
            remote = run(["git", "rev-parse", f"origin/{required_branch}"], cwd=repo).stdout.strip()
            if head != remote:
                warnings.append(f"HEAD_differs_from_origin_{required_branch}")
        else:
            warnings.append(f"origin_{required_branch}_not_available")

if not os.path.isdir(onedrive):
    failures.append(f"onedrive_root_missing:{onedrive}")
try:
    os.makedirs(runtime, exist_ok=True)
    probe = os.path.join(runtime, ".write_probe")
    with open(probe, "w", encoding="utf-8") as f:
        f.write("ok")
    os.remove(probe)
except Exception as e:
    failures.append(f"private_runtime_unwritable:{runtime}:{type(e).__name__}")

for cmd in ["python3"]:
    if not exists_cmd(cmd):
        failures.append(f"{cmd}_missing")
for cmd in ["jq", "psql", "dws", "shasum"]:
    if not exists_cmd(cmd):
        warnings.append(f"{cmd}_missing_optional_or_not_on_path")

result = {
    "status": "fail" if failures else "pass",
    "repo_root": repo,
    "onedrive_root": onedrive,
    "private_runtime": runtime,
    "required_branch": required_branch,
    "target_month": target_month,
    "failures": failures,
    "warnings": warnings,
}
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
if failures:
    sys.exit(1)
PY
