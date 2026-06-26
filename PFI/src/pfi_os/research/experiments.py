from __future__ import annotations

import itertools
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from pfi_os.backtest import BacktestConfig, BacktestEngine, BacktestResult
from pfi_os.config import report_date_dir
from pfi_os.strategies.base import Strategy

StrategyFactory = type[Strategy] | Callable[..., Strategy]


@dataclass(frozen=True)
class ExperimentRun:
    run_id: str
    strategy_id: str
    params: dict[str, Any]
    metrics: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class ParameterStabilityReport:
    score_metric: str
    best_score: float
    top_quantile_mean: float
    top_quantile_threshold: float
    neighbor_mean: float
    neighbor_count: int
    parameter_coverage: float
    stability_status: str
    notes: str


@dataclass(frozen=True)
class TrainTestValidationReport:
    split_datetime: str
    train_rows: int
    test_rows: int
    score_metric: str
    best_train_run_id: str
    best_params: dict[str, Any]
    train_score: float
    test_score: float
    train_total_return: float
    test_total_return: float
    train_max_drawdown: float
    test_max_drawdown: float
    generalization_ratio: float
    validation_status: str
    notes: str


@dataclass(frozen=True)
class WalkForwardValidationReport:
    window_count: int
    pass_count: int
    watch_count: int
    failed_count: int
    average_train_score: float
    average_test_score: float
    average_generalization_ratio: float
    validation_status: str
    notes: str
    windows: list[dict[str, Any]]


def grid_parameters(param_grid: dict[str, Iterable[Any]]) -> list[dict[str, Any]]:
    keys = list(param_grid)
    values = [list(param_grid[key]) for key in keys]
    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


class ExperimentRunner:
    def __init__(self, output_dir: Path | str | None = None, config: BacktestConfig | None = None):
        self.output_dir = Path(output_dir) if output_dir is not None else report_date_dir() / "Experiments"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or BacktestConfig()

    def run_grid(
        self,
        data: pd.DataFrame,
        strategy_cls: StrategyFactory,
        param_grid: dict[str, Iterable[Any]],
        experiment_name: str | None = None,
    ) -> tuple[pd.DataFrame, dict[str, BacktestResult]]:
        experiment_name = experiment_name or f"{_strategy_factory_label(strategy_cls)}_{_timestamp_slug()}"
        result_dir = self.output_dir / experiment_name
        result_dir.mkdir(parents=True, exist_ok=True)
        runs: list[ExperimentRun] = []
        results: dict[str, BacktestResult] = {}
        for idx, params in enumerate(grid_parameters(param_grid), start=1):
            strategy = _build_strategy(strategy_cls, params)
            result = BacktestEngine(self.config).run(data, strategy)
            run_id = f"{experiment_name}_{idx:04d}"
            runs.append(
                ExperimentRun(
                    run_id=run_id,
                    strategy_id=strategy.strategy_id,
                    params=params,
                    metrics=result.metrics,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            )
            results[run_id] = result
        summary = self._summary_frame(runs)
        summary.to_csv(result_dir / "summary.csv", index=False)
        stability = analyze_parameter_stability(summary)
        (result_dir / "stability.json").write_text(json.dumps(asdict(stability), ensure_ascii=False, indent=2), encoding="utf-8")
        (result_dir / "runs.json").write_text(json.dumps([asdict(run) for run in runs], ensure_ascii=False, indent=2), encoding="utf-8")
        return summary, results

    def run_train_test_validation(
        self,
        data: pd.DataFrame,
        strategy_cls: StrategyFactory,
        param_grid: dict[str, Iterable[Any]],
        experiment_name: str,
        split_ratio: float = 0.7,
        score_metric: str = "sharpe",
    ) -> TrainTestValidationReport:
        result_dir = self.output_dir / experiment_name
        result_dir.mkdir(parents=True, exist_ok=True)
        train_data, test_data, split_datetime = split_train_test_by_time(data, split_ratio=split_ratio)
        if train_data.empty or test_data.empty:
            report = TrainTestValidationReport(
                split_datetime="",
                train_rows=int(len(train_data)),
                test_rows=int(len(test_data)),
                score_metric=score_metric,
                best_train_run_id="",
                best_params={},
                train_score=0.0,
                test_score=0.0,
                train_total_return=0.0,
                test_total_return=0.0,
                train_max_drawdown=0.0,
                test_max_drawdown=0.0,
                generalization_ratio=0.0,
                validation_status="InsufficientData",
                notes="Train or test period is empty.",
            )
            (result_dir / "train_test_validation.json").write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
            return report

        train_summary, _ = self._run_grid_without_persist(train_data, strategy_cls, param_grid, experiment_name=f"{experiment_name}_train")
        train_summary.to_csv(result_dir / "train_summary.csv", index=False)
        if train_summary.empty or score_metric not in train_summary.columns:
            report = _empty_train_test_report(split_datetime, len(train_data), len(test_data), score_metric, "Training summary is empty or missing score metric.")
            (result_dir / "train_test_validation.json").write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
            return report

        best_train = train_summary.iloc[0].to_dict()
        best_params = {column.replace("param_", "", 1): _json_value(best_train[column]) for column in train_summary.columns if column.startswith("param_")}
        test_strategy = _build_strategy(strategy_cls, best_params)
        test_result = BacktestEngine(self.config).run(test_data, test_strategy)
        test_row = {"run_id": f"{experiment_name}_test_best", "strategy_id": test_strategy.strategy_id}
        test_row.update({f"param_{key}": value for key, value in best_params.items()})
        test_row.update(test_result.metrics)
        pd.DataFrame([test_row]).to_csv(result_dir / "test_summary.csv", index=False)
        train_score = float(best_train.get(score_metric, 0.0) or 0.0)
        test_score = float(test_result.metrics.get(score_metric, 0.0) or 0.0)
        ratio = test_score / train_score if train_score else 0.0
        status = _train_test_status(train_score, test_score, ratio)
        report = TrainTestValidationReport(
            split_datetime=str(split_datetime),
            train_rows=int(len(train_data)),
            test_rows=int(len(test_data)),
            score_metric=score_metric,
            best_train_run_id=str(best_train.get("run_id", "")),
            best_params=best_params,
            train_score=train_score,
            test_score=test_score,
            train_total_return=float(best_train.get("total_return", 0.0) or 0.0),
            test_total_return=float(test_result.metrics.get("total_return", 0.0) or 0.0),
            train_max_drawdown=float(best_train.get("max_drawdown", 0.0) or 0.0),
            test_max_drawdown=float(test_result.metrics.get("max_drawdown", 0.0) or 0.0),
            generalization_ratio=float(ratio),
            validation_status=status,
            notes=_train_test_notes(status),
        )
        (result_dir / "train_test_validation.json").write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    def run_walk_forward_validation(
        self,
        data: pd.DataFrame,
        strategy_cls: StrategyFactory,
        param_grid: dict[str, Iterable[Any]],
        experiment_name: str,
        train_window: int = 252,
        test_window: int = 63,
        step_window: int | None = None,
        score_metric: str = "sharpe",
    ) -> WalkForwardValidationReport:
        result_dir = self.output_dir / experiment_name
        result_dir.mkdir(parents=True, exist_ok=True)
        windows = walk_forward_windows(data, train_window=train_window, test_window=test_window, step_window=step_window)
        rows = []
        for idx, (train_data, test_data, bounds) in enumerate(windows, start=1):
            train_summary, _ = self._run_grid_without_persist(train_data, strategy_cls, param_grid, experiment_name=f"{experiment_name}_wf{idx:02d}_train")
            if train_summary.empty or score_metric not in train_summary.columns:
                continue
            best_train = train_summary.iloc[0].to_dict()
            best_params = {column.replace("param_", "", 1): _json_value(best_train[column]) for column in train_summary.columns if column.startswith("param_")}
            test_strategy = _build_strategy(strategy_cls, best_params)
            test_result = BacktestEngine(self.config).run(test_data, test_strategy)
            train_score = float(best_train.get(score_metric, 0.0) or 0.0)
            test_score = float(test_result.metrics.get(score_metric, 0.0) or 0.0)
            ratio = test_score / train_score if train_score else 0.0
            status = _train_test_status(train_score, test_score, ratio)
            rows.append(
                {
                    "window": idx,
                    "train_start": str(bounds["train_start"]),
                    "train_end": str(bounds["train_end"]),
                    "test_start": str(bounds["test_start"]),
                    "test_end": str(bounds["test_end"]),
                    "train_rows": int(len(train_data)),
                    "test_rows": int(len(test_data)),
                    "best_train_run_id": str(best_train.get("run_id", "")),
                    "best_params": best_params,
                    "train_score": train_score,
                    "test_score": test_score,
                    "train_total_return": float(best_train.get("total_return", 0.0) or 0.0),
                    "test_total_return": float(test_result.metrics.get("total_return", 0.0) or 0.0),
                    "train_max_drawdown": float(best_train.get("max_drawdown", 0.0) or 0.0),
                    "test_max_drawdown": float(test_result.metrics.get("max_drawdown", 0.0) or 0.0),
                    "generalization_ratio": float(ratio),
                    "validation_status": status,
                }
            )
        report = _walk_forward_report(rows)
        pd.DataFrame(rows).to_csv(result_dir / "walk_forward_windows.csv", index=False)
        (result_dir / "walk_forward_validation.json").write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    @staticmethod
    def _summary_frame(runs: list[ExperimentRun]) -> pd.DataFrame:
        rows = []
        for run in runs:
            row = {"run_id": run.run_id, "strategy_id": run.strategy_id, "created_at": run.created_at}
            row.update({f"param_{k}": v for k, v in run.params.items()})
            row.update(run.metrics)
            rows.append(row)
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows).sort_values(["sharpe", "total_return"], ascending=False, na_position="last")

    def _run_grid_without_persist(
        self,
        data: pd.DataFrame,
        strategy_cls: StrategyFactory,
        param_grid: dict[str, Iterable[Any]],
        experiment_name: str,
    ) -> tuple[pd.DataFrame, dict[str, BacktestResult]]:
        runs: list[ExperimentRun] = []
        results: dict[str, BacktestResult] = {}
        for idx, params in enumerate(grid_parameters(param_grid), start=1):
            strategy = _build_strategy(strategy_cls, params)
            result = BacktestEngine(self.config).run(data, strategy)
            run_id = f"{experiment_name}_{idx:04d}"
            runs.append(
                ExperimentRun(
                    run_id=run_id,
                    strategy_id=strategy.strategy_id,
                    params=params,
                    metrics=result.metrics,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            )
            results[run_id] = result
        return self._summary_frame(runs), results


def _build_strategy(strategy_factory: StrategyFactory, params: dict[str, Any]) -> Strategy:
    strategy = strategy_factory(**params)
    if not isinstance(strategy, Strategy):
        raise TypeError("strategy_factory must return a Strategy instance.")
    return strategy


def _strategy_factory_label(strategy_factory: StrategyFactory) -> str:
    strategy_id = getattr(strategy_factory, "strategy_id", "")
    if strategy_id:
        return str(strategy_id)
    name = getattr(strategy_factory, "__name__", "")
    return name or "strategy"


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def analyze_parameter_stability(summary: pd.DataFrame, score_metric: str = "sharpe", top_quantile: float = 0.2) -> ParameterStabilityReport:
    if summary.empty or score_metric not in summary.columns:
        return ParameterStabilityReport(score_metric, 0.0, 0.0, 0.0, 0.0, 0, 0.0, "InsufficientData", "Summary is empty or missing the score metric.")

    data = summary.copy()
    data = data[pd.to_numeric(data[score_metric], errors="coerce").notna()].copy()
    if data.empty:
        return ParameterStabilityReport(score_metric, 0.0, 0.0, 0.0, 0.0, 0, 0.0, "InsufficientData", "Score metric has no numeric values.")
    data[score_metric] = pd.to_numeric(data[score_metric], errors="coerce")
    parameter_columns = [column for column in data.columns if column.startswith("param_")]
    best = data.sort_values(score_metric, ascending=False).iloc[0]
    best_score = float(best[score_metric])
    threshold = float(data[score_metric].quantile(max(0.0, min(1.0, 1 - top_quantile))))
    top_slice = data[data[score_metric] >= threshold]
    top_mean = float(top_slice[score_metric].mean()) if not top_slice.empty else 0.0
    neighbors = _parameter_neighbors(data, best, parameter_columns)
    neighbor_mean = float(neighbors[score_metric].mean()) if not neighbors.empty else 0.0
    coverage = _parameter_coverage(data, top_slice, parameter_columns)
    status = _stability_status(best_score, top_mean, neighbor_mean, coverage, len(neighbors))
    notes = _stability_notes(status)
    return ParameterStabilityReport(
        score_metric=score_metric,
        best_score=best_score,
        top_quantile_mean=top_mean,
        top_quantile_threshold=threshold,
        neighbor_mean=neighbor_mean,
        neighbor_count=int(len(neighbors)),
        parameter_coverage=float(coverage),
        stability_status=status,
        notes=notes,
    )


def _parameter_neighbors(data: pd.DataFrame, best: pd.Series, parameter_columns: list[str]) -> pd.DataFrame:
    if not parameter_columns:
        return data.iloc[0:0]
    mask = pd.Series(True, index=data.index)
    for column in parameter_columns:
        values = sorted(data[column].dropna().unique())
        if len(values) <= 1:
            continue
        try:
            index = values.index(best[column])
        except ValueError:
            continue
        allowed = set(values[max(0, index - 1) : min(len(values), index + 2)])
        mask &= data[column].isin(allowed)
    neighbors = data[mask].copy()
    return neighbors[neighbors["run_id"] != best.get("run_id")] if "run_id" in neighbors.columns else neighbors


def _parameter_coverage(data: pd.DataFrame, top_slice: pd.DataFrame, parameter_columns: list[str]) -> float:
    if not parameter_columns or top_slice.empty:
        return 0.0
    coverages = []
    for column in parameter_columns:
        total = max(data[column].nunique(dropna=True), 1)
        covered = top_slice[column].nunique(dropna=True)
        coverages.append(covered / total)
    return float(sum(coverages) / len(coverages)) if coverages else 0.0


def _stability_status(best_score: float, top_mean: float, neighbor_mean: float, coverage: float, neighbor_count: int) -> str:
    if best_score <= 0 or neighbor_count == 0:
        return "Review"
    top_ratio = top_mean / best_score if best_score else 0.0
    neighbor_ratio = neighbor_mean / best_score if best_score else 0.0
    if top_ratio >= 0.75 and neighbor_ratio >= 0.65 and coverage >= 0.35:
        return "Stable"
    if top_ratio >= 0.55 and neighbor_ratio >= 0.45:
        return "Watch"
    return "Fragile"


def _stability_notes(status: str) -> str:
    notes = {
        "Stable": "Top parameters and nearby parameters remain reasonably strong; overfitting risk is lower but still requires out-of-sample validation.",
        "Watch": "Some neighboring or top-quantile parameters are acceptable, but stability is not strong enough for high confidence.",
        "Fragile": "Performance appears concentrated around a narrow parameter choice; overfitting risk is high.",
        "Review": "Stability cannot be confirmed because the score is weak, missing, or has too few neighboring parameters.",
    }
    return notes.get(status, "Review required.")


def split_train_test_by_time(data: pd.DataFrame, split_ratio: float = 0.7) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp | str]:
    if data.empty:
        return data.copy(), data.copy(), ""
    ratio = max(0.1, min(0.9, split_ratio))
    ordered = data.copy()
    ordered["datetime"] = pd.to_datetime(ordered["datetime"])
    unique_dates = sorted(ordered["datetime"].dropna().unique())
    if len(unique_dates) < 2:
        return ordered, ordered.iloc[0:0].copy(), ""
    split_index = max(1, min(len(unique_dates) - 1, int(len(unique_dates) * ratio)))
    split_datetime = unique_dates[split_index]
    train = ordered[ordered["datetime"] < split_datetime].copy()
    test = ordered[ordered["datetime"] >= split_datetime].copy()
    return train, test, split_datetime


def walk_forward_windows(
    data: pd.DataFrame,
    train_window: int = 252,
    test_window: int = 63,
    step_window: int | None = None,
) -> list[tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]]:
    if data.empty:
        return []
    train_size = max(2, int(train_window))
    test_size = max(1, int(test_window))
    step = max(1, int(step_window or test_size))
    ordered = data.copy()
    ordered["datetime"] = pd.to_datetime(ordered["datetime"])
    unique_dates = sorted(ordered["datetime"].dropna().unique())
    windows = []
    start = 0
    while start + train_size + test_size <= len(unique_dates):
        train_dates = unique_dates[start : start + train_size]
        test_dates = unique_dates[start + train_size : start + train_size + test_size]
        train = ordered[ordered["datetime"].isin(train_dates)].copy()
        test = ordered[ordered["datetime"].isin(test_dates)].copy()
        windows.append(
            (
                train,
                test,
                {
                    "train_start": train_dates[0],
                    "train_end": train_dates[-1],
                    "test_start": test_dates[0],
                    "test_end": test_dates[-1],
                },
            )
        )
        start += step
    return windows


def _empty_train_test_report(split_datetime, train_rows: int, test_rows: int, score_metric: str, notes: str) -> TrainTestValidationReport:
    return TrainTestValidationReport(
        split_datetime=str(split_datetime),
        train_rows=int(train_rows),
        test_rows=int(test_rows),
        score_metric=score_metric,
        best_train_run_id="",
        best_params={},
        train_score=0.0,
        test_score=0.0,
        train_total_return=0.0,
        test_total_return=0.0,
        train_max_drawdown=0.0,
        test_max_drawdown=0.0,
        generalization_ratio=0.0,
        validation_status="InsufficientData",
        notes=notes,
    )


def _train_test_status(train_score: float, test_score: float, ratio: float) -> str:
    if train_score <= 0:
        return "Review"
    if test_score <= 0:
        return "Failed"
    if ratio >= 0.7:
        return "Pass"
    if ratio >= 0.35:
        return "Watch"
    return "Failed"


def _train_test_notes(status: str) -> str:
    notes = {
        "Pass": "The best training parameter remains reasonably effective in the test period.",
        "Watch": "The best training parameter still works in the test period, but performance decays materially.",
        "Failed": "The best training parameter does not generalize well to the test period.",
        "Review": "Training score is weak or unavailable; out-of-sample validation needs review.",
        "InsufficientData": "Not enough data to split into train and test periods.",
    }
    return notes.get(status, "Review required.")


def _walk_forward_report(rows: list[dict[str, Any]]) -> WalkForwardValidationReport:
    if not rows:
        return WalkForwardValidationReport(0, 0, 0, 0, 0.0, 0.0, 0.0, "InsufficientData", "Not enough data to build walk-forward windows.", [])
    pass_count = sum(1 for row in rows if row["validation_status"] == "Pass")
    watch_count = sum(1 for row in rows if row["validation_status"] == "Watch")
    failed_count = sum(1 for row in rows if row["validation_status"] == "Failed")
    average_train = sum(float(row["train_score"]) for row in rows) / len(rows)
    average_test = sum(float(row["test_score"]) for row in rows) / len(rows)
    average_ratio = sum(float(row["generalization_ratio"]) for row in rows) / len(rows)
    status = _walk_forward_status(pass_count, watch_count, failed_count, len(rows), average_ratio)
    return WalkForwardValidationReport(
        window_count=int(len(rows)),
        pass_count=int(pass_count),
        watch_count=int(watch_count),
        failed_count=int(failed_count),
        average_train_score=float(average_train),
        average_test_score=float(average_test),
        average_generalization_ratio=float(average_ratio),
        validation_status=status,
        notes=_walk_forward_notes(status),
        windows=rows,
    )


def _walk_forward_status(pass_count: int, watch_count: int, failed_count: int, total: int, average_ratio: float) -> str:
    if total <= 0:
        return "InsufficientData"
    pass_rate = pass_count / total
    weak_rate = (pass_count + watch_count) / total
    if pass_rate >= 0.6 and average_ratio >= 0.65:
        return "Pass"
    if weak_rate >= 0.6 and average_ratio >= 0.35:
        return "Watch"
    if failed_count / total >= 0.5:
        return "Failed"
    return "Review"


def _walk_forward_notes(status: str) -> str:
    notes = {
        "Pass": "Most walk-forward windows preserve out-of-sample performance.",
        "Watch": "Some walk-forward windows preserve performance, but decay is material.",
        "Failed": "Walk-forward windows frequently fail out of sample.",
        "Review": "Walk-forward evidence is mixed and needs review.",
        "InsufficientData": "Not enough history to create rolling train/test windows.",
    }
    return notes.get(status, "Review required.")


def _json_value(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value
