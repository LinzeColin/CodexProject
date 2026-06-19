from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from pfi_os.config import REPORT_ROOT_DIR
from pfi_os.research.experiments import analyze_parameter_stability
from pfi_os.risk import evaluate_research_risk_gates


WORD_REPORT_TYPES = {"Backtest Word Report", "Experiment Research Report", "Strategy Review Report"}


@dataclass(frozen=True)
class ReportArtifact:
    name: str
    artifact_type: str
    date_folder: str
    size_kb: float
    path: str
    modified_time: float

    def to_row(self) -> dict[str, object]:
        row = asdict(self)
        row.pop("modified_time", None)
        return row


def collect_report_artifacts(root: Path | str | None = None) -> list[ReportArtifact]:
    report_root = Path(root) if root is not None else REPORT_ROOT_DIR
    if not report_root.exists():
        return []
    artifacts = [
        _artifact(path, report_root)
        for path in report_root.rglob("*")
        if path.is_file() and _artifact_type(path) is not None and not _is_zero_byte_word_report(path)
    ]
    return sorted(artifacts, key=lambda item: item.modified_time, reverse=True)


def report_artifacts_frame(root: Path | str | None = None) -> pd.DataFrame:
    artifacts = collect_report_artifacts(root)
    return pd.DataFrame([artifact.to_row() for artifact in artifacts])


def filter_report_artifacts_frame(
    artifacts: pd.DataFrame,
    artifact_types: list[str] | tuple[str, ...] | set[str],
    date_folders: list[str] | tuple[str, ...] | set[str] | None = None,
) -> pd.DataFrame:
    if artifacts.empty:
        return artifacts.copy()
    selected_types = set(artifact_types)
    if not selected_types:
        return artifacts.iloc[0:0].copy()
    filtered = artifacts[artifacts["artifact_type"].isin(selected_types)]
    if date_folders is None:
        return filtered.copy()
    selected_dates = set(date_folders)
    if not selected_dates:
        return filtered.iloc[0:0].copy()
    return filtered[filtered["date_folder"].isin(selected_dates)].copy()


def search_report_artifacts_frame(artifacts: pd.DataFrame, query: str) -> pd.DataFrame:
    if artifacts.empty:
        return artifacts.copy()
    normalized_query = query.strip().lower()
    if not normalized_query:
        return artifacts.copy()
    searchable_columns = [column for column in ["name", "artifact_type", "date_folder", "path"] if column in artifacts.columns]
    haystack = artifacts[searchable_columns].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    return artifacts[haystack.str.contains(normalized_query, regex=False)].copy()


def latest_report_artifact(artifacts: pd.DataFrame, artifact_types: set[str] | None = None) -> dict[str, object] | None:
    if artifacts.empty:
        return None
    selected_types = artifact_types or WORD_REPORT_TYPES
    candidates = artifacts[artifacts["artifact_type"].isin(selected_types)]
    if candidates.empty:
        return None
    return candidates.iloc[0].to_dict()


def experiment_summaries_frame(root: Path | str | None = None) -> pd.DataFrame:
    report_root = Path(root) if root is not None else REPORT_ROOT_DIR
    if not report_root.exists():
        return pd.DataFrame()
    rows = []
    for summary_path in sorted(report_root.glob("**/Experiments/**/summary.csv"), key=lambda path: path.stat().st_mtime, reverse=True):
        frame = pd.read_csv(summary_path)
        best = frame.iloc[0].to_dict() if not frame.empty else {}
        rows.append(
            {
                "experiment": summary_path.parent.name,
                "date_folder": _date_folder(summary_path, report_root),
                "run_count": int(len(frame)),
                "best_run_id": best.get("run_id", ""),
                "best_total_return": best.get("total_return", ""),
                "best_sharpe": best.get("sharpe", ""),
                "summary_path": str(summary_path),
            }
        )
    return pd.DataFrame(rows)


def run_metadata_summaries_frame(root: Path | str | None = None) -> pd.DataFrame:
    report_root = Path(root) if root is not None else REPORT_ROOT_DIR
    if not report_root.exists():
        return pd.DataFrame()
    rows = []
    for metadata_path in sorted(report_root.glob("**/RunMetadata*.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        metrics = payload.get("metrics", {})
        metadata = payload.get("metadata", {})
        risk_gate = payload.get("risk_gate", {})
        decision_quality = payload.get("decision_quality", {})
        strategy = metadata.get("strategy", {})
        backtest = metadata.get("backtest", {})
        total_return = _safe_float(metrics.get("total_return"))
        max_drawdown = _safe_float(metrics.get("max_drawdown"))
        cost_total = _safe_float(metrics.get("cost_total"))
        ending_equity = _safe_float(metrics.get("ending_equity"))
        cost_ratio = cost_total / ending_equity if ending_equity else 0.0
        rows.append(
            {
                "run": metadata_path.stem,
                "date_folder": _date_folder(metadata_path, report_root),
                "strategy_id": strategy.get("strategy_id", ""),
                "total_return": total_return,
                "annualized_return": _safe_float(metrics.get("annualized_return")),
                "sharpe": _safe_float(metrics.get("sharpe")),
                "max_drawdown": max_drawdown,
                "cost_ratio": cost_ratio,
                "trade_count": int(_safe_float(metrics.get("trade_count"))),
                "status": _run_status(total_return, max_drawdown, cost_ratio),
                "research_status": str(
                    decision_quality.get("status")
                    or risk_gate.get("status")
                    or ""
                ),
                "decision_quality_score": int(_safe_float(decision_quality.get("score"))),
                "missing_evidence_count": len(decision_quality.get("missing_evidence", []) or []),
                "initial_cash": _safe_float(backtest.get("initial_cash")),
                "metadata_path": str(metadata_path),
            }
        )
    return pd.DataFrame(rows)


def report_activity_frame(artifacts: pd.DataFrame) -> pd.DataFrame:
    columns = ["date_folder", "total_artifacts", "word_reports", "data_checks", "experiments"]
    if artifacts.empty:
        return pd.DataFrame(columns=columns)
    frame = artifacts.copy()
    grouped = frame.groupby("date_folder", dropna=False)
    rows = []
    for date_folder, group in grouped:
        rows.append(
            {
                "date_folder": str(date_folder),
                "total_artifacts": int(len(group)),
                "word_reports": int(group["artifact_type"].isin(WORD_REPORT_TYPES).sum()),
                "data_checks": int(group["artifact_type"].isin({"Data Quality", "Cross Validation"}).sum()),
                "experiments": int(group["artifact_type"].isin({"Experiment Summary", "Experiment Validation", "Walk Forward"}).sum()),
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values("date_folder").reset_index(drop=True)


def run_status_counts_frame(runs: pd.DataFrame) -> pd.DataFrame:
    columns = ["status", "count"]
    if runs.empty or "status" not in runs.columns:
        return pd.DataFrame(columns=columns)
    return (
        runs["status"]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
        .sort_values(["status"])
        .reset_index(drop=True)
    )


def strategy_run_summary_frame(runs: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "strategy_id",
        "run_count",
        "avg_total_return",
        "best_total_return",
        "avg_sharpe",
        "worst_max_drawdown",
        "avg_cost_ratio",
        "review_count",
    ]
    if runs.empty or "strategy_id" not in runs.columns:
        return pd.DataFrame(columns=columns)
    frame = runs.copy()
    frame["strategy_id"] = frame["strategy_id"].fillna("Unknown").replace("", "Unknown")
    for column in ["total_return", "sharpe", "max_drawdown", "cost_ratio"]:
        frame[column] = pd.to_numeric(frame.get(column, 0.0), errors="coerce").fillna(0.0)
    summary = (
        frame.groupby("strategy_id", dropna=False)
        .agg(
            run_count=("strategy_id", "size"),
            avg_total_return=("total_return", "mean"),
            best_total_return=("total_return", "max"),
            avg_sharpe=("sharpe", "mean"),
            worst_max_drawdown=("max_drawdown", "min"),
            avg_cost_ratio=("cost_ratio", "mean"),
            review_count=("status", lambda values: int((values.astype(str) == "Review").sum())),
        )
        .reset_index()
        .sort_values(["best_total_return", "avg_sharpe"], ascending=[False, False])
        .reset_index(drop=True)
    )
    return summary[columns]


def report_dashboard_cards(
    counts: dict[str, int],
    artifacts: pd.DataFrame,
    runs: pd.DataFrame,
    experiments: pd.DataFrame,
    date_folder_count: int,
) -> list[dict[str, object]]:
    attention_runs = 0
    if not runs.empty:
        review_mask = runs["status"].astype(str) == "Review" if "status" in runs.columns else pd.Series(False, index=runs.index)
        evidence_mask = (
            runs["research_status"].astype(str).isin({"NeedsMoreEvidence", "DoNotUse"})
            if "research_status" in runs.columns
            else pd.Series(False, index=runs.index)
        )
        attention_runs = int((review_mask | evidence_mask).sum())
    latest_date = str(artifacts["date_folder"].iloc[0]) if not artifacts.empty and "date_folder" in artifacts.columns else "None"
    return [
        {"label": "Word 报告 Word Reports", "value": int(counts.get("Word Report", 0)), "help": "正式研究报告数量"},
        {"label": "运行记录 Backtest Runs", "value": int(len(runs)), "help": "带元数据的回测运行数量"},
        {"label": "需复核/补证据 Attention", "value": attention_runs, "help": "表现需复核、关键证据缺失或研究门禁暂停的运行"},
        {"label": "实验 Experiments", "value": int(len(experiments)), "help": "参数扫描实验数量"},
        {"label": "日期目录 Date Folders", "value": int(date_folder_count), "help": f"最新日期 Latest: {latest_date}"},
    ]


def load_experiment_detail(summary_path: Path | str) -> dict[str, object]:
    path = Path(summary_path)
    summary = pd.read_csv(path)
    runs_path = path.with_name("runs.json")
    stability_path = path.with_name("stability.json")
    validation_path = path.with_name("train_test_validation.json")
    walk_forward_path = path.with_name("walk_forward_validation.json")
    runs = []
    if runs_path.exists():
        runs = json.loads(runs_path.read_text(encoding="utf-8"))
    if stability_path.exists():
        stability = json.loads(stability_path.read_text(encoding="utf-8"))
    else:
        stability = asdict(analyze_parameter_stability(summary))
    validation = {}
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
    walk_forward = {}
    if walk_forward_path.exists():
        walk_forward = json.loads(walk_forward_path.read_text(encoding="utf-8"))
    best = summary.iloc[0].to_dict() if not summary.empty else {}
    parameter_columns = [column for column in summary.columns if column.startswith("param_")]
    metric_columns = [
        column
        for column in [
            "total_return",
            "annualized_return",
            "sharpe",
            "sortino",
            "calmar",
            "max_drawdown",
            "win_rate",
            "trade_count",
            "cost_total",
            "ending_equity",
        ]
        if column in summary.columns
    ]
    risk_gate = evaluate_research_risk_gates(metrics=best, stability=stability, train_test=validation, walk_forward=walk_forward)
    return {
        "experiment": path.parent.name,
        "summary_path": str(path),
        "runs_path": str(runs_path) if runs_path.exists() else "",
        "stability_path": str(stability_path) if stability_path.exists() else "",
        "validation_path": str(validation_path) if validation_path.exists() else "",
        "walk_forward_path": str(walk_forward_path) if walk_forward_path.exists() else "",
        "run_count": int(len(summary)),
        "best_run": best,
        "best_params": {column.replace("param_", "", 1): best.get(column, "") for column in parameter_columns},
        "metric_columns": metric_columns,
        "stability": stability,
        "train_test_validation": validation,
        "walk_forward_validation": walk_forward,
        "risk_gate": asdict(risk_gate),
        "summary": summary,
        "runs": runs,
    }


def artifact_counts(root: Path | str | None = None) -> dict[str, int]:
    counts: dict[str, int] = {
        "Word Report": 0,
        "Backtest Word Report": 0,
        "Experiment Research Report": 0,
        "Strategy Review Report": 0,
        "Run Metadata": 0,
        "Data Quality": 0,
        "Cross Validation": 0,
        "Experiment Summary": 0,
        "Experiment Validation": 0,
        "Walk Forward": 0,
    }
    for artifact in collect_report_artifacts(root):
        counts[artifact.artifact_type] = counts.get(artifact.artifact_type, 0) + 1
        if artifact.artifact_type in {"Backtest Word Report", "Experiment Research Report", "Strategy Review Report"}:
            counts["Word Report"] = counts.get("Word Report", 0) + 1
    return counts


def cleanup_report_junk(root: Path | str | None = None, dry_run: bool = True) -> list[str]:
    report_root = Path(root) if root is not None else REPORT_ROOT_DIR
    if not report_root.exists():
        return []
    targets = [path for path in report_root.rglob("*") if path.is_file() and _is_report_junk(path)]
    removed = []
    for path in targets:
        removed.append(str(path))
        if not dry_run:
            path.unlink(missing_ok=True)
    return removed


def _is_report_junk(path: Path) -> bool:
    return path.name == ".DS_Store" or path.suffix.lower() == ".html" or _is_zero_byte_word_report(path)


def _is_zero_byte_word_report(path: Path) -> bool:
    return path.suffix.lower() == ".docx" and path.stat().st_size == 0


def _artifact(path: Path, root: Path) -> ReportArtifact:
    stat = path.stat()
    return ReportArtifact(
        name=path.name,
        artifact_type=_artifact_type(path) or "Other",
        date_folder=_date_folder(path, root),
        size_kb=round(stat.st_size / 1024, 2),
        path=str(path),
        modified_time=stat.st_mtime,
    )


def _artifact_type(path: Path) -> str | None:
    if path.suffix.lower() == ".docx":
        if path.name.startswith("StrategyReviewReport"):
            return "Strategy Review Report"
        if path.name.startswith("ExperimentResearchReport"):
            return "Experiment Research Report"
        return "Backtest Word Report"
    if path.name == "summary.csv" and "Experiments" in path.parts:
        return "Experiment Summary"
    if path.name == "train_test_validation.json" and "Experiments" in path.parts:
        return "Experiment Validation"
    if path.name == "walk_forward_validation.json" and "Experiments" in path.parts:
        return "Walk Forward"
    if path.suffix.lower() == ".json" and path.name.startswith("RunMetadata"):
        return "Run Metadata"
    if path.suffix.lower() == ".json" and "DataQuality" in path.parts:
        return "Data Quality"
    if path.suffix.lower() == ".json" and "CrossValidation" in path.parts:
        return "Cross Validation"
    return None


def _date_folder(path: Path, root: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return ""
    return relative.parts[0] if relative.parts else ""


def _safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _run_status(total_return: float, max_drawdown: float, cost_ratio: float) -> str:
    if total_return <= 0 or max_drawdown <= -0.25 or cost_ratio >= 0.08:
        return "Review"
    if max_drawdown <= -0.15 or cost_ratio >= 0.03:
        return "Watch"
    return "Pass"
