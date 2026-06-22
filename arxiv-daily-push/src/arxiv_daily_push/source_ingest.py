"""Live arXiv source ingestion with incremental duplicate filtering."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from .arxiv_adapter import (
    ARXIV_API_BASE_URL,
    ArxivAdapterError,
    ArxivQuery,
    build_query_url,
    fetch_atom,
    parse_atom_feed,
)
from .contracts import validate_source_item


SOURCE_INGEST_MODEL_ID = "adp-live-arxiv-ingest-v1"
SOURCE_INGEST_MAX_RESULTS = 10
SOURCE_INGEST_POLITE_DELAY_SECONDS = 3

FetchAtom = Callable[[ArxivQuery], str]


def ingest_latest_arxiv(
    *,
    search_query: str,
    generated_at: str,
    max_results: int = 10,
    start: int = 0,
    seen_source_ids: Iterable[str] | None = None,
    fetcher: FetchAtom | None = None,
) -> dict[str, Any]:
    """Fetch a small latest arXiv window and return only unseen SourceItems."""

    seen = {str(item) for item in (seen_source_ids or []) if str(item)}
    query = ArxivQuery(search_query=search_query, start=start, max_results=max_results)
    request_url = ""
    try:
        if max_results > SOURCE_INGEST_MAX_RESULTS:
            raise ArxivAdapterError(f"max_results must be between 1 and {SOURCE_INGEST_MAX_RESULTS}")
        request_url = build_query_url(query)
        atom_text = (fetcher or fetch_atom)(query)
        source_items = parse_atom_feed(atom_text, retrieved_at=generated_at)
    except Exception as exc:  # noqa: BLE001 - fail closed with a concise operational reason.
        return _blocked_batch(
            search_query=search_query,
            generated_at=generated_at,
            request_url=request_url or f"{ARXIV_API_BASE_URL}?search_query={search_query}",
            reason=f"arXiv ingest failed: {exc}",
        )

    invalid = [
        {"source_id": item.get("source_id", ""), "errors": validate_source_item(item)}
        for item in source_items
        if validate_source_item(item)
    ]
    if invalid:
        return _blocked_batch(
            search_query=search_query,
            generated_at=generated_at,
            request_url=request_url,
            reason=f"arXiv ingest produced invalid SourceItems: {invalid[0]['source_id']}",
            source_items=source_items,
        )

    duplicate_ids = [item["source_id"] for item in source_items if item["source_id"] in seen]
    new_items = [item for item in source_items if item["source_id"] not in seen]
    status = "pass" if new_items else "blocked"
    blocking_reasons = [] if new_items else ["no unseen arXiv SourceItems returned for the configured query"]
    return {
        "ingest_id": "source-ingest:arxiv-latest",
        "model_id": SOURCE_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": "arxiv.atom.v1",
        "generated_at": generated_at,
        "status": status,
        "request": {
            "base_url": ARXIV_API_BASE_URL,
            "url": request_url,
            "search_query": search_query,
            "start": start,
            "max_results": max_results,
            "sort_by": query.sort_by,
            "sort_order": query.sort_order,
        },
        "source_policy": {
            "network_fetch_enabled": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "max_results_per_call": SOURCE_INGEST_MAX_RESULTS,
            "polite_min_interval_seconds": SOURCE_INGEST_POLITE_DELAY_SECONDS,
        },
        "seen_source_ids": sorted(seen),
        "duplicate_source_ids": duplicate_ids,
        "source_items": source_items,
        "new_items": new_items,
        "new_item_count": len(new_items),
        "blocking_reasons": blocking_reasons,
    }


def validate_source_batch(batch: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if batch.get("model_id") != SOURCE_INGEST_MODEL_ID:
        errors.append("source batch model_id must be adp-live-arxiv-ingest-v1")
    status = batch.get("status")
    if status not in {"pass", "blocked"}:
        errors.append("source batch status must be pass or blocked")
    if status == "pass" and not batch.get("new_items"):
        errors.append("passing source batch requires at least one new item")
    if status == "blocked" and not batch.get("blocking_reasons"):
        errors.append("blocked source batch requires blocking_reasons")
    policy = batch.get("source_policy")
    if not isinstance(policy, Mapping):
        errors.append("source batch source_policy must be an object")
    else:
        if policy.get("pdf_download_enabled") is not False:
            errors.append("source ingest must not download PDFs")
        if policy.get("bulk_harvest_enabled") is not False:
            errors.append("source ingest must not perform bulk harvesting")
    for item in batch.get("new_items") or []:
        if isinstance(item, Mapping):
            errors.extend(validate_source_item(item))
        else:
            errors.append("new_items must contain SourceItem objects")
    return errors


def _blocked_batch(
    *,
    search_query: str,
    generated_at: str,
    request_url: str,
    reason: str,
    source_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "ingest_id": "source-ingest:arxiv-latest",
        "model_id": SOURCE_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": "arxiv.atom.v1",
        "generated_at": generated_at,
        "status": "blocked",
        "request": {"base_url": ARXIV_API_BASE_URL, "url": request_url, "search_query": search_query},
        "source_policy": {
            "network_fetch_enabled": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "max_results_per_call": SOURCE_INGEST_MAX_RESULTS,
            "polite_min_interval_seconds": SOURCE_INGEST_POLITE_DELAY_SECONDS,
        },
        "seen_source_ids": [],
        "duplicate_source_ids": [],
        "source_items": source_items or [],
        "new_items": [],
        "new_item_count": 0,
        "blocking_reasons": [reason],
    }
