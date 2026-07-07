from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FILES = [
    "KMFA/daily_routine_check_skill/SKILL.md",
    "KMFA/daily_routine_check_skill/README.md",
    "KMFA/daily_routine_check_skill/references/runbook.md",
    "KMFA/daily_routine_check_skill/references/configuration.md",
    "KMFA/daily_routine_check_skill/references/rules.md",
    "KMFA/daily_routine_check_skill/references/data_contract.md",
    "KMFA/daily_routine_check_skill/references/database_governance.md",
    "KMFA/daily_routine_check_skill/templates/env.local.example",
    "KMFA/daily_routine_check_skill/templates/notification_targets.local.example.json",
    "KMFA/metadata/daily_routine_check/README.md",
    "KMFA/metadata/daily_routine_check/routine_rules.public.yaml",
    "KMFA/metadata/daily_routine_check/cash_monitor.public.yaml",
    "KMFA/metadata/daily_routine_check/database_manifest.json",
    "KMFA/metadata/daily_routine_check/notification_policy.yaml",
    "KMFA/metadata/daily_routine_check/onedrive_storage_manifest.yaml",
    "KMFA/metadata/daily_routine_check/retention_policy.yaml",
    "KMFA/metadata/daily_routine_check/codex_automation/automation_manifest.json",
    "KMFA/metadata/daily_routine_check/codex_automation/daily_routine_check.prompt.md",
    "KMFA/tools/daily_routine_check/main.py",
    "KMFA/tools/daily_routine_check/git_autosync.py",
    "KMFA/tests/test_daily_routine_check.py",
]
BLOCKED_SUFFIXES = {".sqlite", ".db", ".jsonl", ".gz"}
BLOCKED_NAMES = {".env.local"}
BLOCKED_PATH_PARTS = {"private_runtime"}
PRIVATE_RUNTIME_ALLOWLIST = {"README.md", ".gitkeep"}
REQUIRED_PHRASES = [
    "Dingtalk-routine-check",
    "钉钉工作检查",
    "morning_1135",
    "evening_1705",
    "11:35",
    "17:05",
    "run_at_beijing",
    "trigger_window",
    "rules_evaluated",
    "rules_skipped",
    "SOURCE_MISSING",
    "SOURCE_STALE",
    "LATE_ROUTINE_ITEM",
    "WRONG_ROUTINE_ITEM",
    "MERGED_ROUTINE_ITEM",
    "abnormal_type",
    "reminder_level",
    "late",
    "review",
    "wrong",
    "merged",
    "P0",
    "P1",
    "P2",
    "资金账户明细表",
    "资金流水明细",
    "资金明细",
    "张霖泽",
    "Asia/Shanghai",
    "DWS_Outputs",
]


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (REPO_ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")

    searchable = []
    for rel in REQUIRED_FILES:
        path = REPO_ROOT / rel
        if path.exists() and path.suffix in {".md", ".yaml", ".json", ".py", ".example"}:
            searchable.append(path.read_text(encoding="utf-8", errors="ignore"))
    joined = "\n".join(searchable)
    for phrase in REQUIRED_PHRASES:
        if phrase not in joined:
            errors.append(f"missing required phrase: {phrase}")

    for base in [REPO_ROOT / "KMFA" / "daily_routine_check_skill", REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check"]:
        if base.exists():
            for path in base.rglob("*"):
                rel = path.relative_to(REPO_ROOT)
                if path.name in BLOCKED_NAMES or path.suffix in BLOCKED_SUFFIXES or any(part in rel.parts for part in BLOCKED_PATH_PARTS):
                    # private_runtime directory placeholder is allowed only if empty/.gitkeep; actual private files are not.
                    if path.is_dir() and path.name == "private_runtime":
                        continue
                    if "private_runtime" in rel.parts and path.name in PRIVATE_RUNTIME_ALLOWLIST:
                        continue
                    errors.append(f"blocked file in public package: {rel}")

    if errors:
        print("daily-routine-check skill validation FAILED")
        for err in errors:
            print("-", err)
        return 1
    print("daily-routine-check skill validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
