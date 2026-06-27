from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


def estimate_manifest_budget(
    manifest: pd.DataFrame,
    seconds_per_task: float = 0.05,
    workers: int = 1,
    million_test_multiplier: int = 1,
) -> dict[str, object]:
    tasks = int(len(manifest))
    workers = max(1, int(workers))
    effective_tasks = tasks * max(1, int(million_test_multiplier))
    total_seconds = effective_tasks * float(seconds_per_task)
    wall_seconds = total_seconds / workers
    symbols = int(manifest["symbol"].nunique()) if "symbol" in manifest else 0
    strategies = int(manifest["strategy_id"].nunique()) if "strategy_id" in manifest else 0
    windows = int(manifest["window_label"].nunique()) if "window_label" in manifest else 0
    return {
        "tasks": tasks,
        "symbols": symbols,
        "strategies": strategies,
        "windows": windows,
        "million_test_multiplier": int(million_test_multiplier),
        "effective_tasks": effective_tasks,
        "seconds_per_task": float(seconds_per_task),
        "workers": workers,
        "estimated_total_seconds": round(total_seconds, 2),
        "estimated_wall_seconds": round(wall_seconds, 2),
        "estimated_wall_minutes": round(wall_seconds / 60, 2),
        "estimated_wall_hours": round(wall_seconds / 3600, 2),
    }


def split_manifest(manifest: pd.DataFrame, output_dir: Path | str, chunk_size: int = 10_000, prefix: str = "manifest_part") -> pd.DataFrame:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    rows = []
    total = len(manifest)
    parts = math.ceil(total / chunk_size) if total else 0
    for idx in range(parts):
        start = idx * chunk_size
        end = min(start + chunk_size, total)
        part = manifest.iloc[start:end].copy()
        path = output / f"{prefix}_{idx + 1:04d}.csv"
        part.to_csv(path, index=False)
        rows.append({"part": idx + 1, "path": str(path), "tasks": int(len(part)), "start_row": start, "end_row": end - 1})
    index = pd.DataFrame(rows)
    index.to_csv(output / f"{prefix}_index.csv", index=False)
    return index


def sample_manifest_stratified(
    manifest: pd.DataFrame,
    max_tasks: int,
    output: Path | str | None = None,
    seed: int = 42,
    group_cols: tuple[str, ...] = ("symbol", "strategy_id"),
) -> pd.DataFrame:
    if max_tasks <= 0:
        raise ValueError("max_tasks must be positive")
    if manifest.empty:
        sampled = manifest.copy()
    else:
        available_group_cols = [col for col in group_cols if col in manifest.columns]
        if not available_group_cols:
            sampled = manifest.sample(n=min(max_tasks, len(manifest)), random_state=seed).reset_index(drop=True)
        else:
            groups = list(manifest.groupby(available_group_cols, dropna=False, sort=True))
            per_group = max(1, math.ceil(max_tasks / max(1, len(groups))))
            chunks = []
            for idx, (_, group) in enumerate(groups):
                n = min(per_group, len(group))
                chunks.append(group.sample(n=n, random_state=seed + idx))
            sampled = pd.concat(chunks, ignore_index=True) if chunks else manifest.head(0).copy()
            if len(sampled) > max_tasks:
                sampled = sampled.sample(n=max_tasks, random_state=seed).reset_index(drop=True)
            elif len(sampled) < max_tasks:
                existing = set(sampled["task_id"]) if "task_id" in sampled.columns else set(sampled.index)
                if "task_id" in manifest.columns:
                    remainder = manifest[~manifest["task_id"].isin(existing)]
                else:
                    remainder = manifest.drop(index=sampled.index, errors="ignore")
                needed = min(max_tasks - len(sampled), len(remainder))
                if needed > 0:
                    fill = remainder.sample(n=needed, random_state=seed + 10_000)
                    sampled = pd.concat([sampled, fill], ignore_index=True)
            sampled = sampled.sort_values([col for col in ["symbol", "strategy_id", "window_start", "window_end"] if col in sampled.columns]).reset_index(drop=True)
    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        sampled.to_csv(path, index=False)
        summary = {
            "source_rows": int(len(manifest)),
            "sampled_rows": int(len(sampled)),
            "seed": int(seed),
            "group_cols": list(group_cols),
            "symbols": int(sampled["symbol"].nunique()) if "symbol" in sampled.columns else 0,
            "strategies": int(sampled["strategy_id"].nunique()) if "strategy_id" in sampled.columns else 0,
            "windows": int(sampled["window_label"].nunique()) if "window_label" in sampled.columns else 0,
        }
        pd.Series(summary).to_json(path.with_suffix(".summary.json"), force_ascii=False, indent=2)
    return sampled
