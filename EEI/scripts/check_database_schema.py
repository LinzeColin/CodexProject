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

REQUIRED_TEMPORAL_COLUMNS = {
    "relationships": {"valid_from", "valid_to", "announced_at", "filed_at", "observed_at"},
    "events": {"announced_at", "effective_at", "period_start", "period_end", "observed_at"},
    "source_documents": {"document_date", "observed_at", "retrieved_at"},
    "ingestion_runs": {"started_at", "finished_at"},
}

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

        for table_name, required_columns in REQUIRED_TEMPORAL_COLUMNS.items():
            missing_temporal_columns = sorted(
                required_columns - columns_by_table.get(table_name, set())
            )
            if missing_temporal_columns:
                raise RuntimeError(
                    f"{table_name} missing temporal columns: {missing_temporal_columns}"
                )

        payload: dict[str, object] = {
            "required_tables": len(REQUIRED_TABLES),
            "missing_tables": missing,
            "required_entity_types": sorted(REQUIRED_ENTITY_TYPES),
            "supply_chain_attribute_columns": sorted(REQUIRED_SUPPLY_CHAIN_ATTRIBUTE_COLUMNS),
            "temporal_tables_checked": sorted(REQUIRED_TEMPORAL_COLUMNS),
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

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Database schema check failed: {exc}")
        raise SystemExit(1) from exc
