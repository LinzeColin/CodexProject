#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from db_tools import ROOT, connect_database
from psycopg.types.json import Jsonb


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def record_seed_run(connection: object, seed_name: str, path: Path, row_count: int) -> None:
    source_path = path.relative_to(ROOT).as_posix()
    connection.execute(
        """
        INSERT INTO seed_runs(seed_name, source_path, source_hash, row_count, status)
        VALUES (%s, %s, %s, %s, 'loaded')
        ON CONFLICT (source_path, source_hash) DO UPDATE SET
          seed_name = EXCLUDED.seed_name,
          row_count = EXCLUDED.row_count,
          status = EXCLUDED.status,
          loaded_at = now()
        """,
        (seed_name, source_path, file_hash(path), row_count),
    )


def load_relationship_families(connection: object) -> int:
    path = ROOT / "data/relationship_family_catalog.csv"
    rows = read_csv(path)
    for row in rows:
        connection.execute(
            """
            INSERT INTO relationship_families(
              family_key, family_id, name_zh, slug, default_graph_zone, definition,
              relationship_type_count, default_evidence_threshold, default_visual_encoding,
              recursive_pivot
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (family_key) DO UPDATE SET
              family_id = EXCLUDED.family_id,
              name_zh = EXCLUDED.name_zh,
              slug = EXCLUDED.slug,
              default_graph_zone = EXCLUDED.default_graph_zone,
              definition = EXCLUDED.definition,
              relationship_type_count = EXCLUDED.relationship_type_count,
              default_evidence_threshold = EXCLUDED.default_evidence_threshold,
              default_visual_encoding = EXCLUDED.default_visual_encoding,
              recursive_pivot = EXCLUDED.recursive_pivot,
              loaded_at = now()
            """,
            (
                row["family_key"],
                row["family_id"],
                row["name_zh"],
                row["slug"],
                row["default_graph_zone"],
                row["definition"],
                int(row["relationship_type_count"]),
                row["default_evidence_threshold"],
                row["default_visual_encoding"],
                as_bool(row["recursive_pivot"]),
            ),
        )
    record_seed_run(connection, "relationship_families", path, len(rows))
    return len(rows)


def load_relationship_types(connection: object) -> int:
    path = ROOT / "data/relationship_taxonomy.csv"
    rows = read_csv(path)
    for row in rows:
        connection.execute(
            """
            INSERT INTO relationship_type_catalog(
              relationship_type,
              family_key,
              direction,
              amount_allowed,
              percentage_allowed,
              definition
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (relationship_type) DO UPDATE SET
              family_key = EXCLUDED.family_key,
              direction = EXCLUDED.direction,
              amount_allowed = EXCLUDED.amount_allowed,
              percentage_allowed = EXCLUDED.percentage_allowed,
              definition = EXCLUDED.definition,
              loaded_at = now()
            """,
            (
                row["relationship_type"],
                row["family"],
                row["direction"],
                as_bool(row["amount_allowed"]),
                as_bool(row["percentage_allowed"]),
                row["definition"],
            ),
        )
    record_seed_run(connection, "relationship_types", path, len(rows))
    return len(rows)


def load_industries(connection: object) -> int:
    path = ROOT / "data/industry_taxonomy.csv"
    rows = read_csv(path)
    for row in rows:
        connection.execute(
            """
            INSERT INTO industries(external_id, slug, name_zh, name_en, kind, taxonomy_version)
            VALUES (%s, %s, %s, %s, %s, 'v4.2.0')
            ON CONFLICT (slug) DO UPDATE SET
              external_id = EXCLUDED.external_id,
              name_zh = EXCLUDED.name_zh,
              name_en = EXCLUDED.name_en,
              kind = EXCLUDED.kind,
              taxonomy_version = EXCLUDED.taxonomy_version
            """,
            (
                row["industry_id"],
                row["slug"],
                row["name_zh"],
                row["name_en"],
                row["kind"],
            ),
        )
    for row in rows:
        if not row["parent_id"]:
            connection.execute(
                "UPDATE industries SET parent_id = NULL WHERE external_id = %s",
                (row["industry_id"],),
            )
            continue
        connection.execute(
            """
            UPDATE industries child
            SET parent_id = parent.id
            FROM industries parent
            WHERE child.external_id = %s AND parent.external_id = %s
            """,
            (row["industry_id"], row["parent_id"]),
        )
    record_seed_run(connection, "industries", path, len(rows))
    return len(rows)


def load_supply_chain_stages(connection: object) -> int:
    path = ROOT / "data/supply_chain_stage_taxonomy.csv"
    rows = read_csv(path)
    for row in rows:
        connection.execute(
            """
            INSERT INTO supply_chain_stages(
              stage_id, stage_order, slug, name_zh, name_en, default_direction, examples
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (stage_id) DO UPDATE SET
              stage_order = EXCLUDED.stage_order,
              slug = EXCLUDED.slug,
              name_zh = EXCLUDED.name_zh,
              name_en = EXCLUDED.name_en,
              default_direction = EXCLUDED.default_direction,
              examples = EXCLUDED.examples,
              loaded_at = now()
            """,
            (
                row["stage_id"],
                int(row["stage_order"]),
                row["slug"],
                row["name_zh"],
                row["name_en"],
                row["default_direction"],
                row["examples"],
            ),
        )
    record_seed_run(connection, "supply_chain_stages", path, len(rows))
    return len(rows)


def load_research_universe(connection: object) -> int:
    path = ROOT / "data/research_universe.csv"
    rows = read_csv(path)
    for row in rows:
        connection.execute(
            """
            INSERT INTO company_research_universe(
              research_id, tier, canonical_name, power_system, initial_form,
              research_focus, verification_status, source_path
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (research_id) DO UPDATE SET
              tier = EXCLUDED.tier,
              canonical_name = EXCLUDED.canonical_name,
              power_system = EXCLUDED.power_system,
              initial_form = EXCLUDED.initial_form,
              research_focus = EXCLUDED.research_focus,
              verification_status = EXCLUDED.verification_status,
              data_mode = 'research_target_not_verified_fact',
              source_path = EXCLUDED.source_path,
              loaded_at = now()
            """,
            (
                row["research_id"],
                row["tier"],
                row["canonical_name"],
                row["power_system"],
                row["initial_form"],
                row["research_focus"],
                row["verification_status"],
                path.relative_to(ROOT).as_posix(),
            ),
        )
    record_seed_run(connection, "research_universe", path, len(rows))
    return len(rows)


def load_default_scoring_profile(connection: object) -> int:
    profile_path = ROOT / "config/model_profiles/balanced-v2.json"
    threshold_path = ROOT / "config/thresholds/default-v2.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    thresholds = json.loads(threshold_path.read_text(encoding="utf-8"))
    model_key = profile["model_version"]
    version = int(profile["version"])
    model_row = connection.execute(
        """
        INSERT INTO scoring_models(model_key, version, name, formula, input_schema, status)
        VALUES (%s, %s, %s, %s, %s, 'active')
        ON CONFLICT (model_key, version) DO UPDATE SET
          name = EXCLUDED.name,
          formula = EXCLUDED.formula,
          input_schema = EXCLUDED.input_schema,
          status = 'active'
        RETURNING id
        """,
        (
            model_key,
            version,
            profile["name"],
            Jsonb(profile),
            Jsonb(
                {
                    "schema_version": profile["schema_version"],
                    "components": list(profile["weights"].keys()),
                    "component_weights": profile["component_weights"],
                }
            ),
        ),
    ).fetchone()
    profile_row = connection.execute(
        """
        INSERT INTO scoring_profiles(namespace, profile_key, name, is_system_default)
        VALUES ('system', %s, %s, true)
        ON CONFLICT (namespace, profile_key) DO UPDATE SET
          name = EXCLUDED.name,
          is_system_default = true
        RETURNING id
        """,
        (profile["profile_key"], profile["name"]),
    ).fetchone()
    connection.execute(
        """
        UPDATE scoring_profile_versions
        SET active = false
        WHERE profile_id = %s
        """,
        (profile_row[0],),
    )
    profile_version_row = connection.execute(
        """
        INSERT INTO scoring_profile_versions(
          profile_id, model_id, version, weights, thresholds, half_lives,
          missing_value_policy, reason, active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
        ON CONFLICT (profile_id, version) DO UPDATE SET
          model_id = EXCLUDED.model_id,
          weights = EXCLUDED.weights,
          thresholds = EXCLUDED.thresholds,
          half_lives = EXCLUDED.half_lives,
          missing_value_policy = EXCLUDED.missing_value_policy,
          reason = EXCLUDED.reason,
          active = true
        RETURNING id
        """,
        (
            profile_row[0],
            model_row[0],
            version,
            Jsonb(profile["weights"]),
            Jsonb(thresholds),
            Jsonb(profile["half_life_days"]),
            profile["missing_value_policy"],
            "Seeded from config/model_profiles/balanced-v2.json for MVP default profile.",
        ),
    ).fetchone()
    connection.execute(
        """
        INSERT INTO active_analysis_contexts(
          context_key, active_scoring_profile_version_id, status, activated_by,
          affected_modules, metadata
        )
        VALUES ('global', %s, 'active', 'system', %s, %s)
        ON CONFLICT (context_key) DO UPDATE SET
          active_scoring_profile_version_id = EXCLUDED.active_scoring_profile_version_id,
          status = 'active',
          activated_by = 'system',
          affected_modules = EXCLUDED.affected_modules,
          metadata = active_analysis_contexts.metadata || EXCLUDED.metadata,
          updated_at = now()
        """,
        (
            profile_version_row[0],
            Jsonb(
                [
                    "business_empire",
                    "group_structure",
                    "business_segments",
                    "supply_chain",
                    "capital_network",
                    "ma_transactions",
                    "control_relationships",
                    "policy_environment",
                    "strategic_signals",
                    "watchlist",
                    "evidence_center",
                    "model_center",
                    "data_center",
                ]
            ),
            Jsonb(
                {
                    "source": "seed_default_scoring_profile",
                    "profile_key": profile["profile_key"],
                    "profile_version": version,
                    "model_version": model_key,
                    "cache_policy": "clients compare refresh_token and refresh_generation",
                }
            ),
        ),
    )
    record_seed_run(connection, "default_scoring_profile", profile_path, 1)
    record_seed_run(connection, "default_threshold_profile", threshold_path, 1)
    return 1


def main() -> int:
    with connect_database() as connection:
        counts = {
            "relationship_families": load_relationship_families(connection),
            "relationship_types": load_relationship_types(connection),
            "industries": load_industries(connection),
            "supply_chain_stages": load_supply_chain_stages(connection),
            "research_universe": load_research_universe(connection),
            "default_scoring_profiles": load_default_scoring_profile(connection),
        }
    print("Seed catalogs loaded:")
    for name, count in counts.items():
        print(f"  {name}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
