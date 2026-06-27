from __future__ import annotations

from pathlib import Path

import pandas as pd


def index_runs(runs_dir: Path | str, output_dir: Path | str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    root = Path(runs_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    run_rows = []
    result_frames = []
    summary_frames = []
    for result_path in sorted(root.glob("**/validation_results.csv")):
        run_dir = result_path.parent
        summary_path = run_dir / "strategy_summary.csv"
        status_path = run_dir / "task_status.csv"
        pdf_paths = sorted(run_dir.glob("*.pdf"))
        run_rows.append(
            {
                "run_dir": str(run_dir),
                "validation_results": str(result_path),
                "strategy_summary": str(summary_path) if summary_path.exists() else "",
                "task_status": str(status_path) if status_path.exists() else "",
                "pdf_count": len(pdf_paths),
            }
        )
        try:
            results = pd.read_csv(result_path)
            results["run_dir"] = str(run_dir)
            result_frames.append(results)
        except Exception as exc:
            run_rows[-1]["validation_results_error"] = str(exc)
        if summary_path.exists():
            try:
                summary = pd.read_csv(summary_path)
                summary["run_dir"] = str(run_dir)
                summary_frames.append(summary)
            except Exception as exc:
                run_rows[-1]["strategy_summary_error"] = str(exc)
    run_index = pd.DataFrame(run_rows)
    all_results = pd.concat(result_frames, ignore_index=True) if result_frames else pd.DataFrame()
    all_summaries = pd.concat(summary_frames, ignore_index=True) if summary_frames else pd.DataFrame()
    run_index.to_csv(output / "run_index.csv", index=False)
    all_results.to_csv(output / "all_validation_results.csv", index=False)
    all_summaries.to_csv(output / "all_strategy_summaries.csv", index=False)
    market_summary = summarize_by_strategy_market(all_results)
    market_summary.to_csv(output / "strategy_market_summary.csv", index=False)
    return run_index, all_results, market_summary


def summarize_by_strategy_market(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty or "strategy_id" not in results.columns:
        return pd.DataFrame()
    frame = results.copy()
    if "error" in frame.columns:
        frame = frame[frame["error"].fillna("").astype(str).str.len() == 0]
    if frame.empty:
        return pd.DataFrame()
    if "market" not in frame.columns:
        frame["market"] = "UNKNOWN"
    grouped = frame.groupby(["strategy_id", "market"], dropna=False)
    return grouped.agg(
        samples=("strategy_id", "count"),
        pass_rate=("passes_user_floor", "mean"),
        avg_total_gap=("total_return_gap", "mean"),
        median_total_gap=("total_return_gap", "median"),
        avg_annualized_gap=("annualized_return_gap", "mean"),
        avg_drawdown_improvement=("drawdown_improvement", "mean"),
        avg_var_5=("strategy_var_5", "mean"),
        avg_cvar_5=("strategy_cvar_5", "mean"),
    ).reset_index().sort_values(
        ["pass_rate", "avg_annualized_gap", "avg_drawdown_improvement"],
        ascending=[False, False, False],
    )
