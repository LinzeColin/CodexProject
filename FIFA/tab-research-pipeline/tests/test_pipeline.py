import csv
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import importlib.util
import argparse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tab_research.parser import invalid_market_price_rows, parse_market_pairs
from tab_research.pipeline import EXPECTED_MATCHES, automation_gate, expected_match_names, generate_candidates, has_full_core_markets, match_is_in_play, quality_audit, render_markdown as render_matches_markdown, write_outputs
from tab_research.australia_markets import EXPECTED_MARKETS as AUSTRALIA_EXPECTED_MARKETS
from tab_research.australia_markets import MARKET_ID_TO_NAME as AUSTRALIA_MARKET_ID_TO_NAME
from tab_research.australia_markets import australia_gate, parse_australia_raw, parse_price_rows, render_australia_markdown
from tab_research.automation_config import automation_authorization_from_mapping, load_automation_authorization
from tab_research.automation_candidate import (
    AUTOMATION_CANDIDATE_LATEST,
    AUTOMATION_CANDIDATE_PDF_LATEST,
    AUTOMATION_CANDIDATE_REPORT_LATEST,
    build_automation_candidate,
    write_automation_candidate,
    write_automation_candidate_pdf,
    write_automation_candidate_report,
)
from tab_research.automation_doctor import (
    AUTOMATION_DOCTOR_JSON_LATEST,
    AUTOMATION_DOCTOR_MD_LATEST,
    AUTOMATION_DOCTOR_PDF_LATEST,
    write_automation_doctor_bundle,
)
from tab_research.automation_maturity import (
    AUTOMATION_MATURITY_JSON_LATEST,
    AUTOMATION_MATURITY_MD_LATEST,
    AUTOMATION_MATURITY_PDF_LATEST,
    write_automation_maturity_bundle,
)
from tab_research.goal_traceability import (
    GOAL_TRACEABILITY_JSON_LATEST,
    GOAL_TRACEABILITY_MD_LATEST,
    GOAL_TRACEABILITY_PDF_LATEST,
    downloads_entry_trace,
    source_file_trace,
    write_goal_traceability_bundle,
)
from tab_research.fixture_sanity import (
    FIXTURE_SANITY_JSON_LATEST,
    FIXTURE_SANITY_MD_LATEST,
    FIXTURE_SANITY_PDF_LATEST,
    write_fixture_sanity_bundle,
)
from tab_research.position_monitor import (
    POSITION_MONITOR_JSON_LATEST,
    POSITION_MONITOR_MD_LATEST,
    POSITION_MONITOR_PDF_LATEST,
    position_report_date,
    recommended_next_action as position_recommended_next_action,
    write_position_monitor_bundle,
)
from tab_research.product_readiness import (
    PRODUCT_READINESS_JSON_LATEST,
    PRODUCT_READINESS_MD_LATEST,
    PRODUCT_READINESS_PDF_LATEST,
    write_product_readiness_bundle,
)
from tab_research.active_timeline_report import (
    ACTIVE_TIMELINE_REPORT_JSON_LATEST,
    ACTIVE_TIMELINE_REPORT_MD_LATEST,
    ACTIVE_TIMELINE_REPORT_PDF_LATEST,
    write_active_timeline_report_bundle,
)
from tab_research.available_board_strategy import (
    AVAILABLE_BOARD_STRATEGY_JSON_LATEST,
    AVAILABLE_BOARD_STRATEGY_MD_LATEST,
    AVAILABLE_BOARD_STRATEGY_PDF_LATEST,
    write_available_board_strategy_bundle,
)
from tab_research.partial_daily_research import (
    PARTIAL_DAILY_RESEARCH_JSON_LATEST,
    PARTIAL_DAILY_RESEARCH_MD_LATEST,
    PARTIAL_DAILY_RESEARCH_PDF_LATEST,
    RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST,
    write_partial_daily_research_bundle,
)
from tab_research.live_board_discovery import (
    LIVE_BOARD_DISCOVERY_JSON_LATEST,
    LIVE_BOARD_DISCOVERY_MD_LATEST,
    LIVE_BOARD_DISCOVERY_PDF_LATEST,
    LIVE_BOARD_DISCOVERY_RAW_LATEST,
    write_live_board_discovery_bundle,
)
import tab_research.automation_readiness as automation_readiness_module
from tab_research.automation_readiness import write_automation_readiness_pdf, write_automation_readiness_report, write_automation_readiness_summary
from tab_research.compare import compact_portfolio_baseline, compare_portfolio_recommendations, compare_recommendations
from tab_research.boards import BoardConfig, audit_portfolio, board_by_id, board_registry, refresh_driver, render_portfolio_markdown
from tab_research.bankroll import allocate_time_adjusted_stakes, build_bankroll_plan
from tab_research.daily_boards import current_matches_board, missing_runner_board_ids, response_metrics
from tab_research.dashboard import (
    DASHBOARD_MD_LATEST,
    DASHBOARD_PDF_LATEST,
    publish_dashboard_latest,
    write_dashboard,
    write_dashboard_sidecar_bundle,
)
from tab_research.evidence import build_missing_data_logs
from tab_research.event_monitor import audit_event_feeds, event_risk_for_match, parse_google_news_rss
from tab_research.futures import CORE_MARKETS as FUTURES_CORE_MARKETS
from tab_research.futures import EXPECTED_TEAMS as FUTURES_EXPECTED_TEAMS
from tab_research.futures import (
    futures_gate,
    generate_futures_report,
    no_vig_market_probabilities,
    parse_core_futures,
    parse_current_detail_markets,
    render_futures_markdown,
)
from tab_research.group_betting import group_gate, parse_group_winners, render_group_markdown
from tab_research.io import atomic_write_json, atomic_write_text, single_instance_lock
from tab_research.latest_commit import latest_commit_artifact_consistency_issues
from tab_research.model import implied_probability, novig_probabilities
from tab_research.model_compare import (
    MODEL_COMPARISON_JSON,
    MODEL_COMPARISON_MD,
    MODEL_COMPARISON_PDF,
    compare_match_models,
    generate_model_comparison,
    render_model_comparison_markdown,
    write_model_comparison,
    write_model_comparison_pdf,
)
from tab_research.model_divergence_review import (
    MODEL_DIVERGENCE_REVIEW_JSON_LATEST,
    MODEL_DIVERGENCE_REVIEW_MD_LATEST,
    MODEL_DIVERGENCE_REVIEW_PDF_LATEST,
    write_model_divergence_review_bundle,
)
from tab_research.my_bets_bootstrap import build_private_position_bootstrap_status
from tab_research.my_bets import assert_private_snapshot_dir, build_snapshot, parse_my_bets_text, validate_snapshot, write_private_snapshot
from tab_research.odds import parse_decimal_odds, valid_decimal_odds
from tab_research.paths import resolve_output_dir, resolve_workspace_root
from tab_research.pdf_qa import DEFAULT_REQUIRED_TERMS, audit_pdf_report
from tab_research.preflight import audit_automation_preflight, scan_risky_autobet_code
from tab_research.public_sources import PublicSource, audit_sources
from tab_research.raw_refresh import audit_raw_refresh, audit_staged_raw_refresh, normalize_partial_research_refresh, raw_refresh_health, validate_raw_snapshot, write_raw_refresh_batch_manifest
import tab_research.odds_provider_adapter as odds_provider_adapter_module
from tab_research.odds_provider_adapter import (
    ODDS_PROVIDER_BLOCKED_LATEST,
    ODDS_PROVIDER_COVERAGE_LATEST,
    adapt_provider_payloads,
    build_provider_coverage,
    build_the_odds_api_event_markets_requests,
    build_the_odds_api_event_odds_requests,
    build_the_odds_api_requests,
    default_the_odds_api_sports,
    event_market_probe_plan,
    fetch_provider_requests,
    fetch_the_odds_api_sports,
    historical_market_covered_event_ids,
    merge_historical_provider_raws,
    normalize_the_odds_api_sports_config,
    provider_event_descriptors,
    resolve_target_board_ids,
    resolve_the_odds_api_sports_from_catalog,
    publish_verified_provider_raw,
    validate_provider_analysis_snapshot,
    write_provider_staging_bundle,
)
from refresh_odds_provider_raw import (
    historical_merge_market_keys,
    load_local_env_files,
    select_event_descriptors_for_event_level_probe,
    should_load_env_value,
    write_blocked_provider_payload,
)
from tab_research.provider_alternate_plan import (
    PROVIDER_ALTERNATE_EVIDENCE_JSON_LATEST,
    PROVIDER_ALTERNATE_PLAN_JSON_LATEST,
    build_provider_alternate_plan,
    write_provider_alternate_plan_bundle,
)
from tab_research.provider_fallback_verification import (
    PROVIDER_FALLBACK_VERIFICATION_JSON_LATEST,
    write_provider_fallback_verification_bundle,
)
from tab_research.provider_config_doctor import (
    PROVIDER_CONFIG_DOCTOR_JSON_LATEST,
    PROVIDER_CONFIG_DOCTOR_MD_LATEST,
    PROVIDER_CONFIG_DOCTOR_PDF_LATEST,
    build_provider_config_doctor,
    write_provider_config_doctor_bundle,
)
from tab_research.provider_kpi import build_provider_kpi, write_provider_kpi_bundle
from tab_research.provider_manual_verification import (
    CSV_FIELDS,
    DEFAULT_IMPORT_RELATIVE_PATH,
    DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH,
    PROVIDER_MANUAL_HASH_GATE_JSON_LATEST,
    PROVIDER_MANUAL_OVERLAY_APPROVAL_TEMPLATE_JSON_LATEST,
    PROVIDER_MANUAL_OVERLAY_PREVIEW_JSON_LATEST,
    PROVIDER_MANUAL_OVERLAY_PUBLISH_JSON_LATEST,
    PROVIDER_MANUAL_OVERLAY_PUBLISH_MD_LATEST,
    PROVIDER_MANUAL_OVERLAY_PUBLISH_PDF_LATEST,
    PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_JSON_LATEST,
    PROVIDER_MANUAL_OVERLAY_RAW_LATEST,
    PROVIDER_MANUAL_PAIR_TEMPLATE_CSV_LATEST,
    PROVIDER_MANUAL_WORKBENCH_JSON_LATEST,
    PROVIDER_MANUAL_WORKBENCH_MD_LATEST,
    PROVIDER_MANUAL_WORKBENCH_PDF_LATEST,
    PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST,
    PROVIDER_MANUAL_VERIFICATION_STATUS_JSON_LATEST,
    PROVIDER_MANUAL_VERIFICATION_TEMPLATE_CSV_LATEST,
    publish_provider_manual_overlay,
    write_provider_manual_verification_bundle,
)
from tab_research.public_snapshot_importer import (
    DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH,
    PUBLIC_SNAPSHOT_APPROVAL_TEMPLATE_JSON_LATEST,
    PUBLIC_SNAPSHOT_IMPORT_DIR,
    PUBLIC_SNAPSHOT_IMPORT_PREVIEW_RAW_LATEST,
    PUBLIC_SNAPSHOT_IMPORT_STATUS_JSON_LATEST,
    PUBLIC_SNAPSHOT_IMPORT_TEMPLATE_JSON_LATEST,
    PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST,
    PUBLIC_SNAPSHOT_RAW_PUBLISH_JSON_LATEST,
    PUBLIC_SNAPSHOT_RAW_PUBLISH_MD_LATEST,
    PUBLIC_SNAPSHOT_RAW_PUBLISH_PDF_LATEST,
    publish_public_snapshot_raw,
    write_public_snapshot_import_bundle,
)
from tab_research.raw_refresh_recovery import (
    RAW_REFRESH_RECOVERY_JSON_LATEST,
    RAW_REFRESH_RECOVERY_MD_LATEST,
    RAW_REFRESH_RECOVERY_PDF_LATEST,
    write_raw_refresh_recovery_bundle,
)
from tab_research.report_store import (
    connect_report_db,
    latest_automation_runs,
    latest_runs,
    store_automation_run,
    store_daily_run,
    update_run_dashboard_paths,
    write_report_index,
    write_report_index_pdf,
    write_report_index_report,
)
from tab_research.report_intelligence import (
    REPORT_INTELLIGENCE_JSON_LATEST,
    REPORT_INTELLIGENCE_MD_LATEST,
    REPORT_INTELLIGENCE_PDF_LATEST,
    write_report_intelligence_bundle,
)
from tab_research.report_evolution import (
    REPORT_EVOLUTION_JSON_LATEST,
    REPORT_EVOLUTION_MD_LATEST,
    REPORT_EVOLUTION_PDF_LATEST,
    write_report_evolution_bundle,
)
from tab_research.report_visual_inventory import (
    REPORT_VISUAL_INVENTORY_JSON_LATEST,
    REPORT_VISUAL_INVENTORY_MD_LATEST,
    REPORT_VISUAL_INVENTORY_PDF_LATEST,
    write_report_visual_inventory_bundle,
)
from tab_research.recommendation_operations import (
    RECOMMENDATION_OPERATIONS_JSON_LATEST,
    RECOMMENDATION_OPERATIONS_MD_LATEST,
    RECOMMENDATION_OPERATIONS_PDF_LATEST,
    apply_execution_gate as apply_recommendation_execution_gate,
    model_calibration_for_recommendation,
    write_recommendation_operations_bundle,
)
from tab_research.strategy_performance import (
    STRATEGY_PERFORMANCE_JSON_LATEST,
    STRATEGY_PERFORMANCE_MD_LATEST,
    STRATEGY_PERFORMANCE_PDF_LATEST,
    write_strategy_performance_bundle,
)
from tab_research.recommendations import enrich_match_recommendations_with_model_comparison
from tab_research.safety import audit_output_safety, audit_public_artifact_safety, audit_safety, redact_sensitive_text
from tab_research.source_model_registry import (
    SOURCE_MODEL_REGISTRY_JSON_LATEST,
    SOURCE_MODEL_REGISTRY_MD_LATEST,
    SOURCE_MODEL_REGISTRY_PDF_LATEST,
    write_source_model_registry_bundle,
)
from tab_research.source_model_metadata import SOURCE_MODEL_GITHUB_METADATA_JSON_LATEST
from tab_research.team_futures_multi import EXPECTED_CODES as TEAM_MULTI_EXPECTED_CODES
from tab_research.team_futures_multi import MARKETS as TEAM_MULTI_MARKETS
from tab_research.team_futures_multi import no_vig_market_probabilities as team_multi_no_vig
from tab_research.team_futures_multi import parse_team_futures_multi, team_multi_gate, render_team_multi_markdown
from generate_business_pdf_report import assert_pdf_input_gates, odds_or_pending, public_bankroll_summary, resolve_portfolio_compare
from run_daily_report import (
    latest_commit_payload,
    looks_like_access_denied,
    matches_chunk_quality_errors,
    matches_refresh_chunk_size,
    public_refresh_summary,
    public_tail,
    preflight_run_path,
    publish_convenience_latest_artifacts,
    publish_latest_baseline,
    publish_latest_commit,
    refresh_process_timeout_seconds,
    select_previous_baseline_path,
    select_previous_portfolio_baseline_path,
    should_try_headed_refresh_fallback,
)


def full_matches_raw_fixture():
    return {
        "generated_at": "2026-06-03T00:00:00Z",
        "source": "unit_fixture",
        "matches": [full_match_fixture(match) for match in EXPECTED_MATCHES],
    }


def full_provider_matches_raw_fixture():
    raw = full_matches_raw_fixture()
    raw["refresh_id"] = "provider-full-fixture"
    raw["source_mode"] = "provider_staged_fixture"
    for index, match in enumerate(raw["matches"], start=1):
        match["provider_event_id"] = f"event-{index}"
        match["commence_time"] = "2026-06-12T05:00:00Z"
    return raw


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def full_match_fixture(match_name):
    home, away = match_name.split(" v ", 1)
    return {
        "match": match_name,
        "markets": {
            "Result": f"Result\n{home}\n2.00\nDraw\n3.20\n{away}\n3.80\n",
            "Double Chance": f"Double Chance\n{home} or Draw\n1.25\n{away} or Draw\n1.75\n{home} or {away}\n1.33\n",
            "Handicap": f"Handicap\n{home} -1.5\n4.00\n{away} +1.5\n1.25\n",
            "Total Goals Over/Under": "Total Goals Over/Under\nOver 2.5 Goals\n2.05\nUnder 2.5 Goals\n1.85\n",
            "Both Teams to Score": "Both Teams to Score\nBoth Teams to Score\n1.90\nOnly One or Neither to score\n1.90\n",
            "Draw No Bet": f"Draw No Bet\n{home}\n1.55\n{away}\n2.30\n",
        },
        "errors": [],
        "partial_core_only": False,
    }


def the_odds_api_tab_event_fixture(match_name="Mexico v South Africa"):
    home, away = match_name.split(" v ", 1)
    return {
        "id": f"fixture-{home.lower()}-{away.lower()}".replace(" ", "-"),
        "sport_key": "soccer_fifa_world_cup",
        "commence_time": "2026-06-12T05:00:00Z",
        "home_team": home,
        "away_team": away,
        "bookmakers": [
            {
                "key": "tab",
                "title": "TAB",
                "last_update": "2026-06-13T00:00:00Z",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": home, "price": 2.00, "home": True},
                            {"name": "Draw", "price": 3.20},
                            {"name": away, "price": 3.80, "away": True},
                        ],
                    },
                    {
                        "key": "spreads",
                        "outcomes": [
                            {"name": home, "price": 4.00, "point": -1.5},
                            {"name": away, "price": 1.25, "point": 1.5},
                        ],
                    },
                    {
                        "key": "totals",
                        "outcomes": [
                            {"name": "Over", "price": 2.05, "point": 2.5},
                            {"name": "Under", "price": 1.85, "point": 2.5},
                        ],
                    },
                    {
                        "key": "team_totals",
                        "outcomes": [
                            {"name": "Over", "description": home, "price": 2.30, "point": 1.5},
                            {"name": "Under", "description": home, "price": 1.60, "point": 1.5},
                            {"name": "Over", "description": away, "price": 2.80, "point": 0.5},
                            {"name": "Under", "description": away, "price": 1.42, "point": 0.5},
                        ],
                    },
                    {
                        "key": "btts",
                        "outcomes": [
                            {"name": "Both Teams to Score", "price": 1.90},
                            {"name": "Only One or Neither to score", "price": 1.90},
                        ],
                    },
                    {
                        "key": "double_chance",
                        "outcomes": [
                            {"name": f"{home} or Draw", "price": 1.25},
                            {"name": f"{away} or Draw", "price": 1.75},
                            {"name": f"{home} or {away}", "price": 1.33},
                        ],
                    },
                    {
                        "key": "draw_no_bet",
                        "outcomes": [
                            {"name": home, "price": 1.55},
                            {"name": away, "price": 2.30},
                        ],
                    },
                ],
            }
        ],
    }


def the_odds_api_payload_fixture():
    return {
        "provider": "the_odds_api",
        "fetched_at": "2026-06-13T00:00:00Z",
        "request_url": "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/?apiKey=REDACTED&bookmakers=tab",
        "sport_key": "soccer_fifa_world_cup",
        "market_keys": ["h2h", "totals", "spreads"],
        "request_kind": "odds",
        "ok": True,
        "payload": [the_odds_api_tab_event_fixture(match) for match in EXPECTED_MATCHES],
    }


def the_odds_api_event_markets_payload_fixture():
    event = the_odds_api_tab_event_fixture()
    return {
        "provider": "the_odds_api",
        "fetched_at": "2026-06-13T00:03:00Z",
        "request_url": f"https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/events/{event['id']}/markets?apiKey=REDACTED&bookmakers=tab",
        "sport_key": "soccer_fifa_world_cup",
        "market_keys": [],
        "board_scope": "matches",
        "estimated_credit_cost": 1,
        "request_kind": "event_markets",
        "event_id": event["id"],
        "ok": True,
        "usage": {"requests_remaining": 493, "requests_used": 7, "requests_last": 1},
        "payload": {
            "id": event["id"],
            "sport_key": "soccer_fifa_world_cup",
            "commence_time": event["commence_time"],
            "home_team": event["home_team"],
            "away_team": event["away_team"],
            "bookmakers": [
                {
                    "key": "tab",
                    "title": "TAB",
                    "markets": [
                        {"key": "h2h"},
                        {"key": "spreads"},
                        {"key": "alternate_totals"},
                        {"key": "team_totals"},
                    ],
                }
            ],
        },
    }


def the_odds_api_event_odds_payload_fixture():
    event = the_odds_api_tab_event_fixture()
    return {
        "provider": "the_odds_api",
        "fetched_at": "2026-06-13T00:04:00Z",
        "request_url": f"https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/events/{event['id']}/odds?apiKey=REDACTED&bookmakers=tab",
        "sport_key": "soccer_fifa_world_cup",
        "market_keys": ["alternate_totals", "team_totals"],
        "board_scope": "matches",
        "estimated_credit_cost": 2,
        "request_kind": "event_odds",
        "event_id": event["id"],
        "ok": True,
        "usage": {"requests_remaining": 491, "requests_used": 9, "requests_last": 2},
        "payload": {
            "id": event["id"],
            "sport_key": "soccer_fifa_world_cup",
            "commence_time": event["commence_time"],
            "home_team": event["home_team"],
            "away_team": event["away_team"],
            "bookmakers": [
                {
                    "key": "tab",
                    "title": "TAB",
                    "markets": [
                        {
                            "key": "alternate_totals",
                            "outcomes": [
                                {"name": "Over", "price": 2.10, "point": 2.5},
                                {"name": "Under", "price": 1.78, "point": 2.5},
                            ],
                        },
                        {
                            "key": "team_totals",
                            "outcomes": [
                                {"name": "Over", "description": event["home_team"], "price": 2.30, "point": 1.5},
                                {"name": "Under", "description": event["home_team"], "price": 1.60, "point": 1.5},
                            ],
                        },
                    ],
                }
            ],
        },
    }


def sample_openfootball_2026_payload():
    return {
        "name": "World Cup 2026",
        "matches": [
            {
                "round": "Matchday 1",
                "date": "2026-06-11",
                "time": "13:00",
                "team1": "Mexico",
                "team2": "South Africa",
                "group": "Group A",
                "ground": "Estadio Azteca",
                "score": {"ft": [2, 0]},
            },
            {
                "round": "Matchday 1",
                "date": "2026-06-11",
                "time": "20:00",
                "team1": "South Korea",
                "team2": "Czech Republic",
                "group": "Group A",
                "ground": "Estadio Akron",
                "score": {"ft": [2, 1]},
            },
            {
                "round": "Matchday 1",
                "date": "2026-06-12",
                "time": "18:00",
                "team1": "United States",
                "team2": "Paraguay",
                "group": "Group D",
                "ground": "SoFi Stadium",
            },
        ],
    }


def partial_matches_raw_fixture():
    raw = full_matches_raw_fixture()
    raw["matches"] = [match for match in raw["matches"] if match["match"] != "Ghana v Panama"]
    raw["matches"][0]["errors"] = ["Market header expansion failed for Handicap"]
    portugal = next(match for match in raw["matches"] if match["match"] == "Portugal v DR Congo")
    portugal["markets"] = {"Result": portugal["markets"]["Result"]}
    portugal["partial_core_only"] = True
    return raw


def sample_my_bets_text():
    return """My Bets
Bets
Pending
Won
Mon 01 Jun - 21:41:10
FO
Win
Pending
Spain
WC Spai-CabV Result
Stake
$100.00
Odds
1.08
Estimated Return
$108.00
Mon 01 Jun - 21:38:46
FO
Win
Won
Germany
WC Gmny-Crco Result
Stake
$500.00
Odds
1.03
Estimated Return
$515.00
Language:
English
"""


def group_betting_text_fixture():
    groups = []
    for index, group in enumerate("ABCDEFGHIJKL"):
        teams = [f"Team {group}{slot}" for slot in range(1, 5)]
        if group == "F":
            teams = ["Netherlands", "Japan", "Tunisia", "Sweden"]
        groups.extend(
            [
                f"World Cup Group {group} ({', '.join(teams)})",
                "1 Market",
                f"WC26 Group {group} Winner",
            ]
        )
        for slot, team in enumerate(teams):
            groups.extend([team, f"{2.0 + index * 0.1 + slot * 0.2:.2f}"])
    return "\n".join(groups)


def collapsed_futures_winner_text_fixture():
    return "\n".join(
        [
            "Home",
            "Soccer",
            "2026 World Cup Futures",
            "2026 World Cup Futures - Betting Odds",
            "2026 World Cup",
            "102 Markets",
            "2026 World Cup WinnerMon 20 Jul 5:00Bet live",
            "Australia",
            "401.00",
            "Spain",
            "5.50",
            "France",
            "5.50",
            "Portugal",
            "8.50",
            "England",
            "9.00",
            "Brazil",
            "10.00",
            "Argentina",
            "11.00",
            "Germany",
            "15.00",
            "Netherlands",
            "17.00",
            "Norway",
            "34.00",
            "Belgium",
            "41.00",
            "Colombia",
            "41.00",
            "Japan",
            "41.00",
            "Morocco",
            "51.00",
            "Mexico",
            "51.00",
            "USA",
            "67.00",
            "Switzerland",
            "67.00",
            "Show All Selections",
            "Top Goal Scorer",
            "Reach Round of 16",
            "Language:",
        ]
    )


def detail_futures_winner_text_fixture():
    teams = [
        "Australia", "Spain", "France", "Portugal", "England", "Brazil", "Argentina", "Germany",
        "Netherlands", "Norway", "Belgium", "Colombia", "Japan", "Morocco", "Mexico", "USA",
        "Switzerland", "Ecuador", "Turkiye", "Uruguay", "Croatia", "Senegal", "Austria", "Sweden",
        "Cote d Ivoire", "Canada", "Korea Republic", "Paraguay", "Scotland", "Egypt", "Algeria",
        "Bosnia Herzegovina", "Czechia", "Ghana", "Congo DR", "Iran", "Iraq", "Tunisia",
        "New Zealand", "Panama", "Qatar", "Saudi Arabia", "South Africa", "Cabo Verde",
        "Uzbekistan", "Jordan", "Curacao", "Haiti",
    ]
    lines = [
        "Home",
        "Soccer",
        "2026 World Cup Futures",
        "2026 World Cup",
        "Winner",
        "|2026 World Cup Winner|Mon 20 Jul 05:00|Bet live",
    ]
    for index, team in enumerate(teams):
        price = f"{2.0 + index:.2f}"
        lines.extend([team, price, price])
    lines.extend(["Stage of Elimination", "Team Tournament Goals O/U", "Language:"])
    return "\n".join(lines)


def current_futures_detail_text_fixture():
    teams = list(FUTURES_EXPECTED_TEAMS)
    outcomes = [
        "Group Stage",
        "Round of 32",
        "Last 16",
        "Quarter Finals",
        "Semi Finals",
        "Runner Up",
        "Winner",
    ]
    players = [
        "Kylian Mbappe",
        "Erling Haaland",
        "Harry Kane",
        "Vinicius Junior",
        "Lionel Messi",
        "Cristiano Ronaldo",
        "Lamine Yamal",
        "Jamal Musiala",
        "Julian Alvarez",
        "Darwin Nunez",
        "Raphinha",
        "Memphis Depay",
        "Lautaro Martinez",
        "Bukayo Saka",
        "Khvicha Kvaratskhelia",
        "Mohamed Salah",
        "Son Heung-min",
    ]
    lines = [
        "Home",
        "Soccer",
        "2026 World Cup Futures",
        "2026 World Cup",
        "Winner",
        "|2026 World Cup Winner|Mon 20 Jul 05:00|Bet live",
    ]
    for index, team in enumerate(teams):
        price = f"{2.0 + index:.2f}"
        lines.extend([team, price, price])
    lines.append("Stage of Elimination")
    for team_index, team in enumerate(teams[12:]):
        lines.append(f"|{team} Stage of Elimination|Mon 20 Jul 05:00|Bet live")
        for outcome_index, outcome in enumerate(outcomes):
            price = f"{1.20 + team_index * 0.05 + outcome_index * 0.20:.2f}"
            lines.extend([f"{team} {outcome}", price, price])
    lines.append("Team Tournament Goals O/U")
    for team_index, team in enumerate(teams[8:]):
        line = 2.5 + (team_index % 5)
        over_price = f"{1.70 + (team_index % 6) * 0.04:.2f}"
        under_price = f"{1.80 + (team_index % 5) * 0.05:.2f}"
        lines.extend(
            [
                f"|{team} Total Goals|Mon 20 Jul 05:00|Bet live",
                f"{team} Over {line:.1f} Goals",
                over_price,
                over_price,
                f"{team} Under {line:.1f} Goals",
                under_price,
                under_price,
            ]
        )
    lines.append("Player Tournament Goals OU")
    for player_index, player in enumerate(players):
        line = 1.5 + (player_index % 4)
        over_price = f"{1.90 + (player_index % 5) * 0.05:.2f}"
        under_price = f"{1.75 + (player_index % 4) * 0.06:.2f}"
        lines.extend(
            [
                f"|{player} Goals O/U|Mon 20 Jul 05:00|Bet live",
                f"{player} Over {line:.1f} Goals",
                over_price,
                over_price,
                f"{player} Under {line:.1f} Goals",
                under_price,
                under_price,
            ]
        )
    lines.extend(["Language:", "English"])
    return "\n".join(lines)


def australia_raw_fixture():
    markets = []
    for market_id, market_name in AUSTRALIA_MARKET_ID_TO_NAME.items():
        if market_name == "Top Australian Goalscorer":
            lines = [market_name]
            for index in range(18):
                lines.extend([f"Player {index + 1}", f"{4.0 + index * 0.5:.2f}"])
        else:
            lines = [market_name, "Option A", "2.00", "Option B", "2.20", "Option C", "3.40", "Option D", "4.60"]
        markets.append({"id": market_id, "afterText": "\n".join(lines)})
    return {"markets": markets}


def australia_gate_markets_fixture():
    markets = []
    for market in AUSTRALIA_EXPECTED_MARKETS:
        if "O/U" in market:
            rows = [
                {"selection": f"{market} Over 2.5", "odds": 1.90},
                {"selection": f"{market} Under 2.5", "odds": 1.90},
            ]
        elif market == "Top Australian Goalscorer":
            rows = [
                {"selection": "Nestory Irankunda", "odds": 7.00},
                {"selection": "No Australian Goalscorer", "odds": 8.00},
            ]
        else:
            rows = [
                {"selection": f"{market} Option A", "odds": 2.00},
                {"selection": f"{market} Option B", "odds": 2.20},
            ]
        markets.append({"market": market, "status": "priced", "rows": rows})
    return markets


def team_futures_multi_text_fixture():
    codes = ["ARG", "AUS", "BEL", "BRA", "CRO", "ENG", "ESP", "FRA", "GER", "JPN", "NED", "NOR", "POR", "USA"]
    lines = []
    for index, code in enumerate(codes):
        quarter_final = "3.75" if code == "JPN" else f"{2.20 + index * 0.15:.2f}"
        lines.extend(
            [
                f"2026 SWC Futures Multi {code}",
                "1 Market",
                f"2026 SWC Futures Multi {code}",
                f"{code} Win World Cup",
                f"{9.0 + index:.2f}",
                f"{code} Reach Final",
                f"{5.0 + index * 0.4:.2f}",
                f"{code} Reach Semi Final",
                f"{3.0 + index * 0.25:.2f}",
                f"{code} Reach Quarter Final",
                quarter_final,
            ]
        )
    return "\n".join(lines)


def ready_pdf_gate():
    return {"automation_ready": True, "blocking_reasons": []}


def pdf_matches_artifact():
    gate = ready_pdf_gate()
    gate["coverage"] = {
        "detail_main_markets": {"covered": len(EXPECTED_MATCHES), "total": len(EXPECTED_MATCHES)},
        "full_main_markets": {"covered": len(EXPECTED_MATCHES), "total": len(EXPECTED_MATCHES)},
    }
    recommendations = [
        ("Netherlands v Japan", "Result", "Japan", 3.70, 0.32, 0.184, 40),
        ("Brazil v Morocco", "Result", "Morocco", 6.00, 0.20, 0.200, 45),
        ("France v Senegal", "Result", "Senegal", 7.50, 0.16, 0.200, 35),
        ("England v Croatia", "Result", "Croatia", 5.00, 0.23, 0.150, 30),
        ("Belgium v Egypt", "Total Goals Over/Under", "Under 2.5 Goals", 1.95, 0.57, 0.112, 50),
    ]
    return {
        "version": "fixture-pdf",
        "recommended_new_exposure_aud": sum(item[-1] for item in recommendations),
        "automation_gate": gate,
        "recommendations": [
            {
                "match": match,
                "market": market,
                "selection": selection,
                "odds": odds,
                "model_probability": probability,
                "expected_value": ev,
                "stake_aud": stake,
                "decision": "buy",
                "rationale": "fixture edge",
            }
            for match, market, selection, odds, probability, ev, stake in recommendations
        ],
    }


def pdf_futures_artifact():
    teams = ["Belgium", "Colombia", "Japan", "Morocco", "Croatia"]
    return {
        "version": "fixture-pdf",
        "automation_gate": ready_pdf_gate(),
        "recommendations": [
            {
                "team": team,
                "market": "To Qualify for Quarter Final",
                "odds": 3.2 + index * 0.2,
                "no_vig_probability": 0.24 + index * 0.01,
                "stake_aud": 0,
                "rationale": "路径仍需确认，观察不下注。",
            }
            for index, team in enumerate(teams)
        ],
    }


def pdf_group_artifact():
    return {
        "version": "fixture-pdf",
        "automation_gate": ready_pdf_gate(),
        "recommendations": [
            {
                "group": group,
                "team": team,
                "market": "Group Winner",
                "odds": 2.6 + index * 0.3,
                "no_vig_probability": 0.22 + index * 0.02,
                "stake_aud": 0,
                "rationale": "等待逐场路径模型确认。",
            }
            for index, (group, team) in enumerate([("F", "Japan"), ("C", "Morocco"), ("D", "Australia"), ("E", "Croatia"), ("G", "Belgium")])
        ],
    }


def pdf_australia_artifact():
    rows = [
        ("Team Total Group Goals Scored O/U", "AUS Under 3.5 Group Gls", 1.85, 0.58),
        ("AUS Concede In Every Group Match", "AUS Concede Every Grp Match", 2.10, 0.49),
        ("Team Total Group Goals Conceded O/U", "AUS Concede Under 5.5 Grp Gls", 1.95, 0.54),
        ("AUS Group Point O/U", "AUS Over 2.5 Grp Pts", 2.25, 0.46),
        ("AUS Group Exact Finishing Position", "AUS 4th In Grp D", 3.30, 0.33),
    ]
    return {
        "version": "fixture-pdf",
        "automation_gate": ready_pdf_gate(),
        "recommendations": [],
        "markets": [
            {
                "market": market,
                "probability_method": "fixture_no_vig",
                "rows": [{"selection": selection, "odds": odds, "probability": probability}],
            }
            for market, selection, odds, probability in rows
        ],
    }


def pdf_team_multi_artifact():
    return {"version": "fixture-pdf", "automation_gate": ready_pdf_gate(), "recommendations": []}


class PipelineTests(unittest.TestCase):
    def test_goal_traceability_source_and_homepage_trace_include_chatgpt_template_and_value_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            downloads = home / "Downloads"
            workspace = root / "workspace"
            pipeline = workspace / "work" / "tab-research-pipeline"
            report_dir = downloads / "FIFA Report"
            (workspace / "outputs").mkdir(parents=True)
            pipeline.mkdir(parents=True)
            report_dir.mkdir(parents=True)
            (downloads / "football_betting_analysis_ABC_template.xlsx").write_text("fixture", encoding="utf-8")
            (workspace / "HANDOFF.md").write_text("handoff", encoding="utf-8")
            (workspace / "outputs" / "fifa_prd_and_technical_plan.md").write_text("prd", encoding="utf-8")
            (pipeline / "HANDOFF.md").write_text("pipeline handoff", encoding="utf-8")
            (pipeline / "README.md").write_text("readme", encoding="utf-8")
            (pipeline / "RUNBOOK.md").write_text("runbook", encoding="utf-8")
            entry_html = report_dir / "TAB FIFA盘口研究系统.html"
            entry_html.write_text(
                """
                <h2>推荐下注板块</h2>
                <button>主动测试并自动补缺</button>
                <table><thead><tr>
                <th>时间</th><th>板块</th><th>盘口</th><th>下注</th><th>赔率</th><th>金额</th><th>操作</th>
                <th>分析一致性</th><th>盘口价值</th><th>Edge</th><th>套利率</th><th>Risk of ruin</th>
                <th>EV</th><th>概率赔率编辑</th><th>置信度</th><th>价值信号</th><th>价格容忍度</th>
                <th>上限占用</th><th>Kelly安全垫</th><th>风险调整分</th><th>非surebet</th>
                </tr></thead></table>
                <h2>今日操作摘要</h2>
                <h2>主动测试与补跑</h2>
                """,
                encoding="utf-8",
            )
            with mock.patch("tab_research.goal_traceability.Path.home", return_value=home):
                source = source_file_trace(workspace, pipeline)
                entry = downloads_entry_trace()
            self.assertTrue(source["chatgpt_template_exists"])
            self.assertTrue(source["requirements_trace_ready"])
            self.assertFalse(source["original_prompt_exists"])
            self.assertIn("football_betting_analysis_ABC_template.xlsx", [item["name"] for item in source["available_sources"]])
            self.assertEqual(entry["required_column_count"], 21)
            self.assertEqual(entry["present_required_column_count"], 21)
            self.assertTrue(entry["all_required_columns"])
            self.assertTrue(entry["recommendation_first"])
            self.assertTrue(entry["active_test_in_recommendation"])

    def test_parse_market_pairs(self):
        section = """Result
Mexico
1.42
1.42
Draw
4.25
4.25
South Africa
8.00
8.00
	"""
        self.assertEqual(parse_market_pairs(section, "Result"), {"Mexico": 1.42, "Draw": 4.25, "South Africa": 8.0})

    def test_decimal_odds_validation_is_shared_and_fail_closed(self):
        self.assertEqual(parse_decimal_odds("1.01"), 1.01)
        self.assertTrue(valid_decimal_odds(2.5))
        for value in ["1.00", "0", "SUSP", "NaN", "inf", float("nan"), float("inf"), None, True]:
            self.assertIsNone(parse_decimal_odds(value))
            self.assertFalse(valid_decimal_odds(value))
        with self.assertRaises(ValueError):
            novig_probabilities([2.0, 1.0])
        with self.assertRaises(ValueError):
            implied_probability(float("inf"))

    def test_parse_market_pairs_rejects_invalid_decimal_odds_tokens(self):
        section = """Result
Mexico
1.00
Draw
NaN
South Africa
SUSP
"""
        self.assertEqual(parse_market_pairs(section, "Result"), {})
        invalid = invalid_market_price_rows(section, "Result")
        self.assertEqual(invalid, ["Mexico=1.00", "Draw=NaN"])

    def test_matches_gate_blocks_invalid_raw_decimal_odds(self):
        raw = full_matches_raw_fixture()
        raw["matches"][0]["markets"]["Result"] = """Result
Mexico
1.00
Draw
4.25
South Africa
8.00
"""
        public_ok = {"all_sources_ok": True, "ok_count": 3, "source_count": 3}
        event_ok = {"all_feeds_ok": True, "ok_count": 1, "feed_count": 1, "flagged_item_count": 0}
        gate = automation_gate(raw, generate_candidates(raw), public_ok, event_ok)
        self.assertFalse(gate["automation_ready"])
        self.assertEqual(gate["coverage"]["market_integrity_errors"], 1)
        self.assertTrue(any("Invalid decimal odds" in reason for reason in gate["blocking_reasons"]))
        audit = quality_audit(raw)
        self.assertEqual(audit["market_integrity_errors"][0]["match"], "Mexico v South Africa")

    def test_markdown_reports_include_visual_summary_charts(self):
        match_gate = {
            "automation_ready": True,
            "manual_report_ready": True,
            "blocking_reasons": [],
            "coverage": {
                "detail_main_markets": {"covered": 26, "total": 26},
                "full_main_markets": {"covered": 26, "total": 26},
            },
            "quality_audit": {"missing_detail_matches": [], "partial_core_only_matches": [], "matches_with_errors": []},
            "public_sources": {"ready": True},
            "event_monitor": {"ready": True},
        }
        matches_report = render_matches_markdown(
            {
                "version": "test",
                "bankroll_aud": 4000,
                "unit_aud": 40,
                "recommended_new_exposure_aud": 40,
                "automation_gate": match_gate,
                "public_source_baseline": [{"name": "FIFA", "usage": "schedule", "url": "https://www.fifa.com"}],
                "recommendations": [
                    {
                        "match": "A v B",
                        "market": "Result",
                        "selection": "A",
                        "odds": 2.2,
                        "model_probability": 0.5,
                        "breakeven_probability": 0.45,
                        "expected_value": 0.1,
                        "stake_aud": 40,
                        "stake_unit": 1.0,
                        "decision": "buy",
                        "event_risk": {"flag_count": 0},
                    }
                ],
            }
        )
        futures_report = render_futures_markdown(
            {
                "version": "test",
                "automation_gate": {"automation_ready": True, "manual_report_ready": True, "blocking_reasons": [], "coverage": {"teams": {"covered": 2, "total": 2}}},
                "rows": [
                    {"team": "Japan", "markets": {"Winner": 15, "To Qualify for Final": 8, "To Qualify For Semi Final": 4, "To Qualify for Quarter Final": 2}},
                    {"team": "Brazil", "markets": {"Winner": 6, "To Qualify for Final": 3, "To Qualify For Semi Final": 2, "To Qualify for Quarter Final": 1.4}},
                ],
                "probabilities": {"Winner": {"Japan": 0.30, "Brazil": 0.70}, "To Qualify for Quarter Final": {"Japan": 0.42, "Brazil": 0.58}},
                "recommendations": [{"team": "Japan", "market": "Winner", "odds": 15, "no_vig_probability": 0.3, "decision": "watch", "stake_aud": 0, "rationale": "fixture"}],
            }
        )
        group_report = render_group_markdown(
            {
                "version": "test",
                "automation_gate": {"automation_ready": True, "manual_report_ready": True, "blocking_reasons": [], "coverage": {"groups": {"covered": 1, "total": 1}, "complete_group_winner_markets": {"covered": 1, "total": 1}}},
                "groups": [{"group": "A", "rows": [{"team": "Japan", "odds": 2.5}], "probabilities": {"Japan": 1.0}}],
                "recommendations": [{"group": "A", "team": "Japan", "odds": 2.5, "no_vig_probability": 1.0, "decision": "watch", "stake_aud": 0, "rationale": "fixture"}],
            }
        )
        australia_report = render_australia_markdown(
            {
                "version": "test",
                "automation_gate": {"automation_ready": True, "manual_report_ready": True, "blocking_reasons": [], "coverage": {"markets": {"covered": 1, "total": 1}, "priced_markets": {"covered": 1, "total": 1}}},
                "markets": [{"market": "AUS Group Point O/U", "status": "priced", "probability_method": "fixture", "rows": [{"selection": "Over", "odds": 2.2, "probability": 0.55}]}],
                "recommendations": [{"market": "AUS Group Point O/U", "selection": "Over", "odds": 2.2, "probability": 0.55, "decision": "watch", "stake_aud": 0, "stake_unit": 0, "rationale": "fixture"}],
            }
        )
        team_multi_report = render_team_multi_markdown(
            {
                "version": "test",
                "automation_gate": {"automation_ready": True, "manual_report_ready": True, "blocking_reasons": [], "coverage": {"teams": {"covered": 1, "total": 1}, "complete_team_markets": {"covered": 1, "total": 1}}},
                "rows": [{"team": "Japan", "markets": {"Win World Cup": 15, "Reach Final": 8, "Reach Semi Final": 4, "Reach Quarter Final": 2}}],
                "probabilities": {"Win World Cup": {"Japan": 1.0}, "Reach Quarter Final": {"Japan": 1.0}},
                "recommendations": [{"team": "Japan", "market": "Reach Quarter Final", "odds": 2, "no_vig_probability": 1.0, "decision": "watch", "stake_aud": 0, "stake_unit": 0, "rationale": "fixture"}],
            }
        )
        portfolio_report = render_portfolio_markdown(
            {
                "portfolio_automation_ready": True,
                "ready_required_board_count": 1,
                "required_board_count": 1,
                "generated_at": "2026-06-04T00:00:00Z",
                "blocking_reasons": [],
                "board_statuses": [
                    {
                        "priority": 1,
                        "name": "2026 World Cup Matches",
                        "ready": True,
                        "raw_exists": True,
                        "raw_fresh": True,
                        "raw_valid": True,
                        "gate_ready": True,
                        "report_exists": True,
                        "missing": [],
                    }
                ],
            }
        )
        for report in [matches_report, futures_report, group_report, australia_report, team_multi_report, portfolio_report]:
            self.assertIn("## Visual Summary", report)
            self.assertIn("```mermaid", report)

    def test_generate_candidates_and_gate(self):
        raw = full_matches_raw_fixture()
        candidates = generate_candidates(raw)
        self.assertGreater(len(candidates), 0)
        gate = automation_gate(raw, candidates)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(gate["manual_report_ready"])
        self.assertIn("quality_audit", gate)
        self.assertFalse(gate["public_sources"]["ready"])

    def test_matches_gate_uses_live_target_matches_when_present(self):
        raw = {
            "generated_at": "2026-06-12T00:00:00Z",
            "target_source": "live_board_discovery",
            "target_matches": ["Canada v Bosn-Herzegovina", "USA v Paraguay"],
            "matches": [
                full_match_fixture("Canada v Bosn-Herzegovina"),
                full_match_fixture("USA v Paraguay"),
            ],
        }
        public_ok = {"all_sources_ok": True, "ok_count": 3, "source_count": 3}
        event_ok = {"all_feeds_ok": True, "ok_count": 1, "feed_count": 1, "flagged_item_count": 0}
        self.assertEqual(expected_match_names(raw), ["Canada v Bosn-Herzegovina", "USA v Paraguay"])
        gate = automation_gate(raw, generate_candidates(raw), public_ok, event_ok)
        self.assertTrue(gate["automation_ready"], gate)
        self.assertTrue(gate["manual_report_ready"], gate)
        self.assertEqual(gate["coverage"]["target_source"], "live_board_discovery")
        self.assertEqual(gate["coverage"]["detail_main_markets"], {"covered": 2, "total": 2, "rate": 1.0})
        self.assertEqual(quality_audit(raw)["missing_detail_matches"], [])
        validation = validate_raw_snapshot("world_cup_matches", raw)
        self.assertTrue(validation["valid"], validation)
        self.assertEqual(validation["errors"], [])
        self.assertEqual(validation["pre_match_eligible_count"], 2)

    def test_matches_raw_validation_excludes_in_play_from_pre_match_coverage(self):
        raw = {
            "generated_at": "2026-06-13T00:00:00Z",
            "target_source": "live_board_discovery",
            "target_matches": ["Canada v Bosn-Herzegovina", "USA v Paraguay"],
            "matches": [
                full_match_fixture("Canada v Bosn-Herzegovina"),
                full_match_fixture("USA v Paraguay"),
            ],
        }
        usa = raw["matches"][1]
        usa["text"] = "USA v Paraguay\nIn-Play|Bet by phone for suspended markets."
        usa["markets"]["Both Teams to Score"] = "Both Teams to Score\nUSA v Paraguay\nIn-Play|Bet by phone\n"

        validation = validate_raw_snapshot("world_cup_matches", raw)

        self.assertTrue(validation["valid"], validation)
        self.assertEqual(validation["pre_match_eligible_count"], 1)
        self.assertEqual(validation["in_play_excluded_matches"], ["USA v Paraguay"])
        self.assertEqual(validation["errors"], [])

    def test_matches_gate_blocks_missing_live_target_match(self):
        raw = {
            "generated_at": "2026-06-12T00:00:00Z",
            "target_source": "live_board_discovery",
            "target_matches": ["Canada v Bosn-Herzegovina", "USA v Paraguay"],
            "matches": [full_match_fixture("Canada v Bosn-Herzegovina")],
        }
        public_ok = {"all_sources_ok": True, "ok_count": 3, "source_count": 3}
        event_ok = {"all_feeds_ok": True, "ok_count": 1, "feed_count": 1, "flagged_item_count": 0}
        gate = automation_gate(raw, generate_candidates(raw), public_ok, event_ok)
        self.assertFalse(gate["automation_ready"])
        self.assertEqual(gate["coverage"]["detail_main_markets"], {"covered": 1, "total": 2, "rate": 0.5})
        self.assertEqual(quality_audit(raw)["missing_detail_matches"], ["USA v Paraguay"])
        validation = validate_raw_snapshot("world_cup_matches", raw)
        self.assertFalse(validation["valid"])
        self.assertTrue(any("detail coverage 1/2" in item for item in validation["errors"]))

    def test_quality_audit(self):
        audit = quality_audit(partial_matches_raw_fixture())
        self.assertIn("Ghana v Panama", audit["missing_detail_matches"])
        self.assertIn("Portugal v DR Congo", audit["partial_core_only_matches"])
        self.assertGreater(len(audit["matches_with_errors"]), 0)

    def test_write_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            raw_path = output_dir / "matches_raw.json"
            previous = output_dir / "previous_report_baseline.json"
            public_source_audit = output_dir / "public_source_audit.json"
            event_audit = output_dir / "event_audit.json"
            atomic_write_json(raw_path, full_matches_raw_fixture())
            atomic_write_json(previous, {"version": "fixture", "recommendations": []})
            atomic_write_json(public_source_audit, {"all_sources_ok": True, "ok_count": 3, "source_count": 3})
            atomic_write_json(event_audit, {"all_feeds_ok": True, "ok_count": 1, "feed_count": 1, "flagged_item_count": 0})
            result = write_outputs(
                raw_path,
                Path(tmp),
                version="test",
                previous_baseline_path=previous,
                public_source_audit_path=public_source_audit,
                event_audit_path=event_audit,
            )
            self.assertEqual(result["export_status"], "ready")
            self.assertIn("recommendations", result)
            self.assertIn("daily_compare", result)
            self.assertTrue((Path(tmp) / "tab_fifa_world_cup_matches_recommendations_test.json").exists())
            self.assertTrue((Path(tmp) / "automation_gate_test.json").exists())
            self.assertTrue((Path(tmp) / "previous_report_baseline_test.json").exists())

    def test_write_outputs_fails_closed_without_success_deliverables_when_gate_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            raw_path = output_dir / "matches_raw.json"
            atomic_write_json(raw_path, full_matches_raw_fixture())

            result = write_outputs(raw_path, output_dir, version="blocked")

            self.assertEqual(result["export_status"], "failed_closed")
            self.assertEqual(result["failure_stage"], "validation")
            self.assertFalse(result["automation_gate"]["automation_ready"])
            self.assertEqual(result["recommended_new_exposure_aud"], 0)
            self.assertEqual(result["recommendations"], [])
            self.assertTrue((output_dir / "automation_gate_blocked.json").exists())
            self.assertTrue((output_dir / "tab_fifa_world_cup_matches_failed_closed_blocked.json").exists())
            self.assertFalse((output_dir / "tab_fifa_world_cup_matches_recommendations_blocked.json").exists())
            self.assertFalse((output_dir / "tab_fifa_world_cup_matches_blocked_pipeline_report.md").exists())
            self.assertFalse((output_dir / "previous_report_baseline_blocked.json").exists())
            self.assertTrue(any("Public source audit" in item for item in result["blocking_reasons"]))

    def test_write_outputs_fails_closed_on_raw_parse_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            raw_path = output_dir / "broken_raw.json"
            raw_path.write_text("{not json", encoding="utf-8")

            result = write_outputs(raw_path, output_dir, version="parse-error")

            self.assertEqual(result["export_status"], "failed_closed")
            self.assertEqual(result["failure_stage"], "parse")
            self.assertEqual(result["recommendations"], [])
            self.assertTrue((output_dir / "tab_fifa_world_cup_matches_failed_closed_parse-error.json").exists())
            self.assertFalse((output_dir / "tab_fifa_world_cup_matches_recommendations_parse-error.json").exists())
            self.assertFalse((output_dir / "tab_fifa_world_cup_matches_parse-error_pipeline_report.md").exists())

    def test_write_outputs_legacy_blocked_export_requires_explicit_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            raw_path = output_dir / "matches_raw.json"
            atomic_write_json(raw_path, full_matches_raw_fixture())

            result = write_outputs(raw_path, output_dir, version="legacy", allow_blocked_export=True)

            self.assertEqual(result["export_status"], "legacy_blocked_export")
            self.assertFalse(result["automation_gate"]["automation_ready"])
            self.assertTrue((output_dir / "tab_fifa_world_cup_matches_recommendations_legacy.json").exists())
            self.assertTrue((output_dir / "tab_fifa_world_cup_matches_legacy_pipeline_report.md").exists())
            self.assertTrue((output_dir / "previous_report_baseline_legacy.json").exists())

    def test_public_source_audit(self):
        sources = [
            PublicSource(
                name="Test source",
                url="https://example.test/source",
                usage="test",
                required_terms=["World Cup", "ranking"],
            )
        ]

        def fetcher(_url):
            return 200, "Official World Cup ranking page"

        result = audit_sources(sources=sources, fetcher=fetcher)
        self.assertTrue(result["all_sources_ok"])
        self.assertEqual(result["ok_count"], 1)

    def test_event_monitor_parse_and_risk(self):
        xml = """<?xml version="1.0"?>
<rss><channel><item>
<title>Morocco World Cup squad injury doubt</title>
<link>https://example.test/story</link>
<source>Example</source>
<pubDate>Wed, 03 Jun 2026 00:00:00 GMT</pubDate>
</item></channel></rss>"""
        items = parse_google_news_rss("Morocco", xml)
        self.assertEqual(len(items), 1)
        self.assertIn("injury", items[0].matched_keywords)
        audit = {
            "flagged_items": [
                {
                    "team": "Morocco",
                    "title": items[0].title,
                    "matched_keywords": items[0].matched_keywords,
                    "source": "Example",
                }
            ]
        }
        risk = event_risk_for_match("Brazil v Morocco", audit)
        self.assertEqual(risk["flag_count"], 1)

    def test_event_feed_audit(self):
        def fetcher(_url):
            return 200, """<?xml version="1.0"?><rss><channel><item><title>Japan World Cup squad news</title></item></channel></rss>"""

        result = audit_event_feeds(teams=["Japan"], fetcher=fetcher)
        self.assertTrue(result["all_feeds_ok"])
        self.assertEqual(result["ok_count"], 1)

    def test_full_gate_requires_event_monitor(self):
        raw = full_matches_raw_fixture()
        candidates = generate_candidates(raw)
        public_ok = {"all_sources_ok": True, "ok_count": 3, "source_count": 3}
        without_event = automation_gate(raw, candidates, public_ok)
        self.assertFalse(without_event["automation_ready"])
        event_ok = {"all_feeds_ok": True, "ok_count": 1, "feed_count": 1, "flagged_item_count": 0}
        with_event = automation_gate(raw, candidates, public_ok, event_ok)
        self.assertTrue(with_event["automation_ready"])
        raw_with_error = full_matches_raw_fixture()
        raw_with_error["matches"][0]["errors"] = ["Market header expansion failed for Double Chance: timeout"]
        with_market_error = automation_gate(raw_with_error, generate_candidates(raw_with_error), public_ok, event_ok)
        self.assertFalse(with_market_error["automation_ready"])
        self.assertIn("Market expansion errors remain in raw data.", with_market_error["blocking_reasons"])

    def test_compare_recommendations(self):
        before = {
            "version": "before",
            "recommended_new_exposure_aud": 10,
            "recommendations": [
                {"match": "A v B", "market": "Result", "selection": "A", "odds": 2.0, "model_probability": 0.55, "expected_value": 0.10, "stake_aud": 10}
            ],
        }
        after = {
            "version": "after",
            "recommended_new_exposure_aud": 20,
            "recommendations": [
                {"match": "A v B", "market": "Result", "selection": "A", "odds": 2.1, "model_probability": 0.56, "expected_value": 0.176, "stake_aud": 20},
                {"match": "C v D", "market": "Result", "selection": "D", "odds": 4.0, "model_probability": 0.30, "expected_value": 0.20, "stake_aud": 10},
            ],
        }
        diff = compare_recommendations(after, before)
        self.assertEqual(diff["summary"]["added_count"], 1)
        self.assertEqual(diff["summary"]["changed_count"], 1)
        self.assertEqual(diff["summary"]["exposure_change_aud"], 10)

    def test_portfolio_compare_covers_all_boards(self):
        before = {
            "world_cup_matches": {
                "version": "before",
                "recommendations": [
                    {"match": "A v B", "market": "Result", "selection": "A", "odds": 2.0, "model_probability": 0.55, "expected_value": 0.10, "stake_aud": 10}
                ],
            },
            "world_cup_futures": {
                "version": "before",
                "recommendations": [
                    {"team": "Japan", "market": "Reach Quarter Final", "odds": 3.5, "no_vig_probability": 0.30, "stake_aud": 0}
                ],
            },
        }
        after = {
            "world_cup_matches": {
                "version": "after",
                "recommendations": [
                    {"match": "A v B", "market": "Result", "selection": "A", "odds": 2.2, "model_probability": 0.57, "expected_value": 0.25, "stake_aud": 20}
                ],
            },
            "world_cup_group_betting": {
                "version": "after",
                "recommendations": [
                    {"group": "F", "team": "Japan", "market": "Group Winner", "odds": 3.65, "no_vig_probability": 0.25, "stake_aud": 0}
                ],
            },
        }
        previous = compact_portfolio_baseline(before)
        diff = compare_portfolio_recommendations(after, previous)
        self.assertEqual(diff["summary"]["added_count"], 1)
        self.assertEqual(diff["summary"]["removed_count"], 1)
        self.assertEqual(diff["summary"]["changed_count"], 1)
        self.assertIn("world_cup_matches", diff["by_board"])
        self.assertIn("world_cup_group_betting", diff["by_board"])
        self.assertEqual(diff["by_board"]["world_cup_matches"]["exposure_change_aud"], 10)

    def test_pdf_portfolio_compare_override_wins_over_latest(self):
        import generate_business_pdf_report as pdf_report

        with tempfile.TemporaryDirectory() as tmp:
            original_out = pdf_report.OUT
            original_load_json = pdf_report.load_json
            try:
                pdf_report.OUT = Path(tmp)
                atomic_write_json(pdf_report.OUT / "portfolio_daily_compare_latest.json", {"summary": {"added_count": 99}})

                def fail_if_latest_is_read(_name):
                    raise AssertionError("current run PDF must not read portfolio_daily_compare_latest.json")

                pdf_report.load_json = fail_if_latest_is_read
                current = {"summary": {"added_count": 1}, "by_board": {}}
                self.assertEqual(resolve_portfolio_compare(current), current)
            finally:
                pdf_report.OUT = original_out
                pdf_report.load_json = original_load_json

    def test_render_pdf_fixture_generates_valid_private_and_public_reports(self):
        import generate_business_pdf_report as pdf_report
        from pypdf import PdfReader

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "outputs"
            private_dir = root / "private"
            report_dir = root / "downloads" / "FIFA Report"
            output_dir.mkdir()
            private_dir.mkdir()
            report_dir.mkdir(parents=True)

            originals = {
                "OUT": pdf_report.OUT,
                "PRIVATE_DATA_DIR": pdf_report.PRIVATE_DATA_DIR,
                "REPORT_DIR": pdf_report.REPORT_DIR,
                "REPORT_DATE": pdf_report.REPORT_DATE,
                "PDF_PATH": pdf_report.PDF_PATH,
                "OUTPUT_COPY_PATH": pdf_report.OUTPUT_COPY_PATH,
                "BANKROLL_PLAN_PATH": pdf_report.BANKROLL_PLAN_PATH,
                "PRIVATE_BANKROLL_PLAN_PATH": pdf_report.PRIVATE_BANKROLL_PLAN_PATH,
                "audit_raw_refresh": pdf_report.audit_raw_refresh,
                "audit_portfolio": pdf_report.audit_portfolio,
                "audit_safety": pdf_report.audit_safety,
            }
            try:
                pdf_report.OUT = output_dir
                pdf_report.PRIVATE_DATA_DIR = private_dir
                pdf_report.REPORT_DIR = report_dir
                pdf_report.REPORT_DATE = "01012026"
                pdf_report.PDF_PATH = report_dir / "01012026.pdf"
                pdf_report.OUTPUT_COPY_PATH = output_dir / "01012026.pdf"
                pdf_report.BANKROLL_PLAN_PATH = output_dir / "tab_fifa_bankroll_plan_01012026.json"
                pdf_report.PRIVATE_BANKROLL_PLAN_PATH = private_dir / "tab_fifa_bankroll_plan_01012026.json"
                pdf_report.audit_raw_refresh = lambda _out: {"raw_refresh_ready": True, "blocking_reasons": []}
                pdf_report.audit_portfolio = lambda _out: {
                    "portfolio_automation_ready": True,
                    "ready_required_board_count": 5,
                    "required_board_count": 5,
                    "board_statuses": [
                        {"name": "Matches", "ready": True, "raw_fresh": True, "raw_valid": True, "gate_ready": True, "report_exists": True},
                        {"name": "Futures", "ready": True, "raw_fresh": True, "raw_valid": True, "gate_ready": True, "report_exists": True},
                    ],
                    "blocking_reasons": [],
                }
                pdf_report.audit_safety = lambda *_args, **_kwargs: {"automation_safety_ready": True, "blocking_reasons": []}

                model_fixture = generate_model_comparison(full_matches_raw_fixture())
                match_fixture = enrich_match_recommendations_with_model_comparison(pdf_matches_artifact(), model_fixture)
                atomic_write_json(output_dir / pdf_report.MATCHES_BOARD.recommendations_artifact, match_fixture)
                atomic_write_json(output_dir / pdf_report.FUTURES_BOARD.recommendations_artifact, pdf_futures_artifact())
                atomic_write_json(output_dir / pdf_report.GROUP_BOARD.recommendations_artifact, pdf_group_artifact())
                atomic_write_json(output_dir / pdf_report.AUSTRALIA_BOARD.recommendations_artifact, pdf_australia_artifact())
                atomic_write_json(output_dir / pdf_report.TEAM_MULTI_BOARD.recommendations_artifact, pdf_team_multi_artifact())
                atomic_write_json(output_dir / MODEL_COMPARISON_JSON, model_fixture)
                atomic_write_json(
                    private_dir / "tab_my_bets_positions_01012026.json",
                    {
                        "summary": {
                            "bet_count": 1,
                            "pending_count": 1,
                            "settled_count": 0,
                            "unknown_status_count": 0,
                            "total_stake_aud": 2000,
                            "open_stake_aud": 2000,
                            "realized_pnl_aud": 0,
                            "realized_roi": 0,
                            "estimated_return_if_all_win_aud": 2600,
                            "potential_profit_if_all_win_aud": 600,
                        },
                        "bets": [
                            {
                                "placed_at_text": "01 Jan 2026",
                                "selection": "Japan",
                                "market": "Result",
                                "stake_aud": 2000,
                                "odds": 1.30,
                                "estimated_return_aud": 2600,
                                "status": "Pending",
                            }
                        ],
                    },
                )

                portfolio_compare = compare_portfolio_recommendations({"world_cup_matches": match_fixture}, None)
                summary = pdf_report.render_pdf(portfolio_compare_override=portfolio_compare)

                public_pdf = Path(summary["pdf_output_copy"])
                self.assertTrue(public_pdf.exists())
                self.assertEqual(Path(summary["pdf_path"]), public_pdf)
                self.assertFalse((report_dir / "01012026.pdf").exists())
                self.assertFalse(summary["private_pdf_available"])
                self.assertTrue(summary["private_pdf_path_omitted"])
                self.assertGreater(public_pdf.stat().st_size, 8_000)
                self.assertEqual(public_pdf.read_bytes()[:4], b"%PDF")

                public_reader = PdfReader(str(public_pdf))
                self.assertGreaterEqual(len(public_reader.pages), 1)
                public_text = "\n".join(page.extract_text() or "" for page in public_reader.pages)
                self.assertIn("公开脱敏研究副本", public_text)
                self.assertIn("模型交叉验证", public_text)
                self.assertIn("模型交叉验证审计", public_text)
                self.assertIn("Top分歧比赛", public_text)
                self.assertIn("Elo/Dixon-Coles", public_text)
                self.assertIn("可复用/UI启发", public_text)
                self.assertNotIn("Public Sanitized Research Copy", public_text)
                self.assertNotIn("Professional Betting Research Report", public_text)
                self.assertNotIn(str(report_dir), public_text)
                self.assertNotIn("/Users/", public_text)
                self.assertNotIn("private_detail_path", public_text)
                self.assertNotIn("placed_at_text", public_text)
                self.assertNotIn("01 Jan 2026", public_text)
                self.assertNotIn("持仓状态已读取", public_text)
                self.assertNotIn("TAB私有持仓", public_text)

                public_bankroll = json.loads(pdf_report.BANKROLL_PLAN_PATH.read_text(encoding="utf-8"))
                self.assertTrue(public_bankroll["private_pdf_path_omitted"])
                self.assertEqual(public_bankroll["pdf_output_copy"], public_pdf.name)
                self.assertNotIn("pdf_path", public_bankroll)
                self.assertNotIn("positions_ready", public_bankroll)
                self.assertNotIn("private_detail_available", public_bankroll)
                self.assertNotIn("match_stakes", public_bankroll)
                self.assertNotIn(str(report_dir), json.dumps(public_bankroll, ensure_ascii=False))
                self.assertGreater(public_bankroll["time_adjusted_new_exposure_aud"], 0)
                public_gate = audit_public_artifact_safety([public_pdf, pdf_report.BANKROLL_PLAN_PATH])
                self.assertTrue(public_gate["public_artifact_safety_ready"], public_gate)
                pdf_qa = audit_pdf_report(
                    public_pdf,
                    min_size_bytes=8_000,
                    visual_smoke=True,
                    require_visual_smoke=True,
                )
                self.assertTrue(pdf_qa["pdf_qa_ready"], pdf_qa)
                self.assertTrue(pdf_qa["visual_smoke"]["ready"], pdf_qa["visual_smoke"])
            finally:
                for name, value in originals.items():
                    setattr(pdf_report, name, value)

    def test_pdf_qa_detects_missing_required_report_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "qa.pdf"
            styles = getSampleStyleSheet()
            custom_terms = ["Hicruben", "goalmodel", "RyanSCodes"]
            story = [Paragraph(term, styles["Normal"]) for term in custom_terms]
            SimpleDocTemplate(str(pdf_path), pagesize=A4).build(story)
            ok = audit_pdf_report(
                pdf_path,
                required_terms=custom_terms,
                min_pages=1,
                min_text_chars=20,
                min_size_bytes=100,
                visual_smoke=True,
                require_visual_smoke=True,
            )
            self.assertTrue(ok["pdf_qa_ready"], ok)
            self.assertTrue(ok["visual_smoke"]["ready"], ok["visual_smoke"])

            missing_path = Path(tmp) / "missing.pdf"
            SimpleDocTemplate(str(missing_path), pagesize=A4).build([Paragraph("不完整报告", styles["Normal"])])
            failed = audit_pdf_report(missing_path, min_pages=1, min_text_chars=1, min_size_bytes=100)
            self.assertFalse(failed["pdf_qa_ready"])
            self.assertIn("模型交叉验证", failed["missing_terms"])
            self.assertIn("模型交叉验证审计", failed["missing_terms"])
            self.assertIn("Top分歧比赛", failed["missing_terms"])

    def test_pdf_qa_visual_smoke_detects_blank_rendering(self):
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "invisible.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=A4)
            c.setFillColorRGB(1, 1, 1)
            c.drawString(72, 720, "Invisible report text")
            c.showPage()
            c.save()

            failed = audit_pdf_report(
                pdf_path,
                required_terms=[],
                min_pages=1,
                min_text_chars=0,
                min_size_bytes=100,
                visual_smoke=True,
                require_visual_smoke=True,
            )
            self.assertFalse(failed["pdf_qa_ready"], failed)
            self.assertTrue(failed["visual_smoke"]["available"], failed["visual_smoke"])
            self.assertFalse(failed["visual_smoke"]["ready"], failed["visual_smoke"])
            self.assertIn("PDF visual smoke failed", "; ".join(failed["blocking_reasons"]))

    def test_daily_baseline_latest_publish_and_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            fallback = output_dir / "previous_report_baseline_v0_10.json"
            current = output_dir / "previous_report_baseline_test.json"
            latest = output_dir / "previous_report_baseline_latest.json"
            fallback.write_text('{"version": "v0_10", "recommendations": []}', encoding="utf-8")
            self.assertEqual(select_previous_baseline_path(output_dir), fallback)
            current.write_text('{"version": "test", "recommendations": [{"match": "A v B", "market": "Result", "selection": "A"}]}', encoding="utf-8")
            published = publish_latest_baseline(output_dir, "test")
            self.assertEqual(published, latest)
            self.assertEqual(select_previous_baseline_path(output_dir), latest)
            self.assertEqual(json.loads(latest.read_text())["version"], "test")

    def test_previous_baselines_prefer_committed_latest_commit_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            stale_latest = output_dir / "previous_report_baseline_latest.json"
            stale_portfolio_latest = output_dir / "portfolio_report_baseline_latest.json"
            committed_baseline = output_dir / "previous_report_baseline_committed.json"
            committed_portfolio = output_dir / "portfolio_report_baseline_committed.json"
            atomic_write_json(stale_latest, {"version": "stale_latest"})
            atomic_write_json(stale_portfolio_latest, {"version": "stale_portfolio_latest"})
            atomic_write_json(committed_baseline, {"version": "committed"})
            atomic_write_json(committed_portfolio, {"version": "committed_portfolio"})
            atomic_write_json(
                output_dir / "latest_commit.json",
                {
                    "status": "ready_for_manual_report",
                    "public_artifact_safety_ready": True,
                    "artifacts": {
                        "current_baseline": committed_baseline.name,
                        "portfolio_baseline": committed_portfolio.name,
                    },
                },
            )
            self.assertEqual(select_previous_baseline_path(output_dir), committed_baseline)
            self.assertEqual(select_previous_portfolio_baseline_path(output_dir), committed_portfolio)

            atomic_write_json(
                output_dir / "latest_commit.json",
                {
                    "status": "blocked_by_gate",
                    "public_artifact_safety_ready": False,
                    "artifacts": {
                        "current_baseline": committed_baseline.name,
                        "portfolio_baseline": committed_portfolio.name,
                    },
                },
            )
            self.assertEqual(select_previous_baseline_path(output_dir), stale_latest)
            self.assertEqual(select_previous_portfolio_baseline_path(output_dir), stale_portfolio_latest)

    def test_report_store_and_dashboard_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            matches_board = board_by_id("world_cup_matches")
            portfolio = {
                "portfolio_automation_ready": True,
                "required_board_count": 1,
                "ready_required_board_count": 1,
                "board_statuses": [
                    {
                        "board_id": matches_board.board_id,
                        "name": matches_board.name,
                        "priority": matches_board.priority,
                        "ready": True,
                        "raw_fresh": True,
                        "raw_valid": True,
                        "gate_ready": True,
                        "report_exists": True,
                        "raw_age_hours": 0.5,
                        "missing": [],
                        "raw_validation_errors": [],
                    }
                ],
            }
            recommendations = {
                "version": "test",
                "recommended_new_exposure_aud": 10,
                "recommendations": [
                    {
                        "match": "A v B",
                        "market": "Result",
                        "selection": "A",
                        "odds": 2.0,
                        "model_probability": 0.56,
                        "expected_value": 0.12,
                        "stake_aud": 10,
                        "decision": "small_stake",
                    }
                ],
                "daily_compare": {
                    "summary": {
                        "added_count": 1,
                        "removed_count": 0,
                        "changed_count": 0,
                        "retained_count": 0,
                        "exposure_change_aud": 10,
                    }
                },
            }
            atomic_write_json(output_dir / "portfolio_automation_gate_v0_12.json", portfolio)
            atomic_write_json(output_dir / matches_board.recommendations_artifact, recommendations)
            comparison = generate_model_comparison(full_matches_raw_fixture())
            atomic_write_json(output_dir / MODEL_COMPARISON_JSON, comparison)
            write_model_comparison_pdf(comparison, output_dir / MODEL_COMPARISON_PDF)
            atomic_write_json(
                output_dir / "automation_preflight_latest.json",
                {"technical_preflight_ready": False, "automation_entry_ready": False, "blocking_reasons": ["stale latest preflight"]},
            )
            atomic_write_json(
                output_dir / "automation_preflight_test-run.json",
                {"technical_preflight_ready": True, "automation_entry_ready": False, "blocking_reasons": ["user has not authorized recurring automation"]},
            )
            atomic_write_json(output_dir / "raw_refresh_manifest_latest.json", {"raw_refresh_ready": False, "ready_required_target_count": 0, "required_target_count": 1})
            atomic_write_json(output_dir / "raw_refresh_manifest_test-run.json", {"raw_refresh_ready": True, "ready_required_target_count": 1, "required_target_count": 1})
            atomic_write_json(output_dir / "automation_safety_gate.json", {"automation_safety_ready": False, "blocking_reasons": ["stale latest safety"]})
            atomic_write_json(output_dir / "automation_safety_gate_test-run.json", {"automation_safety_ready": True, "blocking_reasons": []})
            atomic_write_json(
                output_dir / "tab_fifa_bankroll_plan_01012026.json",
                {
                    "time_adjusted_new_exposure_aud": 25,
                    "pdf_output_copy": str(output_dir / "01012026.pdf"),
                    "match_stakes": [
                        {
                            "match": "A v B",
                            "market": "Result",
                            "selection": "A",
                            "base_stake_aud": 10,
                            "time_adjusted_stake_aud": 25,
                            "time_adjusted_stake_unit": 0.625,
                        }
                    ],
                },
            )
            atomic_write_json(
                output_dir / "tab_fifa_bankroll_plan_01012026_test-run.json",
                {
                    "time_adjusted_new_exposure_aud": 120,
                    "pdf_output_copy": str(output_dir / "01012026_test-run.pdf"),
                    "match_stakes": [
                        {
                            "match": "A v B",
                            "market": "Result",
                            "selection": "A",
                            "base_stake_aud": 10,
                            "time_adjusted_stake_aud": 120,
                            "time_adjusted_stake_unit": 3.0,
                        }
                    ],
                },
            )
            manifest = {
                "run_id": "test-run",
                "started_at": "2026-01-01T00:00:00+00:00",
                "finished_at": "2026-01-01T00:00:02+00:00",
                "status": "ready_for_manual_report",
                "report_date": "01012026",
                "technical_automation_ready": True,
                "automation_entry_ready": False,
                "user_automation_authorized": False,
                "outputs": {
                    "raw_refresh_ready": True,
                    "automation_safety_ready": True,
                    "portfolio_automation_ready": True,
                    "pdf_time_adjusted_new_exposure_aud": 120,
                    "model_comparison_json": str(output_dir / MODEL_COMPARISON_JSON),
                    "model_comparison_pdf": str(output_dir / MODEL_COMPARISON_PDF),
                    "pdf_output_copy": str(output_dir / "01012026.pdf"),
                    "bankroll_plan": str(output_dir / "tab_fifa_bankroll_plan_01012026_test-run.json"),
                    "automation_preflight": str(output_dir / "automation_preflight_test-run.json"),
                    "raw_refresh_manifest": str(output_dir / "raw_refresh_manifest_test-run.json"),
                    "raw_refresh_diagnostics": str(output_dir / "raw_refresh_diagnostics_test-run.json"),
                    "raw_refresh_diagnostics_latest": str(output_dir / "raw_refresh_diagnostics_latest.json"),
                    "safety_gate": str(output_dir / "automation_safety_gate_test-run.json"),
                    "manifest": str(output_dir / "daily_report_manifest_test-run.json"),
                },
            }
            portfolio_compare = compare_portfolio_recommendations({"world_cup_matches": recommendations}, None)
            atomic_write_json(output_dir / "portfolio_daily_compare_latest.json", portfolio_compare)
            manifest["outputs"]["portfolio_daily_compare"] = str(output_dir / "portfolio_daily_compare_latest.json")
            manifest["outputs"]["portfolio_daily_compare_latest"] = str(output_dir / "portfolio_daily_compare_latest.json")
            manifest["outputs"]["portfolio_baseline"] = str(output_dir / "portfolio_report_baseline_test.json")
            manifest["outputs"]["portfolio_baseline_latest"] = str(output_dir / "portfolio_report_baseline_latest.json")
            manifest["outputs"]["portfolio_gate"] = str(output_dir / "portfolio_automation_gate_v0_12.json")
            manifest["outputs"]["latest_commit"] = str(output_dir / "latest_commit.json")
            manifest["outputs"]["report_index"] = str(output_dir / "report_index_test-run.json")
            manifest["outputs"]["report_index_latest"] = str(output_dir / "report_index_latest.json")
            manifest["outputs"]["report_index_report"] = str(output_dir / "report_index_test-run.md")
            manifest["outputs"]["report_index_report_latest"] = str(output_dir / "report_index_latest.md")
            manifest["outputs"]["report_index_pdf"] = str(output_dir / "report_index_test-run.pdf")
            manifest["outputs"]["report_index_pdf_latest"] = str(output_dir / "report_index_latest.pdf")
            manifest["outputs"]["report_intelligence"] = str(output_dir / "report_intelligence_test-run.json")
            manifest["outputs"]["report_intelligence_latest"] = str(output_dir / REPORT_INTELLIGENCE_JSON_LATEST)
            manifest["outputs"]["report_intelligence_report"] = str(output_dir / "report_intelligence_test-run.md")
            manifest["outputs"]["report_intelligence_report_latest"] = str(output_dir / REPORT_INTELLIGENCE_MD_LATEST)
            manifest["outputs"]["report_intelligence_pdf"] = str(output_dir / "report_intelligence_test-run.pdf")
            manifest["outputs"]["report_intelligence_pdf_latest"] = str(output_dir / REPORT_INTELLIGENCE_PDF_LATEST)
            atomic_write_json(output_dir / "automation_readiness_latest.json", {"status": "fixture"})
            atomic_write_text(output_dir / "automation_readiness_latest.md", "# fixture\n\n```mermaid\npie showData\n```")
            SimpleDocTemplate(str(output_dir / "automation_readiness_latest.pdf"), pagesize=A4).build(
                [Paragraph("Automation readiness fixture", getSampleStyleSheet()["Normal"])]
            )
            manifest["outputs"]["automation_readiness"] = str(output_dir / "automation_readiness_latest.json")
            manifest["outputs"]["automation_readiness_report"] = str(output_dir / "automation_readiness_latest.md")
            manifest["outputs"]["automation_readiness_pdf"] = str(output_dir / "automation_readiness_latest.pdf")
            candidate = build_automation_candidate()
            write_automation_candidate(output_dir, output_dir / AUTOMATION_CANDIDATE_LATEST, candidate=candidate)
            write_automation_candidate_report(output_dir, output_dir / AUTOMATION_CANDIDATE_REPORT_LATEST, candidate=candidate)
            write_automation_candidate_pdf(output_dir, output_dir / AUTOMATION_CANDIDATE_PDF_LATEST, candidate=candidate)
            manifest["outputs"]["automation_candidate"] = str(output_dir / AUTOMATION_CANDIDATE_LATEST)
            manifest["outputs"]["automation_candidate_report"] = str(output_dir / AUTOMATION_CANDIDATE_REPORT_LATEST)
            manifest["outputs"]["automation_candidate_pdf"] = str(output_dir / AUTOMATION_CANDIDATE_PDF_LATEST)
            db_path = output_dir / "tab_fifa_reports.sqlite3"
            stored = store_daily_run(db_path, manifest, output_dir)
            self.assertEqual(stored["recommendation_count"], 1)
            self.assertEqual(stored["model_comparison_count"], len(EXPECTED_MATCHES))
            self.assertEqual(stored["visual_chart_count"], 10)
            self.assertGreaterEqual(stored["evidence_summary"]["source_count"], 3)
            self.assertGreaterEqual(stored["evidence_summary"]["decision_count"], 1)
            self.assertEqual(latest_runs(db_path, limit=1)[0]["run_id"], "test-run")
            with connect_report_db(db_path) as conn:
                visual_count = conn.execute("SELECT COUNT(*) FROM visual_snapshots WHERE run_id = ?", ("test-run",)).fetchone()[0]
                self.assertEqual(visual_count, 10)
                visual_ids = {
                    row[0]
                    for row in conn.execute("SELECT chart_id FROM visual_snapshots WHERE run_id = ?", ("test-run",)).fetchall()
                }
                self.assertIn("stake_allocation", visual_ids)
                self.assertIn("odds_probability_edge", visual_ids)
                self.assertIn("model_consensus", visual_ids)
                self.assertIn("model_capability_coverage", visual_ids)
                board_diff_count = conn.execute("SELECT COUNT(*) FROM board_diffs WHERE run_id = ?", ("test-run",)).fetchone()[0]
                self.assertEqual(board_diff_count, 1)
                stored_stake = conn.execute("SELECT stake_aud FROM recommendations WHERE run_id = ? AND board_id = ?", ("test-run", "world_cup_matches")).fetchone()[0]
                self.assertEqual(stored_stake, 120)
                artifact_kinds = {
                    row[0]
                    for row in conn.execute("SELECT kind FROM artifacts WHERE run_id = ?", ("test-run",)).fetchall()
                }
                self.assertIn("portfolio_daily_compare", artifact_kinds)
                self.assertIn("portfolio_daily_compare_latest", artifact_kinds)
                self.assertIn("portfolio_baseline", artifact_kinds)
                self.assertIn("portfolio_baseline_latest", artifact_kinds)
                self.assertIn("portfolio_gate", artifact_kinds)
                self.assertIn("raw_refresh_diagnostics", artifact_kinds)
                self.assertIn("raw_refresh_diagnostics_latest", artifact_kinds)
                self.assertIn("report_index_report", artifact_kinds)
                self.assertIn("report_index_report_latest", artifact_kinds)
                self.assertIn("report_index_pdf", artifact_kinds)
                self.assertIn("report_index_pdf_latest", artifact_kinds)
                self.assertIn("report_intelligence", artifact_kinds)
                self.assertIn("report_intelligence_latest", artifact_kinds)
                self.assertIn("report_intelligence_report", artifact_kinds)
                self.assertIn("report_intelligence_report_latest", artifact_kinds)
                self.assertIn("report_intelligence_pdf", artifact_kinds)
                self.assertIn("report_intelligence_pdf_latest", artifact_kinds)
                self.assertIn("automation_readiness", artifact_kinds)
                self.assertIn("automation_readiness_report", artifact_kinds)
                self.assertIn("automation_readiness_pdf", artifact_kinds)
                self.assertIn("automation_candidate", artifact_kinds)
                self.assertIn("automation_candidate_report", artifact_kinds)
                self.assertIn("automation_candidate_pdf", artifact_kinds)
                self.assertIn("model_comparison_pdf", artifact_kinds)
                self.assertIn("latest_commit", artifact_kinds)
                summary_json = conn.execute("SELECT summary_json FROM report_runs WHERE run_id = ?", ("test-run",)).fetchone()[0]
                artifact_paths = "\n".join(
                    row[0]
                    for row in conn.execute("SELECT path FROM artifacts WHERE run_id = ?", ("test-run",)).fetchall()
                )
                self.assertNotIn(str(output_dir), summary_json)
                self.assertNotIn(str(output_dir), artifact_paths)
                self.assertTrue(audit_public_artifact_safety([db_path])["public_artifact_safety_ready"])
                self.assertGreater(conn.execute("SELECT COUNT(*) FROM source_logs WHERE run_id = ?", ("test-run",)).fetchone()[0], 0)
                self.assertGreater(conn.execute("SELECT COUNT(*) FROM audit_logs WHERE run_id = ?", ("test-run",)).fetchone()[0], 0)
                self.assertGreater(conn.execute("SELECT COUNT(*) FROM decision_records WHERE run_id = ?", ("test-run",)).fetchone()[0], 0)
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM manual_review_queue WHERE run_id = ?", ("test-run",)).fetchone()[0], 0)
            store_automation_run(
                db_path,
                {
                    "schema_version": 1,
                    "mode": "verify-only",
                    "verify_mode": "hermetic",
                    "status": "verified",
                    "exit_code": 0,
                    "started_at": "2026-01-01T00:00:03Z",
                    "finished_at": "2026-01-01T00:00:04Z",
                    "stdout_log": "tab_fifa_daily_20260101T000003Z-test.stdout.log",
                    "run_id": "test-run",
                    "raw_refresh_ready": True,
                    "my_bets_capture": {
                        "enabled": True,
                        "report_date": "01012026",
                        "capture_exit_code": 1,
                        "import_exit_code": 0,
                        "raw_text_seen": False,
                        "capture_log": str(output_dir / "work/private/tab_fifa/automation_run_logs/capture.log"),
                        "import_log": str(output_dir / "work/private/tab_fifa/automation_run_logs/import.log"),
                    },
                    "last_success": {"run_id": "test-run"},
                    "automation_readiness": {
                        "formal_report_publish_ready": False,
                        "recurring_automation_ready": False,
                    },
                },
            )
            report_index_path = output_dir / "report_index_test-run.json"
            report_index = write_report_index(
                db_path,
                output_dir,
                report_index_path,
                latest_commit={
                    "run_id": "test-run",
                    "report_date": "01012026",
                    "status": "ready_for_manual_report",
                    "technical_automation_ready": True,
                    "public_artifact_safety_ready": True,
                    "ready_required_boards": "5/5",
                },
            )
            self.assertEqual(report_index["latest_success_run_id"], "test-run")
            self.assertEqual(report_index["latest_commit"]["run_id"], "test-run")
            self.assertEqual(report_index["runs"][0]["counts"]["visual_charts"], 10)
            self.assertEqual(report_index["runs"][0]["counts"]["recommendations"], 1)
            self.assertEqual(report_index["runs"][0]["compare_summary"]["added_count"], 1)
            self.assertEqual(report_index["runs"][0]["artifact_refs"]["pdf_report"], "01012026.pdf")
            self.assertEqual(report_index["automation_run_count"], 1)
            self.assertEqual(report_index["automation_runs"][0]["verify_mode"], "hermetic")
            self.assertNotIn(str(output_dir), json.dumps(report_index, ensure_ascii=False))
            self.assertTrue(audit_public_artifact_safety([report_index_path])["public_artifact_safety_ready"])
            report_index_report_path = output_dir / "report_index_test-run.md"
            report_index_report = write_report_index_report(report_index, report_index_report_path)
            self.assertEqual(report_index_report["mermaid_blocks"], 6)
            report_index_markdown = report_index_report_path.read_text(encoding="utf-8")
            self.assertIn("## Visual Summary", report_index_markdown)
            self.assertIn("Run status mix", report_index_markdown)
            self.assertIn("New-vs-old changed items by run", report_index_markdown)
            self.assertIn("Automation runner status mix", report_index_markdown)
            self.assertIn("Automation Runner History", report_index_markdown)
            self.assertIn("verify-only", report_index_markdown)
            self.assertIn("hermetic", report_index_markdown)
            self.assertNotIn(str(output_dir), report_index_markdown)
            self.assertTrue(audit_public_artifact_safety([report_index_report_path])["public_artifact_safety_ready"])
            report_index_pdf_path = output_dir / "report_index_test-run.pdf"
            report_index_pdf = write_report_index_pdf(report_index, report_index_pdf_path)
            self.assertEqual(report_index_pdf["chart_count"], 7)
            self.assertEqual(report_index_pdf["extra_table_count"], 1)
            self.assertEqual(report_index_pdf["extra_detail_row_count"], 1)
            self.assertTrue(report_index_pdf_path.exists())
            self.assertTrue(audit_public_artifact_safety([report_index_pdf_path])["public_artifact_safety_ready"])
            report_intelligence = write_report_intelligence_bundle(
                output_dir,
                db_path,
                json_name="report_intelligence_test-run.json",
                markdown_name="report_intelligence_test-run.md",
                pdf_name="report_intelligence_test-run.pdf",
                latest_commit_override={
                    "run_id": "test-run",
                    "report_date": "01012026",
                    "status": "ready_for_manual_report",
                    "technical_automation_ready": True,
                    "public_artifact_safety_ready": True,
                    "ready_required_boards": "5/5",
                },
                report_index_override=report_index,
                readiness_override={
                    "formal_report_publish_ready": True,
                    "recurring_automation_ready": False,
                    "raw_refresh": {"ready": True},
                    "public_safety": {"output_safety_ready": True},
                    "technical_preflight": {"ready": True, "run_id": "test-run"},
                    "private_position_bootstrap": {"ready": True},
                },
                candidate_override={"status": "review_only"},
                timeline_override={
                    "summary": {
                        "day_count": 1,
                        "complete_day_count": 0,
                        "missing_analysis_day_count": 1,
                        "missing_report_day_count": 1,
                        "backfill_queue_count": 1,
                        "cadence_ready_for_all_days": False,
                        "formal_report_ready_for_all_days": False,
                    },
                    "cadence_rule": {
                        "min_analyses_per_day": 4,
                        "target_slots": ["00:00-05:00", "05:00-10:00"],
                    },
                    "days": [
                        {
                            "display_date": "01/01/2026",
                            "effective_analysis_count": 1,
                            "covered_slots": ["00:00-05:00"],
                            "missing_slots": ["05:00-10:00"],
                            "formal_report_exists": False,
                            "needs_backfill": True,
                            "backfill_reasons": ["有效分析 1/4", "Downloads 正式日报缺失"],
                        }
                    ],
                },
            )
            self.assertEqual(report_intelligence["executive_status"]["trusted_run_id"], "test-run")
            self.assertEqual(report_intelligence["recommendation_summary"]["buy_count"], 1)
            self.assertEqual(report_intelligence["timeline_health"]["slot_coverage"][0]["covered_day_count"], 1)
            self.assertEqual(report_intelligence["timeline_health"]["slot_heatmap"][0]["cells"][1]["status"], "missing")
            self.assertEqual(report_intelligence["automation_dashboard"]["ready_count"], 6)
            self.assertIn("公开盘口 raw", [row["label"] for row in report_intelligence["automation_dashboard"]["rows"]])
            self.assertEqual(report_intelligence["report_comparison"]["added_count"], 1)
            self.assertEqual(report_intelligence["artifacts"]["pdf"], "report_intelligence_test-run.pdf")
            self.assertEqual(report_intelligence["artifacts"]["pdf_summary"]["chart_count"], 11)
            self.assertEqual(report_intelligence["artifacts"]["pdf_summary"]["extra_table_count"], 6)
            report_intelligence_md = output_dir / "report_intelligence_test-run.md"
            report_intelligence_pdf = output_dir / "report_intelligence_test-run.pdf"
            report_intelligence_text = report_intelligence_md.read_text(encoding="utf-8")
            self.assertIn("Automation Dashboard", report_intelligence_text)
            self.assertIn("新旧报告对比与本地数据库", report_intelligence_text)
            self.assertIn("推荐下注板块", report_intelligence_text)
            self.assertIn("主动测试时间线热力图", report_intelligence_text)
            self.assertIn("主动测试历史趋势", report_intelligence_text)
            self.assertIn("00-05", report_intelligence_text)
            self.assertTrue(report_intelligence_pdf.exists())
            self.assertTrue(
                audit_public_artifact_safety(
                    [output_dir / "report_intelligence_test-run.json", report_intelligence_md, report_intelligence_pdf]
                )["public_artifact_safety_ready"]
            )
            shutil.copyfile(report_index_path, output_dir / "report_index_latest.json")
            shutil.copyfile(report_index_report_path, output_dir / "report_index_latest.md")
            shutil.copyfile(report_index_pdf_path, output_dir / "report_index_latest.pdf")
            shutil.copyfile(output_dir / "report_intelligence_test-run.json", output_dir / REPORT_INTELLIGENCE_JSON_LATEST)
            shutil.copyfile(report_intelligence_md, output_dir / REPORT_INTELLIGENCE_MD_LATEST)
            shutil.copyfile(report_intelligence_pdf, output_dir / REPORT_INTELLIGENCE_PDF_LATEST)

            maturity = write_automation_maturity_bundle(output_dir, db_path)
            self.assertEqual(maturity["artifacts"]["json"], AUTOMATION_MATURITY_JSON_LATEST)
            self.assertEqual(maturity["artifacts"]["markdown"], AUTOMATION_MATURITY_MD_LATEST)
            self.assertEqual(maturity["artifacts"]["pdf"], AUTOMATION_MATURITY_PDF_LATEST)
            self.assertEqual(maturity["artifacts"]["pdf_summary"]["chart_count"], 5)
            self.assertEqual(maturity["artifacts"]["pdf_summary"]["extra_table_count"], 3)
            self.assertEqual(maturity["storage"]["status"], "stored")
            self.assertIn("old_new_compare", maturity)
            self.assertIn("automation_recovery_playbook", maturity)
            self.assertTrue(any(item["priority"] == "P0" for item in maturity["automation_recovery_playbook"]))
            self.assertIn("public_raw_crawler", [row["requirement_id"] for row in maturity["rows"]])
            self.assertIn("old_new_compare", [row["requirement_id"] for row in maturity["rows"]])
            self.assertIn("open_source_models", [row["requirement_id"] for row in maturity["rows"]])
            self.assertFalse(maturity["executive_status"]["automation_ready"])
            self.assertGreaterEqual(maturity["summary"]["required_count"], 12)
            self.assertGreaterEqual(maturity["summary"]["required_ready_count"], 5)
            maturity_md = (output_dir / AUTOMATION_MATURITY_MD_LATEST).read_text(encoding="utf-8")
            self.assertIn("Automation 恢复 Playbook", maturity_md)
            self.assertIn("新旧成熟度", maturity_md)
            self.assertIn("不自动下注", maturity_md)
            with sqlite3.connect(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM automation_maturity_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / AUTOMATION_MATURITY_JSON_LATEST,
                        output_dir / AUTOMATION_MATURITY_MD_LATEST,
                        output_dir / AUTOMATION_MATURITY_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": True,
                    "status": "ready",
                    "ready_required_target_count": 5,
                    "required_target_count": 5,
                    "blocker_codes": [],
                    "targets": [
                        {"board_id": "matches", "name": "2026 World Cup Matches", "status": "ready", "raw_fresh": True, "raw_valid": True, "driver_configured": True},
                        {"board_id": "futures", "name": "2026 World Cup Futures", "status": "ready", "raw_fresh": True, "raw_valid": True, "driver_configured": True},
                    ],
                },
            )
            raw_recovery = write_raw_refresh_recovery_bundle(output_dir)
            self.assertEqual(raw_recovery["artifacts"]["json"], RAW_REFRESH_RECOVERY_JSON_LATEST)
            self.assertEqual(raw_recovery["artifacts"]["markdown"], RAW_REFRESH_RECOVERY_MD_LATEST)
            self.assertEqual(raw_recovery["artifacts"]["pdf"], RAW_REFRESH_RECOVERY_PDF_LATEST)
            self.assertEqual(raw_recovery["artifacts"]["pdf_summary"]["chart_count"], 6)
            self.assertEqual(raw_recovery["artifacts"]["pdf_summary"]["extra_table_count"], 7)
            self.assertIn("old_new_compare", raw_recovery)
            self.assertIn("board_failure_count", raw_recovery["summary"])
            self.assertIn("board_recovery_matrix_count", raw_recovery["summary"])
            self.assertIn("board_recovery_matrix", raw_recovery)
            self.assertTrue(any(row["automation_action"] in {"monitor", "auto_retry_read_only"} for row in raw_recovery["board_recovery_matrix"]))
            self.assertIn("新旧恢复变化", (output_dir / RAW_REFRESH_RECOVERY_MD_LATEST).read_text(encoding="utf-8"))
            self.assertIn("单板失败隔离", (output_dir / RAW_REFRESH_RECOVERY_MD_LATEST).read_text(encoding="utf-8"))
            self.assertIn("板块级恢复矩阵", (output_dir / RAW_REFRESH_RECOVERY_MD_LATEST).read_text(encoding="utf-8"))
            self.assertIn("raw_refresh_recovery_dashboard", raw_recovery["mode"])
            self.assertIn("safe_no_latest_publish", json.dumps(raw_recovery, ensure_ascii=False))
            self.assertTrue(any(row["phase_id"] == "safe_backfill" for row in raw_recovery["phase_rows"]))
            self.assertTrue(any(row["mode"] in {"standard_read_only_refresh", "safe_no_latest_publish"} for row in raw_recovery["next_retry_plan"]))
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / RAW_REFRESH_RECOVERY_JSON_LATEST,
                        output_dir / RAW_REFRESH_RECOVERY_MD_LATEST,
                        output_dir / RAW_REFRESH_RECOVERY_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            atomic_write_json(
                output_dir / "active_timeline_latest.json",
                {
                    "cadence_rule": {
                        "target_slots": ["00:00-05:00", "05:00-10:00", "10:00-15:00"],
                        "min_analyses_per_day": 4,
                    },
                    "summary": {
                        "day_count": 2,
                        "complete_day_count": 0,
                        "missing_analysis_day_count": 2,
                        "missing_report_day_count": 2,
                        "backfill_queue_count": 2,
                        "formal_report_ready_for_all_days": False,
                        "cadence_ready_for_all_days": False,
                    },
                    "days": [
                        {
                            "report_date": "01012026",
                            "display_date": "01/01/2026",
                            "effective_analysis_count": 1,
                            "covered_slots": ["00:00-05:00"],
                            "missing_slots": ["05:00-10:00", "10:00-15:00"],
                            "formal_report_exists": False,
                            "needs_backfill": True,
                            "backfill_reasons": ["有效分析 1/4", "Downloads 正式日报缺失"],
                            "latest_status": "blocked_by_gate",
                        },
                        {
                            "report_date": "02012026",
                            "display_date": "02/01/2026",
                            "effective_analysis_count": 0,
                            "covered_slots": [],
                            "missing_slots": ["00:00-05:00", "05:00-10:00", "10:00-15:00"],
                            "formal_report_exists": False,
                            "needs_backfill": True,
                            "backfill_reasons": ["有效分析 0/4", "Downloads 正式日报缺失"],
                            "latest_status": "missing",
                        },
                    ],
                    "backfill_queue": [
                        {
                            "repair_rank": 1,
                            "report_date": "02012026",
                            "display_date": "02/01/2026",
                            "priority_score": 140,
                            "reason": "有效分析 0/4；Downloads 正式日报缺失",
                            "priority_reason": "缺失时段 3/5；有效分析 0/4；日报缺失；latest=missing",
                            "mode": "safe_no_latest_publish",
                        }
                    ],
                },
            )
            atomic_write_json(
                output_dir / "active_backfill_latest.json",
                {
                    "status": "blocked_by_raw_refresh",
                    "partial_daily_research": {
                        "ready": True,
                        "status": "ready_research_only",
                        "report_date": "01012026",
                        "generated_at": "2026-01-01T10:00:00+11:00",
                        "execution_allowed": False,
                        "current_executable_new_stake_aud": 0,
                        "partial_successful_board_count": 3,
                        "partial_attempted_board_count": 5,
                        "unavailable_board_count": 2,
                        "freshness_status": "fresh_research_only",
                        "fresh_within_sla": True,
                        "pdf": PARTIAL_DAILY_RESEARCH_PDF_LATEST,
                        "dated_pdf": "01012026_partial_daily_research.pdf",
                    },
                },
            )
            active_timeline_report = write_active_timeline_report_bundle(output_dir)
            self.assertEqual(active_timeline_report["artifacts"]["json"], ACTIVE_TIMELINE_REPORT_JSON_LATEST)
            self.assertEqual(active_timeline_report["artifacts"]["markdown"], ACTIVE_TIMELINE_REPORT_MD_LATEST)
            self.assertEqual(active_timeline_report["artifacts"]["pdf"], ACTIVE_TIMELINE_REPORT_PDF_LATEST)
            self.assertEqual(active_timeline_report["artifacts"]["pdf_summary"]["chart_count"], 5)
            self.assertEqual(active_timeline_report["artifacts"]["pdf_summary"]["extra_table_count"], 5)
            self.assertIn("active_timeline_dashboard", active_timeline_report["mode"])
            self.assertIn("active_timeline_report_", active_timeline_report["snapshot_id"])
            self.assertIn("safe_no_latest_publish", json.dumps(active_timeline_report, ensure_ascii=False))
            self.assertEqual(active_timeline_report["partial_daily_research"]["status"], "ready_research_only")
            self.assertFalse(active_timeline_report["partial_daily_research"]["execution_allowed"])
            self.assertEqual(active_timeline_report["summary"]["partial_daily_research_new_stake_aud"], 0)
            self.assertEqual(active_timeline_report["backfill_recovery_plan"]["status"], "ready_to_backfill")
            self.assertEqual(active_timeline_report["backfill_recovery_plan"]["max_safe_backfill_runs"], 1)
            self.assertTrue(active_timeline_report["summary"]["safe_to_backfill_now"])
            self.assertEqual(active_timeline_report["storage"]["status"], "stored")
            self.assertTrue(active_timeline_report["backfill_guard"]["raw_ready"])
            timeline_md = (output_dir / ACTIVE_TIMELINE_REPORT_MD_LATEST).read_text(encoding="utf-8")
            self.assertIn("补缺恢复计划", timeline_md)
            self.assertIn("研究诊断日报补写", timeline_md)
            self.assertIn("ready_research_only", timeline_md)
            self.assertIn("AUD 0", timeline_md)
            with connect_report_db(output_dir / "tab_fifa_reports.sqlite3") as conn:
                rows = conn.execute("SELECT * FROM active_timeline_report_snapshots").fetchall()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["recovery_plan_status"], "ready_to_backfill")
                self.assertEqual(rows[0]["safe_to_backfill_now"], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / ACTIVE_TIMELINE_REPORT_JSON_LATEST,
                        output_dir / ACTIVE_TIMELINE_REPORT_MD_LATEST,
                        output_dir / ACTIVE_TIMELINE_REPORT_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-12T07:44:00Z",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "expected_boards": [
                        {
                            "refresh_board_id": "matches",
                            "board": "2026 World Cup Matches",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"}],
                            "automation_decision": "refresh_allowed",
                        },
                        {
                            "refresh_board_id": "futures",
                            "board": "2026 World Cup Futures",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Futures", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures"}],
                            "automation_decision": "refresh_allowed",
                        },
                    ],
                    "observed_world_cup_links": [
                        {"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"},
                        {"text": "2026 World Cup Futures", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures"},
                        {
                            "text": "World Cup Group D (USA/TUR/PAR/AUS)",
                            "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Group%20Betting/matches/World%20Cup%20Group%20D%20(USA~2FTUR~2FPAR~2FAUS)",
                        },
                    ],
                },
            )
            write_live_board_discovery_bundle(output_dir)
            available_strategy = write_available_board_strategy_bundle(output_dir, db_path)
            self.assertEqual(available_strategy["artifacts"]["json"], AVAILABLE_BOARD_STRATEGY_JSON_LATEST)
            self.assertEqual(available_strategy["storage"]["status"], "stored")
            with connect_report_db(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO recommendations(
                        run_id, board_id, board_name, rank, event_name, market, selection,
                        odds, probability, expected_value, stake_aud, action, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "test-run",
                        "world_cup_australia_markets",
                        "2026 World Cup Australia Markets",
                        2,
                        "AUS Group Match Wins",
                        "AUS Group Match Wins",
                        "Over 1.5",
                        2.2,
                        0.55,
                        0.21,
                        25,
                        "buy",
                        json.dumps({"edge": 0.095}, ensure_ascii=False),
                    ),
                )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            atomic_write_json(
                output_dir / "automation_preflight_latest.json",
                {
                    "report_date": "01012026",
                    "technical_preflight_ready": False,
                    "private_output_mode": True,
                },
            )
            position_monitor = write_position_monitor_bundle(output_dir, db_path)
            self.assertEqual(position_monitor["artifacts"]["json"], POSITION_MONITOR_JSON_LATEST)
            self.assertEqual(position_monitor["artifacts"]["markdown"], POSITION_MONITOR_MD_LATEST)
            self.assertEqual(position_monitor["artifacts"]["pdf"], POSITION_MONITOR_PDF_LATEST)
            self.assertEqual(position_monitor["artifacts"]["pdf_summary"]["chart_count"], 4)
            self.assertEqual(position_monitor["artifacts"]["pdf_summary"]["extra_table_count"], 3)
            self.assertEqual(position_monitor["storage"]["status"], "stored")
            self.assertIn("position_monitor_dashboard", position_monitor["mode"])
            self.assertEqual(position_monitor["summary"]["report_date"], "01012026")
            self.assertIn("TAB 专用已登录 profile", position_monitor["executive_status"]["recommended_next_action"])
            self.assertEqual(position_monitor["summary"]["public_visible_balance"], "account-update-pending")
            self.assertEqual(position_monitor["summary"]["public_visible_open_exposure"], "account-update-pending")
            self.assertEqual(position_monitor["summary"]["public_visible_realized_roi"], "account-update-pending")
            self.assertIn("preflight_status", position_monitor["summary"])
            self.assertIn("preflight_blocking_reason", position_monitor["summary"])
            self.assertIn("credential_policy", position_monitor["summary"])
            self.assertIn("automation_boundary", position_monitor["summary"])
            self.assertIn("private_preflight", position_monitor)
            self.assertTrue(any(row["item_id"] == "private_preflight" for row in position_monitor["monitor_rows"]))
            self.assertFalse(position_monitor["summary"]["snapshot_ready"])
            self.assertIn("本机私有存储", json.dumps(position_monitor, ensure_ascii=False))
            self.assertNotIn("work/private", json.dumps(position_monitor, ensure_ascii=False))
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM position_monitor_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / POSITION_MONITOR_JSON_LATEST,
                        output_dir / POSITION_MONITOR_MD_LATEST,
                        output_dir / POSITION_MONITOR_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            goal_traceability = write_goal_traceability_bundle(output_dir, db_path)
            self.assertEqual(goal_traceability["artifacts"]["json"], GOAL_TRACEABILITY_JSON_LATEST)
            self.assertEqual(goal_traceability["artifacts"]["markdown"], GOAL_TRACEABILITY_MD_LATEST)
            self.assertEqual(goal_traceability["artifacts"]["pdf"], GOAL_TRACEABILITY_PDF_LATEST)
            self.assertEqual(goal_traceability["artifacts"]["pdf_summary"]["chart_count"], 5)
            self.assertEqual(goal_traceability["artifacts"]["pdf_summary"]["extra_table_count"], 3)
            self.assertEqual(goal_traceability["storage"]["status"], "stored")
            self.assertIn("goal_traceability_dashboard", goal_traceability["mode"])
            self.assertIn("github_models", [row["requirement_id"] for row in goal_traceability["rows"]])
            self.assertIn("business_homepage", [row["requirement_id"] for row in goal_traceability["rows"]])
            self.assertIn("old_new_report_compare", [row["requirement_id"] for row in goal_traceability["rows"]])
            self.assertIn("position_roi", [row["requirement_id"] for row in goal_traceability["rows"]])
            self.assertFalse(goal_traceability["executive_status"]["goal_ready"])
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM goal_traceability_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / GOAL_TRACEABILITY_JSON_LATEST,
                        output_dir / GOAL_TRACEABILITY_MD_LATEST,
                        output_dir / GOAL_TRACEABILITY_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            atomic_write_json(
                output_dir / "latest_commit.json",
                {
                    "run_id": "test-run",
                    "report_date": "01012026",
                    "status": "ready_for_manual_report",
                    "public_artifact_safety_ready": True,
                    "time_adjusted_new_exposure_aud": 120,
                },
            )
            atomic_write_json(
                output_dir / "automation_readiness_latest.json",
                {
                    "formal_report_publish_ready": True,
                    "recurring_automation_ready": False,
                    "raw_refresh": {"ready": True},
                    "technical_preflight": {"run_id": "test-run", "technical_preflight_ready": True},
                    "private_position_bootstrap": {"ready": True},
                },
            )
            recommendation_operations = write_recommendation_operations_bundle(output_dir, db_path)
            self.assertEqual(recommendation_operations["artifacts"]["json"], RECOMMENDATION_OPERATIONS_JSON_LATEST)
            self.assertEqual(recommendation_operations["artifacts"]["markdown"], RECOMMENDATION_OPERATIONS_MD_LATEST)
            self.assertEqual(recommendation_operations["artifacts"]["pdf"], RECOMMENDATION_OPERATIONS_PDF_LATEST)
            self.assertEqual(recommendation_operations["artifacts"]["pdf_summary"]["chart_count"], 11)
            self.assertEqual(recommendation_operations["artifacts"]["pdf_summary"]["extra_table_count"], 27)
            self.assertEqual(recommendation_operations["storage"]["status"], "stored")
            self.assertIn("recommendation_operations_dashboard", recommendation_operations["mode"])
            self.assertTrue(recommendation_operations["summary"]["execution_allowed"])
            self.assertEqual(recommendation_operations["summary"]["candidate_count"], 1)
            self.assertEqual(recommendation_operations["summary"]["all_candidate_count_before_scope"], 2)
            self.assertEqual(recommendation_operations["summary"]["excluded_unavailable_candidate_count"], 1)
            self.assertEqual(recommendation_operations["summary"]["excluded_unavailable_stake_aud"], 25)
            self.assertIn("板块缺失排除", recommendation_operations["summary"]["live_board_scope_distribution"])
            self.assertEqual(len(recommendation_operations["excluded_unavailable_rows"]), 1)
            self.assertEqual(recommendation_operations["excluded_unavailable_rows"][0]["board_id"], "world_cup_australia_markets")
            self.assertEqual(recommendation_operations["excluded_unavailable_rows"][0]["action"], "排除-板块缺失")
            self.assertEqual(recommendation_operations["excluded_unavailable_rows"][0]["executable_stake_aud"], 0.0)
            self.assertEqual(recommendation_operations["summary"]["research_candidate_stake_aud"], 120)
            self.assertEqual(recommendation_operations["summary"]["executable_new_stake_aud"], 120)
            self.assertEqual(recommendation_operations["summary"]["average_arbitrage_rate"], 0.12)
            self.assertGreater(recommendation_operations["summary"]["max_risk_of_ruin"], 0)
            self.assertIn("edge_threshold_pass_count", recommendation_operations["summary"])
            self.assertIn("average_edge_threshold_gap", recommendation_operations["summary"])
            self.assertIn("high_risk_of_ruin_count", recommendation_operations["summary"])
            self.assertIn("expected_profit_at_research_stake_aud", recommendation_operations["summary"])
            self.assertIn("average_expected_profit_per_100_aud", recommendation_operations["summary"])
            self.assertIn("ror_review_count", recommendation_operations["summary"])
            self.assertIn("value_signal_pass_count", recommendation_operations["summary"])
            self.assertIn("positive_arbitrage_count", recommendation_operations["summary"])
            self.assertIn("price_buffer_positive_count", recommendation_operations["summary"])
            self.assertIn("low_or_medium_ror_count", recommendation_operations["summary"])
            self.assertEqual(recommendation_operations["summary"]["analysis_basis_complete_count"], 1)
            self.assertIn("analysis_data_gap_row_count", recommendation_operations["summary"])
            self.assertGreater(recommendation_operations["summary"]["pre_bet_checklist_item_count"], 0)
            self.assertIn("model_calibrated_count", recommendation_operations["summary"])
            self.assertIn("model_high_divergence_count", recommendation_operations["summary"])
            self.assertIn("model_reverse_consensus_count", recommendation_operations["summary"])
            self.assertIn("model_review_required_count", recommendation_operations["summary"])
            self.assertIn("average_price_drift_tolerance_pct", recommendation_operations["summary"])
            self.assertIn("average_stake_to_cap_ratio", recommendation_operations["summary"])
            self.assertIn("average_risk_adjusted_value_score", recommendation_operations["summary"])
            self.assertIn("market_funding", recommendation_operations["summary"])
            self.assertIn("average_market_funding_tendency_score", recommendation_operations["summary"])
            self.assertIn("total_funds_proxy_aud", recommendation_operations["summary"])
            self.assertIn("net_funds_proxy_aud", recommendation_operations["summary"])
            self.assertIn("turnover_proxy_aud", recommendation_operations["summary"])
            self.assertIn("average_liquidity_score", recommendation_operations["summary"])
            self.assertIn("average_market_depth_score", recommendation_operations["summary"])
            self.assertIn("average_daily_line_move_float_rate", recommendation_operations["summary"])
            self.assertEqual(recommendation_operations["summary"]["market_funding_row_count"], 1)
            self.assertGreater(recommendation_operations["summary"]["average_market_funding_tendency_score"], 0)
            self.assertEqual(
                recommendation_operations["summary"]["market_funding"]["data_status"],
                "proxy_inferred_from_public_odds",
            )
            self.assertIn("portfolio_risk", recommendation_operations["summary"])
            self.assertIn("portfolio_risk_of_ruin", recommendation_operations["summary"])
            self.assertIn("portfolio_expected_profit_aud", recommendation_operations["summary"])
            self.assertIn("portfolio_worst_case_new_loss_aud", recommendation_operations["summary"])
            self.assertEqual(recommendation_operations["summary"]["portfolio_risk"]["declared_committed_reference_aud"], 2000.0)
            self.assertGreaterEqual(recommendation_operations["summary"]["portfolio_risk"]["budget_floor_headroom_aud"], 0)
            self.assertGreater(recommendation_operations["summary"]["portfolio_risk_of_ruin"], 0)
            self.assertEqual(recommendation_operations["calculation_policy"]["template_reference"], "football_betting_analysis_ABC_template.xlsx")
            self.assertIn("template_read_status", recommendation_operations["calculation_policy"])
            self.assertIn("template_evidence_digest", recommendation_operations["calculation_policy"])
            self.assertIn("template_formula_count", recommendation_operations["calculation_policy"])
            self.assertIn("template_evidence_terms", recommendation_operations["calculation_policy"])
            self.assertIn("template_decision_rules", recommendation_operations["calculation_policy"])
            self.assertIn("template_analysis_materials", recommendation_operations["calculation_policy"])
            self.assertIn("excel_reference_profile", recommendation_operations["calculation_policy"])
            self.assertIn("extracted_template_controls", recommendation_operations["calculation_policy"])
            self.assertIn("price_drift_tolerance_formula", recommendation_operations["calculation_policy"])
            self.assertIn("stake_cap_usage_formula", recommendation_operations["calculation_policy"])
            self.assertIn("risk_adjusted_value_formula", recommendation_operations["calculation_policy"])
            self.assertIn("portfolio_risk_formula", recommendation_operations["calculation_policy"])
            self.assertIn("market_funding_tendency_formula", recommendation_operations["calculation_policy"])
            self.assertIn("market_funding_proxy_formula", recommendation_operations["calculation_policy"])
            self.assertIn("probability_engine_framework", recommendation_operations["calculation_policy"])
            self.assertIn("probability_engine_formula", recommendation_operations["calculation_policy"])
            self.assertIn("data_leakage_control_rule", recommendation_operations["calculation_policy"])
            self.assertIn("budget_reference", recommendation_operations["calculation_policy"])
            self.assertIn("probability_engine", recommendation_operations)
            self.assertEqual(recommendation_operations["probability_engine"]["status"], "framework_mapped_partial_implementation")
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_module_count"], 10)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_leakage_control_count"], 6)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_metric_count"], 6)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_objective_module_count"], 8)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_ml_model_count"], 7)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_technical_rule_count"], 5)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_scoring_model_count"], 2)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_fundamental_layer_count"], 4)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_tournament_rule_count"], 8)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_prediction_contract_field_count"], 9)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_prediction_contract_ready_count"], 6)
            self.assertGreaterEqual(recommendation_operations["summary"]["probability_engine_backtest_control_count"], 7)
            self.assertIn("objective_modules", recommendation_operations["probability_engine"])
            self.assertIn("ml_models", recommendation_operations["probability_engine"])
            self.assertIn("technical_rules", recommendation_operations["probability_engine"])
            self.assertIn("scoring_models", recommendation_operations["probability_engine"])
            self.assertIn("fundamental_layers", recommendation_operations["probability_engine"])
            self.assertIn("tournament_rule_requirements", recommendation_operations["probability_engine"])
            self.assertIn("prediction_contract_fields", recommendation_operations["probability_engine"])
            self.assertIn("calibration_backtest_controls", recommendation_operations["probability_engine"])
            self.assertIn("accepted_modules", recommendation_operations["calculation_policy"]["excel_reference_profile"])
            self.assertIn("价值套利率", recommendation_operations["calculation_policy"]["arbitrage_rate_formula"])
            self.assertTrue(any("赛前10分钟清单" in item for item in recommendation_operations["calculation_policy"]["judgment_basis"]))
            self.assertTrue(any("市场资金层" in item for item in recommendation_operations["calculation_policy"]["judgment_basis"]))
            self.assertTrue(any("概率工程层" in item for item in recommendation_operations["calculation_policy"]["judgment_basis"]))
            self.assertTrue(any("penaltyblog" in item for item in recommendation_operations["calculation_policy"]["judgment_basis"]))
            self.assertEqual(recommendation_operations["recommendation_rows"][0]["action"], "买入")
            self.assertEqual(recommendation_operations["recommendation_rows"][0]["arbitrage_rate"], 0.12)
            self.assertGreater(recommendation_operations["recommendation_rows"][0]["risk_of_ruin"], 0)
            self.assertIn("edge_threshold", recommendation_operations["recommendation_rows"][0])
            self.assertIn("edge_threshold_gap", recommendation_operations["recommendation_rows"][0])
            self.assertIn("edge_quality", recommendation_operations["recommendation_rows"][0])
            self.assertIn("risk_of_ruin_grade", recommendation_operations["recommendation_rows"][0])
            self.assertIn("risk_drivers", recommendation_operations["recommendation_rows"][0])
            self.assertIn("discounted_kelly_fraction", recommendation_operations["recommendation_rows"][0])
            self.assertIn("minimum_acceptable_odds", recommendation_operations["recommendation_rows"][0])
            self.assertIn("expected_profit_per_100_aud", recommendation_operations["recommendation_rows"][0])
            self.assertIn("price_drift_tolerance_pct", recommendation_operations["recommendation_rows"][0])
            self.assertIn("stake_to_cap_ratio", recommendation_operations["recommendation_rows"][0])
            self.assertIn("kelly_safety_margin", recommendation_operations["recommendation_rows"][0])
            self.assertIn("risk_adjusted_value_score", recommendation_operations["recommendation_rows"][0])
            self.assertIn("value_signal", recommendation_operations["recommendation_rows"][0])
            self.assertIn("market_funding", recommendation_operations["recommendation_rows"][0])
            self.assertIn("market_funding_tendency_score", recommendation_operations["recommendation_rows"][0]["market_funding"])
            self.assertIn("total_funds_proxy_aud", recommendation_operations["recommendation_rows"][0]["market_funding"])
            self.assertIn("net_funds_proxy_aud", recommendation_operations["recommendation_rows"][0]["market_funding"])
            self.assertIn("turnover_proxy_aud", recommendation_operations["recommendation_rows"][0]["market_funding"])
            self.assertIn("liquidity_score", recommendation_operations["recommendation_rows"][0]["market_funding"])
            self.assertIn("market_depth_score", recommendation_operations["recommendation_rows"][0]["market_funding"])
            self.assertIn("daily_line_move_float_rate", recommendation_operations["recommendation_rows"][0]["market_funding"])
            self.assertEqual(
                recommendation_operations["recommendation_rows"][0]["market_funding"]["data_status"],
                "proxy_inferred_from_public_odds",
            )
            self.assertIn("model_calibration", recommendation_operations["recommendation_rows"][0])
            self.assertIn("consistency_label", recommendation_operations["recommendation_rows"][0]["model_calibration"])
            self.assertIn("review_action", recommendation_operations["recommendation_rows"][0]["model_calibration"])
            self.assertIn("decision_metric_pack", recommendation_operations["recommendation_rows"][0])
            self.assertIn("edge", recommendation_operations["recommendation_rows"][0]["decision_metric_pack"])
            self.assertIn("arbitrage_rate", recommendation_operations["recommendation_rows"][0]["decision_metric_pack"])
            self.assertIn("risk_of_ruin", recommendation_operations["recommendation_rows"][0]["decision_metric_pack"])
            self.assertIn("模型价值率", recommendation_operations["recommendation_rows"][0]["decision_metric_pack"]["arbitrage_rate"]["decision_use"])
            self.assertIn("不自动下注", recommendation_operations["recommendation_rows"][0]["decision_metric_pack"]["manual_use_only"])
            self.assertIn("analysis_basis", recommendation_operations["recommendation_rows"][0])
            self.assertIn("probability_value_basis", recommendation_operations["recommendation_rows"][0]["analysis_basis"])
            self.assertIn("price_execution_basis", recommendation_operations["recommendation_rows"][0]["analysis_basis"])
            self.assertIn("risk_control_basis", recommendation_operations["recommendation_rows"][0]["analysis_basis"])
            self.assertIn("source_basis", recommendation_operations["recommendation_rows"][0]["analysis_basis"])
            self.assertIn("data_gaps", recommendation_operations["recommendation_rows"][0]["analysis_basis"])
            self.assertIn("pre_bet_checklist", recommendation_operations["recommendation_rows"][0]["analysis_basis"])
            self.assertIn("不作为自动下注授权", recommendation_operations["recommendation_rows"][0]["analysis_basis"]["decision_use"])
            self.assertIn("decision_diagnostics", recommendation_operations["recommendation_rows"][0])
            self.assertIn("minimum_acceptable_odds", recommendation_operations["recommendation_rows"][0]["decision_diagnostics"])
            self.assertIn("ror_status", recommendation_operations["recommendation_rows"][0]["decision_diagnostics"])
            self.assertIn("price_drift_tolerance_pct", recommendation_operations["recommendation_rows"][0]["decision_diagnostics"])
            self.assertIn("stake_to_cap_ratio", recommendation_operations["recommendation_rows"][0]["decision_diagnostics"])
            self.assertIn("kelly_safety_margin", recommendation_operations["recommendation_rows"][0]["decision_diagnostics"])
            self.assertIn("risk_adjusted_value_score", recommendation_operations["recommendation_rows"][0]["decision_diagnostics"])
            self.assertIn("value_signal", recommendation_operations["recommendation_rows"][0]["decision_diagnostics"])
            self.assertIn("概率", recommendation_operations["recommendation_rows"][0]["reason"])
            self.assertIn("Edge门槛", recommendation_operations["recommendation_rows"][0]["reason"])
            self.assertIn("Risk of ruin", recommendation_operations["recommendation_rows"][0]["reason"])
            self.assertIn("赔率执行底线", recommendation_operations["recommendation_rows"][0]["reason"])
            self.assertIn("价值信号", recommendation_operations["recommendation_rows"][0]["reason"])
            self.assertIn("价格容忍度", recommendation_operations["recommendation_rows"][0]["reason"])
            self.assertIn("市场资金分析", recommendation_operations["recommendation_rows"][0]["reason"])
            self.assertIn("CLV/ROI复盘", recommendation_operations["recommendation_rows"][0]["reason"])
            self.assertIn("market_funding_analysis", recommendation_operations)
            self.assertEqual(recommendation_operations["market_funding_analysis"]["summary"]["funding_row_count"], 1)
            recommendation_operations_md = (output_dir / RECOMMENDATION_OPERATIONS_MD_LATEST).read_text(encoding="utf-8")
            self.assertIn("Excel模板吸收范围", recommendation_operations_md)
            self.assertIn("Excel模板证据增强", recommendation_operations_md)
            self.assertIn("Excel决策规则", recommendation_operations_md)
            self.assertIn("判断依据来源", recommendation_operations_md)
            self.assertIn("Excel赛前控制映射", recommendation_operations_md)
            self.assertIn("逐行判断依据包", recommendation_operations_md)
            self.assertIn("资料缺口", recommendation_operations_md)
            self.assertIn("赛前复核清单", recommendation_operations_md)
            self.assertIn("Edge/RoR 决策诊断", recommendation_operations_md)
            self.assertIn("三指标解释包", recommendation_operations_md)
            self.assertIn("组合风险与预算压力", recommendation_operations_md)
            self.assertIn("模型共识校准", recommendation_operations_md)
            self.assertIn("概率工程吸收", recommendation_operations_md)
            self.assertIn("赛制模拟与预测合约", recommendation_operations_md)
            self.assertIn("Dixon-Coles", recommendation_operations_md)
            self.assertIn("Bayesian Poisson", recommendation_operations_md)
            self.assertIn("Monte Carlo", recommendation_operations_md)
            self.assertIn("48队 / 12组 / 每组4队", recommendation_operations_md)
            self.assertIn("小组前二 + 8个最佳第三晋级32强", recommendation_operations_md)
            self.assertIn("prediction_timestamp", recommendation_operations_md)
            self.assertIn("odds_phase", recommendation_operations_md)
            self.assertIn("Settled position import", recommendation_operations_md)
            self.assertIn("防泄漏/可复现要求", recommendation_operations_md)
            self.assertIn("Brier score", recommendation_operations_md)
            self.assertIn("opening/closing odds store", recommendation_operations_md)
            self.assertIn("目标与指标落地", recommendation_operations_md)
            self.assertIn("机器学习候选模型", recommendation_operations_md)
            self.assertIn("Logistic Regression", recommendation_operations_md)
            self.assertIn("XGBoost / LightGBM", recommendation_operations_md)
            self.assertIn("技术面与模型公式", recommendation_operations_md)
            self.assertIn("RAEV = 模型认为的胜利概率", recommendation_operations_md)
            self.assertIn("CLV = 下注时赔率是否优于 closing odds", recommendation_operations_md)
            self.assertIn("Poisson(lambda_home)", recommendation_operations_md)
            self.assertIn("Dixon-Coles-Adjusted Poisson Model", recommendation_operations_md)
            self.assertIn("基本面分析层", recommendation_operations_md)
            self.assertIn("Team Level", recommendation_operations_md)
            self.assertIn("Player Level", recommendation_operations_md)
            self.assertIn("市场资金分析", recommendation_operations_md)
            self.assertIn("总资金代理", recommendation_operations_md)
            self.assertIn("日均盘口变动浮动率", recommendation_operations_md)
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM recommendation_operation_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / RECOMMENDATION_OPERATIONS_JSON_LATEST,
                        output_dir / RECOMMENDATION_OPERATIONS_MD_LATEST,
                        output_dir / RECOMMENDATION_OPERATIONS_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            blocked_rows = apply_recommendation_execution_gate(
                recommendation_operations["research_rows_before_gate"],
                execution_allowed=False,
                gate_message="测试门禁阻塞。",
            )
            self.assertEqual(blocked_rows[0]["action"], "暂停执行")
            self.assertEqual(blocked_rows[0]["action_class"], "blocked")
            self.assertEqual(blocked_rows[0]["original_action"], "买入")
            self.assertEqual(blocked_rows[0]["original_action_class"], "buy")
            self.assertEqual(blocked_rows[0]["executable_stake_aud"], 0.0)

            model_divergence_review = write_model_divergence_review_bundle(output_dir, db_path)
            self.assertEqual(model_divergence_review["artifacts"]["json"], MODEL_DIVERGENCE_REVIEW_JSON_LATEST)
            self.assertEqual(model_divergence_review["artifacts"]["markdown"], MODEL_DIVERGENCE_REVIEW_MD_LATEST)
            self.assertEqual(model_divergence_review["artifacts"]["pdf"], MODEL_DIVERGENCE_REVIEW_PDF_LATEST)
            self.assertEqual(model_divergence_review["artifacts"]["pdf_summary"]["chart_count"], 4)
            self.assertEqual(model_divergence_review["artifacts"]["pdf_summary"]["extra_table_count"], 3)
            self.assertEqual(model_divergence_review["storage"]["status"], "stored")
            self.assertIn("model_divergence_review_dashboard", model_divergence_review["mode"])
            self.assertEqual(model_divergence_review["summary"]["execution_unlock"], "blocked_by_design")
            self.assertGreaterEqual(model_divergence_review["summary"]["high_divergence_count"], 1)
            self.assertIn("high_priority_review_count", model_divergence_review["summary"])
            self.assertTrue(any(row["review_priority"] in {"高", "中", "低"} for row in model_divergence_review["review_rows"]))
            self.assertIn("old_new_compare", model_divergence_review)
            model_divergence_md = (output_dir / MODEL_DIVERGENCE_REVIEW_MD_LATEST).read_text(encoding="utf-8")
            self.assertIn("模型分歧复核 Dashboard", model_divergence_md)
            self.assertIn("Automation 使用视角", model_divergence_md)
            self.assertIn("blocked_by_design", model_divergence_md)
            self.assertIn("GitHub", model_divergence_md)
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM model_divergence_review_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / MODEL_DIVERGENCE_REVIEW_JSON_LATEST,
                        output_dir / MODEL_DIVERGENCE_REVIEW_MD_LATEST,
                        output_dir / MODEL_DIVERGENCE_REVIEW_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            strategy_performance = write_strategy_performance_bundle(output_dir, db_path)
            self.assertEqual(strategy_performance["artifacts"]["json"], STRATEGY_PERFORMANCE_JSON_LATEST)
            self.assertEqual(strategy_performance["artifacts"]["markdown"], STRATEGY_PERFORMANCE_MD_LATEST)
            self.assertEqual(strategy_performance["artifacts"]["pdf"], STRATEGY_PERFORMANCE_PDF_LATEST)
            self.assertEqual(strategy_performance["artifacts"]["pdf_summary"]["chart_count"], 5)
            self.assertEqual(strategy_performance["artifacts"]["pdf_summary"]["extra_table_count"], 4)
            self.assertEqual(strategy_performance["storage"]["status"], "stored")
            self.assertIn("strategy_performance_dashboard", strategy_performance["mode"])
            self.assertGreaterEqual(strategy_performance["summary"]["recommendation_count"], 1)
            self.assertGreaterEqual(strategy_performance["summary"]["buy_recommendation_count"], 1)
            self.assertEqual(strategy_performance["summary"]["realized_roi_status"], "outcome_pending")
            self.assertEqual(strategy_performance["summary"]["clv_tracking_status"], "clv_pending")
            self.assertGreater(strategy_performance["summary"]["backtest_readiness_score"], 0)
            self.assertIn("outcome_pending", strategy_performance["truthfulness_note"])
            self.assertIn("不自动下注", strategy_performance["safety_note"])
            self.assertTrue(any(row["board"] == "2026 World Cup Matches" for row in strategy_performance["board_rows"]))
            self.assertTrue(any(row["metric"] == "收盘赔率" for row in strategy_performance["clv_readiness_rows"]))
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM strategy_performance_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / STRATEGY_PERFORMANCE_JSON_LATEST,
                        output_dir / STRATEGY_PERFORMANCE_MD_LATEST,
                        output_dir / STRATEGY_PERFORMANCE_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            report_evolution = write_report_evolution_bundle(output_dir, db_path)
            self.assertEqual(report_evolution["artifacts"]["json"], REPORT_EVOLUTION_JSON_LATEST)
            self.assertEqual(report_evolution["artifacts"]["markdown"], REPORT_EVOLUTION_MD_LATEST)
            self.assertEqual(report_evolution["artifacts"]["pdf"], REPORT_EVOLUTION_PDF_LATEST)
            self.assertEqual(report_evolution["artifacts"]["pdf_summary"]["chart_count"], 5)
            self.assertEqual(report_evolution["artifacts"]["pdf_summary"]["extra_table_count"], 4)
            self.assertEqual(report_evolution["storage"]["status"], "stored")
            self.assertIn("report_evolution_dashboard", report_evolution["mode"])
            self.assertGreaterEqual(report_evolution["summary"]["report_diff_count"], 1)
            self.assertGreaterEqual(report_evolution["summary"]["evolution_score"], 0.35)
            self.assertEqual(len(report_evolution["signal_rows"]), 3)
            self.assertIn("日报级变化", report_evolution["evidence_layers"][0]["text"])
            self.assertIn("不自动下注", report_evolution["automation_note"])
            self.assertIn("不提交下注", report_evolution["safety_note"])
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM report_evolution_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / REPORT_EVOLUTION_JSON_LATEST,
                        output_dir / REPORT_EVOLUTION_MD_LATEST,
                        output_dir / REPORT_EVOLUTION_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            atomic_write_json(
                output_dir / current_matches_board().raw_snapshot,
                {
                    "generated_at": "2026-06-12T06:00:00Z",
                    "source": "unit_fixture_tab_matches",
                    "matches": [
                        {"match": "Mexico v South Africa", "href": "https://tab.test/mex-rsa", "markets": {"Result": "Mexico 1.50"}},
                        {"match": "South Korea v Czechia", "href": "https://tab.test/kor-cze", "markets": {"Result": "South Korea 2.10"}},
                        {"match": "Canada v Bosn-Herzegovina", "href": "https://tab.test/can-bih", "markets": {"Result": "Canada 2.30"}},
                    ],
                },
            )
            fixture_sanity = write_fixture_sanity_bundle(output_dir, db_path, openfootball_payload=sample_openfootball_2026_payload())
            self.assertEqual(fixture_sanity["artifacts"]["json"], FIXTURE_SANITY_JSON_LATEST)
            self.assertEqual(fixture_sanity["artifacts"]["markdown"], FIXTURE_SANITY_MD_LATEST)
            self.assertEqual(fixture_sanity["artifacts"]["pdf"], FIXTURE_SANITY_PDF_LATEST)
            self.assertEqual(fixture_sanity["artifacts"]["pdf_summary"]["chart_count"], 4)
            self.assertEqual(fixture_sanity["artifacts"]["pdf_summary"]["extra_table_count"], 3)
            self.assertEqual(fixture_sanity["storage"]["status"], "stored")
            self.assertIn("fixture_sanity_dashboard", fixture_sanity["mode"])
            self.assertEqual(fixture_sanity["summary"]["matched_count"], 2)
            self.assertEqual(fixture_sanity["summary"]["tab_only_count"], 1)
            self.assertEqual(fixture_sanity["summary"]["openfootball_only_count"], 1)
            self.assertEqual(fixture_sanity["source_fetch_status"]["status"], "injected_fixture")
            self.assertIn("delayed_public_source_not_live", fixture_sanity["summary"]["source_freshness"])
            self.assertIn("openfootball/worldcup.json", fixture_sanity["source_caveat"]["source"])
            self.assertIn("不是赔率源", fixture_sanity["truthfulness_note"])
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM fixture_sanity_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / FIXTURE_SANITY_JSON_LATEST,
                        output_dir / FIXTURE_SANITY_MD_LATEST,
                        output_dir / FIXTURE_SANITY_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            product_readiness = write_product_readiness_bundle(output_dir, db_path)
            self.assertEqual(product_readiness["artifacts"]["json"], PRODUCT_READINESS_JSON_LATEST)
            self.assertEqual(product_readiness["artifacts"]["markdown"], PRODUCT_READINESS_MD_LATEST)
            self.assertEqual(product_readiness["artifacts"]["pdf"], PRODUCT_READINESS_PDF_LATEST)
            self.assertEqual(product_readiness["artifacts"]["pdf_summary"]["chart_count"], 5)
            self.assertEqual(product_readiness["artifacts"]["pdf_summary"]["extra_table_count"], 3)
            self.assertEqual(product_readiness["storage"]["status"], "stored")
            self.assertIn("product_readiness_dashboard", product_readiness["mode"])
            product_rows_by_id = {row["row_id"]: row for row in product_readiness["rows"]}
            self.assertEqual(product_readiness["summary"]["capability_count"], 13)
            self.assertIn("betting_decision_home", product_rows_by_id)
            self.assertEqual(product_readiness["downloads_entry"]["required_column_count"], 21)
            self.assertEqual(product_readiness["downloads_entry"]["present_required_column_count"], 21)
            self.assertTrue(product_readiness["downloads_entry"]["all_required_columns"])
            self.assertIn("21/21", product_rows_by_id["betting_decision_home"]["evidence"])
            self.assertIn("recommendation_operation_archive", product_rows_by_id)
            self.assertEqual(product_rows_by_id["recommendation_operation_archive"]["status"], "ready")
            self.assertIn("strategy_performance_tracking", product_rows_by_id)
            self.assertEqual(product_rows_by_id["strategy_performance_tracking"]["status"], "partial")
            self.assertIn("report_evolution_control", product_rows_by_id)
            self.assertEqual(product_rows_by_id["report_evolution_control"]["status"], "ready")
            self.assertIn("open_source_model_adoption", product_rows_by_id)
            self.assertIn("public_fixture_sanity", product_rows_by_id)
            self.assertEqual(product_rows_by_id["public_fixture_sanity"]["status"], "ready")
            self.assertIn("database_and_old_new_compare", product_rows_by_id)
            self.assertIn("automation_without_autobet", product_rows_by_id)
            self.assertEqual(product_readiness["executive_status"]["current_executable_new_stake_aud"], 0)
            self.assertIn(product_readiness["executive_status"]["status"], {"in_progress", "ready"})
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM product_readiness_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / PRODUCT_READINESS_JSON_LATEST,
                        output_dir / PRODUCT_READINESS_MD_LATEST,
                        output_dir / PRODUCT_READINESS_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

            atomic_write_json(
                output_dir / SOURCE_MODEL_GITHUB_METADATA_JSON_LATEST,
                {
                    "schema_version": 1,
                    "generated_at": "2026-06-12T10:00:00+10:00",
                    "status": "partial",
                    "source_count": 6,
                    "fetched_count": 2,
                    "failed_count": 1,
                    "skipped_count": 0,
                    "stars_total": 855,
                    "forks_total": 153,
                    "open_issues_total": 18,
                    "rows": [
                        {
                            "source": "Hicruben/world-cup-2026-prediction-model",
                            "display_name": "Hicruben 2026 WC",
                            "url": "https://github.com/Hicruben/world-cup-2026-prediction-model",
                            "repo_slug": "Hicruben/world-cup-2026-prediction-model",
                            "api_url": "https://api.github.com/repos/Hicruben/world-cup-2026-prediction-model",
                            "fetched_at": "2026-06-12T10:00:00+10:00",
                            "fetch_status": "ready",
                            "stargazers_count": 22,
                            "forks_count": 6,
                            "open_issues_count": 1,
                            "watchers_count": 22,
                            "default_branch": "main",
                            "pushed_at": "2026-06-12T01:00:00Z",
                            "updated_at": "2026-06-12T02:00:00Z",
                            "archived": False,
                            "disabled": False,
                            "visibility": "public",
                            "license_key": "mit",
                            "license_name": "MIT License",
                            "language": "JavaScript",
                        },
                        {
                            "source": "martineastwood/penaltyblog",
                            "display_name": "penaltyblog",
                            "url": "https://github.com/martineastwood/penaltyblog",
                            "repo_slug": "martineastwood/penaltyblog",
                            "api_url": "https://api.github.com/repos/martineastwood/penaltyblog",
                            "fetched_at": "2026-06-12T10:00:00+10:00",
                            "fetch_status": "ready",
                            "stargazers_count": 833,
                            "forks_count": 147,
                            "open_issues_count": 17,
                            "watchers_count": 833,
                            "default_branch": "master",
                            "pushed_at": "2026-06-10T01:00:00Z",
                            "updated_at": "2026-06-11T02:00:00Z",
                            "archived": False,
                            "disabled": False,
                            "visibility": "public",
                            "license_key": "mit",
                            "license_name": "MIT License",
                            "language": "Python",
                        },
                        {
                            "source": "RyanSCodes/Dixon-Coles-Football-Predictor",
                            "display_name": "RyanSCodes DC",
                            "url": "https://github.com/RyanSCodes/Dixon-Coles-Football-Predictor",
                            "repo_slug": "RyanSCodes/Dixon-Coles-Football-Predictor",
                            "api_url": "https://api.github.com/repos/RyanSCodes/Dixon-Coles-Football-Predictor",
                            "fetched_at": "2026-06-12T10:00:00+10:00",
                            "fetch_status": "failed",
                            "error_type": "http_error",
                            "error_message": "HTTP 403",
                        },
                    ],
                },
            )
            source_model_registry = write_source_model_registry_bundle(output_dir, db_path)
            self.assertEqual(source_model_registry["artifacts"]["json"], SOURCE_MODEL_REGISTRY_JSON_LATEST)
            self.assertEqual(source_model_registry["artifacts"]["markdown"], SOURCE_MODEL_REGISTRY_MD_LATEST)
            self.assertEqual(source_model_registry["artifacts"]["pdf"], SOURCE_MODEL_REGISTRY_PDF_LATEST)
            self.assertEqual(source_model_registry["artifacts"]["pdf_summary"]["chart_count"], 9)
            self.assertEqual(source_model_registry["artifacts"]["pdf_summary"]["extra_table_count"], 5)
            self.assertEqual(source_model_registry["storage"]["status"], "stored")
            self.assertIn("source_model_registry_dashboard", source_model_registry["mode"])
            self.assertEqual(source_model_registry["summary"]["reference_count"], 6)
            self.assertEqual(source_model_registry["summary"]["implemented_reference_count"], 3)
            self.assertEqual(source_model_registry["summary"]["design_reference_count"], 3)
            self.assertEqual(source_model_registry["summary"]["ui_blueprint_count"], 6)
            self.assertEqual(source_model_registry["summary"]["ui_blueprint_implemented_count"], 4)
            self.assertEqual(source_model_registry["summary"]["ui_blueprint_partial_count"], 1)
            self.assertEqual(source_model_registry["summary"]["ui_blueprint_data_required_count"], 1)
            self.assertEqual(source_model_registry["summary"]["ui_blueprint_dashboard_covered_count"], 6)
            self.assertEqual(source_model_registry["summary"]["ui_blueprint_dashboard_gated_count"], 2)
            self.assertTrue(source_model_registry["summary"]["ui_blueprint_layout_ready"])
            self.assertGreaterEqual(source_model_registry["summary"]["license_risk_count"], 1)
            self.assertEqual(source_model_registry["summary"]["live_metadata_status"], "partial")
            self.assertEqual(source_model_registry["summary"]["live_metadata_ready_count"], 2)
            self.assertIn("live_metadata_freshness_status", source_model_registry["summary"])
            self.assertIn("live_metadata_fresh_within_sla_count", source_model_registry["summary"])
            self.assertIn("live_metadata_stale_count", source_model_registry["summary"])
            self.assertEqual(source_model_registry["summary"]["live_metadata_freshness_sla_hours"], 4)
            self.assertEqual(source_model_registry["summary"]["github_stars_total"], 855)
            self.assertEqual(source_model_registry["summary"]["github_open_issues_total"], 18)
            self.assertEqual(source_model_registry["github_metadata"]["artifact"], SOURCE_MODEL_GITHUB_METADATA_JSON_LATEST)
            self.assertTrue(any(row["source"] == "Hicruben/world-cup-2026-prediction-model" for row in source_model_registry["rows"]))
            self.assertTrue(any(row["source"] == "opisthokonta/goalmodel" for row in source_model_registry["rows"]))
            self.assertTrue(any(row["source"] == "RyanSCodes/Dixon-Coles-Football-Predictor" for row in source_model_registry["rows"]))
            self.assertTrue(any(row["source"] == "martineastwood/penaltyblog" for row in source_model_registry["rows"]))
            self.assertTrue(any(row["source"] == "ML-KULeuven/socceraction" for row in source_model_registry["rows"]))
            self.assertTrue(any(row["source"] == "openfootball/worldcup.json" for row in source_model_registry["rows"]))
            hicruben_row = next(row for row in source_model_registry["rows"] if row["source"] == "Hicruben/world-cup-2026-prediction-model")
            self.assertEqual(hicruben_row["live_fetch_status"], "ready")
            self.assertEqual(hicruben_row["github_stars"], 22)
            self.assertEqual(hicruben_row["github_license_live"], "MIT License")
            self.assertIn("live_metadata_freshness", hicruben_row)
            self.assertIn("live_metadata_age_hours", hicruben_row)
            self.assertIn("ui_blueprint", source_model_registry)
            self.assertTrue(any(item["component_id"] == "recommendation_command_center" for item in source_model_registry["ui_blueprint"]))
            self.assertTrue(any(item["component_id"] == "model_divergence_review_queue" for item in source_model_registry["ui_blueprint"]))
            fundamental_item = next(item for item in source_model_registry["ui_blueprint"] if item["component_id"] == "fundamental_context_layer")
            self.assertEqual(fundamental_item["implementation_status"], "data_required")
            self.assertEqual(fundamental_item["dashboard_coverage_status"], "covered_gated")
            self.assertIn("基本面解释位", fundamental_item["dashboard_surface"])
            source_model_registry_md = (output_dir / SOURCE_MODEL_REGISTRY_MD_LATEST).read_text(encoding="utf-8")
            self.assertIn("本地UI合同", source_model_registry_md)
            self.assertIn("UI / Dashboard Blueprint", source_model_registry_md)
            self.assertIn("UI界面覆盖", source_model_registry_md)
            self.assertIn("covered_gated", source_model_registry_md)
            self.assertIn("freshness_sla", source_model_registry_md)
            self.assertIn("Freshness", source_model_registry_md)
            self.assertIn("推荐下注指挥台", source_model_registry_md)
            self.assertTrue(any("FACT" == item["layer"] for row in source_model_registry["rows"] for item in row["evidence_layers"]))
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM source_model_registry_snapshots").fetchone()[0], 1)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / SOURCE_MODEL_REGISTRY_JSON_LATEST,
                        output_dir / SOURCE_MODEL_REGISTRY_MD_LATEST,
                        output_dir / SOURCE_MODEL_REGISTRY_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )
            maturity_with_registry = write_automation_maturity_bundle(output_dir, db_path)
            maturity_model_row = next(row for row in maturity_with_registry["rows"] if row["requirement_id"] == "open_source_models")
            self.assertIn("UI蓝图", maturity_model_row["evidence"])
            self.assertIn("GitHub元数据", maturity_model_row["evidence"])
            self.assertIn("4小时freshness", maturity_model_row["evidence"])
            self.assertEqual(maturity_with_registry["old_new_compare"]["status"], "compared")

            product_readiness_with_registry = write_product_readiness_bundle(output_dir, db_path)
            product_model_row = next(row for row in product_readiness_with_registry["rows"] if row["row_id"] == "open_source_model_adoption")
            self.assertEqual(product_model_row["status"], "ready")
            self.assertIn("UI蓝图", product_model_row["evidence"])
            self.assertIn("UI界面覆盖", product_model_row["evidence"])
            self.assertIn("4小时freshness", product_model_row["evidence"])
            self.assertIn("报告界面设计", product_model_row["value_over_static_report"])

            goal_traceability_with_registry = write_goal_traceability_bundle(output_dir, db_path)
            goal_model_row = next(row for row in goal_traceability_with_registry["rows"] if row["requirement_id"] == "github_models")
            self.assertEqual(goal_model_row["score"], 1.0)
            self.assertIn("UI蓝图", goal_model_row["evidence"])
            self.assertIn("功能、布局、界面和 UI", goal_model_row["user_value"])

            atomic_write_text(
                output_dir / "tab_fifa_dashboard_latest.html",
                "<html><body>Dashboard automation GitHub old compare 新旧 开源模型</body></html>",
            )
            atomic_write_json(
                output_dir / "tab_fifa_dashboard_data_latest.json",
                {
                    "schema_version": 1,
                    "generated_at": "2026-06-12T10:00:00+10:00",
                    "run_id": "test-run",
                    "report_date": "12062026",
                    "status": "ready_for_manual_report",
                    "technical_ready": True,
                    "automation_entry_ready": False,
                    "automation_authorized": False,
                    "kpis": [{"label": "技术自动化", "value": "通过", "state": "ok"}],
                    "board_statuses": [
                        {
                            "name": "2026 World Cup Matches",
                            "ready": True,
                            "raw_fresh": True,
                            "raw_valid": True,
                            "gate_ready": True,
                            "missing": [],
                        }
                    ],
                    "recommendations": [
                        {
                            "board_name": "2026 World Cup Matches",
                            "event_name": "A v B",
                            "market": "Result",
                            "selection": "A",
                            "odds": 2.0,
                            "probability": 0.55,
                            "expected_value": 0.1,
                            "stake_aud": 10,
                            "model_summary": "GitHub model cross-check",
                        }
                    ],
                    "visual_summary": [
                        {
                            "title": "板块自动化就绪度",
                            "kind": "bar",
                            "unit": "%",
                            "note": "automation dashboard",
                            "items": [{"label": "Matches", "value": 1.0, "display": "100%"}],
                        },
                        {
                            "title": "新旧报告对比",
                            "kind": "bar",
                            "unit": "count",
                            "note": "old/new compare",
                            "items": [{"label": "保留", "value": 1, "display": "1"}],
                        },
                    ],
                    "model_comparison": {
                        "summary": {"high_divergence_count": 1},
                        "rows": [
                            {
                                "match": "A v B",
                                "consensus": {"selection": "A", "mean_probability": 0.55, "confidence": "medium"},
                                "disagreement": {"max_abs_current_vs_elo_dc": 0.05},
                                "ratings": {"source": "Hicruben GitHub"},
                            }
                        ],
                    },
                    "compare_summary": {"added_count": 0, "removed_count": 0, "changed_count": 0, "retained_count": 1},
                    "preflight": {"technical_preflight_ready": True, "automation_entry_ready": False, "blocking_reasons": []},
                    "raw_refresh": {"ready": True, "ready_required": "1/1"},
                    "safety": {"ready": True, "blocking_reasons": []},
                },
            )
            dashboard_sidecar = write_dashboard_sidecar_bundle(output_dir)
            self.assertEqual(dashboard_sidecar["status"], "ready")

            visual_inventory = write_report_visual_inventory_bundle(output_dir)
            self.assertEqual(visual_inventory["artifacts"]["json"], REPORT_VISUAL_INVENTORY_JSON_LATEST)
            self.assertEqual(visual_inventory["artifacts"]["markdown"], REPORT_VISUAL_INVENTORY_MD_LATEST)
            self.assertEqual(visual_inventory["artifacts"]["pdf"], REPORT_VISUAL_INVENTORY_PDF_LATEST)
            self.assertEqual(visual_inventory["artifacts"]["pdf_summary"]["chart_count"], 5)
            self.assertEqual(visual_inventory["artifacts"]["pdf_summary"]["extra_table_count"], 2)
            self.assertEqual(visual_inventory["storage"]["status"], "stored")
            self.assertEqual(visual_inventory["storage"]["catalog_item_count"], 21)
            self.assertEqual(visual_inventory["summary"]["report_count"], 21)
            self.assertGreaterEqual(visual_inventory["summary"]["reports_with_charts"], 2)
            self.assertGreaterEqual(visual_inventory["summary"]["old_new_compare_count"], 2)
            self.assertIn("database_saved_count", visual_inventory["summary"])
            self.assertIn("decision_matrix_ready_count", visual_inventory["summary"])
            self.assertIn("blocking_gap_count", visual_inventory["summary"])
            self.assertIn("top_gap_capabilities", visual_inventory["summary"])
            self.assertTrue(any(row["report_id"] == "recommendation_operations" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "strategy_performance" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "report_evolution" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "fixture_sanity" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "model_divergence_review" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "source_model_registry" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "product_readiness" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "goal_traceability" for row in visual_inventory["rows"]))
            dashboard_row = next(row for row in visual_inventory["rows"] if row["report_id"] == "dashboard")
            self.assertTrue(dashboard_row["has_markdown"])
            self.assertTrue(dashboard_row["has_pdf"])
            recommendation_visual_row = next(row for row in visual_inventory["rows"] if row["report_id"] == "recommendation_operations")
            self.assertIn("decision_focus", recommendation_visual_row)
            self.assertIn("database_snapshot_count", recommendation_visual_row)
            self.assertIn("gap_severity", recommendation_visual_row)
            self.assertIn("publish_action", recommendation_visual_row)
            self.assertTrue(recommendation_visual_row["has_database_snapshot"])
            self.assertGreater(recommendation_visual_row["database_snapshot_count"], 0)
            self.assertTrue(any(row["report_id"] == "position_monitor" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "automation_maturity" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "raw_refresh_recovery" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "available_board_strategy" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "active_timeline" for row in visual_inventory["rows"]))
            self.assertTrue(any(row["report_id"] == "report_intelligence" and row["chart_count"] >= 11 for row in visual_inventory["rows"]))
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM report_visual_inventory_snapshots").fetchone()[0], 1)
                self.assertEqual(
                    conn.execute(
                        "SELECT COUNT(*) FROM report_catalog_items WHERE snapshot_id = ?",
                        (visual_inventory["storage"]["snapshot_id"],),
                    ).fetchone()[0],
                    21,
                )
                self.assertEqual(
                conn.execute(
                        "SELECT has_old_new_compare FROM report_catalog_items WHERE snapshot_id = ? AND report_id = ?",
                        (visual_inventory["storage"]["snapshot_id"], "recommendation_operations"),
                    ).fetchone()[0],
                    1,
                )
                catalog_columns = {row["name"] for row in conn.execute("PRAGMA table_info(report_catalog_items)").fetchall()}
                self.assertIn("has_database_snapshot", catalog_columns)
                self.assertIn("decision_focus", catalog_columns)
                self.assertEqual(
                    conn.execute(
                        "SELECT has_database_snapshot FROM report_catalog_items WHERE snapshot_id = ? AND report_id = ?",
                        (visual_inventory["storage"]["snapshot_id"], "recommendation_operations"),
                    ).fetchone()[0],
                    1,
                )
            write_automation_doctor_bundle(output_dir, db_path)
            product_readiness_after_visual = write_product_readiness_bundle(output_dir, db_path)
            self.assertGreaterEqual(product_readiness_after_visual["db_summary"]["report_visual_inventory_count"], 1)
            self.assertGreaterEqual(product_readiness_after_visual["db_summary"]["automation_doctor_count"], 1)
            self.assertEqual(product_readiness_after_visual["db_summary"]["report_catalog_item_count"], 21)
            self.assertIn(
                "report_catalog=21",
                next(row for row in product_readiness_after_visual["rows"] if row["row_id"] == "database_and_old_new_compare")["evidence"],
            )
            self.assertIn(
                "report_evolution=",
                next(row for row in product_readiness_after_visual["rows"] if row["row_id"] == "database_and_old_new_compare")["evidence"],
            )
            self.assertIn(
                "strategy_performance=",
                next(row for row in product_readiness_after_visual["rows"] if row["row_id"] == "database_and_old_new_compare")["evidence"],
            )
            self.assertIn(
                "fixture_sanity=",
                next(row for row in product_readiness_after_visual["rows"] if row["row_id"] == "database_and_old_new_compare")["evidence"],
            )
            self.assertIn(
                "automation_doctor=",
                next(row for row in product_readiness_after_visual["rows"] if row["row_id"] == "database_and_old_new_compare")["evidence"],
            )
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / REPORT_VISUAL_INVENTORY_JSON_LATEST,
                        output_dir / REPORT_VISUAL_INVENTORY_MD_LATEST,
                        output_dir / REPORT_VISUAL_INVENTORY_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )
            for name in [
                "tab_fifa_dashboard_latest.html",
                "tab_fifa_dashboard_data_latest.json",
                DASHBOARD_MD_LATEST,
                DASHBOARD_PDF_LATEST,
            ]:
                (output_dir / name).unlink(missing_ok=True)
            dashboard = write_dashboard(output_dir, db_path, manifest, publish_latest=False)
            self.assertTrue((output_dir / "tab_fifa_dashboard_test-run.html").exists())
            self.assertTrue((output_dir / "tab_fifa_dashboard_data_test-run.json").exists())
            self.assertFalse((output_dir / "tab_fifa_dashboard_latest.html").exists())
            self.assertFalse((output_dir / "tab_fifa_dashboard_data_latest.json").exists())
            update_run_dashboard_paths(
                db_path,
                "test-run",
                Path(dashboard["dashboard_run_copy"]),
                Path(dashboard["dashboard_data_run_copy"]),
            )
            with connect_report_db(db_path) as conn:
                artifact_kinds = {
                    row[0]
                    for row in conn.execute("SELECT kind FROM artifacts WHERE run_id = ?", ("test-run",)).fetchall()
                }
                self.assertIn("dashboard_run_copy", artifact_kinds)
                self.assertIn("dashboard_data_run_copy", artifact_kinds)
            self.assertEqual(latest_runs(db_path, limit=1)[0]["dashboard_path"], "tab_fifa_dashboard_test-run.html")
            publish_dashboard_latest(
                output_dir,
                Path(dashboard["dashboard_run_copy"]),
                Path(dashboard["dashboard_data_run_copy"]),
            )
            sidecar = write_dashboard_sidecar_bundle(output_dir)
            self.assertEqual(sidecar["status"], "ready")
            self.assertTrue((output_dir / DASHBOARD_MD_LATEST).exists())
            self.assertTrue((output_dir / DASHBOARD_PDF_LATEST).exists())
            dashboard_payload = json.loads((output_dir / "tab_fifa_dashboard_data_latest.json").read_text(encoding="utf-8"))
            self.assertEqual(dashboard_payload["artifacts"]["markdown"], DASHBOARD_MD_LATEST)
            self.assertEqual(dashboard_payload["artifacts"]["pdf"], DASHBOARD_PDF_LATEST)
            self.assertGreaterEqual(dashboard_payload["artifacts"]["pdf_summary"]["chart_count"], 4)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / DASHBOARD_MD_LATEST,
                        output_dir / DASHBOARD_PDF_LATEST,
                        output_dir / "tab_fifa_dashboard_data_latest.json",
                    ]
                )["public_artifact_safety_ready"]
            )
            html = Path(dashboard["dashboard"]).read_text(encoding="utf-8")
            self.assertIn("TAB FIFA 2026 盘口研究仪表盘", html)
            self.assertIn("A v B", html)
            self.assertIn("AUD 120", html)
            self.assertIn("开源模型分歧", html)
            self.assertIn("概率-赔率边际", html)
            self.assertIn("模型共识强度", html)
            self.assertIn("模型能力覆盖矩阵", html)
            self.assertIn("开源模型采用覆盖", html)
            self.assertIn("开源模型采用矩阵", html)
            self.assertIn("可复用/UI启发", html)
            self.assertIn("48队赛事路径 Monte Carlo 接口", html)
            self.assertIn("证据源日志", html)
            self.assertIn("运行审计与人工复核", html)
            self.assertIn("报告历史索引", html)
            self.assertIn("本地报告索引", html)
            self.assertIn("最新报告索引", html)
            self.assertIn("本地报告历史可视化", html)
            self.assertIn("最新报告历史可视化", html)
            self.assertIn("本地报告历史 PDF", html)
            self.assertIn("最新报告历史 PDF", html)
            self.assertIn("开源模型对比 PDF", html)
            self.assertIn("自动化就绪 PDF", html)
            self.assertIn("自动化候选 PDF", html)
            self.assertIn("自动化运行历史", html)
            self.assertIn("verify-only", html)
            self.assertIn("verify-only / hermetic", html)
            self.assertIn("capture 1 / import 0", html)
            self.assertIn("私有持仓", html)
            self.assertNotIn("My Bets", html)
            self.assertNotIn(str(output_dir), html)
            payload = json.loads(Path(dashboard["dashboard_data"]).read_text())
            self.assertEqual(payload["compare_summary"]["added_count"], 1)
            self.assertEqual(payload["bankroll"]["time_adjusted_new_exposure_aud"], 120)
            self.assertNotIn("positions_ready", payload["bankroll"])
            self.assertNotIn("private_detail_available", payload["bankroll"])
            self.assertNotIn("match_stakes", payload["bankroll"])
            self.assertTrue(payload["preflight"]["technical_preflight_ready"])
            self.assertTrue(payload["raw_refresh"]["ready"])
            self.assertTrue(payload["safety"]["ready"])
            self.assertEqual(payload["model_comparison"]["match_count"], len(EXPECTED_MATCHES))
            self.assertEqual(len(payload["visual_summary"]), 10)
            visual_ids = [chart["id"] for chart in payload["visual_summary"]]
            self.assertEqual(visual_ids[0], "board_readiness")
            self.assertEqual(visual_ids[-1], "model_capability_coverage")
            self.assertIn("stake_allocation", visual_ids)
            self.assertIn("odds_probability_edge", visual_ids)
            self.assertIn("model_consensus", visual_ids)
            self.assertIn("model_source_coverage", visual_ids)
            self.assertIn("evidence", payload)
            self.assertEqual(payload["artifacts"]["report_index"], "report_index_test-run.json")
            self.assertEqual(payload["artifacts"]["report_index_latest"], "report_index_latest.json")
            self.assertEqual(payload["artifacts"]["report_index_report"], "report_index_test-run.md")
            self.assertEqual(payload["artifacts"]["report_index_report_latest"], "report_index_latest.md")
            self.assertEqual(payload["artifacts"]["report_index_pdf"], "report_index_test-run.pdf")
            self.assertEqual(payload["artifacts"]["report_index_pdf_latest"], "report_index_latest.pdf")
            self.assertEqual(payload["artifacts"]["report_intelligence"], "report_intelligence_test-run.json")
            self.assertEqual(payload["artifacts"]["report_intelligence_latest"], REPORT_INTELLIGENCE_JSON_LATEST)
            self.assertEqual(payload["artifacts"]["report_intelligence_report"], "report_intelligence_test-run.md")
            self.assertEqual(payload["artifacts"]["report_intelligence_report_latest"], REPORT_INTELLIGENCE_MD_LATEST)
            self.assertEqual(payload["artifacts"]["report_intelligence_pdf"], "report_intelligence_test-run.pdf")
            self.assertEqual(payload["artifacts"]["report_intelligence_pdf_latest"], REPORT_INTELLIGENCE_PDF_LATEST)
            self.assertEqual(payload["artifacts"]["automation_readiness"], "automation_readiness_latest.json")
            self.assertEqual(payload["artifacts"]["automation_readiness_report"], "automation_readiness_latest.md")
            self.assertEqual(payload["artifacts"]["automation_readiness_pdf"], "automation_readiness_latest.pdf")
            self.assertEqual(payload["artifacts"]["automation_candidate"], AUTOMATION_CANDIDATE_LATEST)
            self.assertEqual(payload["artifacts"]["automation_candidate_report"], AUTOMATION_CANDIDATE_REPORT_LATEST)
            self.assertEqual(payload["artifacts"]["automation_candidate_pdf"], AUTOMATION_CANDIDATE_PDF_LATEST)
            self.assertEqual(payload["artifacts"]["model_comparison_pdf"], MODEL_COMPARISON_PDF)
            self.assertEqual(payload["automation_runs"][0]["automation_run_id"], "tab_fifa_daily_20260101T000003Z-test")
            self.assertEqual(payload["automation_runs"][0]["verify_mode"], "hermetic")
            self.assertTrue(payload["automation_runs"][0]["my_bets_capture_enabled"])
            self.assertFalse(payload["automation_runs"][0]["formal_report_publish_ready"])
            self.assertEqual(payload["automation_runs"][0]["capture_log"], "capture.log")
            self.assertGreaterEqual(payload["evidence"]["summary"]["source_count"], 3)
            self.assertGreater(len(payload["evidence"]["source_logs"]), 0)
            self.assertGreater(len(payload["evidence"]["audit_logs"]), 0)
            stake_chart = next(chart for chart in payload["visual_summary"] if chart["id"] == "stake_allocation")
            self.assertEqual(stake_chart["items"][0]["display"], "AUD 120")
            recommendation_row = next(row for row in payload["recommendations"] if row["board_id"] == "world_cup_matches")
            self.assertEqual(recommendation_row["stake_aud"], 120)
            self.assertIn("source_adoption", payload["model_comparison"])
            self.assertNotIn(str(output_dir), json.dumps(payload, ensure_ascii=False))
            self.assertTrue(
                audit_public_artifact_safety([Path(dashboard["dashboard"]), Path(dashboard["dashboard_data"])])[
                    "public_artifact_safety_ready"
                ]
            )
            self.assertTrue((output_dir / "tab_fifa_dashboard_test-run.html").exists())

    def test_automation_doctor_bundle_is_public_safe_and_blocks_entry_when_gaps_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / "automation_readiness_latest.json",
                {
                    "formal_report_publish_ready": False,
                    "recurring_automation_ready": False,
                    "raw_refresh": {"ready": True, "status": "ready", "ready_required": "5/5"},
                    "public_safety": {"output_safety_ready": True, "artifact_safety_ready": True},
                    "technical_preflight": {"publication_clear": False, "run_id": "attempt-run"},
                    "automation_candidate": {"ready": False, "status": "review_only"},
                    "private_position_bootstrap": {
                        "ready": False,
                        "report_date": "01012026",
                        "status": "profile_login_required",
                        "next_action": "run headed read-only capture",
                        "profile": {"exists": False},
                        "files": {
                            "snapshot_exists": False,
                            "raw_text_exists": False,
                            "diagnostics_exists": True,
                        },
                    },
                },
            )
            atomic_write_json(
                output_dir / "active_timeline_latest.json",
                {
                    "cadence_rule": {
                        "target_slots": ["00:00-05:00", "05:00-10:00", "10:00-15:00"],
                        "min_analyses_per_day": 4,
                    },
                    "summary": {
                        "day_count": 2,
                        "complete_day_count": 0,
                        "missing_analysis_day_count": 2,
                        "missing_report_day_count": 2,
                        "backfill_queue_count": 2,
                    },
                    "days": [
                        {
                            "display_date": "01/01/2026",
                            "effective_analysis_count": 1,
                            "covered_slots": ["00:00-05:00"],
                            "missing_slots": ["05:00-10:00", "10:00-15:00"],
                            "formal_report_exists": False,
                            "backfill_reasons": ["有效分析 1/4", "Downloads 正式日报缺失"],
                        },
                        {
                            "display_date": "02/01/2026",
                            "effective_analysis_count": 0,
                            "covered_slots": [],
                            "missing_slots": ["00:00-05:00", "05:00-10:00", "10:00-15:00"],
                            "formal_report_exists": False,
                            "backfill_reasons": ["有效分析 0/4", "Downloads 正式日报缺失"],
                        },
                    ],
                    "backfill_queue": [
                        {
                            "repair_rank": 1,
                            "display_date": "02/01/2026",
                            "priority_score": 140,
                            "reason": "有效分析 0/4；Downloads 正式日报缺失",
                            "priority_reason": "缺失时段 3/5；有效分析 0/4；日报缺失；latest=missing",
                        },
                        {
                            "repair_rank": 2,
                            "display_date": "01/01/2026",
                            "priority_score": 105,
                            "reason": "有效分析 1/4；Downloads 正式日报缺失",
                            "priority_reason": "缺失时段 2/5；有效分析 1/4；日报缺失；latest=blocked_by_gate",
                        },
                    ],
                },
            )
            atomic_write_json(
                output_dir / "latest_commit.json",
                {
                    "run_id": "trusted-run",
                    "report_date": "01012026",
                    "status": "ready_for_manual_report",
                    "public_artifact_safety_ready": True,
                },
            )
            atomic_write_json(output_dir / "raw_refresh_health_latest.json", {"ready": True, "status": "ready"})
            atomic_write_json(
                output_dir / "report_intelligence_latest.json",
                {
                    "executive_status": {"current_action": "hold"},
                    "timeline_health": {
                        "audit_trend_summary": {
                            "audit_count": 2,
                            "latest_complete_ratio": 0.25,
                            "latest_gap_count": 4,
                            "raw_ready_audit_count": 1,
                            "trend_direction": "improving",
                        },
                        "slot_heatmap": [
                            {
                                "date": "01/01/2026",
                                "effective_analysis_count": 1,
                                "formal_report_exists": False,
                                "reason": "有效分析 1/4",
                                "cells": [
                                    {"label": "00-05", "status": "covered"},
                                    {"label": "05-10", "status": "missing"},
                                    {"label": "10-15", "status": "missing"},
                                ],
                            },
                            {
                                "date": "02/01/2026",
                                "effective_analysis_count": 0,
                                "formal_report_exists": False,
                                "reason": "有效分析 0/4",
                                "cells": [
                                    {"label": "00-05", "status": "missing"},
                                    {"label": "05-10", "status": "missing"},
                                    {"label": "10-15", "status": "missing"},
                                ],
                            },
                        ],
                    },
                },
            )

            db_path = output_dir / "tab_fifa_reports.sqlite3"
            payload = write_automation_doctor_bundle(output_dir, db_path)

            self.assertFalse(payload["executive_status"]["ready_to_enter_recurring_automation"])
            self.assertEqual(payload["executive_status"]["primary_blocker"], "私有持仓快照缺失")
            self.assertEqual(payload["artifacts"]["json"], AUTOMATION_DOCTOR_JSON_LATEST)
            self.assertEqual(payload["artifacts"]["markdown"], AUTOMATION_DOCTOR_MD_LATEST)
            self.assertEqual(payload["artifacts"]["pdf"], AUTOMATION_DOCTOR_PDF_LATEST)
            self.assertEqual(payload["artifacts"]["pdf_summary"]["chart_count"], 7)
            self.assertEqual(payload["artifacts"]["pdf_summary"]["extra_table_count"], 6)
            self.assertTrue(payload["snapshot_id"].startswith("automation-doctor-"))
            self.assertEqual(payload["storage"]["status"], "stored")
            self.assertEqual(payload["storage"]["table"], "automation_doctor_snapshots")
            self.assertIn("old_new_compare", payload)
            self.assertIn("summary", payload)
            self.assertEqual(payload["summary"]["automation_entry_status"], "blocked")
            self.assertEqual(payload["summary"]["private_position_status"], "profile_login_required")
            self.assertEqual(payload["summary"]["backfill_queue_count"], 2)
            self.assertIn("暂不进入每日自动化", payload["summary"]["decision_sentence"])
            self.assertIn("不自动下注", payload["summary"]["safety_boundary"])
            self.assertEqual(payload["doctor_dashboard"]["title"], "Automation Doctor Dashboard")
            self.assertEqual(payload["doctor_dashboard"]["entry_decision"], "暂不进入每日自动化")
            self.assertGreater(payload["doctor_dashboard"]["p0_blocker_count"], 0)
            self.assertEqual(payload["automation_trend"]["audit_count"], 2)
            self.assertEqual(payload["automation_trend"]["trend_direction"], "improving")
            self.assertEqual(payload["automation_trend"]["repeated_missing_slots"][0]["slot"], "05-10")
            self.assertEqual(payload["automation_trend"]["backfill_queue_preview"][0]["date"], "02/01/2026")
            self.assertEqual(payload["automation_trend"]["backfill_queue_preview"][0]["score"], 140)
            self.assertIn("优先补齐日期", payload["automation_trend"]["repair_focus"])
            command_text = json.dumps(payload["command_queue"], ensure_ascii=False)
            self.assertIn("建立私有持仓读取 profile", command_text)
            self.assertIn("补齐主动测试缺口", command_text)
            self.assertIn("重点时段", command_text)
            self.assertIn("<private_raw_text_01012026.txt>", command_text)
            doctor_md = (output_dir / AUTOMATION_DOCTOR_MD_LATEST).read_text(encoding="utf-8")
            self.assertIn("Automation Doctor Dashboard", doctor_md)
            self.assertIn("Summary For Aggregation", doctor_md)
            self.assertIn("automation_entry_status", doctor_md)
            self.assertIn("入场门禁得分", doctor_md)
            self.assertIn("修复优先级趋势", doctor_md)
            self.assertIn("新旧诊断变化", doctor_md)
            self.assertIn("补跑顺序", doctor_md)
            self.assertIn("缺失时段 3/5", doctor_md)
            self.assertIn("05-10", doctor_md)
            doctor_paths = [
                output_dir / AUTOMATION_DOCTOR_JSON_LATEST,
                output_dir / AUTOMATION_DOCTOR_MD_LATEST,
                output_dir / AUTOMATION_DOCTOR_PDF_LATEST,
            ]
            self.assertTrue(all(path.exists() for path in doctor_paths))
            with connect_report_db(db_path) as conn:
                self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM automation_doctor_snapshots").fetchone()[0], 1)
                stored = conn.execute(
                    "SELECT p0_blocker_count, private_position_status FROM automation_doctor_snapshots ORDER BY generated_at DESC LIMIT 1"
                ).fetchone()
                self.assertGreater(stored["p0_blocker_count"], 0)
                self.assertEqual(stored["private_position_status"], "profile_login_required")
            self.assertTrue(audit_public_artifact_safety(doctor_paths)["public_artifact_safety_ready"])

    def test_automation_doctor_prefers_current_position_monitor_over_stale_readiness_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            private_dir = output_dir / "private"
            private_dir.mkdir(parents=True)
            (private_dir / "tab_chrome_profile").mkdir()
            atomic_write_json(
                private_dir / "tab_my_bets_capture_diagnostics_13062026.json",
                {
                    "report_date": "13062026",
                    "ready": False,
                    "auth_status": "login_required",
                    "auth_mode": "persistent-profile",
                    "reason": "TAB My Bets page appears unauthenticated",
                },
            )
            atomic_write_json(
                output_dir / "automation_readiness_latest.json",
                {
                    "formal_report_publish_ready": False,
                    "recurring_automation_ready": False,
                    "raw_refresh": {"ready": False, "status": "blocked"},
                    "public_safety": {"output_safety_ready": True, "artifact_safety_ready": True},
                    "technical_preflight": {"publication_clear": False},
                    "private_position_bootstrap": {
                        "ready": False,
                        "report_date": "04062026",
                        "status": "raw_ready_import_needed",
                        "next_action": "stale import command",
                        "profile": {"exists": False},
                        "files": {"raw_text_exists": True, "snapshot_exists": True, "diagnostics_exists": False},
                    },
                },
            )
            atomic_write_json(
                output_dir / "position_monitor_latest.json",
                {
                    "summary": {
                        "report_date": "13062026",
                        "snapshot_ready": False,
                        "diagnostics_exists": True,
                        "profile_exists": True,
                    }
                },
            )
            atomic_write_json(output_dir / "active_timeline_latest.json", {"summary": {}})
            atomic_write_json(output_dir / "latest_commit.json", {"run_id": "trusted", "report_date": "04062026", "public_artifact_safety_ready": True})
            atomic_write_json(output_dir / "raw_refresh_health_latest.json", {"ready": False, "status": "blocked"})

            with mock.patch.dict(os.environ, {"TAB_FIFA_PRIVATE_DIR": str(private_dir)}):
                payload = write_automation_doctor_bundle(output_dir, output_dir / "tab_fifa_reports.sqlite3")

            bootstrap = payload["private_position_bootstrap"]
            self.assertEqual(bootstrap["report_date"], "13062026")
            self.assertEqual(bootstrap["status"], "profile_login_required")
            self.assertTrue(bootstrap["profile_exists"])
            self.assertEqual(payload["doctor_dashboard"]["private_position_status"], "profile_login_required")
            self.assertNotIn("04062026", json.dumps(payload["command_queue"], ensure_ascii=False))
            self.assertIn("13062026", json.dumps(payload["command_queue"], ensure_ascii=False))

    def test_automation_run_history_persists_public_safe_runner_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "tab_fifa_reports.sqlite3"
            summary = {
                "schema_version": 1,
                "mode": "verify-only",
                "verify_mode": "artifact-chain-only",
                "status": "verified",
                "exit_code": 0,
                "started_at": "2026-06-06T00:27:26Z",
                "finished_at": "2026-06-06T00:27:54Z",
                "stdout_log": "tab_fifa_daily_20260606T002726Z-63662.stdout.log",
                "stderr_log": "tab_fifa_daily_20260606T002726Z-63662.stderr.log",
                "stderr_tail": "AssertionError at async file://capture_tab_my_bets_readonly_security.test.mjs:51:3",
                "run_id": "20260604T135753Z-212e8e9a",
                "raw_refresh_ready": True,
                "my_bets_capture": {
                    "enabled": True,
                    "report_date": "06062026",
                    "capture_exit_code": 1,
                    "import_exit_code": 0,
                    "raw_text_seen": False,
                    "capture_log": "/Users/test/work/private/tab_fifa/automation_run_logs/tab_fifa_my_bets_capture_x.log",
                    "import_log": "/Users/test/work/private/tab_fifa/automation_run_logs/tab_fifa_my_bets_import_x.log",
                },
                "last_success": {
                    "run_id": "20260604T135753Z-212e8e9a",
                },
                "automation_readiness": {
                    "formal_report_publish_ready": False,
                    "recurring_automation_ready": False,
                    "private_position_bootstrap": {
                        "status": "profile_login_required",
                        "capture_diagnostic": {
                            "auth_status": "access_denied",
                            "reason": "TAB My Bets page access denied",
                        },
                    },
                },
            }
            stored = store_automation_run(db_path, summary)
            self.assertEqual(stored["automation_run_id"], "tab_fifa_daily_20260606T002726Z-63662")
            rows = latest_automation_runs(db_path, limit=1)
            self.assertEqual(rows[0]["automation_run_id"], "tab_fifa_daily_20260606T002726Z-63662")
            self.assertEqual(rows[0]["verify_mode"], "artifact-chain-only")
            self.assertTrue(rows[0]["my_bets_capture_enabled"])
            self.assertEqual(rows[0]["my_bets_report_date"], "06062026")
            self.assertEqual(rows[0]["my_bets_capture_exit_code"], 1)
            self.assertEqual(rows[0]["capture_log"], "tab_fifa_my_bets_capture_x.log")
            self.assertFalse(rows[0]["formal_report_publish_ready"])
            with connect_report_db(db_path) as conn:
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='automation_runs'").fetchall()
                self.assertEqual(len(tables), 1)
                summary_json = conn.execute("SELECT summary_json FROM automation_runs").fetchone()[0]
                self.assertNotIn("/Users/", summary_json)
                self.assertNotIn("/work/private/", summary_json)
                self.assertNotIn("My Bets", summary_json)
                self.assertNotIn("file://", summary_json)
            self.assertTrue(audit_public_artifact_safety([db_path])["public_artifact_safety_ready"])

    def test_automation_readiness_summary_reports_live_data_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            run_id = "run-123"
            artifact_names = [
                f"tab_fifa_bankroll_plan_01012026_{run_id}.json",
                f"tab_fifa_dashboard_{run_id}.html",
                f"tab_fifa_dashboard_data_{run_id}.json",
                f"daily_report_manifest_{run_id}.json",
                f"report_index_{run_id}.json",
                "report_index_latest.json",
            ]
            for name in artifact_names:
                (output_dir / name).write_text('{"ok": true}', encoding="utf-8")
            styles = getSampleStyleSheet()
            SimpleDocTemplate(str(output_dir / f"01012026_{run_id}.pdf"), pagesize=A4).build(
                [Paragraph("Public TAB FIFA report fixture", styles["Normal"])]
            )
            latest_commit = {
                "run_id": run_id,
                "report_date": "01012026",
                "status": "ready_for_manual_report",
                "technical_automation_ready": True,
                "automation_entry_ready": False,
                "public_artifact_safety_ready": True,
                "ready_required_boards": "5/5",
                "artifacts": {
                    "pdf_run_copy": f"01012026_{run_id}.pdf",
                    "bankroll_plan_run_copy": f"tab_fifa_bankroll_plan_01012026_{run_id}.json",
                    "dashboard_run_copy": f"tab_fifa_dashboard_{run_id}.html",
                    "dashboard_data_run_copy": f"tab_fifa_dashboard_data_{run_id}.json",
                    "manifest": f"daily_report_manifest_{run_id}.json",
                    "report_index": f"report_index_{run_id}.json",
                    "report_index_latest": "report_index_latest.json",
                },
                "run_artifacts": {
                    "pdf_run_copy": f"01012026_{run_id}.pdf",
                    "bankroll_plan_run_copy": f"tab_fifa_bankroll_plan_01012026_{run_id}.json",
                    "dashboard_run_copy": f"tab_fifa_dashboard_{run_id}.html",
                    "dashboard_data_run_copy": f"tab_fifa_dashboard_data_{run_id}.json",
                    "manifest": f"daily_report_manifest_{run_id}.json",
                },
            }
            atomic_write_json(output_dir / "latest_commit.json", latest_commit)
            atomic_write_json(
                output_dir / "report_index_latest.json",
                {
                    "schema_version": 1,
                    "committed_latest_run_id": run_id,
                    "latest_success_run_id": run_id,
                    "run_count": 1,
                },
            )
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "refresh_error": "matches refresh command timed out after 180 seconds",
                },
            )
            summary_path = output_dir / "automation_readiness_latest.json"
            summary = write_automation_readiness_summary(
                output_dir,
                summary_path,
                command_status={"mode": "verify-only", "exit_code": 1},
            )
            self.assertEqual(summary["status"], "code_ready_live_data_blocked")
            self.assertFalse(summary["formal_report_publish_ready"])
            self.assertFalse(summary["recurring_automation_ready"])
            self.assertTrue(summary["automation_candidate"]["ready"])
            self.assertEqual(summary["automation_candidate"]["recommended_cadence"], "4h")
            self.assertFalse(summary["automation_candidate"]["installed"])
            self.assertIn("raw_refresh_blocked", {item["code"] for item in summary["blockers"]})
            self.assertIn("recurring_authorization_missing", {item["code"] for item in summary["blockers"]})
            self.assertEqual(summary["latest_commit"]["run_id"], run_id)
            self.assertEqual(summary["report_index"]["latest_success_run_id"], run_id)
            self.assertIn("refresh_command_failed", summary["raw_refresh"]["blocker_codes"])
            self.assertIn("检查 raw refresh", summary["raw_refresh"]["recommended_next_action"])
            self.assertTrue(summary_path.exists())
            self.assertNotIn(str(output_dir), json.dumps(summary, ensure_ascii=False))
            self.assertTrue(audit_public_artifact_safety([summary_path])["public_artifact_safety_ready"])
            report_path = output_dir / "automation_readiness_latest.md"
            report = write_automation_readiness_report(output_dir, report_path, summary=summary)
            markdown = report_path.read_text(encoding="utf-8")
            self.assertEqual(report["mermaid_blocks"], 4)
            self.assertIn("## Visual Summary", markdown)
            self.assertIn("Gate readiness mix", markdown)
            self.assertIn("Gate scorecard", markdown)
            self.assertIn("Blocker severity mix", markdown)
            self.assertIn("Next action priority", markdown)
            self.assertIn("automation candidate", markdown)
            self.assertIn("4h", markdown)
            self.assertNotIn(str(output_dir), markdown)
            self.assertTrue(audit_public_artifact_safety([report_path])["public_artifact_safety_ready"])
            pdf_path = output_dir / "automation_readiness_latest.pdf"
            pdf = write_automation_readiness_pdf(output_dir, pdf_path, summary=summary)
            self.assertEqual(pdf["chart_count"], 4)
            self.assertTrue(pdf_path.exists())
            self.assertTrue(audit_public_artifact_safety([pdf_path])["public_artifact_safety_ready"])

    def test_automation_readiness_blocks_newer_failed_technical_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            private_dir = Path(tmp) / "private" / "tab_fifa"
            private_dir.mkdir(parents=True)
            latest_run_id = "20260604T135753Z-212e8e9a"
            failed_run_id = "20260605T084257Z-6cd72c59"
            failed_report_date = "05062026"
            for name in [
                f"tab_fifa_bankroll_plan_04062026_{latest_run_id}.json",
                f"tab_fifa_dashboard_{latest_run_id}.html",
                f"tab_fifa_dashboard_data_{latest_run_id}.json",
                f"daily_report_manifest_{latest_run_id}.json",
                f"report_index_{latest_run_id}.json",
            ]:
                (output_dir / name).write_text('{"ok": true}', encoding="utf-8")
            SimpleDocTemplate(str(output_dir / f"04062026_{latest_run_id}.pdf"), pagesize=A4).build(
                [Paragraph("Public TAB FIFA report fixture", getSampleStyleSheet()["Normal"])]
            )
            atomic_write_json(
                output_dir / "latest_commit.json",
                {
                    "run_id": latest_run_id,
                    "report_date": "04062026",
                    "status": "ready_for_manual_report",
                    "technical_automation_ready": True,
                    "automation_entry_ready": False,
                    "public_artifact_safety_ready": True,
                    "ready_required_boards": "5/5",
                    "artifacts": {
                        "pdf_run_copy": f"04062026_{latest_run_id}.pdf",
                        "bankroll_plan_run_copy": f"tab_fifa_bankroll_plan_04062026_{latest_run_id}.json",
                        "dashboard_run_copy": f"tab_fifa_dashboard_{latest_run_id}.html",
                        "dashboard_data_run_copy": f"tab_fifa_dashboard_data_{latest_run_id}.json",
                        "manifest": f"daily_report_manifest_{latest_run_id}.json",
                        "report_index": f"report_index_{latest_run_id}.json",
                    },
                    "run_artifacts": {
                        "pdf_run_copy": f"04062026_{latest_run_id}.pdf",
                        "bankroll_plan_run_copy": f"tab_fifa_bankroll_plan_04062026_{latest_run_id}.json",
                        "dashboard_run_copy": f"tab_fifa_dashboard_{latest_run_id}.html",
                        "dashboard_data_run_copy": f"tab_fifa_dashboard_data_{latest_run_id}.json",
                        "manifest": f"daily_report_manifest_{latest_run_id}.json",
                    },
                },
            )
            atomic_write_json(
                output_dir / "report_index_latest.json",
                {
                    "schema_version": 1,
                    "committed_latest_run_id": latest_run_id,
                    "latest_success_run_id": latest_run_id,
                    "run_count": 2,
                },
            )
            atomic_write_json(
                output_dir / f"automation_preflight_{failed_run_id}.json",
                {
                    "schema_version": 1,
                    "run_id": failed_run_id,
                    "technical_preflight_ready": False,
                    "automation_entry_ready": False,
                    "blocking_reasons": [
                        "current-day private position snapshot missing",
                        "user has not authorized recurring automation",
                    ],
                    "checks": [
                        {
                            "name": "private_positions_available",
                            "passed": False,
                            "message": "current-day private position snapshot missing",
                            "details": [
                                {
                                    "capture_diagnostic": {
                                        "report_date": failed_report_date,
                                        "ready": False,
                                        "auth_status": "access_denied",
                                        "auth_mode": "persistent-profile",
                                        "reason": "TAB My Bets page access denied",
                                        "text_length": 120,
                                    }
                                }
                            ],
                        }
                    ],
                },
            )
            atomic_write_json(
                private_dir / f"tab_my_bets_capture_diagnostics_{failed_report_date}.json",
                {
                    "schema_version": 1,
                    "private_diagnostic": True,
                    "report_date": failed_report_date,
                    "ready": False,
                    "auth_status": "access_denied",
                    "auth_mode": "persistent-profile",
                    "reason": "TAB My Bets page access denied",
                    "text_length": 120,
                },
            )
            original_audit_raw_refresh = automation_readiness_module.audit_raw_refresh
            original_raw_refresh_health = automation_readiness_module.raw_refresh_health
            original_private_dir = os.environ.get("TAB_FIFA_PRIVATE_DIR")
            try:
                os.environ["TAB_FIFA_PRIVATE_DIR"] = str(private_dir)
                automation_readiness_module.audit_raw_refresh = lambda _output_dir: {
                    "raw_refresh_ready": True,
                    "ready_required_target_count": 5,
                    "required_target_count": 5,
                    "blocking_reasons": [],
                }
                automation_readiness_module.raw_refresh_health = lambda _gate, refresh_error="": {
                    "ready": True,
                    "status": "ready",
                    "blocker_codes": [],
                    "blocking_reasons": [],
                    "recommended_next_action": "",
                }
                summary = automation_readiness_module.write_automation_readiness_summary(
                    output_dir,
                    output_dir / "automation_readiness_latest.json",
                )
            finally:
                automation_readiness_module.audit_raw_refresh = original_audit_raw_refresh
                automation_readiness_module.raw_refresh_health = original_raw_refresh_health
                if original_private_dir is None:
                    os.environ.pop("TAB_FIFA_PRIVATE_DIR", None)
                else:
                    os.environ["TAB_FIFA_PRIVATE_DIR"] = original_private_dir

            self.assertEqual(summary["status"], "current_run_preflight_blocked")
            self.assertFalse(summary["formal_report_publish_ready"])
            self.assertTrue(summary["technical_preflight"]["blocks_publication"])
            self.assertEqual(summary["technical_preflight"]["run_id"], failed_run_id)
            self.assertEqual(summary["private_position_bootstrap"]["report_date"], failed_report_date)
            self.assertEqual(summary["private_position_bootstrap"]["status"], "profile_login_required")
            self.assertEqual(summary["private_position_bootstrap"]["capture_diagnostic"]["auth_status"], "access_denied")
            self.assertTrue(summary["technical_preflight"]["newer_than_latest_success"])
            self.assertIn("current_preflight_blocked", {item["code"] for item in summary["blockers"]})
            self.assertTrue(any("capture_tab_my_bets_readonly.mjs" in action for action in summary["next_actions"]))
            self.assertNotIn(str(output_dir), json.dumps(summary, ensure_ascii=False))

    def test_automation_candidate_artifacts_are_review_only_and_public_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            candidate = build_automation_candidate()
            self.assertTrue(candidate["candidate_ready"])
            self.assertFalse(candidate["installed"])
            self.assertEqual(candidate["recommended_cadence"], "4h")
            self.assertEqual(candidate["rrule"], "FREQ=HOURLY;INTERVAL=4")
            self.assertFalse(candidate["auto_wagering_allowed"])
            self.assertTrue(candidate["requires_user_authorization"])
            self.assertIn("report_generation_only", candidate["scope"])
            self.assertIn("--allow-research-only-success", candidate["entrypoint"])
            self.assertIn("DDMMYYYY_partial_daily_research.pdf", candidate["expected_artifacts"])
            self.assertTrue(any(item["code"] == "research_only_daily_allowed" for item in candidate["guardrails"]))
            self.assertTrue(any(item["name"] == "research-only daily PDF" for item in candidate["required_gates"]))
            self.assertTrue(any(item["code"] == "no_auto_wagering" for item in candidate["guardrails"]))
            json_path = output_dir / AUTOMATION_CANDIDATE_LATEST
            md_path = output_dir / AUTOMATION_CANDIDATE_REPORT_LATEST
            pdf_path = output_dir / AUTOMATION_CANDIDATE_PDF_LATEST
            write_automation_candidate(output_dir, json_path, candidate=candidate)
            report = write_automation_candidate_report(output_dir, md_path, candidate=candidate)
            pdf = write_automation_candidate_pdf(output_dir, pdf_path, candidate=candidate)
            self.assertEqual(report["mermaid_blocks"], 4)
            self.assertEqual(pdf["chart_count"], 4)
            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("Visual Summary", markdown)
            self.assertIn("FREQ=HOURLY;INTERVAL=4", markdown)
            self.assertIn("review-only", markdown)
            self.assertNotIn(str(output_dir), json.dumps(candidate, ensure_ascii=False))
            self.assertTrue(audit_public_artifact_safety([json_path, md_path, pdf_path])["public_artifact_safety_ready"])

    def test_automation_readiness_separates_research_only_daily_from_formal_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            partial_payload = {
                "schema_version": 1,
                "generated_at": "2026-06-13T05:00:00+10:00",
                "report_date": "13062026",
                "executive_status": {
                    "status": "ready_research_only",
                    "partial_daily_report_ready": True,
                    "execution_allowed": False,
                    "current_executable_new_stake_aud": 0,
                    "recommended_next_action": "继续只读发现缺失板块。",
                },
                "summary": {
                    "partial_successful_board_count": 4,
                    "partial_attempted_board_count": 5,
                    "unavailable_board_count": 1,
                    "partial_freshness_status": "fresh_4h",
                    "partial_fresh_within_sla": True,
                    "board_scope_source": "current_discovery+partial_raw_success",
                    "partial_evidence_source": "raw_refresh_research_only_latest.json",
                },
                "artifacts": {
                    "json": PARTIAL_DAILY_RESEARCH_JSON_LATEST,
                    "markdown": PARTIAL_DAILY_RESEARCH_MD_LATEST,
                    "pdf": PARTIAL_DAILY_RESEARCH_PDF_LATEST,
                    "dated_pdf": "13062026_partial_daily_research.pdf",
                },
            }
            atomic_write_json(output_dir / PARTIAL_DAILY_RESEARCH_JSON_LATEST, partial_payload)
            atomic_write_text(output_dir / PARTIAL_DAILY_RESEARCH_MD_LATEST, "# Research only daily report\n\nNo wagering execution.\n")
            styles = getSampleStyleSheet()
            for name in [PARTIAL_DAILY_RESEARCH_PDF_LATEST, "13062026_partial_daily_research.pdf"]:
                SimpleDocTemplate(str(output_dir / name), pagesize=A4).build(
                    [Paragraph("Research only daily report. No wagering execution.", styles["Normal"])]
                )
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "blocker_codes": ["missing_board"],
                    "blocking_reasons": ["Australia Markets unavailable"],
                },
            )

            summary = write_automation_readiness_summary(
                output_dir,
                output_dir / "automation_readiness_latest.json",
                command_status={"mode": "daily", "exit_code": 1, "research_only_daily_report_ready": True},
            )

            self.assertEqual(summary["status"], "research_only_daily_ready_formal_blocked")
            self.assertTrue(summary["research_only_daily_report_ready"])
            self.assertTrue(summary["research_only_recurring_candidate_ready"])
            self.assertFalse(summary["formal_report_publish_ready"])
            self.assertFalse(summary["recurring_automation_ready"])
            self.assertEqual(summary["research_only_daily_report"]["partial_successful_board_count"], 4)
            self.assertEqual(summary["research_only_daily_report"]["current_executable_new_stake_aud"], 0)
            self.assertTrue(summary["public_safety"]["partial_artifact_safety_ready"])
            self.assertIn("raw_refresh_blocked", {item["code"] for item in summary["blockers"]})
            report_path = output_dir / "automation_readiness_latest.md"
            write_automation_readiness_report(output_dir, report_path, summary=summary)
            markdown = report_path.read_text(encoding="utf-8")
            self.assertIn("research-only daily PDF", markdown)
            self.assertIn("current_discovery+partial_raw_success", markdown)
            pdf_path = output_dir / "automation_readiness_latest.pdf"
            pdf = write_automation_readiness_pdf(output_dir, pdf_path, summary=summary)
            self.assertTrue(pdf["research_only_daily_report_ready"])
            self.assertTrue(audit_public_artifact_safety([output_dir / "automation_readiness_latest.json", report_path, pdf_path])["public_artifact_safety_ready"])

    def test_automation_readiness_uses_pending_latest_commit_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            stale_run_id = "stale-run"
            pending_run_id = "pending-run"
            for run_id in [stale_run_id, pending_run_id]:
                for name in [
                    f"tab_fifa_bankroll_plan_01012026_{run_id}.json",
                    f"tab_fifa_dashboard_{run_id}.html",
                    f"tab_fifa_dashboard_data_{run_id}.json",
                    f"daily_report_manifest_{run_id}.json",
                    f"report_index_{run_id}.json",
                ]:
                    (output_dir / name).write_text('{"ok": true}', encoding="utf-8")
                SimpleDocTemplate(str(output_dir / f"01012026_{run_id}.pdf"), pagesize=A4).build(
                    [Paragraph("Public TAB FIFA report fixture", getSampleStyleSheet()["Normal"])]
                )
            atomic_write_json(
                output_dir / "latest_commit.json",
                {
                    "run_id": stale_run_id,
                    "report_date": "01012026",
                    "status": "ready_for_manual_report",
                    "technical_automation_ready": True,
                    "automation_entry_ready": False,
                    "public_artifact_safety_ready": True,
                    "ready_required_boards": "5/5",
                    "artifacts": {
                        "pdf_run_copy": f"01012026_{stale_run_id}.pdf",
                        "bankroll_plan_run_copy": f"tab_fifa_bankroll_plan_01012026_{stale_run_id}.json",
                        "dashboard_run_copy": f"tab_fifa_dashboard_{stale_run_id}.html",
                        "dashboard_data_run_copy": f"tab_fifa_dashboard_data_{stale_run_id}.json",
                        "manifest": f"daily_report_manifest_{stale_run_id}.json",
                    },
                    "run_artifacts": {
                        "pdf_run_copy": f"01012026_{stale_run_id}.pdf",
                        "bankroll_plan_run_copy": f"tab_fifa_bankroll_plan_01012026_{stale_run_id}.json",
                        "dashboard_run_copy": f"tab_fifa_dashboard_{stale_run_id}.html",
                        "dashboard_data_run_copy": f"tab_fifa_dashboard_data_{stale_run_id}.json",
                        "manifest": f"daily_report_manifest_{stale_run_id}.json",
                    },
                },
            )
            atomic_write_json(
                output_dir / "report_index_latest.json",
                {
                    "schema_version": 1,
                    "committed_latest_run_id": pending_run_id,
                    "latest_success_run_id": pending_run_id,
                    "run_count": 2,
                },
            )
            pending_commit = {
                "run_id": pending_run_id,
                "report_date": "01012026",
                "status": "ready_for_manual_report",
                "technical_automation_ready": True,
                "automation_entry_ready": False,
                "public_artifact_safety_ready": True,
                "ready_required_boards": "5/5",
                "artifacts": {
                    "pdf_run_copy": f"01012026_{pending_run_id}.pdf",
                    "bankroll_plan_run_copy": f"tab_fifa_bankroll_plan_01012026_{pending_run_id}.json",
                    "dashboard_run_copy": f"tab_fifa_dashboard_{pending_run_id}.html",
                    "dashboard_data_run_copy": f"tab_fifa_dashboard_data_{pending_run_id}.json",
                    "manifest": f"daily_report_manifest_{pending_run_id}.json",
                    "report_index": f"report_index_{pending_run_id}.json",
                },
                "run_artifacts": {
                    "pdf_run_copy": f"01012026_{pending_run_id}.pdf",
                    "bankroll_plan_run_copy": f"tab_fifa_bankroll_plan_01012026_{pending_run_id}.json",
                    "dashboard_run_copy": f"tab_fifa_dashboard_{pending_run_id}.html",
                    "dashboard_data_run_copy": f"tab_fifa_dashboard_data_{pending_run_id}.json",
                    "manifest": f"daily_report_manifest_{pending_run_id}.json",
                },
            }
            summary = write_automation_readiness_summary(
                output_dir,
                output_dir / "automation_readiness_latest.json",
                latest_commit_override=pending_commit,
            )
            self.assertEqual(summary["latest_commit"]["run_id"], pending_run_id)
            self.assertEqual(summary["report_index"]["latest_success_run_id"], pending_run_id)
            self.assertFalse(any(item["code"] == "report_index_inconsistent" for item in summary["blockers"]))
            self.assertNotIn(stale_run_id, json.dumps(summary["latest_commit"], ensure_ascii=False))

    def test_missing_data_logs_skip_automation_authorization_only(self):
        rows = build_missing_data_logs(
            public_sources={
                "sources": [
                    {"name": "FIFA", "ok": False, "missing_terms": ["team list missing"]},
                ]
            },
            event_monitor={"feeds": []},
            raw_refresh={"targets": []},
            preflight={
                "blocking_reasons": [
                    "user has not authorized recurring automation",
                    "raw refresh stale",
                ]
            },
            safety={"blocking_reasons": ["public artifact safety failed"]},
            portfolio={"board_statuses": []},
        )
        messages = [row["message"] for row in rows]
        self.assertNotIn("user has not authorized recurring automation", messages)
        self.assertIn("team list missing", messages)
        self.assertIn("raw refresh stale", messages)
        self.assertIn("public artifact safety failed", messages)

    def test_latest_runs_prefers_committed_run_dashboard_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "tab_fifa_reports.sqlite3"
            with connect_report_db(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO report_runs(
                        run_id, status, report_date, started_at, finished_at,
                        technical_ready, automation_entry_ready,
                        recommended_new_exposure_aud, time_adjusted_new_exposure_aud,
                        dashboard_path, summary_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "run-older",
                        "ready_for_manual_report",
                        "01012026",
                        "2026-01-01T00:00:00+00:00",
                        "2026-01-01T00:00:01+00:00",
                        1,
                        0,
                        0,
                        120,
                        "tab_fifa_dashboard_latest.html",
                        "{}",
                    ),
                )
                conn.execute(
                    "INSERT INTO artifacts(run_id, kind, path) VALUES (?, ?, ?)",
                    ("run-older", "dashboard_run_copy", "tab_fifa_dashboard_run-older.html"),
                )
                conn.commit()
            row = latest_runs(db_path, limit=1)[0]
            self.assertEqual(row["dashboard_path"], "tab_fifa_dashboard_run-older.html")

    def test_report_index_uses_latest_commit_as_success_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "tab_fifa_reports.sqlite3"
            with connect_report_db(db_path) as conn:
                for run_id, started_at, report_date in [
                    ("committed-run", "2026-01-01T00:00:00+00:00", "01012026"),
                    ("newer-legacy-ready", "2026-01-02T00:00:00+00:00", "02012026"),
                ]:
                    conn.execute(
                        """
                        INSERT INTO report_runs(
                            run_id, status, report_date, started_at, finished_at,
                            technical_ready, automation_entry_ready,
                            recommended_new_exposure_aud, time_adjusted_new_exposure_aud,
                            dashboard_path, summary_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run_id,
                            "ready_for_manual_report",
                            report_date,
                            started_at,
                            started_at,
                            1,
                            0,
                            0,
                            100,
                            f"tab_fifa_dashboard_{run_id}.html",
                            "{}",
                        ),
                    )
                conn.commit()
            index_path = root / "report_index_committed-run.json"
            index = write_report_index(
                db_path,
                root,
                index_path,
                latest_commit={
                    "run_id": "committed-run",
                    "report_date": "01012026",
                    "status": "ready_for_manual_report",
                    "technical_automation_ready": True,
                    "public_artifact_safety_ready": True,
                    "ready_required_boards": "5/5",
                },
            )
            self.assertEqual(index["committed_latest_run_id"], "committed-run")
            self.assertEqual(index["latest_success_run_id"], "committed-run")
            self.assertEqual(index["runs"][0]["run_id"], "newer-legacy-ready")
            self.assertTrue(index_path.exists())

    def test_model_comparison_open_source_layer(self):
        comparison = generate_model_comparison(full_matches_raw_fixture())
        self.assertTrue(comparison["ready"])
        self.assertEqual(comparison["match_count"], len(EXPECTED_MATCHES))
        self.assertEqual(comparison["model_count"], 3)
        self.assertEqual(comparison["model_dashboard"]["title"], "Open-source Model Dashboard")
        self.assertEqual(comparison["model_dashboard"]["decision"], "用于交叉验证，不单独触发下注")
        self.assertTrue(comparison["model_dashboard"]["github_source_audit_ready"])
        self.assertEqual(comparison["source_adoption"]["reference_count"], 6)
        self.assertEqual(comparison["source_adoption"]["implemented_reference_count"], 3)
        self.assertEqual(comparison["source_adoption"]["design_reference_count"], 3)
        self.assertIn("Monte Carlo", comparison["source_adoption"]["coverage_counts"])
        self.assertIn("评分规则", comparison["source_adoption"]["coverage_counts"])
        self.assertIn("Poisson比分矩阵", comparison["source_adoption"]["coverage_counts"])
        self.assertIn("No-vig implied probability", comparison["source_adoption"]["coverage_counts"])
        self.assertIn("xT", comparison["source_adoption"]["coverage_counts"])
        self.assertIn("World Cup 2026 schedule", comparison["source_adoption"]["coverage_counts"])
        self.assertTrue(any("Hicruben" in ref["name"] for ref in comparison["references"]))
        self.assertTrue(any("goalmodel" in ref["name"] for ref in comparison["references"]))
        self.assertTrue(any("RyanSCodes" in ref["name"] for ref in comparison["references"]))
        self.assertTrue(any("penaltyblog" in ref["name"] for ref in comparison["references"]))
        self.assertTrue(any("socceraction" in ref["name"] for ref in comparison["references"]))
        self.assertTrue(any("openfootball" in ref["name"] for ref in comparison["references"]))
        for row in comparison["source_adoption"]["rows"]:
            self.assertEqual(row["verified_at"], "2026-06-12")
            self.assertGreater(len(row["github_evidence"]), 0)
            self.assertGreater(len(row["reusable_features"]), 0)
            self.assertGreater(len(row["layout_patterns"]), 0)
        hicruben = next(row for row in comparison["source_adoption"]["rows"] if row["source"].startswith("Hicruben"))
        self.assertIn("48队赛事路径 Monte Carlo 接口", hicruben["reusable_features"])
        self.assertIn("Track record", hicruben["coverage"])
        goalmodel = next(row for row in comparison["source_adoption"]["rows"] if row["source"] == "opisthokonta/goalmodel")
        self.assertIn("同一 xG 分布同时驱动 1X2、OU、BTTS", goalmodel["reusable_features"])
        self.assertIn("Extra time offset", goalmodel["coverage"])
        penaltyblog = next(row for row in comparison["source_adoption"]["rows"] if row["source"] == "martineastwood/penaltyblog")
        self.assertIn("赔率去水和 overround removal 统一口径", penaltyblog["reusable_features"])
        self.assertIn("Asian Handicap", penaltyblog["coverage"])
        socceraction = next(row for row in comparison["source_adoption"]["rows"] if row["source"] == "ML-KULeuven/socceraction")
        self.assertIn("xT / VAEP 作为基本面强弱和伤停影响的解释层", socceraction["reusable_features"])
        openfootball = next(row for row in comparison["source_adoption"]["rows"] if row["source"] == "openfootball/worldcup.json")
        self.assertIn("2026 World Cup 赛程与阶段校验", openfootball["reusable_features"])
        self.assertIn("automation_view", comparison)
        self.assertTrue(comparison["automation_view"]["automation_view_ready"])
        self.assertIn("研究交叉验证层", comparison["automation_view"]["automation_role"])
        self.assertTrue(any(row["gate"] == "execution_unlock" and row["status"] == "blocked_by_design" for row in comparison["automation_view"]["gates"]))
        first = comparison["rows"][0]
        self.assertIn("current_market_poisson", first)
        self.assertIn("open_source_elo_dixon_coles", first)
        self.assertIn("goalmodel_market_dc_proxy", first)
        self.assertIn("consensus", first)
        probability_sum = (
            first["open_source_elo_dixon_coles"]["home_win"]
            + first["open_source_elo_dixon_coles"]["draw"]
            + first["open_source_elo_dixon_coles"]["away_win"]
        )
        self.assertAlmostEqual(probability_sum, 1.0, places=6)
        markdown = render_model_comparison_markdown(comparison)
        self.assertIn("## Open-source Model Dashboard", markdown)
        self.assertIn("## Visual Summary", markdown)
        self.assertIn("Model disagreement by match", markdown)
        self.assertIn("Consensus confidence mix", markdown)
        self.assertIn("Open-source capability coverage", markdown)
        self.assertIn("GitHub reference adoption mix", markdown)
        self.assertIn("Automation model gates", markdown)
        self.assertIn("## Automation 使用视角", markdown)
        self.assertIn("execution_unlock", markdown)
        self.assertIn("## GitHub Source Audit", markdown)
        self.assertGreaterEqual(markdown.count("```mermaid"), 6)
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / MODEL_COMPARISON_PDF
            pdf = write_model_comparison_pdf(comparison, pdf_path)
            self.assertEqual(pdf["chart_count"], 6)
            self.assertEqual(pdf["extra_table_count"], 4)
            self.assertEqual(pdf["detail_row_count"], 12)
            self.assertEqual(pdf["match_count"], len(EXPECTED_MATCHES))
            self.assertTrue(pdf_path.exists())
            self.assertTrue(audit_public_artifact_safety([pdf_path])["public_artifact_safety_ready"])
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            first_written = write_model_comparison(full_matches_raw_fixture(), output_dir)
            self.assertIn("old_new_compare", first_written)
            self.assertEqual(first_written["old_new_compare"]["status"], "no_previous_artifact")
            self.assertEqual(first_written["artifacts"]["json"], MODEL_COMPARISON_JSON)
            self.assertEqual(first_written["artifacts"]["pdf_summary"]["chart_count"], 6)
            self.assertEqual(json.loads((output_dir / MODEL_COMPARISON_JSON).read_text(encoding="utf-8"))["artifacts"]["pdf_summary"]["chart_count"], 6)
            self.assertEqual(first_written["pdf_summary"]["extra_table_count"], 5)
            self.assertIn("Automation 使用视角", (output_dir / MODEL_COMPARISON_MD).read_text(encoding="utf-8"))
            self.assertIn("新旧模型变化", (output_dir / MODEL_COMPARISON_MD).read_text(encoding="utf-8"))
            second_written = write_model_comparison(full_matches_raw_fixture(), output_dir)
            self.assertEqual(second_written["old_new_compare"]["status"], "compared_with_previous_artifact")
            self.assertEqual(second_written["old_new_compare"]["changed_count"], 0)
            self.assertTrue(audit_public_artifact_safety([output_dir / MODEL_COMPARISON_JSON, output_dir / MODEL_COMPARISON_MD, output_dir / MODEL_COMPARISON_PDF])["public_artifact_safety_ready"])

    def test_match_recommendations_include_model_divergence_reason(self):
        comparison = generate_model_comparison(full_matches_raw_fixture())
        payload = {
            "version": "test",
            "recommendations": [
                {
                    "match": "Brazil v Morocco",
                    "market": "Result",
                    "selection": "Morocco",
                    "odds": 5.5,
                    "model_probability": 0.22,
                    "expected_value": 0.2,
                    "stake_aud": 40,
                    "rationale": "fixture edge",
                }
            ],
        }
        enriched = enrich_match_recommendations_with_model_comparison(payload, comparison)
        item = enriched["recommendations"][0]
        self.assertIn("model_signal", item)
        self.assertIn("模型交叉验证", item["rationale"])
        self.assertIn("三模型概率", item["model_signal"]["summary_zh"])
        self.assertIn("open_source_elo_dixon_coles", item["model_signal"]["probabilities"])

    def test_recommendation_model_calibration_maps_open_source_comparison(self):
        comparison = generate_model_comparison(full_matches_raw_fixture())
        model_index = {row["match"]: row for row in comparison["rows"]}
        calibration = model_calibration_for_recommendation(
            event="Brazil v Morocco",
            market="Result",
            selection="Morocco",
            probability=0.22,
            model_index=model_index,
        )
        self.assertEqual(calibration["status"], "model_linked")
        self.assertEqual(calibration["selection_alignment"], "against_consensus")
        self.assertEqual(calibration["consistency_label"], "逆共识价值复核")
        self.assertIn(calibration["review_priority"], {"中", "高"})
        self.assertIn("复核", calibration["review_action"])
        self.assertIn("开源模型共识", calibration["evidence_text"])

        goals_calibration = model_calibration_for_recommendation(
            event="Brazil v Morocco",
            market="Total Goals Over/Under",
            selection="Under 2.5 Goals",
            probability=0.57,
            model_index=model_index,
        )
        self.assertEqual(goals_calibration["market_model_key"], "under_2_5")
        self.assertEqual(goals_calibration["selection_alignment"], "market_probability_supported")
        self.assertIn(goals_calibration["consistency_label"], {"模型一致-强", "模型一致-中", "模型一致-低置信", "模型概率偏离"})

    def test_model_comparison_maps_result_prices_by_team_name(self):
        match = full_match_fixture("Mexico v South Africa")
        match["markets"]["Result"] = "Result\nDraw\n3.20\nSouth Africa\n3.80\nMexico\n2.00\n"
        row = compare_match_models(match)
        self.assertEqual(row["home"], "Mexico")
        self.assertEqual(row["away"], "South Africa")
        self.assertGreater(row["market_no_vig"]["home_win"], row["market_no_vig"]["away_win"])

    def test_latest_commit_payload_is_atomic_public_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit_path = root / "latest_commit.json"
            manifest = {
                "run_id": "run-123",
                "report_date": "01012026",
                "status": "ready_for_manual_report",
                "technical_automation_ready": True,
                "automation_entry_ready": False,
                "user_automation_authorized": False,
                "automation_authorization": {
                    "authorized": False,
                    "allow_recurring": False,
                    "allow_auto_betting": False,
                    "entry_authorized": False,
                    "blocking_reasons": ["user has not authorized recurring automation"],
                },
            }
            response = {
                "ready_required_boards": "5/5",
                "time_adjusted_new_exposure_aud": 120,
                "pdf_run_copy": str(root / "01012026_run-123.pdf"),
                "bankroll_plan_run_copy": str(root / "tab_fifa_bankroll_plan_01012026_run-123.json"),
                "dashboard_run_copy": str(root / "tab_fifa_dashboard_run-123.html"),
                "dashboard_data_run_copy": str(root / "tab_fifa_dashboard_data_run-123.json"),
                "manifest": str(root / "daily_report_manifest_run-123.json"),
                "public_artifact_safety": {"public_artifact_safety_ready": True},
            }
            latest_artifacts = {
                "dashboard": root / "tab_fifa_dashboard_latest.html",
                "daily_report_manifest_latest": root / "daily_report_manifest_latest.json",
                "report_database": root / "tab_fifa_reports.sqlite3",
            }
            payload = latest_commit_payload(manifest, response, latest_artifacts)
            serialized = json.dumps(payload, ensure_ascii=False)
            self.assertEqual(payload["run_id"], "run-123")
            self.assertEqual(payload["artifacts"]["dashboard"], "tab_fifa_dashboard_latest.html")
            self.assertEqual(payload["run_artifacts"]["pdf_run_copy"], "01012026_run-123.pdf")
            self.assertEqual(latest_commit_artifact_consistency_issues(payload), [])
            self.assertFalse(payload["automation_authorization"]["authorized"])
            self.assertFalse(payload["automation_authorization"]["allow_auto_betting"])
            self.assertNotIn(str(root), serialized)
            publish_latest_commit(manifest, response, latest_artifacts, path=commit_path)
            written = json.loads(commit_path.read_text(encoding="utf-8"))
            self.assertEqual(written["run_id"], "run-123")
            self.assertEqual(written["artifacts"]["report_database"], "tab_fifa_reports.sqlite3")

    def test_latest_commit_consistency_rejects_run_key_pointing_to_latest_artifact(self):
        payload = {
            "run_id": "run-123",
            "artifacts": {
                "automation_preflight": "automation_preflight_latest.json",
                "pdf_qa": "pdf_qa_run-123.json",
            },
            "run_artifacts": {
                "pdf_run_copy": "01012026_run-123.pdf",
                "bankroll_plan_run_copy": "tab_fifa_bankroll_plan_01012026_run-123.json",
                "dashboard_run_copy": "tab_fifa_dashboard_run-123.html",
                "dashboard_data_run_copy": "tab_fifa_dashboard_data_run-123.json",
                "manifest": "daily_report_manifest_run-123.json",
            },
        }
        issues = latest_commit_artifact_consistency_issues(payload)
        self.assertTrue(any("automation_preflight" in issue and "latest artifact" in issue for issue in issues), issues)

    def test_convenience_latest_publish_is_non_blocking_after_commit_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            pdf_run = output_dir / "01012026_run-123.pdf"
            bankroll_run = output_dir / "tab_fifa_bankroll_plan_01012026_run-123.json"
            dashboard_run = output_dir / "tab_fifa_dashboard_run-123.html"
            dashboard_data_run = output_dir / "tab_fifa_dashboard_data_run-123.json"
            for path, text in [
                (pdf_run, "%PDF fixture"),
                (bankroll_run, '{"time_adjusted_new_exposure_aud": 120}'),
                (dashboard_run, "<html>run dashboard</html>"),
                (dashboard_data_run, '{"run_id": "run-123"}'),
                (output_dir / "previous_report_baseline_test.json", '{"version": "test"}'),
                (output_dir / "portfolio_report_baseline_test.json", '{"version": "test"}'),
                (output_dir / "portfolio_daily_compare_test.json", '{"summary": {}}'),
            ]:
                path.write_text(text, encoding="utf-8")
            result = publish_convenience_latest_artifacts(
                pdf_run_copy=pdf_run,
                bankroll_run_copy=bankroll_run,
                dashboard_run_copy=dashboard_run,
                dashboard_data_run_copy=dashboard_data_run,
                output_pdf=output_dir / "01012026.pdf",
                output_bankroll=output_dir / "tab_fifa_bankroll_plan_01012026.json",
                version="test",
                output_dir=output_dir,
            )
            self.assertTrue(result["ready"], result)
            self.assertTrue((output_dir / "01012026.pdf").exists())
            self.assertTrue((output_dir / "tab_fifa_dashboard_latest.html").exists())
            self.assertTrue((output_dir / "tab_fifa_dashboard_data_latest.json").exists())

            failed = publish_convenience_latest_artifacts(
                pdf_run_copy=output_dir / "missing.pdf",
                bankroll_run_copy=bankroll_run,
                dashboard_run_copy=dashboard_run,
                dashboard_data_run_copy=dashboard_data_run,
                output_pdf=output_dir / "missing-latest.pdf",
                output_bankroll=output_dir / "tab_fifa_bankroll_plan_01012026.json",
                version="test",
                output_dir=output_dir,
            )
            self.assertFalse(failed["ready"])
            self.assertTrue(any(error["artifact"] == "pdf_latest_copy" for error in failed["errors"]))

    def test_daily_report_latest_commit_is_final_success_pointer(self):
        source = (ROOT / "run_daily_report.py").read_text(encoding="utf-8")
        technical_gate_idx = source.index("technical automation preflight failed; refusing to publish latest artifacts")
        db_idx = source.index("final_db_summary = store_daily_run")
        report_index_payload_idx = source.index("report_index_commit_payload = latest_commit_payload(manifest, response, public_artifacts_to_publish)")
        report_index_idx = source.index("write_report_index(REPORT_DB, OUT, report_index_path, latest_commit=report_index_commit_payload)")
        readiness_override_idx = source.index("latest_commit_override=readiness_commit_payload")
        readiness_safety_idx = source.index("readiness_safety = audit_public_artifact_safety([AUTOMATION_READINESS_PATH, AUTOMATION_READINESS_REPORT_PATH, AUTOMATION_READINESS_PDF_PATH])")
        report_intelligence_idx = source.index("report_intelligence = write_report_intelligence_bundle")
        report_intelligence_artifact_idx = source.index('public_artifacts_to_publish["report_intelligence"] = report_intelligence_path')
        final_safety_idx = source.index("final_artifact_safety = audit_public_artifact_safety(public_artifacts_to_publish.values())")
        commit_idx = source.index("publish_latest_commit(manifest, response, commit_artifacts)")
        post_commit_research_idx = source.index("recommendation_operations = write_recommendation_operations_bundle")
        model_divergence_review_idx = source.index("model_divergence_review = write_model_divergence_review_bundle")
        convenience_idx = source.index("convenience_latest = publish_convenience_latest_artifacts")
        intelligence_latest_idx = source.index('("report_intelligence_latest", report_intelligence_path, REPORT_INTELLIGENCE_LATEST_PATH)')
        post_commit_latest_idx = source.index("post_commit_latest_publish")
        print_idx = source.index("print(json.dumps(sanitize_public_manifest(response), indent=2))")
        self.assertLess(technical_gate_idx, db_idx)
        self.assertLess(report_index_payload_idx, report_index_idx)
        self.assertLess(report_index_idx, readiness_override_idx)
        self.assertLess(readiness_override_idx, readiness_safety_idx)
        self.assertLess(readiness_safety_idx, report_intelligence_idx)
        self.assertLess(report_intelligence_idx, report_intelligence_artifact_idx)
        self.assertLess(report_intelligence_artifact_idx, final_safety_idx)
        self.assertLess(readiness_safety_idx, final_safety_idx)
        self.assertLess(final_safety_idx, commit_idx)
        self.assertLess(commit_idx, convenience_idx)
        self.assertLess(convenience_idx, intelligence_latest_idx)
        self.assertLess(intelligence_latest_idx, post_commit_latest_idx)
        self.assertLess(post_commit_latest_idx, post_commit_research_idx)
        self.assertLess(post_commit_research_idx, model_divergence_review_idx)
        self.assertLess(model_divergence_review_idx, print_idx)
        self.assertLess(convenience_idx, post_commit_latest_idx)
        self.assertLess(post_commit_latest_idx, print_idx)

    def test_report_store_migrates_v1_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "tab_fifa_reports.sqlite3"
            with sqlite3.connect(db_path) as conn:
                conn.executescript(
                    """
                    CREATE TABLE schema_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    INSERT INTO schema_meta(key, value) VALUES('schema_version', '1');
                    CREATE TABLE report_runs(
                        run_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        report_date TEXT,
                        started_at TEXT,
                        finished_at TEXT,
                        technical_ready INTEGER NOT NULL DEFAULT 0,
                        automation_entry_ready INTEGER NOT NULL DEFAULT 0,
                        raw_refresh_ready INTEGER NOT NULL DEFAULT 0,
                        safety_ready INTEGER NOT NULL DEFAULT 0,
                        portfolio_ready INTEGER NOT NULL DEFAULT 0,
                        recommended_new_exposure_aud REAL NOT NULL DEFAULT 0,
                        pdf_report TEXT,
                        pdf_output_copy TEXT,
                        dashboard_path TEXT,
                        dashboard_data_path TEXT,
                        manifest_path TEXT,
                        summary_json TEXT NOT NULL
                    );
                    CREATE TABLE artifacts(
                        run_id TEXT NOT NULL,
                        kind TEXT NOT NULL
                    );
                    INSERT INTO artifacts(run_id, kind) VALUES('old-run', 'dashboard');
                    INSERT INTO artifacts(run_id, kind) VALUES('old-run', 'dashboard');
                    CREATE TABLE model_comparisons(
                        run_id TEXT NOT NULL,
                        match_name TEXT NOT NULL
                    );
                    INSERT INTO model_comparisons(run_id, match_name) VALUES('old-run', 'A v B');
                    INSERT INTO model_comparisons(run_id, match_name) VALUES('old-run', 'A v B');
                    CREATE TABLE visual_snapshots(
                        run_id TEXT NOT NULL,
                        chart_id TEXT NOT NULL
                    );
                    INSERT INTO visual_snapshots(run_id, chart_id) VALUES('old-run', 'board_readiness');
                    INSERT INTO visual_snapshots(run_id, chart_id) VALUES('old-run', 'board_readiness');
                    CREATE TABLE board_diffs(
                        run_id TEXT NOT NULL,
                        board_id TEXT NOT NULL
                    );
                    INSERT INTO board_diffs(run_id, board_id) VALUES('old-run', 'world_cup_matches');
                    INSERT INTO board_diffs(run_id, board_id) VALUES('old-run', 'world_cup_matches');
                    """
                )
            with connect_report_db(db_path) as conn:
                columns = {row["name"] for row in conn.execute("PRAGMA table_info(report_runs)").fetchall()}
                self.assertIn("time_adjusted_new_exposure_aud", columns)
                artifact_columns = {row["name"] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()}
                self.assertIn("path", artifact_columns)
                model_columns = {row["name"] for row in conn.execute("PRAGMA table_info(model_comparisons)").fetchall()}
                self.assertIn("consensus_selection", model_columns)
                self.assertIn("raw_json", model_columns)
                visual_columns = {row["name"] for row in conn.execute("PRAGMA table_info(visual_snapshots)").fetchall()}
                self.assertIn("title", visual_columns)
                board_diff_columns = {row["name"] for row in conn.execute("PRAGMA table_info(board_diffs)").fetchall()}
                self.assertIn("exposure_change_aud", board_diff_columns)
                visual_tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visual_snapshots'").fetchall()
                self.assertEqual(len(visual_tables), 1)
                board_diff_tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='board_diffs'").fetchall()
                self.assertEqual(len(board_diff_tables), 1)
                version = conn.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'").fetchone()["value"]
                self.assertEqual(version, "10")
                for table_name in [
                    "source_logs",
                    "audit_logs",
                    "decision_records",
                    "missing_data_logs",
                    "manual_review_queue",
                    "automation_runs",
                    "active_timeline_audits",
                    "available_board_strategy_snapshots",
                    "position_monitor_snapshots",
                ]:
                    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchall()
                    self.assertEqual(len(tables), 1)
                artifact_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(artifacts)").fetchall()}
                self.assertIn("idx_artifacts_run_kind", artifact_indexes)
                model_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(model_comparisons)").fetchall()}
                self.assertIn("idx_model_comparisons_run_match", model_indexes)
                visual_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(visual_snapshots)").fetchall()}
                self.assertIn("idx_visual_snapshots_run_chart", visual_indexes)
                board_diff_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(board_diffs)").fetchall()}
                self.assertIn("idx_board_diffs_run_board", board_diff_indexes)
                active_timeline_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(active_timeline_audits)").fetchall()}
                self.assertIn("idx_active_timeline_audits_audit", active_timeline_indexes)
                available_board_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(available_board_strategy_snapshots)").fetchall()}
                self.assertIn("idx_available_board_strategy_id", available_board_indexes)
                position_monitor_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(position_monitor_snapshots)").fetchall()}
                self.assertIn("idx_position_monitor_id", position_monitor_indexes)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM artifacts WHERE run_id = 'old-run' AND kind = 'dashboard'").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM model_comparisons WHERE run_id = 'old-run' AND match_name = 'A v B'").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM visual_snapshots WHERE run_id = 'old-run' AND chart_id = 'board_readiness'").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM board_diffs WHERE run_id = 'old-run' AND board_id = 'world_cup_matches'").fetchone()[0], 1)

    def test_public_bankroll_summary_omits_private_detail_flags(self):
        summary = {
            "report_date": "01012026",
            "pdf_output_copy": "out.pdf",
            "positions_ready": True,
            "base_selected_exposure_aud": 0,
            "time_adjusted_new_exposure_aud": 0,
            "match_stakes": [
                {
                    "match": "A v B",
                    "market": "Result",
                    "selection": "A",
                    "time_adjusted_stake_aud": 120,
                }
            ],
        }
        public = public_bankroll_summary(summary)
        self.assertNotIn("positions_ready", public)
        self.assertNotIn("private_detail_available", public)
        self.assertNotIn("match_stakes", public)
        self.assertEqual(public["match_candidate_count"], 1)

    def test_board_registry_matches_readonly_refresh_script(self):
        script = (ROOT / "scripts" / "refresh_tab_readonly.mjs").read_text(encoding="utf-8")
        registry = board_registry()
        self.assertEqual(len(registry), 5)
        for board in registry:
            self.assertIn(board["version"], board["recommendations_artifact"])
            self.assertIn(board["version"], board["gate_artifact"])
            self.assertIn(board["version"], board["report_artifact"])
            self.assertIn(board["refresh_board_id"], script)
            self.assertIn(board["raw_snapshot"], script)
            self.assertIn("https://www.tab.com.au" + board["tab_path"], script)
            self.assertEqual(refresh_driver(type("BoardLike", (), board)), f"scripts/refresh_tab_readonly.mjs --board {board['refresh_board_id']}")

    def test_daily_board_registry_covers_required_boards(self):
        self.assertEqual(missing_runner_board_ids(), [])
        ready_gate = {"automation_ready": True, "manual_report_ready": True, "public_sources": {"ready": True}, "event_monitor": {"ready": True}}
        results = {
            "world_cup_matches": {"version": "test", "automation_gate": ready_gate, "recommended_new_exposure_aud": 80, "recommendations": [{}, {}]},
            "world_cup_futures": {"version": "test", "automation_gate": ready_gate, "recommendations": [{}]},
            "world_cup_group_betting": {"version": "test", "automation_gate": ready_gate, "recommendations": [{}]},
            "world_cup_australia_markets": {"version": "test", "automation_gate": ready_gate, "recommendations": []},
            "world_cup_team_futures_multi": {"version": "test", "automation_gate": ready_gate, "recommendations": [{}]},
        }
        metrics = response_metrics(results)
        self.assertTrue(metrics["automation_ready"])
        self.assertEqual(metrics["recommendations"], 2)
        self.assertEqual(metrics["recommended_new_exposure_aud"], 80)
        self.assertTrue(metrics["futures_automation_ready"])
        self.assertTrue(metrics["group_betting_automation_ready"])
        self.assertTrue(metrics["australia_markets_manual_report_ready"])
        self.assertIn("world_cup_team_futures_multi", metrics["board_results"])

    def test_portfolio_gate_distinguishes_single_board_from_full_system(self):
        boards = [
            BoardConfig(
                board_id="test_board_one",
                refresh_board_id="test_one",
                name="Test Board One",
                tab_path="/sports/test/one",
                priority=1,
                version="test",
                required_for_full_automation=True,
                parser_strategy="test",
                refresh_method="test",
                raw_snapshot="one_raw.json",
                recommendations_artifact="one_recommendations.json",
                gate_artifact="one_gate.json",
                report_artifact="one_report.md",
            ),
            BoardConfig(
                board_id="test_board_two",
                refresh_board_id="test_two",
                name="Test Board Two",
                tab_path="/sports/test/two",
                priority=2,
                version="test",
                required_for_full_automation=True,
                parser_strategy="test",
                refresh_method="test",
                raw_snapshot="two_raw.json",
                recommendations_artifact="two_recommendations.json",
                gate_artifact="two_gate.json",
                report_artifact="two_report.md",
            ),
        ]
        fixed_now = datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            for board in boards:
                (output_dir / board.raw_snapshot).write_text('{"generated_at": "2026-06-03T00:00:00Z"}', encoding="utf-8")
                (output_dir / board.gate_artifact).write_text('{"automation_ready": true}', encoding="utf-8")
                (output_dir / board.report_artifact).write_text("ready", encoding="utf-8")
            portfolio = audit_portfolio(output_dir, boards=boards, now=fixed_now)
            self.assertTrue(portfolio["portfolio_automation_ready"])
            self.assertEqual(portfolio["ready_required_board_count"], 2)
            self.assertEqual(len(portfolio["blocking_reasons"]), 0)
            markdown = render_portfolio_markdown(portfolio)
            self.assertIn("Test Board Two", markdown)

            first_gate = output_dir / boards[0].gate_artifact
            first_gate.write_text('{"automation_ready": false}', encoding="utf-8")
            blocked = audit_portfolio(output_dir, boards=boards, now=fixed_now)
            self.assertFalse(blocked["portfolio_automation_ready"])
            self.assertEqual(blocked["ready_required_board_count"], 1)

            first_gate.write_text('{"automation_ready": true}', encoding="utf-8")
            first_raw = output_dir / boards[0].raw_snapshot
            first_raw.write_text('{"generated_at": "2026-06-03T02:00:00Z"}', encoding="utf-8")
            future_raw = audit_portfolio(output_dir, boards=boards, now=fixed_now)
            self.assertFalse(future_raw["portfolio_automation_ready"])
            self.assertIn("raw_snapshot_fresh", future_raw["board_statuses"][0]["missing"])

            first_raw.write_text("{not valid json", encoding="utf-8")
            malformed = audit_portfolio(output_dir, boards=boards, now=fixed_now)
            self.assertFalse(malformed["portfolio_automation_ready"])
            self.assertIn("raw_snapshot_parseable", malformed["board_statuses"][0]["missing"])
            self.assertIn("JSONDecodeError", malformed["board_statuses"][0]["raw_parse_error"])

    def test_portfolio_gate_validates_real_board_raw_content(self):
        fixed_now = datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc)
        board = board_by_id("world_cup_matches")
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            (output_dir / board.raw_snapshot).write_text('{"generated_at": "2026-06-03T00:00:00Z", "matches": []}', encoding="utf-8")
            (output_dir / board.gate_artifact).write_text('{"automation_ready": true}', encoding="utf-8")
            (output_dir / board.report_artifact).write_text("ready", encoding="utf-8")
            portfolio = audit_portfolio(output_dir, boards=[board], now=fixed_now)
            self.assertFalse(portfolio["portfolio_automation_ready"])
            self.assertIn("raw_snapshot_valid", portfolio["board_statuses"][0]["missing"])
            self.assertTrue(portfolio["board_statuses"][0]["raw_validation_errors"])

    def test_futures_multi_slot_no_vig_probabilities(self):
        rows = [
            {"team": "A", "markets": {"To Qualify for Quarter Final": 2.0}},
            {"team": "B", "markets": {"To Qualify for Quarter Final": 2.0}},
            {"team": "C", "markets": {"To Qualify for Quarter Final": 4.0}},
            {"team": "D", "markets": {"To Qualify for Quarter Final": 4.0}},
        ]
        probs = no_vig_market_probabilities(rows, "To Qualify for Quarter Final")
        self.assertAlmostEqual(sum(probs.values()), 8.0)

    def test_futures_gate_blocks_invalid_decimal_odds(self):
        rows = [
            {"team": team, "markets": {market: 2.0 + index * 0.05 for market in FUTURES_CORE_MARKETS}}
            for index, team in enumerate(FUTURES_EXPECTED_TEAMS)
        ]
        rows[0]["markets"]["Winner"] = float("inf")
        gate = futures_gate(rows, {})
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("Invalid decimal odds" in reason for reason in gate["blocking_reasons"]))

    def test_collapsed_futures_winner_market_parses_but_keeps_gate_blocked(self):
        rows = parse_core_futures(collapsed_futures_winner_text_fixture())
        self.assertGreaterEqual(len(rows), 12)
        australia = next(row for row in rows if row["team"] == "Australia")
        self.assertEqual(australia["markets"], {"Winner": 401.0})
        gate = futures_gate(rows, {})
        self.assertFalse(gate["automation_ready"])
        self.assertFalse(gate["manual_report_ready"])
        self.assertTrue(any("complete futures rows" in reason for reason in gate["blocking_reasons"]))
        self.assertTrue(any("Missing futures teams" in reason for reason in gate["blocking_reasons"]))
        self.assertFalse(any("Invalid decimal odds" in reason for reason in gate["blocking_reasons"]))

    def test_detail_futures_winner_market_parses_48_team_detail_format(self):
        rows = parse_core_futures(detail_futures_winner_text_fixture())
        self.assertEqual(len(rows), 48)
        self.assertEqual(rows[0]["team"], "Australia")
        self.assertEqual(rows[-1]["team"], "Haiti")
        self.assertTrue(all(set(row["markets"]) == {"Winner"} for row in rows))
        gate = futures_gate(rows, {})
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(gate["manual_report_ready"])
        self.assertEqual(gate["coverage"]["core_markets"], {"covered": 1, "total": 4})
        self.assertFalse(any("Expected 48 teams" in reason for reason in gate["blocking_reasons"]))
        self.assertTrue(any("complete futures rows" in reason for reason in gate["blocking_reasons"]))

    def test_current_futures_detail_markets_can_pass_current_market_gate(self):
        text = current_futures_detail_text_fixture()
        rows = parse_core_futures(text)
        current = parse_current_detail_markets(text)
        self.assertEqual(len(rows), 48)
        self.assertEqual(len(current["stage_of_elimination"]), 36)
        self.assertEqual(len(current["team_tournament_goals_ou"]), 40)
        self.assertEqual(len(current["player_tournament_goals_ou"]), 17)
        self.assertTrue(all(len(row["outcomes"]) == 7 for row in current["stage_of_elimination"]))

        gate = futures_gate(rows, {"text": text})
        self.assertTrue(gate["automation_ready"], gate["blocking_reasons"])
        self.assertTrue(gate["manual_report_ready"])
        self.assertEqual(gate["coverage"]["current_detail_markets"]["stage_of_elimination"]["covered"], 36)
        self.assertEqual(gate["coverage"]["current_detail_markets"]["team_tournament_goals_ou"]["covered"], 40)
        self.assertEqual(gate["coverage"]["current_detail_markets"]["player_tournament_goals_ou"]["covered"], 17)
        self.assertIn("Stage of Elimination", gate["coverage"]["current_detail_markets"]["parsed_market_names"])
        self.assertTrue(gate["availability_notes"])
        self.assertFalse(any("complete futures rows" in reason for reason in gate["blocking_reasons"]))

    def test_collapsed_futures_report_renders_missing_markets_as_na(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            raw_path = output_dir / "tab_fifa_world_cup_futures_raw_v0_13.json"
            atomic_write_json(
                raw_path,
                {
                    "generated_at": "2026-06-13T00:00:00Z",
                    "board": "2026 World Cup Futures",
                    "url": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures",
                    "text": collapsed_futures_winner_text_fixture(),
                    "futures_market_coverage": {
                        "status": "winner_market_visible",
                        "partial_winner_market_visible": True,
                    },
                },
            )
            result = generate_futures_report(raw_path, output_dir)
            self.assertFalse(result["automation_gate"]["automation_ready"])
            self.assertIn("Winner", result["probabilities"])
            self.assertEqual(result["probabilities"]["To Qualify for Quarter Final"], {})
            report = (output_dir / "tab_fifa_world_cup_futures_v0_13_report.md").read_text(encoding="utf-8")
            self.assertIn("| Australia | 401.00 | n/a | n/a | n/a |", report)
            self.assertIn("Expected 48 complete futures rows", report)

    def test_group_winner_parser(self):
        text = group_betting_text_fixture()
        groups = parse_group_winners(text)
        self.assertEqual(len(groups), 12)
        self.assertTrue(all(len(group["rows"]) == 4 for group in groups))
        group_f = next(group for group in groups if group["group"] == "F")
        self.assertIn("Japan", group_f["probabilities"])

    def test_group_gate_requires_roster_consistency(self):
        groups = parse_group_winners(group_betting_text_fixture())
        self.assertTrue(group_gate(groups)["automation_ready"])
        group_f = next(group for group in groups if group["group"] == "F")
        group_f["rows"][3] = {"team": "Japan", "odds": 9.0}
        group_f["probabilities"] = {}
        gate = group_gate(groups)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("Group F duplicate teams" in reason for reason in gate["blocking_reasons"]))
        self.assertTrue(any("Group F roster mismatch" in reason for reason in gate["blocking_reasons"]))

    def test_group_gate_accepts_tab_code_roster_hints(self):
        text = """World Cup Group A (MEX/CZE/KOR/RSA)
7 Markets
WC26 Group A WinnerFri 12 Jun 5:00
Mexico
1.85
Korea Republic
4.00
Czechia
4.25
South Africa
13.00
"""
        groups = parse_group_winners(text)
        gate = group_gate(groups)
        self.assertFalse(any("roster mismatch" in reason for reason in gate["blocking_reasons"]))
        self.assertFalse(any("duplicate teams" in reason for reason in gate["blocking_reasons"]))

    def test_group_gate_marks_missing_current_group_as_unavailable_not_blocking(self):
        text = group_betting_text_fixture()
        text = re.sub(
            r"World Cup Group D \([^)]+\)\n1 Market\nWC26 Group D Winner\n(?:Team D[1-4]\n\d+\.\d+\n?){4}",
            "",
            text,
        )
        groups = parse_group_winners(text)
        gate = group_gate(groups)
        self.assertEqual(len(groups), 11)
        self.assertTrue(gate["automation_ready"], gate)
        self.assertEqual(gate["coverage"]["unavailable_groups"], ["D"])
        self.assertTrue(any("Group D is not listed" in note for note in gate["availability_notes"]))
        self.assertFalse(any("Missing groups" in reason for reason in gate["blocking_reasons"]))

    def test_group_gate_blocks_invalid_decimal_odds(self):
        groups = parse_group_winners(group_betting_text_fixture())
        self.assertTrue(group_gate(groups)["automation_ready"])
        groups[0]["rows"][0]["odds"] = 1.0
        gate = group_gate(groups)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("invalid decimal odds" in reason for reason in gate["blocking_reasons"]))

    def test_australia_markets_parser_reads_expanded_markets(self):
        markets = parse_australia_raw(australia_raw_fixture())
        self.assertEqual(len(markets), 14)
        priced = [market for market in markets if market["status"] == "priced"]
        self.assertEqual(len(priced), 14)
        self.assertEqual(priced[0]["market"], "AUS Group Match Wins")
        self.assertEqual(len(priced[0]["rows"]), 4)
        top_scorer = next(market for market in markets if market["market"] == "Top Australian Goalscorer")
        self.assertGreaterEqual(len(top_scorer["rows"]), 18)
        self.assertEqual(top_scorer["probability_method"], "displayed_subset_no_vig")

    def test_australia_gate_blocks_invalid_decimal_odds(self):
        markets = australia_gate_markets_fixture()
        self.assertTrue(australia_gate(markets)["automation_ready"])
        markets[0]["rows"][0]["odds"] = float("nan")
        gate = australia_gate(markets)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("invalid decimal odds" in reason for reason in gate["blocking_reasons"]))

    def test_team_futures_multi_parser(self):
        text = team_futures_multi_text_fixture()
        rows = parse_team_futures_multi(text)
        self.assertEqual(len(rows), 14)
        self.assertTrue(all(len(row["markets"]) == 4 for row in rows))
        japan = next(row for row in rows if row["team"] == "Japan")
        self.assertEqual(japan["markets"]["Reach Quarter Final"], 3.75)
        probs = team_multi_no_vig(rows, "Reach Quarter Final")
        self.assertAlmostEqual(sum(probs.values()), 8.0)

    def test_team_futures_multi_gate_requires_expected_codes(self):
        rows = [
            {"code": code, "team": code, "markets": {market: 2.0 for market in TEAM_MULTI_MARKETS}}
            for code in TEAM_MULTI_EXPECTED_CODES
        ]
        self.assertTrue(team_multi_gate(rows)["automation_ready"])
        rows[-1] = {"code": "XYZ", "team": "XYZ", "markets": {market: 2.0 for market in TEAM_MULTI_MARKETS}}
        gate = team_multi_gate(rows)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("Missing team futures multi codes" in reason for reason in gate["blocking_reasons"]))
        self.assertTrue(any("Unknown team futures multi codes" in reason for reason in gate["blocking_reasons"]))

    def test_team_futures_multi_gate_blocks_invalid_decimal_odds(self):
        rows = [
            {"code": code, "team": code, "markets": {market: 2.0 for market in TEAM_MULTI_MARKETS}}
            for code in TEAM_MULTI_EXPECTED_CODES
        ]
        self.assertTrue(team_multi_gate(rows)["automation_ready"])
        rows[0]["markets"]["Reach Final"] = 0
        gate = team_multi_gate(rows)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("Invalid decimal odds" in reason for reason in gate["blocking_reasons"]))

    def test_futures_gate_requires_expected_team_names(self):
        rows = [
            {"team": team, "markets": {market: 2.0 for market in FUTURES_CORE_MARKETS}}
            for team in FUTURES_EXPECTED_TEAMS
        ]
        self.assertTrue(futures_gate(rows, {})["automation_ready"])
        rows[-1] = {"team": "Atlantis", "markets": {market: 2.0 for market in FUTURES_CORE_MARKETS}}
        gate = futures_gate(rows, {})
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("Missing futures teams" in reason for reason in gate["blocking_reasons"]))
        self.assertTrue(any("Unknown futures teams" in reason for reason in gate["blocking_reasons"]))

    def test_my_bets_parser_and_summary(self):
        text = sample_my_bets_text().replace("Won\nGermany", "Pending\nGermany")
        bets = parse_my_bets_text(text)
        self.assertEqual(len(bets), 2)
        self.assertEqual(bets[0]["selection"], "Spain")
        self.assertEqual(bets[1]["stake_aud"], 500.0)
        snapshot = build_snapshot(text, source_url="https://www.tab.com.au/accounts/my-bets/bets", scraped_at="2026-06-03T00:00:00Z")
        self.assertEqual(snapshot["summary"]["bet_count"], 2)
        self.assertEqual(snapshot["summary"]["open_stake_aud"], 600.0)
        self.assertEqual(snapshot["summary"]["potential_profit_if_all_win_aud"], 23.0)
        self.assertFalse(any("raw_lines" in bet for bet in snapshot["bets"]))
        self.assertEqual(validate_snapshot(snapshot), [])

    def test_workspace_root_resolver_handles_local_workspace_and_github_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local_workspace = root / "files-mentioned-by-the-user-fifa"
            local_pipeline = local_workspace / "work" / "tab-research-pipeline"
            local_outputs = local_workspace / "outputs"
            local_pipeline.mkdir(parents=True)
            local_outputs.mkdir()
            local_anchor = local_pipeline / "run_daily_report.py"
            local_anchor.write_text("", encoding="utf-8")
            self.assertEqual(resolve_workspace_root(local_anchor), local_workspace.resolve())
            self.assertEqual(resolve_output_dir(local_anchor), local_outputs.resolve())

            github_repo = local_workspace / "github_sync" / "FIFA"
            github_pipeline = github_repo / "tab-research-pipeline"
            github_pipeline.mkdir(parents=True)
            (github_repo / "AGENTS.md").write_text("", encoding="utf-8")
            github_anchor = github_pipeline / "run_daily_report.py"
            github_anchor.write_text("", encoding="utf-8")
            self.assertEqual(resolve_workspace_root(github_anchor), local_workspace.resolve())
            self.assertEqual(resolve_output_dir(github_anchor), local_outputs.resolve())

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "FIFA"
            pipeline = repo / "tab-research-pipeline"
            pipeline.mkdir(parents=True)
            (repo / "AGENTS.md").write_text("", encoding="utf-8")
            anchor = pipeline / "run_daily_report.py"
            anchor.write_text("", encoding="utf-8")
            self.assertEqual(resolve_workspace_root(anchor), repo.resolve())
            self.assertEqual(resolve_output_dir(anchor), (repo / "outputs").resolve())

    def test_my_bets_private_snapshot_writer_validates_and_locks_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "private" / "tab_fifa"
            result = write_private_snapshot(
                sample_my_bets_text(),
                private_dir,
                "01012026",
                source_url="https://www.tab.com.au/accounts/my-bets/bets",
                scraped_at="2026-06-03T00:00:00Z",
            )
            path = result["path"]
            self.assertTrue(result["ready"])
            self.assertEqual(path.name, "tab_my_bets_positions_01012026.json")
            snapshot = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(snapshot["private_snapshot"])
            self.assertEqual(snapshot["report_date"], "01012026")
            self.assertEqual(snapshot["summary"]["bet_count"], 2)
            self.assertEqual(snapshot["summary"]["pending_count"], 1)
            self.assertEqual(snapshot["summary"]["settled_count"], 1)
            self.assertEqual(snapshot["validation_issues"], [])
            self.assertFalse(path.stat().st_mode & 0o077)
            self.assertFalse(private_dir.stat().st_mode & 0o077)

    def test_my_bets_private_snapshot_writer_rejects_public_outputs_private_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            public_private_dir = root / "outputs" / "private" / "tab_fifa"
            with self.assertRaisesRegex(ValueError, "public outputs"):
                write_private_snapshot(sample_my_bets_text(), public_private_dir, "01012026")
            with self.assertRaisesRegex(ValueError, "private path"):
                assert_private_snapshot_dir(root / "public" / "tab_fifa")

    def test_private_position_bootstrap_status_is_actionable_and_public_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "private" / "tab_fifa"
            private_dir.mkdir(parents=True)
            status = build_private_position_bootstrap_status(private_dir, "01012026")
            self.assertEqual(status["status"], "capture_not_run")
            self.assertFalse(status["ready"])
            self.assertEqual(status["profile"]["profile_name"], "tab_chrome_profile")
            self.assertIn("--wait-for-login-ms 600000", status["next_action"])
            self.assertIn("preflight", status)
            self.assertTrue(status["preflight"]["can_start_bootstrap"])
            self.assertTrue(status["preflight"]["login_window_required"])
            self.assertEqual(status["preflight"]["wait_for_login_seconds"], 600)
            self.assertIn("credential_policy", status["preflight"])
            self.assertIn("automation_boundary", status["preflight"])
            self.assertNotIn(str(private_dir), json.dumps(status, ensure_ascii=False))

            atomic_write_json(
                private_dir / "tab_my_bets_capture_diagnostics_01012026.json",
                {
                    "schema_version": 1,
                    "private_diagnostic": True,
                    "report_date": "01012026",
                    "ready": False,
                    "auth_status": "access_denied",
                    "auth_mode": "persistent-profile",
                    "reason": "TAB My Bets page access denied",
                    "text_length": 120,
                },
            )
            status = build_private_position_bootstrap_status(private_dir, "01012026")
            self.assertEqual(status["status"], "profile_login_required")
            self.assertEqual(status["capture_diagnostic"]["auth_status"], "access_denied")
            self.assertTrue(status["preflight"]["manual_step_required"])
            self.assertIn("授权状态不可用", status["preflight"]["blocking_reason"])
            self.assertNotIn("My Bets", json.dumps(status, ensure_ascii=False))

            raw = private_dir / "tab_my_bets_raw_01012026.txt"
            raw.write_text(sample_my_bets_text(), encoding="utf-8")
            status = build_private_position_bootstrap_status(private_dir, "01012026")
            self.assertEqual(status["status"], "raw_ready_import_needed")
            self.assertIn("import_my_bets_snapshot.py", status["next_action"])
            self.assertTrue(status["preflight"]["can_import_snapshot"])

            write_private_snapshot(sample_my_bets_text(), private_dir, "01012026", scraped_at="2026-01-01T00:00:00Z")
            status = build_private_position_bootstrap_status(private_dir, "01012026")
            self.assertEqual(status["status"], "snapshot_ready")
            self.assertTrue(status["ready"])
            self.assertTrue(status["snapshot_validation"]["valid"])
            self.assertTrue(status["preflight"]["can_rerun_daily_gate"])
            self.assertNotIn("stake_aud", json.dumps(status, ensure_ascii=False))

    def test_my_bets_import_cli_writes_private_snapshot_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "private" / "tab_fifa" / "raw.txt"
            private_dir = root / "private" / "tab_fifa"
            private_dir.mkdir(parents=True)
            raw.write_text(sample_my_bets_text(), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "import_my_bets_snapshot.py"),
                    "--source",
                    str(raw),
                    "--report-date",
                    "01012026",
                    "--private-dir",
                    str(private_dir),
                    "--source-url",
                    "https://www.tab.com.au/accounts/my-bets/bets",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["private_snapshot_file"], "tab_my_bets_positions_01012026.json")
            self.assertNotIn(str(private_dir), completed.stdout)
            snapshot_path = private_dir / "tab_my_bets_positions_01012026.json"
            self.assertTrue(snapshot_path.exists())
            self.assertFalse(snapshot_path.stat().st_mode & 0o077)
            self.assertFalse((root / "outputs" / snapshot_path.name).exists())

    def test_my_bets_realized_roi_uses_settled_stake(self):
        text = """Mon 01 Jun - 21:41:10
FO
Win
Won
Spain
WC Spai-CabV Result
Stake
$100.00
Odds
1.08
Estimated Return
$108.00
Mon 01 Jun - 21:38:46
FO
Win
Pending
Germany
WC Gmny-Crco Result
Stake
$500.00
Odds
1.03
Estimated Return
$515.00
"""
        snapshot = build_snapshot(text, scraped_at="2026-06-03T00:00:00Z")
        self.assertEqual(snapshot["summary"]["settled_stake_aud"], 100.0)
        self.assertEqual(snapshot["summary"]["realized_pnl_aud"], 8.0)
        self.assertAlmostEqual(snapshot["summary"]["realized_roi"], 0.08)

    def test_my_bets_status_mapping_and_unknown_gate(self):
        text = """Mon 01 Jun - 21:41:10
FO
Win
Void
Spain
WC Spai-CabV Result
Stake
$100.00
Odds
1.08
Estimated Return
$100.00
Mon 01 Jun - 21:38:46
FO
Win
Cashed Out
Germany
WC Gmny-Crco Result
Stake
$500.00
Odds
1.03
Estimated Return
$520.00
Mon 01 Jun - 21:37:46
FO
Win
Manual Review
Japan
WC Neth-Jpn Result
Stake
$40.00
Odds
3.70
Estimated Return
$148.00
"""
        snapshot = build_snapshot(text, scraped_at="2026-06-03T00:00:00Z")
        summary = snapshot["summary"]
        self.assertEqual(summary["settled_count"], 2)
        self.assertEqual(summary["unknown_status_count"], 1)
        self.assertIn("manual review", summary["unknown_statuses"])
        self.assertFalse(summary["position_statuses_valid"])
        self.assertEqual(summary["realized_pnl_aud"], 20.0)

    def test_time_aware_bankroll_plan_uses_pending_results(self):
        summary = {
            "open_stake_aud": 2000,
            "estimated_return_if_all_win_aud": 2522,
            "potential_profit_if_all_win_aud": 522,
        }
        plan = build_bankroll_plan(summary, base_candidate_exposure_aud=60, unit_aud=40)
        self.assertEqual(plan.current_window_target_aud, 120.0)
        self.assertEqual(plan.lose_all_balance_mid_aud, 2000.0)
        self.assertEqual(plan.stake_return_balance_mid_aud, 4000.0)
        self.assertEqual(plan.win_all_balance_mid_aud, 4522.0)
        self.assertAlmostEqual(plan.win_all_roi_on_open_stake, 0.261)

        allocated = allocate_time_adjusted_stakes(
            [
                {"selection": "Japan", "stake_aud": 20, "expected_value": 0.104},
                {"selection": "Morocco", "stake_aud": 10, "expected_value": 0.275},
                {"selection": "Senegal", "stake_aud": 10, "expected_value": 0.238},
                {"selection": "Croatia", "stake_aud": 10, "expected_value": 0.154},
                {"selection": "Under 2.5", "stake_aud": 10, "expected_value": 0.076},
            ],
            target_aud=plan.current_window_target_aud,
            unit_aud=40,
        )
        self.assertEqual(sum(item["time_adjusted_stake_aud"] for item in allocated), 120.0)
        self.assertTrue(all(item["time_adjusted_stake_aud"] >= 10 for item in allocated))

    def test_bankroll_plan_fails_closed_when_budget_fully_committed(self):
        plan = build_bankroll_plan({"open_stake_aud": 4000}, base_candidate_exposure_aud=60, unit_aud=40)
        self.assertEqual(plan.uncommitted_mid_aud, 0.0)
        self.assertEqual(plan.current_window_target_aud, 0.0)
        allocated = allocate_time_adjusted_stakes(
            [{"selection": "Japan", "stake_aud": 20, "expected_value": 0.104}],
            target_aud=plan.current_window_target_aud,
            unit_aud=40,
        )
        self.assertEqual(allocated[0]["base_stake_aud"], 20.0)
        self.assertEqual(allocated[0]["time_adjusted_stake_aud"], 0.0)

    def test_bankroll_zero_open_stake_and_small_window_do_not_overallocate(self):
        plan = build_bankroll_plan({"open_stake_aud": 0, "total_stake_aud": 1000}, base_candidate_exposure_aud=60)
        self.assertEqual(plan.open_stake_aud, 0.0)
        allocated = allocate_time_adjusted_stakes(
            [
                {"selection": "A", "stake_aud": 20, "expected_value": 0.30},
                {"selection": "B", "stake_aud": 20, "expected_value": 0.20},
                {"selection": "C", "stake_aud": 20, "expected_value": 0.10},
                {"selection": "D", "stake_aud": 20, "expected_value": 0.05},
                {"selection": "E", "stake_aud": 20, "expected_value": 0.01},
            ],
            target_aud=20,
        )
        self.assertLessEqual(sum(item["time_adjusted_stake_aud"] for item in allocated), 20.0)
        self.assertEqual(len([item for item in allocated if item["time_adjusted_stake_aud"] > 0]), 2)

    def test_australia_gate_requires_unique_expected_markets(self):
        duplicate_markets = [
            {
                "market": AUSTRALIA_EXPECTED_MARKETS[0],
                "status": "priced",
                "rows": [{"selection": "AUS Win Exactly 1 Grp Match", "odds": 2.25}],
            }
            for _ in AUSTRALIA_EXPECTED_MARKETS
        ]
        gate = australia_gate(duplicate_markets)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("Duplicate Australia markets" in reason for reason in gate["blocking_reasons"]))

    def test_australia_gate_requires_selection_integrity(self):
        markets = australia_gate_markets_fixture()
        self.assertTrue(australia_gate(markets)["automation_ready"])

        markets = australia_gate_markets_fixture()
        markets[0]["rows"].append(dict(markets[0]["rows"][0]))
        gate = australia_gate(markets)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("duplicate Australia selections" in reason for reason in gate["blocking_reasons"]))

        markets = australia_gate_markets_fixture()
        ou_market = next(market for market in markets if market["market"] == "Team Total Group Goals Scored O/U")
        ou_market["rows"] = [{"selection": "AUS Over 2.5 Group Gls", "odds": 1.90}]
        gate = australia_gate(markets)
        self.assertFalse(gate["automation_ready"])
        self.assertTrue(any("threshold 2.5 missing Under side" in reason for reason in gate["blocking_reasons"]))

    def test_australia_price_parser_ignores_duplicate_numeric_price(self):
        rows = parse_price_rows(
            """AUS Group Point O/U
AUS Over 2.5 Grp Pts
1.66
1.66
AUS Under 2.5 Grp Pts
2.10
2.10
"""
        )
        self.assertEqual([row["selection"] for row in rows], ["AUS Over 2.5 Grp Pts", "AUS Under 2.5 Grp Pts"])

    def test_team_futures_multi_skips_incomplete_rows(self):
        text = """2026 SWC Futures Multi JPN
1 Market
2026 SWC Futures Multi JPN
JPN Win World Cup
41.00
JPN Reach Final
12.00
"""
        rows = parse_team_futures_multi(text)
        self.assertEqual(rows, [])
        gate = team_multi_gate(rows)
        self.assertFalse(gate["automation_ready"])

    def test_quantity_gates_reject_duplicate_entities(self):
        futures_rows = [{"team": "Japan", "markets": {market: 2.0 for market in ["Winner", "To Qualify for Final", "To Qualify For Semi Final", "To Qualify for Quarter Final"]}} for _ in range(48)]
        self.assertFalse(futures_gate(futures_rows, {})["automation_ready"])

        duplicate_groups = [
            {"group": "A", "rows": [{"team": f"T{i}", "odds": 2.0} for i in range(4)]}
            for _ in range(12)
        ]
        self.assertFalse(group_gate(duplicate_groups)["automation_ready"])

        duplicate_multi = [
            {"code": "JPN", "team": "Japan", "markets": {market: 2.0 for market in ["Win World Cup", "Reach Final", "Reach Semi Final", "Reach Quarter Final"]}}
            for _ in range(14)
        ]
        self.assertFalse(team_multi_gate(duplicate_multi)["automation_ready"])

    def test_safety_gate_detects_sensitive_scrape_and_private_positions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "outputs"
            private_dir = root / "work" / "private" / "tab_fifa"
            tmp_refresh_dir = root / "work" / "tmp_refresh_x"
            output_dir.mkdir()
            private_dir.mkdir(parents=True)
            private_dir.chmod(0o700)
            tmp_refresh_dir.mkdir(parents=True)
            (root / "scraped_example.json").write_text(
                "sessionId=abc&session_id=def&balance=10&Pending Bets",
                encoding="utf-8",
            )
            (tmp_refresh_dir / "raw.json").write_text("My Bets\n/accounts/\nBet Slip", encoding="utf-8")
            (output_dir / "tab_fifa_bankroll_plan_01012026.json").write_text(
                '{"private_detail_path": "/work/private/tab_fifa/secret.json"}',
                encoding="utf-8",
            )
            (output_dir / "tab_my_bets_positions_01012026.json").write_text("{}", encoding="utf-8")
            nested_public_private = output_dir / "private" / "tab_fifa"
            nested_public_private.mkdir(parents=True)
            (nested_public_private / "tab_my_bets_positions_02012026.json").write_text("{}", encoding="utf-8")
            gate = audit_safety(root, output_dir)
            self.assertFalse(gate["automation_safety_ready"])
            self.assertIn("private/tab_fifa/tab_my_bets_positions_02012026.json", gate["public_position_files"])
            (nested_public_private / "tab_my_bets_positions_02012026.json").unlink()
            redacted = redact_sensitive_text((root / "scraped_example.json").read_text())
            self.assertNotIn("session_id", redacted)
            self.assertNotIn("Pending Bets", redacted)
            (root / "scraped_example.json").write_text(redacted.replace("sessionId", "REDACTED_SID"), encoding="utf-8")
            gate = audit_safety(root, output_dir, private_dir=private_dir, allow_private_positions=True)
            self.assertFalse(gate["automation_safety_ready"])
            private_position = private_dir / "tab_my_bets_positions_01012026.json"
            (output_dir / "tab_my_bets_positions_01012026.json").rename(private_position)
            private_position.chmod(0o600)
            gate = audit_safety(root, output_dir, private_dir=private_dir)
            self.assertFalse(gate["automation_safety_ready"])
            gate = audit_safety(root, output_dir, private_dir=private_dir, allow_private_positions=True)
            self.assertFalse(gate["automation_safety_ready"])
            self.assertTrue(any("raw.json" in item["path"] for item in gate["sensitive_artifacts"]))
            (tmp_refresh_dir / "raw.json").unlink()
            (output_dir / "tab_fifa_bankroll_plan_01012026.json").write_text(
                '{"private_detail_available": true}',
                encoding="utf-8",
            )
            gate = audit_safety(root, output_dir, private_dir=private_dir, allow_private_positions=True)
            self.assertFalse(gate["automation_safety_ready"])
            self.assertTrue(any("REDACTED_PENDING_BETS" in item["markers"] for item in gate["sensitive_artifacts"]))
            (root / "scraped_example.json").unlink()
            gate = audit_safety(root, output_dir, private_dir=private_dir, allow_private_positions=True)
            self.assertFalse(gate["automation_safety_ready"])
            self.assertTrue(any("private_detail_available" in item["markers"] for item in gate["sensitive_artifacts"]))
            (output_dir / "tab_fifa_bankroll_plan_01012026.json").write_text("{}", encoding="utf-8")
            gate = audit_safety(root, output_dir, private_dir=private_dir, allow_private_positions=True)
            self.assertTrue(gate["automation_safety_ready"])
            (output_dir / "public_report.md").write_text("placed_at_text\nopen_stake_aud", encoding="utf-8")
            gate = audit_safety(root, output_dir, private_dir=private_dir, allow_private_positions=True)
            self.assertFalse(gate["automation_safety_ready"])

    def test_staged_output_safety_blocks_sensitive_raw_before_promote(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / "tab_fifa_world_cup_matches_raw_test.json",
                {
                    "generated_at": "2026-06-03T00:00:00Z",
                    "refresh_id": "batch-sensitive",
                    "text": "My Bets Balance accountNumber",
                },
            )
            (output_dir / "dashboard.html").write_text("<html>Bet Slip 0</html>", encoding="utf-8")
            gate = audit_output_safety(output_dir)
            self.assertFalse(gate["automation_safety_ready"])
            self.assertEqual(gate["sensitive_artifact_count"], 2)
            self.assertTrue(any("staged output artifacts" in reason for reason in gate["blocking_reasons"]))

    def test_public_artifact_safety_blocks_private_fields_and_local_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            safe = output_dir / "safe_dashboard.html"
            balanced = output_dir / "balanced.json"
            unsafe = output_dir / "unsafe_manifest.json"
            safe.write_text("<html>tab_fifa_dashboard_latest.html</html>", encoding="utf-8")
            balanced.write_text('{"rationale":"Balanced match with low-total profile"}', encoding="utf-8")
            unsafe.write_text(
                json.dumps(
                    {
                        "path": "/Users/linzezhang/Downloads/FIFA Report/04062026.pdf",
                        "private_detail_path": "/work/private/tab_fifa/secret.json",
                        "positions_ready": True,
                        "match_stakes": [],
                    }
                ),
                encoding="utf-8",
            )
            gate = audit_public_artifact_safety([safe, balanced])
            self.assertTrue(gate["public_artifact_safety_ready"])
            gate = audit_public_artifact_safety([safe, unsafe])
            self.assertFalse(gate["public_artifact_safety_ready"])
            self.assertEqual(gate["public_artifact_issue_count"], 1)
            markers = gate["public_artifact_issues"][0]["markers"]
            self.assertIn("private_detail_path", markers)
            self.assertIn("positions_ready", markers)
            self.assertIn("match_stakes", markers)
            self.assertIn("local_user_path_marker", markers)

            safety_message = output_dir / "safety_message.json"
            safety_message.write_text('{"message":"5 scraped artifacts still contain login/account/betting UI markers."}', encoding="utf-8")
            gate = audit_public_artifact_safety([safety_message])
            self.assertTrue(gate["public_artifact_safety_ready"], gate)

            pending_account_marker = output_dir / "pending_account_marker.json"
            pending_account_marker.write_text('{"status":"account-update-pending"}', encoding="utf-8")
            gate = audit_public_artifact_safety([pending_account_marker])
            self.assertTrue(gate["public_artifact_safety_ready"], gate)

            pending_balance_marker = output_dir / "pending_balance_marker.json"
            pending_balance_marker.write_text(
                '{"evidence":"balance=account-update-pending","public_visible_balance":"account-update-pending"}',
                encoding="utf-8",
            )
            gate = audit_public_artifact_safety([pending_balance_marker])
            self.assertTrue(gate["public_artifact_safety_ready"], gate)

            real_account = output_dir / "real_account.json"
            real_account.write_text('{"text":"accountNumber=123"}', encoding="utf-8")
            gate = audit_public_artifact_safety([real_account])
            self.assertFalse(gate["public_artifact_safety_ready"])

            real_balance = output_dir / "real_balance.json"
            real_balance.write_text('{"balance":"$123.45"}', encoding="utf-8")
            gate = audit_public_artifact_safety([real_balance])
            self.assertFalse(gate["public_artifact_safety_ready"])

            safe_db = output_dir / "safe.sqlite3"
            with sqlite3.connect(safe_db) as conn:
                conn.execute("CREATE TABLE audit_log (message TEXT)")
                conn.execute("INSERT INTO audit_log VALUES (?)", ("public odds report; balance=account-update-pending",))
            safe_db.chmod(0o600)
            gate = audit_public_artifact_safety([safe_db])
            self.assertTrue(gate["public_artifact_safety_ready"], gate)

            real_balance_db = output_dir / "real_balance.sqlite3"
            with sqlite3.connect(real_balance_db) as conn:
                conn.execute("CREATE TABLE audit_log (message TEXT)")
                conn.execute("INSERT INTO audit_log VALUES (?)", ('{"balance":"$123.45"}',))
            real_balance_db.chmod(0o600)
            gate = audit_public_artifact_safety([real_balance_db])
            self.assertFalse(gate["public_artifact_safety_ready"], gate)

    def test_atomic_io_and_single_instance_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            atomic_write_json(root / "nested" / "result.json", {"ok": True})
            atomic_write_text(root / "nested" / "report.md", "done")
            self.assertEqual(json.loads((root / "nested" / "result.json").read_text())["ok"], True)
            self.assertEqual((root / "nested" / "report.md").read_text(), "done")

            lock_path = root / "daily.lock"
            with single_instance_lock(lock_path):
                self.assertTrue(lock_path.exists())
                with self.assertRaises(RuntimeError):
                    with single_instance_lock(lock_path):
                        pass
            self.assertTrue(lock_path.exists())

    def test_automation_preflight_requires_user_authorization_after_technical_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code_dir = root / "code"
            output_dir = root / "outputs"
            private_dir = root / "private"
            code_dir.mkdir()
            output_dir.mkdir()
            private_dir.mkdir()
            downloads_pdf = root / "downloads.pdf"
            output_pdf = output_dir / "01012026.pdf"
            bankroll = output_dir / "bankroll.json"
            downloads_pdf.write_bytes(b"x" * 11000)
            output_pdf.write_bytes(b"x" * 11000)
            bankroll.write_text('{"positions_ready": true, "time_adjusted_new_exposure_aud": 120, "notes": "' + ("x" * 120) + '"}', encoding="utf-8")
            write_private_snapshot(sample_my_bets_text(), private_dir, "01012026", scraped_at="2026-01-01T00:00:00Z")
            safety = {"automation_safety_ready": True, "blocking_reasons": []}
            portfolio = {"portfolio_automation_ready": True, "ready_required_board_count": 5, "required_board_count": 5}
            raw_refresh = {"raw_refresh_ready": True, "blocking_reasons": []}
            authorization = automation_authorization_from_mapping(
                {
                    "authorized": False,
                    "allow_recurring": False,
                    "allow_auto_betting": False,
                    "cadence": "manual",
                }
            )
            preflight = audit_automation_preflight(
                code_dir=code_dir,
                output_dir=output_dir,
                private_dir=private_dir,
                safety=safety,
                portfolio=portfolio,
                raw_refresh=raw_refresh,
                report_date="01012026",
                downloads_pdf=downloads_pdf,
                output_pdf=output_pdf,
                bankroll_plan=bankroll,
                private_output_mode=True,
                raw_refresh_enabled=True,
                raw_refresh_succeeded=True,
                user_automation_authorized=authorization.entry_authorized,
                automation_authorization=authorization.to_public_dict(),
            )
            self.assertTrue(preflight["technical_preflight_ready"])
            self.assertFalse(preflight["automation_entry_ready"])
            self.assertIn("user has not authorized recurring automation", preflight["blocking_reasons"])
            self.assertFalse(preflight["automation_authorization"]["authorized"])
            no_downloads_preflight = audit_automation_preflight(
                code_dir=code_dir,
                output_dir=output_dir,
                private_dir=private_dir,
                safety=safety,
                portfolio=portfolio,
                raw_refresh=raw_refresh,
                report_date="01012026",
                downloads_pdf=None,
                output_pdf=output_pdf,
                bankroll_plan=bankroll,
                private_output_mode=True,
                raw_refresh_enabled=True,
                raw_refresh_succeeded=True,
                user_automation_authorized=False,
            )
            self.assertTrue(no_downloads_preflight["technical_preflight_ready"])
            self.assertNotIn("downloads_pdf", {check["name"] for check in no_downloads_preflight["checks"]})
            write_private_snapshot(sample_my_bets_text(), private_dir, "01012026", scraped_at="2026-01-02T00:00:00Z")
            stale_private = audit_automation_preflight(
                code_dir=code_dir,
                output_dir=output_dir,
                private_dir=private_dir,
                safety=safety,
                portfolio=portfolio,
                raw_refresh=raw_refresh,
                report_date="01012026",
                downloads_pdf=downloads_pdf,
                output_pdf=output_pdf,
                bankroll_plan=bankroll,
                private_output_mode=True,
                raw_refresh_enabled=True,
                raw_refresh_succeeded=True,
                user_automation_authorized=False,
            )
            self.assertFalse(stale_private["technical_preflight_ready"])
            self.assertTrue(any("scraped_at is not on current report date" in reason for reason in stale_private["blocking_reasons"]))
            write_private_snapshot(sample_my_bets_text(), private_dir, "01012026", scraped_at="2026-01-01T00:00:00Z")
            file_checks = [check for check in preflight["checks"] if check["name"] in {"downloads_pdf", "output_pdf_copy", "bankroll_plan"}]
            self.assertTrue(file_checks)
            for check in file_checks:
                self.assertNotIn(str(root), check["message"])
                self.assertIn("file_name", check["details"])
                self.assertIn("size_bytes", check["details"])
            missing_raw = audit_automation_preflight(
                code_dir=code_dir,
                output_dir=output_dir,
                private_dir=private_dir,
                safety=safety,
                portfolio=portfolio,
                raw_refresh=None,
                report_date="01012026",
                downloads_pdf=downloads_pdf,
                output_pdf=output_pdf,
                bankroll_plan=bankroll,
                private_output_mode=True,
                raw_refresh_enabled=True,
                raw_refresh_succeeded=True,
                user_automation_authorized=False,
            )
            self.assertFalse(missing_raw["technical_preflight_ready"])
            self.assertIn("raw refresh gate is missing", missing_raw["blocking_reasons"])

            (private_dir / "tab_my_bets_positions_01012026.json").write_text("{}", encoding="utf-8")
            invalid_private = audit_automation_preflight(
                code_dir=code_dir,
                output_dir=output_dir,
                private_dir=private_dir,
                safety=safety,
                portfolio=portfolio,
                raw_refresh=raw_refresh,
                report_date="01012026",
                downloads_pdf=downloads_pdf,
                output_pdf=output_pdf,
                bankroll_plan=bankroll,
                private_output_mode=True,
                raw_refresh_enabled=True,
                raw_refresh_succeeded=True,
                user_automation_authorized=False,
            )
            self.assertFalse(invalid_private["technical_preflight_ready"])
            self.assertTrue(any("snapshot invalid" in reason for reason in invalid_private["blocking_reasons"]))

            (private_dir / "tab_my_bets_positions_01012026.json").unlink()
            atomic_write_json(
                private_dir / "tab_my_bets_capture_diagnostics_01012026.json",
                {
                    "schema_version": 1,
                    "private_diagnostic": True,
                    "report_date": "01012026",
                    "ready": False,
                    "auth_status": "login_required",
                    "auth_mode": "persistent-profile",
                    "reason": "TAB My Bets page appears unauthenticated",
                    "final_url_public": "https://login.tab.com.au/login",
                    "text_length": 0,
                },
            )
            login_required_private = audit_automation_preflight(
                code_dir=code_dir,
                output_dir=output_dir,
                private_dir=private_dir,
                safety=safety,
                portfolio=portfolio,
                raw_refresh=raw_refresh,
                report_date="01012026",
                downloads_pdf=downloads_pdf,
                output_pdf=output_pdf,
                bankroll_plan=bankroll,
                private_output_mode=True,
                raw_refresh_enabled=True,
                raw_refresh_succeeded=True,
                user_automation_authorized=False,
            )
            self.assertFalse(login_required_private["technical_preflight_ready"])
            self.assertTrue(any("login_required" in reason for reason in login_required_private["blocking_reasons"]))
            private_check = next(
                check for check in login_required_private["checks"] if check["name"] == "private_positions_available"
            )
            diagnostic_detail = private_check["details"][0]["capture_diagnostic"]
            self.assertEqual(diagnostic_detail["auth_status"], "login_required")
            self.assertNotIn("final_url_public", diagnostic_detail)

    def test_automation_authorization_config_defaults_to_manual_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_config = Path(tmp) / "missing.toml"
            authorization = load_automation_authorization(missing_config)
            public = authorization.to_public_dict()
            self.assertFalse(authorization.entry_authorized)
            self.assertFalse(public["authorized"])
            self.assertFalse(public["allow_recurring"])
            self.assertFalse(public["allow_auto_betting"])
            self.assertEqual(public["cadence"], "manual")
            self.assertIn("user has not authorized recurring automation", public["blocking_reasons"])

        repo_config = ROOT / "config" / "automation.toml"
        configured = load_automation_authorization(repo_config)
        self.assertFalse(configured.entry_authorized)
        self.assertFalse(configured.allow_auto_betting)
        self.assertIn("user has not authorized recurring automation", configured.blocking_reasons)

    def test_automation_authorization_can_enable_report_generation_only(self):
        authorization = automation_authorization_from_mapping(
            {
                "authorized": True,
                "allow_recurring": True,
                "allow_auto_betting": False,
                "cadence": "daily",
                "approved_at": "2026-06-04T00:00:00+10:00",
                "approved_by": "user",
                "scope": "report_generation_only",
            }
        )
        self.assertTrue(authorization.entry_authorized)
        self.assertEqual(authorization.blocking_reasons, ())
        self.assertTrue(authorization.to_public_dict()["entry_authorized"])

    def test_automation_authorization_never_allows_auto_betting(self):
        authorization = automation_authorization_from_mapping(
            {
                "authorized": True,
                "allow_recurring": True,
                "allow_auto_betting": True,
                "cadence": "daily",
                "scope": "report_generation_only",
            }
        )
        self.assertFalse(authorization.entry_authorized)
        self.assertIn("automation config attempts to allow auto betting, which is forbidden", authorization.blocking_reasons)

    def test_raw_refresh_gate_has_all_refresh_drivers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "outputs"
            driver = root / "work" / "tab-research-pipeline" / "scripts" / "refresh_tab_readonly.mjs"
            output_dir.mkdir()
            driver.parent.mkdir(parents=True)
            driver.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            manifest = audit_raw_refresh(output_dir, now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc))
            self.assertFalse(manifest["raw_refresh_ready"])
            self.assertEqual(manifest["required_target_count"], 5)
            self.assertEqual(manifest["driver_ready_required_target_count"], 5)
            self.assertEqual(manifest["ready_required_target_count"], 0)
            self.assertTrue(any("raw snapshot is missing" in reason for reason in manifest["blocking_reasons"]))

    def test_the_odds_api_request_is_tab_au_decimal_only(self):
        placeholder_key = "test" + "-key"
        requests = build_the_odds_api_requests(api_key=placeholder_key, sports=["soccer_fifa_world_cup"], markets=["h2h", "totals"])
        self.assertEqual(len(requests), 1)
        request = requests[0]
        self.assertEqual(request.provider, "the_odds_api")
        self.assertIn("/v4/sports/soccer_fifa_world_cup/odds/", request.url)
        self.assertIn("regions=au", request.url)
        self.assertIn("bookmakers=tab", request.url)
        self.assertIn("oddsFormat=decimal", request.url)
        self.assertNotIn(placeholder_key, request.redacted_url)

    def test_the_odds_api_default_scope_is_matches_first_and_ignores_region_markets(self):
        placeholder_key = "test" + "-key"
        requests = build_the_odds_api_requests(api_key=placeholder_key)
        request = requests[0]

        self.assertEqual(default_the_odds_api_sports("matches"), ["soccer_fifa_world_cup"])
        self.assertEqual(default_the_odds_api_sports("futures"), ["soccer_fifa_world_cup_winner"])
        self.assertEqual(list(request.market_keys), ["h2h", "totals", "spreads"])
        self.assertIn("/v4/sports/soccer_fifa_world_cup/odds/", request.url)
        self.assertNotIn("outrights", request.url)
        self.assertEqual(request.board_scope, "matches")
        self.assertEqual(request.estimated_credit_cost, 3)
        self.assertEqual(resolve_target_board_ids("matches"), ["world_cup_matches"])
        self.assertNotIn("world_cup_australia_markets", resolve_target_board_ids("all"))

    def test_the_odds_api_request_builder_maps_legacy_sport_without_discovery(self):
        placeholder_key = "unit" + "-test"
        requests = build_the_odds_api_requests(
            api_key=placeholder_key,
            sports=["soccer_world_cup"],
            scope="matches",
        )
        futures_requests = build_the_odds_api_requests(
            api_key=placeholder_key,
            sports=["soccer_world_cup"],
            scope="futures",
        )

        self.assertEqual(normalize_the_odds_api_sports_config(["soccer_world_cup"], "matches"), ["soccer_fifa_world_cup"])
        self.assertEqual(normalize_the_odds_api_sports_config(["soccer_world_cup"], "futures"), ["soccer_fifa_world_cup_winner"])
        self.assertIn("/v4/sports/soccer_fifa_world_cup/odds/", requests[0].url)
        self.assertNotIn("soccer_world_cup/odds", requests[0].url)
        self.assertIn("/v4/sports/soccer_fifa_world_cup_winner/odds/", futures_requests[0].url)

    def test_the_odds_api_sports_catalog_filters_stale_config_keys(self):
        catalog = [
            {
                "key": "soccer_fifa_world_cup",
                "group": "Soccer",
                "title": "FIFA World Cup",
                "description": "FIFA World Cup 2026",
                "active": True,
                "has_outrights": False,
            },
            {
                "key": "soccer_fifa_world_cup_winner",
                "group": "Soccer",
                "title": "FIFA World Cup Winner",
                "description": "FIFA World Cup Winner 2026",
                "active": True,
                "has_outrights": True,
            },
        ]

        self.assertEqual(
            resolve_the_odds_api_sports_from_catalog(
                catalog,
                requested_sports=["soccer_fifa_world_cup", "soccer_world_cup"],
                scope="matches",
            ),
            ["soccer_fifa_world_cup"],
        )
        self.assertEqual(
            resolve_the_odds_api_sports_from_catalog(catalog, requested_sports=[], scope="futures"),
            ["soccer_fifa_world_cup_winner"],
        )

    def test_provider_env_loader_accepts_fixed_example_filename_without_placeholder_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "odds_providers.local.env.example"
            env_path.write_text(
                "\n".join(
                    [
                        "THE_ODDS_API_KEY=replace_with_rotated_key",
                        "TAB_FIFA_THE_ODDS_API_SPORTS=soccer_fifa_world_cup",
                        "TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY=1",
                    ]
                ),
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {}, clear=True):
                loaded = load_local_env_files([env_path])

                self.assertEqual(loaded, [str(env_path)])
                self.assertNotIn("THE_ODDS_API_KEY", os.environ)
                self.assertEqual(os.environ["TAB_FIFA_THE_ODDS_API_SPORTS"], "soccer_fifa_world_cup")
                self.assertEqual(os.environ["TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY"], "1")
                self.assertFalse(should_load_env_value("replace_with_rotated_key"))
                self.assertTrue(should_load_env_value("unit-test-real-looking-key"))

    def test_the_odds_api_event_market_requests_are_tab_scoped_and_redacted(self):
        placeholder_key = "test" + "-key"
        requests = build_the_odds_api_event_markets_requests(
            api_key=placeholder_key,
            sport="soccer_fifa_world_cup",
            event_ids=["event-123"],
        )
        request = requests[0]

        self.assertIn("/v4/sports/soccer_fifa_world_cup/events/event-123/markets", request.url)
        self.assertIn("bookmakers=tab", request.url)
        self.assertEqual(request.request_kind, "event_markets")
        self.assertEqual(request.estimated_credit_cost, 1)
        self.assertNotIn(placeholder_key, request.redacted_url)

    def test_the_odds_api_event_market_probe_builds_event_odds_requests(self):
        placeholder_key = "test" + "-key"
        event_market_payload = the_odds_api_event_markets_payload_fixture()
        plan = event_market_probe_plan(
            [event_market_payload],
            target_markets=["totals", "alternate_totals", "team_totals"],
            max_event_odds_requests=2,
        )
        requests = build_the_odds_api_event_odds_requests(
            api_key=placeholder_key,
            sport="soccer_fifa_world_cup",
            event_market_plan=plan,
        )

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["markets"], ["alternate_totals", "team_totals"])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].request_kind, "event_odds")
        self.assertIn("markets=alternate_totals%2Cteam_totals", requests[0].url)
        self.assertNotIn(placeholder_key, requests[0].redacted_url)

    def test_the_odds_api_sports_discovery_uses_certifi_ssl_fallback(self):
        class FakeResponse:
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps([{"key": "soccer_fifa_world_cup", "active": True}]).encode("utf-8")

        fallback_context = object()
        seen_contexts = []

        def fake_urlopen(_request, timeout, context=None):
            seen_contexts.append(context)
            if context is None:
                raise urllib.error.URLError("CERTIFICATE_VERIFY_FAILED")
            return FakeResponse()

        with mock.patch.object(
            odds_provider_adapter_module,
            "provider_ssl_attempts",
            return_value=[("urllib_default_ssl", None), ("urllib_certifi_ssl", fallback_context)],
        ), mock.patch.object(odds_provider_adapter_module.urllib.request, "urlopen", side_effect=fake_urlopen):
            catalog = fetch_the_odds_api_sports(api_key="test-key", timeout_seconds=1)

        self.assertEqual(catalog[0]["key"], "soccer_fifa_world_cup")
        self.assertEqual(seen_contexts, [None, fallback_context])

    def test_provider_request_fetch_uses_certifi_ssl_fallback_and_records_transport(self):
        class FakeResponse:
            def __init__(self):
                self.headers = {
                    "x-requests-remaining": "497",
                    "x-requests-used": "3",
                    "x-requests-last": "1",
                }

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps([{"id": "event-1", "bookmakers": []}]).encode("utf-8")

        fallback_context = object()
        seen_contexts = []

        def fake_urlopen(_request, timeout, context=None):
            seen_contexts.append(context)
            if context is None:
                raise urllib.error.URLError("CERTIFICATE_VERIFY_FAILED")
            return FakeResponse()

        provider_requests = build_the_odds_api_requests(
            api_key="test-key",
            sports=["soccer_fifa_world_cup"],
            markets=["h2h"],
            scope="matches",
        )
        with mock.patch.object(
            odds_provider_adapter_module,
            "provider_ssl_attempts",
            return_value=[("urllib_default_ssl", None), ("urllib_certifi_ssl", fallback_context)],
        ), mock.patch.object(odds_provider_adapter_module.urllib.request, "urlopen", side_effect=fake_urlopen):
            payloads = fetch_provider_requests(provider_requests, timeout_seconds=1)

        self.assertEqual(seen_contexts, [None, fallback_context])
        self.assertTrue(payloads[0]["ok"])
        self.assertEqual(payloads[0]["transport_ssl_mode"], "urllib_certifi_ssl")
        self.assertEqual(payloads[0]["usage"]["requests_remaining"], 497)
        self.assertNotIn("test-key", payloads[0]["request_url"])

    def test_provider_historical_merge_keys_preserve_primary_totals_for_team_total_probe(self):
        args = argparse.Namespace(scope="matches", event_odds_markets="team_totals,alternate_team_totals")
        with mock.patch.dict(
            os.environ,
            {
                "TAB_FIFA_THE_ODDS_API_MARKETS": "",
                "TAB_FIFA_THE_ODDS_API_MATCH_MARKETS": "h2h,totals,spreads",
                "TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS": "",
            },
        ):
            market_keys = historical_merge_market_keys(args)

        self.assertIn("totals", market_keys)
        self.assertIn("team_totals", market_keys)
        self.assertIn("alternate_team_totals", market_keys)

    def test_provider_adapter_maps_team_total_markets_for_matches(self):
        raws = adapt_provider_payloads(
            [the_odds_api_payload_fixture()],
            refresh_id="provider-team-total",
            generated_at="2026-06-13T00:00:00Z",
            target_board_ids=["world_cup_matches"],
        )
        first_match = raws["world_cup_matches"]["matches"][0]

        self.assertIn("Team Total Goals Over/Under", first_match["markets"])
        self.assertIn("Mexico Over 1.5 Goals", first_match["markets"]["Team Total Goals Over/Under"])
        self.assertIn("South Africa Under 0.5 Goals", first_match["markets"]["Team Total Goals Over/Under"])

    def test_provider_adapter_merges_event_odds_alternate_markets_into_existing_match(self):
        raws = adapt_provider_payloads(
            [the_odds_api_payload_fixture(), the_odds_api_event_markets_payload_fixture(), the_odds_api_event_odds_payload_fixture()],
            refresh_id="provider-event-odds",
            generated_at="2026-06-13T00:00:00Z",
            target_board_ids=["world_cup_matches"],
        )
        matches = raws["world_cup_matches"]["matches"]
        mexico = next(item for item in matches if item["match"] == "Mexico v South Africa")

        self.assertEqual(len([item for item in matches if item["match"] == "Mexico v South Africa"]), 1)
        self.assertIn("Total Goals Over/Under", mexico["markets"])
        self.assertIn("Team Total Goals Over/Under", mexico["markets"])
        self.assertIn("event_odds", mexico["provider_request_kinds"])

    def test_provider_analysis_allows_result_handicap_when_totals_are_missing(self):
        raw = {
            "matches": [
                {
                    "match": "Qatar v Switzerland",
                    "markets": {
                        "Result": "Result\nQatar\n15.00\nDraw\n6.50\nSwitzerland\n1.18\n",
                        "Handicap": "Handicap\nQatar +2.5\n1.90\nSwitzerland -2.5\n1.90\n",
                    },
                },
                {
                    "match": "Mexico v South Africa",
                    "markets": {
                        "Result": "Result\nMexico\n1.60\nDraw\n3.80\nSouth Africa\n5.50\n",
                    },
                },
            ]
        }

        validation = validate_provider_analysis_snapshot("world_cup_matches", raw)

        self.assertTrue(validation["valid"], validation)
        self.assertEqual(validation["coverage"]["result_market_count"], 2)
        self.assertEqual(validation["coverage"]["handicap_market_count"], 1)
        self.assertEqual(validation["coverage"]["secondary_market_available"], "Handicap")
        self.assertTrue(any("Total O/U and Team Total O/U" in warning for warning in validation["warnings"]))

    def test_provider_adapter_stages_tab_labeled_matches_without_formal_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-fixture-batch"
            payloads = [the_odds_api_payload_fixture()]
            raws = adapt_provider_payloads(
                payloads,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            self.assertIn("world_cup_matches", raws)
            validation = validate_raw_snapshot("world_cup_matches", raws["world_cup_matches"])
            self.assertTrue(validation["valid"], validation)

            manifest = write_provider_staging_bundle(
                output_dir,
                raws,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=payloads,
            )
            coverage = build_provider_coverage(output_dir, manifest)

            self.assertFalse(coverage["formal_publish_allowed"])
            self.assertFalse(coverage["full_automation_allowed"])
            self.assertEqual(coverage["target_board_ids"], ["world_cup_matches"])
            matches_target = next(row for row in coverage["targets"] if row["board_id"] == "world_cup_matches")
            self.assertTrue(matches_target["raw_valid"], matches_target)
            self.assertTrue(matches_target["provider_analysis_ready"], matches_target)
            self.assertFalse(matches_target["tab_manual_verified"])
            self.assertTrue(any("provider raw requires TAB manual final verification" in reason for reason in coverage["blocking_reasons"]))
            self.assertTrue((output_dir / ODDS_PROVIDER_COVERAGE_LATEST).exists())
            self.assertFalse((output_dir / current_matches_board().raw_snapshot).exists())

    def test_provider_kpi_reports_market_gaps_and_credit_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-kpi-batch"
            payloads = [the_odds_api_payload_fixture(), the_odds_api_event_odds_payload_fixture()]
            raws = adapt_provider_payloads(
                payloads,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            manifest = write_provider_staging_bundle(
                output_dir,
                raws,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=payloads,
            )
            build_provider_coverage(output_dir, manifest)
            payload = write_provider_kpi_bundle(output_dir)

            self.assertEqual(payload["refresh_id"], refresh_id)
            self.assertEqual(payload["summary"]["event_count"], len(EXPECTED_MATCHES))
            self.assertTrue(any(row["id"] == "result_coverage" and row["status"] == "ready" for row in payload["kpi_rows"]))
            self.assertTrue(any(row["id"] == "provider_credit_budget" for row in payload["kpi_rows"]))
            self.assertIn("alternate_plan", payload["summary"])
            self.assertTrue(any(row["id"] == "alternate_probe_plan" for row in payload["kpi_rows"]))
            self.assertTrue((output_dir / "provider_kpi_latest.json").exists())
            self.assertTrue((output_dir / "provider_kpi_latest.md").exists())
            self.assertTrue((output_dir / "provider_kpi_latest.pdf").exists())

    def test_provider_kpi_marks_previous_blocked_attempt_as_history_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-current-success"
            payloads = [the_odds_api_payload_fixture()]
            raws = adapt_provider_payloads(
                payloads,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            manifest = write_provider_staging_bundle(
                output_dir,
                raws,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=payloads,
            )
            build_provider_coverage(output_dir, manifest)
            write_blocked_provider_payload(
                output_dir,
                provider="the_odds_api",
                refresh_id="provider-old-blocked",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                error='the_odds_api HTTP 404: {"message":"Unknown sport"}',
            )

            payload = write_provider_kpi_bundle(output_dir)
            blocked = payload["last_blocked_attempt"]
            markdown = (output_dir / "provider_kpi_latest.md").read_text(encoding="utf-8")

            self.assertEqual(payload["refresh_id"], refresh_id)
            self.assertEqual(blocked["refresh_id"], "provider-old-blocked")
            self.assertFalse(blocked["is_current_refresh_blocker"])
            self.assertTrue(blocked["stale_history_only"])
            self.assertIn("Last Blocked Provider Attempt (History Only)", markdown)

    def test_provider_refresh_cli_rebuilds_kpi_for_same_refresh_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "outputs"
            output_dir.mkdir()
            input_path = Path(tmp) / "provider_payload.json"
            refresh_id = "provider-cli-kpi-sync"
            input_path.write_text(json.dumps(the_odds_api_payload_fixture()), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "refresh_odds_provider_raw.py"),
                    "--provider",
                    "the_odds_api",
                    "--scope",
                    "matches",
                    "--input-json",
                    str(input_path),
                    "--output-dir",
                    str(output_dir),
                    "--refresh-id",
                    refresh_id,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            kpi = json.loads((output_dir / "provider_kpi_latest.json").read_text(encoding="utf-8"))
            self.assertEqual(result["provider_kpi"], "provider_kpi_latest.json")
            self.assertEqual(result["provider_kpi_refresh_id"], refresh_id)
            self.assertEqual(kpi["refresh_id"], refresh_id)
            self.assertEqual(kpi["refresh_id"], result["refresh_id"])
            self.assertIn("provider_kpi_primary_gap", result)

    def test_provider_config_doctor_redacts_keys_and_flags_legacy_sport(self):
        with tempfile.TemporaryDirectory() as tmp:
            pipeline_root = Path(tmp) / "pipeline"
            output_dir = Path(tmp) / "outputs"
            (pipeline_root / "config").mkdir(parents=True)
            output_dir.mkdir()
            (pipeline_root / "config" / "odds_providers.local.env").write_text(
                "\n".join(
                    [
                        "THE_ODDS_API_" + "KEY=unit-test-secret",
                        "OPTICODDS_API_" + "KEY=optic-test-secret",
                        "TAB_FIFA_THE_ODDS_API_SPORTS=soccer_fifa_world_cup,soccer_world_cup",
                        "TAB_FIFA_THE_ODDS_API_MATCH_MARKETS=h2h,totals,spreads",
                        "TAB_FIFA_THE_ODDS_API_EVENT_MARKET_PROBE_LIMIT=0",
                    ]
                ),
                encoding="utf-8",
            )

            payload = write_provider_config_doctor_bundle(output_dir, pipeline_root)
            json_text = (output_dir / PROVIDER_CONFIG_DOCTOR_JSON_LATEST).read_text(encoding="utf-8")
            markdown_text = (output_dir / PROVIDER_CONFIG_DOCTOR_MD_LATEST).read_text(encoding="utf-8")

            self.assertEqual(payload["status"], "ready_with_warnings")
            self.assertTrue(payload["local_env"]["exists"])
            self.assertTrue(payload["the_odds_api"]["api_key_present"])
            self.assertTrue(payload["opticodds"]["api_key_present"])
            self.assertIn("soccer_world_cup", payload["the_odds_api"]["known_invalid_or_legacy_sports"])
            self.assertEqual(payload["recommended_env_patch"]["TAB_FIFA_THE_ODDS_API_SPORTS"], "soccer_fifa_world_cup")
            self.assertTrue(payload["the_odds_api"]["sports_discovery_enabled"])
            self.assertEqual(payload["current_executable_new_stake_aud"], 0)
            self.assertNotIn("unit-test-secret", json_text)
            self.assertNotIn("optic-test-secret", json_text)
            self.assertNotIn("unit-test-secret", markdown_text)
            self.assertTrue((output_dir / PROVIDER_CONFIG_DOCTOR_PDF_LATEST).exists())

    def test_provider_config_doctor_blocks_missing_local_env_and_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            pipeline_root = Path(tmp) / "pipeline"
            pipeline_root.mkdir()
            payload = build_provider_config_doctor(
                pipeline_root,
                env={
                    "TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY": "0",
                    "TAB_FIFA_THE_ODDS_API_SPORTS": "soccer_world_cup",
                },
            )

            self.assertEqual(payload["status"], "blocked")
            codes = {issue["code"] for issue in payload["issues"]}
            self.assertIn("provider_local_env_missing", codes)
            self.assertIn("provider_api_keys_missing", codes)
            self.assertIn("sports_discovery_disabled", codes)
            self.assertIn("the_odds_api_legacy_unknown_sport", codes)
            self.assertEqual(payload["current_executable_new_stake_aud"], 0)

    def test_provider_config_doctor_supports_fixed_example_env_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            pipeline_root = Path(tmp) / "pipeline"
            (pipeline_root / "config").mkdir(parents=True)
            (pipeline_root / "config" / "odds_providers.local.env.example").write_text(
                "\n".join(
                    [
                        "THE_ODDS_API_" + "KEY=unit-test-secret",
                        "OPTICODDS_API_" + "KEY=replace_with_opticodds_key_if_available",
                        "TAB_FIFA_THE_ODDS_API_SPORTS=soccer_fifa_world_cup",
                        "TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY=1",
                    ]
                ),
                encoding="utf-8",
            )

            payload = build_provider_config_doctor(pipeline_root, env={})
            codes = {issue["code"] for issue in payload["issues"]}

            self.assertEqual(payload["status"], "ready_with_warnings")
            self.assertFalse(payload["local_env"]["exists"])
            self.assertTrue(payload["local_env"]["effective_exists"])
            self.assertTrue(payload["local_env"]["using_example_fallback"])
            self.assertTrue(payload["the_odds_api"]["api_key_present"])
            self.assertFalse(payload["opticodds"]["api_key_present"])
            self.assertIn("provider_example_env_fallback_in_use", codes)
            self.assertNotIn("provider_local_env_missing", codes)
            self.assertEqual(payload["current_executable_new_stake_aud"], 0)

    def test_provider_alternate_plan_builds_credit_safe_probe_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-alternate-plan"
            primary = json.loads(json.dumps(the_odds_api_payload_fixture()))
            for event in primary["payload"]:
                for bookmaker in event.get("bookmakers") or []:
                    bookmaker["markets"] = [
                        market for market in bookmaker.get("markets") or [] if market.get("key") in {"h2h", "spreads"}
                    ]
            event_market = the_odds_api_event_markets_payload_fixture()
            payloads = [primary, event_market]
            raws = adapt_provider_payloads(
                payloads,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            manifest = write_provider_staging_bundle(
                output_dir,
                raws,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=payloads,
            )
            build_provider_coverage(output_dir, manifest)
            plan = write_provider_alternate_plan_bundle(output_dir, provider_payloads=payloads)
            plan_text = json.dumps(plan, ensure_ascii=False)

            self.assertEqual(plan["refresh_id"], refresh_id)
            self.assertEqual(plan["status"], "in_progress")
            self.assertGreater(plan["probe_queue_count"], 0)
            self.assertGreater(plan["credit_policy"]["recommended_batch_size"], 0)
            self.assertEqual(plan["recommended_batch_size"], plan["credit_policy"]["recommended_batch_size"])
            self.assertEqual(
                plan["estimated_next_batch_credit_floor"],
                plan["credit_policy"]["estimated_next_batch_credit_floor"],
            )
            self.assertEqual(
                plan["estimated_next_batch_credit_ceiling"],
                plan["credit_policy"]["estimated_next_batch_credit_ceiling"],
            )
            self.assertIn("Team Total Goals Over/Under", plan["next_probe_queue"][0]["missing_families"])
            self.assertEqual(plan["event_probe_evidence"]["market_probe_count"], 1)
            self.assertEqual(plan["event_probe_evidence"]["team_total_available_probe_count"], 1)
            self.assertIn("--event-market-probe-limit", plan["recommended_command"])
            self.assertNotIn("apiKey=", plan_text)
            self.assertTrue((output_dir / PROVIDER_ALTERNATE_PLAN_JSON_LATEST).exists())
            self.assertTrue((output_dir / "provider_alternate_plan_latest.md").exists())
            self.assertTrue((output_dir / "provider_alternate_plan_latest.pdf").exists())

    def test_provider_alternate_plan_marks_exhausted_provider_path_as_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-exhausted-total"
            staged_rel = "provider_raw/provider-exhausted-total/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            matches = []
            for idx in range(10):
                markets = {"Result": {}, "Handicap": {}}
                if idx < 8:
                    markets["Total Goals Over/Under"] = {}
                matches.append(
                    {
                        "provider_event_id": f"event-{idx}",
                        "match": f"Team {idx} v Opp {idx}",
                        "commence_time": "2026-06-13T00:00:00Z",
                        "provider_request_kinds": ["event_odds"],
                        "markets": markets,
                    }
                )
            atomic_write_json(staged_path, {"matches": matches})
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "formal_publish_allowed": False,
                    "full_automation_allowed": False,
                    "request_usage": {
                        "reported_requests_used_max": 180,
                        "reported_requests_remaining_min": 320,
                        "reported_last_request_cost": 13,
                    },
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "event_count": 10,
                            "provider_analysis_ready": True,
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 10,
                                "Handicap": 10,
                                "Total Goals Over/Under": 8,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )
            atomic_write_json(
                output_dir / PROVIDER_ALTERNATE_PLAN_JSON_LATEST,
                {
                    "refresh_id": refresh_id,
                    "event_probe_evidence": {
                        "market_probe_count": 5,
                        "event_odds_count": 5,
                        "team_total_available_probe_count": 0,
                        "total_available_probe_count": 5,
                        "event_odds_event_ids": [f"event-{idx}" for idx in range(10)],
                    },
                },
            )

            plan = build_provider_alternate_plan(output_dir)
            total = next(row for row in plan["market_family_gaps"] if row["id"] == "total_ou")

            self.assertEqual(plan["status"], "fallback_required")
            self.assertEqual(plan["probe_queue_count"], 0)
            self.assertEqual(plan["fallback_queue_count"], 10)
            self.assertEqual(total["status"], "ready")
            self.assertEqual(total["provider_status"], "coverage_threshold_met_no_remaining_the_odds_api_queue")
            self.assertIn("Team Total 转入 OpticOdds", plan["recommended_next_action"])

    def test_provider_alternate_plan_stops_low_yield_team_total_probe_after_small_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-low-yield-team-total"
            primary = json.loads(json.dumps(the_odds_api_payload_fixture()))
            for event in primary["payload"]:
                for bookmaker in event.get("bookmakers") or []:
                    bookmaker["markets"] = [
                        market for market in bookmaker.get("markets") or [] if market.get("key") in {"h2h", "totals", "spreads"}
                    ]
            event_market_payloads = []
            for index, event in enumerate(primary["payload"][:3]):
                event_market = json.loads(json.dumps(the_odds_api_event_markets_payload_fixture()))
                event_market["event_id"] = event["id"]
                event_market["payload"]["id"] = event["id"]
                event_market["payload"]["home_team"] = event["home_team"]
                event_market["payload"]["away_team"] = event["away_team"]
                event_market["payload"]["bookmakers"][0]["markets"] = [
                    {"key": "h2h"},
                    {"key": "spreads"},
                    {"key": "alternate_spreads"},
                    {"key": "alternate_totals"},
                    {"key": "btts"},
                    {"key": "double_chance"},
                    {"key": "draw_no_bet"},
                ]
                event_market["usage"] = {"requests_remaining": 299 - index, "requests_used": 201 + index, "requests_last": 1}
                event_market_payloads.append(event_market)
            payloads = [primary, *event_market_payloads]
            raws = adapt_provider_payloads(
                payloads,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            manifest = write_provider_staging_bundle(
                output_dir,
                raws,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=payloads,
            )
            build_provider_coverage(output_dir, manifest)

            plan = write_provider_alternate_plan_bundle(output_dir, provider_payloads=payloads)
            team_total = next(row for row in plan["market_family_gaps"] if row["id"] == "team_total_ou")

            self.assertEqual(plan["status"], "in_progress")
            self.assertGreater(plan["probe_queue_count"], 0)
            self.assertEqual(plan["recommended_batch_size"], 3)
            self.assertEqual(plan["credit_policy"]["primary_refresh_credit_floor"], 3)
            self.assertEqual(plan["credit_policy"]["estimated_event_probe_credit_floor"], 3)
            self.assertEqual(plan["estimated_next_batch_credit_floor"], 6)
            self.assertEqual(
                plan["estimated_next_batch_credit_ceiling"],
                plan["credit_policy"]["estimated_next_batch_credit_ceiling"],
            )
            self.assertGreaterEqual(plan["estimated_next_batch_credit_ceiling"], plan["estimated_next_batch_credit_floor"])
            self.assertEqual(plan["fallback_queue_count"], len(EXPECTED_MATCHES))
            self.assertEqual(team_total["provider_status"], "low_yield_in_current_the_odds_api_tab_sample")
            self.assertEqual(plan["operational_decision"]["status"], "alternate_probe_plus_team_total_manual")
            self.assertIn("Team Total 继续 TT-001 人工校验", plan["operational_decision"]["primary_action"])
            self.assertIn("btts", plan["recommended_command"])
            self.assertNotIn("team_totals", plan["recommended_command"])
            self.assertEqual(plan["event_probe_evidence"]["canonical_available_market_counts"]["btts"], 3)
            self.assertTrue(any(row["id"] == "btts" and row["provider_status"] == "available_in_current_the_odds_api_tab_sample" for row in plan["market_family_gaps"]))
            self.assertTrue((output_dir / PROVIDER_ALTERNATE_EVIDENCE_JSON_LATEST).exists())

    def test_provider_alternate_plan_credit_estimate_includes_primary_refresh_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            staged_rel = "provider_raw/provider-credit-cost/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            atomic_write_json(
                staged_path,
                {
                    "matches": [
                        {
                            "provider_event_id": "event-1",
                            "match": "A v B",
                            "commence_time": "2026-06-13T00:00:00Z",
                            "provider_request_kinds": ["odds"],
                            "markets": {"Result": {}, "Handicap": {}, "Total Goals Over/Under": {}},
                        }
                    ]
                },
            )
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": "provider-credit-cost",
                    "scope": "matches",
                    "request_usage": {
                        "request_kind_counts": {"odds": 1},
                        "markets": ["h2h", "spreads", "totals", "btts", "double_chance", "draw_no_bet"],
                        "reported_requests_used_max": 264,
                        "reported_requests_remaining_min": 236,
                        "reported_last_request_cost": 5,
                    },
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "event_count": 1,
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 1,
                                "Handicap": 1,
                                "Total Goals Over/Under": 1,
                                "Both Teams to Score": 0,
                                "Double Chance": 0,
                                "Draw No Bet": 0,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )
            atomic_write_json(
                output_dir / PROVIDER_ALTERNATE_PLAN_JSON_LATEST,
                {
                    "event_probe_evidence": {
                        "market_probe_count": 3,
                        "team_total_available_probe_count": 0,
                        "canonical_available_market_counts": {
                            "btts": 3,
                            "double_chance": 3,
                            "draw_no_bet": 3,
                        },
                        "market_probes": [
                            {
                                "event_id": "sample-1",
                                "available_markets": ["btts", "double_chance", "draw_no_bet"],
                                "has_team_total_ou": False,
                            },
                            {
                                "event_id": "sample-2",
                                "available_markets": ["btts", "double_chance", "draw_no_bet"],
                                "has_team_total_ou": False,
                            },
                            {
                                "event_id": "sample-3",
                                "available_markets": ["btts", "double_chance", "draw_no_bet"],
                                "has_team_total_ou": False,
                            },
                        ],
                    }
                },
            )

            plan = build_provider_alternate_plan(output_dir)
            credit = plan["credit_policy"]

            self.assertEqual(credit["recommended_batch_size"], 1)
            self.assertEqual(credit["primary_refresh_credit_floor"], 3)
            self.assertEqual(credit["estimated_event_probe_credit_floor"], 1)
            self.assertEqual(credit["estimated_event_probe_credit_ceiling"], 4)
            self.assertEqual(credit["estimated_next_batch_credit_floor"], 4)
            self.assertEqual(credit["estimated_next_batch_credit_ceiling"], 7)
            self.assertEqual(plan["estimated_next_batch_credit_floor"], 4)
            self.assertEqual(plan["estimated_next_batch_credit_ceiling"], 7)

    def test_provider_alternate_plan_keeps_low_yield_evidence_across_primary_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            first_refresh_id = "provider-low-yield-first"
            primary = json.loads(json.dumps(the_odds_api_payload_fixture()))
            for event in primary["payload"]:
                for bookmaker in event.get("bookmakers") or []:
                    bookmaker["markets"] = [
                        market for market in bookmaker.get("markets") or [] if market.get("key") in {"h2h", "totals", "spreads"}
                    ]
            event_market_payloads = []
            for index, event in enumerate(primary["payload"][:3]):
                event_market = json.loads(json.dumps(the_odds_api_event_markets_payload_fixture()))
                event_market["event_id"] = event["id"]
                event_market["payload"]["id"] = event["id"]
                event_market["payload"]["bookmakers"][0]["markets"] = [
                    {"key": "h2h"},
                    {"key": "spreads"},
                    {"key": "alternate_spreads"},
                    {"key": "alternate_totals"},
                    {"key": "btts"},
                    {"key": "double_chance"},
                    {"key": "draw_no_bet"},
                ]
                event_market["usage"] = {"requests_remaining": 299 - index, "requests_used": 201 + index, "requests_last": 1}
                event_market_payloads.append(event_market)
            first_payloads = [primary, *event_market_payloads]
            first_raws = adapt_provider_payloads(
                first_payloads,
                refresh_id=first_refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            first_manifest = write_provider_staging_bundle(
                output_dir,
                first_raws,
                refresh_id=first_refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=first_payloads,
            )
            build_provider_coverage(output_dir, first_manifest)
            first_plan = write_provider_alternate_plan_bundle(output_dir, provider_payloads=first_payloads)
            self.assertEqual(first_plan["status"], "in_progress")

            second_refresh_id = "provider-primary-refresh"
            second_payloads = [primary]
            second_raws = adapt_provider_payloads(
                second_payloads,
                refresh_id=second_refresh_id,
                generated_at="2026-06-13T01:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            second_manifest = write_provider_staging_bundle(
                output_dir,
                second_raws,
                refresh_id=second_refresh_id,
                generated_at="2026-06-13T01:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=second_payloads,
            )
            build_provider_coverage(output_dir, second_manifest)
            second_plan = write_provider_alternate_plan_bundle(output_dir, provider_payloads=second_payloads)
            team_total = next(row for row in second_plan["market_family_gaps"] if row["id"] == "team_total_ou")

            self.assertEqual(second_plan["refresh_id"], second_refresh_id)
            self.assertEqual(second_plan["status"], "in_progress")
            self.assertGreater(second_plan["probe_queue_count"], 0)
            self.assertEqual(second_plan["event_probe_evidence"]["market_probe_count"], 3)
            self.assertEqual(second_plan["event_probe_evidence"]["team_total_available_probe_count"], 0)
            self.assertEqual(second_plan["event_probe_evidence"]["canonical_available_market_counts"]["btts"], 3)
            self.assertEqual(team_total["provider_status"], "low_yield_in_current_the_odds_api_tab_sample")
            self.assertEqual(second_plan["operational_decision"]["status"], "alternate_probe_plus_team_total_manual")

    def test_provider_fallback_verification_builds_manual_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-fallback-verification"
            staged_rel = "provider_raw/provider-fallback-verification/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            atomic_write_json(
                staged_path,
                {
                    "matches": [
                        {
                            "provider_event_id": "event-1",
                            "match": "Mexico v South Africa",
                            "commence_time": "2026-06-12T05:00:00Z",
                            "provider_request_kinds": ["odds", "event_odds"],
                            "markets": {
                                "Result": {},
                                "Total Goals Over/Under": {},
                                "Handicap": {},
                            },
                        }
                    ]
                },
            )
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "formal_publish_allowed": False,
                    "full_automation_allowed": False,
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "event_count": 1,
                            "provider_analysis_ready": True,
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 1,
                                "Total Goals Over/Under": 1,
                                "Handicap": 1,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )
            atomic_write_json(
                output_dir / PROVIDER_ALTERNATE_PLAN_JSON_LATEST,
                {
                    "refresh_id": refresh_id,
                    "status": "fallback_required",
                    "fallback_queue_count": 1,
                },
            )
            atomic_write_json(
                output_dir / ODDS_PROVIDER_BLOCKED_LATEST,
                {
                    "provider": "opticodds",
                    "blocker_code": "opticodds_access_denied_1010",
                    "last_good_coverage_preserved": True,
                },
            )

            payload = write_provider_fallback_verification_bundle(output_dir)
            payload_text = json.dumps(payload, ensure_ascii=False)

            self.assertEqual(payload["refresh_id"], refresh_id)
            self.assertGreater(payload["queue_count"], 0)
            self.assertIn("manual_verification_required", payload["status"])
            self.assertEqual(payload["current_executable_new_stake_aud"], 0)
            self.assertEqual(payload["provider_blocker_code"], "opticodds_access_denied_1010")
            self.assertIn("自动下注", payload_text)
            self.assertNotIn("apiKey=", payload_text)
            self.assertTrue((output_dir / PROVIDER_FALLBACK_VERIFICATION_JSON_LATEST).exists())
            self.assertTrue((output_dir / "provider_fallback_verification_latest.md").exists())
            self.assertTrue((output_dir / "provider_fallback_verification_latest.pdf").exists())

    def test_public_snapshot_importer_waits_for_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            payload = write_public_snapshot_import_bundle(output_dir)
            preview_raw = json.loads((output_dir / PUBLIC_SNAPSHOT_IMPORT_PREVIEW_RAW_LATEST).read_text(encoding="utf-8"))
            approval_template = json.loads((output_dir / PUBLIC_SNAPSHOT_APPROVAL_TEMPLATE_JSON_LATEST).read_text(encoding="utf-8"))
            publish_preflight = json.loads((output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "waiting_for_snapshot_import")
            self.assertEqual(payload["match_count"], 0)
            self.assertEqual(payload["current_executable_new_stake_aud"], 0)
            self.assertFalse(payload["formal_publish_allowed"])
            self.assertFalse(payload["full_automation_allowed"])
            self.assertEqual(payload["publish_preflight_summary"]["status"], "waiting_for_snapshot_import")
            self.assertEqual(preview_raw["matches"], [])
            self.assertTrue(preview_raw["snapshot_import_preview_only"])
            self.assertEqual(approval_template["save_as"], DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH)
            self.assertFalse(approval_template["approved_by_user"])
            self.assertEqual(publish_preflight["status"], "waiting_for_snapshot_import")
            self.assertFalse(publish_preflight["snapshot_publish_preflight_passed"])
            self.assertFalse(publish_preflight["formal_publish_allowed"])
            self.assertEqual(publish_preflight["current_executable_new_stake_aud"], 0)
            self.assertTrue((output_dir / PUBLIC_SNAPSHOT_IMPORT_TEMPLATE_JSON_LATEST).exists())
            self.assertTrue((output_dir / PUBLIC_SNAPSHOT_IMPORT_STATUS_JSON_LATEST).exists())
            self.assertTrue((output_dir / "public_snapshot_import_status_latest.md").exists())
            self.assertTrue((output_dir / "public_snapshot_import_status_latest.pdf").exists())
            self.assertTrue((output_dir / "public_snapshot_import_publish_preflight_latest.md").exists())
            self.assertTrue((output_dir / "public_snapshot_import_publish_preflight_latest.pdf").exists())

    def test_public_snapshot_importer_builds_preview_raw_from_matches_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            import_dir = output_dir / PUBLIC_SNAPSHOT_IMPORT_DIR
            import_dir.mkdir(parents=True)
            atomic_write_json(
                import_dir / "world_cup_matches_public_snapshot.json",
                {
                    "generated_at": "2026-06-13T00:00:00Z",
                    "matches": [
                        {
                            "match": "Mexico v South Africa",
                            "markets": {
                                "Result": "Result\nMexico\n2.00\nDraw\n3.20\nSouth Africa\n3.80\n",
                                "Total Goals Over/Under": "Total Goals Over/Under\nOver 2.5 Goals\n2.05\nUnder 2.5 Goals\n1.85\n",
                                "Team Total Goals Over/Under": "Team Total Goals Over/Under\nMexico Over 1.5 Goals\n1.91\nMexico Under 1.5 Goals\n1.91\n",
                            },
                        }
                    ],
                },
            )

            payload = write_public_snapshot_import_bundle(output_dir)
            preview_raw = json.loads((output_dir / PUBLIC_SNAPSHOT_IMPORT_PREVIEW_RAW_LATEST).read_text(encoding="utf-8"))
            publish_preflight = json.loads((output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "snapshot_import_preview_ready")
            self.assertEqual(payload["match_count"], 1)
            self.assertEqual(payload["market_coverage"]["Result"], 1)
            self.assertEqual(payload["market_coverage"]["Total Goals Over/Under"], 1)
            self.assertEqual(payload["market_coverage"]["Team Total Goals Over/Under"], 1)
            self.assertRegex(payload["selected_snapshot_sha256"], r"^[a-f0-9]{64}$")
            self.assertRegex(payload["preview_raw_sha256"], r"^[a-f0-9]{64}$")
            self.assertTrue(preview_raw["snapshot_import_preview_only"])
            self.assertEqual(preview_raw["matches"][0]["match"], "Mexico v South Africa")
            self.assertFalse(preview_raw["formal_publish_allowed"])
            self.assertFalse(preview_raw["full_automation_allowed"])
            self.assertEqual(preview_raw["current_executable_new_stake_aud"], 0)
            self.assertEqual(publish_preflight["status"], "waiting_for_signature")
            self.assertFalse(publish_preflight["snapshot_publish_preflight_passed"])
            self.assertFalse(publish_preflight["formal_publish_allowed"])
            self.assertEqual(publish_preflight["current_executable_new_stake_aud"], 0)

    def test_public_snapshot_importer_publish_preflight_requires_matching_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            import_dir = output_dir / PUBLIC_SNAPSHOT_IMPORT_DIR
            import_dir.mkdir(parents=True)
            atomic_write_json(
                import_dir / "world_cup_matches_public_snapshot.json",
                {
                    "generated_at": "2026-06-13T00:00:00Z",
                    "matches": [
                        {
                            "match": "Mexico v South Africa",
                            "markets": {
                                "Result": "Result\nMexico\n2.00\nDraw\n3.20\nSouth Africa\n3.80\n",
                                "Total Goals Over/Under": "Total Goals Over/Under\nOver 2.5 Goals\n2.05\nUnder 2.5 Goals\n1.85\n",
                            },
                        }
                    ],
                },
            )

            first_payload = write_public_snapshot_import_bundle(output_dir)
            first_preflight = json.loads((output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))
            self.assertEqual(first_preflight["status"], "waiting_for_signature")

            approval_path = output_dir / DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(
                approval_path,
                {
                    "schema_version": 1,
                    "mode": "public_snapshot_import_approval",
                    "scope": "matches",
                    "board_id": "world_cup_matches",
                    "selected_snapshot_sha256": first_payload["selected_snapshot_sha256"],
                    "preview_raw_sha256": "bad",
                    "approved_by_user": True,
                    "operator_initials": "LZ",
                    "signed_at_aest": "2026-06-14 01:45 AEST",
                    "source_verification_note": "manual TAB source checked",
                },
            )
            write_public_snapshot_import_bundle(output_dir)
            blocked = json.loads((output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))
            self.assertEqual(blocked["status"], "blocked_signature_mismatch")
            self.assertTrue(any(row["field"] == "preview_raw_sha256" for row in blocked["issues"]))

            atomic_write_json(
                approval_path,
                {
                    "schema_version": 1,
                    "mode": "public_snapshot_import_approval",
                    "scope": "matches",
                    "board_id": "world_cup_matches",
                    "selected_snapshot_sha256": first_payload["selected_snapshot_sha256"],
                    "preview_raw_sha256": first_payload["preview_raw_sha256"],
                    "approved_by_user": True,
                    "operator_initials": "LZ",
                    "signed_at_aest": "2026-06-14 01:45 AEST",
                    "source_verification_note": "manual TAB source checked",
                },
            )
            payload = write_public_snapshot_import_bundle(output_dir)
            ready = json.loads((output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(ready["status"], "ready_for_snapshot_publish_preflight")
            self.assertTrue(ready["snapshot_publish_preflight_passed"])
            self.assertTrue(ready["publish_compatible_with_snapshot_preview"])
            self.assertTrue(ready["approved_by_user"])
            self.assertFalse(ready["formal_publish_allowed"])
            self.assertFalse(ready["full_automation_allowed"])
            self.assertEqual(ready["current_executable_new_stake_aud"], 0)
            self.assertEqual(payload["publish_preflight_summary"]["status"], "ready_for_snapshot_publish_preflight")
            self.assertTrue(payload["publish_preflight_summary"]["snapshot_publish_preflight_passed"])

    def test_public_snapshot_raw_publish_blocks_without_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            import_dir = output_dir / PUBLIC_SNAPSHOT_IMPORT_DIR
            import_dir.mkdir(parents=True)
            atomic_write_json(import_dir / "world_cup_matches_public_snapshot.json", full_matches_raw_fixture())

            result = publish_public_snapshot_raw(output_dir)

            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "blocked_publish_preflight")
            self.assertTrue(any(row["field"] == "preflight" for row in result["issues"]))
            self.assertFalse((output_dir / current_matches_board().raw_snapshot).exists())
            self.assertEqual(result["current_executable_new_stake_aud"], 0)
            self.assertTrue((output_dir / PUBLIC_SNAPSHOT_RAW_PUBLISH_JSON_LATEST).exists())
            self.assertTrue((output_dir / PUBLIC_SNAPSHOT_RAW_PUBLISH_MD_LATEST).exists())
            self.assertTrue((output_dir / PUBLIC_SNAPSHOT_RAW_PUBLISH_PDF_LATEST).exists())

    def test_public_snapshot_raw_publish_writes_matches_raw_after_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            import_dir = output_dir / PUBLIC_SNAPSHOT_IMPORT_DIR
            import_dir.mkdir(parents=True)
            atomic_write_json(import_dir / "world_cup_matches_public_snapshot.json", full_matches_raw_fixture())

            first_payload = write_public_snapshot_import_bundle(output_dir)
            approval_path = output_dir / DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(
                approval_path,
                {
                    "schema_version": 1,
                    "mode": "public_snapshot_import_approval",
                    "scope": "matches",
                    "board_id": "world_cup_matches",
                    "selected_snapshot_sha256": first_payload["selected_snapshot_sha256"],
                    "preview_raw_sha256": first_payload["preview_raw_sha256"],
                    "approved_by_user": True,
                    "operator_initials": "LZ",
                    "signed_at_aest": "2026-06-14 02:10 AEST",
                    "source_verification_note": "manual TAB source checked",
                },
            )

            result = publish_public_snapshot_raw(output_dir)
            published_raw = json.loads((output_dir / current_matches_board().raw_snapshot).read_text(encoding="utf-8"))

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "published_scope_matches")
            self.assertEqual(result["published_raw_snapshot"], current_matches_board().raw_snapshot)
            self.assertTrue(result["formal_raw_publish_performed"])
            self.assertFalse(result["full_automation_allowed"])
            self.assertFalse(result["raw_batch_manifest_written"])
            self.assertFalse((output_dir / "raw_refresh_batch_latest.json").exists())
            self.assertEqual(result["current_executable_new_stake_aud"], 0)
            self.assertEqual(published_raw["source_mode"], "user_public_snapshot_manual_verified")
            self.assertFalse(published_raw["snapshot_import_preview_only"])
            self.assertTrue(published_raw["public_snapshot_publish_verified"])
            self.assertRegex(published_raw["refresh_id"], r"public-snapshot$")
            self.assertTrue(validate_raw_snapshot("world_cup_matches", published_raw)["valid"])

    def test_public_snapshot_importer_blocks_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            import_dir = output_dir / PUBLIC_SNAPSHOT_IMPORT_DIR
            import_dir.mkdir(parents=True)
            atomic_write_text(import_dir / "world_cup_matches_public_snapshot.json", "{bad json")

            payload = write_public_snapshot_import_bundle(output_dir)
            preview_raw = json.loads((output_dir / PUBLIC_SNAPSHOT_IMPORT_PREVIEW_RAW_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "blocked_import_errors")
            self.assertIn("JSONDecodeError", payload["issues"][0]["issue"])
            self.assertEqual(payload["current_executable_new_stake_aud"], 0)
            self.assertEqual(preview_raw["matches"], [])
            self.assertFalse(preview_raw["formal_publish_allowed"])

    def test_provider_manual_verification_writes_template_when_import_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-manual-missing"
            staged_rel = "provider_raw/provider-manual-missing/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            atomic_write_json(
                staged_path,
                {
                    "matches": [
                        {
                            "provider_event_id": "event-1",
                            "match": "Qatar v Switzerland",
                            "commence_time": "2026-06-12T05:00:00Z",
                            "markets": {
                                "Result": {},
                                "Total Goals Over/Under": {},
                            },
                        }
                    ]
                },
            )
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 1,
                                "Total Goals Over/Under": 1,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )

            payload = write_provider_manual_verification_bundle(output_dir)
            template_text = (output_dir / PROVIDER_MANUAL_VERIFICATION_TEMPLATE_CSV_LATEST).read_text(encoding="utf-8")
            pair_template_rows = read_csv_rows(output_dir / PROVIDER_MANUAL_PAIR_TEMPLATE_CSV_LATEST)
            next_batch_pair_rows = read_csv_rows(output_dir / PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST)
            hash_gate = json.loads((output_dir / PROVIDER_MANUAL_HASH_GATE_JSON_LATEST).read_text(encoding="utf-8"))
            overlay_preview = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_PREVIEW_JSON_LATEST).read_text(encoding="utf-8"))
            overlay_raw = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_RAW_LATEST).read_text(encoding="utf-8"))
            approval_template = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_APPROVAL_TEMPLATE_JSON_LATEST).read_text(encoding="utf-8"))
            overlay_preflight = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))
            workbench = json.loads((output_dir / PROVIDER_MANUAL_WORKBENCH_JSON_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "import_missing")
            self.assertEqual(payload["completion"]["complete_event_count"], 0)
            self.assertEqual(payload["current_executable_new_stake_aud"], 0)
            self.assertEqual(hash_gate["status"], "waiting_for_import")
            self.assertEqual(hash_gate["manual_import_sha256"], "")
            self.assertFalse(hash_gate["ready_for_manual_signature"])
            self.assertFalse(hash_gate["provider_tab_final_verification_draft"]["approved_by_user"])
            self.assertEqual(overlay_preview["status"], "waiting_for_import")
            self.assertEqual(overlay_preview["overlay_event_count"], 0)
            self.assertFalse(overlay_preview["ready_for_publish_preflight"])
            self.assertFalse(overlay_preview["formal_publish_allowed"])
            self.assertFalse(overlay_preview["provider_tab_final_verification_overlay_draft"]["approved_by_user"])
            self.assertEqual(overlay_preview["current_executable_new_stake_aud"], 0)
            self.assertEqual(overlay_raw["matches"], [])
            self.assertTrue(overlay_raw["overlay_preview_only"])
            self.assertEqual(approval_template["save_as"], DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH)
            self.assertEqual(approval_template["approved_by_user"], False)
            self.assertEqual(overlay_preflight["status"], "waiting_for_import")
            self.assertFalse(overlay_preflight["overlay_publish_preflight_passed"])
            self.assertFalse(overlay_preflight["publish_compatible_with_provider_raw"])
            self.assertFalse(overlay_preflight["formal_publish_allowed"])
            self.assertEqual(overlay_preflight["current_executable_new_stake_aud"], 0)
            self.assertEqual(workbench["status"], "waiting_for_first_batch")
            self.assertEqual(workbench["queue_count"], 1)
            self.assertEqual(workbench["remaining_event_count"], 1)
            self.assertEqual(workbench["next_batch"]["batch_id"], "TT-001")
            self.assertEqual(workbench["next_batch"]["event_count"], 1)
            self.assertEqual(workbench["pair_templates"]["all_candidate_pair_rows"], 2)
            self.assertEqual(workbench["pair_templates"]["next_batch_pair_rows"], 2)
            self.assertEqual(workbench["operator_cockpit"]["current_batch_id"], "TT-001")
            self.assertEqual(workbench["operator_cockpit"]["current_batch_pair_rows"], 2)
            self.assertEqual(workbench["operator_cockpit"]["import_target"], DEFAULT_IMPORT_RELATIVE_PATH)
            self.assertEqual(workbench["operator_cockpit"]["publish_status"], "blocked_until_manual_import_and_signature")
            self.assertFalse(workbench["operator_cockpit"]["can_publish_now"])
            self.assertEqual(workbench["manual_intake_contract"]["current_batch_id"], "TT-001")
            self.assertEqual(workbench["manual_intake_contract"]["template_csv"], PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST)
            self.assertEqual(workbench["manual_intake_contract"]["import_target"], DEFAULT_IMPORT_RELATIVE_PATH)
            self.assertEqual(
                workbench["manual_intake_contract"]["rebuild_command"],
                "TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py",
            )
            self.assertIn("current_executable_new_stake_aud=0", " ".join(workbench["manual_intake_contract"]["acceptance_criteria"]))
            self.assertIn("点击赔率", " ".join(workbench["manual_intake_contract"]["forbidden_actions"]))
            self.assertEqual(workbench["next_batch_summary"]["pair_rows_required"], 2)
            self.assertEqual(workbench["next_batch_summary"]["high_priority_count"], 1)
            self.assertEqual(payload["import_quality"]["status"], "waiting_for_manual_rows")
            self.assertEqual(payload["import_quality"]["missing_event_count"], 1)
            self.assertEqual(payload["import_quality"]["event_quality"][0]["status"], "missing_rows")
            self.assertIn("over", payload["import_quality"]["event_quality"][0]["missing_directions"])
            self.assertIn("under", payload["import_quality"]["event_quality"][0]["missing_directions"])
            self.assertEqual(workbench["import_quality"]["status"], "waiting_for_manual_rows")
            self.assertEqual(workbench["next_batch_quality"]["status_counts"]["missing_rows"], 1)
            self.assertEqual(workbench["quality_gate_summary"]["import_quality_status"], "waiting_for_manual_rows")
            self.assertEqual(workbench["quality_gate_summary"]["missing_event_count"], 1)
            self.assertTrue(any(row["field"] == "decimal_odds" for row in workbench["field_checklist"]))
            self.assertTrue(any(row["field"] == "tab_match_name" for row in workbench["field_checklist"]))
            self.assertTrue(any(row["field"] == "operator_initials" for row in workbench["field_checklist"]))
            self.assertTrue(any(row["field"] == "verification_status" for row in workbench["field_checklist"]))
            self.assertTrue(any(step["title"] == "只读 TAB 核验" for step in workbench["workflow_steps"]))
            self.assertIn("点击赔率", " ".join(workbench["action_contract"]["forbidden_actions"]))
            self.assertEqual(len(pair_template_rows), 2)
            self.assertEqual(len(next_batch_pair_rows), 2)
            self.assertEqual({row["direction_hint"] for row in pair_template_rows}, {"Over", "Under"})
            self.assertEqual(workbench["current_executable_new_stake_aud"], 0)
            self.assertIn("event-1", template_text)
            self.assertIn("tab_market_name", template_text)
            self.assertTrue((output_dir / PROVIDER_MANUAL_VERIFICATION_STATUS_JSON_LATEST).exists())
            self.assertTrue((output_dir / "provider_manual_verification_status_latest.md").exists())
            self.assertTrue((output_dir / "provider_manual_verification_status_latest.pdf").exists())
            self.assertTrue((output_dir / "provider_manual_hash_gate_latest.md").exists())
            self.assertTrue((output_dir / "provider_manual_hash_gate_latest.pdf").exists())
            self.assertTrue((output_dir / "provider_manual_overlay_preview_latest.md").exists())
            self.assertTrue((output_dir / "provider_manual_overlay_preview_latest.pdf").exists())
            self.assertTrue((output_dir / "provider_manual_overlay_publish_preflight_latest.md").exists())
            self.assertTrue((output_dir / "provider_manual_overlay_publish_preflight_latest.pdf").exists())
            self.assertTrue((output_dir / PROVIDER_MANUAL_WORKBENCH_MD_LATEST).exists())
            self.assertTrue((output_dir / PROVIDER_MANUAL_WORKBENCH_PDF_LATEST).exists())
            self.assertTrue((output_dir / PROVIDER_MANUAL_PAIR_TEMPLATE_CSV_LATEST).exists())
            self.assertTrue((output_dir / PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST).exists())

    def test_provider_manual_verification_template_and_workbench_do_not_truncate_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-manual-full-queue"
            staged_rel = "provider_raw/provider-manual-full-queue/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            matches = [
                {
                    "provider_event_id": f"event-{index}",
                    "match": f"Team {index}A v Team {index}B",
                    "commence_time": f"2026-06-{10 + (index % 10):02d}T05:00:00Z",
                    "markets": {
                        "Result": {},
                        "Total Goals Over/Under": {},
                    },
                }
                for index in range(1, 69)
            ]
            atomic_write_json(staged_path, {"matches": matches})
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 68,
                                "Total Goals Over/Under": 68,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )

            payload = write_provider_manual_verification_bundle(output_dir)
            template_rows = read_csv_rows(output_dir / PROVIDER_MANUAL_VERIFICATION_TEMPLATE_CSV_LATEST)
            template_text = (output_dir / PROVIDER_MANUAL_VERIFICATION_TEMPLATE_CSV_LATEST).read_text(encoding="utf-8")
            pair_template_rows = read_csv_rows(output_dir / PROVIDER_MANUAL_PAIR_TEMPLATE_CSV_LATEST)
            next_batch_pair_rows = read_csv_rows(output_dir / PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST)
            workbench = json.loads((output_dir / PROVIDER_MANUAL_WORKBENCH_JSON_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(payload["queue_count"], 68)
            self.assertEqual(len(payload["queue"]), 68)
            self.assertEqual(len(template_rows), 68)
            self.assertIn("event-68", template_text)
            self.assertEqual(len(pair_template_rows), 136)
            self.assertEqual(len(next_batch_pair_rows), 16)
            self.assertEqual({row["direction_hint"] for row in next_batch_pair_rows}, {"Over", "Under"})
            self.assertEqual(workbench["queue_count"], 68)
            self.assertEqual(workbench["remaining_event_count"], 68)
            self.assertEqual(workbench["remaining_high_priority_count"], 68)
            self.assertEqual(workbench["batch_count"], 9)
            self.assertEqual(workbench["next_batch"]["batch_id"], "TT-001")
            self.assertEqual(workbench["next_batch"]["event_count"], 8)
            self.assertEqual(workbench["batches"][-1]["event_count"], 4)
            self.assertEqual(workbench["pair_templates"]["all_candidate_pair_rows"], 136)
            self.assertEqual(workbench["pair_templates"]["next_batch_pair_rows"], 16)
            self.assertEqual(workbench["operator_cockpit"]["current_batch_event_count"], 8)
            self.assertEqual(workbench["operator_cockpit"]["current_batch_pair_rows"], 16)
            self.assertEqual(workbench["manual_intake_contract"]["current_state"]["missing_event_count"], 68)
            self.assertEqual(workbench["manual_intake_contract"]["current_state"]["next_batch_pair_rows"], 16)
            self.assertIn("outputs/", workbench["manual_intake_contract"]["import_target_display"])
            self.assertEqual(workbench["next_batch_summary"]["rank_start"], 1)
            self.assertEqual(workbench["next_batch_summary"]["rank_end"], 8)
            self.assertEqual(len(workbench["next_batch_summary"]["top_matches"]), 5)
            self.assertEqual(workbench["next_batch_quality"]["status_counts"]["missing_rows"], 8)
            self.assertEqual(workbench["quality_gate_summary"]["missing_event_count"], 68)
            self.assertGreaterEqual(len(workbench["field_checklist"]), 11)
            self.assertEqual(workbench["workflow_steps"][0]["status"], "manual_required")
            self.assertFalse(workbench["formal_publish_allowed"])
            self.assertFalse(workbench["full_automation_allowed"])
            self.assertEqual(workbench["current_executable_new_stake_aud"], 0)

    def test_provider_manual_verification_accepts_complete_over_under_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-manual-ready"
            staged_rel = "provider_raw/provider-manual-ready/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            atomic_write_json(
                staged_path,
                {
                    "matches": [
                        {
                            "provider_event_id": "event-1",
                            "match": "Qatar v Switzerland",
                            "commence_time": "2026-06-12T05:00:00Z",
                            "markets": {
                                "Result": {},
                                "Total Goals Over/Under": {},
                            },
                        }
                    ]
                },
            )
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 1,
                                "Total Goals Over/Under": 1,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )
            import_path = output_dir / DEFAULT_IMPORT_RELATIVE_PATH
            import_path.parent.mkdir(parents=True)
            atomic_write_text(
                import_path,
                "\n".join(
                    [
                        "event_id,rank,match,commence_time,priority_tier,missing_market,tab_match_name,team_scope,tab_market_name,selection_name,line,decimal_odds,observed_at_aest,operator_initials,evidence_note_or_screenshot_ref,verification_status",
                        "event-1,1,Qatar v Switzerland,2026-06-12T05:00:00Z,high,Team Total Goals Over/Under,Qatar v Switzerland,home,Qatar Team Total Goals,Over,1.5,1.91,2026-06-14 00:30 AEST,LZ,note,verified",
                        "event-1,1,Qatar v Switzerland,2026-06-12T05:00:00Z,high,Team Total Goals Over/Under,Qatar v Switzerland,home,Qatar Team Total Goals,Under,1.5,1.91,2026-06-14 00:30 AEST,LZ,note,verified",
                    ]
                )
                + "\n",
            )

            payload = write_provider_manual_verification_bundle(output_dir)
            hash_gate = json.loads((output_dir / PROVIDER_MANUAL_HASH_GATE_JSON_LATEST).read_text(encoding="utf-8"))
            overlay_preview = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_PREVIEW_JSON_LATEST).read_text(encoding="utf-8"))
            overlay_raw = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_RAW_LATEST).read_text(encoding="utf-8"))
            overlay_preflight = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "import_ready_for_hash_gate")
            self.assertEqual(payload["import_quality"]["status"], "complete_quality_ready_for_hash_gate")
            self.assertEqual(payload["import_quality"]["event_quality"][0]["status"], "complete_pair")
            self.assertEqual(payload["import_quality"]["direction_coverage"]["complete_direction_pair_count"], 1)
            self.assertEqual(payload["completion"]["complete_event_count"], 1)
            self.assertEqual(payload["completion"]["invalid_row_count"], 0)
            self.assertEqual(payload["completion"]["high_priority_complete_count"], 1)
            self.assertEqual(payload["current_executable_new_stake_aud"], 0)
            self.assertEqual(hash_gate["status"], "ready_full_manual_hash")
            self.assertRegex(hash_gate["manual_import_sha256"], r"^[a-f0-9]{64}$")
            self.assertTrue(hash_gate["ready_for_manual_signature"])
            self.assertFalse(hash_gate["provider_tab_final_verification_draft"]["approved_by_user"])
            self.assertFalse(hash_gate["provider_tab_final_verification_draft"]["publish_compatible_with_provider_raw"])
            self.assertEqual(hash_gate["current_executable_new_stake_aud"], 0)
            self.assertIn("hash gate", payload["recommended_next_action"])
            self.assertEqual(overlay_preview["status"], "overlay_preview_full")
            self.assertEqual(overlay_preview["overlay_event_count"], 1)
            self.assertEqual(overlay_preview["overlay_row_count"], 2)
            self.assertRegex(overlay_preview["overlay_raw_sha256"], r"^[a-f0-9]{64}$")
            self.assertTrue(overlay_preview["ready_for_publish_preflight"])
            self.assertFalse(overlay_preview["formal_publish_allowed"])
            self.assertFalse(overlay_preview["provider_tab_final_verification_overlay_draft"]["approved_by_user"])
            self.assertFalse(overlay_preview["provider_tab_final_verification_overlay_draft"]["publish_compatible_with_provider_raw"])
            self.assertEqual(overlay_preview["current_executable_new_stake_aud"], 0)
            self.assertTrue(overlay_raw["overlay_preview_only"])
            self.assertEqual(overlay_raw["team_total_overlay_event_count"], 1)
            market_text = overlay_raw["matches"][0]["markets"]["Team Total Goals Over/Under"]
            self.assertIn("Qatar Over 1.5 Goals", market_text)
            self.assertIn("Qatar Under 1.5 Goals", market_text)
            self.assertEqual(overlay_preflight["status"], "waiting_for_signature")
            self.assertFalse(overlay_preflight["overlay_publish_preflight_passed"])
            self.assertFalse(overlay_preflight["formal_publish_allowed"])
            self.assertEqual(overlay_preflight["current_executable_new_stake_aud"], 0)

    def test_provider_manual_overlay_publish_preflight_requires_matching_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-manual-signature"
            staged_rel = "provider_raw/provider-manual-signature/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            atomic_write_json(
                staged_path,
                {
                    "matches": [
                        {
                            "provider_event_id": "event-1",
                            "match": "Qatar v Switzerland",
                            "commence_time": "2026-06-12T05:00:00Z",
                            "markets": {
                                "Result": {},
                                "Total Goals Over/Under": {},
                            },
                        }
                    ]
                },
            )
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 1,
                                "Total Goals Over/Under": 1,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )
            import_path = output_dir / DEFAULT_IMPORT_RELATIVE_PATH
            import_path.parent.mkdir(parents=True)
            atomic_write_text(
                import_path,
                "\n".join(
                    [
                        "event_id,rank,match,commence_time,priority_tier,missing_market,tab_match_name,team_scope,tab_market_name,selection_name,line,decimal_odds,observed_at_aest,operator_initials,evidence_note_or_screenshot_ref,verification_status",
                        "event-1,1,Qatar v Switzerland,2026-06-12T05:00:00Z,high,Team Total Goals Over/Under,Qatar v Switzerland,home,Qatar Team Total Goals,Over,1.5,1.91,2026-06-14 00:30 AEST,LZ,note,verified",
                        "event-1,1,Qatar v Switzerland,2026-06-12T05:00:00Z,high,Team Total Goals Over/Under,Qatar v Switzerland,home,Qatar Team Total Goals,Under,1.5,1.91,2026-06-14 00:30 AEST,LZ,note,verified",
                    ]
                )
                + "\n",
            )

            write_provider_manual_verification_bundle(output_dir)
            overlay_preview = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_PREVIEW_JSON_LATEST).read_text(encoding="utf-8"))
            approval_path = output_dir / DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(
                approval_path,
                {
                    "schema_version": 1,
                    "mode": "provider_manual_team_total_overlay_approval",
                    "refresh_id": refresh_id,
                    "board_id": "world_cup_matches",
                    "market_family": "Team Total Goals Over/Under",
                    "manual_import_sha256": overlay_preview["manual_import_sha256"],
                    "overlay_raw_sha256": "bad",
                    "approved_by_user": True,
                    "operator_initials": "LZ",
                    "signed_at_aest": "2026-06-14 01:05 AEST",
                },
            )

            write_provider_manual_verification_bundle(output_dir)
            blocked = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))
            self.assertEqual(blocked["status"], "blocked_signature_mismatch")
            self.assertFalse(blocked["overlay_publish_preflight_passed"])
            self.assertTrue(any(row["field"] == "overlay_raw_sha256" for row in blocked["issues"]))

            atomic_write_json(
                approval_path,
                {
                    "schema_version": 1,
                    "mode": "provider_manual_team_total_overlay_approval",
                    "refresh_id": refresh_id,
                    "board_id": "world_cup_matches",
                    "market_family": "Team Total Goals Over/Under",
                    "manual_import_sha256": overlay_preview["manual_import_sha256"],
                    "overlay_raw_sha256": overlay_preview["overlay_raw_sha256"],
                    "approved_by_user": True,
                    "operator_initials": "LZ",
                    "signed_at_aest": "2026-06-14 01:05 AEST",
                },
            )
            payload = write_provider_manual_verification_bundle(output_dir)
            ready = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_JSON_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(ready["status"], "ready_for_overlay_publish_preflight")
            self.assertTrue(ready["overlay_publish_preflight_passed"])
            self.assertTrue(ready["publish_compatible_with_provider_raw"])
            self.assertTrue(ready["approved_by_user"])
            self.assertFalse(ready["formal_publish_allowed"])
            self.assertEqual(ready["current_executable_new_stake_aud"], 0)
            self.assertTrue(payload["overlay_publish_preflight_summary"]["overlay_publish_preflight_passed"])

    def test_provider_manual_overlay_publish_blocks_without_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-manual-publish-blocked"
            staged_rel = "provider_raw/provider-manual-publish-blocked/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            atomic_write_json(
                staged_path,
                {
                    "matches": [
                        {
                            "provider_event_id": "event-1",
                            "match": "Qatar v Switzerland",
                            "commence_time": "2026-06-12T05:00:00Z",
                            "markets": {
                                "Result": {},
                                "Total Goals Over/Under": {},
                            },
                        }
                    ]
                },
            )
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 1,
                                "Total Goals Over/Under": 1,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )

            result = publish_provider_manual_overlay(output_dir)

            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "blocked_overlay_publish_preflight")
            self.assertTrue(any(row["field"] == "preflight" for row in result["issues"]))
            self.assertFalse((output_dir / current_matches_board().raw_snapshot).exists())
            self.assertEqual(result["current_executable_new_stake_aud"], 0)
            self.assertTrue((output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_JSON_LATEST).exists())
            self.assertTrue((output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_MD_LATEST).exists())
            self.assertTrue((output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PDF_LATEST).exists())

    def test_provider_manual_overlay_publish_writes_matches_raw_after_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-manual-publish-ready"
            staged_rel = "provider_raw/provider-manual-publish-ready/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            staged_raw = full_provider_matches_raw_fixture()
            staged_raw["refresh_id"] = refresh_id
            atomic_write_json(staged_path, staged_raw)
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": len(EXPECTED_MATCHES),
                                "Total Goals Over/Under": len(EXPECTED_MATCHES),
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )
            import_path = output_dir / DEFAULT_IMPORT_RELATIVE_PATH
            import_path.parent.mkdir(parents=True)
            first_match = EXPECTED_MATCHES[0]
            home_team = first_match.split(" v ", 1)[0]
            atomic_write_text(
                import_path,
                "\n".join(
                    [
                        "event_id,rank,match,commence_time,priority_tier,missing_market,tab_match_name,team_scope,tab_market_name,selection_name,line,decimal_odds,observed_at_aest,operator_initials,evidence_note_or_screenshot_ref,verification_status",
                        f"event-1,1,{first_match},2026-06-12T05:00:00Z,high,Team Total Goals Over/Under,{first_match},home,{home_team} Team Total Goals,Over,1.5,1.91,2026-06-14 00:30 AEST,LZ,note,verified",
                        f"event-1,1,{first_match},2026-06-12T05:00:00Z,high,Team Total Goals Over/Under,{first_match},home,{home_team} Team Total Goals,Under,1.5,1.91,2026-06-14 00:30 AEST,LZ,note,verified",
                    ]
                )
                + "\n",
            )
            write_provider_manual_verification_bundle(output_dir)
            overlay_preview = json.loads((output_dir / PROVIDER_MANUAL_OVERLAY_PREVIEW_JSON_LATEST).read_text(encoding="utf-8"))
            approval_path = output_dir / DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(
                approval_path,
                {
                    "schema_version": 1,
                    "mode": "provider_manual_team_total_overlay_approval",
                    "refresh_id": refresh_id,
                    "board_id": "world_cup_matches",
                    "market_family": "Team Total Goals Over/Under",
                    "manual_import_sha256": overlay_preview["manual_import_sha256"],
                    "overlay_raw_sha256": overlay_preview["overlay_raw_sha256"],
                    "approved_by_user": True,
                    "operator_initials": "LZ",
                    "signed_at_aest": "2026-06-14 02:20 AEST",
                },
            )

            result = publish_provider_manual_overlay(output_dir)
            published_raw = json.loads((output_dir / current_matches_board().raw_snapshot).read_text(encoding="utf-8"))

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "published_scope_matches_overlay")
            self.assertEqual(result["published_raw_snapshot"], current_matches_board().raw_snapshot)
            self.assertTrue(result["formal_raw_publish_performed"])
            self.assertFalse(result["full_automation_allowed"])
            self.assertFalse(result["raw_batch_manifest_written"])
            self.assertFalse((output_dir / "raw_refresh_batch_latest.json").exists())
            self.assertEqual(result["current_executable_new_stake_aud"], 0)
            self.assertEqual(published_raw["source_mode"], "provider_manual_team_total_overlay_verified")
            self.assertFalse(published_raw["overlay_preview_only"])
            self.assertTrue(published_raw["provider_manual_team_total_overlay_published"])
            self.assertRegex(published_raw["refresh_id"], r"manual-overlay$")
            self.assertTrue(validate_raw_snapshot("world_cup_matches", published_raw)["valid"])
            first_published = next(item for item in published_raw["matches"] if item["provider_event_id"] == "event-1")
            self.assertIn("Team Total Goals Over/Under", first_published["markets"])
            self.assertIn(f"{home_team} Over 1.5 Goals", first_published["markets"]["Team Total Goals Over/Under"])

    def test_provider_event_probe_excludes_historical_total_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-history-old"
            historical_payloads = [the_odds_api_event_odds_payload_fixture()]
            raws = adapt_provider_payloads(
                historical_payloads,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            write_provider_staging_bundle(
                output_dir,
                raws,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=historical_payloads,
            )

            covered = historical_market_covered_event_ids(output_dir, ["totals", "alternate_totals"])
            descriptors = provider_event_descriptors([the_odds_api_payload_fixture()])
            next_descriptors = [item for item in descriptors if item["event_id"] not in covered]

            self.assertIn(the_odds_api_tab_event_fixture()["id"], covered)
            self.assertNotEqual(next_descriptors[0]["event_id"], the_odds_api_tab_event_fixture()["id"])

    def test_provider_event_probe_prefers_planned_alternate_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            primary = the_odds_api_payload_fixture()
            descriptors = provider_event_descriptors([primary])
            planned_id = descriptors[1]["event_id"]
            atomic_write_json(
                output_dir / PROVIDER_ALTERNATE_PLAN_JSON_LATEST,
                {
                    "next_probe_queue": [
                        {
                            "event_id": planned_id,
                            "recommended_markets": ["btts", "double_chance", "draw_no_bet"],
                        }
                    ]
                },
            )

            selected = select_event_descriptors_for_event_level_probe(
                output_dir=output_dir,
                primary_payloads=[primary],
                sport="soccer_fifa_world_cup",
                target_markets=["btts", "double_chance", "draw_no_bet"],
                probe_limit=1,
            )

            self.assertEqual([row["event_id"] for row in selected], [planned_id])

    def test_provider_event_probe_skips_previous_event_odds_without_plan_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            primary = the_odds_api_payload_fixture()
            descriptors = provider_event_descriptors([primary])
            already_fetched_id = descriptors[0]["event_id"]
            atomic_write_json(
                output_dir / PROVIDER_ALTERNATE_EVIDENCE_JSON_LATEST,
                {
                    "event_probe_evidence": {
                        "event_odds_event_ids": [already_fetched_id],
                    }
                },
            )

            selected = select_event_descriptors_for_event_level_probe(
                output_dir=output_dir,
                primary_payloads=[primary],
                sport="soccer_fifa_world_cup",
                target_markets=["btts", "double_chance", "draw_no_bet"],
                probe_limit=1,
            )

            self.assertEqual(len(selected), 1)
            self.assertNotEqual(selected[0]["event_id"], already_fetched_id)

    def test_provider_event_probe_skips_previous_market_probe_without_plan_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            primary = the_odds_api_payload_fixture()
            descriptors = provider_event_descriptors([primary])
            already_probed_id = descriptors[0]["event_id"]
            atomic_write_json(
                output_dir / PROVIDER_ALTERNATE_EVIDENCE_JSON_LATEST,
                {
                    "event_probe_evidence": {
                        "probed_event_ids": [already_probed_id],
                    }
                },
            )

            selected = select_event_descriptors_for_event_level_probe(
                output_dir=output_dir,
                primary_payloads=[primary],
                sport="soccer_fifa_world_cup",
                target_markets=["btts", "double_chance", "draw_no_bet"],
                probe_limit=1,
            )

            self.assertEqual(len(selected), 1)
            self.assertNotEqual(selected[0]["event_id"], already_probed_id)

    def test_provider_adapter_merges_historical_event_odds_into_new_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            historical_payloads = [the_odds_api_event_odds_payload_fixture()]
            historical_raws = adapt_provider_payloads(
                historical_payloads,
                refresh_id="provider-history-old",
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            write_provider_staging_bundle(
                output_dir,
                historical_raws,
                refresh_id="provider-history-old",
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=historical_payloads,
            )
            primary = json.loads(json.dumps(the_odds_api_payload_fixture()))
            for event in primary["payload"]:
                for bookmaker in event.get("bookmakers") or []:
                    bookmaker["markets"] = [
                        market for market in bookmaker.get("markets") or [] if market.get("key") in {"h2h", "spreads"}
                    ]
            current_raws = adapt_provider_payloads(
                [primary],
                refresh_id="provider-history-new",
                generated_at="2026-06-13T01:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            merged = merge_historical_provider_raws(current_raws, output_dir, current_refresh_id="provider-history-new")
            mexico = next(item for item in merged["world_cup_matches"]["matches"] if item["match"] == "Mexico v South Africa")

            self.assertTrue(merged["world_cup_matches"]["provider_historical_merge"])
            self.assertIn("Total Goals Over/Under", mexico["markets"])
            self.assertIn("historical_event_odds", mexico["provider_request_kinds"])
            self.assertTrue(mexico["provider_historical_merge"])

    def test_provider_history_merge_can_be_limited_to_requested_markets(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            historical_payloads = [the_odds_api_event_odds_payload_fixture()]
            historical_raws = adapt_provider_payloads(
                historical_payloads,
                refresh_id="provider-history-old",
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            write_provider_staging_bundle(
                output_dir,
                historical_raws,
                refresh_id="provider-history-old",
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=historical_payloads,
            )
            primary = json.loads(json.dumps(the_odds_api_payload_fixture()))
            for event in primary["payload"]:
                for bookmaker in event.get("bookmakers") or []:
                    bookmaker["markets"] = [
                        market for market in bookmaker.get("markets") or [] if market.get("key") in {"h2h", "spreads"}
                    ]
            current_raws = adapt_provider_payloads(
                [primary],
                refresh_id="provider-history-new",
                generated_at="2026-06-13T01:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            merged = merge_historical_provider_raws(
                current_raws,
                output_dir,
                current_refresh_id="provider-history-new",
                market_keys=["totals", "alternate_totals"],
            )
            mexico = next(item for item in merged["world_cup_matches"]["matches"] if item["match"] == "Mexico v South Africa")

            self.assertIn("Total Goals Over/Under", mexico["markets"])
            self.assertNotIn("Team Total Goals Over/Under", mexico["markets"])

    def test_provider_blocked_attempt_preserves_last_good_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-last-good"
            payloads = [the_odds_api_payload_fixture()]
            raws = adapt_provider_payloads(
                payloads,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            manifest = write_provider_staging_bundle(
                output_dir,
                raws,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                provider_payloads=payloads,
            )
            last_good = build_provider_coverage(output_dir, manifest)

            blocked = write_blocked_provider_payload(
                output_dir,
                provider="opticodds",
                refresh_id="provider-optic-blocked",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                error="opticodds HTTP 403: Error 1010: Access denied",
            )
            coverage_after = json.loads((output_dir / ODDS_PROVIDER_COVERAGE_LATEST).read_text(encoding="utf-8"))
            blocked_after = json.loads((output_dir / ODDS_PROVIDER_BLOCKED_LATEST).read_text(encoding="utf-8"))

            self.assertEqual(coverage_after["refresh_id"], last_good["refresh_id"])
            self.assertTrue(coverage_after.get("targets"))
            self.assertEqual(blocked["blocker_code"], "opticodds_access_denied_1010")
            self.assertTrue(blocked["last_good_coverage_preserved"])
            self.assertEqual(blocked_after["refresh_id"], "provider-optic-blocked")

    def test_provider_unknown_sport_blocker_explains_discovery_and_credit_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            blocked = write_blocked_provider_payload(
                output_dir,
                provider="the_odds_api",
                refresh_id="provider-unknown-sport",
                scope="matches",
                target_board_ids=["world_cup_matches"],
                error='the_odds_api HTTP 404: {"message":"Unknown sport"}; provider_request_context(request_kind=odds; sport_key=soccer_fifa_world_cup; markets=h2h; redacted_url=https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/?apiKey=REDACTED)',
            )

            self.assertEqual(blocked["blocker_code"], "provider_unknown_sport")
            self.assertEqual(blocked["diagnostics"]["category"], "the_odds_api_sport_coverage_or_env_mismatch")
            self.assertIn("TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY=1", " ".join(blocked["diagnostics"]["safe_checks"]))
            self.assertIn("Team Total", blocked["diagnostics"]["credit_policy"])
            self.assertFalse(blocked["formal_publish_allowed"])
            self.assertEqual(blocked["current_executable_new_stake_aud"], 0)

    def test_provider_adapter_publishes_only_when_manual_verification_hash_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-verified-batch"
            raws = adapt_provider_payloads(
                [the_odds_api_payload_fixture()],
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                target_board_ids=["world_cup_matches"],
            )
            manifest = write_provider_staging_bundle(
                output_dir,
                raws,
                refresh_id=refresh_id,
                generated_at="2026-06-13T00:00:00Z",
                scope="matches",
                target_board_ids=["world_cup_matches"],
            )
            matches_artifact = next(item for item in manifest["artifacts"] if item["board_id"] == "world_cup_matches")
            verification = {
                "schema_version": 1,
                "refresh_id": refresh_id,
                "approvals": [
                    {
                        "board_id": "world_cup_matches",
                        "sha256": matches_artifact["sha256"],
                        "approved_by_user": True,
                        "tab_checked_at": "2026-06-13T00:05:00Z",
                    }
                ],
            }
            coverage = build_provider_coverage(output_dir, manifest, verification=verification)
            matches_target = next(row for row in coverage["targets"] if row["board_id"] == "world_cup_matches")

            self.assertTrue(matches_target["formal_publish_ready"])
            self.assertTrue(coverage["formal_publish_allowed"])
            self.assertFalse(coverage["full_automation_allowed"])
            result = publish_verified_provider_raw(output_dir, coverage)
            self.assertIn(current_matches_board().raw_snapshot, result["published_raw_snapshots"])

    def test_generate_candidates_includes_team_total_ou_when_provider_supplies_it(self):
        raw = full_matches_raw_fixture()
        first = raw["matches"][0]
        first["markets"]["Team Total Goals Over/Under"] = (
            "Team Total Goals Over/Under\n"
            "Mexico Over 1.5 Goals\n"
            "2.30\n"
            "Mexico Under 1.5 Goals\n"
            "1.60\n"
            "South Africa Over 0.5 Goals\n"
            "2.80\n"
            "South Africa Under 0.5 Goals\n"
            "1.42\n"
        )

        candidates = generate_candidates(raw)

        self.assertTrue(any(item.market == "Team Total Goals Over/Under" for item in candidates))

    def test_raw_refresh_gate_rejects_mixed_refresh_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "outputs"
            driver = root / "work" / "tab-research-pipeline" / "scripts" / "refresh_tab_readonly.mjs"
            output_dir.mkdir()
            driver.parent.mkdir(parents=True)
            driver.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            boards = [
                BoardConfig(
                    board_id=f"test_board_{idx}",
                    refresh_board_id=f"test_{idx}",
                    name=f"Test Board {idx}",
                    tab_path=f"/sports/test/{idx}",
                    priority=idx,
                    version="test",
                    required_for_full_automation=True,
                    parser_strategy="fixture",
                    refresh_method="fixture",
                    raw_snapshot=f"test_raw_{idx}.json",
                    recommendations_artifact=None,
                    gate_artifact=None,
                    report_artifact=None,
                )
                for idx in range(1, 4)
            ]
            for idx, board in enumerate(boards, start=1):
                atomic_write_json(
                    output_dir / board.raw_snapshot,
                    {
                        "generated_at": "2026-06-03T00:00:00Z",
                        "refresh_id": "batch-a" if idx < 3 else "batch-b",
                    },
                )
            manifest = audit_raw_refresh(output_dir, boards=boards, now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc))
            self.assertFalse(manifest["raw_refresh_ready"])
            self.assertFalse(manifest["refresh_batch_ready"])
            self.assertTrue(any("not from one refresh batch" in reason for reason in manifest["blocking_reasons"]))

            atomic_write_json(
                output_dir / boards[-1].raw_snapshot,
                {"generated_at": "2026-06-03T00:00:00Z", "refresh_id": "batch-a"},
            )
            manifest = audit_raw_refresh(output_dir, boards=boards, now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc))
            self.assertFalse(manifest["raw_refresh_ready"])
            self.assertFalse(manifest["refresh_batch_manifest_ready"])
            self.assertTrue(any("batch manifest is missing" in reason for reason in manifest["blocking_reasons"]))
            write_raw_refresh_batch_manifest(output_dir, "batch-a", boards=boards, generated_at="2026-06-03T00:00:00Z")
            manifest = audit_raw_refresh(output_dir, boards=boards, now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc))
            self.assertTrue(manifest["raw_refresh_ready"])
            self.assertTrue(manifest["refresh_batch_ready"])
            self.assertTrue(manifest["refresh_batch_manifest_ready"])

            atomic_write_json(
                output_dir / boards[0].raw_snapshot,
                {"generated_at": "2026-06-03T00:00:00Z", "refresh_id": "batch-a", "changed": True},
            )
            manifest = audit_raw_refresh(output_dir, boards=boards, now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc))
            self.assertFalse(manifest["raw_refresh_ready"])
            self.assertTrue(any("sha256 mismatch" in reason for reason in manifest["blocking_reasons"]))

    def test_raw_refresh_health_classifies_stale_access_denied_and_batch_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "outputs"
            driver = root / "work" / "tab-research-pipeline" / "scripts" / "refresh_tab_readonly.mjs"
            output_dir.mkdir()
            driver.parent.mkdir(parents=True)
            driver.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            boards = [
                BoardConfig(
                    board_id="world_cup_matches",
                    refresh_board_id="matches",
                    name="2026 World Cup Matches",
                    tab_path="/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches",
                    priority=1,
                    version="test",
                    required_for_full_automation=True,
                    parser_strategy="fixture",
                    refresh_method="fixture",
                    raw_snapshot="matches.json",
                    recommendations_artifact=None,
                    gate_artifact=None,
                    report_artifact=None,
                )
            ]
            raw = full_matches_raw_fixture()
            raw["refresh_id"] = "batch-health"
            denied = raw["matches"][0]
            denied["title"] = "Access Denied"
            denied["access_status"] = "access_denied"
            denied["markets"] = {}
            denied["partial_core_only"] = True
            atomic_write_json(output_dir / "matches.json", raw)
            write_raw_refresh_batch_manifest(output_dir, "batch-health", boards=boards, generated_at="2026-06-03T00:00:00Z")

            gate = audit_raw_refresh(output_dir, boards=boards, now=datetime(2026, 6, 3, 8, 30, tzinfo=timezone.utc))
            health = raw_refresh_health(gate)
            self.assertFalse(health["ready"])
            self.assertEqual(health["status"], "blocked")
            self.assertIn("stale_raw", health["blocker_codes"])
            self.assertIn("invalid_raw", health["blocker_codes"])
            self.assertIn("access_denied", health["blocker_codes"])
            self.assertIn("ai_controlled_access_rejected", health["blocker_codes"])
            self.assertEqual(health["access_policy"]["status"], "blocked_by_access_policy")
            self.assertTrue(health["refresh_batch_manifest_ready"])
            self.assertIn("TAB 已拒绝 AI controlled access", health["recommended_next_action"])

    def test_raw_refresh_health_classifies_australia_route_mismatch(self):
        health = raw_refresh_health(
            {
                "generated_at": "2026-06-12T07:24:36Z",
                "raw_refresh_ready": False,
                "refresh_driver_ready": True,
                "refresh_batch_ready": False,
                "refresh_batch_manifest_ready": False,
                "required_target_count": 5,
                "ready_required_target_count": 3,
                "blocking_reasons": [],
                "targets": [],
            },
            refresh_error=(
                "2026 World Cup Australia Markets route mismatch: "
                "landed on 2026 World Cup Matches; TAB live soccer nav may not list this board"
            ),
            refresh_diagnostics={
                "status": "failed",
                "refresh_id": "refresh-live-partial",
                "matches_target_source": "live_board_discovery",
                "matches_target_count": 9,
                "finished_at": "2026-06-12T07:23:00Z",
                "attempts": [
                    {"board_id": "matches", "exit_code": 0, "access_denied": False},
                    {"board_id": "futures", "exit_code": 0, "access_denied": False},
                    {"board_id": "group_betting", "exit_code": 0, "access_denied": False},
                    {"board_id": "australia_markets", "exit_code": 1, "access_denied": False, "error_class": "route_mismatch"},
                ],
            },
        )
        self.assertFalse(health["ready"])
        self.assertIn("route_mismatch", health["blocker_codes"])
        self.assertIn("refresh_command_failed", health["blocker_codes"])
        self.assertIn("TAB 当前导航未列出", health["recommended_next_action"])
        self.assertIn("不用旧盘口生成建议", health["recommended_next_action"])
        partial = health["partial_research_refresh"]
        self.assertEqual(partial["status"], "partial_ready")
        self.assertTrue(partial["research_only_allowed"])
        self.assertEqual(partial["successful_board_count"], 3)
        self.assertEqual(partial["attempted_board_count"], 4)
        self.assertEqual(partial["matches_target_count"], 9)
        self.assertEqual(partial["matches_target_source"], "live_board_discovery")
        self.assertEqual(partial["freshness_sla_hours"], 4.0)
        self.assertEqual(partial["freshness_status"], "fresh_research_only")
        self.assertTrue(partial["fresh_within_sla"])
        self.assertFalse(partial["execution_allowed"])

    def test_raw_refresh_health_classifies_staged_validation_as_partial_coverage(self):
        health = raw_refresh_health(
            {
                "generated_at": "2026-06-13T01:30:53Z",
                "raw_refresh_ready": False,
                "refresh_driver_ready": True,
                "refresh_batch_ready": True,
                "refresh_batch_manifest_ready": True,
                "required_target_count": 5,
                "ready_required_target_count": 3,
                "blocking_reasons": [],
                "targets": [],
            },
            refresh_error=(
                "staged raw validation gate failed; "
                "2026 World Cup Futures staged raw validation failed: Expected 48 teams in futures core table, parsed 20.; "
                "2026 World Cup Group Betting staged raw validation failed: Missing groups: D."
            ),
        )

        self.assertIn("partial_coverage", health["blocker_codes"])
        self.assertIn("refresh_command_failed", health["blocker_codes"])
        self.assertIn("raw 内容不满足覆盖", health["recommended_next_action"])

    def test_partial_research_refresh_freshness_is_recomputed_at_read_time(self):
        partial = normalize_partial_research_refresh(
            {
                "status": "partial_ready",
                "research_only_allowed": True,
                "freshness_status": "fresh_research_only",
                "freshness_sla_hours": 4.0,
                "generated_at": "2026-06-12T17:25:52Z",
                "age_hours": 1.47,
                "fresh_within_sla": True,
                "successful_board_count": 3,
                "attempted_board_count": 4,
                "successful_boards": [{"name": "2026 World Cup Matches"}],
                "failed_boards": [{"name": "2026 World Cup Australia Markets"}],
            },
            now=datetime(2026, 6, 12, 22, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(partial["freshness_status"], "stale_research_only")
        self.assertFalse(partial["fresh_within_sla"])
        self.assertFalse(partial["current_research_only_allowed"])
        self.assertTrue(partial["historical_research_evidence_available"])
        self.assertEqual(partial["age_hours"], 4.57)
        self.assertIn("历史诊断证据", partial["note"])

    def test_raw_refresh_recovery_routes_australia_mismatch_to_live_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "ready_required_target_count": 3,
                    "required_target_count": 5,
                    "blocker_codes": ["refresh_command_failed", "route_mismatch", "stale_raw"],
                    "partial_research_refresh": {
                        "status": "partial_ready",
                        "research_only_allowed": True,
                        "freshness_status": "fresh_research_only",
                        "fresh_within_sla": True,
                        "freshness_sla_hours": 4.0,
                        "generated_at": "2026-06-01T17:25:52Z",
                        "age_hours": 1.47,
                        "successful_board_count": 3,
                        "attempted_board_count": 4,
                        "successful_boards": [{"name": "2026 World Cup Matches"}],
                        "failed_boards": [{"name": "2026 World Cup Australia Markets"}],
                    },
                    "refresh_error": (
                        "2026 World Cup Australia Markets route mismatch: "
                        "landed on 2026 World Cup Matches; TAB live soccer nav may not list this board"
                    ),
                    "targets": [
                        {"board_id": "world_cup_australia_markets", "name": "2026 World Cup Australia Markets", "status": "blocked", "raw_fresh": False, "raw_valid": False, "driver_configured": True, "blocker_codes": ["route_mismatch"]},
                    ],
                },
            )
            atomic_write_json(
                output_dir / "raw_refresh_diagnostics_latest.json",
                {
                    "status": "failed",
                    "continued_after_board_failure": True,
                    "staged_batch_manifest_skipped": True,
                    "board_failures": [
                        {
                            "board_id": "australia_markets",
                            "output": "tab_fifa_world_cup_australia_markets_expanded_raw_v0_17.json",
                            "error": "2026 World Cup Australia Markets route mismatch: landed on 2026 World Cup Matches",
                        }
                    ],
                    "attempts": [
                        {
                            "board_id": "australia_markets",
                            "attempt": 1,
                            "exit_code": 1,
                            "stderr_tail": (
                                "2026 World Cup Australia Markets route mismatch: "
                                "landed on 2026 World Cup Matches; TAB live soccer nav may not list this board"
                            ),
                        }
                    ],
                },
            )
            atomic_write_json(output_dir / "active_timeline_latest.json", {"summary": {"backfill_queue_count": 2}, "backfill_queue": []})
            atomic_write_json(output_dir / "active_backfill_latest.json", {"status": "blocked_by_raw_refresh", "blocked_queue_count": 2})
            payload = write_raw_refresh_recovery_bundle(output_dir)

            self.assertEqual(payload["summary"]["route_mismatch_attempt_count"], 1)
            self.assertEqual(payload["summary"]["board_failure_count"], 1)
            self.assertTrue(payload["summary"]["continued_after_board_failure"])
            self.assertTrue(payload["summary"]["staged_batch_manifest_skipped"])
            self.assertIn("Australia Markets", payload["executive_status"]["primary_blocker"])
            self.assertIn("重新发现 TAB Soccer live board list", payload["executive_status"]["recommended_next_action"])
            self.assertEqual(payload["next_retry_plan"][0]["mode"], "live_board_discovery_review")
            self.assertIn("14 expected markets priced", payload["next_retry_plan"][0]["success_gate"])
            self.assertEqual(payload["board_failure_rows"][0]["board_id"], "australia_markets")
            australia_row = next(row for row in payload["board_recovery_matrix"] if row["board_id"] == "world_cup_australia_markets")
            self.assertEqual(australia_row["automation_action"], "mark_unavailable_review")
            self.assertFalse(australia_row["safe_to_retry_now"])
            self.assertIn("unavailable review queue", australia_row["next_action"])
            self.assertEqual(payload["partial_research_refresh"]["freshness_status"], "stale_research_only")
            self.assertFalse(payload["partial_research_refresh"]["current_research_only_allowed"])
            self.assertTrue((output_dir / RAW_REFRESH_RECOVERY_JSON_LATEST).exists())
            self.assertIn("单板失败隔离", (output_dir / RAW_REFRESH_RECOVERY_MD_LATEST).read_text(encoding="utf-8"))
            self.assertIn("板块级恢复矩阵", (output_dir / RAW_REFRESH_RECOVERY_MD_LATEST).read_text(encoding="utf-8"))

    def test_raw_refresh_recovery_summary_counts_all_attempts_not_preview_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "ready_required_target_count": 0,
                    "required_target_count": 5,
                    "blocker_codes": ["refresh_command_failed"],
                    "targets": [],
                },
            )
            attempts = [
                {
                    "board_id": "matches",
                    "attempt": idx,
                    "exit_code": 0,
                    "access_denied": False,
                    "chunk_offset": (idx - 1) * 5,
                    "chunk_limit": 5,
                }
                for idx in range(1, 11)
            ]
            attempts[-1]["exit_code"] = 1
            attempts[-1]["error"] = "2026 World Cup Australia Markets route mismatch: landed on 2026 World Cup Matches"
            atomic_write_json(
                output_dir / "raw_refresh_diagnostics_latest.json",
                {
                    "status": "failed",
                    "attempts": attempts,
                    "board_failures": [{"board_id": "australia_markets", "output": "australia.json", "error": "route mismatch"}],
                    "continued_after_board_failure": True,
                    "staged_batch_manifest_skipped": True,
                },
            )
            payload = write_raw_refresh_recovery_bundle(output_dir)

            self.assertEqual(payload["summary"]["attempt_count"], 10)
            self.assertEqual(len(payload["attempt_rows"]), 8)
            self.assertEqual(payload["summary"]["route_mismatch_attempt_count"], 1)
            self.assertTrue(payload["summary"]["continued_after_board_failure"])
            self.assertEqual(payload["summary"]["board_recovery_matrix_count"], 5)
            self.assertGreaterEqual(payload["summary"]["board_recovery_unavailable_count"], 1)

    def test_raw_refresh_recovery_routes_successful_futures_with_staged_validation_to_partial_coverage_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "ready_required_target_count": 0,
                    "required_target_count": 5,
                    "blocker_codes": ["refresh_command_failed", "stale_raw"],
                    "partial_research_refresh": {
                        "status": "partial_ready",
                        "research_only_allowed": True,
                        "freshness_status": "fresh_research_only",
                        "fresh_within_sla": True,
                        "freshness_sla_hours": 4.0,
                        "generated_at": "2026-06-13T07:45:00+10:00",
                        "successful_board_count": 3,
                        "failed_board_count": 2,
                        "attempted_board_count": 5,
                        "successful_boards": [{"board_id": "world_cup_futures", "name": "2026 World Cup Futures"}],
                        "failed_boards": [],
                    },
                    "targets": [
                        {"board_id": "world_cup_futures", "name": "2026 World Cup Futures", "status": "blocked", "raw_fresh": False, "raw_valid": True, "driver_configured": True, "blocker_codes": ["stale_raw"]},
                    ],
                },
            )
            atomic_write_json(
                output_dir / "raw_refresh_diagnostics_latest.json",
                {
                    "status": "failed",
                    "attempts": [{"board_id": "futures", "attempt": 1, "exit_code": 0, "access_denied": False}],
                    "error": (
                        "staged raw validation gate failed; refusing to publish raw snapshots: "
                        "2026 World Cup Futures staged raw validation failed: Expected 48 teams in futures core table, parsed 20.; "
                        "2026 World Cup Futures staged raw validation failed: Expected 48 complete futures rows, parsed 0."
                    ),
                },
            )
            atomic_write_json(
                output_dir / "live_board_discovery_latest.json",
                {
                    "expected_board_rows": [
                        {
                            "refresh_board_id": "futures",
                            "live_nav_status": "listed",
                            "matched_link_count": 3,
                        }
                    ]
                },
            )
            payload = write_raw_refresh_recovery_bundle(output_dir)
            futures_row = next(row for row in payload["board_recovery_matrix"] if row["board_id"] == "world_cup_futures")
            self.assertEqual(futures_row["partial_result"], "partial_success")
            self.assertEqual(futures_row["last_exit_code"], 0)
            self.assertEqual(futures_row["automation_action"], "partial_coverage_review")
            self.assertFalse(futures_row["safe_to_retry_now"])
            self.assertEqual(futures_row["staged_validation_error_count"], 2)
            self.assertIn("Expected 48 teams", futures_row["evidence"])
            self.assertEqual(payload["summary"]["board_recovery_partial_coverage_count"], 1)
            self.assertEqual(payload["summary"]["board_recovery_validation_fix_count"], 0)
            self.assertEqual(payload["summary"]["board_recovery_staged_validation_error_count"], 1)

    def test_raw_refresh_recovery_routes_matches_staged_coverage_to_auto_match_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "ready_required_target_count": 3,
                    "required_target_count": 5,
                    "blocker_codes": ["refresh_command_failed", "staged_validation_failed"],
                    "partial_research_refresh": {
                        "status": "partial_ready",
                        "research_only_allowed": True,
                        "freshness_status": "fresh_research_only",
                        "fresh_within_sla": True,
                        "freshness_sla_hours": 4.0,
                        "generated_at": "2026-06-13T08:20:00+10:00",
                        "successful_board_count": 3,
                        "failed_board_count": 2,
                        "attempted_board_count": 5,
                        "successful_boards": [{"board_id": "world_cup_matches", "name": "2026 World Cup Matches"}],
                        "failed_boards": [],
                    },
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "name": "2026 World Cup Matches",
                            "status": "blocked",
                            "raw_fresh": False,
                            "raw_valid": True,
                            "driver_configured": True,
                            "blocker_codes": ["staged_validation_failed"],
                        },
                    ],
                },
            )
            atomic_write_json(
                output_dir / "raw_refresh_diagnostics_latest.json",
                {
                    "status": "failed",
                    "attempts": [{"board_id": "matches", "attempt": 1, "exit_code": 0, "access_denied": False}],
                    "error": (
                        "staged raw validation gate failed; refusing to publish raw snapshots: "
                        "2026 World Cup Matches staged raw validation failed: result market coverage 8/9 does not match detail coverage; "
                        "2026 World Cup Matches staged raw validation failed: full core coverage 8/9 below 90% for Result/Handicap/Total Goals/Both Teams To Score."
                    ),
                },
            )
            atomic_write_json(
                output_dir / "live_board_discovery_latest.json",
                {
                    "expected_board_rows": [
                        {
                            "refresh_board_id": "matches",
                            "live_nav_status": "listed",
                            "matched_link_count": 9,
                        }
                    ]
                },
            )

            payload = write_raw_refresh_recovery_bundle(output_dir)
            matches_row = next(row for row in payload["board_recovery_matrix"] if row["board_id"] == "world_cup_matches")

            self.assertEqual(matches_row["partial_result"], "partial_success")
            self.assertEqual(matches_row["last_exit_code"], 0)
            self.assertEqual(matches_row["automation_action"], "auto_retry_with_match_repair")
            self.assertTrue(matches_row["safe_to_retry_now"])
            self.assertEqual(matches_row["staged_validation_error_count"], 2)
            self.assertIn("--match", matches_row["next_action"])
            self.assertIn("单场", matches_row["success_gate"])
            self.assertEqual(payload["summary"]["board_recovery_match_repair_count"], 1)
            self.assertEqual(payload["summary"]["board_recovery_validation_fix_count"], 0)
            self.assertEqual(payload["summary"]["board_recovery_staged_validation_error_count"], 1)

    def test_raw_refresh_recovery_routes_matches_chunk_quality_errors_to_match_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "ready_required_target_count": 0,
                    "required_target_count": 5,
                    "blocker_codes": ["refresh_command_failed"],
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "name": "2026 World Cup Matches",
                            "status": "blocked",
                            "raw_fresh": False,
                            "raw_valid": True,
                            "driver_configured": True,
                            "blocker_codes": ["refresh_command_failed"],
                        },
                    ],
                },
            )
            atomic_write_json(
                output_dir / "raw_refresh_diagnostics_latest.json",
                {
                    "status": "interrupted",
                    "attempts": [
                        {
                            "board_id": "matches",
                            "attempt": 2,
                            "exit_code": 0,
                            "access_denied": False,
                            "chunk_index": 2,
                            "chunk_offset": 5,
                            "chunk_limit": 4,
                            "chunk_quality_errors": [
                                "chunk market expansion errors remain: Germany v Curacao: Market header expansion failed for Handicap"
                            ],
                        }
                    ],
                },
            )
            atomic_write_json(
                output_dir / "live_board_discovery_latest.json",
                {
                    "expected_board_rows": [
                        {
                            "refresh_board_id": "matches",
                            "live_nav_status": "listed",
                            "matched_link_count": 20,
                        }
                    ]
                },
            )
            atomic_write_json(
                output_dir / "matches_repair_validation_latest.json",
                {
                    "schema_version": 1,
                    "generated_at": "2026-06-13T09:23:11+10:00",
                    "source": "playwright_read_only_match_detail_chunk_validation",
                    "status": "passed",
                    "board_id": "matches",
                    "refresh_id": "codex-offset5-check",
                    "scope": "matches offset 5 limit 4",
                    "trigger": "Germany v Curacao Handicap chunk_quality_errors",
                    "read_only_guard": "market header expansion only; no odds click; wager state guard",
                    "match_count": 4,
                    "market_count": 24,
                    "error_count": 0,
                    "validated_matches": ["Germany v Curacao"],
                },
            )

            payload = write_raw_refresh_recovery_bundle(output_dir)
            matches_row = next(row for row in payload["board_recovery_matrix"] if row["board_id"] == "world_cup_matches")

            self.assertEqual(payload["summary"]["diagnostics_status"], "interrupted")
            self.assertTrue(payload["summary"]["diagnostics_interrupted"])
            self.assertEqual(payload["summary"]["matches_repair_validation_status"], "passed")
            self.assertTrue(payload["summary"]["matches_repair_validation_passed"])
            self.assertEqual(payload["summary"]["matches_repair_validation_market_count"], 24)
            self.assertEqual(matches_row["automation_action"], "auto_retry_with_match_repair")
            self.assertTrue(matches_row["safe_to_retry_now"])
            self.assertEqual(matches_row["repair_validation_status"], "passed")
            self.assertIn("Germany v Curacao", matches_row["evidence"])
            self.assertIn("Handicap", matches_row["evidence"])
            self.assertIn("repair_validation=passed", matches_row["evidence"])
            self.assertEqual(payload["summary"]["board_recovery_match_repair_count"], 1)

    def test_live_board_discovery_bundle_marks_missing_expected_boards(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-12T07:44:00Z",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "title": "Soccer Betting & Odds 2026 - TAB.com.au",
                    "expected_boards": [
                        {
                            "refresh_board_id": "matches",
                            "board": "2026 World Cup Matches",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"}],
                            "automation_decision": "refresh_allowed",
                        },
                        {
                            "refresh_board_id": "australia_markets",
                            "board": "2026 World Cup Australia Markets",
                            "live_nav_status": "missing_from_live_nav",
                            "matched_link_count": 0,
                            "matched_links": [],
                            "automation_decision": "temporarily_unavailable_review",
                        },
                    ],
                    "observed_world_cup_links": [
                        {"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"},
                        {"text": "2026 World Cup Futures", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures"},
                        {
                            "text": "World Cup Group D (USA/TUR/PAR/AUS)",
                            "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Group%20Betting/matches/World%20Cup%20Group%20D%20(USA~2FTUR~2FPAR~2FAUS)",
                        },
                    ],
                },
            )
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "blocker_codes": ["route_mismatch"],
                    "refresh_error": "2026 World Cup Australia Markets route mismatch: landed on 2026 World Cup Matches",
                },
            )
            payload = write_live_board_discovery_bundle(output_dir)

            self.assertEqual(payload["artifacts"]["json"], LIVE_BOARD_DISCOVERY_JSON_LATEST)
            self.assertEqual(payload["artifacts"]["markdown"], LIVE_BOARD_DISCOVERY_MD_LATEST)
            self.assertEqual(payload["artifacts"]["pdf"], LIVE_BOARD_DISCOVERY_PDF_LATEST)
            self.assertEqual(payload["artifacts"]["pdf_summary"]["chart_count"], 4)
            self.assertEqual(payload["artifacts"]["pdf_summary"]["extra_table_count"], 3)
            self.assertIn("old_new_compare", payload)
            self.assertEqual(payload["executive_status"]["status"], "blocked")
            self.assertTrue(payload["executive_status"]["route_mismatch_active"])
            self.assertGreaterEqual(payload["summary"]["missing_expected_count"], 1)
            self.assertTrue(any(row["name"] == "2026 World Cup Australia Markets" for row in payload["unavailable_review_queue"]))
            observed_mapping = {row["text"]: row["mapped_expected_board"] for row in payload["observed_world_cup_links"]}
            self.assertEqual(observed_mapping["World Cup Group D (USA/TUR/PAR/AUS)"], "2026 World Cup Group Betting")
            self.assertIn("不用旧盘口生成下注建议", (output_dir / LIVE_BOARD_DISCOVERY_MD_LATEST).read_text(encoding="utf-8"))
            self.assertIn("新旧发现变化", (output_dir / LIVE_BOARD_DISCOVERY_MD_LATEST).read_text(encoding="utf-8"))
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / LIVE_BOARD_DISCOVERY_JSON_LATEST,
                        output_dir / LIVE_BOARD_DISCOVERY_MD_LATEST,
                        output_dir / LIVE_BOARD_DISCOVERY_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

    def test_live_board_discovery_access_denied_requires_retry_not_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-12T09:39:31.995Z",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "title": "Access Denied",
                    "headless": True,
                    "page_markers": {
                        "text_length": 215,
                        "link_count": 0,
                        "has_soccer": False,
                        "has_world_cup": False,
                        "access_denied": True,
                    },
                    "summary": {
                        "expected_board_count": 5,
                        "listed_expected_count": 0,
                        "missing_expected_count": 5,
                        "observed_world_cup_link_count": 0,
                        "discovery_ready": False,
                        "quality_status": "blocked_access_denied",
                        "quality_issues": ["access_denied", "soccer_page_marker_missing", "link_count_zero"],
                        "access_denied": True,
                        "full_expected_nav_ready": False,
                    },
                    "expected_boards": [
                        {
                            "refresh_board_id": refresh_id,
                            "board": board_name,
                            "live_nav_status": "discovery_blocked",
                            "matched_link_count": 0,
                            "matched_links": [],
                            "automation_decision": "discovery_retry_required",
                        }
                        for refresh_id, board_name in [
                            ("matches", "2026 World Cup Matches"),
                            ("futures", "2026 World Cup Futures"),
                            ("group_betting", "2026 World Cup Group Betting"),
                            ("australia_markets", "2026 World Cup Australia Markets"),
                            ("team_futures_multi", "2026 World Cup Team Futures Multi"),
                        ]
                    ],
                    "observed_world_cup_links": [],
                },
            )
            payload = write_live_board_discovery_bundle(output_dir)

            self.assertFalse(payload["summary"]["discovery_ready"])
            self.assertTrue(payload["summary"]["access_denied"])
            self.assertEqual(payload["summary"]["temporarily_unavailable_count"], 0)
            self.assertEqual(payload["summary"]["retry_required_count"], 5)
            self.assertEqual(payload["unavailable_review_queue"], [])
            self.assertEqual(len(payload["discovery_retry_queue"]), 5)
            self.assertIn("不把板块标记为下架", payload["executive_status"]["recommended_next_action"])
            self.assertIn("Discovery Retry Queue", (output_dir / LIVE_BOARD_DISCOVERY_MD_LATEST).read_text(encoding="utf-8"))

            strategy = write_available_board_strategy_bundle(output_dir, output_dir / "tab_fifa_reports.sqlite3")
            self.assertEqual(strategy["executive_status"]["status"], "blocked")
            self.assertEqual(strategy["summary"]["unavailable_board_count"], 0)
            self.assertEqual(strategy["summary"]["discovery_retry_board_count"], 5)
            self.assertFalse(strategy["summary"]["discovery_ready"])
            self.assertEqual(strategy["excluded_boards"], [])
            self.assertEqual(len(strategy["discovery_retry_boards"]), 5)
            self.assertIn("discovery 质量门禁失败", strategy["executive_status"]["recommended_next_action"])

    def test_live_board_discovery_failed_raw_requires_retry_not_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-13T04:42:08.462408+00:00",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "status": "failed",
                    "refresh_error": "live board discovery failed",
                    "discovery_error": "TAB Soccer navigation returned no usable board payload",
                    "truthfulness_note": "live board discovery failed; do not use old odds for current betting advice.",
                },
            )

            payload = write_live_board_discovery_bundle(output_dir)

            self.assertFalse(payload["summary"]["discovery_ready"])
            self.assertTrue(payload["summary"]["discovery_failed"])
            self.assertEqual(payload["summary"]["temporarily_unavailable_count"], 0)
            self.assertEqual(payload["summary"]["retry_required_count"], 5)
            self.assertEqual(payload["unavailable_review_queue"], [])
            self.assertEqual(len(payload["discovery_retry_queue"]), 5)
            self.assertTrue(
                all(row["automation_decision"] == "discovery_retry_required" for row in payload["expected_board_rows"])
            )
            self.assertIn("TAB 拒绝 AI controlled access", payload["executive_status"]["recommended_next_action"])
            self.assertIn("授权数据源或用户导出导入", payload["executive_status"]["recommended_next_action"])

            strategy = write_available_board_strategy_bundle(output_dir, output_dir / "tab_fifa_reports.sqlite3")
            self.assertFalse(strategy["summary"]["discovery_ready"])
            self.assertEqual(strategy["summary"]["unavailable_board_count"], 0)
            self.assertEqual(strategy["summary"]["discovery_retry_board_count"], 5)
            self.assertEqual(len(strategy["discovery_retry_boards"]), 5)

    def test_available_board_strategy_uses_partial_raw_success_when_discovery_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            db_path = output_dir / "tab_fifa_reports.sqlite3"
            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-13T04:42:08.462408+00:00",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "status": "failed",
                    "refresh_error": "live board discovery failed",
                    "discovery_error": "TAB Soccer navigation returned no usable board payload",
                },
            )
            atomic_write_json(
                output_dir / RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST,
                {
                    "status": "partial_ready_research_only",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "successful_board_count": 4,
                    "failed_board_count": 1,
                    "successful_boards": [
                        {"board_id": "world_cup_matches", "refresh_board_id": "matches", "name": "2026 World Cup Matches"},
                        {"board_id": "world_cup_futures", "refresh_board_id": "futures", "name": "2026 World Cup Futures"},
                        {"board_id": "world_cup_group_betting", "refresh_board_id": "group_betting", "name": "2026 World Cup Group Betting"},
                        {"board_id": "world_cup_team_futures_multi", "refresh_board_id": "team_futures_multi", "name": "2026 World Cup Team Futures Multi"},
                    ],
                    "failed_boards": [
                        {
                            "board_id": "world_cup_australia_markets",
                            "refresh_board_id": "australia_markets",
                            "name": "2026 World Cup Australia Markets",
                        }
                    ],
                },
            )

            write_live_board_discovery_bundle(output_dir)
            strategy = write_available_board_strategy_bundle(output_dir, db_path)

            self.assertFalse(strategy["summary"]["discovery_ready"])
            self.assertEqual(strategy["summary"]["partial_evidence_source"], RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST)
            self.assertEqual(strategy["summary"]["board_scope_source"], "current_discovery+partial_raw_success")
            self.assertEqual(strategy["summary"]["research_allowed_board_count"], 4)
            self.assertEqual(strategy["summary"]["unavailable_board_count"], 1)
            self.assertEqual(strategy["summary"]["discovery_retry_board_count"], 0)
            self.assertEqual(strategy["summary"]["partial_raw_scope_success_count"], 4)
            self.assertEqual(strategy["summary"]["partial_raw_scope_failure_count"], 1)
            allowed_names = {row["name"] for row in strategy["available_research_boards"]}
            self.assertIn("2026 World Cup Team Futures Multi", allowed_names)
            australia = next(row for row in strategy["board_scope_rows"] if row["board_id"] == "world_cup_australia_markets")
            self.assertEqual(australia["board_scope"], "unavailable_excluded")
            self.assertEqual(australia["partial_raw_evidence"], "failure")
            self.assertFalse(strategy["summary"]["executable_report_allowed"])
            self.assertEqual(strategy["summary"]["current_executable_new_stake_aud"], 0)
            recovery = write_raw_refresh_recovery_bundle(output_dir)
            self.assertEqual(recovery["summary"]["effective_board_scope_source"], "current_discovery+partial_raw_success")
            self.assertEqual(recovery["summary"]["board_recovery_research_only_ready_count"], 4)
            self.assertEqual(recovery["summary"]["board_recovery_unavailable_count"], 1)

    def test_available_board_strategy_persists_scope_and_compares_previous_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            db_path = output_dir / "tab_fifa_reports.sqlite3"
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "blocker_codes": ["route_mismatch"],
                    "refresh_error": "2026 World Cup Australia Markets route mismatch: landed on 2026 World Cup Matches",
                },
            )
            atomic_write_json(
                output_dir / "automation_readiness_latest.json",
                {"formal_report_publish_ready": False},
            )
            atomic_write_json(
                output_dir / "active_timeline_report_latest.json",
                {"executive_status": {"status": "blocked"}},
            )
            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-12T07:44:00Z",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "expected_boards": [
                        {
                            "refresh_board_id": "matches",
                            "board": "2026 World Cup Matches",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"}],
                            "automation_decision": "refresh_allowed",
                        }
                    ],
                    "observed_world_cup_links": [
                        {"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"},
                    ],
                },
            )
            write_live_board_discovery_bundle(output_dir)
            first = write_available_board_strategy_bundle(output_dir, db_path)

            self.assertEqual(first["artifacts"]["json"], AVAILABLE_BOARD_STRATEGY_JSON_LATEST)
            self.assertEqual(first["artifacts"]["markdown"], AVAILABLE_BOARD_STRATEGY_MD_LATEST)
            self.assertEqual(first["artifacts"]["pdf"], AVAILABLE_BOARD_STRATEGY_PDF_LATEST)
            self.assertEqual(first["artifacts"]["pdf_summary"]["chart_count"], 6)
            self.assertEqual(first["artifacts"]["pdf_summary"]["extra_table_count"], 4)
            self.assertEqual(first["executive_status"]["status"], "research_only")
            self.assertFalse(first["executive_status"]["executable_report_allowed"])
            self.assertTrue(first["executive_status"]["research_diagnostic_allowed"])
            self.assertEqual(first["summary"]["current_executable_new_stake_aud"], 0)
            self.assertIn("partial_refresh_freshness_status", first["summary"])
            self.assertIn("partial_raw_freshness", first)
            self.assertFalse(first["partial_raw_freshness"]["execution_allowed"])
            self.assertEqual(first["summary"]["board_scope_source"], "current_discovery")
            self.assertEqual(first["storage"]["status"], "stored")
            self.assertIn("AUD 0", (output_dir / AVAILABLE_BOARD_STRATEGY_MD_LATEST).read_text(encoding="utf-8"))
            self.assertIn("partial raw freshness", (output_dir / AVAILABLE_BOARD_STRATEGY_MD_LATEST).read_text(encoding="utf-8"))
            self.assertIn("Last-success Fallback", (output_dir / AVAILABLE_BOARD_STRATEGY_MD_LATEST).read_text(encoding="utf-8"))

            with connect_report_db(db_path) as conn:
                rows = conn.execute("SELECT * FROM available_board_strategy_snapshots").fetchall()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["status"], "research_only")
                self.assertEqual(rows[0]["listed_expected_count"], 1)

            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-12T08:44:00Z",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "expected_boards": [
                        {
                            "refresh_board_id": "matches",
                            "board": "2026 World Cup Matches",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"}],
                            "automation_decision": "refresh_allowed",
                        },
                        {
                            "refresh_board_id": "futures",
                            "board": "2026 World Cup Futures",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Futures", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures"}],
                            "automation_decision": "refresh_allowed",
                        },
                    ],
                    "observed_world_cup_links": [
                        {"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"},
                        {"text": "2026 World Cup Futures", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures"},
                    ],
                },
            )
            write_live_board_discovery_bundle(output_dir)
            second = write_available_board_strategy_bundle(output_dir, db_path)

            self.assertEqual(second["old_new_compare"]["status"], "compared_with_previous_snapshot")
            self.assertEqual(second["old_new_compare"]["listed_count_delta"], 1)
            self.assertEqual(second["old_new_compare"]["missing_count_delta"], -1)
            self.assertTrue(any("Futures" in name for name in second["old_new_compare"]["newly_listed"]))
            with connect_report_db(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM available_board_strategy_snapshots").fetchone()[0], 2)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / AVAILABLE_BOARD_STRATEGY_JSON_LATEST,
                        output_dir / AVAILABLE_BOARD_STRATEGY_MD_LATEST,
                        output_dir / AVAILABLE_BOARD_STRATEGY_PDF_LATEST,
                    ]
                )["public_artifact_safety_ready"]
            )

    def test_partial_daily_research_bundle_marks_unavailable_boards_no_bet(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            db_path = output_dir / "tab_fifa_reports.sqlite3"
            generated_at = datetime.now(timezone.utc).isoformat()
            listed = [
                ("matches", "2026 World Cup Matches"),
                ("futures", "2026 World Cup Futures"),
                ("group_betting", "2026 World Cup Group Betting"),
            ]
            missing = [
                ("australia_markets", "2026 World Cup Australia Markets"),
                ("team_futures_multi", "2026 World Cup Team Futures Multi"),
            ]
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "blocker_codes": ["route_mismatch", "refresh_command_failed", "stale_raw"],
                    "partial_research_refresh": {
                        "status": "partial_ready",
                        "generated_at": generated_at,
                        "freshness_sla_hours": 4,
                        "successful_board_count": 3,
                        "attempted_board_count": 5,
                        "failed_board_count": 2,
                        "successful_boards": [
                            {"board_id": board_id, "name": name}
                            for board_id, name in listed
                        ],
                        "failed_boards": [
                            {"board_id": board_id, "name": name}
                            for board_id, name in missing
                        ],
                    },
                },
            )
            atomic_write_json(
                output_dir / "raw_refresh_diagnostics_latest.json",
                {
                    "status": "failed",
                    "failed_board_ids": ["australia_markets", "team_futures_multi"],
                    "staged_validation_errors": [],
                },
            )
            atomic_write_json(
                output_dir / RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST,
                {
                    "schema_version": 1,
                    "generated_at": generated_at,
                    "refresh_id": "refresh-unit",
                    "status": "partial_ready_research_only",
                    "full_publish_allowed": False,
                    "execution_allowed": False,
                    "current_executable_new_stake_aud": 0,
                    "required_target_count": 5,
                    "ready_required_target_count": 3,
                    "successful_board_count": 3,
                    "failed_board_count": 2,
                    "successful_boards": [
                        {
                            "refresh_board_id": board_id,
                            "board_id": board_id,
                            "name": name,
                            "raw_snapshot": f"{board_id}.json",
                            "research_only_raw_snapshot": f"research_only_raw/refresh-unit_{board_id}.json",
                        }
                        for board_id, name in listed
                    ],
                    "failed_boards": [
                        {
                            "refresh_board_id": board_id,
                            "board_id": board_id,
                            "name": name,
                            "raw_snapshot": f"{board_id}.json",
                        }
                        for board_id, name in missing
                    ],
                },
            )
            atomic_write_json(output_dir / "automation_readiness_latest.json", {"formal_report_publish_ready": False})
            atomic_write_json(output_dir / "active_timeline_report_latest.json", {"executive_status": {"status": "blocked"}})
            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": generated_at,
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "summary": {
                        "expected_board_count": 5,
                        "listed_expected_count": 3,
                        "missing_expected_count": 2,
                        "discovery_ready": True,
                        "quality_status": "ready",
                    },
                    "expected_boards": [
                        {
                            "refresh_board_id": board_id,
                            "board": name,
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": name, "href": f"https://www.tab.com.au/{board_id}"}],
                            "automation_decision": "refresh_allowed",
                        }
                        for board_id, name in listed
                    ]
                    + [
                        {
                            "refresh_board_id": board_id,
                            "board": name,
                            "live_nav_status": "missing_from_live_nav",
                            "matched_link_count": 0,
                            "matched_links": [],
                            "automation_decision": "temporarily_unavailable_review",
                        }
                        for board_id, name in missing
                    ],
                    "observed_world_cup_links": [
                        {"text": name, "href": f"https://www.tab.com.au/{board_id}"}
                        for board_id, name in listed
                    ],
                },
            )

            write_live_board_discovery_bundle(output_dir)
            write_available_board_strategy_bundle(output_dir, db_path)
            write_raw_refresh_recovery_bundle(output_dir)
            payload = write_partial_daily_research_bundle(output_dir, report_date="13062026")

            self.assertEqual(payload["artifacts"]["json"], PARTIAL_DAILY_RESEARCH_JSON_LATEST)
            self.assertEqual(payload["artifacts"]["markdown"], PARTIAL_DAILY_RESEARCH_MD_LATEST)
            self.assertEqual(payload["artifacts"]["pdf"], PARTIAL_DAILY_RESEARCH_PDF_LATEST)
            self.assertEqual(payload["artifacts"]["dated_pdf"], "13062026_partial_daily_research.pdf")
            self.assertEqual(payload["executive_status"]["status"], "ready_research_only")
            self.assertTrue(payload["executive_status"]["partial_daily_report_ready"])
            self.assertFalse(payload["executive_status"]["execution_allowed"])
            self.assertEqual(payload["summary"]["partial_successful_board_count"], 3)
            self.assertEqual(payload["summary"]["partial_evidence_source"], RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST)
            self.assertEqual(payload["summary"]["research_only_raw_status"], "partial_ready_research_only")
            self.assertEqual(payload["summary"]["research_only_raw_successful_board_count"], 3)
            self.assertEqual(payload["summary"]["unavailable_board_count"], 2)
            self.assertEqual(payload["summary"]["current_executable_new_stake_aud"], 0)
            unavailable_rows = [
                row
                for row in payload["board_rows"]
                if row["board_scope"] == "unavailable_excluded"
            ]
            self.assertEqual(len(unavailable_rows), 2)
            self.assertTrue(all(row["betting_action"] == "No Bet / 不下注" for row in unavailable_rows))
            self.assertTrue(all(row["stake_aud"] == 0 for row in payload["board_rows"]))
            self.assertTrue((output_dir / "13062026_partial_daily_research.json").exists())
            self.assertTrue((output_dir / "13062026_partial_daily_research.md").exists())
            self.assertTrue((output_dir / "13062026_partial_daily_research.pdf").exists())
            markdown = (output_dir / PARTIAL_DAILY_RESEARCH_MD_LATEST).read_text(encoding="utf-8")
            self.assertIn("No Bet / 不下注", markdown)
            self.assertIn("unavailable review", markdown)
            self.assertTrue(
                audit_public_artifact_safety(
                    [
                        output_dir / PARTIAL_DAILY_RESEARCH_JSON_LATEST,
                        output_dir / PARTIAL_DAILY_RESEARCH_MD_LATEST,
                        output_dir / PARTIAL_DAILY_RESEARCH_PDF_LATEST,
                        output_dir / "13062026_partial_daily_research.pdf",
                    ]
                )["public_artifact_safety_ready"]
            )

    def test_available_board_strategy_uses_fresh_last_success_when_current_discovery_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            db_path = output_dir / "tab_fifa_reports.sqlite3"
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "blocker_codes": ["refresh_command_failed", "stale_raw"],
                    "partial_research_refresh": {
                        "status": "partial_ready",
                        "freshness_status": "fresh_research_only",
                        "fresh_within_sla": True,
                        "freshness_sla_hours": 4.0,
                        "age_hours": 0.5,
                        "successful_board_count": 3,
                        "attempted_board_count": 4,
                    },
                },
            )
            atomic_write_json(output_dir / "automation_readiness_latest.json", {"formal_report_publish_ready": False})
            atomic_write_json(output_dir / "active_timeline_report_latest.json", {"executive_status": {"status": "blocked"}})
            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-12T18:50:00Z",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "summary": {"discovery_ready": True, "quality_status": "ready"},
                    "expected_boards": [
                        {
                            "refresh_board_id": "matches",
                            "board": "2026 World Cup Matches",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Matches", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches"}],
                            "automation_decision": "refresh_allowed",
                        },
                        {
                            "refresh_board_id": "futures",
                            "board": "2026 World Cup Futures",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Futures", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures"}],
                            "automation_decision": "refresh_allowed",
                        },
                        {
                            "refresh_board_id": "group_betting",
                            "board": "2026 World Cup Group Betting",
                            "live_nav_status": "listed",
                            "matched_link_count": 1,
                            "matched_links": [{"text": "2026 World Cup Group Betting", "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Group%20Betting"}],
                            "automation_decision": "refresh_allowed",
                        },
                    ],
                    "observed_world_cup_links": [],
                },
            )
            write_live_board_discovery_bundle(output_dir)
            first = write_available_board_strategy_bundle(output_dir, db_path)
            self.assertEqual(first["executive_status"]["status"], "research_only")
            self.assertEqual(first["summary"]["research_allowed_board_count"], 3)

            atomic_write_json(
                output_dir / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-12T19:01:25Z",
                    "source": "playwright_read_only_tab_soccer_live_nav",
                    "title": "Access Denied",
                    "headless": True,
                    "page_markers": {
                        "text_length": 215,
                        "link_count": 0,
                        "has_soccer": False,
                        "has_world_cup": False,
                        "access_denied": True,
                    },
                    "summary": {
                        "expected_board_count": 5,
                        "listed_expected_count": 0,
                        "missing_expected_count": 5,
                        "observed_world_cup_link_count": 0,
                        "discovery_ready": False,
                        "quality_status": "blocked_access_denied",
                        "quality_issues": ["access_denied", "soccer_page_marker_missing", "link_count_zero"],
                        "access_denied": True,
                        "full_expected_nav_ready": False,
                    },
                    "expected_boards": [
                        {
                            "refresh_board_id": refresh_id,
                            "board": board_name,
                            "live_nav_status": "discovery_blocked",
                            "matched_link_count": 0,
                            "matched_links": [],
                            "automation_decision": "discovery_retry_required",
                        }
                        for refresh_id, board_name in [
                            ("matches", "2026 World Cup Matches"),
                            ("futures", "2026 World Cup Futures"),
                            ("group_betting", "2026 World Cup Group Betting"),
                            ("australia_markets", "2026 World Cup Australia Markets"),
                            ("team_futures_multi", "2026 World Cup Team Futures Multi"),
                        ]
                    ],
                    "observed_world_cup_links": [],
                },
            )
            write_live_board_discovery_bundle(output_dir)
            second = write_available_board_strategy_bundle(output_dir, db_path)

            self.assertFalse(second["summary"]["discovery_ready"])
            self.assertTrue(second["summary"]["last_success_fallback_used"])
            self.assertEqual(second["summary"]["board_scope_source"], "last_success_fallback")
            self.assertEqual(second["last_success_fallback"]["status"], "fresh_last_success")
            self.assertEqual(second["summary"]["research_allowed_board_count"], 3)
            self.assertEqual(second["summary"]["discovery_retry_board_count"], 0)
            self.assertEqual(len(second["discovery_retry_boards"]), 0)
            self.assertEqual(
                len(
                    [
                        row
                        for row in second["current_discovery_board_scope_rows"]
                        if row["board_scope"] == "discovery_retry_required"
                    ]
                ),
                5,
            )
            self.assertTrue(second["executive_status"]["research_diagnostic_allowed"])
            self.assertFalse(second["executive_status"]["executable_report_allowed"])
            self.assertEqual(second["summary"]["current_executable_new_stake_aud"], 0)
            self.assertTrue(all(row["scope_source"] == "last_success_fallback" for row in second["board_scope_rows"]))
            self.assertIn("last-success", (output_dir / AVAILABLE_BOARD_STRATEGY_MD_LATEST).read_text(encoding="utf-8"))
            recovery = write_raw_refresh_recovery_bundle(output_dir)
            self.assertEqual(recovery["summary"]["effective_board_scope_source"], "last_success_fallback")
            self.assertTrue(recovery["summary"]["effective_board_scope_last_success_fallback_used"])
            self.assertEqual(recovery["summary"]["effective_board_scope_research_allowed_count"], 3)
            self.assertEqual(recovery["summary"]["effective_board_scope_unavailable_count"], 2)
            self.assertFalse(recovery["summary"]["live_discovery_ready"])
            atomic_write_json(
                output_dir / RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST,
                {
                    "schema_version": 1,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "refresh_id": "fallback-research-only",
                    "status": "partial_ready_research_only",
                    "full_publish_allowed": False,
                    "execution_allowed": False,
                    "current_executable_new_stake_aud": 0,
                    "required_target_count": 5,
                    "ready_required_target_count": 3,
                    "successful_board_count": 3,
                    "failed_board_count": 2,
                    "successful_boards": [
                        {"refresh_board_id": "matches", "board_id": "world_cup_matches", "name": "2026 World Cup Matches", "raw_snapshot": "matches.json"},
                        {"refresh_board_id": "futures", "board_id": "world_cup_futures", "name": "2026 World Cup Futures", "raw_snapshot": "futures.json"},
                        {"refresh_board_id": "group_betting", "board_id": "world_cup_group_betting", "name": "2026 World Cup Group Betting", "raw_snapshot": "group.json"},
                    ],
                    "failed_boards": [
                        {"refresh_board_id": "australia_markets", "board_id": "world_cup_australia_markets", "name": "2026 World Cup Australia Markets", "raw_snapshot": "australia.json"},
                        {"refresh_board_id": "team_futures_multi", "board_id": "world_cup_team_futures_multi", "name": "2026 World Cup Team Futures Multi", "raw_snapshot": "team_multi.json"},
                    ],
                },
            )
            partial = write_partial_daily_research_bundle(output_dir, report_date="13062026")
            self.assertEqual(partial["executive_status"]["status"], "ready_research_only")
            self.assertTrue(partial["executive_status"]["partial_daily_report_ready"])
            self.assertEqual(partial["summary"]["board_scope_source"], "last_success_fallback")
            self.assertTrue(partial["summary"]["board_scope_last_success_fallback_used"])
            self.assertEqual(partial["summary"]["research_allowed_board_count"], 3)
            self.assertEqual(partial["summary"]["current_executable_new_stake_aud"], 0)

    def test_access_denied_refresh_never_uses_headed_fallback_for_public_raw(self):
        self.assertTrue(looks_like_access_denied("2026 World Cup Matches returned Access Denied"))
        self.assertFalse(looks_like_access_denied("timeout waiting for selector"))
        previous = os.environ.get("TAB_FIFA_HEADLESS")
        try:
            os.environ.pop("TAB_FIFA_HEADLESS", None)
            self.assertFalse(should_try_headed_refresh_fallback())
            os.environ["TAB_FIFA_HEADLESS"] = "0"
            self.assertFalse(should_try_headed_refresh_fallback())
            os.environ["TAB_FIFA_HEADLESS"] = "false"
            self.assertFalse(should_try_headed_refresh_fallback())
            os.environ["TAB_FIFA_HEADLESS"] = "1"
            self.assertFalse(should_try_headed_refresh_fallback())
        finally:
            if previous is None:
                os.environ.pop("TAB_FIFA_HEADLESS", None)
            else:
                os.environ["TAB_FIFA_HEADLESS"] = previous

    def test_public_raw_refresh_ignores_requested_headed_fallback(self):
        import run_daily_report as daily

        captured_env = {}
        original_run = daily.subprocess.run

        def fake_run(command, cwd=None, text=None, capture_output=None, timeout=None, check=None, env=None):
            captured_env.update(env or {})
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps({"ok": True, "board": "matches"}),
                stderr="",
            )

        try:
            daily.subprocess.run = fake_run
            summary, last_error, diagnostic = daily.run_refresh_attempt(
                "matches",
                Path("/private/tmp/tab-fifa-refresh-unit"),
                "refresh-unit",
                1,
                headed_fallback=True,
                extra_env={"TAB_FIFA_HEADLESS": "0"},
            )
        finally:
            daily.subprocess.run = original_run

        self.assertEqual(captured_env["TAB_FIFA_HEADLESS"], "1")
        self.assertEqual(last_error, "")
        self.assertFalse(summary["headed_fallback"])
        self.assertTrue(summary["requested_headed_fallback"])
        self.assertTrue(summary["headed_fallback_ignored_by_access_policy"])
        self.assertFalse(diagnostic["headed_fallback"])
        self.assertTrue(diagnostic["requested_headed_fallback"])
        self.assertTrue(diagnostic["headed_fallback_ignored_by_access_policy"])

    def test_live_board_discovery_access_denied_blocks_ai_controlled_access(self):
        import run_daily_report as daily

        calls = []
        original_run = daily.subprocess.run
        original_out = daily.OUT
        original_node = daily.NODE_BIN
        previous_headless = os.environ.get("TAB_FIFA_HEADLESS")

        def fake_run(command, cwd=None, text=None, capture_output=None, check=None, timeout=None, env=None):
            headless = str((env or {}).get("TAB_FIFA_HEADLESS", ""))
            calls.append(headless)
            atomic_write_json(
                daily.OUT / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                {
                    "generated_at": "2026-06-12T00:00:00Z",
                    "source": "unit_fixture",
                    "page_markers": {"access_denied": True, "has_soccer": False, "link_count": 0},
                    "expected_boards": [],
                    "observed_world_cup_links": [],
                    "summary": {
                        "discovery_ready": False,
                        "quality_status": "blocked_access_denied",
                        "quality_issues": ["access_denied"],
                        "access_denied": True,
                    },
                },
            )
            return subprocess.CompletedProcess(command, 0, stdout='{"ok":true}', stderr="")

        try:
            with tempfile.TemporaryDirectory() as tmp:
                daily.OUT = Path(tmp)
                daily.NODE_BIN = Path(sys.executable)
                daily.subprocess.run = fake_run
                os.environ["TAB_FIFA_HEADLESS"] = "1"
                result = daily.run_live_board_discovery()
                raw = json.loads((Path(tmp) / LIVE_BOARD_DISCOVERY_RAW_LATEST).read_text(encoding="utf-8"))
        finally:
            daily.subprocess.run = original_run
            daily.OUT = original_out
            daily.NODE_BIN = original_node
            if previous_headless is None:
                os.environ.pop("TAB_FIFA_HEADLESS", None)
            else:
                os.environ["TAB_FIFA_HEADLESS"] = previous_headless

        self.assertEqual(calls, ["1"])
        self.assertFalse(result["headed_fallback"])
        self.assertTrue(result["access_denied"])
        self.assertEqual(result["quality_status"], "blocked_access_denied")
        self.assertEqual(result["access_policy_status"], "blocked_by_access_policy")
        self.assertEqual(result["blocker_code"], "ai_controlled_access_rejected")
        self.assertEqual(raw["access_policy"]["status"], "blocked_by_access_policy")
        self.assertIn("ai_controlled_access_rejected", raw["summary"]["quality_issues"])

    def test_pre_raw_live_board_discovery_failure_refuses_stale_match_targets(self):
        import run_daily_report as daily

        original_out = daily.OUT
        original_run_live = daily.run_live_board_discovery
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                daily.OUT = root

                def fail_discovery():
                    raise RuntimeError("/Users/linzezhang/private stale discovery failed")

                daily.run_live_board_discovery = fail_discovery
                with self.assertRaises(RuntimeError) as ctx:
                    daily.write_live_board_discovery_before_raw_refresh()
                raw = json.loads((root / LIVE_BOARD_DISCOVERY_RAW_LATEST).read_text(encoding="utf-8"))
        finally:
            daily.OUT = original_out
            daily.run_live_board_discovery = original_run_live

        self.assertIn("refusing to use stale TAB match targets", str(ctx.exception))
        self.assertEqual(raw["status"], "failed")
        self.assertEqual(raw["stage"], "pre_raw_refresh")
        self.assertNotIn("/Users/", json.dumps(raw, ensure_ascii=False))
        self.assertIn("不能沿用旧 match targets", raw["truthfulness_note"])

    def test_raw_refresh_continues_after_single_board_failure_then_fails_closed(self):
        import run_daily_report as daily

        calls = []
        original_out = daily.OUT
        original_diag_latest = daily.RAW_REFRESH_DIAGNOSTICS_PATH
        original_boards = daily.RAW_REFRESH_BOARDS
        original_refresh_board = daily.refresh_board_to_staging
        original_safety = daily.audit_output_safety
        original_staged_gate = daily.audit_staged_raw_refresh
        original_private_dir = daily.PRIVATE_DATA_DIR

        def fake_refresh_board_to_staging(board_id, staging, attempts=1, refresh_id=None, run_id=None, diagnostics=None):
            calls.append(board_id)
            if board_id == "australia_markets":
                if diagnostics is not None:
                    diagnostics.setdefault("attempts", []).append(
                        {
                            "board_id": board_id,
                            "attempt": 1,
                            "exit_code": 1,
                            "access_denied": False,
                            "error": "2026 World Cup Australia Markets route mismatch: landed on 2026 World Cup Matches",
                        }
                    )
                raise RuntimeError(
                    "australia_markets refresh failed after 1 attempt(s): "
                    "2026 World Cup Australia Markets route mismatch"
                )
            output_name = {
                "matches": "matches.json",
                "team_futures_multi": "team_futures_multi.json",
            }[board_id]
            output_path = Path(staging) / output_name
            atomic_write_json(
                output_path,
                {
                    "generated_at": "2026-06-12T00:00:00Z",
                    "refresh_id": refresh_id,
                    "source": "unit_fixture",
                },
            )
            if diagnostics is not None:
                diagnostics.setdefault("attempts", []).append(
                    {
                        "board_id": board_id,
                        "attempt": 1,
                        "exit_code": 0,
                        "access_denied": False,
                    }
                )
            return {
                "generated_at": "2026-06-12T00:00:00Z",
                "refresh_id": refresh_id,
                "results": [
                    {
                        "board_id": board_id,
                        "output": str(output_path),
                        "text_length": 1000,
                        "match_count": 0,
                        "market_count": 1,
                        "error_count": 0,
                        "link_count": 0,
                    }
                ],
            }

        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                daily.OUT = root
                daily.PRIVATE_DATA_DIR = root / "private"
                daily.RAW_REFRESH_DIAGNOSTICS_PATH = root / "raw_refresh_diagnostics_latest.json"
                daily.RAW_REFRESH_BOARDS = [
                    ("matches", root / "matches.json"),
                    ("australia_markets", root / "australia.json"),
                    ("team_futures_multi", root / "team_futures_multi.json"),
                ]
                daily.refresh_board_to_staging = fake_refresh_board_to_staging
                daily.audit_output_safety = lambda _staging: {"automation_safety_ready": True, "blocking_reasons": []}
                daily.audit_staged_raw_refresh = lambda _staging, expected_refresh_id=None: {
                    "staged_raw_ready": False,
                    "ready_required_target_count": 2,
                    "required_target_count": 3,
                    "blocking_reasons": ["2026 World Cup Australia Markets staged raw snapshot is missing."],
                    "targets": [
                        {
                            "board_id": "matches",
                            "name": "2026 World Cup Matches",
                            "raw_snapshot": "matches.json",
                            "raw_exists": True,
                            "raw_timestamp": "2026-06-12T00:00:00Z",
                            "refresh_id": expected_refresh_id,
                            "sha256": "sha-matches",
                            "raw_fresh": True,
                            "raw_valid": True,
                            "refresh_ready": True,
                        },
                        {
                            "board_id": "australia_markets",
                            "name": "2026 World Cup Australia Markets",
                            "raw_snapshot": "australia.json",
                            "raw_exists": False,
                            "raw_timestamp": "",
                            "refresh_id": "",
                            "sha256": None,
                            "raw_fresh": False,
                            "raw_valid": False,
                            "refresh_ready": False,
                            "raw_validation_errors": ["missing"],
                        },
                        {
                            "board_id": "team_futures_multi",
                            "name": "2026 World Cup Team Futures Multi",
                            "raw_snapshot": "team_futures_multi.json",
                            "raw_exists": True,
                            "raw_timestamp": "2026-06-12T00:00:00Z",
                            "refresh_id": expected_refresh_id,
                            "sha256": "sha-team",
                            "raw_fresh": True,
                            "raw_valid": True,
                            "refresh_ready": True,
                        },
                    ],
                }
                with self.assertRaises(RuntimeError) as ctx:
                    daily.refresh_raw_snapshots("run-continue-after-failure")
                diagnostics = json.loads(daily.RAW_REFRESH_DIAGNOSTICS_PATH.read_text(encoding="utf-8"))
                research_manifest_path = root / RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST
                research_manifest = json.loads(research_manifest_path.read_text(encoding="utf-8"))
                copied_raw_paths = sorted((root / "research_only_raw").glob("*.json"))
                canonical_raw_exists = (root / "matches.json").exists() or (root / "team_futures_multi.json").exists()
                batch_manifest_exists = (root / "raw_refresh_batch_latest.json").exists()
                public_safety = audit_public_artifact_safety([research_manifest_path, *copied_raw_paths])
        finally:
            daily.OUT = original_out
            daily.RAW_REFRESH_DIAGNOSTICS_PATH = original_diag_latest
            daily.RAW_REFRESH_BOARDS = original_boards
            daily.refresh_board_to_staging = original_refresh_board
            daily.audit_output_safety = original_safety
            daily.audit_staged_raw_refresh = original_staged_gate
            daily.PRIVATE_DATA_DIR = original_private_dir

        self.assertEqual(calls, ["matches", "australia_markets", "team_futures_multi"])
        self.assertIn("board refresh failures", str(ctx.exception))
        self.assertEqual(diagnostics["status"], "failed")
        self.assertTrue(diagnostics["continued_after_board_failure"])
        self.assertTrue(diagnostics["staged_batch_manifest_skipped"])
        self.assertEqual(diagnostics["failed_board_ids"], ["australia_markets"])
        self.assertEqual(diagnostics["board_failure_count"], 1)
        self.assertEqual(diagnostics["ready_required_target_count"], 2)
        self.assertEqual(diagnostics["required_target_count"], 3)
        self.assertEqual(diagnostics["research_only_staged_raw_status"], "partial_ready_research_only")
        self.assertEqual(diagnostics["research_only_successful_board_count"], 2)
        self.assertFalse(diagnostics["research_only_execution_allowed"])
        self.assertEqual(diagnostics["research_only_current_executable_new_stake_aud"], 0)
        self.assertEqual(research_manifest["status"], "partial_ready_research_only")
        self.assertFalse(research_manifest["official_raw_promoted"])
        self.assertFalse(research_manifest["execution_allowed"])
        self.assertEqual(research_manifest["current_executable_new_stake_aud"], 0)
        self.assertEqual(research_manifest["successful_board_count"], 2)
        self.assertEqual(research_manifest["failed_board_count"], 1)
        self.assertEqual(len(copied_raw_paths), 2)
        self.assertFalse(canonical_raw_exists)
        self.assertFalse(batch_manifest_exists)
        self.assertTrue(public_safety["public_artifact_safety_ready"], public_safety)
        self.assertEqual([item["board_id"] for item in diagnostics["attempts"]], ["matches", "australia_markets", "team_futures_multi"])

    def test_research_only_staged_raw_manifest_keeps_valid_timeout_as_warning(self):
        import run_daily_report as daily

        original_out = daily.OUT
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                staging = root / "staging"
                staging.mkdir()
                daily.OUT = root
                atomic_write_json(
                    staging / "futures.json",
                    {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "refresh_id": "refresh-warning",
                        "source": "unit_fixture",
                    },
                )
                payload = daily.write_research_only_staged_raw_manifest(
                    staging,
                    refresh_id="refresh-warning",
                    diagnostics={
                        "board_failures": [
                            {
                                "board_id": "futures",
                                "error": "futures refresh failed after 1 attempt(s): refresh command timed out after 180 seconds",
                            }
                        ]
                    },
                    staged_raw_gate={
                        "staged_raw_ready": False,
                        "required_target_count": 1,
                        "ready_required_target_count": 1,
                        "targets": [
                            {
                                "board_id": "futures",
                                "name": "2026 World Cup Futures",
                                "raw_snapshot": "futures.json",
                                "raw_timestamp": datetime.now(timezone.utc).isoformat(),
                                "refresh_id": "refresh-warning",
                                "sha256": "sha-futures",
                                "raw_exists": True,
                                "raw_fresh": True,
                                "raw_valid": True,
                                "refresh_ready": True,
                            }
                        ],
                        "blocking_reasons": ["other required boards are missing"],
                    },
                    staged_safety={"automation_safety_ready": True},
                )
                manifest_path = root / "raw_refresh_research_only_latest.json"
                copied_raw_paths = sorted((root / "research_only_raw").glob("*.json"))
                public_safety = audit_public_artifact_safety([manifest_path, *copied_raw_paths])
        finally:
            daily.OUT = original_out

        self.assertEqual(payload["status"], "partial_ready_research_only")
        self.assertEqual(payload["successful_board_count"], 1)
        self.assertEqual(payload["failed_board_count"], 0)
        self.assertEqual(payload["attempt_warning_count"], 1)
        self.assertEqual(payload["attempt_warnings"][0]["refresh_board_id"], "futures")
        self.assertEqual(len(copied_raw_paths), 1)
        self.assertTrue(public_safety["public_artifact_safety_ready"], public_safety)

    def test_raw_refresh_interruption_writes_failed_diagnostic(self):
        import run_daily_report as daily

        original_out = daily.OUT
        original_diag_latest = daily.RAW_REFRESH_DIAGNOSTICS_PATH
        original_boards = daily.RAW_REFRESH_BOARDS
        original_refresh_board = daily.refresh_board_to_staging

        def interrupted_refresh_board_to_staging(*_args, **_kwargs):
            raise KeyboardInterrupt("/Users/linzezhang/private/chrome-profile")

        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                daily.OUT = root
                daily.RAW_REFRESH_DIAGNOSTICS_PATH = root / "raw_refresh_diagnostics_latest.json"
                daily.RAW_REFRESH_BOARDS = [("matches", root / "matches.json")]
                daily.refresh_board_to_staging = interrupted_refresh_board_to_staging
                with self.assertRaises(KeyboardInterrupt):
                    daily.refresh_raw_snapshots("run-interrupted")
                latest = json.loads(daily.RAW_REFRESH_DIAGNOSTICS_PATH.read_text(encoding="utf-8"))
                run_specific = json.loads((root / "raw_refresh_diagnostics_run-interrupted.json").read_text(encoding="utf-8"))
        finally:
            daily.OUT = original_out
            daily.RAW_REFRESH_DIAGNOSTICS_PATH = original_diag_latest
            daily.RAW_REFRESH_BOARDS = original_boards
            daily.refresh_board_to_staging = original_refresh_board

        self.assertEqual(latest["status"], "interrupted")
        self.assertEqual(run_specific["status"], "interrupted")
        self.assertIn("raw refresh interrupted", latest["error"])
        self.assertIn("interrupted_at", latest)
        serialized = json.dumps(latest, ensure_ascii=False)
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn("chrome-profile", serialized)

    def test_matches_chunk_access_denied_blocks_ai_controlled_access(self):
        import run_daily_report as daily

        calls = []
        original_run_refresh_attempt = daily.run_refresh_attempt
        original_expected_matches = daily.EXPECTED_MATCHES
        original_out = daily.OUT
        original_heartbeat = daily.heartbeat_raw_refresh_diagnostics
        previous_headless = os.environ.get("TAB_FIFA_HEADLESS")

        def fake_run_refresh_attempt(board_id, staging, refresh_id, attempt, headed_fallback=False, extra_args=None, extra_env=None):
            calls.append(
                {
                    "board_id": board_id,
                    "attempt": attempt,
                    "headed_fallback": headed_fallback,
                    "extra_args": list(extra_args or []),
                    "extra_env": dict(extra_env or {}),
                }
            )
            diagnostic = {
                "board_id": board_id,
                "attempt": attempt,
                "headed_fallback": headed_fallback,
                "exit_code": 1,
                "access_denied": True,
                "ai_controlled_access_rejected": True,
                "access_policy_status": "blocked_by_access_policy",
                "stderr_tail": "Access Denied",
                "stdout_tail": "",
            }
            diagnostic["error"] = "Access Denied"
            return None, "Access Denied", diagnostic

        try:
            os.environ.pop("TAB_FIFA_HEADLESS", None)
            daily.run_refresh_attempt = fake_run_refresh_attempt
            daily.EXPECTED_MATCHES = ["Mexico v South Africa"]
            daily.heartbeat_raw_refresh_diagnostics = lambda _run_id, _diagnostics: Path("/tmp/raw_refresh_diagnostics_test.json")
            with tempfile.TemporaryDirectory() as tmp:
                daily.OUT = Path(tmp)
                diagnostics = {
                    "schema_version": 1,
                    "run_id": "run-headed",
                    "generated_at": "2026-06-12T00:00:00Z",
                    "refresh_id": "refresh-headed",
                    "status": "running",
                    "attempts": [],
                    "results": [],
                }
                with self.assertRaises(RuntimeError) as ctx:
                    daily.refresh_matches_board_to_staging(
                        Path(tmp),
                        attempts=2,
                        refresh_id="refresh-headed",
                        run_id="run-headed",
                        diagnostics=diagnostics,
                    )
        finally:
            daily.run_refresh_attempt = original_run_refresh_attempt
            daily.EXPECTED_MATCHES = original_expected_matches
            daily.OUT = original_out
            daily.heartbeat_raw_refresh_diagnostics = original_heartbeat
            if previous_headless is None:
                os.environ.pop("TAB_FIFA_HEADLESS", None)
            else:
                os.environ["TAB_FIFA_HEADLESS"] = previous_headless

        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0]["headed_fallback"])
        self.assertIn("--offset", calls[0]["extra_args"])
        self.assertIn("ai_controlled_access_rejected", str(ctx.exception))
        self.assertEqual(len(diagnostics["attempts"]), 1)
        self.assertFalse(diagnostics["attempts"][-1]["headed_fallback"])
        self.assertTrue(diagnostics["attempts"][-1]["access_denied"])
        self.assertTrue(diagnostics["attempts"][-1]["ai_controlled_access_rejected"])
        self.assertEqual(diagnostics["access_policy_status"], "blocked_by_access_policy")
        self.assertEqual(diagnostics["access_policy_blocker_code"], "ai_controlled_access_rejected")

    def test_matches_refresh_uses_live_discovery_match_targets(self):
        import run_daily_report as daily

        calls = []
        original_run_refresh_attempt = daily.run_refresh_attempt
        original_out = daily.OUT
        original_expected_matches = daily.EXPECTED_MATCHES
        original_heartbeat = daily.heartbeat_raw_refresh_diagnostics

        def fake_run_refresh_attempt(board_id, staging, refresh_id, attempt, headed_fallback=False, extra_args=None, extra_env=None):
            calls.append(
                {
                    "board_id": board_id,
                    "attempt": attempt,
                    "headed_fallback": headed_fallback,
                    "extra_args": list(extra_args or []),
                    "extra_env": dict(extra_env or {}),
                }
            )
            targets = json.loads((extra_env or {}).get("TAB_FIFA_MATCH_TARGETS_JSON", "[]"))
            offset = int((extra_args or [])[((extra_args or []).index("--offset") + 1)] if "--offset" in (extra_args or []) else 0)
            limit = int((extra_args or [])[((extra_args or []).index("--limit") + 1)] if "--limit" in (extra_args or []) else len(targets))
            chunk_targets = targets[offset:offset + limit]
            output_path = Path(staging) / daily.MATCHES_BOARD.raw_snapshot
            atomic_write_json(
                output_path,
                {
                    "generated_at": "2026-06-12T00:00:00Z",
                    "source": "unit_fixture",
                    "refresh_id": refresh_id,
                    "target_source": "live_board_discovery",
                    "available_match_count": len(targets),
                    "matches": [full_match_fixture(item["match"]) | {"href": item["href"]} for item in chunk_targets],
                },
            )
            return (
                {
                    "generated_at": "2026-06-12T00:00:00Z",
                    "refresh_id": refresh_id,
                    "dry_run": False,
                    "smoke": True,
                    "headless": False,
                    "boards": [{"board_id": "matches", "board": daily.MATCHES_BOARD.name, "output": str(output_path)}],
                    "results": [
                        {
                            "board_id": "matches",
                            "output": str(output_path),
                            "text_length": 0,
                            "match_count": len(chunk_targets),
                            "market_count": 6 * len(chunk_targets),
                            "error_count": 0,
                            "link_count": 0,
                        }
                    ],
                },
                "",
                {"board_id": board_id, "attempt": attempt, "exit_code": 0, "access_denied": False},
            )

        try:
            with tempfile.TemporaryDirectory() as tmp:
                daily.OUT = Path(tmp)
                atomic_write_json(
                    daily.OUT / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                    {
                        "expected_boards": [
                            {
                                "refresh_board_id": "matches",
                                "matched_links": [
                                    {
                                        "text": "Soccer",
                                        "href": "https://www.tab.com.au/sports/results/Soccer/competitions/2026%20World%20Cup%20Matches",
                                    },
                                    {
                                        "text": "Canada v Bosn-Herzegovina",
                                        "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/Canada%20v%20Bosn-Herzegovina",
                                    },
                                    {
                                        "text": "324 Markets",
                                        "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/Canada%20v%20Bosn-Herzegovina",
                                    },
                                    {
                                        "text": "USA v Paraguay",
                                        "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/USA%20v%20Paraguay",
                                    },
                                ],
                            }
                        ]
                    },
                )
                daily.run_refresh_attempt = fake_run_refresh_attempt
                daily.EXPECTED_MATCHES = ["Mexico v South Africa", "South Korea v Czechia", "Canada v Bosn-Herzegovina"]
                daily.heartbeat_raw_refresh_diagnostics = lambda _run_id, _diagnostics: Path("/tmp/raw_refresh_diagnostics_test.json")
                summary = daily.refresh_matches_board_to_staging(
                    Path(tmp),
                    attempts=1,
                    refresh_id="refresh-live-targets",
                    run_id="run-live-targets",
                    diagnostics={"schema_version": 1, "attempts": [], "results": []},
                )
        finally:
            daily.run_refresh_attempt = original_run_refresh_attempt
            daily.OUT = original_out
            daily.EXPECTED_MATCHES = original_expected_matches
            daily.heartbeat_raw_refresh_diagnostics = original_heartbeat

        self.assertEqual(summary["target_source"], "live_board_discovery")
        self.assertEqual(summary["available_match_count"], 2)
        self.assertEqual(summary["results"][0]["match_count"], 2)
        self.assertTrue(calls)
        sent_targets = json.loads(calls[0]["extra_env"]["TAB_FIFA_MATCH_TARGETS_JSON"])
        self.assertEqual([item["match"] for item in sent_targets], ["Canada v Bosn-Herzegovina", "USA v Paraguay"])
        self.assertNotIn("Mexico v South Africa", json.dumps(sent_targets))

    def test_matches_refresh_repairs_partial_core_after_chunk_merge(self):
        import run_daily_report as daily

        calls = []
        original_run_refresh_attempt = daily.run_refresh_attempt
        original_out = daily.OUT
        original_expected_matches = daily.EXPECTED_MATCHES
        original_heartbeat = daily.heartbeat_raw_refresh_diagnostics

        def partial_match_fixture(match_name):
            return {
                "match": match_name,
                "markets": {"Result": "Result\nUSA\n2.00\nDraw\n3.10\nParaguay\n3.50\n"},
                "errors": [],
            }

        def fake_run_refresh_attempt(board_id, staging, refresh_id, attempt, headed_fallback=False, extra_args=None, extra_env=None):
            calls.append(
                {
                    "board_id": board_id,
                    "attempt": attempt,
                    "headed_fallback": headed_fallback,
                    "extra_args": list(extra_args or []),
                    "extra_env": dict(extra_env or {}),
                }
            )
            targets = json.loads((extra_env or {}).get("TAB_FIFA_MATCH_TARGETS_JSON", "[]"))
            output_path = Path(staging) / daily.MATCHES_BOARD.raw_snapshot
            if "--match" in (extra_args or []):
                match_name = (extra_args or [])[((extra_args or []).index("--match") + 1)]
                rows = [full_match_fixture(match_name)]
            else:
                rows = [
                    full_match_fixture(targets[0]["match"]),
                    partial_match_fixture(targets[1]["match"]),
                ]
            atomic_write_json(
                output_path,
                {
                    "generated_at": "2026-06-12T00:00:00Z",
                    "source": "unit_fixture",
                    "refresh_id": refresh_id,
                    "target_source": "live_board_discovery",
                    "available_match_count": len(targets),
                    "target_matches": [item["match"] for item in targets],
                    "matches": rows,
                },
            )
            return (
                {
                    "generated_at": "2026-06-12T00:00:00Z",
                    "refresh_id": refresh_id,
                    "dry_run": False,
                    "smoke": "--match" not in (extra_args or []),
                    "headless": False,
                    "boards": [{"board_id": "matches", "board": daily.MATCHES_BOARD.name, "output": str(output_path)}],
                    "results": [
                        {
                            "board_id": "matches",
                            "output": str(output_path),
                            "text_length": 0,
                            "match_count": len(rows),
                            "market_count": sum(len(row.get("markets", {})) for row in rows),
                            "error_count": 0,
                            "link_count": 0,
                        }
                    ],
                },
                "",
                {"board_id": board_id, "attempt": attempt, "exit_code": 0, "access_denied": False},
            )

        try:
            with tempfile.TemporaryDirectory() as tmp:
                daily.OUT = Path(tmp)
                atomic_write_json(
                    daily.OUT / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                    {
                        "expected_boards": [
                            {
                                "refresh_board_id": "matches",
                                "matched_links": [
                                    {
                                        "text": "USA v Paraguay",
                                        "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/USA%20v%20Paraguay",
                                    },
                                    {
                                        "text": "Qatar v Switzerland",
                                        "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/Qatar%20v%20Switzerland",
                                    },
                                ],
                            }
                        ]
                    },
                )
                daily.run_refresh_attempt = fake_run_refresh_attempt
                daily.EXPECTED_MATCHES = ["USA v Paraguay", "Qatar v Switzerland"]
                daily.heartbeat_raw_refresh_diagnostics = lambda _run_id, _diagnostics: Path("/tmp/raw_refresh_diagnostics_test.json")
                diagnostics = {"schema_version": 1, "attempts": [], "results": []}
                summary = daily.refresh_matches_board_to_staging(
                    Path(tmp),
                    attempts=1,
                    refresh_id="refresh-repair",
                    run_id="run-repair",
                    diagnostics=diagnostics,
                )
                raw = json.loads((Path(tmp) / daily.MATCHES_BOARD.raw_snapshot).read_text(encoding="utf-8"))
        finally:
            daily.run_refresh_attempt = original_run_refresh_attempt
            daily.OUT = original_out
            daily.EXPECTED_MATCHES = original_expected_matches
            daily.heartbeat_raw_refresh_diagnostics = original_heartbeat

        self.assertEqual(summary["merged_repair_attempt_count"], 1)
        self.assertEqual(summary["merged_repair_success_count"], 1)
        self.assertEqual(len(calls), 2)
        self.assertIn("--match", calls[-1]["extra_args"])
        self.assertEqual(calls[-1]["extra_args"][calls[-1]["extra_args"].index("--match") + 1], "Qatar v Switzerland")
        self.assertTrue(diagnostics["attempts"][-1]["repair_success"])
        repaired = {row["match"]: row for row in raw["matches"]}
        self.assertTrue(has_full_core_markets(repaired["Qatar v Switzerland"]))

    def test_matches_repair_targets_skip_in_play_matches(self):
        import run_daily_report as daily

        in_play = full_match_fixture("USA v Paraguay")
        in_play["text"] = "USA v Paraguay\nIn-Play|Bet by phone for suspended markets."
        in_play["markets"]["Both Teams to Score"] = "Both Teams to Score\nUSA v Paraguay\nIn-Play|Bet by phone\n"
        partial_pre_match = {
            "match": "Qatar v Switzerland",
            "markets": {"Result": "Result\nQatar\n2.00\nDraw\n3.10\nSwitzerland\n3.50\n"},
            "errors": [],
        }

        targets = daily.merged_match_repair_targets(
            [in_play, partial_pre_match],
            ["USA v Paraguay", "Qatar v Switzerland"],
        )

        self.assertEqual(targets, [{"match": "Qatar v Switzerland", "reason": "partial_core_markets"}])

    def test_live_discovery_board_href_rejects_match_detail_url(self):
        import run_daily_report as daily

        original_out = daily.OUT
        try:
            with tempfile.TemporaryDirectory() as tmp:
                daily.OUT = Path(tmp)
                atomic_write_json(
                    daily.OUT / LIVE_BOARD_DISCOVERY_RAW_LATEST,
                    {
                        "expected_boards": [
                            {
                                "refresh_board_id": "matches",
                                "matched_links": [
                                    {
                                        "text": "Canada v Bosn-Herzegovina",
                                        "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/Canada%20v%20Bosn-Herzegovina",
                                    }
                                ],
                            }
                        ]
                    },
                )
                self.assertEqual(daily.live_discovery_href_for_board("matches"), "")
                self.assertEqual(len(daily.live_discovery_match_targets()), 1)
        finally:
            daily.OUT = original_out

    def test_raw_refresh_diagnostics_are_public_safe(self):
        summary = public_refresh_summary(
            {
                "generated_at": "2026-06-04T00:00:00Z",
                "refresh_id": "batch-1",
                "dry_run": False,
                "smoke": False,
                "headless": False,
                "output_dir": "/private/tmp/tab-fifa-refresh-secret",
                "boards": [
                    {
                        "board_id": "matches",
                        "board": "2026 World Cup Matches",
                        "output": "/Users/linzezhang/Documents/Codex/secret/tab_fifa_matches_main_markets_raw_v0_9.json",
                    }
                ],
                "results": [
                    {
                        "board_id": "matches",
                        "output": "/private/tmp/tab_fifa_matches_main_markets_raw_v0_9.json",
                        "text_length": 0,
                        "match_count": 26,
                        "market_count": 156,
                        "error_count": 0,
                        "link_count": 26,
                    }
                ],
            }
        )
        serialized = json.dumps(summary, ensure_ascii=False)
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn("/private/tmp", serialized)
        self.assertEqual(summary["boards"][0]["output"], "tab_fifa_matches_main_markets_raw_v0_9.json")
        self.assertEqual(summary["results"][0]["match_count"], 26)
        tail = public_tail("Access Denied at /Users/linzezhang/private/path/output.json")
        self.assertNotIn("/Users/", tail)
        self.assertIn("Access Denied", tail)

    def test_raw_refresh_attempt_timeout_returns_public_safe_diagnostic(self):
        import run_daily_report as daily

        original_run = daily.subprocess.run

        def fake_timeout_run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(
                cmd=["node", "refresh_tab_readonly.mjs"],
                timeout=12,
                output=b"stdout path /Users/linzezhang/private/raw.json",
                stderr=b"Access Denied at /private/tmp/tab-fifa-refresh-secret/output.json",
            )

        try:
            daily.subprocess.run = fake_timeout_run
            summary, last_error, diagnostic = daily.run_refresh_attempt(
                "matches",
                Path("/private/tmp/tab-fifa-refresh-secret"),
                "refresh-timeout",
                1,
                headed_fallback=False,
            )
        finally:
            daily.subprocess.run = original_run

        self.assertIsNone(summary)
        self.assertEqual(last_error, "refresh command timed out after 12 seconds")
        self.assertTrue(diagnostic["timeout"])
        self.assertEqual(diagnostic["exit_code"], "timeout")
        self.assertEqual(diagnostic["timeout_seconds"], 12)
        self.assertTrue(diagnostic["access_denied"])
        self.assertTrue(diagnostic["ai_controlled_access_rejected"])
        self.assertEqual(diagnostic["access_policy_status"], "blocked_by_access_policy")
        self.assertEqual(diagnostic["blocker_code"], "ai_controlled_access_rejected")
        serialized = json.dumps(diagnostic, ensure_ascii=False)
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn("/private/tmp", serialized)
        self.assertIn("Access Denied", serialized)

    def test_matches_chunk_quality_errors_rejects_partial_core_and_expansion_errors(self):
        raw = {
            "matches": [
                full_match_fixture("Mexico v South Africa"),
                {
                    "match": "South Korea v Czechia",
                    "markets": {"Result": "Result\nSouth Korea\n2.00\nDraw\n3.10\nCzechia\n3.50\n"},
                    "errors": ["Market header expansion failed for Handicap"],
                },
            ]
        }
        errors = matches_chunk_quality_errors(raw)
        self.assertTrue(any("South Korea v Czechia" in error for error in errors))
        self.assertTrue(any("market expansion errors" in error for error in errors))
        tolerated_partial = {
            "matches": [
                full_match_fixture("Mexico v South Africa"),
                {
                    "match": "USA v Australia",
                    "markets": {"Result": "Result\nUSA\n2.00\nDraw\n3.10\nAustralia\n3.50\n"},
                    "errors": [],
                },
            ]
        }
        self.assertEqual(matches_chunk_quality_errors(tolerated_partial), [])
        tolerated_multiple_partial = {
            "matches": [
                full_match_fixture("Mexico v South Africa"),
                {
                    "match": "Ghana v Panama",
                    "markets": {"Result": "Result\nGhana\n2.00\nDraw\n3.10\nPanama\n3.50\n"},
                    "errors": [],
                },
                {
                    "match": "USA v Australia",
                    "markets": {"Result": "Result\nUSA\n2.00\nDraw\n3.10\nAustralia\n3.50\n"},
                    "errors": [],
                },
            ]
        }
        self.assertEqual(matches_chunk_quality_errors(tolerated_multiple_partial), [])
        all_partial = {
            "matches": [
                {
                    "match": "Ghana v Panama",
                    "markets": {"Result": "Result\nGhana\n2.00\nDraw\n3.10\nPanama\n3.50\n"},
                    "errors": [],
                },
                {
                    "match": "USA v Australia",
                    "markets": {"Result": "Result\nUSA\n2.00\nDraw\n3.10\nAustralia\n3.50\n"},
                    "errors": [],
                },
            ]
        }
        self.assertEqual(matches_chunk_quality_errors(all_partial), [])
        self.assertEqual(matches_chunk_quality_errors({"matches": [full_match_fixture("Mexico v South Africa")]}), [])

    def test_raw_refresh_diagnostics_heartbeat_writes_each_attempt(self):
        import run_daily_report as daily

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            originals = {
                "OUT": daily.OUT,
                "RAW_REFRESH_DIAGNOSTICS_PATH": daily.RAW_REFRESH_DIAGNOSTICS_PATH,
            }
            try:
                daily.OUT = output_dir
                daily.RAW_REFRESH_DIAGNOSTICS_PATH = output_dir / "raw_refresh_diagnostics_latest.json"
                diagnostics = {
                    "schema_version": 1,
                    "run_id": "run-heartbeat",
                    "generated_at": "2026-06-04T00:00:00Z",
                    "refresh_id": "refresh-heartbeat",
                    "status": "running",
                    "attempts": [],
                    "results": [],
                }
                run_path = daily.heartbeat_raw_refresh_diagnostics("run-heartbeat", diagnostics)
                self.assertTrue(run_path.exists())
                self.assertTrue((output_dir / "raw_refresh_diagnostics_latest.json").exists())
                initial = json.loads(run_path.read_text(encoding="utf-8"))
                self.assertEqual(initial["heartbeat_count"], 0)

                daily.record_refresh_attempt(
                    "run-heartbeat",
                    diagnostics,
                    {
                        "board_id": "matches",
                        "attempt": 1,
                        "headed_fallback": False,
                        "exit_code": 1,
                        "access_denied": True,
                        "stderr_tail": "Access Denied at /Users/linzezhang/private/raw.json",
                    },
                )
                payload = json.loads(run_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["heartbeat_count"], 1)
                self.assertEqual(payload["last_attempt"]["board_id"], "matches")
                self.assertTrue(payload["last_attempt"]["access_denied"])
                serialized = json.dumps(payload, ensure_ascii=False)
                self.assertNotIn("/Users/", serialized)
                self.assertTrue(audit_public_artifact_safety([run_path, daily.RAW_REFRESH_DIAGNOSTICS_PATH])["public_artifact_safety_ready"])

                reused_path = daily.write_reused_raw_refresh_diagnostics(
                    "run-reused",
                    {"raw_refresh_ready": True, "ready_required_target_count": 5, "required_target_count": 5, "targets": []},
                )
                reused = json.loads(reused_path.read_text(encoding="utf-8"))
                self.assertEqual(reused["status"], "reused_fresh_validated_raw")
                self.assertEqual(reused["heartbeat_count"], 0)

                disabled_path = daily.write_disabled_raw_refresh_diagnostics("run-disabled")
                disabled = json.loads(disabled_path.read_text(encoding="utf-8"))
                self.assertEqual(disabled["status"], "raw_refresh_disabled")
                self.assertEqual(disabled["heartbeat_count"], 0)
            finally:
                for name, value in originals.items():
                    setattr(daily, name, value)

    def test_raw_refresh_gate_requires_refresh_id_batch_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "outputs"
            driver = root / "work" / "tab-research-pipeline" / "scripts" / "refresh_tab_readonly.mjs"
            output_dir.mkdir()
            driver.parent.mkdir(parents=True)
            driver.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            boards = [
                BoardConfig(
                    board_id=f"test_board_{idx}",
                    refresh_board_id=f"test_{idx}",
                    name=f"Test Board {idx}",
                    tab_path=f"/sports/test/{idx}",
                    priority=idx,
                    version="test",
                    required_for_full_automation=True,
                    parser_strategy="fixture",
                    refresh_method="fixture",
                    raw_snapshot=f"test_raw_{idx}.json",
                    recommendations_artifact=None,
                    gate_artifact=None,
                    report_artifact=None,
                )
                for idx in range(1, 3)
            ]
            for board in boards:
                atomic_write_json(output_dir / board.raw_snapshot, {"generated_at": "2026-06-03T00:00:00Z"})
            manifest = audit_raw_refresh(output_dir, boards=boards, now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc))
            self.assertFalse(manifest["raw_refresh_ready"])
            self.assertFalse(manifest["refresh_batch_ready"])
            self.assertTrue(any("missing a required refresh_id" in reason for reason in manifest["blocking_reasons"]))

    def test_daily_automation_runner_contract(self):
        script = ROOT / "scripts" / "run_tab_fifa_daily_automation.sh"
        text = script.read_text(encoding="utf-8")
        self.assertTrue(script.exists())
        self.assertIn("--verify-only", text)
        self.assertIn("automation_run_latest.json", text)
        self.assertIn("automation_readiness_latest.json", text)
        self.assertIn("automation_readiness_latest.md", text)
        self.assertIn("automation_readiness_latest.pdf", text)
        self.assertIn("automation_candidate_latest.json", text)
        self.assertIn("automation_candidate_latest.md", text)
        self.assertIn("automation_candidate_latest.pdf", text)
        self.assertIn("write_automation_readiness_summary", text)
        self.assertIn("write_automation_readiness_report", text)
        self.assertIn("write_automation_readiness_pdf", text)
        self.assertIn("store_automation_run", text)
        self.assertIn("automation_run_store", text)
        self.assertIn("write_automation_candidate", text)
        self.assertIn("write_automation_candidate_report", text)
        self.assertIn("write_automation_candidate_pdf", text)
        self.assertIn("does not create a recurring", text)
        self.assertIn("place bets", text)
        self.assertIn("add selections to Bet Slip", text)
        self.assertIn("TAB_FIFA_OUTPUT_DIR", text)
        self.assertIn("TAB_FIFA_LOG_DIR", text)
        self.assertIn("TAB_FIFA_RUNNER_LOCK_DIR", text)
        self.assertIn("acquire_runner_lock", text)
        self.assertIn("release_runner_lock", text)
        self.assertIn("another TAB FIFA automation runner is active", text)
        self.assertIn("exit 75", text)
        self.assertIn("trap release_runner_lock EXIT INT TERM", text)
        self.assertIn("--capture-my-bets", text)
        self.assertIn("TAB_FIFA_CAPTURE_MY_BETS", text)
        self.assertIn('VERIFY_MODE="${TAB_FIFA_VERIFY_MODE:-hermetic}"', text)
        self.assertIn('"--${VERIFY_MODE}"', text)
        self.assertIn("TAB_FIFA_RUN_VERIFY_MODE", text)
        self.assertIn("TAB_FIFA_MY_BETS_WAIT_FOR_LOGIN_MS", text)
        self.assertIn("report date must use DDMMYYYY format", text)
        self.assertIn("must be a non-negative integer", text)
        self.assertIn("capture_tab_my_bets_readonly.mjs", text)
        self.assertIn('--output-dir "${PRIVATE_DIR}"', text)
        self.assertIn('--chrome-user-data-dir "${MY_BETS_CHROME_PROFILE_DIR}"', text)
        self.assertIn("import_my_bets_snapshot.py", text)
        self.assertIn("MY_BETS_CAPTURE_EXIT_CODE", text)
        self.assertIn("raw_text_stale", text)
        self.assertIn("raw_text_fresh", text)
        self.assertIn("--scraped-at", text)
        self.assertIn("my_bets_capture", text)
        self.assertIn("work/private/tab_fifa", text)
        self.assertIn("sanitize_public_manifest", text)
        self.assertIn("atomic_write_json", text)
        self.assertIn("POST_EXIT=0", text)
        self.assertIn("post_run_persistence_failed", text)
        self.assertIn("raise SystemExit(5)", text)
        self.assertIn("last_success", text)
        self.assertIn("automation_authorization", text)
        self.assertIn("private_position_bootstrap", text)
        self.assertIn("--allow-research-only-success", text)
        self.assertIn("TAB_FIFA_ALLOW_RESEARCH_ONLY_SUCCESS", text)
        self.assertIn("research_only_success_exit_override", text)
        self.assertIn("formal_exit_code", text)
        self.assertIn("effective_exit_code", text)
        self.assertIn("partial_daily_research_latest.json", text)
        self.assertNotIn('LOG_DIR="${OUTPUT_DIR}/automation_run_logs"', text)
        self.assertNotRegex(text, r"\b(click|tap|press)\b.*(odds|price|bet|selection)", "runner must not interact with TAB betting UI")
        python_start = text.index("<<'PY'\n") + len("<<'PY'\n")
        python_end = text.index("\nPY\n", python_start)
        compile(text[python_start:python_end], "run_tab_fifa_daily_automation.sh:embedded_python", "exec")

        completed = subprocess.run(
            [str(script), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("run_tab_fifa_daily_automation.sh --verify-only", completed.stdout)
        self.assertIn("run_tab_fifa_daily_automation.sh --allow-research-only-success", completed.stdout)
        self.assertIn("run_tab_fifa_daily_automation.sh --capture-my-bets --report-date DDMMYYYY", completed.stdout)
        self.assertIn("does not create a recurring", completed.stdout)
        self.assertIn("log in on your behalf", completed.stdout)
        self.assertIn("TAB_FIFA_OUTPUT_DIR", completed.stdout)
        self.assertIn("TAB_FIFA_LOG_DIR", completed.stdout)
        self.assertIn("TAB_FIFA_CAPTURE_MY_BETS", completed.stdout)
        self.assertIn("TAB_FIFA_VERIFY_MODE=hermetic", completed.stdout)
        self.assertIn("TAB_FIFA_ALLOW_RESEARCH_ONLY_SUCCESS=1", completed.stdout)

        daily_text = (ROOT / "run_daily_report.py").read_text(encoding="utf-8")
        self.assertIn("discover_tab_live_boards.mjs", daily_text)
        self.assertIn("write_live_board_discovery_before_raw_refresh", daily_text)
        self.assertIn("live_board_discovery_pre_raw", daily_text)
        self.assertIn("write_live_board_discovery_after_raw_failure", daily_text)
        self.assertIn("write_live_board_discovery_bundle", daily_text)
        self.assertIn("write_partial_research_sidecars_after_raw_failure", daily_text)
        self.assertIn("write_partial_daily_research_bundle", daily_text)
        self.assertIn("partial_daily_report_ready", daily_text)
        self.assertIn("write_source_model_github_metadata", daily_text)
        self.assertIn("write_source_model_registry_bundle", daily_text)
        self.assertIn("source_model_metadata", daily_text)
        self.assertIn("TAB_FIFA_SOURCE_METADATA_TIMEOUT_SECONDS", daily_text)
        self.assertIn("write_recommendation_operations_bundle", daily_text)
        self.assertIn("write_model_divergence_review_bundle", daily_text)
        self.assertIn("post_commit_research_sidecars", daily_text)

    def test_local_app_private_position_bootstrap_contract(self):
        server = ROOT / "scripts" / "tab_fifa_app_server.py"
        text = server.read_text(encoding="utf-8")
        self.assertIn("/api/active-test", text)
        self.assertIn("/api/backfill-missing", text)
        self.assertIn("/api/private-bootstrap", text)
        self.assertIn("/api/rerun-daily-report", text)
        self.assertIn("/api/public-raw-refresh", text)
        self.assertIn("/api/live-board-discovery", text)
        self.assertIn("/api/source-model-metadata-refresh", text)
        self.assertIn("/api/status", text)
        self.assertIn("start_private_position_bootstrap", text)
        self.assertIn("start_daily_report_rerun", text)
        self.assertIn("start_public_raw_refresh", text)
        self.assertIn("start_live_board_discovery", text)
        self.assertIn("start_source_model_metadata_refresh", text)
        self.assertIn("ACTION_TOKEN", text)
        self.assertIn("validate_post_request", text)
        self.assertIn("X-TAB-FIFA-Action-Token", text)
        self.assertIn("html_with_action_token", text)
        self.assertIn("invalid_origin", text)
        self.assertIn("invalid_referer", text)
        self.assertIn("invalid_host", text)
        self.assertIn("PRIVATE_BOOTSTRAP_PID_PATH", text)
        self.assertIn("DAILY_RERUN_PID_PATH", text)
        self.assertIn("PUBLIC_RAW_REFRESH_PID_PATH", text)
        self.assertIn("LIVE_DISCOVERY_PID_PATH", text)
        self.assertIn("SOURCE_METADATA_PID_PATH", text)
        self.assertIn("ACTIVE_BACKFILL_LATEST_JSON", text)
        self.assertIn("write_blocked_backfill_latest", text)
        self.assertIn("TAB_FIFA_HEADLESS=0 TAB_FIFA_REFRESH_RAW=reuse_fresh", text)
        self.assertIn("scripts/run_tab_fifa_daily_automation.sh --capture-my-bets", text)
        self.assertIn("--wait-for-login-ms 600000", text)
        self.assertIn("TAB_FIFA_REFRESH_RAW=reuse_fresh scripts/run_tab_fifa_daily_automation.sh", text)
        self.assertIn("public_raw_access_policy_blocked", text)
        self.assertIn("live_board_discovery_access_policy_blocked", text)
        self.assertIn("ai_controlled_access_rejected", text)
        self.assertIn("TAB_FIFA_HEADLESS=0", text)
        self.assertIn("scripts/refresh_source_model_metadata.py --output-dir", text)
        self.assertIn("freshness_status", text)

        self.assertIn("freshness_sla_hours", text)
        self.assertIn("scripts/build_downloads_app_entry.py", text)
        self.assertIn("process_running(PRIVATE_BOOTSTRAP_PID_PATH)", text)
        self.assertIn("process_running(DAILY_RERUN_PID_PATH)", text)
        self.assertIn("process_running(LIVE_DISCOVERY_PID_PATH)", text)
        self.assertIn("process_running(SOURCE_METADATA_PID_PATH)", text)
        self.assertIn("source_model_metadata", text)
        self.assertIn("LOCAL_WEB_APP_URL", text)
        self.assertIn("interaction_mode", text)
        self.assertIn('"primary": "web"', text)
        self.assertIn('"web_primary": True', text)
        self.assertIn('"current_surface": "local_web_app"', text)
        self.assertIn('"static_html_role": "read_only_preview"', text)
        self.assertIn('"runtime_controls_enabled": True', text)
        self.assertIn("current_private_position_bootstrap", text)
        self.assertIn("build_private_position_bootstrap_status", text)
        self.assertIn("private_preflight", text)
        self.assertIn("blocking_reason", text)
        self.assertIn("next_safe_action", text)
        self.assertIn("login_window_required", text)
        self.assertIn("credential_policy", text)
        self.assertIn("automation_boundary", text)
        self.assertIn("ENTRY_FALLBACK_HTML", text)
        self.assertIn("serve_first_readable", text)
        self.assertIn("safe_asset_paths", text)
        self.assertIn("active_test_fallback_payload", text)
        self.assertIn("refresh_assets: bool = False", text)
        self.assertIn("skipped_for_fast_result", text)
        self.assertIn("TAB_FIFA_FAST_ENTRY_REBUILD=1", text)
        entry_text = (ROOT / "scripts" / "build_downloads_app_entry.py").read_text(encoding="utf-8")
        self.assertIn("workflow_nav_html", entry_text)
        self.assertIn("operation-panel", entry_text)
        self.assertIn("user_operation_panel_html", entry_text)
        self.assertIn("updateOperationPanel", entry_text)
        self.assertIn("操作总览", entry_text)
        self.assertIn("command-center", entry_text)
        self.assertIn("automation-scorecard", entry_text)
        self.assertIn("automation_scorecard_html", entry_text)
        self.assertIn("automation_scorecard_from_artifacts", entry_text)
        self.assertIn("alternate-market-workbench", entry_text)
        self.assertIn("effective_alternate_plan", entry_text)
        self.assertIn("alternate_market_workbench_html", entry_text)
        self.assertIn("activeSkeletonHtml", entry_text)
        self.assertIn("缓存降级", entry_text)
        self.assertIn("工作台导航", entry_text)
        self.assertIn("fast_entry_rebuild", entry_text)
        self.assertIn("process_is_zombie", text)
        self.assertIn("rc=$?", text)
        self.assertNotIn("status=$?", text)
        self.assertNotRegex(text, r"\b(click|tap|press)\b.*(odds|price|selection)", "local app must not interact with betting controls")
        compile(text, "tab_fifa_app_server.py", "exec")

        entry = ROOT / "scripts" / "build_downloads_app_entry.py"
        entry_text = entry.read_text(encoding="utf-8")
        self.assertIn("recommendation-block", entry_text)
        self.assertIn("recommendation-block priority", entry_text)
        self.assertIn("推荐下注决策条", entry_text)
        self.assertIn('PYTHON_BIN="{sys.executable}"', entry_text)
        self.assertIn('"$PYTHON_BIN" scripts/tab_fifa_app_server.py', entry_text)
        self.assertNotIn("/usr/bin/python3 scripts/tab_fifa_app_server.py", entry_text)
        self.assertIn("RUNTIME_ENTRY_HTML", entry_text)
        self.assertIn("write_entry_html_artifacts", entry_text)
        self.assertIn("WEB_APP_URL", entry_text)
        self.assertIn("web-runtime-panel", entry_text)
        self.assertIn("data-primary-interaction-mode=\"web\"", entry_text)
        self.assertIn("网页主控台", entry_text)
        self.assertIn("运行交互方式", entry_text)
        self.assertIn("网页主控台优先", entry_text)
        self.assertIn("静态只读预览", entry_text)
        self.assertIn("打开网页主控台", entry_text)
        self.assertIn("runtimeStatusButton", entry_text)
        self.assertIn("PRIMARY_WEB_APP_URL", entry_text)
        self.assertIn("refreshRuntimeStatus", entry_text)
        self.assertIn("webAppPromptText", entry_text)
        self.assertIn("interaction_mode", entry_text)
        self.assertIn("runtime_controls_enabled", entry_text)
        self.assertIn("先看这里", entry_text)
        self.assertIn("每天至少 4 次分析", entry_text)
        self.assertIn("自动补缺状态", entry_text)
        self.assertIn("研究日报 automation", entry_text)
        self.assertIn("research_only_daily_report_ready", entry_text)
        self.assertIn("research_only_recurring_candidate_ready", entry_text)
        self.assertLess(entry_text.index('<section class="recommendation-block priority" id="recommendations">'), entry_text.index('<div class="hero">'))
        self.assertLess(entry_text.index("<h2>推荐下注板块</h2>"), entry_text.index("<h2>今日操作摘要</h2>"))
        self.assertLess(entry_text.index("{recommendations_table(rec_rows)}"), entry_text.index("{action_cards_html(rec_rows)}"))
        self.assertIn("概率赔率编辑", entry_text)
        self.assertIn("Edge", entry_text)
        self.assertIn("Edge信息", entry_text)
        self.assertIn("Edge 过门槛", entry_text)
        self.assertIn("edgeThreshold", entry_text)
        self.assertIn("盈亏平衡", entry_text)
        self.assertIn("套利率", entry_text)
        self.assertIn("Risk of ruin", entry_text)
        self.assertIn("半Kelly / 仓位", entry_text)
        self.assertIn("最低可接受赔率", entry_text)
        self.assertIn("价格容忍度", entry_text)
        self.assertIn("价值信号", entry_text)
        self.assertIn("上限占用", entry_text)
        self.assertIn("Kelly安全垫", entry_text)
        self.assertIn("风险调整分", entry_text)
        self.assertIn("组合RoR", entry_text)
        self.assertIn("组合Risk of ruin", entry_text)
        self.assertIn("组合预计收益", entry_text)
        self.assertIn("最坏新增亏损", entry_text)
        self.assertIn("最坏全输新增亏损", entry_text)
        self.assertIn("预算压力", entry_text)
        self.assertIn("组合风险与预算压力", entry_text)
        self.assertIn("portfolio_risk", entry_text)
        self.assertIn("board_scope_index", entry_text)
        self.assertIn("annotate_live_board_scope", entry_text)
        self.assertIn("live_board_scope_allowed", entry_text)
        self.assertIn("缺失板块候选", entry_text)
        self.assertIn("缺失板块排除审计", entry_text)
        self.assertIn("不进入当前推荐池", entry_text)
        self.assertIn("公开盘口状态", entry_text)
        self.assertIn("私有持仓状态", entry_text)
        self.assertIn("非surebet", entry_text)
        self.assertIn("每 AUD100 预期", entry_text)
        self.assertIn("每AUD100预期", entry_text)
        self.assertIn("RoR复核", entry_text)
        self.assertIn("判断依据包", entry_text)
        self.assertIn("analysis-basis-grid", entry_text)
        self.assertIn("概率价值依据", entry_text)
        self.assertIn("价格执行依据", entry_text)
        self.assertIn("风险控制依据", entry_text)
        self.assertIn("资料缺口", entry_text)
        self.assertIn("赛前复核清单", entry_text)
        self.assertIn("pre_bet_checklist_item_count", entry_text)
        self.assertIn("diagnostic-strip", entry_text)
        self.assertIn("diag-min-odds", entry_text)
        self.assertIn("diag-price-tolerance", entry_text)
        self.assertIn("diag-cap-usage", entry_text)
        self.assertIn("diag-kelly-margin", entry_text)
        self.assertIn("diag-value-score", entry_text)
        self.assertIn("diag-value-signal", entry_text)
        self.assertIn("formatSignedDecimal", entry_text)
        self.assertIn("diagnosticConclusion", entry_text)
        self.assertIn("valueSignalLabel", entry_text)
        self.assertIn("riskAdjustedValueScore", entry_text)
        self.assertIn("市场资金倾向分", entry_text)
        self.assertIn("市场资金分析", entry_text)
        self.assertIn("总资金代理", entry_text)
        self.assertIn("净资金代理", entry_text)
        self.assertIn("成交量代理", entry_text)
        self.assertIn("流动性", entry_text)
        self.assertIn("盘口深度", entry_text)
        self.assertIn("日均盘口变动浮动率", entry_text)
        self.assertIn("概率工程吸收", entry_text)
        self.assertIn("probability_engine_html", entry_text)
        self.assertIn("赛制规则", entry_text)
        self.assertIn("赛制模拟与预测合约", entry_text)
        self.assertIn("预测合约字段", entry_text)
        self.assertIn("校准/回测控制", entry_text)
        self.assertIn("prediction_timestamp", entry_text)
        self.assertIn("odds_phase", entry_text)
        self.assertIn("Dixon-Coles", entry_text)
        self.assertIn("Bayesian Poisson", entry_text)
        self.assertIn("Monte Carlo", entry_text)
        self.assertIn("xG/xT/VAEP", entry_text)
        self.assertIn("防泄漏/可复现要求", entry_text)
        self.assertIn("Brier / Log loss / 校准曲线", entry_text)
        self.assertIn("fixed_random_seed_policy", entry_text)
        self.assertIn("EV / RAEV / CLV", entry_text)
        self.assertIn("Logistic / XGBoost / CatBoost", entry_text)
        self.assertIn("Team / Player / Tactical / News", entry_text)
        self.assertIn("技术面规则", entry_text)
        self.assertIn("机器学习模型", entry_text)
        self.assertIn("基本面层级", entry_text)
        self.assertIn("RAEV = 模型认为的胜利概率", entry_text)
        self.assertIn("CLV = 下注时赔率是否优于 closing odds", entry_text)
        self.assertIn("funding-cell", entry_text)
        self.assertIn("diag-funding-score", entry_text)
        self.assertIn("estimateFundingScore", entry_text)
        self.assertIn("fundingBiasLabel", entry_text)
        self.assertIn("market_funding_analysis_html", entry_text)
        self.assertIn("Excel参考", entry_text)
        self.assertIn("template_evidence_digest", entry_text)
        self.assertIn("模板公式", entry_text)
        self.assertIn("template_formula_count", entry_text)
        self.assertIn("模板证据资料", entry_text)
        self.assertIn("template_analysis_materials", entry_text)
        self.assertIn("模板决策规则", entry_text)
        self.assertIn("riskDriverText", entry_text)
        self.assertIn("risk-value", entry_text)
        self.assertIn("edge-cell", entry_text)
        self.assertIn("arb-cell", entry_text)
        self.assertIn("ror-cell", entry_text)
        self.assertIn("buy-cell", entry_text)
        self.assertIn("data-original-action", entry_text)
        self.assertIn("原买入", entry_text)
        self.assertIn("estimateRiskOfRuin", entry_text)
        self.assertIn("主动测试与自动补缺", entry_text)
        self.assertIn("priorityActiveMessage", entry_text)
        self.assertIn("每4-5小时一次", entry_text)
        self.assertIn("setActiveMessage", entry_text)
        self.assertIn("positive-ev", entry_text)
        self.assertLess(entry_text.index("主动测试与自动补缺"), entry_text.index("<h2>主动测试与补跑</h2>"))
        self.assertIn("/api/active-test", entry_text)
        self.assertIn("/api/backfill-missing", entry_text)
        self.assertIn("持仓读取与日报发布", entry_text)
        self.assertIn("只读 Preflight", entry_text)
        self.assertIn("Preflight 阻塞", entry_text)
        self.assertIn("只读授权窗口", entry_text)
        self.assertIn("凭据策略", entry_text)
        self.assertIn("credential_policy", entry_text)
        self.assertIn("automation_boundary", entry_text)
        self.assertIn("privateBootstrapButton", entry_text)
        self.assertIn("dailyReportButton", entry_text)
        self.assertIn("rawRefreshButton", entry_text)
        self.assertIn("/api/private-bootstrap", entry_text)
        self.assertIn("/api/rerun-daily-report", entry_text)
        self.assertIn("/api/public-raw-refresh", entry_text)
        self.assertIn("escapeHtml", entry_text)
        self.assertIn("actionHeaders", entry_text)
        self.assertIn("postOptions", entry_text)
        self.assertIn("postJson", entry_text)
        self.assertIn("X-TAB-FIFA-Action-Token", entry_text)
        self.assertIn('meta[name="tab-fifa-action-token"]', entry_text)
        self.assertIn("公开盘口刷新", entry_text)
        self.assertIn("修复焦点", entry_text)
        self.assertIn("研究可用", entry_text)
        self.assertIn("当前研究证据", entry_text)
        self.assertIn("current_research_only_allowed", entry_text)
        self.assertIn("partial_research_refresh", entry_text)
        self.assertIn("repair_focus", entry_text)
        self.assertIn("补跑优先队列", entry_text)
        self.assertIn("priority_score", entry_text)
        self.assertIn("priority_reason", entry_text)
        self.assertIn("Automation 得分", entry_text)
        self.assertIn("automation_dashboard", entry_text)
        self.assertIn("Automation 成熟度验收", entry_text)
        self.assertIn("automation_maturity_latest.pdf", entry_text)
        self.assertIn("成熟度验收 JSON", entry_text)
        self.assertIn("Automation 恢复 Playbook", entry_text)
        self.assertIn("新旧变化", entry_text)
        self.assertIn("产品完成度 Dashboard", entry_text)
        self.assertIn("product_readiness_dashboard_latest.pdf", entry_text)
        self.assertIn("product_readiness_dashboard_latest.json", entry_text)
        self.assertIn("product_readiness_html", entry_text)
        self.assertIn("比静态报告更有价值", entry_text)
        self.assertIn("相对静态报告价值", entry_text)
        self.assertIn("<th>证据</th>", entry_text)
        self.assertIn("推荐操作 Dashboard", entry_text)
        self.assertIn("tab_fifa_dashboard_latest.pdf", entry_text)
        self.assertIn("tab_fifa_dashboard_latest.md", entry_text)
        self.assertIn("ensure_dashboard_sidecars", entry_text)
        self.assertIn("recommendation_operations_latest.pdf", entry_text)
        self.assertIn("recommendation_operations_latest.json", entry_text)
        self.assertIn("recommendation_operations_latest.md", entry_text)
        self.assertIn("recommendation_operations_html", entry_text)
        self.assertIn("策略表现 / CLV / ROI 回测 Dashboard", entry_text)
        self.assertIn("strategy_performance_latest.pdf", entry_text)
        self.assertIn("strategy_performance_latest.json", entry_text)
        self.assertIn("strategy_performance_latest.md", entry_text)
        self.assertIn("strategy_performance_html", entry_text)
        self.assertIn("outcome_pending", entry_text)
        self.assertIn("不编造收益", entry_text)
        self.assertIn("新旧报告变化总控台", entry_text)
        self.assertIn("report_evolution_latest.pdf", entry_text)
        self.assertIn("report_evolution_latest.json", entry_text)
        self.assertIn("report_evolution_latest.md", entry_text)
        self.assertIn("report_evolution_html", entry_text)
        self.assertIn("日报 diff、报告目录、推荐操作、策略表现和产品完成度变化", entry_text)
        self.assertLess(entry_text.index("{recommendations_table(rec_rows)}"), entry_text.index("{recommendation_operations_html(recommendation_operations)}"))
        self.assertLess(entry_text.index("{recommendation_operations_html(recommendation_operations)}"), entry_text.index("{strategy_performance_html(strategy_performance)}"))
        self.assertLess(entry_text.index("{strategy_performance_html(strategy_performance)}"), entry_text.index("{report_evolution_html(report_evolution)}"))
        self.assertLess(entry_text.index("{report_evolution_html(report_evolution)}"), entry_text.index("<h2>今日操作摘要</h2>"))
        self.assertIn("目标验收追踪", entry_text)
        self.assertIn("goal_traceability_latest.pdf", entry_text)
        self.assertIn("goal_traceability_latest.json", entry_text)
        self.assertIn("goal_traceability_html", entry_text)
        self.assertIn("Ready / Partial / Blocked", entry_text)
        self.assertIn("用户价值", entry_text)
        self.assertIn("持仓监控 Dashboard", entry_text)
        self.assertIn("position_monitor_latest.pdf", entry_text)
        self.assertIn("position_monitor_latest.json", entry_text)
        self.assertIn("position_monitor_html", entry_text)
        self.assertIn("account-update-pending", entry_text)
        self.assertIn("不展示账户余额或逐笔下注", entry_text)
        self.assertIn("Raw 恢复与补跑控制台", entry_text)
        self.assertIn("raw_refresh_recovery_latest.pdf", entry_text)
        self.assertIn("Raw 恢复 JSON", entry_text)
        self.assertIn("Partial freshness", entry_text)
        self.assertIn("Partial raw freshness", entry_text)
        self.assertIn("研究-only板块", entry_text)
        self.assertIn("自动raw允许", entry_text)
        self.assertIn("AI访问拒绝", entry_text)
        self.assertIn("检查Raw合规状态", entry_text)
        self.assertIn("Route mismatch", entry_text)
        self.assertIn("Diagnostics", entry_text)
        self.assertIn("diagnostics_status", entry_text)
        self.assertIn("板块级恢复矩阵", entry_text)
        self.assertIn("board_recovery_matrix", entry_text)
        self.assertIn("board_recovery_auto_retry_count", entry_text)
        self.assertIn("board_recovery_access_policy_blocked_count", entry_text)
        self.assertIn("board_recovery_validation_fix_count", entry_text)
        self.assertIn("board_recovery_staged_validation_error_count", entry_text)
        self.assertIn("访问政策阻断", entry_text)
        self.assertIn("matches_repair_validation_latest.json", entry_text)
        self.assertIn("Matches修复验证", entry_text)
        self.assertIn("Matches Repair Live Validation", entry_text)
        self.assertIn("matches_repair_validation_status", entry_text)
        self.assertIn("staged错误", entry_text)
        self.assertIn("修复验证", entry_text)
        self.assertIn("staged_validation_error_count", entry_text)
        self.assertIn("可自动重试", entry_text)
        self.assertIn("下一次刷新计划", entry_text)
        self.assertIn("TAB Live 访问合规状态", entry_text)
        self.assertIn("live_board_discovery_latest.pdf", entry_text)
        self.assertIn("live_board_discovery_latest.json", entry_text)
        self.assertIn("检查Live合规状态", entry_text)
        self.assertIn("liveDiscoveryButton", entry_text)
        self.assertIn("/api/live-board-discovery", entry_text)
        self.assertIn("Discovery Retry Queue", entry_text)
        self.assertIn("retry_required_count", entry_text)
        self.assertIn("质量门禁", entry_text)
        self.assertIn("Unavailable review queue", entry_text)
        self.assertIn("TAB 拒绝 AI controlled access", entry_text)
        self.assertIn("授权/导入后的板块可用性", entry_text)
        self.assertIn("可用板块策略", entry_text)
        self.assertIn("available_board_strategy_latest.pdf", entry_text)
        self.assertIn("available_board_strategy_latest.json", entry_text)
        self.assertIn("哪些能继续研究，哪些必须排除", entry_text)
        self.assertIn("{available_board_strategy_html(available_strategy)}", entry_text)
        self.assertLess(entry_text.index("{recommendations_table(rec_rows)}"), entry_text.index("{available_board_strategy_html(available_strategy)}"))
        self.assertIn("研究诊断日报", entry_text)
        self.assertIn("partial_daily_research_latest.pdf", entry_text)
        self.assertIn("partial_daily_research_latest.json", entry_text)
        self.assertIn("partial_daily_research_latest.md", entry_text)
        self.assertIn("{partial_daily_research_html(partial_daily_research)}", entry_text)
        self.assertIn("缺失板块写 No Bet / unavailable", entry_text)
        self.assertIn("不使用旧盘口补齐", entry_text)
        self.assertIn("ensure_partial_daily_research", entry_text)
        self.assertIn("*_partial_daily_research.*", entry_text)
        self.assertLess(entry_text.index("{available_board_strategy_html(available_strategy)}"), entry_text.index("{partial_daily_research_html(partial_daily_research)}"))
        self.assertIn("赛程校验 Dashboard", entry_text)
        self.assertIn("fixture_sanity_latest.pdf", entry_text)
        self.assertIn("fixture_sanity_latest.json", entry_text)
        self.assertIn("fixture_sanity_latest.md", entry_text)
        self.assertIn("openfootball_worldcup_2026_raw_latest.json", entry_text)
        self.assertIn("fixture_sanity_html", entry_text)
        self.assertIn("delayed_public_source_not_live", entry_text)
        self.assertIn("不是 live odds，也不替代 TAB 盘口", entry_text)
        self.assertLess(entry_text.index("{partial_daily_research_html(partial_daily_research)}"), entry_text.index("{fixture_sanity_html(fixture_sanity)}"))
        self.assertLess(entry_text.index("{available_board_strategy_html(available_strategy)}"), entry_text.index("{fixture_sanity_html(fixture_sanity)}"))
        self.assertLess(entry_text.index("{recommendations_table(rec_rows)}"), entry_text.index("{fixture_sanity_html(fixture_sanity)}"))
        self.assertIn("主动测试时间线 Dashboard", entry_text)
        self.assertIn("active_timeline_report_latest.pdf", entry_text)
        self.assertIn("主动测试时间线 JSON", entry_text)
        self.assertIn("研究诊断补写", entry_text)
        self.assertIn("补写执行金额", entry_text)
        self.assertIn("partial_daily_research", entry_text)
        self.assertIn("正式补跑", entry_text)
        self.assertIn("本地研究数据库", entry_text)
        self.assertIn("tab_fifa_reports.sqlite3", entry_text)
        self.assertIn("开源模型 Dashboard", entry_text)
        self.assertIn("tab_fifa_model_comparison_v0_1.pdf", entry_text)
        self.assertIn("tab_fifa_model_comparison_v0_1.json", entry_text)
        self.assertIn("model_comparison_dashboard_html", entry_text)
        self.assertIn("模型分歧复核 Dashboard", entry_text)
        self.assertIn("model_divergence_review_latest.pdf", entry_text)
        self.assertIn("model_divergence_review_latest.json", entry_text)
        self.assertIn("model_divergence_review_html", entry_text)
        self.assertIn("高优先级复核", entry_text)
        self.assertIn("只用于模型解释、分歧复核和概率校准", entry_text)
        self.assertIn("GitHub Source Audit", entry_text)
        self.assertIn("Automation 使用视角", entry_text)
        self.assertIn("automation_view", entry_text)
        self.assertIn("execution_unlock", entry_text)
        self.assertIn("blocked_by_design", entry_text)
        self.assertIn("raw/private/preflight/public-safety 任一失败", entry_text)
        self.assertIn("不自动下注；不点击赔率；不添加投注单；不绕过门禁", entry_text)
        self.assertIn("只用于模型解释、分歧复核和概率校准", entry_text)
        self.assertIn("开源模型库 Dashboard", entry_text)
        self.assertIn("source_model_registry_latest.pdf", entry_text)
        self.assertIn("source_model_registry_latest.json", entry_text)
        self.assertIn("source_model_registry_latest.md", entry_text)
        self.assertIn("source_model_registry_html", entry_text)
        self.assertIn("source_model_github_metadata_latest.json", entry_text)
        self.assertIn("sourceMetadataButton", entry_text)
        self.assertIn("sourceMetadataMessage", entry_text)
        self.assertIn("/api/source-model-metadata-refresh", entry_text)
        self.assertIn("刷新开源模型证据", entry_text)
        self.assertIn("只读访问 GitHub 公共 API", entry_text)
        self.assertIn("4小时 freshness", entry_text)
        self.assertIn("live_metadata_freshness_status", entry_text)
        self.assertIn("live_metadata_fresh_within_sla_count", entry_text)
        self.assertIn("live_metadata_age_hours", entry_text)
        self.assertIn("license_control_required", entry_text)
        self.assertIn("可复用功能", entry_text)
        self.assertIn("布局模式", entry_text)
        self.assertIn("UI / Dashboard Blueprint", entry_text)
        self.assertIn("UI蓝图", entry_text)
        self.assertIn("UI界面覆盖", entry_text)
        self.assertIn("dashboard_coverage_status", entry_text)
        self.assertIn("ui_blueprint", entry_text)
        self.assertIn("component_title", entry_text)
        self.assertIn("local_ui_contract", entry_text)
        self.assertIn("报表可视化覆盖", entry_text)
        self.assertIn("报表决策矩阵覆盖", entry_text)
        self.assertIn("database_saved_count", entry_text)
        self.assertIn("decision_matrix_ready_count", entry_text)
        self.assertIn("Top缺口", entry_text)
        self.assertIn("has_database_snapshot", entry_text)
        self.assertIn("report_visual_inventory_latest.pdf", entry_text)

    def test_downloads_entry_downgrades_recommendations_when_publish_gate_blocks(self):
        entry = ROOT / "scripts" / "build_downloads_app_entry.py"
        entry_text = entry.read_text(encoding="utf-8")
        self.assertIn("recommendation_execution_allowed", entry_text)
        self.assertIn("formal_report_publish_ready", entry_text)
        self.assertIn("raw_refresh_ready", entry_text)
        self.assertIn("apply_execution_gate", entry_text)
        self.assertIn('next_item["action"] = "暂停执行"', entry_text)
        self.assertIn('next_item["action_class"] = "blocked"', entry_text)
        self.assertIn('next_item["original_action_class"] = item.get("action_class")', entry_text)
        self.assertIn(".recommendations td.buy-cell", entry_text)
        self.assertIn("当前可执行新增暴露", entry_text)
        self.assertIn("新增执行金额为 AUD 0", entry_text)
        self.assertIn("暂不新增下注", entry_text)
        self.assertIn("研究候选合计", entry_text)
        self.assertIn("当前推荐池只包含 TAB live nav 已确认可研究的板块", entry_text)
        self.assertIn(".pill.blocked", entry_text)
        self.assertIn(".bet-card.blocked", entry_text)

    def test_local_app_blocks_public_raw_and_live_discovery_when_tab_rejects_ai_access(self):
        spec = importlib.util.spec_from_file_location("tab_fifa_app_server_policy_test", ROOT / "scripts" / "tab_fifa_app_server.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "outputs"
            output_dir.mkdir(parents=True)
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "blocker_codes": ["ai_controlled_access_rejected"],
                    "partial_research_refresh": {"status": "partial_ready", "successful_board_count": 4},
                },
            )
            original_output = module.OUTPUT_DIR
            try:
                module.OUTPUT_DIR = output_dir
                raw = module.start_public_raw_refresh()
                live = module.start_live_board_discovery()
                status = module.app_status()
            finally:
                module.OUTPUT_DIR = original_output

        self.assertFalse(raw["started"])
        self.assertTrue(raw["blocked"])
        self.assertEqual(raw["mode"], "public_raw_access_policy_blocked")
        self.assertEqual(raw["blocker_code"], "ai_controlled_access_rejected")
        self.assertIn("headed_fallback", raw["forbidden_recovery"])
        self.assertFalse(live["started"])
        self.assertTrue(live["blocked"])
        self.assertEqual(live["mode"], "live_board_discovery_access_policy_blocked")
        self.assertEqual(status["raw_refresh"]["blocker_codes"], ["ai_controlled_access_rejected"])

    def test_local_app_post_actions_require_local_action_token(self):
        spec = importlib.util.spec_from_file_location("tab_fifa_app_server_action_token_test", ROOT / "scripts" / "tab_fifa_app_server.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.ACTION_TOKEN = "unit-test-token"

        class FakeServer:
            server_port = 8767

        class FakeHandler:
            server = FakeServer()

            def __init__(self, headers):
                self.headers = headers

        valid = FakeHandler(
            {
                "Host": "127.0.0.1:8767",
                "Origin": "http://127.0.0.1:8767",
                "Referer": "http://127.0.0.1:8767/",
                "X-TAB-FIFA-Action-Token": "unit-test-token",
            }
        )
        self.assertEqual(module.validate_post_request(valid), (True, ""))

        missing_token = FakeHandler({"Host": "127.0.0.1:8767", "Origin": "http://127.0.0.1:8767"})
        self.assertEqual(module.validate_post_request(missing_token), (False, "invalid_action_token"))

        evil_origin = FakeHandler(
            {
                "Host": "127.0.0.1:8767",
                "Origin": "https://example.com",
                "X-TAB-FIFA-Action-Token": "unit-test-token",
            }
        )
        self.assertEqual(module.validate_post_request(evil_origin), (False, "invalid_origin"))

        evil_host = FakeHandler(
            {
                "Host": "example.com",
                "Origin": "http://127.0.0.1:8767",
                "X-TAB-FIFA-Action-Token": "unit-test-token",
            }
        )
        self.assertEqual(module.validate_post_request(evil_host), (False, "invalid_host"))

        injected = module.html_with_action_token("<html><head><title>x</title></head><body></body></html>")
        self.assertIn('name="tab-fifa-action-token"', injected)
        self.assertIn('content="unit-test-token"', injected)

    def test_local_app_status_section_payload_returns_single_status_block(self):
        spec = importlib.util.spec_from_file_location("tab_fifa_app_server_status_section_test", ROOT / "scripts" / "tab_fifa_app_server.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "outputs"
            output_dir.mkdir(parents=True)
            atomic_write_json(
                output_dir / "provider_config_doctor_latest.json",
                {
                    "status": "ready_with_warnings",
                    "summary": {
                        "issue_count": 1,
                        "legacy_sport_count": 1,
                        "next_safe_action": "先修正 sport key。",
                    },
                    "local_env": {"exists": True},
                    "the_odds_api": {
                        "api_key_present": True,
                        "sports_discovery_enabled": True,
                        "requested_sports": ["soccer_fifa_world_cup", "soccer_world_cup"],
                        "recommended_sports": ["soccer_fifa_world_cup"],
                        "known_invalid_or_legacy_sports": ["soccer_world_cup"],
                        "event_market_probe_limit": 0,
                    },
                    "opticodds": {"api_key_present": True},
                    "recommended_env_patch": {"TAB_FIFA_THE_ODDS_API_SPORTS": "soccer_fifa_world_cup"},
                    "current_executable_new_stake_aud": 0,
                },
            )
            atomic_write_json(
                output_dir / "provider_manual_overlay_publish_latest.json",
                {
                    "ok": False,
                    "status": "blocked_overlay_publish_preflight",
                    "formal_raw_publish_performed": False,
                    "raw_batch_manifest_written": False,
                    "current_executable_new_stake_aud": 0,
                },
            )
            atomic_write_json(
                output_dir / "position_monitor_latest.json",
                {
                    "executive_status": {
                        "status": "blocked",
                        "private_metrics_available": False,
                        "recommended_next_action": "建立 TAB 专用已登录 profile 后只读同步持仓。",
                    },
                    "summary": {
                        "report_date": "01012026",
                        "snapshot_ready": False,
                        "snapshot_status": "missing",
                        "snapshot_issue_count": 1,
                        "raw_text_exists": False,
                        "snapshot_exists": False,
                        "diagnostics_exists": False,
                        "profile_exists": True,
                        "preflight_status": "capture_not_run",
                        "preflight_blocking_reason": "尚未运行只读持仓读取。",
                        "preflight_next_safe_action": "点击只读持仓读取。",
                        "login_window_required": True,
                        "manual_step_required": True,
                        "wait_for_login_seconds": 600,
                        "capture_mode": "headed_read_only_authorized_profile",
                        "credential_policy": "不读取、不保存、不填写账号密码或OTP。",
                        "automation_boundary": "只读抓取；禁止赔率点击、下注单修改和自动下注。",
                        "public_visible_balance": "account-update-pending",
                        "public_visible_open_exposure": "account-update-pending",
                        "public_visible_realized_roi": "account-update-pending",
                        "raw_refresh_ready": False,
                        "active_backfill_queue_count": 8,
                    },
                    "monitor_rows": [
                        {
                            "item_id": "position_snapshot",
                            "label": "持仓快照",
                            "status": "missing",
                            "ready": False,
                            "next_action": "导入或刷新当日只读快照。",
                        },
                        {
                            "item_id": "profile",
                            "label": "TAB 专用 profile",
                            "status": "present",
                            "ready": True,
                            "next_action": "保持自动审计。",
                        },
                    ],
                    "private_metric_policy": {
                        "public_outputs": "只展示 ready/blocked、文件存在性和下一步。",
                        "amount_display_until_ready": "account-update-pending",
                        "credential_policy": "不读取、不保存、不填写账号密码或OTP。",
                        "automation_boundary": "只读抓取；禁止自动下注。",
                    },
                },
            )
            atomic_write_json(
                output_dir / "provider_manual_workbench_latest.json",
                {
                    "status": "waiting_for_first_batch",
                    "batch_count": 9,
                    "remaining_event_count": 68,
                    "remaining_high_priority_count": 55,
                    "next_batch": {"batch_id": "TT-001", "event_count": 8},
                    "pair_templates": {
                        "all_candidates_csv": "provider_manual_pair_template_latest.csv",
                        "next_batch_csv": "provider_manual_next_batch_pair_template_latest.csv",
                        "all_candidate_pair_rows": 136,
                        "next_batch_pair_rows": 16,
                        "import_target": DEFAULT_IMPORT_RELATIVE_PATH,
                    },
                    "operator_cockpit": {
                        "current_batch_id": "TT-001",
                        "current_batch_event_count": 8,
                        "current_batch_pair_rows": 16,
                        "next_batch_pair_template_csv": "provider_manual_next_batch_pair_template_latest.csv",
                        "import_target": DEFAULT_IMPORT_RELATIVE_PATH,
                        "publish_status": "blocked_until_manual_import_and_signature",
                        "can_publish_now": False,
                    },
                    "next_batch_summary": {"batch_id": "TT-001", "event_count": 8, "pair_rows_required": 16},
                    "import_quality": {
                        "status": "waiting_for_manual_rows",
                        "queue_count": 68,
                        "missing_event_count": 68,
                    },
                    "next_batch_quality": {
                        "batch_id": "TT-001",
                        "event_count": 8,
                        "status_counts": {"missing_rows": 8},
                        "rows": [
                            {
                                "rank": 1,
                                "event_id": "event-1",
                                "match": "Qatar v Switzerland",
                                "status": "missing_rows",
                                "missing_fields": ["decimal_odds"],
                                "missing_directions": ["over", "under"],
                                "next_action": "补字段和方向",
                            }
                        ],
                    },
                    "quality_gate_summary": {
                        "import_quality_status": "waiting_for_manual_rows",
                        "next_batch_quality_status_counts": {"missing_rows": 8},
                        "missing_event_count": 68,
                        "partial_event_count": 0,
                        "invalid_event_count": 0,
                        "complete_event_count": 0,
                        "next_action": "填写 TT-001",
                    },
                    "field_checklist": [{"field": "decimal_odds", "required": True}],
                    "workflow_steps": [{"step": 1, "title": "只读 TAB 核验", "status": "manual_required"}],
                    "action_contract": {"forbidden_actions": ["点击赔率", "加入 Bet Slip"]},
                    "manual_intake_contract": {
                        "title": "TT-001 Team Total 人工导入合同",
                        "current_batch_id": "TT-001",
                        "template_csv": "provider_manual_next_batch_pair_template_latest.csv",
                        "import_target": DEFAULT_IMPORT_RELATIVE_PATH,
                        "import_target_display": f"outputs/{DEFAULT_IMPORT_RELATIVE_PATH}",
                        "rebuild_command": "TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py",
                        "current_state": {
                            "missing_event_count": 68,
                            "next_batch_pair_rows": 16,
                            "current_executable_new_stake_aud": 0,
                        },
                        "acceptance_criteria": ["current_executable_new_stake_aud=0"],
                        "forbidden_actions": ["点击赔率", "加入 Bet Slip"],
                    },
                    "current_executable_new_stake_aud": 0,
                },
            )
            atomic_write_json(
                output_dir / "provider_alternate_plan_latest.json",
                {
                    "status": "fallback_required",
                    "refresh_id": "provider-low-yield-team-total",
                    "probe_queue_count": 0,
                    "fallback_queue_count": 68,
                    "credit_policy": {
                        "recommended_batch_size": 0,
                        "estimated_next_batch_credit_floor": 0,
                        "estimated_next_batch_credit_ceiling": 0,
                    },
                    "recommended_command": "暂停 The Odds API team_totals；改查 OpticOdds 或 TAB 人工最终校验候选比赛。",
                    "recommended_next_action": "Team Total 转入人工校验。",
                    "operational_decision": {
                        "status": "manual_or_official_provider_priority",
                        "title": "Team Total 转人工/官方访问优先",
                        "primary_action": "先处理 TT-001 人工校验。",
                    },
                    "event_probe_evidence": {
                        "market_probe_count": 3,
                        "event_odds_count": 0,
                        "team_total_available_probe_count": 0,
                        "total_available_probe_count": 3,
                    },
                    "market_family_gaps": [
                        {
                            "id": "btts",
                            "label": "Both Teams to Score",
                            "role": "value_support",
                            "covered_count": 24,
                            "event_count": 68,
                            "coverage_ratio": 0.3529,
                            "required_ratio": 0.35,
                            "missing_count": 44,
                            "status": "ready",
                            "provider_status": "available_in_current_the_odds_api_tab_sample",
                            "available_probe_count": 24,
                            "recommended_provider_action": "覆盖已达到研究阈值，候选下注前仍需 TAB 最终校验。",
                        },
                        {
                            "id": "total_ou",
                            "label": "Total Goals Over/Under",
                            "role": "core_price_context",
                            "covered_count": 54,
                            "event_count": 68,
                            "coverage_ratio": 0.7941,
                            "required_ratio": 0.7,
                            "missing_count": 14,
                            "status": "ready",
                            "provider_status": "coverage_threshold_met",
                            "available_probe_count": 12,
                            "recommended_provider_action": "核心大小球覆盖已达到研究阈值。",
                        },
                        {
                            "id": "team_total_ou",
                            "label": "Team Total Goals Over/Under",
                            "role": "primary_market",
                            "covered_count": 0,
                            "event_count": 68,
                            "coverage_ratio": 0.0,
                            "required_ratio": 0.7,
                            "missing_count": 68,
                            "status": "gap",
                            "provider_status": "not_available_in_current_the_odds_api_tab_sample",
                            "available_probe_count": 0,
                            "recommended_provider_action": "走 TT-001 人工只读或 OpticOdds 官方访问。",
                        },
                    ],
                    "next_probe_queue": [
                        {
                            "event_id": "event-next",
                            "match": "Argentina v Algeria",
                            "commence_time": "2026-06-17T01:00:00Z",
                            "missing_families": ["Double Chance"],
                            "recommended_markets": ["double_chance"],
                            "recommended_action": "仅在 credit_safe 时小批量 probe。",
                        }
                    ],
                    "stop_conditions": ["如果 credit runway 不安全，暂停 The Odds API batch。"],
                    "current_executable_new_stake_aud": 0,
                },
            )
            atomic_write_json(
                output_dir / "provider_kpi_latest.json",
                {
                    "provider_analysis_ready": True,
                    "refresh_id": "provider-low-yield-team-total",
                    "formal_publish_allowed": False,
                    "full_automation_allowed": False,
                    "current_executable_new_stake_aud": 0,
                    "executive_status": {
                        "status": "in_progress",
                        "overall_progress_pct": 0.615,
                        "primary_gap": "Team Total Score O/U 覆盖: 0/68",
                        "recommended_next_action": "先处理 TT-001 人工校验。",
                    },
                    "summary": {
                        "event_count": 68,
                        "credit": {
                            "reported_remaining": 229,
                            "reported_used": 271,
                            "remaining_ratio": 0.458,
                            "reported_last_request_cost": 7,
                            "inferred_monthly_limit": 500,
                        },
                    },
                },
            )
            original_output = module.OUTPUT_DIR
            try:
                module.OUTPUT_DIR = output_dir
                config_payload, config_status_code = module.app_status_section_payload(
                    "/api/status.provider_config_doctor"
                )
                payload, status_code = module.app_status_section_payload("/api/status.provider_manual_overlay_publish")
                workbench_payload, workbench_status_code = module.app_status_section_payload(
                    "/api/status.provider_manual_workbench"
                )
                alternate_payload, alternate_status_code = module.app_status_section_payload(
                    "/api/status.provider_alternate_plan"
                )
                command_center_payload, command_center_status_code = module.app_status_section_payload(
                    "/api/status.provider_command_center"
                )
                alternate_workbench_payload, alternate_workbench_status_code = module.app_status_section_payload(
                    "/api/status.provider_alternate_workbench"
                )
                position_monitor_payload, position_monitor_status_code = module.app_status_section_payload(
                    "/api/status.position_monitor"
                )
                work_queue_payload, work_queue_status_code = module.app_status_section_payload(
                    "/api/status.automation_work_queue"
                )
                scorecard_payload, scorecard_status_code = module.app_status_section_payload(
                    "/api/status.automation_scorecard"
                )
                operation_payload, operation_status_code = module.app_status_section_payload(
                    "/api/status.operation_panel"
                )
                missing_payload, missing_status_code = module.app_status_section_payload("/api/status.not_a_real_status")
                bad_payload, bad_status_code = module.app_status_section_payload("/api/status.provider-manual")
            finally:
                module.OUTPUT_DIR = original_output

        self.assertEqual(config_status_code, 200)
        self.assertEqual(config_payload["status"], "ready_with_warnings")
        self.assertTrue(config_payload["the_odds_api_key_present"])
        self.assertEqual(config_payload["known_invalid_or_legacy_sports"], ["soccer_world_cup"])
        self.assertEqual(config_payload["recommended_env_patch"]["TAB_FIFA_THE_ODDS_API_SPORTS"], "soccer_fifa_world_cup")
        self.assertEqual(config_payload["current_executable_new_stake_aud"], 0)
        self.assertEqual(status_code, 200)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["key"], "provider_manual_overlay_publish")
        self.assertEqual(payload["status"], "blocked_overlay_publish_preflight")
        self.assertFalse(payload["formal_raw_publish_performed"])
        self.assertFalse(payload["raw_batch_manifest_written"])
        self.assertEqual(payload["current_executable_new_stake_aud"], 0)
        self.assertEqual(workbench_status_code, 200)
        self.assertEqual(workbench_payload["status"], "waiting_for_first_batch")
        self.assertEqual(workbench_payload["batch_count"], 9)
        self.assertEqual(workbench_payload["remaining_event_count"], 68)
        self.assertEqual(workbench_payload["next_batch_id"], "TT-001")
        self.assertEqual(workbench_payload["all_candidate_pair_rows"], 136)
        self.assertEqual(workbench_payload["next_batch_pair_rows"], 16)
        self.assertEqual(workbench_payload["next_batch_pair_template_csv"], "provider_manual_next_batch_pair_template_latest.csv")
        self.assertEqual(workbench_payload["operator_cockpit"]["current_batch_id"], "TT-001")
        self.assertEqual(workbench_payload["next_batch_summary"]["pair_rows_required"], 16)
        self.assertEqual(workbench_payload["import_quality"]["status"], "waiting_for_manual_rows")
        self.assertEqual(workbench_payload["next_batch_quality"]["status_counts"]["missing_rows"], 8)
        self.assertEqual(workbench_payload["quality_gate_summary"]["missing_event_count"], 68)
        self.assertEqual(workbench_payload["field_checklist"][0]["field"], "decimal_odds")
        self.assertEqual(workbench_payload["workflow_steps"][0]["status"], "manual_required")
        self.assertIn("点击赔率", workbench_payload["action_contract"]["forbidden_actions"])
        self.assertEqual(workbench_payload["manual_intake_contract"]["current_batch_id"], "TT-001")
        self.assertEqual(workbench_payload["manual_intake_contract"]["import_target"], DEFAULT_IMPORT_RELATIVE_PATH)
        self.assertIn("build_downloads_app_entry.py", workbench_payload["manual_intake_contract"]["rebuild_command"])
        self.assertFalse(workbench_payload["can_publish_now"])
        self.assertEqual(workbench_payload["publish_status"], "blocked_until_manual_import_and_signature")
        self.assertEqual(workbench_payload["current_executable_new_stake_aud"], 0)
        self.assertEqual(alternate_status_code, 200)
        self.assertTrue(alternate_payload["ready"])
        self.assertEqual(alternate_payload["status"], "fallback_required")
        self.assertEqual(alternate_payload["fallback_queue_count"], 68)
        self.assertEqual(alternate_payload["operational_decision"]["status"], "manual_or_official_provider_priority")
        self.assertEqual(alternate_payload["event_probe_evidence"]["market_probe_count"], 3)
        self.assertEqual(alternate_payload["event_probe_evidence"]["team_total_available_probe_count"], 0)
        self.assertEqual(alternate_payload["current_executable_new_stake_aud"], 0)
        self.assertEqual(command_center_status_code, 200)
        self.assertEqual(command_center_payload["status"], "fallback_required")
        self.assertFalse(command_center_payload["can_run_provider_batch"])
        self.assertEqual(command_center_payload["provider_batch"]["recommended_batch_size"], 0)
        self.assertEqual(command_center_payload["provider_batch"]["estimated_credit_floor"], 0)
        self.assertEqual(command_center_payload["provider_batch"]["provider_key_present"], True)
        self.assertEqual(command_center_payload["credit"]["reported_remaining"], 229)
        self.assertEqual(command_center_payload["credit_runway"]["status"], "no_api_batch_recommended")
        self.assertEqual(command_center_payload["credit_runway"]["reserve_floor"], 200)
        self.assertEqual(command_center_payload["team_total_manual"]["next_batch_id"], "TT-001")
        self.assertEqual(command_center_payload["team_total_manual"]["next_batch_pair_rows"], 16)
        self.assertEqual(
            command_center_payload["team_total_manual"]["manual_intake_contract"]["import_target"],
            DEFAULT_IMPORT_RELATIVE_PATH,
        )
        self.assertEqual(command_center_payload["evidence"]["team_total_available_probe_count"], 0)
        self.assertFalse(command_center_payload["gates"]["formal_publish_allowed"])
        self.assertFalse(command_center_payload["gates"]["full_automation_allowed"])
        self.assertEqual(command_center_payload["gates"]["current_executable_new_stake_aud"], 0)
        self.assertEqual(alternate_workbench_status_code, 200)
        self.assertTrue(alternate_workbench_payload["ready"])
        self.assertEqual(alternate_workbench_payload["status"], "fallback_required")
        self.assertEqual(alternate_workbench_payload["summary"]["market_family_count"], 3)
        self.assertEqual(alternate_workbench_payload["summary"]["coverage_threshold_met_count"], 2)
        self.assertEqual(alternate_workbench_payload["summary"]["manual_or_official_required_count"], 1)
        self.assertEqual(alternate_workbench_payload["summary"]["value_support_ready_count"], 1)
        self.assertEqual(alternate_workbench_payload["credit_runway_status"], "no_api_batch_recommended")
        market_action_by_id = {item["market_id"]: item for item in alternate_workbench_payload["market_rows"]}
        self.assertEqual(market_action_by_id["team_total_ou"]["action_status"], "manual_or_official_required")
        self.assertEqual(alternate_workbench_payload["next_probe_queue_preview"][0]["match"], "Argentina v Algeria")
        self.assertEqual(alternate_workbench_payload["current_executable_new_stake_aud"], 0)
        self.assertIn("不触发 API refresh", alternate_workbench_payload["safety_boundary"])
        self.assertEqual(position_monitor_status_code, 200)
        self.assertFalse(position_monitor_payload["ready"])
        self.assertTrue(position_monitor_payload["artifact_ready"])
        self.assertEqual(position_monitor_payload["status"], "blocked")
        self.assertEqual(position_monitor_payload["report_date"], "01012026")
        self.assertFalse(position_monitor_payload["snapshot_ready"])
        self.assertTrue(position_monitor_payload["profile_exists"])
        self.assertEqual(position_monitor_payload["public_visible_balance"], "account-update-pending")
        self.assertEqual(position_monitor_payload["current_executable_new_stake_aud"], 0)
        self.assertEqual(position_monitor_payload["monitor_rows"][0]["item_id"], "position_snapshot")
        self.assertIn("只读抓取", position_monitor_payload["automation_boundary"])
        self.assertEqual(work_queue_status_code, 200)
        self.assertFalse(work_queue_payload["automation_ready"])
        self.assertFalse(work_queue_payload["formal_publish_allowed"])
        self.assertFalse(work_queue_payload["full_automation_allowed"])
        self.assertEqual(work_queue_payload["current_executable_new_stake_aud"], 0)
        self.assertEqual(work_queue_payload["summary"]["team_total_missing_event_count"], 68)
        self.assertEqual(work_queue_payload["summary"]["team_total_next_batch_pair_rows"], 16)
        task_by_id = {item["id"]: item for item in work_queue_payload["tasks"]}
        self.assertEqual(work_queue_payload["tasks"][0]["priority"], "P0")
        self.assertIn("TT-001", task_by_id)
        self.assertEqual(task_by_id["TT-001"]["status"], "manual_required")
        self.assertEqual(task_by_id["TT-001"]["artifact"], f"outputs/{DEFAULT_IMPORT_RELATIVE_PATH}")
        self.assertIn("build_downloads_app_entry.py", task_by_id["TT-001"]["command"])
        self.assertIn("CREDIT-RESERVE", task_by_id)
        self.assertEqual(task_by_id["CREDIT-RESERVE"]["status"], "credit_or_yield_blocked")
        self.assertIn("FORMAL-PUBLISH-GATE", task_by_id)
        self.assertEqual(task_by_id["FORMAL-PUBLISH-GATE"]["status"], "blocked_until_manual_signature")
        self.assertEqual(task_by_id["MY-BETS-READONLY"]["status"], "login_required")
        self.assertIn("profile_exists=True", task_by_id["MY-BETS-READONLY"]["evidence"])
        self.assertIn("AUTOMATION-READINESS", task_by_id)
        self.assertIn("不触发 provider refresh", work_queue_payload["safety_boundary"])
        self.assertEqual(scorecard_status_code, 200)
        self.assertTrue(scorecard_payload["ready"])
        self.assertEqual(scorecard_payload["automation_progress_pct"], 0.4)
        self.assertEqual(scorecard_payload["passed_weight"], 40)
        self.assertEqual(scorecard_payload["total_weight"], 100)
        self.assertEqual(scorecard_payload["next_gate_id"], "provider_key_and_sport_config")
        self.assertFalse(scorecard_payload["can_enter_daily_automation"])
        self.assertEqual(scorecard_payload["current_executable_new_stake_aud"], 0)
        scorecard_gate_by_id = {item["id"]: item for item in scorecard_payload["gate_rows"]}
        self.assertEqual(scorecard_gate_by_id["provider_key_and_sport_config"]["status"], "blocked")
        self.assertEqual(scorecard_gate_by_id["core_matches_coverage"]["status"], "passed")
        self.assertEqual(scorecard_gate_by_id["value_support_coverage"]["status"], "passed")
        self.assertEqual(scorecard_gate_by_id["team_total_coverage"]["status"], "manual_required")
        self.assertIn("不触发 provider refresh", scorecard_payload["safety_boundary"])
        self.assertEqual(operation_status_code, 200)
        self.assertTrue(operation_payload["ready"])
        self.assertEqual(operation_payload["headline"], "当前不要新增下注")
        self.assertEqual(operation_payload["primary_label"], "填写 TT-001")
        self.assertEqual(operation_payload["primary_href"], "#team-total-manual-entry")
        self.assertEqual(operation_payload["current_executable_new_stake_aud"], 0)
        self.assertEqual(operation_payload["status_cards"][0]["status"], "blocked")
        self.assertEqual(operation_payload["quick_steps"][1]["href"], "#team-total-manual-entry")
        self.assertGreaterEqual(len(operation_payload["blockers"]), 1)
        self.assertIn("不触发 provider refresh", operation_payload["safety_boundary"])
        self.assertEqual(missing_status_code, 404)
        self.assertEqual(missing_payload["error"], "unknown_status_key")
        self.assertEqual(bad_status_code, 400)
        self.assertEqual(bad_payload["error"], "invalid_status_key")

    def test_provider_command_center_blocks_api_batch_when_next_batch_crosses_credit_reserve(self):
        spec = importlib.util.spec_from_file_location("tab_fifa_app_server_credit_runway_test", ROOT / "scripts" / "tab_fifa_app_server.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        payload = module.provider_command_center_payload(
            provider_config_doctor={
                "summary": {"next_safe_action": "配置可用。"},
                "the_odds_api": {"api_key_present": True},
            },
            provider_kpi={
                "refresh_id": "provider-credit-reserve",
                "summary": {
                    "credit": {
                        "reported_remaining": 201,
                        "reported_used": 299,
                        "remaining_ratio": 0.402,
                        "reported_last_request_cost": 7,
                        "inferred_monthly_limit": 500,
                    }
                },
                "executive_status": {"primary_gap": "Team Total 0/64", "recommended_next_action": "转人工。"},
                "formal_publish_allowed": False,
                "full_automation_allowed": False,
                "current_executable_new_stake_aud": 0,
            },
            provider_alternate_plan={
                "status": "in_progress",
                "refresh_id": "provider-credit-reserve",
                "probe_queue_count": 50,
                "credit_policy": {
                    "recommended_batch_size": 1,
                    "estimated_next_batch_credit_floor": 4,
                    "estimated_next_batch_credit_ceiling": 7,
                },
                "recommended_command": "python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches",
                "operational_decision": {"title": "非 Team Total 可补齐", "primary_action": "小批量补齐。"},
                "event_probe_evidence": {"market_probe_count": 14, "team_total_available_probe_count": 0},
            },
            provider_manual_workbench={
                "status": "waiting_for_first_batch",
                "next_batch": {"batch_id": "TT-001", "event_count": 8},
                "pair_templates": {"next_batch_pair_rows": 16},
                "quality_gate_summary": {"missing_event_count": 64},
            },
        )

        self.assertFalse(payload["can_run_provider_batch"])
        self.assertEqual(payload["provider_batch"]["recommended_batch_size"], 1)
        self.assertEqual(payload["credit_runway"]["status"], "next_batch_would_cross_reserve")
        self.assertEqual(payload["credit_runway"]["reported_remaining"], 201)
        self.assertEqual(payload["credit_runway"]["remaining_after_next_batch_ceiling"], 194)
        self.assertEqual(payload["credit_runway"]["safe_next_batch_count_before_reserve"], 0)
        self.assertIn("暂停 API", payload["credit_runway"]["recommended_action"])
        self.assertEqual(payload["gates"]["current_executable_new_stake_aud"], 0)

    def test_local_app_manual_team_total_entry_writes_fixed_import_target(self):
        spec = importlib.util.spec_from_file_location("tab_fifa_app_server_manual_entry_test", ROOT / "scripts" / "tab_fifa_app_server.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            refresh_id = "provider-manual-entry"
            staged_rel = "provider_raw/provider-manual-entry/world_cup_matches.json"
            staged_path = output_dir / staged_rel
            staged_path.parent.mkdir(parents=True)
            atomic_write_json(
                staged_path,
                {
                    "matches": [
                        {
                            "provider_event_id": "event-1",
                            "match": "Qatar v Switzerland",
                            "commence_time": "2026-06-12T05:00:00Z",
                            "markets": {"Result": {}, "Total Goals Over/Under": {}},
                        }
                    ]
                },
            )
            atomic_write_json(
                output_dir / ODDS_PROVIDER_COVERAGE_LATEST,
                {
                    "refresh_id": refresh_id,
                    "scope": "matches",
                    "targets": [
                        {
                            "board_id": "world_cup_matches",
                            "provider_staged_path": staged_rel,
                            "market_coverage": {
                                "Result": 1,
                                "Total Goals Over/Under": 1,
                                "Team Total Goals Over/Under": 0,
                            },
                        }
                    ],
                },
            )
            write_provider_manual_verification_bundle(output_dir)
            original = {
                "OUTPUT_DIR": module.OUTPUT_DIR,
                "refresh_download_assets": module.refresh_download_assets,
            }
            try:
                module.OUTPUT_DIR = output_dir
                module.refresh_download_assets = lambda: None
                payload = module.manual_team_total_entry_payload()
                empty_result, empty_status = module.save_manual_team_total_entry(
                    {"import_target": "/tmp/should-not-be-used.csv", "entries": [{"event_id": "event-1"}]}
                )
                empty_rows = read_csv_rows(output_dir / DEFAULT_IMPORT_RELATIVE_PATH)
                result, status = module.save_manual_team_total_entry(
                    {
                        "entries": [
                            {
                                "event_id": "event-1",
                                "tab_match_name": "Qatar v Switzerland",
                                "team_scope": "home",
                                "tab_market_name": "Qatar Team Total Goals",
                                "line": "1.5",
                                "over_decimal_odds": "1.91",
                                "under_decimal_odds": "1.91",
                                "observed_at_aest": "2026-06-14 08:00 AEST",
                                "operator_initials": "LZ",
                                "evidence_note_or_screenshot_ref": "TAB readonly final check",
                                "verification_status": "verified",
                            }
                        ]
                    }
                )
            finally:
                for name, value in original.items():
                    setattr(module, name, value)

            import_path = output_dir / DEFAULT_IMPORT_RELATIVE_PATH
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["event_count"], 1)
            self.assertEqual(payload["entries"][0]["match"], "Qatar v Switzerland")
            self.assertEqual(payload["import_target"], DEFAULT_IMPORT_RELATIVE_PATH)
            self.assertEqual(empty_status, 200)
            self.assertEqual(empty_result["import_target"], DEFAULT_IMPORT_RELATIVE_PATH)
            self.assertEqual(empty_result["complete_event_count"], 0)
            self.assertEqual(empty_result["skipped_incomplete_event_count"], 1)
            self.assertEqual(empty_result["invalid_row_count"], 0)
            self.assertEqual(len(empty_rows), 2)
            self.assertEqual({row["verification_status"] for row in empty_rows}, {"pending"})
            self.assertFalse(any(row["decimal_odds"] for row in empty_rows))
            self.assertFalse((output_dir / "tmp" / "should-not-be-used.csv").exists())
            self.assertEqual(status, 200)
            self.assertTrue(result["ok"])
            self.assertEqual(result["import_target"], DEFAULT_IMPORT_RELATIVE_PATH)
            self.assertEqual(result["written_row_count"], 2)
            self.assertEqual(result["complete_event_count"], 1)
            self.assertEqual(result["skipped_incomplete_event_count"], 0)
            self.assertEqual(result["valid_row_count"], 2)
            self.assertEqual(result["invalid_row_count"], 0)
            self.assertEqual(result["manual_import_status"], "import_ready_for_hash_gate")
            self.assertEqual(result["quality_status"], "complete_quality_ready_for_hash_gate")
            rows = read_csv_rows(import_path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(set(rows[0].keys()), set(CSV_FIELDS))
            self.assertEqual({row["selection_name"] for row in rows}, {"Over", "Under"})
            self.assertEqual({row["decimal_odds"] for row in rows}, {"1.91"})
            self.assertEqual({row["verification_status"] for row in rows}, {"verified"})
            self.assertEqual(result["current_executable_new_stake_aud"], 0)

    def test_active_backfill_queue_prioritizes_largest_gaps(self):
        spec = importlib.util.spec_from_file_location("active_timeline_priority_test", ROOT / "scripts" / "active_timeline_check.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        queue = module.build_backfill_queue(
            [
                {
                    "report_date": "01012026",
                    "display_date": "01/01/2026",
                    "needs_backfill": True,
                    "backfill_reasons": ["有效分析 2/4"],
                    "effective_analysis_count": 2,
                    "covered_slots": ["00:00-05:00", "05:00-10:00"],
                    "missing_slots": ["10:00-15:00"],
                    "formal_report_exists": True,
                    "latest_status": "blocked_by_gate",
                },
                {
                    "report_date": "02012026",
                    "display_date": "02/01/2026",
                    "needs_backfill": True,
                    "backfill_reasons": ["有效分析 0/4", "Downloads 正式日报缺失"],
                    "effective_analysis_count": 0,
                    "covered_slots": [],
                    "missing_slots": ["00:00-05:00", "05:00-10:00", "10:00-15:00", "15:00-20:00"],
                    "formal_report_exists": False,
                    "latest_status": "missing",
                },
            ],
            min_analyses=4,
        )

        self.assertEqual(queue[0]["report_date"], "02012026")
        self.assertEqual(queue[0]["repair_rank"], 1)
        self.assertGreater(queue[0]["priority_score"], queue[1]["priority_score"])
        self.assertIn("缺失时段 4/5", queue[0]["priority_reason"])
        self.assertIn("日报缺失", queue[0]["priority_reason"])

    def test_active_backfill_fails_fast_when_raw_refresh_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "outputs"
            output_dir.mkdir()
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "ready_required_target_count": 0,
                    "blocker_codes": ["refresh_command_failed", "stale_raw"],
                    "recommended_next_action": "检查 raw refresh 诊断输出和 Chrome/TAB 访问状态后重新执行只读刷新。",
                },
            )
            spec = importlib.util.spec_from_file_location("active_timeline_check_test", ROOT / "scripts" / "active_timeline_check.py")
            module = importlib.util.module_from_spec(spec)
            self.assertIsNotNone(spec.loader)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            original_paths = {
                "OUTPUT_DIR": module.OUTPUT_DIR,
                "BACKFILL_LATEST_JSON": module.BACKFILL_LATEST_JSON,
                "RAW_REFRESH_HEALTH_JSON": module.RAW_REFRESH_HEALTH_JSON,
            }
            try:
                module.OUTPUT_DIR = output_dir
                module.BACKFILL_LATEST_JSON = output_dir / "active_backfill_latest.json"
                module.RAW_REFRESH_HEALTH_JSON = output_dir / "raw_refresh_health_latest.json"
                payload = {
                    "days": [
                        {
                            "report_date": "01012026",
                            "display_date": "01/01/2026",
                            "needs_backfill": True,
                            "backfill_reasons": ["有效分析 0/4"],
                        }
                    ]
                }
                args = argparse.Namespace(max_backfill_runs=1)
                result = module.run_backfills(args, payload)
            finally:
                for name, value in original_paths.items():
                    setattr(module, name, value)

            self.assertEqual(result["status"], "blocked_by_raw_refresh")
            self.assertEqual(result["requested_count"], 0)
            self.assertEqual(result["completed_count"], 0)
            self.assertEqual(result["blocked_queue_count"], 1)
            self.assertEqual(result["blocker"]["code"], "raw_refresh_not_ready")
            self.assertEqual(result["blocker"]["blocker_codes"], ["refresh_command_failed", "stale_raw"])
            self.assertIn("partial_daily_research", result)
            self.assertEqual(result["partial_daily_research"]["status"], "blocked")
            self.assertFalse(result["partial_daily_research"]["execution_allowed"])
            self.assertEqual(result["partial_daily_research"]["current_executable_new_stake_aud"], 0)
            self.assertIn("未达到 ready", result["partial_daily_research"]["message"])
            self.assertNotIn("已补写", result["partial_daily_research"]["message"])
            self.assertTrue((output_dir / "active_backfill_latest.json").exists())
            self.assertTrue((output_dir / PARTIAL_DAILY_RESEARCH_JSON_LATEST).exists())
            latest_backfill = json.loads((output_dir / "active_backfill_latest.json").read_text(encoding="utf-8"))
            self.assertIn("partial_daily_research", latest_backfill)
            self.assertEqual(latest_backfill["partial_daily_research"]["current_executable_new_stake_aud"], 0)

    def test_active_timeline_persists_history_to_report_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "outputs"
            output_dir.mkdir()
            db_path = output_dir / "tab_fifa_reports.sqlite3"
            raw_health = output_dir / "raw_refresh_health_latest.json"
            backfill_latest = output_dir / "active_backfill_latest.json"
            atomic_write_json(
                raw_health,
                {"ready": False, "status": "blocked", "blocker_codes": ["stale_raw"]},
            )
            atomic_write_json(backfill_latest, {"status": "blocked_by_raw_refresh"})
            spec = importlib.util.spec_from_file_location("active_timeline_persist_test", ROOT / "scripts" / "active_timeline_check.py")
            module = importlib.util.module_from_spec(spec)
            self.assertIsNotNone(spec.loader)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            original_paths = {
                "DB_PATH": module.DB_PATH,
                "RAW_REFRESH_HEALTH_JSON": module.RAW_REFRESH_HEALTH_JSON,
                "BACKFILL_LATEST_JSON": module.BACKFILL_LATEST_JSON,
            }
            try:
                module.DB_PATH = db_path
                module.RAW_REFRESH_HEALTH_JSON = raw_health
                module.BACKFILL_LATEST_JSON = backfill_latest
                result = module.persist_timeline_audit(
                    {
                        "generated_at": "2026-01-01T10:00:00+11:00",
                        "timezone": "Australia/Sydney",
                        "summary": {
                            "day_count": 2,
                            "complete_day_count": 1,
                            "missing_analysis_day_count": 1,
                            "missing_report_day_count": 1,
                            "backfill_queue_count": 1,
                            "cadence_ready_for_all_days": False,
                            "formal_report_ready_for_all_days": False,
                        },
                        "days": [],
                    }
                )
            finally:
                for name, value in original_paths.items():
                    setattr(module, name, value)

            self.assertEqual(result["status"], "stored")
            self.assertEqual(result["table"], "active_timeline_audits")
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM active_timeline_audits").fetchone()
                self.assertEqual(row["day_count"], 2)
                self.assertEqual(row["complete_day_count"], 1)
                self.assertEqual(row["backfill_status"], "blocked_by_raw_refresh")
                self.assertEqual(row["raw_refresh_status"], "blocked")
                self.assertEqual(json.loads(row["raw_blocker_json"]), ["stale_raw"])

    def test_local_app_backfill_button_blocks_when_raw_refresh_is_not_ready(self):
        spec = importlib.util.spec_from_file_location("tab_fifa_app_server_backfill_test", ROOT / "scripts" / "tab_fifa_app_server.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "outputs"
            private_log_dir = root / "private" / "logs"
            output_dir.mkdir(parents=True)
            atomic_write_json(
                output_dir / "raw_refresh_health_latest.json",
                {
                    "ready": False,
                    "status": "blocked",
                    "ready_required_target_count": 0,
                    "blocker_codes": ["stale_raw"],
                },
            )
            atomic_write_json(output_dir / "active_timeline_latest.json", {"summary": {"backfill_queue_count": 3}})
            original = {
                "OUTPUT_DIR": module.OUTPUT_DIR,
                "PRIVATE_LOG_DIR": module.PRIVATE_LOG_DIR,
                "BACKFILL_PID_PATH": module.BACKFILL_PID_PATH,
                "ACTIVE_BACKFILL_LATEST_JSON": module.ACTIVE_BACKFILL_LATEST_JSON,
            }
            try:
                module.OUTPUT_DIR = output_dir
                module.PRIVATE_LOG_DIR = private_log_dir
                module.BACKFILL_PID_PATH = private_log_dir / "active_backfill_worker.pid"
                module.ACTIVE_BACKFILL_LATEST_JSON = output_dir / "active_backfill_latest.json"
                result = module.start_backfill()
                status = module.app_status()
            finally:
                for name, value in original.items():
                    setattr(module, name, value)

            self.assertTrue(result["ok"])
            self.assertFalse(result["started"])
            self.assertTrue(result["blocked"])
            self.assertEqual(result["blocker"]["code"], "raw_refresh_not_ready")
            self.assertEqual(result["blocked_queue_count"], 3)
            self.assertEqual(result["latest_status"], "blocked_by_raw_refresh")
            self.assertIn("partial_daily_research", result)
            self.assertEqual(result["partial_daily_research"]["status"], "blocked")
            self.assertFalse(result["partial_daily_research"]["execution_allowed"])
            self.assertEqual(result["partial_daily_research"]["current_executable_new_stake_aud"], 0)
            self.assertIn("研究诊断日报", result["message"])
            self.assertIn("未达到 ready", result["message"])
            self.assertNotIn("已补写", result["message"])
            self.assertFalse((private_log_dir / "active_backfill_worker.pid").exists())
            blocked_payload = json.loads((output_dir / "active_backfill_latest.json").read_text(encoding="utf-8"))
            self.assertEqual(blocked_payload["status"], "blocked_by_raw_refresh")
            self.assertEqual(blocked_payload["blocked_queue_count"], 3)
            self.assertEqual(blocked_payload["total_backfill_queue_count"], 3)
            self.assertEqual(blocked_payload["max_backfill_runs"], 3)
            self.assertEqual(blocked_payload["requested_count"], 0)
            self.assertEqual(blocked_payload["completed_count"], 0)
            self.assertIn("partial_daily_research", blocked_payload)
            self.assertEqual(blocked_payload["partial_daily_research"]["current_executable_new_stake_aud"], 0)
            self.assertTrue((output_dir / PARTIAL_DAILY_RESEARCH_JSON_LATEST).exists())
            self.assertEqual(status["partial_daily_research"]["current_executable_new_stake_aud"], 0)
            self.assertEqual(status["partial_daily_research"]["status"], "blocked")

    def test_local_app_active_test_returns_cached_timeline_on_runtime_failure(self):
        spec = importlib.util.spec_from_file_location("tab_fifa_app_server_active_test", ROOT / "scripts" / "tab_fifa_app_server.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "outputs"
            output_dir.mkdir(parents=True)
            latest = output_dir / "active_timeline_latest.json"
            atomic_write_json(
                latest,
                {
                    "summary": {
                        "day_count": 2,
                        "missing_analysis_day_count": 1,
                        "missing_report_day_count": 1,
                        "backfill_queue_count": 1,
                    },
                    "days": [],
                    "backfill_queue": [],
                },
            )
            original = {
                "OUTPUT_DIR": module.OUTPUT_DIR,
                "ACTIVE_TIMELINE_LATEST_JSON": module.ACTIVE_TIMELINE_LATEST_JSON,
            }
            try:
                module.OUTPUT_DIR = output_dir
                module.ACTIVE_TIMELINE_LATEST_JSON = latest
                with mock.patch.object(
                    module.subprocess,
                    "run",
                    side_effect=subprocess.TimeoutExpired(cmd=["active_timeline_check.py"], timeout=45),
                ):
                    result = module.run_active_test()
            finally:
                for name, value in original.items():
                    setattr(module, name, value)

            self.assertTrue(result["ok"])
            self.assertTrue(result["fallback_used"])
            self.assertEqual(result["summary"]["backfill_queue_count"], 1)
            self.assertEqual(result["auto_backfill"]["started"], False)
            self.assertTrue(result["auto_backfill"]["fallback_guard"])
            self.assertEqual(result["active_test_runtime"]["mode"], "cached_timeline_after_failure")

    def test_my_bets_capture_script_contract_is_readonly_private(self):
        script = ROOT / "scripts" / "capture_tab_my_bets_readonly.mjs"
        text = script.read_text(encoding="utf-8")
        self.assertIn("isBlockedMyBetsRequest", text)
        self.assertIn("POST", text)
        self.assertIn("place-bet", text)
        self.assertIn("--chrome-user-data-dir", text)
        self.assertIn("--wait-for-login-ms", text)
        self.assertIn('serviceWorkers: "block"', text)
        self.assertIn("tab_chrome_profile", text)
        self.assertIn("My Bets capture refuses to write into public outputs", text)
        self.assertIn("requires an output directory under a private path", text)
        self.assertIn("requires the Chrome profile under a private path", text)
        self.assertNotRegex(text, r"\b(click|tap|press)\b.*(odds|price|bet|selection)", "capture must not interact with betting UI")

        bundled = Path("/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
        node = Path(os.environ.get("TAB_FIFA_NODE_BIN") or str(bundled if bundled.exists() else (shutil.which("node") or bundled)))
        if not node.exists():
            self.skipTest(f"node runtime not available: {node}")
        env = os.environ.copy()
        env.pop("TAB_FIFA_CHROME_USER_DATA_DIR", None)
        completed = subprocess.run(
            [str(node), str(script), "--dry-run", "--report-date", "01012026"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["raw_text_file"], "tab_my_bets_raw_01012026.txt")
        self.assertEqual(payload["diagnostics_file"], "tab_my_bets_capture_diagnostics_01012026.json")
        self.assertEqual(payload["auth_profile"], "tab_chrome_profile")
        self.assertTrue(payload["path_guard_ready"])

    def test_verify_readiness_script_splits_hermetic_and_live_artifact_gates(self):
        script = ROOT / "scripts" / "verify_fifa_automation_readiness.sh"
        text = script.read_text(encoding="utf-8")
        self.assertIn("--hermetic", text)
        self.assertIn("--live-artifacts", text)
        self.assertIn("--artifact-chain-only", text)
        self.assertIn("TAB_FIFA_VERIFY_MODE", text)
        hermetic_exit_idx = text.index("OK: FIFA automation readiness hermetic verification passed.")
        live_gate_idx = text.index('echo "[8/8] Report artifact safety and preflight scan"')
        raw_gate_idx = text.index("raw_gate = audit_raw_refresh(output_dir)")
        consistency_idx = text.index("latest_commit_artifact_consistency_issues(payload)")
        preflight_idx = text.index("technical_preflight_publication_blocker(preflight, payload)")
        self.assertLess(hermetic_exit_idx, live_gate_idx)
        self.assertLess(live_gate_idx, raw_gate_idx)
        self.assertLess(raw_gate_idx, consistency_idx)
        self.assertLess(consistency_idx, preflight_idx)

    def test_runbook_contract_documents_failure_matrix_and_boundaries(self):
        runbook = ROOT / "RUNBOOK.md"
        text = runbook.read_text(encoding="utf-8")
        self.assertIn("失败处理矩阵", text)
        self.assertIn("config/automation.toml", text)
        self.assertIn("allow_auto_betting = false", text)
        self.assertIn("不自动下注", text)
        self.assertIn("不点击赔率价格", text)
        for marker in [
            "automation unauthorized",
            "raw_refresh_blocked",
            "access_denied",
            "raw_stale",
            "mixed_refresh_id",
            "event/source failed",
            "public_artifact_safety_failed",
            "latest_publish_failed",
            "test failure",
        ]:
            self.assertIn(marker, text)

    def test_staged_raw_refresh_gate_validates_before_promote(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            boards = [
                BoardConfig(
                    board_id="world_cup_matches",
                    refresh_board_id="matches",
                    name="2026 World Cup Matches",
                    tab_path="/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches",
                    priority=1,
                    version="test",
                    required_for_full_automation=True,
                    parser_strategy="fixture",
                    refresh_method="fixture",
                    raw_snapshot="matches.json",
                    recommendations_artifact=None,
                    gate_artifact=None,
                    report_artifact=None,
                )
            ]
            partial = partial_matches_raw_fixture()
            partial["refresh_id"] = "batch-staged"
            atomic_write_json(output_dir / "matches.json", partial)
            gate = audit_staged_raw_refresh(
                output_dir,
                boards=boards,
                expected_refresh_id="batch-staged",
                now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(gate["staged_raw_ready"])
            self.assertTrue(any("staged raw validation failed" in reason for reason in gate["blocking_reasons"]))

            full = full_matches_raw_fixture()
            full["refresh_id"] = "batch-staged"
            atomic_write_json(output_dir / "matches.json", full)
            gate = audit_staged_raw_refresh(
                output_dir,
                boards=boards,
                expected_refresh_id="batch-staged",
                now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(gate["staged_raw_ready"])
            self.assertFalse(gate["refresh_batch_manifest_ready"])
            write_raw_refresh_batch_manifest(output_dir, "batch-staged", boards=boards, generated_at="2026-06-03T00:00:00Z")
            gate = audit_staged_raw_refresh(
                output_dir,
                boards=boards,
                expected_refresh_id="batch-staged",
                now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc),
            )
            self.assertTrue(gate["staged_raw_ready"])

            full["refresh_id"] = "other-batch"
            atomic_write_json(output_dir / "matches.json", full)
            gate = audit_staged_raw_refresh(
                output_dir,
                boards=boards,
                expected_refresh_id="batch-staged",
                now=datetime(2026, 6, 3, 1, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(gate["staged_raw_ready"])
            self.assertTrue(any("does not match expected" in reason for reason in gate["blocking_reasons"]))

    def test_automation_gate_blocks_access_denied_match_detail(self):
        raw = full_matches_raw_fixture()
        canada = next(match for match in raw["matches"] if match["match"] == "Canada v Bosn-Herzegovina")
        canada["title"] = "Access Denied"
        canada["access_status"] = "access_denied"
        canada["markets"] = {}
        canada["partial_core_only"] = True
        gate = automation_gate(
            raw,
            generate_candidates(raw),
            public_source_audit={"all_sources_ok": True},
            event_audit={"all_feeds_ok": True},
        )
        self.assertFalse(gate["automation_ready"])
        self.assertEqual(gate["coverage"]["access_denied_matches"], 1)
        self.assertIn("Canada v Bosn-Herzegovina", gate["quality_audit"]["access_denied_matches"])
        self.assertTrue(any("Access Denied" in reason for reason in gate["blocking_reasons"]))

    def test_in_play_match_is_excluded_from_pre_match_gate(self):
        raw = full_matches_raw_fixture()
        usa = next(match for match in raw["matches"] if match["match"] == "USA v Paraguay")
        usa["text"] = "USA v Paraguay\nIn-Play|Bet by phone for suspended markets."
        usa["markets"]["Both Teams to Score"] = "Both Teams to Score\nUSA v Paraguay\nIn-Play|Bet by phone\n"

        gate = automation_gate(
            raw,
            generate_candidates(raw),
            public_source_audit={"all_sources_ok": True},
            event_audit={"all_feeds_ok": True},
        )

        self.assertTrue(match_is_in_play(usa))
        self.assertTrue(gate["automation_ready"])
        self.assertEqual(gate["coverage"]["pre_match_eligible_matches"], len(EXPECTED_MATCHES) - 1)
        self.assertEqual(gate["coverage"]["in_play_excluded_matches"], 1)
        self.assertIn("USA v Paraguay", gate["quality_audit"]["in_play_excluded_matches"])
        self.assertNotIn("USA v Paraguay", gate["quality_audit"]["partial_core_only_matches"])

    def test_in_play_match_is_not_recommended_as_pre_match_candidate(self):
        raw = {
            "generated_at": "2026-06-13T00:00:00Z",
            "source": "unit_fixture",
            "target_matches": ["USA v Paraguay"],
            "matches": [full_match_fixture("USA v Paraguay")],
        }
        self.assertTrue(generate_candidates(raw))

        raw["matches"][0]["text"] = "USA v Paraguay\nIn-Play|Bet by phone for suspended markets."
        self.assertEqual(generate_candidates(raw), [])

    def test_raw_refresh_dry_run_contract_does_not_require_playwright(self):
        bundled = Path("/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
        node = Path(os.environ.get("TAB_FIFA_NODE_BIN") or str(bundled if bundled.exists() else (shutil.which("node") or bundled)))
        if not node.exists():
            self.skipTest(f"node runtime not available: {node}")
        env = os.environ.copy()
        env["TAB_FIFA_NODE_MODULES"] = str(Path(tempfile.gettempdir()) / "missing-tab-fifa-node-modules")
        completed = subprocess.run(
            [
                str(node),
                str(ROOT / "scripts" / "refresh_tab_readonly.mjs"),
                "--dry-run",
                "--board",
                "matches",
                "--refresh-id",
                "dry-run-test",
                "--smoke",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["dry_run"])
        self.assertTrue(payload["smoke"])
        self.assertEqual(payload["refresh_id"], "dry-run-test")
        self.assertEqual(payload["boards"][0]["board_id"], "matches")
        self.assertIn("tab_fifa_matches_main_markets_raw_v0_9.json", payload["boards"][0]["output"])

    def test_live_board_discovery_dry_run_contract_does_not_require_playwright(self):
        bundled = Path("/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
        node = Path(os.environ.get("TAB_FIFA_NODE_BIN") or str(bundled if bundled.exists() else (shutil.which("node") or bundled)))
        if not node.exists():
            self.skipTest(f"node runtime not available: {node}")
        env = os.environ.copy()
        env["TAB_FIFA_NODE_MODULES"] = str(Path(tempfile.gettempdir()) / "missing-tab-fifa-node-modules")
        completed = subprocess.run(
            [
                str(node),
                str(ROOT / "scripts" / "discover_tab_live_boards.mjs"),
                "--dry-run",
                "--output-dir",
                str(Path(tempfile.gettempdir()) / "tab-live-board-discovery"),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["dry_run"])
        self.assertIn("tab_fifa_live_board_discovery_raw_latest.json", payload["output"])
        self.assertTrue(any(row["refresh_board_id"] == "australia_markets" for row in payload["expected_boards"]))
        self.assertIn("https://www.tab.com.au/sports/betting/Soccer", payload["url"])

    def test_live_board_discovery_preserves_visible_match_links(self):
        bundled = Path("/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
        node = Path(os.environ.get("TAB_FIFA_NODE_BIN") or str(bundled if bundled.exists() else (shutil.which("node") or bundled)))
        if not node.exists():
            self.skipTest(f"node runtime not available: {node}")
        snippet = """
import { expectedBoardRows } from './scripts/discover_tab_live_boards.mjs';
const links = Array.from({ length: 12 }, (_, index) => ({
  text: `Team${index} v Opp${index}`,
  href: `https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/Team${index}%20v%20Opp${index}`
}));
const rows = expectedBoardRows(links, '2026 World Cup Matches', true);
const matches = rows.find((row) => row.refresh_board_id === 'matches');
console.log(JSON.stringify({ matched: matches.matched_link_count, retained: matches.matched_links.length }));
"""
        completed = subprocess.run(
            [str(node), "--input-type=module", "-e", snippet],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["matched"], 12)
        self.assertEqual(payload["retained"], 12)

    def test_refresh_script_live_match_targets_env_contract(self):
        bundled = Path("/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
        node = Path(os.environ.get("TAB_FIFA_NODE_BIN") or str(bundled if bundled.exists() else (shutil.which("node") or bundled)))
        if not node.exists():
            self.skipTest(f"node runtime not available: {node}")
        env = os.environ.copy()
        env["TAB_FIFA_MATCH_TARGETS_JSON"] = json.dumps(
            [
                {
                    "match": "Canada v Bosn-Herzegovina",
                    "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/Canada%20v%20Bosn-Herzegovina",
                },
                {
                    "match": "324 Markets",
                    "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/Canada%20v%20Bosn-Herzegovina",
                },
                {
                    "match": "USA v Paraguay",
                    "href": "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/USA%20v%20Paraguay",
                },
                {"match": "Soccer", "href": "https://www.tab.com.au/sports/results/Soccer/competitions/2026%20World%20Cup%20Matches"},
            ]
        )
        snippet = """
import { liveMatchTargetsFromEnv, isUsableMatchHref } from './scripts/refresh_tab_readonly.mjs';
const rows = liveMatchTargetsFromEnv();
console.log(JSON.stringify({
  count: rows.length,
  names: rows.map((row) => row.match),
  matchHref: isUsableMatchHref('https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/USA%20v%20Paraguay'),
  boardHref: isUsableMatchHref('https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches')
}));
"""
        completed = subprocess.run(
            [str(node), "--input-type=module", "-e", snippet],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["names"], ["Canada v Bosn-Herzegovina", "USA v Paraguay"])
        self.assertTrue(payload["matchHref"])
        self.assertFalse(payload["boardHref"])

    def test_australia_refresh_route_mismatch_contract_is_public_safe(self):
        bundled = Path("/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
        node = Path(os.environ.get("TAB_FIFA_NODE_BIN") or str(bundled if bundled.exists() else (shutil.which("node") or bundled)))
        if not node.exists():
            self.skipTest(f"node runtime not available: {node}")
        snippet = """
import { validatePayload } from './scripts/refresh_tab_readonly.mjs';
try {
  validatePayload(
    { board: '2026 World Cup Australia Markets', mode: 'australia_expanded' },
    {
      title: '2026 World Cup Matches Betting & Odds 2026 - TAB.com.au',
      text: 'Home\\nSoccer\\n2026 World Cup Matches\\n2026 World Cup Matches - Betting Odds',
      markets: [{ id: 'team_group_match_wins', beforeClass: '', beforeText: '', afterClass: '', afterText: '' }]
    },
    true
  );
  process.exit(2);
} catch (error) {
  console.log(error.message);
}
"""
        completed = subprocess.run(
            [str(node), "--input-type=module", "-e", snippet],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("route mismatch", completed.stdout)
        self.assertIn("landed on 2026 World Cup Matches", completed.stdout)
        self.assertNotIn(str(ROOT), completed.stdout)

    def test_status_helpers_prefer_current_private_position_date_over_stale_latest_commit(self):
        self.assertEqual(
            position_report_date(
                {},
                {"private_position_bootstrap": {"report_date": "01012026"}},
                {"report_date": "02012026"},
                default_date="13062026",
            ),
            "13062026",
        )
        self.assertEqual(
            position_report_date(
                {"report_date": "14062026"},
                {"private_position_bootstrap": {"report_date": "01012026"}},
                {"report_date": "02012026"},
                default_date="13062026",
            ),
            "14062026",
        )
        self.assertIn(
            "并行处理两个门禁",
            position_recommended_next_action(
                {"ready": False, "next_action": "建立或刷新 TAB 专用已登录 profile。"},
                {"ready": False},
            ),
        )

        import scripts.tab_fifa_app_server as app_server

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "outputs"
            output_dir.mkdir(parents=True)
            original_output = app_server.OUTPUT_DIR
            try:
                app_server.OUTPUT_DIR = output_dir
                stale_readiness = {
                    "private_position_bootstrap": {
                        "ready": True,
                        "report_date": "01012026",
                        "status": "snapshot_ready",
                    }
                }
                bootstrap = app_server.current_private_position_bootstrap(stale_readiness, "13062026")
            finally:
                app_server.OUTPUT_DIR = original_output
            self.assertEqual(bootstrap["report_date"], "13062026")
            self.assertFalse(bootstrap["ready"])
            self.assertEqual(bootstrap["status"], "capture_not_run")

    def test_raw_refresh_refuses_canonical_output_dir_before_browser_launch(self):
        bundled = Path("/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
        node = Path(os.environ.get("TAB_FIFA_NODE_BIN") or str(bundled if bundled.exists() else (shutil.which("node") or bundled)))
        if not node.exists():
            self.skipTest(f"node runtime not available: {node}")
        env = os.environ.copy()
        env["TAB_FIFA_NODE_MODULES"] = str(Path(tempfile.gettempdir()) / "missing-tab-fifa-node-modules")
        canonical_output_dir = Path(tempfile.gettempdir()) / "tab-fifa-canonical-refusal-output"
        env["TAB_FIFA_OUTPUT_DIR"] = str(canonical_output_dir)
        completed = subprocess.run(
            [
                str(node),
                str(ROOT / "scripts" / "refresh_tab_readonly.mjs"),
                "--board",
                "matches",
                "--output-dir",
                str(canonical_output_dir),
                "--refresh-id",
                "canonical-refusal-test",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("refuses to write directly to canonical outputs", completed.stderr or completed.stdout)

    def test_failed_preflight_sanitizes_local_paths_in_exception_message(self):
        import run_daily_report as daily

        with tempfile.TemporaryDirectory() as tmp:
            original_out = daily.OUT
            original_path = daily.PREFLIGHT_PATH
            daily.OUT = Path(tmp)
            daily.PREFLIGHT_PATH = Path(tmp) / "automation_preflight_latest.json"
            try:
                daily.write_failed_preflight(
                    "failed-run",
                    RuntimeError(
                        "Command '['/Users/tester/.cache/node/bin/node', "
                        "'/Users/tester/project/scripts/refresh_tab_readonly.mjs', "
                        "'/var/folders/0w/example/T/tab-fifa-refresh-abc']' timed out after 900 seconds"
                    ),
                )
                run_path = daily.preflight_run_path("failed-run")
                text = run_path.read_text(encoding="utf-8")
                payload = json.loads(text)
                self.assertNotIn("/Users/", text)
                self.assertNotIn("/var/folders/", text)
                self.assertIn("node", payload["blocking_reasons"][0])
                self.assertIn("refresh_tab_readonly.mjs", payload["blocking_reasons"][0])
                self.assertFalse(daily.PREFLIGHT_PATH.exists())
                self.assertTrue(audit_public_artifact_safety([run_path])["public_artifact_safety_ready"])
                published_path = daily.write_failed_preflight(
                    "failed-run-latest",
                    RuntimeError("technical preflight failed after private snapshot gate"),
                    publish_latest=True,
                )
                self.assertEqual(published_path.name, "automation_preflight_failed-run-latest.json")
                self.assertTrue(daily.PREFLIGHT_PATH.exists())
                self.assertTrue(audit_public_artifact_safety([published_path, daily.PREFLIGHT_PATH])["public_artifact_safety_ready"])
            finally:
                daily.OUT = original_out
                daily.PREFLIGHT_PATH = original_path

    def test_refresh_process_timeout_is_bounded_and_configurable(self):
        import run_daily_report as daily

        old_value = os.environ.get("TAB_FIFA_REFRESH_PROCESS_TIMEOUT_SECONDS")
        old_chunk = os.environ.get("TAB_FIFA_MATCHES_REFRESH_CHUNK_SIZE")
        try:
            os.environ.pop("TAB_FIFA_REFRESH_PROCESS_TIMEOUT_SECONDS", None)
            os.environ.pop("TAB_FIFA_MATCHES_REFRESH_CHUNK_SIZE", None)
            self.assertEqual(refresh_process_timeout_seconds(), 180)
            self.assertEqual(daily.refresh_process_timeout_seconds("matches"), 180)
            self.assertEqual(daily.refresh_process_timeout_seconds("futures"), 180)
            self.assertEqual(matches_refresh_chunk_size(), 5)
            os.environ["TAB_FIFA_MATCHES_REFRESH_CHUNK_SIZE"] = "100"
            self.assertEqual(daily.matches_refresh_chunk_size(), len(EXPECTED_MATCHES))
            os.environ["TAB_FIFA_MATCHES_REFRESH_CHUNK_SIZE"] = "bad"
            self.assertEqual(daily.matches_refresh_chunk_size(), 5)
            os.environ["TAB_FIFA_REFRESH_PROCESS_TIMEOUT_SECONDS"] = "10"
            self.assertEqual(daily.refresh_process_timeout_seconds(), 30)
            self.assertEqual(daily.refresh_process_timeout_seconds("matches"), 30)
            os.environ["TAB_FIFA_REFRESH_PROCESS_TIMEOUT_SECONDS"] = "9999"
            self.assertEqual(daily.refresh_process_timeout_seconds(), 900)
            os.environ["TAB_FIFA_REFRESH_PROCESS_TIMEOUT_SECONDS"] = "bad"
            self.assertEqual(daily.refresh_process_timeout_seconds(), 180)
            self.assertEqual(daily.refresh_process_timeout_seconds("matches"), 180)
        finally:
            if old_value is None:
                os.environ.pop("TAB_FIFA_REFRESH_PROCESS_TIMEOUT_SECONDS", None)
            else:
                os.environ["TAB_FIFA_REFRESH_PROCESS_TIMEOUT_SECONDS"] = old_value
            if old_chunk is None:
                os.environ.pop("TAB_FIFA_MATCHES_REFRESH_CHUNK_SIZE", None)
            else:
                os.environ["TAB_FIFA_MATCHES_REFRESH_CHUNK_SIZE"] = old_chunk

    def test_pdf_input_gate_requires_all_boards(self):
        ready_gate = {"automation_ready": True, "blocking_reasons": []}
        portfolio = {"portfolio_automation_ready": True, "blocking_reasons": []}
        safety = {"automation_safety_ready": True, "blocking_reasons": []}
        raw_refresh = {"raw_refresh_ready": True, "blocking_reasons": []}
        assert_pdf_input_gates(
            {"automation_gate": ready_gate},
            {"automation_gate": ready_gate},
            {"automation_gate": ready_gate},
            {"automation_gate": ready_gate},
            {"automation_gate": ready_gate},
            portfolio,
            safety,
            raw_refresh,
        )
        with self.assertRaises(RuntimeError):
            assert_pdf_input_gates(
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                portfolio,
                None,
                raw_refresh,
            )
        with self.assertRaises(RuntimeError):
            assert_pdf_input_gates(
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                portfolio,
                safety,
                None,
            )
        with self.assertRaises(RuntimeError):
            assert_pdf_input_gates(
                {"automation_gate": ready_gate},
                {"automation_gate": {"automation_ready": False, "blocking_reasons": ["futures failed"]}},
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                {"automation_gate": ready_gate},
                portfolio,
                safety,
                raw_refresh,
            )

    def test_safe_odds_formatting_handles_missing_values(self):
        self.assertEqual(odds_or_pending(None), "待同步")
        self.assertEqual(odds_or_pending(1.234), "1.23")

    def test_risky_autobet_code_scan_detects_click_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "danger.py").write_text("page.click('button')", encoding="utf-8")
            (root / "danger.mjs").write_text("await submitBet()", encoding="utf-8")
            hits = scan_risky_autobet_code(root)
            self.assertTrue(any(hit["pattern"] == "page.click(" for hit in hits))
            self.assertTrue(any(hit["pattern"] == "submitBet" for hit in hits))


if __name__ == "__main__":
    unittest.main()
