#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 1-18 overall review evidence.

This phase is a local, public-safe final readiness audit. It summarizes the
existing v0.1.4 Stage 1-18 review evidence and keeps release, upload, app
reinstall, and business execution blocked until raw alignment and lineage
completion gates are separately resolved.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


TASK_ID = "KMFA-V014-STAGE1-18-OVERALL-REVIEW-20260705"
ACCEPTANCE_ID = "ACC-V014-STAGE1-18-OVERALL-REVIEW"
SCHEMA_VERSION = "kmfa.v014_stage1_18_overall_review.v1"
REVIEW_SCOPE = "v014_stage1_18_overall_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_STAGE1_18_OVERALL_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage1_18_overall_review_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage1_18_overall_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "overall_review_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_stage1_18_overall_review_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_stage1_18_overall_go_no_go_report.json")

TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
S05_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S05_P1_A0_FILE_REGISTRATION/machine/a0_file_registration_manifest.json"
)
LINEAGE_REVIEW_PATH = Path("KMFA/metadata/lineage/lineage_completeness_review.json")
S18_STAGE_REVIEW_PATH = Path("KMFA/metadata/quality/v014_s18_stage_review_manifest.json")

NEXT_PHASE = "V014_RAW_ALIGNMENT_REMEDIATION"
NEXT_REQUIRED_STEP = (
    "Resolve raw alignment and lineage completeness in a separate phase before any GitHub main upload, "
    "app reinstall, formal report release, production restore, external service call, live connector call, "
    "or business execution."
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def stage_review_manifest_path(stage_no: int) -> Path:
    stage_id = f"S{stage_no:02d}"
    machine_dir = Path(f"KMFA/stage_artifacts/V014_{stage_id}_STAGE_REVIEW/machine")
    matches = sorted(machine_dir.glob(f"stage{stage_no}_review_manifest.json"))
    if not matches:
        matches = sorted(machine_dir.glob("*review_manifest.json"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one Stage {stage_no} review manifest, found {len(matches)}")
    return matches[0]


def load_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = ROADMAP_PATH.read_text(encoding="utf-8")
    for token in ("不提交原始敏感数据到公开GitHub", "不把缺数据报告伪装成完整报告", "Go/No-Go评审通过"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing required marker: {token}")
    for token in ("S01", "S18", "精度与压力测试", "全量回归和验收"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing required marker: {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_stage_count": 18,
        "roadmap_phase_count": 54,
        "roadmap_task_count": 162,
        "public_safe_boundary_confirmed": True,
        "source_refs": {
            "taskpack": TASKPACK_PATH.as_posix(),
            "roadmap": ROADMAP_PATH.as_posix(),
        },
    }


def _open_finding_count(payload: dict[str, Any]) -> int:
    summary = payload.get("review_findings_summary")
    if isinstance(summary, dict) and isinstance(summary.get("open_finding_count"), int):
        return int(summary["open_finding_count"])
    for key in ("open_review_finding_count", "open_finding_count"):
        if isinstance(payload.get(key), int):
            return int(payload[key])
    return 0


def load_stage_review_summary() -> dict[str, Any]:
    stage_summaries: list[dict[str, Any]] = []
    open_findings = 0
    pass_count = 0
    for stage_no in range(1, 19):
        path = stage_review_manifest_path(stage_no)
        payload = read_json(path)
        stage_id = f"S{stage_no:02d}"
        status = str(payload.get("status") or "")
        open_count = _open_finding_count(payload)
        review_performed = payload.get("stage_review_performed") is True or "review_passed" in status
        stage_passed = review_performed and open_count == 0 and "review_passed" in status
        if stage_passed:
            pass_count += 1
        open_findings += open_count
        stage_summaries.append(
            {
                "stage_id": stage_id,
                "status": status,
                "review_manifest": path.as_posix(),
                "review_performed": review_performed,
                "stage_passed": stage_passed,
                "open_finding_count": open_count,
                "github_upload_performed": payload.get("github_upload_performed") is True,
            }
        )
    return {
        "stage_review_count": len(stage_summaries),
        "stage_review_pass_count": pass_count,
        "completed_stage_ids": [item["stage_id"] for item in stage_summaries if item["stage_passed"]],
        "total_phase_count": 54,
        "total_task_count": 162,
        "open_stage_review_finding_count": open_findings,
        "stage_validator_rerun_required_by_validator": True,
        "stage_validator_rerun_performed_by_generator": False,
        "stage_summaries": stage_summaries,
    }


def raw_alignment_gate() -> dict[str, Any]:
    s05_p1 = read_json(S05_P1_MANIFEST_PATH)
    raw = s05_p1.get("raw_alignment", {})
    if not isinstance(raw, dict):
        raise RuntimeError("S05-P1 raw_alignment must be an object")
    return {
        "source_phase": "S05-P1",
        "s05_p1_private_raw_registration_evidence_present": raw.get("private_package_hash_recorded") is True,
        "raw_alignment_complete": False,
        "local_raw_package_hash_matches_registered": raw.get("local_raw_package_hash_matches_registered") is True,
        "local_raw_package_size_matches_registered": raw.get("local_raw_package_size_matches_registered") is True,
        "raw_publication_allowed": False,
        "raw_inbox_read_by_this_overall_review": False,
        "raw_inbox_listed_by_this_overall_review": False,
        "raw_inbox_hashed_by_this_overall_review": False,
        "raw_inbox_mutated_by_this_overall_review": False,
        "public_raw_filenames_committed": raw.get("public_raw_member_names_committed") is True,
        "public_raw_hashes_committed": raw.get("public_actual_raw_package_hash_committed") is True
        or raw.get("public_actual_raw_member_hashes_committed") is True,
        "blocker_ids": [
            "RAW_ALIGNMENT_NOT_PROVEN_COMPLETE",
            "RAW_PACKAGE_HASH_OR_SIZE_MISMATCH",
        ],
    }


def lineage_gate() -> dict[str, Any]:
    lineage = read_json(LINEAGE_REVIEW_PATH)
    return {
        "lineage_review_ref": LINEAGE_REVIEW_PATH.as_posix(),
        "lineage_status": lineage.get("status"),
        "lineage_full_check_complete": lineage.get("lineage_full_check_complete") is True,
        "lineage_full_check_performed": lineage.get("lineage_full_check_performed") is True,
        "official_report_release_allowed": lineage.get("official_report_release_allowed") is True,
        "delivery_allowed": lineage.get("delivery_allowed") is True,
        "github_upload_allowed": lineage.get("github_upload_allowed") is True,
        "blocker_ids": ["LINEAGE_FULL_CHECK_NOT_COMPLETE"],
    }


def final_readiness_gates(stage_summary: dict[str, Any], raw_gate: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
    s18 = read_json(S18_STAGE_REVIEW_PATH)
    stage_gate = s18.get("stage_gate", {})
    if not isinstance(stage_gate, dict):
        raise RuntimeError("S18 stage_gate must be an object")
    return {
        "stage_reviews_all_passed": stage_summary["stage_review_count"] == stage_summary["stage_review_pass_count"] == 18,
        "stage_review_open_finding_count": stage_summary["open_stage_review_finding_count"],
        "raw_alignment_complete": raw_gate["raw_alignment_complete"],
        "lineage_full_check_complete": lineage["lineage_full_check_complete"],
        "official_report_release_allowed": lineage["official_report_release_allowed"],
        "github_main_upload_allowed": False,
        "app_reinstall_allowed": False,
        "delivery_allowed": False,
        "business_execution_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": stage_gate.get("current_data_quality_grade", "Q4"),
        "current_report_grade": stage_gate.get("current_report_grade", "D"),
        "pending_reconciliation_count": stage_gate.get("pending_reconciliation_count"),
        "html_audit_fail_count": stage_gate.get("html_audit_fail_count"),
        "public_safe_evidence_only": True,
    }


def public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "credential_or_secret_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "field_or_header_plaintext_committed": False,
        "business_values_committed": False,
        "formal_report_committed": False,
        "github_upload_artifact_committed": False,
        "app_reinstall_artifact_committed": False,
        "production_restore_artifact_committed": False,
        "external_service_artifact_committed": False,
        "live_connector_artifact_committed": False,
    }


def build_go_no_go(gates: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "v014_stage1_18_overall_go_no_go_report",
        "project_id": "KMFA",
        "version": "0.1.4",
        "phase_id": "V014_STAGE1_18_OVERALL_REVIEW",
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": (
            "Stage review evidence is locally complete, but raw alignment, lineage completeness, "
            "official report release, GitHub main upload, and app reinstall remain blocked."
        ),
        "delivery_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_complete": gates["lineage_full_check_complete"],
        "raw_alignment_complete": gates["raw_alignment_complete"],
        "official_report_release_allowed": gates["official_report_release_allowed"],
        "pending_reconciliation_count": gates["pending_reconciliation_count"],
        "blocker_ids": [
            "RAW_ALIGNMENT_NOT_PROVEN_COMPLETE",
            "RAW_PACKAGE_HASH_OR_SIZE_MISMATCH",
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "S09_PENDING_RECONCILIATION_12",
            "GITHUB_UPLOAD_BLOCKED_BY_RAW_ALIGNMENT_AND_LINEAGE",
            "APP_REINSTALL_BLOCKED_UNTIL_GITHUB_PARITY_AND_RELEASE_GATE",
        ],
        "resolved_blocker_ids": [
            "S18_STAGE_REVIEW_PENDING",
            "V014_STAGE1_18_OVERALL_REVIEW_PENDING",
        ],
        "next_required_phase": NEXT_PHASE,
    }


def _markdown_report(manifest: dict[str, Any]) -> str:
    gates = manifest["final_readiness_gates"]
    stage = manifest["stage_review_summary"]
    raw = manifest["raw_alignment_gate"]
    return f"""# KMFA v0.1.4 Stage 1-18 Overall Review

Status: {manifest["status"]}

## Scope
- Phase: {manifest["phase_id"]}
- Review scope: {manifest["review_scope"]}
- Public-safe only: true
- Raw/private inbox access in this phase: false
- GitHub upload: false
- App reinstall: false

## Result
- Stage reviews passed: {stage["stage_review_pass_count"]}/{stage["stage_review_count"]}
- Implementation coverage: {stage["total_phase_count"]} phases / {stage["total_task_count"]} tasks
- Open stage review findings: {stage["open_stage_review_finding_count"]}
- Current Go/No-Go: {gates["current_go_no_go"]}
- Current report grade: {gates["current_report_grade"]}
- Pending reconciliation count: {gates["pending_reconciliation_count"]}

## Blocking Gates
- Raw alignment complete: {str(raw["raw_alignment_complete"]).lower()}
- Private package match complete: false
- Lineage full check complete: {str(gates["lineage_full_check_complete"]).lower()}
- Official report release allowed: {str(gates["official_report_release_allowed"]).lower()}
- GitHub main upload allowed: {str(gates["github_main_upload_allowed"]).lower()}
- App reinstall allowed: {str(gates["app_reinstall_allowed"]).lower()}

## Next
{manifest["next_required_step"]}
"""


def _go_no_go_record(go_no_go: dict[str, Any]) -> str:
    blockers = "\n".join(f"- {item}" for item in go_no_go["blocker_ids"])
    resolved = "\n".join(f"- {item}" for item in go_no_go["resolved_blocker_ids"])
    return f"""# KMFA v0.1.4 Stage 1-18 Go/No-Go

Decision: {go_no_go["decision"]}

Reason: {go_no_go["decision_reason"]}

## Active Blockers
{blockers}

## Resolved In This Phase
{resolved}
"""


def _risk_register() -> str:
    return """# KMFA v0.1.4 Stage 1-18 Risk Register

| Risk | Status | Control |
| --- | --- | --- |
| Raw alignment not proven complete | open | Keep upload, app reinstall, formal report, and business execution blocked |
| Lineage full check not complete | open | Require separate lineage completion phase and validator pass |
| Pending reconciliation remains | open | Require mismatch resolution/rerun evidence before delivery |
| Public evidence accidentally exposes private source detail | controlled | This phase records only public-safe booleans, counts, and blocker ids |
"""


def _rollback_plan() -> str:
    return """# KMFA v0.1.4 Stage 1-18 Rollback Plan

This phase only writes public-safe review artifacts, validators, tests, and governance records.

Rollback path:
1. Revert the local commit for this phase.
2. Remove the generated `V014_STAGE1_18_OVERALL_REVIEW` public evidence directory if needed.
3. Re-run v0.1.4 Stage 18 review validator to return to the previous local state.

No raw/private source files are read, modified, moved, deleted, or committed by this phase.
"""


def _test_results_placeholder() -> str:
    return """# KMFA v0.1.4 Stage 1-18 Test Results

Initial status: generated, pending final validation run.

Required validation:
- v0.1.4 Stage 1-18 overall review validator
- focused unittest
- governance validators
- raw/private public evidence scan
- secret scan
"""


def generate(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    baseline = load_taskpack_baseline()
    stage_summary = load_stage_review_summary()
    raw_gate = raw_alignment_gate()
    lineage = lineage_gate()
    gates = final_readiness_gates(stage_summary, raw_gate, lineage)
    go_no_go = build_go_no_go(gates)
    status = "overall_review_completed_local_only_no_go_upload_app_reinstall_blocked"

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S01-S18",
        "phase_id": "V014_STAGE1_18_OVERALL_REVIEW",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "review_scope": REVIEW_SCOPE,
        "status": status,
        "generated_at": generated_at,
        "taskpack_baseline": baseline,
        "stage_review_summary": stage_summary,
        "raw_alignment_gate": raw_gate,
        "lineage_gate": lineage,
        "final_readiness_gates": gates,
        "overall_go_no_go": go_no_go,
        "public_repo_safety": public_repo_safety(),
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_blocked_by_raw_alignment_and_lineage",
        "github_upload_deferred": True,
        "app_reinstall_performed": False,
        "app_reinstall_status": "not_reinstalled_blocked_until_github_parity_and_release_gate",
        "formal_report_release_performed": False,
        "business_execution_performed": False,
        "raw_inbox_access_performed_by_this_phase": False,
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
        ],
        "validator_refs": [
            "KMFA/tools/check_v014_stage1_18_overall_review.py",
            "KMFA/tests/test_v014_stage1_18_overall_review.py",
        ],
        "final_validation_summary": {
            "status": "pending_final_validation",
            "all_required_validators_passed": False,
            "last_validated_at": None,
            "validation_event_id": None,
        },
    }

    write_json(MANIFEST_PATH, manifest)
    write_json(GO_NO_GO_PATH, go_no_go)
    write_json(METADATA_MANIFEST_PATH, manifest)
    write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    write_text(REPORT_PATH, _markdown_report(manifest))
    write_text(GO_NO_GO_RECORD_PATH, _go_no_go_record(go_no_go))
    write_text(TEST_RESULTS_PATH, _test_results_placeholder())
    write_text(RISK_REGISTER_PATH, _risk_register())
    write_text(ROLLBACK_PATH, _rollback_plan())
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "Generated KMFA v0.1.4 Stage 1-18 overall review evidence "
        f"(stage_reviews={manifest['stage_review_summary']['stage_review_pass_count']}/18, "
        f"go_no_go={manifest['overall_go_no_go']['decision']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"app_reinstall={str(manifest['app_reinstall_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
