#!/usr/bin/env python3
"""Build Memory Atlas S08 P3 lightweight stage flight recorder."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json")
S08P1_REPORT_PATH = Path("data/derived/agent_collaboration/agent_collaboration_quality_report.json")
S08P2_REPORT_PATH = Path("data/derived/agent_collaboration/agent_authorization_boundary_report.json")
OUTPUT_PATH = Path("data/derived/agent_collaboration/stage_flight_recorder.json")
TASK_ID = "MA-V12-S08P3"
ACCEPTANCE_ID = "ACC-MA-V12-S08P3"
STATUS = "phase_s08_p3_stage_flight_recorder_completed_pending_s08_review"


class StageFlightBuildError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise StageFlightBuildError(f"{label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise StageFlightBuildError(f"{label} must be a JSON object: {path}")
    return payload


def evidence(ref_id: str, path: Path, source_id: str = "governance") -> dict[str, str]:
    return {
        "evidence_level": "lightweight_run_evidence",
        "path": path.as_posix(),
        "ref_id": ref_id,
        "ref_type": "stage_flight",
        "source_id": source_id,
    }


def validate_config(config: dict[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise StageFlightBuildError("stage flight recorder config identity mismatch")
    if config.get("recorder_mode") != "lightweight_run_evidence_fields":
        raise StageFlightBuildError("stage flight recorder must remain lightweight")
    field_policy = config.get("field_policy") if isinstance(config.get("field_policy"), dict) else {}
    max_fields = int(field_policy.get("max_required_fields") or 0)
    required_fields = [item for item in as_list(config.get("required_fields")) if isinstance(item, dict)]
    if not required_fields or len(required_fields) > max_fields:
        raise StageFlightBuildError("required field count violates lightweight policy")
    required_ids = {str(item.get("field_id")) for item in required_fields}
    for field_id in {
        "stage_id",
        "phase_id",
        "task_id",
        "acceptance_id",
        "status",
        "summary_zh",
        "evidence_refs",
        "validation_refs",
        "boundary_flags",
        "next_gate",
    }:
        if field_id not in required_ids:
            raise StageFlightBuildError(f"missing required stage flight field: {field_id}")
    for key in ["no_transcript_payloads", "no_raw_content", "no_bulky_human_docs", "development_record_summary_only"]:
        if field_policy.get(key) is not True:
            raise StageFlightBuildError(f"field policy {key} must be true")
    boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
    false_flags = {
        "raw_mutation",
        "github_main_upload",
        "complex_delegation_contract_ui",
        "multi_agent_system_implementation",
        "bulky_human_documentation",
        "human_readable_page_required",
    }
    for key in false_flags:
        if boundary.get(key) is not False:
            raise StageFlightBuildError(f"scope boundary {key} must be false")
    if boundary.get("development_record_summary_only") is not True:
        raise StageFlightBuildError("S08 P3 summary must stay in development records")
    if boundary.get("next_phase") != "S08 Review":
        raise StageFlightBuildError("S08 P3 next phase must be S08 Review")


def validate_inputs(s08p1: dict[str, Any], s08p2: dict[str, Any]) -> None:
    if s08p1.get("task_id") != "MA-V12-S08P1" or s08p1.get("acceptance_id") != "ACC-MA-V12-S08P1":
        raise StageFlightBuildError("S08 P1 collaboration report identity mismatch")
    if s08p2.get("task_id") != "MA-V12-S08P2" or s08p2.get("acceptance_id") != "ACC-MA-V12-S08P2":
        raise StageFlightBuildError("S08 P2 authorization report identity mismatch")
    if (s08p1.get("phase_boundary") or {}).get("does_not_generate_stage_flight_recorder") is not True:
        raise StageFlightBuildError("S08 P1 must defer stage flight recorder")
    if (s08p2.get("phase_boundary") or {}).get("does_not_generate_stage_flight_recorder") is not True:
        raise StageFlightBuildError("S08 P2 must defer stage flight recorder")


def check_item(
    check_id: str,
    name_zh: str,
    assertion: str,
    explanation_zh: str,
    evidence_refs: list[dict[str, str]],
    failure_action_zh: str,
) -> dict[str, Any]:
    if not evidence_refs:
        raise StageFlightBuildError(f"{check_id} missing evidence")
    return {
        "check_id": check_id,
        "name_zh": name_zh,
        "assertion": assertion,
        "status": "PASS",
        "explanation_zh": explanation_zh,
        "evidence_refs": evidence_refs,
        "failure_action_zh": failure_action_zh,
    }


def phase_record(
    phase_id: str,
    task_id: str,
    acceptance_id: str,
    status: str,
    summary_zh: str,
    evidence_refs: list[dict[str, str]],
    validation_refs: list[str],
    next_gate: str,
) -> dict[str, Any]:
    return {
        "stage_id": "S08",
        "phase_id": phase_id,
        "task_id": task_id,
        "acceptance_id": acceptance_id,
        "status": status,
        "summary_zh": summary_zh,
        "evidence_refs": evidence_refs,
        "validation_refs": validation_refs,
        "boundary_flags": {
            "raw_mutation": False,
            "github_main_upload": False,
            "complex_delegation_contract_ui": False,
            "multi_agent_system_implementation": False,
        },
        "next_gate": next_gate,
    }


def build_stage_flight_recorder(
    database_dir: Path,
    *,
    dry_run: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    config = load_json(database_dir / CONFIG_PATH, "stage flight recorder config")
    s08p1 = load_json(database_dir / S08P1_REPORT_PATH, "S08 P1 collaboration report")
    s08p2 = load_json(database_dir / S08P2_REPORT_PATH, "S08 P2 authorization report")
    validate_config(config)
    validate_inputs(s08p1, s08p2)

    configured_checks = [item for item in as_list(config.get("output_checks")) if isinstance(item, dict)]
    checks_by_id = {str(item.get("check_id")): item for item in configured_checks}
    required_fields = [item for item in as_list(config.get("required_fields")) if isinstance(item, dict)]
    phase_records = [
        phase_record(
            "S08 P1",
            "MA-V12-S08P1",
            "ACC-MA-V12-S08P1",
            "phase_s08_p1_collaboration_metrics_completed_pending_s08_p2",
            "S08 P1 生成 Codex/Agent 协作质量报告，保持证据化中文摘要。",
            [evidence("s08p1_collaboration_report", S08P1_REPORT_PATH, "derived")],
            ["validate:v1.2-s08-p1", "python scripts/atlasctl.py audit --check agent-collaboration"],
            "S08 P2",
        ),
        phase_record(
            "S08 P2",
            "MA-V12-S08P2",
            "ACC-MA-V12-S08P2",
            "phase_s08_p2_authorization_boundary_completed_pending_s08_p3",
            "S08 P2 定义授权边界，确认 raw 不可修改且 proposal 需人类授权。",
            [evidence("s08p2_authorization_report", S08P2_REPORT_PATH, "derived")],
            ["validate:v1.2-s08-p2", "python scripts/atlasctl.py audit --check agent-authorization"],
            "S08 P3",
        ),
        phase_record(
            "S08 P3",
            TASK_ID,
            ACCEPTANCE_ID,
            STATUS,
            "S08 P3 只记录 lightweight stage flight recorder 字段，不生成臃肿人类文档。",
            [evidence("s08p3_flight_recorder_config", CONFIG_PATH)],
            ["validate:v1.2-s08-p3", "python scripts/atlasctl.py audit --check stage-flight"],
            "S08 Review",
        ),
    ]

    output_checks = [
        check_item(
            "S08P3-CHECK-001",
            "字段数量保持轻量",
            checks_by_id["S08P3-CHECK-001"]["assertion"],
            f"required_fields 当前为 {len(required_fields)} 个，未超过 max_required_fields。",
            [evidence("s08p3_flight_recorder_config", CONFIG_PATH)],
            checks_by_id["S08P3-CHECK-001"]["failure_action_zh"],
        ),
        check_item(
            "S08P3-CHECK-002",
            "不携带 raw 或 transcript 载荷",
            checks_by_id["S08P3-CHECK-002"]["assertion"],
            "field_policy 明确 no_transcript_payloads、no_raw_content、no_bulky_human_docs 均为 true。",
            [evidence("s08p3_flight_recorder_config", CONFIG_PATH)],
            checks_by_id["S08P3-CHECK-002"]["failure_action_zh"],
        ),
        check_item(
            "S08P3-CHECK-003",
            "覆盖 S08 三个 phase",
            checks_by_id["S08P3-CHECK-003"]["assertion"],
            "phase_records 覆盖 S08 P1、S08 P2、S08 P3，且每条都有 evidence_refs 和 validation_refs。",
            [
                evidence("s08p1_collaboration_report", S08P1_REPORT_PATH, "derived"),
                evidence("s08p2_authorization_report", S08P2_REPORT_PATH, "derived"),
                evidence("s08p3_flight_recorder_config", CONFIG_PATH),
            ],
            checks_by_id["S08P3-CHECK-003"]["failure_action_zh"],
        ),
        check_item(
            "S08P3-CHECK-004",
            "只在开发记录总结必要信息",
            checks_by_id["S08P3-CHECK-004"]["assertion"],
            "scope_boundary 标记 development_record_summary_only=true，human_readable_page_required=false。",
            [evidence("s08p3_flight_recorder_config", CONFIG_PATH)],
            checks_by_id["S08P3-CHECK-004"]["failure_action_zh"],
        ),
    ]
    report = {
        "schema_version": "memory_atlas_stage_flight_recorder.v1_2_s08_p3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": generated_at or now_utc(),
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "config_path": CONFIG_PATH.as_posix(),
        "output_path": OUTPUT_PATH.as_posix(),
        "stage_id": "S08",
        "recorder_mode": config["recorder_mode"],
        "field_policy": config["field_policy"],
        "required_fields": required_fields,
        "phase_records": phase_records,
        "machine_output_checks": output_checks,
        "machine_output_check_summary": {
            "check_count": len(output_checks),
            "pass_count": len([item for item in output_checks if item["status"] == "PASS"]),
            "fail_count": 0,
            "required_field_count": len(required_fields),
            "phase_record_count": len(phase_records),
            "bulky_human_documentation": False,
        },
        "stage_summary_zh": "S08 已具备协作质量、授权边界和轻量运行证据，可进入 S08 Review。",
        "phase_boundary": {
            "lightweight_stage_flight_recorder": True,
            "does_not_include_raw_or_transcript_payloads": True,
            "does_not_generate_bulky_human_docs": True,
            "records_necessary_info_in_development_records": True,
            "does_not_modify_raw": True,
            "does_not_upload_github_main": True,
            "does_not_create_multi_agent_system": True,
            "does_not_implement_complex_delegation_contract_ui": True,
            "next_phase": "S08 Review",
        },
    }
    if not dry_run:
        output_path = database_dir / OUTPUT_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Memory Atlas v1.2 S08 P3 stage flight recorder.")
    parser.add_argument("--database-dir", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = build_stage_flight_recorder(args.database_dir, dry_run=args.dry_run)
    except StageFlightBuildError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
