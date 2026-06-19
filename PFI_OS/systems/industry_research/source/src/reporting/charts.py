from __future__ import annotations

import json
import ssl
import urllib.request
from pathlib import Path

import certifi

from src.pfi_os.engine import latest_result_by_symbol
from src.reporting.paths import image_dir
from src.reporting.renderer import table

USER_TRADABLE_INDEX_SYMBOLS = {"000688", "399986"}
USER_TRADABLE_INDEX_YAHOO_PROXIES = {
    "000688": "588090.SS",
    "399986": "512800.SS",
}


def market_structure_charts(factors: list[dict[str, object]], as_of: str, report_key: str) -> str:
    rows = [item for item in factors if _is_cn(item) and item.get("daily_change_pct") not in {"", None}]
    if not rows:
        return "- A股板块热力图/气泡图：当前缺少可用 A 股行情。"
    out_dir = image_dir(as_of, "market_structure")
    out_dir.mkdir(parents=True, exist_ok=True)
    heatmap = out_dir / f"heatmap_{report_key}_{as_of.replace('-', '')}.png"
    bubble = out_dir / f"bubble_{report_key}_{as_of.replace('-', '')}.png"
    validation_by_symbol = latest_result_by_symbol(as_of)
    _plot_heatmap(rows, heatmap)
    _plot_bubble(rows, bubble, validation_by_symbol)
    return (
        f"![A股板块热力图]({heatmap})\n\n"
        f"![A股板块气泡图]({bubble})\n\n"
        "- 图表说明：热力图使用浅色背景和深色文字，按研究分组聚合，热力图每格列出该板块下明确对象名称、平均涨跌、对象数量和最多6个对象涨跌；气泡图底部横轴=当日涨跌幅，顶部横轴=左侧下跌承接/风险释放、右侧上涨兑现/趋势延续，左侧纵轴=复合质量分（量价、PFIOS、风险闸门、成交额），右侧纵轴=质量分区（0-40低质量、40-60观察、60+重点跟踪），气泡大小=成交额，颜色=涨跌方向（红涨绿跌），气泡标注=对象名称。\n\n"
        "### 板块对象明细\n\n"
        + _heatmap_object_table(rows, validation_by_symbol)
    )


def kline_long_report_sections(
    factors: list[dict[str, object]],
    advice: list[dict[str, object]],
    as_of: str,
) -> tuple[str, list[dict[str, object]], list[dict[str, object]]]:
    selected = _select_kline_universe(factors, advice)
    advice_by_name = {str(row.get("Name")): row for row in advice}
    sections = []
    technical_rows = []
    for item in selected:
        history = fetch_history(item)
        advice_row = advice_by_name.get(str(item.get("name")), {})
        action = str(advice_row.get("Position") or "观望")
        signal = _technical_signal(item, history, action)
        technical_rows.append(
            {
                **signal,
                "symbol": item.get("symbol", ""),
                "name": item.get("name", ""),
                "kline_group": item.get("kline_group", ""),
                "Position": action,
            }
        )
        summary = _indicator_summary(item, history, action, signal)
        charts = _indicator_charts(item, history, as_of)
        sections.append(_symbol_section(item, summary, charts, history, action, signal))
    return "\n\n".join(sections), selected, technical_rows


def fetch_history(item: dict[str, object]) -> list[dict[str, float]]:
    symbol = _to_yahoo_symbol(item)
    if not symbol:
        raise RuntimeError(f"No supported history source for {item.get('symbol')} {item.get('name')}.")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=9mo&interval=1d"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=10, context=_verified_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"History fetch failed for {symbol}.") from exc
    chart = payload.get("chart", {})
    if chart.get("error") or not chart.get("result"):
        raise RuntimeError(f"History source returned no usable data for {symbol}.")
    result = chart["result"][0]
    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    rows = []
    for idx, timestamp in enumerate(timestamps):
        close = _series_value(quote.get("close"), idx)
        if close in {"", None}:
            continue
        rows.append(
            {
                "date": float(timestamp),
                "open": float(_series_value(quote.get("open"), idx) or close),
                "high": float(_series_value(quote.get("high"), idx) or close),
                "low": float(_series_value(quote.get("low"), idx) or close),
                "close": float(close),
                "volume": float(_series_value(quote.get("volume"), idx) or 0),
            }
        )
    if len(rows) < 30:
        raise RuntimeError(f"History source returned fewer than 30 usable rows for {symbol}.")
    return rows[-160:]


def _plot_heatmap(rows: list[dict[str, object]], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _configure_matplotlib(plt)

    grouped: dict[str, list[dict[str, object]]] = {}
    for item in rows:
        grouped.setdefault(str(item.get("research_group") or item.get("industry") or "未分类"), []).append(item)
    items = []
    for label, group_rows in grouped.items():
        changes = [float(item["daily_change_pct"]) for item in group_rows]
        avg_change = sum(changes) / len(changes)
        names = sorted(group_rows, key=lambda item: float(item["daily_change_pct"]), reverse=True)
        name_text = "、".join(
            f"{str(item.get('name') or item.get('symbol'))[:8]} {_pct(float(item['daily_change_pct']))}"
            for item in names[:6]
        )
        items.append((label, avg_change, len(group_rows), name_text))
    items.sort(key=lambda row: row[1], reverse=True)
    cols = min(4, max(1, len(items)))
    rows_count = (len(items) + cols - 1) // cols
    fig, ax = plt.subplots(figsize=(12.5, max(3.4, rows_count * 1.35)), dpi=160)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows_count)
    ax.axis("off")
    max_abs = max([abs(value) for _, value, _, _ in items] + [0.01])
    for idx, (label, value, count, name_text) in enumerate(items):
        col = idx % cols
        row = rows_count - 1 - idx // cols
        intensity = min(1.0, abs(value) / max_abs)
        color = _blend("#fff7f8", "#f1c3cc", intensity) if value >= 0 else _blend("#f5fcf6", "#c9ead1", intensity)
        rect = plt.Rectangle((col + 0.03, row + 0.05), 0.94, 0.92, facecolor=color, edgecolor="#ffffff", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(col + 0.5, row + 0.73, label[:18], ha="center", va="center", fontsize=9, color="#111111", fontweight="bold")
        ax.text(col + 0.5, row + 0.51, f"均值 {_pct(value)} / {count}只", ha="center", va="center", fontsize=8, color="#111111")
        ax.text(col + 0.5, row + 0.26, _wrap_label("对象：" + name_text, 25), ha="center", va="center", fontsize=6.3, color="#111111")
    ax.set_title("A股板块热力图：板块均值 + 明确对象名称", fontsize=12, pad=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _heatmap_object_table(rows: list[dict[str, object]], validation_by_symbol: dict[str, dict[str, str]]) -> str:
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in rows:
        grouped.setdefault(str(item.get("research_group") or item.get("industry") or "未分类"), []).append(item)
    table_rows = []
    for group, items in grouped.items():
        sorted_items = sorted(items, key=lambda item: float(item.get("daily_change_pct") or 0), reverse=True)
        changes = [float(item.get("daily_change_pct") or 0) for item in sorted_items if item.get("daily_change_pct") not in {"", None}]
        turnover = sum(float(item.get("turnover") or 0) for item in sorted_items)
        quality = sum(_bubble_quality_score(item, validation_by_symbol) for item in sorted_items) / len(sorted_items)
        object_names = "、".join(
            f"{str(item.get('name') or item.get('symbol'))}({_pct(float(item.get('daily_change_pct') or 0))})"
            for item in sorted_items[:6]
        )
        table_rows.append(
            {
                "group": group,
                "objects": object_names,
                "avg_change_pct": sum(changes) / len(changes) if changes else 0.0,
                "turnover": turnover,
                "quality": quality,
                "judgement": _sector_judgement(sum(changes) / len(changes) if changes else 0.0, turnover, quality),
            }
        )
    return table(
        sorted(table_rows, key=lambda row: float(row["quality"]), reverse=True),
        ["group", "objects", "avg_change_pct", "turnover", "quality", "judgement"],
        ["板块/主题", "明确对象名称", "平均涨跌", "合计成交额", "复合质量分", "判断结论"],
    )


def _plot_bubble(rows: list[dict[str, object]], path: Path, validation_by_symbol: dict[str, dict[str, str]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _configure_matplotlib(plt)

    ranked = sorted(rows, key=lambda item: _bubble_quality_score(item, validation_by_symbol), reverse=True)
    x = [float(item["daily_change_pct"]) * 100 for item in ranked]
    y = [_bubble_quality_score(item, validation_by_symbol) for item in ranked]
    colors = ["#c1121f" if value >= 0 else "#16833a" for value in x]
    sizes = [max(90, min(2600, float(item.get("turnover") or 0) / 8e6)) for item in ranked]
    labels = [str(item["name"]) for item in ranked]
    fig, ax = plt.subplots(figsize=(12.5, 5.8), dpi=160)
    ax.axhspan(0, 40, facecolor="#f2f2f2", alpha=0.75, zorder=0)
    ax.axhspan(40, 60, facecolor="#fff3cd", alpha=0.38, zorder=0)
    ax.axhspan(60, 100, facecolor="#d8f3dc", alpha=0.34, zorder=0)
    ax.scatter(x, y, s=sizes, c=colors, alpha=0.72, edgecolors="#333", linewidths=0.4)
    for idx, label in enumerate(labels):
        ax.text(x[idx], y[idx], label[:11], fontsize=6.8, va="center", ha="center")
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.axhline(60, color="#666", linewidth=0.7, linestyle="--", alpha=0.65)
    ax.set_ylim(0, 100)
    ax.set_xlabel("横轴：当日涨跌幅（%）")
    ax.set_ylabel("纵轴：复合质量分（0-100，越高越值得跟踪）")
    ax.set_title("A股板块气泡图：涨跌幅 × 复合质量分 × 成交额")
    top = ax.secondary_xaxis("top")
    top.set_xlabel("顶部横轴：左=下跌承接/风险释放；右=上涨兑现/趋势延续")
    right = ax.secondary_yaxis("right")
    right.set_ylabel("右侧纵轴：0-40低质量 / 40-60观察 / 60+重点跟踪")
    ax.text(0.02, 0.95, "左侧：下跌承接/风险释放", transform=ax.transAxes, ha="left", va="top", fontsize=8, color="#176f37")
    ax.text(0.98, 0.95, "右侧：上涨兑现/趋势延续", transform=ax.transAxes, ha="right", va="top", fontsize=8, color="#7f0018")
    ax.text(0.02, 0.05, "下方：质量不足，先观察", transform=ax.transAxes, ha="left", va="bottom", fontsize=8, color="#555")
    ax.text(0.98, 0.86, "上方：质量较高，仍需风控闸门", transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="#176f37")
    ax.text(0.985, 0.24, "低质量", transform=ax.transAxes, ha="right", va="center", fontsize=8, color="#555")
    ax.text(0.985, 0.50, "观察", transform=ax.transAxes, ha="right", va="center", fontsize=8, color="#7a5b00")
    ax.text(0.985, 0.78, "重点跟踪", transform=ax.transAxes, ha="right", va="center", fontsize=8, color="#176f37")
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _sector_judgement(avg_change: float, turnover: float, quality: float) -> str:
    turnover_text = f"{turnover:,.0f}"
    base = f"平均涨跌{_pct(avg_change)}、质量分{quality:.3f}、成交额{turnover_text}"
    if quality >= 65 and avg_change >= 0 and turnover > 0:
        return (
            f"强势跟踪：{base}；只有单标的PFIOS/账户闸门通过才保留Volume，"
            "若放量冲高但事件不支持则降额或观望。"
        )
    if quality >= 55 and avg_change < 0 and turnover > 0:
        return (
            f"下跌承接观察：{base}；14:30-14:55只看止跌和成交额收敛，"
            "放量破位或负面事件出现则取消买入候选。"
        )
    if quality < 40:
        return f"低质量过滤：{base}；不扩大买卖，除非连续2日质量分升至55且成交额>0。"
    return (
        f"中性观察：{base}；升级条件=成交额>0、事件原文核验无负面且PFIOS不Blocked；"
        "否则维持观望，不扩大Volume。"
    )


def _bubble_quality_score(item: dict[str, object], validation_by_symbol: dict[str, dict[str, str]]) -> float:
    validation = validation_by_symbol.get(str(item.get("symbol") or ""), {})
    score = 0.0
    if item.get("close") not in {"", None} and item.get("daily_change_pct") not in {"", None}:
        score += 18
    turnover = float(item.get("turnover") or 0)
    if turnover > 0:
        score += min(18, 8 + turnover / 120_000_000)
    change = abs(float(item.get("daily_change_pct") or 0))
    score += min(14, change * 450)
    status = str(validation.get("validation_status") or "")
    gate = str(validation.get("risk_gate") or "")
    if status == "ContinueResearch":
        score += 22
    elif status == "NeedsMoreEvidence":
        score += 11
    elif status == "DataQualityReview":
        score += 4
    else:
        score += 7
    if gate == "Pass":
        score += 12
    elif gate == "Blocked":
        score -= 6
    try:
        loss = validation.get("monte_carlo_loss_probability")
        if loss not in {"", None}:
            score += max(0, min(16, (1 - float(loss) - 0.45) / 0.25 * 16))
    except (TypeError, ValueError):
        pass
    return round(max(0, min(100, score)), 3)


def _pct(value: float) -> str:
    return f"{value * 100:.3f}%"


def _wrap_label(value: str, width: int) -> str:
    text = str(value)
    if len(text) <= width:
        return text
    chunks = []
    line = ""
    for part in text.split("、"):
        candidate = part if not line else line + "、" + part
        if len(candidate) > width and line:
            chunks.append(line)
            line = part
        else:
            line = candidate
    if line:
        chunks.append(line)
    return "\n".join(chunks[:2])


def _indicator_charts(item: dict[str, object], history: list[dict[str, float]], as_of: str) -> list[tuple[str, str]]:
    out_dir = image_dir(as_of, "kline_deep")
    out_dir.mkdir(parents=True, exist_ok=True)
    symbol = str(item["symbol"]).replace("/", "_")
    indicators = [
        ("MA", _plot_ma),
        ("EMA", _plot_ema),
        ("BOLL", _plot_boll),
        ("MACD", _plot_macd),
        ("VOL", _plot_volume),
        ("RSI", _plot_rsi),
        ("KDJ", _plot_kdj),
        ("MIX", _plot_mix),
    ]
    charts = []
    for label, plotter in indicators:
        path = out_dir / f"{symbol}_{label}.png"
        plotter(item, history, path)
        charts.append((label, str(path)))
    return charts


def _symbol_section(
    item: dict[str, object],
    summary: str,
    charts: list[tuple[str, str]],
    history: list[dict[str, float]],
    action: str,
    signal: dict[str, object],
) -> str:
    lines = [
        "<!-- PAGEBREAK -->",
        f"## {item['symbol']} {item['name']}：技术面、基本面、价值面综合分析",
        "",
        summary,
    ]
    for label, path in charts:
        lines.extend(["", "<!-- PAGEBREAK -->", f"### {label} 单独/组合分析", "", f"![{label}]({path})", "", _chart_note(label, item, history, action, signal)])
    return "\n".join(lines)


def _indicator_summary(
    item: dict[str, object],
    history: list[dict[str, float]],
    action: str,
    signal: dict[str, object],
) -> str:
    closes = [row["close"] for row in history]
    change = item.get("daily_change_pct")
    latest = closes[-1] if closes else item.get("close", "")
    rows = [
        {
            "dimension": "最终操作",
            "reading": signal["final_action"],
            "standard": "原建议 + 技术三要素：趋势、动能、成交量",
            "conclusion": signal["quality"],
            "operation": signal["operation_rule"],
        },
        {
            "dimension": "训练题答案",
            "reading": signal["training_answer"],
            "standard": "趋势延续/情绪脉冲/均值回归/震荡噪音四分类",
            "conclusion": signal["thought_process"],
            "operation": signal["if_confirmed_action"],
        },
        {
            "dimension": "等待样本",
            "reading": signal["sample_to_wait"],
            "standard": "1-3个交易日收盘价、成交量、MACD柱、MA20位置",
            "conclusion": signal["expected_result"],
            "operation": signal["if_failed_action"],
        },
    ]
    return (
        f"- 当前价格：{latest:.3f}；当日涨跌幅：{float(change or 0) * 100:.3f}%；原始建议：{action}。\n"
        f"- 判断结论：{signal['final_action']}。分析逻辑：{signal['thought_process']}。\n"
        f"- 事实证据：{signal['evidence']}。\n\n"
        f"- 基本面/价值面约束：{_fundamental_value_checkpoint(item)}\n\n"
        + _mini_table(rows)
    )


def _select_kline_universe(factors: list[dict[str, object]], advice: list[dict[str, object]]) -> list[dict[str, object]]:
    by_name = {str(item["name"]): item for item in factors}
    action_by_name = {str(row.get("Name")): str(row.get("Position", "")) for row in advice}
    supported = [item for item in factors if _to_yahoo_symbol(item) and item.get("asset_class") in {"Stock", "ETF", "Index"}]
    supported_symbols = {item.get("symbol") for item in supported}
    ranked = sorted([item for item in supported if item.get("daily_change_pct") not in {"", None}], key=lambda row: float(row["daily_change_pct"]), reverse=True)
    buys = [
        by_name[str(row["Name"])]
        for row in advice
        if _is_buy_action(str(row.get("Position", "")))
        and str(row["Name"]) in by_name
        and by_name[str(row["Name"])].get("symbol") in supported_symbols
    ]
    sells = [
        by_name[str(row["Name"])]
        for row in advice
        if _is_sell_action(str(row.get("Position", "")))
        and str(row["Name"]) in by_name
        and by_name[str(row["Name"])].get("symbol") in supported_symbols
    ]
    watches = [
        by_name[str(row["Name"])]
        for row in advice
        if str(row.get("Position", "")) in {"观察", "观望"}
        and str(row["Name"]) in by_name
        and by_name[str(row["Name"])].get("symbol") in supported_symbols
    ]
    neutral_ranked = [
        item
        for item in ranked
        if not _is_buy_action(action_by_name.get(str(item.get("name")), ""))
        and not _is_sell_action(action_by_name.get(str(item.get("name")), ""))
    ]
    if len(ranked) < 7:
        raise RuntimeError("K-line report requires at least 7 supported symbols with current quotes.")
    selected: list[dict[str, object]] = []
    selected = _append_until(selected, buys, 3, "建议买入技术候选")
    selected = _append_until(selected, watches, 3, "建议买入技术替代-观望")
    selected = _append_until(selected, neutral_ranked, 3, "建议买入技术替代-观望")
    selected = _append_until(selected, sells, 6, "建议卖出技术候选")
    selected = _append_until(selected, watches, 6, "建议卖出技术替代-观望")
    selected = _append_until(selected, list(reversed(neutral_ranked)), 6, "建议卖出技术替代-观望")
    selected = _append_until(selected, watches, 7, "中性观望候选")
    selected = _append_until(selected, ranked, 7, "中性观望替代")
    return selected


def _is_buy_action(action: str) -> bool:
    return any(token in action for token in ["建议买入", "买入", "补仓", "承接", "低仓位"])


def _is_sell_action(action: str) -> bool:
    return any(token in action for token in ["建议卖出", "卖出", "减仓", "减暴露", "降暴露"])


def _append_until(
    selected: list[dict[str, object]],
    candidates: list[dict[str, object]],
    target_count: int,
    slot_label: str,
) -> list[dict[str, object]]:
    output = list(selected)
    seen = {item.get("symbol") for item in output}
    for item in candidates:
        if len(output) >= target_count:
            break
        symbol = item.get("symbol")
        if symbol in seen:
            continue
        seen.add(symbol)
        output.append({**item, "kline_group": slot_label})
    return output


def _plot_ma(item: dict[str, object], history: list[dict[str, float]], path: Path) -> None:
    _line_chart(item, history, path, ["close", "ma20", "ma60"], "MA trend")


def _plot_ema(item: dict[str, object], history: list[dict[str, float]], path: Path) -> None:
    _line_chart(item, history, path, ["close", "ema12", "ema26"], "EMA trend")


def _plot_boll(item: dict[str, object], history: list[dict[str, float]], path: Path) -> None:
    _line_chart(item, history, path, ["close", "boll_upper", "ma20", "boll_lower"], "BOLL channel")


def _plot_macd(item: dict[str, object], history: list[dict[str, float]], path: Path) -> None:
    _line_chart(item, history, path, ["macd", "signal", "hist"], "MACD momentum")


def _plot_volume(item: dict[str, object], history: list[dict[str, float]], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _configure_matplotlib(plt)

    rows = _enriched(history)
    x = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(12, 4.4), dpi=150)
    ax.bar(x, [row["volume"] for row in rows], color="#4c78a8")
    ax.set_title(f"{item['symbol']} {item['name']} VOL")
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_rsi(item: dict[str, object], history: list[dict[str, float]], path: Path) -> None:
    _line_chart(item, history, path, ["rsi6", "rsi14"], "RSI")


def _plot_kdj(item: dict[str, object], history: list[dict[str, float]], path: Path) -> None:
    _line_chart(item, history, path, ["k", "d", "j"], "KDJ")


def _plot_mix(item: dict[str, object], history: list[dict[str, float]], path: Path) -> None:
    _line_chart(item, history, path, ["close", "ma20", "ema12", "boll_upper", "boll_lower"], "Mixed trend system")


def _line_chart(item: dict[str, object], history: list[dict[str, float]], path: Path, keys: list[str], title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _configure_matplotlib(plt)

    rows = _enriched(history)
    x = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(12, 4.4), dpi=150)
    for key in keys:
        ax.plot(x, [row.get(key, 0) for row in rows], label=key, linewidth=1.4)
    ax.set_title(f"{item['symbol']} {item['name']} {title}")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _enriched(history: list[dict[str, float]]) -> list[dict[str, float]]:
    rows = [dict(row) for row in history]
    closes = [row["close"] for row in rows]
    highs = [row["high"] for row in rows]
    lows = [row["low"] for row in rows]
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    signal = _ema([a - b for a, b in zip(ema12, ema26)], 9)
    rsi6 = _rsi(closes, 6)
    rsi14 = _rsi(closes, 14)
    k_values, d_values, j_values = _kdj(highs, lows, closes)
    for idx, row in enumerate(rows):
        ma20 = _mean(closes[max(0, idx - 19) : idx + 1])
        ma60 = _mean(closes[max(0, idx - 59) : idx + 1])
        std20 = _std(closes[max(0, idx - 19) : idx + 1])
        row.update(
            {
                "ma20": ma20,
                "ma60": ma60,
                "ema12": ema12[idx],
                "ema26": ema26[idx],
                "boll_upper": ma20 + 2 * std20,
                "boll_lower": ma20 - 2 * std20,
                "macd": ema12[idx] - ema26[idx],
                "signal": signal[idx],
                "hist": ema12[idx] - ema26[idx] - signal[idx],
                "rsi6": rsi6[idx],
                "rsi14": rsi14[idx],
                "k": k_values[idx],
                "d": d_values[idx],
                "j": j_values[idx],
            }
        )
    return rows


def _ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(alpha * value + (1 - alpha) * result[-1])
    return result


def _rsi(values: list[float], period: int) -> list[float]:
    output = []
    for idx in range(len(values)):
        window = values[max(0, idx - period) : idx + 1]
        gains = [max(0, window[i] - window[i - 1]) for i in range(1, len(window))]
        losses = [max(0, window[i - 1] - window[i]) for i in range(1, len(window))]
        avg_gain = _mean(gains) or 0.000001
        avg_loss = _mean(losses) or 0.000001
        output.append(100 - 100 / (1 + avg_gain / avg_loss))
    return output


def _kdj(highs: list[float], lows: list[float], closes: list[float]) -> tuple[list[float], list[float], list[float]]:
    k_values, d_values, j_values = [], [], []
    k, d = 50.0, 50.0
    for idx, close in enumerate(closes):
        high = max(highs[max(0, idx - 8) : idx + 1])
        low = min(lows[max(0, idx - 8) : idx + 1])
        rsv = 50.0 if high == low else (close - low) / (high - low) * 100
        k = 2 / 3 * k + 1 / 3 * rsv
        d = 2 / 3 * d + 1 / 3 * k
        j = 3 * k - 2 * d
        k_values.append(k)
        d_values.append(d)
        j_values.append(j)
    return k_values, d_values, j_values


def _chart_note(
    label: str,
    item: dict[str, object],
    history: list[dict[str, float]],
    action: str,
    signal: dict[str, object],
) -> str:
    rows = _enriched(history)
    latest = rows[-1]
    notes = {
        "MA": {
            "reading": f"收盘 {latest['close']:.3f} / MA20 {latest['ma20']:.3f} / MA60 {latest['ma60']:.3f}",
            "standard": "收盘价>MA20且MA20>MA60为趋势偏多；跌破MA20则买入候选转观望，跌破MA60为转弱。",
            "conclusion": signal["trend_conclusion"],
            "operation": signal["ma_action"],
        },
        "EMA": {
            "reading": f"EMA12 {latest['ema12']:.3f} / EMA26 {latest['ema26']:.3f}",
            "standard": "EMA12>EMA26为短线趋势占优；EMA12下穿EMA26为短线转弱。",
            "conclusion": signal["ema_conclusion"],
            "operation": signal["ema_action"],
        },
        "BOLL": {
            "reading": f"BOLL位置 {float(signal['boll_position']) * 100:.3f}%",
            "standard": "接近上轨>85%为追高风险；接近下轨<15%为超跌观察；中轨附近看方向选择。",
            "conclusion": signal["boll_conclusion"],
            "operation": signal["boll_action"],
        },
        "MACD": {
            "reading": f"MACD柱 {latest['hist']:.4f}",
            "standard": "柱状图连续扩大为动能增强；翻绿或收窄为动能衰减。",
            "conclusion": signal["macd_conclusion"],
            "operation": signal["macd_action"],
        },
        "VOL": {
            "reading": f"成交量/20日均量 {float(signal['volume_ratio']) * 100:.3f}%",
            "standard": ">=120%确认突破/下跌；80%-120%为一般确认；<80%信号可信度下降。",
            "conclusion": signal["volume_conclusion"],
            "operation": signal["volume_action"],
        },
        "RSI": {
            "reading": f"RSI14 {latest['rsi14']:.3f}",
            "standard": ">70偏过热，<30偏超跌，45-60为健康区间。",
            "conclusion": signal["rsi_conclusion"],
            "operation": signal["rsi_action"],
        },
        "KDJ": {
            "reading": f"K {latest['k']:.3f} / D {latest['d']:.3f} / J {latest['j']:.3f}",
            "standard": "K>D且J<90为短线偏强；J>100为过热；K<D为动能转弱。",
            "conclusion": signal["kdj_conclusion"],
            "operation": signal["kdj_action"],
        },
        "MIX": {
            "reading": f"趋势{signal['trend_score']} / 动能{signal['momentum_score']} / 成交量{signal['volume_score']} / 总分{signal['total_score']}",
            "standard": "MA/EMA/BOLL 看趋势区间，MACD/RSI/KDJ 看动能，VOL 看确认；三者同向时信号质量高。",
            "conclusion": signal["mix_conclusion"],
            "operation": signal["operation_rule"],
        },
    }
    row = notes[label]
    return _mini_table(
        [
            {
                "dimension": label,
                "reading": row["reading"],
                "standard": row["standard"],
                "conclusion": row["conclusion"],
                "operation": row["operation"],
            }
        ]
    )


def _technical_signal(item: dict[str, object], history: list[dict[str, float]], action: str) -> dict[str, object]:
    rows = _enriched(history)
    latest = rows[-1]
    prev = rows[-2] if len(rows) > 1 else latest
    volume_ma20 = _mean([row["volume"] for row in rows[-20:]]) or 1.0
    volume_ratio = latest["volume"] / volume_ma20
    boll_range = max(latest["boll_upper"] - latest["boll_lower"], 0.000001)
    boll_position = (latest["close"] - latest["boll_lower"]) / boll_range
    trend_score = 0
    if latest["close"] > latest["ma20"] > latest["ma60"]:
        trend_score += 2
    elif latest["close"] > latest["ma20"]:
        trend_score += 1
    elif latest["close"] < latest["ma20"] < latest["ma60"]:
        trend_score -= 2
    elif latest["close"] < latest["ma20"]:
        trend_score -= 1
    ema_score = 1 if latest["ema12"] > latest["ema26"] else -1
    momentum_score = 0
    if latest["hist"] > 0 and latest["hist"] >= prev.get("hist", latest["hist"]):
        momentum_score += 1
    elif latest["hist"] < 0:
        momentum_score -= 1
    if latest["k"] > latest["d"] and latest["j"] < 95:
        momentum_score += 1
    elif latest["k"] < latest["d"]:
        momentum_score -= 1
    if latest["rsi14"] > 72:
        momentum_score -= 1
    elif 45 <= latest["rsi14"] <= 65:
        momentum_score += 1
    elif latest["rsi14"] < 32:
        momentum_score -= 1
    volume_score = 1 if volume_ratio >= 1.2 else -1 if volume_ratio < 0.8 else 0
    boll_score = -1 if boll_position > 0.88 else 1 if 0.25 <= boll_position <= 0.75 else 0
    total_score = trend_score + ema_score + momentum_score + volume_score + boll_score
    quality = "High" if total_score >= 4 and volume_score >= 0 else "Medium" if total_score >= 1 else "Low"
    final_action, operation_rule = _final_action(action, total_score, quality, volume_score, boll_position)
    training_answer = _training_answer(trend_score, momentum_score, volume_score, boll_position, latest)
    thought = _thought_process(training_answer, latest, trend_score, momentum_score, volume_ratio, boll_position)
    sample_to_wait = _sample_to_wait(training_answer, latest, trend_score, momentum_score, volume_ratio, boll_position)
    expected = _expected_result(training_answer, latest, trend_score, momentum_score, volume_ratio, boll_position)
    if_confirmed = _confirmed_action(action, final_action)
    if_failed = _failed_action(action)
    return {
        "quality": quality,
        "final_action": final_action,
        "operation_rule": operation_rule,
        "trend_score": trend_score,
        "momentum_score": momentum_score,
        "volume_score": volume_score,
        "boll_position": round(boll_position, 6),
        "volume_ratio": round(volume_ratio, 6),
        "total_score": total_score,
        "training_answer": training_answer,
        "thought_process": thought,
        "sample_to_wait": sample_to_wait,
        "expected_result": expected,
        "if_confirmed_action": if_confirmed,
        "if_failed_action": if_failed,
        "evidence": (
            f"MA20 {latest['ma20']:.3f}、MA60 {latest['ma60']:.3f}、EMA12/26 {latest['ema12']:.3f}/{latest['ema26']:.3f}、"
            f"MACD柱 {latest['hist']:.4f}、RSI14 {latest['rsi14']:.3f}、K/D/J {latest['k']:.3f}/{latest['d']:.3f}/{latest['j']:.3f}、"
            f"成交量倍率 {volume_ratio:.3f}。"
        ),
        "trend_conclusion": "趋势偏多" if trend_score > 0 else "趋势偏空" if trend_score < 0 else "趋势震荡",
        "ema_conclusion": "短线趋势占优" if ema_score > 0 else "短线趋势转弱",
        "boll_conclusion": "接近上轨，追高风险上升" if boll_position > 0.88 else "接近下轨，观察修复" if boll_position < 0.15 else "处于通道中部，等待方向",
        "macd_conclusion": "动能增强" if latest["hist"] > 0 and latest["hist"] >= prev.get("hist", latest["hist"]) else "动能衰减",
        "volume_conclusion": "成交量确认" if volume_score > 0 else "缩量，信号质量下降" if volume_score < 0 else "成交量一般确认",
        "rsi_conclusion": "过热" if latest["rsi14"] > 72 else "超跌" if latest["rsi14"] < 32 else "动能健康/中性",
        "kdj_conclusion": "短线偏强" if latest["k"] > latest["d"] and latest["j"] < 95 else "短线转弱或过热",
        "mix_conclusion": f"{quality} signal；趋势、动能、成交量一致性得分 {total_score}",
        "ma_action": _indicator_action(action, trend_score),
        "ema_action": _indicator_action(action, ema_score),
        "boll_action": _indicator_action(action, -1 if boll_position > 0.88 else 1 if boll_position < 0.25 else 0),
        "macd_action": _indicator_action(action, 1 if latest["hist"] > 0 else -1),
        "volume_action": _indicator_action(action, volume_score),
        "rsi_action": _indicator_action(action, -1 if latest["rsi14"] > 72 else 1 if latest["rsi14"] < 40 else 0),
        "kdj_action": _indicator_action(action, 1 if latest["k"] > latest["d"] and latest["j"] < 95 else -1),
    }


def _final_action(action: str, total_score: int, quality: str, volume_score: int, boll_position: float) -> tuple[str, str]:
    if _account_update_pending(action):
        if _is_buy_action(action):
            return "账户待更新-买入不执行", "Volume=0；先更新支付宝流水/持仓并重生成报告，技术信号只保留买入候选方向。"
        if _is_sell_action(action):
            return "账户待更新-卖出不执行", "Volume=0；先更新支付宝流水/持仓并重生成报告，技术信号只保留卖出候选方向。"
        return "账户待更新-观望", "账户未更新，不新增买卖。"
    if _is_buy_action(action):
        if total_score >= 3 and volume_score >= 0 and boll_position < 0.88:
            return "买入候选保留", "账户、PFIOS、尾盘价格和成交额全部通过后重算候选Volume；突破上轨不追高。"
        if total_score >= 1:
            return "买入候选降级", "Volume=0；等待收盘站稳 MA20 且成交量确认后重算。"
        return "改为观望", "不新增买入；等待收盘重新站上 MA20 且成交量确认。"
    if _is_sell_action(action):
        if total_score <= 1 or boll_position > 0.85:
            return "卖出候选保留", "账户确认且尾盘未放量突破时重算候选Volume；若次日放量突破则暂停。"
        return "卖出候选降级", "Volume=0；趋势继续放量时暂停卖出，保留风险观察。"
    if "等待确认" in action:
        return "等待确认", "已有订单未确认，不重复买卖。"
    if total_score >= 4:
        return "观望不追", "等待回踩 MA20 后再评估买入。"
    if total_score <= -2:
        return "观望防跌", "等待止跌和成交量缩小后再评估。"
    return "继续观望", "没有足够一致信号，不做新动作。"


def _indicator_action(action: str, score: int) -> str:
    if _account_update_pending(action):
        return "账户未更新，不执行；更新后重算"
    if _is_buy_action(action):
        return "支持买入候选，仍需闸门通过后重算" if score > 0 else "买入取消或Volume=0" if score < 0 else "买入需等待确认"
    if _is_sell_action(action):
        return "支持卖出候选，仍需账户确认" if score <= 0 else "卖出暂停或Volume=0" if score > 0 else "卖出需等待确认"
    if score > 0:
        return "观望偏强；需价格/动能/成交额连续2日同向才升级，否则Volume=0"
    if score < 0:
        return "观望防跌；若价格/动能/成交额继续转弱则维持Volume=0并进入风险观察"
    return "维持观望；缺少同向触发条件，Volume=0"


def _training_answer(trend_score: int, momentum_score: int, volume_score: int, boll_position: float, latest: dict[str, float]) -> str:
    if trend_score > 0 and momentum_score > 0 and volume_score >= 0:
        return "趋势延续"
    if trend_score > 0 and (volume_score < 0 or boll_position > 0.88 or latest["rsi14"] > 72):
        return "情绪脉冲"
    if trend_score < 0 and boll_position < 0.2 and latest["rsi14"] < 40:
        return "均值回归候选"
    return "震荡噪音"


def _thought_process(answer: str, latest: dict[str, float], trend_score: int, momentum_score: int, volume_ratio: float, boll_position: float) -> str:
    return (
        f"{answer}；趋势分 {trend_score}，动能分 {momentum_score}，成交量倍率 {volume_ratio:.3f}，"
        f"BOLL位置 {boll_position * 100:.3f}%，RSI14 {latest['rsi14']:.3f}。"
    )


def _sample_to_wait(
    answer: str,
    latest: dict[str, float],
    trend_score: int,
    momentum_score: int,
    volume_ratio: float,
    boll_position: float,
) -> str:
    if answer == "趋势延续":
        return (
            f"后续1-2日收盘价守住MA20 {latest['ma20']:.3f}；"
            f"成交量倍率维持>=1.000（当前{volume_ratio:.3f}）；MACD柱保持不低于0（当前{latest['hist']:.4f}）。"
        )
    if answer == "情绪脉冲":
        return (
            f"后续1日收盘不跌回MA20 {latest['ma20']:.3f}；"
            f"BOLL位置从{boll_position * 100:.3f}%回落但仍高于中轨；成交量倍率>=1.200才算延续。"
        )
    if answer == "均值回归候选":
        return (
            f"后续1-3日收盘重新站上MA20 {latest['ma20']:.3f}或跌幅明显收窄；"
            f"RSI14从{latest['rsi14']:.3f}修复到40以上；成交量倍率降至0.800-1.200。"
        )
    if trend_score < 0:
        return (
            f"后续2日必须收复MA20 {latest['ma20']:.3f}，否则维持弱势；"
            f"MACD柱需从{latest['hist']:.4f}转正或连续改善，K/D需重新金叉。"
        )
    if momentum_score < 0:
        return (
            f"后续2日价格需保持在MA60 {latest['ma60']:.3f}上方且MACD柱改善；"
            f"RSI14当前{latest['rsi14']:.3f}，低于45则不升级。"
        )
    if volume_ratio < 0.8:
        return (
            f"后续1-2日成交量倍率需从{volume_ratio:.3f}恢复到0.900以上；"
            f"价格同时站稳MA20 {latest['ma20']:.3f}才允许升级。"
        )
    return (
        f"后续2日需要收盘突破MA20 {latest['ma20']:.3f}或跌破MA60 {latest['ma60']:.3f}给出方向；"
        f"当前BOLL位置{boll_position * 100:.3f}%，未脱离中轨前只做观察。"
    )


def _expected_result(
    answer: str,
    latest: dict[str, float],
    trend_score: int,
    momentum_score: int,
    volume_ratio: float,
    boll_position: float,
) -> str:
    if answer == "趋势延续":
        return f"价格沿MA20 {latest['ma20']:.3f}上方运行，MACD柱不转负，成交量不低于20日均量。"
    if answer == "情绪脉冲":
        return f"若只是脉冲，次日价格跌回MA20 {latest['ma20']:.3f}附近或成交量倍率低于1.000。"
    if answer == "均值回归候选":
        return f"跌幅收窄，RSI14从{latest['rsi14']:.3f}向45-55修复，成交量倍率回到0.800-1.200。"
    if trend_score < 0:
        return f"弱势被推翻的标准是收盘站回MA20 {latest['ma20']:.3f}且MACD柱改善；否则继续防守。"
    if momentum_score < 0:
        return f"动能修复标准是MACD柱改善、K>D且RSI14高于45；当前RSI14为{latest['rsi14']:.3f}。"
    if volume_ratio < 0.8:
        return f"量能确认标准是成交量倍率恢复到0.900以上；当前{volume_ratio:.3f}不足以支持升级。"
    return f"价格突破MA20 {latest['ma20']:.3f}/MA60 {latest['ma60']:.3f}区间后再判断方向。"


def _confirmed_action(action: str, final_action: str) -> str:
    if _account_update_pending(action):
        return "先更新支付宝流水/持仓并重生成报告；更新前不执行。"
    if _is_buy_action(action):
        return "满足样本后保留买入候选；账户、PFIOS和尾盘量价通过后重算Volume。"
    if _is_sell_action(action):
        return "满足样本后维持卖出；若趋势突破确认则停止追加卖出。"
    return f"{final_action}，不提前交易。"


def _failed_action(action: str) -> str:
    if _account_update_pending(action):
        return "账户未更新前不执行；更新后若样本不满足则取消候选。"
    if _is_buy_action(action):
        return "不满足则取消买入，已有持仓只观察不补。"
    if _is_sell_action(action):
        return "不满足则暂停卖出，避免卖在趋势启动初期。"
    return "不满足则继续观望。"


def _mini_table(rows: list[dict[str, object]]) -> str:
    header = "| 维度 | 当前读数 | 参考标准 | 判断结论 | 建议操作 |\n| --- | --- | --- | --- | --- |"
    body = [
        f"| {row['dimension']} | {row['reading']} | {row['standard']} | {row['conclusion']} | {row['operation']} |"
        for row in rows
    ]
    return "\n".join([header, *body])


def _account_update_pending(action: str) -> bool:
    return "账户待更新" in action


def _fundamental_value_checkpoint(item: dict[str, object]) -> str:
    asset_class = str(item.get("asset_class") or "")
    pe = item.get("pe")
    pb = item.get("pb")
    group = str(item.get("research_group") or item.get("industry") or "未分类")
    if pe not in {"", None} or pb not in {"", None}:
        return f"{group}；PE {pe if pe not in {'', None} else '缺失'}，PB {pb if pb not in {'', None} else '缺失'}。若估值高位且技术过热，买入候选转观望；若估值低位且技术止跌，才保留承接。"
    if asset_class in {"ETF", "Fund", "Index"}:
        return f"{group}；ETF/指数用跟踪资产、行业估值分位和主题景气作价值代理。技术信号只决定执行时机，不能单独扩大Volume。"
    return f"{group}；PE/PB缺失时启用行业估值分位代理，技术信号质量最高降一级，直到财报/估值源补齐。"


def _to_yahoo_symbol(item: dict[str, object]) -> str:
    symbol = str(item["symbol"])
    exchange = str(item.get("exchange") or "")
    asset_class = str(item.get("asset_class") or "")
    if asset_class == "Index" and symbol not in USER_TRADABLE_INDEX_SYMBOLS:
        return ""
    if asset_class == "Index" and symbol in USER_TRADABLE_INDEX_YAHOO_PROXIES:
        return USER_TRADABLE_INDEX_YAHOO_PROXIES[symbol]
    if exchange == "US":
        return symbol
    if exchange == "SSE":
        return f"{symbol}.SS"
    if exchange == "SZSE":
        return f"{symbol}.SZ"
    if exchange == "SEHK":
        return f"{symbol.zfill(4)}.HK"
    return ""


def _is_cn(item: dict[str, object]) -> bool:
    return str(item.get("exchange") or "") in {"SSE", "SZSE"}


def _fill_unique(primary: list[dict[str, object]], fallback: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    rows = _unique_items(primary)
    for item in fallback:
        if len(rows) >= count:
            break
        if item not in rows:
            rows.append(item)
    return rows


def _unique_items(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    seen = set()
    output = []
    for row in rows:
        symbol = row.get("symbol")
        if symbol in seen:
            continue
        seen.add(symbol)
        output.append(row)
    return output


def _series_value(values: object, idx: int) -> object:
    if not isinstance(values, list) or idx >= len(values):
        return ""
    return values[idx]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    avg = _mean(values)
    return (sum((value - avg) ** 2 for value in values) / len(values)) ** 0.5


def _configure_matplotlib(plt: object) -> None:
    plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "STHeiti", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def _verified_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _blend(light: str, dark: str, ratio: float) -> str:
    def rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    a = rgb(light)
    b = rgb(dark)
    mixed = tuple(round(a[idx] + (b[idx] - a[idx]) * ratio) for idx in range(3))
    return "#{:02x}{:02x}{:02x}".format(*mixed)
