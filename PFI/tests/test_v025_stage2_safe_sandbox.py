from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import pfi_v02.stage_v025_safe_sandbox as sandbox_module
from pfi_v02.stage_v025_safe_sandbox import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_IDS,
    build_no_fake_audit,
    build_phase23_contract,
    build_phase23_privacy_scan_report,
    isolate_operational_sqlite,
    resolve_git_object_snapshot,
    run_git_object_read_parse_baseline,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
MODULE_PATH = PFI_ROOT / "src" / "pfi_v02" / "stage_v025_safe_sandbox.py"
SCRIPT_PATH = PFI_ROOT / "scripts" / "v025" / "run_stage2_phase23_baseline.py"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_2" / "phase_2_3"
SANDBOX_SCHEMA_PATH = PFI_ROOT / "config" / "schemas" / "v025" / "safe_sandbox_attestation.schema.json"
PERFORMANCE_SCHEMA_PATH = PFI_ROOT / "config" / "schemas" / "v025" / "performance_baseline.schema.json"
SOURCE_LOCK_PATH = PFI_ROOT / "config" / "sources" / "v025_immutable_real_source_lock.json"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_phase_contract_is_exactly_phase_23() -> None:
    contract = build_phase23_contract()
    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 2
    assert contract["phase_id"] == PHASE_ID == "V025-S2-P2.3"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S2-P3-T1",
        "S2-P3-T2",
        "S2-P3-T3",
        "S2-P3-T4",
    ]
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-S2-P23-SAFE-SANDBOX"
    assert contract["current_phase_only"] is True
    assert contract["real_data_read_only"] is True
    assert contract["financial_fixture_fallback_allowed"] is False
    assert contract["finder_used"] is False
    assert "Stage 2 whole-stage review" in contract["explicitly_not_done"]
    assert "Stage 3" in contract["explicitly_not_done"]


def test_git_object_snapshot_is_immutable_redacted_and_commit_bound() -> None:
    snapshot = resolve_git_object_snapshot(REPO_ROOT)
    source_commit = str(_json(SOURCE_LOCK_PATH)["source_commit"])
    assert snapshot["status"] == "ready"
    assert snapshot["source_id"] == "SRC-TRANSACTIONS-ALIPAY"
    assert snapshot["isolation_mode"] == "immutable_git_object_snapshot"
    assert snapshot["resolved_commit"] == source_commit
    assert snapshot["path_alias"] == "MetaDatabase/PFI"
    assert snapshot["snapshot_immutable"] is True
    assert snapshot["source_write_capability"] is False
    assert snapshot["source_mutation_performed"] is False
    assert snapshot["private_values_included"] is False
    assert snapshot["raw_rows_emitted"] == 0
    for field in ("tree_oid", "manifest_blob_oid", "transactions_blob_oid"):
        assert len(str(snapshot[field])) == 40
    assert int(snapshot["input_bytes"]) > 2_000_000


def test_real_scale_baseline_reads_all_rows_without_emitting_financial_values() -> None:
    baseline = run_git_object_read_parse_baseline(REPO_ROOT, iterations=2)
    assert baseline["status"] == "pass"
    assert baseline["real_input_status"] == "ready"
    assert baseline["record_count"] == 8815
    assert baseline["manifest_record_count"] == 8815
    assert baseline["record_count_matches_manifest"] is True
    assert baseline["iterations"] == 2
    assert baseline["elapsed_ms"]["min"] > 0
    assert baseline["elapsed_ms"]["max"] >= baseline["elapsed_ms"]["min"]
    assert baseline["peak_python_alloc_bytes"]["max"] > 0
    assert baseline["source_identity_before"] == baseline["source_identity_after"]
    assert baseline["source_mutation_performed"] is False
    assert baseline["financial_fixture_fallback_used"] is False
    assert baseline["financial_values_emitted"] == 0


def test_missing_real_source_is_blocked_without_fallback() -> None:
    baseline = run_git_object_read_parse_baseline(REPO_ROOT, git_ref="refs/heads/definitely-missing", iterations=1)
    assert baseline["status"] == "blocked"
    assert baseline["real_input_status"] == "source_missing"
    assert baseline["record_count"] is None
    assert baseline["elapsed_ms"] is None
    assert baseline["peak_python_alloc_bytes"] is None
    assert baseline["financial_fixture_fallback_used"] is False
    assert baseline["source_mutation_performed"] is False


def test_sqlite_isolated_copy_is_private_read_only_and_cleaned(tmp_path: Path) -> None:
    data_home = tmp_path / "source-home"
    database = data_home / "private" / "operational" / "pfi.sqlite"
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, text_data TEXT)")
    connection.commit()
    connection.close()
    source_before = database.stat()
    temp_root = tmp_path / "ephemeral-root"
    temp_root.mkdir(mode=0o700)

    report = isolate_operational_sqlite(REPO_ROOT, data_home=data_home, temp_root=temp_root)

    source_after = database.stat()
    assert report["status"] == "pass"
    assert report["isolation_mode"] == "ephemeral_0600_file_copy"
    assert report["source_path_redacted"] is True
    assert report["source_before_after_unchanged"] is True
    assert report["source_hash"] == report["copy_hash"]
    assert report["copy_mode"] == "0600"
    assert report["temp_directory_mode"] == "0700"
    assert report["sqlite_quick_check"] == "ok"
    assert report["cleanup_complete"] is True
    assert report["row_values_emitted"] == 0
    assert report["table_names_emitted"] == 0
    assert report["source_mutation_performed"] is False
    assert list(temp_root.iterdir()) == []
    assert (source_before.st_ino, source_before.st_size, source_before.st_mtime_ns, source_before.st_ctime_ns) == (
        source_after.st_ino,
        source_after.st_size,
        source_after.st_mtime_ns,
        source_after.st_ctime_ns,
    )


def test_sqlite_copy_fails_closed_for_missing_or_sidecar_source(tmp_path: Path) -> None:
    missing = isolate_operational_sqlite(REPO_ROOT, data_home=tmp_path / "missing")
    assert missing["status"] == "source_missing"
    assert missing["cleanup_complete"] is True
    assert missing["source_mutation_performed"] is False

    data_home = tmp_path / "sidecar-home"
    database = data_home / "private" / "operational" / "pfi.sqlite"
    database.parent.mkdir(parents=True)
    sqlite3.connect(database).close()
    database.with_name(database.name + "-wal").write_bytes(b"blocked")
    sidecar = isolate_operational_sqlite(REPO_ROOT, data_home=data_home)
    assert sidecar["status"] == "blocked_sidecar_present"
    assert sidecar["cleanup_complete"] is True
    assert sidecar["copy_hash"] is None


def test_no_fake_audit_is_structural_and_fail_closed() -> None:
    audit = build_no_fake_audit(MODULE_PATH)
    assert audit["status"] == "pass"
    assert audit["baseline_accepts_external_financial_records"] is False
    assert audit["source_missing_behavior"] == "blocked_without_fallback"
    assert audit["financial_fixture_fallback_used"] is False
    assert audit["network_capability_present"] is False
    assert audit["finder_used"] is False
    assert audit["source_mutation_capability_present"] is False


def test_cli_emits_redacted_real_baseline_without_creating_repo_files() -> None:
    before = subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout
    completed = subprocess.run(
        [
            str(PFI_ROOT / ".venv" / "bin" / "python"),
            "-B",
            str(SCRIPT_PATH),
            "--repo-root",
            str(REPO_ROOT),
            "--git-ref",
            str(_json(SOURCE_LOCK_PATH)["source_commit"]),
            "--iterations",
            "1",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(PFI_ROOT / "src")},
    )
    payload = json.loads(completed.stdout)
    after = subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout
    assert payload["performance_baseline"]["record_count"] == 8815
    assert payload["database_before_after"]["source_path_redacted"] is True
    assert payload["private_values_included"] is False
    assert payload["finder_used"] is False
    assert before == after


def test_taskpack_evidence_schema_accepts_phase_evidence() -> None:
    taskpack = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    with zipfile.ZipFile(taskpack) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(_json(REPORT_ROOT / "evidence.json"))


def test_tracked_sandbox_and_performance_artifacts_validate() -> None:
    sandbox = _json(REPORT_ROOT / "sandbox_attestation.json")
    performance = _json(REPORT_ROOT / "performance_baseline.json")
    database = _json(REPORT_ROOT / "database_before_after.json")
    sandbox_schema = _json(SANDBOX_SCHEMA_PATH)
    performance_schema = _json(PERFORMANCE_SCHEMA_PATH)
    Draft202012Validator.check_schema(sandbox_schema)
    Draft202012Validator.check_schema(performance_schema)
    Draft202012Validator(sandbox_schema).validate(sandbox)
    Draft202012Validator(performance_schema).validate(performance)
    assert sandbox["status"] == "pass"
    assert sandbox["git_object_snapshot"]["snapshot_immutable"] is True
    assert sandbox["database_before_after_ref"] == "PFI/reports/pfi_v025/stage_2/phase_2_3/database_before_after.json"
    assert database["status"] == "pass"
    assert database["cleanup_complete"] is True
    assert database["source_before_after_unchanged"] is True
    assert performance["record_count"] == 8815
    assert performance["financial_values_emitted"] == 0
    assert performance["source_identity_before"] == performance["source_identity_after"]


def test_tracked_no_fake_and_privacy_audits_are_deterministic() -> None:
    no_fake = _json(REPORT_ROOT / "no_fake_audit.json")
    assert no_fake == build_no_fake_audit(MODULE_PATH)
    assert no_fake["status"] == "pass"
    tracked = (REPORT_ROOT / "privacy_scan.txt").read_text(encoding="utf-8")
    observed_at = next(
        line.removeprefix("observed_at=") for line in tracked.splitlines() if line.startswith("observed_at=")
    )
    assert build_phase23_privacy_scan_report(REPO_ROOT, observed_at) == tracked
    assert tracked.splitlines()[0] == "PASS"
    assert "input_count=10" in tracked
    for counter in (
        "absolute_private_paths",
        "raw_filenames",
        "financial_row_values",
        "account_identifiers",
        "credentials",
        "sqlite_table_names",
        "finder_operations",
        "source_mutations",
        "financial_fixture_fallback",
    ):
        assert f"{counter}=0" in tracked


def test_stage2_evidence_index_stops_before_whole_review_and_stage3() -> None:
    index = _json(REPORT_ROOT / "stage_2_evidence_index.json")
    assert index["status"] == "ready_for_whole_stage_review"
    assert index["phase_status"] == {
        "2.1": "candidate_pass",
        "2.2": "candidate_pass",
        "2.3": "candidate_pass",
    }
    assert index["technical_acceptance_criteria_passed"] == 6
    assert index["technical_acceptance_criteria_total"] == 6
    assert index["stage_2_whole_stage_review_status"] == "not_started"
    assert index["user_acceptance_status"] == "pending_whole_stage_review"
    assert index["stage_3_entry_authorized"] is False
    assert index["production_accepted"] is False
    assert index["final_human_acceptance"] is False


def test_phase23_tracked_scope_contains_no_private_values_or_untracked_deliverables() -> None:
    expected = {
        "PFI/docs/pfi_v025/stage_2/sandbox_spec.md",
        "PFI/reports/pfi_v025/stage_2/phase_2_3/database_before_after.json",
        "PFI/reports/pfi_v025/stage_2/phase_2_3/evidence.json",
        "PFI/reports/pfi_v025/stage_2/phase_2_3/no_fake_audit.json",
        "PFI/reports/pfi_v025/stage_2/phase_2_3/performance_baseline.json",
        "PFI/reports/pfi_v025/stage_2/phase_2_3/privacy_scan.txt",
        "PFI/reports/pfi_v025/stage_2/phase_2_3/sandbox_attestation.json",
        "PFI/reports/pfi_v025/stage_2/phase_2_3/stage_2_evidence_index.json",
    }
    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
        ).stdout.splitlines()
    )
    assert expected <= tracked
    for path in expected:
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        assert "/Users/" not in text
        assert "file:///" not in text


def test_artifact_hashes_are_sha256_bound() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    for relative, expected in evidence["artifact_hashes"].items():
        observed = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
        assert observed == expected
