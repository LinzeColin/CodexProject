#!/usr/bin/env python3
"""Validate public-safe owner decision templates for KMFA S05-P2.

Templates are not owner decisions. They define how an owner or authorized
delegate can create a future decision record without committing raw business
values or jumping to Q4/Q5.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES_DIR = (
    ROOT
    / "stage_artifacts"
    / "S05_P2_a0_golden_fixture"
    / "machine"
    / "owner_decision_templates"
)

EXPECTED_TEMPLATE_RECORD_TYPE = "s05_p2_excel_owner_resolution_decision_template"
ACTIVE_DECISION_RECORD_TYPE = "s05_p2_excel_owner_resolution_decision"
EXPECTED_SCHEMA_VERSION = "kmfa.s05_p2_excel_owner_resolution_decision_template.v1"
EXPECTED_PROJECT_ID = "KMFA"
EXPECTED_STAGE_ID = "S05"
EXPECTED_PHASE_ID = "S05-P2"
EXPECTED_GATE = "KMFA-S05-P2-EXCEL-RESOLUTION-GATE"
EXPECTED_CANDIDATE_ID = "A0-CAND-70023EFC7305"
EXPECTED_FILE_ID = "A0-FILE-BAE6D90834C5"
EXPECTED_DECISIONS = {
    "provide_private_field_mapping",
    "downgrade_to_cross_source_support",
    "keep_pending",
}
EXPECTED_FIELDS = {
    "contract_amount",
    "total_expense",
    "gross_profit",
    "gross_margin",
    "cost_category",
}
FALSE_REQUIRED_FLAGS = {
    "business_plaintext_committed",
    "raw_source_committed",
    "private_csv_committed",
    "q4_confirmation_claimed",
    "q5_baseline_claimed",
    "source_layer_write_allowed",
}
FORBIDDEN_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path} must contain a JSON object")
    return payload


def walk_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                fail(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, f"{path}[{index}]")


def require_equal(template: dict[str, Any], key: str, expected: Any, path: Path) -> None:
    if template.get(key) != expected:
        fail(f"{path.name}.{key} mismatch")


def require_false(template: dict[str, Any], key: str, path: Path) -> None:
    if template.get(key) is not False:
        fail(f"{path.name}.{key} must be false")


def require_non_empty_list(template: dict[str, Any], key: str, path: Path) -> None:
    value = template.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        fail(f"{path.name}.{key} must be a non-empty string list")


def validate_template(path: Path) -> dict[str, Any]:
    template = read_json(path)
    walk_forbidden_keys(template)
    if template.get("record_type") == ACTIVE_DECISION_RECORD_TYPE:
        fail("templates must not use active decision record_type")
    require_equal(template, "record_type", EXPECTED_TEMPLATE_RECORD_TYPE, path)
    require_equal(template, "schema_version", EXPECTED_SCHEMA_VERSION, path)
    require_equal(template, "project_id", EXPECTED_PROJECT_ID, path)
    require_equal(template, "stage_id", EXPECTED_STAGE_ID, path)
    require_equal(template, "phase_id", EXPECTED_PHASE_ID, path)
    require_equal(template, "current_gate", EXPECTED_GATE, path)
    require_equal(template, "candidate_id", EXPECTED_CANDIDATE_ID, path)
    require_equal(template, "file_id", EXPECTED_FILE_ID, path)
    require_equal(template, "not_decision_record", True, path)
    require_equal(template, "output_record_type_after_activation", ACTIVE_DECISION_RECORD_TYPE, path)

    decision_code = template.get("decision_code")
    if decision_code not in EXPECTED_DECISIONS:
        fail(f"{path.name}.decision_code is not allowed")
    if set(template.get("field_keys") or []) != EXPECTED_FIELDS:
        fail(f"{path.name}.field_keys must match pending Excel fields")

    for key in FALSE_REQUIRED_FLAGS:
        require_false(template, key, path)
    require_non_empty_list(template, "activation_requires", path)
    require_non_empty_list(template, "required_fill_fields", path)
    if "remove_template_marker" not in template["activation_requires"]:
        fail(f"{path.name}.activation_requires must include remove_template_marker")

    if decision_code == "provide_private_field_mapping":
        if set(template.get("required_private_hash_ref_fields") or []) != EXPECTED_FIELDS:
            fail(f"{path.name}.required_private_hash_ref_fields must include every pending field")
        if set(template.get("required_source_anchor_ref_fields") or []) != EXPECTED_FIELDS:
            fail(f"{path.name}.required_source_anchor_ref_fields must include every pending field")
    elif decision_code in {"downgrade_to_cross_source_support", "keep_pending"}:
        if template.get("private_hash_refs_allowed") is not False:
            fail(f"{path.name}.private_hash_refs_allowed must be false")
    return template


def validate_templates(templates_dir: Path) -> list[dict[str, Any]]:
    try:
        paths = sorted(templates_dir.glob("*.json"))
    except FileNotFoundError:
        fail(f"missing templates dir: {templates_dir}")
    if not paths:
        fail(f"no templates found in {templates_dir}")
    templates = [validate_template(path) for path in paths]
    decision_codes = {template["decision_code"] for template in templates}
    if decision_codes != EXPECTED_DECISIONS:
        fail("template decision set must exactly match owner decision packet")
    if len(templates) != len(EXPECTED_DECISIONS):
        fail("template count must match allowed decision count")
    return templates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S05-P2 owner decision templates.")
    parser.add_argument("--templates-dir", type=Path, default=DEFAULT_TEMPLATES_DIR)
    args = parser.parse_args(argv)

    templates = validate_templates(args.templates_dir)
    print(
        "PASS: KMFA S05-P2 owner decision templates check passed "
        f"(template_count={len(templates)}, "
        "active_decision_records=0)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
