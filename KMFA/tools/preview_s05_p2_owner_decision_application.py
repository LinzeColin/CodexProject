#!/usr/bin/env python3
"""Preview public-safe application of a future S05-P2 owner decision.

This tool is intentionally a preview layer. It validates a supplied owner or
authorized decision record and emits the deterministic public-safe application
path without mutating the A0 fixture, promoting Q4/Q5, or recording raw values.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_s05_p2_owner_decision_intake import (
    EXPECTED_CANDIDATE_ID,
    EXPECTED_FIELDS,
    EXPECTED_FILE_ID,
    read_json,
    validate_decision,
)


FIELD_KEYS = ["contract_amount", "total_expense", "gross_profit", "gross_margin", "cost_category"]


def base_preview(decision_code: str, application_status: str) -> dict[str, Any]:
    return {
        "record_type": "s05_p2_owner_decision_application_preview",
        "schema_version": "kmfa.s05_p2_owner_decision_application_preview.v1",
        "project_id": "KMFA",
        "stage_id": "S05",
        "phase_id": "S05-P2",
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "file_id": EXPECTED_FILE_ID,
        "decision_code": decision_code,
        "application_status": application_status,
        "q4_confirmation_claimed": False,
        "q5_baseline_claimed": False,
        "raw_source_committed": False,
        "business_plaintext_committed": False,
        "private_csv_committed": False,
        "public_safety": {
            "raw_or_plaintext_values_included": False,
            "source_layer_write_allowed": False,
            "github_upload_allowed_by_preview": False,
        },
    }


def no_decision_preview() -> dict[str, Any]:
    preview = base_preview("none", "blocked")
    preview.update(
        {
            "blocker": "no_owner_or_authorized_decision_supplied",
            "completion_gate_effect": "does_not_resolve_excel_candidate",
            "candidate_application": {
                "candidate_role": "pending_excel_candidate",
                "pending_field_count": len(FIELD_KEYS),
                "field_actions": FIELD_KEYS,
            },
        }
    )
    return preview


def private_mapping_preview(decision: dict[str, Any]) -> dict[str, Any]:
    preview = base_preview("provide_private_field_mapping", "ready")
    preview.update(
        {
            "completion_gate_effect": "resolves_excel_candidate_without_public_plaintext",
            "candidate_application": {
                "candidate_role": "a0_fixture_with_private_hash_refs",
                "pending_field_count": len(FIELD_KEYS),
                "field_actions": FIELD_KEYS,
                "private_hash_refs": {
                    field_key: decision["private_hash_refs"][field_key] for field_key in FIELD_KEYS
                },
                "source_anchor_refs": {
                    field_key: decision["source_anchor_refs"][field_key] for field_key in FIELD_KEYS
                },
            },
        }
    )
    return preview


def downgrade_preview(decision: dict[str, Any]) -> dict[str, Any]:
    preview = base_preview("downgrade_to_cross_source_support", "ready")
    preview.update(
        {
            "completion_gate_effect": "resolves_excel_candidate_without_q4_q5",
            "candidate_application": {
                "candidate_role": "cross_source_support_only",
                "pending_field_count": len(FIELD_KEYS),
                "field_actions": FIELD_KEYS,
                "cross_source_support_scope": decision["cross_source_support_scope"],
                "q5_exclusion_confirmed": True,
            },
        }
    )
    return preview


def keep_pending_preview(decision: dict[str, Any]) -> dict[str, Any]:
    preview = base_preview("keep_pending", "blocked")
    preview.update(
        {
            "blocker": "owner_decision_keeps_excel_candidate_pending",
            "completion_gate_effect": "does_not_resolve_excel_candidate",
            "candidate_application": {
                "candidate_role": "pending_excel_candidate",
                "pending_field_count": len(FIELD_KEYS),
                "field_actions": FIELD_KEYS,
                "reason_pending": decision["reason_pending"],
                "next_review_trigger": decision["next_review_trigger"],
            },
        }
    )
    return preview


def build_preview(decision_path: Path | None) -> dict[str, Any]:
    if decision_path is None:
        return no_decision_preview()

    decision = read_json(decision_path)
    decision_code = validate_decision(decision)
    if set(FIELD_KEYS) != EXPECTED_FIELDS:
        raise SystemExit("configured field keys do not match S05-P2 intake contract")

    if decision_code == "provide_private_field_mapping":
        return private_mapping_preview(decision)
    if decision_code == "downgrade_to_cross_source_support":
        return downgrade_preview(decision)
    if decision_code == "keep_pending":
        return keep_pending_preview(decision)
    raise SystemExit(f"unsupported decision_code: {decision_code}")


def emit_preview(preview: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.write_text(text, encoding="utf-8")
    print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview KMFA S05-P2 owner decision application.")
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    preview = build_preview(args.decision)
    emit_preview(preview, args.output)
    return 0 if preview["application_status"] == "ready" else 2


if __name__ == "__main__":
    sys.exit(main())
