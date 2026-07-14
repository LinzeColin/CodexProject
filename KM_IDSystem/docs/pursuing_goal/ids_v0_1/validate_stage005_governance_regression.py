"""Validate the IDS STAGE-005 governance-regression boundary."""

from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


STAGE = "STAGE-005"
ACCEPTANCE_ID = "ACC-STAGE-005"
CURRENT_PRODUCT_NAME = "IDS / Industrial Data System"
ACCEPTED_NAMES = (CURRENT_PRODUCT_NAME, "ProductMetaDatabase", "FinanceMetaDatabase")

STAGE038_SOURCE_VALUES = {
    "source_archive_path": (
        "/Users/linzezhang/Downloads/"
        "IDS_Taskpack_v0_1_only_中文修订版.zip"
    ),
    "source_archive_sha256": (
        "55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3"
    ),
    "source_member": (
        "IDS_v0_1_Final_Chinese_Revised/stages/"
        "STAGE-038_Worker队列基线.md"
    ),
    "source_member_match_count": "1",
    "source_member_integrity": "OK",
    "source_member_sha256": (
        "613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634"
    ),
    "roadmap_sha256": (
        "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6"
    ),
    "instructions_sha256": (
        "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8"
    ),
    "source_verification_status": "SOURCE_VERIFIED",
    "reconciliation_status": "passed",
    "source_reverification_required_before_phase2": "false",
    "independent_review_status": "passed",
    "phase2_entry_authorized": "true",
}


@lru_cache(maxsize=64)
def _parse_yaml_text(text: str) -> dict[str, Any]:
    module_name = "_ids_stage005_governance_yaml"
    module = sys.modules.get(module_name)
    if module is None:
        parser_path = Path(__file__).resolve().parents[4] / "scripts" / "validate_project_governance.py"
        spec = importlib.util.spec_from_file_location(module_name, parser_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load governance YAML parser: {parser_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    try:
        parsed = module.fallback_yaml_load(text)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _stage038_markdown_assignments(text: str) -> dict[str, list[str]]:
    return {
        key: re.findall(rf"`{re.escape(key)}=([^`\n]+)`", text)
        for key in STAGE038_SOURCE_VALUES
    }


def evaluate_stage038_source_reverification(
    batch_text: str,
    roadmap_text: str,
    entry_text: str,
    phase1_text: str,
    source_evidence_text: str,
    review_text: str,
) -> dict[str, bool]:
    """Validate the exact finite state that authorizes STAGE-038 Phase 2."""
    batch = _parse_yaml_text(batch_text)
    roadmap = _parse_yaml_text(roadmap_text)

    stage_progress = batch.get("stage_progress")
    stage_progress = stage_progress if isinstance(stage_progress, dict) else {}
    batch_stage = stage_progress.get("STAGE-038")
    batch_stage = batch_stage if isinstance(batch_stage, dict) else {}
    decision = batch.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    upload_gate = batch.get("upload_gate")
    upload_gate = upload_gate if isinstance(upload_gate, dict) else {}

    roadmap_stages = roadmap.get("stages")
    roadmap_stages = roadmap_stages if isinstance(roadmap_stages, list) else []
    roadmap_stage = next(
        (
            item
            for item in roadmap_stages
            if isinstance(item, dict) and item.get("stage_id") == "IDS-STAGE038"
        ),
        {},
    )
    source_gate = roadmap_stage.get("source_reverification_gate")
    source_gate = source_gate if isinstance(source_gate, dict) else {}
    phases = roadmap_stage.get("phases")
    phases = phases if isinstance(phases, list) else []
    phase2 = next(
        (
            item
            for item in phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE038-P2"
        ),
        {},
    )
    phase3 = next(
        (
            item
            for item in phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE038-P3"
        ),
        {},
    )
    phase4 = next(
        (
            item
            for item in phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE038-P4"
        ),
        {},
    )
    stage_review = roadmap_stage.get("review")
    stage_review = stage_review if isinstance(stage_review, dict) else {}

    expected_yaml_values: dict[str, Any] = {
        key: (
            1
            if key == "source_member_match_count"
            else False
            if key == "source_reverification_required_before_phase2"
            else True
            if key == "phase2_entry_authorized"
            else value
        )
        for key, value in STAGE038_SOURCE_VALUES.items()
    }
    batch_source_tuple_exact = all(
        batch_stage.get(key) == value for key, value in expected_yaml_values.items()
    )
    roadmap_source_tuple_exact = all(
        source_gate.get(key) == value for key, value in expected_yaml_values.items()
    )

    markdown_surfaces = {
        "entry_source_tuple_exact": entry_text,
        "phase1_source_tuple_exact": phase1_text,
        "source_evidence_tuple_exact": source_evidence_text,
        "review_source_tuple_exact": review_text,
    }
    markdown_checks: dict[str, bool] = {}
    markdown_assignments: list[dict[str, list[str]]] = []
    for check_name, text in markdown_surfaces.items():
        assignments = _stage038_markdown_assignments(text)
        markdown_assignments.append(assignments)
        markdown_checks[check_name] = all(
            assignments[key] == [value]
            for key, value in STAGE038_SOURCE_VALUES.items()
        )

    hash_keys = (
        "source_archive_sha256",
        "source_member_sha256",
        "roadmap_sha256",
        "instructions_sha256",
    )
    observed_hash_tuples: list[tuple[Any, ...]] = [
        tuple(batch_stage.get(key) for key in hash_keys),
        tuple(source_gate.get(key) for key in hash_keys),
    ]
    observed_hash_tuples.extend(
        tuple(assignments[key][0] if len(assignments[key]) == 1 else None for key in hash_keys)
        for assignments in markdown_assignments
    )
    expected_hash_tuple = tuple(STAGE038_SOURCE_VALUES[key] for key in hash_keys)

    mixed_yaml_tokens = (
        'source_verification_status: "EXTERNAL_TASKPACK_ABSENT"',
        'source_reverification_gate_status: "pending_independent_review"',
        'source_reverification_gate_status: "blocked_external_taskpack_absent"',
        'reconciliation_status: "implemented_pending_independent_review"',
        'independent_review_status: "pending"',
        "source_reverification_required_before_phase2: true",
        "phase2_entry_authorized: false",
    )
    mixed_markdown_tokens = (
        "source_verification_status=EXTERNAL_TASKPACK_ABSENT",
        "reconciliation_status=IMPLEMENTED_PENDING_INDEPENDENT_REVIEW",
        "independent_review_status=PENDING",
        "source_reverification_required_before_phase2=true",
        "phase2_entry_authorized=false",
    )

    return {
        "yaml_documents_parsed": bool(batch) and bool(roadmap),
        "batch_source_tuple_exact": batch_source_tuple_exact,
        "roadmap_source_tuple_exact": roadmap_source_tuple_exact,
        **markdown_checks,
        "all_hashes_match_exact_sources": all(
            value == expected_hash_tuple for value in observed_hash_tuples
        ),
        "batch_final_state_exact": (
            (
                batch.get("status") == "stage038_phase1_source_reverified"
                and batch_stage.get("status")
                == "stage038_phase1_source_reverified"
                and batch_stage.get("current_task_id")
                == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"
                and batch_stage.get("next_phase") == "Phase 2"
                and batch_stage.get("next_gate") == "IDS-STAGE038-P2-GATE"
                and decision.get("current_task_id")
                == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"
                and decision.get("next_allowed_task_id")
                == "IDS-V0_1-STAGE038-P2"
            )
            or (
                batch.get("status") == "stage038_phase2_completed"
                and batch_stage.get("status") == "stage038_phase2_completed"
                and batch_stage.get("current_task_id")
                == "IDS-V0_1-STAGE038-P2"
                and batch_stage.get("completed_phases")
                == ["Phase 1", "Phase 2"]
                and batch_stage.get("next_phase") == "Phase 3"
                and batch_stage.get("next_gate") == "IDS-STAGE038-P3-GATE"
                and decision.get("current_task_id")
                == "IDS-V0_1-STAGE038-P2"
                and decision.get("next_allowed_task_id")
                == "IDS-V0_1-STAGE038-P3"
            )
            or (
                batch.get("status") == "stage038_phase3_completed"
                and batch_stage.get("status") == "stage038_phase3_completed"
                and batch_stage.get("current_task_id")
                == "IDS-V0_1-STAGE038-P3"
                and batch_stage.get("completed_phases")
                == ["Phase 1", "Phase 2", "Phase 3"]
                and batch_stage.get("next_phase") == "Phase 4"
                and batch_stage.get("next_gate") == "IDS-STAGE038-P4-GATE"
                and decision.get("current_task_id")
                == "IDS-V0_1-STAGE038-P3"
                and decision.get("next_allowed_task_id")
                == "IDS-V0_1-STAGE038-P4"
            )
            or (
                batch.get("status")
                == "stage038_phase4_completed_review_pending"
                and batch_stage.get("status")
                == "stage038_phase4_completed_review_pending"
                and batch_stage.get("current_task_id")
                == "IDS-V0_1-STAGE038-P4"
                and batch_stage.get("completed_phases")
                == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
                and batch_stage.get("review_status") == "pending"
                and batch_stage.get("next_phase") == "stage_review"
                and batch_stage.get("next_gate")
                == "IDS-STAGE038-REVIEW-GATE"
                and decision.get("current_task_id")
                == "IDS-V0_1-STAGE038-P4"
                and decision.get("next_allowed_task_id")
                == "IDS-V0_1-STAGE038-REVIEW"
            )
            or (
                batch.get("status") == "stage038_completed_reviewed_local"
                and batch_stage.get("status") == "completed_reviewed_local"
                and batch_stage.get("completed_phases")
                == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
                and batch_stage.get("review_status") == "passed"
                and batch_stage.get("next_stage") == "STAGE-039"
                and batch_stage.get("next_gate") == "IDS-STAGE039-P1-GATE"
                and batch_stage.get("current_task_id")
                == "IDS-V0_1-STAGE038-REVIEW"
                and batch_stage.get("acceptance_status")
                == "reviewed_local_passed"
                and decision.get("current_task_id")
                == "IDS-V0_1-STAGE038-REVIEW"
                and decision.get("next_allowed_task_id")
                == "IDS-V0_1-STAGE039-P1"
            )
            or (
                batch.get("status")
                in {
                    "stage039_phase1_completed",
                    "stage039_phase2_completed",
                    "stage039_phase3_completed",
                    "stage039_phase4_completed_review_pending",
                    "stage039_completed_reviewed_local",
                    "stage040_phase1_completed",
                    "stage040_phase2_completed",
                    "stage040_phase3_completed",
                    "stage040_phase4_completed_review_pending",
                    "stage040_completed_reviewed_local",
                    "reviewed_ready_for_upload_no_github_upload",
                    "local_batch_upload_gate_passed_pending_github_merge",
                    "uploaded_to_github_main",
                }
                and batch_stage.get("status") == "completed_reviewed_local"
                and batch_stage.get("completed_phases")
                == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
                and batch_stage.get("review_status") == "passed"
                and batch_stage.get("next_stage") == "STAGE-039"
                and batch_stage.get("next_gate") == "IDS-STAGE039-P1-GATE"
                and batch_stage.get("current_task_id")
                == "IDS-V0_1-STAGE038-REVIEW"
                and batch_stage.get("acceptance_status")
                == "reviewed_local_passed"
                and (
                    (
                        batch.get("status") == "stage039_phase1_completed"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE039-P1"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE039-P2"
                    )
                    or (
                        batch.get("status") == "stage039_phase2_completed"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE039-P2"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE039-P3"
                    )
                    or (
                        batch.get("status") == "stage039_phase3_completed"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE039-P3"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE039-P4"
                    )
                    or (
                        batch.get("status")
                        == "stage039_phase4_completed_review_pending"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE039-P4"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE039-REVIEW"
                    )
                    or (
                        batch.get("status")
                        == "stage039_completed_reviewed_local"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE039-REVIEW"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE040-P1"
                    )
                    or (
                        batch.get("status") == "stage040_phase1_completed"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE040-P1"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE040-P2"
                    )
                    or (
                        batch.get("status") == "stage040_phase2_completed"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE040-P2"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE040-P3"
                    )
                    or (
                        batch.get("status") == "stage040_phase3_completed"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE040-P3"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE040-P4"
                    )
                    or (
                        batch.get("status")
                        == "stage040_phase4_completed_review_pending"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE040-P4"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-STAGE040-REVIEW"
                    )
                    or (
                        batch.get("status")
                        == "stage040_completed_reviewed_local"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-STAGE040-REVIEW"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
                    )
                    or (
                        batch.get("status")
                        == "reviewed_ready_for_upload_no_github_upload"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
                    )
                    or (
                        batch.get("status")
                        == "local_batch_upload_gate_passed_pending_github_merge"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
                        and decision.get("next_allowed_task_id")
                        == "IDS-V0_1-BATCH-031-040-GITHUB-MERGE"
                    )
                    or (
                        batch.get("status") == "uploaded_to_github_main"
                        and decision.get("current_task_id")
                        == "IDS-V0_1-BATCH-031-040-MAIN-MERGED"
                        and decision.get("next_allowed_task_id")
                        == "IDS-STAGE041-P1-GATE"
                    )
                )
            )
        )
        and batch_stage.get("source_reverification_gate_status") == "passed"
        and (
            (
                batch.get("status")
                in {
                    "local_batch_upload_gate_passed_pending_github_merge",
                    "uploaded_to_github_main",
                }
                and decision.get("github_upload_allowed") is True
                and upload_gate.get("push_allowed") is True
            )
            or (
                batch.get("status")
                not in {
                    "local_batch_upload_gate_passed_pending_github_merge",
                    "uploaded_to_github_main",
                }
                and decision.get("github_upload_allowed") is False
                and upload_gate.get("push_allowed") is False
            )
        ),
        "roadmap_final_state_exact": (
            (
            roadmap.get("current_stage_id") == "IDS-STAGE038"
            and source_gate.get("gate_id")
            == "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"
            and source_gate.get("status") == "passed"
            and source_gate.get("task_id")
            == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"
            and phase2.get("entry_authorized") is True
            and "entry_blocker" not in phase2
            and (
                (
                    roadmap.get("current_phase_id") == "IDS-STAGE038-P1"
                    and roadmap.get("current_task_id")
                    == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"
                    and roadmap.get("next_gate_id") == "IDS-STAGE038-P2-GATE"
                    and phase2.get("status") == "planned"
                )
                or (
                    roadmap.get("current_phase_id") == "IDS-STAGE038-P2"
                    and roadmap.get("current_task_id")
                    == "IDS-V0_1-STAGE038-P2"
                    and roadmap.get("next_gate_id") == "IDS-STAGE038-P3-GATE"
                    and phase2.get("status") == "passed_with_local_evidence"
                    and any(
                        isinstance(task, dict)
                        and task.get("task_id") == "IDS-V0_1-STAGE038-P2"
                        and task.get("status") == "completed"
                        for task in phase2.get("tasks", [])
                    )
                )
                or (
                    roadmap.get("current_phase_id") == "IDS-STAGE038-P3"
                    and roadmap.get("current_task_id")
                    == "IDS-V0_1-STAGE038-P3"
                    and roadmap.get("next_gate_id") == "IDS-STAGE038-P4-GATE"
                    and phase2.get("status") == "passed_with_local_evidence"
                    and phase3.get("status") == "passed_with_local_evidence"
                    and any(
                        isinstance(task, dict)
                        and task.get("task_id") == "IDS-V0_1-STAGE038-P3"
                        and task.get("status") == "completed"
                        for task in phase3.get("tasks", [])
                    )
                )
                or (
                    roadmap.get("current_phase_id") == "IDS-STAGE038-P4"
                    and roadmap.get("current_task_id")
                    == "IDS-V0_1-STAGE038-P4"
                    and roadmap.get("next_gate_id")
                    == "IDS-STAGE038-REVIEW-GATE"
                    and phase2.get("status") == "passed_with_local_evidence"
                    and phase3.get("status") == "passed_with_local_evidence"
                    and phase4.get("status") == "passed_with_local_evidence"
                    and any(
                        isinstance(task, dict)
                        and task.get("task_id") == "IDS-V0_1-STAGE038-P4"
                        and task.get("status") == "completed"
                        for task in phase4.get("tasks", [])
                    )
                )
                or (
                    roadmap.get("current_phase_id") == "IDS-STAGE038-REVIEW"
                    and roadmap.get("current_task_id")
                    == "IDS-V0_1-STAGE038-REVIEW"
                    and roadmap.get("next_gate_id") == "IDS-STAGE039-P1-GATE"
                    and phase2.get("status") == "passed_with_local_evidence"
                    and phase3.get("status") == "passed_with_local_evidence"
                    and phase4.get("status") == "passed_with_local_evidence"
                    and stage_review.get("review_id") == "IDS-STAGE038-REVIEW"
                    and stage_review.get("task_id")
                    == "IDS-V0_1-STAGE038-REVIEW"
                    and stage_review.get("status") == "completed"
                    and "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md"
                    in stage_review.get("evidence_refs", [])
                )
            )
            )
            or (
                roadmap.get("current_stage_id") == "IDS-STAGE039"
                and (
                    (
                        roadmap.get("current_phase_id") == "IDS-STAGE039-P1"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE039-P1"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE039-P2-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id") == "IDS-STAGE039-P2"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE039-P2"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE039-P3-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id") == "IDS-STAGE039-P3"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE039-P3"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE039-P4-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id") == "IDS-STAGE039-P4"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE039-P4"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE039-REVIEW-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id")
                        == "IDS-STAGE039-REVIEW"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE039-REVIEW"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE040-P1-GATE"
                    )
                )
                and source_gate.get("gate_id")
                == "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"
                and source_gate.get("status") == "passed"
                and source_gate.get("task_id")
                == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"
                and source_gate.get("phase2_entry_authorized") is True
                and phase2.get("entry_authorized") is True
                and phase2.get("status") == "passed_with_local_evidence"
                and phase3.get("status") == "passed_with_local_evidence"
                and phase4.get("status") == "passed_with_local_evidence"
                and stage_review.get("review_id") == "IDS-STAGE038-REVIEW"
                and stage_review.get("task_id")
                == "IDS-V0_1-STAGE038-REVIEW"
                and stage_review.get("status") == "completed"
            )
            or (
                roadmap.get("current_stage_id") == "IDS-STAGE040"
                and (
                    (
                        roadmap.get("current_phase_id") == "IDS-STAGE040-P1"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE040-P1"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE040-P2-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id") == "IDS-STAGE040-P2"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE040-P2"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE040-P3-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id") == "IDS-STAGE040-P3"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE040-P3"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE040-P4-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id") == "IDS-STAGE040-P4"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE040-P4"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE040-REVIEW-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id")
                        == "IDS-STAGE040-REVIEW"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-STAGE040-REVIEW"
                        and roadmap.get("next_gate_id")
                        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id")
                        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
                        and roadmap.get("next_gate_id")
                        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
                    )
                    or (
                        roadmap.get("current_phase_id")
                        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
                        and roadmap.get("next_gate_id")
                        == "IDS-V0_1-BATCH-031-040-GITHUB-MERGE"
                    )
                    or (
                        roadmap.get("current_phase_id")
                        == "IDS-V0_1-BATCH-031-040-MAIN-MERGED"
                        and roadmap.get("current_task_id")
                        == "IDS-V0_1-BATCH-031-040-MAIN-MERGED"
                        and roadmap.get("next_gate_id")
                        == "IDS-STAGE041-P1-GATE"
                    )
                )
                and source_gate.get("gate_id")
                == "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"
                and source_gate.get("status") == "passed"
                and source_gate.get("task_id")
                == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"
                and source_gate.get("phase2_entry_authorized") is True
                and phase2.get("entry_authorized") is True
                and phase2.get("status") == "passed_with_local_evidence"
                and phase3.get("status") == "passed_with_local_evidence"
                and phase4.get("status") == "passed_with_local_evidence"
                and stage_review.get("review_id") == "IDS-STAGE038-REVIEW"
                and stage_review.get("task_id")
                == "IDS-V0_1-STAGE038-REVIEW"
                and stage_review.get("status") == "completed"
            )
        ),
        "no_mixed_yaml_state": not any(
            token in batch_text or token in roadmap_text
            for token in mixed_yaml_tokens
        ),
        "no_mixed_markdown_state": not any(
            token in text
            for token in mixed_markdown_tokens
            for text in markdown_surfaces.values()
        ),
    }

SURFACE_PREFIXES = {
    "README": ("KM_IDSystem/README.md",),
    "handoff_docs": ("KM_IDSystem/docs/HANDOFF.md",),
    "governance": ("KM_IDSystem/docs/governance/",),
    "ids_pursuing_goal": ("KM_IDSystem/docs/pursuing_goal/ids_v0_1/",),
    "scripts": ("KM_IDSystem/scripts/",),
    "backend_tests": ("KM_IDSystem/backend/tests/",),
    "backend_app": ("KM_IDSystem/backend/app/",),
    "frontend": ("KM_IDSystem/frontend/",),
    "app_bundle": ("KM_IDSystem/app_bundle/",),
    "product_meta_database": ("KM_IDSystem/product_meta_database/",),
}

REQUIRED_FILES = (
    "KM_IDSystem/README.md",
    "KM_IDSystem/docs/HANDOFF.md",
    "KM_IDSystem/docs/governance/roadmap.yaml",
    "KM_IDSystem/docs/governance/events.jsonl",
    "KM_IDSystem/docs/governance/project.yaml",
    "KM_IDSystem/docs/governance/model_registry.yaml",
    "KM_IDSystem/docs/governance/formula_registry.yaml",
    "KM_IDSystem/docs/governance/parameter_registry.csv",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/batch_review/stage031_040_batch_review_contract.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_batch031_040_review_gate.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE001_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE002_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE003_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE2_GOVERNANCE_REGRESSION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE3_VALIDATION_SCAN.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage003_finance_meta_rename.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage003_finance_meta_rename.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py",
    "KM_IDSystem/product_meta_database/validate_product_meta_database.py",
    "KM_IDSystem/product_meta_database/tests/test_contract.py",
    "KM_IDSystem/backend/tests/test_stage001_naming_contract.py",
    "KM_IDSystem/scripts/check_safe_mode_baseline.py",
    "KM_IDSystem/scripts/check_batch031_040_review.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE2_READONLY_IDENTITY_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE2_FILE_FINGERPRINT_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE2_MANIFEST_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE2_DUPLICATE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE2_IMPORT_IDEMPOTENCY_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE2_REGRESSION_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE2_PREFLIGHT_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE2_RISK_ESTIMATOR_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE2_COST_ESTIMATOR_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE2_PREFLIGHT_CONFIRMATION_UI_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE2_DATA_PRIORITY_QUEUE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE2_PREFLIGHT_SCENARIO_TESTS_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE2_SAFE_EXTRACTION_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE2_SAFE_EXTRACTION_ENGINE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE2_ARCHIVE_MANIFEST_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE2_REINGEST_EXTRACTED_FILES_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE2_ARCHIVE_ADVERSARIAL_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE2_CLEANUP_ALLOWLIST_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE2_POSTGRES_CONTROL_PLANE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE2_SCHEMA_MIGRATION_SAFETY_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_STAGE_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE2_CONNECTION_POOL_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_STAGE_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE2_DATABASE_SIZE_GUARD_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_STAGE_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE2_DATA_RETENTION_TABLE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_STAGE_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE2_DATABASE_RECOVERY_SMOKE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_STAGE_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE2_DATABASE_QUALITY_CONSTRAINTS_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_STAGE_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
    "KM_IDSystem/scripts/check_job_state_model.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_baseline_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_scenarios.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
    "KM_IDSystem/scripts/check_worker_queue_baseline.py",
    "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
    "KM_IDSystem/scripts/check_worker_queue_delivery.py",
    "KM_IDSystem/scripts/check_worker_queue_stage_review.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_runtime.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_scenarios.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_delivery.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_review.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_policy_contract.json",
    "KM_IDSystem/scripts/check_retry_dead_letter_policy.py",
    "KM_IDSystem/scripts/check_retry_dead_letter_runtime.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_policy.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_STAGE_REVIEW.md",
    "KM_IDSystem/scripts/check_retry_dead_letter_stage_review.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_review.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_policy_contract.json",
    "KM_IDSystem/scripts/check_backpressure_policy.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_policy.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_runtime_contract.json",
    "KM_IDSystem/scripts/check_backpressure_runtime.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_runtime.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_scenarios.json",
    "KM_IDSystem/scripts/check_backpressure_scenarios.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_scenarios.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_delivery_contract.json",
    "KM_IDSystem/scripts/check_backpressure_delivery.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_delivery.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_STAGE_REVIEW.md",
    "KM_IDSystem/scripts/check_backpressure_stage_review.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_review.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/stage036_database_quality_constraints_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/002_database_quality_constraints.sql",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/stage036_quality_profile_queries.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_recovery_smoke/stage035_database_recovery_smoke_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/data_retention_table/stage034_data_retention_table_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_original_raw_identity.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_file_fingerprint.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_manifest_generation.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage015_duplicate_detection.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_import_idempotency.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage017_original_regression.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage018_import_preflight.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage019_import_risk_estimator.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage020_import_cost_estimator.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage021_preflight_confirmation_ui.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_data_priority_queue.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_preflight_scenario_tests.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_archive_threat_model.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage025_safe_extraction_engine.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_archive_manifest.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage027_reingest_extracted_files.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage028_archive_adversarial_tests.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage029_archive_cleanup_allowlist.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage030_postgresql_control_plane.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage031_schema_migration_safety.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage032_database_connection_pool.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage033_database_size_guard.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage034_data_retention_table.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage035_database_recovery_smoke.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage036_database_quality_constraints.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_baseline.py",
    "KM_IDSystem/scripts/check_data_retention_table.py",
    "KM_IDSystem/scripts/check_database_recovery_smoke.py",
    "KM_IDSystem/scripts/check_database_quality_constraints.py",
    "KM_IDSystem/scripts/run_stage036_migration_section.py",
    "KM_IDSystem/scripts/check_database_connection_pool.py",
    "KM_IDSystem/scripts/check_original_raw_identity.py",
    "KM_IDSystem/scripts/check_file_fingerprint.py",
    "KM_IDSystem/scripts/check_manifest_generation.py",
    "KM_IDSystem/scripts/check_duplicate_files.py",
    "KM_IDSystem/scripts/check_import_idempotency.py",
    "KM_IDSystem/scripts/check_original_regression.py",
    "KM_IDSystem/scripts/check_import_preflight.py",
    "KM_IDSystem/scripts/check_import_risk_estimator.py",
    "KM_IDSystem/scripts/check_import_cost_estimator.py",
    "KM_IDSystem/scripts/check_preflight_confirmation_ui.py",
    "KM_IDSystem/scripts/check_data_priority_queue.py",
    "KM_IDSystem/scripts/check_preflight_scenario_tests.py",
    "KM_IDSystem/scripts/check_archive_threat_model.py",
    "KM_IDSystem/scripts/check_safe_extraction_engine.py",
    "KM_IDSystem/scripts/check_archive_manifest.py",
    "KM_IDSystem/scripts/check_reingest_extracted_files.py",
    "KM_IDSystem/scripts/check_archive_adversarial_tests.py",
    "KM_IDSystem/scripts/check_archive_cleanup_allowlist.py",
    "KM_IDSystem/scripts/check_postgresql_control_plane.py",
    "KM_IDSystem/scripts/check_schema_migration_safety.py",
    "KM_IDSystem/scripts/check_database_connection_pool.py",
    "KM_IDSystem/scripts/build_app_bundle.sh",
    "KM_IDSystem/scripts/diagnose_app_entry.sh",
    "KM_IDSystem/scripts/run_local_services.sh",
    "KM_IDSystem/scripts/smoke_test.sh",
    "KM_IDSystem/scripts/install_app_entries.sh",
    "KM_IDSystem/scripts/stop_local_services.sh",
)

REQUIRED_EVENT_IDS = (
    "EVT-IDS-V0_1-STAGE001-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE002-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE003-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE004-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE005-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE005-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE005-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE005-P4-20260702-001",
    "EVT-IDS-V0_1-BATCH-001-010-IDS-METADATA-BOUNDARY-20260702-001",
    "EVT-IDS-V0_1-STAGE018-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE018-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE018-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE019-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE019-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE019-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE019-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE020-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE020-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE020-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE020-P4-20260702-001",
    "EVT-IDS-V0_1-BATCH-011-020-REVIEW-GATE-20260702-001",
    "EVT-IDS-V0_1-BATCH-011-020-UPLOAD-GATE-20260702-001",
    "EVT-IDS-V0_1-BATCH-011-020-MAIN-MERGED-20260702-001",
    "EVT-IDS-V0_1-STAGE021-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE021-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE021-P3-20260702-001",
    "EVT-IDS-V0_1-STAGE021-P4-20260702-001",
    "EVT-IDS-V0_1-STAGE022-P1-20260702-001",
    "EVT-IDS-V0_1-STAGE022-P2-20260702-001",
    "EVT-IDS-V0_1-STAGE022-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE022-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE023-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE023-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE023-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE023-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE024-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE024-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE024-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE024-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE025-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE025-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE025-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE025-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE026-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE026-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE026-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE026-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE027-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE027-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE027-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE027-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE028-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE028-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE028-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE028-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE029-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE029-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE029-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE029-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE030-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE030-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE030-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE030-P4-20260703-001",
    "EVT-IDS-V0_1-BATCH-021-030-REVIEW-GATE-20260703-001",
    "EVT-IDS-V0_1-BATCH-021-030-UPLOAD-GATE-20260703-001",
    "EVT-IDS-V0_1-BATCH-021-030-MAIN-MERGED-20260703-001",
    "EVT-IDS-V0_1-STAGE031-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE031-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE031-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE031-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE031-REVIEW-20260703-001",
    "EVT-IDS-V0_1-STAGE031-REVIEW-20260703-002",
    "EVT-IDS-V0_1-STAGE032-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE032-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE032-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE032-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE032-REVIEW-20260703-001",
    "EVT-IDS-V0_1-STAGE033-P1-20260703-001",
    "EVT-IDS-V0_1-STAGE033-P2-20260703-001",
    "EVT-IDS-V0_1-STAGE033-P3-20260703-001",
    "EVT-IDS-V0_1-STAGE033-P4-20260703-001",
    "EVT-IDS-V0_1-STAGE033-REVIEW-20260704-001",
    "EVT-IDS-V0_1-STAGE034-P1-20260704-001",
    "EVT-IDS-V0_1-STAGE034-P2-20260704-001",
    "EVT-IDS-V0_1-STAGE034-P3-20260710-001",
    "EVT-IDS-V0_1-STAGE034-P4-20260710-001",
    "EVT-IDS-V0_1-STAGE034-REVIEW-20260710-001",
    "EVT-IDS-V0_1-STAGE035-P1-20260710-001",
    "EVT-IDS-V0_1-STAGE035-P2-20260710-001",
    "EVT-IDS-V0_1-STAGE035-P3-20260710-001",
    "EVT-IDS-V0_1-STAGE035-P4-20260710-001",
    "EVT-IDS-V0_1-STAGE035-REVIEW-20260710-001",
    "EVT-IDS-V0_1-STAGE036-P1-20260710-001",
    "EVT-IDS-V0_1-STAGE036-P2-20260710-001",
    "EVT-IDS-V0_1-STAGE036-P3-20260710-001",
    "EVT-IDS-V0_1-STAGE036-P4-20260710-001",
    "EVT-IDS-V0_1-STAGE036-REVIEW-20260711-001",
    "EVT-IDS-V0_1-STAGE037-P1-20260711-001",
    "EVT-IDS-V0_1-STAGE037-P2-20260711-001",
    "EVT-IDS-V0_1-STAGE037-P3-20260711-001",
    "EVT-IDS-V0_1-STAGE037-P4-20260711-001",
    "EVT-IDS-V0_1-STAGE037-REVIEW-20260711-001",
    "EVT-IDS-V0_1-STAGE038-P1-20260711-001",
    "EVT-IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY-20260711-001",
    "EVT-IDS-V0_1-STAGE038-P2-20260713-001",
    "EVT-IDS-V0_1-STAGE038-P3-20260713-001",
    "EVT-IDS-V0_1-STAGE038-P4-20260713-001",
    "EVT-IDS-V0_1-STAGE038-REVIEW-20260713-001",
    "EVT-IDS-V0_1-STAGE039-P1-20260713-001",
    "EVT-IDS-V0_1-STAGE039-P2-20260713-001",
    "EVT-IDS-V0_1-STAGE039-P3-20260713-001",
    "EVT-IDS-V0_1-STAGE039-P4-20260713-001",
    "EVT-IDS-V0_1-STAGE039-REVIEW-20260713-001",
    "EVT-IDS-V0_1-STAGE040-P1-20260713-001",
    "EVT-IDS-V0_1-STAGE040-P2-20260713-001",
    "EVT-IDS-V0_1-STAGE040-P3-20260713-001",
    "EVT-IDS-V0_1-STAGE040-P4-20260714-001",
    "EVT-IDS-V0_1-STAGE040-REVIEW-20260714-001",
    "EVT-IDS-V0_1-BATCH031-040-REVIEW-20260714-001",
    "EVT-IDS-V0_1-BATCH-031-040-UPLOAD-GATE-20260714-001",
)

FORBIDDEN_RUNTIME_PREFIXES = (
    "KM_IDSystem/data/",
    "KM_IDSystem/reports/",
    "KM_IDSystem/outputs/",
    "KM_IDSystem/.venv/",
    "KM_IDSystem/frontend/node_modules/",
    "KM_IDSystem/frontend/dist/",
)

ALLOWED_CHANGED_PATHS = {
    "KM_IDSystem/CHANGELOG.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py",
    "KM_IDSystem/docs/HANDOFF.md",
    "KM_IDSystem/docs/governance/DEVELOPMENT_LEDGER.md",
    "KM_IDSystem/docs/governance/DELIVERY_PLAN.md",
    "KM_IDSystem/docs/governance/OWNER_STATUS.md",
    "KM_IDSystem/docs/governance/STATUS.md",
    "KM_IDSystem/docs/governance/TRACEABILITY_MATRIX.csv",
    "KM_IDSystem/docs/governance/VERSION_MATRIX.yaml",
    "KM_IDSystem/docs/governance/delivery_tasks.yaml",
    "KM_IDSystem/docs/governance/development_events.jsonl",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_GATE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/batch_review/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/batch_review/stage031_040_batch_review_contract.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_batch031_040_review_gate.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "KM_IDSystem/scripts/check_safe_mode_baseline.py",
    "KM_IDSystem/scripts/check_manifest_generation.py",
    "KM_IDSystem/scripts/check_duplicate_files.py",
    "KM_IDSystem/scripts/check_import_idempotency.py",
    "KM_IDSystem/scripts/check_original_regression.py",
    "KM_IDSystem/scripts/check_import_preflight.py",
    "KM_IDSystem/scripts/check_import_risk_estimator.py",
    "KM_IDSystem/scripts/check_batch031_040_review.py",
    "KM_IDSystem/scripts/check_import_cost_estimator.py",
    "KM_IDSystem/scripts/check_safe_extraction_engine.py",
    "KM_IDSystem/scripts/check_archive_manifest.py",
    "KM_IDSystem/scripts/check_reingest_extracted_files.py",
    "KM_IDSystem/scripts/check_archive_adversarial_tests.py",
    "KM_IDSystem/scripts/check_archive_cleanup_allowlist.py",
    "KM_IDSystem/scripts/check_postgresql_control_plane.py",
    "KM_IDSystem/scripts/check_schema_migration_safety.py",
    "KM_IDSystem/scripts/check_database_connection_pool.py",
    "KM_IDSystem/scripts/check_database_recovery_smoke.py",
    "KM_IDSystem/scripts/check_database_quality_constraints.py",
    "KM_IDSystem/scripts/check_job_state_model.py",
    "KM_IDSystem/scripts/run_stage036_migration_section.py",
    "KM_IDSystem/scripts/build_app_bundle.sh",
    "KM_IDSystem/scripts/diagnose_app_entry.sh",
    "KM_IDSystem/scripts/install_app_entries.sh",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE2_PREFLIGHT_CONFIRMATION_UI_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage021_preflight_confirmation_ui.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE2_DATA_PRIORITY_QUEUE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_data_priority_queue.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE2_PREFLIGHT_SCENARIO_TESTS_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE3_SCENARIO_VALIDATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_preflight_scenario_tests.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE1_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE2_SAFE_EXTRACTION_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_archive_threat_model.py",
    "KM_IDSystem/scripts/check_preflight_scenario_tests.py",
    "KM_IDSystem/scripts/check_archive_threat_model.py",
    "KM_IDSystem/scripts/check_preflight_confirmation_ui.py",
    "KM_IDSystem/scripts/check_data_priority_queue.py",
    "KM_IDSystem/docs/governance/roadmap.yaml",
    "KM_IDSystem/docs/governance/events.jsonl",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_baseline.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE4_CLOSEOUT.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_baseline_index.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_scenarios.json",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
    "KM_IDSystem/scripts/check_worker_queue_baseline.py",
    "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
    "KM_IDSystem/scripts/check_worker_queue_delivery.py",
    "KM_IDSystem/scripts/check_worker_queue_stage_review.py",
    "KM_IDSystem/scripts/check_retry_dead_letter_policy.py",
    "KM_IDSystem/scripts/check_retry_dead_letter_runtime.py",
    "KM_IDSystem/scripts/check_retry_dead_letter_scenarios.py",
    "KM_IDSystem/scripts/check_retry_dead_letter_delivery.py",
    "KM_IDSystem/scripts/check_retry_dead_letter_stage_review.py",
    "KM_IDSystem/scripts/check_backpressure_delivery.py",
    "KM_IDSystem/scripts/check_backpressure_stage_review.py",
    "KM_IDSystem/docs/governance/project.yaml",
    "KM_IDSystem/docs/governance/model_registry.yaml",
    "KM_IDSystem/docs/governance/formula_registry.yaml",
    "KM_IDSystem/docs/governance/parameter_registry.csv",
    "KM_IDSystem/docs/governance/MODEL_SPEC.md",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_runtime.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_scenarios.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_delivery.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_review.py",
    "KM_IDSystem/功能清单.md",
    "KM_IDSystem/开发记录.md",
    "KM_IDSystem/模型参数文件.md",
}
ALLOWED_CHANGED_PREFIXES = (
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage015_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage017_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage018_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage019_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage020_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage025_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage027_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage028_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage029_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage030_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage031_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage032_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage033_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage034_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage035_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage036_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_",
    "KM_IDSystem/scripts/check_backpressure_policy.py",
    "KM_IDSystem/scripts/check_backpressure_runtime.py",
    "KM_IDSystem/scripts/check_backpressure_scenarios.py",
    "KM_IDSystem/scripts/check_original_raw_identity.py",
    "KM_IDSystem/scripts/check_file_fingerprint.py",
    "KM_IDSystem/scripts/check_database_size_guard.py",
    "KM_IDSystem/scripts/check_data_retention_table.py",
    "KM_IDSystem/scripts/check_database_recovery_smoke.py",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/data_retention_table/",
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_recovery_smoke/",
)


def _repo_root(root: Path) -> Path:
    return root.parent


def _git_ls_files(root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotePath=false", "ls-files", root.name],
            cwd=_repo_root(root),
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return [
            path.relative_to(_repo_root(root)).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        ]
    return [line for line in output.splitlines() if line.strip()]


def _git_changed_paths(root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain"],
            cwd=_repo_root(root),
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line[3:] for line in output.splitlines() if line.strip()]


def _iter_text_files(root: Path, tracked_paths: Iterable[str]) -> Iterable[tuple[str, Path]]:
    repo_root = _repo_root(root)
    for rel_path in tracked_paths:
        path = repo_root / rel_path
        if not path.is_file():
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        yield rel_path, path


def is_forbidden_runtime_path(path: str) -> bool:
    return path.startswith(FORBIDDEN_RUNTIME_PREFIXES)


def _is_allowed_changed_path(path: str) -> bool:
    return path in ALLOWED_CHANGED_PATHS or path.startswith(ALLOWED_CHANGED_PREFIXES)


def classify_governance_error(line: str) -> str:
    root_missing_markers = (
        "[ERROR] root: Missing file: governance/schemas/",
        "[ERROR] root: Missing file: tests/governance/",
        "[ERROR] root: Missing file: .github/",
        "[ERROR] root: Missing file: .agents/",
        "[ERROR] root: Missing file: .codex/",
    )
    registered_project_marker = "Registered project path missing:"
    if line.startswith(root_missing_markers) or registered_project_marker in line:
        return "sparse_worktree_diagnostic"
    if "KM_IDSystem" in line:
        return "project_regression"
    return "other"


def _parse_events(path: Path) -> tuple[list[dict], list[str]]:
    events: list[dict] = []
    errors: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.as_posix()}:{lineno}:{exc.msg}")
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            errors.append(f"{path.as_posix()}:{lineno}:event must be a JSON object")
    return events, errors


def _note_assignment_values(notes: str, field: str) -> list[str]:
    assignment_pattern = rf"(?<![\w]){re.escape(field)}\s*="
    assignment_count = len(re.findall(assignment_pattern, notes, re.I))
    values = re.findall(
        rf"{assignment_pattern}\s*([^,;\s]+?)(?=(?:\.(?:\s|$))|[,;\s]|$)",
        notes,
        re.I,
    )
    if len(values) != assignment_count:
        values.append("<MALFORMED_ASSIGNMENT>")
    return values


def evaluate_required_event_semantics(events: list[dict]) -> list[str]:
    expected_event_keys = {
        "schema_version",
        "event_id",
        "project_id",
        "occurred_at",
        "event_type",
        "summary",
        "fact_level",
        "task_id",
        "acceptance_ids",
        "changed_files",
        "evidence_refs",
        "actor_role",
        "notes",
    }
    event_specs = {
        "EVT-IDS-V0_1-STAGE036-P1-20260710-001": {
            "event_type": "stage_boundary",
            "task_id": "IDS-V0_1-STAGE036-P1",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE1_SCOPE_BOUNDARY.md",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE1_SCOPE_BOUNDARY.md",
            },
        },
        "EVT-IDS-V0_1-STAGE036-P2-20260710-001": {
            "event_type": "stage_slice",
            "task_id": "IDS-V0_1-STAGE036-P2",
            "required_changed_files": {
                "KM_IDSystem/scripts/check_database_quality_constraints.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/stage036_database_quality_constraints_index.json",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/002_database_quality_constraints.sql",
            },
            "required_refs": {
                "KM_IDSystem/scripts/check_database_quality_constraints.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/stage036_database_quality_constraints_index.json",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/002_database_quality_constraints.sql",
            },
        },
        "EVT-IDS-V0_1-STAGE036-P3-20260710-001": {
            "event_type": "validation",
            "task_id": "IDS-V0_1-STAGE036-P3",
            "required_changed_files": {
                "KM_IDSystem/scripts/check_database_quality_constraints.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE3_SCENARIO_VALIDATION.md",
            },
            "required_refs": {
                "KM_IDSystem/scripts/check_database_quality_constraints.py#build_stage036_scenario_validation_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE3_SCENARIO_VALIDATION.md",
            },
        },
        "EVT-IDS-V0_1-STAGE036-P4-20260710-001": {
            "event_type": "stage_closeout",
            "task_id": "IDS-V0_1-STAGE036-P4",
            "required_changed_files": {
                "KM_IDSystem/scripts/check_database_quality_constraints.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/scripts/check_database_quality_constraints.py#build_stage036_delivery_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE4_CLOSEOUT.md",
            },
            "next_gate": "IDS-STAGE036-REVIEW-GATE",
            "exact_runtime_results_required": True,
        },
        "EVT-IDS-V0_1-STAGE036-REVIEW-20260711-001": {
            "event_type": "stage_review",
            "task_id": "IDS-V0_1-STAGE036-REVIEW",
            "required_changed_files": {
                "KM_IDSystem/scripts/check_database_quality_constraints.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_STAGE_REVIEW.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/scripts/check_database_quality_constraints.py#build_stage036_delivery_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_STAGE_REVIEW.md",
            },
            "next_gate": "IDS-STAGE037-P1-GATE",
            "exact_runtime_results_required": True,
        },
        "EVT-IDS-V0_1-STAGE037-P1-20260711-001": {
            "event_type": "stage_boundary",
            "task_id": "IDS-V0_1-STAGE037-P1",
            "acceptance_id": "ACC-STAGE-037",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
            },
        },
        "EVT-IDS-V0_1-STAGE037-P2-20260711-001": {
            "event_type": "stage_slice",
            "task_id": "IDS-V0_1-STAGE037-P2",
            "acceptance_id": "ACC-STAGE-037",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
                "KM_IDSystem/scripts/check_job_state_model.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
                "KM_IDSystem/scripts/check_job_state_model.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
            },
        },
        "EVT-IDS-V0_1-STAGE037-P3-20260711-001": {
            "event_type": "validation",
            "task_id": "IDS-V0_1-STAGE037-P3",
            "acceptance_id": "ACC-STAGE-037",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md",
                "KM_IDSystem/scripts/check_job_state_model.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
                "KM_IDSystem/scripts/check_job_state_model.py#build_stage037_scenario_validation_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
            },
        },
        "EVT-IDS-V0_1-STAGE037-P4-20260711-001": {
            "event_type": "phase_closeout",
            "task_id": "IDS-V0_1-STAGE037-P4",
            "acceptance_id": "ACC-STAGE-037",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
                "KM_IDSystem/scripts/check_job_state_model.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
                "KM_IDSystem/scripts/check_job_state_model.py#build_stage037_delivery_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
            },
            "next_gate": "IDS-STAGE037-REVIEW-GATE",
            "exact_job_runtime_results_required": True,
        },
        "EVT-IDS-V0_1-STAGE037-REVIEW-20260711-001": {
            "event_type": "stage_review",
            "task_id": "IDS-V0_1-STAGE037-REVIEW",
            "acceptance_id": "ACC-STAGE-037",
            "required_changed_files": {
                "KM_IDSystem/scripts/check_job_state_model.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_STAGE_REVIEW.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/scripts/check_job_state_model.py#build_stage037_delivery_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_STAGE_REVIEW.md",
            },
            "next_gate": "IDS-STAGE038-P1-GATE",
            "exact_job_runtime_results_required": True,
        },
        "EVT-IDS-V0_1-STAGE038-P1-20260711-001": {
            "event_type": "stage_boundary",
            "task_id": "IDS-V0_1-STAGE038-P1",
            "acceptance_id": "ACC-STAGE-038",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_baseline.py",
            },
            "required_note_assignments": {
                "source_verification_status": "EXTERNAL_TASKPACK_ABSENT",
                "source_reverification_required_before_phase2": "true",
                "phase2_entry_authorized": "false",
                "live_execution_performed": "false",
                "queue_runtime_performed": "false",
                "worker_runtime_performed": "false",
                "claim_persistence_performed": "false",
                "retry_scheduler_performed": "false",
                "dead_letter_runtime_performed": "false",
                "backpressure_runtime_performed": "false",
                "lock_runtime_performed": "false",
                "automatic_lifecycle_runtime_performed": "false",
                "crash_recovery_runtime_performed": "false",
                "cleanup_runtime_performed": "false",
                "database_connection_performed": "false",
                "schema_change_performed": "false",
                "state_registry_write_performed": "false",
                "source_read_performed": "false",
                "runtime_output_written": "false",
                "real_job_created": "false",
                "fake_ids_business_data_used": "false",
                "raw_metadata_content_accessed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY-20260711-001": {
            "event_type": "source_reverification",
            "task_id": "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY",
            "acceptance_id": "ACC-STAGE-038",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_baseline.py",
            },
            "required_note_assignments": {
                "source_verification_status": "SOURCE_VERIFIED",
                "source_member_match_count": "1",
                "source_member_sha256": "613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634",
                "source_reverification_required_before_phase2": "false",
                "independent_review_status": "passed",
                "phase2_entry_authorized": "true",
                "taskpack_source_read_performed": "true",
                "ids_business_source_read_performed": "false",
                "live_execution_performed": "false",
                "queue_runtime_performed": "false",
                "worker_runtime_performed": "false",
                "claim_persistence_performed": "false",
                "retry_scheduler_performed": "false",
                "dead_letter_runtime_performed": "false",
                "backpressure_runtime_performed": "false",
                "lock_runtime_performed": "false",
                "automatic_lifecycle_runtime_performed": "false",
                "crash_recovery_runtime_performed": "false",
                "cleanup_runtime_performed": "false",
                "database_connection_performed": "false",
                "schema_change_performed": "false",
                "state_registry_write_performed": "false",
                "runtime_output_written": "false",
                "real_job_created": "false",
                "fake_ids_business_data_used": "false",
                "raw_metadata_content_accessed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE038-P2-20260713-001": {
            "event_type": "phase_completed",
            "task_id": "IDS-V0_1-STAGE038-P2",
            "acceptance_id": "ACC-STAGE-038",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_baseline_index.json",
                "KM_IDSystem/scripts/check_worker_queue_baseline.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_runtime.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_baseline_index.json",
                "KM_IDSystem/scripts/check_worker_queue_baseline.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_runtime.py",
            },
            "required_note_assignments": {
                "execution_mode": (
                    "ISOLATED_NON_PRODUCTION_ASYNC_CONTROL_METADATA_SLICE"
                ),
                "contract_valid": "true",
                "slice_valid": "true",
                "queue_runtime_performed": "true",
                "worker_runtime_performed": "true",
                "isolated_control_job_created": "true",
                "capacity_backpressure_signal_verified": "true",
                "production_runtime_activation_performed": "false",
                "claim_persistence_performed": "false",
                "persistent_queue_write_performed": "false",
                "retry_scheduler_performed": "false",
                "dead_letter_runtime_performed": "false",
                "measured_backpressure_runtime_performed": "false",
                "production_lock_runtime_performed": "false",
                "automatic_lifecycle_runtime_performed": "false",
                "crash_recovery_runtime_performed": "false",
                "cleanup_runtime_performed": "false",
                "database_connection_performed": "false",
                "schema_change_performed": "false",
                "state_registry_write_performed": "false",
                "runtime_output_written": "false",
                "ids_business_source_read_performed": "false",
                "external_api_call_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "real_ids_business_job_created": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE038-P3-20260713-001": {
            "event_type": "validation",
            "task_id": "IDS-V0_1-STAGE038-P3",
            "acceptance_id": "ACC-STAGE-038",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_scenarios.json",
                "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_scenarios.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_scenarios.json",
                "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_scenarios.py",
            },
            "required_note_assignments": {
                "execution_mode": "ISOLATED_NON_PRODUCTION_WORKER_QUEUE_SCENARIOS",
                "contract_valid": "true",
                "scenario_validation_valid": "true",
                "scenario_count": "6",
                "isolated_queue_runtime_performed": "true",
                "actual_worker_exception_performed": "true",
                "actual_disk_observation_performed": "true",
                "resource_conflict_result": "RESOURCE_CONFLICT_ACTIVE",
                "physical_drive_removal_performed": "false",
                "disk_allocation_performed": "false",
                "cleanup_runtime_performed": "false",
                "protected_ref_delete_performed": "false",
                "production_runtime_activation_performed": "false",
                "persistent_queue_write_performed": "false",
                "database_connection_performed": "false",
                "schema_change_performed": "false",
                "state_registry_write_performed": "false",
                "runtime_output_written": "false",
                "ids_business_source_read_performed": "false",
                "external_api_call_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "real_ids_business_job_created": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE038-P4-20260713-001": {
            "event_type": "phase_completed",
            "task_id": "IDS-V0_1-STAGE038-P4",
            "acceptance_id": "ACC-STAGE-038",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
                "KM_IDSystem/scripts/check_worker_queue_delivery.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_delivery.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
                "KM_IDSystem/scripts/check_worker_queue_delivery.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_delivery.py",
            },
            "required_note_assignments": {
                "execution_mode": "ISOLATED_NON_PRODUCTION_CLOSEOUT_EVIDENCE",
                "contract_valid": "true",
                "delivery_contract_valid": "true",
                "result": "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED",
                "job_state_count": "11",
                "allowed_transition_count": "21",
                "actual_worker_exception_performed": "true",
                "capacity_backpressure_result": "QUEUE_CAPACITY_REACHED",
                "cleanup_eligible_class_count": "2",
                "automatic_recovery_case_count": "0",
                "orderly_shutdown_proved": "true",
                "production_runtime_activation_performed": "false",
                "claim_persistence_performed": "false",
                "persistent_queue_write_performed": "false",
                "retry_scheduler_performed": "false",
                "dead_letter_runtime_performed": "false",
                "measured_backpressure_runtime_performed": "false",
                "production_lock_runtime_performed": "false",
                "automatic_lifecycle_runtime_performed": "false",
                "crash_recovery_runtime_performed": "false",
                "cleanup_runtime_performed": "false",
                "database_connection_performed": "false",
                "schema_change_performed": "false",
                "state_registry_write_performed": "false",
                "runtime_output_written": "false",
                "ids_business_source_read_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "whole_stage_review_performed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE038-REVIEW-20260713-001": {
            "event_type": "stage_review",
            "task_id": "IDS-V0_1-STAGE038-REVIEW",
            "acceptance_id": "ACC-STAGE-038",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
                "KM_IDSystem/scripts/check_worker_queue_stage_review.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/scripts/check_worker_queue_stage_review.py#build_stage038_review_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
            },
            "required_note_assignments": {
                "review_valid": "true",
                "stage_review_status": "completed_reviewed_local",
                "contract_shape_repairs": "3",
                "external_api_budget_gate_proved": "true",
                "same_operation_resubmission_available": "false",
                "production_runtime_activation_performed": "false",
                "persistent_queue_write_performed": "false",
                "retry_scheduler_performed": "false",
                "automatic_lifecycle_runtime_performed": "false",
                "crash_recovery_runtime_performed": "false",
                "cleanup_runtime_performed": "false",
                "database_connection_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE039-P1-20260713-001": {
            "event_type": "stage_boundary",
            "task_id": "IDS-V0_1-STAGE039-P1",
            "acceptance_id": "ACC-STAGE-039",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_policy_contract.json",
                "KM_IDSystem/scripts/check_retry_dead_letter_policy.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_policy.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_policy_contract.json",
                "KM_IDSystem/scripts/check_retry_dead_letter_policy.py#build_stage039_phase1_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_policy.py",
            },
            "required_note_assignments": {
                "source_verification_status": "SOURCE_VERIFIED",
                "source_member_match_count": "1",
                "source_member_sha256": "504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9",
                "retry_policy_contract_version": "IDS_RETRY_DEAD_LETTER_V0_1_P1",
                "contract_state": "PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED",
                "phase2_entry_authorized": "true",
                "taskpack_source_read_performed": "true",
                "ids_business_source_read_performed": "false",
                "retry_scheduler_performed": "false",
                "dead_letter_runtime_performed": "false",
                "queue_runtime_performed": "false",
                "worker_runtime_performed": "false",
                "database_connection_performed": "false",
                "schema_change_performed": "false",
                "state_registry_write_performed": "false",
                "runtime_output_written": "false",
                "real_ids_business_job_created": "false",
                "fake_ids_business_data_used": "false",
                "external_api_call_performed": "false",
                "raw_metadata_content_accessed": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE039-P2-20260713-001": {
            "event_type": "phase_completed",
            "task_id": "IDS-V0_1-STAGE039-P2",
            "acceptance_id": "ACC-STAGE-039",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_runtime_contract.json",
                "KM_IDSystem/scripts/check_retry_dead_letter_runtime.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_runtime.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_runtime_contract.json",
                "KM_IDSystem/scripts/check_retry_dead_letter_runtime.py#build_stage039_phase2_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_runtime.py",
            },
            "required_note_assignments": {
                "policy_version_id": "IDS_RETRY_POLICY_V0_1_STAGE039_P2",
                "fact_level": "ASSUMPTION",
                "production_calibrated": "false",
                "max_retries": "2",
                "total_attempt_limit": "3",
                "jitter_policy": "DETERMINISTIC_BOUNDED_HASH_JITTER_V1",
                "contract_valid": "true",
                "slice_valid": "true",
                "final_state": "DEAD_LETTERED",
                "final_retry_count": "2",
                "duplicate_admission_increment_count": "0",
                "duplicate_failure_reservation_increment_count": "0",
                "stage038_and_stage039_job_ids_differ": "true",
                "max_retries_mutation_after_creation": "false",
                "resource_pause_consumes_retry": "false",
                "stage038_isolated_admission_performed": "true",
                "database_connection_performed": "false",
                "persistent_queue_write_performed": "false",
                "runtime_output_written": "false",
                "ids_business_source_read_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "real_ids_business_job_created": "false",
                "external_api_call_performed": "false",
                "production_runtime_activation_performed": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE039-P3-20260713-001": {
            "event_type": "phase_completed",
            "task_id": "IDS-V0_1-STAGE039-P3",
            "acceptance_id": "ACC-STAGE-039",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE3_SCENARIO_VALIDATION.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_scenarios.json",
                "KM_IDSystem/scripts/check_retry_dead_letter_scenarios.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_scenarios.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE3_SCENARIO_VALIDATION.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_scenarios.json",
                "KM_IDSystem/scripts/check_retry_dead_letter_scenarios.py#build_stage039_phase3_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_scenarios.py",
            },
            "required_note_assignments": {
                "policy_version_id": "IDS_RETRY_POLICY_V0_1_STAGE039_P2",
                "contract_valid": "true",
                "scenario_validation_valid": "true",
                "scenario_count": "10",
                "passed_scenario_count": "10",
                "actual_worker_exception_performed": "true",
                "actual_disk_observation_performed": "true",
                "process_termination_performed": "false",
                "physical_drive_removal_performed": "false",
                "disk_allocation_performed": "false",
                "external_api_call_performed": "false",
                "cleanup_runtime_performed": "false",
                "protected_ref_delete_performed": "false",
                "persistent_queue_write_performed": "false",
                "database_connection_performed": "false",
                "runtime_output_written": "false",
                "ids_business_source_read_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "real_ids_business_job_created": "false",
                "production_runtime_activation_performed": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE039-P4-20260713-001": {
            "event_type": "phase_completed",
            "task_id": "IDS-V0_1-STAGE039-P4",
            "acceptance_id": "ACC-STAGE-039",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_delivery_contract.json",
                "KM_IDSystem/scripts/check_retry_dead_letter_delivery.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_delivery.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_delivery_contract.json",
                "KM_IDSystem/scripts/check_retry_dead_letter_delivery.py#build_stage039_phase4_delivery_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_delivery.py",
            },
            "required_note_assignments": {
                "policy_version_id": "IDS_RETRY_POLICY_V0_1_STAGE039_P2",
                "contract_valid": "true",
                "delivery_contract_valid": "true",
                "result": "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED",
                "job_type_count": "8",
                "job_state_count": "11",
                "transition_count": "21",
                "attempt_count": "3",
                "final_retry_count": "2",
                "final_state": "DEAD_LETTERED",
                "backpressure_signal_count": "5",
                "cleanup_eligible_class_count": "2",
                "cleanup_protected_class_count": "8",
                "automatic_retry_eligible_code_count": "2",
                "successful_automatic_recovery_case_count": "0",
                "manual_action_case_count": "8",
                "transport_orderly_shutdown_proved": "true",
                "production_runtime_activation_performed": "false",
                "persistent_queue_write_performed": "false",
                "database_connection_performed": "false",
                "runtime_output_written": "false",
                "ids_business_source_read_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "real_ids_business_job_created": "false",
                "measured_backpressure_runtime_performed": "false",
                "production_lock_runtime_performed": "false",
                "automatic_lifecycle_runtime_performed": "false",
                "process_crash_recovery_performed": "false",
                "cleanup_runtime_performed": "false",
                "whole_stage_review_performed": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE039-REVIEW-20260713-001": {
            "event_type": "stage_review",
            "task_id": "IDS-V0_1-STAGE039-REVIEW",
            "acceptance_id": "ACC-STAGE-039",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_STAGE_REVIEW.md",
                "KM_IDSystem/scripts/check_retry_dead_letter_stage_review.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_review.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py",
                "KM_IDSystem/docs/governance/model_registry.yaml",
                "KM_IDSystem/docs/governance/formula_registry.yaml",
                "KM_IDSystem/docs/governance/parameter_registry.csv",
                "KM_IDSystem/docs/governance/MODEL_SPEC.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_STAGE_REVIEW.md",
                "KM_IDSystem/scripts/check_retry_dead_letter_stage_review.py#build_stage039_review_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_review.py",
            },
            "required_note_assignments": {
                "review_valid": "true",
                "stage_review_status": "completed_reviewed_local",
                "registry_model_count": "8",
                "registry_formula_count": "8",
                "registry_parameter_count": "55",
                "active_model_count": "7",
                "active_formula_count": "7",
                "active_parameter_count": "49",
                "manual_rerun_candidate_only": "true",
                "manual_rerun_job_created": "false",
                "production_runtime_activation_performed": "false",
                "persistent_queue_write_performed": "false",
                "database_connection_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE040-P1-20260713-001": {
            "event_type": "stage_boundary",
            "task_id": "IDS-V0_1-STAGE040-P1",
            "acceptance_id": "ACC-STAGE-040",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_policy_contract.json",
                "KM_IDSystem/scripts/check_backpressure_policy.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_policy.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_ENTRY_CONTRACT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_policy_contract.json",
                "KM_IDSystem/scripts/check_backpressure_policy.py#build_stage040_phase1_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_policy.py",
            },
            "required_note_assignments": {
                "source_verification_status": "SOURCE_VERIFIED",
                "source_member_match_count": "1",
                "source_member_sha256": "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d",
                "contract_state": "PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED",
                "phase2_entry_authorized": "true",
                "numeric_policy_values_assigned": "false",
                "taskpack_source_read_performed": "true",
                "ids_business_source_read_performed": "false",
                "raw_metadata_content_accessed": "false",
                "backpressure_runtime_performed": "false",
                "queue_runtime_performed": "false",
                "worker_runtime_performed": "false",
                "lock_runtime_performed": "false",
                "automatic_resume_performed": "false",
                "cleanup_runtime_performed": "false",
                "database_connection_performed": "false",
                "schema_change_performed": "false",
                "state_registry_write_performed": "false",
                "runtime_output_written": "false",
                "real_ids_business_job_created": "false",
                "fake_ids_business_data_used": "false",
                "external_api_call_performed": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE040-P2-20260713-001": {
            "event_type": "phase_completed",
            "task_id": "IDS-V0_1-STAGE040-P2",
            "acceptance_id": "ACC-STAGE-040",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_runtime_contract.json",
                "KM_IDSystem/scripts/check_backpressure_runtime.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_runtime.py",
                "KM_IDSystem/docs/governance/model_registry.yaml",
                "KM_IDSystem/docs/governance/formula_registry.yaml",
                "KM_IDSystem/docs/governance/parameter_registry.csv",
                "KM_IDSystem/docs/governance/MODEL_SPEC.md",
                "KM_IDSystem/docs/governance/project.yaml",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_runtime_contract.json",
                "KM_IDSystem/scripts/check_backpressure_runtime.py#build_stage040_phase2_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_runtime.py",
                "KM_IDSystem/docs/governance/project.yaml",
            },
            "required_note_assignments": {
                "source_verification_status": "SOURCE_VERIFIED",
                "source_member_match_count": "1",
                "source_member_sha256": "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d",
                "contract_state": "PHASE2_ISOLATED_DECISION_SLICE_ENABLED_PRODUCTION_DISABLED",
                "parameter_fact_level": "PROPOSED",
                "production_calibrated": "false",
                "production_calibration_task_id": "TASK-OPME-B-001",
                "isolated_slice_valid": "true",
                "actual_project_disk_observation_performed": "true",
                "backpressure_decision_runtime_performed": "true",
                "phase3_entry_authorized": "true",
                "taskpack_source_read_performed": "true",
                "ids_business_source_read_performed": "false",
                "raw_metadata_content_accessed": "false",
                "queue_runtime_performed": "false",
                "worker_runtime_performed": "false",
                "retry_scheduler_performed": "false",
                "lock_runtime_performed": "false",
                "automatic_resume_performed": "false",
                "cleanup_runtime_performed": "false",
                "database_connection_performed": "false",
                "state_registry_write_performed": "false",
                "runtime_output_written": "false",
                "real_ids_business_job_created": "false",
                "fake_ids_business_data_used": "false",
                "external_api_call_performed": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE040-P3-20260713-001": {
            "event_type": "phase_completed",
            "task_id": "IDS-V0_1-STAGE040-P3",
            "acceptance_id": "ACC-STAGE-040",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE3_SCENARIO_VALIDATION.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_scenarios.json",
                "KM_IDSystem/scripts/check_backpressure_scenarios.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_scenarios.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE3_SCENARIO_VALIDATION.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_scenarios.json",
                "KM_IDSystem/scripts/check_backpressure_scenarios.py#build_stage040_phase3_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_scenarios.py",
            },
            "required_note_assignments": {
                "source_verification_status": "SOURCE_VERIFIED",
                "source_member_match_count": "1",
                "source_member_sha256": "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d",
                "contract_state": "PHASE3_SCENARIOS_ENABLED_PRODUCTION_DISABLED",
                "scenario_validation_valid": "true",
                "scenario_count": "8",
                "passed_scenario_count": "8",
                "actual_isolated_worker_exception_performed": "true",
                "actual_disk_observation_performed": "true",
                "stage038_isolated_worker_exception_replayed": "true",
                "reviewed_control_lock_proof_replayed": "true",
                "phase4_entry_authorized": "true",
                "taskpack_source_read_performed": "true",
                "ids_business_source_read_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "real_ids_business_job_created": "false",
                "process_termination_performed": "false",
                "physical_drive_removal_performed": "false",
                "disk_allocation_performed": "false",
                "external_api_call_performed": "false",
                "cleanup_runtime_performed": "false",
                "protected_ref_delete_performed": "false",
                "stage040_queue_runtime_performed": "false",
                "stage040_worker_runtime_performed": "false",
                "production_lock_runtime_performed": "false",
                "crash_recovery_runtime_performed": "false",
                "production_runtime_activation_performed": "false",
                "persistent_queue_write_performed": "false",
                "database_connection_performed": "false",
                "runtime_output_written": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE040-P4-20260714-001": {
            "event_type": "phase_completed",
            "task_id": "IDS-V0_1-STAGE040-P4",
            "acceptance_id": "ACC-STAGE-040",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_delivery_contract.json",
                "KM_IDSystem/scripts/check_backpressure_delivery.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_delivery.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_delivery_contract.json",
                "KM_IDSystem/scripts/check_backpressure_delivery.py#build_stage040_phase4_delivery_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_delivery.py",
            },
            "required_note_assignments": {
                "source_verification_status": "SOURCE_VERIFIED",
                "source_member_match_count": "1",
                "source_member_sha256": "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d",
                "delivery_contract_schema": "ids.stage040.backpressure.phase4.delivery.v1",
                "contract_state": "PHASE4_CLOSEOUT_EVIDENCE_REVIEW_PENDING",
                "delivery_contract_valid": "true",
                "delivery_result": "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED",
                "required_job_type_count": "8",
                "required_job_state_count": "11",
                "required_terminal_state_count": "4",
                "required_transition_count": "21",
                "required_pressure_signal_count": "7",
                "failure_retry_log_attempt_count": "3",
                "failure_retry_log_retry_count": "2",
                "automatic_recovery_eligible_case_count": "0",
                "successful_automatic_recovery_case_count": "0",
                "reviewed_failure_retry_log_replayed": "true",
                "reviewed_transport_shutdown_replayed": "true",
                "stage_review_status": "pending_next_run",
                "taskpack_source_read_performed": "true",
                "backpressure_decision_runtime_performed": "true",
                "actual_disk_observation_performed": "true",
                "actual_isolated_worker_exception_replayed": "true",
                "ids_business_source_read_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "real_ids_business_job_created": "false",
                "process_termination_performed": "false",
                "physical_drive_removal_performed": "false",
                "disk_allocation_performed": "false",
                "external_api_call_performed": "false",
                "cleanup_runtime_performed": "false",
                "protected_ref_delete_performed": "false",
                "stage040_queue_runtime_performed": "false",
                "stage040_worker_runtime_performed": "false",
                "persistent_queue_write_performed": "false",
                "database_connection_performed": "false",
                "runtime_output_written": "false",
                "measured_throughput_or_fairness_performed": "false",
                "production_lock_runtime_performed": "false",
                "automatic_resume_performed": "false",
                "process_crash_recovery_performed": "false",
                "production_runtime_activation_performed": "false",
                "whole_stage_review_performed": "false",
                "batch_review_performed": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
                "push_allowed": "false",
            },
        },
        "EVT-IDS-V0_1-STAGE040-REVIEW-20260714-001": {
            "event_type": "stage_review",
            "task_id": "IDS-V0_1-STAGE040-REVIEW",
            "acceptance_id": "ACC-STAGE-040",
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_STAGE_REVIEW.md",
                "KM_IDSystem/scripts/check_backpressure_stage_review.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_review.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_STAGE_REVIEW.md",
                "KM_IDSystem/scripts/check_backpressure_stage_review.py#build_stage040_review_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_review.py",
            },
            "required_note_assignments": {
                "review_valid": "true",
                "stage_review_status": "completed_reviewed_local",
                "result": "PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED",
                "finding_count": "3",
                "critical_finding_count": "1",
                "important_finding_count": "2",
                "minor_finding_count": "0",
                "all_findings_repaired": "true",
                "source_integrity_valid": "true",
                "phase1_contract_valid": "true",
                "phase2_slice_valid": "true",
                "phase3_scenarios_valid": "true",
                "phase4_delivery_valid": "true",
                "batch_review_performed": "false",
                "production_runtime_activation_performed": "false",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
                "stage041_started": "false",
                "push_allowed": "false",
                "next_gate": "IDS-V0_1-BATCH-031-040-REVIEW-GATE",
            },
        },
        "EVT-IDS-V0_1-BATCH031-040-REVIEW-20260714-001": {
            "event_type": "batch_review",
            "task_id": "IDS-V0_1-BATCH-031-040-REVIEW-GATE",
            "acceptance_ids": [
                f"ACC-STAGE-{stage:03d}" for stage in range(31, 41)
            ],
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/batch_review/stage031_040_batch_review_contract.json",
                "KM_IDSystem/scripts/check_batch031_040_review.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_batch031_040_review_gate.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/batch_review/stage031_040_batch_review_contract.json",
                "KM_IDSystem/scripts/check_batch031_040_review.py#build_batch031_040_review_report",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_batch031_040_review_gate.py",
            },
            "required_note_assignments": {
                "review_valid": "true",
                "result": "PASS_REVIEWED_READY_FOR_UPLOAD_GATE_NO_GITHUB_UPLOAD",
                "reviewed_stage_count": "10",
                "critical_finding_count": "1",
                "important_finding_count": "2",
                "minor_finding_count": "0",
                "all_findings_repaired": "true",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "production_runtime_activation_performed": "false",
                "github_upload_allowed": "false",
                "app_reinstall_allowed": "false",
                "stage041_started": "false",
                "push_allowed": "false",
                "next_gate": "IDS-V0_1-BATCH-031-040-UPLOAD-GATE",
            },
        },
        "EVT-IDS-V0_1-BATCH-031-040-UPLOAD-GATE-20260714-001": {
            "event_type": "batch_upload_gate",
            "expected_push_allowed": "true",
            "task_id": "IDS-V0_1-BATCH-031-040-UPLOAD-GATE",
            "acceptance_ids": [
                f"ACC-STAGE-{stage:03d}" for stage in range(31, 41)
            ],
            "required_changed_files": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_GATE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            },
            "required_refs": {
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_GATE.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py",
            },
            "required_note_assignments": {
                "local_upload_gate_valid": "true",
                "review_valid": "true",
                "precheck_open_prs": "0",
                "precheck_open_issues": "0",
                "raw_metadata_content_accessed": "false",
                "fake_ids_business_data_used": "false",
                "stage041_started": "false",
                "push_allowed": "true",
                "next_gate": "IDS-V0_1-BATCH-031-040-GITHUB-MERGE",
            },
        },
    }

    errors: list[str] = []
    recognized_events = 0
    for event_id, spec in event_specs.items():
        matching = [
            event
            for event in events
            if isinstance(event, dict) and event.get("event_id") == event_id
        ]
        if not matching:
            continue
        recognized_events += 1
        if len(matching) != 1:
            errors.append(f"{event_id}: expected exactly one event")
            continue

        event = matching[0]
        if set(event) != expected_event_keys:
            errors.append(f"{event_id}: top-level event keys must be exact")
        if (
            event.get("schema_version") != "codexproject.event.v1"
            or event.get("project_id") != "KM_IDSystem"
            or event.get("fact_level") != "VERIFIED"
            or event.get("actor_role") != "Codex"
            or not isinstance(event.get("occurred_at"), str)
            or not isinstance(event.get("summary"), str)
        ):
            errors.append(f"{event_id}: event identity fields are invalid")
        if event.get("event_type") != spec["event_type"]:
            errors.append(
                f"{event_id}: event_type must be {spec['event_type']}"
            )
        if event.get("task_id") != spec["task_id"]:
            errors.append(f"{event_id}: task_id mismatch")
        expected_acceptance_ids = spec.get("acceptance_ids")
        if expected_acceptance_ids is None:
            expected_acceptance_ids = [
                spec.get("acceptance_id", "ACC-STAGE-036")
            ]
        if event.get("acceptance_ids") != expected_acceptance_ids:
            errors.append(
                f"{event_id}: acceptance_ids must bind {expected_acceptance_ids}"
            )

        changed_files = event.get("changed_files")
        changed_files = (
            set(changed_files)
            if isinstance(changed_files, list)
            and all(isinstance(path, str) for path in changed_files)
            else set()
        )
        if not spec["required_changed_files"].issubset(changed_files):
            errors.append(f"{event_id}: required changed_files are incomplete")

        evidence_refs = event.get("evidence_refs")
        evidence_refs = evidence_refs if isinstance(evidence_refs, list) else []
        refs = {
            item.get("ref")
            for item in evidence_refs
            if isinstance(item, dict) and isinstance(item.get("ref"), str)
        }
        if not spec["required_refs"].issubset(refs):
            errors.append(f"{event_id}: required evidence_refs are incomplete")

        notes = event.get("notes")
        notes = notes if isinstance(notes, str) else ""
        push_values = [
            value.lower()
            for value in _note_assignment_values(notes, "push_allowed")
        ]
        expected_push_allowed = spec.get("expected_push_allowed", "false")
        if push_values != [expected_push_allowed]:
            errors.append(
                f"{event_id}: push_allowed must be exactly "
                f"{expected_push_allowed}"
            )

        for field, expected_value in spec.get(
            "required_note_assignments", {}
        ).items():
            values = _note_assignment_values(notes, field)
            if values != [expected_value]:
                errors.append(
                    f"{event_id}: {field} must be exactly {expected_value}"
                )

        if spec.get("exact_job_runtime_results_required"):
            exact_job_runtime_results = {
                field: [
                    value.lower()
                    for value in _note_assignment_values(notes, field)
                ]
                for field in (
                    "live_execution_performed",
                    "queue_runtime_performed",
                    "worker_runtime_performed",
                    "retry_scheduler_performed",
                    "dead_letter_runtime_performed",
                    "backpressure_runtime_performed",
                    "lock_runtime_performed",
                    "automatic_lifecycle_runtime_performed",
                    "crash_recovery_runtime_performed",
                    "cleanup_runtime_performed",
                    "database_connection_performed",
                    "schema_change_performed",
                    "state_registry_write_performed",
                    "runtime_output_written",
                    "real_job_created",
                    "fake_ids_business_data_used",
                    "raw_metadata_content_accessed",
                )
            }
            stage_gate_tokens = [
                value.upper()
                for value in re.findall(
                    r"\bIDS-STAGE\d+-(?:P\d+|REVIEW)-GATE\b",
                    notes,
                    re.I,
                )
            ]
            next_gate_values = [
                value.upper()
                for value in _note_assignment_values(notes, "next_gate")
            ]
            expected_gate = spec["next_gate"]
            if (
                not all(
                    values == ["false"]
                    for values in exact_job_runtime_results.values()
                )
                or stage_gate_tokens != [expected_gate]
                or next_gate_values != [expected_gate]
            ):
                errors.append(
                    f"{event_id}: next-gate or no-job-runtime notes are incomplete"
                )
        elif spec.get("exact_runtime_results_required"):
            exact_runtime_results = {
                field: [
                    value.upper()
                    for value in _note_assignment_values(notes, field)
                ]
                for field in (
                    "live_schema_diff_result",
                    "live_migration_result",
                    "live_constraint_validation_result",
                    "live_recovery_smoke_result",
                )
            }
            stage_gate_tokens = [
                value.upper()
                for value in re.findall(
                    r"\bIDS-STAGE\d+-(?:P\d+|REVIEW)-GATE\b",
                    notes,
                    re.I,
                )
            ]
            next_gate_values = [
                value.upper()
                for value in _note_assignment_values(notes, "next_gate")
            ]
            expected_gate = spec["next_gate"]
            if (
                not all(
                    values == ["NOT_EXECUTED"]
                    for values in exact_runtime_results.values()
                )
                or stage_gate_tokens != [expected_gate]
                or next_gate_values != [expected_gate]
            ):
                errors.append(
                    f"{event_id}: next-gate or no-live notes are incomplete"
                )
        else:
            stage_gate_tokens = re.findall(
                r"\bIDS-STAGE\d+-(?:P\d+|REVIEW)-GATE\b", notes, re.I
            )
            next_gate_values = _note_assignment_values(notes, "next_gate")
            unexpected_live_values = [
                value
                for field in (
                    "live_schema_diff_result",
                    "live_migration_result",
                    "live_constraint_validation_result",
                    "live_recovery_smoke_result",
                )
                for value in _note_assignment_values(notes, field)
            ]
            stage_review_batch_gate_valid = (
                event.get("event_type")
                in {"stage_review", "batch_review", "batch_upload_gate"}
                and not stage_gate_tokens
                and not unexpected_live_values
                and next_gate_values
                == [
                    spec.get("required_note_assignments", {}).get("next_gate")
                ]
            )
            if (
                stage_gate_tokens or next_gate_values or unexpected_live_values
            ) and not stage_review_batch_gate_valid:
                errors.append(
                    f"{event_id}: phase event must not claim gate or live results"
                )

    known_stage_event_ids = {
        stage: {event_id for event_id in event_specs if stage in event_id}
        for stage in ("STAGE037", "STAGE038", "STAGE039", "STAGE040")
    }
    for event in events:
        if not isinstance(event, dict):
            continue
        task_id = event.get("task_id")
        event_id = event.get("event_id")
        if isinstance(task_id, str):
            for stage, known_ids in known_stage_event_ids.items():
                if (
                    task_id.startswith(f"IDS-V0_1-{stage}-")
                    and event_id not in known_ids
                ):
                    errors.append(f"{event_id}: unknown {stage} event")

    if recognized_events == 0:
        errors.append("required staged event: expected exactly one recognized event")
    return errors


def _surface_counts(tracked_paths: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for surface, prefixes in SURFACE_PREFIXES.items():
        counts[surface] = sum(
            1
            for path in tracked_paths
            if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in prefixes)
        )
    return counts


def _text_checks(root: Path, tracked_paths: list[str]) -> dict[str, int]:
    hits = {name: 0 for name in ACCEPTED_NAMES}
    for _rel_path, path in _iter_text_files(root, tracked_paths):
        text = path.read_text(encoding="utf-8")
        for name in ACCEPTED_NAMES:
            hits[name] += text.count(name)
    return hits


def evaluate_current_state_consistency(
    batch_text: str, roadmap_text: str
) -> dict[str, bool]:
    batch = _parse_yaml_text(batch_text)
    roadmap = _parse_yaml_text(roadmap_text)
    current_stage_id = roadmap.get("current_stage_id")
    stage_suffix = (
        current_stage_id.removeprefix("IDS-STAGE")
        if isinstance(current_stage_id, str)
        and current_stage_id.startswith("IDS-STAGE")
        else ""
    )
    stage_key = f"STAGE-{stage_suffix}" if stage_suffix else ""
    stage_prefix = f"stage{stage_suffix}" if stage_suffix else ""
    stage_progress = batch.get("stage_progress")
    stage_progress = stage_progress if isinstance(stage_progress, dict) else {}
    stage_node = stage_progress.get(stage_key)
    stage_node = stage_node if isinstance(stage_node, dict) else {}
    upload_gate = batch.get("upload_gate")
    upload_gate = upload_gate if isinstance(upload_gate, dict) else {}
    decision = batch.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    roadmap_phase = roadmap.get("current_phase_id")
    batch031_040_review_current = (
        current_stage_id == "IDS-STAGE040"
        and roadmap_phase == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and roadmap.get("current_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
    )
    batch031_040_upload_current = (
        current_stage_id == "IDS-STAGE040"
        and roadmap_phase == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and roadmap.get("current_task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
    )
    batch031_040_main_current = (
        current_stage_id == "IDS-STAGE040"
        and roadmap_phase == "IDS-V0_1-BATCH-031-040-MAIN-MERGED"
        and roadmap.get("current_task_id")
        == "IDS-V0_1-BATCH-031-040-MAIN-MERGED"
    )
    batch031_040_gate_current = (
        batch031_040_review_current
        or batch031_040_upload_current
        or batch031_040_main_current
    )
    stage037_phase1_current = (
        current_stage_id == "IDS-STAGE037"
        and roadmap_phase == "IDS-STAGE037-P1"
    )
    stage037_phase2_current = (
        current_stage_id == "IDS-STAGE037"
        and roadmap_phase == "IDS-STAGE037-P2"
    )
    stage037_phase3_current = (
        current_stage_id == "IDS-STAGE037"
        and roadmap_phase == "IDS-STAGE037-P3"
    )
    stage037_phase4_current = (
        current_stage_id == "IDS-STAGE037"
        and roadmap_phase == "IDS-STAGE037-P4"
    )
    stage037_current = (
        stage037_phase1_current
        or stage037_phase2_current
        or stage037_phase3_current
        or stage037_phase4_current
    )
    stage038_phase1_current = (
        current_stage_id == "IDS-STAGE038"
        and roadmap_phase == "IDS-STAGE038-P1"
    )
    stage038_phase2_current = (
        current_stage_id == "IDS-STAGE038"
        and roadmap_phase == "IDS-STAGE038-P2"
    )
    stage038_phase3_current = (
        current_stage_id == "IDS-STAGE038"
        and roadmap_phase == "IDS-STAGE038-P3"
    )
    stage038_phase4_current = (
        current_stage_id == "IDS-STAGE038"
        and roadmap_phase == "IDS-STAGE038-P4"
    )
    stage039_phase1_current = (
        current_stage_id == "IDS-STAGE039"
        and roadmap_phase == "IDS-STAGE039-P1"
    )
    stage039_phase2_current = (
        current_stage_id == "IDS-STAGE039"
        and roadmap_phase == "IDS-STAGE039-P2"
    )
    stage039_phase3_current = (
        current_stage_id == "IDS-STAGE039"
        and roadmap_phase == "IDS-STAGE039-P3"
    )
    stage039_phase4_current = (
        current_stage_id == "IDS-STAGE039"
        and roadmap_phase == "IDS-STAGE039-P4"
    )
    stage040_phase1_current = (
        current_stage_id == "IDS-STAGE040"
        and roadmap_phase == "IDS-STAGE040-P1"
    )
    stage040_phase2_current = (
        current_stage_id == "IDS-STAGE040"
        and roadmap_phase == "IDS-STAGE040-P2"
    )
    stage040_phase3_current = (
        current_stage_id == "IDS-STAGE040"
        and roadmap_phase == "IDS-STAGE040-P3"
    )
    stage040_phase4_current = (
        current_stage_id == "IDS-STAGE040"
        and roadmap_phase == "IDS-STAGE040-P4"
    )
    governed_current = (
        stage037_current
        or stage038_phase1_current
        or stage038_phase2_current
        or stage038_phase3_current
        or stage038_phase4_current
        or stage039_phase1_current
        or stage039_phase2_current
        or stage039_phase3_current
        or stage039_phase4_current
        or stage040_phase1_current
        or stage040_phase2_current
        or stage040_phase3_current
        or stage040_phase4_current
    )

    completed_phases = stage_node.get("completed_phases")
    expected_completed_phase = {
        "IDS-STAGE037-P1": "Phase 1",
        "IDS-STAGE037-P2": "Phase 2",
        "IDS-STAGE037-P3": "Phase 3",
        "IDS-STAGE037-P4": "Phase 4",
        "IDS-STAGE038-P1": "Phase 1",
        "IDS-STAGE038-P2": "Phase 2",
        "IDS-STAGE038-P3": "Phase 3",
        "IDS-STAGE038-P4": "Phase 4",
        "IDS-STAGE039-P1": "Phase 1",
        "IDS-STAGE039-P2": "Phase 2",
        "IDS-STAGE039-P3": "Phase 3",
        "IDS-STAGE039-P4": "Phase 4",
        "IDS-STAGE040-P1": "Phase 1",
        "IDS-STAGE040-P2": "Phase 2",
        "IDS-STAGE040-P3": "Phase 3",
        "IDS-STAGE040-P4": "Phase 4",
    }.get(roadmap_phase)
    batch_current_phase_completed = not governed_current or (
        isinstance(completed_phases, list)
        and expected_completed_phase in completed_phases
    )
    roadmap_stage_node: dict[str, Any] = {}
    roadmap_stages = roadmap.get("stages")
    if isinstance(roadmap_stages, list):
        roadmap_stage_node = next(
            (
                candidate
                for candidate in roadmap_stages
                if isinstance(candidate, dict)
                and candidate.get("stage_id") == current_stage_id
            ),
            {},
        )
    roadmap_phase_node: dict[str, Any] = {}
    roadmap_phases = roadmap_stage_node.get("phases")
    if isinstance(roadmap_phases, list):
        roadmap_phase_node = next(
            (
                candidate
                for candidate in roadmap_phases
                if isinstance(candidate, dict)
                and candidate.get("phase_id") == roadmap_phase
            ),
            {},
        )
    roadmap_phase2_node: dict[str, Any] = {}
    if isinstance(roadmap_phases, list):
        roadmap_phase2_node = next(
            (
                candidate
                for candidate in roadmap_phases
                if isinstance(candidate, dict)
                and candidate.get("phase_id") == "IDS-STAGE038-P2"
            ),
            {},
        )
    source_gate = roadmap_stage_node.get("source_reverification_gate")
    source_gate = source_gate if isinstance(source_gate, dict) else {}
    stage038_source_gate_blocked = (
        stage_node.get("source_verification_status")
        == "EXTERNAL_TASKPACK_ABSENT"
        and stage_node.get("source_reverification_gate_status")
        == "blocked_external_taskpack_absent"
        and stage_node.get("phase2_entry_authorized") is False
        and stage_node.get("next_phase") == "Phase 1 source reverification"
        and stage_node.get("next_gate")
        == "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"
        and decision.get("next_allowed_task_id")
        == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"
        and source_gate.get("gate_id")
        == "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"
        and source_gate.get("status") == "blocked_external_taskpack_absent"
        and source_gate.get("phase2_entry_authorized") is False
        and roadmap_phase2_node.get("entry_authorized") is False
        and roadmap_phase2_node.get("entry_blocker")
        == "source_reverification_required_before_phase2"
    )
    stage038_source_tuple_verified = (
        stage_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage_node.get("source_reverification_gate_status") == "passed"
        and stage_node.get("phase2_entry_authorized") is True
        and source_gate.get("gate_id")
        == "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"
        and source_gate.get("status") == "passed"
        and source_gate.get("task_id")
        == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"
        and source_gate.get("source_verification_status") == "SOURCE_VERIFIED"
        and source_gate.get("source_member_match_count") == 1
        and source_gate.get("source_member_sha256")
        == "613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634"
        and source_gate.get("reconciliation_status") == "passed"
        and source_gate.get("independent_review_status") == "passed"
        and source_gate.get("phase2_entry_authorized") is True
        and roadmap_phase2_node.get("entry_authorized") is True
        and "entry_blocker" not in roadmap_phase2_node
    )
    stage038_source_gate_verified_for_phase1 = (
        stage038_source_tuple_verified
        and stage_node.get("next_phase") == "Phase 2"
        and stage_node.get("next_gate") == "IDS-STAGE038-P2-GATE"
        and decision.get("next_allowed_task_id") == "IDS-V0_1-STAGE038-P2"
    )
    stage038_source_gate_verified_for_phase2 = (
        stage038_source_tuple_verified
        and stage_node.get("status") == "stage038_phase2_completed"
        and stage_node.get("next_phase") == "Phase 3"
        and stage_node.get("next_gate") == "IDS-STAGE038-P3-GATE"
        and decision.get("next_allowed_task_id") == "IDS-V0_1-STAGE038-P3"
    )
    stage038_source_gate_verified_for_phase3 = (
        stage038_source_tuple_verified
        and stage_node.get("status") == "stage038_phase3_completed"
        and stage_node.get("next_phase") == "Phase 4"
        and stage_node.get("next_gate") == "IDS-STAGE038-P4-GATE"
        and decision.get("next_allowed_task_id") == "IDS-V0_1-STAGE038-P4"
    )
    stage038_source_gate_verified_for_phase4 = (
        stage038_source_tuple_verified
        and stage_node.get("status")
        == "stage038_phase4_completed_review_pending"
        and stage_node.get("review_status") == "pending"
        and stage_node.get("next_phase") == "stage_review"
        and stage_node.get("next_gate") == "IDS-STAGE038-REVIEW-GATE"
        and decision.get("next_allowed_task_id")
        == "IDS-V0_1-STAGE038-REVIEW"
    )
    stage038_source_gate_consistent = (
        not stage038_phase1_current
        and not stage038_phase2_current
        and not stage038_phase3_current
        and not stage038_phase4_current
    ) or (
        stage038_source_gate_blocked
        or stage038_source_gate_verified_for_phase1
        or stage038_source_gate_verified_for_phase2
        or stage038_source_gate_verified_for_phase3
        or stage038_source_gate_verified_for_phase4
    )
    roadmap_current_phase_passed = not governed_current or (
        roadmap_phase_node.get("status") == "passed_with_local_evidence"
    )
    roadmap_task_node: dict[str, Any] = {}
    roadmap_tasks = roadmap_phase_node.get("tasks")
    roadmap_task = roadmap.get("current_task_id")
    if isinstance(roadmap_tasks, list):
        roadmap_task_node = next(
            (
                candidate
                for candidate in roadmap_tasks
                if isinstance(candidate, dict)
                and candidate.get("task_id") == roadmap_task
            ),
            {},
        )
    roadmap_current_task_completed = not governed_current or (
        roadmap_task_node.get("status") == "completed"
    )
    batch031_040_review_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/batch_review/stage031_040_batch_review_contract.json",
        "KM_IDSystem/scripts/check_batch031_040_review.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_batch031_040_review_gate.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
    }
    batch031_040_review_acceptance_ids = [
        f"ACC-STAGE-{stage:03d}" for stage in range(31, 41)
    ]
    batch031_040_review_consistent = not batch031_040_review_current or (
        batch.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch.get("status")
        == "reviewed_ready_for_upload_no_github_upload"
        and batch.get("review_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and batch.get("review_evidence_ref")
        == "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md"
        and upload_gate.get("push_allowed") is False
        and upload_gate.get("review_gate") == "BATCH031_040_REVIEW_GATE"
        and upload_gate.get("gate_task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and decision.get("current_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and decision.get("next_allowed_task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and decision.get("github_upload_allowed") is False
        and roadmap.get("next_gate_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and roadmap_phase_node.get("status") == "completed"
        and roadmap_task_node.get("task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and roadmap_task_node.get("status") == "completed"
        and roadmap_task_node.get("acceptance_ids")
        == batch031_040_review_acceptance_ids
        and batch031_040_review_evidence.issubset(
            {
                item
                for item in roadmap_task_node.get("evidence_refs", [])
                if isinstance(item, str)
            }
        )
        and all(
            isinstance(stage_progress.get(f"STAGE-{stage:03d}"), dict)
            and stage_progress[f"STAGE-{stage:03d}"].get("status")
            == "completed_reviewed_local"
            and stage_progress[f"STAGE-{stage:03d}"].get("review_status")
            == "passed"
            for stage in range(31, 41)
        )
    )
    batch031_040_upload_consistent = not batch031_040_upload_current or (
        batch.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch.get("status")
        == "local_batch_upload_gate_passed_pending_github_merge"
        and batch.get("review_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and batch.get("review_evidence_ref")
        == "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md"
        and upload_gate.get("push_allowed") is True
        and upload_gate.get("review_gate") == "BATCH031_040_REVIEW_GATE"
        and upload_gate.get("gate_task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and upload_gate.get("gate_evidence_ref")
        == "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_GATE.md"
        and decision.get("current_task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and decision.get("next_allowed_task_id")
        == "IDS-V0_1-BATCH-031-040-GITHUB-MERGE"
        and decision.get("github_upload_allowed") is True
        and roadmap.get("next_gate_id")
        == "IDS-V0_1-BATCH-031-040-GITHUB-MERGE"
        and roadmap_phase_node.get("status")
        == "passed_pending_github_merge"
        and roadmap_task_node.get("task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and roadmap_task_node.get("status") == "passed_pending_github_merge"
        and roadmap_task_node.get("acceptance_ids")
        == batch031_040_review_acceptance_ids
        and all(
            isinstance(stage_progress.get(f"STAGE-{stage:03d}"), dict)
            and stage_progress[f"STAGE-{stage:03d}"].get("status")
            == "completed_reviewed_local"
            and stage_progress[f"STAGE-{stage:03d}"].get("review_status")
            == "passed"
            for stage in range(31, 41)
        )
    )
    batch031_040_main_consistent = not batch031_040_main_current or (
        batch.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch.get("status") == "uploaded_to_github_main"
        and batch.get("review_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and batch.get("review_evidence_ref")
        == "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md"
        and upload_gate.get("push_allowed") is True
        and upload_gate.get("gate_task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and upload_gate.get("gate_evidence_ref")
        == "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_GATE.md"
        and isinstance(upload_gate.get("github_pr"), str)
        and re.fullmatch(
            r"https://github\.com/LinzeColin/CodexProject/pull/\d+",
            upload_gate["github_pr"],
        )
        is not None
        and isinstance(upload_gate.get("merged_sha"), str)
        and re.fullmatch(r"[0-9a-f]{40}", upload_gate["merged_sha"])
        is not None
        and upload_gate.get("post_merge_open_prs") == 0
        and upload_gate.get("post_merge_open_issues") == 0
        and decision.get("current_task_id")
        == "IDS-V0_1-BATCH-031-040-MAIN-MERGED"
        and decision.get("next_allowed_task_id") == "IDS-STAGE041-P1-GATE"
        and decision.get("github_upload_allowed") is True
        and roadmap.get("next_gate_id") == "IDS-STAGE041-P1-GATE"
        and roadmap_phase_node.get("status") == "completed"
        and roadmap_task_node.get("task_id")
        == "IDS-V0_1-BATCH-031-040-MAIN-MERGED"
        and roadmap_task_node.get("status") == "completed"
        and roadmap_task_node.get("acceptance_ids")
        == batch031_040_review_acceptance_ids
    )
    batch031_040_gate_consistent = (
        batch031_040_review_consistent
        and batch031_040_upload_consistent
        and batch031_040_main_consistent
    )
    task_results = roadmap_task_node.get("test_results")
    expected_stage037_phase1_result_block = (
        "GREEN: Stage037 8 tests OK, Stage005 134 tests OK, "
        "Stage031-037 aggregate 138 tests OK, Stage026-030 75 tests OK, "
        "full IDS v0.1 discovery 532 tests OK, Stage005 validator valid=true"
    )
    expected_stage037_phase2_result_block = (
        "GREEN: Stage037 Phase2 8 tests OK, Stage037 aggregate 16 tests OK, "
        "Stage005 135 tests OK, Stage031-037 aggregate 146 tests OK, "
        "Stage026-030 75 tests OK, full IDS v0.1 discovery 541 tests OK, "
        "checker contract_valid=true, Stage005 validator valid=true"
    )
    expected_stage037_phase3_result_block = (
        "GREEN: Stage037 Phase3 6 tests OK, Stage037 aggregate 22 tests OK, "
        "Stage005 136 tests OK, Stage031-037 aggregate 152 tests OK, "
        "Stage026-030 75 tests OK, full IDS v0.1 discovery 548 tests OK, "
        "checker scenario_validation_valid=true, Stage005 validator valid=true; "
        "independent Phase 3 review found 0 Critical and 6 Important issues, "
        "all six were repaired, and final re-review found 0 Critical, "
        "0 Important, and 0 Minor issues with Ready for local commit=Yes"
    )
    expected_stage037_phase4_result_block = (
        "GREEN: Stage037 Phase4 7 tests OK, Stage037 aggregate 29 tests OK, "
        "Stage005 137 tests OK, Stage031-037 aggregate 159 tests OK, "
        "Stage026-030 75 tests OK, full IDS v0.1 discovery 556 tests OK, "
        "checker delivery_contract_valid=true, Stage005 validator valid=true"
    )
    expected_stage038_phase1_result_block = (
        "GREEN: Stage038 8 tests OK, Stage005 140 tests OK, "
        "Stage031-038 aggregate 177 tests OK, Stage026-030 75 tests OK, "
        "full IDS v0.1 discovery 577 tests OK, Stage005 validator valid=true"
    )
    expected_stage038_source_reverification_result_block = (
        "GREEN: Stage038 8 tests OK, Stage005 142 tests OK, "
        "Stage031-038 aggregate 177 tests OK, Stage026-030 75 tests OK, "
        "full IDS v0.1 discovery 579 tests OK, Stage005 validator valid=true"
    )
    expected_stage038_phase2_result_block = (
        "GREEN: Stage038 17 tests OK, Stage005 143 tests OK, "
        "Stage031-038 aggregate 186 tests OK, Stage026-030 75 tests OK, "
        "full IDS v0.1 discovery 589 tests OK, "
        "checker contract_valid=true slice_valid=true, "
        "Stage005 validator valid=true"
    )
    expected_stage038_phase3_result_block = (
        "GREEN: Stage038 25 tests OK, Stage005 144 tests OK, "
        "Stage031-038 aggregate 194 tests OK, Stage026-030 75 tests OK, "
        "full IDS v0.1 discovery 598 tests OK, "
        "checker contract_valid=true scenario_validation_valid=true, "
        "scoped Stage005 validator valid=true; direct workspace report blocked "
        "only by four pre-existing owner dirty paths"
    )
    expected_stage038_phase4_result_block = (
        "GREEN: Stage038 33 tests OK, Stage005 145 tests OK, "
        "Stage031-038 aggregate 202 tests OK, Stage026-030 75 tests OK, "
        "full IDS v0.1 discovery 607 tests OK, "
        "checker contract_valid=true delivery_contract_valid=true, "
        "scoped Stage005 validator valid=true; direct workspace report blocked "
        "only by four pre-existing owner dirty paths"
    )
    expected_stage039_phase1_result_block = (
        "TDD RED: Stage039 10 tests produced 12 failures and 1 error because "
        "the Phase1 contract, checker, documents, and governance route did "
        "not exist. GREEN: Stage039 10 tests OK; Stage005 146 tests OK; "
        "Stage031-039 aggregate 217 tests OK; Stage026-030 compatibility "
        "75 tests OK; full IDS v0.1 discovery 623 tests OK; checker returned "
        "17/17 contract checks true and phase1_contract_valid=true. "
        "Retry/dead-letter, queue/worker, database/schema, raw metadata, fake "
        "IDS business data, runtime output, GitHub, app reinstall, Phase2, "
        "Stage040, stage review, and batch gates were not executed. Direct "
        "Stage005 failed closed only on the four preserved owner dirty paths "
        "while scoped Stage005 valid=true; 183 events parsed with zero "
        "duplicate ids and one Stage039 Phase1 event; 9 staged Python files "
        "compiled in memory; owner render drift/reference counts zero; git "
        "diff check passed; changed-only governance errors=0 and warnings=0. "
        "Full semantic validation returned only the expected 29 sparse-"
        "worktree missing root/unrelated-project paths, so sparse scope was "
        "not expanded."
    )
    expected_stage039_phase2_result_block = (
        "TDD RED: Stage039 Phase2 10 tests failed because the runtime checker "
        "and contract did not exist. GREEN: Stage039 20 tests OK; Stage005 "
        "146 tests OK; Stage031-039 aggregate 227 tests OK; Stage026-030 "
        "compatibility 75 tests OK; full IDS v0.1 discovery 633 tests OK; "
        "checker returned contract_valid=true and slice_valid=true. The "
        "isolated metadata path completed two retry admissions with exact "
        "idempotent replay and then DEAD_LETTERED at retry_count=2. Production "
        "runtime, persistence, database, raw metadata, fake IDS business data, "
        "runtime output, external API, GitHub, app reinstall, Phase3, Stage040, "
        "stage review, and batch gates were not executed. Scoped Stage005 "
        "validator valid=true; final layered validation details are recorded "
        "in the Phase2 evidence and event."
    )
    expected_stage039_phase3_result_block = (
        "TDD RED: Stage039 Phase3 11 tests failed because the contract, "
        "checker, evidence, and governance route did not exist. GREEN: "
        "checker 14/14 contract checks true and 10/10 scenarios passed; "
        "Stage039 31 tests OK; Stage005 146 tests OK; Stage031-039 aggregate "
        "238 tests OK; Stage026-030 compatibility 75 tests OK; full IDS v0.1 "
        "discovery 644 tests OK. Actual isolated worker exception and actual "
        "disk-free observation reused the reviewed Stage038 boundary; process "
        "termination, physical drive removal, disk allocation, external API "
        "call, cleanup/delete, persistence, database, raw metadata, fake IDS "
        "business data, production, GitHub, app reinstall, Phase4, Stage040, "
        "stage review, and batch gates were not executed. Scoped Stage005 "
        "validator valid=true. Pre-commit self-review repaired one Important "
        "ambiguity by changing a candidate-only manual rerun from "
        "job_state=CREATED to proposed_initial_state=CREATED. Final layered "
        "validation details are recorded in the Phase3 evidence and event."
    )
    expected_stage039_phase4_result_block = (
        "TDD RED: Stage039 Phase4 10/10 tests failed because the delivery "
        "contract, checker, closeout, and governance route did not exist. "
        "GREEN: checker 14/14 contract checks and 7/7 delivery checks true; "
        "Stage039 41 tests OK; Stage005 146 tests OK; Stage031-039 aggregate "
        "248 tests OK; Stage026-030 compatibility 75 tests OK; full IDS v0.1 "
        "discovery 654 tests OK. The report binds the exact 8-type/11-state/"
        "21-transition graph, actual three-attempt retry/dead-letter log, five "
        "backpressure signals, two-class cleanup allowlist, zero observed "
        "successful automatic recovery cases, eight manual-action cases, "
        "reviewed transport shutdown, and fail-closed rollback. No production, "
        "persistence, database, raw metadata, fake IDS business data, "
        "Stage040-044 runtime ownership, whole-stage review, GitHub, or app "
        "reinstall ran. Scoped Stage005 validator valid=true and changed-only "
        "governance returned errors=0/warnings=0. Project-wide Lean semantic "
        "validation retained 29 sparse root/unrelated-path diagnostics and 21 "
        "pre-existing Stage039 Phase2 registry/schema/count diagnostics; these "
        "are mandatory whole-stage review inputs, and sparse scope was not "
        "expanded. Pre-commit implementation review repaired one Important "
        "fail-closed gap so non-object delivery_contract tampering returns a "
        "structured blocked report. Final layered validation details are "
        "recorded in the Phase4 evidence and event."
    )
    expected_stage040_phase1_result_block = (
        "TDD RED: Stage040 10 tests produced 12 failures and 1 error because "
        "the Phase1 contract, checker, documents, and governance route did "
        "not exist. GREEN: checker 20/20 contract checks true; Stage040 10 "
        "tests OK; Stage005 146 tests OK; Stage037 39 tests OK; Stage038 "
        "review 5 tests OK; Stage039 review 6 tests OK; Stage026-030 "
        "compatibility 75 tests OK; full IDS v0.1 discovery 671 tests OK. "
        "Direct Stage005 failed closed only on the four preserved owner dirty "
        "paths while scoped Stage005 valid=true; 188 events parsed with zero "
        "duplicate ids and one Stage040 Phase1 event; owner render drift/"
        "reference counts zero; git diff checks passed; changed-only "
        "governance errors=0 and warnings=0. Full semantic validation returned "
        "only the expected 29 sparse-worktree missing root/unrelated-project "
        "paths, so sparse scope was not expanded. No backpressure/queue/worker/"
        "lock/resume/cleanup runtime, database, raw metadata, fake IDS business "
        "data, GitHub, app reinstall, Phase2, stage review, or batch gate ran."
    )
    expected_stage040_phase2_result_block = (
        "TDD RED: Stage040 Phase2 15 tests produced 17 failures and 1 error "
        "because the contract, checker, evidence, registry entries, and governance "
        "transition did not exist. GREEN: checker 18/18 contract checks and 8/8 "
        "slice checks true; Stage040 Phase2 15 tests OK; Stage040 aggregate 25 "
        "tests OK; Stage005 147 tests OK; Stage037 39 tests OK; Stage038 review 5 "
        "tests OK; Stage039 review 6 tests OK; Stage031-039 aggregate 254 tests "
        "OK; Stage026-030 compatibility 75 tests OK; full IDS v0.1 discovery 687 "
        "tests OK. Stage004 legacy scan valid=true after repairing one active-"
        "display identifier construction; direct Stage005 failed closed only on "
        "the four preserved owner dirty paths while scoped Stage005 valid=true; "
        "189 events parsed with zero duplicate ids and one Stage040 Phase2 event; "
        "owner render drift/reference counts zero; git diff checks passed; changed-"
        "only governance errors=0 and warnings=0. The repository-wide semantic "
        "HEAD baseline also returned errors=0 and warnings=0 but reported "
        "changed_files:none, so it is not used as staged-change proof. Self-review "
        "repaired Stage039 planned-registry growth/current-phase compatibility and "
        "the resulting hash chain. No queue, worker, retry scheduler, lock, resume, "
        "cleanup, persistence, database, raw metadata, fake IDS business data, "
        "external API, production, GitHub, app reinstall, Phase3, stage review, or "
        "batch gate ran."
    )
    expected_stage040_phase3_result_block = (
        "TDD RED: Stage040 Phase3 11/11 tests failed because the scenario "
        "contract, checker, evidence, and governance transition did not exist. "
        "GREEN: checker 18/18 contract checks and 8/8 scenarios true; Stage040 "
        "Phase3 11 tests OK; Stage040 aggregate 36 tests OK; Stage005 148 tests "
        "OK; Stage037 39 tests OK; Stage038 review 5 tests OK; Stage039 review 6 "
        "tests OK; Stage031-039 aggregate 254 tests OK; Stage026-030 compatibility "
        "75 tests OK; full IDS v0.1 discovery 699 tests OK. Stage004 legacy scan "
        "valid=true; direct Stage005 failed closed only on the four preserved "
        "owner dirty paths while scoped Stage005 valid=true; 190 events parsed "
        "with zero duplicate ids and one Stage040 Phase3 event; owner render "
        "drift/reference counts zero; git diff checks passed; changed-only "
        "governance errors=0 and warnings=0. Self-review repaired one Important "
        "machine-truth gap by exposing the Stage038 worker-exception replay and "
        "reviewed lock-proof replay flags in the Phase3 report. No Stage040 queue/"
        "worker runtime, process termination, physical drive removal, disk "
        "allocation, external API call, cleanup/delete, production lock, crash "
        "recovery, persistence, database, raw metadata, fake IDS business data, "
        "production, GitHub, app reinstall, Phase4, stage review, or batch gate "
        "ran."
    )
    expected_stage040_phase4_result_block = (
        "TDD RED: Stage040 Phase4 10/10 tests failed because the checker, contract, "
        "closeout evidence, and governance route did not exist. GREEN: checker 14/14 "
        "contract checks and 8/8 delivery checks true; Stage040 Phase4 10 tests OK; "
        "Stage040 aggregate 46 tests OK; Stage005 149 tests OK; Stage031-039 aggregate "
        "254 tests OK; Stage026-030 compatibility 75 tests OK; full IDS v0.1 discovery "
        "710 tests OK. Direct Stage005 failed closed only on the four preserved owner "
        "dirty paths while scoped Stage005 valid=true; 191 events parsed with zero "
        "duplicate ids and one Stage040 Phase4 event; owner render drift/reference "
        "counts zero; git diff checks passed; changed-only governance errors=0 and "
        "warnings=0. Implementation self-review repaired dotted-schema note parsing "
        "and the missing checker changed-path allowlist. No Stage040 queue/worker "
        "runtime, process termination, physical drive removal, disk allocation, "
        "external API call, cleanup/delete, production lock, automatic resume, crash "
        "recovery, persistence, database, raw metadata, fake IDS business data, "
        "production, GitHub, issue mutation, app reinstall, whole-stage review, or "
        "batch gate ran."
    )
    expected_governed_result_block = {
        "IDS-STAGE037-P1": expected_stage037_phase1_result_block,
        "IDS-STAGE037-P2": expected_stage037_phase2_result_block,
        "IDS-STAGE037-P3": expected_stage037_phase3_result_block,
        "IDS-STAGE037-P4": expected_stage037_phase4_result_block,
        "IDS-STAGE038-P1": expected_stage038_phase1_result_block,
        "IDS-STAGE038-P2": expected_stage038_phase2_result_block,
        "IDS-STAGE038-P3": expected_stage038_phase3_result_block,
        "IDS-STAGE038-P4": expected_stage038_phase4_result_block,
        "IDS-STAGE039-P1": expected_stage039_phase1_result_block,
        "IDS-STAGE039-P2": expected_stage039_phase2_result_block,
        "IDS-STAGE039-P3": expected_stage039_phase3_result_block,
        "IDS-STAGE039-P4": expected_stage039_phase4_result_block,
        "IDS-STAGE040-P1": expected_stage040_phase1_result_block,
        "IDS-STAGE040-P2": expected_stage040_phase2_result_block,
        "IDS-STAGE040-P3": expected_stage040_phase3_result_block,
        "IDS-STAGE040-P4": expected_stage040_phase4_result_block,
    }.get(roadmap_phase)
    if roadmap_task == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY":
        expected_governed_result_block = (
            expected_stage038_source_reverification_result_block
        )
    roadmap_current_task_results_recorded = not governed_current or (
        task_results == expected_governed_result_block
    )
    required_stage037_phase1_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_ENTRY_CONTRACT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage037_phase2_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
        "KM_IDSystem/scripts/check_job_state_model.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage037_phase3_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
        "KM_IDSystem/scripts/check_job_state_model.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage037_phase4_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE4_CLOSEOUT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
        "KM_IDSystem/scripts/check_job_state_model.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage038_phase1_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_baseline.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage038_source_reverification_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_baseline.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage038_phase2_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_baseline_index.json",
        "KM_IDSystem/scripts/check_worker_queue_baseline.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_runtime.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage038_phase3_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_baseline_index.json",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_scenarios.json",
        "KM_IDSystem/scripts/check_worker_queue_baseline.py",
        "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_runtime.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_scenarios.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage038_phase4_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE4_CLOSEOUT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_baseline_index.json",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_scenarios.json",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
        "KM_IDSystem/scripts/check_worker_queue_baseline.py",
        "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
        "KM_IDSystem/scripts/check_worker_queue_delivery.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_runtime.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_scenarios.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_delivery.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage039_phase1_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_ENTRY_CONTRACT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_policy_contract.json",
        "KM_IDSystem/scripts/check_retry_dead_letter_policy.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_policy.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage039_phase2_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_policy_contract.json",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_runtime_contract.json",
        "KM_IDSystem/scripts/check_retry_dead_letter_policy.py",
        "KM_IDSystem/scripts/check_retry_dead_letter_runtime.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_policy.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_runtime.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage039_phase3_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE3_SCENARIO_VALIDATION.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_scenarios.json",
        "KM_IDSystem/scripts/check_retry_dead_letter_scenarios.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_scenarios.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage039_phase4_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE3_SCENARIO_VALIDATION.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE4_CLOSEOUT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_delivery_contract.json",
        "KM_IDSystem/scripts/check_retry_dead_letter_delivery.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage039_retry_dead_letter_delivery.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage040_phase1_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_ENTRY_CONTRACT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_policy_contract.json",
        "KM_IDSystem/scripts/check_backpressure_policy.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_policy.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage040_phase2_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_runtime_contract.json",
        "KM_IDSystem/scripts/check_backpressure_runtime.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_runtime.py",
        "KM_IDSystem/docs/governance/model_registry.yaml",
        "KM_IDSystem/docs/governance/formula_registry.yaml",
        "KM_IDSystem/docs/governance/parameter_registry.csv",
        "KM_IDSystem/docs/governance/MODEL_SPEC.md",
        "KM_IDSystem/docs/governance/project.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage040_phase3_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE3_SCENARIO_VALIDATION.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_scenarios.json",
        "KM_IDSystem/scripts/check_backpressure_scenarios.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_scenarios.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_stage040_phase4_evidence = {
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE3_SCENARIO_VALIDATION.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE4_CLOSEOUT.md",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_delivery_contract.json",
        "KM_IDSystem/scripts/check_backpressure_delivery.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage040_backpressure_delivery.py",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
    }
    required_governed_evidence = {
        "IDS-STAGE037-P1": required_stage037_phase1_evidence,
        "IDS-STAGE037-P2": required_stage037_phase2_evidence,
        "IDS-STAGE037-P3": required_stage037_phase3_evidence,
        "IDS-STAGE037-P4": required_stage037_phase4_evidence,
        "IDS-STAGE038-P1": required_stage038_phase1_evidence,
        "IDS-STAGE038-P2": required_stage038_phase2_evidence,
        "IDS-STAGE038-P3": required_stage038_phase3_evidence,
        "IDS-STAGE038-P4": required_stage038_phase4_evidence,
        "IDS-STAGE039-P1": required_stage039_phase1_evidence,
        "IDS-STAGE039-P2": required_stage039_phase2_evidence,
        "IDS-STAGE039-P3": required_stage039_phase3_evidence,
        "IDS-STAGE039-P4": required_stage039_phase4_evidence,
        "IDS-STAGE040-P1": required_stage040_phase1_evidence,
        "IDS-STAGE040-P2": required_stage040_phase2_evidence,
        "IDS-STAGE040-P3": required_stage040_phase3_evidence,
        "IDS-STAGE040-P4": required_stage040_phase4_evidence,
    }.get(roadmap_phase, set())
    if roadmap_task == "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY":
        required_governed_evidence = (
            required_stage038_source_reverification_evidence
        )
    task_evidence = roadmap_task_node.get("evidence_refs")
    roadmap_current_task_evidence_recorded = not governed_current or (
        isinstance(task_evidence, list)
        and required_governed_evidence.issubset(
            {item for item in task_evidence if isinstance(item, str)}
        )
    )

    if not stage_node:
        return {
            "yaml_documents_parsed": bool(batch) and bool(roadmap),
            "current_stage_node_resolved": False,
            "batch_top_status_matches_stage": True,
            "batch_stage_task_matches_roadmap": True,
            "batch_stage_gate_matches_roadmap": True,
            "roadmap_phase_matches_stage": True,
            "decision_task_matches_roadmap": True,
            "decision_next_allowed_task_matches_gate": True,
            "push_locked_structurally": upload_gate.get("push_allowed") is False,
            "decision_upload_locked": decision.get("github_upload_allowed")
            in (None, False),
            "batch_current_phase_completed": batch_current_phase_completed,
            "roadmap_current_phase_passed": roadmap_current_phase_passed,
            "roadmap_current_task_completed": roadmap_current_task_completed,
            "roadmap_current_task_results_recorded": (
                roadmap_current_task_results_recorded
            ),
            "roadmap_current_task_evidence_recorded": (
                roadmap_current_task_evidence_recorded
            ),
            "stage038_source_gate_consistent": stage038_source_gate_consistent,
        }

    stage_status = stage_node.get("status")
    expected_batch_statuses = {stage_status}
    if isinstance(stage_status, str) and not stage_status.startswith(stage_prefix):
        expected_batch_statuses.add(f"{stage_prefix}_{stage_status}")
    roadmap_gate = roadmap.get("next_gate_id")
    expected_next_task = None
    if (
        isinstance(roadmap_gate, str)
        and roadmap_gate.startswith("IDS-STAGE")
        and roadmap_gate.endswith("-GATE")
    ):
        expected_next_task = (
            "IDS-V0_1-" + roadmap_gate.removeprefix("IDS-").removesuffix("-GATE")
        )

    return {
        "yaml_documents_parsed": bool(batch) and bool(roadmap),
        "current_stage_node_resolved": bool(stage_key) and bool(stage_node),
        "batch_top_status_matches_stage": (
            (
                batch.get("status")
                == "reviewed_ready_for_upload_no_github_upload"
                if batch031_040_review_current
                else batch.get("status")
                == "local_batch_upload_gate_passed_pending_github_merge"
                if batch031_040_upload_current
                else batch.get("status") == "uploaded_to_github_main"
            )
            if batch031_040_gate_current
            else batch.get("status") in expected_batch_statuses
        ),
        "batch_stage_task_matches_roadmap": (
            decision.get("current_task_id") == roadmap_task
            if batch031_040_gate_current
            else stage_node.get("current_task_id") == roadmap_task
        ),
        "batch_stage_gate_matches_roadmap": (
            decision.get("next_allowed_task_id") == roadmap_gate
            if batch031_040_gate_current
            else stage_node.get("next_gate") == roadmap_gate
        ),
        "roadmap_phase_matches_stage": (
            batch031_040_gate_current
            or (
                isinstance(roadmap_phase, str)
                and roadmap_phase.startswith(f"IDS-STAGE{stage_suffix}")
            )
        ),
        "decision_task_matches_roadmap": not decision
        or decision.get("current_task_id") == roadmap_task,
        "decision_next_allowed_task_matches_gate": (
            decision.get("next_allowed_task_id") == roadmap_gate
            if batch031_040_gate_current
            else decision.get("next_allowed_task_id") == expected_next_task
            if roadmap_phase in {"IDS-STAGE036-P4", "IDS-STAGE037-P4"}
            else (
                not decision
                or expected_next_task is None
                or decision.get("next_allowed_task_id")
                in (None, expected_next_task)
            )
        ),
        "push_locked_structurally": (
            upload_gate.get("push_allowed") is True
            if batch031_040_upload_current or batch031_040_main_current
            else upload_gate.get("push_allowed") is False
        ),
        "decision_upload_locked": (
            decision.get("github_upload_allowed") is True
            if batch031_040_upload_current or batch031_040_main_current
            else decision.get("github_upload_allowed") in (None, False)
        ),
        "batch_current_phase_completed": batch_current_phase_completed,
        "roadmap_current_phase_passed": roadmap_current_phase_passed,
        "roadmap_current_task_completed": roadmap_current_task_completed,
        "roadmap_current_task_results_recorded": (
            roadmap_current_task_results_recorded
        ),
        "roadmap_current_task_evidence_recorded": (
            roadmap_current_task_evidence_recorded
        ),
        "stage038_source_gate_consistent": stage038_source_gate_consistent,
        "batch031_040_review_consistent": batch031_040_gate_consistent,
    }


def evaluate_phase_state(
    batch_text: str, roadmap_text: str, *, require_structured: bool = False
) -> dict[str, bool]:
    batch_upload_gate_active = (
        'gate_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"' in batch_text
        and 'current_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-001-010-GITHUB-MERGE"' in roadmap_text
    )
    batch_uploaded_to_main = (
        'status: "uploaded_to_github_main"' in batch_text
        and 'merged_sha: "2d418ccba1e16bcb940387c6e8152668fc2dccaf"' in batch_text
        and 'current_task_id: "IDS-V0_1-BATCH-001-010-MAIN-MERGED"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE011-P1-GATE"' in roadmap_text
    )
    stage011_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE011-P2"' in batch_text
        and 'acceptance_status: "phase2_implementation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE011"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE011-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE011-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE011-P3-GATE"' in roadmap_text
    )
    stage011_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE011-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE011"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE011-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE011-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE011-P4-GATE"' in roadmap_text
    )
    stage011_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE011-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-012"' in batch_text
        and 'current_stage_id: "IDS-STAGE011"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE011-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE011-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE012-P1-GATE"' in roadmap_text
    )
    stage012_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE012-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE012"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE012-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE012-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE012-P2-GATE"' in roadmap_text
    )
    stage012_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE012-P2"' in batch_text
        and 'acceptance_status: "phase2_readonly_identity_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE012"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE012-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE012-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE012-P3-GATE"' in roadmap_text
    )
    stage012_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE012-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE012"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE012-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE012-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE012-P4-GATE"' in roadmap_text
    )
    stage012_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE012-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-013"' in batch_text
        and 'current_stage_id: "IDS-STAGE012"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE012-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE012-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE013-P1-GATE"' in roadmap_text
    )
    stage013_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE013-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE013"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE013-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE013-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE013-P2-GATE"' in roadmap_text
    )
    stage013_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE013-P2"' in batch_text
        and 'acceptance_status: "phase2_fingerprint_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE013"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE013-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE013-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE013-P3-GATE"' in roadmap_text
    )
    stage013_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE013-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE013"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE013-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE013-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE013-P4-GATE"' in roadmap_text
    )
    stage013_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE013-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-014"' in batch_text
        and 'current_stage_id: "IDS-STAGE013"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE013-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE013-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE014-P1-GATE"' in roadmap_text
    )
    stage014_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE014-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE014"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE014-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE014-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE014-P2-GATE"' in roadmap_text
    )
    stage014_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE014-P2"' in batch_text
        and 'acceptance_status: "phase2_manifest_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE014"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE014-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE014-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE014-P3-GATE"' in roadmap_text
    )
    stage014_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE014-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE014"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE014-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE014-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE014-P4-GATE"' in roadmap_text
    )
    stage014_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE014-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-015"' in batch_text
        and 'current_stage_id: "IDS-STAGE014"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE014-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE014-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE015-P1-GATE"' in roadmap_text
    )
    stage015_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE015-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE015"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE015-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE015-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE015-P2-GATE"' in roadmap_text
    )
    stage015_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE015-P2"' in batch_text
        and 'acceptance_status: "phase2_duplicate_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE015"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE015-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE015-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE015-P3-GATE"' in roadmap_text
    )
    stage015_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE015-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE015"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE015-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE015-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE015-P4-GATE"' in roadmap_text
    )
    stage015_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE015-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-016"' in batch_text
        and 'current_stage_id: "IDS-STAGE015"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE015-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE015-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE016-P1-GATE"' in roadmap_text
    )
    stage016_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE016-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE016"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE016-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE016-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE016-P2-GATE"' in roadmap_text
    )
    stage016_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE016-P2"' in batch_text
        and 'acceptance_status: "phase2_import_idempotency_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE016"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE016-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE016-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE016-P3-GATE"' in roadmap_text
    )
    stage016_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE016-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE016"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE016-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE016-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE016-P4-GATE"' in roadmap_text
    )
    stage016_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE016-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-017"' in batch_text
        and 'current_stage_id: "IDS-STAGE016"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE016-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE016-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE017-P1-GATE"' in roadmap_text
    )
    stage017_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE017-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE017"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE017-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE017-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE017-P2-GATE"' in roadmap_text
    )
    stage017_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE017-P2"' in batch_text
        and 'acceptance_status: "phase2_regression_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE017"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE017-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE017-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE017-P3-GATE"' in roadmap_text
    )
    stage017_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE017-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE017"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE017-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE017-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE017-P4-GATE"' in roadmap_text
    )
    stage017_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE017-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-018"' in batch_text
        and 'current_stage_id: "IDS-STAGE017"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE017-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE017-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE018-P1-GATE"' in roadmap_text
    )
    stage018_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE018-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE018"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE018-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE018-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE018-P2-GATE"' in roadmap_text
    )
    stage018_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE018-P2"' in batch_text
        and 'acceptance_status: "phase2_preflight_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE018"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE018-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE018-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE018-P3-GATE"' in roadmap_text
    )
    stage018_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE018-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE018"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE018-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE018-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE018-P4-GATE"' in roadmap_text
    )
    stage018_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE018-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-019"' in batch_text
        and 'current_stage_id: "IDS-STAGE018"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE018-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE018-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE019-P1-GATE"' in roadmap_text
    )
    stage019_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE019-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE019"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE019-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE019-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE019-P2-GATE"' in roadmap_text
    )
    stage019_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE019-P2"' in batch_text
        and 'acceptance_status: "phase2_risk_estimator_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE019"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE019-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE019-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE019-P3-GATE"' in roadmap_text
    )
    stage019_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE019-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE019"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE019-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE019-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE019-P4-GATE"' in roadmap_text
    )
    stage019_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE019-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-020"' in batch_text
        and 'current_stage_id: "IDS-STAGE019"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE019-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE019-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE020-P1-GATE"' in roadmap_text
    )
    stage020_phase1_active = (
        'current_task_id: "IDS-V0_1-STAGE020-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE020-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE020-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE020-P2-GATE"' in roadmap_text
    )
    stage020_phase2_active = (
        'current_task_id: "IDS-V0_1-STAGE020-P2"' in batch_text
        and 'acceptance_status: "phase2_cost_estimator_slice_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE020-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE020-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE020-P3-GATE"' in roadmap_text
    )
    stage020_phase3_active = (
        'current_task_id: "IDS-V0_1-STAGE020-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE020-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE020-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE020-P4-GATE"' in roadmap_text
    )
    stage020_phase4_closeout = (
        'current_task_id: "IDS-V0_1-STAGE020-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-021"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE020-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE020-P4"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"' in roadmap_text
    )
    batch011_020_reviewed_pending_upload = (
        'status: "reviewed_ready_for_upload_no_github_upload"' in batch_text
        and 'review_task_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"' in batch_text
        and 'review_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_REVIEW_GATE.md"'
        in batch_text
        and 'push_allowed: false' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in roadmap_text
    )
    batch011_020_upload_gate_active = (
        'status: "local_batch_upload_gate_passed_pending_github_merge"' in batch_text
        and 'push_allowed: true' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in batch_text
        and 'gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md"'
        in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-011-020-GITHUB-MERGE"' in roadmap_text
    )
    batch011_020_uploaded_to_main = (
        'status: "uploaded_to_github_main"' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"' in batch_text
        and 'github_pr: "https://github.com/LinzeColin/CodexProject/pull/271"' in batch_text
        and 'merged_sha: "61fcb5295c6e0046059eba236c4cedbdaa2f2fed"' in batch_text
        and 'post_merge_open_prs: 0' in batch_text
        and 'post_merge_open_issues: 0' in batch_text
        and 'current_stage_id: "IDS-STAGE020"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-011-020-MAIN-MERGED"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-011-020-MAIN-MERGED"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE021-P1-GATE"' in roadmap_text
    )
    stage021_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE021-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE021"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE021-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE021-P2-GATE"' in roadmap_text
    )
    stage021_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P2"' in batch_text
        and 'acceptance_status: "phase2_preflight_confirmation_ui_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE021-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE021"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE021-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE021-P3-GATE"' in roadmap_text
    )
    stage021_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE021-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE021"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE021-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE021-P4-GATE"' in roadmap_text
    )
    stage021_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE022-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE021"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE021-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE021-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE022-P1-GATE"' in roadmap_text
    )
    stage022_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE022-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE022"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE022-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE022-P2-GATE"' in roadmap_text
    )
    stage022_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P2"' in batch_text
        and 'acceptance_status: "phase2_priority_queue_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE022-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE022"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE022-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE022-P3-GATE"' in roadmap_text
    )
    stage022_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE022-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE022"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE022-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE022-P4-GATE"' in roadmap_text
    )
    stage022_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE023-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE022"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE022-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE022-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE023-P1-GATE"' in roadmap_text
    )
    stage023_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE023-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE023"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE023-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE023-P2-GATE"' in roadmap_text
    )
    stage023_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P2"' in batch_text
        and 'acceptance_status: "phase2_preflight_scenario_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE023-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE023"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE023-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE023-P3-GATE"' in roadmap_text
    )
    stage023_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE023-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE023"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE023-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE023-P4-GATE"' in roadmap_text
    )
    stage023_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE024-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE023"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE023-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE023-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE024-P1-GATE"' in roadmap_text
    )
    stage024_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE024-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE024"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE024-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE024-P2-GATE"' in roadmap_text
    )
    stage024_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P2"' in batch_text
        and 'acceptance_status: "phase2_safe_extraction_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE024-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE024"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE024-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE024-P3-GATE"' in roadmap_text
    )
    stage024_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE024-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE024"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE024-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE024-P4-GATE"' in roadmap_text
    )
    stage024_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE025-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE024"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE024-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE024-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE025-P1-GATE"' in roadmap_text
    )
    stage025_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE025-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE025"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE025-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE025-P2-GATE"' in roadmap_text
    )
    stage025_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P2"' in batch_text
        and 'acceptance_status: "phase2_safe_extraction_engine_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE025-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE025"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE025-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE025-P3-GATE"' in roadmap_text
    )
    stage025_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE025-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE025"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE025-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE025-P4-GATE"' in roadmap_text
    )
    stage025_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE026-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE025"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE025-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE025-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE026-P1-GATE"' in roadmap_text
    )
    stage026_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE026-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE026"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE026-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE026-P2-GATE"' in roadmap_text
    )
    stage026_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P2"' in batch_text
        and 'acceptance_status: "phase2_archive_manifest_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE026-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE026"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE026-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE026-P3-GATE"' in roadmap_text
    )
    stage026_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE026-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE026"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE026-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE026-P4-GATE"' in roadmap_text
    )
    stage026_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_gate: "IDS-STAGE027-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE026"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE026-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE026-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE027-P1-GATE"' in roadmap_text
    )
    stage027_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE027-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE027"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE027-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE027-P2-GATE"' in roadmap_text
    )
    stage027_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P2"' in batch_text
        and 'acceptance_status: "phase2_reingest_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE027-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE027"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE027-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE027-P3-GATE"' in roadmap_text
    )
    stage027_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE027-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE027"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE027-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE027-P4-GATE"' in roadmap_text
    )
    stage027_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-028"' in batch_text
        and 'next_gate: "IDS-STAGE028-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE027"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE027-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE027-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE028-P1-GATE"' in roadmap_text
    )
    stage028_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage028_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE028-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE028"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE028-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE028-P2-GATE"' in roadmap_text
    )
    stage028_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage028_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P2"' in batch_text
        and 'acceptance_status: "phase2_archive_adversarial_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE028-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE028"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE028-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE028-P3-GATE"' in roadmap_text
    )
    stage028_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage028_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE028-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE028"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE028-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE028-P4-GATE"' in roadmap_text
    )
    stage028_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage028_completed_local_pending_stage029"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-029"' in batch_text
        and 'next_gate: "IDS-STAGE029-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE028"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE028-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE028-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE029-P1-GATE"' in roadmap_text
    )
    stage029_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage029_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE029-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE029"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE029-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE029-P2-GATE"' in roadmap_text
    )
    stage029_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage029_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P2"' in batch_text
        and 'acceptance_status: "phase2_cleanup_allowlist_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE029-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE029"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE029-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE029-P3-GATE"' in roadmap_text
    )
    stage029_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage029_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE029-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE029"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE029-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE029-P4-GATE"' in roadmap_text
    )
    stage029_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage029_completed_local_pending_stage030"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_stage: "STAGE-030"' in batch_text
        and 'next_gate: "IDS-STAGE030-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE029"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE029-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE029-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE030-P1-GATE"' in roadmap_text
    )
    stage030_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage030_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE030-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE030-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE030-P2-GATE"' in roadmap_text
    )
    stage030_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage030_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P2"' in batch_text
        and 'acceptance_status: "phase2_schema_migration_slice_complete"' in batch_text
        and 'next_gate: "IDS-STAGE030-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE030-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE030-P3-GATE"' in roadmap_text
    )
    stage030_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage030_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_complete"' in batch_text
        and 'next_gate: "IDS-STAGE030-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE030-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE030-P4-GATE"' in roadmap_text
    )
    stage030_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-021-030"' in batch_text
        and 'status: "stage030_completed_local_pending_batch_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P4"' in batch_text
        and 'acceptance_status: "local_passed"' in batch_text
        and 'next_phase: "batch_review_gate"' in batch_text
        and 'next_gate: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE030-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE030-P4"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in roadmap_text
    )
    batch021_030_reviewed_pending_upload = (
        'status: "reviewed_ready_for_upload_no_github_upload"' in batch_text
        and 'review_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in batch_text
        and 'review_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_REVIEW_GATE.md"'
        in batch_text
        and 'push_allowed: false' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in roadmap_text
    )
    batch021_030_upload_gate_active = (
        'status: "local_batch_upload_gate_passed_pending_github_merge"' in batch_text
        and 'push_allowed: true' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in batch_text
        and 'gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md"'
        in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"' in roadmap_text
    )
    batch021_030_uploaded_to_main = (
        'status: "uploaded_to_github_main"' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"' in batch_text
        and 'github_pr: "https://github.com/LinzeColin/CodexProject/pull/272"' in batch_text
        and 'merged_sha: "88a428c7901226bd44d5e4ff106cd51d74b550fe"' in batch_text
        and 'post_merge_open_prs: 0' in batch_text
        and 'post_merge_open_issues: 0' in batch_text
        and 'current_stage_id: "IDS-STAGE030"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-P1-GATE"' in roadmap_text
    )
    stage031_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE031-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-P2-GATE"' in roadmap_text
    )
    stage031_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P2"' in batch_text
        and 'acceptance_status: "phase2_safety_slice_defined"' in batch_text
        and 'next_gate: "IDS-STAGE031-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-P3-GATE"' in roadmap_text
    )
    stage031_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_defined"' in batch_text
        and 'next_gate: "IDS-STAGE031-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-P4-GATE"' in roadmap_text
    )
    stage031_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_completed_local_pending_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P4"' in batch_text
        and 'acceptance_status: "local_passed_pending_stage_review"' in batch_text
        and 'next_gate: "IDS-STAGE031-REVIEW-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE031-REVIEW-GATE"' in roadmap_text
    )
    stage031_reviewed_local = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage031_completed_reviewed_local"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE031-REVIEW"' in batch_text
        and 'acceptance_status: "reviewed_local_passed"' in batch_text
        and 'next_stage: "STAGE-032"' in batch_text
        and 'next_gate: "IDS-STAGE032-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE031"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE031-REVIEW"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE031-REVIEW"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE032-P1-GATE"' in roadmap_text
    )
    stage032_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage032_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE032-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE032-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE032"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE032-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE032-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE032-P2-GATE"' in roadmap_text
    )
    stage032_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage032_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE032-P2"' in batch_text
        and 'acceptance_status: "phase2_connection_pool_slice_defined"' in batch_text
        and 'next_gate: "IDS-STAGE032-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE032"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE032-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE032-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE032-P3-GATE"' in roadmap_text
    )
    stage032_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage032_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE032-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_defined"' in batch_text
        and 'next_gate: "IDS-STAGE032-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE032"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE032-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE032-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE032-P4-GATE"' in roadmap_text
    )
    stage032_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage032_completed_local_pending_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE032-P4"' in batch_text
        and 'acceptance_status: "local_passed_pending_stage_review"' in batch_text
        and 'next_phase: "stage_review_gate"' in batch_text
        and 'next_gate: "IDS-STAGE032-REVIEW-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE032"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE032-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE032-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE032-REVIEW-GATE"' in roadmap_text
    )
    stage032_reviewed_local = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage032_completed_reviewed_local"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE032-REVIEW"' in batch_text
        and 'acceptance_status: "reviewed_local_passed"' in batch_text
        and 'next_stage: "STAGE-033"' in batch_text
        and 'next_gate: "IDS-STAGE033-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE032"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE032-REVIEW"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE032-REVIEW"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE033-P1-GATE"' in roadmap_text
    )
    stage033_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage033_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE033-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE033-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE033"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE033-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE033-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE033-P2-GATE"' in roadmap_text
    )
    stage033_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage033_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE033-P2"' in batch_text
        and 'acceptance_status: "phase2_size_guard_slice_defined"' in batch_text
        and 'next_gate: "IDS-STAGE033-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE033"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE033-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE033-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE033-P3-GATE"' in roadmap_text
    )
    stage033_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage033_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE033-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_passed"' in batch_text
        and 'next_gate: "IDS-STAGE033-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE033"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE033-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE033-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE033-P4-GATE"' in roadmap_text
    )
    stage033_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage033_completed_local_pending_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE033-P4"' in batch_text
        and 'acceptance_status: "phase4_closeout_complete"' in batch_text
        and 'next_gate: "IDS-STAGE033-REVIEW-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE033"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE033-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE033-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE033-REVIEW-GATE"' in roadmap_text
    )
    stage033_reviewed_local = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage033_completed_reviewed_local"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE033-REVIEW"' in batch_text
        and 'acceptance_status: "reviewed_local_passed"' in batch_text
        and 'next_stage: "STAGE-034"' in batch_text
        and 'next_gate: "IDS-STAGE034-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE033"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE033-REVIEW"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE033-REVIEW"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE034-P1-GATE"' in roadmap_text
    )
    stage034_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage034_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE034-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE034-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE034"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE034-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE034-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE034-P2-GATE"' in roadmap_text
    )
    stage034_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage034_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE034-P2"' in batch_text
        and 'acceptance_status: "phase2_retention_table_slice_defined"' in batch_text
        and 'next_gate: "IDS-STAGE034-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE034"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE034-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE034-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE034-P3-GATE"' in roadmap_text
    )
    stage034_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage034_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE034-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_passed"' in batch_text
        and 'next_gate: "IDS-STAGE034-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE034"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE034-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE034-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE034-P4-GATE"' in roadmap_text
    )
    stage034_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage034_completed_local_pending_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE034-P4"' in batch_text
        and 'acceptance_status: "phase4_closeout_complete"' in batch_text
        and 'next_gate: "IDS-STAGE034-REVIEW-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE034"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE034-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE034-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE034-REVIEW-GATE"' in roadmap_text
    )
    stage034_reviewed_local = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage034_completed_reviewed_local"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE034-REVIEW"' in batch_text
        and 'acceptance_status: "reviewed_local_passed"' in batch_text
        and 'next_stage: "STAGE-035"' in batch_text
        and 'next_gate: "IDS-STAGE035-P1-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE034"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE034-REVIEW"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE034-REVIEW"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE035-P1-GATE"' in roadmap_text
    )
    stage035_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage035_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE035-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE035-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE035"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE035-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE035-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE035-P2-GATE"' in roadmap_text
    )
    stage035_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage035_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE035-P2"' in batch_text
        and 'acceptance_status: "phase2_static_recovery_smoke_contract_validated"'
        in batch_text
        and 'next_gate: "IDS-STAGE035-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE035"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE035-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE035-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE035-P3-GATE"' in roadmap_text
    )
    stage035_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage035_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE035-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_passed"' in batch_text
        and 'next_gate: "IDS-STAGE035-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE035"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE035-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE035-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE035-P4-GATE"' in roadmap_text
    )
    stage035_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage035_completed_local_pending_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE035-P4"' in batch_text
        and 'acceptance_status: "phase4_closeout_complete"' in batch_text
        and 'next_phase: "stage_review_gate"' in batch_text
        and 'next_gate: "IDS-STAGE035-REVIEW-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE035"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE035-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE035-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE035-REVIEW-GATE"' in roadmap_text
    )
    stage035_reviewed_local = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage035_completed_reviewed_local"' in batch_text
        and 'status: "completed_reviewed_local"' in batch_text
        and 'review_status: "passed"' in batch_text
        and 'next_stage: "STAGE-036"' in batch_text
        and 'next_gate: "IDS-STAGE036-P1-GATE"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE035-REVIEW"' in batch_text
        and 'acceptance_status: "reviewed_local_passed"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE035"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE035-REVIEW"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE035-REVIEW"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE036-P1-GATE"' in roadmap_text
    )
    stage036_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage036_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE036-P1"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_gate: "IDS-STAGE036-P2-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE036"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE036-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE036-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE036-P2-GATE"' in roadmap_text
    )
    stage036_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage036_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE036-P2"' in batch_text
        and 'acceptance_status: "phase2_static_quality_constraint_contract_validated"'
        in batch_text
        and 'next_gate: "IDS-STAGE036-P3-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE036"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE036-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE036-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE036-P3-GATE"' in roadmap_text
    )
    stage036_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage036_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE036-P3"' in batch_text
        and 'acceptance_status: "phase3_scenario_validation_passed"' in batch_text
        and 'next_gate: "IDS-STAGE036-P4-GATE"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE036"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE036-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE036-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE036-P4-GATE"' in roadmap_text
    )
    stage036_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage036_completed_local_pending_review"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE036-P4"' in batch_text
        and 'acceptance_status: "phase4_closeout_complete"' in batch_text
        and 'next_phase: "stage_review_gate"' in batch_text
        and 'next_gate: "IDS-STAGE036-REVIEW-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE036-REVIEW"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE036"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE036-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE036-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE036-REVIEW-GATE"' in roadmap_text
    )
    stage036_reviewed_local = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage036_completed_reviewed_local"' in batch_text
        and 'status: "completed_reviewed_local"' in batch_text
        and 'review_status: "passed"' in batch_text
        and 'next_stage: "STAGE-037"' in batch_text
        and 'next_gate: "IDS-STAGE037-P1-GATE"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE036-REVIEW"' in batch_text
        and 'acceptance_status: "reviewed_local_passed"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE037-P1"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE036"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE036-REVIEW"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE036-REVIEW"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE037-P1-GATE"' in roadmap_text
    )
    stage037_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage037_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE037-P1"' in batch_text
        and 'acceptance_id: "ACC-STAGE-037"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined"' in batch_text
        and 'next_phase: "Phase 2"' in batch_text
        and 'next_gate: "IDS-STAGE037-P2-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE037-P2"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE037"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE037-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE037-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE037-P2-GATE"' in roadmap_text
    )
    stage037_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage037_phase2_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE037-P2"' in batch_text
        and 'acceptance_id: "ACC-STAGE-037"' in batch_text
        and 'acceptance_status: "phase2_deterministic_engine_passed"'
        in batch_text
        and 'next_phase: "Phase 3"' in batch_text
        and 'next_gate: "IDS-STAGE037-P3-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE037-P3"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE037"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE037-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE037-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE037-P3-GATE"' in roadmap_text
    )
    stage037_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage037_phase3_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE037-P3"' in batch_text
        and 'acceptance_id: "ACC-STAGE-037"' in batch_text
        and 'acceptance_status: "phase3_adversarial_scenarios_passed"'
        in batch_text
        and 'next_phase: "Phase 4"' in batch_text
        and 'next_gate: "IDS-STAGE037-P4-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE037-P4"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE037"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE037-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE037-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE037-P4-GATE"' in roadmap_text
    )
    stage037_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage037_phase4_completed_review_pending"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE037-P4"' in batch_text
        and 'acceptance_id: "ACC-STAGE-037"' in batch_text
        and 'acceptance_status: "phase4_closeout_passed_review_pending"'
        in batch_text
        and 'review_status: "pending"' in batch_text
        and 'next_phase: "stage_review"' in batch_text
        and 'next_gate: "IDS-STAGE037-REVIEW-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE037-REVIEW"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE037"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE037-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE037-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE037-REVIEW-GATE"' in roadmap_text
    )
    stage038_phase1_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage038_phase1_in_progress"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P1"' in batch_text
        and 'acceptance_id: "ACC-STAGE-038"' in batch_text
        and 'acceptance_status: "phase1_scope_boundary_defined_source_reverification_required"'
        in batch_text
        and 'source_verification_status: "EXTERNAL_TASKPACK_ABSENT"'
        in batch_text
        and 'source_reverification_gate_status: "blocked_external_taskpack_absent"'
        in batch_text
        and 'phase2_entry_authorized: false' in batch_text
        and 'next_phase: "Phase 1 source reverification"' in batch_text
        and 'next_gate: "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"'
        in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"'
        in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE038"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE038-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P1"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"'
        in roadmap_text
        and 'entry_authorized: false' in roadmap_text
        and 'entry_blocker: "source_reverification_required_before_phase2"'
        in roadmap_text
    )
    stage038_source_reverified = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage038_phase1_source_reverified"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"'
        in batch_text
        and 'acceptance_id: "ACC-STAGE-038"' in batch_text
        and 'acceptance_status: "phase1_source_reverified_phase2_authorized"'
        in batch_text
        and 'source_verification_status: "SOURCE_VERIFIED"' in batch_text
        and 'source_reverification_gate_status: "passed"' in batch_text
        and 'phase2_entry_authorized: true' in batch_text
        and 'next_phase: "Phase 2"' in batch_text
        and 'next_gate: "IDS-STAGE038-P2-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE038-P2"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE038"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE038-P1"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"'
        in roadmap_text
        and 'next_gate_id: "IDS-STAGE038-P2-GATE"' in roadmap_text
        and 'gate_id: "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE"'
        in roadmap_text
        and 'source_member_match_count: 1' in roadmap_text
        and 'source_member_sha256: "613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634"'
        in roadmap_text
        and 'reconciliation_status: "passed"' in roadmap_text
        and 'independent_review_status: "passed"' in roadmap_text
        and 'entry_authorized: true' in roadmap_text
    )
    stage038_phase2_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage038_phase2_completed"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P2"' in batch_text
        and 'acceptance_id: "ACC-STAGE-038"' in batch_text
        and 'acceptance_status: "phase2_isolated_async_slice_passed"'
        in batch_text
        and 'source_verification_status: "SOURCE_VERIFIED"' in batch_text
        and 'source_reverification_gate_status: "passed"' in batch_text
        and 'phase2_entry_authorized: true' in batch_text
        and 'next_phase: "Phase 3"' in batch_text
        and 'next_gate: "IDS-STAGE038-P3-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE038-P3"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE038"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE038-P2"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P2"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE038-P3-GATE"' in roadmap_text
    )
    stage038_phase3_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage038_phase3_completed"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P3"' in batch_text
        and 'acceptance_id: "ACC-STAGE-038"' in batch_text
        and 'acceptance_status: "phase3_isolated_scenarios_passed"'
        in batch_text
        and 'source_verification_status: "SOURCE_VERIFIED"' in batch_text
        and 'source_reverification_gate_status: "passed"' in batch_text
        and 'phase2_entry_authorized: true' in batch_text
        and 'next_phase: "Phase 4"' in batch_text
        and 'next_gate: "IDS-STAGE038-P4-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE038-P4"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE038"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE038-P3"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P3"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE038-P4-GATE"' in roadmap_text
    )
    stage038_phase4_closeout = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "stage038_phase4_completed_review_pending"' in batch_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P4"' in batch_text
        and 'acceptance_id: "ACC-STAGE-038"' in batch_text
        and 'acceptance_status: "phase4_closeout_passed_review_pending"'
        in batch_text
        and 'source_verification_status: "SOURCE_VERIFIED"' in batch_text
        and 'source_reverification_gate_status: "passed"' in batch_text
        and 'phase2_entry_authorized: true' in batch_text
        and 'review_status: "pending"' in batch_text
        and 'next_phase: "stage_review"' in batch_text
        and 'next_gate: "IDS-STAGE038-REVIEW-GATE"' in batch_text
        and 'next_allowed_task_id: "IDS-V0_1-STAGE038-REVIEW"' in batch_text
        and 'push_allowed: false' in batch_text
        and 'current_stage_id: "IDS-STAGE038"' in roadmap_text
        and 'current_phase_id: "IDS-STAGE038-P4"' in roadmap_text
        and 'current_task_id: "IDS-V0_1-STAGE038-P4"' in roadmap_text
        and 'next_gate_id: "IDS-STAGE038-REVIEW-GATE"' in roadmap_text
    )
    batch_document = _parse_yaml_text(batch_text)
    roadmap_document = _parse_yaml_text(roadmap_text)
    stage_progress = batch_document.get("stage_progress")
    stage_progress = stage_progress if isinstance(stage_progress, dict) else {}
    stage037_node = stage_progress.get("STAGE-037")
    stage037_node = stage037_node if isinstance(stage037_node, dict) else {}
    upload_gate = batch_document.get("upload_gate")
    upload_gate = upload_gate if isinstance(upload_gate, dict) else {}
    decision_node = batch_document.get("decision")
    decision_node = decision_node if isinstance(decision_node, dict) else {}
    roadmap_stages = roadmap_document.get("stages")
    roadmap_stages = roadmap_stages if isinstance(roadmap_stages, list) else []
    roadmap_stage037 = next(
        (
            item
            for item in roadmap_stages
            if isinstance(item, dict) and item.get("stage_id") == "IDS-STAGE037"
        ),
        {},
    )
    roadmap_stage037 = (
        roadmap_stage037 if isinstance(roadmap_stage037, dict) else {}
    )
    roadmap_stage037_review = roadmap_stage037.get("review")
    roadmap_stage037_review = (
        roadmap_stage037_review
        if isinstance(roadmap_stage037_review, dict)
        else {}
    )
    stage037_reviewed_local = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage037_completed_reviewed_local"
        and upload_gate.get("push_allowed") is False
        and stage037_node.get("status") == "completed_reviewed_local"
        and stage037_node.get("completed_phases")
        == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        and stage037_node.get("review_status") == "passed"
        and stage037_node.get("next_stage") == "STAGE-038"
        and stage037_node.get("next_gate") == "IDS-STAGE038-P1-GATE"
        and stage037_node.get("current_task_id")
        == "IDS-V0_1-STAGE037-REVIEW"
        and stage037_node.get("acceptance_id") == "ACC-STAGE-037"
        and stage037_node.get("acceptance_status") == "reviewed_local_passed"
        and decision_node.get("current_task_id")
        == "IDS-V0_1-STAGE037-REVIEW"
        and decision_node.get("next_allowed_task_id") == "IDS-V0_1-STAGE038-P1"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE037"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE037-REVIEW"
        and roadmap_document.get("current_task_id")
        == "IDS-V0_1-STAGE037-REVIEW"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE038-P1-GATE"
        and roadmap_stage037_review.get("review_id")
        == "IDS-STAGE037-REVIEW"
        and roadmap_stage037_review.get("task_id")
        == "IDS-V0_1-STAGE037-REVIEW"
        and roadmap_stage037_review.get("status") == "completed"
        and "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_STAGE_REVIEW.md"
        in roadmap_stage037_review.get("evidence_refs", [])
    )
    stage038_node = stage_progress.get("STAGE-038")
    stage038_node = stage038_node if isinstance(stage038_node, dict) else {}
    roadmap_stage038 = next(
        (
            item
            for item in roadmap_stages
            if isinstance(item, dict) and item.get("stage_id") == "IDS-STAGE038"
        ),
        {},
    )
    roadmap_stage038 = (
        roadmap_stage038 if isinstance(roadmap_stage038, dict) else {}
    )
    roadmap_stage038_review = roadmap_stage038.get("review")
    roadmap_stage038_review = (
        roadmap_stage038_review
        if isinstance(roadmap_stage038_review, dict)
        else {}
    )
    stage038_reviewed_local = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage038_completed_reviewed_local"
        and upload_gate.get("push_allowed") is False
        and stage038_node.get("status") == "completed_reviewed_local"
        and stage038_node.get("completed_phases")
        == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        and stage038_node.get("review_status") == "passed"
        and stage038_node.get("next_stage") == "STAGE-039"
        and stage038_node.get("next_gate") == "IDS-STAGE039-P1-GATE"
        and stage038_node.get("current_task_id")
        == "IDS-V0_1-STAGE038-REVIEW"
        and stage038_node.get("acceptance_id") == "ACC-STAGE-038"
        and stage038_node.get("acceptance_status") == "reviewed_local_passed"
        and decision_node.get("current_task_id")
        == "IDS-V0_1-STAGE038-REVIEW"
        and decision_node.get("next_allowed_task_id")
        == "IDS-V0_1-STAGE039-P1"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE038"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE038-REVIEW"
        and roadmap_document.get("current_task_id")
        == "IDS-V0_1-STAGE038-REVIEW"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE039-P1-GATE"
        and roadmap_stage038_review.get("review_id")
        == "IDS-STAGE038-REVIEW"
        and roadmap_stage038_review.get("task_id")
        == "IDS-V0_1-STAGE038-REVIEW"
        and roadmap_stage038_review.get("status") == "completed"
        and "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md"
        in roadmap_stage038_review.get("evidence_refs", [])
    )
    stage039_node = stage_progress.get("STAGE-039")
    stage039_node = stage039_node if isinstance(stage039_node, dict) else {}
    stage039_phase1_active = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage039_phase1_completed"
        and upload_gate.get("push_allowed") is False
        and stage039_node.get("status") == "stage039_phase1_completed"
        and stage039_node.get("completed_phases") == ["Phase 1"]
        and stage039_node.get("review_status") == "pending"
        and stage039_node.get("next_phase") == "Phase 2"
        and stage039_node.get("next_gate") == "IDS-STAGE039-P2-GATE"
        and stage039_node.get("current_task_id") == "IDS-V0_1-STAGE039-P1"
        and stage039_node.get("acceptance_id") == "ACC-STAGE-039"
        and stage039_node.get("acceptance_status")
        == "phase1_scope_boundary_complete"
        and stage039_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage039_node.get("source_member_match_count") == 1
        and stage039_node.get("source_member_sha256")
        == "504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9"
        and stage039_node.get("phase2_entry_authorized") is True
        and stage039_node.get("retry_policy_contract_id")
        == "ids.retry_dead_letter.v0_1.p1"
        and stage039_node.get("contract_state")
        == "PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED"
        and stage039_node.get("numeric_policy_values_assigned") is False
        and decision_node.get("current_task_id") == "IDS-V0_1-STAGE039-P1"
        and decision_node.get("next_allowed_task_id")
        == "IDS-V0_1-STAGE039-P2"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE039"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE039-P1"
        and roadmap_document.get("current_task_id") == "IDS-V0_1-STAGE039-P1"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE039-P2-GATE"
    )
    roadmap_stage039 = next(
        (
            item
            for item in roadmap_stages
            if isinstance(item, dict) and item.get("stage_id") == "IDS-STAGE039"
        ),
        {},
    )
    roadmap_stage039 = roadmap_stage039 if isinstance(roadmap_stage039, dict) else {}
    roadmap_stage039_phases = roadmap_stage039.get("phases")
    roadmap_stage039_phases = (
        roadmap_stage039_phases if isinstance(roadmap_stage039_phases, list) else []
    )
    roadmap_stage039_phase2 = next(
        (
            item
            for item in roadmap_stage039_phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE039-P2"
        ),
        {},
    )
    roadmap_stage039_phase2 = (
        roadmap_stage039_phase2
        if isinstance(roadmap_stage039_phase2, dict)
        else {}
    )
    roadmap_stage039_phase3 = next(
        (
            item
            for item in roadmap_stage039_phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE039-P3"
        ),
        {},
    )
    roadmap_stage039_phase3 = (
        roadmap_stage039_phase3
        if isinstance(roadmap_stage039_phase3, dict)
        else {}
    )
    roadmap_stage039_phase4 = next(
        (
            item
            for item in roadmap_stage039_phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE039-P4"
        ),
        {},
    )
    roadmap_stage039_phase4 = (
        roadmap_stage039_phase4
        if isinstance(roadmap_stage039_phase4, dict)
        else {}
    )
    roadmap_stage039_review = roadmap_stage039.get("review")
    roadmap_stage039_review = (
        roadmap_stage039_review
        if isinstance(roadmap_stage039_review, dict)
        else {}
    )
    stage039_phase2_active = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage039_phase2_completed"
        and upload_gate.get("push_allowed") is False
        and stage039_node.get("status") == "stage039_phase2_completed"
        and stage039_node.get("completed_phases") == ["Phase 1", "Phase 2"]
        and stage039_node.get("review_status") == "pending"
        and stage039_node.get("next_phase") == "Phase 3"
        and stage039_node.get("next_gate") == "IDS-STAGE039-P3-GATE"
        and stage039_node.get("current_task_id") == "IDS-V0_1-STAGE039-P2"
        and stage039_node.get("acceptance_id") == "ACC-STAGE-039"
        and stage039_node.get("acceptance_status")
        == "phase2_isolated_slice_complete"
        and stage039_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage039_node.get("source_member_match_count") == 1
        and stage039_node.get("source_member_sha256")
        == "504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9"
        and stage039_node.get("phase3_entry_authorized") is True
        and stage039_node.get("retry_policy_contract_id")
        == "ids.retry_dead_letter.v0_1.p2"
        and stage039_node.get("policy_version")
        == "ids.retry_policy.v0_1.stage039.p2"
        and stage039_node.get("contract_state")
        == "PHASE2_ISOLATED_SLICE_ENABLED_PRODUCTION_DISABLED"
        and stage039_node.get("numeric_policy_values_assigned") is True
        and stage039_node.get("isolated_slice_valid") is True
        and decision_node.get("current_task_id") == "IDS-V0_1-STAGE039-P2"
        and decision_node.get("next_allowed_task_id") == "IDS-V0_1-STAGE039-P3"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE039"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE039-P2"
        and roadmap_document.get("current_task_id") == "IDS-V0_1-STAGE039-P2"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE039-P3-GATE"
        and roadmap_stage039_phase2.get("status") == "passed_with_local_evidence"
    )
    stage039_phase3_active = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage039_phase3_completed"
        and upload_gate.get("push_allowed") is False
        and stage039_node.get("status") == "stage039_phase3_completed"
        and stage039_node.get("completed_phases")
        == ["Phase 1", "Phase 2", "Phase 3"]
        and stage039_node.get("review_status") == "pending"
        and stage039_node.get("next_phase") == "Phase 4"
        and stage039_node.get("next_gate") == "IDS-STAGE039-P4-GATE"
        and stage039_node.get("current_task_id") == "IDS-V0_1-STAGE039-P3"
        and stage039_node.get("acceptance_id") == "ACC-STAGE-039"
        and stage039_node.get("acceptance_status")
        == "phase3_scenarios_complete"
        and stage039_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage039_node.get("source_member_match_count") == 1
        and stage039_node.get("source_member_sha256")
        == "504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9"
        and stage039_node.get("phase4_entry_authorized") is True
        and stage039_node.get("policy_version")
        == "ids.retry_policy.v0_1.stage039.p2"
        and stage039_node.get("phase2_contract_state")
        == "PHASE2_ISOLATED_SLICE_ENABLED_PRODUCTION_DISABLED"
        and stage039_node.get("contract_state")
        == "PHASE3_SCENARIOS_ENABLED_PRODUCTION_DISABLED"
        and stage039_node.get("scenario_contract_id")
        == "ids.retry_dead_letter.v0_1.p3.scenarios"
        and stage039_node.get("scenario_validation_valid") is True
        and stage039_node.get("scenario_count") == 10
        and stage039_node.get("passed_scenario_count") == 10
        and stage039_node.get("actual_worker_exception_performed") is True
        and stage039_node.get("actual_disk_observation_performed") is True
        and stage039_node.get("process_termination_performed") is False
        and stage039_node.get("physical_drive_removal_performed") is False
        and stage039_node.get("disk_allocation_performed") is False
        and stage039_node.get("external_api_call_performed") is False
        and stage039_node.get("cleanup_runtime_performed") is False
        and stage039_node.get("protected_ref_delete_performed") is False
        and decision_node.get("current_task_id") == "IDS-V0_1-STAGE039-P3"
        and decision_node.get("next_allowed_task_id") == "IDS-V0_1-STAGE039-P4"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE039"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE039-P3"
        and roadmap_document.get("current_task_id") == "IDS-V0_1-STAGE039-P3"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE039-P4-GATE"
        and roadmap_stage039_phase3.get("status") == "passed_with_local_evidence"
    )
    stage039_phase4_closeout = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status")
        == "stage039_phase4_completed_review_pending"
        and upload_gate.get("push_allowed") is False
        and stage039_node.get("status")
        == "stage039_phase4_completed_review_pending"
        and stage039_node.get("completed_phases")
        == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        and stage039_node.get("review_status") == "pending"
        and stage039_node.get("next_phase") == "stage_review_gate"
        and stage039_node.get("next_gate") == "IDS-STAGE039-REVIEW-GATE"
        and stage039_node.get("current_task_id") == "IDS-V0_1-STAGE039-P4"
        and stage039_node.get("acceptance_id") == "ACC-STAGE-039"
        and stage039_node.get("acceptance_status")
        == "phase4_closeout_complete_review_pending"
        and stage039_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage039_node.get("source_member_match_count") == 1
        and stage039_node.get("source_member_sha256")
        == "504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9"
        and stage039_node.get("policy_version")
        == "ids.retry_policy.v0_1.stage039.p2"
        and stage039_node.get("phase2_contract_state")
        == "PHASE2_ISOLATED_SLICE_ENABLED_PRODUCTION_DISABLED"
        and stage039_node.get("phase3_contract_state")
        == "PHASE3_SCENARIOS_ENABLED_PRODUCTION_DISABLED"
        and stage039_node.get("contract_state")
        == "PHASE4_CLOSEOUT_EVIDENCE_REVIEW_PENDING"
        and stage039_node.get("scenario_validation_valid") is True
        and stage039_node.get("delivery_contract_schema")
        == "ids.stage039.retry_dead_letter.phase4.delivery.v1"
        and stage039_node.get("delivery_contract_valid") is True
        and stage039_node.get("delivery_result")
        == "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED"
        and stage039_node.get("stage_review_status") == "pending_next_run"
        and stage039_node.get("required_job_type_count") == 8
        and stage039_node.get("required_job_state_count") == 11
        and stage039_node.get("required_transition_count") == 21
        and stage039_node.get("automatic_retry_eligible_safe_error_code_count")
        == 2
        and stage039_node.get("successful_automatic_recovery_case_count") == 0
        and stage039_node.get("whole_stage_review_performed") is False
        and stage039_node.get("production_runtime_activation_performed") is False
        and stage039_node.get("persistent_queue_write_performed") is False
        and stage039_node.get("database_connection_performed") is False
        and stage039_node.get("raw_metadata_content_accessed") is False
        and stage039_node.get("fake_ids_business_data_used") is False
        and decision_node.get("current_task_id") == "IDS-V0_1-STAGE039-P4"
        and decision_node.get("next_allowed_task_id")
        == "IDS-V0_1-STAGE039-REVIEW"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE039"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE039-P4"
        and roadmap_document.get("current_task_id") == "IDS-V0_1-STAGE039-P4"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE039-REVIEW-GATE"
        and roadmap_stage039_phase4.get("status") == "passed_with_local_evidence"
    )
    stage039_reviewed_local = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage039_completed_reviewed_local"
        and upload_gate.get("push_allowed") is False
        and stage039_node.get("status") == "completed_reviewed_local"
        and stage039_node.get("completed_phases")
        == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        and stage039_node.get("review_status") == "passed"
        and stage039_node.get("next_stage") == "STAGE-040"
        and stage039_node.get("next_gate") == "IDS-STAGE040-P1-GATE"
        and stage039_node.get("current_task_id")
        == "IDS-V0_1-STAGE039-REVIEW"
        and stage039_node.get("acceptance_id") == "ACC-STAGE-039"
        and stage039_node.get("acceptance_status") == "reviewed_local_passed"
        and stage039_node.get("stage_review_status")
        == "completed_reviewed_local"
        and stage039_node.get("whole_stage_review_performed") is True
        and stage039_node.get("production_runtime_activation_performed") is False
        and stage039_node.get("persistent_queue_write_performed") is False
        and stage039_node.get("database_connection_performed") is False
        and stage039_node.get("raw_metadata_content_accessed") is False
        and stage039_node.get("fake_ids_business_data_used") is False
        and decision_node.get("current_task_id")
        == "IDS-V0_1-STAGE039-REVIEW"
        and decision_node.get("next_allowed_task_id")
        == "IDS-V0_1-STAGE040-P1"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE039"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE039-REVIEW"
        and roadmap_document.get("current_task_id")
        == "IDS-V0_1-STAGE039-REVIEW"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE040-P1-GATE"
        and roadmap_stage039.get("status") == "completed_reviewed_local"
        and roadmap_stage039.get("stop_gate", {}).get("status") == "passed"
        and roadmap_stage039_review.get("review_id") == "IDS-STAGE039-REVIEW"
        and roadmap_stage039_review.get("task_id")
        == "IDS-V0_1-STAGE039-REVIEW"
        and roadmap_stage039_review.get("status") == "completed"
        and "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_STAGE_REVIEW.md"
        in roadmap_stage039_review.get("evidence_refs", [])
    )
    stage040_node = stage_progress.get("STAGE-040")
    stage040_node = stage040_node if isinstance(stage040_node, dict) else {}
    roadmap_stage040 = next(
        (
            item
            for item in roadmap_stages
            if isinstance(item, dict) and item.get("stage_id") == "IDS-STAGE040"
        ),
        {},
    )
    roadmap_stage040 = roadmap_stage040 if isinstance(roadmap_stage040, dict) else {}
    roadmap_stage040_phases = roadmap_stage040.get("phases")
    roadmap_stage040_phases = (
        roadmap_stage040_phases
        if isinstance(roadmap_stage040_phases, list)
        else []
    )
    roadmap_stage040_phase1 = next(
        (
            item
            for item in roadmap_stage040_phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE040-P1"
        ),
        {},
    )
    roadmap_stage040_phase1 = (
        roadmap_stage040_phase1
        if isinstance(roadmap_stage040_phase1, dict)
        else {}
    )
    roadmap_stage040_phase2 = next(
        (
            item
            for item in roadmap_stage040_phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE040-P2"
        ),
        {},
    )
    roadmap_stage040_phase2 = (
        roadmap_stage040_phase2
        if isinstance(roadmap_stage040_phase2, dict)
        else {}
    )
    roadmap_stage040_phase3 = next(
        (
            item
            for item in roadmap_stage040_phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE040-P3"
        ),
        {},
    )
    roadmap_stage040_phase3 = (
        roadmap_stage040_phase3
        if isinstance(roadmap_stage040_phase3, dict)
        else {}
    )
    roadmap_stage040_phase4 = next(
        (
            item
            for item in roadmap_stage040_phases
            if isinstance(item, dict) and item.get("phase_id") == "IDS-STAGE040-P4"
        ),
        {},
    )
    roadmap_stage040_phase4 = (
        roadmap_stage040_phase4
        if isinstance(roadmap_stage040_phase4, dict)
        else {}
    )
    roadmap_stage040_review = roadmap_stage040.get("review")
    roadmap_stage040_review = (
        roadmap_stage040_review
        if isinstance(roadmap_stage040_review, dict)
        else {}
    )
    stage040_phase1_active = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage040_phase1_completed"
        and upload_gate.get("push_allowed") is False
        and stage040_node.get("status") == "stage040_phase1_completed"
        and stage040_node.get("completed_phases") == ["Phase 1"]
        and stage040_node.get("review_status") == "pending"
        and stage040_node.get("next_phase") == "Phase 2"
        and stage040_node.get("next_gate") == "IDS-STAGE040-P2-GATE"
        and stage040_node.get("current_task_id") == "IDS-V0_1-STAGE040-P1"
        and stage040_node.get("acceptance_id") == "ACC-STAGE-040"
        and stage040_node.get("acceptance_status")
        == "phase1_engineering_contract_complete"
        and stage040_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage040_node.get("source_member_match_count") == 1
        and stage040_node.get("source_member_sha256")
        == "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d"
        and stage040_node.get("phase2_entry_authorized") is True
        and stage040_node.get("backpressure_policy_contract_id")
        == "ids.backpressure_policy.v0_1.p1"
        and stage040_node.get("contract_state")
        == "PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED"
        and stage040_node.get("numeric_policy_values_assigned") is False
        and stage040_node.get("backpressure_runtime_performed") is False
        and stage040_node.get("queue_runtime_performed") is False
        and stage040_node.get("worker_runtime_performed") is False
        and stage040_node.get("lock_runtime_performed") is False
        and stage040_node.get("automatic_resume_performed") is False
        and stage040_node.get("cleanup_runtime_performed") is False
        and stage040_node.get("database_connection_performed") is False
        and stage040_node.get("raw_metadata_content_accessed") is False
        and stage040_node.get("fake_ids_business_data_used") is False
        and decision_node.get("current_task_id") == "IDS-V0_1-STAGE040-P1"
        and decision_node.get("next_allowed_task_id") == "IDS-V0_1-STAGE040-P2"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE040"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE040-P1"
        and roadmap_document.get("current_task_id") == "IDS-V0_1-STAGE040-P1"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE040-P2-GATE"
        and roadmap_stage040.get("status") == "in_progress"
        and roadmap_stage040_phase1.get("status")
        == "passed_with_local_evidence"
    )
    stage040_phase2_active = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage040_phase2_completed"
        and upload_gate.get("push_allowed") is False
        and stage040_node.get("status") == "stage040_phase2_completed"
        and stage040_node.get("completed_phases") == ["Phase 1", "Phase 2"]
        and stage040_node.get("review_status") == "pending"
        and stage040_node.get("next_phase") == "Phase 3"
        and stage040_node.get("next_gate") == "IDS-STAGE040-P3-GATE"
        and stage040_node.get("current_task_id") == "IDS-V0_1-STAGE040-P2"
        and stage040_node.get("acceptance_id") == "ACC-STAGE-040"
        and stage040_node.get("acceptance_status")
        == "phase2_isolated_decision_slice_complete"
        and stage040_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage040_node.get("source_member_match_count") == 1
        and stage040_node.get("source_member_sha256")
        == "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d"
        and stage040_node.get("phase3_entry_authorized") is True
        and stage040_node.get("backpressure_policy_contract_id")
        == "ids.backpressure_policy.v0_1.stage040.p2"
        and stage040_node.get("policy_version")
        == "ids.backpressure_policy.v0_1.stage040.p2"
        and stage040_node.get("contract_state")
        == "PHASE2_ISOLATED_DECISION_SLICE_ENABLED_PRODUCTION_DISABLED"
        and stage040_node.get("parameter_fact_level") == "PROPOSED"
        and stage040_node.get("production_calibrated") is False
        and stage040_node.get("production_calibration_task_id")
        == "TASK-OPME-B-001"
        and stage040_node.get("numeric_policy_values_assigned") is True
        and stage040_node.get("queue_soft_pressure_threshold") == 2
        and stage040_node.get("queue_hard_capacity_threshold") == 4
        and stage040_node.get("disk_free_bytes_threshold") == 1073741824
        and stage040_node.get("disk_reserve_bytes") == 536870912
        and stage040_node.get("external_api_budget_window_seconds") == 60
        and stage040_node.get("queue_low_watermark") == 1
        and stage040_node.get("observation_ttl_seconds") == 30
        and stage040_node.get("per_job_type_concurrency_limit") == 1
        and stage040_node.get("admission_rate_limit_per_window") == 4
        and stage040_node.get("isolated_slice_valid") is True
        and stage040_node.get("actual_project_disk_observation_performed") is True
        and stage040_node.get("backpressure_decision_runtime_performed") is True
        and stage040_node.get("production_runtime_activation_performed") is False
        and stage040_node.get("queue_runtime_performed") is False
        and stage040_node.get("worker_runtime_performed") is False
        and stage040_node.get("retry_scheduler_performed") is False
        and stage040_node.get("lock_runtime_performed") is False
        and stage040_node.get("automatic_resume_performed") is False
        and stage040_node.get("cleanup_runtime_performed") is False
        and stage040_node.get("database_connection_performed") is False
        and stage040_node.get("raw_metadata_content_accessed") is False
        and stage040_node.get("fake_ids_business_data_used") is False
        and decision_node.get("current_task_id") == "IDS-V0_1-STAGE040-P2"
        and decision_node.get("next_allowed_task_id") == "IDS-V0_1-STAGE040-P3"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE040"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE040-P2"
        and roadmap_document.get("current_task_id") == "IDS-V0_1-STAGE040-P2"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE040-P3-GATE"
        and roadmap_stage040.get("status") == "in_progress"
        and roadmap_stage040_phase2.get("status")
        == "passed_with_local_evidence"
    )
    stage040_phase3_active = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage040_phase3_completed"
        and upload_gate.get("push_allowed") is False
        and stage040_node.get("status") == "stage040_phase3_completed"
        and stage040_node.get("completed_phases")
        == ["Phase 1", "Phase 2", "Phase 3"]
        and stage040_node.get("review_status") == "pending"
        and stage040_node.get("next_phase") == "Phase 4"
        and stage040_node.get("next_gate") == "IDS-STAGE040-P4-GATE"
        and stage040_node.get("current_task_id") == "IDS-V0_1-STAGE040-P3"
        and stage040_node.get("acceptance_id") == "ACC-STAGE-040"
        and stage040_node.get("acceptance_status")
        == "phase3_scenarios_complete"
        and stage040_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage040_node.get("source_member_match_count") == 1
        and stage040_node.get("source_member_sha256")
        == "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d"
        and stage040_node.get("phase4_entry_authorized") is True
        and stage040_node.get("policy_version")
        == "ids.backpressure_policy.v0_1.stage040.p2"
        and stage040_node.get("phase2_contract_state")
        == "PHASE2_ISOLATED_DECISION_SLICE_ENABLED_PRODUCTION_DISABLED"
        and stage040_node.get("scenario_contract_id")
        == "ids.backpressure_policy.v0_1.stage040.p3.scenarios"
        and stage040_node.get("contract_state")
        == "PHASE3_SCENARIOS_ENABLED_PRODUCTION_DISABLED"
        and stage040_node.get("scenario_validation_valid") is True
        and stage040_node.get("scenario_count") == 8
        and stage040_node.get("passed_scenario_count") == 8
        and stage040_node.get("actual_isolated_worker_exception_performed") is True
        and stage040_node.get("actual_project_disk_observation_performed") is True
        and stage040_node.get("stage038_isolated_worker_exception_replayed") is True
        and stage040_node.get("reviewed_control_lock_proof_replayed") is True
        and stage040_node.get("process_termination_performed") is False
        and stage040_node.get("physical_drive_removal_performed") is False
        and stage040_node.get("disk_allocation_performed") is False
        and stage040_node.get("external_api_call_performed") is False
        and stage040_node.get("protected_ref_delete_performed") is False
        and stage040_node.get("production_lock_runtime_performed") is False
        and stage040_node.get("crash_recovery_runtime_performed") is False
        and stage040_node.get("production_runtime_activation_performed") is False
        and stage040_node.get("queue_runtime_performed") is False
        and stage040_node.get("worker_runtime_performed") is False
        and stage040_node.get("retry_scheduler_performed") is False
        and stage040_node.get("lock_runtime_performed") is False
        and stage040_node.get("automatic_resume_performed") is False
        and stage040_node.get("cleanup_runtime_performed") is False
        and stage040_node.get("database_connection_performed") is False
        and stage040_node.get("raw_metadata_content_accessed") is False
        and stage040_node.get("fake_ids_business_data_used") is False
        and decision_node.get("current_task_id") == "IDS-V0_1-STAGE040-P3"
        and decision_node.get("next_allowed_task_id") == "IDS-V0_1-STAGE040-P4"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE040"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE040-P3"
        and roadmap_document.get("current_task_id") == "IDS-V0_1-STAGE040-P3"
        and roadmap_document.get("next_gate_id") == "IDS-STAGE040-P4-GATE"
        and roadmap_stage040.get("status") == "in_progress"
        and roadmap_stage040_phase3.get("status")
        == "passed_with_local_evidence"
    )
    stage040_phase4_active = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status")
        == "stage040_phase4_completed_review_pending"
        and upload_gate.get("push_allowed") is False
        and stage040_node.get("status")
        == "stage040_phase4_completed_review_pending"
        and stage040_node.get("completed_phases")
        == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        and stage040_node.get("review_status") == "pending"
        and stage040_node.get("next_phase") == "stage_review"
        and stage040_node.get("next_gate") == "IDS-STAGE040-REVIEW-GATE"
        and stage040_node.get("current_task_id") == "IDS-V0_1-STAGE040-P4"
        and stage040_node.get("acceptance_id") == "ACC-STAGE-040"
        and stage040_node.get("acceptance_status")
        == "phase4_delivery_complete_review_pending"
        and stage040_node.get("source_verification_status") == "SOURCE_VERIFIED"
        and stage040_node.get("source_member_match_count") == 1
        and stage040_node.get("source_member_sha256")
        == "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d"
        and stage040_node.get("policy_version")
        == "ids.backpressure_policy.v0_1.stage040.p2"
        and stage040_node.get("contract_state")
        == "PHASE4_CLOSEOUT_EVIDENCE_REVIEW_PENDING"
        and stage040_node.get("delivery_contract_schema")
        == "ids.stage040.backpressure.phase4.delivery.v1"
        and stage040_node.get("delivery_contract_valid") is True
        and stage040_node.get("delivery_result")
        == "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED"
        and stage040_node.get("stage_review_status") == "pending_next_run"
        and stage040_node.get("required_job_type_count") == 8
        and stage040_node.get("required_job_state_count") == 11
        and stage040_node.get("required_terminal_state_count") == 4
        and stage040_node.get("required_transition_count") == 21
        and stage040_node.get("required_pressure_signal_count") == 7
        and stage040_node.get("failure_retry_log_attempt_count") == 3
        and stage040_node.get("failure_retry_log_retry_count") == 2
        and stage040_node.get("automatic_recovery_eligible_case_count") == 0
        and stage040_node.get("successful_automatic_recovery_case_count") == 0
        and stage040_node.get("reviewed_failure_retry_log_replayed") is True
        and stage040_node.get("reviewed_transport_shutdown_replayed") is True
        and stage040_node.get("process_termination_performed") is False
        and stage040_node.get("physical_drive_removal_performed") is False
        and stage040_node.get("disk_allocation_performed") is False
        and stage040_node.get("external_api_call_performed") is False
        and stage040_node.get("protected_ref_delete_performed") is False
        and stage040_node.get("production_lock_runtime_performed") is False
        and stage040_node.get("crash_recovery_runtime_performed") is False
        and stage040_node.get("production_runtime_activation_performed") is False
        and stage040_node.get("queue_runtime_performed") is False
        and stage040_node.get("worker_runtime_performed") is False
        and stage040_node.get("retry_scheduler_performed") is False
        and stage040_node.get("lock_runtime_performed") is False
        and stage040_node.get("automatic_resume_performed") is False
        and stage040_node.get("cleanup_runtime_performed") is False
        and stage040_node.get("whole_stage_review_performed") is False
        and stage040_node.get("batch_review_performed") is False
        and stage040_node.get("database_connection_performed") is False
        and stage040_node.get("raw_metadata_content_accessed") is False
        and stage040_node.get("fake_ids_business_data_used") is False
        and decision_node.get("current_task_id") == "IDS-V0_1-STAGE040-P4"
        and decision_node.get("next_allowed_task_id")
        == "IDS-V0_1-STAGE040-REVIEW"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE040"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE040-P4"
        and roadmap_document.get("current_task_id") == "IDS-V0_1-STAGE040-P4"
        and roadmap_document.get("next_gate_id")
        == "IDS-STAGE040-REVIEW-GATE"
        and roadmap_stage040.get("status") == "in_progress"
        and roadmap_stage040_phase4.get("status")
        == "passed_with_local_evidence"
    )
    stage040_reviewed_local = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status") == "stage040_completed_reviewed_local"
        and upload_gate.get("push_allowed") is False
        and stage040_node.get("status") == "stage040_completed_reviewed_local"
        and stage040_node.get("completed_phases")
        == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        and stage040_node.get("review_status") == "passed"
        and stage040_node.get("next_phase") == "batch_review_gate"
        and stage040_node.get("next_gate")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and stage040_node.get("current_task_id")
        == "IDS-V0_1-STAGE040-REVIEW"
        and stage040_node.get("acceptance_id") == "ACC-STAGE-040"
        and stage040_node.get("acceptance_status") == "reviewed_local_passed"
        and stage040_node.get("stage_review_schema")
        == "ids.stage040.backpressure.stage_review.v1"
        and stage040_node.get("stage_review_status")
        == "completed_reviewed_local"
        and stage040_node.get("stage_review_result")
        == "PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED"
        and stage040_node.get("review_finding_count") == 3
        and stage040_node.get("review_critical_finding_count") == 1
        and stage040_node.get("review_important_finding_count") == 2
        and stage040_node.get("review_minor_finding_count") == 0
        and stage040_node.get("review_findings_repaired") is True
        and stage040_node.get("whole_stage_review_performed") is True
        and stage040_node.get("batch_review_performed") is False
        and stage040_node.get("production_runtime_activation_performed") is False
        and stage040_node.get("raw_metadata_content_accessed") is False
        and stage040_node.get("fake_ids_business_data_used") is False
        and decision_node.get("current_task_id")
        == "IDS-V0_1-STAGE040-REVIEW"
        and decision_node.get("next_allowed_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE040"
        and roadmap_document.get("current_phase_id") == "IDS-STAGE040-REVIEW"
        and roadmap_document.get("current_task_id")
        == "IDS-V0_1-STAGE040-REVIEW"
        and roadmap_document.get("next_gate_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and roadmap_stage040.get("status") == "completed_reviewed_local"
        and roadmap_stage040.get("stop_gate", {}).get("status") == "passed"
        and roadmap_stage040_review.get("review_id") == "IDS-STAGE040-REVIEW"
        and roadmap_stage040_review.get("task_id")
        == "IDS-V0_1-STAGE040-REVIEW"
        and roadmap_stage040_review.get("status") == "completed"
        and "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_STAGE_REVIEW.md"
        in roadmap_stage040_review.get("evidence_refs", [])
    )
    batch031_040_reviewed_pending_upload = (
        batch_document.get("batch_id") == "IDS-V0_1-BATCH-031-040"
        and batch_document.get("status")
        == "reviewed_ready_for_upload_no_github_upload"
        and batch_document.get("review_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and batch_document.get("review_evidence_ref")
        == "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md"
        and upload_gate.get("push_allowed") is False
        and upload_gate.get("review_gate") == "BATCH031_040_REVIEW_GATE"
        and upload_gate.get("gate_task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and decision_node.get("current_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and decision_node.get("next_allowed_task_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
        and decision_node.get("github_upload_allowed") is False
        and roadmap_document.get("current_stage_id") == "IDS-STAGE040"
        and roadmap_document.get("current_phase_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and roadmap_document.get("current_task_id")
        == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        and roadmap_document.get("next_gate_id")
        == "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
    )
    batch031_040_upload_gate_active = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "local_batch_upload_gate_passed_pending_github_merge"'
        in batch_text
        and "push_allowed: true" in batch_text
        and 'review_gate: "BATCH031_040_REVIEW_GATE"' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"'
        in batch_text
        and 'gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_GATE.md"'
        in batch_text
        and 'current_stage_id: "IDS-STAGE040"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"'
        in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"'
        in roadmap_text
        and 'next_gate_id: "IDS-V0_1-BATCH-031-040-GITHUB-MERGE"'
        in roadmap_text
    )
    batch031_040_uploaded_to_main = (
        'batch_id: "IDS-V0_1-BATCH-031-040"' in batch_text
        and 'status: "uploaded_to_github_main"' in batch_text
        and "push_allowed: true" in batch_text
        and 'review_gate: "BATCH031_040_REVIEW_GATE"' in batch_text
        and 'gate_task_id: "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"'
        in batch_text
        and 'gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_GATE.md"'
        in batch_text
        and re.search(
            r'github_pr: "https://github\.com/LinzeColin/CodexProject/pull/\d+"',
            batch_text,
        )
        is not None
        and re.search(r'merged_sha: "[0-9a-f]{40}"', batch_text)
        is not None
        and "post_merge_open_prs: 0" in batch_text
        and "post_merge_open_issues: 0" in batch_text
        and 'current_stage_id: "IDS-STAGE040"' in roadmap_text
        and 'current_phase_id: "IDS-V0_1-BATCH-031-040-MAIN-MERGED"'
        in roadmap_text
        and 'current_task_id: "IDS-V0_1-BATCH-031-040-MAIN-MERGED"'
        in roadmap_text
        and 'next_gate_id: "IDS-STAGE041-P1-GATE"' in roadmap_text
    )
    batch_terminal_state = batch_upload_gate_active or batch_uploaded_to_main
    later_stage_state = (
        batch_terminal_state
        or stage011_phase2_active
        or stage011_phase3_active
        or stage011_phase4_closeout
        or stage012_phase1_active
        or stage012_phase2_active
        or stage012_phase3_active
        or stage012_phase4_closeout
        or stage013_phase1_active
        or stage013_phase2_active
        or stage013_phase3_active
        or stage013_phase4_closeout
        or stage014_phase1_active
        or stage014_phase2_active
        or stage014_phase3_active
        or stage014_phase4_closeout
        or stage015_phase1_active
        or stage015_phase2_active
        or stage015_phase3_active
        or stage015_phase4_closeout
        or stage016_phase1_active
        or stage016_phase2_active
        or stage016_phase3_active
        or stage016_phase4_closeout
        or stage017_phase1_active
        or stage017_phase2_active
        or stage017_phase3_active
        or stage017_phase4_closeout
        or stage018_phase1_active
        or stage018_phase2_active
        or stage018_phase3_active
        or stage018_phase4_closeout
        or stage019_phase1_active
        or stage019_phase2_active
        or stage019_phase3_active
        or stage019_phase4_closeout
        or stage020_phase1_active
        or stage020_phase2_active
        or stage020_phase3_active
        or stage020_phase4_closeout
        or batch011_020_reviewed_pending_upload
        or batch011_020_upload_gate_active
        or batch011_020_uploaded_to_main
        or stage021_phase1_active
        or stage021_phase2_active
        or stage021_phase3_active
        or stage021_phase4_closeout
        or stage022_phase1_active
        or stage022_phase2_active
        or stage022_phase3_active
        or stage022_phase4_closeout
        or stage023_phase1_active
        or stage023_phase2_active
        or stage023_phase3_active
        or stage023_phase4_closeout
        or stage024_phase1_active
        or stage024_phase2_active
        or stage024_phase3_active
        or stage024_phase4_closeout
        or stage025_phase1_active
        or stage025_phase2_active
        or stage025_phase3_active
        or stage025_phase4_closeout
        or stage026_phase1_active
        or stage026_phase2_active
        or stage026_phase3_active
        or stage026_phase4_closeout
        or stage027_phase1_active
        or stage027_phase2_active
        or stage027_phase3_active
        or stage027_phase4_closeout
        or stage028_phase1_active
        or stage028_phase2_active
        or stage028_phase3_active
        or stage028_phase4_closeout
        or stage029_phase1_active
        or stage029_phase2_active
        or stage029_phase3_active
        or stage029_phase4_closeout
        or stage030_phase1_active
        or stage030_phase2_active
        or stage030_phase3_active
        or stage030_phase4_closeout
        or batch021_030_reviewed_pending_upload
        or batch021_030_upload_gate_active
        or batch021_030_uploaded_to_main
        or stage031_phase1_active
        or stage031_phase2_active
        or stage031_phase3_active
        or stage031_phase4_closeout
        or stage031_reviewed_local
        or stage032_phase1_active
        or stage032_phase2_active
        or stage032_phase3_active
        or stage032_phase4_closeout
        or stage032_reviewed_local
        or stage033_phase1_active
        or stage033_phase2_active
        or stage033_phase3_active
        or stage033_phase4_closeout
        or stage033_reviewed_local
        or stage034_phase1_active
        or stage034_phase2_active
        or stage034_phase3_active
        or stage034_phase4_closeout
        or stage034_reviewed_local
        or stage035_phase1_active
        or stage035_phase2_active
        or stage035_phase3_active
        or stage035_phase4_closeout
        or stage035_reviewed_local
        or stage036_phase1_active
        or stage036_phase2_active
        or stage036_phase3_active
        or stage036_phase4_closeout
        or stage036_reviewed_local
        or stage037_phase1_active
        or stage037_phase2_active
        or stage037_phase3_active
        or stage037_phase4_closeout
        or stage037_reviewed_local
        or stage038_phase1_active
        or stage038_source_reverified
        or stage038_phase2_active
        or stage038_phase3_active
        or stage038_phase4_closeout
        or stage038_reviewed_local
        or stage039_phase1_active
        or stage039_phase2_active
        or stage039_phase3_active
        or stage039_phase4_closeout
        or stage039_reviewed_local
        or stage040_phase1_active
        or stage040_phase2_active
        or stage040_phase3_active
        or stage040_phase4_active
        or stage040_reviewed_local
        or batch031_040_reviewed_pending_upload
        or batch031_040_upload_gate_active
        or batch031_040_uploaded_to_main
    )
    phase2_completed = '      - "Phase 2"' in batch_text
    stage005_active_or_complete = (
        'STAGE-005:\n    status: "in_progress"' in batch_text
        or 'STAGE-005:\n    status: "completed_local"' in batch_text
        or later_stage_state
    )
    current_task_allowed = (
        'current_task_id: "IDS-V0_1-STAGE005-P2"' in batch_text
        or 'current_task_id: "IDS-V0_1-STAGE005-P3"' in batch_text
        or 'current_task_id: "IDS-V0_1-STAGE005-P4"' in batch_text
        or later_stage_state
    )
    next_phase_allowed = (
        'next_phase: "Phase 3"' in batch_text
        or 'next_phase: "Phase 2"' in batch_text
        or 'next_phase: "Phase 4"' in batch_text
        or 'next_phase: "stage_review_gate"' in batch_text
        or 'next_phase: "batch_review_gate"' in batch_text
        or 'next_stage: "STAGE-006"' in batch_text
        or 'next_stage: "STAGE-012"' in batch_text
        or 'next_stage: "STAGE-013"' in batch_text
        or 'next_stage: "STAGE-014"' in batch_text
        or 'next_stage: "STAGE-015"' in batch_text
        or 'next_stage: "STAGE-016"' in batch_text
        or 'next_stage: "STAGE-017"' in batch_text
        or 'next_stage: "STAGE-018"' in batch_text
        or 'next_stage: "STAGE-019"' in batch_text
        or 'next_stage: "STAGE-020"' in batch_text
        or 'next_stage: "STAGE-021"' in batch_text
        or 'next_stage: "STAGE-022"' in batch_text
        or 'next_stage: "STAGE-026"' in batch_text
        or 'next_stage: "STAGE-027"' in batch_text
        or 'next_stage: "STAGE-028"' in batch_text
        or 'next_stage: "STAGE-029"' in batch_text
        or 'next_stage: "STAGE-030"' in batch_text
        or 'next_stage: "STAGE-031"' in batch_text
        or 'next_stage: "STAGE-032"' in batch_text
        or 'next_stage: "STAGE-033"' in batch_text
        or 'next_stage: "STAGE-034"' in batch_text
        or later_stage_state
    )
    current_phase_allowed = (
        'current_phase_id: "IDS-STAGE005-P2"' in roadmap_text
        or 'current_phase_id: "IDS-STAGE005-P3"' in roadmap_text
        or 'current_phase_id: "IDS-STAGE005-P4"' in roadmap_text
        or later_stage_state
    )
    current_roadmap_task_allowed = (
        'current_task_id: "IDS-V0_1-STAGE005-P2"' in roadmap_text
        or 'current_task_id: "IDS-V0_1-STAGE005-P3"' in roadmap_text
        or 'current_task_id: "IDS-V0_1-STAGE005-P4"' in roadmap_text
        or later_stage_state
    )
    next_gate_allowed = (
        'next_gate_id: "IDS-STAGE005-P3-GATE"' in roadmap_text
        or 'next_gate_id: "IDS-STAGE005-P4-GATE"' in roadmap_text
        or 'next_gate_id: "IDS-STAGE006-P1-GATE"' in roadmap_text
        or later_stage_state
    )
    checks = {
        "stage005_active_or_complete": stage005_active_or_complete,
        "phase2_completed": phase2_completed,
        "current_task_allowed": current_task_allowed,
        "next_phase_allowed": next_phase_allowed,
        "push_locked": "push_allowed: false" in batch_text or later_stage_state,
        "current_stage005": 'current_stage_id: "IDS-STAGE005"' in roadmap_text
        or later_stage_state,
        "current_phase_allowed": current_phase_allowed,
        "current_roadmap_task_allowed": current_roadmap_task_allowed,
        "next_gate_allowed": next_gate_allowed,
        "roadmap_phase2_completed": 'phase_id: "IDS-STAGE005-P2"' in roadmap_text
        and 'status: "passed_with_local_evidence"' in roadmap_text
        or later_stage_state,
    }
    structured_checks = evaluate_current_state_consistency(batch_text, roadmap_text)
    if structured_checks["yaml_documents_parsed"] and (
        require_structured or structured_checks["current_stage_node_resolved"]
    ):
        checks.update(
            {
                f"current_state_{name}": value
                for name, value in structured_checks.items()
            }
        )
    return checks


def evaluate_data_boundary(root_lock_text: str, batch_text: str, boundary_text: str) -> dict[str, bool]:
    raw_root = "/Users/linzezhang/Downloads/IDS_MetaData"
    boundary_ref = "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md"
    combined = "\n".join((root_lock_text, batch_text, boundary_text))
    boundary_mutation_ban = (
        "do not modify" in boundary_text
        or "must not create, edit, delete, move" in boundary_text
        or "Raw directory content modified: `no`" in boundary_text
    )
    return {
        "raw_root_recorded": raw_root in combined,
        "boundary_ref_recorded": boundary_ref in root_lock_text and boundary_ref in batch_text,
        "read_only_policy_recorded": "read-only" in combined and boundary_mutation_ban,
        "raw_content_not_committed": "raw database content is not committed" in root_lock_text
        and "Raw directory content copied into GitHub: `no`" in boundary_text,
        "real_data_only_policy_recorded": "real_data_only_policy" in root_lock_text
        and "Real Data Only Policy" in boundary_text
        and "fake business data" in combined,
    }


def build_stage037_review_governance_report(root: Path | None = None) -> dict:
    """Return only the structured evidence needed by the Stage037 review gate."""
    root = (root or Path(__file__).resolve().parents[3]).resolve()
    required_paths = {
        "review_artifact": root
        / "docs/pursuing_goal/ids_v0_1/STAGE037_STAGE_REVIEW.md",
        "batch_lock": root
        / "docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "roadmap": root / "docs/governance/roadmap.yaml",
        "events": root / "docs/governance/events.jsonl",
        "root_lock": root / "docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml",
        "raw_boundary": root
        / "docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
        "validator": Path(__file__).resolve(),
    }
    missing_required_files = [
        name for name, path in required_paths.items() if not path.is_file()
    ]

    def read_text(name: str) -> str:
        path = required_paths[name]
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    events, event_json_errors = _parse_events(required_paths["events"])
    event_ids = {
        event.get("event_id") for event in events if isinstance(event, dict)
    }
    missing_event_ids = [
        event_id for event_id in REQUIRED_EVENT_IDS if event_id not in event_ids
    ]
    event_semantic_errors = evaluate_required_event_semantics(events)
    batch_text = read_text("batch_lock")
    roadmap_text = read_text("roadmap")
    phase_state_checks = evaluate_phase_state(
        batch_text, roadmap_text, require_structured=True
    )
    data_boundary_checks = evaluate_data_boundary(
        read_text("root_lock"), batch_text, read_text("raw_boundary")
    )
    tracked_forbidden_runtime_files = [
        path for path in _git_ls_files(root) if is_forbidden_runtime_path(path)
    ]
    issues: list[str] = []
    if missing_required_files:
        issues.append("missing Stage037 review governance files")
    if event_json_errors or event_semantic_errors or missing_event_ids:
        issues.append("Stage037 review event governance is invalid")
    if not all(phase_state_checks.values()):
        issues.append("Stage037 reviewed-local state is inconsistent")
    if not all(data_boundary_checks.values()):
        issues.append("IDS raw or real-data-only boundary is incomplete")
    if tracked_forbidden_runtime_files:
        issues.append("forbidden runtime files are tracked")
    return {
        "acceptance_id": ACCEPTANCE_ID,
        "data_boundary_checks": data_boundary_checks,
        "event_json_errors": event_json_errors,
        "event_semantic_errors": event_semantic_errors,
        "issues": issues,
        "missing_event_ids": missing_event_ids,
        "missing_required_files": missing_required_files,
        "phase_state_checks": phase_state_checks,
        "stage": STAGE,
        "tracked_forbidden_runtime_files": tracked_forbidden_runtime_files,
        "valid": not issues,
    }


def build_stage038_review_governance_report(root: Path | None = None) -> dict:
    """Return structured governance evidence for the Stage038 review gate."""
    root = (root or Path(__file__).resolve().parents[3]).resolve()
    required_paths = {
        "review_artifact": root
        / "docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
        "review_checker": root / "scripts/check_worker_queue_stage_review.py",
        "batch_lock": root
        / "docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
        "roadmap": root / "docs/governance/roadmap.yaml",
        "events": root / "docs/governance/events.jsonl",
        "root_lock": root / "docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml",
        "raw_boundary": root
        / "docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
        "validator": Path(__file__).resolve(),
    }
    missing_required_files = [
        name for name, path in required_paths.items() if not path.is_file()
    ]

    def read_text(name: str) -> str:
        path = required_paths[name]
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    events, event_json_errors = _parse_events(required_paths["events"])
    event_ids = {
        event.get("event_id") for event in events if isinstance(event, dict)
    }
    missing_event_ids = [
        event_id for event_id in REQUIRED_EVENT_IDS if event_id not in event_ids
    ]
    event_semantic_errors = evaluate_required_event_semantics(events)
    batch_text = read_text("batch_lock")
    roadmap_text = read_text("roadmap")
    phase_state_checks = evaluate_phase_state(
        batch_text, roadmap_text, require_structured=True
    )
    data_boundary_checks = evaluate_data_boundary(
        read_text("root_lock"), batch_text, read_text("raw_boundary")
    )
    tracked_forbidden_runtime_files = [
        path for path in _git_ls_files(root) if is_forbidden_runtime_path(path)
    ]
    issues: list[str] = []
    if missing_required_files:
        issues.append("missing Stage038 review governance files")
    if event_json_errors or event_semantic_errors or missing_event_ids:
        issues.append("Stage038 review event governance is invalid")
    if not all(phase_state_checks.values()):
        issues.append("Stage038 reviewed-local state is inconsistent")
    if not all(data_boundary_checks.values()):
        issues.append("IDS raw or real-data-only boundary is incomplete")
    if tracked_forbidden_runtime_files:
        issues.append("forbidden runtime files are tracked")
    return {
        "acceptance_id": ACCEPTANCE_ID,
        "data_boundary_checks": data_boundary_checks,
        "event_json_errors": event_json_errors,
        "event_semantic_errors": event_semantic_errors,
        "issues": issues,
        "missing_event_ids": missing_event_ids,
        "missing_required_files": missing_required_files,
        "phase_state_checks": phase_state_checks,
        "stage": STAGE,
        "tracked_forbidden_runtime_files": tracked_forbidden_runtime_files,
        "valid": not issues,
    }


def build_stage_review_governance_report(root: Path | None = None) -> dict:
    """Return current structured stage-review governance evidence."""
    return build_stage038_review_governance_report(root)


def build_report(root: Path | None = None) -> dict:
    root = (root or Path(__file__).resolve().parents[3]).resolve()
    repo_root = _repo_root(root)
    issues: list[str] = []

    tracked_paths = _git_ls_files(root)
    changed_paths = _git_changed_paths(root)
    missing_required_files = [
        path for path in REQUIRED_FILES if not (repo_root / path).is_file()
    ]
    tracked_forbidden_runtime_files = [
        path for path in tracked_paths if is_forbidden_runtime_path(path)
    ]
    forbidden_changed_paths = [
        path for path in changed_paths if is_forbidden_runtime_path(path)
    ]
    unexpected_changed_paths = [
        path for path in changed_paths if path.startswith("KM_IDSystem/") and not _is_allowed_changed_path(path)
    ]

    events_path = root / "docs/governance/events.jsonl"
    events, event_json_errors = _parse_events(events_path)
    event_ids = {event.get("event_id") for event in events}
    missing_event_ids = [event_id for event_id in REQUIRED_EVENT_IDS if event_id not in event_ids]
    event_semantic_errors = evaluate_required_event_semantics(events)

    batch_paths = [
        root / "docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml",
        root / "docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml",
        root / "docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml",
        root / "docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
    ]
    batch_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in batch_paths
        if path.is_file()
    )
    root_lock_text = (root / "docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml").read_text(
        encoding="utf-8"
    )
    boundary_text = (
        root / "docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md"
    ).read_text(encoding="utf-8")
    roadmap_text = (root / "docs/governance/roadmap.yaml").read_text(encoding="utf-8")
    readme_text = (root / "README.md").read_text(encoding="utf-8")
    handoff_text = (root / "docs/HANDOFF.md").read_text(encoding="utf-8")

    def read_optional(rel_path: str) -> str:
        path = root / rel_path
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    phase_state_checks = evaluate_phase_state(
        batch_text, roadmap_text, require_structured=True
    )
    source_reverification_checks = evaluate_stage038_source_reverification(
        read_optional("docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml"),
        roadmap_text,
        read_optional("docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md"),
        read_optional(
            "docs/pursuing_goal/ids_v0_1/"
            "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md"
        ),
        read_optional(
            "docs/pursuing_goal/ids_v0_1/"
            "STAGE038_PHASE1_SOURCE_REVERIFICATION.md"
        ),
        read_optional(
            "docs/pursuing_goal/ids_v0_1/"
            "STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md"
        ),
    )
    data_boundary_checks = evaluate_data_boundary(root_lock_text, batch_text, boundary_text)
    owner_text_checks = {
        "readme_current_name": CURRENT_PRODUCT_NAME in readme_text,
        "handoff_current_name": CURRENT_PRODUCT_NAME in handoff_text,
        "readme_legacy_policy": "Legacy aliases" in readme_text,
        "handoff_legacy_policy": "Legacy aliases" in handoff_text,
    }
    surface_counts = _surface_counts(tracked_paths)
    accepted_name_hits = _text_checks(root, tracked_paths)

    if missing_required_files:
        issues.append("missing required files")
    if event_json_errors:
        issues.append("events.jsonl has invalid JSON lines")
    if missing_event_ids:
        issues.append("missing required stage events")
    if event_semantic_errors:
        issues.append("required stage event semantics are invalid")
    if tracked_forbidden_runtime_files:
        issues.append("forbidden runtime files are tracked")
    if forbidden_changed_paths:
        issues.append("forbidden runtime path changed")
    if unexpected_changed_paths:
        issues.append("unexpected KM_IDSystem path changed")
    if not all(phase_state_checks.values()):
        issues.append("phase state is not within the accepted STAGE-005 Phase 2-4 progression")
    if not all(source_reverification_checks.values()):
        issues.append("STAGE-038 source-reverification state is inconsistent")
    if not all(data_boundary_checks.values()):
        issues.append("IDS metadata raw data boundary or real-data-only policy is incomplete")
    if not all(owner_text_checks.values()):
        issues.append("owner-facing identity or legacy policy text is missing")
    if any(count == 0 for count in surface_counts.values()):
        issues.append("one or more governance regression surfaces are empty")
    for accepted_name, hit_count in accepted_name_hits.items():
        if hit_count == 0:
            issues.append(f"accepted name missing from tracked text: {accepted_name}")

    return {
        "acceptance_id": ACCEPTANCE_ID,
        "accepted_name_hits": accepted_name_hits,
        "phase_state_checks": phase_state_checks,
        "source_reverification_checks": source_reverification_checks,
        "changed_paths": changed_paths,
        "event_json_errors": event_json_errors,
        "event_semantic_errors": event_semantic_errors,
        "data_boundary_checks": data_boundary_checks,
        "forbidden_changed_paths": forbidden_changed_paths,
        "issues": issues,
        "missing_event_ids": missing_event_ids,
        "missing_required_files": missing_required_files,
        "owner_text_checks": owner_text_checks,
        "stage": STAGE,
        "surface_counts": surface_counts,
        "tracked_forbidden_runtime_files": tracked_forbidden_runtime_files,
        "tracked_km_ids_files": len(tracked_paths),
        "unexpected_changed_paths": unexpected_changed_paths,
        "valid": not issues,
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
