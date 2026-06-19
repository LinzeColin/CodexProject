from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from src.pfi_os.engine import latest_result_by_symbol
from src.reporting.paths import image_dir
from src.reporting.renderer import format_percent


def decision_quality_dashboard(
    as_of: str,
    report_key: str,
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    advice: list[dict[str, object]],
    account_summary: dict[str, object],
    exposure: dict[str, object] | None = None,
) -> str:
    out_dir = image_dir(as_of, "decision_quality_dashboard")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"decision_quality_{report_key}_{as_of.replace('-', '')}.png"
    _plot_dashboard(path, as_of, factors, events, advice, account_summary, exposure or {})
    return (
        f"![研究质量检查图]({path})\n\n"
        "- 图表说明：左上为主题热度，左下为研究质量，右上为持仓风险，右下为复盘有效性。"
        "该图用于检查研究线索是否值得进入 PFIOS 验证，不作为最终账户操作依据。"
    )


def _plot_dashboard(
    path: Path,
    as_of: str,
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    advice: list[dict[str, object]],
    account_summary: dict[str, object],
    exposure: dict[str, object],
) -> None:
    pfi_os_by_symbol = latest_result_by_symbol(as_of)
    plt = _plt()
    fig, axes = plt.subplots(2, 2, figsize=(13.4, 8.2), dpi=160)
    fig.patch.set_facecolor("#f7f9fb")
    _plot_theme_heat(axes[0][0], factors, events)
    _plot_research_quality(axes[1][0], factors, events, advice, pfi_os_by_symbol)
    _plot_holding_risk(axes[0][1], factors, advice, account_summary, exposure)
    _plot_review_dashboard(axes[1][1], factors, advice, pfi_os_by_symbol)
    fig.suptitle("Research Quality Check", fontsize=14, fontweight="bold", color="#102a43")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path)
    plt.close(fig)


def _plot_theme_heat(ax, factors: list[dict[str, object]], events: list[dict[str, str]]) -> None:
    rows = _theme_rows(factors, events)[:9]
    if not rows:
        _empty(ax, "暂无主题行情")
        return
    labels = [_short(row["theme"], 15) for row in rows]
    values = [row["change"] * 100 for row in rows]
    colors = ["#c1121f" if value >= 0 else "#16833a" for value in values]
    y = list(range(len(rows)))
    ax.barh(y, values, color=colors, alpha=0.82)
    for idx, row in enumerate(rows):
        marker = "E" if row["has_event"] else "-"
        ax.text(values[idx], idx, f" {values[idx]:.3f}% {marker}", va="center", fontsize=7.5, color="#102a43")
    ax.axvline(0, color="#334e68", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("今日强弱 %")
    ax.set_title("主题热度 | E=事件催化")
    ax.grid(axis="x", alpha=0.2)


def _plot_research_quality(
    ax,
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    advice: list[dict[str, object]],
    pfi_os_by_symbol: dict[str, dict[str, str]],
) -> None:
    levels = [_confidence_level(item, events, _advice_for(item, advice), pfi_os_by_symbol) for item in factors]
    counts = Counter(levels)
    labels = ["High", "Medium", "Low", "Watch", "Insufficient"]
    keys = ["High Confidence Research", "Medium Confidence Research", "Low Confidence Research", "Watch Only", "Insufficient Evidence"]
    values = [counts.get(key, 0) for key in keys]
    colors = ["#1f7a4d", "#2f80ed", "#f59f00", "#486581", "#9b2226"]
    ax.bar(labels, values, color=colors, alpha=0.84)
    for idx, value in enumerate(values):
        ax.text(idx, value + 0.04, str(value), ha="center", fontsize=8)
    data_gaps = sum(1 for item in factors if item.get("close") in {"", None} or item.get("turnover") in {"", None})
    validation_gaps = sum(
        1
        for item in factors
        if _validation_status(item, _advice_for(item, advice), pfi_os_by_symbol)
        in {"NotValidated", "NeedsMoreEvidence", "DataQualityReview", "DoNotUse"}
    )
    ax.text(
        0.02,
        0.92,
        f"数据异常 {data_gaps} | 未充分验证 {validation_gaps}",
        transform=ax.transAxes,
        fontsize=8,
        color="#334e68",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "#ffffff", "edgecolor": "#d9e2ec"},
    )
    ax.set_ylim(0, max(values + [1]) * 1.35)
    ax.set_title("研究质量 Dashboard")
    ax.grid(axis="y", alpha=0.2)


def _plot_holding_risk(
    ax,
    factors: list[dict[str, object]],
    advice: list[dict[str, object]],
    account_summary: dict[str, object],
    exposure: dict[str, object],
) -> None:
    total_holding = _float(account_summary.get("total_holding_amount"))
    pending = _float(account_summary.get("pending_order_amount"))
    cash = _float(exposure.get("cash_weight"))
    if cash <= 0:
        cash = max(0.0, 1.0 - sum(_float(row.get("Volume")) for row in advice))
    max_holding = max((_float(row.get("holding_amount")) for row in advice), default=0.0)
    max_single = max_holding / total_holding if total_holding > 0 else 0.0
    max_theme = _max_theme_weight(factors, advice, total_holding)
    pending_ratio = pending / total_holding if total_holding > 0 else 0.0
    scenario_loss = _downside_scenario(advice, total_holding)
    labels = ["现金缓冲", "单标的集中", "主题集中", "待确认/持仓", "下跌情景"]
    values = [cash, max_single, max_theme, pending_ratio, scenario_loss]
    colors = [_risk_color(value, idx) for idx, value in enumerate(values)]
    ax.bar(labels, [value * 100 for value in values], color=colors, alpha=0.84)
    for idx, value in enumerate(values):
        ax.text(idx, value * 100 + 0.15, format_percent(value), ha="center", fontsize=7.5)
    ax.set_ylabel("占比")
    ax.set_title("持仓风险 Dashboard")
    ax.tick_params(axis="x", labelrotation=18)
    ax.grid(axis="y", alpha=0.2)


def _plot_review_dashboard(
    ax,
    factors: list[dict[str, object]],
    advice: list[dict[str, object]],
    pfi_os_by_symbol: dict[str, dict[str, str]],
) -> None:
    weighted = _weighted_return(advice, factors)
    active = [row for row in advice if _float(row.get("Volume")) > 0]
    queued = sum(1 for row in active if _validation_status(_factor_for(row, factors), row, pfi_os_by_symbol) == "ValidationQueued")
    weak_evidence = sum(
        1
        for row in active
        if _validation_status(_factor_for(row, factors), row, pfi_os_by_symbol)
        in {"NeedsMoreEvidence", "DataQualityReview", "NotValidated", "DoNotUse"}
    )
    positive_themes = sum(1 for row in _theme_rows(factors, []) if row["change"] > 0)
    metrics = [
        ("纸面收益", weighted * 100, "%"),
        ("重点线索", float(len(active)), "个"),
        ("验证排队", float(queued), "个"),
        ("证据不足", float(weak_evidence), "个"),
        ("走强主题", float(positive_themes), "个"),
    ]
    labels = [item[0] for item in metrics]
    values = [item[1] for item in metrics]
    colors = ["#c1121f" if values[0] >= 0 else "#16833a", "#486581", "#2f80ed", "#f59f00", "#1f7a4d"]
    ax.barh(labels, values, color=colors, alpha=0.84)
    for idx, (_, value, unit) in enumerate(metrics):
        ax.text(value, idx, f" {value:.3f}{unit}", va="center", fontsize=8)
    ax.axvline(0, color="#334e68", linewidth=0.8)
    ax.set_title("复盘 Dashboard")
    ax.grid(axis="x", alpha=0.2)


def _theme_rows(factors: list[dict[str, object]], events: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    event_blob = " ".join(str(event.get("industry", "")) + " " + str(event.get("title", "")) for event in events)
    for item in factors:
        theme = str(item.get("research_group") or item.get("industry") or "未分类")
        grouped[theme].append(item)
    rows = []
    for theme, items in grouped.items():
        changes = [_float(item.get("daily_change_pct")) for item in items if item.get("daily_change_pct") not in {"", None}]
        turnover = sum(_float(item.get("turnover")) for item in items)
        rows.append(
            {
                "theme": theme,
                "change": sum(changes) / len(changes) if changes else 0.0,
                "turnover": turnover,
                "has_event": theme in event_blob,
            }
        )
    return sorted(rows, key=lambda row: (abs(float(row["change"])), float(row["turnover"])), reverse=True)


def _confidence_level(
    item: dict[str, object],
    events: list[dict[str, str]],
    advice_row: dict[str, object],
    pfi_os_by_symbol: dict[str, dict[str, str]],
) -> str:
    score = 0
    event_blob = " ".join(str(event.get("related_symbols", "")) + " " + str(event.get("title", "")) for event in events)
    if item.get("close") not in {"", None} and item.get("daily_change_pct") not in {"", None}:
        score += 25
    if item.get("turnover") not in {"", None}:
        score += 15
    if str(item.get("name", "")) in event_blob or str(item.get("symbol", "")) in event_blob:
        score += 15
    if abs(_float(item.get("daily_change_pct"))) > 0.01:
        score += 10
    if item.get("pe") not in {"", None, ""} or item.get("pb") not in {"", None, ""}:
        score += 10
    if _float(advice_row.get("holding_amount")) > 0:
        score += 10
    validation_status = _validation_status(item, advice_row, pfi_os_by_symbol)
    if validation_status == "ContinueResearch":
        score += 15
    elif validation_status == "ValidationQueued":
        score += 6
    return _cap_confidence_level(_confidence_level_from_score(score), validation_status)


def _validation_status(
    item: dict[str, object],
    advice_row: dict[str, object],
    pfi_os_by_symbol: dict[str, dict[str, str]] | None = None,
) -> str:
    symbol = str(item.get("symbol") or advice_row.get("symbol") or "")
    validation = (pfi_os_by_symbol or {}).get(symbol, {})
    if validation.get("validation_status"):
        return str(validation["validation_status"])
    if item.get("close") in {"", None} or item.get("daily_change_pct") in {"", None}:
        return "DataQualityReview"
    if _float(advice_row.get("Volume")) > 0:
        return "ValidationQueued"
    if abs(_float(item.get("daily_change_pct"))) > 0.02:
        return "NeedsMoreEvidence"
    return "NotValidated"


def _confidence_level_from_score(score: int) -> str:
    if score >= 75:
        return "High Confidence Research"
    if score >= 55:
        return "Medium Confidence Research"
    if score >= 35:
        return "Low Confidence Research"
    if score >= 20:
        return "Watch Only"
    return "Insufficient Evidence"


def _cap_confidence_level(level: str, pfi_os_status: str) -> str:
    order = {
        "Insufficient Evidence": 0,
        "Watch Only": 1,
        "Low Confidence Research": 2,
        "Medium Confidence Research": 3,
        "High Confidence Research": 4,
    }
    caps = {
        "ContinueResearch": "High Confidence Research",
        "ValidationQueued": "Medium Confidence Research",
        "NeedsMoreEvidence": "Watch Only",
        "DataQualityReview": "Insufficient Evidence",
        "DoNotUse": "Insufficient Evidence",
        "WatchOnly": "Watch Only",
        "NotValidated": "Watch Only",
    }
    cap = caps.get(pfi_os_status, "Watch Only")
    return level if order[level] <= order[cap] else cap


def _weighted_return(advice: list[dict[str, object]], factors: list[dict[str, object]]) -> float:
    factor_by_name = {str(item.get("name")): item for item in factors}
    weighted = 0.0
    total_weight = 0.0
    for row in advice:
        weight = _float(row.get("Volume"))
        if weight <= 0:
            continue
        factor = factor_by_name.get(str(row.get("Name")), {})
        change = factor.get("daily_change_pct")
        if change in {"", None}:
            continue
        weighted += _float(change) * weight
        total_weight += weight
    return weighted / total_weight if total_weight else 0.0


def _max_theme_weight(factors: list[dict[str, object]], advice: list[dict[str, object]], total_holding: float) -> float:
    if total_holding <= 0:
        return 0.0
    factor_by_name = {str(item.get("name")): item for item in factors}
    grouped: dict[str, float] = defaultdict(float)
    for row in advice:
        factor = factor_by_name.get(str(row.get("Name")), {})
        theme = str(factor.get("research_group") or factor.get("industry") or "未分类")
        grouped[theme] += _float(row.get("holding_amount"))
    return max(grouped.values(), default=0.0) / total_holding


def _downside_scenario(advice: list[dict[str, object]], total_holding: float) -> float:
    if total_holding <= 0:
        return 0.0
    exposed = sum(_float(row.get("holding_amount")) for row in advice if _float(row.get("holding_amount")) > 0)
    return exposed * 0.03 / total_holding


def _advice_for(item: dict[str, object], advice: list[dict[str, object]]) -> dict[str, object]:
    name = str(item.get("name"))
    for row in advice:
        if str(row.get("Name")) == name:
            return row
    return {}


def _factor_for(row: dict[str, object], factors: list[dict[str, object]]) -> dict[str, object]:
    name = str(row.get("Name"))
    for item in factors:
        if str(item.get("name")) == name:
            return item
    return {}


def _risk_color(value: float, idx: int) -> str:
    if idx == 0:
        return "#1f7a4d" if value >= 0.2 else "#f59f00"
    return "#c1121f" if value >= 0.2 else "#486581"


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.sans-serif"] = [
        "PingFang SC",
        "Heiti SC",
        "Arial Unicode MS",
        "Noto Sans CJK SC",
        "DejaVu Sans",
    ]
    return plt


def _empty(ax, title: str) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.5, title, ha="center", va="center", fontsize=11, color="#52606d", transform=ax.transAxes)
    ax.set_title(title)


def _float(value: object) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def _short(value: object, max_len: int) -> str:
    text = str(value)
    return text if len(text) <= max_len else text[: max_len - 1] + "..."
