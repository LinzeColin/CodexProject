from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from qbvs.planning import estimate_manifest_budget, split_manifest


CAMPAIGN_SCHEMA_VERSION = "qbvs-long-run-campaign-v1"


@dataclass(frozen=True)
class CampaignConfig:
    chunk_size: int = 10_000
    workers: int = 1
    seconds_per_task: float = 0.05
    min_quality_score: float = 70.0
    skip_low_quality: bool = True
    million_test_multiplier: int = 1
    target_symbols: int = 200
    target_strategies: int = 200
    target_tests_per_strategy: int = 1_000_000
    python_executable: str = "python3"


@dataclass(frozen=True)
class PromotionConfig:
    top_n: int = 20
    min_samples: int = 1
    min_pass_rate: float = 0.60
    min_avg_total_gap: float = -0.08
    min_avg_annualized_gap: float = -0.03
    min_avg_drawdown_improvement: float = -0.005


def build_long_run_campaign(
    manifest_path: Path | str,
    output_dir: Path | str,
    config: CampaignConfig | None = None,
) -> dict[str, Path]:
    config = config or CampaignConfig()
    manifest_file = Path(manifest_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(manifest_file)
    manifest_copy = output / "campaign_manifest.csv"
    manifest.to_csv(manifest_copy, index=False)

    parts_dir = output / "manifest_parts"
    part_index = split_manifest(manifest, parts_dir, chunk_size=config.chunk_size, prefix="campaign_part")
    budget = estimate_manifest_budget(
        manifest,
        seconds_per_task=config.seconds_per_task,
        workers=config.workers,
        million_test_multiplier=config.million_test_multiplier,
    )
    commands = _build_commands(part_index, output, config)
    command_path = output / "run_commands.sh"
    command_path.write_text("\n".join(commands) + ("\n" if commands else ""), encoding="utf-8")

    status = part_index.copy()
    if status.empty:
        status = pd.DataFrame(columns=["part", "path", "tasks", "start_row", "end_row"])
    status["run_dir"] = status["part"].map(lambda part: str(output / "runs" / f"part_{int(part):04d}")) if not status.empty else []
    status["status"] = "pending"
    status["completed_tasks"] = 0
    status["failed_tasks"] = 0
    status_path = output / "campaign_status.csv"
    status.to_csv(status_path, index=False)

    plan = _build_plan(manifest_file, manifest_copy, part_index, budget, commands, config)
    plan_path = output / "campaign_plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    verification = verify_long_run_campaign(output)
    verification_path = output / "campaign_verification.json"
    verification_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "plan": plan_path,
        "manifest": manifest_copy,
        "part_index": parts_dir / "campaign_part_index.csv",
        "commands": command_path,
        "status": status_path,
        "verification": verification_path,
    }


def verify_long_run_campaign(campaign_dir: Path | str) -> dict[str, Any]:
    root = Path(campaign_dir)
    errors: list[str] = []
    warnings: list[str] = []
    required = ["campaign_plan.json", "campaign_manifest.csv", "campaign_status.csv", "run_commands.sh"]
    for name in required:
        if not (root / name).exists():
            errors.append(f"missing required artifact: {name}")
    plan: dict[str, Any] = {}
    if (root / "campaign_plan.json").exists():
        try:
            plan = json.loads((root / "campaign_plan.json").read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid campaign_plan.json: {exc}")
    if plan:
        if plan.get("schema_version") != CAMPAIGN_SCHEMA_VERSION:
            errors.append("unsupported campaign schema_version")
        for artifact in plan.get("artifacts", []):
            path = root / artifact.get("path", "")
            if not path.exists():
                errors.append(f"plan artifact missing on disk: {artifact.get('path')}")
        if plan.get("writes_quantlab_database") is not False:
            errors.append("campaign must not write QuantLab database")
        if plan.get("starts_background_processes") is not False:
            errors.append("campaign builder must not start background processes")
        target = plan.get("user_scale_target", {})
        actual = plan.get("actual_manifest_scope", {})
        if actual.get("symbols", 0) < target.get("target_symbols", 0):
            warnings.append("manifest_symbol_count_below_user_target")
        if actual.get("strategies", 0) < target.get("target_strategies", 0):
            warnings.append("manifest_strategy_count_below_user_target")
    if (root / "campaign_status.csv").exists():
        try:
            status = pd.read_csv(root / "campaign_status.csv")
            if "status" not in status.columns:
                errors.append("campaign_status.csv missing status column")
        except Exception as exc:
            errors.append(f"invalid campaign_status.csv: {exc}")
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "campaign_dir": str(root),
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }


def promote_candidates_from_summary(
    summary_path: Path | str,
    output_path: Path | str,
    config: PromotionConfig | None = None,
) -> pd.DataFrame:
    config = config or PromotionConfig()
    summary = pd.read_csv(summary_path)
    frame = summary.copy()
    for col in ["samples", "pass_rate", "avg_total_gap", "avg_annualized_gap", "avg_drawdown_improvement"]:
        if col not in frame.columns:
            frame[col] = 0
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)
    frame["promotion_state"] = "review_only"
    mask = (
        (frame["samples"] >= config.min_samples)
        & (frame["pass_rate"] >= config.min_pass_rate)
        & (frame["avg_total_gap"] >= config.min_avg_total_gap)
        & (frame["avg_annualized_gap"] >= config.min_avg_annualized_gap)
        & (frame["avg_drawdown_improvement"] >= config.min_avg_drawdown_improvement)
    )
    frame.loc[mask, "promotion_state"] = "external_candidate"
    frame["requires_quantlab_exact_rerun"] = True
    frame["requires_user_approval_before_strategy_library_write"] = True
    frame = frame.sort_values(
        ["promotion_state", "pass_rate", "avg_annualized_gap", "avg_drawdown_improvement", "avg_total_gap"],
        ascending=[True, False, False, False, False],
    ).head(config.top_n)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    meta = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "summary_path": str(summary_path),
        "output_path": str(output),
        "promotion_config": asdict(config),
        "candidate_rows": int(len(frame)),
        "external_candidate_rows": int((frame["promotion_state"] == "external_candidate").sum()),
        "writes_quantlab_database": False,
    }
    output.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return frame


def _build_commands(part_index: pd.DataFrame, output: Path, config: CampaignConfig) -> list[str]:
    commands: list[str] = []
    for _, row in part_index.iterrows():
        part = int(row["part"])
        run_dir = output / "runs" / f"part_{part:04d}"
        command = (
            f"PYTHONPATH=. {config.python_executable} -m qbvs.cli run-manifest "
            f"--manifest {row['path']} "
            f"--run-dir {run_dir} "
            f"--min-quality-score {config.min_quality_score}"
        )
        if config.skip_low_quality:
            command += " --skip-low-quality"
        commands.append(command)
    return commands


def _build_plan(
    source_manifest: Path,
    manifest_copy: Path,
    part_index: pd.DataFrame,
    budget: dict[str, object],
    commands: list[str],
    config: CampaignConfig,
) -> dict[str, Any]:
    return {
        "schema_version": CAMPAIGN_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_manifest": str(source_manifest),
        "campaign_manifest": str(manifest_copy),
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
        "starts_background_processes": False,
        "execution_mode": "manual_or_external_scheduler_runs_commands",
        "quality_gate": {
            "min_quality_score": config.min_quality_score,
            "skip_low_quality": config.skip_low_quality,
        },
        "actual_manifest_scope": {
            "tasks": budget.get("tasks", 0),
            "symbols": budget.get("symbols", 0),
            "strategies": budget.get("strategies", 0),
            "windows": budget.get("windows", 0),
            "parts": int(len(part_index)),
        },
        "user_scale_target": {
            "target_symbols": config.target_symbols,
            "target_strategies": config.target_strategies,
            "target_tests_per_strategy": config.target_tests_per_strategy,
        },
        "budget_estimate": budget,
        "artifacts": [
            {"path": "campaign_plan.json", "kind": "plan"},
            {"path": "campaign_manifest.csv", "kind": "manifest_copy"},
            {"path": "manifest_parts/campaign_part_index.csv", "kind": "part_index"},
            {"path": "campaign_status.csv", "kind": "status"},
            {"path": "run_commands.sh", "kind": "manual_run_commands"},
        ],
        "commands": commands,
    }
