"""Top-journal public metadata adapter for Stage 2 shadow runs.

The adapter uses official public RSS metadata only. It never downloads PDFs,
full text, media, or paywalled content.
"""

from __future__ import annotations

import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .contracts import stable_content_hash, validate_source_item


TOP_JOURNAL_INGEST_MODEL_ID = "adp-stage2-top-journal-ingest-v1"
NATURE_RSS_URL = "https://www.nature.com/nature.rss"
NATURE_RESEARCH_ARTICLES_URL = "https://www.nature.com/nature/research-articles"
TOP_JOURNAL_MAX_CANARY_RECORDS = 10
SUPPORTED_TOP_JOURNALS = ("nature",)

RSS_NS = "{http://purl.org/rss/1.0/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
PRISM_NS = "{http://prismstandard.org/namespaces/basic/2.0/}"


class TopJournalAdapterError(ValueError):
    """Raised when public top-journal metadata cannot be converted safely."""


@dataclass(frozen=True)
class TopJournalQuery:
    journal: str = "nature"


TopJournalFetcher = Callable[[TopJournalQuery], str]


def normalize_top_journal(journal: str) -> str:
    normalized = str(journal or "").strip().lower()
    if normalized not in SUPPORTED_TOP_JOURNALS:
        raise TopJournalAdapterError("journal must be nature")
    return normalized


def build_top_journal_rss_url(query: TopJournalQuery) -> str:
    journal = normalize_top_journal(query.journal)
    if journal == "nature":
        return NATURE_RSS_URL
    raise TopJournalAdapterError("unsupported top journal")


def fetch_top_journal_rss(
    query: TopJournalQuery,
    *,
    timeout: float = 20.0,
    user_agent: str = "arXiv Daily Push/0.24",
) -> str:
    request = urllib.request.Request(build_top_journal_rss_url(query), headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch_top_journal_rss_with_curl(query: TopJournalQuery, *, timeout_seconds: int = 30) -> str:
    url = build_top_journal_rss_url(query)
    result = subprocess.run(
        ["curl", "-fsSL", "--max-time", str(int(timeout_seconds)), url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "curl returned no output").strip().splitlines()
        raise RuntimeError(f"curl top-journal fetch failed: {detail[0] if detail else result.returncode}")
    if not result.stdout.strip():
        raise RuntimeError("curl top-journal fetch returned an empty response")
    return result.stdout


def parse_top_journal_rss(
    xml_text: str,
    *,
    journal: str,
    retrieved_at: str,
    request_url: str = "",
    max_records: int | None = None,
) -> list[dict[str, Any]]:
    source_journal = normalize_top_journal(journal)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise TopJournalAdapterError(f"Invalid top-journal RSS XML: {exc}") from exc
    limit = TOP_JOURNAL_MAX_CANARY_RECORDS if max_records is None else int(max_records)
    if limit < 0:
        raise TopJournalAdapterError("max_records must be >= 0")
    items: list[dict[str, Any]] = []
    for node in root.findall(f".//{RSS_NS}item"):
        item = _rss_item_to_source_item(node, journal=source_journal, retrieved_at=retrieved_at, request_url=request_url)
        if item is not None:
            items.append(item)
        if len(items) >= limit:
            break
    return items


def ingest_latest_top_journal(
    *,
    journal: str,
    generated_at: str,
    max_records: int = TOP_JOURNAL_MAX_CANARY_RECORDS,
    seen_source_ids: Iterable[str] | None = None,
    fetcher: TopJournalFetcher | None = None,
) -> dict[str, Any]:
    """Fetch one small official RSS metadata window and return unseen SourceItems."""

    seen = {str(item) for item in (seen_source_ids or []) if str(item)}
    request_url = ""
    try:
        source_journal = normalize_top_journal(journal)
        if max_records < 0 or max_records > TOP_JOURNAL_MAX_CANARY_RECORDS:
            raise TopJournalAdapterError(f"max_records must be between 0 and {TOP_JOURNAL_MAX_CANARY_RECORDS}")
        query = TopJournalQuery(journal=source_journal)
        request_url = build_top_journal_rss_url(query)
        xml_text = (fetcher or fetch_top_journal_rss)(query)
        source_items = parse_top_journal_rss(
            xml_text,
            journal=source_journal,
            retrieved_at=generated_at,
            request_url=request_url,
            max_records=max_records,
        )
    except Exception as exc:  # noqa: BLE001 - operational boundary must fail closed.
        return _blocked_batch(
            journal=str(journal or ""),
            generated_at=generated_at,
            request_url=request_url,
            reason=f"top-journal ingest failed: {exc}",
        )
    invalid = [
        {"source_id": item.get("source_id", ""), "errors": validate_source_item(item)}
        for item in source_items
        if validate_source_item(item)
    ]
    if invalid:
        return _blocked_batch(
            journal=source_journal,
            generated_at=generated_at,
            request_url=request_url,
            reason=f"top-journal ingest produced invalid SourceItems: {invalid[0]['source_id']}",
            source_items=source_items,
        )
    duplicate_ids = [item["source_id"] for item in source_items if item["source_id"] in seen]
    new_items = [item for item in source_items if item["source_id"] not in seen]
    terminal_status = "new_records" if new_items else "duplicate_or_no_update" if source_items else "no_update"
    return {
        "ingest_id": f"source-ingest:{source_journal}-rss-latest",
        "model_id": TOP_JOURNAL_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": f"{source_journal}.rss.v1",
        "generated_at": generated_at,
        "status": "pass",
        "terminal_status": terminal_status,
        "journal": source_journal,
        "request": {
            "url": request_url,
            "max_records": max_records,
            "official_research_page": NATURE_RESEARCH_ARTICLES_URL if source_journal == "nature" else "",
        },
        "source_policy": _source_policy(max_records=max_records),
        "seen_source_ids": sorted(seen),
        "duplicate_source_ids": duplicate_ids,
        "source_items": source_items,
        "new_items": new_items,
        "new_item_count": len(new_items),
        "blocking_reasons": [],
    }


def validate_top_journal_source_batch(batch: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if batch.get("model_id") != TOP_JOURNAL_INGEST_MODEL_ID:
        errors.append("top-journal source batch model_id must be adp-stage2-top-journal-ingest-v1")
    status = batch.get("status")
    if status not in {"pass", "blocked"}:
        errors.append("top-journal source batch status must be pass or blocked")
    journal = str(batch.get("journal") or "")
    try:
        normalize_top_journal(journal)
    except TopJournalAdapterError:
        errors.append("top-journal source batch journal must be nature")
    if status == "blocked" and not batch.get("blocking_reasons"):
        errors.append("blocked top-journal source batch requires blocking_reasons")
    policy = batch.get("source_policy")
    if not isinstance(policy, Mapping):
        errors.append("top-journal source batch source_policy must be an object")
    else:
        if policy.get("pdf_download_enabled") is not False:
            errors.append("top-journal ingest must not download PDFs")
        if policy.get("full_text_download_enabled") is not False:
            errors.append("top-journal ingest must not download full text")
        if policy.get("bulk_harvest_enabled") is not False:
            errors.append("top-journal ingest must not perform bulk harvesting")
        if policy.get("paywall_bypass_allowed") is not False:
            errors.append("top-journal ingest must not bypass paywalls")
        if int(policy.get("max_records_per_call") or 0) > TOP_JOURNAL_MAX_CANARY_RECORDS:
            errors.append(f"top-journal max_records_per_call must be <= {TOP_JOURNAL_MAX_CANARY_RECORDS}")
    seen_source_ids: set[str] = set()
    seen_canonical_ids: set[str] = set()
    for index, item in enumerate(batch.get("source_items") or []):
        if not isinstance(item, Mapping):
            errors.append(f"source_items[{index}] must be an object")
            continue
        errors.extend(f"source_items[{index}]: {error}" for error in validate_source_item(item))
        source_id = str(item.get("source_id") or "")
        if source_id in seen_source_ids:
            errors.append(f"duplicate source_id in top-journal batch: {source_id}")
        seen_source_ids.add(source_id)
        canonical_id = _canonical_document_id(item)
        if canonical_id in seen_canonical_ids:
            errors.append(f"duplicate canonical_document_id in top-journal batch: {canonical_id}")
        seen_canonical_ids.add(canonical_id)
    for index, item in enumerate(batch.get("new_items") or []):
        if isinstance(item, Mapping):
            errors.extend(f"new_items[{index}]: {error}" for error in validate_source_item(item))
        else:
            errors.append(f"new_items[{index}] must be an object")
    return errors


def _rss_item_to_source_item(
    node: ET.Element,
    *,
    journal: str,
    retrieved_at: str,
    request_url: str,
) -> dict[str, Any] | None:
    link = _clean_text(_child_text(node, f"{RSS_NS}link"))
    article_id = _nature_article_id(link)
    if not article_id:
        return None
    title = _clean_text(_child_text(node, f"{RSS_NS}title"))
    if not title:
        raise TopJournalAdapterError(f"{journal} RSS item {article_id} missing title")
    description = _clean_text(_child_text(node, f"{RSS_NS}description"))
    summary = description or title
    publication_date = _clean_text(_child_text(node, f"{PRISM_NS}publicationDate") or _child_text(node, f"{DC_NS}date"))
    authors = [_clean_text(author.text or "") for author in node.findall(f"{DC_NS}creator") if _clean_text(author.text or "")]
    stable_id = article_id.lower()
    source_id = f"{journal}:{stable_id}"
    canonical_document_id = f"{journal}:{stable_id}"
    metadata = {
        "top_journal": {
            "journal": "Nature",
            "journal_id": journal,
            "article_id": stable_id,
            "article_family": "nature_main_journal",
            "article_type": "research_article_feed_item",
            "publication_date": publication_date,
            "summary": summary,
            "summary_fallback": "rss_title" if not description else "rss_description",
            "authors": authors,
            "rss_url": request_url or NATURE_RSS_URL,
            "official_research_page": NATURE_RESEARCH_ARTICLES_URL,
        },
        "identity": {
            "canonical_document_id": canonical_document_id,
            "source_family": "top_journal",
        },
    }
    return {
        "source_id": source_id,
        "source_type": "rss",
        "source_adapter": f"{journal}.rss.v1",
        "stable_id": stable_id,
        "title": title,
        "retrieved_at": retrieved_at,
        "canonical_url": link,
        "metadata": metadata,
        "content_refs": [
            {"ref_id": "metadata", "ref_type": "rss", "uri": request_url or NATURE_RSS_URL},
            {"ref_id": "article_landing_page", "ref_type": "html", "uri": link},
        ],
        "license": {
            "status": "rights_reserved_metadata_and_link_only",
            "usage": "metadata_and_link_only_no_fulltext_download",
        },
        "evidence_refs": [link, request_url or NATURE_RSS_URL, NATURE_RESEARCH_ARTICLES_URL],
    }


def _blocked_batch(
    *,
    journal: str,
    generated_at: str,
    request_url: str,
    reason: str,
    source_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    normalized_journal = journal.lower() if journal.lower() in SUPPORTED_TOP_JOURNALS else "unknown"
    return {
        "ingest_id": f"source-ingest:{normalized_journal}-rss-latest",
        "model_id": TOP_JOURNAL_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": f"{normalized_journal}.rss.v1",
        "generated_at": generated_at,
        "status": "blocked",
        "terminal_status": "blocked",
        "journal": normalized_journal,
        "request": {
            "url": request_url,
            "max_records": TOP_JOURNAL_MAX_CANARY_RECORDS,
            "official_research_page": NATURE_RESEARCH_ARTICLES_URL if normalized_journal == "nature" else "",
        },
        "source_policy": _source_policy(max_records=TOP_JOURNAL_MAX_CANARY_RECORDS),
        "seen_source_ids": [],
        "duplicate_source_ids": [],
        "source_items": source_items or [],
        "new_items": [],
        "new_item_count": 0,
        "blocking_reasons": [reason],
    }


def _source_policy(*, max_records: int) -> dict[str, Any]:
    return {
        "network_fetch_enabled": True,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "bulk_harvest_enabled": False,
        "paywall_bypass_allowed": False,
        "undocumented_endpoint_allowed": False,
        "max_records_per_call": int(max_records),
        "official_rss_url": NATURE_RSS_URL,
        "official_research_page": NATURE_RESEARCH_ARTICLES_URL,
    }


def _child_text(node: ET.Element, path: str) -> str:
    child = node.find(path)
    return "" if child is None or child.text is None else child.text


def _nature_article_id(url: str) -> str:
    match = re.search(r"/articles/(s41586-[A-Za-z0-9._-]+)", url)
    return match.group(1).lower() if match else ""


def _canonical_document_id(item: Mapping[str, Any]) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
    identity = metadata.get("identity") if isinstance(metadata.get("identity"), Mapping) else {}
    return str(identity.get("canonical_document_id") or item.get("source_id") or stable_content_hash(dict(item))[:16])


def _clean_text(value: str) -> str:
    return " ".join(str(value or "").split())
