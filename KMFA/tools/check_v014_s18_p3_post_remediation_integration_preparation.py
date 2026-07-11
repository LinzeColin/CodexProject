#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S18-P3 integration-preparation evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import v014_s18_p3_post_remediation_integration_preparation as phase  # noqa: E402


SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
)


class ValidationError(ValueError):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        capture_output=True,
        check=False,
    )


def _public_paths() -> tuple[Path, ...]:
    return (
        phase.MANIFEST_PATH,
        phase.CONNECTOR_PLAN_PATH,
        phase.OPME_PLAN_PATH,
        phase.BACKLOG_PATH,
        phase.ACCEPTANCE_MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.CONNECTOR_RECORD_PATH,
        phase.OPME_RECORD_PATH,
        phase.BACKLOG_RECORD_PATH,
        phase.GO_NO_GO_RECORD_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_CONNECTOR_PLAN_PATH,
        phase.METADATA_OPME_PLAN_PATH,
        phase.METADATA_BACKLOG_PATH,
        phase.METADATA_ACCEPTANCE_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )


def _check_public_text(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public evidence: {path}", errors)
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8", errors="strict")
    lower = text.lower()
    for token in phase.FORBIDDEN_PUBLIC_TEXT:
        _require(token.lower() not in lower, f"forbidden public token {token!r}: {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like material found in {path}", errors)


def _check_private_evidence(errors: list[str]) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_DIAGNOSTIC_PATH,
        phase.PRIVATE_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"missing private evidence: {path}", errors)
        ignored = _git(["check-ignore", "-q", path.as_posix()])
        _require(ignored.returncode == 0, f"private evidence must be gitignored: {path}", errors)
    if not all(path.is_file() for path in private_paths[:3]):
        return
    raw_helper = (
        phase.s18_p2.s18_p1.s17_review.p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    )
    before = phase._read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = phase._read_json(phase.PRIVATE_RAW_AFTER_PATH)
    prior = phase._read_json(phase.s18_p2.PRIVATE_RAW_AFTER_PATH)
    diagnostic = phase._read_json(phase.PRIVATE_DIAGNOSTIC_PATH)
    normalize = raw_helper._normalize_raw
    current = raw_helper._raw_snapshot("validate_v014_s18_p3_post_remediation_integration_preparation")
    _require(normalize(before) == normalize(after), "private raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior), "private raw snapshot differs from current S18-P2", errors)
    _require(normalize(before) == normalize(current), "private raw snapshot differs from current raw source", errors)
    _require(diagnostic.get("raw_phase_exact") is True, "private raw phase exact flag missing", errors)
    _require(diagnostic.get("raw_cross_phase_exact") is True, "private raw cross-phase exact flag missing", errors)
    _require(diagnostic.get("connector_call_count") == 0, "private connector call count must be zero", errors)
    _require(diagnostic.get("external_service_call_count") == 0, "private external call count must be zero", errors)
    _require(diagnostic.get("credential_material_present") is False, "private credential flag must be false", errors)


def _check_governance_history(errors: list[str]) -> None:
    for path in (
        phase.DEVELOPMENT_EVENTS_PATH,
        phase.STAGE_STATUS_PATH,
        phase.TASK_STATUS_PATH,
    ):
        rows = phase._read_jsonl(path)
        _require(
            sum(row.get("phase_id") == phase.PHASE_ID for row in rows) == 1,
            f"{path} must contain exactly one current S18-P3 row",
            errors,
        )
        _require(
            sum(row.get("phase_id") == phase.s18_p2.PHASE_ID for row in rows) == 1,
            f"{path} must preserve exactly one current S18-P2 row",
            errors,
        )


def _expected_parameters() -> dict[str, str]:
    return {
        "PARAM-KMFA-1813": "3;3;0;0;0;0;0",
        "PARAM-KMFA-1814": "4;false;false;6;0;0",
        "PARAM-KMFA-1815": "5;true;3;9;2;1;true;false;false;false;false;false;Q4;D;NO_GO",
    }


def _check_current_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    current = f'current_phase: "{phase.PHASE_ID}"' in version_matrix
    if current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        for token in (
            phase.PHASE_ID,
            "下一步只能执行 Stage 18 整体复审",
            "不得执行最终整体复审",
            "不得执行 GitHub upload",
        ):
            _require(token in handoff, f"HANDOFF token missing: {token}", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in agents and "Stage 18 整体复审" in agents, "AGENTS scope drift", errors)

    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in trace and phase.ACCEPTANCE_ID in trace, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    for token in (
        phase.FORMULA_ID,
        "connector_plan_count == 3",
        "read_only_connector_count == 3",
        "live_connector_call_count == 0",
        "source_mutation_allowed_count == 0",
        "opme_entry_surface_count == 4",
        "shared_database_allowed == false",
        "backlog_item_count == 6",
        "backlog_started_count == 0",
        "raw_exact == true",
        "stage18_review_performed == false",
        "github_upload_performed == false",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)

    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model profile missing: {path}", errors)
        _require(phase.FORMULA_ID in text, f"model formula missing: {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"model parameter missing: {path}:{parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    for parameter_id, expected in _expected_parameters().items():
        row = parameters.get(parameter_id, {})
        _require(row.get("formula_id") == phase.FORMULA_ID, f"parameter formula drift: {parameter_id}", errors)
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter value drift: {parameter_id}:{field}", errors)
        _require(row.get("status") == "active", f"parameter status drift: {parameter_id}", errors)

    assurance = phase.ASSURANCE_STATUS_PATH.read_text(encoding="utf-8")
    for token in (
        phase.TASK_ID,
        phase.ACCEPTANCE_ID,
        phase.FORMULA_ID,
    ):
        _require(token in assurance, f"assurance token missing: {token}", errors)
    if current:
        for token in (
            f'snapshot_event_time: "{manifest["generated_at"]}"',
            "total_active_parameters: 1433",
            "total_active_formulas: 313",
        ):
            _require(token in assurance, f"current assurance token missing: {token}", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)

    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/README.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/docs/governance/OWNER_STATUS.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/STATUS.md"), phase.PHASE_ID),
        (Path("KMFA/功能清单.md"), "S18-P3 修补后后续接入准备"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def validate_v014_s18_p3_post_remediation_integration_preparation(
    manifest_path: Path = phase.MANIFEST_PATH,
    *,
    require_private_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    _require(manifest_path.is_file(), f"missing manifest: {manifest_path}", errors)
    if errors:
        raise ValidationError("\n".join(errors))

    manifest = phase._read_json(manifest_path)
    metadata_manifest = phase._read_json(phase.METADATA_MANIFEST_PATH)
    connectors = phase._read_jsonl(phase.CONNECTOR_PLAN_PATH)
    metadata_connectors = phase._read_jsonl(phase.METADATA_CONNECTOR_PLAN_PATH)
    opme = phase._read_json(phase.OPME_PLAN_PATH)
    metadata_opme = phase._read_json(phase.METADATA_OPME_PLAN_PATH)
    backlog = phase._read_jsonl(phase.BACKLOG_PATH)
    metadata_backlog = phase._read_jsonl(phase.METADATA_BACKLOG_PATH)
    acceptance = phase._read_json(phase.ACCEPTANCE_MATRIX_PATH)
    metadata_acceptance = phase._read_json(phase.METADATA_ACCEPTANCE_MATRIX_PATH)
    go_no_go = phase._read_json(phase.GO_NO_GO_PATH)
    metadata_go_no_go = phase._read_json(phase.METADATA_GO_NO_GO_PATH)
    dependency = phase._s18_p2_dependency()
    historical = phase._historical_baseline()
    taskpack = phase._taskpack_contract()
    summary = manifest.get("summary", {})

    _require(metadata_manifest == manifest, "metadata manifest mirror mismatch", errors)
    _require(metadata_connectors == connectors, "metadata connector mirror mismatch", errors)
    _require(metadata_opme == opme, "metadata OpMe mirror mismatch", errors)
    _require(metadata_backlog == backlog, "metadata backlog mirror mismatch", errors)
    _require(metadata_acceptance == acceptance, "metadata acceptance mirror mismatch", errors)
    _require(metadata_go_no_go == go_no_go, "metadata Go/No-Go mirror mismatch", errors)

    expected_identity = {
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": phase.ROADMAP_PHASE_ID,
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "decision": phase.DECISION,
        "formula_id": phase.FORMULA_ID,
        "model_registry_key": phase.MODEL_REGISTRY_KEY,
    }
    for key, value in expected_identity.items():
        _require(manifest.get(key) == value, f"manifest {key} mismatch", errors)
    _require(
        manifest.get("schema_version") == "kmfa.v014.s18_p3_post_remediation_integration_preparation_manifest.v1",
        "manifest schema version mismatch",
        errors,
    )
    _require(manifest.get("parameter_ids") == list(phase.PARAMETER_IDS), "parameter id mismatch", errors)
    _require(manifest.get("branch") == "codex/kmfa", "branch identity mismatch", errors)
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("git_head", "")))), "git_head format mismatch", errors)

    _require(manifest.get("s18_p2_dependency") == dependency, "current S18-P2 dependency mismatch", errors)
    _require(dependency.get("phase_id") == phase.s18_p2.PHASE_ID, "dependency phase mismatch", errors)
    _require(dependency.get("decision") == "NO_GO", "dependency decision mismatch", errors)
    _require(
        manifest.get("historical_s18_p3_structural_baseline_validated") is True,
        "historical structural baseline flag missing",
        errors,
    )
    _require(
        manifest.get("historical_s18_p3_dynamic_state_authoritative") is False,
        "historical dynamic state must not be authoritative",
        errors,
    )
    _require(manifest.get("historical_s18_p3_baseline") == historical, "historical structural summary mismatch", errors)
    _require(manifest.get("taskpack_contract") == taskpack, "taskpack contract mismatch", errors)

    _require(manifest.get("required_connector_ids") == list(phase.REQUIRED_CONNECTOR_IDS), "connector id registry mismatch", errors)
    _require(
        manifest.get("required_opme_entry_surfaces") == list(phase.REQUIRED_OPME_ENTRY_SURFACES),
        "OpMe surface registry mismatch",
        errors,
    )
    _require(
        manifest.get("required_opme_exchange_refs") == list(phase.REQUIRED_OPME_EXCHANGE_REFS),
        "OpMe exchange registry mismatch",
        errors,
    )
    _require(manifest.get("required_backlog_ids") == list(phase.REQUIRED_BACKLOG_IDS), "backlog registry mismatch", errors)
    _require(
        manifest.get("completion_gate_sequence") == list(phase.COMPLETION_GATE_SEQUENCE),
        "completion gate sequence mismatch",
        errors,
    )

    expected_summary = {
        "taskpack_contract_validated": True,
        "s18_p2_dependency_validated": True,
        "historical_s18_p3_structural_baseline_validated": True,
        "connector_plan_count": 3,
        "read_only_connector_count": 3,
        "opme_entry_surface_count": 4,
        "backlog_item_count": 6,
        "live_connector_call_count": 0,
        "external_service_call_count": 0,
        "source_mutation_allowed_count": 0,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "raw_business_content_used_for_integration_plan": False,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s18_p1_performed": True,
        "s18_p2_performed": True,
        "s18_p3_performed": True,
        "stage18_review_performed": False,
        "final_overall_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
    }
    for key, value in expected_summary.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)

    _require([row.get("connector_id") for row in connectors] == list(phase.REQUIRED_CONNECTOR_IDS), "connector order mismatch", errors)
    for row in connectors:
        connector_id = row.get("connector_id")
        _require(row.get("phase_id") == phase.PHASE_ID, f"{connector_id} phase mismatch", errors)
        _require(row.get("task_id") == "S18P3T01", f"{connector_id} task mismatch", errors)
        _require(row.get("integration_mode") == "read_only_future_connector", f"{connector_id} mode mismatch", errors)
        _require(row.get("lifecycle_state") == "proposal_only_not_authorized", f"{connector_id} lifecycle mismatch", errors)
        _require(row.get("authorization_state") == "not_requested_in_this_phase", f"{connector_id} authorization mismatch", errors)
        _require(row.get("connection_state") == "not_connected", f"{connector_id} connection mismatch", errors)
        for key in (
            "owner_authorization_required",
            "private_runtime_only",
            "hash_manifest_required",
            "schema_contract_required",
            "idempotency_key_required",
            "rollback_required",
        ):
            _require(row.get(key) is True, f"{connector_id}.{key} must be true", errors)
        for key in (
            "polling_enabled",
            "source_mutation_allowed",
            "writeback_allowed",
            "auto_write_allowed",
            "credential_required_now",
            "credential_material_present",
            "live_connector_called",
            "external_service_called",
            "raw_business_data_used",
            "raw_business_data_committed",
            "field_plaintext_committed",
            "github_upload_allowed",
            "business_execution_allowed",
        ):
            _require(row.get(key) is False, f"{connector_id}.{key} must be false", errors)

    _require(opme.get("phase_id") == phase.PHASE_ID, "OpMe phase mismatch", errors)
    _require(opme.get("task_id") == "S18P3T02", "OpMe task mismatch", errors)
    _require(opme.get("integration_mode") == "entry_link_and_status_index_only", "OpMe mode mismatch", errors)
    _require(opme.get("coupling_level") == "light_entry_only", "OpMe coupling mismatch", errors)
    _require(tuple(opme.get("entry_surfaces", ())) == phase.REQUIRED_OPME_ENTRY_SURFACES, "OpMe surfaces mismatch", errors)
    _require(tuple(opme.get("allowed_exchange_refs", ())) == phase.REQUIRED_OPME_EXCHANGE_REFS, "OpMe exchanges mismatch", errors)
    for key in (
        "deep_coupling_allowed",
        "shared_database_allowed",
        "shared_runtime_logic_allowed",
        "sensitive_data_mixing_allowed",
        "opme_controls_kmfa_business_logic",
        "kmfa_controls_opme_service_logic",
        "raw_business_data_exposed",
        "field_plaintext_exposed",
        "credential_material_present",
        "external_service_called",
        "github_upload_allowed",
        "business_execution_allowed",
    ):
        _require(opme.get(key) is False, f"opme.{key} must be false", errors)

    _require([row.get("backlog_id") for row in backlog] == list(phase.REQUIRED_BACKLOG_IDS), "backlog order mismatch", errors)
    _require([row.get("priority") for row in backlog] == list(range(1, 7)), "backlog priority mismatch", errors)
    for row in backlog:
        backlog_id = row.get("backlog_id")
        _require(row.get("phase_id") == phase.PHASE_ID, f"{backlog_id} phase mismatch", errors)
        _require(row.get("task_id") == "S18P3T03", f"{backlog_id} task mismatch", errors)
        _require(row.get("status") == "backlog_proposed_not_started", f"{backlog_id} status mismatch", errors)
        for key in (
            "started",
            "external_connector_allowed",
            "persistent_write_allowed",
            "business_execution_allowed",
            "github_upload_allowed",
            "app_reinstall_allowed",
            "raw_business_data_required_in_public_repo",
        ):
            _require(row.get(key) is False, f"{backlog_id}.{key} must be false", errors)

    _require(go_no_go == manifest.get("go_no_go"), "manifest Go/No-Go mismatch", errors)
    _require(go_no_go.get("decision") == "NO_GO", "Go/No-Go decision mismatch", errors)
    _require(go_no_go.get("maximum_report_grade") == "D", "Go/No-Go report grade mismatch", errors)
    for blocker in (
        "LINEAGE_FULL_CHECK_NOT_COMPLETE",
        "OPEN_RECONCILIATION_REMAINS",
        "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
        "STAGE18_REVIEW_PENDING",
        "FINAL_OVERALL_REVIEW_PENDING",
        "GITHUB_MAIN_UPLOAD_DEFERRED",
        "APP_REINSTALL_DEFERRED",
    ):
        _require(blocker in go_no_go.get("blocker_ids", []), f"missing blocker {blocker}", errors)
    _require("S18_P3_PENDING" not in go_no_go.get("blocker_ids", []), "S18_P3_PENDING must be closed", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_performed"):
            _require(value is False, f"go_no_go.{key} must be false", errors)

    expected_phase_boundaries = phase._phase_boundaries()
    _require(manifest.get("phase_boundaries") == expected_phase_boundaries, "phase boundary mismatch", errors)
    _require(manifest.get("public_repo_safety") == phase._public_repo_safety(), "public repo safety mismatch", errors)
    _require(acceptance == manifest.get("acceptance_matrix"), "manifest acceptance matrix mismatch", errors)
    _require(acceptance.get("check_count", 0) >= 24, "acceptance matrix too narrow", errors)
    _require(acceptance.get("check_fail_count") == 0, "acceptance matrix contains failures", errors)
    _require(
        acceptance.get("check_pass_count") == acceptance.get("check_count"),
        "acceptance pass count mismatch",
        errors,
    )

    bundle = {"summary": summary, "connectors": connectors, "opme": opme, "backlog": backlog, "go_no_go": go_no_go}
    try:
        phase.validate_integration_bundle(bundle)
    except ValueError as exc:
        errors.append(f"integration bundle invalid: {exc}")
    _require(manifest.get("content_hash") == phase._sha256_json(bundle), "content hash mismatch", errors)
    _require(manifest.get("next_phase") == "S18_STAGE_REVIEW", "next phase mismatch", errors)

    validation = manifest.get("validation_summary", {})
    if require_final_evidence:
        _require(validation.get("final_validation_recorded") is True, "final validation flag missing", errors)
        _require(validation.get("focused_tests") == "PASS", "focused tests not final", errors)
        _require(validation.get("strict_validator") == "PASS", "strict validator not final", errors)
        _require(validation.get("governance_and_safety_scans") == "PASS", "safety scans not final", errors)
    if require_private_evidence:
        _check_private_evidence(errors)

    for path in _public_paths():
        _check_public_text(path, errors)
    _check_governance_history(errors)
    _check_current_governance(manifest, errors)

    required_human_phrases = {
        phase.REPORT_PATH: ("后续接入准备", "下一步只能单独执行 Stage 18 整体复审"),
        phase.CONNECTOR_RECORD_PATH: ("后续只读连接器方案", "写回与源修改均关闭"),
        phase.OPME_RECORD_PATH: ("OpMe 轻入口方案", "不共享数据库"),
        phase.BACKLOG_RECORD_PATH: ("下一阶段 Backlog", "状态为未启动"),
        phase.GO_NO_GO_RECORD_PATH: ("决策：NO_GO", "全部不允许"),
    }
    for path, phrases in required_human_phrases.items():
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                _require(phrase in text, f"missing Chinese human evidence phrase {phrase!r}: {path}", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate current KMFA S18-P3 integration-preparation evidence")
    parser.add_argument("--manifest", type=Path, default=phase.MANIFEST_PATH)
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args(argv)
    manifest = validate_v014_s18_p3_post_remediation_integration_preparation(
        args.manifest,
        require_private_evidence=args.require_private_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S18-P3 strict PASS: "
        f"connectors={summary['connector_plan_count']} opme={summary['opme_entry_surface_count']} "
        f"backlog={summary['backlog_item_count']} raw={summary['raw_snapshot_exact_match']} "
        f"stage18_review={summary['stage18_review_performed']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
