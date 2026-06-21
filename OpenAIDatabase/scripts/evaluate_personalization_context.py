#!/usr/bin/env python3
"""Evaluate OpenAIDatabase personalization architecture completeness."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HARNESS_CONFIG = Path("config/evaluation/personalization_harness.json")
TASK_RUN_SCHEMA = Path("config/evaluation/task_run.schema.json")
RUN_LOG_ROOT = Path("data/run_logs")
EVALUATION_LOG_DIR = Path("data/run_logs/evaluation_runs")
VALID_RUN_TYPES = {"sync_run", "export_run", "evaluation_run", "agent_run"}
VALID_STATUSES = {"PASS", "FAIL", "NOT_RUN"}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def git_head(database_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=database_dir,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_NO_GIT_HEAD"


def rel_to_database(database_dir: Path, path: Path) -> str:
    try:
        return str(path.relative_to(database_dir))
    except ValueError:
        return str(path)


def is_pending(value: Any) -> bool:
    return isinstance(value, str) and value.upper() == "PENDING"


def require_list(row: dict[str, Any], field: str, failures: list[str], prefix: str) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list):
        failures.append(f"{prefix}:field_not_list:{field}")
        return []
    return value


def validate_task_run_record(database_dir: Path, path: Path, line_no: int, row: Any, failures: list[str]) -> None:
    scope = f"{rel_to_database(database_dir, path)}:{line_no}"
    if not isinstance(row, dict):
        failures.append(f"invalid_jsonl_row:{scope}:not_object")
        return

    required = [
        "task_id",
        "run_type",
        "status",
        "context_used",
        "tools_used",
        "tests_run",
        "failure_recovery",
        "base_commit",
        "result_commit",
        "residual_risks",
    ]
    for field in required:
        if field not in row:
            failures.append(f"task_run_missing_field:{scope}:{field}")

    task_id = row.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        failures.append(f"task_run_invalid_task_id:{scope}")

    run_type = row.get("run_type")
    if run_type not in VALID_RUN_TYPES:
        failures.append(f"task_run_invalid_run_type:{scope}:{run_type}")

    status = row.get("status")
    if status not in VALID_STATUSES:
        failures.append(f"task_run_invalid_status:{scope}:{status}")
    if status == "NOT_RUN" and not str(row.get("not_run_reason") or "").strip():
        failures.append(f"task_run_not_run_missing_reason:{scope}")

    for field in ("git_commit", "base_commit", "result_commit"):
        if is_pending(row.get(field)):
            failures.append(f"task_run_pending_commit:{scope}:{field}")

    for idx, item in enumerate(require_list(row, "context_used", failures, scope), 1):
        if not isinstance(item, dict):
            failures.append(f"context_used_not_object:{scope}:{idx}")
            continue
        if not str(item.get("source") or "").strip():
            failures.append(f"context_used_missing_source:{scope}:{idx}")
        if not str(item.get("reason") or "").strip():
            failures.append(f"context_used_missing_reason:{scope}:{idx}")

    for idx, item in enumerate(require_list(row, "tools_used", failures, scope), 1):
        if not isinstance(item, dict):
            failures.append(f"tools_used_not_object:{scope}:{idx}")
            continue
        for field in ("tool", "operation", "result"):
            if not str(item.get(field) or "").strip():
                failures.append(f"tools_used_missing_{field}:{scope}:{idx}")

    tests = require_list(row, "tests_run", failures, scope)
    if status == "PASS" and not tests:
        failures.append(f"task_run_pass_without_tests:{scope}")
    for idx, item in enumerate(tests, 1):
        if not isinstance(item, dict):
            failures.append(f"tests_run_not_object:{scope}:{idx}")
            continue
        command = str(item.get("command") or "").strip()
        result = item.get("result")
        if not command:
            failures.append(f"tests_run_missing_command:{scope}:{idx}")
        if result not in VALID_STATUSES:
            failures.append(f"tests_run_invalid_result:{scope}:{idx}:{result}")
        if result == "PASS" and item.get("exit_code") != 0:
            failures.append(f"tests_run_pass_without_exit_code_zero:{scope}:{idx}")
        if result == "NOT_RUN" and not str(item.get("not_run_reason") or "").strip():
            failures.append(f"tests_run_not_run_missing_reason:{scope}:{idx}")
        evidence = str(item.get("evidence") or "").strip()
        if result == "PASS" and not evidence:
            failures.append(f"tests_run_pass_missing_evidence:{scope}:{idx}")
        if evidence and not (database_dir / evidence).exists():
            failures.append(f"tests_run_missing_evidence_file:{scope}:{idx}:{evidence}")

    require_list(row, "failure_recovery", failures, scope)
    require_list(row, "residual_risks", failures, scope)


def validate_run_logs(database_dir: Path) -> list[str]:
    failures: list[str] = []
    schema = read_json(database_dir / TASK_RUN_SCHEMA)
    if not schema:
        failures.append(f"missing_or_invalid_schema:{TASK_RUN_SCHEMA}")

    log_root = database_dir / RUN_LOG_ROOT
    jsonl_files = sorted(log_root.glob("*/*.jsonl"))
    if not jsonl_files:
        failures.append("missing_jsonl_run_logs")
        return failures

    for path in jsonl_files:
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"invalid_jsonl:{rel_to_database(database_dir, path)}:{line_no}:{exc.msg}")
                continue
            validate_task_run_record(database_dir, path, line_no, row, failures)
    return failures


def append_evaluation_log(database_dir: Path, row: dict[str, Any]) -> Path:
    log_dir = database_dir / EVALUATION_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    day = row["timestamp"][:10]
    log_path = log_dir / f"{day}.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return log_path


def evaluate(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    harness = read_json(database_dir / HARNESS_CONFIG)
    required_files = harness.get("required_files", [])
    required_sections = harness.get("required_export_sections", [])
    required_targets = harness.get("required_update_targets", [])
    required_logs = harness.get("required_log_categories", [])
    forbidden_patterns = harness.get("forbidden_plaintext_patterns", [])
    failures: list[str] = []

    if not isinstance(required_files, list):
        required_files = []
    if not isinstance(required_sections, list):
        required_sections = []
    if not isinstance(required_targets, list):
        required_targets = []
    if not isinstance(required_logs, list):
        required_logs = []
    if not isinstance(forbidden_patterns, list):
        forbidden_patterns = []

    for file_name in required_files:
        if not (database_dir / str(file_name)).exists():
            failures.append(f"missing_required_file:{file_name}")

    chatgpt_export = read_text(database_dir / "data/derived/personalization/chatgpt_personalization.md")
    codex_export = read_text(database_dir / "data/derived/personalization/codex_personalization.md")
    combined_text = f"{chatgpt_export}\n{codex_export}"
    for section in required_sections:
        if str(section) not in combined_text:
            failures.append(f"missing_export_section:{section}")
    for pattern in forbidden_patterns:
        if pattern and str(pattern) in combined_text:
            failures.append(f"forbidden_plaintext_pattern:{pattern}")

    export_payload = read_json(database_dir / "data/derived/personalization/personalization_export.json")
    actual_targets = set(export_payload.get("sync_required_targets", [])) if isinstance(export_payload.get("sync_required_targets"), list) else set()
    for target in required_targets:
        if str(target) not in actual_targets:
            failures.append(f"missing_sync_target:{target}")
    actual_logs = set(export_payload.get("run_log_categories", [])) if isinstance(export_payload.get("run_log_categories"), list) else set()
    for category in required_logs:
        category_text = str(category)
        if category_text not in actual_logs:
            failures.append(f"missing_log_category_in_export:{category_text}")
        category_dir = database_dir / "data/run_logs" / category_text
        if not category_dir.exists():
            failures.append(f"missing_log_directory:{category_text}")
        elif not any(category_dir.glob("*.jsonl")):
            failures.append(f"missing_log_records:{category_text}")

    failures.extend(validate_run_logs(database_dir))

    head = git_head(database_dir)
    result = {
        "timestamp": now_utc(),
        "category": "evaluation_runs",
        "task_id": "TASK-OAI-D-001",
        "run_type": "evaluation_run",
        "status": "PASS" if not failures else "FAIL",
        "task": "evaluate_personalization_context",
        "updated_targets": sorted(actual_targets),
        "source_files": [str(HARNESS_CONFIG), "data/derived/personalization/personalization_export.json"],
        "output_files": ["data/run_logs/evaluation_runs"],
        "context_used": [
            {"source": str(HARNESS_CONFIG), "reason": "evaluation harness contract"},
            {"source": str(TASK_RUN_SCHEMA), "reason": "task-run evidence schema"},
            {"source": "data/derived/personalization/personalization_export.json", "reason": "generated personalization export"},
        ],
        "tools_used": [
            {"tool": "python", "operation": "evaluate_personalization_context", "result": "success" if not failures else "failure"}
        ],
        "tests": [
            "required_files",
            "required_sections",
            "sync_targets",
            "run_log_categories",
            "run_log_records",
            "task_run_schema",
            "jsonl_parse",
            "task_run_evidence",
            "forbidden_patterns",
        ],
        "tests_run": [
            {
                "command": "python3 scripts/evaluate_personalization_context.py --database-dir .",
                "exit_code": 0 if not failures else 2,
                "result": "PASS" if not failures else "FAIL",
                "evidence": "data/run_logs/evaluation_runs",
            }
        ],
        "failure_recovery": [] if not failures else [{"failure_count": len(failures), "action": "fix reported failures and rerun evaluator"}],
        "failures": failures,
        "risks": ["pattern scan is a guardrail, not a full secret scanner"],
        "base_commit": head,
        "result_commit": head,
        "residual_risks": ["pattern scan is a guardrail, not a full secret scanner"],
    }
    result["log"] = "not_appended_default_ci_safe"
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate personalization context architecture.")
    parser.add_argument("--database-dir", type=Path, default=Path("."), help="OpenAIDatabase repository root.")
    parser.add_argument("--write-log", action="store_true", help="Append an evaluation run log. CI should omit this to keep the tree clean.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = evaluate(args.database_dir)
    if args.write_log:
        log_path = append_evaluation_log(args.database_dir.resolve(), result)
        result["log"] = str(log_path.relative_to(args.database_dir.resolve()))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
