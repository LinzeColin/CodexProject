"""Stage 2 source-promotion gates and local shadow artifacts."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Iterable, Mapping, Sequence
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
    LANCET_ACCEPTED_ARTICLE_TYPES,
    SCIENCE_ACCEPTED_ARTICLE_TYPES,
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
S2P2_TOP_JOURNAL_SHADOW_MODEL_ID = "adp-s2pct01-top-journal-shadow-daily-v1"
S2P2_ACCEPTANCE_ID = "ACC-S2PCT01-NATURE"
S2P2_TASK_ID = "S2PCT01"
S2P2_LEGACY_TASK_ID = "S2P2T01"
S2P2_REQUIRED_JOURNALS = ("nature",)
S2P2_QUEUE_FILENAME = "stage2_s2p2_top_journal_queue.json"
S2P2_LEDGER_FILENAME = "stage2_s2p2_top_journal_ledger.jsonl"
S2PCT02_SCIENCE_SHADOW_MODEL_ID = "adp-s2pct02-science-shadow-daily-v1"
S2PCT02_ACCEPTANCE_ID = "ACC-S2PCT02-SCIENCE"
S2PCT02_TASK_ID = "S2PCT02"
S2PCT02_LEGACY_TASK_ID = "S2P2T02"
S2PCT02_REQUIRED_JOURNALS = ("science",)
S2PCT02_QUEUE_FILENAME = "stage2_s2pct02_science_queue.json"
S2PCT02_LEDGER_FILENAME = "stage2_s2pct02_science_ledger.jsonl"
S2PCT03_LANCET_SHADOW_MODEL_ID = "adp-s2pct03-lancet-shadow-daily-v1"
S2PCT03_ACCEPTANCE_ID = "ACC-S2PCT03-LANCET"
S2PCT03_TASK_ID = "S2PCT03"
S2PCT03_LEGACY_TASK_ID = "S2P2T03"
S2PCT03_REQUIRED_JOURNALS = ("lancet",)
S2PCT03_QUEUE_FILENAME = "stage2_s2pct03_lancet_queue.json"
S2PCT03_LEDGER_FILENAME = "stage2_s2pct03_lancet_ledger.jsonl"
S2PCT04_JOURNAL_PROFILE_MODEL_ID = "adp-s2pct04-top-journal-profile-v1"
S2PCT04_ACCEPTANCE_ID = "ACC-S2PCT04-JOURNAL-PROFILE"
S2PCT04_TASK_ID = "S2PCT04"
S2PCT04_LEGACY_TASK_ID = "S2P2T04"
S2PCT04_REQUIRED_JOURNALS = ("nature", "science", "lancet")
S2PCT04_REQUIRED_PROFILE_KINDS = ("research", "review", "editorial", "news", "correction", "retraction")
S2PCT04_FORCED_EVENT_TYPES = ("correction", "retraction")
S2PCT04_LEDGER_FILENAME = "stage2_s2pct04_profile_ledger.jsonl"
S2PCT05_ENGINEERING_SIGNAL_MODEL_ID = "adp-s2pct05-engineering-signals-v1"
S2PCT05_ACCEPTANCE_ID = "ACC-S2PCT05-ENGINEERING-SIGNALS"
S2PCT05_TASK_ID = "S2PCT05"
S2PCT05_REQUIRED_SIGNAL_TYPES = (
    "official_code_repository",
    "official_release",
    "model_card",
    "benchmark_result",
    "standard_or_spec",
)
S2PCT05_ALLOWED_RELATION_TYPES = (
    "implements_paper",
    "version_of",
    "documents_model",
    "evaluates",
    "standardizes",
)
S2PCT05_ALLOWED_OFFICIALITY_STATES = ("official", "publisher_linked", "standards_body")
S2PCT05_ALLOWED_REPRODUCIBILITY_STATES = ("reproducible", "partial", "claimed", "not_applicable")
S2PCT05_LEDGER_FILENAME = "stage2_s2pct05_engineering_signal_ledger.jsonl"
S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID = "adp-s2pct06-authoritative-reports-v1"
S2PCT06_ACCEPTANCE_ID = "ACC-S2PCT06-REPORTS"
S2PCT06_TASK_ID = "S2PCT06"
S2PCT06_REQUIRED_REPORT_TYPES = (
    "research_institution_report",
    "lab_technical_report",
    "industry_technical_report",
    "product_technical_note",
)
S2PCT06_ALLOWED_PUBLISHER_TYPES = (
    "research_institution",
    "public_lab",
    "industry_research_lab",
    "company_product_org",
)
S2PCT06_ALLOWED_IDENTITY_STATES = (
    "official_domain",
    "institutional_repository",
    "publisher_signed",
    "standards_or_government_affiliated",
)
S2PCT06_ALLOWED_INTEREST_RELATIONS = (
    "independent_research",
    "sponsor_disclosed",
    "vendor_authored",
    "product_owner_authored",
)
S2PCT06_ALLOWED_EVIDENCE_LEVELS = (
    "primary_research_report",
    "technical_whitepaper",
    "methodology_note",
    "product_technical_note",
)
S2PCT06_LEDGER_FILENAME = "stage2_s2pct06_authoritative_report_ledger.jsonl"
S2PCT07_D2_QUALIFICATION_MODEL_ID = "adp-s2pct07-d2-source-domain-qualification-v1"
S2PCT07_ACCEPTANCE_ID = "ACC-S2PCT07-D2"
S2PCT07_TASK_ID = "S2PCT07"
S2PCT07_REQUIRED_DOMAINS = ("top_journal", "engineering_signal", "authoritative_report")
S2PCT07_REQUIRED_REPLAY_DATES = 30
S2PCT07_REQUIRED_SHADOW_HOURS = 48
S2PCT07_REQUIRED_FORCED_EVENT_TYPES = ("correction", "retraction")
S2PCT07_REQUIRED_QUEUE_EXPLANATION_STATES = ("selected", "queued", "deferred")
S2PCT07_QUALIFICATION_REPORT_FILENAME = "stage2_s2pct07_d2_source_domain_qualification_report.json"
S2PDT01_CHINA_C0_SOURCE_MODEL_ID = "adp-s2pdt01-china-c0-source-foundation-v1"
S2PDT01_ACCEPTANCE_ID = "ACC-S2PDT01-C0"
S2PDT01_TASK_ID = "S2PDT01"
S2PDT01_LEGACY_TASK_ID = "S2P3T01"
S2PDT01_REQUIRED_AUTHORITY_TYPES = (
    "law_regulation",
    "npc_document",
    "state_council_document",
    "gazette",
    "supreme_court_procuratorate_document",
)
S2PDT01_REQUIRED_TRACE_FIELDS = ("authority_name", "official_domain", "document_number", "published_date")
S2PDT01_ALLOWED_IDENTITY_STATES = ("official_domain", "official_gazette", "official_publication_portal")
S2PDT01_REPORT_FILENAME = "stage2_s2pdt01_china_c0_source_foundation_report.json"
S2PDT02_CHINA_C1_SOURCE_MODEL_ID = "adp-s2pdt02-china-c1-department-source-map-v1"
S2PDT02_ACCEPTANCE_ID = "ACC-S2PDT02-C1"
S2PDT02_TASK_ID = "S2PDT02"
S2PDT02_LEGACY_TASK_ID = "S2P3T02"
S2PDT02_REQUIRED_SECTORS = (
    "macro_policy",
    "science_technology",
    "industry_policy",
    "finance",
    "market_regulation",
    "key_industry",
)
S2PDT02_REQUIRED_ROUTE_FIELDS = ("aliases", "industry_routes", "official_domain", "source_url")
S2PDT02_ALLOWED_IDENTITY_STATES = ("official_domain", "official_publication_portal")
S2PDT02_REPORT_FILENAME = "stage2_s2pdt02_china_c1_department_source_map_report.json"
S2PDT03_LEGAL_METADATA_MODEL_ID = "adp-s2pdt03-china-legal-metadata-relation-shadow-v1"
S2PDT03_ACCEPTANCE_ID = "ACC-S2PDT03-LEGAL"
S2PDT03_TASK_ID = "S2PDT03"
S2PDT03_LEGACY_TASK_ID = "S2P3T03"
S2PDT03_REQUIRED_LEGAL_STATUSES = ("draft", "formal", "amended", "repealed", "implemented", "interpreted")
S2PDT03_REQUIRED_RELATION_TYPES = ("draft_to_formal", "amends", "repeals", "implements", "interprets", "reprint_of")
S2PDT03_REQUIRED_DATE_FIELDS = ("published_date", "effective_date")
S2PDT03_REQUIRED_FORCED_UPDATE_FIELDS = ("update_required", "rescore_required", "updated_state")
S2PDT03_ALLOWED_IDENTITY_STATES = ("official_domain", "official_gazette", "official_publication_portal")
S2PDT03_REPORT_FILENAME = "stage2_s2pdt03_china_legal_metadata_relation_shadow_report.json"
S2PDT04_D3_READINESS_MODEL_ID = "adp-s2pdt04-china-d3-readiness-review-v1"
S2PDT04_ACCEPTANCE_ID = "ACC-S2PDT04-D3-CORE"
S2PDT04_TASK_ID = "S2PDT04"
S2PDT04_LEGACY_TASK_ID = "S2P3T04"
S2PDT04_REQUIRED_REPLAY_DATES = 30
S2PDT04_REQUIRED_SHADOW_DAYS = 2
S2PDT04_REQUIRED_BOARD_IDS = ("B2_policy", "B3_frontier", "B4_industry", "B5_macro", "B6_risk")
S2PDT04_REQUIRED_ROUTE_FIELDS = ("board_id", "source_ids", "route_explanation", "authority_gate", "metadata_only")
S2PDT04_REPORT_FILENAME = "stage2_s2pdt04_china_d3_readiness_review_report.json"
S2PFT01_CHINA_PROVINCIAL_MODEL_ID = "adp-s2pft01-china-provincial-template-coverage-v1"
S2PFT01_ACCEPTANCE_ID = "ACC-S2PFT01-PROVINCES"
S2PFT01_TASK_ID = "S2PFT01"
S2PFT01_LEGACY_TASK_ID = "S2P5T01"
S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS = (
    "beijing",
    "tianjin",
    "hebei",
    "shanxi",
    "inner_mongolia",
    "liaoning",
    "jilin",
    "heilongjiang",
    "shanghai",
    "jiangsu",
    "zhejiang",
    "anhui",
    "fujian",
    "jiangxi",
    "shandong",
    "henan",
    "hubei",
    "hunan",
    "guangdong",
    "guangxi",
    "hainan",
    "chongqing",
    "sichuan",
    "guizhou",
    "yunnan",
    "tibet",
    "shaanxi",
    "gansu",
    "qinghai",
    "ningxia",
    "xinjiang",
)
S2PFT01_REQUIRED_LOCALITY_TYPES = ("province", "autonomous_region", "municipality")
S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES = (
    "government_portal",
    "development_reform",
    "science_technology",
    "industry_information",
    "finance",
    "market_regulation",
)
S2PFT01_ALLOWED_HEALTH_TIERS = ("green", "yellow", "red")
S2PFT01_ALLOWED_IDENTITY_STATES = ("official_domain", "official_publication_portal")
S2PFT01_REPORT_FILENAME = "stage2_s2pft01_china_provincial_template_coverage_report.json"
S2PFT02_HK_MO_PROFILE_MODEL_ID = "adp-s2pft02-hk-mo-independent-profile-v1"
S2PFT02_ACCEPTANCE_ID = "ACC-S2PFT02-HK-MO"
S2PFT02_TASK_ID = "S2PFT02"
S2PFT02_LEGACY_TASK_ID = "S2P5T02"
S2PFT02_REQUIRED_JURISDICTION_IDS = ("hong_kong", "macau")
S2PFT02_REQUIRED_LANGUAGE_PROFILES = ("zh_hant", "en", "pt")
S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES = ("common_law", "civil_law_portuguese_heritage")
S2PFT02_REQUIRED_PROFILE_FIELDS = (
    "jurisdiction_id",
    "jurisdiction_name",
    "legal_system_state",
    "government_structure_model",
    "official_domain",
    "source_url",
    "authority_gate",
    "metadata_only",
)
S2PFT02_FORBIDDEN_TEMPLATE_STATES = ("mainland_province_template", "mainland_city_template")
S2PFT02_REPORT_FILENAME = "stage2_s2pft02_hk_mo_independent_profile_report.json"
S2PFT03_KEY_CITY_COVERAGE_MODEL_ID = "adp-s2pft03-key-city-coverage-v1"
S2PFT03_ACCEPTANCE_ID = "ACC-S2PFT03-CITIES"
S2PFT03_TASK_ID = "S2PFT03"
S2PFT03_LEGACY_TASK_ID = "S2P5T03"
S2PFT03_REQUIRED_CITY_IDS = (
    "beijing",
    "shanghai",
    "shenzhen",
    "guangzhou",
    "tianjin",
    "chongqing",
    "hangzhou",
    "nanjing",
    "suzhou",
    "hefei",
    "wuhan",
    "xian",
    "chengdu",
    "changsha",
    "wuxi",
    "dongguan",
    "foshan",
    "zhuhai",
    "shenyang",
    "ningbo",
    "qingdao",
    "xiamen",
    "dalian",
    "zhengzhou",
)
S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES = (
    "party_committee",
    "government_portal",
    "development_reform",
    "science_technology",
    "industry_information",
    "finance",
    "commerce",
    "market_regulation",
    "data",
    "financial_regulation",
)
S2PFT03_ALLOWED_REGION_GROUPS = ("national_municipality", "yangtze_delta", "pearl_delta", "central", "western", "northeast", "coastal")
S2PFT03_ALLOWED_HEALTH_TIERS = ("green", "yellow", "red")
S2PFT03_REPORT_FILENAME = "stage2_s2pft03_key_city_coverage_report.json"


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
        "legacy_task_id": S2P2_LEGACY_TASK_ID,
        "phase": "S2PC",
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
        "legacy_task_id": S2P2_LEGACY_TASK_ID,
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
        errors.append("S2PC shadow report model_id must be adp-s2pct01-top-journal-shadow-daily-v1")
    if report.get("task_id") != S2P2_TASK_ID:
        errors.append("S2PC shadow report task_id must be S2PCT01")
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


def build_s2pct02_science_daily_input(
    *,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a no-send S2PCT02 Science shadow daily input from public metadata."""

    scan = _top_journal_scan(
        source_batches,
        generated_at=generated_at,
        required_journals=S2PCT02_REQUIRED_JOURNALS,
        model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
        scan_id="s2pct02-science-scan:shadow",
        no_candidate_message="no eligible new Science main-journal candidates for shadow daily input",
    )
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    if scan["status"] == "blocked":
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            scan["blocking_reasons"],
            model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            task_id=S2PCT02_TASK_ID,
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
            model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            task_id=S2PCT02_TASK_ID,
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
        run_label="s2pct02-science",
        scan_scope="s2pct02_science_shadow",
        source_count=len(S2PCT02_REQUIRED_JOURNALS),
        task_id=S2PCT02_TASK_ID,
    )
    return {
        "model_id": S2PCT02_SCIENCE_SHADOW_MODEL_ID,
        "task_id": S2PCT02_TASK_ID,
        "legacy_task_id": S2PCT02_LEGACY_TASK_ID,
        "phase": "S2PC",
        "acceptance_id": S2PCT02_ACCEPTANCE_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "pass",
        "daily_input_ready": True,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "blocking_reasons": [],
    }


def run_s2pct02_science_shadow_daily(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    write: bool = True,
) -> dict[str, Any]:
    """Run one no-send S2PCT02 Science shadow daily path and persist evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct02-science-shadow"
    queue_path = state / S2PCT02_QUEUE_FILENAME
    ledger_path = state / S2PCT02_LEDGER_FILENAME
    queue_state = queue if queue is not None else _load_json(queue_path) if queue_path.exists() else None
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)

    daily_report = build_s2pct02_science_daily_input(
        date=date,
        generated_at=generated_at,
        source_batches=source_batches,
        queue=queue_state,
        recent_source_ids=recent_source_ids,
    )
    if write:
        _write_json(run_dir / "adp-s2pct02-science-daily-input-report.json", daily_report)
    if daily_report.get("daily_input_ready") is not True:
        report = _base_shadow_report(
            status="blocked",
            date=date,
            generated_at=generated_at,
            state=state,
            run_dir=run_dir,
            blocking_reasons=list(daily_report.get("blocking_reasons") or ["Science daily input blocked"]),
            daily_report=daily_report,
            model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            acceptance_id=S2PCT02_ACCEPTANCE_ID,
            task_id=S2PCT02_TASK_ID,
        )
        report["legacy_task_id"] = S2PCT02_LEGACY_TASK_ID
        return _write_or_return_s2pct02(report, run_dir, write=write)
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
        report = _base_shadow_report(
            status="blocked",
            date=date,
            generated_at=generated_at,
            state=state,
            run_dir=run_dir,
            blocking_reasons=[f"Science shadow pipeline failed: {error}"],
            daily_report=daily_report,
            model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            acceptance_id=S2PCT02_ACCEPTANCE_ID,
            task_id=S2PCT02_TASK_ID,
        )
        report["legacy_task_id"] = S2PCT02_LEGACY_TASK_ID
        return _write_or_return_s2pct02(report, run_dir, write=write)
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
        "task_id": S2PCT02_TASK_ID,
        "legacy_task_id": S2PCT02_LEGACY_TASK_ID,
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
        _write_json(run_dir / "adp-s2pct02-science-daily-run.json", daily_run)
        _write_json(run_dir / "adp-s2pct02-science-delivery-package.json", {k: v for k, v in delivery_package.items() if k != "notification"})
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
        model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
        acceptance_id=S2PCT02_ACCEPTANCE_ID,
        task_id=S2PCT02_TASK_ID,
    )
    report.update(
        {
            "legacy_task_id": S2PCT02_LEGACY_TASK_ID,
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
            "d2_source_domain_accepted": False,
            "stage2_production_accepted": False,
            "integrated_production_accepted": False,
        }
    )
    return _write_or_return_s2pct02(report, run_dir, write=write)


def validate_s2pct02_science_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT02_SCIENCE_SHADOW_MODEL_ID:
        errors.append("S2PCT02 shadow report model_id must be adp-s2pct02-science-shadow-daily-v1")
    if report.get("task_id") != S2PCT02_TASK_ID:
        errors.append("S2PCT02 shadow report task_id must be S2PCT02")
    if report.get("acceptance_id") != S2PCT02_ACCEPTANCE_ID:
        errors.append("S2PCT02 shadow report acceptance_id must be ACC-S2PCT02-SCIENCE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT02 shadow report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "production_affected",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT02 Science shadow daily")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT02 shadow report requires blocking_reasons")
    if report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing S2PCT02 shadow report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing S2PCT02 shadow report requires email_preview_written")
        source_item = (
            report.get("daily_report", {}).get("daily_input", {}).get("source_item", {})
            if isinstance(report.get("daily_report"), Mapping)
            else {}
        )
        if not isinstance(source_item, Mapping):
            source_item = {}
        source_id = str(report.get("selected_source_id") or source_item.get("source_id") or "")
        if not source_id.startswith("science:10.1126/science."):
            errors.append("passing S2PCT02 shadow report requires selected Science main-journal source_id")
        top_journal = source_item.get("metadata", {}).get("top_journal", {}) if isinstance(source_item.get("metadata"), Mapping) else {}
        article_type = str(top_journal.get("article_type") or "") if isinstance(top_journal, Mapping) else ""
        if article_type not in SCIENCE_ACCEPTED_ARTICLE_TYPES:
            errors.append("passing S2PCT02 shadow report requires Science article_type classification")
    return errors


def build_s2pct03_lancet_daily_input(
    *,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a no-send S2PCT03 The Lancet shadow daily input from public metadata."""

    scan = _top_journal_scan(
        source_batches,
        generated_at=generated_at,
        required_journals=S2PCT03_REQUIRED_JOURNALS,
        model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
        scan_id="s2pct03-lancet-scan:shadow",
        no_candidate_message="no eligible new The Lancet main-journal candidates for shadow daily input",
    )
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    if scan["status"] == "blocked":
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            scan["blocking_reasons"],
            model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
            task_id=S2PCT03_TASK_ID,
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
            model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
            task_id=S2PCT03_TASK_ID,
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
        run_label="s2pct03-lancet",
        scan_scope="s2pct03_lancet_shadow",
        source_count=len(S2PCT03_REQUIRED_JOURNALS),
        task_id=S2PCT03_TASK_ID,
    )
    return {
        "model_id": S2PCT03_LANCET_SHADOW_MODEL_ID,
        "task_id": S2PCT03_TASK_ID,
        "legacy_task_id": S2PCT03_LEGACY_TASK_ID,
        "phase": "S2PC",
        "acceptance_id": S2PCT03_ACCEPTANCE_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "pass",
        "daily_input_ready": True,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "blocking_reasons": [],
    }


def run_s2pct03_lancet_shadow_daily(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    write: bool = True,
) -> dict[str, Any]:
    """Run one no-send S2PCT03 The Lancet shadow daily path and persist evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct03-lancet-shadow"
    queue_path = state / S2PCT03_QUEUE_FILENAME
    ledger_path = state / S2PCT03_LEDGER_FILENAME
    queue_state = queue if queue is not None else _load_json(queue_path) if queue_path.exists() else None
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)

    daily_report = build_s2pct03_lancet_daily_input(
        date=date,
        generated_at=generated_at,
        source_batches=source_batches,
        queue=queue_state,
        recent_source_ids=recent_source_ids,
    )
    if write:
        _write_json(run_dir / "adp-s2pct03-lancet-daily-input-report.json", daily_report)
    if daily_report.get("daily_input_ready") is not True:
        report = _base_shadow_report(
            status="blocked",
            date=date,
            generated_at=generated_at,
            state=state,
            run_dir=run_dir,
            blocking_reasons=list(daily_report.get("blocking_reasons") or ["The Lancet daily input blocked"]),
            daily_report=daily_report,
            model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
            acceptance_id=S2PCT03_ACCEPTANCE_ID,
            task_id=S2PCT03_TASK_ID,
        )
        report["legacy_task_id"] = S2PCT03_LEGACY_TASK_ID
        return _write_or_return_s2pct03(report, run_dir, write=write)
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
        report = _base_shadow_report(
            status="blocked",
            date=date,
            generated_at=generated_at,
            state=state,
            run_dir=run_dir,
            blocking_reasons=[f"The Lancet shadow pipeline failed: {error}"],
            daily_report=daily_report,
            model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
            acceptance_id=S2PCT03_ACCEPTANCE_ID,
            task_id=S2PCT03_TASK_ID,
        )
        report["legacy_task_id"] = S2PCT03_LEGACY_TASK_ID
        return _write_or_return_s2pct03(report, run_dir, write=write)
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
        "task_id": S2PCT03_TASK_ID,
        "legacy_task_id": S2PCT03_LEGACY_TASK_ID,
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
        _write_json(run_dir / "adp-s2pct03-lancet-daily-run.json", daily_run)
        _write_json(run_dir / "adp-s2pct03-lancet-delivery-package.json", {k: v for k, v in delivery_package.items() if k != "notification"})
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
        model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
        acceptance_id=S2PCT03_ACCEPTANCE_ID,
        task_id=S2PCT03_TASK_ID,
    )
    report.update(
        {
            "legacy_task_id": S2PCT03_LEGACY_TASK_ID,
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
            "d2_source_domain_accepted": False,
            "stage2_production_accepted": False,
            "integrated_production_accepted": False,
        }
    )
    return _write_or_return_s2pct03(report, run_dir, write=write)


def validate_s2pct03_lancet_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT03_LANCET_SHADOW_MODEL_ID:
        errors.append("S2PCT03 shadow report model_id must be adp-s2pct03-lancet-shadow-daily-v1")
    if report.get("task_id") != S2PCT03_TASK_ID:
        errors.append("S2PCT03 shadow report task_id must be S2PCT03")
    if report.get("acceptance_id") != S2PCT03_ACCEPTANCE_ID:
        errors.append("S2PCT03 shadow report acceptance_id must be ACC-S2PCT03-LANCET")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT03 shadow report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "production_affected",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT03 The Lancet shadow daily")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT03 shadow report requires blocking_reasons")
    if report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing S2PCT03 shadow report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing S2PCT03 shadow report requires email_preview_written")
        source_item = (
            report.get("daily_report", {}).get("daily_input", {}).get("source_item", {})
            if isinstance(report.get("daily_report"), Mapping)
            else {}
        )
        if not isinstance(source_item, Mapping):
            source_item = {}
        source_id = str(report.get("selected_source_id") or source_item.get("source_id") or "")
        if not source_id.startswith("lancet:10.1016/s0140-6736"):
            errors.append("passing S2PCT03 shadow report requires selected The Lancet main-journal DOI source_id")
        top_journal = source_item.get("metadata", {}).get("top_journal", {}) if isinstance(source_item.get("metadata"), Mapping) else {}
        article_type = str(top_journal.get("article_type") or "") if isinstance(top_journal, Mapping) else ""
        if article_type not in LANCET_ACCEPTED_ARTICLE_TYPES:
            errors.append("passing S2PCT03 shadow report requires Lancet article_type classification")
        if isinstance(top_journal, Mapping):
            if top_journal.get("index_alignment_gate") != "pass":
                errors.append("passing S2PCT03 shadow report requires Lancet index_alignment_gate")
            medical_indexing = top_journal.get("medical_indexing")
            if not isinstance(medical_indexing, Mapping):
                errors.append("passing S2PCT03 shadow report requires medical_indexing")
            elif medical_indexing.get("pubmed_relation_gate") not in {"doi_query_ready", "pmid_present"}:
                errors.append("passing S2PCT03 shadow report requires PubMed DOI relationship gate")
    return errors


def build_s2pct04_top_journal_profile_report(
    *,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    publication_events: Sequence[Mapping[str, Any]] = (),
    prior_profile_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build metadata-only profile/relation evidence across completed D2 top journals."""

    source_profiles, relation_edges, source_reports, source_errors = _top_journal_profiles_from_batches(
        source_batches,
        generated_at=generated_at,
    )
    known_targets = {str(profile.get("canonical_document_id") or "") for profile in source_profiles}
    prior_index = _prior_profile_state_index(prior_profile_state)
    known_targets.update(prior_index)
    event_profiles, event_edges, forced_updates, event_reports, event_errors = _top_journal_profiles_from_publication_events(
        publication_events,
        generated_at=generated_at,
        known_targets=known_targets,
        prior_index=prior_index,
    )
    profiles = source_profiles + event_profiles
    relation_edges = relation_edges + event_edges
    observed_profile_kinds = sorted({str(profile.get("profile_kind") or "") for profile in profiles if profile.get("profile_kind")})
    missing_profile_kinds = [kind for kind in S2PCT04_REQUIRED_PROFILE_KINDS if kind not in observed_profile_kinds]
    duplicate_profile_ids = _duplicate_values(str(profile.get("profile_id") or "") for profile in profiles)
    relation_errors = _publication_relation_errors(profiles, relation_edges)
    forced_event_errors = _forced_event_update_errors(event_profiles, forced_updates)
    blocking_reasons = source_errors + event_errors + relation_errors + forced_event_errors
    if missing_profile_kinds:
        blocking_reasons.append(f"missing required top-journal profile kinds: {', '.join(missing_profile_kinds)}")
    if duplicate_profile_ids:
        blocking_reasons.append("duplicate top-journal profile ids: " + ", ".join(duplicate_profile_ids))
    taxonomy_gate = "pass" if not missing_profile_kinds and not duplicate_profile_ids else "blocked"
    relation_gate = "pass" if not relation_errors and relation_edges else "blocked"
    forced_gate = "pass" if not forced_event_errors and _forced_event_kinds(forced_updates) == set(S2PCT04_FORCED_EVENT_TYPES) else "blocked"
    if forced_gate == "blocked" and not forced_event_errors:
        blocking_reasons.append("correction and retraction forced-event updates are both required")
    status = "pass" if not blocking_reasons and taxonomy_gate == relation_gate == forced_gate == "pass" else "blocked"
    return {
        "model_id": S2PCT04_JOURNAL_PROFILE_MODEL_ID,
        "acceptance_id": S2PCT04_ACCEPTANCE_ID,
        "task_id": S2PCT04_TASK_ID,
        "legacy_task_id": S2PCT04_LEGACY_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "profile_taxonomy_gate": taxonomy_gate,
        "publication_relation_gate": relation_gate,
        "forced_event_update_gate": forced_gate,
        "required_profile_kinds": list(S2PCT04_REQUIRED_PROFILE_KINDS),
        "profile_kinds_observed": observed_profile_kinds,
        "source_reports": source_reports,
        "event_reports": event_reports,
        "source_profile_count": len(source_profiles),
        "publication_event_count": len(publication_events),
        "relation_edge_count": len(relation_edges),
        "forced_event_update_count": len(forced_updates),
        "source_profiles": profiles,
        "publication_relation_edges": relation_edges,
        "forced_event_updates": forced_updates,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "production_affected": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "blocking_reasons": blocking_reasons,
    }


def run_s2pct04_top_journal_profile_shadow(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    publication_events: Sequence[Mapping[str, Any]] = (),
    prior_profile_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PCT04 metadata-only top-journal profile/relation evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct04-top-journal-profile-shadow"
    ledger_path = state / S2PCT04_LEDGER_FILENAME
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pct04_top_journal_profile_report(
        generated_at=generated_at,
        source_batches=source_batches,
        publication_events=publication_events,
        prior_profile_state=prior_profile_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "profile_report_path": str(run_dir / "adp-s2pct04-top-journal-profile-report.json"),
            "profile_ledger_path": str(ledger_path),
            "profile_ledger_row_count": len(report.get("forced_event_updates") or []),
        }
    )
    if write:
        for row in report.get("forced_event_updates") or []:
            if isinstance(row, Mapping):
                _append_jsonl(ledger_path, row)
    return _write_or_return_s2pct04(report, run_dir, write=write)


def validate_s2pct04_top_journal_profile_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT04_JOURNAL_PROFILE_MODEL_ID:
        errors.append("S2PCT04 profile report model_id must be adp-s2pct04-top-journal-profile-v1")
    if report.get("task_id") != S2PCT04_TASK_ID:
        errors.append("S2PCT04 profile report task_id must be S2PCT04")
    if report.get("legacy_task_id") != S2PCT04_LEGACY_TASK_ID:
        errors.append("S2PCT04 profile report legacy_task_id must be S2P2T04")
    if report.get("acceptance_id") != S2PCT04_ACCEPTANCE_ID:
        errors.append("S2PCT04 profile report acceptance_id must be ACC-S2PCT04-JOURNAL-PROFILE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT04 profile report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT04 top-journal profile shadow")
    profiles = report.get("source_profiles")
    edges = report.get("publication_relation_edges")
    updates = report.get("forced_event_updates")
    if not isinstance(profiles, list):
        errors.append("S2PCT04 source_profiles must be a list")
        profiles = []
    if not isinstance(edges, list):
        errors.append("S2PCT04 publication_relation_edges must be a list")
        edges = []
    if not isinstance(updates, list):
        errors.append("S2PCT04 forced_event_updates must be a list")
        updates = []
    observed = set(report.get("profile_kinds_observed") or [])
    missing = [kind for kind in S2PCT04_REQUIRED_PROFILE_KINDS if kind not in observed]
    if missing:
        errors.append("S2PCT04 profile taxonomy missing required kinds: " + ", ".join(missing))
    profile_ids: set[str] = set()
    for index, profile in enumerate(profiles):
        if not isinstance(profile, Mapping):
            errors.append(f"source_profiles[{index}] must be an object")
            continue
        profile_id = str(profile.get("profile_id") or "")
        if not profile_id:
            errors.append(f"source_profiles[{index}].profile_id is required")
        if profile_id in profile_ids:
            errors.append(f"duplicate S2PCT04 profile_id: {profile_id}")
        profile_ids.add(profile_id)
        if profile.get("metadata_only") is not True:
            errors.append(f"source_profiles[{index}].metadata_only must be true")
        if profile.get("profile_kind") not in S2PCT04_REQUIRED_PROFILE_KINDS:
            errors.append(f"source_profiles[{index}].profile_kind is not supported")
        if not profile.get("canonical_document_id"):
            errors.append(f"source_profiles[{index}].canonical_document_id is required")
        if profile.get("profile_kind") in S2PCT04_FORCED_EVENT_TYPES and not profile.get("target_canonical_document_id"):
            errors.append(f"source_profiles[{index}] forced event requires target_canonical_document_id")
    for index, edge in enumerate(edges):
        if not isinstance(edge, Mapping):
            errors.append(f"publication_relation_edges[{index}] must be an object")
            continue
        if not edge.get("relation_type"):
            errors.append(f"publication_relation_edges[{index}].relation_type is required")
        if not edge.get("source_canonical_document_id"):
            errors.append(f"publication_relation_edges[{index}].source_canonical_document_id is required")
        if edge.get("target_required") is True and not edge.get("target_canonical_document_id"):
            errors.append(f"publication_relation_edges[{index}] required target_canonical_document_id is missing")
        if edge.get("metadata_only") is not True:
            errors.append(f"publication_relation_edges[{index}].metadata_only must be true")
    update_kinds = _forced_event_kinds(updates)
    if update_kinds != set(S2PCT04_FORCED_EVENT_TYPES):
        errors.append("S2PCT04 forced_event_updates must include correction and retraction")
    for index, update in enumerate(updates):
        if not isinstance(update, Mapping):
            errors.append(f"forced_event_updates[{index}] must be an object")
            continue
        if update.get("event_type") not in S2PCT04_FORCED_EVENT_TYPES:
            errors.append(f"forced_event_updates[{index}].event_type must be correction or retraction")
        if not update.get("target_canonical_document_id"):
            errors.append(f"forced_event_updates[{index}].target_canonical_document_id is required")
        if update.get("forced_review_required") is not True:
            errors.append(f"forced_event_updates[{index}].forced_review_required must be true")
        if update.get("updated_conclusion_state") not in {"requires_revision", "invalidated"}:
            errors.append(f"forced_event_updates[{index}].updated_conclusion_state is invalid")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT04 profile report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in ("profile_taxonomy_gate", "publication_relation_gate", "forced_event_update_gate"):
            if report.get(key) != "pass":
                errors.append(f"passing S2PCT04 profile report requires {key}=pass")
    return errors


def build_s2pct05_engineering_signal_report(
    *,
    generated_at: str,
    profile_report: Mapping[str, Any],
    engineering_signals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build metadata-only public engineering signal evidence after S2PCT04."""

    profile_errors = validate_s2pct04_top_journal_profile_report(profile_report)
    profile_gate = "pass" if not profile_errors and profile_report.get("status") == "pass" else "blocked"
    known_documents = _s2pct05_known_documents(profile_report)
    normalized_signals, signal_reports, signal_errors = _s2pct05_normalize_engineering_signals(
        engineering_signals,
        known_documents=known_documents,
        generated_at=generated_at,
    )
    observed_signal_types = sorted({str(signal.get("signal_type") or "") for signal in normalized_signals if signal.get("signal_type")})
    missing_signal_types = [signal_type for signal_type in S2PCT05_REQUIRED_SIGNAL_TYPES if signal_type not in observed_signal_types]
    duplicate_signal_ids = _duplicate_values(str(signal.get("signal_id") or "") for signal in normalized_signals)
    officiality_errors = _s2pct05_officiality_errors(normalized_signals) + [
        reason for reason in signal_errors if "officiality" in reason
    ]
    version_errors = _s2pct05_version_errors(normalized_signals) + [
        reason for reason in signal_errors if "version_reference" in reason
    ]
    relation_errors = _s2pct05_relation_errors(normalized_signals, known_documents) + [
        reason for reason in signal_errors if "canonical_document_id" in reason or "paper_relation_type" in reason
    ]
    reproducibility_errors = _s2pct05_reproducibility_errors(normalized_signals) + [
        reason for reason in signal_errors if "reproducibility" in reason or "metric_name" in reason
    ]
    officiality_gate = "pass" if not officiality_errors else "blocked"
    version_gate = "pass" if not version_errors else "blocked"
    relation_gate = "pass" if not relation_errors else "blocked"
    reproducibility_gate = "pass" if not reproducibility_errors else "blocked"
    blocking_reasons = list(profile_errors) + signal_errors
    if profile_gate != "pass":
        blocking_reasons.append("S2PCT04 profile report must pass before S2PCT05 engineering signals")
    if missing_signal_types:
        blocking_reasons.append("missing required engineering signal types: " + ", ".join(missing_signal_types))
    if duplicate_signal_ids:
        blocking_reasons.append("duplicate engineering signal ids: " + ", ".join(duplicate_signal_ids))
    for gate_errors in (officiality_errors, version_errors, relation_errors, reproducibility_errors):
        for reason in gate_errors:
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)
    taxonomy_gate = "pass" if not missing_signal_types and not duplicate_signal_ids else "blocked"
    status = (
        "pass"
        if not blocking_reasons
        and profile_gate == taxonomy_gate == officiality_gate == version_gate == relation_gate == reproducibility_gate == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PCT05_ENGINEERING_SIGNAL_MODEL_ID,
        "acceptance_id": S2PCT05_ACCEPTANCE_ID,
        "task_id": S2PCT05_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "profile_gate": profile_gate,
        "engineering_signal_taxonomy_gate": taxonomy_gate,
        "officiality_gate": officiality_gate,
        "version_traceability_gate": version_gate,
        "paper_relation_gate": relation_gate,
        "reproducibility_state_gate": reproducibility_gate,
        "required_signal_types": list(S2PCT05_REQUIRED_SIGNAL_TYPES),
        "signal_types_observed": observed_signal_types,
        "engineering_signal_count": len(normalized_signals),
        "known_document_count": len(known_documents),
        "signal_reports": signal_reports,
        "engineering_signals": normalized_signals,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "blocking_reasons": blocking_reasons,
    }


def run_s2pct05_engineering_signal_shadow(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    profile_report: Mapping[str, Any],
    engineering_signals: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PCT05 metadata-only engineering signal evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct05-engineering-signals-shadow"
    ledger_path = state / S2PCT05_LEDGER_FILENAME
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pct05_engineering_signal_report(
        generated_at=generated_at,
        profile_report=profile_report,
        engineering_signals=engineering_signals,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "engineering_signal_report_path": str(run_dir / "adp-s2pct05-engineering-signal-report.json"),
            "engineering_signal_ledger_path": str(ledger_path),
            "engineering_signal_ledger_row_count": len(report.get("engineering_signals") or []),
        }
    )
    if write:
        for row in report.get("engineering_signals") or []:
            if isinstance(row, Mapping):
                _append_jsonl(ledger_path, row)
    return _write_or_return_s2pct05(report, run_dir, write=write)


def validate_s2pct05_engineering_signal_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT05_ENGINEERING_SIGNAL_MODEL_ID:
        errors.append("S2PCT05 engineering signal report model_id must be adp-s2pct05-engineering-signals-v1")
    if report.get("task_id") != S2PCT05_TASK_ID:
        errors.append("S2PCT05 engineering signal report task_id must be S2PCT05")
    if report.get("acceptance_id") != S2PCT05_ACCEPTANCE_ID:
        errors.append("S2PCT05 engineering signal report acceptance_id must be ACC-S2PCT05-ENGINEERING-SIGNALS")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT05 engineering signal report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT05 engineering signal shadow")
    signals = report.get("engineering_signals")
    if not isinstance(signals, list):
        errors.append("S2PCT05 engineering_signals must be a list")
        signals = []
    observed = set(report.get("signal_types_observed") or [])
    missing = [signal_type for signal_type in S2PCT05_REQUIRED_SIGNAL_TYPES if signal_type not in observed]
    if missing:
        errors.append("S2PCT05 signal taxonomy missing required types: " + ", ".join(missing))
    signal_ids: set[str] = set()
    for index, signal in enumerate(signals):
        if not isinstance(signal, Mapping):
            errors.append(f"engineering_signals[{index}] must be an object")
            continue
        signal_id = str(signal.get("signal_id") or "")
        if not signal_id:
            errors.append(f"engineering_signals[{index}].signal_id is required")
        if signal_id in signal_ids:
            errors.append(f"duplicate S2PCT05 signal_id: {signal_id}")
        signal_ids.add(signal_id)
        if signal.get("signal_type") not in S2PCT05_REQUIRED_SIGNAL_TYPES:
            errors.append(f"engineering_signals[{index}].signal_type is not supported")
        if signal.get("metadata_only") is not True:
            errors.append(f"engineering_signals[{index}].metadata_only must be true")
        if signal.get("officiality_state") not in S2PCT05_ALLOWED_OFFICIALITY_STATES:
            errors.append(f"engineering_signals[{index}].officiality_state is not accepted")
        if signal.get("paper_relation_type") not in S2PCT05_ALLOWED_RELATION_TYPES:
            errors.append(f"engineering_signals[{index}].paper_relation_type is not supported")
        if not signal.get("canonical_document_id"):
            errors.append(f"engineering_signals[{index}].canonical_document_id is required")
        if not signal.get("version_reference"):
            errors.append(f"engineering_signals[{index}].version_reference is required")
        if signal.get("reproducibility_state") not in S2PCT05_ALLOWED_REPRODUCIBILITY_STATES:
            errors.append(f"engineering_signals[{index}].reproducibility_state is invalid")
        if not signal.get("evidence_refs"):
            errors.append(f"engineering_signals[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT05 engineering signal report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "profile_gate",
            "engineering_signal_taxonomy_gate",
            "officiality_gate",
            "version_traceability_gate",
            "paper_relation_gate",
            "reproducibility_state_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PCT05 engineering signal report requires {key}=pass")
    return errors


def build_s2pct06_authoritative_report_source_report(
    *,
    generated_at: str,
    engineering_signal_report: Mapping[str, Any],
    technical_reports: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build metadata-only authoritative technical report evidence after S2PCT05."""

    engineering_errors = validate_s2pct05_engineering_signal_report(engineering_signal_report)
    engineering_gate = "pass" if not engineering_errors and engineering_signal_report.get("status") == "pass" else "blocked"
    known_signals = _s2pct06_known_signals(engineering_signal_report)
    known_documents = {
        str(signal.get("canonical_document_id") or "")
        for signal in known_signals.values()
        if signal.get("canonical_document_id")
    }
    normalized_reports, source_reports, report_errors = _s2pct06_normalize_reports(
        technical_reports,
        known_signals=known_signals,
        known_documents=known_documents,
        generated_at=generated_at,
    )
    observed_report_types = sorted(
        {str(report.get("report_type") or "") for report in normalized_reports if report.get("report_type")}
    )
    missing_report_types = [
        report_type for report_type in S2PCT06_REQUIRED_REPORT_TYPES if report_type not in observed_report_types
    ]
    duplicate_report_ids = _duplicate_values(str(report.get("report_id") or "") for report in normalized_reports)
    publisher_identity_errors = _s2pct06_publisher_identity_errors(normalized_reports) + [
        reason
        for reason in report_errors
        if "publisher_identity" in reason or "publisher_type" in reason or "publisher" in reason
    ]
    interest_errors = _s2pct06_interest_relation_errors(normalized_reports) + [
        reason for reason in report_errors if "interest_relation" in reason or "interest_disclosure" in reason
    ]
    evidence_errors = _s2pct06_evidence_level_errors(normalized_reports) + [
        reason for reason in report_errors if "evidence_level" in reason
    ]
    traceability_errors = _s2pct06_traceability_errors(normalized_reports, known_signals, known_documents) + [
        reason
        for reason in report_errors
        if "related_signal_ids" in reason or "canonical_document_id" in reason
    ]
    publisher_identity_gate = "pass" if not publisher_identity_errors else "blocked"
    interest_relation_gate = "pass" if not interest_errors else "blocked"
    evidence_level_gate = "pass" if not evidence_errors else "blocked"
    traceability_gate = "pass" if not traceability_errors else "blocked"
    blocking_reasons = list(engineering_errors) + report_errors
    if engineering_gate != "pass":
        blocking_reasons.append("S2PCT05 engineering signal report must pass before S2PCT06 authoritative reports")
    if missing_report_types:
        blocking_reasons.append("missing required authoritative report types: " + ", ".join(missing_report_types))
    if duplicate_report_ids:
        blocking_reasons.append("duplicate authoritative report ids: " + ", ".join(duplicate_report_ids))
    for gate_errors in (publisher_identity_errors, interest_errors, evidence_errors, traceability_errors):
        for reason in gate_errors:
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)
    report_taxonomy_gate = "pass" if not missing_report_types and not duplicate_report_ids else "blocked"
    status = (
        "pass"
        if not blocking_reasons
        and engineering_gate
        == report_taxonomy_gate
        == publisher_identity_gate
        == interest_relation_gate
        == evidence_level_gate
        == traceability_gate
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID,
        "acceptance_id": S2PCT06_ACCEPTANCE_ID,
        "task_id": S2PCT06_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "engineering_signal_gate": engineering_gate,
        "report_taxonomy_gate": report_taxonomy_gate,
        "publisher_identity_gate": publisher_identity_gate,
        "interest_relation_gate": interest_relation_gate,
        "evidence_level_gate": evidence_level_gate,
        "traceability_gate": traceability_gate,
        "required_report_types": list(S2PCT06_REQUIRED_REPORT_TYPES),
        "report_types_observed": observed_report_types,
        "authoritative_report_count": len(normalized_reports),
        "known_signal_count": len(known_signals),
        "known_document_count": len(known_documents),
        "source_reports": source_reports,
        "authoritative_reports": normalized_reports,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "marketing_material_accepted": False,
        "blocking_reasons": blocking_reasons,
    }


def run_s2pct06_authoritative_report_shadow(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    engineering_signal_report: Mapping[str, Any],
    technical_reports: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PCT06 metadata-only authoritative report source evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct06-authoritative-reports-shadow"
    ledger_path = state / S2PCT06_LEDGER_FILENAME
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pct06_authoritative_report_source_report(
        generated_at=generated_at,
        engineering_signal_report=engineering_signal_report,
        technical_reports=technical_reports,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "authoritative_report_path": str(run_dir / "adp-s2pct06-authoritative-report-source-report.json"),
            "authoritative_report_ledger_path": str(ledger_path),
            "authoritative_report_ledger_row_count": len(report.get("authoritative_reports") or []),
        }
    )
    if write:
        for row in report.get("authoritative_reports") or []:
            if isinstance(row, Mapping):
                _append_jsonl(ledger_path, row)
    return _write_or_return_s2pct06(report, run_dir, write=write)


def validate_s2pct06_authoritative_report_source_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID:
        errors.append("S2PCT06 authoritative report model_id must be adp-s2pct06-authoritative-reports-v1")
    if report.get("task_id") != S2PCT06_TASK_ID:
        errors.append("S2PCT06 authoritative report task_id must be S2PCT06")
    if report.get("acceptance_id") != S2PCT06_ACCEPTANCE_ID:
        errors.append("S2PCT06 authoritative report acceptance_id must be ACC-S2PCT06-REPORTS")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT06 authoritative report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "marketing_material_accepted",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT06 authoritative report shadow")
    reports = report.get("authoritative_reports")
    if not isinstance(reports, list):
        errors.append("S2PCT06 authoritative_reports must be a list")
        reports = []
    observed = set(report.get("report_types_observed") or [])
    missing = [report_type for report_type in S2PCT06_REQUIRED_REPORT_TYPES if report_type not in observed]
    if missing:
        errors.append("S2PCT06 report taxonomy missing required types: " + ", ".join(missing))
    report_ids: set[str] = set()
    for index, item in enumerate(reports):
        if not isinstance(item, Mapping):
            errors.append(f"authoritative_reports[{index}] must be an object")
            continue
        report_id = str(item.get("report_id") or "")
        if not report_id:
            errors.append(f"authoritative_reports[{index}].report_id is required")
        if report_id in report_ids:
            errors.append(f"duplicate S2PCT06 report_id: {report_id}")
        report_ids.add(report_id)
        if item.get("report_type") not in S2PCT06_REQUIRED_REPORT_TYPES:
            errors.append(f"authoritative_reports[{index}].report_type is not supported")
        if item.get("publisher_type") not in S2PCT06_ALLOWED_PUBLISHER_TYPES:
            errors.append(f"authoritative_reports[{index}].publisher_type is not supported")
        if item.get("publisher_identity_state") not in S2PCT06_ALLOWED_IDENTITY_STATES:
            errors.append(f"authoritative_reports[{index}].publisher_identity_state is not accepted")
        if item.get("interest_relation") not in S2PCT06_ALLOWED_INTEREST_RELATIONS:
            errors.append(f"authoritative_reports[{index}].interest_relation is not accepted")
        if item.get("evidence_level") not in S2PCT06_ALLOWED_EVIDENCE_LEVELS:
            errors.append(f"authoritative_reports[{index}].evidence_level is not accepted")
        if item.get("metadata_only") is not True:
            errors.append(f"authoritative_reports[{index}].metadata_only must be true")
        if item.get("marketing_material_accepted") is not False:
            errors.append(f"authoritative_reports[{index}].marketing_material_accepted must be false")
        if not item.get("source_url"):
            errors.append(f"authoritative_reports[{index}].source_url is required")
        if not item.get("version_reference"):
            errors.append(f"authoritative_reports[{index}].version_reference is required")
        if not item.get("publisher_identity_evidence"):
            errors.append(f"authoritative_reports[{index}].publisher_identity_evidence is required")
        if not item.get("interest_disclosure"):
            errors.append(f"authoritative_reports[{index}].interest_disclosure is required")
        if not item.get("canonical_document_id"):
            errors.append(f"authoritative_reports[{index}].canonical_document_id is required")
        if not item.get("related_signal_ids"):
            errors.append(f"authoritative_reports[{index}].related_signal_ids is required")
        if not item.get("evidence_refs"):
            errors.append(f"authoritative_reports[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT06 authoritative report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "engineering_signal_gate",
            "report_taxonomy_gate",
            "publisher_identity_gate",
            "interest_relation_gate",
            "evidence_level_gate",
            "traceability_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PCT06 authoritative report requires {key}=pass")
    return errors


def build_s2pct07_d2_source_domain_qualification_report(
    *,
    generated_at: str,
    profile_report: Mapping[str, Any],
    engineering_signal_report: Mapping[str, Any],
    authoritative_report: Mapping[str, Any],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    forced_event_records: Sequence[Mapping[str, Any]],
    queue_explanation_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Calibrate D2 source-domain readiness without granting production acceptance."""

    profile_errors = validate_s2pct04_top_journal_profile_report(profile_report)
    engineering_errors = validate_s2pct05_engineering_signal_report(engineering_signal_report)
    report_errors = validate_s2pct06_authoritative_report_source_report(authoritative_report)
    upstream_gate = (
        "pass"
        if not profile_errors
        and not engineering_errors
        and not report_errors
        and profile_report.get("status") == engineering_signal_report.get("status") == authoritative_report.get("status") == "pass"
        else "blocked"
    )
    domain_matrix, domain_errors = _s2pct07_domain_matrix(
        profile_report=profile_report,
        engineering_signal_report=engineering_signal_report,
        authoritative_report=authoritative_report,
    )
    replay_gate = _s2pct07_replay_gate(replay_records)
    shadow_gate = _s2pct07_shadow_gate(shadow_records)
    forced_event_gate = _s2pct07_forced_event_gate(forced_event_records)
    queue_explanation_gate = _s2pct07_queue_explanation_gate(queue_explanation_records)
    type_calibration = _s2pct07_type_calibration(domain_matrix)
    blocking_reasons = [
        *profile_errors,
        *engineering_errors,
        *report_errors,
        *domain_errors,
        *replay_gate["blocking_reasons"],
        *shadow_gate["blocking_reasons"],
        *forced_event_gate["blocking_reasons"],
        *queue_explanation_gate["blocking_reasons"],
        *type_calibration["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PCT07 requires passing S2PCT04, S2PCT05, and S2PCT06 upstream reports")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == replay_gate["status"]
        == shadow_gate["status"]
        == forced_event_gate["status"]
        == queue_explanation_gate["status"]
        == type_calibration["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PCT07_D2_QUALIFICATION_MODEL_ID,
        "acceptance_id": S2PCT07_ACCEPTANCE_ID,
        "task_id": S2PCT07_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_gate": upstream_gate,
        "domain_coverage_gate": "pass" if not domain_errors else "blocked",
        "replay_gate": replay_gate["status"],
        "shadow_gate": shadow_gate["status"],
        "forced_event_gate": forced_event_gate["status"],
        "queue_explanation_gate": queue_explanation_gate["status"],
        "type_calibration_gate": type_calibration["status"],
        "required_domains": list(S2PCT07_REQUIRED_DOMAINS),
        "domain_coverage_matrix": domain_matrix,
        "type_calibration": type_calibration,
        "replay_summary": replay_gate,
        "shadow_summary": shadow_gate,
        "forced_event_summary": forced_event_gate,
        "queue_explanation_summary": queue_explanation_gate,
        "d2_source_domain_qualification_ready": status == "pass",
        "d2_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "marketing_material_accepted": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pct07_d2_source_domain_qualification(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    profile_report: Mapping[str, Any],
    engineering_signal_report: Mapping[str, Any],
    authoritative_report: Mapping[str, Any],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    forced_event_records: Sequence[Mapping[str, Any]],
    queue_explanation_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PCT07 D2 qualification evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct07-d2-source-domain-qualification"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pct07_d2_source_domain_qualification_report(
        generated_at=generated_at,
        profile_report=profile_report,
        engineering_signal_report=engineering_signal_report,
        authoritative_report=authoritative_report,
        replay_records=replay_records,
        shadow_records=shadow_records,
        forced_event_records=forced_event_records,
        queue_explanation_records=queue_explanation_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "qualification_report_path": str(run_dir / "adp-s2pct07-d2-source-domain-qualification-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pct07-d2-source-domain-qualification-report.json", report)
        _write_json(state / S2PCT07_QUALIFICATION_REPORT_FILENAME, report)
    return report


def validate_s2pct07_d2_source_domain_qualification_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT07_D2_QUALIFICATION_MODEL_ID:
        errors.append("S2PCT07 qualification model_id must be adp-s2pct07-d2-source-domain-qualification-v1")
    if report.get("task_id") != S2PCT07_TASK_ID:
        errors.append("S2PCT07 qualification task_id must be S2PCT07")
    if report.get("acceptance_id") != S2PCT07_ACCEPTANCE_ID:
        errors.append("S2PCT07 qualification acceptance_id must be ACC-S2PCT07-D2")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT07 qualification status must be pass or blocked")
    for key in (
        "d2_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "marketing_material_accepted",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT07 qualification evidence")
    matrix = report.get("domain_coverage_matrix")
    if not isinstance(matrix, Mapping):
        errors.append("S2PCT07 domain_coverage_matrix must be an object")
        matrix = {}
    missing_domains = [domain for domain in S2PCT07_REQUIRED_DOMAINS if domain not in matrix]
    if missing_domains:
        errors.append("S2PCT07 domain coverage missing required domains: " + ", ".join(missing_domains))
    for domain in S2PCT07_REQUIRED_DOMAINS:
        row = matrix.get(domain)
        if not isinstance(row, Mapping):
            errors.append(f"S2PCT07 domain_coverage_matrix.{domain} must be an object")
            continue
        if row.get("coverage_gate") != "pass":
            errors.append(f"S2PCT07 domain_coverage_matrix.{domain}.coverage_gate must pass")
        if int(row.get("evidence_count") or 0) < 1:
            errors.append(f"S2PCT07 domain_coverage_matrix.{domain}.evidence_count must be positive")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT07 qualification report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_gate",
            "domain_coverage_gate",
            "replay_gate",
            "shadow_gate",
            "forced_event_gate",
            "queue_explanation_gate",
            "type_calibration_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PCT07 qualification requires {key}=pass")
        if report.get("d2_source_domain_qualification_ready") is not True:
            errors.append("passing S2PCT07 qualification requires d2_source_domain_qualification_ready=true")
    return errors


def build_s2pdt01_china_c0_source_foundation_report(
    *,
    generated_at: str,
    d2_qualification_report: Mapping[str, Any],
    authority_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build C0 China official source foundation evidence without production inclusion."""

    d2_errors = validate_s2pct07_d2_source_domain_qualification_report(d2_qualification_report)
    d2_gate = (
        "pass"
        if not d2_errors
        and d2_qualification_report.get("status") == "pass"
        and d2_qualification_report.get("d2_source_domain_qualification_ready") is True
        else "blocked"
    )
    authority_rows, authority_errors = _s2pdt01_authority_rows(authority_records)
    taxonomy_gate = _s2pdt01_taxonomy_gate(authority_rows)
    identity_gate = _s2pdt01_identity_gate(authority_rows)
    traceability_gate = _s2pdt01_traceability_gate(authority_rows)
    metadata_gate = _s2pdt01_metadata_gate(authority_rows)
    blocking_reasons = [
        *d2_errors,
        *authority_errors,
        *taxonomy_gate["blocking_reasons"],
        *identity_gate["blocking_reasons"],
        *traceability_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if d2_gate != "pass":
        blocking_reasons.append("S2PDT01 requires passing S2PCT07 D2 qualification readiness")
    status = (
        "pass"
        if not blocking_reasons
        and d2_gate
        == taxonomy_gate["status"]
        == identity_gate["status"]
        == traceability_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PDT01_CHINA_C0_SOURCE_MODEL_ID,
        "acceptance_id": S2PDT01_ACCEPTANCE_ID,
        "task_id": S2PDT01_TASK_ID,
        "legacy_task_id": S2PDT01_LEGACY_TASK_ID,
        "phase": "S2PD",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_d2_qualification_gate": d2_gate,
        "authority_taxonomy_gate": taxonomy_gate["status"],
        "official_identity_gate": identity_gate["status"],
        "document_traceability_gate": traceability_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_authority_types": list(S2PDT01_REQUIRED_AUTHORITY_TYPES),
        "authority_types_observed": taxonomy_gate["authority_types_observed"],
        "required_trace_fields": list(S2PDT01_REQUIRED_TRACE_FIELDS),
        "authority_records": authority_rows,
        "authority_record_count": len(authority_rows),
        "taxonomy_summary": taxonomy_gate,
        "identity_summary": identity_gate,
        "traceability_summary": traceability_gate,
        "metadata_summary": metadata_gate,
        "d3_c0_source_foundation_ready": status == "pass",
        "d3_core_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pdt01_china_c0_source_foundation(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    d2_qualification_report: Mapping[str, Any],
    authority_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PDT01 China C0 source foundation evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pdt01-china-c0-source-foundation"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pdt01_china_c0_source_foundation_report(
        generated_at=generated_at,
        d2_qualification_report=d2_qualification_report,
        authority_records=authority_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "source_foundation_report_path": str(run_dir / "adp-s2pdt01-china-c0-source-foundation-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pdt01-china-c0-source-foundation-report.json", report)
        _write_json(state / S2PDT01_REPORT_FILENAME, report)
    return report


def validate_s2pdt01_china_c0_source_foundation_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PDT01_CHINA_C0_SOURCE_MODEL_ID:
        errors.append("S2PDT01 C0 model_id must be adp-s2pdt01-china-c0-source-foundation-v1")
    if report.get("task_id") != S2PDT01_TASK_ID:
        errors.append("S2PDT01 C0 task_id must be S2PDT01")
    if report.get("legacy_task_id") != S2PDT01_LEGACY_TASK_ID:
        errors.append("S2PDT01 C0 legacy_task_id must be S2P3T01")
    if report.get("acceptance_id") != S2PDT01_ACCEPTANCE_ID:
        errors.append("S2PDT01 C0 acceptance_id must be ACC-S2PDT01-C0")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PDT01 C0 status must be pass or blocked")
    for key in (
        "d3_core_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PDT01 C0 source foundation")
    records = report.get("authority_records")
    if not isinstance(records, list):
        errors.append("S2PDT01 authority_records must be a list")
        records = []
    observed = set(report.get("authority_types_observed") or [])
    missing = [authority_type for authority_type in S2PDT01_REQUIRED_AUTHORITY_TYPES if authority_type not in observed]
    if missing:
        errors.append("S2PDT01 C0 taxonomy missing required authority types: " + ", ".join(missing))
    source_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"authority_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "")
        if not source_id:
            errors.append(f"authority_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PDT01 source_id: {source_id}")
        source_ids.add(source_id)
        if record.get("authority_type") not in S2PDT01_REQUIRED_AUTHORITY_TYPES:
            errors.append(f"authority_records[{index}].authority_type is not supported")
        if record.get("identity_state") not in S2PDT01_ALLOWED_IDENTITY_STATES:
            errors.append(f"authority_records[{index}].identity_state is not accepted")
        if record.get("metadata_only") is not True:
            errors.append(f"authority_records[{index}].metadata_only must be true")
        if record.get("pdf_downloaded") is not False:
            errors.append(f"authority_records[{index}].pdf_downloaded must be false")
        if record.get("full_text_extracted") is not False:
            errors.append(f"authority_records[{index}].full_text_extracted must be false")
        for field in S2PDT01_REQUIRED_TRACE_FIELDS:
            if not record.get(field):
                errors.append(f"authority_records[{index}].{field} is required")
        if not record.get("source_url"):
            errors.append(f"authority_records[{index}].source_url is required")
        if not record.get("attachment_trace"):
            errors.append(f"authority_records[{index}].attachment_trace is required")
        if not record.get("evidence_refs"):
            errors.append(f"authority_records[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PDT01 C0 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_d2_qualification_gate",
            "authority_taxonomy_gate",
            "official_identity_gate",
            "document_traceability_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PDT01 C0 report requires {key}=pass")
        if report.get("d3_c0_source_foundation_ready") is not True:
            errors.append("passing S2PDT01 C0 report requires d3_c0_source_foundation_ready=true")
    return errors


def build_s2pdt02_china_c1_department_source_map_report(
    *,
    generated_at: str,
    c0_source_foundation_report: Mapping[str, Any],
    department_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build China C1 central department source-map evidence without production inclusion."""

    c0_errors = validate_s2pdt01_china_c0_source_foundation_report(c0_source_foundation_report)
    c0_gate = (
        "pass"
        if not c0_errors
        and c0_source_foundation_report.get("status") == "pass"
        and c0_source_foundation_report.get("d3_c0_source_foundation_ready") is True
        else "blocked"
    )
    department_rows, department_errors = _s2pdt02_department_rows(department_records)
    sector_gate = _s2pdt02_sector_gate(department_rows)
    identity_gate = _s2pdt02_identity_gate(department_rows)
    alias_gate = _s2pdt02_alias_gate(department_rows)
    route_gate = _s2pdt02_route_gate(department_rows)
    metadata_gate = _s2pdt02_metadata_gate(department_rows)
    blocking_reasons = [
        *c0_errors,
        *department_errors,
        *sector_gate["blocking_reasons"],
        *identity_gate["blocking_reasons"],
        *alias_gate["blocking_reasons"],
        *route_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if c0_gate != "pass":
        blocking_reasons.append("S2PDT02 requires passing S2PDT01 China C0 source foundation")
    status = (
        "pass"
        if not blocking_reasons
        and c0_gate
        == sector_gate["status"]
        == identity_gate["status"]
        == alias_gate["status"]
        == route_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PDT02_CHINA_C1_SOURCE_MODEL_ID,
        "acceptance_id": S2PDT02_ACCEPTANCE_ID,
        "task_id": S2PDT02_TASK_ID,
        "legacy_task_id": S2PDT02_LEGACY_TASK_ID,
        "phase": "S2PD",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_c0_source_foundation_gate": c0_gate,
        "sector_coverage_gate": sector_gate["status"],
        "official_identity_gate": identity_gate["status"],
        "alias_gate": alias_gate["status"],
        "industry_route_gate": route_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_sectors": list(S2PDT02_REQUIRED_SECTORS),
        "sectors_observed": sector_gate["sectors_observed"],
        "required_route_fields": list(S2PDT02_REQUIRED_ROUTE_FIELDS),
        "department_records": department_rows,
        "department_record_count": len(department_rows),
        "sector_summary": sector_gate,
        "identity_summary": identity_gate,
        "alias_summary": alias_gate,
        "route_summary": route_gate,
        "metadata_summary": metadata_gate,
        "d3_c1_department_source_map_ready": status == "pass",
        "d3_core_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pdt02_china_c1_department_source_map(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    c0_source_foundation_report: Mapping[str, Any],
    department_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PDT02 China C1 department source-map evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pdt02-china-c1-department-source-map"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pdt02_china_c1_department_source_map_report(
        generated_at=generated_at,
        c0_source_foundation_report=c0_source_foundation_report,
        department_records=department_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "department_source_map_report_path": str(run_dir / "adp-s2pdt02-china-c1-department-source-map-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pdt02-china-c1-department-source-map-report.json", report)
        _write_json(state / S2PDT02_REPORT_FILENAME, report)
    return report


def validate_s2pdt02_china_c1_department_source_map_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PDT02_CHINA_C1_SOURCE_MODEL_ID:
        errors.append("S2PDT02 C1 model_id must be adp-s2pdt02-china-c1-department-source-map-v1")
    if report.get("task_id") != S2PDT02_TASK_ID:
        errors.append("S2PDT02 C1 task_id must be S2PDT02")
    if report.get("legacy_task_id") != S2PDT02_LEGACY_TASK_ID:
        errors.append("S2PDT02 C1 legacy_task_id must be S2P3T02")
    if report.get("acceptance_id") != S2PDT02_ACCEPTANCE_ID:
        errors.append("S2PDT02 C1 acceptance_id must be ACC-S2PDT02-C1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PDT02 C1 status must be pass or blocked")
    for key in (
        "d3_core_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PDT02 C1 department source map")
    records = report.get("department_records")
    if not isinstance(records, list):
        errors.append("S2PDT02 department_records must be a list")
        records = []
    observed = set(report.get("sectors_observed") or [])
    missing = [sector for sector in S2PDT02_REQUIRED_SECTORS if sector not in observed]
    if missing:
        errors.append("S2PDT02 C1 sector coverage missing required sectors: " + ", ".join(missing))
    source_ids: set[str] = set()
    department_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"department_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "")
        department_id = str(record.get("department_id") or "")
        if not source_id:
            errors.append(f"department_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PDT02 source_id: {source_id}")
        source_ids.add(source_id)
        if not department_id:
            errors.append(f"department_records[{index}].department_id is required")
        if department_id in department_ids:
            errors.append(f"duplicate S2PDT02 department_id: {department_id}")
        department_ids.add(department_id)
        if record.get("sector") not in S2PDT02_REQUIRED_SECTORS:
            errors.append(f"department_records[{index}].sector is not supported")
        if record.get("identity_state") not in S2PDT02_ALLOWED_IDENTITY_STATES:
            errors.append(f"department_records[{index}].identity_state is not accepted")
        if record.get("metadata_only") is not True:
            errors.append(f"department_records[{index}].metadata_only must be true")
        if record.get("pdf_downloaded") is not False:
            errors.append(f"department_records[{index}].pdf_downloaded must be false")
        if record.get("full_text_extracted") is not False:
            errors.append(f"department_records[{index}].full_text_extracted must be false")
        for field in ("department_name", "official_domain", "source_url"):
            if not record.get(field):
                errors.append(f"department_records[{index}].{field} is required")
        for field in ("aliases", "industry_routes", "evidence_refs"):
            if not record.get(field):
                errors.append(f"department_records[{index}].{field} is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PDT02 C1 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_c0_source_foundation_gate",
            "sector_coverage_gate",
            "official_identity_gate",
            "alias_gate",
            "industry_route_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PDT02 C1 report requires {key}=pass")
        if report.get("d3_c1_department_source_map_ready") is not True:
            errors.append("passing S2PDT02 C1 report requires d3_c1_department_source_map_ready=true")
    return errors


def build_s2pdt03_china_legal_metadata_relation_shadow_report(
    *,
    generated_at: str,
    c1_department_source_map_report: Mapping[str, Any],
    legal_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
    prior_conclusion_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build China legal status/version/reprint relation evidence without production inclusion."""

    c1_errors = validate_s2pdt02_china_c1_department_source_map_report(c1_department_source_map_report)
    c1_gate = (
        "pass"
        if not c1_errors
        and c1_department_source_map_report.get("status") == "pass"
        and c1_department_source_map_report.get("d3_c1_department_source_map_ready") is True
        else "blocked"
    )
    legal_rows, legal_errors = _s2pdt03_legal_rows(legal_records)
    relation_rows, relation_errors = _s2pdt03_relation_rows(relation_records, legal_rows)
    prior_rows, prior_errors = _s2pdt03_prior_conclusion_rows(prior_conclusion_records, legal_rows)
    status_gate = _s2pdt03_legal_status_gate(legal_rows)
    effectivity_gate = _s2pdt03_version_effectivity_gate(legal_rows, relation_rows)
    reprint_gate = _s2pdt03_reprint_relation_gate(relation_rows)
    forced_update_gate = _s2pdt03_forced_update_gate(relation_rows, prior_rows)
    metadata_gate = _s2pdt03_metadata_gate(legal_rows, relation_rows)
    blocking_reasons = [
        *c1_errors,
        *legal_errors,
        *relation_errors,
        *prior_errors,
        *status_gate["blocking_reasons"],
        *effectivity_gate["blocking_reasons"],
        *reprint_gate["blocking_reasons"],
        *forced_update_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if c1_gate != "pass":
        blocking_reasons.append("S2PDT03 requires passing S2PDT02 China C1 department source map")
    status = (
        "pass"
        if not blocking_reasons
        and c1_gate
        == status_gate["status"]
        == effectivity_gate["status"]
        == reprint_gate["status"]
        == forced_update_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PDT03_LEGAL_METADATA_MODEL_ID,
        "acceptance_id": S2PDT03_ACCEPTANCE_ID,
        "task_id": S2PDT03_TASK_ID,
        "legacy_task_id": S2PDT03_LEGACY_TASK_ID,
        "phase": "S2PD",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_c1_department_source_map_gate": c1_gate,
        "legal_status_taxonomy_gate": status_gate["status"],
        "version_effectivity_gate": effectivity_gate["status"],
        "reprint_relation_gate": reprint_gate["status"],
        "forced_update_gate": forced_update_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_legal_statuses": list(S2PDT03_REQUIRED_LEGAL_STATUSES),
        "legal_statuses_observed": status_gate["legal_statuses_observed"],
        "required_relation_types": list(S2PDT03_REQUIRED_RELATION_TYPES),
        "relation_types_observed": effectivity_gate["relation_types_observed"],
        "required_date_fields": list(S2PDT03_REQUIRED_DATE_FIELDS),
        "required_forced_update_fields": list(S2PDT03_REQUIRED_FORCED_UPDATE_FIELDS),
        "legal_records": legal_rows,
        "relation_records": relation_rows,
        "prior_conclusion_records": prior_rows,
        "legal_record_count": len(legal_rows),
        "relation_record_count": len(relation_rows),
        "prior_conclusion_record_count": len(prior_rows),
        "legal_status_summary": status_gate,
        "version_effectivity_summary": effectivity_gate,
        "reprint_relation_summary": reprint_gate,
        "forced_update_summary": forced_update_gate,
        "metadata_summary": metadata_gate,
        "d3_legal_metadata_relation_shadow_ready": status == "pass",
        "legal_advice_provided": False,
        "v7_1_current_switched": False,
        "v7_2_mail_or_schema_prerun": False,
        "d3_core_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pdt03_china_legal_metadata_relation_shadow(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    c1_department_source_map_report: Mapping[str, Any],
    legal_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
    prior_conclusion_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PDT03 legal metadata relation evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pdt03-china-legal-metadata-relation-shadow"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pdt03_china_legal_metadata_relation_shadow_report(
        generated_at=generated_at,
        c1_department_source_map_report=c1_department_source_map_report,
        legal_records=legal_records,
        relation_records=relation_records,
        prior_conclusion_records=prior_conclusion_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "legal_metadata_relation_report_path": str(run_dir / "adp-s2pdt03-china-legal-metadata-relation-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pdt03-china-legal-metadata-relation-report.json", report)
        _write_json(state / S2PDT03_REPORT_FILENAME, report)
    return report


def validate_s2pdt03_china_legal_metadata_relation_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PDT03_LEGAL_METADATA_MODEL_ID:
        errors.append("S2PDT03 legal model_id must be adp-s2pdt03-china-legal-metadata-relation-shadow-v1")
    if report.get("task_id") != S2PDT03_TASK_ID:
        errors.append("S2PDT03 legal task_id must be S2PDT03")
    if report.get("legacy_task_id") != S2PDT03_LEGACY_TASK_ID:
        errors.append("S2PDT03 legal legacy_task_id must be S2P3T03")
    if report.get("acceptance_id") != S2PDT03_ACCEPTANCE_ID:
        errors.append("S2PDT03 legal acceptance_id must be ACC-S2PDT03-LEGAL")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PDT03 legal status must be pass or blocked")
    for key in (
        "legal_advice_provided",
        "v7_1_current_switched",
        "v7_2_mail_or_schema_prerun",
        "d3_core_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PDT03 legal metadata relation shadow")
    records = report.get("legal_records")
    if not isinstance(records, list):
        errors.append("S2PDT03 legal_records must be a list")
        records = []
    relations = report.get("relation_records")
    if not isinstance(relations, list):
        errors.append("S2PDT03 relation_records must be a list")
        relations = []
    prior_records = report.get("prior_conclusion_records")
    if not isinstance(prior_records, list):
        errors.append("S2PDT03 prior_conclusion_records must be a list")
        prior_records = []
    legal_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"legal_records[{index}] must be an object")
            continue
        legal_id = str(record.get("legal_id") or "")
        if not legal_id:
            errors.append(f"legal_records[{index}].legal_id is required")
        if legal_id in legal_ids:
            errors.append(f"duplicate S2PDT03 legal_id: {legal_id}")
        legal_ids.add(legal_id)
        if record.get("legal_status") not in S2PDT03_REQUIRED_LEGAL_STATUSES:
            errors.append(f"legal_records[{index}].legal_status is not supported")
        if record.get("identity_state") not in S2PDT03_ALLOWED_IDENTITY_STATES:
            errors.append(f"legal_records[{index}].identity_state is not accepted")
        for field in ("source_id", "title", "official_domain", "source_url", *S2PDT03_REQUIRED_DATE_FIELDS):
            if not record.get(field):
                errors.append(f"legal_records[{index}].{field} is required")
        if record.get("metadata_only") is not True:
            errors.append(f"legal_records[{index}].metadata_only must be true")
        if record.get("pdf_downloaded") is not False:
            errors.append(f"legal_records[{index}].pdf_downloaded must be false")
        if record.get("full_text_extracted") is not False:
            errors.append(f"legal_records[{index}].full_text_extracted must be false")
        if not record.get("evidence_refs"):
            errors.append(f"legal_records[{index}].evidence_refs is required")
    relation_ids: set[str] = set()
    for index, relation in enumerate(relations):
        if not isinstance(relation, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_id = str(relation.get("relation_id") or "")
        if not relation_id:
            errors.append(f"relation_records[{index}].relation_id is required")
        if relation_id in relation_ids:
            errors.append(f"duplicate S2PDT03 relation_id: {relation_id}")
        relation_ids.add(relation_id)
        if relation.get("relation_type") not in S2PDT03_REQUIRED_RELATION_TYPES:
            errors.append(f"relation_records[{index}].relation_type is not supported")
        for field in ("source_legal_id", "target_legal_id", "relation_date"):
            if not relation.get(field):
                errors.append(f"relation_records[{index}].{field} is required")
        if relation.get("metadata_only") is not True:
            errors.append(f"relation_records[{index}].metadata_only must be true")
        if not relation.get("evidence_refs"):
            errors.append(f"relation_records[{index}].evidence_refs is required")
    observed_statuses = set(report.get("legal_statuses_observed") or [])
    missing_statuses = [status for status in S2PDT03_REQUIRED_LEGAL_STATUSES if status not in observed_statuses]
    if missing_statuses:
        errors.append("S2PDT03 legal status coverage missing required statuses: " + ", ".join(missing_statuses))
    observed_relations = set(report.get("relation_types_observed") or [])
    missing_relations = [relation for relation in S2PDT03_REQUIRED_RELATION_TYPES if relation not in observed_relations]
    if missing_relations:
        errors.append("S2PDT03 legal relation coverage missing required relation types: " + ", ".join(missing_relations))
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PDT03 legal report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_c1_department_source_map_gate",
            "legal_status_taxonomy_gate",
            "version_effectivity_gate",
            "reprint_relation_gate",
            "forced_update_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PDT03 legal report requires {key}=pass")
        if report.get("d3_legal_metadata_relation_shadow_ready") is not True:
            errors.append("passing S2PDT03 legal report requires d3_legal_metadata_relation_shadow_ready=true")
    return errors


def build_s2pdt04_china_d3_readiness_review_report(
    *,
    generated_at: str,
    c0_source_foundation_report: Mapping[str, Any],
    c1_department_source_map_report: Mapping[str, Any],
    legal_metadata_relation_report: Mapping[str, Any],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    board_route_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build China D3 core replay/shadow/routing readiness without production inclusion."""

    c0_errors = validate_s2pdt01_china_c0_source_foundation_report(c0_source_foundation_report)
    c1_errors = validate_s2pdt02_china_c1_department_source_map_report(c1_department_source_map_report)
    legal_errors = validate_s2pdt03_china_legal_metadata_relation_shadow_report(legal_metadata_relation_report)
    c0_gate = (
        "pass"
        if not c0_errors
        and c0_source_foundation_report.get("status") == "pass"
        and c0_source_foundation_report.get("d3_c0_source_foundation_ready") is True
        else "blocked"
    )
    c1_gate = (
        "pass"
        if not c1_errors
        and c1_department_source_map_report.get("status") == "pass"
        and c1_department_source_map_report.get("d3_c1_department_source_map_ready") is True
        else "blocked"
    )
    legal_gate = (
        "pass"
        if not legal_errors
        and legal_metadata_relation_report.get("status") == "pass"
        and legal_metadata_relation_report.get("d3_legal_metadata_relation_shadow_ready") is True
        else "blocked"
    )
    replay_rows, replay_errors = _s2pdt04_replay_rows(replay_records)
    shadow_rows, shadow_errors = _s2pdt04_shadow_rows(shadow_records)
    route_rows, route_errors = _s2pdt04_board_route_rows(board_route_records)
    replay_gate = _s2pdt04_replay_gate(replay_rows)
    shadow_gate = _s2pdt04_shadow_gate(shadow_rows)
    authority_gate = _s2pdt04_authority_gate(replay_rows, shadow_rows, route_rows)
    route_gate = _s2pdt04_board_routing_gate(route_rows)
    metadata_gate = _s2pdt04_metadata_gate(replay_rows, shadow_rows, route_rows)
    upstream_gate = "pass" if c0_gate == c1_gate == legal_gate == "pass" else "blocked"
    blocking_reasons = [
        *c0_errors,
        *c1_errors,
        *legal_errors,
        *replay_errors,
        *shadow_errors,
        *route_errors,
        *replay_gate["blocking_reasons"],
        *shadow_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *route_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PDT04 requires passing S2PDT01 C0, S2PDT02 C1, and S2PDT03 legal metadata reports")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == replay_gate["status"]
        == shadow_gate["status"]
        == authority_gate["status"]
        == route_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PDT04_D3_READINESS_MODEL_ID,
        "acceptance_id": S2PDT04_ACCEPTANCE_ID,
        "task_id": S2PDT04_TASK_ID,
        "legacy_task_id": S2PDT04_LEGACY_TASK_ID,
        "phase": "S2PD",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_source_evidence_gate": upstream_gate,
        "upstream_c0_source_foundation_gate": c0_gate,
        "upstream_c1_department_source_map_gate": c1_gate,
        "upstream_legal_metadata_relation_gate": legal_gate,
        "d3_replay_gate": replay_gate["status"],
        "d3_shadow_gate": shadow_gate["status"],
        "authority_gate": authority_gate["status"],
        "board_routing_gate": route_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_replay_dates": S2PDT04_REQUIRED_REPLAY_DATES,
        "replay_dates_observed": replay_gate["replay_dates_observed"],
        "required_shadow_days": S2PDT04_REQUIRED_SHADOW_DAYS,
        "shadow_dates_observed": shadow_gate["shadow_dates_observed"],
        "required_board_ids": list(S2PDT04_REQUIRED_BOARD_IDS),
        "board_ids_observed": route_gate["board_ids_observed"],
        "required_route_fields": list(S2PDT04_REQUIRED_ROUTE_FIELDS),
        "replay_records": replay_rows,
        "shadow_records": shadow_rows,
        "board_route_records": route_rows,
        "replay_record_count": len(replay_rows),
        "shadow_record_count": len(shadow_rows),
        "board_route_record_count": len(route_rows),
        "replay_summary": replay_gate,
        "shadow_summary": shadow_gate,
        "authority_summary": authority_gate,
        "board_routing_summary": route_gate,
        "metadata_summary": metadata_gate,
        "d3_core_readiness_review_ready": status == "pass",
        "d3_core_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_mail_or_schema_prerun": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pdt04_china_d3_readiness_review(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    c0_source_foundation_report: Mapping[str, Any],
    c1_department_source_map_report: Mapping[str, Any],
    legal_metadata_relation_report: Mapping[str, Any],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    board_route_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PDT04 China D3 readiness review evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pdt04-china-d3-readiness-review"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pdt04_china_d3_readiness_review_report(
        generated_at=generated_at,
        c0_source_foundation_report=c0_source_foundation_report,
        c1_department_source_map_report=c1_department_source_map_report,
        legal_metadata_relation_report=legal_metadata_relation_report,
        replay_records=replay_records,
        shadow_records=shadow_records,
        board_route_records=board_route_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "d3_readiness_review_report_path": str(run_dir / "adp-s2pdt04-china-d3-readiness-review-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pdt04-china-d3-readiness-review-report.json", report)
        _write_json(state / S2PDT04_REPORT_FILENAME, report)
    return report


def validate_s2pdt04_china_d3_readiness_review_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PDT04_D3_READINESS_MODEL_ID:
        errors.append("S2PDT04 D3 readiness model_id must be adp-s2pdt04-china-d3-readiness-review-v1")
    if report.get("task_id") != S2PDT04_TASK_ID:
        errors.append("S2PDT04 D3 readiness task_id must be S2PDT04")
    if report.get("legacy_task_id") != S2PDT04_LEGACY_TASK_ID:
        errors.append("S2PDT04 D3 readiness legacy_task_id must be S2P3T04")
    if report.get("acceptance_id") != S2PDT04_ACCEPTANCE_ID:
        errors.append("S2PDT04 D3 readiness acceptance_id must be ACC-S2PDT04-D3-CORE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PDT04 D3 readiness status must be pass or blocked")
    for key in (
        "d3_core_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_mail_or_schema_prerun",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PDT04 D3 readiness review")
    replay_records = report.get("replay_records")
    if not isinstance(replay_records, list):
        errors.append("S2PDT04 replay_records must be a list")
        replay_records = []
    shadow_records = report.get("shadow_records")
    if not isinstance(shadow_records, list):
        errors.append("S2PDT04 shadow_records must be a list")
        shadow_records = []
    route_records = report.get("board_route_records")
    if not isinstance(route_records, list):
        errors.append("S2PDT04 board_route_records must be a list")
        route_records = []
    observed_dates = set(report.get("replay_dates_observed") or [])
    if len(observed_dates) < S2PDT04_REQUIRED_REPLAY_DATES:
        errors.append("S2PDT04 replay coverage requires at least 30 distinct dates")
    observed_shadow_dates = set(report.get("shadow_dates_observed") or [])
    if len(observed_shadow_dates) < S2PDT04_REQUIRED_SHADOW_DAYS:
        errors.append("S2PDT04 shadow coverage requires at least 2 distinct dates")
    observed_boards = set(report.get("board_ids_observed") or [])
    missing_boards = [board for board in S2PDT04_REQUIRED_BOARD_IDS if board not in observed_boards]
    if missing_boards:
        errors.append("S2PDT04 board routing missing required boards: " + ", ".join(missing_boards))
    for index, record in enumerate(replay_records):
        if not isinstance(record, Mapping):
            errors.append(f"replay_records[{index}] must be an object")
            continue
        if not _is_iso_date(str(record.get("as_of_date") or "")):
            errors.append(f"replay_records[{index}].as_of_date must be YYYY-MM-DD")
        if record.get("status") != "pass":
            errors.append(f"replay_records[{index}].status must be pass")
        for key in ("future_leakage_count", "p0_p1_blocker_count"):
            if int(record.get(key) or 0) != 0:
                errors.append(f"replay_records[{index}].{key} must be 0")
        for key in ("authority_gate", "board_route_gate"):
            if record.get(key) != "pass":
                errors.append(f"replay_records[{index}].{key} must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"replay_records[{index}].metadata_only must be true")
    for index, record in enumerate(shadow_records):
        if not isinstance(record, Mapping):
            errors.append(f"shadow_records[{index}] must be an object")
            continue
        if not _is_iso_date(str(record.get("shadow_date") or "")):
            errors.append(f"shadow_records[{index}].shadow_date must be YYYY-MM-DD")
        if record.get("status") != "pass":
            errors.append(f"shadow_records[{index}].status must be pass")
        if record.get("production_affected") is not False:
            errors.append(f"shadow_records[{index}].production_affected must be false")
        if record.get("real_smtp_sent") is not False:
            errors.append(f"shadow_records[{index}].real_smtp_sent must be false")
    for index, record in enumerate(route_records):
        if not isinstance(record, Mapping):
            errors.append(f"board_route_records[{index}] must be an object")
            continue
        for field in S2PDT04_REQUIRED_ROUTE_FIELDS:
            if field not in record:
                errors.append(f"board_route_records[{index}].{field} is required")
        if record.get("board_id") not in S2PDT04_REQUIRED_BOARD_IDS:
            errors.append(f"board_route_records[{index}].board_id is not supported")
        if not record.get("source_ids"):
            errors.append(f"board_route_records[{index}].source_ids is required")
        if not record.get("route_explanation"):
            errors.append(f"board_route_records[{index}].route_explanation is required")
        if record.get("authority_gate") != "pass":
            errors.append(f"board_route_records[{index}].authority_gate must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"board_route_records[{index}].metadata_only must be true")
        if record.get("production_affected") is not False:
            errors.append(f"board_route_records[{index}].production_affected must be false")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PDT04 D3 readiness report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_source_evidence_gate",
            "d3_replay_gate",
            "d3_shadow_gate",
            "authority_gate",
            "board_routing_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PDT04 D3 readiness report requires {key}=pass")
        if report.get("d3_core_readiness_review_ready") is not True:
            errors.append("passing S2PDT04 D3 readiness report requires d3_core_readiness_review_ready=true")
    return errors


def build_s2pft01_china_provincial_template_coverage_report(
    *,
    generated_at: str,
    d3_readiness_review_report: Mapping[str, Any],
    provincial_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build mainland provincial template coverage evidence without production inclusion."""

    d3_errors = validate_s2pdt04_china_d3_readiness_review_report(d3_readiness_review_report)
    d3_gate = (
        "pass"
        if not d3_errors
        and d3_readiness_review_report.get("status") == "pass"
        and d3_readiness_review_report.get("d3_core_readiness_review_ready") is True
        else "blocked"
    )
    province_rows, row_errors = _s2pft01_provincial_rows(provincial_records)
    coverage_gate = _s2pft01_provincial_coverage_gate(province_rows)
    department_gate = _s2pft01_core_department_gate(province_rows)
    health_gate = _s2pft01_health_tier_gate(province_rows)
    authority_gate = _s2pft01_provincial_authority_gate(province_rows)
    metadata_gate = _s2pft01_provincial_metadata_gate(province_rows)
    blocking_reasons = [
        *d3_errors,
        *row_errors,
        *coverage_gate["blocking_reasons"],
        *department_gate["blocking_reasons"],
        *health_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if d3_gate != "pass":
        blocking_reasons.append("S2PFT01 requires passing S2PDT04 China D3 readiness review evidence")
    status = (
        "pass"
        if not blocking_reasons
        and d3_gate
        == coverage_gate["status"]
        == department_gate["status"]
        == health_gate["status"]
        == authority_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PFT01_CHINA_PROVINCIAL_MODEL_ID,
        "acceptance_id": S2PFT01_ACCEPTANCE_ID,
        "task_id": S2PFT01_TASK_ID,
        "legacy_task_id": S2PFT01_LEGACY_TASK_ID,
        "phase": "S2PF",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_d3_readiness_gate": d3_gate,
        "provincial_coverage_gate": coverage_gate["status"],
        "core_department_template_gate": department_gate["status"],
        "health_tier_gate": health_gate["status"],
        "authority_gate": authority_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_mainland_provincial_ids": list(S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS),
        "required_mainland_provincial_count": len(S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS),
        "provincial_ids_observed": coverage_gate["provincial_ids_observed"],
        "provincial_record_count": len(province_rows),
        "required_locality_types": list(S2PFT01_REQUIRED_LOCALITY_TYPES),
        "locality_types_observed": coverage_gate["locality_types_observed"],
        "required_core_department_roles": list(S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES),
        "health_tiers_observed": health_gate["health_tiers_observed"],
        "provincial_records": province_rows,
        "provincial_coverage_summary": coverage_gate,
        "core_department_template_summary": department_gate,
        "health_tier_summary": health_gate,
        "authority_summary": authority_gate,
        "metadata_summary": metadata_gate,
        "s2pf_provincial_template_coverage_ready": status == "pass",
        "d3_full_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "v7_2_mail_or_schema_prerun": False,
        "hk_mo_profile_modeled": False,
        "city_coverage_modeled": False,
        "special_zone_discovery_enabled": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pft01_china_provincial_template_coverage(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    d3_readiness_review_report: Mapping[str, Any],
    provincial_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PFT01 China provincial template coverage evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pft01-china-provincial-template-coverage"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pft01_china_provincial_template_coverage_report(
        generated_at=generated_at,
        d3_readiness_review_report=d3_readiness_review_report,
        provincial_records=provincial_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "provincial_template_coverage_report_path": str(
                run_dir / "adp-s2pft01-china-provincial-template-coverage-report.json"
            ),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pft01-china-provincial-template-coverage-report.json", report)
        _write_json(state / S2PFT01_REPORT_FILENAME, report)
    return report


def validate_s2pft01_china_provincial_template_coverage_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PFT01_CHINA_PROVINCIAL_MODEL_ID:
        errors.append("S2PFT01 provincial model_id must be adp-s2pft01-china-provincial-template-coverage-v1")
    if report.get("task_id") != S2PFT01_TASK_ID:
        errors.append("S2PFT01 provincial task_id must be S2PFT01")
    if report.get("legacy_task_id") != S2PFT01_LEGACY_TASK_ID:
        errors.append("S2PFT01 provincial legacy_task_id must be S2P5T01")
    if report.get("acceptance_id") != S2PFT01_ACCEPTANCE_ID:
        errors.append("S2PFT01 provincial acceptance_id must be ACC-S2PFT01-PROVINCES")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PFT01 provincial status must be pass or blocked")
    for key in (
        "d3_full_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
        "v7_2_mail_or_schema_prerun",
        "hk_mo_profile_modeled",
        "city_coverage_modeled",
        "special_zone_discovery_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PFT01 provincial template coverage")
    provincial_records = report.get("provincial_records")
    if not isinstance(provincial_records, list):
        errors.append("S2PFT01 provincial_records must be a list")
        provincial_records = []
    observed_ids = set(report.get("provincial_ids_observed") or [])
    missing_ids = [province_id for province_id in S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS if province_id not in observed_ids]
    if missing_ids:
        errors.append("S2PFT01 missing mainland provincial ids: " + ", ".join(missing_ids))
    observed_types = set(report.get("locality_types_observed") or [])
    missing_types = [locality_type for locality_type in S2PFT01_REQUIRED_LOCALITY_TYPES if locality_type not in observed_types]
    if missing_types:
        errors.append("S2PFT01 missing locality types: " + ", ".join(missing_types))
    for index, record in enumerate(provincial_records):
        if not isinstance(record, Mapping):
            errors.append(f"provincial_records[{index}] must be an object")
            continue
        if record.get("province_id") not in S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS:
            errors.append(f"provincial_records[{index}].province_id is not supported")
        if record.get("locality_type") not in S2PFT01_REQUIRED_LOCALITY_TYPES:
            errors.append(f"provincial_records[{index}].locality_type is not supported")
        if not record.get("province_name"):
            errors.append(f"provincial_records[{index}].province_name is required")
        for field in ("official_domain", "source_url", "health_explanation"):
            if not record.get(field):
                errors.append(f"provincial_records[{index}].{field} is required")
        if record.get("identity_state") not in S2PFT01_ALLOWED_IDENTITY_STATES:
            errors.append(f"provincial_records[{index}].identity_state is not supported")
        if record.get("health_tier") not in S2PFT01_ALLOWED_HEALTH_TIERS:
            errors.append(f"provincial_records[{index}].health_tier is not supported")
        missing_roles = [
            role for role in S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES if role not in set(record.get("core_department_roles") or [])
        ]
        if missing_roles:
            errors.append(f"provincial_records[{index}] missing core roles: " + ", ".join(missing_roles))
        if record.get("authority_gate") != "pass":
            errors.append(f"provincial_records[{index}].authority_gate must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"provincial_records[{index}].metadata_only must be true")
        for field in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if record.get(field) is not False:
                errors.append(f"provincial_records[{index}].{field} must be false")
        if not record.get("evidence_refs"):
            errors.append(f"provincial_records[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PFT01 provincial report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_d3_readiness_gate",
            "provincial_coverage_gate",
            "core_department_template_gate",
            "health_tier_gate",
            "authority_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PFT01 provincial report requires {key}=pass")
        if report.get("s2pf_provincial_template_coverage_ready") is not True:
            errors.append("passing S2PFT01 provincial report requires s2pf_provincial_template_coverage_ready=true")
    return errors


def build_s2pft02_hk_mo_independent_profile_report(
    *,
    generated_at: str,
    provincial_template_coverage_report: Mapping[str, Any],
    jurisdiction_profiles: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build Hong Kong and Macau independent profile evidence without production inclusion."""

    upstream_errors = validate_s2pft01_china_provincial_template_coverage_report(provincial_template_coverage_report)
    upstream_gate = (
        "pass"
        if not upstream_errors
        and provincial_template_coverage_report.get("status") == "pass"
        and provincial_template_coverage_report.get("s2pf_provincial_template_coverage_ready") is True
        else "blocked"
    )
    profiles, profile_errors = _s2pft02_jurisdiction_profiles(jurisdiction_profiles)
    jurisdiction_gate = _s2pft02_jurisdiction_coverage_gate(profiles)
    language_gate = _s2pft02_language_gate(profiles)
    legal_gate = _s2pft02_legal_status_gate(profiles)
    independence_gate = _s2pft02_template_independence_gate(profiles)
    authority_gate = _s2pft02_authority_gate(profiles)
    metadata_gate = _s2pft02_metadata_gate(profiles)
    blocking_reasons = [
        *upstream_errors,
        *profile_errors,
        *jurisdiction_gate["blocking_reasons"],
        *language_gate["blocking_reasons"],
        *legal_gate["blocking_reasons"],
        *independence_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PFT02 requires passing S2PFT01 provincial template coverage evidence")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == jurisdiction_gate["status"]
        == language_gate["status"]
        == legal_gate["status"]
        == independence_gate["status"]
        == authority_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PFT02_HK_MO_PROFILE_MODEL_ID,
        "acceptance_id": S2PFT02_ACCEPTANCE_ID,
        "task_id": S2PFT02_TASK_ID,
        "legacy_task_id": S2PFT02_LEGACY_TASK_ID,
        "phase": "S2PF",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_provincial_template_gate": upstream_gate,
        "jurisdiction_coverage_gate": jurisdiction_gate["status"],
        "language_profile_gate": language_gate["status"],
        "legal_status_gate": legal_gate["status"],
        "template_independence_gate": independence_gate["status"],
        "authority_gate": authority_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_jurisdiction_ids": list(S2PFT02_REQUIRED_JURISDICTION_IDS),
        "jurisdiction_ids_observed": jurisdiction_gate["jurisdiction_ids_observed"],
        "jurisdiction_profile_count": len(profiles),
        "required_language_profiles": list(S2PFT02_REQUIRED_LANGUAGE_PROFILES),
        "language_profiles_observed": language_gate["language_profiles_observed"],
        "required_profile_fields": list(S2PFT02_REQUIRED_PROFILE_FIELDS),
        "allowed_legal_system_states": list(S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES),
        "legal_system_states_observed": legal_gate["legal_system_states_observed"],
        "jurisdiction_profiles": profiles,
        "jurisdiction_coverage_summary": jurisdiction_gate,
        "language_profile_summary": language_gate,
        "legal_status_summary": legal_gate,
        "template_independence_summary": independence_gate,
        "authority_summary": authority_gate,
        "metadata_summary": metadata_gate,
        "s2pf_hk_mo_profile_ready": status == "pass",
        "d3_full_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "v7_2_mail_or_schema_prerun": False,
        "hk_mo_profile_modeled": status == "pass",
        "mainland_template_applied_to_hk_mo": False,
        "city_coverage_modeled": False,
        "special_zone_discovery_enabled": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pft02_hk_mo_independent_profile(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    provincial_template_coverage_report: Mapping[str, Any],
    jurisdiction_profiles: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PFT02 Hong Kong/Macau profile evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pft02-hk-mo-independent-profile"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pft02_hk_mo_independent_profile_report(
        generated_at=generated_at,
        provincial_template_coverage_report=provincial_template_coverage_report,
        jurisdiction_profiles=jurisdiction_profiles,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "hk_mo_profile_report_path": str(run_dir / "adp-s2pft02-hk-mo-independent-profile-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pft02-hk-mo-independent-profile-report.json", report)
        _write_json(state / S2PFT02_REPORT_FILENAME, report)
    return report


def validate_s2pft02_hk_mo_independent_profile_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PFT02_HK_MO_PROFILE_MODEL_ID:
        errors.append("S2PFT02 HK/MO model_id must be adp-s2pft02-hk-mo-independent-profile-v1")
    if report.get("task_id") != S2PFT02_TASK_ID:
        errors.append("S2PFT02 HK/MO task_id must be S2PFT02")
    if report.get("legacy_task_id") != S2PFT02_LEGACY_TASK_ID:
        errors.append("S2PFT02 HK/MO legacy_task_id must be S2P5T02")
    if report.get("acceptance_id") != S2PFT02_ACCEPTANCE_ID:
        errors.append("S2PFT02 HK/MO acceptance_id must be ACC-S2PFT02-HK-MO")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PFT02 HK/MO status must be pass or blocked")
    for key in (
        "d3_full_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
        "v7_2_mail_or_schema_prerun",
        "mainland_template_applied_to_hk_mo",
        "city_coverage_modeled",
        "special_zone_discovery_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PFT02 HK/MO profile evidence")
    profiles = report.get("jurisdiction_profiles")
    if not isinstance(profiles, list):
        errors.append("S2PFT02 jurisdiction_profiles must be a list")
        profiles = []
    observed_ids = set(report.get("jurisdiction_ids_observed") or [])
    missing_ids = [jurisdiction_id for jurisdiction_id in S2PFT02_REQUIRED_JURISDICTION_IDS if jurisdiction_id not in observed_ids]
    if missing_ids:
        errors.append("S2PFT02 missing jurisdiction ids: " + ", ".join(missing_ids))
    observed_languages = set(report.get("language_profiles_observed") or [])
    missing_languages = [
        language_profile for language_profile in S2PFT02_REQUIRED_LANGUAGE_PROFILES if language_profile not in observed_languages
    ]
    if missing_languages:
        errors.append("S2PFT02 missing language profiles: " + ", ".join(missing_languages))
    observed_legal_states = set(report.get("legal_system_states_observed") or [])
    for state in S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES:
        if state not in observed_legal_states:
            errors.append(f"S2PFT02 missing legal system state: {state}")
    for index, profile in enumerate(profiles):
        if not isinstance(profile, Mapping):
            errors.append(f"jurisdiction_profiles[{index}] must be an object")
            continue
        if profile.get("jurisdiction_id") not in S2PFT02_REQUIRED_JURISDICTION_IDS:
            errors.append(f"jurisdiction_profiles[{index}].jurisdiction_id is not supported")
        for field in S2PFT02_REQUIRED_PROFILE_FIELDS:
            if profile.get(field) in (None, "", []):
                errors.append(f"jurisdiction_profiles[{index}].{field} is required")
        if profile.get("legal_system_state") not in S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES:
            errors.append(f"jurisdiction_profiles[{index}].legal_system_state is not supported")
        if profile.get("template_source") in S2PFT02_FORBIDDEN_TEMPLATE_STATES:
            errors.append(f"jurisdiction_profiles[{index}].template_source must not be mainland template")
        if profile.get("mainland_template_applied") is not False:
            errors.append(f"jurisdiction_profiles[{index}].mainland_template_applied must be false")
        if profile.get("authority_gate") != "pass":
            errors.append(f"jurisdiction_profiles[{index}].authority_gate must be pass")
        if profile.get("metadata_only") is not True:
            errors.append(f"jurisdiction_profiles[{index}].metadata_only must be true")
        for field in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if profile.get(field) is not False:
                errors.append(f"jurisdiction_profiles[{index}].{field} must be false")
        if not profile.get("language_profiles"):
            errors.append(f"jurisdiction_profiles[{index}].language_profiles is required")
        if not profile.get("evidence_refs"):
            errors.append(f"jurisdiction_profiles[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PFT02 HK/MO report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_provincial_template_gate",
            "jurisdiction_coverage_gate",
            "language_profile_gate",
            "legal_status_gate",
            "template_independence_gate",
            "authority_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PFT02 HK/MO report requires {key}=pass")
        if report.get("s2pf_hk_mo_profile_ready") is not True:
            errors.append("passing S2PFT02 HK/MO report requires s2pf_hk_mo_profile_ready=true")
        if report.get("hk_mo_profile_modeled") is not True:
            errors.append("passing S2PFT02 HK/MO report requires hk_mo_profile_modeled=true")
    return errors


def build_s2pft03_key_city_coverage_report(
    *,
    generated_at: str,
    hk_mo_profile_report: Mapping[str, Any],
    city_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build first key-city metadata coverage evidence without production inclusion."""

    upstream_errors = validate_s2pft02_hk_mo_independent_profile_report(hk_mo_profile_report)
    upstream_gate = (
        "pass"
        if not upstream_errors
        and hk_mo_profile_report.get("status") == "pass"
        and hk_mo_profile_report.get("s2pf_hk_mo_profile_ready") is True
        else "blocked"
    )
    city_rows, row_errors = _s2pft03_city_rows(city_records)
    coverage_gate = _s2pft03_city_coverage_gate(city_rows)
    alias_gate = _s2pft03_city_alias_gate(city_rows)
    department_gate = _s2pft03_city_department_gate(city_rows)
    region_gate = _s2pft03_region_weight_gate(city_rows)
    health_gate = _s2pft03_city_health_gate(city_rows)
    authority_gate = _s2pft03_city_authority_gate(city_rows)
    metadata_gate = _s2pft03_city_metadata_gate(city_rows)
    blocking_reasons = [
        *upstream_errors,
        *row_errors,
        *coverage_gate["blocking_reasons"],
        *alias_gate["blocking_reasons"],
        *department_gate["blocking_reasons"],
        *region_gate["blocking_reasons"],
        *health_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PFT03 requires passing S2PFT02 Hong Kong/Macau profile evidence")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == coverage_gate["status"]
        == alias_gate["status"]
        == department_gate["status"]
        == region_gate["status"]
        == health_gate["status"]
        == authority_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PFT03_KEY_CITY_COVERAGE_MODEL_ID,
        "acceptance_id": S2PFT03_ACCEPTANCE_ID,
        "task_id": S2PFT03_TASK_ID,
        "legacy_task_id": S2PFT03_LEGACY_TASK_ID,
        "phase": "S2PF",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_hk_mo_profile_gate": upstream_gate,
        "city_coverage_gate": coverage_gate["status"],
        "city_alias_gate": alias_gate["status"],
        "city_department_template_gate": department_gate["status"],
        "region_weight_gate": region_gate["status"],
        "health_tier_gate": health_gate["status"],
        "authority_gate": authority_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_city_ids": list(S2PFT03_REQUIRED_CITY_IDS),
        "required_city_count": len(S2PFT03_REQUIRED_CITY_IDS),
        "city_ids_observed": coverage_gate["city_ids_observed"],
        "city_record_count": len(city_rows),
        "required_city_department_roles": list(S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES),
        "allowed_region_groups": list(S2PFT03_ALLOWED_REGION_GROUPS),
        "region_groups_observed": region_gate["region_groups_observed"],
        "allowed_health_tiers": list(S2PFT03_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": health_gate["health_tiers_observed"],
        "city_records": city_rows,
        "city_coverage_summary": coverage_gate,
        "city_alias_summary": alias_gate,
        "city_department_template_summary": department_gate,
        "region_weight_summary": region_gate,
        "health_tier_summary": health_gate,
        "authority_summary": authority_gate,
        "metadata_summary": metadata_gate,
        "s2pf_key_city_coverage_ready": status == "pass",
        "d3_full_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "v7_2_mail_or_schema_prerun": False,
        "city_coverage_modeled": status == "pass",
        "special_zone_discovery_enabled": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pft03_key_city_coverage(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    hk_mo_profile_report: Mapping[str, Any],
    city_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PFT03 key-city coverage evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pft03-key-city-coverage"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pft03_key_city_coverage_report(
        generated_at=generated_at,
        hk_mo_profile_report=hk_mo_profile_report,
        city_records=city_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "key_city_coverage_report_path": str(run_dir / "adp-s2pft03-key-city-coverage-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pft03-key-city-coverage-report.json", report)
        _write_json(state / S2PFT03_REPORT_FILENAME, report)
    return report


def validate_s2pft03_key_city_coverage_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PFT03_KEY_CITY_COVERAGE_MODEL_ID:
        errors.append("S2PFT03 city model_id must be adp-s2pft03-key-city-coverage-v1")
    if report.get("task_id") != S2PFT03_TASK_ID:
        errors.append("S2PFT03 city task_id must be S2PFT03")
    if report.get("legacy_task_id") != S2PFT03_LEGACY_TASK_ID:
        errors.append("S2PFT03 city legacy_task_id must be S2P5T03")
    if report.get("acceptance_id") != S2PFT03_ACCEPTANCE_ID:
        errors.append("S2PFT03 city acceptance_id must be ACC-S2PFT03-CITIES")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PFT03 city status must be pass or blocked")
    for key in (
        "d3_full_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
        "v7_2_mail_or_schema_prerun",
        "special_zone_discovery_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PFT03 key-city coverage")
    city_records = report.get("city_records")
    if not isinstance(city_records, list):
        errors.append("S2PFT03 city_records must be a list")
        city_records = []
    observed_ids = set(report.get("city_ids_observed") or [])
    missing_ids = [city_id for city_id in S2PFT03_REQUIRED_CITY_IDS if city_id not in observed_ids]
    if missing_ids:
        errors.append("S2PFT03 missing city ids: " + ", ".join(missing_ids))
    for index, record in enumerate(city_records):
        if not isinstance(record, Mapping):
            errors.append(f"city_records[{index}] must be an object")
            continue
        if record.get("city_id") not in S2PFT03_REQUIRED_CITY_IDS:
            errors.append(f"city_records[{index}].city_id is not supported")
        if not record.get("city_name"):
            errors.append(f"city_records[{index}].city_name is required")
        if record.get("region_group") not in S2PFT03_ALLOWED_REGION_GROUPS:
            errors.append(f"city_records[{index}].region_group is not supported")
        if record.get("health_tier") not in S2PFT03_ALLOWED_HEALTH_TIERS:
            errors.append(f"city_records[{index}].health_tier is not supported")
        if not record.get("health_explanation"):
            errors.append(f"city_records[{index}].health_explanation is required")
        if not record.get("aliases"):
            errors.append(f"city_records[{index}].aliases is required")
        missing_roles = [
            role for role in S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES if role not in set(record.get("department_roles") or [])
        ]
        if missing_roles:
            errors.append(f"city_records[{index}] missing city roles: " + ", ".join(missing_roles))
        if record.get("authority_gate") != "pass":
            errors.append(f"city_records[{index}].authority_gate must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"city_records[{index}].metadata_only must be true")
        for field in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if record.get(field) is not False:
                errors.append(f"city_records[{index}].{field} must be false")
        if not record.get("official_domain") or not record.get("source_url") or not record.get("evidence_refs"):
            errors.append(f"city_records[{index}] requires official_domain, source_url, and evidence_refs")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PFT03 city report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_hk_mo_profile_gate",
            "city_coverage_gate",
            "city_alias_gate",
            "city_department_template_gate",
            "region_weight_gate",
            "health_tier_gate",
            "authority_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PFT03 city report requires {key}=pass")
        if report.get("s2pf_key_city_coverage_ready") is not True:
            errors.append("passing S2PFT03 city report requires s2pf_key_city_coverage_ready=true")
        if report.get("city_coverage_modeled") is not True:
            errors.append("passing S2PFT03 city report requires city_coverage_modeled=true")
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


def fetch_s2pct02_science_batches(*, generated_at: str, max_records: int = 3) -> dict[str, dict[str, Any]]:
    return {
        journal: ingest_latest_top_journal(
            journal=journal,
            generated_at=generated_at,
            max_records=max_records,
        )
        for journal in S2PCT02_REQUIRED_JOURNALS
    }


def fetch_s2pct03_lancet_batches(*, generated_at: str, max_records: int = 3) -> dict[str, dict[str, Any]]:
    return {
        journal: ingest_latest_top_journal(
            journal=journal,
            generated_at=generated_at,
            max_records=max_records,
        )
        for journal in S2PCT03_REQUIRED_JOURNALS
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


def _top_journal_scan(
    source_batches: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
    required_journals: Sequence[str] = S2P2_REQUIRED_JOURNALS,
    model_id: str = S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
    scan_id: str = "s2p2-top-journal-scan:shadow",
    no_candidate_message: str = "no eligible new Nature main-journal candidates for shadow daily input",
) -> dict[str, Any]:
    source_reports: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_candidate_ids: set[str] = set()
    for journal in required_journals:
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
    blocking_reasons = errors if errors else [] if candidates else [no_candidate_message]
    return {
        "scan_id": scan_id,
        "model_id": model_id,
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


def _write_or_return_s2pct02(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized.setdefault("d2_source_domain_accepted", False)
    normalized.setdefault("stage2_production_accepted", False)
    normalized.setdefault("integrated_production_accepted", False)
    normalized["validation_errors"] = validate_s2pct02_science_shadow_report(normalized)
    if write:
        _write_json(run_dir / "adp-s2pct02-science-shadow-report.json", normalized)
    return normalized


def _write_or_return_s2pct03(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized.setdefault("d2_source_domain_accepted", False)
    normalized.setdefault("stage2_production_accepted", False)
    normalized.setdefault("integrated_production_accepted", False)
    normalized["validation_errors"] = validate_s2pct03_lancet_shadow_report(normalized)
    if write:
        _write_json(run_dir / "adp-s2pct03-lancet-shadow-report.json", normalized)
    return normalized


def _write_or_return_s2pct04(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
    ):
        normalized.setdefault(key, False)
    normalized["validation_errors"] = validate_s2pct04_top_journal_profile_report(normalized)
    if write:
        report_path = Path(str(normalized.get("profile_report_path") or run_dir / "adp-s2pct04-top-journal-profile-report.json"))
        _write_json(report_path, normalized)
    return normalized


def _write_or_return_s2pct05(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        normalized.setdefault(key, False)
    normalized["validation_errors"] = validate_s2pct05_engineering_signal_report(normalized)
    if write:
        report_path = Path(str(normalized.get("engineering_signal_report_path") or run_dir / "adp-s2pct05-engineering-signal-report.json"))
        _write_json(report_path, normalized)
    return normalized


def _write_or_return_s2pct06(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "marketing_material_accepted",
    ):
        normalized.setdefault(key, False)
    normalized["validation_errors"] = validate_s2pct06_authoritative_report_source_report(normalized)
    if write:
        report_path = Path(str(normalized.get("authoritative_report_path") or run_dir / "adp-s2pct06-authoritative-report-source-report.json"))
        _write_json(report_path, normalized)
    return normalized


def _s2pct05_known_documents(profile_report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    documents: dict[str, Mapping[str, Any]] = {}
    for profile in profile_report.get("source_profiles") or []:
        if not isinstance(profile, Mapping):
            continue
        canonical_id = str(profile.get("canonical_document_id") or "")
        if canonical_id:
            documents[canonical_id] = profile
    return documents


def _s2pct05_normalize_engineering_signals(
    engineering_signals: Sequence[Mapping[str, Any]],
    *,
    known_documents: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    normalized: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, signal in enumerate(engineering_signals):
        if not isinstance(signal, Mapping):
            reason = f"engineering_signals[{index}] must be an object"
            reports.append({"index": index, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        item = _s2pct05_normalize_signal(signal, generated_at=generated_at)
        item_errors = _s2pct05_signal_errors(item, known_documents=known_documents)
        reports.append(
            {
                "signal_id": item.get("signal_id", ""),
                "signal_type": item.get("signal_type", ""),
                "status": "blocked" if item_errors else "pass",
                "blocking_reasons": item_errors,
            }
        )
        errors.extend(item_errors)
        if not item_errors:
            normalized.append(item)
    return normalized, reports, errors


def _s2pct05_normalize_signal(signal: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    signal_type = _s2pct05_signal_type(str(signal.get("signal_type") or signal.get("type") or ""))
    canonical_id = str(signal.get("canonical_document_id") or signal.get("paper_canonical_document_id") or "")
    url = _s2pct05_signal_url(signal)
    version_reference = _s2pct05_version_reference(signal)
    signal_id = str(signal.get("signal_id") or "")
    if not signal_id and signal_type and canonical_id:
        signal_id = f"eng-signal:{signal_type}:{_safe_id(canonical_id)}:{_safe_id(version_reference or url or 'unversioned')}"
    return {
        "signal_id": signal_id,
        "signal_type": signal_type,
        "title": str(signal.get("title") or signal.get("name") or ""),
        "canonical_document_id": canonical_id,
        "paper_relation_type": _profile_token(str(signal.get("paper_relation_type") or signal.get("relation_type") or "")),
        "provider": str(signal.get("provider") or signal.get("publisher") or signal.get("organization") or ""),
        "source_url": url,
        "repository_url": str(signal.get("repository_url") or ""),
        "version_reference": version_reference,
        "release_tag": str(signal.get("release_tag") or ""),
        "commit_sha": str(signal.get("commit_sha") or ""),
        "benchmark_name": str(signal.get("benchmark_name") or ""),
        "metric_name": str(signal.get("metric_name") or ""),
        "standard_id": str(signal.get("standard_id") or ""),
        "officiality_state": _profile_token(str(signal.get("officiality_state") or signal.get("officiality_verdict") or "")),
        "officiality_evidence_type": _profile_token(str(signal.get("officiality_evidence_type") or "")),
        "reproducibility_state": _profile_token(str(signal.get("reproducibility_state") or "")),
        "reproducibility_evidence": str(signal.get("reproducibility_evidence") or ""),
        "metadata_only": True,
        "production_eligible": False,
        "generated_at": generated_at,
        "evidence_refs": list(signal.get("evidence_refs") or []),
    }


def _s2pct05_signal_errors(signal: Mapping[str, Any], *, known_documents: Mapping[str, Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    signal_id = str(signal.get("signal_id") or "engineering-signal")
    signal_type = str(signal.get("signal_type") or "")
    canonical_id = str(signal.get("canonical_document_id") or "")
    if not signal.get("signal_id"):
        errors.append(f"{signal_id}: signal_id is required")
    if signal_type not in S2PCT05_REQUIRED_SIGNAL_TYPES:
        errors.append(f"{signal_id}: signal_type is not supported")
    if not canonical_id:
        errors.append(f"{signal_id}: canonical_document_id is required")
    elif canonical_id not in known_documents:
        errors.append(f"{signal_id}: canonical_document_id is unknown: {canonical_id}")
    if signal.get("paper_relation_type") not in S2PCT05_ALLOWED_RELATION_TYPES:
        errors.append(f"{signal_id}: paper_relation_type is not supported")
    if signal.get("officiality_state") not in S2PCT05_ALLOWED_OFFICIALITY_STATES:
        errors.append(f"{signal_id}: officiality_state is not accepted")
    if not signal.get("source_url"):
        errors.append(f"{signal_id}: source_url is required")
    if not signal.get("version_reference"):
        errors.append(f"{signal_id}: version_reference is required")
    if signal.get("reproducibility_state") not in S2PCT05_ALLOWED_REPRODUCIBILITY_STATES:
        errors.append(f"{signal_id}: reproducibility_state is invalid")
    if not signal.get("evidence_refs"):
        errors.append(f"{signal_id}: evidence_refs are required")
    errors.extend(_s2pct05_type_specific_errors(signal))
    return errors


def _s2pct05_type_specific_errors(signal: Mapping[str, Any]) -> list[str]:
    signal_id = str(signal.get("signal_id") or "engineering-signal")
    signal_type = str(signal.get("signal_type") or "")
    errors: list[str] = []
    if signal_type == "official_code_repository" and not signal.get("repository_url"):
        errors.append(f"{signal_id}: official_code_repository requires repository_url")
    if signal_type == "official_release" and not signal.get("release_tag"):
        errors.append(f"{signal_id}: official_release requires release_tag")
    if signal_type == "model_card" and "model" not in str(signal.get("source_url") or "").lower():
        errors.append(f"{signal_id}: model_card source_url must identify a model-card or model page")
    if signal_type == "benchmark_result" and not signal.get("benchmark_name"):
        errors.append(f"{signal_id}: benchmark_result requires benchmark_name")
    if signal_type == "standard_or_spec" and not signal.get("standard_id"):
        errors.append(f"{signal_id}: standard_or_spec requires standard_id")
    return errors


def _s2pct05_signal_type(raw: str) -> str:
    token = _profile_token(raw)
    aliases = {
        "code": "official_code_repository",
        "code_repository": "official_code_repository",
        "repository": "official_code_repository",
        "repo": "official_code_repository",
        "official_repo": "official_code_repository",
        "release": "official_release",
        "official_release": "official_release",
        "modelcard": "model_card",
        "model_card": "model_card",
        "benchmark": "benchmark_result",
        "benchmark_result": "benchmark_result",
        "standard": "standard_or_spec",
        "standards": "standard_or_spec",
        "spec": "standard_or_spec",
        "specification": "standard_or_spec",
        "standard_or_spec": "standard_or_spec",
    }
    return aliases.get(token, token)


def _s2pct05_signal_url(signal: Mapping[str, Any]) -> str:
    for key in ("source_url", "url", "repository_url", "release_url", "model_card_url", "benchmark_url", "standard_url"):
        value = str(signal.get(key) or "")
        if value:
            return value
    return ""


def _s2pct05_version_reference(signal: Mapping[str, Any]) -> str:
    for key in ("version_reference", "release_tag", "version", "model_card_version", "standard_version", "commit_sha"):
        value = str(signal.get(key) or "")
        if value:
            return value
    return ""


def _s2pct05_officiality_errors(signals: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for signal in signals:
        if signal.get("officiality_state") not in S2PCT05_ALLOWED_OFFICIALITY_STATES:
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: officiality_state is not accepted")
        if not signal.get("officiality_evidence_type"):
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: officiality_evidence_type is required")
    return errors


def _s2pct05_version_errors(signals: Sequence[Mapping[str, Any]]) -> list[str]:
    return [
        f"{signal.get('signal_id', 'engineering-signal')}: version_reference is required"
        for signal in signals
        if not signal.get("version_reference")
    ]


def _s2pct05_relation_errors(
    signals: Sequence[Mapping[str, Any]],
    known_documents: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    for signal in signals:
        canonical_id = str(signal.get("canonical_document_id") or "")
        if canonical_id not in known_documents:
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: canonical_document_id is unknown: {canonical_id}")
        if signal.get("paper_relation_type") not in S2PCT05_ALLOWED_RELATION_TYPES:
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: paper_relation_type is not supported")
    return errors


def _s2pct05_reproducibility_errors(signals: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for signal in signals:
        if signal.get("reproducibility_state") not in S2PCT05_ALLOWED_REPRODUCIBILITY_STATES:
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: reproducibility_state is invalid")
        if signal.get("signal_type") == "benchmark_result" and not signal.get("metric_name"):
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: benchmark_result requires metric_name")
    return errors


def _s2pct06_known_signals(engineering_signal_report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    signals: dict[str, Mapping[str, Any]] = {}
    for signal in engineering_signal_report.get("engineering_signals") or []:
        if not isinstance(signal, Mapping):
            continue
        signal_id = str(signal.get("signal_id") or "")
        if signal_id:
            signals[signal_id] = signal
    return signals


def _s2pct06_normalize_reports(
    technical_reports: Sequence[Mapping[str, Any]],
    *,
    known_signals: Mapping[str, Mapping[str, Any]],
    known_documents: set[str],
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    normalized: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, report in enumerate(technical_reports):
        if not isinstance(report, Mapping):
            reason = f"technical_reports[{index}] must be an object"
            source_reports.append({"index": index, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        item = _s2pct06_normalize_report(report, generated_at=generated_at)
        item_errors = _s2pct06_report_errors(item, known_signals=known_signals, known_documents=known_documents)
        source_reports.append(
            {
                "report_id": item.get("report_id", ""),
                "report_type": item.get("report_type", ""),
                "publisher": item.get("publisher", ""),
                "status": "blocked" if item_errors else "pass",
                "blocking_reasons": item_errors,
            }
        )
        errors.extend(item_errors)
        if not item_errors:
            normalized.append(item)
    return normalized, source_reports, errors


def _s2pct06_normalize_report(report: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    report_type = _s2pct06_report_type(str(report.get("report_type") or report.get("type") or ""))
    publisher_type = _s2pct06_publisher_type(str(report.get("publisher_type") or report.get("organization_type") or ""))
    canonical_id = str(report.get("canonical_document_id") or report.get("paper_canonical_document_id") or "")
    related_signal_ids = [str(value) for value in report.get("related_signal_ids") or report.get("signal_ids") or [] if str(value)]
    source_url = _s2pct06_report_url(report)
    version_reference = _s2pct06_report_version_reference(report)
    report_id = str(report.get("report_id") or "")
    if not report_id and report_type and source_url:
        report_id = f"auth-report:{report_type}:{_safe_id(source_url)}"
    return {
        "report_id": report_id,
        "report_type": report_type,
        "title": str(report.get("title") or report.get("name") or ""),
        "publisher": str(report.get("publisher") or report.get("organization") or ""),
        "publisher_type": publisher_type,
        "publisher_identity_state": _profile_token(str(report.get("publisher_identity_state") or report.get("identity_state") or "")),
        "publisher_identity_evidence": str(report.get("publisher_identity_evidence") or report.get("identity_evidence") or ""),
        "source_url": source_url,
        "landing_page_url": str(report.get("landing_page_url") or ""),
        "publication_date": str(report.get("publication_date") or report.get("date") or ""),
        "version_reference": version_reference,
        "canonical_document_id": canonical_id,
        "related_signal_ids": related_signal_ids,
        "interest_relation": _profile_token(str(report.get("interest_relation") or report.get("conflict_of_interest_state") or "")),
        "interest_disclosure": str(report.get("interest_disclosure") or report.get("conflict_of_interest_statement") or ""),
        "evidence_level": _s2pct06_evidence_level(str(report.get("evidence_level") or report.get("evidence_type") or "")),
        "product_name": str(report.get("product_name") or ""),
        "methodology_summary": str(report.get("methodology_summary") or ""),
        "metadata_only": True,
        "marketing_material_accepted": False,
        "production_eligible": False,
        "generated_at": generated_at,
        "evidence_refs": list(report.get("evidence_refs") or []),
    }


def _s2pct06_report_errors(
    report: Mapping[str, Any],
    *,
    known_signals: Mapping[str, Mapping[str, Any]],
    known_documents: set[str],
) -> list[str]:
    errors: list[str] = []
    report_id = str(report.get("report_id") or "authoritative-report")
    report_type = str(report.get("report_type") or "")
    canonical_id = str(report.get("canonical_document_id") or "")
    related_signal_ids = [str(value) for value in report.get("related_signal_ids") or []]
    if not report.get("report_id"):
        errors.append(f"{report_id}: report_id is required")
    if report_type not in S2PCT06_REQUIRED_REPORT_TYPES:
        errors.append(f"{report_id}: report_type is not supported")
    if not report.get("publisher"):
        errors.append(f"{report_id}: publisher is required")
    if report.get("publisher_type") not in S2PCT06_ALLOWED_PUBLISHER_TYPES:
        errors.append(f"{report_id}: publisher_type is not supported")
    if report.get("publisher_identity_state") not in S2PCT06_ALLOWED_IDENTITY_STATES:
        errors.append(f"{report_id}: publisher_identity_state is not accepted")
    if not report.get("publisher_identity_evidence"):
        errors.append(f"{report_id}: publisher_identity_evidence is required")
    if report.get("interest_relation") not in S2PCT06_ALLOWED_INTEREST_RELATIONS:
        errors.append(f"{report_id}: interest_relation is not accepted")
    if not report.get("interest_disclosure"):
        errors.append(f"{report_id}: interest_disclosure is required")
    if report.get("evidence_level") not in S2PCT06_ALLOWED_EVIDENCE_LEVELS:
        errors.append(f"{report_id}: evidence_level is not accepted")
    if not report.get("source_url"):
        errors.append(f"{report_id}: source_url is required")
    if not report.get("version_reference"):
        errors.append(f"{report_id}: version_reference is required")
    if not canonical_id:
        errors.append(f"{report_id}: canonical_document_id is required")
    elif canonical_id not in known_documents:
        errors.append(f"{report_id}: canonical_document_id is unknown: {canonical_id}")
    if not related_signal_ids:
        errors.append(f"{report_id}: related_signal_ids are required")
    unknown_signal_ids = [signal_id for signal_id in related_signal_ids if signal_id not in known_signals]
    if unknown_signal_ids:
        errors.append(f"{report_id}: related_signal_ids unknown: {', '.join(unknown_signal_ids)}")
    if related_signal_ids and canonical_id:
        mismatched = [
            signal_id
            for signal_id in related_signal_ids
            if str(known_signals.get(signal_id, {}).get("canonical_document_id") or "") != canonical_id
        ]
        if mismatched:
            errors.append(f"{report_id}: related_signal_ids do not trace to canonical_document_id: {', '.join(mismatched)}")
    if not report.get("evidence_refs"):
        errors.append(f"{report_id}: evidence_refs are required")
    errors.extend(_s2pct06_type_specific_errors(report))
    return errors


def _s2pct06_type_specific_errors(report: Mapping[str, Any]) -> list[str]:
    report_id = str(report.get("report_id") or "authoritative-report")
    report_type = str(report.get("report_type") or "")
    errors: list[str] = []
    if report_type == "product_technical_note" and not report.get("product_name"):
        errors.append(f"{report_id}: product_technical_note requires product_name")
    if report_type in {"research_institution_report", "lab_technical_report"} and report.get("publisher_type") == "company_product_org":
        errors.append(f"{report_id}: research/lab reports cannot use company_product_org publisher_type")
    if report_type == "industry_technical_report" and report.get("interest_relation") == "independent_research":
        errors.append(f"{report_id}: industry_technical_report requires disclosed industry interest relation")
    if report_type in {"research_institution_report", "lab_technical_report", "industry_technical_report"} and not report.get("methodology_summary"):
        errors.append(f"{report_id}: methodology_summary is required")
    return errors


def _s2pct06_report_type(raw: str) -> str:
    token = _profile_token(raw)
    aliases = {
        "research_report": "research_institution_report",
        "research_institution_report": "research_institution_report",
        "institution_report": "research_institution_report",
        "lab_report": "lab_technical_report",
        "laboratory_report": "lab_technical_report",
        "lab_technical_report": "lab_technical_report",
        "industry_report": "industry_technical_report",
        "industry_technical_report": "industry_technical_report",
        "technical_report": "industry_technical_report",
        "product_note": "product_technical_note",
        "product_technical_note": "product_technical_note",
        "technical_note": "product_technical_note",
    }
    return aliases.get(token, token)


def _s2pct06_publisher_type(raw: str) -> str:
    token = _profile_token(raw)
    aliases = {
        "institute": "research_institution",
        "research_institute": "research_institution",
        "research_institution": "research_institution",
        "public_lab": "public_lab",
        "government_lab": "public_lab",
        "national_lab": "public_lab",
        "industry_lab": "industry_research_lab",
        "industry_research_lab": "industry_research_lab",
        "corporate_research": "industry_research_lab",
        "company": "company_product_org",
        "company_product_org": "company_product_org",
        "vendor": "company_product_org",
    }
    return aliases.get(token, token)


def _s2pct06_evidence_level(raw: str) -> str:
    token = _profile_token(raw)
    aliases = {
        "primary_report": "primary_research_report",
        "primary_research_report": "primary_research_report",
        "research_report": "primary_research_report",
        "whitepaper": "technical_whitepaper",
        "technical_whitepaper": "technical_whitepaper",
        "methodology": "methodology_note",
        "methodology_note": "methodology_note",
        "product_note": "product_technical_note",
        "product_technical_note": "product_technical_note",
    }
    return aliases.get(token, token)


def _s2pct06_report_url(report: Mapping[str, Any]) -> str:
    for key in ("source_url", "url", "landing_page_url", "report_url", "technical_note_url"):
        value = str(report.get(key) or "")
        if value:
            return value
    return ""


def _s2pct06_report_version_reference(report: Mapping[str, Any]) -> str:
    for key in ("version_reference", "version", "publication_date", "date", "report_number", "revision"):
        value = str(report.get(key) or "")
        if value:
            return value
    return ""


def _s2pct06_publisher_identity_errors(reports: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for report in reports:
        report_id = str(report.get("report_id") or "authoritative-report")
        if report.get("publisher_type") not in S2PCT06_ALLOWED_PUBLISHER_TYPES:
            errors.append(f"{report_id}: publisher_type is not supported")
        if report.get("publisher_identity_state") not in S2PCT06_ALLOWED_IDENTITY_STATES:
            errors.append(f"{report_id}: publisher_identity_state is not accepted")
        if not report.get("publisher_identity_evidence"):
            errors.append(f"{report_id}: publisher_identity_evidence is required")
    return errors


def _s2pct06_interest_relation_errors(reports: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for report in reports:
        report_id = str(report.get("report_id") or "authoritative-report")
        if report.get("interest_relation") not in S2PCT06_ALLOWED_INTEREST_RELATIONS:
            errors.append(f"{report_id}: interest_relation is not accepted")
        if not report.get("interest_disclosure"):
            errors.append(f"{report_id}: interest_disclosure is required")
    return errors


def _s2pct06_evidence_level_errors(reports: Sequence[Mapping[str, Any]]) -> list[str]:
    return [
        f"{report.get('report_id', 'authoritative-report')}: evidence_level is not accepted"
        for report in reports
        if report.get("evidence_level") not in S2PCT06_ALLOWED_EVIDENCE_LEVELS
    ]


def _s2pct06_traceability_errors(
    reports: Sequence[Mapping[str, Any]],
    known_signals: Mapping[str, Mapping[str, Any]],
    known_documents: set[str],
) -> list[str]:
    errors: list[str] = []
    for report in reports:
        report_id = str(report.get("report_id") or "authoritative-report")
        canonical_id = str(report.get("canonical_document_id") or "")
        if canonical_id not in known_documents:
            errors.append(f"{report_id}: canonical_document_id is unknown: {canonical_id}")
        related_signal_ids = [str(value) for value in report.get("related_signal_ids") or []]
        if not related_signal_ids:
            errors.append(f"{report_id}: related_signal_ids are required")
            continue
        unknown_signal_ids = [signal_id for signal_id in related_signal_ids if signal_id not in known_signals]
        if unknown_signal_ids:
            errors.append(f"{report_id}: related_signal_ids unknown: {', '.join(unknown_signal_ids)}")
    return errors


def _s2pct07_domain_matrix(
    *,
    profile_report: Mapping[str, Any],
    engineering_signal_report: Mapping[str, Any],
    authoritative_report: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    matrix = {
        "top_journal": {
            "coverage_gate": "pass" if profile_report.get("status") == "pass" else "blocked",
            "evidence_count": len(profile_report.get("source_profiles") or []),
            "type_count": len(set(profile_report.get("profile_kinds_observed") or [])),
            "required_types": list(S2PCT04_REQUIRED_PROFILE_KINDS),
            "observed_types": sorted(set(str(value) for value in profile_report.get("profile_kinds_observed") or [])),
        },
        "engineering_signal": {
            "coverage_gate": "pass" if engineering_signal_report.get("status") == "pass" else "blocked",
            "evidence_count": len(engineering_signal_report.get("engineering_signals") or []),
            "type_count": len(set(engineering_signal_report.get("signal_types_observed") or [])),
            "required_types": list(S2PCT05_REQUIRED_SIGNAL_TYPES),
            "observed_types": sorted(set(str(value) for value in engineering_signal_report.get("signal_types_observed") or [])),
        },
        "authoritative_report": {
            "coverage_gate": "pass" if authoritative_report.get("status") == "pass" else "blocked",
            "evidence_count": len(authoritative_report.get("authoritative_reports") or []),
            "type_count": len(set(authoritative_report.get("report_types_observed") or [])),
            "required_types": list(S2PCT06_REQUIRED_REPORT_TYPES),
            "observed_types": sorted(set(str(value) for value in authoritative_report.get("report_types_observed") or [])),
        },
    }
    errors: list[str] = []
    for domain in S2PCT07_REQUIRED_DOMAINS:
        row = matrix[domain]
        missing = sorted(set(row["required_types"]) - set(row["observed_types"]))
        row["missing_types"] = missing
        if row["coverage_gate"] != "pass":
            errors.append(f"{domain}: upstream coverage gate is blocked")
        if int(row["evidence_count"] or 0) < 1:
            errors.append(f"{domain}: evidence_count must be positive")
        if missing:
            errors.append(f"{domain}: missing required types: {', '.join(missing)}")
    return matrix, errors


def _s2pct07_replay_gate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = {str(record.get("as_of_date") or record.get("date") or "")[:10] for record in records if isinstance(record, Mapping)}
    passing = [record for record in records if isinstance(record, Mapping) and record.get("status") == "pass"]
    future_leakage = [record for record in records if isinstance(record, Mapping) and int(record.get("future_leakage_count") or 0) > 0]
    p0_p1 = [record for record in records if isinstance(record, Mapping) and int(record.get("p0_p1_blocker_count") or 0) > 0]
    domains = {str(record.get("domain") or "") for record in records if isinstance(record, Mapping)}
    reasons: list[str] = []
    if len(dates) < S2PCT07_REQUIRED_REPLAY_DATES:
        reasons.append("S2PCT07 D2 replay requires 30 unique dates")
    if len(passing) < len(records) or not records:
        reasons.append("S2PCT07 D2 replay records must all pass")
    missing_domains = sorted(set(S2PCT07_REQUIRED_DOMAINS) - domains)
    if missing_domains:
        reasons.append("S2PCT07 D2 replay missing domains: " + ", ".join(missing_domains))
    if future_leakage:
        reasons.append("S2PCT07 D2 replay has future leakage")
    if p0_p1:
        reasons.append("S2PCT07 D2 replay has P0/P1 blockers")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_unique_dates": S2PCT07_REQUIRED_REPLAY_DATES,
        "unique_date_count": len(dates),
        "record_count": len(records),
        "passing_record_count": len(passing),
        "domains_observed": sorted(domain for domain in domains if domain),
        "future_leakage_count": len(future_leakage),
        "p0_p1_blocker_count": len(p0_p1),
        "blocking_reasons": reasons,
    }


def _s2pct07_shadow_gate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    hours = max([float(record.get("shadow_hours") or 0.0) for record in records if isinstance(record, Mapping)] or [0.0])
    passing = [record for record in records if isinstance(record, Mapping) and record.get("status") == "pass"]
    production_affected = [record for record in records if isinstance(record, Mapping) and record.get("production_affected") is not False]
    smtp_sent = [record for record in records if isinstance(record, Mapping) and record.get("real_smtp_sent") is not False]
    reasons: list[str] = []
    if hours < S2PCT07_REQUIRED_SHADOW_HOURS:
        reasons.append("S2PCT07 D2 shadow requires at least 48 hours")
    if len(passing) < len(records) or not records:
        reasons.append("S2PCT07 D2 shadow records must all pass")
    if production_affected:
        reasons.append("S2PCT07 D2 shadow must not affect production")
    if smtp_sent:
        reasons.append("S2PCT07 D2 shadow must not send SMTP")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_shadow_hours": S2PCT07_REQUIRED_SHADOW_HOURS,
        "shadow_hours": hours,
        "record_count": len(records),
        "passing_record_count": len(passing),
        "production_affected_count": len(production_affected),
        "real_smtp_sent_count": len(smtp_sent),
        "blocking_reasons": reasons,
    }


def _s2pct07_forced_event_gate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    event_types = {str(record.get("event_type") or "") for record in records if isinstance(record, Mapping)}
    passing = [record for record in records if isinstance(record, Mapping) and record.get("status") == "pass"]
    no_updates = [
        record
        for record in records
        if isinstance(record, Mapping)
        and not (record.get("forced_review_required") is True and str(record.get("updated_conclusion_state") or ""))
    ]
    reasons: list[str] = []
    missing = sorted(set(S2PCT07_REQUIRED_FORCED_EVENT_TYPES) - event_types)
    if missing:
        reasons.append("S2PCT07 forced-event calibration missing event types: " + ", ".join(missing))
    if len(passing) < len(records) or not records:
        reasons.append("S2PCT07 forced-event records must all pass")
    if no_updates:
        reasons.append("S2PCT07 forced-event records must force review and update conclusion state")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_event_types": list(S2PCT07_REQUIRED_FORCED_EVENT_TYPES),
        "event_types_observed": sorted(event_type for event_type in event_types if event_type),
        "record_count": len(records),
        "passing_record_count": len(passing),
        "forced_update_count": len(records) - len(no_updates),
        "blocking_reasons": reasons,
    }


def _s2pct07_queue_explanation_gate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    states = {str(record.get("queue_state") or record.get("decision") or "") for record in records if isinstance(record, Mapping)}
    missing_explanation = [
        record
        for record in records
        if isinstance(record, Mapping)
        and (not str(record.get("explanation") or "") or not str(record.get("candidate_id") or record.get("source_id") or ""))
    ]
    reasons: list[str] = []
    missing_states = sorted(set(S2PCT07_REQUIRED_QUEUE_EXPLANATION_STATES) - states)
    if missing_states:
        reasons.append("S2PCT07 queue explanation missing states: " + ", ".join(missing_states))
    if missing_explanation:
        reasons.append("S2PCT07 queue explanation records require candidate_id/source_id and explanation")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_queue_states": list(S2PCT07_REQUIRED_QUEUE_EXPLANATION_STATES),
        "queue_states_observed": sorted(state for state in states if state),
        "record_count": len(records),
        "explained_record_count": len(records) - len(missing_explanation),
        "blocking_reasons": reasons,
    }


def _s2pct07_type_calibration(matrix: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    reasons: list[str] = []
    for domain in S2PCT07_REQUIRED_DOMAINS:
        row = matrix.get(domain) if isinstance(matrix.get(domain), Mapping) else {}
        required = set(row.get("required_types") or [])
        observed = set(row.get("observed_types") or [])
        coverage = (len(observed & required) / len(required)) if required else 0.0
        rows.append(
            {
                "domain": domain,
                "required_type_count": len(required),
                "observed_required_type_count": len(observed & required),
                "coverage_ratio": round(coverage, 4),
            }
        )
        if coverage < 1.0:
            reasons.append(f"{domain}: type coverage ratio must be 1.0")
    ratios = [float(row["coverage_ratio"]) for row in rows]
    spread = max(ratios) - min(ratios) if ratios else 1.0
    if spread > 0.0:
        reasons.append("S2PCT07 cross-type calibration spread must be 0 after required coverage")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_coverage_ratio": 1.0,
        "coverage_rows": rows,
        "coverage_spread": round(spread, 4),
        "blocking_reasons": reasons,
    }


def _s2pdt01_authority_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    source_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"authority_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "").strip()
        authority_type = str(record.get("authority_type") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        row = {
            "source_id": source_id,
            "authority_type": authority_type,
            "authority_name": str(record.get("authority_name") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "document_number": str(record.get("document_number") or "").strip(),
            "published_date": str(record.get("published_date") or "").strip(),
            "attachment_trace": str(record.get("attachment_trace") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not source_id:
            errors.append(f"authority_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PDT01 source_id: {source_id}")
        source_ids.add(source_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"authority_records[{index}].source_url must contain official_domain")
        rows.append(row)
    if not rows:
        errors.append("S2PDT01 requires at least one C0 authority record")
    return rows, errors


def _s2pdt01_taxonomy_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("authority_type") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT01_REQUIRED_AUTHORITY_TYPES) - observed)
    unsupported = sorted(observed - set(S2PDT01_REQUIRED_AUTHORITY_TYPES))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT01 C0 taxonomy missing authority types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT01 C0 taxonomy has unsupported authority types: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_authority_types": list(S2PDT01_REQUIRED_AUTHORITY_TYPES),
        "authority_types_observed": sorted(authority_type for authority_type in observed if authority_type),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt01_identity_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PDT01_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PDT01 C0 identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PDT01_ALLOWED_IDENTITY_STATES),
        "verified_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt01_traceability_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_rows = []
    for row in rows:
        if not isinstance(row, Mapping):
            missing_rows.append(row)
            continue
        if any(not row.get(field) for field in S2PDT01_REQUIRED_TRACE_FIELDS) or not row.get("attachment_trace") or not row.get("evidence_refs"):
            missing_rows.append(row)
    reasons: list[str] = []
    if missing_rows:
        reasons.append("S2PDT01 C0 traceability requires authority_name, official_domain, document_number, published_date, attachment_trace, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_trace_fields": list(S2PDT01_REQUIRED_TRACE_FIELDS),
        "traceable_record_count": len(rows) - len(missing_rows),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt01_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PDT01 C0 records must be metadata-only with pdf_downloaded=false and full_text_extracted=false")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(rows) - len(violations),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_department_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    source_ids: set[str] = set()
    department_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"department_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "").strip()
        department_id = str(record.get("department_id") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        aliases = [str(alias).strip() for alias in record.get("aliases") or [] if str(alias).strip()]
        industry_routes = [str(route).strip() for route in record.get("industry_routes") or [] if str(route).strip()]
        board_routes = [str(route).strip() for route in record.get("board_routes") or [] if str(route).strip()]
        row = {
            "source_id": source_id,
            "department_id": department_id,
            "department_name": str(record.get("department_name") or "").strip(),
            "sector": str(record.get("sector") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "aliases": aliases,
            "industry_routes": industry_routes,
            "board_routes": board_routes,
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not source_id:
            errors.append(f"department_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PDT02 source_id: {source_id}")
        source_ids.add(source_id)
        if not department_id:
            errors.append(f"department_records[{index}].department_id is required")
        if department_id in department_ids:
            errors.append(f"duplicate S2PDT02 department_id: {department_id}")
        department_ids.add(department_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"department_records[{index}].source_url must contain official_domain")
        rows.append(row)
    if not rows:
        errors.append("S2PDT02 requires at least one C1 department record")
    return rows, errors


def _s2pdt02_sector_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("sector") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT02_REQUIRED_SECTORS) - observed)
    unsupported = sorted(observed - set(S2PDT02_REQUIRED_SECTORS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT02 C1 sector coverage missing sectors: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT02 C1 sector coverage has unsupported sectors: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_sectors": list(S2PDT02_REQUIRED_SECTORS),
        "sectors_observed": sorted(sector for sector in observed if sector),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_identity_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PDT02_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PDT02 C1 identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PDT02_ALLOWED_IDENTITY_STATES),
        "verified_department_count": len(rows) - len(invalid),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_alias_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing = [row for row in rows if not isinstance(row, Mapping) or not row.get("aliases")]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT02 C1 alias map requires at least one alias for every department")
    return {
        "status": "pass" if not reasons else "blocked",
        "aliased_department_count": len(rows) - len(missing),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_route_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing = [row for row in rows if not isinstance(row, Mapping) or not row.get("industry_routes") or not row.get("board_routes")]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT02 C1 route map requires industry_routes and board_routes for every department")
    return {
        "status": "pass" if not reasons else "blocked",
        "routed_department_count": len(rows) - len(missing),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PDT02 C1 records must be metadata-only with pdf_downloaded=false and full_text_extracted=false")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_department_count": len(rows) - len(violations),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt03_legal_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    legal_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"legal_records[{index}] must be an object")
            continue
        legal_id = str(record.get("legal_id") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        row = {
            "legal_id": legal_id,
            "source_id": str(record.get("source_id") or "").strip(),
            "title": str(record.get("title") or "").strip(),
            "legal_status": str(record.get("legal_status") or "").strip(),
            "version_label": str(record.get("version_label") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "published_date": str(record.get("published_date") or "").strip(),
            "effective_date": str(record.get("effective_date") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not legal_id:
            errors.append(f"legal_records[{index}].legal_id is required")
        if legal_id in legal_ids:
            errors.append(f"duplicate S2PDT03 legal_id: {legal_id}")
        legal_ids.add(legal_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"legal_records[{index}].source_url must contain official_domain")
        if not _is_iso_date(row["published_date"]):
            errors.append(f"legal_records[{index}].published_date must be YYYY-MM-DD")
        if not _is_iso_date(row["effective_date"]):
            errors.append(f"legal_records[{index}].effective_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PDT03 requires at least one legal metadata record")
    return rows, errors


def _s2pdt03_relation_rows(
    records: Sequence[Mapping[str, Any]],
    legal_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    relation_ids: set[str] = set()
    legal_ids = {str(row.get("legal_id") or "") for row in legal_rows if isinstance(row, Mapping)}
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_id = str(record.get("relation_id") or "").strip()
        source_legal_id = str(record.get("source_legal_id") or "").strip()
        target_legal_id = str(record.get("target_legal_id") or "").strip()
        row = {
            "relation_id": relation_id,
            "relation_type": str(record.get("relation_type") or "").strip(),
            "source_legal_id": source_legal_id,
            "target_legal_id": target_legal_id,
            "relation_date": str(record.get("relation_date") or "").strip(),
            "source_role": str(record.get("source_role") or "").strip(),
            "target_role": str(record.get("target_role") or "").strip(),
            "original_source_verified": record.get("original_source_verified") is True,
            "forced_update_required": record.get("forced_update_required") is True,
            "metadata_only": record.get("metadata_only") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not relation_id:
            errors.append(f"relation_records[{index}].relation_id is required")
        if relation_id in relation_ids:
            errors.append(f"duplicate S2PDT03 relation_id: {relation_id}")
        relation_ids.add(relation_id)
        if source_legal_id not in legal_ids:
            errors.append(f"relation_records[{index}].source_legal_id must reference legal_records")
        if target_legal_id not in legal_ids:
            errors.append(f"relation_records[{index}].target_legal_id must reference legal_records")
        if source_legal_id and target_legal_id and source_legal_id == target_legal_id:
            errors.append(f"relation_records[{index}] source_legal_id and target_legal_id must differ")
        if not _is_iso_date(row["relation_date"]):
            errors.append(f"relation_records[{index}].relation_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PDT03 requires at least one legal relation record")
    return rows, errors


def _s2pdt03_prior_conclusion_rows(
    records: Sequence[Mapping[str, Any]],
    legal_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    conclusion_ids: set[str] = set()
    legal_ids = {str(row.get("legal_id") or "") for row in legal_rows if isinstance(row, Mapping)}
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"prior_conclusion_records[{index}] must be an object")
            continue
        conclusion_id = str(record.get("conclusion_id") or "").strip()
        legal_id = str(record.get("legal_id") or "").strip()
        row = {
            "conclusion_id": conclusion_id,
            "legal_id": legal_id,
            "previous_state": str(record.get("previous_state") or "").strip(),
            "updated_state": str(record.get("updated_state") or "").strip(),
            "update_required": record.get("update_required") is True,
            "rescore_required": record.get("rescore_required") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not conclusion_id:
            errors.append(f"prior_conclusion_records[{index}].conclusion_id is required")
        if conclusion_id in conclusion_ids:
            errors.append(f"duplicate S2PDT03 conclusion_id: {conclusion_id}")
        conclusion_ids.add(conclusion_id)
        if legal_id not in legal_ids:
            errors.append(f"prior_conclusion_records[{index}].legal_id must reference legal_records")
        rows.append(row)
    if not rows:
        errors.append("S2PDT03 requires at least one prior conclusion update record")
    return rows, errors


def _s2pdt03_legal_status_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("legal_status") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT03_REQUIRED_LEGAL_STATUSES) - observed)
    unsupported = sorted(observed - set(S2PDT03_REQUIRED_LEGAL_STATUSES))
    invalid_identity = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PDT03_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT03 legal status coverage missing statuses: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT03 legal status coverage has unsupported statuses: " + ", ".join(unsupported))
    if invalid_identity:
        reasons.append("S2PDT03 legal identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_legal_statuses": list(S2PDT03_REQUIRED_LEGAL_STATUSES),
        "legal_statuses_observed": sorted(status for status in observed if status),
        "accepted_identity_count": len(rows) - len(invalid_identity),
        "legal_record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt03_version_effectivity_gate(
    legal_rows: Sequence[Mapping[str, Any]],
    relation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    relation_types = {str(row.get("relation_type") or "") for row in relation_rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT03_REQUIRED_RELATION_TYPES) - relation_types)
    unsupported = sorted(relation_types - set(S2PDT03_REQUIRED_RELATION_TYPES))
    date_confused = [
        row
        for row in legal_rows
        if not isinstance(row, Mapping)
        or not _is_iso_date(str(row.get("published_date") or ""))
        or not _is_iso_date(str(row.get("effective_date") or ""))
    ]
    relation_date_confused = [
        row
        for row in relation_rows
        if not isinstance(row, Mapping) or not _is_iso_date(str(row.get("relation_date") or ""))
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT03 version/effectivity relation coverage missing relation types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT03 version/effectivity relation coverage has unsupported relation types: " + ", ".join(unsupported))
    if date_confused or relation_date_confused:
        reasons.append("S2PDT03 date confusion guard requires YYYY-MM-DD published/effective/relation dates")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_relation_types": list(S2PDT03_REQUIRED_RELATION_TYPES),
        "relation_types_observed": sorted(relation_type for relation_type in relation_types if relation_type),
        "date_checked_legal_record_count": len(legal_rows) - len(date_confused),
        "date_checked_relation_record_count": len(relation_rows) - len(relation_date_confused),
        "blocking_reasons": reasons,
    }


def _s2pdt03_reprint_relation_gate(relation_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reprints = [row for row in relation_rows if isinstance(row, Mapping) and row.get("relation_type") == "reprint_of"]
    invalid = [
        row
        for row in reprints
        if row.get("source_role") != "reprint"
        or row.get("target_role") != "original"
        or row.get("original_source_verified") is not True
    ]
    reasons: list[str] = []
    if not reprints:
        reasons.append("S2PDT03 reprint relation guard requires at least one reprint_of relation")
    if invalid:
        reasons.append("S2PDT03 reprint relation guard requires source_role=reprint, target_role=original, and original_source_verified=true")
    return {
        "status": "pass" if not reasons else "blocked",
        "reprint_relation_count": len(reprints),
        "verified_reprint_relation_count": len(reprints) - len(invalid),
        "blocking_reasons": reasons,
    }


def _s2pdt03_forced_update_gate(
    relation_rows: Sequence[Mapping[str, Any]],
    prior_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    forced_relations = [
        row
        for row in relation_rows
        if isinstance(row, Mapping)
        and row.get("relation_type") in {"amends", "repeals", "implements", "interprets"}
        and row.get("forced_update_required") is True
    ]
    updatable_legal_ids = {
        str(row.get("source_legal_id") or "")
        for row in forced_relations
        if isinstance(row, Mapping) and str(row.get("source_legal_id") or "")
    }
    updatable_legal_ids.update(
        str(row.get("target_legal_id") or "")
        for row in forced_relations
        if isinstance(row, Mapping) and str(row.get("target_legal_id") or "")
    )
    valid_prior_updates = [
        row
        for row in prior_rows
        if isinstance(row, Mapping)
        and row.get("legal_id") in updatable_legal_ids
        and row.get("update_required") is True
        and row.get("rescore_required") is True
        and str(row.get("updated_state") or "")
    ]
    missing_fields = [
        row
        for row in prior_rows
        if not isinstance(row, Mapping)
        or row.get("update_required") is not True
        or row.get("rescore_required") is not True
        or not str(row.get("updated_state") or "")
    ]
    reasons: list[str] = []
    if len(forced_relations) < 4:
        reasons.append("S2PDT03 forced-update gate requires amend/repeal/implement/interpret relations with forced_update_required=true")
    if not valid_prior_updates:
        reasons.append("S2PDT03 status changes must trigger rescore and old conclusion update")
    if missing_fields:
        reasons.append("S2PDT03 prior conclusions require update_required, rescore_required, and updated_state")
    return {
        "status": "pass" if not reasons else "blocked",
        "forced_relation_count": len(forced_relations),
        "prior_update_count": len(valid_prior_updates),
        "affected_legal_ids": sorted(updatable_legal_ids),
        "blocking_reasons": reasons,
    }


def _s2pdt03_metadata_gate(
    legal_rows: Sequence[Mapping[str, Any]],
    relation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    legal_violations = [
        row
        for row in legal_rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
    ]
    relation_violations = [
        row for row in relation_rows if not isinstance(row, Mapping) or row.get("metadata_only") is not True
    ]
    evidence_missing = [
        row
        for row in [*legal_rows, *relation_rows]
        if not isinstance(row, Mapping) or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if legal_violations or relation_violations:
        reasons.append("S2PDT03 legal records and relations must stay metadata-only with no PDF/full-text extraction")
    if evidence_missing:
        reasons.append("S2PDT03 legal records and relations require evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_legal_record_count": len(legal_rows) - len(legal_violations),
        "metadata_only_relation_record_count": len(relation_rows) - len(relation_violations),
        "evidence_backed_record_count": len(legal_rows) + len(relation_rows) - len(evidence_missing),
        "blocking_reasons": reasons,
    }


def _s2pdt04_replay_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"replay_records[{index}] must be an object")
            continue
        row = {
            "as_of_date": str(record.get("as_of_date") or "").strip(),
            "source_domain": str(record.get("source_domain") or record.get("domain") or "d3_china_official").strip(),
            "status": str(record.get("status") or "").strip(),
            "future_leakage_count": int(record.get("future_leakage_count") or 0),
            "p0_p1_blocker_count": int(record.get("p0_p1_blocker_count") or 0),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "board_route_gate": str(record.get("board_route_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "formal_production_inclusion": record.get("formal_production_inclusion") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not _is_iso_date(row["as_of_date"]):
            errors.append(f"replay_records[{index}].as_of_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PDT04 requires at least one replay record")
    return rows, errors


def _s2pdt04_shadow_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"shadow_records[{index}] must be an object")
            continue
        row = {
            "shadow_date": str(record.get("shadow_date") or record.get("date") or "").strip(),
            "source_domain": str(record.get("source_domain") or record.get("domain") or "d3_china_official").strip(),
            "status": str(record.get("status") or "").strip(),
            "shadow_hours": int(record.get("shadow_hours") or 24),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "board_route_gate": str(record.get("board_route_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "formal_production_inclusion": record.get("formal_production_inclusion") is True,
            "d3_core_source_domain_accepted": record.get("d3_core_source_domain_accepted") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not _is_iso_date(row["shadow_date"]):
            errors.append(f"shadow_records[{index}].shadow_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PDT04 requires at least one shadow record")
    return rows, errors


def _s2pdt04_board_route_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    board_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"board_route_records[{index}] must be an object")
            continue
        board_id = str(record.get("board_id") or "").strip()
        row = {
            "board_id": board_id,
            "source_ids": list(record.get("source_ids") or []),
            "route_explanation": str(record.get("route_explanation") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not board_id:
            errors.append(f"board_route_records[{index}].board_id is required")
        if board_id in board_ids:
            errors.append(f"duplicate S2PDT04 board_id: {board_id}")
        board_ids.add(board_id)
        rows.append(row)
    if not rows:
        errors.append("S2PDT04 requires at least one board route record")
    return rows, errors


def _s2pdt04_replay_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = sorted({str(row.get("as_of_date") or "") for row in rows if isinstance(row, Mapping) and _is_iso_date(str(row.get("as_of_date") or ""))})
    bad_status = [row for row in rows if not isinstance(row, Mapping) or row.get("status") != "pass"]
    leakage = [row for row in rows if not isinstance(row, Mapping) or int(row.get("future_leakage_count") or 0) != 0]
    blockers = [row for row in rows if not isinstance(row, Mapping) or int(row.get("p0_p1_blocker_count") or 0) != 0]
    production = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("production_affected") is not False
        or row.get("formal_production_inclusion") is not False
    ]
    reasons: list[str] = []
    if len(dates) < S2PDT04_REQUIRED_REPLAY_DATES:
        reasons.append("S2PDT04 D3 replay requires at least 30 distinct as-of dates")
    if bad_status:
        reasons.append("S2PDT04 D3 replay records must all status=pass")
    if leakage:
        reasons.append("S2PDT04 D3 replay requires future_leakage_count=0")
    if blockers:
        reasons.append("S2PDT04 D3 replay requires p0_p1_blocker_count=0")
    if production:
        reasons.append("S2PDT04 D3 replay must not affect production or formal inclusion")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_replay_dates": S2PDT04_REQUIRED_REPLAY_DATES,
        "replay_dates_observed": dates,
        "replay_date_count": len(dates),
        "blocking_reasons": reasons,
    }


def _s2pdt04_shadow_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = sorted({str(row.get("shadow_date") or "") for row in rows if isinstance(row, Mapping) and _is_iso_date(str(row.get("shadow_date") or ""))})
    bad_status = [row for row in rows if not isinstance(row, Mapping) or row.get("status") != "pass"]
    production = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
        or row.get("formal_production_inclusion") is not False
        or row.get("d3_core_source_domain_accepted") is not False
    ]
    reasons: list[str] = []
    if len(dates) < S2PDT04_REQUIRED_SHADOW_DAYS:
        reasons.append("S2PDT04 D3 shadow requires at least 2 distinct shadow dates")
    if bad_status:
        reasons.append("S2PDT04 D3 shadow records must all status=pass")
    if production:
        reasons.append("S2PDT04 D3 shadow must not affect production, send SMTP, or accept D3 core")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_shadow_days": S2PDT04_REQUIRED_SHADOW_DAYS,
        "shadow_dates_observed": dates,
        "shadow_day_count": len(dates),
        "shadow_record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt04_authority_gate(
    replay_rows: Sequence[Mapping[str, Any]],
    shadow_rows: Sequence[Mapping[str, Any]],
    route_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    records = [*replay_rows, *shadow_rows, *route_rows]
    bad_authority = [
        row
        for row in records
        if not isinstance(row, Mapping) or row.get("authority_gate") != "pass" or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if bad_authority:
        reasons.append("S2PDT04 authority gate requires authority_gate=pass and evidence_refs on replay, shadow, and board routes")
    return {
        "status": "pass" if not reasons else "blocked",
        "authority_checked_record_count": len(records) - len(bad_authority),
        "record_count": len(records),
        "blocking_reasons": reasons,
    }


def _s2pdt04_board_routing_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("board_id") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT04_REQUIRED_BOARD_IDS) - observed)
    unsupported = sorted(observed - set(S2PDT04_REQUIRED_BOARD_IDS))
    incomplete = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or not row.get("source_ids")
        or not row.get("route_explanation")
        or row.get("authority_gate") != "pass"
        or row.get("metadata_only") is not True
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT04 board routing missing required boards: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT04 board routing has unsupported boards: " + ", ".join(unsupported))
    if incomplete:
        reasons.append("S2PDT04 board routes require source_ids, route_explanation, authority_gate=pass, and metadata_only=true")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_board_ids": list(S2PDT04_REQUIRED_BOARD_IDS),
        "board_ids_observed": sorted(board for board in observed if board),
        "route_record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt04_metadata_gate(
    replay_rows: Sequence[Mapping[str, Any]],
    shadow_rows: Sequence[Mapping[str, Any]],
    route_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    records = [*replay_rows, *shadow_rows, *route_rows]
    violations = [
        row
        for row in records
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
    ]
    evidence_missing = [row for row in records if not isinstance(row, Mapping) or not row.get("evidence_refs")]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PDT04 D3 readiness records must be metadata-only and production_affected=false")
    if evidence_missing:
        reasons.append("S2PDT04 D3 readiness records require evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(records) - len(violations),
        "evidence_backed_record_count": len(records) - len(evidence_missing),
        "record_count": len(records),
        "blocking_reasons": reasons,
    }


def _s2pft01_provincial_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    province_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"provincial_records[{index}] must be an object")
            continue
        province_id = str(record.get("province_id") or "").strip()
        row = {
            "province_id": province_id,
            "province_name": str(record.get("province_name") or "").strip(),
            "locality_type": str(record.get("locality_type") or "").strip(),
            "official_domain": str(record.get("official_domain") or "").strip(),
            "source_url": str(record.get("source_url") or "").strip(),
            "core_department_roles": list(record.get("core_department_roles") or []),
            "health_tier": str(record.get("health_tier") or "").strip(),
            "health_explanation": str(record.get("health_explanation") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not province_id:
            errors.append(f"provincial_records[{index}].province_id is required")
        if province_id in province_ids:
            errors.append(f"duplicate S2PFT01 province_id: {province_id}")
        province_ids.add(province_id)
        rows.append(row)
    if not rows:
        errors.append("S2PFT01 requires at least one provincial record")
    return rows, errors


def _s2pft01_provincial_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("province_id") or "") for row in rows if isinstance(row, Mapping)}
    observed_types = {
        str(row.get("locality_type") or "") for row in rows if isinstance(row, Mapping) and str(row.get("locality_type") or "")
    }
    missing = [province_id for province_id in S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS if province_id not in observed]
    unsupported = sorted(observed - set(S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS))
    missing_types = [locality_type for locality_type in S2PFT01_REQUIRED_LOCALITY_TYPES if locality_type not in observed_types]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT01 provincial coverage missing mainland provincial ids: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PFT01 provincial coverage has unsupported ids: " + ", ".join(unsupported))
    if missing_types:
        reasons.append("S2PFT01 provincial coverage missing locality types: " + ", ".join(missing_types))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_mainland_provincial_ids": list(S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS),
        "provincial_ids_observed": sorted(province_id for province_id in observed if province_id),
        "required_locality_types": list(S2PFT01_REQUIRED_LOCALITY_TYPES),
        "locality_types_observed": sorted(observed_types),
        "missing_mainland_provincial_ids": missing,
        "unsupported_provincial_ids": unsupported,
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft01_core_department_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    incomplete: list[Mapping[str, Any]] = []
    for row in rows:
        roles = set(row.get("core_department_roles") or []) if isinstance(row, Mapping) else set()
        if not set(S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES).issubset(roles):
            incomplete.append(row)
    reasons: list[str] = []
    if incomplete:
        reasons.append("S2PFT01 provincial records must include all required core department roles")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_core_department_roles": list(S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES),
        "complete_template_record_count": len(rows) - len(incomplete),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft01_health_tier_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    tiers = sorted(
        {
            str(row.get("health_tier") or "")
            for row in rows
            if isinstance(row, Mapping) and str(row.get("health_tier") or "")
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("health_tier") not in S2PFT01_ALLOWED_HEALTH_TIERS
        or not row.get("health_explanation")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT01 health tier requires allowed tier and health_explanation on every provincial record")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_health_tiers": list(S2PFT01_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": tiers,
        "healthy_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft01_provincial_authority_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("authority_gate") != "pass"
        or row.get("identity_state") not in S2PFT01_ALLOWED_IDENTITY_STATES
        or not row.get("official_domain")
        or not row.get("source_url")
        or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT01 authority gate requires official identity, domain, source_url, authority_gate=pass, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PFT01_ALLOWED_IDENTITY_STATES),
        "authority_checked_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft01_provincial_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PFT01 provincial records must stay metadata-only with no PDF/full-text, production, or SMTP side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(rows) - len(violations),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft02_jurisdiction_profiles(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    profiles: list[dict[str, Any]] = []
    errors: list[str] = []
    jurisdiction_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"jurisdiction_profiles[{index}] must be an object")
            continue
        jurisdiction_id = str(record.get("jurisdiction_id") or "").strip()
        profile = {
            "jurisdiction_id": jurisdiction_id,
            "jurisdiction_name": str(record.get("jurisdiction_name") or "").strip(),
            "legal_system_state": str(record.get("legal_system_state") or "").strip(),
            "government_structure_model": str(record.get("government_structure_model") or "").strip(),
            "language_profiles": list(record.get("language_profiles") or []),
            "official_domain": str(record.get("official_domain") or "").strip(),
            "source_url": str(record.get("source_url") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "template_source": str(record.get("template_source") or "").strip(),
            "mainland_template_applied": record.get("mainland_template_applied") is True,
            "autonomy_basis": str(record.get("autonomy_basis") or "").strip(),
            "legal_status_reference": str(record.get("legal_status_reference") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not jurisdiction_id:
            errors.append(f"jurisdiction_profiles[{index}].jurisdiction_id is required")
        if jurisdiction_id in jurisdiction_ids:
            errors.append(f"duplicate S2PFT02 jurisdiction_id: {jurisdiction_id}")
        jurisdiction_ids.add(jurisdiction_id)
        profiles.append(profile)
    if not profiles:
        errors.append("S2PFT02 requires at least one jurisdiction profile")
    return profiles, errors


def _s2pft02_jurisdiction_coverage_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(profile.get("jurisdiction_id") or "") for profile in profiles if isinstance(profile, Mapping)}
    missing = [jurisdiction_id for jurisdiction_id in S2PFT02_REQUIRED_JURISDICTION_IDS if jurisdiction_id not in observed]
    unsupported = sorted(observed - set(S2PFT02_REQUIRED_JURISDICTION_IDS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT02 HK/MO profile missing jurisdiction ids: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PFT02 HK/MO profile has unsupported jurisdiction ids: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_jurisdiction_ids": list(S2PFT02_REQUIRED_JURISDICTION_IDS),
        "jurisdiction_ids_observed": sorted(jurisdiction_id for jurisdiction_id in observed if jurisdiction_id),
        "missing_jurisdiction_ids": missing,
        "unsupported_jurisdiction_ids": unsupported,
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_language_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(language)
            for profile in profiles
            if isinstance(profile, Mapping)
            for language in list(profile.get("language_profiles") or [])
            if str(language)
        }
    )
    missing = [language for language in S2PFT02_REQUIRED_LANGUAGE_PROFILES if language not in set(observed)]
    missing_per_profile = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping) or not profile.get("language_profiles")
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT02 HK/MO profile missing language profiles: " + ", ".join(missing))
    if missing_per_profile:
        reasons.append("S2PFT02 each jurisdiction profile requires language_profiles")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_language_profiles": list(S2PFT02_REQUIRED_LANGUAGE_PROFILES),
        "language_profiles_observed": observed,
        "complete_language_profile_count": len(profiles) - len(missing_per_profile),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_legal_status_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(profile.get("legal_system_state") or "")
            for profile in profiles
            if isinstance(profile, Mapping) and str(profile.get("legal_system_state") or "")
        }
    )
    invalid = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping)
        or profile.get("legal_system_state") not in S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES
        or not profile.get("government_structure_model")
        or not profile.get("autonomy_basis")
        or not profile.get("legal_status_reference")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT02 legal status requires allowed legal system, government structure, autonomy basis, and legal status reference")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_legal_system_states": list(S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES),
        "legal_system_states_observed": observed,
        "legal_status_checked_record_count": len(profiles) - len(invalid),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_template_independence_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping)
        or profile.get("mainland_template_applied") is not False
        or profile.get("template_source") in S2PFT02_FORBIDDEN_TEMPLATE_STATES
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT02 HK/MO profiles must not reuse mainland province or city templates")
    return {
        "status": "pass" if not reasons else "blocked",
        "forbidden_template_states": list(S2PFT02_FORBIDDEN_TEMPLATE_STATES),
        "independent_profile_count": len(profiles) - len(invalid),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_authority_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping)
        or profile.get("authority_gate") != "pass"
        or not profile.get("official_domain")
        or not profile.get("source_url")
        or not profile.get("evidence_refs")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT02 authority gate requires official_domain, source_url, authority_gate=pass, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "authority_checked_record_count": len(profiles) - len(invalid),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_metadata_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping)
        or profile.get("metadata_only") is not True
        or profile.get("pdf_downloaded") is not False
        or profile.get("full_text_extracted") is not False
        or profile.get("production_affected") is not False
        or profile.get("real_smtp_sent") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PFT02 HK/MO profiles must stay metadata-only with no PDF/full-text, production, or SMTP side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(profiles) - len(violations),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    city_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"city_records[{index}] must be an object")
            continue
        city_id = str(record.get("city_id") or "").strip()
        try:
            region_weight = float(record.get("region_weight", 0))
        except (TypeError, ValueError):
            region_weight = 0.0
        row = {
            "city_id": city_id,
            "city_name": str(record.get("city_name") or "").strip(),
            "province_id": str(record.get("province_id") or "").strip(),
            "region_group": str(record.get("region_group") or "").strip(),
            "aliases": list(record.get("aliases") or []),
            "department_roles": list(record.get("department_roles") or []),
            "region_weight": region_weight,
            "health_tier": str(record.get("health_tier") or "").strip(),
            "health_explanation": str(record.get("health_explanation") or "").strip(),
            "official_domain": str(record.get("official_domain") or "").strip(),
            "source_url": str(record.get("source_url") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not city_id:
            errors.append(f"city_records[{index}].city_id is required")
        if city_id in city_ids:
            errors.append(f"duplicate S2PFT03 city_id: {city_id}")
        city_ids.add(city_id)
        rows.append(row)
    if not rows:
        errors.append("S2PFT03 requires at least one city record")
    return rows, errors


def _s2pft03_city_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("city_id") or "") for row in rows if isinstance(row, Mapping)}
    missing = [city_id for city_id in S2PFT03_REQUIRED_CITY_IDS if city_id not in observed]
    unsupported = sorted(observed - set(S2PFT03_REQUIRED_CITY_IDS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT03 key-city coverage missing city ids: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PFT03 key-city coverage has unsupported city ids: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_city_ids": list(S2PFT03_REQUIRED_CITY_IDS),
        "city_ids_observed": sorted(city_id for city_id in observed if city_id),
        "missing_city_ids": missing,
        "unsupported_city_ids": unsupported,
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_alias_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [row for row in rows if not isinstance(row, Mapping) or not row.get("city_name") or not row.get("aliases")]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT03 key-city records require city_name and aliases")
    return {
        "status": "pass" if not reasons else "blocked",
        "alias_checked_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_department_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_by_city: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        roles = set(row.get("department_roles") or [])
        missing = [role for role in S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES if role not in roles]
        if missing:
            missing_by_city[str(row.get("city_id") or "")] = missing
    reasons: list[str] = []
    if missing_by_city:
        reasons.append("S2PFT03 key-city records missing required department roles")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_city_department_roles": list(S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES),
        "complete_department_record_count": len(rows) - len(missing_by_city),
        "record_count": len(rows),
        "missing_roles_by_city": missing_by_city,
        "blocking_reasons": reasons,
    }


def _s2pft03_region_weight_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(row.get("region_group") or "")
            for row in rows
            if isinstance(row, Mapping) and str(row.get("region_group") or "")
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("region_group") not in S2PFT03_ALLOWED_REGION_GROUPS
        or not (0 < float(row.get("region_weight") or 0) <= 1)
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT03 key-city records require allowed region_group and region_weight in (0, 1]")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_region_groups": list(S2PFT03_ALLOWED_REGION_GROUPS),
        "region_groups_observed": observed,
        "region_weight_total": round(sum(float(row.get("region_weight") or 0) for row in rows if isinstance(row, Mapping)), 6),
        "weighted_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_health_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(row.get("health_tier") or "")
            for row in rows
            if isinstance(row, Mapping) and str(row.get("health_tier") or "")
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("health_tier") not in S2PFT03_ALLOWED_HEALTH_TIERS
        or not row.get("health_explanation")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT03 key-city records require allowed health_tier and health_explanation")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_health_tiers": list(S2PFT03_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": observed,
        "healthy_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_authority_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("authority_gate") != "pass"
        or not row.get("official_domain")
        or not row.get("source_url")
        or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT03 key-city authority gate requires official_domain, source_url, authority_gate=pass, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "authority_checked_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PFT03 key-city records must stay metadata-only with no PDF/full-text, production, or SMTP side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(rows) - len(violations),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _is_iso_date(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        Date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _top_journal_profiles_from_batches(
    source_batches: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    profiles: list[dict[str, Any]] = []
    relation_edges: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []
    errors: list[str] = []
    for journal in S2PCT04_REQUIRED_JOURNALS:
        batch = source_batches.get(journal)
        if not isinstance(batch, Mapping):
            reason = f"{journal}: missing completed top-journal source batch for S2PCT04 profile modeling"
            source_reports.append({"journal": journal, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        batch_errors = validate_top_journal_source_batch(batch)
        blocked = bool(batch_errors or batch.get("status") == "blocked")
        source_reports.append(
            {
                "journal": journal,
                "status": "blocked" if blocked else "pass",
                "source_item_count": len(batch.get("source_items") or []),
                "new_item_count": int(batch.get("new_item_count") or 0),
                "blocking_reasons": batch_errors or list(batch.get("blocking_reasons") or []),
            }
        )
        if blocked:
            errors.extend(f"{journal}: {reason}" for reason in (batch_errors or batch.get("blocking_reasons") or []))
            continue
        for source_item in batch.get("source_items") or []:
            if not isinstance(source_item, Mapping):
                continue
            profile, edge, profile_errors = _top_journal_profile_from_source_item(source_item, generated_at=generated_at)
            errors.extend(profile_errors)
            if profile_errors:
                continue
            profiles.append(profile)
            relation_edges.append(edge)
    return profiles, relation_edges, source_reports, errors


def _top_journal_profile_from_source_item(
    source_item: Mapping[str, Any],
    *,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    metadata = source_item.get("metadata") if isinstance(source_item.get("metadata"), Mapping) else {}
    top_journal = metadata.get("top_journal") if isinstance(metadata.get("top_journal"), Mapping) else {}
    if not isinstance(top_journal, Mapping) or not top_journal:
        return {}, {}, [f"{source_item.get('source_id', 'source')}: top_journal metadata missing"]
    canonical_id = _canonical_document_id(source_item)
    source_id = str(source_item.get("source_id") or canonical_id)
    article_type = str(top_journal.get("article_type") or "")
    profile_kind = _top_journal_profile_kind(article_type)
    if not profile_kind:
        errors.append(f"{source_id}: unsupported top-journal profile article_type {article_type!r}")
    journal = str(top_journal.get("journal_id") or "")
    if journal not in S2PCT04_REQUIRED_JOURNALS:
        errors.append(f"{source_id}: journal must be one of {list(S2PCT04_REQUIRED_JOURNALS)}")
    profile = {
        "profile_id": f"profile:{canonical_id}",
        "source_id": source_id,
        "canonical_document_id": canonical_id,
        "journal": journal,
        "journal_display": str(top_journal.get("journal") or journal),
        "title": str(source_item.get("title") or ""),
        "article_type": article_type,
        "article_type_raw": str(top_journal.get("article_type_raw") or article_type),
        "profile_kind": profile_kind,
        "profile_role": _top_journal_profile_role(profile_kind),
        "publication_status": "active",
        "generated_at": generated_at,
        "metadata_only": True,
        "production_eligible": False,
        "evidence_refs": list(source_item.get("evidence_refs") or []),
    }
    relation = {
        "edge_id": f"relation:{canonical_id}:original-publication",
        "relation_type": "original_publication",
        "source_canonical_document_id": canonical_id,
        "target_canonical_document_id": canonical_id,
        "target_required": False,
        "event_type": "original_publication",
        "metadata_only": True,
        "evidence_refs": list(source_item.get("evidence_refs") or []),
    }
    return profile, relation, errors


def _top_journal_profiles_from_publication_events(
    publication_events: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
    known_targets: set[str],
    prior_index: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    profiles: list[dict[str, Any]] = []
    relation_edges: list[dict[str, Any]] = []
    forced_updates: list[dict[str, Any]] = []
    event_reports: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, event in enumerate(publication_events):
        if not isinstance(event, Mapping):
            reason = f"publication_events[{index}] must be an object"
            event_reports.append({"index": index, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        profile, edge, profile_errors = _top_journal_profile_from_publication_event(
            event,
            generated_at=generated_at,
            known_targets=known_targets,
        )
        event_reports.append(
            {
                "event_id": str(event.get("event_id") or event.get("source_id") or f"publication-event-{index}"),
                "status": "blocked" if profile_errors else "pass",
                "profile_kind": profile.get("profile_kind", ""),
                "relation_type": edge.get("relation_type", ""),
                "blocking_reasons": profile_errors,
            }
        )
        errors.extend(profile_errors)
        if profile_errors:
            continue
        profiles.append(profile)
        relation_edges.append(edge)
        if profile.get("profile_kind") in S2PCT04_FORCED_EVENT_TYPES:
            forced_updates.append(_forced_event_update_from_profile(profile, prior_index=prior_index))
    return profiles, relation_edges, forced_updates, event_reports, errors


def _top_journal_profile_from_publication_event(
    event: Mapping[str, Any],
    *,
    generated_at: str,
    known_targets: set[str],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    event_id = str(event.get("event_id") or event.get("source_id") or "")
    source_id = str(event.get("source_id") or event_id)
    canonical_id = str(event.get("canonical_document_id") or source_id)
    journal = str(event.get("journal") or "")
    title = str(event.get("title") or "")
    article_type = str(event.get("article_type") or event.get("event_type") or event.get("profile_kind") or "")
    profile_kind = _top_journal_profile_kind(article_type)
    target_id = str(event.get("target_canonical_document_id") or "")
    relation_type = str(event.get("relation_type") or _default_relation_type(profile_kind))
    target_required = relation_type != "original_publication" or profile_kind in S2PCT04_FORCED_EVENT_TYPES
    if not event_id:
        errors.append("publication event requires event_id or source_id")
    if journal not in S2PCT04_REQUIRED_JOURNALS:
        errors.append(f"{event_id or source_id}: journal must be one of {list(S2PCT04_REQUIRED_JOURNALS)}")
    if not canonical_id:
        errors.append(f"{event_id or source_id}: canonical_document_id is required")
    if not title:
        errors.append(f"{event_id or source_id}: title is required")
    if not profile_kind:
        errors.append(f"{event_id or source_id}: unsupported publication event article_type {article_type!r}")
    if target_required and not target_id:
        errors.append(f"{event_id or source_id}: target_canonical_document_id is required for {relation_type}")
    if target_id and target_id not in known_targets:
        errors.append(f"{event_id or source_id}: target_canonical_document_id is unknown: {target_id}")
    profile = {
        "profile_id": f"profile:{canonical_id}",
        "event_id": event_id,
        "source_id": source_id,
        "canonical_document_id": canonical_id,
        "target_canonical_document_id": target_id,
        "journal": journal,
        "journal_display": str(event.get("journal_display") or journal.title()),
        "title": title,
        "article_type": _profile_token(article_type),
        "article_type_raw": article_type,
        "profile_kind": profile_kind,
        "profile_role": _top_journal_profile_role(profile_kind),
        "publication_status": profile_kind if profile_kind in S2PCT04_FORCED_EVENT_TYPES else "active",
        "generated_at": generated_at,
        "observed_at": str(event.get("observed_at") or generated_at),
        "metadata_only": True,
        "production_eligible": False,
        "evidence_refs": list(event.get("evidence_refs") or []),
    }
    edge = {
        "edge_id": f"relation:{canonical_id}:{relation_type}:{target_id or canonical_id}",
        "event_id": event_id,
        "relation_type": relation_type,
        "source_canonical_document_id": canonical_id,
        "target_canonical_document_id": target_id or canonical_id,
        "target_required": target_required,
        "event_type": profile_kind,
        "metadata_only": True,
        "evidence_refs": list(event.get("evidence_refs") or []),
    }
    return profile, edge, errors


def _top_journal_profile_kind(article_type: str) -> str:
    token = _profile_token(article_type)
    if token in {"research", "research_article", "research_article_feed_item", "report", "article", "articles"}:
        return "research"
    if token in {"review", "seminar", "series", "commission", "commissions", "clinical_rounds"}:
        return "review"
    if token in {"editorial", "commentary", "opinion", "perspective", "perspectives", "viewpoint", "viewpoints"}:
        return "editorial"
    if token in {"news", "news_feature", "news_and_views", "news_analysis"}:
        return "news"
    if token in {"correction", "corrigendum", "erratum", "addendum"}:
        return "correction"
    if token in {"retraction", "retracted", "withdrawal", "withdrawn"}:
        return "retraction"
    return ""


def _top_journal_profile_role(profile_kind: str) -> str:
    return {
        "research": "primary_evidence_candidate",
        "review": "synthesis_context_candidate",
        "editorial": "opinion_or_context_not_primary_evidence",
        "news": "secondary_news_context_not_primary_evidence",
        "correction": "forced_revision_event",
        "retraction": "forced_invalidation_event",
    }.get(profile_kind, "unknown")


def _default_relation_type(profile_kind: str) -> str:
    if profile_kind == "correction":
        return "corrects"
    if profile_kind == "retraction":
        return "retracts"
    if profile_kind in {"editorial", "news"}:
        return "discusses"
    return "original_publication"


def _prior_profile_state_index(prior_profile_state: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not isinstance(prior_profile_state, Mapping):
        return {}
    raw_items: list[Any] = []
    if isinstance(prior_profile_state.get("items"), list):
        raw_items = list(prior_profile_state["items"])
    elif prior_profile_state.get("canonical_document_id"):
        raw_items = [prior_profile_state]
    else:
        raw_items = [value for value in prior_profile_state.values() if isinstance(value, Mapping)]
    index: dict[str, Mapping[str, Any]] = {}
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        canonical_id = str(item.get("canonical_document_id") or item.get("source_id") or "")
        if canonical_id:
            index[canonical_id] = item
    return index


def _forced_event_update_from_profile(profile: Mapping[str, Any], *, prior_index: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    event_type = str(profile.get("profile_kind") or "")
    target_id = str(profile.get("target_canonical_document_id") or "")
    prior = prior_index.get(target_id, {})
    invalidating = event_type == "retraction"
    return {
        "update_id": f"forced-update:{event_type}:{_safe_id(target_id)}:{_safe_id(str(profile.get('event_id') or profile.get('source_id') or 'event'))}",
        "model_id": S2PCT04_JOURNAL_PROFILE_MODEL_ID,
        "acceptance_id": S2PCT04_ACCEPTANCE_ID,
        "task_id": S2PCT04_TASK_ID,
        "legacy_task_id": S2PCT04_LEGACY_TASK_ID,
        "event_id": str(profile.get("event_id") or profile.get("source_id") or ""),
        "event_type": event_type,
        "event_canonical_document_id": str(profile.get("canonical_document_id") or ""),
        "target_canonical_document_id": target_id,
        "prior_conclusion_state": str(prior.get("conclusion_state") or prior.get("publication_status") or "active_or_unknown"),
        "updated_conclusion_state": "invalidated" if invalidating else "requires_revision",
        "publication_status": "retracted" if invalidating else "corrected",
        "forced_review_required": True,
        "allowed_action": "remove_or_mark_invalid_before_reuse" if invalidating else "revise_existing_summary_before_reuse",
        "metadata_only": True,
        "generated_at": str(profile.get("generated_at") or ""),
    }


def _publication_relation_errors(profiles: Sequence[Mapping[str, Any]], relation_edges: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    edge_sources = {str(edge.get("source_canonical_document_id") or "") for edge in relation_edges if isinstance(edge, Mapping)}
    for profile in profiles:
        canonical_id = str(profile.get("canonical_document_id") or "")
        if canonical_id and canonical_id not in edge_sources:
            errors.append(f"{canonical_id}: missing publication relation edge")
    for edge in relation_edges:
        if not isinstance(edge, Mapping):
            errors.append("publication relation edge must be an object")
            continue
        if not edge.get("relation_type"):
            errors.append("publication relation edge missing relation_type")
        if edge.get("target_required") is True and not edge.get("target_canonical_document_id"):
            errors.append(f"{edge.get('edge_id', 'relation')}: missing required target_canonical_document_id")
        if edge.get("metadata_only") is not True:
            errors.append(f"{edge.get('edge_id', 'relation')}: relation edge must be metadata_only")
    return errors


def _forced_event_update_errors(
    event_profiles: Sequence[Mapping[str, Any]],
    forced_updates: Sequence[Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    update_keys = {
        (str(update.get("event_type") or ""), str(update.get("target_canonical_document_id") or ""))
        for update in forced_updates
        if isinstance(update, Mapping)
    }
    for profile in event_profiles:
        profile_kind = str(profile.get("profile_kind") or "")
        if profile_kind not in S2PCT04_FORCED_EVENT_TYPES:
            continue
        target_id = str(profile.get("target_canonical_document_id") or "")
        if not target_id:
            errors.append(f"{profile.get('event_id', 'forced-event')}: forced event target missing")
            continue
        if (profile_kind, target_id) not in update_keys:
            errors.append(f"{profile.get('event_id', 'forced-event')}: forced event update not generated")
    return errors


def _forced_event_kinds(updates: Sequence[Mapping[str, Any]]) -> set[str]:
    return {str(update.get("event_type") or "") for update in updates if isinstance(update, Mapping) and update.get("event_type")}


def _duplicate_values(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _profile_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


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
