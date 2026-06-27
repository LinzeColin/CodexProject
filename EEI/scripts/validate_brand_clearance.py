#!/usr/bin/env python3
"""Generate and validate the A210 brand clearance preflight contract."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised on minimal operator hosts
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = Path("config/brand_policy.yaml")
CONFLICT_PATH = Path("data/brand_name_conflict_register.csv")
OUTPUT_PATH = Path("artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json")
INTAKE_TEMPLATE_PATH = Path("artifacts/tests/a210/t1309_brand_clearance_intake_template.json")

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
INTAKE_SCHEMA_VERSION = "eei-a210-brand-clearance-intake-v1"
REQUIRED_TRADEMARK_JURISDICTIONS = {"CN", "US", "EU", "UK", "AU"}
REQUIRED_SURFACES = {
    "company_name",
    "domain",
    "social_handle",
    "app_store",
    "github",
    "npm",
    "pypi",
}
SIGNED_CLEARANCE_STATUSES = {"CLEARED", "RISK_WAIVER_ACCEPTED"}
SIGNED_BUNDLE_ALLOWED_REPO_PREFIXES = (
    "artifacts/operator_inputs/",
    "operator_inputs/",
    "work/operator_inputs/",
)
SIGNED_BUNDLE_DISALLOWED_REPO_PREFIXES = (
    "artifacts/tests/",
    "data/",
    "tests/",
    "docs/",
    "config/",
    "brand/",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_brand_policy_fallback(text: str) -> dict[str, Any]:
    """Parse the small checked-in brand policy when PyYAML is unavailable."""
    payload: dict[str, Any] = {}
    current_key: str | None = None
    nested_key: str | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0:
            nested_key = None
            if line.endswith(":"):
                current_key = line[:-1]
                payload[current_key] = []
                continue
            key, separator, value = line.partition(":")
            require(bool(separator), f"unsupported brand policy line: {raw_line}")
            current_key = key
            payload[key] = value.strip()
        elif indent == 2 and line.startswith("- "):
            require(current_key is not None, f"orphan list item: {raw_line}")
            require(isinstance(payload.get(current_key), list), f"{current_key} must be a list")
            payload[current_key].append(line[2:].strip())
        elif indent == 2:
            require(current_key is not None, f"orphan nested key: {raw_line}")
            if not isinstance(payload.get(current_key), dict):
                payload[current_key] = {}
            key, separator, value = line.partition(":")
            require(bool(separator), f"unsupported nested brand policy line: {raw_line}")
            nested_key = key
            payload[current_key][key] = [] if not value.strip() else value.strip()
        elif indent == 4 and line.startswith("- "):
            require(
                current_key is not None and nested_key is not None,
                f"orphan nested list item: {raw_line}",
            )
            section = payload[current_key]
            require(isinstance(section, dict), f"{current_key} must be a mapping")
            values = section.get(nested_key)
            require(isinstance(values, list), f"{current_key}.{nested_key} must be a list")
            values.append(line[2:].strip())
        else:
            raise AssertionError(f"unsupported brand policy YAML structure: {raw_line}")
    return payload


def read_policy() -> dict[str, Any]:
    text = (ROOT / POLICY_PATH).read_text(encoding="utf-8")
    payload = yaml.safe_load(text) if yaml else parse_brand_policy_fallback(text)
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


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    require(isinstance(value, str) and value.strip(), f"missing required text: {key}")
    return str(value).strip()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def signed_bundle_source_boundary(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    root = ROOT.resolve()
    try:
        repo_relative = resolved.relative_to(root).as_posix()
    except ValueError:
        return {
            "path": resolved.as_posix(),
            "source_kind": "external_operator_file",
            "repository_relative": None,
            "closure_allowed": True,
            "reason": "signed A210 bundle is outside the repository fixture/template tree",
        }
    if resolved == (ROOT / INTAKE_TEMPLATE_PATH).resolve():
        return {
            "path": repo_relative,
            "source_kind": "repository_template",
            "repository_relative": repo_relative,
            "closure_allowed": False,
            "reason": "default A210 intake template is not signed brand clearance evidence",
        }
    if repo_relative.startswith(SIGNED_BUNDLE_ALLOWED_REPO_PREFIXES):
        return {
            "path": repo_relative,
            "source_kind": "repository_operator_input",
            "repository_relative": repo_relative,
            "closure_allowed": True,
            "reason": "signed A210 bundle is under an approved operator input directory",
        }
    if repo_relative.startswith(SIGNED_BUNDLE_DISALLOWED_REPO_PREFIXES):
        return {
            "path": repo_relative,
            "source_kind": "repository_fixture_or_source",
            "repository_relative": repo_relative,
            "closure_allowed": False,
            "reason": "repository fixtures, templates, configs, docs and data cannot close A210",
        }
    return {
        "path": repo_relative,
        "source_kind": "repository_unapproved_path",
        "repository_relative": repo_relative,
        "closure_allowed": False,
        "reason": (
            "signed A210 bundle must be outside the repository or under "
            "artifacts/operator_inputs"
        ),
    }


def validate_signed_bundle_source_path(path: Path) -> dict[str, Any]:
    boundary = signed_bundle_source_boundary(path)
    if boundary["closure_allowed"] is not True:
        raise AssertionError(
            "A210 signed brand-clearance bundle must be operator-supplied, not "
            f"{boundary['source_kind']}: {boundary['path']}"
        )
    return boundary


def template_trademark_entry(jurisdiction: str) -> dict[str, Any]:
    return {
        "jurisdiction": jurisdiction,
        "registry_or_search_system": "",
        "search_query": EXPECTED_SYSTEM["en_name"],
        "searched_at": "",
        "result_summary": "",
        "blocking_conflicts_found": None,
        "evidence_uri": "",
        "reviewer": "",
        "signature": "",
    }


def template_surface_entry(surface: str) -> dict[str, Any]:
    return {
        "surface": surface,
        "search_query": EXPECTED_SYSTEM["en_name"],
        "searched_at": "",
        "result_summary": "",
        "blocking_conflicts_found": None,
        "evidence_uri": "",
        "reviewer": "",
        "signature": "",
    }


def build_intake_template() -> dict[str, Any]:
    return {
        "schema_version": INTAKE_SCHEMA_VERSION,
        "artifact_id": "t1309-a210-brand-clearance-intake-template",
        "generated_at": utc_now(),
        "system_name": "EEI",
        "system": EXPECTED_SYSTEM,
        "task_id": "T1309",
        "acceptance_ids": ["A210"],
        "bundle_status": "TEMPLATE_ONLY",
        "release_gate_closure_allowed": False,
        "public_brand_launch_allowed": False,
        "template_counts_as_clearance": False,
        "decision_scope": {
            "public_domain_registration": False,
            "app_store_publication": False,
            "public_saas_launch": False,
            "trademark_filing": False,
            "paid_public_marketing_campaign": False,
        },
        "trademark_knockout_reviews": [
            template_trademark_entry(jurisdiction)
            for jurisdiction in sorted(REQUIRED_TRADEMARK_JURISDICTIONS)
        ],
        "market_surface_searches": [
            template_surface_entry(surface) for surface in sorted(REQUIRED_SURFACES)
        ],
        "phonetic_semantic_review": {
            "chinese_reviewer": "",
            "english_reviewer": "",
            "reviewed_at": "",
            "decision": "PENDING_REVIEW",
            "evidence_uri": "",
            "signature": "",
        },
        "legal_or_owner_decision": {
            "decision": "PENDING_REVIEW",
            "scope": "",
            "opinion_or_waiver_ref": "",
            "signed_by": "",
            "signed_role": "",
            "signed_at": "",
            "signature": "",
        },
        "attestation": {
            "signed_by": "",
            "signed_at": "",
            "signature": "",
        },
        "validation_policy": {
            "template_only_counts_as_clearance": False,
            "signed_bundle_required_for_a210_closure": True,
            "signed_bundle_source_must_be_operator_supplied": True,
            "repository_fixtures_and_templates_count_as_clearance": False,
            "signed_bundle_must_cover_all_required_jurisdictions": True,
            "signed_bundle_must_cover_all_required_market_surfaces": True,
            "signed_bundle_with_blocking_conflicts_must_fail": True,
            "signed_bundle_counts_as_release_ready": False,
        },
        "non_claims": [
            "This template is not a legal opinion.",
            "This template is not trademark clearance.",
            "This template is not market clearance.",
            "This template does not permit public launch or paid marketing.",
            "This template does not change the product name from EEI.",
        ],
    }


def validate_intake_common(payload: dict[str, Any]) -> None:
    require(
        payload.get("schema_version") == INTAKE_SCHEMA_VERSION,
        f"schema_version must be {INTAKE_SCHEMA_VERSION}",
    )
    require(payload.get("system_name") == "EEI", "system_name must be EEI")
    require(payload.get("system") == EXPECTED_SYSTEM, "system identity mismatch")
    require(payload.get("task_id") == "T1309", "task_id must be T1309")
    require(payload.get("acceptance_ids") == ["A210"], "acceptance_ids must be ['A210']")
    decision_scope = payload.get("decision_scope")
    require(isinstance(decision_scope, dict), "decision_scope must be present")
    for key in (
        "public_domain_registration",
        "app_store_publication",
        "public_saas_launch",
        "trademark_filing",
        "paid_public_marketing_campaign",
    ):
        require(decision_scope.get(key) is False, f"decision_scope.{key} must be false")

    trademark_reviews = payload.get("trademark_knockout_reviews")
    require(
        isinstance(trademark_reviews, list) and trademark_reviews,
        "trademark_knockout_reviews must be non-empty",
    )
    jurisdictions = {
        str(entry.get("jurisdiction"))
        for entry in trademark_reviews
        if isinstance(entry, dict)
    }
    require(
        REQUIRED_TRADEMARK_JURISDICTIONS.issubset(jurisdictions),
        "trademark reviews must cover CN/US/EU/UK/AU",
    )
    market_searches = payload.get("market_surface_searches")
    require(
        isinstance(market_searches, list) and market_searches,
        "market_surface_searches must be non-empty",
    )
    surfaces = {
        str(entry.get("surface"))
        for entry in market_searches
        if isinstance(entry, dict)
    }
    require(REQUIRED_SURFACES.issubset(surfaces), "market searches miss required surfaces")
    for section in ("phonetic_semantic_review", "legal_or_owner_decision", "attestation"):
        require(isinstance(payload.get(section), dict), f"{section} must be present")


def validate_intake_template(payload: dict[str, Any]) -> None:
    validate_intake_common(payload)
    require(payload.get("bundle_status") == "TEMPLATE_ONLY", "template status mismatch")
    require(
        payload.get("release_gate_closure_allowed") is False,
        "template must not close release gate",
    )
    require(
        payload.get("public_brand_launch_allowed") is False,
        "template must not allow public launch",
    )
    require(
        payload.get("template_counts_as_clearance") is False,
        "template must not count as clearance",
    )
    for entry in payload["trademark_knockout_reviews"]:
        require(entry.get("blocking_conflicts_found") is None, "template conflict flag unset")
        for key in ("registry_or_search_system", "searched_at", "result_summary", "evidence_uri"):
            require(entry.get(key) == "", f"template trademark {key} must be blank")
    for entry in payload["market_surface_searches"]:
        require(entry.get("blocking_conflicts_found") is None, "template conflict flag unset")
        for key in ("searched_at", "result_summary", "evidence_uri"):
            require(entry.get(key) == "", f"template surface {key} must be blank")
    require(
        payload["phonetic_semantic_review"].get("decision") == "PENDING_REVIEW",
        "template phonetic decision must be pending",
    )
    require(
        payload["legal_or_owner_decision"].get("decision") == "PENDING_REVIEW",
        "template legal decision must be pending",
    )


def validate_signed_intake_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    validate_intake_common(payload)
    require(
        payload.get("bundle_status") == "SIGNED_BRAND_CLEARANCE_BUNDLE",
        "signed bundle_status must be SIGNED_BRAND_CLEARANCE_BUNDLE",
    )
    require(
        payload.get("release_gate_closure_allowed") is True,
        "signed bundle must explicitly allow A210 closure",
    )
    require(
        payload.get("public_brand_launch_allowed") is True,
        "signed bundle must explicitly allow public brand launch",
    )
    for entry in payload["trademark_knockout_reviews"]:
        for key in (
            "jurisdiction",
            "registry_or_search_system",
            "search_query",
            "searched_at",
            "result_summary",
            "evidence_uri",
            "reviewer",
            "signature",
        ):
            require_text(entry, key)
        require(
            entry.get("blocking_conflicts_found") is False,
            f"{entry.get('jurisdiction')} trademark review has blocking conflict",
        )
    for entry in payload["market_surface_searches"]:
        for key in (
            "surface",
            "search_query",
            "searched_at",
            "result_summary",
            "evidence_uri",
            "reviewer",
            "signature",
        ):
            require_text(entry, key)
        require(
            entry.get("blocking_conflicts_found") is False,
            f"{entry.get('surface')} market search has blocking conflict",
        )
    phonetic = payload["phonetic_semantic_review"]
    for key in (
        "chinese_reviewer",
        "english_reviewer",
        "reviewed_at",
        "decision",
        "evidence_uri",
        "signature",
    ):
        require_text(phonetic, key)
    require(
        phonetic["decision"] in SIGNED_CLEARANCE_STATUSES,
        "phonetic_semantic_review decision must be cleared or risk-waived",
    )
    legal = payload["legal_or_owner_decision"]
    for key in (
        "decision",
        "scope",
        "opinion_or_waiver_ref",
        "signed_by",
        "signed_role",
        "signed_at",
        "signature",
    ):
        require_text(legal, key)
    require(
        legal["decision"] in SIGNED_CLEARANCE_STATUSES,
        "legal_or_owner_decision must be cleared or risk-waived",
    )
    for key in ("signed_by", "signed_at", "signature"):
        require_text(payload["attestation"], key)
    return {
        "trademark_jurisdictions": sorted(REQUIRED_TRADEMARK_JURISDICTIONS),
        "market_surfaces": sorted(REQUIRED_SURFACES),
        "legal_or_owner_decision": legal["decision"],
        "phonetic_semantic_decision": phonetic["decision"],
    }


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
            "brand_clearance_intake_template": str(INTAKE_TEMPLATE_PATH),
        },
        "signed_bundle_source_boundary_policy": {
            "signed_bundle_source_must_be_operator_supplied": True,
            "repository_fixtures_and_templates_count_as_clearance": False,
            "allowed_repository_prefixes": list(SIGNED_BUNDLE_ALLOWED_REPO_PREFIXES),
            "disallowed_repository_prefixes": list(SIGNED_BUNDLE_DISALLOWED_REPO_PREFIXES),
            "default_template_source_kind": "repository_template",
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
    source_boundary_policy = payload.get("signed_bundle_source_boundary_policy") or {}
    require(
        source_boundary_policy.get("signed_bundle_source_must_be_operator_supplied") is True,
        "signed bundle must be operator supplied",
    )
    require(
        source_boundary_policy.get("repository_fixtures_and_templates_count_as_clearance")
        is False,
        "repository fixtures/templates must not count as clearance",
    )
    require(
        tuple(source_boundary_policy.get("allowed_repository_prefixes") or ())
        == SIGNED_BUNDLE_ALLOWED_REPO_PREFIXES,
        "allowed signed-bundle prefixes drift",
    )
    require(
        tuple(source_boundary_policy.get("disallowed_repository_prefixes") or ())
        == SIGNED_BUNDLE_DISALLOWED_REPO_PREFIXES,
        "disallowed signed-bundle prefixes drift",
    )
    if (ROOT / INTAKE_TEMPLATE_PATH).is_file():
        validate_intake_template(json.loads((ROOT / INTAKE_TEMPLATE_PATH).read_text()))


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


def generate_template() -> None:
    payload = build_intake_template()
    target = ROOT / INTAKE_TEMPLATE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validate_intake_template(payload)
    print(
        json.dumps(
            {
                "generated": True,
                "artifact": str(INTAKE_TEMPLATE_PATH),
                "status": payload["bundle_status"],
                "release_gate_closure_allowed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def validate_template() -> None:
    payload = json.loads((ROOT / INTAKE_TEMPLATE_PATH).read_text(encoding="utf-8"))
    validate_intake_template(payload)
    print(
        json.dumps(
            {
                "valid": True,
                "artifact": str(INTAKE_TEMPLATE_PATH),
                "status": payload["bundle_status"],
                "release_gate_closure_allowed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def validate_signed_bundle(path: Path) -> None:
    source_boundary = validate_signed_bundle_source_path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = validate_signed_intake_bundle(payload)
    print(
        json.dumps(
            {
                "valid": True,
                "bundle": display_path(path),
                "a210_clearance_complete": True,
                "release_ready": False,
                "signed_bundle_source_boundary": source_boundary,
                "remaining_external_gates": [
                    "A202_source_license_owner_legal_release",
                    "A026_A027_production_gold_labels",
                    "A209_24h_operator_soak",
                    "release_manager_activation",
                ],
                **summary,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "generate",
            "validate",
            "generate-template",
            "validate-template",
            "validate-signed",
        ],
    )
    parser.add_argument("--bundle", type=Path, default=ROOT / INTAKE_TEMPLATE_PATH)
    args = parser.parse_args()
    try:
        if args.command == "generate":
            generate()
        elif args.command == "validate":
            validate()
        elif args.command == "generate-template":
            generate_template()
        elif args.command == "validate-template":
            validate_template()
        else:
            validate_signed_bundle(args.bundle)
    except (AssertionError, json.JSONDecodeError, KeyError) as exc:
        print(f"Brand clearance validation: FAIL - {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
