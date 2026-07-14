#!/usr/bin/env python3
"""Build the fail-closed STAGE-038 whole-stage review report."""

from __future__ import annotations

import copy
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
DELIVERY_CHECKER_PATH = PROJECT_ROOT / "scripts" / "check_worker_queue_delivery.py"
GOVERNANCE_VALIDATOR_PATH = (
    PURSUE_ROOT / "validate_stage005_governance_regression.py"
)
REVIEW_ARTIFACT_PATH = PURSUE_ROOT / "STAGE038_STAGE_REVIEW.md"
BATCH_LOCK_PATH = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP_PATH = PROJECT_ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS_PATH = PROJECT_ROOT / "docs" / "governance" / "events.jsonl"

REPORT_SCHEMA_VERSION = "ids.stage038.worker_queue_baseline.stage_review.v1"
TASK_ID = "IDS-V0_1-STAGE038-REVIEW"
ACCEPTANCE_ID = "ACC-STAGE-038"
REVIEW_STATUS = "completed_reviewed_local"
REVIEW_RESULT = "PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED"
REVIEW_GATE = "IDS-STAGE038-REVIEW-GATE"
NEXT_GATE = "IDS-STAGE039-P1-GATE"

SOURCE_HASH_TERMS = {
    "source_archive_sha256": (
        "55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3"
    ),
    "source_member_sha256": (
        "613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634"
    ),
    "roadmap_sha256": (
        "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6"
    ),
    "instructions_sha256": (
        "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8"
    ),
}

REVIEW_SOURCE_PATHS = {
    "entry_contract": PURSUE_ROOT / "STAGE038_ENTRY_CONTRACT.md",
    "phase1_boundary": PURSUE_ROOT / "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
    "source_reverification": PURSUE_ROOT / "STAGE038_PHASE1_SOURCE_REVERIFICATION.md",
    "source_reverification_review": (
        PURSUE_ROOT / "STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md"
    ),
    "phase2_evidence": PURSUE_ROOT / "STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md",
    "phase3_evidence": PURSUE_ROOT / "STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md",
    "phase4_evidence": PURSUE_ROOT / "STAGE038_PHASE4_CLOSEOUT.md",
    "review_artifact": REVIEW_ARTIFACT_PATH,
    "phase2_contract": (
        PURSUE_ROOT
        / "worker_queue_baseline"
        / "stage038_worker_queue_baseline_index.json"
    ),
    "phase3_contract": (
        PURSUE_ROOT
        / "worker_queue_baseline"
        / "stage038_worker_queue_scenarios.json"
    ),
    "phase4_contract": (
        PURSUE_ROOT
        / "worker_queue_baseline"
        / "stage038_worker_queue_delivery_contract.json"
    ),
    "phase2_checker": PROJECT_ROOT / "scripts" / "check_worker_queue_baseline.py",
    "phase3_checker": PROJECT_ROOT / "scripts" / "check_worker_queue_scenarios.py",
    "phase4_checker": DELIVERY_CHECKER_PATH,
    "review_checker": Path(__file__).resolve(),
    "phase2_test": (
        PURSUE_ROOT / "tests" / "test_stage038_worker_queue_runtime.py"
    ),
    "phase3_test": (
        PURSUE_ROOT / "tests" / "test_stage038_worker_queue_scenarios.py"
    ),
    "phase4_test": (
        PURSUE_ROOT / "tests" / "test_stage038_worker_queue_delivery.py"
    ),
    "review_test": (
        PURSUE_ROOT / "tests" / "test_stage038_worker_queue_review.py"
    ),
    "batch_lock": BATCH_LOCK_PATH,
    "roadmap": ROADMAP_PATH,
    "events": EVENTS_PATH,
    "governance_validator": GOVERNANCE_VALIDATOR_PATH,
}

_DELIVERY_MODULE: Any = None


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
            DELIVERY_CHECKER_PATH,
            "stage038_worker_queue_delivery_for_review",
        )
    return _DELIVERY_MODULE


def _parse_yaml_text(text: str) -> dict[str, Any]:
    parsed = _delivery_module()._parse_yaml_text(text)
    return parsed if isinstance(parsed, dict) else {}


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


def _git_head_matches(path: Path) -> bool:
    return _git_tracked(path) and _git_path_check(
        path, ["diff", "--cached", "--quiet", "HEAD"]
    )


def _review_source_binding() -> dict[str, Any]:
    tracked: dict[str, bool] = {}
    index_matches: dict[str, bool] = {}
    head_matches: dict[str, bool] = {}
    observed: dict[str, Optional[str]] = {}
    for name, path in REVIEW_SOURCE_PATHS.items():
        is_file = path.is_file()
        tracked[name] = is_file and _git_tracked(path)
        index_matches[name] = tracked[name] and _git_index_matches(path)
        head_matches[name] = tracked[name] and _git_head_matches(path)
        observed[name] = _sha256_file(path) if is_file else None
    return {
        "all_sources_git_tracked": bool(tracked) and all(tracked.values()),
        "all_sources_match_git_index": (
            bool(index_matches) and all(index_matches.values())
        ),
        "all_sources_match_head": bool(head_matches) and all(head_matches.values()),
        "git_tracked_sources": tracked,
        "git_index_sources": index_matches,
        "git_head_sources": head_matches,
        "observed_source_sha256": observed,
    }


def _source_tuple_recorded() -> bool:
    try:
        text = (
            PURSUE_ROOT / "STAGE038_PHASE1_SOURCE_REVERIFICATION.md"
        ).read_text(encoding="utf-8")
    except OSError:
        return False
    return all(f"`{key}={value}`" in text for key, value in SOURCE_HASH_TERMS.items())


def _review_artifact_semantics_exact() -> bool:
    try:
        text = REVIEW_ARTIFACT_PATH.read_text(encoding="utf-8")
    except OSError:
        return False
    required_terms = {
        "# STAGE-038 Whole-Stage Review - Worker 队列基线",
        "- Review Task ID: `IDS-V0_1-STAGE038-REVIEW`",
        "- Acceptance ID: `ACC-STAGE-038`",
        "- Current state: `completed_reviewed_local`",
        "- Current upload switch: `push_allowed=false`",
        "- Next allowed gate: `IDS-STAGE039-P1-GATE`",
        "STAGE038-REVIEW-F1",
        "STAGE038-REVIEW-F2",
        "STAGE038-REVIEW-F3",
        "STAGE038-REVIEW-F4",
        "NO_GITHUB_UPLOAD",
        "NO_APP_REINSTALL",
        "NO_STAGE039_THIS_RUN",
        "/Users/linzezhang/Downloads/IDS_MetaData",
        "## Real Data Only Policy",
    }
    contradictory_true = re.search(
        r"\b(?:push_allowed|github_upload_allowed|app_reinstall_allowed|"
        r"production_runtime_activation_performed|raw_metadata_content_accessed|"
        r"fake_ids_business_data_used)\s*=\s*true\b",
        text,
        re.IGNORECASE,
    )
    return all(term in text for term in required_terms) and contradictory_true is None


def _canonical_review_governance_report() -> dict[str, Any]:
    try:
        module = _load_module(
            GOVERNANCE_VALIDATOR_PATH,
            "stage038_review_governance_validator",
        )
        report = module.build_stage038_review_governance_report(PROJECT_ROOT)
    except Exception as exc:
        return {"valid": False, "load_error": f"{type(exc).__name__}: {exc}"}
    return copy.deepcopy(report) if isinstance(report, dict) else {"valid": False}


def _review_governance_checks(report: Mapping[str, Any]) -> dict[str, bool]:
    phase_checks = report.get("phase_state_checks")
    phase_checks = phase_checks if isinstance(phase_checks, dict) else {}
    data_checks = report.get("data_boundary_checks")
    data_checks = data_checks if isinstance(data_checks, dict) else {}
    return {
        "validator_identity_exact": (
            report.get("stage") == "STAGE-005"
            and report.get("acceptance_id") == "ACC-STAGE-005"
        ),
        "validator_valid": report.get("valid") is True,
        "phase_state_structured_and_exact": (
            bool(phase_checks) and all(value is True for value in phase_checks.values())
        ),
        "review_event_semantics_exact": (
            report.get("event_json_errors") == []
            and report.get("event_semantic_errors") == []
            and report.get("missing_event_ids") == []
        ),
        "raw_and_real_data_boundaries_exact": (
            bool(data_checks) and all(value is True for value in data_checks.values())
        ),
        "required_governance_files_present": report.get("missing_required_files")
        == [],
        "no_tracked_forbidden_runtime_paths": report.get(
            "tracked_forbidden_runtime_files"
        )
        == [],
    }


def build_stage038_review_report(
    *,
    review_governance_report: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    try:
        delivery_report = _delivery_module().build_stage038_phase4_delivery_report()
    except Exception as exc:
        delivery_report = {
            "delivery_contract_valid": False,
            "load_error": f"{type(exc).__name__}: {exc}",
        }
    governance_report = (
        _canonical_review_governance_report()
        if review_governance_report is None
        else copy.deepcopy(dict(review_governance_report))
    )
    governance_checks = _review_governance_checks(governance_report)
    source_binding = _review_source_binding()
    delivery_checks = delivery_report.get("delivery_check_results")
    delivery_checks = delivery_checks if isinstance(delivery_checks, dict) else {}
    backpressure = delivery_report.get("backpressure_trigger_proof")
    backpressure = backpressure if isinstance(backpressure, dict) else {}
    failure = delivery_report.get("failure_retry_log")
    failure = failure if isinstance(failure, dict) else {}

    review_checks = {
        "phase4_delivery_valid": (
            delivery_report.get("contract_valid") is True
            and delivery_report.get("delivery_contract_valid") is True
            and bool(delivery_checks)
            and all(delivery_checks.values())
        ),
        "contract_shapes_exact": (
            delivery_report.get("phase2_report", {})
            .get("contract_checks", {})
            .get("contract_shape_exact")
            is True
            and delivery_report.get("phase3_report", {})
            .get("contract_checks", {})
            .get("contract_shape_exact")
            is True
            and delivery_report.get("contract_checks", {}).get(
                "contract_shape_exact"
            )
            is True
        ),
        "external_api_budget_gate_proved": (
            backpressure.get("external_api_budget_insufficient", {}).get(
                "result_code"
            )
            == "PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT"
            and backpressure.get("external_api_budget_insufficient", {}).get(
                "queue_records_created"
            )
            == 0
            and backpressure.get("external_api_budget_insufficient", {}).get(
                "external_api_call_performed"
            )
            is False
        ),
        "same_operation_resubmission_truthful": (
            failure.get("same_operation_resubmission_available") is False
            and failure.get("same_operation_resubmission_result")
            == "EXISTING_QUEUE_ENTRY"
        ),
        "review_artifact_semantics_exact": _review_artifact_semantics_exact(),
        "source_tuple_recorded": _source_tuple_recorded(),
        "review_governance_valid": (
            bool(governance_checks) and all(governance_checks.values())
        ),
        "review_sources_git_tracked": source_binding[
            "all_sources_git_tracked"
        ],
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
        "stage": "STAGE-038",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_valid": review_valid,
        "review_checks": review_checks,
        "result": REVIEW_RESULT if review_valid else "FAIL_CLOSED",
        "stage_review_status": (
            REVIEW_STATUS if review_valid else "blocked_invalid_review_evidence"
        ),
        "next_gate": NEXT_GATE if review_valid else REVIEW_GATE,
        "review_source_binding": source_binding,
        "review_governance_checks": governance_checks,
        "review_governance_report": governance_report,
        "delivery_report": delivery_report,
        "whole_stage_review_performed": True,
        "isolated_queue_runtime_performed": delivery_report.get(
            "isolated_queue_runtime_performed"
        )
        is True,
        "production_runtime_activation_performed": False,
        "persistent_queue_write_performed": False,
        "retry_scheduler_performed": False,
        "automatic_lifecycle_runtime_performed": False,
        "crash_recovery_runtime_performed": False,
        "cleanup_runtime_performed": False,
        "database_connection_performed": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "owner_feedback_zh": (
            "Worker 队列基线已完成本地整阶段复审；合同注入、API 预算暂停和失败后"
            "同操作重跑边界已修复。生产运行与批次上传继续禁用。"
            if review_valid
            else "Worker 队列整阶段复审证据无效；保持 Review gate 失败关闭。"
        ),
    }


def main() -> int:
    report = build_stage038_review_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["review_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
