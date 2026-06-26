from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from statistics import mean

from src.config import ROOT
from src.pfi_os.engine import latest_result_by_symbol
from src.reporting.naming import daily_report_name, kline_report_name, weekly_report_name
from src.reporting.paths import markdown_path
from src.reporting.renderer import format_percent, table
from src.reporting.schedule import SESSION_TIMES


USER_TRADABLE_INDEX_NAMES = {"中证银行", "科创50"}
USER_TRADABLE_INDEX_SYMBOLS = {"399986", "000688", "SZ.399986", "SH.000688"}


def report_meta(as_of: str, session: str) -> str:
    times = SESSION_TIMES[session]
    generated = datetime.now().strftime("%Y-%m-%d %H:%M Australia/Sydney")
    actual_snapshot = _actual_snapshot_time()
    return (
        f"- 报告生成时间：{generated}\n"
        f"- 计划报告时间：{as_of} {times['report']} Australia/Sydney\n"
        f"- 报告场景时间：{as_of} {times['snapshot']} Australia/Sydney\n"
        f"- 实际行情刷新时间：{actual_snapshot}\n"
        f"- 重点观察窗口：{times['order']} Australia/Sydney\n"
        "- 支付宝交易规则：15:00 前提交按当日收盘价确认，15:00 后顺延下一交易日。\n"
        "- 说明：本报告用于研究与纸面交易复盘，不代表真实账户操作。"
    )


def volume_explanation() -> str:
    return (
        "- Volume 含义：本报告中的 Volume 是建议本次买入/卖出的账户仓位比例上限；若有可确认账户总金额，可换算为参考金额。\n"
        "- 支付宝执行口径：15:00 前提交按当日收盘价确认，15:00 后顺延；报告建议必须结合当前持仓金额、持有收益率、待确认订单和尾盘价格。"
    )


def account_overview(account_summary: dict[str, object]) -> str:
    source_status = str(account_summary.get("source_status") or "missing")
    source_label = str(account_summary.get("source_label") or "未导入确认持仓")
    note = str(account_summary.get("notes") or "")
    if source_status == "confirmed_positions":
        weight_note = "现仓优先使用支付宝确认持仓权重；若单项缺权重，则用该项持仓金额/账户持仓总金额估算。"
    elif source_status == "video_candidate":
        weight_note = "当前有支付宝持仓，但明细来自视频/OCR候选数据；现仓按候选持仓金额/视频账户总金额估算，只能辅助判断，不能替代支付宝确认持仓。"
    else:
        weight_note = "当前缺少确认持仓；现仓为空或为 0 的标的不得解读为你实际没有持仓。"
    update_status = str(account_summary.get("alipay_update_status") or "unknown")
    update_note = "当日支付宝流水已记录。"
    execution_block_reason = str(account_summary.get("alipay_execution_block_reason") or "")
    if account_summary.get("alipay_execution_blocked"):
        missing = "、".join(str(item) for item in account_summary.get("alipay_missing_dates", []) if item) or "报告日"
        update_note = f"执行金额闸门阻断：{execution_block_reason or missing}；报告保留研究方向，但所有买卖候选执行金额归零，账户确认后必须重算。"
    return (
        f"- 账户数据状态：{source_label}。\n"
        f"- 现仓口径：{weight_note}\n"
        f"- 支付宝流水更新状态：{update_status}；{update_note}\n"
        f"- 账户口径说明：{note}"
    )


def position_action_recommendations(
    session: str,
    advice: list[dict[str, object]],
    factors: list[dict[str, object]],
    account_summary: dict[str, object],
    events: list[dict[str, str]] | None = None,
    as_of: str | None = None,
) -> str:
    factor_by_name = {str(item.get("name")): item for item in factors}
    pfi_os_by_symbol = latest_result_by_symbol(as_of) if as_of else {}
    total_amount = float(account_summary.get("total_holding_amount") or 0)
    rows = []
    sorted_advice = sorted(advice, key=lambda item: (_action_priority(str(item.get("Position", ""))), -float(item.get("Volume") or 0)))
    for row in sorted_advice:
        if not _include_in_core_action_table(row):
            continue
        factor = factor_by_name.get(str(row.get("Name")), {})
        symbol = str(factor.get("symbol") or row.get("symbol") or "")
        validation = pfi_os_by_symbol.get(symbol, {})
        status = str(validation.get("validation_status") or _pfi_os_status(factor, row, validation))
        composite_quality = _weekly_composite_score(factor, row, events or [], pfi_os_by_symbol)
        volume = float(row.get("Volume") or 0)
        suggested_amount = total_amount * volume if total_amount > 0 and volume > 0 else 0.0
        rows.append(
            {
                "Name": row.get("Name"),
                "Position": row.get("Position"),
                "Volume": volume,
                "composite_quality_pct": composite_quality / 100,
                "persuasion": _persuasion_summary(composite_quality, row, factor, validation),
                "suggested_amount": suggested_amount,
                "holding_amount": row.get("holding_amount", 0),
                "holding_return_pct": row.get("holding_return_pct", 0),
                "current_weight": row.get("current_weight", 0),
                "pending_order_amount": row.get("pending_order_amount", 0),
                "daily_change_pct": factor.get("daily_change_pct", ""),
                "trade_window": SESSION_TIMES[session]["order"] + " Australia/Sydney",
                "basis": _compact_basis(row, factor),
                "volume_basis": _compact_report_text(row.get("volume_basis") or "Volume=0；无可执行仓位幅度。", 120),
                "risk": _compact_core_risk(row),
                "operation_conclusion": _compact_report_text(_decision_operation_conclusion(row, factor, status), 80),
            }
        )
    active_count = sum(1 for row in rows if float(row.get("Volume") or 0) > 0)
    omitted_count = len(sorted_advice) - len(rows)
    omitted_note = f"；{omitted_count} 个纯背景/零持仓观望对象转入信号矩阵或市场结构，不占用核心操作表。" if omitted_count else "。"
    return (
        f"- 当前可执行优先级：卖出风险控制 > 买入承接/补足 > 等待确认 > 持仓观察；复合质量分和说服力已并入本表，本次有明确买卖建议 {active_count} 条{omitted_note}\n"
        + table(
            rows,
            [
                "Name",
                "Position",
                "Volume",
                "composite_quality_pct",
                "persuasion",
                "suggested_amount",
                "holding_amount",
                "holding_return_pct",
                "current_weight",
                "pending_order_amount",
                "daily_change_pct",
                "trade_window",
                "operation_conclusion",
                "volume_basis",
                "basis",
                "risk",
            ],
            [
                "Name",
                "Position",
                "Volume",
                "复合质量分",
                "说服力",
                "建议金额",
                "持仓金额",
                "持有收益率",
                "现仓",
                "待确认金额",
                "当日涨跌",
                "执行窗口",
                "操作结论",
                "Volume依据",
                "依据",
                "风险点",
            ],
        )
    )


def _include_in_core_action_table(row: dict[str, object]) -> bool:
    position = str(row.get("Position") or "")
    if any(token in position for token in ["买入", "卖出", "等待确认", "账户待更新"]):
        return True
    if _is_user_tradable_index(row):
        return True
    return float(row.get("holding_amount") or 0) > 0 or float(row.get("pending_order_amount") or 0) > 0


def _is_user_tradable_index(row: dict[str, object]) -> bool:
    name = str(row.get("Name") or row.get("name") or "")
    symbol = str(row.get("symbol") or "")
    return name in USER_TRADABLE_INDEX_NAMES or symbol in USER_TRADABLE_INDEX_SYMBOLS


def decision_signal_quality_matrix(
    factors: list[dict[str, object]],
    advice: list[dict[str, object]],
    as_of: str | None = None,
) -> str:
    factor_by_name = {str(item.get("name")): item for item in factors}
    pfi_os_by_symbol = latest_result_by_symbol(as_of) if as_of else {}
    rows = []
    for row in sorted(advice, key=lambda item: (_action_priority(str(item.get("Position", ""))), -float(item.get("Volume") or 0))):
        factor = factor_by_name.get(str(row.get("Name")), {})
        symbol = str(factor.get("symbol") or row.get("symbol") or "")
        validation = pfi_os_by_symbol.get(symbol, {})
        status = validation.get("validation_status") or _pfi_os_status(factor, row, validation)
        rows.append(
            {
                "Name": row.get("Name", ""),
                "Position": row.get("Position", "观察"),
                "quality": _decision_signal_quality(row, factor, str(status)),
                "trend": _trend_range_conclusion(row, factor),
                "momentum": _momentum_conclusion(factor),
                "volume": _volume_confirmation(row, factor),
                "mixed": _mixed_signal_conclusion(row, factor, str(status)),
                "evidence": _decision_evidence_needed(row, factor, str(status), validation),
                "operation": _decision_operation_conclusion(row, factor, str(status)),
            }
        )
    return table(
        rows,
        ["Name", "Position", "quality", "trend", "momentum", "volume", "mixed", "evidence", "operation"],
        ["Name", "Position", "信号质量", "MA/EMA/BOLL趋势区间", "MACD/RSI/KDJ动能", "VOL确认", "混合结论", "还需要的证据", "明确操作结论"],
    )


def core_trading_summary(
    session: str,
    advice: list[dict[str, object]],
    factors: list[dict[str, object]],
    exposure: dict[str, object],
) -> str:
    active = [row for row in advice if float(row.get("Volume") or 0) > 0 and _is_accumulation_observation(str(row.get("Position", "")))]
    trims = [row for row in advice if _is_reduce_observation(str(row.get("Position", "")))]
    pending = [row for row in advice if "等待确认" in str(row.get("Position", "")) or float(row.get("pending_order_amount") or 0) > 0]
    watch = [row for row in advice if str(row.get("Position", "")) == "观察"]
    times = SESSION_TIMES[session]
    table_rows = _core_rows(pending[:6], factors, "待确认") + _core_rows(active, factors, "重点观察") + _core_rows(trims[:5], factors, "风控")
    if not table_rows:
        table_rows = [{"priority": "现金", "Name": "暂无高优先级研究线索", "Position": "观察", "Volume": 0, "reason": "没有满足升级条件的标的", "risk": "保留观察，等待下一次确认"}]
    return (
        f"- 支付宝观察窗口：{times['order']} Australia/Sydney；15:00 前后仅用于判断净值确认时点，不构成账户操作依据。\n"
        f"- 承接类待验证线索：{len(active)} 个；减暴露类风险线索：{len(trims)} 个；待确认订单相关：{len(pending)} 个；普通观察：{len(watch)} 个；现金权重：{format_percent(float(exposure.get('cash_weight', 0)))}\n"
        "- 研究原则：先做事实整理和风险识别，再进入 PFIOS 验证；验证不足时只输出观察或待验证。\n"
        + strategy_sizing_basis()
    )


def strategy_sizing_basis() -> str:
    return (
        "- 承接类Volume依据：基础0.800% + 跌幅项 + 亏损项 + 低仓项 - 放量扣减；目标/风险上限为2.000%-6.000%，现仓过高时上限降至2.000%。\n"
        "- 减暴露类Volume依据：基础1.000% + 涨幅项 + 收益项 + 集中度项 - 突破扣减；最终不超过当前现仓和单次8.000%上限。\n"
        "- 每条核心建议必须展示Volume依据；同样是买入或卖出，不同持仓、收益率、量能和现仓会得到不同Volume。\n"
        "- 待确认订单规则：同向订单仍未确认时，不升级研究状态，先等待支付宝确认份额、净值和手续费。"
    )


def alipay_execution_dashboard(factors: list[dict[str, object]], advice: list[dict[str, object]]) -> str:
    factor_by_name = {str(item["name"]): item for item in factors}
    rows = []
    for row in sorted(advice, key=lambda item: _action_priority(str(item.get("Position", "")))):
        factor = factor_by_name.get(str(row["Name"]), {})
        rows.append(
            {
                "Name": row["Name"],
                "Position": row["Position"],
                "Volume": row.get("Volume", 0),
                "holding_amount": row.get("holding_amount", 0),
                "holding_return_amount": row.get("holding_return_amount", 0),
                "current_weight": row.get("current_weight", 0),
                "holding_return_pct": row.get("holding_return_pct", 0),
                "pending_order_amount": row.get("pending_order_amount", 0),
                "pending_order_side": row.get("pending_order_side", ""),
                "daily_change_pct": factor.get("daily_change_pct", ""),
                "turnover": factor.get("turnover", ""),
                "current_weight_basis": row.get("current_weight_basis", ""),
                "trade_deadline": row.get("trade_deadline", ""),
                "decision_basis": _compact_basis(row, factor),
            }
        )
    return table(
        rows,
        ["Name", "Position", "Volume", "holding_amount", "holding_return_amount", "current_weight", "holding_return_pct", "pending_order_amount", "pending_order_side", "daily_change_pct", "turnover", "current_weight_basis", "decision_basis"],
        ["Name", "Position", "Volume", "持仓金额", "持有收益金额", "现仓", "持有收益", "待确认金额", "待确认方向", "当日涨跌", "成交额", "现仓口径", "决策依据"],
    )


def daily_session_analysis(session: str, factors: list[dict[str, object]], advice: list[dict[str, object]]) -> str:
    leaders = _leaders(factors)
    active = [row for row in advice if float(row.get("Volume") or 0) > 0]
    active_text = "、".join(row["Name"] for row in active) if active else "暂无高优先级研究线索"
    leader_text = "、".join(item["name"] for item in leaders) if leaders else "暂无明确强势标的"
    if session == "pre_open":
        return (
            f"- 分析时间：08:45 Australia/Sydney。\n"
            f"- 盘前判断：当前强势线索集中在 {leader_text}。\n"
            f"- 观察结论：盘前只做事实整理，不把隔夜信息写成操作依据；14:30-14:55 只观察收盘价方向是否支持 {active_text}。\n"
            "- 纪律提醒：禁止因为单日上涨追高或因为单日下跌情绪化承接。"
        )
    if session == "midday":
        return (
            f"- 分析时间：12:05 Australia/Sydney。\n"
            f"- 盘中判断：上午强弱排序显示 {leader_text}，下午应降低对弱势或缺行情标的的主动判断权重。\n"
            f"- 观察结论：午间不追盘中高点；14:30-14:55 只验证下午是否延续 {active_text} 的证据链。\n"
            "- 纪律提醒：涨幅扩大要检查拥挤度，跌幅扩大要检查负面事件和成交额确认。"
        )
    return (
        f"- 分析时间：16:05 Australia/Sydney。\n"
        f"- 盘后判断：全天强势线索集中在 {leader_text}，需检查是否只是单日情绪脉冲。\n"
        f"- 观察结论：盘后不生成当日动作；将 {active_text} 放入次日收盘价观察池。\n"
        "- 纪律提醒：次日仍需先确认事实、反方观点和 PFIOS 状态。"
    )


def daily_operation_rule_checklist(
    session: str,
    factors: list[dict[str, object]],
    advice: list[dict[str, object]],
    account_summary: dict[str, object],
    as_of: str | None = None,
) -> str:
    factor_by_name = {str(item.get("name")): item for item in factors}
    pfi_os_by_symbol = latest_result_by_symbol(as_of) if as_of else {}
    account_blocked = bool(account_summary.get("alipay_execution_blocked"))
    account_reason = str(account_summary.get("alipay_execution_block_reason") or "账户数据未确认")
    rows = []
    for row in sorted(advice, key=lambda item: (_action_priority(str(item.get("Position", ""))), -float(item.get("Volume") or 0)))[:12]:
        factor = factor_by_name.get(str(row.get("Name")), {})
        symbol = str(factor.get("symbol") or row.get("symbol") or "")
        validation = pfi_os_by_symbol.get(symbol, {})
        status = str(validation.get("validation_status") or _pfi_os_status(factor, row, validation))
        rows.append(
            {
                "Name": row.get("Name", ""),
                "Position": row.get("Position", "观察"),
                "window": SESSION_TIMES[session]["order"] + " Australia/Sydney",
                "account_gate": _account_gate_text(account_blocked, account_reason, row),
                "quality": _decision_signal_quality(row, factor, status),
                "pass_condition": _daily_pass_condition(row, factor, status),
                "fail_action": _daily_fail_action(row, factor),
                "evidence_gap": _decision_evidence_needed(row, factor, status, validation),
                "pfi_os_gate": validation.get("risk_gate") or _pfi_os_operation_behavior(row, factor, validation),
                "final_rule": _decision_operation_conclusion(row, factor, status),
            }
        )
    if not rows:
        rows = [
            {
                "Name": "暂无",
                "Position": "观察",
                "window": SESSION_TIMES[session]["order"] + " Australia/Sydney",
                "account_gate": "账户闸门：无买卖候选。",
                "quality": "Low",
                "pass_condition": "没有满足升级条件的对象。",
                "fail_action": "维持观望，不占用资金。",
                "evidence_gap": "继续刷新行情、账户、事件和PFIOS结果。",
                "pfi_os_gate": "无可验证线索",
                "final_rule": "明确结论：观望。",
            }
        ]
    return (
        "- 本表用于 14:30-14:55 Australia/Sydney 收盘前检查；不再单独列行情排行，所有价格/成交额只作为成立条件的一部分。\n"
        "- 若账户闸门阻断，所有买卖候选只能保留研究方向，Volume 和建议金额必须为 0，更新支付宝流水/持仓后重新生成报告。\n"
        + table(
            rows,
            ["Name", "Position", "window", "account_gate", "quality", "pass_condition", "fail_action", "evidence_gap", "pfi_os_gate", "final_rule"],
            ["Name", "Position", "检查时间", "账户闸门", "信号质量", "成立条件", "不成立动作", "证据缺口", "PFIOS闸门", "最终规则"],
        )
    )


def fact_inference_opinion(
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    advice: list[dict[str, object]],
    account_summary: dict[str, object],
) -> str:
    leaders = _leaders(factors)
    weak = _weak(factors)
    pending_amount = float(account_summary.get("pending_order_amount") or 0)
    event_text = _event_text(events)
    observation_names = "、".join(str(row["Name"]) for row in advice if str(row.get("Position")) != "观察") or "暂无"
    alipay_update = str(account_summary.get("alipay_update_status") or "unknown")
    execution_state = "阻断执行金额" if account_summary.get("alipay_execution_blocked") else "可用于执行金额计算"
    return (
        "### 事实\n"
        f"- 自选池强势靠前：{_names(leaders)}；弱势或转弱：{_names(weak)}。\n"
        f"- 账户待确认订单金额：{pending_amount:,.2f} 元；账户数据状态：{account_summary.get('source_label', '未标注')}；支付宝流水更新状态：{alipay_update}；执行金额确认状态：{execution_state}。\n"
        f"- 已记录事件：{event_text or '暂无新增事件'}。\n\n"
        "### 推论\n"
        "- 强弱排序只能说明当前资金和价格行为，不等于主题长期有效。\n"
        "- 若成交额没有同步放大，单日上涨/下跌更可能是噪音或流动性扰动。\n"
        "- 待确认订单会扭曲现仓判断，相关对象不得重复升级观察状态。\n\n"
        "### 观点\n"
        f"- 当前进入重点观察或风险观察的对象：{observation_names}。\n"
        "- 买卖建议只在行情、账户、事件与 PFIOS 证据可串联时保留；当日支付宝流水缺失或仅为待确认候选数据时只能保留买/卖研究候选，执行金额必须为0。\n"
        "- 若事实、推论、观点之间无法形成闭环，研究状态应降级并进入下一轮验证。"
    )


def research_confidence_table(
    factors: list[dict[str, object]],
    advice: list[dict[str, object]],
    events: list[dict[str, str]],
    as_of: str | None = None,
) -> str:
    event_blob = " ".join(str(item.get("related_symbols", "")) + " " + str(item.get("title", "")) for item in events)
    advice_by_name = {str(row.get("Name")): row for row in advice}
    pfi_os_by_symbol = latest_result_by_symbol(as_of) if as_of else {}
    rows = []
    for item in sorted(factors, key=lambda row: float(row.get("daily_change_pct") or -999), reverse=True)[:12]:
        name = str(item.get("name", ""))
        advice_row = advice_by_name.get(name, {})
        symbol = str(item.get("symbol") or advice_row.get("symbol") or "")
        validation = pfi_os_by_symbol.get(symbol, {})
        score, level, gaps = _research_confidence(item, advice_row, event_blob, validation)
        rows.append(
            {
                "name": name,
                "research_group": item.get("research_group") or item.get("industry", ""),
                "score": score / 100,
                "level": level,
                "data_status": "完整" if item.get("close") not in {"", None} and item.get("turnover") not in {"", None} else "缺行情/成交额",
                "validation_status": _pfi_os_status_display(_pfi_os_status(item, advice_row, validation)),
                "validation_plan": gaps,
            }
        )
    return table(
        rows,
        ["name", "research_group", "score", "level", "data_status", "validation_status", "validation_plan"],
        ["Name", "主题", "Research Confidence Score", "研究等级", "数据完整性", "PFIOS状态", "已处理/待跟踪事项"],
    )


def counter_thesis(advice: list[dict[str, object]], factors: list[dict[str, object]]) -> str:
    factor_by_name = {str(item.get("name")): item for item in factors}
    rows = []
    for row in advice[:10]:
        name = str(row.get("Name"))
        factor = factor_by_name.get(name, {})
        action = str(row.get("Position", ""))
        rows.append(
            {
                "Name": name,
                "counter": _counter_reason(row, factor),
                "wait_sample": _counter_wait_sample(row, factor),
                "expected": _counter_expected_result(row, factor),
                "invalidate": _risk_trigger(factor, action),
                "conclusion": _counter_clear_conclusion(row, factor),
                "operation": _counter_operation(row, factor),
            }
        )
    return table(
        rows,
        ["Name", "counter", "wait_sample", "expected", "invalidate", "conclusion", "operation"],
        ["Name", "反方观点", "等待样本", "期望结果", "推翻条件", "明确结论", "触发后操作"],
    )


def discipline_check(account_summary: dict[str, object], advice: list[dict[str, object]], exposure: dict[str, object] | None = None) -> str:
    pending_amount = float(account_summary.get("pending_order_amount") or 0)
    pending_count = int(float(account_summary.get("pending_order_count") or 0))
    active_count = sum(1 for row in advice if float(row.get("Volume") or 0) > 0)
    cash_weight = float((exposure or {}).get("cash_weight", 0))
    missing_dates = "、".join(str(item) for item in account_summary.get("alipay_missing_dates", []) if item) or "无"
    execution_reason = str(account_summary.get("alipay_execution_block_reason") or "")
    rows = [
        {
            "item": "支付宝执行金额确认",
            "status": "阻断执行" if account_summary.get("alipay_execution_blocked") else "正常",
            "detail": f"缺失日期：{missing_dates}；原因：{execution_reason or '已达到执行计算口径'}；阻断时买卖候选Volume必须为0，确认后重新生成报告",
        },
        {"item": "待确认订单", "status": "需等待" if pending_count else "正常", "detail": f"{pending_count} 笔 / {pending_amount:,.2f} 元"},
        {"item": "重复升级观察", "status": "需检查" if pending_count and active_count else "正常", "detail": "待确认订单存在时，不升级同向研究状态"},
        {"item": "现金缓冲", "status": "偏低" if cash_weight < 0.2 else "正常", "detail": format_percent(cash_weight)},
        {"item": "情绪化追涨/补跌", "status": "需检查", "detail": "任何单日涨跌触发的线索必须经过反方观点和 PFIOS 验证"},
        {"item": "现实现金流影响", "status": "需人工确认", "detail": "报告系统无法判断生活现金流，必须由用户确认"},
    ]
    return table(rows, ["item", "status", "detail"], ["纪律项", "状态", "说明"])


def pfi_os_validation_queue(factors: list[dict[str, object]], advice: list[dict[str, object]], as_of: str | None = None) -> str:
    factor_by_name = {str(item.get("name")): item for item in factors}
    pfi_os_by_symbol = latest_result_by_symbol(as_of) if as_of else {}
    rows = []
    for row in advice:
        if str(row.get("Position")) == "观察" and float(row.get("Volume") or 0) <= 0:
            continue
        factor = factor_by_name.get(str(row.get("Name")), {})
        symbol = str(factor.get("symbol") or row.get("symbol") or "")
        validation = pfi_os_by_symbol.get(symbol, {})
        rows.append(
            {
                "Name": row.get("Name"),
                "status": _pfi_os_status_display(str(validation.get("validation_status") or _pfi_os_status(factor, row))),
                "target": symbol,
                "sample": _pfi_os_sample_text(validation),
                "cost": validation.get("cost_assumption") or "申赎费/管理费/滑点/15:00收盘确认",
                "monte_carlo": _pfi_os_monte_carlo_text(validation),
                "rerun": _pfi_os_rerun_text(validation),
                "risk_gate": _risk_gate_display(str(validation.get("risk_gate") or "")),
                "needed": _decision_evidence_needed(row, factor, str(validation.get("validation_status") or _pfi_os_status(factor, row)), validation),
                "operation": _pfi_os_operation_behavior(row, factor, validation),
                "conclusion": _pfi_os_conclusion_display(validation),
            }
        )
    if not rows:
        rows = [{"Name": "暂无", "status": "排队验证", "target": "", "sample": "", "cost": "", "monte_carlo": ">=100,000次", "rerun": "全流程>=2次", "risk_gate": "无可验证线索", "needed": "等待下一次行情和账户更新", "operation": "维持观望", "conclusion": "暂无可验证线索；等待下一次行情和账户更新。"}]
    return table(
        rows,
        ["Name", "status", "target", "sample", "cost", "monte_carlo", "rerun", "risk_gate", "needed", "operation", "conclusion"],
        ["Name", "验证状态", "回测对象", "样本区间", "成本假设", "模拟次数", "重跑要求", "风险闸门", "还需要的证据", "验证队列操作行为", "验证结论"],
    )


def risk_explanation() -> str:
    return (
        "- 主题暴露含义：当前研究权重上限按研究分组汇总后的占比，用来检查是否过度集中在同一主题。\n"
        "- 现金缓冲含义：未被研究权重占用的观察空间；现金越高，说明系统越保守，留给后续确认或风险事件的缓冲越大。\n"
    )


def comparison_backtest(session: str, factors: list[dict[str, object]], advice: list[dict[str, object]], as_of: str | None = None) -> str:
    active = [row for row in advice if float(row.get("Volume") or 0) > 0]
    weighted_return = _directional_weighted_return(active, factors)
    current_counts = _action_counts(advice)
    if session == "pre_open":
        return (
            "- 开盘前报告为当天计划基准，尚无盘中/盘后复盘结果。\n"
            f"- 计划结构：{_counts_text(current_counts)}；后续盘中与盘后用同一口径复盘买卖方向收益。\n"
            "- 优化重点：若开盘后强弱排序与成交额不匹配，盘中报告必须降低相应建议力度。"
        )
    if session == "midday":
        pre_open = _daily_report_digest(as_of, "pre_open") if as_of else "未读取盘前报告。"
        return (
            f"- 与盘前报告对比：{pre_open}\n"
            f"- 盘中当前结构：{_counts_text(current_counts)}；若按当前买卖方向和建议 Volume 纸面跟踪，盘中方向收益率约 {format_percent(weighted_return)}。\n"
            "- 复盘结论：方向收益为正且成交额同步时，下午保留；方向收益为负或成交额背离时，下午降低 Volume 或转为等待确认。\n"
            "- 优化动作：缺行情/权限不足标的只保留观望；买入只保留跌幅、现仓、收益率、事件风险同时支持的对象。"
        )
    pre_open = _daily_report_digest(as_of, "pre_open") if as_of else "未读取盘前报告。"
    midday = _daily_report_digest(as_of, "midday") if as_of else "未读取盘中报告。"
    return (
        f"- 与盘前报告对比：{pre_open}\n"
        f"- 与盘中报告对比：{midday}\n"
        f"- 盘后当前结构：{_counts_text(current_counts)}；若按当前买卖方向和建议 Volume 纸面跟踪，盘后方向收益率约 {format_percent(weighted_return)}。\n"
        "- 复盘结论：收益来自单一主题时，次日降低主题集中；收益来自多主题且 PFIOS 风险闸门未否定时，保留为次日优先观察。\n"
        "- 规则优化：后续只用可验证价格、涨跌幅、成交额、持仓收益率和待确认订单共同决定买卖幅度。"
    )


def multi_dimensional_analysis(factors: list[dict[str, object]], events: list[dict[str, str]]) -> str:
    leaders = _leaders(factors)
    weak = _weak(factors)
    event_text = _event_text(events)
    return (
        f"- 新闻/公告：{event_text or '暂无新增事件'}。\n"
        f"- 技术面：强势排序靠前为 {_names(leaders)}；下跌或需回避观察为 {_names(weak)}。\n"
        "- 基本面：ETF 侧重行业景气和政策方向，个股侧重盈利质量与事件催化；当前自选池更偏科技成长与美股 ETF。\n"
        "- 价值面：若涨幅来自估值扩张而非盈利/景气改善，应降低研究权重；若成交额同步放大且主题有新闻支撑，可保留观察。\n"
        "- 观察结论：只对价格、涨跌幅、成交额均可验证的标的升级研究状态；数据缺失标的仅保留在观察池。"
    )


def section_explanation_daily() -> str:
    return (
        "- 仓位操作建议：汇总可执行方向、Volume、持仓金额、持有收益率、执行窗口和失效条件。\n"
        "- 研究质量检查图：用主题热度、研究质量、持仓风险和复盘有效性检查研究线索是否值得升级。\n"
        "- 催化剂与风险事件：按时间、主题、影响方向、确定性、可验证数据和后续指标拆解事件，不把新闻标题直接等同于结论。\n"
        "- 核心观察清单：Name 是标的名称，观察状态是研究结论等级，研究权重上限用于后续验证，不是最终操作依据。\n"
        "- 研究证据与观察优先级：按强弱排序、数据来源、研究价值和风险触发判断是否值得进入验证队列。\n"
        "- 热力图与气泡图：快速查看 A股自选板块强弱、成交额和异常波动。\n"
        "- 场景分析与观察结论：给出当前时点该怎么判断、几点重点观察。\n"
        "- 复盘与模拟收益：用当前快照估算如果按早盘/盘中候选权重纸面跟踪的收益。\n"
        "- 账户与组合风险控制：检查主题集中、现金缓冲和数据异常。\n"
        "- 末尾账户附图：集中放置持仓、收益、待确认订单和上一周支付宝现金流，避免正文重复。"
    )


def weekly_multi_dimensional_analysis(factors: list[dict[str, object]], events: list[dict[str, str]]) -> str:
    return (
        f"- 技术面：本周优先关注 {_names(_leaders(factors))} 是否延续强势。\n"
        f"- 事件面：重点事件为 {_event_text(events)}。\n"
        "- 基本面：科技、半导体、美股 ETF 偏成长弹性；红利、银行、黄金偏防御或对冲。\n"
        "- 价值面：成长方向若快速上涨，需要用成交额和后续业绩/政策验证，避免只因短线涨幅追高。\n"
        "- 周度观察结论：周一建立主题雷达和验证队列；周五以复盘命中率和主题延续性决定下周研究优先级。"
    )


def weekly_operation_synthesis(
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    advice: list[dict[str, object]],
    as_of: str,
) -> str:
    leaders = _leaders(factors)
    weak = _weak(factors)
    counts = _action_counts(advice)
    verified_events = [event for event in events if _event_has_original_source(event)]
    pfi_os_by_symbol = latest_result_by_symbol(as_of)
    pass_count = sum(1 for row in pfi_os_by_symbol.values() if str(row.get("risk_gate") or "") == "Pass")
    blocked_count = sum(1 for row in pfi_os_by_symbol.values() if str(row.get("risk_gate") or "") == "Blocked")
    return (
        f"- 综合结论：本周只把 {_names(leaders)} 作为强势观察线索，把 {_names(weak)} 作为风险/承接校验线索；单独收盘价、涨跌幅、成交额不构成周报结论。\n"
        f"- 操作结构：{_counts_text(counts)}；买入必须满足尾盘止跌、成交额不恶化、事件原文无负面扩散和 PFIOS 未阻断，卖出优先处理上涨兑现、转弱降仓和现仓集中风险。\n"
        f"- 事件核验：已完成原文核验事件 {len(verified_events)} 条；未核验政策/新闻只作为风险背景，不增加买入分、买入金额或 Volume。\n"
        f"- PFIOS闸门：通过 {pass_count} 个，阻断 {blocked_count} 个；被阻断的买入自动取消或观望，卖出/风控优先。\n"
        "- 高概率盈利口径：只有复合质量分、策略胜率代理、事件核验、持仓纪律和失败动作同时成立时才进入高概率候选；否则降级为中概率、低概率或观望。"
    )


def weekly_composite_strategy_table(
    factors: list[dict[str, object]],
    advice: list[dict[str, object]],
    events: list[dict[str, str]],
    as_of: str,
) -> str:
    advice_by_name = {str(row.get("Name")): row for row in advice}
    pfi_os_by_symbol = latest_result_by_symbol(as_of)
    rows = []
    ranked = sorted(
        factors,
        key=lambda item: _weekly_composite_score(item, advice_by_name.get(str(item.get("name")), {}), events, pfi_os_by_symbol),
        reverse=True,
    )
    for item in ranked[:16]:
        name = str(item.get("name") or "")
        row = advice_by_name.get(name, {"Name": name, "Position": "观望", "Volume": 0})
        symbol = str(item.get("symbol") or row.get("symbol") or "")
        validation = pfi_os_by_symbol.get(symbol, {})
        score = _weekly_composite_score(item, row, events, pfi_os_by_symbol)
        win_rate = _strategy_win_rate(validation, item, row)
        rows.append(
            {
                "Name": name,
                "Position": _weekly_position_with_quality(row, score, win_rate, validation),
                "theme": item.get("research_group") or item.get("industry", ""),
                "composite_quality_pct": score / 100,
                "strategy_win_rate_pct": win_rate,
                "probability_grade": _probability_grade(score, win_rate, validation),
                "accuracy_basis": _accuracy_basis(score, win_rate, validation),
                "profit_condition": _high_probability_profit_condition(row, item, score, win_rate, validation),
                "risk_gate": _weekly_risk_gate_label(validation),
                "max_drawdown_pct": _validation_float(validation, "max_drawdown"),
                "walk_forward_return_pct": _validation_float(validation, "walk_forward_return"),
                "price_volume_evidence": _price_volume_evidence(item),
                "event_source_verification": _event_original_verification_for_item(item, events),
                "policy_support": _policy_support_for_item(item, events),
                "operation_strategy": _weekly_operation_strategy(row, item, score, win_rate, validation),
                "failure_action": _weekly_failure_action(row, item, validation),
            }
        )
    return (
        "- 本表不把收盘价、涨跌幅、成交额单独作为结论；它们只进入“量价证据”。排序依据为复合质量分、策略胜率代理、PFIOS 风险闸门、政策/事件支持、持仓逻辑和反方触发条件。\n"
        "- 策略胜率代理 = 1 - PFIOS 蒙特卡洛亏损概率；若样本不足，则用数据完整性、量价一致性和持仓约束给出低权重代理，不能视为历史真实胜率，也不能保证盈利。\n"
        "- 高概率盈利条件必须同时满足量价、持仓纪律、事件原文核验和 PFIOS 风险闸门；任一关键条件缺失，操作策略自动降额、取消或观望。\n"
        + table(
            rows,
            [
                "Name",
                "Position",
                "theme",
                "composite_quality_pct",
                "strategy_win_rate_pct",
                "probability_grade",
                "accuracy_basis",
                "profit_condition",
                "risk_gate",
                "max_drawdown_pct",
                "walk_forward_return_pct",
                "price_volume_evidence",
                "event_source_verification",
                "policy_support",
                "operation_strategy",
                "failure_action",
            ],
            [
                "Name",
                "Position",
                "主题",
                "复合质量分",
                "策略胜率代理",
                "概率等级",
                "准确性依据",
                "高概率盈利条件",
                "风险闸门",
                "最大回撤",
                "Walk-forward",
                "量价证据",
                "事件原文核验",
                "政策/事件支持",
                "操作策略",
                "失败动作",
            ],
        )
    )


def theme_tracking_table(factors: list[dict[str, object]], events: list[dict[str, str]]) -> str:
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in factors:
        theme = str(item.get("research_group") or item.get("industry") or "未分类")
        grouped.setdefault(theme, []).append(item)
    rows = []
    for theme, items in sorted(grouped.items()):
        changes = [float(item.get("daily_change_pct") or 0) for item in items if item.get("daily_change_pct") not in {"", None}]
        turnover = sum(float(item.get("turnover") or 0) for item in items)
        related = [event for event in events if theme in str(event.get("industry", "")) or theme in str(event.get("title", ""))]
        avg_change = sum(changes) / len(changes) if changes else 0.0
        rows.append(
            {
                "theme": theme,
                "today": avg_change,
                "turnover": turnover,
                "catalyst": related[0].get("title", "暂无明确催化") if related else "暂无明确催化",
                "risk": _theme_risk(theme, avg_change, turnover),
                "symbols": "、".join(str(item.get("name")) for item in items[:4]),
                "validation": "排队验证-未完成" if abs(avg_change) > 0.015 or related else "仅观察",
                "status": "验证通过-可继续研究" if abs(avg_change) > 0.01 else "仅观察",
            }
        )
    return table(
        rows,
        ["theme", "today", "turnover", "catalyst", "risk", "symbols", "validation", "status"],
        ["主题", "今日强弱", "成交额", "主要催化剂", "主要风险", "相关标的", "PFIOS", "研究状态"],
    )


def catalyst_risk_event_table(events: list[dict[str, str]], factors: list[dict[str, object]], as_of: str) -> str:
    factor_theme_by_symbol = {}
    for item in factors:
        theme = str(item.get("research_group") or item.get("industry") or "未分类")
        factor_theme_by_symbol[str(item.get("symbol", ""))] = theme
        factor_theme_by_symbol[str(item.get("quote_code", ""))] = theme
    rows = []
    for event in events:
        if event.get("date", "") > as_of:
            continue
        full_time = _full_event_time(event)
        related = str(event.get("related_symbols", ""))
        theme = str(event.get("industry") or _theme_from_related(related, factor_theme_by_symbol) or "待分类")
        rows.append(
            {
                "time": full_time,
                "type": event.get("type", ""),
                "theme": theme,
                "title": event.get("title", ""),
                "impact": _impact_label(event.get("impact", "")),
                "certainty": _event_certainty(event),
                "verifiable": _verifiable_data(event, related),
                "source_review": _event_source_review(event),
                "source_chain": _event_source_chain(event),
                "follow_up": _follow_up_indicator(event),
                "operation": _event_operation_impact(event),
            }
        )
    if not rows:
        rows = [
            {
                "time": "",
                "type": "暂无",
                "theme": "",
                "title": "暂无新增催化剂或风险事件",
                "impact": "",
                "certainty": "Insufficient Evidence",
                "verifiable": "暂无官方源、新闻源或行情源交叉数据",
                "source_review": "未形成原文核验链路；不作为新增买入依据",
                "source_chain": "无新增事件链路",
                "follow_up": "下一轮自动抓取新闻、公告、政策和行情后再判断",
                "operation": "不扩大买入；既有风控逻辑保留",
            }
        ]
    return table(
        sorted(rows, key=lambda row: _event_time_sort_key(row.get("time"))),
        ["time", "type", "theme", "title", "impact", "certainty", "verifiable", "source_review", "source_chain", "follow_up", "operation"],
        ["时间（含年月日/来源当地时区）", "类型", "相关主题", "事件/催化剂", "影响方向", "确定性", "可验证数据", "原文核验", "来源链路", "后续指标", "操作影响"],
    )


def weekly_review(session: str, factors: list[dict[str, object]], advice: list[dict[str, object]], as_of: str | None = None) -> str:
    ret = _directional_weighted_return([row for row in advice if float(row.get("Volume") or 0) > 0], factors)
    current_counts = _action_counts(advice)
    if session == "monday_pre_open":
        return (
            "- 周一报告为本周计划基准，后续用周五报告验证。\n"
            f"- 本周初始结构：{_counts_text(current_counts)}。\n"
            "- 本周评估指标：买卖方向收益率、强势主题延续天数、失效信号数量、待确认订单影响。"
        )
    week_digest = _weekly_generated_report_digest(as_of) if as_of else "未读取本周报告。"
    return (
        f"- 本周报告对比：{week_digest}\n"
        f"- 周五当前结构：{_counts_text(current_counts)}；按当前买卖方向和建议 Volume 纸面跟踪，周五方向收益率约 {format_percent(ret)}。\n"
        "- 逻辑总结：买入建议必须来自下跌承接/低仓位补足且风险事件未恶化；卖出建议必须来自上涨兑现/转弱降仓且现仓收益率支持。\n"
        "- 优化结论：保留成交额可验证且强势延续的方向；剔除无行情权限、事件证据薄弱或仅有单日脉冲的方向。"
    )


def section_explanation_weekly() -> str:
    return (
        "- 周度核心观点：总结本周或下周最重要的研究判断。\n"
        "- 仓位纪律与账户附图：用待确认订单、研究观察状态和历史交易流检查本周操作是否过度集中或过度频繁。\n"
        "- 研究质量检查图：汇总主题热度、研究质量、持仓风险和周度复盘有效性。\n"
        "- 复合判断质量表：把量价证据、PFIOS、政策事件、持仓约束和失败动作合成操作策略，不把裸行情当结论。\n"
        "- 主题、新闻、公告与行业跟踪：解释哪些事件正在影响标的。\n"
        "- 多维研究分析：从技术面、事件面、基本面、价值面综合判断。\n"
        "- 下周核心观察清单：给出 Name、观察状态、研究权重上限和验证缺口。\n"
        "- 周度复盘与优化结论：验证研究判断是否有效，并更新下一轮规则。"
    )


def event_table_rows(events: list[dict[str, str]], as_of: str) -> list[dict[str, str]]:
    labels = {"positive": "正面", "negative": "负面", "neutral": "中性"}
    rows = []
    for event in events:
        if event["date"] <= as_of:
            rows.append(
                {
                    "event_time": _full_event_time(event),
                    "type": event["type"],
                    "title": event["title"],
                    "impact": labels.get(event.get("impact", ""), event.get("impact", "")),
                    "source_name": event["source_name"],
                }
            )
    return sorted(rows, key=lambda row: _event_time_sort_key(row.get("event_time")))


def _full_event_time(event: dict[str, str]) -> str:
    event_date = str(event.get("date") or "")
    event_time = _event_time_with_timezone(str(event.get("event_time") or ""), event)
    if event_date and event_time:
        return f"{event_date} {event_time}"
    return event_date or event_time


def _event_time_with_timezone(event_time: str, event: dict[str, str]) -> str:
    if not event_time or _has_timezone_marker(event_time):
        return event_time
    source = str(event.get("source_name") or "")
    industry = str(event.get("industry") or "")
    url = str(event.get("source_url") or "")
    if any(token in source for token in ["Nasdaq", "Kiplinger", "Clearank"]) or "美股" in industry:
        return f"{event_time} America/New_York"
    if "Moomoo" in source or url.startswith("opend://") or "A股" in industry or "港股" in industry:
        return f"{event_time} Asia/Shanghai"
    return f"{event_time} Australia/Sydney"


def _has_timezone_marker(value: str) -> bool:
    return bool(
        re.search(r"\b(?:Asia|Australia|America|Europe|UTC|GMT)/?[A-Za-z_]*\b", value)
        or re.search(r"(?:Z|[+-]\d{2}:?\d{2})\b", value)
    )


def _event_sort_key(event: dict[str, str]) -> tuple[str, int, int, str]:
    return _event_time_sort_key(_full_event_time(event))


def _event_time_sort_key(value: object) -> tuple[str, int, int, str]:
    text = str(value or "")
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    time_match = re.search(r"(?:^|\s)(\d{1,2}):(\d{2})", text)
    date_key = date_match.group(0) if date_match else "9999-99-99"
    hour = int(time_match.group(1)) if time_match else 99
    minute = int(time_match.group(2)) if time_match else 99
    return (date_key, hour, minute, text)


def _weekly_composite_score(
    item: dict[str, object],
    row: dict[str, object],
    events: list[dict[str, str]],
    pfi_os_by_symbol: dict[str, dict[str, str]],
) -> float:
    symbol = str(item.get("symbol") or row.get("symbol") or "")
    validation = pfi_os_by_symbol.get(symbol, {})
    data_score = 0
    if item.get("close") not in {"", None} and item.get("daily_change_pct") not in {"", None}:
        data_score += 12
    if item.get("turnover") not in {"", None} and float(item.get("turnover") or 0) > 0:
        data_score += 8
    signal_score = min(20, _daily_signal_score(row, item) * 5)
    status = str(validation.get("validation_status") or _pfi_os_status(item, row, validation))
    risk_gate = str(validation.get("risk_gate") or "")
    pfi_os_score = {
        "ContinueResearch": 24,
        "NeedsMoreEvidence": 12,
        "DataQualityReview": 4,
        "ValidationQueued": 10,
        "WatchOnly": 8,
        "DoNotUse": 0,
    }.get(status, 6)
    if risk_gate == "Pass":
        pfi_os_score += 8
    elif risk_gate == "Blocked":
        pfi_os_score -= 5
    win_score = max(0, min(14, (_strategy_win_rate(validation, item, row) - 0.45) / 0.25 * 14))
    policy_score = _policy_support_score(item, events)
    holding_score = 8 if float(row.get("holding_amount") or 0) > 0 else 3
    pending_penalty = 8 if float(row.get("pending_order_amount") or 0) > 0 else 0
    raw = data_score + signal_score + pfi_os_score + win_score + policy_score + holding_score - pending_penalty
    if status == "DataQualityReview":
        raw = min(raw, 42)
    if risk_gate == "Blocked":
        raw = min(raw, 68)
    return round(max(0, min(100, raw)), 3)


def _strategy_win_rate(validation: dict[str, str], item: dict[str, object], row: dict[str, object]) -> float:
    loss_probability = validation.get("monte_carlo_loss_probability")
    try:
        if loss_probability not in {"", None}:
            return round(max(0.0, min(1.0, 1 - float(loss_probability))), 6)
    except (TypeError, ValueError):
        pass
    score = _daily_signal_score(row, item)
    data_ok = item.get("close") not in {"", None} and item.get("turnover") not in {"", None}
    base = 0.48 + min(score, 4) * 0.025
    if not data_ok:
        base -= 0.08
    if float(row.get("pending_order_amount") or 0) > 0:
        base -= 0.04
    return round(max(0.25, min(0.58, base)), 6)


def _weekly_position_with_quality(
    row: dict[str, object],
    score: float,
    win_rate: float,
    validation: dict[str, str],
) -> str:
    action = str(row.get("Position") or "观望")
    if "账户待更新" in action:
        return action
    if str(validation.get("risk_gate") or "") == "Blocked" and _is_buy_action(action):
        return "买入取消-风险闸门"
    if _is_buy_action(action) and score >= 70 and win_rate >= 0.56:
        return "建议买入-高质量"
    if _is_buy_action(action):
        return "建议买入-待重算"
    if _is_sell_action(action) and score >= 55:
        return "建议卖出-高质量"
    if _is_sell_action(action):
        return "建议卖出-待重算"
    return action


def _persuasion_summary(
    score: float,
    row: dict[str, object],
    factor: dict[str, object],
    validation: dict[str, str],
) -> str:
    action = str(row.get("Position") or "观望")
    status = str(validation.get("validation_status") or _pfi_os_status(factor, row, validation))
    risk_gate = str(validation.get("risk_gate") or "")
    evidence = []
    daily_change = factor.get("daily_change_pct")
    if daily_change not in {"", None}:
        evidence.append(f"涨跌{format_percent(float(daily_change or 0))}")
    turnover = float(factor.get("turnover") or 0)
    if turnover > 0:
        evidence.append("成交额>0")
    holding_weight = float(row.get("holding_weight") or 0)
    if holding_weight > 0:
        evidence.append(f"现仓{format_percent(holding_weight)}")
    holding_return = float(row.get("holding_return_pct") or 0)
    if float(row.get("holding_amount") or 0) > 0:
        evidence.append(f"收益{format_percent(holding_return)}")
    pending = float(row.get("pending_order_amount") or 0)
    if pending > 0:
        evidence.append(f"待确认{pending:,.0f}")
    if status == "ContinueResearch":
        evidence.append("PFIOS通过")
    elif status in {"NeedsMoreEvidence", "DataQualityReview", "DoNotUse"}:
        evidence.append(f"PFIOS{_short_pfi_os_status(status)}")
    if risk_gate == "Blocked":
        evidence.append("风险闸门阻断")
    if "账户待更新" in action:
        level = "低"
        if _is_buy_action(action):
            conclusion = "账户未确认，买入归零"
        elif _is_sell_action(action):
            conclusion = "账户未确认，卖出暂停"
        else:
            conclusion = "账户未确认，维持观察"
    elif risk_gate == "Blocked" or status in {"DataQualityReview", "DoNotUse"}:
        level = "低"
        conclusion = "只保留防错观察"
    elif score >= 70:
        level = "高"
        conclusion = "证据链较完整"
    elif score >= 55:
        level = "中"
        conclusion = "可观察但需尾盘确认"
    else:
        level = "低"
        conclusion = "不足以扩大动作"
    evidence_text = "、".join(evidence[:5]) or "证据不足"
    return _compact_report_text(f"{level}：{conclusion}；{evidence_text}", 76)


def _short_pfi_os_status(status: str) -> str:
    if status == "NeedsMoreEvidence":
        return "不足"
    if status == "DataQualityReview":
        return "待审"
    if status == "DoNotUse":
        return "停用"
    return status


def _accuracy_basis(score: float, win_rate: float, validation: dict[str, str]) -> str:
    raw_status = str(validation.get("validation_status") or "")
    status = _pfi_os_status_display(raw_status) if raw_status else "基础代理"
    sample_rows = str(validation.get("sample_rows") or "本地快照")
    if score >= 72 and win_rate >= 0.58:
        level = "高概率"
    elif score >= 55 and win_rate >= 0.52:
        level = "中概率"
    else:
        level = "低概率/防错"
    return f"{level}；样本 {sample_rows}；状态 {status}。"


def _probability_grade(score: float, win_rate: float, validation: dict[str, str]) -> str:
    gate = str(validation.get("risk_gate") or "")
    status = str(validation.get("validation_status") or "")
    if gate == "Blocked" or status in {"DoNotUse", "DataQualityReview"}:
        return "低概率-风险优先"
    if score >= 72 and win_rate >= 0.58 and gate == "Pass":
        return "高概率候选"
    if score >= 55 and win_rate >= 0.52:
        return "中概率候选"
    return "低概率/只观察"


def _high_probability_profit_condition(
    row: dict[str, object],
    item: dict[str, object],
    score: float,
    win_rate: float,
    validation: dict[str, str],
) -> str:
    action = str(row.get("Position") or "观望")
    pfi_os = str(validation.get("risk_gate") or "")
    volume = float(row.get("Volume") or 0)
    if "账户待更新" in action:
        return "账户未确认前盈利条件无效：Volume=0，先更新支付宝流水/持仓。"
    if pfi_os == "Blocked":
        return "风险闸门阻断：不按高概率盈利处理，买入取消，卖出只保留风控候选。"
    if _is_buy_action(action):
        return (
            "买入盈利条件：尾盘跌幅收窄或止跌、成交额不继续异常放大、事件原文无负面扩散、"
            f"策略胜率代理≥52.000%、本次Volume≤{format_percent(volume)}。"
        )
    if _is_sell_action(action):
        return (
            "卖出盈利条件：上涨乏力或转弱、成交额未支持继续突破、持有收益/现仓需要兑现，"
            f"策略胜率代理≥52.000%、本次Volume≤{format_percent(volume)}。"
        )
    if score >= 55 and win_rate >= 0.52:
        return "观察盈利条件：连续1-2日量价和事件同向后，下一轮才允许升级。"
    return "不满足高概率盈利条件：不占用资金，只记录观察。"


def _weekly_risk_gate_label(validation: dict[str, str]) -> str:
    gate = str(validation.get("risk_gate") or "")
    status = str(validation.get("validation_status") or "")
    if gate == "Pass":
        return "通过：允许进入操作策略评分。"
    if gate == "Blocked":
        return "阻断：买入取消；卖出只保留风控候选。"
    if status:
        return f"{_pfi_os_status_display(status)}：只作为观察权重。"
    return "基础代理：未拿到完整PFIOS指标。"


def _validation_float(validation: dict[str, str], key: str) -> float | str:
    value = validation.get(key)
    try:
        if value in {"", None}:
            return ""
        return float(value)
    except (TypeError, ValueError):
        return ""


def _price_volume_evidence(item: dict[str, object]) -> str:
    close = item.get("close")
    change = item.get("daily_change_pct")
    turnover = item.get("turnover")
    if close in {"", None} or change in {"", None}:
        return "量价证据缺失：不能升级。"
    turnover_text = _short_amount(float(turnover or 0)) if turnover not in {"", None} else "成交额缺失"
    source = str(item.get("source_name") or "未标注来源")
    return f"收盘 {float(close):.3f}；涨跌 {format_percent(float(change))}；成交额 {turnover_text}；{source}。"


def _policy_support_for_item(item: dict[str, object], events: list[dict[str, str]]) -> str:
    matched = _policy_events_for_item(item, events)
    if not matched:
        return "未命中高相关政策催化：不扩大Volume。"
    verified = [event for event in matched if _event_has_original_source(event)]
    if not verified:
        return "政策/事件原文未核验：只能作为风险背景，不扩大Volume。"
    event = verified[0]
    operation = str(event.get("policy_operation_impact") or "")
    authority = str(event.get("policy_authority") or "")
    title = str(event.get("title") or "")
    return f"{_compact_report_text(title, 36)}；权威 {authority}；{_compact_report_text(operation, 54)}"


def _policy_support_score(item: dict[str, object], events: list[dict[str, str]]) -> int:
    matched = _policy_events_for_item(item, events)
    if not matched:
        return 0
    best = 0
    for event in matched:
        status = str(event.get("policy_bridge_status") or "")
        if status not in {"refreshed", "cached_refreshed"}:
            continue
        if not _event_has_original_source(event):
            continue
        try:
            importance = int(float(event.get("policy_importance_score") or 0))
        except (TypeError, ValueError):
            importance = 0
        impact = str(event.get("impact") or "")
        best = max(best, 10 if impact == "positive" and importance >= 90 else 7 if impact == "positive" else 3)
    return best


def _policy_events_for_item(item: dict[str, object], events: list[dict[str, str]]) -> list[dict[str, str]]:
    symbol = str(item.get("symbol") or "")
    name = str(item.get("name") or "")
    theme = str(item.get("research_group") or item.get("industry") or "")
    matched = []
    for event in events:
        if str(event.get("type") or "") != "government_policy_bridge":
            continue
        blob = " ".join(str(event.get(key, "")) for key in ["related_symbols", "industry", "title", "summary"])
        if (symbol and symbol in blob) or (name and name in blob) or (theme and theme in blob):
            matched.append(event)
    return matched


def _event_original_verification_for_item(item: dict[str, object], events: list[dict[str, str]]) -> str:
    matched = _policy_events_for_item(item, events)
    if not matched:
        return "未命中政府/公告/新闻原文：不加分。"
    verified = [event for event in matched if _event_has_original_source(event)]
    if verified:
        event = verified[0]
        return f"已核验原文：{_compact_report_text(event.get('source_name', ''), 30)}；{_compact_report_text(event.get('source_url', ''), 46)}"
    statuses = "、".join(sorted({str(event.get("policy_bridge_status") or "unknown") for event in matched}))
    return f"未完成原文核验：桥接状态 {statuses}；只能作风险背景。"


def _event_has_original_source(event: dict[str, str]) -> bool:
    url = str(event.get("source_url") or "")
    if not url or "example.com" in url:
        return False
    return url.startswith("https://") or url.startswith("http://")


def _weekly_operation_strategy(
    row: dict[str, object],
    item: dict[str, object],
    score: float,
    win_rate: float,
    validation: dict[str, str],
) -> str:
    action = str(row.get("Position") or "观望")
    if "账户待更新" in action:
        if _is_buy_action(action):
            return "等待账户确认；当前买入取消为可执行项，Volume=0；更新支付宝流水/持仓并重生成后再评估。"
        if _is_sell_action(action):
            return "等待账户确认；当前卖出暂停为可执行项，Volume=0；更新支付宝流水/持仓并重生成后再评估。"
        return "账户待更新，维持观望。"
    if "等待确认" in action:
        return "待确认订单优先：不重复买卖，确认份额/净值后重新计算现仓。"
    if _is_buy_action(action):
        if str(validation.get("risk_gate") or "") == "Blocked":
            return "买入取消；风险闸门未通过前Volume=0，进入验证队列。"
        if score >= 70 and win_rate >= 0.56:
            return "买入候选保留；14:30-14:55尾盘仍止跌、量价不背离且账户/PFIOS通过后重算Volume。"
        if score >= 55:
            return "证据不足时不执行买入；账户、PFIOS和量价同时通过后重算候选Volume。"
        return "买入取消，转观望。"
    if _is_sell_action(action):
        if score >= 55:
            return "卖出候选保留；若放量突破并有政策/业绩支持则暂停卖出并重算。"
        return "卖出暂停；只保留风控提醒。"
    return "观望，不占用新增资金；仅记录主题强弱和政策催化。"


def _weekly_failure_action(row: dict[str, object], item: dict[str, object], validation: dict[str, str]) -> str:
    action = str(row.get("Position") or "观望")
    risk_trigger = _risk_trigger(item, action)
    if "账户待更新" in action:
        return "失败动作：账户未更新前不执行；若更新后持仓收益率、待确认订单或尾盘量价反向，取消该候选。"
    if _is_buy_action(action):
        return f"失败动作：取消买入；已有持仓不补。触发条件：{risk_trigger}"
    if _is_sell_action(action):
        return f"失败动作：暂停卖出。触发条件：{risk_trigger}"
    if "等待确认" in action:
        return "失败动作：若待确认订单与最新行情反向，确认后先降低下一次Volume。"
    return "失败动作：继续观望；不把单一政策或单日行情升级成买卖。"


def _short_amount(value: float) -> str:
    abs_value = abs(value)
    if abs_value >= 100_000_000:
        return f"{value / 100_000_000:.3f}亿"
    if abs_value >= 10_000:
        return f"{value / 10_000:.3f}万"
    return f"{value:.3f}"


def _compact_report_text(value: object, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def _weighted_return(advice: list[dict[str, object]], factors: list[dict[str, object]]) -> float:
    if not advice:
        return 0.0
    factor_by_name = {str(item["name"]): item for item in factors}
    weighted = []
    weights = []
    for row in advice:
        factor = factor_by_name.get(str(row["Name"]))
        if not factor:
            continue
        change = factor.get("daily_change_pct")
        if change in {"", None}:
            continue
        weight = float(row.get("Volume") or 0)
        weighted.append(float(change) * weight)
        weights.append(weight)
    return sum(weighted) / sum(weights) if weights and sum(weights) else 0.0


def _directional_weighted_return(advice: list[dict[str, object]], factors: list[dict[str, object]]) -> float:
    if not advice:
        return 0.0
    factor_by_name = {str(item["name"]): item for item in factors}
    weighted = []
    weights = []
    for row in advice:
        factor = factor_by_name.get(str(row["Name"]))
        if not factor:
            continue
        change = factor.get("daily_change_pct")
        if change in {"", None}:
            continue
        weight = float(row.get("Volume") or 0)
        direction = -1.0 if _is_sell_action(str(row.get("Position", ""))) else 1.0
        weighted.append(float(change) * weight * direction)
        weights.append(weight)
    return sum(weighted) / sum(weights) if weights and sum(weights) else 0.0


def _action_counts(advice: list[dict[str, object]]) -> dict[str, int]:
    counts = {"买入": 0, "卖出": 0, "等待确认": 0, "观望": 0}
    for row in advice:
        action = str(row.get("Position", ""))
        if "等待确认" in action:
            counts["等待确认"] += 1
        elif _is_buy_action(action):
            counts["买入"] += 1
        elif _is_sell_action(action):
            counts["卖出"] += 1
        else:
            counts["观望"] += 1
    return counts


def _counts_text(counts: dict[str, int]) -> str:
    return "、".join(f"{key}{value}" for key, value in counts.items())


def _daily_report_digest(as_of: str | None, session: str) -> str:
    if not as_of:
        return "未提供日期，无法读取对比报告。"
    path = markdown_path(daily_report_name(session, as_of) + ".md")
    if not path.exists():
        return f"{session} 报告未生成，无法对比。"
    content = path.read_text(encoding="utf-8")
    counts = _report_action_counts(content)
    return f"{path.name} 已生成，动作结构 {_counts_text(counts)}。"


def _weekly_generated_report_digest(as_of: str | None) -> str:
    if not as_of:
        return "未提供日期，无法读取本周报告。"
    day = date.fromisoformat(as_of)
    monday = day - timedelta(days=day.weekday())
    sessions = ["pre_open", "midday", "post_close"]
    generated = 0
    aggregate = {"买入": 0, "卖出": 0, "等待确认": 0, "观望": 0}
    for offset in range(5):
        current = (monday + timedelta(days=offset)).isoformat()
        for session in sessions:
            path = markdown_path(daily_report_name(session, current) + ".md")
            if not path.exists():
                continue
            generated += 1
            counts = _report_action_counts(path.read_text(encoding="utf-8"))
            for key, value in counts.items():
                aggregate[key] += value
        kline_path = markdown_path(kline_report_name((monday + timedelta(days=offset)).isoformat()) + ".md")
        if kline_path.exists():
            generated += 1
            counts = _report_action_counts(kline_path.read_text(encoding="utf-8"))
            for key, value in counts.items():
                aggregate[key] += value
    monday_path = markdown_path(weekly_report_name("monday_pre_open", monday.isoformat()) + ".md")
    friday_path = markdown_path(weekly_report_name("friday_post_close", (monday + timedelta(days=4)).isoformat()) + ".md")
    weekly_count = sum(1 for path in [monday_path, friday_path] if path.exists())
    return f"本周已读取日报/K线 {generated} 份、周报 {weekly_count} 份，累计动作结构 {_counts_text(aggregate)}。"


def _report_action_counts(content: str) -> dict[str, int]:
    return {
        "买入": content.count("建议买入"),
        "卖出": content.count("建议卖出"),
        "等待确认": content.count("等待确认"),
        "观望": content.count("观望"),
    }


def _core_rows(advice: list[dict[str, object]], factors: list[dict[str, object]], priority: str) -> list[dict[str, object]]:
    factor_by_name = {str(item["name"]): item for item in factors}
    rows = []
    for row in advice:
        factor = factor_by_name.get(str(row["Name"]), {})
        change = factor.get("daily_change_pct")
        change_text = format_percent(float(change)) if change not in {"", None} else "无涨跌幅"
        source = factor.get("source_name", "来源未标注")
        rows.append(
            {
                "priority": priority,
                "Name": row["Name"],
                "Position": row["Position"],
                "Volume": row["Volume"],
                "holding_amount": row.get("holding_amount", 0),
                "holding_return_amount": row.get("holding_return_amount", 0),
                "current_weight": row.get("current_weight", 0),
                "holding_return_pct": row.get("holding_return_pct", 0),
                "pending_order_amount": row.get("pending_order_amount", 0),
                "reason": f"{change_text}；{source}",
                "risk": row.get("exit_condition") or row.get("risk_note") or "",
            }
        )
    return rows


def _leaders(factors: list[dict[str, object]]) -> list[dict[str, object]]:
    valid = [item for item in factors if item.get("daily_change_pct") not in {"", None}]
    return sorted(valid, key=lambda item: float(item.get("daily_change_pct") or 0), reverse=True)[:3]


def _research_confidence(
    item: dict[str, object],
    advice_row: dict[str, object],
    event_blob: str,
    validation: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    score = 0
    validation_plan = []
    if item.get("close") not in {"", None} and item.get("daily_change_pct") not in {"", None}:
        score += 20
    else:
        validation_plan.append("行情源缺口：补齐当日价格、涨跌幅和成交额，否则降级观望")
    if item.get("turnover") not in {"", None}:
        score += 10
    else:
        validation_plan.append("成交额待补齐")
    if str(item.get("name", "")) in event_blob or str(item.get("symbol", "")) in event_blob:
        score += 15
    else:
        validation_plan.append("事件源持续扫描")
    if abs(float(item.get("daily_change_pct") or 0)) > 0.01:
        score += 10
    if item.get("pe") not in {"", None, ""} or item.get("pb") not in {"", None, ""}:
        score += 10
    else:
        score += 4
        validation_plan.append(_valuation_proxy_text(item))
    if advice_row.get("holding_amount", 0):
        score += 10
    pfi_os_status = _pfi_os_status(item, advice_row, validation or {})
    if pfi_os_status == "ContinueResearch":
        score += 15
    elif pfi_os_status == "ValidationQueued":
        score += 6
        validation_plan.append("PFIOS排队")
    else:
        validation_plan.append(_pfi_os_gap(pfi_os_status, validation or {}))
    if advice_row.get("risk_note"):
        score += 10
    level = _cap_confidence_level(_confidence_level_from_score(score), pfi_os_status)
    return score, level, "；".join(validation_plan[:3]) or "已完成基础行情/估值/PFIOS校验"


def _pfi_os_status(item: dict[str, object], advice_row: dict[str, object], validation: dict[str, str] | None = None) -> str:
    if validation and validation.get("validation_status"):
        return str(validation["validation_status"])
    if item.get("close") in {"", None} or item.get("daily_change_pct") in {"", None}:
        return "DataQualityReview"
    if float(advice_row.get("Volume") or 0) > 0:
        return "ValidationQueued"
    if abs(float(item.get("daily_change_pct") or 0)) > 0.02:
        return "NeedsMoreEvidence"
    return "WatchOnly"


def _pfi_os_gap(status: str, validation: dict[str, str]) -> str:
    if status == "NeedsMoreEvidence":
        if str(validation.get("risk_gate", "")) == "Blocked":
            return "PFIOS风险闸门未通过"
        return "PFIOS证据不足"
    if status == "DataQualityReview":
        rows = validation.get("sample_rows")
        return f"PFIOS样本不足({rows}条)" if rows not in {"", None} else "PFIOS数据质量待核验"
    if status == "DoNotUse":
        return "PFIOS停用"
    if status == "WatchOnly":
        return "PFIOS仅观察"
    if status == "ValidationQueued":
        return "PFIOS排队待验证"
    if status == "NotValidated":
        return "已补入PFIOS基础覆盖队列"
    return "PFIOS状态待确认"


def _pfi_os_status_display(status: str) -> str:
    mapping = {
        "ContinueResearch": "验证通过-可继续研究",
        "ValidationQueued": "排队验证-未完成",
        "DataQualityReview": "数据质量待复核",
        "NeedsMoreEvidence": "证据不足-禁止执行买入",
        "DoNotUse": "验证停用-不得执行",
        "WatchOnly": "仅观察",
        "NotValidated": "未验证-仅观察",
    }
    return mapping.get(status, "状态待确认")


def _risk_gate_display(status: str) -> str:
    mapping = {
        "Pass": "通过",
        "Blocked": "阻断",
        "Pending": "待验证",
    }
    return mapping.get(status, status or "待验证")


def _pfi_os_conclusion_display(validation: dict[str, str]) -> str:
    raw = str(validation.get("conclusion") or "")
    if raw:
        return (
            raw.replace("ValidationQueued", "排队验证")
            .replace("NeedsMoreEvidence", "证据不足")
            .replace("DataQualityReview", "数据质量待复核")
            .replace("ContinueResearch", "验证通过")
            .replace("NotValidated", "未验证")
            .replace("DoNotUse", "验证停用")
        )
    return "排队验证；等待 PFIOS 生成可审计结果，未完成前不升级为执行依据。"


def _valuation_proxy_text(item: dict[str, object]) -> str:
    asset_class = str(item.get("asset_class") or "")
    if asset_class in {"ETF", "Fund", "Index"}:
        return "估值代理校验：ETF/指数用行业PB、宽基估值分位和跟踪资产替代"
    return "估值代理校验：个股优先补PE/PB，缺失时用行业估值分位替代"


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


def _pfi_os_sample_text(validation: dict[str, str]) -> str:
    if not validation:
        return "近3年日频 + 近1年滚动样本（待生成）"
    rows = validation.get("sample_rows", "")
    return f"可用历史样本 {rows} 条"


def _pfi_os_monte_carlo_text(validation: dict[str, str]) -> str:
    runs = validation.get("monte_carlo_runs", "") if validation else ""
    if not runs or str(runs) == "0":
        return "未运行；样本不足或待验证"
    return f"{runs}次"


def _pfi_os_rerun_text(validation: dict[str, str]) -> str:
    reruns = validation.get("pipeline_reruns", "") if validation else ""
    if not reruns:
        return "全流程>=2次（待生成）"
    return f"全流程{reruns}次"


def _counter_reason(row: dict[str, object], factor: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    turnover = float(factor.get("turnover") or 0)
    if _is_buy_action(action):
        return "买入假设可能错在把趋势下跌误判为低吸；若尾盘继续放量下跌或出现负面事件，买入结论失效。"
    if _is_sell_action(action):
        return "卖出假设可能错在把真实突破误判为兑现点；若放量站稳并有事件/基本面支持，卖出结论应暂停并重算。"
    if turnover <= 0:
        return "缺少成交额确认，价格信号不能证明资金真实参与。"
    return "观望假设可能错在忽略了趋势启动；若连续放量突破，应从普通观察升级为重点观察。"


def _decision_signal_quality(row: dict[str, object], factor: dict[str, object], status: str) -> str:
    if status == "DataQualityReview" or factor.get("daily_change_pct") in {"", None}:
        return "Low"
    score = _daily_signal_score(row, factor)
    if status == "ContinueResearch" and score >= 3:
        return "High"
    if score >= 2 and status not in {"DoNotUse", "DataQualityReview"}:
        return "Medium"
    return "Low"


def _daily_signal_score(row: dict[str, object], factor: dict[str, object]) -> int:
    action = str(row.get("Position", ""))
    change = float(factor.get("daily_change_pct") or 0)
    momentum = float(factor.get("momentum_5d") or change)
    volume_ratio = float(factor.get("volume_ratio_5d") or 0)
    score = 0
    if factor.get("turnover") not in {"", None} and float(factor.get("turnover") or 0) > 0:
        score += 1
    if volume_ratio >= 1.0:
        score += 1
    if _is_buy_action(action) and change <= 0 and momentum > -0.08:
        score += 1
    elif _is_sell_action(action) and (change >= 0 or momentum < 0):
        score += 1
    elif not _is_buy_action(action) and not _is_sell_action(action) and abs(change) < 0.015:
        score += 1
    if row.get("holding_amount", 0) not in {"", None} and float(row.get("holding_amount") or 0) > 0:
        score += 1
    return score


def _trend_range_conclusion(row: dict[str, object], factor: dict[str, object]) -> str:
    change = factor.get("daily_change_pct")
    momentum = float(factor.get("momentum_5d") or change or 0)
    if change in {"", None}:
        return "缺当日价格，MA/EMA/BOLL不得下结论。"
    action = str(row.get("Position", ""))
    if _is_buy_action(action):
        if float(change) <= 0 and momentum > -0.08:
            return "趋势区间结论：下跌承接可观察；尾盘不破位才保留买入。"
        return "趋势区间结论：追高或破位风险，取消买入并重算。"
    if _is_sell_action(action):
        if float(change) >= 0:
            return "趋势区间结论：上涨兑现成立；若收盘放量突破则暂停卖出。"
        return "趋势区间结论：转弱降仓成立；反弹站回区间则暂停追加卖出。"
    if momentum > 0.015:
        return "趋势区间结论：偏强但未到动作阈值，等待回踩或放量确认。"
    if momentum < -0.015:
        return "趋势区间结论：偏弱，等待止跌样本。"
    return "趋势区间结论：震荡，维持观望。"


def _momentum_conclusion(factor: dict[str, object]) -> str:
    change = factor.get("daily_change_pct")
    momentum = float(factor.get("momentum_5d") or change or 0)
    if change in {"", None}:
        return "缺价格，MACD/RSI/KDJ动能不得确认。"
    if momentum >= 0.025:
        return "动能结论：偏强，防追高；需成交量确认。"
    if momentum <= -0.025:
        return "动能结论：偏弱，只有止跌才可承接。"
    return "动能结论：中性，单日涨跌不能单独决定买卖。"


def _volume_confirmation(row: dict[str, object], factor: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    turnover = factor.get("turnover")
    ratio = float(factor.get("volume_ratio_5d") or 0)
    if turnover in {"", None} or float(turnover or 0) <= 0:
        return "VOL结论：缺成交额，信号降级。"
    if "账户待更新" in action:
        return "VOL结论：成交额只作研究确认；账户未确认，不支持执行Volume。"
    if "等待确认" in action:
        return "VOL结论：成交额只作背景确认；待确认订单未结算，不支持新增Volume。"
    if not _is_buy_action(action) and not _is_sell_action(action):
        return "VOL结论：成交额只作观察确认；当前不执行Volume。"
    if ratio >= 1.2:
        return "VOL结论：成交量确认，信号可保留。"
    if ratio < 0.8:
        return "VOL结论：缩量，买卖候选降级；执行Volume需重算。"
    return "VOL结论：一般确认；保留候选Volume上限，执行前仍需账户和PFIOS闸门通过。"


def _mixed_signal_conclusion(row: dict[str, object], factor: dict[str, object], status: str) -> str:
    action = str(row.get("Position", ""))
    if "账户待更新" in action:
        return "账户闸门未通过：技术信号只保留研究方向，不执行候选Volume；更新支付宝流水/持仓并重生成后重算。"
    if "等待确认" in action:
        return "待确认订单优先：不执行候选Volume；确认份额、净值和手续费后再判断是否保留方向。"
    if not _is_buy_action(action) and not _is_sell_action(action):
        return "观察状态：不执行候选Volume；只有连续1-2日强弱、成交额、事件和PFIOS同向才升级。"
    quality = _decision_signal_quality(row, factor, status)
    if quality == "High":
        return "三类信号基本同向：趋势/动能/VOL支持；保留候选Volume上限，执行前仍需账户和PFIOS闸门通过。"
    if quality == "Medium":
        return "两类信号可用但仍有缺口：尾盘价格、成交额、事件方向全部满足后重算候选Volume；任一不满足则取消执行。"
    return "信号不一致或数据缺口：取消、暂停或观望。"


def _decision_evidence_needed(
    row: dict[str, object],
    factor: dict[str, object],
    status: str,
    validation: dict[str, str] | None = None,
) -> str:
    action = str(row.get("Position", ""))
    if factor.get("daily_change_pct") in {"", None}:
        return "补齐当日价格、涨跌幅、成交额和来源交叉校验。"
    if status == "DataQualityReview":
        rows = (validation or {}).get("sample_rows")
        return f"补齐>=60条日频样本、成交额、收盘价；当前样本 {rows or '未知'} 条。"
    if status == "NeedsMoreEvidence":
        if _is_buy_action(action):
            return "需要尾盘止跌、成交额不继续异常放大、无负面事件、PFIOS风险闸门通过。"
        if _is_sell_action(action):
            return "需要尾盘不能放量突破、上涨缺乏持续事件支持、PFIOS风险闸门不否定卖出。"
        return "需要连续1-2日强弱排序、成交额和事件面同向后再升级。"
    if status == "ValidationQueued":
        return "等待PFIOS完成>=100,000次模拟、全流程>=2次重跑和样本外检查。"
    return "维持现有证据链，持续监控推翻条件。"


def _decision_operation_conclusion(row: dict[str, object], factor: dict[str, object], status: str) -> str:
    action = str(row.get("Position", ""))
    quality = _decision_signal_quality(row, factor, status)
    if "账户待更新" in action:
        if _is_buy_action(action):
            return "明确结论：等待账户确认；当前买入动作取消为可执行项，Volume 0；账户与PFIOS闸门通过后重新评估。"
        if _is_sell_action(action):
            return "明确结论：等待账户确认；当前卖出动作暂停为可执行项，Volume 0；账户确认后重新评估。"
        return "明确结论：账户待更新，维持观望。"
    if status == "DataQualityReview":
        return "明确结论：观望；不新增买卖。"
    if _is_buy_action(action):
        if quality == "High":
            return "明确结论：买入候选保留；账户、PFIOS和尾盘量价通过后重算Volume，跌破关键区间则取消。"
        if quality == "Medium":
            return "明确结论：证据不足时不买；账户、PFIOS和尾盘量价同时通过后重算候选Volume。"
        return "明确结论：不买，改观望。"
    if _is_sell_action(action):
        if quality in {"High", "Medium"}:
            return "明确结论：卖出候选；账户确认且尾盘未放量突破时重算Volume。"
        return "明确结论：卖出暂停，等待收盘确认。"
    if "等待确认" in action:
        return "明确结论：等待确认；不重复买卖。"
    return "明确结论：观望；只有连续1-2日强弱排序改善、成交额>0且事件/PFIOS同向时才升级，否则不新增买卖。"


def _account_gate_text(blocked: bool, reason: str, row: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    if blocked:
        if _is_buy_action(action):
            return f"阻断买入金额：{reason}；Volume=0，账户确认后重算。"
        if _is_sell_action(action):
            return f"阻断卖出金额：{reason}；Volume=0，账户确认后重算。"
        return f"账户未确认：{reason}；仅观察。"
    pending = float(row.get("pending_order_amount") or 0)
    if pending > 0:
        return f"已有待确认订单 {pending:,.2f} 元；不重复升级同向动作。"
    return "账户闸门通过：仍受尾盘样本、事件和PFIOS约束。"


def _daily_pass_condition(row: dict[str, object], factor: dict[str, object], status: str) -> str:
    action = str(row.get("Position", ""))
    if factor.get("daily_change_pct") in {"", None}:
        return "成立条件缺失：没有当日行情，不升级。"
    if _is_buy_action(action):
        return "买入成立：尾盘跌幅收窄或止跌，成交额不继续异常放大，无新增负面事件，PFIOS未阻断。"
    if _is_sell_action(action):
        return "卖出成立：尾盘上涨乏力或转弱，成交额未支持继续突破，持仓收益/现仓需要降风险。"
    if "等待确认" in action:
        return "成立条件：待确认订单完成后，份额、净值、手续费与持仓金额可核验。"
    if status == "ContinueResearch":
        return "观察成立：连续强弱排序、成交额和事件面同向，可进入下一轮重点观察。"
    return "观察成立：当前不占用资金；升级条件为连续1-2日强弱排序改善、成交额>0、事件面与PFIOS不反向。"


def _daily_fail_action(row: dict[str, object], factor: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    trigger = _risk_trigger(factor, action)
    if "账户待更新" in action:
        return "更新账户前不执行；账户确认后若尾盘和事件反向，取消该候选。"
    if _is_buy_action(action):
        return f"取消买入；触发：{trigger}"
    if _is_sell_action(action):
        return f"暂停卖出；触发：{trigger}"
    if "等待确认" in action:
        return "确认结果与当前方向冲突时，下一次报告降低该对象权重。"
    return "维持观望；若成交额缺失、价格未转强或PFIOS风险闸门阻断，不因单日行情升级。"


def _pfi_os_operation_behavior(row: dict[str, object], factor: dict[str, object], validation: dict[str, str]) -> str:
    status = str(validation.get("validation_status") or _pfi_os_status(factor, row, validation))
    if status == "ContinueResearch":
        return "允许进入报告信号质量矩阵；仍受Volume和风险触发约束。"
    if status == "ValidationQueued":
        return "进入验证队列；等待模拟、样本外和风险闸门，不升级高可信。"
    if status == "NeedsMoreEvidence":
        return _decision_operation_conclusion(row, factor, status)
    if status == "DataQualityReview":
        return "先修数据；报告只能观望，不能新增动作。"
    if status == "DoNotUse":
        return "停用该线索。"
    return "维持观察。"


def _counter_wait_sample(row: dict[str, object], factor: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    if _is_buy_action(action):
        return "14:30-14:55 Australia/Sydney 检查收盘前是否止跌、成交额是否收敛、新闻/公告是否无负面扩散。"
    if _is_sell_action(action):
        return "14:30-14:55 Australia/Sydney 检查是否放量突破、是否由事件催化支持、是否仍高于兑现区间。"
    return "连续1-2个交易日检查强弱排序、成交额和事件面是否同向。"


def _counter_expected_result(row: dict[str, object], factor: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    if _is_buy_action(action):
        return "期望看到跌幅收窄或翻红、成交额不再异常放大、无新增负面事件。"
    if _is_sell_action(action):
        return "期望看到上涨乏力或回落；若继续放量走强，则卖出假设被削弱。"
    return "期望看到方向突破且成交额确认；否则继续观望。"


def _counter_clear_conclusion(row: dict[str, object], factor: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    turnover = float(factor.get("turnover") or 0)
    if factor.get("daily_change_pct") in {"", None}:
        return "结论：观望；缺当日价格和成交额，不能升级为买卖候选。"
    if "账户待更新" in action:
        if _is_buy_action(action):
            return "结论：买入候选保留，但账户未更新前不执行。"
        if _is_sell_action(action):
            return "结论：卖出候选保留，但账户未更新前不执行。"
        return "结论：账户待更新，观望；更新账户前不新增买卖。"
    if _is_buy_action(action):
        return "结论：买入可保留，但只在尾盘样本满足时执行。"
    if _is_sell_action(action):
        return "结论：卖出候选可保留；若放量突破则暂停并重算。"
    if turnover <= 0:
        return "结论：观望；成交额缺失，不能证明资金参与。"
    return "结论：观望；只有方向突破、成交额确认且事件/PFIOS同向时升级，否则维持观望。"


def _counter_operation(row: dict[str, object], factor: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    if "账户待更新" in action:
        return "先更新支付宝流水/持仓并重新生成报告；更新前Volume为0，不执行买卖。"
    if _is_buy_action(action):
        return "若反方触发：取消买入；已有持仓不补。若未触发：按信号质量矩阵执行。"
    if _is_sell_action(action):
        return "若反方触发：卖出暂停。若未触发：账户确认后按收盘规则重算Volume。"
    return "若反方触发且成交额/事件/PFIOS同向：升级到重点观察；否则维持观望且不占用资金。"


def _theme_risk(theme: str, avg_change: float, turnover: float) -> str:
    if turnover <= 0:
        return "成交额缺失"
    if abs(avg_change) > 0.03:
        return "单日波动过大，防止过度解读"
    if any(token in theme for token in ["纳指", "美股", "港股", "黄金"]):
        return "汇率/海外市场风险"
    return "需要事件和成交额持续确认"


def _is_accumulation_observation(action: str) -> bool:
    return _is_buy_action(action)


def _is_reduce_observation(action: str) -> bool:
    return _is_sell_action(action)


def _is_buy_action(action: str) -> bool:
    return any(token in action for token in ["建议买入", "买入", "补仓", "承接", "低仓位"])


def _is_sell_action(action: str) -> bool:
    return any(token in action for token in ["建议卖出", "卖出", "减仓", "减暴露", "降暴露"])


def _weak(factors: list[dict[str, object]]) -> list[dict[str, object]]:
    valid = [
        item
        for item in factors
        if item.get("daily_change_pct") not in {"", None} and float(item.get("daily_change_pct") or 0) < 0
    ]
    return sorted(valid, key=lambda item: float(item.get("daily_change_pct") or 0))[:3]


def _names(rows: list[dict[str, object]]) -> str:
    return "、".join(str(item["name"]) for item in rows) if rows else "暂无可验证标的"


def _event_text(events: list[dict[str, str]]) -> str:
    return "；".join(
        f"{_full_event_time(event)} {event['title']}（{event.get('source_name', '来源未标注')}）"
        for event in sorted(events, key=_event_sort_key)[:6]
    )


def _theme_from_related(related: str, factor_theme_by_symbol: dict[str, str]) -> str:
    for symbol in related.replace(",", ";").split(";"):
        symbol = symbol.strip()
        if symbol in factor_theme_by_symbol:
            return factor_theme_by_symbol[symbol]
    return ""


def _impact_label(value: object) -> str:
    labels = {"positive": "正面", "negative": "负面", "neutral": "中性"}
    return labels.get(str(value), str(value or ""))


def _event_certainty(event: dict[str, str]) -> str:
    if str(event.get("type") or "") == "government_policy_bridge":
        status = str(event.get("policy_bridge_status") or "")
        authority = str(event.get("policy_authority") or "")
        if status in {"refreshed", "cached_refreshed"} and authority and "未标注" not in authority and _event_has_original_source(event):
            return "High"
        if status in {"refreshed", "cached_refreshed"}:
            return "Medium-Low"
        return "Low"
    url = str(event.get("source_url", ""))
    source = str(event.get("source_name", ""))
    related = str(event.get("related_symbols", ""))
    if url.startswith("https://") and related:
        return "High"
    if url.startswith("opend://") or "Moomoo" in source:
        return "Medium"
    if url.startswith("local://"):
        return "Medium-Low"
    if "example.com" in url or not url:
        return "Low"
    return "Medium"


def _verifiable_data(event: dict[str, str], related: str) -> str:
    pieces = []
    if related:
        pieces.append(f"相关标的 {related}")
    if event.get("source_name"):
        pieces.append(str(event.get("source_name")))
    if event.get("source_url"):
        pieces.append("原文URL已记录" if _event_has_original_source(event) else "仅记录系统/本地状态URL")
    if event.get("policy_authority"):
        pieces.append(f"政策权威 {event.get('policy_authority')}")
    if event.get("policy_importance_score"):
        pieces.append(f"政策重要性 {event.get('policy_importance_score')}")
    return "；".join(pieces) if pieces else "待补充来源"


def _event_source_review(event: dict[str, str]) -> str:
    url = str(event.get("source_url") or "")
    event_type = str(event.get("type") or "")
    if event_type == "government_policy_bridge":
        status = str(event.get("policy_bridge_status") or "unknown")
        report_path = str(event.get("policy_report_path") or "")
        original_fetch = str(event.get("policy_original_fetch_status") or "unknown")
        misread_risk = _policy_misread_risk(event)
        if status in {"refreshed", "cached_refreshed"} and _event_has_original_source(event):
            archive_status = "政策系统报告已归档" if report_path else "政策系统报告待归档"
            return (
                f"政府文件解读系统已完成原文核验；原文抓取状态 {original_fetch}；"
                f"误读风险：{misread_risk}；{archive_status}。"
            )
        if url:
            return f"政府文件解读系统只有状态/缓存URL或刷新状态 {status}；原文抓取状态 {original_fetch}；误读风险：高；只作为风险背景。"
        return f"政府文件解读系统未返回原文URL；状态 {status}；原文抓取状态 {original_fetch}；误读风险：高；不提高买入权重。"
    if url.startswith("https://") or url.startswith("http://"):
        return "已记录公告/新闻原文URL；需与行情、成交额和持仓约束同向才改变Volume。"
    if url.startswith("file://") or url.startswith("local://"):
        return "本地来源已记录；不能单独升级为买卖依据。"
    if url.startswith("opend://"):
        return "行情链路已记录；只证明价格/成交额，不证明事件原因。"
    return "缺少原文URL；不作为新增买入依据。"


def _event_source_chain(event: dict[str, str]) -> str:
    if str(event.get("type") or "") == "government_policy_bridge":
        status = str(event.get("policy_bridge_status") or "")
        authority = str(event.get("policy_authority") or "")
        url = str(event.get("source_url") or "")
        report_path = str(event.get("policy_report_path") or "")
        request_path = str(event.get("policy_request_path") or "")
        original_fetch = str(event.get("policy_original_fetch_status") or "unknown")
        original_status = "原文核验=通过" if _event_has_original_source(event) else "原文核验=未通过"
        pieces = [
            f"政府文件解读系统：{status}",
            f"权威 {authority}",
            original_status,
            f"原文抓取状态={original_fetch}",
            f"误读风险={_policy_misread_risk(event)}",
        ]
        if url:
            pieces.append(f"原文 {_compact_report_text(url, 46)}")
        if request_path:
            pieces.append("独立爬虫请求已记录")
        if report_path:
            pieces.append("政策系统报告已归档")
        return "；".join(pieces) + "。"
    source = str(event.get("source_name") or "未标注来源")
    url = str(event.get("source_url") or "")
    if url.startswith("opend://"):
        return f"{source}；OpenD/自选池行情链路。"
    if url.startswith("https://"):
        return f"{source}；公开网页源。"
    return f"{source}；本地记录源。"


def _follow_up_indicator(event: dict[str, str]) -> str:
    impact = str(event.get("impact", ""))
    event_type = str(event.get("type", ""))
    if event_type == "government_policy_bridge":
        return "跟踪政策细则、地方配套、资金安排、主题成交额和相关对象相对强弱。"
    if impact == "positive":
        return "成交额延续、主题强弱连续、公告/政策后续落地进度"
    if impact == "negative":
        return "跌幅是否扩散至持仓、是否放量、是否触发纪律降级"
    if "technical" in event_type:
        return "收盘价、MA/EMA/BOLL 与成交量是否共同确认"
    if "fundamental" in event_type:
        return "业绩、估值和现金流指标是否支持价格变化"
    return "价格、成交额、公告和新闻下一轮交叉验证结果"


def _event_operation_impact(event: dict[str, str]) -> str:
    if event.get("policy_operation_impact"):
        return str(event["policy_operation_impact"])
    impact = str(event.get("impact") or "")
    if impact == "positive":
        return "正面事件只增强观察优先级；买入仍需量价和持仓约束同向。"
    if impact == "negative":
        return "负面事件提高卖出风控优先级；买入类信号取消或转观望。"
    return "中性事件只作为背景，不改变Volume。"


def _policy_misread_risk(event: dict[str, str]) -> str:
    if not _event_has_original_source(event):
        return "高，缺原文URL，禁止提高买入分和Volume"
    status = str(event.get("policy_original_fetch_status") or "")
    if status != "verified":
        return "中高，原文抓取状态未验证，只能作为风险背景"
    operation = str(event.get("policy_operation_impact") or "")
    if "不提高买入" in operation or "不单独扩大Volume" in operation:
        return "中，政策不直接支持加仓"
    return "低，仍需量价和持仓纪律同向"


def _actual_snapshot_time() -> str:
    status_path = ROOT / "data" / "sample" / "opend_status.json"
    if not status_path.exists():
        return "未记录"
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "读取失败"
    return str(payload.get("updated_at") or "未记录")


def _risk_trigger(item: dict[str, object], action: str) -> str:
    change = item.get("daily_change_pct")
    if change in {"", None}:
        return "继续缺行情或来源冲突"
    if _is_buy_action(action):
        return "尾盘继续放量下跌、负面事件确认或跌破关键均线"
    if _is_sell_action(action):
        return "继续放量突破或基本面改善时，卖出假设失效"
    return "成交额进入前列但价格未转强"


def _action_priority(action: str) -> int:
    if _is_sell_action(action):
        return 0
    if _is_buy_action(action):
        return 1
    if "等待确认" in action:
        return 2
    return 3


def _compact_basis(row: dict[str, object], factor: dict[str, object]) -> str:
    change = factor.get("daily_change_pct")
    change_text = format_percent(float(change)) if change not in {"", None} else "无涨跌"
    entry = str(row.get("entry_condition", ""))
    if "账户待更新" in str(row.get("Position", "")):
        entry = _after_marker(entry, "原研究依据：") or "账户未更新，方向仅保留研究。"
        return _compact_report_text(f"{change_text}；账户未更新，Volume=0；原依据：{entry}", 150)
    return _compact_report_text(f"{change_text}；{entry}", 150)


def _compact_core_risk(row: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    risk = str(row.get("risk_note", ""))
    pieces = []
    if "账户待更新" in action:
        pieces.append("账户未更新，Volume=0，确认后重算。")
    if _is_buy_action(action):
        pieces.append("买入失效：尾盘放量下跌/负面事件/待确认买单。")
    elif _is_sell_action(action):
        pieces.append("卖出失效：放量突破且事件面支持趋势。")
    else:
        pieces.append(_compact_report_text(risk, 72) or "观望对象：不因单日行情升级。")
    holding = float(row.get("current_weight") or 0)
    holding_return = float(row.get("holding_return_pct") or 0)
    if holding > 0:
        pieces.append(f"现仓{holding * 100:.3f}%，收益{holding_return * 100:.3f}%。")
    return _compact_report_text(" ".join(pieces), 150)


def _after_marker(text: str, marker: str) -> str:
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].strip()
