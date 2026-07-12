#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = ROOT / "docker-compose.yml"
OUTPUT_PATH = Path("artifacts/tests/a005/t101_postgres_compose_clean_environment.json")
PROJECT_NAME = "eei-a005-t101"
CONTAINER_NAME = "eei-a005-postgres"
VOLUME_NAME = "eei-a005-t101-postgres-data"
HOST = "127.0.0.1"
HOST_PORT = 55432
PROTECTED_CONTAINERS = ("eei-postgres", "eei-worker")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def git_commit() -> str:
    return run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()


def container_snapshot(name: str) -> dict[str, Any] | None:
    completed = run(["docker", "inspect", name], check=False)
    if completed.returncode != 0:
        return None
    payload = json.loads(completed.stdout)
    require(isinstance(payload, list) and len(payload) == 1, f"invalid inspect payload: {name}")
    container = payload[0]
    state = container.get("State") or {}
    health = state.get("Health") or {}
    config = container.get("Config") or {}
    labels = config.get("Labels") or {}
    return {
        "id": container.get("Id"),
        "name": str(container.get("Name") or "").lstrip("/"),
        "image": config.get("Image"),
        "state": state.get("Status"),
        "health": health.get("Status"),
        "started_at": state.get("StartedAt"),
        "compose_project": labels.get("com.docker.compose.project"),
        "compose_service": labels.get("com.docker.compose.service"),
    }


def protected_snapshots() -> dict[str, dict[str, Any]]:
    snapshots: dict[str, dict[str, Any]] = {}
    for name in PROTECTED_CONTAINERS:
        snapshot = container_snapshot(name)
        require(snapshot is not None, f"protected container is missing: {name}")
        require(snapshot["state"] == "running", f"protected container is not running: {name}")
        require(snapshot["health"] == "healthy", f"protected container is not healthy: {name}")
        snapshots[name] = snapshot
    return snapshots


def protected_unchanged(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
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


def project_networks() -> list[str]:
    completed = run(
        [
            "docker",
            "network",
            "ls",
            "--filter",
            f"label=com.docker.compose.project={PROJECT_NAME}",
            "--format",
            "{{.Name}}",
        ]
    )
    return [line for line in completed.stdout.splitlines() if line]


def port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def compose_override() -> str:
    return f"""services:
  postgres:
    container_name: {CONTAINER_NAME}
    ports: !override
      - \"{HOST}:{HOST_PORT}:5432\"
    volumes: !override
      - a005-postgres-data:/var/lib/postgresql/data

volumes:
  a005-postgres-data:
    name: {VOLUME_NAME}
"""


def validate_compose_config(config: dict[str, Any]) -> dict[str, Any]:
    services = config.get("services") or {}
    postgres = services.get("postgres") or {}
    require(postgres.get("container_name") == CONTAINER_NAME, "isolated container name mismatch")

    ports = postgres.get("ports") or []
    published_ports = {int(item["published"]) for item in ports}
    require(published_ports == {HOST_PORT}, "isolated host port mismatch")
    require(all(item.get("host_ip") == HOST for item in ports), "isolated bind host mismatch")

    mounts = postgres.get("volumes") or []
    volume_sources = {item.get("source") for item in mounts if item.get("type") == "volume"}
    require(volume_sources == {"a005-postgres-data"}, "isolated volume mount mismatch")
    volume_config = (config.get("volumes") or {}).get("a005-postgres-data") or {}
    require(volume_config.get("name") == VOLUME_NAME, "isolated volume name mismatch")
    require("healthcheck" in postgres, "postgres healthcheck missing from merged config")
    return {
        "project_name": PROJECT_NAME,
        "container_name": CONTAINER_NAME,
        "host": HOST,
        "host_port": HOST_PORT,
        "container_port": 5432,
        "volume_name": VOLUME_NAME,
        "healthcheck_present": True,
    }


def compose_command(override_path: Path) -> list[str]:
    return [
        "docker",
        "compose",
        "--project-name",
        PROJECT_NAME,
        "-f",
        str(COMPOSE_PATH),
        "-f",
        str(override_path),
    ]


def postgres_identity() -> dict[str, Any]:
    with psycopg.connect(
        host=HOST,
        port=HOST_PORT,
        dbname="eei",
        user="eei",
        password="change-me-local-only",
        connect_timeout=5,
    ) as connection:
        row = connection.execute(
            "SELECT current_database(), current_user, current_setting('server_version_num'), 1"
        ).fetchone()
    require(row is not None, "PostgreSQL identity query returned no row")
    database, user, server_version_num, probe = row
    require(database == "eei", "unexpected PostgreSQL database")
    require(user == "eei", "unexpected PostgreSQL user")
    require(str(server_version_num).startswith("16"), "PostgreSQL 16 is required")
    require(probe == 1, "PostgreSQL SELECT 1 probe failed")
    return {
        "database": database,
        "user": user,
        "server_version_num": server_version_num,
        "select_one": probe,
    }


def execute_clean_environment_probe() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "eei-a005-postgres-clean-environment-v1",
        "status": "FAIL",
        "task_id": "T101",
        "acceptance_ids": ["A005"],
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_commit": git_commit(),
        "release_scope": {
            "a005_closed_by_validator": False,
            "mvp_release_ready": False,
        },
    }
    compose: list[str] | None = None
    temporary_directory: tempfile.TemporaryDirectory[str] | None = None
    failure: str | None = None
    before: dict[str, dict[str, Any]] = {}
    after: dict[str, dict[str, Any]] = {}
    cleanup: dict[str, Any] = {
        "down_exit_code": None,
        "container_absent": False,
        "volume_absent": False,
        "network_absent": False,
        "protected_containers_unchanged": False,
    }

    try:
        docker_version = run(
            ["docker", "version", "--format", "{{.Server.Version}}"]
        ).stdout.strip()
        compose_version = run(["docker", "compose", "version", "--short"]).stdout.strip()
        require(container_snapshot(CONTAINER_NAME) is None, "isolated container already exists")
        require(not volume_exists(VOLUME_NAME), "isolated volume already exists")
        require(port_is_available(HOST, HOST_PORT), f"host port {HOST_PORT} is already in use")
        before = protected_snapshots()

        temporary_directory = tempfile.TemporaryDirectory(prefix="eei-a005-")
        override_path = Path(temporary_directory.name) / "compose.override.yml"
        override_path.write_text(compose_override(), encoding="utf-8")
        compose = compose_command(override_path)
        config_payload = json.loads(run([*compose, "config", "--format", "json"]).stdout)
        isolation = validate_compose_config(config_payload)

        run([*compose, "up", "-d", "--wait", "--wait-timeout", "90", "postgres"])
        isolated = container_snapshot(CONTAINER_NAME)
        require(isolated is not None, "isolated PostgreSQL container was not created")
        require(isolated["state"] == "running", "isolated PostgreSQL is not running")
        require(isolated["health"] == "healthy", "isolated PostgreSQL is not healthy")
        require(isolated["compose_project"] == PROJECT_NAME, "isolated project label mismatch")
        require(isolated["compose_service"] == "postgres", "isolated service label mismatch")
        identity = postgres_identity()

        payload.update(
            {
                "runtime": {
                    "docker_server_version": docker_version,
                    "docker_compose_version": compose_version,
                    "postgres_image": isolated["image"],
                },
                "isolation": isolation,
                "checks": {
                    "clean_container_precondition": True,
                    "clean_volume_precondition": True,
                    "host_port_available_precondition": True,
                    "merged_compose_config_isolated": True,
                    "container_running": True,
                    "container_healthy": True,
                    "host_sql_identity": identity,
                },
            }
        )
    except (
        AssertionError,
        json.JSONDecodeError,
        OSError,
        psycopg.Error,
        subprocess.CalledProcessError,
    ) as exc:
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        if compose is not None:
            completed = run(
                [*compose, "down", "-v", "--remove-orphans", "--timeout", "10"],
                check=False,
            )
            cleanup["down_exit_code"] = completed.returncode
        if temporary_directory is not None:
            temporary_directory.cleanup()
        cleanup["container_absent"] = container_snapshot(CONTAINER_NAME) is None
        cleanup["volume_absent"] = not volume_exists(VOLUME_NAME)
        cleanup["network_absent"] = not project_networks()
        try:
            after = protected_snapshots()
            cleanup["protected_containers_unchanged"] = protected_unchanged(before, after)
        except AssertionError as exc:
            failure = failure or f"AssertionError: {exc}"

    payload["protected_resources"] = {"before": before, "after": after}
    payload["cleanup"] = cleanup
    cleanup_passed = (
        cleanup["down_exit_code"] == 0
        and cleanup["container_absent"]
        and cleanup["volume_absent"]
        and cleanup["network_absent"]
        and cleanup["protected_containers_unchanged"]
    )
    if failure is None and cleanup_passed:
        payload["status"] = "PASS"
        payload["release_scope"]["a005_closed_by_validator"] = True
    else:
        payload["failure"] = failure or "cleanup contract failed"
    payload["rollback"] = [
        f"docker compose --project-name {PROJECT_NAME} down -v --remove-orphans",
        f"docker rm -f {CONTAINER_NAME} only if the isolated container remains",
        f"docker volume rm {VOLUME_NAME} only if the isolated volume remains",
        "Do not stop, recreate or remove eei-postgres or eei-worker during A209.",
    ]
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate isolated PostgreSQL Compose clean start."
    )
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()
    payload = execute_clean_environment_probe()
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": payload["status"] == "PASS", "output": args.output}, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
