from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from qbvs.backtest import compare_to_buy_hold, normalize_ohlcv, run_buy_hold, run_target_weight_backtest
from qbvs.simulation import RandomPathConfig, generate_random_paths
from qbvs.strategies import generate_signals, select_strategy_specs_by_id
from qbvs.validation import ValidationConfig, summarize_results


ROOT = Path(__file__).resolve().parents[1]
STRATEGY_IDS = [
    "bw99_boll_or_rsi_none_ma_trend_full_none",
    "bw99_none_none_ma_trend_full_none",
    "bw98_boll_or_rsi_none_ma_trend_full_none",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run resumable random stress batches for current-stage behavior candidates.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "runs/current_stage_bw99_random_stress_20260606")
    parser.add_argument("--target-paths", type=int, default=100_000)
    parser.add_argument("--batch-paths", type=int, default=2_000)
    parser.add_argument("--days", type=int, default=252)
    parser.add_argument("--base-seed", type=int, default=20260606)
    parser.add_argument("--max-batches", type=int, help="Run at most this many new batches in this invocation.")
    parser.add_argument("--strategy-ids", default=",".join(STRATEGY_IDS))
    args = parser.parse_args()

    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_dir = output_dir / "batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    strategy_ids = [part.strip() for part in args.strategy_ids.split(",") if part.strip()]
    specs = select_strategy_specs_by_id(strategy_ids)
    config = ValidationConfig()

    existing_batches = sorted(batch_dir.glob("batch_*.csv"))
    completed_batches = {int(path.stem.split("_")[1]) for path in existing_batches}
    needed_batches = (args.target_paths + args.batch_paths - 1) // args.batch_paths
    scheduled = [i for i in range(needed_batches) if i not in completed_batches]
    if args.max_batches is not None:
        scheduled = scheduled[: args.max_batches]

    for batch_index in scheduled:
        paths = min(args.batch_paths, args.target_paths - batch_index * args.batch_paths)
        seed = args.base_seed + batch_index
        random_config = RandomPathConfig(paths=paths, days=args.days, seed=seed)
        rows = run_batch(specs, random_config, config, batch_index)
        pd.DataFrame(rows).to_csv(batch_dir / f"batch_{batch_index:04d}.csv", index=False)

    results = load_results(batch_dir)
    summary = summarize_results(results)
    results.to_csv(output_dir / "validation_results.csv", index=False)
    summary.to_csv(output_dir / "strategy_summary.csv", index=False)
    status = build_status(output_dir, args, strategy_ids, results, summary, completed_batches | set(scheduled), needed_batches)
    (output_dir / "campaign_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.Series(asdict(config)).to_json(output_dir / "validation_config.json", force_ascii=False, indent=2)
    print(json.dumps(status, ensure_ascii=False, indent=2))


def run_batch(specs, random_config: RandomPathConfig, config: ValidationConfig, batch_index: int) -> list[dict[str, object]]:
    generated = generate_random_paths(random_config)
    benchmark_cache: dict[str, dict[str, object]] = {}
    rows: list[dict[str, object]] = []
    for path_offset, (regime, frame) in enumerate(generated):
        bars = normalize_ohlcv(frame)
        key = str(bars["symbol"].iloc[0])
        if key not in benchmark_cache:
            benchmark_cache[key] = run_buy_hold(bars, config.cost_model())["metrics"]
        benchmark = benchmark_cache[key]
        for spec in specs:
            try:
                signals = generate_signals(bars, spec)
                strategy = run_target_weight_backtest(bars, signals, config.cost_model())
                comparison = compare_to_buy_hold(strategy["metrics"], benchmark)
                rows.append(
                    {
                        "batch": batch_index,
                        "path_offset": path_offset,
                        "strategy_id": spec.strategy_id,
                        "symbol": key,
                        "regime": regime,
                        "start": str(pd.Timestamp(bars["datetime"].iloc[0]).date()),
                        "end": str(pd.Timestamp(bars["datetime"].iloc[-1]).date()),
                        "bars": int(len(bars)),
                        **{f"strategy_{k}": v for k, v in strategy["metrics"].items()},
                        **{f"buy_hold_{k}": v for k, v in benchmark.items()},
                        **comparison,
                    }
                )
            except Exception as exc:
                rows.append({"batch": batch_index, "path_offset": path_offset, "strategy_id": spec.strategy_id, "symbol": key, "regime": regime, "error": str(exc)})
    return rows


def load_results(batch_dir: Path) -> pd.DataFrame:
    frames = [pd.read_csv(path) for path in sorted(batch_dir.glob("batch_*.csv"))]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_status(output_dir: Path, args, strategy_ids: list[str], results: pd.DataFrame, summary: pd.DataFrame, completed_batches: set[int], needed_batches: int) -> dict[str, object]:
    per_strategy_samples = {}
    if not results.empty and "strategy_id" in results:
        per_strategy_samples = {str(k): int(v) for k, v in results.groupby("strategy_id").size().to_dict().items()}
    return {
        "schema_version": "qbvs-current-stage-random-stress-campaign-v1",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir.resolve().relative_to(ROOT)),
        "strategy_ids": strategy_ids,
        "target_paths_per_strategy": int(args.target_paths),
        "batch_paths": int(args.batch_paths),
        "days": int(args.days),
        "completed_batches": len(completed_batches),
        "needed_batches": needed_batches,
        "complete": len(completed_batches) >= needed_batches,
        "result_rows": int(len(results)),
        "per_strategy_samples": per_strategy_samples,
        "summary_rows": int(len(summary)),
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
        "live_trading": False,
        "uses_opend": False,
    }


if __name__ == "__main__":
    main()
