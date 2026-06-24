"""bioRxiv/medRxiv metadata adapter for Stage 2 source promotion.

The adapter uses the public CSHL API metadata endpoint only. It never downloads
PDFs, JATS XML, full text, media, or private/paywalled content.
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .contracts import stable_content_hash, validate_source_item


PREPRINT_INGEST_MODEL_ID = "adp-stage2-preprint-ingest-v1"
PREPRINT_DETAILS_BASE_URL = "https://api.biorxiv.org/details"
PREPRINT_API_DOC_URL = "https://api.biorxiv.org/"
PREPRINT_API_MAX_PAGE_SIZE = 100
PREPRINT_MAX_CANARY_RECORDS = 10
SUPPORTED_PREPRINT_SERVERS = ("biorxiv", "medrxiv")
PREPRINT_SERVER_HOSTS = {
    "biorxiv": "www.biorxiv.org",
    "medrxiv": "www.medrxiv.org",
}


class PreprintAdapterError(ValueError):
    """Raised when bioRxiv/medRxiv metadata cannot be converted safely."""


@dataclass(frozen=True)
class PreprintQuery:
    server: str
    interval: str = "1d"
    cursor: int = 0
    format: str = "json"


PreprintFetcher = Callable[[PreprintQuery], str]


def normalize_preprint_server(server: str) -> str:
    normalized = str(server or "").strip().lower()
    if normalized not in SUPPORTED_PREPRINT_SERVERS:
        raise PreprintAdapterError("server must be biorxiv or medrxiv")
    return normalized


def build_preprint_details_url(query: PreprintQuery, base_url: str = PREPRINT_DETAILS_BASE_URL) -> str:
    server = normalize_preprint_server(query.server)
    if int(query.cursor) < 0:
        raise PreprintAdapterError("cursor must be >= 0")
    if query.format != "json":
        raise PreprintAdapterError("Stage 2 preprint adapter supports JSON only")
    interval = str(query.interval or "").strip()
    if not _valid_interval(interval):
        raise PreprintAdapterError("interval must be Nd, N, DOI, or YYYY-MM-DD/YYYY-MM-DD")
    return "/".join(
        [
            base_url.rstrip("/"),
            urllib.parse.quote(server, safe=""),
            urllib.parse.quote(interval, safe="/."),
            str(int(query.cursor)),
            "json",
        ]
    )


def fetch_preprint_details(query: PreprintQuery, *, timeout: float = 20.0, user_agent: str = "arXiv Daily Push/0.24") -> str:
    request = urllib.request.Request(build_preprint_details_url(query), headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch_preprint_details_with_curl(query: PreprintQuery, *, timeout_seconds: int = 30) -> str:
    """Fetch public bioRxiv/medRxiv JSON through curl when Python CA trust is broken."""

    url = build_preprint_details_url(query)
    result = subprocess.run(
        ["curl", "-fsSL", "--max-time", str(int(timeout_seconds)), url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "curl returned no output").strip().splitlines()
        raise RuntimeError(f"curl preprint fetch failed: {detail[0] if detail else result.returncode}")
    if not result.stdout.strip():
        raise RuntimeError("curl preprint fetch returned an empty response")
    return result.stdout


def parse_preprint_details(
    json_text: str,
    *,
    server: str,
    retrieved_at: str,
    request_url: str = "",
    max_records: int | None = None,
) -> list[dict[str, Any]]:
    source_server = normalize_preprint_server(server)
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise PreprintAdapterError(f"Invalid preprint JSON: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise PreprintAdapterError("preprint API payload must be a JSON object")
    collection = payload.get("collection")
    if not isinstance(collection, list):
        raise PreprintAdapterError("preprint API payload missing collection array")
    limit = PREPRINT_API_MAX_PAGE_SIZE if max_records is None else int(max_records)
    if limit < 0:
        raise PreprintAdapterError("max_records must be >= 0")
    return [
        _record_to_source_item(record, server=source_server, retrieved_at=retrieved_at, request_url=request_url)
        for record in collection[:limit]
        if isinstance(record, Mapping)
    ]


def ingest_latest_preprints(
    *,
    server: str,
    generated_at: str,
    interval: str = "1d",
    cursor: int = 0,
    max_records: int = PREPRINT_MAX_CANARY_RECORDS,
    seen_source_ids: Iterable[str] | None = None,
    fetcher: PreprintFetcher | None = None,
) -> dict[str, Any]:
    """Fetch one small bioRxiv/medRxiv metadata window and return unseen SourceItems."""

    seen = {str(item) for item in (seen_source_ids or []) if str(item)}
    request_url = ""
    try:
        source_server = normalize_preprint_server(server)
        if max_records < 0 or max_records > PREPRINT_MAX_CANARY_RECORDS:
            raise PreprintAdapterError(f"max_records must be between 0 and {PREPRINT_MAX_CANARY_RECORDS}")
        query = PreprintQuery(server=source_server, interval=interval, cursor=cursor)
        request_url = build_preprint_details_url(query)
        json_text = (fetcher or fetch_preprint_details)(query)
        source_items = parse_preprint_details(
            json_text,
            server=source_server,
            retrieved_at=generated_at,
            request_url=request_url,
            max_records=max_records,
        )
    except Exception as exc:  # noqa: BLE001 - operational boundary must fail closed.
        return _blocked_batch(
            server=str(server or ""),
            generated_at=generated_at,
            interval=interval,
            cursor=cursor,
            request_url=request_url,
            reason=f"preprint ingest failed: {exc}",
        )

    invalid = [
        {"source_id": item.get("source_id", ""), "errors": validate_source_item(item)}
        for item in source_items
        if validate_source_item(item)
    ]
    if invalid:
        return _blocked_batch(
            server=source_server,
            generated_at=generated_at,
            interval=interval,
            cursor=cursor,
            request_url=request_url,
            reason=f"preprint ingest produced invalid SourceItems: {invalid[0]['source_id']}",
            source_items=source_items,
        )
    duplicate_ids = [item["source_id"] for item in source_items if item["source_id"] in seen]
    new_items = [item for item in source_items if item["source_id"] not in seen]
    terminal_status = "new_records" if new_items else "duplicate_or_no_update" if source_items else "no_update"
    return {
        "ingest_id": f"source-ingest:{source_server}-latest",
        "model_id": PREPRINT_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": f"{source_server}.details.v1",
        "generated_at": generated_at,
        "status": "pass",
        "terminal_status": terminal_status,
        "server": source_server,
        "request": {
            "base_url": PREPRINT_DETAILS_BASE_URL,
            "url": request_url,
            "interval": interval,
            "cursor": cursor,
            "max_records": max_records,
            "api_docs": PREPRINT_API_DOC_URL,
        },
        "source_policy": _source_policy(max_records=max_records),
        "seen_source_ids": sorted(seen),
        "duplicate_source_ids": duplicate_ids,
        "source_items": source_items,
        "new_items": new_items,
        "new_item_count": len(new_items),
        "blocking_reasons": [],
    }


def validate_preprint_source_batch(batch: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if batch.get("model_id") != PREPRINT_INGEST_MODEL_ID:
        errors.append("preprint source batch model_id must be adp-stage2-preprint-ingest-v1")
    status = batch.get("status")
    if status not in {"pass", "blocked"}:
        errors.append("preprint source batch status must be pass or blocked")
    server = str(batch.get("server") or "")
    try:
        normalize_preprint_server(server)
    except PreprintAdapterError:
        errors.append("preprint source batch server must be biorxiv or medrxiv")
    if status == "blocked" and not batch.get("blocking_reasons"):
        errors.append("blocked preprint source batch requires blocking_reasons")
    policy = batch.get("source_policy")
    if not isinstance(policy, Mapping):
        errors.append("preprint source batch source_policy must be an object")
    else:
        if policy.get("pdf_download_enabled") is not False:
            errors.append("preprint ingest must not download PDFs")
        if policy.get("full_text_download_enabled") is not False:
            errors.append("preprint ingest must not download full text")
        if policy.get("bulk_harvest_enabled") is not False:
            errors.append("preprint ingest must not perform bulk harvesting")
        if int(policy.get("max_records_per_call") or 0) > PREPRINT_MAX_CANARY_RECORDS:
            errors.append(f"preprint max_records_per_call must be <= {PREPRINT_MAX_CANARY_RECORDS}")
    seen_source_ids: set[str] = set()
    seen_canonical_ids: set[str] = set()
    for index, item in enumerate(batch.get("source_items") or []):
        if not isinstance(item, Mapping):
            errors.append(f"source_items[{index}] must be an object")
            continue
        errors.extend(f"source_items[{index}]: {error}" for error in validate_source_item(item))
        source_id = str(item.get("source_id") or "")
        if source_id in seen_source_ids:
            errors.append(f"duplicate source_id in preprint batch: {source_id}")
        seen_source_ids.add(source_id)
        canonical_id = _canonical_document_id(item)
        if canonical_id in seen_canonical_ids:
            errors.append(f"duplicate canonical_document_id in preprint batch: {canonical_id}")
        seen_canonical_ids.add(canonical_id)
    for index, item in enumerate(batch.get("new_items") or []):
        if isinstance(item, Mapping):
            errors.extend(f"new_items[{index}]: {error}" for error in validate_source_item(item))
        else:
            errors.append(f"new_items[{index}] must be an object")
    return errors


def _record_to_source_item(
    record: Mapping[str, Any],
    *,
    server: str,
    retrieved_at: str,
    request_url: str,
) -> dict[str, Any]:
    doi = _normalize_doi(str(record.get("doi") or ""))
    if not doi:
        raise PreprintAdapterError("preprint record missing DOI")
    title = _clean_text(str(record.get("title") or ""))
    if not title:
        raise PreprintAdapterError(f"preprint record {doi} missing title")
    record_server = normalize_preprint_server(str(record.get("server") or server))
    version = _normalize_version(record.get("version"))
    canonical_url = _preprint_content_url(record_server, doi=doi, version=version)
    abstract = _clean_text(str(record.get("abstract") or ""))
    license_text = _clean_text(str(record.get("license") or ""))
    category = _clean_text(str(record.get("category") or ""))
    stable_id = doi.lower()
    source_id = f"{record_server}:{_safe_doi(stable_id)}"
    canonical_document_id = f"doi:{stable_id}"
    metadata = {
        "preprint": {
            "server": record_server,
            "doi": stable_id,
            "version": version,
            "type": _clean_text(str(record.get("type") or "")),
            "date": _clean_text(str(record.get("date") or "")),
            "category": category,
            "abstract": abstract,
            "authors": _split_authors(record.get("authors")),
            "author_corresponding": _clean_text(str(record.get("author_corresponding") or "")),
            "author_corresponding_institution": _clean_text(str(record.get("author_corresponding_institution") or "")),
            "license": license_text,
            "published": _clean_text(str(record.get("published") or "")),
            "funding": record.get("funding") if isinstance(record.get("funding"), list) else [],
            "jats_xml_path": _clean_text(str(record.get("jats xml path") or record.get("jatsxml") or "")),
            "api_request_url": request_url,
            "api_docs": PREPRINT_API_DOC_URL,
        },
        "identity": {
            "canonical_doi": stable_id,
            "canonical_document_id": canonical_document_id,
            "source_family": "preprint",
        },
    }
    content_refs = [{"ref_id": "abstract", "ref_type": "html", "uri": canonical_url}]
    jats_path = metadata["preprint"]["jats_xml_path"]
    if jats_path:
        content_refs.append({"ref_id": "jats_xml_metadata_link", "ref_type": "jats_xml", "uri": jats_path})
    return {
        "source_id": source_id,
        "source_type": "preprint",
        "source_adapter": f"{record_server}.details.v1",
        "stable_id": stable_id,
        "title": title,
        "retrieved_at": retrieved_at,
        "canonical_url": canonical_url,
        "metadata": metadata,
        "content_refs": content_refs,
        "license": {
            "status": license_text or "unknown",
            "usage": "metadata_and_link_only_no_fulltext_download",
        },
        "evidence_refs": [canonical_url, request_url or PREPRINT_API_DOC_URL],
    }


def _blocked_batch(
    *,
    server: str,
    generated_at: str,
    interval: str,
    cursor: int,
    request_url: str,
    reason: str,
    source_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    normalized_server = server.lower() if server.lower() in SUPPORTED_PREPRINT_SERVERS else "unknown"
    return {
        "ingest_id": f"source-ingest:{normalized_server}-latest",
        "model_id": PREPRINT_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": f"{normalized_server}.details.v1",
        "generated_at": generated_at,
        "status": "blocked",
        "terminal_status": "blocked",
        "server": normalized_server,
        "request": {
            "base_url": PREPRINT_DETAILS_BASE_URL,
            "url": request_url,
            "interval": interval,
            "cursor": cursor,
            "api_docs": PREPRINT_API_DOC_URL,
        },
        "source_policy": _source_policy(max_records=PREPRINT_MAX_CANARY_RECORDS),
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
        "api_page_size": PREPRINT_API_MAX_PAGE_SIZE,
        "api_docs": PREPRINT_API_DOC_URL,
    }


def _valid_interval(interval: str) -> bool:
    if re.fullmatch(r"\d+d?", interval):
        return True
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}", interval):
        return True
    return bool(re.fullmatch(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", interval))


def _normalize_doi(value: str) -> str:
    doi = value.strip().lower()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    return doi


def _normalize_version(value: Any) -> str:
    raw = str(value or "1").strip().lower()
    raw = raw[1:] if raw.startswith("v") else raw
    return raw if raw.isdigit() else "1"


def _preprint_content_url(server: str, *, doi: str, version: str) -> str:
    host = PREPRINT_SERVER_HOSTS[server]
    suffix = f"v{version}" if version else ""
    return f"https://{host}/content/{doi}{suffix}"


def _safe_doi(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", doi).strip("-") or stable_content_hash({"doi": doi})[:16]


def _split_authors(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean_text(str(item)) for item in value if _clean_text(str(item))]
    text = _clean_text(str(value or ""))
    if not text:
        return []
    if ";" in text:
        return [item.strip() for item in re.split(r"\s*;\s*", text) if item.strip()]
    return [text]


def _canonical_document_id(item: Mapping[str, Any]) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
    identity = metadata.get("identity") if isinstance(metadata.get("identity"), Mapping) else {}
    return str(identity.get("canonical_document_id") or item.get("source_id") or "")


def _clean_text(value: str) -> str:
    return " ".join(str(value or "").split())
