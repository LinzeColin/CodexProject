from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from qbvs.strategies import select_strategy_specs_by_id
from qbvs.tasks import build_cache_pair_task_manifest


@dataclass(frozen=True)
class FinalistSelectionConfig:
    top_n: int = 20
    min_samples: int = 150
    min_pass_rate: float = 0.60
    min_avg_total_gap: float = -0.08
    min_avg_annualized_gap: float = -0.03
    min_avg_drawdown_improvement: float = -0.005


def select_finalist_strategy_ids(summary_path: Path | str, config: FinalistSelectionConfig | None = None) -> pd.DataFrame:
    config = config or FinalistSelectionConfig()
    summary = pd.read_csv(summary_path)
    frame = summary.copy()
    required = ["strategy_id", "samples", "pass_rate", "avg_total_gap", "avg_annualized_gap", "avg_drawdown_improvement"]
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"summary missing required columns: {', '.join(missing)}")
    for col in required:
        if col != "strategy_id":
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)
    eligible = frame[
        (frame["samples"] >= config.min_samples)
        & (frame["pass_rate"] >= config.min_pass_rate)
        & (frame["avg_total_gap"] >= config.min_avg_total_gap)
        & (frame["avg_annualized_gap"] >= config.min_avg_annualized_gap)
        & (frame["avg_drawdown_improvement"] >= config.min_avg_drawdown_improvement)
    ].copy()
    eligible = eligible.sort_values(
        ["pass_rate", "avg_annualized_gap", "avg_drawdown_improvement", "avg_total_gap"],
        ascending=[False, False, False, False],
    ).head(config.top_n)
    eligible["finalist_rank"] = range(1, len(eligible) + 1)
    return eligible


def build_finalist_cache_pair_manifest(
    summary_path: Path | str,
    cache_index_path: Path | str,
    output_path: Path | str,
    selection_config: FinalistSelectionConfig | None = None,
    mode: str = "rolling",
    window_lengths: tuple[int, ...] = (252, 504, 756),
    step: int = 63,
    min_bars: int = 120,
    max_symbols: int | None = None,
    windows_per_pair: int = 5,
) -> tuple[pd.DataFrame, Path, Path]:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    selection_config = selection_config or FinalistSelectionConfig()
    finalists = select_finalist_strategy_ids(summary_path, selection_config)
    specs = select_strategy_specs_by_id(finalists["strategy_id"].tolist())
    manifest = build_cache_pair_task_manifest(
        cache_index_path,
        specs,
        mode=mode,
        window_lengths=window_lengths,
        step=step,
        min_bars=min_bars,
        max_symbols=max_symbols,
        windows_per_pair=windows_per_pair,
    )
    if not manifest.empty:
        manifest = manifest.merge(
            finalists[["strategy_id", "finalist_rank", "pass_rate", "avg_total_gap", "avg_annualized_gap", "avg_drawdown_improvement"]],
            on="strategy_id",
            how="left",
            suffixes=("", "_baseline"),
        )
    manifest.to_csv(output, index=False)
    finalists_path = output.with_suffix(".finalists.csv")
    finalists.to_csv(finalists_path, index=False)
    summary = {
        "rows": int(len(manifest)),
        "symbols": int(manifest["symbol"].nunique()) if not manifest.empty and "symbol" in manifest else 0,
        "strategies": int(manifest["strategy_id"].nunique()) if not manifest.empty and "strategy_id" in manifest else 0,
        "windows": int(manifest["window_label"].nunique()) if not manifest.empty and "window_label" in manifest else 0,
        "windows_per_pair": int(windows_per_pair),
        "mode": mode,
        "selection_config": asdict(selection_config),
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
    }
    summary_path = output.with_suffix(".summary.json")
    pd.Series(summary).to_json(summary_path, force_ascii=False, indent=2)
    return manifest, finalists_path, summary_path
