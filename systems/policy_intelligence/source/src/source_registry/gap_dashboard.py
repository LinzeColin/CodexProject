from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .reference_gaps import gap_action_label, gap_type_label


def write_gap_dashboard(
    path: str | Path,
    gaps: list[Mapping[str, Any]],
    *,
    title: str = "外部参考缺口管理仪表盘",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_gap_dashboard(gaps, title=title), encoding="utf-8")
    return str(output)


def render_gap_dashboard(
    gaps: list[Mapping[str, Any]],
    *,
    title: str = "外部参考缺口管理仪表盘",
) -> str:
    pending = [gap for gap in gaps if str(gap.get("status") or "pending") == "pending"]
    by_action = Counter(str(gap.get("required_action") or "unknown") for gap in pending)
    by_platform = Counter(str(gap.get("platform") or "unknown") for gap in pending)
    by_status = Counter(str(gap.get("status") or "pending") for gap in gaps)
    top = sorted(pending, key=lambda gap: int(gap.get("priority_score") or 0), reverse=True)[:30]
    data = _dashboard_data(gaps)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --ink: #182230;
      --muted: #667085;
      --line: #d0d5dd;
      --paper: #f4f6f8;
      --panel: #ffffff;
      --brand: #0b5c6b;
      --brand-dark: #063f4b;
      --accent: #9a4a13;
      --risk: #9b2c2c;
      --ok: #176345;
      --soft: #f8fafc;
      --focus: #155eef;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
      line-height: 1.58;
    }}
    .page {{ max-width: 1240px; margin: 0 auto; padding: 28px 22px 54px; }}
    .hero {{ border-top: 5px solid var(--brand-dark); background: var(--panel); padding: 22px 0 18px; border-bottom: 1px solid var(--line); }}
    .hero p {{ margin: 0; color: var(--muted); }}
    .hero h1 {{ margin: 3px 0 8px; font-size: 28px; line-height: 1.22; color: var(--brand-dark); }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; border: 1px solid var(--line); background: var(--panel); margin: 14px 0 18px; }}
    .metric {{ padding: 10px 12px; border-right: 1px solid var(--line); }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; color: var(--brand-dark); font-size: 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 16px 0 22px; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; }}
    .panel.wide {{ grid-column: 1 / -1; }}
    .panel h2 {{ margin: 0 0 9px; color: var(--brand-dark); font-size: 16px; }}
    .note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    .toolbar {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; align-items: end; }}
    .field label {{ display: block; margin: 0 0 4px; color: var(--muted); font-size: 12px; }}
    select, input, textarea, button {{
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      font: inherit;
      font-size: 12px;
    }}
    select, input, button {{ min-height: 34px; padding: 6px 9px; }}
    button {{ cursor: pointer; font-weight: 700; }}
    button.primary {{ color: #fff; background: var(--brand); border-color: var(--brand); }}
    button.secondary {{ color: var(--brand-dark); background: #edf4f7; border-color: #bed7df; }}
    button:focus-visible, select:focus-visible, input:focus-visible, textarea:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
    .actions {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 10px; }}
    .selection-summary {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0 0; }}
    .selection-summary span {{ border: 1px solid var(--line); background: var(--soft); padding: 3px 8px; font-size: 12px; }}
    .bars {{ display: grid; gap: 8px; }}
    .row {{ display: grid; grid-template-columns: 150px 1fr 48px; gap: 8px; align-items: center; font-size: 12px; }}
    .label {{ color: #344054; overflow-wrap: anywhere; }}
    .track {{ height: 10px; background: #e7eef1; border: 1px solid #d5e2e6; }}
    .fill {{ display: block; height: 100%; background: var(--brand); }}
    .fill.warn {{ background: var(--accent); }}
    .fill.risk {{ background: var(--risk); }}
    .fill.ok {{ background: var(--ok); }}
    .value {{ color: var(--brand-dark); font-weight: 700; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; vertical-align: top; text-align: left; }}
    th {{ background: #edf4f7; color: var(--brand-dark); }}
    td {{ background: var(--panel); }}
    tr.is-hidden {{ display: none; }}
    .check {{ width: 34px; text-align: center; }}
    .check input {{ width: 16px; min-height: 16px; padding: 0; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; color: #344054; overflow-wrap: anywhere; }}
    textarea.cmd {{ min-height: 98px; padding: 8px; resize: vertical; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    @media (max-width: 860px) {{
      .page {{ padding: 20px 15px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
      .panel.wide {{ grid-column: auto; }}
      .toolbar {{ grid-template-columns: 1fr 1fr; }}
      .actions {{ grid-template-columns: 1fr 1fr; }}
      .row {{ grid-template-columns: 104px 1fr 40px; }}
    }}
    @media (max-width: 560px) {{
      .toolbar, .actions {{ grid-template-columns: 1fr; }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Policy Intelligence Gap Operations</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(generated_at)}｜该页面只展示缺口元数据，不展示 API key、cookie 或账号密码。</p>
    </section>
    <section class="metrics">
      {_metric("全部缺口", len(gaps))}
      {_metric("待处理", len(pending))}
      {_metric("涉及动作", len(by_action))}
      {_metric("涉及平台", len(by_platform))}
    </section>
    <section class="grid">
      {_bar_panel("按建议动作", [(gap_action_label(k), v, _class_for_action(k)) for k, v in by_action.most_common()])}
      {_bar_panel("按平台", [(k, v, "") for k, v in by_platform.most_common(12)])}
      {_bar_panel("按状态", [(k, v, "ok" if k == "resolved" else "warn" if k == "ignored" else "risk") for k, v in by_status.most_common()])}
      {_command_panel(by_action)}
      {_interactive_panel(data)}
      {_table_panel(top)}
    </section>
  </main>
  <script type="application/json" id="gap-data">{_json_for_script(data)}</script>
  <script>
    (function () {{
      const dataNode = document.getElementById("gap-data");
      const rows = JSON.parse(dataNode ? dataNode.textContent : "[]");
      const state = {{ selected: new Set() }};
      const els = {{
        action: document.getElementById("filter-action"),
        platform: document.getElementById("filter-platform"),
        status: document.getElementById("filter-status"),
        search: document.getElementById("filter-search"),
        reviewStatus: document.getElementById("review-status"),
        tbody: document.getElementById("gap-workbench-body"),
        visibleCount: document.getElementById("visible-count"),
        selectedCount: document.getElementById("selected-count"),
        commandOutput: document.getElementById("command-output"),
        selectVisible: document.getElementById("select-visible"),
        clearSelection: document.getElementById("clear-selection"),
        buildBulk: document.getElementById("build-bulk-command"),
        buildSingle: document.getElementById("build-single-command"),
        copyCommand: document.getElementById("copy-command")
      }};

      function uniqueValues(key) {{
        return Array.from(new Set(rows.map((row) => row[key]).filter(Boolean))).sort();
      }}

      function fillOptions(select, values) {{
        values.forEach((value) => {{
          const option = document.createElement("option");
          option.value = value;
          option.textContent = value;
          select.appendChild(option);
        }});
      }}

      function escapeCell(value) {{
        return String(value || "")
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#39;");
      }}

      function shellQuote(value) {{
        const text = String(value || "");
        if (/^[A-Za-z0-9_./:@%+=,-]+$/.test(text)) {{
          return text;
        }}
        return "'" + text.replace(/'/g, "'\\\\''") + "'";
      }}

      function currentRows() {{
        const action = els.action.value;
        const platform = els.platform.value;
        const status = els.status.value;
        const term = els.search.value.trim().toLowerCase();
        return rows.filter((row) => {{
          if (action !== "all" && row.required_action !== action) return false;
          if (platform !== "all" && row.platform !== platform) return false;
          if (status !== "all" && row.status !== status) return false;
          if (!term) return true;
          const haystack = [row.gap_id, row.title, row.platform, row.gap_type_label, row.action_label, row.query]
            .join(" ")
            .toLowerCase();
          return haystack.includes(term);
        }});
      }}

      function renderTable() {{
        const visible = currentRows();
        els.visibleCount.textContent = String(visible.length);
        els.selectedCount.textContent = String(state.selected.size);
        els.tbody.innerHTML = "";
        visible.forEach((row) => {{
          const tr = document.createElement("tr");
          tr.setAttribute("data-gap-id", row.gap_id);
          const checked = state.selected.has(row.gap_id) ? "checked" : "";
          tr.innerHTML = `
            <td class="check"><input type="checkbox" aria-label="选择缺口 ${{escapeCell(row.gap_id)}}" data-gap-id="${{escapeCell(row.gap_id)}}" ${{checked}}></td>
            <td>${{escapeCell(row.priority_score)}}</td>
            <td>${{escapeCell(row.platform)}}</td>
            <td>${{escapeCell(row.gap_type_label)}}</td>
            <td>${{escapeCell(row.action_label)}}</td>
            <td>${{escapeCell(row.status)}}</td>
            <td>${{escapeCell(row.title)}}</td>
            <td class="cmd">${{escapeCell(row.gap_id)}}</td>
          `;
          els.tbody.appendChild(tr);
        }});
      }}

      function buildBulkCommand() {{
        const parts = [
          "PYTHONPATH=src",
          "python3",
          "-m",
          "source_registry",
          "--db",
          "data/source_registry.sqlite",
          "gap-bulk-review",
          "--content-db",
          "data/policy_documents.sqlite",
          "--status",
          shellQuote(els.reviewStatus.value),
          "--from-status",
          shellQuote(els.status.value === "all" ? "pending" : els.status.value)
        ];
        if (els.action.value !== "all") parts.push("--required-action", shellQuote(els.action.value));
        if (els.platform.value !== "all") parts.push("--platform", shellQuote(els.platform.value));
        parts.push("--reviewer", "linze", "--note", shellQuote("dashboard dry-run review"), "--dry-run");
        els.commandOutput.value = parts.join(" ");
      }}

      function buildSingleCommands() {{
        const selectedRows = rows.filter((row) => state.selected.has(row.gap_id));
        if (!selectedRows.length) {{
          els.commandOutput.value = "# 先勾选至少一个 gap_id";
          return;
        }}
        els.commandOutput.value = selectedRows.map((row) => [
          "PYTHONPATH=src",
          "python3",
          "-m",
          "source_registry",
          "--db",
          "data/source_registry.sqlite",
          "gap-review",
          shellQuote(row.gap_id),
          "--content-db",
          "data/policy_documents.sqlite",
          "--status",
          shellQuote(els.reviewStatus.value),
          "--reviewer",
          "linze",
          "--note",
          shellQuote("dashboard selected review")
        ].join(" ")).join("\\n");
      }}

      fillOptions(els.action, uniqueValues("required_action"));
      fillOptions(els.platform, uniqueValues("platform"));
      fillOptions(els.status, uniqueValues("status"));
      ["change", "input"].forEach((eventName) => {{
        [els.action, els.platform, els.status, els.search].forEach((control) => {{
          control.addEventListener(eventName, renderTable);
        }});
      }});
      els.tbody.addEventListener("change", (event) => {{
        const target = event.target;
        if (!target || !target.getAttribute) return;
        const gapId = target.getAttribute("data-gap-id");
        if (!gapId) return;
        if (target.checked) state.selected.add(gapId);
        else state.selected.delete(gapId);
        renderTable();
      }});
      els.selectVisible.addEventListener("click", () => {{
        currentRows().forEach((row) => state.selected.add(row.gap_id));
        renderTable();
      }});
      els.clearSelection.addEventListener("click", () => {{
        state.selected.clear();
        renderTable();
      }});
      els.buildBulk.addEventListener("click", buildBulkCommand);
      els.buildSingle.addEventListener("click", buildSingleCommands);
      els.copyCommand.addEventListener("click", () => {{
        els.commandOutput.select();
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(els.commandOutput.value).catch(() => document.execCommand("copy"));
        }} else {{
          document.execCommand("copy");
        }}
      }});
      renderTable();
      buildBulkCommand();
    }})();
  </script>
</body>
</html>
"""


def _metric(label: str, value: object) -> str:
    return f'<article class="metric"><span>{html.escape(str(label))}</span><strong>{html.escape(str(value))}</strong></article>'


def _bar_panel(title: str, rows: list[tuple[str, int, str]]) -> str:
    if not rows:
        return f'<article class="panel"><h2>{html.escape(title)}</h2><p class="note">暂无数据。</p></article>'
    maximum = max([value for _, value, _ in rows] + [1])
    return (
        f'<article class="panel"><h2>{html.escape(title)}</h2>'
        f'<section class="bars">{"".join(_bar_row(label, value, maximum, klass) for label, value, klass in rows)}</section>'
        '</article>'
    )


def _bar_row(label: str, value: int, maximum: int, klass: str) -> str:
    pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
    klass_attr = f" {klass}" if klass else ""
    return (
        '<div class="row">'
        f'<span class="label">{html.escape(str(label))}</span>'
        f'<span class="track"><span class="fill{klass_attr}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(str(value))}</span>'
        '</div>'
    )


def _command_panel(by_action: Counter[str]) -> str:
    if not by_action:
        return '<article class="panel"><h2>推荐操作命令</h2><p class="note">当前没有待处理动作。</p></article>'
    chips = []
    for action, count in by_action.most_common():
        command = (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite "
            f"gap-bulk-review --required-action {action} --status resolved --dry-run"
        )
        chips.append(
            '<p>'
            f'<span class="pill">{html.escape(gap_action_label(action))}：{count}</span>'
            f'<span class="cmd">{html.escape(command)}</span>'
            '</p>'
        )
    return (
        '<article class="panel"><h2>推荐操作命令</h2>'
        f'{"".join(chips)}'
        '<p class="note">批量复核前先 dry-run；只有实际补齐 key、授权或完成复核后再去掉 dry-run。</p></article>'
    )


def _interactive_panel(gaps: list[dict[str, Any]]) -> str:
    if not gaps:
        return '<article class="panel wide"><h2>缺口复核工作台</h2><p class="note">暂无可复核缺口。</p></article>'
    return """
      <article class="panel wide" id="gap-workbench">
        <h2>缺口复核工作台</h2>
        <section class="toolbar" aria-label="缺口筛选">
          <div class="field">
            <label for="filter-action">建议动作</label>
            <select id="filter-action"><option value="all">全部动作</option></select>
          </div>
          <div class="field">
            <label for="filter-platform">平台</label>
            <select id="filter-platform"><option value="all">全部平台</option></select>
          </div>
          <div class="field">
            <label for="filter-status">状态</label>
            <select id="filter-status"><option value="all">全部状态</option></select>
          </div>
          <div class="field">
            <label for="filter-search">关键词</label>
            <input id="filter-search" type="search" placeholder="标题 / gap_id / query">
          </div>
          <div class="field">
            <label for="review-status">目标状态</label>
            <select id="review-status">
              <option value="resolved">resolved</option>
              <option value="ignored">ignored</option>
              <option value="pending">pending</option>
            </select>
          </div>
        </section>
        <section class="actions">
          <button type="button" class="secondary" id="select-visible">全选当前筛选</button>
          <button type="button" class="secondary" id="clear-selection">清空选择</button>
          <button type="button" class="primary" id="build-bulk-command">生成批量预演命令</button>
          <button type="button" class="secondary" id="build-single-command">生成单条复核命令</button>
        </section>
        <section class="selection-summary" aria-live="polite">
          <span>当前筛选：<strong id="visible-count">0</strong></span>
          <span>已选择：<strong id="selected-count">0</strong></span>
        </section>
        <textarea class="cmd" id="command-output" aria-label="复核命令输出"></textarea>
        <button type="button" class="secondary" id="copy-command">复制命令</button>
        <table>
          <thead>
            <tr>
              <th class="check">选</th><th>优先级</th><th>平台</th><th>缺口</th><th>建议动作</th><th>状态</th><th>标题</th><th>gap_id</th>
            </tr>
          </thead>
          <tbody id="gap-workbench-body"></tbody>
        </table>
        <p class="note">批量命令默认带 dry-run；单条复核命令只生成文本，执行前需要确认真实 key、授权或人工复核已经完成。</p>
      </article>
    """


def _table_panel(gaps: list[Mapping[str, Any]]) -> str:
    if not gaps:
        return '<article class="panel wide"><h2>最高优先级缺口</h2><p class="note">暂无待处理缺口。</p></article>'
    rows = []
    for gap in gaps:
        title = _truncate(str(gap.get("title") or gap.get("document_title") or "未命名缺口"), 80)
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(gap.get('priority_score') or 0))}</td>"
            f"<td>{html.escape(str(gap.get('platform') or 'unknown'))}</td>"
            f"<td>{html.escape(gap_type_label(str(gap.get('gap_type') or '')))}</td>"
            f"<td>{html.escape(gap_action_label(str(gap.get('required_action') or '')))}</td>"
            f"<td>{html.escape(title)}</td>"
            f"<td class=\"cmd\">{html.escape(str(gap.get('gap_id') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>最高优先级缺口</h2>'
        '<table><thead><tr><th>优先级</th><th>平台</th><th>缺口</th><th>建议动作</th><th>标题</th><th>gap_id</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _class_for_action(action: str) -> str:
    if action in {"provide_search_api_key", "provide_platform_auth"}:
        return "risk"
    if action in {"review_candidate_url", "refine_public_site_search", "retry_request"}:
        return "warn"
    return ""


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: max(0, limit - 3)] + "..."


def _dashboard_data(gaps: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for gap in sorted(gaps, key=lambda item: int(item.get("priority_score") or 0), reverse=True):
        gap_type = str(gap.get("gap_type") or "")
        action = str(gap.get("required_action") or "")
        rows.append(
            {
                "gap_id": str(gap.get("gap_id") or ""),
                "status": str(gap.get("status") or "pending"),
                "priority_score": int(gap.get("priority_score") or 0),
                "platform": str(gap.get("platform") or "unknown"),
                "gap_type": gap_type,
                "gap_type_label": gap_type_label(gap_type),
                "required_action": action,
                "action_label": gap_action_label(action),
                "title": _truncate(str(gap.get("title") or gap.get("document_title") or "未命名缺口"), 100),
                "url": str(gap.get("url") or ""),
                "query": str(gap.get("query") or ""),
            }
        )
    return rows


def _json_for_script(data: list[dict[str, Any]]) -> str:
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
