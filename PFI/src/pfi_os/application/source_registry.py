from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pfi_os.application.operational_store import DataDomain, OperationalStore, SourceRecord


PRIVATE_DOMAINS = {DataDomain.PRIVATE_USER.value, DataDomain.PRIVATE_DERIVED.value, DataDomain.SECRET.value}


@dataclass(frozen=True)
class SourceRegistryRow:
    source_id: str
    domain: str
    source_type: str
    uri: str
    as_of: str
    evidence_class: str
    freshness: str
    title: str


class SourceRegistry:
    def __init__(self, store: OperationalStore | None = None):
        self.store = store or OperationalStore()

    def initialize(self) -> None:
        self.store.initialize()

    def register_source(self, record: SourceRecord) -> SourceRecord:
        return self.store.upsert_source(record)

    def rows(self, *, include_private_uri: bool = False, now: datetime | None = None) -> list[SourceRegistryRow]:
        records = self.store.table_rows("source_records")
        return self._rows_from_records(records, include_private_uri=include_private_uri, now=now)

    def point_in_time_rows(self, as_of: str, *, include_private_uri: bool = False, now: datetime | None = None) -> list[SourceRegistryRow]:
        records = self.store.point_in_time_sources(as_of)
        return self._rows_from_records(records, include_private_uri=include_private_uri, now=now)

    def _rows_from_records(
        self,
        records: list[dict[str, Any]],
        *,
        include_private_uri: bool,
        now: datetime | None,
    ) -> list[SourceRegistryRow]:
        return [
            SourceRegistryRow(
                source_id=str(row["source_id"]),
                domain=str(row["domain"]),
                source_type=str(row["source_type"]),
                uri=_safe_uri(str(row["uri"]), str(row["domain"]), include_private_uri=include_private_uri),
                as_of=str(row["as_of"]),
                evidence_class=str(row["evidence_class"]),
                freshness=_freshness(str(row["as_of"]), now=now),
                title=str(row["title"]),
            )
            for row in sorted(records, key=lambda item: (str(item["source_type"]), str(item["source_id"])))
        ]

    def summary(self, *, now: datetime | None = None) -> dict[str, Any]:
        rows = self.rows(now=now)
        domain_counts: dict[str, int] = {}
        freshness_counts: dict[str, int] = {}
        for row in rows:
            domain_counts[row.domain] = domain_counts.get(row.domain, 0) + 1
            freshness_counts[row.freshness] = freshness_counts.get(row.freshness, 0) + 1
        return {
            "schema": "PFIOSSourceRegistrySummaryV1",
            "source_count": len(rows),
            "domain_counts": domain_counts,
            "freshness_counts": freshness_counts,
            "rows": [row.__dict__ for row in rows],
            "private_uri_policy": "Private, private-derived, and secret source URIs are redacted by default.",
            "truth_role": "Operational source_records table is the source registry; ResearchBus remains compatibility events only.",
        }


def _safe_uri(uri: str, domain: str, *, include_private_uri: bool) -> str:
    if include_private_uri or domain not in PRIVATE_DOMAINS:
        return uri
    return "[redacted-private-uri]"


def _freshness(as_of: str, *, now: datetime | None = None) -> str:
    parsed = _parse_datetime(as_of)
    if parsed is None:
        return "Unknown"
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    age_seconds = (reference - parsed.astimezone(timezone.utc)).total_seconds()
    if age_seconds < 0:
        return "Future"
    if age_seconds <= 6 * 60 * 60:
        return "Fresh"
    if age_seconds <= 24 * 60 * 60:
        return "Delayed"
    if age_seconds <= 7 * 24 * 60 * 60:
        return "Stale"
    return "Expired"


def _parse_datetime(value: str) -> datetime | None:
    clean = str(value or "").strip()
    if not clean:
        return None
    if clean.endswith("Z"):
        clean = f"{clean[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(f"{clean}T00:00:00+00:00")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def pretty_source_registry_summary(summary: dict[str, Any]) -> str:
    return json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
