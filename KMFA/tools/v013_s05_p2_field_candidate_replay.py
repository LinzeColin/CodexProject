#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S05-P2 field candidate replay evidence.

This phase replays the existing public-safe S05-P2 A0 golden fixture candidate
artifacts and active owner/authorized downgrade decision. It does not read the
local raw data inbox and does not publish raw values, normalized values, raw
filenames, sheet names, ZIP member names, or business plaintext.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.a0_golden_fixture import (
    DEFAULT_OUTPUT_CANDIDATES,
    DEFAULT_OUTPUT_MANIFEST,
    validate_a0_golden_fixture,
)
from KMFA.tools.check_s05_p2_completion_gate import evaluate_gate, validate_active_decision
from KMFA.tools.check_s05_p2_excel_owner_decision import (
    DEFAULT_CONTROL_EVENTS,
    DEFAULT_FIXTURE_CANDIDATES,
    DEFAULT_FIXTURE_MANIFEST,
    DEFAULT_PACKET,
    DEFAULT_RESOLUTION_EVENTS,
    validate_excel_owner_decision,
)
from KMFA.tools.check_s05_p2_owner_decision_templates import DEFAULT_TEMPLATES_DIR, validate_templates
from KMFA.tools.check_v013_s05_p1_a0_file_registration import validate_v013_s05_p1_a0_file_registration
from KMFA.tools.preview_s05_p2_owner_decision_application import build_preview
from KMFA.tools.v013_s05_p1_a0_file_registration import MANIFEST_PATH as S05_P1_MANIFEST_PATH
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S05_P2_FIELD_CANDIDATE_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/field_candidate_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/field_candidate_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
ACTIVE_DECISION_PATH = Path(
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json"
)
ACTIVE_PREVIEW_PATH = Path(
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_decision_application_preview.json"
)
TASK_ID = "KMFA-V013-S05-P2-FIELD-CANDIDATE-REPLAY-20260702"
SCHEMA_VERSION = "kmfa.v013_s05_p2_field_candidate_replay.v1"


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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path} contains non-object JSONL row")
            records.append(value)
    return records


def summarize_fixture(manifest: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    validate_a0_golden_fixture(manifest, candidates)
    summary = manifest["field_summary"]
    source_format_counts = Counter(
        str((item.get("source_binding") or {}).get("source_file_format", "unknown")) for item in candidates
    )
    q3_candidate_count = sum(
        1 for item in candidates if (item.get("quality_state") or {}).get("machine_candidate_quality_grade") == "Q3"
    )
    q4_human_confirmed_count = sum(
        1 for item in candidates if (item.get("quality_state") or {}).get("q4_human_confirmed") is True
    )
    q5_calculation_baseline_allowed_count = sum(
        1 for item in candidates if (item.get("quality_state") or {}).get("q5_calculation_baseline_allowed") is True
    )
    pending_candidate_ids = {
        str(item.get("candidate_id"))
        for item in candidates
        if not (item.get("value_binding") or {}).get("raw_value_hash")
    }
    return {
        "a0_project_candidates": summary["a0_project_candidates"],
        "required_fields_per_candidate": summary["required_fields_per_candidate"],
        "fixture_candidate_count": summary["fixture_candidate_count"],
        "private_value_hash_recorded_count": summary["private_value_hash_recorded_count"],
        "private_value_pending_count": summary["private_value_pending_count"],
        "source_anchor_recorded_count": summary["source_anchor_recorded_count"],
        "source_anchor_pending_count": summary["source_anchor_pending_count"],
        "source_format_counts": dict(sorted(source_format_counts.items())),
        "q3_field_candidate_count": q3_candidate_count,
        "q4_human_confirmed_count": q4_human_confirmed_count,
        "q5_calculation_baseline_allowed_count": q5_calculation_baseline_allowed_count,
        "pending_source_candidate_count": len(pending_candidate_ids),
    }


def validate_legacy_s05_p2() -> dict[str, Any]:
    fixture_manifest = read_json(DEFAULT_OUTPUT_MANIFEST)
    fixture_candidates = read_jsonl(DEFAULT_OUTPUT_CANDIDATES)
    fixture_summary = summarize_fixture(fixture_manifest, fixture_candidates)

    packet = validate_excel_owner_decision(
        packet_path=DEFAULT_PACKET,
        fixture_manifest_path=DEFAULT_FIXTURE_MANIFEST,
        fixture_candidates_path=DEFAULT_FIXTURE_CANDIDATES,
        resolution_events_path=DEFAULT_RESOLUTION_EVENTS,
        control_events_path=DEFAULT_CONTROL_EVENTS,
    )
    templates = validate_templates(DEFAULT_TEMPLATES_DIR)
    decision_code = validate_active_decision(ACTIVE_DECISION_PATH)
    gate = evaluate_gate(fixture_manifest, fixture_candidates, decision_code)
    preview = build_preview(ACTIVE_DECISION_PATH)
    preview_recorded = read_json(ACTIVE_PREVIEW_PATH)
    if preview != preview_recorded:
        raise ValueError("active owner decision preview does not match deterministic replay")

    return {
        "fixture_summary": fixture_summary,
        "owner_packet_status": packet["resolution_status"],
        "owner_allowed_decision_count": len(packet["allowed_decision_codes"]),
        "owner_template_count": len(templates),
        "active_decision_code": decision_code,
        "completion_gate_ready": gate.ready,
        "completion_gate_mode": gate.mode,
        "completion_gate_reason": gate.reason,
        "completion_gate_pending_fields": gate.pending_fields,
        "active_preview_status": preview["application_status"],
        "active_preview_candidate_role": preview["candidate_application"]["candidate_role"],
        "active_preview_q5_exclusion_confirmed": preview["candidate_application"].get("q5_exclusion_confirmed") is True,
    }


def build_manifest() -> dict[str, Any]:
    s05_p1 = validate_v013_s05_p1_a0_file_registration()
    legacy = validate_legacy_s05_p2()
    fixture_summary = legacy["fixture_summary"]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S05",
        "stage_name": "v0.1.3 A0 authority project cost golden baseline",
        "phase_id": "S05-P2",
        "phase_name": "field-level golden baseline candidate replay",
        "phase_scope": "v013_s05_p2_field_candidate_replay_only",
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_owner_downgrade_replayed",
        "completed_task_ids": ["S5PBT01", "S5PBT02", "S5PBT03"],
        "s05_p1_dependency_validated": (
            s05_p1.get("phase_id") == "S05-P1"
            and s05_p1.get("github_upload_performed") is False
            and s05_p1.get("github_upload_deferred_until_stage10_batch") is True
        ),
        "s05_p1_dependency_ref": str(S05_P1_MANIFEST_PATH),
        "legacy_s05_p2_dependency_validated": True,
        "field_candidate_summary": fixture_summary,
        "owner_decision_summary": {
            "owner_packet_status": legacy["owner_packet_status"],
            "owner_allowed_decision_count": legacy["owner_allowed_decision_count"],
            "owner_template_count": legacy["owner_template_count"],
            "active_decision_present": True,
            "active_actor_role_validated": True,
            "active_decision_code": legacy["active_decision_code"],
            "active_decision_public_safe": True,
            "active_decision_raw_or_plaintext_values_included": False,
            "active_preview_status": legacy["active_preview_status"],
            "active_preview_candidate_role": legacy["active_preview_candidate_role"],
            "active_preview_q5_exclusion_confirmed": legacy["active_preview_q5_exclusion_confirmed"],
        },
        "completion_gate": {
            "ready": legacy["completion_gate_ready"],
            "mode": legacy["completion_gate_mode"],
            "reason": legacy["completion_gate_reason"],
            "pending_fields": legacy["completion_gate_pending_fields"],
            "q4_confirmation_claimed": False,
            "q5_baseline_claimed": False,
            "stage5_review_claimed": False,
        },
        "raw_data_boundary": {
            "local_raw_data_dir": str(RAW_DIR),
            "local_raw_data_dir_role": "user_finance_raw_business_data_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "codex_create_extra_files_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
            "extra_work_dir_requirement": "must_be_project_controlled_and_gitignored",
        },
        "raw_dir_read_required": False,
        "raw_dir_read_performed": False,
        "raw_dir_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_file_bytes_committed": False,
        "raw_filename_publication_allowed": False,
        "raw_file_hash_publication_allowed": False,
        "field_plaintext_publication_allowed": False,
        "sheet_name_publication_allowed": False,
        "zip_member_name_publication_allowed": False,
        "row_value_publication_allowed": False,
        "business_value_publication_allowed": False,
        "business_field_parsing_performed": False,
        "raw_value_matching_performed": False,
        "s05_p3_performed": False,
        "stage5_review_performed": False,
        "github_upload_performed": False,
        "github_upload_deferred_until_stage10_batch": True,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q2",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "field_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "raw_business_values_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s05_p2_field_candidate_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_p2_field_candidate_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s05_p2_field_candidate_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_a0_golden_fixture.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s05_p2_excel_owner_decision.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s05_p2_owner_decision_intake.py --decision KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s05_p2_owner_decision_templates.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s05_p2_completion_gate.py --decision KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_p1_a0_file_registration.py --require-private-diagnostic",
        ],
        "evidence_refs": [
            "KMFA/stage_artifacts/V013_S05_P2_FIELD_CANDIDATE_REPLAY/human/field_candidate_replay_report.md",
            "KMFA/stage_artifacts/V013_S05_P2_FIELD_CANDIDATE_REPLAY/human/test_results.md",
            "KMFA/stage_artifacts/V013_S05_P2_FIELD_CANDIDATE_REPLAY/machine/field_candidate_replay_manifest.json",
        ],
        "legacy_s05_p2_refs": [
            "KMFA/tools/a0_golden_fixture.py",
            "KMFA/tools/check_a0_golden_fixture.py",
            "KMFA/tools/check_s05_p2_excel_owner_decision.py",
            "KMFA/tools/check_s05_p2_owner_decision_intake.py",
            "KMFA/tools/check_s05_p2_owner_decision_templates.py",
            "KMFA/tools/preview_s05_p2_owner_decision_application.py",
            "KMFA/tools/check_s05_p2_completion_gate.py",
            "KMFA/metadata/baseline/a0_golden_fixture_manifest.json",
            "KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl",
            "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/test_results.md",
            "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/owner_decision_record.md",
            "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json",
        ],
        "non_scope": [
            "S05-P3 authority baseline lock",
            "Stage 5 review",
            "GitHub upload",
            "raw data inspection",
            "raw directory mutation",
            "raw filename or raw hash publication",
            "field/header plaintext from raw sources",
            "sheet or ZIP member name publication",
            "row value publication",
            "business value publication",
            "raw value matching",
            "lineage full check completion",
            "formal report release",
            "live connector",
            "business execution",
        ],
        "next_required_step": "S05-P3 authority baseline lock in a separate run. Do not perform Stage 5 review or GitHub upload in S05-P2; GitHub main upload remains deferred until Stage 1-10 are complete, whole review passes, and findings are fixed.",
    }


def write_report(manifest: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = manifest["field_candidate_summary"]
    owner = manifest["owner_decision_summary"]
    gate = manifest["completion_gate"]
    lines = [
        "# KMFA v0.1.3 S05-P2 Field Candidate Replay",
        "",
        "- status: `completed_validated_local_only_no_go_upload_deferred_owner_downgrade_replayed`",
        "- phase_scope: `v013_s05_p2_field_candidate_replay_only`",
        f"- a0_project_candidates: `{summary['a0_project_candidates']}`",
        f"- required_fields_per_candidate: `{summary['required_fields_per_candidate']}`",
        f"- fixture_candidate_count: `{summary['fixture_candidate_count']}`",
        f"- private_value_hash_recorded_count: `{summary['private_value_hash_recorded_count']}`",
        f"- private_value_pending_count: `{summary['private_value_pending_count']}`",
        f"- source_anchor_recorded_count: `{summary['source_anchor_recorded_count']}`",
        f"- source_anchor_pending_count: `{summary['source_anchor_pending_count']}`",
        f"- pending_source_candidate_count: `{summary['pending_source_candidate_count']}`",
        f"- q3_field_candidate_count: `{summary['q3_field_candidate_count']}`",
        f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
        f"- q5_calculation_baseline_allowed_count: `{summary['q5_calculation_baseline_allowed_count']}`",
        f"- owner_allowed_decision_count: `{owner['owner_allowed_decision_count']}`",
        f"- owner_template_count: `{owner['owner_template_count']}`",
        f"- active_decision_code: `{owner['active_decision_code']}`",
        f"- active_preview_status: `{owner['active_preview_status']}`",
        f"- completion_gate_ready: `{str(gate['ready']).lower()}`",
        f"- completion_gate_mode: `{gate['mode']}`",
        "- raw_dir_read_required: `false`",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- raw_filename_publication_allowed: `false`",
        "- field_plaintext_publication_allowed: `false`",
        "- sheet_name_publication_allowed: `false`",
        "- zip_member_name_publication_allowed: `false`",
        "- row_value_publication_allowed: `false`",
        "- business_value_publication_allowed: `false`",
        "- s05_p3_performed: `false`",
        "- stage5_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- current_data_quality_grade: `Q2`",
        "- current_report_grade: `D`",
        "- release_permission: `blocked`",
        "",
        "## Boundary Note",
        "",
        "This replay uses only existing public-safe S05-P2 metadata and owner/authorized decision records. It does not read the local raw inbox, does not publish raw or normalized business values, and does not promote Q4/Q5 authority baseline status.",
        "",
        "`/Users/linzezhang/Downloads/KMFA_MetaData` is the user finance raw business data inbox. Codex must not modify, delete, move, rename, overwrite, or write generated/extra files inside that directory. Private diagnostics or scratch outputs must use `KMFA/.codex_private_runtime/` or another project-controlled gitignored work directory.",
        "",
        "## Next",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results_if_missing() -> None:
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TEST_RESULTS_PATH.exists():
        return
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.3 S05-P2 Test Results",
                "",
                "- status: `pending_final_validation`",
                "",
                "Final validation results will be recorded before local commit.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    PUBLIC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results_if_missing()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["field_candidate_summary"]
    print(
        "PASS: KMFA v0.1.3 S05-P2 field candidate replay evidence generated "
        f"(fixture_candidates={summary['fixture_candidate_count']}, "
        f"hash_recorded={summary['private_value_hash_recorded_count']}, "
        f"pending={summary['private_value_pending_count']}, "
        f"owner_decision={manifest['owner_decision_summary']['active_decision_code']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
