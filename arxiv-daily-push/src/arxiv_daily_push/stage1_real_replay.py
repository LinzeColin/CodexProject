"""Stage 1 real arXiv 30 as-of-date replay evidence builder."""

from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .arxiv_adapter import ArxivQuery, build_query_url, fetch_atom
from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .contracts import stable_content_hash, validate_source_item
from .global_scan import (
    ALL_ARXIV_MAX_TOTAL_CANDIDATES,
    CANDIDATE_QUEUE_MAX_ITEMS,
    CANDIDATE_QUEUE_MODEL_ID,
    ROI_RANKING_MODEL_ID,
    _candidate_from_source_item,
    _daily_input_from_selection,
    _sort_candidates,
    normalize_candidate_queue,
    select_roi_candidate,
    update_candidate_queue,
)
from .source_ingest import SOURCE_INGEST_MODEL_ID, FetchAtom, ingest_latest_arxiv, validate_source_batch
from .stage1_b1_report import build_b1_report_email_package, validate_b1_report_email_package
from .stage1_historical_previews import _future_leakage_refs
from .stage1_queue import STAGE1_CONTENT_LEDGER_COLUMNS, render_content_ledger_csv


STAGE1_REAL_REPLAY_MODEL_ID = "adp-stage1-real-arxiv-30-asof-replay-v1"
STAGE1_REAL_REPLAY_SCHEMA_VERSION = 1
STAGE1_REAL_REPLAY_ACCEPTANCE_ID = "ADP-ACC-S1P5T03-REAL-ARXIV-30-ASOF-REPLAY"
STAGE1_REAL_REPLAY_REQUIRED_COUNT = 30
STAGE1_REAL_REPLAY_DEFAULT_LOOKBACK_DAYS = 7
STAGE1_REAL_REPLAY_DEFAULT_MAX_RESULTS = 10
STAGE1_REAL_REPLAY_OFFICIAL_API_REF = "https://info.arxiv.org/help/api/user-manual.html"
STAGE1_REAL_REPLAY_QUERY_POLICY = "submittedDate:[YYYYMMDD0000 TO YYYYMMDD2359]"
STAGE1_REAL_REPLAY_ARTIFACT_FILES = (
    "adp-real-historical-replay-manifest.json",
    "CONTENT_LEDGER.csv",
    "daily_inputs.jsonl",
    "reports.md",
    "email_previews.txt",
    "queue_ledgers.jsonl",
    "run_records.jsonl",
)

RealReplayFetcher = Callable[[ArxivQuery], str]


def build_real_historical_arxiv_replay(
    *,
    generated_at: str,
    start_date: str | None = None,
    end_date: str | None = None,
    count: int = STAGE1_REAL_REPLAY_REQUIRED_COUNT,
    lookback_days: int = STAGE1_REAL_REPLAY_DEFAULT_LOOKBACK_DAYS,
    max_results: int = STAGE1_REAL_REPLAY_DEFAULT_MAX_RESULTS,
    recipient: str = DEFAULT_RECIPIENT,
    artifact_dir: str | Path | None = None,
    write: bool = False,
    fetcher: RealReplayFetcher | None = None,
    source_batches_by_date: Mapping[str, Mapping[str, Any]] | None = None,
    polite_delay_seconds: float = 3.0,
) -> dict[str, Any]:
    """Replay real arXiv as-of dates without production side effects."""

    dates, date_errors = _replay_dates(start_date=start_date, end_date=end_date, count=count, generated_at=generated_at)
    if date_errors:
        return _blocked_report(generated_at=generated_at, reasons=date_errors, requested_count=count)
    if write and artifact_dir is None:
        return _blocked_report(
            generated_at=generated_at,
            reasons=["artifact_dir is required when write is true"],
            requested_count=count,
        )

    fetch = fetcher or fetch_atom_with_curl
    queue_state = normalize_candidate_queue(None, generated_at=generated_at)
    recent_source_ids: set[str] = set()
    previous_queue_after_hash = ""
    day_records: list[dict[str, Any]] = []
    daily_inputs: list[dict[str, Any]] = []
    report_markdowns: list[dict[str, str]] = []
    email_previews: list[dict[str, str]] = []
    queue_ledgers: list[dict[str, Any]] = []
    content_ledger_rows: list[dict[str, str]] = []
    blocking_reasons: list[str] = []

    for index, as_of in enumerate(dates):
        as_of_text = as_of.isoformat()
        day_generated_at = f"{as_of_text}T05:00:00+10:00"
        queue_before_hash = stable_content_hash({"queue": queue_state})
        query = build_submitted_date_query(as_of, lookback_days=lookback_days)
        if source_batches_by_date and as_of_text in source_batches_by_date:
            source_batch = dict(source_batches_by_date[as_of_text])
        else:
            source_batch = ingest_latest_arxiv(
                search_query=query,
                generated_at=day_generated_at,
                max_results=max_results,
                seen_source_ids=[],
                fetcher=fetch,
            )
            if polite_delay_seconds > 0 and index < len(dates) - 1:
                time.sleep(float(polite_delay_seconds))

        day_record, next_queue_state = _build_replay_day(
            as_of=as_of,
            day_generated_at=day_generated_at,
            query=query,
            source_batch=source_batch,
            queue_state=queue_state,
            recent_source_ids=recent_source_ids,
            previous_queue_after_hash=previous_queue_after_hash,
            queue_before_hash=queue_before_hash,
            recipient=recipient,
        )
        day_records.append(day_record)
        if day_record["status"] == "pass":
            daily_inputs.append(day_record["daily_input"])
            report_markdowns.append(
                {
                    "date": as_of_text,
                    "source_id": day_record["selected_source_id"],
                    "markdown": day_record["report_markdown"],
                }
            )
            email_previews.append(
                {
                    "date": as_of_text,
                    "source_id": day_record["selected_source_id"],
                    "subject": day_record["email_subject"],
                    "plain": day_record["email_plain"],
                    "html": day_record["email_html"],
                }
            )
            queue_ledgers.append(day_record["queue_ledger"])
            content_ledger_rows.extend(day_record["content_ledger_rows"])
            recent_source_ids.add(day_record["selected_source_id"])
            queue_state = next_queue_state
            previous_queue_after_hash = day_record["queue_after_hash"]
        else:
            blocking_reasons.extend(f"{as_of_text}: {reason}" for reason in day_record["blocking_reasons"])

    report = _summarize_replay(
        generated_at=generated_at,
        requested_count=count,
        lookback_days=lookback_days,
        max_results=max_results,
        day_records=day_records,
        daily_inputs=daily_inputs,
        report_markdowns=report_markdowns,
        email_previews=email_previews,
        queue_ledgers=queue_ledgers,
        content_ledger_rows=content_ledger_rows,
        blocking_reasons=blocking_reasons,
    )
    validation_errors = validate_real_historical_arxiv_replay_report(report)
    if validation_errors:
        report["status"] = "blocked"
        report["blocking_reasons"] = sorted(set([*blocking_reasons, *validation_errors]))
    if write and artifact_dir is not None:
        artifact_summary = write_real_historical_replay_artifacts(
            report,
            daily_inputs=daily_inputs,
            report_markdowns=report_markdowns,
            email_previews=email_previews,
            queue_ledgers=queue_ledgers,
            content_ledger_rows=content_ledger_rows,
            artifact_dir=artifact_dir,
        )
        report["artifact_summary"] = artifact_summary
        if report["status"] == "pass":
            artifact_errors = validate_real_historical_arxiv_replay_report(report)
            if artifact_errors:
                report["status"] = "blocked"
                report["blocking_reasons"] = sorted(set([*report.get("blocking_reasons", []), *artifact_errors]))
    return report


def validate_real_historical_arxiv_replay_report(report: Mapping[str, Any]) -> list[str]:
    """Validate the real arXiv 30 as-of-date replay acceptance evidence."""

    errors: list[str] = []
    if report.get("model_id") != STAGE1_REAL_REPLAY_MODEL_ID:
        errors.append("model_id must be adp-stage1-real-arxiv-30-asof-replay-v1")
    if report.get("schema_version") != STAGE1_REAL_REPLAY_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if report.get("acceptance_id") != STAGE1_REAL_REPLAY_ACCEPTANCE_ID:
        errors.append("acceptance_id must be ADP-ACC-S1P5T03-REAL-ARXIV-30-ASOF-REPLAY")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("status must be pass or blocked")
    day_records = report.get("day_records")
    if not isinstance(day_records, list):
        errors.append("day_records must be an array")
        day_records = []
    required = int(report.get("required_replay_count") or STAGE1_REAL_REPLAY_REQUIRED_COUNT)
    if report.get("replay_count") != len(day_records):
        errors.append("replay_count must match day_records length")
    gates = report.get("quality_gates")
    if not isinstance(gates, Mapping):
        errors.append("quality_gates must be an object")
        gates = {}
    for key in (
        "thirty_of_thirty_success",
        "thirty_unique_as_of_dates",
        "real_arxiv_source_ids",
        "no_future_data_leakage",
        "no_duplicate_lead",
        "candidate_queue_continuous",
        "unsupported_p0_p1_zero",
        "daily_inputs_generated",
        "reports_generated",
        "email_previews_generated",
        "queue_ledgers_generated",
        "content_ledger_selected_rows_generated",
        "content_ledger_queued_rows_generated",
        "content_ledger_email_state_present",
        "content_ledger_artifact_refs_present",
        "no_production_side_effects",
    ):
        if gates.get(key) is not True:
            errors.append(f"quality_gates.{key} must be true")
    if report.get("success_count") != required:
        errors.append("success_count must equal required_replay_count")
    if report.get("unique_as_of_date_count") != required:
        errors.append("unique_as_of_date_count must equal required_replay_count")
    if report.get("unique_selected_source_count") != required:
        errors.append("unique_selected_source_count must equal required_replay_count")
    if report.get("real_arxiv_source_id_count") != required:
        errors.append("real_arxiv_source_id_count must equal required_replay_count")
    for count_key in (
        "future_leakage_count",
        "duplicate_lead_count",
        "queue_continuity_break_count",
        "unsupported_p0_p1_count",
    ):
        if int(report.get(count_key) or 0) != 0:
            errors.append(f"{count_key} must be 0")
    for count_key in ("daily_input_count", "report_count", "email_preview_count", "queue_ledger_count"):
        if int(report.get(count_key) or 0) != required:
            errors.append(f"{count_key} must equal required_replay_count")
    if int(report.get("content_ledger_selected_row_count") or 0) != required:
        errors.append("content_ledger_selected_row_count must equal required_replay_count")
    if int(report.get("content_ledger_queued_row_count") or 0) < required:
        errors.append("content_ledger_queued_row_count must be at least required_replay_count")
    source_policy = report.get("source_policy")
    if not isinstance(source_policy, Mapping):
        errors.append("source_policy must be an object")
    else:
        if source_policy.get("source_type") != "arxiv":
            errors.append("source_policy.source_type must be arxiv")
        if source_policy.get("network_fetch_enabled") is not True:
            errors.append("source_policy.network_fetch_enabled must be true")
        for key in ("pdf_download_enabled", "bulk_harvest_enabled", "peer_review_claim_enabled"):
            if source_policy.get(key) is not False:
                errors.append(f"source_policy.{key} must be false")
        if "cs.AI" in str(source_policy.get("query_policy") or ""):
            errors.append("source_policy.query_policy must not collapse to cs.AI")
    side_effects = report.get("side_effect_policy")
    if not isinstance(side_effects, Mapping):
        errors.append("side_effect_policy must be an object")
    else:
        for key in ("real_smtp_sent", "release_uploaded", "video_generated", "scheduler_enabled", "secret_values_logged"):
            if side_effects.get(key) is not False:
                errors.append(f"side_effect_policy.{key} must be false")
    artifact_summary = report.get("artifact_summary")
    if isinstance(artifact_summary, Mapping) and artifact_summary:
        expected = set(STAGE1_REAL_REPLAY_ARTIFACT_FILES)
        actual = {str(item.get("name") or "") for item in artifact_summary.get("files") or [] if isinstance(item, Mapping)}
        if expected - actual:
            errors.append("artifact_summary.files must include all real replay artifact files")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked replay report requires blocking_reasons")
    return errors


def build_submitted_date_query(as_of: date, *, lookback_days: int) -> str:
    """Build an all-arXiv submittedDate query ending at the as-of date."""

    window = max(1, int(lookback_days))
    start = as_of - timedelta(days=window - 1)
    return f"submittedDate:[{start:%Y%m%d}0000 TO {as_of:%Y%m%d}2359]"


def fetch_atom_with_curl(
    query: ArxivQuery,
    *,
    timeout_seconds: int = 45,
    retry_count: int = 3,
    retry_delay_seconds: float = 10.0,
) -> str:
    """Fetch arXiv Atom through curl for hosts whose Python CA store is broken."""

    url = build_query_url(query)
    attempts = max(1, int(retry_count) + 1)
    last_detail = ""
    for attempt in range(1, attempts + 1):
        result = subprocess.run(
            ["curl", "-fsSL", "--max-time", str(int(timeout_seconds)), url],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        detail = (result.stderr or result.stdout or "curl returned no output").strip().splitlines()
        last_detail = detail[0] if detail else str(result.returncode)
        if attempt < attempts:
            time.sleep(max(0.0, float(retry_delay_seconds)))
    if last_detail == "curl returned no output":
        raise RuntimeError("curl arXiv fetch returned an empty response")
    raise RuntimeError(f"curl arXiv fetch failed after {attempts} attempts: {last_detail}")


def fetch_atom_with_urllib(query: ArxivQuery) -> str:
    """Fetch arXiv Atom through Python urllib."""

    return fetch_atom(query)


def write_real_historical_replay_artifacts(
    report: Mapping[str, Any],
    *,
    daily_inputs: Sequence[Mapping[str, Any]],
    report_markdowns: Sequence[Mapping[str, str]],
    email_previews: Sequence[Mapping[str, str]],
    queue_ledgers: Sequence[Mapping[str, Any]],
    content_ledger_rows: Sequence[Mapping[str, Any]],
    artifact_dir: str | Path,
) -> dict[str, Any]:
    """Write compact aggregate replay artifacts."""

    root = Path(artifact_dir)
    root.mkdir(parents=True, exist_ok=True)
    slim_report = {
        key: value
        for key, value in report.items()
        if key not in {"artifact_summary", "blocking_reasons"}
    }
    slim_report["blocking_reasons"] = list(report.get("blocking_reasons") or [])
    files = {
        "adp-real-historical-replay-manifest.json": json.dumps(slim_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "CONTENT_LEDGER.csv": render_content_ledger_csv(content_ledger_rows),
        "daily_inputs.jsonl": _jsonl(daily_inputs),
        "reports.md": _reports_markdown(report_markdowns),
        "email_previews.txt": _email_preview_text(email_previews),
        "queue_ledgers.jsonl": _jsonl(queue_ledgers),
        "run_records.jsonl": _jsonl(report.get("day_records") if isinstance(report.get("day_records"), list) else []),
    }
    refs = []
    for name, content in files.items():
        path = root / name
        path.write_text(content, encoding="utf-8")
        refs.append(
            {
                "name": name,
                "path": str(path),
                "sha256": stable_content_hash({"content": content}),
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "write_enabled": True,
        "artifact_dir": str(root),
        "file_count": len(refs),
        "files": refs,
    }


def _build_replay_day(
    *,
    as_of: date,
    day_generated_at: str,
    query: str,
    source_batch: Mapping[str, Any],
    queue_state: Mapping[str, Any],
    recent_source_ids: set[str],
    previous_queue_after_hash: str,
    queue_before_hash: str,
    recipient: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    as_of_text = as_of.isoformat()
    batch_errors = validate_source_batch(source_batch)
    hard_blocked = bool(batch_errors) or source_batch.get("status") == "blocked"
    if hard_blocked:
        return (
            _blocked_day(
                as_of_text,
                query=query,
                queue_before_hash=queue_before_hash,
                previous_queue_after_hash=previous_queue_after_hash,
                reasons=batch_errors or list(source_batch.get("blocking_reasons") or ["source batch blocked"]),
            ),
            dict(queue_state),
        )

    candidates, candidate_errors, future_refs = _candidates_from_batch(source_batch, as_of=as_of, generated_at=day_generated_at)
    selection = select_roi_candidate(candidates, queue_state.get("items") if isinstance(queue_state.get("items"), list) else [], recent_source_ids=recent_source_ids)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        reasons = list(selection.get("blocking_reasons") or ["no selected candidate"])
        if candidate_errors:
            reasons.append(f"candidate conversion errors: {candidate_errors[0]}")
        return (
            _blocked_day(
                as_of_text,
                query=query,
                queue_before_hash=queue_before_hash,
                previous_queue_after_hash=previous_queue_after_hash,
                reasons=reasons,
                future_filtered_refs=future_refs,
            ),
            dict(queue_state),
        )

    updated_queue = update_candidate_queue(
        existing_items=queue_state.get("items") if isinstance(queue_state.get("items"), list) else [],
        new_candidates=candidates,
        selected_source_id=str(selected["source_id"]),
        generated_at=day_generated_at,
        max_items=CANDIDATE_QUEUE_MAX_ITEMS,
    )
    scan = {
        "scan_id": f"real-historical-asof:{as_of_text}",
        "model_id": STAGE1_REAL_REPLAY_MODEL_ID,
        "generated_at": day_generated_at,
        "status": "pass",
        "archive_count": 1,
        "blocked_archive_count": 0,
        "candidate_count": len(candidates),
        "candidates": _sort_candidates(candidates)[:ALL_ARXIV_MAX_TOTAL_CANDIDATES],
        "candidate_errors": candidate_errors,
        "query": query,
        "source_batch_model_id": source_batch.get("model_id"),
    }
    daily_input = _daily_input_from_selection(
        selected,
        date=as_of_text,
        generated_at=day_generated_at,
        timezone=DEFAULT_TIMEZONE,
        scan=scan,
        queue=updated_queue,
    )
    queue_ledger = {
        "date": as_of_text,
        "model_id": CANDIDATE_QUEUE_MODEL_ID,
        "queue_before_hash": queue_before_hash,
        "queue_after_hash": stable_content_hash({"queue": updated_queue}),
        "previous_queue_after_hash": previous_queue_after_hash,
        "queue_continuity_passed": not previous_queue_after_hash or previous_queue_after_hash == queue_before_hash,
        "queued_item_count": len(updated_queue.get("items") or []),
        "selected_source_id": str(selected["source_id"]),
        "top_queued": daily_input["queue_summary"]["top_queued"],
    }
    package_payload = {
        "daily_input": daily_input,
        "candidate_count": len(candidates),
        "queue_report": {
            "total_items": len(updated_queue.get("items") or []) + 1,
            "active_count": len(updated_queue.get("items") or []),
        },
    }
    package = build_b1_report_email_package(
        package_payload,
        generated_at=day_generated_at,
        recipient=recipient,
        write=False,
    )
    package_errors = validate_b1_report_email_package(package)
    if package_errors or package.get("status") != "pass":
        return (
            _blocked_day(
                as_of_text,
                query=query,
                queue_before_hash=queue_before_hash,
                previous_queue_after_hash=previous_queue_after_hash,
                reasons=package_errors or list(package.get("blocking_reasons") or ["report/email package blocked"]),
                future_filtered_refs=future_refs,
            ),
            dict(queue_state),
        )
    source_item = daily_input["source_item"]
    content_ledger_rows = _content_ledger_rows_for_day(
        date_text=as_of_text,
        generated_at=day_generated_at,
        selected=selected,
        daily_input=daily_input,
        package=package,
        queue=updated_queue,
    )
    selected_future_refs = _future_leakage_refs(daily_input)
    audit = package.get("claim_evidence_audit") if isinstance(package.get("claim_evidence_audit"), Mapping) else {}
    unsupported = [str(item) for item in audit.get("unsupported_critical_claim_ids") or [] if str(item)]
    arxiv = source_item.get("metadata", {}).get("arxiv", {}) if isinstance(source_item.get("metadata"), Mapping) else {}
    return (
        {
            "date": as_of_text,
            "status": "pass",
            "query": query,
            "source_batch_model_id": source_batch.get("model_id", SOURCE_INGEST_MODEL_ID),
            "source_batch_new_item_count": int(source_batch.get("new_item_count") or 0),
            "candidate_count": len(candidates),
            "future_filtered_refs": future_refs,
            "future_filtered_count": len(future_refs),
            "selected_future_leakage_refs": selected_future_refs,
            "selected_source_id": str(source_item["source_id"]),
            "selected_stable_id": str(source_item["stable_id"]),
            "selected_title": str(source_item["title"]),
            "selected_primary_category": str(arxiv.get("primary_category") or ""),
            "selected_published": str(arxiv.get("published") or ""),
            "selected_updated": str(arxiv.get("updated") or ""),
            "selection_source": selected.get("selection_source", ""),
            "selection_model_id": ROI_RANKING_MODEL_ID,
            "queue_before_hash": queue_before_hash,
            "queue_after_hash": queue_ledger["queue_after_hash"],
            "previous_queue_after_hash": previous_queue_after_hash,
            "queue_continuity_passed": queue_ledger["queue_continuity_passed"],
            "unsupported_p0_p1_count": len(unsupported),
            "unsupported_p0_p1_claim_ids": unsupported,
            "daily_input_hash": stable_content_hash({"daily_input": daily_input}),
            "report_markdown_hash": stable_content_hash({"report_markdown": package.get("report_markdown", "")}),
            "email_preview_hash": stable_content_hash({"email_plain": package.get("email_plain", ""), "email_html": package.get("email_html", "")}),
            "queue_ledger_hash": stable_content_hash({"queue_ledger": queue_ledger}),
            "content_ledger_row_count": len(content_ledger_rows),
            "content_ledger_selected_row_count": 1,
            "content_ledger_queued_row_count": max(0, len(content_ledger_rows) - 1),
            "email_subject": str(package["email_subject"]),
            "report_id": str(package["report_id"]),
            "email_id": str(package["email_id"]),
            "daily_input": daily_input,
            "report_markdown": str(package["report_markdown"]),
            "email_plain": str(package["email_plain"]),
            "email_html": str(package["email_html"]),
            "queue_ledger": queue_ledger,
            "content_ledger_rows": content_ledger_rows,
            "blocking_reasons": [],
        },
        updated_queue,
    )


def _candidates_from_batch(source_batch: Mapping[str, Any], *, as_of: date, generated_at: str) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    candidates: list[dict[str, Any]] = []
    candidate_errors: list[str] = []
    future_refs: list[str] = []
    seen: set[str] = set()
    for source_item in source_batch.get("new_items") or source_batch.get("source_items") or []:
        if not isinstance(source_item, Mapping):
            continue
        errors = validate_source_item(source_item)
        if errors:
            candidate_errors.append(f"{source_item.get('source_id', 'unknown')}: {errors[0]}")
            continue
        source_id = str(source_item.get("source_id") or "")
        if source_id in seen:
            continue
        seen.add(source_id)
        leakage = _source_item_future_refs(source_item, as_of=as_of)
        if leakage:
            future_refs.extend(leakage)
            continue
        candidate, conversion_errors = _candidate_from_source_item(source_item, generated_at=generated_at)
        candidate_errors.extend(conversion_errors)
        if candidate:
            candidates.append(candidate)
    return _sort_candidates(candidates)[:ALL_ARXIV_MAX_TOTAL_CANDIDATES], candidate_errors, future_refs


def _source_item_future_refs(source_item: Mapping[str, Any], *, as_of: date) -> list[str]:
    daily_input = {
        "date": as_of.isoformat(),
        "source_item": source_item,
    }
    return _future_leakage_refs(daily_input)


def _summarize_replay(
    *,
    generated_at: str,
    requested_count: int,
    lookback_days: int,
    max_results: int,
    day_records: Sequence[Mapping[str, Any]],
    daily_inputs: Sequence[Mapping[str, Any]],
    report_markdowns: Sequence[Mapping[str, str]],
    email_previews: Sequence[Mapping[str, str]],
    queue_ledgers: Sequence[Mapping[str, Any]],
    content_ledger_rows: Sequence[Mapping[str, str]],
    blocking_reasons: Sequence[str],
) -> dict[str, Any]:
    passed = [record for record in day_records if record.get("status") == "pass"]
    dates = [str(record.get("date") or "") for record in day_records if record.get("date")]
    selected = [str(record.get("selected_source_id") or "") for record in passed if record.get("selected_source_id")]
    duplicate_leads = len(selected) - len(set(selected))
    future_leakage_count = sum(len(record.get("selected_future_leakage_refs") or []) for record in passed)
    queue_breaks = sum(1 for record in passed if record.get("queue_continuity_passed") is not True)
    unsupported_p0_p1 = sum(int(record.get("unsupported_p0_p1_count") or 0) for record in passed)
    real_source_ids = [source_id for source_id in selected if source_id.startswith("arxiv:")]
    selected_ledger_rows = [row for row in content_ledger_rows if str(row.get("queue_state") or "") == "covered_deep"]
    queued_ledger_rows = [row for row in content_ledger_rows if str(row.get("queue_state") or "") == "queued"]
    artifact_ref_rows = [
        row
        for row in content_ledger_rows
        if str(row.get("report_path") or "") not in {"", "NOT_APPLICABLE"}
        or str(row.get("reason_detail") or "").find("artifact_ref=") >= 0
    ]
    email_state_rows = [row for row in content_ledger_rows if str(row.get("email_state") or "") not in {"", "NOT_APPLICABLE"}]
    required = int(requested_count)
    status = "pass" if not blocking_reasons else "blocked"
    summary_records = [
        {
            key: value
            for key, value in record.items()
            if key not in {"daily_input", "report_markdown", "email_plain", "email_html", "queue_ledger"}
        }
        for record in day_records
    ]
    quality_gates = {
        "thirty_of_thirty_success": len(passed) == required,
        "thirty_unique_as_of_dates": len(set(dates)) == required,
        "real_arxiv_source_ids": len(real_source_ids) == required,
        "no_future_data_leakage": future_leakage_count == 0,
        "no_duplicate_lead": duplicate_leads == 0,
        "candidate_queue_continuous": queue_breaks == 0 and len(passed) == required,
        "unsupported_p0_p1_zero": unsupported_p0_p1 == 0,
        "daily_inputs_generated": len(daily_inputs) == required,
        "reports_generated": len(report_markdowns) == required,
        "email_previews_generated": len(email_previews) == required,
        "queue_ledgers_generated": len(queue_ledgers) == required,
        "content_ledger_selected_rows_generated": len(selected_ledger_rows) == required,
        "content_ledger_queued_rows_generated": len(queued_ledger_rows) >= required,
        "content_ledger_email_state_present": len(email_state_rows) == len(content_ledger_rows) and bool(content_ledger_rows),
        "content_ledger_artifact_refs_present": len(artifact_ref_rows) >= required,
        "no_production_side_effects": True,
    }
    report = {
        "model_id": STAGE1_REAL_REPLAY_MODEL_ID,
        "schema_version": STAGE1_REAL_REPLAY_SCHEMA_VERSION,
        "project_id": "arxiv-daily-push",
        "acceptance_id": STAGE1_REAL_REPLAY_ACCEPTANCE_ID,
        "status": status,
        "generated_at": generated_at,
        "required_replay_count": required,
        "replay_count": len(day_records),
        "success_count": len(passed),
        "unique_as_of_date_count": len(set(dates)),
        "unique_selected_source_count": len(set(selected)),
        "real_arxiv_source_id_count": len(real_source_ids),
        "future_leakage_count": future_leakage_count,
        "duplicate_lead_count": duplicate_leads,
        "queue_continuity_break_count": queue_breaks,
        "unsupported_p0_p1_count": unsupported_p0_p1,
        "daily_input_count": len(daily_inputs),
        "report_count": len(report_markdowns),
        "email_preview_count": len(email_previews),
        "queue_ledger_count": len(queue_ledgers),
        "content_ledger_row_count": len(content_ledger_rows),
        "content_ledger_selected_row_count": len(selected_ledger_rows),
        "content_ledger_queued_row_count": len(queued_ledger_rows),
        "lookback_days": int(lookback_days),
        "max_results": int(max_results),
        "source_policy": {
            "source_type": "arxiv",
            "source_adapter": "arxiv.atom.v1",
            "network_fetch_enabled": True,
            "fetch_surface": "arxiv_api_query",
            "query_policy": STAGE1_REAL_REPLAY_QUERY_POLICY,
            "official_api_reference": STAGE1_REAL_REPLAY_OFFICIAL_API_REF,
            "all_arxiv_date_filter": True,
            "legacy_single_category_query_forbidden": "cat:cs.AI",
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "peer_review_claim_enabled": False,
        },
        "side_effect_policy": {
            "real_smtp_sent": False,
            "release_uploaded": False,
            "video_generated": False,
            "scheduler_enabled": False,
            "secret_values_logged": False,
            "email_body_logged_to_ci": False,
        },
        "quality_gates": quality_gates,
        "selected_source_ids": selected,
        "content_ledger_columns": list(STAGE1_CONTENT_LEDGER_COLUMNS),
        "content_ledger_artifact": "CONTENT_LEDGER.csv",
        "day_records": summary_records,
        "artifact_summary": {},
        "blocking_reasons": list(blocking_reasons),
    }
    if not all(quality_gates.values()):
        report["status"] = "blocked"
    return report


def _replay_dates(
    *,
    start_date: str | None,
    end_date: str | None,
    count: int,
    generated_at: str,
) -> tuple[list[date], list[str]]:
    if count < 1:
        return [], ["count must be positive"]
    end = _parse_date(end_date) if end_date else _parse_date(generated_at[:10])
    if end is None:
        return [], ["end_date or generated_at date is invalid"]
    start = _parse_date(start_date) if start_date else end - timedelta(days=count - 1)
    if start is None:
        return [], ["start_date is invalid"]
    dates = [start + timedelta(days=index) for index in range((end - start).days + 1)]
    if len(dates) != count:
        return dates, [f"date range must produce exactly {count} dates"]
    return dates, []


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _blocked_day(
    date_text: str,
    *,
    query: str,
    queue_before_hash: str,
    previous_queue_after_hash: str,
    reasons: Sequence[str],
    future_filtered_refs: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "date": date_text,
        "status": "blocked",
        "query": query,
        "queue_before_hash": queue_before_hash,
        "previous_queue_after_hash": previous_queue_after_hash,
        "queue_continuity_passed": not previous_queue_after_hash or previous_queue_after_hash == queue_before_hash,
        "future_filtered_refs": list(future_filtered_refs),
        "future_filtered_count": len(future_filtered_refs),
        "blocking_reasons": [str(reason) for reason in reasons if str(reason)],
    }


def _content_ledger_rows_for_day(
    *,
    date_text: str,
    generated_at: str,
    selected: Mapping[str, Any],
    daily_input: Mapping[str, Any],
    package: Mapping[str, Any],
    queue: Mapping[str, Any],
) -> list[dict[str, str]]:
    source_item = daily_input["source_item"]
    arxiv = source_item.get("metadata", {}).get("arxiv", {}) if isinstance(source_item.get("metadata"), Mapping) else {}
    selected_source_id = str(source_item["source_id"])
    report_anchor = f"reports.md#{date_text}-{_ledger_safe_id(selected_source_id)}"
    email_anchor = f"email_previews.txt#{date_text}-{_ledger_safe_id(selected_source_id)}"
    rows = [
        _ledger_row(
            source_id=selected_source_id,
            title=str(source_item.get("title") or ""),
            date_text=date_text,
            generated_at=generated_at,
            primary_category=str(arxiv.get("primary_category") or ""),
            score=str(selected.get("roi_total_score") or ""),
            rank="1",
            queue_state="covered_deep",
            explanation_state="report_generated",
            reason_code="S1P5T03R_SELECTED",
            reason_detail=f"selected as daily lead; artifact_ref={report_anchor}; email_ref={email_anchor}",
            report_id=str(package.get("report_id") or ""),
            report_file_state="generated",
            report_path=report_anchor,
            email_id=str(package.get("email_id") or ""),
            email_state="preview_generated",
            email_sent_at="NOT_SENT_DRY_RUN",
            run_id=str(daily_input.get("run_id") or ""),
        )
    ]
    for rank, item in enumerate(queue.get("items") or [], start=1):
        if not isinstance(item, Mapping):
            continue
        source = item.get("source_item") if isinstance(item.get("source_item"), Mapping) else {}
        primary = str(item.get("primary_category") or "")
        rows.append(
            _ledger_row(
                source_id=str(item.get("source_id") or source.get("source_id") or ""),
                title=str(item.get("title") or source.get("title") or ""),
                date_text=date_text,
                generated_at=generated_at,
                primary_category=primary,
                score=str(item.get("roi_total_score") or ""),
                rank=str(rank),
                queue_state="queued",
                explanation_state="not_generated",
                reason_code="S1P5T03R_QUEUED",
                reason_detail=f"queued candidate after daily selection; artifact_ref=queue_ledgers.jsonl#{date_text}",
                report_id="NOT_GENERATED_QUEUE_CANDIDATE",
                report_file_state="not_generated",
                report_path="NOT_APPLICABLE",
                email_id="NOT_GENERATED_QUEUE_CANDIDATE",
                email_state="not_sent_queue",
                email_sent_at="NOT_SENT_DRY_RUN",
                run_id=str(daily_input.get("run_id") or ""),
            )
        )
    return rows


def _ledger_row(
    *,
    source_id: str,
    title: str,
    date_text: str,
    generated_at: str,
    primary_category: str,
    score: str,
    rank: str,
    queue_state: str,
    explanation_state: str,
    reason_code: str,
    reason_detail: str,
    report_id: str,
    report_file_state: str,
    report_path: str,
    email_id: str,
    email_state: str,
    email_sent_at: str,
    run_id: str,
) -> dict[str, str]:
    return {
        "item_id": source_id,
        "document_id": source_id.removeprefix("arxiv:"),
        "event_id": f"S1P5T03-R:{date_text}",
        "theme_cluster_id": primary_category or "arxiv",
        "board_id": "B1",
        "source_id": source_id,
        "title": title,
        "event_date": date_text,
        "industry_tags": primary_category or "arxiv",
        "current_score": score or "NOT_APPLICABLE",
        "current_rank": rank,
        "previous_score": "NOT_APPLICABLE",
        "previous_rank": "NOT_APPLICABLE",
        "queue_state": queue_state,
        "explanation_state": explanation_state,
        "reason_code": reason_code,
        "reason_detail": reason_detail,
        "report_id": report_id,
        "report_file_state": report_file_state,
        "report_path": report_path,
        "email_id": email_id,
        "email_state": email_state,
        "email_sent_at": email_sent_at,
        "model_version": STAGE1_REAL_REPLAY_MODEL_ID,
        "parameter_version": "adp-stage1-real-arxiv-replay-parameters-v1",
        "source_registry_version": "arxiv.atom.v1",
        "run_id": run_id,
        "first_seen_at": generated_at,
        "last_updated_at": generated_at,
    }


def _ledger_safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()


def _blocked_report(*, generated_at: str, reasons: Sequence[str], requested_count: int) -> dict[str, Any]:
    return {
        "model_id": STAGE1_REAL_REPLAY_MODEL_ID,
        "schema_version": STAGE1_REAL_REPLAY_SCHEMA_VERSION,
        "project_id": "arxiv-daily-push",
        "acceptance_id": STAGE1_REAL_REPLAY_ACCEPTANCE_ID,
        "status": "blocked",
        "generated_at": generated_at,
        "required_replay_count": requested_count,
        "replay_count": 0,
        "success_count": 0,
        "day_records": [],
        "quality_gates": {},
        "source_policy": {
            "source_type": "arxiv",
            "network_fetch_enabled": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "peer_review_claim_enabled": False,
            "query_policy": STAGE1_REAL_REPLAY_QUERY_POLICY,
        },
        "side_effect_policy": {
            "real_smtp_sent": False,
            "release_uploaded": False,
            "video_generated": False,
            "scheduler_enabled": False,
            "secret_values_logged": False,
            "email_body_logged_to_ci": False,
        },
        "blocking_reasons": [str(reason) for reason in reasons if str(reason)],
    }


def _jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def _reports_markdown(rows: Sequence[Mapping[str, str]]) -> str:
    parts = []
    for row in rows:
        parts.append(f"\n\n<!-- date={row['date']} source_id={row['source_id']} -->\n\n")
        parts.append(row["markdown"].strip() + "\n")
    return "".join(parts).lstrip()


def _email_preview_text(rows: Sequence[Mapping[str, str]]) -> str:
    parts = []
    for row in rows:
        parts.append(
            "\n".join(
                [
                    f"===== {row['date']} | {row['source_id']} =====",
                    f"Subject: {row['subject']}",
                    "",
                    row["plain"].strip(),
                    "",
                ]
            )
        )
    return "\n".join(parts).strip() + "\n"
