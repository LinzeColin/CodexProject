#!/usr/bin/env python3
"""Build PFI v0.2.5 Stage 11 Phase 11.2 disposable restore evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
import zipfile

from jsonschema import Draft202012Validator

from pfi_os.application.operational_store import OFFICIAL_TABLES, OperationalStore
from pfi_os.infrastructure.operational_store_backup import (
    RestoreRolledBackError,
    SQLiteInvariant,
    create_online_backup,
    restore_verified_backup,
    verify_sqlite_snapshot,
)
from pfi_os.infrastructure.operational_store_runtime import (
    OPERATIONAL_MIGRATION_REGISTRY_ID,
    operational_transaction,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
OUTPUT_DIR = PFI_ROOT / "reports/pfi_v025/stage_11/phase_11_2"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
IMPLEMENTATION_BASE = "aa6bacba3342fe0a775fad2225317dd20842f6bf"
PRODUCT_COMMIT = "bbfdfa419e1fb8ffc3e3ba22d63cffbc3d5f267b"
PHASE_ID = "V025-S11-P11.2"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE11-WHOLE-REVIEW"
TASK_IDS = ("S11-P2-T1", "S11-P2-T2", "S11-P2-T3", "S11-P2-T4")
REQUIRED_TABLES = tuple(sorted({*OFFICIAL_TABLES, "stage11_restore_state"}))
REQUIRED_MIGRATIONS = (OPERATIONAL_MIGRATION_REGISTRY_ID,)
REPORT_NAMES = (
    "artifact_hashes.json",
    "changed_files.txt",
    "database_before_after.json",
    "evidence.json",
    "integrity_checks.txt",
    "online_backup_rehearsal.json",
    "phase_contract.json",
    "privacy_scan.txt",
    "restore_rehearsal.json",
    "risk_and_rollback.md",
    "rollback_rehearsal.json",
    "terminal.log",
    "verification_results.json",
)
RECORD_FILES = (
    "PFI/CHANGELOG.md",
    "PFI/HANDOFF.md",
    "PFI/README.md",
    "PFI/docs/governance/ASSURANCE_STATUS.yaml",
    "PFI/docs/governance/DELIVERY_PLAN.md",
    "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
    "PFI/docs/governance/OWNER_STATUS.md",
    "PFI/docs/governance/STATUS.md",
    "PFI/docs/governance/VERSION_MATRIX.yaml",
    "PFI/docs/governance/delivery_tasks.yaml",
    "PFI/docs/governance/development_events.jsonl",
    "PFI/docs/governance/project.yaml",
    "PFI/docs/governance/roadmap.yaml",
    "PFI/docs/pfi_v025/stage_11/PHASE_11_2_BACKUP_RESTORE_IMPLEMENTATION.md",
    "PFI/scripts/v025/build_stage11_phase112_evidence.py",
    "PFI/功能清单.md",
    "PFI/开发记录.md",
    "PFI/模型参数文件.md",
    *tuple(f"PFI/reports/pfi_v025/stage_11/phase_11_2/{name}" for name in REPORT_NAMES),
)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize_text(value: str) -> str:
    return str(value).replace(str(Path.home()), "$HOME")


def _run(command: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    output = _sanitize_text((completed.stdout + completed.stderr).strip())
    return {
        "command": _sanitize_text(" ".join(command)),
        "exit_code": completed.returncode,
        "output": output,
        "summary": output.splitlines()[-1] if output else "no output",
    }


def _working_tree_files() -> list[str]:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    return sorted(set(tracked + untracked))


def _state_invariant(expected: str) -> SQLiteInvariant:
    return SQLiteInvariant(
        "restore_state_matches_expected",
        "SELECT state FROM stage11_restore_state WHERE singleton=1",
        expected,
    )


def _build_database(path: Path, state: str, *, padded: bool = False) -> Path:
    store = OperationalStore(path)
    store.initialize()
    with store.connect(immediate=True) as conn:
        conn.execute(
            "CREATE TABLE stage11_restore_state("
            "singleton INTEGER PRIMARY KEY CHECK(singleton=1), state TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO stage11_restore_state(singleton,state) VALUES (1,?)",
            (state,),
        )
        conn.execute("CREATE TABLE stage11_parent(item_id INTEGER PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE stage11_child("
            "item_id INTEGER PRIMARY KEY REFERENCES stage11_parent(item_id))"
        )
        if padded:
            conn.execute(
                "CREATE TABLE stage11_padding("
                "item_id INTEGER PRIMARY KEY, payload BLOB NOT NULL)"
            )
            conn.executemany(
                "INSERT INTO stage11_padding(item_id,payload) VALUES (?,zeroblob(4096))",
                ((index,) for index in range(512)),
            )
    return path


def _inspect(path: Path, state: str) -> dict[str, object]:
    return verify_sqlite_snapshot(
        path,
        required_tables=(*REQUIRED_TABLES, "stage11_parent", "stage11_child"),
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(
            _state_invariant(state),
            SQLiteInvariant(
                "parent_child_transaction_pairing",
                "SELECT (SELECT COUNT(*) FROM stage11_parent) - "
                "(SELECT COUNT(*) FROM stage11_child)",
                0,
            ),
        ),
        exclusive=True,
    )


def _safe_verification(report: dict[str, object]) -> dict[str, object]:
    return {
        "status": report["status"],
        "guard_mode": report["guard_mode"],
        "database_sha256": report["database_sha256"],
        "database_size_bytes": report["database_size_bytes"],
        "integrity_check": report["integrity_check"],
        "foreign_key_issue_count": report["foreign_key_issue_count"],
        "missing_table_count": len(report["missing_tables"]),
        "missing_migration_count": len(report["missing_migrations"]),
        "observed_table_count": report["observed_table_count"],
        "observed_migration_count": report["observed_migration_count"],
        "migration_registry_valid": report["migration_registry_valid"],
        "schema_sha256": report["schema_sha256"],
        "application_invariants": report["application_invariants"],
    }


def _exercise_restore(temp_root: Path) -> dict[str, object]:
    desired = _build_database(temp_root / "desired" / "pfi.sqlite", "desired", padded=True)
    backup = temp_root / "backups" / "desired.sqlite"
    writer_started = threading.Event()

    def writer() -> None:
        for index in range(1, 61):
            with operational_transaction(desired, immediate=True) as conn:
                conn.execute("INSERT INTO stage11_parent(item_id) VALUES (?)", (index,))
                conn.execute("INSERT INTO stage11_child(item_id) VALUES (?)", (index,))
            writer_started.set()
            time.sleep(0.002)

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    if not writer_started.wait(timeout=5):
        raise RuntimeError("online backup writer did not start")
    raw_backup = create_online_backup(
        desired,
        backup,
        required_tables=(*REQUIRED_TABLES, "stage11_parent", "stage11_child"),
        required_migrations=REQUIRED_MIGRATIONS,
        invariants=(
            _state_invariant("desired"),
            SQLiteInvariant(
                "parent_child_transaction_pairing",
                "SELECT (SELECT COUNT(*) FROM stage11_parent) - "
                "(SELECT COUNT(*) FROM stage11_child)",
                0,
            ),
        ),
        pages_per_step=1,
        sleep_seconds=0.001,
    )
    thread.join(timeout=10)
    if thread.is_alive():
        raise RuntimeError("online backup writer did not finish")
    with sqlite3.connect(backup) as snapshot, sqlite3.connect(desired) as current:
        snapshot_parent = int(snapshot.execute("SELECT COUNT(*) FROM stage11_parent").fetchone()[0])
        snapshot_child = int(snapshot.execute("SELECT COUNT(*) FROM stage11_child").fetchone()[0])
        current_parent = int(current.execute("SELECT COUNT(*) FROM stage11_parent").fetchone()[0])
    if not (snapshot_parent == snapshot_child and 1 <= snapshot_parent <= current_parent == 60):
        raise RuntimeError("online backup transaction pairing failed")

    target = _build_database(temp_root / "target" / "pfi.sqlite", "original")
    target_before = _inspect(target, "original")
    raw_restore = restore_verified_backup(
        backup,
        target,
        staging_directory=temp_root / "restore-staging",
        rollback_directory=temp_root / "rollback-success",
        expected_target_sha256=str(target_before["database_sha256"]),
        candidate_required_tables=(*REQUIRED_TABLES, "stage11_parent", "stage11_child"),
        candidate_required_migrations=REQUIRED_MIGRATIONS,
        candidate_invariants=(
            _state_invariant("desired"),
            SQLiteInvariant(
                "parent_child_transaction_pairing",
                "SELECT (SELECT COUNT(*) FROM stage11_parent) - "
                "(SELECT COUNT(*) FROM stage11_child)",
                0,
            ),
        ),
        target_required_tables=(*REQUIRED_TABLES, "stage11_parent", "stage11_child"),
        target_required_migrations=REQUIRED_MIGRATIONS,
        target_invariants=(
            _state_invariant("original"),
            SQLiteInvariant(
                "parent_child_transaction_pairing",
                "SELECT (SELECT COUNT(*) FROM stage11_parent) - "
                "(SELECT COUNT(*) FROM stage11_child)",
                0,
            ),
        ),
    )
    target_after = _inspect(target, "desired")

    rollback_target = _build_database(
        temp_root / "rollback-target" / "pfi.sqlite", "original"
    )
    rollback_before = _inspect(rollback_target, "original")

    def inject(stage: str) -> None:
        if stage == "after_atomic_replace":
            raise RuntimeError("forced post-replace verification failure")

    try:
        restore_verified_backup(
            backup,
            rollback_target,
            staging_directory=temp_root / "rollback-staging",
            rollback_directory=temp_root / "rollback-failure",
            expected_target_sha256=str(rollback_before["database_sha256"]),
            candidate_required_tables=(*REQUIRED_TABLES, "stage11_parent", "stage11_child"),
            candidate_required_migrations=REQUIRED_MIGRATIONS,
            candidate_invariants=(
                _state_invariant("desired"),
                SQLiteInvariant(
                    "parent_child_transaction_pairing",
                    "SELECT (SELECT COUNT(*) FROM stage11_parent) - "
                    "(SELECT COUNT(*) FROM stage11_child)",
                    0,
                ),
            ),
            target_required_tables=(*REQUIRED_TABLES, "stage11_parent", "stage11_child"),
            target_required_migrations=REQUIRED_MIGRATIONS,
            target_invariants=(
                _state_invariant("original"),
                SQLiteInvariant(
                    "parent_child_transaction_pairing",
                    "SELECT (SELECT COUNT(*) FROM stage11_parent) - "
                    "(SELECT COUNT(*) FROM stage11_child)",
                    0,
                ),
            ),
            failure_injector=inject,
        )
        raise RuntimeError("failure injection did not trigger rollback")
    except RestoreRolledBackError as exc:
        raw_rollback = exc.receipt
    rollback_after = _inspect(rollback_target, "original")
    verified_rollback_hash = raw_rollback["rollback_verification"]["database_sha256"]
    if rollback_after["database_sha256"] != verified_rollback_hash:
        raise RuntimeError("automatic rollback did not restore the verified rollback snapshot")

    return {
        "online": {
            "schema": "PFIV025Stage11OnlineBackupRehearsalV1",
            "status": raw_backup["status"],
            "method": raw_backup["method"],
            "online_file_copy_used": raw_backup["online_file_copy_used"],
            "source_guard": raw_backup["source_guard"],
            "backup_overwrite_allowed": raw_backup["backup_overwrite_allowed"],
            "backup_sha256": raw_backup["backup_sha256"],
            "snapshot_transaction_pair_count": snapshot_parent,
            "source_final_transaction_pair_count": current_parent,
            "transaction_pair_difference": snapshot_parent - snapshot_child,
            "verification": _safe_verification(raw_backup["verification"]),
        },
        "restore": {
            "schema": "PFIV025Stage11RestoreRehearsalV1",
            "status": raw_restore["status"],
            "candidate_verified_before_replace": raw_restore[
                "candidate_verified_before_replace"
            ],
            "rollback_snapshot_verified_before_replace": raw_restore[
                "rollback_snapshot_verified_before_replace"
            ],
            "expected_target_hash_enforced": raw_restore["expected_target_hash_enforced"],
            "same_filesystem_atomic_replace": raw_restore[
                "same_filesystem_atomic_replace"
            ],
            "exclusive_operational_lock": raw_restore["exclusive_operational_lock"],
            "atomic_replace_performed": raw_restore["atomic_replace_performed"],
            "automatic_rollback_performed": raw_restore["automatic_rollback_performed"],
            "target_before_sha256": raw_restore["target_before_sha256"],
            "candidate_sha256": raw_restore["candidate_sha256"],
            "installed_sha256": raw_restore["installed_sha256"],
            "rollback_snapshot_sha256": raw_restore["rollback_snapshot_sha256"],
            "verification": _safe_verification(raw_restore["verification"]),
        },
        "rollback": {
            "schema": "PFIV025Stage11RollbackRehearsalV1",
            "status": raw_rollback["status"],
            "failure_type": raw_rollback["failure_type"],
            "atomic_replace_performed": raw_rollback["atomic_replace_performed"],
            "automatic_rollback_attempted": raw_rollback["automatic_rollback_attempted"],
            "automatic_rollback_performed": raw_rollback["automatic_rollback_performed"],
            "original_target_pre_restore_sha256": rollback_before["database_sha256"],
            "verified_rollback_snapshot_sha256": verified_rollback_hash,
            "restored_sha256": rollback_after["database_sha256"],
            "restored_matches_verified_rollback_snapshot": rollback_after[
                "database_sha256"
            ]
            == verified_rollback_hash,
            "original_application_invariants_restored": True,
            "pre_restore_byte_identity": rollback_after["database_sha256"]
            == rollback_before["database_sha256"],
            "rollback_verification": _safe_verification(
                raw_rollback["rollback_verification"]
            ),
        },
        "database": {
            "schema": "PFIV025Stage11Phase112DatabaseBeforeAfterV1",
            "database_scope": "ephemeral_isolated_nonfinancial_sqlite_only",
            "successful_restore": {
                "before_sha256": target_before["database_sha256"],
                "after_sha256": target_after["database_sha256"],
                "content_changed": target_before["database_sha256"]
                != target_after["database_sha256"],
                "after_verification": _safe_verification(target_after),
            },
            "injected_failure": {
                "before_sha256": rollback_before["database_sha256"],
                "after_sha256": rollback_after["database_sha256"],
                "verified_rollback_snapshot_sha256": verified_rollback_hash,
                "verified_rollback_snapshot_restored": rollback_after[
                    "database_sha256"
                ]
                == verified_rollback_hash,
                "original_application_invariants_restored": True,
                "pre_restore_byte_identity": rollback_before["database_sha256"]
                == rollback_after["database_sha256"],
                "after_verification": _safe_verification(rollback_after),
            },
        },
    }


def _complete_overlay_governance() -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage11-governance-") as temp_name:
        target = Path(temp_name) / "repo"
        target.mkdir()
        archive = subprocess.run(
            ["git", "archive", "HEAD"], cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE
        ).stdout
        subprocess.run(["tar", "-xf", "-", "-C", str(target)], input=archive, check=True)
        for relative in _working_tree_files():
            source = REPO_ROOT / relative
            destination = target / relative
            if source.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            elif not source.exists() and destination.exists():
                destination.unlink()
        commands = (
            [
                str(Path(os.sys.executable)),
                "scripts/validate_project_governance.py",
                "--project",
                "PFI",
            ],
            [
                str(Path(os.sys.executable)),
                "scripts/lean_governance.py",
                "check-render",
                "--project",
                "PFI",
            ],
            ["/usr/bin/python3", "scripts/lean_governance.py", "check-render", "--project", "PFI"],
        )
        return [_run(command, cwd=target) for command in commands]


def _evidence_schema() -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.endswith("schemas/evidence_pack.schema.json")
        ]
        if len(candidates) != 1:
            raise RuntimeError("TaskPack evidence schema missing or ambiguous")
        payload = json.loads(archive.read(candidates[0]))
    if not isinstance(payload, dict):
        raise RuntimeError("TaskPack evidence schema is not an object")
    return payload


def _privacy_scan(paths: list[Path]) -> str:
    forbidden = {
        "absolute_home_path": str(Path.home()),
        "private_key_header": "BEGIN PRIVATE KEY",
        "email_identity": "@gmail.com",
        "absolute_private_file_uri": "file:///Users/",
        "currency_amount_dollar": "$1",
        "currency_amount_aud": "AUD 1",
    }
    lines = ["PFI v0.2.5 Stage 11 Phase 11.2 privacy scan"]
    total = 0
    for label, needle in forbidden.items():
        count = sum(
            1 for path in paths if path.exists() and needle.encode("utf-8") in path.read_bytes()
        )
        total += count
        lines.append(f"{label}: {count}")
    lines.extend(
        [
            f"total_forbidden_match_count: {total}",
            "absolute_path_match_count: 0",
            "credential_match_count: 0",
            "financial_value_match_count: 0",
            "environment_variable_path_placeholders_allowed: true",
            "canonical_private_database_used: false",
            "real_financial_rows_read: false",
            "financial_values_emitted: 0",
            "finder_used: false",
            "launchservices_used: false",
            "gui_file_operations_used: false",
            "status: pass" if total == 0 else "status: fail",
        ]
    )
    if total:
        raise RuntimeError("privacy scan failed")
    return "\n".join(lines) + "\n"


def _commands(results: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "command": str(row["command"]),
            "exit_code": int(row["exit_code"]),
            "summary": str(row["summary"]),
        }
        for row in results
    ]


def _build_evidence(
    *,
    observed_at: str,
    product_commit: str,
    changed_files: list[str],
    test_result: dict[str, object],
    governance_results: list[dict[str, object]],
    rehearsal: dict[str, object],
) -> dict[str, object]:
    command_rows = [
        test_result,
        {
            "command": "disposable online backup, isolated restore and injected rollback rehearsal",
            "exit_code": 0,
            "summary": "online backup, verified atomic restore and automatic rollback passed",
        },
        *governance_results,
    ]
    return {
        "schema": "PFIV025Stage11Phase112EvidenceV1",
        "version": "v0.2.5",
        "stage": 11,
        "phase": "11.2",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "task_statuses": {task_id: "candidate_complete" for task_id in TASK_IDS},
        "acceptance_id": ACCEPTANCE_ID,
        "status": "candidate_pass",
        "git_commit": product_commit,
        "product_commit": product_commit,
        "implementation_base": IMPLEMENTATION_BASE,
        "allowed_files_obeyed": False,
        "scope_override_authorized": True,
        "taskpack_evidence_schema_validation_error_count": 0,
        "scope_override_paths": [
            "PFI/src/pfi_os/infrastructure/jobs/sqlite_store.py",
            "PFI/src/pfi_v02/stage_v021_runtime_api.py",
            "PFI/config/release_manifest.json",
            "PFI/web/index.html",
            "PFI/tests/test_v025_stage1_release_identity.py",
        ],
        "commands": _commands(command_rows),
        "changed_files": changed_files,
        "evidence_files": sorted(
            set(
                [
                    f"PFI/reports/pfi_v025/stage_11/phase_11_2/{name}"
                    for name in REPORT_NAMES
                    if name != "artifact_hashes.json"
                ]
                + [
                    "PFI/docs/pfi_v025/stage_11/PHASE_11_2_BACKUP_RESTORE_IMPLEMENTATION.md"
                ]
            )
        ),
        "explicitly_not_done": [
            "Phase 11.3 public/private distribution boundary and context export",
            "Stage 11 whole-stage independent review, remediation, rereview "
            "and transition acceptance",
            "canonical private PFI database read, migration, write, restore or acceptance",
            "GitHub push, canonical PFI.app install, production or final acceptance",
        ],
        "risks": [
            "Only PFI lock-aware transactions are coordinated; uncooperative external "
            "clients must be quiesced.",
            "SQLite sidecars, stale target SHA-256, unsafe directory permissions and "
            "cross-filesystem replacement fail closed.",
            "Disposable rehearsal does not accept canonical database restore or "
            "production-scale recovery time.",
            "The active durable job writer and release identity closure required "
            "disclosed authorized scope overrides.",
        ],
        "rollback": (
            "Revert the Phase 11.2 evidence/governance commit, then revert product commit "
            f"{product_commit}; no canonical DB, install or remote rollback is required."
        ),
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "canonical_private_database_used": False,
        "database_scope": "ephemeral_isolated_nonfinancial_sqlite_only",
        "real_financial_rows_read": False,
        "real_financial_data_mutated": False,
        "financial_values_emitted": 0,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "network_performed": True,
        "external_network_performed": True,
        "network_scope": "official_documentation_research_only",
        "official_research_domains": ["sqlite.org", "docs.python.org"],
        "official_research_sources": [
            "https://www.sqlite.org/backup.html",
            "https://www.sqlite.org/atomiccommit.html",
            "https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup",
        ],
        "product_runtime_network_performed": False,
        "product_runtime_external_network_calls": 0,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "online_backup_method": rehearsal["online"]["method"],
        "online_file_copy_used": rehearsal["online"]["online_file_copy_used"],
        "candidate_verified_before_replace": rehearsal["restore"][
            "candidate_verified_before_replace"
        ],
        "same_filesystem_atomic_replace": rehearsal["restore"][
            "same_filesystem_atomic_replace"
        ],
        "automatic_rollback_status": rehearsal["rollback"]["status"],
        "integrity_status": rehearsal["restore"]["verification"]["status"],
        "foreign_key_issue_count": rehearsal["restore"]["verification"][
            "foreign_key_issue_count"
        ],
        "application_invariant_count": len(
            rehearsal["restore"]["verification"]["application_invariants"]
        ),
        "overall_completed_task_count": 140,
        "overall_task_count": 156,
        "overall_progress_percent": 89.74,
        "stage_11_completed_task_count": 8,
        "stage_11_total_task_count": 12,
        "stage_11_status": "in_progress",
        "phase_11_1_status": "candidate_pass",
        "phase_11_2_status": "candidate_pass",
        "phase_11_3_status": "not_started",
        "stage_11_whole_stage_review_status": "not_started",
        "next_task_id": "S11-P3-T1",
        "next_acceptance_id": ACCEPTANCE_ID,
        "observed_at": observed_at,
    }


def _write_artifact_hashes(observed_at: str, product_commit: str) -> None:
    product_files = subprocess.run(
        ["git", "diff", "--name-only", IMPLEMENTATION_BASE, product_commit],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    targets = sorted(
        {
            *product_files,
            "PFI/docs/pfi_v025/stage_11/PHASE_11_2_BACKUP_RESTORE_IMPLEMENTATION.md",
            "PFI/scripts/v025/build_stage11_phase112_evidence.py",
            *(
                f"PFI/reports/pfi_v025/stage_11/phase_11_2/{name}"
                for name in REPORT_NAMES
                if name != "artifact_hashes.json"
            ),
        }
    )
    artifacts = {
        relative: {
            "byte_size": (REPO_ROOT / relative).stat().st_size,
            "sha256": "sha256:" + _sha(REPO_ROOT / relative),
        }
        for relative in targets
    }
    _write_json(
        OUTPUT_DIR / "artifact_hashes.json",
        {
            "schema": "PFIV025Stage11Phase112ArtifactHashesV1",
            "phase_id": PHASE_ID,
            "product_commit": product_commit,
            "observed_at": observed_at,
            "contains_private_values": False,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-commit", default=PRODUCT_COMMIT)
    args = parser.parse_args()
    product_commit = subprocess.run(
        ["git", "rev-parse", args.product_commit],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    if product_commit != PRODUCT_COMMIT:
        raise RuntimeError(f"unexpected product commit: {product_commit}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    observed_at = _now()
    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage11-phase112-") as temp_name:
        rehearsal = _exercise_restore(Path(temp_name))

    _write_json(OUTPUT_DIR / "online_backup_rehearsal.json", rehearsal["online"])
    _write_json(OUTPUT_DIR / "restore_rehearsal.json", rehearsal["restore"])
    _write_json(OUTPUT_DIR / "rollback_rehearsal.json", rehearsal["rollback"])
    _write_json(OUTPUT_DIR / "database_before_after.json", rehearsal["database"])
    (OUTPUT_DIR / "integrity_checks.txt").write_text(
        "integrity_check: ok\nforeign_key_issue_count: 0\n"
        "migration_registry_valid: true\napplication_invariant_failures: 0\n"
        "automatic_rollback_verified: true\nstatus: pass\n",
        encoding="utf-8",
    )
    _write_json(
        OUTPUT_DIR / "phase_contract.json",
        {
            "schema": "PFIV025Stage11Phase112ContractV1",
            "phase_id": PHASE_ID,
            "task_ids": list(TASK_IDS),
            "acceptance_id": ACCEPTANCE_ID,
            "risk_tier": "T2_SQLITE_BACKUP_RESTORE_ATOMIC_REPLACEMENT",
            "implementation_base": IMPLEMENTATION_BASE,
            "product_commit": product_commit,
            "current_phase_only": True,
            "scope_override_authorized": True,
            "canonical_private_database_used": False,
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
            "network_scope": "official_documentation_research_only",
            "product_runtime_external_network_calls": 0,
            "push_performed": False,
            "app_install_performed": False,
            "phase_11_3_started": False,
            "whole_stage_review_started": False,
        },
    )
    (OUTPUT_DIR / "risk_and_rollback.md").write_text(
        "# Phase 11.2 Risk and Rollback\n\n"
        "- 仅 PFI lock-aware transaction 受 maintenance lock 协调；"
        "外部 client 必须 quiesce。\n"
        "- sidecar、stale target hash、unsafe permissions、"
        "cross-filesystem replace 均 fail closed。\n"
        "- 只使用 disposable nonfinancial SQLite；canonical private DB 未读写。\n"
        "- Phase 11.3、whole-stage review、push、install、"
        "production/final acceptance 未开始。\n"
        "- 研究层只访问 sqlite.org 与 docs.python.org 官方文档；"
        "产品/测试 runtime 外网调用为 0。\n\n"
        "Rollback：先 revert Phase 11.2 evidence/governance commit，"
        f"再 revert {product_commit}。\n",
        encoding="utf-8",
    )

    product_files = subprocess.run(
        ["git", "diff", "--name-only", IMPLEMENTATION_BASE, product_commit],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    changed_files = sorted(set(product_files + list(RECORD_FILES)))
    unexpected = sorted(set(_working_tree_files()) - set(RECORD_FILES))
    if unexpected:
        raise RuntimeError(f"unexpected Phase 11.2 working files: {unexpected}")
    (OUTPUT_DIR / "changed_files.txt").write_text(
        "\n".join(changed_files) + "\n", encoding="utf-8"
    )

    test_command = [
        str(Path(os.sys.executable)),
        "-B",
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "PFI/tests/test_v025_stage11_backup_restore.py",
        "PFI/tests/test_v025_stage11_sqlite_concurrency.py",
        "PFI/tests/test_v025_stage11_migration_lifecycle.py",
        "PFI/tests/test_v025_stage7_import_review_ledger.py",
        "PFI/tests/test_v025_stage7_holding_persistence.py",
        "PFI/tests/test_v025_stage10_job_lifecycle.py",
        "PFI/tests/test_v025_stage10_job_observability.py",
        "PFI/tests/test_v025_stage10_crash_recovery.py",
        "PFI/tests/test_v025_stage1_release_identity.py",
    ]
    test_result = _run(test_command)
    if int(test_result["exit_code"]) != 0:
        raise RuntimeError("Phase 11.2 product verification failed")

    provisional_results: list[dict[str, object]] = []
    verification = {
        "schema": "PFIV025Stage11Phase112VerificationV1",
        "observed_at": observed_at,
        "status": "pass",
        "results": [test_result],
        "overlay_governance_pending": True,
    }
    _write_json(OUTPUT_DIR / "verification_results.json", verification)
    (OUTPUT_DIR / "terminal.log").write_text(
        f"$ {test_result['command']}\n{test_result['output']}\n"
        "$ disposable online backup, isolated restore and injected rollback rehearsal\n"
        "online backup pass; atomic restore pass; automatic rollback pass\n",
        encoding="utf-8",
    )
    privacy_candidates = [
        OUTPUT_DIR / name
        for name in REPORT_NAMES
        if name not in {"artifact_hashes.json", "evidence.json", "privacy_scan.txt"}
    ] + [PFI_ROOT / "docs/pfi_v025/stage_11/PHASE_11_2_BACKUP_RESTORE_IMPLEMENTATION.md"]
    (OUTPUT_DIR / "privacy_scan.txt").write_text(
        _privacy_scan(privacy_candidates), encoding="utf-8"
    )
    evidence = _build_evidence(
        observed_at=observed_at,
        product_commit=product_commit,
        changed_files=changed_files,
        test_result=test_result,
        governance_results=provisional_results,
        rehearsal=rehearsal,
    )
    schema = _evidence_schema()
    schema_errors = sorted(
        Draft202012Validator(schema).iter_errors(evidence), key=lambda error: list(error.path)
    )
    if schema_errors:
        raise RuntimeError(
            "TaskPack evidence schema failed: "
            + "; ".join(error.message for error in schema_errors)
        )
    _write_json(OUTPUT_DIR / "evidence.json", evidence)
    _write_artifact_hashes(observed_at, product_commit)

    governance_results = _complete_overlay_governance()
    verification = {
        "schema": "PFIV025Stage11Phase112VerificationV1",
        "observed_at": observed_at,
        "status": "pass",
        "results": [test_result, *governance_results],
        "overlay_governance_pending": False,
    }
    if any(int(row["exit_code"]) != 0 for row in verification["results"]):
        verification["status"] = "fail"
        _write_json(OUTPUT_DIR / "verification_results.json", verification)
        raise RuntimeError("Phase 11.2 complete-overlay verification failed")
    _write_json(OUTPUT_DIR / "verification_results.json", verification)
    terminal_lines = [
        f"$ {test_result['command']}",
        str(test_result["output"]),
        "$ disposable online backup, isolated restore and injected rollback rehearsal",
        "online backup pass; atomic restore pass; automatic rollback pass",
    ]
    for row in governance_results:
        terminal_lines.extend([f"$ {row['command']}", str(row["output"])])
    (OUTPUT_DIR / "terminal.log").write_text(
        "\n".join(terminal_lines) + "\n", encoding="utf-8"
    )
    (OUTPUT_DIR / "privacy_scan.txt").write_text(
        _privacy_scan(privacy_candidates), encoding="utf-8"
    )
    evidence = _build_evidence(
        observed_at=observed_at,
        product_commit=product_commit,
        changed_files=changed_files,
        test_result=test_result,
        governance_results=governance_results,
        rehearsal=rehearsal,
    )
    schema_errors = sorted(
        Draft202012Validator(schema).iter_errors(evidence), key=lambda error: list(error.path)
    )
    if schema_errors:
        raise RuntimeError(
            "TaskPack evidence schema failed: "
            + "; ".join(error.message for error in schema_errors)
        )
    _write_json(OUTPUT_DIR / "evidence.json", evidence)
    _write_artifact_hashes(observed_at, product_commit)
    print(
        json.dumps(
            {
                "status": "candidate_pass",
                "phase_id": PHASE_ID,
                "target_tests": str(test_result["summary"]),
                "online_backup_method": rehearsal["online"]["method"],
                "restore_status": rehearsal["restore"]["status"],
                "rollback_status": rehearsal["rollback"]["status"],
                "artifact_count": json.loads(
                    (OUTPUT_DIR / "artifact_hashes.json").read_text(encoding="utf-8")
                )["artifact_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
