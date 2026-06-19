from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from qbvs.batch import stress_random_parallel
from qbvs.cache import cache_csv_ohlcv, cache_yahoo_ohlcv, refresh_cache_index
from qbvs.campaign import (
    CampaignConfig,
    PromotionConfig,
    build_long_run_campaign,
    promote_candidates_from_summary,
    verify_long_run_campaign,
)
from qbvs.data import fetch_yahoo_universe, load_csv, load_universe
from qbvs.datasources import (
    cache_alipay_fund_nav,
    cache_moomoo_history,
    probe_moomoo_opend,
    write_probe_report,
    write_tradable_universe_template,
)
from qbvs.fast import FastScreenConfig, benchmark_summary, compare_fast_to_exact, fast_summary, fast_validate_universe
from qbvs.finalists import FinalistSelectionConfig, build_finalist_cache_pair_manifest
from qbvs.fund_rules import (
    default_alipay_fund_rule,
    load_fund_rule,
    summarize_fund_results,
    validate_fund_universe,
    write_fund_rule_template,
)
from qbvs.goal_audit import GoalAuditConfig, audit_goal_readiness
from qbvs.handshake import create_handshake_bundle, verify_handshake_ack
from qbvs.moomoo_batch import MoomooBatchConfig, cache_moomoo_batch
from qbvs.planning import estimate_manifest_budget, sample_manifest_stratified, split_manifest
from qbvs.quality import assess_ohlcv_quality
from qbvs.quantlab_adapter import QuantLabAdapterPackConfig, build_quantlab_adapter_pack, verify_quantlab_adapter_pack
from qbvs.quantlab_bundle import QuantLabBundleConfig, export_quantlab_bundle, verify_quantlab_bundle
from qbvs.reporting import build_pdf_report
from qbvs.repository import index_runs
from qbvs.simulation import RandomPathConfig
from qbvs.strategies import generate_strategy_specs, specs_to_frame
from qbvs.symbol_aliases import normalize_moomoo_source_symbol
from qbvs.tasks import build_cache_pair_task_manifest, build_cache_task_manifest, build_csv_task_manifest, run_task_manifest
from qbvs.universe_seed import (
    build_seed_cache_plan,
    build_seed_universe,
    build_seed_yahoo_cache_plan,
    build_seed_yahoo_universe,
    sample_universe_stratified,
    validate_seed_universe,
)
from qbvs.validation import (
    ValidationConfig,
    stress_random,
    summarize_results,
    validate_event_universe,
    validate_rolling_universe,
    validate_universe,
    write_run_artifacts,
)
from qbvs.warehouse import export_warehouse_tables, import_runs_to_warehouse, init_warehouse, warehouse_stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent behavior-strategy validation system.")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list-strategies", help="List generated strategy families.")
    list_parser.add_argument("--limit", type=int, default=240)
    list_parser.add_argument("--output", type=Path)

    stress_parser = sub.add_parser("stress-random", help="Run Monte Carlo stress validation.")
    stress_parser.add_argument("--strategies", type=int, default=240)
    stress_parser.add_argument("--paths", type=int, default=1_000)
    stress_parser.add_argument("--days", type=int, default=252)
    stress_parser.add_argument("--seed", type=int, default=42)
    stress_parser.add_argument("--workers", type=int, default=1)
    stress_parser.add_argument("--chunk-size", type=int, default=20)
    stress_parser.add_argument("--output-dir", type=Path, default=Path("runs/random_smoke"))

    csv_parser = sub.add_parser("validate-csv", help="Validate strategies on local CSV data.")
    csv_parser.add_argument("--csv", type=Path, required=True)
    csv_parser.add_argument("--symbol", default="CSV")
    csv_parser.add_argument("--market", default="CSV")
    csv_parser.add_argument("--strategies", type=int, default=20)
    csv_parser.add_argument("--rolling-windows", action="store_true")
    csv_parser.add_argument("--window-days", default="252,504,756")
    csv_parser.add_argument("--step-days", type=int, default=63)
    csv_parser.add_argument("--event-windows", type=Path)
    csv_parser.add_argument("--output-dir", type=Path, default=Path("runs/csv_validation"))

    fast_csv_parser = sub.add_parser("fast-screen-csv", help="Run vectorized screening on local CSV data.")
    fast_csv_parser.add_argument("--csv", type=Path, required=True)
    fast_csv_parser.add_argument("--symbol", default="CSV")
    fast_csv_parser.add_argument("--market", default="CSV")
    fast_csv_parser.add_argument("--strategies", type=int, default=240)
    fast_csv_parser.add_argument("--output-dir", type=Path, default=Path("runs/fast_screen_csv"))

    fast_benchmark_parser = sub.add_parser("fast-benchmark-csv", help="Compare fast screening approximations against exact backtest metrics.")
    fast_benchmark_parser.add_argument("--csv", type=Path, required=True)
    fast_benchmark_parser.add_argument("--symbol", default="CSV")
    fast_benchmark_parser.add_argument("--market", default="CSV")
    fast_benchmark_parser.add_argument("--strategies", type=int, default=20)
    fast_benchmark_parser.add_argument("--output-dir", type=Path, default=Path("runs/fast_benchmark_csv"))

    yahoo_parser = sub.add_parser("validate-yahoo", help="Validate strategies on Yahoo chart data.")
    yahoo_parser.add_argument("--universe", type=Path, required=True)
    yahoo_parser.add_argument("--limit", type=int, default=10)
    yahoo_parser.add_argument("--strategies", type=int, default=20)
    yahoo_parser.add_argument("--rolling-windows", action="store_true")
    yahoo_parser.add_argument("--window-days", default="252,504,756")
    yahoo_parser.add_argument("--step-days", type=int, default=63)
    yahoo_parser.add_argument("--event-windows", type=Path)
    yahoo_parser.add_argument("--output-dir", type=Path, default=Path("runs/yahoo_validation"))
    yahoo_parser.add_argument("--allow-insecure-ssl", action="store_true", help="Use only when local Python CA certificates are broken.")

    manifest_parser = sub.add_parser("build-csv-manifest", help="Build a resumable task manifest from one local CSV.")
    manifest_parser.add_argument("--csv", type=Path, required=True)
    manifest_parser.add_argument("--symbol", default="CSV")
    manifest_parser.add_argument("--market", default="CSV")
    manifest_parser.add_argument("--strategies", type=int, default=20)
    manifest_parser.add_argument("--mode", choices=["full", "rolling"], default="rolling")
    manifest_parser.add_argument("--window-days", default="252,504,756")
    manifest_parser.add_argument("--step-days", type=int, default=63)
    manifest_parser.add_argument("--min-bars", type=int, default=120)
    manifest_parser.add_argument("--output", type=Path, required=True)

    run_manifest_parser = sub.add_parser("run-manifest", help="Run a task manifest with per-task JSON cache and resume.")
    run_manifest_parser.add_argument("--manifest", type=Path, required=True)
    run_manifest_parser.add_argument("--max-tasks", type=int)
    run_manifest_parser.add_argument("--no-resume", action="store_true")
    run_manifest_parser.add_argument("--run-dir", type=Path, help="Use an exact run directory so repeated commands resume the same cache.")
    run_manifest_parser.add_argument("--output-dir", type=Path, default=Path("runs/task_manifest_run"))
    run_manifest_parser.add_argument("--min-quality-score", type=float)
    run_manifest_parser.add_argument("--skip-low-quality", action="store_true")

    cache_csv_parser = sub.add_parser("cache-csv", help="Normalize one CSV into the reusable OHLCV cache.")
    cache_csv_parser.add_argument("--csv", type=Path, required=True)
    cache_csv_parser.add_argument("--symbol", required=True)
    cache_csv_parser.add_argument("--market", required=True)
    cache_csv_parser.add_argument("--source", default="csv")
    cache_csv_parser.add_argument("--cache-dir", type=Path, default=Path("data_cache"))
    cache_csv_parser.add_argument("--asset-class", default="")
    cache_csv_parser.add_argument("--tradability", default="")
    cache_csv_parser.add_argument("--currency", default="")
    cache_csv_parser.add_argument("--timezone", default="")

    cache_yahoo_parser = sub.add_parser("cache-yahoo", help="Fetch Yahoo data and write reusable OHLCV cache files.")
    cache_yahoo_parser.add_argument("--universe", type=Path, required=True)
    cache_yahoo_parser.add_argument("--limit", type=int)
    cache_yahoo_parser.add_argument("--cache-dir", type=Path, default=Path("data_cache"))
    cache_yahoo_parser.add_argument("--allow-insecure-ssl", action="store_true")

    probe_moomoo_parser = sub.add_parser("probe-moomoo-opend", help="Check whether Moomoo/OpenD and the local SDK are available.")
    probe_moomoo_parser.add_argument("--host", default="127.0.0.1")
    probe_moomoo_parser.add_argument("--port", type=int, default=11111)
    probe_moomoo_parser.add_argument("--timeout", type=float, default=2.0)
    probe_moomoo_parser.add_argument("--output", type=Path)

    moomoo_cache_parser = sub.add_parser("cache-moomoo-history", help="Fetch Moomoo/OpenD daily history into the standard OHLCV cache.")
    moomoo_cache_parser.add_argument("--symbol", required=True)
    moomoo_cache_parser.add_argument("--market", required=True)
    moomoo_cache_parser.add_argument("--start", required=True)
    moomoo_cache_parser.add_argument("--end", required=True)
    moomoo_cache_parser.add_argument("--host", default="127.0.0.1")
    moomoo_cache_parser.add_argument("--port", type=int, default=11111)
    moomoo_cache_parser.add_argument("--ktype", default="K_DAY")
    moomoo_cache_parser.add_argument("--autype", default="QFQ")
    moomoo_cache_parser.add_argument("--cache-dir", type=Path, default=Path("data_cache"))
    moomoo_cache_parser.add_argument("--asset-class", default="")
    moomoo_cache_parser.add_argument("--tradability", default="CONFIRMED_SOURCE_NEEDS_ACCOUNT_PERMISSION_CHECK")
    moomoo_cache_parser.add_argument("--currency", default="")
    moomoo_cache_parser.add_argument("--timezone", default="")

    moomoo_batch_parser = sub.add_parser("cache-moomoo-batch", help="Fetch a universe slice from Moomoo/OpenD into the standard OHLCV cache.")
    moomoo_batch_parser.add_argument("--universe", type=Path, required=True)
    moomoo_batch_parser.add_argument("--cache-dir", type=Path, required=True)
    moomoo_batch_parser.add_argument("--attempts-output", type=Path, required=True)
    moomoo_batch_parser.add_argument("--summary-output", type=Path, required=True)
    moomoo_batch_parser.add_argument("--start", required=True)
    moomoo_batch_parser.add_argument("--end", required=True)
    moomoo_batch_parser.add_argument("--offset", type=int, default=0)
    moomoo_batch_parser.add_argument("--limit", type=int)
    moomoo_batch_parser.add_argument("--host", default="127.0.0.1")
    moomoo_batch_parser.add_argument("--port", type=int, default=11111)
    moomoo_batch_parser.add_argument("--ktype", default="K_DAY")
    moomoo_batch_parser.add_argument("--autype", default="QFQ")

    alipay_nav_parser = sub.add_parser("cache-alipay-fund-nav", help="Normalize an Alipay fund NAV CSV into the standard OHLCV cache.")
    alipay_nav_parser.add_argument("--csv", type=Path, required=True)
    alipay_nav_parser.add_argument("--symbol", required=True)
    alipay_nav_parser.add_argument("--fund-name", default="")
    alipay_nav_parser.add_argument("--date-col", default="date")
    alipay_nav_parser.add_argument("--nav-col", default="nav")
    alipay_nav_parser.add_argument("--cache-dir", type=Path, default=Path("data_cache"))

    universe_template_parser = sub.add_parser("create-tradable-universe-template", help="Create a Moomoo/Alipay tradable universe CSV template.")
    universe_template_parser.add_argument("--kind", choices=["mixed", "moomoo", "alipay"], default="mixed")
    universe_template_parser.add_argument("--output", type=Path, required=True)

    seed_universe_parser = sub.add_parser("create-seed-universe", help="Create a 200+ symbol reviewable universe seed for Moomoo/Yahoo validation.")
    seed_universe_parser.add_argument("--output", type=Path, required=True)
    seed_universe_parser.add_argument("--limit", type=int, default=220)

    verify_seed_universe_parser = sub.add_parser("verify-seed-universe", help="Verify a universe seed CSV.")
    verify_seed_universe_parser.add_argument("--universe", type=Path, required=True)
    verify_seed_universe_parser.add_argument("--min-symbols", type=int, default=200)

    seed_cache_plan_parser = sub.add_parser("build-seed-cache-plan", help="Build explicit Moomoo/OpenD cache commands from a seed universe.")
    seed_cache_plan_parser.add_argument("--universe", type=Path, required=True)
    seed_cache_plan_parser.add_argument("--output-dir", type=Path, required=True)
    seed_cache_plan_parser.add_argument("--start", default="2000-01-01")
    seed_cache_plan_parser.add_argument("--end", default="2026-06-05")
    seed_cache_plan_parser.add_argument("--cache-dir", default="data_cache_seed")
    seed_cache_plan_parser.add_argument("--python-executable", default="python3")
    seed_cache_plan_parser.add_argument("--limit", type=int)

    seed_yahoo_universe_parser = sub.add_parser("build-seed-yahoo-universe", help="Build a Yahoo-readable public-data universe from the 200+ symbol seed.")
    seed_yahoo_universe_parser.add_argument("--universe", type=Path, required=True)
    seed_yahoo_universe_parser.add_argument("--output", type=Path, required=True)
    seed_yahoo_universe_parser.add_argument("--limit", type=int)

    seed_yahoo_cache_plan_parser = sub.add_parser("build-seed-yahoo-cache-plan", help="Build explicit Yahoo public-data cache command plan from a seed Yahoo universe.")
    seed_yahoo_cache_plan_parser.add_argument("--universe", type=Path, required=True)
    seed_yahoo_cache_plan_parser.add_argument("--output-dir", type=Path, required=True)
    seed_yahoo_cache_plan_parser.add_argument("--cache-dir", default="data_cache_seed_yahoo")
    seed_yahoo_cache_plan_parser.add_argument("--python-executable", default="python3")
    seed_yahoo_cache_plan_parser.add_argument("--limit", type=int)
    seed_yahoo_cache_plan_parser.add_argument("--allow-insecure-ssl", action="store_true")

    sample_universe_parser = sub.add_parser("sample-universe", help="Create a representative stratified subset from a universe CSV.")
    sample_universe_parser.add_argument("--universe", type=Path, required=True)
    sample_universe_parser.add_argument("--max-symbols", type=int, required=True)
    sample_universe_parser.add_argument("--output", type=Path, required=True)
    sample_universe_parser.add_argument("--seed", type=int, default=42)
    sample_universe_parser.add_argument("--group-cols", default="market,asset_class")

    fund_rule_parser = sub.add_parser("create-fund-rule-template", help="Create an Alipay fund trading-rule JSON template.")
    fund_rule_parser.add_argument("--output", type=Path, required=True)

    fund_validate_parser = sub.add_parser("validate-fund-csv", help="Validate strategies on a CSV using Alipay fund execution rules.")
    fund_validate_parser.add_argument("--csv", type=Path, required=True)
    fund_validate_parser.add_argument("--symbol", default="ALIPAY_FUND")
    fund_validate_parser.add_argument("--market", default="ALIPAY_FUND")
    fund_validate_parser.add_argument("--strategies", type=int, default=20)
    fund_validate_parser.add_argument("--rule", type=Path)
    fund_validate_parser.add_argument("--output-dir", type=Path, default=Path("runs/fund_validation"))

    cache_manifest_parser = sub.add_parser("build-cache-manifest", help="Build a resumable manifest from cache_index.csv.")
    cache_manifest_parser.add_argument("--cache-index", type=Path, required=True)
    cache_manifest_parser.add_argument("--strategies", type=int, default=20)
    cache_manifest_parser.add_argument("--mode", choices=["full", "rolling"], default="rolling")
    cache_manifest_parser.add_argument("--window-days", default="252,504,756")
    cache_manifest_parser.add_argument("--step-days", type=int, default=63)
    cache_manifest_parser.add_argument("--min-bars", type=int, default=120)
    cache_manifest_parser.add_argument("--max-symbols", type=int)
    cache_manifest_parser.add_argument("--output", type=Path, required=True)

    pair_manifest_parser = sub.add_parser("build-cache-pair-manifest", help="Build a scalable manifest with sampled windows for each symbol-strategy pair.")
    pair_manifest_parser.add_argument("--cache-index", type=Path, required=True)
    pair_manifest_parser.add_argument("--strategies", type=int, default=200)
    pair_manifest_parser.add_argument("--mode", choices=["full", "rolling"], default="rolling")
    pair_manifest_parser.add_argument("--window-days", default="252,504,756")
    pair_manifest_parser.add_argument("--step-days", type=int, default=126)
    pair_manifest_parser.add_argument("--min-bars", type=int, default=120)
    pair_manifest_parser.add_argument("--max-symbols", type=int)
    pair_manifest_parser.add_argument("--windows-per-pair", type=int, default=1)
    pair_manifest_parser.add_argument("--output", type=Path, required=True)

    finalist_manifest_parser = sub.add_parser("build-finalist-manifest", help="Build a deeper cache-pair manifest for finalist strategies selected from a summary CSV.")
    finalist_manifest_parser.add_argument("--summary", type=Path, required=True)
    finalist_manifest_parser.add_argument("--cache-index", type=Path, required=True)
    finalist_manifest_parser.add_argument("--output", type=Path, required=True)
    finalist_manifest_parser.add_argument("--top-n", type=int, default=20)
    finalist_manifest_parser.add_argument("--min-samples", type=int, default=150)
    finalist_manifest_parser.add_argument("--min-pass-rate", type=float, default=0.60)
    finalist_manifest_parser.add_argument("--min-avg-total-gap", type=float, default=-0.08)
    finalist_manifest_parser.add_argument("--min-avg-annualized-gap", type=float, default=-0.03)
    finalist_manifest_parser.add_argument("--min-avg-drawdown-improvement", type=float, default=-0.005)
    finalist_manifest_parser.add_argument("--mode", choices=["full", "rolling"], default="rolling")
    finalist_manifest_parser.add_argument("--window-days", default="252,504,756")
    finalist_manifest_parser.add_argument("--step-days", type=int, default=63)
    finalist_manifest_parser.add_argument("--min-bars", type=int, default=120)
    finalist_manifest_parser.add_argument("--max-symbols", type=int)
    finalist_manifest_parser.add_argument("--windows-per-pair", type=int, default=5)

    index_parser = sub.add_parser("index-runs", help="Aggregate validation run outputs across a runs directory.")
    index_parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    index_parser.add_argument("--output-dir", type=Path, default=Path("runs/index"))

    quality_parser = sub.add_parser("assess-csv-quality", help="Assess OHLCV data quality for one CSV.")
    quality_parser.add_argument("--csv", type=Path, required=True)
    quality_parser.add_argument("--symbol", default="CSV")
    quality_parser.add_argument("--market", default="CSV")
    quality_parser.add_argument("--output", type=Path)

    split_parser = sub.add_parser("split-manifest", help="Split a manifest into smaller chunk files.")
    split_parser.add_argument("--manifest", type=Path, required=True)
    split_parser.add_argument("--chunk-size", type=int, default=10000)
    split_parser.add_argument("--output-dir", type=Path, required=True)
    split_parser.add_argument("--prefix", default="manifest_part")

    sample_manifest_parser = sub.add_parser("sample-manifest", help="Create a representative stratified task subset from a manifest.")
    sample_manifest_parser.add_argument("--manifest", type=Path, required=True)
    sample_manifest_parser.add_argument("--max-tasks", type=int, required=True)
    sample_manifest_parser.add_argument("--output", type=Path, required=True)
    sample_manifest_parser.add_argument("--seed", type=int, default=42)
    sample_manifest_parser.add_argument("--group-cols", default="symbol,strategy_id")

    campaign_parser = sub.add_parser("build-campaign", help="Build a long-run validation campaign plan from a manifest.")
    campaign_parser.add_argument("--manifest", type=Path, required=True)
    campaign_parser.add_argument("--output-dir", type=Path, required=True)
    campaign_parser.add_argument("--chunk-size", type=int, default=10000)
    campaign_parser.add_argument("--workers", type=int, default=1)
    campaign_parser.add_argument("--seconds-per-task", type=float, default=0.05)
    campaign_parser.add_argument("--min-quality-score", type=float, default=70.0)
    campaign_parser.add_argument("--skip-low-quality", action="store_true")
    campaign_parser.add_argument("--million-test-multiplier", type=int, default=1)
    campaign_parser.add_argument("--target-symbols", type=int, default=200)
    campaign_parser.add_argument("--target-strategies", type=int, default=200)
    campaign_parser.add_argument("--target-tests-per-strategy", type=int, default=1_000_000)
    campaign_parser.add_argument("--python-executable", default="python3")

    verify_campaign_parser = sub.add_parser("verify-campaign", help="Verify a long-run validation campaign directory.")
    verify_campaign_parser.add_argument("--campaign-dir", type=Path, required=True)

    promote_parser = sub.add_parser("promote-candidates", help="Create a gated candidate list from a strategy summary CSV.")
    promote_parser.add_argument("--summary", type=Path, required=True)
    promote_parser.add_argument("--output", type=Path, required=True)
    promote_parser.add_argument("--top-n", type=int, default=20)
    promote_parser.add_argument("--min-samples", type=int, default=1)
    promote_parser.add_argument("--min-pass-rate", type=float, default=0.60)
    promote_parser.add_argument("--min-avg-total-gap", type=float, default=-0.08)
    promote_parser.add_argument("--min-avg-annualized-gap", type=float, default=-0.03)
    promote_parser.add_argument("--min-avg-drawdown-improvement", type=float, default=-0.005)

    budget_parser = sub.add_parser("estimate-budget", help="Estimate manifest runtime budget.")
    budget_parser.add_argument("--manifest", type=Path, required=True)
    budget_parser.add_argument("--seconds-per-task", type=float, default=0.05)
    budget_parser.add_argument("--workers", type=int, default=1)
    budget_parser.add_argument("--million-test-multiplier", type=int, default=1)
    budget_parser.add_argument("--output", type=Path)

    handshake_parser = sub.add_parser("create-handshake", help="Create a QuantLab interoperability handshake request and ack template.")
    handshake_parser.add_argument("--output-dir", type=Path, default=Path("handoff"))
    handshake_parser.add_argument("--quantlab-root", type=Path)

    verify_handshake_parser = sub.add_parser("verify-handshake", help="Verify a QuantLab handshake ack JSON file.")
    verify_handshake_parser.add_argument("--ack", type=Path, required=True)

    quantlab_bundle_parser = sub.add_parser("export-quantlab-bundle", help="Export a QuantLab-readable external evidence bundle from one run directory.")
    quantlab_bundle_parser.add_argument("--run-dir", type=Path, required=True)
    quantlab_bundle_parser.add_argument("--output-dir", type=Path, required=True)
    quantlab_bundle_parser.add_argument("--top-n", type=int, default=20)
    quantlab_bundle_parser.add_argument("--min-pass-rate", type=float, default=0.60)
    quantlab_bundle_parser.add_argument("--min-avg-total-gap", type=float, default=-0.08)
    quantlab_bundle_parser.add_argument("--min-avg-annualized-gap", type=float, default=-0.03)
    quantlab_bundle_parser.add_argument("--min-avg-drawdown-improvement", type=float, default=-0.005)

    verify_quantlab_bundle_parser = sub.add_parser("verify-quantlab-bundle", help="Verify a QuantLab-readable external evidence bundle.")
    verify_quantlab_bundle_parser.add_argument("--bundle-dir", type=Path, required=True)

    adapter_pack_parser = sub.add_parser("build-quantlab-adapter-pack", help="Build a read-only QBVS adapter pack for QuantLab-side consumption.")
    adapter_pack_parser.add_argument("--output-dir", type=Path, required=True)
    adapter_pack_parser.add_argument("--quantlab-root", default="")
    adapter_pack_parser.add_argument("--default-bundle-dir", default="")
    adapter_pack_parser.add_argument("--default-campaign-dir", default="")
    adapter_pack_parser.add_argument("--default-promotion-candidates", default="")

    verify_adapter_pack_parser = sub.add_parser("verify-quantlab-adapter-pack", help="Verify a read-only QBVS adapter pack.")
    verify_adapter_pack_parser.add_argument("--pack-dir", type=Path, required=True)

    warehouse_init_parser = sub.add_parser("warehouse-init", help="Initialize a SQLite result warehouse.")
    warehouse_init_parser.add_argument("--db", type=Path, default=Path("warehouse/qbvs_results.sqlite"))

    warehouse_import_parser = sub.add_parser("warehouse-import-runs", help="Import run CSV outputs into the SQLite warehouse.")
    warehouse_import_parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    warehouse_import_parser.add_argument("--db", type=Path, default=Path("warehouse/qbvs_results.sqlite"))

    warehouse_export_parser = sub.add_parser("warehouse-export", help="Export SQLite warehouse tables to CSV.")
    warehouse_export_parser.add_argument("--db", type=Path, default=Path("warehouse/qbvs_results.sqlite"))
    warehouse_export_parser.add_argument("--output-dir", type=Path, default=Path("warehouse/export"))

    warehouse_stats_parser = sub.add_parser("warehouse-stats", help="Print SQLite warehouse row counts.")
    warehouse_stats_parser.add_argument("--db", type=Path, default=Path("warehouse/qbvs_results.sqlite"))

    audit_goal_parser = sub.add_parser("audit-goal-readiness", help="Audit current evidence against the full user goal.")
    audit_goal_parser.add_argument("--summary", type=Path, required=True)
    audit_goal_parser.add_argument("--results", type=Path, required=True)
    audit_goal_parser.add_argument("--manifest", type=Path)
    audit_goal_parser.add_argument("--moomoo-probe", type=Path)
    audit_goal_parser.add_argument("--handshake-ack", type=Path)
    audit_goal_parser.add_argument("--output-dir", type=Path, required=True)
    audit_goal_parser.add_argument("--target-symbols", type=int, default=200)
    audit_goal_parser.add_argument("--target-strategies", type=int, default=200)
    audit_goal_parser.add_argument("--target-tests-per-strategy", type=int, default=1_000_000)
    audit_goal_parser.add_argument("--min-avg-total-gap", type=float, default=-0.08)
    audit_goal_parser.add_argument("--min-avg-annualized-gap", type=float, default=-0.03)
    audit_goal_parser.add_argument("--min-avg-drawdown-improvement", type=float, default=-0.005)

    args = parser.parse_args()
    if args.command == "list-strategies":
        frame = specs_to_frame(generate_strategy_specs(args.limit))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(args.output, index=False)
        else:
            print(frame.to_string(index=False))
        return 0
    if args.command == "stress-random":
        specs = generate_strategy_specs(args.strategies)
        config = ValidationConfig()
        random_config = RandomPathConfig(paths=args.paths, days=args.days, seed=args.seed)
        if args.workers > 1:
            results = stress_random_parallel(specs, random_config, config, workers=args.workers, chunk_size=args.chunk_size)
        else:
            results = stress_random(specs, random_config, config)
        summary = summarize_results(results)
        run_dir = _run_dir(args.output_dir)
        write_run_artifacts(run_dir, results, summary, config)
        build_pdf_report(
            run_dir / "Behavior_Strategy_Validation_Report.pdf",
            "Behavior Strategy Random Stress Validation",
            summary,
            [
                f"Strategy families: {len(specs)}; random paths: {args.paths}; days per path: {args.days}.",
                f"Workers: {args.workers}; chunk size: {args.chunk_size}.",
                "User floor: total return gap >= -8%, annualized gap >= -3%, drawdown improvement not materially worse than buy-and-hold.",
            ],
        )
        print(run_dir)
        return 0
    if args.command == "validate-csv":
        specs = generate_strategy_specs(args.strategies)
        frame = load_csv(args.csv, args.symbol, args.market)
        config = ValidationConfig()
        results = _validate_with_window_options({args.symbol: frame}, specs, config, args)
        summary = summarize_results(results)
        run_dir = _run_dir(args.output_dir)
        write_run_artifacts(run_dir, results, summary, config)
        build_pdf_report(run_dir / "Behavior_Strategy_Validation_Report.pdf", "Behavior Strategy CSV Validation", summary)
        print(run_dir)
        return 0
    if args.command == "fast-screen-csv":
        specs = generate_strategy_specs(args.strategies)
        frame = load_csv(args.csv, args.symbol, args.market)
        config = FastScreenConfig()
        results = fast_validate_universe({args.symbol: frame}, specs, config)
        summary = fast_summary(results)
        run_dir = _run_dir(args.output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        results.to_csv(run_dir / "fast_validation_results.csv", index=False)
        summary.to_csv(run_dir / "fast_strategy_summary.csv", index=False)
        pd.Series(
            {
                "engine": "fast_screen",
                "warning": "screening only; finalists must be rerun with exact backtest engine",
                **config.__dict__,
            }
        ).to_json(run_dir / "fast_screen_config.json", force_ascii=False, indent=2)
        build_pdf_report(
            run_dir / "Behavior_Strategy_Fast_Screen_Report.pdf",
            "Behavior Strategy Fast Screening",
            summary,
            [
                f"Strategy families: {len(specs)}; symbol: {args.symbol}; market: {args.market}.",
                "Fast screening uses vectorized target-weight approximations for candidate ranking.",
                "Final strategy approval must rerun candidates through the exact backtest engine.",
            ],
        )
        print(run_dir)
        return 0
    if args.command == "fast-benchmark-csv":
        specs = generate_strategy_specs(args.strategies)
        frame = load_csv(args.csv, args.symbol, args.market)
        comparison = compare_fast_to_exact(frame, specs, FastScreenConfig())
        summary = benchmark_summary(comparison)
        run_dir = _run_dir(args.output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        comparison.to_csv(run_dir / "fast_exact_comparison.csv", index=False)
        summary.to_csv(run_dir / "fast_exact_summary.csv", index=False)
        build_pdf_report(
            run_dir / "Behavior_Strategy_Fast_Exact_Benchmark_Report.pdf",
            "Fast Screening vs Exact Backtest Benchmark",
            summary,
            [
                f"Compared strategies: {len(specs)}; symbol: {args.symbol}; market: {args.market}.",
                "Use this report to decide whether fast screening is accurate enough for candidate narrowing on this dataset.",
                "A low error does not replace final exact validation; it only supports using fast screening before exact reruns.",
            ],
        )
        print(run_dir)
        return 0
    if args.command == "validate-yahoo":
        specs = generate_strategy_specs(args.strategies)
        universe = load_universe(args.universe)
        fetch_errors: list[dict[str, str]] = []
        data = fetch_yahoo_universe(
            universe,
            limit=args.limit,
            allow_insecure_ssl=args.allow_insecure_ssl,
            errors=fetch_errors,
        )
        if not data:
            run_dir = _run_dir(args.output_dir)
            run_dir.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(fetch_errors).to_csv(run_dir / "data_fetch_errors.csv", index=False)
            raise SystemExit(f"No Yahoo data fetched. Errors saved to {run_dir / 'data_fetch_errors.csv'}")
        config = ValidationConfig()
        results = _validate_with_window_options(data, specs, config, args)
        summary = summarize_results(results)
        run_dir = _run_dir(args.output_dir)
        write_run_artifacts(run_dir, results, summary, config)
        if fetch_errors:
            pd.DataFrame(fetch_errors).to_csv(run_dir / "data_fetch_errors.csv", index=False)
        build_pdf_report(run_dir / "Behavior_Strategy_Validation_Report.pdf", "Behavior Strategy Yahoo Validation", summary)
        print(run_dir)
        return 0
    if args.command == "build-csv-manifest":
        specs = generate_strategy_specs(args.strategies)
        lengths = [int(part.strip()) for part in args.window_days.split(",") if part.strip()]
        manifest = build_csv_task_manifest(
            args.csv,
            args.symbol,
            args.market,
            specs,
            mode=args.mode,
            window_lengths=lengths,
            step=args.step_days,
            min_bars=args.min_bars,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(args.output, index=False)
        print(args.output)
        return 0
    if args.command == "run-manifest":
        config = ValidationConfig()
        run_dir = args.run_dir if args.run_dir else _run_dir(args.output_dir)
        status, results, summary = run_task_manifest(
            args.manifest,
            run_dir,
            config=config,
            max_tasks=args.max_tasks,
            resume=not args.no_resume,
            min_quality_score=args.min_quality_score,
            skip_low_quality=args.skip_low_quality,
        )
        build_pdf_report(
            run_dir / "Behavior_Strategy_Task_Run_Report.pdf",
            "Behavior Strategy Resumable Task Validation",
            summary,
            [
                f"Manifest: {args.manifest}",
                f"Tasks attempted: {len(status)}; cached: {(status['status'] == 'cached').sum() if not status.empty else 0}; completed: {(status['status'] == 'completed').sum() if not status.empty else 0}; failed: {(status['status'] == 'failed').sum() if not status.empty else 0}.",
                f"Quality skipped: {(status['status'] == 'skipped_quality').sum() if not status.empty else 0}; min quality score: {args.min_quality_score if args.min_quality_score is not None else 'not set'}.",
                f"Aggregated result rows: {len(results)}.",
            ],
        )
        print(run_dir)
        return 0
    if args.command == "cache-csv":
        row = cache_csv_ohlcv(
            args.csv,
            args.cache_dir,
            args.symbol,
            args.market,
            source=args.source,
            asset_class=args.asset_class,
            tradability=args.tradability,
            currency=args.currency,
            timezone=args.timezone,
        )
        print(row["cache_path"])
        return 0
    if args.command == "cache-yahoo":
        index, errors = cache_yahoo_ohlcv(
            args.universe,
            args.cache_dir,
            limit=args.limit,
            allow_insecure_ssl=args.allow_insecure_ssl,
        )
        args.cache_dir.mkdir(parents=True, exist_ok=True)
        if not errors.empty:
            errors.to_csv(args.cache_dir / "cache_errors.csv", index=False)
        refresh_cache_index(args.cache_dir)
        print(args.cache_dir / "cache_index.csv")
        return 0
    if args.command == "probe-moomoo-opend":
        result = probe_moomoo_opend(host=args.host, port=args.port, timeout=args.timeout)
        output = pd.Series(result.to_dict()).to_json(force_ascii=False, indent=2)
        if args.output:
            write_probe_report(result, args.output)
            print(args.output)
        else:
            print(output)
        return 0 if result.ready_for_fetch else 2
    if args.command == "cache-moomoo-history":
        alias = normalize_moomoo_source_symbol(symbol=args.symbol, market=args.market, source_symbol=args.symbol)
        row = cache_moomoo_history(
            symbol=alias.normalized_source_symbol,
            market=args.market,
            cache_dir=args.cache_dir,
            start=args.start,
            end=args.end,
            host=args.host,
            port=args.port,
            ktype=args.ktype,
            autype=args.autype,
            asset_class=args.asset_class,
            tradability=args.tradability,
            currency=args.currency,
            timezone=args.timezone,
        )
        print(row["cache_path"])
        return 0
    if args.command == "cache-moomoo-batch":
        paths = cache_moomoo_batch(
            MoomooBatchConfig(
                universe=args.universe,
                cache_dir=args.cache_dir,
                attempts_output=args.attempts_output,
                summary_output=args.summary_output,
                start=args.start,
                end=args.end,
                offset=args.offset,
                limit=args.limit,
                host=args.host,
                port=args.port,
                ktype=args.ktype,
                autype=args.autype,
            )
        )
        for path in paths.values():
            print(path)
        return 0
    if args.command == "cache-alipay-fund-nav":
        row = cache_alipay_fund_nav(
            args.csv,
            args.cache_dir,
            symbol=args.symbol,
            fund_name=args.fund_name,
            date_col=args.date_col,
            nav_col=args.nav_col,
        )
        print(row["cache_path"])
        return 0
    if args.command == "create-tradable-universe-template":
        path = write_tradable_universe_template(args.output, kind=args.kind)
        print(path)
        return 0
    if args.command == "create-seed-universe":
        path, summary_path = build_seed_universe(args.output, limit=args.limit)
        print(path)
        print(summary_path)
        return 0
    if args.command == "verify-seed-universe":
        result = validate_seed_universe(args.universe, min_symbols=args.min_symbols)
        print(pd.Series({"valid": result["valid"], "errors": json_dumps(result["errors"]), "warnings": json_dumps(result["warnings"]), "symbols": result["symbols"]}).to_json(force_ascii=False, indent=2))
        return 0 if result["valid"] else 2
    if args.command == "build-seed-cache-plan":
        paths = build_seed_cache_plan(
            args.universe,
            args.output_dir,
            start=args.start,
            end=args.end,
            cache_dir=args.cache_dir,
            python_executable=args.python_executable,
            limit=args.limit,
        )
        for path in paths.values():
            print(path)
        return 0
    if args.command == "build-seed-yahoo-universe":
        path, summary_path = build_seed_yahoo_universe(args.universe, args.output, limit=args.limit)
        print(path)
        print(summary_path)
        return 0
    if args.command == "build-seed-yahoo-cache-plan":
        paths = build_seed_yahoo_cache_plan(
            args.universe,
            args.output_dir,
            cache_dir=args.cache_dir,
            python_executable=args.python_executable,
            limit=args.limit,
            allow_insecure_ssl=args.allow_insecure_ssl,
        )
        for path in paths.values():
            print(path)
        return 0
    if args.command == "sample-universe":
        group_cols = tuple(part.strip() for part in args.group_cols.split(",") if part.strip())
        path, summary_path = sample_universe_stratified(args.universe, args.output, max_symbols=args.max_symbols, seed=args.seed, group_cols=group_cols)
        print(path)
        print(summary_path)
        return 0
    if args.command == "create-fund-rule-template":
        path = write_fund_rule_template(args.output)
        print(path)
        return 0
    if args.command == "validate-fund-csv":
        specs = generate_strategy_specs(args.strategies)
        frame = load_csv(args.csv, args.symbol, args.market)
        rule = load_fund_rule(args.rule) if args.rule else default_alipay_fund_rule()
        results = validate_fund_universe({args.symbol: frame}, specs, rule)
        summary = summarize_fund_results(results)
        run_dir = _run_dir(args.output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        results.to_csv(run_dir / "fund_validation_results.csv", index=False)
        summary.to_csv(run_dir / "fund_strategy_summary.csv", index=False)
        pd.Series(rule.to_dict()).to_json(run_dir / "fund_trading_rule.json", force_ascii=False, indent=2)
        build_pdf_report(
            run_dir / "Alipay_Fund_Strategy_Validation_Report.pdf",
            "Alipay Fund Behavior Strategy Validation",
            summary,
            [
                f"Strategy families: {len(specs)}; symbol: {args.symbol}; market: {args.market}.",
                "Execution model includes subscription fee, redemption fee, buy confirmation delay, sell cash delay, and minimum holding constraints.",
                "This fund execution mode is separate from stock/ETF instant target-weight backtesting.",
            ],
        )
        print(run_dir)
        return 0
    if args.command == "build-cache-manifest":
        specs = generate_strategy_specs(args.strategies)
        lengths = [int(part.strip()) for part in args.window_days.split(",") if part.strip()]
        manifest = build_cache_task_manifest(
            args.cache_index,
            specs,
            mode=args.mode,
            window_lengths=lengths,
            step=args.step_days,
            min_bars=args.min_bars,
            max_symbols=args.max_symbols,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(args.output, index=False)
        print(args.output)
        return 0
    if args.command == "build-cache-pair-manifest":
        specs = generate_strategy_specs(args.strategies)
        lengths = [int(part.strip()) for part in args.window_days.split(",") if part.strip()]
        manifest = build_cache_pair_task_manifest(
            args.cache_index,
            specs,
            mode=args.mode,
            window_lengths=lengths,
            step=args.step_days,
            min_bars=args.min_bars,
            max_symbols=args.max_symbols,
            windows_per_pair=args.windows_per_pair,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(args.output, index=False)
        pd.Series(
            {
                "rows": len(manifest),
                "symbols": int(manifest["symbol"].nunique()) if not manifest.empty else 0,
                "strategies": int(manifest["strategy_id"].nunique()) if not manifest.empty else 0,
                "windows_per_pair": args.windows_per_pair,
                "mode": args.mode,
            }
        ).to_json(args.output.with_suffix(".summary.json"), force_ascii=False, indent=2)
        print(args.output)
        return 0
    if args.command == "build-finalist-manifest":
        selection_config = FinalistSelectionConfig(
            top_n=args.top_n,
            min_samples=args.min_samples,
            min_pass_rate=args.min_pass_rate,
            min_avg_total_gap=args.min_avg_total_gap,
            min_avg_annualized_gap=args.min_avg_annualized_gap,
            min_avg_drawdown_improvement=args.min_avg_drawdown_improvement,
        )
        lengths = tuple(int(part.strip()) for part in args.window_days.split(",") if part.strip())
        manifest, finalists_path, summary_path = build_finalist_cache_pair_manifest(
            args.summary,
            args.cache_index,
            args.output,
            selection_config=selection_config,
            mode=args.mode,
            window_lengths=lengths,
            step=args.step_days,
            min_bars=args.min_bars,
            max_symbols=args.max_symbols,
            windows_per_pair=args.windows_per_pair,
        )
        print(args.output)
        print(finalists_path)
        print(summary_path)
        print(f"rows={len(manifest)}")
        return 0
    if args.command == "index-runs":
        run_index, all_results, market_summary = index_runs(args.runs_dir, args.output_dir)
        build_pdf_report(
            args.output_dir / "Behavior_Strategy_Run_Index_Report.pdf",
            "Behavior Strategy Run Repository Index",
            market_summary.rename(columns={"market": "strategy_market"}) if not market_summary.empty else market_summary,
            [
                f"Runs indexed: {len(run_index)}.",
                f"Validation result rows: {len(all_results)}.",
                "Use strategy_market_summary.csv for cross-run market-level ranking.",
            ],
        )
        print(args.output_dir)
        return 0
    if args.command == "assess-csv-quality":
        frame = load_csv(args.csv, args.symbol, args.market)
        report = assess_ohlcv_quality(frame, symbol=args.symbol, market=args.market).to_dict()
        output = pd.Series(report).to_json(force_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
            print(args.output)
        else:
            print(output)
        return 0
    if args.command == "split-manifest":
        manifest = pd.read_csv(args.manifest)
        index = split_manifest(manifest, args.output_dir, chunk_size=args.chunk_size, prefix=args.prefix)
        print(args.output_dir / f"{args.prefix}_index.csv")
        print(f"parts={len(index)}")
        return 0
    if args.command == "sample-manifest":
        manifest = pd.read_csv(args.manifest)
        group_cols = tuple(part.strip() for part in args.group_cols.split(",") if part.strip())
        sampled = sample_manifest_stratified(manifest, max_tasks=args.max_tasks, output=args.output, seed=args.seed, group_cols=group_cols)
        print(args.output)
        print(f"rows={len(sampled)}")
        return 0
    if args.command == "build-campaign":
        config = CampaignConfig(
            chunk_size=args.chunk_size,
            workers=args.workers,
            seconds_per_task=args.seconds_per_task,
            min_quality_score=args.min_quality_score,
            skip_low_quality=args.skip_low_quality,
            million_test_multiplier=args.million_test_multiplier,
            target_symbols=args.target_symbols,
            target_strategies=args.target_strategies,
            target_tests_per_strategy=args.target_tests_per_strategy,
            python_executable=args.python_executable,
        )
        paths = build_long_run_campaign(args.manifest, args.output_dir, config)
        for path in paths.values():
            print(path)
        return 0
    if args.command == "verify-campaign":
        result = verify_long_run_campaign(args.campaign_dir)
        print(pd.Series({"valid": result["valid"], "errors": json_dumps(result["errors"]), "warnings": json_dumps(result["warnings"])}).to_json(force_ascii=False, indent=2))
        return 0 if result["valid"] else 2
    if args.command == "promote-candidates":
        config = PromotionConfig(
            top_n=args.top_n,
            min_samples=args.min_samples,
            min_pass_rate=args.min_pass_rate,
            min_avg_total_gap=args.min_avg_total_gap,
            min_avg_annualized_gap=args.min_avg_annualized_gap,
            min_avg_drawdown_improvement=args.min_avg_drawdown_improvement,
        )
        frame = promote_candidates_from_summary(args.summary, args.output, config)
        print(args.output)
        print(f"rows={len(frame)}")
        return 0
    if args.command == "estimate-budget":
        manifest = pd.read_csv(args.manifest)
        budget = estimate_manifest_budget(
            manifest,
            seconds_per_task=args.seconds_per_task,
            workers=args.workers,
            million_test_multiplier=args.million_test_multiplier,
        )
        output = pd.Series(budget).to_json(force_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
            print(args.output)
        else:
            print(output)
        return 0
    if args.command == "create-handshake":
        paths = create_handshake_bundle(args.output_dir, quantlab_root=args.quantlab_root)
        print(paths["request"])
        print(paths["ack_template"])
        return 0
    if args.command == "verify-handshake":
        result = verify_handshake_ack(args.ack)
        print(pd.Series({"valid": result["valid"], "errors": json_dumps(result["errors"])}).to_json(force_ascii=False, indent=2))
        return 0 if result["valid"] else 2
    if args.command == "export-quantlab-bundle":
        config = QuantLabBundleConfig(
            top_n=args.top_n,
            min_pass_rate=args.min_pass_rate,
            min_avg_total_gap=args.min_avg_total_gap,
            min_avg_annualized_gap=args.min_avg_annualized_gap,
            min_avg_drawdown_improvement=args.min_avg_drawdown_improvement,
        )
        paths = export_quantlab_bundle(args.run_dir, args.output_dir, config)
        for path in paths.values():
            print(path)
        return 0
    if args.command == "verify-quantlab-bundle":
        result = verify_quantlab_bundle(args.bundle_dir)
        print(pd.Series({"valid": result["valid"], "errors": json_dumps(result["errors"]), "warnings": json_dumps(result["warnings"])}).to_json(force_ascii=False, indent=2))
        return 0 if result["valid"] else 2
    if args.command == "build-quantlab-adapter-pack":
        config = QuantLabAdapterPackConfig(
            quantlab_root=args.quantlab_root,
            default_bundle_dir=args.default_bundle_dir,
            default_campaign_dir=args.default_campaign_dir,
            default_promotion_candidates=args.default_promotion_candidates,
        )
        paths = build_quantlab_adapter_pack(args.output_dir, config)
        for path in paths.values():
            print(path)
        return 0
    if args.command == "verify-quantlab-adapter-pack":
        result = verify_quantlab_adapter_pack(args.pack_dir)
        print(pd.Series({"valid": result["valid"], "errors": json_dumps(result["errors"]), "warnings": json_dumps(result["warnings"])}).to_json(force_ascii=False, indent=2))
        return 0 if result["valid"] else 2
    if args.command == "warehouse-init":
        path = init_warehouse(args.db)
        print(path)
        return 0
    if args.command == "warehouse-import-runs":
        stats = import_runs_to_warehouse(args.runs_dir, args.db)
        print(pd.Series(stats).to_json(force_ascii=False, indent=2))
        return 0
    if args.command == "warehouse-export":
        paths = export_warehouse_tables(args.db, args.output_dir)
        for path in paths.values():
            print(path)
        return 0
    if args.command == "warehouse-stats":
        stats = warehouse_stats(args.db)
        print(pd.Series(stats).to_json(force_ascii=False, indent=2))
        return 0
    if args.command == "audit-goal-readiness":
        config = GoalAuditConfig(
            target_symbols=args.target_symbols,
            target_strategies=args.target_strategies,
            target_tests_per_strategy=args.target_tests_per_strategy,
            min_avg_total_gap=args.min_avg_total_gap,
            min_avg_annualized_gap=args.min_avg_annualized_gap,
            min_avg_drawdown_improvement=args.min_avg_drawdown_improvement,
        )
        paths = audit_goal_readiness(
            args.output_dir,
            summary_path=args.summary,
            results_path=args.results,
            manifest_path=args.manifest,
            moomoo_probe_path=args.moomoo_probe,
            handshake_ack_path=args.handshake_ack,
            config=config,
        )
        for path in paths.values():
            print(path)
        return 0
    return 1


def _run_dir(base: Path) -> Path:
    return base / datetime.now().strftime("%Y%m%d_%H%M%S")


def _validate_with_window_options(data: dict[str, pd.DataFrame], specs, config: ValidationConfig, args) -> pd.DataFrame:
    if args.event_windows:
        return validate_event_universe(data, specs, args.event_windows, config=config)
    if args.rolling_windows:
        lengths = [int(part.strip()) for part in args.window_days.split(",") if part.strip()]
        return validate_rolling_universe(data, specs, lengths=lengths, step=args.step_days, config=config)
    return validate_universe(data, specs, config)


def json_dumps(value) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


if __name__ == "__main__":
    raise SystemExit(main())
