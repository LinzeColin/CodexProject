#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

try:
    from db_tools import ROOT, connect_database
    from fetch_official_source_full_text import (
        canonical_json,
        file_hash,
        normalize_name,
        sha256_text,
        token_present,
    )
    from load_curated_ingestion_anchors import (
        ANCHOR_PATH,
        ANCHOR_SUBJECT,
        anchor_scope_metadata,
        expected_tokens,
        media_type,
        parse_source_date,
        read_csv,
        resolve_candidate,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts package.
    from scripts.db_tools import ROOT, connect_database
    from scripts.fetch_official_source_full_text import (
        canonical_json,
        file_hash,
        normalize_name,
        sha256_text,
        token_present,
    )
    from scripts.load_curated_ingestion_anchors import (
        ANCHOR_PATH,
        ANCHOR_SUBJECT,
        anchor_scope_metadata,
        expected_tokens,
        media_type,
        parse_source_date,
        read_csv,
        resolve_candidate,
    )

FIXTURE_PATH = (
    ROOT / "tests/fixtures/operator_source_captures/nvidia_operator_source_captures.json"
)
PARSER_VERSION = "nvidia-operator-source-capture-v1"
RECORD_MODE = "operator_source_capture"
MIN_TEXT_CHARS = 240
MIN_TOKEN_COVERAGE_RATIO = 1.0
REQUIRED_USAGE_ATTESTATIONS = {
    "official_source_observed",
    "source_url_matches_anchor",
    "no_paywall_or_login_bypass",
    "copyright_excerpt_only_for_evidence",
    "not_production_fact_approval",
}


def load_fixture(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "nvidia-operator-source-capture-fixture-v1":
        raise ValueError(
            "Fixture schema_version must be nvidia-operator-source-capture-fixture-v1"
        )
    captures = payload.get("captures")
    if not isinstance(captures, list):
        raise ValueError("Fixture captures must be a list")
    by_anchor: dict[str, dict[str, object]] = {}
    for capture in captures:
        if not isinstance(capture, dict):
            raise ValueError("Fixture capture entries must be objects")
        anchor_id = str(capture.get("anchor_id") or "")
        capture_id = str(capture.get("capture_id") or "")
        if not anchor_id or not capture_id:
            raise ValueError("Fixture anchor_id and capture_id are required")
        if anchor_id in by_anchor:
            raise ValueError(f"Duplicate fixture anchor_id: {anchor_id}")
        by_anchor[anchor_id] = capture
    return by_anchor


def validate_usage_attestation(capture: dict[str, object]) -> dict[str, bool]:
    usage = capture.get("usage_attestation")
    if not isinstance(usage, dict):
        raise ValueError(f"{capture['anchor_id']} usage_attestation must be an object")
    missing = [
        key
        for key in sorted(REQUIRED_USAGE_ATTESTATIONS)
        if usage.get(key) is not True
    ]
    if missing:
        raise ValueError(f"{capture['anchor_id']} usage attestation missing {missing}")
    return {key: True for key in sorted(REQUIRED_USAGE_ATTESTATIONS)}


def validate_capture(
    row: dict[str, str],
    capture: dict[str, object],
) -> dict[str, object]:
    source_text = str(capture.get("source_text") or "").strip()
    if len(source_text) < MIN_TEXT_CHARS:
        raise ValueError(f"{row['anchor_id']} operator source_text is too short")
    if capture.get("source_url") != row["url"]:
        raise ValueError(f"{row['anchor_id']} source_url does not match anchor CSV")
    if capture.get("capture_status") != "operator_verified":
        raise ValueError(f"{row['anchor_id']} capture_status must be operator_verified")
    for required_field in [
        "captured_by",
        "captured_at",
        "capture_method",
        "approval_scope",
        "operator_signature",
        "source_text_sha256",
    ]:
        if not str(capture.get(required_field) or "").strip():
            raise ValueError(f"{row['anchor_id']} missing {required_field}")
    if capture.get("approval_scope") != "A202_official_source_capture_contract_only":
        raise ValueError(f"{row['anchor_id']} approval_scope is outside A202 contract")
    observed_hash = sha256_text(source_text)
    if capture.get("source_text_sha256") != observed_hash:
        raise ValueError(f"{row['anchor_id']} source_text_sha256 does not match text")
    datetime.fromisoformat(str(capture["captured_at"]).replace("Z", "+00:00"))
    usage_attestation = validate_usage_attestation(capture)
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
        "status": "operator_verified",
        "expected_token_count": len(expected),
        "matched_token_count": len(matched),
        "missing_tokens": missing,
        "token_coverage": {
            "ratio": coverage_ratio,
            "minimum_ratio": MIN_TOKEN_COVERAGE_RATIO,
        },
        "text_char_count": len(source_text),
        "content_type": str(capture.get("content_type") or media_type(row["url"])),
        "captured_at": str(capture["captured_at"]),
        "captured_by": str(capture["captured_by"]),
        "capture_method": str(capture["capture_method"]),
        "source_text_sha256": observed_hash,
        "usage_attestation": usage_attestation,
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
          'operator-provided official source capture; live retrieval still preferred',
          'A202 operator capture contract. Capture is not fact approval or legal clearance.',
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
                    "operator_supplied_capture": True,
                    "live_retrieval": False,
                    "release_clearance": False,
                    "contract": "A202_operator_official_source_capture_v1",
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


def upsert_source_document(
    connection: object,
    *,
    source_id: str,
    row: dict[str, str],
    content_hash: str,
    capture: dict[str, object],
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
            f"{row['anchor_id']}:operator-source-capture:{capture['capture_id']}",
            row["url"],
            row["title"],
            row["official_publisher"],
            parse_source_date(row["source_date"]),
            datetime.fromisoformat(str(capture["captured_at"]).replace("Z", "+00:00")),
            content_hash,
            str(capture.get("content_type") or media_type(row["url"])),
            f"{FIXTURE_PATH.relative_to(ROOT).as_posix()}#{capture['capture_id']}",
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'operator_verified')
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
            "operator_verified",
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
    capture: dict[str, object],
    tokens: list[str],
    source_health: dict[str, object],
    support_excerpt: str,
) -> None:
    structured_fact = {
        "anchor_id": row["anchor_id"],
        "capture_id": capture["capture_id"],
        "official_url": row["url"],
        "evidence_scope": row["evidence_scope"],
        "expected_entities_or_stages": tokens,
        "anchor_scope": anchor_scope_metadata(row),
        "record_mode": RECORD_MODE,
        "edge_publication": "operator_capture_context_only_not_published_relationship",
        "operator_source_capture": PARSER_VERSION,
        "source_health": source_health,
        "operator_provenance": {
            "captured_by": capture["captured_by"],
            "captured_at": capture["captured_at"],
            "capture_method": capture["capture_method"],
            "operator_signature_hash": sha256_text(str(capture["operator_signature"])),
        },
        "release_clearance": False,
    }
    connection.execute(
        """
        INSERT INTO ingestion_evidence_chain(
          raw_snapshot_id, source_document_id, subject_resolution_id,
          relationship_family, evidence_role, locator, support_excerpt,
          structured_fact, counter_evidence, parser_version, confidence, review_status
        )
        VALUES (
          %s, %s, %s, 'supply_chain_operations', 'context', %s, %s, %s, %s, %s, 0.780,
          'operator_verified'
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
            f"{FIXTURE_PATH.relative_to(ROOT).as_posix()}#{capture['capture_id']}",
            support_excerpt,
            Jsonb(structured_fact),
            Jsonb([]),
            PARSER_VERSION,
        ),
    )


def load_operator_source_captures(*, fixture_path: Path = FIXTURE_PATH) -> dict[str, Any]:
    rows = read_csv(ANCHOR_PATH)
    captures = load_fixture(fixture_path)
    source_hash = file_hash(ANCHOR_PATH)
    fixture_hash = file_hash(fixture_path)
    selected_rows = [row for row in rows if row["anchor_id"] in captures]
    if not selected_rows:
        raise ValueError("No operator captures matched the official anchor CSV")

    validation: dict[str, dict[str, object]] = {}
    for row in selected_rows:
        validation[row["anchor_id"]] = validate_capture(row, captures[row["anchor_id"]])

    with connect_database() as connection:
        source_id = ensure_company_official_source(connection)
        ingestion_run_id = start_ingestion_run(
            connection,
            source_id=source_id,
            source_hash=source_hash,
            fixture_hash=fixture_hash,
        )
        candidate_total = 0
        for row in selected_rows:
            capture = captures[row["anchor_id"]]
            tokens = expected_tokens(row, include_anchor_subject=True)
            source_text = str(capture["source_text"]).strip()
            source_health = validation[row["anchor_id"]]
            raw_payload = {
                "source_row": row,
                "source_text": source_text,
                "source_text_sha256": source_health["source_text_sha256"],
                "tokens": tokens,
                "anchor_scope": anchor_scope_metadata(row),
                "parser_version": PARSER_VERSION,
                "record_mode": RECORD_MODE,
                "source_kind": "operator_provided_official_source_capture",
                "source_health": source_health,
                "operator_capture": {
                    "capture_id": capture["capture_id"],
                    "captured_by": capture["captured_by"],
                    "captured_at": capture["captured_at"],
                    "capture_method": capture["capture_method"],
                    "approval_scope": capture["approval_scope"],
                    "operator_signature_hash": sha256_text(
                        str(capture["operator_signature"])
                    ),
                },
                "operator_supplied_capture": True,
                "live_retrieval": False,
                "release_clearance": False,
                "relationship_publication": False,
            }
            content_hash = sha256_text(canonical_json(raw_payload))
            source_document_id = upsert_source_document(
                connection,
                source_id=source_id,
                row=row,
                content_hash=content_hash,
                capture=capture,
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
                capture=capture,
                tokens=tokens,
                source_health=source_health,
                support_excerpt=source_text[:480],
            )

        counts = {
            "captures": len(selected_rows),
            "entity_resolution_candidates": candidate_total,
            "evidence_chain_rows": len(selected_rows),
            "source_hash": source_hash,
            "fixture_hash": fixture_hash,
            "parser_version": PARSER_VERSION,
            "record_mode": RECORD_MODE,
            "source_health_status": "operator_verified",
            "min_token_coverage_ratio": min(
                float(row["token_coverage"]["ratio"]) for row in validation.values()
            ),
            "operator_supplied_capture": True,
            "live_retrieval": False,
            "release_clearance": False,
            "relationship_publication": False,
        }
        finish_ingestion_run(connection, ingestion_run_id, counts)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIXTURE_PATH,
        help="Operator capture fixture JSON path.",
    )
    args = parser.parse_args()
    counts = load_operator_source_captures(fixture_path=args.fixture)
    print(json.dumps({"loaded": True, **counts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
