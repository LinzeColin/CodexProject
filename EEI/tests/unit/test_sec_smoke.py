from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from apps.api.app.ingest.sec_normalizer import SecNormalizationError
from apps.api.app.ingest.sec_smoke import (
    SEC_SMOKE_REPORT_VERSION,
    SecSmokeConfigurationError,
    run_fixture_smoke,
    run_live_smoke,
)

ROOT = Path(__file__).resolve().parents[2]
SUBMISSIONS_FIXTURE = ROOT / "tests/fixtures/sec/submissions_golden.json"
COMPANYFACTS_FIXTURE = ROOT / "tests/fixtures/sec/companyfacts_golden.json"
LIVE_USER_AGENT = "EEI/0.1 live-smoke eei-operator@example.com"


def read_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def fixed_clock() -> Any:
    current = datetime(2026, 7, 13, 1, 0, tzinfo=UTC)

    def now() -> datetime:
        nonlocal current
        result = current
        current += timedelta(seconds=1)
        return result

    return now


def test_fixture_smoke_combines_allowlist_retry_and_dry_run_without_network() -> None:
    report = asyncio.run(
        run_fixture_smoke(
            read_fixture(SUBMISSIONS_FIXTURE),
            read_fixture(COMPANYFACTS_FIXTURE),
            now=fixed_clock(),
        )
    )

    assert report["schema_version"] == SEC_SMOKE_REPORT_VERSION
    assert report["status"] == "succeeded"
    assert report["transport"] == "httpx.MockTransport"
    assert report["request_contract"]["request_count"] == 4
    assert report["request_contract"]["allowed_hosts_only"] is True
    assert report["request_contract"]["credentials_absent"] is True
    assert all(
        request["user_agent_matches"] for request in report["request_contract"]["requests"]
    )
    assert report["responses"]["submissions"]["attempt_count"] == 2
    assert report["responses"]["submissions"]["retry_delays_seconds"] == [0.25]
    assert report["responses"]["companyfacts"]["attempt_count"] == 2
    assert report["responses"]["companyfacts"]["retry_delays_seconds"] == [0.25]
    assert report["ingestion"]["execution_mode"] == "dry_run"
    assert report["ingestion"]["counts"]["source_documents_planned"] == 2
    assert report["ingestion"]["database_write_performed"] is False
    assert report["ingestion"]["ingestion_run_id"] is None
    assert report["release_scope"]["live_network_performed"] is False
    assert report["release_scope"]["mvp_release_ready"] is False


def test_live_smoke_requires_explicit_network_opt_in_before_transport_use() -> None:
    transport_called = False

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal transport_called
        transport_called = True
        return httpx.Response(500)

    with pytest.raises(SecSmokeConfigurationError, match="explicit network opt-in"):
        asyncio.run(
            run_live_smoke(
                cik="1",
                user_agent=LIVE_USER_AGENT,
                allow_live_network=False,
                transport=httpx.MockTransport(handler),
            )
        )

    assert transport_called is False


def test_live_smoke_path_normalizes_injected_non_fixture_payload_without_persistence() -> None:
    submissions = deepcopy(read_fixture(SUBMISSIONS_FIXTURE))
    companyfacts = deepcopy(read_fixture(COMPANYFACTS_FIXTURE))
    submissions.pop("_fixture_metadata")
    companyfacts.pop("_fixture_metadata")

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = companyfacts if "/companyfacts/" in request.url.path else submissions
        return httpx.Response(200, json=payload)

    report = asyncio.run(
        run_live_smoke(
            cik="1",
            user_agent=LIVE_USER_AGENT,
            allow_live_network=True,
            transport=httpx.MockTransport(handler),
            now=fixed_clock(),
        )
    )

    assert report["mode"] == "live"
    assert report["transport"] == "injected_transport"
    assert report["responses"]["submissions"]["normalized_filing_count"] == 2
    assert report["responses"]["companyfacts"]["normalized_fact_count"] == 3
    assert report["persistence"]["database_write_performed"] is False
    assert report["persistence"]["publication_performed"] is False
    assert report["release_scope"]["live_network_performed"] is False
    assert LIVE_USER_AGENT not in json.dumps(report)


def test_fixture_payload_cannot_be_relabelled_by_live_smoke_path() -> None:
    submissions = read_fixture(SUBMISSIONS_FIXTURE)
    companyfacts = read_fixture(COMPANYFACTS_FIXTURE)

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = companyfacts if "/companyfacts/" in request.url.path else submissions
        return httpx.Response(200, json=payload)

    with pytest.raises(SecNormalizationError, match="cannot be relabeled"):
        asyncio.run(
            run_live_smoke(
                cik="1",
                user_agent=LIVE_USER_AGENT,
                allow_live_network=True,
                transport=httpx.MockTransport(handler),
            )
        )
