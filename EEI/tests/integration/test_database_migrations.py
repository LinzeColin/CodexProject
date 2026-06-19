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
THEME_AI_INFRA_ID = "00000000-0000-4000-8000-000000000020"
FIXTURE_DATACENTER_ID = "00000000-0000-4000-8000-000000000024"
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

    industries_response = client.get("/v1/industries")
    assert industries_response.status_code == 200
    industries = industries_response.json()
    semiconductor = next(
        row for row in industries if row["slug"] == "semiconductors-electronics"
    )
    assert semiconductor["taxonomy_version"] == "v4.2.0"
    assert semiconductor["name_zh"] == "半导体与电子系统"
    assert semiconductor["entity_count"] >= 2
    subindustry_response = client.get(f"/v1/industries?parent={semiconductor['id']}")
    assert subindustry_response.status_code == 200
    assert any(row["slug"] == "chip-design-ip" for row in subindustry_response.json())

    semiconductor_landscape_response = client.get(
        f"/v1/industries/{semiconductor['id']}/landscape"
    )
    assert semiconductor_landscape_response.status_code == 200
    semiconductor_landscape = semiconductor_landscape_response.json()
    assert semiconductor_landscape["industry"]["slug"] == "semiconductors-electronics"
    assert semiconductor_landscape["taxonomy_version"] == "v4.2.0"
    assert len(semiconductor_landscape["chain_stages"]) == 16
    assert any(
        row["relationship_count"] > 0
        for row in semiconductor_landscape["chain_stages"]
    )
    assert semiconductor_landscape["bottlenecks"]
    assert semiconductor_landscape["navigation"]["cross_industry_allowed"] is True
    assert semiconductor_landscape["cross_industry_links"]
    nvidia_industry_row = next(
        row for row in semiconductor_landscape["entities"] if row["id"] == NVIDIA_ID
    )
    nvidia_roles = {row["role"] for row in nvidia_industry_row["industries"]}
    assert {"primary", "secondary"} <= nvidia_roles
    assert nvidia_industry_row["primary_industry_id"] == semiconductor["id"]
    assert nvidia_industry_row["secondary_industry_ids"]
    assert nvidia_industry_row["cross_industry"] is True

    ai_cloud = next(row for row in industries if row["slug"] == "ai-cloud-data")
    ai_landscape = client.get(f"/v1/industries/{ai_cloud['id']}/landscape").json()
    assert ai_landscape["capital"]
    software = next(row for row in industries if row["slug"] == "software-cybersecurity")
    software_landscape = client.get(f"/v1/industries/{software['id']}/landscape").json()
    assert software_landscape["policy"]

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
    assert exploration["query"]["focus"]["object_id"] == NVIDIA_ID
    assert exploration["query"]["active_layers"] == [
        "supply_chain_operations",
        "technology_data_ip",
    ]
    assert exploration["query"]["direction"] == "both"
    assert exploration["query"]["hops"] == 1
    assert exploration["query"]["budget"] == {
        "max_nodes": 42,
        "max_edges": 64,
        "expand_nodes": 12,
    }
    assert exploration["query"]["hard_limits"] == {
        "max_hops": 2,
        "max_nodes": 500,
        "max_edges": 2000,
        "max_path_length": 8,
    }

    default_explore_response = client.post(
        "/v1/explore",
        json={"focus": {"object_type": "entity", "object_id": NVIDIA_ID}},
    )
    assert default_explore_response.status_code == 200
    default_exploration = default_explore_response.json()
    assert default_exploration["query"]["active_layers"] == ["supply_chain_operations"]
    assert default_exploration["query"]["direction"] == "both"
    assert default_exploration["query"]["hops"] == 1
    assert default_exploration["query"]["budget"] == {
        "max_nodes": 42,
        "max_edges": 64,
        "expand_nodes": 12,
    }
    assert len(default_exploration["nodes"]) <= 42
    assert len(default_exploration["edges"]) <= 64

    profile_id = profiles[0]["id"]
    explicit_explore_response = client.post(
        "/v1/explore",
        json={
            "focus": {"object_type": "entity", "object_id": NVIDIA_ID},
            "active_layers": ["capital_control", "policy_regulatory"],
            "direction": "upstream",
            "hops": 2,
            "as_of": "2026-06-19T00:00:00Z",
            "scoring_profile_version_id": profile_id,
            "filters": {"relationship_family": ["capital_financing"]},
            "budget": {"max_nodes": 7, "max_edges": 8, "expand_nodes": 3},
        },
    )
    assert explicit_explore_response.status_code == 200
    explicit_exploration = explicit_explore_response.json()
    assert explicit_exploration["query"]["direction"] == "upstream"
    assert explicit_exploration["query"]["hops"] == 2
    assert explicit_exploration["query"]["as_of"] == "2026-06-19T00:00:00Z"
    assert explicit_exploration["query"]["scoring_profile_version_id"] == profile_id
    assert explicit_exploration["query"]["filters"] == {
        "relationship_family": ["capital_financing"]
    }
    assert explicit_exploration["query"]["budget"] == {
        "max_nodes": 7,
        "max_edges": 8,
        "expand_nodes": 3,
    }
    explicit_state = explicit_exploration["state"]
    assert explicit_state["version"] == "exploration-state-v1"
    assert explicit_state["session_id"] == explicit_exploration["session_id"]
    assert explicit_state["focus"] == {"object_type": "entity", "object_id": NVIDIA_ID}
    assert explicit_state["active_layers"] == ["capital_control", "policy_regulatory"]
    assert explicit_state["direction"] == "upstream"
    assert explicit_state["hops"] == 2
    assert explicit_state["as_of"] == "2026-06-19T00:00:00Z"
    assert explicit_state["scoring_profile_version_id"] == profile_id
    assert explicit_state["filters"] == {"relationship_family": ["capital_financing"]}
    assert explicit_state["budget"] == {"max_nodes": 7, "max_edges": 8, "expand_nodes": 3}
    url_state = explicit_state["url_state"]
    assert url_state["version"] == "exploration-url-state-v1"
    assert url_state["route"] == "/"
    assert url_state["query"]["session"] == explicit_exploration["session_id"]
    assert url_state["query"]["focus"] == f"entity:{NVIDIA_ID}"
    assert url_state["query"]["layers"] == "capital_control,policy_regulatory"
    assert url_state["query"]["direction"] == "upstream"
    assert url_state["query"]["hops"] == "2"
    assert url_state["query"]["as_of"] == "2026-06-19T00:00:00Z"
    assert url_state["query"]["profile"] == profile_id
    assert url_state["query"]["filters"] == '{"relationship_family":["capital_financing"]}'
    assert "direction=upstream" in url_state["query_string"]
    assert "hops=2" in url_state["query_string"]

    restored_explore_response = client.post(
        "/v1/explore",
        json=url_state["restore_payload"],
    )
    assert restored_explore_response.status_code == 200
    restored_exploration = restored_explore_response.json()
    assert restored_exploration["session_id"] == explicit_exploration["session_id"]
    assert restored_exploration["state"]["url_state"]["query"] == url_state["query"]
    assert restored_exploration["state"]["url_state"]["restore_payload"] == url_state[
        "restore_payload"
    ]
    with connect_database() as connection:
        session_row = connection.execute(
            """
            SELECT active_layers, direction, hops, budget, filters, state_version
            FROM exploration_sessions
            WHERE id = %s
            """,
            (explicit_exploration["session_id"],),
        ).fetchone()
    assert session_row[0] == ["capital_control", "policy_regulatory"]
    assert session_row[1] == "upstream"
    assert session_row[2] == 2
    assert session_row[3] == {"max_nodes": 7, "max_edges": 8, "expand_nodes": 3}
    assert session_row[4] == {"relationship_family": ["capital_financing"]}
    assert session_row[5] == "exploration-state-v1"

    for invalid_payload in (
        {
            "focus": {"object_type": "entity", "object_id": NVIDIA_ID},
            "hops": 3,
        },
        {
            "focus": {"object_type": "entity", "object_id": NVIDIA_ID},
            "budget": {"max_nodes": 501, "max_edges": 64, "expand_nodes": 12},
        },
        {
            "focus": {"object_type": "entity", "object_id": NVIDIA_ID},
            "budget": {"max_nodes": 42, "max_edges": 2001, "expand_nodes": 12},
        },
    ):
        invalid_explore_response = client.post("/v1/explore", json=invalid_payload)
        assert invalid_explore_response.status_code == 422

    over_budget_response = client.post(
        "/v1/explore",
        json={
            "focus": {"object_type": "entity", "object_id": NVIDIA_ID},
            "budget": {"max_nodes": 2, "max_edges": 1, "expand_nodes": 1},
        },
    )
    assert over_budget_response.status_code == 200
    over_budget = over_budget_response.json()
    assert over_budget["truncated"] is True
    assert over_budget["truncation"]["applied"] is True
    assert set(over_budget["truncation"]["reasons"]) & {"edge_budget", "node_budget"}
    assert over_budget["truncation"]["returned_edge_count"] <= 1
    assert over_budget["truncation"]["returned_node_count"] <= 2
    assert len(over_budget["edges"]) <= 1
    assert len(over_budget["nodes"]) <= 2
    assert over_budget["continuation"]["available"] is True
    assert over_budget["continuation"]["expand_endpoint"] == "/v1/explore/expand"
    assert over_budget["continuation"]["anchor_entity_id"] == NVIDIA_ID
    assert any(
        warning.startswith("bounded_graph_budget_applied:")
        for warning in over_budget["warnings"]
    )

    home_response = client.get("/v1/home")
    assert home_response.status_code == 200
    home = home_response.json()
    assert home["global_search"]["endpoint"] == "/v1/entities"
    assert "legal_entity" in home["global_search"]["supported_entity_types"]
    assert home["global_search"]["example"] == {"q": "NVDA", "type": "legal_entity"}
    assert home["industries"][0]["taxonomy_version"]
    assert home["watchlists"][0]["items"][0]["object_id"] == NVIDIA_ID
    assert home["recent_explorations"][0]["current_focus_entity_id"] == NVIDIA_ID
    assert isinstance(home["changes"], list)
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

    watchlist_detail = client.get(f"/v1/watchlists/{watchlist_id}")
    assert watchlist_detail.status_code == 200
    assert watchlist_detail.json()["items"][0]["saved_state"] == {"lens": "supply_chain"}

    remove_response = client.delete(
        f"/v1/watchlists/{watchlist_id}/items",
        params={"object_type": "entity", "object_id": NVIDIA_ID},
    )
    assert remove_response.status_code == 204
    removed_detail = client.get(f"/v1/watchlists/{watchlist_id}").json()
    assert all(item["object_id"] != NVIDIA_ID for item in removed_detail["items"])

    restored_entity_response = client.post(
        f"/v1/watchlists/{watchlist_id}/items",
        json={
            "object_type": "entity",
            "object_id": NVIDIA_ID,
            "labels": ["restored", "capital"],
            "note": "restored item",
            "saved_state": {"lens": "capital_control", "profile": "balanced-v2"},
        },
    )
    assert restored_entity_response.status_code == 201
    industry_item_response = client.post(
        f"/v1/watchlists/{watchlist_id}/items",
        json={
            "object_type": "industry",
            "object_id": semiconductor["id"],
            "labels": ["industry"],
            "saved_state": {"view": "landscape"},
        },
    )
    assert industry_item_response.status_code == 201
    theme_item_response = client.post(
        f"/v1/watchlists/{watchlist_id}/items",
        json={
            "object_type": "theme",
            "object_id": THEME_AI_INFRA_ID,
            "labels": ["theme"],
            "saved_state": {"lens": "strategy"},
        },
    )
    assert theme_item_response.status_code == 201
    facility_item_response = client.post(
        f"/v1/watchlists/{watchlist_id}/items",
        json={
            "object_type": "facility",
            "object_id": FIXTURE_DATACENTER_ID,
            "labels": ["facility"],
            "saved_state": {"lens": "supply_chain"},
        },
    )
    assert facility_item_response.status_code == 201
    invalid_facility_response = client.post(
        f"/v1/watchlists/{watchlist_id}/items",
        json={
            "object_type": "facility",
            "object_id": NVIDIA_ID,
            "saved_state": {},
        },
    )
    assert invalid_facility_response.status_code == 404
    restored_detail = client.get(f"/v1/watchlists/{watchlist_id}").json()
    item_types = {item["object_type"] for item in restored_detail["items"]}
    assert {"entity", "industry", "theme", "facility"} <= item_types
    restored_entity = next(
        item
        for item in restored_detail["items"]
        if item["object_type"] == "entity" and item["object_id"] == NVIDIA_ID
    )
    assert restored_entity["saved_state"]["lens"] == "capital_control"

    audit_logs = client.get("/v1/audit-logs").json()
    action_types = {row["action_type"] for row in audit_logs}
    assert {
        "create_watchlist",
        "add_watchlist_item",
        "remove_watchlist_item",
        "queue_calibration",
    } <= action_types

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
    home_after_changes = client.get("/v1/home").json()
    assert len(home_after_changes["changes"]) >= 2

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
