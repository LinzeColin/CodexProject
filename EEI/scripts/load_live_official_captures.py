#!/usr/bin/env python3
"""Load operator-reviewed live official-source capture artifacts into PostgreSQL."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

try:
    from db_tools import ROOT, connect_database
    from fetch_official_source_full_text import (
        LIVE_CAPTURE_SCHEMA_VERSION,
        LIVE_EXCERPT_CHARS,
        LIVE_PARSER_VERSION,
        MIN_TEXT_CHARS,
        MIN_TOKEN_COVERAGE_RATIO,
        RETRY_POLICY,
        canonical_json,
        file_hash,
        normalize_name,
        sha256_text,
    )
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
    from scripts.fetch_official_source_full_text import (
        LIVE_CAPTURE_SCHEMA_VERSION,
        LIVE_EXCERPT_CHARS,
        LIVE_PARSER_VERSION,
        MIN_TEXT_CHARS,
        MIN_TOKEN_COVERAGE_RATIO,
        RETRY_POLICY,
        canonical_json,
        file_hash,
        normalize_name,
        sha256_text,
    )
    from scripts.load_curated_ingestion_anchors import (
        ANCHOR_PATH,
        ANCHOR_SUBJECT,
        expected_tokens,
        media_type,
        parse_source_date,
        read_csv,
        resolve_candidate,
    )

DEFAULT_ARTIFACT_PATH = ROOT / "artifacts/private/t1301_live_official_capture.json"
CONTRACT_ARTIFACT_PATH = (
    ROOT / "artifacts/tests/a202/t1301_live_capture_postgres_ingestion_contract.json"
)
RECORD_MODE = "live"
SOURCE_KIND = "live_official_retrieval_hash_excerpt"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def relative_artifact_locator(path: Path) -> str:
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def load_artifact(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Live capture artifact must be a JSON object")
    return payload


def source_hash_from_artifact(path: Path, payload: dict[str, object]) -> str:
    return sha256_text(canonical_json(payload)) if not path.exists() else file_hash(path)


def anchor_rows_by_id() -> dict[str, dict[str, str]]:
    rows = read_csv(ANCHOR_PATH)
    return {row["anchor_id"]: row for row in rows}


def validate_capture_policy(payload: dict[str, object]) -> dict[str, object]:
    policy = payload.get("capture_policy")
    if not isinstance(policy, dict):
        raise ValueError("capture_policy must be present")
    expected = {
        "live_retrieval": True,
        "relationship_publication": False,
        "release_clearance": False,
        "committed_full_text": False,
        "requires_operator_review": True,
    }
    mismatches = [
        key for key, value in expected.items() if policy.get(key) is not value
    ]
    if mismatches:
        raise ValueError(f"capture_policy mismatch for {mismatches}")
    return policy


def validate_live_anchor(row: dict[str, str], anchor: dict[str, object]) -> dict[str, object]:
    anchor_id = row["anchor_id"]
    if anchor.get("anchor_id") != anchor_id:
        raise ValueError(f"{anchor_id} anchor_id mismatch")
    if anchor.get("source_url") != row["url"]:
        raise ValueError(f"{anchor_id} source_url does not match anchor registry")
    if anchor.get("source_url_sha256") != sha256_text(row["url"]):
        raise ValueError(f"{anchor_id} source_url_sha256 does not match anchor registry")
    if anchor.get("capture_status") != "success":
        raise ValueError(f"{anchor_id} capture_status must be success")
    if anchor.get("relationship_publication") is not False:
        raise ValueError(f"{anchor_id} relationship_publication must be false")
    if anchor.get("release_clearance") is not False:
        raise ValueError(f"{anchor_id} release_clearance must be false")
    if "source_text" in anchor:
        raise ValueError(f"{anchor_id} must not include committed source_text")

    source_text_sha256 = str(anchor.get("source_text_sha256") or "")
    if not SHA256_PATTERN.fullmatch(source_text_sha256):
        raise ValueError(f"{anchor_id} source_text_sha256 must be a sha256 hex digest")

    excerpt = str(anchor.get("source_text_excerpt") or "").strip()
    if not excerpt:
        raise ValueError(f"{anchor_id} source_text_excerpt is required")
    if len(excerpt) > LIVE_EXCERPT_CHARS:
        raise ValueError(f"{anchor_id} source_text_excerpt exceeds contract length")

    source_health = anchor.get("source_health")
    if not isinstance(source_health, dict):
        raise ValueError(f"{anchor_id} source_health must be an object")
    if source_health.get("status") != "healthy":
        raise ValueError(f"{anchor_id} source_health.status must be healthy")
    if int(source_health.get("text_char_count") or 0) < MIN_TEXT_CHARS:
        raise ValueError(f"{anchor_id} text_char_count is below contract minimum")
    token_coverage = source_health.get("token_coverage")
    if not isinstance(token_coverage, dict):
        raise ValueError(f"{anchor_id} token_coverage must be an object")
    if float(token_coverage.get("ratio") or 0) < MIN_TOKEN_COVERAGE_RATIO:
        raise ValueError(f"{anchor_id} token coverage below contract minimum")
    expected = expected_tokens(row, include_anchor_subject=True)
    if int(source_health.get("expected_token_count") or 0) != len(expected):
        raise ValueError(f"{anchor_id} expected_token_count does not match registry")
    if int(source_health.get("matched_token_count") or 0) != len(expected):
        raise ValueError(f"{anchor_id} matched_token_count does not match registry")
    if source_health.get("missing_tokens") not in ([], None):
        raise ValueError(f"{anchor_id} missing_tokens must be empty")
    attempts = source_health.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ValueError(f"{anchor_id} source_health.attempts must be non-empty")
    return source_health


def validate_live_capture_artifact(
    payload: dict[str, object],
    *,
    allow_fixture_capture: bool = False,
) -> dict[str, Any]:
    if payload.get("schema_version") != LIVE_CAPTURE_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {LIVE_CAPTURE_SCHEMA_VERSION}")
    if payload.get("system_name") != "EEI":
        raise ValueError("system_name must be EEI")
    if payload.get("task_id") != "T1301":
        raise ValueError("task_id must be T1301")
    if payload.get("acceptance_ids") != ["A202", "A206"]:
        raise ValueError("acceptance_ids must be ['A202', 'A206']")
    if payload.get("status") != "LIVE_CAPTURE_READY_FOR_OPERATOR_REVIEW":
        raise ValueError("status must be LIVE_CAPTURE_READY_FOR_OPERATOR_REVIEW")
    if payload.get("record_mode") != RECORD_MODE:
        raise ValueError("record_mode must be live")
    if payload.get("parser_version") != LIVE_PARSER_VERSION:
        raise ValueError(f"parser_version must be {LIVE_PARSER_VERSION}")
    if payload.get("source_registry") != ANCHOR_PATH.relative_to(ROOT).as_posix():
        raise ValueError("source_registry must match the official anchor registry")
    if payload.get("source_registry_sha256") != file_hash(ANCHOR_PATH):
        raise ValueError("source_registry_sha256 does not match current anchor registry")
    if payload.get("fixture_artifact") is True and not allow_fixture_capture:
        raise ValueError("fixture_artifact requires --allow-fixture-capture")
    validate_capture_policy(payload)

    anchors = payload.get("anchors")
    if not isinstance(anchors, list) or not anchors:
        raise ValueError("anchors must be a non-empty list")
    rows = anchor_rows_by_id()
    seen: set[str] = set()
    validation: dict[str, dict[str, object]] = {}
    for anchor in anchors:
        if not isinstance(anchor, dict):
            raise ValueError("anchors entries must be JSON objects")
        anchor_id = str(anchor.get("anchor_id") or "")
        if anchor_id in seen:
            raise ValueError(f"Duplicate live capture anchor_id: {anchor_id}")
        seen.add(anchor_id)
        row = rows.get(anchor_id)
        if row is None:
            raise ValueError(f"Unknown live capture anchor_id: {anchor_id}")
        validation[anchor_id] = validate_live_anchor(row, anchor)

    counts = payload.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("counts must be present")
    if int(counts.get("anchors_total", -1)) != len(anchors):
        raise ValueError("counts.anchors_total must match anchors length")
    if int(counts.get("anchors_healthy", -1)) != len(anchors):
        raise ValueError("counts.anchors_healthy must match healthy anchors")
    if int(counts.get("anchors_failed", -1)) != 0:
        raise ValueError("counts.anchors_failed must be zero for PostgreSQL ingestion")

    datetime.fromisoformat(str(payload["generated_at"]).replace("Z", "+00:00"))
    return {"anchors": anchors, "validation": validation}


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
          'live official retrieval hash/excerpt capture; operator review required',
          'A202 live capture ingestion contract. No full text, fact approval or legal clearance.',
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
    artifact_hash: str,
    artifact_path: Path,
    fixture_artifact: bool,
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
            LIVE_PARSER_VERSION,
            RECORD_MODE,
            Jsonb(
                {
                    "source_path": ANCHOR_PATH.relative_to(ROOT).as_posix(),
                    "source_hash": source_hash,
                    "artifact_path": relative_artifact_locator(artifact_path),
                    "artifact_hash": artifact_hash,
                    "source_kind": SOURCE_KIND,
                    "live_retrieval": True,
                    "operator_review_required": True,
                    "release_clearance": False,
                    "relationship_publication": False,
                    "committed_full_text": False,
                    "fixture_artifact": fixture_artifact,
                    "contract": "A202_live_official_capture_postgres_ingestion_v1",
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
    anchor: dict[str, object],
    artifact_path: Path,
    observed_at: datetime,
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
            f"{row['anchor_id']}:live-official-retrieval:{content_hash[:16]}",
            row["url"],
            row["title"],
            row["official_publisher"],
            parse_source_date(row["source_date"]),
            observed_at,
            content_hash,
            str(anchor.get("source_health", {}).get("content_type") or media_type(row["url"])),
            f"{relative_artifact_locator(artifact_path)}#{row['anchor_id']}",
            LIVE_PARSER_VERSION,
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
            LIVE_PARSER_VERSION,
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'machine_verified', %s)
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
            LIVE_PARSER_VERSION,
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
    anchor: dict[str, object],
    tokens: list[str],
    artifact_path: Path,
    fixture_artifact: bool,
) -> None:
    source_health = anchor["source_health"]
    structured_fact = {
        "anchor_id": row["anchor_id"],
        "official_url": row["url"],
        "evidence_scope": row["evidence_scope"],
        "expected_entities_or_stages": tokens,
        "record_mode": RECORD_MODE,
        "source_kind": SOURCE_KIND,
        "edge_publication": "live_capture_context_only_not_published_relationship",
        "live_capture_ingestion": LIVE_PARSER_VERSION,
        "source_text_sha256": anchor["source_text_sha256"],
        "source_text_excerpt_chars": len(str(anchor["source_text_excerpt"])),
        "source_health": source_health,
        "retry_policy": RETRY_POLICY,
        "live_retrieval": True,
        "operator_review_required": True,
        "source_license_review_required": True,
        "release_clearance": False,
        "relationship_publication": False,
        "committed_full_text": False,
        "fixture_artifact": fixture_artifact,
    }
    connection.execute(
        """
        INSERT INTO ingestion_evidence_chain(
          raw_snapshot_id, source_document_id, subject_resolution_id,
          relationship_family, evidence_role, locator, support_excerpt,
          structured_fact, counter_evidence, parser_version, confidence, review_status
        )
        VALUES (
          %s, %s, %s, 'supply_chain_operations', 'context', %s, %s, %s, %s, %s, 0.770,
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
            f"{relative_artifact_locator(artifact_path)}#{row['anchor_id']}",
            str(anchor["source_text_excerpt"]),
            Jsonb(structured_fact),
            Jsonb([]),
            LIVE_PARSER_VERSION,
        ),
    )


def load_live_official_captures(
    *,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    allow_fixture_capture: bool = False,
) -> dict[str, Any]:
    payload = load_artifact(artifact_path)
    validation_result = validate_live_capture_artifact(
        payload,
        allow_fixture_capture=allow_fixture_capture,
    )
    rows = anchor_rows_by_id()
    source_hash = file_hash(ANCHOR_PATH)
    artifact_hash = source_hash_from_artifact(artifact_path, payload)
    fixture_artifact = bool(payload.get("fixture_artifact") is True)
    observed_at = datetime.fromisoformat(str(payload["generated_at"]).replace("Z", "+00:00"))

    with connect_database() as connection:
        source_id = ensure_company_official_source(connection)
        ingestion_run_id = start_ingestion_run(
            connection,
            source_id=source_id,
            source_hash=source_hash,
            artifact_hash=artifact_hash,
            artifact_path=artifact_path,
            fixture_artifact=fixture_artifact,
        )
        candidate_total = 0
        for anchor in validation_result["anchors"]:
            row = rows[str(anchor["anchor_id"])]
            tokens = expected_tokens(row, include_anchor_subject=True)
            raw_payload = {
                "source_row": row,
                "source_text_sha256": anchor["source_text_sha256"],
                "source_text_excerpt": anchor["source_text_excerpt"],
                "tokens": tokens,
                "parser_version": LIVE_PARSER_VERSION,
                "record_mode": RECORD_MODE,
                "source_kind": SOURCE_KIND,
                "source_health": anchor["source_health"],
                "retry_policy": RETRY_POLICY,
                "attempts": anchor["source_health"]["attempts"],
                "live_retrieval": True,
                "operator_review_required": True,
                "source_license_review_required": True,
                "release_clearance": False,
                "relationship_publication": False,
                "committed_full_text": False,
                "fixture_artifact": fixture_artifact,
            }
            if "source_text" in raw_payload:
                raise RuntimeError("Internal error: raw_payload must not contain source_text")
            content_hash = str(anchor["source_text_sha256"])
            source_document_id = upsert_source_document(
                connection,
                source_id=source_id,
                row=row,
                content_hash=content_hash,
                anchor=anchor,
                artifact_path=artifact_path,
                observed_at=observed_at,
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
                anchor=anchor,
                tokens=tokens,
                artifact_path=artifact_path,
                fixture_artifact=fixture_artifact,
            )

        min_token_coverage = min(
            float(anchor["source_health"]["token_coverage"]["ratio"])
            for anchor in validation_result["anchors"]
        )
        counts = {
            "captures": len(validation_result["anchors"]),
            "entity_resolution_candidates": candidate_total,
            "evidence_chain_rows": len(validation_result["anchors"]),
            "source_hash": source_hash,
            "artifact_hash": artifact_hash,
            "parser_version": LIVE_PARSER_VERSION,
            "record_mode": RECORD_MODE,
            "source_kind": SOURCE_KIND,
            "source_health_status": "healthy",
            "min_token_coverage_ratio": min_token_coverage,
            "live_retrieval": True,
            "operator_review_required": True,
            "source_license_review_required": True,
            "release_clearance": False,
            "relationship_publication": False,
            "committed_full_text": False,
            "fixture_artifact": fixture_artifact,
        }
        finish_ingestion_run(connection, ingestion_run_id, counts)
    return counts


def build_contract_artifact() -> dict[str, object]:
    return {
        "schema_version": 1,
        "artifact_id": "t1301-live-capture-postgres-ingestion-contract",
        "task_id": "T1301",
        "acceptance_ids": ["A202", "A206"],
        "status": "MISSING_OPERATOR_LIVE_PAYLOAD",
        "record_mode": RECORD_MODE,
        "parser_version": LIVE_PARSER_VERSION,
        "system": {
            "zh_name": "商域图谱",
            "en_name": "Enterprise Ecosystem Intelligence",
            "subtitle": "企业商业版图与供应链递归探索系统",
        },
        "implemented_scope": [
            (
                "scripts/load_live_official_captures.py validates a live "
                "official-source retrieval artifact before database writes."
            ),
            (
                "The loader rejects committed official full text and stores only "
                "source_text_sha256, short source_text_excerpt, retry/source_health "
                "metadata and context evidence."
            ),
            (
                "PostgreSQL writes are idempotent through source_documents, "
                "raw_source_snapshots, entity_resolution_candidates and "
                "ingestion_evidence_chain upserts under record_mode=live."
            ),
            (
                "The loader never creates relationship_fact_candidates, never "
                "publishes relationships and keeps release_clearance=false."
            ),
            "Fixture artifacts require --allow-fixture-capture and cannot close A202.",
        ],
        "commands": {
            "generate_contract": (
                "UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python "
                "scripts/load_live_official_captures.py --generate-contract --output "
                "artifacts/tests/a202/t1301_live_capture_postgres_ingestion_contract.json"
            ),
            "operator_live_capture": (
                "UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python "
                "scripts/fetch_official_source_full_text.py --capture-live "
                "--allow-live-network --output artifacts/private/t1301_live_official_capture.json"
            ),
            "operator_postgres_ingestion": (
                "UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python "
                "scripts/load_live_official_captures.py --artifact "
                "artifacts/private/t1301_live_official_capture.json"
            ),
        },
        "database_contract": {
            "source_documents": (
                "external_id suffix live-official-retrieval and "
                "content_hash=source_text_sha256"
            ),
            "raw_source_snapshots": (
                "record_mode=live, review_status=machine_verified, no raw source_text"
            ),
            "entity_resolution_candidates": (
                "parser_version=nvidia-official-fulltext-live-v1, "
                "review_status=machine_verified"
            ),
            "ingestion_evidence_chain": (
                "evidence_role=context, edge_publication="
                "live_capture_context_only_not_published_relationship"
            ),
            "relationship_fact_candidates": "must remain zero for this parser",
        },
        "remaining_gaps_before_a202_done": [
            "No operator-approved live network payload is committed.",
            (
                "No formal source-license review, production owner sign-off or "
                "legal/release clearance is attached."
            ),
            "A206/A209 long-duration retry/dead-letter soak evidence remains incomplete.",
        ],
        "rollback": [
            (
                "Remove scripts/load_live_official_captures.py, the fixture, "
                "tests and contract artifact."
            ),
            (
                "Delete live parser rows by parser_version before deployment, "
                "or run a schema/data snapshot restore if already deployed."
            ),
            (
                "Continue using dry-run and operator-source capture contracts "
                "until live evidence is ready."
            ),
        ],
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact",
        type=Path,
        default=DEFAULT_ARTIFACT_PATH,
        help="Live capture JSON artifact path.",
    )
    parser.add_argument(
        "--allow-fixture-capture",
        action="store_true",
        help="Allow a committed fixture_artifact for CI/integration validation only.",
    )
    parser.add_argument(
        "--generate-contract",
        action="store_true",
        help="Write the no-network A202 PostgreSQL ingestion contract artifact.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=CONTRACT_ARTIFACT_PATH,
        help="Output path for --generate-contract.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress JSON stdout.")
    args = parser.parse_args()

    if args.generate_contract:
        payload = build_contract_artifact()
        write_json(args.output, payload)
        if not args.quiet:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    counts = load_live_official_captures(
        artifact_path=args.artifact,
        allow_fixture_capture=args.allow_fixture_capture,
    )
    result = {"loaded": True, **counts}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
