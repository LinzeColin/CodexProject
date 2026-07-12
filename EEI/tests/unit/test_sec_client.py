from __future__ import annotations

import asyncio
import hashlib
import json

import httpx
import pytest

from apps.api.app.ingest.sec_client import (
    SEC_DEFAULT_TIMEOUT_SECONDS,
    SEC_MAX_ATTEMPTS,
    SEC_MAX_REQUESTS_PER_SECOND,
    SEC_MIN_REQUEST_INTERVAL_SECONDS,
    ContentHashCache,
    DeterministicRateLimiter,
    SecClientConfigurationError,
    SecEdgarClient,
    SecRetryPolicy,
    SecUrlNotAllowedError,
    normalize_cik,
    validate_sec_url,
    validate_sec_user_agent,
)
from scripts.validate_sec_client_contract import (
    build_contracts,
    build_resilience_contracts,
    validate_artifacts,
    validate_resilience_artifacts,
)

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


def zero_jitter(_maximum_seconds: float) -> float:
    return 0.0


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


def test_timeout_retries_are_bounded_and_preserve_configured_timeout() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) < SEC_MAX_ATTEMPTS:
            raise httpx.ReadTimeout("fixture timeout", request=request)
        return httpx.Response(200, content=b'{"status":"ok"}')

    clock = FakeClock()

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            limiter=DeterministicRateLimiter(clock=clock, sleep=clock.sleep),
            retry_sleep=clock.sleep,
            jitter=zero_jitter,
            transport=httpx.MockTransport(handler),
        ) as client:
            result = await client.get_json("submissions/timeout-retry.json")

        assert result.attempt_count == SEC_MAX_ATTEMPTS
        assert result.retry_delays_seconds == pytest.approx((0.25, 0.5))
        assert result.processing_required is True

    asyncio.run(run())

    assert len(requests) == SEC_MAX_ATTEMPTS
    assert all(
        request.extensions["timeout"]["read"] == SEC_DEFAULT_TIMEOUT_SECONDS
        for request in requests
    )
    assert clock.sleeps == pytest.approx([0.25, 0.5])


def test_429_and_503_retry_after_delays_are_honored_and_capped() -> None:
    responses = [
        httpx.Response(429, headers={"retry-after": "1.5"}),
        httpx.Response(503, headers={"retry-after": "999"}),
        httpx.Response(200, content=b'{"status":"recovered"}'),
    ]
    clock = FakeClock()

    async def handler(_request: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            limiter=DeterministicRateLimiter(clock=clock, sleep=clock.sleep),
            retry_sleep=clock.sleep,
            jitter=zero_jitter,
            transport=httpx.MockTransport(handler),
        ) as client:
            result = await client.get_json("submissions/status-retry.json")

        assert result.attempt_count == 3
        assert result.retry_delays_seconds == pytest.approx((1.5, 2.0))
        assert result.payload == {"status": "recovered"}

    asyncio.run(run())

    assert responses == []
    assert clock.sleeps == pytest.approx([1.5, 2.0])


def test_timeout_exhaustion_stops_after_three_attempts() -> None:
    attempts = 0
    clock = FakeClock()

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("persistent timeout", request=request)

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            limiter=DeterministicRateLimiter(clock=clock, sleep=clock.sleep),
            retry_sleep=clock.sleep,
            jitter=zero_jitter,
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(httpx.ReadTimeout, match="persistent timeout"):
                await client.get_json("submissions/exhausted.json")

    asyncio.run(run())

    assert attempts == SEC_MAX_ATTEMPTS
    assert clock.sleeps == pytest.approx([0.25, 0.5])


def test_non_retryable_status_fails_without_retry() -> None:
    attempts = 0
    clock = FakeClock()
    content_hash_cache = ContentHashCache()

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(500, content=b'{"error":"server"}')

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            limiter=DeterministicRateLimiter(clock=clock, sleep=clock.sleep),
            content_hash_cache=content_hash_cache,
            retry_sleep=clock.sleep,
            jitter=zero_jitter,
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(httpx.HTTPStatusError, match="500 Internal Server Error"):
                await client.get_json("submissions/non-retryable.json")

    asyncio.run(run())

    assert attempts == 1
    assert clock.sleeps == []


def test_content_hash_cache_skips_unchanged_duplicate_processing() -> None:
    bodies = [b'{"value":1}', b'{"value":1}', b'{"value":2}']
    clock = FakeClock()

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=bodies.pop(0))

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            limiter=DeterministicRateLimiter(clock=clock, sleep=clock.sleep),
            retry_sleep=clock.sleep,
            jitter=zero_jitter,
            transport=httpx.MockTransport(handler),
        ) as client:
            first = await client.get_json("submissions/repeated.json")
            repeated = await client.get_json("submissions/repeated.json")
            changed = await client.get_json("submissions/repeated.json")

        first_hash = hashlib.sha256(b'{"value":1}').hexdigest()
        changed_hash = hashlib.sha256(b'{"value":2}').hexdigest()
        assert first.content_sha256 == first_hash
        assert first.previous_content_sha256 is None
        assert first.processing_required is True
        assert first.cache_hit is False
        assert repeated.content_sha256 == first_hash
        assert repeated.previous_content_sha256 == first_hash
        assert repeated.processing_required is False
        assert repeated.cache_hit is True
        assert changed.content_sha256 == changed_hash
        assert changed.previous_content_sha256 == first_hash
        assert changed.processing_required is True
        assert changed.cache_hit is False

    asyncio.run(run())

    assert bodies == []


def test_invalid_json_does_not_replace_last_successful_content_hash() -> None:
    bodies = [b'{"value":1}', b"not-json", b'{"value":1}']
    clock = FakeClock()

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=bodies.pop(0))

    async def run() -> None:
        async with SecEdgarClient(
            user_agent=USER_AGENT,
            limiter=DeterministicRateLimiter(clock=clock, sleep=clock.sleep),
            retry_sleep=clock.sleep,
            jitter=zero_jitter,
            transport=httpx.MockTransport(handler),
        ) as client:
            first = await client.get_json("submissions/parse-failure.json")
            with pytest.raises(json.JSONDecodeError):
                await client.get_json("submissions/parse-failure.json")
            after_failure = await client.get_json("submissions/parse-failure.json")

        assert first.processing_required is True
        assert after_failure.processing_required is False
        assert after_failure.previous_content_sha256 == first.content_sha256

    asyncio.run(run())


def test_retry_policy_and_timeout_cannot_exceed_governed_bounds() -> None:
    with pytest.raises(ValueError, match="between 1 and 3"):
        SecRetryPolicy(max_attempts=SEC_MAX_ATTEMPTS + 1)
    with pytest.raises(ValueError, match="<= 30.0"):
        SecEdgarClient(user_agent=USER_AGENT, timeout_seconds=31.0)

    policy = SecRetryPolicy()
    assert policy.delay_seconds(
        failed_attempt=1,
        retry_after_seconds=None,
        jitter=lambda maximum: maximum,
    ) == pytest.approx(0.375)
    assert policy.delay_seconds(
        failed_attempt=1,
        retry_after_seconds=999.0,
        jitter=lambda maximum: maximum,
    ) == pytest.approx(2.0)
    with pytest.raises(SecClientConfigurationError, match="out-of-range"):
        policy.delay_seconds(
            failed_attempt=1,
            retry_after_seconds=None,
            jitter=lambda maximum: maximum + 1,
        )


def test_contract_artifacts_are_mock_only_and_do_not_close_release_gates() -> None:
    a096, a097 = build_contracts()

    validate_artifacts(a096, a097)

    assert a096["release_scope"]["live_sec_request_performed"] is False
    assert a096["release_scope"]["mvp_release_ready"] is False
    assert a097["contract"]["max_requests_per_second"] == 8


def test_resilience_contract_artifacts_are_fail_closed_and_truthful() -> None:
    a098, a099 = build_resilience_contracts()

    validate_resilience_artifacts(a098, a099)

    assert a098["contract"]["max_attempts"] == 3
    assert a098["contract"]["retryable_status_codes"] == [429, 503]
    assert a099["contract"]["network_fetch_skipped_by_hash_cache"] is False
    assert a099["release_scope"]["mvp_release_ready"] is False
