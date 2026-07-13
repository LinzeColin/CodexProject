from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from .sec_client import (
    DeterministicRateLimiter,
    SecEdgarClient,
    normalize_cik,
    validate_sec_user_agent,
)
from .sec_fixture_ingestion import run_sec_fixture_ingestion
from .sec_normalizer import normalize_sec_company_facts, normalize_sec_submissions

SEC_SMOKE_REPORT_VERSION = "eei-sec-connector-smoke-v1"
SEC_FIXTURE_SMOKE_USER_AGENT = "EEI/0.1 fixture-smoke eei-operator@example.com"


class SecSmokeConfigurationError(ValueError):
    pass


class SyntheticClock:
    def __init__(self) -> None:
        self.value = 100.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.value

    async def sleep(self, delay: float) -> None:
        self.sleeps.append(delay)
        self.value += delay


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


def user_agent_evidence(user_agent: str) -> dict[str, Any]:
    return {
        "value_recorded": False,
        "sha256": hashlib.sha256(user_agent.encode("utf-8")).hexdigest(),
        "contact_email_present": "@" in user_agent,
        "descriptive_identity_present": len(user_agent.split()) >= 2,
    }


def release_scope(*, live_network_performed: bool) -> dict[str, Any]:
    return {
        "live_network_performed": live_network_performed,
        "database_write_performed": False,
        "production_publication_performed": False,
        "a202_closed_by_smoke": False,
        "a209_closed_by_smoke": False,
        "mvp_release_ready": False,
    }


def validate_live_smoke_inputs(
    *,
    cik: str,
    user_agent: str,
    allow_live_network: bool,
) -> str:
    if not allow_live_network:
        raise SecSmokeConfigurationError("live smoke requires explicit network opt-in")
    if not cik.strip():
        raise SecSmokeConfigurationError("live smoke requires an explicit CIK")
    if not user_agent.strip():
        raise SecSmokeConfigurationError("live smoke requires SEC_USER_AGENT")
    validate_sec_user_agent(user_agent)
    return normalize_cik(cik)


async def run_fixture_smoke(
    submissions_payload: Mapping[str, Any],
    companyfacts_payload: Mapping[str, Any],
    *,
    now: Callable[[], datetime] = utc_now,
) -> dict[str, Any]:
    started_at = now()
    fixture_bodies = {
        "submissions": canonical_json_bytes(submissions_payload),
        "companyfacts": canonical_json_bytes(companyfacts_payload),
    }
    attempts = {"submissions": 0, "companyfacts": 0}
    requests: list[dict[str, Any]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        kind = "companyfacts" if "/companyfacts/" in request.url.path else "submissions"
        attempts[kind] += 1
        requests.append(
            {
                "url": str(request.url),
                "host": request.url.host,
                "user_agent_matches": request.headers.get("user-agent")
                == SEC_FIXTURE_SMOKE_USER_AGENT,
                "authorization_present": "authorization" in request.headers,
                "cookie_present": "cookie" in request.headers,
            }
        )
        if attempts[kind] == 1:
            status_code = 503 if kind == "submissions" else 429
            return httpx.Response(status_code, headers={"retry-after": "0.25"})
        return httpx.Response(
            200,
            content=fixture_bodies[kind],
            headers={"content-type": "application/json"},
        )

    clock = SyntheticClock()
    async with SecEdgarClient(
        user_agent=SEC_FIXTURE_SMOKE_USER_AGENT,
        limiter=DeterministicRateLimiter(clock=clock, sleep=clock.sleep),
        retry_sleep=clock.sleep,
        jitter=lambda _maximum: 0.0,
        transport=httpx.MockTransport(handler),
    ) as client:
        submissions = await client.get_submissions("0000000001")
        companyfacts = await client.get_company_facts("0000000001")

    ingestion_moments = iter((started_at, started_at + timedelta(seconds=1)))
    ingestion = run_sec_fixture_ingestion(
        submissions.payload,
        companyfacts.payload,
        execution_mode="dry_run",
        clock=lambda: next(ingestion_moments),
    )
    if ingestion["status"] != "succeeded":
        raise RuntimeError(f"fixture dry-run failed: {ingestion['error_message']}")

    return {
        "schema_version": SEC_SMOKE_REPORT_VERSION,
        "task_id": "T706",
        "acceptance_ids": ["A096", "A098", "A102"],
        "mode": "fixture",
        "status": "succeeded",
        "started_at": isoformat(started_at),
        "finished_at": isoformat(now()),
        "transport": "httpx.MockTransport",
        "request_contract": {
            "request_count": len(requests),
            "requests": requests,
            "allowed_hosts_only": all(
                request["host"] in {"data.sec.gov", "www.sec.gov"} for request in requests
            ),
            "credentials_absent": all(
                not request["authorization_present"] and not request["cookie_present"]
                for request in requests
            ),
            "user_agent": user_agent_evidence(SEC_FIXTURE_SMOKE_USER_AGENT),
        },
        "responses": {
            "submissions": {
                "attempt_count": submissions.attempt_count,
                "retry_delays_seconds": list(submissions.retry_delays_seconds),
                "content_sha256": submissions.content_sha256,
                "processing_required": submissions.processing_required,
            },
            "companyfacts": {
                "attempt_count": companyfacts.attempt_count,
                "retry_delays_seconds": list(companyfacts.retry_delays_seconds),
                "content_sha256": companyfacts.content_sha256,
                "processing_required": companyfacts.processing_required,
            },
        },
        "ingestion": {
            "execution_mode": ingestion["execution_mode"],
            "record_mode": ingestion["record_mode"],
            "status": ingestion["status"],
            "checkpoint": ingestion["checkpoint"],
            "counts": ingestion["counts"],
            "database_write_performed": ingestion["database_write_performed"],
            "ingestion_run_id": ingestion["ingestion_run_id"],
        },
        "release_scope": release_scope(live_network_performed=False),
    }


async def run_live_smoke(
    *,
    cik: str,
    user_agent: str,
    allow_live_network: bool,
    transport: httpx.AsyncBaseTransport | None = None,
    now: Callable[[], datetime] = utc_now,
) -> dict[str, Any]:
    started_at = now()
    normalized_cik = validate_live_smoke_inputs(
        cik=cik,
        user_agent=user_agent,
        allow_live_network=allow_live_network,
    )
    async with SecEdgarClient(user_agent=user_agent, transport=transport) as client:
        submissions_response = await client.get_submissions(normalized_cik)
        companyfacts_response = await client.get_company_facts(normalized_cik)

    submissions = normalize_sec_submissions(
        submissions_response.payload,
        record_mode="live",
    )
    companyfacts = normalize_sec_company_facts(
        companyfacts_response.payload,
        record_mode="live",
    )
    if submissions.cik != companyfacts.cik:
        raise RuntimeError("live SEC payload CIK mismatch")

    live_network_performed = transport is None
    return {
        "schema_version": SEC_SMOKE_REPORT_VERSION,
        "task_id": "T706",
        "acceptance_ids": ["A096", "A098", "A102"],
        "mode": "live",
        "status": "succeeded",
        "started_at": isoformat(started_at),
        "finished_at": isoformat(now()),
        "transport": "external_https" if live_network_performed else "injected_transport",
        "cik": normalized_cik,
        "user_agent": user_agent_evidence(user_agent),
        "responses": {
            "submissions": {
                "attempt_count": submissions_response.attempt_count,
                "retry_delays_seconds": list(submissions_response.retry_delays_seconds),
                "content_sha256": submissions_response.content_sha256,
                "normalized_filing_count": len(submissions.filings),
            },
            "companyfacts": {
                "attempt_count": companyfacts_response.attempt_count,
                "retry_delays_seconds": list(companyfacts_response.retry_delays_seconds),
                "content_sha256": companyfacts_response.content_sha256,
                "normalized_fact_count": len(companyfacts.facts),
            },
        },
        "persistence": {
            "database_write_performed": False,
            "publication_performed": False,
        },
        "release_scope": release_scope(live_network_performed=live_network_performed),
    }
