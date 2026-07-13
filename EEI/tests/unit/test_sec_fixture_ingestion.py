from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from apps.api.app.ingest.sec_fixture_ingestion import (
    SEC_FIXTURE_REPORT_VERSION,
    build_sec_fixture_plan,
    run_sec_fixture_ingestion,
)

ROOT = Path(__file__).resolve().parents[2]
SUBMISSIONS_FIXTURE = ROOT / "tests/fixtures/sec/submissions_golden.json"
COMPANYFACTS_FIXTURE = ROOT / "tests/fixtures/sec/companyfacts_golden.json"


def read_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def fixtures() -> tuple[dict[str, Any], dict[str, Any]]:
    return read_fixture(SUBMISSIONS_FIXTURE), read_fixture(COMPANYFACTS_FIXTURE)


def fixed_clock() -> Any:
    moments = iter(
        (
            datetime(2026, 7, 13, 0, 0, tzinfo=UTC),
            datetime(2026, 7, 13, 0, 0, 1, tzinfo=UTC),
        )
    )
    return lambda: next(moments)


def test_plan_preserves_fixture_identity_and_normalized_counts() -> None:
    submissions, companyfacts = fixtures()

    plan = build_sec_fixture_plan(submissions, companyfacts)

    assert plan.cik == "0000000001"
    assert plan.entity_name == "EEI SEC Golden Fixture Corp"
    assert len(plan.documents) == 2
    assert len(plan.submissions.filings) == 2
    assert len(plan.companyfacts.facts) == 3
    assert {item.kind for item in plan.documents} == {"submissions", "companyfacts"}
    assert all(item.source_url.startswith("fixture://sec/") for item in plan.documents)
    assert all(len(item.content_hash) == 64 for item in plan.documents)


def test_dry_run_reports_plan_without_database_write() -> None:
    submissions, companyfacts = fixtures()

    report = run_sec_fixture_ingestion(
        submissions,
        companyfacts,
        execution_mode="dry_run",
        clock=fixed_clock(),
    )

    assert report["schema_version"] == SEC_FIXTURE_REPORT_VERSION
    assert report["status"] == "succeeded"
    assert report["checkpoint"]["stage"] == "completed"
    assert report["counts"]["source_documents_planned"] == 2
    assert report["counts"]["raw_snapshots_planned"] == 2
    assert report["counts"]["source_documents_inserted"] == 0
    assert report["counts"]["raw_snapshots_inserted"] == 0
    assert report["database_write_performed"] is False
    assert report["ingestion_run_id"] is None
    assert report["error_class"] is None
    assert report["release_scope"]["mvp_release_ready"] is False


def test_fixture_mode_without_connection_fails_with_error_class() -> None:
    submissions, companyfacts = fixtures()

    report = run_sec_fixture_ingestion(
        submissions,
        companyfacts,
        execution_mode="fixture",
        clock=fixed_clock(),
    )

    assert report["status"] == "failed"
    assert report["checkpoint"] == {"stage": "failed"}
    assert report["error_class"] == "ValueError"
    assert "PostgreSQL connection" in report["error_message"]
    assert report["database_write_performed"] is False


def test_mismatched_fixture_identity_fails_closed() -> None:
    submissions, companyfacts = fixtures()
    companyfacts["cik"] = 2

    report = run_sec_fixture_ingestion(
        submissions,
        companyfacts,
        execution_mode="dry_run",
        clock=fixed_clock(),
    )

    assert report["status"] == "failed"
    assert report["error_class"] == "ValueError"
    assert report["error_message"] == "SEC fixture CIK mismatch"


def test_synthetic_fixture_cannot_be_relabeled_or_lose_metadata() -> None:
    submissions, companyfacts = fixtures()
    del submissions["_fixture_metadata"]

    report = run_sec_fixture_ingestion(
        submissions,
        companyfacts,
        execution_mode="dry_run",
        clock=fixed_clock(),
    )

    assert report["status"] == "failed"
    assert report["error_class"] == "ValueError"
    assert "_fixture_metadata" in report["error_message"]


def test_report_timestamps_are_bounded_by_injected_clock() -> None:
    submissions, companyfacts = fixtures()
    start = datetime(2026, 7, 13, 1, 2, 3, tzinfo=UTC)
    moments = iter((start, start + timedelta(seconds=2)))

    report = run_sec_fixture_ingestion(
        submissions,
        companyfacts,
        execution_mode="dry_run",
        clock=lambda: next(moments),
    )

    assert report["started_at"] == "2026-07-13T01:02:03Z"
    assert report["finished_at"] == "2026-07-13T01:02:05Z"
