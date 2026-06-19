from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


DEFAULT_BENCHMARK_FILE = "config/benchmark_models.json"


def load_benchmark_registry(path: str | Path | None = None) -> dict[str, Any]:
    benchmark_path = Path(path or DEFAULT_BENCHMARK_FILE)
    if not benchmark_path.exists():
        return {"last_refreshed": "", "source_note": "benchmark config missing", "models": [], "capability_targets": []}
    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("benchmark config must be a JSON object")
    models = payload.get("models") or []
    targets = payload.get("capability_targets") or []
    return {
        "last_refreshed": str(payload.get("last_refreshed") or ""),
        "source_note": str(payload.get("source_note") or ""),
        "models": [dict(item) for item in models if isinstance(item, Mapping)],
        "capability_targets": [dict(item) for item in targets if isinstance(item, Mapping)],
    }


def build_benchmark_status(path: str | Path | None = None) -> dict[str, Any]:
    registry = load_benchmark_registry(path)
    models = registry["models"]
    targets = registry["capability_targets"]
    status_counts = Counter(str(model.get("status") or "unknown") for model in models)
    family_counts = Counter(str(model.get("family") or "unknown") for model in models)
    source_counts = Counter(str(model.get("source_kind") or "unknown") for model in models)
    target_rows = _capability_rows(models, targets)
    summary = {
        "model_count": len(models),
        "open_source_count": sum(1 for model in models if str(model.get("source_kind")) == "github"),
        "commercial_count": sum(1 for model in models if str(model.get("source_kind")) == "official_site"),
        "capability_count": len(targets),
        "required_capability_count": sum(1 for target in targets if target.get("required_for_full_web")),
        "acceptance_check_count": sum(1 for model in models if model.get("acceptance_check")),
        "partial_count": int(status_counts.get("partial", 0)),
        "planned_count": int(status_counts.get("planned", 0)),
    }
    return {
        **registry,
        "summary": summary,
        "status_counts": dict(status_counts),
        "family_counts": dict(family_counts),
        "source_counts": dict(source_counts),
        "capability_rows": target_rows,
        "adoption_queue": sorted(models, key=lambda item: int(item.get("priority") or 0), reverse=True),
    }


def benchmark_model_rows(path: str | Path | None = None, *, limit: int | None = None) -> list[tuple[str, str, str]]:
    models = build_benchmark_status(path)["adoption_queue"]
    rows = [
        (
            str(model.get("name") or ""),
            str(model.get("borrowed") or model.get("focus") or ""),
            str(model.get("current_implementation") or model.get("next_implementation") or ""),
        )
        for model in models
    ]
    return rows[:limit] if limit else rows


def write_benchmark_dashboard(
    path: str | Path,
    *,
    benchmark_file: str | Path | None = None,
    title: str = "开源/商业模型对标 dashboard",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    status = build_benchmark_status(benchmark_file)
    output.write_text(render_benchmark_dashboard(status, title=title), encoding="utf-8")
    return str(output)


def render_benchmark_dashboard(
    status: Mapping[str, Any],
    *,
    title: str = "开源/商业模型对标 dashboard",
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
    .panel.third {{ grid-column: span 4; }}
    .panel.wide {{ grid-column: 1 / -1; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    .note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    .bars {{ display: grid; gap: 8px; }}
    .bar {{ display: grid; grid-template-columns: minmax(130px, 220px) 1fr 48px; gap: 8px; align-items: center; font-size: 12px; }}
    .label {{ overflow-wrap: anywhere; }}
    .track {{ height: 10px; border: 1px solid #d5e2e6; background: #e7eef1; }}
    .fill {{ display: block; height: 100%; background: var(--teal); }}
    .fill.partial {{ background: var(--amber); }}
    .fill.planned {{ background: var(--blue); }}
    .fill.required {{ background: var(--green); }}
    .value {{ color: #063f4b; font-weight: 700; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    a {{ color: var(--blue); text-decoration: none; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    @media (max-width: 980px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .panel, .panel.third {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 620px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .bar {{ grid-template-columns: 110px 1fr 40px; }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Benchmark Evidence And Capability Adoption</p>
      <h1>{html.escape(title)}</h1>
      <p>刷新日期：{html.escape(str(status.get("last_refreshed") or ""))}｜用于把“真正全网”拆成可验证能力，不展示 secret 或授权数据。</p>
    </section>
    <section class="metrics">
      {_metric("对标来源", summary.get("model_count", 0))}
      {_metric("开源 GitHub", summary.get("open_source_count", 0))}
      {_metric("商业/官网", summary.get("commercial_count", 0))}
      {_metric("能力目标", summary.get("capability_count", 0))}
      {_metric("必需能力", summary.get("required_capability_count", 0))}
      {_metric("验收标准", summary.get("acceptance_check_count", 0))}
    </section>
    <section class="grid">
      {_counter_panel("来源类型", status.get("source_counts") or {})}
      {_counter_panel("落地状态", status.get("status_counts") or {})}
      {_counter_panel("模型家族", status.get("family_counts") or {}, limit=8)}
      {_capability_panel(list(status.get("capability_rows") or []))}
      {_source_table(list(status.get("adoption_queue") or []))}
      {_adoption_queue_table(list(status.get("adoption_queue") or []))}
      {_compliance_panel(str(status.get("source_note") or ""))}
    </section>
  </main>
</body>
</html>
"""


def _capability_rows(models: list[Mapping[str, Any]], targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    model_by_capability: dict[str, list[str]] = {}
    for model in models:
        for tag in model.get("capability_tags") or []:
            model_by_capability.setdefault(str(tag), []).append(str(model.get("name") or ""))
    rows = []
    for target in targets:
        capability = str(target.get("capability") or "")
        names = model_by_capability.get(capability, [])
        rows.append(
            {
                "capability": capability,
                "label": str(target.get("label") or capability),
                "required": bool(target.get("required_for_full_web")),
                "model_count": len(names),
                "models": names,
            }
        )
    return sorted(rows, key=lambda item: (not item["required"], -int(item["model_count"]), item["label"]))


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _counter_panel(title: str, counts: Mapping[str, int], limit: int | None = None) -> str:
    rows = sorted(counts.items(), key=lambda item: int(item[1]), reverse=True)
    if limit:
        rows = rows[:limit]
    if not rows:
        return f'<article class="panel third"><h2>{html.escape(title)}</h2><p class="note">暂无数据。</p></article>'
    maximum = max([int(value) for _, value in rows] + [1])
    rendered = "".join(_bar(str(label), int(value), maximum, str(label)) for label, value in rows)
    return f'<article class="panel third"><h2>{html.escape(title)}</h2><section class="bars">{rendered}</section></article>'


def _capability_panel(rows: list[Mapping[str, Any]]) -> str:
    if not rows:
        return '<article class="panel wide"><h2>能力目标覆盖</h2><p class="note">暂无数据。</p></article>'
    maximum = max([int(row.get("model_count") or 0) for row in rows] + [1])
    rendered = "".join(
        _bar(
            str(row.get("label") or ""),
            int(row.get("model_count") or 0),
            maximum,
            "required" if row.get("required") else "",
        )
        for row in rows[:22]
    )
    return (
        '<article class="panel wide"><h2>能力目标覆盖</h2>'
        f'<section class="bars">{rendered}</section>'
        '<p class="note">数值表示有多少参考模型支撑该能力；必需能力优先进入后续实现队列。</p></article>'
    )


def _source_table(models: list[Mapping[str, Any]]) -> str:
    rows = []
    for model in models:
        tags = "".join(f'<span class="pill">{html.escape(str(tag))}</span>' for tag in model.get("capability_tags") or [])
        source_url = str(model.get("source_url") or "")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(model.get('name') or ''))}</td>"
            f"<td>{html.escape(str(model.get('source_kind') or ''))}</td>"
            f'<td><a href="{html.escape(source_url)}">{html.escape(source_url)}</a></td>'
            f"<td>{html.escape(str(model.get('focus') or ''))}</td>"
            f"<td>{tags}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>证据来源矩阵</h2>'
        '<table><thead><tr><th>模型</th><th>来源类型</th><th>证据链接</th><th>能力重点</th><th>能力标签</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"5\">暂无对标来源。</td></tr>"}</tbody></table></article>'
    )


def _adoption_queue_table(models: list[Mapping[str, Any]]) -> str:
    rows = []
    for model in models:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(model.get('priority') or ''))}</td>"
            f"<td>{html.escape(str(model.get('name') or ''))}</td>"
            f"<td>{html.escape(str(model.get('status') or ''))}</td>"
            f"<td>{html.escape(str(model.get('borrowed') or ''))}</td>"
            f"<td>{html.escape(str(model.get('current_implementation') or ''))}</td>"
            f"<td>{html.escape(str(model.get('next_implementation') or ''))}</td>"
            f"<td>{html.escape(str(model.get('acceptance_check') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>吸收能力实施队列</h2>'
        '<table><thead><tr><th>优先级</th><th>模型</th><th>状态</th><th>吸收能力</th><th>当前落地</th><th>下一步</th><th>验收标准</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"7\">暂无实施队列。</td></tr>"}</tbody></table></article>'
    )


def _compliance_panel(source_note: str) -> str:
    return (
        '<article class="panel wide"><h2>合规边界</h2>'
        f'<p>{html.escape(source_note)}</p>'
        '<p class="note">对标只吸收架构、工作流和 UI/运营能力；不复制商业平台专有数据，不绕过验证码、付费墙、访问控制或平台明确禁止的接口。</p>'
        "</article>"
    )


def _bar(label: str, value: int, maximum: int, klass: str = "") -> str:
    pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
    class_attr = f" {klass}" if klass in {"partial", "planned", "required"} else ""
    return (
        '<div class="bar">'
        f'<span class="label">{html.escape(label)}</span>'
        f'<span class="track"><span class="fill{html.escape(class_attr)}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(str(value))}</span>'
        "</div>"
    )
