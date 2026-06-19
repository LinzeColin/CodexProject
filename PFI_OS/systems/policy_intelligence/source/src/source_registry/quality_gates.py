from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Mapping

from .report_artifacts import inspect_report_artifacts


DEFAULT_RULE_FILE = "rules/quality_gates.json"
SOURCE_ROOT = Path(__file__).resolve().parents[2]


def load_quality_rules(path: str | Path | None = None) -> dict[str, Any]:
    rule_path = Path(path or DEFAULT_RULE_FILE).expanduser()
    if not rule_path.is_absolute() and not rule_path.exists():
        rule_path = SOURCE_ROOT / rule_path
    if not rule_path.exists():
        return {
            "version": "",
            "scope": "",
            "hard_gates": [],
            "compliance_guardrails": [],
            "operational_targets": [],
        }
    payload = json.loads(rule_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("quality gate rules must be a JSON object")
    return {
        "version": str(payload.get("version") or ""),
        "last_updated": str(payload.get("last_updated") or ""),
        "scope": str(payload.get("scope") or ""),
        "hard_gates": _mapping_list(payload.get("hard_gates")),
        "compliance_guardrails": _mapping_list(payload.get("compliance_guardrails")),
        "operational_targets": _mapping_list(payload.get("operational_targets")),
    }


def quality_rule_thresholds(path: str | Path | None = None) -> dict[str, Any]:
    rules = load_quality_rules(path)
    thresholds: dict[str, Any] = {}
    for gate in rules.get("hard_gates") or []:
        metric = str(gate.get("metric") or "")
        if metric:
            thresholds[metric] = gate.get("threshold")
    return thresholds


def build_quality_gate_status(
    *,
    rule_file: str | Path | None = None,
    metrics: Mapping[str, Any] | None = None,
    monitor_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rules = load_quality_rules(rule_file)
    merged_metrics = _metrics_from_monitor(monitor_status)
    merged_metrics.update({str(key): value for key, value in (metrics or {}).items()})
    gate_rows = [_evaluate_gate(gate, merged_metrics) for gate in rules.get("hard_gates") or []]
    summary = {
        "hard_gate_count": len(gate_rows),
        "passed_count": sum(1 for row in gate_rows if row["status"] == "passed"),
        "failed_count": sum(1 for row in gate_rows if row["status"] == "failed"),
        "not_checked_count": sum(1 for row in gate_rows if row["status"] == "not_checked"),
        "guardrail_count": len(rules.get("compliance_guardrails") or []),
        "operational_target_count": len(rules.get("operational_targets") or []),
        "all_checked_gates_passed": all(row["status"] != "failed" for row in gate_rows),
    }
    return {
        **rules,
        "summary": summary,
        "metrics": merged_metrics,
        "gate_results": gate_rows,
    }


def write_quality_gates_dashboard(
    path: str | Path,
    *,
    rule_file: str | Path | None = None,
    metrics: Mapping[str, Any] | None = None,
    monitor_status: Mapping[str, Any] | None = None,
    title: str = "报告质量门槛规则 dashboard",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    status = build_quality_gate_status(
        rule_file=rule_file,
        metrics=metrics,
        monitor_status=monitor_status,
    )
    output.write_text(render_quality_gates_dashboard(status, title=title), encoding="utf-8")
    return str(output)


def render_quality_gates_dashboard(
    status: Mapping[str, Any],
    *,
    title: str = "报告质量门槛规则 dashboard",
) -> str:
    summary = status.get("summary") or {}
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
      --teal: #0b6477;
      --green: #177245;
      --amber: #9a4a13;
      --red: #9b2c2c;
      --blue: #155eef;
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
    .metrics {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
    .metric {{ padding: 10px 12px; border-right: 1px solid var(--line); min-height: 70px; }}
    .metric:last-child {{ border-right: 0; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; color: #063f4b; font-size: 22px; }}
    .grid {{ display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 12px; }}
    .panel {{ grid-column: span 6; background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; }}
    .panel.wide {{ grid-column: 1 / -1; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    .note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    .bars {{ display: grid; gap: 8px; }}
    .bar {{ display: grid; grid-template-columns: minmax(150px, 250px) 1fr 80px; gap: 8px; align-items: center; font-size: 12px; }}
    .label {{ overflow-wrap: anywhere; }}
    .track {{ height: 10px; border: 1px solid #d5e2e6; background: #e7eef1; }}
    .fill {{ display: block; height: 100%; background: var(--teal); }}
    .fill.passed {{ background: var(--green); }}
    .fill.failed {{ background: var(--red); }}
    .fill.not_checked {{ background: var(--amber); }}
    .value {{ color: #063f4b; font-weight: 700; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .passed {{ color: var(--green); font-weight: 700; }}
    .failed {{ color: var(--red); font-weight: 700; }}
    .not_checked {{ color: var(--amber); font-weight: 700; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    @media (max-width: 900px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .panel {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 620px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .bar {{ grid-template-columns: 120px 1fr 58px; }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Declarative Quality Gates</p>
      <h1>{html.escape(title)}</h1>
      <p>版本：{html.escape(str(status.get("version") or ""))}｜范围：{html.escape(str(status.get("scope") or ""))}｜规则来自本地 JSON，不展示 secret。</p>
    </section>
    <section class="metrics">
      {_metric("硬门槛", summary.get("hard_gate_count", 0))}
      {_metric("通过", summary.get("passed_count", 0))}
      {_metric("失败", summary.get("failed_count", 0))}
      {_metric("未验证", summary.get("not_checked_count", 0))}
      {_metric("合规护栏", summary.get("guardrail_count", 0))}
      {_metric("运营目标", summary.get("operational_target_count", 0))}
    </section>
    <section class="grid">
      {_gate_bars(list(status.get("gate_results") or []))}
      {_gate_table(list(status.get("gate_results") or []))}
      {_guardrail_panel(list(status.get("compliance_guardrails") or []))}
      {_target_panel(list(status.get("operational_targets") or []))}
      {_metrics_panel(status.get("metrics") or {})}
    </section>
  </main>
</body>
</html>
"""


def _metrics_from_monitor(monitor_status: Mapping[str, Any] | None) -> dict[str, Any]:
    if not monitor_status:
        return {}
    quality = monitor_status.get("quality_gate") or {}
    report = monitor_status.get("report") or {}
    latest = monitor_status.get("latest_run") or {}
    stats = latest.get("stats") if isinstance(latest.get("stats"), Mapping) else {}
    metrics = {
        "external_reference_count": quality.get("external_reference_count"),
        "external_platform_count": quality.get("external_platform_count"),
        "primary_report_suffix": Path(str(report.get("path") or "")).suffix if report.get("path") else "",
        "report_exists": bool(report.get("exists")),
    }
    if report.get("path"):
        artifact_check = inspect_report_artifacts(str(report.get("path") or ""))
        metrics.update(
            {
                key: artifact_check.get(key)
                for key in [
                    "report_document_count",
                    "deep_chapter_count",
                    "pdf_page_count",
                    "primary_report_suffix",
                    "reference_section_estimated_pages",
                    "reference_section_compact",
                    "business_value_density_score",
                    "business_value_low_value_units",
                    "business_value_total_units",
                    "business_value_repeated_units",
                    "blank_risk",
                ]
                if artifact_check.get(key) is not None
            }
        )
    if stats:
        metrics.update(stats)
    return {key: value for key, value in metrics.items() if value is not None}


def _evaluate_gate(gate: Mapping[str, Any], metrics: Mapping[str, Any]) -> dict[str, Any]:
    metric = str(gate.get("metric") or "")
    actual = metrics.get(metric)
    if actual is None or actual == "":
        status = "not_checked"
    else:
        status = "passed" if _compare(actual, str(gate.get("operator") or ""), gate.get("threshold")) else "failed"
    return {
        "id": str(gate.get("id") or ""),
        "label": str(gate.get("label") or ""),
        "metric": metric,
        "operator": str(gate.get("operator") or ""),
        "threshold": gate.get("threshold"),
        "actual": actual if actual is not None else "",
        "status": status,
        "severity": str(gate.get("severity") or ""),
        "rationale": str(gate.get("rationale") or ""),
    }


def _compare(actual: Any, operator: str, threshold: Any) -> bool:
    if operator in {">=", ">", "<=", "<"}:
        try:
            left = float(actual)
            right = float(threshold)
        except (TypeError, ValueError):
            return False
        if operator == ">=":
            return left >= right
        if operator == ">":
            return left > right
        if operator == "<=":
            return left <= right
        return left < right
    if operator == "==":
        return str(actual) == str(threshold)
    if operator == "!=":
        return str(actual) != str(threshold)
    return False


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _gate_bars(rows: list[Mapping[str, Any]]) -> str:
    if not rows:
        return '<article class="panel wide"><h2>硬门槛状态</h2><p class="note">暂无规则。</p></article>'
    rendered = []
    for row in rows:
        status = str(row.get("status") or "not_checked")
        value = 1 if status == "passed" else 0
        rendered.append(_bar(str(row.get("label") or row.get("id") or ""), value, 1, status))
    return f'<article class="panel wide"><h2>硬门槛状态</h2><section class="bars">{"".join(rendered)}</section></article>'


def _gate_table(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows:
        status = str(row.get("status") or "")
        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('label') or ''))}</td>"
            f'<td class="{html.escape(status)}">{html.escape(status)}</td>'
            f"<td>{html.escape(str(row.get('metric') or ''))}</td>"
            f"<td>{html.escape(str(row.get('actual') if row.get('actual') != '' else '未取得'))}</td>"
            f"<td>{html.escape(str(row.get('operator') or ''))} {html.escape(str(row.get('threshold') or ''))}</td>"
            f"<td>{html.escape(str(row.get('severity') or ''))}</td>"
            f"<td>{html.escape(str(row.get('rationale') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>硬门槛明细</h2>'
        '<table><thead><tr><th>规则</th><th>状态</th><th>指标</th><th>当前值</th><th>要求</th><th>严重程度</th><th>原因</th></tr></thead>'
        f'<tbody>{"".join(rendered) if rendered else "<tr><td colspan=\"7\">暂无规则。</td></tr>"}</tbody></table></article>'
    )


def _guardrail_panel(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('label') or row.get('id') or ''))}</td>"
            f"<td>{html.escape(str(row.get('rule') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>合规护栏</h2>'
        '<table><thead><tr><th>护栏</th><th>规则</th></tr></thead>'
        f'<tbody>{"".join(rendered) if rendered else "<tr><td colspan=\"2\">暂无护栏。</td></tr>"}</tbody></table></article>'
    )


def _target_panel(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('label') or row.get('id') or ''))}</td>"
            f"<td>{html.escape(str(row.get('target') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>运营目标</h2>'
        '<table><thead><tr><th>目标</th><th>说明</th></tr></thead>'
        f'<tbody>{"".join(rendered) if rendered else "<tr><td colspan=\"2\">暂无目标。</td></tr>"}</tbody></table></article>'
    )


def _metrics_panel(metrics: Mapping[str, Any]) -> str:
    rows = []
    for key, value in sorted(metrics.items()):
        if key.lower().endswith(("key", "cookie", "secret", "session")):
            continue
        rows.append(f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>")
    return (
        '<article class="panel wide"><h2>当前可验证指标</h2>'
        '<table><tbody>'
        f'{"".join(rows) if rows else "<tr><td colspan=\"2\">当前只展示规则定义，尚未传入运行指标。</td></tr>"}'
        '</tbody></table>'
        '<p class="note">未取得指标的硬门槛显示为 not_checked，不用弱证据冒充达标。</p></article>'
    )


def _bar(label: str, value: int, maximum: int, klass: str) -> str:
    pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
    return (
        '<div class="bar">'
        f'<span class="label">{html.escape(label)}</span>'
        f'<span class="track"><span class="fill {html.escape(klass)}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(klass)}</span>'
        "</div>"
    )
