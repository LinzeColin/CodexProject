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
SCIENCE_RSS_URL = "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science"
SCIENCE_TABLE_OF_CONTENTS_URL = "https://www.science.org/loi/science?af=R"
LANCET_CURRENT_RSS_URL = "https://www.thelancet.com/rssfeed/lancet_current.xml"
LANCET_ONLINE_FIRST_RSS_URL = "https://www.thelancet.com/rssfeed/lancet_online.xml"
LANCET_ONLINE_FIRST_PAGE_URL = "https://www.thelancet.com/journals/lancet/issues"
LANCET_PUBMED_DOI_QUERY_URL_TEMPLATE = "https://pubmed.ncbi.nlm.nih.gov/?term={doi}%5Bdoi%5D"
TOP_JOURNAL_MAX_CANARY_RECORDS = 10
SUPPORTED_TOP_JOURNALS = ("nature", "science", "lancet")
SCIENCE_ACCEPTED_ARTICLE_TYPES = ("research_article", "report", "review", "perspective")
LANCET_ACCEPTED_ARTICLE_TYPES = (
    "article",
    "review",
    "seminar",
    "series",
    "commission",
    "clinical_rounds",
    "viewpoint",
    "perspective",
)
_SCIENCE_ARTICLE_TYPE_MAP = {
    "research article": "research_article",
    "report": "report",
    "review": "review",
    "perspective": "perspective",
}
_LANCET_ARTICLE_TYPE_MAP = {
    "article": "article",
    "articles": "article",
    "review": "review",
    "seminar": "seminar",
    "series": "series",
    "commission": "commission",
    "commissions": "commission",
    "clinical rounds": "clinical_rounds",
    "viewpoint": "viewpoint",
    "perspective": "perspective",
    "perspectives": "perspective",
}
_JOURNAL_DISPLAY_NAMES = {
    "nature": "Nature",
    "science": "Science",
    "lancet": "The Lancet",
}

RSS_NS = "{http://purl.org/rss/1.0/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
PRISM_NS = "{http://prismstandard.org/namespaces/basic/2.0/}"
PRISM_12_NS = "{http://prismstandard.org/namespaces/1.2/basic/}"


class TopJournalAdapterError(ValueError):
    """Raised when public top-journal metadata cannot be converted safely."""


@dataclass(frozen=True)
class TopJournalQuery:
    journal: str = "nature"


TopJournalFetcher = Callable[[TopJournalQuery], str]


def normalize_top_journal(journal: str) -> str:
    normalized = str(journal or "").strip().lower()
    if normalized not in SUPPORTED_TOP_JOURNALS:
        raise TopJournalAdapterError("journal must be one of: " + ", ".join(SUPPORTED_TOP_JOURNALS))
    return normalized


def build_top_journal_rss_url(query: TopJournalQuery) -> str:
    journal = normalize_top_journal(query.journal)
    if journal == "nature":
        return NATURE_RSS_URL
    if journal == "science":
        return SCIENCE_RSS_URL
    if journal == "lancet":
        return LANCET_ONLINE_FIRST_RSS_URL
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
            "official_research_page": _official_top_journal_page(source_journal),
        },
        "source_policy": _source_policy(max_records=max_records, journal=source_journal),
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
        errors.append("top-journal source batch journal must be one of: " + ", ".join(SUPPORTED_TOP_JOURNALS))
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
        if policy.get("undocumented_endpoint_allowed") is not False:
            errors.append("top-journal ingest must not use undocumented endpoints")
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
        if journal and item.get("source_adapter") != f"{journal}.rss.v1":
            errors.append(f"source_items[{index}].source_adapter must be {journal}.rss.v1")
        top_journal = item.get("metadata", {}).get("top_journal", {}) if isinstance(item.get("metadata"), Mapping) else {}
        if isinstance(top_journal, Mapping):
            if journal and top_journal.get("journal_id") != journal:
                errors.append(f"source_items[{index}].metadata.top_journal.journal_id must be {journal}")
            if journal == "science" and top_journal.get("article_type") not in SCIENCE_ACCEPTED_ARTICLE_TYPES:
                errors.append(f"source_items[{index}] Science article_type must be one of {list(SCIENCE_ACCEPTED_ARTICLE_TYPES)}")
            if journal == "lancet":
                if top_journal.get("article_type") not in LANCET_ACCEPTED_ARTICLE_TYPES:
                    errors.append(f"source_items[{index}] Lancet article_type must be one of {list(LANCET_ACCEPTED_ARTICLE_TYPES)}")
                if top_journal.get("index_alignment_gate") != "pass":
                    errors.append(f"source_items[{index}] Lancet index_alignment_gate must pass")
                medical_indexing = top_journal.get("medical_indexing")
                if not isinstance(medical_indexing, Mapping):
                    errors.append(f"source_items[{index}] Lancet medical_indexing must be an object")
                else:
                    if medical_indexing.get("pubmed_relation_gate") not in {"doi_query_ready", "pmid_present"}:
                        errors.append(f"source_items[{index}] Lancet pubmed_relation_gate must be doi_query_ready or pmid_present")
                    query_url = str(medical_indexing.get("pubmed_doi_query_url") or "")
                    if "pubmed.ncbi.nlm.nih.gov" not in query_url or "%5Bdoi%5D" not in query_url:
                        errors.append(f"source_items[{index}] Lancet PubMed DOI query URL is required")
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
    article_id = _top_journal_article_id(node, journal=journal, link=link)
    if not article_id:
        return None
    title = _clean_text(_child_text(node, f"{RSS_NS}title"))
    if not title:
        raise TopJournalAdapterError(f"{journal} RSS item {article_id} missing title")
    article_type_raw = _top_journal_article_type_raw(node, journal=journal, title=title)
    article_type = _top_journal_article_type(journal=journal, raw_type=article_type_raw)
    if not article_type:
        return None
    description = _clean_text(_child_text(node, f"{RSS_NS}description"))
    summary = description or title
    publication_date = _clean_text(
        _child_text_any(node, (f"{PRISM_NS}publicationDate", f"{PRISM_12_NS}publicationDate", f"{DC_NS}date"))
    )
    authors = [_clean_text(author.text or "") for author in node.findall(f"{DC_NS}creator") if _clean_text(author.text or "")]
    stable_id = article_id.lower()
    source_id = f"{journal}:{stable_id}"
    canonical_document_id = f"{journal}:{stable_id}"
    display_name = _JOURNAL_DISPLAY_NAMES[journal]
    official_page = _official_top_journal_page(journal)
    metadata = {
        "top_journal": {
            "journal": display_name,
            "journal_id": journal,
            "article_id": stable_id,
            "article_family": f"{journal}_main_journal",
            "article_type": article_type,
            "article_type_raw": article_type_raw,
            "publication_date": publication_date,
            "summary": summary,
            "summary_fallback": "rss_title" if not description else "rss_description",
            "authors": authors,
            "rss_url": request_url or build_top_journal_rss_url(TopJournalQuery(journal=journal)),
            "official_research_page": official_page,
        },
        "identity": {
            "canonical_document_id": canonical_document_id,
            "source_family": "top_journal",
        },
    }
    if journal == "lancet":
        metadata["top_journal"].update(_lancet_index_metadata(article_id, link))
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
            {"ref_id": "metadata", "ref_type": "rss", "uri": request_url or build_top_journal_rss_url(TopJournalQuery(journal=journal))},
            {"ref_id": "article_landing_page", "ref_type": "html", "uri": link},
        ],
        "license": {
            "status": "rights_reserved_metadata_and_link_only",
            "usage": "metadata_and_link_only_no_fulltext_download",
        },
        "evidence_refs": [link, request_url or build_top_journal_rss_url(TopJournalQuery(journal=journal)), official_page],
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
            "official_research_page": _official_top_journal_page(normalized_journal),
        },
        "source_policy": _source_policy(max_records=TOP_JOURNAL_MAX_CANARY_RECORDS, journal=normalized_journal),
        "seen_source_ids": [],
        "duplicate_source_ids": [],
        "source_items": source_items or [],
        "new_items": [],
        "new_item_count": 0,
        "blocking_reasons": [reason],
    }


def _source_policy(*, max_records: int, journal: str = "nature") -> dict[str, Any]:
    policy = {
        "network_fetch_enabled": True,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "bulk_harvest_enabled": False,
        "paywall_bypass_allowed": False,
        "undocumented_endpoint_allowed": False,
        "max_records_per_call": int(max_records),
        "official_rss_url": _official_top_journal_rss_url(journal),
        "official_research_page": _official_top_journal_page(journal),
    }
    if journal == "lancet":
        policy.update(
            {
                "official_current_issue_rss_url": LANCET_CURRENT_RSS_URL,
                "pubmed_lookup_enabled": False,
                "pubmed_relation_mode": "doi_query_reference_only",
                "tdm_policy_url": "https://www.elsevier.com/tdm/tdmrep-policy.json",
                "tdm_reservation_observed": True,
            }
        )
    return policy


def _child_text(node: ET.Element, path: str) -> str:
    child = node.find(path)
    return "" if child is None or child.text is None else child.text


def _child_text_any(node: ET.Element, paths: Iterable[str]) -> str:
    for path in paths:
        text = _child_text(node, path)
        if text:
            return text
    return ""


def _nature_article_id(url: str) -> str:
    match = re.search(r"/articles/(s41586-[A-Za-z0-9._-]+)", url)
    return match.group(1).lower() if match else ""


def _top_journal_article_id(node: ET.Element, *, journal: str, link: str) -> str:
    if journal == "nature":
        return _nature_article_id(link)
    if journal == "science":
        return _science_article_doi(node, link=link)
    if journal == "lancet":
        return _lancet_article_doi(node, link=link)
    return ""


def _science_article_doi(node: ET.Element, *, link: str) -> str:
    identifier = _clean_text(_child_text(node, f"{DC_NS}identifier"))
    match = re.search(r"doi:(10\.1126/science\.[A-Za-z0-9._-]+)", identifier, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower()
    match = re.search(r"/doi/(?:abs|full)/(10\.1126/science\.[A-Za-z0-9._-]+)", link, flags=re.IGNORECASE)
    return match.group(1).lower() if match else ""


def _lancet_article_doi(node: ET.Element, *, link: str) -> str:
    identifier = _clean_text(_child_text(node, f"{DC_NS}identifier") or _child_text_any(node, (f"{PRISM_12_NS}doi", f"{PRISM_NS}doi")))
    match = re.search(r"(10\.1016/S0140-6736\([0-9]{2}\)[A-Za-z0-9-]+)", identifier, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower()
    match = re.search(r"/article/(PIIS0140-6736\([0-9]{2}\)[A-Za-z0-9-]+)/", link, flags=re.IGNORECASE)
    return f"10.1016/{match.group(1)[3:]}".lower() if match else ""


def _top_journal_article_type_raw(node: ET.Element, *, journal: str, title: str) -> str:
    if journal == "lancet":
        section = _clean_text(_child_text_any(node, (f"{PRISM_12_NS}section", f"{PRISM_NS}section")))
        if section:
            return section
        match = re.match(r"\[([^\]]+)\]", title)
        return _clean_text(match.group(1)) if match else ""
    return _clean_text(_child_text(node, f"{DC_NS}type"))


def _top_journal_article_type(*, journal: str, raw_type: str) -> str:
    if journal == "nature":
        return "research_article_feed_item"
    if journal == "science":
        return _SCIENCE_ARTICLE_TYPE_MAP.get(_clean_text(raw_type).lower(), "")
    if journal == "lancet":
        return _LANCET_ARTICLE_TYPE_MAP.get(_clean_text(raw_type).lower(), "")
    return ""


def _official_top_journal_rss_url(journal: str) -> str:
    if journal == "nature":
        return NATURE_RSS_URL
    if journal == "science":
        return SCIENCE_RSS_URL
    if journal == "lancet":
        return LANCET_ONLINE_FIRST_RSS_URL
    return ""


def _official_top_journal_page(journal: str) -> str:
    if journal == "nature":
        return NATURE_RESEARCH_ARTICLES_URL
    if journal == "science":
        return SCIENCE_TABLE_OF_CONTENTS_URL
    if journal == "lancet":
        return LANCET_ONLINE_FIRST_PAGE_URL
    return ""


def _lancet_index_metadata(doi: str, link: str) -> dict[str, Any]:
    pubmed_url = LANCET_PUBMED_DOI_QUERY_URL_TEMPLATE.format(doi=doi)
    pmid = ""
    return {
        "index_alignment_gate": "pass",
        "license_gate": "metadata_only_pass",
        "online_first_rss_url": LANCET_ONLINE_FIRST_RSS_URL,
        "current_issue_rss_url": LANCET_CURRENT_RSS_URL,
        "landing_page_relation": "lancet_article_landing_page" if "/journals/lancet/article/" in link else "unknown",
        "medical_indexing": {
            "pubmed_relation_gate": "pmid_present" if pmid else "doi_query_ready",
            "pubmed_lookup_performed": False,
            "pmid": pmid,
            "pubmed_doi_query_url": pubmed_url,
        },
    }


def _canonical_document_id(item: Mapping[str, Any]) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
    identity = metadata.get("identity") if isinstance(metadata.get("identity"), Mapping) else {}
    return str(identity.get("canonical_document_id") or item.get("source_id") or stable_content_hash(dict(item))[:16])


def _clean_text(value: str) -> str:
    return " ".join(str(value or "").split())
