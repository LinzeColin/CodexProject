#!/usr/bin/env python3
"""Build the fail-closed STAGE-039 whole-stage review report."""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
DELIVERY_CHECKER_PATH = PROJECT_ROOT / "scripts" / "check_retry_dead_letter_delivery.py"
SCENARIO_CHECKER_PATH = PROJECT_ROOT / "scripts" / "check_retry_dead_letter_scenarios.py"
GOVERNANCE_VALIDATOR_PATH = PURSUE_ROOT / "validate_stage005_governance_regression.py"
YAML_PARSER_PATH = PROJECT_ROOT / "scripts" / "check_worker_queue_delivery.py"
REVIEW_ARTIFACT_PATH = PURSUE_ROOT / "STAGE039_STAGE_REVIEW.md"
BATCH_LOCK_PATH = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP_PATH = PROJECT_ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS_PATH = PROJECT_ROOT / "docs" / "governance" / "events.jsonl"
MODEL_REGISTRY_PATH = PROJECT_ROOT / "docs" / "governance" / "model_registry.yaml"
FORMULA_REGISTRY_PATH = PROJECT_ROOT / "docs" / "governance" / "formula_registry.yaml"
PARAMETER_REGISTRY_PATH = PROJECT_ROOT / "docs" / "governance" / "parameter_registry.csv"
MODEL_SPEC_PATH = PROJECT_ROOT / "docs" / "governance" / "MODEL_SPEC.md"
PROJECT_FACTS_PATH = PROJECT_ROOT / "docs" / "governance" / "project.yaml"

REPORT_SCHEMA_VERSION = "ids.stage039.retry_dead_letter.stage_review.v1"
TASK_ID = "IDS-V0_1-STAGE039-REVIEW"
ACCEPTANCE_ID = "ACC-STAGE-039"
REVIEW_STATUS = "completed_reviewed_local"
REVIEW_RESULT = "PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED"
REVIEW_GATE = "IDS-STAGE039-REVIEW-GATE"
NEXT_GATE = "IDS-STAGE040-P1-GATE"

REVIEW_SOURCE_PATHS = {
    "entry_contract": PURSUE_ROOT / "STAGE039_ENTRY_CONTRACT.md",
    "phase1_evidence": PURSUE_ROOT / "STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
    "phase2_evidence": PURSUE_ROOT / "STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md",
    "phase3_evidence": PURSUE_ROOT / "STAGE039_PHASE3_SCENARIO_VALIDATION.md",
    "phase4_evidence": PURSUE_ROOT / "STAGE039_PHASE4_CLOSEOUT.md",
    "review_artifact": REVIEW_ARTIFACT_PATH,
    "phase1_contract": PURSUE_ROOT / "retry_dead_letter" / "stage039_retry_dead_letter_policy_contract.json",
    "phase2_contract": PURSUE_ROOT / "retry_dead_letter" / "stage039_retry_dead_letter_runtime_contract.json",
    "phase3_contract": PURSUE_ROOT / "retry_dead_letter" / "stage039_retry_dead_letter_scenarios.json",
    "phase4_contract": PURSUE_ROOT / "retry_dead_letter" / "stage039_retry_dead_letter_delivery_contract.json",
    "phase1_checker": PROJECT_ROOT / "scripts" / "check_retry_dead_letter_policy.py",
    "phase2_checker": PROJECT_ROOT / "scripts" / "check_retry_dead_letter_runtime.py",
    "phase3_checker": SCENARIO_CHECKER_PATH,
    "phase4_checker": DELIVERY_CHECKER_PATH,
    "review_checker": Path(__file__).resolve(),
    "phase1_test": PURSUE_ROOT / "tests" / "test_stage039_retry_dead_letter_policy.py",
    "phase2_test": PURSUE_ROOT / "tests" / "test_stage039_retry_dead_letter_runtime.py",
    "phase3_test": PURSUE_ROOT / "tests" / "test_stage039_retry_dead_letter_scenarios.py",
    "phase4_test": PURSUE_ROOT / "tests" / "test_stage039_retry_dead_letter_delivery.py",
    "review_test": PURSUE_ROOT / "tests" / "test_stage039_retry_dead_letter_review.py",
    "stage004_compatibility_validator": PURSUE_ROOT
    / "validate_stage004_legacy_name_scan.py",
    "stage004_compatibility_test": PURSUE_ROOT
    / "tests"
    / "test_stage004_legacy_name_scan.py",
    "model_registry": MODEL_REGISTRY_PATH,
    "formula_registry": FORMULA_REGISTRY_PATH,
    "parameter_registry": PARAMETER_REGISTRY_PATH,
    "model_spec": MODEL_SPEC_PATH,
    "project_facts": PROJECT_FACTS_PATH,
    "batch_lock": BATCH_LOCK_PATH,
    "roadmap": ROADMAP_PATH,
    "events": EVENTS_PATH,
    "handoff": PROJECT_ROOT / "docs" / "HANDOFF.md",
    "governance_validator": GOVERNANCE_VALIDATOR_PATH,
}

_DELIVERY_MODULE: Any = None
_SCENARIO_MODULE: Any = None
_YAML_MODULE: Any = None


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _delivery_module() -> Any:
    global _DELIVERY_MODULE
    if _DELIVERY_MODULE is None:
        _DELIVERY_MODULE = _load_module(
            DELIVERY_CHECKER_PATH, "stage039_delivery_for_review"
        )
    return _DELIVERY_MODULE


def _scenario_module() -> Any:
    global _SCENARIO_MODULE
    if _SCENARIO_MODULE is None:
        _SCENARIO_MODULE = _load_module(
            SCENARIO_CHECKER_PATH, "stage039_scenarios_for_review"
        )
    return _SCENARIO_MODULE


def _yaml_module() -> Any:
    global _YAML_MODULE
    if _YAML_MODULE is None:
        _YAML_MODULE = _load_module(YAML_PARSER_PATH, "stage039_review_yaml_parser")
    return _YAML_MODULE


def _parse_yaml_text(text: str) -> dict[str, Any]:
    value = _yaml_module()._parse_yaml_text(text)
    return value if isinstance(value, dict) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_relative(path: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return None


def _git_path_check(path: Path, arguments: list[str]) -> bool:
    relative = _git_relative(path)
    if relative is None:
        return False
    try:
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *arguments, "--", relative],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _git_tracked(path: Path) -> bool:
    return _git_path_check(path, ["ls-files", "--error-unmatch"])


def _git_index_matches(path: Path) -> bool:
    return _git_tracked(path) and _git_path_check(path, ["diff", "--quiet"])


def _review_source_binding() -> dict[str, Any]:
    tracked: dict[str, bool] = {}
    index_matches: dict[str, bool] = {}
    observed: dict[str, Optional[str]] = {}
    for name, path in REVIEW_SOURCE_PATHS.items():
        is_file = path.is_file()
        tracked[name] = is_file and _git_tracked(path)
        index_matches[name] = tracked[name] and _git_index_matches(path)
        observed[name] = _sha256_file(path) if is_file else None
    return {
        "all_sources_git_tracked": bool(tracked) and all(tracked.values()),
        "all_sources_match_git_index": bool(index_matches)
        and all(index_matches.values()),
        "git_tracked_sources": tracked,
        "git_index_sources": index_matches,
        "observed_source_sha256": observed,
    }


def _find_by_id(items: Any, key: str, identifier: str) -> dict[str, Any]:
    if not isinstance(items, list):
        return {}
    return next(
        (
            item
            for item in items
            if isinstance(item, dict) and item.get(key) == identifier
        ),
        {},
    )


def _registry_evidence() -> tuple[dict[str, int], dict[str, bool]]:
    try:
        models_doc = _parse_yaml_text(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
        formulas_doc = _parse_yaml_text(
            FORMULA_REGISTRY_PATH.read_text(encoding="utf-8")
        )
        project_doc = _parse_yaml_text(PROJECT_FACTS_PATH.read_text(encoding="utf-8"))
        with PARAMETER_REGISTRY_PATH.open(encoding="utf-8", newline="") as handle:
            parameters = list(csv.DictReader(handle))
        model_spec = MODEL_SPEC_PATH.read_text(encoding="utf-8")
    except (OSError, csv.Error):
        return {}, {"registry_files_parse": False}

    models = models_doc.get("models")
    models = models if isinstance(models, list) else []
    assumptions = models_doc.get("assumptions")
    assumptions = assumptions if isinstance(assumptions, list) else []
    formulas = formulas_doc.get("formulas")
    formulas = formulas if isinstance(formulas, list) else []
    stage_parameters = [
        row
        for row in parameters
        if row.get("parameter_id") in {f"PARAM-{number:03d}" for number in range(50, 56)}
    ]

    mod008 = _find_by_id(models, "model_id", "MOD-008")
    asm004 = _find_by_id(assumptions, "assumption_id", "ASM-004")
    form008 = _find_by_id(formulas, "formula_id", "FORM-008")
    project_mod008 = _find_by_id(project_doc.get("models"), "model_id", "MOD-008")
    project_form008 = _find_by_id(
        project_doc.get("formulas"), "formula_id", "FORM-008"
    )
    project_feature = _find_by_id(
        project_doc.get("features"), "feature_id", "FEAT-OPME-006"
    )
    project_parameters = [
        item
        for item in project_doc.get("parameters", [])
        if isinstance(item, dict)
        and item.get("parameter_id")
        in {f"PARAM-{number:03d}" for number in range(50, 56)}
    ]

    counts = {
        "model_count": len(models),
        "formula_count": len(formulas),
        "parameter_count": len(parameters),
        "active_model_count": sum(item.get("status") == "active" for item in models),
        "active_formula_count": sum(
            item.get("status") == "active" for item in formulas
        ),
        "active_parameter_count": sum(
            row.get("status") == "active" for row in parameters
        ),
    }
    checks = {
        "registry_files_parse": True,
        "planned_registry_statuses_exact": (
            mod008.get("status") == "planned"
            and form008.get("status") == "planned"
            and len(stage_parameters) == 6
            and all(row.get("status") == "planned" for row in stage_parameters)
        ),
        "proposed_registry_fact_levels_exact": (
            asm004.get("fact_level") == "PROPOSED"
            and mod008.get("fact_level") == "PROPOSED"
            and all(row.get("fact_level") == "PROPOSED" for row in stage_parameters)
        ),
        "production_calibration_task_links_exact": (
            asm004.get("unknown_task_ids") == ["TASK-OPME-B-001"]
            and form008.get("open_task_ids") == ["TASK-OPME-B-001"]
            and all(
                row.get("unknown_task_ids") == "TASK-OPME-B-001"
                for row in stage_parameters
            )
        ),
        "registry_total_counts_exact": (
            counts["model_count"] >= 8
            and counts["formula_count"] >= 8
            and counts["parameter_count"] >= 55
        ),
        "registry_active_counts_preserved": (
            counts["active_model_count"] == 7
            and counts["active_formula_count"] == 7
            and counts["active_parameter_count"] == 49
        ),
        "model_spec_counts_exact": all(
            term in model_spec
            for term in (
                f'- model_count: {counts["model_count"]}',
                f'- formula_count: {counts["formula_count"]}',
                f'- parameter_count: {counts["parameter_count"]}',
                "- active_model_count: 7",
                "- active_formula_count: 7",
                "- active_parameter_count: 49",
            )
        ),
        "project_policy_projection_exact": (
            project_feature.get("status") == "planned"
            and project_feature.get("fact_level") == "PROPOSED"
            and project_mod008.get("status") == "planned"
            and project_mod008.get("fact_level") == "PROPOSED"
            and project_form008.get("status") == "planned"
            and project_form008.get("fact_level") == "PROPOSED"
            and project_form008.get("open_task_ids") == ["TASK-OPME-B-001"]
            and len(project_parameters) == 6
            and all(item.get("status") == "planned" for item in project_parameters)
            and all(item.get("fact_level") == "PROPOSED" for item in project_parameters)
        ),
    }
    return counts, checks


def _manual_rerun_truth(scenario_report: Mapping[str, Any]) -> dict[str, bool]:
    scenario = scenario_report.get("scenario_results", {}).get(
        "manual_rerun_lineage_idempotent", {}
    )
    try:
        contract = _scenario_module().load_scenario_contract()
    except (OSError, ValueError, json.JSONDecodeError):
        contract = {}
    manual = contract.get("manual_rerun_contract", {})
    return {
        "new_linked_identity_required": manual.get("new_job_identity_required") is True,
        "candidate_only": scenario.get("candidate_only") is True,
        "job_created": scenario.get("job_created") is True,
        "persisted": scenario.get("persisted") is True,
        "terminal_job_reopen_allowed": manual.get("terminal_reopen_allowed") is True,
    }


def _canonical_governance_report() -> dict[str, Any]:
    try:
        module = _load_module(
            GOVERNANCE_VALIDATOR_PATH, "stage039_review_governance_validator"
        )
        report = module.build_stage_review_governance_report(PROJECT_ROOT)
    except Exception as exc:
        return {"valid": False, "load_error": f"{type(exc).__name__}: {exc}"}
    return copy.deepcopy(report) if isinstance(report, dict) else {"valid": False}


def _governance_checks(report: Mapping[str, Any]) -> dict[str, bool]:
    phase_checks = report.get("phase_state_checks")
    phase_checks = phase_checks if isinstance(phase_checks, dict) else {}
    data_checks = report.get("data_boundary_checks")
    data_checks = data_checks if isinstance(data_checks, dict) else {}
    return {
        "validator_valid": report.get("valid") is True,
        "phase_state_structured_and_exact": bool(phase_checks)
        and all(value is True for value in phase_checks.values()),
        "review_event_semantics_exact": (
            report.get("event_json_errors") == []
            and report.get("event_semantic_errors") == []
            and report.get("missing_event_ids") == []
        ),
        "raw_and_real_data_boundaries_exact": bool(data_checks)
        and all(value is True for value in data_checks.values()),
        "required_governance_files_present": report.get("missing_required_files") == [],
        "no_tracked_forbidden_runtime_paths": report.get(
            "tracked_forbidden_runtime_files"
        )
        == [],
    }


def _review_artifact_semantics_exact() -> bool:
    try:
        text = REVIEW_ARTIFACT_PATH.read_text(encoding="utf-8")
    except OSError:
        return False
    required = {
        "# STAGE-039 Whole-Stage Review - Retry And Dead-Letter Policy",
        "IDS-V0_1-STAGE039-REVIEW",
        "ACC-STAGE-039",
        "completed_reviewed_local",
        "IDS-STAGE040-P1-GATE",
        "STAGE039-REVIEW-F1",
        "STAGE039-REVIEW-F2",
        "STAGE039-REVIEW-F3",
        "STAGE039-REVIEW-F4",
        "NO_GITHUB_UPLOAD",
        "NO_APP_REINSTALL",
        "NO_STAGE040_THIS_RUN",
        "/Users/linzezhang/Downloads/IDS_MetaData",
    }
    contradictory_true = re.search(
        r"\b(?:push_allowed|github_upload_allowed|app_reinstall_allowed|"
        r"production_runtime_activation_performed|raw_metadata_content_accessed|"
        r"fake_ids_business_data_used)\s*=\s*true\b",
        text,
        re.IGNORECASE,
    )
    return all(term in text for term in required) and contradictory_true is None


def build_stage039_review_report(
    *,
    registry_repair_checks: Optional[Mapping[str, Any]] = None,
    review_governance_report: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    try:
        delivery_report = _delivery_module().build_stage039_phase4_delivery_report()
        scenario_report = _scenario_module().build_stage039_phase3_report()
    except Exception as exc:
        delivery_report = {"delivery_contract_valid": False, "load_error": str(exc)}
        scenario_report = {"scenario_validation_valid": False, "load_error": str(exc)}

    counts, canonical_registry_checks = _registry_evidence()
    registry_checks = (
        canonical_registry_checks
        if registry_repair_checks is None
        else copy.deepcopy(dict(registry_repair_checks))
    )
    governance_report = (
        _canonical_governance_report()
        if review_governance_report is None
        else copy.deepcopy(dict(review_governance_report))
    )
    governance_checks = _governance_checks(governance_report)
    source_binding = _review_source_binding()
    manual_truth = _manual_rerun_truth(scenario_report)

    review_checks = {
        "phase4_delivery_valid": delivery_report.get("delivery_contract_valid") is True,
        "phase3_scenarios_valid": scenario_report.get("scenario_validation_valid") is True,
        "registry_repairs_valid": bool(registry_checks)
        and all(value is True for value in registry_checks.values()),
        "manual_rerun_truth_exact": (
            manual_truth.get("new_linked_identity_required") is True
            and manual_truth.get("candidate_only") is True
            and manual_truth.get("job_created") is False
            and manual_truth.get("persisted") is False
            and manual_truth.get("terminal_job_reopen_allowed") is False
        ),
        "review_artifact_semantics_exact": _review_artifact_semantics_exact(),
        "review_governance_valid": bool(governance_checks)
        and all(governance_checks.values()),
        "review_sources_git_tracked": source_binding["all_sources_git_tracked"],
        "review_sources_match_git_index": source_binding[
            "all_sources_match_git_index"
        ],
        "upload_and_app_remain_blocked": (
            delivery_report.get("github_upload_allowed") is False
            and delivery_report.get("app_reinstall_allowed") is False
        ),
    }
    review_valid = all(review_checks.values())
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "stage": "STAGE-039",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_valid": review_valid,
        "review_checks": review_checks,
        "result": REVIEW_RESULT if review_valid else "FAIL_CLOSED",
        "stage_review_status": REVIEW_STATUS
        if review_valid
        else "blocked_invalid_review_evidence",
        "next_gate": NEXT_GATE if review_valid else REVIEW_GATE,
        "registry_counts": counts,
        "registry_repair_checks": registry_checks,
        "manual_rerun_truth": manual_truth,
        "review_source_binding": source_binding,
        "review_governance_checks": governance_checks,
        "review_governance_report": governance_report,
        "delivery_report": delivery_report,
        "scenario_report": scenario_report,
        "whole_stage_review_performed": True,
        "production_runtime_activation_performed": False,
        "persistent_queue_write_performed": False,
        "database_connection_performed": False,
        "runtime_output_written": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "owner_feedback_zh": (
            "重试与死信策略已完成本地整阶段复审；治理登记、总数和人工重跑"
            "事实边界已修复，生产运行与批次上传继续禁用。"
            if review_valid
            else "重试与死信整阶段复审证据无效；保持 Review gate 失败关闭。"
        ),
    }


def main() -> int:
    report = build_stage039_review_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["review_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
