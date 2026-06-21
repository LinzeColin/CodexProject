"""Build scheduled daily input from a live arXiv source batch."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from .config import DEFAULT_TIMEZONE
from .contracts import validate_evidence_claim, validate_source_item
from .ranking import selection_payload
from .source_ingest import validate_source_batch


DAILY_INPUT_BUILDER_MODEL_ID = "adp-daily-input-builder-v1"
DAILY_INPUT_CLAIM_SOURCE = "arxiv_atom_summary_only"
DAILY_INPUT_PRIORITY_CATEGORIES = frozenset({"cs.AI", "cs.CL", "cs.LG", "stat.ML"})
DAILY_INPUT_PDF_DOWNLOAD_ENABLED = False
DAILY_INPUT_BULK_HARVEST_ENABLED = False


def build_daily_input_package(
    source_batch: Mapping[str, Any],
    *,
    date: str,
    generated_at: str,
    timezone: str = DEFAULT_TIMEZONE,
    recent_source_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Convert a source ingest batch into one ranked daily pipeline input."""

    batch_errors = validate_source_batch(source_batch)
    if batch_errors:
        return _blocked_report(
            source_batch=source_batch,
            date=date,
            generated_at=generated_at,
            timezone=timezone,
            reasons=[f"invalid source batch: {batch_errors[0]}"],
        )
    if source_batch.get("status") != "pass":
        return _blocked_report(
            source_batch=source_batch,
            date=date,
            generated_at=generated_at,
            timezone=timezone,
            reasons=list(source_batch.get("blocking_reasons") or ["source batch blocked"]),
        )

    new_items = [item for item in source_batch.get("new_items") or [] if isinstance(item, Mapping)]
    if not new_items:
        return _blocked_report(
            source_batch=source_batch,
            date=date,
            generated_at=generated_at,
            timezone=timezone,
            reasons=["source batch has no new_items for daily input generation"],
        )

    candidates: list[dict[str, Any]] = []
    candidate_errors: list[str] = []
    for item in new_items:
        candidate, errors = _candidate_from_source_item(item, generated_at=generated_at)
        candidate_errors.extend(errors)
        if candidate:
            candidates.append(candidate)
    if not candidates:
        return _blocked_report(
            source_batch=source_batch,
            date=date,
            generated_at=generated_at,
            timezone=timezone,
            reasons=candidate_errors or ["no eligible source items could be converted into candidates"],
        )

    selection = selection_payload(candidates, recent_source_ids=recent_source_ids)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        reasons = candidate_errors + _selection_blockers(selection)
        return _blocked_report(
            source_batch=source_batch,
            date=date,
            generated_at=generated_at,
            timezone=timezone,
            reasons=reasons or ["no eligible ranking candidate selected"],
            candidate_count=len(candidates),
            selection=selection,
        )

    selected_source_id = str(selected.get("source_id") or "")
    selected_candidate = next(
        candidate for candidate in candidates if candidate["source_item"]["source_id"] == selected_source_id
    )
    source_item = dict(selected_candidate["source_item"])
    claims = [dict(claim) for claim in selected_candidate["evidence_claims"]]
    daily_input = {
        "run_id": f"daily:{date}:arxiv:{_safe_id(str(source_item['stable_id']))}",
        "publication_id": f"pub:daily:{date}:arxiv:{_safe_id(str(source_item['stable_id']))}",
        "date": date,
        "generated_at": generated_at,
        "timezone": timezone,
        "source_item": source_item,
        "claims": claims,
        "selection_audit": selection,
    }
    report = _base_report(
        source_batch=source_batch,
        date=date,
        generated_at=generated_at,
        timezone=timezone,
        candidate_count=len(candidates),
        selection=selection,
    )
    report.update(
        {
            "status": "pass",
            "daily_input_ready": True,
            "daily_input": daily_input,
            "blocking_reasons": [],
            "candidate_errors": candidate_errors,
        }
    )
    return report


def validate_daily_input_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != DAILY_INPUT_BUILDER_MODEL_ID:
        errors.append("daily input builder model_id must be adp-daily-input-builder-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("daily input builder status must be pass or blocked")
    policy = report.get("source_policy")
    if not isinstance(policy, Mapping):
        errors.append("daily input builder source_policy is required")
    else:
        if policy.get("claim_source") != DAILY_INPUT_CLAIM_SOURCE:
            errors.append("daily input builder claim_source must be arxiv_atom_summary_only")
        if policy.get("pdf_download_enabled") is not False:
            errors.append("daily input builder must not download PDFs")
        if policy.get("bulk_harvest_enabled") is not False:
            errors.append("daily input builder must not perform bulk harvesting")
        if policy.get("peer_review_claim_enabled") is not False:
            errors.append("daily input builder must not claim peer review from arXiv metadata")
    if report.get("status") == "blocked":
        if report.get("daily_input_ready") is not False:
            errors.append("blocked daily input builder report requires daily_input_ready false")
        if not report.get("blocking_reasons"):
            errors.append("blocked daily input builder report requires blocking_reasons")
        return errors
    if report.get("daily_input_ready") is not True:
        errors.append("passing daily input builder report requires daily_input_ready true")
    daily_input = report.get("daily_input")
    if not isinstance(daily_input, Mapping):
        errors.append("passing daily input builder report requires daily_input object")
        return errors
    for field in ("run_id", "publication_id", "date", "generated_at", "timezone", "source_item", "claims"):
        if not daily_input.get(field):
            errors.append(f"daily_input.{field} is required")
    source_item = daily_input.get("source_item")
    if isinstance(source_item, Mapping):
        errors.extend(validate_source_item(source_item))
    else:
        errors.append("daily_input.source_item must be an object")
    claims = daily_input.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("daily_input.claims must be a non-empty array")
    else:
        for index, claim in enumerate(claims):
            if isinstance(claim, Mapping):
                errors.extend(f"daily_input.claims[{index}]: {error}" for error in validate_evidence_claim(claim))
            else:
                errors.append(f"daily_input.claims[{index}] must be an object")
    selection = report.get("selection")
    if not isinstance(selection, Mapping) or selection.get("status") != "pass" or not selection.get("selected"):
        errors.append("passing daily input builder report requires passing selection audit")
    return errors


def _candidate_from_source_item(
    source_item: Mapping[str, Any],
    *,
    generated_at: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    errors = validate_source_item(source_item)
    source_id = str(source_item.get("source_id") or "")
    arxiv = (source_item.get("metadata") or {}).get("arxiv") if isinstance(source_item.get("metadata"), Mapping) else {}
    if not isinstance(arxiv, Mapping):
        errors.append("SourceItem.metadata.arxiv must be an object")
        arxiv = {}
    summary = _clean_text(str(arxiv.get("summary") or ""))
    if not summary:
        errors.append(f"{source_id or 'source item'} missing arXiv Atom summary")
    if errors:
        return None, errors
    claims = _claims_from_source_item(source_item, summary=summary, generated_at=generated_at)
    signals = _signals_from_source_item(source_item)
    return (
        {
            "candidate_id": f"candidate:{source_id}",
            "source_item": dict(source_item),
            "evidence_claims": claims,
            "signals": signals,
            "claim_source": DAILY_INPUT_CLAIM_SOURCE,
        },
        [],
    )


def _claims_from_source_item(
    source_item: Mapping[str, Any],
    *,
    summary: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    source_id = str(source_item["source_id"])
    stable_url = str(source_item["canonical_url"])
    arxiv = (source_item.get("metadata") or {}).get("arxiv", {})
    primary_category = str(arxiv.get("primary_category") or "") if isinstance(arxiv, Mapping) else ""
    claims = [
        {
            "claim_id": f"claim:{source_id}:abstract-summary",
            "source_id": source_id,
            "claim_type": "author_claim",
            "priority": "P0",
            "statement": f"The arXiv Atom summary states: {summary}",
            "locator": {
                "locator_type": "abstract",
                "stable_url": stable_url,
                "section": "abstract",
                "quote": summary,
            },
            "support_status": "supported",
            "extracted_at": generated_at,
            "notes": "Generated from arXiv Atom <summary>; not a peer-review, PDF, or independent result claim.",
        }
    ]
    if primary_category:
        claims.append(
            {
                "claim_id": f"claim:{source_id}:primary-category",
                "source_id": source_id,
                "claim_type": "metadata",
                "priority": "P1",
                "statement": f"The arXiv Atom metadata lists primary category {primary_category}.",
                "locator": {
                    "locator_type": "metadata",
                    "stable_url": stable_url,
                    "section": "arxiv:primary_category",
                    "quote": primary_category,
                },
                "support_status": "supported",
                "extracted_at": generated_at,
            }
        )
    return claims


def _signals_from_source_item(source_item: Mapping[str, Any]) -> dict[str, float]:
    arxiv = (source_item.get("metadata") or {}).get("arxiv", {})
    categories: set[str] = set()
    primary_category = ""
    if isinstance(arxiv, Mapping):
        primary_category = str(arxiv.get("primary_category") or "")
        raw_categories = arxiv.get("categories") or []
        if isinstance(raw_categories, list):
            categories = {str(category) for category in raw_categories if category}
    priority_match = bool((categories | {primary_category}) & set(DAILY_INPUT_PRIORITY_CATEGORIES))
    return {
        "frontier_signal": 0.75 if priority_match else 0.55,
        "evidence_reliability": 0.90,
        "novelty": 0.65,
        "transfer_value": 0.65,
        "problem_importance": 0.60,
        "taxonomy_priority": 1.0 if priority_match else 0.70,
        "waiting_time": 0.50,
        "diversity": 0.50,
    }


def _base_report(
    *,
    source_batch: Mapping[str, Any],
    date: str,
    generated_at: str,
    timezone: str,
    candidate_count: int = 0,
    selection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "builder_id": f"daily-input:arxiv-latest:{date}",
        "model_id": DAILY_INPUT_BUILDER_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": timezone,
        "status": "blocked",
        "daily_input_ready": False,
        "source_batch_ref": str(source_batch.get("ingest_id") or ""),
        "candidate_count": candidate_count,
        "selection": dict(selection or {"status": "blocked", "selected": None, "audits": []}),
        "daily_input": {},
        "source_policy": {
            "claim_source": DAILY_INPUT_CLAIM_SOURCE,
            "pdf_download_enabled": DAILY_INPUT_PDF_DOWNLOAD_ENABLED,
            "bulk_harvest_enabled": DAILY_INPUT_BULK_HARVEST_ENABLED,
            "peer_review_claim_enabled": False,
            "network_fetch_enabled": False,
            "source_batch_model_id": str(source_batch.get("model_id") or ""),
        },
        "blocking_reasons": [],
    }


def _blocked_report(
    *,
    source_batch: Mapping[str, Any],
    date: str,
    generated_at: str,
    timezone: str,
    reasons: list[str],
    candidate_count: int = 0,
    selection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report = _base_report(
        source_batch=source_batch,
        date=date,
        generated_at=generated_at,
        timezone=timezone,
        candidate_count=candidate_count,
        selection=selection,
    )
    report["blocking_reasons"] = reasons
    return report


def _selection_blockers(selection: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for audit in selection.get("audits") or []:
        if not isinstance(audit, Mapping):
            continue
        source_id = str(audit.get("source_id") or "unknown")
        for reason in audit.get("blocking_reasons") or []:
            reasons.append(f"{source_id}: {reason}")
    return reasons


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return safe.strip("-") or "unknown"


def _clean_text(value: str) -> str:
    return " ".join(value.split())
