from __future__ import annotations

import asyncio

import httpx
import pytest

from apps.api.app.ingest.sec_client import (
    SEC_MAX_REQUESTS_PER_SECOND,
    SEC_MIN_REQUEST_INTERVAL_SECONDS,
    DeterministicRateLimiter,
    SecClientConfigurationError,
    SecEdgarClient,
    SecUrlNotAllowedError,
    normalize_cik,
    validate_sec_url,
    validate_sec_user_agent,
)
from scripts.validate_sec_client_contract import build_contracts, validate_artifacts

USER_AGENT = "EEI/0.1 data-operations eei-operator@example.com"


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.value

    async def sleep(self, delay: float) -> None:
        self.sleeps.append(delay)
        self.value += delay


def test_descriptive_user_agent_requires_application_identity_and_contact() -> None:
    assert validate_sec_user_agent(USER_AGENT) == USER_AGENT

    with pytest.raises(SecClientConfigurationError, match="contact email"):
        validate_sec_user_agent("python-httpx/0.28")
    with pytest.raises(SecClientConfigurationError, match="application identity"):
        validate_sec_user_agent("(eei-operator@example.com)")


@pytest.mark.parametrize(
    "url",
    [
        "http://data.sec.gov/submissions/CIK0000320193.json",
        "https://data.sec.gov.evil.example/submissions/CIK0000320193.json",
        "https://example.com/",
        "//example.com/escape",
        "https://user:password@data.sec.gov/submissions/example.json",
        "https://data.sec.gov:8443/submissions/example.json",
        "https://data.sec.gov/submissions/example.json#fragment",
    ],
)
def test_url_allowlist_rejects_unsafe_or_non_sec_urls(url: str) -> None:
    with pytest.raises(SecUrlNotAllowedError):
        validate_sec_url(url)


def test_url_allowlist_accepts_exact_sec_hosts_and_relative_data_paths() -> None:
    assert validate_sec_url("submissions/example.json") == (
        "https://data.sec.gov/submissions/example.json"
    )
    assert validate_sec_url("https://www.sec.gov/Archives/example.json") == (
        "https://www.sec.gov/Archives/example.json"
    )


def test_mock_request_uses_governed_headers_without_credentials() -> None:
    captured_requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            json={"cik": "0000320193"},
            headers={"x-amzn-requestid": "request-123"},
        )

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            transport=httpx.MockTransport(handler),
        ) as client:
            result = await client.get_submissions("320193")

        assert result.status_code == 200
        assert result.payload == {"cik": "0000320193"}
        assert result.request_id == "request-123"

    asyncio.run(run())

    assert len(captured_requests) == 1
    request = captured_requests[0]
    assert str(request.url) == "https://data.sec.gov/submissions/CIK0000320193.json"
    assert request.headers["user-agent"] == USER_AGENT
    assert request.headers["accept"] == "application/json"
    assert "authorization" not in request.headers
    assert "cookie" not in request.headers


def test_company_facts_url_preserves_canonical_cik_padding() -> None:
    requested_urls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200, json={"entityName": "Apple Inc."})

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            transport=httpx.MockTransport(handler),
        ) as client:
            await client.get_company_facts("CIK320193")

    asyncio.run(run())

    assert normalize_cik(320193) == "0000320193"
    assert requested_urls == [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    ]


def test_client_does_not_follow_redirects_outside_allowlist() -> None:
    requested_urls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://example.com/escape"})

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(httpx.HTTPStatusError, match="302 Found"):
                await client.get_json("https://www.sec.gov/Archives/example.json")

    asyncio.run(run())

    assert requested_urls == ["https://www.sec.gov/Archives/example.json"]


def test_deterministic_limiter_serializes_starts_at_no_more_than_eight_per_second() -> None:
    clock = FakeClock()
    limiter = DeterministicRateLimiter(clock=clock, sleep=clock.sleep)
    acquired_at: list[float] = []

    async def run() -> None:
        for _ in range(10):
            await limiter.acquire()
            acquired_at.append(clock())

    asyncio.run(run())

    assert limiter.max_requests_per_second == SEC_MAX_REQUESTS_PER_SECOND
    assert limiter.minimum_interval_seconds == SEC_MIN_REQUEST_INTERVAL_SECONDS
    assert clock.sleeps == pytest.approx([SEC_MIN_REQUEST_INTERVAL_SECONDS] * 9)
    assert all(
        later - earlier >= SEC_MIN_REQUEST_INTERVAL_SECONDS - 1e-12
        for earlier, later in zip(acquired_at, acquired_at[1:], strict=False)
    )


def test_limiter_rejects_rate_above_governed_ceiling() -> None:
    with pytest.raises(ValueError, match="<= 8"):
        DeterministicRateLimiter(max_requests_per_second=9)


def test_contract_artifacts_are_mock_only_and_do_not_close_release_gates() -> None:
    a096, a097 = build_contracts()

    validate_artifacts(a096, a097)

    assert a096["release_scope"]["live_sec_request_performed"] is False
    assert a096["release_scope"]["mvp_release_ready"] is False
    assert a097["contract"]["max_requests_per_second"] == 8
