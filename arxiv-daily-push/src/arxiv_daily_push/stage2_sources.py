"""Stage 2 source-promotion gates and local shadow artifacts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
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


S2P1_PREPRINT_PROMOTION_MODEL_ID = "adp-s2p1-preprint-source-promotion-v1"
S2P1_PREPRINT_SHADOW_MODEL_ID = "adp-s2p1-preprint-shadow-daily-v1"
S2P1_ACCEPTANCE_ID = "ADP-ACC-S2P1T01-SOURCE-PROMOTION"
S2P1_TASK_ID = "S2P1T01"
S2P1_REQUIRED_SERVERS = ("biorxiv", "medrxiv")
S2P1_REPLAY_REQUIRED_DATES = 30
S2P1_SHADOW_REQUIRED_HOURS = 48
S2P1_QUEUE_FILENAME = "stage2_s2p1_preprint_queue.json"
S2P1_LEDGER_FILENAME = "stage2_s2p1_preprint_ledger.jsonl"


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


def _daily_input_from_selection(selected: Mapping[str, Any], *, date: str, generated_at: str, queue: Mapping[str, Any]) -> dict[str, Any]:
    source_item = dict(selected["source_item"])
    stable_id = _safe_id(str(source_item.get("stable_id") or selected.get("source_id") or "unknown"))
    queue_items = queue.get("items") if isinstance(queue.get("items"), list) else []
    return {
        "run_id": f"daily:{date}:s2p1-preprint:{stable_id}",
        "publication_id": f"pub:daily:{date}:s2p1-preprint:{stable_id}",
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
            "scope": "s2p1_biorxiv_medrxiv_shadow",
            "source_count": len(S2P1_REQUIRED_SERVERS),
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
            "task_id": S2P1_TASK_ID,
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
) -> dict[str, Any]:
    return {
        "model_id": S2P1_PREPRINT_SHADOW_MODEL_ID,
        "task_id": S2P1_TASK_ID,
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
) -> dict[str, Any]:
    return {
        "model_id": S2P1_PREPRINT_SHADOW_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
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
