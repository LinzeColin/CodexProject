#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from psycopg.types.json import Jsonb
from pypdf import PdfReader

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
LIVE_PARSER_VERSION = "nvidia-official-fulltext-live-v1"
LIVE_CAPTURE_SCHEMA_VERSION = "nvidia-official-fulltext-live-capture-v1"
LIVE_CONTRACT_ARTIFACT = (
    ROOT / "artifacts/tests/a202/t1301_live_official_retrieval_contract.json"
)
RECORD_MODE = "dry_run"
LIVE_RECORD_MODE = "live"
MIN_TEXT_CHARS = 240
LIVE_EXCERPT_CHARS = 220
DEFAULT_LIVE_TIMEOUT_SECONDS = 20.0
DEFAULT_LIVE_MAX_BYTES = 8 * 1024 * 1024
MIN_TOKEN_COVERAGE_RATIO = 1.0
RETRY_POLICY = {
    "max_attempts": 3,
    "backoff_seconds": [0, 2, 5],
    "retryable_statuses": [408, 425, 429, 500, 502, 503, 504],
    "dead_letter_after_attempts": 3,
}


@dataclass(frozen=True)
class LiveCaptureOptions:
    timeout_seconds: float = DEFAULT_LIVE_TIMEOUT_SECONDS
    max_bytes: int = DEFAULT_LIVE_MAX_BYTES
    include_excerpt: bool = True
    sleep_between_retries: bool = True


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


def normalize_live_text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def html_to_text(raw_html: str) -> str:
    without_scripts = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>",
        " ",
        raw_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return normalize_live_text(without_tags)


def response_charset(content_type: str) -> str:
    match = re.search(r"charset=([^;\s]+)", content_type, flags=re.IGNORECASE)
    return match.group(1).strip('"') if match else "utf-8"


def extract_text_from_response(*, url: str, content_type: str, body: bytes) -> str:
    if media_type(url) == "application/pdf" or "application/pdf" in content_type.lower():
        reader = PdfReader(BytesIO(body))
        return normalize_live_text("\n".join(page.extract_text() or "" for page in reader.pages))
    encoding = response_charset(content_type)
    raw_text = body.decode(encoding, errors="replace")
    if "html" in content_type.lower() or "<html" in raw_text[:500].lower():
        return html_to_text(raw_text)
    return normalize_live_text(raw_text)


def live_capture_source_health(
    row: dict[str, str],
    *,
    source_text: str,
    http_status: int,
    content_type: str,
    content_length_bytes: int,
    attempts: list[dict[str, object]],
) -> dict[str, object]:
    expected = expected_tokens(row, include_anchor_subject=True)
    missing = [token for token in expected if not token_present(source_text, token)]
    matched = [token for token in expected if token not in missing]
    coverage_ratio = len(matched) / len(expected)
    status = "healthy"
    if len(source_text) < MIN_TEXT_CHARS:
        status = "unhealthy_text_too_short"
    elif coverage_ratio < MIN_TOKEN_COVERAGE_RATIO:
        status = "unhealthy_token_coverage"
    return {
        "status": status,
        "expected_token_count": len(expected),
        "matched_token_count": len(matched),
        "missing_tokens": missing,
        "token_coverage": {
            "ratio": coverage_ratio,
            "minimum_ratio": MIN_TOKEN_COVERAGE_RATIO,
        },
        "text_char_count": len(source_text),
        "content_length_bytes": content_length_bytes,
        "http_status": http_status,
        "content_type": content_type,
        "attempts": attempts,
    }


def live_capture_excerpt(source_text: str) -> str:
    return source_text[:LIVE_EXCERPT_CHARS].strip()


def should_retry_status(status_code: int) -> bool:
    return status_code in RETRY_POLICY["retryable_statuses"]


def fetch_live_anchor(
    row: dict[str, str],
    *,
    client: httpx.Client,
    options: LiveCaptureOptions,
) -> dict[str, object]:
    attempts = []
    response: httpx.Response | None = None
    body = b""
    last_error: str | None = None
    for index in range(1, int(RETRY_POLICY["max_attempts"]) + 1):
        started = time.monotonic()
        try:
            response = client.get(row["url"], follow_redirects=True)
            raw_body = response.content
            too_large = len(raw_body) > options.max_bytes
            body = raw_body[: options.max_bytes]
            elapsed_ms = round((time.monotonic() - started) * 1000, 4)
            attempts.append(
                {
                    "attempt": index,
                    "transport": "httpx",
                    "status": "response",
                    "http_status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "retryable": should_retry_status(response.status_code),
                    "truncated_by_max_bytes": too_large,
                }
            )
            if too_large:
                last_error = f"response exceeded max_bytes={options.max_bytes}"
                break
            if response.status_code < 400:
                last_error = None
                break
            last_error = f"http_status={response.status_code}"
            if not should_retry_status(response.status_code):
                break
        except httpx.HTTPError as exc:
            elapsed_ms = round((time.monotonic() - started) * 1000, 4)
            last_error = exc.__class__.__name__
            attempts.append(
                {
                    "attempt": index,
                    "transport": "httpx",
                    "status": "error",
                    "error": last_error,
                    "elapsed_ms": elapsed_ms,
                    "retryable": True,
                }
            )
        if index < int(RETRY_POLICY["max_attempts"]) and options.sleep_between_retries:
            backoff_index = min(index - 1, len(RETRY_POLICY["backoff_seconds"]) - 1)
            time.sleep(float(RETRY_POLICY["backoff_seconds"][backoff_index]))

    content_type = response.headers.get("content-type", media_type(row["url"])) if response else ""
    http_status = response.status_code if response else 0
    source_text = ""
    if response is not None and response.status_code < 400 and not last_error:
        source_text = extract_text_from_response(
            url=row["url"],
            content_type=content_type,
            body=body,
        )
    source_health = live_capture_source_health(
        row,
        source_text=source_text,
        http_status=http_status,
        content_type=content_type or media_type(row["url"]),
        content_length_bytes=len(body),
        attempts=attempts,
    )
    if last_error and source_health["status"] == "healthy":
        source_health["status"] = "unhealthy_transport_error"
    return {
        "anchor_id": row["anchor_id"],
        "source_url": row["url"],
        "source_url_sha256": sha256_text(row["url"]),
        "document_date": row["source_date"],
        "title": row["title"],
        "official_publisher": row["official_publisher"],
        "capture_status": "success" if source_health["status"] == "healthy" else "failed",
        "last_error": last_error,
        "source_text_sha256": sha256_text(source_text) if source_text else None,
        "source_text_excerpt": live_capture_excerpt(source_text) if options.include_excerpt else "",
        "source_health": source_health,
        "relationship_publication": False,
        "release_clearance": False,
    }


def capture_live_official_sources(
    *,
    rows: list[dict[str, str]] | None = None,
    client: httpx.Client | None = None,
    options: LiveCaptureOptions | None = None,
) -> dict[str, object]:
    if options is None:
        options = LiveCaptureOptions()
    anchor_rows = rows or read_csv(ANCHOR_PATH)
    close_client = client is None
    if client is None:
        client = httpx.Client(
            timeout=options.timeout_seconds,
            headers={
                "User-Agent": (
                    "EEI/0.1 official-source-retrieval "
                    "(Enterprise Ecosystem Intelligence; contact=operator)"
                )
            },
        )
    try:
        anchors = [fetch_live_anchor(row, client=client, options=options) for row in anchor_rows]
    finally:
        if close_client:
            client.close()
    healthy_count = sum(
        1 for anchor in anchors if anchor["source_health"]["status"] == "healthy"
    )
    status = "LIVE_CAPTURE_READY_FOR_OPERATOR_REVIEW"
    if healthy_count == 0:
        status = "LIVE_CAPTURE_FAILED"
    elif healthy_count != len(anchors):
        status = "LIVE_CAPTURE_PARTIAL"
    return {
        "schema_version": LIVE_CAPTURE_SCHEMA_VERSION,
        "system_name": "EEI",
        "task_id": "T1301",
        "acceptance_ids": ["A202", "A206"],
        "status": status,
        "record_mode": LIVE_RECORD_MODE,
        "parser_version": LIVE_PARSER_VERSION,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_registry": ANCHOR_PATH.relative_to(ROOT).as_posix(),
        "source_registry_sha256": file_hash(ANCHOR_PATH),
        "capture_policy": {
            "live_retrieval": True,
            "relationship_publication": False,
            "release_clearance": False,
            "committed_full_text": False,
            "requires_operator_review": True,
        },
        "parameters": {
            "min_text_chars": MIN_TEXT_CHARS,
            "min_token_coverage_ratio": MIN_TOKEN_COVERAGE_RATIO,
            "timeout_seconds": options.timeout_seconds,
            "max_bytes": options.max_bytes,
            "retry_policy": RETRY_POLICY,
        },
        "counts": {
            "anchors_total": len(anchors),
            "anchors_healthy": healthy_count,
            "anchors_failed": len(anchors) - healthy_count,
        },
        "anchors": anchors,
        "remaining_gaps_before_a202_done": [
            "Operator must review the live capture payload and source licensing.",
            "Live capture payload must be loaded into PostgreSQL evidence tables.",
            "Production owner decision and formal release/legal clearance remain required.",
        ],
    }


def build_live_contract_artifact() -> dict[str, object]:
    return {
        "schema_version": LIVE_CAPTURE_SCHEMA_VERSION,
        "system_name": "EEI",
        "task_id": "T1301",
        "acceptance_ids": ["A202", "A206"],
        "status": "NETWORK_EVIDENCE_MISSING",
        "record_mode": LIVE_RECORD_MODE,
        "parser_version": LIVE_PARSER_VERSION,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "capture_policy": {
            "live_retrieval": False,
            "relationship_publication": False,
            "release_clearance": False,
            "committed_full_text": False,
            "requires_operator_review": True,
        },
        "implemented_scope": [
            (
                "scripts/fetch_official_source_full_text.py can capture live "
                "official-source URLs only when --capture-live and "
                "--allow-live-network are both supplied."
            ),
            (
                "Live capture extracts normalized text from HTML or PDF responses, "
                "computes content hashes, validates expected-token coverage and "
                "records retry/source-health metadata."
            ),
            (
                "Default CI generation does not access the network and does not "
                "commit official full text; it records NETWORK_EVIDENCE_MISSING "
                "until an operator live run is attached."
            ),
            (
                "Live capture does not publish relationship facts and does not "
                "imply release/legal clearance."
            ),
        ],
        "commands": {
            "generate_contract": (
                "UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python "
                "scripts/fetch_official_source_full_text.py "
                "--generate-live-contract --output "
                "artifacts/tests/a202/t1301_live_official_retrieval_contract.json"
            ),
            "operator_live_capture": (
                "UV_CACHE_DIR=/private/tmp/eei-uv-cache .venv/bin/uv run python "
                "scripts/fetch_official_source_full_text.py --capture-live "
                "--allow-live-network --output "
                "artifacts/private/t1301_live_official_capture.json"
            ),
        },
        "required_operator_evidence": [
            (
                "Successful operator live capture payload with status "
                "LIVE_CAPTURE_READY_FOR_OPERATOR_REVIEW."
            ),
            "Operator review decision for source licensing and source text retention policy.",
            (
                "PostgreSQL ingestion evidence proving live capture rows, source health "
                "and retry metadata."
            ),
        ],
        "remaining_gaps_before_a202_done": [
            "No committed live network payload is present.",
            "No production owner sign-off or release/legal clearance is attached.",
            "A206/A209 long-duration retry/dead-letter soak evidence remains incomplete.",
        ],
        "rollback": [
            "Revert the live capture adapter and generated contract artifact.",
            "Continue using the dry-run fixture connector until live evidence is ready.",
        ],
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    parser.add_argument(
        "--generate-live-contract",
        action="store_true",
        help="Write the no-network A202 live official retrieval contract artifact.",
    )
    parser.add_argument(
        "--capture-live",
        action="store_true",
        help="Capture official-source URLs over the network. Requires --allow-live-network.",
    )
    parser.add_argument(
        "--allow-live-network",
        action="store_true",
        help="Explicit operator approval for live network retrieval.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for --generate-live-contract or --capture-live.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_TIMEOUT_SECONDS,
        help="Live HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_LIVE_MAX_BYTES,
        help="Maximum response bytes retained per official source during live capture.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress JSON stdout after writing an output artifact.",
    )
    args = parser.parse_args()

    if args.generate_live_contract and args.capture_live:
        parser.error("--generate-live-contract and --capture-live are mutually exclusive")
    if args.allow_live_network and not args.capture_live:
        parser.error("--allow-live-network requires --capture-live")
    if args.max_bytes <= 0:
        parser.error("--max-bytes must be positive")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")

    if args.generate_live_contract:
        output_path = args.output or LIVE_CONTRACT_ARTIFACT
        payload = build_live_contract_artifact()
        write_json(output_path, payload)
        if not args.quiet:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.capture_live:
        if not args.allow_live_network:
            print(
                json.dumps(
                    {
                        "captured": False,
                        "status": "LIVE_NETWORK_NOT_ALLOWED",
                        "reason": "--capture-live requires --allow-live-network",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2
        output_path = args.output or ROOT / "artifacts/private/t1301_live_official_capture.json"
        payload = capture_live_official_sources(
            options=LiveCaptureOptions(
                timeout_seconds=args.timeout_seconds,
                max_bytes=args.max_bytes,
            )
        )
        write_json(output_path, payload)
        if not args.quiet:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] == "LIVE_CAPTURE_READY_FOR_OPERATOR_REVIEW" else 1

    counts = load_official_full_text_dry_run(fixture_path=args.fixture)
    print(json.dumps({"loaded": True, **counts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
