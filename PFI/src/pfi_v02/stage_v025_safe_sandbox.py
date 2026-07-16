from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import sqlite3
import stat
import subprocess
import tempfile
import tracemalloc
from pathlib import Path
from statistics import median
from time import perf_counter_ns
from typing import Any, Mapping

from pfi_v02.stage_v025_data_inventory import build_public_artifact_scan_report


VERSION = "v0.2.5"
STAGE = 2
PHASE_ID = "V025-S2-P2.3"
TASK_IDS = ("S2-P3-T1", "S2-P3-T2", "S2-P3-T3", "S2-P3-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S2-P23-SAFE-SANDBOX"
CONTRACT_ID = "PFI-V025-STAGE2-PHASE23-SAFE-SANDBOX"
TRANSACTION_SOURCE_ID = "SRC-TRANSACTIONS-ALIPAY"
DATABASE_SOURCE_ID = "SRC-OPERATIONAL-SQLITE"
TRANSACTION_ROOT_ALIAS = "MetaDatabase/PFI"
TRANSACTION_TREE_PATH = "MetaDatabase/PFI"
TRANSACTION_MANIFEST_PATH = "MetaDatabase/PFI/alipay_daily/processed/alipay_import_manifest.json"
TRANSACTION_CSV_PATH = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv"
DATABASE_ALIAS = "$PFI_DATA_HOME/private/operational/pfi.sqlite"
_KNOWN_DB_TABLES = (
    "source_records",
    "source_versions",
    "entity_records",
    "evidence_records",
    "job_records",
    "task_records",
    "holding_snapshots",
)
_NETWORK_IMPORT_ROOTS = {"aiohttp", "httpx", "requests", "socket", "urllib"}
_FORBIDDEN_BASELINE_ARGUMENTS = {
    "data",
    "financial_records",
    "fixture",
    "fixtures",
    "records",
    "rows",
    "sample",
    "synthetic",
    "transactions",
}
_PHASE23_PRIVACY_INPUTS = (
    "PFI/reports/pfi_v025/stage_2/phase_2_3/sandbox_attestation.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/database_before_after.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/performance_baseline.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/no_fake_audit.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/stage_2_evidence_index.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/evidence.json",
    "PFI/docs/pfi_v025/stage_2/sandbox_spec.md",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/risk_and_rollback.md",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/terminal.log",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/changed_files.txt",
)


def build_phase23_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage2Phase23ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "contract_id": CONTRACT_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "current_phase_only": True,
        "real_data_read_only": True,
        "financial_fixture_fallback_allowed": False,
        "public_evidence_redacted": True,
        "finder_used": False,
        "risk_tier": "T3_PRIVACY_REAL_DATA",
        "explicitly_not_done": [
            "Stage 2 whole-stage review",
            "Stage 2 user acceptance",
            "Stage 3",
            "production FX load",
            "financial metric calculation",
            "source or database mutation",
            "GitHub push",
            "canonical App install",
        ],
    }


def resolve_git_object_snapshot(
    project_root: str | Path,
    *,
    git_ref: str = "HEAD",
) -> dict[str, Any]:
    repo_root = _repo_root(project_root)
    base = {
        "status": "source_missing",
        "source_id": TRANSACTION_SOURCE_ID,
        "path_alias": TRANSACTION_ROOT_ALIAS,
        "isolation_mode": "immutable_git_object_snapshot",
        "resolved_commit": None,
        "tree_oid": None,
        "manifest_blob_oid": None,
        "transactions_blob_oid": None,
        "manifest_bytes": None,
        "input_bytes": None,
        "snapshot_immutable": True,
        "source_write_capability": False,
        "source_mutation_performed": False,
        "private_values_included": False,
        "raw_rows_emitted": 0,
        "finder_used": False,
    }
    try:
        commit = _git_text(repo_root, "rev-parse", "--verify", f"{git_ref}^{{commit}}")
        tree_oid = _git_text(repo_root, "rev-parse", f"{commit}:{TRANSACTION_TREE_PATH}")
        manifest_oid = _git_text(repo_root, "rev-parse", f"{commit}:{TRANSACTION_MANIFEST_PATH}")
        transactions_oid = _git_text(repo_root, "rev-parse", f"{commit}:{TRANSACTION_CSV_PATH}")
        manifest_bytes = int(_git_text(repo_root, "cat-file", "-s", manifest_oid))
        input_bytes = int(_git_text(repo_root, "cat-file", "-s", transactions_oid))
        for oid, expected_kind in (
            (tree_oid, "tree"),
            (manifest_oid, "blob"),
            (transactions_oid, "blob"),
        ):
            if _git_text(repo_root, "cat-file", "-t", oid) != expected_kind:
                raise ValueError("unexpected_git_object_kind")
    except (OSError, ValueError, subprocess.CalledProcessError):
        return base
    return {
        **base,
        "status": "ready",
        "resolved_commit": commit,
        "tree_oid": tree_oid,
        "manifest_blob_oid": manifest_oid,
        "transactions_blob_oid": transactions_oid,
        "manifest_bytes": manifest_bytes,
        "input_bytes": input_bytes,
    }


def run_git_object_read_parse_baseline(
    project_root: str | Path,
    *,
    git_ref: str = "HEAD",
    iterations: int = 3,
) -> dict[str, Any]:
    if type(iterations) is not int or not 1 <= iterations <= 10:
        raise ValueError("iterations must be an integer between 1 and 10")
    repo_root = _repo_root(project_root)
    snapshot = resolve_git_object_snapshot(repo_root, git_ref=git_ref)
    identity_before = _snapshot_identity(snapshot)
    blocked = {
        "schema": "PFIV025Phase23PerformanceBaselineV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "2.3",
        "source_id": TRANSACTION_SOURCE_ID,
        "status": "blocked",
        "real_input_status": str(snapshot["status"]),
        "isolation_mode": "immutable_git_object_snapshot",
        "resolved_commit": snapshot["resolved_commit"],
        "tree_oid": snapshot["tree_oid"],
        "transactions_blob_oid": snapshot["transactions_blob_oid"],
        "parser": "python_csv_utf8_sig_in_memory_read_only_v1",
        "input_bytes": snapshot["input_bytes"],
        "manifest_record_count": None,
        "record_count": None,
        "field_count": None,
        "record_count_matches_manifest": False,
        "iterations": iterations,
        "elapsed_ms": None,
        "peak_python_alloc_bytes": None,
        "source_identity_before": identity_before,
        "source_identity_after": identity_before,
        "source_mutation_performed": False,
        "financial_fixture_fallback_used": False,
        "financial_values_emitted": 0,
        "raw_rows_emitted": 0,
        "private_values_included": False,
        "finder_used": False,
    }
    if snapshot["status"] != "ready":
        return blocked

    elapsed_samples: list[float] = []
    peak_samples: list[int] = []
    observed_counts: list[int] = []
    observed_field_counts: list[int] = []
    manifest_counts: list[int] = []
    try:
        for _ in range(iterations):
            tracemalloc.start()
            started = perf_counter_ns()
            manifest_raw = _git_bytes(repo_root, "cat-file", "blob", str(snapshot["manifest_blob_oid"]))
            transactions_raw = _git_bytes(
                repo_root,
                "cat-file",
                "blob",
                str(snapshot["transactions_blob_oid"]),
            )
            manifest = json.loads(manifest_raw.decode("utf-8"))
            reader = csv.reader(io.StringIO(transactions_raw.decode("utf-8-sig"), newline=""))
            header = next(reader)
            row_count = sum(1 for _row in reader)
            elapsed = (perf_counter_ns() - started) / 1_000_000
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed_samples.append(elapsed)
            peak_samples.append(peak)
            observed_counts.append(row_count)
            observed_field_counts.append(len(header))
            manifest_counts.append(int(manifest["transaction_count"]))
    except (KeyError, OSError, UnicodeError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError):
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        return blocked

    snapshot_after = resolve_git_object_snapshot(repo_root, git_ref=str(snapshot["resolved_commit"]))
    identity_after = _snapshot_identity(snapshot_after)
    counts_consistent = len(set(observed_counts)) == 1 and len(set(manifest_counts)) == 1
    fields_consistent = len(set(observed_field_counts)) == 1
    count_matches = counts_consistent and observed_counts[0] == manifest_counts[0]
    identity_unchanged = identity_before == identity_after
    passed = count_matches and fields_consistent and identity_unchanged
    return {
        **blocked,
        "status": "pass" if passed else "blocked",
        "real_input_status": "ready",
        "manifest_record_count": manifest_counts[0] if counts_consistent else None,
        "record_count": observed_counts[0] if counts_consistent else None,
        "field_count": observed_field_counts[0] if fields_consistent else None,
        "record_count_matches_manifest": count_matches,
        "elapsed_ms": _sample_summary(elapsed_samples),
        "peak_python_alloc_bytes": _sample_summary(peak_samples, decimals=0),
        "source_identity_after": identity_after,
        "source_mutation_performed": not identity_unchanged,
    }


def isolate_operational_sqlite(
    project_root: str | Path,
    *,
    data_home: str | Path | None = None,
    temp_root: str | Path | None = None,
) -> dict[str, Any]:
    repo_root = _repo_root(project_root)
    configured = str(os.environ.get("PFI_DATA_HOME", "")).strip()
    root = Path(data_home) if data_home is not None else Path(configured) if configured else Path.home() / ".pfi"
    root = root.expanduser().absolute()
    database = root / "private" / "operational" / "pfi.sqlite"
    base = {
        "schema": "PFIV025Phase23DatabaseBeforeAfterV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "2.3",
        "source_id": DATABASE_SOURCE_ID,
        "path_alias": DATABASE_ALIAS,
        "status": "source_missing",
        "isolation_mode": "ephemeral_0600_file_copy",
        "source_path_redacted": True,
        "source_bytes": None,
        "source_mode": None,
        "source_hash": None,
        "copy_hash": None,
        "copy_mode": None,
        "temp_directory_mode": None,
        "sqlite_quick_check": None,
        "known_table_count": None,
        "source_identity_before": None,
        "source_identity_after": None,
        "source_before_after_unchanged": None,
        "cleanup_complete": True,
        "row_values_emitted": 0,
        "table_names_emitted": 0,
        "source_mutation_performed": False,
        "private_values_included": False,
        "finder_used": False,
    }
    if _is_relative_to(root, repo_root):
        return {**base, "status": "blocked_unsafe_root"}
    chain = _path_chain_status(database)
    if chain != "ready":
        return {**base, "status": chain}
    sidecar_count = _sidecar_count(database)
    if sidecar_count:
        return {**base, "status": "blocked_sidecar_present"}
    before = _file_fingerprint(database)
    if before is None:
        return base
    header_mode = _sqlite_header_mode(database)
    if header_mode != "rollback_journal":
        return {**base, "status": "blocked_non_quiescent_database"}

    sandbox_dir: Path | None = None
    copy_path: Path | None = None
    report = dict(base)
    try:
        parent = Path(temp_root).expanduser().absolute() if temp_root is not None else None
        if parent is not None:
            parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        sandbox_dir = Path(tempfile.mkdtemp(prefix="pfi-v025-phase23-", dir=parent))
        os.chmod(sandbox_dir, 0o700)
        copy_path = sandbox_dir / "isolated.sqlite"
        _copy_read_only_source(database, copy_path)
        copy_fingerprint = _file_fingerprint(copy_path)
        if copy_fingerprint is None:
            raise OSError("ephemeral_copy_missing")
        quick_check, known_table_count = _probe_isolated_sqlite(copy_path)
        after = _file_fingerprint(database)
        unchanged = before == after and _sidecar_count(database) == 0
        source_hash = str(before["content_hash"])
        copy_hash = str(copy_fingerprint["content_hash"])
        passed = unchanged and source_hash == copy_hash and quick_check == "ok"
        report = {
            **base,
            "status": "pass" if passed else "blocked_integrity_mismatch",
            "source_bytes": before["size"],
            "source_mode": before["mode"],
            "source_hash": source_hash,
            "copy_hash": copy_hash,
            "copy_mode": copy_fingerprint["mode"],
            "temp_directory_mode": format(stat.S_IMODE(sandbox_dir.stat().st_mode), "04o"),
            "sqlite_quick_check": quick_check,
            "known_table_count": known_table_count,
            "source_identity_before": _fingerprint_identity(before),
            "source_identity_after": _fingerprint_identity(after),
            "source_before_after_unchanged": unchanged,
            "source_mutation_performed": not unchanged,
        }
    except (OSError, PermissionError, sqlite3.Error, ValueError):
        report = {**base, "status": "blocked_copy_or_integrity_check"}
    finally:
        if copy_path is not None:
            try:
                copy_path.unlink(missing_ok=True)
            except OSError:
                pass
        if sandbox_dir is not None:
            try:
                sandbox_dir.rmdir()
            except OSError:
                pass
        cleanup_complete = sandbox_dir is None or not sandbox_dir.exists()
        report["cleanup_complete"] = cleanup_complete
        if not cleanup_complete:
            report["status"] = "blocked_cleanup_incomplete"
    return report


def build_sandbox_attestation(
    snapshot: Mapping[str, Any],
    database_before_after: Mapping[str, Any],
) -> dict[str, Any]:
    passed = snapshot.get("status") == "ready" and database_before_after.get("status") == "pass"
    return {
        "schema": "PFIV025Phase23SafeSandboxAttestationV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "2.3",
        "status": "pass" if passed else "blocked",
        "git_object_snapshot": dict(snapshot),
        "database_before_after_ref": "PFI/reports/pfi_v025/stage_2/phase_2_3/database_before_after.json",
        "operational_sqlite_copy_status": database_before_after.get("status"),
        "database_source_hash": database_before_after.get("source_hash"),
        "database_copy_hash": database_before_after.get("copy_hash"),
        "database_source_before_after_unchanged": database_before_after.get("source_before_after_unchanged"),
        "cleanup_complete": database_before_after.get("cleanup_complete") is True,
        "source_mutation_performed": bool(database_before_after.get("source_mutation_performed")),
        "financial_fixture_fallback_used": False,
        "private_values_included": False,
        "finder_used": False,
    }


def build_no_fake_audit(module_path: str | Path) -> dict[str, Any]:
    path = Path(module_path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        str(node.module).split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    baseline = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "run_git_object_read_parse_baseline"
    )
    argument_names = {
        argument.arg
        for argument in (*baseline.args.posonlyargs, *baseline.args.args, *baseline.args.kwonlyargs)
    }
    injection_arguments = sorted(argument_names & _FORBIDDEN_BASELINE_ARGUMENTS)
    network_roots = sorted(imported_roots & _NETWORK_IMPORT_ROOTS)
    finder_markers = (
        "open -a finder",
        'tell application "finder"',
        "finder_activate",
        "finder_reveal",
    )
    source_mutation_symbols = {
        "os.replace",
        "os.rename",
        "os.utime",
        "shutil.move",
    }
    called_symbols = {
        _ast_call_path(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    source_mutation_capability = bool(called_symbols & source_mutation_symbols)
    finder_call_present = any(
        any(marker in ast.unparse(node).lower() for marker in finder_markers)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _ast_call_path(node.func) in {"subprocess.call", "subprocess.Popen", "subprocess.run"}
    )
    passed = (
        not injection_arguments
        and not network_roots
        and not finder_call_present
        and not source_mutation_capability
    )
    return {
        "schema": "PFIV025Phase23NoFakeAuditV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "2.3",
        "status": "pass" if passed else "fail",
        "audited_module": "PFI/src/pfi_v02/stage_v025_safe_sandbox.py",
        "baseline_function": "run_git_object_read_parse_baseline",
        "baseline_accepts_external_financial_records": bool(injection_arguments),
        "forbidden_injection_arguments": injection_arguments,
        "source_missing_behavior": "blocked_without_fallback",
        "financial_fixture_fallback_used": False,
        "network_capability_present": bool(network_roots),
        "network_import_roots": network_roots,
        "source_mutation_capability_present": source_mutation_capability,
        "temp_copy_write_is_ephemeral_destination_only": True,
        "finder_used": False,
        "private_values_included": False,
    }


def build_phase23_privacy_scan_report(project_root: str | Path, observed_at: str) -> str:
    return build_public_artifact_scan_report(
        project_root,
        observed_at,
        inputs=_PHASE23_PRIVACY_INPUTS,
        scanner_name="pfi-v025-phase23-public-artifact-scan-v1",
        scan_command=(
            "PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B -m pytest "
            "-p no:cacheprovider PFI/tests/test_v025_stage2_safe_sandbox.py "
            "-q -k tracked_no_fake_and_privacy_audits_are_deterministic"
        ),
    )


def _repo_root(project_root: str | Path) -> Path:
    candidate = Path(project_root).expanduser().absolute()
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=candidate,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return Path(completed.stdout.strip())


def _git_bytes(repo_root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout


def _git_text(repo_root: Path, *args: str) -> str:
    return _git_bytes(repo_root, *args).decode("utf-8").strip()


def _snapshot_identity(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "resolved_commit": snapshot.get("resolved_commit"),
        "tree_oid": snapshot.get("tree_oid"),
        "manifest_blob_oid": snapshot.get("manifest_blob_oid"),
        "transactions_blob_oid": snapshot.get("transactions_blob_oid"),
        "input_bytes": snapshot.get("input_bytes"),
    }


def _sample_summary(samples: list[int | float], *, decimals: int = 3) -> dict[str, int | float]:
    render = (lambda number: int(number)) if decimals == 0 else (lambda number: round(float(number), decimals))
    return {
        "min": render(min(samples)),
        "median": render(median(samples)),
        "max": render(max(samples)),
    }


def _path_chain_status(path: Path) -> str:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            return "source_missing"
        except PermissionError:
            return "permission_denied"
        if stat.S_ISLNK(info.st_mode):
            return "blocked_symlink"
    try:
        info = path.lstat()
    except FileNotFoundError:
        return "source_missing"
    except PermissionError:
        return "permission_denied"
    return "ready" if stat.S_ISREG(info.st_mode) else "blocked_non_regular_database"


def _sidecar_count(database: Path) -> int:
    prefix = database.name + "-"
    with os.scandir(database.parent) as entries:
        return sum(1 for entry in entries if entry.name.startswith(prefix))


def _file_fingerprint(path: Path) -> dict[str, Any] | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        return None
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "device": info.st_dev,
        "inode": info.st_ino,
        "size": info.st_size,
        "mode": format(stat.S_IMODE(info.st_mode), "04o"),
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
        "content_hash": "sha256:" + digest.hexdigest(),
    }


def _fingerprint_identity(fingerprint: Mapping[str, Any] | None) -> str | None:
    if fingerprint is None:
        return None
    raw = json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _sqlite_header_mode(path: Path) -> str:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        header = stream.read(20)
    if len(header) != 20 or header[:16] != b"SQLite format 3\x00":
        return "invalid"
    return "rollback_journal" if (header[18], header[19]) == (1, 1) else "wal" if 2 in {header[18], header[19]} else "invalid"


def _copy_read_only_source(source: Path, destination: Path) -> None:
    source_fd = os.open(source, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
    destination_fd = os.open(
        destination,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            view = memoryview(chunk)
            while view:
                written = os.write(destination_fd, view)
                view = view[written:]
        os.fsync(destination_fd)
    finally:
        os.close(source_fd)
        os.close(destination_fd)


def _probe_isolated_sqlite(path: Path) -> tuple[str, int]:
    uri = path.absolute().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=0, isolation_level=None)
    try:
        connection.enable_load_extension(False)
        connection.execute("PRAGMA query_only=ON")
        connection.set_authorizer(_sqlite_read_only_authorizer)
        row = connection.execute("PRAGMA quick_check").fetchone()
        quick_check = "ok" if row and str(row[0]) == "ok" else "not_ok"
        placeholders = ",".join("?" for _ in _KNOWN_DB_TABLES)
        known_table_count = int(
            connection.execute(
                f"SELECT COUNT(*) FROM sqlite_schema WHERE type='table' AND name IN ({placeholders})",
                _KNOWN_DB_TABLES,
            ).fetchone()[0]
        )
    finally:
        connection.close()
    return quick_check, known_table_count


def _sqlite_read_only_authorizer(
    action: int,
    argument_1: str | None,
    argument_2: str | None,
    database_name: str | None,
    trigger_name: str | None,
) -> int:
    del argument_2, database_name, trigger_name
    allowed = {
        getattr(sqlite3, "SQLITE_SELECT", -1),
        getattr(sqlite3, "SQLITE_READ", -1),
        getattr(sqlite3, "SQLITE_FUNCTION", -1),
    }
    if action in allowed:
        return sqlite3.SQLITE_OK
    if action == getattr(sqlite3, "SQLITE_PRAGMA", -2) and str(argument_1 or "").lower() == "quick_check":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _ast_call_path(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _ast_call_path(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""
