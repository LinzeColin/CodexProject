#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from db_tools import ROOT, connect_database
from psycopg.types.json import Jsonb

DATASET_KEY = "synthetic_nvidia_recursive_supply_chain_v1"
OBSERVED_AT = "2026-01-01T00:00:00Z"
ENTITY_INDUSTRY_MEMBERSHIPS = {
    "amazon": [("IND-002-02", "primary", 0.9)],
    "anthropic": [("IND-002-01", "primary", 0.92)],
    "coreweave": [("IND-002-03", "primary", 0.95), ("IND-001", "secondary", 0.78)],
    "microsoft": [("IND-002-02", "primary", 0.93), ("IND-003", "secondary", 0.86)],
    "nvidia": [("IND-001", "primary", 0.96), ("IND-002", "secondary", 0.72)],
    "openai_group": [("IND-002-01", "primary", 0.94), ("IND-003", "secondary", 0.7)],
    "palantir": [("IND-003", "primary", 0.91), ("IND-008", "secondary", 0.7)],
    "tsmc": [("IND-001-02", "primary", 0.95), ("IND-001", "supply_chain", 0.91)],
    "fixture_foundry": [("IND-001-02", "primary", 0.9)],
    "fixture_equipment": [("IND-001-04", "primary", 0.9)],
    "fixture_materials": [("IND-001-04", "primary", 0.82)],
    "fixture_datacenter": [("IND-002-03", "primary", 0.88), ("IND-010", "secondary", 0.72)],
    "fixture_utility": [("IND-006", "primary", 0.86), ("IND-013", "secondary", 0.64)],
    "fixture_integrator": [("IND-009", "primary", 0.82), ("IND-001", "secondary", 0.7)],
    "fixture_cloud_customer": [("IND-002-02", "primary", 0.84)],
}


def read_json(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def dataset_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def ensure_dataset(connection: object, paths: list[Path]) -> None:
    connection.execute(
        """
        INSERT INTO fixture_datasets(dataset_key, description, source_hash, synthetic)
        VALUES (%s, %s, %s, true)
        ON CONFLICT (dataset_key) DO UPDATE SET
          description = EXCLUDED.description,
          source_hash = EXCLUDED.source_hash,
          synthetic = true,
          loaded_at = now()
        """,
        (
            DATASET_KEY,
            "Synthetic NVIDIA recursive supply-chain fixture for MVP tests.",
            dataset_hash(paths),
        ),
    )


def ensure_fixture_source(connection: object) -> str:
    row = connection.execute(
        """
        INSERT INTO sources(
          code, name, base_url, source_tier, expected_cadence, terms_notes, active
        )
        VALUES (
          'synthetic_fixture',
          'EEI Synthetic Fixture Source',
          'fixture://eei',
          5,
          'static',
          'Synthetic fixture records only; never present as live facts.',
          true
        )
        ON CONFLICT (code) DO UPDATE SET
          name = EXCLUDED.name,
          base_url = EXCLUDED.base_url,
          source_tier = EXCLUDED.source_tier,
          expected_cadence = EXCLUDED.expected_cadence,
          terms_notes = EXCLUDED.terms_notes,
          active = true
        RETURNING id
        """
    ).fetchone()
    return str(row[0])


def load_entities(connection: object, entities: list[dict[str, object]]) -> None:
    for entity in entities:
        connection.execute(
            """
            INSERT INTO entities(id, canonical_name, entity_type, status, description)
            VALUES (%s, %s, %s, 'fixture', %s)
            ON CONFLICT (id) DO UPDATE SET
              canonical_name = EXCLUDED.canonical_name,
              entity_type = EXCLUDED.entity_type,
              status = 'fixture',
              description = EXCLUDED.description,
              updated_at = now()
            """,
            (
                entity["id"],
                entity["canonical_name"],
                entity["entity_type"],
                entity["fixture_notice"],
            ),
        )
        for identifier in entity.get("identifiers", []):
            connection.execute(
                """
                INSERT INTO entity_identifiers(entity_id, scheme, value, issuer)
                VALUES (%s, %s, %s, 'synthetic_fixture')
                ON CONFLICT (scheme, value) DO UPDATE SET
                  entity_id = EXCLUDED.entity_id,
                  issuer = EXCLUDED.issuer
                """,
                (entity["id"], identifier["scheme"], identifier["value"]),
            )
        alias_values: set[tuple[str, str]] = {
            (str(entity["entity_key"]), "fixture_key"),
            (str(entity["entity_key"]).replace("_", " "), "fixture_key_words"),
        }
        canonical_name = str(entity["canonical_name"])
        short_name = canonical_name.replace(" Corporation", "").replace(", Inc.", "")
        alias_values.add((short_name.replace(" (Synthetic)", ""), "short_name"))
        for identifier in entity.get("identifiers", []):
            if identifier["scheme"] == "TICKER":
                for ticker in str(identifier["value"]).split("/"):
                    alias_values.add((ticker, "ticker"))
        for alias, alias_type in sorted(alias_values):
            if not alias.strip():
                continue
            connection.execute(
                """
                INSERT INTO entity_aliases(entity_id, alias, alias_type)
                VALUES (%s, %s, %s)
                ON CONFLICT (entity_id, alias, alias_type) DO NOTHING
                """,
                (entity["id"], alias, alias_type),
            )
        connection.execute(
            """
            INSERT INTO fixture_entity_notices(entity_id, dataset_key, fixture_notice, synthetic)
            VALUES (%s, %s, %s, true)
            ON CONFLICT (entity_id) DO UPDATE SET
              dataset_key = EXCLUDED.dataset_key,
              fixture_notice = EXCLUDED.fixture_notice,
              synthetic = true,
              loaded_at = now()
            """,
            (entity["id"], DATASET_KEY, entity["fixture_notice"]),
        )
        for industry_external_id, role, confidence in ENTITY_INDUSTRY_MEMBERSHIPS.get(
            str(entity["entity_key"]),
            [],
        ):
            connection.execute(
                """
                INSERT INTO entity_industry_memberships(
                  entity_id, industry_id, role, confidence, valid_from, evidence_required
                )
                SELECT %s, id, %s, %s, %s, false
                FROM industries
                WHERE external_id = %s
                ON CONFLICT (entity_id, industry_id, role, valid_from) DO UPDATE SET
                  confidence = EXCLUDED.confidence,
                  evidence_required = false
                """,
                (entity["id"], role, confidence, OBSERVED_AT, industry_external_id),
            )


def ensure_source_document(
    connection: object,
    source_id: str,
    document_id: str,
    relationship_id: str,
    evidence: dict[str, object],
) -> None:
    content_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode("utf-8")).hexdigest()
    connection.execute(
        """
        INSERT INTO source_documents(
          id, source_id, external_id, url, title, publisher, observed_at, content_hash,
          media_type, parser_version
        )
        VALUES (%s, %s, %s, %s, %s, 'EEI', %s, %s, 'application/json', 'fixture-v1')
        ON CONFLICT (id) DO UPDATE SET
          source_id = EXCLUDED.source_id,
          external_id = EXCLUDED.external_id,
          url = EXCLUDED.url,
          title = EXCLUDED.title,
          publisher = EXCLUDED.publisher,
          observed_at = EXCLUDED.observed_at,
          content_hash = EXCLUDED.content_hash,
          media_type = EXCLUDED.media_type,
          parser_version = EXCLUDED.parser_version
        """,
        (
            document_id,
            source_id,
            f"{relationship_id}:{document_id}",
            f"fixture://relationship/{relationship_id}/{document_id}",
            "Synthetic fixture evidence",
            OBSERVED_AT,
            content_hash,
        ),
    )


def load_relationships(
    connection: object,
    source_id: str,
    relationships: list[dict[str, object]],
) -> None:
    for relationship in relationships:
        qualifiers = relationship.get("qualifiers") or {}
        observed_at = relationship.get("valid_from") or OBSERVED_AT
        connection.execute(
            """
            INSERT INTO relationships(
              id, subject_entity_id, object_entity_id, relationship_type, relationship_family,
              status, confidence, valid_from, valid_to, observed_at, amount, currency,
              amount_kind, qualifiers
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
              subject_entity_id = EXCLUDED.subject_entity_id,
              object_entity_id = EXCLUDED.object_entity_id,
              relationship_type = EXCLUDED.relationship_type,
              relationship_family = EXCLUDED.relationship_family,
              status = EXCLUDED.status,
              confidence = EXCLUDED.confidence,
              valid_from = EXCLUDED.valid_from,
              valid_to = EXCLUDED.valid_to,
              observed_at = EXCLUDED.observed_at,
              amount = EXCLUDED.amount,
              currency = EXCLUDED.currency,
              amount_kind = EXCLUDED.amount_kind,
              qualifiers = EXCLUDED.qualifiers
            """,
            (
                relationship["id"],
                relationship["subject_entity_id"],
                relationship["object_entity_id"],
                relationship["relationship_type"],
                relationship["relationship_family"],
                relationship["status"],
                relationship["confidence"],
                relationship["valid_from"],
                relationship["valid_to"],
                observed_at,
                relationship["amount"],
                relationship["currency"],
                relationship["amount_kind"],
                Jsonb(qualifiers),
            ),
        )
        connection.execute(
            """
            INSERT INTO fixture_relationship_notices(
              relationship_id, dataset_key, fixture_notice, synthetic
            )
            VALUES (%s, %s, %s, true)
            ON CONFLICT (relationship_id) DO UPDATE SET
              dataset_key = EXCLUDED.dataset_key,
              fixture_notice = EXCLUDED.fixture_notice,
              synthetic = true,
              loaded_at = now()
            """,
            (relationship["id"], DATASET_KEY, relationship["fixture_notice"]),
        )
        if "stage_from" in qualifiers or "stage_to" in qualifiers:
            connection.execute(
                """
                INSERT INTO supply_chain_relationship_attributes(
                  relationship_id, stage_from, stage_to, tier, materiality
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (relationship_id) DO UPDATE SET
                  stage_from = EXCLUDED.stage_from,
                  stage_to = EXCLUDED.stage_to,
                  tier = EXCLUDED.tier,
                  materiality = EXCLUDED.materiality,
                  last_verified_at = now()
                """,
                (
                    relationship["id"],
                    qualifiers.get("stage_from"),
                    qualifiers.get("stage_to"),
                    qualifiers.get("tier"),
                    qualifiers.get("materiality"),
                ),
            )
        for evidence in relationship["evidence"]:
            document_id = evidence["source_document_id"]
            ensure_source_document(connection, source_id, document_id, relationship["id"], evidence)
            connection.execute(
                """
                INSERT INTO relationship_evidence(
                  relationship_id, source_document_id, role, locator, support_excerpt
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (relationship_id, source_document_id, role) DO UPDATE SET
                  locator = EXCLUDED.locator,
                  support_excerpt = EXCLUDED.support_excerpt
                """,
                (
                    relationship["id"],
                    document_id,
                    evidence["role"],
                    evidence["locator"],
                    evidence["support_excerpt"],
                ),
            )


def main() -> int:
    entity_path = ROOT / "data/mock_entities.json"
    relationship_path = ROOT / "data/mock_relationships.json"
    entities = read_json(entity_path)
    relationships = read_json(relationship_path)
    with connect_database() as connection:
        ensure_dataset(connection, [entity_path, relationship_path])
        source_id = ensure_fixture_source(connection)
        load_entities(connection, entities)
        load_relationships(connection, source_id, relationships)
    print("Synthetic fixtures loaded:")
    print(f"  entities: {len(entities)}")
    print(f"  relationships: {len(relationships)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
