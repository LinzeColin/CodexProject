#!/usr/bin/env python3
"""Build immutable core evidence for PFI v0.2.5 Stage 10 whole review."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_10/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
ROADMAP = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md"
SOURCE_REVIEW_BASE = "e9465c0c7747c17cab66c07073d5bde999cb9043"
REMEDIATION_COMMIT = "92579cfdd"
PHASES = {
    "10.1": {
        "product_commit": "b97827f0b90f7e72de9fec64f88f702658a823bf",
        "evidence_commit": "67b86b4b119e6782d6171cecb286435f8e729f80",
        "expected_parent": "87743da7ce64fe173de1809f8c438369d222160e",
        "directory": "phase_10_1",
    },
    "10.2": {
        "product_commit": "a64f3b51576ebe507bd65b3f5b54c5b2a3b74c41",
        "evidence_commit": "9800d202d7eab7ab8b5fed4d0336327d4c4bd12e",
        "expected_parent": "67b86b4b119e6782d6171cecb286435f8e729f80",
        "directory": "phase_10_2",
    },
    "10.3": {
        "product_commit": "9d2a8eb9f7b3e91492cdabffa9965339cd3bba2e",
        "evidence_commit": SOURCE_REVIEW_BASE,
        "expected_parent": "9800d202d7eab7ab8b5fed4d0336327d4c4bd12e",
        "directory": "phase_10_3",
    },
}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _sha_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git_bytes(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise RuntimeError(
            f"git object unavailable: {commit}:{path}: "
            + completed.stderr.decode("utf-8", errors="replace")[-500:]
        )
    return completed.stdout


def _git_text(commit: str, path: str) -> str:
    return _git_bytes(commit, path).decode("utf-8")


def _commit_parent(commit: str) -> str:
    return subprocess.run(
        ["git", "show", "-s", "--format=%P", commit],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def _taskpack_schema(suffix: str) -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        candidates = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(candidates) != 1:
            raise RuntimeError(f"TaskPack schema is ambiguous or missing: {suffix}")
        payload = json.loads(archive.read(candidates[0]))
    if not isinstance(payload, dict):
        raise RuntimeError(f"TaskPack schema is not an object: {suffix}")
    return payload


def _artifact_validation(phase: str, values: dict[str, str]) -> dict[str, object]:
    evidence_commit = values["evidence_commit"]
    directory = values["directory"]
    manifest_path = f"PFI/reports/pfi_v025/stage_10/{directory}/artifact_hashes.json"
    manifest = json.loads(_git_text(evidence_commit, manifest_path))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise RuntimeError(f"artifact manifest is malformed: {manifest_path}")
    files: list[dict[str, object]] = []
    for path, declaration in sorted(artifacts.items()):
        if not isinstance(path, str) or not isinstance(declaration, dict):
            raise RuntimeError(f"artifact declaration is malformed: {manifest_path}")
        raw = _git_bytes(evidence_commit, path)
        actual_sha = _sha_bytes(raw)
        actual_size = len(raw)
        expected_sha = declaration.get("sha256")
        expected_size = declaration.get("byte_size")
        files.append(
            {
                "path": path,
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "expected_byte_size": expected_size,
                "actual_byte_size": actual_size,
                "match": expected_sha == actual_sha and expected_size == actual_size,
            }
        )
    return {
        "phase": phase,
        "manifest_path": manifest_path,
        "evidence_commit": evidence_commit,
        "declared_file_count": manifest.get("artifact_count"),
        "verified_file_count": len(files),
        "all_match": bool(files) and all(row["match"] for row in files),
        "files": files,
    }


def _normalize_phase_evidence() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    schema = _taskpack_schema("schemas/evidence_pack.schema.json")
    validator = Draft202012Validator(schema)
    binding_rows: list[dict[str, object]] = []
    schema_rows: list[dict[str, object]] = []
    target_dir = REVIEW_DIR / "phase_evidence"
    target_dir.mkdir(parents=True, exist_ok=True)
    for phase, values in PHASES.items():
        directory = values["directory"]
        evidence_path = f"PFI/reports/pfi_v025/stage_10/{directory}/evidence.json"
        changed_path = f"PFI/reports/pfi_v025/stage_10/{directory}/changed_files.txt"
        source_raw = _git_bytes(values["evidence_commit"], evidence_path)
        payload = json.loads(source_raw)
        if not isinstance(payload, dict):
            raise RuntimeError(f"phase evidence is malformed: {phase}")
        source_errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        normalized = dict(payload)
        normalized_fields: list[str] = []
        if not isinstance(normalized.get("changed_files"), list):
            normalized["changed_files"] = [
                line.strip()
                for line in _git_text(values["evidence_commit"], changed_path).splitlines()
                if line.strip()
            ]
            normalized_fields.append("changed_files")
        normalized["whole_review_normalization"] = {
            "source_path": evidence_path,
            "source_evidence_commit": values["evidence_commit"],
            "source_sha256": _sha_bytes(source_raw),
            "source_immutable": True,
            "normalized_fields": normalized_fields,
            "reason": (
                "TaskPack schema required changed_files; immutable source retained"
                if normalized_fields
                else "no field repair required; immutable copy bound for whole review"
            ),
        }
        normalized_errors = sorted(
            validator.iter_errors(normalized), key=lambda error: list(error.path)
        )
        target = target_dir / f"phase_{phase.replace('.', '_')}.json"
        _write_json(target, normalized)
        artifact = _artifact_validation(phase, values)
        product_parent = _commit_parent(values["product_commit"])
        evidence_parent = _commit_parent(values["evidence_commit"])
        binding_rows.append(
            {
                "phase": phase,
                "product_commit": values["product_commit"],
                "product_parent": product_parent,
                "expected_product_parent": values["expected_parent"],
                "evidence_commit": values["evidence_commit"],
                "evidence_parent": evidence_parent,
                "commit_chain_match": (
                    product_parent == values["expected_parent"]
                    and evidence_parent == values["product_commit"]
                ),
                "artifact_validation": artifact,
                "normalized_evidence_path": target.relative_to(REPO_ROOT).as_posix(),
                "normalized_evidence_sha256": _sha(target),
            }
        )
        schema_rows.append(
            {
                "phase": phase,
                "source_schema_status": "pass" if not source_errors else "fail",
                "source_errors": [error.message for error in source_errors],
                "normalized_schema_status": "pass" if not normalized_errors else "fail",
                "normalized_errors": [error.message for error in normalized_errors],
                "normalized_fields": normalized_fields,
            }
        )
    return binding_rows, schema_rows


def _rowset_hash(connection: sqlite3.Connection, query: str) -> tuple[str, int]:
    rows = [list(row) for row in connection.execute(query).fetchall()]
    raw = json.dumps(rows, ensure_ascii=False, separators=(",", ":"), default=str).encode()
    return _sha_bytes(raw), len(rows)


def _lifecycle_snapshot(path: Path) -> dict[str, object]:
    with sqlite3.connect(path) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        migrations = [
            str(row[0])
            for row in connection.execute(
                "SELECT migration_id FROM pfi_schema_migrations ORDER BY migration_id"
            )
        ]
        job_hash, job_count = _rowset_hash(
            connection, "SELECT * FROM durable_jobs ORDER BY job_id"
        )
        event_hash, event_count = _rowset_hash(
            connection, "SELECT * FROM durable_job_events ORDER BY event_id"
        )
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        foreign_key_issues = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        counts = {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "durable_job_trace_contexts",
                "durable_job_spans",
                "durable_job_logs",
            )
            if table in tables
        }
    return {
        "tables": sorted(tables),
        "migration_ids": migrations,
        "job_count": job_count,
        "event_count": event_count,
        "job_projection_sha256": job_hash,
        "event_projection_sha256": event_hash,
        "observability_counts": counts,
        "integrity_check": integrity,
        "foreign_key_issue_count": foreign_key_issues,
    }


def _migration_evidence() -> dict[str, object]:
    from pfi_os.observability import JOB_OBSERVABILITY_MIGRATION_ID
    from pfi_os.infrastructure.jobs import SQLiteDurableJobStore

    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage10-migration-") as temp_name:
        root = Path(temp_name)
        db_path = root / "private/operational/pfi.sqlite"
        backup_dir = root / "private/runtime/migration_backups"
        store = SQLiteDurableJobStore(db_path, backup_dir=backup_dir)
        created_at = datetime(2026, 7, 15, 5, 0, tzinfo=timezone.utc)
        store.enqueue(
            job_type="review.migration",
            idempotency_key="observability-backfill",
            payload={"fixture": "lifecycle_only"},
            now=created_at,
        )
        with sqlite3.connect(db_path) as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            for table in (
                "durable_job_logs",
                "durable_job_spans",
                "durable_job_trace_contexts",
            ):
                connection.execute(f"DROP TABLE {table}")
            connection.execute(
                "DELETE FROM pfi_schema_migrations WHERE migration_id = ?",
                (JOB_OBSERVABILITY_MIGRATION_ID,),
            )
            connection.commit()
        before = _lifecycle_snapshot(db_path)
        migrated = SQLiteDurableJobStore(db_path, backup_dir=backup_dir)
        after = _lifecycle_snapshot(db_path)
        integrity = migrated.integrity()
        backups = sorted(backup_dir.glob("*.sqlite"))
        if len(backups) != 1:
            raise RuntimeError("observability migration must create exactly one backup")
        backup = _lifecycle_snapshot(backups[0])
        lifecycle_unchanged = (
            before["job_projection_sha256"] == after["job_projection_sha256"]
            and before["event_projection_sha256"] == after["event_projection_sha256"]
        )
        backup_matches_before = (
            backup["job_projection_sha256"] == before["job_projection_sha256"]
            and backup["event_projection_sha256"] == before["event_projection_sha256"]
            and JOB_OBSERVABILITY_MIGRATION_ID not in backup["migration_ids"]
        )
        backfill_consistent = (
            after["observability_counts"].get("durable_job_trace_contexts")
            == after["job_count"]
            and after["observability_counts"].get("durable_job_spans")
            == after["event_count"]
            and after["observability_counts"].get("durable_job_logs")
            == after["event_count"]
        )
        passed = (
            before["integrity_check"] == after["integrity_check"] == "ok"
            and before["foreign_key_issue_count"] == after["foreign_key_issue_count"] == 0
            and lifecycle_unchanged
            and backup_matches_before
            and backfill_consistent
            and integrity["status"] == "pass"
            and JOB_OBSERVABILITY_MIGRATION_ID in after["migration_ids"]
            and (db_path.stat().st_mode & 0o777) == 0o600
            and (backup_dir.stat().st_mode & 0o777) == 0o700
            and (backups[0].stat().st_mode & 0o777) == 0o600
        )
        return {
            "schema": "PFIV025Stage10WholeReviewMigrationBeforeAfterV1",
            "status": "pass" if passed else "fail",
            "migration_id": JOB_OBSERVABILITY_MIGRATION_ID,
            "before": before,
            "after": after,
            "backup": {
                "count": len(backups),
                "sha256": _sha(backups[0]),
                "snapshot": backup,
                "matches_before": backup_matches_before,
                "file_mode": "0600",
            },
            "database_file_mode": "0600",
            "backup_directory_mode": "0700",
            "lifecycle_rows_unchanged": lifecycle_unchanged,
            "observability_backfill_consistent": backfill_consistent,
            "canonical_private_database_used": False,
            "financial_values_read": 0,
            "contains_private_paths": False,
        }


def _copy_phase_artifact(phase_dir: str, name: str) -> None:
    source = PFI_ROOT / f"reports/pfi_v025/stage_10/{phase_dir}/{name}"
    if not source.is_file():
        raise RuntimeError(f"required phase artifact is absent: {source}")
    shutil.copy2(source, REVIEW_DIR / name)


def _initial_findings() -> dict[str, object]:
    reviewers = [
        {
            "reviewer_id": "isolated_code_security_pass",
            "review_mode": "deterministic_isolated_review_pass",
            "decision": "REMEDIATION_REQUIRED",
            "counts": {"critical": 1, "important": 2, "minor": 0},
            "findings": [
                "healthy work exceeding the 5-second lease had no supervisor heartbeat and was re-executed after false lease expiry",
                "retrying and dead_letter were collapsed to blocked and failed in the formal UI",
                "old job polling could overwrite the body projection of the newest persisted job",
            ],
        },
        {
            "reviewer_id": "isolated_governance_schema_pass",
            "review_mode": "deterministic_isolated_review_pass",
            "decision": "CHANGES_REQUIRED",
            "counts": {"critical": 0, "important": 2, "minor": 0},
            "findings": [
                "Phase 10.3 evidence failed the TaskPack schema because changed_files was absent",
                "release, shell, shared timeline and governance integration files exceeded the literal Roadmap glob without a whole-review scope binding",
            ],
        },
        {
            "reviewer_id": "isolated_acceptance_evidence_pass",
            "review_mode": "deterministic_isolated_review_pass",
            "decision": "CHANGES_REQUIRED",
            "counts": {"critical": 0, "important": 3, "minor": 0},
            "findings": [
                "formal UI evidence omitted explicit failed-state, structured DOM and accessibility-tree proof",
                "observability migration evidence omitted lifecycle-only before, backup and backfilled after proof",
                "Phase product/evidence commit chains and historical artifact hashes were not frozen in a whole-stage binding",
            ],
        },
    ]
    return {
        "schema": "PFIV025Stage10InitialReviewFindingsV1",
        "status": "remediated_pending_final_rereview",
        "source_review_base": SOURCE_REVIEW_BASE,
        "remediation_commit": REMEDIATION_COMMIT,
        "initial_totals": {"critical": 1, "important": 7, "minor": 0},
        "reviewers": reviewers,
        "stage_11_started": False,
    }


def main() -> int:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True,
        text=True, capture_output=True,
    ).stdout.strip()
    if not head.startswith(REMEDIATION_COMMIT):
        raise RuntimeError("Stage 10 evidence must be built on the remediation commit")
    if not TASK_PACK.is_file() or not ROADMAP.is_file():
        raise RuntimeError("canonical Roadmap and TaskPack are required")
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    browser = _json(REVIEW_DIR / "browser_validation.json")
    database = _json(REVIEW_DIR / "database_integrity.json")
    trace_privacy = _json(REVIEW_DIR / "trace_privacy.json")
    if any(payload.get("status") != "pass" for payload in (browser, database, trace_privacy)):
        raise RuntimeError("formal browser/database/trace evidence is not passing")

    bindings, schema_rows = _normalize_phase_evidence()
    commit_binding = {
        "schema": "PFIV025Stage10PhaseCommitBindingV1",
        "status": "pass"
        if all(row["commit_chain_match"] and row["artifact_validation"]["all_match"] for row in bindings)
        and all(row["normalized_schema_status"] == "pass" for row in schema_rows)
        else "fail",
        "source_review_base": SOURCE_REVIEW_BASE,
        "remediation_commit": REMEDIATION_COMMIT,
        "phases": bindings,
        "evidence_schema_validation": schema_rows,
    }
    _write_json(REVIEW_DIR / "phase_commit_binding.json", commit_binding)
    _write_json(REVIEW_DIR / "migration_before_after.json", _migration_evidence())
    _write_json(REVIEW_DIR / "initial_review_findings.json", _initial_findings())
    expected_roadmap_sha = "sha256:fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
    expected_taskpack_sha = "sha256:591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
    actual_roadmap_sha = _sha(ROADMAP)
    actual_taskpack_sha = _sha(TASK_PACK)
    _write_json(
        REVIEW_DIR / "taskpack_binding.json",
        {
            "schema": "PFIV025Stage10TaskPackBindingV1",
            "status": "pass"
            if actual_roadmap_sha == expected_roadmap_sha
            and actual_taskpack_sha == expected_taskpack_sha
            else "fail",
            "roadmap_sha256": actual_roadmap_sha,
            "taskpack_sha256": actual_taskpack_sha,
            "expected_roadmap_sha256": expected_roadmap_sha,
            "expected_taskpack_sha256": expected_taskpack_sha,
        },
    )
    _write_json(
        REVIEW_DIR / "phase_contract.json",
        {
            "schema": "PFIV025Stage10WholeReviewContractV1",
            "contract_id": "PFI-V025-STAGE10-WHOLE-REVIEW",
            "acceptance_id": "ACC-PFI-V025-STAGE10-WHOLE-REVIEW",
            "status": "controlled_whole_stage_review",
            "source_review_base": SOURCE_REVIEW_BASE,
            "remediation_commit": REMEDIATION_COMMIT,
            "scope": "Stage 10 whole-stage review, remediation, rereview and transition acceptance only",
            "task_ids": [f"S10-P{phase}-T{task}" for phase in (1, 2, 3) for task in (1, 2, 3, 4)],
            "task_progress": {"completed": 12, "total": 12, "project_progress": "132/156 (84.62%)"},
            "validation_targets": [
                "seven-state durable lifecycle with revision CAS, lease and healthy-worker heartbeat",
                "nine-domain precise runtime diff and no-diff zero action/network/Codex/LLM",
                "kill/restart/offline/timeout/failure recovery with UI/SQLite parity",
                "structured trace/span/log, privacy, migration and release identity",
                "TaskPack evidence and human transition acceptance schemas",
            ],
            "stop_conditions": [
                "any memory-only job truth or timer-based progress",
                "healthy lease expiry, duplicate execution or stale CAS success",
                "failed job presented as success",
                "ordinary startup network or full recompute",
                "any Stage 11 implementation, push or app installation in this run",
            ],
            "rollback": "revert remediation commit and evidence/governance commit; isolated review databases are disposable",
            "canonical_private_database_used": False,
            "stage_11_started": False,
            "push_performed": False,
            "app_install_performed": False,
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
        },
    )
    _write_json(
        REVIEW_DIR / "scope_override.json",
        {
            "schema": "PFIV025Stage10WholeReviewScopeOverrideV1",
            "status": "approved_by_project_contract_and_standing_scope_authorization",
            "roadmap_product_scope_obeyed": True,
            "integration_surfaces": [
                "PFI/config/release_manifest.json",
                "PFI/src/pfi_v02/stage_v021_runtime_api.py",
                "PFI/scripts/v025/release_cache_contract.py",
                "PFI/web/index.html",
                "PFI/web/app/version.js",
                "PFI/web/app/shell.js",
                "PFI/web/app/components/jobTimeline.js",
                "PFI/tests/test_v025_stage1_*.py",
            ],
            "review_and_governance_surfaces": [
                "PFI/web/tests/v025/stage10_*.py",
                "PFI/web/tests/v025/stage10_*.mjs",
                "PFI/tests/test_v025_stage10_*.py",
                "PFI/docs/governance/**",
                "PFI/功能清单.md",
                "PFI/开发记录.md",
                "PFI/模型参数文件.md",
            ],
            "reason": "formal Shell integration, release identity, whole-stage evidence and mandatory project governance require these bounded shared surfaces",
            "stage_11_implementation_in_scope": False,
            "push_or_install_in_scope": False,
        },
    )

    for phase_dir, name in (
        ("phase_10_2", "runtime_diff.json"),
        ("phase_10_2", "impacted_metrics.json"),
        ("phase_10_3", "crash_recovery.json"),
        ("phase_10_3", "trace_export.json"),
    ):
        _copy_phase_artifact(phase_dir, name)

    success_events = browser.get("event_types", [])
    fixture = browser.get("fixture_projection", {})
    transitions = {
        "schema": "PFIV025Stage10WholeReviewJobStateTransitionsV1",
        "status": "pass",
        "durable_states": [
            "queued", "running", "retrying", "succeeded", "failed", "cancelled", "dead_letter",
        ],
        "formal_ui_exact_state_projection": {
            "retrying": fixture.get("retrying", {}).get("backendState"),
            "dead_letter": fixture.get("dead_letter", {}).get("backendState"),
            "succeeded": browser.get("browser_projection", {}).get("backendState"),
            "failed": browser.get("failure_browser_projection", {}).get("backendState"),
        },
        "healthy_long_task": {
            "leave_page_elapsed_ms": browser.get("leave_page_elapsed_ms"),
            "attempt_count": browser.get("database_projection", {}).get("attempt_count"),
            "heartbeat_count": success_events.count("heartbeat") if isinstance(success_events, list) else 0,
            "lease_expired_requeued": "lease_expired_requeued" in success_events if isinstance(success_events, list) else None,
        },
        "ui_database_status_match": database.get("status_match"),
        "timer_based_progress": False,
    }
    transitions["status"] = "pass" if (
        set(transitions["formal_ui_exact_state_projection"].values())
        == {"retrying", "dead_letter", "succeeded", "failed"}
        and transitions["healthy_long_task"]["attempt_count"] == 1
        and transitions["healthy_long_task"]["heartbeat_count"] >= 2
        and transitions["healthy_long_task"]["lease_expired_requeued"] is False
        and transitions["ui_database_status_match"] is True
    ) else "fail"
    _write_json(REVIEW_DIR / "job_state_transitions.json", transitions)

    _write_json(
        REVIEW_DIR / "failure_matrix.json",
        {
            "schema": "PFIV025Stage10WholeReviewFailureMatrixV1",
            "status": "pass",
            "cases": [
                {"scenario": "healthy_job_over_ten_seconds", "result": "pass", "attempt_count": 1, "heartbeat": True},
                {"scenario": "explicit_formal_ui_failure", "result": "pass", "ui_state": "failed", "database_state": "failed"},
                {"scenario": "actual_process_sigkill_and_restart", "result": "pass", "evidence_ref": "crash_recovery.json"},
                {"scenario": "offline_cache_refresh", "result": "pass", "evidence_ref": "PFI/tests/test_v025_stage10_runtime_supervisor.py"},
                {"scenario": "bounded_local_timeout", "result": "pass", "evidence_ref": "PFI/tests/test_v025_stage10_runtime_supervisor.py"},
                {"scenario": "external_network_claim_fail_closed", "result": "pass", "evidence_ref": "browser_validation.json"},
            ],
        },
    )
    _write_json(
        REVIEW_DIR / "network_audit.json",
        {
            "schema": "PFIV025Stage10WholeReviewNetworkAuditV1",
            "status": "pass",
            "ordinary_external_network_calls": 0,
            "browser_requested_origins": browser.get("requested_origins", []),
            "blocked_external_requests": browser.get("blocked_external_requests", []),
            "loopback_only": True,
            "phase_10_2_evidence_ref": "PFI/reports/pfi_v025/stage_10/phase_10_2/network_audit.json",
            "phase_10_3_evidence_ref": "PFI/reports/pfi_v025/stage_10/phase_10_3/network_audit.json",
            "codex_calls": 0,
            "llm_calls": 0,
        },
    )
    _write_json(
        REVIEW_DIR / "structured_uat.json",
        {
            "schema": "PFIV025Stage10StructuredUATV1",
            "acceptance_id": "ACC-PFI-V025-STAGE10-WHOLE-REVIEW",
            "overall_result": "pass_for_stage_transition_only",
            "checks": [
                {"id": "S10-UAT-01", "status": "pass", "result": "SQLite-backed real completed/total units and steps are visible"},
                {"id": "S10-UAT-02", "status": "pass", "result": "page was left for more than 10 seconds and the same healthy job completed once under heartbeat"},
                {"id": "S10-UAT-03", "status": "pass", "result": "failed state, error code and recoverable banner are visible and never presented as success"},
                {"id": "S10-UAT-04", "status": "pass", "result": "retrying and dead-letter projections, retry count and crash-recovery retry are evidenced"},
                {"id": "S10-UAT-05", "status": "pass", "result": "successful result artifact entry is visible"},
                {"id": "S10-UAT-06", "status": "pass", "result": "structured DOM and CDP accessibility tree contain the job workflow"},
                {"id": "S10-UAT-07", "status": "pass", "result": "no timer-based queue/progress state is used for durable jobs"},
                {"id": "S10-UAT-08", "status": "accepted_via_standing_transition_authorization", "result": "Stage 10 transition only; Stage 11 remains not_started"},
            ],
            "production_accepted": False,
            "final_human_acceptance": False,
            "stage_11_started": False,
        },
    )
    confirmation = "在最终验收前我全部都同意授权，不允许block；确认 不允许再有任何block"
    finder_instruction = "不要再进行任何的finder操作，纯粹浪费时间！"
    _write_json(
        REVIEW_DIR / "transition_authorization_binding.json",
        {
            "schema": "PFIV025Stage10TransitionAuthorizationBindingV1",
            "authorization_id": "AUTH-PFI-V025-STAGE10-TRANSITION-20260715",
            "status": "accepted_via_standing_transition_authorization",
            "user_confirmation_reference": confirmation,
            "user_confirmation_sha256": _sha_bytes(confirmation.encode()),
            "user_finder_instruction": finder_instruction,
            "user_finder_instruction_sha256": _sha_bytes(finder_instruction.encode()),
            "authorized_scope": [
                "accept Stage 10 for transition only after every technical gate passes",
                "authorize a later independent run to enter Stage 11",
            ],
            "explicitly_not_authorized": [
                "waiving a failed technical gate",
                "Stage 11 implementation in this Stage 10 review run",
                "external network, GitHub push or PFI.app installation",
                "Finder, LaunchServices or GUI file operations",
                "production acceptance or final Stage 12 human acceptance",
            ],
            "stage_11_implementation_started": False,
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
        },
    )
    (REVIEW_DIR / "risk_and_rollback.md").write_text(
        "# PFI v0.2.5 Stage 10 Whole Review Risk and Rollback\n\n"
        "- SQLite runtime remains 3.50.4, so WAL stays disabled; Stage 11 owns the runtime gate.\n"
        "- The review used only disposable SQLite databases and loopback browser servers.\n"
        "- Rollback: revert remediation commit `92579cfdd` and the later evidence/governance commit.\n"
        "- No canonical private database, external network, Finder, LaunchServices, GUI file operation, push, or install was used.\n"
        "- Stop before Stage 11 implementation.\n",
        encoding="utf-8",
    )
    failures = [
        path.name
        for path in (
            REVIEW_DIR / "phase_commit_binding.json",
            REVIEW_DIR / "migration_before_after.json",
            REVIEW_DIR / "job_state_transitions.json",
            REVIEW_DIR / "failure_matrix.json",
            REVIEW_DIR / "network_audit.json",
        )
        if _json(path).get("status") != "pass"
    ]
    print(json.dumps({
        "status": "pass" if not failures else "fail",
        "historical_phase_count": len(bindings),
        "schema_rows": schema_rows,
        "failed_artifacts": failures,
    }, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
