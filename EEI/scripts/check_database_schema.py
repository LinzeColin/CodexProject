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
}

SEED_EXPECTATIONS = {
    "relationship_families": 10,
    "relationship_type_catalog": 52,
    "industries": 26,
    "supply_chain_stages": 16,
    "company_research_universe": 140,
}


def scalar(connection: object, query: str, params: tuple[object, ...] = ()) -> object:
    return connection.execute(query, params).fetchone()[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check EEI PostgreSQL schema invariants.")
    parser.add_argument(
        "--expect-seeds",
        action="store_true",
        help="Check deterministic seed counts.",
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

        payload: dict[str, object] = {
            "required_tables": len(REQUIRED_TABLES),
            "missing_tables": missing,
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
            live_entity_count = int(scalar(connection, "SELECT count(*) FROM entities"))
            if p0_count != 30:
                raise RuntimeError(f"P0 research universe expected 30 rows, found {p0_count}")
            if live_entity_count != 0:
                raise RuntimeError("Seeded research universe must not create live entity facts")
            payload["seed_counts"] = seed_counts | {
                "p0_research_universe": p0_count,
                "live_entities": live_entity_count,
            }

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Database schema check failed: {exc}")
        raise SystemExit(1) from exc
