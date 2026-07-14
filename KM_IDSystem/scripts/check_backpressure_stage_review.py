#!/usr/bin/env python3
"""Build the fail-closed STAGE-040 whole-stage review report."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Optional
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
POLICY_ROOT = PURSUE_ROOT / "backpressure_policy"

ARCHIVE_PATH = Path(
    "/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip"
)
ROADMAP_SOURCE_PATH = Path(
    "/Users/linzezhang/Downloads/IDS_Codex开发Roadmap_v0_1_only_中文修订版.txt"
)
INSTRUCTIONS_SOURCE_PATH = Path(
    "/Users/linzezhang/Downloads/IDS_Codex使用说明_v0_1_only_中文修订版.txt"
)
SOURCE_MEMBER = (
    "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-040_反压策略.md"
)
EXPECTED_SOURCE_HASHES = {
    "archive_sha256_exact": (
        ARCHIVE_PATH,
        "55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3",
    ),
    "roadmap_sha256_exact": (
        ROADMAP_SOURCE_PATH,
        "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6",
    ),
    "instructions_sha256_exact": (
        INSTRUCTIONS_SOURCE_PATH,
        "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8",
    ),
}
EXPECTED_MEMBER_SHA256 = (
    "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d"
)

PHASE_CHECKERS = {
    "phase1": PROJECT_ROOT / "scripts" / "check_backpressure_policy.py",
    "phase2": PROJECT_ROOT / "scripts" / "check_backpressure_runtime.py",
    "phase3": PROJECT_ROOT / "scripts" / "check_backpressure_scenarios.py",
    "phase4": PROJECT_ROOT / "scripts" / "check_backpressure_delivery.py",
}
POLICY_CONTRACT_PATH = POLICY_ROOT / "stage040_backpressure_policy_contract.json"
REVIEW_ARTIFACT_PATH = PURSUE_ROOT / "STAGE040_STAGE_REVIEW.md"
BATCH_PATH = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP_PATH = PROJECT_ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS_PATH = PROJECT_ROOT / "docs" / "governance" / "events.jsonl"
CONTROL_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md"
)

TASK_ID = "IDS-V0_1-STAGE040-REVIEW"
ACCEPTANCE_ID = "ACC-STAGE-040"
REVIEW_GATE = "IDS-STAGE040-REVIEW-GATE"
NEXT_GATE = "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
PASS_RESULT = "PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED"
REVIEW_EVENT_ID = "EVT-IDS-V0_1-STAGE040-REVIEW-20260714-001"

REVIEW_SOURCE_PATHS = (
    PURSUE_ROOT / "STAGE040_ENTRY_CONTRACT.md",
    PURSUE_ROOT / "STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
    POLICY_ROOT / "stage040_backpressure_policy_contract.json",
    PHASE_CHECKERS["phase1"],
    PURSUE_ROOT / "tests" / "test_stage040_backpressure_policy.py",
    PURSUE_ROOT / "STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
    POLICY_ROOT / "stage040_backpressure_runtime_contract.json",
    PHASE_CHECKERS["phase2"],
    PURSUE_ROOT / "tests" / "test_stage040_backpressure_runtime.py",
    PURSUE_ROOT / "STAGE040_PHASE3_SCENARIO_VALIDATION.md",
    POLICY_ROOT / "stage040_backpressure_scenarios.json",
    PHASE_CHECKERS["phase3"],
    PURSUE_ROOT / "tests" / "test_stage040_backpressure_scenarios.py",
    PURSUE_ROOT / "STAGE040_PHASE4_CLOSEOUT.md",
    POLICY_ROOT / "stage040_backpressure_delivery_contract.json",
    PHASE_CHECKERS["phase4"],
    PURSUE_ROOT / "tests" / "test_stage040_backpressure_delivery.py",
    REVIEW_ARTIFACT_PATH,
    Path(__file__).resolve(),
    PURSUE_ROOT / "tests" / "test_stage040_backpressure_review.py",
    PURSUE_ROOT / "tests" / "test_stage038_worker_queue_baseline.py",
    PURSUE_ROOT / "tests" / "test_stage038_worker_queue_delivery.py",
    PURSUE_ROOT / "tests" / "test_stage038_worker_queue_review.py",
    PURSUE_ROOT / "tests" / "test_stage038_worker_queue_runtime.py",
    PURSUE_ROOT / "tests" / "test_stage038_worker_queue_scenarios.py",
    PURSUE_ROOT / "tests" / "test_stage039_retry_dead_letter_review.py",
    PURSUE_ROOT / "validate_stage005_governance_regression.py",
    PURSUE_ROOT / "tests" / "test_stage005_governance_regression.py",
    BATCH_PATH,
    ROADMAP_PATH,
    EVENTS_PATH,
    PROJECT_ROOT / "docs" / "HANDOFF.md",
    PROJECT_ROOT / "CHANGELOG.md",
    PROJECT_ROOT / "功能清单.md",
    PROJECT_ROOT / "开发记录.md",
    PROJECT_ROOT / "模型参数文件.md",
)


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_integrity_checks() -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for name, (path, expected) in EXPECTED_SOURCE_HASHES.items():
        try:
            checks[name] = path.is_file() and _sha256_file(path) == expected
        except OSError:
            checks[name] = False

    try:
        with zipfile.ZipFile(ARCHIVE_PATH) as archive:
            matches = [name for name in archive.namelist() if name == SOURCE_MEMBER]
            member = archive.read(SOURCE_MEMBER) if len(matches) == 1 else b""
    except (OSError, KeyError, zipfile.BadZipFile, RuntimeError):
        matches = []
        member = b""
    checks["source_member_unique"] = len(matches) == 1
    checks["source_member_sha256_exact"] = (
        bool(member) and hashlib.sha256(member).hexdigest() == EXPECTED_MEMBER_SHA256
    )
    return checks


def _phase_results() -> dict[str, bool]:
    try:
        phase1 = _load_module(PHASE_CHECKERS["phase1"], "stage040_review_phase1")
        phase2 = _load_module(PHASE_CHECKERS["phase2"], "stage040_review_phase2")
        phase3 = _load_module(PHASE_CHECKERS["phase3"], "stage040_review_phase3")
        phase4 = _load_module(PHASE_CHECKERS["phase4"], "stage040_review_phase4")
        phase1_report = phase1.build_stage040_phase1_report()
        phase2_report = phase2.build_stage040_phase2_report()
        phase3_contract = phase3.load_scenario_contract()
        phase3_checks = phase3.validate_scenario_contract(phase3_contract)
        phase4_contract = phase4.load_delivery_contract()
        phase4_checks = phase4.validate_delivery_contract(phase4_contract)
    except Exception:
        return {
            "phase1_contract_valid": False,
            "phase2_slice_valid": False,
            "phase3_contract_valid": False,
            "phase4_contract_valid": False,
        }
    return {
        "phase1_contract_valid": phase1_report.get("phase1_contract_valid") is True,
        "phase2_slice_valid": phase2_report.get("slice_valid") is True,
        "phase3_contract_valid": bool(phase3_checks) and all(phase3_checks.values()),
        "phase4_contract_valid": bool(phase4_checks) and all(phase4_checks.values()),
    }


def _canonical_finding_checks() -> dict[str, bool]:
    try:
        runtime = _load_module(
            PHASE_CHECKERS["phase2"], "stage040_review_runtime_findings"
        )
        runtime_contract = runtime.load_contract()
        valid_job = runtime.build_control_job(CONTROL_REF)
        invalid_observation = runtime.evaluate_backpressure(
            valid_job,
            {"unexpected": object()},
            contract=runtime_contract,
            now_epoch_seconds=1,
        )
        malformed_results = []
        for invalid_refs in (
            [{"private_payload": "SENTINEL"}],
            ["PRIVATE_SENTINEL_NOT_A_REF"],
        ):
            invalid_job = copy.deepcopy(valid_job)
            invalid_job["input_refs"] = invalid_refs
            malformed_results.append(
                runtime.evaluate_backpressure(
                    invalid_job,
                    {},
                    contract=runtime_contract,
                    now_epoch_seconds=1,
                )
            )
        encoded_results = json.dumps(
            [invalid_observation, *malformed_results], ensure_ascii=False
        )
        policy = json.loads(POLICY_CONTRACT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "invalid_metadata_is_structured_and_redacted": False,
            "pause_status_is_state_aware": False,
            "scheduler_fairness_is_not_overclaimed": False,
        }

    projection = policy.get("human_status_projection", {})
    fairness = policy.get("fairness_contract", {})
    invalid_metadata_safe = (
        invalid_observation.get("decision_action") == "REQUIRE_MANUAL_REVIEW"
        and invalid_observation.get("reason_code")
        == "INVALID_PRESSURE_OBSERVATION"
        and invalid_observation.get("observed_at_epoch_seconds") is None
        and all(
            result.get("decision_action") == "REQUIRE_MANUAL_REVIEW"
            and result.get("reason_code") == "INVALID_CONTRACT_OR_JOB"
            and result.get("input_refs") == []
            for result in malformed_results
        )
        and "SENTINEL" not in encoded_results
    )
    return {
        "invalid_metadata_is_structured_and_redacted": invalid_metadata_safe,
        "pause_status_is_state_aware": projection.get("PAUSE_RESOURCE_GATE")
        == {
            "QUEUED_OR_RETRY_WAIT": "已暂停",
            "CLAIMED_OR_RUNNING": "暂停中",
        },
        "scheduler_fairness_is_not_overclaimed": fairness
        == {
            "priority_cannot_bypass_safety_gate": True,
            "starvation_prevention_proved": False,
            "priority_vocabulary_owner": "STAGE-022",
            "scheduler_algorithm": "NOT_IMPLEMENTED_IN_STAGE040",
            "per_job_type_concurrency": "PHASE2_ADMISSION_GUARD_ONLY",
        },
    }


def _governance_checks() -> dict[str, bool]:
    try:
        batch = BATCH_PATH.read_text(encoding="utf-8")
        roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
        events = [
            json.loads(line)
            for line in EVENTS_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        review = REVIEW_ARTIFACT_PATH.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        return {"governance_files_parse": False}
    matching = [event for event in events if event.get("event_id") == REVIEW_EVENT_ID]
    return {
        "governance_files_parse": True,
        "batch_reviewed_local_exact": all(
            term in batch
            for term in (
                'status: "stage040_completed_reviewed_local"',
                'review_status: "passed"',
                'current_task_id: "IDS-V0_1-STAGE040-REVIEW"',
                'next_allowed_task_id: "IDS-V0_1-BATCH-031-040-REVIEW-GATE"',
                "push_allowed: false",
                "batch_review_performed: false",
            )
        ),
        "roadmap_reviewed_local_exact": all(
            term in roadmap
            for term in (
                'current_phase_id: "IDS-STAGE040-REVIEW"',
                'current_task_id: "IDS-V0_1-STAGE040-REVIEW"',
                'next_gate_id: "IDS-V0_1-BATCH-031-040-REVIEW-GATE"',
                'status: "completed_reviewed_local"',
            )
        ),
        "review_event_exact": len(matching) == 1
        and matching[0].get("event_type") == "stage_review"
        and matching[0].get("task_id") == TASK_ID
        and matching[0].get("acceptance_ids") == [ACCEPTANCE_ID],
        "review_markers_exact": all(
            term in review
            for term in (
                "STAGE040-REVIEW-F1",
                "STAGE040-REVIEW-F2",
                "STAGE040-REVIEW-F3",
                "NO_BATCH_REVIEW_THIS_RUN",
                "NO_GITHUB_UPLOAD",
                "NO_APP_REINSTALL",
                "NO_STAGE041_THIS_RUN",
            )
        ),
    }


def _git_source_binding_checks() -> dict[str, bool]:
    tracked: list[bool] = []
    index_matches: list[bool] = []
    for path in REVIEW_SOURCE_PATHS:
        try:
            relative = path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            tracked.append(False)
            index_matches.append(False)
            continue
        tracked_result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        tracked.append(path.is_file() and tracked_result.returncode == 0)
        index_result = subprocess.run(
            ["git", "diff", "--quiet", "--", relative],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        index_matches.append(tracked[-1] and index_result.returncode == 0)
    return {
        "all_review_sources_git_tracked": bool(tracked) and all(tracked),
        "all_review_sources_match_git_index": bool(index_matches)
        and all(index_matches),
    }


def build_stage040_review_report(
    *, finding_checks: Optional[Mapping[str, Any]] = None
) -> dict[str, Any]:
    source_checks = _source_integrity_checks()
    phase_results = _phase_results()
    canonical_findings = _canonical_finding_checks()
    effective_findings = (
        dict(finding_checks) if isinstance(finding_checks, Mapping) else canonical_findings
    )
    governance_checks = _governance_checks()
    source_binding_checks = _git_source_binding_checks()
    review_valid = all(
        bool(checks) and all(value is True for value in checks.values())
        for checks in (
            source_checks,
            phase_results,
            effective_findings,
            governance_checks,
            source_binding_checks,
        )
    )
    return {
        "schema_version": "ids.stage040.backpressure.stage_review.v1",
        "stage": "STAGE-040",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_valid": review_valid,
        "result": PASS_RESULT if review_valid else "FAIL_CLOSED",
        "stage_review_status": (
            "completed_reviewed_local" if review_valid else "review_blocked"
        ),
        "next_gate": NEXT_GATE if review_valid else REVIEW_GATE,
        "source_integrity_valid": bool(source_checks)
        and all(source_checks.values()),
        "source_integrity_checks": source_checks,
        "phase_results": phase_results,
        "finding_count": 3,
        "finding_counts": {"Critical": 1, "Important": 2, "Minor": 0},
        "finding_checks": effective_findings,
        "governance_checks": governance_checks,
        "source_binding_checks": source_binding_checks,
        "production_runtime_activation_performed": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "batch_review_performed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "stage041_started": False,
    }


def main() -> int:
    report = build_stage040_review_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["review_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
