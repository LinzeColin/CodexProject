from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


DEFAULT_INDUSTRY_RANK = 999
DEFAULT_INDUSTRY_NAME = "待研判行业"
DEFAULT_DOCUMENT_SINCE = "2025-01-01"


@dataclass(frozen=True)
class IndustryRule:
    rank: int
    name: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class IndustryConfig:
    version: str
    default_since: str
    rules: tuple[IndustryRule, ...]


def load_industry_config(path: str | Path | None = None) -> IndustryConfig:
    if path is None:
        return IndustryConfig("industry-default-empty", DEFAULT_DOCUMENT_SINCE, ())
    config_path = Path(path)
    if not config_path.exists():
        return IndustryConfig("industry-default-empty", DEFAULT_DOCUMENT_SINCE, ())
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    rules = tuple(
        IndustryRule(
            rank=int(item["rank"]),
            name=str(item["name"]),
            keywords=tuple(str(keyword) for keyword in item.get("keywords", [])),
        )
        for item in payload.get("industries", [])
    )
    return IndustryConfig(
        version=str(payload.get("version") or "industry-priority-v1"),
        default_since=str(payload.get("default_since") or DEFAULT_DOCUMENT_SINCE),
        rules=tuple(sorted(rules, key=lambda rule: rule.rank)),
    )


def classify_document_industry(
    document: Mapping[str, Any],
    config: IndustryConfig,
) -> tuple[int, str]:
    text = _document_title_text(document)
    for rule in config.rules:
        if any(_keyword_matches(text, keyword) for keyword in rule.keywords):
            return rule.rank, rule.name
    return DEFAULT_INDUSTRY_RANK, DEFAULT_INDUSTRY_NAME


def document_sort_time(document: Mapping[str, Any]) -> str | None:
    value = document.get("published_date") or _inferred_policy_date(document) or document.get("discovered_at")
    return str(value) if value else None


def document_is_since(document: Mapping[str, Any], since: str | None) -> bool:
    if not since:
        return True
    sort_time = document_sort_time(document)
    if not sort_time:
        return False
    return sort_time[:10] >= since


def _document_text(document: Mapping[str, Any]) -> str:
    return " ".join(
        str(document.get(key) or "")
        for key in ("title", "text_excerpt", "source_name", "canonical_url", "url")
    )


def _document_title_text(document: Mapping[str, Any]) -> str:
    return " ".join(
        str(document.get(key) or "")
        for key in ("title", "source_name", "canonical_url", "url")
    )


def _inferred_policy_date(document: Mapping[str, Any]) -> str | None:
    text = _document_title_text(document)
    plan_years = (
        (("第十一个五年", "十一五"), "2006-01-01"),
        (("第十二个五年", "十二五"), "2011-01-01"),
        (("第十三个五年", "十三五"), "2016-01-01"),
        (("第十四个五年", "十四五"), "2021-01-01"),
        (("第十五个五年", "十五五"), "2026-01-01"),
    )
    for markers, date_value in plan_years:
        if any(marker in text for marker in markers):
            return date_value
    year_match = re.search(r"(20\d{2})年", text)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return None


def _keyword_matches(text: str, keyword: str) -> bool:
    if not keyword:
        return False
    if keyword.upper() == "AI":
        return bool(re.search(r"(?<![A-Za-z])AI(?![A-Za-z])", text, re.IGNORECASE))
    return keyword in text
