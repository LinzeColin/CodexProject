#!/usr/bin/env python3
"""Build KMFA S17-P2 public-safe notification reminder artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "notifications" / "notification_manifest.json"
DEFAULT_OUTPUT_RULES = ROOT / "metadata" / "notifications" / "notification_rules.jsonl"
DEFAULT_OUTPUT_EVENTS = ROOT / "metadata" / "notifications" / "notification_events.jsonl"
DEFAULT_OUTPUT_DISPATCH_LOG = ROOT / "metadata" / "notifications" / "notification_dispatch_log.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S17_P2_notification"
    / "machine"
    / "s17_p2_manifest.json"
)

REQUIRED_NOTIFICATION_TRIGGERS = (
    "report_generation_completed",
    "major_risk",
    "data_source_missing",
)

POLICY_VERSION = "KMFA-S17P2-NOTIFICATION-REMINDER-PUBLIC-SAFE-001"
RULE_VERSION = "NOTIFY-RULE-KMFA-S17P2-001"
EVENT_VERSION = "NOTIFY-EVENT-KMFA-S17P2-001"
DISPATCH_VERSION = "NOTIFY-DISPATCH-KMFA-S17P2-METADATA-OUTBOX-001"

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "private://",
    "private_ref://",
    "full_report_body_text",
    "complete_report_body_text",
    "report_attachment_path",
    "recipient_email",
    "smtp",
    "sk-",
    "-----BEGIN",
)


class NotificationReminderError(ValueError):
    """Raised when S17-P2 notification reminder artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise NotificationReminderError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise NotificationReminderError(f"{path} contains a non-object JSONL record")
            rows.append(value)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "private_tabular_material_committed": False,
        "source_document_committed": False,
        "field_text_committed": False,
        "true_money_committed": False,
        "true_customer_project_committed": False,
        "recipient_address_committed": False,
        "credential_committed": False,
        "full_report_body_committed": False,
        "report_attachment_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s17_p1_scope_included": False,
        "s17_p2_scope_included": True,
        "s17_p3_scope_included": False,
        "stage17_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "business_execution_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "notification_rules_complete": True,
        "notification_events_generated": True,
        "notification_logs_written_to_metadata": True,
        "email_reminder_only": True,
        "email_full_report_body_allowed": False,
        "email_attachment_allowed": False,
        "recipient_address_plaintext_allowed": False,
        "raw_payload_allowed": False,
        "external_email_connector_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_allowed": False,
        "s17_p3_scope_allowed": False,
        "stage17_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "release_block_reason": "s17_p2_is_local_metadata_notification_reminder_only",
    }


def _notification_rule_specs() -> list[dict[str, str]]:
    return [
        {
            "trigger_type": "report_generation_completed",
            "recipient_role": "management",
            "priority": "normal",
            "subject_template_id": "KMFA-S17P2-SUBJECT-REPORT-READY",
            "body_template_id": "KMFA-S17P2-BODY-REPORT-READY-REMINDER",
            "trigger_evidence_ref": "KMFA/metadata/reports/report_export_manifest.json",
            "body_summary": "报告预览已生成，请在系统内查看 D 级限制和证据索引。",
        },
        {
            "trigger_type": "major_risk",
            "recipient_role": "reviewer",
            "priority": "high",
            "subject_template_id": "KMFA-S17P2-SUBJECT-MAJOR-RISK",
            "body_template_id": "KMFA-S17P2-BODY-MAJOR-RISK-REMINDER",
            "trigger_evidence_ref": "KMFA/metadata/reports/operating_report_quality_report.json",
            "body_summary": "存在重大风险或 D 级阻断，请复核风险清单和人工事项。",
        },
        {
            "trigger_type": "data_source_missing",
            "recipient_role": "finance",
            "priority": "high",
            "subject_template_id": "KMFA-S17P2-SUBJECT-MISSING-SOURCE",
            "body_template_id": "KMFA-S17P2-BODY-MISSING-SOURCE-REMINDER",
            "trigger_evidence_ref": "KMFA/metadata/imports/source_check_matrix.jsonl",
            "body_summary": "存在数据源缺失或待补证，请补齐授权导出并重新登记。",
        },
    ]


def _notification_rules() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in _notification_rule_specs():
        trigger_type = spec["trigger_type"]
        rows.append(
            {
                "record_type": "notification_rule",
                "policy_version": RULE_VERSION,
                "rule_id": f"notification_rule_s17p2_{trigger_type}",
                "trigger_type": trigger_type,
                "channel": "email_reminder",
                "recipient_role": spec["recipient_role"],
                "priority": spec["priority"],
                "subject_template_id": spec["subject_template_id"],
                "body_template_id": spec["body_template_id"],
                "body_summary_max_chars": 120,
                "full_report_body_allowed": False,
                "report_attachment_allowed": False,
                "raw_payload_allowed": False,
                "recipient_address_plaintext_allowed": False,
                "metadata_log_required": True,
                "public_safe_template_only": True,
                "external_connector_required": False,
                "trigger_evidence_ref": spec["trigger_evidence_ref"],
                "metadata_target": "KMFA/metadata/notifications/notification_rules.jsonl",
            }
        )
    return rows


def _notification_events(generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in _notification_rule_specs():
        trigger_type = spec["trigger_type"]
        rows.append(
            {
                "record_type": "notification_event",
                "event_id": f"NOTIFY-EVENT-S17P2-{trigger_type}",
                "policy_version": EVENT_VERSION,
                "event_time": generated_at,
                "trigger_type": trigger_type,
                "source_state_ref": spec["trigger_evidence_ref"],
                "recipient_role": spec["recipient_role"],
                "channel": "email_reminder",
                "append_only": True,
                "metadata_target": "KMFA/metadata/notifications/notification_events.jsonl",
                "raw_business_data_included": False,
                "full_report_body_included": False,
                "report_attachment_included": False,
                "recipient_address_plaintext_included": False,
                "evidence_ref": "KMFA/metadata/notifications/notification_events.jsonl",
                "result_status": "notification_event_generated",
            }
        )
    return rows


def _dispatch_logs(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    body_summaries = {spec["trigger_type"]: spec["body_summary"] for spec in _notification_rule_specs()}
    rows: list[dict[str, Any]] = []
    for event in events:
        trigger_type = event["trigger_type"]
        rows.append(
            {
                "record_type": "notification_dispatch_log",
                "dispatch_log_id": f"NOTIFY-DISPATCH-S17P2-{trigger_type}",
                "event_id": event["event_id"],
                "policy_version": DISPATCH_VERSION,
                "trigger_type": trigger_type,
                "recipient_role": event["recipient_role"],
                "recipient_address_ref": "role_ref_only",
                "channel": "email_reminder",
                "delivery_mode": "metadata_outbox_only",
                "delivery_status": "metadata_logged",
                "result_status": "metadata_logged",
                "body_summary": body_summaries[trigger_type],
                "subject_template_id": next(
                    spec["subject_template_id"]
                    for spec in _notification_rule_specs()
                    if spec["trigger_type"] == trigger_type
                ),
                "body_template_id": next(
                    spec["body_template_id"]
                    for spec in _notification_rule_specs()
                    if spec["trigger_type"] == trigger_type
                ),
                "full_report_body_included": False,
                "report_attachment_included": False,
                "raw_payload_included": False,
                "append_only": True,
                "metadata_target": "KMFA/metadata/notifications/notification_dispatch_log.jsonl",
                "evidence_ref": "KMFA/metadata/notifications/notification_dispatch_log.jsonl",
            }
        )
    return rows


def _manifest(generated_at: str, rules: list[dict[str, Any]], events: list[dict[str, Any]], dispatch_logs: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "notification_rule_count": len(rules),
        "notification_event_count": len(events),
        "notification_dispatch_log_count": len(dispatch_logs),
        "trigger_type_count": len({row["trigger_type"] for row in rules}),
    }
    payload_hash = _sha256_json(
        {
            "rules": rules,
            "events": events,
            "dispatch_logs": dispatch_logs,
            "summary": summary,
            "stage_scope": _stage_scope(),
            "quality_gate": _quality_gate(),
        }
    )
    return {
        "record_type": "s17_p2_notification_manifest",
        "project_id": "KMFA",
        "stage_id": "S17",
        "stage_phase": "S17-P2",
        "phase_id": "S17PB",
        "iteration_id": "ITER-20260701-KMFA-S17P2-NOTIFICATION",
        "policy_version": POLICY_VERSION,
        "generated_at": generated_at,
        "required_notification_triggers": list(REQUIRED_NOTIFICATION_TRIGGERS),
        "summary": summary,
        "public_repo_safety": _public_repo_safety(),
        "stage_scope": _stage_scope(),
        "quality_gate": _quality_gate(),
        "metadata_outputs": {
            "notification_manifest": "KMFA/metadata/notifications/notification_manifest.json",
            "notification_rules": "KMFA/metadata/notifications/notification_rules.jsonl",
            "notification_events": "KMFA/metadata/notifications/notification_events.jsonl",
            "notification_dispatch_log": "KMFA/metadata/notifications/notification_dispatch_log.jsonl",
        },
        "stage_artifact_ref": "KMFA/stage_artifacts/S17_P2_notification/machine/s17_p2_manifest.json",
        "content_hash": payload_hash,
        "fact_level": "EXTRACTED",
    }


def build_default_notification_reminders(
    generated_at: str = "2026-07-01T23:59:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rules = _notification_rules()
    events = _notification_events(generated_at=generated_at)
    dispatch_logs = _dispatch_logs(events)
    manifest = _manifest(
        generated_at=generated_at,
        rules=rules,
        events=events,
        dispatch_logs=dispatch_logs,
    )
    return manifest, rules, events, dispatch_logs


def _scan_forbidden_payload(payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        if forbidden in encoded:
            raise NotificationReminderError(f"forbidden public payload text found: {forbidden}")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise NotificationReminderError(message)


def validate_notification_reminder_artifacts(
    manifest: dict[str, Any],
    rules: list[dict[str, Any]],
    events: list[dict[str, Any]],
    dispatch_logs: list[dict[str, Any]],
) -> None:
    _scan_forbidden_payload([manifest, rules, events, dispatch_logs])

    _require(manifest.get("stage_phase") == "S17-P2", "manifest must be S17-P2")
    _require(tuple(manifest.get("required_notification_triggers", [])) == REQUIRED_NOTIFICATION_TRIGGERS, "required notification triggers drift")

    quality_gate = manifest.get("quality_gate", {})
    stage_scope = manifest.get("stage_scope", {})
    for key in (
        "notification_rules_complete",
        "notification_events_generated",
        "notification_logs_written_to_metadata",
        "email_reminder_only",
    ):
        _require(quality_gate.get(key) is True, f"quality gate must enable {key}")
    for key in (
        "email_full_report_body_allowed",
        "email_attachment_allowed",
        "recipient_address_plaintext_allowed",
        "raw_payload_allowed",
        "external_email_connector_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "lineage_full_check_allowed",
        "s17_p3_scope_allowed",
        "stage17_review_allowed",
        "github_upload_allowed",
        "phase_completion_upload_allowed",
    ):
        _require(quality_gate.get(key) is False, f"quality gate must block {key}")
    _require(stage_scope.get("s17_p2_scope_included") is True, "S17-P2 scope must be included")
    for key, value in stage_scope.items():
        if key != "s17_p2_scope_included":
            _require(value is False, f"stage scope must exclude {key}")

    rules_by_trigger = {row.get("trigger_type"): row for row in rules}
    events_by_trigger = {row.get("trigger_type"): row for row in events}
    logs_by_trigger = {row.get("trigger_type"): row for row in dispatch_logs}
    required = set(REQUIRED_NOTIFICATION_TRIGGERS)
    _require(set(rules_by_trigger) == required, "notification rules must cover required triggers")
    _require(set(events_by_trigger) == required, "notification events must cover required triggers")
    _require(set(logs_by_trigger) == required, "notification dispatch logs must cover required triggers")
    _require(manifest.get("summary", {}).get("notification_rule_count") == len(rules) == 3, "notification rule count drift")
    _require(manifest.get("summary", {}).get("notification_event_count") == len(events) == 3, "notification event count drift")
    _require(manifest.get("summary", {}).get("notification_dispatch_log_count") == len(dispatch_logs) == 3, "dispatch log count drift")

    for trigger_type, row in rules_by_trigger.items():
        _require(row.get("record_type") == "notification_rule", "rule record type drift")
        _require(row.get("channel") == "email_reminder", "rules must use email reminder channel")
        _require(row.get("recipient_role") in {"management", "finance", "reviewer"}, "rule recipient role drift")
        _require(row.get("full_report_body_allowed") is False, "full report body must be blocked in rule")
        _require(row.get("report_attachment_allowed") is False, "report attachment must be blocked in rule")
        _require(row.get("raw_payload_allowed") is False, "raw payload must be blocked in rule")
        _require(row.get("recipient_address_plaintext_allowed") is False, "recipient address plaintext must be blocked")
        _require(row.get("metadata_log_required") is True, "metadata log must be required")
        _require(row.get("public_safe_template_only") is True, "templates must be public-safe only")
        _require(row.get("external_connector_required") is False, "external connector must not be required")
        _require(str(trigger_type) in str(row.get("rule_id")), "rule id must include trigger type")

    event_ids = {row.get("event_id") for row in events}
    for row in events:
        _require(row.get("record_type") == "notification_event", "event record type drift")
        _require(row.get("append_only") is True, "events must be append-only")
        _require(row.get("metadata_target") == "KMFA/metadata/notifications/notification_events.jsonl", "event metadata target drift")
        _require(row.get("raw_business_data_included") is False, "event raw data must be absent")
        _require(row.get("full_report_body_included") is False, "event full report body must be absent")
        _require(row.get("report_attachment_included") is False, "event report attachment must be absent")
        _require(row.get("recipient_address_plaintext_included") is False, "event recipient address plaintext must be absent")
        _require(bool(row.get("evidence_ref")), "event evidence ref required")

    for row in dispatch_logs:
        encoded = json.dumps(row, ensure_ascii=False, sort_keys=True)
        _require("@" not in encoded, "dispatch log must not contain email address plaintext")
        _require(row.get("record_type") == "notification_dispatch_log", "dispatch log record type drift")
        _require(row.get("event_id") in event_ids, "dispatch log event id missing from events")
        _require(row.get("channel") == "email_reminder", "dispatch channel drift")
        _require(row.get("delivery_mode") == "metadata_outbox_only", "delivery mode drift")
        _require(row.get("delivery_status") == "metadata_logged", "delivery status drift")
        _require(row.get("result_status") == "metadata_logged", "result status drift")
        _require(row.get("recipient_address_ref") == "role_ref_only", "recipient address must be role ref only")
        _require(row.get("full_report_body_included") is False, "dispatch full report body must be absent")
        _require(row.get("report_attachment_included") is False, "dispatch report attachment must be absent")
        _require(row.get("raw_payload_included") is False, "dispatch raw payload must be absent")
        _require(row.get("append_only") is True, "dispatch logs must be append-only")
        _require(row.get("metadata_target") == "KMFA/metadata/notifications/notification_dispatch_log.jsonl", "dispatch metadata target drift")
        _require(len(str(row.get("body_summary", ""))) <= 120, "body summary too long")


def write_default_notification_reminders(
    *,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    rules_path: Path = DEFAULT_OUTPUT_RULES,
    events_path: Path = DEFAULT_OUTPUT_EVENTS,
    dispatch_log_path: Path = DEFAULT_OUTPUT_DISPATCH_LOG,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    generated_at: str = "2026-07-01T23:59:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest, rules, events, dispatch_logs = build_default_notification_reminders(generated_at=generated_at)
    validate_notification_reminder_artifacts(manifest, rules, events, dispatch_logs)
    write_json(manifest_path, manifest)
    write_jsonl(rules_path, rules)
    write_jsonl(events_path, events)
    write_jsonl(dispatch_log_path, dispatch_logs)
    stage_manifest = dict(manifest)
    stage_manifest["record_type"] = "s17_p2_stage_artifact_manifest"
    stage_manifest["metadata_manifest_ref"] = "KMFA/metadata/notifications/notification_manifest.json"
    write_json(stage_manifest_path, stage_manifest)
    return manifest, rules, events, dispatch_logs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S17-P2 public-safe notification reminder artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:59:00+10:00")
    parser.add_argument("--check-only", action="store_true", help="Validate generated defaults without writing files.")
    args = parser.parse_args(argv)

    manifest, rules, events, dispatch_logs = build_default_notification_reminders(generated_at=args.generated_at)
    validate_notification_reminder_artifacts(manifest, rules, events, dispatch_logs)
    if not args.check_only:
        write_default_notification_reminders(generated_at=args.generated_at)
    print(
        "PASS: generated S17-P2 notification artifacts "
        f"(rules={len(rules)}, events={len(events)}, dispatch_logs={len(dispatch_logs)}, "
        "email_reminder_only=true, full_report_body=false, metadata_logs=true, "
        "stage17_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
