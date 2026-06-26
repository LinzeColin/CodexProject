from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from src.accounting.alipay_ledger import TRADE_LEDGER, load_current_positions, load_pending_orders, load_position_candidates
from src.data_io import read_csv
from src.reporting.paths import image_dir
from src.reporting.renderer import format_percent


def account_dashboard(
    as_of: str,
    report_key: str,
    account_summary: dict[str, object],
    advice: list[dict[str, object]],
) -> str:
    out_dir = image_dir(as_of, "account_dashboard")
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{report_key}_{as_of.replace('-', '')}"
    kpi = out_dir / f"account_kpi_{prefix}.png"
    position_pending = out_dir / f"position_pending_{prefix}.png"
    action_flow = out_dir / f"action_flow_{prefix}.png"
    _plot_account_kpis(account_summary, kpi)
    _plot_position_pending(as_of, position_pending)
    _plot_action_flow(as_of, advice, action_flow)
    return (
        f"![账户关键指标]({kpi})\n\n"
        f"![持仓收益与待确认订单]({position_pending})\n\n"
        f"![建议动作与支付宝历史交易流]({action_flow})\n\n"
        "- 图表说明：三张持仓图统一放在报告末尾；第一张看账户总体，第二张看单项持仓/收益/待确认订单，第三张看本报告买卖结构和上一周支付宝现金流。"
    )


def _plot_account_kpis(account_summary: dict[str, object], path: Path) -> None:
    plt = _plt()
    labels = ["持仓总金额", "持有收益", "持有收益率", "待确认金额", "待确认笔数", "当日/昨日收益"]
    values = [
        _money(account_summary.get("total_holding_amount")),
        _money(account_summary.get("total_holding_return_amount")),
        format_percent(_float(account_summary.get("total_holding_return_pct"))),
        _money(account_summary.get("pending_order_amount")),
        f"{int(_float(account_summary.get('pending_order_count')))}",
        _money(account_summary.get("daily_return_amount")),
    ]
    fig, axes = plt.subplots(1, 6, figsize=(13.2, 2.35), dpi=160)
    fig.patch.set_facecolor("#f7f9fb")
    status = str(account_summary.get("source_label") or "未导入确认持仓")
    for ax, label, value in zip(axes.flatten(), labels, values):
        ax.set_facecolor("#ffffff")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#d9e2ec")
        ax.text(0.06, 0.68, label, transform=ax.transAxes, fontsize=8.5, color="#52606d")
        ax.text(0.06, 0.28, value, transform=ax.transAxes, fontsize=12.5, color="#102a43", fontweight="bold")
    fig.suptitle(f"账户关键指标 | {status}", fontsize=13, color="#102a43")
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.savefig(path)
    plt.close(fig)


def _plot_position_pending(as_of: str, path: Path) -> None:
    plt = _plt()
    rows = load_current_positions() or load_position_candidates(as_of)
    rows = [row for row in rows if _float(row.get("amount") or row.get("holding_amount")) > 0]
    pending_by_name = _pending_by_name()
    rows.sort(
        key=lambda row: _float(row.get("amount") or row.get("holding_amount"))
        + pending_by_name.get(str(row.get("name") or ""), 0.0),
        reverse=True,
    )
    rows = rows[:12]
    fig, ax = plt.subplots(figsize=(12, max(3.6, len(rows) * 0.36)), dpi=160)
    if not rows:
        _empty_chart(ax, "暂无确认持仓明细")
    else:
        labels = [_short(row.get("name") or row.get("symbol") or "未命名", 18) for row in rows]
        amounts = [_float(row.get("amount") or row.get("holding_amount")) for row in rows]
        returns = [_float(row.get("holding_return_amount")) for row in rows]
        pending = [pending_by_name.get(str(row.get("name") or ""), 0.0) for row in rows]
        y = list(range(len(rows)))
        ax.barh(y, amounts, color="#486581", alpha=0.82, label="持仓金额")
        ax.barh(y, pending, left=amounts, color="#f59f00", alpha=0.88, label="待确认订单")
        ax.barh(y, returns, color=["#c1121f" if value >= 0 else "#16833a" for value in returns], alpha=0.72, label="持有收益")
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("金额 CNY")
        ax.set_title("持仓金额、持有收益与待确认订单")
        ax.legend(fontsize=8)
        ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_action_flow(as_of: str, advice: list[dict[str, object]], path: Path) -> None:
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.2), dpi=160)
    _draw_advice_actions(advice, axes[0])
    _draw_trade_flow(as_of, axes[1])
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _draw_advice_actions(advice: list[dict[str, object]], ax) -> None:
    grouped: dict[str, float] = defaultdict(float)
    for row in advice:
        action = str(row.get("Position") or "观察")
        grouped[_action_bucket(action)] += _float(row.get("Volume"))
    labels = ["建议买入", "建议卖出", "等待确认", "观望"]
    values = [grouped.get(label, 0.0) * 100 for label in labels]
    colors = ["#c1121f", "#16833a", "#f59f00", "#486581"]
    ax.bar(labels, values, color=colors, alpha=0.82)
    for idx, value in enumerate(values):
        ax.text(idx, value + 0.05, f"{value:.3f}%", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("建议 Volume")
    ax.set_title("本报告建议动作分布")
    ax.grid(axis="y", alpha=0.22)


def _draw_trade_flow(as_of: str, ax) -> None:
    rows = read_csv(TRADE_LEDGER) if TRADE_LEDGER.exists() else []
    days = _previous_week_dates(as_of)
    daily: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in rows:
        day = _day_key(row.get("trade_date") or row.get("order_time"))
        if day not in days:
            continue
        side = str(row.get("side") or "其他")
        amount = _float(row.get("order_amount") or row.get("confirmed_amount"))
        daily[day][_side_bucket(side)] += amount
    if not days:
        _empty_chart(ax, "暂无上一周交易流水")
        return
    buys = [daily[day].get("买入", 0.0) for day in days]
    sells = [daily[day].get("卖出", 0.0) for day in days]
    refunds = [daily[day].get("退款/其他", 0.0) for day in days]
    net_inflow = [sell + refund - buy for buy, sell, refund in zip(buys, sells, refunds)]
    x = list(range(len(days)))
    width = 0.24
    ax.bar([idx - width for idx in x], buys, width=width, color="#c1121f", alpha=0.76, label="买入")
    ax.bar(x, sells, width=width, color="#16833a", alpha=0.76, label="卖出")
    ax.bar([idx + width for idx in x], refunds, width=width, color="#486581", alpha=0.72, label="退款/其他")
    ax.plot(x, net_inflow, color="#111827", marker="o", linewidth=1.4, label="现金流净流入")
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([datetime.fromisoformat(day).strftime("%m-%d") for day in days], rotation=30, ha="right", fontsize=7.5)
    ax.set_ylabel("金额 CNY")
    ax.set_title("上一周支付宝历史交易流")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.22)


def _pending_by_name() -> dict[str, float]:
    grouped: dict[str, float] = defaultdict(float)
    for row in load_pending_orders():
        name = row.get("name") or row.get("symbol") or "未命名"
        grouped[str(name)] += _float(row.get("order_amount"))
    return dict(grouped)


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _configure_matplotlib(plt)
    return plt


def _configure_matplotlib(plt) -> None:
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.sans-serif"] = [
        "PingFang SC",
        "Heiti SC",
        "Arial Unicode MS",
        "Noto Sans CJK SC",
        "DejaVu Sans",
    ]


def _empty_chart(ax, title: str) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.5, title, ha="center", va="center", fontsize=12, color="#52606d", transform=ax.transAxes)
    ax.set_title(title)


def _action_bucket(action: str) -> str:
    if "买入" in action or "承接" in action or "低仓位" in action:
        return "建议买入"
    if "卖出" in action or "减仓" in action or "减暴露" in action or "降暴露" in action:
        return "建议卖出"
    if "等待确认" in action:
        return "等待确认"
    return "观望"


def _side_bucket(side: str) -> str:
    if "买" in side:
        return "买入"
    if "卖" in side:
        return "卖出"
    return "退款/其他"


def _day_key(value: object) -> str:
    text = str(value or "")
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    try:
        return datetime.fromisoformat(text[:19]).date().isoformat()
    except ValueError:
        return ""


def _previous_week_dates(as_of: str) -> list[str]:
    current = date.fromisoformat(as_of)
    this_monday = current - timedelta(days=current.weekday())
    previous_monday = this_monday - timedelta(days=7)
    return [(previous_monday + timedelta(days=idx)).isoformat() for idx in range(7)]


def _float(value: object) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def _money(value: object) -> str:
    return f"{_float(value):,.2f}"


def _short(value: object, max_len: int) -> str:
    text = str(value)
    return text if len(text) <= max_len else text[: max_len - 1] + "..."
