from __future__ import annotations

from typing import Any


def _pct_float(value: str | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    if text in {"", "N/A", "数据不足", "不适用"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _change_float(value: str | float | int | None) -> float:
    return _pct_float(value)


def _yuan(cents: int) -> float:
    return round(cents / 100, 2)


def _amount_cents_from_yuan(value: Any) -> int:
    try:
        return int(round(float(value) * 100))
    except (TypeError, ValueError):
        return 0


def _main_amounts(category_summary: list[dict[str, Any]]) -> dict[str, int]:
    return {
        item["main_category"]: int(item.get("amount_cents", 0))
        for item in category_summary
        if item.get("level") == "主类"
    }


def _sub_amounts(category_summary: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    return {
        (item["main_category"], item["sub_category"]): int(item.get("amount_cents", 0))
        for item in category_summary
        if item.get("level") == "子类"
    }


def _risk_amounts(risk_summary: list[dict[str, Any]]) -> dict[str, int]:
    return {item["risk_tag"]: int(item.get("amount_cents", 0)) for item in risk_summary}


def _row(
    priority: str,
    focus_area: str,
    trigger_metric: str,
    current_amount_cents: int,
    total_expense_cents: int,
    recommended_action: str,
    suggested_cap_cents: int,
    estimated_saving_cents: int,
    review_needed: str,
) -> dict[str, Any]:
    return {
        "priority": priority,
        "focus_area": focus_area,
        "trigger_metric": trigger_metric,
        "current_amount": _yuan(current_amount_cents),
        "current_amount_cents": current_amount_cents,
        "current_pct": f"{(current_amount_cents / total_expense_cents * 100):.2f}%" if total_expense_cents else "0.00%",
        "recommended_action": recommended_action,
        "suggested_cap": _yuan(suggested_cap_cents),
        "suggested_cap_cents": suggested_cap_cents,
        "estimated_saving": _yuan(max(0, estimated_saving_cents)),
        "estimated_saving_cents": max(0, estimated_saving_cents),
        "review_needed": review_needed,
    }


def build_control_plan(
    metrics: dict[str, Any],
    category_summary: list[dict[str, Any]],
    risk_summary: list[dict[str, Any]],
    trend_rows: list[dict[str, Any]] | None = None,
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    total = int(metrics.get("total_expense", 0))
    main = _main_amounts(category_summary)
    sub = _sub_amounts(category_summary)
    risks = _risk_amounts(risk_summary)
    trend_rows = trend_rows or []
    rows: list[dict[str, Any]] = []

    pending = int(metrics.get("pending_review", 0))
    if pending > 0:
        rows.append(
            _row(
                "P0",
                "大额待复核",
                f"未确认大额支出 ¥{_yuan(pending):,.2f}",
                pending,
                total,
                "先在复核工作台确认用途；未确认前不扩大预算判断。",
                0,
                0,
                "是",
            )
        )

    optimizable = main.get("可优化消费", 0)
    if optimizable > 0:
        cap = round(optimizable * 0.75)
        rows.append(
            _row(
                "P1",
                "可优化消费",
                "主类存在可压缩支出",
                optimizable,
                total,
                "设置下期可优化消费上限为本期 75%；超出后延迟 24 小时再支付。",
                cap,
                optimizable - cap,
                "否",
            )
        )

    for focus, pct_cut in [
        (("可优化消费", "外卖即时零售"), 0.25),
        (("可优化消费", "低复购购物"), 0.35),
        (("可优化消费", "会员订阅"), 0.20),
        (("可优化消费", "便利饮品"), 0.25),
    ]:
        amount = sub.get(focus, 0)
        if amount <= 0:
            continue
        cap = round(amount * (1 - pct_cut))
        rows.append(
            _row(
                "P1",
                "/".join(focus),
                f"子类金额 ¥{_yuan(amount):,.2f}",
                amount,
                total,
                f"下期压缩 {int(pct_cut * 100)}%；保留必要项，其他加入延迟购买清单。",
                cap,
                amount - cap,
                "否",
            )
        )

    social = main.get("社交家庭", 0)
    if total and social / total >= 0.15:
        cap = round(social * 0.85)
        rows.append(
            _row(
                "P1",
                "社交家庭",
                "主类占总支出超过 15%",
                social,
                total,
                "亲情卡/人情往来保留必要预算；大额转账逐笔确认是否可回收或是否家庭共同承担。",
                cap,
                social - cap,
                "是",
            )
        )

    financial = main.get("金融资金", 0)
    if total and financial / total >= 0.25:
        cap = round(financial * 0.80)
        rows.append(
            _row(
                "P1",
                "金融资金",
                "金融资金占总支出超过 25%",
                financial,
                total,
                "固定投资/还款窗口；窗口外只记录理由，不即时买入或周转。",
                cap,
                financial - cap,
                "否",
            )
        )

    credit = risks.get("信用工具", 0) + risks.get("信用周转", 0)
    if total and credit / total >= 0.10:
        rows.append(
            _row(
                "P2",
                "信用工具",
                "信用工具或信用周转占总支出超过 10%",
                credit,
                total,
                "单列花呗/备用金/信用卡还款计划，禁止把授信额度视为可支配现金。",
                credit,
                0,
                "否",
            )
        )

    long_term = risks.get("长期扣费", 0)
    if long_term > 0:
        cap = round(long_term * 0.90)
        rows.append(
            _row(
                "P2",
                "长期扣费",
                "存在会员/保险/通信等长期扣费",
                long_term,
                total,
                "建立固定扣费清单，取消低使用率订阅或重复保障。",
                cap,
                long_term - cap,
                "否",
            )
        )

    for item in trend_rows:
        if item.get("level") != "主类":
            continue
        current = _amount_cents_from_yuan(item.get("current"))
        if current <= 0:
            continue
        mom = _change_float(item.get("mom"))
        yoy = _change_float(item.get("yoy"))
        if mom >= 20 or yoy >= 20:
            cap = round(current * 0.85)
            metric = f"环比 {item.get('mom')}" if mom >= 20 else f"同比 {item.get('yoy')}"
            rows.append(
                _row(
                    "P2",
                    str(item.get("category", "趋势异常")),
                    metric,
                    current,
                    total,
                    "本类支出出现趋势扩张，下期冻结非必要新增并逐笔复核。",
                    cap,
                    current - cap,
                    "否",
                )
            )

    rows.sort(key=lambda item: (item["priority"], -item["estimated_saving_cents"], -item["current_amount_cents"]))
    return rows[:limit]


def control_plan_to_suggestions(control_plan: list[dict[str, Any]]) -> list[str]:
    if not control_plan:
        return ["当前没有单一异常项特别突出。继续积累周期数据后，重点看主类占比和风险标签趋势。"]
    return [
        f"{item['focus_area']}：{item['recommended_action']} 当前金额 ¥{item['current_amount']:,.2f}，预计可优化 ¥{item['estimated_saving']:,.2f}。"
        for item in control_plan[:5]
    ]


def _pressure_row(
    dimension: str,
    source: str,
    current_amount_cents: int,
    total_expense_cents: int,
    target_pct: float,
    control_action: str,
    *,
    target_label: str | None = None,
    review_needed: str = "否",
) -> dict[str, Any]:
    current_pct_value = (current_amount_cents / total_expense_cents * 100) if total_expense_cents else 0.0
    if target_pct <= 0:
        pressure_score = 100.0 if current_amount_cents > 0 else 0.0
    else:
        pressure_score = current_pct_value / target_pct * 100

    if target_pct <= 0 and current_amount_cents > 0:
        status = "阻断"
        priority = "P0"
    elif pressure_score >= 100:
        status = "超压"
        priority = "P1"
    elif pressure_score >= 75:
        status = "临界"
        priority = "P2"
    else:
        status = "正常"
        priority = "P3"

    return {
        "priority": priority,
        "dimension": dimension,
        "source": source,
        "current_amount": _yuan(current_amount_cents),
        "current_amount_cents": current_amount_cents,
        "current_pct": f"{current_pct_value:.2f}%",
        "target_pct": target_label or f"{target_pct:.2f}%",
        "pressure_score": round(pressure_score, 2),
        "status": status,
        "control_action": control_action,
        "review_needed": review_needed,
    }


def build_budget_pressure_radar(
    metrics: dict[str, Any],
    category_summary: list[dict[str, Any]],
    risk_summary: list[dict[str, Any]],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Build a budget pressure view without changing accounting categories."""

    total = int(metrics.get("total_expense", 0))
    main = _main_amounts(category_summary)
    sub = _sub_amounts(category_summary)
    risks = _risk_amounts(risk_summary)
    rows = [
        _pressure_row(
            "大额待复核",
            "manual_review_queue",
            int(metrics.get("pending_review", 0)),
            total,
            0.0,
            "先完成单笔 >= ¥10,000 的用途确认，再更新数据库和报告。",
            target_label="应为 0.00%",
            review_needed="是",
        ),
        _pressure_row(
            "可优化消费",
            "main_category",
            main.get("可优化消费", 0),
            total,
            5.0,
            "下期设置总额上限；超出后延迟 24 小时再支付。",
        ),
        _pressure_row(
            "低复购购物",
            "sub_category",
            sub.get(("可优化消费", "低复购购物"), 0),
            total,
            2.0,
            "非必要购物进入冷静清单，复购价值不明的项目不即时支付。",
        ),
        _pressure_row(
            "外卖即时零售",
            "sub_category",
            sub.get(("可优化消费", "外卖即时零售"), 0),
            total,
            2.0,
            "把外卖和即时零售合并设周上限，平台便利不再单独扩容。",
        ),
        _pressure_row(
            "社交家庭",
            "main_category",
            main.get("社交家庭", 0),
            total,
            12.0,
            "亲情卡/人情往来保留必要预算，大额转账逐笔确认归属。",
            review_needed="是",
        ),
        _pressure_row(
            "金融资金",
            "main_category",
            main.get("金融资金", 0),
            total,
            20.0,
            "投资、保险和信用周转固定窗口处理，窗口外只记录不交易。",
        ),
        _pressure_row(
            "信用工具",
            "risk_tag",
            risks.get("信用工具", 0) + risks.get("信用周转", 0),
            total,
            8.0,
            "授信和现金账户分离，先列还款计划再判断可支配现金。",
        ),
        _pressure_row(
            "长期扣费",
            "risk_tag",
            risks.get("长期扣费", 0),
            total,
            2.0,
            "建立固定扣费清单，取消低使用率订阅或重复保障。",
        ),
    ]
    rows.sort(key=lambda item: (item["priority"], -float(item["pressure_score"]), -int(item["current_amount_cents"])))
    return rows[:limit]
