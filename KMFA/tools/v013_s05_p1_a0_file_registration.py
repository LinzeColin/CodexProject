#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S05-P1 A0 file registration replay evidence.

This phase replays the existing S05-P1 A0 file registration capability and
performs a read-only local alignment check against the user raw inbox. Public
evidence records only aggregate alignment status. Private raw hashes and member
diagnostics are written to the ignored private runtime directory.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.a0_file_register import (
    DEFAULT_OUTPUT_CANDIDATES,
    DEFAULT_OUTPUT_MANIFEST,
    validate_a0_registration,
)
from KMFA.tools.check_v013_s04_stage_review import validate_v013_s04_stage_review


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S05_P1_A0_FILE_REGISTRATION")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/a0_file_registration_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/a0_file_registration_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v013_s05_p1_a0_file_registration")
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_raw_zip_alignment_diagnostic.json"

RAW_DIR = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
PRIVATE_RAW_ZIP_ENV = "KMFA_PRIVATE_A0_RAW_ZIP"
TASK_ID = "KMFA-V013-S05-P1-A0-FILE-REGISTRATION-20260702"
SCHEMA_VERSION = "kmfa.v013_s05_p1_a0_file_registration.v1"


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_package_from_a0_manifest(a0_manifest: dict[str, Any]) -> dict[str, Any]:
    package = a0_manifest.get("source_package")
    if not isinstance(package, dict):
        raise ValueError("A0 source package must be an object")
    package_hash = str(package.get("package_hash", ""))
    if not package_hash.startswith("sha256:"):
        raise ValueError("A0 source package hash must be sha256-prefixed")
    return package


def is_hidden_zip_member(member_name: str) -> bool:
    return Path(member_name).name.startswith(".") or "__MACOSX/" in member_name


def inspect_zip_public_shape(path: Path) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            public_shape = {
                "business_member_count": 0,
                "pdf_member_count": 0,
                "excel_member_count": 0,
                "hidden_member_count": 0,
            }
            for info in archive.infolist():
                if info.is_dir():
                    continue
                suffix = Path(info.filename).suffix.lower()
                if is_hidden_zip_member(info.filename):
                    public_shape["hidden_member_count"] += 1
                    continue
                public_shape["business_member_count"] += 1
                if suffix == ".pdf":
                    public_shape["pdf_member_count"] += 1
                if suffix in {".xlsx", ".xls", ".xlsm"}:
                    public_shape["excel_member_count"] += 1
            return public_shape
    except (OSError, zipfile.BadZipFile):
        return None


def resolve_private_raw_zip() -> tuple[Path | None, str, int]:
    env_value = os.environ.get(PRIVATE_RAW_ZIP_ENV, "").strip()
    if env_value:
        candidate = Path(env_value)
        if not candidate.is_absolute():
            candidate = RAW_DIR / candidate
        return candidate if candidate.exists() else None, "env_path_missing", 0

    matching_candidates: list[Path] = []
    try:
        raw_zip_candidates = sorted(RAW_DIR.glob("*.zip"))
    except OSError:
        return None, "raw_dir_unavailable", 0

    for candidate in raw_zip_candidates:
        public_shape = inspect_zip_public_shape(candidate)
        if not public_shape:
            continue
        if (
            public_shape["business_member_count"] == 9
            and public_shape["pdf_member_count"] == 8
            and public_shape["excel_member_count"] == 1
        ):
            matching_candidates.append(candidate)

    if len(matching_candidates) == 1:
        return matching_candidates[0], "public_shape_unique_match", len(matching_candidates)
    if matching_candidates:
        return None, "public_shape_ambiguous_multiple_matches", len(matching_candidates)
    return None, "public_shape_no_match", 0


def inspect_private_raw_zip(source_package: dict[str, Any]) -> dict[str, Any]:
    raw_zip, selector_status, matching_candidate_count = resolve_private_raw_zip()
    result: dict[str, Any] = {
        "raw_data_inbox_read_required": True,
        "raw_data_inbox_read_performed": True,
        "raw_data_inbox_mutation_performed": False,
        "private_raw_zip_selector": "public_shape_or_env_private_path",
        "private_raw_zip_selector_status": selector_status,
        "private_raw_zip_matching_candidate_count": matching_candidate_count,
        "local_raw_zip_present": raw_zip is not None and raw_zip.exists(),
        "local_raw_zip_openable": False,
        "local_raw_package_hash_matches_registered": False,
        "local_raw_package_size_matches_registered": False,
        "local_raw_business_member_count": 0,
        "local_raw_pdf_member_count": 0,
        "local_raw_excel_member_count": 0,
        "local_raw_hidden_member_count": 0,
        "member_sha256_public_backfill_performed": False,
        "member_sha256_public_backfill_blocked_reason": "local_raw_zip_missing",
        "private_diagnostic_written": False,
        "private_diagnostic_ref": str(PRIVATE_DIAGNOSTIC_PATH),
        "public_actual_raw_package_hash_committed": False,
        "public_actual_raw_member_hashes_committed": False,
        "public_raw_member_names_committed": False,
    }
    if raw_zip is None or not raw_zip.exists():
        write_private_diagnostic(
            {
                "raw_zip_present": False,
                "private_raw_zip_selector_status": selector_status,
                "private_raw_zip_matching_candidate_count": matching_candidate_count,
            }
        )
        result["private_diagnostic_written"] = True
        return result

    expected_hash = str(source_package["package_hash"]).replace("sha256:", "")
    expected_size = int(source_package["package_size_bytes"])
    actual_hash = sha256_file(raw_zip)
    actual_size = raw_zip.stat().st_size
    result["local_raw_package_hash_matches_registered"] = actual_hash == expected_hash
    result["local_raw_package_size_matches_registered"] = actual_size == expected_size

    member_private_records: list[dict[str, Any]] = []
    with zipfile.ZipFile(raw_zip) as archive:
        result["local_raw_zip_openable"] = True
        for info in archive.infolist():
            if info.is_dir():
                continue
            member_name = info.filename
            is_hidden = is_hidden_zip_member(member_name)
            suffix = Path(member_name).suffix.lower()
            if is_hidden:
                result["local_raw_hidden_member_count"] += 1
            else:
                result["local_raw_business_member_count"] += 1
                if suffix == ".pdf":
                    result["local_raw_pdf_member_count"] += 1
                if suffix in {".xlsx", ".xls", ".xlsm"}:
                    result["local_raw_excel_member_count"] += 1
            digest = hashlib.sha256()
            with archive.open(info) as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            member_private_records.append(
                {
                    "member_name_sha256": hashlib.sha256(member_name.encode("utf-8")).hexdigest(),
                    "member_suffix": suffix,
                    "member_size_bytes": info.file_size,
                    "member_sha256": digest.hexdigest(),
                    "hidden_or_macos_metadata": is_hidden,
                }
            )

    if result["local_raw_package_hash_matches_registered"] and result["local_raw_package_size_matches_registered"]:
        result["member_sha256_public_backfill_blocked_reason"] = "not_backfilled_in_v013_replay_without_explicit_owner_scope"
    else:
        result["member_sha256_public_backfill_blocked_reason"] = "local_raw_package_hash_or_size_mismatch"
    write_private_diagnostic(
        {
            "raw_zip_present": True,
            "private_raw_zip_selector_status": selector_status,
            "private_raw_zip_matching_candidate_count": matching_candidate_count,
            "actual_package_sha256": actual_hash,
            "actual_package_size_bytes": actual_size,
            "expected_package_sha256": expected_hash,
            "expected_package_size_bytes": expected_size,
            "package_hash_matches_registered": result["local_raw_package_hash_matches_registered"],
            "package_size_matches_registered": result["local_raw_package_size_matches_registered"],
            "member_records": member_private_records,
        }
    )
    result["private_diagnostic_written"] = True
    return result


def write_private_diagnostic(payload: dict[str, Any]) -> None:
    PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    enriched = {
        "schema_version": "kmfa.private.v013_s05_p1_raw_zip_alignment.v1",
        "classification": "private_raw_diagnostic_do_not_commit",
        "raw_data_inbox": str(RAW_DIR),
        "private_raw_zip_selector": "public_shape_or_env_private_path",
        "private_raw_zip_env": PRIVATE_RAW_ZIP_ENV,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        **payload,
    }
    PRIVATE_DIAGNOSTIC_PATH.write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_manifest() -> dict[str, Any]:
    stage4 = validate_v013_s04_stage_review()
    a0_manifest = read_json(DEFAULT_OUTPUT_MANIFEST)
    candidates = read_jsonl(DEFAULT_OUTPUT_CANDIDATES)
    validate_a0_registration(a0_manifest, candidates)
    source_package = source_package_from_a0_manifest(a0_manifest)
    raw_alignment = inspect_private_raw_zip(source_package)
    file_summary = a0_manifest["file_summary"]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S05",
        "stage_name": "v0.1.3 A0 authority project cost golden baseline",
        "phase_id": "S05-P1",
        "phase_name": "A0 file registration replay and raw alignment check",
        "phase_scope": "v013_s05_p1_a0_file_registration_replay_only",
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_private_source_mismatch",
        "completed_task_ids": ["S5PAT01", "S5PAT02", "S5PAT03"],
        "stage4_review_dependency_validated": (
            stage4.get("stage_id") == "S04"
            and stage4.get("stage_review_performed") is True
            and stage4.get("github_upload_performed") is False
            and stage4.get("github_upload_deferred_until_stage10_batch") is True
        ),
        "stage4_review_dependency_ref": "KMFA/stage_artifacts/V013_S04_STAGE_REVIEW/machine/stage4_review_manifest.json",
        "legacy_s05_p1_dependency_validated": True,
        "legacy_s05_p1_refs": [
            "KMFA/tools/a0_file_register.py",
            "KMFA/tools/check_a0_file_registration.py",
            "KMFA/tests/test_a0_file_register.py",
            "KMFA/metadata/baseline/a0_file_manifest.json",
            "KMFA/metadata/baseline/a0_project_candidates.jsonl",
            "KMFA/stage_artifacts/S05_P1_a0_file_registration/human/s05_p1_completion_record.md",
            "KMFA/stage_artifacts/S05_P1_a0_file_registration/human/test_results.md",
        ],
        "a0_file_summary": {
            "total_files": file_summary["total_files"],
            "pdf_files": file_summary["pdf_files"],
            "excel_files": file_summary["excel_files"],
            "legacy_fingerprint_recorded_count": file_summary["legacy_fingerprint_recorded_count"],
            "member_sha256_recorded_count": file_summary["member_sha256_recorded_count"],
            "member_sha256_pending_count": file_summary["member_sha256_pending_count"],
        },
        "a0_candidate_summary": {
            "candidate_count": len(candidates),
            "q3_machine_candidate_count": sum(
                1 for item in candidates if item.get("machine_candidate_quality_grade") == "Q3"
            ),
            "q4_human_locked_count": sum(1 for item in candidates if item.get("q4_human_locked") is True),
            "q5_formal_report_allowed_count": sum(
                1 for item in candidates if item.get("q5_formal_report_allowed") is True
            ),
        },
        "registered_source_package": {
            "package_name_committed": False,
            "package_ref": "registered_a0_source_package_private_name_redacted",
            "registered_hash_present": True,
            "registered_size_bytes": source_package["package_size_bytes"],
            "public_actual_raw_package_hash_committed": False,
            "public_actual_raw_member_hashes_committed": False,
            "public_raw_member_names_committed": False,
        },
        "raw_alignment": raw_alignment,
        "raw_data_boundary": {
            "local_raw_data_dir": str(RAW_DIR),
            "local_raw_data_dir_role": "user_finance_raw_business_data_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": True,
            "codex_read_performed_by_this_phase": True,
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
        "raw_dir_mutation_performed": False,
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
        "s05_p2_performed": False,
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
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s05_p1_a0_file_registration.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_p1_a0_file_registration.py --require-private-diagnostic",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s05_p1_a0_file_registration -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_a0_file_registration.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_stage_review.py",
        ],
        "evidence_refs": [
            "KMFA/stage_artifacts/V013_S05_P1_A0_FILE_REGISTRATION/human/a0_file_registration_replay_report.md",
            "KMFA/stage_artifacts/V013_S05_P1_A0_FILE_REGISTRATION/human/test_results.md",
            "KMFA/stage_artifacts/V013_S05_P1_A0_FILE_REGISTRATION/machine/a0_file_registration_replay_manifest.json",
        ],
        "private_diagnostic_ref": str(PRIVATE_DIAGNOSTIC_PATH),
        "non_scope": [
            "S05-P2 field-level golden baseline",
            "Stage 5 review",
            "GitHub upload",
            "raw directory mutation",
            "raw filename publication",
            "raw file hash publication",
            "field or header plaintext publication",
            "sheet or ZIP member name publication",
            "row value publication",
            "business value publication",
            "raw value matching",
            "lineage full check completion",
            "formal report release",
            "live connector",
            "business execution",
        ],
        "next_required_step": (
            "Proceed to v0.1.3 S05-P2 as a separate run only after S05-P1 local commit. "
            "GitHub main upload remains deferred until v0.1.3 Stages 1-10 are complete, "
            "the whole Stage 1-10 review passes, and review findings are fixed."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = manifest["a0_file_summary"]
    candidates = manifest["a0_candidate_summary"]
    alignment = manifest["raw_alignment"]
    lines = [
        "# KMFA v0.1.3 S05-P1 A0 File Registration Replay",
        "",
        "## Result",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- stage4_review_dependency_validated: `{str(manifest['stage4_review_dependency_validated']).lower()}`",
        f"- legacy_s05_p1_dependency_validated: `{str(manifest['legacy_s05_p1_dependency_validated']).lower()}`",
        f"- files: `{summary['total_files']}` total, `{summary['pdf_files']}` PDF, `{summary['excel_files']}` Excel",
        f"- candidates: `{candidates['candidate_count']}` Q3 machine candidates",
        f"- q4_human_locked_count: `{candidates['q4_human_locked_count']}`",
        f"- q5_formal_report_allowed_count: `{candidates['q5_formal_report_allowed_count']}`",
        f"- raw_zip_present: `{str(alignment['local_raw_zip_present']).lower()}`",
        f"- raw_zip_openable: `{str(alignment['local_raw_zip_openable']).lower()}`",
        f"- local_raw_package_hash_matches_registered: `{str(alignment['local_raw_package_hash_matches_registered']).lower()}`",
        f"- local_raw_package_size_matches_registered: `{str(alignment['local_raw_package_size_matches_registered']).lower()}`",
        f"- local_raw_business_member_count: `{alignment['local_raw_business_member_count']}`",
        f"- local_raw_pdf_member_count: `{alignment['local_raw_pdf_member_count']}`",
        f"- local_raw_excel_member_count: `{alignment['local_raw_excel_member_count']}`",
        f"- member_sha256_public_backfill_performed: `{str(alignment['member_sha256_public_backfill_performed']).lower()}`",
        f"- member_sha256_public_backfill_blocked_reason: `{alignment['member_sha256_public_backfill_blocked_reason']}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        f"- github_upload_deferred_until_stage10_batch: `{str(manifest['github_upload_deferred_until_stage10_batch']).lower()}`",
        f"- formal_report_allowed: `{str(manifest['formal_report_allowed']).lower()}`",
        "",
        "## Public Safety",
        "",
        "- Public evidence does not contain raw ZIP bytes, PDF bytes, Excel bytes, raw member names, raw member hashes, sheet names, field/header plaintext, row values, or business values.",
        "- Private raw package/member diagnostics were written only to the git-ignored private runtime directory.",
        "- The raw inbox was read only for this phase and was not modified, deleted, moved, renamed, overwritten, or used for generated files.",
        "",
        "## Stop Line",
        "",
        "S05-P1 does not extract contract amount, expense total, margin, margin rate, or cost category fields. It does not perform S05-P2, Stage 5 review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, or business execution.",
        "",
        "## Next",
        "",
        manifest["next_required_step"],
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_test_results(manifest: dict[str, Any]) -> None:
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.3 S05-P1 Test Results",
                "",
                "| Command | Expected Result |",
                "|---|---|",
                "| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s05_p1_a0_file_registration.py` | PASS: evidence generated |",
                "| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_p1_a0_file_registration.py --require-private-diagnostic` | PASS: public manifest and private diagnostic boundary validated |",
                "| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s05_p1_a0_file_registration -q` | PASS: focused unit test |",
                "| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_a0_file_registration.py` | PASS: legacy A0 registration remains valid |",
                "",
                "## Evidence Snapshot",
                "",
                f"- status: `{manifest['status']}`",
                f"- raw_zip_present: `{str(manifest['raw_alignment']['local_raw_zip_present']).lower()}`",
                f"- raw_zip_openable: `{str(manifest['raw_alignment']['local_raw_zip_openable']).lower()}`",
                f"- local_raw_package_hash_matches_registered: `{str(manifest['raw_alignment']['local_raw_package_hash_matches_registered']).lower()}`",
                f"- local_raw_package_size_matches_registered: `{str(manifest['raw_alignment']['local_raw_package_size_matches_registered']).lower()}`",
                f"- member_sha256_public_backfill_blocked_reason: `{manifest['raw_alignment']['member_sha256_public_backfill_blocked_reason']}`",
                f"- private_diagnostic_written: `{str(manifest['raw_alignment']['private_diagnostic_written']).lower()}`",
                "- No GitHub upload, S05-P2, Stage 5 review, raw value matching, formal report, or business execution was performed.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    PUBLIC_OUTPUT_DIR.joinpath("machine").mkdir(parents=True, exist_ok=True)
    PUBLIC_OUTPUT_DIR.joinpath("human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results(manifest)
    print(
        "PASS: KMFA v0.1.3 S05-P1 A0 file registration replay generated "
        f"(files={manifest['a0_file_summary']['total_files']}, "
        f"candidates={manifest['a0_candidate_summary']['candidate_count']}, "
        f"raw_zip_openable={str(manifest['raw_alignment']['local_raw_zip_openable']).lower()}, "
        f"package_hash_match={str(manifest['raw_alignment']['local_raw_package_hash_matches_registered']).lower()}, "
        f"github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
