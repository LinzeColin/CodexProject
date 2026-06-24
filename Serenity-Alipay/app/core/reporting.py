from __future__ import annotations

import html
from pathlib import Path

from app.core.time_display import format_display_time


def pct(value: float | None) -> str:
    if value is None:
        return "缺失"
    return f"{value:.2%}"


def _zh_action(action: object) -> str:
    return {
        "Maintain": "维持",
        "Increase": "增配/买入候选",
        "Reduce": "减配/卖出候选",
        "Pause New": "暂停新增",
        "Clear": "清仓/退出",
        "Block": "禁止新增",
        "Manual Review": "人工复核",
        "No-New-Order": "禁止新增",
    }.get(str(action), "人工复核")


def _zh_grade(grade: object) -> str:
    return {
        "Action-Ready": "可执行",
        "Watch": "观察",
        "Manual Review": "人工复核",
        "Block": "阻断",
    }.get(str(grade), str(grade))


def _zh_status(status: object) -> str:
    return {
        "success": "成功",
        "degraded": "降级",
        "failed": "失败",
        "error": "失败",
    }.get(str(status), str(status))


def _zh_data_quality(status: object) -> str:
    return {
        "pass": "通过",
        "manual_review": "人工复核",
        "degraded": "降级",
        "block": "阻断",
    }.get(str(status), str(status))


def _zh_moomoo_status(status: object) -> str:
    return {
        "available": "可用",
        "unavailable": "不可用",
        "degraded": "降级",
        "mock": "模拟数据",
    }.get(str(status), str(status))


def _zh_compare_type(compare_type: object) -> str:
    text = str(compare_type or "")
    return {
        "same_day_previous": "当日上一轮",
        "previous_day": "前一交易日",
        "previous_week": "前一周",
        "previous_month": "前一月",
    }.get(text, text or "无")


def _zh_reason(reason: object) -> str:
    text = str(reason or "")
    lowered = text.lower()
    if not text:
        return "未触发额外原因"
    if "target/current deviation" in lowered or "deviation" in lowered:
        return "目标权重与基准权重偏离超过阈值"
    if "serenity judgment supported" in lowered or "score and evidence support" in lowered:
        return "Serenity判断与证据置信度支持候选"
    if "evidence confidence watch" in lowered or "watch score band" in lowered:
        return "证据置信度处于观察区间"
    if "same_day_previous" in lowered or "key field sigma" in lowered:
        return "同日对比关键字段波动超过阈值"
    if "top5" in lowered:
        return "Top5 候选池变化超过阈值"
    if "underperformed" in lowered:
        return "收益窗口低于沪指和标普500"
    if "official source count" in lowered:
        return "官方级证据不足"
    if "fee" in lowered or "redemption" in lowered or "subscription" in lowered:
        return "申赎或费率状态不足"
    if "source conflict" in lowered:
        return "来源冲突，需要人工复核"
    if "aggregated fallback" in lowered:
        return "聚合来源导致评级上限"
    if "max_drawdown" in lowered:
        return "最大回撤触发风控"
    if "recovery_time" in lowered:
        return "回撤修复时间超过阈值"
    if "missing" in lowered:
        return "关键数据缺失"
    return "策略触发条件命中"


def _notification_subject(severity: str, locked: bool, urgent: bool, actionable_count: int) -> str:
    if locked:
        return "[Serenity自动化][复核] 数据不足，暂停新增"
    if urgent:
        return "[Serenity自动化][紧急] 风控触发，立即复核"
    if actionable_count > 0:
        return "[Serenity自动化][调仓] 需要确认持仓动作"
    if severity == "Alert":
        return "[Serenity自动化][复核] 信号变化，保持当前持仓"
    if severity == "Warn":
        return "[Serenity自动化][观察] 暂不新增，等待复核"
    return "[Serenity自动化][完成] 无需操作，保持当前持仓"


def _notification_next_step(locked: bool, urgent: bool, actionable_count: int) -> str:
    if locked:
        return "暂停新增，不下单；先补齐人工复核项或等待下一轮自动复核。"
    if urgent:
        return "立即打开交易平台人工确认；若确认执行，优先在北京时间15:00前完成。"
    if actionable_count > 0:
        return "按下方动作清单人工确认费率、限额和截止时间；确认后再操作。"
    return "无需操作；保持当前持仓，等待下一轮自动复核。"


def _notification_deadline(locked: bool, actionable_count: int) -> str:
    if locked:
        return "下一次运行前补证据；当前不新增、不提交订单。"
    if actionable_count > 0:
        return "优先北京时间15:00前处理；超过15:00按平台规则顺延。"
    return "无需处理；下一运行点自动复核。"


def _recommendation_line(index: int, row: dict[str, object], locked: bool) -> str:
    action = "禁止新增" if locked else _zh_action(row.get("action_label"))
    deviation = float(row.get("deviation") or 0.0)
    return (
        f"{index}. {row.get('asset_name')}（{row.get('asset_code')}）："
        f"{action}，目标 {pct(float(row.get('target_weight') or 0.0))}，"
        f"相对基准 {deviation:+.2%}，{_zh_grade(row.get('grade'))}"
    )


def _mail_escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _mail_action_style(action_label: object, locked: bool) -> tuple[str, str, str]:
    if locked:
        return "禁止新增", "#7f1d1d", "#fee2e2"
    action = str(action_label or "")
    if action in {"Increase"}:
        return _zh_action(action), "#b91c1c", "#fee2e2"
    if action in {"Reduce", "Clear", "Block"}:
        return _zh_action(action), "#047857", "#dcfce7"
    if action in {"Pause New", "Manual Review"}:
        return _zh_action(action), "#92400e", "#fef3c7"
    return _zh_action(action), "#1d4ed8", "#e8f4ff"


def _mail_badge(label: str, fg: str, bg: str) -> str:
    return (
        f'<span style="display:inline-block;padding:5px 10px;border-radius:999px;'
        f'font-weight:700;color:{fg};background-color:{bg};border:1px solid {fg};">'
        f"{_mail_escape(label)}</span>"
    )


def _mail_table_rows(recommendations: list[dict[str, object]], locked: bool) -> str:
    rows: list[str] = []
    for index, row in enumerate(recommendations[:5], start=1):
        action_label, fg, bg = _mail_action_style(row.get("action_label"), locked)
        deviation = float(row.get("deviation") or 0.0)
        rows.append(
            "<tr>"
            f'<td style="padding:9px 8px;border-bottom:1px solid #e5e7eb;text-align:center;">{index}</td>'
            f'<td style="padding:9px 8px;border-bottom:1px solid #e5e7eb;">'
            f'<strong>{_mail_escape(row.get("asset_name"))}</strong><br>'
            f'<span style="color:#64748b;">{_mail_escape(row.get("asset_code"))}</span></td>'
            f'<td style="padding:9px 8px;border-bottom:1px solid #e5e7eb;text-align:center;">'
            f'{_mail_badge(action_label, fg, bg)}</td>'
            f'<td style="padding:9px 8px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:700;">'
            f'{pct(float(row.get("target_weight") or 0.0))}</td>'
            f'<td style="padding:9px 8px;border-bottom:1px solid #e5e7eb;text-align:right;">'
            f'{pct(float(row.get("current_weight") or 0.0))}</td>'
            f'<td style="padding:9px 8px;border-bottom:1px solid #e5e7eb;text-align:right;color:{fg};font-weight:700;">'
            f'{deviation:+.2%}</td>'
            f'<td style="padding:9px 8px;border-bottom:1px solid #e5e7eb;text-align:center;">'
            f'{_mail_escape(_zh_grade(row.get("grade")))}</td>'
            "</tr>"
        )
    if not rows:
        return (
            '<tr><td colspan="7" style="padding:14px 10px;text-align:center;'
            'color:#64748b;border-bottom:1px solid #e5e7eb;">本轮没有可用候选。</td></tr>'
        )
    return "\n".join(rows)


def render_notification_html(
    title: str,
    run_id: str,
    severity: str,
    recommendations: list[dict[str, object]],
    run_time_bj: str,
    run_time_au: str,
    *,
    data_quality_status: str = "pass",
    event_reason: object = "",
    manual_review_items: list[str] | None = None,
    execution_locked: bool | None = None,
) -> str:
    locked = data_quality_status != "pass" if execution_locked is None else execution_locked
    urgent = severity == "Urgent" or any(row.get("action_label") in {"Clear", "Block"} for row in recommendations)
    actionable = [row for row in recommendations if str(row.get("action_label")) not in {"Maintain"}]
    primary_action = "禁止新增" if locked else (_zh_action(actionable[0].get("action_label")) if actionable else "维持")
    primary_fg = "#7f1d1d" if locked or urgent else ("#b91c1c" if actionable else "#1d4ed8")
    primary_bg = "#fee2e2" if locked or urgent else ("#fee2e2" if actionable else "#e8f4ff")
    action_summary = (
        "；".join(
            f"{row.get('asset_name')}：{_zh_action(row.get('action_label'))} {float(row.get('deviation') or 0.0):+.2%}"
            for row in actionable[:5]
        )
        if actionable
        else "保持当前持仓，等待下一轮自动复核。"
    )
    manual_html = ""
    if manual_review_items:
        manual_html = "".join(
            f'<li style="margin:6px 0;">{_mail_escape(item)}</li>' for item in manual_review_items[:5]
        )
    else:
        manual_html = '<li style="margin:6px 0;">暂无额外人工复核项。</li>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_mail_escape(title)}</title>
</head>
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'PingFang SC','Microsoft YaHei',sans-serif;color:#0f172a;">
  <div style="max-width:760px;margin:0 auto;padding:22px;">
    <div style="background-color:#ffffff;border:1px solid #dbe4ee;border-radius:10px;overflow:hidden;">
      <div style="background-color:#102033;color:#ffffff;padding:20px 22px;">
        <h1 style="margin:0 0 8px 0;font-size:22px;line-height:1.35;">{_mail_escape(title)}</h1>
        <p style="margin:0;color:#cbd5e1;">Serenity Daily Analysis · 生产通知</p>
      </div>
      <div style="padding:20px 22px;">
        <h2 style="margin:0 0 10px 0;font-size:18px;color:#102033;border-bottom:2px solid #dbeafe;padding-bottom:8px;">一、结论</h2>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;margin:0 0 16px 0;">
          <tr>
            <td style="padding:8px 0;color:#64748b;width:120px;">本轮运行</td>
            <td style="padding:8px 0;"><strong>{_mail_escape(format_display_time(run_time_bj, 'Asia/Shanghai'))}</strong> / {_mail_escape(format_display_time(run_time_au, 'Australia/Sydney'))}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#64748b;">当前结论</td>
            <td style="padding:8px 0;">{_mail_badge(primary_action, primary_fg, primary_bg)}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#64748b;">处理截止</td>
            <td style="padding:8px 0;"><strong style="color:{primary_fg};text-decoration:underline;">{_mail_escape(_notification_deadline(locked, len(actionable)))}</strong></td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#64748b;">执行边界</td>
            <td style="padding:8px 0;"><strong>系统不自动交易、不提交申购或赎回；真实操作必须人工确认。</strong></td>
          </tr>
        </table>

        <h2 style="margin:20px 0 10px 0;font-size:18px;color:#102033;border-bottom:2px solid #dbeafe;padding-bottom:8px;">二、需变化的行为</h2>
        <h3 style="margin:0 0 8px 0;font-size:15px;color:{primary_fg};">本轮动作重点</h3>
        <p style="margin:0 0 10px 0;padding:12px 14px;background-color:{primary_bg};border-left:4px solid {primary_fg};line-height:1.65;">
          <strong>{_mail_escape(action_summary)}</strong>
        </p>
        <p style="margin:0 0 16px 0;color:#475569;line-height:1.65;">
          <em>原因：</em>{_mail_escape(_zh_reason(event_reason))}。操作前先核对支付宝或官方平台费率、限额、15:00 截止和确认到账时间。
        </p>

        <h2 style="margin:20px 0 10px 0;font-size:18px;color:#102033;border-bottom:2px solid #dbeafe;padding-bottom:8px;">三、当前持仓建议</h2>
        <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;border:1px solid #dbe4ee;font-size:13px;">
          <thead>
            <tr style="background-color:#eff6ff;color:#102033;">
              <th style="padding:9px 8px;border-bottom:1px solid #dbe4ee;text-align:center;">排名</th>
              <th style="padding:9px 8px;border-bottom:1px solid #dbe4ee;text-align:left;">持仓/基金</th>
              <th style="padding:9px 8px;border-bottom:1px solid #dbe4ee;text-align:center;">需操作行为</th>
              <th style="padding:9px 8px;border-bottom:1px solid #dbe4ee;text-align:right;">目标权重</th>
              <th style="padding:9px 8px;border-bottom:1px solid #dbe4ee;text-align:right;">当前/基准权重</th>
              <th style="padding:9px 8px;border-bottom:1px solid #dbe4ee;text-align:right;">偏离</th>
              <th style="padding:9px 8px;border-bottom:1px solid #dbe4ee;text-align:center;">等级</th>
            </tr>
          </thead>
          <tbody>
            {_mail_table_rows(recommendations, locked)}
          </tbody>
        </table>

        <h2 style="margin:20px 0 10px 0;font-size:18px;color:#102033;border-bottom:2px solid #dbeafe;padding-bottom:8px;">四、人工复核与风控兜底</h2>
        <h3 style="margin:0 0 8px 0;font-size:15px;color:#92400e;">复核项</h3>
        <ul style="margin:0 0 12px 18px;padding:0;line-height:1.6;">
          {manual_html}
        </ul>
        <p style="margin:0;padding:12px 14px;background-color:#f8fafc;border:1px solid #e2e8f0;line-height:1.65;">
          <strong>降级规则：</strong>数据缺失、来源冲突、申赎/费率异常、MDD 硬门槛或执行状态异常时，一律暂停新增并等待下一轮复核。
        </p>
      </div>
    </div>
  </div>
</body>
</html>
"""


def render_markdown_report(
    run_id: str,
    slot: str,
    run_time_bj: str,
    run_time_au: str,
    status: str,
    data_quality_status: str,
    moomoo_status: str,
    recommendations: list[dict[str, object]],
    benchmark_returns: dict[str, dict[str, float | None]],
    notification_title: str,
    comparison_summaries: list[dict[str, object]] | None = None,
    rebalance_events: list[str] | None = None,
    execution_locked: bool | None = None,
) -> str:
    locked = data_quality_status != "pass" if execution_locked is None else execution_locked
    execution_status = "ON" if locked else "OFF"
    prohibited_action = "禁止新增（No-New-Order）" if locked else "禁止自动下单；必须人工确认"
    lines = [
        f"# Serenity 每日分析正式报告：{run_id}",
        "",
        "## 运行状态",
        "",
        f"- 最新运行时间：{format_display_time(run_time_bj, 'Asia/Shanghai')}",
        f"- 北京时间：{format_display_time(run_time_bj, 'Asia/Shanghai')}",
        f"- 澳洲时间：{format_display_time(run_time_au, 'Australia/Sydney')}",
        f"- 运行状态：{_zh_status(status)}",
        f"- 数据质量：{_zh_data_quality(data_quality_status)}",
        f"- MooMoo/moomoo_OpenD：{_zh_moomoo_status(moomoo_status)}",
        "- 交易边界：仅输出研究结论、纪律标签和通知；不自动下单，不提交申购或赎回。",
        f"- 执行锁：{execution_status}",
        f"- 当前禁止动作：{prohibited_action}",
        "- 建议金额：0.00",
        "- 建议份额：0",
        "- 基准目标：目标与沪指、标普500进行 1个月、3个月、1年、最近10交易日收益对比；不承诺未来一定跑赢。",
        "- 纪律基准：首个合格运行从 0.00% 参考权重开始；后续运行相对上一轮 Serenity 基准调整，不把真实支付宝仓位当作 baseline。",
        "",
        "## Top5 候选池",
        "",
        "| 排名 | 代码 | 名称 | 等级 | 证据置信度 | 目标权重 | 基准权重 | 偏离 | 研究动作 | 执行状态 | 建议金额 | 建议份额 | 触发原因 |",
        "|---:|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---|",
    ]
    for row in recommendations:
        row_execution_status = "禁止新增（No-New-Order）" if locked else _zh_action(row["action_label"])
        lines.append(
            "| {rank} | {asset_code} | {asset_name} | {grade} | {score:.2f} | {target} | {current} | {deviation} | {action} | {execution_status} | 0.00 | 0 | {trigger} |".format(
                rank=row["rank"],
                asset_code=row["asset_code"],
                asset_name=row["asset_name"],
                grade=_zh_grade(row["grade"]),
                score=float(row["score"]),
                target=pct(row["target_weight"]),
                current=pct(row["current_weight"]),
                deviation=pct(row["deviation"]),
                action=_zh_action(row["action_label"]),
                execution_status=row_execution_status,
                trigger=_zh_reason(row["trigger_reason"]),
            )
        )

    lines.extend(
        [
            "",
            "## 基准收益对比",
            "",
            "| 基准 | 1个月 | 3个月 | 1年 | 最近10交易日 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for name, returns in benchmark_returns.items():
        benchmark_name = {"Shanghai Composite": "沪指", "S&P 500": "标普500"}.get(name, name)
        lines.append(
            f"| {benchmark_name} | {pct(returns.get('1m'))} | {pct(returns.get('3m'))} | {pct(returns.get('12m'))} | {pct(returns.get('10d'))} |"
        )

    lines.extend(
        [
            "",
            "## 当日与历史对比",
            "",
            "| 对比口径 | 对比运行 | 上轮 Top5 | 本轮 Top5 | 变动率 | 新增 | 替换 | 最大 Sigma |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in comparison_summaries or []:
        lines.append(
            "| {compare_type} | {base_run_id} | {old_top5} | {new_top5} | {change_rate} | {new_count} | {replacement_count} | {max_sigma:.2f} |".format(
                compare_type=_zh_compare_type(row["compare_type"]),
                base_run_id=row.get("base_run_id") or "无",
                old_top5=", ".join(row.get("old_top5", [])) or "无",
                new_top5=", ".join(row.get("new_top5", [])) or "无",
                change_rate=pct(row.get("top5_change_rate")),
                new_count=row.get("new_count", 0),
                replacement_count=row.get("replacement_count", 0),
                max_sigma=float(row.get("max_key_field_sigma", 0.0)),
            )
        )

    lines.extend(
        [
            "",
            "## 调仓触发矩阵",
            "",
        ]
    )
    if rebalance_events:
        for event in rebalance_events:
            lines.append(f"- {_zh_reason(event)}")
    else:
        lines.append("- 未触发重平衡阈值。")

    lines.extend(
        [
            "",
            "## 证据与降级说明",
            "",
            "- 聚合来源只能补齐视图，不能单独把候选标记为可执行。",
            "- 官方级来源少于 2 个时，不能进入可执行等级。",
            "- 申购费、赎回费或赎回状态缺失时，禁止新增订单。",
            "- MDD >= 40.00% 或回撤修复时间 >= 365 天时，触发硬降级。",
            "- 支付宝当前持仓只作为可选参考；纪律基准由 Serenity 生成的目标权重驱动。",
            "- 数据质量不是通过时，执行锁强制 No-New-Order，建议金额 0.00，建议份额 0。",
            "",
            "## 通知预览",
            "",
            f"- 标题：{notification_title}",
            "- 通道：生成 Apple Mail 可发送 Markdown 和本地离线报告；真实发送需要非 dry-run 命令与发送开关。",
            "",
        ]
    )
    return "\n".join(lines)


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def render_offline_html(title: str, markdown_text: str) -> str:
    body = html.escape(markdown_text)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; color: #111827; background: #f7f7f4; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px 20px 56px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #ffffff; border: 1px solid #d8d8d0; border-radius: 8px; padding: 20px; line-height: 1.45; }}
  </style>
</head>
<body>
  <main>
    <pre>{body}</pre>
  </main>
</body>
</html>
"""


def render_offline_index(runs: list[dict[str, str]]) -> str:
    def status_class(value: str) -> str:
        if value == "success":
            return "good"
        if value == "degraded":
            return "warn"
        return "bad"

    def quality_class(value: str) -> str:
        if value == "pass":
            return "good"
        if value == "manual_review":
            return "warn"
        return "bad"

    total_count = len(runs)
    pass_count = sum(1 for row in runs if row["status"] == "success" and row["quality"] == "pass")
    review_count = sum(1 for row in runs if row["quality"] == "manual_review")
    degraded_count = sum(1 for row in runs if row["status"] == "degraded")
    rows = "\n".join(
        '<tr data-status="{status_raw}" data-quality="{quality_raw}" data-slot="{slot_raw}" data-run="{run_raw}">'
        '<td><span class="run-id">{run_id}</span><button type="button" class="copy-run" data-copy-value="{run_raw}">复制</button></td>'
        "<td><strong>{run_time}</strong></td>"
        '<td><span class="badge {status_class}">{status}</span></td>'
        '<td><span class="badge {quality_class}">{quality}</span></td>'
        '<td class="links"><a class="action primary" href="{html_file}">HTML</a><a class="action" href="{md_file}">Markdown</a></td>'
        "</tr>".format(
            run_id=html.escape(row["run_id"]),
            run_raw=html.escape(row["run_id"].lower()),
            run_time=html.escape(row.get("run_time_bj") or row["slot"]),
            slot_raw=html.escape(row["slot"].lower()),
            status=html.escape(_zh_status(row["status"].lower())),
            status_raw=html.escape(row["status"].lower()),
            status_class=status_class(row["status"].lower()),
            quality=html.escape(_zh_data_quality(row["quality"].lower())),
            quality_raw=html.escape(row["quality"].lower()),
            quality_class=quality_class(row["quality"].lower()),
            html_file=html.escape(row["html_file"]),
            md_file=html.escape(row["md_file"]),
        )
        for row in runs
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Serenity 每日分析报告归档</title>
  <style>
    :root {{
      color-scheme: light;
      --page: #f5f7f4;
      --surface: #ffffff;
      --surface-2: #eef3ef;
      --ink: #132027;
      --muted: #64717b;
      --line: #d9e0da;
      --accent: #0b6f7b;
      --good: #1f7a4d;
      --warn: #946200;
      --bad: #a33b3b;
      --radius: 8px;
    }}

    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; color: var(--ink); background: var(--page); }}
    main {{ max-width: 1220px; margin: 0 auto; padding: 24px 18px 56px; }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: start;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      margin-bottom: 18px;
    }}
    h1 {{ margin: 0; font-size: 30px; line-height: 1.15; letter-spacing: 0; }}
    .meta {{ color: var(--muted); margin-top: 8px; line-height: 1.5; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}
    .metric {{ background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px; min-height: 82px; }}
    .metric span {{ color: var(--muted); display: block; font-size: 13px; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 8px; }}
    .tools {{
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto;
      gap: 10px;
      align-items: center;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 12px;
      margin-bottom: 12px;
    }}
    input {{
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 8px 10px;
      font: inherit;
      background: #fff;
      color: var(--ink);
    }}
    input:focus-visible, button:focus-visible, a.action:focus-visible {{
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(11, 111, 123, 0.14);
    }}
    .filters {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    button, a.action {{
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      color: var(--ink);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      font: inherit;
      font-weight: 700;
      padding: 8px 10px;
      text-decoration: none;
      transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease, background 160ms ease;
    }}
    button:hover, a.action:hover {{ border-color: var(--accent); }}
    button:active, a.action:active {{ transform: translateY(1px); }}
    button[aria-pressed="true"], .primary {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
    .table-wrap {{ overflow: auto; border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); }}
    table {{ width: 100%; min-width: 860px; border-collapse: collapse; }}
    th, td {{ padding: 11px 12px; border-bottom: 1px solid var(--line); text-align: left; font-size: 14px; vertical-align: top; }}
    th {{ background: var(--surface-2); color: #26323a; }}
    tr:last-child td {{ border-bottom: 0; }}
    .run-id {{ display: block; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; overflow-wrap: anywhere; margin-bottom: 8px; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 9px;
      font-size: 12px;
      font-weight: 800;
      border: 1px solid var(--line);
      white-space: nowrap;
    }}
    .badge.good {{ background: #e8f5ed; border-color: #c9e3d3; color: var(--good); }}
    .badge.warn {{ background: #fff4d8; border-color: #ead59d; color: var(--warn); }}
    .badge.bad {{ background: #fae9e9; border-color: #ebc6c6; color: var(--bad); }}
    .empty {{ display: none; color: var(--muted); background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px; margin-top: 12px; }}
    .toast {{
      position: fixed;
      right: 18px;
      bottom: 18px;
      background: #14242a;
      color: #fff;
      border-radius: var(--radius);
      padding: 12px 14px;
      opacity: 0;
      transform: translateY(10px);
      transition: opacity 180ms ease, transform 180ms ease;
      pointer-events: none;
      z-index: 10;
    }}
    .toast.show {{ opacity: 1; transform: translateY(0); }}
    @media (max-width: 860px) {{
      header, .tools {{ grid-template-columns: 1fr; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 540px) {{
      main {{ padding: 18px 12px 42px; }}
      h1 {{ font-size: 24px; }}
      .summary {{ grid-template-columns: 1fr; }}
      .filters, .links {{ display: grid; }}
      button, a.action {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Serenity 每日分析报告归档</h1>
        <div class="meta">搜索、筛选、打开报告，并复制本地归档运行 ID。</div>
      </div>
      <a class="action primary" href="../../outputs/application/index.html">返回首页</a>
    </header>

    <section class="summary" aria-label="报告归档摘要">
      <div class="metric"><span>总运行数</span><strong>{total_count}</strong></div>
      <div class="metric"><span>成功且通过</span><strong>{pass_count}</strong></div>
      <div class="metric"><span>人工复核</span><strong>{review_count}</strong></div>
      <div class="metric"><span>降级运行</span><strong>{degraded_count}</strong></div>
    </section>

    <section class="tools" aria-label="报告筛选">
      <input id="search" type="search" placeholder="搜索运行 ID、运行时间、状态或数据质量" autocomplete="off">
      <div class="filters">
        <button type="button" data-filter="all" aria-pressed="true">全部</button>
        <button type="button" data-filter="pass" aria-pressed="false">通过</button>
        <button type="button" data-filter="manual_review" aria-pressed="false">人工复核</button>
        <button type="button" data-filter="degraded" aria-pressed="false">降级</button>
      </div>
    </section>

    <div class="table-wrap">
      <table>
        <thead><tr><th>运行</th><th>运行时间</th><th>状态</th><th>数据质量</th><th>打开</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div class="empty" id="empty">当前筛选条件下没有匹配报告。</div>
  </main>
  <div class="toast" role="status" aria-live="polite" id="toast">完成</div>
  <script>
    const rows = Array.from(document.querySelectorAll("tbody tr"));
    const search = document.getElementById("search");
    const empty = document.getElementById("empty");
    const toast = document.getElementById("toast");
    let activeFilter = "all";

    const showToast = (message) => {{
      toast.textContent = message;
      toast.classList.add("show");
      window.clearTimeout(showToast.timer);
      showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 1800);
    }};

    const matchesFilter = (row) => {{
      if (activeFilter === "all") return true;
      if (activeFilter === "pass") return row.dataset.status === "success" && row.dataset.quality === "pass";
      if (activeFilter === "manual_review") return row.dataset.quality === "manual_review";
      if (activeFilter === "degraded") return row.dataset.status === "degraded";
      return true;
    }};

    const updateRows = () => {{
      const query = search.value.trim().toLowerCase();
      let shown = 0;
      rows.forEach((row) => {{
        const textMatch = !query || row.textContent.toLowerCase().includes(query);
        const visible = textMatch && matchesFilter(row);
        row.style.display = visible ? "" : "none";
        if (visible) shown += 1;
      }});
      empty.style.display = shown ? "none" : "block";
    }};

    search.addEventListener("input", updateRows);
    document.querySelectorAll("[data-filter]").forEach((button) => {{
      button.addEventListener("click", () => {{
        activeFilter = button.dataset.filter;
        document.querySelectorAll("[data-filter]").forEach((item) => item.setAttribute("aria-pressed", "false"));
        button.setAttribute("aria-pressed", "true");
        updateRows();
        showToast(`已应用筛选：${{button.textContent.trim()}}`);
      }});
    }});

    document.querySelectorAll("[data-copy-value]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const value = button.dataset.copyValue;
        const original = button.textContent;
        try {{
          await navigator.clipboard.writeText(value);
        }} catch {{
          const holder = document.createElement("textarea");
          holder.value = value;
          holder.setAttribute("readonly", "");
          holder.style.position = "fixed";
          holder.style.opacity = "0";
          document.body.appendChild(holder);
          holder.select();
          document.execCommand("copy");
          holder.remove();
        }}
        button.textContent = "已复制";
        showToast("运行 ID 已复制");
        window.setTimeout(() => {{ button.textContent = original; }}, 1400);
      }});
    }});
  </script>
</body>
</html>
"""


def render_notification(
    run_id: str,
    severity: str,
    recommendations: list[dict[str, object]],
    run_time_bj: str,
    run_time_au: str,
    data_quality_status: str = "pass",
    execution_locked: bool | None = None,
) -> tuple[str, str]:
    top = recommendations[:5]
    urgent = any(row["action_label"] in {"Clear", "Block"} for row in recommendations)
    locked = data_quality_status != "pass" if execution_locked is None else execution_locked
    if urgent:
        severity = "Urgent"
    actionable = [row for row in recommendations if str(row.get("action_label")) not in {"Maintain"}]
    actionable_count = len(actionable)
    title = _notification_subject(severity, locked, urgent, actionable_count)
    primary_action = "禁止新增" if locked else (_zh_action(actionable[0]["action_label"]) if actionable else "维持")
    body_lines = [
        f"# {title}",
        "",
        "## 结论",
        f"- 本轮运行：{format_display_time(run_time_bj, 'Asia/Shanghai')} / {format_display_time(run_time_au, 'Australia/Sydney')}",
        f"- 当前结论：{primary_action}",
        f"- 处理截止：{_notification_deadline(locked, actionable_count)}",
        f"- 执行锁：{'ON' if locked else 'OFF'}",
        f"- 当前禁止动作：{'禁止新增（No-New-Order）' if locked else '禁止自动下单；必须人工确认'}",
    ]
    if locked:
        body_lines.extend(["- 建议金额：0.00", "- 建议份额：0"])

    body_lines.extend(
        [
            "",
            "## 需要你做什么",
            f"- {_notification_next_step(locked, urgent, actionable_count)}",
            "- 系统只给纪律建议，不会自动交易、不提交申购或赎回。",
            "",
            "## 持仓动作清单",
        ]
    )
    if top:
        body_lines.extend(_recommendation_line(index, row, locked) for index, row in enumerate(top, start=1))
    else:
        body_lines.append("- 本轮没有可用候选。")

    body_lines.extend(
        [
            "",
            "## 风控兜底",
            f"- 关键原因：{_zh_reason(actionable[0]['trigger_reason'] if actionable else (top[0]['trigger_reason'] if top else ''))}",
            "- 数据缺失、冲突或执行状态异常时，一律暂停新增并等待下一轮复核。",
            "",
        ]
    )
    body = "\n".join(body_lines)
    return title, body
