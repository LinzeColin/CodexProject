#!/usr/bin/env python3
"""Validate KMFA v0.1.4 current-state pointers after owner fill application."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_VERSION = "0.1.4-private-processed-value-source-map-owner-authorized-fill-application"
EXPECTED_PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION"
EXPECTED_STATUS = "completed_validated_local_only_no_go_active_owner_authorized_fill_record_missing"
EXPECTED_NEXT_INPUT = "active_owner_or_authorized_delegate_fill_record"
REPAIR_PHASE_ID = "V014_CURRENT_STATE_POINTER_REPAIR"

ROOT = Path(__file__).resolve().parents[2]
VERSION_PATH = ROOT / "KMFA" / "VERSION"
HANDOFF_PATH = ROOT / "KMFA" / "HANDOFF.md"
STATUS_PATH = ROOT / "KMFA" / "docs" / "governance" / "STATUS.md"
OWNER_STATUS_PATH = ROOT / "KMFA" / "docs" / "governance" / "OWNER_STATUS.md"
FEATURES_PATH = ROOT / "KMFA" / "功能清单.md"
PARAMETERS_PATH = ROOT / "KMFA" / "模型参数文件.md"
APPLICATION_MANIFEST_PATH = (
    ROOT
    / "KMFA"
    / "stage_artifacts"
    / EXPECTED_PHASE_ID
    / "machine"
    / "private_processed_value_source_map_owner_authorized_fill_application_manifest.json"
)
EVIDENCE_DIR = ROOT / "KMFA" / "stage_artifacts" / REPAIR_PHASE_ID
EVIDENCE_MANIFEST_PATH = EVIDENCE_DIR / "machine" / "current_state_pointer_repair_manifest.json"
EVIDENCE_REPORT_PATH = EVIDENCE_DIR / "human" / "current_state_pointer_repair_report.md"

REPAIRED_PUBLIC_STATE_FILES = [
    HANDOFF_PATH,
    STATUS_PATH,
    OWNER_STATUS_PATH,
    FEATURES_PATH,
    PARAMETERS_PATH,
]


class ValidationError(Exception):
    pass


def _read_text(path: Path) -> str:
    if not path.exists():
        raise ValidationError(f"missing required file: {path}")
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing required JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _section_until(text: str, marker: str) -> str:
    return text.split(marker, 1)[0] if marker in text else text


def _section_between(text: str, start: str, end: str) -> str:
    if start not in text:
        raise ValidationError(f"missing section start: {start}")
    section = text.split(start, 1)[1]
    return section.split(end, 1)[0] if end in section else section


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _application_gate_summary(manifest: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    go_no_go = manifest.get("go_no_go")
    summary = manifest.get("owner_authorized_fill_application_summary")
    _require(isinstance(go_no_go, dict), "application manifest go_no_go must be an object", errors)
    _require(isinstance(summary, dict), "application summary must be an object", errors)
    if not isinstance(go_no_go, dict) or not isinstance(summary, dict):
        return {}

    _require(manifest.get("phase_id") == EXPECTED_PHASE_ID, "application phase_id mismatch", errors)
    _require(manifest.get("status") == "owner_authorized_fill_application_blocked_no_active_fill_record_no_go", "application status mismatch", errors)
    _require(go_no_go.get("decision") == "NO_GO", "application decision must be NO_GO", errors)
    _require(go_no_go.get("next_required_input") == EXPECTED_NEXT_INPUT, "application next_required_input mismatch", errors)
    _require(go_no_go.get("active_authorized_fill_record_found") is False, "active fill record must remain false", errors)
    _require(go_no_go.get("fill_application_performed") is False, "fill application must remain false", errors)
    _require(go_no_go.get("processed_value_materialization_replay_allowed") is False, "materialization replay must remain blocked", errors)
    _require(go_no_go.get("raw_to_processed_value_comparison_allowed") is False, "raw comparison must remain blocked", errors)
    _require(go_no_go.get("github_upload_allowed") is False, "GitHub upload must remain blocked", errors)
    _require(summary.get("source_unresolved_gap_item_count") == 113, "unresolved gap count mismatch", errors)
    _require(summary.get("final_discrepancy_report_required_if_later_cross_validation_fails") is True, "discrepancy duty missing", errors)
    return {
        "go_no_go_decision": go_no_go.get("decision"),
        "next_required_input": go_no_go.get("next_required_input"),
        "processed_value_materialization_replay_allowed": go_no_go.get("processed_value_materialization_replay_allowed"),
        "raw_to_processed_value_comparison_allowed": go_no_go.get("raw_to_processed_value_comparison_allowed"),
        "github_upload_allowed": go_no_go.get("github_upload_allowed"),
        "source_unresolved_gap_item_count": summary.get("source_unresolved_gap_item_count"),
        "private_intake_request_item_count": summary.get("private_intake_request_item_count"),
        "candidate_active_fill_record_path_count": summary.get("candidate_active_fill_record_path_count"),
        "final_discrepancy_report_required_if_later_cross_validation_fails": summary.get(
            "final_discrepancy_report_required_if_later_cross_validation_fails"
        ),
    }


def validate_current_state_pointer_repair() -> dict[str, Any]:
    errors: list[str] = []
    version = _read_text(VERSION_PATH).strip()
    manifest = _read_json(APPLICATION_MANIFEST_PATH)
    application = _application_gate_summary(manifest, errors)

    handoff_top = _section_until(_read_text(HANDOFF_PATH), "## v0.1.3 历史状态")
    status_top = _section_until(_read_text(STATUS_PATH), "## 已完成")
    owner_status_top = _section_until(_read_text(OWNER_STATUS_PATH), "## 你现在能信任什么")
    features_summary = _section_between(_read_text(FEATURES_PATH), "## 摘要", "## Owner 决策")
    parameters_summary = _section_between(_read_text(PARAMETERS_PATH), "## 摘要", "## 证据")

    _require(version == EXPECTED_VERSION, f"VERSION mismatch: {version!r}", errors)

    for label, section in (
        ("handoff_top", handoff_top),
        ("status_top", status_top),
        ("owner_status_top", owner_status_top),
        ("features_summary", features_summary),
        ("parameters_summary", parameters_summary),
    ):
        _require(EXPECTED_PHASE_ID in section, f"{label} missing latest phase id", errors)
        _require(EXPECTED_VERSION in section, f"{label} missing latest version", errors)
        _require(EXPECTED_NEXT_INPUT in section, f"{label} missing next required input", errors)
        _require("materialization replay" in section or "processed value materialization" in section, f"{label} missing replay blocker", errors)
        _require("raw-to-processed" in section or "raw comparison" in section, f"{label} missing raw comparison blocker", errors)

    _require("current_phase: `V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE`" not in status_top, "status top still points to intake", errors)
    _require("current_phase: `V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE`" not in features_summary, "features summary still points to intake", errors)
    _require("current_phase: `V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE`" not in parameters_summary, "parameters summary still points to intake", errors)
    _require("next_gate: `private_processed_value_source_map_owner_authorized_fill_application`" not in features_summary, "features next gate still points to completed application", errors)
    _require("next_gate: `private_processed_value_source_map_owner_authorized_fill_application`" not in parameters_summary, "parameters next gate still points to completed application", errors)

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "record_type": "v014_current_state_pointer_repair_manifest",
        "phase_id": REPAIR_PHASE_ID,
        "canonical_phase_id": EXPECTED_PHASE_ID,
        "canonical_version": EXPECTED_VERSION,
        "canonical_status": EXPECTED_STATUS,
        "source_evidence_ref": str(APPLICATION_MANIFEST_PATH.relative_to(ROOT)),
        "repaired_public_state_file_count": len(REPAIRED_PUBLIC_STATE_FILES),
        "repaired_public_state_files": [str(path.relative_to(ROOT)) for path in REPAIRED_PUBLIC_STATE_FILES],
        "handoff_top_current": EXPECTED_PHASE_ID in handoff_top,
        "status_top_current": EXPECTED_PHASE_ID in status_top,
        "owner_status_top_current": EXPECTED_PHASE_ID in owner_status_top,
        "features_summary_current": EXPECTED_PHASE_ID in features_summary,
        "parameters_summary_current": EXPECTED_PHASE_ID in parameters_summary,
        "raw_inbox_access_performed_by_repair": False,
        "raw_inbox_mutation_performed_by_repair": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        **application,
    }


def validate_recorded_current_state_pointer_repair() -> dict[str, Any]:
    """Validate the frozen repair evidence without treating it as today's pointer."""
    errors: list[str] = []
    evidence = _read_json(EVIDENCE_MANIFEST_PATH)
    _require(evidence.get("phase_id") == REPAIR_PHASE_ID, "recorded repair phase mismatch", errors)
    _require(evidence.get("canonical_phase_id") == EXPECTED_PHASE_ID, "recorded canonical phase mismatch", errors)
    _require(evidence.get("canonical_version") == EXPECTED_VERSION, "recorded canonical version mismatch", errors)
    _require(evidence.get("canonical_status") == EXPECTED_STATUS, "recorded canonical status mismatch", errors)
    _require(evidence.get("go_no_go_decision") == "NO_GO", "recorded decision mismatch", errors)
    _require(evidence.get("next_required_input") == EXPECTED_NEXT_INPUT, "recorded next input mismatch", errors)
    _require(evidence.get("repaired_public_state_file_count") == 5, "recorded repair file count mismatch", errors)
    for key in (
        "handoff_top_current",
        "status_top_current",
        "owner_status_top_current",
        "features_summary_current",
        "parameters_summary_current",
    ):
        _require(evidence.get(key) is True, f"recorded {key} must be true", errors)
    for key in (
        "processed_value_materialization_replay_allowed",
        "raw_to_processed_value_comparison_allowed",
        "github_upload_allowed",
        "raw_inbox_access_performed_by_repair",
        "raw_inbox_mutation_performed_by_repair",
        "github_upload_performed",
        "app_reinstall_performed",
    ):
        _require(evidence.get(key) is False, f"recorded {key} must be false", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return evidence


def write_evidence() -> dict[str, Any]:
    evidence = validate_current_state_pointer_repair()
    (EVIDENCE_MANIFEST_PATH.parent).mkdir(parents=True, exist_ok=True)
    (EVIDENCE_REPORT_PATH.parent).mkdir(parents=True, exist_ok=True)
    EVIDENCE_MANIFEST_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    EVIDENCE_REPORT_PATH.write_text(
        "\n".join(
            [
                "# V014 Current State Pointer Repair",
                "",
                f"- phase_id: `{REPAIR_PHASE_ID}`",
                f"- canonical_phase_id: `{EXPECTED_PHASE_ID}`",
                f"- canonical_version: `{EXPECTED_VERSION}`",
                f"- go_no_go_decision: `{evidence['go_no_go_decision']}`",
                f"- next_required_input: `{EXPECTED_NEXT_INPUT}`",
                "- repaired_public_state_file_count: `5`",
                "- raw_inbox_access_performed_by_repair: `false`",
                "- raw_inbox_mutation_performed_by_repair: `false`",
                "- github_upload_performed: `false`",
                "- app_reinstall_performed: `false`",
                "",
                "This repair only realigns public current-state pointers to the already validated owner-authorized fill application gate. It does not create an active fill record, does not run materialization replay, does not run raw-to-processed comparison, and does not claim business value consistency.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true", help="write public-safe repair evidence after validation")
    args = parser.parse_args(argv)
    try:
        evidence = write_evidence() if args.write_evidence else validate_current_state_pointer_repair()
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **evidence}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
