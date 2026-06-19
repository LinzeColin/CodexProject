from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from qbvs.reporting import build_pdf_report


BUNDLE_SCHEMA_VERSION = "qbvs-quantlab-evidence-bundle-v1"


@dataclass(frozen=True)
class QuantLabBundleConfig:
    top_n: int = 20
    min_pass_rate: float = 0.60
    min_avg_total_gap: float = -0.08
    min_avg_annualized_gap: float = -0.03
    min_avg_drawdown_improvement: float = -0.005


def export_quantlab_bundle(
    run_dir: Path | str,
    output_dir: Path | str,
    config: QuantLabBundleConfig | None = None,
) -> dict[str, Path]:
    config = config or QuantLabBundleConfig()
    source = Path(run_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    run = _load_run_artifacts(source)
    candidates = _select_candidates(run["summary"], run["engine"], config)
    copied_reports = _copy_reports(run["pdfs"], output)

    candidates_path = output / "quantlab_candidate_strategies.csv"
    payload_path = output / "quantlab_ingestion_payload.json"
    manifest_path = output / "quantlab_bundle_manifest.json"
    verification_path = output / "quantlab_bundle_verification.json"
    report_path = output / "QuantLab_Integration_Bundle_Report.pdf"

    candidates.to_csv(candidates_path, index=False)
    payload = _build_payload(source, output, run, candidates, copied_reports, config)
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    manifest = _build_manifest(source, output, run, candidates, copied_reports, config)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    verification = verify_quantlab_bundle(output)
    verification_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    build_pdf_report(
        report_path,
        "QuantLab Integration Evidence Bundle",
        _report_summary(candidates),
        [
            f"Source run: {source}",
            f"Engine: {run['engine']}; candidates: {len(candidates)}; top_n: {config.top_n}.",
            "This bundle is external evidence for QuantLab. It must not be treated as a direct database write or approved strategy insertion.",
            "Fast-screening candidates require exact validation before approval.",
        ],
    )
    return {
        "manifest": manifest_path,
        "payload": payload_path,
        "candidates": candidates_path,
        "verification": verification_path,
        "report": report_path,
    }


def verify_quantlab_bundle(bundle_dir: Path | str) -> dict[str, Any]:
    root = Path(bundle_dir)
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        "quantlab_bundle_manifest.json",
        "quantlab_ingestion_payload.json",
        "quantlab_candidate_strategies.csv",
    ]
    for name in required:
        if not (root / name).exists():
            errors.append(f"missing required artifact: {name}")

    manifest: dict[str, Any] = {}
    payload: dict[str, Any] = {}
    candidates = pd.DataFrame()
    if not errors:
        try:
            manifest = json.loads((root / "quantlab_bundle_manifest.json").read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid manifest json: {exc}")
        try:
            payload = json.loads((root / "quantlab_ingestion_payload.json").read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid payload json: {exc}")
        try:
            candidates = pd.read_csv(root / "quantlab_candidate_strategies.csv")
        except Exception as exc:
            errors.append(f"invalid candidates csv: {exc}")

    if manifest:
        if manifest.get("schema_version") != BUNDLE_SCHEMA_VERSION:
            errors.append("unsupported schema_version")
        if manifest.get("writes_quantlab_database") is not False:
            errors.append("manifest must state writes_quantlab_database=false")
        if manifest.get("writes_quantlab_source") is not False:
            errors.append("manifest must state writes_quantlab_source=false")
        for artifact in manifest.get("artifacts", []):
            path = root / artifact.get("path", "")
            if not path.exists():
                errors.append(f"manifest artifact missing on disk: {artifact.get('path')}")

    if payload:
        if payload.get("schema_version") != BUNDLE_SCHEMA_VERSION:
            errors.append("payload schema_version does not match")
        if payload.get("target_system") != "quantlab":
            errors.append("payload target_system must be quantlab")
        if payload.get("ingestion_mode") != "external_evidence_only":
            errors.append("payload ingestion_mode must be external_evidence_only")

    if not candidates.empty:
        required_cols = {
            "strategy_id",
            "approval_state",
            "requires_exact_validation",
            "pass_rate",
            "avg_total_gap",
            "avg_annualized_gap",
        }
        missing = sorted(required_cols - set(candidates.columns))
        if missing:
            errors.append(f"candidate csv missing columns: {missing}")
        if "approval_state" in candidates.columns:
            invalid = candidates["approval_state"].fillna("").ne("external_evidence_only")
            if invalid.any():
                errors.append("candidate csv contains non-external approval_state")
        if "requires_exact_validation" in candidates.columns and "engine" in candidates.columns:
            fast_mask = candidates["engine"].fillna("").eq("fast_screen")
            exact_required = candidates["requires_exact_validation"].astype(str).str.lower().isin(["true", "1", "yes"])
            if fast_mask.any() and not exact_required[fast_mask].all():
                errors.append("fast_screen candidates must require exact validation")
        if len(candidates) == 0:
            warnings.append("candidate csv is empty")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "bundle_dir": str(root),
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }


def _load_run_artifacts(run_dir: Path) -> dict[str, Any]:
    exact_summary = run_dir / "strategy_summary.csv"
    exact_results = run_dir / "validation_results.csv"
    fast_summary_path = run_dir / "fast_strategy_summary.csv"
    fast_results_path = run_dir / "fast_validation_results.csv"
    fund_summary_path = run_dir / "fund_strategy_summary.csv"
    fund_results_path = run_dir / "fund_validation_results.csv"
    if exact_summary.exists() and exact_results.exists():
        summary_path = exact_summary
        results_path = exact_results
        engine = "exact_backtest"
    elif fast_summary_path.exists() and fast_results_path.exists():
        summary_path = fast_summary_path
        results_path = fast_results_path
        engine = "fast_screen"
    elif fund_summary_path.exists() and fund_results_path.exists():
        summary_path = fund_summary_path
        results_path = fund_results_path
        engine = "alipay_fund_rules"
    else:
        raise FileNotFoundError(
            "run_dir must contain exact, fast, or fund validation result pairs: "
            f"{run_dir}"
        )
    summary = pd.read_csv(summary_path)
    results = pd.read_csv(results_path)
    pdfs = sorted(run_dir.glob("*.pdf"))
    return {
        "engine": engine,
        "summary": summary,
        "results": results,
        "summary_path": summary_path,
        "results_path": results_path,
        "pdfs": pdfs,
    }


def _select_candidates(summary: pd.DataFrame, engine: str, config: QuantLabBundleConfig) -> pd.DataFrame:
    frame = summary.copy()
    for col in ["pass_rate", "avg_total_gap", "avg_annualized_gap", "avg_drawdown_improvement"]:
        if col not in frame.columns:
            frame[col] = 0.0
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    filtered = frame[
        (frame["pass_rate"] >= config.min_pass_rate)
        & (frame["avg_total_gap"] >= config.min_avg_total_gap)
        & (frame["avg_annualized_gap"] >= config.min_avg_annualized_gap)
        & (frame["avg_drawdown_improvement"] >= config.min_avg_drawdown_improvement)
    ].copy()
    if filtered.empty:
        filtered = frame.copy()
        filtered["bundle_warning"] = "no_strategy_met_filters; exported_top_ranked_for_review_only"
    else:
        filtered["bundle_warning"] = ""
    filtered = filtered.sort_values(
        ["pass_rate", "avg_annualized_gap", "avg_drawdown_improvement", "avg_total_gap"],
        ascending=[False, False, False, False],
    ).head(config.top_n)
    filtered["engine"] = engine
    filtered["approval_state"] = "external_evidence_only"
    filtered["requires_exact_validation"] = engine == "fast_screen"
    filtered["requires_fund_rule_review"] = engine == "alipay_fund_rules"
    filtered["requires_user_approval_before_quantlab_write"] = True
    return filtered.reset_index(drop=True)


def _copy_reports(pdfs: list[Path], output: Path) -> list[dict[str, str]]:
    report_dir = output / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for path in pdfs:
        target = report_dir / path.name
        shutil.copy2(path, target)
        copied.append({"path": str(target.relative_to(output)), "source": str(path), "kind": "pdf_report"})
    return copied


def _build_manifest(
    source: Path,
    output: Path,
    run: dict[str, Any],
    candidates: pd.DataFrame,
    copied_reports: list[dict[str, str]],
    config: QuantLabBundleConfig,
) -> dict[str, Any]:
    artifacts = [
        {"path": "quantlab_candidate_strategies.csv", "kind": "candidate_strategy_table"},
        {"path": "quantlab_ingestion_payload.json", "kind": "quantlab_payload"},
        *copied_reports,
    ]
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_system": "quant_behavior_validation_system",
        "target_system": "quantlab",
        "source_run_dir": str(source),
        "bundle_dir": str(output),
        "engine": run["engine"],
        "candidate_count": int(len(candidates)),
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
        "ingestion_mode": "external_evidence_only",
        "approval_boundary": "QuantLab may read this bundle; user approval is required before writing approved strategy records.",
        "selection_config": asdict(config),
        "source_artifacts": {
            "summary": str(run["summary_path"]),
            "results": str(run["results_path"]),
        },
        "artifacts": artifacts,
    }


def _build_payload(
    source: Path,
    output: Path,
    run: dict[str, Any],
    candidates: pd.DataFrame,
    copied_reports: list[dict[str, str]],
    config: QuantLabBundleConfig,
) -> dict[str, Any]:
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_system": "quant_behavior_validation_system",
        "target_system": "quantlab",
        "ingestion_mode": "external_evidence_only",
        "source_run_dir": str(source),
        "bundle_dir": str(output),
        "engine": run["engine"],
        "user_acceptance_floor": {
            "total_return_gap_vs_buy_hold_min": config.min_avg_total_gap,
            "annualized_return_gap_vs_buy_hold_min": config.min_avg_annualized_gap,
            "drawdown_improvement_min": config.min_avg_drawdown_improvement,
            "pass_rate_min": config.min_pass_rate,
        },
        "required_quantlab_actions": [
            "read_bundle_manifest",
            "read_candidate_strategy_table",
            "display_external_evidence",
            "rerun_exact_validation_for_fast_screen_candidates",
            "require_user_approval_before_database_write",
        ],
        "reports": copied_reports,
        "candidates": candidates.to_dict(orient="records"),
    }


def _report_summary(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()
    cols = [
        "strategy_id",
        "samples",
        "pass_rate",
        "avg_total_gap",
        "avg_annualized_gap",
        "avg_drawdown_improvement",
        "avg_var_5",
        "avg_cvar_5",
    ]
    available = [col for col in cols if col in candidates.columns]
    return candidates[available].copy()
