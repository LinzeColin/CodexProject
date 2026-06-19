from __future__ import annotations

import html
import csv
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tab_research.automation_doctor import write_automation_doctor_bundle
from tab_research.automation_maturity import write_automation_maturity_bundle
from tab_research.active_timeline_report import write_active_timeline_report_bundle
from tab_research.available_board_strategy import write_available_board_strategy_bundle
from tab_research.daily_boards import current_matches_board
from tab_research.dashboard import write_dashboard_sidecar_bundle
from tab_research.fixture_sanity import write_fixture_sanity_bundle
from tab_research.live_board_discovery import write_live_board_discovery_bundle
from tab_research.model_compare import MODEL_COMPARISON_JSON, write_model_comparison
from tab_research.model_divergence_review import write_model_divergence_review_bundle
from tab_research.partial_daily_research import write_partial_daily_research_bundle
from tab_research.paths import resolve_output_dir, resolve_workspace_root
from tab_research.raw_refresh_recovery import write_raw_refresh_recovery_bundle
from tab_research.raw_refresh import normalize_partial_research_refresh
from tab_research.goal_traceability import write_goal_traceability_bundle
from tab_research.position_monitor import write_position_monitor_bundle
from tab_research.product_readiness import write_product_readiness_bundle
from tab_research.provider_alternate_plan import write_provider_alternate_plan_bundle
from tab_research.provider_config_doctor import write_provider_config_doctor_bundle
from tab_research.provider_fallback_verification import write_provider_fallback_verification_bundle
from tab_research.provider_kpi import write_provider_kpi_bundle
from tab_research.provider_manual_verification import (
    DEFAULT_IMPORT_RELATIVE_PATH,
    PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST,
    write_provider_manual_verification_bundle,
)
from tab_research.public_snapshot_importer import write_public_snapshot_import_bundle
from tab_research.report_evolution import write_report_evolution_bundle
from tab_research.report_intelligence import write_report_intelligence_bundle
from tab_research.report_visual_inventory import write_report_visual_inventory_bundle
from tab_research.recommendation_operations import (
    DEFAULT_BANKROLL_REFERENCE_AUD,
    annotate_live_board_scope,
    bankroll_reference_aud,
    board_scope_index,
    decision_diagnostics,
    decision_metric_pack,
    discounted_kelly_fraction,
    edge_quality_label,
    edge_threshold_gap,
    expected_profit_aud,
    expected_profit_per_100_aud,
    full_kelly_fraction,
    kelly_safety_margin,
    market_edge_threshold,
    market_edge_threshold_range,
    market_funding_profile,
    market_funding_reason,
    market_funding_summary,
    model_calibration_for_recommendation,
    model_calibration_index,
    minimum_acceptable_odds,
    odds_buffer,
    over_half_kelly_ratio,
    price_drift_tolerance_pct,
    risk_drivers,
    risk_adjusted_value_score,
    risk_of_ruin_estimate,
    risk_of_ruin_grade,
    row_analysis_basis,
    stake_to_cap_ratio,
    stake_fraction_of_bankroll,
    value_arbitrage_rate,
    value_signal_label,
    write_recommendation_operations_bundle,
    live_board_scope_allowed,
)
from tab_research.source_model_registry import write_source_model_registry_bundle
from tab_research.strategy_performance import write_strategy_performance_bundle


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = resolve_workspace_root(Path(__file__))
OUTPUT_DIR = resolve_output_dir(Path(__file__))
DOWNLOADS_DIR = Path.home() / "Downloads"
REPORT_DIR = DOWNLOADS_DIR / "FIFA Report"
ENTRY_HTML = REPORT_DIR / "TAB FIFA盘口研究系统.html"
APP_BUNDLE = DOWNLOADS_DIR / "TAB FIFA盘口研究系统.app"
ASSETS_DIR = REPORT_DIR / "app_assets"
RUNTIME_ENTRY_HTML = OUTPUT_DIR / "tab_fifa_app_entry_runtime.html"
APP_PORT = int(os.getenv("TAB_FIFA_APP_PORT", "8767"))
WEB_APP_URL = f"http://127.0.0.1:{APP_PORT}/"
APP_ICON_NAME = "TABFIFAResearch"
APP_ICON_SOURCE = PIPELINE_ROOT / "assets" / "app_icon" / f"{APP_ICON_NAME}.icns"
PROVIDER_CREDIT_RESERVE_FLOOR = 200


ASSET_COPIES = {
    "tab_fifa_dashboard_latest.html": "dashboard.html",
    "tab_fifa_dashboard_data_latest.json": "dashboard_data_latest.json",
    "tab_fifa_dashboard_latest.md": "tab_fifa_dashboard_latest.md",
    "tab_fifa_dashboard_latest.pdf": "tab_fifa_dashboard_latest.pdf",
    "report_index_latest.json": "report_index_latest.json",
    "report_index_latest.md": "report_index_latest.md",
    "report_index_latest.pdf": "report_index_latest.pdf",
    "automation_readiness_latest.json": "automation_readiness_latest.json",
    "automation_readiness_latest.md": "automation_readiness_latest.md",
    "automation_readiness_latest.pdf": "automation_readiness_latest.pdf",
    "automation_candidate_latest.json": "automation_candidate_latest.json",
    "automation_candidate_latest.md": "automation_candidate_latest.md",
    "automation_candidate_latest.pdf": "automation_candidate_latest.pdf",
    "tab_fifa_reports.sqlite3": "tab_fifa_reports.sqlite3",
    "latest_commit.json": "latest_commit.json",
    "automation_run_latest.json": "automation_run_latest.json",
    "raw_refresh_health_latest.json": "raw_refresh_health_latest.json",
    "raw_refresh_research_only_latest.json": "raw_refresh_research_only_latest.json",
    "matches_repair_validation_latest.json": "matches_repair_validation_latest.json",
    "raw_refresh_recovery_latest.json": "raw_refresh_recovery_latest.json",
    "raw_refresh_recovery_latest.md": "raw_refresh_recovery_latest.md",
    "raw_refresh_recovery_latest.pdf": "raw_refresh_recovery_latest.pdf",
    "tab_fifa_live_board_discovery_raw_latest.json": "tab_fifa_live_board_discovery_raw_latest.json",
    "live_board_discovery_latest.json": "live_board_discovery_latest.json",
    "live_board_discovery_latest.md": "live_board_discovery_latest.md",
    "live_board_discovery_latest.pdf": "live_board_discovery_latest.pdf",
    "available_board_strategy_latest.json": "available_board_strategy_latest.json",
    "available_board_strategy_latest.md": "available_board_strategy_latest.md",
    "available_board_strategy_latest.pdf": "available_board_strategy_latest.pdf",
    "partial_daily_research_latest.json": "partial_daily_research_latest.json",
    "partial_daily_research_latest.md": "partial_daily_research_latest.md",
    "partial_daily_research_latest.pdf": "partial_daily_research_latest.pdf",
    "fixture_sanity_latest.json": "fixture_sanity_latest.json",
    "fixture_sanity_latest.md": "fixture_sanity_latest.md",
    "fixture_sanity_latest.pdf": "fixture_sanity_latest.pdf",
    "openfootball_worldcup_2026_raw_latest.json": "openfootball_worldcup_2026_raw_latest.json",
    "active_timeline_latest.json": "active_timeline_latest.json",
    "active_timeline_report_latest.json": "active_timeline_report_latest.json",
    "active_timeline_report_latest.md": "active_timeline_report_latest.md",
    "active_timeline_report_latest.pdf": "active_timeline_report_latest.pdf",
    "active_backfill_latest.json": "active_backfill_latest.json",
    "recommendation_operations_latest.json": "recommendation_operations_latest.json",
    "recommendation_operations_latest.md": "recommendation_operations_latest.md",
    "recommendation_operations_latest.pdf": "recommendation_operations_latest.pdf",
    "strategy_performance_latest.json": "strategy_performance_latest.json",
    "strategy_performance_latest.md": "strategy_performance_latest.md",
    "strategy_performance_latest.pdf": "strategy_performance_latest.pdf",
    "product_readiness_dashboard_latest.json": "product_readiness_dashboard_latest.json",
    "product_readiness_dashboard_latest.md": "product_readiness_dashboard_latest.md",
    "product_readiness_dashboard_latest.pdf": "product_readiness_dashboard_latest.pdf",
    "automation_maturity_latest.json": "automation_maturity_latest.json",
    "automation_maturity_latest.md": "automation_maturity_latest.md",
    "automation_maturity_latest.pdf": "automation_maturity_latest.pdf",
    "goal_traceability_latest.json": "goal_traceability_latest.json",
    "goal_traceability_latest.md": "goal_traceability_latest.md",
    "goal_traceability_latest.pdf": "goal_traceability_latest.pdf",
    "position_monitor_latest.json": "position_monitor_latest.json",
    "position_monitor_latest.md": "position_monitor_latest.md",
    "position_monitor_latest.pdf": "position_monitor_latest.pdf",
    "tab_fifa_model_comparison_v0_1.json": "tab_fifa_model_comparison_v0_1.json",
    "tab_fifa_model_comparison_v0_1.md": "tab_fifa_model_comparison_v0_1.md",
    "tab_fifa_model_comparison_v0_1.pdf": "tab_fifa_model_comparison_v0_1.pdf",
    "model_divergence_review_latest.json": "model_divergence_review_latest.json",
    "model_divergence_review_latest.md": "model_divergence_review_latest.md",
    "model_divergence_review_latest.pdf": "model_divergence_review_latest.pdf",
    "source_model_registry_latest.json": "source_model_registry_latest.json",
    "source_model_registry_latest.md": "source_model_registry_latest.md",
    "source_model_registry_latest.pdf": "source_model_registry_latest.pdf",
    "source_model_github_metadata_latest.json": "source_model_github_metadata_latest.json",
    "report_intelligence_latest.json": "report_intelligence_latest.json",
    "report_intelligence_latest.md": "report_intelligence_latest.md",
    "report_intelligence_latest.pdf": "report_intelligence_latest.pdf",
    "report_evolution_latest.json": "report_evolution_latest.json",
    "report_evolution_latest.md": "report_evolution_latest.md",
    "report_evolution_latest.pdf": "report_evolution_latest.pdf",
    "report_visual_inventory_latest.json": "report_visual_inventory_latest.json",
    "report_visual_inventory_latest.md": "report_visual_inventory_latest.md",
    "report_visual_inventory_latest.pdf": "report_visual_inventory_latest.pdf",
    "automation_doctor_latest.json": "automation_doctor_latest.json",
    "automation_doctor_latest.md": "automation_doctor_latest.md",
    "automation_doctor_latest.pdf": "automation_doctor_latest.pdf",
    "provider_config_doctor_latest.json": "provider_config_doctor_latest.json",
    "provider_config_doctor_latest.md": "provider_config_doctor_latest.md",
    "provider_config_doctor_latest.pdf": "provider_config_doctor_latest.pdf",
    "provider_kpi_latest.json": "provider_kpi_latest.json",
    "provider_kpi_latest.md": "provider_kpi_latest.md",
    "provider_kpi_latest.pdf": "provider_kpi_latest.pdf",
    "odds_provider_coverage_latest.json": "odds_provider_coverage_latest.json",
    "odds_provider_blocked_latest.json": "odds_provider_blocked_latest.json",
    "provider_alternate_plan_latest.json": "provider_alternate_plan_latest.json",
    "provider_alternate_plan_latest.md": "provider_alternate_plan_latest.md",
    "provider_alternate_plan_latest.pdf": "provider_alternate_plan_latest.pdf",
    "provider_alternate_probe_evidence_latest.json": "provider_alternate_probe_evidence_latest.json",
    "provider_fallback_verification_latest.json": "provider_fallback_verification_latest.json",
    "provider_fallback_verification_latest.md": "provider_fallback_verification_latest.md",
    "provider_fallback_verification_latest.pdf": "provider_fallback_verification_latest.pdf",
    "provider_manual_verification_template_latest.csv": "provider_manual_verification_template_latest.csv",
    "provider_manual_pair_template_latest.csv": "provider_manual_pair_template_latest.csv",
    "provider_manual_next_batch_pair_template_latest.csv": "provider_manual_next_batch_pair_template_latest.csv",
    "provider_manual_verification_status_latest.json": "provider_manual_verification_status_latest.json",
    "provider_manual_verification_status_latest.md": "provider_manual_verification_status_latest.md",
    "provider_manual_verification_status_latest.pdf": "provider_manual_verification_status_latest.pdf",
    "provider_manual_hash_gate_latest.json": "provider_manual_hash_gate_latest.json",
    "provider_manual_hash_gate_latest.md": "provider_manual_hash_gate_latest.md",
    "provider_manual_hash_gate_latest.pdf": "provider_manual_hash_gate_latest.pdf",
    "provider_manual_overlay_preview_latest.json": "provider_manual_overlay_preview_latest.json",
    "provider_manual_overlay_preview_latest.md": "provider_manual_overlay_preview_latest.md",
    "provider_manual_overlay_preview_latest.pdf": "provider_manual_overlay_preview_latest.pdf",
    "provider_manual_team_total_overlay_raw_latest.json": "provider_manual_team_total_overlay_raw_latest.json",
    "provider_manual_overlay_approval_template_latest.json": "provider_manual_overlay_approval_template_latest.json",
    "provider_manual_overlay_publish_preflight_latest.json": "provider_manual_overlay_publish_preflight_latest.json",
    "provider_manual_overlay_publish_preflight_latest.md": "provider_manual_overlay_publish_preflight_latest.md",
    "provider_manual_overlay_publish_preflight_latest.pdf": "provider_manual_overlay_publish_preflight_latest.pdf",
    "provider_manual_overlay_publish_latest.json": "provider_manual_overlay_publish_latest.json",
    "provider_manual_overlay_publish_latest.md": "provider_manual_overlay_publish_latest.md",
    "provider_manual_overlay_publish_latest.pdf": "provider_manual_overlay_publish_latest.pdf",
    "provider_manual_workbench_latest.json": "provider_manual_workbench_latest.json",
    "provider_manual_workbench_latest.md": "provider_manual_workbench_latest.md",
    "provider_manual_workbench_latest.pdf": "provider_manual_workbench_latest.pdf",
    "public_snapshot_import_status_latest.json": "public_snapshot_import_status_latest.json",
    "public_snapshot_import_status_latest.md": "public_snapshot_import_status_latest.md",
    "public_snapshot_import_status_latest.pdf": "public_snapshot_import_status_latest.pdf",
    "public_snapshot_import_manifest_template_latest.json": "public_snapshot_import_manifest_template_latest.json",
    "public_snapshot_import_preview_raw_latest.json": "public_snapshot_import_preview_raw_latest.json",
    "public_snapshot_import_approval_template_latest.json": "public_snapshot_import_approval_template_latest.json",
    "public_snapshot_import_publish_preflight_latest.json": "public_snapshot_import_publish_preflight_latest.json",
    "public_snapshot_import_publish_preflight_latest.md": "public_snapshot_import_publish_preflight_latest.md",
    "public_snapshot_import_publish_preflight_latest.pdf": "public_snapshot_import_publish_preflight_latest.pdf",
    "public_snapshot_raw_publish_latest.json": "public_snapshot_raw_publish_latest.json",
    "public_snapshot_raw_publish_latest.md": "public_snapshot_raw_publish_latest.md",
    "public_snapshot_raw_publish_latest.pdf": "public_snapshot_raw_publish_latest.pdf",
}


def ensure_default_backfill_status() -> None:
    path = OUTPUT_DIR / "active_backfill_latest.json"
    if path.exists():
        return
    payload = {
        "schema_version": 1,
        "mode": "safe_no_latest_publish",
        "requested_count": 0,
        "completed_count": 0,
        "results": [],
        "status": "not_run_yet",
        "truthfulness_note": "尚未执行主动补跑；补跑报告不会发布 latest_commit。",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_dashboard_sidecars() -> dict[str, Any]:
    return write_dashboard_sidecar_bundle(OUTPUT_DIR)


def ensure_report_intelligence() -> dict[str, Any]:
    return write_report_intelligence_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_report_evolution() -> dict[str, Any]:
    return write_report_evolution_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_model_comparison() -> dict[str, Any]:
    raw_path = OUTPUT_DIR / current_matches_board().raw_snapshot
    if not raw_path.exists():
        return load_json(OUTPUT_DIR / MODEL_COMPARISON_JSON)
    try:
        raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return load_json(OUTPUT_DIR / MODEL_COMPARISON_JSON)
    return write_model_comparison(raw_payload, OUTPUT_DIR)


def ensure_automation_doctor() -> dict[str, Any]:
    return write_automation_doctor_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_automation_maturity() -> dict[str, Any]:
    return write_automation_maturity_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_goal_traceability() -> dict[str, Any]:
    return write_goal_traceability_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_position_monitor() -> dict[str, Any]:
    return write_position_monitor_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_product_readiness() -> dict[str, Any]:
    return write_product_readiness_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_provider_kpi() -> dict[str, Any]:
    write_provider_alternate_plan_bundle(OUTPUT_DIR)
    return write_provider_kpi_bundle(OUTPUT_DIR)


def ensure_provider_config_doctor() -> dict[str, Any]:
    return write_provider_config_doctor_bundle(OUTPUT_DIR, PIPELINE_ROOT)


def ensure_provider_fallback_verification() -> dict[str, Any]:
    return write_provider_fallback_verification_bundle(OUTPUT_DIR)


def ensure_provider_manual_verification() -> dict[str, Any]:
    return write_provider_manual_verification_bundle(OUTPUT_DIR)


def ensure_public_snapshot_import() -> dict[str, Any]:
    return write_public_snapshot_import_bundle(OUTPUT_DIR)


def ensure_recommendation_operations() -> dict[str, Any]:
    return write_recommendation_operations_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_strategy_performance() -> dict[str, Any]:
    return write_strategy_performance_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_model_divergence_review() -> dict[str, Any]:
    return write_model_divergence_review_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_source_model_registry() -> dict[str, Any]:
    return write_source_model_registry_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_raw_refresh_recovery() -> dict[str, Any]:
    return write_raw_refresh_recovery_bundle(OUTPUT_DIR)


def ensure_live_board_discovery() -> dict[str, Any]:
    return write_live_board_discovery_bundle(OUTPUT_DIR)


def ensure_available_board_strategy() -> dict[str, Any]:
    return write_available_board_strategy_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_partial_daily_research() -> dict[str, Any]:
    return write_partial_daily_research_bundle(OUTPUT_DIR)


def ensure_fixture_sanity() -> dict[str, Any]:
    return write_fixture_sanity_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_active_timeline_report() -> dict[str, Any]:
    return write_active_timeline_report_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def ensure_report_visual_inventory() -> dict[str, Any]:
    return write_report_visual_inventory_bundle(OUTPUT_DIR, OUTPUT_DIR / "tab_fifa_reports.sqlite3")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def text(value: Any, default: str = "待同步") -> str:
    if value is None or value == "":
        return default
    return str(value)


def yn(value: Any) -> str:
    return "是" if value is True else "否"


def money(value: Any) -> str:
    try:
        return f"AUD {float(value):,.0f}"
    except (TypeError, ValueError):
        return "待同步"


def pct(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "待校准"


def width_pct(value: Any) -> str:
    try:
        ratio = min(max(float(value), 0.0), 1.0)
        return f"{ratio * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def pp(value: Any) -> str:
    try:
        return f"{float(value) * 100:+.2f}pp"
    except (TypeError, ValueError):
        return "待校准"


def decimal(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "待校准"


def decimal_signed(value: Any) -> str:
    try:
        return f"{float(value):+.2f}"
    except (TypeError, ValueError):
        return "待校准"


def int_or_none(value: Any) -> int | None:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def provider_credit_runway(
    *,
    reported_remaining: Any,
    estimated_credit_floor: Any,
    estimated_credit_ceiling: Any,
    recommended_batch_size: int,
) -> dict[str, Any]:
    remaining = int_or_none(reported_remaining)
    floor = max(0, int_or_none(estimated_credit_floor) or 0)
    ceiling = max(floor, int_or_none(estimated_credit_ceiling) or floor)
    remaining_after_floor = remaining - floor if remaining is not None else None
    remaining_after_ceiling = remaining - ceiling if remaining is not None else None
    if remaining is None:
        status = "credit_unknown"
        safe_batches = 0
        label = "Credit 未同步"
        action = "暂停 API，先刷新 Provider KPI。"
    elif remaining <= PROVIDER_CREDIT_RESERVE_FLOOR:
        status = "reserve_floor_reached"
        safe_batches = 0
        label = "已到保底线"
        action = "停止 The Odds API 新增 probe，转 TT-001 人工校验或 OpticOdds。"
    elif ceiling and remaining_after_ceiling is not None and remaining_after_ceiling < PROVIDER_CREDIT_RESERVE_FLOOR:
        status = "next_batch_would_cross_reserve"
        safe_batches = max(0, (remaining - PROVIDER_CREDIT_RESERVE_FLOOR) // ceiling)
        label = "下一批会破保底"
        action = "暂停 API，小批量补齐改走人工/OpticOdds。"
    elif recommended_batch_size <= 0 or ceiling <= 0:
        status = "no_api_batch_recommended"
        safe_batches = 0
        label = "无 API 批次"
        action = "按人工工作台或新 provider 数据推进。"
    else:
        status = "credit_safe"
        safe_batches = max(0, (remaining - PROVIDER_CREDIT_RESERVE_FLOOR) // ceiling)
        label = "Credit 安全"
        action = "可按推荐 batch 小批量执行，之后复核 KPI。"
    return {
        "status": status,
        "label": label,
        "reserve_floor": PROVIDER_CREDIT_RESERVE_FLOOR,
        "reported_remaining": remaining,
        "estimated_credit_floor": floor,
        "estimated_credit_ceiling": ceiling,
        "remaining_after_next_batch_floor": remaining_after_floor,
        "remaining_after_next_batch_ceiling": remaining_after_ceiling,
        "safe_next_batch_count_before_reserve": safe_batches,
        "recommended_action": action,
    }


def effective_alternate_plan(provider_kpi: dict[str, Any], provider_alternate_plan: dict[str, Any] | None = None) -> dict[str, Any]:
    if provider_alternate_plan and (
        provider_alternate_plan.get("market_family_gaps")
        or provider_alternate_plan.get("next_probe_queue")
        or provider_alternate_plan.get("event_probe_evidence")
    ):
        return provider_alternate_plan
    summary = provider_kpi.get("summary") or {}
    return provider_kpi.get("alternate_plan") or summary.get("alternate_plan") or provider_alternate_plan or {}


def report_date_label(value: str) -> str:
    if len(value) == 8 and value.isdigit():
        return f"{value[:2]}/{value[2:4]}/{value[4:]}"
    return text(value)


def short_date(value: Any) -> str:
    raw = str(value or "")
    if len(raw) >= 10:
        return raw[:10]
    return text(raw)


def esc(value: Any) -> str:
    return html.escape(text(value), quote=True)


def attr(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def relative_link(path: Path) -> str:
    return html.escape(os.path.relpath(path, ENTRY_HTML.parent), quote=True)


def read_csv_dict_rows(path: Path, *, max_rows: int = 500) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for index, row in enumerate(reader):
            if index >= max_rows:
                break
            rows.append({str(key or ""): str(value or "").strip() for key, value in (row or {}).items()})
        return rows


def csv_manual_direction(row: dict[str, str]) -> str:
    text_value = " ".join(
        [
            str(row.get("direction_hint") or ""),
            str(row.get("entry_slot") or ""),
            str(row.get("selection_name") or ""),
        ]
    ).lower()
    if "over" in text_value:
        return "Over"
    if "under" in text_value:
        return "Under"
    return ""


def first_csv_value(*values: Any) -> str:
    for value in values:
        text_value = text(value, "").strip()
        if text_value:
            return text_value
    return ""


def team_total_manual_entry_rows() -> list[dict[str, str]]:
    template_rows = read_csv_dict_rows(OUTPUT_DIR / PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST, max_rows=160)
    import_rows = read_csv_dict_rows(OUTPUT_DIR / DEFAULT_IMPORT_RELATIVE_PATH, max_rows=160)
    existing: dict[str, dict[str, dict[str, str]]] = {}
    for row in import_rows:
        event_id = text(row.get("event_id"), "").strip()
        direction = csv_manual_direction(row)
        if event_id and direction:
            existing.setdefault(event_id, {})[direction] = row
    grouped: dict[str, dict[str, Any]] = {}
    for row in template_rows:
        event_id = text(row.get("event_id"), "").strip()
        if not event_id:
            continue
        group = grouped.setdefault(
            event_id,
            {
                "event_id": event_id,
                "rank": row.get("rank", ""),
                "match": row.get("match", ""),
                "commence_time": row.get("commence_time", ""),
                "priority_tier": row.get("priority_tier", ""),
                "missing_market": row.get("missing_market", "Team Total Goals Over/Under"),
            },
        )
        group[csv_manual_direction(row)] = row
    entries = []
    for event_id, group in grouped.items():
        over = existing.get(event_id, {}).get("Over", {})
        under = existing.get(event_id, {}).get("Under", {})
        entries.append(
            {
                "event_id": event_id,
                "rank": group.get("rank", ""),
                "match": group.get("match", ""),
                "commence_time": group.get("commence_time", ""),
                "priority_tier": group.get("priority_tier", ""),
                "missing_market": group.get("missing_market", "Team Total Goals Over/Under"),
                "tab_match_name": first_csv_value(over.get("tab_match_name"), under.get("tab_match_name"), group.get("match")),
                "team_scope": first_csv_value(over.get("team_scope"), under.get("team_scope")),
                "tab_market_name": first_csv_value(over.get("tab_market_name"), under.get("tab_market_name"), "Team Total Goals"),
                "line": first_csv_value(over.get("line"), under.get("line")),
                "over_decimal_odds": first_csv_value(over.get("decimal_odds")),
                "under_decimal_odds": first_csv_value(under.get("decimal_odds")),
                "observed_at_aest": first_csv_value(over.get("observed_at_aest"), under.get("observed_at_aest")),
                "operator_initials": first_csv_value(over.get("operator_initials"), under.get("operator_initials")),
                "evidence_note_or_screenshot_ref": first_csv_value(
                    over.get("evidence_note_or_screenshot_ref"),
                    under.get("evidence_note_or_screenshot_ref"),
                ),
                "verification_status": first_csv_value(over.get("verification_status"), under.get("verification_status"), "pending"),
            }
        )
    return entries


def copy_public_assets() -> list[dict[str, str]]:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for source_name, target_name in ASSET_COPIES.items():
        source = OUTPUT_DIR / source_name
        if not source.exists():
            continue
        target = ASSETS_DIR / target_name
        if source.suffix == ".sqlite3":
            copy_sqlite_database(source, target)
        else:
            shutil.copy2(source, target)
        copied.append({"source": source_name, "target": target_name})
    for source in sorted(OUTPUT_DIR.glob("*_partial_daily_research.*")):
        if source.name.startswith("partial_daily_research_"):
            continue
        target = ASSETS_DIR / source.name
        shutil.copy2(source, target)
        copied.append({"source": source.name, "target": source.name})
    research_only_dir = OUTPUT_DIR / "research_only_raw"
    if research_only_dir.exists():
        target_dir = ASSETS_DIR / "research_only_raw"
        target_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(research_only_dir.glob("*.json")):
            target = target_dir / source.name
            shutil.copy2(source, target)
            copied.append({"source": f"research_only_raw/{source.name}", "target": f"research_only_raw/{source.name}"})
    return copied


def copy_sqlite_database(source: Path, target: Path) -> None:
    if target.exists():
        target.unlink()
    source_conn = sqlite3.connect(source)
    try:
        target_conn = sqlite3.connect(target)
        try:
            source_conn.backup(target_conn)
            target_conn.commit()
        finally:
            target_conn.close()
    finally:
        source_conn.close()
    shutil.copystat(source, target)


def latest_pdf_path(latest_commit: dict[str, Any]) -> Path | None:
    report_date = latest_commit.get("report_date")
    if report_date:
        pdf_path = REPORT_DIR / f"{report_date}.pdf"
        if pdf_path.exists():
            return pdf_path
    return None


def latest_attempt_pdf_qa() -> dict[str, Any]:
    qa_files = sorted(OUTPUT_DIR.glob("pdf_qa_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    return load_json(qa_files[0]) if qa_files else {}


def blocker_summary(readiness: dict[str, Any]) -> list[str]:
    reasons = []
    if readiness.get("formal_report_publish_ready") is False:
        reasons.append("当前 attempted run 未通过发布门禁，继续保留上一个可信成功报告。")
    bootstrap = readiness.get("private_position_bootstrap") or {}
    if bootstrap.get("ready") is False:
        reasons.append("当日私有持仓快照未就绪，暂不能更新真实持仓金额和累计收益率。")
    if readiness.get("recurring_automation_ready") is False:
        reasons.append("Recurring automation 尚未安装，当前只允许手动触发报告与检查。")
    if not reasons:
        reasons = [text(reason) for reason in (readiness.get("blocking_reasons") or [])]
    return reasons[:3]


def raw_refresh_ready(raw_health: dict[str, Any], readiness: dict[str, Any]) -> bool:
    readiness_raw = readiness.get("raw_refresh") or {}
    if raw_health:
        return raw_health.get("ready") is True
    return readiness_raw.get("ready") is True


def recommendation_execution_allowed(readiness: dict[str, Any], raw_health: dict[str, Any]) -> bool:
    return readiness.get("formal_report_publish_ready") is True and raw_refresh_ready(raw_health, readiness)


def execution_gate_message(readiness: dict[str, Any], raw_health: dict[str, Any]) -> str:
    raw = raw_health or (readiness.get("raw_refresh") or {})
    blockers = raw.get("blocker_codes") or []
    if not raw_refresh_ready(raw_health, readiness):
        detail = f"阻塞类型：{'、'.join(str(item) for item in blockers[:3])}。" if blockers else ""
        return f"公开盘口 raw 未就绪，暂停执行新增下注；TAB 拒绝 AI controlled access 时需接入授权数据源或导入用户导出快照，再重跑日报门禁。{detail}"
    if readiness.get("formal_report_publish_ready") is not True:
        return "当前日报发布门禁未通过，暂停执行新增下注；保留研究候选，等待持仓和日报门禁恢复。"
    return "公开盘口和日报门禁已通过，可按执行清单逐项复核 TAB 实时赔率。"


def apply_execution_gate(
    rows: list[dict[str, Any]],
    *,
    execution_allowed: bool,
    gate_message: str,
) -> list[dict[str, Any]]:
    if execution_allowed:
        return rows
    gated = []
    for item in rows:
        next_item = dict(item)
        next_item["original_action"] = item.get("action")
        next_item["original_action_class"] = item.get("action_class")
        next_item["action"] = "暂停执行"
        next_item["action_class"] = "blocked"
        next_item["value_label"] = "需刷新复核"
        next_item["reason"] = (
            f"{gate_message} 本行仅保留为研究候选，不作为当前可执行下注。"
            f"原研究动作：{text(item.get('action'))}，原研究金额：{money(item.get('stake_aud'))}。"
            f" {text(item.get('reason'), '')}"
        ).strip()
        gated.append(next_item)
    return gated


def decision_strip_html(
    rows: list[dict[str, Any]],
    *,
    execution_allowed: bool,
    gate_message: str,
    latest_commit: dict[str, Any],
    timeline: dict[str, Any],
) -> str:
    first = rows[0] if rows else {}
    research_total = sum(float(item.get("stake_aud") or 0) for item in rows)
    executable_total = research_total if execution_allowed else 0.0
    buy_count = len([item for item in rows if item.get("action_class") == "buy"])
    candidate_count = len(rows)
    summary = timeline.get("summary") or {}
    if execution_allowed and buy_count:
        next_action = "按推荐逐项复核后执行"
        next_detail = "先核对 TAB 实时赔率是否仍高于报告赔率，再按金额执行。"
        class_name = "buy"
    elif candidate_count:
        next_action = "暂不新增下注"
        next_detail = "当前只保留研究候选，公开盘口和日报门禁恢复前金额为 0。"
        class_name = "blocked"
    else:
        next_action = "等待新日报"
        next_detail = "暂无可用推荐，先刷新盘口并重跑日报。"
        class_name = "watch"
    if first:
        first_pick = f"{text(first.get('selection'))} · {text(first.get('event'))}"
        first_market = f"{text(first.get('market'))} / 赔率 {float(first.get('odds')):.2f}" if first.get("odds") is not None else text(first.get("market"))
        first_ev = pct(first.get("expected_value"))
        first_confidence = text(first.get("confidence"))
    else:
        first_pick = "待新报告生成"
        first_market = "无盘口"
        first_ev = "待校准"
        first_confidence = "待校准"
    cadence_text = (
        f"缺分析 {summary.get('missing_analysis_day_count', 0)} 日 / 缺日报 {summary.get('missing_report_day_count', 0)} 日"
        if summary
        else "待主动测试"
    )
    gate_copy = "可执行" if execution_allowed else gate_message
    return f"""
    <section class="decision-strip {esc(class_name)}" aria-label="推荐下注决策条">
      <div class="decision-main">
        <span class="eyebrow">先看这里</span>
        <h2>推荐下注决策条</h2>
        <p>{esc(next_action)}。{esc(next_detail)}</p>
      </div>
      <div class="decision-grid">
        <div>
          <span>下一步</span>
          <strong>{esc(next_action)}</strong>
          <small>{esc(gate_copy)}</small>
        </div>
        <div>
          <span>首选盘口</span>
          <strong>{esc(first_pick)}</strong>
          <small>{esc(first_market)} / EV {esc(first_ev)} / {esc(first_confidence)}置信度</small>
        </div>
        <div>
          <span>金额</span>
          <strong>{money(executable_total)}</strong>
          <small>研究候选合计 {money(research_total)}；可信报告 {esc(report_date_label(text(latest_commit.get("report_date"))))}</small>
        </div>
        <div>
          <span>自动检测</span>
          <strong>{esc(cadence_text)}</strong>
          <small>规则：每天至少 4 次分析，并生成 1 份日报。</small>
        </div>
      </div>
    </section>
    """


def user_operation_panel_html(
    rows: list[dict[str, Any]],
    *,
    execution_allowed: bool,
    gate_message: str,
    latest_commit: dict[str, Any],
    raw_health: dict[str, Any],
    automation_scorecard: dict[str, Any],
    automation_work_queue: dict[str, Any],
    provider_kpi: dict[str, Any],
    provider_alternate_plan: dict[str, Any],
    position_monitor: dict[str, Any],
    timeline: dict[str, Any],
) -> str:
    first = rows[0] if rows else {}
    work_summary = automation_work_queue.get("summary") or {}
    tasks = automation_work_queue.get("tasks") or []
    next_task = tasks[0] if tasks else {}
    next_task_id = str(next_task.get("id") or "")
    current_stake = float(automation_scorecard.get("current_executable_new_stake_aud") or 0)
    can_execute = execution_allowed and current_stake > 0 and bool(automation_scorecard.get("can_enter_daily_automation"))
    if next_task_id.startswith("TT-"):
        primary_href = "#team-total-manual-entry"
        primary_label = "填写 TT-001"
    elif next_task_id.startswith("MY-BETS"):
        primary_href = "#position-monitor"
        primary_label = "同步只读持仓"
    elif next_task_id.startswith("CREDIT") or next_task_id.startswith("OPTICODDS"):
        primary_href = "#provider-command-console"
        primary_label = "看采集控制台"
    elif next_task_id:
        primary_href = "#automation-work-queue"
        primary_label = "处理工作队列"
    else:
        primary_href = "#active-test"
        primary_label = "运行最终验证"
    provider_summary = provider_kpi.get("summary") or {}
    provider_credit = provider_summary.get("credit") or {}
    provider_executive = provider_kpi.get("executive_status") or {}
    raw_partial = normalize_partial_research_refresh(raw_health.get("partial_research_refresh") or {})
    timeline_summary = timeline.get("summary") or {}
    report_label = report_date_label(text(latest_commit.get("report_date")))
    headline = "可进入人工复核执行" if can_execute else "当前不要新增下注"
    subheadline = (
        "所有 gate 已通过，仍需人工复核 TAB 实时赔率后再执行。"
        if can_execute
        else "首页保留研究候选，但新增执行金额保持 AUD 0。先处理下方最短路径，再重跑主动测试。"
    )
    top_candidate = "暂无候选"
    if first:
        top_candidate = " / ".join(
            item
            for item in [
                text(first.get("event"), ""),
                text(first.get("market"), ""),
                text(first.get("selection"), ""),
            ]
            if item
        )
    status_cards = [
        ("下注状态", "可人工复核执行" if can_execute else "暂停新增下注", f"新增可执行金额 {money(current_stake)}", "ok" if can_execute else "blocked"),
        (
            "首选候选",
            top_candidate,
            f"赔率 {decimal(first.get('odds')) if first else '待校准'} / EV {pct(first.get('expected_value')) if first else '待校准'}",
            "watch" if first else "blocked",
        ),
        (
            "Automation",
            pct(automation_scorecard.get("automation_progress_pct"), 2),
            f"{automation_scorecard.get('passed_gate_count', 0)}/{automation_scorecard.get('gate_count', 0)} gates；P0 {automation_scorecard.get('p0_count', 0)}",
            "ok" if automation_scorecard.get("can_enter_daily_automation") else "watch",
        ),
        (
            "数据新鲜度",
            raw_partial.get("freshness_status") or raw_health.get("status") or "missing",
            f"Raw {raw_health.get('status', 'missing')}；报告 {report_label}",
            "ok" if raw_health.get("ready") else "blocked",
        ),
        (
            "盘口覆盖",
            provider_executive.get("status") or provider_alternate_plan.get("status") or "missing",
            f"Events {provider_summary.get('event_count', 0)}；Credit {provider_credit.get('reported_remaining', '待同步')}",
            "watch",
        ),
        (
            "只读持仓",
            "已同步" if (position_monitor.get("summary") or {}).get("snapshot_ready") else "待同步",
            text((position_monitor.get("summary") or {}).get("preflight_blocking_reason"), "用于同步已下注、余额和累计收益率。"),
            "ok" if (position_monitor.get("summary") or {}).get("snapshot_ready") else "blocked",
        ),
    ]
    card_html = "".join(
        f"""
        <div class="operation-card {esc(status)}">
          <span>{esc(label)}</span>
          <strong>{esc(value)}</strong>
          <small>{esc(detail)}</small>
        </div>
        """
        for label, value, detail, status in status_cards
    )
    steps = [
        ("1", "看推荐", "#recommendations", "只读查看候选，不代表可执行。", "ok" if first else "watch"),
        ("2", primary_label, primary_href, text(next_task.get("title"), automation_scorecard.get("next_gate_title", "")), "blocked" if not can_execute else "ok"),
        (
            "3",
            "主动测试",
            "#active-test",
            f"缺分析 {timeline_summary.get('missing_analysis_day_count', 0)} 日 / 缺日报 {timeline_summary.get('missing_report_day_count', 0)} 日",
            "watch",
        ),
        ("4", "最后执行", "#execution-list", "所有 gate 通过前金额保持 0。", "ok" if can_execute else "blocked"),
    ]
    step_html = "".join(
        f"""
        <a class="operation-step {esc(status)}" href="{esc(href)}">
          <b>{esc(number)}</b>
          <span>{esc(label)}</span>
          <small>{esc(detail)}</small>
        </a>
        """
        for number, label, href, detail, status in steps
    )
    blockers = [
        row
        for row in (automation_scorecard.get("gate_rows") or [])
        if not row.get("done")
    ][:4]
    blocker_html = "".join(
        f"<li><strong>{esc(item.get('title'))}</strong><span>{esc(item.get('next_action'))}</span></li>"
        for item in blockers
    )
    return f"""
    <section class="operation-panel" id="operation-panel" aria-label="操作总览">
      <div class="operation-hero">
        <div>
          <span class="eyebrow">首页操作总览</span>
          <h2 id="operationHeadline">{esc(headline)}</h2>
          <p id="operationSubheadline">{esc(subheadline)}</p>
          <div class="operation-actions">
            <a class="action primary" id="operationPrimaryAction" href="{esc(primary_href)}">{esc(primary_label)}</a>
            <a class="action secondary" href="#active-test">主动测试与自动补缺</a>
            <a class="action secondary" href="#recommendations">查看推荐下注</a>
          </div>
        </div>
        <div class="operation-next">
          <span>下一步最短路径</span>
          <strong id="operationNextTitle">{esc(next_task.get('title') or automation_scorecard.get('next_gate_title') or '等待最终验证')}</strong>
          <small id="operationNextDetail">{esc(next_task.get('action') or automation_scorecard.get('next_safe_action') or gate_message)}</small>
        </div>
      </div>
      <div class="operation-grid">{card_html}</div>
      <div class="operation-flow">{step_html}</div>
      <div class="operation-blockers">
        <span>当前关键阻塞</span>
        <ul>{blocker_html or '<li><strong>无阻塞</strong><span>可进入最终 readiness 验证。</span></li>'}</ul>
      </div>
      <p class="note">边界：此面板只读展示状态和跳转，不触发 provider refresh、TAB 点击、Bet Slip 修改或自动下注。更新时间以本地网页状态 API 和最新 artifacts 为准。</p>
    </section>
    """


def html_status_class(value: Any) -> str:
    if value is True or value in {"ready", "verified", "ready_for_manual_report", "ok", "passed"}:
        return "ok"
    if value in {
        "current_run_preflight_blocked",
        "blocked_by_gate",
        "blocked",
        False,
        "failed",
        "manual_required",
        "login_required",
        "not_ready",
        "paused",
        "credit_or_yield_blocked",
        "provider_access_required",
        "blocked_until_manual_signature",
    }:
        return "blocked"
    return "watch"


def strategy_status_label(value: Any) -> str:
    return {
        "research_only": "仅研究诊断",
        "full_scope_ready": "完整范围可用",
        "blocked": "阻塞",
    }.get(str(value or ""), text(value))


def match_time_index() -> dict[str, str]:
    payload = load_json(OUTPUT_DIR / "tab_fifa_matches_main_markets_raw_v0_9.json")
    index: dict[str, str] = {}
    pattern = re.compile(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}\s+[A-Z][a-z]{2}\s+\d{1,2}:\d{2}\b")
    for item in payload.get("matches", []):
        match = str(item.get("match") or "")
        markets = item.get("markets") or {}
        block = "\n".join(str(value) for value in markets.values())
        found = pattern.search(block)
        if match and found:
            index[match] = found.group(0)
    return index


def recommendation_rows(latest_commit: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    run_id = str(latest_commit.get("run_id") or "")
    db_path = OUTPUT_DIR / "tab_fifa_reports.sqlite3"
    if not run_id or not db_path.exists():
        return []
    uri = f"file:{db_path.resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT board_name, rank, event_name, market, selection, odds,
                   board_id, probability, expected_value, stake_aud, action, raw_json
            FROM recommendations
            WHERE run_id = ?
            ORDER BY
              CASE WHEN action = 'buy' THEN 0 ELSE 1 END,
              stake_aud DESC,
              COALESCE(expected_value, -999) DESC,
              rank ASC
            LIMIT ?
            """,
            (run_id, max(limit * 4, limit)),
        ).fetchall()
    finally:
        conn.close()
    time_index = match_time_index()
    bankroll_reference = bankroll_reference_aud(OUTPUT_DIR, latest_commit)
    scope_index = board_scope_index(load_json(OUTPUT_DIR / "available_board_strategy_latest.json"))
    model_index = model_calibration_index(OUTPUT_DIR)
    normalized = []
    for row in rows:
        raw = parse_raw_json(row["raw_json"])
        probability = row["probability"]
        odds = row["odds"]
        breakeven = (1 / float(odds)) if odds else None
        edge = raw.get("edge")
        if edge is None and probability is not None and breakeven is not None:
            edge = float(probability) - breakeven
        stake = float(row["stake_aud"] or 0)
        risk_flags = int((raw.get("event_risk") or {}).get("flag_count") or 0)
        arbitrage_rate = value_arbitrage_rate(row["expected_value"], probability, odds)
        risk_of_ruin = risk_of_ruin_estimate(probability, odds, stake, bankroll_reference, risk_flags=risk_flags)
        threshold = market_edge_threshold(row["market"])
        threshold_gap = edge_threshold_gap(edge, threshold)
        half_kelly = discounted_kelly_fraction(probability, odds)
        stake_fraction = stake_fraction_of_bankroll(stake, bankroll_reference)
        half_kelly_ratio = over_half_kelly_ratio(stake_fraction, half_kelly)
        risk_grade = risk_of_ruin_grade(risk_of_ruin)
        expected_profit = expected_profit_aud(stake, row["expected_value"])
        expected_profit_100 = expected_profit_per_100_aud(row["expected_value"])
        min_acceptable_odds = minimum_acceptable_odds(probability, threshold)
        current_odds_buffer = odds_buffer(odds, min_acceptable_odds)
        current_price_tolerance = price_drift_tolerance_pct(current_odds_buffer, odds)
        stake_cap_ratio = stake_to_cap_ratio(stake_fraction)
        kelly_margin = kelly_safety_margin(half_kelly_ratio)
        value_score = risk_adjusted_value_score(row["expected_value"], threshold_gap, risk_of_ruin)
        value_signal = value_signal_label(row["expected_value"], threshold_gap, current_odds_buffer, risk_of_ruin)
        drivers = risk_drivers(
            edge=edge,
            edge_threshold_gap=threshold_gap,
            risk_of_ruin=risk_of_ruin,
            stake_fraction=stake_fraction,
            half_kelly_ratio=half_kelly_ratio,
            risk_flags=risk_flags,
        )
        diagnostic = decision_diagnostics(
            probability=probability,
            odds=odds,
            edge=edge,
            edge_threshold=threshold,
            edge_threshold_gap=threshold_gap,
            expected_value=row["expected_value"],
            stake_aud=stake,
            expected_profit=expected_profit,
            expected_profit_100=expected_profit_100,
            min_acceptable_odds=min_acceptable_odds,
            current_odds_buffer=current_odds_buffer,
            price_tolerance=current_price_tolerance,
            risk_of_ruin=risk_of_ruin,
            risk_grade=risk_grade,
            stake_fraction=stake_fraction,
            half_kelly_ratio=half_kelly_ratio,
            stake_cap_ratio=stake_cap_ratio,
            kelly_margin=kelly_margin,
            value_score=value_score,
            value_signal=value_signal,
            risk_drivers=drivers,
        )
        metric_pack = decision_metric_pack(
            probability=probability,
            breakeven=breakeven,
            edge=edge,
            edge_threshold=threshold,
            edge_threshold_gap=threshold_gap,
            arbitrage_rate=arbitrage_rate,
            expected_value=row["expected_value"],
            risk_of_ruin=risk_of_ruin,
            risk_grade=risk_grade,
            diagnostic=diagnostic,
            risk_drivers=drivers,
        )
        model_calibration = model_calibration_for_recommendation(
            event=row["event_name"],
            market=row["market"],
            selection=row["selection"],
            probability=probability,
            model_index=model_index,
        )
        analysis_basis = row_analysis_basis(
            row=row,
            raw=raw,
            breakeven=breakeven,
            edge=edge,
            edge_threshold=threshold,
            edge_threshold_gap=threshold_gap,
            arbitrage_rate=arbitrage_rate,
            risk_of_ruin=risk_of_ruin,
            risk_grade=risk_grade,
            risk_drivers=drivers,
            diagnostic=diagnostic,
            bankroll_reference=bankroll_reference,
            model_calibration=model_calibration,
        )
        funding_profile = market_funding_profile(
            board=row["board_name"],
            market=row["market"],
            selection=row["selection"],
            odds=odds,
            probability=probability,
            expected_value=row["expected_value"],
            edge=edge,
            arbitrage_rate=arbitrage_rate,
            price_drift_tolerance=current_price_tolerance,
            stake_aud=stake,
            stake_fraction=stake_fraction,
            risk_of_ruin=risk_of_ruin,
            risk_flags=risk_flags,
        )
        item = {
                "time": time_index.get(str(row["event_name"]), "长期/待赛程"),
                "board_id": row["board_id"],
                "board": row["board_name"],
                "event": row["event_name"],
                "market": row["market"],
                "selection": row["selection"],
                "odds": odds,
                "probability": probability,
                "breakeven": breakeven,
                "edge": edge,
                "edge_pp": edge,
                "edge_threshold": threshold,
                "edge_threshold_range": market_edge_threshold_range(row["market"]),
                "edge_threshold_gap": threshold_gap,
                "edge_quality": edge_quality_label(edge, threshold),
                "expected_value": row["expected_value"],
                "arbitrage_rate": arbitrage_rate,
                "minimum_acceptable_odds": min_acceptable_odds,
                "odds_buffer": current_odds_buffer,
                "expected_profit_aud": expected_profit,
                "expected_profit_per_100_aud": expected_profit_100,
                "price_drift_tolerance_pct": current_price_tolerance,
                "full_kelly_fraction": full_kelly_fraction(probability, odds),
                "discounted_kelly_fraction": half_kelly,
                "risk_of_ruin": risk_of_ruin,
                "risk_of_ruin_grade": risk_grade,
                "stake_fraction": stake_fraction,
                "stake_to_cap_ratio": stake_cap_ratio,
                "half_kelly_ratio": half_kelly_ratio,
                "kelly_safety_margin": kelly_margin,
                "risk_adjusted_value_score": value_score,
                "value_signal": value_signal,
                "bankroll_reference_aud": bankroll_reference,
                "risk_flags": risk_flags,
                "risk_drivers": drivers,
                "decision_metric_pack": metric_pack,
                "decision_diagnostics": diagnostic,
                "analysis_basis": analysis_basis,
                "model_calibration": model_calibration,
                "market_funding": funding_profile,
                "stake_aud": stake,
                "action": action_label(row["action"], stake),
                "action_class": "buy" if stake > 0 else "watch",
                "consistency": model_calibration.get("consistency_label") or consistency_label(raw),
                "value_label": value_label(row["expected_value"], edge, stake),
                "confidence": model_calibration.get("confidence_zh") or confidence_label(raw),
                "reason": chinese_reason(
                    row,
                    raw,
                    breakeven,
                    edge,
                    arbitrage_rate,
                    risk_of_ruin,
                    bankroll_reference,
                    edge_threshold=threshold,
                    edge_threshold_gap=threshold_gap,
                    risk_grade=risk_grade,
                    risk_drivers=drivers,
                    decision_diagnostic=diagnostic,
                    model_calibration=model_calibration,
                )
                + market_funding_reason(funding_profile),
            }
        item = annotate_live_board_scope(item, scope_index)
        if live_board_scope_allowed(item):
            normalized.append(item)
        if len(normalized) >= limit:
            break
    return normalized


def parse_raw_json(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def action_label(action: str, stake: Any) -> str:
    try:
        if float(stake or 0) > 0:
            return "买入"
    except (TypeError, ValueError):
        pass
    if action == "watch_or_no_bet":
        return "观察/不下注"
    return text(action)


def consistency_label(raw: dict[str, Any]) -> str:
    signal = raw.get("model_signal") or {}
    if not signal:
        return "待模型校准"
    if signal.get("high_divergence"):
        return "模型分歧高"
    if signal.get("selection_aligned_with_consensus"):
        return "三模型一致"
    return "部分一致"


def confidence_label(raw: dict[str, Any]) -> str:
    signal = raw.get("model_signal") or {}
    value = str(signal.get("consensus_confidence") or "")
    mapping = {"high": "高", "medium": "中", "low": "低"}
    return mapping.get(value.lower(), "待校准")


def value_label(expected_value: Any, edge: Any, stake: Any) -> str:
    try:
        ev = float(expected_value)
    except (TypeError, ValueError):
        ev = None
    try:
        stake_value = float(stake or 0)
    except (TypeError, ValueError):
        stake_value = 0
    if stake_value <= 0:
        return "观察价值"
    if ev is not None and ev >= 0.15:
        return "高价值"
    if ev is not None and ev >= 0.05:
        return "中高价值"
    try:
        if float(edge) > 0:
            return "小正边际"
    except (TypeError, ValueError):
        pass
    return "待复核"


def ev_status_class(expected_value: Any) -> str:
    try:
        value = float(expected_value)
    except (TypeError, ValueError):
        return "watch-ev"
    if value > 0:
        return "positive-ev"
    if value < 0:
        return "negative-ev"
    return "watch-ev"


def chinese_reason(
    row: sqlite3.Row,
    raw: dict[str, Any],
    breakeven: float | None,
    edge: Any,
    arbitrage_rate: Any,
    risk_of_ruin: Any,
    bankroll_reference: float,
    *,
    edge_threshold: Any = None,
    edge_threshold_gap: Any = None,
    risk_grade: str = "",
    risk_drivers: list[str] | None = None,
    decision_diagnostic: dict[str, Any] | None = None,
    model_calibration: dict[str, Any] | None = None,
) -> str:
    probability = row["probability"]
    odds = row["odds"]
    ev = row["expected_value"]
    stake = float(row["stake_aud"] or 0)
    if probability is not None and breakeven is not None and ev is not None:
        base = (
            f"模型概率 {pct(probability)} 高于赔率盈亏平衡 {pct(breakeven)}，"
            f"Edge {pp(edge)}，套利率 {pct(arbitrage_rate)}，EV {pct(ev)}。"
        )
    elif probability is not None and odds is not None:
        base = f"当前概率 {pct(probability)}，TAB 赔率 {float(odds):.2f}，仍需补充独立模型 EV 校准。"
    else:
        base = "当前只进入观察池，缺少足够独立概率和 EV 证据。"
    if stake > 0:
        base += f" 建议执行金额 {money(stake)}，属于小仓分散下注。"
    else:
        base += " 当前不建议投入真实金额。"
    if edge_threshold is not None and edge_threshold_gap is not None:
        base += f" Edge门槛 {pp(edge_threshold)}，门槛差 {pp(edge_threshold_gap)}，纪律等级：{edge_quality_label(edge, edge_threshold)}。"
    base += f" Risk of ruin 估计 {pct(risk_of_ruin)}（{risk_grade or risk_of_ruin_grade(risk_of_ruin)}），按平衡口径资金池 {money(bankroll_reference)}、单注比例和半Kelly偏离计算。"
    if risk_drivers:
        base += f" 主要风险触发：{'；'.join(str(item) for item in risk_drivers)}。"
    diagnostic = decision_diagnostic or {}
    if diagnostic:
        base += (
            f" 赔率执行底线：最低可接受赔率 {decimal(diagnostic.get('minimum_acceptable_odds'))}，"
            f"当前赔率缓冲 {decimal_signed(diagnostic.get('odds_buffer'))}，"
            f"价格容忍度 {pct(diagnostic.get('price_drift_tolerance_pct'))}；"
            f"预计收益 {money(diagnostic.get('expected_profit_aud'))}，每 AUD100 预期 {money(diagnostic.get('expected_profit_per_100_aud'))}。"
            f" 仓位纪律：{diagnostic.get('stake_discipline_status', '待校准')}；"
            f"RoR复核：{diagnostic.get('ror_status', '待校准')}；"
            f"价值信号：{diagnostic.get('value_signal', '待校准')}；"
            f"仓位上限占用 {pct(diagnostic.get('stake_to_cap_ratio'))}，Kelly安全垫 {pct(diagnostic.get('kelly_safety_margin'))}。"
        )
    base += " 判断依据覆盖赔率去水、EV/Edge/Kelly、Poisson/xG、开源模型交叉验证、赛前10分钟清单和CLV/ROI复盘。"
    if model_calibration:
        base += (
            f" 模型校准：{model_calibration.get('consistency_label', '待模型校准')}，"
            f"{model_calibration.get('evidence_text', '')}"
            f" 复核动作：{model_calibration.get('review_action', '待复核')}。"
        )
    if (raw.get("event_risk") or {}).get("flag_count"):
        base += " 赛前需复核伤停、阵容和新闻事件。"
    return base


def recommendations_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<div class="empty">暂无可展示的推荐下注数据，请先运行日报。</div>'
    body = []
    for idx, item in enumerate(rows):
        probability_pct = "" if item["probability"] is None else f"{float(item['probability']) * 100:.2f}"
        odds_value = "" if item["odds"] is None else f"{float(item['odds']):.2f}"
        ev_value = "" if item["expected_value"] is None else f"{float(item['expected_value']) * 100:.2f}%"
        probability_value = pct(item.get("probability"))
        breakeven_value = pct(item.get("breakeven"))
        edge_value = pp(item.get("edge"))
        edge_threshold_value = pp(item.get("edge_threshold"))
        edge_gap_value = pp(item.get("edge_threshold_gap"))
        edge_quality = text(item.get("edge_quality"), "待校准")
        arbitrage_value = pct(item.get("arbitrage_rate"))
        ruin_value = pct(item.get("risk_of_ruin"))
        risk_grade = text(item.get("risk_of_ruin_grade"), "待校准")
        half_kelly_value = pct(item.get("discounted_kelly_fraction"))
        stake_fraction_value = pct(item.get("stake_fraction"))
        risk_driver_text = "；".join(str(driver) for driver in (item.get("risk_drivers") or [])) or "无明显额外触发因素"
        diagnostic = item.get("decision_diagnostics") or {}
        min_odds_value = decimal(diagnostic.get("minimum_acceptable_odds"))
        odds_buffer_value = decimal_signed(diagnostic.get("odds_buffer"))
        price_tolerance_value = pct(diagnostic.get("price_drift_tolerance_pct"))
        profit_100_value = money(diagnostic.get("expected_profit_per_100_aud"))
        expected_profit_value = money(diagnostic.get("expected_profit_aud"))
        cap_usage_value = pct(diagnostic.get("stake_to_cap_ratio"))
        kelly_margin_value = pct(diagnostic.get("kelly_safety_margin"))
        risk_adjusted_value = pct(diagnostic.get("risk_adjusted_value_score"))
        value_signal = text(diagnostic.get("value_signal"), "待校准")
        stake_status = text(diagnostic.get("stake_discipline_status"), "待校准")
        ror_status = text(diagnostic.get("ror_status"), "待校准")
        diagnostic_conclusion = text(diagnostic.get("conclusion"), "待校准")
        basis = item.get("analysis_basis") or {}
        metric_pack = item.get("decision_metric_pack") or {}
        model_calibration = item.get("model_calibration") or {}
        edge_pack = metric_pack.get("edge") or {}
        arb_pack = metric_pack.get("arbitrage_rate") or {}
        ror_pack = metric_pack.get("risk_of_ruin") or {}
        metric_action = text(metric_pack.get("combined_action"), "三指标解释待生成")
        basis_summary = text(basis.get("summary"), "判断依据待生成")
        basis_strength = text(basis.get("evidence_strength"), "待校准")
        probability_basis = "；".join(str(value) for value in (basis.get("probability_value_basis") or [])[:2]) or "概率价值依据待生成"
        price_basis = "；".join(str(value) for value in (basis.get("price_execution_basis") or [])[:2]) or "价格执行依据待生成"
        risk_basis = "；".join(str(value) for value in (basis.get("risk_control_basis") or [])[:2]) or "风险控制依据待生成"
        data_gaps = "；".join(str(value) for value in (basis.get("data_gaps") or [])[:3]) or "资料缺口待复核"
        pre_bet_checklist = "；".join(str(value) for value in (basis.get("pre_bet_checklist") or [])[:3]) or "赛前复核清单待生成"
        model_consensus = text(model_calibration.get("consensus_selection"), "待校准")
        model_consistency = text(model_calibration.get("consistency_label"), "待模型校准")
        model_review_priority = text(model_calibration.get("review_priority"), "待校准")
        model_review_action = text(model_calibration.get("review_action"), "待复核")
        model_evidence = text(model_calibration.get("evidence_text"), "模型校准待生成")
        funding = item.get("market_funding") or {}
        funding_score = text(funding.get("market_funding_tendency_score"), "待校准")
        funding_grade = text(funding.get("market_funding_tendency_grade"), "待校准")
        funding_bias = text(funding.get("market_funding_bias_label"), "待校准")
        total_funds_proxy = money(funding.get("total_funds_proxy_aud"))
        net_funds_proxy = money(funding.get("net_funds_proxy_aud"))
        turnover_proxy = money(funding.get("turnover_proxy_aud"))
        liquidity_label = f"{pct(funding.get('liquidity_score'))} / {text(funding.get('liquidity_grade'), '待校准')}"
        depth_label = f"{pct(funding.get('market_depth_score'))} / {text(funding.get('market_depth_grade'), '待校准')}"
        float_rate_label = pct(funding.get("daily_line_move_float_rate"))
        ev_class = ev_status_class(item["expected_value"])
        action_class = str(item.get("action_class") or "watch")
        original_action_class = str(item.get("original_action_class") or action_class)
        is_research_buy = action_class == "buy" or original_action_class == "buy"
        action_cell_class = "buy-cell" if is_research_buy else "watch-cell"
        action_hint = (
            '<small class="action-hint buy-hint">原买入</small>'
            if is_research_buy and action_class != "buy"
            else ""
        )
        body.append(
            f"""
            <tr data-rec-row="{idx}">
              <td>{esc(item['time'])}</td>
              <td>{esc(item['board'])}<br><span>{esc(item.get('live_board_scope_label', '当前可研究'))}</span></td>
              <td><strong>{esc(item['event'])}</strong><br><span>{esc(item['market'])}</span></td>
              <td>{esc(item['selection'])}</td>
              <td><strong>{esc(odds_value or '待校准')}</strong></td>
              <td><strong>{money(item['stake_aud'])}</strong></td>
              <td class="{esc(action_cell_class)}" data-original-action="{esc(item.get('original_action') or item.get('action'))}"><span class="pill {esc(action_class)}">{esc(item['action'])}</span>{action_hint}</td>
              <td>{esc(item['consistency'])}</td>
              <td>{esc(item['value_label'])}</td>
              <td class="funding-cell" data-funding-score="{esc(funding.get('market_funding_tendency_score'))}" data-total-funds="{esc(funding.get('total_funds_proxy_aud'))}" data-liquidity="{esc(funding.get('liquidity_score'))}" data-depth="{esc(funding.get('market_depth_score'))}" data-daily-float="{esc(funding.get('daily_line_move_float_rate'))}">
                <strong class="funding-value">{esc(funding_score)}</strong><br><span class="funding-detail">{esc(funding_bias)} / {esc(funding_grade)} · 净 {esc(net_funds_proxy)}</span>
              </td>
              <td class="edge-cell" data-edge="{esc(item.get('edge'))}" data-edge-threshold="{esc(item.get('edge_threshold'))}">
                <strong class="edge-value">{esc(edge_value)}</strong><br><span class="edge-detail">概率 {esc(probability_value)} / 盈亏平衡 {esc(breakeven_value)} / 门槛 {esc(edge_threshold_value)} / 差 {esc(edge_gap_value)} / {esc(edge_quality)}</span>
              </td>
              <td class="arb-cell" data-arb="{esc(item.get('arbitrage_rate'))}">
                <strong class="arb-value">{esc(arbitrage_value)}</strong><br><span class="arb-detail">每AUD100 {esc(profit_100_value)} · 非surebet</span>
              </td>
              <td class="ror-cell" data-risk="{esc(item.get('risk_of_ruin'))}" data-risk-flags="{esc(item.get('risk_flags'))}" data-bankroll="{esc(item.get('bankroll_reference_aud') or DEFAULT_BANKROLL_REFERENCE_AUD)}">
                <strong class="risk-value">{esc(ruin_value)}</strong><br><span class="risk-detail">{esc(risk_grade)} · 半Kelly {esc(half_kelly_value)} / 仓位 {esc(stake_fraction_value)} · 上限占用 {esc(cap_usage_value)} · {esc(risk_driver_text)}</span>
              </td>
              <td class="ev-cell {esc(ev_class)}" data-ev="{esc(item['expected_value'])}" data-stake="{esc(item['stake_aud'])}">{esc(ev_value or '待校准')}</td>
              <td>
                <label>概率 <input class="mini-input prob-input" type="number" min="0" max="100" step="0.1" value="{esc(probability_pct)}"></label>
                <label>赔率 <input class="mini-input odds-input" type="number" min="1.01" step="0.01" value="{esc(odds_value)}"></label>
              </td>
              <td>{esc(item['confidence'])}</td>
              <td><strong>{esc(model_consistency)}</strong><br><span>{esc(model_review_priority)} / {esc(model_review_action)}</span><br><span>共识 {esc(model_consensus)}</span></td>
            </tr>
            <tr class="reason-row">
              <td colspan="17">
                <div class="diagnostic-strip">
                  <span>价值信号 <strong class="diag-value-signal">{esc(value_signal)}</strong></span>
                  <span>最低可接受赔率 <strong class="diag-min-odds">{esc(min_odds_value)}</strong></span>
                  <span>赔率缓冲 <strong class="diag-odds-buffer">{esc(odds_buffer_value)}</strong></span>
                  <span>价格容忍度 <strong class="diag-price-tolerance">{esc(price_tolerance_value)}</strong></span>
                  <span>每AUD100预期 <strong class="diag-profit-100">{esc(profit_100_value)}</strong></span>
                  <span>本注预计收益 <strong class="diag-profit">{esc(expected_profit_value)}</strong></span>
                  <span>上限占用 <strong class="diag-cap-usage">{esc(cap_usage_value)}</strong></span>
                  <span>Kelly安全垫 <strong class="diag-kelly-margin">{esc(kelly_margin_value)}</strong></span>
                  <span>风险调整分 <strong class="diag-value-score">{esc(risk_adjusted_value)}</strong></span>
                  <span>仓位纪律 <strong class="diag-stake-status">{esc(stake_status)}</strong></span>
                  <span>RoR复核 <strong class="diag-ror-status">{esc(ror_status)}</strong></span>
                  <span>结论 <strong class="diag-conclusion">{esc(diagnostic_conclusion)}</strong></span>
                  <span>模型校准 <strong class="diag-model-calibration">{esc(model_consistency)} / {esc(model_review_priority)}</strong></span>
                  <span>市场资金倾向 <strong class="diag-funding-score">{esc(funding_score)} / {esc(funding_bias)}</strong></span>
                </div>
                <div class="analysis-basis-grid">
                  <span>三指标解释 <strong>{esc(metric_action)}</strong></span>
                  <span>Edge解释 <strong>{esc(edge_pack.get('decision_use', 'Edge解释待生成'))}</strong></span>
                  <span>套利率解释 <strong>{esc(arb_pack.get('decision_use', '套利率解释待生成'))}</strong></span>
                  <span>RoR解释 <strong>{esc(ror_pack.get('decision_use', 'Risk of ruin解释待生成'))}</strong></span>
                  <span>判断依据包 <strong>{esc(basis_strength)}</strong><small>{esc(basis_summary)}</small></span>
                  <span>概率价值依据 <strong>{esc(probability_basis)}</strong></span>
                  <span>价格执行依据 <strong>{esc(price_basis)}</strong></span>
                  <span>风险控制依据 <strong>{esc(risk_basis)}</strong></span>
                  <span>市场资金分析 <strong>总资金{esc(total_funds_proxy)} / 净资金{esc(net_funds_proxy)} / 成交量{esc(turnover_proxy)}</strong><small>流动性 {esc(liquidity_label)}；盘口深度 {esc(depth_label)}；日均浮动 {esc(float_rate_label)}</small></span>
                  <span>资料缺口 <strong>{esc(data_gaps)}</strong></span>
                  <span>赛前复核清单 <strong>{esc(pre_bet_checklist)}</strong></span>
                  <span>模型共识校准 <strong>{esc(model_evidence)}</strong></span>
                </div>
                <div class="reason-text">{esc(item['reason'])}</div>
              </td>
            </tr>
            """
        )
    return f"""
      <div class="table-scroll">
        <table class="recommendations">
          <thead>
            <tr>
              <th>时</th><th>板块</th><th>盘口</th><th>下注</th><th>赔率</th><th>金额</th>
              <th>操作</th><th>分析一致性</th><th>盘口价值</th><th>市场资金倾向分</th><th>Edge信息</th><th>套利率</th><th>Risk of ruin</th><th>EV</th><th>概率赔率编辑</th><th>置信度</th><th>模型校准</th>
            </tr>
          </thead>
          <tbody>{''.join(body)}</tbody>
        </table>
      </div>
    """


def recommendation_basis_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    policy = payload.get("calculation_policy") or {}
    summary = payload.get("summary") or {}
    portfolio = summary.get("portfolio_risk") or {}
    discipline = policy.get("risk_discipline") or {}
    source_alignment = payload.get("source_alignment") or {}
    excel_profile = policy.get("excel_reference_profile") or {}
    template_status = text(excel_profile.get("template_read_status"), "static_profile")
    template_sheet_count = excel_profile.get("sheet_count") or policy.get("template_sheet_count") or len(excel_profile.get("sheet_names") or [])
    template_formula_count = int(policy.get("template_formula_count") or excel_profile.get("formula_count_total") or 0)
    template_topics = "、".join(str(item) for item in (excel_profile.get("detected_topics") or [])[:5]) or "赛前检查、EV/Edge、下注日志"
    template_evidence_terms = "、".join(str(item) for item in (policy.get("template_evidence_terms") or [])[:5]) or "No Bet、EV/Edge、Kelly、CLV"
    template_rules = "；".join(str(item) for item in (policy.get("template_decision_rules") or [])[:3]) or "价格走差放弃；Edge不足No Bet；超仓取消。"
    template_material_count = len(policy.get("template_analysis_materials") or [])
    template_digest = text(policy.get("template_evidence_digest"), "Excel模板结构画像已纳入判断依据。")
    forbidden = "、".join(discipline.get("forbidden_behaviors") or ["追损", "加倍", "情绪下注", "无首发重仓", "无记录下注"])
    return f"""
      <div class="basis-panel">
        <div>
          <span>Excel参考</span>
          <strong>{esc(template_status)} · {esc(template_sheet_count)} sheets</strong>
          <small>{esc(template_topics)}</small>
        </div>
        <div>
          <span>模板公式</span>
          <strong>{esc(template_formula_count)} 个可审计公式</strong>
          <small>{esc(template_evidence_terms)}</small>
        </div>
        <div>
          <span>模板证据资料</span>
          <strong>{esc(template_material_count)} 组判断资料</strong>
          <small>No Bet / EV / Kelly / Poisson / CLV</small>
        </div>
        <div>
          <span>Edge 门槛</span>
          <strong>主流 {esc(discipline.get('main_market_edge_threshold', '2%-3%'))} / 小市场 {esc(discipline.get('small_market_edge_threshold', '4%-6%'))}</strong>
        </div>
        <div>
          <span>资金纪律</span>
          <strong>基础 {esc(discipline.get('base_stake_range', '0.5%-1.0% bankroll'))} / 上限 {esc(discipline.get('single_bet_cap', '2.0% bankroll'))}</strong>
        </div>
        <div>
          <span>优先玩法</span>
          <strong>{esc(discipline.get('preferred_market_order', '亚洲让球 / 大小球 > 1X2'))}</strong>
        </div>
        <div>
          <span>复盘口径</span>
          <strong>{esc(discipline.get('review_priority', '先看 CLV，再看 ROI'))}</strong>
        </div>
        <div>
          <span>核心公式</span>
          <strong>EV、Edge、半Kelly、RoR 同屏校验</strong>
        </div>
        <div>
          <span>价格执行</span>
          <strong>最低赔率 / 缓冲 / 容忍度</strong>
        </div>
        <div>
          <span>风险约束</span>
          <strong>上限占用 / Kelly安全垫 / RoR复核</strong>
        </div>
        <div>
          <span>补充模型</span>
          <strong>{esc(source_alignment.get('implemented_reference_count', 0))}/{esc(source_alignment.get('reference_count', 0))} 已吸收</strong>
        </div>
      </div>
      <div class="basis-panel portfolio-panel">
        <div>
          <span>组合RoR</span>
          <strong>{esc(pct(portfolio.get('portfolio_risk_of_ruin'), 2))} / {esc(portfolio.get('portfolio_risk_grade', '待校准'))}</strong>
          <small>{esc(portfolio.get('portfolio_ror_status', '持仓快照未同步'))}</small>
        </div>
        <div>
          <span>组合预计收益</span>
          <strong>{money(portfolio.get('expected_profit_aud'))}</strong>
          <small>每AUD100 {money(portfolio.get('expected_profit_per_100_aud'))}</small>
        </div>
        <div>
          <span>最坏新增亏损</span>
          <strong>{money(portfolio.get('worst_case_new_loss_aud'))}</strong>
          <small>只含本轮研究候选</small>
        </div>
        <div>
          <span>预算压力</span>
          <strong>{esc(pct(portfolio.get('combined_mid_usage_pct'), 2))}</strong>
          <small>下沿余量 {money(portfolio.get('budget_floor_headroom_aud'))}</small>
        </div>
        <div>
          <span>组合动作</span>
          <strong>{esc(portfolio.get('recommended_action', '待校准'))}</strong>
          <small>待同步确认</small>
        </div>
      </div>
      <p class="note">Excel模板证据：{esc(template_digest)}</p>
      <p class="note">模板决策规则：{esc(template_rules)}</p>
      <p class="note">赛前10分钟复核：{esc(discipline.get('late_check_window', '价格、去水、首发、伤停、动机、赛程疲劳、战术匹配和大小球节奏。'))}</p>
      <p class="note">禁止动作：{esc(forbidden)}。</p>
    """


def market_funding_analysis_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    analysis = payload.get("market_funding_analysis") or {}
    summary = analysis.get("summary") or (payload.get("summary") or {}).get("market_funding") or {}
    rows = []
    for item in (analysis.get("rows") or [])[:10]:
        rows.append(
            "<tr>"
            f"<td>{esc(item.get('time'))}</td>"
            f"<td>{esc(item.get('event'))}<br><span>{esc(item.get('market'))}</span></td>"
            f"<td>{esc(item.get('selection'))}</td>"
            f"<td><strong>{esc(item.get('market_funding_tendency_score', '待校准'))}</strong><br><span>{esc(item.get('market_funding_bias_label', '待校准'))} / {esc(item.get('market_funding_tendency_grade', '待校准'))}</span></td>"
            f"<td>{money(item.get('total_funds_proxy_aud'))}</td>"
            f"<td>{money(item.get('net_funds_proxy_aud'))}</td>"
            f"<td>{money(item.get('turnover_proxy_aud'))}</td>"
            f"<td>{esc(pct(item.get('liquidity_score')))}<br><span>{esc(item.get('liquidity_grade'))}</span></td>"
            f"<td>{esc(pct(item.get('market_depth_score')))}<br><span>{esc(item.get('market_depth_grade'))}</span></td>"
            f"<td>{esc(pct(item.get('daily_line_move_float_rate')))}</td>"
            "</tr>"
        )
    return f"""
    <section class="market-funding-panel" id="market-funding" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>市场资金分析</h2>
          <p class="subtitle">把盘口价值、价格缓冲、流动性、盘口深度和风险事件转成资金面代理指标；不声称读取 TAB 官方成交资金。</p>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>平均资金倾向分</span><strong>{esc(summary.get('average_market_funding_tendency_score', 0))}</strong><small>支持 {esc(summary.get('supportive_funding_count', 0))} / 偏弱 {esc(summary.get('weak_funding_count', 0))}</small></div>
        <div class="insight"><span>总资金代理</span><strong>{money(summary.get('total_funds_proxy_aud'))}</strong></div>
        <div class="insight"><span>净资金代理</span><strong>{money(summary.get('net_funds_proxy_aud'))}</strong></div>
        <div class="insight"><span>成交量代理</span><strong>{money(summary.get('turnover_proxy_aud'))}</strong></div>
        <div class="insight"><span>平均流动性</span><strong>{esc(pct(summary.get('average_liquidity_score')))}</strong></div>
        <div class="insight"><span>平均盘口深度</span><strong>{esc(pct(summary.get('average_market_depth_score')))}</strong></div>
        <div class="insight"><span>日均盘口变动浮动率</span><strong>{esc(pct(summary.get('average_daily_line_move_float_rate')))}</strong></div>
        <div class="insight"><span>Top 资金倾向</span><strong>{esc(summary.get('top_funding_selection', '待校准'))}</strong></div>
      </div>
      <p class="note">真实性边界：{esc(summary.get('truthfulness_note', '资金字段为盘口资金代理指标，不是 TAB 官方成交数据。'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>时</th><th>盘口</th><th>下注</th><th>资金倾向分</th><th>总资金</th><th>净资金</th><th>成交量</th><th>流动性</th><th>盘口深度</th><th>日均盘口变动浮动率</th></tr></thead>
          <tbody>{''.join(rows) or '<tr><td colspan="10">暂无市场资金分析数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def probability_engine_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    engine = payload.get("probability_engine") or (payload.get("calculation_policy") or {}).get("probability_engine_framework") or {}
    summary = payload.get("summary") or {}
    if not engine:
        return ""
    module_rows = []
    for item in (engine.get("modules") or [])[:10]:
        module_rows.append(
            "<tr>"
            f"<td>{esc(item.get('module'))}<br><span>{esc(item.get('recommended_status'))}</span></td>"
            f"<td>{esc(item.get('role'))}</td>"
            f"<td>{esc(item.get('key_output'))}</td>"
            f"<td><span class=\"pill {esc(str(item.get('current_status') or 'planned'))}\">{esc(item.get('current_status'))}</span></td>"
            "</tr>"
        )
    control_rows = []
    for item in (engine.get("leakage_controls") or [])[:6]:
        control_rows.append(
            "<tr>"
            f"<td>{esc(item.get('control'))}</td>"
            f"<td>{'是' if item.get('required') else '否'}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            f"<td>{esc(item.get('evidence'))}</td>"
            "</tr>"
        )
    metric_rows = []
    for item in (engine.get("metrics") or [])[:6]:
        metric_rows.append(
            "<tr>"
            f"<td>{esc(item.get('metric'))}</td>"
            f"<td>{esc(item.get('purpose'))}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            "</tr>"
        )
    technical_rows = []
    for item in (engine.get("technical_rules") or [])[:5]:
        technical_rows.append(
            "<tr>"
            f"<td>{esc(item.get('name'))}</td>"
            f"<td>{esc(item.get('formula'))}</td>"
            f"<td>{esc(item.get('decision_rule'))}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            "</tr>"
        )
    objective_rows = []
    for item in (engine.get("objective_modules") or [])[:8]:
        objective_rows.append(
            "<tr>"
            f"<td>{esc(item.get('module'))}</td>"
            f"<td>{esc(item.get('goal'))}</td>"
            f"<td>{esc(item.get('common_metrics'))}</td>"
            f"<td>{esc(item.get('output'))}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            "</tr>"
        )
    ml_rows = []
    for item in (engine.get("ml_models") or [])[:7]:
        ml_rows.append(
            "<tr>"
            f"<td>{esc(item.get('model'))}</td>"
            f"<td>{esc(item.get('task'))}</td>"
            f"<td>{esc(item.get('risk'))}</td>"
            f"<td>{esc(item.get('current_decision'))}</td>"
            "</tr>"
        )
    scoring_rows = []
    for item in (engine.get("scoring_models") or [])[:2]:
        scoring_rows.append(
            "<tr>"
            f"<td>{esc(item.get('name'))}</td>"
            f"<td>{esc(item.get('formula'))}</td>"
            f"<td>{esc(item.get('use'))}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            "</tr>"
        )
    fundamental_rows = []
    for item in (engine.get("fundamental_layers") or [])[:4]:
        fundamental_rows.append(
            "<tr>"
            f"<td>{esc(item.get('layer'))}</td>"
            f"<td>{esc(item.get('inputs'))}</td>"
            f"<td>{esc(item.get('decision_use'))}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            "</tr>"
        )
    tournament_rows = []
    for item in (engine.get("tournament_rule_requirements") or [])[:8]:
        tournament_rows.append(
            "<tr>"
            f"<td>{esc(item.get('rule'))}</td>"
            f"<td>{esc(item.get('decision_use'))}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            f"<td>{esc(item.get('automation_gate'))}</td>"
            "</tr>"
        )
    contract_rows = []
    for item in (engine.get("prediction_contract_fields") or [])[:9]:
        contract_rows.append(
            "<tr>"
            f"<td>{esc(item.get('field'))}</td>"
            f"<td>{'是' if item.get('required') else '否'}</td>"
            f"<td>{esc(item.get('decision_use'))}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            "</tr>"
        )
    backtest_rows = []
    for item in (engine.get("calibration_backtest_controls") or [])[:7]:
        backtest_rows.append(
            "<tr>"
            f"<td>{esc(item.get('control'))}</td>"
            f"<td>{esc(item.get('purpose'))}</td>"
            f"<td>{esc(item.get('current_status'))}</td>"
            f"<td>{esc(item.get('automation_use'))}</td>"
            "</tr>"
        )
    return f"""
    <section class="probability-engine-panel" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>概率工程吸收</h2>
          <p class="subtitle">把赛制规则、球队强度、Dixon-Coles / Bayesian Poisson 进球模型、xG/xT/VAEP、市场基准、Monte Carlo、校准指标和防泄漏规则拆成可执行覆盖矩阵；未上线项不会伪装成已实现。</p>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>工程状态</span><strong>{esc(engine.get('status'))}</strong></div>
        <div class="insight"><span>固定 seed 策略</span><strong>{esc(engine.get('fixed_random_seed_policy'))}</strong><small>Monte Carlo 待实装</small></div>
        <div class="insight"><span>模块覆盖</span><strong>{esc(summary.get('probability_engine_implemented_or_partial_count', 0))}/{esc(summary.get('probability_engine_module_count', 0))}</strong><small>已实现或部分实现</small></div>
        <div class="insight"><span>防泄漏规则</span><strong>{esc(summary.get('probability_engine_leakage_policy_defined_count', 0))}/{esc(summary.get('probability_engine_leakage_control_count', 0))}</strong></div>
        <div class="insight"><span>校准指标</span><strong>{esc(summary.get('probability_engine_calibration_metric_count', 0))}</strong><small>Brier / Log loss / 校准曲线</small></div>
        <div class="insight"><span>技术规则</span><strong>{esc(summary.get('probability_engine_implemented_technical_rule_count', 0))}/{esc(summary.get('probability_engine_technical_rule_count', 0))}</strong><small>EV / RAEV / CLV</small></div>
        <div class="insight"><span>ML候选模型</span><strong>{esc(summary.get('probability_engine_ml_model_count', 0))}</strong><small>Logistic / XGBoost / CatBoost 等</small></div>
        <div class="insight"><span>基本面层</span><strong>{esc(summary.get('probability_engine_fundamental_layer_count', 0))}</strong><small>Team / Player / Tactical / News</small></div>
        <div class="insight"><span>赛制规则门禁</span><strong>{esc(summary.get('probability_engine_tournament_rule_ready_count', 0))}/{esc(summary.get('probability_engine_tournament_rule_count', 0))}</strong><small>48队路径模拟</small></div>
        <div class="insight"><span>预测合约字段</span><strong>{esc(summary.get('probability_engine_prediction_contract_ready_count', 0))}/{esc(summary.get('probability_engine_prediction_contract_field_count', 0))}</strong><small>prediction_timestamp / odds_phase / source version</small></div>
        <div class="insight"><span>校准回测控制</span><strong>{esc(summary.get('probability_engine_backtest_ready_count', 0))}/{esc(summary.get('probability_engine_backtest_control_count', 0))}</strong><small>Brier / Log loss / CLV / ROI</small></div>
        <div class="insight"><span>下一步升级</span><strong>{esc(engine.get('default_next_upgrade'))}</strong></div>
      </div>
      <p class="note">{esc(engine.get('truthfulness_note'))}</p>
      <p class="note">技术规则包含 EV = 模型概率 × 盘口赔率 - 1；RAEV = 模型认为的胜利概率 × 去水后盘口公平赔率 - 1；CLV = 下注时赔率是否优于 closing odds。</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>模块</th><th>作用</th><th>关键输出</th><th>当前状态</th></tr></thead>
          <tbody>{''.join(module_rows) or '<tr><td colspan="4">暂无概率工程模块数据</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">赛制模拟与预测合约</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>赛制规则</th><th>决策用途</th><th>当前状态</th><th>Automation门禁</th></tr></thead>
          <tbody>{''.join(tournament_rows) or '<tr><td colspan="4">暂无赛制规则门禁</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>预测合约字段</th><th>必须</th><th>决策用途</th><th>当前状态</th></tr></thead>
          <tbody>{''.join(contract_rows) or '<tr><td colspan="4">暂无预测合约字段</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>校准/回测控制</th><th>作用</th><th>当前状态</th><th>Automation用途</th></tr></thead>
          <tbody>{''.join(backtest_rows) or '<tr><td colspan="4">暂无校准回测控制</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>防泄漏/可复现要求</th><th>必须</th><th>当前状态</th><th>证据</th></tr></thead>
          <tbody>{''.join(control_rows) or '<tr><td colspan="4">暂无防泄漏规则</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>模型监控指标</th><th>作用</th><th>当前状态</th></tr></thead>
          <tbody>{''.join(metric_rows) or '<tr><td colspan="3">暂无模型监控指标</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">目标与指标落地</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>模块</th><th>目标</th><th>常用指标</th><th>输出</th><th>当前状态</th></tr></thead>
          <tbody>{''.join(objective_rows) or '<tr><td colspan="5">暂无目标与指标矩阵</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">技术面与模型公式</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>技术面规则</th><th>公式</th><th>决策规则</th><th>当前状态</th></tr></thead>
          <tbody>{''.join(technical_rows) or '<tr><td colspan="4">暂无技术面规则</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>进球模型</th><th>公式</th><th>用途</th><th>当前状态</th></tr></thead>
          <tbody>{''.join(scoring_rows) or '<tr><td colspan="4">暂无进球模型说明</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">机器学习候选模型</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>机器学习模型</th><th>适合任务</th><th>风险</th><th>当前决策</th></tr></thead>
          <tbody>{''.join(ml_rows) or '<tr><td colspan="4">暂无机器学习模型</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">基本面分析层</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>基本面层级</th><th>输入</th><th>决策用途</th><th>当前状态</th></tr></thead>
          <tbody>{''.join(fundamental_rows) or '<tr><td colspan="4">暂无基本面层</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def active_test_decision_html(timeline: dict[str, Any], raw_health: dict[str, Any]) -> str:
    summary = timeline.get("summary") or {}
    rule = timeline.get("cadence_rule") or {}
    min_analyses = rule.get("min_analyses_per_day", 4)
    report_per_day = rule.get("report_per_day", 1)
    slots = rule.get("target_slots") or ["00:00-05:00", "05:00-10:00", "10:00-15:00", "15:00-20:00", "20:00-24:00"]
    raw_ready = raw_health.get("ready") is True
    if raw_ready:
        fill_status = "发现缺口后自动补跑"
        fill_detail = "补跑使用 safe no-latest-publish 模式，完成后再重跑日报门禁。"
        class_name = "ok"
    else:
        fill_status = "等待授权raw"
        fill_detail = "raw 未就绪时不会补跑，避免用过期盘口生成误导报告。"
        class_name = "blocked"
    missing_analysis = summary.get("missing_analysis_day_count", 0)
    missing_report = summary.get("missing_report_day_count", 0)
    queue_count = summary.get("backfill_queue_count", 0)
    slot_text = " / ".join(short_slot(str(slot)) for slot in slots)
    return f"""
      <div class="active-decision {esc(class_name)}">
        <div>
          <span>覆盖规则</span>
          <strong>每天 {esc(min_analyses)} 次分析 + {esc(report_per_day)} 份日报</strong>
          <small>每4-5小时一次：{esc(slot_text)}</small>
        </div>
        <div>
          <span>当前缺口</span>
          <strong>分析 {esc(missing_analysis)} 日 / 日报 {esc(missing_report)} 日</strong>
          <small>待补队列 {esc(queue_count)} 个日期</small>
        </div>
        <div>
          <span>自动补缺状态</span>
          <strong>{esc(fill_status)}</strong>
          <small>{esc(fill_detail)}</small>
        </div>
      </div>
    """


def workflow_nav_html() -> str:
    groups = [
        (
            "决策",
            [
                ("操作总览", "#operation-panel"),
                ("总览", "#command-center"),
                ("推荐下注", "#recommendations"),
                ("Automation评分", "#automation-scorecard"),
                ("采集控制台", "#provider-command-console"),
                ("盘口覆盖", "#alternate-market-workbench"),
                ("工作队列", "#automation-work-queue"),
                ("TT-001录入", "#team-total-manual-entry"),
                ("Provider配置", "#provider-config-doctor"),
                ("Provider KPI", "#provider-kpi"),
                ("Snapshot导入", "#public-snapshot-import"),
                ("人工校验", "#provider-fallback-verification"),
                ("导入状态", "#provider-manual-verification"),
                ("Overlay预览", "#provider-manual-verification"),
                ("执行清单", "#execution-list"),
                ("资金分析", "#market-funding"),
            ],
        ),
        (
            "自动化",
            [
                ("主动测试与自动补缺", "#active-test"),
                ("Raw刷新", "#raw-refresh"),
                ("可用板块", "#available-board-strategy"),
                ("恢复矩阵", "#raw-recovery"),
                ("持仓监控", "#position-monitor"),
            ],
        ),
        (
            "报告",
            [
                ("研究诊断", "#partial-daily-research"),
                ("模型证据", "#source-model-registry"),
                ("成熟度", "#automation-maturity"),
                ("报告下载", "#reports"),
            ],
        ),
    ]
    blocks = []
    for label, items in groups:
        links = "".join(f'<a href="{href}" data-nav-link="{href}">{esc(item)}</a>' for item, href in items)
        blocks.append(f'<div class="nav-group"><span>{esc(label)}</span><div>{links}</div></div>')
    return f"""
    <nav class="command-nav" aria-label="页面快速导航">
      <strong>工作台导航</strong>
      <div class="nav-groups">{''.join(blocks)}</div>
    </nav>
    """


def command_center_html(
    rows: list[dict[str, Any]],
    *,
    execution_allowed: bool,
    gate_message: str,
    raw_health: dict[str, Any],
    timeline: dict[str, Any],
    recommendation_operations: dict[str, Any],
    partial_daily_research: dict[str, Any],
    readiness: dict[str, Any],
    provider_kpi: dict[str, Any],
) -> str:
    first = rows[0] if rows else {}
    rec_summary = recommendation_operations.get("summary") or {}
    portfolio = rec_summary.get("portfolio_risk") or {}
    timeline_summary = timeline.get("summary") or {}
    partial_summary = partial_daily_research.get("summary") or {}
    research_only_readiness = readiness.get("research_only_daily_report") or {}
    raw_partial = normalize_partial_research_refresh(raw_health.get("partial_research_refresh") or {})
    private_bootstrap = readiness.get("private_position_bootstrap") or {}
    private_preflight = private_bootstrap.get("preflight") or {}
    provider_executive = provider_kpi.get("executive_status") or {}
    provider_summary = provider_kpi.get("summary") or {}
    provider_credit = provider_summary.get("credit") or {}
    provider_alt_summary = provider_summary.get("alternate_plan") or {}
    provider_operational_action = (
        provider_alt_summary.get("operational_primary_action")
        or provider_executive.get("recommended_next_action")
        or provider_executive.get("primary_gap")
    )
    top_action = text(first.get("action"), "暂无下注动作")
    if not execution_allowed:
        top_action = "暂停新增下注"
    top_pick = " / ".join(
        item
        for item in [
            text(first.get("event"), ""),
            text(first.get("market"), ""),
            text(first.get("selection"), ""),
        ]
        if item
    ) or text((rec_summary.get("top_pick") or {}).get("selection"), "暂无候选")
    raw_ready = raw_health.get("ready") is True
    queue_count = int(timeline_summary.get("backfill_queue_count") or 0)
    research_allowed = int(partial_summary.get("research_allowed_board_count") or 0)
    unavailable_boards = int(partial_summary.get("unavailable_board_count") or 0)
    private_ready = bool(private_bootstrap.get("ready"))
    task_rows = [
        {
            "status": "暂停" if not execution_allowed else "可执行",
            "class": "blocked" if not execution_allowed else "ok",
            "title": "推荐下注",
            "detail": "当前新增执行金额为 AUD 0；先恢复 raw 和日报门禁。" if not execution_allowed else "按首选盘口逐项复核 TAB 实时赔率。",
            "href": "#recommendations",
            "action": "看推荐",
        },
        {
            "status": f"{research_allowed}/5 可研究",
            "class": "watch" if unavailable_boards else "ok",
            "title": "板块覆盖",
            "detail": f"缺失/排除 {unavailable_boards} 个板块；不可用板块不进入下注候选。",
            "href": "#available-board-strategy",
            "action": "看板块",
        },
        {
            "status": f"待补 {queue_count}",
            "class": "blocked" if queue_count else "ok",
            "title": "主动测试与自动补缺",
            "detail": "点击后先显示时间线快照，再返回实时检测结果；raw blocked 时只补研究诊断。",
            "href": "#active-test",
            "action": "去测试",
        },
        {
            "status": "raw ready" if raw_ready else "raw blocked",
            "class": "ok" if raw_ready else "blocked",
            "title": "公开盘口 raw",
            "detail": text(raw_health.get("recommended_next_action"), "接入授权 raw 或导入用户导出快照后再重跑日报门禁。"),
            "href": "#raw-refresh",
            "action": "看门禁",
        },
        {
            "status": text(provider_executive.get("status"), "provider missing"),
            "class": "ok" if provider_kpi.get("provider_analysis_ready") else "watch",
            "title": "Provider 覆盖",
            "detail": text(provider_operational_action, "授权 provider KPI 待生成。"),
            "href": "#provider-kpi",
            "action": "看覆盖",
        },
        {
            "status": "持仓 ready" if private_ready else text(private_bootstrap.get("status"), "未就绪"),
            "class": "ok" if private_ready else "watch",
            "title": "只读持仓",
            "detail": text(private_preflight.get("blocking_reason"), "用于同步已下注、余额和累计收益率。"),
            "href": "#position-monitor",
            "action": "看持仓",
        },
    ]
    task_html = "".join(
        f"""
        <a class="task-row {esc(item['class'])}" href="{esc(item['href'])}">
          <span class="task-state">{esc(item['status'])}</span>
          <strong>{esc(item['title'])}</strong>
          <small>{esc(item['detail'])}</small>
          <em>{esc(item['action'])}</em>
        </a>
        """
        for item in task_rows
    )
    return f"""
    <section class="command-center" id="command-center" aria-label="今日决策中心">
      <div class="section-head">
        <div>
          <h2>今日决策中心</h2>
          <p class="subtitle">先看动作、金额、缺口和门禁；需要深挖时再跳到下方报告与表格。</p>
        </div>
      </div>
      <div class="command-grid">
        <div class="command-card primary">
          <span>现在应该做什么</span>
          <strong>{esc(top_action)}</strong>
          <small>{esc(gate_message)}</small>
        </div>
        <div class="command-card">
          <span>最高价值盘口</span>
          <strong>{esc(top_pick)}</strong>
          <small>金额 {money(first.get('stake_aud') if execution_allowed else 0)}；EV {esc(pct(first.get('expected_value')))}；Edge {esc(pp(first.get('edge')))}</small>
        </div>
        <div class="command-card">
          <span>主动测试缺口</span>
          <strong>分析 {esc(timeline_summary.get('missing_analysis_day_count', 0))} 日 / 日报 {esc(timeline_summary.get('missing_report_day_count', 0))} 日</strong>
          <small>待补队列 {esc(timeline_summary.get('backfill_queue_count', 0))}；点击按钮后优先返回时间线结果。</small>
        </div>
        <div class="command-card">
          <span>Raw 与研究证据</span>
          <strong>{esc(raw_health.get('status', 'missing'))} / {esc(raw_partial.get('successful_board_count', 0))}/{esc(raw_partial.get('attempted_board_count', 0))}</strong>
          <small>Research-only {esc(raw_partial.get('status', 'not_attempted'))}；新增执行金额 {money(partial_summary.get('current_executable_new_stake_aud', 0))}</small>
        </div>
        <div class="command-card">
          <span>研究日报 automation</span>
          <strong>{'可定时生成' if readiness.get('research_only_daily_report_ready') else '未就绪'} / {'候选就绪' if readiness.get('research_only_recurring_candidate_ready') else '候选待补'}</strong>
          <small>{esc(research_only_readiness.get('status', 'missing'))}；PDF {esc(research_only_readiness.get('pdf', ''))}；正式日报 {'ready' if readiness.get('formal_report_publish_ready') else 'blocked'}</small>
        </div>
        <div class="command-card">
          <span>Provider 覆盖</span>
          <strong>{esc(pct(provider_executive.get('overall_score')))} / {esc(provider_summary.get('event_count', 0))} 场</strong>
          <small>Credit 剩余 {esc(provider_credit.get('reported_remaining', '待同步'))}；{esc(provider_executive.get('primary_gap', '等待 provider KPI'))}</small>
        </div>
        <div class="command-card">
          <span>组合风险</span>
          <strong>{esc(pct(portfolio.get('risk_of_ruin') if portfolio.get('risk_of_ruin') is not None else portfolio.get('portfolio_risk_of_ruin')))}</strong>
          <small>{esc(portfolio.get('recommended_action', '持仓未同步前不解锁执行。'))}</small>
        </div>
        <div class="command-card">
          <span>只读持仓</span>
          <strong>{esc(private_bootstrap.get('status', 'profile_login_required'))}</strong>
          <small>{esc(private_preflight.get('blocking_reason', 'TAB profile 授权状态待同步。'))}</small>
        </div>
      </div>
      <div class="task-list" aria-label="当前任务清单">
        {task_html}
      </div>
    </section>
    """


def action_cards_html(rows: list[dict[str, Any]]) -> str:
    buy_rows = [item for item in rows if item.get("action_class") == "buy"][:5]
    blocked_rows = [item for item in rows if item.get("action_class") == "blocked"][:5]
    display_rows = buy_rows or blocked_rows
    blocked_mode = not buy_rows and bool(blocked_rows)
    if not display_rows:
        return """
          <section class="execution-list" id="execution-list">
            <div class="section-head">
              <div>
                <h2>下注执行清单</h2>
                <p class="subtitle">当前没有通过金额门槛的买入项，先观察盘口变化并刷新日报。</p>
              </div>
            </div>
          </section>
        """
    subtitle = (
        "当前门禁未通过，以下仅为研究候选。TAB 拒绝 AI controlled access 时不能自动刷新 raw；需接入授权数据源或导入用户导出快照，并重跑日报门禁后才可执行。"
        if blocked_mode
        else "按当前可信报告排序，优先展示需要执行的买入项。金额是研究建议金额，执行前仍需复核 TAB 实时赔率。"
    )
    cards = []
    for index, item in enumerate(display_rows, start=1):
        ev_value = pct(item.get("expected_value"))
        edge_value = pp(item.get("edge"))
        edge_gap_value = pp(item.get("edge_threshold_gap"))
        edge_quality = text(item.get("edge_quality"), "待校准")
        arbitrage_value = pct(item.get("arbitrage_rate"))
        risk_value = pct(item.get("risk_of_ruin"))
        risk_grade = text(item.get("risk_of_ruin_grade"), "待校准")
        breakeven_value = pct(item.get("breakeven"))
        half_kelly_value = pct(item.get("discounted_kelly_fraction"))
        stake_fraction_value = pct(item.get("stake_fraction"))
        risk_driver_text = "；".join(str(driver) for driver in (item.get("risk_drivers") or [])) or "无明显额外触发因素"
        diagnostic = item.get("decision_diagnostics") or {}
        min_odds_value = decimal(diagnostic.get("minimum_acceptable_odds"))
        odds_buffer_value = decimal_signed(diagnostic.get("odds_buffer"))
        price_tolerance_value = pct(diagnostic.get("price_drift_tolerance_pct"))
        expected_profit_100 = money(diagnostic.get("expected_profit_per_100_aud"))
        expected_profit = money(diagnostic.get("expected_profit_aud"))
        cap_usage_value = pct(diagnostic.get("stake_to_cap_ratio"))
        kelly_margin_value = pct(diagnostic.get("kelly_safety_margin"))
        risk_adjusted_value = pct(diagnostic.get("risk_adjusted_value_score"))
        value_signal = text(diagnostic.get("value_signal"), "待校准")
        stake_status = text(diagnostic.get("stake_discipline_status"), "待校准")
        ror_status = text(diagnostic.get("ror_status"), "待校准")
        diagnostic_conclusion = text(diagnostic.get("conclusion"), "待校准")
        basis = item.get("analysis_basis") or {}
        model_calibration = item.get("model_calibration") or {}
        basis_summary = text(basis.get("summary"), "判断依据待生成")
        basis_strength = text(basis.get("evidence_strength"), "待校准")
        data_gaps = "；".join(str(value) for value in (basis.get("data_gaps") or [])[:2]) or "资料缺口待复核"
        pre_bet_checklist = "；".join(str(value) for value in (basis.get("pre_bet_checklist") or [])[:2]) or "赛前复核清单待生成"
        model_consistency = text(model_calibration.get("consistency_label"), "待模型校准")
        model_review = text(model_calibration.get("review_action"), "待复核")
        model_evidence = text(model_calibration.get("evidence_text"), "模型校准待生成")
        funding = item.get("market_funding") or {}
        funding_score = text(funding.get("market_funding_tendency_score"), "待校准")
        funding_bias = text(funding.get("market_funding_bias_label"), "待校准")
        funding_net = money(funding.get("net_funds_proxy_aud"))
        funding_turnover = money(funding.get("turnover_proxy_aud"))
        probability = pct(item.get("probability"))
        odds = "待校准" if item.get("odds") is None else f"{float(item['odds']):.2f}"
        action_class = str(item.get("action_class") or "watch")
        action_text_class = "blocked-text" if action_class == "blocked" else "buy-text"
        action_text = text(item.get("action"), "观察")
        amount_label = "研究金额" if action_class == "blocked" else "金额"
        cards.append(
            f"""
            <article class="bet-card {esc(action_class)}">
              <div class="bet-rank">#{index}</div>
              <div class="bet-main">
                <div class="bet-title">{esc(item.get("selection"))}</div>
                <div class="bet-subtitle">{esc(item.get("event"))} / {esc(item.get("market"))}</div>
                <div class="bet-meta">
                  <span>{esc(item.get("time"))}</span>
                  <span>{esc(item.get("board"))}</span>
                  <span>{esc(item.get("value_label"))}</span>
                  <span>{esc(item.get("confidence"))}置信度</span>
                </div>
              </div>
              <div class="bet-numbers">
                <div><span>操作</span><strong class="{action_text_class}">{esc(action_text)}</strong></div>
                <div><span>{esc(amount_label)}</span><strong>{money(item.get("stake_aud"))}</strong></div>
                <div><span>赔率</span><strong>{esc(odds)}</strong></div>
                <div><span>模型概率</span><strong>{esc(probability)}</strong></div>
                <div><span>盈亏平衡</span><strong>{esc(breakeven_value)}</strong></div>
                <div><span>Edge信息</span><strong>{esc(edge_value)} / 差 {esc(edge_gap_value)}</strong><small>{esc(edge_quality)}</small></div>
                <div><span>套利率</span><strong>{esc(arbitrage_value)}</strong></div>
                <div><span>半Kelly / 仓位</span><strong>{esc(half_kelly_value)} / {esc(stake_fraction_value)}</strong></div>
                <div><span>Risk of ruin</span><strong>{esc(risk_value)} / {esc(risk_grade)}</strong><small>{esc(risk_driver_text)}</small></div>
                <div><span>EV</span><strong>{esc(ev_value)}</strong></div>
                <div><span>价值信号</span><strong>{esc(value_signal)}</strong><small>风险调整分 {esc(risk_adjusted_value)}</small></div>
                <div><span>市场资金倾向分</span><strong>{esc(funding_score)} / {esc(funding_bias)}</strong><small>净 {esc(funding_net)} / 成交量 {esc(funding_turnover)}</small></div>
                <div><span>最低可接受赔率</span><strong>{esc(min_odds_value)}</strong><small>缓冲 {esc(odds_buffer_value)} / 容忍 {esc(price_tolerance_value)}</small></div>
                <div><span>每 AUD100 预期</span><strong>{esc(expected_profit_100)}</strong><small>本注 {esc(expected_profit)}</small></div>
                <div><span>纪律 / RoR复核</span><strong>{esc(stake_status)} / {esc(ror_status)}</strong><small>上限占用 {esc(cap_usage_value)} / Kelly垫 {esc(kelly_margin_value)} · {esc(diagnostic_conclusion)}</small></div>
                <div><span>判断依据包</span><strong>{esc(basis_strength)}</strong><small>{esc(basis_summary)}</small></div>
                <div><span>模型校准</span><strong>{esc(model_consistency)}</strong><small>{esc(model_review)}</small></div>
              </div>
              <p class="bet-reason compact-basis"><strong>资料缺口：</strong>{esc(data_gaps)}<br><strong>模型证据：</strong>{esc(model_evidence)}<br><strong>赛前复核：</strong>{esc(pre_bet_checklist)}</p>
              <p class="bet-reason">{esc(item.get("reason"))}</p>
            </article>
            """
        )
    return f"""
      <section class="execution-list" id="execution-list">
        <div class="section-head">
          <div>
            <h2>下注执行清单</h2>
            <p class="subtitle">{esc(subtitle)}</p>
          </div>
        </div>
        <div class="bet-card-list">{''.join(cards)}</div>
      </section>
    """


def timeline_summary_html(timeline: dict[str, Any]) -> str:
    if not timeline:
        return '<div class="empty">尚未运行主动测试。点击“主动测试时间线”后会生成缺口清单。</div>'
    summary = timeline.get("summary") or {}
    days = timeline.get("days") or []
    rule = timeline.get("cadence_rule") or {}
    target_slots = rule.get("target_slots") or []
    rows = []
    for item in days[-8:]:
        status = "缺口" if item.get("needs_backfill") else "完整"
        status_class = "blocked" if item.get("needs_backfill") else "ok"
        covered_slots = set(item.get("covered_slots") or [])
        missing_slots = set(item.get("missing_slots") or [])
        slot_cells = "".join(
            f'<span class="slot-chip {slot_status(slot, covered_slots, missing_slots)}">{esc(short_slot(slot))}</span>'
            for slot in target_slots
        )
        rows.append(
            f"<tr><td>{esc(item.get('display_date'))}</td><td><div class=\"slot-strip\">{slot_cells}</div></td>"
            f"<td>{esc(item.get('effective_analysis_count'))}/{esc(rule.get('min_analyses_per_day'))}</td>"
            f"<td>{'有' if item.get('formal_report_exists') else '缺失'}</td><td><span class=\"status {status_class}\">{status}</span></td>"
            f"<td>{esc('；'.join(item.get('backfill_reasons') or []) or '无需补跑')}</td></tr>"
        )
    return f"""
      <div class="timeline-metrics">
        <div><span>检查天数</span><strong>{esc(summary.get('day_count'))}</strong></div>
        <div><span>分析缺口日</span><strong>{esc(summary.get('missing_analysis_day_count'))}</strong></div>
        <div><span>日报缺口日</span><strong>{esc(summary.get('missing_report_day_count'))}</strong></div>
        <div><span>待补队列</span><strong>{esc(summary.get('backfill_queue_count'))}</strong></div>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>日期</th><th>时段覆盖</th><th>有效分析</th><th>日报</th><th>状态</th><th>补跑判断</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
      {backfill_queue_html(timeline)}
    """


def backfill_queue_html(timeline: dict[str, Any]) -> str:
    queue = timeline.get("backfill_queue") or []
    if not queue:
        return '<div class="empty compact-note">当前没有需要补跑的日期。</div>'
    rows = []
    for item in queue[:5]:
        rows.append(
            f"<tr><td>{esc(item.get('repair_rank'))}</td><td>{esc(item.get('display_date'))}</td>"
            f"<td>{esc(item.get('priority_score'))}</td><td>{esc(item.get('reason'))}</td>"
            f"<td>{esc(item.get('priority_reason'))}</td></tr>"
        )
    return f"""
      <h3 class="subsection-title">补跑优先队列</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>日期</th><th>分数</th><th>缺口</th><th>排序依据</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    """


def short_slot(slot: str) -> str:
    value = text(slot, "")
    value = value.replace(":00", "")
    return value.replace("-", " - ")


def slot_status(slot: str, covered_slots: set[str], missing_slots: set[str]) -> str:
    if slot in covered_slots:
        return "covered"
    if slot in missing_slots:
        return "missing"
    return "unknown"


def report_intelligence_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    status = payload.get("executive_status") or {}
    rec = payload.get("recommendation_summary") or {}
    timeline = payload.get("timeline_health") or {}
    trend = timeline.get("audit_trend_summary") or {}
    model = payload.get("open_source_model_alignment") or {}
    automation_dashboard = payload.get("automation_dashboard") or {}
    feature_counts = payload.get("feature_status_counts") or {}
    next_actions = payload.get("next_actions") or []
    action_rows = "\n".join(
        f"<tr><td>{esc(item.get('priority'))}</td><td>{esc(item.get('title'))}</td><td>{esc(item.get('operation'))}</td></tr>"
        for item in next_actions[:4]
    )
    dashboard_rows = "\n".join(
        f"<tr><td>{esc(item.get('label'))}</td><td>{esc(item.get('status'))}</td><td>{esc(pct(item.get('score'), 2))}</td><td>{esc(item.get('next_action'))}</td></tr>"
        for item in (automation_dashboard.get("rows") or [])[:8]
    )
    feature_text = " / ".join(f"{key} {value}" for key, value in feature_counts.items()) or "待同步"
    return f"""
    <section class="intelligence" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>研究智能层</h2>
          <p class="subtitle">把推荐、回测缺口、报告历史、开源模型和自动化门禁合并成一页业务摘要。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/report_intelligence_latest.pdf">智能层 PDF</a>
          <a class="action secondary" href="app_assets/report_intelligence_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight">
          <span>当前判断</span>
          <strong>{esc(status.get("current_action"))}</strong>
        </div>
        <div class="insight">
          <span>买入候选</span>
          <strong>{esc(rec.get("buy_count", 0))} 条 / {money(rec.get("total_recommended_stake_aud"))}</strong>
        </div>
        <div class="insight">
          <span>主动测试缺口</span>
          <strong>分析 {esc(timeline.get("missing_analysis_day_count", 0))} 日，日报 {esc(timeline.get("missing_report_day_count", 0))} 日</strong>
        </div>
        <div class="insight">
          <span>历史审计趋势</span>
          <strong>{esc(trend.get("audit_count", 0))} 次 / 完整率 {esc(pct(trend.get("latest_complete_ratio"), 2))}</strong>
        </div>
        <div class="insight">
          <span>Automation 得分</span>
          <strong>{esc(pct(automation_dashboard.get("average_score"), 2))} · 阻塞 {esc(automation_dashboard.get("blocked_count", 0))} 项</strong>
        </div>
        <div class="insight">
          <span>开源模型参考</span>
          <strong>{esc(model.get("implemented_reference_count", 0))}/{esc(model.get("reference_count", 0))} 已转化</strong>
        </div>
      </div>
      <p class="note">功能成熟度：{esc(feature_text)}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>模块</th><th>状态</th><th>得分</th><th>下一步</th></tr></thead>
          <tbody>{dashboard_rows or '<tr><td colspan="4">暂无 automation dashboard 数据</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>优先级</th><th>下一步</th><th>操作</th></tr></thead>
          <tbody>{action_rows}</tbody>
        </table>
      </div>
    </section>
    """


def automation_doctor_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    status = payload.get("executive_status") or {}
    timeline = payload.get("timeline_summary") or {}
    trend = payload.get("automation_trend") or {}
    dashboard = payload.get("doctor_dashboard") or {}
    blockers = payload.get("blockers") or []
    commands = payload.get("command_queue") or []
    blocker_rows = "\n".join(
        f"<tr><td>{esc(item.get('priority'))}</td><td>{esc(item.get('title'))}</td><td>{esc(item.get('impact'))}</td></tr>"
        for item in blockers[:4]
    )
    command_rows = "\n".join(
        f"<tr><td>{esc(item.get('priority'))}</td><td>{esc(item.get('title'))}</td><td>{'需要' if item.get('needs_user_presence') else '不需要'}</td><td>{esc(item.get('expected_effect'))}</td></tr>"
        for item in commands[:5]
    )
    ready_text = "可以进入自动日报" if status.get("ready_to_enter_recurring_automation") else "暂不能进入自动日报"
    return f"""
    <section class="doctor" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Automation Doctor Dashboard</h2>
          <p class="subtitle">主动测试发现缺口后，页面会按这个顺序补齐分析和日报。这里只显示业务动作摘要，不要求你读技术日志。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/automation_doctor_latest.pdf">修复计划 PDF</a>
          <a class="action secondary" href="app_assets/automation_doctor_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight">
          <span>统一状态</span>
          <strong>{esc(summary.get("automation_entry_status", "待同步"))}</strong>
          <small>{esc(summary.get("decision_sentence", ""))}</small>
        </div>
        <div class="insight">
          <span>入场判断</span>
          <strong>{esc(dashboard.get("entry_decision", ready_text))}</strong>
        </div>
        <div class="insight">
          <span>入场门禁得分</span>
          <strong>{esc(pct(dashboard.get("readiness_score"), 2))}</strong>
        </div>
        <div class="insight">
          <span>P0 阻塞</span>
          <strong>{esc(dashboard.get("p0_blocker_count", 0))}</strong>
        </div>
        <div class="insight">
          <span>公开盘口状态</span>
          <strong>{esc(dashboard.get("raw_status", "待同步"))}</strong>
        </div>
        <div class="insight">
          <span>私有持仓状态</span>
          <strong>{esc(dashboard.get("private_position_status", "待同步"))}</strong>
        </div>
        <div class="insight">
          <span>首要阻塞</span>
          <strong>{esc(status.get("primary_blocker"))}</strong>
        </div>
        <div class="insight">
          <span>待补分析日</span>
          <strong>{esc(timeline.get("missing_analysis_day_count", 0))} 日</strong>
        </div>
        <div class="insight">
          <span>待补日报日</span>
          <strong>{esc(timeline.get("missing_report_day_count", 0))} 日</strong>
        </div>
        <div class="insight">
          <span>修复焦点</span>
          <strong>{esc(trend.get("repair_focus", "待同步"))}</strong>
        </div>
        <div class="insight">
          <span>下一步动作</span>
          <strong>{esc(summary.get("next_best_action", dashboard.get("next_best_action", "待同步")))}</strong>
        </div>
      </div>
      <p class="note">{esc(summary.get("safety_boundary", "只生成研究报告和诊断，不自动下注。"))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>优先级</th><th>阻塞</th><th>影响</th></tr></thead>
          <tbody>{blocker_rows or '<tr><td colspan="3">暂无阻塞项</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact stacked-table">
        <table>
          <thead><tr><th>优先级</th><th>下一步动作</th><th>人在场</th><th>预期效果</th></tr></thead>
          <tbody>{command_rows}</tbody>
        </table>
      </div>
    </section>
    """


def model_comparison_dashboard_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    dashboard = payload.get("model_dashboard") or {}
    summary = payload.get("summary") or {}
    source = payload.get("source_adoption") or {}
    automation_view = payload.get("automation_view") or {}
    automation_gates = automation_view.get("gates") or []
    execution_gate = next((item for item in automation_gates if item.get("gate") == "execution_unlock"), {})
    divergence_gate = next((item for item in automation_gates if item.get("gate") == "high_divergence_review_queue"), {})
    automation_ready = bool(automation_view.get("automation_view_ready"))
    gate_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('gate'))}</td>"
        f"<td>{esc(item.get('status'))}</td>"
        f"<td>{esc(item.get('evidence'))}</td>"
        "</tr>"
        for item in automation_gates
    )
    prohibited_text = "；".join(str(item) for item in (automation_view.get("prohibited_actions") or []))
    dashboard_usage = "；".join(str(item) for item in (automation_view.get("dashboard_usage") or []))
    top_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('match'))}</td>"
        f"<td>{esc((item.get('consensus') or {}).get('selection'))}</td>"
        f"<td>{esc((item.get('consensus') or {}).get('confidence'))}</td>"
        f"<td>{esc(pct((item.get('disagreement') or {}).get('max_abs_current_vs_elo_dc'), 2))}</td>"
        f"<td>{'是' if (item.get('disagreement') or {}).get('high_divergence') else '否'}</td>"
        "</tr>"
        for item in (payload.get("rows") or [])[:6]
    )
    source_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('display_name'))}</td>"
        f"<td>{esc(item.get('license'))}</td>"
        f"<td>{esc(item.get('adoption_status'))}</td>"
        f"<td>{esc('; '.join((item.get('github_evidence') or [])[-2:]))}</td>"
        "</tr>"
        for item in (source.get("rows") or [])[:4]
    )
    return f"""
    <section class="model-dashboard" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>开源模型 Dashboard</h2>
          <p class="subtitle">把 GitHub 开源模型转成概率交叉验证层：只用于解释分歧、提升概率校准，不单独触发下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/tab_fifa_model_comparison_v0_1.pdf">模型 PDF</a>
          <a class="action secondary" href="app_assets/tab_fifa_model_comparison_v0_1.json">JSON</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>模型定位</span><strong>{esc(dashboard.get('decision'))}</strong></div>
        <div class="insight"><span>比较比赛</span><strong>{esc(dashboard.get('match_count', payload.get('match_count', 0)))}</strong></div>
        <div class="insight"><span>高分歧场次</span><strong>{esc(dashboard.get('high_divergence_count', summary.get('high_divergence_count', 0)))} / {esc(pct(dashboard.get('high_divergence_ratio'), 2))}</strong></div>
        <div class="insight"><span>平均分歧</span><strong>{esc(pct(dashboard.get('avg_disagreement'), 2))}</strong></div>
        <div class="insight"><span>GitHub 源</span><strong>{esc(dashboard.get('implemented_reference_count', 0))}/{esc(dashboard.get('reference_count', 0))} 已转化</strong></div>
        <div class="insight"><span>下一步</span><strong>{esc(dashboard.get('next_action'))}</strong></div>
      </div>
      <p class="note">{esc(dashboard.get('model_risk'))}</p>
      <h3 class="subsection-title">Automation 使用视角</h3>
      <div class="insight-grid">
        <div class="insight"><span>Automation 角色</span><strong>{esc(automation_view.get('automation_role', '研究交叉验证层'))}</strong></div>
        <div class="insight"><span>视角状态</span><strong>{'ready' if automation_ready else 'blocked'}</strong></div>
        <div class="insight"><span>执行解锁</span><strong>{esc(execution_gate.get('status', 'blocked_by_design'))}</strong></div>
        <div class="insight"><span>高分歧复核</span><strong>{esc(divergence_gate.get('status', 'manual_review'))}</strong></div>
      </div>
      <p class="note">Fail-closed：{esc(automation_view.get('fail_closed_policy', 'raw/private/preflight/public-safety 任一失败时，可执行新增下注金额为 AUD 0。'))}</p>
      <p class="note">禁止动作：{esc(prohibited_text or '不自动下注；不点击赔率；不添加投注单；不绕过门禁。')}</p>
      <p class="note">Dashboard 用法：{esc(dashboard_usage or '只用于模型解释、分歧复核和概率校准，不作为下注执行授权。')}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>Gate</th><th>Status</th><th>Evidence</th></tr></thead>
          <tbody>{gate_rows or '<tr><td colspan="3">暂无 Automation gate 数据</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>比赛</th><th>共识注</th><th>置信度</th><th>最大分歧</th><th>高分歧</th></tr></thead>
          <tbody>{top_rows or '<tr><td colspan="5">暂无模型分歧数据</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">GitHub Source Audit</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>来源</th><th>License</th><th>采用状态</th><th>当前证据</th></tr></thead>
          <tbody>{source_rows or '<tr><td colspan="4">暂无 GitHub 源审计</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def model_divergence_review_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('match'))}</td>"
        f"<td>{esc(item.get('consensus_selection'))}<br><span>{esc(pct(item.get('consensus_probability'), 2))}</span></td>"
        f"<td>{esc(item.get('consensus_confidence'))}</td>"
        f"<td>{esc(pct(item.get('max_disagreement'), 2))}</td>"
        f"<td>{'是' if item.get('high_divergence') else '否'}</td>"
        f"<td>{esc(item.get('linked_market'))}<br><span>{esc(item.get('linked_selection'))}</span></td>"
        f"<td>{money(item.get('linked_research_stake_aud'))}</td>"
        f"<td>{esc(pp(item.get('linked_edge_threshold_gap')))}</td>"
        f"<td>{esc(pct(item.get('linked_risk_of_ruin'), 2))}</td>"
        f"<td>{esc(item.get('review_priority'))}</td>"
        f"<td>{esc(item.get('review_action'))}</td>"
        "</tr>"
        for item in (payload.get("review_rows") or [])[:10]
    )
    return f"""
    <section class="model-divergence-review" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>模型分歧复核 Dashboard</h2>
          <p class="subtitle">把开源模型对比转成可归档复核队列：高分歧、低置信、关联推荐下注的盘口先复核，不自动解锁下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/model_divergence_review_latest.pdf">分歧复核 PDF</a>
          <a class="action secondary" href="app_assets/model_divergence_review_latest.json">JSON</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>复核状态</span><strong>{esc(executive.get('status'))}</strong></div>
        <div class="insight"><span>执行解锁</span><strong>{esc(executive.get('execution_unlock'))}</strong></div>
        <div class="insight"><span>高分歧场次</span><strong>{esc(summary.get('high_divergence_count', 0))} / {esc(pct(summary.get('high_divergence_ratio'), 2))}</strong></div>
        <div class="insight"><span>高优先级复核</span><strong>{esc(summary.get('high_priority_review_count', 0))}</strong></div>
        <div class="insight"><span>关联推荐</span><strong>{esc(summary.get('linked_recommendation_count', 0))} / {money(summary.get('linked_research_stake_aud'))}</strong></div>
        <div class="insight"><span>最大模型分歧</span><strong>{esc(pct(summary.get('max_disagreement'), 2))}</strong></div>
        <div class="insight"><span>新旧变化</span><strong>{esc(compare.get('status'))} · 高优先级Δ {esc(compare.get('high_priority_delta', 0))}</strong></div>
        <div class="insight"><span>首要缺口</span><strong>{esc(executive.get('primary_gap'))}</strong></div>
      </div>
      <p class="note">当前动作：{esc(executive.get('current_action'))}</p>
      <p class="note">来源：GitHub 开源模型对比 + 推荐操作 Dashboard；只用于模型解释、分歧复核和概率校准。</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>比赛</th><th>共识</th><th>置信度</th><th>最大分歧</th><th>高分歧</th><th>关联盘口</th><th>金额</th><th>Edge差</th><th>RoR</th><th>优先级</th><th>复核动作</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="11">暂无模型分歧复核数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def source_model_registry_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    github_metadata = payload.get("github_metadata") or {}
    ui_blueprint = payload.get("ui_blueprint") or []
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('display_name'))}</td>"
        f"<td>{esc(item.get('license'))} / {esc(item.get('license_risk'))}</td>"
        f"<td>{esc(item.get('registry_status'))}</td>"
        f"<td>{esc(pct(item.get('implemented_score'), 2))}</td>"
        f"<td>{esc(item.get('live_fetch_status'))}</td>"
        f"<td>{esc(item.get('live_metadata_freshness'))}<br><span>{esc(item.get('live_metadata_age_hours'))}h</span></td>"
        f"<td>{esc(item.get('github_stars', 0))}</td>"
        f"<td>{esc(item.get('github_open_issues', 0))}</td>"
        f"<td>{esc(short_date(item.get('github_pushed_at')))}</td>"
        f"<td>{esc('; '.join((item.get('reusable_features') or [])[:3]))}</td>"
        f"<td>{esc('; '.join((item.get('layout_patterns') or [])[:3]))}</td>"
        f"<td>{esc(item.get('next_conversion_task'))}</td>"
        "</tr>"
        for item in (payload.get("rows") or [])[:6]
    )
    blueprint_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('component_title'))}</td>"
        f"<td>{esc(item.get('implementation_status'))}</td>"
        f"<td>{esc(item.get('dashboard_coverage_status'))}</td>"
        f"<td>{esc('; '.join((item.get('source_refs') or [])[:3]))}</td>"
        f"<td>{esc('; '.join((item.get('borrowed_patterns') or [])[:3]))}</td>"
        f"<td>{esc(item.get('local_ui_contract'))}</td>"
        f"<td>{esc(item.get('dashboard_surface'))}</td>"
        f"<td>{esc(item.get('data_gate'))}</td>"
        f"<td>{esc(item.get('next_step'))}</td>"
        "</tr>"
        for item in ui_blueprint[:6]
    )
    return f"""
    <section class="source-model-registry" id="source-model-registry" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>开源模型库 Dashboard</h2>
          <p class="subtitle">把 GitHub 模型源拆成可复用功能、布局模式、许可风险和下一步转换任务，方便你判断系统到底吸收了哪些外部能力。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/source_model_registry_latest.pdf">模型库 PDF</a>
          <a class="action secondary" href="app_assets/source_model_registry_latest.json">JSON</a>
          <a class="action secondary" href="app_assets/source_model_github_metadata_latest.json">GitHub元数据</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>模型库状态</span><strong>{esc(executive.get('status'))}</strong></div>
        <div class="insight"><span>参考源</span><strong>{esc(summary.get('reference_count', 0))}</strong></div>
        <div class="insight"><span>已吸收 / 设计参考</span><strong>{esc(summary.get('implemented_reference_count', 0))} / {esc(summary.get('design_reference_count', 0))}</strong></div>
        <div class="insight"><span>许可风险</span><strong>{esc(summary.get('license_risk_count', 0))}</strong></div>
        <div class="insight"><span>可复用功能</span><strong>{esc(summary.get('reusable_feature_count', 0))}</strong></div>
        <div class="insight"><span>布局模式</span><strong>{esc(summary.get('layout_pattern_count', 0))}</strong></div>
        <div class="insight"><span>UI蓝图</span><strong>{esc(summary.get('ui_blueprint_implemented_count', 0))}/{esc(summary.get('ui_blueprint_count', 0))} 已落地</strong></div>
        <div class="insight"><span>UI界面覆盖</span><strong>{esc(summary.get('ui_blueprint_dashboard_covered_count', 0))}/{esc(summary.get('ui_blueprint_count', 0))}</strong><small>gated {esc(summary.get('ui_blueprint_dashboard_gated_count', 0))}</small></div>
        <div class="insight"><span>旧新变化</span><strong>{esc(compare.get('status'))} · impl Δ {esc(compare.get('implemented_delta', 0))}</strong></div>
        <div class="insight"><span>自动化复用</span><strong>{'可复用' if executive.get('automation_reuse_ready') else '待增强'}</strong></div>
        <div class="insight"><span>license_control_required</span><strong>{'是' if executive.get('license_control_required') else '否'}</strong></div>
        <div class="insight"><span>GitHub元数据</span><strong>{esc(summary.get('live_metadata_status', github_metadata.get('status', 'missing')))} · {esc(summary.get('live_metadata_ready_count', 0))}/{esc(summary.get('reference_count', 0))}</strong></div>
        <div class="insight"><span>4小时 freshness</span><strong>{esc(summary.get('live_metadata_freshness_status', 'missing'))} · {esc(summary.get('live_metadata_fresh_within_sla_count', 0))}/{esc(summary.get('live_metadata_ready_count', 0))}</strong><small>stale {esc(summary.get('live_metadata_stale_count', 0))} · max age {esc(summary.get('live_metadata_max_age_hours', ''))}h</small></div>
        <div class="insight"><span>Stars / Open issues</span><strong>{esc(summary.get('github_stars_total', 0))} / {esc(summary.get('github_open_issues_total', 0))}</strong></div>
        <div class="insight"><span>最近Push</span><strong>{esc(short_date(summary.get('latest_github_pushed_at')))}</strong></div>
      </div>
      <p class="note">下一步：{esc(executive.get('next_conversion_task'))}</p>
      <div class="button-row">
        <button id="sourceMetadataButton" class="action secondary" type="button">刷新开源模型证据</button>
      </div>
      <div id="sourceMetadataMessage" class="message">只读访问 GitHub 公共 API，更新开源模型证据、模型库报告和本地数据库；不会触发 TAB 或下注操作。</div>
      <h3 class="subsection-title">UI / Dashboard Blueprint</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>组件</th><th>实现状态</th><th>界面覆盖</th><th>来源</th><th>借鉴模式</th><th>本地UI合同</th><th>可用界面</th><th>数据门禁</th><th>下一步</th></tr></thead>
          <tbody>{blueprint_rows or '<tr><td colspan="9">暂无 UI 蓝图数据</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>来源</th><th>License/风险</th><th>采用</th><th>得分</th><th>Fetch</th><th>Freshness</th><th>Stars</th><th>Open issues</th><th>Pushed</th><th>可复用功能</th><th>布局模式</th><th>下一步</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="12">暂无开源模型库数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def recommendation_operations_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    policy = payload.get("calculation_policy") or {}
    top = summary.get("top_pick") or {}
    portfolio = summary.get("portfolio_risk") or {}
    funding_summary = summary.get("market_funding") or {}
    rows = "\n".join(
        recommendation_operation_row_html(item)
        for item in (payload.get("recommendation_rows") or [])[:8]
    )
    excluded_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('board'))}</td>"
        f"<td>{esc(item.get('event'))}<br><span>{esc(item.get('market'))}</span></td>"
        f"<td>{esc(item.get('selection'))}</td>"
        f"<td>{esc(item.get('original_action') or item.get('action'))}</td>"
        f"<td>{money(item.get('stake_aud'))}</td>"
        f"<td>{esc(item.get('live_board_scope_label'))}</td>"
        "</tr>"
        for item in (payload.get("excluded_unavailable_rows") or [])[:6]
    )
    excluded_table = (
        f"""
      <h3 class="subsection-title">缺失板块排除审计</h3>
      <p class="note">这些候选来自历史/旧日报，但当前 TAB live nav 未确认板块可读；系统不把它们计入当前推荐池、Top 盘口或金额汇总。</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>板块</th><th>盘口</th><th>下注</th><th>原动作</th><th>原金额</th><th>范围状态</th></tr></thead>
          <tbody>{excluded_rows}</tbody>
        </table>
      </div>
        """
        if excluded_rows
        else ""
    )
    return f"""
    <section class="recommendation-operations" id="recommendation-operations" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>推荐操作 Dashboard</h2>
          <p class="subtitle">把首页推荐下注板块归档成正式研究报告：操作金额、执行门禁、Edge、套利率、Risk of ruin、EV、概率、置信度和新旧变化一页看清。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/recommendation_operations_latest.pdf">操作 PDF</a>
          <a class="action secondary" href="app_assets/recommendation_operations_latest.json">JSON</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>当前动作</span><strong>{esc(executive.get('current_action'))}</strong></div>
        <div class="insight"><span>可执行新增金额</span><strong>{money(summary.get('executable_new_stake_aud'))}</strong></div>
        <div class="insight"><span>研究候选金额</span><strong>{money(summary.get('research_candidate_stake_aud'))}</strong></div>
        <div class="insight"><span>候选盘口</span><strong>{esc(summary.get('candidate_count', 0))}</strong><small>当前可研究</small></div>
        <div class="insight"><span>缺失板块候选</span><strong>{esc(summary.get('excluded_unavailable_candidate_count', 0))}</strong><small>不进入当前推荐池</small></div>
        <div class="insight"><span>全量历史候选</span><strong>{esc(summary.get('all_candidate_count_before_scope', summary.get('candidate_count', 0)))}</strong><small>scope过滤前</small></div>
        <div class="insight"><span>平均 EV</span><strong>{esc(pct(summary.get('average_ev'), 2))}</strong></div>
        <div class="insight"><span>平均边际</span><strong>{esc(pp(summary.get('average_edge')))}</strong></div>
        <div class="insight"><span>Edge 过门槛</span><strong>{esc(summary.get('edge_threshold_pass_count', 0))}/{esc(summary.get('candidate_count', 0))} · 均差 {esc(pp(summary.get('average_edge_threshold_gap')))}</strong></div>
        <div class="insight"><span>平均套利率</span><strong>{esc(pct(summary.get('average_arbitrage_rate'), 2))}</strong></div>
        <div class="insight"><span>最高 Risk of ruin</span><strong>{esc(pct(summary.get('max_risk_of_ruin'), 2))}</strong></div>
        <div class="insight"><span>RoR 偏高/高</span><strong>{esc(summary.get('high_risk_of_ruin_count', 0))}</strong></div>
        <div class="insight"><span>研究预计收益</span><strong>{money(summary.get('expected_profit_at_research_stake_aud'))}</strong></div>
        <div class="insight"><span>每 AUD100 预期</span><strong>{money(summary.get('average_expected_profit_per_100_aud'))}</strong></div>
        <div class="insight"><span>RoR复核队列</span><strong>{esc(summary.get('ror_review_count', 0))}</strong></div>
        <div class="insight"><span>价值通过</span><strong>{esc(summary.get('value_signal_pass_count', 0))}/{esc(summary.get('candidate_count', 0))}</strong></div>
        <div class="insight"><span>价格缓冲通过</span><strong>{esc(summary.get('price_buffer_positive_count', 0))}</strong></div>
        <div class="insight"><span>低/中 RoR</span><strong>{esc(summary.get('low_or_medium_ror_count', 0))}</strong></div>
        <div class="insight"><span>判断依据包</span><strong>{esc(summary.get('analysis_basis_complete_count', 0))}/{esc(summary.get('candidate_count', 0))}</strong><small>资料缺口 {esc(summary.get('analysis_data_gap_row_count', 0))}</small></div>
        <div class="insight"><span>赛前复核项</span><strong>{esc(summary.get('pre_bet_checklist_item_count', 0))}</strong><small>逐行清单</small></div>
        <div class="insight"><span>模型校准覆盖</span><strong>{esc(summary.get('model_calibrated_count', 0))}/{esc(summary.get('candidate_count', 0))}</strong><small>高分歧 {esc(summary.get('model_high_divergence_count', 0))}</small></div>
        <div class="insight"><span>模型复核队列</span><strong>{esc(summary.get('model_review_required_count', 0))}</strong><small>逆共识 {esc(summary.get('model_reverse_consensus_count', 0))}</small></div>
        <div class="insight"><span>平均价格容忍度</span><strong>{esc(pct(summary.get('average_price_drift_tolerance_pct'), 2))}</strong></div>
        <div class="insight"><span>平均上限占用</span><strong>{esc(pct(summary.get('average_stake_to_cap_ratio'), 2))}</strong></div>
        <div class="insight"><span>风险调整价值分</span><strong>{esc(pct(summary.get('average_risk_adjusted_value_score'), 2))}</strong></div>
        <div class="insight"><span>市场资金倾向分</span><strong>{esc(summary.get('average_market_funding_tendency_score', 0))}</strong><small>支持 {esc(summary.get('supportive_funding_count', 0))} / 偏弱 {esc(summary.get('weak_funding_count', 0))}</small></div>
        <div class="insight"><span>资金代理净额</span><strong>{money(funding_summary.get('net_funds_proxy_aud'))}</strong><small>总 {money(funding_summary.get('total_funds_proxy_aud'))} / 成交量 {money(funding_summary.get('turnover_proxy_aud'))}</small></div>
        <div class="insight"><span>组合Risk of ruin</span><strong>{esc(pct(summary.get('portfolio_risk_of_ruin'), 2))} / {esc(summary.get('portfolio_risk_grade'))}</strong><small>{esc(portfolio.get('portfolio_ror_status'))}</small></div>
        <div class="insight"><span>组合预计收益</span><strong>{money(summary.get('portfolio_expected_profit_aud'))}</strong><small>每AUD100 {money(summary.get('portfolio_expected_profit_per_100_aud'))}</small></div>
        <div class="insight"><span>最坏全输新增亏损</span><strong>{money(summary.get('portfolio_worst_case_new_loss_aud'))}</strong><small>只含本轮候选</small></div>
        <div class="insight"><span>中位预算总占用</span><strong>{esc(pct(summary.get('portfolio_combined_mid_usage_pct'), 2))}</strong><small>下沿余量 {money(summary.get('portfolio_budget_floor_headroom_aud'))}</small></div>
        <div class="insight"><span>Top 盘口</span><strong>{esc(top.get('selection'))} · {esc(top.get('event'))}</strong></div>
        <div class="insight"><span>新旧变化</span><strong>{esc(compare.get('status'))} · stake Δ {money(compare.get('research_stake_delta_aud', 0))}</strong></div>
      </div>
      <p class="note">套利率为模型价值率，不代表跨平台无风险套利；Risk of ruin 使用平衡预算口径和半Kelly偏离估计。</p>
      <p class="note">组合风险：{esc(portfolio.get('recommended_action', '待校准'))}；{esc(portfolio.get('verification_status', '持仓快照未同步前不解锁执行。'))}</p>
      <p class="note">当前推荐池只包含 TAB live nav 已确认可研究的板块；缺失或 route mismatch 板块进入排除审计，不参与 Top pick、Edge、套利率、Risk of ruin 汇总。</p>
      <p class="note">判断依据：{esc(policy.get('template_evidence_digest', 'Excel模板结构、EV/Edge、Kelly、Poisson/xG、赛前清单和CLV/ROI已纳入。'))}</p>
      <p class="note">{esc(executive.get('gate_message'))}</p>
      <h3 class="subsection-title">组合风险与预算压力</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>预算区间</th><th>已投入参考</th><th>研究候选金额</th><th>组合预期</th><th>最坏新增亏损</th><th>组合RoR</th><th>中位预算占用</th><th>预算下沿余量</th><th>动作</th></tr></thead>
          <tbody>
            <tr>
              <td>{money(portfolio.get('budget_floor_aud'))} - {money(portfolio.get('budget_ceiling_aud'))}<br><span>中位 {money(portfolio.get('budget_mid_aud'))}</span></td>
              <td>{money(portfolio.get('declared_committed_reference_aud'))}<br><span>待同步确认</span></td>
              <td>{money(portfolio.get('candidate_stake_aud'))}<br><span>{esc(portfolio.get('candidate_count', 0))} 条</span></td>
              <td>{money(portfolio.get('expected_profit_aud'))}<br><span>每100 {money(portfolio.get('expected_profit_per_100_aud'))}</span></td>
              <td>{money(portfolio.get('worst_case_new_loss_aud'))}</td>
              <td>{esc(pct(portfolio.get('portfolio_risk_of_ruin'), 2))}<br><span>{esc(portfolio.get('portfolio_risk_grade'))} / {esc(portfolio.get('portfolio_ror_status'))}</span></td>
              <td>{esc(pct(portfolio.get('combined_mid_usage_pct'), 2))}</td>
              <td>{money(portfolio.get('budget_floor_headroom_aud'))}</td>
              <td>{esc(portfolio.get('recommended_action'))}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>时</th><th>板块</th><th>盘口</th><th>下注</th><th>赔率</th><th>最低赔率</th><th>金额</th><th>预计收益</th><th>操作</th><th>市场资金倾向分</th><th>Edge信息</th><th>套利率</th><th>Risk of ruin</th><th>价值信号</th><th>EV</th><th>置信度</th><th>模型校准</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="17">暂无推荐操作数据</td></tr>'}</tbody>
        </table>
      </div>
      {excluded_table}
    </section>
    """


def provider_config_doctor_html(payload: dict[str, Any]) -> str:
    if not payload:
        return """
        <section class="provider-kpi" id="provider-config-doctor" style="margin-top:16px;">
          <h2>Provider 配置医生</h2>
          <p class="empty">Provider 配置诊断尚未生成。</p>
        </section>
        """
    summary = payload.get("summary") or {}
    odds = payload.get("the_odds_api") or {}
    optic = payload.get("opticodds") or {}
    credit = payload.get("credit_policy") or {}
    issues = payload.get("issues") or []
    patch = payload.get("recommended_env_patch") or {}
    commands = payload.get("recommended_commands") or []
    issue_rows = "".join(
        f"""
        <tr>
          <td><span class="status {html_status_class('blocked' if row.get('severity') in {'critical', 'high'} else 'watch')}">{esc(row.get('severity'))}</span></td>
          <td>{esc(row.get('code'))}</td>
          <td>{esc(row.get('message'))}</td>
          <td>{esc(row.get('fix'))}</td>
        </tr>
        """
        for row in issues
    )
    patch_rows = "".join(
        f"""
        <tr>
          <td><code>{esc(key)}</code></td>
          <td><code>{esc(value)}</code></td>
        </tr>
        """
        for key, value in patch.items()
    )
    command_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('title'))}</td>
          <td><code>{esc(row.get('command'))}</code></td>
          <td>{esc(row.get('why'))}</td>
        </tr>
        """
        for row in commands
    )
    requested_sports = ", ".join(odds.get("requested_sports") or [])
    recommended_sports = ", ".join(odds.get("recommended_sports") or [])
    legacy_sports = ", ".join(odds.get("known_invalid_or_legacy_sports") or []) or "无"
    return f"""
    <section class="provider-kpi" id="provider-config-doctor" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Provider 配置医生</h2>
          <p class="subtitle">先检查本机 ignored provider env、Unknown Sport 防护和 credit-safe 参数。这里不会请求 odds，不显示真实 API key，也不会下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/provider_config_doctor_latest.pdf">配置诊断 PDF</a>
          <a class="action secondary" href="app_assets/provider_config_doctor_latest.json">JSON</a>
          <a class="action secondary" href="app_assets/provider_config_doctor_latest.md">Markdown</a>
        </div>
      </div>
      <div class="provider-kpi-grid">
        <div class="provider-kpi-primary">
          <span>配置状态</span>
          <strong>{esc(payload.get('status'))}</strong>
          <small>{esc(summary.get('next_safe_action'))}</small>
        </div>
        <div>
          <span>Local env</span>
          <strong>{'存在' if (payload.get('local_env') or {}).get('exists') else '缺失'}</strong>
          <small>{esc((payload.get('local_env') or {}).get('relative_path'))}</small>
        </div>
        <div>
          <span>The Odds API</span>
          <strong>{'已配置' if odds.get('api_key_present') else '缺失'}</strong>
          <small>真实 key 不写入产物</small>
        </div>
        <div>
          <span>OpticOdds</span>
          <strong>{'已配置' if optic.get('api_key_present') else '缺失'}</strong>
          <small>{esc(optic.get('endpoint'))}</small>
        </div>
        <div>
          <span>Unknown Sport 防护</span>
          <strong>{'开启' if odds.get('sports_discovery_enabled') else '关闭'}</strong>
          <small>旧 key：{esc(legacy_sports)}</small>
        </div>
        <div>
          <span>请求 Sport</span>
          <strong>{esc(recommended_sports)}</strong>
          <small>当前：{esc(requested_sports)}</small>
        </div>
        <div>
          <span>Event Probe</span>
          <strong>{esc(odds.get('event_market_probe_limit', 0))}</strong>
          <small>event odds limit {esc(odds.get('event_odds_limit', 0))}</small>
        </div>
        <div>
          <span>Team Total 策略</span>
          <strong>人工/官方访问</strong>
          <small>{esc(credit.get('team_total_policy'))}</small>
        </div>
        <div>
          <span>可执行金额</span>
          <strong>{money(payload.get('current_executable_new_stake_aud'))}</strong>
          <small>配置诊断不解锁下注</small>
        </div>
      </div>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>严重程度</th><th>代码</th><th>问题</th><th>建议修复</th></tr></thead>
          <tbody>{issue_rows or '<tr><td colspan="4">暂无配置问题</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">推荐 env 设置</h3>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>变量</th><th>推荐值</th></tr></thead>
          <tbody>{patch_rows}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">安全命令</h3>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>动作</th><th>命令</th><th>原因</th></tr></thead>
          <tbody>{command_rows}</tbody>
        </table>
      </div>
      <p class="note">安全边界：{esc(payload.get('safety_boundary'))}</p>
    </section>
    """


def provider_collection_console_html(
    provider_kpi: dict[str, Any],
    manual_workbench: dict[str, Any],
    provider_config_doctor: dict[str, Any],
    provider_alternate_plan: dict[str, Any] | None = None,
) -> str:
    if not provider_kpi:
        return """
        <section class="provider-command-console" id="provider-command-console" style="margin-top:16px;">
          <h2>Provider 采集控制台</h2>
          <p class="empty">Provider KPI 尚未生成。先配置授权 API key 并运行 matches refresh。</p>
        </section>
        """
    executive = provider_kpi.get("executive_status") or {}
    summary = provider_kpi.get("summary") or {}
    credit = summary.get("credit") or {}
    alternate_plan = effective_alternate_plan(provider_kpi, provider_alternate_plan)
    operational_decision = alternate_plan.get("operational_decision") or {}
    config_summary = provider_config_doctor.get("summary") or {}
    config_odds = provider_config_doctor.get("the_odds_api") or {}
    next_batch = int(alternate_plan.get("recommended_batch_size") or 0)
    credit_floor = alternate_plan.get("estimated_next_batch_credit_floor")
    credit_ceiling = alternate_plan.get("estimated_next_batch_credit_ceiling")
    remaining = credit.get("reported_remaining")
    remaining_ratio = credit.get("remaining_ratio")
    command = str(alternate_plan.get("recommended_command") or "")
    credit_runway = provider_credit_runway(
        reported_remaining=remaining,
        estimated_credit_floor=credit_floor,
        estimated_credit_ceiling=credit_ceiling,
        recommended_batch_size=next_batch,
    )
    can_probe = bool(
        command
        and next_batch > 0
        and config_odds.get("api_key_present")
        and credit_runway["status"] == "credit_safe"
    )
    manual_next_batch = manual_workbench.get("next_batch") or {}
    pair_templates = manual_workbench.get("pair_templates") or {}
    quality_gate = manual_workbench.get("quality_gate_summary") or {}
    event_probe = alternate_plan.get("event_probe_evidence") or {}
    stop_items = alternate_plan.get("stop_conditions") or []
    stop_rows = "".join(f"<li>{esc(item)}</li>" for item in stop_items[:5])
    family_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('label'))}<br><span>{esc(row.get('role'))}</span></td>
          <td>
            <div class="coverage-bar" aria-label="{esc(row.get('label'))} coverage">
              <span style="width:{width_pct(row.get('coverage_ratio'))}"></span>
            </div>
            <strong>{esc(row.get('covered_count', 0))}/{esc(row.get('event_count', 0))}</strong>
          </td>
          <td><span class="status {html_status_class(row.get('status'))}">{esc(row.get('status'))}</span></td>
          <td>{esc(row.get('available_probe_count', 0))}</td>
          <td>{esc(row.get('provider_status'))}</td>
        </tr>
        """
        for row in (alternate_plan.get("market_family_gaps") or [])[:10]
    )
    queue_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('match'))}<br><span>{esc(row.get('commence_time'))}</span></td>
          <td>{esc(', '.join(row.get('recommended_markets') or []))}</td>
          <td>{esc(', '.join(row.get('missing_families') or []))}</td>
          <td>{esc(row.get('recommended_action'))}</td>
        </tr>
        """
        for row in (alternate_plan.get("next_probe_queue") or alternate_plan.get("next_probe_queue_preview") or [])[:6]
    )
    provider_status_class = "ok" if can_probe else "watch"
    if not config_odds.get("api_key_present"):
        provider_status_class = "blocked"
    elif credit_runway["status"] in {"reserve_floor_reached", "next_batch_would_cross_reserve", "credit_unknown"}:
        provider_status_class = "blocked"
    command_button = (
        f'<button class="action secondary" type="button" data-copy-command="{esc(command)}" data-copy-target="providerCommandMessage" data-copy-label="推荐命令">复制推荐命令</button>'
        if command
        else ""
    )
    manual_action = manual_workbench.get("recommended_next_action") or "等待 Team Total 人工校验工作台。"
    return f"""
    <section class="provider-command-console" id="provider-command-console" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Provider 采集控制台</h2>
          <p class="subtitle">把 API 补齐、credit 风控、Team Total 人工路径和 formal gate 放在一个操作面板。这里不直接请求 provider、不点击 TAB、不下注。</p>
        </div>
        <div class="actions compact-actions">
          {command_button}
          <a class="action secondary" href="app_assets/provider_alternate_plan_latest.pdf">补齐计划</a>
          <a class="action secondary" href="app_assets/provider_manual_next_batch_pair_template_latest.csv">TT-001 模板</a>
          <a class="action secondary" href="app_assets/provider_kpi_latest.json">KPI JSON</a>
          <div id="providerCommandMessage" class="message priority-message">当前推荐命令只用于终端人工执行；执行后必须重建 KPI 并复核 stake 仍为 AUD 0。</div>
        </div>
      </div>
      <div class="provider-control-grid">
        <div class="provider-control-card {esc(provider_status_class)}">
          <span>1. API 小批量补齐</span>
          <strong>{esc('可执行下一批' if can_probe else '暂不建议 API 扩大')}</strong>
          <small>batch {esc(next_batch)} / 队列 {esc(alternate_plan.get('probe_queue_count', 0))} / 预计 {esc(credit_floor)}-{esc(credit_ceiling)} credits</small>
        </div>
        <div class="provider-control-card watch">
          <span>2. Team Total 人工路径</span>
          <strong>{esc(manual_next_batch.get('batch_id') or 'TT-001')}</strong>
          <small>{esc(manual_next_batch.get('event_count', 0))} 场 / {esc(pair_templates.get('next_batch_pair_rows', 0))} 行；{esc(quality_gate.get('import_quality_status') or 'waiting_for_manual_rows')}</small>
        </div>
        <div class="provider-control-card watch">
          <span>3. Credit 风控</span>
          <strong>{esc(credit_runway.get('label'))}</strong>
          <small>剩余 {esc(remaining)}；保底 {esc(credit_runway.get('reserve_floor'))}；下一批后最低 {esc(credit_runway.get('remaining_after_next_batch_ceiling'))}</small>
        </div>
        <div class="provider-control-card blocked">
          <span>4. 发布与下注 Gate</span>
          <strong>{money(provider_kpi.get('current_executable_new_stake_aud'))}</strong>
          <small>formal {esc(yn(provider_kpi.get('formal_publish_allowed')))} / automation {esc(yn(provider_kpi.get('full_automation_allowed')))}</small>
        </div>
      </div>
      <div class="provider-command-lanes">
        <div>
          <span>当前运营判断</span>
          <strong>{esc(operational_decision.get('title') or executive.get('primary_gap') or '等待 provider plan')}</strong>
          <p>{esc(operational_decision.get('primary_action') or executive.get('recommended_next_action'))}</p>
          <small>{esc(operational_decision.get('why') or config_summary.get('next_safe_action'))}</small>
        </div>
        <div>
          <span>Credit Runway</span>
          <strong>{esc(credit_runway.get('label'))}</strong>
          <p>{esc(credit_runway.get('recommended_action'))}</p>
          <small>安全批次数 {esc(credit_runway.get('safe_next_batch_count_before_reserve'))}；剩余比例 {esc(pct(remaining_ratio))}；latest cost {esc(credit.get('reported_last_request_cost'))}</small>
        </div>
        <div>
          <span>样本证据</span>
          <strong>market {esc(event_probe.get('market_probe_count', 0))} / odds {esc(event_probe.get('event_odds_count', 0))}</strong>
          <p>Team Total 可用样本 {esc(event_probe.get('team_total_available_probe_count', 0))}；Total 可用样本 {esc(event_probe.get('total_available_probe_count', 0))}。</p>
          <small>Team Total 不跟随 The Odds API 盲扫；优先 TT-001 或 OpticOdds 官方访问。</small>
        </div>
        <div>
          <span>停止条件</span>
          <ul>{stop_rows or '<li>如果连续低增量或剩余额度不足，暂停 API probe，转人工/官方 provider。</li>'}</ul>
        </div>
      </div>
      <div class="provider-plan-card">
        <span>推荐命令</span>
        <code>{esc(command or '等待 provider alternate plan 生成推荐命令。')}</code>
      </div>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>盘口族</th><th>覆盖进度</th><th>状态</th><th>可用样本</th><th>Provider 状态</th></tr></thead>
          <tbody>{family_rows or '<tr><td colspan="5">暂无盘口族覆盖数据。</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>下一批事件</th><th>目标 markets</th><th>缺口</th><th>动作</th></tr></thead>
          <tbody>{queue_rows or '<tr><td colspan="4">暂无 API 下一批队列；转 Team Total 人工或等待 provider 数据。</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">人工路径：{esc(manual_action)}</p>
      <p class="note">边界：Provider 采集只改善研究覆盖；formal publish、TAB 人工最终校验和持仓 gate 未通过前，新增执行金额保持 AUD 0。</p>
    </section>
    """


def automation_work_queue_from_artifacts(
    *,
    provider_kpi: dict[str, Any],
    provider_alternate_plan: dict[str, Any],
    manual_workbench: dict[str, Any],
    provider_config_doctor: dict[str, Any],
    provider_fallback_verification: dict[str, Any],
    provider_manual_overlay_publish_preflight: dict[str, Any],
    provider_manual_overlay_publish: dict[str, Any],
    readiness: dict[str, Any],
    raw_health: dict[str, Any],
    position_monitor: dict[str, Any],
) -> dict[str, Any]:
    summary = provider_kpi.get("summary") or {}
    credit = summary.get("credit") or {}
    alternate_plan = provider_alternate_plan or provider_kpi.get("alternate_plan") or summary.get("alternate_plan") or {}
    credit_policy = alternate_plan.get("credit_policy") or alternate_plan
    next_batch = int(credit_policy.get("recommended_batch_size") or alternate_plan.get("recommended_batch_size") or 0)
    credit_runway = provider_credit_runway(
        reported_remaining=credit.get("reported_remaining"),
        estimated_credit_floor=credit_policy.get("estimated_next_batch_credit_floor"),
        estimated_credit_ceiling=credit_policy.get("estimated_next_batch_credit_ceiling"),
        recommended_batch_size=next_batch,
    )
    config_odds = provider_config_doctor.get("the_odds_api") or {}
    config_optic = provider_config_doctor.get("opticodds") or {}
    next_batch_payload = manual_workbench.get("next_batch") or {}
    pair_templates = manual_workbench.get("pair_templates") or {}
    quality_gate = manual_workbench.get("quality_gate_summary") or {}
    manual_intake = manual_workbench.get("manual_intake_contract") or {}
    intake_state = manual_intake.get("current_state") or {}
    gates = {
        "formal_publish_allowed": bool(provider_kpi.get("formal_publish_allowed")),
        "full_automation_allowed": bool(provider_kpi.get("full_automation_allowed")),
        "current_executable_new_stake_aud": provider_kpi.get("current_executable_new_stake_aud", 0) or 0,
    }
    tasks: list[dict[str, Any]] = []

    def add_task(
        task_id: str,
        priority: str,
        title: str,
        status: str,
        owner: str,
        gate: str,
        action: str,
        acceptance: str,
        *,
        blocker: str = "",
        command: str = "",
        artifact: str = "",
        evidence: str = "",
    ) -> None:
        tasks.append(
            {
                "id": task_id,
                "priority": priority,
                "title": title,
                "status": status,
                "owner": owner,
                "gate": gate,
                "action": action,
                "blocker": blocker,
                "command": command,
                "artifact": artifact,
                "evidence": evidence,
                "acceptance": acceptance,
                "stake_boundary": "current_executable_new_stake_aud=0",
            }
        )

    missing_events = int(quality_gate.get("missing_event_count") or intake_state.get("missing_event_count") or 0)
    pair_rows = int(pair_templates.get("next_batch_pair_rows") or intake_state.get("next_batch_pair_rows") or 0)
    batch_id = str(next_batch_payload.get("batch_id") or manual_intake.get("current_batch_id") or "TT-001")
    if missing_events > 0 or pair_rows > 0:
        add_task(
            "TT-001",
            "P0",
            f"{batch_id} Team Total 人工导入",
            "manual_required",
            "operator",
            "provider_manual_workbench",
            f"填写 {pair_rows} 行 Team Total O/U，只读核验 TAB，不点击赔率或 Bet Slip。",
            "导入质量达到可解释状态，hash gate 生成，stake 仍为 0。",
            blocker=f"Team Total 缺失 {missing_events} 场；API 未覆盖完整盘口。",
            command=str(manual_intake.get("rebuild_command") or "TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py"),
            artifact=str(manual_intake.get("import_target_display") or manual_intake.get("import_target") or pair_templates.get("import_target") or ""),
            evidence=f"quality={quality_gate.get('import_quality_status', '')}; batch={batch_id}; rows={pair_rows}",
        )

    provider_command = str(alternate_plan.get("recommended_command") or "")
    can_probe = bool(
        provider_command
        and next_batch > 0
        and config_odds.get("api_key_present")
        and credit_runway.get("status") == "credit_safe"
    )
    if not can_probe:
        add_task(
            "CREDIT-RESERVE",
            "P0",
            "The Odds API batch 暂停",
            "credit_or_yield_blocked",
            "system",
            "provider_credit_runway",
            "不要继续批量消耗 The Odds API credits；保留 200 credits 安全线，优先人工/官方 provider。",
            "只有 credit_runway=credit_safe 且 recommended_batch_size>0 时，才允许人工终端执行下一批。",
            blocker=str(credit_runway.get("recommended_action") or alternate_plan.get("recommended_next_action") or ""),
            command=provider_command,
            artifact="outputs/provider_kpi_latest.json",
            evidence=f"remaining={credit_runway.get('reported_remaining')}; reserve={credit_runway.get('reserve_floor')}; after_next={credit_runway.get('remaining_after_next_batch_ceiling')}; status={credit_runway.get('status')}",
        )

    fallback_queue_count = int(provider_fallback_verification.get("queue_count") or alternate_plan.get("fallback_queue_count") or 0)
    if fallback_queue_count > 0 or not config_optic.get("api_key_present"):
        add_task(
            "OPTICODDS-ACCESS",
            "P1",
            "OpticOdds 官方访问/白名单",
            "provider_access_required",
            "operator",
            "authorized_provider_access",
            "申请或配置 OpticOdds 官方访问，用于补 Team Total 和盘口深度，不绕过 TAB AI access 限制。",
            "Provider doctor 显示 OpticOdds key 可用，且 Team Total coverage 能通过官方 API 或人工最终校验增加。",
            blocker=f"fallback queue {fallback_queue_count}; opticodds_key_present={bool(config_optic.get('api_key_present'))}",
            artifact="config/odds_providers.local.env.example",
            evidence=str(provider_fallback_verification.get("provider_blocker_code") or ""),
        )

    if not position_monitor.get("ready"):
        add_task(
            "MY-BETS-READONLY",
            "P1",
            "My Bets 私有持仓只读同步",
            "login_required",
            "operator",
            "private_position_profile",
            "在本机 Chrome/TAB 登录状态下运行只读持仓读取；不自动下注、不改 Bet Slip。",
            "position_monitor 能同步已下注、结算和累计收益率；失败时继续 stake=0。",
            blocker=str(position_monitor.get("recommended_next_action") or position_monitor.get("status") or "profile login required"),
            artifact="private_outputs/my_bets/",
            evidence=f"ready={bool(position_monitor.get('ready'))}; status={position_monitor.get('status', 'missing')}",
        )

    if not gates["formal_publish_allowed"] or not gates["full_automation_allowed"]:
        add_task(
            "FORMAL-PUBLISH-GATE",
            "P1",
            "正式 raw 发布与 automation gate",
            "blocked_until_manual_signature",
            "system",
            "manual_hash_overlay_preflight",
            "等人工导入、hash gate、overlay preflight 和用户签名全部通过后，才允许正式 raw/报告发布。",
            "formal_publish_allowed=true、full_automation_allowed=true 且当前新增下注金额由报告策略重新计算。",
            blocker=f"formal={gates['formal_publish_allowed']}; automation={gates['full_automation_allowed']}",
            artifact="outputs/provider_manual_overlay_publish_preflight_latest.json",
            evidence=f"preflight={provider_manual_overlay_publish_preflight.get('status', 'missing')}; publish={provider_manual_overlay_publish.get('status', 'not_run')}",
        )

    raw_ready = bool(raw_health.get("ready"))
    readiness_status = str(readiness.get("status") or readiness.get("automation_status") or "unknown")
    add_task(
        "AUTOMATION-READINESS",
        "P2",
        "每日 automation readiness 验证",
        "not_ready" if tasks or not raw_ready else "ready_for_review",
        "system",
        "end_to_end_verification",
        "在所有 P0/P1 gate 关闭后，运行完整测试、报告构建、浏览器 smoke 和 API status smoke。",
        "测试通过、报告可打开、status 无冲突、stake 不再被 gate 强制归零后，再讨论每日自动生成。",
        blocker="" if raw_ready else str(raw_health.get("recommended_next_action") or "raw_refresh not ready"),
        artifact="outputs/automation_readiness_latest.json",
        evidence=f"readiness={readiness_status}; raw_ready={raw_ready}",
    )

    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    status_order = {
        "manual_required": 0,
        "credit_or_yield_blocked": 1,
        "provider_access_required": 2,
        "login_required": 3,
        "blocked_until_manual_signature": 4,
        "not_ready": 5,
    }
    tasks.sort(
        key=lambda item: (
            priority_order.get(str(item.get("priority")), 9),
            status_order.get(str(item.get("status")), 9),
            str(item.get("id")),
        )
    )
    blocked_statuses = {"manual_required", "credit_or_yield_blocked", "provider_access_required", "login_required", "blocked_until_manual_signature", "not_ready"}
    blocked_count = sum(1 for item in tasks if item.get("status") in blocked_statuses)
    return {
        "automation_ready": blocked_count == 0 and gates["full_automation_allowed"] and raw_ready,
        "current_executable_new_stake_aud": gates["current_executable_new_stake_aud"],
        "summary": {
            "task_count": len(tasks),
            "blocked_count": blocked_count,
            "manual_required_count": sum(1 for item in tasks if item.get("status") == "manual_required"),
            "p0_count": sum(1 for item in tasks if item.get("priority") == "P0"),
            "next_task_id": (tasks[0] or {}).get("id") if tasks else "",
            "next_task_title": (tasks[0] or {}).get("title") if tasks else "",
            "credit_runway_status": credit_runway.get("status"),
            "team_total_missing_event_count": missing_events,
            "team_total_next_batch_pair_rows": pair_rows,
            "provider_fallback_queue_count": fallback_queue_count,
        },
        "tasks": tasks,
        "safety_boundary": "此队列只读聚合，不触发 provider refresh、TAB 点击、Bet Slip 修改或自动下注。",
    }


def automation_work_queue_html(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    tasks = payload.get("tasks") or []
    cards = [
        ("Automation", "ready" if payload.get("automation_ready") else "blocked", "可进入" if payload.get("automation_ready") else "未解锁"),
        ("当前任务", summary.get("task_count", 0), f"P0 {summary.get('p0_count', 0)} / blocked {summary.get('blocked_count', 0)}"),
        ("Team Total", summary.get("team_total_missing_event_count", 0), f"下一批 {summary.get('team_total_next_batch_pair_rows', 0)} 行"),
        ("Credit", summary.get("credit_runway_status") or "missing", "保底线 200 credits"),
        ("新增可执行金额", money(payload.get("current_executable_new_stake_aud") or 0), "gate 未过保持 0"),
    ]
    card_html = "".join(
        f"""
        <div class="provider-control-card {'blocked' if str(value) in {'blocked', '未解锁'} else 'watch'}">
          <span>{esc(label)}</span>
          <strong>{esc(value)}</strong>
          <small>{esc(detail)}</small>
        </div>
        """
        for label, value, detail in cards
    )
    task_rows = "".join(
        f"""
        <tr>
          <td><strong>{esc(item.get('priority'))}</strong><br><span>{esc(item.get('owner'))}</span></td>
          <td><span class="status {html_status_class(item.get('status'))}">{esc(item.get('status'))}</span><br><span>{esc(item.get('gate'))}</span></td>
          <td>{esc(item.get('title'))}<br><span>{esc(item.get('artifact'))}</span></td>
          <td>{esc(item.get('action'))}<br><span>验收：{esc(item.get('acceptance'))}</span></td>
          <td>{esc(item.get('blocker'))}<br><span>{esc(item.get('evidence'))}</span></td>
          <td>
            <button class="action secondary" type="button" data-copy-command="{esc(item.get('command'))}" data-copy-target="automationWorkQueueMessage" data-copy-label="任务命令">复制命令</button>
            <small>{esc(item.get('stake_boundary'))}</small>
          </td>
        </tr>
        """
        for item in tasks
    )
    return f"""
    <section class="provider-command-console" id="automation-work-queue" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Automation 工作队列</h2>
          <p class="subtitle">把 Team Total、credit reserve、OpticOdds、My Bets、formal publish gate 汇总成下一步任务。这里是只读状态面板，不会运行刷新、不消耗 API、不下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/provider_manual_workbench_latest.pdf">TT 工作台</a>
          <a class="action secondary" href="app_assets/provider_kpi_latest.json">KPI JSON</a>
          <a class="action secondary" href="app_assets/automation_readiness_latest.json">Readiness JSON</a>
          <div id="automationWorkQueueMessage" class="message priority-message">优先处理 P0。复制命令后仍需人工终端执行并刷新状态；任何 gate 未通过时 stake 保持 AUD 0。</div>
        </div>
      </div>
      <div class="provider-control-grid">{card_html}</div>
      <div class="provider-plan-card">
        <span>下一步</span>
        <code>{esc(summary.get('next_task_title') or '所有 gate 已清空，进入最终 readiness 验证。')}</code>
      </div>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>优先级</th><th>状态/Gate</th><th>任务</th><th>动作/验收</th><th>阻塞/证据</th><th>操作</th></tr></thead>
          <tbody>{task_rows or '<tr><td colspan="6">当前没有阻塞任务。</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">边界：{esc(payload.get('safety_boundary'))}</p>
    </section>
    """


def automation_scorecard_from_artifacts(
    *,
    provider_kpi: dict[str, Any],
    provider_alternate_plan: dict[str, Any],
    provider_config_doctor: dict[str, Any],
    automation_work_queue: dict[str, Any],
    position_monitor: dict[str, Any],
    raw_health: dict[str, Any],
) -> dict[str, Any]:
    config_odds = provider_config_doctor.get("the_odds_api") or {}
    summary = provider_kpi.get("summary") or {}
    credit = summary.get("credit") or {}
    plan = effective_alternate_plan(provider_kpi, provider_alternate_plan)
    credit_policy = plan.get("credit_policy") or plan
    next_batch = int(credit_policy.get("recommended_batch_size") or plan.get("recommended_batch_size") or 0)
    credit_runway = provider_credit_runway(
        reported_remaining=credit.get("reported_remaining"),
        estimated_credit_floor=credit_policy.get("estimated_next_batch_credit_floor"),
        estimated_credit_ceiling=credit_policy.get("estimated_next_batch_credit_ceiling"),
        recommended_batch_size=next_batch,
    )
    family_rows = [row for row in (plan.get("market_family_gaps") or []) if isinstance(row, dict)]
    ready_count = sum(
        1
        for row in family_rows
        if row.get("status") == "ready"
        or (float(row.get("required_ratio") or 0) and float(row.get("coverage_ratio") or 0) >= float(row.get("required_ratio") or 0))
    )
    value_rows = [row for row in family_rows if row.get("role") == "value_support"]
    value_ready_count = sum(1 for row in value_rows if row.get("status") == "ready")
    manual_required_count = sum(1 for row in family_rows if row.get("id") == "team_total_ou" and row.get("status") != "ready")
    api_candidate_count = sum(1 for row in family_rows if row.get("status") != "ready" and row.get("id") != "team_total_ou")
    credit_done = credit_runway.get("status") == "credit_safe" or (
        credit_runway.get("status") == "no_api_batch_recommended" and api_candidate_count == 0
    )
    gates = {
        "formal_publish_allowed": bool(provider_kpi.get("formal_publish_allowed")),
        "full_automation_allowed": bool(provider_kpi.get("full_automation_allowed")),
        "current_executable_new_stake_aud": provider_kpi.get("current_executable_new_stake_aud", 0) or 0,
    }
    tasks = automation_work_queue.get("tasks") or []
    task_by_id = {str(item.get("id") or ""): item for item in tasks if isinstance(item, dict)}
    gate_rows: list[dict[str, Any]] = []

    def add_gate(gate_id: str, title: str, weight: int, done: bool, status: str, owner: str, evidence: str, next_action: str) -> None:
        gate_rows.append(
            {
                "id": gate_id,
                "title": title,
                "weight": weight,
                "done": bool(done),
                "status": "passed" if done else status,
                "owner": owner,
                "evidence": evidence,
                "next_action": "保持监控。" if done else next_action,
            }
        )

    add_gate(
        "provider_key_and_sport_config",
        "Provider key 与 sport 配置",
        10,
        bool(config_odds.get("api_key_present")) and "soccer_world_cup" not in (config_odds.get("known_invalid_or_legacy_sports") or []),
        "blocked",
        "system",
        f"the_odds_key={bool(config_odds.get('api_key_present'))}; recommended_sports={','.join(config_odds.get('recommended_sports') or [])}",
        "配置 THE_ODDS_API_KEY，并保持 sport 为 soccer_fifa_world_cup；不把真实 key 提交到 Git。",
    )
    add_gate(
        "core_matches_coverage",
        "Matches 核心盘口覆盖",
        18,
        ready_count >= 2,
        "in_progress",
        "system",
        f"ready_families={ready_count}/{len(family_rows)}; events={summary.get('event_count', 0)}",
        "继续用授权 provider 或人工最终校验补齐 Result/Handicap/Total 等核心上下文。",
    )
    add_gate(
        "value_support_coverage",
        "Value-support 盘口覆盖",
        12,
        bool(value_rows) and value_ready_count >= len(value_rows),
        "paused",
        "system",
        f"value_support_ready={value_ready_count}/{len(value_rows)}; api_candidates={api_candidate_count}",
        "只在 credit_safe 时小批量补 BTTS、Double Chance、Draw No Bet；否则等待额度或官方源。",
    )
    add_gate(
        "team_total_coverage",
        "Team Total O/U 覆盖",
        18,
        manual_required_count == 0 and "TT-001" not in task_by_id,
        "manual_required",
        "operator",
        f"manual_or_official_required={manual_required_count}; fallback_queue={plan.get('fallback_queue_count', 0)}",
        "完成 TT-001 人工只读录入，或接入 OpticOdds 官方访问/白名单。",
    )
    add_gate(
        "credit_runway",
        "Credit runway",
        10,
        credit_done,
        "paused",
        "system",
        f"status={credit_runway.get('status')}; remaining={credit_runway.get('reported_remaining')}; after_next={credit_runway.get('remaining_after_next_batch_ceiling')}",
        "保持 200 credits reserve；只有 credit_safe 或无剩余 API 候选时才解锁。",
    )
    add_gate(
        "my_bets_readonly_snapshot",
        "My Bets 只读持仓快照",
        14,
        bool(position_monitor.get("ready")) and bool(position_monitor.get("snapshot_ready")),
        "login_required",
        "operator",
        f"ready={bool(position_monitor.get('ready'))}; status={position_monitor.get('status', 'missing')}",
        "在本机 TAB 登录后运行只读持仓读取；不同步持仓时 stake 继续为 0。",
    )
    add_gate(
        "formal_publish_gate",
        "Formal publish / automation gate",
        12,
        gates["formal_publish_allowed"] and gates["full_automation_allowed"],
        "blocked",
        "system",
        f"formal={gates['formal_publish_allowed']}; automation={gates['full_automation_allowed']}",
        "等待人工导入、hash gate、overlay preflight 和用户签名全部通过。",
    )
    add_gate(
        "daily_automation_verification",
        "每日 automation E2E 验证",
        6,
        bool(automation_work_queue.get("automation_ready")) and bool(raw_health.get("ready")),
        "not_ready",
        "system",
        f"automation_ready={bool(automation_work_queue.get('automation_ready'))}; raw_ready={bool(raw_health.get('ready'))}",
        "所有 P0/P1 gate 清空后运行完整测试、报告构建、浏览器 smoke 和 API smoke。",
    )
    total_weight = sum(int(row["weight"]) for row in gate_rows) or 1
    passed_weight = sum(int(row["weight"]) for row in gate_rows if row["done"])
    blocked_rows = [row for row in gate_rows if not row["done"]]
    return {
        "ready": True,
        "stage": "automation_ready" if not blocked_rows else "research_platform_with_manual_gates",
        "automation_progress_pct": round(passed_weight / total_weight, 4),
        "passed_weight": passed_weight,
        "total_weight": total_weight,
        "gate_count": len(gate_rows),
        "passed_gate_count": len(gate_rows) - len(blocked_rows),
        "blocked_gate_count": len(blocked_rows),
        "p0_count": int((automation_work_queue.get("summary") or {}).get("p0_count") or 0),
        "next_gate_id": (blocked_rows[0] or {}).get("id") if blocked_rows else "",
        "next_gate_title": (blocked_rows[0] or {}).get("title") if blocked_rows else "Ready for final automation verification",
        "next_safe_action": (blocked_rows[0] or {}).get("next_action") if blocked_rows else "运行最终 readiness 验证并准备每日自动报告。",
        "current_executable_new_stake_aud": gates["current_executable_new_stake_aud"],
        "can_enter_daily_automation": not blocked_rows and bool(automation_work_queue.get("automation_ready")),
        "gate_rows": gate_rows,
        "safety_boundary": "Scorecard 只读聚合现有 artifacts/API 状态，不触发 provider refresh、TAB 点击、Bet Slip 修改或自动下注。",
    }


def automation_scorecard_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    gate_rows = "".join(
        f"""
        <tr>
          <td>{esc(item.get('title'))}<br><span>{esc(item.get('id'))}</span></td>
          <td><span class="status {html_status_class(item.get('status'))}">{esc(item.get('status'))}</span><br><span>权重 {esc(item.get('weight'))}</span></td>
          <td>{esc(item.get('owner'))}</td>
          <td>{esc(item.get('evidence'))}</td>
          <td>{esc(item.get('next_action'))}</td>
        </tr>
        """
        for item in payload.get("gate_rows") or []
    )
    progress_pct = pct(payload.get("automation_progress_pct"), 2)
    return f"""
    <section class="provider-command-console" id="automation-scorecard" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Automation 评分卡</h2>
          <p class="subtitle">把进入每日自动报告前必须通过的 gate 合并成一张评分卡。这里不运行刷新、不消耗 credits、不下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/automation_readiness_latest.json">Readiness JSON</a>
          <a class="action secondary" href="app_assets/provider_kpi_latest.json">Provider KPI</a>
          <a class="action secondary" href="#automation-work-queue">看任务队列</a>
        </div>
      </div>
      <div class="provider-control-grid">
        <div class="provider-control-card {'ok' if payload.get('can_enter_daily_automation') else 'blocked'}">
          <span>Automation进度</span>
          <strong>{esc(progress_pct)}</strong>
          <small>{esc(payload.get('passed_weight'))}/{esc(payload.get('total_weight'))} weighted points</small>
        </div>
        <div class="provider-control-card watch">
          <span>下一 Gate</span>
          <strong>{esc(payload.get('next_gate_title'))}</strong>
          <small>{esc(payload.get('next_gate_id'))}</small>
        </div>
        <div class="provider-control-card blocked">
          <span>未通过 Gate</span>
          <strong>{esc(payload.get('blocked_gate_count'))}/{esc(payload.get('gate_count'))}</strong>
          <small>P0 {esc(payload.get('p0_count'))}</small>
        </div>
        <div class="provider-control-card blocked">
          <span>新增可执行金额</span>
          <strong>{money(payload.get('current_executable_new_stake_aud'))}</strong>
          <small>所有 gate 通过前保持 AUD 0</small>
        </div>
      </div>
      <div class="provider-plan-card">
        <span>下一步</span>
        <code>{esc(payload.get('next_safe_action'))}</code>
      </div>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>Gate</th><th>状态/权重</th><th>Owner</th><th>证据</th><th>下一步</th></tr></thead>
          <tbody>{gate_rows or '<tr><td colspan="5">暂无 scorecard gate。</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">边界：{esc(payload.get('safety_boundary'))}</p>
    </section>
    """


def team_total_manual_entry_html(manual_workbench: dict[str, Any]) -> str:
    entries = team_total_manual_entry_rows()
    quality_gate = manual_workbench.get("quality_gate_summary") or {}
    next_batch = manual_workbench.get("next_batch") or {}
    pair_templates = manual_workbench.get("pair_templates") or {}
    intake = manual_workbench.get("manual_intake_contract") or {}
    status = manual_workbench.get("status") or "missing"

    def selected(value: str, current: str) -> str:
        return " selected" if str(value).lower() == str(current).lower() else ""

    rows = []
    for entry in entries:
        event_id = entry.get("event_id", "")
        rows.append(
            f"""
            <tr data-team-total-entry data-event-id="{attr(event_id)}">
              <td>
                <strong>{esc(entry.get('rank'))}. {esc(entry.get('match'))}</strong><br>
                <span>{esc(entry.get('commence_time'))}</span><br>
                <small>{esc(entry.get('priority_tier'))} / {esc(event_id)}</small>
              </td>
              <td>
                <input class="entry-input wide" data-field="tab_match_name" value="{attr(entry.get('tab_match_name'))}" placeholder="TAB match name">
                <select class="entry-input" data-field="team_scope">
                  <option value="">Scope</option>
                  <option value="home"{selected('home', entry.get('team_scope', ''))}>home</option>
                  <option value="away"{selected('away', entry.get('team_scope', ''))}>away</option>
                  <option value="team"{selected('team', entry.get('team_scope', ''))}>team</option>
                </select>
              </td>
              <td>
                <input class="entry-input wide" data-field="tab_market_name" value="{attr(entry.get('tab_market_name'))}" placeholder="Team Total Goals">
                <input class="entry-input" data-field="line" value="{attr(entry.get('line'))}" inputmode="decimal" placeholder="Line">
              </td>
              <td>
                <input class="entry-input odds" data-field="over_decimal_odds" value="{attr(entry.get('over_decimal_odds'))}" inputmode="decimal" placeholder="Over">
                <input class="entry-input odds" data-field="under_decimal_odds" value="{attr(entry.get('under_decimal_odds'))}" inputmode="decimal" placeholder="Under">
              </td>
              <td>
                <input class="entry-input wide" data-field="observed_at_aest" value="{attr(entry.get('observed_at_aest'))}" placeholder="YYYY-MM-DD HH:mm AEST">
                <input class="entry-input" data-field="operator_initials" value="{attr(entry.get('operator_initials'))}" placeholder="Initials">
              </td>
              <td>
                <input class="entry-input wide" data-field="evidence_note_or_screenshot_ref" value="{attr(entry.get('evidence_note_or_screenshot_ref'))}" placeholder="证据/截图/备注">
                <select class="entry-input" data-field="verification_status">
                  <option value="pending"{selected('pending', entry.get('verification_status', 'pending'))}>pending</option>
                  <option value="pending_review"{selected('pending_review', entry.get('verification_status', ''))}>pending_review</option>
                  <option value="verified"{selected('verified', entry.get('verification_status', ''))}>verified</option>
                  <option value="manual_verified"{selected('manual_verified', entry.get('verification_status', ''))}>manual_verified</option>
                </select>
              </td>
            </tr>
            """
        )
    cards = [
        ("批次", next_batch.get("batch_id") or intake.get("current_batch_id") or "TT-001", f"{len(entries)} 场 / {pair_templates.get('next_batch_pair_rows', len(entries) * 2)} 行"),
        ("导入状态", status, quality_gate.get("import_quality_status") or "waiting"),
        ("缺失比赛", quality_gate.get("missing_event_count", 0), "只完成成对 Over/Under 才进入 hash gate"),
        ("写入目标", f"outputs/{DEFAULT_IMPORT_RELATIVE_PATH}", "固定路径 / 不接受用户路径"),
        ("可执行金额", "AUD 0", "formal gate 前保持 0"),
    ]
    card_html = "".join(
        f"""
        <div class="provider-control-card {'blocked' if label in {'可执行金额', '缺失比赛'} else 'watch'}">
          <span>{esc(label)}</span>
          <strong>{esc(value)}</strong>
          <small>{esc(detail)}</small>
        </div>
        """
        for label, value, detail in cards
    )
    return f"""
    <section class="provider-command-console" id="team-total-manual-entry" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>TT-001 Team Total 网页录入</h2>
          <p class="subtitle">按比赛录入 TAB 页面看到的 Team Total Over/Under。保存后系统自动生成成对 CSV 并重建校验产物；不会运行 provider refresh，不点击 TAB，不加入 Bet Slip。</p>
        </div>
        <div class="actions compact-actions">
          <button class="action secondary" id="teamTotalObservedNowButton" type="button">填入当前AEST时间</button>
          <button class="action primary" id="teamTotalEntrySaveButton" type="button">保存导入CSV</button>
          <a class="action secondary" href="app_assets/provider_manual_next_batch_pair_template_latest.csv">查看模板</a>
          <a class="action secondary" href="app_assets/provider_manual_workbench_latest.pdf">工作台PDF</a>
          <div id="teamTotalEntryMessage" class="message priority-message">只保存完整成对记录；未填完整的比赛会保持 pending 空行，避免污染 Hash Gate。</div>
        </div>
      </div>
      <div class="provider-control-grid">{card_html}</div>
      <div class="table-scroll stacked-table compact manual-entry-table">
        <table>
          <thead><tr><th>比赛</th><th>队伍范围</th><th>盘口/Line</th><th>Over / Under</th><th>时间/操作员</th><th>证据/状态</th></tr></thead>
          <tbody>{''.join(rows) or '<tr><td colspan="6">下一批模板尚未生成。先重建 provider manual workbench。</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">保存规则：同一比赛必须有 team_scope、line、Over odds、Under odds、observed_at_aest、operator_initials、evidence，才写入有效 Over/Under 两行；否则该比赛保持 pending。</p>
      <p class="note">安全边界：只写固定 import target `{esc(DEFAULT_IMPORT_RELATIVE_PATH)}`，不触发下注、不触发 TAB 自动访问、不消耗 The Odds API credits。</p>
    </section>
    """


def alternate_market_action(row: dict[str, Any], credit_runway: dict[str, Any]) -> dict[str, str]:
    family_id = str(row.get("id") or "")
    status = str(row.get("status") or "")
    coverage_ratio = float(row.get("coverage_ratio") or 0)
    required_ratio = float(row.get("required_ratio") or 0)
    missing_count = int(row.get("missing_count") or 0)
    if family_id == "team_total_ou":
        return {
            "status": "manual_or_official_required",
            "class": "blocked",
            "label": "转 TT-001 / OpticOdds",
            "action": "The Odds API 当前 TAB 样本未提供 Team Total；走 TT-001 人工只读或 OpticOdds 官方访问。",
        }
    if status == "ready" or (required_ratio and coverage_ratio >= required_ratio):
        return {
            "status": "coverage_threshold_met",
            "class": "ok",
            "label": "覆盖够用",
            "action": "已达到当前研究阈值；进入候选下注前仍需 TAB/官方源最终校验。",
        }
    if credit_runway.get("status") != "credit_safe":
        return {
            "status": "credit_paused",
            "class": "blocked",
            "label": "暂停 API",
            "action": "当前 credit runway 不允许继续 batch；保留现有覆盖，等待额度或转人工/官方源。",
        }
    if missing_count > 0:
        return {
            "status": "api_batch_candidate",
            "class": "watch",
            "label": "小批量补齐",
            "action": "仅在 credit_safe 时按推荐命令小批量补齐，完成后重建 KPI。",
        }
    return {
        "status": "watch",
        "class": "watch",
        "label": "观察",
        "action": "等待下一批 provider evidence。",
    }


def alternate_market_workbench_html(
    provider_kpi: dict[str, Any],
    provider_alternate_plan: dict[str, Any],
    provider_config_doctor: dict[str, Any],
) -> str:
    plan = effective_alternate_plan(provider_kpi, provider_alternate_plan)
    if not plan:
        return """
        <section class="provider-command-console" id="alternate-market-workbench" style="margin-top:16px;">
          <h2>盘口覆盖工作台</h2>
          <p class="empty">Provider alternate plan 尚未生成。先完成授权 raw/KPI 生成，再查看盘口覆盖。</p>
        </section>
        """
    summary = provider_kpi.get("summary") or {}
    executive = provider_kpi.get("executive_status") or {}
    credit = summary.get("credit") or {}
    credit_policy = plan.get("credit_policy") or plan
    operational_decision = plan.get("operational_decision") or {}
    next_batch = int(credit_policy.get("recommended_batch_size") or plan.get("recommended_batch_size") or 0)
    credit_runway = provider_credit_runway(
        reported_remaining=credit.get("reported_remaining"),
        estimated_credit_floor=credit_policy.get("estimated_next_batch_credit_floor"),
        estimated_credit_ceiling=credit_policy.get("estimated_next_batch_credit_ceiling"),
        recommended_batch_size=next_batch,
    )
    config_odds = provider_config_doctor.get("the_odds_api") or {}
    command = str(plan.get("recommended_command") or "")
    can_probe = bool(
        command
        and next_batch > 0
        and config_odds.get("api_key_present")
        and credit_runway.get("status") == "credit_safe"
    )
    family_rows_data = [row for row in (plan.get("market_family_gaps") or []) if isinstance(row, dict)]
    ready_count = 0
    api_candidate_count = 0
    manual_count = 0
    credit_paused_count = 0
    value_support_count = 0
    value_support_ready_count = 0
    market_rows = []
    for row in family_rows_data:
        decision = alternate_market_action(row, credit_runway)
        ready_count += 1 if decision["status"] == "coverage_threshold_met" else 0
        api_candidate_count += 1 if decision["status"] == "api_batch_candidate" else 0
        manual_count += 1 if decision["status"] == "manual_or_official_required" else 0
        credit_paused_count += 1 if decision["status"] == "credit_paused" else 0
        if row.get("role") == "value_support":
            value_support_count += 1
            value_support_ready_count += 1 if row.get("status") == "ready" else 0
        market_rows.append(
            f"""
            <tr>
              <td>{esc(row.get('label'))}<br><span>{esc(row.get('role'))}</span></td>
              <td>
                <div class="coverage-bar" aria-label="{esc(row.get('label'))} coverage">
                  <span style="width:{width_pct(row.get('coverage_ratio'))}"></span>
                </div>
                <strong>{esc(row.get('covered_count', 0))}/{esc(row.get('event_count', 0))}</strong>
                <span>阈值 {esc(pct(row.get('required_ratio')))} / 当前 {esc(pct(row.get('coverage_ratio')))}</span>
              </td>
              <td><span class="status {esc(decision['class'])}">{esc(decision['label'])}</span></td>
              <td>{esc(row.get('missing_count', 0))}</td>
              <td>{esc(row.get('provider_status'))}</td>
              <td>{esc(row.get('recommended_provider_action') or decision['action'])}</td>
            </tr>
            """
        )
    next_queue = plan.get("next_probe_queue") or plan.get("next_probe_queue_preview") or []
    queue_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('match'))}<br><span>{esc(row.get('commence_time'))}</span></td>
          <td>{esc(', '.join(row.get('recommended_markets') or []))}</td>
          <td>{esc(', '.join(row.get('missing_families') or []))}</td>
          <td>{esc(row.get('recommended_action'))}</td>
        </tr>
        """
        for row in next_queue[:10]
        if isinstance(row, dict)
    )
    stop_rows = "".join(f"<li>{esc(item)}</li>" for item in (plan.get("stop_conditions") or [])[:6])
    command_button = (
        f'<button class="action secondary" type="button" data-copy-command="{esc(command)}" data-copy-target="alternateMarketCommandMessage" data-copy-label="盘口覆盖命令">复制命令</button>'
        if command
        else ""
    )
    batch_label = "可小批量补齐" if can_probe else "暂停 API 补齐"
    batch_class = "ok" if can_probe else "blocked"
    next_safe_action = (
        "credit_safe 时才允许人工终端执行 recommended command；执行后重建 KPI。"
        if can_probe
        else "不执行 The Odds API 新 batch；优先 TT-001 人工校验、OpticOdds 官方访问和 My Bets 只读持仓。"
    )
    return f"""
    <section class="provider-command-console" id="alternate-market-workbench" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>盘口覆盖工作台</h2>
          <p class="subtitle">按盘口族判断哪些可进入研究、哪些需要人工/官方源、哪些因 credit 风控暂停。这里只读聚合已有 artifacts，不触发 API refresh。</p>
        </div>
        <div class="actions compact-actions">
          {command_button}
          <a class="action secondary" href="app_assets/provider_alternate_plan_latest.pdf">补齐计划PDF</a>
          <a class="action secondary" href="app_assets/provider_alternate_plan_latest.json">Plan JSON</a>
          <div id="alternateMarketCommandMessage" class="message priority-message">{esc(next_safe_action)}</div>
        </div>
      </div>
      <div class="provider-control-grid">
        <div class="provider-control-card {esc(batch_class)}">
          <span>API 补齐状态</span>
          <strong>{esc(batch_label)}</strong>
          <small>batch {esc(next_batch)} / queue {esc(plan.get('probe_queue_count', len(next_queue)))} / runway {esc(credit_runway.get('label'))}</small>
        </div>
        <div class="provider-control-card ok">
          <span>已达阈值盘口族</span>
          <strong>{esc(ready_count)}/{esc(len(family_rows_data))}</strong>
          <small>进入候选前仍需 TAB/官方源最终校验。</small>
        </div>
        <div class="provider-control-card watch">
          <span>Value-support 覆盖</span>
          <strong>{esc(value_support_ready_count)}/{esc(value_support_count)}</strong>
          <small>BTTS / Double Chance / Draw No Bet 等辅助正 EV 筛选。</small>
        </div>
        <div class="provider-control-card blocked">
          <span>人工/官方源缺口</span>
          <strong>{esc(manual_count)} 族</strong>
          <small>credit 暂停 {esc(credit_paused_count)} 族；API候选 {esc(api_candidate_count)} 族。</small>
        </div>
      </div>
      <div class="provider-command-lanes">
        <div>
          <span>当前运营判断</span>
          <strong>{esc(operational_decision.get('title') or executive.get('primary_gap') or plan.get('status'))}</strong>
          <p>{esc(operational_decision.get('primary_action') or plan.get('recommended_next_action'))}</p>
          <small>{esc(operational_decision.get('why') or next_safe_action)}</small>
        </div>
        <div>
          <span>Credit Runway</span>
          <strong>{esc(credit_runway.get('label'))}</strong>
          <p>{esc(credit_runway.get('recommended_action'))}</p>
          <small>剩余 {esc(credit.get('reported_remaining'))} / 保底 {esc(credit_runway.get('reserve_floor'))} / latest cost {esc(credit.get('reported_last_request_cost'))}</small>
        </div>
        <div>
          <span>停止条件</span>
          <ul>{stop_rows or '<li>若下一批会跌破 credit reserve 或连续低增量，停止 API probe，转人工/官方 provider。</li>'}</ul>
        </div>
      </div>
      <div class="provider-plan-card">
        <span>推荐命令</span>
        <code>{esc(command or '等待 provider alternate plan 生成推荐命令。')}</code>
      </div>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>盘口族</th><th>覆盖</th><th>动作</th><th>缺口</th><th>Provider状态</th><th>建议</th></tr></thead>
          <tbody>{''.join(market_rows) or '<tr><td colspan="6">暂无盘口族覆盖数据。</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>下一批事件</th><th>目标 markets</th><th>缺口</th><th>动作</th></tr></thead>
          <tbody>{queue_rows or '<tr><td colspan="4">暂无可执行 API 队列；当前优先人工/官方源。</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">边界：本工作台不触发外部请求、不点击 TAB、不加入 Bet Slip、不自动下注；formal publish 和持仓 gate 未通过前，新增可执行金额保持 {money(provider_kpi.get('current_executable_new_stake_aud'))}。</p>
    </section>
    """


def provider_kpi_html(payload: dict[str, Any], provider_alternate_plan: dict[str, Any] | None = None) -> str:
    if not payload:
        return """
        <section class="provider-kpi" id="provider-kpi" style="margin-top:16px;">
          <h2>Provider 覆盖与缺口</h2>
          <p class="empty">Provider KPI 尚未生成。先运行授权 provider refresh，再重建首页。</p>
        </section>
        """
    executive = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    credit = summary.get("credit") or {}
    alternate_plan = effective_alternate_plan(payload, provider_alternate_plan)
    operational_decision = alternate_plan.get("operational_decision") or {}
    blocked_attempt = payload.get("last_blocked_attempt") or {}
    probe_count = int(alternate_plan.get("probe_queue_count") or 0)
    next_batch = int(alternate_plan.get("recommended_batch_size") or 0)
    plan_status = str(alternate_plan.get("status") or "")
    probe_label = "下一批 Probe" if next_batch else "Provider 路径"
    probe_value = f"{next_batch} 场" if next_batch else ("转人工校验" if plan_status == "fallback_required" else "暂停")
    probe_detail = (
        f"队列 {probe_count} / credit {alternate_plan.get('estimated_next_batch_credit_floor')}-{alternate_plan.get('estimated_next_batch_credit_ceiling')}"
        if next_batch
        else f"状态 {plan_status or 'missing'} / 队列 {probe_count}"
    )
    market_rows = payload.get("market_coverage") or []
    kpi_rows = payload.get("kpi_rows") or []
    queue_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('match'))}<br><span>{esc(row.get('commence_time'))}</span></td>
          <td>{esc(', '.join(row.get('missing_families') or []))}</td>
          <td>{esc(', '.join(row.get('recommended_markets') or []))}</td>
          <td>{esc(row.get('recommended_action'))}</td>
        </tr>
        """
        for row in (alternate_plan.get("next_probe_queue") or alternate_plan.get("next_probe_queue_preview") or [])[:5]
    )
    fallback_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('match'))}<br><span>{esc(row.get('commence_time'))}</span></td>
          <td>{esc(', '.join(row.get('missing_families') or []))}</td>
          <td>{esc(row.get('recommended_action'))}</td>
        </tr>
        """
        for row in (alternate_plan.get("fallback_queue_preview") or [])[:5]
    )
    family_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('label'))}<br><span>{esc(row.get('role'))}</span></td>
          <td>{esc(row.get('covered_count', 0))}/{esc(row.get('event_count', 0))}<br><span>{esc(pct(row.get('coverage_ratio')))}</span></td>
          <td><span class="status {html_status_class(row.get('status'))}">{esc(row.get('status'))}</span></td>
          <td>{esc(row.get('available_probe_count', 0))}</td>
          <td>{esc(row.get('provider_status'))}</td>
        </tr>
        """
        for row in (alternate_plan.get("market_family_gaps") or [])[:8]
    )
    market_cells = "".join(
        f"""
        <div>
          <span>{esc(row.get('market'))}</span>
          <strong>{esc(row.get('covered_count', 0))}/{esc(row.get('event_count', 0))}</strong>
          <small>覆盖率 {esc(pct(row.get('coverage_ratio')))}</small>
        </div>
        """
        for row in market_rows
    )
    kpi_table = "".join(
        f"""
        <tr>
          <td>{esc(row.get('name'))}</td>
          <td><span class="status {html_status_class(row.get('status'))}">{esc(row.get('status'))}</span></td>
          <td>{esc(pct(row.get('score')))}</td>
          <td>{esc(row.get('evidence'))}</td>
          <td>{esc(row.get('next_action'))}</td>
        </tr>
        """
        for row in kpi_rows
    )
    decision_status = str(operational_decision.get("status") or plan_status or "missing")
    decision_class = (
        "watch"
        if decision_status == "alternate_probe_plus_team_total_manual" or plan_status == "in_progress"
        else "blocked"
        if "manual" in decision_status or "fallback" in plan_status
        else "watch"
        if decision_status != "ready"
        else "ok"
    )
    decision_title = operational_decision.get("title") or "Provider 下一步"
    decision_action = operational_decision.get("primary_action") or alternate_plan.get("recommended_next_action") or executive.get("recommended_next_action")
    decision_why = operational_decision.get("why") or "等待 provider plan 生成。"
    decision_operator = operational_decision.get("operator_next_step") or "查看补齐计划和人工校验工作台。"
    decision_credit = operational_decision.get("credit_guidance") or probe_detail
    family_by_id = {
        str(row.get("id") or ""): row
        for row in alternate_plan.get("market_family_gaps") or []
        if isinstance(row, dict)
    }
    value_support_parts = []
    for family_id, label in [
        ("btts", "BTTS"),
        ("double_chance", "Double Chance"),
        ("draw_no_bet", "Draw No Bet"),
    ]:
        row = family_by_id.get(family_id) or {}
        value_support_parts.append(
            f"{label} {row.get('covered_count', 0)}/{row.get('event_count', summary.get('event_count', 0))}"
        )
    value_support_summary = "；".join(value_support_parts)
    remaining_ratio = credit.get("remaining_ratio")
    credit_efficiency_note = (
        f"剩余额度 {pct(remaining_ratio)}；只按 batch {next_batch} 保守推进，连续低增量则转 OpticOdds/TAB 人工。"
        if remaining_ratio is not None
        else "缺少 provider usage header；保持小批量 probe。"
    )
    blocked_is_current = bool(blocked_attempt.get("is_current_refresh_blocker"))
    blocked_is_history = bool(blocked_attempt.get("stale_history_only"))
    blocked_label = "当前阻塞" if blocked_is_current else "历史失败" if blocked_is_history else "最近阻断"
    blocked_detail = (
        "影响当前 refresh；先按阻断建议处理"
        if blocked_is_current
        else "历史失败已保留；不代表当前 refresh 失败"
        if blocked_is_history
        else "无阻断或未验证"
    )
    blocked_note = ""
    if blocked_attempt:
        blocked_note = (
            f'<p class="note">Provider {esc(blocked_label)}：{esc(blocked_attempt.get("next_safe_action"))} '
            f'{esc(blocked_detail)}</p>'
        )
    return f"""
    <section class="provider-kpi" id="provider-kpi" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Provider 覆盖与缺口</h2>
          <p class="subtitle">授权数据源当前覆盖能力。这里决定推荐下注板块能不能使用实时盘口，不会触发下注、不点击 TAB。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/provider_kpi_latest.pdf">KPI PDF</a>
          <a class="action secondary" href="app_assets/provider_kpi_latest.json">JSON</a>
          <a class="action secondary" href="app_assets/odds_provider_coverage_latest.json">Coverage</a>
          <a class="action secondary" href="app_assets/provider_alternate_plan_latest.pdf">补齐计划</a>
        </div>
      </div>
      <div class="provider-decision {esc(decision_class)}">
        <div>
          <span>运营决策</span>
          <strong>{esc(decision_title)}</strong>
          <p>{esc(decision_action)}</p>
        </div>
        <div>
          <span>判断依据</span>
          <p>{esc(decision_why)}</p>
        </div>
        <div>
          <span>下一步</span>
          <p>{esc(decision_operator)}</p>
          <small>{esc(decision_credit)}</small>
        </div>
      </div>
      <div class="provider-kpi-grid">
        <div class="provider-kpi-primary">
          <span>平台进度</span>
          <strong>{esc(pct(executive.get('overall_score')))}</strong>
          <small>{esc(executive.get('primary_gap'))}</small>
        </div>
        <div>
          <span>Refresh ID</span>
          <strong>{esc(payload.get('refresh_id') or 'missing')}</strong>
          <small>用于核对 raw / coverage / KPI 是否同一批</small>
        </div>
        <div>
          <span>Matches 覆盖</span>
          <strong>{esc(summary.get('event_count', 0))} 场</strong>
          <small>已覆盖盘口族 {esc(summary.get('covered_market_family_count', 0))} 个</small>
        </div>
        <div>
          <span>Credit</span>
          <strong>{esc(credit.get('reported_remaining'))} 剩余</strong>
          <small>last cost {esc(credit.get('reported_last_request_cost'))} / inferred limit {esc(credit.get('inferred_monthly_limit'))}</small>
        </div>
        <div>
          <span>额度效率</span>
          <strong>last {esc(credit.get('reported_last_request_cost'))} / batch {esc(next_batch)}</strong>
          <small>{esc(credit_efficiency_note)}</small>
        </div>
        <div>
          <span>Value-support 覆盖</span>
          <strong>{esc(value_support_summary)}</strong>
          <small>用于 Result/Total 主推荐之外的正 EV 辅助筛选</small>
        </div>
        <div>
          <span>可执行金额</span>
          <strong>{money(payload.get('current_executable_new_stake_aud'))}</strong>
          <small>formal publish 未通过前保持 0</small>
        </div>
        <div>
          <span>{esc(probe_label)}</span>
          <strong>{esc(probe_value)}</strong>
          <small>{esc(probe_detail)}</small>
        </div>
        <div>
          <span>Fallback 队列</span>
          <strong>{esc(alternate_plan.get('fallback_queue_count', 0))} 场</strong>
          <small>Team Total 转 OpticOdds / TAB 人工校验</small>
        </div>
        <div>
          <span>{esc(blocked_label)}</span>
          <strong>{esc(blocked_attempt.get('blocker_code') or '无')}</strong>
          <small>{esc(blocked_detail)}</small>
        </div>
      </div>
      {blocked_note}
      <div class="provider-market-strip">
        {market_cells}
      </div>
      <div class="table-scroll stacked-table compact" style="margin-top:12px;">
        <table>
          <thead><tr><th>盘口族</th><th>覆盖</th><th>状态</th><th>可用样本</th><th>Provider 状态</th></tr></thead>
          <tbody>{family_rows or '<tr><td colspan="5">暂无 alternate 盘口族诊断</td></tr>'}</tbody>
        </table>
      </div>
      <div class="provider-plan-card">
        <div>
          <span>推荐命令</span>
          <code>{esc(alternate_plan.get('recommended_command') or '等待 provider coverage')}</code>
        </div>
        <div class="table-scroll stacked-table compact">
          <table>
            <thead><tr><th>比赛</th><th>缺口</th><th>目标 markets</th><th>动作</th></tr></thead>
            <tbody>{queue_rows or '<tr><td colspan="4">暂无下一批 probe 队列</td></tr>'}</tbody>
          </table>
        </div>
        <p class="note">{esc(alternate_plan.get('recommended_next_action'))}</p>
        <div class="table-scroll stacked-table compact">
          <table>
            <thead><tr><th>Fallback 比赛</th><th>缺口</th><th>动作</th></tr></thead>
            <tbody>{fallback_rows or '<tr><td colspan="3">暂无 fallback 队列</td></tr>'}</tbody>
          </table>
        </div>
      </div>
      <div class="table-scroll stacked-table">
        <table>
          <thead><tr><th>KPI</th><th>状态</th><th>分数</th><th>证据</th><th>下一步</th></tr></thead>
          <tbody>{kpi_table}</tbody>
        </table>
      </div>
      <p class="note">下一步：{esc(executive.get('recommended_next_action'))}</p>
    </section>
    """


def provider_fallback_verification_html(payload: dict[str, Any]) -> str:
    if not payload:
        return """
        <section class="provider-kpi" id="provider-fallback-verification" style="margin-top:16px;">
          <h2>Team Total 人工校验队列</h2>
          <p class="empty">Provider fallback verification 尚未生成。</p>
        </section>
        """
    rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('rank'))}</td>
          <td>{esc(row.get('match'))}<br><span>{esc(row.get('commence_time'))}</span></td>
          <td><span class="status {html_status_class('ready' if row.get('priority_tier') == 'high' else 'watch')}">{esc(row.get('priority_tier'))}</span></td>
          <td>{esc(row.get('missing_market'))}</td>
          <td>{esc(row.get('rank_reason'))}</td>
          <td>{esc(row.get('post_verification_gate'))}</td>
        </tr>
        """
        for row in (payload.get("manual_verification_queue") or [])[:10]
    )
    contract = payload.get("manual_verification_contract") or {}
    forbidden = "；".join(str(item) for item in contract.get("forbidden_actions") or [])
    return f"""
    <section class="provider-kpi" id="provider-fallback-verification" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Team Total 人工校验队列</h2>
          <p class="subtitle">当 The Odds API 与 OpticOdds 无法覆盖 Team Total 时，这里给出最小人工校验任务。只读盘口，不执行下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/provider_fallback_verification_latest.pdf">校验队列 PDF</a>
          <a class="action secondary" href="app_assets/provider_fallback_verification_latest.json">JSON</a>
          <a class="action secondary" href="app_assets/provider_fallback_verification_latest.md">Markdown</a>
        </div>
      </div>
      <div class="provider-kpi-grid">
        <div class="provider-kpi-primary">
          <span>队列状态</span>
          <strong>{esc(payload.get('status'))}</strong>
          <small>{esc(payload.get('recommended_next_action'))}</small>
        </div>
        <div>
          <span>待校验比赛</span>
          <strong>{esc(payload.get('queue_count', 0))} 场</strong>
          <small>high priority {esc(payload.get('top_priority_count', 0))} 场</small>
        </div>
        <div>
          <span>Provider 阻断</span>
          <strong>{esc(payload.get('provider_blocker_code') or '无')}</strong>
          <small>Team Total 走人工/官方白名单路径</small>
        </div>
        <div>
          <span>可执行金额</span>
          <strong>{money(payload.get('current_executable_new_stake_aud'))}</strong>
          <small>人工校验前保持 0</small>
        </div>
      </div>
      <p class="note">禁止动作：{esc(forbidden)}</p>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>序号</th><th>比赛</th><th>优先级</th><th>缺口</th><th>为什么先看</th><th>校验后门禁</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="6">暂无人工校验队列</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">下一步：{esc(payload.get('recommended_next_action'))}</p>
    </section>
    """


def public_snapshot_import_html(
    payload: dict[str, Any],
    publish_preflight: dict[str, Any] | None = None,
    raw_publish: dict[str, Any] | None = None,
) -> str:
    if not payload:
        return """
        <section class="provider-kpi" id="public-snapshot-import" style="margin-top:16px;">
          <h2>Public Raw Snapshot 导入</h2>
          <p class="empty">Public snapshot 导入状态尚未生成。</p>
        </section>
        """
    coverage = payload.get("market_coverage") or {}
    issues = payload.get("issues") or []
    publish_preflight = publish_preflight or {}
    raw_publish = raw_publish or {}
    preflight_issues = publish_preflight.get("issues") or []
    publish_issues = raw_publish.get("issues") or []
    digest = str(payload.get("preview_raw_sha256") or "")
    short_digest = f"{digest[:10]}...{digest[-8:]}" if len(digest) > 22 else (digest or "pending")
    market_cells = "".join(
        f"""
        <div>
          <span>{esc(name)}</span>
          <strong>{esc(count)} 场</strong>
          <small>{'可用于预览' if int(count or 0) > 0 else '未覆盖'}</small>
        </div>
        """
        for name, count in coverage.items()
    )
    issue_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('field'))}</td>
          <td>{esc(row.get('issue'))}</td>
        </tr>
        """
        for row in issues[:8]
    )
    status = payload.get("status")
    return f"""
    <section class="provider-kpi" id="public-snapshot-import" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Public Raw Snapshot 导入</h2>
          <p class="subtitle">当 TAB 拒绝 AI controlled access 时，可导入人工或第三方工具导出的公开 Matches JSON。这里只生成研究预览 raw，不解锁正式发布或下注金额。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action" href="app_assets/public_snapshot_import_manifest_template_latest.json">导入模板</a>
          <a class="action secondary" href="app_assets/public_snapshot_import_status_latest.pdf">状态 PDF</a>
          <a class="action secondary" href="app_assets/public_snapshot_import_approval_template_latest.json">签名模板</a>
          <a class="action secondary" href="app_assets/public_snapshot_import_publish_preflight_latest.pdf">发布预检</a>
          <a class="action secondary" href="app_assets/public_snapshot_raw_publish_latest.pdf">Raw发布</a>
          <a class="action secondary" href="app_assets/public_snapshot_import_preview_raw_latest.json">Preview Raw</a>
          <a class="action secondary" href="app_assets/public_snapshot_import_status_latest.json">JSON</a>
          <a class="action secondary" href="app_assets/public_snapshot_import_status_latest.md">Markdown</a>
        </div>
      </div>
      <div class="provider-kpi-grid">
        <div class="provider-kpi-primary">
          <span>导入状态</span>
          <strong>{esc(status)}</strong>
          <small>{esc(payload.get('recommended_next_action'))}</small>
        </div>
        <div>
          <span>导入文件</span>
          <strong>{esc(payload.get('selected_snapshot_file') or '等待导入')}</strong>
          <small>{esc(payload.get('import_dir_relative_path'))}</small>
        </div>
        <div>
          <span>比赛数量</span>
          <strong>{esc(payload.get('match_count', 0))} 场</strong>
          <small>核心盘口族 {esc(payload.get('covered_market_family_count', 0))} 个</small>
        </div>
        <div>
          <span>Preview Raw Hash</span>
          <strong>{esc(short_digest)}</strong>
          <small>仅用于研究预览与交接复核</small>
        </div>
        <div>
          <span>可执行金额</span>
          <strong>{money(payload.get('current_executable_new_stake_aud'))}</strong>
          <small>正式 gate 前保持 0</small>
        </div>
        <div>
          <span>问题数量</span>
          <strong>{esc(len(issues))}</strong>
          <small>{'需要修复' if issues else '无结构问题'}</small>
        </div>
        <div>
          <span>签名预检</span>
          <strong>{esc(publish_preflight.get('status') or 'missing')}</strong>
          <small>通过：{esc('是' if publish_preflight.get('snapshot_publish_preflight_passed') else '否')}</small>
        </div>
        <div>
          <span>Approval 文件</span>
          <strong>{esc(publish_preflight.get('approval_relative_path') or '等待生成')}</strong>
          <small>问题 {esc(len(preflight_issues))} 个 / stake AUD 0</small>
        </div>
        <div>
          <span>Raw 发布</span>
          <strong>{esc(raw_publish.get('status') or 'not_run')}</strong>
          <small>已发布：{esc('是' if raw_publish.get('formal_raw_publish_performed') else '否')}</small>
        </div>
        <div>
          <span>发布文件</span>
          <strong>{esc(raw_publish.get('published_raw_snapshot') or '未发布')}</strong>
          <small>batch manifest：{esc('已写入' if raw_publish.get('raw_batch_manifest_written') else '未写入')}</small>
        </div>
        <div>
          <span>Raw Gate</span>
          <strong>{esc('ready' if raw_publish.get('raw_gate_ready') else 'blocked/not run')}</strong>
          <small>问题 {esc(len(publish_issues))} 个 / stake AUD 0</small>
        </div>
      </div>
      <div class="provider-market-strip">
        {market_cells or '<div><span>盘口覆盖</span><strong>0</strong><small>等待导入</small></div>'}
      </div>
      <div class="table-scroll stacked-table compact">
        <table>
          <thead><tr><th>字段</th><th>问题</th></tr></thead>
          <tbody>{issue_rows or '<tr><td colspan="2">暂无结构问题</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">下一步：{esc(payload.get('recommended_next_action'))}</p>
      <p class="note">发布预检：{esc(publish_preflight.get('next_safe_action'))}</p>
      <p class="note">Raw发布：{esc(raw_publish.get('next_safe_action', '未运行 publish_public_snapshot_raw.py；签名通过后才允许显式发布 Matches raw。'))}</p>
      <p class="note">真实性边界：{esc(payload.get('truthfulness_note'))}</p>
    </section>
    """


def provider_manual_verification_html(
    payload: dict[str, Any],
    hash_gate: dict[str, Any] | None = None,
    overlay_preview: dict[str, Any] | None = None,
    overlay_publish_preflight: dict[str, Any] | None = None,
    overlay_publish: dict[str, Any] | None = None,
    manual_workbench: dict[str, Any] | None = None,
) -> str:
    if not payload:
        return """
        <section class="provider-kpi" id="provider-manual-verification" style="margin-top:16px;">
          <h2>人工校验导入状态</h2>
          <p class="empty">人工校验导入状态尚未生成。</p>
        </section>
        """
    completion = payload.get("completion") or {}
    hash_gate = hash_gate or {}
    overlay_preview = overlay_preview or {}
    overlay_publish_preflight = overlay_publish_preflight or {}
    overlay_publish = overlay_publish or {}
    manual_workbench = manual_workbench or {}
    manual_hash = str(hash_gate.get("manual_import_sha256") or "")
    short_hash = f"{manual_hash[:10]}...{manual_hash[-8:]}" if len(manual_hash) > 22 else (manual_hash or "pending")
    overlay_hash = str(overlay_preview.get("overlay_raw_sha256") or "")
    short_overlay_hash = f"{overlay_hash[:10]}...{overlay_hash[-8:]}" if len(overlay_hash) > 22 else (overlay_hash or "pending")
    invalid_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('row_number'))}</td>
          <td>{esc(row.get('event_id'))}</td>
          <td>{esc(row.get('issue'))}</td>
        </tr>
        """
        for row in (payload.get("invalid_rows") or [])[:8]
    )
    workflow = payload.get("manual_workflow") or {}
    steps = "".join(f"<li>{esc(value)}</li>" for _key, value in workflow.items())
    complete = int(completion.get("complete_event_count") or 0)
    total = int(completion.get("queue_count") or payload.get("queue_count") or 0)
    high_complete = int(completion.get("high_priority_complete_count") or 0)
    high_total = int(completion.get("high_priority_count") or payload.get("high_priority_count") or 0)
    next_batch = manual_workbench.get("next_batch") or {}
    pair_templates = manual_workbench.get("pair_templates") or {}
    operator_cockpit = manual_workbench.get("operator_cockpit") or {}
    next_batch_summary = manual_workbench.get("next_batch_summary") or {}
    quality_gate_summary = manual_workbench.get("quality_gate_summary") or {}
    next_batch_quality = manual_workbench.get("next_batch_quality") or {}
    manual_intake = manual_workbench.get("manual_intake_contract") or {}
    intake_state = manual_intake.get("current_state") or {}
    intake_step_rows = "".join(f"<li>{esc(step)}</li>" for step in (manual_intake.get("operator_steps") or [])[:6])
    intake_acceptance_rows = "".join(
        f"<li>{esc(item)}</li>" for item in (manual_intake.get("acceptance_criteria") or [])[:8]
    )
    workflow_rows = "".join(
        f"""
        <tr>
          <td>{esc(step.get('step'))}</td>
          <td>{esc(step.get('title'))}</td>
          <td>{esc(step.get('status'))}</td>
          <td>{esc(step.get('action'))}</td>
        </tr>
        """
        for step in (manual_workbench.get("workflow_steps") or [])[:6]
    )
    field_rows = "".join(
        f"""
        <tr>
          <td>{esc(field.get('label'))}<br><span>{esc(field.get('field'))}</span></td>
          <td>{esc(yn(field.get('required')))}</td>
          <td>{esc(field.get('validation'))}</td>
          <td>{esc(field.get('reason'))}</td>
        </tr>
        """
        for field in (manual_workbench.get("field_checklist") or [])[:12]
    )
    quality_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('rank'))}</td>
          <td>{esc(row.get('match'))}<br><span>{esc(row.get('event_id'))}</span></td>
          <td>{esc(row.get('status'))}</td>
          <td>{esc(', '.join(str(item) for item in (row.get('missing_fields') or [])[:6]) or 'none')}</td>
          <td>{esc('/'.join(str(item) for item in (row.get('missing_directions') or [])) or 'none')}</td>
          <td>{esc(row.get('next_action'))}</td>
        </tr>
        """
        for row in (next_batch_quality.get("rows") or [])[:10]
    )
    next_batch_rows = "".join(
        f"""
        <tr>
          <td>{esc(row.get('rank'))}</td>
          <td>{esc(row.get('match'))}<br><span>{esc(row.get('commence_time'))}</span></td>
          <td>{esc(row.get('priority_tier'))}</td>
          <td>{esc(row.get('rank_reason'))}</td>
        </tr>
        """
        for row in (next_batch.get("rows") or [])[:8]
    )
    return f"""
    <section class="provider-kpi" id="provider-manual-verification" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>人工校验导入状态</h2>
          <p class="subtitle">把无法由 API 覆盖的 Team Total 盘口变成可填写、可校验、可追踪的人工输入闭环。导入完成也只进入 hash gate，不解锁自动下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action" href="app_assets/provider_manual_verification_template_latest.csv">下载 CSV 模板</a>
          <a class="action" href="app_assets/provider_manual_next_batch_pair_template_latest.csv">下一批成对模板</a>
          <a class="action secondary" href="app_assets/provider_manual_pair_template_latest.csv">全量成对模板</a>
          <a class="action secondary" href="app_assets/provider_manual_verification_status_latest.pdf">状态 PDF</a>
          <a class="action secondary" href="app_assets/provider_manual_hash_gate_latest.pdf">Hash Gate</a>
          <a class="action secondary" href="app_assets/provider_manual_overlay_preview_latest.pdf">Overlay预览</a>
          <a class="action secondary" href="app_assets/provider_manual_overlay_publish_preflight_latest.pdf">发布预检</a>
          <a class="action secondary" href="app_assets/provider_manual_overlay_publish_latest.pdf">Overlay发布</a>
          <a class="action secondary" href="app_assets/provider_manual_workbench_latest.pdf">校验工作台</a>
          <button class="action secondary" type="button" data-copy-command="{esc(manual_intake.get('import_target_display') or manual_intake.get('import_target') or payload.get('import_relative_path'))}" data-copy-target="manualIntakeMessage" data-copy-label="导入目标">复制导入目标</button>
          <button class="action secondary" type="button" data-copy-command="{esc(manual_intake.get('rebuild_command'))}" data-copy-target="manualIntakeMessage" data-copy-label="重建命令">复制重建命令</button>
          <a class="action secondary" href="app_assets/provider_manual_verification_status_latest.json">JSON</a>
          <a class="action secondary" href="app_assets/provider_manual_verification_status_latest.md">Markdown</a>
          <div id="manualIntakeMessage" class="message priority-message">TT-001 只读导入合同已生成；复制目标或命令后，仍需人工填写 CSV，不能自动下注。</div>
        </div>
      </div>
      <div class="provider-kpi-grid">
        <div class="provider-kpi-primary">
          <span>导入状态</span>
          <strong>{esc(payload.get('status'))}</strong>
          <small>{esc(payload.get('recommended_next_action'))}</small>
        </div>
        <div>
          <span>完成比赛</span>
          <strong>{esc(complete)}/{esc(total)}</strong>
          <small>{esc(pct(completion.get('completion_pct')))} 完成</small>
        </div>
        <div>
          <span>高优先级</span>
          <strong>{esc(high_complete)}/{esc(high_total)}</strong>
          <small>{esc(pct(completion.get('high_priority_completion_pct')))} 完成</small>
        </div>
        <div>
          <span>错误行</span>
          <strong>{esc(completion.get('invalid_row_count', 0))}</strong>
          <small>valid rows {esc(completion.get('valid_row_count', 0))}</small>
        </div>
        <div>
          <span>Hash Gate</span>
          <strong>{esc(hash_gate.get('status') or 'missing')}</strong>
          <small>ready {esc(hash_gate.get('ready_for_manual_signature', False))}</small>
        </div>
        <div>
          <span>Manual SHA</span>
          <strong>{esc(short_hash)}</strong>
          <small>approved_by_user false</small>
        </div>
        <div>
          <span>Overlay 预览</span>
          <strong>{esc(overlay_preview.get('status') or 'missing')}</strong>
          <small>preview only / 不发布正式 raw</small>
        </div>
        <div>
          <span>合入比赛</span>
          <strong>{esc(overlay_preview.get('overlay_event_count', 0))}/{esc((overlay_preview.get('completion') or {}).get('queue_count', total))}</strong>
          <small>rows {esc(overlay_preview.get('overlay_row_count', 0))}</small>
        </div>
        <div>
          <span>Overlay SHA</span>
          <strong>{esc(short_overlay_hash)}</strong>
          <small>preflight {esc(overlay_preview.get('ready_for_publish_preflight', False))}</small>
        </div>
        <div>
          <span>发布边界</span>
          <strong>{esc(yn(overlay_preview.get('formal_publish_allowed', False)))}</strong>
          <small>approved_by_user false / stake AUD 0</small>
        </div>
        <div>
          <span>发布预检</span>
          <strong>{esc(overlay_publish_preflight.get('status') or 'missing')}</strong>
          <small>通过 {esc(yn(overlay_publish_preflight.get('overlay_publish_preflight_passed', False)))}</small>
        </div>
        <div>
          <span>签名状态</span>
          <strong>{esc(yn(overlay_publish_preflight.get('approved_by_user', False)))}</strong>
          <small>issues {esc(len(overlay_publish_preflight.get('issues') or []))}</small>
        </div>
        <div>
          <span>Overlay 发布</span>
          <strong>{esc(overlay_publish.get('status') or 'not_run')}</strong>
          <small>已发布 {esc(yn(overlay_publish.get('formal_raw_publish_performed', False)))}</small>
        </div>
        <div>
          <span>发布文件</span>
          <strong>{esc(overlay_publish.get('published_raw_snapshot') or '未发布')}</strong>
          <small>batch manifest {esc(yn(overlay_publish.get('raw_batch_manifest_written', False)))}</small>
        </div>
        <div>
          <span>发布 Gate</span>
          <strong>{esc('ready' if overlay_publish.get('raw_gate_ready') else 'blocked/not run')}</strong>
          <small>issues {esc(len(overlay_publish.get('issues') or []))} / stake AUD 0</small>
        </div>
        <div>
          <span>校验工作台</span>
          <strong>{esc(manual_workbench.get('status') or 'missing')}</strong>
          <small>批次 {esc(manual_workbench.get('batch_count', 0))} / 下一批 {esc(next_batch.get('batch_id') or 'none')}</small>
        </div>
        <div>
          <span>剩余候选</span>
          <strong>{esc(manual_workbench.get('remaining_event_count', total - complete))}</strong>
          <small>高优先级剩余 {esc(manual_workbench.get('remaining_high_priority_count', high_total - high_complete))}</small>
        </div>
        <div>
          <span>成对模板</span>
          <strong>{esc(pair_templates.get('next_batch_pair_rows', 0))}</strong>
          <small>下一批行数 / 全量 {esc(pair_templates.get('all_candidate_pair_rows', 0))}</small>
        </div>
        <div>
          <span>导入文件</span>
          <strong>{esc(payload.get('import_file'))}</strong>
          <small>{esc(payload.get('import_relative_path'))}</small>
        </div>
        <div>
          <span>可执行金额</span>
          <strong>{money(payload.get('current_executable_new_stake_aud'))}</strong>
          <small>hash gate 前保持 0</small>
        </div>
      </div>
      <div class="provider-decision" style="margin-top:12px;">
        <div>
          <span>TT-001 操作台</span>
          <strong>{esc(operator_cockpit.get('primary_action') or manual_workbench.get('recommended_next_action') or '等待人工导入')}</strong>
          <p>{esc(operator_cockpit.get('operator_warning') or '只读核验，不点击赔率，不加入 Bet Slip。')}</p>
        </div>
        <div>
          <span>当前批次</span>
          <strong>{esc(operator_cockpit.get('current_batch_id') or next_batch.get('batch_id') or 'none')}</strong>
          <small>{esc(operator_cockpit.get('current_batch_event_count') or next_batch.get('event_count') or 0)} 场 / {esc(operator_cockpit.get('current_batch_pair_rows') or pair_templates.get('next_batch_pair_rows', 0))} 行</small>
        </div>
        <div>
          <span>导入目标</span>
          <strong>{esc(operator_cockpit.get('import_target') or pair_templates.get('import_target') or payload.get('import_relative_path'))}</strong>
          <small>模板 {esc(operator_cockpit.get('next_batch_pair_template_csv') or pair_templates.get('next_batch_csv'))}</small>
        </div>
        <div>
          <span>发布状态</span>
          <strong>{esc(operator_cockpit.get('publish_status') or 'blocked')}</strong>
          <small>can publish {esc(yn(operator_cockpit.get('can_publish_now', False)))} / stake AUD 0</small>
        </div>
        <div>
          <span>质量 Gate</span>
          <strong>{esc(quality_gate_summary.get('import_quality_status') or 'waiting_for_manual_rows')}</strong>
          <small>missing {esc(quality_gate_summary.get('missing_event_count', 0))} / partial {esc(quality_gate_summary.get('partial_event_count', 0))} / invalid {esc(quality_gate_summary.get('invalid_event_count', 0))}</small>
        </div>
      </div>
      <div class="provider-command-lanes" style="margin-top:12px;">
        <div>
          <span>TT-001 Intake Contract</span>
          <strong>{esc(manual_intake.get('title') or 'Team Total 人工导入合同')}</strong>
          <p>模板 {esc(manual_intake.get('template_csv') or pair_templates.get('next_batch_csv'))}；保存到 {esc(manual_intake.get('import_target_display') or manual_intake.get('import_target') or payload.get('import_relative_path'))}。</p>
          <small>{esc(manual_intake.get('next_safe_action') or quality_gate_summary.get('next_action') or '等待人工导入。')}</small>
        </div>
        <div>
          <span>重建命令</span>
          <strong>{esc(manual_intake.get('rebuild_command') or 'TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py')}</strong>
          <p>重建后复核 Hash Gate、Overlay 预览、发布预检和 Downloads 首页。</p>
          <small>签名通过后才允许：{esc(manual_intake.get('publish_command_after_signature') or 'python3 publish_provider_manual_overlay.py')}</small>
        </div>
        <div>
          <span>当前缺口</span>
          <strong>missing {esc(intake_state.get('missing_event_count', quality_gate_summary.get('missing_event_count', 0)))}</strong>
          <p>partial {esc(intake_state.get('partial_event_count', 0))} / invalid {esc(intake_state.get('invalid_event_count', 0))} / complete {esc(intake_state.get('complete_event_count', 0))}</p>
          <small>当前可执行新增金额 {money(intake_state.get('current_executable_new_stake_aud', 0))}</small>
        </div>
      </div>
      <div class="provider-plan-card" style="margin-top:12px;">
        <div>
          <span>导入步骤</span>
          <ol>{intake_step_rows or '<li>打开下一批成对模板，按 TAB 页面只读填写 Team Total Over/Under。</li>'}</ol>
        </div>
        <div>
          <span>验收条件</span>
          <ul>{intake_acceptance_rows or '<li>Hash Gate、Overlay Preview、Publish Preflight 均通过前，stake 保持 AUD 0。</li>'}</ul>
        </div>
      </div>
      <div class="provider-plan-card">
        <div>
          <span>人工工作流</span>
          <ol>{steps}</ol>
        </div>
        <div class="table-scroll stacked-table compact">
          <table>
            <thead><tr><th>行号</th><th>Event</th><th>问题</th></tr></thead>
            <tbody>{invalid_rows or '<tr><td colspan="3">暂无错误行；如果状态仍未完成，说明导入文件缺失或候选尚未填满 Over/Under 成对记录。</td></tr>'}</tbody>
          </table>
        </div>
      </div>
      <div class="provider-plan-card" style="margin-top:12px;">
        <div>
          <span>操作台流程</span>
          <div class="table-scroll stacked-table compact">
            <table>
              <thead><tr><th>Step</th><th>动作</th><th>状态</th><th>执行说明</th></tr></thead>
              <tbody>{workflow_rows or '<tr><td colspan="4">暂无流程状态；请先重建校验工作台。</td></tr>'}</tbody>
            </table>
          </div>
        </div>
        <div>
          <span>字段检查</span>
          <div class="table-scroll stacked-table compact">
            <table>
              <thead><tr><th>字段</th><th>必填</th><th>校验</th><th>原因</th></tr></thead>
              <tbody>{field_rows or '<tr><td colspan="4">暂无字段清单；请先重建校验工作台。</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="table-scroll stacked-table compact" style="margin-top:12px;">
        <table>
          <thead><tr><th>Rank</th><th>下一批比赛</th><th>优先级</th><th>原因</th></tr></thead>
          <tbody>{next_batch_rows or '<tr><td colspan="4">没有剩余批次；请复核 hash gate、overlay preview 和签名。</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll stacked-table compact" style="margin-top:12px;">
        <table>
          <thead><tr><th>Rank</th><th>比赛</th><th>质量状态</th><th>缺字段</th><th>缺方向</th><th>下一步</th></tr></thead>
          <tbody>{quality_rows or '<tr><td colspan="6">暂无下一批质量诊断；请先重建校验工作台。</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">下一批摘要：{esc(next_batch_summary.get('batch_id') or next_batch.get('batch_id') or 'none')}，{esc(next_batch_summary.get('event_count') or next_batch.get('event_count') or 0)} 场，需填写 {esc(next_batch_summary.get('pair_rows_required') or pair_templates.get('next_batch_pair_rows', 0))} 行，高优先级 {esc(next_batch_summary.get('high_priority_count', 0))} 场。</p>
      <p class="note">质量诊断：{esc(quality_gate_summary.get('next_action') or '等待人工导入。')}</p>
      <p class="note">校验工作台下一步：{esc(manual_workbench.get('recommended_next_action') or '等待人工导入。')}</p>
      <p class="note">成对模板：下一批 `{esc(pair_templates.get('next_batch_csv') or 'provider_manual_next_batch_pair_template_latest.csv')}`，全量 `{esc(pair_templates.get('all_candidates_csv') or 'provider_manual_pair_template_latest.csv')}`；模板只预留 Over/Under 行，不代表已取得 TAB 盘口。</p>
      <p class="note">Hash Gate 下一步：{esc(hash_gate.get('recommended_next_action') or '等待人工导入。')}</p>
      <p class="note">Overlay 下一步：{esc(overlay_preview.get('recommended_next_action') or '等待人工导入。')}</p>
      <p class="note">发布预检下一步：{esc(overlay_publish_preflight.get('next_safe_action') or '等待人工导入。')}</p>
      <p class="note">Overlay发布下一步：{esc(overlay_publish.get('next_safe_action') or '未运行 publish_provider_manual_overlay.py；签名通过后才允许显式发布 Matches raw。')}</p>
      <p class="note">边界：{esc(payload.get('truthfulness_note'))} {esc(hash_gate.get('truthfulness_note') or '')}</p>
    </section>
    """


def recommendation_operation_row_html(item: dict[str, Any]) -> str:
    action_class = str(item.get("action_class") or "watch")
    original_action_class = str(item.get("original_action_class") or action_class)
    is_research_buy = action_class == "buy" or original_action_class == "buy"
    action_cell_class = "buy-cell" if is_research_buy else "watch-cell"
    action_hint = (
        '<small class="action-hint buy-hint">原买入</small>'
        if is_research_buy and action_class != "buy"
        else ""
    )
    diagnostic = item.get("decision_diagnostics") or {}
    calibration = item.get("model_calibration") or {}
    funding = item.get("market_funding") or {}
    return (
        "<tr>"
        f"<td>{esc(item.get('time'))}</td>"
        f"<td>{esc(item.get('board'))}<br><span>{esc(item.get('live_board_scope_label', '当前可研究'))}</span></td>"
        f"<td>{esc(item.get('event'))}<br><span>{esc(item.get('market'))}</span></td>"
        f"<td>{esc(item.get('selection'))}</td>"
        f"<td>{esc(item.get('odds'))}</td>"
        f"<td>{esc(decimal(diagnostic.get('minimum_acceptable_odds')))}<br><span>缓冲 {esc(decimal_signed(diagnostic.get('odds_buffer')))}</span></td>"
        f"<td>{money(item.get('stake_aud'))}</td>"
        f"<td>{money(diagnostic.get('expected_profit_aud'))}<br><span>每100 {money(diagnostic.get('expected_profit_per_100_aud'))}</span></td>"
        f"<td class=\"{esc(action_cell_class)}\" data-original-action=\"{esc(item.get('original_action') or item.get('action'))}\"><span class=\"pill {esc(action_class)}\">{esc(item.get('action'))}</span>{action_hint}</td>"
        f"<td>{esc(funding.get('market_funding_tendency_score', '待校准'))}<br><span>{esc(funding.get('market_funding_bias_label', ''))} / 净 {money(funding.get('net_funds_proxy_aud'))}</span></td>"
        f"<td>{esc(pp(item.get('edge')))}<br><span>门槛 {esc(pp(item.get('edge_threshold')))} / 差 {esc(pp(item.get('edge_threshold_gap')))} / {esc(item.get('edge_quality'))}</span></td>"
        f"<td>{esc(pct(item.get('arbitrage_rate'), 2))}<br><span>每100 {money(diagnostic.get('expected_profit_per_100_aud'))}</span></td>"
        f"<td>{esc(pct(item.get('risk_of_ruin'), 2))}<br><span>{esc(item.get('risk_of_ruin_grade'))} / 上限占用 {esc(pct(diagnostic.get('stake_to_cap_ratio')))}</span></td>"
        f"<td>{esc(diagnostic.get('value_signal'))}<br><span>容忍 {esc(pct(diagnostic.get('price_drift_tolerance_pct')))} / 分 {esc(pct(diagnostic.get('risk_adjusted_value_score')))}</span><br><span>{esc((item.get('decision_metric_pack') or {}).get('combined_action', '三指标解释待生成'))}</span></td>"
        f"<td>{esc(pct(item.get('expected_value'), 2))}</td>"
        f"<td>{esc(item.get('confidence'))}</td>"
        f"<td>{esc(calibration.get('consistency_label', '待模型校准'))}<br><span>{esc(calibration.get('review_priority', '待校准'))} / {esc(calibration.get('review_action', '待复核'))}</span></td>"
        "</tr>"
    )


def strategy_performance_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    board_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('board'))}</td>"
        f"<td>{esc(item.get('buy_count', 0))}</td>"
        f"<td>{money(item.get('research_stake_aud'))}</td>"
        f"<td>{money(item.get('expected_profit_aud'))}</td>"
        f"<td>{esc(pct(item.get('stake_weighted_ev'), 2))}</td>"
        f"<td>{esc(pp(item.get('average_edge')))}</td>"
        f"<td>{esc(item.get('outcome_status'))}</td>"
        "</tr>"
        for item in (payload.get("board_rows") or [])[:8]
    )
    clv_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('metric'))}</td>"
        f"<td>{esc(item.get('status'))}</td>"
        f"<td>{esc(pct(item.get('coverage_rate'), 2))}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("clv_readiness_rows") or [])[:4]
    )
    return f"""
    <section class="strategy-performance" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>策略表现 / CLV / ROI 回测 Dashboard</h2>
          <p class="subtitle">把历史推荐样本、EV/Edge、研究金额、预期收益、CLV/ROI 准备度和新旧变化放在一起；没有真实结算或收盘赔率时显示 outcome_pending，不编造收益。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/strategy_performance_latest.pdf">策略表现 PDF</a>
          <a class="action secondary" href="app_assets/strategy_performance_latest.json">JSON</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>回测状态</span><strong>{esc(executive.get('status'))}</strong></div>
        <div class="insight"><span>历史推荐</span><strong>{esc(summary.get('recommendation_count', 0))}</strong></div>
        <div class="insight"><span>买入样本</span><strong>{esc(summary.get('buy_recommendation_count', 0))}</strong></div>
        <div class="insight"><span>研究金额</span><strong>{money(summary.get('research_stake_aud'))}</strong></div>
        <div class="insight"><span>预期收益</span><strong>{money(summary.get('expected_profit_aud'))}</strong></div>
        <div class="insight"><span>加权 EV</span><strong>{esc(pct(summary.get('stake_weighted_ev'), 2))}</strong></div>
        <div class="insight"><span>真实 ROI</span><strong>{esc(summary.get('realized_roi_status'))}</strong></div>
        <div class="insight"><span>CLV</span><strong>{esc(summary.get('clv_tracking_status'))}</strong></div>
        <div class="insight"><span>回测准备度</span><strong>{esc(pct(summary.get('backtest_readiness_score'), 2))}</strong></div>
        <div class="insight"><span>新旧变化</span><strong>{esc(compare.get('status'))} · stake Δ {money(compare.get('stake_delta_aud', 0))}</strong></div>
      </div>
      <p class="note">{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>板块</th><th>买入样本</th><th>研究金额</th><th>预期收益</th><th>加权EV</th><th>平均Edge</th><th>结果</th></tr></thead>
          <tbody>{board_rows or '<tr><td colspan="7">暂无策略表现样本</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact stacked-table">
        <table>
          <thead><tr><th>复盘指标</th><th>状态</th><th>覆盖率</th><th>下一步</th></tr></thead>
          <tbody>{clv_rows or '<tr><td colspan="4">暂无 CLV/ROI 准备度数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def report_evolution_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    catalog = payload.get("catalog_compare") or {}
    signal_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('signal'))}</td>"
        f"<td>{esc(item.get('status'))}</td>"
        f"<td>{esc(item.get('current_value'))}</td>"
        f"<td>{esc(item.get('old_new_status'))}</td>"
        f"<td>{esc(item.get('risk_note'))}</td>"
        "</tr>"
        for item in (payload.get("signal_rows") or [])[:6]
    )
    catalog_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td>{esc(item.get('current_status'))}</td>"
        f"<td>{esc(item.get('previous_status'))}</td>"
        f"<td>{esc(pp(item.get('score_delta')))}</td>"
        f"<td>{esc(item.get('chart_delta', 0))}</td>"
        f"<td>{esc(item.get('table_delta', 0))}</td>"
        "</tr>"
        for item in (catalog.get("rows") or [])[:8]
    )
    return f"""
    <section class="report-evolution" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>新旧报告变化总控台</h2>
          <p class="subtitle">把日报 diff、报告目录、推荐操作、策略表现和产品完成度变化合并成跨报告族 Dashboard；用于每日 automation 复盘，不自动下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/report_evolution_latest.pdf">变化总控 PDF</a>
          <a class="action secondary" href="app_assets/report_evolution_latest.json">JSON</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>总控状态</span><strong>{esc(executive.get('status'))}</strong></div>
        <div class="insight"><span>Evolution 得分</span><strong>{esc(pct(summary.get('evolution_score'), 2))}</strong></div>
        <div class="insight"><span>日报 diff</span><strong>{esc(summary.get('report_diff_count', 0))}</strong></div>
        <div class="insight"><span>报告族</span><strong>{esc(summary.get('current_report_family_count', 0))}</strong></div>
        <div class="insight"><span>新旧覆盖</span><strong>{esc(summary.get('old_new_compare_count', 0))} / {esc(summary.get('current_report_family_count', 0))}</strong></div>
        <div class="insight"><span>目录变化</span><strong>{esc(catalog.get('status'))} · Δ {esc(catalog.get('report_count_delta', 0))}</strong></div>
        <div class="insight"><span>变动报告</span><strong>{esc(catalog.get('changed_report_count', 0))}</strong></div>
        <div class="insight"><span>首要缺口</span><strong>{esc(executive.get('primary_gap'))}</strong></div>
      </div>
      <p class="note">{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>信号</th><th>状态</th><th>当前值</th><th>新旧状态</th><th>风险说明</th></tr></thead>
          <tbody>{signal_rows or '<tr><td colspan="5">暂无业务信号变化</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact stacked-table">
        <table>
          <thead><tr><th>报告</th><th>当前</th><th>上次</th><th>得分变化</th><th>图表Δ</th><th>附表Δ</th></tr></thead>
          <tbody>{catalog_rows or '<tr><td colspan="6">暂无报告目录对比</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def product_readiness_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('title'))}</td>"
        f"<td><span class=\"status {html_status_class(trace_status_class(item.get('status')))}\">{esc(trace_status_label(item.get('status')))}</span></td>"
        f"<td>{esc(pct(item.get('score'), 2))}</td>"
        f"<td>{esc(item.get('evidence'))}</td>"
        f"<td>{esc(item.get('user_takeaway'))}</td>"
        f"<td>{esc(item.get('value_over_static_report'))}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("rows") or [])
    )
    return f"""
    <section class="product-readiness" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>产品完成度 Dashboard</h2>
          <p class="subtitle">从你的使用目标出发，验收系统是否已经比静态报告更有价值：推荐下注首页、可视化报告、开源模型、数据库新旧对比、主动测试、持仓收益率和 automation 准入。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/product_readiness_dashboard_latest.pdf">完成度 PDF</a>
          <a class="action secondary" href="app_assets/product_readiness_dashboard_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>产品状态</span><strong>{esc(trace_status_label(executive.get('status')))}</strong></div>
        <div class="insight"><span>完成度得分</span><strong>{esc(pct(executive.get('product_readiness_score'), 2))}</strong></div>
        <div class="insight"><span>Ready / Partial / Blocked</span><strong>{esc(summary.get('ready_count', 0))} / {esc(summary.get('partial_count', 0))} / {esc(summary.get('blocked_count', 0))}</strong></div>
        <div class="insight"><span>当前可执行新增金额</span><strong>{money(summary.get('current_executable_new_stake_aud') or 0)}</strong></div>
        <div class="insight"><span>首页下注体验</span><strong>{'已就绪' if summary.get('homepage_ready') else '需增强'}</strong></div>
        <div class="insight"><span>数据库</span><strong>{'已写入' if summary.get('database_ready') else '未就绪'}</strong></div>
        <div class="insight"><span>新旧变化</span><strong>{esc(compare.get('status'))} · Δ {esc(compare.get('score_delta', 0))}</strong></div>
        <div class="insight"><span>首要动作</span><strong>{esc(executive.get('primary_user_action'))}</strong></div>
      </div>
      <p class="note">下一步：{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>能力</th><th>状态</th><th>得分</th><th>证据</th><th>用户结论</th><th>相对静态报告价值</th><th>下一步</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="7">暂无产品完成度数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def report_visual_inventory_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td>{esc(item.get('status'))}</td>"
        f"<td>{esc(pct(item.get('score'), 2))}</td>"
        f"<td>{esc(item.get('chart_count', 0))}</td>"
        f"<td>{esc(item.get('table_count', 0))}</td>"
        f"<td>{'有' if item.get('has_old_new_compare') else '缺'}</td>"
        f"<td>{'有' if item.get('has_database_snapshot') else '缺'} / {esc(item.get('database_snapshot_count', 0))}</td>"
        f"<td>{'有' if item.get('has_automation_view') else '缺'}</td>"
        f"<td>{'有' if item.get('has_github_reference') else '缺'}</td>"
        f"<td>{esc(item.get('gap_severity'))}</td>"
        f"<td>{esc(item.get('publish_action') or item.get('next_action'))}</td>"
        "</tr>"
        for item in sorted(payload.get("rows") or [], key=lambda row: (0 if row.get("gap_severity") == "阻塞" else 1 if row.get("gap_severity") == "需增强" else 2, -float(row.get("score") or 0)))[:10]
    )
    top_gaps = " / ".join(
        f"{item.get('capability')} {item.get('count')}"
        for item in (summary.get("top_gap_capabilities") or [])[:4]
        if isinstance(item, dict)
    ) or "无"
    return f"""
    <section class="visual-inventory" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>报表决策矩阵覆盖</h2>
          <p class="subtitle">从原报表可视化覆盖升级为决策矩阵：检查所有公开报告是否包含图表、表格、Dashboard、自动化状态、新旧对比、数据库保存和 GitHub 开源模型参考。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/report_visual_inventory_latest.pdf">覆盖审计 PDF</a>
          <a class="action secondary" href="app_assets/report_visual_inventory_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>报告族</span><strong>{esc(summary.get("report_count", 0))}</strong></div>
        <div class="insight"><span>带图表</span><strong>{esc(summary.get("reports_with_charts", 0))}</strong></div>
        <div class="insight"><span>带新旧对比</span><strong>{esc(summary.get("old_new_compare_count", 0))}</strong></div>
        <div class="insight"><span>已入库</span><strong>{esc(summary.get("database_saved_count", 0))}</strong></div>
        <div class="insight"><span>矩阵就绪</span><strong>{esc(summary.get("decision_matrix_ready_count", 0))}</strong><small>阻塞 {esc(summary.get("blocking_gap_count", 0))}</small></div>
        <div class="insight"><span>带 Automation 状态</span><strong>{esc(summary.get("automation_view_count", 0))}</strong></div>
        <div class="insight"><span>平均覆盖得分</span><strong>{esc(pct(summary.get("average_score"), 2))}</strong></div>
      </div>
      <p class="note">Top缺口：{esc(top_gaps)}。矩阵就绪代表该报告同时有图表/附表/入口/新旧对比/automation状态/数据库保存，才适合进入每日automation日报链路。</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>报告</th><th>状态</th><th>得分</th><th>图表</th><th>附表</th><th>对比</th><th>入库</th><th>Automation</th><th>GitHub</th><th>缺口</th><th>动作</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="11">暂无覆盖审计数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def goal_traceability_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('title'))}</td>"
        f"<td><span class=\"status {html_status_class(trace_status_class(item.get('status')))}\">{esc(trace_status_label(item.get('status')))}</span></td>"
        f"<td>{esc(pct(item.get('score'), 2))}</td>"
        f"<td>{esc(item.get('evidence'))}</td>"
        f"<td>{esc(item.get('user_value'))}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("rows") or [])[:12]
    )
    source = payload.get("source_trace") or {}
    source_text = " / ".join(item.get("name", "") for item in (source.get("available_sources") or [])[:4]) or "待同步"
    return f"""
    <section class="goal-traceability" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>目标验收追踪</h2>
          <p class="subtitle">把你的原始目标拆成可审计条目：需求来源、GitHub模型、图表/Dashboard、PDF/数据库、新旧对比、首页下注决策、主动测试和 automation 门禁。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/goal_traceability_latest.pdf">目标追踪 PDF</a>
          <a class="action secondary" href="app_assets/goal_traceability_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>总状态</span><strong>{esc(trace_status_label(executive.get('status')))}</strong></div>
        <div class="insight"><span>总得分</span><strong>{esc(pct(executive.get('overall_score'), 2))}</strong></div>
        <div class="insight"><span>Ready / Partial / Blocked</span><strong>{esc(summary.get('ready_count', 0))} / {esc(summary.get('partial_count', 0))} / {esc(summary.get('blocked_count', 0))}</strong></div>
        <div class="insight"><span>首要缺口</span><strong>{esc(executive.get('primary_gap'))}</strong></div>
        <div class="insight"><span>新旧追踪</span><strong>{esc(compare.get('status'))} · Δ {esc(compare.get('score_delta', 0))}</strong></div>
        <div class="insight"><span>需求来源</span><strong>{esc(source_text)}</strong></div>
      </div>
      <p class="note">下一步：{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>目标项</th><th>状态</th><th>得分</th><th>证据</th><th>用户价值</th><th>下一步</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="6">暂无目标追踪数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def position_monitor_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    preflight = payload.get("private_preflight") or {}
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('label'))}</td>"
        f"<td><span class=\"status {html_status_class(bool(item.get('ready')))}\">{esc(item.get('status'))}</span></td>"
        f"<td>{'是' if item.get('ready') else '否'}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("monitor_rows") or [])[:8]
    )
    return f"""
    <section class="position-monitor" id="position-monitor" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>持仓监控 Dashboard</h2>
          <p class="subtitle">监控已下注持仓、余额和累计收益率的更新条件。公开入口只显示聚合状态和下一步，不展示账户余额或逐笔下注。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/position_monitor_latest.pdf">持仓监控 PDF</a>
          <a class="action secondary" href="app_assets/position_monitor_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>当前状态</span><strong>{esc(trace_status_label(executive.get('status')))}</strong></div>
        <div class="insight"><span>检查日期</span><strong>{esc(report_date_label(str(summary.get('report_date') or '')))}</strong></div>
        <div class="insight"><span>快照 Ready</span><strong>{'是' if summary.get('snapshot_ready') else '否'}</strong></div>
        <div class="insight"><span>余额</span><strong>{esc(summary.get('public_visible_balance', 'account-update-pending'))}</strong></div>
        <div class="insight"><span>持仓金额</span><strong>{esc(summary.get('public_visible_open_exposure', 'account-update-pending'))}</strong></div>
        <div class="insight"><span>累计收益率</span><strong>{esc(summary.get('public_visible_realized_roi', 'account-update-pending'))}</strong></div>
        <div class="insight"><span>只读 Preflight</span><strong>{esc(summary.get('preflight_status', preflight.get('status', 'missing')))}</strong><small>{esc(summary.get('preflight_blocking_reason', preflight.get('blocking_reason', '')))}</small></div>
        <div class="insight"><span>授权窗口</span><strong>{'需要' if summary.get('login_window_required') else '不需要'}</strong><small>{esc(summary.get('wait_for_login_seconds', preflight.get('wait_for_login_seconds', 0)))} 秒等待</small></div>
        <div class="insight"><span>新旧状态</span><strong>{esc(compare.get('summary'))}</strong></div>
        <div class="insight"><span>下一步</span><strong>{esc(executive.get('recommended_next_action'))}</strong></div>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>项目</th><th>状态</th><th>Ready</th><th>下一步</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="4">暂无持仓监控数据</td></tr>'}</tbody>
        </table>
      </div>
      <p class="note">显示策略：{esc((payload.get('private_metric_policy') or {}).get('public_outputs'))}</p>
    </section>
    """


def trace_status_class(value: Any) -> Any:
    if value == "ready":
        return True
    if value == "blocked":
        return "blocked"
    return "watch"


def trace_status_label(value: Any) -> str:
    return {
        "ready": "已完成",
        "partial": "部分完成",
        "blocked": "阻塞",
        "in_progress": "持续优化中",
    }.get(str(value or ""), text(value))


def automation_maturity_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('title'))}</td>"
        f"<td><span class=\"status {html_status_class(item.get('status'))}\">{esc(item.get('status'))}</span></td>"
        f"<td>{esc(pct(item.get('score'), 2))}</td>"
        f"<td>{esc(item.get('evidence'))}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("rows") or [])[:13]
    )
    queue_rows = "\n".join(
        f"<tr><td>{esc(item.get('title'))}</td><td>{esc(item.get('gap'))}</td><td>{esc(item.get('user_value'))}</td></tr>"
        for item in (payload.get("manual_review_queue") or [])[:6]
    )
    playbook_rows = "\n".join(
        "<tr>"
        f"<td><span class=\"status {html_status_class(item.get('status'))}\">{esc(item.get('priority'))}</span></td>"
        f"<td>{esc(item.get('order'))}</td>"
        f"<td>{esc(item.get('title'))}</td>"
        f"<td>{esc(item.get('action'))}</td>"
        f"<td>{esc(item.get('verify'))}</td>"
        f"</tr>"
        for item in (payload.get("automation_recovery_playbook") or [])[:5]
    )
    return f"""
    <section class="maturity" id="automation-maturity" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Automation 成熟度验收</h2>
          <p class="subtitle">按最终目标逐项检查：自动爬虫、4小时节奏、每日PDF、本地数据库、新旧对比、图表/Dashboard、开源模型、推荐首页、持仓监控和安全边界。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/automation_maturity_latest.pdf">成熟度 PDF</a>
          <a class="action secondary" href="app_assets/automation_maturity_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>Automation ready</span><strong>{'是' if executive.get('automation_ready') else '否'}</strong></div>
        <div class="insight"><span>总得分</span><strong>{esc(pct(summary.get('average_score'), 2))}</strong></div>
        <div class="insight"><span>已就绪</span><strong>{esc(summary.get('required_ready_count', 0))}/{esc(summary.get('required_count', 0))}</strong></div>
        <div class="insight"><span>P0 阻塞</span><strong>{esc(summary.get('p0_blocker_count', 0))}</strong></div>
        <div class="insight"><span>首要缺口</span><strong>{esc(executive.get('primary_gap'))}</strong></div>
        <div class="insight"><span>新旧变化</span><strong>{esc(compare.get('status', 'none'))} · Δ {esc(compare.get('score_delta', 0))}</strong></div>
      </div>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>验收项</th><th>状态</th><th>得分</th><th>证据</th><th>下一步</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="5">暂无成熟度验收数据</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">人工复核队列</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>验收项</th><th>缺口</th><th>用户价值</th></tr></thead>
          <tbody>{queue_rows or '<tr><td colspan="3">当前无阻塞项</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">Automation 恢复 Playbook</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>优先级</th><th>步骤</th><th>动作</th><th>恢复动作</th><th>验证证据</th></tr></thead>
          <tbody>{playbook_rows or '<tr><td colspan="5">暂无恢复队列</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def private_position_action_html(readiness: dict[str, Any]) -> str:
    bootstrap = readiness.get("private_position_bootstrap") or {}
    files = bootstrap.get("files") or {}
    profile = bootstrap.get("profile") or {}
    preflight = bootstrap.get("preflight") or {}
    status = str(bootstrap.get("status") or "待同步")
    ready = bool(bootstrap.get("ready"))
    if ready:
        next_step = "私有持仓快照已就绪。可以重跑日报门禁，若其他门禁通过即可发布正式报告。"
    elif status == "raw_ready_import_needed":
        next_step = "已读取 raw text，但尚未导入快照。点击重跑日报门禁前建议先运行导入链；runner 会继续 fail-closed。"
    elif status == "profile_login_required":
        next_step = "需要建立或刷新 TAB 授权状态。点击只读持仓读取后，在打开的 TAB 窗口完成授权。"
    else:
        next_step = "尚未形成可用快照。优先启动只读持仓读取；完成后系统会重跑日报门禁。"
    return f"""
    <section class="private-actions" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>持仓读取与日报发布</h2>
          <p class="subtitle">当前正式报告被私有持仓快照挡住。这里把建立授权、导入快照、重跑日报门禁收进同一个本地流程。</p>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight">
          <span>持仓快照</span>
          <strong>{'已就绪' if ready else '未就绪'}</strong>
        </div>
        <div class="insight">
          <span>检查日期</span>
          <strong>{esc(report_date_label(str(bootstrap.get("report_date") or "")))}</strong>
        </div>
        <div class="insight">
          <span>专用 profile</span>
          <strong>{'已建立' if profile.get("exists") else '未建立'}</strong>
        </div>
        <div class="insight">
          <span>读取链</span>
          <strong>raw {'有' if files.get("raw_text_exists") else '缺'} / snapshot {'有' if files.get("snapshot_exists") else '缺'}</strong>
        </div>
        <div class="insight">
          <span>Preflight 阻塞</span>
          <strong>{esc(preflight.get("blocking_reason", status))}</strong>
          <small>{esc(preflight.get("next_safe_action", next_step))}</small>
        </div>
        <div class="insight">
          <span>只读授权窗口</span>
          <strong>{'需要' if preflight.get("login_window_required") else '不需要'}</strong>
          <small>等待 {esc(preflight.get("wait_for_login_seconds", 600))} 秒 · {esc(preflight.get("capture_mode", "headed_read_only_authorized_profile"))}</small>
        </div>
      </div>
      <div class="button-row">
        <button id="privateBootstrapButton" class="action primary" type="button">启动只读持仓读取</button>
        <button id="dailyReportButton" class="action secondary" type="button">重跑日报门禁</button>
      </div>
      <div id="privateMessage" class="message">{esc(next_step)}</div>
      <p class="note">凭据策略：{esc(preflight.get("credential_policy", "不读取、不保存、不填写账号密码或OTP；只复用用户授权的本机 profile。"))}</p>
      <p class="note">安全边界：{esc(preflight.get("automation_boundary", "本流程只读取并生成研究报告，不点击赔率、不提交投注、不创建 recurring automation。"))}</p>
    </section>
    """


def raw_refresh_action_html(raw_health: dict[str, Any], readiness: dict[str, Any]) -> str:
    ready = bool(raw_health.get("ready"))
    status = str(raw_health.get("status") or "待同步")
    ready_count = raw_health.get("ready_required_target_count") or raw_health.get("ready_required") or "待同步"
    blocker_codes = raw_health.get("blocker_codes") or []
    readiness_raw = readiness.get("raw_refresh") or {}
    partial = normalize_partial_research_refresh(raw_health.get("partial_research_refresh") or {})
    partial_success = int(partial.get("successful_board_count") or 0)
    partial_attempted = int(partial.get("attempted_board_count") or 0)
    partial_freshness = text(partial.get("freshness_status"), "missing")
    partial_age = partial.get("age_hours")
    partial_sla = partial.get("freshness_sla_hours") or raw_health.get("max_raw_age_hours") or 4
    partial_success_names = "、".join(
        str(item.get("name") or item.get("board_id") or "") for item in (partial.get("successful_boards") or [])[:4]
    ) or "暂无"
    partial_failed_names = "、".join(
        str(item.get("name") or item.get("board_id") or "") for item in (partial.get("failed_boards") or [])[:4]
    ) or "暂无"
    if ready:
        next_step = "公开盘口 raw 当前可用。若持仓快照也就绪，可以重跑日报门禁。"
    elif blocker_codes:
        next_step = "公开盘口 raw 当前不可用。TAB 拒绝 AI controlled access；停止 headed 自动刷新，等待授权数据源或用户导出导入。"
    else:
        next_step = "公开盘口状态不完整。先接入授权 raw 或导入用户导出快照，再重跑日报门禁。"
    blocker_text = "、".join(str(item) for item in blocker_codes[:4]) or str(readiness_raw.get("status") or status)
    return f"""
    <section class="raw-actions" id="raw-refresh" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>公开盘口刷新</h2>
          <p class="subtitle">自动报告需要新鲜公开盘口 raw。TAB 拒绝 AI controlled access 时，系统不做自动抓取绕过，只接受授权数据源或用户导出导入。</p>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight">
          <span>Raw 状态</span>
          <strong>{'可用' if ready else '阻塞'}</strong>
        </div>
        <div class="insight">
          <span>覆盖板块</span>
          <strong>{esc(ready_count)}</strong>
        </div>
        <div class="insight">
          <span>状态码</span>
          <strong>{esc(status)}</strong>
        </div>
        <div class="insight">
          <span>研究可用</span>
          <strong>{esc(partial_success)}/{esc(partial_attempted)}</strong>
        </div>
        <div class="insight">
          <span>Partial freshness</span>
          <strong>{esc(partial_freshness)}</strong>
          <small>age {esc(partial_age if partial_age is not None else 'n/a')}h / SLA {esc(partial_sla)}h</small>
        </div>
        <div class="insight">
          <span>当前研究证据</span>
          <strong>{'可用' if partial.get('current_research_only_allowed') else '不可用'}</strong>
          <small>历史证据 {'有' if partial.get('historical_research_evidence_available') else '无'}</small>
        </div>
        <div class="insight">
          <span>研究-only板块</span>
          <strong>{esc(partial_success_names)}</strong>
          <small>失败：{esc(partial_failed_names)}</small>
        </div>
        <div class="insight">
          <span>阻塞类型</span>
          <strong>{esc(blocker_text)}</strong>
        </div>
      </div>
      <div class="button-row">
        <button id="rawRefreshButton" class="action primary" type="button">检查Raw合规状态</button>
      </div>
      <div id="rawMessage" class="message">{esc(next_step)}</div>
      <p class="note">TAB 拒绝 AI controlled access 时，本系统不使用 headed fallback、验证码绕过、指纹伪装或 stealth browser；公开 raw 只能来自官方/授权数据源或用户导出导入。</p>
      <p class="note">Partial raw freshness 只证明部分板块可研究，不解锁正式日报或新增下注；全量 raw/private/preflight 未通过时执行金额仍为 AUD 0。</p>
    </section>
    """


def raw_refresh_recovery_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    repair_validation = payload.get("matches_repair_validation") or {}
    phase_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('title'))}</td>"
        f"<td><span class=\"status {html_status_class(item.get('status'))}\">{esc(item.get('status'))}</span></td>"
        f"<td>{esc(item.get('evidence'))}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("phase_rows") or [])[:8]
    )
    target_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td>{esc(item.get('status'))}</td>"
        f"<td>{'是' if item.get('raw_fresh') else '否'}</td>"
        f"<td>{'是' if item.get('raw_valid') else '否'}</td>"
        f"<td>{esc(', '.join(item.get('blocker_codes') or []))}</td>"
        "</tr>"
        for item in (payload.get("target_rows") or [])[:8]
    )
    queue_rows = "\n".join(
        f"<tr><td>{esc(item.get('rank'))}</td><td>{esc(item.get('display_date'))}</td><td>{esc(item.get('priority_score'))}</td><td>{esc(item.get('reason'))}</td><td>{esc(item.get('mode'))}</td></tr>"
        for item in (payload.get("backfill_queue_preview") or [])[:7]
    )
    retry_rows = "\n".join(
        f"<tr><td>{esc(item.get('rank'))}</td><td>{esc(item.get('scope'))}</td><td>{esc(item.get('trigger'))}</td><td>{esc(item.get('operation'))}</td><td>{esc(item.get('mode'))}</td><td>{esc(item.get('success_gate'))}</td></tr>"
        for item in (payload.get("next_retry_plan") or [])[:4]
    )
    board_matrix_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('priority'))}</td>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td>{esc(item.get('live_nav_status'))}</td>"
        f"<td>{esc(item.get('raw_status'))}</td>"
        f"<td>{esc(item.get('partial_result'))}</td>"
        f"<td>{esc(item.get('attempt_count'))}</td>"
        f"<td>{esc(item.get('staged_validation_error_count', 0))}</td>"
        f"<td>{esc(item.get('repair_validation_status', 'missing'))}</td>"
        f"<td>{esc(item.get('automation_action'))}</td>"
        f"<td>{'是' if item.get('safe_to_retry_now') else '否'}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("board_recovery_matrix") or [])[:5]
    )
    failure_rows = "\n".join(
        f"<tr><td>{esc(item.get('rank'))}</td><td>{esc(item.get('board_id'))}</td><td>{esc(item.get('output'))}</td><td>{esc(item.get('error'))}</td></tr>"
        for item in (payload.get("board_failure_rows") or [])[:5]
    )
    return f"""
    <section class="raw-recovery" id="raw-recovery" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>Raw 恢复与补跑控制台</h2>
          <p class="subtitle">集中显示公开盘口抓取失败原因、最近尝试、5个目标板块状态和补跑队列；raw 未就绪时补跑保持阻断。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/raw_refresh_recovery_latest.pdf">恢复控制台 PDF</a>
          <a class="action secondary" href="app_assets/raw_refresh_recovery_latest.md">Markdown</a>
          <a class="action secondary" href="app_assets/matches_repair_validation_latest.json">修复验证 JSON</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>Raw 状态</span><strong>{esc(executive.get('status'))}</strong></div>
        <div class="insight"><span>Diagnostics</span><strong>{esc(summary.get('diagnostics_status', 'missing'))}</strong><small>interrupted {'是' if summary.get('diagnostics_interrupted') else '否'}</small></div>
        <div class="insight"><span>目标板块</span><strong>{esc(summary.get('ready_required_target_count', 0))}/{esc(summary.get('required_target_count', 0))}</strong></div>
        <div class="insight"><span>AI访问拒绝</span><strong>{esc(summary.get('ai_controlled_access_rejected_attempt_count', summary.get('access_denied_attempt_count', 0)))}/{esc(summary.get('attempt_count', 0))}</strong></div>
        <div class="insight"><span>Route mismatch</span><strong>{esc(summary.get('route_mismatch_attempt_count', 0))}</strong></div>
        <div class="insight"><span>单板失败</span><strong>{esc(summary.get('board_failure_count', 0))}</strong></div>
        <div class="insight"><span>失败后继续</span><strong>{'是' if summary.get('continued_after_board_failure') else '否'}</strong></div>
        <div class="insight"><span>自动raw允许</span><strong>{'是' if summary.get('automated_public_raw_refresh_allowed') else '否'}</strong></div>
        <div class="insight"><span>Live Discovery</span><strong>{esc(summary.get('live_discovery_status', 'missing'))}</strong><small>{esc(summary.get('live_discovery_quality_status', 'missing'))} · ready {'是' if summary.get('live_discovery_ready') else '否'}</small></div>
        <div class="insight"><span>有效研究范围</span><strong>{esc(summary.get('effective_board_scope_research_allowed_count', 0))}/{esc(summary.get('required_target_count', 0))}</strong><small>{esc(summary.get('effective_board_scope_source', 'missing'))} · fallback {'是' if summary.get('effective_board_scope_last_success_fallback_used') else '否'}</small></div>
        <div class="insight"><span>板块恢复矩阵</span><strong>{esc(summary.get('board_recovery_matrix_count', 0))}</strong><small>research-only {esc(summary.get('board_recovery_research_only_ready_count', 0))} / 自动重试 {esc(summary.get('board_recovery_auto_retry_count', 0))} / 访问政策阻断 {esc(summary.get('board_recovery_access_policy_blocked_count', 0))} / validation {esc(summary.get('board_recovery_validation_fix_count', 0))} / staged {esc(summary.get('board_recovery_staged_validation_error_count', 0))} / unavailable {esc(summary.get('board_recovery_unavailable_count', 0))}</small></div>
        <div class="insight"><span>Matches修复验证</span><strong>{esc(summary.get('matches_repair_validation_status', 'missing'))}</strong><small>{esc(summary.get('matches_repair_validation_match_count', 0))}场 / {esc(summary.get('matches_repair_validation_market_count', 0))}盘口 / 错误{esc(summary.get('matches_repair_validation_error_count', 0))}</small></div>
        <div class="insight"><span>补跑队列</span><strong>{esc(summary.get('backfill_queue_count', 0))}</strong></div>
        <div class="insight"><span>首要阻塞</span><strong>{esc(executive.get('primary_blocker'))}</strong></div>
      </div>
      <p class="note">下一步：{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>恢复阶段</th><th>状态</th><th>证据</th><th>下一步</th></tr></thead>
          <tbody>{phase_rows or '<tr><td colspan="4">暂无恢复阶段数据</td></tr>'}</tbody>
        </table>
      </div>
      <div class="table-scroll compact stacked-table">
        <table>
          <thead><tr><th>目标板块</th><th>状态</th><th>fresh</th><th>valid</th><th>blocker</th></tr></thead>
          <tbody>{target_rows or '<tr><td colspan="5">暂无目标板块数据</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">板块级恢复矩阵</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>优先级</th><th>板块</th><th>live</th><th>raw</th><th>partial</th><th>尝试</th><th>staged错误</th><th>修复验证</th><th>动作</th><th>可自动重试</th><th>下一步</th></tr></thead>
          <tbody>{board_matrix_rows or '<tr><td colspan="11">暂无板块级恢复矩阵</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">Matches Repair Live Validation</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>状态</th><th>范围</th><th>触发</th><th>覆盖</th><th>只读保护</th></tr></thead>
          <tbody><tr><td>{esc(repair_validation.get('status', 'missing'))}</td><td>{esc(repair_validation.get('scope', ''))}</td><td>{esc(repair_validation.get('trigger', ''))}</td><td>{esc(repair_validation.get('match_count', 0))}场 / {esc(repair_validation.get('market_count', 0))}盘口 / 错误{esc(repair_validation.get('error_count', 0))}</td><td>{esc(repair_validation.get('read_only_guard', ''))}</td></tr></tbody>
        </table>
      </div>
      <h3 class="subsection-title">单板失败隔离</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>板块</th><th>输出</th><th>错误</th></tr></thead>
          <tbody>{failure_rows or '<tr><td colspan="4">暂无单板失败；若未来某板块失败，系统会继续尝试后续板块并保持全量门禁关闭。</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">下一次刷新计划</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>范围</th><th>触发条件</th><th>操作</th><th>模式</th><th>成功门禁</th></tr></thead>
          <tbody>{retry_rows or '<tr><td colspan="6">暂无刷新计划</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">补跑队列预览</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>日期</th><th>分数</th><th>原因</th><th>模式</th></tr></thead>
          <tbody>{queue_rows or '<tr><td colspan="5">暂无待补跑项</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def live_board_discovery_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    expected_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td><span class=\"status {html_status_class(item.get('live_nav_status') == 'listed')}\">{esc(item.get('live_nav_status'))}</span></td>"
        f"<td>{esc(item.get('matched_link_count', 0))}</td>"
        f"<td>{'是' if item.get('matched_text_marker') else '否'}</td>"
        f"<td>{esc(item.get('automation_decision'))}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("expected_board_rows") or [])[:8]
    )
    queue_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('rank'))}</td>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td>{esc(item.get('reason'))}</td>"
        f"<td>{esc(item.get('operation'))}</td>"
        f"<td>{esc(item.get('success_gate'))}</td>"
        "</tr>"
        for item in (payload.get("unavailable_review_queue") or [])[:8]
    )
    retry_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('rank'))}</td>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td>{esc(item.get('reason'))}</td>"
        f"<td>{esc(item.get('operation'))}</td>"
        f"<td>{esc(item.get('success_gate'))}</td>"
        "</tr>"
        for item in (payload.get("discovery_retry_queue") or [])[:8]
    )
    observed_rows = "\n".join(
        f"<tr><td>{esc(item.get('rank'))}</td><td>{esc(item.get('text'))}</td><td>{esc(item.get('mapped_expected_board'))}</td></tr>"
        for item in (payload.get("observed_world_cup_links") or [])[:10]
    )
    return f"""
    <section class="live-board-discovery" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>TAB Live 访问合规状态</h2>
          <p class="subtitle">TAB 拒绝 AI controlled access 时不再自动读取公开导航；本区只展示合规阻断、已有快照和授权/导入后的板块可用性。</p>
        </div>
        <div class="actions compact-actions">
          <button id="liveDiscoveryButton" class="action primary" type="button">检查Live合规状态</button>
          <a class="action secondary" href="app_assets/live_board_discovery_latest.pdf">Discovery PDF</a>
          <a class="action secondary" href="app_assets/live_board_discovery_latest.md">Markdown</a>
          <div id="liveDiscoveryMessage" class="message priority-message">当前只检查 Live 访问合规状态；不会点击赔率、加入 Bet Slip 或尝试绕过 TAB 拦截。</div>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>Discovery 状态</span><strong>{esc(executive.get('status'))}</strong></div>
        <div class="insight"><span>质量门禁</span><strong>{esc(summary.get('quality_status'))}</strong></div>
        <div class="insight"><span>Expected boards</span><strong>{esc(summary.get('listed_expected_count', 0))}/{esc(summary.get('expected_board_count', 0))}</strong></div>
        <div class="insight"><span>缺失板块</span><strong>{esc(summary.get('missing_expected_count', 0))}</strong></div>
        <div class="insight"><span>Observed links</span><strong>{esc(summary.get('observed_world_cup_link_count', 0))}</strong></div>
        <div class="insight"><span>Route mismatch</span><strong>{'是' if summary.get('route_mismatch_active') else '否'}</strong></div>
        <div class="insight"><span>Unavailable</span><strong>{esc(summary.get('temporarily_unavailable_count', 0))}</strong></div>
        <div class="insight"><span>需重试板块</span><strong>{esc(summary.get('retry_required_count', 0))}</strong></div>
      </div>
      <p class="note">下一步：{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>Expected board</th><th>Live nav</th><th>Links</th><th>Text marker</th><th>Automation decision</th><th>下一步</th></tr></thead>
          <tbody>{expected_rows or '<tr><td colspan="6">暂无 discovery 数据</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">Discovery Retry Queue</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>板块</th><th>原因</th><th>操作</th><th>成功门禁</th></tr></thead>
          <tbody>{retry_rows or '<tr><td colspan="5">当前无需 discovery 重试</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">Unavailable review queue</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>板块</th><th>原因</th><th>操作</th><th>成功门禁</th></tr></thead>
          <tbody>{queue_rows or '<tr><td colspan="5">暂无缺失板块</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">Observed World Cup links</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>链接文本</th><th>映射板块</th></tr></thead>
          <tbody>{observed_rows or '<tr><td colspan="3">暂无 World Cup 链接</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def available_board_strategy_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    allowed_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td><span class=\"status ok\">可研究</span></td>"
        f"<td>{esc(item.get('report_usage'))}</td>"
        f"<td>{esc(item.get('amount_policy'))}</td>"
        f"<td>{esc(item.get('reason'))}</td>"
        "</tr>"
        for item in (payload.get("available_research_boards") or [])[:8]
    )
    excluded_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td><span class=\"status blocked\">排除</span></td>"
        f"<td>{esc(item.get('live_nav_status'))}</td>"
        f"<td>{esc(item.get('amount_policy'))}</td>"
        f"<td>{esc(item.get('next_action'))}</td>"
        "</tr>"
        for item in (payload.get("excluded_boards") or [])[:8]
    )
    compare_text = compare.get("summary") or "暂无上一版对比。"
    status_class = html_status_class(executive.get("status"))
    return f"""
    <section class="available-board-strategy" id="available-board-strategy" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>可用板块策略</h2>
          <p class="subtitle">把 TAB 当前真实可见板块转换为下注研究范围：哪些能继续研究，哪些必须排除，当前是否允许新增执行金额。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/available_board_strategy_latest.pdf">策略 PDF</a>
          <a class="action secondary" href="app_assets/available_board_strategy_latest.json">JSON</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>当前策略</span><strong><span class="status {esc(status_class)}">{esc(strategy_status_label(executive.get('status')))}</span></strong></div>
        <div class="insight"><span>当前动作</span><strong>{esc(executive.get('current_action'))}</strong></div>
        <div class="insight"><span>可研究板块</span><strong>{esc(summary.get('research_allowed_board_count', 0))}/{esc(summary.get('expected_board_count', 0))}</strong></div>
        <div class="insight"><span>排除板块</span><strong>{esc(summary.get('unavailable_board_count', 0))}</strong></div>
        <div class="insight"><span>范围来源</span><strong>{esc(summary.get('board_scope_source', 'missing'))}</strong><small>fallback {'是' if summary.get('last_success_fallback_used') else '否'} · fresh {'是' if summary.get('last_success_fresh_within_sla') else '否'}</small></div>
        <div class="insight"><span>当前发现质量</span><strong>{esc(summary.get('current_discovery_quality_status', 'missing'))}</strong><small>discovery ready {'是' if summary.get('discovery_ready') else '否'}</small></div>
        <div class="insight"><span>新增执行金额</span><strong>{money(summary.get('current_executable_new_stake_aud') or 0)}</strong></div>
        <div class="insight"><span>新旧变化</span><strong>{esc(compare_text)}</strong></div>
        <div class="insight"><span>Raw 门禁</span><strong>{'通过' if summary.get('raw_refresh_ready') else '未通过'}</strong></div>
        <div class="insight"><span>日报发布</span><strong>{'允许' if summary.get('formal_report_publish_ready') else '暂停'}</strong></div>
      </div>
      <p class="note">下一步：{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>可研究板块</th><th>状态</th><th>报告用途</th><th>金额策略</th><th>原因</th></tr></thead>
          <tbody>{allowed_rows or '<tr><td colspan="5">暂无可研究板块</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">排除板块</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>板块</th><th>状态</th><th>Live nav</th><th>金额策略</th><th>下一步</th></tr></thead>
          <tbody>{excluded_rows or '<tr><td colspan="5">暂无排除板块</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def partial_daily_research_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    artifacts = payload.get("artifacts") or {}
    dated_pdf = artifacts.get("dated_pdf") or payload.get("dated_artifacts", {}).get("pdf") or ""
    status_class = "ok" if executive.get("partial_daily_report_ready") else "blocked"
    board_rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('name'))}</td>"
        f"<td>{esc(item.get('live_nav_status'))}</td>"
        f"<td>{esc(item.get('board_scope'))}</td>"
        f"<td>{'是' if item.get('partial_raw_fresh') else '否'}</td>"
        f"<td>{esc(item.get('research_action'))}</td>"
        f"<td><span class=\"status blocked\">{esc(item.get('betting_action'))}</span></td>"
        f"<td>{money(item.get('stake_aud') or 0)}</td>"
        "</tr>"
        for item in (payload.get("board_rows") or [])[:8]
    )
    return f"""
    <section class="partial-daily-research" id="partial-daily-research" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>研究诊断日报</h2>
          <p class="subtitle">当 TAB 部分板块当前不可见时，仍生成每日研究诊断 PDF；缺失板块写 No Bet / unavailable，不使用旧盘口补齐。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action primary" href="app_assets/partial_daily_research_latest.pdf">研究诊断 PDF</a>
          {f'<a class="action secondary" href="app_assets/{esc(dated_pdf)}">日期版 PDF</a>' if dated_pdf else ''}
          <a class="action secondary" href="app_assets/partial_daily_research_latest.json">JSON</a>
          <a class="action secondary" href="app_assets/partial_daily_research_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>日报状态</span><strong><span class="status {esc(status_class)}">{esc(executive.get('status'))}</span></strong></div>
        <div class="insight"><span>Partial Raw</span><strong>{esc(summary.get('partial_successful_board_count', 0))}/{esc(summary.get('partial_attempted_board_count', 0))}</strong></div>
        <div class="insight"><span>Freshness</span><strong>{esc(summary.get('partial_freshness_status'))}</strong><small>age {esc(summary.get('partial_age_hours', 'n/a'))}h</small></div>
        <div class="insight"><span>缺失板块</span><strong>{esc(summary.get('unavailable_board_count', 0))}</strong></div>
        <div class="insight"><span>范围来源</span><strong>{esc(summary.get('board_scope_source', 'missing'))}</strong><small>fallback {'是' if summary.get('board_scope_last_success_fallback_used') else '否'} · current {esc(summary.get('current_discovery_quality_status', 'missing'))}</small></div>
        <div class="insight"><span>执行金额</span><strong>{money(summary.get('current_executable_new_stake_aud') or 0)}</strong></div>
        <div class="insight"><span>诊断状态</span><strong>{esc(summary.get('raw_diagnostics_status'))}</strong></div>
      </div>
      <p class="note">下一步：{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>板块</th><th>Live nav</th><th>范围</th><th>Fresh</th><th>研究动作</th><th>下注动作</th><th>金额</th></tr></thead>
          <tbody>{board_rows or '<tr><td colspan="7">暂无研究诊断行</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def fixture_sanity_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    source = payload.get("source_caveat") or {}
    compare = payload.get("old_new_compare") or {}
    rows = "\n".join(
        "<tr>"
        f"<td>{esc(item.get('status'))}</td>"
        f"<td>{esc(item.get('tab_match') or '无')}</td>"
        f"<td>{esc(item.get('openfootball_match') or '无')}</td>"
        f"<td>{esc(str(item.get('date') or '') + ' ' + str(item.get('time') or ''))}</td>"
        f"<td>{esc(str(item.get('group') or '') + ' ' + str(item.get('round') or ''))}</td>"
        f"<td>{esc(item.get('reason'))}</td>"
        "</tr>"
        for item in (payload.get("comparison_rows") or [])[:10]
    )
    return f"""
    <section class="fixture-sanity" data-source-freshness="delayed_public_source_not_live" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>赛程校验 Dashboard</h2>
          <p class="subtitle">使用 openfootball/worldcup.json 公开赛程交叉检查 TAB Matches raw 的比赛名称、日期、分组、场地和赛果字段；这是延迟公开源，不是 live odds，也不替代 TAB 盘口。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/fixture_sanity_latest.pdf">赛程校验 PDF</a>
          <a class="action secondary" href="app_assets/fixture_sanity_latest.json">JSON</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>校验状态</span><strong>{esc(executive.get('status'))}</strong></div>
        <div class="insight"><span>openfootball 赛程</span><strong>{esc(summary.get('openfootball_match_count', 0))}</strong></div>
        <div class="insight"><span>TAB raw 比赛</span><strong>{esc(summary.get('tab_match_count', 0))}</strong></div>
        <div class="insight"><span>匹配成功</span><strong>{esc(summary.get('matched_count', 0))}</strong></div>
        <div class="insight"><span>Review Queue</span><strong>{esc(summary.get('mismatch_review_count', 0))}</strong></div>
        <div class="insight"><span>公开源时效</span><strong>{esc(summary.get('source_freshness'))}</strong></div>
        <div class="insight"><span>新旧变化</span><strong>{esc(compare.get('status'))} · match Δ {esc(compare.get('matched_count_delta', 0))}</strong></div>
        <div class="insight"><span>GitHub/公开源</span><strong>{esc(source.get('license'))}</strong></div>
      </div>
      <p class="note">限制：{esc(source.get('limitation'))}</p>
      <p class="note">下一步：{esc(executive.get('recommended_next_action'))}</p>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>状态</th><th>TAB比赛</th><th>公开赛程</th><th>日期</th><th>分组/轮次</th><th>原因</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="6">暂无赛程校验数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def active_timeline_report_html(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    recovery = payload.get("backfill_recovery_plan") or {}
    partial = payload.get("partial_daily_research") or {}
    compare = (payload.get("old_new_compare") or {}).get("rows") or []
    queue = payload.get("backfill_queue_rows") or []
    slot_rows = payload.get("slot_rows") or []
    compare_rows = "\n".join(
        f"<tr><td>{esc(item.get('metric'))}</td><td>{esc(item.get('current'))}</td><td>{esc(item.get('previous'))}</td><td>{esc(item.get('delta'))}</td><td>{esc(item.get('direction'))}</td></tr>"
        for item in compare[:5]
    )
    queue_rows = "\n".join(
        f"<tr><td>{esc(item.get('rank'))}</td><td>{esc(item.get('display_date'))}</td><td>{esc(item.get('priority_score'))}</td><td>{esc(item.get('reason'))}</td><td>{esc(item.get('mode'))}</td></tr>"
        for item in queue[:6]
    )
    recovery_rows = "\n".join(
        f"<tr><td>{esc(item.get('rank'))}</td><td>{esc(item.get('display_date'))}</td><td>{esc(item.get('priority_score'))}</td><td>{esc(item.get('reason'))}</td><td>{esc(item.get('action'))}</td><td>{esc(item.get('mode'))}</td></tr>"
        for item in (recovery.get("date_priority_rows") or [])[:6]
    )
    slot_text = " / ".join(
        f"{short_slot(str(item.get('slot') or ''))}: {pct(item.get('coverage_ratio'), 0)}"
        for item in slot_rows[:5]
    ) or "待同步"
    return f"""
    <section class="timeline-dashboard" style="margin-top:16px;">
      <div class="section-head">
        <div>
          <h2>主动测试时间线 Dashboard</h2>
          <p class="subtitle">把每天至少四次分析、每天一份报告、补跑队列和新旧变化合并成一张业务视图。</p>
        </div>
        <div class="actions compact-actions">
          <a class="action secondary" href="app_assets/active_timeline_report_latest.pdf">时间线 PDF</a>
          <a class="action secondary" href="app_assets/active_timeline_report_latest.md">Markdown</a>
        </div>
      </div>
      <div class="insight-grid">
        <div class="insight"><span>状态</span><strong>{esc(executive.get('status'))}</strong></div>
        <div class="insight"><span>检查天数</span><strong>{esc(summary.get('day_count', 0))}</strong></div>
        <div class="insight"><span>完整天数</span><strong>{esc(summary.get('complete_day_count', 0))}</strong></div>
        <div class="insight"><span>分析缺口日</span><strong>{esc(summary.get('missing_analysis_day_count', 0))}</strong></div>
        <div class="insight"><span>日报缺口日</span><strong>{esc(summary.get('missing_report_day_count', 0))}</strong></div>
        <div class="insight"><span>待补队列</span><strong>{esc(summary.get('backfill_queue_count', 0))}</strong></div>
        <div class="insight"><span>恢复状态</span><strong>{esc(recovery.get('status'))}</strong></div>
        <div class="insight"><span>当前可补跑</span><strong>{'是' if recovery.get('safe_to_backfill_now') else '否'}</strong></div>
        <div class="insight"><span>研究诊断补写</span><strong>{esc(partial.get('status', 'missing'))}</strong><small>{'ready' if partial.get('ready') else 'not ready'}</small></div>
        <div class="insight"><span>补写执行金额</span><strong>{money(partial.get('current_executable_new_stake_aud') or 0)}</strong></div>
      </div>
      <p class="note">下一步：{esc(recovery.get('next_unlock_action') or executive.get('recommended_next_action'))}</p>
      <p class="note">安全边界：{esc(recovery.get('safety_boundary'))}</p>
      <p class="note">研究诊断日报补写：{esc(partial.get('report_usage') or '未生成 research-only 补写状态。')} {esc(partial.get('pdf') or '')}</p>
      <p class="note">时段覆盖：{esc(slot_text)}</p>
      <h3 class="subsection-title">补缺恢复计划</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>日期</th><th>分数</th><th>缺口</th><th>动作</th><th>模式</th></tr></thead>
          <tbody>{recovery_rows or '<tr><td colspan="6">当前没有待补跑项</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">补跑优先队列</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>顺序</th><th>日期</th><th>分数</th><th>缺口</th><th>模式</th></tr></thead>
          <tbody>{queue_rows or '<tr><td colspan="5">当前没有待补跑项</td></tr>'}</tbody>
        </table>
      </div>
      <h3 class="subsection-title">新旧审计变化</h3>
      <div class="table-scroll compact">
        <table>
          <thead><tr><th>指标</th><th>当前</th><th>上次</th><th>变化</th><th>方向</th></tr></thead>
          <tbody>{compare_rows or '<tr><td colspan="5">暂无上次审计可比数据</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """


def build_entry_html() -> str:
    latest_commit = load_json(OUTPUT_DIR / "latest_commit.json")
    readiness = load_json(OUTPUT_DIR / "automation_readiness_latest.json")
    runner = load_json(OUTPUT_DIR / "automation_run_latest.json")
    raw_health = load_json(OUTPUT_DIR / "raw_refresh_health_latest.json")
    raw_recovery = load_json(OUTPUT_DIR / "raw_refresh_recovery_latest.json")
    live_discovery = load_json(OUTPUT_DIR / "live_board_discovery_latest.json")
    available_strategy = load_json(OUTPUT_DIR / "available_board_strategy_latest.json")
    partial_daily_research = load_json(OUTPUT_DIR / "partial_daily_research_latest.json")
    fixture_sanity = load_json(OUTPUT_DIR / "fixture_sanity_latest.json")
    report_index = load_json(OUTPUT_DIR / "report_index_latest.json")
    timeline = load_json(OUTPUT_DIR / "active_timeline_latest.json")
    active_timeline_report = load_json(OUTPUT_DIR / "active_timeline_report_latest.json")
    recommendation_operations = load_json(OUTPUT_DIR / "recommendation_operations_latest.json")
    strategy_performance = load_json(OUTPUT_DIR / "strategy_performance_latest.json")
    report_evolution = load_json(OUTPUT_DIR / "report_evolution_latest.json")
    product_readiness = load_json(OUTPUT_DIR / "product_readiness_dashboard_latest.json")
    maturity = load_json(OUTPUT_DIR / "automation_maturity_latest.json")
    goal_traceability = load_json(OUTPUT_DIR / "goal_traceability_latest.json")
    position_monitor = load_json(OUTPUT_DIR / "position_monitor_latest.json")
    provider_config_doctor = load_json(OUTPUT_DIR / "provider_config_doctor_latest.json")
    provider_kpi = load_json(OUTPUT_DIR / "provider_kpi_latest.json")
    provider_alternate_plan = load_json(OUTPUT_DIR / "provider_alternate_plan_latest.json")
    public_snapshot_import = load_json(OUTPUT_DIR / "public_snapshot_import_status_latest.json")
    public_snapshot_publish_preflight = load_json(OUTPUT_DIR / "public_snapshot_import_publish_preflight_latest.json")
    public_snapshot_raw_publish = load_json(OUTPUT_DIR / "public_snapshot_raw_publish_latest.json")
    provider_fallback_verification = load_json(OUTPUT_DIR / "provider_fallback_verification_latest.json")
    provider_manual_verification = load_json(OUTPUT_DIR / "provider_manual_verification_status_latest.json")
    provider_manual_hash_gate = load_json(OUTPUT_DIR / "provider_manual_hash_gate_latest.json")
    provider_manual_overlay_preview = load_json(OUTPUT_DIR / "provider_manual_overlay_preview_latest.json")
    provider_manual_overlay_publish_preflight = load_json(OUTPUT_DIR / "provider_manual_overlay_publish_preflight_latest.json")
    provider_manual_overlay_publish = load_json(OUTPUT_DIR / "provider_manual_overlay_publish_latest.json")
    provider_manual_workbench = load_json(OUTPUT_DIR / "provider_manual_workbench_latest.json")
    intelligence = load_json(OUTPUT_DIR / "report_intelligence_latest.json")
    model_comparison = load_json(OUTPUT_DIR / "tab_fifa_model_comparison_v0_1.json")
    model_divergence_review = load_json(OUTPUT_DIR / "model_divergence_review_latest.json")
    source_model_registry = load_json(OUTPUT_DIR / "source_model_registry_latest.json")
    automation_doctor = load_json(OUTPUT_DIR / "automation_doctor_latest.json")
    visual_inventory = load_json(OUTPUT_DIR / "report_visual_inventory_latest.json")
    pdf_qa = latest_attempt_pdf_qa()
    visual = pdf_qa.get("visual_smoke") or {}
    latest_pdf = latest_pdf_path(latest_commit)
    raw_rec_rows = recommendation_rows(latest_commit)
    execution_allowed = recommendation_execution_allowed(readiness, raw_health)
    gate_message = execution_gate_message(readiness, raw_health)
    rec_rows = apply_execution_gate(raw_rec_rows, execution_allowed=execution_allowed, gate_message=gate_message)
    automation_work_queue = automation_work_queue_from_artifacts(
        provider_kpi=provider_kpi,
        provider_alternate_plan=provider_alternate_plan,
        manual_workbench=provider_manual_workbench,
        provider_config_doctor=provider_config_doctor,
        provider_fallback_verification=provider_fallback_verification,
        provider_manual_overlay_publish_preflight=provider_manual_overlay_publish_preflight,
        provider_manual_overlay_publish=provider_manual_overlay_publish,
        readiness=readiness,
        raw_health=raw_health,
        position_monitor=position_monitor,
    )
    automation_scorecard = automation_scorecard_from_artifacts(
        provider_kpi=provider_kpi,
        provider_alternate_plan=provider_alternate_plan,
        provider_config_doctor=provider_config_doctor,
        automation_work_queue=automation_work_queue,
        position_monitor=position_monitor,
        raw_health=raw_health,
    )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    latest_status = latest_commit.get("status")
    run_store = runner.get("automation_run_store") or {}
    latest_attempt_run = (readiness.get("technical_preflight") or {}).get("run_id") or text((pdf_qa.get("pdf_file") or "").replace(".pdf", ""), "待同步")
    blockers = blocker_summary(readiness)
    blocker_rows = "\n".join(f"<li>{esc(reason)}</li>" for reason in blockers) or "<li>暂无阻塞记录</li>"
    recommended_exposure = latest_commit.get("time_adjusted_new_exposure_aud") if execution_allowed else 0
    buy_count = len([item for item in rec_rows if item.get("action_class") == "buy"])
    first_action = rec_rows[0] if rec_rows else {}
    summary_card_class = "buy" if buy_count else ("blocked" if rec_rows and not execution_allowed else "watch")

    action_links = []
    if latest_pdf:
        action_links.append(("打开可信 PDF", relative_link(latest_pdf), "primary"))
    action_links.extend(
        [
            ("Dashboard", "app_assets/dashboard.html", "secondary"),
            ("Dashboard PDF", "app_assets/tab_fifa_dashboard_latest.pdf", "secondary"),
            ("推荐操作", "app_assets/recommendation_operations_latest.pdf", "secondary"),
            ("Provider配置", "app_assets/provider_config_doctor_latest.pdf", "secondary"),
            ("Provider KPI", "app_assets/provider_kpi_latest.pdf", "secondary"),
            ("补齐计划", "app_assets/provider_alternate_plan_latest.pdf", "secondary"),
            ("Snapshot导入", "app_assets/public_snapshot_import_status_latest.pdf", "secondary"),
            ("Snapshot预检", "app_assets/public_snapshot_import_publish_preflight_latest.pdf", "secondary"),
            ("人工校验队列", "app_assets/provider_fallback_verification_latest.pdf", "secondary"),
            ("人工导入模板", "app_assets/provider_manual_verification_template_latest.csv", "secondary"),
            ("下一批成对模板", "app_assets/provider_manual_next_batch_pair_template_latest.csv", "secondary"),
            ("导入状态", "app_assets/provider_manual_verification_status_latest.pdf", "secondary"),
            ("人工 Hash Gate", "app_assets/provider_manual_hash_gate_latest.pdf", "secondary"),
            ("Overlay预览", "app_assets/provider_manual_overlay_preview_latest.pdf", "secondary"),
            ("发布预检", "app_assets/provider_manual_overlay_publish_preflight_latest.pdf", "secondary"),
            ("Overlay发布", "app_assets/provider_manual_overlay_publish_latest.pdf", "secondary"),
            ("校验工作台", "app_assets/provider_manual_workbench_latest.pdf", "secondary"),
            ("策略表现", "app_assets/strategy_performance_latest.pdf", "secondary"),
            ("新旧总控", "app_assets/report_evolution_latest.pdf", "secondary"),
            ("主动测试", "app_assets/active_timeline_report_latest.pdf", "secondary"),
            ("Raw 恢复", "app_assets/raw_refresh_recovery_latest.pdf", "secondary"),
            ("Live 板块", "app_assets/live_board_discovery_latest.pdf", "secondary"),
            ("可用板块", "app_assets/available_board_strategy_latest.pdf", "secondary"),
            ("研究诊断日报", "app_assets/partial_daily_research_latest.pdf", "secondary"),
            ("赛程校验", "app_assets/fixture_sanity_latest.pdf", "secondary"),
            ("产品完成度", "app_assets/product_readiness_dashboard_latest.pdf", "secondary"),
            ("目标追踪", "app_assets/goal_traceability_latest.pdf", "secondary"),
            ("持仓监控", "app_assets/position_monitor_latest.pdf", "secondary"),
            ("开源模型", "app_assets/tab_fifa_model_comparison_v0_1.pdf", "secondary"),
            ("模型分歧复核", "app_assets/model_divergence_review_latest.pdf", "secondary"),
            ("开源模型库", "app_assets/source_model_registry_latest.pdf", "secondary"),
            ("自动化就绪", "app_assets/automation_readiness_latest.pdf", "secondary"),
            ("报告历史", "app_assets/report_index_latest.pdf", "secondary"),
            ("报表覆盖", "app_assets/report_visual_inventory_latest.pdf", "secondary"),
        ]
    )
    action_buttons = "\n".join(
        f'<a class="action {kind}" href="{href}">{esc(label)}</a>' for label, href, kind in action_links
    )

    artifacts = [
        ("可信最新报告", relative_link(latest_pdf) if latest_pdf else "", latest_pdf.name if latest_pdf else "待同步"),
        ("Dashboard", "app_assets/dashboard.html", "tab_fifa_dashboard_latest.html"),
        ("Dashboard PDF", "app_assets/tab_fifa_dashboard_latest.pdf", "tab_fifa_dashboard_latest.pdf"),
        ("Dashboard Markdown", "app_assets/tab_fifa_dashboard_latest.md", "tab_fifa_dashboard_latest.md"),
        ("推荐操作 Dashboard", "app_assets/recommendation_operations_latest.pdf", "recommendation_operations_latest.pdf"),
        ("推荐操作 JSON", "app_assets/recommendation_operations_latest.json", "recommendation_operations_latest.json"),
        ("推荐操作 Markdown", "app_assets/recommendation_operations_latest.md", "recommendation_operations_latest.md"),
        ("Provider 配置医生", "app_assets/provider_config_doctor_latest.pdf", "provider_config_doctor_latest.pdf"),
        ("Provider 配置医生 JSON", "app_assets/provider_config_doctor_latest.json", "provider_config_doctor_latest.json"),
        ("Provider 配置医生 Markdown", "app_assets/provider_config_doctor_latest.md", "provider_config_doctor_latest.md"),
        ("Provider KPI", "app_assets/provider_kpi_latest.pdf", "provider_kpi_latest.pdf"),
        ("Provider KPI JSON", "app_assets/provider_kpi_latest.json", "provider_kpi_latest.json"),
        ("Provider KPI Markdown", "app_assets/provider_kpi_latest.md", "provider_kpi_latest.md"),
        ("Provider 补齐计划", "app_assets/provider_alternate_plan_latest.pdf", "provider_alternate_plan_latest.pdf"),
        ("Provider 补齐计划 JSON", "app_assets/provider_alternate_plan_latest.json", "provider_alternate_plan_latest.json"),
        ("Provider 补齐计划 Markdown", "app_assets/provider_alternate_plan_latest.md", "provider_alternate_plan_latest.md"),
        ("Provider Probe Evidence", "app_assets/provider_alternate_probe_evidence_latest.json", "provider_alternate_probe_evidence_latest.json"),
        ("Public Snapshot 导入状态", "app_assets/public_snapshot_import_status_latest.pdf", "public_snapshot_import_status_latest.pdf"),
        ("Public Snapshot 导入状态 JSON", "app_assets/public_snapshot_import_status_latest.json", "public_snapshot_import_status_latest.json"),
        ("Public Snapshot 导入状态 Markdown", "app_assets/public_snapshot_import_status_latest.md", "public_snapshot_import_status_latest.md"),
        ("Public Snapshot 导入模板", "app_assets/public_snapshot_import_manifest_template_latest.json", "public_snapshot_import_manifest_template_latest.json"),
        ("Public Snapshot Preview Raw", "app_assets/public_snapshot_import_preview_raw_latest.json", "public_snapshot_import_preview_raw_latest.json"),
        ("Public Snapshot 签名模板", "app_assets/public_snapshot_import_approval_template_latest.json", "public_snapshot_import_approval_template_latest.json"),
        ("Public Snapshot 发布预检", "app_assets/public_snapshot_import_publish_preflight_latest.pdf", "public_snapshot_import_publish_preflight_latest.pdf"),
        ("Public Snapshot 发布预检 JSON", "app_assets/public_snapshot_import_publish_preflight_latest.json", "public_snapshot_import_publish_preflight_latest.json"),
        ("Public Snapshot 发布预检 Markdown", "app_assets/public_snapshot_import_publish_preflight_latest.md", "public_snapshot_import_publish_preflight_latest.md"),
        ("Provider 人工校验队列", "app_assets/provider_fallback_verification_latest.pdf", "provider_fallback_verification_latest.pdf"),
        ("Provider 人工校验队列 JSON", "app_assets/provider_fallback_verification_latest.json", "provider_fallback_verification_latest.json"),
        ("Provider 人工校验队列 Markdown", "app_assets/provider_fallback_verification_latest.md", "provider_fallback_verification_latest.md"),
        ("Provider 人工导入模板 CSV", "app_assets/provider_manual_verification_template_latest.csv", "provider_manual_verification_template_latest.csv"),
        ("Provider 人工全量成对模板 CSV", "app_assets/provider_manual_pair_template_latest.csv", "provider_manual_pair_template_latest.csv"),
        ("Provider 人工下一批成对模板 CSV", "app_assets/provider_manual_next_batch_pair_template_latest.csv", "provider_manual_next_batch_pair_template_latest.csv"),
        ("Provider 人工导入状态", "app_assets/provider_manual_verification_status_latest.pdf", "provider_manual_verification_status_latest.pdf"),
        ("Provider 人工导入状态 JSON", "app_assets/provider_manual_verification_status_latest.json", "provider_manual_verification_status_latest.json"),
        ("Provider 人工导入状态 Markdown", "app_assets/provider_manual_verification_status_latest.md", "provider_manual_verification_status_latest.md"),
        ("Provider 人工 Hash Gate", "app_assets/provider_manual_hash_gate_latest.pdf", "provider_manual_hash_gate_latest.pdf"),
        ("Provider 人工 Hash Gate JSON", "app_assets/provider_manual_hash_gate_latest.json", "provider_manual_hash_gate_latest.json"),
        ("Provider 人工 Hash Gate Markdown", "app_assets/provider_manual_hash_gate_latest.md", "provider_manual_hash_gate_latest.md"),
        ("Provider Team Total Overlay 预览", "app_assets/provider_manual_overlay_preview_latest.pdf", "provider_manual_overlay_preview_latest.pdf"),
        ("Provider Team Total Overlay 预览 JSON", "app_assets/provider_manual_overlay_preview_latest.json", "provider_manual_overlay_preview_latest.json"),
        ("Provider Team Total Overlay 预览 Markdown", "app_assets/provider_manual_overlay_preview_latest.md", "provider_manual_overlay_preview_latest.md"),
        ("Provider Team Total Overlay Raw 预览", "app_assets/provider_manual_team_total_overlay_raw_latest.json", "provider_manual_team_total_overlay_raw_latest.json"),
        ("Provider Team Total Overlay 签名模板", "app_assets/provider_manual_overlay_approval_template_latest.json", "provider_manual_overlay_approval_template_latest.json"),
        ("Provider Team Total Overlay 发布预检", "app_assets/provider_manual_overlay_publish_preflight_latest.pdf", "provider_manual_overlay_publish_preflight_latest.pdf"),
        ("Provider Team Total Overlay 发布预检 JSON", "app_assets/provider_manual_overlay_publish_preflight_latest.json", "provider_manual_overlay_publish_preflight_latest.json"),
        ("Provider Team Total Overlay 发布预检 Markdown", "app_assets/provider_manual_overlay_publish_preflight_latest.md", "provider_manual_overlay_publish_preflight_latest.md"),
        ("Provider Team Total Overlay 发布", "app_assets/provider_manual_overlay_publish_latest.pdf", "provider_manual_overlay_publish_latest.pdf"),
        ("Provider Team Total Overlay 发布 JSON", "app_assets/provider_manual_overlay_publish_latest.json", "provider_manual_overlay_publish_latest.json"),
        ("Provider Team Total Overlay 发布 Markdown", "app_assets/provider_manual_overlay_publish_latest.md", "provider_manual_overlay_publish_latest.md"),
        ("Provider Team Total 校验工作台", "app_assets/provider_manual_workbench_latest.pdf", "provider_manual_workbench_latest.pdf"),
        ("Provider Team Total 校验工作台 JSON", "app_assets/provider_manual_workbench_latest.json", "provider_manual_workbench_latest.json"),
        ("Provider Team Total 校验工作台 Markdown", "app_assets/provider_manual_workbench_latest.md", "provider_manual_workbench_latest.md"),
        ("策略表现 Dashboard", "app_assets/strategy_performance_latest.pdf", "strategy_performance_latest.pdf"),
        ("策略表现 JSON", "app_assets/strategy_performance_latest.json", "strategy_performance_latest.json"),
        ("策略表现 Markdown", "app_assets/strategy_performance_latest.md", "strategy_performance_latest.md"),
        ("新旧报告变化总控台", "app_assets/report_evolution_latest.pdf", "report_evolution_latest.pdf"),
        ("新旧报告变化 JSON", "app_assets/report_evolution_latest.json", "report_evolution_latest.json"),
        ("新旧报告变化 Markdown", "app_assets/report_evolution_latest.md", "report_evolution_latest.md"),
        ("自动化就绪", "app_assets/automation_readiness_latest.pdf", "automation_readiness_latest.pdf"),
        ("本地研究数据库", "app_assets/tab_fifa_reports.sqlite3", "tab_fifa_reports.sqlite3"),
        ("主动测试时间线", "app_assets/active_timeline_report_latest.pdf", "active_timeline_report_latest.pdf"),
        ("Raw 恢复与补跑控制台", "app_assets/raw_refresh_recovery_latest.pdf", "raw_refresh_recovery_latest.pdf"),
        ("研究级 raw 证据", "app_assets/raw_refresh_research_only_latest.json", "raw_refresh_research_only_latest.json"),
        ("TAB Live 板块发现", "app_assets/live_board_discovery_latest.pdf", "live_board_discovery_latest.pdf"),
        ("可用板块策略", "app_assets/available_board_strategy_latest.pdf", "available_board_strategy_latest.pdf"),
        ("研究诊断日报", "app_assets/partial_daily_research_latest.pdf", "partial_daily_research_latest.pdf"),
        ("研究诊断 JSON", "app_assets/partial_daily_research_latest.json", "partial_daily_research_latest.json"),
        ("研究诊断 Markdown", "app_assets/partial_daily_research_latest.md", "partial_daily_research_latest.md"),
        ("赛程校验 Dashboard", "app_assets/fixture_sanity_latest.pdf", "fixture_sanity_latest.pdf"),
        ("赛程校验 JSON", "app_assets/fixture_sanity_latest.json", "fixture_sanity_latest.json"),
        ("赛程校验 Markdown", "app_assets/fixture_sanity_latest.md", "fixture_sanity_latest.md"),
        ("报告历史", "app_assets/report_index_latest.pdf", "report_index_latest.pdf"),
        ("研究智能层", "app_assets/report_intelligence_latest.pdf", "report_intelligence_latest.pdf"),
        ("目标验收追踪", "app_assets/goal_traceability_latest.pdf", "goal_traceability_latest.pdf"),
        ("目标验收追踪 JSON", "app_assets/goal_traceability_latest.json", "goal_traceability_latest.json"),
        ("持仓监控", "app_assets/position_monitor_latest.pdf", "position_monitor_latest.pdf"),
        ("持仓监控 JSON", "app_assets/position_monitor_latest.json", "position_monitor_latest.json"),
        ("开源模型 Dashboard", "app_assets/tab_fifa_model_comparison_v0_1.pdf", "tab_fifa_model_comparison_v0_1.pdf"),
        ("模型分歧复核 Dashboard", "app_assets/model_divergence_review_latest.pdf", "model_divergence_review_latest.pdf"),
        ("模型分歧复核 JSON", "app_assets/model_divergence_review_latest.json", "model_divergence_review_latest.json"),
        ("模型分歧复核 Markdown", "app_assets/model_divergence_review_latest.md", "model_divergence_review_latest.md"),
        ("开源模型库", "app_assets/source_model_registry_latest.pdf", "source_model_registry_latest.pdf"),
        ("开源模型库 JSON", "app_assets/source_model_registry_latest.json", "source_model_registry_latest.json"),
        ("报表可视化覆盖", "app_assets/report_visual_inventory_latest.pdf", "report_visual_inventory_latest.pdf"),
        ("Automation 成熟度验收", "app_assets/automation_maturity_latest.pdf", "automation_maturity_latest.pdf"),
        ("缺口修复计划", "app_assets/automation_doctor_latest.pdf", "automation_doctor_latest.pdf"),
        ("主动测试 JSON", "app_assets/active_timeline_latest.json", "active_timeline_latest.json"),
        ("主动测试时间线 JSON", "app_assets/active_timeline_report_latest.json", "active_timeline_report_latest.json"),
        ("补跑结果 JSON", "app_assets/active_backfill_latest.json", "active_backfill_latest.json"),
        ("产品完成度 Dashboard", "app_assets/product_readiness_dashboard_latest.pdf", "product_readiness_dashboard_latest.pdf"),
        ("产品完成度 JSON", "app_assets/product_readiness_dashboard_latest.json", "product_readiness_dashboard_latest.json"),
        ("成熟度验收 JSON", "app_assets/automation_maturity_latest.json", "automation_maturity_latest.json"),
        ("研究智能层 JSON", "app_assets/report_intelligence_latest.json", "report_intelligence_latest.json"),
        ("开源模型 Dashboard JSON", "app_assets/tab_fifa_model_comparison_v0_1.json", "tab_fifa_model_comparison_v0_1.json"),
        ("开源模型库 Markdown", "app_assets/source_model_registry_latest.md", "source_model_registry_latest.md"),
        ("报表覆盖 JSON", "app_assets/report_visual_inventory_latest.json", "report_visual_inventory_latest.json"),
        ("缺口修复计划 JSON", "app_assets/automation_doctor_latest.json", "automation_doctor_latest.json"),
        ("最新成功指针", "app_assets/latest_commit.json", "latest_commit.json"),
        ("Runner 摘要", "app_assets/automation_run_latest.json", "automation_run_latest.json"),
        ("Research-only raw manifest", "app_assets/raw_refresh_research_only_latest.json", "raw_refresh_research_only_latest.json"),
        ("Raw 恢复 JSON", "app_assets/raw_refresh_recovery_latest.json", "raw_refresh_recovery_latest.json"),
        ("Live 板块发现 JSON", "app_assets/live_board_discovery_latest.json", "live_board_discovery_latest.json"),
        ("可用板块策略 JSON", "app_assets/available_board_strategy_latest.json", "available_board_strategy_latest.json"),
    ]
    artifact_rows = "\n".join(
        f'<tr><td>{esc(label)}</td><td><a href="{href}">{esc(name)}</a></td></tr>'
        for label, href, name in artifacts
        if href
    )

    if first_action and execution_allowed:
        top_summary = (
            f"首选：{first_action.get('event', '待同步')} / {first_action.get('market', '')} / {first_action.get('selection', '')}，"
            f"金额 {money(first_action.get('stake_aud'))}。"
        )
    elif first_action:
        top_summary = f"{gate_message} 当前保留 {len(rec_rows)} 条研究候选，新增执行金额为 AUD 0。"
    else:
        top_summary = "暂无可执行推荐。"
    hero_note = (
        "当前展示的是可执行下注建议；执行前请以 TAB 实时赔率复核。"
        if execution_allowed
        else "当前展示的是研究候选，不是执行指令；需先接入授权 raw 或导入用户导出快照，并通过日报门禁。"
    )
    recommendation_note = (
        "按表格从上到下复核，红色买入项优先；金额为研究建议金额，执行前以 TAB 实时赔率和账户余额为准。"
        if execution_allowed
        else "当前推荐只作为研究候选保留；系统已把操作改为暂停执行，金额不进入新增下注。"
    )
    exposure_label = "建议新增暴露" if execution_allowed else "当前可执行新增暴露"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TAB FIFA盘口研究系统</title>
  <link rel="icon" href="data:,">
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fb;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #667085;
      --line: #d9e0e8;
      --head: #f3f7fb;
      --green: #0f7b4f;
      --red: #c62828;
      --amber: #9a6700;
      --blue: #1d4ed8;
      --soft-green: #e8f6ef;
      --soft-red: #fdecec;
      --soft-blue: #edf4ff;
      --soft-amber: #fff6db;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.45;
    }}
    html {{ scroll-behavior: smooth; }}
    [id] {{ scroll-margin-top: 82px; }}
    main {{ width: min(1280px, calc(100vw - 36px)); margin: 0 auto; padding: 22px 0 42px; }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 22px;
      align-items: flex-start;
      padding: 18px 0 16px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; line-height: 1.18; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }}
    h3 {{ margin: 0 0 8px; font-size: 15px; letter-spacing: 0; }}
    p {{ margin: 0; }}
    .subtitle {{ color: var(--muted); max-width: 780px; }}
    .stamp {{ color: var(--muted); font-size: 13px; white-space: nowrap; }}
    .command-nav {{
      position: sticky;
      top: 0;
      z-index: 12;
      display: grid;
      grid-template-columns: 122px 1fr;
      gap: 12px;
      align-items: start;
      margin: 0 0 14px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.96);
      box-shadow: 0 8px 22px rgba(23, 32, 42, 0.06);
      backdrop-filter: blur(8px);
    }}
    .command-nav strong {{ font-size: 13px; color: #344054; padding-top: 5px; }}
    .nav-groups {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 9px;
    }}
    .nav-group > span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      margin-bottom: 5px;
    }}
    .nav-group > div {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .command-nav a {{
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 4px 9px;
      border-radius: 7px;
      border: 1px solid var(--line);
      background: #fbfcfe;
      color: var(--ink);
      text-decoration: none;
      font-size: 12px;
      font-weight: 760;
    }}
    .command-nav a:hover {{ border-color: #9fb0c3; background: #f3f7fb; }}
    .command-nav a.active {{ border-color: #8bb7a0; background: var(--soft-green); color: var(--green); }}
    .operation-panel {{
      margin: 14px 0 16px;
      border-left: 5px solid var(--red);
      background: #fff;
    }}
    .operation-hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(260px, 0.65fr);
      gap: 12px;
      align-items: stretch;
      margin-bottom: 12px;
    }}
    .operation-hero h2 {{
      margin: 0 0 8px;
      font-size: 24px;
      line-height: 1.2;
      color: var(--red);
    }}
    .operation-hero p {{
      max-width: 780px;
      color: #344054;
      font-size: 14px;
      font-weight: 650;
    }}
    .operation-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 9px;
      margin-top: 12px;
    }}
    .operation-next {{
      border: 1px solid #efc7c7;
      border-radius: 8px;
      background: #fffafa;
      padding: 12px;
      min-width: 0;
    }}
    .operation-next span,
    .operation-card span,
    .operation-blockers > span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 760;
      margin-bottom: 6px;
    }}
    .operation-next strong {{
      display: block;
      font-size: 18px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }}
    .operation-next small {{
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }}
    .operation-grid {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 9px;
      margin-bottom: 10px;
    }}
    .operation-card {{
      min-height: 94px;
      border: 1px solid var(--line);
      border-top: 4px solid #bcd3f4;
      border-radius: 8px;
      background: #fbfcfe;
      padding: 10px;
      min-width: 0;
    }}
    .operation-card.ok {{ border-top-color: var(--green); background: #f6fbf8; }}
    .operation-card.watch {{ border-top-color: var(--amber); background: #fffdf5; }}
    .operation-card.blocked {{ border-top-color: var(--red); background: #fffafa; }}
    .operation-card strong {{
      display: block;
      font-size: 15px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }}
    .operation-card small {{
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
    .operation-flow {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 9px;
      margin: 10px 0;
    }}
    .operation-step {{
      display: grid;
      grid-template-columns: 32px 1fr;
      gap: 4px 8px;
      align-items: start;
      min-height: 76px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      text-decoration: none;
    }}
    .operation-step.ok {{ border-color: #b8dfca; background: #f7fbf8; }}
    .operation-step.watch {{ border-color: #efd78d; background: #fffdf5; }}
    .operation-step.blocked {{ border-color: #efc7c7; background: #fffafa; }}
    .operation-step b {{
      grid-row: 1 / 3;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 8px;
      background: #edf4ff;
      color: var(--blue);
      font-size: 13px;
    }}
    .operation-step span {{ font-weight: 850; font-size: 13px; line-height: 1.25; }}
    .operation-step small {{
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
    .operation-blockers {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
      padding: 10px 12px;
      margin-top: 10px;
    }}
    .operation-blockers ul {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .operation-blockers li {{
      border-left: 3px solid var(--amber);
      padding-left: 8px;
      min-width: 0;
    }}
    .operation-blockers strong {{
      display: block;
      font-size: 13px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }}
    .operation-blockers li span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      margin-top: 3px;
      overflow-wrap: anywhere;
    }}
    .command-center {{
      margin: 14px 0 16px;
      border-left: 5px solid var(--green);
    }}
    .command-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .command-card {{
      min-height: 98px;
      padding: 11px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
    }}
    .command-card.primary {{ background: #fffafa; border-color: #efc7c7; }}
    .command-card span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 6px; }}
    .command-card strong {{ display: block; font-size: 15px; line-height: 1.32; overflow-wrap: anywhere; }}
    .command-card small {{ display: block; color: var(--muted); font-size: 11px; line-height: 1.35; margin-top: 6px; overflow-wrap: anywhere; }}
    .task-list {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }}
    .task-row {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 4px 8px;
      align-items: start;
      min-height: 86px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      text-decoration: none;
    }}
    .task-row.ok {{ border-color: #b8dfca; background: #f7fbf8; }}
    .task-row.blocked {{ border-color: #efc7c7; background: #fffafa; }}
    .task-row.watch {{ border-color: #efd78d; background: #fffdf5; }}
    .task-state {{
      grid-column: 1 / 3;
      color: var(--muted);
      font-size: 11px;
      font-weight: 850;
    }}
    .task-row strong {{ font-size: 13px; line-height: 1.25; }}
    .task-row small {{
      grid-column: 1 / 3;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
    .task-row em {{
      align-self: start;
      justify-self: end;
      color: var(--blue);
      font-size: 11px;
      font-style: normal;
      font-weight: 850;
    }}
    .hero {{
      margin: 18px 0 16px;
      display: grid;
      grid-template-columns: 1fr 310px;
      gap: 16px;
      align-items: stretch;
    }}
    .web-runtime-panel {{
      margin: 14px 0 12px;
      display: grid;
      grid-template-columns: 1.2fr repeat(3, minmax(0, 1fr));
      gap: 10px;
      align-items: stretch;
      border: 1px solid var(--line);
      border-left: 5px solid var(--green);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
    }}
    .web-runtime-panel.static {{ border-left-color: var(--amber); background: #fffdf5; }}
    .web-runtime-panel.offline {{ border-left-color: var(--red); background: #fffafa; }}
    .web-runtime-panel div {{
      min-height: 72px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
      padding: 10px;
    }}
    .web-runtime-panel span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 5px;
    }}
    .web-runtime-panel strong {{
      display: block;
      font-size: 14px;
      line-height: 1.3;
      overflow-wrap: anywhere;
    }}
    .web-runtime-panel small {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      margin-top: 5px;
      overflow-wrap: anywhere;
    }}
    .web-runtime-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-top: 8px;
    }}
    section, .summary-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .recommendation-block.priority {{
      margin: 16px 0;
      border-left: 5px solid var(--red);
    }}
    .recommendation-block.priority .decision-strip {{
      margin-top: 4px;
    }}
    .summary-card.buy {{
      border-left: 5px solid var(--red);
      background: #fffafa;
    }}
    .summary-card.blocked {{
      border-left: 5px solid var(--amber);
      background: #fffdf5;
    }}
    .summary-card.watch {{
      border-left: 5px solid var(--blue);
      background: #f8fbff;
    }}
    .summary-card .big {{ font-size: 24px; font-weight: 780; margin: 6px 0; }}
    .summary-card .muted {{ color: var(--muted); font-size: 13px; }}
    .decision-strip {{
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 14px;
      align-items: stretch;
      margin: 0 0 16px;
    }}
    .decision-strip.buy {{ border-left: 5px solid var(--red); }}
    .decision-strip.blocked {{ border-left: 5px solid var(--amber); }}
    .decision-strip.watch {{ border-left: 5px solid var(--blue); }}
    .eyebrow {{
      display: inline-flex;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0;
    }}
    .decision-main h2 {{ margin-bottom: 8px; }}
    .decision-main p {{ color: #344054; font-weight: 650; }}
    .decision-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .decision-grid div, .active-decision div {{
      background: #fbfcfe;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      min-height: 96px;
    }}
    .decision-grid span, .active-decision span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .decision-grid strong, .active-decision strong {{
      display: block;
      font-size: 15px;
      line-height: 1.3;
      overflow-wrap: anywhere;
    }}
    .decision-grid small, .active-decision small {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      margin-top: 6px;
    }}
    .active-decision {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin: 0 0 12px;
      padding: 0;
      border: 0;
      background: transparent;
    }}
    .active-decision.ok div {{ border-color: #b8dfca; background: #f6fbf8; }}
    .active-decision.blocked div {{ border-color: #efd78d; background: #fffdf5; }}
    .basis-panel {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin: 12px 0;
    }}
    .basis-panel div {{
      background: #fbfcfe;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      min-height: 78px;
    }}
    .basis-panel span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .basis-panel strong {{
      display: block;
      font-size: 13px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
    .basis-panel small {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      margin-top: 5px;
      overflow-wrap: anywhere;
    }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 14px 0 0; min-width: 0; }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 14px;
      margin-bottom: 12px;
      min-width: 0;
    }}
    .compact-actions {{ margin: 0; }}
    .compact-actions .priority-message {{ flex-basis: 100%; }}
    .action, button.action {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 8px 13px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 700;
      border: 1px solid var(--line);
      color: var(--ink);
      background: #fff;
      cursor: pointer;
      font: inherit;
      max-width: 100%;
      min-width: 0;
      overflow-wrap: anywhere;
      text-align: center;
    }}
    a:focus-visible, button:focus-visible, input:focus-visible {{
      outline: 3px solid rgba(29, 78, 216, 0.28);
      outline-offset: 2px;
    }}
    button.action:disabled {{
      cursor: progress;
      opacity: 0.72;
    }}
    .action.primary {{ background: var(--green); color: #fff; border-color: var(--green); }}
    .action.danger {{ background: var(--red); color: #fff; border-color: var(--red); }}
    .action.secondary:hover {{ border-color: #9fb0c3; background: #f9fbfd; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }}
    .insight-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 12px 0; }}
    .insight {{ background: #fbfcfe; border: 1px solid var(--line); border-radius: 8px; padding: 12px; min-height: 86px; }}
    .insight span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 7px; }}
    .insight strong {{ display: block; font-size: 16px; line-height: 1.35; overflow-wrap: anywhere; }}
    .insight small {{ display: block; color: var(--muted); font-size: 11px; line-height: 1.35; margin-top: 5px; overflow-wrap: anywhere; }}
    .provider-kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      margin: 12px 0;
    }}
    .provider-decision {{
      display: grid;
      grid-template-columns: minmax(220px, 1.15fr) minmax(220px, 1fr) minmax(220px, 1fr);
      gap: 10px;
      border: 1px solid #d7e3ef;
      border-radius: 8px;
      background: #f8fbff;
      padding: 12px;
      margin: 12px 0;
    }}
    .provider-decision > div {{
      min-width: 0;
      max-width: 100%;
    }}
    .provider-decision.blocked {{
      border-color: #efc7c7;
      background: #fffafa;
    }}
    .provider-decision.watch {{
      border-color: #efd78d;
      background: #fffdf5;
    }}
    .provider-decision span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .provider-decision strong {{
      display: block;
      font-size: 18px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }}
    .provider-decision p,
    .provider-decision small {{
      display: block;
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }}
    .provider-kpi-grid > div,
    .provider-market-strip > div,
    .provider-plan-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfe;
      min-width: 0;
    }}
    .provider-kpi-grid > div,
    .provider-market-strip > div {{ min-height: 82px; }}
    .provider-kpi-grid .provider-kpi-primary {{
      background: #f5f9ff;
      border-color: #bcd3f4;
    }}
    .provider-kpi-grid span,
    .provider-market-strip span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .provider-kpi-grid strong,
    .provider-market-strip strong {{
      display: block;
      font-size: 18px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }}
    .provider-kpi-grid small,
    .provider-market-strip small {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      margin-top: 5px;
      overflow-wrap: anywhere;
    }}
    .provider-market-strip {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 10px 0 12px;
    }}
    .provider-plan-card {{
      margin: 10px 0 12px;
      background: #fff;
      overflow-wrap: anywhere;
    }}
    .provider-plan-card > div {{
      min-width: 0;
      max-width: 100%;
    }}
    .provider-plan-card span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .provider-plan-card code {{
      display: block;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f7f9fc;
      padding: 10px;
      color: var(--ink);
      font-size: 12px;
      line-height: 1.45;
    }}
    .provider-plan-card ol {{
      margin: 0;
      padding-left: 18px;
      overflow-wrap: anywhere;
    }}
    .provider-plan-card li {{ overflow-wrap: anywhere; }}
    .provider-command-console {{
      border-left: 5px solid var(--blue);
    }}
    .provider-control-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 12px 0;
    }}
    .provider-control-card {{
      min-height: 118px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfe;
      border-top: 4px solid #bcd3f4;
    }}
    .provider-control-card.ok {{ border-top-color: var(--green); background: #f6fbf8; }}
    .provider-control-card.watch {{ border-top-color: var(--amber); background: #fffdf5; }}
    .provider-control-card.blocked {{ border-top-color: var(--red); background: #fffafa; }}
    .provider-control-card span,
    .provider-command-lanes span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 7px;
    }}
    .provider-control-card strong,
    .provider-command-lanes strong {{
      display: block;
      font-size: 17px;
      line-height: 1.3;
      overflow-wrap: anywhere;
    }}
    .provider-control-card small,
    .provider-command-lanes small {{
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }}
    .provider-command-lanes {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin: 12px 0;
    }}
    .provider-command-lanes > div {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
      min-width: 0;
    }}
    .provider-command-lanes p {{
      margin: 6px 0 0;
      color: #344054;
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }}
    .provider-command-lanes ul {{ margin-top: 4px; }}
    .coverage-bar {{
      position: relative;
      height: 8px;
      border-radius: 999px;
      background: #edf2f7;
      overflow: hidden;
      margin-bottom: 6px;
    }}
    .coverage-bar span {{
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--blue), var(--green));
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 100px;
      min-width: 0;
      max-width: 100%;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .metric * {{ min-width: 0; max-width: 100%; }}
    .label {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; }}
    .value {{ font-size: 19px; font-weight: 750; line-height: 1.25; overflow-wrap: anywhere; }}
    .status, .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 3px 9px;
      border-radius: 999px;
      font-weight: 750;
      font-size: 13px;
      max-width: 100%;
      line-height: 1.25;
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .status.ok {{ background: var(--soft-green); color: var(--green); }}
    .status.blocked {{ background: var(--soft-red); color: var(--red); }}
    .status.watch {{ background: var(--soft-amber); color: var(--amber); }}
    .pill.buy {{ background: var(--red); color: #fff; }}
    .pill.watch {{ background: var(--soft-amber); color: var(--amber); }}
    .pill.blocked {{ background: var(--soft-red); color: var(--red); }}
    .gate-warning {{
      margin-top: 12px;
      border: 1px solid #f1c9c9;
      background: #fff8f8;
      color: #7a271a;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 13px;
      font-weight: 650;
    }}
    .layout {{ display: grid; grid-template-columns: 1fr 0.72fr; gap: 16px; margin-top: 16px; }}
    .execution-list {{ margin-bottom: 16px; }}
    .bet-card-list {{ display: grid; gap: 10px; }}
    .bet-card {{
      display: grid;
      grid-template-columns: 44px 1fr minmax(330px, 0.75fr);
      gap: 12px;
      align-items: start;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fff;
    }}
    .bet-card.blocked {{
      border-color: #edc6c6;
      background: #fffafa;
    }}
    .bet-rank {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 34px;
      height: 34px;
      border-radius: 8px;
      background: var(--soft-red);
      color: var(--red);
      font-weight: 800;
    }}
    .bet-title {{ font-size: 17px; font-weight: 820; margin-bottom: 4px; overflow-wrap: anywhere; }}
    .bet-subtitle {{ color: var(--ink); font-size: 13px; margin-bottom: 8px; overflow-wrap: anywhere; }}
    .bet-meta {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .bet-meta span {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 8px;
      border-radius: 999px;
      background: #f7f9fc;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
    }}
    .bet-numbers {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 8px;
    }}
    .bet-numbers div {{
      min-height: 58px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px;
      background: #fbfcfe;
    }}
    .bet-numbers span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 4px; }}
    .bet-numbers strong {{ display: block; font-size: 14px; line-height: 1.25; overflow-wrap: anywhere; }}
    .bet-numbers small {{ display: block; color: var(--muted); font-size: 11px; line-height: 1.3; margin-top: 3px; overflow-wrap: anywhere; }}
    .buy-text {{ color: var(--red); }}
    .blocked-text {{ color: var(--red); }}
    .bet-reason {{ grid-column: 2 / 4; color: #344054; font-size: 13px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; padding: 9px 8px; border-bottom: 1px solid var(--line); vertical-align: top; overflow-wrap: anywhere; }}
    th {{ background: var(--head); color: #344054; font-weight: 800; }}
    tr:last-child td {{ border-bottom: 0; }}
    .table-scroll {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; max-width: 100%; min-width: 0; box-sizing: border-box; }}
    .table-scroll table th:first-child, .table-scroll table td:first-child {{ padding-left: 12px; }}
    .recommendations strong {{ font-weight: 800; }}
    .recommendations span {{ color: var(--muted); }}
    .recommendations td.buy-cell,
    .recommendation-operations td.buy-cell {{
      background: #fff5f3;
      border-left: 3px solid var(--red);
      color: var(--red);
      font-weight: 800;
    }}
    .action-hint {{
      display: block;
      margin-top: 5px;
      font-size: 11px;
      line-height: 1.1;
      font-weight: 800;
    }}
    .buy-hint {{ color: var(--red); }}
    .reason-row td {{ background: #fbfcfe; color: #344054; font-size: 13px; padding-top: 8px; padding-bottom: 12px; }}
    .diagnostic-strip {{
      display: grid;
      grid-template-columns: repeat(7, minmax(120px, 1fr));
      gap: 8px;
      margin-bottom: 8px;
    }}
    .diagnostic-strip span {{
      display: block;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--muted);
      padding: 7px 8px;
      font-size: 11px;
      line-height: 1.3;
    }}
    .diagnostic-strip strong {{
      display: block;
      color: var(--ink);
      font-size: 13px;
      margin-top: 3px;
      overflow-wrap: anywhere;
    }}
    .analysis-basis-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(180px, 1fr));
      gap: 8px;
      margin-bottom: 8px;
    }}
    .analysis-basis-grid span {{
      display: block;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--muted);
      padding: 7px 8px;
      font-size: 11px;
      line-height: 1.35;
    }}
    .analysis-basis-grid strong {{
      display: block;
      color: var(--ink);
      font-size: 12px;
      margin-top: 3px;
      overflow-wrap: anywhere;
    }}
    .analysis-basis-grid small {{
      display: block;
      margin-top: 3px;
      color: var(--muted);
      overflow-wrap: anywhere;
    }}
    .compact-basis {{
      background: #fbfcfe;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px 10px;
    }}
    .reason-text {{ line-height: 1.45; }}
    .ev-cell {{ font-weight: 800; }}
    .ev-cell.positive-ev {{ color: var(--red); }}
    .ev-cell.negative-ev {{ color: var(--muted); }}
    .ev-cell.watch-ev {{ color: var(--amber); }}
    .mini-input {{
      width: 76px;
      height: 28px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 3px 6px;
      font: inherit;
      margin: 2px 0 4px 4px;
      background: #fff;
    }}
    .manual-entry-table table {{
      min-width: 1120px;
    }}
    .entry-input {{
      width: min(100%, 128px);
      min-height: 31px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 5px 7px;
      margin: 0 6px 6px 0;
      font: inherit;
      font-size: 12px;
      background: #fff;
      color: var(--ink);
      box-sizing: border-box;
    }}
    .entry-input.wide {{ width: min(100%, 220px); }}
    .entry-input.odds {{ width: 86px; font-weight: 750; }}
    .entry-input:focus {{
      outline: 2px solid #bcd3f4;
      border-color: #7aa7d9;
    }}
    label {{ display: block; color: var(--muted); white-space: nowrap; }}
    a {{ color: var(--blue); }}
    ul {{ margin: 0; padding-left: 18px; }}
    li + li {{ margin-top: 8px; }}
    .note, .empty {{ margin-top: 12px; color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }}
    .compact-note {{ margin: 12px 0 0; }}
    .subsection-title {{ margin: 16px 0 8px; font-size: 15px; color: var(--ink); }}
    .timeline-metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px; }}
    .timeline-metrics div {{ background: #fbfcfe; border: 1px solid var(--line); border-radius: 8px; padding: 10px; }}
    .timeline-metrics span {{ display: block; color: var(--muted); font-size: 12px; }}
    .timeline-metrics strong {{ display: block; font-size: 18px; margin-top: 4px; }}
    .slot-strip {{ display: flex; flex-wrap: wrap; gap: 4px; min-width: 0; max-width: 100%; }}
    .slot-chip {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex: 1 1 44px;
      min-width: 0;
      min-height: 23px;
      padding: 2px 6px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 750;
      border: 1px solid var(--line);
    }}
    .slot-chip.covered {{ background: var(--soft-green); color: var(--green); border-color: #b8dfca; }}
    .slot-chip.missing {{ background: var(--soft-red); color: var(--red); border-color: #efc7c7; }}
    .slot-chip.unknown {{ background: var(--soft-amber); color: var(--amber); border-color: #efd78d; }}
    .button-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }}
    .message {{ min-height: 20px; color: var(--muted); font-size: 13px; margin-bottom: 10px; }}
    .active-progress {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }}
    .active-progress div {{
      min-height: 78px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
      padding: 10px;
    }}
    .active-progress span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 5px; }}
    .active-progress strong {{ display: block; font-size: 14px; line-height: 1.35; }}
    .active-warning {{
      margin: 0 0 10px;
      border: 1px solid #efd78d;
      border-radius: 8px;
      background: #fffdf5;
      color: #7a4c00;
      padding: 9px 11px;
      font-size: 13px;
      font-weight: 650;
    }}
    .priority-message {{
      margin-top: 10px;
      margin-bottom: 0;
      padding: 9px 11px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
    }}
    .stacked-table {{ margin-top: 10px; }}
      @media (max-width: 980px) {{
      main {{ width: min(100vw - 24px, 1280px); padding-top: 12px; }}
      header, .hero {{ grid-template-columns: 1fr; flex-direction: column; gap: 10px; }}
      .stamp {{ white-space: normal; }}
      .grid, .timeline-metrics, .insight-grid, .basis-panel {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .command-nav {{ grid-template-columns: 1fr; }}
      .nav-groups {{ grid-template-columns: 1fr; }}
      .operation-hero {{ grid-template-columns: 1fr; }}
      .operation-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .operation-flow {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .operation-blockers ul {{ grid-template-columns: 1fr; }}
      .command-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .task-list {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .active-progress {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .provider-kpi-grid, .provider-market-strip, .provider-decision {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .provider-control-grid, .provider-command-lanes {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .web-runtime-panel {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .decision-strip {{ grid-template-columns: 1fr; }}
      .decision-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .active-decision {{ grid-template-columns: 1fr; }}
      .section-head {{ flex-direction: column; }}
      .layout {{ grid-template-columns: 1fr; }}
      .bet-card {{ grid-template-columns: 36px 1fr; }}
      .bet-numbers, .bet-reason {{ grid-column: 1 / 3; }}
      .bet-numbers {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .diagnostic-strip, .analysis-basis-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      h1 {{ font-size: 24px; }}
    }}
    @media (max-width: 560px) {{
      .grid, .timeline-metrics, .insight-grid, .basis-panel {{ grid-template-columns: 1fr; }}
      .operation-grid, .operation-flow {{ grid-template-columns: 1fr; }}
      .operation-hero h2 {{ font-size: 22px; }}
      .command-grid, .active-progress {{ grid-template-columns: 1fr; }}
      .provider-kpi-grid, .provider-market-strip, .provider-decision {{ grid-template-columns: 1fr; }}
      .provider-control-grid, .provider-command-lanes {{ grid-template-columns: 1fr; }}
      .task-list {{ grid-template-columns: 1fr; }}
      .web-runtime-panel {{ grid-template-columns: 1fr; }}
      .decision-grid {{ grid-template-columns: 1fr; }}
      .bet-card {{ grid-template-columns: 1fr; }}
      .bet-numbers, .bet-reason {{ grid-column: 1; }}
      .bet-numbers {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .diagnostic-strip, .analysis-basis-grid {{ grid-template-columns: 1fr; }}
      .action {{ width: 100%; }}
      table {{ table-layout: fixed; }}
      .table-scroll.compact th,
      .table-scroll.compact td {{ padding: 7px 4px; }}
      .table-scroll.compact th {{
        padding-left: 0;
        padding-right: 0;
        font-size: 8px;
        line-height: 1.1;
        word-break: break-all;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>TAB FIFA盘口研究系统</h1>
        <p class="subtitle">首页优先显示可执行下注建议。所有按钮只生成研究、检查和补跑报告，不会点击赔率、添加投注单或自动下注。</p>
      </div>
      <p class="stamp">入口更新时间：{esc(generated_at)} AEST</p>
    </header>

    {workflow_nav_html()}
    {user_operation_panel_html(rec_rows, execution_allowed=execution_allowed, gate_message=gate_message, latest_commit=latest_commit, raw_health=raw_health, automation_scorecard=automation_scorecard, automation_work_queue=automation_work_queue, provider_kpi=provider_kpi, provider_alternate_plan=provider_alternate_plan, position_monitor=position_monitor, timeline=timeline)}
    {command_center_html(rec_rows, execution_allowed=execution_allowed, gate_message=gate_message, raw_health=raw_health, timeline=timeline, recommendation_operations=recommendation_operations, partial_daily_research=partial_daily_research, readiness=readiness, provider_kpi=provider_kpi)}
    {automation_scorecard_html(automation_scorecard)}
    {provider_collection_console_html(provider_kpi, provider_manual_workbench, provider_config_doctor, provider_alternate_plan)}
    {alternate_market_workbench_html(provider_kpi, provider_alternate_plan, provider_config_doctor)}
    {automation_work_queue_html(automation_work_queue)}
    {team_total_manual_entry_html(provider_manual_workbench)}
    {provider_config_doctor_html(provider_config_doctor)}
    {provider_kpi_html(provider_kpi, provider_alternate_plan)}
    {public_snapshot_import_html(public_snapshot_import, public_snapshot_publish_preflight, public_snapshot_raw_publish)}
    {provider_fallback_verification_html(provider_fallback_verification)}
    {provider_manual_verification_html(provider_manual_verification, provider_manual_hash_gate, provider_manual_overlay_preview, provider_manual_overlay_publish_preflight, provider_manual_overlay_publish, provider_manual_workbench)}

    <div class="web-runtime-panel" id="webRuntimePanel" data-primary-interaction-mode="web" data-app-url="{esc(WEB_APP_URL)}">
      <div>
        <span>运行交互方式</span>
        <strong id="runtimeMode">网页主控台优先</strong>
        <small id="runtimeModeDetail">本地网页负责主动测试、刷新、补跑和持仓读取；静态 HTML 只作为只读预览。</small>
      </div>
      <div>
        <span>主入口 URL</span>
        <strong>{esc(WEB_APP_URL)}</strong>
        <small>Downloads 的 `.app` 会打开这个本地网页。</small>
      </div>
      <div>
        <span>运行按钮状态</span>
        <strong id="runtimeControlsStatus">检测中</strong>
        <small id="runtimeControlsDetail">连接本地服务后可触发只读刷新和报告补跑。</small>
      </div>
      <div>
        <span>入口操作</span>
        <strong>Web first</strong>
        <div class="web-runtime-actions">
          <a class="action secondary" id="webAppLink" href="{esc(WEB_APP_URL)}">打开网页主控台</a>
          <button class="action secondary" id="runtimeStatusButton" type="button">刷新网页状态</button>
        </div>
      </div>
    </div>

    <section class="recommendation-block priority" id="recommendations">
      <div class="section-head">
        <div>
          <h2>推荐下注板块</h2>
          <p class="subtitle">{esc(recommendation_note)} 分析一致性用于判断模型、盘口和资金面是否同向；概率赔率编辑只在页面内即时重算 EV，不写回报告；风险调整分用于把正EV、Edge和RoR合并成排序参考。</p>
        </div>
        <div class="actions compact-actions">
          <button id="activeTestButton" class="action primary" type="button">主动测试与自动补缺</button>
          <button id="backfillButton" class="action danger" type="button">补跑缺失分析/报告</button>
          <div id="priorityActiveMessage" class="message priority-message">点击后回测时间线：每4-5小时至少一次分析、每天一份报告；发现缺口会在 raw 通过时主动补跑。</div>
        </div>
      </div>
      {decision_strip_html(rec_rows, execution_allowed=execution_allowed, gate_message=gate_message, latest_commit=latest_commit, timeline=timeline)}
      {recommendation_basis_html(recommendation_operations)}
      {probability_engine_html(recommendation_operations)}
      {market_funding_analysis_html(recommendation_operations)}
      {recommendations_table(rec_rows)}
    </section>

    {recommendation_operations_html(recommendation_operations)}
    {strategy_performance_html(strategy_performance)}
    {report_evolution_html(report_evolution)}

    <div class="hero">
      <section>
        <h2>今日操作摘要</h2>
        <p class="subtitle">基于最新可信报告 {esc(report_date_label(text(latest_commit.get("report_date"))))}。{esc(hero_note)}</p>
        <div class="gate-warning">{esc(gate_message)}</div>
        <div class="actions">{action_buttons}</div>
      </section>
      <div class="summary-card {esc(summary_card_class)}">
        <h3>操作摘要</h3>
        <div class="big">{money(recommended_exposure)}</div>
        <p class="muted">{esc(exposure_label)} / 买入候选 {buy_count} 条</p>
        <p class="note">{esc(top_summary)}</p>
      </div>
    </div>

    {available_board_strategy_html(available_strategy)}
    {partial_daily_research_html(partial_daily_research)}
    {fixture_sanity_html(fixture_sanity)}

    {action_cards_html(rec_rows)}

    {raw_refresh_action_html(raw_health, readiness)}
    {raw_refresh_recovery_html(raw_recovery)}
    {live_board_discovery_html(live_discovery)}

    <section id="active-test" style="margin-top:16px;">
      <h2>主动测试与补跑</h2>
      {active_test_decision_html(timeline, raw_health)}
      <div id="activeMessage" class="message">规则：每天至少 4 次分析；目标时间窗为 00/05/10/15/20 点附近；每天至少 1 份报告。点击后先显示快照，再更新实时结果；若公开盘口 raw 未就绪，系统只补研究诊断，不启动正式补跑。</div>
      <div id="timelinePanel">{timeline_summary_html(timeline)}</div>
    </section>

    {active_timeline_report_html(active_timeline_report)}

    {product_readiness_html(product_readiness)}
    {goal_traceability_html(goal_traceability)}
    {position_monitor_html(position_monitor)}
    {automation_maturity_html(maturity)}
    {private_position_action_html(readiness)}
    {report_intelligence_html(intelligence)}
    {source_model_registry_html(source_model_registry)}
    {model_comparison_dashboard_html(model_comparison)}
    {model_divergence_review_html(model_divergence_review)}
    {report_visual_inventory_html(visual_inventory)}
    {automation_doctor_html(automation_doctor)}

    <div class="grid">
      <div class="metric">
        <div class="label">当前可信报告</div>
        <div class="value">{esc(report_date_label(text(latest_commit.get("report_date"))))}</div>
        <span class="status {html_status_class(latest_status)}">{esc(latest_status)}</span>
      </div>
      <div class="metric">
        <div class="label">当前 attempted run</div>
        <div class="value">{esc(latest_attempt_run)}</div>
        <span class="status blocked">未发布</span>
      </div>
      <div class="metric">
        <div class="label">Raw 数据</div>
        <div class="value">{esc(raw_health.get("ready_required_target_count", "5/5"))}</div>
        <span class="status {html_status_class(raw_health.get("status"))}">{esc(raw_health.get("status"))}</span>
      </div>
      <div class="metric">
        <div class="label">Runner 最新验证</div>
        <div class="value">{esc(run_store.get("automation_run_id", "待同步"))}</div>
        <span class="status {html_status_class(runner.get("status"))}">{esc(runner.get("verify_mode", runner.get("status")))}</span>
      </div>
    </div>

    <div class="layout">
      <section>
        <h2>报告状态</h2>
        <table>
          <thead><tr><th>项目</th><th>当前值</th></tr></thead>
          <tbody>
            <tr><td>正式报告可发布</td><td><span class="status {html_status_class(readiness.get("formal_report_publish_ready"))}">{yn(readiness.get("formal_report_publish_ready"))}</span></td></tr>
            <tr><td>Recurring automation ready</td><td><span class="status {html_status_class(readiness.get("recurring_automation_ready"))}">{yn(readiness.get("recurring_automation_ready"))}</span></td></tr>
            <tr><td>可信 run id</td><td>{esc(latest_commit.get("run_id"))}</td></tr>
            <tr><td>Ready boards</td><td>{esc(latest_commit.get("ready_required_boards"))}</td></tr>
            <tr><td>Report index runner history</td><td>{esc(report_index.get("automation_run_count", "待同步"))}</td></tr>
            <tr><td>PDF 视觉 QA</td><td>{esc(visual.get("renderer", "待同步"))} / {esc(visual.get("visible_page_count", "0"))}/{esc(visual.get("rendered_page_count", "0"))} 页可见</td></tr>
          </tbody>
        </table>
      </section>

      <section>
        <h2>当前阻塞</h2>
        <ul>{blocker_rows}</ul>
        <p class="note">阻塞时保持上一个可信成功报告，不把 failed run 当成下注日报。</p>
      </section>
    </div>

    <section id="reports" style="margin-top:16px;">
      <h2>公开产物入口</h2>
      <table>
        <thead><tr><th>产物</th><th>文件</th></tr></thead>
        <tbody>{artifact_rows}</tbody>
      </table>
    </section>
  </main>
  <script>
    const PRIMARY_WEB_APP_URL = "{esc(WEB_APP_URL)}";
    function webAppPromptText() {{
      return "当前为静态只读预览；运行操作请使用网页主控台 " + PRIMARY_WEB_APP_URL + " 或 Downloads 的 .app 入口。";
    }}
    function setRuntimePanel(mode, detail, controlStatus, controlDetail, state) {{
      const panel = document.getElementById("webRuntimePanel");
      if (panel) {{
        panel.classList.remove("static", "offline");
        if (state) panel.classList.add(state);
      }}
      const modeNode = document.getElementById("runtimeMode");
      const detailNode = document.getElementById("runtimeModeDetail");
      const controlsNode = document.getElementById("runtimeControlsStatus");
      const controlsDetailNode = document.getElementById("runtimeControlsDetail");
      if (modeNode) modeNode.textContent = mode;
      if (detailNode) detailNode.textContent = detail;
      if (controlsNode) controlsNode.textContent = controlStatus;
      if (controlsDetailNode) controlsDetailNode.textContent = controlDetail;
    }}
    function updateOperationPanel(panel) {{
      if (!panel) return;
      const headlineNode = document.getElementById("operationHeadline");
      const subheadlineNode = document.getElementById("operationSubheadline");
      const primaryNode = document.getElementById("operationPrimaryAction");
      const nextTitleNode = document.getElementById("operationNextTitle");
      const nextDetailNode = document.getElementById("operationNextDetail");
      if (headlineNode && panel.headline) headlineNode.textContent = panel.headline;
      if (subheadlineNode && panel.subheadline) subheadlineNode.textContent = panel.subheadline;
      if (primaryNode) {{
        if (panel.primary_label) primaryNode.textContent = panel.primary_label;
        if (panel.primary_href) primaryNode.setAttribute("href", panel.primary_href);
      }}
      if (nextTitleNode && panel.quick_steps && panel.quick_steps[1]) {{
        nextTitleNode.textContent = panel.quick_steps[1].detail || panel.next_safe_action || "等待最终验证";
      }}
      if (nextDetailNode && panel.next_safe_action) nextDetailNode.textContent = panel.next_safe_action;
    }}
    async function refreshRuntimeStatus() {{
      if (!location.protocol.startsWith("http")) {{
        setRuntimePanel("静态只读预览", "当前文件可查看报告，但不能启动只读刷新、补跑或持仓读取。", "运行按钮不可用", "请打开网页主控台或 Downloads 的 .app 入口。", "static");
        return;
      }}
      setRuntimePanel("网页主控台已连接", "当前正在通过本地网页运行。", "读取状态中", "正在检查 /api/status。", "");
      try {{
        const res = await fetch("/api/status");
        const payload = await res.json();
        const interaction = payload.interaction_mode || {{}};
        updateOperationPanel(payload.operation_panel);
        const rawStatus = payload.raw_refresh && payload.raw_refresh.status ? payload.raw_refresh.status : "unknown";
        const privateStatus = payload.private_position && payload.private_position.status ? payload.private_position.status : "unknown";
        const controls = interaction.runtime_controls_enabled === false ? "运行按钮受限" : "运行按钮走本地 API";
        setRuntimePanel(
          interaction.current_surface === "local_web_app" ? "网页主控台已连接" : "网页主控台优先",
          "主入口：" + (interaction.primary_entry || PRIMARY_WEB_APP_URL) + "；静态 HTML 角色：" + (interaction.static_html_role || "read_only_preview"),
          controls,
          "Raw " + rawStatus + "；私有持仓 " + privateStatus + "；仍不自动下注。",
          ""
        );
      }} catch (err) {{
        setRuntimePanel("网页主控台离线", "本地网页已打开但状态接口暂不可读。", "运行按钮需复核", "错误：" + err.message, "offline");
      }}
    }}
    function formatPct(value) {{
      if (!Number.isFinite(value)) return "待校准";
      return (value * 100).toFixed(2) + "%";
    }}
    function formatPp(value) {{
      if (!Number.isFinite(value)) return "待校准";
      return (value >= 0 ? "+" : "") + (value * 100).toFixed(2) + "pp";
    }}
    function formatDecimal(value) {{
      if (!Number.isFinite(value)) return "待校准";
      return value.toFixed(2);
    }}
    function formatSignedDecimal(value) {{
      if (!Number.isFinite(value)) return "待校准";
      return (value >= 0 ? "+" : "") + value.toFixed(2);
    }}
    function formatMoney(value) {{
      if (!Number.isFinite(value)) return "AUD 0";
      return "AUD " + value.toFixed(0);
    }}
    function edgeQuality(edgeGap) {{
      if (!Number.isFinite(edgeGap)) return "待校准";
      if (edgeGap >= 0.02) return "强通过";
      if (edgeGap >= 0) return "通过";
      if (edgeGap >= -0.01) return "接近门槛";
      return "未达门槛";
    }}
    function riskGradeValue(risk) {{
      if (!Number.isFinite(risk)) return "待校准";
      if (risk < 0.02) return "低";
      if (risk < 0.05) return "中";
      if (risk < 0.10) return "偏高";
      return "高";
    }}
    function riskDriverText(edge, edgeGap, risk, stake, bankroll, riskFlags, prob, odds) {{
      const drivers = [];
      if (Number.isFinite(edgeGap) && edgeGap < 0) drivers.push("Edge未达门槛");
      if (Number.isFinite(edge) && edge < 0) drivers.push("模型概率低于盈亏平衡");
      const stakeFraction = Number.isFinite(stake) && Number.isFinite(bankroll) && bankroll > 0 ? stake / bankroll : NaN;
      if (Number.isFinite(stakeFraction) && stakeFraction > 0.02) drivers.push("单注超过2%资金上限");
      if (Number.isFinite(prob) && Number.isFinite(odds) && odds > 1 && Number.isFinite(stakeFraction)) {{
        const fullKelly = Math.max(0, prob - (1 - prob) / (odds - 1));
        const halfKelly = fullKelly * 0.5;
        if (halfKelly > 0 && stakeFraction / halfKelly > 1) drivers.push("仓位超过半Kelly");
      }}
      if (Number.isFinite(risk) && risk >= 0.05) drivers.push("RoR偏高");
      if (Number.isFinite(riskFlags) && riskFlags > 0) drivers.push("赛前事件风险" + riskFlags + "项");
      return drivers.slice(0, 4).join("；") || "无明显额外触发因素";
    }}
    function stakeDisciplineStatus(stakeFraction, halfKelly) {{
      if (!Number.isFinite(stakeFraction)) return "待校准";
      if (stakeFraction > 0.02) return "超过2%上限";
      if (Number.isFinite(halfKelly) && halfKelly > 0 && stakeFraction / halfKelly > 1) return "超过半Kelly";
      if (stakeFraction <= 0) return "观察";
      return "通过";
    }}
    function rorReviewStatus(risk) {{
      if (!Number.isFinite(risk)) return "待校准";
      return risk >= 0.05 ? "需复核/降仓" : "通过";
    }}
    function diagnosticConclusion(ev, edgeGap, oddsBuffer, risk, stakeStatus) {{
      const passEdge = Number.isFinite(edgeGap) && edgeGap >= 0;
      const passOdds = !Number.isFinite(oddsBuffer) || oddsBuffer >= 0;
      const passRisk = rorReviewStatus(risk) === "通过";
      const passStake = stakeStatus === "通过" || stakeStatus === "观察";
      if (Number.isFinite(ev) && ev > 0 && passEdge && passOdds && passRisk && passStake) return "研究买入候选";
      if (Number.isFinite(ev) && ev > 0 && passEdge) return "正EV但需复核";
      return "观察或放弃";
    }}
    function valueSignalLabel(ev, edgeGap, oddsBuffer, risk) {{
      if (!Number.isFinite(ev) || !Number.isFinite(edgeGap)) return "待校准";
      if (Number.isFinite(oddsBuffer) && oddsBuffer < 0) return "价格已走差";
      if (ev > 0 && edgeGap >= 0 && (!Number.isFinite(risk) || risk < 0.05)) return "价值通过";
      if (ev > 0 && edgeGap >= 0) return "价值通过但RoR复核";
      if (ev > 0) return "EV正但Edge不足";
      return "观察或放弃";
    }}
    function riskAdjustedValueScore(ev, edgeGap, risk) {{
      if (!Number.isFinite(ev) || !Number.isFinite(risk)) return NaN;
      return ev + Math.max(0, Number.isFinite(edgeGap) ? edgeGap : 0) - risk;
    }}
    function estimateRiskOfRuin(prob, odds, stake, bankroll, riskFlags) {{
      if (!Number.isFinite(prob) || !Number.isFinite(odds) || odds <= 1 || !Number.isFinite(bankroll) || bankroll <= 0) return NaN;
      if (!Number.isFinite(stake) || stake <= 0) return 0;
      const p = Math.min(1, Math.max(0, prob));
      const stakeFraction = Math.min(1, Math.max(0, stake / bankroll));
      const ev = p * odds - 1;
      const lossProbability = Math.max(0, 1 - p);
      const fullKelly = Math.max(0, p - (1 - p) / (odds - 1));
      const halfKelly = fullKelly * 0.5;
      let risk = 0.01 + Math.min(0.2, lossProbability * stakeFraction * 1.5);
      if (ev <= 0) {{
        risk += 0.12 + Math.min(0.35, lossProbability * stakeFraction * 4);
      }} else {{
        const overbetRatio = stakeFraction / Math.max(halfKelly, 0.002);
        if (overbetRatio > 1) {{
          risk += Math.min(0.4, (overbetRatio - 1) * 0.08);
        }} else if (overbetRatio < 0.5) {{
          risk *= 0.5;
        }}
      }}
      risk += Math.min(0.06, Math.max(0, riskFlags || 0) * 0.015);
      return Math.max(0, Math.min(0.95, risk));
    }}
    function fundingGrade(score) {{
      if (!Number.isFinite(score)) return "待校准";
      if (score >= 75) return "强";
      if (score >= 60) return "中强";
      if (score >= 45) return "中性";
      if (score >= 30) return "偏弱";
      return "弱";
    }}
    function fundingBiasLabel(score) {{
      if (!Number.isFinite(score)) return "待校准";
      if (score >= 65) return "资金倾向支持";
      if (score >= 55) return "轻微支持";
      if (score >= 45) return "资金中性";
      return "资金倾向不支持";
    }}
    function estimateFundingScore(ev, edge, arbitrageRate, priceTolerance, riskOfRuin, liquidity, depth, dailyFloat, riskFlags) {{
      const safeEv = Number.isFinite(ev) ? ev : 0;
      const safeEdge = Number.isFinite(edge) ? edge : 0;
      const safeArb = Number.isFinite(arbitrageRate) ? arbitrageRate : Math.max(0, safeEv);
      const safeTolerance = Number.isFinite(priceTolerance) ? priceTolerance : 0;
      const safeRisk = Number.isFinite(riskOfRuin) ? riskOfRuin : 0;
      const safeLiquidity = Number.isFinite(liquidity) ? liquidity : 0.55;
      const safeDepth = Number.isFinite(depth) ? depth : 0.55;
      const safeFloat = Number.isFinite(dailyFloat) ? dailyFloat : 0.05;
      const safeFlags = Math.max(0, Number.isFinite(riskFlags) ? riskFlags : 0);
      const valuePressure = safeEv * 42 + safeEdge * 220 + safeArb * 26 + safeTolerance * 18;
      const liquidityPressure = (safeLiquidity - 0.55) * 18 + (safeDepth - 0.55) * 10;
      const riskPressure = safeRisk * 80 + safeFloat * 22 + safeFlags * 1.5;
      return Math.max(0, Math.min(100, 50 + valuePressure + liquidityPressure - riskPressure));
    }}
    function setActiveMessage(text) {{
      ["priorityActiveMessage", "activeMessage"].forEach((id) => {{
        const node = document.getElementById(id);
        if (node) node.textContent = text;
      }});
    }}
    function recalcRow(row) {{
      const probInput = row.querySelector(".prob-input");
      const oddsInput = row.querySelector(".odds-input");
      const evCell = row.querySelector(".ev-cell");
      const edgeCell = row.querySelector(".edge-cell");
      const arbCell = row.querySelector(".arb-cell");
      const rorCell = row.querySelector(".ror-cell");
      const fundingCell = row.querySelector(".funding-cell");
      if (!probInput || !oddsInput || !evCell) return;
      const prob = Number(probInput.value) / 100;
      const odds = Number(oddsInput.value);
      const stake = Number(evCell.dataset.stake || 0);
      const bankroll = Number((rorCell && rorCell.dataset.bankroll) || {DEFAULT_BANKROLL_REFERENCE_AUD});
      const riskFlags = Number((rorCell && rorCell.dataset.riskFlags) || 0);
      if (!Number.isFinite(prob) || !Number.isFinite(odds) || odds <= 1) {{
        evCell.textContent = "待校准";
        evCell.classList.remove("positive-ev", "negative-ev");
        evCell.classList.add("watch-ev");
        if (edgeCell) {{
          const edgeValueNode = edgeCell.querySelector(".edge-value");
          const edgeDetailNode = edgeCell.querySelector(".edge-detail");
          if (edgeValueNode) edgeValueNode.textContent = "待校准";
          if (edgeDetailNode) edgeDetailNode.textContent = "概率 待校准 / 盈亏平衡 待校准 / 门槛 待校准 / 差 待校准 / 待校准";
        }}
        if (arbCell) {{
          const arbValueNode = arbCell.querySelector(".arb-value");
          const arbDetailNode = arbCell.querySelector(".arb-detail");
          if (arbValueNode) {{
            arbValueNode.textContent = "待校准";
          }} else {{
            arbCell.textContent = "待校准";
          }}
          if (arbDetailNode) arbDetailNode.textContent = "每AUD100 待校准 · 非surebet";
        }}
        if (rorCell) {{
          const riskValueNode = rorCell.querySelector(".risk-value");
          const riskDetailNode = rorCell.querySelector(".risk-detail");
          if (riskValueNode) riskValueNode.textContent = "待校准";
          if (riskDetailNode) riskDetailNode.textContent = "待校准 · 半Kelly 待校准 / 仓位 待校准 · 无明显额外触发因素";
        }}
        if (fundingCell) {{
          const fundingValueNode = fundingCell.querySelector(".funding-value");
          const fundingDetailNode = fundingCell.querySelector(".funding-detail");
          if (fundingValueNode) fundingValueNode.textContent = "待校准";
          if (fundingDetailNode) fundingDetailNode.textContent = "待校准 / 待校准 · 净 AUD 0";
        }}
        const reasonRow = row.nextElementSibling;
        if (reasonRow && reasonRow.classList.contains("reason-row")) {{
          [".diag-value-signal", ".diag-min-odds", ".diag-odds-buffer", ".diag-price-tolerance", ".diag-profit-100", ".diag-profit", ".diag-cap-usage", ".diag-kelly-margin", ".diag-value-score", ".diag-stake-status", ".diag-ror-status", ".diag-conclusion", ".diag-funding-score"].forEach((selector) => {{
            const node = reasonRow.querySelector(selector);
            if (node) node.textContent = "待校准";
          }});
        }}
        return;
      }}
      const ev = prob * odds - 1;
      const breakeven = 1 / odds;
      const edge = prob - breakeven;
      const edgeThreshold = Number((edgeCell && edgeCell.dataset.edgeThreshold) || NaN);
      const edgeGap = Number.isFinite(edgeThreshold) ? edge - edgeThreshold : NaN;
      const arbitrageRate = Math.max(0, ev);
      const riskOfRuin = estimateRiskOfRuin(prob, odds, stake, bankroll, riskFlags);
      const fullKelly = Math.max(0, prob - (1 - prob) / (odds - 1));
      const halfKelly = fullKelly * 0.5;
      const stakeFraction = Number.isFinite(stake) && Number.isFinite(bankroll) && bankroll > 0 ? stake / bankroll : NaN;
      const stakeCapRatio = Number.isFinite(stakeFraction) ? stakeFraction / 0.02 : NaN;
      const kellyMargin = Number.isFinite(halfKelly) && halfKelly > 0 ? 1 - (stakeFraction / halfKelly) : NaN;
      const profit = stake * ev;
      const minAcceptableOdds = Number.isFinite(edgeThreshold) && prob > edgeThreshold ? 1 / (prob - edgeThreshold) : NaN;
      const oddsBuffer = Number.isFinite(minAcceptableOdds) ? odds - minAcceptableOdds : NaN;
      const priceTolerance = Number.isFinite(oddsBuffer) && Number.isFinite(odds) && odds > 0 ? oddsBuffer / odds : NaN;
      const profitPer100 = 100 * ev;
      const stakeStatus = stakeDisciplineStatus(stakeFraction, halfKelly);
      const rorStatus = rorReviewStatus(riskOfRuin);
      const conclusion = diagnosticConclusion(ev, edgeGap, oddsBuffer, riskOfRuin, stakeStatus);
      const valueSignal = valueSignalLabel(ev, edgeGap, oddsBuffer, riskOfRuin);
      const valueScore = riskAdjustedValueScore(ev, edgeGap, riskOfRuin);
      const fundingLiquidity = Number((fundingCell && fundingCell.dataset.liquidity) || NaN);
      const fundingDepth = Number((fundingCell && fundingCell.dataset.depth) || NaN);
      const fundingDailyFloat = Number((fundingCell && fundingCell.dataset.dailyFloat) || NaN);
      const fundingScore = estimateFundingScore(ev, edge, arbitrageRate, priceTolerance, riskOfRuin, fundingLiquidity, fundingDepth, fundingDailyFloat, riskFlags);
      const fundingTotal = Number((fundingCell && fundingCell.dataset.totalFunds) || NaN);
      const fundingNet = Number.isFinite(fundingTotal) && Number.isFinite(fundingScore) ? fundingTotal * ((fundingScore - 50) / 100) : NaN;
      evCell.textContent = formatPct(ev) + (stake > 0 ? " / AUD " + profit.toFixed(0) : "");
      evCell.dataset.ev = String(ev);
      if (edgeCell) {{
        const edgeValueNode = edgeCell.querySelector(".edge-value");
        const edgeDetailNode = edgeCell.querySelector(".edge-detail");
        if (edgeValueNode) edgeValueNode.textContent = formatPp(edge);
        if (edgeDetailNode) edgeDetailNode.textContent = "概率 " + formatPct(prob) + " / 盈亏平衡 " + formatPct(breakeven) + " / 门槛 " + formatPp(edgeThreshold) + " / 差 " + formatPp(edgeGap) + " / " + edgeQuality(edgeGap);
        edgeCell.dataset.edge = String(edge);
      }}
      if (arbCell) {{
        const arbValueNode = arbCell.querySelector(".arb-value");
        const arbDetailNode = arbCell.querySelector(".arb-detail");
        if (arbValueNode) {{
          arbValueNode.textContent = formatPct(arbitrageRate);
        }} else {{
          arbCell.textContent = formatPct(arbitrageRate);
        }}
        if (arbDetailNode) arbDetailNode.textContent = "每AUD100 " + formatMoney(profitPer100) + " · 非surebet";
        arbCell.dataset.arb = String(arbitrageRate);
      }}
      if (rorCell) {{
        const riskValueNode = rorCell.querySelector(".risk-value");
        const riskDetailNode = rorCell.querySelector(".risk-detail");
        const grade = riskGradeValue(riskOfRuin);
        if (riskValueNode) riskValueNode.textContent = formatPct(riskOfRuin);
        if (riskDetailNode) riskDetailNode.textContent = grade + " · 半Kelly " + formatPct(halfKelly) + " / 仓位 " + formatPct(stakeFraction) + " · 上限占用 " + formatPct(stakeCapRatio) + " · " + riskDriverText(edge, edgeGap, riskOfRuin, stake, bankroll, riskFlags, prob, odds);
        rorCell.dataset.risk = String(riskOfRuin);
      }}
      if (fundingCell) {{
        const fundingValueNode = fundingCell.querySelector(".funding-value");
        const fundingDetailNode = fundingCell.querySelector(".funding-detail");
        const fundingScoreText = Number.isFinite(fundingScore) ? fundingScore.toFixed(1) : "待校准";
        const fundingBias = fundingBiasLabel(fundingScore);
        const fundingGradeText = fundingGrade(fundingScore);
        if (fundingValueNode) fundingValueNode.textContent = fundingScoreText;
        if (fundingDetailNode) fundingDetailNode.textContent = fundingBias + " / " + fundingGradeText + " · 净 " + formatMoney(fundingNet);
        fundingCell.dataset.fundingScore = String(fundingScore);
      }}
      const reasonRow = row.nextElementSibling;
      if (reasonRow && reasonRow.classList.contains("reason-row")) {{
        const setDiag = (selector, value) => {{
          const node = reasonRow.querySelector(selector);
          if (node) node.textContent = value;
        }};
        setDiag(".diag-min-odds", formatDecimal(minAcceptableOdds));
        setDiag(".diag-odds-buffer", formatSignedDecimal(oddsBuffer));
        setDiag(".diag-price-tolerance", formatPct(priceTolerance));
        setDiag(".diag-profit-100", formatMoney(profitPer100));
        setDiag(".diag-profit", formatMoney(profit));
        setDiag(".diag-cap-usage", formatPct(stakeCapRatio));
        setDiag(".diag-kelly-margin", formatPct(kellyMargin));
        setDiag(".diag-value-score", formatPct(valueScore));
        setDiag(".diag-value-signal", valueSignal);
        setDiag(".diag-stake-status", stakeStatus);
        setDiag(".diag-ror-status", rorStatus);
        setDiag(".diag-conclusion", conclusion);
        setDiag(".diag-funding-score", (Number.isFinite(fundingScore) ? fundingScore.toFixed(1) : "待校准") + " / " + fundingBiasLabel(fundingScore));
      }}
      evCell.classList.toggle("positive-ev", ev > 0);
      evCell.classList.toggle("negative-ev", ev < 0);
      evCell.classList.toggle("watch-ev", ev === 0);
    }}
    document.querySelectorAll("tr[data-rec-row]").forEach((row) => {{
      row.querySelectorAll("input").forEach((input) => input.addEventListener("input", () => recalcRow(row)));
    }});

    function shortSlot(slot) {{
      return String(slot || "").replaceAll(":00", "").replace("-", " - ");
    }}
    function slotClass(slot, item) {{
      const covered = new Set(item.covered_slots || []);
      const missing = new Set(item.missing_slots || []);
      if (covered.has(slot)) return "covered";
      if (missing.has(slot)) return "missing";
      return "unknown";
    }}
    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, (ch) => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }}[ch]));
    }}
    function actionToken() {{
      const meta = document.querySelector('meta[name="tab-fifa-action-token"]');
      return meta ? (meta.getAttribute("content") || "") : "";
    }}
    function actionHeaders() {{
      const token = actionToken();
      return token ? {{"X-TAB-FIFA-Action-Token": token}} : {{}};
    }}
    function postOptions() {{
      return {{ method: "POST", headers: actionHeaders() }};
    }}
    function jsonPostOptions(payload) {{
      return {{
        method: "POST",
        headers: Object.assign({{"Content-Type": "application/json"}}, actionHeaders()),
        body: JSON.stringify(payload || {{}})
      }};
    }}
    async function fetchJson(url, options) {{
      const res = await fetch(url, options || {{}});
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    }}
    async function postJson(endpoint) {{
      return await fetchJson(endpoint, postOptions());
    }}
    async function postJsonBody(endpoint, payload) {{
      return await fetchJson(endpoint, jsonPostOptions(payload));
    }}
    function timelineHtml(payload) {{
      const summary = payload.summary || {{}};
      const rule = payload.cadence_rule || {{}};
      const autoBackfill = payload.auto_backfill || payload.backfill_result || {{}};
      const partial = autoBackfill.partial_daily_research || payload.partial_daily_research || {{}};
      const runtime = payload.active_test_runtime || {{}};
      const runtimeText = runtime.elapsed_ms ? `${{(runtime.elapsed_ms / 1000).toFixed(1)}}秒 / ${{runtime.mode || "timeline"}}` : "已生成";
      const previewMode = runtime.mode === "cached_snapshot_fast_preview";
      const fallbackWarning = payload.fallback_used
        ? `<div class="active-warning">${{previewMode ? "实时结果返回前，先展示最近一次时间线快照。" : "实时主动测试失败，当前展示最近一次时间线快照；本次未启动自动补缺。"}}原因：${{escapeHtml(payload.warning || "unknown")}}</div>`
        : "";
      const slots = rule.target_slots || [];
      const rows = (payload.days || []).slice(-8).map((item) => {{
        const blocked = item.needs_backfill;
        const reason = (item.backfill_reasons || []).join("；") || "无需补跑";
        const slotCells = slots.map((slot) => `<span class="slot-chip ${{slotClass(slot, item)}}">${{escapeHtml(shortSlot(slot))}}</span>`).join("");
        return `<tr><td>${{escapeHtml(item.display_date || "")}}</td><td><div class="slot-strip">${{slotCells}}</div></td><td>${{item.effective_analysis_count || 0}}/${{rule.min_analyses_per_day || 4}}</td><td>${{item.formal_report_exists ? "有" : "缺失"}}</td><td><span class="status ${{blocked ? "blocked" : "ok"}}">${{blocked ? "缺口" : "完整"}}</span></td><td>${{escapeHtml(reason)}}</td></tr>`;
      }}).join("");
      const queueRows = (payload.backfill_queue || []).slice(0, 5).map((item) => {{
        return `<tr><td>${{item.repair_rank || ""}}</td><td>${{escapeHtml(item.display_date || "")}}</td><td>${{item.priority_score || 0}}</td><td>${{escapeHtml(item.reason || "")}}</td><td>${{escapeHtml(item.priority_reason || "")}}</td></tr>`;
      }}).join("");
      const queueHtml = queueRows
        ? `<h3 class="subsection-title">补跑优先队列</h3><div class="table-scroll compact"><table><thead><tr><th>顺序</th><th>日期</th><th>分数</th><th>缺口</th><th>排序依据</th></tr></thead><tbody>${{queueRows}}</tbody></table></div>`
        : `<div class="empty compact-note">当前没有需要补跑的日期。</div>`;
      return `
        ${{fallbackWarning}}
        <div class="timeline-metrics">
          <div><span>检查天数</span><strong>${{summary.day_count || 0}}</strong></div>
          <div><span>分析缺口日</span><strong>${{summary.missing_analysis_day_count || 0}}</strong></div>
          <div><span>日报缺口日</span><strong>${{summary.missing_report_day_count || 0}}</strong></div>
          <div><span>待补队列</span><strong>${{summary.backfill_queue_count || 0}}</strong></div>
          <div><span>研究诊断补写</span><strong>${{partial.status || "missing"}}</strong></div>
          <div><span>补写执行金额</span><strong>${{formatMoney(partial.current_executable_new_stake_aud || 0)}}</strong></div>
          <div><span>结果模式</span><strong>${{payload.fallback_used ? "缓存降级" : "新鲜回测"}}</strong></div>
          <div><span>接口耗时</span><strong>${{runtimeText}}</strong></div>
        </div>
        ${{partial.status ? `<div class="compact-note">研究诊断日报：${{partial.ready ? "ready" : "not ready"}} / ${{partial.pdf || "no pdf"}} / 正式补跑${{autoBackfill.blocked ? "因 raw blocked 暂停" : "状态待复核"}}</div>` : ""}}
        <div class="table-scroll compact">
          <table><thead><tr><th>日期</th><th>时段覆盖</th><th>有效分析</th><th>日报</th><th>状态</th><th>补跑判断</th></tr></thead><tbody>${{rows}}</tbody></table>
        </div>${{queueHtml}}`;
    }}
    function activeSkeletonHtml() {{
      return `
        <div class="active-progress" aria-live="polite">
          <div><span>1. 读取时间线</span><strong>正在检查每日 4-5 小时节奏</strong></div>
          <div><span>2. 识别缺口</span><strong>扫描分析次数和日报 PDF</strong></div>
          <div><span>3. 安全补缺</span><strong>raw 未就绪时只补研究诊断</strong></div>
          <div><span>4. 返回结果</span><strong>优先直接显示，不等待重建入口</strong></div>
        </div>
        <div class="empty compact-note">主动测试运行中，通常几秒内返回；若实时检查失败，会自动展示最近一次时间线快照。</div>
      `;
    }}
    async function renderCachedActiveSnapshot(reason) {{
      const panel = document.getElementById("timelinePanel");
      if (!panel) return false;
      try {{
        const payload = await fetchJson("app_assets/active_timeline_latest.json");
        if (!payload || !payload.summary) return false;
        payload.fallback_used = true;
        payload.warning = reason || "实时主动测试仍在运行，先展示最近一次时间线快照。";
        payload.active_test_runtime = {{
          elapsed_ms: 0,
          mode: "cached_snapshot_fast_preview",
          downloads_rebuild: "skipped_for_fast_result"
        }};
        panel.innerHTML = timelineHtml(payload);
        setActiveMessage("已先展示最近一次时间线快照；实时主动测试仍在运行，稍后会自动覆盖结果。");
        return true;
      }} catch (err) {{
        return false;
      }}
    }}
    let activeTestRequestSeq = 0;
    async function activeTest() {{
      const requestSeq = ++activeTestRequestSeq;
      const httpMode = location.protocol.startsWith("http");
      const button = document.getElementById("activeTestButton");
      const originalText = button ? button.textContent : "";
      if (button) {{
        button.disabled = true;
        button.textContent = "测试中...";
      }}
      setActiveMessage("正在主动测试：读取时间线、识别缺口、判断是否可安全补缺。");
      const panel = document.getElementById("timelinePanel");
      if (panel) panel.innerHTML = activeSkeletonHtml();
      try {{
        let cachedRendered = false;
        if (httpMode) {{
          const cachePreview = renderCachedActiveSnapshot("实时结果返回前，先展示最近一次时间线快照。").then((value) => {{
            cachedRendered = value;
            return value;
          }});
          await Promise.race([cachePreview, new Promise((resolve) => setTimeout(resolve, 500))]);
        }}
        const url = httpMode ? "/api/active-test" : "app_assets/active_timeline_latest.json";
        const options = httpMode ? postOptions() : {{}};
        const payload = await fetchJson(url, options);
        if (requestSeq !== activeTestRequestSeq) return;
        if (payload.ok === false) throw new Error(payload.error || "主动测试失败");
        document.getElementById("timelinePanel").innerHTML = timelineHtml(payload);
        const summary = payload.summary || {{}};
        const autoBackfill = payload.auto_backfill || {{}};
        const fillText = !httpMode
          ? webAppPromptText()
          : payload.fallback_used
          ? (payload.auto_backfill && payload.auto_backfill.message ? payload.auto_backfill.message : "实时检查失败，已展示最近一次时间线快照。")
          : autoBackfill.blocked
          ? (autoBackfill.message || "公开盘口 raw 未就绪；TAB 拒绝 AI controlled access 时需授权数据源或用户导出导入。")
          : autoBackfill.started
          ? "已自动启动安全补跑。"
          : (autoBackfill.message || "未启动补跑。");
        setActiveMessage(`主动测试完成：分析缺口日 ${{summary.missing_analysis_day_count || 0}}，日报缺口日 ${{summary.missing_report_day_count || 0}}。${{fillText}}`);
        if (autoBackfill.started) {{
          setTimeout(refreshRuntimeStatus, 1200);
          setTimeout(refreshRuntimeStatus, 5000);
        }}
      }} catch (err) {{
        const recovered = await renderCachedActiveSnapshot("实时主动测试失败：" + err.message + "。当前展示最近一次时间线快照。");
        setActiveMessage(recovered ? "实时主动测试失败，已保留最近一次时间线快照：" + err.message : "主动测试失败：" + err.message);
        if (!recovered && panel) panel.innerHTML = `<div class="active-warning">主动测试失败：${{escapeHtml(err.message)}}。请确认网页主控台仍在运行，或稍后重试。</div>` + panel.innerHTML;
      }} finally {{
        if (button) {{
          button.disabled = false;
          button.textContent = originalText || "主动测试与自动补缺";
        }}
      }}
    }}
    async function backfillMissing() {{
      if (!location.protocol.startsWith("http")) {{
        setActiveMessage(webAppPromptText());
        return;
      }}
      setActiveMessage("正在启动安全补跑...");
      try {{
        const payload = await postJson("/api/backfill-missing");
        if (!payload.ok) throw new Error(payload.error || "补跑启动失败");
        setActiveMessage(payload.message || "补跑已启动，完成后点击主动测试刷新。");
      }} catch (err) {{
        setActiveMessage("补跑启动失败：" + err.message);
      }}
    }}
    document.getElementById("activeTestButton").addEventListener("click", activeTest);
    document.getElementById("backfillButton").addEventListener("click", backfillMissing);
    async function postLocal(endpoint, busyText) {{
      const msg = document.getElementById("privateMessage");
      if (!location.protocol.startsWith("http")) {{
        msg.textContent = webAppPromptText();
        return;
      }}
      msg.textContent = busyText;
      try {{
        const payload = await postJson(endpoint);
        if (!payload.ok) throw new Error(payload.error || "启动失败");
        msg.textContent = payload.message || "已启动。";
      }} catch (err) {{
        msg.textContent = "启动失败：" + err.message;
      }}
    }}
    document.getElementById("privateBootstrapButton").addEventListener("click", () => {{
      postLocal("/api/private-bootstrap", "正在启动只读持仓读取...");
    }});
    document.getElementById("dailyReportButton").addEventListener("click", () => {{
      postLocal("/api/rerun-daily-report", "正在启动日报门禁重跑...");
    }});
    async function postRawRefresh() {{
      const msg = document.getElementById("rawMessage");
      if (!location.protocol.startsWith("http")) {{
        msg.textContent = webAppPromptText();
        return;
      }}
      msg.textContent = "正在检查 raw 合规状态...";
      try {{
        const payload = await postJson("/api/public-raw-refresh");
        if (!payload.ok) throw new Error(payload.error || "启动失败");
        msg.textContent = payload.message || "已返回 raw 合规状态。";
      }} catch (err) {{
        msg.textContent = "启动失败：" + err.message;
      }}
    }}
    document.getElementById("rawRefreshButton").addEventListener("click", postRawRefresh);
    async function postLiveDiscovery() {{
      const msg = document.getElementById("liveDiscoveryMessage");
      if (!location.protocol.startsWith("http")) {{
        msg.textContent = webAppPromptText();
        return;
      }}
      msg.textContent = "正在检查 Live 访问合规状态...";
      try {{
        const payload = await postJson("/api/live-board-discovery");
        if (!payload.ok) throw new Error(payload.error || "启动失败");
        msg.textContent = payload.message || "已返回 Live 访问合规状态。";
      }} catch (err) {{
        msg.textContent = "启动失败：" + err.message;
      }}
    }}
    const liveDiscoveryButton = document.getElementById("liveDiscoveryButton");
    if (liveDiscoveryButton) liveDiscoveryButton.addEventListener("click", postLiveDiscovery);
    async function postSourceMetadataRefresh() {{
      const msg = document.getElementById("sourceMetadataMessage");
      if (!msg) return;
      if (!location.protocol.startsWith("http")) {{
        msg.textContent = webAppPromptText();
        return;
      }}
      msg.textContent = "正在刷新开源模型证据...";
      try {{
        const payload = await postJson("/api/source-model-metadata-refresh");
        if (!payload.ok) throw new Error(payload.error || "启动失败");
        msg.textContent = payload.message || "已启动开源模型证据刷新。完成后刷新页面查看最新 GitHub 元数据。";
      }} catch (err) {{
        msg.textContent = "启动失败：" + err.message;
      }}
    }}
    const sourceMetadataButton = document.getElementById("sourceMetadataButton");
    if (sourceMetadataButton) sourceMetadataButton.addEventListener("click", postSourceMetadataRefresh);
    const runtimeStatusButton = document.getElementById("runtimeStatusButton");
    if (runtimeStatusButton) runtimeStatusButton.addEventListener("click", refreshRuntimeStatus);
    function setTeamTotalEntryMessage(text) {{
      const node = document.getElementById("teamTotalEntryMessage");
      if (node) node.textContent = text;
    }}
    function teamTotalObservedAtNow() {{
      const now = new Date();
      const parts = new Intl.DateTimeFormat("en-CA", {{
        timeZone: "Australia/Sydney",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZoneName: "short"
      }}).formatToParts(now).reduce((acc, part) => {{
        acc[part.type] = part.value;
        return acc;
      }}, {{}});
      const zone = parts.timeZoneName || "AEST";
      return `${{parts.year}}-${{parts.month}}-${{parts.day}} ${{parts.hour}}:${{parts.minute}} ${{zone}}`;
    }}
    function fillTeamTotalObservedAt() {{
      const value = teamTotalObservedAtNow();
      document.querySelectorAll('[data-team-total-entry] [data-field="observed_at_aest"]').forEach((input) => {{
        if (!input.value) input.value = value;
      }});
      setTeamTotalEntryMessage("已填入空白 observed_at_aest：" + value + "。保存前仍需逐场核对 TAB 盘口。");
    }}
    function teamTotalEntryPayload() {{
      const entries = Array.from(document.querySelectorAll("[data-team-total-entry]")).map((row) => {{
        const entry = {{ event_id: row.getAttribute("data-event-id") || "" }};
        row.querySelectorAll("[data-field]").forEach((input) => {{
          entry[input.getAttribute("data-field")] = input.value || "";
        }});
        return entry;
      }});
      return {{ entries }};
    }}
    async function saveTeamTotalEntry() {{
      const button = document.getElementById("teamTotalEntrySaveButton");
      const originalText = button ? button.textContent : "";
      if (!location.protocol.startsWith("http")) {{
        setTeamTotalEntryMessage(webAppPromptText());
        return;
      }}
      if (button) {{
        button.disabled = true;
        button.textContent = "保存中...";
      }}
      setTeamTotalEntryMessage("正在保存 Team Total 导入 CSV，并重建 Hash Gate / Overlay 预览...");
      try {{
        const payload = await postJsonBody("/api/manual-team-total-entry", teamTotalEntryPayload());
        if (!payload.ok) throw new Error(payload.error || "保存失败");
        setTeamTotalEntryMessage(
          "保存完成：" +
          payload.import_target_display +
          "；完整比赛 " + (payload.complete_event_count || 0) +
          "，跳过未完整 " + (payload.skipped_incomplete_event_count || 0) +
          "，invalid rows " + (payload.invalid_row_count || 0) +
          "；状态 " + (payload.manual_import_status || payload.status || "saved") +
          "。刷新页面查看最新质量 Gate。"
        );
        setTimeout(refreshRuntimeStatus, 500);
      }} catch (err) {{
        setTeamTotalEntryMessage("保存失败：" + err.message + "。确认本地网页主控台仍在运行。");
      }} finally {{
        if (button) {{
          button.disabled = false;
          button.textContent = originalText || "保存导入CSV";
        }}
      }}
    }}
    const teamTotalObservedNowButton = document.getElementById("teamTotalObservedNowButton");
    if (teamTotalObservedNowButton) teamTotalObservedNowButton.addEventListener("click", fillTeamTotalObservedAt);
    const teamTotalEntrySaveButton = document.getElementById("teamTotalEntrySaveButton");
    if (teamTotalEntrySaveButton) teamTotalEntrySaveButton.addEventListener("click", saveTeamTotalEntry);
    async function copyProviderCommand(button) {{
      const command = button.getAttribute("data-copy-command") || "";
      const targetId = button.getAttribute("data-copy-target") || "";
      const label = button.getAttribute("data-copy-label") || "内容";
      const target = targetId ? document.getElementById(targetId) : null;
      function fallbackCopyText(text) {{
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        const copied = document.execCommand("copy");
        document.body.removeChild(textarea);
        return copied;
      }}
      if (!command) {{
        if (target) target.textContent = "当前没有可复制" + label + "。";
        return;
      }}
      try {{
        let copied = false;
        if (navigator.clipboard && window.isSecureContext) {{
          try {{
            await navigator.clipboard.writeText(command);
            copied = true;
          }} catch (clipboardErr) {{
            copied = fallbackCopyText(command);
          }}
        }} else {{
          copied = fallbackCopyText(command);
        }}
        if (target) {{
          target.textContent = copied
            ? "已复制" + label + "。执行后刷新状态，并确认 formal publish=false、stake=AUD 0。"
            : "浏览器未授权自动复制；请手动复制" + label + "：" + command + "。执行后刷新状态，并确认 formal publish=false、stake=AUD 0。";
        }}
      }} catch (err) {{
        if (target) target.textContent = "复制失败，请手动复制" + label + "：" + err.message;
      }}
    }}
    document.querySelectorAll("[data-copy-command]").forEach((button) => {{
      button.addEventListener("click", () => copyProviderCommand(button));
    }});
    function initSectionNav() {{
      const links = Array.from(document.querySelectorAll("[data-nav-link]"));
      if (!links.length || !("IntersectionObserver" in window)) return;
      const byId = new Map();
      links.forEach((link) => {{
        const id = String(link.getAttribute("href") || "").slice(1);
        const target = document.getElementById(id);
        if (target) byId.set(id, link);
      }});
      const observer = new IntersectionObserver((entries) => {{
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (!visible || !visible.target || !visible.target.id) return;
        links.forEach((link) => link.classList.remove("active"));
        const active = byId.get(visible.target.id);
        if (active) active.classList.add("active");
      }}, {{ rootMargin: "-12% 0px -70% 0px", threshold: [0.1, 0.3, 0.6] }});
      byId.forEach((_, id) => {{
        const target = document.getElementById(id);
        if (target) observer.observe(target);
      }});
    }}
    initSectionNav();
    refreshRuntimeStatus();
  </script>
</body>
</html>
"""


def write_app_bundle() -> None:
    macos_dir = APP_BUNDLE / "Contents" / "MacOS"
    resources_dir = APP_BUNDLE / "Contents" / "Resources"
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    launcher = macos_dir / "TABFIFALauncher"
    launcher.write_text(
        f"""#!/bin/zsh
PIPELINE_ROOT="{PIPELINE_ROOT}"
PYTHON_BIN="{sys.executable}"
PORT="${{TAB_FIFA_APP_PORT:-{APP_PORT}}}"
LOG_DIR="$HOME/Downloads/FIFA Report/app_assets"
LOG_FILE="$LOG_DIR/app_server.log"
mkdir -p "$LOG_DIR"
if ! /usr/sbin/lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  cd "$PIPELINE_ROOT" || exit 2
  "$PYTHON_BIN" scripts/tab_fifa_app_server.py --port "$PORT" >>"$LOG_FILE" 2>&1 &
  sleep 1
fi
/usr/bin/open "http://127.0.0.1:$PORT/"
""",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    if APP_ICON_SOURCE.exists():
        shutil.copy2(APP_ICON_SOURCE, resources_dir / f"{APP_ICON_NAME}.icns")
    (APP_BUNDLE / "Contents" / "Info.plist").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>zh_CN</string>
  <key>CFBundleExecutable</key>
  <string>TABFIFALauncher</string>
  <key>CFBundleIdentifier</key>
  <string>local.tab-fifa-research.launcher</string>
  <key>CFBundleIconFile</key>
  <string>TABFIFAResearch</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>TAB FIFA盘口研究系统</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.1</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.15</string>
</dict>
</plist>
""",
        encoding="utf-8",
    )


def write_entry_html_artifacts() -> None:
    html_text = build_entry_html()
    ENTRY_HTML.write_text(html_text, encoding="utf-8")
    RUNTIME_ENTRY_HTML.write_text(html_text, encoding="utf-8")


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_default_backfill_status()
    if os.getenv("TAB_FIFA_FAST_ENTRY_REBUILD") == "1":
        write_entry_html_artifacts()
        copied = copy_public_assets()
        write_app_bundle()
        print(
            json.dumps(
                {
                    "entry_html": str(ENTRY_HTML),
                    "runtime_entry_html": str(RUNTIME_ENTRY_HTML),
                    "app_bundle": str(APP_BUNDLE),
                    "assets_dir": str(ASSETS_DIR),
                    "app_url": f"http://127.0.0.1:{APP_PORT}/",
                    "mode": "fast_entry_rebuild",
                    "copied_assets": copied,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    dashboard_sidecars = ensure_dashboard_sidecars()
    model_comparison = ensure_model_comparison()
    source_model_registry = ensure_source_model_registry()
    intelligence = ensure_report_intelligence()
    automation_doctor = ensure_automation_doctor()
    automation_maturity = ensure_automation_maturity()
    position_monitor = ensure_position_monitor()
    live_discovery = ensure_live_board_discovery()
    available_strategy = ensure_available_board_strategy()
    partial_daily_research = ensure_partial_daily_research()
    fixture_sanity = ensure_fixture_sanity()
    raw_recovery = ensure_raw_refresh_recovery()
    active_timeline_report = ensure_active_timeline_report()
    recommendation_operations = ensure_recommendation_operations()
    provider_config_doctor = ensure_provider_config_doctor()
    provider_kpi = ensure_provider_kpi()
    public_snapshot_import = ensure_public_snapshot_import()
    public_snapshot_raw_publish = load_json(OUTPUT_DIR / "public_snapshot_raw_publish_latest.json")
    provider_fallback_verification = ensure_provider_fallback_verification()
    provider_manual_verification = ensure_provider_manual_verification()
    provider_manual_overlay_publish = load_json(OUTPUT_DIR / "provider_manual_overlay_publish_latest.json")
    model_divergence_review = ensure_model_divergence_review()
    strategy_performance = ensure_strategy_performance()
    product_readiness = ensure_product_readiness()
    goal_traceability = ensure_goal_traceability()
    visual_inventory = ensure_report_visual_inventory()
    report_evolution = ensure_report_evolution()
    visual_inventory = ensure_report_visual_inventory()
    product_readiness = ensure_product_readiness()
    write_entry_html_artifacts()
    product_readiness = ensure_product_readiness()
    write_entry_html_artifacts()
    copied = copy_public_assets()
    write_app_bundle()
    summary = {
        "entry_html": str(ENTRY_HTML),
        "app_bundle": str(APP_BUNDLE),
        "assets_dir": str(ASSETS_DIR),
        "app_url": f"http://127.0.0.1:{APP_PORT}/",
        "dashboard_sidecars": dashboard_sidecars,
        "report_intelligence": (intelligence.get("artifacts") or {}).get("pdf", "report_intelligence_latest.pdf"),
        "automation_doctor": (automation_doctor.get("artifacts") or {}).get("pdf", "automation_doctor_latest.pdf"),
        "automation_maturity": (automation_maturity.get("artifacts") or {}).get("pdf", "automation_maturity_latest.pdf"),
        "provider_config_doctor": (provider_config_doctor.get("artifacts") or {}).get("pdf", "provider_config_doctor_latest.pdf"),
        "provider_kpi": (provider_kpi.get("artifacts") or {}).get("pdf", "provider_kpi_latest.pdf"),
        "public_snapshot_import": (public_snapshot_import.get("artifacts") or {}).get("pdf", "public_snapshot_import_status_latest.pdf"),
        "public_snapshot_publish_preflight": (public_snapshot_import.get("artifacts") or {}).get(
            "publish_preflight_pdf", "public_snapshot_import_publish_preflight_latest.pdf"
        ),
        "public_snapshot_raw_publish": (public_snapshot_raw_publish.get("artifacts") or {}).get(
            "pdf", "public_snapshot_raw_publish_latest.pdf"
        ),
        "provider_fallback_verification": (provider_fallback_verification.get("artifacts") or {}).get("pdf", "provider_fallback_verification_latest.pdf"),
        "provider_manual_verification": (provider_manual_verification.get("artifacts") or {}).get("pdf", "provider_manual_verification_status_latest.pdf"),
        "provider_manual_hash_gate": (provider_manual_verification.get("artifacts") or {}).get("hash_gate_pdf", "provider_manual_hash_gate_latest.pdf"),
        "provider_manual_overlay_preview": (provider_manual_verification.get("artifacts") or {}).get(
            "overlay_preview_pdf", "provider_manual_overlay_preview_latest.pdf"
        ),
        "provider_manual_overlay_publish_preflight": (provider_manual_verification.get("artifacts") or {}).get(
            "overlay_publish_preflight_pdf", "provider_manual_overlay_publish_preflight_latest.pdf"
        ),
        "provider_manual_overlay_publish": (provider_manual_overlay_publish.get("artifacts") or {}).get(
            "pdf", "provider_manual_overlay_publish_latest.pdf"
        ),
        "provider_manual_workbench": (provider_manual_verification.get("artifacts") or {}).get(
            "manual_workbench_pdf", "provider_manual_workbench_latest.pdf"
        ),
        "recommendation_operations": (recommendation_operations.get("artifacts") or {}).get("pdf", "recommendation_operations_latest.pdf"),
        "model_divergence_review": (model_divergence_review.get("artifacts") or {}).get("pdf", "model_divergence_review_latest.pdf"),
        "strategy_performance": (strategy_performance.get("artifacts") or {}).get("pdf", "strategy_performance_latest.pdf"),
        "report_evolution": (report_evolution.get("artifacts") or {}).get("pdf", "report_evolution_latest.pdf"),
        "product_readiness": (product_readiness.get("artifacts") or {}).get("pdf", "product_readiness_dashboard_latest.pdf"),
        "goal_traceability": (goal_traceability.get("artifacts") or {}).get("pdf", "goal_traceability_latest.pdf"),
        "position_monitor": (position_monitor.get("artifacts") or {}).get("pdf", "position_monitor_latest.pdf"),
        "model_comparison": (model_comparison.get("pdf_artifact") or "tab_fifa_model_comparison_v0_1.pdf"),
        "source_model_registry": (source_model_registry.get("artifacts") or {}).get("pdf", "source_model_registry_latest.pdf"),
        "live_board_discovery": (live_discovery.get("artifacts") or {}).get("pdf", "live_board_discovery_latest.pdf"),
        "available_board_strategy": (available_strategy.get("artifacts") or {}).get("pdf", "available_board_strategy_latest.pdf"),
        "partial_daily_research": (partial_daily_research.get("artifacts") or {}).get("pdf", "partial_daily_research_latest.pdf"),
        "fixture_sanity": (fixture_sanity.get("artifacts") or {}).get("pdf", "fixture_sanity_latest.pdf"),
        "raw_refresh_recovery": (raw_recovery.get("artifacts") or {}).get("pdf", "raw_refresh_recovery_latest.pdf"),
        "active_timeline_report": (active_timeline_report.get("artifacts") or {}).get("pdf", "active_timeline_report_latest.pdf"),
        "report_visual_inventory": (visual_inventory.get("artifacts") or {}).get("pdf", "report_visual_inventory_latest.pdf"),
        "copied_assets": copied,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
