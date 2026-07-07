#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${KMFA_REPO_ROOT:-/Users/linzezhang/CodexProject/KMFA}"
SKILL_DIR="${KMFA_SKILL_DIR:-$REPO_ROOT/kmfa-dingtalk-attendance-skill}"
PRIVATE_RUNTIME="${KMFA_PRIVATE_RUNTIME:-$REPO_ROOT/metadata/dingtalk_attendance/private_runtime}"
OUT="${KMFA_VALIDATE_OUT:-$PRIVATE_RUNTIME/offline_validate_manifest.json}"
mkdir -p "$(dirname "$OUT")"

python3 - "$SKILL_DIR" "$OUT" <<'PY'
import ast, json, os, sys
skill_dir, out = sys.argv[1:3]
failures=[]
warnings=[]
checked=[]

for rel in ["SKILL.md", "references/stage2_shadow_payroll_acceptance.md", "scripts/month_gate.py", "scripts/stage2_consensus_gate.py", "scripts/write_stage2_run_artifacts.py", "scripts/validate_database_contract.py", "scripts/resolve_stage2_source.py"]:
    path = os.path.join(skill_dir, rel)
    checked.append(rel)
    if not os.path.exists(path):
        failures.append(f"missing:{rel}")

scripts_dir = os.path.join(skill_dir, "scripts")
if os.path.isdir(scripts_dir):
    for name in sorted(os.listdir(scripts_dir)):
        if name.endswith(".py"):
            path = os.path.join(scripts_dir, name)
            checked.append(f"syntax:{name}")
            try:
                with open(path, encoding="utf-8") as f:
                    ast.parse(f.read(), filename=path)
            except SyntaxError as e:
                failures.append(f"syntax_error:{name}:{e.lineno}:{e.msg}")
else:
    failures.append("scripts_dir_missing")

skill_md = os.path.join(skill_dir, "SKILL.md")
if os.path.isfile(skill_md):
    text = open(skill_md, encoding="utf-8").read()
    for required in ["name: kmfa-dingtalk-attendance-skill", "stage-2", "location", "trajectory", "Q5"]:
        if required not in text:
            warnings.append(f"skill_missing_keyword:{required}")

result={"status":"fail" if failures else "pass", "checked": checked, "failures": failures, "warnings": warnings}
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
if failures:
    sys.exit(1)
PY
