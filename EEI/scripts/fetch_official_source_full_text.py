#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

try:
    from db_tools import ROOT, connect_database
    from load_curated_ingestion_anchors import (
        ANCHOR_PATH,
        ANCHOR_SUBJECT,
        expected_tokens,
        media_type,
        parse_source_date,
        read_csv,
        resolve_candidate,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts package.
    from scripts.db_tools import ROOT, connect_database
    from scripts.load_curated_ingestion_anchors import (
        ANCHOR_PATH,
        ANCHOR_SUBJECT,
        expected_tokens,
        media_type,
        parse_source_date,
        read_csv,
        resolve_candidate,
    )

FIXTURE_PATH = (
    ROOT
    / "tests/fixtures/official_source_full_text/nvidia_official_full_text_dry_run.json"
)
PARSER_VERSION = "nvidia-official-fulltext-dry-run-v1"
RECORD_MODE = "dry_run"
MIN_TEXT_CHARS = 240
MIN_TOKEN_COVERAGE_RATIO = 1.0
RETRY_POLICY = {
    "max_attempts": 3,
    "backoff_seconds": [0, 2, 5],
    "retryable_statuses": [408, 425, 429, 500, 502, 503, 504],
    "dead_letter_after_attempts": 3,
}


def canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def token_words(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


def token_present(source_text: str, token: str) -> bool:
    normalized_text = f" {token_words(source_text)} "
    normalized_token = token_words(token)
    return bool(normalized_token) and f" {normalized_token} " in normalized_text


def load_fixture(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "nvidia-official-fulltext-dry-run-fixture-v1":
        raise ValueError(
            "Fixture schema_version must be nvidia-official-fulltext-dry-run-fixture-v1"
        )
    anchors = payload.get("anchors")
    if not isinstance(anchors, list):
        raise ValueError("Fixture anchors must be a list")
    by_anchor: dict[str, dict[str, object]] = {}
    for anchor in anchors:
        if not isinstance(anchor, dict):
            raise ValueError("Fixture anchor entries must be objects")
        anchor_id = str(anchor.get("anchor_id") or "")
        if not anchor_id:
            raise ValueError("Fixture anchor_id is required")
        if anchor_id in by_anchor:
            raise ValueError(f"Duplicate fixture anchor_id: {anchor_id}")
        by_anchor[anchor_id] = anchor
    return by_anchor


def validate_fixture_anchor(
    row: dict[str, str],
    fixture_anchor: dict[str, object],
) -> dict[str, object]:
    source_text = str(fixture_anchor.get("source_text") or "").strip()
    if len(source_text) < MIN_TEXT_CHARS:
        raise ValueError(f"{row['anchor_id']} fixture source_text is too short")
    if fixture_anchor.get("source_url") != row["url"]:
        raise ValueError(f"{row['anchor_id']} fixture source_url does not match anchor CSV")
    if fixture_anchor.get("capture_status") != "success":
        raise ValueError(f"{row['anchor_id']} fixture capture_status must be success")
    expected = expected_tokens(row, include_anchor_subject=True)
    missing = [token for token in expected if not token_present(source_text, token)]
    matched = [token for token in expected if token not in missing]
    coverage_ratio = len(matched) / len(expected)
    if coverage_ratio < MIN_TOKEN_COVERAGE_RATIO:
        raise ValueError(
            f"{row['anchor_id']} token coverage {coverage_ratio:.3f} below "
            f"{MIN_TOKEN_COVERAGE_RATIO:.3f}: missing {missing}"
        )
    return {
        "status": "healthy",
        "expected_token_count": len(expected),
        "matched_token_count": len(matched),
        "missing_tokens": missing,
        "token_coverage": {
            "ratio": coverage_ratio,
            "minimum_ratio": MIN_TOKEN_COVERAGE_RATIO,
        },
        "text_char_count": len(source_text),
        "http_status": int(fixture_anchor.get("http_status") or 0),
        "content_type": str(fixture_anchor.get("content_type") or media_type(row["url"])),
        "captured_at": str(fixture_anchor.get("captured_at") or ""),
    }


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
          'dry-run full-text fixture; live official retrieval required before release',
          'A202 dry-run full-text connector. Fixture text is not production clearance.',
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


def start_ingestion_run(
    connection: object,
    *,
    source_id: str,
    source_hash: str,
    fixture_hash: str,
) -> str:
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
                    "fixture_path": FIXTURE_PATH.relative_to(ROOT).as_posix(),
                    "fixture_hash": fixture_hash,
                    "retry_policy": RETRY_POLICY,
                    "live_retrieval": False,
                }
            ),
        ),
    ).fetchone()
    return str(row[0])


def finish_ingestion_run(connection: object, ingestion_run_id: str, counts: dict[str, Any]) -> None:
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


def resolve_for_database(connection: object, candidate_name: str) -> dict[str, object]:
    resolution = resolve_candidate(connection, candidate_name)
    matched_research_id = resolution["matched_research_id"]
    matched_entity_id = resolution["matched_entity_id"]
    if matched_research_id is None and candidate_name == ANCHOR_SUBJECT:
        matched_research_id = find_research_id(connection, "P0-006")
    canonical_name = str(resolution["canonical_name"])
    if matched_entity_id is None and canonical_name:
        matched_entity_id = find_entity_id(connection, canonical_name)
    return {
        **resolution,
        "matched_research_id": matched_research_id,
        "matched_entity_id": matched_entity_id,
    }


def normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().replace("/", " / ").split())


def upsert_source_document(
    connection: object,
    *,
    source_id: str,
    row: dict[str, str],
    content_hash: str,
    fixture_anchor: dict[str, object],
) -> str:
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
            f"{row['anchor_id']}:full-text-dry-run",
            row["url"],
            row["title"],
            row["official_publisher"],
            parse_source_date(row["source_date"]),
            datetime.fromisoformat(str(fixture_anchor["captured_at"]).replace("Z", "+00:00")),
            content_hash,
            str(fixture_anchor.get("content_type") or media_type(row["url"])),
            f"{FIXTURE_PATH.relative_to(ROOT).as_posix()}#{row['anchor_id']}",
            PARSER_VERSION,
        ),
    ).fetchone()
    return str(result[0])


def upsert_raw_snapshot(
    connection: object,
    *,
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
    *,
    raw_snapshot_id: str,
    candidate_name: str,
) -> str:
    resolution = resolve_for_database(connection, candidate_name)
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
    *,
    raw_snapshot_id: str,
    source_document_id: str,
    subject_resolution_id: str,
    row: dict[str, str],
    tokens: list[str],
    source_health: dict[str, object],
    support_excerpt: str,
) -> None:
    structured_fact = {
        "anchor_id": row["anchor_id"],
        "official_url": row["url"],
        "evidence_scope": row["evidence_scope"],
        "expected_entities_or_stages": tokens,
        "record_mode": RECORD_MODE,
        "edge_publication": "dry_run_context_only_not_published_relationship",
        "full_text_connector": PARSER_VERSION,
        "source_health": source_health,
        "retry_policy": RETRY_POLICY,
    }
    connection.execute(
        """
        INSERT INTO ingestion_evidence_chain(
          raw_snapshot_id, source_document_id, subject_resolution_id,
          relationship_family, evidence_role, locator, support_excerpt,
          structured_fact, counter_evidence, parser_version, confidence, review_status
        )
        VALUES (
          %s, %s, %s, 'supply_chain_operations', 'context', %s, %s, %s, %s, %s, 0.760,
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
            f"{FIXTURE_PATH.relative_to(ROOT).as_posix()}#{row['anchor_id']}",
            support_excerpt,
            Jsonb(structured_fact),
            Jsonb([]),
            PARSER_VERSION,
        ),
    )


def load_official_full_text_dry_run(*, fixture_path: Path = FIXTURE_PATH) -> dict[str, Any]:
    rows = read_csv(ANCHOR_PATH)
    fixtures = load_fixture(fixture_path)
    source_hash = file_hash(ANCHOR_PATH)
    fixture_hash = file_hash(fixture_path)
    validation: dict[str, dict[str, object]] = {}
    for row in rows:
        fixture_anchor = fixtures.get(row["anchor_id"])
        if fixture_anchor is None:
            raise ValueError(f"Missing fixture anchor for {row['anchor_id']}")
        validation[row["anchor_id"]] = validate_fixture_anchor(row, fixture_anchor)

    with connect_database() as connection:
        source_id = ensure_company_official_source(connection)
        ingestion_run_id = start_ingestion_run(
            connection,
            source_id=source_id,
            source_hash=source_hash,
            fixture_hash=fixture_hash,
        )
        candidate_total = 0
        for row in rows:
            fixture_anchor = fixtures[row["anchor_id"]]
            tokens = expected_tokens(row, include_anchor_subject=True)
            source_text = str(fixture_anchor["source_text"]).strip()
            source_health = validation[row["anchor_id"]]
            raw_payload = {
                "source_row": row,
                "source_text": source_text,
                "tokens": tokens,
                "parser_version": PARSER_VERSION,
                "record_mode": RECORD_MODE,
                "source_kind": "official_full_text_dry_run",
                "source_health": source_health,
                "retry_policy": RETRY_POLICY,
                "attempts": [
                    {
                        "attempt": 1,
                        "transport": "fixture_file",
                        "status": "success",
                        "retryable": False,
                        "http_status": source_health["http_status"],
                    }
                ],
                "live_retrieval": False,
                "release_clearance": False,
            }
            content_hash = sha256_text(canonical_json(raw_payload))
            source_document_id = upsert_source_document(
                connection,
                source_id=source_id,
                row=row,
                content_hash=content_hash,
                fixture_anchor=fixture_anchor,
            )
            raw_snapshot_id = upsert_raw_snapshot(
                connection,
                ingestion_run_id=ingestion_run_id,
                source_document_id=source_document_id,
                row=row,
                raw_payload=raw_payload,
                content_hash=content_hash,
            )
            subject_resolution_id = ""
            for token in tokens:
                candidate_id = upsert_resolution_candidate(
                    connection,
                    raw_snapshot_id=raw_snapshot_id,
                    candidate_name=token,
                )
                if token == ANCHOR_SUBJECT:
                    subject_resolution_id = candidate_id
                candidate_total += 1
            if not subject_resolution_id:
                raise RuntimeError(f"Missing NVIDIA subject resolution for {row['anchor_id']}")
            upsert_evidence_chain(
                connection,
                raw_snapshot_id=raw_snapshot_id,
                source_document_id=source_document_id,
                subject_resolution_id=subject_resolution_id,
                row=row,
                tokens=tokens,
                source_health=source_health,
                support_excerpt=source_text[:480],
            )

        counts = {
            "anchors": len(rows),
            "entity_resolution_candidates": candidate_total,
            "evidence_chain_rows": len(rows),
            "source_hash": source_hash,
            "fixture_hash": fixture_hash,
            "parser_version": PARSER_VERSION,
            "record_mode": RECORD_MODE,
            "source_health_status": "healthy",
            "min_token_coverage_ratio": min(
                float(row["token_coverage"]["ratio"]) for row in validation.values()
            ),
            "retry_policy": RETRY_POLICY,
            "live_retrieval": False,
            "release_clearance": False,
        }
        finish_ingestion_run(connection, ingestion_run_id, counts)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIXTURE_PATH,
        help="Dry-run fixture JSON path. Defaults to the committed official-source fixture.",
    )
    args = parser.parse_args()
    counts = load_official_full_text_dry_run(fixture_path=args.fixture)
    print(json.dumps({"loaded": True, **counts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
