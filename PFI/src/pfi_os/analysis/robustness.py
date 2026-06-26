from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MIN_BOOTSTRAP_SIMULATIONS = 10_000


@dataclass(frozen=True)
class BootstrapRobustnessResult:
    summary: dict[str, float | int]
    simulations: pd.DataFrame
    sample_paths: pd.DataFrame
    path_interval: pd.DataFrame


def bootstrap_equity_robustness(
    equity_curve: pd.DataFrame,
    simulations: int = 10_000,
    seed: int = 42,
    target_return: float = 0.0,
    sample_path_count: int = 30,
    annualization: int = 252,
) -> BootstrapRobustnessResult:
    simulations = max(MIN_BOOTSTRAP_SIMULATIONS, int(simulations))
    returns = _equity_returns(equity_curve)
    if returns.empty:
        empty_summary = {
            "simulations": 0,
            "horizon": 0,
            "median_total_return": 0.0,
            "p05_total_return": 0.0,
            "p95_total_return": 0.0,
            "median_max_drawdown": 0.0,
            "p05_max_drawdown": 0.0,
            "p95_max_drawdown": 0.0,
            "median_sharpe": 0.0,
            "loss_probability": 0.0,
            "target_probability": 0.0,
            "severe_drawdown_probability": 0.0,
        }
        return BootstrapRobustnessResult(empty_summary, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    rng = np.random.default_rng(seed)
    horizon = int(len(returns))
    sampled = rng.choice(returns.to_numpy(dtype=float), size=(int(simulations), horizon), replace=True)
    wealth_paths = np.cumprod(1.0 + sampled, axis=1)
    total_returns = wealth_paths[:, -1] - 1.0
    running_peak = np.maximum.accumulate(wealth_paths, axis=1)
    drawdowns = wealth_paths / running_peak - 1.0
    max_drawdowns = drawdowns.min(axis=1)
    volatility = sampled.std(axis=1, ddof=1) * annualization**0.5
    annualized_mean = sampled.mean(axis=1) * annualization
    sharpes = np.divide(annualized_mean, volatility, out=np.zeros_like(annualized_mean), where=volatility != 0)
    simulation_frame = pd.DataFrame(
        {
            "simulation": np.arange(1, int(simulations) + 1),
            "total_return": total_returns,
            "max_drawdown": max_drawdowns,
            "sharpe": sharpes,
        }
    )
    sample_paths = pd.DataFrame(wealth_paths[: int(sample_path_count)].T)
    sample_paths.insert(0, "step", np.arange(1, horizon + 1))
    path_interval = pd.DataFrame(
        {
            "step": np.arange(1, horizon + 1),
            "p05": np.quantile(wealth_paths, 0.05, axis=0),
            "median": np.quantile(wealth_paths, 0.50, axis=0),
            "p95": np.quantile(wealth_paths, 0.95, axis=0),
        }
    )
    summary = {
        "simulations": int(simulations),
        "horizon": horizon,
        "median_total_return": float(np.median(total_returns)),
        "p05_total_return": float(np.quantile(total_returns, 0.05)),
        "p95_total_return": float(np.quantile(total_returns, 0.95)),
        "median_max_drawdown": float(np.median(max_drawdowns)),
        "p05_max_drawdown": float(np.quantile(max_drawdowns, 0.05)),
        "p95_max_drawdown": float(np.quantile(max_drawdowns, 0.95)),
        "median_sharpe": float(np.median(sharpes)),
        "loss_probability": float((total_returns < 0).mean()),
        "target_probability": float((total_returns >= target_return).mean()),
        "severe_drawdown_probability": float((max_drawdowns <= -0.20).mean()),
    }
    return BootstrapRobustnessResult(summary=summary, simulations=simulation_frame, sample_paths=sample_paths, path_interval=path_interval)


def robustness_summary_rows(result: BootstrapRobustnessResult) -> list[dict[str, str]]:
    summary = result.summary
    return [
        _row("模拟次数 Simulations", summary.get("simulations", 0), "integer"),
        _row("重采样周期 Horizon", summary.get("horizon", 0), "integer"),
        _row("中位总收益 Median Total Return", summary.get("median_total_return", 0.0), "percent"),
        _row("5% 分位总收益 5th Percentile Return", summary.get("p05_total_return", 0.0), "percent"),
        _row("95% 分位总收益 95th Percentile Return", summary.get("p95_total_return", 0.0), "percent"),
        _row("中位最大回撤 Median Max Drawdown", summary.get("median_max_drawdown", 0.0), "percent"),
        _row("5% 分位最大回撤 5th Percentile Max DD", summary.get("p05_max_drawdown", 0.0), "percent"),
        _row("中位夏普 Median Sharpe", summary.get("median_sharpe", 0.0), "number"),
        _row("亏损概率 Loss Probability", summary.get("loss_probability", 0.0), "percent"),
        _row("达到目标收益概率 Target Probability", summary.get("target_probability", 0.0), "percent"),
        _row("严重回撤概率 Severe DD Probability", summary.get("severe_drawdown_probability", 0.0), "percent"),
    ]


def _equity_returns(equity_curve: pd.DataFrame) -> pd.Series:
    if equity_curve.empty or "equity" not in equity_curve.columns:
        return pd.Series(dtype=float)
    equity = pd.to_numeric(equity_curve["equity"], errors="coerce").dropna()
    if len(equity) < 3:
        return pd.Series(dtype=float)
    returns = equity.pct_change().dropna()
    return returns.replace([float("inf"), -float("inf")], np.nan).dropna()


def _row(label: str, value: object, formatter: str) -> dict[str, str]:
    if formatter == "integer":
        formatted = str(int(float(value or 0)))
    elif formatter == "percent":
        formatted = f"{float(value or 0.0):.2%}"
    else:
        formatted = f"{float(value or 0.0):.2f}"
    return {"指标 Metric": label, "值 Value": formatted}
