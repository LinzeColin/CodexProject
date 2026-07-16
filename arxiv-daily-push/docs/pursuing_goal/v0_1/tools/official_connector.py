#!/usr/bin/env python3
"""ADP V0.1 minimal Official Connector Interface / SDK (ADP-S3-P01-T031).

A tiny, dependency-free (stdlib only) connector kernel for China A0 central-government official
sources. It defines exactly the capabilities the pilot needs -- discover / fetch / verify /
normalize / attachments / cursor / health -- as a typed contract, plus an adapter registry. It has
NO business UI, NO knowledge graph, and NO new-platform coupling; a MockConnector exercises the full
chain deterministically, and a real stdlib HttpFetcher makes `fetch` a genuine HTTP GET for the real
A0 adapters (T034+). NOT_DEPLOYED: this is the SDK; nothing is wired into the worker or D1 yet.

Determinism: the contract test runs on the MockConnector + a local fixture (no network). A real
gov.cn fetch is exercised separately as a live, point-in-time evidence smoke, never in CI.
"""
from __future__ import annotations
import abc, dataclasses, hashlib, ssl, time, urllib.request, urllib.error
from typing import Optional

SCHEMA_VERSION = "adp.official_connector.v0_1"
USER_AGENT = "ADP-A0-connector/0.1 (+research; single-GET; respects robots)"

# --- typed contract -----------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class DiscoverItem:
    url: str
    title: str
    hint_date: Optional[str] = None      # YYYY-MM-DD if the listing exposes one

@dataclasses.dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    content_type: str
    body: bytes
    sha256: str
    fetched_at: str                      # ISO8601; supplied by caller (no clock inside the SDK)
    ok: bool

@dataclasses.dataclass(frozen=True)
class Attachment:
    url: str
    kind: str                            # pdf / doc / image / other
    sha256: Optional[str] = None

@dataclasses.dataclass(frozen=True)
class NormalizedDoc:
    source_id: str
    doc_id: str
    title: str
    doc_number: Optional[str]            # 文号 e.g. 国发〔2026〕1号
    doc_date: Optional[str]              # 成文/发布日期 YYYY-MM-DD
    status: Optional[str]               # 现行有效 / 已废止 / ...
    authority_level: str                # A0 / A1 / A2 / unofficial
    body_text: str
    attachments: tuple = ()
    canonical_hint: Optional[str] = None  # doi:/ttl: hint for T024 identity

@dataclasses.dataclass(frozen=True)
class VerifyResult:
    is_official: bool
    authority_level: str                # A0 / A1 / A2 / unofficial
    official_domain: bool
    reasons: tuple = ()

@dataclasses.dataclass(frozen=True)
class HealthResult:
    ok: bool
    checked: str                        # what was checked
    note: str = ""

@dataclasses.dataclass(frozen=True)
class Cursor:
    last_id: Optional[str] = None
    last_date: Optional[str] = None


class OfficialConnector(abc.ABC):
    """The minimal interface every A0 adapter implements. Exactly seven capabilities; nothing else."""
    source_id: str = "abstract"
    authority_level: str = "unofficial"

    @abc.abstractmethod
    def discover(self, cursor: Cursor) -> list: ...           # -> [DiscoverItem]
    @abc.abstractmethod
    def fetch(self, url: str, fetched_at: str) -> FetchResult: ...
    @abc.abstractmethod
    def verify(self, item: DiscoverItem, fetched: FetchResult) -> VerifyResult: ...
    @abc.abstractmethod
    def normalize(self, item: DiscoverItem, fetched: FetchResult) -> NormalizedDoc: ...
    @abc.abstractmethod
    def attachments(self, fetched: FetchResult) -> list: ...  # -> [Attachment]
    @abc.abstractmethod
    def cursor(self, docs: list) -> Cursor: ...               # advance the incremental cursor
    @abc.abstractmethod
    def health(self) -> HealthResult: ...


# --- real HTTP fetch (stdlib only; used by the real A0 adapters) --------------------------
class HttpFetcher:
    """A genuine HTTP GET with a UA, timeout, and a size cap. No third-party deps."""
    def __init__(self, timeout: float = 15.0, max_bytes: int = 5_000_000):
        self.timeout = timeout
        self.max_bytes = max_bytes

    def get(self, url: str, fetched_at: str) -> FetchResult:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                body = resp.read(self.max_bytes)
                status = resp.getcode()
                ctype = resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            body, status, ctype = b"", e.code, ""
        except Exception as e:                       # network/timeout/ssl -> ok=False, not a crash
            return FetchResult(url, 0, "", b"", "", fetched_at, False)
        return FetchResult(url, status, ctype, body,
                           hashlib.sha256(body).hexdigest(), fetched_at, 200 <= status < 300 and len(body) > 0)


# --- adapter registry ---------------------------------------------------------------------
class AdapterRegistry:
    """source_id -> connector instance. Adapters (T034+) register here; no dynamic import magic."""
    def __init__(self):
        self._by_id = {}

    def register(self, connector: OfficialConnector) -> None:
        if connector.source_id in self._by_id:
            raise ValueError(f"duplicate source_id: {connector.source_id}")
        self._by_id[connector.source_id] = connector

    def get(self, source_id: str) -> OfficialConnector:
        return self._by_id[source_id]

    def ids(self) -> list:
        return sorted(self._by_id)


def run_chain(connector: OfficialConnector, cursor: Cursor, fetched_at: str) -> dict:
    """Drive the full capability chain once: health -> discover -> (fetch -> verify -> normalize ->
    attachments)* -> cursor. Returns a structured trace. Pure orchestration; no I/O of its own."""
    health = connector.health()
    items = connector.discover(cursor)
    docs, verifies = [], []
    for it in items:
        fr = connector.fetch(it.url, fetched_at)
        vr = connector.verify(it, fr)
        nd = connector.normalize(it, fr)
        atts = connector.attachments(fr)
        nd = dataclasses.replace(nd, attachments=tuple(atts))
        docs.append(nd)
        verifies.append(vr)
    new_cursor = connector.cursor(docs)
    return {"schema_version": SCHEMA_VERSION, "source_id": connector.source_id,
            "health": health, "discovered": len(items), "docs": docs, "verifies": verifies,
            "cursor_before": cursor, "cursor_after": new_cursor}
