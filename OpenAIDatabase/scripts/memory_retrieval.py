#!/usr/bin/env python3
"""Portable lexical routing and bounded GitHub conditional reads for memory."""

from __future__ import annotations

import email.utils
import re
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import timezone
from pathlib import PurePosixPath
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


TASK_ID = "TSK.OpenAIDatabase.PAM1.0015"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0015"
INDEX_SCHEMA_VERSION = "openai_database.memory_lexical_routing_index.v1"
ALGORITHM_VERSION = "nfkc_casefold_alias_scope_cjk_latin_ngram.v1"
GITHUB_API_VERSION = "2022-11-28"
TRANSIENT_GITHUB_STATUS_CODES = {408, 500, 502, 503, 504}
GIT_SHA_RE = re.compile(r"^[a-f0-9]{40,64}$")
REPOSITORY_PART_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
ASCII_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._:/+-][a-z0-9]+)*")
CJK_TOKEN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")


class RetrievalError(RuntimeError):
    """Stable fail-closed error code that never includes memory or credentials."""


def validate_retrieval_contract(config: Mapping[str, Any]) -> None:
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise RetrievalError("retrieval_contract_identity_invalid")
    if config.get("algorithm_version") != ALGORITHM_VERSION:
        raise RetrievalError("retrieval_contract_algorithm_invalid")
    expected_budget = {
        "default_discovery_object_count_max": 1,
        "indexed_fact_content_get_count_max": 2,
        "raw_expansion_content_get_count_max": 3,
        "recursive_full_tree_scan_count_max": 0,
    }
    if config.get("request_budget") != expected_budget:
        raise RetrievalError("retrieval_request_budget_invalid")
    expected_cache = {
        "commit_sha_required": True,
        "etag_required": True,
        "if_none_match_required_on_warm_read": True,
        "not_modified_status": 304,
        "max_attempts": 3,
        "max_retry_seconds": 120,
        "serial_requests": True,
    }
    if config.get("cache") != expected_cache:
        raise RetrievalError("retrieval_cache_contract_invalid")


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


def _ngrams(value: str, size: int) -> set[str]:
    return {value[index : index + size] for index in range(max(0, len(value) - size + 1))}


def lexical_terms(values: Sequence[Any]) -> list[str]:
    """Return deterministic terms that tolerate case, punctuation and CJK phrasing."""

    terms: set[str] = set()
    for raw in values:
        if raw is None:
            continue
        value = normalize_text(str(raw))
        if not value:
            continue
        if 2 <= len(value) <= 64:
            terms.add(value)
        for token in ASCII_TOKEN_RE.findall(value):
            if len(token) >= 2:
                terms.add(token)
            if len(token) >= 3:
                terms.update(_ngrams(token, 3))
        for token in CJK_TOKEN_RE.findall(value):
            if 2 <= len(token) <= 64:
                terms.add(token)
            terms.update(_ngrams(token, 2))
            if len(token) >= 3:
                terms.update(_ngrams(token, 3))
    return sorted(terms)


def supports_complete_substring_prefilter(query: str) -> bool:
    """Return true only when an indexed n-gram must cover every substring hit."""

    value = normalize_text(query)
    return any(len(token) >= 3 for token in ASCII_TOKEN_RE.findall(value)) or any(
        len(token) >= 2 for token in CJK_TOKEN_RE.findall(value)
    )


def _scope_value(scope: Any) -> str | None:
    if isinstance(scope, Mapping):
        scope_type = str(scope.get("type") or "").strip()
        scope_key = str(scope.get("key") or "").strip()
        if scope_type and scope_key:
            return f"{scope_type}:{scope_key}"
        return scope_type or None
    value = str(scope or "").strip()
    return value or None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise RetrievalError("lexical_list_field_invalid")
    return [str(item) for item in value]


def build_lexical_index(
    records: Sequence[Mapping[str, Any]],
    shard_by_record: Mapping[str, str],
    *,
    statuses: set[str] | None = {"active"},
) -> dict[str, Any]:
    """Build a compact deterministic routing index without a vector database."""

    postings: dict[str, set[str]] = defaultdict(set)
    indexed_records: dict[str, dict[str, str]] = {}
    seen: set[str] = set()
    for record in sorted(records, key=lambda row: str(row.get("id") or "")):
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            raise RetrievalError("lexical_record_id_invalid")
        seen.add(record_id)
        status = str(record.get("status") or "")
        if statuses is not None and status not in statuses:
            continue
        shard = shard_by_record.get(record_id)
        if not isinstance(shard, str) or not shard:
            raise RetrievalError("lexical_record_shard_missing")
        aliases = _string_list(record.get("aliases"))
        values: list[Any] = [
            record_id,
            record.get("memory_key"),
            record.get("statement"),
            record.get("kind"),
            *_string_list(record.get("tags")),
            *_string_list(record.get("negative_triggers")),
            *aliases,
        ]
        scope = _scope_value(record.get("scope"))
        if scope:
            values.append(scope)
            postings[f"scope={normalize_text(scope)}"].add(record_id)
        for alias in aliases:
            normalized_alias = normalize_text(alias)
            if normalized_alias:
                postings[f"alias={normalized_alias}"].add(record_id)
        for term in lexical_terms(values):
            postings[term].add(record_id)
        indexed_records[record_id] = {"shard": shard}

    rendered_postings = {
        term: sorted(record_ids)
        for term, record_ids in sorted(postings.items())
        if record_ids
    }
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "record_count": len(indexed_records),
        "posting_count": len(rendered_postings),
        "posting_membership_count": sum(len(ids) for ids in rendered_postings.values()),
        "records": dict(sorted(indexed_records.items())),
        "postings": rendered_postings,
    }


def route_lexical_index(
    index: Mapping[str, Any],
    query: str,
    *,
    aliases: Sequence[str] = (),
    scope: str | None = None,
    limit: int = 20,
    max_shards: int = 1,
) -> dict[str, Any]:
    """Route one indexed fact to at most one canonical shard by default."""

    if index.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise RetrievalError("lexical_index_schema_invalid")
    if not isinstance(limit, int) or not 1 <= limit <= 200:
        raise RetrievalError("lexical_route_limit_invalid")
    if not isinstance(max_shards, int) or not 1 <= max_shards <= 2:
        raise RetrievalError("lexical_route_shard_bound_invalid")
    postings = index.get("postings")
    records = index.get("records")
    if not isinstance(postings, Mapping) or not isinstance(records, Mapping):
        raise RetrievalError("lexical_index_shape_invalid")

    query_terms = lexical_terms([query, *aliases])
    alias_terms = [f"alias={normalize_text(alias)}" for alias in aliases if normalize_text(alias)]
    general_hits: set[str] = set()
    alias_hits: set[str] = set()
    scores: Counter[str] = Counter()
    matched_terms: list[str] = []
    for term in query_terms:
        ids = postings.get(term)
        if not isinstance(ids, list):
            continue
        matched_terms.append(term)
        for record_id in ids:
            if isinstance(record_id, str):
                general_hits.add(record_id)
                scores[record_id] += 1
    for term in alias_terms:
        ids = postings.get(term)
        if not isinstance(ids, list):
            continue
        matched_terms.append(term)
        for record_id in ids:
            if isinstance(record_id, str):
                alias_hits.add(record_id)
                scores[record_id] += 100

    candidates = alias_hits if alias_hits else general_hits
    scope_term = None
    if scope:
        scope_term = f"scope={normalize_text(scope)}"
        scoped = postings.get(scope_term)
        scoped_ids = {item for item in scoped or [] if isinstance(item, str)}
        candidates &= scoped_ids
        for record_id in candidates:
            scores[record_id] += 1000

    ranked = sorted(candidates, key=lambda record_id: (-scores[record_id], record_id))
    shard_scores: dict[str, tuple[int, int, str]] = {}
    for record_id in ranked:
        metadata = records.get(record_id)
        shard = metadata.get("shard") if isinstance(metadata, Mapping) else None
        if not isinstance(shard, str) or not shard:
            raise RetrievalError("lexical_index_record_invalid")
        maximum, total, _ = shard_scores.get(shard, (0, 0, shard))
        shard_scores[shard] = (max(maximum, scores[record_id]), total + scores[record_id], shard)
    selected_shards = [
        row[2]
        for row in sorted(shard_scores.values(), key=lambda row: (-row[0], -row[1], row[2]))[
            :max_shards
        ]
    ]
    selected_set = set(selected_shards)
    selected_ids = [
        record_id
        for record_id in ranked
        if isinstance(records.get(record_id), Mapping)
        and records[record_id].get("shard") in selected_set
    ][:limit]
    return {
        "record_ids": selected_ids,
        "shards": selected_shards,
        "candidate_count": len(candidates),
        "returned_count": len(selected_ids),
        "query_term_count": len(query_terms),
        "matched_term_count": len(set(matched_terms)),
        "scope_term": scope_term,
        "discovery_object_count": 1,
        "content_get_count": 1 + len(selected_shards),
        "recursive_full_tree_scan_count": 0,
    }


@dataclass(frozen=True)
class TransportResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True)
class CacheEntry:
    commit_sha: str
    etag: str
    body: bytes


Requester = Callable[[str, Mapping[str, str], int], TransportResponse]


def _safe_repository_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or path.as_posix() == "."
        or path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
    ):
        raise RetrievalError("github_path_invalid")
    return path.as_posix()


def _header_map(headers: Mapping[str, str]) -> dict[str, str]:
    return {str(key).casefold(): str(value) for key, value in headers.items()}


def _stdlib_requester(url: str, headers: Mapping[str, str], max_bytes: int) -> TransportResponse:
    request = Request(url, headers=dict(headers), method="GET")
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - URL is fixed to api.github.com.
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise RetrievalError("github_response_size_exceeded")
            return TransportResponse(int(response.status), dict(response.headers.items()), body)
    except HTTPError as exc:
        body = exc.read(min(max_bytes + 1, 64 * 1024))
        return TransportResponse(int(exc.code), dict(exc.headers.items()), body)


def _retry_delay_seconds(
    headers: Mapping[str, str],
    *,
    attempt: int,
    now_epoch: float,
) -> float:
    retry_after = headers.get("retry-after")
    if retry_after is not None:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            try:
                parsed = email.utils.parsedate_to_datetime(retry_after)
            except (TypeError, ValueError) as exc:
                raise RetrievalError("retry_after_invalid") from exc
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return max(0.0, parsed.timestamp() - now_epoch)
    if headers.get("x-ratelimit-remaining") == "0":
        try:
            return max(0.0, float(headers["x-ratelimit-reset"]) - now_epoch)
        except (KeyError, ValueError) as exc:
            raise RetrievalError("rate_limit_reset_invalid") from exc
    return float(60 * (2 ** max(0, attempt - 1)))


class ConditionalGitHubReader:
    """Serial, authenticated Contents API reader with commit-scoped ETag cache."""

    def __init__(
        self,
        authorization_provider: Callable[[], str],
        *,
        requester: Requester = _stdlib_requester,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        max_attempts: int = 3,
        max_retry_seconds: float = 120.0,
        max_response_bytes: int = 921_600,
        transient_retry_base_seconds: float = 1.0,
    ) -> None:
        if not callable(authorization_provider):
            raise RetrievalError("authorization_provider_required")
        if not 1 <= max_attempts <= 3:
            raise RetrievalError("github_max_attempts_invalid")
        if (
            max_retry_seconds <= 0
            or max_response_bytes <= 0
            or transient_retry_base_seconds <= 0
            or transient_retry_base_seconds > max_retry_seconds
        ):
            raise RetrievalError("github_reader_bound_invalid")
        self._authorization_provider = authorization_provider
        self._requester = requester
        self._sleeper = sleeper
        self._clock = clock
        self._max_attempts = max_attempts
        self._max_retry_seconds = max_retry_seconds
        self._max_response_bytes = max_response_bytes
        self._transient_retry_base_seconds = transient_retry_base_seconds
        self._cache: dict[tuple[str, str, str, str], CacheEntry] = {}

    def cache_commits(self, owner: str, repo: str, path: str) -> list[str]:
        prefix = (owner, repo, _safe_repository_path(path))
        return sorted(key[3] for key in self._cache if key[:3] == prefix)

    def read(self, owner: str, repo: str, path: str, commit_sha: str) -> dict[str, Any]:
        if not REPOSITORY_PART_RE.fullmatch(owner) or not REPOSITORY_PART_RE.fullmatch(repo):
            raise RetrievalError("github_repository_invalid")
        if GIT_SHA_RE.fullmatch(commit_sha) is None:
            raise RetrievalError("github_commit_sha_invalid")
        safe_path = _safe_repository_path(path)
        key = (owner, repo, safe_path, commit_sha)
        cached = self._cache.get(key)
        token = self._authorization_provider()
        if not isinstance(token, str) or not token.strip():
            raise RetrievalError("github_authorization_unavailable")
        token = token.strip()
        url = (
            f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/contents/"
            f"{quote(safe_path, safe='/')}?{urlencode({'ref': commit_sha})}"
        )
        headers = {
            "Accept": "application/vnd.github.raw+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "OpenAIDatabase-memory-retrieval",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        if cached is not None:
            headers["If-None-Match"] = cached.etag

        retry_delays: list[float] = []
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._requester(url, headers, self._max_response_bytes)
            except (TimeoutError, OSError) as exc:
                if attempt >= self._max_attempts:
                    raise RetrievalError("github_transient_retry_exhausted") from exc
                delay = self._transient_retry_base_seconds * (2 ** (attempt - 1))
                if sum(retry_delays) + delay > self._max_retry_seconds:
                    raise RetrievalError("github_retry_delay_exceeds_bound") from exc
                retry_delays.append(round(delay, 6))
                self._sleeper(delay)
                continue
            response_headers = _header_map(response.headers)
            if response.status == 304:
                if cached is None:
                    raise RetrievalError("github_304_without_cache")
                return {
                    "status": 304,
                    "body": cached.body,
                    "etag": cached.etag,
                    "commit_sha": commit_sha,
                    "cache_hit": True,
                    "request_count": attempt,
                    "transferred_bytes": 0,
                    "retry_delays_seconds": retry_delays,
                    "cache_entry_count": len(self._cache),
                }
            if response.status == 200:
                etag = response_headers.get("etag")
                if not etag:
                    raise RetrievalError("github_etag_missing")
                if len(response.body) > self._max_response_bytes:
                    raise RetrievalError("github_response_size_exceeded")
                for old_key in list(self._cache):
                    if old_key[:3] == key[:3] and old_key != key:
                        del self._cache[old_key]
                self._cache[key] = CacheEntry(commit_sha=commit_sha, etag=etag, body=response.body)
                return {
                    "status": 200,
                    "body": response.body,
                    "etag": etag,
                    "commit_sha": commit_sha,
                    "cache_hit": False,
                    "request_count": attempt,
                    "transferred_bytes": len(response.body),
                    "retry_delays_seconds": retry_delays,
                    "cache_entry_count": len(self._cache),
                }
            secondary_limit_message = (
                response.status == 403
                and b"secondary rate limit" in response.body[: 64 * 1024].lower()
            )
            rate_limited = response.status == 429 or secondary_limit_message or (
                response.status == 403
                and (
                    "retry-after" in response_headers
                    or response_headers.get("x-ratelimit-remaining") == "0"
                )
            )
            if not rate_limited:
                if response.status in TRANSIENT_GITHUB_STATUS_CODES:
                    if attempt >= self._max_attempts:
                        raise RetrievalError("github_transient_retry_exhausted")
                    delay = self._transient_retry_base_seconds * (2 ** (attempt - 1))
                    if sum(retry_delays) + delay > self._max_retry_seconds:
                        raise RetrievalError("github_retry_delay_exceeds_bound")
                    retry_delays.append(round(delay, 6))
                    self._sleeper(delay)
                    continue
                if response.status == 403:
                    raise RetrievalError("github_read_forbidden")
                if response.status == 404:
                    raise RetrievalError("github_read_not_found")
                raise RetrievalError("github_read_failed")
            if attempt >= self._max_attempts:
                raise RetrievalError("github_rate_limit_retry_exhausted")
            delay = _retry_delay_seconds(
                response_headers,
                attempt=attempt,
                now_epoch=self._clock(),
            )
            if sum(retry_delays) + delay > self._max_retry_seconds:
                raise RetrievalError("github_retry_delay_exceeds_bound")
            retry_delays.append(round(delay, 6))
            self._sleeper(delay)
        raise RetrievalError("github_read_unreachable")
