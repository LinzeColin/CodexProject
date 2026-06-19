from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PublicSource:
    name: str
    url: str
    usage: str
    required_terms: List[str]
    validation_mode: str = "content_terms"


@dataclass(frozen=True)
class SourceStatus:
    name: str
    url: str
    usage: str
    ok: bool
    status_code: Optional[int]
    content_sha256: Optional[str]
    matched_terms: List[str]
    missing_terms: List[str]
    fetched_at: str
    error: Optional[str] = None


PUBLIC_SOURCES = [
    PublicSource(
        name="FIFA World Cup 2026 official schedule",
        url="https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums",
        usage="fixture, venue, host context",
        required_terms=["fifa", "manifest.webmanifest"],
        validation_mode="app_shell",
    ),
    PublicSource(
        name="FIFA qualified teams tracker",
        url="https://www.fifa.com/en/articles/world-cup-2026-who-has-qualified",
        usage="qualification context and confederation coverage",
        required_terms=["fifa", "manifest.webmanifest"],
        validation_mode="app_shell",
    ),
    PublicSource(
        name="FIFA/Coca-Cola men's world ranking",
        url="https://inside.fifa.com/fifa-world-ranking/men",
        usage="team-strength baseline and official ranking-change monitor",
        required_terms=["FIFA/Coca-Cola", "Men"],
    ),
]


def source_baseline() -> List[Dict]:
    return [
        {
            "name": source.name,
            "url": source.url,
            "usage": source.usage,
            "required_terms": source.required_terms,
            "validation_mode": source.validation_mode,
        }
        for source in PUBLIC_SOURCES
    ]


def fetch_url(url: str, timeout: int = 12) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 TAB FIFA research monitor"})
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, data.decode(charset, errors="ignore")
    except Exception as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        return fetch_url_with_curl(url, timeout)


def fetch_url_with_curl(url: str, timeout: int = 12) -> tuple[int, str]:
    result = subprocess.run(
        [
            "curl",
            "--location",
            "--silent",
            "--show-error",
            "--max-time",
            str(timeout),
            "--user-agent",
            "Mozilla/5.0 TAB FIFA research monitor",
            "--write-out",
            "\n%{http_code}",
            url,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"curl exited {result.returncode}")
    body, _, status_text = result.stdout.rpartition("\n")
    status_code = int(status_text.strip())
    return status_code, body


def audit_sources(
    sources: Iterable[PublicSource] = PUBLIC_SOURCES,
    fetcher: Callable[[str], tuple[int, str]] = fetch_url,
) -> Dict:
    statuses = []
    for source in sources:
        fetched_at = datetime.now(timezone.utc).isoformat()
        try:
            status_code, body = fetcher(source.url)
            body_lower = body.lower()
            matched = [term for term in source.required_terms if term.lower() in body_lower]
            missing = [term for term in source.required_terms if term.lower() not in body_lower]
            source_ok = 200 <= status_code < 300 and not missing
            statuses.append(
                SourceStatus(
                    name=source.name,
                    url=source.url,
                    usage=source.usage,
                    ok=source_ok,
                    status_code=status_code,
                    content_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    matched_terms=matched,
                    missing_terms=missing,
                    fetched_at=fetched_at,
                )
            )
        except Exception as exc:
            statuses.append(
                SourceStatus(
                    name=source.name,
                    url=source.url,
                    usage=source.usage,
                    ok=False,
                    status_code=None,
                    content_sha256=None,
                    matched_terms=[],
                    missing_terms=list(source.required_terms),
                    fetched_at=fetched_at,
                    error=str(exc),
                )
            )
    source_dicts = [asdict(status) for status in statuses]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(source_dicts),
        "ok_count": sum(1 for item in source_dicts if item["ok"]),
        "all_sources_ok": all(item["ok"] for item in source_dicts),
        "sources": source_dicts,
    }


def load_source_audit(path: Optional[Path]) -> Optional[Dict]:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text())
