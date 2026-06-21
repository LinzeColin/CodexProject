#!/usr/bin/env python3
"""Generate and validate the A210 brand clearance preflight contract."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = Path("config/brand_policy.yaml")
CONFLICT_PATH = Path("data/brand_name_conflict_register.csv")
OUTPUT_PATH = Path("artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json")

EXPECTED_SYSTEM = {
    "zh_name": "商域图谱",
    "en_name": "Enterprise Ecosystem Intelligence",
    "abbreviation": "EEI",
    "subtitle": "企业商业版图与供应链递归探索系统",
}
REQUIRED_RELEASE_GATE_CHECKS = {
    "CN/US/EU/UK/AU trademark knockout",
    "company-name search",
    "domain and social handles",
    "app stores",
    "GitHub/npm/PyPI",
    "phonetic and semantic review in Chinese and English",
    "same-category and adjacent-category competitor review",
    "legal counsel sign-off or explicit risk waiver",
}
REQUIRED_BEFORE = {
    "public domain registration",
    "app store publication",
    "public SaaS launch",
    "trademark filing",
    "paid public marketing campaign",
}
BLOCKING_DECISIONS = {"DISQUALIFIED", "HIGH_RISK_FAMILY", "HISTORICAL_SOURCE_ONLY"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_policy() -> dict[str, Any]:
    payload = yaml.safe_load((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "brand policy must be a mapping")
    return payload


def read_conflicts() -> list[dict[str, str]]:
    with (ROOT / CONFLICT_PATH).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(rows, "brand conflict register must not be empty")
    return rows


def conflict_covers_name(name: str, rows: list[dict[str, str]]) -> bool:
    lowered = name.casefold()
    for row in rows:
        row_name = row["name"].casefold()
        if row_name == lowered:
            return True
        if "*atlas" in row_name and "atlas" in lowered:
            return True
    return False


def validate_policy(policy: dict[str, Any], conflicts: list[dict[str, str]]) -> None:
    require(policy.get("system_name_zh") == EXPECTED_SYSTEM["zh_name"], "Chinese name changed")
    require(policy.get("system_name_en") == EXPECTED_SYSTEM["en_name"], "English name changed")
    require(
        policy.get("system_abbreviation") == EXPECTED_SYSTEM["abbreviation"],
        "EEI abbreviation changed",
    )
    require(policy.get("subtitle_zh") == EXPECTED_SYSTEM["subtitle"], "subtitle changed")
    require(
        policy.get("public_disclosure_status") == "not_cleared_for_public_brand_launch",
        "public disclosure must remain fail-closed until A210 closes",
    )

    release_gate = policy.get("release_gate") or {}
    require(release_gate.get("id") == "BRAND-G1", "brand release gate id must be BRAND-G1")
    require(
        REQUIRED_BEFORE.issubset(set(release_gate.get("required_before") or [])),
        "BRAND-G1 required_before list is incomplete",
    )
    require(
        REQUIRED_RELEASE_GATE_CHECKS.issubset(set(release_gate.get("checks") or [])),
        "BRAND-G1 checks list is incomplete",
    )

    forbidden_names = policy.get("forbidden_active_names") or []
    require(forbidden_names, "forbidden_active_names must not be empty")
    for name in forbidden_names:
        require(
            conflict_covers_name(str(name), conflicts),
            f"forbidden brand name lacks conflict-register coverage: {name}",
        )
    for active_name in [
        policy["system_name_zh"],
        policy["system_name_en"],
        policy["system_abbreviation"],
    ]:
        require(
            active_name not in forbidden_names,
            f"active EEI name is incorrectly listed as forbidden: {active_name}",
        )

    for row in conflicts:
        require(row["decision"] in BLOCKING_DECISIONS, f"unexpected brand decision: {row}")
        require(row["repository_policy"], f"missing repository policy for conflict {row['id']}")


def build_payload() -> dict[str, Any]:
    policy = read_policy()
    conflicts = read_conflicts()
    validate_policy(policy, conflicts)
    gate = policy["release_gate"]
    forbidden_names = [str(name) for name in policy["forbidden_active_names"]]

    return {
        "schema_version": 1,
        "artifact_id": "t1309-brand-clearance-preflight-contract",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "task_id": "T1309",
        "acceptance_ids": ["A210"],
        "system": EXPECTED_SYSTEM,
        "source_files": {
            "brand_policy": str(POLICY_PATH),
            "conflict_register": str(CONFLICT_PATH),
            "competitive_landscape": "data/competitive_product_landscape.csv",
            "research_summary": "brand/BRAND_AND_COMPETITIVE_LANDSCAPE_RESEARCH.md",
        },
        "release_gate": {
            "id": gate["id"],
            "status": "BLOCKING",
            "public_release_allowed": False,
            "public_disclosure_status": policy["public_disclosure_status"],
            "required_before": sorted(gate["required_before"]),
            "checks": sorted(gate["checks"]),
        },
        "conflict_register": {
            "row_count": len(conflicts),
            "blocking_decisions": sorted(BLOCKING_DECISIONS),
            "forbidden_active_names": forbidden_names,
            "covered_forbidden_names": [
                name for name in forbidden_names if conflict_covers_name(name, conflicts)
            ],
        },
        "clearance_requirements": {
            "formal_legal_clearance_required": True,
            "market_clearance_required": True,
            "risk_waiver_allowed": True,
            "legal_counsel_or_owner_signature_required": True,
            "public_launch_must_fail_closed_without_clearance": True,
        },
        "current_clearance_status": {
            "formal_legal_clearance": "NOT_COMPLETE",
            "market_clearance": "NOT_COMPLETE",
            "signed_risk_waiver": "NOT_PROVIDED",
            "owner_signoff": "NOT_PROVIDED",
            "a210_status": "IN_PROGRESS",
        },
        "remaining_blockers": [
            "Attach dated CN/US/EU/UK/AU trademark knockout evidence or explicit risk waiver.",
            "Attach company-name, domain, social handle, app store, "
            "GitHub/npm/PyPI search evidence.",
            "Attach phonetic and semantic Chinese/English review.",
            "Attach legal counsel sign-off or repository-owner risk waiver before public launch.",
        ],
        "non_claims": [
            "This artifact does not certify legal clearance.",
            "This artifact does not permit public brand launch.",
            "This artifact does not change the product name from EEI.",
        ],
    }


def validate_payload(payload: dict[str, Any]) -> None:
    policy = read_policy()
    conflicts = read_conflicts()
    validate_policy(policy, conflicts)
    require(payload.get("schema_version") == 1, "schema_version must be 1")
    require(payload.get("task_id") == "T1309", "artifact must cite T1309")
    require(payload.get("acceptance_ids") == ["A210"], "artifact must cite A210")
    require(payload.get("system") == EXPECTED_SYSTEM, "system identity mismatch")

    release_gate = payload.get("release_gate") or {}
    require(release_gate.get("id") == "BRAND-G1", "artifact release gate mismatch")
    require(release_gate.get("status") == "BLOCKING", "brand gate must remain blocking")
    require(release_gate.get("public_release_allowed") is False, "public release must be false")
    require(
        release_gate.get("public_disclosure_status") == "not_cleared_for_public_brand_launch",
        "public disclosure status must be fail-closed",
    )

    conflict_register = payload.get("conflict_register") or {}
    require(conflict_register.get("row_count") == len(conflicts), "conflict row count drift")
    require(
        sorted(conflict_register.get("forbidden_active_names") or [])
        == sorted(policy["forbidden_active_names"]),
        "forbidden active names drift",
    )
    require(
        sorted(conflict_register.get("covered_forbidden_names") or [])
        == sorted(policy["forbidden_active_names"]),
        "not all forbidden active names are covered",
    )

    clearance = payload.get("clearance_requirements") or {}
    require(clearance.get("formal_legal_clearance_required") is True, "legal clearance required")
    require(clearance.get("market_clearance_required") is True, "market clearance required")
    require(
        clearance.get("public_launch_must_fail_closed_without_clearance") is True,
        "public launch must fail closed",
    )

    current = payload.get("current_clearance_status") or {}
    require(current.get("a210_status") == "IN_PROGRESS", "A210 must remain in progress")
    for key in ["formal_legal_clearance", "market_clearance"]:
        require(current.get(key) == "NOT_COMPLETE", f"{key} must not be complete")
    require(current.get("signed_risk_waiver") == "NOT_PROVIDED", "risk waiver must not be provided")


def generate() -> None:
    payload = build_payload()
    target = ROOT / OUTPUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validate_payload(payload)
    print(
        json.dumps(
            {"generated": True, "artifact": str(OUTPUT_PATH)},
            ensure_ascii=False,
            indent=2,
        )
    )


def validate() -> None:
    payload = json.loads((ROOT / OUTPUT_PATH).read_text(encoding="utf-8"))
    validate_payload(payload)
    print(json.dumps({"valid": True, "artifact": str(OUTPUT_PATH)}, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate", "validate"])
    args = parser.parse_args()
    try:
        if args.command == "generate":
            generate()
        else:
            validate()
    except (AssertionError, json.JSONDecodeError, KeyError) as exc:
        print(f"Brand clearance validation: FAIL - {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
