from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import pandas as pd

from qbvs.cache import load_cache_index
from qbvs.data import load_csv
from qbvs.strategies import BehaviorStrategySpec
from qbvs.validation import ValidationConfig, summarize_results, validate_one
from qbvs.windows import rolling_windows


def build_csv_task_manifest(
    csv_path: Path | str,
    symbol: str,
    market: str,
    specs: Iterable[BehaviorStrategySpec],
    mode: str = "full",
    window_lengths: Iterable[int] = (252, 504, 756),
    step: int = 63,
    min_bars: int = 120,
) -> pd.DataFrame:
    source_path = str(Path(csv_path).resolve())
    base = load_csv(source_path, symbol=symbol, market=market)
    if mode == "full":
        windows = [("full", base)]
    elif mode == "rolling":
        windows = [(window.label, window.frame) for window in rolling_windows(base, lengths=window_lengths, step=step, min_bars=min_bars)]
    else:
        raise ValueError("mode must be full or rolling")
    rows = []
    for spec in specs:
        spec_json = json.dumps(asdict(spec), ensure_ascii=False, sort_keys=True)
        for label, frame in windows:
            window_start = str(pd.Timestamp(frame["datetime"].iloc[0]).date())
            window_end = str(pd.Timestamp(frame["datetime"].iloc[-1]).date())
            row = {
                "task_id": "",
                "source_type": "csv",
                "source_path": source_path,
                "symbol": symbol,
                "market": market,
                "mode": mode,
                "window_label": label,
                "window_start": window_start,
                "window_end": window_end,
                "bars": int(len(frame)),
                "strategy_id": spec.strategy_id,
                "spec_json": spec_json,
            }
            row["task_id"] = task_id(row)
            rows.append(row)
    return pd.DataFrame(rows)


def build_cache_task_manifest(
    cache_index_path: Path | str,
    specs: Iterable[BehaviorStrategySpec],
    mode: str = "full",
    window_lengths: Iterable[int] = (252, 504, 756),
    step: int = 63,
    min_bars: int = 120,
    max_symbols: int | None = None,
) -> pd.DataFrame:
    index = load_cache_index(cache_index_path)
    selected = index.head(max_symbols) if max_symbols else index
    frames = []
    for _, row in selected.iterrows():
        frames.append(
            build_csv_task_manifest(
                row["cache_path"],
                str(row["symbol"]),
                str(row["market"]),
                specs,
                mode=mode,
                window_lengths=window_lengths,
                step=step,
                min_bars=min_bars,
            )
        )
    manifest = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not manifest.empty:
        metadata_cols = [
            "asset_class",
            "tradability",
            "currency",
            "timezone",
            "quality_score",
            "quality_grade",
            "quality_warnings",
        ]
        available = [col for col in metadata_cols if col in selected.columns]
        if available:
            metadata = selected[["symbol", "market", "cache_path", *available]].copy()
            metadata["source_path"] = metadata["cache_path"].map(lambda value: str(Path(value).resolve()))
            metadata = metadata.drop(columns=["cache_path"])
            manifest = manifest.merge(
                metadata,
                on=["symbol", "market", "source_path"],
                how="left",
            )
    return manifest


def build_cache_pair_task_manifest(
    cache_index_path: Path | str,
    specs: Iterable[BehaviorStrategySpec],
    mode: str = "rolling",
    window_lengths: Iterable[int] = (252, 504, 756),
    step: int = 126,
    min_bars: int = 120,
    max_symbols: int | None = None,
    windows_per_pair: int = 1,
) -> pd.DataFrame:
    index = load_cache_index(cache_index_path)
    selected = index.head(max_symbols) if max_symbols else index
    metadata_cols = [
        "asset_class",
        "tradability",
        "currency",
        "timezone",
        "quality_score",
        "quality_grade",
        "quality_warnings",
    ]
    available_metadata = [col for col in metadata_cols if col in selected.columns]
    rows = []
    specs_list = list(specs)
    for _, source in selected.iterrows():
        source_path = str(Path(source["cache_path"]).resolve())
        symbol = str(source["symbol"])
        market = str(source["market"])
        base = load_csv(source_path, symbol=symbol, market=market)
        if mode == "full":
            windows = [("full", base)]
        elif mode == "rolling":
            windows = [(window.label, window.frame) for window in rolling_windows(base, lengths=window_lengths, step=step, min_bars=min_bars)]
        else:
            raise ValueError("mode must be full or rolling")
        if windows_per_pair > 0:
            windows = _select_even_windows(windows, windows_per_pair)
        for spec in specs_list:
            spec_json = json.dumps(asdict(spec), ensure_ascii=False, sort_keys=True)
            for label, frame in windows:
                window_start = str(pd.Timestamp(frame["datetime"].iloc[0]).date())
                window_end = str(pd.Timestamp(frame["datetime"].iloc[-1]).date())
                row = {
                    "task_id": "",
                    "source_type": "csv",
                    "source_path": source_path,
                    "symbol": symbol,
                    "market": market,
                    "mode": mode,
                    "window_label": label,
                    "window_start": window_start,
                    "window_end": window_end,
                    "bars": int(len(frame)),
                    "strategy_id": spec.strategy_id,
                    "spec_json": spec_json,
                }
                for field in available_metadata:
                    row[field] = source.get(field)
                row["task_id"] = task_id(row)
                rows.append(row)
    return pd.DataFrame(rows)


def _select_even_windows(windows: list[tuple[str, pd.DataFrame]], limit: int) -> list[tuple[str, pd.DataFrame]]:
    if limit <= 0 or len(windows) <= limit:
        return windows
    if limit == 1:
        return [windows[len(windows) // 2]]
    positions = [round(i * (len(windows) - 1) / (limit - 1)) for i in range(limit)]
    seen = set()
    selected = []
    for pos in positions:
        if pos in seen:
            continue
        seen.add(pos)
        selected.append(windows[pos])
    return selected


def task_id(row: dict[str, object]) -> str:
    payload = json.dumps(
        {
            "source_type": row.get("source_type"),
            "source_path": row.get("source_path"),
            "symbol": row.get("symbol"),
            "market": row.get("market"),
            "mode": row.get("mode"),
            "window_label": row.get("window_label"),
            "window_start": row.get("window_start"),
            "window_end": row.get("window_end"),
            "strategy_id": row.get("strategy_id"),
            "spec_json": row.get("spec_json"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def run_task_manifest(
    manifest_path: Path | str,
    output_dir: Path | str,
    config: ValidationConfig | None = None,
    max_tasks: int | None = None,
    resume: bool = True,
    min_quality_score: float | None = None,
    skip_low_quality: bool = False,
    cancel_after_tasks: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config = config or ValidationConfig()
    if cancel_after_tasks is not None and cancel_after_tasks < 0:
        raise ValueError("cancel_after_tasks must be non-negative")
    manifest = pd.read_csv(manifest_path)
    run_dir = Path(output_dir)
    result_dir = run_dir / "task_results"
    result_dir.mkdir(parents=True, exist_ok=True)
    selected = manifest.head(max_tasks) if max_tasks else manifest
    status_rows = []
    attempted_tasks = 0
    cancel_reason = ""
    for _, task in selected.iterrows():
        result_path = result_dir / f"{task['task_id']}.json"
        if resume and result_path.exists():
            status_rows.append({**task.to_dict(), "status": "cached", "result_path": str(result_path)})
            continue
        if cancel_after_tasks is not None and attempted_tasks >= cancel_after_tasks:
            cancel_reason = f"cancel_after_tasks={cancel_after_tasks}"
            status_rows.append(
                {
                    **task.to_dict(),
                    "status": "cancelled",
                    "result_path": "",
                    "cancellation_reason": cancel_reason,
                }
            )
            continue
        attempted_tasks += 1
        quality_decision = quality_gate_decision(task, min_quality_score=min_quality_score, skip_low_quality=skip_low_quality)
        if quality_decision["skip"]:
            skipped = {
                "task_id": task["task_id"],
                "strategy_id": task.get("strategy_id", ""),
                "symbol": task.get("symbol", ""),
                "market": task.get("market", ""),
                "error": quality_decision["reason"],
                "quality_score": quality_decision["quality_score"],
                "quality_gate": "skipped",
            }
            result_path.write_text(json.dumps(skipped, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            status_rows.append(
                {
                    **task.to_dict(),
                    "status": "skipped_quality",
                    "result_path": str(result_path),
                    "quality_gate_reason": quality_decision["reason"],
                }
            )
            continue
        try:
            result = run_one_task(task, config)
            result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            status_rows.append({**task.to_dict(), "status": "completed", "result_path": str(result_path)})
        except Exception as exc:
            error = {"task_id": task["task_id"], "strategy_id": task.get("strategy_id", ""), "symbol": task.get("symbol", ""), "error": str(exc)}
            result_path.write_text(json.dumps(error, ensure_ascii=False, indent=2), encoding="utf-8")
            status_rows.append({**task.to_dict(), "status": "failed", "result_path": str(result_path), "error": str(exc)})
    status = pd.DataFrame(status_rows)
    results = aggregate_task_results(result_dir)
    summary = summarize_results(results)
    status.to_csv(run_dir / "task_status.csv", index=False)
    results.to_csv(run_dir / "validation_results.csv", index=False)
    summary.to_csv(run_dir / "strategy_summary.csv", index=False)
    (run_dir / "validation_config.json").write_text(pd.Series(asdict(config)).to_json(force_ascii=False, indent=2), encoding="utf-8")
    run_control = {
        "manifest_path": str(Path(manifest_path)),
        "resume": bool(resume),
        "max_tasks": max_tasks,
        "cancel_after_tasks": cancel_after_tasks,
        "selected_tasks": int(len(selected)),
        "newly_attempted_tasks": int(attempted_tasks),
        "cancelled_tasks": int((status["status"] == "cancelled").sum()) if not status.empty else 0,
        "cancellation_reason": cancel_reason,
    }
    (run_dir / "run_control.json").write_text(json.dumps(run_control, ensure_ascii=False, indent=2), encoding="utf-8")
    return status, results, summary


def quality_gate_decision(
    task: pd.Series,
    min_quality_score: float | None = None,
    skip_low_quality: bool = False,
) -> dict[str, object]:
    if min_quality_score is None or not skip_low_quality:
        return {"skip": False, "reason": "", "quality_score": None}
    if "quality_score" not in task or pd.isna(task.get("quality_score")):
        return {"skip": False, "reason": "quality_score_missing", "quality_score": None}
    quality_score = float(task.get("quality_score"))
    if quality_score < float(min_quality_score):
        return {
            "skip": True,
            "reason": f"quality_score {quality_score:.2f} below minimum {float(min_quality_score):.2f}",
            "quality_score": quality_score,
        }
    return {"skip": False, "reason": "", "quality_score": quality_score}


def run_one_task(task: pd.Series, config: ValidationConfig | None = None) -> dict[str, object]:
    config = config or ValidationConfig()
    spec = BehaviorStrategySpec(**json.loads(str(task["spec_json"])))
    frame = load_csv(str(task["source_path"]), symbol=str(task["symbol"]), market=str(task["market"]))
    start = pd.Timestamp(task["window_start"])
    end = pd.Timestamp(task["window_end"])
    window = frame[(frame["datetime"] >= start) & (frame["datetime"] <= end)].reset_index(drop=True)
    result = validate_one(window, spec, config)
    result["task_id"] = str(task["task_id"])
    result["window_label"] = str(task["window_label"])
    result["source_type"] = str(task["source_type"])
    result["source_path"] = str(task["source_path"])
    for field in ["asset_class", "tradability", "quality_score", "quality_grade", "quality_warnings"]:
        if field in task and not pd.isna(task.get(field)):
            result[field] = task.get(field)
    return result


def aggregate_task_results(result_dir: Path | str) -> pd.DataFrame:
    rows = []
    for path in sorted(Path(result_dir).glob("*.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            rows.append({"task_id": path.stem, "error": str(exc)})
    return pd.DataFrame(rows)
