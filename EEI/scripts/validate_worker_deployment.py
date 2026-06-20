#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = Path("docker-compose.yml")
WORKER_DOCKERFILE = Path("infra/docker/worker.Dockerfile")
OUTPUT_PATH = Path("artifacts/tests/a206/t1304_worker_deployment_binding_contract.json")


def read_compose() -> dict[str, Any]:
    payload = yaml.safe_load((ROOT / COMPOSE_PATH).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError("docker-compose.yml must parse as a YAML object")
    return payload


def command_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value or "")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_binding() -> dict[str, Any]:
    compose = read_compose()
    services = compose.get("services")
    require(isinstance(services, dict), "docker-compose.yml must define services")
    for service_name in ("postgres", "migrate", "worker"):
        require(service_name in services, f"missing compose service: {service_name}")

    postgres = services["postgres"]
    migrate = services["migrate"]
    worker = services["worker"]

    require("healthcheck" in postgres, "postgres service must define a healthcheck")
    require("worker" in (migrate.get("profiles") or []), "migrate service must use worker profile")
    require("worker" in (worker.get("profiles") or []), "worker service must use worker profile")

    migrate_depends = migrate.get("depends_on", {})
    require(
        migrate_depends.get("postgres", {}).get("condition") == "service_healthy",
        "migrate must wait for healthy postgres",
    )
    migrate_command = command_text(migrate.get("command"))
    require("scripts/migrate.py upgrade" in migrate_command, "migrate must run schema upgrade")

    worker_depends = worker.get("depends_on", {})
    require(
        worker_depends.get("postgres", {}).get("condition") == "service_healthy",
        "worker must wait for healthy postgres",
    )
    require(
        worker_depends.get("migrate", {}).get("condition") == "service_completed_successfully",
        "worker must wait for successful migration",
    )

    worker_command = command_text(worker.get("command"))
    require(
        "apps.worker.app.main supervise" in worker_command,
        "worker command must run apps.worker supervisor",
    )
    for token in (
        "--worker-id",
        "--max-jobs-per-cycle",
        "--max-outbox-per-cycle",
        "--poll-interval-seconds",
    ):
        require(token in worker_command, f"worker command missing {token}")
    require(
        worker.get("restart") == "unless-stopped",
        "worker restart policy must be unless-stopped",
    )
    require(worker.get("stop_grace_period") == "30s", "worker stop_grace_period must be 30s")
    require("healthcheck" in worker, "worker service must define a healthcheck")
    healthcheck = command_text(worker["healthcheck"].get("test"))
    require(
        "apps.worker.app.main health" in healthcheck,
        "worker healthcheck must call apps.worker health",
    )

    dockerfile = (ROOT / WORKER_DOCKERFILE).read_text(encoding="utf-8")
    for token in (
        "FROM python:3.12-slim",
        "uv sync --frozen",
        "COPY apps ./apps",
        "COPY infra ./infra",
        "apps.worker.app.main",
    ):
        require(token in dockerfile, f"worker Dockerfile missing {token}")

    return {
        "schema_version": "eei-worker-deployment-binding-v1",
        "status": "PASS",
        "task_id": "T1304",
        "acceptance_ids": ["A206", "A209"],
        "runtime": {
            "process_manager": "docker_compose",
            "compose_file": str(COMPOSE_PATH),
            "worker_profile": "worker",
            "start_command": "docker compose --profile worker up -d worker",
            "stop_command": "docker compose --profile worker stop worker",
            "logs_command": "docker compose logs --tail=200 worker",
        },
        "services": {
            "postgres": {
                "healthcheck": True,
            },
            "migrate": {
                "waits_for_postgres": True,
                "command": migrate_command,
            },
            "worker": {
                "dockerfile": str(WORKER_DOCKERFILE),
                "command": worker_command,
                "restart": worker["restart"],
                "stop_grace_period": worker["stop_grace_period"],
                "healthcheck": healthcheck,
                "waits_for_postgres": True,
                "waits_for_migration": True,
            },
        },
        "operator_controls": {
            "health": "make worker-health",
            "once": "make worker-once",
            "supervise": "make worker-supervise",
        },
        "soak_readiness": {
            "worker_supervisor_bound": True,
            "short_duration_hours": 4,
            "long_duration_hours": 24,
            "a209_status": "PARTIAL_UNTIL_OPERATOR_RUNS_COMPLETE",
        },
        "remaining_gaps_before_done": [
            "Run T1307 4h and 24h operator soak using the Docker Compose worker binding.",
            "Attach completed operator evidence before marking A209 DONE.",
        ],
        "rollback": [
            "Run docker compose --profile worker stop worker.",
            "Revert docker-compose.yml worker/migrate services and infra/docker/worker.Dockerfile.",
            "Regenerate release artifacts and rerun make verify.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate EEI worker deployment binding.")
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()
    try:
        payload = validate_binding()
        output = ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"valid": True, "output": args.output}, indent=2))
    except (AssertionError, OSError, yaml.YAMLError) as exc:
        print(f"Worker deployment validation: FAIL - {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
