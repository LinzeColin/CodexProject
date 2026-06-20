#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from db_tools import connect_database

REQUIRED_TABLES = {
    "entities",
    "relationships",
    "relationship_families",
    "relationship_type_catalog",
    "relationship_evidence",
    "events",
    "event_evidence",
    "industries",
    "entity_industry_memberships",
    "entity_aliases",
    "entity_identifiers",
    "supply_chain_relationship_attributes",
    "exploration_sessions",
    "watchlists",
    "scoring_models",
    "operation_logs",
    "calibration_runs",
    "supply_chain_stages",
    "company_research_universe",
    "seed_runs",
    "exploration_steps",
    "watchlist_items",
    "scoring_profiles",
    "scoring_profile_versions",
    "scoring_runs",
    "score_results",
    "changes",
    "data_snapshots",
    "fact_versions",
    "fact_version_evidence",
    "raw_source_snapshots",
    "entity_resolution_candidates",
    "ingestion_evidence_chain",
    "relationship_fact_candidates",
    "relationship_fact_candidate_evidence",
    "manual_review_queue",
}

REQUIRED_ENTITY_TYPES = {
    "legal_entity",
    "brand",
    "facility",
    "product",
    "business_segment",
    "industry",
    "asset",
}

REQUIRED_SUPPLY_CHAIN_ATTRIBUTE_COLUMNS = {
    "tier",
    "materiality",
    "substitutability_score",
    "capacity_value",
    "capacity_unit",
    "geographic_exposure",
    "coverage",
}

REQUIRED_EXPLORATION_SESSION_COLUMNS = {
    "active_layers",
    "as_of",
    "budget",
    "direction",
    "filters",
    "hops",
    "scoring_profile_version_id",
    "state_version",
}

REQUIRED_TEMPORAL_COLUMNS = {
    "relationships": {"valid_from", "valid_to", "announced_at", "filed_at", "observed_at"},
    "events": {"announced_at", "effective_at", "period_start", "period_end", "observed_at"},
    "source_documents": {"document_date", "observed_at", "retrieved_at"},
    "ingestion_runs": {"started_at", "finished_at"},
    "data_snapshots": {"as_of", "activated_at", "created_at"},
    "fact_versions": {"valid_from", "valid_to", "observed_at", "created_at"},
    "raw_source_snapshots": {"source_date", "retrieved_at", "created_at"},
    "entity_resolution_candidates": {"created_at"},
    "ingestion_evidence_chain": {"created_at"},
    "relationship_fact_candidates": {"created_at", "updated_at"},
    "relationship_fact_candidate_evidence": {"created_at"},
    "manual_review_queue": {"created_at", "resolved_at"},
}

REQUIRED_PRODUCTION_VERSION_COLUMNS = {
    "data_snapshots": {
        "snapshot_key",
        "scope",
        "record_mode",
        "status",
        "source_hash",
        "supersedes_snapshot_id",
        "metadata",
    },
    "fact_versions": {
        "snapshot_id",
        "object_type",
        "object_id",
        "version_no",
        "fact_status",
        "record_mode",
        "source_document_id",
        "ingestion_run_id",
        "parser_version",
        "payload_hash",
        "payload",
        "previous_fact_version_id",
    },
    "fact_version_evidence": {
        "fact_version_id",
        "source_document_id",
        "role",
        "locator",
        "support_excerpt",
        "structured_fact",
    },
}

REQUIRED_CURATED_INGESTION_COLUMNS = {
    "raw_source_snapshots": {
        "ingestion_run_id",
        "source_document_id",
        "anchor_id",
        "source_url",
        "publisher",
        "title",
        "evidence_scope",
        "record_mode",
        "validation_status",
        "parser_version",
        "content_hash",
        "raw_payload",
        "review_status",
    },
    "entity_resolution_candidates": {
        "raw_snapshot_id",
        "candidate_name",
        "normalized_name",
        "matched_entity_id",
        "matched_research_id",
        "match_method",
        "confidence",
        "decision_reason",
        "review_status",
        "parser_version",
    },
    "ingestion_evidence_chain": {
        "raw_snapshot_id",
        "source_document_id",
        "subject_resolution_id",
        "object_resolution_id",
        "relationship_type",
        "relationship_family",
        "evidence_role",
        "locator",
        "support_excerpt",
        "structured_fact",
        "counter_evidence",
        "parser_version",
        "confidence",
        "review_status",
    },
    "relationship_fact_candidates": {
        "candidate_key",
        "subject_resolution_id",
        "object_resolution_id",
        "relationship_type",
        "relationship_family",
        "record_mode",
        "fact_status",
        "publication_status",
        "confidence",
        "independent_source_count",
        "source_threshold_met",
        "review_status",
        "parser_version",
        "structured_fact",
        "counter_evidence",
    },
    "relationship_fact_candidate_evidence": {
        "candidate_id",
        "ingestion_evidence_chain_id",
        "source_document_id",
        "role",
        "locator",
        "support_excerpt",
    },
    "manual_review_queue": {
        "queue_key",
        "object_type",
        "object_id",
        "reason",
        "priority",
        "status",
        "requested_by",
        "reviewer",
        "decision",
    },
}

REQUIRED_CURATED_INGESTION_INDEXES = {
    "raw_source_snapshots_mode_time_idx",
    "raw_source_snapshots_document_idx",
    "entity_resolution_candidates_snapshot_idx",
    "entity_resolution_candidates_entity_idx",
    "entity_resolution_candidates_research_idx",
    "ingestion_evidence_chain_snapshot_idx",
    "ingestion_evidence_chain_source_document_idx",
    "relationship_fact_candidates_type_idx",
    "relationship_fact_candidates_review_idx",
    "relationship_fact_candidate_evidence_source_idx",
    "manual_review_queue_status_idx",
}

CURATED_ANCHOR_PARSER_VERSION = "nvidia-public-anchor-v1"

SEED_EXPECTATIONS = {
    "relationship_families": 10,
    "relationship_type_catalog": 52,
    "industries": 26,
    "supply_chain_stages": 16,
    "company_research_universe": 140,
    "scoring_models": 1,
    "scoring_profiles": 1,
    "scoring_profile_versions": 1,
}

RESEARCH_TIER_EXPECTATIONS = {
    "P0": 30,
    "P1": 50,
    "P2": 40,
    "X": 20,
}

FIXTURE_EXPECTATIONS = {
    "entities": 30,
    "relationships": 26,
    "fixture_entity_notices": 30,
    "fixture_relationship_notices": 26,
}

REQUIRED_FIXTURE_FAMILIES = {
    "capital_financing",
    "commercial_dependency",
    "corporate_structure",
    "governance_people",
    "government_policy",
    "mergers_acquisitions",
    "ownership_control",
    "strategic_signal",
    "supply_chain_operations",
    "technology_data_ip",
}

REQUIRED_NVIDIA_STAGES = {"SC-02", "SC-04", "SC-05", "SC-06", "SC-08", "SC-09", "SC-10", "SC-12"}


def scalar(connection: object, query: str, params: tuple[object, ...] = ()) -> object:
    return connection.execute(query, params).fetchone()[0]


def rows(
    connection: object,
    query: str,
    params: tuple[object, ...] = (),
) -> list[tuple[object, ...]]:
    return connection.execute(query, params).fetchall()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check EEI PostgreSQL schema invariants.")
    parser.add_argument(
        "--expect-seeds",
        action="store_true",
        help="Check deterministic seed counts.",
    )
    parser.add_argument(
        "--expect-fixtures",
        action="store_true",
        help="Check synthetic fixture invariants.",
    )
    parser.add_argument(
        "--expect-curated-ingestion",
        action="store_true",
        help="Check curated official ingestion anchor invariants.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with connect_database() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
            ).fetchall()
        }
        missing = sorted(REQUIRED_TABLES - tables)
        if missing:
            raise RuntimeError(f"Missing required tables: {', '.join(missing)}")

        extension_rows = rows(
            connection,
            """
            SELECT extname
            FROM pg_extension
            WHERE extname IN ('pgcrypto', 'pg_trgm')
            """,
        )
        extensions = {str(row[0]) for row in extension_rows}
        missing_extensions = sorted({"pgcrypto", "pg_trgm"} - extensions)
        if missing_extensions:
            raise RuntimeError(f"Missing required PostgreSQL extensions: {missing_extensions}")

        column_rows = rows(
            connection,
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            """,
        )
        columns_by_table: dict[str, set[str]] = {}
        for table_name, column_name in column_rows:
            columns_by_table.setdefault(str(table_name), set()).add(str(column_name))

        entity_type_rows = rows(
            connection,
            """
            SELECT enumlabel
            FROM pg_enum
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
            WHERE pg_type.typname = 'entity_type'
            """,
        )
        entity_type_values = {str(row[0]) for row in entity_type_rows}
        missing_entity_types = sorted(REQUIRED_ENTITY_TYPES - entity_type_values)
        if missing_entity_types:
            raise RuntimeError(f"Missing entity type labels: {missing_entity_types}")

        supply_chain_columns = columns_by_table.get("supply_chain_relationship_attributes", set())
        missing_supply_chain_columns = sorted(
            REQUIRED_SUPPLY_CHAIN_ATTRIBUTE_COLUMNS - supply_chain_columns
        )
        if missing_supply_chain_columns:
            raise RuntimeError(
                f"Missing supply-chain attribute columns: {missing_supply_chain_columns}"
            )

        exploration_session_columns = columns_by_table.get("exploration_sessions", set())
        missing_exploration_columns = sorted(
            REQUIRED_EXPLORATION_SESSION_COLUMNS - exploration_session_columns
        )
        if missing_exploration_columns:
            raise RuntimeError(
                f"Missing exploration session columns: {missing_exploration_columns}"
            )

        for table_name, required_columns in REQUIRED_TEMPORAL_COLUMNS.items():
            missing_temporal_columns = sorted(
                required_columns - columns_by_table.get(table_name, set())
            )
            if missing_temporal_columns:
                raise RuntimeError(
                    f"{table_name} missing temporal columns: {missing_temporal_columns}"
                )

        for table_name, required_columns in REQUIRED_PRODUCTION_VERSION_COLUMNS.items():
            missing_version_columns = sorted(
                required_columns - columns_by_table.get(table_name, set())
            )
            if missing_version_columns:
                raise RuntimeError(
                    f"{table_name} missing production version columns: {missing_version_columns}"
                )

        for table_name, required_columns in REQUIRED_CURATED_INGESTION_COLUMNS.items():
            missing_curated_columns = sorted(
                required_columns - columns_by_table.get(table_name, set())
            )
            if missing_curated_columns:
                raise RuntimeError(
                    f"{table_name} missing curated ingestion columns: {missing_curated_columns}"
                )

        production_index_rows = rows(
            connection,
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname IN (
                'data_snapshots_one_active_per_scope_mode_idx',
                'fact_versions_object_idx',
                'fact_versions_snapshot_status_idx',
                'fact_versions_time_idx'
              )
            """,
        )
        production_indexes = {str(row[0]) for row in production_index_rows}
        missing_production_indexes = sorted(
            {
                "data_snapshots_one_active_per_scope_mode_idx",
                "fact_versions_object_idx",
                "fact_versions_snapshot_status_idx",
                "fact_versions_time_idx",
            }
            - production_indexes
        )
        if missing_production_indexes:
            raise RuntimeError(
                f"Missing production version indexes: {missing_production_indexes}"
            )

        curated_index_rows = rows(
            connection,
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname = ANY(%s)
            """,
            (list(REQUIRED_CURATED_INGESTION_INDEXES),),
        )
        curated_indexes = {str(row[0]) for row in curated_index_rows}
        missing_curated_indexes = sorted(REQUIRED_CURATED_INGESTION_INDEXES - curated_indexes)
        if missing_curated_indexes:
            raise RuntimeError(f"Missing curated ingestion indexes: {missing_curated_indexes}")

        payload: dict[str, object] = {
            "required_tables": len(REQUIRED_TABLES),
            "missing_tables": missing,
            "required_extensions": sorted(extensions),
            "required_entity_types": sorted(REQUIRED_ENTITY_TYPES),
            "supply_chain_attribute_columns": sorted(REQUIRED_SUPPLY_CHAIN_ATTRIBUTE_COLUMNS),
            "exploration_session_columns": sorted(REQUIRED_EXPLORATION_SESSION_COLUMNS),
            "temporal_tables_checked": sorted(REQUIRED_TEMPORAL_COLUMNS),
            "production_version_tables_checked": sorted(REQUIRED_PRODUCTION_VERSION_COLUMNS),
            "production_version_indexes": sorted(production_indexes),
            "curated_ingestion_tables_checked": sorted(REQUIRED_CURATED_INGESTION_COLUMNS),
            "curated_ingestion_indexes": sorted(curated_indexes),
            "seed_counts": {},
        }

        if args.expect_seeds:
            seed_counts: dict[str, int] = {}
            for table, expected in SEED_EXPECTATIONS.items():
                count = int(scalar(connection, f"SELECT count(*) FROM {table}"))
                seed_counts[table] = count
                if count != expected:
                    raise RuntimeError(f"{table} expected {expected} rows, found {count}")

            p0_count = int(scalar(
                connection,
                "SELECT count(*) FROM company_research_universe WHERE tier = 'P0'",
            ))
            tier_rows = rows(
                connection,
                """
                SELECT tier, count(*)
                FROM company_research_universe
                GROUP BY tier
                """,
            )
            tier_counts = {str(row[0]): int(row[1]) for row in tier_rows}
            live_entity_count = int(
                scalar(connection, "SELECT count(*) FROM entities WHERE status <> 'fixture'")
            )
            industry_child_count = int(
                scalar(connection, "SELECT count(*) FROM industries WHERE parent_id IS NOT NULL")
            )
            industry_membership_table_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'entity_industry_memberships'
                    """,
                )
            )
            if p0_count != 30:
                raise RuntimeError(f"P0 research universe expected 30 rows, found {p0_count}")
            if tier_counts != RESEARCH_TIER_EXPECTATIONS:
                raise RuntimeError(
                    f"Research universe tier counts expected {RESEARCH_TIER_EXPECTATIONS}, "
                    f"found {tier_counts}"
                )
            if industry_child_count < 1:
                raise RuntimeError("Industry taxonomy must include parent/child rows")
            if industry_membership_table_count != 1:
                raise RuntimeError("Missing multi-label industry membership table")
            if live_entity_count != 0:
                raise RuntimeError(
                    "Seeded research universe/fixtures must not create live entity facts"
                )
            active_profile_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM scoring_profile_versions
                    WHERE active = true
                    """,
                )
            )
            weight_sum = float(
                scalar(
                    connection,
                    """
                    SELECT COALESCE(sum((value)::numeric), 0)
                    FROM scoring_profile_versions spv,
                         jsonb_each_text(spv.weights)
                    WHERE spv.active = true
                    """,
                )
            )
            calibration_cadence_violations = int(
                scalar(connection, "SELECT count(*) FROM calibration_runs WHERE cadence_days <> 14")
            )
            if active_profile_count != 1:
                raise RuntimeError(
                    f"Expected exactly one active scoring profile, found {active_profile_count}"
                )
            if abs(weight_sum - 1.0) > 0.0001:
                raise RuntimeError(
                    f"Active scoring profile weights must sum to 1.0, found {weight_sum}"
                )
            if calibration_cadence_violations:
                raise RuntimeError("Calibration cadence must remain fixed at 14 days")
            payload["seed_counts"] = seed_counts | {
                "p0_research_universe": p0_count,
                "research_tiers": tier_counts,
                "industry_child_rows": industry_child_count,
                "industry_membership_tables": industry_membership_table_count,
                "live_entities": live_entity_count,
                "active_scoring_profiles": active_profile_count,
                "active_profile_weight_sum": round(weight_sum, 4),
                "calibration_cadence_violations": calibration_cadence_violations,
            }

        if args.expect_fixtures:
            fixture_counts: dict[str, int] = {}
            for table, expected in FIXTURE_EXPECTATIONS.items():
                count = int(scalar(connection, f"SELECT count(*) FROM {table}"))
                fixture_counts[table] = count
                if count != expected:
                    raise RuntimeError(f"{table} expected {expected} rows, found {count}")

            non_fixture_entities = int(
                scalar(connection, "SELECT count(*) FROM entities WHERE status <> 'fixture'")
            )
            unmarked_relationships = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM relationships r
                    LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
                    WHERE frn.synthetic IS DISTINCT FROM true
                    """,
                )
            )
            family_rows = connection.execute(
                "SELECT DISTINCT relationship_family FROM relationships"
            ).fetchall()
            fixture_families = {row[0] for row in family_rows}
            missing_families = sorted(REQUIRED_FIXTURE_FAMILIES - fixture_families)
            stage_rows = connection.execute(
                """
                SELECT DISTINCT stage
                FROM (
                  SELECT stage_from AS stage FROM supply_chain_relationship_attributes
                  UNION
                  SELECT stage_to AS stage FROM supply_chain_relationship_attributes
                ) stages
                WHERE stage IS NOT NULL
                """
            ).fetchall()
            fixture_stages = {row[0] for row in stage_rows}
            missing_stages = sorted(REQUIRED_NVIDIA_STAGES - fixture_stages)
            if non_fixture_entities:
                raise RuntimeError("Synthetic fixture load created non-fixture entities")
            if unmarked_relationships:
                raise RuntimeError("Synthetic fixture relationships must have fixture notices")
            if missing_families:
                raise RuntimeError(f"Missing fixture relationship families: {missing_families}")
            if missing_stages:
                raise RuntimeError(
                    f"Missing NVIDIA synthetic supply-chain stages: {missing_stages}"
                )

            publishable_relationships_without_evidence = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM (
                      SELECT r.id
                      FROM relationships r
                      LEFT JOIN relationship_evidence re ON re.relationship_id = r.id
                      WHERE r.status IN ('reported', 'derived', 'disputed', 'unknown')
                      GROUP BY r.id
                      HAVING count(re.source_document_id) = 0
                    ) missing_relationship_evidence
                    """,
                )
                or 0
            )
            publishable_events_without_evidence = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM (
                      SELECT e.id
                      FROM events e
                      LEFT JOIN event_evidence ee ON ee.event_id = e.id
                      WHERE e.status IN ('reported', 'derived', 'disputed', 'unknown')
                      GROUP BY e.id
                      HAVING count(ee.source_document_id) = 0
                    ) missing_event_evidence
                    """,
                )
                or 0
            )
            unknown_relationships = int(
                scalar(connection, "SELECT count(*) FROM relationships WHERE status = 'unknown'")
            )
            unknown_relationships_coerced_to_zero = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM relationships
                    WHERE status = 'unknown'
                      AND (amount = 0 OR percentage = 0 OR confidence = 0)
                    """,
                )
            )
            amount_semantic_violations = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM relationships
                    WHERE amount IS NOT NULL
                      AND (currency IS NULL OR amount_kind IS NULL)
                    """,
                )
            )
            amount_buckets = rows(
                connection,
                """
                SELECT amount_kind, currency, count(*)
                FROM relationships
                WHERE amount IS NOT NULL
                GROUP BY amount_kind, currency
                ORDER BY amount_kind, currency
                """,
            )
            if publishable_relationships_without_evidence:
                raise RuntimeError("Publishable relationships must have evidence")
            if publishable_events_without_evidence:
                raise RuntimeError("Publishable events must have evidence")
            if unknown_relationships < 1:
                raise RuntimeError("Unknown relationship fixtures must remain explicitly unknown")
            if unknown_relationships_coerced_to_zero:
                raise RuntimeError("Unknown relationships must not be coerced to zero")
            if amount_semantic_violations:
                raise RuntimeError("Amounts require currency and amount_kind")
            payload["fixture_counts"] = fixture_counts | {
                "non_fixture_entities": non_fixture_entities,
                "unmarked_relationships": unmarked_relationships,
                "relationship_families": len(fixture_families),
                "nvidia_supply_chain_stages": len(fixture_stages),
                "publishable_relationships_without_evidence": (
                    publishable_relationships_without_evidence
                ),
                "publishable_events_without_evidence": publishable_events_without_evidence,
                "unknown_relationships": unknown_relationships,
                "unknown_relationships_coerced_to_zero": unknown_relationships_coerced_to_zero,
                "amount_semantic_violations": amount_semantic_violations,
                "amount_buckets": [
                    {"amount_kind": row[0], "currency": row[1], "row_count": int(row[2])}
                    for row in amount_buckets
                ],
            }

        if args.expect_curated_ingestion:
            parser_version = CURATED_ANCHOR_PARSER_VERSION
            raw_snapshot_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM raw_source_snapshots
                    WHERE parser_version = %s
                      AND record_mode = 'curated_official_fixture'
                    """,
                    (parser_version,),
                )
            )
            raw_snapshot_field_violations = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM raw_source_snapshots
                    WHERE parser_version = %s
                      AND (
                        anchor_id = ''
                        OR source_url = ''
                        OR content_hash = ''
                        OR jsonb_typeof(raw_payload) <> 'object'
                        OR review_status NOT IN (
                          'unreviewed','machine_verified','human_verified','disputed'
                        )
                      )
                    """,
                    (parser_version,),
                )
            )
            source_document_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(DISTINCT sd.id)
                    FROM raw_source_snapshots rss
                    JOIN source_documents sd ON sd.id = rss.source_document_id
                    WHERE rss.parser_version = %s
                      AND sd.parser_version = %s
                      AND (
                        sd.raw_storage_uri LIKE 'data/nvidia_public_source_anchors.csv#%%'
                        OR sd.raw_storage_uri LIKE 'data/golden_vertical_fact_candidates.json#%%'
                      )
                    """,
                    (parser_version, parser_version),
                )
            )
            candidate_row = rows(
                connection,
                """
                SELECT
                  count(*) AS total,
                  count(*) FILTER (WHERE confidence >= 0.72) AS above_min_confidence,
                  count(*) FILTER (WHERE review_status = 'machine_verified') AS verified,
                  count(*) FILTER (WHERE matched_research_id IS NOT NULL) AS matched_research
                FROM entity_resolution_candidates
                WHERE parser_version = %s
                """,
                (parser_version,),
            )[0]
            evidence_row = rows(
                connection,
                """
                SELECT
                  count(*) AS total,
                  count(*) FILTER (WHERE jsonb_typeof(counter_evidence) = 'array') AS counters,
                  count(*) FILTER (WHERE review_status = 'machine_verified') AS verified,
                  count(*) FILTER (WHERE evidence_role = 'context') AS context_rows,
                  count(*) FILTER (WHERE evidence_role = 'supports') AS support_rows,
                  count(*) FILTER (WHERE relationship_type IS NOT NULL) AS typed_candidate_rows
                FROM ingestion_evidence_chain
                WHERE parser_version = %s
                """,
                (parser_version,),
            )[0]
            nvidia_subject_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM entity_resolution_candidates
                    WHERE parser_version = %s
                      AND candidate_name = 'NVIDIA Corporation'
                      AND matched_research_id = 'P0-006'
                      AND match_method = 'anchor_subject'
                    """,
                    (parser_version,),
                )
            )
            tsmc_candidate_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM entity_resolution_candidates
                    WHERE parser_version = %s
                      AND candidate_name = 'TSMC'
                      AND matched_research_id = 'X-001'
                      AND confidence >= 0.72
                    """,
                    (parser_version,),
                )
            )
            if raw_snapshot_count != 6:
                raise RuntimeError(
                    f"Expected 6 curated official raw snapshots, found {raw_snapshot_count}"
                )
            if raw_snapshot_field_violations:
                raise RuntimeError(
                    "Curated raw snapshots must preserve hash, payload and review state"
                )
            if source_document_count != 6:
                raise RuntimeError(
                    "Curated source documents must preserve parser version and raw storage URI"
                )
            if int(candidate_row[0]) < 55:
                raise RuntimeError("Curated ingestion must create entity/stage candidates")
            if int(candidate_row[1]) < 10:
                raise RuntimeError("Curated entity resolution must record confidence values")
            if int(candidate_row[2]) < 4:
                raise RuntimeError("Curated entity resolution must record review status")
            if int(candidate_row[3]) < 6:
                raise RuntimeError("Curated entity resolution must map known catalog entities")
            if int(evidence_row[0]) != 6:
                raise RuntimeError(
                    "Curated ingestion evidence chain must contain six rows"
                )
            if int(evidence_row[1]) != int(evidence_row[0]):
                raise RuntimeError("Curated evidence chain counter_evidence must be an array")
            if int(evidence_row[2]) != int(evidence_row[0]):
                raise RuntimeError("Curated evidence chain must preserve review status")
            if int(evidence_row[3]) != 4:
                raise RuntimeError(
                    "Curated ingestion evidence chain must include four context rows"
                )
            if int(evidence_row[4]) != 2:
                raise RuntimeError("Curated ingestion evidence chain must include two support rows")
            if int(evidence_row[5]) != 2:
                raise RuntimeError("Curated Golden Vertical must include typed candidate evidence")
            if nvidia_subject_count != 4:
                raise RuntimeError("Every curated anchor must resolve the NVIDIA subject")
            if tsmc_candidate_count < 2:
                raise RuntimeError("Golden Vertical TSMC candidate resolution is missing")
            fact_candidate_row = rows(
                connection,
                """
                SELECT
                  count(*) AS total,
                  count(*) FILTER (WHERE publication_status = 'candidate') AS candidates,
                  count(*) FILTER (WHERE source_threshold_met = false) AS below_threshold,
                  count(*) FILTER (WHERE review_status = 'machine_verified') AS verified,
                  count(*) FILTER (WHERE jsonb_typeof(counter_evidence) = 'array') AS counters
                FROM relationship_fact_candidates
                WHERE parser_version = %s
                """,
                (parser_version,),
            )[0]
            fact_evidence_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM relationship_fact_candidate_evidence rfce
                    JOIN relationship_fact_candidates rfc ON rfc.id = rfce.candidate_id
                    WHERE rfc.parser_version = %s
                    """,
                    (parser_version,),
                )
            )
            review_queue_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM manual_review_queue mrq
                    JOIN relationship_fact_candidates rfc ON rfc.id = mrq.object_id
                    WHERE mrq.object_type = 'relationship_fact_candidate'
                      AND mrq.status = 'open'
                      AND rfc.parser_version = %s
                    """,
                    (parser_version,),
                )
            )
            golden_path_candidate_count = int(
                scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM relationship_fact_candidates rfc
                    WHERE rfc.parser_version = %s
                      AND rfc.structured_fact->>'path_role' IN (
                        'NVIDIA_TO_TSMC_GOLDEN_VERTICAL',
                        'TSMC_TO_ASML_GOLDEN_VERTICAL'
                      )
                    """,
                    (parser_version,),
                )
            )
            if int(fact_candidate_row[0]) != 2:
                raise RuntimeError("Golden Vertical must load two relationship fact candidates")
            if int(fact_candidate_row[1]) != 2:
                raise RuntimeError("Golden Vertical fact candidates must remain candidate status")
            if int(fact_candidate_row[2]) != 2:
                raise RuntimeError(
                    "Single-source fact candidates must remain below source threshold"
                )
            if int(fact_candidate_row[3]) != 2:
                raise RuntimeError("Fact candidates must preserve machine review status")
            if int(fact_candidate_row[4]) != 2:
                raise RuntimeError("Fact candidates must preserve counter_evidence arrays")
            if fact_evidence_count != 2:
                raise RuntimeError("Fact candidates must link to evidence chain rows")
            if review_queue_count != 2:
                raise RuntimeError("Fact candidates must create open review queue items")
            if golden_path_candidate_count != 2:
                raise RuntimeError("Golden Vertical NVIDIA-TSMC-ASML candidate path is missing")
            payload["curated_ingestion_counts"] = {
                "parser_version": parser_version,
                "raw_source_snapshots": raw_snapshot_count,
                "raw_snapshot_field_violations": raw_snapshot_field_violations,
                "source_documents": source_document_count,
                "entity_resolution_candidates": int(candidate_row[0]),
                "entity_candidates_above_min_confidence": int(candidate_row[1]),
                "entity_candidates_machine_verified": int(candidate_row[2]),
                "entity_candidates_matched_research": int(candidate_row[3]),
                "ingestion_evidence_chain": int(evidence_row[0]),
                "counter_evidence_arrays": int(evidence_row[1]),
                "evidence_chain_machine_verified": int(evidence_row[2]),
                "context_evidence_rows": int(evidence_row[3]),
                "support_evidence_rows": int(evidence_row[4]),
                "typed_candidate_evidence_rows": int(evidence_row[5]),
                "nvidia_subject_candidates": nvidia_subject_count,
                "tsmc_candidates": tsmc_candidate_count,
                "relationship_fact_candidates": int(fact_candidate_row[0]),
                "fact_candidate_evidence_rows": fact_evidence_count,
                "open_review_queue_items": review_queue_count,
                "golden_path_candidate_rows": golden_path_candidate_count,
            }

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Database schema check failed: {exc}")
        raise SystemExit(1) from exc
