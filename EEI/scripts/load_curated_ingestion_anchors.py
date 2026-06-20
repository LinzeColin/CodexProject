#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

from db_tools import ROOT, connect_database
from psycopg.types.json import Jsonb

ANCHOR_PATH = ROOT / "data/nvidia_public_source_anchors.csv"
PARSER_VERSION = "nvidia-public-anchor-v1"
RECORD_MODE = "curated_official_fixture"
ENTITY_RESOLUTION_MIN_CONFIDENCE = 0.72
ANCHOR_SUBJECT = "NVIDIA Corporation"

STAGE_TERMS = {
    "AI factories",
    "CoWoS",
    "Omniverse",
    "assembly",
    "chip",
    "foundry",
    "manufacturing",
    "memory",
    "packaging",
    "packaging/test",
    "systems",
    "testing",
    "wafer",
}


class AliasRule(NamedTuple):
    canonical_name: str
    research_id: str
    confidence: float


ALIAS_RULES = {
    "ASML": AliasRule("ASML Holding N.V.", "X-002", 0.94),
    "Foxconn": AliasRule("Hon Hai Precision Industry Co., Ltd. (Foxconn)", "X-006", 0.90),
    "Hon Hai/Foxconn": AliasRule(
        "Hon Hai Precision Industry Co., Ltd. (Foxconn)",
        "X-006",
        0.93,
    ),
    "Micron": AliasRule("Micron Technology, Inc.", "P1-047", 0.91),
    "NVIDIA": AliasRule("NVIDIA Corporation", "P0-006", 0.99),
    "NVIDIA Corporation": AliasRule("NVIDIA Corporation", "P0-006", 0.99),
    "Samsung": AliasRule("Samsung Electronics Co., Ltd.", "X-003", 0.90),
    "SK hynix": AliasRule("SK hynix Inc.", "X-004", 0.91),
    "TSMC": AliasRule(
        "Taiwan Semiconductor Manufacturing Company Limited (TSMC)",
        "X-001",
        0.95,
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_source_date(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def media_type(url: str) -> str:
    return "application/pdf" if url.lower().endswith(".pdf") else "text/html"


def normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().replace("/", " / ").split())


def expected_tokens(row: dict[str, str]) -> list[str]:
    tokens = [ANCHOR_SUBJECT]
    tokens.extend(
        token.strip()
        for token in row["expected_entities_or_stages"].split(";")
        if token.strip()
    )
    seen: set[str] = set()
    unique_tokens = []
    for token in tokens:
        if token not in seen:
            unique_tokens.append(token)
            seen.add(token)
    return unique_tokens


def ensure_company_official_source(connection: object) -> str:
    row = connection.execute(
        """
        INSERT INTO sources(
          code, name, base_url, source_tier, expected_cadence,
          typical_disclosure_lag, terms_notes, active
        )
        VALUES (
          'company_official',
          'Official company IR/newsroom',
          'source-specific',
          2,
          'event-driven',
          'self-reported',
          'Curated official anchors; cross-check before publishing precise facts.',
          true
        )
        ON CONFLICT (code) DO UPDATE SET
          name = EXCLUDED.name,
          source_tier = EXCLUDED.source_tier,
          expected_cadence = EXCLUDED.expected_cadence,
          typical_disclosure_lag = EXCLUDED.typical_disclosure_lag,
          terms_notes = EXCLUDED.terms_notes,
          active = true,
          last_verified_at = now()
        RETURNING id
        """
    ).fetchone()
    return str(row[0])


def start_ingestion_run(connection: object, source_id: str, source_hash: str) -> str:
    row = connection.execute(
        """
        INSERT INTO ingestion_runs(
          source_id, connector_version, mode, checkpoint, started_at, status
        )
        VALUES (%s, %s, %s, %s, now(), 'running')
        RETURNING id
        """,
        (
            source_id,
            PARSER_VERSION,
            RECORD_MODE,
            Jsonb(
                {
                    "source_path": ANCHOR_PATH.relative_to(ROOT).as_posix(),
                    "source_hash": source_hash,
                }
            ),
        ),
    ).fetchone()
    return str(row[0])


def finish_ingestion_run(connection: object, ingestion_run_id: str, counts: dict[str, int]) -> None:
    connection.execute(
        """
        UPDATE ingestion_runs
        SET finished_at = now(), status = 'succeeded', counts = %s
        WHERE id = %s
        """,
        (Jsonb(counts), ingestion_run_id),
    )


def find_entity_id(connection: object, canonical_name: str) -> str | None:
    row = connection.execute(
        """
        SELECT id
        FROM entities
        WHERE lower(canonical_name) = lower(%s)
        ORDER BY id
        LIMIT 1
        """,
        (canonical_name,),
    ).fetchone()
    return str(row[0]) if row else None


def find_research_id(connection: object, research_id: str) -> str | None:
    row = connection.execute(
        """
        SELECT research_id
        FROM company_research_universe
        WHERE research_id = %s
        """,
        (research_id,),
    ).fetchone()
    return str(row[0]) if row else None


def resolve_candidate(connection: object, candidate_name: str) -> dict[str, object]:
    if candidate_name in ALIAS_RULES:
        rule = ALIAS_RULES[candidate_name]
        method = "anchor_subject" if candidate_name == ANCHOR_SUBJECT else "alias_exact"
        return {
            "canonical_name": rule.canonical_name,
            "matched_entity_id": find_entity_id(connection, rule.canonical_name),
            "matched_research_id": find_research_id(connection, rule.research_id),
            "match_method": method,
            "confidence": rule.confidence,
            "review_status": "machine_verified",
            "decision_reason": (
                f"{candidate_name} mapped by curated official alias rule to "
                f"{rule.canonical_name}."
            ),
        }
    if candidate_name in STAGE_TERMS:
        return {
            "canonical_name": candidate_name,
            "matched_entity_id": None,
            "matched_research_id": None,
            "match_method": "stage_keyword",
            "confidence": 0.55,
            "review_status": "unreviewed",
            "decision_reason": "Source anchor names a supply-chain stage or technical keyword.",
        }
    return {
        "canonical_name": candidate_name,
        "matched_entity_id": None,
        "matched_research_id": None,
        "match_method": "official_named_context",
        "confidence": 0.62,
        "review_status": "unreviewed",
        "decision_reason": (
            "Official anchor names this party, but no canonical entity mapping is "
            "approved in the current MVP research universe."
        ),
    }


def upsert_source_document(
    connection: object,
    source_id: str,
    row: dict[str, str],
    content_hash: str,
) -> str:
    source_date = parse_source_date(row["source_date"])
    source_path = ANCHOR_PATH.relative_to(ROOT).as_posix()
    result = connection.execute(
        """
        INSERT INTO source_documents(
          source_id, external_id, url, title, publisher, document_date, observed_at,
          content_hash, media_type, raw_storage_uri, parser_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_id, external_id, content_hash) DO UPDATE SET
          url = EXCLUDED.url,
          title = EXCLUDED.title,
          publisher = EXCLUDED.publisher,
          document_date = EXCLUDED.document_date,
          observed_at = EXCLUDED.observed_at,
          media_type = EXCLUDED.media_type,
          raw_storage_uri = EXCLUDED.raw_storage_uri,
          parser_version = EXCLUDED.parser_version,
          retrieved_at = now()
        RETURNING id
        """,
        (
            source_id,
            row["anchor_id"],
            row["url"],
            row["title"],
            row["official_publisher"],
            source_date,
            source_date,
            content_hash,
            media_type(row["url"]),
            f"{source_path}#{row['anchor_id']}",
            PARSER_VERSION,
        ),
    ).fetchone()
    return str(result[0])


def upsert_raw_snapshot(
    connection: object,
    ingestion_run_id: str,
    source_document_id: str,
    row: dict[str, str],
    raw_payload: dict[str, object],
    content_hash: str,
) -> str:
    result = connection.execute(
        """
        INSERT INTO raw_source_snapshots(
          ingestion_run_id, source_document_id, anchor_id, source_url, source_date,
          publisher, title, evidence_scope, record_mode, validation_status,
          parser_version, content_hash, raw_payload, review_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'machine_verified')
        ON CONFLICT (anchor_id, content_hash) DO UPDATE SET
          ingestion_run_id = EXCLUDED.ingestion_run_id,
          source_document_id = EXCLUDED.source_document_id,
          source_url = EXCLUDED.source_url,
          source_date = EXCLUDED.source_date,
          publisher = EXCLUDED.publisher,
          title = EXCLUDED.title,
          evidence_scope = EXCLUDED.evidence_scope,
          record_mode = EXCLUDED.record_mode,
          validation_status = EXCLUDED.validation_status,
          parser_version = EXCLUDED.parser_version,
          raw_payload = EXCLUDED.raw_payload,
          review_status = EXCLUDED.review_status,
          retrieved_at = now()
        RETURNING id
        """,
        (
            ingestion_run_id,
            source_document_id,
            row["anchor_id"],
            row["url"],
            parse_source_date(row["source_date"]),
            row["official_publisher"],
            row["title"],
            row["evidence_scope"],
            RECORD_MODE,
            row["validation_status"],
            PARSER_VERSION,
            content_hash,
            Jsonb(raw_payload),
        ),
    ).fetchone()
    return str(result[0])


def upsert_resolution_candidate(
    connection: object,
    raw_snapshot_id: str,
    candidate_name: str,
) -> str:
    resolution = resolve_candidate(connection, candidate_name)
    result = connection.execute(
        """
        INSERT INTO entity_resolution_candidates(
          raw_snapshot_id, candidate_name, normalized_name, matched_entity_id,
          matched_research_id, match_method, confidence, decision_reason,
          review_status, parser_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (raw_snapshot_id, candidate_name) DO UPDATE SET
          normalized_name = EXCLUDED.normalized_name,
          matched_entity_id = EXCLUDED.matched_entity_id,
          matched_research_id = EXCLUDED.matched_research_id,
          match_method = EXCLUDED.match_method,
          confidence = EXCLUDED.confidence,
          decision_reason = EXCLUDED.decision_reason,
          review_status = EXCLUDED.review_status,
          parser_version = EXCLUDED.parser_version
        RETURNING id
        """,
        (
            raw_snapshot_id,
            candidate_name,
            normalize_name(str(resolution["canonical_name"])),
            resolution["matched_entity_id"],
            resolution["matched_research_id"],
            resolution["match_method"],
            resolution["confidence"],
            resolution["decision_reason"],
            resolution["review_status"],
            PARSER_VERSION,
        ),
    ).fetchone()
    return str(result[0])


def upsert_evidence_chain(
    connection: object,
    raw_snapshot_id: str,
    source_document_id: str,
    subject_resolution_id: str,
    row: dict[str, str],
    tokens: list[str],
) -> None:
    structured_fact = {
        "anchor_id": row["anchor_id"],
        "official_url": row["url"],
        "evidence_scope": row["evidence_scope"],
        "expected_entities_or_stages": tokens,
        "record_mode": RECORD_MODE,
        "edge_publication": "candidate_context_only_not_published_relationship",
        "minimum_entity_resolution_confidence": ENTITY_RESOLUTION_MIN_CONFIDENCE,
    }
    connection.execute(
        """
        INSERT INTO ingestion_evidence_chain(
          raw_snapshot_id, source_document_id, subject_resolution_id,
          relationship_family, evidence_role, locator, support_excerpt,
          structured_fact, counter_evidence, parser_version, confidence, review_status
        )
        VALUES (
          %s, %s, %s, 'supply_chain_operations', 'context', %s, %s, %s, %s, %s, 0.740,
          'machine_verified'
        )
        ON CONFLICT (
          raw_snapshot_id, source_document_id, evidence_role, locator, parser_version
        ) DO UPDATE SET
          subject_resolution_id = EXCLUDED.subject_resolution_id,
          relationship_family = EXCLUDED.relationship_family,
          support_excerpt = EXCLUDED.support_excerpt,
          structured_fact = EXCLUDED.structured_fact,
          counter_evidence = EXCLUDED.counter_evidence,
          confidence = EXCLUDED.confidence,
          review_status = EXCLUDED.review_status
        """,
        (
            raw_snapshot_id,
            source_document_id,
            subject_resolution_id,
            f"{ANCHOR_PATH.relative_to(ROOT).as_posix()}#{row['anchor_id']}",
            row["notes"],
            Jsonb(structured_fact),
            Jsonb([]),
            PARSER_VERSION,
        ),
    )


def load_anchors() -> dict[str, int]:
    rows = read_csv(ANCHOR_PATH)
    source_hash = file_hash(ANCHOR_PATH)
    with connect_database() as connection:
        source_id = ensure_company_official_source(connection)
        ingestion_run_id = start_ingestion_run(connection, source_id, source_hash)
        candidate_total = 0
        for row in rows:
            tokens = expected_tokens(row)
            raw_payload = {
                "source_row": row,
                "tokens": tokens,
                "parser_version": PARSER_VERSION,
                "record_mode": RECORD_MODE,
            }
            content_hash = sha256_text(canonical_json(raw_payload))
            source_document_id = upsert_source_document(connection, source_id, row, content_hash)
            raw_snapshot_id = upsert_raw_snapshot(
                connection,
                ingestion_run_id,
                source_document_id,
                row,
                raw_payload,
                content_hash,
            )
            subject_resolution_id = ""
            for token in tokens:
                candidate_id = upsert_resolution_candidate(connection, raw_snapshot_id, token)
                candidate_total += 1
                if token == ANCHOR_SUBJECT:
                    subject_resolution_id = candidate_id
            if not subject_resolution_id:
                raise RuntimeError(f"{row['anchor_id']} missing NVIDIA subject candidate")
            upsert_evidence_chain(
                connection,
                raw_snapshot_id,
                source_document_id,
                subject_resolution_id,
                row,
                tokens,
            )
        counts = {
            "anchors": len(rows),
            "entity_resolution_candidates": candidate_total,
            "evidence_chain_rows": len(rows),
        }
        finish_ingestion_run(connection, ingestion_run_id, counts)
    return counts


def main() -> int:
    counts = load_anchors()
    print(json.dumps({"loaded": True, **counts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
