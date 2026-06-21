"""arXiv SourceAdapter.

Phase 3 keeps the adapter low pressure: it can build API URLs, fetch a small
Atom response when explicitly called, and parse Atom XML into generic
SourceItem dictionaries. Tests use local fixtures and never call the network.
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any


ARXIV_API_BASE_URL = "https://export.arxiv.org/api/query"
ARXIV_ACKNOWLEDGEMENT = "Thank you to arXiv for use of its open access interoperability."
ARXIV_NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}
MAX_PHASE3_RESULTS = 50


class ArxivAdapterError(ValueError):
    """Raised when an arXiv feed cannot be converted into SourceItems."""


@dataclass(frozen=True)
class ArxivQuery:
    search_query: str
    start: int = 0
    max_results: int = 10
    sort_by: str = "submittedDate"
    sort_order: str = "descending"


def build_query_url(query: ArxivQuery, base_url: str = ARXIV_API_BASE_URL) -> str:
    if query.start < 0:
        raise ArxivAdapterError("start must be >= 0")
    if query.max_results < 1 or query.max_results > MAX_PHASE3_RESULTS:
        raise ArxivAdapterError(f"max_results must be between 1 and {MAX_PHASE3_RESULTS}")
    params = {
        "search_query": query.search_query,
        "start": str(query.start),
        "max_results": str(query.max_results),
        "sortBy": query.sort_by,
        "sortOrder": query.sort_order,
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def fetch_atom(query: ArxivQuery, *, timeout: float = 20.0, user_agent: str = "arXiv Daily Push/0.3") -> str:
    request = urllib.request.Request(build_query_url(query), headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def parse_atom_feed(xml_text: str, *, retrieved_at: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ArxivAdapterError(f"Invalid Atom XML: {exc}") from exc
    entries = root.findall("atom:entry", ARXIV_NAMESPACES)
    items = [_entry_to_source_item(entry, retrieved_at=retrieved_at) for entry in entries]
    if items and any(item["metadata"]["arxiv"].get("api_error") for item in items):
        first = items[0]["metadata"]["arxiv"].get("api_error") or "arXiv API error"
        raise ArxivAdapterError(str(first))
    return items


def _entry_to_source_item(entry: ET.Element, *, retrieved_at: str) -> dict[str, Any]:
    title = _text(entry, "atom:title")
    summary = _normalize_space(_text(entry, "atom:summary"))
    entry_id = _text(entry, "atom:id")
    if title == "Error" or "/api/errors#" in entry_id:
        return _error_item(entry, retrieved_at=retrieved_at, entry_id=entry_id, title=title)
    versioned_id = _extract_arxiv_id(entry_id)
    stable_id = _strip_version(versioned_id)
    links = _links(entry)
    canonical_url = links.get("alternate") or f"https://arxiv.org/abs/{versioned_id}"
    pdf_url = links.get("pdf") or f"https://arxiv.org/pdf/{versioned_id}"
    primary_category = _primary_category(entry)
    categories = [category.get("term", "") for category in entry.findall("atom:category", ARXIV_NAMESPACES) if category.get("term")]
    return {
        "source_id": f"arxiv:{stable_id}",
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": stable_id,
        "title": _normalize_space(title),
        "retrieved_at": retrieved_at,
        "canonical_url": canonical_url,
        "metadata": {
            "arxiv": {
                "versioned_id": versioned_id,
                "primary_category": primary_category,
                "categories": categories,
                "published": _text(entry, "atom:published"),
                "updated": _text(entry, "atom:updated"),
                "authors": [_normalize_space(_text(author, "atom:name")) for author in entry.findall("atom:author", ARXIV_NAMESPACES)],
                "summary": summary,
                "comment": _text(entry, "arxiv:comment"),
                "journal_ref": _text(entry, "arxiv:journal_ref"),
                "doi": _text(entry, "arxiv:doi"),
                "acknowledgement": ARXIV_ACKNOWLEDGEMENT,
            }
        },
        "content_refs": [
            {"ref_id": "abstract", "ref_type": "html", "uri": canonical_url},
            {"ref_id": "pdf", "ref_type": "pdf", "uri": pdf_url},
        ],
        "license": {"status": "unknown", "usage": "private_learning_link_only"},
        "evidence_refs": [canonical_url],
    }


def _error_item(entry: ET.Element, *, retrieved_at: str, entry_id: str, title: str) -> dict[str, Any]:
    return {
        "source_id": "arxiv:error",
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": "error",
        "title": title or "Error",
        "retrieved_at": retrieved_at,
        "canonical_url": entry_id,
        "metadata": {"arxiv": {"api_error": _normalize_space(_text(entry, "atom:summary"))}},
        "content_refs": [{"ref_id": "error", "ref_type": "html", "uri": entry_id}],
        "license": {"status": "not_applicable", "usage": "error_record"},
        "evidence_refs": [entry_id],
    }


def _extract_arxiv_id(entry_id: str) -> str:
    value = entry_id.rstrip("/").rsplit("/", 1)[-1]
    if not value:
        raise ArxivAdapterError("entry id is missing arXiv identifier")
    return value


def _strip_version(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id)


def _text(element: ET.Element, path: str) -> str:
    found = element.find(path, ARXIV_NAMESPACES)
    return "" if found is None or found.text is None else found.text.strip()


def _normalize_space(value: str) -> str:
    return " ".join(value.split())


def _links(entry: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for link in entry.findall("atom:link", ARXIV_NAMESPACES):
        href = link.get("href")
        if not href:
            continue
        if link.get("rel") == "alternate":
            result["alternate"] = href
        if link.get("title") == "pdf":
            result["pdf"] = href
    return result


def _primary_category(entry: ET.Element) -> str:
    primary = entry.find("arxiv:primary_category", ARXIV_NAMESPACES)
    return "" if primary is None else str(primary.get("term") or "")
