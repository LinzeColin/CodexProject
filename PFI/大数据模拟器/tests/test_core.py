from __future__ import annotations

from tempfile import TemporaryDirectory

import json
import pandas as pd

from qbvs.backtest import run_buy_hold, run_target_weight_backtest
from qbvs.batch import stress_random_parallel
from qbvs.cache import cache_csv_ohlcv, cache_yahoo_ohlcv, refresh_cache_index
from qbvs.campaign import (
    CampaignConfig,
    PromotionConfig,
    build_long_run_campaign,
    promote_candidates_from_summary,
    verify_long_run_campaign,
)
from qbvs.datasources import cache_alipay_fund_nav, probe_moomoo_opend, write_tradable_universe_template
from qbvs.fast import FastScreenConfig, compare_fast_to_exact, fast_summary, fast_validate_one, fast_validate_universe
from qbvs.finalists import FinalistSelectionConfig, build_finalist_cache_pair_manifest, select_finalist_strategy_ids
from qbvs.fund_rules import (
    FundTradingRule,
    load_fund_rule,
    run_fund_buy_hold,
    run_fund_target_weight_backtest,
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
from qbvs.repository import index_runs
from qbvs.simulation import RandomPathConfig, generate_random_paths
from qbvs.strategies import BehaviorStrategySpec, generate_signals, generate_strategy_specs
from qbvs.symbol_aliases import normalize_moomoo_source_symbol
from qbvs.tasks import build_cache_pair_task_manifest, build_cache_task_manifest, build_csv_task_manifest, quality_gate_decision, run_task_manifest
from qbvs.universe_seed import (
    build_seed_cache_plan,
    build_seed_universe,
    build_seed_yahoo_cache_plan,
    build_seed_yahoo_universe,
    sample_universe_stratified,
    validate_seed_universe,
)
from qbvs.validation import stress_random, summarize_results, validate_rolling_universe
from qbvs.warehouse import export_warehouse_tables, import_runs_to_warehouse, warehouse_stats
from qbvs.windows import rolling_windows


def _write_frame_csv(frame: pd.DataFrame, root: str, symbol: str) -> str:
    path = f"{root}/{symbol.replace('.', '_')}.csv"
    frame.to_csv(path, index=False)
    return path


def test_strategy_factory_has_at_least_200_specs():
    assert len(generate_strategy_specs(240)) >= 200


def test_backtest_runs_on_random_path():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=120, seed=1))[0]
    spec = BehaviorStrategySpec("test", 0.99, "boll_lower", "none", "strong_trend_full", "none")
    signals = generate_signals(frame, spec)
    result = run_target_weight_backtest(frame, signals)
    benchmark = run_buy_hold(frame)
    assert result["metrics"]["trade_count"] > 0
    assert pd.notna(result["metrics"]["total_return"])
    assert pd.notna(benchmark["metrics"]["total_return"])


def test_random_stress_summary_contains_user_floor_metric():
    specs = generate_strategy_specs(3)
    results = stress_random(specs, RandomPathConfig(paths=3, days=90, seed=2))
    summary = summarize_results(results)
    assert "pass_rate" in summary.columns
    assert "avg_annualized_gap" in summary.columns


def test_rolling_windows_and_parallel_batch_smoke():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=3))[0]
    windows = rolling_windows(frame, lengths=[120], step=60, min_bars=90)
    assert windows
    specs = generate_strategy_specs(2)
    rolling_results = validate_rolling_universe({"SIM": frame}, specs, lengths=[120], step=60, min_bars=90)
    assert "window_label" in rolling_results.columns
    parallel_results = stress_random_parallel(specs, RandomPathConfig(paths=2, days=90, seed=4), workers=1)
    assert len(parallel_results) == 4


def test_resumable_task_manifest_smoke():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=5))[0]
    with TemporaryDirectory() as tmp:
        csv_path = f"{tmp}/sample.csv"
        manifest_path = f"{tmp}/manifest.csv"
        run_dir = f"{tmp}/run"
        frame.to_csv(csv_path, index=False)
        specs = generate_strategy_specs(2)
        manifest = build_csv_task_manifest(
            csv_path,
            "SIMTASK",
            "SIM",
            specs,
            mode="rolling",
            window_lengths=[120],
            step=90,
            min_bars=90,
        )
        manifest.to_csv(manifest_path, index=False)
        assert len(manifest) > 0
        status, results, summary = run_task_manifest(manifest_path, run_dir, max_tasks=2)
        assert set(status["status"]) == {"completed"}
        assert len(results) == 2
        assert not summary.empty
        status2, results2, _ = run_task_manifest(manifest_path, run_dir, max_tasks=2)
        assert set(status2["status"]) == {"cached"}
        assert len(results2) == 2


def test_cache_manifest_and_run_index_smoke():
    _, frame_a = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=6))[0]
    _, frame_b = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=7))[0]
    with TemporaryDirectory() as tmp:
        csv_a = f"{tmp}/a.csv"
        csv_b = f"{tmp}/b.csv"
        cache_dir = f"{tmp}/cache"
        manifest_path = f"{tmp}/cache_manifest.csv"
        run_dir = f"{tmp}/run"
        index_dir = f"{tmp}/index"
        frame_a.to_csv(csv_a, index=False)
        frame_b.to_csv(csv_b, index=False)
        cache_csv_ohlcv(csv_a, cache_dir, "SIMA", "SIM", source="unit")
        cache_csv_ohlcv(csv_b, cache_dir, "SIMB", "SIM", source="unit", asset_class="ETF", tradability="TESTABLE")
        index = refresh_cache_index(cache_dir)
        assert len(index) == 2
        assert "quality_score" in index.columns
        assert "asset_class" in index.columns
        specs = generate_strategy_specs(2)
        manifest = build_cache_task_manifest(
            f"{cache_dir}/cache_index.csv",
            specs,
            mode="rolling",
            window_lengths=[120],
            step=90,
            min_bars=90,
        )
        manifest.to_csv(manifest_path, index=False)
        assert set(manifest["symbol"]) == {"SIMA", "SIMB"}
        assert manifest["quality_score"].notna().all()
        assert manifest["asset_class"].notna().all()
        run_task_manifest(manifest_path, run_dir, max_tasks=4)
        run_index, all_results, market_summary = index_runs(tmp, index_dir)
        assert not run_index.empty
        assert len(all_results) == 4
        assert not market_summary.empty


def test_cache_pair_manifest_samples_each_symbol_strategy_pair():
    _, frame_a = generate_random_paths(RandomPathConfig(paths=1, days=220, seed=19))[0]
    _, frame_b = generate_random_paths(RandomPathConfig(paths=1, days=220, seed=20))[0]
    with TemporaryDirectory() as tmp:
        csv_a = f"{tmp}/a.csv"
        csv_b = f"{tmp}/b.csv"
        cache_dir = f"{tmp}/cache"
        frame_a.to_csv(csv_a, index=False)
        frame_b.to_csv(csv_b, index=False)
        cache_csv_ohlcv(csv_a, cache_dir, "PAIR_A", "SIM", source="unit")
        cache_csv_ohlcv(csv_b, cache_dir, "PAIR_B", "SIM", source="unit")
        manifest = build_cache_pair_task_manifest(
            f"{cache_dir}/cache_index.csv",
            generate_strategy_specs(3),
            mode="rolling",
            window_lengths=[120],
            step=40,
            min_bars=90,
            windows_per_pair=2,
        )
        assert len(manifest) == 2 * 3 * 2
        assert manifest["symbol"].nunique() == 2
        assert manifest["strategy_id"].nunique() == 3
        assert manifest["quality_score"].notna().all()


def test_cache_yahoo_preserves_universe_metadata(monkeypatch):
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=15))[0]
    with TemporaryDirectory() as tmp:
        universe_path = f"{tmp}/universe.csv"
        cache_dir = f"{tmp}/cache"
        pd.DataFrame(
            [
                {
                    "symbol": "METAETF",
                    "market": "US_ETF",
                    "asset_class": "ETF",
                    "tradability": "PUBLIC_HISTORY_ONLY",
                    "currency": "USD",
                    "timezone": "America/New_York",
                }
            ]
        ).to_csv(universe_path, index=False)

        def fake_fetch(rows, limit=None, allow_insecure_ssl=False, errors=None):
            return {"METAETF": frame}

        monkeypatch.setattr("qbvs.cache.fetch_yahoo_universe", fake_fetch)
        index, errors = cache_yahoo_ohlcv(universe_path, cache_dir)
        assert errors.empty
        assert index.loc[0, "asset_class"] == "ETF"
        assert index.loc[0, "tradability"] == "PUBLIC_HISTORY_ONLY"
        cached = pd.read_csv(f"{cache_dir}/cache_index.csv")
        assert cached.loc[0, "currency"] == "USD"
        assert cached.loc[0, "timezone"] == "America/New_York"


def test_quality_budget_and_manifest_split_smoke():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=8))[0]
    report = assess_ohlcv_quality(frame)
    assert report.quality_score > 0
    with TemporaryDirectory() as tmp:
        csv_path = f"{tmp}/sample.csv"
        manifest_path = f"{tmp}/manifest.csv"
        split_dir = f"{tmp}/splits"
        frame.to_csv(csv_path, index=False)
        manifest = build_csv_task_manifest(
            csv_path,
            "SIMSPLIT",
            "SIM",
            generate_strategy_specs(3),
            mode="rolling",
            window_lengths=[120],
            step=90,
            min_bars=90,
        )
        manifest.to_csv(manifest_path, index=False)
        budget = estimate_manifest_budget(manifest, seconds_per_task=0.1, workers=2)
        assert budget["tasks"] == len(manifest)
        assert budget["estimated_wall_seconds"] > 0
        index = split_manifest(manifest, split_dir, chunk_size=2)
        assert len(index) >= 1


def test_stratified_manifest_sample_covers_symbols_and_strategies():
    _, frame_a = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=16))[0]
    _, frame_b = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=17))[0]
    with TemporaryDirectory() as tmp:
        csv_a = f"{tmp}/a.csv"
        csv_b = f"{tmp}/b.csv"
        cache_dir = f"{tmp}/cache"
        frame_a.to_csv(csv_a, index=False)
        frame_b.to_csv(csv_b, index=False)
        cache_csv_ohlcv(csv_a, cache_dir, "SAMPLE_A", "SIM", source="unit")
        cache_csv_ohlcv(csv_b, cache_dir, "SAMPLE_B", "SIM", source="unit")
        manifest = build_cache_task_manifest(
            f"{cache_dir}/cache_index.csv",
            generate_strategy_specs(4),
            mode="rolling",
            window_lengths=[120],
            step=30,
            min_bars=90,
        )
        sampled = sample_manifest_stratified(manifest, max_tasks=8, output=f"{tmp}/sampled.csv", seed=7)
        assert len(sampled) == 8
        assert sampled["symbol"].nunique() == 2
        assert sampled["strategy_id"].nunique() >= 3
        summary = json.loads(open(f"{tmp}/sampled.summary.json", encoding="utf-8").read())
        assert summary["sampled_rows"] == 8


def test_quality_gate_skips_low_quality_tasks():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=9))[0]
    with TemporaryDirectory() as tmp:
        csv_path = f"{tmp}/sample.csv"
        manifest_path = f"{tmp}/manifest.csv"
        run_dir = f"{tmp}/run"
        frame.to_csv(csv_path, index=False)
        manifest = build_csv_task_manifest(
            csv_path,
            "SIMLOWQ",
            "SIM",
            generate_strategy_specs(2),
            mode="rolling",
            window_lengths=[120],
            step=90,
            min_bars=90,
        )
        manifest["quality_score"] = 50.0
        manifest.to_csv(manifest_path, index=False)
        decision = quality_gate_decision(manifest.iloc[0], min_quality_score=70, skip_low_quality=True)
        assert decision["skip"] is True
        status, results, summary = run_task_manifest(
            manifest_path,
            run_dir,
            max_tasks=2,
            min_quality_score=70,
            skip_low_quality=True,
        )
        assert set(status["status"]) == {"skipped_quality"}
        assert len(results) == 2
        assert "quality_gate" in results.columns
        assert summary.empty


def test_handshake_bundle_and_ack_verification():
    with TemporaryDirectory() as tmp:
        paths = create_handshake_bundle(tmp, quantlab_root="/tmp/QuantLab")
        assert paths["request"].exists()
        assert paths["ack_template"].exists()
        ack = json.loads(paths["ack_template"].read_text(encoding="utf-8"))
        ack["created_at"] = "2026-06-04T00:00:00"
        ack["accepted"] = True
        ack["accepted_artifacts"] = ["strategy_summary.csv", "validation_results.csv"]
        ack["quantlab_entrypoint"] = "external_validation_artifact_reader"
        ack_path = f"{tmp}/quantlab_handshake_ack.json"
        with open(ack_path, "w", encoding="utf-8") as handle:
            json.dump(ack, handle, ensure_ascii=False, indent=2)
        result = verify_handshake_ack(ack_path)
        assert result["valid"] is True
        ack["accepted"] = False
        with open(ack_path, "w", encoding="utf-8") as handle:
            json.dump(ack, handle, ensure_ascii=False, indent=2)
        result = verify_handshake_ack(ack_path)
        assert result["valid"] is False


def test_sqlite_warehouse_import_export_smoke():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=10))[0]
    with TemporaryDirectory() as tmp:
        csv_path = f"{tmp}/sample.csv"
        manifest_path = f"{tmp}/manifest.csv"
        run_dir = f"{tmp}/runs/run1"
        db_path = f"{tmp}/warehouse/qbvs.sqlite"
        export_dir = f"{tmp}/warehouse/export"
        frame.to_csv(csv_path, index=False)
        manifest = build_csv_task_manifest(
            csv_path,
            "SIMDB",
            "SIM",
            generate_strategy_specs(2),
            mode="rolling",
            window_lengths=[120],
            step=90,
            min_bars=90,
        )
        manifest.to_csv(manifest_path, index=False)
        _, results, _ = run_task_manifest(manifest_path, run_dir, max_tasks=3)
        imported = import_runs_to_warehouse(f"{tmp}/runs", db_path)
        assert imported["runs"] == 1
        assert imported["validation_results"] == len(results)
        stats = warehouse_stats(db_path)
        assert stats["validation_results"] == len(results)
        paths = export_warehouse_tables(db_path, export_dir)
        assert paths["strategy_market_summary"].exists()


def test_fast_screening_and_exact_benchmark_smoke():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=11))[0]
    specs = generate_strategy_specs(3)
    result = fast_validate_one(frame, specs[0], FastScreenConfig())
    assert result["engine"] == "fast_screen"
    assert pd.notna(result["strategy_total_return"])
    results = fast_validate_universe({"SIMFAST": frame}, specs)
    summary = fast_summary(results)
    assert len(results) == 3
    assert "pass_rate" in summary.columns
    comparison = compare_fast_to_exact(frame, specs)
    assert len(comparison) == 3
    assert comparison["total_return_abs_diff"].notna().all()
    assert comparison["annualized_return_abs_diff"].notna().all()


def test_quantlab_bundle_export_and_verify_smoke():
    with TemporaryDirectory() as tmp:
        run_dir = f"{tmp}/run"
        bundle_dir = f"{tmp}/bundle"
        import os

        os.makedirs(run_dir, exist_ok=True)
        pd.DataFrame(
            [
                {
                    "strategy_id": "candidate_exact",
                    "samples": 5,
                    "pass_rate": 0.8,
                    "avg_total_gap": -0.01,
                    "avg_annualized_gap": -0.005,
                    "avg_drawdown_improvement": 0.02,
                    "avg_var_5": -0.01,
                    "avg_cvar_5": -0.02,
                }
            ]
        ).to_csv(f"{run_dir}/strategy_summary.csv", index=False)
        pd.DataFrame(
            [
                {
                    "strategy_id": "candidate_exact",
                    "symbol": "SIM",
                    "market": "SIM",
                    "passes_user_floor": True,
                    "total_return_gap": -0.01,
                    "annualized_return_gap": -0.005,
                    "drawdown_improvement": 0.02,
                }
            ]
        ).to_csv(f"{run_dir}/validation_results.csv", index=False)
        paths = export_quantlab_bundle(run_dir, bundle_dir, QuantLabBundleConfig(top_n=1))
        assert paths["manifest"].exists()
        verification = verify_quantlab_bundle(bundle_dir)
        assert verification["valid"] is True
        candidates = pd.read_csv(paths["candidates"])
        assert set(candidates["approval_state"]) == {"external_evidence_only"}
        assert candidates["requires_exact_validation"].astype(str).str.lower().isin(["false", "0"]).all()


def test_quantlab_fast_bundle_requires_exact_validation():
    with TemporaryDirectory() as tmp:
        run_dir = f"{tmp}/fast_run"
        bundle_dir = f"{tmp}/fast_bundle"
        import os

        os.makedirs(run_dir, exist_ok=True)
        pd.DataFrame(
            [
                {
                    "strategy_id": "candidate_fast",
                    "samples": 5,
                    "pass_rate": 0.8,
                    "avg_total_gap": -0.01,
                    "avg_annualized_gap": -0.005,
                    "avg_drawdown_improvement": 0.02,
                    "avg_var_5": -0.01,
                    "avg_cvar_5": -0.02,
                }
            ]
        ).to_csv(f"{run_dir}/fast_strategy_summary.csv", index=False)
        pd.DataFrame(
            [
                {
                    "strategy_id": "candidate_fast",
                    "symbol": "SIM",
                    "market": "SIM",
                    "passes_user_floor": True,
                    "total_return_gap": -0.01,
                    "annualized_return_gap": -0.005,
                    "drawdown_improvement": 0.02,
                }
            ]
        ).to_csv(f"{run_dir}/fast_validation_results.csv", index=False)
        paths = export_quantlab_bundle(run_dir, bundle_dir, QuantLabBundleConfig(top_n=1))
        verification = verify_quantlab_bundle(bundle_dir)
        assert verification["valid"] is True
        candidates = pd.read_csv(paths["candidates"])
        assert set(candidates["engine"]) == {"fast_screen"}
        assert candidates["requires_exact_validation"].astype(str).str.lower().isin(["true", "1"]).all()


def test_quantlab_fund_bundle_requires_rule_review():
    with TemporaryDirectory() as tmp:
        run_dir = f"{tmp}/fund_run"
        bundle_dir = f"{tmp}/fund_bundle"
        import os

        os.makedirs(run_dir, exist_ok=True)
        pd.DataFrame(
            [
                {
                    "strategy_id": "candidate_fund",
                    "samples": 5,
                    "pass_rate": 0.8,
                    "avg_total_gap": -0.01,
                    "avg_annualized_gap": -0.005,
                    "avg_drawdown_improvement": 0.02,
                    "avg_var_5": -0.01,
                    "avg_cvar_5": -0.02,
                    "avg_subscription_fee": 100.0,
                    "avg_redemption_fee": 10.0,
                }
            ]
        ).to_csv(f"{run_dir}/fund_strategy_summary.csv", index=False)
        pd.DataFrame(
            [
                {
                    "strategy_id": "candidate_fund",
                    "symbol": "ALIPAY_TEST",
                    "market": "ALIPAY_FUND",
                    "passes_user_floor": True,
                    "total_return_gap": -0.01,
                    "annualized_return_gap": -0.005,
                    "drawdown_improvement": 0.02,
                }
            ]
        ).to_csv(f"{run_dir}/fund_validation_results.csv", index=False)
        paths = export_quantlab_bundle(run_dir, bundle_dir, QuantLabBundleConfig(top_n=1))
        verification = verify_quantlab_bundle(bundle_dir)
        assert verification["valid"] is True
        candidates = pd.read_csv(paths["candidates"])
        assert set(candidates["engine"]) == {"alipay_fund_rules"}
        assert candidates["requires_fund_rule_review"].astype(str).str.lower().isin(["true", "1"]).all()


def test_datasource_probe_and_templates_smoke():
    result = probe_moomoo_opend(host="127.0.0.1", port=1, timeout=0.01)
    assert result.host == "127.0.0.1"
    assert isinstance(result.errors, list)
    with TemporaryDirectory() as tmp:
        path = write_tradable_universe_template(f"{tmp}/universe.csv", kind="mixed")
        frame = pd.read_csv(path)
        assert {"symbol", "market", "source", "tradability"}.issubset(frame.columns)
        assert {"moomoo_opend", "alipay_fund_nav_csv"}.issubset(set(frame["source"]))


def test_moomoo_cache_metadata_arguments_are_preserved(monkeypatch):
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=160, seed=23))[0]

    class FakeQuoteContext:
        def __init__(self, host: str, port: int):
            self.host = host
            self.port = port

        def request_history_kline(self, *args, **kwargs):
            raw = pd.DataFrame(
                {
                    "time_key": frame["datetime"].astype(str),
                    "open": frame["open"],
                    "high": frame["high"],
                    "low": frame["low"],
                    "close": frame["close"],
                    "volume": frame["volume"],
                }
            )
            return 0, raw, None

        def close(self):
            return None

    class FakeMoomoo:
        RET_OK = 0
        OpenQuoteContext = FakeQuoteContext

        class KLType:
            K_DAY = "K_DAY"

        class AuType:
            QFQ = "QFQ"

    with TemporaryDirectory() as tmp:
        monkeypatch.setattr("qbvs.datasources.probe_moomoo_opend", lambda host, port: type("Probe", (), {"ready_for_fetch": True, "errors": []})())
        monkeypatch.setattr("qbvs.datasources._load_futu_module", lambda: FakeMoomoo)
        from qbvs.datasources import cache_moomoo_history

        metadata = cache_moomoo_history(
            symbol="US.SPY",
            market="US_ETF",
            cache_dir=tmp,
            start="2024-01-01",
            end="2024-12-31",
            asset_class="ETF",
            tradability="LIKELY_TRADABLE_NEEDS_ACCOUNT_PERMISSION_CHECK",
            currency="USD",
            timezone="America/New_York",
        )
        index = pd.read_csv(f"{tmp}/cache_index.csv")
        assert metadata["asset_class"] == "ETF"
        assert index.loc[0, "asset_class"] == "ETF"
        assert index.loc[0, "currency"] == "USD"
        assert index.loc[0, "timezone"] == "America/New_York"


def test_alipay_nav_csv_caches_to_standard_ohlcv():
    with TemporaryDirectory() as tmp:
        dates = pd.date_range("2024-01-01", periods=40, freq="D")
        nav = pd.Series(range(40), dtype=float) / 1000 + 1.0
        source = f"{tmp}/alipay_nav.csv"
        cache_dir = f"{tmp}/cache"
        pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "nav": nav}).to_csv(source, index=False)
        metadata = cache_alipay_fund_nav(
            source,
            cache_dir,
            symbol="ALIPAY_TEST_FUND",
            fund_name="Test Fund",
        )
        assert metadata["source"] == "alipay_fund_nav_csv"
        assert metadata["asset_class"] == "FUND"
        assert metadata["tradability"] == "CONFIRMED_SOURCE_NEEDS_ORDER_RULE_CHECK"
        index = pd.read_csv(f"{cache_dir}/cache_index.csv")
        assert set(index["symbol"]) == {"ALIPAY_TEST_FUND"}


def test_alipay_fund_rule_template_and_execution_smoke():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=160, seed=12))[0]
    spec = BehaviorStrategySpec("fund_test", 0.98, "boll_lower", "none", "strong_trend_full", "none")
    signals = generate_signals(frame, spec)
    rule = FundTradingRule(
        subscription_fee_rate=0.001,
        redemption_fee_rate_short=0.01,
        redemption_fee_rate_long=0.002,
        buy_confirmation_days=1,
        sell_cash_delay_days=2,
    )
    result = run_fund_target_weight_backtest(frame, signals, rule)
    benchmark = run_fund_buy_hold(frame, rule)
    assert result["metrics"]["trade_count"] > 0
    assert "subscription_fee_total" in result["metrics"]
    assert "redemption_fee_total" in result["metrics"]
    assert pd.notna(benchmark["metrics"]["total_return"])
    with TemporaryDirectory() as tmp:
        path = write_fund_rule_template(f"{tmp}/fund_rule.json")
        loaded = load_fund_rule(path)
        assert loaded.buy_confirmation_days == 1


def test_alipay_fund_strategy_summary_smoke():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=160, seed=13))[0]
    specs = generate_strategy_specs(3)
    results = validate_fund_universe({"SIMFUND": frame}, specs, FundTradingRule())
    summary = summarize_fund_results(results)
    assert len(results) == 3
    assert "avg_subscription_fee" in summary.columns
    assert "avg_redemption_fee" in summary.columns


def test_long_run_campaign_and_candidate_promotion_smoke():
    _, frame = generate_random_paths(RandomPathConfig(paths=1, days=180, seed=14))[0]
    with TemporaryDirectory() as tmp:
        csv_path = f"{tmp}/sample.csv"
        manifest_path = f"{tmp}/manifest.csv"
        campaign_dir = f"{tmp}/campaign"
        candidates_path = f"{tmp}/candidates/promotion_candidates.csv"
        frame.to_csv(csv_path, index=False)
        manifest = build_csv_task_manifest(
            csv_path,
            "SIMCAMP",
            "SIM",
            generate_strategy_specs(3),
            mode="rolling",
            window_lengths=[120],
            step=90,
            min_bars=90,
        )
        manifest.to_csv(manifest_path, index=False)
        paths = build_long_run_campaign(
            manifest_path,
            campaign_dir,
            CampaignConfig(chunk_size=2, workers=2, seconds_per_task=0.1, skip_low_quality=True),
        )
        assert paths["plan"].exists()
        verification = verify_long_run_campaign(campaign_dir)
        assert verification["valid"] is True
        commands = paths["commands"].read_text(encoding="utf-8")
        assert "run-manifest" in commands
        summary = pd.DataFrame(
            [
                {
                    "strategy_id": "candidate_a",
                    "samples": 10,
                    "pass_rate": 0.8,
                    "avg_total_gap": -0.01,
                    "avg_annualized_gap": -0.005,
                    "avg_drawdown_improvement": 0.02,
                },
                {
                    "strategy_id": "candidate_b",
                    "samples": 2,
                    "pass_rate": 0.2,
                    "avg_total_gap": -0.2,
                    "avg_annualized_gap": -0.1,
                    "avg_drawdown_improvement": -0.1,
                },
            ]
        )
        summary_path = f"{tmp}/summary.csv"
        summary.to_csv(summary_path, index=False)
        promoted = promote_candidates_from_summary(summary_path, candidates_path, PromotionConfig(top_n=2, min_samples=2))
        assert set(promoted["promotion_state"]) == {"external_candidate", "review_only"}
        assert promoted["requires_user_approval_before_strategy_library_write"].all()


def test_quantlab_readonly_adapter_pack_smoke():
    with TemporaryDirectory() as tmp:
        pack_dir = f"{tmp}/adapter"
        paths = build_quantlab_adapter_pack(
            pack_dir,
            QuantLabAdapterPackConfig(
                quantlab_root="/tmp/QuantLab",
                default_bundle_dir="/tmp/qbvs/bundle",
                default_campaign_dir="/tmp/qbvs/campaign",
                default_promotion_candidates="/tmp/qbvs/promotion.csv",
            ),
        )
        assert paths["adapter"].exists()
        verification = verify_quantlab_adapter_pack(pack_dir)
        assert verification["valid"] is True
        namespace: dict[str, object] = {}
        exec(paths["adapter"].read_text(encoding="utf-8"), namespace)
        assert "read_qbvs_bundle" in namespace


def test_goal_readiness_audit_outputs_json_csv_pdf():
    with TemporaryDirectory() as tmp:
        summary_path = f"{tmp}/strategy_summary.csv"
        results_path = f"{tmp}/validation_results.csv"
        probe_path = f"{tmp}/moomoo_probe.json"
        ack_path = f"{tmp}/quantlab_handshake_ack.json"
        output_dir = f"{tmp}/audit"
        pd.DataFrame(
            [
                {
                    "strategy_id": "candidate",
                    "samples": 2,
                    "pass_rate": 1.0,
                    "avg_total_gap": -0.01,
                    "avg_annualized_gap": -0.005,
                    "avg_drawdown_improvement": 0.02,
                }
            ]
        ).to_csv(summary_path, index=False)
        pd.DataFrame(
            [
                {
                    "strategy_id": "candidate",
                    "symbol": "SIMA",
                    "passes_user_floor": True,
                    "total_return_gap": -0.01,
                    "annualized_return_gap": -0.005,
                    "drawdown_improvement": 0.02,
                },
                {
                    "strategy_id": "candidate",
                    "symbol": "SIMB",
                    "passes_user_floor": True,
                    "total_return_gap": -0.02,
                    "annualized_return_gap": -0.006,
                    "drawdown_improvement": 0.01,
                },
            ]
        ).to_csv(results_path, index=False)
        with open(probe_path, "w", encoding="utf-8") as handle:
            json.dump({"ready_for_fetch": True, "errors": []}, handle)
        with open(ack_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "protocol_version": "qbvs-quantlab-handshake-v1",
                    "message_type": "handshake_ack",
                    "source_system": "quantlab",
                    "target_system": "quant_behavior_validation_system",
                    "accepted": True,
                    "quantlab_entrypoint": "external_validation_reader",
                },
                handle,
            )
        paths = audit_goal_readiness(
            output_dir,
            summary_path,
            results_path,
            moomoo_probe_path=probe_path,
            handshake_ack_path=ack_path,
            config=GoalAuditConfig(target_symbols=2, target_strategies=1, target_tests_per_strategy=10),
        )
        assert paths["json"].exists()
        assert paths["csv"].exists()
        assert paths["pdf"].exists()
        audit = json.loads(paths["json"].read_text(encoding="utf-8"))
        statuses = {item["requirement_id"]: item["status"] for item in audit["items"]}
        assert statuses["user_return_floor"] == "passed"
        assert statuses["real_tradable_moomoo_gate"] == "passed"
        assert statuses["quantlab_handshake_ack"] == "passed"


def test_seed_universe_has_200_reviewable_symbols():
    with TemporaryDirectory() as tmp:
        path, summary_path = build_seed_universe(f"{tmp}/seed.csv", limit=220)
        assert path.exists()
        assert summary_path.exists()
        result = validate_seed_universe(path, min_symbols=200)
        assert result["valid"] is True
        assert result["symbols"] >= 200
        assert result["markets"] >= 4
        assert result["asset_classes"] >= 5
        frame = pd.read_csv(path)
        assert frame["symbol"].is_unique
        assert {"symbol", "source_symbol", "yahoo_symbol", "tradability"}.issubset(frame.columns)
        plan_paths = build_seed_cache_plan(path, f"{tmp}/cache_plan", limit=5)
        plan = pd.read_csv(plan_paths["plan"])
        assert len(plan) == 5
        assert "cache-moomoo-history" in plan_paths["commands"].read_text(encoding="utf-8")
        summary = json.loads(plan_paths["summary"].read_text(encoding="utf-8"))
        assert summary["starts_background_processes"] is False


def test_moomoo_symbol_alias_normalizes_us_class_share_candidates():
    decision = normalize_moomoo_source_symbol("BRK-B", "US_STOCK", "US.BRK-B")
    assert decision.normalized_source_symbol == "US.BRK.B"
    assert decision.rule_id == "us_class_share_dash_to_dot"
    assert decision.requires_single_symbol_probe is True

    unchanged = normalize_moomoo_source_symbol("AAPL", "US_STOCK", "US.AAPL")
    assert unchanged.normalized_source_symbol == "US.AAPL"
    assert unchanged.rule_id == "no_change"


def test_moomoo_batch_uses_normalized_source_symbol_for_class_share():
    with TemporaryDirectory() as tmp:
        universe_path = f"{tmp}/universe.csv"
        cache_dir = f"{tmp}/cache"
        attempts_path = f"{tmp}/attempts.csv"
        summary_path = f"{tmp}/summary.json"
        pd.DataFrame(
            [
                {
                    "symbol": "BRK-B",
                    "source_symbol": "US.BRK-B",
                    "market": "US_STOCK",
                    "asset_class": "STOCK",
                    "tradability": "LIKELY_TRADABLE_NEEDS_ACCOUNT_PERMISSION_CHECK",
                    "currency": "USD",
                    "timezone": "America/New_York",
                }
            ]
        ).to_csv(universe_path, index=False)

        seen_symbols = []

        def fake_cache(**kwargs):
            seen_symbols.append(kwargs["symbol"])
            dates = pd.date_range("2024-01-01", periods=40, freq="D")
            frame = pd.DataFrame(
                {
                    "datetime": dates,
                    "symbol": kwargs["symbol"],
                    "market": kwargs["market"],
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1000.0,
                }
            )
            return cache_csv_ohlcv(
                _write_frame_csv(frame, tmp, kwargs["symbol"]),
                kwargs["cache_dir"],
                kwargs["symbol"],
                kwargs["market"],
                source="fake_moomoo",
                asset_class=kwargs["asset_class"],
                tradability=kwargs["tradability"],
                currency=kwargs["currency"],
                timezone=kwargs["timezone"],
            )

        paths = cache_moomoo_batch(
            MoomooBatchConfig(
                universe=universe_path,
                cache_dir=cache_dir,
                attempts_output=attempts_path,
                summary_output=summary_path,
                start="2024-01-01",
                end="2024-06-01",
            ),
            cache_func=fake_cache,
        )
        attempts = pd.read_csv(paths["attempts"])
        assert seen_symbols == ["US.BRK.B"]
        assert attempts.loc[0, "source_symbol"] == "US.BRK.B"
        assert attempts.loc[0, "original_source_symbol"] == "US.BRK-B"
        assert attempts.loc[0, "source_symbol_rule"] == "us_class_share_dash_to_dot"


def test_seed_yahoo_universe_and_cache_plan_smoke():
    with TemporaryDirectory() as tmp:
        seed_path, _ = build_seed_universe(f"{tmp}/seed.csv", limit=220)
        yahoo_path, yahoo_summary_path = build_seed_yahoo_universe(seed_path, f"{tmp}/seed_yahoo.csv", limit=12)
        frame = pd.read_csv(yahoo_path)
        assert len(frame) == 12
        assert {"symbol", "market", "source", "original_symbol"}.issubset(frame.columns)
        assert set(frame["source"]) == {"yahoo_public_chart"}
        summary = json.loads(yahoo_summary_path.read_text(encoding="utf-8"))
        assert summary["starts_background_processes"] is False
        plan_paths = build_seed_yahoo_cache_plan(yahoo_path, f"{tmp}/yahoo_cache_plan", limit=5)
        plan = pd.read_csv(plan_paths["plan"])
        assert len(plan) == 5
        command = plan_paths["commands"].read_text(encoding="utf-8")
        assert "cache-yahoo" in command
        assert "--limit 5" in command
        plan_summary = json.loads(plan_paths["summary"].read_text(encoding="utf-8"))
        assert plan_summary["provider"] == "yahoo_public_chart"
        assert plan_summary["writes_quantlab_database"] is False


def test_sample_universe_stratified_covers_markets_and_assets():
    with TemporaryDirectory() as tmp:
        seed_path, _ = build_seed_universe(f"{tmp}/seed.csv", limit=220)
        yahoo_path, _ = build_seed_yahoo_universe(seed_path, f"{tmp}/seed_yahoo.csv")
        sample_path, summary_path = sample_universe_stratified(
            yahoo_path,
            f"{tmp}/seed_yahoo_sample.csv",
            max_symbols=40,
            seed=18,
            group_cols=("market", "asset_class"),
        )
        sample = pd.read_csv(sample_path)
        assert len(sample) == 40
        assert sample["market"].nunique() >= 4
        assert sample["asset_class"].nunique() >= 5
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["sampled_symbols"] == 40
        assert summary["starts_background_processes"] is False


def test_finalist_manifest_selects_ranked_strategy_ids():
    _, frame_a = generate_random_paths(RandomPathConfig(paths=1, days=260, seed=21))[0]
    _, frame_b = generate_random_paths(RandomPathConfig(paths=1, days=260, seed=22))[0]
    with TemporaryDirectory() as tmp:
        csv_a = f"{tmp}/a.csv"
        csv_b = f"{tmp}/b.csv"
        cache_dir = f"{tmp}/cache"
        summary_path = f"{tmp}/strategy_summary.csv"
        manifest_path = f"{tmp}/finalist_manifest.csv"
        frame_a.to_csv(csv_a, index=False)
        frame_b.to_csv(csv_b, index=False)
        cache_csv_ohlcv(csv_a, cache_dir, "FIN_A", "SIM", source="unit")
        cache_csv_ohlcv(csv_b, cache_dir, "FIN_B", "SIM", source="unit")
        strategy_ids = [spec.strategy_id for spec in generate_strategy_specs(4)]
        pd.DataFrame(
            [
                {
                    "strategy_id": strategy_ids[0],
                    "samples": 20,
                    "pass_rate": 0.95,
                    "avg_total_gap": -0.01,
                    "avg_annualized_gap": -0.005,
                    "avg_drawdown_improvement": 0.02,
                },
                {
                    "strategy_id": strategy_ids[1],
                    "samples": 20,
                    "pass_rate": 0.90,
                    "avg_total_gap": -0.02,
                    "avg_annualized_gap": -0.006,
                    "avg_drawdown_improvement": 0.01,
                },
                {
                    "strategy_id": strategy_ids[2],
                    "samples": 20,
                    "pass_rate": 0.40,
                    "avg_total_gap": -0.20,
                    "avg_annualized_gap": -0.10,
                    "avg_drawdown_improvement": -0.05,
                },
            ]
        ).to_csv(summary_path, index=False)
        finalists = select_finalist_strategy_ids(summary_path, FinalistSelectionConfig(top_n=2, min_samples=10))
        assert finalists["strategy_id"].tolist() == strategy_ids[:2]
        manifest, finalists_path, manifest_summary_path = build_finalist_cache_pair_manifest(
            summary_path,
            f"{cache_dir}/cache_index.csv",
            manifest_path,
            selection_config=FinalistSelectionConfig(top_n=2, min_samples=10),
            window_lengths=(120,),
            step=40,
            windows_per_pair=2,
        )
        assert set(manifest["strategy_id"]) == set(strategy_ids[:2])
        assert manifest["symbol"].nunique() == 2
        assert len(manifest) == 2 * 2 * 2
        assert "finalist_rank" in manifest.columns
        assert finalists_path.exists()
        summary = json.loads(manifest_summary_path.read_text(encoding="utf-8"))
        assert summary["strategies"] == 2
        assert summary["writes_quantlab_database"] is False


def test_moomoo_batch_cache_records_attempts_and_summary():
    with TemporaryDirectory() as tmp:
        universe_path = f"{tmp}/universe.csv"
        cache_dir = f"{tmp}/cache"
        attempts_path = f"{tmp}/attempts.csv"
        summary_path = f"{tmp}/summary.json"
        pd.DataFrame(
            [
                {
                    "symbol": "SKIP",
                    "source_symbol": "US.SKIP",
                    "market": "US_ETF",
                    "asset_class": "ETF",
                    "tradability": "T0",
                    "currency": "USD",
                    "timezone": "America/New_York",
                },
                {
                    "symbol": "AAA",
                    "source_symbol": "US.AAA",
                    "market": "US_ETF",
                    "asset_class": "ETF",
                    "tradability": "T1",
                    "currency": "USD",
                    "timezone": "America/New_York",
                },
                {
                    "symbol": "BBB",
                    "source_symbol": "US.BBB",
                    "market": "US_ETF",
                    "asset_class": "ETF",
                    "tradability": "T2",
                    "currency": "USD",
                    "timezone": "America/New_York",
                },
            ]
        ).to_csv(universe_path, index=False)

        def fake_cache(**kwargs):
            dates = pd.date_range("2024-01-01", periods=140, freq="D")
            frame = pd.DataFrame(
                {
                    "datetime": dates,
                    "symbol": kwargs["symbol"],
                    "market": kwargs["market"],
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1000.0,
                }
            )
            return cache_csv_ohlcv(
                _write_frame_csv(frame, tmp, kwargs["symbol"]),
                kwargs["cache_dir"],
                kwargs["symbol"],
                kwargs["market"],
                source="fake_moomoo",
                asset_class=kwargs["asset_class"],
                tradability=kwargs["tradability"],
                currency=kwargs["currency"],
                timezone=kwargs["timezone"],
            )

        paths = cache_moomoo_batch(
            MoomooBatchConfig(
                universe=universe_path,
                cache_dir=cache_dir,
                attempts_output=attempts_path,
                summary_output=summary_path,
                start="2024-01-01",
                end="2024-06-01",
                offset=1,
                limit=2,
            ),
            cache_func=fake_cache,
        )
        attempts = pd.read_csv(paths["attempts"])
        assert attempts["source_symbol"].tolist() == ["US.AAA", "US.BBB"]
        assert attempts["returncode"].tolist() == [0, 0]
        summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
        assert summary["success"] == 2
        assert summary["failed"] == 0
        assert summary["writes_quantlab_database"] is False
        index = pd.read_csv(paths["cache_index"])
        assert set(index["symbol"]) == {"US.AAA", "US.BBB"}
