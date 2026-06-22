"""V5 Stage 1 scoring, queue, and content ledger contracts."""

from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any


STAGE1_QUEUE_MODEL_ID = "adp-stage1-scoring-queue-ledger-v1"
STAGE1_QUEUE_SCHEMA_VERSION = 1
STAGE1_PARAMETER_PROFILE_VERSION = "adp-stage1-scoring-queue-parameters-v1"
STAGE1_SOURCE_REGISTRY_VERSION = "source-connector-contract-v1"
STAGE1_DEFAULT_MAX_ACTIVE_ITEMS = 10000
STAGE1_DEFAULT_MAX_EVENT_AGE_DAYS = 365
STAGE1_DEFAULT_SOURCE_SHARE_CAP_PER_BOARD = 0.40
STAGE1_DEFAULT_SOFT_QUOTAS: dict[str, int] = {
    "B1": 3500,
    "B2": 1500,
    "B3": 3000,
    "B4": 2000,
}
STAGE1_DEFAULT_RESEARCH_WEIGHTS: dict[str, int] = {
    "relevance": 22,
    "novelty": 16,
    "evidence_quality": 16,
    "technical_breakthrough": 16,
    "conversion_economic_value": 14,
    "impact_scale": 8,
    "timeliness_version_change": 5,
    "diversity_coverage": 3,
}
STAGE1_DEFAULT_QUEUE_PRIORITY_WEIGHTS: dict[str, int] = {
    "quality": 55,
    "event_delta": 15,
    "urgency": 10,
    "cross_board_linkage": 10,
    "waiting_credit": 5,
    "source_balance": 5,
}
STAGE1_CONTENT_LEDGER_COLUMNS: tuple[str, ...] = (
    "item_id",
    "document_id",
    "event_id",
    "theme_cluster_id",
    "board_id",
    "source_id",
    "title",
    "event_date",
    "industry_tags",
    "current_score",
    "current_rank",
    "previous_score",
    "previous_rank",
    "queue_state",
    "explanation_state",
    "reason_code",
    "reason_detail",
    "report_id",
    "report_file_state",
    "report_path",
    "email_id",
    "email_state",
    "email_sent_at",
    "model_version",
    "parameter_version",
    "source_registry_version",
    "run_id",
    "first_seen_at",
    "last_updated_at",
)
STAGE1_NON_ACTIVE_STATES = frozenset({"evicted", "retracted", "superseded", "blocked"})
STAGE1_REACTIVATION_EVENTS = frozenset({"PUBLISHED_AS", "VERSION_OF", "REPLACES", "CORRECTS", "AMENDS"})
STAGE1_RETRACTION_STATUSES = frozenset({"RETRACTED", "WITHDRAWN"})
STAGE1_SUPERSEDED_STATUSES = frozenset({"SUPERSEDED", "REPLACED"})


class Stage1QueueError(ValueError):
    """Raised when Stage 1 queue input cannot be evaluated."""


def score_research_item(item: Mapping[str, Any], controls: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Score one Stage 1 research item from explicit normalized component signals."""

    weights = _research_weights(controls)
    signals = _mapping(item.get("signals"))
    component_scores: dict[str, float] = {}
    missing_components: list[str] = []
    invalid_components: list[str] = []
    for component, weight in weights.items():
        raw_value = signals.get(component)
        if raw_value is None:
            missing_components.append(component)
            normalized = 0.0
        else:
            try:
                normalized = _bounded_float(raw_value, minimum=0.0, maximum=1.0)
            except Stage1QueueError:
                invalid_components.append(component)
                normalized = 0.0
        component_scores[component] = round(normalized * float(weight), 12)
    score = round(sum(component_scores.values()), 12)
    blocking_reasons = [f"invalid signal: {item}" for item in invalid_components]
    return {
        "model_id": STAGE1_QUEUE_MODEL_ID,
        "parameter_version": STAGE1_PARAMETER_PROFILE_VERSION,
        "document_id": _text(item.get("document_id") or item.get("item_id") or "UNKNOWN_DOCUMENT"),
        "score": score,
        "component_scores": component_scores,
        "missing_components": missing_components,
        "blocking_reasons": blocking_reasons,
        "status": "blocked" if blocking_reasons else "pass",
    }


def build_stage1_queue_report(
    items: Sequence[Mapping[str, Any]],
    controls: Mapping[str, Any],
    *,
    as_of_date: str,
    generated_at: str,
    run_id: str = "stage1-queue-fixture",
    previous_entries: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic Stage 1 queue and machine-readable content ledger."""

    params = _queue_parameters(controls)
    as_of = _parse_date(as_of_date, field_name="as_of_date")
    previous_by_item = _previous_by_item(previous_entries or ())
    accepted: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, str]] = []

    for index, raw_item in enumerate(items):
        normalized = _normalize_item(raw_item, generated_at=generated_at, index=index)
        lifecycle_status = _text(raw_item.get("lifecycle_status")).upper()
        if lifecycle_status in STAGE1_RETRACTION_STATUSES:
            ledger_rows.append(
                _ledger_row(
                    normalized,
                    score=None,
                    rank=None,
                    previous=previous_by_item.get(normalized["item_id"], {}),
                    queue_state="retracted",
                    reason_code="RETRACTED_OR_WITHDRAWN",
                    reason_detail="Lifecycle status excludes the item from active queue.",
                    generated_at=generated_at,
                    run_id=run_id,
                )
            )
            continue
        if lifecycle_status in STAGE1_SUPERSEDED_STATUSES:
            ledger_rows.append(
                _ledger_row(
                    normalized,
                    score=None,
                    rank=None,
                    previous=previous_by_item.get(normalized["item_id"], {}),
                    queue_state="superseded",
                    reason_code="SUPERSEDED_OR_REPLACED",
                    reason_detail="Lifecycle status excludes the superseded item from active queue.",
                    generated_at=generated_at,
                    run_id=run_id,
                )
            )
            continue
        event_date = _parse_date(normalized["event_date"], field_name="event_date")
        age_days = (as_of - event_date).days
        if age_days < 0:
            ledger_rows.append(
                _ledger_row(
                    normalized,
                    score=None,
                    rank=None,
                    previous=previous_by_item.get(normalized["item_id"], {}),
                    queue_state="blocked",
                    reason_code="BLOCKED_FUTURE_EVENT_DATE",
                    reason_detail="Event date is after the queue as_of_date.",
                    generated_at=generated_at,
                    run_id=run_id,
                )
            )
            continue
        if age_days > params["max_event_age_days"]:
            ledger_rows.append(
                _ledger_row(
                    normalized,
                    score=None,
                    rank=None,
                    previous=previous_by_item.get(normalized["item_id"], {}),
                    queue_state="evicted",
                    reason_code="EVICTED_AGE",
                    reason_detail=f"Event age {age_days} days is greater than {params['max_event_age_days']}.",
                    generated_at=generated_at,
                    run_id=run_id,
                )
            )
            continue
        score = score_research_item(raw_item, controls)
        queue_score = _queue_priority_score(raw_item, score["score"], controls, max_event_age_days=params["max_event_age_days"])
        reason_code = "REACTIVATED_VERSION" if _text(raw_item.get("version_event_type")).upper() in STAGE1_REACTIVATION_EVENTS else "QUEUED"
        accepted.append(
            {
                **normalized,
                "input_index": index,
                "research_score": score["score"],
                "queue_priority_score": queue_score,
                "reason_code": reason_code,
                "reason_detail": "New version or formal publication reactivates queue eligibility."
                if reason_code == "REACTIVATED_VERSION"
                else "Within Stage 1 active window and eligible for ranking.",
            }
        )

    ordered = sorted(
        accepted,
        key=lambda item: (-float(item["queue_priority_score"]), -float(item["research_score"]), int(item["input_index"])),
    )
    ordered, source_cap_evictions = _apply_source_share_cap(
        ordered,
        params["source_share_cap_per_board"],
        generated_at=generated_at,
        run_id=run_id,
        previous_by_item=previous_by_item,
    )
    ledger_rows.extend(source_cap_evictions)
    active = ordered[: params["max_active_items"]]
    capacity_evicted = ordered[params["max_active_items"] :]
    for rank, item in enumerate(active, start=1):
        ledger_rows.append(
            _ledger_row(
                item,
                score=float(item["research_score"]),
                rank=rank,
                previous=previous_by_item.get(item["item_id"], {}),
                queue_state="queued",
                reason_code=_text(item["reason_code"]),
                reason_detail=_text(item["reason_detail"]),
                generated_at=generated_at,
                run_id=run_id,
            )
        )
    for item in capacity_evicted:
        ledger_rows.append(
            _ledger_row(
                item,
                score=float(item["research_score"]),
                rank=None,
                previous=previous_by_item.get(item["item_id"], {}),
                queue_state="evicted",
                reason_code="EVICTED_CAPACITY",
                reason_detail=f"Queue keeps the first {params['max_active_items']} deterministic ranked items.",
                generated_at=generated_at,
                run_id=run_id,
            )
        )

    ledger_rows = sorted(ledger_rows, key=lambda row: (_state_sort_key(row["queue_state"]), _rank_sort_key(row["current_rank"]), row["item_id"]))
    return {
        "model_id": STAGE1_QUEUE_MODEL_ID,
        "schema_version": STAGE1_QUEUE_SCHEMA_VERSION,
        "status": "pass",
        "generated_at": generated_at,
        "as_of_date": as_of_date,
        "run_id": run_id,
        "parameter_version": STAGE1_PARAMETER_PROFILE_VERSION,
        "source_registry_version": STAGE1_SOURCE_REGISTRY_VERSION,
        "max_active_items": params["max_active_items"],
        "max_event_age_days": params["max_event_age_days"],
        "source_share_cap_per_board": params["source_share_cap_per_board"],
        "soft_quotas": params["soft_quotas"],
        "total_items": len(items),
        "active_count": len(active),
        "evicted_count": sum(1 for row in ledger_rows if row["queue_state"] in STAGE1_NON_ACTIVE_STATES),
        "reason_counts": dict(sorted(Counter(row["reason_code"] for row in ledger_rows).items())),
        "quota_report": _quota_report(active, params["soft_quotas"], params["max_active_items"]),
        "content_ledger_columns": list(STAGE1_CONTENT_LEDGER_COLUMNS),
        "content_ledger_rows": ledger_rows,
        "content_ledger_csv": render_content_ledger_csv(ledger_rows),
        "blocking_reasons": [],
    }


def validate_stage1_queue_report(report: Mapping[str, Any]) -> list[str]:
    """Validate the Stage 1 queue report without trusting the caller."""

    errors: list[str] = []
    if report.get("model_id") != STAGE1_QUEUE_MODEL_ID:
        errors.append("model_id does not match Stage 1 queue model")
    if report.get("schema_version") != STAGE1_QUEUE_SCHEMA_VERSION:
        errors.append("schema_version does not match Stage 1 queue schema")
    active_count = int(report.get("active_count") or 0)
    max_active = int(report.get("max_active_items") or 0)
    if active_count > max_active:
        errors.append("active_count exceeds max_active_items")
    rows = _sequence_of_mappings(report.get("content_ledger_rows"))
    if len(rows) != int(report.get("total_items") or 0):
        errors.append("content_ledger_rows must contain one row per input item")
    seen_item_ids: set[str] = set()
    for row in rows:
        item_id = _text(row.get("item_id"))
        if not item_id:
            errors.append("content ledger row missing item_id")
        if item_id in seen_item_ids:
            errors.append(f"duplicate content ledger item_id: {item_id}")
        seen_item_ids.add(item_id)
        if _text(row.get("queue_state")) in STAGE1_NON_ACTIVE_STATES and not _text(row.get("reason_code")):
            errors.append(f"{item_id}: non-active row missing reason_code")
        if tuple(row.keys()) != STAGE1_CONTENT_LEDGER_COLUMNS:
            errors.append(f"{item_id}: content ledger columns are not canonical")
    active_rows = [row for row in rows if row.get("queue_state") == "queued"]
    ranks = [int(row["current_rank"]) for row in active_rows if str(row.get("current_rank") or "").isdigit()]
    if ranks != list(range(1, len(active_rows) + 1)):
        errors.append("queued rows must have contiguous 1-based current_rank values")
    return errors


def render_content_ledger_csv(rows: Sequence[Mapping[str, Any]]) -> str:
    """Render canonical Stage 1 content ledger rows as CSV."""

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=STAGE1_CONTENT_LEDGER_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: _text(row.get(column, "UNKNOWN")) for column in STAGE1_CONTENT_LEDGER_COLUMNS})
    return buffer.getvalue()


def placeholder_content_ledger_rows(*, generated_at: str) -> list[dict[str, str]]:
    """Return the owner-view placeholder when no production content rows exist."""

    return [
        {
            "item_id": "NO_PRODUCTION_CONTENT_ROWS_S1_06",
            "document_id": "NOT_APPLICABLE",
            "event_id": "S1-06-SCORING-QUEUE-LEDGER-001",
            "theme_cluster_id": "NOT_APPLICABLE",
            "board_id": "NOT_APPLICABLE",
            "source_id": "NOT_APPLICABLE",
            "title": "Stage 1 queue contract is deterministic; no production content ledger rows exist yet",
            "event_date": "2026-06-22",
            "industry_tags": "NOT_APPLICABLE",
            "current_score": "NOT_APPLICABLE",
            "current_rank": "NOT_APPLICABLE",
            "previous_score": "NOT_APPLICABLE",
            "previous_rank": "NOT_APPLICABLE",
            "queue_state": "NOT_APPLICABLE",
            "explanation_state": "not_generated",
            "reason_code": "NO_PRODUCTION_CONTENT_ROWS",
            "reason_detail": "S1-06 proves deterministic fixture scoring and queue behavior but does not claim production content output.",
            "report_id": "NOT_APPLICABLE",
            "report_file_state": "NOT_APPLICABLE",
            "report_path": "NOT_APPLICABLE",
            "email_id": "NOT_APPLICABLE",
            "email_state": "NOT_APPLICABLE",
            "email_sent_at": "NOT_APPLICABLE",
            "model_version": STAGE1_QUEUE_MODEL_ID,
            "parameter_version": STAGE1_PARAMETER_PROFILE_VERSION,
            "source_registry_version": STAGE1_SOURCE_REGISTRY_VERSION,
            "run_id": "NOT_APPLICABLE",
            "first_seen_at": "NOT_APPLICABLE",
            "last_updated_at": generated_at,
        }
    ]


def _queue_parameters(controls: Mapping[str, Any]) -> dict[str, Any]:
    queue = _mapping(controls.get("queue"))
    return {
        "max_active_items": int(queue.get("max_active_items") or STAGE1_DEFAULT_MAX_ACTIVE_ITEMS),
        "max_event_age_days": int(queue.get("max_event_age_days") or STAGE1_DEFAULT_MAX_EVENT_AGE_DAYS),
        "source_share_cap_per_board": float(
            queue.get("source_share_cap_per_board") or STAGE1_DEFAULT_SOURCE_SHARE_CAP_PER_BOARD
        ),
        "soft_quotas": {
            key: int(value)
            for key, value in (_mapping(queue.get("soft_quotas")) or STAGE1_DEFAULT_SOFT_QUOTAS).items()
        },
    }


def _research_weights(controls: Mapping[str, Any] | None) -> dict[str, float]:
    scoring = _mapping((controls or {}).get("scoring"))
    research = _mapping(scoring.get("research"))
    source = research or STAGE1_DEFAULT_RESEARCH_WEIGHTS
    return {key: float(source.get(key, 0)) for key in STAGE1_DEFAULT_RESEARCH_WEIGHTS}


def _queue_priority_weights(controls: Mapping[str, Any]) -> dict[str, float]:
    scoring = _mapping(controls.get("scoring"))
    queue_priority = _mapping(scoring.get("queue_priority"))
    source = queue_priority or STAGE1_DEFAULT_QUEUE_PRIORITY_WEIGHTS
    return {key: float(source.get(key, 0)) for key in STAGE1_DEFAULT_QUEUE_PRIORITY_WEIGHTS}


def _queue_priority_score(
    item: Mapping[str, Any],
    research_score: float,
    controls: Mapping[str, Any],
    *,
    max_event_age_days: int,
) -> float:
    weights = _queue_priority_weights(controls)
    waiting_days = max(0.0, _numeric(item.get("waiting_days"), default=0.0))
    components = {
        "quality": max(0.0, min(1.0, research_score / 100.0)),
        "event_delta": _bounded_float(item.get("event_delta", 0), minimum=0.0, maximum=1.0),
        "urgency": _bounded_float(item.get("urgency", 0), minimum=0.0, maximum=1.0),
        "cross_board_linkage": _bounded_float(item.get("cross_board_linkage", 0), minimum=0.0, maximum=1.0),
        "waiting_credit": max(0.0, min(1.0, waiting_days / float(max_event_age_days))),
        "source_balance": _bounded_float(item.get("source_balance", 1), minimum=0.0, maximum=1.0),
    }
    return round(sum(components[key] * weights[key] for key in STAGE1_DEFAULT_QUEUE_PRIORITY_WEIGHTS), 12)


def _apply_source_share_cap(
    ordered: list[dict[str, Any]],
    cap: float,
    *,
    generated_at: str,
    run_id: str,
    previous_by_item: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if cap <= 0 or cap >= 1:
        return ordered, []
    active = list(ordered)
    evictions: list[dict[str, str]] = []
    changed = True
    while changed:
        changed = False
        by_board: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in active:
            by_board[_text(item["board_id"])].append(item)
        for board_items in by_board.values():
            sources = Counter(_text(item["source_id"]) for item in board_items)
            if len(sources) <= 1:
                continue
            total = len(board_items)
            over_source = next((source for source, count in sources.items() if count / total > cap), "")
            if not over_source:
                continue
            other_count = total - sources[over_source]
            max_allowed = int((cap * other_count) // (1.0 - cap))
            source_items = [item for item in board_items if item["source_id"] == over_source]
            if len(source_items) <= max_allowed:
                continue
            item_to_evict = source_items[-1]
            active.remove(item_to_evict)
            evictions.append(
                _ledger_row(
                    item_to_evict,
                    score=float(item_to_evict["research_score"]),
                    rank=None,
                    previous=previous_by_item.get(item_to_evict["item_id"], {}),
                    queue_state="evicted",
                    reason_code="EVICTED_SOURCE_CAP",
                    reason_detail=f"Source share for {over_source} on board {item_to_evict['board_id']} would exceed {cap:.2f}.",
                    generated_at=generated_at,
                    run_id=run_id,
                )
            )
            changed = True
            break
    return active, evictions


def _quota_report(active: Sequence[Mapping[str, Any]], soft_quotas: Mapping[str, int], max_active_items: int) -> dict[str, Any]:
    counts = Counter(_text(item.get("board_id")) for item in active)
    unused_capacity = max(0, max_active_items - len(active))
    report: dict[str, Any] = {}
    for board_id, quota in soft_quotas.items():
        count = counts.get(board_id, 0)
        report[board_id] = {
            "active_count": count,
            "soft_quota": int(quota),
            "over_soft_quota": max(0, count - int(quota)),
            "borrowed_unused_capacity": count > int(quota) and unused_capacity > 0,
        }
    return report


def _normalize_item(raw_item: Mapping[str, Any], *, generated_at: str, index: int) -> dict[str, Any]:
    document_id = _text(raw_item.get("document_id") or raw_item.get("source_id") or f"doc-{index:05d}")
    return {
        "item_id": _text(raw_item.get("item_id") or document_id),
        "document_id": document_id,
        "event_id": _text(raw_item.get("event_id") or f"event:{document_id}"),
        "theme_cluster_id": _text(raw_item.get("theme_cluster_id") or "UNASSIGNED"),
        "board_id": _text(raw_item.get("board_id") or "B1"),
        "source_id": _text(raw_item.get("source_id") or "SRC-ARXIV"),
        "title": _text(raw_item.get("title") or document_id),
        "event_date": _text(raw_item.get("event_date") or raw_item.get("published_at") or raw_item.get("updated_at")),
        "industry_tags": _tags_text(raw_item.get("industry_tags") or raw_item.get("tags")),
        "first_seen_at": _text(raw_item.get("first_seen_at") or generated_at),
        "last_seen_at": _text(raw_item.get("last_seen_at") or generated_at),
    }


def _ledger_row(
    item: Mapping[str, Any],
    *,
    score: float | None,
    rank: int | None,
    previous: Mapping[str, Any],
    queue_state: str,
    reason_code: str,
    reason_detail: str,
    generated_at: str,
    run_id: str,
) -> dict[str, str]:
    return {
        "item_id": _text(item.get("item_id")),
        "document_id": _text(item.get("document_id")),
        "event_id": _text(item.get("event_id")),
        "theme_cluster_id": _text(item.get("theme_cluster_id")),
        "board_id": _text(item.get("board_id")),
        "source_id": _text(item.get("source_id")),
        "title": _text(item.get("title")),
        "event_date": _text(item.get("event_date")),
        "industry_tags": _text(item.get("industry_tags") or "NOT_APPLICABLE"),
        "current_score": _format_score(score) if score is not None else "NOT_APPLICABLE",
        "current_rank": str(rank) if rank is not None else "NOT_APPLICABLE",
        "previous_score": _text(previous.get("current_score") or previous.get("previous_score") or "UNKNOWN_NO_PRIOR_LEDGER"),
        "previous_rank": _text(previous.get("current_rank") or previous.get("previous_rank") or "UNKNOWN_NO_PRIOR_LEDGER"),
        "queue_state": queue_state,
        "explanation_state": "not_generated",
        "reason_code": reason_code,
        "reason_detail": reason_detail,
        "report_id": "NOT_APPLICABLE",
        "report_file_state": "not_generated",
        "report_path": "NOT_APPLICABLE",
        "email_id": "NOT_APPLICABLE",
        "email_state": "not_sent",
        "email_sent_at": "NOT_APPLICABLE",
        "model_version": STAGE1_QUEUE_MODEL_ID,
        "parameter_version": STAGE1_PARAMETER_PROFILE_VERSION,
        "source_registry_version": STAGE1_SOURCE_REGISTRY_VERSION,
        "run_id": run_id,
        "first_seen_at": _text(item.get("first_seen_at") or generated_at),
        "last_updated_at": generated_at,
    }


def _previous_by_item(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        item_id = _text(row.get("item_id") or row.get("document_id"))
        if item_id:
            result[item_id] = row
    return result


def _parse_date(value: str, *, field_name: str) -> date:
    if not value:
        raise Stage1QueueError(f"{field_name} is required")
    text = value[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise Stage1QueueError(f"{field_name} must use YYYY-MM-DD: {value}") from exc


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _bounded_float(value: Any, *, minimum: float, maximum: float) -> float:
    numeric = _numeric(value, default=None)
    if numeric is None:
        raise Stage1QueueError(f"value is not numeric: {value!r}")
    return max(minimum, min(maximum, numeric))


def _numeric(value: Any, *, default: float | None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        if default is not None:
            return default
        raise Stage1QueueError(f"value is not numeric: {value!r}") from None


def _tags_text(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return "|".join(_text(item) for item in value)
    return _text(value or "NOT_APPLICABLE")


def _format_score(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _state_sort_key(state: str) -> int:
    return 0 if state == "queued" else 1


def _rank_sort_key(value: str) -> int:
    return int(value) if value.isdigit() else 1_000_000_000
