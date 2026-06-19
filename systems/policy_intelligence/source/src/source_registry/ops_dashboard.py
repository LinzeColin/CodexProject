from __future__ import annotations

import html
import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .monitor import build_monitor_status
from .reference_gaps import gap_action_label, gap_type_label


def write_ops_dashboard(
    path: str | Path,
    conn: sqlite3.Connection,
    *,
    data_dir: str | Path = "data",
    analysis_mode: str = "template",
    min_external_references: int = 5,
    min_external_platforms: int = 2,
    quality_rules_file: str | Path | None = None,
    title: str = "政策智能运营总览",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_ops_dashboard(
            conn,
            data_dir=data_dir,
            analysis_mode=analysis_mode,
            min_external_references=min_external_references,
            min_external_platforms=min_external_platforms,
            quality_rules_file=quality_rules_file,
            title=title,
        ),
        encoding="utf-8",
    )
    return str(output)


def render_ops_dashboard(
    conn: sqlite3.Connection,
    *,
    data_dir: str | Path = "data",
    analysis_mode: str = "template",
    min_external_references: int = 5,
    min_external_platforms: int = 2,
    quality_rules_file: str | Path | None = None,
    title: str = "政策智能运营总览",
) -> str:
    status = build_monitor_status(
        conn,
        data_dir,
        analysis_mode,
        min_external_references=min_external_references,
        min_external_platforms=min_external_platforms,
        quality_rules_file=quality_rules_file,
        queue_limit=20,
    )
    context = _ops_context(conn, status, analysis_mode)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #667085;
      --line: #d0d5dd;
      --paper: #f4f6f8;
      --panel: #ffffff;
      --blue: #155eef;
      --teal: #0b6477;
      --green: #177245;
      --amber: #9a4a13;
      --red: #9b2c2c;
      --soft: #f8fafc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
      line-height: 1.55;
    }}
    .page {{ max-width: 1320px; margin: 0 auto; padding: 24px 20px 52px; }}
    .hero {{ background: var(--panel); border-top: 5px solid var(--teal); border-bottom: 1px solid var(--line); padding: 18px 0 16px; }}
    .hero h1 {{ margin: 2px 0 8px; color: #063f4b; font-size: 28px; line-height: 1.22; }}
    .hero p {{ margin: 0; color: var(--muted); }}
    .metrics {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
    .metric {{ padding: 10px 12px; border-right: 1px solid var(--line); min-height: 70px; }}
    .metric:last-child {{ border-right: 0; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; color: #063f4b; font-size: 22px; }}
    .grid {{ display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 12px; }}
    .panel {{ grid-column: span 6; background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; }}
    .panel.third {{ grid-column: span 4; }}
    .panel.wide {{ grid-column: 1 / -1; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    .note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    .bars {{ display: grid; gap: 8px; }}
    .bar {{ display: grid; grid-template-columns: minmax(110px, 170px) 1fr 46px; gap: 8px; align-items: center; font-size: 12px; }}
    .label {{ overflow-wrap: anywhere; }}
    .track {{ height: 10px; border: 1px solid #d5e2e6; background: #e7eef1; }}
    .fill {{ display: block; height: 100%; background: var(--teal); }}
    .fill.green {{ background: var(--green); }}
    .fill.amber {{ background: var(--amber); }}
    .fill.red {{ background: var(--red); }}
    .fill.blue {{ background: var(--blue); }}
    .value {{ color: #063f4b; font-weight: 700; text-align: right; }}
    .stack {{ display: flex; min-height: 18px; border: 1px solid var(--line); background: #e7eef1; }}
    .seg {{ min-width: 2px; }}
    .seg.completed, .seg.generated {{ background: var(--green); }}
    .seg.failed, .seg.pending {{ background: var(--red); }}
    .seg.running, .seg.skipped {{ background: var(--amber); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .status-pill {{ display: inline-block; padding: 2px 7px; border: 1px solid var(--line); background: var(--soft); }}
    .ok {{ color: var(--green); font-weight: 700; }}
    .warn {{ color: var(--amber); font-weight: 700; }}
    .risk {{ color: var(--red); font-weight: 700; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    @media (max-width: 980px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .panel, .panel.third {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 620px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .bar {{ grid-template-columns: 96px 1fr 38px; }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Policy Intelligence Operations Dashboard</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(generated_at)}｜分析模式：{html.escape(analysis_mode)}｜该页面不展示 API key、cookie、账号密码或本地 secret 路径。</p>
    </section>
    <section class="metrics">
      {_metric("待生产报告", context["pending_queue"])}
      {_metric("外部缺口", context["pending_gaps"])}
      {_metric("缺搜索 Key", context["missing_search_keys"], "risk" if context["missing_search_keys"] else "ok")}
      {_metric("缺平台授权", context["missing_platform_auth"], "risk" if context["missing_platform_auth"] else "ok")}
      {_metric("质量门槛", "达标" if context["quality_met"] else "未达标", "ok" if context["quality_met"] else "risk")}
    </section>
    <section class="grid">
      {_quality_panel(status)}
      {_quality_rules_panel(status)}
      {_next_actions_panel(context)}
      {_queue_table(context["queue_preview"])}
      {_gap_table(context["gap_preview"])}
      {_coverage_link_panel()}
    </section>
  </main>
</body>
</html>
"""


def _ops_context(conn: sqlite3.Connection, status: Mapping[str, Any], analysis_mode: str) -> dict[str, Any]:
    queue_status_counts = Counter(str(row["status"]) for row in _queue_status_rows(conn, analysis_mode))
    gaps = _gap_rows(conn)
    pending_gaps = [row for row in gaps if str(row.get("status") or "pending") == "pending"]
    gap_action_counts = Counter(str(row.get("required_action") or "unknown") for row in pending_gaps)
    generated_reports = _generated_report_count(conn, analysis_mode)
    quality = status.get("quality_gate") or {}
    return {
        "run_total": _run_count(conn),
        "generated_reports": generated_reports,
        "pending_queue": int(queue_status_counts.get("pending", 0)),
        "pending_gaps": len(pending_gaps),
        "quality_met": bool(quality.get("met")),
        "missing_search_keys": int(gap_action_counts.get("provide_search_api_key", 0)),
        "missing_platform_auth": int(gap_action_counts.get("provide_platform_auth", 0)),
        "gap_action_counts": gap_action_counts,
        "gap_platform_counts": Counter(str(row.get("platform") or "unknown") for row in pending_gaps),
        "queue_preview": (status.get("queue") or {}).get("preview") or [],
        "gap_preview": (status.get("external_reference_gaps") or {}).get("preview") or [],
    }


def _run_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS count FROM pipeline_runs").fetchone()
    return int(row["count"] if row else 0)


def _queue_status_rows(
    conn: sqlite3.Connection,
    analysis_mode: str,
    status: str | None = None,
) -> list[dict[str, Any]]:
    params: list[Any] = [analysis_mode]
    where = "WHERE analysis_mode = ?"
    if status:
        where += " AND status = ?"
        params.append(status)
    rows = conn.execute(
        f"SELECT status, primary_industry, industry_bucket FROM report_queue {where}",
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def _gap_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT status, required_action, platform FROM external_reference_gaps"
    ).fetchall()
    return [dict(row) for row in rows]


def _generated_report_count(conn: sqlite3.Connection, analysis_mode: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM report_queue
        WHERE analysis_mode = ? AND status = 'generated'
        """,
        (analysis_mode,),
    ).fetchone()
    return int(row["count"] if row else 0)


def _metric(label: str, value: object, klass: str = "") -> str:
    class_attr = f' class="{html.escape(klass)}"' if klass else ""
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong{class_attr}>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _quality_panel(status: Mapping[str, Any]) -> str:
    quality = status.get("quality_gate") or {}
    external = status.get("external_collection") or {}
    gap_total = max(1, int((status.get("external_reference_gaps") or {}).get("pending_count") or 0))
    rows = [
        ("有效外部参考", int(quality.get("external_reference_count") or 0), int(quality.get("min_external_references") or 5), "green"),
        ("外部平台覆盖", int(quality.get("external_platform_count") or 0), int(quality.get("min_external_platforms") or 2), "blue"),
        ("缺搜索 key", int(external.get("interpretation_missing_api_keys") or 0), gap_total, "red"),
        ("需平台授权", int(external.get("interpretation_auth_missing") or 0), gap_total, "amber"),
        ("授权采集结果", int(external.get("authorized_public_results") or 0), gap_total, "green"),
    ]
    return (
        '<article class="panel wide"><h2>质量门槛与外部采集</h2>'
        f'<section class="bars">{"".join(_ratio_bar(label, value, target, klass) for label, value, target, klass in rows)}</section>'
        f'<p class="note">质量门槛：{"达标" if quality.get("met") else "未达标"}；平台：{html.escape(", ".join(quality.get("platforms") or []) or "暂无")}。</p>'
        "</article>"
    )


def _quality_rules_panel(status: Mapping[str, Any]) -> str:
    rules = status.get("quality_gate_rules") or {}
    results = list(rules.get("gate_results") or [])
    if not results:
        return '<article class="panel wide"><h2>规则化质量门槛</h2><p class="note">暂无规则状态。</p></article>'
    counts = Counter(str(item.get("status") or "not_checked") for item in results)
    rows = [
        ("passed", int(counts.get("passed", 0)), "green"),
        ("failed", int(counts.get("failed", 0)), "red"),
        ("not_checked", int(counts.get("not_checked", 0)), "amber"),
    ]
    maximum = max([value for _, value, _ in rows] + [1])
    preview = "".join(
        f'<span class="status-pill">{html.escape(str(item.get("label") or item.get("id") or ""))}：{html.escape(str(item.get("status") or ""))}</span> '
        for item in results
    )
    return (
        '<article class="panel wide"><h2>规则化质量门槛</h2>'
        f'<section class="bars">{"".join(_bar_row(label, value, maximum, klass) for label, value, klass in rows)}</section>'
        f'<p>{preview}</p>'
        '<p class="note">完整规则见 <a href="quality_gates_dashboard.html">reports/quality_gates_dashboard.html</a>；not_checked 表示当前运行缺少可验证证据。</p>'
        "</article>"
    )


def _ratio_bar(label: str, value: int, target: int, klass: str) -> str:
    pct = 0 if target <= 0 else min(100, round(value / target * 100, 1))
    return (
        '<div class="bar">'
        f'<span class="label">{html.escape(label)}</span>'
        f'<span class="track"><span class="fill {html.escape(klass)}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(str(value))}/{html.escape(str(target))}</span>'
        "</div>"
    )


def _next_actions_panel(context: Mapping[str, Any]) -> str:
    rows = [
        (gap_action_label(k), v, _gap_action_class(k))
        for k, v in context["gap_action_counts"].most_common(6)
    ]
    if not rows:
        return '<article class="panel wide"><h2>下一步动作</h2><p class="note">暂无待处理动作。</p></article>'
    maximum = max([value for _, value, _ in rows] + [1])
    return (
        '<article class="panel wide"><h2>下一步动作</h2>'
        f'<section class="bars">{"".join(_bar_row(label, value, maximum, klass) for label, value, klass in rows)}</section>'
        '<p class="note">只展示直接影响报告质量门槛的动作；详细筛选和批量复核见 external_reference_gap_dashboard.html。</p></article>'
    )


def _bar_row(label: str, value: int, maximum: int, klass: str) -> str:
    pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
    class_attr = f" {klass}" if klass else ""
    return (
        '<div class="bar">'
        f'<span class="label">{html.escape(str(label))}</span>'
        f'<span class="track"><span class="fill{html.escape(class_attr)}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(str(value))}</span>'
        "</div>"
    )


def _queue_table(items: list[Mapping[str, Any]]) -> str:
    rows = []
    for position, item in enumerate(items[:12], start=1):
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(position))}</td>"
            f"<td>{html.escape(str(item.get('industry_rank') or ''))}</td>"
            f"<td>{html.escape(str(item.get('industry') or ''))}</td>"
            f"<td>{html.escape(_truncate(str(item.get('title') or ''), 70))}</td>"
            f"<td>{html.escape(str(item.get('source_name') or ''))}</td>"
            f"<td>{html.escape(str(item.get('sort_time') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>待生产队列</h2>'
        '<table><thead><tr><th>队列序</th><th>行业优先级</th><th>行业</th><th>标题</th><th>来源</th><th>时间</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"6\">暂无待生产报告。</td></tr>"}</tbody></table>'
        '<p class="note">队列序是当前 pending 报告的实际生产顺序；行业优先级只用于排序，不代表报告编号。</p></article>'
    )


def _gap_table(items: list[Mapping[str, Any]]) -> str:
    rows = []
    for item in items[:12]:
        gap_type = str(item.get("gap_type") or "")
        action = str(item.get("required_action") or "")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('priority_score') or 0))}</td>"
            f"<td>{html.escape(str(item.get('platform') or ''))}</td>"
            f"<td>{html.escape(gap_type_label(gap_type))}</td>"
            f"<td>{html.escape(gap_action_label(action))}</td>"
            f"<td class=\"cmd\">{html.escape(str(item.get('gap_id') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>外部参考缺口</h2>'
        '<table><thead><tr><th>优先级</th><th>平台</th><th>缺口</th><th>动作</th><th>gap_id</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"5\">暂无待处理缺口。</td></tr>"}</tbody></table></article>'
    )


def _coverage_link_panel() -> str:
    return (
        '<article class="panel wide"><h2>全网覆盖入口</h2>'
        '<p><a href="access_readiness_dashboard.html">全网接入验收</a> ｜ <a href="automation_readiness_dashboard.html">自动化就绪</a> ｜ <a href="setup_wizard_dashboard.html">本地接入验收</a> ｜ <a href="search_secret_intake_dashboard.html">搜索 API 接入</a> ｜ <a href="platform_coverage_dashboard.html">平台覆盖矩阵</a> ｜ <a href="platform_parser_dashboard.html">平台解析器</a> ｜ <a href="platform_parser_validation_dashboard.html">解析器验收</a> ｜ <a href="platform_parser_sample_dashboard.html">样本验收</a> ｜ <a href="crawl_policy_dashboard.html">抓取策略</a> ｜ <a href="attachment_parser_dashboard.html">附件解析</a> ｜ <a href="external_reference_gap_dashboard.html">缺口复核</a></p>'
        '<p><a href="quality_gates_dashboard.html">质量门槛</a> ｜ <a href="report_artifact_check_dashboard.html">报告自检</a> ｜ <a href="benchmark_dashboard.html">模型对标</a></p>'
        '<p class="note">总览只保留影响交付的决策入口；步骤日志、凭据体检、搜索验证和授权验证在专项 dashboard 中查看。</p>'
        "</article>"
    )


def _gap_action_class(action: str) -> str:
    if action in {"provide_search_api_key", "provide_platform_auth"}:
        return "red"
    if action in {"review_candidate_url", "refine_public_site_search", "retry_request"}:
        return "amber"
    return "blue"


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: max(0, limit - 3)] + "..."


def ops_dashboard_summary(conn: sqlite3.Connection, analysis_mode: str = "template") -> dict[str, Any]:
    status = build_monitor_status(conn, "data", analysis_mode)
    context = _ops_context(conn, status, analysis_mode)
    return {
        "run_total": context["run_total"],
        "generated_reports": context["generated_reports"],
        "pending_queue": context["pending_queue"],
        "pending_gaps": context["pending_gaps"],
        "quality_met": context["quality_met"],
    }
