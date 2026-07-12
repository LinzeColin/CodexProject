from __future__ import annotations

import pytest

from scripts.validate_postgres_compose_clean_environment import (
    CONTAINER_NAME,
    HOST,
    HOST_PORT,
    PROJECT_NAME,
    VOLUME_NAME,
    compose_override,
    protected_unchanged,
    validate_compose_config,
)


def test_compose_override_uses_isolated_resources() -> None:
    payload = compose_override()

    assert f"container_name: {CONTAINER_NAME}" in payload
    assert f'"{HOST}:{HOST_PORT}:5432"' in payload
    assert f"name: {VOLUME_NAME}" in payload
    assert "!override" in payload
    assert "eei-postgres" not in payload


def test_validate_compose_config_requires_isolated_postgres_contract() -> None:
    result = validate_compose_config(
        {
            "services": {
                "postgres": {
                    "container_name": CONTAINER_NAME,
                    "ports": [{"host_ip": HOST, "published": str(HOST_PORT), "target": 5432}],
                    "volumes": [
                        {
                            "type": "volume",
                            "source": "a005-postgres-data",
                            "target": "/var/lib/postgresql/data",
                        }
                    ],
                    "healthcheck": {"test": ["CMD-SHELL", "pg_isready"]},
                }
            },
            "volumes": {"a005-postgres-data": {"name": VOLUME_NAME}},
        }
    )

    assert result["project_name"] == PROJECT_NAME
    assert result["host_port"] == HOST_PORT
    assert result["healthcheck_present"] is True


def test_validate_compose_config_rejects_default_port() -> None:
    with pytest.raises(AssertionError, match="isolated host port mismatch"):
        validate_compose_config(
            {
                "services": {
                    "postgres": {
                        "container_name": CONTAINER_NAME,
                        "ports": [{"host_ip": HOST, "published": "5432", "target": 5432}],
                        "volumes": [
                            {"type": "volume", "source": "a005-postgres-data"}
                        ],
                        "healthcheck": {"test": ["CMD-SHELL", "pg_isready"]},
                    }
                },
                "volumes": {"a005-postgres-data": {"name": VOLUME_NAME}},
            }
        )


def test_protected_unchanged_requires_same_identity_and_health() -> None:
    before = {
        "eei-postgres": {"id": "postgres-id", "started_at": "t1"},
        "eei-worker": {"id": "worker-id", "started_at": "t2"},
    }
    after = {
        "eei-postgres": {
            "id": "postgres-id",
            "started_at": "t1",
            "state": "running",
            "health": "healthy",
        },
        "eei-worker": {
            "id": "worker-id",
            "started_at": "t2",
            "state": "running",
            "health": "healthy",
        },
    }

    assert protected_unchanged(before, after) is True
    after["eei-worker"]["id"] = "restarted-worker"
    assert protected_unchanged(before, after) is False
