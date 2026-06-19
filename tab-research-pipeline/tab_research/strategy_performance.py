from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


STRATEGY_PERFORMANCE_JSON_LATEST = "strategy_performance_latest.json"
STRATEGY_PERFORMANCE_MD_LATEST = "strategy_performance_latest.md"
STRATEGY_PERFORMANCE_PDF_LATEST = "strategy_performance_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_strategy_performance_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_strategy_performance(output_dir, db_path)
    json_path = output_dir / STRATEGY_PERFORMANCE_JSON_LATEST
    md_path = output_dir / STRATEGY_PERFORMANCE_MD_LATEST
    pdf_path = output_dir / STRATEGY_PERFORMANCE_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_strategy_performance_markdown(payload))
    pdf_summary = write_strategy_performance_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_strategy_performance(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_strategy_performance(output_dir: Path, db_path: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    recs, runs = load_recommendation_history(db_path)
    position_monitor = load_json(output_dir / "position_monitor_latest.json")
    latest_commit = load_json(output_dir / "latest_commit.json")
    run_rows = build_run_rows(recs, runs)
    board_rows = build_board_rows(recs)
    ev_bucket_rows = build_ev_bucket_rows(recs)
    clv_rows = build_clv_readiness_rows(recs, position_monitor)
    summary = summarize_performance(recs, run_rows, board_rows, ev_bucket_rows, clv_rows, latest_commit, position_monitor)
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "strategy_performance_dashboard",
        "purpose": "把历史推荐、EV/Edge、仓位、门禁状态、CLV/ROI 复盘准备度和新旧变化沉淀为策略表现 Dashboard；没有真实结算或收盘赔率时明确标记 outcome_pending，不伪造收益。",
        "executive_status": {
            "status": "tracking_ready_outcome_pending" if summary["recommendation_count"] else "no_recommendation_history",
            "realized_roi_status": summary["realized_roi_status"],
            "clv_tracking_status": summary["clv_tracking_status"],
            "current_action": "继续积累真实结算/收盘赔率，当前仅做 EV/Edge 研究样本回测准备。" if summary["settled_bet_count"] == 0 else "结合真实结算结果校准 EV/Edge。",
            "primary_gap": primary_gap(summary),
            "recommended_next_action": recommended_next_action(summary),
        },
        "summary": summary,
        "run_rows": run_rows,
        "board_rows": board_rows,
        "ev_bucket_rows": ev_bucket_rows,
        "clv_readiness_rows": clv_rows,
        "old_new_compare": old_new_compare(db_path, summary, board_rows, ev_bucket_rows),
        "calibration_policy": {
            "source_template": "football_betting_analysis_ABC_template.xlsx / 下注日志",
            "roi_formula": "ROI = settled_profit / settled_stake；未结算时显示 outcome_pending。",
            "clv_formula": "CLV% = entry_odds / closing_odds - 1；未抓到收盘赔率时显示 clv_pending。",
            "expected_profit_formula": "expected_profit_aud = stake_aud × expected_value。",
            "weighted_ev_formula": "stake_weighted_ev = Σ(stake × EV) / Σ(stake)。",
            "interpretation": "当前阶段先用 EV/Edge/仓位和门禁状态做研究样本审计；真实 ROI/CLV 只在有私有结算和收盘赔率证据时计算。",
        },
        "evidence_layers": [
            {"layer": "FACT", "text": "历史推荐来自 SQLite recommendations/report_runs。"},
            {"layer": "FACT", "text": "真实持仓和收益率只有在 position_monitor snapshot_ready=true 时可用。"},
            {"layer": "INFERENCE", "text": "预期收益、EV 分桶、样本覆盖和回测准备度由本地统计计算。"},
            {"layer": "OBSERVATION", "text": "当前缺少可公开展示的真实收盘赔率和结算结果，因此 ROI/CLV 不做确定性结论。"},
        ],
        "truthfulness_note": "本报告不伪造赛果、收盘赔率、CLV 或 ROI；缺失时统一标记 outcome_pending / clv_pending。",
        "safety_note": "该报告只用于自动化策略复盘和概率校准，不自动下注、不点击赔率、不添加 Bet Slip。",
    }
    return sanitize_public_payload(payload)


def load_recommendation_history(db_path: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if not Path(db_path).exists():
        return [], {}
    try:
        uri = f"file:{Path(db_path).resolve()}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            recs = [dict(row) for row in conn.execute("SELECT * FROM recommendations ORDER BY id")]
            runs = {
                str(row["run_id"]): dict(row)
                for row in conn.execute(
                    "SELECT run_id, status, report_date, started_at, finished_at, raw_refresh_ready, safety_ready, portfolio_ready, time_adjusted_new_exposure_aud FROM report_runs"
                )
            }
        finally:
            conn.close()
        return [normalize_recommendation(row, runs.get(str(row.get("run_id")) or "", {})) for row in recs], runs
    except sqlite3.Error:
        return [], {}


def normalize_recommendation(row: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    raw = parse_json(row.get("raw_json"))
    edge = raw.get("edge")
    probability = row.get("probability")
    odds = row.get("odds")
    if edge is None and probability is not None and odds:
        try:
            edge = float(probability) - 1 / float(odds)
        except (TypeError, ValueError, ZeroDivisionError):
            edge = None
    ev = row.get("expected_value")
    stake = float(row.get("stake_aud") or 0)
    return {
        "run_id": str(row.get("run_id") or ""),
        "report_date": str(run.get("report_date") or ""),
        "run_status": str(run.get("status") or ""),
        "raw_refresh_ready": bool(run.get("raw_refresh_ready")),
        "safety_ready": bool(run.get("safety_ready")),
        "portfolio_ready": bool(run.get("portfolio_ready")),
        "board_id": str(row.get("board_id") or ""),
        "board_name": str(row.get("board_name") or ""),
        "rank": int(row.get("rank") or 0),
        "event_name": str(row.get("event_name") or ""),
        "market": str(row.get("market") or ""),
        "selection": str(row.get("selection") or ""),
        "odds": to_float(odds),
        "probability": to_float(probability),
        "expected_value": to_float(ev),
        "edge": to_float(edge),
        "stake_aud": stake,
        "action": str(row.get("action") or ""),
        "buy_like": stake > 0,
        "expected_profit_aud": round(stake * float(ev), 2) if ev is not None else 0.0,
        "risk_flags": int((raw.get("event_risk") or {}).get("flag_count") or 0),
        "settlement_status": "outcome_pending",
        "clv_status": "clv_pending",
    }


def build_run_rows(recs: list[dict[str, Any]], runs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in recs:
        by_run[rec["run_id"]].append(rec)
    rows = []
    for run_id, items in by_run.items():
        run = runs.get(run_id, {})
        buy_items = [item for item in items if item["buy_like"]]
        stake = sum(item["stake_aud"] for item in buy_items)
        ev_values = [float(item["expected_value"]) for item in buy_items if item.get("expected_value") is not None]
        expected_profit = sum(item["expected_profit_aud"] for item in buy_items)
        rows.append(
            {
                "run_id": run_id,
                "report_date": str(run.get("report_date") or ""),
                "status": str(run.get("status") or ""),
                "recommendation_count": len(items),
                "buy_count": len(buy_items),
                "research_stake_aud": round(stake, 2),
                "expected_profit_aud": round(expected_profit, 2),
                "stake_weighted_ev": round(expected_profit / stake, 4) if stake else 0.0,
                "average_ev": round(sum(ev_values) / len(ev_values), 4) if ev_values else 0.0,
                "raw_refresh_ready": bool(run.get("raw_refresh_ready")),
                "portfolio_ready": bool(run.get("portfolio_ready")),
                "outcome_coverage": 0.0,
                "clv_coverage": 0.0,
                "status_note": "真实 ROI/CLV 待结算和收盘赔率；当前只做 EV/Edge 样本审计。",
            }
        )
    return sorted(rows, key=lambda row: (row.get("report_date") or "", row.get("run_id") or ""))[-20:]


def build_board_rows(recs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_board: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in recs:
        by_board[rec["board_name"] or rec["board_id"]].append(rec)
    rows = []
    for board, items in by_board.items():
        buy_items = [item for item in items if item["buy_like"]]
        stake = sum(item["stake_aud"] for item in buy_items)
        expected_profit = sum(item["expected_profit_aud"] for item in buy_items)
        ev_values = [float(item["expected_value"]) for item in buy_items if item.get("expected_value") is not None]
        edges = [float(item["edge"]) for item in buy_items if item.get("edge") is not None]
        rows.append(
            {
                "board": board,
                "recommendation_count": len(items),
                "buy_count": len(buy_items),
                "research_stake_aud": round(stake, 2),
                "expected_profit_aud": round(expected_profit, 2),
                "stake_weighted_ev": round(expected_profit / stake, 4) if stake else 0.0,
                "average_ev": round(sum(ev_values) / len(ev_values), 4) if ev_values else 0.0,
                "average_edge": round(sum(edges) / len(edges), 4) if edges else 0.0,
                "positive_ev_count": sum(1 for item in buy_items if (item.get("expected_value") or 0) > 0),
                "outcome_status": "outcome_pending",
            }
        )
    return sorted(rows, key=lambda row: (row["research_stake_aud"], row["recommendation_count"]), reverse=True)


def build_ev_bucket_rows(recs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = [
        ("EV < 0", None, 0.0),
        ("0% <= EV < 5%", 0.0, 0.05),
        ("5% <= EV < 10%", 0.05, 0.10),
        ("EV >= 10%", 0.10, None),
        ("EV missing", "missing", "missing"),
    ]
    rows = []
    buy_items = [item for item in recs if item["buy_like"]]
    for label, low, high in buckets:
        if low == "missing":
            items = [item for item in buy_items if item.get("expected_value") is None]
        elif low is None:
            items = [item for item in buy_items if item.get("expected_value") is not None and float(item["expected_value"]) < float(high)]
        elif high is None:
            items = [item for item in buy_items if item.get("expected_value") is not None and float(item["expected_value"]) >= float(low)]
        else:
            items = [item for item in buy_items if item.get("expected_value") is not None and float(low) <= float(item["expected_value"]) < float(high)]
        stake = sum(item["stake_aud"] for item in items)
        expected_profit = sum(item["expected_profit_aud"] for item in items)
        rows.append(
            {
                "bucket": label,
                "buy_count": len(items),
                "research_stake_aud": round(stake, 2),
                "expected_profit_aud": round(expected_profit, 2),
                "stake_weighted_ev": round(expected_profit / stake, 4) if stake else 0.0,
                "settled_count": 0,
                "settled_roi": None,
                "status": "tracking_ready_outcome_pending" if items else "empty_bucket",
            }
        )
    return rows


def build_clv_readiness_rows(recs: list[dict[str, Any]], position_monitor: dict[str, Any]) -> list[dict[str, Any]]:
    buy_count = sum(1 for item in recs if item["buy_like"])
    snapshot_ready = bool((position_monitor.get("summary") or {}).get("snapshot_ready"))
    return [
        {
            "metric": "入场赔率",
            "status": "ready",
            "coverage_count": buy_count,
            "coverage_rate": 1.0 if buy_count else 0.0,
            "evidence": "recommendations.odds",
            "next_action": "保持每次推荐都记录入场赔率。",
        },
        {
            "metric": "收盘赔率",
            "status": "clv_pending",
            "coverage_count": 0,
            "coverage_rate": 0.0,
            "evidence": "closing odds source missing",
            "next_action": "后续 raw refresh 增加开赛前/收盘赔率快照，才能计算 CLV%。",
        },
        {
            "metric": "结算结果",
            "status": "outcome_pending" if snapshot_ready else "private_snapshot_pending",
            "coverage_count": 0,
            "coverage_rate": 0.0,
            "evidence": "TAB My Bets private snapshot" if snapshot_ready else "position_monitor snapshot_ready=false",
            "next_action": "只读导入已下注持仓和结算结果后，按 settled stake 计算 ROI。",
        },
        {
            "metric": "复盘样本",
            "status": "sample_ready",
            "coverage_count": buy_count,
            "coverage_rate": 1.0 if buy_count else 0.0,
            "evidence": "历史 buy-like recommendations",
            "next_action": "样本先按 EV bucket 和板块分布观察，不用短期输赢改模型。",
        },
    ]


def summarize_performance(
    recs: list[dict[str, Any]],
    run_rows: list[dict[str, Any]],
    board_rows: list[dict[str, Any]],
    ev_bucket_rows: list[dict[str, Any]],
    clv_rows: list[dict[str, Any]],
    latest_commit: dict[str, Any],
    position_monitor: dict[str, Any],
) -> dict[str, Any]:
    buy_items = [item for item in recs if item["buy_like"]]
    stake = sum(item["stake_aud"] for item in buy_items)
    expected_profit = sum(item["expected_profit_aud"] for item in buy_items)
    ev_values = [float(item["expected_value"]) for item in buy_items if item.get("expected_value") is not None]
    edge_values = [float(item["edge"]) for item in buy_items if item.get("edge") is not None]
    board_counts = Counter(item["board_name"] for item in buy_items)
    return {
        "latest_report_date": str(latest_commit.get("report_date") or ""),
        "run_count": len({item["run_id"] for item in recs}),
        "recommendation_count": len(recs),
        "buy_recommendation_count": len(buy_items),
        "board_count": len(board_rows),
        "research_stake_aud": round(stake, 2),
        "expected_profit_aud": round(expected_profit, 2),
        "stake_weighted_ev": round(expected_profit / stake, 4) if stake else 0.0,
        "average_ev": round(sum(ev_values) / len(ev_values), 4) if ev_values else 0.0,
        "average_edge": round(sum(edge_values) / len(edge_values), 4) if edge_values else 0.0,
        "positive_ev_buy_count": sum(1 for item in buy_items if (item.get("expected_value") or 0) > 0),
        "settled_bet_count": 0,
        "settled_stake_aud": 0.0,
        "realized_profit_aud": 0.0,
        "realized_roi": None,
        "realized_roi_status": "outcome_pending",
        "clv_coverage_count": 0,
        "clv_coverage_rate": 0.0,
        "clv_tracking_status": "clv_pending",
        "snapshot_ready": bool((position_monitor.get("summary") or {}).get("snapshot_ready")),
        "top_board_by_research_stake": board_rows[0]["board"] if board_rows else "",
        "buy_distribution_by_board": dict(board_counts),
        "ev_bucket_count": len(ev_bucket_rows),
        "clv_readiness_metric_count": len(clv_rows),
        "backtest_readiness_score": backtest_readiness_score(buy_items, clv_rows, position_monitor),
    }


def old_new_compare(db_path: Path, summary: dict[str, Any], board_rows: list[dict[str, Any]], ev_bucket_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"status": "no_previous_snapshot", "buy_count_delta": 0, "stake_delta_aud": 0}
    try:
        with connect_report_db(db_path) as conn:
            previous = conn.execute(
                """
                SELECT generated_at, buy_recommendation_count, research_stake_aud,
                       stake_weighted_ev, payload_json
                FROM strategy_performance_snapshots
                ORDER BY generated_at DESC
                LIMIT 1
                """
            ).fetchone()
    except sqlite3.Error as exc:
        if "no such table" in str(exc).lower():
            return {"status": "no_previous_snapshot", "buy_count_delta": 0, "stake_delta_aud": 0}
        return {"status": "compare_unavailable", "buy_count_delta": 0, "stake_delta_aud": 0}
    if not previous:
        return {"status": "no_previous_snapshot", "buy_count_delta": 0, "stake_delta_aud": 0}
    previous_payload = parse_json(previous["payload_json"])
    previous_boards = {row.get("board") for row in previous_payload.get("board_rows") or [] if isinstance(row, dict)}
    current_boards = {row.get("board") for row in board_rows}
    previous_buckets = {row.get("bucket"): row for row in previous_payload.get("ev_bucket_rows") or [] if isinstance(row, dict)}
    bucket_deltas = []
    for row in ev_bucket_rows:
        old = previous_buckets.get(row.get("bucket")) or {}
        bucket_deltas.append({"bucket": row.get("bucket"), "buy_count_delta": int(row.get("buy_count") or 0) - int(old.get("buy_count") or 0)})
    return {
        "status": "compared",
        "previous_generated_at": previous["generated_at"],
        "buy_count_delta": int(summary.get("buy_recommendation_count") or 0) - int(previous["buy_recommendation_count"] or 0),
        "stake_delta_aud": round(float(summary.get("research_stake_aud") or 0) - float(previous["research_stake_aud"] or 0), 2),
        "stake_weighted_ev_delta": round(float(summary.get("stake_weighted_ev") or 0) - float(previous["stake_weighted_ev"] or 0), 4),
        "new_boards": sorted(current_boards - previous_boards)[:8],
        "removed_boards": sorted(previous_boards - current_boards)[:8],
        "ev_bucket_deltas": bucket_deltas,
    }


def persist_strategy_performance(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_performance_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    recommendation_count INTEGER NOT NULL DEFAULT 0,
                    buy_recommendation_count INTEGER NOT NULL DEFAULT 0,
                    research_stake_aud REAL NOT NULL DEFAULT 0,
                    expected_profit_aud REAL NOT NULL DEFAULT 0,
                    stake_weighted_ev REAL NOT NULL DEFAULT 0,
                    settled_bet_count INTEGER NOT NULL DEFAULT 0,
                    realized_roi_status TEXT NOT NULL DEFAULT '',
                    clv_tracking_status TEXT NOT NULL DEFAULT '',
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO strategy_performance_snapshots(
                    snapshot_id, generated_at, status, recommendation_count,
                    buy_recommendation_count, research_stake_aud, expected_profit_aud,
                    stake_weighted_ev, settled_bet_count, realized_roi_status,
                    clv_tracking_status, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(public_payload.get("snapshot_id") or ""),
                    str(public_payload.get("generated_at") or ""),
                    str(executive.get("status") or ""),
                    int(summary.get("recommendation_count") or 0),
                    int(summary.get("buy_recommendation_count") or 0),
                    float(summary.get("research_stake_aud") or 0),
                    float(summary.get("expected_profit_aud") or 0),
                    float(summary.get("stake_weighted_ev") or 0),
                    int(summary.get("settled_bet_count") or 0),
                    str(summary.get("realized_roi_status") or ""),
                    str(summary.get("clv_tracking_status") or ""),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {
            "status": "stored",
            "database": Path(db_path).name,
            "table": "strategy_performance_snapshots",
            "snapshot_id": str(public_payload.get("snapshot_id") or ""),
        }
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def render_strategy_performance_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA 策略表现 / CLV / ROI 回测 Dashboard",
        "",
        "本报告把历史推荐、EV/Edge、仓位、门禁状态和回测准备度汇总为策略复盘面板。没有真实结算或收盘赔率时，不计算虚假 ROI/CLV。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- recommendation_count: `{summary.get('recommendation_count', 0)}`",
        f"- buy_recommendation_count: `{summary.get('buy_recommendation_count', 0)}`",
        f"- research_stake_aud: `{money(summary.get('research_stake_aud'))}`",
        f"- expected_profit_aud: `{money(summary.get('expected_profit_aud'))}`",
        f"- stake_weighted_ev: `{pct(summary.get('stake_weighted_ev'))}`",
        f"- average_edge: `{pp(summary.get('average_edge'))}`",
        f"- realized_roi_status: `{summary.get('realized_roi_status', '')}`",
        f"- clv_tracking_status: `{summary.get('clv_tracking_status', '')}`",
        f"- backtest_readiness_score: `{pct(summary.get('backtest_readiness_score'))}`",
        f"- recommended_next_action: {md(executive.get('recommended_next_action'))}",
        "",
        "## 新旧变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- buy_count_delta: `{compare.get('buy_count_delta', 0)}`",
        f"- stake_delta_aud: `{money(compare.get('stake_delta_aud', 0))}`",
        f"- stake_weighted_ev_delta: `{pp(compare.get('stake_weighted_ev_delta', 0))}`",
        "",
        "## 板块表现",
        "",
        "| 板块 | 推荐数 | 买入样本 | 研究金额 | 预期收益 | 加权EV | 平均Edge | 真实结果 |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload.get("board_rows") or []:
        lines.append(
            f"| {md(row.get('board'))} | {row.get('recommendation_count', 0)} | {row.get('buy_count', 0)} | {money(row.get('research_stake_aud'))} | {money(row.get('expected_profit_aud'))} | {pct(row.get('stake_weighted_ev'))} | {pp(row.get('average_edge'))} | {md(row.get('outcome_status'))} |"
        )
    lines.extend(
        [
            "",
            "## EV 分桶",
            "",
            "| EV桶 | 买入样本 | 研究金额 | 预期收益 | 加权EV | 结算ROI | 状态 |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload.get("ev_bucket_rows") or []:
        lines.append(
            f"| {md(row.get('bucket'))} | {row.get('buy_count', 0)} | {money(row.get('research_stake_aud'))} | {money(row.get('expected_profit_aud'))} | {pct(row.get('stake_weighted_ev'))} | {md(row.get('settled_roi') if row.get('settled_roi') is not None else 'outcome_pending')} | {md(row.get('status'))} |"
        )
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}", "", f"> {payload.get('safety_note', '')}"])
    return "\n".join(lines)


def write_strategy_performance_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    board_rows = payload.get("board_rows") or []
    run_rows = payload.get("run_rows") or []
    ev_rows = payload.get("ev_bucket_rows") or []
    clv_rows = payload.get("clv_readiness_rows") or []
    compare = payload.get("old_new_compare") or {}
    charts = [
        chart_from_items("研究金额 by 板块", [(row.get("board", ""), row.get("research_stake_aud", 0)) for row in board_rows], "#1F4E79"),
        chart_from_items("预期收益 by 板块", [(row.get("board", ""), max(0.0, float(row.get("expected_profit_aud") or 0))) for row in board_rows], "#247A5A"),
        chart_from_items("EV 分桶买入数", [(row.get("bucket", ""), row.get("buy_count", 0)) for row in ev_rows], "#6A4C93"),
        chart_from_items("近20次 run 加权EV", [(row.get("report_date") or row.get("run_id", "")[-6:], max(0.0, float(row.get("stake_weighted_ev") or 0) * 100)) for row in run_rows], "#A56710"),
        chart_from_items("CLV/ROI 覆盖", [(row.get("metric", ""), float(row.get("coverage_rate") or 0) * 100) for row in clv_rows], "#C7352B"),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 策略表现 / CLV / ROI 回测 Dashboard",
        subtitle="历史推荐样本、EV/Edge、仓位、CLV/ROI 准备度和新旧变化；缺少真实结算时不伪造 ROI。",
        summary_rows=[
            ("status", str((payload.get("executive_status") or {}).get("status", ""))),
            ("recommendations", str(summary.get("recommendation_count", 0))),
            ("buy samples", str(summary.get("buy_recommendation_count", 0))),
            ("research stake", money(summary.get("research_stake_aud"))),
            ("expected profit", money(summary.get("expected_profit_aud"))),
            ("stake weighted EV", pct(summary.get("stake_weighted_ev"))),
            ("realized ROI", str(summary.get("realized_roi_status", ""))),
            ("CLV", str(summary.get("clv_tracking_status", ""))),
            ("backtest readiness", pct(summary.get("backtest_readiness_score"))),
        ],
        charts=charts,
        table_headers=["板块", "推荐数", "买入", "研究金额", "预期收益", "加权EV", "结果"],
        table_rows=[
            [
                str(row.get("board", "")),
                str(row.get("recommendation_count", 0)),
                str(row.get("buy_count", 0)),
                money(row.get("research_stake_aud")),
                money(row.get("expected_profit_aud")),
                pct(row.get("stake_weighted_ev")),
                str(row.get("outcome_status", "")),
            ]
            for row in board_rows
        ],
        extra_tables=[
            {
                "title": "EV 分桶",
                "headers": ["EV桶", "买入", "研究金额", "预期收益", "加权EV", "状态"],
                "rows": [
                    [
                        str(row.get("bucket", "")),
                        str(row.get("buy_count", 0)),
                        money(row.get("research_stake_aud")),
                        money(row.get("expected_profit_aud")),
                        pct(row.get("stake_weighted_ev")),
                        str(row.get("status", "")),
                    ]
                    for row in ev_rows
                ],
            },
            {
                "title": "CLV/ROI 准备度",
                "headers": ["指标", "状态", "覆盖", "证据", "下一步"],
                "rows": [
                    [str(row.get("metric", "")), str(row.get("status", "")), pct(row.get("coverage_rate")), str(row.get("evidence", "")), str(row.get("next_action", ""))]
                    for row in clv_rows
                ],
            },
            {
                "title": "近20次 run",
                "headers": ["日期", "状态", "推荐", "买入", "研究金额", "加权EV"],
                "rows": [
                    [
                        str(row.get("report_date", "")),
                        str(row.get("status", "")),
                        str(row.get("recommendation_count", 0)),
                        str(row.get("buy_count", 0)),
                        money(row.get("research_stake_aud")),
                        pct(row.get("stake_weighted_ev")),
                    ]
                    for row in run_rows
                ],
            },
            {
                "title": "新旧策略表现变化",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous_generated_at", str(compare.get("previous_generated_at", ""))],
                    ["buy_count_delta", str(compare.get("buy_count_delta", 0))],
                    ["stake_delta_aud", money(compare.get("stake_delta_aud", 0))],
                    ["stake_weighted_ev_delta", pp(compare.get("stake_weighted_ev_delta", 0))],
                ],
            },
        ],
    )


def backtest_readiness_score(buy_items: list[dict[str, Any]], clv_rows: list[dict[str, Any]], position_monitor: dict[str, Any]) -> float:
    if not buy_items:
        return 0.0
    score = 0.35
    if any(item.get("expected_value") is not None for item in buy_items):
        score += 0.25
    if any(item.get("edge") is not None for item in buy_items):
        score += 0.15
    if bool((position_monitor.get("summary") or {}).get("snapshot_ready")):
        score += 0.15
    if any(row.get("status") == "ready" and row.get("metric") == "收盘赔率" for row in clv_rows):
        score += 0.10
    return round(min(1.0, score), 4)


def primary_gap(summary: dict[str, Any]) -> str:
    if summary.get("settled_bet_count", 0) == 0:
        return "真实结算结果缺失"
    if summary.get("clv_coverage_count", 0) == 0:
        return "收盘赔率缺失"
    return "无关键复盘缺口"


def recommended_next_action(summary: dict[str, Any]) -> str:
    if summary.get("settled_bet_count", 0) == 0:
        return "先导入只读 My Bets 结算快照；在此之前只展示 EV/Edge 样本，不计算真实 ROI。"
    if summary.get("clv_coverage_count", 0) == 0:
        return "增加收盘赔率快照，启用 CLV% 统计。"
    return "按 EV bucket 和 CLV/ROI 偏差校准下注阈值。"


def snapshot_id(generated_at: str) -> str:
    return "strategy-performance-" + str(generated_at or "").replace(":", "").replace("+", "-").replace(".", "-")


def to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_json(value: Any) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def money(value: Any) -> str:
    try:
        return f"AUD {float(value):,.0f}"
    except (TypeError, ValueError):
        return "AUD 0"


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


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
