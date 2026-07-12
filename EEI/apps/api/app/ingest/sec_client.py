from __future__ import annotations

import asyncio
import hashlib
import math
import random
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import monotonic
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

SEC_ALLOWED_HOSTS = frozenset({"data.sec.gov", "www.sec.gov"})
SEC_MAX_REQUESTS_PER_SECOND = 8
SEC_MIN_REQUEST_INTERVAL_SECONDS = 1 / SEC_MAX_REQUESTS_PER_SECOND
SEC_DATA_BASE_URL = "https://data.sec.gov/"
SEC_SUBMISSIONS_PATH = "submissions/CIK{cik}.json"
SEC_COMPANY_FACTS_PATH = "api/xbrl/companyfacts/CIK{cik}.json"
SEC_DEFAULT_TIMEOUT_SECONDS = 10.0
SEC_MAX_TIMEOUT_SECONDS = 30.0
SEC_MAX_ATTEMPTS = 3
SEC_RETRY_BACKOFF_BASE_SECONDS = 0.25
SEC_RETRY_BACKOFF_CAP_SECONDS = 2.0
SEC_RETRY_JITTER_CAP_SECONDS = 0.125
SEC_RETRYABLE_STATUS_CODES = frozenset({429, 503})

_CONTACT_EMAIL_PATTERN = re.compile(
    r"(?i)(?<![\w.+-])[a-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+(?![\w.-])"
)

Clock = Callable[[], float]
Sleeper = Callable[[float], Awaitable[None]]
Jitter = Callable[[float], float]


class SecClientConfigurationError(ValueError):
    """Raised when the SEC client identity is not safe to use."""


class SecUrlNotAllowedError(ValueError):
    """Raised when a request is outside the governed SEC host boundary."""


def random_jitter(maximum_seconds: float) -> float:
    return random.uniform(0.0, maximum_seconds)


def validate_sec_user_agent(value: str) -> str:
    user_agent = value.strip()
    if not user_agent:
        raise SecClientConfigurationError("SEC User-Agent is required")
    if not _CONTACT_EMAIL_PATTERN.search(user_agent):
        raise SecClientConfigurationError(
            "SEC User-Agent must include an operator contact email"
        )

    descriptor = _CONTACT_EMAIL_PATTERN.sub("", user_agent).strip(" ()[];/")
    if len(descriptor) < 3 or not any(character.isalpha() for character in descriptor):
        raise SecClientConfigurationError(
            "SEC User-Agent must include a descriptive application identity"
        )
    return user_agent


def validate_sec_url(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise SecUrlNotAllowedError("SEC request URL is required")
    if candidate.startswith("//"):
        raise SecUrlNotAllowedError("scheme-relative SEC request URLs are not allowed")

    absolute = candidate if urlsplit(candidate).scheme else urljoin(SEC_DATA_BASE_URL, candidate)
    parsed = urlsplit(absolute)
    if parsed.scheme.lower() != "https":
        raise SecUrlNotAllowedError("SEC request URL must use HTTPS")
    if parsed.hostname is None or parsed.hostname.lower() not in SEC_ALLOWED_HOSTS:
        raise SecUrlNotAllowedError("SEC request host is not allowlisted")
    if parsed.username is not None or parsed.password is not None:
        raise SecUrlNotAllowedError("SEC request URL must not contain credentials")
    try:
        port = parsed.port
    except ValueError as exc:
        raise SecUrlNotAllowedError("SEC request URL has an invalid port") from exc
    if port not in {None, 443}:
        raise SecUrlNotAllowedError("SEC request URL must use the standard HTTPS port")
    if parsed.fragment:
        raise SecUrlNotAllowedError("SEC request URL must not contain a fragment")
    return absolute


def normalize_cik(value: str | int) -> str:
    raw_value = str(value).strip()
    if raw_value.upper().startswith("CIK"):
        raw_value = raw_value[3:]
    if not raw_value.isascii() or not raw_value.isdigit():
        raise ValueError("CIK must contain ASCII digits only")
    if len(raw_value) > 10:
        raise ValueError("CIK must contain at most 10 digits")
    return raw_value.zfill(10)


class DeterministicRateLimiter:
    """Serialize request starts with a fixed minimum interval and no burst allowance."""

    def __init__(
        self,
        *,
        max_requests_per_second: int = SEC_MAX_REQUESTS_PER_SECOND,
        clock: Clock = monotonic,
        sleep: Sleeper = asyncio.sleep,
    ) -> None:
        if max_requests_per_second <= 0:
            raise ValueError("max_requests_per_second must be positive")
        if max_requests_per_second > SEC_MAX_REQUESTS_PER_SECOND:
            raise ValueError(
                f"SEC client rate must be <= {SEC_MAX_REQUESTS_PER_SECOND} requests/sec"
            )
        self.max_requests_per_second = max_requests_per_second
        self.minimum_interval_seconds = 1 / max_requests_per_second
        self._clock = clock
        self._sleep = sleep
        self._lock = asyncio.Lock()
        self._next_request_at: float | None = None

    async def acquire(self) -> float:
        async with self._lock:
            now = self._clock()
            if self._next_request_at is None:
                self._next_request_at = now + self.minimum_interval_seconds
                return 0.0

            delay = max(0.0, self._next_request_at - now)
            if delay > 0:
                await self._sleep(delay)
            now = self._clock()
            self._next_request_at = max(self._next_request_at, now) + (
                self.minimum_interval_seconds
            )
            return delay


@dataclass(frozen=True)
class SecRetryPolicy:
    max_attempts: int = SEC_MAX_ATTEMPTS
    backoff_base_seconds: float = SEC_RETRY_BACKOFF_BASE_SECONDS
    backoff_cap_seconds: float = SEC_RETRY_BACKOFF_CAP_SECONDS
    jitter_cap_seconds: float = SEC_RETRY_JITTER_CAP_SECONDS
    retryable_status_codes: frozenset[int] = SEC_RETRYABLE_STATUS_CODES

    def __post_init__(self) -> None:
        if not 1 <= self.max_attempts <= SEC_MAX_ATTEMPTS:
            raise ValueError(f"max_attempts must be between 1 and {SEC_MAX_ATTEMPTS}")
        if self.backoff_base_seconds <= 0:
            raise ValueError("backoff_base_seconds must be positive")
        if self.backoff_cap_seconds < self.backoff_base_seconds:
            raise ValueError("backoff_cap_seconds must be >= backoff_base_seconds")
        if not 0 <= self.jitter_cap_seconds <= self.backoff_cap_seconds:
            raise ValueError("jitter_cap_seconds must be between 0 and backoff_cap_seconds")
        if not SEC_RETRYABLE_STATUS_CODES.issubset(self.retryable_status_codes):
            raise ValueError("retryable_status_codes must include HTTP 429 and 503")

    def delay_seconds(
        self,
        *,
        failed_attempt: int,
        retry_after_seconds: float | None,
        jitter: Jitter,
    ) -> float:
        if not 1 <= failed_attempt < self.max_attempts:
            raise ValueError("failed_attempt must identify a retryable non-final attempt")
        exponential = self.backoff_base_seconds * (2 ** (failed_attempt - 1))
        base_delay = min(self.backoff_cap_seconds, exponential)
        if retry_after_seconds is not None:
            base_delay = min(
                self.backoff_cap_seconds,
                max(base_delay, retry_after_seconds),
            )
        jitter_seconds = jitter(self.jitter_cap_seconds)
        if (
            not math.isfinite(jitter_seconds)
            or jitter_seconds < 0
            or jitter_seconds > self.jitter_cap_seconds
        ):
            raise SecClientConfigurationError("retry jitter returned an out-of-range value")
        return min(self.backoff_cap_seconds, base_delay + jitter_seconds)


def parse_retry_after_seconds(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value.strip())
    except ValueError:
        return None
    if not math.isfinite(parsed) or parsed < 0:
        return None
    return parsed


@dataclass(frozen=True)
class ContentHashDecision:
    content_sha256: str
    previous_content_sha256: str | None
    processing_required: bool

    @property
    def cache_hit(self) -> bool:
        return not self.processing_required


class ContentHashCache:
    """Track the last successful raw-response hash per canonical request URL."""

    def __init__(self) -> None:
        self._hashes: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def observe(self, *, url: str, content: bytes) -> ContentHashDecision:
        content_sha256 = hashlib.sha256(content).hexdigest()
        async with self._lock:
            previous = self._hashes.get(url)
            processing_required = previous != content_sha256
            if processing_required:
                self._hashes[url] = content_sha256
        return ContentHashDecision(
            content_sha256=content_sha256,
            previous_content_sha256=previous,
            processing_required=processing_required,
        )


@dataclass(frozen=True)
class SecJsonResponse:
    url: str
    status_code: int
    payload: Any
    request_id: str | None
    attempt_count: int
    retry_delays_seconds: tuple[float, ...]
    content_sha256: str
    previous_content_sha256: str | None
    processing_required: bool
    cache_hit: bool


class SecEdgarClient:
    def __init__(
        self,
        *,
        user_agent: str,
        limiter: DeterministicRateLimiter | None = None,
        retry_policy: SecRetryPolicy | None = None,
        content_hash_cache: ContentHashCache | None = None,
        timeout_seconds: float = SEC_DEFAULT_TIMEOUT_SECONDS,
        retry_sleep: Sleeper = asyncio.sleep,
        jitter: Jitter = random_jitter,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not 0 < timeout_seconds <= SEC_MAX_TIMEOUT_SECONDS:
            raise ValueError(
                f"timeout_seconds must be > 0 and <= {SEC_MAX_TIMEOUT_SECONDS}"
            )
        self.user_agent = validate_sec_user_agent(user_agent)
        self.limiter = limiter or DeterministicRateLimiter()
        self.retry_policy = retry_policy or SecRetryPolicy()
        self.content_hash_cache = content_hash_cache or ContentHashCache()
        self._retry_sleep = retry_sleep
        self._jitter = jitter
        self._client = httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "User-Agent": self.user_agent,
            },
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            transport=transport,
            trust_env=False,
        )

    async def __aenter__(self) -> SecEdgarClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_json(self, url: str) -> SecJsonResponse:
        request_url = str(httpx.URL(validate_sec_url(url)))
        retry_delays: list[float] = []
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            await self.limiter.acquire()
            try:
                response = await self._client.get(request_url)
            except httpx.TimeoutException:
                if attempt == self.retry_policy.max_attempts:
                    raise
                delay = self.retry_policy.delay_seconds(
                    failed_attempt=attempt,
                    retry_after_seconds=None,
                    jitter=self._jitter,
                )
                retry_delays.append(delay)
                await self._retry_sleep(delay)
                continue

            if (
                response.status_code in self.retry_policy.retryable_status_codes
                and attempt < self.retry_policy.max_attempts
            ):
                delay = self.retry_policy.delay_seconds(
                    failed_attempt=attempt,
                    retry_after_seconds=parse_retry_after_seconds(
                        response.headers.get("retry-after")
                    ),
                    jitter=self._jitter,
                )
                retry_delays.append(delay)
                await response.aclose()
                await self._retry_sleep(delay)
                continue

            response.raise_for_status()
            payload = response.json()
            cache = await self.content_hash_cache.observe(
                url=request_url,
                content=response.content,
            )
            return SecJsonResponse(
                url=str(response.url),
                status_code=response.status_code,
                payload=payload,
                request_id=response.headers.get("x-amzn-requestid"),
                attempt_count=attempt,
                retry_delays_seconds=tuple(retry_delays),
                content_sha256=cache.content_sha256,
                previous_content_sha256=cache.previous_content_sha256,
                processing_required=cache.processing_required,
                cache_hit=cache.cache_hit,
            )
        raise AssertionError("SEC retry loop exhausted without returning or raising")

    async def get_submissions(self, cik: str | int) -> SecJsonResponse:
        return await self.get_json(SEC_SUBMISSIONS_PATH.format(cik=normalize_cik(cik)))

    async def get_company_facts(self, cik: str | int) -> SecJsonResponse:
        return await self.get_json(SEC_COMPANY_FACTS_PATH.format(cik=normalize_cik(cik)))
