from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Any, Literal

from psycopg.types.json import Jsonb

from .sec_normalizer import (
    SEC_COMPANY_FACTS_NORMALIZER_VERSION,
    SEC_SUBMISSIONS_NORMALIZER_VERSION,
    NormalizedSecCompanyFacts,
    NormalizedSecSubmissions,
    normalize_sec_company_facts,
    normalize_sec_submissions,
)

ExecutionMode = Literal["fixture", "dry_run"]

SEC_FIXTURE_CONNECTOR_VERSION = "sec-fixture-ingestion-v1"
SEC_FIXTURE_SOURCE_CODE = "sec_edgar_synthetic_fixture"
SEC_FIXTURE_REPORT_VERSION = "eei-sec-fixture-ingestion-report-v1"
SEC_FIXTURE_PUBLISHER = "SEC EDGAR synthetic golden fixture"
SEC_FIXTURE_EVIDENCE_SCOPE = "normalization_fixture_only_not_publishable"
SUPPORTED_EXECUTION_MODES = frozenset({"fixture", "dry_run"})


@dataclass(frozen=True)
class SecFixtureDocument:
    kind: Literal["submissions", "companyfacts"]
    cik: str
    entity_name: str
    anchor_id: str
    source_url: str
    title: str
    source_date: datetime
    parser_version: str
    content_hash: str
    raw_payload: Mapping[str, Any]
    normalized_record_count: int
    fixture_path: str


@dataclass(frozen=True)
class SecFixturePlan:
    cik: str
    entity_name: str
    submissions: NormalizedSecSubmissions
    companyfacts: NormalizedSecCompanyFacts
    documents: tuple[SecFixtureDocument, ...]

    @property
    def fixture_hashes(self) -> dict[str, str]:
        return {document.kind: document.content_hash for document in self.documents}


def utc_now() -> datetime:
    return datetime.now(UTC)


def isoformat(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def payload_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def as_utc_datetime(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def validate_execution_mode(value: str) -> ExecutionMode:
    if value not in SUPPORTED_EXECUTION_MODES:
        raise ValueError(f"execution_mode must be one of {sorted(SUPPORTED_EXECUTION_MODES)}")
    return value  # type: ignore[return-value]


def require_fixture_metadata(payload: Mapping[str, Any], *, path: str) -> None:
    metadata = payload.get("_fixture_metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError(f"{path} must include _fixture_metadata")
    if metadata.get("record_mode") != "fixture" or metadata.get("synthetic") is not True:
        raise ValueError(f"{path} must be an explicitly synthetic fixture")


def build_sec_fixture_plan(
    submissions_payload: Mapping[str, Any],
    companyfacts_payload: Mapping[str, Any],
    *,
    submissions_fixture_path: str = "tests/fixtures/sec/submissions_golden.json",
    companyfacts_fixture_path: str = "tests/fixtures/sec/companyfacts_golden.json",
) -> SecFixturePlan:
    require_fixture_metadata(submissions_payload, path="submissions")
    require_fixture_metadata(companyfacts_payload, path="companyfacts")
    submissions = normalize_sec_submissions(submissions_payload, record_mode="fixture")
    companyfacts = normalize_sec_company_facts(companyfacts_payload, record_mode="fixture")
    if submissions.cik != companyfacts.cik:
        raise ValueError("SEC fixture CIK mismatch")
    if submissions.entity_name != companyfacts.entity_name:
        raise ValueError("SEC fixture entity name mismatch")
    if not submissions.filings:
        raise ValueError("SEC submissions fixture must contain at least one filing")
    if not companyfacts.facts:
        raise ValueError("SEC Company Facts fixture must contain at least one fact")

    cik_token = f"CIK{submissions.cik}"
    submissions_date = max(item.filed_date for item in submissions.filings)
    companyfacts_date = max(item.filed_date for item in companyfacts.facts)
    documents = (
        SecFixtureDocument(
            kind="submissions",
            cik=submissions.cik,
            entity_name=submissions.entity_name,
            anchor_id=f"sec-submissions-{cik_token}",
            source_url=f"fixture://sec/submissions/{cik_token}.json",
            title=f"{submissions.entity_name} synthetic SEC Submissions fixture",
            source_date=as_utc_datetime(submissions_date),
            parser_version=SEC_SUBMISSIONS_NORMALIZER_VERSION,
            content_hash=payload_sha256(submissions_payload),
            raw_payload=submissions_payload,
            normalized_record_count=len(submissions.filings),
            fixture_path=submissions_fixture_path,
        ),
        SecFixtureDocument(
            kind="companyfacts",
            cik=companyfacts.cik,
            entity_name=companyfacts.entity_name,
            anchor_id=f"sec-companyfacts-{cik_token}",
            source_url=f"fixture://sec/companyfacts/{cik_token}.json",
            title=f"{companyfacts.entity_name} synthetic SEC Company Facts fixture",
            source_date=as_utc_datetime(companyfacts_date),
            parser_version=SEC_COMPANY_FACTS_NORMALIZER_VERSION,
            content_hash=payload_sha256(companyfacts_payload),
            raw_payload=companyfacts_payload,
            normalized_record_count=len(companyfacts.facts),
            fixture_path=companyfacts_fixture_path,
        ),
    )
    return SecFixturePlan(
        cik=submissions.cik,
        entity_name=submissions.entity_name,
        submissions=submissions,
        companyfacts=companyfacts,
        documents=documents,
    )


def empty_counts() -> dict[str, int]:
    return {
        "normalized_filings": 0,
        "normalized_facts": 0,
        "source_documents_planned": 0,
        "raw_snapshots_planned": 0,
        "source_documents_inserted": 0,
        "source_documents_reused": 0,
        "raw_snapshots_inserted": 0,
        "raw_snapshots_reused": 0,
    }


def planned_counts(plan: SecFixturePlan) -> dict[str, int]:
    counts = empty_counts()
    counts.update(
        {
            "normalized_filings": len(plan.submissions.filings),
            "normalized_facts": len(plan.companyfacts.facts),
            "source_documents_planned": len(plan.documents),
            "raw_snapshots_planned": len(plan.documents),
        }
    )
    return counts


def checkpoint(plan: SecFixturePlan, *, stage: str) -> dict[str, Any]:
    return {
        "stage": stage,
        "cik": plan.cik,
        "entity_name": plan.entity_name,
        "fixture_hashes": plan.fixture_hashes,
        "connector_version": SEC_FIXTURE_CONNECTOR_VERSION,
    }


def report_base(
    *,
    execution_mode: ExecutionMode,
    started_at: datetime,
    finished_at: datetime,
) -> dict[str, Any]:
    return {
        "schema_version": SEC_FIXTURE_REPORT_VERSION,
        "task_id": "T703",
        "acceptance_ids": ["A102", "A103"],
        "execution_mode": execution_mode,
        "record_mode": "fixture",
        "started_at": isoformat(started_at),
        "finished_at": isoformat(finished_at),
    }


def failure_report(
    *,
    execution_mode: str,
    error: Exception,
    started_at: datetime,
    finished_at: datetime | None = None,
) -> dict[str, Any]:
    mode: ExecutionMode = (
        execution_mode if execution_mode in SUPPORTED_EXECUTION_MODES else "dry_run"
    )  # type: ignore[assignment]
    completed_at = finished_at or utc_now()
    return {
        **report_base(
            execution_mode=mode,
            started_at=started_at,
            finished_at=completed_at,
        ),
        "status": "failed",
        "checkpoint": {"stage": "failed"},
        "counts": empty_counts(),
        "error_class": type(error).__name__,
        "error_message": str(error),
        "database_write_performed": False,
        "release_scope": {
            "fixture_only": True,
            "live_sec_request_performed": False,
            "a202_closed_by_report": False,
            "a209_closed_by_report": False,
            "mvp_release_ready": False,
        },
    }


def ensure_fixture_source(connection: Any) -> str:
    row = connection.execute(
        """
        INSERT INTO sources(
          code, name, base_url, source_tier, expected_cadence,
          typical_disclosure_lag, terms_notes, active
        )
        VALUES (%s, %s, %s, 5, 'fixture-only', 'not-applicable', %s, true)
        ON CONFLICT (code) DO UPDATE SET
          name = EXCLUDED.name,
          base_url = EXCLUDED.base_url,
          source_tier = EXCLUDED.source_tier,
          expected_cadence = EXCLUDED.expected_cadence,
          typical_disclosure_lag = EXCLUDED.typical_disclosure_lag,
          terms_notes = EXCLUDED.terms_notes,
          active = true
        RETURNING id
        """,
        (
            SEC_FIXTURE_SOURCE_CODE,
            "SEC EDGAR synthetic fixtures",
            "fixture://sec",
            "Synthetic normalization fixtures; never publish as live evidence.",
        ),
    ).fetchone()
    return str(row[0])


def start_ingestion_run(
    connection: Any,
    *,
    source_id: str,
    plan: SecFixturePlan,
    started_at: datetime,
) -> str:
    row = connection.execute(
        """
        INSERT INTO ingestion_runs(
          source_id, connector_version, mode, checkpoint, started_at, status, counts
        )
        VALUES (%s, %s, 'fixture', %s, %s, 'running', %s)
        RETURNING id
        """,
        (
            source_id,
            SEC_FIXTURE_CONNECTOR_VERSION,
            Jsonb(checkpoint(plan, stage="upserting")),
            started_at,
            Jsonb(planned_counts(plan)),
        ),
    ).fetchone()
    return str(row[0])


def upsert_source_document(
    connection: Any,
    *,
    source_id: str,
    document: SecFixtureDocument,
) -> tuple[str, bool]:
    existing = connection.execute(
        """
        SELECT id FROM source_documents
        WHERE source_id = %s AND external_id = %s AND content_hash = %s
        """,
        (source_id, document.anchor_id, document.content_hash),
    ).fetchone()
    row = connection.execute(
        """
        INSERT INTO source_documents(
          source_id, external_id, url, title, publisher, document_date, observed_at,
          content_hash, media_type, raw_storage_uri, parser_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'application/json', %s, %s)
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
            document.anchor_id,
            document.source_url,
            document.title,
            SEC_FIXTURE_PUBLISHER,
            document.source_date,
            document.source_date,
            document.content_hash,
            document.fixture_path,
            document.parser_version,
        ),
    ).fetchone()
    return str(row[0]), existing is None


def upsert_raw_snapshot(
    connection: Any,
    *,
    ingestion_run_id: str,
    source_document_id: str,
    document: SecFixtureDocument,
) -> tuple[str, bool]:
    existing = connection.execute(
        """
        SELECT id FROM raw_source_snapshots
        WHERE anchor_id = %s AND content_hash = %s
        """,
        (document.anchor_id, document.content_hash),
    ).fetchone()
    row = connection.execute(
        """
        INSERT INTO raw_source_snapshots(
          ingestion_run_id, source_document_id, anchor_id, source_url, source_date,
          publisher, title, evidence_scope, record_mode, validation_status,
          parser_version, content_hash, raw_payload, review_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'fixture', 'normalized_fixture',
                %s, %s, %s, 'machine_verified')
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
            document.anchor_id,
            document.source_url,
            document.source_date,
            SEC_FIXTURE_PUBLISHER,
            document.title,
            SEC_FIXTURE_EVIDENCE_SCOPE,
            document.parser_version,
            document.content_hash,
            Jsonb(dict(document.raw_payload)),
        ),
    ).fetchone()
    return str(row[0]), existing is None


def execute_database_upsert(
    connection: Any,
    *,
    plan: SecFixturePlan,
    started_at: datetime,
) -> tuple[dict[str, int], str]:
    counts = planned_counts(plan)
    with connection.transaction():
        source_id = ensure_fixture_source(connection)
        ingestion_run_id = start_ingestion_run(
            connection,
            source_id=source_id,
            plan=plan,
            started_at=started_at,
        )
        for document in plan.documents:
            source_document_id, document_inserted = upsert_source_document(
                connection,
                source_id=source_id,
                document=document,
            )
            _, snapshot_inserted = upsert_raw_snapshot(
                connection,
                ingestion_run_id=ingestion_run_id,
                source_document_id=source_document_id,
                document=document,
            )
            counts[
                "source_documents_inserted" if document_inserted else "source_documents_reused"
            ] += 1
            counts[
                "raw_snapshots_inserted" if snapshot_inserted else "raw_snapshots_reused"
            ] += 1
        connection.execute(
            """
            UPDATE ingestion_runs
            SET checkpoint = %s, counts = %s, status = 'succeeded', finished_at = now(),
                error_class = NULL, error_message = NULL
            WHERE id = %s
            """,
            (
                Jsonb(checkpoint(plan, stage="completed")),
                Jsonb(counts),
                ingestion_run_id,
            ),
        )
    return counts, ingestion_run_id


def run_sec_fixture_ingestion(
    submissions_payload: Mapping[str, Any],
    companyfacts_payload: Mapping[str, Any],
    *,
    execution_mode: str,
    connection: Any | None = None,
    submissions_fixture_path: str = "tests/fixtures/sec/submissions_golden.json",
    companyfacts_fixture_path: str = "tests/fixtures/sec/companyfacts_golden.json",
    clock: Callable[[], datetime] = utc_now,
) -> dict[str, Any]:
    started_at = clock()
    try:
        mode = validate_execution_mode(execution_mode)
        plan = build_sec_fixture_plan(
            submissions_payload,
            companyfacts_payload,
            submissions_fixture_path=submissions_fixture_path,
            companyfacts_fixture_path=companyfacts_fixture_path,
        )
        counts = planned_counts(plan)
        ingestion_run_id: str | None = None
        database_write_performed = False
        if mode == "fixture":
            if connection is None:
                raise ValueError("fixture execution requires a PostgreSQL connection")
            counts, ingestion_run_id = execute_database_upsert(
                connection,
                plan=plan,
                started_at=started_at,
            )
            database_write_performed = True
        finished_at = clock()
        return {
            **report_base(
                execution_mode=mode,
                started_at=started_at,
                finished_at=finished_at,
            ),
            "status": "succeeded",
            "checkpoint": checkpoint(plan, stage="completed"),
            "counts": counts,
            "error_class": None,
            "error_message": None,
            "database_write_performed": database_write_performed,
            "ingestion_run_id": ingestion_run_id,
            "release_scope": {
                "fixture_only": True,
                "live_sec_request_performed": False,
                "a202_closed_by_report": False,
                "a209_closed_by_report": False,
                "mvp_release_ready": False,
            },
        }
    except Exception as exc:  # noqa: BLE001 - report is the governed failure boundary.
        return failure_report(
            execution_mode=execution_mode,
            error=exc,
            started_at=started_at,
            finished_at=clock(),
        )
