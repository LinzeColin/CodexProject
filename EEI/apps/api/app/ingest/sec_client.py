from __future__ import annotations

import asyncio
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

_CONTACT_EMAIL_PATTERN = re.compile(
    r"(?i)(?<![\w.+-])[a-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+(?![\w.-])"
)

Clock = Callable[[], float]
Sleeper = Callable[[float], Awaitable[None]]


class SecClientConfigurationError(ValueError):
    """Raised when the SEC client identity is not safe to use."""


class SecUrlNotAllowedError(ValueError):
    """Raised when a request is outside the governed SEC host boundary."""


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
class SecJsonResponse:
    url: str
    status_code: int
    payload: Any
    request_id: str | None


class SecEdgarClient:
    def __init__(
        self,
        *,
        user_agent: str,
        limiter: DeterministicRateLimiter | None = None,
        timeout_seconds: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.user_agent = validate_sec_user_agent(user_agent)
        self.limiter = limiter or DeterministicRateLimiter()
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
        request_url = validate_sec_url(url)
        await self.limiter.acquire()
        response = await self._client.get(request_url)
        response.raise_for_status()
        return SecJsonResponse(
            url=str(response.url),
            status_code=response.status_code,
            payload=response.json(),
            request_id=response.headers.get("x-amzn-requestid"),
        )

    async def get_submissions(self, cik: str | int) -> SecJsonResponse:
        return await self.get_json(SEC_SUBMISSIONS_PATH.format(cik=normalize_cik(cik)))

    async def get_company_facts(self, cik: str | int) -> SecJsonResponse:
        return await self.get_json(SEC_COMPANY_FACTS_PATH.format(cik=normalize_cik(cik)))
