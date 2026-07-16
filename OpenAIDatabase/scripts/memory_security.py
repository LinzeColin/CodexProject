#!/usr/bin/env python3
"""Fail-closed prompt-injection, credential and workflow security gates."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from privacy_guard import credential_exclusion_hits


DEFAULT_POLICY = Path("config/memory-security-policy.json")
DEFAULT_FIXTURE = Path("tests/fixtures/memory_security/adversarial_cases.json")
TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z0-9][A-Za-z0-9._~+/=-]{23,127})(?![A-Za-z0-9])")
HEX_RE = re.compile(r"(?:sha256:)?[a-fA-F0-9]{32,128}\Z")
UUID_RE = re.compile(
    r"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[1-5][a-fA-F0-9]{3}-[89abAB][a-fA-F0-9]{3}-[a-fA-F0-9]{12}\Z"
)
INVISIBLE_OR_BIDI = frozenset(
    chr(code)
    for code in (
        0x200B,
        0x200C,
        0x200D,
        0x200E,
        0x200F,
        0x202A,
        0x202B,
        0x202C,
        0x202D,
        0x202E,
        0x2060,
        0x2061,
        0x2062,
        0x2063,
        0x2064,
        0x2066,
        0x2067,
        0x2068,
        0x2069,
        0xFEFF,
    )
)


class MemorySecurityError(ValueError):
    """A stable, payload-free security rejection."""


def load_json_strict(path: Path) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise MemorySecurityError("security_json_duplicate_key")
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except MemorySecurityError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MemorySecurityError("security_json_invalid") from exc


def resolve_repository_file(root: Path, relative: str) -> Path:
    candidate = (root.resolve() / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise MemorySecurityError("security_path_outside_root") from exc
    if not candidate.is_file() or candidate.is_symlink():
        raise MemorySecurityError("security_file_missing_or_symlink")
    return candidate


def validate_policy(policy: dict[str, Any]) -> None:
    expected = {
        "schema_version": "openai_database.memory_security.v1",
        "project_id": "OpenAIDatabase",
        "task_id": "TSK.OpenAIDatabase.PAM1.0012",
        "acceptance_id": "ACC.OpenAIDatabase.PAM1.0012",
        "instruction_trust": "none",
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            raise MemorySecurityError(f"security_policy_invalid_{key}")
    boundaries = policy.get("trust_boundaries")
    if boundaries != {
        "raw_evidence": "data_only",
        "pull_request_title": "data_only",
        "pull_request_body": "data_only",
        "external_document": "data_only",
    }:
        raise MemorySecurityError("security_policy_invalid_trust_boundaries")
    injection = policy.get("prompt_injection")
    if not isinstance(injection, dict) or injection.get("normalization") != "NFKC":
        raise MemorySecurityError("security_policy_invalid_prompt_injection")
    patterns = injection.get("patterns")
    if injection.get("block_on_hit") is not True or not isinstance(patterns, list) or not patterns:
        raise MemorySecurityError("security_policy_invalid_prompt_patterns")
    try:
        for pattern in patterns:
            re.compile(str(pattern), re.IGNORECASE)
    except re.error as exc:
        raise MemorySecurityError("security_policy_invalid_prompt_regex") from exc
    scan = policy.get("credential_scan")
    entropy = scan.get("entropy_scan") if isinstance(scan, dict) else None
    if not isinstance(entropy, dict) or scan.get("pattern_scan") is not True:
        raise MemorySecurityError("security_policy_invalid_credential_scan")
    if scan.get("block_on_hit") is not True or scan.get("suspected_value_echo_allowed") is not False:
        raise MemorySecurityError("security_policy_invalid_credential_decision")
    if scan.get("required_block_rate") != 1.0 or scan.get("maximum_echo_count") != 0:
        raise MemorySecurityError("security_policy_invalid_credential_gates")
    if entropy != {
        "enabled": True,
        "min_length": 24,
        "max_length": 128,
        "min_character_classes": 3,
        "min_shannon_bits_per_character": 4.0,
    }:
        raise MemorySecurityError("security_policy_invalid_entropy_contract")
    supply = policy.get("supply_chain")
    if not isinstance(supply, dict) or not supply.get("required_zero_metrics"):
        raise MemorySecurityError("security_policy_invalid_supply_chain")
    incident = policy.get("incident_response")
    if not isinstance(incident, dict) or incident.get("on_real_credential") != "STOP":
        raise MemorySecurityError("security_policy_invalid_incident_response")
    if incident.get("first_actions") != ["revoke", "rotate"]:
        raise MemorySecurityError("security_policy_invalid_incident_order")
    if incident.get("automatic_history_rewrite") is not False:
        raise MemorySecurityError("security_policy_history_rewrite_not_closed")


def load_policy(database_dir: Path, path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    target = path if path.is_absolute() else database_dir / path
    value = load_json_strict(target)
    if not isinstance(value, dict):
        raise MemorySecurityError("security_policy_not_object")
    validate_policy(value)
    return value


def shannon_bits_per_character(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def character_class_count(value: str) -> int:
    return sum(
        (
            any(character.islower() for character in value),
            any(character.isupper() for character in value),
            any(character.isdigit() for character in value),
            any(not character.isalnum() for character in value),
        )
    )


def entropy_credential_count(text: str, policy: dict[str, Any]) -> int:
    entropy = policy["credential_scan"]["entropy_scan"]
    count = 0
    for match in TOKEN_RE.finditer(text):
        candidate = match.group(1)
        if HEX_RE.fullmatch(candidate) or UUID_RE.fullmatch(candidate):
            continue
        if not int(entropy["min_length"]) <= len(candidate) <= int(entropy["max_length"]):
            continue
        if character_class_count(candidate) < int(entropy["min_character_classes"]):
            continue
        if shannon_bits_per_character(candidate) < float(entropy["min_shannon_bits_per_character"]):
            continue
        count += 1
    return count


def scan_untrusted_text(text: str, boundary: str, policy: dict[str, Any]) -> dict[str, Any]:
    if boundary not in policy["trust_boundaries"]:
        raise MemorySecurityError("security_boundary_unknown")
    if not isinstance(text, str):
        raise MemorySecurityError("security_text_not_string")
    reason_codes: list[str] = []
    if "\x00" in text:
        reason_codes.append("unsafe_control")
    if any(character in INVISIBLE_OR_BIDI for character in text):
        reason_codes.append("unsafe_unicode")
    normalized = unicodedata.normalize("NFKC", text)
    injection_count = sum(
        1
        for pattern in policy["prompt_injection"]["patterns"]
        if re.search(str(pattern), normalized, flags=re.IGNORECASE)
    )
    if injection_count:
        reason_codes.append("prompt_injection")
    pattern_hits = credential_exclusion_hits(text)
    entropy_count = entropy_credential_count(text, policy)
    credential_count = len(pattern_hits) + entropy_count
    if credential_count:
        reason_codes.append("credential")
    categories = sorted({str(hit["category"]) for hit in pattern_hits})
    if entropy_count:
        categories.append("high_entropy_token")
    return {
        "status": "BLOCK" if reason_codes else "PASS",
        "boundary": boundary,
        "instruction_obedience_count": 0,
        "prompt_injection_count": injection_count,
        "credential_count": credential_count,
        "credential_categories": categories,
        "suspected_value_echo_count": 0,
        "reason_codes": sorted(set(reason_codes)),
    }


def assert_untrusted_text_safe(text: str, boundary: str, policy: dict[str, Any]) -> None:
    result = scan_untrusted_text(text, boundary, policy)
    if result["status"] != "PASS":
        raise MemorySecurityError("untrusted_text_blocked:" + ",".join(result["reason_codes"]))


def fixture_payload(case: dict[str, Any]) -> str:
    if isinstance(case.get("payload"), str):
        return str(case["payload"])
    parts = case.get("payload_parts")
    if isinstance(parts, list) and parts and all(isinstance(part, str) for part in parts):
        return "".join(parts)
    raise MemorySecurityError("security_fixture_payload_invalid")


def evaluate_fixture(database_dir: Path, fixture_path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    fixture = load_json_strict(fixture_path)
    if not isinstance(fixture, dict) or fixture.get("schema_version") != "openai_database.memory_security_cases.v1":
        raise MemorySecurityError("security_fixture_invalid")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        raise MemorySecurityError("security_fixture_cases_missing")
    failures: list[str] = []
    instruction_cases = 0
    credential_cases = 0
    blocked_credentials = 0
    echo_count = 0
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise MemorySecurityError("security_fixture_case_invalid")
        payload = fixture_payload(case)
        result = scan_untrusted_text(payload, str(case.get("boundary") or ""), policy)
        if result["status"] != case.get("expected_status"):
            failures.append(str(case["id"]))
        kind = case.get("kind")
        instruction_cases += int(kind == "prompt_injection")
        credential_cases += int(kind == "credential")
        blocked_credentials += int(kind == "credential" and result["status"] == "BLOCK")
        serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)
        echo_count += int(bool(payload) and payload in serialized)
    block_rate = blocked_credentials / credential_cases if credential_cases else 0.0
    status = "PASS"
    if failures or block_rate != policy["credential_scan"]["required_block_rate"] or echo_count:
        status = "FAIL"
    return {
        "status": status,
        "case_count": len(cases),
        "prompt_injection_case_count": instruction_cases,
        "credential_case_count": credential_cases,
        "instruction_obedience_count": 0,
        "credential_block_rate": block_rate,
        "suspected_value_echo_count": echo_count,
        "failed_case_ids": failures,
    }


def audit_supply_chain(repo_root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    supply = policy["supply_chain"]
    audit_script = resolve_repository_file(repo_root, str(supply["workflow_audit"]))
    workflow_policy_path = resolve_repository_file(repo_root, str(supply["workflow_policy"]))
    completed = subprocess.run(
        [sys.executable, "-B", str(audit_script), "audit", "--json"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        canonical = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MemorySecurityError("workflow_audit_output_invalid") from exc
    workflow_policy = load_json_strict(workflow_policy_path)
    if not isinstance(workflow_policy, dict):
        raise MemorySecurityError("workflow_policy_not_object")
    failures: list[str] = []
    if completed.returncode != 0 or canonical.get("status") != "PASS":
        failures.append("canonical_workflow_audit")
    for metric in supply["required_zero_metrics"]:
        if canonical.get(metric) != 0:
            failures.append(str(metric))
    pin_policy = supply["action_pin"]
    pins = workflow_policy.get("action_pins")
    pins = pins if isinstance(pins, list) else []
    untraceable_pins = 0
    for pin in pins:
        if not isinstance(pin, dict):
            untraceable_pins += 1
            continue
        sha = str(pin.get("commit_sha") or "")
        source = str(pin.get("source") or "")
        if not re.fullmatch(rf"[a-f0-9]{{{int(pin_policy['full_sha_length'])}}}", sha):
            untraceable_pins += 1
        if not source.startswith(str(pin_policy["resolution_source_prefix"])):
            untraceable_pins += 1
    settlement_policy = supply["settlement"]
    settlement_path = resolve_repository_file(repo_root, str(settlement_policy["path"]))
    settlement_text = settlement_path.read_text(encoding="utf-8")
    settlement_forbidden_count = sum(
        settlement_text.count(str(fragment)) for fragment in settlement_policy["forbidden_fragments"]
    )
    matching_roles = [
        row
        for row in workflow_policy.get("workflows") or []
        if isinstance(row, dict) and row.get("role") == settlement_policy["role"]
    ]
    settlement_contract_ok = (
        len(matching_roles) == 1
        and matching_roles[0].get("path") == settlement_policy["path"]
        and matching_roles[0].get("trust_boundary") == settlement_policy["trust_boundary"]
    )
    if untraceable_pins:
        failures.append("action_pin_traceability")
    if settlement_forbidden_count or not settlement_contract_ok:
        failures.append("settlement_untrusted_execution_boundary")
    return {
        "status": "PASS" if not failures else "FAIL",
        "workflow_count": canonical.get("workflow_count", 0),
        "external_action_ref_count": canonical.get("external_action_refs", 0),
        "resolved_action_pin_count": len(pins),
        "untraceable_action_pin_count": untraceable_pins,
        "settlement_role_count": len(matching_roles),
        "settlement_forbidden_fragment_count": settlement_forbidden_count,
        "required_zero_metrics": {metric: canonical.get(metric) for metric in supply["required_zero_metrics"]},
        "failed_gates": sorted(set(failures)),
    }


def audit_repository(repo_root: Path) -> dict[str, Any]:
    database_dir = repo_root / "OpenAIDatabase"
    policy = load_policy(database_dir)
    corpus = evaluate_fixture(database_dir, database_dir / DEFAULT_FIXTURE, policy)
    supply_chain = audit_supply_chain(repo_root, policy)
    return {
        "schema_version": "openai_database.memory_security_audit.v1",
        "task_id": policy["task_id"],
        "acceptance_id": policy["acceptance_id"],
        "status": "PASS" if corpus["status"] == supply_chain["status"] == "PASS" else "FAIL",
        "corpus": corpus,
        "supply_chain": supply_chain,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="Audit bounded untrusted text cases and workflow security.")
    audit.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    audit.add_argument("--json", action="store_true", help="Emit deterministic machine-readable JSON.")
    args = parser.parse_args(argv)
    if args.command == "audit":
        try:
            result = audit_repository(args.repo_root.resolve())
        except MemorySecurityError as exc:
            result = {
                "schema_version": "openai_database.memory_security_audit.v1",
                "status": "FAIL",
                "error_code": str(exc),
            }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if result.get("status") == "PASS" else 1
    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
