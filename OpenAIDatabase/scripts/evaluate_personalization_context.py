#!/usr/bin/env python3
"""Evaluate OpenAIDatabase personalization architecture completeness."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HARNESS_CONFIG = Path("config/evaluation/personalization_harness.json")
EVALUATION_LOG_DIR = Path("data/run_logs/evaluation_runs")


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
        if not (database_dir / "data/run_logs" / category_text).exists():
            failures.append(f"missing_log_directory:{category_text}")

    result = {
        "timestamp": now_utc(),
        "category": "evaluation_runs",
        "status": "PASS" if not failures else "FAIL",
        "task": "evaluate_personalization_context",
        "updated_targets": sorted(actual_targets),
        "source_files": [str(HARNESS_CONFIG), "data/derived/personalization/personalization_export.json"],
        "output_files": ["data/run_logs/evaluation_runs"],
        "tests": ["required_files", "required_sections", "sync_targets", "run_log_categories", "forbidden_patterns"],
        "failures": failures,
        "risks": ["pattern scan is a guardrail, not a full secret scanner"],
        "git_commit": "PENDING",
    }
    log_path = append_evaluation_log(database_dir, result)
    result["log"] = str(log_path.relative_to(database_dir))
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate personalization context architecture.")
    parser.add_argument("--database-dir", type=Path, default=Path("."), help="OpenAIDatabase repository root.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = evaluate(args.database_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
