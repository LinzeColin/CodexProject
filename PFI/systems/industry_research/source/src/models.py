from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


ClaimType = Literal["fact", "inference", "opinion"]


@dataclass(frozen=True)
class Source:
    source_name: str
    source_url: str
    fetch_time: str
    data_version: str = "v1"


@dataclass(frozen=True)
class EvidenceClaim:
    claim_type: ClaimType
    text: str
    sources: list[Source] = field(default_factory=list)


@dataclass(frozen=True)
class CollectorResult:
    source_name: str
    source_url: str
    fetch_time: str
    raw_response: Any
    parsed_data: list[dict[str, Any]]
    status: str
    error_message: str = ""
    data_version: str = "v1"

    @classmethod
    def ok(
        cls,
        source_name: str,
        source_url: str,
        parsed_data: list[dict[str, Any]],
        raw_response: Any | None = None,
        data_version: str = "v1",
    ) -> "CollectorResult":
        return cls(
            source_name=source_name,
            source_url=source_url,
            fetch_time=datetime.now(timezone.utc).isoformat(),
            raw_response=raw_response if raw_response is not None else parsed_data,
            parsed_data=parsed_data,
            status="ok",
            data_version=data_version,
        )

    def source(self) -> Source:
        return Source(
            source_name=self.source_name,
            source_url=self.source_url,
            fetch_time=self.fetch_time,
            data_version=self.data_version,
        )
