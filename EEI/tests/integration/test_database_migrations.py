from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from psycopg import errors

from apps.api.app.domain_repository import DomainRepository
from apps.api.app.main import app
from scripts.db_tools import connect_database, database_url

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") and not os.path.exists(".env"),
    reason="DATABASE_URL or .env is required for database integration tests",
)

NVIDIA_ID = "00000000-0000-4000-8000-000000000006"
COREWEAVE_NVIDIA_RELATIONSHIP_ID = "10000000-0000-4000-8000-000000000012"
SUPERSESSION_RELATIONSHIP_ID = "20000000-0000-4000-8000-000000000001"


def run_script(*args: str) -> None:
    subprocess.run(
        [sys.executable, *args],
        check=True,
        cwd=os.getcwd(),
        text=True,
    )


def test_core_domain_migration_seed_idempotency_and_rollback() -> None:
    run_script("scripts/migrate.py", "downgrade", "--all")
    run_script("scripts/migrate.py", "upgrade")
    run_script("scripts/check_database_schema.py")
    run_script("scripts/load_seed_catalogs.py")
    run_script("scripts/load_seed_catalogs.py")
    run_script("scripts/check_database_schema.py", "--expect-seeds")
    run_script("scripts/load_synthetic_fixtures.py")
    run_script("scripts/load_synthetic_fixtures.py")
    run_script("scripts/check_database_schema.py", "--expect-seeds", "--expect-fixtures")
    exercise_domain_api_and_repository_contracts()
    run_script("scripts/migrate.py", "downgrade", "--all")
    run_script("scripts/migrate.py", "status", "--json")


def exercise_domain_api_and_repository_contracts() -> None:
    client = TestClient(app)

    profiles_response = client.get("/v1/scoring/profiles")
    assert profiles_response.status_code == 200
    profiles = profiles_response.json()
    assert len(profiles) == 1
    assert profiles[0]["profile_key"] == "balanced-v2"
    assert profiles[0]["active"] is True

    object_scope_response = client.get("/v1/system/object-scope")
    assert object_scope_response.status_code == 200
    object_scope = object_scope_response.json()
    assert object_scope["coverage"]["relationship_types"] == 52
    assert object_scope["coverage"]["companies"] == 140
    assert object_scope["navigation_module"]["visible"] is True

    relationship_catalog = client.get("/v1/catalogs/relationship").json()
    assert relationship_catalog["actual_row_count"] == 52
    assert relationship_catalog["records"][0]["definition"]

    entity_search = client.get("/v1/entities?q=NVDA&type=legal_entity&limit=5")
    assert entity_search.status_code == 200
    entity_results = entity_search.json()
    assert entity_results[0]["canonical_name"] == "NVIDIA Corporation"
    assert entity_results[0]["entity_type"] == "legal_entity"
    assert entity_results[0]["match_type"] in {"ticker", "alias:ticker"}
    assert entity_results[0]["matched_value"] == "NVDA"
    assert entity_results[0]["primary_identifiers"]["TICKER"] == "NVDA"

    facility_alias_search = client.get("/v1/entities?q=fixture_datacenter&type=facility")
    assert facility_alias_search.status_code == 200
    facility_results = facility_alias_search.json()
    assert facility_results[0]["canonical_name"] == "Synthetic AI Data Center Campus"
    assert facility_results[0]["entity_type"] == "facility"
    assert facility_results[0]["match_type"] == "alias:fixture_key"
    assert facility_results[0]["matched_value"] == "fixture_datacenter"
    assert facility_results[0]["synthetic"] is True
    assert facility_results[0]["fixture_notice"]

    wrong_type_search = client.get("/v1/entities?q=fixture_datacenter&type=legal_entity")
    assert wrong_type_search.status_code == 200
    assert wrong_type_search.json() == []

    entity_lookup = client.get(f"/v1/entities/{NVIDIA_ID}")
    assert entity_lookup.status_code == 200
    assert entity_lookup.json()["primary_identifiers"]["TICKER"] == "NVDA"

    watchlist_response = client.post(
        "/v1/watchlists",
        json={"name": "MVP semiconductor fixture"},
    )
    assert watchlist_response.status_code == 201
    watchlist_id = watchlist_response.json()["id"]

    item_response = client.post(
        f"/v1/watchlists/{watchlist_id}/items",
        json={
            "object_type": "entity",
            "object_id": NVIDIA_ID,
            "labels": ["fixture", "supply_chain"],
            "note": "G2 API integration test",
            "saved_state": {"lens": "supply_chain"},
        },
    )
    assert item_response.status_code == 201
    assert item_response.json()["object_id"] == NVIDIA_ID

    explore_response = client.post(
        "/v1/explore",
        json={
            "focus": {"object_type": "entity", "object_id": NVIDIA_ID},
            "active_layers": ["supply_chain_operations", "technology_data_ip"],
            "direction": "both",
            "hops": 1,
            "budget": {"max_nodes": 42, "max_edges": 64, "expand_nodes": 12},
        },
    )
    assert explore_response.status_code == 200
    exploration = explore_response.json()
    assert exploration["focus"]["canonical_name"] == "NVIDIA Corporation"
    assert exploration["coverage"]["synthetic_fixture_edges"] >= 1
    assert any(edge["synthetic"] is True for edge in exploration["edges"])
    assert all(edge["fixture_notice"] for edge in exploration["edges"] if edge["synthetic"])

    home_response = client.get("/v1/home")
    assert home_response.status_code == 200
    home = home_response.json()
    assert home["global_search"]["endpoint"] == "/v1/entities"
    assert "legal_entity" in home["global_search"]["supported_entity_types"]
    assert home["global_search"]["example"] == {"q": "NVDA", "type": "legal_entity"}
    assert home["industries"][0]["taxonomy_version"]
    assert home["watchlists"][0]["items"][0]["object_id"] == NVIDIA_ID
    assert home["recent_explorations"][0]["current_focus_entity_id"] == NVIDIA_ID
    assert len(home["changes"]) >= 1
    assert home["freshness"]["status"] == "synthetic_fixture"
    assert home["freshness"]["source_document_count"] >= 1
    assert home["freshness"]["latest_relationship_observed_at"]
    assert home["model_status"]["active_profile"]["profile_key"] == "balanced-v2"
    assert home["model_status"]["calibration"]["latest_status"] == "not_scheduled"
    assert home["model_status"]["calibration"]["cadence_days"] == 14
    assert "Synthetic fixtures" in home["model_status"]["fixture_policy"]

    calibration_response = client.post("/v1/calibrations/run")
    assert calibration_response.status_code == 202
    assert calibration_response.json()["cadence_days"] == 14
    home_after_calibration = client.get("/v1/home").json()
    calibration_status = home_after_calibration["model_status"]["calibration"]
    assert calibration_status["latest_status"] == "scheduled"
    assert calibration_status["next_scheduled_for"]
    calibration_list = client.get("/v1/calibrations")
    assert calibration_list.status_code == 200
    assert calibration_list.json()[0]["status"] == "scheduled"

    audit_logs = client.get("/v1/audit-logs").json()
    action_types = {row["action_type"] for row in audit_logs}
    assert {"create_watchlist", "add_watchlist_item", "queue_calibration"} <= action_types

    repository = DomainRepository(database_url())
    superseded = repository.record_relationship_supersession(
        supersedes_id=UUID(COREWEAVE_NVIDIA_RELATIONSHIP_ID),
        new_relationship_id=UUID(SUPERSESSION_RELATIONSHIP_ID),
        observed_at=datetime(2026, 6, 19, tzinfo=UTC),
        confidence=0.777,
        reason="A023 integration test supersession",
    )
    assert superseded["supersedes_id"] == COREWEAVE_NVIDIA_RELATIONSHIP_ID

    conflict = repository.record_relationship_conflict(
        relationship_id=UUID(SUPERSESSION_RELATIONSHIP_ID),
        reason="A023 integration test conflict",
    )
    assert conflict["change_type"] == "conflict_detected"
    assert conflict["review_required"] is True

    supersession_changes = client.get("/v1/changes?change_type=superseded").json()
    assert supersession_changes[0]["object_id"] == SUPERSESSION_RELATIONSHIP_ID
    assert supersession_changes[0]["old_value"]["id"] == COREWEAVE_NVIDIA_RELATIONSHIP_ID
    conflict_changes = client.get("/v1/changes?change_type=conflict_detected").json()
    assert conflict_changes[0]["review_required"] is True

    with connect_database() as connection:
        old_status = connection.execute(
            "SELECT status FROM relationships WHERE id = %s",
            (COREWEAVE_NVIDIA_RELATIONSHIP_ID,),
        ).fetchone()[0]
        new_supersedes_id = connection.execute(
            "SELECT supersedes_id FROM relationships WHERE id = %s",
            (SUPERSESSION_RELATIONSHIP_ID,),
        ).fetchone()[0]
    assert old_status == "superseded"
    assert str(new_supersedes_id) == COREWEAVE_NVIDIA_RELATIONSHIP_ID

    with connect_database() as connection:
        try:
            connection.execute(
                """
                INSERT INTO relationships(
                  subject_entity_id, object_entity_id, relationship_type, relationship_family,
                  status, observed_at, amount
                )
                VALUES (%s, %s, 'customer_of', 'commercial_dependency', 'reported', now(), 100)
                """,
                (NVIDIA_ID, NVIDIA_ID),
            )
        except errors.CheckViolation:
            connection.rollback()
        else:  # pragma: no cover - should be unreachable with the migration constraint.
            raise AssertionError("amount without currency and amount_kind must be rejected")
