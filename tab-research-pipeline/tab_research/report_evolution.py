from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


REPORT_EVOLUTION_JSON_LATEST = "report_evolution_latest.json"
REPORT_EVOLUTION_MD_LATEST = "report_evolution_latest.md"
REPORT_EVOLUTION_PDF_LATEST = "report_evolution_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_report_evolution_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_report_evolution(output_dir, db_path)
    json_path = output_dir / REPORT_EVOLUTION_JSON_LATEST
    md_path = output_dir / REPORT_EVOLUTION_MD_LATEST
    pdf_path = output_dir / REPORT_EVOLUTION_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_report_evolution_markdown(payload))
    pdf_summary = write_report_evolution_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_report_evolution(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_report_evolution(output_dir: Path, db_path: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    report_diffs = fetch_report_diffs(db_path)
    catalog_compare = compare_latest_report_catalog(db_path)
    report_inventory = load_json(output_dir / "report_visual_inventory_latest.json")
    recommendation_operations = load_json(output_dir / "recommendation_operations_latest.json")
    strategy_performance = load_json(output_dir / "strategy_performance_latest.json")
    product_readiness = load_json(output_dir / "product_readiness_dashboard_latest.json")
    latest_commit = load_json(output_dir / "latest_commit.json")

    artifact_rows = build_artifact_rows(report_inventory)
    signal_rows = build_signal_rows(recommendation_operations, strategy_performance, product_readiness)
    summary = summarize_evolution(
        report_diffs=report_diffs,
        catalog_compare=catalog_compare,
        artifact_rows=artifact_rows,
        signal_rows=signal_rows,
        report_inventory=report_inventory,
        latest_commit=latest_commit,
    )
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "report_evolution_dashboard",
        "purpose": "把日报 diff、报告目录快照、推荐操作变化、策略表现变化和产品完成度变化合并成跨报告族新旧变化总控台；用于 automation 前的报告质量和决策闭环审计。",
        "executive_status": {
            "status": "tracking_ready" if summary["report_diff_count"] and summary["current_report_family_count"] else "partial_history",
            "evolution_score": summary["evolution_score"],
            "current_action": "继续生成并比对每次日报和报告族；raw/private 未通过时只做研究复盘，不发布新增可执行下注。",
            "primary_gap": primary_gap(summary),
            "recommended_next_action": recommended_next_action(summary),
        },
        "summary": summary,
        "report_diff_rows": report_diffs,
        "catalog_compare": catalog_compare,
        "artifact_rows": artifact_rows,
        "signal_rows": signal_rows,
        "evidence_layers": [
            {"layer": "FACT", "text": "日报级变化来自 SQLite report_diffs/report_runs。"},
            {"layer": "FACT", "text": "报告族覆盖来自 report_visual_inventory_snapshots/report_catalog_items。"},
            {"layer": "FACT", "text": "推荐操作和策略表现来自最新公开 JSON 及对应 SQLite 快照。"},
            {"layer": "INFERENCE", "text": "evolution_score 由 report diff 覆盖、报告族覆盖、新旧对比覆盖和关键业务信号覆盖综合计算。"},
        ],
        "automation_note": "该 Dashboard 可被每日 automation 只读生成，用于发现新报告相对旧报告的变化、缺失和质量退化；不自动下注。",
        "truthfulness_note": "本报告只汇总已有数据库和公开产物；不伪造 TAB live odds、结算结果、CLV 或 ROI。",
        "safety_note": "只生成研究报告和本地数据库快照，不点击赔率、不添加 Bet Slip、不提交下注。",
    }
    return sanitize_public_payload(payload)


def fetch_report_diffs(db_path: Path, limit: int = 20) -> list[dict[str, Any]]:
    if not Path(db_path).exists():
        return []
    try:
        uri = f"file:{Path(db_path).resolve()}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT report_runs.run_id, report_runs.report_date, report_runs.status,
                       report_runs.started_at, report_diffs.added_count,
                       report_diffs.removed_count, report_diffs.changed_count,
                       report_diffs.retained_count, report_diffs.exposure_change_aud
                FROM report_diffs
                LEFT JOIN report_runs ON report_runs.run_id = report_diffs.run_id
                ORDER BY COALESCE(report_runs.started_at, '') DESC, report_diffs.run_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()
        return [
            {
                "run_id": str(row["run_id"] or ""),
                "report_date": str(row["report_date"] or ""),
                "status": str(row["status"] or ""),
                "added_count": int(row["added_count"] or 0),
                "removed_count": int(row["removed_count"] or 0),
                "changed_count": int(row["changed_count"] or 0),
                "retained_count": int(row["retained_count"] or 0),
                "exposure_change_aud": round(float(row["exposure_change_aud"] or 0), 2),
            }
            for row in rows
        ]
    except sqlite3.Error:
        return []


def compare_latest_report_catalog(db_path: Path) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"status": "no_database", "rows": [], "current_report_count": 0, "previous_report_count": 0}
    try:
        uri = f"file:{Path(db_path).resolve()}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            snapshots = conn.execute(
                """
                SELECT snapshot_id, generated_at, report_count, average_score
                FROM report_visual_inventory_snapshots
                ORDER BY generated_at DESC
                LIMIT 2
                """
            ).fetchall()
            if not snapshots:
                return {"status": "no_catalog_snapshot", "rows": [], "current_report_count": 0, "previous_report_count": 0}
            current = snapshots[0]
            previous = snapshots[1] if len(snapshots) > 1 else None
            current_items = fetch_catalog_items(conn, str(current["snapshot_id"]))
            previous_items = fetch_catalog_items(conn, str(previous["snapshot_id"])) if previous else {}
        finally:
            conn.close()
    except sqlite3.Error:
        return {"status": "catalog_compare_unavailable", "rows": [], "current_report_count": 0, "previous_report_count": 0}

    rows = []
    report_ids = sorted(set(current_items) | set(previous_items))
    for report_id in report_ids:
        current_row = current_items.get(report_id) or {}
        previous_row = previous_items.get(report_id) or {}
        rows.append(
            {
                "report_id": report_id,
                "name": str(current_row.get("name") or previous_row.get("name") or report_id),
                "current_status": str(current_row.get("status") or "missing"),
                "previous_status": str(previous_row.get("status") or "missing"),
                "score_delta": round(float(current_row.get("score") or 0) - float(previous_row.get("score") or 0), 4),
                "chart_delta": int(current_row.get("chart_count") or 0) - int(previous_row.get("chart_count") or 0),
                "table_delta": int(current_row.get("table_count") or 0) - int(previous_row.get("table_count") or 0),
                "missing_capabilities": current_row.get("missing_capabilities") or [],
            }
        )
    changed = [
        row
        for row in rows
        if row["current_status"] != row["previous_status"]
        or row["score_delta"] != 0
        or row["chart_delta"] != 0
        or row["table_delta"] != 0
    ]
    return {
        "status": "compared" if previous else "no_previous_catalog_snapshot",
        "current_snapshot_id": str(current["snapshot_id"]),
        "previous_snapshot_id": str(previous["snapshot_id"]) if previous else "",
        "current_generated_at": str(current["generated_at"]),
        "previous_generated_at": str(previous["generated_at"]) if previous else "",
        "current_report_count": int(current["report_count"] or len(current_items)),
        "previous_report_count": int(previous["report_count"] or len(previous_items)) if previous else 0,
        "report_count_delta": int(current["report_count"] or len(current_items)) - (int(previous["report_count"] or len(previous_items)) if previous else 0),
        "average_score_delta": round(float(current["average_score"] or 0) - (float(previous["average_score"] or 0) if previous else 0), 4),
        "changed_report_count": len(changed),
        "new_report_ids": [row["report_id"] for row in rows if row["previous_status"] == "missing" and row["current_status"] != "missing"],
        "degraded_report_ids": [row["report_id"] for row in rows if row["score_delta"] < 0],
        "rows": rows,
    }


def fetch_catalog_items(conn: sqlite3.Connection, snapshot_id_value: str) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT report_id, name, status, score, chart_count, table_count,
               missing_capabilities_json
        FROM report_catalog_items
        WHERE snapshot_id = ?
        """,
        (snapshot_id_value,),
    ).fetchall()
    items = {}
    for row in rows:
        items[str(row["report_id"] or "")] = {
            "report_id": str(row["report_id"] or ""),
            "name": str(row["name"] or ""),
            "status": str(row["status"] or ""),
            "score": float(row["score"] or 0),
            "chart_count": int(row["chart_count"] or 0),
            "table_count": int(row["table_count"] or 0),
            "missing_capabilities": parse_list(row["missing_capabilities_json"]),
        }
    return items


def build_artifact_rows(report_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report_inventory.get("rows") or []
    result = []
    for row in rows[:24]:
        if not isinstance(row, dict):
            continue
        result.append(
            {
                "report_id": str(row.get("report_id") or ""),
                "name": str(row.get("name") or ""),
                "status": str(row.get("status") or ""),
                "score": float(row.get("score") or 0),
                "chart_count": int(row.get("chart_count") or 0),
                "table_count": int(row.get("table_count") or 0),
                "has_old_new_compare": bool(row.get("has_old_new_compare")),
                "has_automation_view": bool(row.get("has_automation_view")),
                "has_github_reference": bool(row.get("has_github_reference")),
                "next_action": str(row.get("next_action") or ""),
            }
        )
    return result


def build_signal_rows(
    recommendation_operations: dict[str, Any],
    strategy_performance: dict[str, Any],
    product_readiness: dict[str, Any],
) -> list[dict[str, Any]]:
    rec_summary = recommendation_operations.get("summary") or {}
    strat_summary = strategy_performance.get("summary") or {}
    product_summary = product_readiness.get("summary") or {}
    return [
        {
            "signal": "推荐操作",
            "status": str((recommendation_operations.get("executive_status") or {}).get("status") or ""),
            "current_value": f"候选 {rec_summary.get('candidate_count', 0)} / 可执行 AUD {float(rec_summary.get('executable_new_stake_aud') or 0):,.0f}",
            "old_new_status": str((recommendation_operations.get("old_new_compare") or {}).get("status") or ""),
            "risk_note": "raw blocked 时执行金额保持 0。",
        },
        {
            "signal": "策略表现",
            "status": str((strategy_performance.get("executive_status") or {}).get("status") or ""),
            "current_value": f"买入样本 {strat_summary.get('buy_recommendation_count', 0)} / 加权EV {pct(strat_summary.get('stake_weighted_ev'))}",
            "old_new_status": str((strategy_performance.get("old_new_compare") or {}).get("status") or ""),
            "risk_note": f"ROI={strat_summary.get('realized_roi_status', '')}；CLV={strat_summary.get('clv_tracking_status', '')}。",
        },
        {
            "signal": "产品完成度",
            "status": str((product_readiness.get("executive_status") or {}).get("status") or ""),
            "current_value": f"{product_summary.get('ready_count', 0)}/{product_summary.get('partial_count', 0)}/{product_summary.get('blocked_count', 0)} ready/partial/blocked",
            "old_new_status": str((product_readiness.get("old_new_compare") or {}).get("status") or ""),
            "risk_note": f"当前可执行新增金额 AUD {float(product_summary.get('current_executable_new_stake_aud') or 0):,.0f}。",
        },
    ]


def summarize_evolution(
    *,
    report_diffs: list[dict[str, Any]],
    catalog_compare: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    signal_rows: list[dict[str, Any]],
    report_inventory: dict[str, Any],
    latest_commit: dict[str, Any],
) -> dict[str, Any]:
    inventory_summary = report_inventory.get("summary") or {}
    ready_artifacts = sum(1 for row in artifact_rows if row.get("status") == "完整")
    total_artifacts = len(artifact_rows)
    diff_coverage = 1.0 if report_diffs else 0.0
    catalog_coverage = 1.0 if catalog_compare.get("status") in {"compared", "no_previous_catalog_snapshot"} and artifact_rows else 0.0
    old_new_coverage = (
        float(inventory_summary.get("old_new_compare_count") or 0) / float(inventory_summary.get("report_count") or 1)
        if inventory_summary.get("report_count")
        else 0.0
    )
    signal_coverage = sum(1 for row in signal_rows if row.get("status")) / len(signal_rows) if signal_rows else 0.0
    score = round((diff_coverage * 0.25) + (catalog_coverage * 0.25) + (old_new_coverage * 0.30) + (signal_coverage * 0.20), 4)
    return {
        "latest_report_date": str(latest_commit.get("report_date") or ""),
        "latest_status": str(latest_commit.get("status") or ""),
        "report_diff_count": len(report_diffs),
        "latest_diff_changed_count": int(report_diffs[0].get("changed_count") or 0) if report_diffs else 0,
        "latest_diff_exposure_change_aud": float(report_diffs[0].get("exposure_change_aud") or 0) if report_diffs else 0.0,
        "current_report_family_count": int(inventory_summary.get("report_count") or catalog_compare.get("current_report_count") or total_artifacts),
        "artifact_ready_count": ready_artifacts,
        "artifact_review_count": total_artifacts - ready_artifacts,
        "old_new_compare_count": int(inventory_summary.get("old_new_compare_count") or 0),
        "automation_view_count": int(inventory_summary.get("automation_view_count") or 0),
        "github_reference_count": int(inventory_summary.get("github_reference_count") or 0),
        "catalog_compare_status": str(catalog_compare.get("status") or ""),
        "catalog_changed_report_count": int(catalog_compare.get("changed_report_count") or 0),
        "catalog_report_count_delta": int(catalog_compare.get("report_count_delta") or 0),
        "signal_count": len(signal_rows),
        "evolution_score": score,
    }


def persist_report_evolution(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS report_evolution_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    evolution_score REAL NOT NULL DEFAULT 0,
                    report_diff_count INTEGER NOT NULL DEFAULT 0,
                    current_report_family_count INTEGER NOT NULL DEFAULT 0,
                    old_new_compare_count INTEGER NOT NULL DEFAULT 0,
                    catalog_changed_report_count INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO report_evolution_snapshots(
                    snapshot_id, generated_at, status, evolution_score,
                    report_diff_count, current_report_family_count,
                    old_new_compare_count, catalog_changed_report_count, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(public_payload.get("snapshot_id") or ""),
                    str(public_payload.get("generated_at") or ""),
                    str(executive.get("status") or ""),
                    float(summary.get("evolution_score") or 0),
                    int(summary.get("report_diff_count") or 0),
                    int(summary.get("current_report_family_count") or 0),
                    int(summary.get("old_new_compare_count") or 0),
                    int(summary.get("catalog_changed_report_count") or 0),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {
            "status": "stored",
            "database": Path(db_path).name,
            "table": "report_evolution_snapshots",
            "snapshot_id": str(public_payload.get("snapshot_id") or ""),
        }
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def render_report_evolution_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    catalog = payload.get("catalog_compare") or {}
    lines = [
        "# TAB FIFA Report Evolution / 新旧报告变化总控台",
        "",
        "本 Dashboard 汇总日报 diff、报告族覆盖、推荐操作变化、策略表现变化和产品完成度变化。它服务于每日 automation 复盘，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- evolution_score: `{pct(summary.get('evolution_score'))}`",
        f"- report_diff_count: `{summary.get('report_diff_count', 0)}`",
        f"- current_report_family_count: `{summary.get('current_report_family_count', 0)}`",
        f"- old_new_compare_count: `{summary.get('old_new_compare_count', 0)}`",
        f"- catalog_compare_status: `{summary.get('catalog_compare_status', '')}`",
        f"- recommended_next_action: {md(executive.get('recommended_next_action'))}",
        "",
        "## 报告目录新旧变化",
        "",
        f"- current_snapshot: `{catalog.get('current_snapshot_id', '')}`",
        f"- previous_snapshot: `{catalog.get('previous_snapshot_id', '')}`",
        f"- report_count_delta: `{catalog.get('report_count_delta', 0)}`",
        f"- changed_report_count: `{catalog.get('changed_report_count', 0)}`",
        "",
        "| 报告 | 当前状态 | 上次状态 | 得分变化 | 图表变化 | 附表变化 | 缺口 |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in (catalog.get("rows") or [])[:20]:
        lines.append(
            f"| {md(row.get('name'))} | {md(row.get('current_status'))} | {md(row.get('previous_status'))} | {pp(row.get('score_delta'))} | {row.get('chart_delta', 0)} | {row.get('table_delta', 0)} | {md(', '.join(row.get('missing_capabilities') or []))} |"
        )
    lines.extend(["", "## 业务信号变化", "", "| 信号 | 状态 | 当前值 | 新旧状态 | 风险说明 |", "|---|---|---|---|---|"])
    for row in payload.get("signal_rows") or []:
        lines.append(
            f"| {md(row.get('signal'))} | {md(row.get('status'))} | {md(row.get('current_value'))} | {md(row.get('old_new_status'))} | {md(row.get('risk_note'))} |"
        )
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}", "", f"> {payload.get('safety_note', '')}"])
    return "\n".join(lines)


def write_report_evolution_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    catalog = payload.get("catalog_compare") or {}
    report_diffs = payload.get("report_diff_rows") or []
    artifact_rows = payload.get("artifact_rows") or []
    signal_rows = payload.get("signal_rows") or []
    catalog_rows = catalog.get("rows") or []
    charts = [
        chart_from_items("日报 diff changed", [(row.get("report_date") or row.get("run_id", "")[-6:], row.get("changed_count", 0)) for row in report_diffs[:10]], "#1F4E79"),
        chart_from_items("报告族得分", [(row.get("name", ""), float(row.get("score") or 0) * 100) for row in artifact_rows[:10]], "#247A5A"),
        chart_from_items("目录变化", [("new", len(catalog.get("new_report_ids") or [])), ("changed", catalog.get("changed_report_count", 0)), ("degraded", len(catalog.get("degraded_report_ids") or []))], "#A56710"),
        chart_from_items("报告能力覆盖", [("old/new", summary.get("old_new_compare_count", 0)), ("automation", summary.get("automation_view_count", 0)), ("github", summary.get("github_reference_count", 0))], "#6A4C93"),
        chart_from_items("业务信号覆盖", [(row.get("signal", ""), 1 if row.get("status") else 0) for row in signal_rows], "#C7352B"),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 新旧报告变化总控台",
        subtitle="跨报告族追踪日报 diff、报告目录、推荐操作、策略表现和产品完成度变化；只读复盘，不自动下注。",
        summary_rows=[
            ("status", str((payload.get("executive_status") or {}).get("status", ""))),
            ("evolution score", pct(summary.get("evolution_score"))),
            ("report diffs", str(summary.get("report_diff_count", 0))),
            ("report families", str(summary.get("current_report_family_count", 0))),
            ("old/new coverage", f"{summary.get('old_new_compare_count', 0)}/{summary.get('current_report_family_count', 0)}"),
            ("catalog compare", str(summary.get("catalog_compare_status", ""))),
            ("current executable", "AUD 0 until raw/private/preflight pass"),
        ],
        charts=charts,
        table_headers=["报告", "当前", "上次", "得分变化", "图表Δ", "附表Δ"],
        table_rows=[
            [
                str(row.get("name", "")),
                str(row.get("current_status", "")),
                str(row.get("previous_status", "")),
                pp(row.get("score_delta")),
                str(row.get("chart_delta", 0)),
                str(row.get("table_delta", 0)),
            ]
            for row in catalog_rows[:18]
        ],
        extra_tables=[
            {
                "title": "日报 diff 历史",
                "headers": ["日期", "状态", "新增", "移除", "变化", "保留", "金额变化"],
                "rows": [
                    [
                        str(row.get("report_date", "")),
                        str(row.get("status", "")),
                        str(row.get("added_count", 0)),
                        str(row.get("removed_count", 0)),
                        str(row.get("changed_count", 0)),
                        str(row.get("retained_count", 0)),
                        money(row.get("exposure_change_aud")),
                    ]
                    for row in report_diffs[:12]
                ],
            },
            {
                "title": "业务信号",
                "headers": ["信号", "状态", "当前值", "新旧状态", "风险说明"],
                "rows": [
                    [
                        str(row.get("signal", "")),
                        str(row.get("status", "")),
                        str(row.get("current_value", "")),
                        str(row.get("old_new_status", "")),
                        str(row.get("risk_note", "")),
                    ]
                    for row in signal_rows
                ],
            },
            {
                "title": "报告族覆盖",
                "headers": ["报告", "状态", "图表", "附表", "新旧", "Automation", "GitHub"],
                "rows": [
                    [
                        str(row.get("name", "")),
                        str(row.get("status", "")),
                        str(row.get("chart_count", 0)),
                        str(row.get("table_count", 0)),
                        yes_no(row.get("has_old_new_compare")),
                        yes_no(row.get("has_automation_view")),
                        yes_no(row.get("has_github_reference")),
                    ]
                    for row in artifact_rows[:12]
                ],
            },
            {
                "title": "新旧目录摘要",
                "headers": ["字段", "值"],
                "rows": [
                    ["current_snapshot", str(catalog.get("current_snapshot_id", ""))],
                    ["previous_snapshot", str(catalog.get("previous_snapshot_id", ""))],
                    ["report_count_delta", str(catalog.get("report_count_delta", 0))],
                    ["average_score_delta", pp(catalog.get("average_score_delta", 0))],
                    ["new_reports", ", ".join(catalog.get("new_report_ids") or [])],
                    ["degraded_reports", ", ".join(catalog.get("degraded_report_ids") or [])],
                ],
            },
        ],
    )


def primary_gap(summary: dict[str, Any]) -> str:
    if not summary.get("report_diff_count"):
        return "日报 diff 历史不足"
    if not summary.get("current_report_family_count"):
        return "报告目录快照不足"
    if summary.get("old_new_compare_count", 0) < summary.get("current_report_family_count", 0):
        return "部分报告缺少新旧对比"
    return "raw/private/preflight 仍未全部恢复"


def recommended_next_action(summary: dict[str, Any]) -> str:
    if not summary.get("report_diff_count"):
        return "先保证每次日报写入 report_diffs，再开启跨报告族变化追踪。"
    if summary.get("old_new_compare_count", 0) < summary.get("current_report_family_count", 0):
        return "补齐缺少 old_new_compare 的报告族，并重跑 visual inventory。"
    return "保持该 Dashboard 随每日报告生成；raw/private/preflight 通过前继续 fail-closed。"


def snapshot_id(generated_at: str) -> str:
    return "report-evolution-" + str(generated_at or "").replace(":", "").replace("+", "-").replace(".", "-")


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not Path(path).exists():
            return {}
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_list(value: Any) -> list[Any]:
    try:
        payload = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "待校准"


def pp(value: Any) -> str:
    try:
        return f"{float(value) * 100:+.2f}pp"
    except (TypeError, ValueError):
        return "待校准"


def money(value: Any) -> str:
    try:
        return f"AUD {float(value):,.0f}"
    except (TypeError, ValueError):
        return "AUD 0"


def yes_no(value: Any) -> str:
    return "有" if bool(value) else "缺"


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
