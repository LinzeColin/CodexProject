#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PACKAGED_PATH_TRIGGERS = {
    "*.md",
    "VERSION",
    "CHECKSUMS.sha256",
    "manifest.txt",
    "DIRECTORY_TREE.txt",
    "docs/**",
    "data/**",
    "models/**",
    "config/**",
    "specs/**",
    "prototype/**",
    "scripts/**",
    ".github/**",
}

REQUIRED_WORKFLOW_COMMANDS = {
    "python scripts/validate_catalog_integrity.py",
    "python scripts/validate_governance.py",
    "python scripts/validate_task_pack.py",
    "python scripts/validate_governance_consistency.py",
    "sha256sum -c CHECKSUMS.sha256",
}

REQUIRED_RELEASE_FILES = {
    "manifest.txt",
    "DIRECTORY_TREE.txt",
    "CHECKSUMS.sha256",
    "artifacts/release_evidence_t1211.json",
    "artifacts/release_operation_log_t1211.jsonl",
}


def read_text(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(read_text(path))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must be a YAML object")
    return payload


def read_csv(path: str) -> list[dict[str, str]]:
    target = ROOT / path
    if not target.is_file():
        raise AssertionError(f"missing required CSV: {path}")
    with target.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def split_ids(value: str) -> list[str]:
    ids: list[str] = []
    for item in [part.strip() for part in re.split(r"[;,]", value or "") if part.strip()]:
        range_match = re.fullmatch(r"([A-Z]+)(\d+)-([A-Z]+)(\d+)", item)
        if not range_match:
            ids.append(item)
            continue
        start_prefix, start_number, end_prefix, end_number = range_match.groups()
        if start_prefix != end_prefix:
            ids.append(item)
            continue
        width = max(len(start_number), len(end_number))
        start = int(start_number)
        end = int(end_number)
        step = 1 if end >= start else -1
        ids.extend(
            f"{start_prefix}{number:0{width}d}" for number in range(start, end + step, step)
        )
    return ids


def validate_packaged_workflow() -> dict[str, Any]:
    workflow_path = ROOT / ".github/workflows/governance-validation.yml"
    workflow = load_yaml(workflow_path)
    events = workflow.get(True) or workflow.get("on")
    if not isinstance(events, dict):
        raise AssertionError("governance-validation workflow must define events")
    pull_request = events.get("pull_request")
    if not isinstance(pull_request, dict):
        raise AssertionError("governance-validation workflow must run on pull_request")
    paths = pull_request.get("paths")
    if not isinstance(paths, list):
        raise AssertionError("governance-validation pull_request must define path filters")
    missing_triggers = sorted(REQUIRED_PACKAGED_PATH_TRIGGERS - set(paths))
    if missing_triggers:
        raise AssertionError(f"governance-validation missing path triggers: {missing_triggers}")
    if "workflow_dispatch" not in events:
        raise AssertionError("governance-validation must support workflow_dispatch")
    push = events.get("push")
    if not isinstance(push, dict) or "main" not in push.get("branches", []):
        raise AssertionError("governance-validation must run on pushes to main")

    workflow_text = read_text(workflow_path)
    missing_commands = sorted(
        command for command in REQUIRED_WORKFLOW_COMMANDS if command not in workflow_text
    )
    if missing_commands:
        raise AssertionError(f"governance-validation missing commands: {missing_commands}")
    return {
        "workflow": ".github/workflows/governance-validation.yml",
        "path_triggers": sorted(REQUIRED_PACKAGED_PATH_TRIGGERS),
        "commands": sorted(REQUIRED_WORKFLOW_COMMANDS),
    }


def validate_root_workflow_if_present() -> dict[str, Any]:
    root_workflow = ROOT.parent / ".github/workflows/eei-validation.yml"
    if not root_workflow.is_file():
        return {
            "workflow": "../.github/workflows/eei-validation.yml",
            "status": "not_present_in_clean_room_package",
        }
    payload = yaml.safe_load(root_workflow.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError("../.github/workflows/eei-validation.yml must be a YAML object")
    events = payload.get(True) or payload.get("on")
    if not isinstance(events, dict):
        raise AssertionError("root EEI workflow must define events")
    for event_name in ("push", "pull_request"):
        event = events.get(event_name)
        if not isinstance(event, dict):
            raise AssertionError(f"root EEI workflow missing {event_name}")
        paths = event.get("paths")
        if not isinstance(paths, list) or "EEI/**" not in paths:
            raise AssertionError(f"root EEI workflow {event_name} must include EEI/** path trigger")
    root_text = root_workflow.read_text(encoding="utf-8")
    for phrase in ["working-directory: EEI", "make verify"]:
        if phrase not in root_text:
            raise AssertionError(f"root EEI workflow missing phrase: {phrase}")
    return {
        "workflow": "../.github/workflows/eei-validation.yml",
        "status": "validated",
        "path_trigger": "EEI/**",
        "delegates_to": "make verify",
    }


def validate_makefile_target() -> dict[str, Any]:
    makefile = read_text(ROOT / "Makefile")
    required_phrases = [
        "validate-governance-consistency:",
        "scripts/validate_governance_consistency.py",
        "verify: validate-governance validate-contracts validate-prototype-parity "
        "validate-github-governance validate-governance-consistency "
        "validate-release-artifacts",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in makefile]
    if missing:
        raise AssertionError(f"Makefile missing governance consistency phrases: {missing}")
    return {"target": "validate-governance-consistency", "wired_into": "make verify"}


def validate_p0_traceability() -> dict[str, Any]:
    functions = read_csv("data/function_catalog.csv")
    tasks = {row["task_id"] for row in read_csv("data/task_backlog.csv")}
    acceptance = {row["acceptance_id"] for row in read_csv("data/acceptance_matrix.csv")}
    traces = read_csv("data/acceptance_traceability.csv")
    traces_by_function: dict[str, list[dict[str, str]]] = {}
    for trace in traces:
        traces_by_function.setdefault(trace["requirement_or_function_id"], []).append(trace)

    checked_functions = 0
    for function in functions:
        if function["priority"] != "P0":
            continue
        checked_functions += 1
        function_id = function["function_id"]
        function_task_ids = split_ids(function["task_ids"])
        if not function_task_ids:
            raise AssertionError(f"{function_id} has no task_ids")
        missing_tasks = sorted(task_id for task_id in function_task_ids if task_id not in tasks)
        if missing_tasks:
            raise AssertionError(f"{function_id} references missing tasks: {missing_tasks}")
        function_acceptance_ids = split_ids(function["acceptance_ids"])
        if not function_acceptance_ids:
            raise AssertionError(f"{function_id} has no acceptance_ids")
        missing_acceptance = sorted(
            acceptance_id
            for acceptance_id in function_acceptance_ids
            if acceptance_id not in acceptance
        )
        if missing_acceptance:
            raise AssertionError(
                f"{function_id} references missing acceptance IDs: {missing_acceptance}"
            )

        trace_candidates = []
        for trace in traces_by_function.get(function_id, []):
            trace_task_ids = split_ids(trace["task_ids"])
            trace_acceptance_id = trace["acceptance_id"]
            has_valid_task = any(task_id in tasks for task_id in trace_task_ids)
            has_valid_acceptance = trace_acceptance_id in acceptance
            has_test_path = bool(trace["test_type"].strip()) and bool(
                trace["evidence_path"].strip()
            )
            if has_valid_task and has_valid_acceptance and has_test_path:
                trace_candidates.append(trace)
        if not trace_candidates:
            raise AssertionError(
                f"{function_id} lacks a task + acceptance + test evidence traceability row"
            )

    if checked_functions == 0:
        raise AssertionError("no P0 functions were checked")
    return {"p0_functions_checked": checked_functions, "traceability_rows": len(traces)}


def validate_release_preflight() -> dict[str, Any]:
    missing = sorted(path for path in REQUIRED_RELEASE_FILES if not (ROOT / path).is_file())
    if missing:
        raise AssertionError(f"missing release preflight files: {missing}")
    checksum_text = read_text(ROOT / "CHECKSUMS.sha256")
    missing_checksum_entries = sorted(
        path
        for path in REQUIRED_RELEASE_FILES - {"CHECKSUMS.sha256"}
        if f"  {path}" not in checksum_text
    )
    if missing_checksum_entries:
        raise AssertionError(
            f"CHECKSUMS.sha256 missing release entries: {missing_checksum_entries}"
        )
    return {"release_files": sorted(REQUIRED_RELEASE_FILES)}


def main() -> int:
    result = {
        "valid": True,
        "acceptance_ids": ["A182", "A183", "A200"],
        "packaged_workflow": validate_packaged_workflow(),
        "root_workflow": validate_root_workflow_if_present(),
        "makefile": validate_makefile_target(),
        "traceability": validate_p0_traceability(),
        "release_preflight": validate_release_preflight(),
    }
    print("Governance consistency validation: PASS")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, csv.Error, yaml.YAMLError) as exc:
        print(f"Governance consistency validation: FAIL - {exc}")
        raise SystemExit(1) from None
