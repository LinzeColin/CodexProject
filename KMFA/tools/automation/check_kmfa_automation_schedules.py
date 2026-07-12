#!/usr/bin/env python3
"""Fail closed when a KMFA Codex automation schedule drifts from its contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path


DEFAULT_CONTRACT = (
    Path(__file__).resolve().parents[2]
    / "metadata"
    / "automation"
    / "codex_app_schedules.contract.toml"
)


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def load_toml(path: Path) -> dict[str, object]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def rrule_policy_errors(rrule: object) -> list[str]:
    if not isinstance(rrule, str):
        return ["rrule_not_string"]

    errors: list[str] = []
    upper = rrule.upper()
    if not rrule.startswith("RRULE:"):
        errors.append("rrule_missing_prefix")
    if "DTSTART" in upper or "TZID" in upper:
        errors.append("forbidden_dtstart_or_tzid")
    if "\n" in rrule or "\r" in rrule or upper.count("RRULE:") != 1:
        errors.append("forbidden_multiple_or_multiline_rrule")
    return errors


def normalized_prompt_sha256(prompt: object) -> str | None:
    if not isinstance(prompt, str):
        return None
    normalized = prompt.rstrip("\r\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-path", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--automation-root", default=str(Path.home() / ".codex" / "automations"))
    args = parser.parse_args()

    contract_path = Path(args.contract_path).expanduser().resolve()
    automation_root = Path(args.automation_root).expanduser().resolve()
    if not contract_path.exists():
        emit({"status": "CODEX_AUTOMATION_CONTRACT_MISSING", "contract_path": str(contract_path)})
        return 2

    contract = load_toml(contract_path)
    automations = contract.get("automations")
    if not isinstance(automations, list) or not automations:
        emit({"status": "CODEX_AUTOMATION_CONTRACT_INVALID", "errors": ["automations_missing"]})
        return 3

    contract_errors: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for item in automations:
        if not isinstance(item, dict):
            contract_errors.append({"id": None, "errors": ["automation_not_table"]})
            continue
        automation_id = item.get("id")
        errors = rrule_policy_errors(item.get("rrule"))
        expected_prompt_hash = item.get("prompt_sha256")
        if expected_prompt_hash is not None and (
            not isinstance(expected_prompt_hash, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_prompt_hash) is None
        ):
            errors.append("prompt_sha256_invalid")
        expected_project_id = item.get("project_id")
        if expected_project_id is not None and (
            not isinstance(expected_project_id, str) or not expected_project_id
        ):
            errors.append("project_id_invalid")
        if not isinstance(automation_id, str) or not automation_id:
            errors.append("id_missing")
        elif automation_id in seen_ids:
            errors.append("duplicate_id")
        else:
            seen_ids.add(automation_id)
        if errors:
            contract_errors.append({"id": automation_id, "errors": errors})

    if contract_errors:
        emit(
            {
                "status": "CODEX_AUTOMATION_CONTRACT_INVALID",
                "contract_path": str(contract_path),
                "automations": contract_errors,
            }
        )
        return 3

    results: list[dict[str, object]] = []
    missing = False
    mismatch = False
    check_fields = (
        "name",
        "kind",
        "status",
        "execution_environment",
        "cwds",
        "model",
        "reasoning_effort",
    )
    for expected in automations:
        automation_id = str(expected["id"])
        automation_path = automation_root / automation_id / "automation.toml"
        result: dict[str, object] = {
            "id": automation_id,
            "automation_path": str(automation_path),
            "mismatches": [],
        }
        mismatches = result["mismatches"]
        assert isinstance(mismatches, list)
        if not automation_path.exists():
            missing = True
            mismatches.append("automation_missing")
            results.append(result)
            continue

        live = load_toml(automation_path)
        if live.get("rrule") != expected.get("rrule"):
            mismatches.append("rrule")
        for error in rrule_policy_errors(live.get("rrule")):
            if error not in mismatches:
                mismatches.append(error)
        if any(key in live for key in ("timezone", "tzid", "scheduler_timezone")):
            mismatches.append("forbidden_explicit_timezone")
        expected_prompt_hash = expected.get("prompt_sha256")
        if (
            expected_prompt_hash is not None
            and normalized_prompt_sha256(live.get("prompt")) != expected_prompt_hash
        ):
            mismatches.append("prompt")
        expected_project_id = expected.get("project_id")
        if expected_project_id is not None:
            target = live.get("target")
            if (
                not isinstance(target, dict)
                or target.get("type") != "project"
                or target.get("project_id") != expected_project_id
            ):
                mismatches.append("project_id")
        for field in check_fields:
            if field in expected and live.get(field) != expected.get(field):
                mismatches.append(field)
        if mismatches:
            mismatch = True
        results.append(result)

    if missing:
        emit({"status": "CODEX_AUTOMATION_MISSING", "automations": results})
        return 2
    if mismatch:
        emit({"status": "CODEX_AUTOMATION_MISMATCH", "automations": results})
        return 4

    emit(
        {
            "status": "CODEX_AUTOMATIONS_READY",
            "contract_path": str(contract_path),
            "automation_count": len(results),
            "automations": results,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
