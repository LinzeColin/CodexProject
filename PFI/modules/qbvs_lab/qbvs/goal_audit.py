from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class GoalAuditConfig:
    target_symbols: int = 200
    target_strategies: int = 200
    target_tests_per_strategy: int = 1_000_000
    min_avg_total_gap: float = -0.08
    min_avg_annualized_gap: float = -0.03
    min_avg_drawdown_improvement: float = -0.005


def audit_goal_readiness(
    output_dir: Path | str,
    summary_path: Path | str,
    results_path: Path | str,
    manifest_path: Path | str | None = None,
    moomoo_probe_path: Path | str | None = None,
    handshake_ack_path: Path | str | None = None,
    config: GoalAuditConfig | None = None,
) -> dict[str, Path]:
    config = config or GoalAuditConfig()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(summary_path)
    results = pd.read_csv(results_path)
    manifest = pd.read_csv(manifest_path) if manifest_path and Path(manifest_path).exists() else pd.DataFrame()
    moomoo_probe = _read_json(moomoo_probe_path)
    handshake_ack = _read_json(handshake_ack_path)

    items = _build_audit_items(summary, results, manifest, moomoo_probe, handshake_ack, config)
    items_frame = pd.DataFrame([asdict(item) for item in items])
    score = _score_items(items)
    audit = {
        "schema_version": "qbvs-goal-readiness-audit-v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "summary_path": str(summary_path),
        "results_path": str(results_path),
        "manifest_path": str(manifest_path) if manifest_path else "",
        "moomoo_probe_path": str(moomoo_probe_path) if moomoo_probe_path else "",
        "handshake_ack_path": str(handshake_ack_path) if handshake_ack_path else "",
        "config": asdict(config),
        "score": score,
        "items": [asdict(item) for item in items],
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
    }

    json_path = output / "goal_readiness_audit.json"
    csv_path = output / "goal_readiness_audit.csv"
    pdf_path = output / "Goal_Readiness_Audit_Report.pdf"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    items_frame.to_csv(csv_path, index=False)
    _write_audit_pdf(pdf_path, audit, items_frame)
    return {"json": json_path, "csv": csv_path, "pdf": pdf_path}


@dataclass(frozen=True)
class AuditItem:
    requirement_id: str
    requirement: str
    status: str
    evidence: str
    gap: str
    next_action: str


def _build_audit_items(
    summary: pd.DataFrame,
    results: pd.DataFrame,
    manifest: pd.DataFrame,
    moomoo_probe: dict[str, Any],
    handshake_ack: dict[str, Any],
    config: GoalAuditConfig,
) -> list[AuditItem]:
    strategy_count = _nunique(results, "strategy_id")
    symbol_count = _nunique(results, "symbol")
    result_rows = int(len(results))
    manifest_rows = int(len(manifest)) if not manifest.empty else 0
    top = _top_candidate(summary)
    passed_floor_count = int(pd.to_numeric(results.get("passes_user_floor", pd.Series(dtype=float)), errors="coerce").fillna(0).astype(bool).sum())
    expected_pair_rows = config.target_symbols * config.target_strategies
    target_effective_tests = config.target_strategies * config.target_tests_per_strategy

    items = [
        AuditItem(
            "strategy_scope_200",
            "Validate at least 200 meaningful behavior-strategy variants.",
            "passed" if strategy_count >= config.target_strategies else "partial",
            f"Observed {strategy_count} unique strategy_id values in validation_results.csv.",
            "" if strategy_count >= config.target_strategies else f"Need {config.target_strategies - strategy_count} more strategy variants.",
            "Keep strategy generation curated; avoid low-value combinations.",
        ),
        AuditItem(
            "symbol_scope_200",
            "Validate at least 200 tradable-candidate symbols across markets and asset classes.",
            "passed" if symbol_count >= config.target_symbols else "partial",
            f"Observed {symbol_count} unique symbols in validation_results.csv.",
            "" if symbol_count >= config.target_symbols else f"Need {config.target_symbols - symbol_count} more symbols.",
            "Replace public fallback symbols with Moomoo/Alipay confirmed tradable symbols when data gates are ready.",
        ),
        AuditItem(
            "pair_baseline_40000",
            "Produce a complete 200-symbol by 200-strategy exact pair baseline.",
            "passed" if result_rows >= expected_pair_rows else "partial",
            f"Observed {result_rows} validation rows; expected pair baseline is {expected_pair_rows}.",
            "" if result_rows >= expected_pair_rows else f"Need {expected_pair_rows - result_rows} more exact pair rows.",
            "Use this as the current public-history interoperability baseline.",
        ),
        AuditItem(
            "user_return_floor",
            "Candidate behavior strategies must keep average total-return gap >= -8% and annualized gap >= -3%.",
            "passed" if _candidate_passes_floor(top, config) else "partial",
            _candidate_evidence(top),
            "" if _candidate_passes_floor(top, config) else "Top candidate does not satisfy every configured floor.",
            "Promote only external_candidate rows and rerun finalists in QuantLab before approval.",
        ),
        AuditItem(
            "downside_protection",
            "Candidate behavior strategies should improve drawdown or avoid materially worse drawdown.",
            "passed" if float(top.get("avg_drawdown_improvement", -999.0)) >= config.min_avg_drawdown_improvement else "partial",
            f"Top candidate avg_drawdown_improvement={float(top.get('avg_drawdown_improvement', 0.0)):.6f}.",
            "" if float(top.get("avg_drawdown_improvement", -999.0)) >= config.min_avg_drawdown_improvement else "Drawdown improvement floor not met.",
            "Stress finalists on bear/crash/high-volatility windows before strategy-library approval.",
        ),
        AuditItem(
            "real_tradable_moomoo_gate",
            "Moomoo/OpenD must be ready before claiming account-level tradable-market validation.",
            "passed" if bool(moomoo_probe.get("ready_for_fetch")) else "blocked",
            f"ready_for_fetch={moomoo_probe.get('ready_for_fetch')}; errors={moomoo_probe.get('errors')}.",
            "Moomoo/OpenD SDK or account data gate is not ready." if not bool(moomoo_probe.get("ready_for_fetch")) else "",
            "Install/enable futu or moomoo SDK, verify OpenD login and permissions, then run cache-moomoo-history plan.",
        ),
        AuditItem(
            "quantlab_handshake_ack",
            "QuantLab must return a real accepted handshake ack before calling integration complete.",
            "passed" if _handshake_accepted(handshake_ack) else "missing",
            f"accepted={handshake_ack.get('accepted')}; entrypoint={handshake_ack.get('quantlab_entrypoint')}.",
            "Real quantlab_handshake_ack.json is missing or not accepted." if not _handshake_accepted(handshake_ack) else "",
            "Run the same instruction on the QuantLab side and write handoff/quantlab_handshake_ack.json.",
        ),
        AuditItem(
            "million_scale_execution",
            "Reach at least 1,000,000 tests per strategy before final production-level claim.",
            "partial" if result_rows >= expected_pair_rows else "missing",
            f"Current exact public-history rows={result_rows}; target effective tests across {config.target_strategies} strategies is {target_effective_tests}.",
            "Executed evidence is far below the million-scale target.",
            "Use fast screening for pruning, then distributed/resumable exact campaigns for finalist strategies.",
        ),
        AuditItem(
            "formal_artifacts",
            "Provide machine-readable and PDF-first artifacts for QuantLab and user review.",
            "passed",
            "This command writes goal_readiness_audit.json, goal_readiness_audit.csv, and Goal_Readiness_Audit_Report.pdf.",
            "",
            "Keep PDF reports as formal deliverables and JSON/CSV as auxiliary evidence.",
        ),
        AuditItem(
            "read_only_quantlab_boundary",
            "Independent validation must not write QuantLab source or database in this workflow.",
            "passed",
            "Audit artifacts are written only under the QBVS output directory.",
            "",
            "QuantLab-side ingestion must remain ReviewOnly until user approval and exact rerun gates pass.",
        ),
    ]
    return items


def _read_json(path: Path | str | None) -> dict[str, Any]:
    if not path:
        return {}
    file = Path(path)
    if not file.exists():
        return {}
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"read_error": str(exc)}


def _nunique(frame: pd.DataFrame, col: str) -> int:
    return int(frame[col].nunique()) if col in frame.columns else 0


def _top_candidate(summary: pd.DataFrame) -> dict[str, Any]:
    if summary.empty:
        return {}
    frame = summary.copy()
    for col in ["samples", "pass_rate", "avg_total_gap", "avg_annualized_gap", "avg_drawdown_improvement"]:
        if col not in frame.columns:
            frame[col] = 0
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)
    frame = frame.sort_values(
        ["pass_rate", "avg_annualized_gap", "avg_drawdown_improvement", "avg_total_gap"],
        ascending=[False, False, False, False],
    )
    return frame.iloc[0].to_dict()


def _candidate_passes_floor(candidate: dict[str, Any], config: GoalAuditConfig) -> bool:
    if not candidate:
        return False
    return (
        float(candidate.get("avg_total_gap", -999.0)) >= config.min_avg_total_gap
        and float(candidate.get("avg_annualized_gap", -999.0)) >= config.min_avg_annualized_gap
        and float(candidate.get("avg_drawdown_improvement", -999.0)) >= config.min_avg_drawdown_improvement
    )


def _candidate_evidence(candidate: dict[str, Any]) -> str:
    if not candidate:
        return "No strategy_summary.csv rows available."
    return (
        f"Top candidate={candidate.get('strategy_id')}; "
        f"samples={int(float(candidate.get('samples', 0)))}; "
        f"pass_rate={float(candidate.get('pass_rate', 0.0)):.4f}; "
        f"avg_total_gap={float(candidate.get('avg_total_gap', 0.0)):.6f}; "
        f"avg_annualized_gap={float(candidate.get('avg_annualized_gap', 0.0)):.6f}."
    )


def _handshake_accepted(ack: dict[str, Any]) -> bool:
    return (
        ack.get("protocol_version") == "qbvs-quantlab-handshake-v1"
        and ack.get("message_type") == "handshake_ack"
        and ack.get("source_system") == "quantlab"
        and ack.get("target_system") == "quant_behavior_validation_system"
        and ack.get("accepted") is True
        and bool(ack.get("quantlab_entrypoint"))
    )


def _score_items(items: list[AuditItem]) -> dict[str, Any]:
    weights = {"passed": 1.0, "partial": 0.5, "blocked": 0.25, "missing": 0.0}
    total = sum(weights.get(item.status, 0.0) for item in items)
    max_total = len(items)
    return {
        "passed": sum(1 for item in items if item.status == "passed"),
        "partial": sum(1 for item in items if item.status == "partial"),
        "blocked": sum(1 for item in items if item.status == "blocked"),
        "missing": sum(1 for item in items if item.status == "missing"),
        "readiness_score": round(total / max_total, 4) if max_total else 0.0,
        "readiness_percent": round(total / max_total * 100, 2) if max_total else 0.0,
    }


def _write_audit_pdf(path: Path, audit: dict[str, Any], items: pd.DataFrame) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
    story: list[Any] = [
        Paragraph("QBVS Goal Readiness Audit", styles["Title"]),
        Paragraph(f"Generated at {audit['created_at']}", styles["Normal"]),
        Spacer(1, 10),
        Paragraph(
            f"Readiness score: {audit['score']['readiness_percent']:.2f}%. "
            "This audit checks the original behavior-strategy validation goal without redefining unfinished gates as complete.",
            styles["BodyText"],
        ),
        Spacer(1, 10),
    ]
    table_cols = ["requirement_id", "status", "evidence", "gap", "next_action"]
    table_data = [table_cols] + items[table_cols].astype(str).values.tolist()
    table = Table(table_data, repeatRows=1, colWidths=[82, 48, 148, 120, 134])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 6.2),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    doc.build(story)
