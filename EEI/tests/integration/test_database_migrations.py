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
from apps.worker.app.main import run_worker_cycle, supervise_worker, worker_health_snapshot
from scripts.db_tools import connect_database, database_url
from scripts.job_scheduler import (
    complete_job,
    connect_job_database,
    dispatch_outbox_once,
    enqueue_job,
    fail_job,
    heartbeat_job,
    lease_next_job,
    recover_expired_leases,
    release_job,
    run_once,
    write_outbox_event,
)

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
NVIDIA_CAPEX_EVENT_ID = "30000000-0000-4000-8000-000000000002"
SUPERSESSION_RELATIONSHIP_ID = "20000000-0000-4000-8000-000000000001"
CURATED_ANCHOR_PARSER_VERSION = "nvidia-public-anchor-v1"
FULL_TEXT_DRY_RUN_PARSER_VERSION = "nvidia-official-fulltext-dry-run-v1"
OPERATOR_SOURCE_CAPTURE_PARSER_VERSION = "nvidia-operator-source-capture-v1"
REVIEWED_DECISION_SET_KEY = "a202-integration-reviewed-golden-vertical-v1"
REVIEWED_RELATIONSHIP_SNAPSHOT_KEY = "a202-reviewed-golden-vertical"
REVIEW_DECISION_FIXTURE_PATH = "tests/fixtures/golden_vertical_review_decisions.json"
OWNER_SIGNOFF_DECISION_SET_KEY = "a202-production-owner-signoff-contract-v1"
OWNER_SIGNOFF_SNAPSHOT_KEY = "a202-production-owner-signoff-golden-vertical"
OWNER_SIGNOFF_DECISION_FIXTURE_PATH = (
    "tests/fixtures/golden_vertical_owner_signoff_decisions.json"
)
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
    run_script("scripts/fetch_official_source_full_text.py")
    run_script("scripts/fetch_official_source_full_text.py")
    run_script("scripts/load_operator_source_captures.py")
    run_script("scripts/load_operator_source_captures.py")
    run_script(
        "scripts/check_database_schema.py",
        "--expect-seeds",
        "--expect-fixtures",
        "--expect-curated-ingestion",
    )
    exercise_curated_official_ingestion_contracts()
    exercise_official_full_text_dry_run_contracts()
    exercise_operator_source_capture_contracts()
    exercise_production_fact_version_contracts()
    exercise_domain_api_and_repository_contracts()
    exercise_reviewed_relationship_publication_contracts()
    exercise_background_scheduler_contracts()
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


def exercise_official_full_text_dry_run_contracts() -> None:
    with connect_database() as connection:
        parser_version = FULL_TEXT_DRY_RUN_PARSER_VERSION
        raw_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE record_mode = 'dry_run'),
                   count(*) FILTER (WHERE review_status = 'machine_verified'),
                   count(DISTINCT source_document_id),
                   min((raw_payload->'source_health'->'token_coverage'->>'ratio')::numeric),
                   count(*) FILTER (
                     WHERE (raw_payload->'retry_policy'->>'dead_letter_after_attempts')::int = 3
                   ),
                   count(*) FILTER (WHERE raw_payload->>'live_retrieval' = 'false'),
                   count(*) FILTER (WHERE raw_payload->>'release_clearance' = 'false')
            FROM raw_source_snapshots
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()
        assert raw_row[0:4] == (4, 4, 4, 4)
        assert float(raw_row[4]) == 1.0
        assert raw_row[5:8] == (4, 4, 4)

        latest_run = connection.execute(
            """
            SELECT status, counts->>'anchors', counts->>'entity_resolution_candidates',
                   counts->>'evidence_chain_rows', counts->>'source_health_status',
                   counts->>'live_retrieval', counts->>'release_clearance'
            FROM ingestion_runs
            WHERE connector_version = %s AND mode = 'dry_run'
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (parser_version,),
        ).fetchone()
        assert latest_run == ("succeeded", "4", "52", "4", "healthy", "false", "false")

        source_documents = connection.execute(
            """
            SELECT count(*)
            FROM source_documents sd
            JOIN raw_source_snapshots rss ON rss.source_document_id = sd.id
            WHERE rss.parser_version = %s
              AND sd.parser_version = %s
              AND sd.raw_storage_uri LIKE
                'tests/fixtures/official_source_full_text/nvidia_official_full_text_dry_run.json#%%'
              AND sd.content_hash = rss.content_hash
            """,
            (parser_version, parser_version),
        ).fetchone()[0]
        assert source_documents == 4

        candidate_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE confidence >= 0.72),
                   count(*) FILTER (WHERE matched_research_id IS NOT NULL),
                   count(*) FILTER (WHERE candidate_name = 'NVIDIA Corporation'),
                   count(*) FILTER (WHERE candidate_name = 'TSMC')
            FROM entity_resolution_candidates
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()
        assert candidate_row == (52, 13, 13, 4, 3)

        evidence_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE evidence_role = 'context'),
                   count(*) FILTER (WHERE review_status = 'machine_verified'),
                   count(*) FILTER (
                     WHERE structured_fact->>'edge_publication' =
                       'dry_run_context_only_not_published_relationship'
                   ),
                   count(*) FILTER (
                     WHERE structured_fact->'source_health'->>'status' = 'healthy'
                   ),
                   count(*) FILTER (
                     WHERE structured_fact->>'full_text_connector' = %s
                   )
            FROM ingestion_evidence_chain
            WHERE parser_version = %s
            """,
            (parser_version, parser_version),
        ).fetchone()
        assert evidence_row == (4, 4, 4, 4, 4, 4)

        dry_run_fact_candidates = connection.execute(
            """
            SELECT count(*)
            FROM relationship_fact_candidates
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()[0]
        assert dry_run_fact_candidates == 0


def exercise_operator_source_capture_contracts() -> None:
    with connect_database() as connection:
        parser_version = OPERATOR_SOURCE_CAPTURE_PARSER_VERSION
        raw_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE record_mode = 'operator_source_capture'),
                   count(*) FILTER (WHERE review_status = 'operator_verified'),
                   count(DISTINCT source_document_id),
                   min((raw_payload->'source_health'->'token_coverage'->>'ratio')::numeric),
                   count(*) FILTER (WHERE raw_payload->>'operator_supplied_capture' = 'true'),
                   count(*) FILTER (WHERE raw_payload->>'live_retrieval' = 'false'),
                   count(*) FILTER (WHERE raw_payload->>'release_clearance' = 'false'),
                   count(*) FILTER (WHERE raw_payload->>'relationship_publication' = 'false')
            FROM raw_source_snapshots
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()
        assert raw_row[0:4] == (2, 2, 2, 2)
        assert float(raw_row[4]) == 1.0
        assert raw_row[5:9] == (2, 2, 2, 2)

        latest_run = connection.execute(
            """
            SELECT status, counts->>'captures', counts->>'entity_resolution_candidates',
                   counts->>'evidence_chain_rows', counts->>'source_health_status',
                   counts->>'operator_supplied_capture', counts->>'live_retrieval',
                   counts->>'release_clearance', counts->>'relationship_publication'
            FROM ingestion_runs
            WHERE connector_version = %s AND mode = 'operator_source_capture'
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (parser_version,),
        ).fetchone()
        assert latest_run == (
            "succeeded",
            "2",
            "30",
            "2",
            "operator_verified",
            "true",
            "false",
            "false",
            "false",
        )

        source_documents = connection.execute(
            """
            SELECT count(*)
            FROM source_documents sd
            JOIN raw_source_snapshots rss ON rss.source_document_id = sd.id
            WHERE rss.parser_version = %s
              AND sd.parser_version = %s
              AND sd.raw_storage_uri LIKE
                'tests/fixtures/operator_source_captures/nvidia_operator_source_captures.json#%%'
              AND sd.content_hash = rss.content_hash
            """,
            (parser_version, parser_version),
        ).fetchone()[0]
        assert source_documents == 2

        candidate_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE confidence >= 0.72),
                   count(*) FILTER (WHERE matched_research_id IS NOT NULL),
                   count(*) FILTER (WHERE review_status = 'operator_verified'),
                   count(*) FILTER (WHERE candidate_name = 'NVIDIA Corporation'),
                   count(*) FILTER (WHERE candidate_name = 'TSMC')
            FROM entity_resolution_candidates
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()
        assert candidate_row[0] == 30
        assert candidate_row[1] >= 6
        assert candidate_row[2] >= 6
        assert candidate_row[3:6] == (30, 2, 2)

        evidence_row = connection.execute(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE evidence_role = 'context'),
                   count(*) FILTER (WHERE review_status = 'operator_verified'),
                   count(*) FILTER (
                     WHERE structured_fact->>'edge_publication' =
                       'operator_capture_context_only_not_published_relationship'
                   ),
                   count(*) FILTER (
                     WHERE structured_fact->'source_health'->>'status' =
                       'operator_verified'
                   ),
                   count(*) FILTER (
                     WHERE structured_fact->>'operator_source_capture' = %s
                   ),
                   count(*) FILTER (
                     WHERE structured_fact->>'release_clearance' = 'false'
                   )
            FROM ingestion_evidence_chain
            WHERE parser_version = %s
            """,
            (parser_version, parser_version),
        ).fetchone()
        assert evidence_row == (2, 2, 2, 2, 2, 2, 2)

        operator_fact_candidates = connection.execute(
            """
            SELECT count(*)
            FROM relationship_fact_candidates
            WHERE parser_version = %s
            """,
            (parser_version,),
        ).fetchone()[0]
        assert operator_fact_candidates == 0


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
    assert len(profiles) == 2
    active_profiles = [profile for profile in profiles if profile["active"] is True]
    inactive_profiles = [profile for profile in profiles if profile["active"] is False]
    assert len(active_profiles) == 1
    assert active_profiles[0]["profile_key"] == "balanced-v2"
    assert {profile["profile_key"] for profile in inactive_profiles} == {"supply-chain-v3"}
    with connect_database() as connection:
        candidate_row = connection.execute(
            """
            SELECT id, candidate_key
            FROM relationship_fact_candidates
            WHERE parser_version = %s
              AND structured_fact->>'path_role' = 'NVIDIA_TO_TSMC_GOLDEN_VERTICAL'
            """,
            (CURATED_ANCHOR_PARSER_VERSION,),
        ).fetchone()
    assert candidate_row is not None

    score_explanation_response = client.get(
        f"/v1/scoring/explain/relationship_fact_candidate/{candidate_row[0]}"
    )
    assert score_explanation_response.status_code == 200
    score_explanation = score_explanation_response.json()
    assert score_explanation["object_type"] == "relationship_fact_candidate"
    assert score_explanation["object_id"] == str(candidate_row[0])
    assert score_explanation["candidate_key"] == candidate_row[1]
    assert score_explanation["record_mode"] == "curated_official_fixture"
    assert score_explanation["publication_status"] == "candidate"
    assert score_explanation["source_threshold"] == {
        "minimum_independent_sources": 2,
        "independent_source_count": 1,
        "met": False,
    }
    assert score_explanation["raw_score"] > score_explanation["adjusted_score"] > 0
    assert score_explanation["evidence_quality"] == 50
    assert "human_review_verification" in score_explanation["missing_inputs"]
    assert "published_relationship_version" in score_explanation["missing_inputs"]
    assert score_explanation["profile_version"].startswith("balanced-v2@")
    assert score_explanation["model_version"]
    assert len(score_explanation["evidence"]) == 1
    assert score_explanation["evidence"][0]["url"].startswith("https://")
    assert score_explanation["review_queue"][0]["status"] == "open"
    score_context = score_explanation["production_context"]
    assert score_context["schema_version"] == "production-context-v1"
    assert score_context["scoring_service_version"] == "candidate-score-explanation-v1"
    assert score_context["publication_policy"][
        "relationship_fact_candidates_in_graph_edges"
    ] is False
    assert score_context["publication_policy"]["minimum_independent_sources"] == 2

    evidence_detail_response = client.get(
        f"/v1/evidence/relationship_fact_candidate/{candidate_row[0]}"
    )
    assert evidence_detail_response.status_code == 200
    evidence_detail = evidence_detail_response.json()
    assert evidence_detail["schema_version"] == "evidence-detail-v1"
    assert evidence_detail["object_type"] == "relationship_fact_candidate"
    assert evidence_detail["object_id"] == str(candidate_row[0])
    assert evidence_detail["object_summary"]["candidate_key"] == candidate_row[1]
    assert evidence_detail["evidence_count"] >= 1
    assert evidence_detail["returned_evidence_count"] >= 1
    assert evidence_detail["source_document_count"] >= 1
    assert evidence_detail["truncated"] is False
    score_source_document_ids = {
        row["source_document_id"] for row in score_explanation["evidence"]
    }
    detail_source_document_ids = {
        row["source_document_id"] for row in evidence_detail["evidence"]
    }
    assert score_source_document_ids <= detail_source_document_ids
    assert any(row["snippet"]["text"] for row in evidence_detail["evidence"])
    assert all(isinstance(row["structured_fact"], dict) for row in evidence_detail["evidence"])
    assert all(isinstance(row["counter_evidence"], list) for row in evidence_detail["evidence"])
    assert any(
        row["source_document"]["url"].startswith("https://") for row in evidence_detail["evidence"]
    )
    assert evidence_detail["production_context"]["schema_version"] == "production-context-v1"

    source_document_id = next(iter(score_source_document_ids))
    source_document_score_response = client.get(
        f"/v1/scoring/explain/source_document/{source_document_id}"
    )
    assert source_document_score_response.status_code == 200
    source_document_score = source_document_score_response.json()
    assert source_document_score["object_type"] == "source_document"
    assert source_document_score["object_id"] == source_document_id
    assert source_document_score["publication_status"] == "evidence_source"
    assert source_document_score["source_document"]["url"].startswith("https://")
    assert source_document_score["source_threshold"]["minimum_independent_sources"] == 1
    assert source_document_score["source_threshold"]["met"] is True
    assert source_document_score["coverage_summary"]["downstream_evidence_count"] >= 1
    assert source_document_score["coverage_summary"]["provenance_field_count"] >= 5
    assert source_document_score["evidence"][0]["source_document_id"] == source_document_id
    if source_document_score["fact_version"] is None:
        assert "source_document_fact_version" in source_document_score["missing_inputs"]

    relationship_evidence_response = client.get(
        f"/v1/evidence/relationship/{COREWEAVE_NVIDIA_RELATIONSHIP_ID}"
    )
    assert relationship_evidence_response.status_code == 200
    relationship_evidence = relationship_evidence_response.json()
    assert relationship_evidence["schema_version"] == "evidence-detail-v1"
    assert relationship_evidence["object_type"] == "relationship"
    assert relationship_evidence["object_id"] == COREWEAVE_NVIDIA_RELATIONSHIP_ID
    assert relationship_evidence["evidence_count"] >= 1
    assert relationship_evidence["source_document_count"] >= 1
    assert any(row["snippet"]["text"] for row in relationship_evidence["evidence"])
    assert all(
        isinstance(row["structured_fact"], dict) for row in relationship_evidence["evidence"]
    )
    assert all(
        isinstance(row["counter_evidence"], list) for row in relationship_evidence["evidence"]
    )
    assert "synthetic" in relationship_evidence["object_summary"]
    if relationship_evidence["object_summary"]["synthetic"]:
        assert relationship_evidence["object_summary"]["fixture_notice"]

    exercise_transactional_model_activation_contract(client, profiles[0])
    exercise_server_saved_view_contracts(client, profiles[0])

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

    industry_score_response = client.get(
        f"/v1/scoring/explain/industry/{semiconductor['id']}"
    )
    assert industry_score_response.status_code == 200
    industry_score = industry_score_response.json()
    assert industry_score["object_type"] == "industry"
    assert industry_score["object_id"] == semiconductor["id"]
    assert industry_score["publication_status"] == "published"
    assert industry_score["industry"]["slug"] == "semiconductors-electronics"
    assert industry_score["source_threshold"]["minimum_independent_sources"] == 1
    assert industry_score["source_threshold"]["independent_source_count"] >= 1
    assert industry_score["source_threshold"]["met"] is True
    assert industry_score["coverage_summary"]["entity_count"] >= 2
    assert industry_score["coverage_summary"]["child_industry_count"] >= 1
    assert industry_score["coverage_summary"]["relationship_count"] >= 3
    assert industry_score["coverage_summary"]["relationship_family_count"] >= 1
    assert industry_score["coverage_summary"]["taxonomy_context_present"] is True
    assert industry_score["evidence"]
    assert industry_score["evidence"][0]["url"].startswith("fixture://relationship/")
    assert "industry_independent_source_threshold>=1" not in industry_score[
        "missing_inputs"
    ]
    if industry_score["fact_version"] is None:
        assert "industry_fact_version" in industry_score["missing_inputs"]

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

    entity_score_response = client.get(f"/v1/scoring/explain/entity/{NVIDIA_ID}")
    assert entity_score_response.status_code == 200
    entity_score = entity_score_response.json()
    assert entity_score["object_type"] == "entity"
    assert entity_score["object_id"] == NVIDIA_ID
    assert entity_score["publication_status"] == "published"
    assert entity_score["entity"]["canonical_name"] == "NVIDIA Corporation"
    assert entity_score["entity"]["entity_type"] == "legal_entity"
    assert entity_score["source_threshold"]["minimum_independent_sources"] == 1
    assert entity_score["source_threshold"]["independent_source_count"] >= 1
    assert entity_score["source_threshold"]["met"] is True
    assert entity_score["coverage_summary"]["relationship_count"] >= 1
    assert entity_score["coverage_summary"]["relationship_family_count"] >= 1
    assert entity_score["coverage_summary"]["industry_membership_count"] >= 1
    assert entity_score["evidence"]
    assert entity_score["evidence"][0]["url"].startswith("fixture://relationship/")
    assert "entity_identifier" not in entity_score["missing_inputs"]
    assert "relationship_context" not in entity_score["missing_inputs"]
    if entity_score["fact_version"] is None:
        assert "entity_fact_version" in entity_score["missing_inputs"]
    assert entity_score["production_context"]["schema_version"] == "production-context-v1"
    assert (
        entity_score["scoring_service_version"]
        == "candidate-score-explanation-v1"
    )

    event_score_response = client.get(
        f"/v1/scoring/explain/event/{NVIDIA_CAPEX_EVENT_ID}"
    )
    assert event_score_response.status_code == 200
    event_score = event_score_response.json()
    assert event_score["object_type"] == "event"
    assert event_score["object_id"] == NVIDIA_CAPEX_EVENT_ID
    assert event_score["publication_status"] == "published"
    assert event_score["event"]["event_type"] == "capital_expenditure"
    assert event_score["event"]["amount"] == 1000000000
    assert event_score["event"]["currency"] == "USD"
    assert event_score["event"]["amount_kind"] == "period_capex"
    assert event_score["source_threshold"]["minimum_independent_sources"] == 1
    assert event_score["source_threshold"]["independent_source_count"] >= 1
    assert event_score["source_threshold"]["met"] is True
    assert event_score["coverage_summary"]["participant_count"] >= 1
    assert event_score["coverage_summary"]["source_document_count"] >= 1
    assert event_score["coverage_summary"]["timing_context_present"] is True
    assert event_score["coverage_summary"]["amount_semantics_present"] is True
    assert event_score["participants"]
    assert event_score["evidence"]
    assert event_score["evidence"][0]["url"].startswith("fixture://event/")
    assert "event_participant_context>=1" not in event_score["missing_inputs"]
    assert "event_amount_semantics" not in event_score["missing_inputs"]
    if event_score["fact_version"] is None:
        assert "event_fact_version" in event_score["missing_inputs"]
    assert event_score["production_context"]["schema_version"] == "production-context-v1"

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
    production_context = exploration["production_context"]
    assert production_context["schema_version"] == "production-context-v1"
    assert production_context["graph_query_version"] == "bounded-recursive-graph-v1"
    assert production_context["active_scoring_profile"]["profile_key"] == "balanced-v2"
    assert production_context["publication_policy"][
        "relationship_fact_candidates_in_graph_edges"
    ] is False
    assert production_context["record_modes"]["relationship_fact_candidates"][
        "curated_official_fixture"
    ] == 2
    assert exploration["coverage"]["relationship_fact_candidates"][
        "excluded_from_graph_edges"
    ] >= 1
    assert all(
        edge["id"] != score_explanation["object_id"] for edge in exploration["edges"]
    )

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
        assert path_payload["production_context"]["graph_query_version"] == (
            "bounded-recursive-graph-v1"
        )
        assert path_payload["production_context"]["publication_policy"][
            "relationship_fact_candidates_in_graph_edges"
        ] is False
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
    calibration_payload = calibration_response.json()
    assert calibration_payload["cadence_days"] == 14
    assert calibration_payload["schema_version"] == "calibration-run-request-v1"
    assert calibration_payload["job"]["job_type"] == "calibration_run"
    assert calibration_payload["job"]["payload"]["schema_version"] == "calibration-run-job-v1"
    assert calibration_payload["job"]["payload"]["calibration_run_id"] == calibration_payload["id"]
    assert calibration_payload["outbox_event"]["event_type"] == "calibration.run.requested"
    assert calibration_payload["activation_policy"]["auto_activation_enabled"] is False
    home_after_calibration = client.get("/v1/home").json()
    calibration_status = home_after_calibration["model_status"]["calibration"]
    assert calibration_status["latest_status"] == "scheduled"
    assert calibration_status["next_scheduled_for"]

    executed_calibration = run_once(
        worker_id="a206-calibration-worker",
        job_type="calibration_run",
    )
    assert executed_calibration is not None
    assert executed_calibration["id"] == calibration_payload["job"]["id"]
    assert executed_calibration["status"] == "succeeded"
    calibration_result = executed_calibration["metadata"]["result"]
    assert calibration_result["handler"] == "calibration_run"
    assert calibration_result["handler_contract"] == "calibration-run-worker-v1"
    assert calibration_result["calibration_run_id"] == calibration_payload["id"]
    assert calibration_result["calibration_status"] in {"passed", "warning"}
    assert calibration_result["proposal_status"] == "none"
    assert calibration_result["drift_report"]["auto_activation_enabled"] is False
    assert calibration_result["metrics"]["relationship_fact_candidates"]["total"] >= 2
    assert calibration_result["outbox_event"]["event_type"] == "calibration.run.completed"
    calibration_list = client.get("/v1/calibrations")
    assert calibration_list.status_code == 200
    assert calibration_list.json()[0]["status"] in {"passed", "warning"}
    assert calibration_list.json()[0]["proposal_status"] == "none"

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


def reviewed_publication_counts(
    *,
    decision_set_key: str = REVIEWED_DECISION_SET_KEY,
    snapshot_key: str = REVIEWED_RELATIONSHIP_SNAPSHOT_KEY,
) -> tuple[int, int, int, int]:
    with connect_database() as connection:
        return connection.execute(
            """
            SELECT
              (
                SELECT count(*)::int
                FROM relationships
                WHERE qualifiers->>'decision_set_key' = %s
              ) AS relationship_count,
              (
                SELECT count(*)::int
                FROM relationship_evidence re
                JOIN relationships r ON r.id = re.relationship_id
                WHERE r.qualifiers->>'decision_set_key' = %s
              ) AS relationship_evidence_count,
              (
                SELECT count(*)::int
                FROM fact_versions fv
                JOIN data_snapshots ds ON ds.id = fv.snapshot_id
                WHERE ds.snapshot_key = %s
              ) AS fact_version_count,
              (
                SELECT count(*)::int
                FROM fact_version_evidence fve
                JOIN fact_versions fv ON fv.id = fve.fact_version_id
                JOIN data_snapshots ds ON ds.id = fv.snapshot_id
                WHERE ds.snapshot_key = %s
              ) AS fact_version_evidence_count
            """,
            (
                decision_set_key,
                decision_set_key,
                snapshot_key,
                snapshot_key,
            ),
        ).fetchone()


def exercise_reviewed_relationship_publication_contracts() -> None:
    run_script(
        "scripts/publish_reviewed_relationship_facts.py",
        "--review-decisions",
        REVIEW_DECISION_FIXTURE_PATH,
        "--snapshot-key",
        REVIEWED_RELATIONSHIP_SNAPSHOT_KEY,
        "--allow-fixture-review",
    )
    with connect_database() as connection:
        candidate_gate_row = connection.execute(
            """
            SELECT count(*)::int,
                   count(*) FILTER (WHERE publication_status = 'published')::int,
                   count(*) FILTER (WHERE source_threshold_met = true)::int,
                   count(*) FILTER (WHERE review_status = 'human_verified')::int,
                   count(*) FILTER (
                     WHERE structured_fact->>'published_relationship_id' IS NOT NULL
                   )::int
            FROM relationship_fact_candidates
            WHERE candidate_key IN ('GV-FACT-001', 'GV-FACT-002')
            """
        ).fetchone()
        assert candidate_gate_row == (2, 2, 2, 2, 2)

        review_queue_row = connection.execute(
            """
            SELECT count(*)::int,
                   count(*) FILTER (WHERE mrq.status = 'resolved')::int,
                   count(*) FILTER (WHERE mrq.reviewer = 'integration-test-reviewer')::int,
                   count(*) FILTER (WHERE mrq.decision = 'approved_for_publication')::int
            FROM manual_review_queue mrq
            JOIN relationship_fact_candidates rfc ON rfc.id = mrq.object_id
            WHERE rfc.candidate_key IN ('GV-FACT-001', 'GV-FACT-002')
            """
        ).fetchone()
        assert review_queue_row == (2, 2, 2, 2)

        relationship_rows = connection.execute(
            """
            SELECT r.id, r.relationship_type, r.relationship_family, r.qualifiers,
                   count(re.source_document_id)::int
            FROM relationships r
            JOIN relationship_evidence re ON re.relationship_id = r.id
            WHERE r.qualifiers->>'decision_set_key' = %s
            GROUP BY r.id, r.relationship_type, r.relationship_family, r.qualifiers
            ORDER BY r.relationship_type
            """,
            (REVIEWED_DECISION_SET_KEY,),
        ).fetchall()
        assert len(relationship_rows) == 2
        assert {row[1] for row in relationship_rows} == {
            "equipment_provider_to",
            "wafer_foundry_for",
        }
        for row in relationship_rows:
            qualifiers = row[3]
            assert row[4] == 1
            assert qualifiers["record_mode"] == "curated_official_fixture"
            assert qualifiers["fixture_review_only_not_production_clearance"] is True
            assert qualifiers["source_threshold_policy"]["independent_source_count"] == 1
            assert qualifiers["source_threshold_policy"]["met_by_review_override"] is True

        relationship_evidence_row = connection.execute(
            """
            SELECT count(*)::int,
                   count(*) FILTER (
                     WHERE re.structured_fact->>'publisher_version'
                       = 'a202-reviewed-publication-v1'
                   )::int,
                   count(*) FILTER (
                     WHERE re.structured_fact->>'fixture_review_only_not_production_clearance'
                       = 'true'
                   )::int,
                   count(*) FILTER (WHERE sd.url LIKE 'https://%%')::int
            FROM relationship_evidence re
            JOIN relationships r ON r.id = re.relationship_id
            JOIN source_documents sd ON sd.id = re.source_document_id
            WHERE r.qualifiers->>'decision_set_key' = %s
            """,
            (REVIEWED_DECISION_SET_KEY,),
        ).fetchone()
        assert relationship_evidence_row == (2, 2, 2, 2)

        materialized_entities = connection.execute(
            """
            SELECT count(*)::int
            FROM company_research_universe cru
            JOIN entities e ON e.id = cru.entity_id
            WHERE cru.research_id IN ('X-001', 'X-002')
              AND e.entity_type = 'legal_entity'
              AND e.status = 'research_target'
            """
        ).fetchone()[0]
        assert materialized_entities == 2

        snapshot_row = connection.execute(
            """
            SELECT ds.snapshot_key, ds.scope, ds.record_mode, ds.status,
                   ds.metadata->>'acceptance_id',
                   ds.metadata->>'fixture_review_only_not_production_clearance',
                   count(DISTINCT fv.id)::int,
                   count(fve.*)::int
            FROM data_snapshots ds
            JOIN fact_versions fv ON fv.snapshot_id = ds.id
            JOIN fact_version_evidence fve ON fve.fact_version_id = fv.id
            WHERE ds.snapshot_key = %s
            GROUP BY ds.id
            """,
            (REVIEWED_RELATIONSHIP_SNAPSHOT_KEY,),
        ).fetchone()
        assert snapshot_row[:6] == (
            REVIEWED_RELATIONSHIP_SNAPSHOT_KEY,
            "golden-vertical:nvidia",
            "curated_official_fixture",
            "active",
            "A202",
            "true",
        )
        assert snapshot_row[6:] == (2, 2)

        fact_version_payload_row = connection.execute(
            """
            SELECT count(*)::int,
                   count(*) FILTER (WHERE fv.payload->>'publication_status' = 'published')::int,
                   count(*) FILTER (WHERE fv.payload->>'review_status' = 'human_verified')::int,
                   count(*) FILTER (WHERE fv.parser_version = 'a202-reviewed-publication-v1')::int
            FROM fact_versions fv
            JOIN data_snapshots ds ON ds.id = fv.snapshot_id
            WHERE ds.snapshot_key = %s
            """,
            (REVIEWED_RELATIONSHIP_SNAPSHOT_KEY,),
        ).fetchone()
        assert fact_version_payload_row == (2, 2, 2, 2)

        candidate_id, relationship_id = connection.execute(
            """
            SELECT id, structured_fact->>'published_relationship_id'
            FROM relationship_fact_candidates
            WHERE candidate_key = 'GV-FACT-001'
            """
        ).fetchone()
        assert relationship_id is not None

    client = TestClient(app)
    score_response = client.get(f"/v1/scoring/explain/relationship_fact_candidate/{candidate_id}")
    assert score_response.status_code == 200
    score = score_response.json()
    assert score["publication_status"] == "published"
    assert score["source_threshold"] == {
        "minimum_independent_sources": 2,
        "independent_source_count": 1,
        "met": True,
    }
    assert score["review_status"] == "human_verified"
    assert "human_review_verification" not in score["missing_inputs"]
    assert "published_relationship_version" not in score["missing_inputs"]
    assert score["review_queue"][0]["status"] == "resolved"

    relationship_score_response = client.get(f"/v1/scoring/explain/relationship/{relationship_id}")
    assert relationship_score_response.status_code == 200
    relationship_score = relationship_score_response.json()
    assert relationship_score["object_type"] == "relationship"
    assert relationship_score["object_id"] == relationship_id
    assert relationship_score["relationship_status"] == "reported"
    assert relationship_score["publication_status"] == "published"
    assert relationship_score["review_status"] == "human_verified"
    assert relationship_score["source_threshold"] == {
        "minimum_independent_sources": 2,
        "independent_source_count": 1,
        "met": True,
    }
    assert relationship_score["fact_version"]["snapshot_key"] == REVIEWED_RELATIONSHIP_SNAPSHOT_KEY
    assert relationship_score["fact_version"]["parser_version"] == "a202-reviewed-publication-v1"
    assert relationship_score["production_context"]["schema_version"] == "production-context-v1"
    assert relationship_score["production_context"]["publication_policy"][
        "relationship_fact_candidates_in_graph_edges"
    ] is False
    assert relationship_score["evidence"][0]["url"].startswith("https://")
    assert relationship_score["evidence"][0]["structured_fact"]["publisher_version"] == (
        "a202-reviewed-publication-v1"
    )
    assert "human_review_verification" not in relationship_score["missing_inputs"]
    assert "published_relationship_version" not in relationship_score["missing_inputs"]
    assert "relationship_fact_version" not in relationship_score["missing_inputs"]

    before_counts = reviewed_publication_counts()
    run_script(
        "scripts/publish_reviewed_relationship_facts.py",
        "--review-decisions",
        REVIEW_DECISION_FIXTURE_PATH,
        "--snapshot-key",
        REVIEWED_RELATIONSHIP_SNAPSHOT_KEY,
        "--allow-fixture-review",
    )
    assert reviewed_publication_counts() == before_counts

    owner_without_gate = subprocess.run(
        [
            sys.executable,
            "scripts/publish_reviewed_relationship_facts.py",
            "--review-decisions",
            OWNER_SIGNOFF_DECISION_FIXTURE_PATH,
            "--snapshot-key",
            OWNER_SIGNOFF_SNAPSHOT_KEY,
        ],
        cwd=os.getcwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert owner_without_gate.returncode != 0
    assert "--allow-production-owner-signoff" in owner_without_gate.stderr

    run_script(
        "scripts/publish_reviewed_relationship_facts.py",
        "--review-decisions",
        OWNER_SIGNOFF_DECISION_FIXTURE_PATH,
        "--snapshot-key",
        OWNER_SIGNOFF_SNAPSHOT_KEY,
        "--allow-production-owner-signoff",
    )
    with connect_database() as connection:
        owner_snapshot_row = connection.execute(
            """
            SELECT ds.snapshot_key,
                   ds.record_mode,
                   ds.status,
                   ds.metadata->>'review_context',
                   ds.metadata->>'production_owner_signoff',
                   ds.metadata->>'fixture_review_only_not_production_clearance',
                   count(DISTINCT fv.id)::int,
                   count(fve.*)::int
            FROM data_snapshots ds
            JOIN fact_versions fv ON fv.snapshot_id = ds.id
            JOIN fact_version_evidence fve ON fve.fact_version_id = fv.id
            WHERE ds.snapshot_key = %s
            GROUP BY ds.id
            """,
            (OWNER_SIGNOFF_SNAPSHOT_KEY,),
        ).fetchone()
        assert owner_snapshot_row[:6] == (
            OWNER_SIGNOFF_SNAPSHOT_KEY,
            "curated_official_fixture",
            "active",
            "production_owner_signoff_contract",
            "true",
            "false",
        )
        assert owner_snapshot_row[6:] == (2, 2)

        owner_relationship_rows = connection.execute(
            """
            SELECT count(*)::int,
                   count(*) FILTER (
                     WHERE qualifiers->>'production_owner_signoff' = 'true'
                   )::int,
                   count(*) FILTER (
                     WHERE qualifiers->>'owner_actor' = 'eei-production-data-owner'
                   )::int,
                   count(*) FILTER (
                     WHERE qualifiers->>'authority_scope' = 'golden-vertical:nvidia'
                   )::int,
                   count(*) FILTER (
                     WHERE qualifiers->>'owner_signature_hash' IS NOT NULL
                   )::int
            FROM relationships
            WHERE qualifiers->>'decision_set_key' = %s
            """,
            (OWNER_SIGNOFF_DECISION_SET_KEY,),
        ).fetchone()
        assert owner_relationship_rows == (2, 2, 2, 2, 2)

        owner_evidence_row = connection.execute(
            """
            SELECT count(*)::int,
                   count(*) FILTER (
                     WHERE re.structured_fact->>'production_owner_signoff' = 'true'
                   )::int,
                   count(*) FILTER (
                     WHERE re.structured_fact->>'owner_role' = 'data_owner'
                   )::int,
                   count(*) FILTER (
                     WHERE re.structured_fact->>'owner_signature_hash' IS NOT NULL
                   )::int
            FROM relationship_evidence re
            JOIN relationships r ON r.id = re.relationship_id
            WHERE r.qualifiers->>'decision_set_key' = %s
            """,
            (OWNER_SIGNOFF_DECISION_SET_KEY,),
        ).fetchone()
        assert owner_evidence_row == (2, 2, 2, 2)

        owner_fact_payload_row = connection.execute(
            """
            SELECT count(*)::int,
                   count(*) FILTER (
                     WHERE fv.payload->'qualifiers'->>'production_owner_signoff' = 'true'
                   )::int,
                   count(*) FILTER (
                     WHERE fv.payload->'qualifiers'->>'owner_role' = 'data_owner'
                   )::int
            FROM fact_versions fv
            JOIN data_snapshots ds ON ds.id = fv.snapshot_id
            WHERE ds.snapshot_key = %s
            """,
            (OWNER_SIGNOFF_SNAPSHOT_KEY,),
        ).fetchone()
        assert owner_fact_payload_row == (2, 2, 2)

        owner_queue_row = connection.execute(
            """
            SELECT count(*)::int,
                   count(*) FILTER (
                     WHERE mrq.status = 'resolved'
                       AND mrq.reviewer = 'production-data-owner-contract'
                   )::int
            FROM manual_review_queue mrq
            JOIN relationship_fact_candidates rfc ON rfc.id = mrq.object_id
            WHERE rfc.candidate_key IN ('GV-FACT-001', 'GV-FACT-002')
            """
        ).fetchone()
        assert owner_queue_row == (2, 2)

    owner_before_counts = reviewed_publication_counts(
        decision_set_key=OWNER_SIGNOFF_DECISION_SET_KEY,
        snapshot_key=OWNER_SIGNOFF_SNAPSHOT_KEY,
    )
    run_script(
        "scripts/publish_reviewed_relationship_facts.py",
        "--review-decisions",
        OWNER_SIGNOFF_DECISION_FIXTURE_PATH,
        "--snapshot-key",
        OWNER_SIGNOFF_SNAPSHOT_KEY,
        "--allow-production-owner-signoff",
    )
    assert (
        reviewed_publication_counts(
            decision_set_key=OWNER_SIGNOFF_DECISION_SET_KEY,
            snapshot_key=OWNER_SIGNOFF_SNAPSHOT_KEY,
        )
        == owner_before_counts
    )


def exercise_server_saved_view_contracts(
    client: TestClient,
    active_profile: dict[str, object],
) -> None:
    state_v1 = {
        "focus": {"object_type": "entity", "object_id": NVIDIA_ID},
        "active_layers": ["supply_chain_operations", "technology_data_ip"],
        "direction": "both",
        "hops": 1,
        "budget": {"max_nodes": 42, "max_edges": 64, "expand_nodes": 12},
        "filters": {"relationship_family": ["supply_chain_operations"]},
        "visual_lens": "supply_chain",
        "workspace_mode": "split",
        "notes": "A207 server-side saved view baseline",
        "scoring_profile_version_id": active_profile["id"],
    }
    create_response = client.post(
        "/v1/saved-views",
        json={
            "name": "A207 Golden Vertical saved view",
            "description": "server contract baseline",
            "workspace_key": "mvp",
            "state": state_v1,
            "change_note": "A207 create version 1",
            "metadata": {"acceptance_id": "A207", "task_id": "T1305"},
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    saved_view_id = created["id"]
    assert created["schema_version"] == "saved-view-v1"
    assert created["current_version"] == 1
    assert created["version_count"] == 1
    assert created["versions"][0]["version_no"] == 1
    assert created["versions"][0]["action_type"] == "create"
    assert created["state"]["visual_lens"] == "supply_chain"
    assert created["namespace"] == "local_user"
    assert created["created_by"] == "local_user"

    namespace_headers = {
        "X-EEI-User-Namespace": "tenant-beta",
        "X-EEI-Actor": "tenant-beta-analyst",
    }
    isolated_create_response = client.post(
        "/v1/saved-views",
        headers=namespace_headers,
        json={
            "name": "A207 Golden Vertical saved view",
            "description": "same name in isolated namespace",
            "workspace_key": "mvp",
            "state": {**state_v1, "notes": "A207 isolated namespace"},
            "change_note": "A207 create isolated namespace version 1",
            "metadata": {"acceptance_id": "A207", "namespace": "tenant-beta"},
        },
    )
    assert isolated_create_response.status_code == 201
    isolated = isolated_create_response.json()
    assert isolated["id"] != saved_view_id
    assert isolated["namespace"] == "tenant-beta"
    assert isolated["created_by"] == "tenant-beta-analyst"

    foreign_detail_response = client.get(
        f"/v1/saved-views/{saved_view_id}",
        headers=namespace_headers,
    )
    assert foreign_detail_response.status_code == 404

    foreign_version_response = client.get(
        f"/v1/saved-views/{saved_view_id}/versions",
        headers=namespace_headers,
    )
    assert foreign_version_response.status_code == 404

    foreign_update_response = client.put(
        f"/v1/saved-views/{saved_view_id}",
        headers=namespace_headers,
        json={
            "expected_version": 1,
            "state": {**state_v1, "visual_lens": "foreign_update_attempt"},
            "change_note": "cross-namespace update should fail closed",
        },
    )
    assert foreign_update_response.status_code == 404

    foreign_restore_response = client.post(
        f"/v1/saved-views/{saved_view_id}/restore",
        headers=namespace_headers,
        json={
            "target_version": 1,
            "expected_version": 1,
            "change_note": "cross-namespace restore should fail closed",
        },
    )
    assert foreign_restore_response.status_code == 404

    duplicate_response = client.post(
        "/v1/saved-views",
        json={
            "name": "A207 Golden Vertical saved view",
            "workspace_key": "mvp",
            "state": state_v1,
        },
    )
    assert duplicate_response.status_code == 409
    duplicate_detail = duplicate_response.json()["detail"]
    assert duplicate_detail["reason"] == "saved_view_name_exists"
    assert duplicate_detail["actual_version"] == 1

    list_response = client.get("/v1/saved-views", params={"workspace_key": "mvp"})
    assert list_response.status_code == 200
    listed = list_response.json()
    assert any(row["id"] == saved_view_id for row in listed)
    assert all(row["id"] != isolated["id"] for row in listed)

    isolated_list_response = client.get(
        "/v1/saved-views",
        headers=namespace_headers,
        params={"workspace_key": "mvp"},
    )
    assert isolated_list_response.status_code == 200
    isolated_list = isolated_list_response.json()
    assert [row["id"] for row in isolated_list] == [isolated["id"]]

    state_v2 = {
        **state_v1,
        "visual_lens": "capital_transactions",
        "notes": "A207 updated view from second client",
        "filters": {"relationship_family": ["capital_financing"]},
    }
    update_response = client.put(
        f"/v1/saved-views/{saved_view_id}",
        json={
            "expected_version": 1,
            "description": "updated with optimistic lock",
            "state": state_v2,
            "change_note": "A207 update version 2",
            "metadata": {"acceptance_id": "A207", "phase": "server-contract"},
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["current_version"] == 2
    assert updated["state"]["visual_lens"] == "capital_transactions"
    assert updated["versions"][0]["action_type"] == "update"

    stale_update_response = client.put(
        f"/v1/saved-views/{saved_view_id}",
        json={
            "expected_version": 1,
            "state": {**state_v2, "visual_lens": "policy_risk"},
            "change_note": "stale client should fail",
        },
    )
    assert stale_update_response.status_code == 409
    stale_detail = stale_update_response.json()["detail"]
    assert stale_detail["schema_version"] == "saved-view-conflict-v1"
    assert stale_detail["reason"] == "stale_saved_view_version"
    assert stale_detail["expected_version"] == 1
    assert stale_detail["actual_version"] == 2
    assert stale_detail["recovery"] == "fetch_latest_saved_view_or_restore_from_versions"

    version_response = client.get(f"/v1/saved-views/{saved_view_id}/versions")
    assert version_response.status_code == 200
    versions = version_response.json()
    assert [row["version_no"] for row in versions] == [2, 1]
    assert [row["action_type"] for row in versions] == ["update", "create"]

    restore_response = client.post(
        f"/v1/saved-views/{saved_view_id}/restore",
        json={
            "target_version": 1,
            "expected_version": 2,
            "change_note": "A207 recover original supply-chain view",
        },
    )
    assert restore_response.status_code == 200
    restored = restore_response.json()
    assert restored["current_version"] == 3
    assert restored["state"]["visual_lens"] == "supply_chain"
    assert restored["versions"][0]["action_type"] == "restore"
    assert restored["versions"][0]["restored_from_version_no"] == 1
    assert restored["last_restored_at"]

    stale_restore_response = client.post(
        f"/v1/saved-views/{saved_view_id}/restore",
        json={
            "target_version": 2,
            "expected_version": 2,
            "change_note": "stale restore should fail after version 3",
        },
    )
    assert stale_restore_response.status_code == 409
    assert stale_restore_response.json()["detail"]["actual_version"] == 3

    detail_response = client.get(f"/v1/saved-views/{saved_view_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["version_count"] == 3
    assert [row["version_no"] for row in detail["versions"]] == [3, 2, 1]

    with connect_database() as connection:
        saved_view_row = connection.execute(
            """
            SELECT current_version, state->>'visual_lens', last_restored_at IS NOT NULL
            FROM saved_views
            WHERE id = %s
            """,
            (saved_view_id,),
        ).fetchone()
        assert saved_view_row == (3, "supply_chain", True)

        version_row = connection.execute(
            """
            SELECT count(*)::int, array_agg(action_type ORDER BY version_no)
            FROM saved_view_versions
            WHERE saved_view_id = %s
            """,
            (saved_view_id,),
        ).fetchone()
        assert version_row[0] == 3
        assert version_row[1] == ["create", "update", "restore"]

        log_row = connection.execute(
            """
            SELECT count(*) FILTER (WHERE result_status = 'success')::int,
                   count(*) FILTER (WHERE result_status = 'conflict')::int
            FROM operation_logs
            WHERE object_type = 'saved_view'
              AND object_id = %s
              AND action_type IN (
                'create_saved_view',
                'update_saved_view',
                'restore_saved_view'
              )
            """,
            (saved_view_id,),
        ).fetchone()
        assert log_row == (3, 3)


def exercise_transactional_model_activation_contract(
    client: TestClient,
    active_profile: dict[str, object],
) -> None:
    context_response = client.get("/v1/scoring/active-context")
    assert context_response.status_code == 200
    active_context = context_response.json()
    assert active_context["schema_version"] == "active-analysis-context-v1"
    assert str(active_context["active_scoring_profile_version_id"]) == str(active_profile["id"])
    assert active_context["client_state"] == "current"
    assert active_context["refresh_generation"] >= 1
    previous_refresh_token = active_context["refresh_token"]

    draft_weights = dict(active_profile["weights"])
    draft_weights["supply_chain_criticality"] = 0.3
    draft_weights["capital_momentum"] = 0.08
    create_draft_response = client.post(
        "/v1/scoring/profiles",
        json={
            "base_profile_version_id": active_profile["id"],
            "profile_key": "balanced-v2-online-draft",
            "name": "Balanced v2 Online Draft",
            "weights": draft_weights,
            "missing_value_policy": active_profile["missing_value_policy"],
            "reason": "T1303/A204 online model edit draft creation path",
        },
    )
    assert create_draft_response.status_code == 201
    draft = create_draft_response.json()
    assert draft["schema_version"] == "scoring-profile-draft-v1"
    assert draft["status"] == "created"
    assert str(draft["base_profile"]["id"]) == str(active_profile["id"])
    assert draft["profile"]["profile_key"] == "balanced-v2-online-draft"
    assert draft["profile"]["active"] is False
    assert draft["profile"]["weights"]["supply_chain_criticality"] == 0.3
    assert draft["profile"]["weights"]["capital_momentum"] == 0.08
    assert draft["validation"]["weight_sum"] == 1.0
    assert draft["validation"]["changed_weights"] == [
        "capital_momentum",
        "supply_chain_criticality",
    ]
    assert draft["validation"]["active_context_unchanged"] is True
    assert str(draft["active_context"]["active_scoring_profile_version_id"]) == str(
        active_profile["id"]
    )
    target_profile_id = str(draft["profile"]["id"])

    invalid_draft_weights = dict(draft_weights)
    invalid_draft_weights["time_relevance"] = 0.2
    invalid_draft_response = client.post(
        "/v1/scoring/profiles",
        json={
            "base_profile_version_id": active_profile["id"],
            "profile_key": "invalid-weight-draft",
            "name": "Invalid Weight Draft",
            "weights": invalid_draft_weights,
            "reason": "T1303/A204 invalid online edit draft path",
        },
    )
    assert invalid_draft_response.status_code == 422
    assert "sum to 1.0" in invalid_draft_response.json()["detail"]

    listed_profiles = client.get("/v1/scoring/profiles").json()
    assert any(str(profile["id"]) == target_profile_id for profile in listed_profiles)

    activation_response = client.post(
        f"/v1/scoring/profiles/{target_profile_id}/activate",
        json={
            "expected_active_profile_version_id": active_profile["id"],
            "client_refresh_token": previous_refresh_token,
            "reason": "T1303/A204 integration activation success path",
        },
    )
    assert activation_response.status_code == 200
    activation = activation_response.json()
    assert activation["schema_version"] == "model-activation-v1"
    assert activation["status"] == "activated"
    assert str(activation["previous_profile"]["id"]) == str(active_profile["id"])
    assert str(activation["activated_profile"]["id"]) == target_profile_id
    assert activation["activated_profile"]["active"] is True
    assert activation["cache_invalidation"]["previous_refresh_token"] == previous_refresh_token
    assert activation["cache_invalidation"]["refresh_token"] != previous_refresh_token
    assert "supply_chain" in activation["active_context"]["affected_modules"]
    assert "model_center" in activation["active_context"]["affected_modules"]
    assert activation["active_context"]["client_state"] == "stale"
    assert activation["outbox_event"]["event_type"] == "model.profile.activated"
    assert str(activation["outbox_event"]["aggregate_id"]) == target_profile_id
    assert activation["outbox_event"]["status"] == "pending"
    assert activation["outbox_event"]["metadata"]["acceptance_ids"] == ["A204", "A205"]
    next_refresh_token = activation["cache_invalidation"]["refresh_token"]
    next_refresh_generation = activation["cache_invalidation"]["refresh_generation"]

    stale_context_response = client.get(
        f"/v1/scoring/active-context?client_refresh_token={previous_refresh_token}"
    )
    assert stale_context_response.status_code == 200
    assert stale_context_response.json()["client_state"] == "stale"
    current_context_response = client.get(
        f"/v1/scoring/active-context?client_refresh_token={next_refresh_token}"
    )
    assert current_context_response.status_code == 200
    assert current_context_response.json()["client_state"] == "current"

    recompute_response = client.post(
        "/v1/scoring/recompute",
        json={
            "expected_active_profile_version_id": str(target_profile_id),
            "client_refresh_token": next_refresh_token,
            "scope": "global",
            "reason": "T1303/T1304 score recompute enqueue success path",
        },
    )
    assert recompute_response.status_code == 200
    recompute = recompute_response.json()
    assert recompute["schema_version"] == "score-recompute-request-v1"
    assert recompute["status"] == "queued"
    assert recompute["active_context"]["active_scoring_profile_version_id"] == str(
        target_profile_id
    )
    assert recompute["active_context"]["client_state"] == "current"
    assert recompute["job"]["job_type"] == "score_recompute"
    assert recompute["job"]["status"] == "queued"
    assert recompute["job"]["payload"]["schema_version"] == "score-recompute-job-v1"
    assert recompute["job"]["payload"]["refresh_token"] == next_refresh_token
    assert recompute["job"]["payload"]["refresh_generation"] == next_refresh_generation
    assert recompute["job"]["payload"]["active_scoring_profile_version_id"] == str(
        target_profile_id
    )
    assert recompute["job"]["metadata"]["acceptance_ids"] == ["A204", "A205", "A206"]
    assert recompute["outbox_event"]["event_type"] == "score.recompute.requested"
    assert recompute["outbox_event"]["aggregate_id"] == recompute["job"]["id"]
    assert recompute["outbox_event"]["status"] == "pending"
    assert recompute["cache_policy"]["refresh_token"] == next_refresh_token

    duplicate_recompute_response = client.post(
        "/v1/scoring/recompute",
        json={
            "expected_active_profile_version_id": str(target_profile_id),
            "client_refresh_token": next_refresh_token,
            "scope": "global",
            "reason": "T1303/T1304 score recompute idempotency path",
        },
    )
    assert duplicate_recompute_response.status_code == 200
    duplicate_recompute = duplicate_recompute_response.json()
    assert duplicate_recompute["job"]["id"] == recompute["job"]["id"]
    assert duplicate_recompute["idempotency_key"] == recompute["idempotency_key"]
    assert duplicate_recompute["outbox_event"]["id"] == recompute["outbox_event"]["id"]

    executed_recompute = run_once(
        worker_id="a206-score-recompute-worker",
        job_type="score_recompute",
    )
    assert executed_recompute is not None
    assert executed_recompute["id"] == recompute["job"]["id"]
    assert executed_recompute["status"] == "succeeded"
    recompute_result = executed_recompute["metadata"]["result"]
    assert recompute_result["handler"] == "score_recompute"
    assert recompute_result["handler_contract"] == "score-recompute-worker-v1"
    assert recompute_result["status"] == "completed"
    assert recompute_result["active_scoring_profile_version_id"] == str(target_profile_id)
    assert recompute_result["previous_refresh_token"] == next_refresh_token
    assert recompute_result["refresh_token"] != next_refresh_token
    assert recompute_result["previous_refresh_generation"] == next_refresh_generation
    assert recompute_result["refresh_generation"] == next_refresh_generation + 1
    assert recompute_result["scored_objects"] >= 1
    expected_mvp_score_types = {
        "relationship_fact_candidate",
        "relationship",
        "entity",
        "event",
        "industry",
        "source_document",
    }
    assert recompute_result["score_result_object_type"] == "mvp_object_family"
    assert set(recompute_result["score_result_object_types"]) == expected_mvp_score_types
    assert set(recompute_result["score_result_object_counts"]) == expected_mvp_score_types
    assert all(
        recompute_result["score_result_object_counts"][object_type] >= 1
        for object_type in expected_mvp_score_types
    )
    assert (
        sum(recompute_result["score_result_object_counts"].values())
        == recompute_result["scored_objects"]
    )
    assert recompute_result["acceptance_ids"] == ["A204", "A205", "A206"]
    assert recompute_result["outbox_event"]["event_type"] == "score.snapshot.activated"
    assert recompute_result["outbox_event"]["aggregate_id"] == recompute_result["scoring_run_id"]
    assert recompute_result["outbox_event"]["status"] == "pending"
    assert (
        set(recompute_result["outbox_event"]["payload"]["score_result_object_types"])
        == expected_mvp_score_types
    )
    assert recompute_result["outbox_event"]["payload"]["score_result_object_counts"] == (
        recompute_result["score_result_object_counts"]
    )
    recompute_refresh_token = recompute_result["refresh_token"]
    recompute_scoring_run_id = recompute_result["scoring_run_id"]

    dispatched_activation = dispatch_outbox_once(
        worker_id="a206-outbox-dispatcher",
        event_type="model.profile.activated",
    )
    assert dispatched_activation is not None
    assert dispatched_activation["status"] == "dispatched"
    assert dispatched_activation["metadata"]["dispatch_result"]["handler_contract"] == (
        "outbox-dispatch-v1"
    )
    dispatched_recompute_request = dispatch_outbox_once(
        worker_id="a206-outbox-dispatcher",
        event_type="score.recompute.requested",
    )
    assert dispatched_recompute_request is not None
    assert dispatched_recompute_request["status"] == "dispatched"
    dispatched_score_snapshot = dispatch_outbox_once(
        worker_id="a206-outbox-dispatcher",
        event_type="score.snapshot.activated",
    )
    assert dispatched_score_snapshot is not None
    assert dispatched_score_snapshot["status"] == "dispatched"
    assert (
        dispatch_outbox_once(
            worker_id="a206-outbox-dispatcher",
            event_type="score.snapshot.activated",
        )
        is None
    )

    with connect_database() as connection:
        recompute_context = connection.execute(
            """
            SELECT active_scoring_profile_version_id, active_scoring_run_id,
                   refresh_token::text, refresh_generation, status
            FROM active_analysis_contexts
            WHERE context_key = 'global'
            """
        ).fetchone()
        assert str(recompute_context[0]) == target_profile_id
        assert str(recompute_context[1]) == recompute_scoring_run_id
        assert recompute_context[2] == recompute_refresh_token
        assert recompute_context[3] == next_refresh_generation + 1
        assert recompute_context[4] == "active"
        score_result_type_rows = connection.execute(
            """
            SELECT object_type, count(*)::int
            FROM score_results
            WHERE scoring_run_id = %s
              AND adjusted_score IS NOT NULL
            GROUP BY object_type
            ORDER BY object_type
            """,
            (UUID(recompute_scoring_run_id),),
        ).fetchall()
        score_result_type_counts = {
            object_type: count for object_type, count in score_result_type_rows
        }
        assert set(score_result_type_counts) == expected_mvp_score_types
        assert score_result_type_counts == recompute_result["score_result_object_counts"]
        assert sum(score_result_type_counts.values()) == recompute_result["scored_objects"]
        missing_metric_count = connection.execute(
            """
            SELECT count(*)::int
            FROM score_results
            WHERE scoring_run_id = %s
              AND (
                raw_score IS NULL
                OR evidence_quality IS NULL
                OR adjusted_score IS NULL
                OR coverage IS NULL
              )
            """,
            (UUID(recompute_scoring_run_id),),
        ).fetchone()[0]
        assert missing_metric_count == 0
        score_result_object_id = connection.execute(
            """
            SELECT object_id
            FROM score_results
            WHERE scoring_run_id = %s
              AND object_type = 'relationship_fact_candidate'
            ORDER BY adjusted_score DESC, object_id
            LIMIT 1
            """,
            (UUID(recompute_scoring_run_id),),
        ).fetchone()[0]

    score_result_response = client.get(
        f"/v1/scoring/explain/score_result/{score_result_object_id}"
    )
    assert score_result_response.status_code == 200
    score_result_score = score_result_response.json()
    assert score_result_score["object_type"] == "score_result"
    assert score_result_score["object_id"] == str(score_result_object_id)
    assert score_result_score["scored_object_type"] == "relationship_fact_candidate"
    assert score_result_score["publication_status"] == "active_score_result"
    assert score_result_score["score_result"]["scoring_run_id"] == recompute_scoring_run_id
    assert score_result_score["score_result"]["object_type"] == "relationship_fact_candidate"
    assert score_result_score["active_context"]["active_scoring_run_id"] == (
        recompute_scoring_run_id
    )
    assert score_result_score["source_threshold"]["met"] is True
    assert score_result_score["coverage_summary"]["active_context_present"] is True
    assert score_result_score["raw_score"] == 100
    assert score_result_score["evidence"] == []

    data_refresh_response = client.post(
        "/v1/data/snapshots/refresh",
        json={
            "expected_active_profile_version_id": str(target_profile_id),
            "client_refresh_token": recompute_refresh_token,
            "scope": "golden-vertical:nvidia",
            "record_mode": "curated_official_fixture",
            "reason": "T1303/T1304 data snapshot refresh enqueue success path",
        },
    )
    assert data_refresh_response.status_code == 200
    data_refresh = data_refresh_response.json()
    assert data_refresh["schema_version"] == "data-snapshot-refresh-request-v1"
    assert data_refresh["status"] == "queued"
    assert data_refresh["job"]["job_type"] == "data_snapshot_refresh"
    assert data_refresh["job"]["payload"]["schema_version"] == (
        "data-snapshot-refresh-job-v1"
    )
    assert data_refresh["job"]["payload"]["refresh_token"] == recompute_refresh_token
    assert data_refresh["job"]["payload"]["record_mode"] == "curated_official_fixture"
    assert data_refresh["outbox_event"]["event_type"] == "data.snapshot.refresh.requested"
    assert data_refresh["outbox_event"]["aggregate_id"] == data_refresh["job"]["id"]
    assert data_refresh["outbox_event"]["status"] == "pending"

    duplicate_data_refresh_response = client.post(
        "/v1/data/snapshots/refresh",
        json={
            "expected_active_profile_version_id": str(target_profile_id),
            "client_refresh_token": recompute_refresh_token,
            "scope": "golden-vertical:nvidia",
            "record_mode": "curated_official_fixture",
            "reason": "T1303/T1304 data snapshot refresh idempotency path",
        },
    )
    assert duplicate_data_refresh_response.status_code == 200
    duplicate_data_refresh = duplicate_data_refresh_response.json()
    assert duplicate_data_refresh["job"]["id"] == data_refresh["job"]["id"]
    assert duplicate_data_refresh["idempotency_key"] == data_refresh["idempotency_key"]
    assert duplicate_data_refresh["outbox_event"]["id"] == data_refresh["outbox_event"]["id"]

    executed_data_refresh = run_once(
        worker_id="a206-data-snapshot-refresh-worker",
        job_type="data_snapshot_refresh",
    )
    assert executed_data_refresh is not None
    assert executed_data_refresh["id"] == data_refresh["job"]["id"]
    assert executed_data_refresh["status"] == "succeeded"
    data_refresh_result = executed_data_refresh["metadata"]["result"]
    assert data_refresh_result["handler"] == "data_snapshot_refresh"
    assert data_refresh_result["handler_contract"] == "data-snapshot-refresh-worker-v1"
    assert data_refresh_result["status"] == "completed"
    assert data_refresh_result["scope"] == "golden-vertical:nvidia"
    assert data_refresh_result["record_mode"] == "curated_official_fixture"
    assert data_refresh_result["previous_refresh_token"] == recompute_refresh_token
    assert data_refresh_result["refresh_token"] != recompute_refresh_token
    assert data_refresh_result["refresh_generation"] == next_refresh_generation + 2
    assert data_refresh_result["data_snapshot_id"]
    assert data_refresh_result["data_snapshot_key"]
    assert data_refresh_result["source_hash"]
    assert data_refresh_result["source_stats"]["fact_candidate_count"] >= 2
    assert data_refresh_result["outbox_event"]["event_type"] == "data.snapshot.activated"
    assert data_refresh_result["outbox_event"]["aggregate_id"] == (
        data_refresh_result["data_snapshot_id"]
    )
    assert data_refresh_result["outbox_event"]["status"] == "pending"
    data_refresh_token = data_refresh_result["refresh_token"]
    data_snapshot_id = data_refresh_result["data_snapshot_id"]

    dispatched_data_refresh_request = dispatch_outbox_once(
        worker_id="a206-outbox-dispatcher",
        event_type="data.snapshot.refresh.requested",
    )
    assert dispatched_data_refresh_request is not None
    assert dispatched_data_refresh_request["status"] == "dispatched"
    dispatched_data_snapshot = dispatch_outbox_once(
        worker_id="a206-outbox-dispatcher",
        event_type="data.snapshot.activated",
    )
    assert dispatched_data_snapshot is not None
    assert dispatched_data_snapshot["status"] == "dispatched"

    with connect_database() as connection:
        data_refresh_context = connection.execute(
            """
            SELECT active_scoring_profile_version_id, active_data_snapshot_id,
                   refresh_token::text, refresh_generation, status
            FROM active_analysis_contexts
            WHERE context_key = 'global'
            """
        ).fetchone()
        assert str(data_refresh_context[0]) == target_profile_id
        assert str(data_refresh_context[1]) == data_snapshot_id
        assert data_refresh_context[2] == data_refresh_token
        assert data_refresh_context[3] == next_refresh_generation + 2
        assert data_refresh_context[4] == "active"
        snapshot_row = connection.execute(
            """
            SELECT snapshot_key, scope, record_mode, status, supersedes_snapshot_id,
                   metadata->>'handler_contract'
            FROM data_snapshots
            WHERE id = %s
            """,
            (UUID(data_snapshot_id),),
        ).fetchone()
        assert snapshot_row[0] == data_refresh_result["data_snapshot_key"]
        assert snapshot_row[1] == "golden-vertical:nvidia"
        assert snapshot_row[2] == "curated_official_fixture"
        assert snapshot_row[3] == "active"
        assert snapshot_row[5] == "data-snapshot-refresh-worker-v1"

    stale_recompute_response = client.post(
        "/v1/scoring/recompute",
        json={
            "expected_active_profile_version_id": str(target_profile_id),
            "client_refresh_token": recompute_refresh_token,
            "scope": "global",
            "reason": "T1303/T1304 stale recompute negative path",
        },
    )
    assert stale_recompute_response.status_code == 409
    recompute_conflict = stale_recompute_response.json()["detail"]
    assert recompute_conflict["schema_version"] == "score-recompute-conflict-v1"
    assert recompute_conflict["status"] == "conflict"
    assert recompute_conflict["reason"] == "stale_client_refresh_token"
    assert str(recompute_conflict["actual_active_profile_version_id"]) == target_profile_id

    stale_activation_response = client.post(
        f"/v1/scoring/profiles/{active_profile['id']}/activate",
        json={
            "expected_active_profile_version_id": active_profile["id"],
            "client_refresh_token": previous_refresh_token,
            "reason": "T1303/A204 stale expected active version negative path",
        },
    )
    assert stale_activation_response.status_code == 409
    conflict = stale_activation_response.json()["detail"]
    assert conflict["status"] == "conflict"
    assert conflict["reason"] == "stale_active_profile_version"
    assert str(conflict["actual_active_profile_version_id"]) == target_profile_id

    rollback_response = client.post(
        f"/v1/scoring/profiles/{active_profile['id']}/rollback",
        json={
            "expected_active_profile_version_id": str(target_profile_id),
            "client_refresh_token": data_refresh_token,
            "reason": "T1303/A204 dedicated rollback endpoint success path",
        },
    )
    assert rollback_response.status_code == 200
    rollback = rollback_response.json()
    assert rollback["schema_version"] == "model-activation-v1"
    assert rollback["status"] == "activated"
    assert str(rollback["previous_profile"]["id"]) == target_profile_id
    assert str(rollback["activated_profile"]["id"]) == str(active_profile["id"])
    assert rollback["activated_profile"]["active"] is True
    assert rollback["cache_invalidation"]["previous_refresh_token"] == data_refresh_token
    assert rollback["cache_invalidation"]["refresh_token"] != data_refresh_token
    assert str(rollback["active_context"]["active_scoring_profile_version_id"]) == str(
        active_profile["id"]
    )
    rollback_refresh_token = rollback["cache_invalidation"]["refresh_token"]

    stale_rollback_response = client.post(
        f"/v1/scoring/profiles/{target_profile_id}/rollback",
        json={
            "expected_active_profile_version_id": str(target_profile_id),
            "client_refresh_token": next_refresh_token,
            "reason": "T1303/A204 stale rollback endpoint negative path",
        },
    )
    assert stale_rollback_response.status_code == 409
    rollback_conflict = stale_rollback_response.json()["detail"]
    assert rollback_conflict["status"] == "conflict"
    assert rollback_conflict["reason"] == "stale_active_profile_version"
    assert str(rollback_conflict["actual_active_profile_version_id"]) == str(
        active_profile["id"]
    )

    with connect_database() as connection:
        active_rows = connection.execute(
            """
            SELECT id
            FROM scoring_profile_versions
            WHERE active = true
            """
        ).fetchall()
        assert [row[0] for row in active_rows] == [UUID(str(active_profile["id"]))]
        context_row = connection.execute(
            """
            SELECT active_scoring_profile_version_id, active_scoring_run_id,
                   refresh_token::text, refresh_generation, status
            FROM active_analysis_contexts
            WHERE context_key = 'global'
            """
        ).fetchone()
        (
            context_profile_version_id,
            context_scoring_run_id,
            context_refresh_token,
            _context_refresh_generation,
            context_status,
        ) = context_row
        assert context_profile_version_id == UUID(str(active_profile["id"]))
        assert context_scoring_run_id is not None
        assert context_refresh_token == rollback_refresh_token
        assert context_status == "active"
        score_run_count = connection.execute(
            """
            SELECT count(*)::int
            FROM scoring_runs
            WHERE id = %s
              AND profile_version_id = %s
              AND status = 'completed'
            """,
            (context_scoring_run_id, UUID(str(active_profile["id"]))),
        ).fetchone()[0]
        assert score_run_count == 1
        recompute_job_count = connection.execute(
            """
            SELECT count(*)::int
            FROM background_jobs
            WHERE job_type = 'score_recompute'
              AND id = %s
              AND idempotency_key = %s
              AND status = 'succeeded'
              AND payload->>'refresh_token' = %s
            """,
            (
                UUID(recompute["job"]["id"]),
                recompute["idempotency_key"],
                next_refresh_token,
            ),
        ).fetchone()[0]
        assert recompute_job_count == 1
        log_counts = {
            (row[0], row[1]): row[2]
            for row in connection.execute(
                """
                SELECT action_type, result_status, count(*)::int
                FROM operation_logs
                WHERE action_type IN (
                  'activate_scoring_profile',
                  'rollback_scoring_profile',
                  'enqueue_score_recompute',
                  'execute_score_recompute',
                  'enqueue_data_snapshot_refresh',
                  'execute_data_snapshot_refresh',
                  'dispatch_outbox_event'
                )
                GROUP BY action_type, result_status
                """
            ).fetchall()
        }
        assert log_counts[("activate_scoring_profile", "success")] == 1
        assert log_counts[("activate_scoring_profile", "conflict")] == 1
        assert log_counts[("rollback_scoring_profile", "success")] == 1
        assert log_counts[("rollback_scoring_profile", "conflict")] == 1
        assert log_counts[("enqueue_score_recompute", "success")] == 2
        assert log_counts[("enqueue_score_recompute", "conflict")] == 1
        assert log_counts[("execute_score_recompute", "success")] == 1
        assert log_counts[("enqueue_data_snapshot_refresh", "success")] == 2
        assert log_counts[("execute_data_snapshot_refresh", "success")] == 1
        assert log_counts[("dispatch_outbox_event", "success")] == 5
        outbox_counts = {
            (row[0], row[1]): row[2]
            for row in connection.execute(
                """
                SELECT event_type, status, count(*)::int
                FROM transactional_outbox
                GROUP BY event_type, status
                """
            ).fetchall()
        }
        assert outbox_counts[("model.profile.activated", "dispatched")] == 1
        assert outbox_counts[("model.profile.activated", "pending")] == 1
        assert outbox_counts[("score.recompute.requested", "dispatched")] == 1
        assert outbox_counts[("score.snapshot.activated", "dispatched")] == 1
        assert outbox_counts[("data.snapshot.refresh.requested", "dispatched")] == 1
        assert outbox_counts[("data.snapshot.activated", "dispatched")] == 1
        try:
            connection.execute(
                "UPDATE scoring_profile_versions SET active = true WHERE id = %s",
                (target_profile_id,),
            )
        except errors.UniqueViolation:
            connection.rollback()
        else:  # pragma: no cover - should be unreachable with the global active index.
            raise AssertionError("Only one globally active scoring profile is allowed")


def exercise_background_scheduler_contracts() -> None:
    worker_id = "a206-integration-worker"
    job = enqueue_job(
        job_type="noop",
        idempotency_key="a206-idempotent-retry-contract",
        payload={"acceptance_id": "A206", "path": "retry-dead-letter"},
        max_attempts=3,
        dead_letter_after_attempts=3,
        metadata={"task_id": "T1304"},
    )
    duplicate = enqueue_job(
        job_type="noop",
        idempotency_key="a206-idempotent-retry-contract",
        payload={"acceptance_id": "A206", "duplicate": True},
        max_attempts=3,
        dead_letter_after_attempts=3,
    )
    assert duplicate["id"] == job["id"]
    assert duplicate["payload"]["path"] == "retry-dead-letter"

    first_lease = lease_next_job(worker_id=worker_id, job_type="noop", lease_ttl_seconds=60)
    assert first_lease is not None
    assert first_lease["id"] == job["id"]
    assert first_lease["status"] == "running"
    assert first_lease["attempt_count"] == 1
    assert first_lease["lease_token"]

    heartbeat = heartbeat_job(
        job_id=first_lease["id"],
        lease_token=first_lease["lease_token"],
        worker_id=worker_id,
        lease_ttl_seconds=120,
    )
    assert heartbeat["heartbeat_at"]
    assert heartbeat["lease_expires_at"] > first_lease["lease_expires_at"]

    released = release_job(
        job_id=first_lease["id"],
        lease_token=first_lease["lease_token"],
        reason="graceful_shutdown",
    )
    assert released["status"] == "queued"
    assert released["attempt_count"] == 1
    assert released["lease_token"] is None
    assert released["metadata"]["last_release_reason"] == "graceful_shutdown"

    second_lease = lease_next_job(worker_id=worker_id, job_type="noop", lease_ttl_seconds=60)
    assert second_lease is not None
    assert second_lease["id"] == job["id"]
    assert second_lease["attempt_count"] == 2
    retry = fail_job(
        job_id=second_lease["id"],
        lease_token=second_lease["lease_token"],
        error_class="fixture_retry",
        error_message="retry path remains bounded",
        retry_backoff_seconds=0,
    )
    assert retry["status"] == "queued"
    assert retry["last_error_class"] == "fixture_retry"

    third_lease = lease_next_job(worker_id=worker_id, job_type="noop", lease_ttl_seconds=60)
    assert third_lease is not None
    assert third_lease["attempt_count"] == 3
    dead = fail_job(
        job_id=third_lease["id"],
        lease_token=third_lease["lease_token"],
        error_class="fixture_terminal",
        error_message="dead-letter after retry cap",
        retry_backoff_seconds=0,
    )
    assert dead["status"] == "dead_letter"
    assert dead["finished_at"]

    expired_job = enqueue_job(
        job_type="noop",
        idempotency_key="a206-expired-lease-contract",
        payload={"acceptance_id": "A206", "path": "expired-lease"},
        max_attempts=3,
        dead_letter_after_attempts=3,
    )
    expired_lease = lease_next_job(worker_id=worker_id, job_type="noop", lease_ttl_seconds=60)
    assert expired_lease is not None
    assert expired_lease["id"] == expired_job["id"]
    with connect_database() as connection:
        connection.execute(
            """
            UPDATE background_jobs
            SET lease_expires_at = now() - interval '1 minute'
            WHERE id = %s
            """,
            (expired_job["id"],),
        )
    recovery = recover_expired_leases()
    assert recovery == {"recovered": 1, "dead_lettered": 0}

    recovered_lease = lease_next_job(worker_id=worker_id, job_type="noop", lease_ttl_seconds=60)
    assert recovered_lease is not None
    assert recovered_lease["id"] == expired_job["id"]
    completed = complete_job(
        job_id=recovered_lease["id"],
        lease_token=recovered_lease["lease_token"],
        result={"handler": "noop", "acceptance_id": "A206"},
    )
    assert completed["status"] == "succeeded"
    assert completed["metadata"]["result"]["acceptance_id"] == "A206"

    with connect_database() as connection:
        dead_letter_row = connection.execute(
            """
            SELECT final_attempt_no, error_class, error_message
            FROM dead_letter_jobs
            WHERE job_id = %s
            """,
            (job["id"],),
        ).fetchone()
        assert dead_letter_row == (3, "fixture_terminal", "dead-letter after retry cap")
        attempt_statuses = connection.execute(
            """
            SELECT bja.status, count(*)::int
            FROM background_job_attempts bja
            JOIN background_jobs bj ON bj.id = bja.job_id
            WHERE bj.job_type = 'noop'
            GROUP BY bja.status
            """
        ).fetchall()
        counts_by_status = {row[0]: row[1] for row in attempt_statuses}
        assert counts_by_status["released"] == 1
        assert counts_by_status["failed"] == 2
        assert counts_by_status["expired"] == 1
        assert counts_by_status["succeeded"] == 1
        job_counts = connection.execute(
            """
            SELECT
              count(*) FILTER (WHERE status = 'succeeded')::int,
              count(*) FILTER (WHERE status = 'dead_letter')::int,
              count(*) FILTER (WHERE status = 'running')::int
            FROM background_jobs
            WHERE job_type = 'noop'
            """
        ).fetchone()
        assert job_counts == (1, 1, 0)

    ingestion_job = enqueue_job(
        job_type="curated_ingestion_refresh",
        idempotency_key="a206-curated-ingestion-refresh-contract",
        payload={
            "schema_version": "curated-ingestion-refresh-job-v1",
            "record_mode": "curated_official_fixture",
            "reason": "T1304/A206 curated ingestion handler contract",
        },
        max_attempts=3,
        dead_letter_after_attempts=3,
        metadata={"task_ids": ["T1301", "T1304"], "acceptance_ids": ["A202", "A206"]},
    )
    executed_ingestion = run_once(
        worker_id="a206-curated-ingestion-worker",
        job_type="curated_ingestion_refresh",
    )
    assert executed_ingestion is not None
    assert executed_ingestion["id"] == ingestion_job["id"]
    assert executed_ingestion["status"] == "succeeded"
    ingestion_result = executed_ingestion["metadata"]["result"]
    assert ingestion_result["handler"] == "curated_ingestion_refresh"
    assert ingestion_result["handler_contract"] == "curated-ingestion-refresh-worker-v1"
    assert ingestion_result["record_mode"] == "curated_official_fixture"
    assert ingestion_result["counts"]["parser_version"] == CURATED_ANCHOR_PARSER_VERSION
    assert ingestion_result["counts"]["relationship_fact_candidates"] >= 2
    assert ingestion_result["source_stats"]["raw_snapshot_count"] >= 6
    assert ingestion_result["source_stats"]["published_fact_candidate_count"] >= 2
    assert ingestion_result["source_stats"]["source_threshold_open_count"] == 0
    assert ingestion_result["source_stats"]["review_open_count"] == 0
    assert ingestion_result["fixture_policy"] == (
        "curated_official_fixture is not live/full-text ingestion"
    )
    assert ingestion_result["outbox_event"]["event_type"] == "data.ingestion.completed"

    supervised_job = enqueue_job(
        job_type="noop",
        idempotency_key="a206-supervised-worker-cycle-contract",
        payload={"acceptance_id": "A206", "path": "worker-supervision"},
        max_attempts=3,
        dead_letter_after_attempts=3,
        metadata={"task_id": "T1304", "contract": "worker-supervisor-v1"},
    )
    supervised_cycle = run_worker_cycle(
        worker_id="a206-supervised-worker",
        job_type="noop",
        max_jobs=1,
        max_outbox=3,
    )
    assert supervised_cycle["handler_contract"] == "worker-supervisor-v1"
    assert supervised_cycle["lease_recovery"] == {"recovered": 0, "dead_lettered": 0}
    assert supervised_cycle["jobs_processed"] == 1
    assert supervised_cycle["outbox_events_dispatched"] >= 1
    assert supervised_cycle["jobs"][0]["id"] == supervised_job["id"]
    assert supervised_cycle["jobs"][0]["status"] == "succeeded"
    assert supervised_cycle["health"]["schema_version"] == "eei-worker-health-v1"
    assert supervised_cycle["health"]["supervision"]["recover_expired_leases"] is True
    assert supervised_cycle["health"]["supervision"]["run_background_jobs"] is True
    assert supervised_cycle["health"]["supervision"]["dispatch_transactional_outbox"] is True

    idle_summary = supervise_worker(
        worker_id="a206-idle-supervisor",
        job_type="a206-idle-probe",
        event_type="a206.idle.probe",
        poll_interval_seconds=0,
        max_cycles=1,
        stop_when_idle=True,
    )
    assert idle_summary["handler_contract"] == "worker-supervisor-v1"
    assert idle_summary["status"] == "stopped"
    assert idle_summary["stop_reason"] == "idle"
    assert idle_summary["cycles"] == 1
    assert idle_summary["last_cycle"]["idle"] is True

    health = worker_health_snapshot()
    assert health["handler_contract"] == "worker-supervisor-v1"
    assert health["background_jobs"]["counts"]["succeeded"] >= 3
    assert health["transactional_outbox"]["counts"]["dispatched"] >= 1
    assert health["dead_letter_job_count"] >= 1
    exercise_worker_supervisor_cli_contracts()


def exercise_worker_supervisor_cli_contracts() -> None:
    cli_job = enqueue_job(
        job_type="noop",
        idempotency_key="a206-worker-supervisor-cli-job-contract",
        payload={"acceptance_id": "A206", "path": "worker-supervisor-cli"},
        max_attempts=3,
        dead_letter_after_attempts=3,
        metadata={
            "task_ids": ["T1304", "T1307"],
            "acceptance_ids": ["A206", "A209"],
            "contract": "worker-supervisor-cli-v1",
        },
    )
    with connect_job_database() as connection:
        cli_event = write_outbox_event(
            connection,
            event_type="a206.worker.cli.wake",
            aggregate_type="worker_supervisor_cli",
            aggregate_id=None,
            idempotency_key="a206-worker-supervisor-cli-outbox-contract",
            payload={
                "schema_version": "worker-supervisor-cli-event-v1",
                "acceptance_ids": ["A206", "A209"],
                "path": "worker-supervisor-cli",
            },
            metadata={
                "task_ids": ["T1304", "T1307"],
                "acceptance_ids": ["A206", "A209"],
                "contract": "worker-supervisor-cli-v1",
            },
        )

    cli_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "apps.worker.app.main",
            "supervise",
            "--worker-id",
            "a206-cli-supervisor",
            "--job-type",
            "noop",
            "--event-type",
            "a206.worker.cli.wake",
            "--max-jobs-per-cycle",
            "1",
            "--max-outbox-per-cycle",
            "1",
            "--poll-interval-seconds",
            "0",
            "--max-cycles",
            "2",
            "--stop-when-idle",
        ],
        cwd=os.getcwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert cli_result.returncode == 0, cli_result.stderr
    cli_summary = json.loads(cli_result.stdout)
    assert cli_summary["schema_version"] == "eei-worker-supervision-summary-v1"
    assert cli_summary["handler_contract"] == "worker-supervisor-v1"
    assert cli_summary["worker_id"] == "a206-cli-supervisor"
    assert cli_summary["status"] == "stopped"
    assert cli_summary["stop_reason"] == "idle"
    assert cli_summary["cycles"] == 2
    assert cli_summary["jobs_processed"] == 1
    assert cli_summary["outbox_events_dispatched"] == 1
    assert cli_summary["acceptance_ids"] == ["A206", "A209"]
    assert cli_summary["last_cycle"]["idle"] is True
    assert cli_summary["health"]["supervision"]["acceptance_ids"] == ["A206", "A209"]
    with connect_database() as connection:
        cli_job_row = connection.execute(
            """
            SELECT status, metadata->'result'->>'handler', payload->>'acceptance_id',
                   metadata->'acceptance_ids'
            FROM background_jobs
            WHERE id = %s
            """,
            (UUID(cli_job["id"]),),
        ).fetchone()
        assert cli_job_row[0:3] == ("succeeded", "noop", "A206")
        assert cli_job_row[3] == ["A206", "A209"]
        cli_event_row = connection.execute(
            """
            SELECT status, metadata->'dispatch_result'->>'handler_contract',
                   metadata->'dispatch_result'->'acceptance_ids'
            FROM transactional_outbox
            WHERE id = %s
            """,
            (UUID(cli_event["id"]),),
        ).fetchone()
        assert cli_event_row[0] == "dispatched"
        assert cli_event_row[1] == "outbox-dispatch-v1"
        assert cli_event_row[2] == ["A206", "A209"]
