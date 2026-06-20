from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from psycopg import errors
from psycopg.types.json import Jsonb

from apps.api.app.domain_repository import DomainRepository
from apps.api.app.main import app
from scripts.db_tools import connect_database, database_url

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") and not os.path.exists(".env"),
    reason="DATABASE_URL or .env is required for database integration tests",
)

NVIDIA_ID = "00000000-0000-4000-8000-000000000006"
MICROSOFT_ID = "00000000-0000-4000-8000-000000000003"
OPENAI_GROUP_ID = "00000000-0000-4000-8000-000000000012"
OPENAI_FOUNDATION_ID = "00000000-0000-4000-8000-000000000013"
PALANTIR_ID = "00000000-0000-4000-8000-000000000009"
GOVERNMENT_BODY_ID = "00000000-0000-4000-8000-000000000019"
THEME_AI_INFRA_ID = "00000000-0000-4000-8000-000000000020"
FIXTURE_MATERIALS_ID = "00000000-0000-4000-8000-000000000023"
FIXTURE_DATACENTER_ID = "00000000-0000-4000-8000-000000000024"
COREWEAVE_NVIDIA_RELATIONSHIP_ID = "10000000-0000-4000-8000-000000000012"
SUPERSESSION_RELATIONSHIP_ID = "20000000-0000-4000-8000-000000000001"
CURATED_ANCHOR_PARSER_VERSION = "nvidia-public-anchor-v1"
DOSSIER_HUMAN_SUMMARY_KEYS = {
    "headline",
    "business",
    "group",
    "dependencies",
    "capital",
    "policy",
    "signals",
    "data_gaps",
}
EMPIRE_WORKSPACE_LAYER_KEYS = [
    "group_structure",
    "business_segments",
    "supply_chain",
    "capital_network",
    "ma_transactions",
    "control_relationships",
    "policy_environment",
    "strategic_signals",
]


def run_script(*args: str) -> None:
    subprocess.run(
        [sys.executable, *args],
        check=True,
        cwd=os.getcwd(),
        text=True,
    )


def assert_evidence_bearing_paths(payload: dict[str, object], *, max_length: int) -> None:
    paths = payload["paths"]
    assert isinstance(paths, list)
    assert 1 <= len(paths) <= 8
    assert payload["coverage"]["path_count"] == len(paths)
    assert payload["coverage"]["all_edges_have_evidence"] is True
    assert payload["coverage"]["source_count"] >= 1
    for path in paths:
        assert path["length"] <= max_length
        assert len(path["relationship_ids"]) == path["length"]
        assert len(path["node_ids"]) == path["length"] + 1
        assert path["evidence"]
        for edge in path["edges"]:
            assert edge["evidence_count"] >= 1
            assert edge["evidence"]
            assert edge["traversal_direction"] in {"forward", "reverse"}
            for evidence in edge["evidence"]:
                assert evidence["source_document_id"]
                assert evidence["source_tier"] >= 1
                assert evidence["support_excerpt"]
                assert evidence["url"].startswith("fixture://relationship/")


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
    run_script("scripts/load_curated_ingestion_anchors.py")
    run_script("scripts/load_curated_ingestion_anchors.py")
    run_script(
        "scripts/check_database_schema.py",
        "--expect-seeds",
        "--expect-fixtures",
        "--expect-curated-ingestion",
    )
    exercise_curated_official_ingestion_contracts()
    exercise_production_fact_version_contracts()
    exercise_domain_api_and_repository_contracts()
    run_script("scripts/migrate.py", "downgrade", "--all")
    run_script("scripts/migrate.py", "status", "--json")


def exercise_curated_official_ingestion_contracts() -> None:
    with connect_database() as connection:
        parser_version = CURATED_ANCHOR_PARSER_VERSION
        raw_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE record_mode = 'curated_official_fixture'),
                   count(*) FILTER (WHERE review_status = 'machine_verified'),
                   count(DISTINCT source_document_id)
            FROM raw_source_snapshots
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()
        assert raw_row == (6, 6, 6, 6)

        latest_run = connection.execute(
            """
            SELECT status, counts->>'anchors', counts->>'fact_source_snapshots',
                   counts->>'relationship_fact_candidates'
            FROM ingestion_runs
            WHERE connector_version = %s AND mode = 'curated_official_fixture'
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (parser_version,),
        ).fetchone()
        assert latest_run[0] == "succeeded"
        assert latest_run[1] == "4"
        assert latest_run[2] == "2"
        assert latest_run[3] == "2"

        source_documents = connection.execute(
            """
            SELECT count(*)
            FROM source_documents sd
            JOIN raw_source_snapshots rss ON rss.source_document_id = sd.id
            WHERE rss.parser_version = %s
              AND sd.parser_version = %s
              AND (
                sd.raw_storage_uri LIKE 'data/nvidia_public_source_anchors.csv#%%'
                OR sd.raw_storage_uri LIKE 'data/golden_vertical_fact_candidates.json#%%'
              )
              AND sd.content_hash = rss.content_hash
            """,
            (parser_version, parser_version),
        ).fetchone()[0]
        assert source_documents == 6

        candidate_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE confidence >= 0.72),
                   count(*) FILTER (WHERE matched_research_id IS NOT NULL),
                   count(*) FILTER (WHERE review_status = 'unreviewed')
            FROM entity_resolution_candidates
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()
        assert candidate_row[0] >= 55
        assert candidate_row[1] >= 10
        assert candidate_row[2] >= 6
        assert candidate_row[3] >= 1

        nvidia_subjects = connection.execute(
            """
            SELECT count(*)
            FROM entity_resolution_candidates erc
            JOIN raw_source_snapshots rss ON rss.id = erc.raw_snapshot_id
            JOIN source_documents sd ON sd.id = rss.source_document_id
            WHERE erc.parser_version = %s
              AND rss.parser_version = %s
              AND sd.parser_version = %s
              AND sd.raw_storage_uri LIKE 'data/nvidia_public_source_anchors.csv#%%'
              AND erc.candidate_name = 'NVIDIA Corporation'
              AND erc.matched_research_id = 'P0-006'
              AND erc.matched_entity_id = %s
              AND erc.match_method = 'anchor_subject'
            """,
            (parser_version, parser_version, parser_version, NVIDIA_ID),
        ).fetchone()[0]
        assert nvidia_subjects == 4

        tsmc_candidates = connection.execute(
            """
            SELECT count(*), min(confidence)
            FROM entity_resolution_candidates
            WHERE parser_version = %s
              AND candidate_name = 'TSMC'
              AND matched_research_id = 'X-001'
            """,
            (parser_version,),
        ).fetchone()
        assert tsmc_candidates[0] >= 2
        assert float(tsmc_candidates[1]) >= 0.72

        evidence_row = connection.execute(
            """
            WITH curated_sources AS (
              SELECT rss.id AS raw_snapshot_id, rss.source_document_id
              FROM raw_source_snapshots rss
              JOIN source_documents sd ON sd.id = rss.source_document_id
              WHERE rss.parser_version = %s
                AND sd.parser_version = %s
                AND (
                  sd.raw_storage_uri LIKE 'data/nvidia_public_source_anchors.csv#%%'
                  OR sd.raw_storage_uri LIKE 'data/golden_vertical_fact_candidates.json#%%'
                )
            )
            SELECT count(iec.*),
                   count(iec.*) FILTER (WHERE iec.evidence_role = 'context'),
                   count(iec.*) FILTER (WHERE iec.evidence_role = 'supports'),
                   count(iec.*) FILTER (WHERE jsonb_typeof(iec.counter_evidence) = 'array'),
                   count(iec.*) FILTER (WHERE iec.review_status = 'machine_verified'),
                   count(iec.*) FILTER (WHERE iec.relationship_type IS NOT NULL)
            FROM curated_sources cs
            JOIN ingestion_evidence_chain iec
              ON iec.raw_snapshot_id = cs.raw_snapshot_id
             AND iec.source_document_id = cs.source_document_id
            WHERE iec.parser_version = %s
            """,
            (parser_version, parser_version, parser_version),
        ).fetchone()
        assert evidence_row == (6, 4, 2, 6, 6, 2)

        evidence_sample = connection.execute(
            """
            SELECT structured_fact->>'edge_publication',
                   structured_fact->>'record_mode',
                   counter_evidence,
                   support_excerpt
            FROM ingestion_evidence_chain
            WHERE parser_version = %s
              AND evidence_role = 'context'
              AND structured_fact ? 'edge_publication'
            ORDER BY locator
            LIMIT 1
            """,
            (parser_version,),
        ).fetchone()
        assert evidence_sample[0] == "candidate_context_only_not_published_relationship"
        assert evidence_sample[1] == "curated_official_fixture"
        assert evidence_sample[2] == []
        assert evidence_sample[3]

        fact_candidate_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE publication_status = 'candidate'),
                   count(*) FILTER (WHERE source_threshold_met = false),
                   count(*) FILTER (WHERE review_status = 'machine_verified'),
                   count(*) FILTER (WHERE jsonb_typeof(counter_evidence) = 'array')
            FROM relationship_fact_candidates
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()
        assert fact_candidate_row == (2, 2, 2, 2, 2)

        golden_path_roles = {
            row[0]
            for row in connection.execute(
                """
                SELECT structured_fact->>'path_role'
                FROM relationship_fact_candidates
                WHERE parser_version = %s
                """,
                (parser_version,),
            ).fetchall()
        }
        assert golden_path_roles == {
            "NVIDIA_TO_TSMC_GOLDEN_VERTICAL",
            "TSMC_TO_ASML_GOLDEN_VERTICAL",
        }

        fact_evidence_count = connection.execute(
            """
            SELECT count(*)
            FROM relationship_fact_candidate_evidence rfce
            JOIN relationship_fact_candidates rfc ON rfc.id = rfce.candidate_id
            WHERE rfc.parser_version = %s
            """,
            (parser_version,),
        ).fetchone()[0]
        assert fact_evidence_count == 2

        review_queue_count = connection.execute(
            """
            SELECT count(*)
            FROM manual_review_queue mrq
            JOIN relationship_fact_candidates rfc ON rfc.id = mrq.object_id
            WHERE mrq.object_type = 'relationship_fact_candidate'
              AND mrq.status = 'open'
              AND rfc.parser_version = %s
            """,
            (parser_version,),
        ).fetchone()[0]
        assert review_queue_count == 2

        relationship_count = connection.execute("SELECT count(*) FROM relationships").fetchone()[0]
        assert relationship_count == 26


def exercise_production_fact_version_contracts() -> None:
    with connect_database() as connection:
        source_document_row = connection.execute(
            """
            SELECT source_document_id
            FROM relationship_evidence
            WHERE relationship_id = %s
            ORDER BY source_document_id
            LIMIT 1
            """,
            (COREWEAVE_NVIDIA_RELATIONSHIP_ID,),
        ).fetchone()
        assert source_document_row is not None
        source_document_id = source_document_row[0]

        snapshot_id = connection.execute(
            """
            INSERT INTO data_snapshots(
              snapshot_key, scope, record_mode, status, source_hash, as_of, activated_at, metadata
            )
            VALUES (
              'a201-fixture-snapshot',
              'golden-vertical:nvidia',
              'fixture',
              'active',
              'a201-source-hash',
              '2026-06-19T00:00:00Z',
              '2026-06-19T00:00:01Z',
              %s
            )
            RETURNING id
            """,
            (Jsonb({"acceptance_id": "A201", "task_id": "T1300"}),),
        ).fetchone()[0]
        fact_version_id = connection.execute(
            """
            INSERT INTO fact_versions(
              snapshot_id, object_type, object_id, version_no, fact_status, record_mode,
              valid_from, valid_to, observed_at, source_document_id, parser_version,
              payload_hash, payload
            )
            VALUES (
              %s,
              'relationship',
              %s,
              1,
              'reported',
              'fixture',
              '2026-01-01T00:00:00Z',
              NULL,
              '2026-06-19T00:00:00Z',
              %s,
              'fixture-v1',
              'a201-payload-hash',
              %s
            )
            RETURNING id
            """,
            (
                snapshot_id,
                COREWEAVE_NVIDIA_RELATIONSHIP_ID,
                source_document_id,
                Jsonb(
                    {
                        "relationship_id": COREWEAVE_NVIDIA_RELATIONSHIP_ID,
                        "relationship_family": "supply_chain_operations",
                    }
                ),
            ),
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO fact_version_evidence(
              fact_version_id, source_document_id, role, locator, support_excerpt,
              structured_fact
            )
            VALUES (%s, %s, 'supports', 'fixture:a201', 'A201 fact version evidence', %s)
            """,
            (
                fact_version_id,
                source_document_id,
                Jsonb({"separate_evidence_layer": True}),
            ),
        )
        layer_row = connection.execute(
            """
            SELECT ds.snapshot_key, fv.object_type, fv.version_no, fv.valid_from,
                   fv.observed_at, fve.role, fv.payload->>'relationship_family'
            FROM fact_versions fv
            JOIN data_snapshots ds ON ds.id = fv.snapshot_id
            JOIN fact_version_evidence fve ON fve.fact_version_id = fv.id
            WHERE fv.id = %s
            """,
            (fact_version_id,),
        ).fetchone()
        assert layer_row[0] == "a201-fixture-snapshot"
        assert layer_row[1] == "relationship"
        assert layer_row[2] == 1
        assert layer_row[3] is not None
        assert layer_row[4] is not None
        assert layer_row[5] == "supports"
        assert layer_row[6] == "supply_chain_operations"
        connection.commit()

        try:
            connection.execute(
                """
                INSERT INTO data_snapshots(
                  snapshot_key, scope, record_mode, status, source_hash, as_of, activated_at
                )
                VALUES (
                  'a201-duplicate-active',
                  'golden-vertical:nvidia',
                  'fixture',
                  'active',
                  'a201-duplicate',
                  '2026-06-20T00:00:00Z',
                  '2026-06-20T00:00:01Z'
                )
                """
            )
        except errors.UniqueViolation:
            connection.rollback()
        else:  # pragma: no cover - should be unreachable with the partial unique index.
            raise AssertionError("Only one active snapshot per scope and record_mode is allowed")

        try:
            connection.execute(
                """
                INSERT INTO fact_versions(
                  snapshot_id, object_type, object_id, version_no, fact_status, record_mode,
                  valid_from, valid_to, observed_at, payload_hash, payload
                )
                VALUES (
                  %s,
                  'relationship',
                  %s,
                  2,
                  'reported',
                  'fixture',
                  '2026-06-20T00:00:00Z',
                  '2026-06-19T00:00:00Z',
                  '2026-06-20T00:00:00Z',
                  'a201-invalid-window',
                  %s
                )
                """,
                (
                    snapshot_id,
                    COREWEAVE_NVIDIA_RELATIONSHIP_ID,
                    Jsonb({"invalid": "valid_to_before_valid_from"}),
                ),
            )
        except errors.CheckViolation:
            connection.rollback()
        else:  # pragma: no cover - should be unreachable with the time-validity check.
            raise AssertionError("Fact versions must reject invalid valid_from/valid_to windows")


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
    nvidia_dossier = entity_lookup.json()
    assert nvidia_dossier["primary_identifiers"]["TICKER"] == "NVDA"
    assert nvidia_dossier["focus_route"] == f"/v1/entities/{NVIDIA_ID}"
    assert nvidia_dossier["ui_route"] == f"/?focus=entity:{NVIDIA_ID}"
    assert nvidia_dossier["coverage"]["entity_focus_page_openable"] is True
    assert set(nvidia_dossier["human_summary"]) >= DOSSIER_HUMAN_SUMMARY_KEYS
    assert nvidia_dossier["coverage"]["human_summary_dimensions_present"] == {
        "business": True,
        "group": True,
        "dependencies": True,
        "capital": True,
        "policy": True,
        "signals": True,
        "data_gaps": True,
    }
    assert nvidia_dossier["dossier_layers"]["business"]["relationship_count"] >= 1
    assert nvidia_dossier["dossier_layers"]["group"]["relationship_count"] >= 1
    assert nvidia_dossier["dossier_layers"]["dependencies"]["relationship_count"] >= 1
    assert nvidia_dossier["dossier_layers"]["signals"]["relationship_count"] >= 1
    assert nvidia_dossier["relationships_summary"]["supply_chain_operations"] >= 3
    gap_dimensions = {
        gap["dimension"] for gap in nvidia_dossier["human_summary"]["data_gaps"]
    }
    assert {"capital", "policy"} <= gap_dimensions
    gap_messages = " ".join(
        gap["message"] for gap in nvidia_dossier["human_summary"]["data_gaps"]
    )
    assert "unknown, not zero" in gap_messages

    seed_entities = json.loads(Path("data/mock_entities.json").read_text(encoding="utf-8"))
    assert len(seed_entities) == 30
    for seed_entity in seed_entities:
        seed_response = client.get(f"/v1/entities/{seed_entity['id']}")
        assert seed_response.status_code == 200
        seed_dossier = seed_response.json()
        assert seed_dossier["id"] == seed_entity["id"]
        assert seed_dossier["coverage"]["entity_focus_page_openable"] is True
        assert set(seed_dossier["human_summary"]) >= DOSSIER_HUMAN_SUMMARY_KEYS

    empire_response = client.get(f"/v1/entities/{NVIDIA_ID}/empire")
    assert empire_response.status_code == 200
    nvidia_empire = empire_response.json()
    assert nvidia_empire["focus"]["id"] == NVIDIA_ID
    assert [layer["key"] for layer in nvidia_empire["workspace_layers"]] == (
        EMPIRE_WORKSPACE_LAYER_KEYS
    )
    assert nvidia_empire["coverage"]["required_workspace_layer_count"] == 8
    assert nvidia_empire["coverage"]["required_workspace_layers_present"] is True
    assert nvidia_empire["coverage"][
        "separates_legal_group_segment_brand_product_facility"
    ] is True
    assert nvidia_empire["coverage"]["commercial_empire_control_claim"] is False
    assert nvidia_empire["content_rules"]["commercial_empire_is_legal_control"] is False
    assert "not a legal-control assertion" in nvidia_empire["content_rules"][
        "commercial_empire_label"
    ]

    structure = nvidia_empire["structure"]
    assert set(structure) >= {
        "legal_group",
        "business_segments",
        "brands",
        "products",
        "facilities",
    }
    assert structure["legal_group"]["items"][0]["relationship"][
        "relationship_type"
    ] == "focus_entity"
    segment_names = {
        item["entity"]["canonical_name"] for item in structure["business_segments"]["items"]
    }
    assert "Accelerated Computing Segment (Synthetic)" in segment_names
    product_names = {item["entity"]["canonical_name"] for item in structure["products"]["items"]}
    assert "AI Accelerator Platform (Synthetic)" in product_names
    assert structure["brands"]["data_status"] == "missing"
    facility_item = next(
        item
        for item in structure["facilities"]["items"]
        if item["entity"]["canonical_name"] == "Synthetic AI Data Center Campus"
    )
    assert facility_item["relationship_scope"] == "adjacent_ecosystem"
    assert "no focus ownership or operation claim" in facility_item["control_semantics"]

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

    inherited_reroot_response = client.post(
        "/v1/explore/reroot",
        json={
            "session_id": explicit_exploration["session_id"],
            "new_focus_entity_id": FIXTURE_DATACENTER_ID,
        },
    )
    assert inherited_reroot_response.status_code == 200
    inherited_reroot = inherited_reroot_response.json()
    assert inherited_reroot["focus"]["canonical_name"] == "Synthetic AI Data Center Campus"
    assert inherited_reroot["state"]["focus"] == {
        "object_type": "entity",
        "object_id": FIXTURE_DATACENTER_ID,
    }
    assert inherited_reroot["state"]["active_layers"] == [
        "capital_control",
        "policy_regulatory",
    ]
    assert inherited_reroot["state"]["direction"] == "upstream"
    assert inherited_reroot["state"]["hops"] == 2
    assert inherited_reroot["state"]["as_of"] == "2026-06-19T00:00:00Z"
    assert inherited_reroot["state"]["scoring_profile_version_id"] == profile_id
    assert inherited_reroot["state"]["filters"] == {
        "relationship_family": ["capital_financing"]
    }
    assert inherited_reroot["state"]["budget"] == {
        "max_nodes": 7,
        "max_edges": 8,
        "expand_nodes": 3,
    }
    assert inherited_reroot["history"][-1]["action"] == "reroot"
    assert inherited_reroot["history"][-1]["inherited_state"]["inherit_state"] is True

    reset_reroot_response = client.post(
        "/v1/explore/reroot",
        json={
            "session_id": explicit_exploration["session_id"],
            "new_focus_entity_id": THEME_AI_INFRA_ID,
            "inherit_state": False,
        },
    )
    assert reset_reroot_response.status_code == 200
    reset_reroot = reset_reroot_response.json()
    assert reset_reroot["focus"]["canonical_name"] == "AI Infrastructure"
    assert reset_reroot["state"]["focus"] == {
        "object_type": "entity",
        "object_id": THEME_AI_INFRA_ID,
    }
    assert reset_reroot["state"]["active_layers"] == ["supply_chain_operations"]
    assert reset_reroot["state"]["direction"] == "both"
    assert reset_reroot["state"]["hops"] == 1
    assert reset_reroot["state"]["as_of"] is None
    assert reset_reroot["state"]["scoring_profile_version_id"] is None
    assert reset_reroot["state"]["filters"] == {}
    assert reset_reroot["state"]["budget"] == {
        "max_nodes": 42,
        "max_edges": 64,
        "expand_nodes": 12,
    }
    assert reset_reroot["history"][-1]["inherited_state"]["inherit_state"] is False
    with connect_database() as connection:
        reset_session_row = connection.execute(
            """
            SELECT current_focus_entity_id, active_layers, direction, hops, budget,
                   as_of, scoring_profile_version_id, filters
            FROM exploration_sessions
            WHERE id = %s
            """,
            (explicit_exploration["session_id"],),
        ).fetchone()
    assert str(reset_session_row[0]) == THEME_AI_INFRA_ID
    assert reset_session_row[1] == ["supply_chain_operations"]
    assert reset_session_row[2] == "both"
    assert reset_session_row[3] == 1
    assert reset_session_row[4] == {"max_nodes": 42, "max_edges": 64, "expand_nodes": 12}
    assert reset_session_row[5] is None
    assert reset_session_row[6] is None
    assert reset_session_row[7] == {}

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
    expand_response = client.post(
        "/v1/explore/expand",
        json={
            "session_id": over_budget["session_id"],
            "anchor_entity_id": NVIDIA_ID,
            "direction": "upstream",
            "layers": ["supply_chain_operations"],
            "budget": {"max_nodes": 42, "max_edges": 64, "expand_nodes": 2},
        },
    )
    assert expand_response.status_code == 200
    expanded = expand_response.json()
    assert expanded["session_id"] == over_budget["session_id"]
    assert expanded["focus"]["canonical_name"] == "NVIDIA Corporation"
    assert expanded["query"]["direction"] == "upstream"
    assert expanded["query"]["active_layers"] == ["supply_chain_operations"]
    assert expanded["query"]["budget"]["expand_nodes"] == 2
    assert 1 <= len(expanded["edges"]) <= 2
    assert len(expanded["nodes"]) <= 3
    assert all(edge["object_id"] == NVIDIA_ID for edge in expanded["edges"])
    assert all(
        edge["relationship_family"] == "supply_chain_operations"
        for edge in expanded["edges"]
    )

    path_cases = [
        ("shortest", FIXTURE_MATERIALS_ID, NVIDIA_ID, 3, "supply_chain_operations"),
        ("upstream", FIXTURE_MATERIALS_ID, NVIDIA_ID, 3, "supply_chain_operations"),
        ("downstream", NVIDIA_ID, FIXTURE_MATERIALS_ID, 3, "supply_chain_operations"),
        ("control", OPENAI_FOUNDATION_ID, OPENAI_GROUP_ID, 1, "ownership_control"),
        ("capital", MICROSOFT_ID, OPENAI_GROUP_ID, 1, "capital_financing"),
        ("policy", GOVERNMENT_BODY_ID, PALANTIR_ID, 1, "government_policy"),
        ("bottleneck", FIXTURE_MATERIALS_ID, NVIDIA_ID, 3, "supply_chain_operations"),
    ]
    for path_type, source_id, target_id, max_length, expected_family in path_cases:
        path_response = client.get(
            "/v1/paths",
            params={
                "from": source_id,
                "to": target_id,
                "path_type": path_type,
                "max_length": max_length,
                "as_of": "2026-06-19T00:00:00Z",
            },
        )
        assert path_response.status_code == 200
        path_payload = path_response.json()
        assert path_payload["query"]["path_type"] == path_type
        assert path_payload["query"]["max_length"] == max_length
        assert path_payload["query"]["hard_limits"]["max_path_length"] == 8
        assert path_payload["query"]["max_paths"] == 8
        assert path_payload["query"]["from"] == source_id
        assert path_payload["query"]["to"] == target_id
        assert path_payload["paths"][0]["node_ids"][0] == source_id
        assert path_payload["paths"][0]["node_ids"][-1] == target_id
        assert_evidence_bearing_paths(path_payload, max_length=max_length)
        assert all(
            edge["relationship_family"] == expected_family
            for path in path_payload["paths"]
            for edge in path["edges"]
        )
        if path_type == "bottleneck":
            assert path_payload["query"]["bottleneck_only"] is True
            assert all(
                edge["materiality"] in {"critical", "high"}
                for path in path_payload["paths"]
                for edge in path["edges"]
            )
    too_long_path_response = client.get(
        "/v1/paths",
        params={
            "from": FIXTURE_MATERIALS_ID,
            "to": NVIDIA_ID,
            "path_type": "shortest",
            "max_length": 9,
        },
    )
    assert too_long_path_response.status_code == 422

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
