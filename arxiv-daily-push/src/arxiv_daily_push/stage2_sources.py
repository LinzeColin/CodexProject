"""Stage 2 source-promotion gates and local shadow artifacts."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Mapping, Sequence
from datetime import date as Date
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import DEFAULT_TIMEZONE
from .global_scan import (
    CANDIDATE_QUEUE_MAX_ITEMS,
    CANDIDATE_QUEUE_MODEL_ID,
    ROI_RANKING_MODEL_ID,
    build_daily_delivery_package,
    candidate_from_source_item,
    normalize_candidate_queue,
    select_roi_candidate,
    update_candidate_queue,
)
from .pipeline import PipelineError, run_daily_dry_run
from .preprint_adapter import (
    PREPRINT_INGEST_MODEL_ID,
    SUPPORTED_PREPRINT_SERVERS,
    ingest_latest_preprints,
    validate_preprint_source_batch,
)
from .top_journal_adapter import (
    TOP_JOURNAL_INGEST_MODEL_ID,
    ingest_latest_top_journal,
    validate_top_journal_source_batch,
)


S2P1_PREPRINT_PROMOTION_MODEL_ID = "adp-s2p1-preprint-source-promotion-v1"
S2P1_PREPRINT_SHADOW_MODEL_ID = "adp-s2p1-preprint-shadow-daily-v1"
S2P1_PREPRINT_REPLAY_MODEL_ID = "adp-s2p1-preprint-terminal-replay-v1"
S2P1_PREPRINT_SHADOW_EVIDENCE_MODEL_ID = "adp-s2p1-preprint-shadow-evidence-v1"
S2P1_ACCEPTANCE_ID = "ADP-ACC-S2P1T01-SOURCE-PROMOTION"
S2P1_TASK_ID = "S2P1T01"
S2P1_REQUIRED_SERVERS = ("biorxiv", "medrxiv")
S2P1_REPLAY_REQUIRED_DATES = 30
S2P1_SHADOW_REQUIRED_HOURS = 48
S2P1_QUEUE_FILENAME = "stage2_s2p1_preprint_queue.json"
S2P1_LEDGER_FILENAME = "stage2_s2p1_preprint_ledger.jsonl"
S2P1_REPLAY_REPORT_FILENAME = "stage2_s2p1_preprint_replay_report.json"
S2P1_SHADOW_EVIDENCE_FILENAME = "stage2_s2p1_preprint_shadow_48h_report.json"
S2P1_PROMOTION_REPORT_FILENAME = "stage2_s2p1_preprint_promotion_report.json"
S2P2_TOP_JOURNAL_SHADOW_MODEL_ID = "adp-s2p2-top-journal-shadow-daily-v1"
S2P2_ACCEPTANCE_ID = "ADP-ACC-S2P2T01-TOP-JOURNAL-SHADOW"
S2P2_TASK_ID = "S2P2T01"
S2P2_REQUIRED_JOURNALS = ("nature",)
S2P2_QUEUE_FILENAME = "stage2_s2p2_top_journal_queue.json"
S2P2_LEDGER_FILENAME = "stage2_s2p2_top_journal_ledger.jsonl"


def build_s2p1_preprint_promotion_report(
    *,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    replay_report: Mapping[str, Any] | None = None,
    shadow_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate source-level promotion gates for bioRxiv and medRxiv."""

    source_reports = []
    blocking_reasons: list[str] = []
    canonical_ids: set[str] = set()
    duplicate_canonical_ids: set[str] = set()
    for server in S2P1_REQUIRED_SERVERS:
        batch = source_batches.get(server)
        if not isinstance(batch, Mapping):
            source_reports.append({"server": server, "status": "blocked", "blocking_reasons": ["missing source batch"]})
            blocking_reasons.append(f"{server}: missing source batch")
            continue
        errors = validate_preprint_source_batch(batch)
        license_errors = _license_gate_errors(batch)
        version_errors = _version_gate_errors(batch)
        identity_ids = _canonical_ids(batch)
        for canonical_id in identity_ids:
            if canonical_id in canonical_ids:
                duplicate_canonical_ids.add(canonical_id)
            canonical_ids.add(canonical_id)
        reasons = errors + license_errors + version_errors
        source_reports.append(
            {
                "server": server,
                "status": "pass" if not reasons and batch.get("status") == "pass" else "blocked",
                "source_adapter": batch.get("source_adapter", ""),
                "source_item_count": len(batch.get("source_items") or []),
                "new_item_count": int(batch.get("new_item_count") or 0),
                "terminal_status": batch.get("terminal_status", ""),
                "identity_gate": "pass" if identity_ids else "blocked",
                "version_gate": "pass" if not version_errors else "blocked",
                "license_gate": "pass" if not license_errors else "blocked",
                "blocking_reasons": reasons,
            }
        )
        blocking_reasons.extend(f"{server}: {reason}" for reason in reasons)
    if duplicate_canonical_ids:
        blocking_reasons.append("duplicate canonical preprint documents: " + ", ".join(sorted(duplicate_canonical_ids)))

    replay_gate = _replay_gate(replay_report)
    shadow_gate = _shadow_gate(shadow_report)
    blocking_reasons.extend(replay_gate["blocking_reasons"])
    blocking_reasons.extend(shadow_gate["blocking_reasons"])
    source_gate_ready = all(item["status"] == "pass" for item in source_reports) and not duplicate_canonical_ids
    ready = source_gate_ready and replay_gate["status"] == "pass" and shadow_gate["status"] == "pass"
    return {
        "model_id": S2P1_PREPRINT_PROMOTION_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "source_gate_ready": source_gate_ready,
        "replay_gate_ready": replay_gate["status"] == "pass",
        "shadow_gate_ready": shadow_gate["status"] == "pass",
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "video_required": False,
        "source_reports": source_reports,
        "replay_gate": replay_gate,
        "shadow_gate": shadow_gate,
        "canonical_document_count": len(canonical_ids),
        "duplicate_canonical_ids": sorted(duplicate_canonical_ids),
        "blocking_reasons": blocking_reasons,
    }


def build_s2p1_preprint_daily_input(
    *,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a shadow daily input from bioRxiv/medRxiv SourceBatches."""

    scan = _preprint_scan(source_batches, generated_at=generated_at)
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    if scan["status"] == "blocked":
        return _blocked_daily_input(date, generated_at, queue_state, scan, scan["blocking_reasons"])
    selection = select_roi_candidate(scan["candidates"], queue_state["items"], recent_source_ids=recent_source_ids)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        return _blocked_daily_input(date, generated_at, queue_state, scan, list(selection.get("blocking_reasons") or []), selection=selection)
    updated_queue = update_candidate_queue(
        existing_items=queue_state["items"],
        new_candidates=scan["candidates"],
        selected_source_id=str(selected["source_id"]),
        generated_at=generated_at,
        max_items=max_queue_items,
    )
    daily_input = _daily_input_from_selection(selected, date=date, generated_at=generated_at, queue=updated_queue)
    return {
        "model_id": S2P1_PREPRINT_SHADOW_MODEL_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "pass",
        "daily_input_ready": True,
        "formal_production_inclusion": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "blocking_reasons": [],
    }


def run_s2p1_preprint_shadow_daily(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    write: bool = True,
) -> dict[str, Any]:
    """Run one no-send Stage 2 shadow daily path and persist local evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2p1-preprint-shadow"
    queue_path = state / S2P1_QUEUE_FILENAME
    ledger_path = state / S2P1_LEDGER_FILENAME
    queue_state = queue if queue is not None else _load_json(queue_path) if queue_path.exists() else None
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)

    daily_report = build_s2p1_preprint_daily_input(
        date=date,
        generated_at=generated_at,
        source_batches=source_batches,
        queue=queue_state,
        recent_source_ids=recent_source_ids,
    )
    if write:
        _write_json(run_dir / "adp-s2p1-preprint-daily-input-report.json", daily_report)
    if daily_report.get("daily_input_ready") is not True:
        return _write_or_return(
            _base_shadow_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=list(daily_report.get("blocking_reasons") or ["preprint daily input blocked"]),
                daily_report=daily_report,
            ),
            run_dir,
            write=write,
        )
    daily_input = daily_report["daily_input"]
    try:
        daily_run = run_daily_dry_run(
            daily_input["source_item"],
            daily_input["claims"],
            run_id=daily_input["run_id"],
            publication_id=daily_input["publication_id"],
            date=daily_input["date"],
            generated_at=generated_at,
            timezone=DEFAULT_TIMEZONE,
        )
    except (KeyError, PipelineError) as error:
        return _write_or_return(
            _base_shadow_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=[f"preprint shadow pipeline failed: {error}"],
                daily_report=daily_report,
            ),
            run_dir,
            write=write,
        )
    delivery_package = build_daily_delivery_package(
        daily_run,
        daily_input,
        {"status": "skipped", "release_ref": "", "assets": []},
        generated_at=generated_at,
    )
    notification = delivery_package["notification"]
    ledger_row = {
        "date": date,
        "generated_at": generated_at,
        "task_id": S2P1_TASK_ID,
        "source_id": daily_input["source_item"]["source_id"],
        "canonical_document_id": _canonical_document_id(daily_input["source_item"]),
        "title": daily_input["source_item"]["title"],
        "shadow_mode": True,
        "formal_production_inclusion": False,
        "email_state": "preview_only",
        "run_dir": str(run_dir),
        "queue_item_count": len(daily_report["candidate_queue"].get("items") or []),
    }
    if write:
        _write_json(run_dir / "adp-s2p1-preprint-daily-run.json", daily_run)
        _write_json(run_dir / "adp-s2p1-preprint-delivery-package.json", {k: v for k, v in delivery_package.items() if k != "notification"})
        _write_json(queue_path, daily_report["candidate_queue"])
        (run_dir / "email_preview.txt").write_text(notification.body, encoding="utf-8")
        (run_dir / "email_preview.html").write_text(notification.html_body, encoding="utf-8")
        _append_jsonl(ledger_path, ledger_row)
    report = _base_shadow_report(
        status="pass",
        date=date,
        generated_at=generated_at,
        state=state,
        run_dir=run_dir,
        blocking_reasons=[],
        daily_report=daily_report,
    )
    report.update(
        {
            "daily_run_status": daily_run["status"],
            "selected_source_id": daily_input["source_item"]["source_id"],
            "selected_title": daily_input["source_item"]["title"],
            "candidate_queue_path": str(queue_path),
            "content_ledger_path": str(ledger_path),
            "content_ledger_row": ledger_row,
            "email_preview_written": write,
            "email_preview_paths": {
                "plain": str(run_dir / "email_preview.txt"),
                "html": str(run_dir / "email_preview.html"),
            },
            "delivery_package": {k: v for k, v in delivery_package.items() if k != "notification"},
            "real_smtp_sent": False,
            "production_affected": False,
        }
    )
    return _write_or_return(report, run_dir, write=write)


def validate_s2p1_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2P1_PREPRINT_SHADOW_MODEL_ID:
        errors.append("S2P1 shadow report model_id must be adp-s2p1-preprint-shadow-daily-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2P1 shadow report status must be pass or blocked")
    for key in ("formal_production_inclusion", "github_cloud_schedule_enabled", "real_smtp_sent", "production_affected"):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2P1 shadow daily")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2P1 shadow report requires blocking_reasons")
    if report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing S2P1 shadow report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing S2P1 shadow report requires email_preview_written")
    return errors


def build_s2p2_top_journal_daily_input(
    *,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a no-send shadow daily input from top-journal public metadata."""

    scan = _top_journal_scan(source_batches, generated_at=generated_at)
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    if scan["status"] == "blocked":
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            scan["blocking_reasons"],
            model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
            task_id=S2P2_TASK_ID,
        )
    selection = select_roi_candidate(scan["candidates"], queue_state["items"], recent_source_ids=recent_source_ids)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            list(selection.get("blocking_reasons") or []),
            selection=selection,
            model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
            task_id=S2P2_TASK_ID,
        )
    updated_queue = update_candidate_queue(
        existing_items=queue_state["items"],
        new_candidates=scan["candidates"],
        selected_source_id=str(selected["source_id"]),
        generated_at=generated_at,
        max_items=max_queue_items,
    )
    daily_input = _daily_input_from_selection(
        selected,
        date=date,
        generated_at=generated_at,
        queue=updated_queue,
        run_label="s2p2-top-journal",
        scan_scope="s2p2_top_journal_shadow",
        source_count=len(S2P2_REQUIRED_JOURNALS),
        task_id=S2P2_TASK_ID,
    )
    return {
        "model_id": S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
        "task_id": S2P2_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "pass",
        "daily_input_ready": True,
        "formal_production_inclusion": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "blocking_reasons": [],
    }


def run_s2p2_top_journal_shadow_daily(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    write: bool = True,
) -> dict[str, Any]:
    """Run one no-send Stage 2 top-journal shadow daily path and persist evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2p2-top-journal-shadow"
    queue_path = state / S2P2_QUEUE_FILENAME
    ledger_path = state / S2P2_LEDGER_FILENAME
    queue_state = queue if queue is not None else _load_json(queue_path) if queue_path.exists() else None
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)

    daily_report = build_s2p2_top_journal_daily_input(
        date=date,
        generated_at=generated_at,
        source_batches=source_batches,
        queue=queue_state,
        recent_source_ids=recent_source_ids,
    )
    if write:
        _write_json(run_dir / "adp-s2p2-top-journal-daily-input-report.json", daily_report)
    if daily_report.get("daily_input_ready") is not True:
        return _write_or_return_s2p2(
            _base_shadow_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=list(daily_report.get("blocking_reasons") or ["top-journal daily input blocked"]),
                daily_report=daily_report,
                model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
                acceptance_id=S2P2_ACCEPTANCE_ID,
                task_id=S2P2_TASK_ID,
            ),
            run_dir,
            write=write,
        )
    daily_input = daily_report["daily_input"]
    try:
        daily_run = run_daily_dry_run(
            daily_input["source_item"],
            daily_input["claims"],
            run_id=daily_input["run_id"],
            publication_id=daily_input["publication_id"],
            date=daily_input["date"],
            generated_at=generated_at,
            timezone=DEFAULT_TIMEZONE,
        )
    except (KeyError, PipelineError) as error:
        return _write_or_return_s2p2(
            _base_shadow_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=[f"top-journal shadow pipeline failed: {error}"],
                daily_report=daily_report,
                model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
                acceptance_id=S2P2_ACCEPTANCE_ID,
                task_id=S2P2_TASK_ID,
            ),
            run_dir,
            write=write,
        )
    delivery_package = build_daily_delivery_package(
        daily_run,
        daily_input,
        {"status": "skipped", "release_ref": "", "assets": []},
        generated_at=generated_at,
    )
    notification = delivery_package["notification"]
    ledger_row = {
        "date": date,
        "generated_at": generated_at,
        "task_id": S2P2_TASK_ID,
        "source_id": daily_input["source_item"]["source_id"],
        "canonical_document_id": _canonical_document_id(daily_input["source_item"]),
        "title": daily_input["source_item"]["title"],
        "shadow_mode": True,
        "formal_production_inclusion": False,
        "email_state": "preview_only",
        "run_dir": str(run_dir),
        "queue_item_count": len(daily_report["candidate_queue"].get("items") or []),
    }
    if write:
        _write_json(run_dir / "adp-s2p2-top-journal-daily-run.json", daily_run)
        _write_json(run_dir / "adp-s2p2-top-journal-delivery-package.json", {k: v for k, v in delivery_package.items() if k != "notification"})
        _write_json(queue_path, daily_report["candidate_queue"])
        (run_dir / "email_preview.txt").write_text(notification.body, encoding="utf-8")
        (run_dir / "email_preview.html").write_text(notification.html_body, encoding="utf-8")
        _append_jsonl(ledger_path, ledger_row)
    report = _base_shadow_report(
        status="pass",
        date=date,
        generated_at=generated_at,
        state=state,
        run_dir=run_dir,
        blocking_reasons=[],
        daily_report=daily_report,
        model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
        acceptance_id=S2P2_ACCEPTANCE_ID,
        task_id=S2P2_TASK_ID,
    )
    report.update(
        {
            "daily_run_status": daily_run["status"],
            "selected_source_id": daily_input["source_item"]["source_id"],
            "selected_title": daily_input["source_item"]["title"],
            "candidate_queue_path": str(queue_path),
            "content_ledger_path": str(ledger_path),
            "content_ledger_row": ledger_row,
            "email_preview_written": write,
            "email_preview_paths": {
                "plain": str(run_dir / "email_preview.txt"),
                "html": str(run_dir / "email_preview.html"),
            },
            "delivery_package": {k: v for k, v in delivery_package.items() if k != "notification"},
            "real_smtp_sent": False,
            "production_affected": False,
        }
    )
    return _write_or_return_s2p2(report, run_dir, write=write)


def validate_s2p2_top_journal_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2P2_TOP_JOURNAL_SHADOW_MODEL_ID:
        errors.append("S2P2 shadow report model_id must be adp-s2p2-top-journal-shadow-daily-v1")
    if report.get("task_id") != S2P2_TASK_ID:
        errors.append("S2P2 shadow report task_id must be S2P2T01")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2P2 shadow report status must be pass or blocked")
    for key in ("formal_production_inclusion", "github_cloud_schedule_enabled", "real_smtp_sent", "production_affected"):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2P2 top-journal shadow daily")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2P2 shadow report requires blocking_reasons")
    if report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing S2P2 shadow report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing S2P2 shadow report requires email_preview_written")
        source_id = str(report.get("selected_source_id") or "")
        if not source_id.startswith("nature:s41586-"):
            errors.append("passing S2P2 shadow report requires selected Nature main-journal source_id")
    return errors


def fetch_s2p2_top_journal_batches(*, generated_at: str, max_records: int = 3) -> dict[str, dict[str, Any]]:
    return {
        journal: ingest_latest_top_journal(
            journal=journal,
            generated_at=generated_at,
            max_records=max_records,
        )
        for journal in S2P2_REQUIRED_JOURNALS
    }


def fetch_s2p1_preprint_batches(
    *,
    generated_at: str,
    interval: str = "1d",
    max_records: int = 3,
) -> dict[str, dict[str, Any]]:
    return {
        server: ingest_latest_preprints(
            server=server,
            generated_at=generated_at,
            interval=interval,
            max_records=max_records,
        )
        for server in S2P1_REQUIRED_SERVERS
    }


def build_s2p1_preprint_replay_shadow_evidence(
    *,
    state_dir: str | Path,
    generated_at: str,
    start_date: str | None = None,
    end_date: str | None = None,
    count: int = S2P1_REPLAY_REQUIRED_DATES,
    lookback_days: int = 7,
    max_records: int = 3,
    source_batches_by_date: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
    fetcher: Any | None = None,
    write: bool = True,
    polite_delay_seconds: float = 0.0,
) -> dict[str, Any]:
    """Build terminal replay plus 48h no-production shadow evidence for S2P1T01."""

    state = Path(state_dir).resolve()
    if write:
        state.mkdir(parents=True, exist_ok=True)
    dates = _replay_dates(start_date=start_date, end_date=end_date, count=count, generated_at=generated_at)
    if not dates:
        replay_report = _blocked_replay_report(generated_at, state, ["date range produced no replay dates"], requested_count=count)
        shadow_report = _shadow_evidence_report(generated_at=generated_at, state=state, daily_reports=[], replay_report=replay_report)
        return _combined_replay_shadow_report(generated_at, state, replay_report, shadow_report, {}, write=write)
    if lookback_days < 1:
        replay_report = _blocked_replay_report(generated_at, state, ["lookback_days must be >= 1"], requested_count=count)
        shadow_report = _shadow_evidence_report(generated_at=generated_at, state=state, daily_reports=[], replay_report=replay_report)
        return _combined_replay_shadow_report(generated_at, state, replay_report, shadow_report, {}, write=write)

    daily_reports: list[dict[str, Any]] = []
    selected_source_ids: list[str] = []
    selected_canonical_ids: list[str] = []
    source_batches_by_server: dict[str, Mapping[str, Any]] = {}
    blocking_reasons: list[str] = []
    queue_state = _load_json(state / S2P1_QUEUE_FILENAME) if (state / S2P1_QUEUE_FILENAME).exists() else None
    for index, as_of in enumerate(dates, start=1):
        source_batches = (
            source_batches_by_date.get(as_of.isoformat(), {})
            if isinstance(source_batches_by_date, Mapping)
            else _fetch_replay_source_batches(
                as_of=as_of,
                generated_at=generated_at,
                lookback_days=lookback_days,
                max_records=max_records,
                fetcher=fetcher,
            )
        )
        if not isinstance(source_batches, Mapping):
            source_batches = {}
        for server in S2P1_REQUIRED_SERVERS:
            batch = source_batches.get(server)
            if isinstance(batch, Mapping):
                source_batches_by_server[server] = batch
        report = run_s2p1_preprint_shadow_daily(
            state_dir=state,
            date=as_of.isoformat(),
            generated_at=generated_at,
            source_batches=source_batches,
            queue=queue_state,
            recent_source_ids=selected_source_ids,
            write=write,
        )
        report["replay_day_index"] = index
        report["accelerated_historical_shadow"] = True
        report["as_of_date"] = as_of.isoformat()
        daily_reports.append(report)
        queue_candidate = report.get("daily_report", {}).get("candidate_queue") if isinstance(report.get("daily_report"), Mapping) else None
        if isinstance(queue_candidate, Mapping):
            queue_state = queue_candidate
        if report.get("status") != "pass":
            blocking_reasons.extend(f"{as_of.isoformat()}: {reason}" for reason in report.get("blocking_reasons") or ["shadow daily blocked"])
        else:
            source_id = str(report.get("selected_source_id") or "")
            canonical_id = str((report.get("content_ledger_row") or {}).get("canonical_document_id") or "")
            if source_id:
                selected_source_ids.append(source_id)
            if canonical_id:
                selected_canonical_ids.append(canonical_id)
        if polite_delay_seconds > 0 and index < len(dates) and source_batches_by_date is None:
            time.sleep(float(polite_delay_seconds))

    replay_report = _replay_report(
        generated_at=generated_at,
        state=state,
        requested_count=count,
        dates=dates,
        daily_reports=daily_reports,
        selected_source_ids=selected_source_ids,
        selected_canonical_ids=selected_canonical_ids,
        blocking_reasons=blocking_reasons,
    )
    shadow_report = _shadow_evidence_report(generated_at=generated_at, state=state, daily_reports=daily_reports, replay_report=replay_report)
    promotion_report = build_s2p1_preprint_promotion_report(
        generated_at=generated_at,
        source_batches=source_batches_by_server,
        replay_report=replay_report,
        shadow_report=shadow_report,
    )
    return _combined_replay_shadow_report(generated_at, state, replay_report, shadow_report, promotion_report, write=write)


def validate_s2p1_preprint_replay_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2P1_PREPRINT_REPLAY_MODEL_ID:
        errors.append("S2P1 replay-shadow report model_id must be adp-s2p1-preprint-terminal-replay-v1")
    replay = report.get("replay_report") if isinstance(report.get("replay_report"), Mapping) else {}
    shadow = report.get("shadow_report") if isinstance(report.get("shadow_report"), Mapping) else {}
    promotion = report.get("promotion_report") if isinstance(report.get("promotion_report"), Mapping) else {}
    if replay.get("status") != "pass":
        errors.append("embedded S2P1 replay_report must pass")
    if shadow.get("status") != "pass":
        errors.append("embedded S2P1 shadow_report must pass")
    if promotion.get("status") != "pass":
        errors.append("embedded S2P1 promotion_report must pass")
    if report.get("formal_production_inclusion") is not False:
        errors.append("formal_production_inclusion must be false")
    if report.get("github_cloud_schedule_enabled") is not False:
        errors.append("github_cloud_schedule_enabled must be false")
    if report.get("real_smtp_sent") is not False:
        errors.append("real_smtp_sent must be false")
    return errors


def _fetch_replay_source_batches(
    *,
    as_of: Date,
    generated_at: str,
    lookback_days: int,
    max_records: int,
    fetcher: Any | None,
) -> dict[str, dict[str, Any]]:
    start = as_of - timedelta(days=int(lookback_days) - 1)
    interval = f"{start.isoformat()}/{as_of.isoformat()}"
    return {
        server: ingest_latest_preprints(
            server=server,
            generated_at=generated_at,
            interval=interval,
            max_records=max_records,
            fetcher=fetcher,
        )
        for server in S2P1_REQUIRED_SERVERS
    }


def _replay_report(
    *,
    generated_at: str,
    state: Path,
    requested_count: int,
    dates: Sequence[Date],
    daily_reports: Sequence[Mapping[str, Any]],
    selected_source_ids: Sequence[str],
    selected_canonical_ids: Sequence[str],
    blocking_reasons: Sequence[str],
) -> dict[str, Any]:
    daily_records = [_daily_replay_record(as_of, report) for as_of, report in zip(dates, daily_reports, strict=False)]
    future_leakage = [record for record in daily_records if record.get("future_leakage")]
    duplicate_selected = _duplicate_values(selected_source_ids)
    duplicate_canonical = _duplicate_values(selected_canonical_ids)
    queue_breaks = [
        record
        for record in daily_records
        if record.get("status") == "pass" and not (record.get("queue_persisted") and record.get("ledger_persisted") and record.get("email_preview_persisted"))
    ]
    p0_p1_records = [record for record in daily_records if int(record.get("p0_p1_blocker_count") or 0) > 0]
    reasons = list(blocking_reasons)
    if len({date.isoformat() for date in dates}) < S2P1_REPLAY_REQUIRED_DATES:
        reasons.append("S2P1 replay requires 30 unique dates")
    if len(daily_reports) < requested_count:
        reasons.append("S2P1 replay did not produce all requested daily reports")
    if duplicate_selected:
        reasons.append("S2P1 replay duplicate selected source IDs: " + ", ".join(duplicate_selected))
    if duplicate_canonical:
        reasons.append("S2P1 replay duplicate canonical document IDs: " + ", ".join(duplicate_canonical))
    if future_leakage:
        reasons.append("S2P1 replay has future-dated selected preprints")
    if queue_breaks:
        reasons.append("S2P1 replay queue/ledger/email persistence continuity failed")
    if p0_p1_records:
        reasons.append("S2P1 replay has P0/P1 blockers")
    status = "pass" if not reasons else "blocked"
    return {
        "model_id": S2P1_PREPRINT_REPLAY_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "state_dir": str(state),
        "required_replay_count": S2P1_REPLAY_REQUIRED_DATES,
        "requested_replay_count": int(requested_count),
        "replay_count": len(daily_reports),
        "success_count": len([report for report in daily_reports if report.get("status") == "pass"]),
        "unique_date_count": len({date.isoformat() for date in dates}),
        "unique_selected_source_count": len(set(selected_source_ids)),
        "unique_selected_canonical_count": len(set(selected_canonical_ids)),
        "real_preprint_source_id_count": len([source_id for source_id in selected_source_ids if _is_preprint_source_id(source_id)]),
        "future_leakage_count": len(future_leakage),
        "duplicate_selected_count": len(duplicate_selected),
        "duplicate_canonical_count": len(duplicate_canonical),
        "queue_continuity_break_count": len(queue_breaks),
        "p0_p1_blocker_count": len(p0_p1_records),
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "video_generated": False,
        "daily_records": daily_records,
        "blocking_reasons": sorted(set(reasons)),
    }


def _daily_replay_record(as_of: Date, report: Mapping[str, Any]) -> dict[str, Any]:
    source_item = (
        report.get("daily_report", {}).get("daily_input", {}).get("source_item", {})
        if isinstance(report.get("daily_report"), Mapping)
        else {}
    )
    if not isinstance(source_item, Mapping):
        source_item = {}
    selected_source_id = str(report.get("selected_source_id") or source_item.get("source_id") or "")
    source_date = _source_item_preprint_date(source_item)
    validation_errors = report.get("validation_errors") if isinstance(report.get("validation_errors"), list) else []
    blocking_reasons = [str(reason) for reason in report.get("blocking_reasons") or []]
    p0_p1_blockers = [
        reason
        for reason in [*blocking_reasons, *[str(error) for error in validation_errors]]
        if "P0" in reason or "P1" in reason or "claim" in reason.lower() or "validation" in reason.lower()
    ]
    return {
        "date": as_of.isoformat(),
        "status": str(report.get("status") or "blocked"),
        "selected_source_id": selected_source_id,
        "selected_title": str(report.get("selected_title") or source_item.get("title") or ""),
        "canonical_document_id": str((report.get("content_ledger_row") or {}).get("canonical_document_id") or _canonical_document_id(source_item)),
        "source_preprint_date": source_date,
        "future_leakage": bool(source_date and source_date > as_of.isoformat()),
        "queue_persisted": Path(str(report.get("candidate_queue_path") or "")).is_file(),
        "ledger_persisted": Path(str(report.get("content_ledger_path") or "")).is_file(),
        "email_preview_persisted": Path(str((report.get("email_preview_paths") or {}).get("plain") or "")).is_file(),
        "daily_input_ready": bool(report.get("daily_input_ready") is True),
        "daily_run_status": str(report.get("daily_run_status") or ""),
        "p0_p1_blocker_count": len(p0_p1_blockers),
        "blocking_reasons": blocking_reasons,
    }


def _shadow_evidence_report(
    *,
    generated_at: str,
    state: Path,
    daily_reports: Sequence[Mapping[str, Any]],
    replay_report: Mapping[str, Any],
) -> dict[str, Any]:
    dates = [str(report.get("date") or report.get("as_of_date") or "") for report in daily_reports if str(report.get("date") or report.get("as_of_date") or "")]
    shadow_hours = _shadow_hours_from_dates(dates)
    reasons: list[str] = []
    if replay_report.get("status") != "pass":
        reasons.append("S2P1 shadow evidence requires passing replay report")
    if shadow_hours < S2P1_SHADOW_REQUIRED_HOURS:
        reasons.append("S2P1 shadow requires at least 48 hours")
    if any(report.get("status") != "pass" for report in daily_reports):
        reasons.append("S2P1 shadow daily reports must all pass")
    if any(report.get("formal_production_inclusion") is not False for report in daily_reports):
        reasons.append("S2P1 shadow daily formal_production_inclusion must be false")
    if any(report.get("real_smtp_sent") is not False for report in daily_reports):
        reasons.append("S2P1 shadow daily must not send SMTP")
    if any(report.get("production_affected") is not False for report in daily_reports):
        reasons.append("S2P1 shadow daily must not affect production")
    return {
        "model_id": S2P1_PREPRINT_SHADOW_EVIDENCE_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if not reasons else "blocked",
        "state_dir": str(state),
        "shadow_hours": shadow_hours,
        "shadow_tick_count": len(daily_reports),
        "accelerated_historical_shadow": True,
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "video_required": False,
        "daily_report_refs": [str(report.get("run_dir") or "") for report in daily_reports],
        "blocking_reasons": reasons,
    }


def _combined_replay_shadow_report(
    generated_at: str,
    state: Path,
    replay_report: Mapping[str, Any],
    shadow_report: Mapping[str, Any],
    promotion_report: Mapping[str, Any],
    *,
    write: bool,
) -> dict[str, Any]:
    status = "pass" if replay_report.get("status") == shadow_report.get("status") == promotion_report.get("status") == "pass" else "blocked"
    artifact_paths = {
        "replay_report": str(state / S2P1_REPLAY_REPORT_FILENAME),
        "shadow_report": str(state / S2P1_SHADOW_EVIDENCE_FILENAME),
        "promotion_report": str(state / S2P1_PROMOTION_REPORT_FILENAME),
        "queue": str(state / S2P1_QUEUE_FILENAME),
        "ledger": str(state / S2P1_LEDGER_FILENAME),
    }
    report = {
        "model_id": S2P1_PREPRINT_REPLAY_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "s2p1_source_promotion_accepted": status == "pass",
        "stage2_production_accepted": False,
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "video_generated": False,
        "replay_report": replay_report,
        "shadow_report": shadow_report,
        "promotion_report": promotion_report,
        "artifact_paths": artifact_paths,
        "blocking_reasons": sorted(set([*replay_report.get("blocking_reasons", []), *shadow_report.get("blocking_reasons", []), *promotion_report.get("blocking_reasons", [])])),
    }
    report["validation_errors"] = validate_s2p1_preprint_replay_shadow_report(report) if status == "pass" else []
    if write:
        _write_json(state / S2P1_REPLAY_REPORT_FILENAME, replay_report)
        _write_json(state / S2P1_SHADOW_EVIDENCE_FILENAME, shadow_report)
        _write_json(state / S2P1_PROMOTION_REPORT_FILENAME, promotion_report)
        _write_json(state / "stage2_s2p1_preprint_replay_shadow_report.json", report)
    return report


def _blocked_replay_report(generated_at: str, state: Path, reasons: Sequence[str], *, requested_count: int) -> dict[str, Any]:
    return {
        "model_id": S2P1_PREPRINT_REPLAY_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "blocked",
        "state_dir": str(state),
        "required_replay_count": S2P1_REPLAY_REQUIRED_DATES,
        "requested_replay_count": int(requested_count),
        "replay_count": 0,
        "success_count": 0,
        "unique_date_count": 0,
        "future_leakage_count": 0,
        "duplicate_selected_count": 0,
        "p0_p1_blocker_count": 0,
        "blocking_reasons": list(reasons),
    }


def _replay_dates(*, start_date: str | None, end_date: str | None, count: int, generated_at: str) -> list[Date]:
    if count < 1:
        return []
    if start_date:
        start = _parse_date(start_date)
        return [start + timedelta(days=offset) for offset in range(count)]
    end = _parse_date(end_date) if end_date else _parse_date(str(generated_at)[:10])
    start = end - timedelta(days=count - 1)
    return [start + timedelta(days=offset) for offset in range(count)]


def _parse_date(value: str) -> Date:
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _source_item_preprint_date(item: Mapping[str, Any]) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
    preprint = metadata.get("preprint") if isinstance(metadata.get("preprint"), Mapping) else {}
    raw = str(preprint.get("date") or "").strip()
    return raw[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", raw) else ""


def _duplicate_values(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        elif value:
            seen.add(value)
    return sorted(duplicates)


def _shadow_hours_from_dates(dates: Sequence[str]) -> float:
    parsed = sorted(_parse_date(item[:10]) for item in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", item[:10]))
    if len(parsed) < 2:
        return 0.0
    return float(((parsed[-1] - parsed[0]).days + 1) * 24)


def _is_preprint_source_id(source_id: str) -> bool:
    return source_id.startswith(("biorxiv:", "medrxiv:"))


def _preprint_scan(source_batches: Mapping[str, Mapping[str, Any]], *, generated_at: str) -> dict[str, Any]:
    source_reports: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_candidate_ids: set[str] = set()
    for server in S2P1_REQUIRED_SERVERS:
        batch = source_batches.get(server)
        if not isinstance(batch, Mapping):
            reason = f"{server}: missing preprint source batch"
            source_reports.append({"server": server, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        batch_errors = validate_preprint_source_batch(batch)
        source_reports.append(
            {
                "server": server,
                "status": "blocked" if batch_errors or batch.get("status") == "blocked" else "pass",
                "source_item_count": len(batch.get("source_items") or []),
                "new_item_count": int(batch.get("new_item_count") or 0),
                "blocking_reasons": batch_errors or list(batch.get("blocking_reasons") or []),
            }
        )
        if batch_errors or batch.get("status") == "blocked":
            errors.extend(f"{server}: {reason}" for reason in (batch_errors or batch.get("blocking_reasons") or []))
            continue
        for source_item in batch.get("new_items") or []:
            if not isinstance(source_item, Mapping):
                continue
            candidate, candidate_errors = candidate_from_source_item(source_item, generated_at=generated_at)
            errors.extend(candidate_errors)
            if not candidate:
                continue
            if candidate["source_id"] in seen_candidate_ids:
                continue
            seen_candidate_ids.add(candidate["source_id"])
            candidates.append(candidate)
    blocking_reasons = errors if errors else [] if candidates else ["no eligible new bioRxiv/medRxiv candidates for shadow daily input"]
    return {
        "scan_id": "s2p1-preprint-scan:shadow",
        "model_id": S2P1_PREPRINT_SHADOW_MODEL_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons else "blocked",
        "source_count": len(source_reports),
        "candidate_count": len(candidates),
        "source_reports": source_reports,
        "candidates": candidates,
        "blocking_reasons": blocking_reasons,
    }


def _top_journal_scan(source_batches: Mapping[str, Mapping[str, Any]], *, generated_at: str) -> dict[str, Any]:
    source_reports: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_candidate_ids: set[str] = set()
    for journal in S2P2_REQUIRED_JOURNALS:
        batch = source_batches.get(journal)
        if not isinstance(batch, Mapping):
            reason = f"{journal}: missing top-journal source batch"
            source_reports.append({"journal": journal, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        batch_errors = validate_top_journal_source_batch(batch)
        source_reports.append(
            {
                "journal": journal,
                "status": "blocked" if batch_errors or batch.get("status") == "blocked" else "pass",
                "source_item_count": len(batch.get("source_items") or []),
                "new_item_count": int(batch.get("new_item_count") or 0),
                "blocking_reasons": batch_errors or list(batch.get("blocking_reasons") or []),
            }
        )
        if batch_errors or batch.get("status") == "blocked":
            errors.extend(f"{journal}: {reason}" for reason in (batch_errors or batch.get("blocking_reasons") or []))
            continue
        for source_item in batch.get("new_items") or []:
            if not isinstance(source_item, Mapping):
                continue
            candidate, candidate_errors = candidate_from_source_item(source_item, generated_at=generated_at)
            errors.extend(candidate_errors)
            if not candidate:
                continue
            if candidate["source_id"] in seen_candidate_ids:
                continue
            seen_candidate_ids.add(candidate["source_id"])
            candidates.append(candidate)
    blocking_reasons = errors if errors else [] if candidates else ["no eligible new Nature main-journal candidates for shadow daily input"]
    return {
        "scan_id": "s2p2-top-journal-scan:shadow",
        "model_id": S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons else "blocked",
        "source_count": len(source_reports),
        "candidate_count": len(candidates),
        "source_reports": source_reports,
        "candidates": candidates,
        "blocking_reasons": blocking_reasons,
    }


def _daily_input_from_selection(
    selected: Mapping[str, Any],
    *,
    date: str,
    generated_at: str,
    queue: Mapping[str, Any],
    run_label: str = "s2p1-preprint",
    scan_scope: str = "s2p1_biorxiv_medrxiv_shadow",
    source_count: int = len(S2P1_REQUIRED_SERVERS),
    task_id: str = S2P1_TASK_ID,
) -> dict[str, Any]:
    source_item = dict(selected["source_item"])
    stable_id = _safe_id(str(source_item.get("stable_id") or selected.get("source_id") or "unknown"))
    queue_items = queue.get("items") if isinstance(queue.get("items"), list) else []
    return {
        "run_id": f"daily:{date}:{run_label}:{stable_id}",
        "publication_id": f"pub:daily:{date}:{run_label}:{stable_id}",
        "date": date,
        "generated_at": generated_at,
        "timezone": DEFAULT_TIMEZONE,
        "source_item": source_item,
        "claims": [dict(claim) for claim in selected["evidence_claims"]],
        "selection_audit": {
            "model_id": ROI_RANKING_MODEL_ID,
            "selection_source": selected.get("selection_source", ""),
            "roi_total_score": selected["roi_total_score"],
            "roi_signals": dict(selected["roi_signals"]),
        },
        "scan_summary": {
            "scope": scan_scope,
            "source_count": int(source_count),
        },
        "queue_summary": {
            "queue_model_id": CANDIDATE_QUEUE_MODEL_ID,
            "queued_item_count": len(queue_items),
            "top_queued": [
                {
                    "source_id": item.get("source_id", ""),
                    "title": item.get("title", ""),
                    "roi_total_score": item.get("roi_total_score", 0.0),
                    "primary_category": item.get("primary_category", ""),
                }
                for item in queue_items[:5]
            ],
        },
        "stage2_shadow": {
            "task_id": task_id,
            "formal_production_inclusion": False,
            "real_smtp_allowed": False,
        },
    }


def _blocked_daily_input(
    date: str,
    generated_at: str,
    queue: Mapping[str, Any],
    scan: Mapping[str, Any],
    reasons: Sequence[str],
    *,
    selection: Mapping[str, Any] | None = None,
    model_id: str = S2P1_PREPRINT_SHADOW_MODEL_ID,
    task_id: str = S2P1_TASK_ID,
) -> dict[str, Any]:
    return {
        "model_id": model_id,
        "task_id": task_id,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "blocked",
        "daily_input_ready": False,
        "formal_production_inclusion": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": queue,
        "selection": dict(selection or {"model_id": ROI_RANKING_MODEL_ID, "status": "blocked", "selected": None}),
        "daily_input": {},
        "blocking_reasons": list(reasons),
    }


def _base_shadow_report(
    *,
    status: str,
    date: str,
    generated_at: str,
    state: Path,
    run_dir: Path,
    blocking_reasons: list[str],
    daily_report: Mapping[str, Any],
    model_id: str = S2P1_PREPRINT_SHADOW_MODEL_ID,
    acceptance_id: str = S2P1_ACCEPTANCE_ID,
    task_id: str = S2P1_TASK_ID,
) -> dict[str, Any]:
    return {
        "model_id": model_id,
        "acceptance_id": acceptance_id,
        "task_id": task_id,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": status,
        "state_dir": str(state),
        "run_dir": str(run_dir),
        "daily_input_ready": bool(daily_report.get("daily_input_ready") is True),
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "production_affected": False,
        "video_required": False,
        "daily_report": daily_report,
        "blocking_reasons": blocking_reasons,
    }


def _write_or_return(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_s2p1_shadow_report(normalized)
    if write:
        _write_json(run_dir / "adp-s2p1-preprint-shadow-report.json", normalized)
    return normalized


def _write_or_return_s2p2(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_s2p2_top_journal_shadow_report(normalized)
    if write:
        _write_json(run_dir / "adp-s2p2-top-journal-shadow-report.json", normalized)
    return normalized


def _replay_gate(report: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(report, Mapping):
        return {"status": "blocked", "blocking_reasons": ["S2P1 replay gate missing 30-day terminal replay report"]}
    reasons: list[str] = []
    if report.get("status") != "pass":
        reasons.append("S2P1 replay report is not pass")
    if int(report.get("unique_date_count") or 0) < S2P1_REPLAY_REQUIRED_DATES:
        reasons.append("S2P1 replay requires 30 unique dates")
    if int(report.get("future_leakage_count") or 0) != 0:
        reasons.append("S2P1 replay future_leakage_count must be 0")
    if int(report.get("duplicate_selected_count") or 0) != 0:
        reasons.append("S2P1 replay duplicate_selected_count must be 0")
    if int(report.get("p0_p1_blocker_count") or 0) != 0:
        reasons.append("S2P1 replay P0/P1 blockers must be 0")
    return {"status": "pass" if not reasons else "blocked", "blocking_reasons": reasons}


def _shadow_gate(report: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(report, Mapping):
        return {"status": "blocked", "blocking_reasons": ["S2P1 shadow gate missing 48h shadow report"]}
    reasons: list[str] = []
    if report.get("status") != "pass":
        reasons.append("S2P1 shadow report is not pass")
    if float(report.get("shadow_hours") or 0.0) < S2P1_SHADOW_REQUIRED_HOURS:
        reasons.append("S2P1 shadow requires at least 48 hours")
    if report.get("formal_production_inclusion") is not False:
        reasons.append("S2P1 shadow must not include formal production inclusion")
    if report.get("production_affected") is not False:
        reasons.append("S2P1 shadow must not affect accepted arXiv production")
    return {"status": "pass" if not reasons else "blocked", "blocking_reasons": reasons}


def _license_gate_errors(batch: Mapping[str, Any]) -> list[str]:
    errors = []
    for item in batch.get("source_items") or []:
        if not isinstance(item, Mapping):
            continue
        license_status = str((item.get("license") or {}).get("status") if isinstance(item.get("license"), Mapping) else "")
        if not license_status or license_status == "unknown":
            errors.append(f"{item.get('source_id', 'preprint')}: license metadata missing")
    return errors


def _version_gate_errors(batch: Mapping[str, Any]) -> list[str]:
    errors = []
    for item in batch.get("source_items") or []:
        if not isinstance(item, Mapping):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
        preprint = metadata.get("preprint") if isinstance(metadata.get("preprint"), Mapping) else {}
        if not preprint.get("version"):
            errors.append(f"{item.get('source_id', 'preprint')}: version metadata missing")
    return errors


def _canonical_ids(batch: Mapping[str, Any]) -> list[str]:
    return [_canonical_document_id(item) for item in batch.get("source_items") or [] if isinstance(item, Mapping)]


def _canonical_document_id(item: Mapping[str, Any]) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
    identity = metadata.get("identity") if isinstance(metadata.get("identity"), Mapping) else {}
    return str(identity.get("canonical_document_id") or item.get("source_id") or "")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-") or "unknown"
