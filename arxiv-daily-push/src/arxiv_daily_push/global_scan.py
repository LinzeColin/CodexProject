"""Phase 12 all-arXiv scan, ROI ranking, queue, and delivery package gates."""

from __future__ import annotations

import json
import re
import time
from html import escape
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .arxiv_adapter import ArxivQuery
from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE, PROJECT_NAME
from .contracts import stable_content_hash, validate_evidence_claim, validate_source_item
from .notifications import EmailNotification
from .source_ingest import FetchAtom, ingest_latest_arxiv, validate_source_batch


ALL_ARXIV_SCAN_MODEL_ID = "adp-all-arxiv-scan-v1"
CANDIDATE_QUEUE_MODEL_ID = "adp-candidate-queue-v1"
ROI_RANKING_MODEL_ID = "adp-roi-ranking-v1"
MAIL_VIDEO_LINK_MODEL_ID = "adp-mail-video-link-v1"
MAIL_TEXT_DELIVERY_MODEL_ID = "adp-mail-text-delivery-v1"
LIVE_ALL_ARXIV_DRY_RUN_MODEL_ID = "adp-live-all-arxiv-dry-run-v1"
LIVE_ARXIV_TRANSIENT_RETRY_COUNT = 2
LIVE_ARXIV_TRANSIENT_RETRY_DELAY_SECONDS = 20.0

ALL_ARXIV_MAX_RESULTS_PER_CATEGORY = 3
ALL_ARXIV_MAX_TOTAL_CANDIDATES = 120
CANDIDATE_QUEUE_MAX_ITEMS = 40
ROI_NEW_HIGH_VALUE_THRESHOLD = 65.0
ROI_SELECTION_MIN_SCORE = 50.0
ROI_QUEUE_MIN_SCORE = 55.0

ALL_ARXIV_ARCHIVES: tuple[dict[str, str], ...] = (
    {
        "archive_id": "cs",
        "group": "Computer Science",
        "query": "cat:cs.AI OR cat:cs.AR OR cat:cs.CC OR cat:cs.CE OR cat:cs.CG OR cat:cs.CL OR cat:cs.CR OR cat:cs.CV OR cat:cs.CY OR cat:cs.DB OR cat:cs.DC OR cat:cs.DL OR cat:cs.DM OR cat:cs.DS OR cat:cs.ET OR cat:cs.FL OR cat:cs.GL OR cat:cs.GR OR cat:cs.GT OR cat:cs.HC OR cat:cs.IR OR cat:cs.IT OR cat:cs.LG OR cat:cs.LO OR cat:cs.MA OR cat:cs.MM OR cat:cs.MS OR cat:cs.NA OR cat:cs.NE OR cat:cs.NI OR cat:cs.OH OR cat:cs.OS OR cat:cs.PF OR cat:cs.PL OR cat:cs.RO OR cat:cs.SC OR cat:cs.SD OR cat:cs.SE OR cat:cs.SI OR cat:cs.SY",
    },
    {"archive_id": "econ", "group": "Economics", "query": "cat:econ.EM OR cat:econ.GN OR cat:econ.TH"},
    {"archive_id": "eess", "group": "Electrical Engineering and Systems Science", "query": "cat:eess.AS OR cat:eess.IV OR cat:eess.SP OR cat:eess.SY"},
    {
        "archive_id": "math",
        "group": "Mathematics",
        "query": "cat:math.AC OR cat:math.AG OR cat:math.AP OR cat:math.AT OR cat:math.CA OR cat:math.CO OR cat:math.CT OR cat:math.CV OR cat:math.DG OR cat:math.DS OR cat:math.FA OR cat:math.GM OR cat:math.GN OR cat:math.GR OR cat:math.GT OR cat:math.HO OR cat:math.IT OR cat:math.KT OR cat:math.LO OR cat:math.MG OR cat:math.MP OR cat:math.NA OR cat:math.NT OR cat:math.OA OR cat:math.OC OR cat:math.PR OR cat:math.QA OR cat:math.RA OR cat:math.RT OR cat:math.SG OR cat:math.SP OR cat:math.ST",
    },
    {"archive_id": "astro-ph", "group": "Physics", "query": "cat:astro-ph.CO OR cat:astro-ph.EP OR cat:astro-ph.GA OR cat:astro-ph.HE OR cat:astro-ph.IM OR cat:astro-ph.SR"},
    {"archive_id": "cond-mat", "group": "Physics", "query": "cat:cond-mat.dis-nn OR cat:cond-mat.mes-hall OR cat:cond-mat.mtrl-sci OR cat:cond-mat.other OR cat:cond-mat.quant-gas OR cat:cond-mat.soft OR cat:cond-mat.stat-mech OR cat:cond-mat.str-el OR cat:cond-mat.supr-con"},
    {"archive_id": "gr-qc", "group": "Physics", "query": "cat:gr-qc"},
    {"archive_id": "hep-ex", "group": "Physics", "query": "cat:hep-ex"},
    {"archive_id": "hep-lat", "group": "Physics", "query": "cat:hep-lat"},
    {"archive_id": "hep-ph", "group": "Physics", "query": "cat:hep-ph"},
    {"archive_id": "hep-th", "group": "Physics", "query": "cat:hep-th"},
    {"archive_id": "math-ph", "group": "Physics", "query": "cat:math-ph"},
    {"archive_id": "nlin", "group": "Physics", "query": "cat:nlin.AO OR cat:nlin.CD OR cat:nlin.CG OR cat:nlin.PS OR cat:nlin.SI"},
    {"archive_id": "nucl-ex", "group": "Physics", "query": "cat:nucl-ex"},
    {"archive_id": "nucl-th", "group": "Physics", "query": "cat:nucl-th"},
    {
        "archive_id": "physics",
        "group": "Physics",
        "query": "cat:physics.acc-ph OR cat:physics.app-ph OR cat:physics.atm-clus OR cat:physics.atom-ph OR cat:physics.bio-ph OR cat:physics.chem-ph OR cat:physics.class-ph OR cat:physics.comp-ph OR cat:physics.data-an OR cat:physics.flu-dyn OR cat:physics.gen-ph OR cat:physics.geo-ph OR cat:physics.hist-ph OR cat:physics.ins-det OR cat:physics.med-ph OR cat:physics.optics OR cat:physics.plasm-ph OR cat:physics.pop-ph OR cat:physics.soc-ph OR cat:physics.space-ph",
    },
    {"archive_id": "quant-ph", "group": "Physics", "query": "cat:quant-ph"},
    {"archive_id": "q-bio", "group": "Quantitative Biology", "query": "cat:q-bio.BM OR cat:q-bio.CB OR cat:q-bio.GN OR cat:q-bio.MN OR cat:q-bio.NC OR cat:q-bio.OT OR cat:q-bio.PE OR cat:q-bio.QM OR cat:q-bio.SC OR cat:q-bio.TO"},
    {"archive_id": "q-fin", "group": "Quantitative Finance", "query": "cat:q-fin.CP OR cat:q-fin.EC OR cat:q-fin.GN OR cat:q-fin.MF OR cat:q-fin.PM OR cat:q-fin.PR OR cat:q-fin.RM OR cat:q-fin.ST OR cat:q-fin.TR"},
    {"archive_id": "stat", "group": "Statistics", "query": "cat:stat.AP OR cat:stat.CO OR cat:stat.ME OR cat:stat.ML OR cat:stat.OT OR cat:stat.TH"},
)

ROI_COMPONENT_WEIGHTS: dict[str, float] = {
    "relevance": 20.0,
    "learning_value": 20.0,
    "economic_conversion_rate": 20.0,
    "roi": 20.0,
    "interdisciplinary_value": 10.0,
    "explainability": 10.0,
}

_ARXIV_GROUP_LABELS: dict[str, str] = {
    "astro-ph": "Astrophysics",
    "cond-mat": "Condensed Matter",
    "cs": "Computer Science",
    "econ": "Economics",
    "eess": "Electrical Engineering",
    "gr-qc": "General Relativity",
    "hep-ex": "High Energy Physics",
    "hep-lat": "High Energy Physics",
    "hep-ph": "High Energy Physics",
    "hep-th": "High Energy Physics",
    "math": "Mathematics",
    "math-ph": "Mathematical Physics",
    "nlin": "Nonlinear Sciences",
    "nucl-ex": "Nuclear Physics",
    "nucl-th": "Nuclear Physics",
    "physics": "Physics",
    "q-bio": "Quant Biology",
    "q-fin": "Quant Finance",
    "quant-ph": "Quant Physics",
    "stat": "Statistics",
}

_RELEVANCE_KEYWORDS = (
    "agent",
    "artificial intelligence",
    "benchmark",
    "control",
    "data",
    "decision",
    "finance",
    "foundation model",
    "language model",
    "learning",
    "market",
    "optimization",
    "policy",
    "risk",
    "robot",
    "simulation",
    "statistics",
)
_LEARNING_KEYWORDS = (
    "algorithm",
    "benchmark",
    "dataset",
    "evaluation",
    "framework",
    "method",
    "model",
    "survey",
    "theory",
)
_ECONOMIC_KEYWORDS = (
    "automation",
    "cost",
    "efficiency",
    "energy",
    "finance",
    "health",
    "market",
    "optimization",
    "portfolio",
    "privacy",
    "risk",
    "security",
    "supply",
    "trading",
)


def build_all_arxiv_scan_plan(
    *,
    max_results_per_category: int = ALL_ARXIV_MAX_RESULTS_PER_CATEGORY,
    archives: Sequence[Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    selected_archives = [dict(item) for item in (archives or ALL_ARXIV_ARCHIVES)]
    return {
        "plan_id": "all-arxiv-scan:primary-archives",
        "model_id": ALL_ARXIV_SCAN_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "scope": "all_arxiv_primary_archives",
        "legacy_single_category_query_forbidden": "cat:cs.AI",
        "max_results_per_category": int(max_results_per_category),
        "archive_count": len(selected_archives),
        "group_count": len({item.get("group") for item in selected_archives}),
        "archives": selected_archives,
        "source_policy": {
            "network_fetch_enabled": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "per_archive_latest_window": True,
            "queue_fallback_enabled": True,
        },
    }


def validate_all_arxiv_scan_plan(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("model_id") != ALL_ARXIV_SCAN_MODEL_ID:
        errors.append("all-arxiv scan plan model_id must be adp-all-arxiv-scan-v1")
    archives = plan.get("archives")
    if not isinstance(archives, list) or not archives:
        errors.append("all-arxiv scan plan requires archives")
        return errors
    archive_ids = {str(item.get("archive_id") or "") for item in archives if isinstance(item, Mapping)}
    missing = sorted(set(_required_archive_ids()) - archive_ids)
    if missing:
        errors.append("all-arxiv scan plan missing required archives: " + ", ".join(missing))
    if archive_ids == {"cs.AI"} or {str(item.get("query") or "") for item in archives if isinstance(item, Mapping)} == {"cat:cs.AI"}:
        errors.append("all-arxiv scan plan must not collapse to cat:cs.AI")
    if int(plan.get("max_results_per_category") or 0) < 1:
        errors.append("max_results_per_category must be positive")
    policy = plan.get("source_policy")
    if not isinstance(policy, Mapping):
        errors.append("all-arxiv scan plan source_policy is required")
    else:
        if policy.get("pdf_download_enabled") is not False:
            errors.append("all-arxiv scan must not download PDFs")
        if policy.get("bulk_harvest_enabled") is not False:
            errors.append("all-arxiv scan must not bulk harvest")
    return errors


def build_all_arxiv_daily_input(
    *,
    date: str,
    generated_at: str,
    timezone: str = DEFAULT_TIMEZONE,
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Iterable[str] = (),
    max_results_per_category: int = ALL_ARXIV_MAX_RESULTS_PER_CATEGORY,
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
    fetcher: FetchAtom | None = None,
    source_batches: Mapping[str, Mapping[str, Any]] | None = None,
    artifact_dir: str | Path | None = None,
    queue_output_path: str | Path | None = None,
    polite_delay_seconds: float = 0.0,
    transient_retry_count: int = LIVE_ARXIV_TRANSIENT_RETRY_COUNT,
    transient_retry_delay_seconds: float = LIVE_ARXIV_TRANSIENT_RETRY_DELAY_SECONDS,
) -> dict[str, Any]:
    """Build one all-arXiv daily input plus queue and delivery artifacts."""

    plan = build_all_arxiv_scan_plan(max_results_per_category=max_results_per_category)
    plan_errors = validate_all_arxiv_scan_plan(plan)
    if plan_errors:
        return _blocked_daily_report(date, generated_at, timezone, plan, [plan_errors[0]])

    recent = {str(item) for item in recent_source_ids if str(item)}
    scan = _scan_archives(
        plan,
        generated_at=generated_at,
        recent_source_ids=recent,
        fetcher=fetcher,
        source_batches=source_batches,
        polite_delay_seconds=polite_delay_seconds,
        transient_retry_count=transient_retry_count,
        transient_retry_delay_seconds=transient_retry_delay_seconds,
    )
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    scan_blockers = _daily_scan_blockers(scan)
    if scan_blockers:
        report = _blocked_daily_report(date, generated_at, timezone, plan, scan_blockers)
        report["scan"] = scan
        report["candidate_queue"] = queue_state
        report["selection"] = {
            "model_id": ROI_RANKING_MODEL_ID,
            "status": "blocked",
            "selected": None,
            "blocking_reasons": scan_blockers,
        }
        return report
    new_candidates = scan["candidates"]
    queued_candidates = [dict(item) for item in queue_state["items"]]
    selection = select_roi_candidate(new_candidates, queued_candidates, recent_source_ids=recent)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        report = _blocked_daily_report(date, generated_at, timezone, plan, list(selection.get("blocking_reasons") or []))
        report["scan"] = scan
        report["candidate_queue"] = queue_state
        report["selection"] = selection
        return report

    updated_queue = update_candidate_queue(
        existing_items=queued_candidates,
        new_candidates=new_candidates,
        selected_source_id=str(selected["source_id"]),
        generated_at=generated_at,
        max_items=max_queue_items,
    )
    daily_input = _daily_input_from_selection(selected, date=date, generated_at=generated_at, timezone=timezone, scan=scan, queue=updated_queue)
    report = {
        "builder_id": f"all-arxiv-daily-input:{date}",
        "model_id": ALL_ARXIV_SCAN_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": timezone,
        "status": "pass",
        "daily_input_ready": True,
        "scan_plan": plan,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "delivery_requirements": _delivery_requirements(),
        "artifact_paths": {},
        "blocking_reasons": [],
    }
    if artifact_dir:
        report["artifact_paths"] = write_phase12_artifacts(report, artifact_dir)
    if queue_output_path:
        Path(queue_output_path).write_text(json.dumps(updated_queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def build_live_all_arxiv_dry_run(
    *,
    generated_at: str,
    date: str | None = None,
    max_results_per_category: int = 1,
    fetcher: FetchAtom | None = None,
    source_batches: Mapping[str, Mapping[str, Any]] | None = None,
    artifact_dir: str | Path | None = None,
    polite_delay_seconds: float = 0.0,
    transient_retry_count: int = LIVE_ARXIV_TRANSIENT_RETRY_COUNT,
    transient_retry_delay_seconds: float = LIVE_ARXIV_TRANSIENT_RETRY_DELAY_SECONDS,
) -> dict[str, Any]:
    """Run a live all-arXiv fetchability dry-run for every primary archive."""

    plan = build_all_arxiv_scan_plan(max_results_per_category=max_results_per_category)
    plan_errors = validate_all_arxiv_scan_plan(plan)
    if plan_errors:
        return {
            "dry_run_id": "live-all-arxiv-dry-run:blocked",
            "model_id": LIVE_ALL_ARXIV_DRY_RUN_MODEL_ID,
            "project_id": "arxiv-daily-push",
            "generated_at": generated_at,
            "status": "blocked",
            "live_dry_run_ready": False,
            "scan_plan": plan,
            "scan": {},
            "archive_count": len(plan.get("archives") or []),
            "verified_archive_count": 0,
            "failed_archive_count": len(plan.get("archives") or []),
            "blocking_reasons": plan_errors,
            "sample_daily_input": {},
            "artifact_paths": {},
        }
    scan = _scan_archives(
        plan,
        generated_at=generated_at,
        recent_source_ids=set(),
        fetcher=fetcher,
        source_batches=source_batches,
        polite_delay_seconds=polite_delay_seconds,
        transient_retry_count=transient_retry_count,
        transient_retry_delay_seconds=transient_retry_delay_seconds,
    )
    category_reports = scan.get("category_reports") if isinstance(scan.get("category_reports"), list) else []
    verified = [item for item in category_reports if isinstance(item, Mapping) and item.get("status") == "pass" and int(item.get("new_item_count") or 0) > 0]
    failed = [item for item in category_reports if item not in verified]
    ready = len(verified) == len(ALL_ARXIV_ARCHIVES) and not failed
    sample_daily_input: dict[str, Any] = {}
    sample_reasons: list[str] = []
    if ready:
        selection = select_roi_candidate(scan.get("candidates") or [], [], recent_source_ids=set())
        selected = selection.get("selected")
        if isinstance(selected, Mapping):
            queue = update_candidate_queue(
                existing_items=[],
                new_candidates=scan.get("candidates") or [],
                selected_source_id=str(selected.get("source_id") or ""),
                generated_at=generated_at,
            )
            sample_daily_input = _daily_input_from_selection(
                selected,
                date=str(date or generated_at[:10]),
                generated_at=generated_at,
                timezone=DEFAULT_TIMEZONE,
                scan=scan,
                queue=queue,
            )
        else:
            sample_reasons = list(selection.get("blocking_reasons") or ["live dry-run could not select a sample daily input"])
            ready = False
    report: dict[str, Any] = {
        "dry_run_id": "live-all-arxiv-dry-run:primary-archives",
        "model_id": LIVE_ALL_ARXIV_DRY_RUN_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "live_dry_run_ready": ready,
        "scan_plan": plan,
        "scan": scan,
        "archive_count": len(category_reports),
        "verified_archive_count": len(verified),
        "failed_archive_count": len(failed),
        "max_results_per_category": int(max_results_per_category),
        "pdf_download_enabled": False,
        "bulk_harvest_enabled": False,
        "production_schedule_enabled": False,
        "smtp_send_enabled": False,
        "release_upload_enabled": False,
        "transient_retry_count": int(transient_retry_count),
        "transient_retry_delay_seconds": float(transient_retry_delay_seconds),
        "sample_daily_input": sample_daily_input,
        "blocking_reasons": _live_dry_run_blockers(failed) + sample_reasons,
        "artifact_paths": {},
    }
    if artifact_dir:
        directory = Path(artifact_dir)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "adp-live-all-arxiv-dry-run.json"
        daily_input_path = directory / "adp-live-daily-input.json"
        if sample_daily_input:
            daily_input_path.write_text(json.dumps(sample_daily_input, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            report["artifact_paths"]["sample_daily_input"] = str(daily_input_path)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["artifact_paths"]["live_all_arxiv_dry_run"] = str(path)
    return report


def validate_live_all_arxiv_dry_run_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != LIVE_ALL_ARXIV_DRY_RUN_MODEL_ID:
        errors.append("live all-arXiv dry-run model_id must be adp-live-all-arxiv-dry-run-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("live all-arXiv dry-run status must be pass or blocked")
    if int(report.get("archive_count") or 0) != len(ALL_ARXIV_ARCHIVES):
        errors.append("live all-arXiv dry-run must cover all 20 primary archives")
    for key in ("pdf_download_enabled", "bulk_harvest_enabled", "production_schedule_enabled", "smtp_send_enabled", "release_upload_enabled"):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for live all-arXiv dry-run")
    if report.get("live_dry_run_ready") is True:
        if int(report.get("verified_archive_count") or 0) != len(ALL_ARXIV_ARCHIVES):
            errors.append("ready live dry-run requires 20 verified archives")
        if int(report.get("failed_archive_count") or 0) != 0:
            errors.append("ready live dry-run requires failed_archive_count 0")
        if report.get("blocking_reasons"):
            errors.append("ready live dry-run cannot include blocking_reasons")
        if not isinstance(report.get("sample_daily_input"), Mapping) or not report.get("sample_daily_input"):
            errors.append("ready live dry-run requires sample_daily_input")
    else:
        if not report.get("blocking_reasons"):
            errors.append("blocked live dry-run requires blocking_reasons")
    return errors


def validate_all_arxiv_daily_input_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != ALL_ARXIV_SCAN_MODEL_ID:
        errors.append("all-arxiv daily report model_id must be adp-all-arxiv-scan-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("all-arxiv daily report status must be pass or blocked")
    errors.extend(validate_all_arxiv_scan_plan(report.get("scan_plan") if isinstance(report.get("scan_plan"), Mapping) else {}))
    requirements = report.get("delivery_requirements")
    if isinstance(requirements, Mapping):
        if requirements.get("email_chinese_lesson_required") is not True:
            errors.append("Stage 1 email must require Chinese lesson text")
        if requirements.get("candidate_queue_summary_required") is not True:
            errors.append("Stage 1 email must require candidate queue summary")
        if requirements.get("email_video_link_required") is not False:
            errors.append("Stage 1 email must not require a video link")
        if requirements.get("video_generation_required") is not False:
            errors.append("Stage 1 must not require video generation")
        if requirements.get("video_attachment_allowed") is not False:
            errors.append("Stage 1 must forbid video email attachments")
    elif report.get("status") == "pass":
        errors.append("passing all-arxiv daily report requires delivery_requirements")
    if report.get("status") == "blocked":
        if report.get("daily_input_ready") is not False:
            errors.append("blocked all-arxiv daily report requires daily_input_ready false")
        if not report.get("blocking_reasons"):
            errors.append("blocked all-arxiv daily report requires blocking_reasons")
        return errors
    if report.get("daily_input_ready") is not True:
        errors.append("passing all-arxiv daily report requires daily_input_ready true")
    daily_input = report.get("daily_input")
    if not isinstance(daily_input, Mapping):
        errors.append("passing all-arxiv daily report requires daily_input")
        return errors
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
    queue_summary = daily_input.get("queue_summary")
    if not isinstance(queue_summary, Mapping):
        errors.append("daily_input.queue_summary is required")
    return errors


def candidate_from_source_item(source_item: Mapping[str, Any], *, generated_at: str) -> tuple[dict[str, Any] | None, list[str]]:
    """Convert a validated SourceItem into a ranked candidate for queue previews."""

    return _candidate_from_source_item(source_item, generated_at=generated_at)


def normalize_candidate_queue(queue: Mapping[str, Any] | None, *, generated_at: str) -> dict[str, Any]:
    raw_items = queue.get("items") if isinstance(queue, Mapping) else []
    items = []
    if isinstance(raw_items, list):
        for item in raw_items:
            if not isinstance(item, Mapping):
                continue
            source_item = item.get("source_item")
            claims = item.get("evidence_claims")
            if not isinstance(source_item, Mapping) or validate_source_item(source_item):
                continue
            if not isinstance(claims, list) or any(validate_evidence_claim(claim) for claim in claims if isinstance(claim, Mapping)):
                continue
            normalized = dict(item)
            normalized["queue_status"] = "queued"
            normalized["carried_count"] = int(normalized.get("carried_count") or 0)
            normalized.setdefault("first_seen_at", generated_at)
            normalized.setdefault("last_seen_at", generated_at)
            items.append(normalized)
    return {
        "queue_id": "adp-candidate-queue",
        "model_id": CANDIDATE_QUEUE_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "updated_at": generated_at,
        "max_items": CANDIDATE_QUEUE_MAX_ITEMS,
        "items": _sort_candidates(items)[:CANDIDATE_QUEUE_MAX_ITEMS],
    }


def select_roi_candidate(
    new_candidates: Sequence[Mapping[str, Any]],
    queued_candidates: Sequence[Mapping[str, Any]],
    *,
    recent_source_ids: Iterable[str] = (),
) -> dict[str, Any]:
    recent = {str(item) for item in recent_source_ids if str(item)}
    eligible_new = [dict(item) for item in new_candidates if item.get("source_id") not in recent]
    eligible_queue = [dict(item) for item in queued_candidates if item.get("source_id") not in recent]
    ranked_new = _sort_candidates(eligible_new)
    ranked_queue = _sort_candidates(eligible_queue)
    best_new = ranked_new[0] if ranked_new else None
    best_queue = ranked_queue[0] if ranked_queue else None
    selected: dict[str, Any] | None = None
    reason = ""
    if best_new and float(best_new["roi_total_score"]) >= ROI_NEW_HIGH_VALUE_THRESHOLD:
        selected = dict(best_new)
        selected["selection_source"] = "new_scan"
        reason = "new candidate passes high-value ROI threshold"
    elif best_queue and float(best_queue["roi_total_score"]) >= ROI_QUEUE_MIN_SCORE:
        selected = dict(best_queue)
        selected["selection_source"] = "candidate_queue"
        reason = "no new high-value candidate; consuming queued high-value candidate"
    elif best_new and float(best_new["roi_total_score"]) >= ROI_SELECTION_MIN_SCORE:
        selected = dict(best_new)
        selected["selection_source"] = "new_scan_below_high_value_no_queue"
        reason = "new candidate passes minimum score and queue fallback is unavailable"
    if selected:
        return {
            "model_id": ROI_RANKING_MODEL_ID,
            "status": "pass",
            "selected": selected,
            "selection_reason": reason,
            "new_candidate_count": len(ranked_new),
            "queued_candidate_count": len(ranked_queue),
            "audits": ranked_new + ranked_queue,
            "thresholds": _thresholds(),
            "blocking_reasons": [],
        }
    return {
        "model_id": ROI_RANKING_MODEL_ID,
        "status": "blocked",
        "selected": None,
        "new_candidate_count": len(ranked_new),
        "queued_candidate_count": len(ranked_queue),
        "audits": ranked_new + ranked_queue,
        "thresholds": _thresholds(),
        "blocking_reasons": ["no new or queued candidate met the minimum ROI selection threshold"],
    }


def update_candidate_queue(
    *,
    existing_items: Sequence[Mapping[str, Any]],
    new_candidates: Sequence[Mapping[str, Any]],
    selected_source_id: str,
    generated_at: str,
    max_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    by_source: dict[str, dict[str, Any]] = {}
    for item in existing_items:
        source_id = str(item.get("source_id") or "")
        if not source_id or source_id == selected_source_id:
            continue
        queued = dict(item)
        queued["queue_status"] = "queued"
        queued["carried_count"] = int(queued.get("carried_count") or 0) + 1
        queued["last_seen_at"] = generated_at
        by_source[source_id] = queued
    for candidate in new_candidates:
        source_id = str(candidate.get("source_id") or "")
        if not source_id or source_id == selected_source_id:
            continue
        if float(candidate.get("roi_total_score") or 0.0) < ROI_QUEUE_MIN_SCORE:
            continue
        queued = dict(candidate)
        queued["queue_status"] = "queued"
        queued["queue_reason"] = "high_value_not_selected_today"
        queued["first_seen_at"] = generated_at
        queued["last_seen_at"] = generated_at
        queued["carried_count"] = 0
        by_source[source_id] = queued
    return {
        "queue_id": "adp-candidate-queue",
        "model_id": CANDIDATE_QUEUE_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "updated_at": generated_at,
        "max_items": int(max_items),
        "items": _sort_candidates(by_source.values())[: int(max_items)],
    }


def write_phase12_artifacts(report: Mapping[str, Any], artifact_dir: str | Path) -> dict[str, str]:
    directory = Path(artifact_dir)
    directory.mkdir(parents=True, exist_ok=True)
    daily_input_path = directory / "adp-daily-input.json"
    queue_path = directory / "adp-candidate-queue.json"
    delivery_policy_path = directory / "adp-text-delivery-policy.json"
    email_path = directory / "adp-email-brief.json"
    daily_input_path.write_text(json.dumps(report["daily_input"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    queue_path.write_text(json.dumps(report["candidate_queue"], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    delivery_policy = {
        "policy_id": f"text-delivery:{stable_content_hash({'date': report['date'], 'generated_at': report['generated_at']})[:16]}",
        "model_id": MAIL_TEXT_DELIVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": report["generated_at"],
        "recipient": DEFAULT_RECIPIENT,
        "delivery_channel": "email",
        "must_include_chinese_lesson": True,
        "must_include_candidate_queue_summary": True,
        "video_required": False,
        "video_generation_required": False,
        "email_video_link_required": False,
        "release_required": False,
        "video_attachment_allowed": False,
        "artifact_storage": "github_actions_artifacts",
    }
    delivery_policy_path.write_text(json.dumps(delivery_policy, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    email_brief = {
        "model_id": MAIL_TEXT_DELIVERY_MODEL_ID,
        "recipient": DEFAULT_RECIPIENT,
        "date": report["date"],
        "selected_title": report["daily_input"]["source_item"]["title"],
        "must_include_chinese_lesson": True,
        "must_include_video_link": False,
        "video_attachment_allowed": False,
        "candidate_queue_summary": report["daily_input"]["queue_summary"],
    }
    email_path.write_text(json.dumps(email_brief, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "daily_input": str(daily_input_path),
        "candidate_queue": str(queue_path),
        "delivery_policy": str(delivery_policy_path),
        "email_brief": str(email_path),
    }


def build_video_artifact_manifest(daily_input: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    source_item = daily_input.get("source_item") if isinstance(daily_input.get("source_item"), Mapping) else {}
    return {
        "artifact_id": f"video-artifact:{stable_content_hash({'source_id': source_item.get('source_id'), 'generated_at': generated_at})[:16]}",
        "model_id": MAIL_VIDEO_LINK_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "artifact_type": "video_manifest",
        "mp4_rendered": False,
        "render_mode": "phase12_video_artifact_manifest",
        "source_id": source_item.get("source_id", ""),
        "title": source_item.get("title", ""),
        "video_attachment_allowed": False,
        "release_storage_required": "github_release",
        "notes": "Phase 12 publishes a video artifact manifest through GitHub Release before real MP4 rendering is enabled.",
    }


def build_daily_delivery_package(
    daily_run_payload: Mapping[str, Any],
    daily_input: Mapping[str, Any],
    release_report: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    links = release_links(release_report)
    lesson = daily_run_payload.get("lesson") if isinstance(daily_run_payload.get("lesson"), Mapping) else {}
    queue_summary = daily_input.get("queue_summary") if isinstance(daily_input.get("queue_summary"), Mapping) else {}
    notification = _daily_email(lesson, daily_input, links, queue_summary, generated_at=generated_at)
    return {
        "model_id": MAIL_TEXT_DELIVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "recipient": DEFAULT_RECIPIENT,
        "release_url": links["release_url"],
        "video_url": links["video_url"],
        "video_link_ready": False,
        "video_required": False,
        "video_generation_required": False,
        "release_required": False,
        "email_contains_chinese_lesson": _lesson_has_chinese_text(lesson),
        "email_contains_video_link": False,
        "email_contains_candidate_queue_summary": bool(queue_summary),
        "email_contains_release_landing_link": False,
        "email_contains_html": bool(notification.html_body),
        "video_attachment_allowed": False,
        "notification": notification,
    }


def release_links(release_report: Mapping[str, Any]) -> dict[str, str]:
    if release_report.get("status") != "created" or not release_report.get("release_ref"):
        return {"release_url": "", "video_url": ""}
    repo = str(release_report.get("repo") or "")
    tag = str(release_report.get("tag") or "")
    release_url = f"https://github.com/{repo}/releases/tag/{tag}" if repo and tag else ""
    asset_names = [str(asset.get("name") or "") for asset in release_report.get("assets") or [] if isinstance(asset, Mapping)]
    video_name = next((name for name in asset_names if name.lower().endswith(".mp4")), "")
    video_url = f"https://github.com/{repo}/releases/download/{tag}/{video_name}" if repo and tag and video_name else ""
    return {"release_url": release_url, "video_url": video_url}


def _scan_archives(
    plan: Mapping[str, Any],
    *,
    generated_at: str,
    recent_source_ids: set[str],
    fetcher: FetchAtom | None,
    source_batches: Mapping[str, Mapping[str, Any]] | None,
    polite_delay_seconds: float = 0.0,
    transient_retry_count: int = 0,
    transient_retry_delay_seconds: float = 0.0,
) -> dict[str, Any]:
    category_reports: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    candidate_errors: list[str] = []
    seen_candidate_ids: set[str] = set()
    archives = list(plan["archives"])
    for index, archive in enumerate(archives):
        archive_id = str(archive["archive_id"])
        query = str(archive["query"])
        retry_attempts = 0
        if source_batches and archive_id in source_batches:
            batch = dict(source_batches[archive_id])
        else:
            while True:
                batch = ingest_latest_arxiv(
                    search_query=query,
                    generated_at=generated_at,
                    max_results=int(plan["max_results_per_category"]),
                    seen_source_ids=recent_source_ids,
                    fetcher=_archive_fetcher(fetcher),
                )
                if retry_attempts >= int(transient_retry_count) or not _transient_source_batch_block(batch):
                    break
                retry_attempts += 1
                if transient_retry_delay_seconds > 0:
                    time.sleep(float(transient_retry_delay_seconds))
        batch_errors = validate_source_batch(batch)
        hard_blocked = bool(batch_errors) or (batch.get("status") == "blocked" and not _only_no_unseen(batch))
        category_reports.append(
            {
                "archive_id": archive_id,
                "group": archive["group"],
                "query": query,
                "status": "blocked" if hard_blocked else "pass",
                "new_item_count": int(batch.get("new_item_count") or 0),
                "retry_attempts": retry_attempts,
                "blocking_reasons": batch_errors or list(batch.get("blocking_reasons") or []),
            }
        )
        if hard_blocked:
            continue
        for item in batch.get("new_items") or []:
            if not isinstance(item, Mapping):
                continue
            candidate, errors = _candidate_from_source_item(item, generated_at=generated_at)
            candidate_errors.extend(errors)
            if not candidate:
                continue
            source_id = candidate["source_id"]
            if source_id in seen_candidate_ids:
                continue
            seen_candidate_ids.add(source_id)
            candidates.append(candidate)
        if not source_batches and polite_delay_seconds > 0 and index < len(archives) - 1:
            time.sleep(float(polite_delay_seconds))
    blocked_categories = [item for item in category_reports if item["status"] == "blocked"]
    return {
        "scan_id": "all-arxiv-scan:latest",
        "model_id": ALL_ARXIV_SCAN_MODEL_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocked_categories else "blocked",
        "archive_count": len(category_reports),
        "blocked_archive_count": len(blocked_categories),
        "category_reports": category_reports,
        "candidate_count": len(candidates),
        "candidates": _sort_candidates(candidates)[:ALL_ARXIV_MAX_TOTAL_CANDIDATES],
        "candidate_errors": candidate_errors,
    }


def _transient_source_batch_block(batch: Mapping[str, Any]) -> bool:
    if batch.get("status") != "blocked":
        return False
    text = " ".join(str(reason) for reason in (batch.get("blocking_reasons") or []))
    transient_markers = (
        "HTTP Error 429",
        "Too Many Requests",
        "timed out",
        "temporarily unavailable",
        "Remote end closed connection",
    )
    return any(marker.lower() in text.lower() for marker in transient_markers)


def _daily_scan_blockers(scan: Mapping[str, Any]) -> list[str]:
    if scan.get("status") != "blocked":
        return []
    reasons: list[str] = []
    for item in scan.get("category_reports") or []:
        if not isinstance(item, Mapping) or item.get("status") != "blocked":
            continue
        archive_id = str(item.get("archive_id") or "unknown")
        detail = "; ".join(str(reason) for reason in item.get("blocking_reasons") or [] if str(reason))
        reasons.append(f"all-arxiv scan blocked: {archive_id}: {detail or 'source fetch failed'}")
    return reasons or ["all-arxiv scan blocked before ROI selection"]


def _candidate_from_source_item(source_item: Mapping[str, Any], *, generated_at: str) -> tuple[dict[str, Any] | None, list[str]]:
    errors = validate_source_item(source_item)
    source_id = str(source_item.get("source_id") or "")
    profile = _source_profile(source_item)
    summary = profile["summary"]
    if not summary:
        errors.append(f"{source_id or 'source item'} missing source abstract/summary")
    if errors:
        return None, errors
    claims = _claims_from_source_item(source_item, profile=profile, generated_at=generated_at)
    signals = _roi_signals(source_item, profile=profile)
    total = round(sum(float(signals[name]) * weight for name, weight in ROI_COMPONENT_WEIGHTS.items()), 4)
    return (
        {
            "candidate_id": f"candidate:{source_id}",
            "source_id": source_id,
            "stable_id": source_item.get("stable_id", ""),
            "title": source_item.get("title", ""),
            "canonical_url": source_item.get("canonical_url", ""),
            "primary_category": profile["primary_category"],
            "categories": profile["categories"],
            "source_item": dict(source_item),
            "evidence_claims": claims,
            "roi_signals": signals,
            "roi_component_weights": dict(ROI_COMPONENT_WEIGHTS),
            "roi_total_score": total,
            "score_model_id": ROI_RANKING_MODEL_ID,
        },
        [],
    )


def _live_dry_run_blockers(failed: Sequence[Mapping[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for item in failed:
        archive_id = str(item.get("archive_id") or "unknown")
        detail = "; ".join(str(reason) for reason in item.get("blocking_reasons") or [])
        count = int(item.get("new_item_count") or 0)
        if detail:
            reasons.append(f"{archive_id}: {detail}")
        elif count <= 0:
            reasons.append(f"{archive_id}: no live SourceItems returned")
        else:
            reasons.append(f"{archive_id}: live archive verification failed")
    return reasons


def _claims_from_source_item(source_item: Mapping[str, Any], *, profile: Mapping[str, Any], generated_at: str) -> list[dict[str, Any]]:
    source_id = str(source_item["source_id"])
    stable_url = str(source_item["canonical_url"])
    summary = str(profile.get("summary") or "")
    primary_category = str(profile.get("primary_category") or "")
    source_label = str(profile.get("source_label") or "source")
    summary_section = str(profile.get("summary_section") or "abstract")
    category_section = str(profile.get("category_section") or "metadata")
    claims = [
        {
            "claim_id": f"claim:{source_id}:abstract-summary",
            "source_id": source_id,
            "claim_type": "author_claim",
            "priority": "P0",
            "statement": f"The {source_label} abstract/summary states: {summary}",
            "locator": {
                "locator_type": "abstract",
                "stable_url": stable_url,
                "section": summary_section,
                "quote": summary,
            },
            "support_status": "supported",
            "extracted_at": generated_at,
            "notes": f"Generated from {source_label} metadata; not a peer-review, PDF, full-text, or independent result claim.",
        }
    ]
    if primary_category:
        claims.append(
            {
                "claim_id": f"claim:{source_id}:primary-category",
                "source_id": source_id,
                "claim_type": "metadata",
                "priority": "P1",
                "statement": f"The {source_label} metadata lists primary category {primary_category}.",
                "locator": {
                    "locator_type": "metadata",
                    "stable_url": stable_url,
                    "section": category_section,
                    "quote": primary_category,
                },
                "support_status": "supported",
                "extracted_at": generated_at,
            }
        )
    return claims


def _roi_signals(source_item: Mapping[str, Any], *, profile: Mapping[str, Any]) -> dict[str, float]:
    summary = str(profile.get("summary") or "")
    categories = [str(category) for category in profile.get("categories") or [] if category]
    primary = str(profile.get("primary_category") or "")
    text = " ".join([str(source_item.get("title") or ""), summary, " ".join(categories), primary]).lower()
    relevance = min(1.0, 0.35 + _keyword_score(text, _RELEVANCE_KEYWORDS, per_hit=0.08))
    learning = min(1.0, 0.40 + _keyword_score(text, _LEARNING_KEYWORDS, per_hit=0.07) + _length_bonus(summary))
    economic = min(1.0, 0.25 + _keyword_score(text, _ECONOMIC_KEYWORDS, per_hit=0.09))
    interdisciplinary = min(1.0, 0.35 + 0.15 * max(0, len(set(_category_groups(categories + [primary]))) - 1) + 0.08 * max(0, len(set(categories)) - 1))
    explainability = min(1.0, 0.40 + _length_bonus(summary) + (0.15 if len(summary.split()) <= 260 else 0.0))
    if profile.get("source_family") == "top_journal":
        relevance = max(relevance, 0.62)
        learning = max(learning, 0.64)
        interdisciplinary = max(interdisciplinary, 0.62)
        explainability = max(explainability, 0.62)
    roi = min(1.0, 0.45 * economic + 0.25 * relevance + 0.15 * learning + 0.15 * explainability)
    return {
        "relevance": round(relevance, 4),
        "learning_value": round(learning, 4),
        "economic_conversion_rate": round(economic, 4),
        "roi": round(roi, 4),
        "interdisciplinary_value": round(interdisciplinary, 4),
        "explainability": round(explainability, 4),
    }


def _daily_input_from_selection(
    selected: Mapping[str, Any],
    *,
    date: str,
    generated_at: str,
    timezone: str,
    scan: Mapping[str, Any],
    queue: Mapping[str, Any],
) -> dict[str, Any]:
    source_item = dict(selected["source_item"])
    stable_id = _safe_id(str(source_item.get("stable_id") or selected.get("source_id") or "unknown"))
    namespace = _source_namespace(source_item)
    queue_items = queue.get("items") if isinstance(queue.get("items"), list) else []
    return {
        "run_id": f"daily:{date}:{namespace}:{stable_id}",
        "publication_id": f"pub:daily:{date}:{namespace}:{stable_id}",
        "date": date,
        "generated_at": generated_at,
        "timezone": timezone,
        "source_item": source_item,
        "claims": [dict(claim) for claim in selected["evidence_claims"]],
        "selection_audit": {
            "model_id": ROI_RANKING_MODEL_ID,
            "selection_source": selected.get("selection_source", ""),
            "roi_total_score": selected["roi_total_score"],
            "roi_signals": dict(selected["roi_signals"]),
            "thresholds": _thresholds(),
        },
        "scan_summary": {
            "scope": "all_arxiv_primary_archives",
            "archive_count": scan["archive_count"],
            "blocked_archive_count": scan["blocked_archive_count"],
            "candidate_count": scan["candidate_count"],
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
        "delivery_requirements": _delivery_requirements(),
    }


def _daily_email(
    lesson: Mapping[str, Any],
    daily_input: Mapping[str, Any],
    links: Mapping[str, str],
    queue_summary: Mapping[str, Any],
    *,
    generated_at: str,
) -> EmailNotification:
    source_item = daily_input.get("source_item") if isinstance(daily_input.get("source_item"), Mapping) else {}
    profile = _source_profile(source_item)
    category = str(profile.get("primary_category") or "")
    title = str(source_item.get("title") or "arXiv Daily Push")
    project_label, group_label = _human_source_labels(source_item, category)
    frontstage = _frontstage_from_lesson(lesson, title=title)
    top_queue = queue_summary.get("top_queued") if isinstance(queue_summary.get("top_queued"), list) else []
    queue_items = _email_queue_items(top_queue, selected_category=category)
    queued_count = int(queue_summary.get("queued_item_count") or len(queue_items))
    source_url = str(source_item.get("canonical_url") or "")
    feedback_links = _feedback_links(str(source_item.get("source_id") or "unknown"))
    body = _daily_email_text(
        title=title,
        project_label=project_label,
        group_label=group_label,
        category=category,
        source_url=source_url,
        frontstage=frontstage,
        queued_count=queued_count,
        queue_items=queue_items,
        feedback_links=feedback_links,
    )
    html_body = _daily_email_html(
        title=title,
        project_label=project_label,
        group_label=group_label,
        category=category,
        source_url=source_url,
        frontstage=frontstage,
        queued_count=queued_count,
        queue_items=queue_items,
        feedback_links=feedback_links,
        date=str(daily_input.get("date") or generated_at[:10]),
    )
    subject = _daily_email_subject(
        date=str(daily_input.get("date") or generated_at),
        project_label=project_label,
        group_label=group_label,
        title=title,
    )
    return EmailNotification(subject=subject, recipient=DEFAULT_RECIPIENT, body=body, html_body=html_body)


def _frontstage_from_lesson(lesson: Mapping[str, Any], *, title: str) -> dict[str, Any]:
    frontstage = lesson.get("frontstage") if isinstance(lesson.get("frontstage"), Mapping) else {}
    score = _bounded_score(frontstage.get("attention_score", 3.0) if isinstance(frontstage, Mapping) else 3.0)
    decision = str(frontstage.get("decision") or ("读" if score >= 4.2 else "扫读" if score >= 3.2 else "跳过"))
    if decision not in {"读", "扫读", "跳过"}:
        decision = "扫读"
    one_line = _frontstage_text(
        frontstage.get("one_line_takeaway"),
        fallback="先判断这篇论文是否提供新变量、新机制或新实验，而不是直接采纳摘要结论。",
    )
    return {
        "decision": decision,
        "attention_score": score,
        "evidence_level": _frontstage_text(frontstage.get("evidence_level"), fallback="摘要级预印本"),
        "estimated_reading_time": _frontstage_text(frontstage.get("estimated_reading_time"), fallback="8-15分钟"),
        "one_line_takeaway": one_line,
        "first_principles_chain": _text_list(frontstage.get("first_principles_chain"), ["问题定义", "关键变量", "方法机制", "可观察输出", "失败条件"]),
        "domain_mappings": _mapping_list(frontstage.get("domain_mappings")),
        "key_questions": _text_list(frontstage.get("key_questions"), ["它是否提供可复验增量？", "摘要主张是否有正文证据支撑？", "失败条件是什么？"]),
        "evidence_gaps": _text_list(frontstage.get("evidence_gaps"), ["当前只基于 arXiv 摘要和分类元数据，不能当作同行评审或实证验证。"]),
        "default_action": _frontstage_text(
            frontstage.get("default_action"),
            fallback="只做一个最小验证：列出输入、输出、失败条件和复现实验，再决定是否深读全文。",
        ),
    }


def _daily_email_text(
    *,
    title: str,
    project_label: str,
    group_label: str,
    category: str,
    source_url: str,
    frontstage: Mapping[str, Any],
    queued_count: int,
    queue_items: Sequence[Mapping[str, str]],
    feedback_links: Sequence[Mapping[str, str]],
) -> str:
    chain = " → ".join(str(item) for item in frontstage["first_principles_chain"])
    mappings = [f"- {item['paper_variable']}：{item['decision_mapping']}" for item in frontstage["domain_mappings"][:4]]
    questions = [f"{index}. {item}" for index, item in enumerate(frontstage["key_questions"][:3], start=1)]
    gaps = [f"- {item}" for item in frontstage["evidence_gaps"][:3]]
    candidates = [
        f"- {_truncate_text(str(item['title']), max_chars=72)}（{item['primary_category']}）：{item['reason']}"
        for item in queue_items[:2]
    ] or ["- 今日无其他合格候选。"]
    feedback_options = " / ".join(str(item["label"]) for item in feedback_links)
    return "\n".join(
        [
            "【今天讲透一个问题】",
            f"建议：{frontstage['decision']} | 证据边界：{frontstage['evidence_level']} | 预计：{frontstage['estimated_reading_time']}",
            str(frontstage["one_line_takeaway"]),
            "",
            "【主讲论文】",
            title,
            f"栏目：{project_label} / {group_label}" + (f" / {category}" if category else ""),
            f"原文：{source_url}",
            "",
            "【为什么值得你看】",
            "- 重点不是论文标题，而是它是否给出可迁移的变量、机制或验证方法。",
            "- 你要带走的是一个可复验判断，不是把摘要结论当成事实。",
            "",
            "【第一性原理链条】",
            chain,
            "",
            "【怎么转成可用判断】",
            *mappings,
            "",
            "【真正值得追问】",
            *questions,
            "",
            "【先别相信的地方】",
            *gaps,
            "",
            "【默认动作】",
            str(frontstage["default_action"]),
            "",
            "【候选队列摘要】",
            f"- 已入队候选：{queued_count} 篇；这里只列最可能形成后续讲解的 1-2 篇。",
            *candidates,
            "",
            "【反馈】",
            f"- 回复本邮件，或点击 HTML 按钮：{feedback_options}",
        ]
    )


def _daily_email_html(
    *,
    title: str,
    project_label: str,
    group_label: str,
    category: str,
    source_url: str,
    frontstage: Mapping[str, Any],
    queued_count: int,
    queue_items: Sequence[Mapping[str, str]],
    feedback_links: Sequence[Mapping[str, str]],
    date: str,
) -> str:
    chain_nodes = "".join(f"<span class=\"node\">{escape(str(item))}</span>" for item in frontstage["first_principles_chain"][:5])
    mappings = "".join(
        f"<div class=\"kv\"><b>{escape(str(item['paper_variable']))}</b><span>{escape(str(item['decision_mapping']))}</span></div>"
        for item in frontstage["domain_mappings"][:4]
    )
    questions = "".join(f"<li>{escape(str(item))}</li>" for item in frontstage["key_questions"][:3])
    gaps = "".join(f"<li>{escape(str(item))}</li>" for item in frontstage["evidence_gaps"][:3])
    candidate_html = "".join(
        "<li><b>"
        + escape(_truncate_text(str(item["title"]), max_chars=76))
        + "</b><span>"
        + escape(f"{item['primary_category']} · {item['reason']}")
        + "</span></li>"
        for item in queue_items[:2]
    ) or "<li><b>今日无其他合格候选</b><span>不为填充版面展示低相关论文。</span></li>"
    feedback_html = "".join(
        f"<a class=\"fb\" href=\"{escape(str(item['url']), quote=True)}\">{escape(str(item['label']))}</a>"
        for item in feedback_links
    )
    source_button = _html_button("查看原文", source_url, primary=True) if source_url else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;background:#f5f7fb;color:#172033;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif}}
.wrap{{max-width:680px;margin:0 auto;padding:18px 12px}}
.card{{background:#fff;border:1px solid #e3e8f0;border-radius:14px;overflow:hidden}}
.head{{background:#172033;color:#fff;padding:22px 24px}}
.brand{{font-size:13px;font-weight:700;color:#cbd6ea;letter-spacing:.04em}}
.date{{float:right;font-size:12px;color:#aebbd2}}
h1{{font-size:23px;line-height:1.32;margin:12px 0 8px}}
.lead{{font-size:14px;line-height:1.6;color:#e2e8f5;margin:0}}
.body{{padding:22px 24px}}
.pill{{display:inline-block;margin:0 6px 8px 0;padding:6px 9px;border-radius:999px;background:#edf2ff;color:#293f91;font-size:12px;font-weight:700}}
.pill.ok{{background:#e7f6ee;color:#12683f}}.pill.warn{{background:#fff4dc;color:#865800}}.pill.gray{{background:#f0f2f5;color:#596275}}
.decision{{border:1px solid #dde5f0;background:#fbfcff;border-radius:12px;padding:15px;margin:8px 0 18px}}
.verdict{{float:right;font-size:25px;font-weight:800;color:#1f6f55}}
h2{{font-size:17px;margin:24px 0 10px}}p,li{{font-size:14px;line-height:1.7}}ul{{padding-left:20px}}
.chain{{margin:10px 0}}.node{{display:inline-block;background:#f1f4f9;border-radius:9px;padding:9px 10px;margin:0 4px 6px 0;font-size:13px;font-weight:700}}
.kv{{border:1px solid #e1e7ef;border-radius:10px;padding:11px;margin:8px 0}}.kv b{{display:block;font-size:13px}}.kv span{{display:block;font-size:13px;color:#4d5870;margin-top:3px}}
.callout{{border-left:4px solid #df9b16;background:#fff8e8;padding:12px 14px;border-radius:0 9px 9px 0}}
.btn{{display:inline-block;text-decoration:none;padding:11px 14px;border-radius:9px;font-size:13px;font-weight:750;margin:0 8px 8px 0;background:#172033;color:#fff!important}}
.btn.alt{{background:#edf1f7;color:#25344f!important}}
.candidates li span{{display:block;color:#657187;font-size:12px}}.feedback{{background:#f7f9fc;border-top:1px solid #e4e9f1;padding:18px 24px}}.fb{{display:inline-block;text-decoration:none;border:1px solid #d5dce8;background:#fff;color:#26344f!important;padding:9px 11px;border-radius:8px;font-size:12px;font-weight:700;margin:5px 5px 0 0}}
.muted{{color:#6b7589;font-size:13px}}
@media(max-width:560px){{.wrap{{padding:0}}.card{{border-radius:0;border-left:0;border-right:0}}.head,.body,.feedback{{padding-left:17px;padding-right:17px}}h1{{font-size:21px}}.verdict{{float:none;display:block;margin-top:4px}}}}
</style>
</head>
<body>
<div class="wrap"><div class="card">
<div class="head"><span class="brand">{escape(project_label)} · {escape(group_label)}</span><span class="date">{escape(date)}</span><h1>{escape(str(frontstage["one_line_takeaway"]))}</h1><p class="lead">{escape(title)}</p></div>
<div class="body">
<span class="pill ok">建议：{escape(str(frontstage["decision"]))}</span><span class="pill warn">证据：{escape(str(frontstage["evidence_level"]))}</span><span class="pill gray">{escape(group_label)}{(" / " + escape(category)) if category else ""}</span>
<div class="decision"><span class="verdict">{escape(str(frontstage["decision"]))}</span><b>今天怎么读？</b><p>{escape(str(frontstage["one_line_takeaway"]))} 建议投入 {escape(str(frontstage["estimated_reading_time"]))}。</p></div>
<h2>为什么值得你看</h2><p>重点不是论文标题，而是它是否给出可迁移的变量、机制或验证方法。今天只带走一个可复验判断，不把摘要结论当成事实。</p>
<h2>第一性原理链条</h2><div class="chain">{chain_nodes}</div>
<h2>怎么转成可用判断</h2>{mappings}
<h2>真正值得追问的 3 个问题</h2><ul>{questions}</ul>
<div class="callout"><b>先别相信的地方</b><ul>{gaps}</ul></div>
<h2>默认动作</h2><p>{escape(str(frontstage["default_action"]))}</p>
<div>{source_button}</div>
<h2>候选队列摘要</h2><p class="muted">已入队候选 {int(queued_count)} 篇；这里只列最可能形成后续讲解的 1-2 篇。</p><ul class="candidates">{candidate_html}</ul>
</div>
<div class="feedback"><b>这封讲解如何？点击一次即可影响后续选题</b><br>{feedback_html}</div>
</div></div>
</body>
</html>"""


def _email_queue_items(top_queue: Sequence[Any], *, selected_category: str) -> list[dict[str, str]]:
    selected_archive = _archive_id_from_category(selected_category)
    rows: list[dict[str, str]] = []
    for item in top_queue:
        if not isinstance(item, Mapping):
            continue
        title = _clean_text(str(item.get("title") or ""))
        category = str(item.get("primary_category") or "")
        archive = _archive_id_from_category(category)
        if not title:
            continue
        reason = ""
        if archive and archive == selected_archive:
            reason = "同栏目高价值候选"
        else:
            reason = _cross_domain_reason(selected_archive, archive, title)
        if not reason:
            continue
        rows.append({"title": title, "primary_category": category or archive or "unknown", "reason": reason})
        if len(rows) >= 2:
            break
    return rows


def _cross_domain_reason(selected_archive: str, candidate_archive: str, title: str) -> str:
    text = title.lower()
    finance_terms = ("finance", "market", "portfolio", "risk", "trading", "liquidity", "volatility", "order")
    if selected_archive == "q-fin":
        if candidate_archive in {"cs", "stat", "econ", "eess", "math", "nlin"} and any(term in text for term in finance_terms):
            return "跨域候选，但标题显示可映射到量化金融问题"
        return ""
    general_terms = ("model", "agent", "benchmark", "optimization", "simulation", "control", "learning", "risk")
    if candidate_archive in {"cs", "stat", "econ", "eess", "math", "q-fin"} and any(term in text for term in general_terms):
        return "跨域候选，具备可迁移方法或验证价值"
    return ""


def _feedback_links(source_id: str) -> list[dict[str, str]]:
    options = ["值得深入", "相关性低", "太浅", "太长", "需要实验"]
    links = []
    for option in options:
        subject = quote(f"ADP反馈：{option}", safe="")
        body = quote(f"source_id: {source_id}\nfeedback: {option}\n", safe="")
        links.append({"label": option, "url": f"mailto:{DEFAULT_RECIPIENT}?subject={subject}&body={body}"})
    return links


def _html_button(label: str, url: str, *, primary: bool) -> str:
    class_name = "btn" if primary else "btn alt"
    return f"<a class=\"{class_name}\" href=\"{escape(url, quote=True)}\">{escape(label)}</a>"


def _bounded_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 3.0
    return min(5.0, max(0.0, round(score, 1)))


def _text_list(value: Any, fallback: Sequence[str]) -> list[str]:
    if isinstance(value, list):
        items = [_frontstage_text(item, fallback="") for item in value if _clean_text(str(item))]
        if items:
            return items
    return list(fallback)


def _mapping_list(value: Any) -> list[dict[str, str]]:
    if isinstance(value, list):
        rows = []
        for item in value:
            if not isinstance(item, Mapping):
                continue
            paper_variable = _frontstage_text(item.get("paper_variable"), fallback="论文变量")
            decision_mapping = _frontstage_text(item.get("decision_mapping"), fallback="决策映射待验证")
            rows.append({"paper_variable": paper_variable, "decision_mapping": decision_mapping})
        if rows:
            return rows
    return [{"paper_variable": "论文变量", "decision_mapping": "是否能转成可观测、可记录、可复验的指标"}]


def _frontstage_text(value: Any, *, fallback: str) -> str:
    text = _clean_text(str(value or fallback))
    replacements = (
        ("roi_total_score", "内部排序依据"),
        ("ROI score", "内部排序依据"),
        ("ROI评分", "内部排序依据"),
        ("ROI 分数", "内部排序依据"),
        ("ROI", "价值转化"),
        ("Release 资料包", "归档资料"),
        ("GitHub Release", "归档资料"),
        ("release link", "归档链接"),
        ("视频入口", "媒体入口"),
        ("观看/下载", "查看"),
        ("12-second video", "短讲解材料"),
        ("12秒视频", "短讲解材料"),
        ("delivery policy", "交付规则"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    return text


def _video_card(value: Any, *, title: str) -> dict[str, str]:
    if isinstance(value, Mapping):
        duration = _clean_text(str(value.get("duration") or "45-60秒"))
        content = _clean_text(str(value.get("content") or "用变量、反馈回路和失败条件解释今天是否值得继续读。"))
        learning_goal = _clean_text(str(value.get("learning_goal") or "看完能回答这篇论文的增量和失败条件。"))
        return {"duration": duration, "content": content, "learning_goal": learning_goal}
    return {
        "duration": "45-60秒",
        "content": f"用图解快速判断《{_truncate_text(title, max_chars=36)}》是否值得继续读。",
        "learning_goal": "看完能回答这篇论文的增量和失败条件。",
    }


def _delivery_requirements() -> dict[str, Any]:
    return {
        "notification_channel": "email",
        "recipient": DEFAULT_RECIPIENT,
        "email_chinese_lesson_required": True,
        "email_video_link_required": False,
        "candidate_queue_summary_required": True,
        "video_generation_required": False,
        "video_attachment_allowed": False,
        "release_upload_required": False,
        "artifact_storage": "github_actions_artifacts",
        "production_enablement_blocked_until_stage1_live_email_verified": True,
    }


def _blocked_daily_report(
    date: str,
    generated_at: str,
    timezone: str,
    plan: Mapping[str, Any],
    reasons: Sequence[str],
) -> dict[str, Any]:
    return {
        "builder_id": f"all-arxiv-daily-input:{date}",
        "model_id": ALL_ARXIV_SCAN_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": timezone,
        "status": "blocked",
        "daily_input_ready": False,
        "scan_plan": dict(plan),
        "scan": {},
        "candidate_queue": normalize_candidate_queue(None, generated_at=generated_at),
        "selection": {"model_id": ROI_RANKING_MODEL_ID, "status": "blocked", "selected": None},
        "daily_input": {},
        "delivery_requirements": _delivery_requirements(),
        "artifact_paths": {},
        "blocking_reasons": list(reasons),
    }


def _archive_fetcher(fetcher: FetchAtom | None) -> FetchAtom | None:
    if fetcher is None:
        return None

    def wrapped(query: ArxivQuery) -> str:
        return fetcher(query)

    return wrapped


def _only_no_unseen(batch: Mapping[str, Any]) -> bool:
    reasons = " ".join(str(reason) for reason in batch.get("blocking_reasons") or [])
    return "no unseen" in reasons.lower()


def _sort_candidates(candidates: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [dict(candidate) for candidate in candidates],
        key=lambda item: (-float(item.get("roi_total_score") or 0.0), str(item.get("source_id") or "")),
    )


def _keyword_score(text: str, keywords: Sequence[str], *, per_hit: float) -> float:
    return sum(per_hit for keyword in keywords if keyword in text)


def _length_bonus(summary: str) -> float:
    words = len(summary.split())
    if 40 <= words <= 180:
        return 0.20
    if 20 <= words < 40 or 180 < words <= 280:
        return 0.10
    return 0.0


def _category_groups(categories: Sequence[str]) -> list[str]:
    groups = []
    for category in categories:
        prefix = str(category).split(".")[0]
        if prefix in {"astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph", "nlin", "nucl-ex", "nucl-th", "physics", "quant-ph"}:
            groups.append("physics")
        elif prefix in {"biorxiv", "medrxiv", "biology", "biochemistry", "bioengineering", "bioinformatics", "medicine", "epidemiology"}:
            groups.append("life_science_preprint")
        elif prefix:
            groups.append(prefix)
    return groups


def _required_archive_ids() -> tuple[str, ...]:
    return tuple(item["archive_id"] for item in ALL_ARXIV_ARCHIVES)


def _thresholds() -> dict[str, float]:
    return {
        "new_high_value": ROI_NEW_HIGH_VALUE_THRESHOLD,
        "selection_min": ROI_SELECTION_MIN_SCORE,
        "queue_min": ROI_QUEUE_MIN_SCORE,
    }


def _lesson_has_chinese_text(lesson: Mapping[str, Any]) -> bool:
    if lesson.get("language") not in {"zh-CN", "zh-Hans"}:
        return False
    text = json.dumps(lesson, ensure_ascii=False)
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _compact_date(value: str) -> str:
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", value)
    if match:
        return "".join(match.groups())
    digits = re.sub(r"\D+", "", value)
    return digits[:8] or "00000000"


def _daily_email_subject(*, date: str, project_label: str, group_label: str, title: str) -> str:
    return " -- ".join(
        [
            _compact_date(date),
            _clean_subject_part(project_label or "arXiv Daily Push"),
            _clean_subject_part(group_label or "All arXiv"),
            _human_email_theme(title),
        ]
    )


def _source_profile(source_item: Mapping[str, Any]) -> dict[str, Any]:
    metadata = source_item.get("metadata") if isinstance(source_item.get("metadata"), Mapping) else {}
    arxiv = metadata.get("arxiv") if isinstance(metadata.get("arxiv"), Mapping) else {}
    if isinstance(arxiv, Mapping) and arxiv:
        primary = str(arxiv.get("primary_category") or "")
        categories = [str(category) for category in arxiv.get("categories") or [] if category]
        return {
            "source_family": "arxiv",
            "source_label": "arXiv Atom",
            "summary": _clean_text(str(arxiv.get("summary") or "")),
            "summary_section": "atom:summary",
            "primary_category": primary,
            "categories": categories,
            "category_section": "arxiv:primary_category",
            "server": "arxiv",
        }
    preprint = metadata.get("preprint") if isinstance(metadata.get("preprint"), Mapping) else {}
    if isinstance(preprint, Mapping) and preprint:
        server = str(preprint.get("server") or "preprint").lower()
        category = _clean_text(str(preprint.get("category") or ""))
        type_label = _clean_text(str(preprint.get("type") or ""))
        categories = [item for item in (category, type_label, server) if item]
        return {
            "source_family": "preprint",
            "source_label": "bioRxiv/medRxiv",
            "summary": _clean_text(str(preprint.get("abstract") or "")),
            "summary_section": "preprint.abstract",
            "primary_category": category or server,
            "categories": categories,
            "category_section": "preprint.category",
            "server": server,
        }
    top_journal = metadata.get("top_journal") if isinstance(metadata.get("top_journal"), Mapping) else {}
    if isinstance(top_journal, Mapping) and top_journal:
        journal = _clean_text(str(top_journal.get("journal") or "Top Journal"))
        article_type = _clean_text(str(top_journal.get("article_type") or "research_article"))
        return {
            "source_family": "top_journal",
            "source_label": journal,
            "summary": _clean_text(str(top_journal.get("summary") or "")),
            "summary_section": "top_journal.summary",
            "primary_category": f"{journal} {article_type}".strip(),
            "categories": [item for item in (journal, article_type, "top_journal") if item],
            "category_section": "top_journal.article_type",
            "server": str(top_journal.get("journal_id") or journal).lower(),
        }
    return {
        "source_family": str(source_item.get("source_type") or "unknown"),
        "source_label": str(source_item.get("source_type") or "source"),
        "summary": "",
        "summary_section": "abstract",
        "primary_category": "",
        "categories": [],
        "category_section": "metadata",
        "server": "",
    }


def _source_namespace(source_item: Mapping[str, Any]) -> str:
    profile = _source_profile(source_item)
    family = str(profile.get("source_family") or source_item.get("source_type") or "source")
    server = str(profile.get("server") or "")
    if family == "preprint" and server:
        return _safe_id(server)
    return _safe_id(family)


def _human_source_labels(source_item: Mapping[str, Any], primary_category: str) -> tuple[str, str]:
    profile = _source_profile(source_item)
    if profile.get("source_family") == "preprint":
        server = str(profile.get("server") or "").lower()
        if server == "biorxiv":
            return "arXiv Research Frontiers", "bioRxiv Life Science"
        if server == "medrxiv":
            return "arXiv Research Frontiers", "medRxiv Medicine"
        return "arXiv Research Frontiers", "Preprint"
    if profile.get("source_family") == "top_journal":
        return "Top Journals", str(profile.get("source_label") or "Top Journal")
    return _human_arxiv_labels(primary_category)


def _human_arxiv_labels(primary_category: str) -> tuple[str, str]:
    archive_id = _archive_id_from_category(primary_category)
    archive = next((item for item in ALL_ARXIV_ARCHIVES if item["archive_id"] == archive_id), None)
    project_label = f"arXiv {archive['group']}" if archive else "arXiv Daily Push"
    group_label = _ARXIV_GROUP_LABELS.get(archive_id, archive_id or "All arXiv")
    return project_label, group_label


def _archive_id_from_category(primary_category: str) -> str:
    value = str(primary_category or "")
    for archive_id in sorted(_required_archive_ids(), key=len, reverse=True):
        if value == archive_id or value.startswith(f"{archive_id}."):
            return archive_id
    return value.split(".")[0] if value else ""


def _human_email_theme(title: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(title or "")).strip(" .:-")
    return _truncate_text(cleaned or "Daily arXiv insight", max_chars=72)


def _clean_subject_part(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" -") or "arXiv"


def _truncate_text(value: str, *, max_chars: int) -> str:
    cleaned = _clean_text(str(value or ""))
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max(0, max_chars - 3)].rstrip(" ,.;:") + "..."


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return safe.strip("-") or "unknown"


def _clean_text(value: str) -> str:
    return " ".join(value.split())
