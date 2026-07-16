#!/usr/bin/env python3
"""Build PFI v0.2.5 Stage 11 Phase 11.1 disposable SQLite evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime, timezone
import zipfile

from jsonschema import Draft202012Validator

from pfi_os.application.operational_store import OperationalStore
from pfi_os.infrastructure.operational_store_runtime import (
    MigrationChecksumMismatch,
    UnsafeSQLiteRuntimeError,
    apply_operational_migration,
    audit_sqlite_connection,
    evaluate_sqlite_runtime,
    migration_checksum,
    operational_transaction,
    select_journal_mode,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
OUTPUT_DIR = PFI_ROOT / "reports/pfi_v025/stage_11/phase_11_1"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
IMPLEMENTATION_BASE = "8b7d301985e83458a4558d01d0603c08ac2e6f8c"
PRIMARY_PRODUCT_COMMIT = "b07709d0453d3d2c6d36a10375d823dbb0870c53"
PRODUCT_COMMIT = "ad16901505f7e6f23653aa8b1e03945211dc4e93"
PHASE_RECORD_COMMIT = "2f3ec4c2f19b6440c009a18ba923e40441cdb07d"
PHASE_ID = "V025-S11-P11.1"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE11-WHOLE-REVIEW"
TASK_IDS = ("S11-P1-T1", "S11-P1-T2", "S11-P1-T3", "S11-P1-T4")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def _run(command: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    output = _sanitize_text((completed.stdout + completed.stderr).strip())
    return {
        "command": _sanitize_text(" ".join(command)),
        "exit_code": completed.returncode,
        "output": output,
        "summary": output.splitlines()[-1] if output else "no output",
    }


def _sanitize_text(value: str) -> str:
    return str(value).replace(str(Path.home()), "$HOME")


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


def _writer(db_path: str, worker_id: int, writes: int, start: object) -> None:
    start.wait(timeout=10)
    for index in range(writes):
        with operational_transaction(db_path, immediate=True) as conn:
            conn.execute(
                "INSERT INTO concurrency_probe(worker_id, row_index) VALUES (?, ?)",
                (worker_id, index),
            )


def _uncommitted_victim(db_path: str, ready: object) -> None:
    with operational_transaction(db_path, immediate=True) as conn:
        conn.execute("INSERT INTO kill_probe(marker) VALUES ('uncommitted')")
        ready.set()
        time.sleep(60)


def _snapshot(db_path: Path) -> dict[str, object]:
    if not db_path.exists():
        return {"exists": False, "table_count": 0, "tables": [], "migration_ids": []}
    with sqlite3.connect(db_path) as conn:
        tables = [
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        migrations = (
            [
                str(row[0])
                for row in conn.execute(
                    "SELECT migration_id FROM pfi_operational_migrations ORDER BY migration_id"
                )
            ]
            if "pfi_operational_migrations" in tables
            else []
        )
        return {
            "exists": True,
            "table_count": len(tables),
            "tables": tables,
            "migration_ids": migrations,
            "integrity_check": str(conn.execute("PRAGMA integrity_check").fetchone()[0]),
            "foreign_key_issue_count": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
        }


def _exercise_database(temp_root: Path) -> dict[str, object]:
    db_path = temp_root / "private" / "operational" / "pfi.sqlite"
    before = _snapshot(db_path)
    store = OperationalStore(db_path)
    store.initialize()
    with store.connect(immediate=True) as conn:
        conn.execute(
            "CREATE TABLE concurrency_probe("
            "worker_id INTEGER NOT NULL, row_index INTEGER NOT NULL, "
            "PRIMARY KEY(worker_id, row_index))"
        )
        conn.execute("CREATE TABLE kill_probe(marker TEXT PRIMARY KEY)")
        pragma = audit_sqlite_connection(conn)

    context = multiprocessing.get_context("spawn")
    worker_count = 4
    writes_per_worker = 25
    start = context.Event()
    workers = [
        context.Process(
            target=_writer,
            args=(str(db_path), worker_id, writes_per_worker, start),
        )
        for worker_id in range(worker_count)
    ]
    started = time.monotonic()
    for worker in workers:
        worker.start()
    start.set()
    for worker in workers:
        worker.join(timeout=30)
    elapsed_ms = round((time.monotonic() - started) * 1000, 3)
    worker_exit_codes = [worker.exitcode for worker in workers]
    if worker_exit_codes != [0] * worker_count:
        raise RuntimeError(f"concurrency workers failed: {worker_exit_codes}")

    ready = context.Event()
    victim = context.Process(target=_uncommitted_victim, args=(str(db_path), ready))
    victim.start()
    if not ready.wait(timeout=10):
        victim.kill()
        raise RuntimeError("SIGKILL victim never reached uncommitted checkpoint")
    victim.kill()
    victim.join(timeout=10)
    if victim.exitcode in (None, 0):
        raise RuntimeError(f"SIGKILL victim did not terminate as expected: {victim.exitcode}")

    migration_sql = """
    CREATE TABLE migration_probe(probe_id TEXT PRIMARY KEY, state TEXT NOT NULL);
    INSERT INTO migration_probe(probe_id, state) VALUES ('phase-11-1', 'applied');
    """
    checksum = migration_checksum(migration_sql)
    applied = apply_operational_migration(
        db_path,
        migration_id="v025_stage11_evidence_probe_v1",
        migration_sql=migration_sql,
        expected_checksum=checksum,
    )
    replayed = apply_operational_migration(
        db_path,
        migration_id="v025_stage11_evidence_probe_v1",
        migration_sql=migration_sql,
        expected_checksum=checksum,
    )
    checksum_drift_rejected = False
    drifted = migration_sql.replace("NOT NULL", "")
    try:
        apply_operational_migration(
            db_path,
            migration_id="v025_stage11_evidence_probe_v1",
            migration_sql=drifted,
            expected_checksum=migration_checksum(drifted),
        )
    except MigrationChecksumMismatch:
        checksum_drift_rejected = True

    failing_sql = """
    CREATE TABLE must_rollback(value TEXT PRIMARY KEY);
    INSERT INTO must_rollback VALUES ('partial');
    INSERT INTO absent_table VALUES ('forced failure');
    """
    failure_type = ""
    try:
        apply_operational_migration(
            db_path,
            migration_id="v025_stage11_forced_failure_probe_v1",
            migration_sql=failing_sql,
            expected_checksum=migration_checksum(failing_sql),
        )
    except sqlite3.OperationalError as exc:
        failure_type = type(exc).__name__

    with store.connect() as conn:
        actual_writes = int(conn.execute("SELECT COUNT(*) FROM concurrency_probe").fetchone()[0])
        unique_writes = int(
            conn.execute(
                "SELECT COUNT(*) FROM (SELECT worker_id, row_index FROM concurrency_probe GROUP BY worker_id, row_index)"
            ).fetchone()[0]
        )
        uncommitted_rows = int(conn.execute("SELECT COUNT(*) FROM kill_probe").fetchone()[0])
        rolled_back_table_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='must_rollback'"
            ).fetchone()[0]
        )
        failed_registry_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM pfi_operational_migrations WHERE migration_id=?",
                ("v025_stage11_forced_failure_probe_v1",),
            ).fetchone()[0]
        )
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        foreign_key_issues = len(conn.execute("PRAGMA foreign_key_check").fetchall())

    expected_writes = worker_count * writes_per_worker
    if not (
        actual_writes == unique_writes == expected_writes
        and uncommitted_rows == 0
        and rolled_back_table_count == 0
        and failed_registry_count == 0
        and integrity == "ok"
        and foreign_key_issues == 0
        and checksum_drift_rejected
        and failure_type == "OperationalError"
    ):
        raise RuntimeError("disposable SQLite evidence invariants failed")

    after = _snapshot(db_path)
    return {
        "before": before,
        "after": after,
        "pragma": pragma,
        "concurrency": {
            "status": "pass",
            "worker_count": worker_count,
            "writes_per_worker": writes_per_worker,
            "expected_write_count": expected_writes,
            "actual_write_count": actual_writes,
            "unique_write_count": unique_writes,
            "worker_exit_codes": worker_exit_codes,
            "elapsed_ms": elapsed_ms,
        },
        "power_loss": {
            "status": "pass",
            "mechanism": "actual multiprocessing.Process.kill (SIGKILL)",
            "victim_exit_code": victim.exitcode,
            "uncommitted_row_count_after_reopen": uncommitted_rows,
            "integrity_check_after_reopen": integrity,
            "foreign_key_issue_count_after_reopen": foreign_key_issues,
        },
        "migration": {
            "status": "pass",
            "migration_id": "v025_stage11_evidence_probe_v1",
            "checksum_sha256": checksum,
            "first_apply": applied,
            "replay": replayed,
            "checksum_drift_rejected": checksum_drift_rejected,
            "forced_failure_type": failure_type,
            "rolled_back_table_count": rolled_back_table_count,
            "failed_registry_entry_count": failed_registry_count,
        },
        "integrity": {
            "status": "pass",
            "integrity_check": integrity,
            "foreign_key_issue_count": foreign_key_issues,
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
            [str(Path(os.sys.executable)), "scripts/validate_project_governance.py", "--project", "PFI"],
            [str(Path(os.sys.executable)), "scripts/lean_governance.py", "check-render", "--project", "PFI"],
            ["/usr/bin/python3", "scripts/lean_governance.py", "check-render", "--project", "PFI"],
        )
        return [_run(command, cwd=target) for command in commands]


def _evidence_schema() -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        candidates = [
            name for name in archive.namelist() if name.endswith("schemas/evidence_pack.schema.json")
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
        "canonical_private_uri": "private/operational/pfi.sqlite",
    }
    lines = ["PFI v0.2.5 Stage 11 Phase 11.1 privacy scan"]
    total = 0
    for label, needle in forbidden.items():
        count = 0
        for path in paths:
            if path.exists() and needle.encode("utf-8") in path.read_bytes():
                count += 1
        total += count
        lines.append(f"{label}: {count}")
    lines.extend(
        [
            f"total_forbidden_match_count: {total}",
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
    assessment = evaluate_sqlite_runtime()
    runtime_payload = assessment.as_dict()
    runtime_payload.update(
        {
            "schema": "PFIV025Stage11SQLiteRuntimeV1",
            "phase_id": PHASE_ID,
            "observed_at": observed_at,
            "python_version": os.sys.version.split()[0],
            "requested_wal_result": "not_evaluated",
        }
    )
    try:
        runtime_payload["requested_wal_result"] = select_journal_mode(
            assessment, request_wal=True
        )
    except UnsafeSQLiteRuntimeError as exc:
        runtime_payload["requested_wal_result"] = "rejected"
        runtime_payload["requested_wal_error"] = str(exc)

    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage11-phase111-") as temp_name:
        database = _exercise_database(Path(temp_name))

    _write_json(OUTPUT_DIR / "sqlite_runtime.json", runtime_payload)
    _write_json(
        OUTPUT_DIR / "pragma_settings.json",
        {
            "schema": "PFIV025Stage11PragmaSettingsV1",
            "phase_id": PHASE_ID,
            "observed_at": observed_at,
            "status": "pass",
            **database["pragma"],
        },
    )
    _write_json(OUTPUT_DIR / "concurrency_result.json", database["concurrency"])
    _write_json(OUTPUT_DIR / "power_loss_recovery.json", database["power_loss"])
    _write_json(OUTPUT_DIR / "migration_rehearsal.json", database["migration"])
    _write_json(
        OUTPUT_DIR / "database_before_after.json",
        {
            "schema": "PFIV025Stage11DatabaseBeforeAfterV1",
            "database_scope": "ephemeral_isolated_sqlite_only",
            "before": database["before"],
            "after": database["after"],
        },
    )
    (OUTPUT_DIR / "integrity_checks.txt").write_text(
        "integrity_check: ok\nforeign_key_issue_count: 0\n"
        "concurrent_write_count: 100\nuncommitted_sigkill_row_count: 0\nstatus: pass\n",
        encoding="utf-8",
    )

    target_command = [
        str(Path(os.sys.executable)),
        "-B",
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "PFI/tests/test_v025_stage11_sqlite_concurrency.py",
        "PFI/tests/test_v025_stage11_migration_lifecycle.py",
        "PFI/tests/test_v025_stage7_import_review_ledger.py",
        "PFI/tests/test_v025_stage7_holding_persistence.py",
        "PFI/tests/test_v025_stage10_job_lifecycle.py",
        "PFI/tests/test_v025_stage1_release_identity.py",
    ]
    target_result = _run(target_command)
    governance_results = _complete_overlay_governance()
    verification = {
        "schema": "PFIV025Stage11Phase111VerificationV1",
        "observed_at": observed_at,
        "status": "pass",
        "results": [target_result, *governance_results],
    }
    if any(int(row["exit_code"]) != 0 for row in verification["results"]):
        verification["status"] = "fail"
        _write_json(OUTPUT_DIR / "verification_results.json", verification)
        raise RuntimeError("Phase 11.1 verification failed")
    _write_json(OUTPUT_DIR / "verification_results.json", verification)

    phase_contract = {
        "schema": "PFIV025Stage11Phase111ContractV1",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "risk_tier": "T2_SQLITE_RUNTIME_CONCURRENCY_MIGRATION",
        "product_commit": product_commit,
        "product_commits": [PRIMARY_PRODUCT_COMMIT, product_commit],
        "current_phase_only": True,
        "scope_override": {
            "authorized": True,
            "path": "PFI/src/pfi_os/application/operational_store.py",
            "reason": "active base OperationalStore must consume the infrastructure gate",
        },
        "safety_boundary": {
            "canonical_private_database_used": False,
            "network_performed": True,
            "external_network_performed": True,
            "network_scope": "official_documentation_research_only",
            "official_research_domains": ["sqlite.org"],
            "product_runtime_network_performed": False,
            "product_runtime_external_network_calls": 0,
            "financial_values_emitted": 0,
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
            "push_performed": False,
            "app_install_performed": False,
        },
        "phase_11_2_started": False,
        "phase_11_3_started": False,
        "whole_stage_review_started": False,
    }
    _write_json(OUTPUT_DIR / "phase_contract.json", phase_contract)

    risk_text = f"""# Phase 11.1 Risk and Rollback

- 当前 SQLite `{assessment.version}` 不在 WAL-safe 集合；显式 WAL 请求 fail closed，默认使用 `DELETE` rollback journal。
- 只验证 disposable SQLite 的并发、SIGKILL、migration 与 rollback；canonical private PFI DB 未读取、未迁移、未修改。
- TaskPack 未列出真实活跃基础入口 `PFI/src/pfi_os/application/operational_store.py`；standing authorization 下仅对该文件作必要 scope override，`allowed_files_obeyed=false` 如实保留。
- Phase 11.2 online backup、隔离 restore、原子替换及失败恢复未开始；任何 canonical migration 前仍须通过该 Phase。
- Phase 11.3 公共/私有分发边界与 Stage 11 whole-stage review 未开始。
- 研究层仅访问 SQLite 官方文档核对当前安全公告；产品/测试 runtime 外网调用为 0。未使用 Finder、LaunchServices、GUI、push 或 app install；model/formula/parameter 数值未修改。

Rollback：先 revert Phase 11.1 证据/治理提交，再依次 revert release-identity 提交 `{product_commit}` 与主产品提交 `{PRIMARY_PRODUCT_COMMIT}`。本轮没有 canonical DB 或安装面副作用。
"""
    (OUTPUT_DIR / "risk_and_rollback.md").write_text(risk_text, encoding="utf-8")

    expected_evidence_files = [
        "artifact_hashes.json",
        "changed_files.txt",
        "concurrency_result.json",
        "database_before_after.json",
        "evidence.json",
        "integrity_checks.txt",
        "migration_rehearsal.json",
        "phase_contract.json",
        "power_loss_recovery.json",
        "pragma_settings.json",
        "privacy_scan.txt",
        "risk_and_rollback.md",
        "sqlite_runtime.json",
        "terminal.log",
        "verification_results.json",
    ]
    phase_files = subprocess.run(
        ["git", "diff", "--name-only", IMPLEMENTATION_BASE, PHASE_RECORD_COMMIT],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    working_files = _working_tree_files()
    report_files = [
        (OUTPUT_DIR / name).relative_to(REPO_ROOT).as_posix() for name in expected_evidence_files
    ]
    changed_files = sorted(set(phase_files + working_files + report_files))
    (OUTPUT_DIR / "changed_files.txt").write_text("\n".join(changed_files) + "\n", encoding="utf-8")

    terminal_lines = [
        f"$ {target_result['command']}",
        str(target_result["output"]),
        "$ disposable SQLite runtime/config/concurrency/SIGKILL/migration rehearsal",
        "runtime gate pass; 100/100 writes; SIGKILL uncommitted rows 0; integrity/FK pass",
    ]
    for row in governance_results:
        terminal_lines.extend([f"$ {row['command']}", str(row["output"])])
    (OUTPUT_DIR / "terminal.log").write_text("\n".join(terminal_lines) + "\n", encoding="utf-8")

    privacy_candidates = [
        OUTPUT_DIR / name
        for name in expected_evidence_files
        if name not in {"artifact_hashes.json", "evidence.json", "privacy_scan.txt"}
    ]
    (OUTPUT_DIR / "privacy_scan.txt").write_text(
        _privacy_scan(privacy_candidates), encoding="utf-8"
    )

    evidence_files = [path.relative_to(REPO_ROOT).as_posix() for path in privacy_candidates]
    evidence_files.extend(
        [
            "PFI/docs/pfi_v025/stage_11/PHASE_11_1_SQLITE_SAFETY_IMPLEMENTATION.md",
            "PFI/reports/pfi_v025/stage_11/phase_11_1/privacy_scan.txt",
        ]
    )
    evidence = {
        "schema": "PFIV025Stage11Phase111EvidenceV1",
        "version": "v0.2.5",
        "stage": 11,
        "phase": "11.1",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "task_statuses": {task_id: "candidate_complete" for task_id in TASK_IDS},
        "acceptance_id": ACCEPTANCE_ID,
        "status": "candidate_pass",
        "git_commit": product_commit,
        "product_commit": product_commit,
        "product_commits": [PRIMARY_PRODUCT_COMMIT, product_commit],
        "implementation_base": IMPLEMENTATION_BASE,
        "primary_product_commit": PRIMARY_PRODUCT_COMMIT,
        "release_identity_commit": product_commit,
        "allowed_files_obeyed": False,
        "scope_override_authorized": True,
        "scope_override_path": "PFI/src/pfi_os/application/operational_store.py",
        "commands": [
            {
                "command": str(target_result["command"]),
                "exit_code": int(target_result["exit_code"]),
                "summary": str(target_result["summary"]),
            },
            {
                "command": "disposable SQLite runtime/config/concurrency/SIGKILL/migration rehearsal",
                "exit_code": 0,
                "summary": "100/100 unique writes; killed uncommitted row rolled back; integrity/FK/checksum lifecycle passed.",
            },
            *[
                {
                    "command": str(row["command"]),
                    "exit_code": int(row["exit_code"]),
                    "summary": str(row["summary"]),
                }
                for row in governance_results
            ],
        ],
        "changed_files": changed_files,
        "evidence_files": sorted(set(evidence_files)),
        "explicitly_not_done": [
            "Phase 11.2 online backup, isolated restore, atomic replacement and automatic rollback",
            "Phase 11.3 public/private distribution boundary and context export",
            "Stage 11 whole-stage independent review, remediation, rereview and transition acceptance",
            "canonical private PFI database read, migration, write or acceptance",
            "product/runtime external network, GitHub push, canonical PFI.app install, production or final acceptance",
        ],
        "risks": [
            f"Current SQLite {assessment.version} is unsafe for concurrent WAL and is therefore gated to DELETE journal.",
            "Disposable stress evidence does not accept canonical private database migration or production load.",
            "The active application OperationalStore required one authorized path override outside the literal TaskPack implementation allowlist.",
            "Backup/restore remains a mandatory Phase 11.2 gate before any canonical database migration.",
        ],
        "rollback": (
            "Revert the Phase 11.1 evidence/governance commit, then revert release-identity commit "
            f"{product_commit} and primary product commit {PRIMARY_PRODUCT_COMMIT}; "
            "no canonical DB or install rollback is required."
        ),
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "canonical_private_database_used": False,
        "database_scope": "ephemeral_isolated_sqlite_only",
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
        "official_research_domains": ["sqlite.org"],
        "official_research_sources": [
            "https://sqlite.org/wal.html",
            "https://sqlite.org/releaselog/3_51_3.html",
        ],
        "product_runtime_network_performed": False,
        "product_runtime_external_network_calls": 0,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "sqlite_version": assessment.version,
        "sqlite_wal_safe": assessment.wal_safe,
        "journal_mode": str(database["pragma"]["journal_mode"]),
        "concurrent_write_count": int(database["concurrency"]["actual_write_count"]),
        "sigkill_uncommitted_row_count": int(
            database["power_loss"]["uncommitted_row_count_after_reopen"]
        ),
        "integrity_status": str(database["integrity"]["status"]),
        "overall_completed_task_count": 136,
        "overall_task_count": 156,
        "overall_progress_percent": 87.18,
        "stage_11_completed_task_count": 4,
        "stage_11_total_task_count": 12,
        "stage_11_status": "in_progress",
        "phase_11_1_status": "candidate_pass",
        "phase_11_2_status": "not_started",
        "phase_11_3_status": "not_started",
        "stage_11_whole_stage_review_status": "not_started",
        "next_task_id": "S11-P2-T1",
        "next_acceptance_id": ACCEPTANCE_ID,
        "observed_at": observed_at,
    }
    schema_errors = sorted(
        Draft202012Validator(_evidence_schema()).iter_errors(evidence),
        key=lambda error: list(error.path),
    )
    if schema_errors:
        raise RuntimeError("TaskPack evidence schema failed: " + "; ".join(e.message for e in schema_errors))
    _write_json(OUTPUT_DIR / "evidence.json", evidence)

    hash_targets = [
        PFI_ROOT / "docs/pfi_v025/stage_11/PHASE_11_1_SQLITE_SAFETY_IMPLEMENTATION.md",
        PFI_ROOT / "src/pfi_os/infrastructure/operational_store_runtime.py",
        PFI_ROOT / "src/pfi_os/application/operational_store.py",
        PFI_ROOT / "src/pfi_os/infrastructure/operational_import_store.py",
        PFI_ROOT / "src/pfi_os/infrastructure/operational_holding_settings_store.py",
        PFI_ROOT / "tests/test_v025_stage11_sqlite_concurrency.py",
        PFI_ROOT / "tests/test_v025_stage11_migration_lifecycle.py",
        PFI_ROOT / "scripts/v025/build_stage11_phase111_evidence.py",
        PFI_ROOT / "config/release_manifest.json",
        PFI_ROOT / "src/pfi_v02/stage_v021_runtime_api.py",
        PFI_ROOT / "tests/test_v025_stage1_release_identity.py",
        PFI_ROOT / "web/index.html",
        *[
            OUTPUT_DIR / name
            for name in expected_evidence_files
            if name != "artifact_hashes.json"
        ],
    ]
    artifacts = {
        path.relative_to(REPO_ROOT).as_posix(): {
            "byte_size": path.stat().st_size,
            "sha256": _sha(path),
        }
        for path in sorted(set(hash_targets))
    }
    _write_json(
        OUTPUT_DIR / "artifact_hashes.json",
        {
            "schema": "PFIV025Stage11Phase111ArtifactHashesV1",
            "phase_id": PHASE_ID,
            "product_commit": product_commit,
            "observed_at": observed_at,
            "contains_private_values": False,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )
    print(
        json.dumps(
            {
                "status": "candidate_pass",
                "phase_id": PHASE_ID,
                "sqlite_version": assessment.version,
                "wal_safe": assessment.wal_safe,
                "journal_mode": database["pragma"]["journal_mode"],
                "concurrent_writes": database["concurrency"]["actual_write_count"],
                "sigkill_uncommitted_rows": database["power_loss"][
                    "uncommitted_row_count_after_reopen"
                ],
                "artifact_count": len(artifacts),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
