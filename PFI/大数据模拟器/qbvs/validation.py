from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from qbvs.backtest import CostModel, compare_to_buy_hold, normalize_ohlcv, run_buy_hold, run_target_weight_backtest
from qbvs.simulation import RandomPathConfig, generate_random_paths
from qbvs.strategies import BehaviorStrategySpec, generate_signals
from qbvs.windows import WindowedFrame, event_windows, load_event_windows, rolling_windows


@dataclass(frozen=True)
class ValidationConfig:
    initial_cash: float = 100_000.0
    commission_rate: float = 0.001
    slippage_bps: float = 5.0
    market_impact_bps: float = 0.0
    annualization: int = 252

    def cost_model(self) -> CostModel:
        return CostModel(
            initial_cash=self.initial_cash,
            commission_rate=self.commission_rate,
            slippage_bps=self.slippage_bps,
            market_impact_bps=self.market_impact_bps,
            annualization=self.annualization,
        )


def validate_one(frame: pd.DataFrame, spec: BehaviorStrategySpec, config: ValidationConfig | None = None) -> dict[str, object]:
    config = config or ValidationConfig()
    bars = normalize_ohlcv(frame)
    signals = generate_signals(bars, spec)
    strategy = run_target_weight_backtest(bars, signals, config.cost_model())
    benchmark = run_buy_hold(bars, config.cost_model())
    comparison = compare_to_buy_hold(strategy["metrics"], benchmark["metrics"])
    return {
        "strategy_id": spec.strategy_id,
        "symbol": str(bars["symbol"].iloc[0]),
        "market": str(bars["market"].iloc[0]),
        "start": str(pd.Timestamp(bars["datetime"].iloc[0]).date()),
        "end": str(pd.Timestamp(bars["datetime"].iloc[-1]).date()),
        "bars": int(len(bars)),
        **{f"strategy_{k}": v for k, v in strategy["metrics"].items()},
        **{f"buy_hold_{k}": v for k, v in benchmark["metrics"].items()},
        **comparison,
    }


def validate_universe(
    data_by_symbol: dict[str, pd.DataFrame],
    specs: Iterable[BehaviorStrategySpec],
    config: ValidationConfig | None = None,
) -> pd.DataFrame:
    rows = []
    for spec in specs:
        for symbol, frame in data_by_symbol.items():
            try:
                rows.append(validate_one(frame, spec, config))
            except Exception as exc:
                rows.append({"strategy_id": spec.strategy_id, "symbol": symbol, "error": str(exc)})
    return pd.DataFrame(rows)


def validate_windowed_universe(
    data_by_symbol: dict[str, pd.DataFrame],
    specs: Iterable[BehaviorStrategySpec],
    windows_by_symbol: dict[str, list[WindowedFrame]],
    config: ValidationConfig | None = None,
) -> pd.DataFrame:
    rows = []
    for spec in specs:
        for symbol, windows in windows_by_symbol.items():
            for window in windows:
                try:
                    result = validate_one(window.frame, spec, config)
                    result["source_symbol"] = symbol
                    result["window_label"] = window.label
                    rows.append(result)
                except Exception as exc:
                    rows.append({"strategy_id": spec.strategy_id, "symbol": symbol, "window_label": window.label, "error": str(exc)})
    return pd.DataFrame(rows)


def validate_rolling_universe(
    data_by_symbol: dict[str, pd.DataFrame],
    specs: Iterable[BehaviorStrategySpec],
    lengths: Iterable[int] = (252, 504, 756, 1260),
    step: int = 63,
    min_bars: int = 120,
    config: ValidationConfig | None = None,
) -> pd.DataFrame:
    windows_by_symbol = {
        symbol: rolling_windows(frame, lengths=lengths, step=step, min_bars=min_bars)
        for symbol, frame in data_by_symbol.items()
    }
    return validate_windowed_universe(data_by_symbol, specs, windows_by_symbol, config)


def validate_event_universe(
    data_by_symbol: dict[str, pd.DataFrame],
    specs: Iterable[BehaviorStrategySpec],
    event_window_path: Path | str,
    min_bars: int = 30,
    config: ValidationConfig | None = None,
) -> pd.DataFrame:
    events = load_event_windows(event_window_path)
    windows_by_symbol = {
        symbol: event_windows(frame, events, min_bars=min_bars)
        for symbol, frame in data_by_symbol.items()
    }
    return validate_windowed_universe(data_by_symbol, specs, windows_by_symbol, config)


def stress_random(
    specs: Iterable[BehaviorStrategySpec],
    random_config: RandomPathConfig,
    config: ValidationConfig | None = None,
) -> pd.DataFrame:
    rows = []
    paths = generate_random_paths(random_config)
    for spec in specs:
        for regime, frame in paths:
            result = validate_one(frame, spec, config)
            result["regime"] = regime
            rows.append(result)
    return pd.DataFrame(rows)


def summarize_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    if "error" in results.columns:
        error_mask = results["error"].fillna("").astype(str).str.len() > 0
        valid = results[~error_mask].copy()
    else:
        valid = results.copy()
    if valid.empty:
        return pd.DataFrame()
    grouped = valid.groupby("strategy_id", dropna=False)
    summary = grouped.agg(
        samples=("symbol", "count"),
        pass_rate=("passes_user_floor", "mean"),
        avg_total_gap=("total_return_gap", "mean"),
        median_total_gap=("total_return_gap", "median"),
        avg_annualized_gap=("annualized_return_gap", "mean"),
        avg_drawdown_improvement=("drawdown_improvement", "mean"),
        avg_strategy_return=("strategy_total_return", "mean"),
        avg_buy_hold_return=("buy_hold_total_return", "mean"),
        avg_var_5=("strategy_var_5", "mean"),
        avg_cvar_5=("strategy_cvar_5", "mean"),
        avg_turnover=("strategy_turnover", "mean"),
        avg_trades=("strategy_trade_count", "mean"),
    ).reset_index()
    return summary.sort_values(
        ["pass_rate", "avg_annualized_gap", "avg_drawdown_improvement", "avg_total_gap"],
        ascending=[False, False, False, False],
    )


def write_run_artifacts(run_dir: Path, results: pd.DataFrame, summary: pd.DataFrame, config: ValidationConfig) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(run_dir / "validation_results.csv", index=False)
    summary.to_csv(run_dir / "strategy_summary.csv", index=False)
    (run_dir / "validation_config.json").write_text(pd.Series(asdict(config)).to_json(force_ascii=False, indent=2), encoding="utf-8")
