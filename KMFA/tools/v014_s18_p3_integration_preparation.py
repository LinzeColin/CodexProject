#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S18-P3 integration-preparation evidence.

This phase prepares future read-only connector, OpMe light-entry, and backlog
evidence. It does not access the raw/private inbox, call live connectors, run
Stage 18 review, upload to GitHub, release formal reports, restore production,
reinstall apps, or execute business actions.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s18_p2_full_regression_acceptance import (  # noqa: E402
    validate_v014_s18_p2_full_regression_acceptance,
)
from KMFA.tools.integration_preparation import (  # noqa: E402
    POLICY_VERSION as LEGACY_S18_P3_POLICY_VERSION,
    REQUIRED_BACKLOG_IDS,
    REQUIRED_CONNECTOR_IDS,
    REQUIRED_OPME_ENTRY_SURFACES,
    build_default_integration_preparation_suite,
    validate_integration_preparation_artifacts,
)


TASK_ID = "KMFA-V014-S18-P3-INTEGRATION-PREPARATION-20260705"
ACCEPTANCE_ID = "ACC-V014-S18-P3-INTEGRATION-PREPARATION"
SCHEMA_VERSION = "kmfa.v014_s18_p3_integration_preparation.v1"
PHASE_SCOPE = "v014_s18_p3_integration_preparation_only"
POLICY_LOCK_VERSION = "LOCK-KMFA-V014-S18P3-INTEGRATION-PREPARATION-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S18P3-INTEGRATION-PREPARATION-001"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S18_P3_INTEGRATION_PREPARATION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
METADATA_DIR = Path("KMFA/metadata/integration")

MANIFEST_PATH = MACHINE_DIR / "integration_preparation_manifest.json"
CONNECTOR_PLAN_PATH = MACHINE_DIR / "read_only_connector_plan.jsonl"
OPME_PLAN_PATH = MACHINE_DIR / "opme_entry_integration_plan.json"
BACKLOG_PATH = MACHINE_DIR / "next_stage_backlog.jsonl"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"

METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s18_p3_integration_preparation_manifest.json"
METADATA_CONNECTOR_PLAN_PATH = METADATA_DIR / "v014_s18_p3_read_only_connector_plan.jsonl"
METADATA_OPME_PLAN_PATH = METADATA_DIR / "v014_s18_p3_opme_entry_integration_plan.json"
METADATA_BACKLOG_PATH = METADATA_DIR / "v014_s18_p3_next_stage_backlog.jsonl"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_s18_p3_go_no_go_report.json"

REPORT_PATH = HUMAN_DIR / "integration_preparation_report.md"
CONNECTOR_PLAN_RECORD_PATH = HUMAN_DIR / "read_only_connector_plan.md"
OPME_PLAN_RECORD_PATH = HUMAN_DIR / "opme_entry_integration_plan.md"
BACKLOG_RECORD_PATH = HUMAN_DIR / "next_stage_backlog.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")

NEXT_PHASE = "S18_STAGE_REVIEW"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 Stage 18 overall review as a separate run. Do not perform GitHub upload, "
    "lineage full-check completion, formal report release, production restore, app reinstall, live connector calls, "
    "external services, raw inbox access, OpMe deep coupling, or business execution in S18-P3."
)

RAW_ACTION_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_s18_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s18_p2_full_regression_acceptance()
    if result.get("stage_id") != "S18" or result.get("phase_id") != "S18-P2":
        raise RuntimeError("S18-P3 requires validated v0.1.4 S18-P2 evidence")
    if result.get("next_phase") != "S18-P3":
        raise RuntimeError("S18-P2 dependency must route to S18-P3")
    progress = result.get("stage18_phase_progress", {})
    if progress.get("s18_p1_performed") is not True or progress.get("s18_p2_performed") is not True:
        raise RuntimeError("S18-P3 requires S18-P1 and S18-P2 completed")
    if progress.get("s18_p3_performed") is not False:
        raise RuntimeError("S18-P2 dependency must not already include S18-P3")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 GitHub upload must remain deferred")
    return result


def validate_historical_s18_p3_public_safe_baseline() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
    list[dict[str, Any]],
]:
    artifacts = build_default_integration_preparation_suite(generated_at="2026-07-01T23:59:59+10:00")
    validate_integration_preparation_artifacts(*artifacts)
    return artifacts


def load_v14_taskpack_baseline() -> dict[str, Any]:
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    for token in ("后续接入准备", "红圈、金蝶、WPS自动接入后续只读方案", "OpMe入口集成方案", "下一阶段Backlog"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S18-P3 marker {token}")
    for token in ("独立开发，后续接入OpMe", "S18 时", "原始数据", "FAIL = 0"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S18-P3 marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s18_p3_requirements": True,
        "taskpack_keeps_opme_as_future_entry": True,
        "taskpack_keeps_raw_boundary_gate": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_boundary() -> dict[str, bool]:
    return {key: False for key in RAW_ACTION_KEYS}


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "private_tabular_material_committed": False,
        "source_document_committed": False,
        "field_text_committed": False,
        "true_money_committed": False,
        "true_customer_project_committed": False,
        "true_account_committed": False,
        "credential_committed": False,
        "private_document_committed": False,
        "raw_file_committed": False,
        "raw_file_name_committed": False,
        "raw_file_hash_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "s18_p2_dependency_validated": True,
        "legacy_s18_p3_public_safe_baseline_validated": True,
        "read_only_connector_plan_created": True,
        "opme_entry_plan_created": True,
        "next_stage_backlog_created": True,
        "stage18_review_next_required": True,
        "metadata_only": True,
        "public_safe_proposal_only": True,
        "no_live_connector_called": True,
        "stage18_review_allowed_in_this_phase": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "external_connector_called": False,
        "external_connector_allowed": False,
        "live_connector_called": False,
        "source_mutation_allowed": False,
        "credential_required_now": False,
        "business_execution_allowed": False,
        "production_restore_allowed": False,
        "app_reinstall_allowed": False,
        "official_report_release_allowed": False,
        "business_decision_basis_allowed": False,
        "lineage_full_check_complete": False,
        "delivery_allowed": False,
        "raw_business_data_used": False,
        "s09_pending_reconciliation_count": 12,
        "maximum_report_grade": "D",
        "release_block_reason": "stage18_review_lineage_full_check_and_official_report_release_pending",
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s18_p2_dependency_reused": True,
        "legacy_s18_p3_public_safe_baseline_reused": True,
        "s18_p3_integration_preparation_scope_included": True,
        "stage18_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "business_execution_scope_included": False,
        "raw_inbox_access_scope_included": False,
        "production_restore_scope_included": False,
        "external_connector_scope_included": False,
        "live_connector_scope_included": False,
        "app_reinstall_scope_included": False,
        "opme_deep_coupling_scope_included": False,
    }


def _connector_rows(legacy_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in legacy_rows:
        item = dict(row)
        item.update(
            {
                "record_type": "v014_s18_p3_read_only_connector_plan",
                "schema_version": "kmfa.v014_s18_p3_read_only_connector_plan.v1",
                "project_id": "KMFA",
                "version": "0.1.4",
                "stage_id": "S18",
                "phase_id": "S18-P3",
                "stage_phase": "S18-P3",
                "task_id": "S18P3T01",
                "acceptance_id": ACCEPTANCE_ID,
                "generated_at": generated_at,
                "policy_lock_version": POLICY_LOCK_VERSION,
                "legacy_policy_version": LEGACY_S18_P3_POLICY_VERSION,
            }
        )
        rows.append(item)
    return rows


def _opme_plan(legacy_plan: dict[str, Any], generated_at: str) -> dict[str, Any]:
    item = dict(legacy_plan)
    item.update(
        {
            "record_type": "v014_s18_p3_opme_entry_integration_plan",
            "schema_version": "kmfa.v014_s18_p3_opme_entry_integration_plan.v1",
            "project_id": "KMFA",
            "version": "0.1.4",
            "stage_id": "S18",
            "phase_id": "S18-P3",
            "stage_phase": "S18-P3",
            "task_id": "S18P3T02",
            "acceptance_id": ACCEPTANCE_ID,
            "generated_at": generated_at,
            "policy_lock_version": POLICY_LOCK_VERSION,
            "legacy_policy_version": LEGACY_S18_P3_POLICY_VERSION,
        }
    )
    return item


def _backlog_rows(legacy_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in legacy_rows:
        item = dict(row)
        item.update(
            {
                "record_type": "v014_s18_p3_next_stage_backlog_item",
                "schema_version": "kmfa.v014_s18_p3_next_stage_backlog_item.v1",
                "project_id": "KMFA",
                "version": "0.1.4",
                "stage_id": "S18",
                "phase_id": "S18-P3",
                "stage_phase": "S18-P3",
                "task_id": "S18P3T03",
                "acceptance_id": ACCEPTANCE_ID,
                "generated_at": generated_at,
                "policy_lock_version": POLICY_LOCK_VERSION,
                "legacy_policy_version": LEGACY_S18_P3_POLICY_VERSION,
            }
        )
        rows.append(item)
    return rows


def _go_no_go() -> dict[str, Any]:
    return {
        "record_type": "v014_s18_p3_go_no_go_report",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S18",
        "phase_id": "S18-P3",
        "task_id": "S18P3T03",
        "decision": "NO_GO",
        "decision_reason": "S18-P3 is complete but Stage18 review, lineage full check and official report release remain pending",
        "blocker_ids": [
            "STAGE18_REVIEW_PENDING",
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "GITHUB_UPLOAD_DEFERRED_UNTIL_V014_STAGE1_18_COMPLETE",
        ],
        "delivery_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "official_report_release_allowed": False,
        "lineage_full_check_complete": False,
        "s18_p3_pending": False,
        "stage18_review_performed": False,
        "next_required_phase": NEXT_PHASE,
    }


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    s18_p2 = validate_s18_p2_dependency()
    legacy_manifest, legacy_connectors, legacy_opme, legacy_backlog = validate_historical_s18_p3_public_safe_baseline()
    v14_baseline = load_v14_taskpack_baseline()
    connector_plans = _connector_rows(legacy_connectors, generated_at)
    opme_plan = _opme_plan(legacy_opme, generated_at)
    backlog_items = _backlog_rows(legacy_backlog, generated_at)
    go_no_go = _go_no_go()
    summary = {
        "connector_plan_count": len(connector_plans),
        "read_only_connector_count": sum(1 for row in connector_plans if row["integration_mode"] == "read_only_future_connector"),
        "opme_entry_surface_count": len(opme_plan["entry_surfaces"]),
        "backlog_item_count": len(backlog_items),
        "live_connector_call_count": sum(1 for row in connector_plans if row["live_connector_called"]),
        "external_service_call_count": sum(1 for row in connector_plans if row["external_service_called"]),
        "source_mutation_allowed_count": sum(1 for row in connector_plans if row["source_mutation_allowed"]),
        "deep_coupling_allowed": opme_plan["deep_coupling_allowed"],
        "next_required_phase": NEXT_PHASE,
    }
    content_hash = sha256_json(
        {
            "connector_plans": connector_plans,
            "opme_plan": opme_plan,
            "backlog_items": backlog_items,
            "go_no_go": go_no_go,
        }
    )
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s18_p3_integration_preparation_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S18",
        "phase_id": "S18-P3",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S18P3T01", "S18P3T02", "S18P3T03"],
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "branch": git_output(["branch", "--show-current"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_integration_preparation_locked",
        "s18_p2_dependency_validated": True,
        "s18_p2_dependency_ref": "KMFA/stage_artifacts/V014_S18_P2_FULL_REGRESSION_ACCEPTANCE/machine/full_regression_acceptance_manifest.json",
        "historical_s18_p3_public_safe_baseline_validated": True,
        "historical_s18_p3_policy_version": LEGACY_S18_P3_POLICY_VERSION,
        "required_connector_ids": list(REQUIRED_CONNECTOR_IDS),
        "required_opme_entry_surfaces": list(REQUIRED_OPME_ENTRY_SURFACES),
        "required_backlog_ids": list(REQUIRED_BACKLOG_IDS),
        "integration_preparation_summary": summary,
        "stage18_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s18_p1_performed": True,
            "s18_p2_performed": True,
            "s18_p3_performed": True,
            "stage18_review_performed": False,
        },
        "quality_gate": _quality_gate(),
        "phase_boundaries": _phase_boundaries(),
        "raw_data_boundary": _raw_boundary(),
        "public_repo_safety": _public_repo_safety(),
        "v14_taskpack_baseline": v14_baseline,
        "s18_p2_dependency_summary": {
            "dependency_phase": s18_p2["phase_id"],
            "dependency_next_phase": s18_p2["next_phase"],
            "dependency_go_no_go_decision": s18_p2["go_no_go"]["decision"],
            "dependency_github_upload_performed": s18_p2["github_upload"]["github_upload_performed"],
        },
        "legacy_s18_p3_summary": legacy_manifest["summary"],
        "read_only_connector_plans": connector_plans,
        "opme_entry_plan": opme_plan,
        "next_stage_backlog": backlog_items,
        "go_no_go": go_no_go,
        "metadata_outputs": {
            "manifest": METADATA_MANIFEST_PATH.as_posix(),
            "connector_plan": METADATA_CONNECTOR_PLAN_PATH.as_posix(),
            "opme_plan": METADATA_OPME_PLAN_PATH.as_posix(),
            "backlog": METADATA_BACKLOG_PATH.as_posix(),
            "go_no_go": METADATA_GO_NO_GO_PATH.as_posix(),
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "connector_plan": CONNECTOR_PLAN_PATH.as_posix(),
            "opme_plan": OPME_PLAN_PATH.as_posix(),
            "backlog": BACKLOG_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "connector_plan_record": CONNECTOR_PLAN_RECORD_PATH.as_posix(),
            "opme_plan_record": OPME_PLAN_RECORD_PATH.as_posix(),
            "backlog_record": BACKLOG_RECORD_PATH.as_posix(),
            "go_no_go_record": GO_NO_GO_RECORD_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "validation_summary": {
            "py_compile": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "s18_p2_dependency_validator": "PASS",
            "historical_s18_p3_baseline_validator": "PASS",
            "s18_p3_validator": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_suffix_scan": "PENDING_FINAL_VALIDATION",
            "high_signal_secret_scan": "PENDING_FINAL_VALIDATION",
            "public_artifact_boundary_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "github_upload": {
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_ready_next_gate": False,
        },
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
        "content_hash": content_hash,
    }

    write_json(MANIFEST_PATH, manifest)
    write_json(METADATA_MANIFEST_PATH, manifest)
    write_jsonl(CONNECTOR_PLAN_PATH, connector_plans)
    write_jsonl(METADATA_CONNECTOR_PLAN_PATH, connector_plans)
    write_json(OPME_PLAN_PATH, opme_plan)
    write_json(METADATA_OPME_PLAN_PATH, opme_plan)
    write_jsonl(BACKLOG_PATH, backlog_items)
    write_jsonl(METADATA_BACKLOG_PATH, backlog_items)
    write_json(GO_NO_GO_PATH, go_no_go)
    write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_human_artifacts(manifest, connector_plans, opme_plan, backlog_items, go_no_go)
    return manifest


def _write_human_artifacts(
    manifest: dict[str, Any],
    connector_plans: list[dict[str, Any]],
    opme_plan: dict[str, Any],
    backlog_items: list[dict[str, Any]],
    go_no_go: dict[str, Any],
) -> None:
    connector_lines = "\n".join(
        f"- {row['connector_id']}: mode={row['integration_mode']}; live_connector_called={row['live_connector_called']}; "
        f"source_mutation_allowed={row['source_mutation_allowed']}; github_upload_allowed={row['github_upload_allowed']}"
        for row in connector_plans
    )
    backlog_lines = "\n".join(
        f"- {row['backlog_id']}: {row['title']}; status={row['status']}; started={row['started']}"
        for row in backlog_items
    )
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P3 Integration Preparation Report",
                "",
                f"- stage_phase: {manifest['phase_id']}",
                f"- connector_plan_count: {manifest['integration_preparation_summary']['connector_plan_count']}",
                f"- opme_entry_surface_count: {manifest['integration_preparation_summary']['opme_entry_surface_count']}",
                f"- backlog_item_count: {manifest['integration_preparation_summary']['backlog_item_count']}",
                f"- decision: {go_no_go['decision']}",
                f"- next_required_phase: {manifest['next_phase']}",
                "- non_goals: Stage18 review, GitHub upload, live connectors, production restore, app reinstall, formal report release, OpMe deep coupling, and business execution.",
                "",
            ]
        ),
    )
    write_text(CONNECTOR_PLAN_RECORD_PATH, "\n".join(["# S18-P3 Read-Only Connector Plan", "", connector_lines, ""]))
    write_text(
        OPME_PLAN_RECORD_PATH,
        "\n".join(
            [
                "# S18-P3 OpMe Entry Integration Plan",
                "",
                f"- integration_mode: {opme_plan['integration_mode']}",
                f"- coupling_level: {opme_plan['coupling_level']}",
                f"- entry_surfaces: {', '.join(opme_plan['entry_surfaces'])}",
                f"- deep_coupling_allowed: {opme_plan['deep_coupling_allowed']}",
                f"- shared_database_allowed: {opme_plan['shared_database_allowed']}",
                f"- sensitive_data_mixing_allowed: {opme_plan['sensitive_data_mixing_allowed']}",
                "",
            ]
        ),
    )
    write_text(BACKLOG_RECORD_PATH, "\n".join(["# S18-P3 Next-Stage Backlog", "", backlog_lines, ""]))
    write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# S18-P3 Go No-Go Record",
                "",
                f"- decision: {go_no_go['decision']}",
                f"- delivery_allowed: {go_no_go['delivery_allowed']}",
                f"- github_upload_allowed: {go_no_go['github_upload_allowed']}",
                f"- blockers: {', '.join(go_no_go['blocker_ids'])}",
                "",
            ]
        ),
    )
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P3 Integration Preparation Test Results",
                "",
                "- py_compile: pending final validation replay",
                "- focused_unittest: pending final validation replay",
                "- s18_p2_dependency_validator: pending final validation replay",
                "- s18_p3_validator: pending final validation replay",
                "- governance_validation: pending final validation replay",
                "- raw_secret_scan: pending final validation replay",
                "",
            ]
        ),
    )
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# S18-P3 Risk Register",
                "",
                "- ISSUE-S18P3-001: Future connector authorization is not granted in this phase; keep all connector rows proposal-only.",
                "- ISSUE-S18P3-002: OpMe deep coupling would mix responsibility boundaries; keep entry-link-only scope.",
                "- ISSUE-S18P3-003: Stage18 review and upload are separate gates and remain blocked in this phase.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# S18-P3 Rollback Plan",
                "",
                "- Remove S18-P3 generated evidence and metadata files if validation fails.",
                "- Re-run S18-P2 validator before regenerating S18-P3 evidence.",
                "- Keep GitHub upload deferred until v1.4 Stage 1-18 completion and overall review gates pass.",
                "",
            ]
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA v0.1.4 S18-P3 integration preparation evidence.")
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args(argv)
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["integration_preparation_summary"]
    print(
        "PASS: KMFA v0.1.4 S18-P3 integration preparation generated "
        f"(connectors={summary['connector_plan_count']}, "
        f"opme_surfaces={summary['opme_entry_surface_count']}, "
        f"backlog={summary['backlog_item_count']}, "
        "live_connector_called=false, stage18_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
