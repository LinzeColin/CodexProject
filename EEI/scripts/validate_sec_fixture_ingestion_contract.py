#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
A102_OUTPUT = ROOT / "artifacts/tests/a102/t703_sec_fixture_idempotent_upsert_contract.json"
A103_OUTPUT = ROOT / "artifacts/tests/a103/t703_sec_ingestion_report_contract.json"
CONTAINER_NAME = "eei-t703-postgres"
VOLUME_NAME = "eei-t703-postgres-data"
HOST = "127.0.0.1"
HOST_PORT = 55433
DATABASE_NAME = "eei_t703"
DATABASE_USER = "eei_t703"
DATABASE_PASSWORD = "eei-t703-local-only"
DATABASE_URL = (
    f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{HOST}:{HOST_PORT}/{DATABASE_NAME}"
)
PROTECTED_CONTAINERS = ("eei-postgres", "eei-worker")
REPORT_REQUIRED_FIELDS = (
    "checkpoint",
    "counts",
    "status",
    "error_class",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(
    command: list[str],
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
        env=env,
    )


def generated_at() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_commit() -> str:
    return run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()


def container_snapshot(name: str) -> dict[str, Any] | None:
    completed = run(["docker", "inspect", name], check=False)
    if completed.returncode != 0:
        return None
    payload = json.loads(completed.stdout)
    require(isinstance(payload, list) and len(payload) == 1, f"invalid inspect: {name}")
    container = payload[0]
    state = container.get("State") or {}
    health = state.get("Health") or {}
    config = container.get("Config") or {}
    return {
        "id": container.get("Id"),
        "name": str(container.get("Name") or "").lstrip("/"),
        "image": config.get("Image"),
        "state": state.get("Status"),
        "health": health.get("Status"),
        "started_at": state.get("StartedAt"),
    }


def protected_snapshots() -> dict[str, dict[str, Any]]:
    snapshots: dict[str, dict[str, Any]] = {}
    for name in PROTECTED_CONTAINERS:
        snapshot = container_snapshot(name)
        require(snapshot is not None, f"protected container missing: {name}")
        require(snapshot["state"] == "running", f"protected container not running: {name}")
        require(snapshot["health"] == "healthy", f"protected container not healthy: {name}")
        snapshots[name] = snapshot
    return snapshots


def protected_unchanged(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> bool:
    return all(
        before[name]["id"] == after[name]["id"]
        and before[name]["started_at"] == after[name]["started_at"]
        and after[name]["state"] == "running"
        and after[name]["health"] == "healthy"
        for name in PROTECTED_CONTAINERS
    )


def volume_exists(name: str) -> bool:
    return run(["docker", "volume", "inspect", name], check=False).returncode == 0


def port_available() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((HOST, HOST_PORT))
        except OSError:
            return False
    return True


def wait_for_health(timeout_seconds: float = 90.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        snapshot = container_snapshot(CONTAINER_NAME)
        if snapshot and snapshot["state"] == "running" and snapshot["health"] == "healthy":
            return snapshot
        time.sleep(0.5)
    logs = run(["docker", "logs", "--tail", "80", CONTAINER_NAME], check=False)
    raise RuntimeError(f"isolated PostgreSQL did not become healthy: {logs.stderr}")


def start_isolated_postgres() -> dict[str, Any]:
    require(container_snapshot(CONTAINER_NAME) is None, "isolated container already exists")
    require(not volume_exists(VOLUME_NAME), "isolated volume already exists")
    require(port_available(), f"isolated host port is unavailable: {HOST_PORT}")
    run(["docker", "volume", "create", VOLUME_NAME])
    run(
        [
            "docker",
            "run",
            "--detach",
            "--name",
            CONTAINER_NAME,
            "--publish",
            f"{HOST}:{HOST_PORT}:5432",
            "--volume",
            f"{VOLUME_NAME}:/var/lib/postgresql/data",
            "--env",
            f"POSTGRES_DB={DATABASE_NAME}",
            "--env",
            f"POSTGRES_USER={DATABASE_USER}",
            "--env",
            f"POSTGRES_PASSWORD={DATABASE_PASSWORD}",
            "--health-cmd",
            f"pg_isready -U {DATABASE_USER} -d {DATABASE_NAME}",
            "--health-interval",
            "1s",
            "--health-timeout",
            "3s",
            "--health-retries",
            "60",
            "postgres:16",
        ]
    )
    return wait_for_health()


def cleanup_isolated_postgres() -> dict[str, Any]:
    remove = run(["docker", "rm", "--force", CONTAINER_NAME], check=False)
    remove_volume = run(["docker", "volume", "rm", "--force", VOLUME_NAME], check=False)
    return {
        "container_remove_exit_code": remove.returncode,
        "volume_remove_exit_code": remove_volume.returncode,
        "container_absent": container_snapshot(CONTAINER_NAME) is None,
        "volume_absent": not volume_exists(VOLUME_NAME),
    }


def command_environment() -> dict[str, str]:
    env = dict(os.environ)
    env["DATABASE_URL"] = DATABASE_URL
    return env


def parse_json_stdout(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    payload = json.loads(completed.stdout)
    require(isinstance(payload, dict), "CLI report must be a JSON object")
    return payload


def run_loader(*, mode: str, database_write: bool) -> dict[str, Any]:
    command = [str(PYTHON), "scripts/load_sec_normalized_fixtures.py", "--mode", mode]
    if database_write:
        command.extend(
            [
                "--database-url",
                DATABASE_URL,
                "--allow-database-write",
            ]
        )
    return parse_json_stdout(run(command, env=command_environment()))


def database_counts() -> dict[str, Any]:
    with psycopg.connect(DATABASE_URL, connect_timeout=5) as connection:
        row = connection.execute(
            """
            SELECT
              (SELECT count(*) FROM sources WHERE code = %s),
              (SELECT count(*) FROM source_documents sd
                JOIN sources s ON s.id = sd.source_id WHERE s.code = %s),
              (SELECT count(*) FROM raw_source_snapshots rss
                JOIN source_documents sd ON sd.id = rss.source_document_id
                JOIN sources s ON s.id = sd.source_id WHERE s.code = %s),
              (SELECT count(*) FROM ingestion_runs ir
                JOIN sources s ON s.id = ir.source_id
                WHERE s.code = %s AND ir.connector_version = 'sec-fixture-ingestion-v1'),
              (SELECT count(*) FROM raw_source_snapshots rss
                JOIN source_documents sd ON sd.id = rss.source_document_id
                JOIN sources s ON s.id = sd.source_id
                WHERE s.code = %s AND rss.record_mode = 'fixture'),
              (SELECT count(DISTINCT rss.content_hash) FROM raw_source_snapshots rss
                JOIN source_documents sd ON sd.id = rss.source_document_id
                JOIN sources s ON s.id = sd.source_id WHERE s.code = %s)
            """,
            ("sec_edgar_synthetic_fixture",) * 6,
        ).fetchone()
        run_statuses = connection.execute(
            """
            SELECT status, count(*)
            FROM ingestion_runs ir
            JOIN sources s ON s.id = ir.source_id
            WHERE s.code = 'sec_edgar_synthetic_fixture'
            GROUP BY status ORDER BY status
            """
        ).fetchall()
    return {
        "sources": row[0],
        "source_documents": row[1],
        "raw_snapshots": row[2],
        "ingestion_runs": row[3],
        "fixture_mode_snapshots": row[4],
        "distinct_snapshot_hashes": row[5],
        "ingestion_run_statuses": {status: count for status, count in run_statuses},
    }


def validate_report_shape(report: dict[str, Any]) -> None:
    for field in REPORT_REQUIRED_FIELDS:
        require(field in report, f"ingestion report field missing: {field}")
    require(report.get("status") == "succeeded", "ingestion report must succeed")
    require(report.get("error_class") is None, "successful report error_class must be null")
    require(report.get("checkpoint", {}).get("stage") == "completed", "checkpoint drift")
    require(isinstance(report.get("counts"), dict), "report counts must be an object")
    release_scope = report.get("release_scope") or {}
    require(release_scope.get("fixture_only") is True, "fixture-only scope missing")
    require(release_scope.get("live_sec_request_performed") is False, "live request claim")
    require(release_scope.get("mvp_release_ready") is False, "release-ready claim")


def build_contracts() -> tuple[dict[str, Any], dict[str, Any]]:
    before = protected_snapshots()
    after: dict[str, dict[str, Any]] = {}
    cleanup: dict[str, Any] = {}
    isolated: dict[str, Any] | None = None
    failure: str | None = None
    first: dict[str, Any] = {}
    second: dict[str, Any] = {}
    dry_run: dict[str, Any] = {}
    db_counts: dict[str, Any] = {}
    migration_versions: list[str] = []
    try:
        isolated = start_isolated_postgres()
        migration_result = parse_json_stdout(
            run([str(PYTHON), "scripts/migrate.py", "upgrade"], env=command_environment())
        )
        migration_versions = list(migration_result.get("applied") or [])
        first = run_loader(mode="fixture", database_write=True)
        second = run_loader(mode="fixture", database_write=True)
        dry_run = run_loader(mode="dry-run", database_write=False)
        for report in (first, second, dry_run):
            validate_report_shape(report)
        require(first["counts"]["source_documents_inserted"] == 2, "first doc inserts")
        require(first["counts"]["raw_snapshots_inserted"] == 2, "first snapshot inserts")
        require(second["counts"]["source_documents_inserted"] == 0, "second doc inserts")
        require(second["counts"]["source_documents_reused"] == 2, "second doc reuse")
        require(second["counts"]["raw_snapshots_inserted"] == 0, "second snapshot inserts")
        require(second["counts"]["raw_snapshots_reused"] == 2, "second snapshot reuse")
        require(dry_run["database_write_performed"] is False, "dry-run wrote database")
        db_counts = database_counts()
        require(db_counts["sources"] == 1, "fixture source fixed point failed")
        require(db_counts["source_documents"] == 2, "source document fixed point failed")
        require(db_counts["raw_snapshots"] == 2, "snapshot fixed point failed")
        require(db_counts["ingestion_runs"] == 2, "dry-run created an ingestion run")
        require(db_counts["fixture_mode_snapshots"] == 2, "record_mode drift")
        require(db_counts["distinct_snapshot_hashes"] == 2, "content hash drift")
        require(db_counts["ingestion_run_statuses"] == {"succeeded": 2}, "run status drift")
    except (
        AssertionError,
        json.JSONDecodeError,
        OSError,
        psycopg.Error,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as exc:
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        cleanup = cleanup_isolated_postgres()
        try:
            after = protected_snapshots()
            cleanup["protected_containers_unchanged"] = protected_unchanged(before, after)
        except AssertionError as exc:
            cleanup["protected_containers_unchanged"] = False
            failure = failure or f"AssertionError: {exc}"

    cleanup_passed = (
        cleanup.get("container_absent") is True
        and cleanup.get("volume_absent") is True
        and cleanup.get("protected_containers_unchanged") is True
    )
    require(failure is None, failure or "T703 isolated probe failed")
    require(cleanup_passed, "T703 isolated resource cleanup failed")

    common = {
        "task_id": "T703",
        "generated_at": generated_at(),
        "source_commit": git_commit(),
        "status": "PASS",
        "isolated_postgresql": {
            "image": "postgres:16",
            "container": isolated,
            "host": HOST,
            "port": HOST_PORT,
            "migration_versions": migration_versions,
        },
        "protected_resources": {"before": before, "after": after},
        "cleanup": cleanup,
        "release_scope": {
            "fixture_only": True,
            "live_sec_request_performed": False,
            "active_a209_database_touched": False,
            "a202_closed_by_contract": False,
            "a209_closed_by_contract": False,
            "mvp_release_ready": False,
        },
    }
    a102 = {
        "schema_version": "eei-a102-sec-fixture-idempotent-upsert-contract-v1",
        "acceptance_ids": ["A102"],
        **common,
        "contract": {
            "execution_modes": ["fixture", "dry_run"],
            "database_write_requires_explicit_opt_in": True,
            "fixture_scheme_required": "fixture://sec/",
            "record_mode": "fixture",
            "content_hash_algorithm": "sha256",
            "idempotency_key_source_document": ["source_id", "external_id", "content_hash"],
            "idempotency_key_raw_snapshot": ["anchor_id", "content_hash"],
            "first_write_counts": first["counts"],
            "second_write_counts": second["counts"],
            "dry_run_counts": dry_run["counts"],
            "database_fixed_point": db_counts,
        },
        "test_evidence": [
            "tests/unit/test_sec_fixture_ingestion.py",
            "scripts/load_sec_normalized_fixtures.py",
            "isolated PostgreSQL 16 double-upsert probe",
        ],
    }
    a103 = {
        "schema_version": "eei-a103-sec-ingestion-report-contract-v1",
        "acceptance_ids": ["A103"],
        **common,
        "contract": {
            "required_fields": list(REPORT_REQUIRED_FIELDS),
            "status_values": ["succeeded", "failed"],
            "successful_error_class": None,
            "failed_error_class_is_exception_type": True,
            "checkpoint_includes": [
                "stage",
                "cik",
                "entity_name",
                "fixture_hashes",
                "connector_version",
            ],
            "counts_include": sorted(first["counts"]),
            "dry_run_database_write_performed": dry_run["database_write_performed"],
        },
        "sample_report": second,
        "test_evidence": [
            "tests/unit/test_sec_fixture_ingestion.py",
            "fixture mode success report",
            "dry-run success report",
            "unit failure report assertion",
        ],
    }
    return a102, a103


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"artifact must be an object: {path}")
    return payload


def validate_artifacts(a102: dict[str, Any], a103: dict[str, Any]) -> None:
    require(a102.get("status") == "PASS", "A102 status must be PASS")
    require(a102.get("task_id") == "T703", "A102 task mapping drift")
    require(a102.get("acceptance_ids") == ["A102"], "A102 acceptance mapping drift")
    contract = a102.get("contract") or {}
    require(contract.get("execution_modes") == ["fixture", "dry_run"], "mode drift")
    require(contract.get("database_write_requires_explicit_opt_in") is True, "write gate")
    fixed_point = contract.get("database_fixed_point") or {}
    require(fixed_point.get("source_documents") == 2, "A102 source document fixed point")
    require(fixed_point.get("raw_snapshots") == 2, "A102 snapshot fixed point")
    require(fixed_point.get("ingestion_runs") == 2, "A102 dry-run persistence drift")
    second = contract.get("second_write_counts") or {}
    require(second.get("source_documents_reused") == 2, "A102 doc reuse evidence")
    require(second.get("raw_snapshots_reused") == 2, "A102 snapshot reuse evidence")

    require(a103.get("status") == "PASS", "A103 status must be PASS")
    require(a103.get("task_id") == "T703", "A103 task mapping drift")
    require(a103.get("acceptance_ids") == ["A103"], "A103 acceptance mapping drift")
    report_contract = a103.get("contract") or {}
    require(
        report_contract.get("required_fields") == list(REPORT_REQUIRED_FIELDS),
        "A103 required report fields drift",
    )
    require(
        report_contract.get("failed_error_class_is_exception_type") is True,
        "A103 failure classification drift",
    )
    sample_report = a103.get("sample_report") or {}
    validate_report_shape(sample_report)

    for artifact in (a102, a103):
        release_scope = artifact.get("release_scope") or {}
        require(release_scope.get("fixture_only") is True, "fixture-only evidence drift")
        require(
            release_scope.get("active_a209_database_touched") is False,
            "A209 database isolation drift",
        )
        require(release_scope.get("mvp_release_ready") is False, "release-ready claim")
        cleanup = artifact.get("cleanup") or {}
        require(cleanup.get("container_absent") is True, "isolated container cleanup missing")
        require(cleanup.get("volume_absent") is True, "isolated volume cleanup missing")
        require(
            cleanup.get("protected_containers_unchanged") is True,
            "protected container identity changed",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate T703 SEC fixture ingestion contracts.")
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args()
    if args.command == "generate":
        a102, a103 = build_contracts()
        write_json(A102_OUTPUT, a102)
        write_json(A103_OUTPUT, a103)
    else:
        a102, a103 = read_json(A102_OUTPUT), read_json(A103_OUTPUT)
    validate_artifacts(a102, a103)
    print(
        json.dumps(
            {
                "valid": True,
                "artifacts": [
                    A102_OUTPUT.relative_to(ROOT).as_posix(),
                    A103_OUTPUT.relative_to(ROOT).as_posix(),
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        raise SystemExit(1) from exc
