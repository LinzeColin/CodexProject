from __future__ import annotations

from src.config import ROOT
from src.models import Source
from src.reporting.account_dashboard import account_dashboard
from src.pfi_os.engine import latest_result_by_symbol
from src.reporting.charts import kline_long_report_sections
from src.reporting.naming import kline_report_name
from src.reporting.renderer import render_template, table, toc_for, write_report_bundle, write_source_log


def generate_kline_report(
    as_of: str,
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    advice: list[dict[str, object]],
    sources: list[Source],
    account_summary: dict[str, object],
) -> str:
    sorted_factors = sorted(
        factors,
        key=lambda item: float(item.get("daily_change_pct") or -999),
        reverse=True,
    )
    long_sections, selected, technical_rows = kline_long_report_sections(factors, advice, as_of)
    report = render_template(
        ROOT / "01_templates" / "K线分析报告模板.md",
        {
            "date": as_of,
            "toc": toc_for(
                [
                    "一、K线操作总表",
                    "二、信号质量矩阵",
                    "三、训练问题答案与分析逻辑",
                    "四、证据缺口与操作规则",
                    "五、反方情景动作矩阵",
                    "六、K线候选池与强弱结论",
                    "七、单标的多指标深度分析",
                    "八、K线训练结论",
                    "九、持仓与支付宝历史交易附图",
                ]
            ),
            "action_table": _kline_action_table(technical_rows, advice, as_of),
            "signal_quality_matrix": _signal_quality_matrix(technical_rows),
            "training_answer_matrix": _training_answer_matrix(technical_rows),
            "evidence_gap_actions": _evidence_gap_actions(technical_rows, as_of),
            "counter_action_matrix": _counter_action_matrix(technical_rows),
            "account_dashboard": account_dashboard(as_of, "kline", account_summary, advice),
            "technical_view": _technical_view(technical_rows),
            "selection_summary": _selection_summary(selected, advice, technical_rows),
            "long_sections": long_sections,
            "learning_notes": (
                "- 训练结论：K线报告只回答技术信号质量、操作确认、失败条件和训练题答案；事实/事件/账户总览不在本报告重复展开。\n"
                "- 执行标准：MA/EMA/BOLL 负责趋势与区间，MACD/RSI/KDJ 负责动能，VOL 负责确认。三类至少两类同向，只能保留研究候选；账户、PFIOS、尾盘价格和成交额全部通过后才重算候选 Volume。\n"
                "- 复盘标准：每个标的后续按“等待样本”列检查；证据不足时必须写清缺口、期望结果和触发后的买卖动作。"
            ),
        },
    )
    report_name = kline_report_name(as_of)
    write_source_log(report_name, sources, {"report_type": "kline"})
    return str(write_report_bundle(report_name, report)["pdf"])


def _kline_action_table(
    technical_rows: list[dict[str, object]],
    advice: list[dict[str, object]],
    as_of: str,
) -> str:
    advice_by_name = {str(row.get("Name")): row for row in advice}
    validation_by_symbol = latest_result_by_symbol(as_of)
    rows = []
    for row in technical_rows:
        advice_row = advice_by_name.get(str(row.get("name")), {})
        position = str(advice_row.get("Position") or row.get("Position") or "观察")
        validation = validation_by_symbol.get(str(row.get("symbol") or ""), {})
        volume = _kline_effective_volume(advice_row, row, validation)
        rows.append(
            {
                "name": row.get("name", ""),
                "position": position,
                "Volume": volume,
                "quality_score_pct": _kline_quality_score(row, validation) / 100,
                "persuasion": _kline_persuasion(row, validation),
                "signal_quality": row.get("quality", ""),
                "operation_conclusion": _kline_operation_conclusion(row, position, validation, volume),
                "basis": _compact(row.get("evidence", ""), 78),
                "risk": _kline_risk(row, validation),
            }
        )
    return table(
        rows,
        ["name", "position", "Volume", "quality_score_pct", "persuasion", "signal_quality", "operation_conclusion", "basis", "risk"],
        ["Name", "Position", "Volume", "复合质量分", "说服力", "信号质量", "操作结论", "依据", "风险点"],
    )


def _kline_effective_volume(
    advice_row: dict[str, object],
    technical: dict[str, object],
    validation: dict[str, str],
) -> float:
    position = str(advice_row.get("Position") or technical.get("Position") or "")
    if "账户待更新" in position:
        return 0.0
    if str(validation.get("risk_gate") or "") == "Blocked" and ("买入" in position or "补仓" in position or "承接" in position):
        return 0.0
    if str(technical.get("quality")) == "Low":
        return 0.0
    try:
        return max(0.0, float(advice_row.get("Volume") or 0.0))
    except (TypeError, ValueError):
        return 0.0


def _kline_quality_score(row: dict[str, object], validation: dict[str, str]) -> float:
    score = 20.0
    score += {"High": 34.0, "Medium": 22.0, "Low": 8.0}.get(str(row.get("quality")), 10.0)
    score += max(0.0, min(16.0, float(row.get("total_score") or 0) * 3.0 + 8.0))
    score += {"ContinueResearch": 18.0, "NeedsMoreEvidence": 9.0, "DataQualityReview": 3.0}.get(str(validation.get("validation_status") or ""), 5.0)
    if str(validation.get("risk_gate") or "") == "Pass":
        score += 12.0
    elif str(validation.get("risk_gate") or "") == "Blocked":
        score -= 8.0
    return round(max(0.0, min(100.0, score)), 3)


def _kline_persuasion(row: dict[str, object], validation: dict[str, str]) -> str:
    quality = str(row.get("quality") or "Unknown")
    status = str(validation.get("validation_status") or "ValidationQueued")
    gate = str(validation.get("risk_gate") or "Pending")
    if quality == "High" and gate == "Pass":
        return "高：技术信号、量能和验证闸门同向。"
    if quality == "Low":
        return "低：技术信号不一致，不能作为独立操作依据。"
    if gate == "Blocked":
        return f"中低：{_pfi_os_status_display(status)} 且风险闸门阻断，只能观察或暂停，Volume=0。"
    return f"中：技术信号{quality}，验证状态{_pfi_os_status_display(status)}，需等待样本确认。"


def _kline_operation_conclusion(
    row: dict[str, object],
    position: str,
    validation: dict[str, str],
    volume: float,
) -> str:
    if "账户待更新" in position:
        return "账户未确认，买卖均不执行；更新支付宝流水/持仓并重生成。"
    if volume <= 0 and ("买入" in position or "补仓" in position or "承接" in position):
        return "买入取消为可执行项，仅保留技术观察。"
    if volume <= 0 and ("卖出" in position or "减仓" in position or "降暴露" in position):
        return "卖出暂停为可执行项，仅保留风险观察。"
    if str(validation.get("risk_gate") or "") == "Blocked":
        return "风险闸门未通过，按等待/观察处理。"
    return str(row.get("final_action") or "继续观察")


def _kline_risk(row: dict[str, object], validation: dict[str, str]) -> str:
    status = str(validation.get("validation_status") or "ValidationQueued")
    gate = str(validation.get("risk_gate") or "Pending")
    return _compact(
        f"{_pfi_os_status_display(status)}/{_risk_gate_display(gate)}；失效条件：{row.get('if_failed_action', '样本不满足则取消方向。')}",
        78,
    )


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


def _compact(value: object, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "..."


def _signal_quality_matrix(rows: list[dict[str, object]]) -> str:
    return table(
        rows,
        ["symbol", "name", "kline_group", "Position", "quality", "final_action", "trend_score", "momentum_score", "volume_score", "total_score", "operation_rule"],
        ["代码", "名称", "K线分组", "Position", "信号质量", "明确操作", "趋势分", "动能分", "量能分", "总分", "执行规则"],
    )


def _training_answer_matrix(rows: list[dict[str, object]]) -> str:
    return table(
        rows,
        ["symbol", "name", "training_answer", "thought_process", "sample_to_wait", "expected_result", "if_confirmed_action", "if_failed_action"],
        ["代码", "名称", "训练题答案", "分析逻辑/思考过程", "等待样本", "期望结果", "满足时操作", "不满足时操作"],
    )


def _evidence_gap_actions(rows: list[dict[str, object]], as_of: str) -> str:
    validation_by_symbol = latest_result_by_symbol(as_of)
    output = []
    for row in rows:
        validation = validation_by_symbol.get(str(row.get("symbol")), {})
        status = str(validation.get("validation_status") or "ValidationQueued")
        output.append(
            {
                "symbol": row.get("symbol", ""),
                "name": row.get("name", ""),
                "status": _pfi_os_status_display(status),
                "needed": _needed_evidence(status, row, validation),
                "why": _why_evidence_needed(status, validation),
                "operation": _operation_for_evidence_status(row, status),
            }
        )
    return table(
        output,
        ["symbol", "name", "status", "needed", "why", "operation"],
        ["代码", "名称", "验证状态", "还需要的证据", "原因", "当前操作行为"],
    )


def _counter_action_matrix(rows: list[dict[str, object]]) -> str:
    output = []
    for row in rows:
        output.append(
            {
                "symbol": row.get("symbol", ""),
                "name": row.get("name", ""),
                "counter": _counter_case(row),
                "evidence": row.get("sample_to_wait", ""),
                "conclusion": _counter_conclusion(row),
                "action": row.get("if_failed_action", ""),
            }
        )
    return table(
        output,
        ["symbol", "name", "counter", "evidence", "conclusion", "action"],
        ["代码", "名称", "反方情景", "验证样本", "明确结论", "触发后操作"],
    )


def _technical_view(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "- K线结论：缺少可用历史行情，不能生成技术判断。"
    high = [row for row in rows if row.get("quality") == "High"]
    medium = [row for row in rows if row.get("quality") == "Medium"]
    low = [row for row in rows if row.get("quality") == "Low"]
    buy = [row for row in rows if "买入" in str(row.get("Position"))]
    sell = [row for row in rows if "卖出" in str(row.get("Position"))]
    return (
        f"- 技术结论：高质量信号 {len(high)} 个，中质量 {len(medium)} 个，低质量 {len(low)} 个。\n"
        f"- 操作结论：买入方向 {len(buy)} 个，卖出方向 {len(sell)} 个；低质量信号必须降额或观望。\n"
        "- 分析逻辑：先看趋势是否站上 MA20/MA60，再看 MACD/RSI/KDJ 是否同向，最后用成交量确认。若三者不一致，不允许用单一K线直接扩大 Volume。"
    )


def _selection_summary(
    selected: list[dict[str, object]],
    advice: list[dict[str, object]],
    technical_rows: list[dict[str, object]],
) -> str:
    advice_by_name = {str(row["Name"]): row for row in advice}
    technical_by_symbol = {str(row.get("symbol")): row for row in technical_rows}
    rows = []
    for item in selected:
        advice_row = advice_by_name.get(str(item["name"]), {})
        technical = technical_by_symbol.get(str(item.get("symbol")), {})
        rows.append(
            {
                "symbol": item["symbol"],
                "name": item["name"],
                "kline_group": item.get("kline_group", _fallback_kline_group(str(advice_row.get("Position", "观察")))),
                "Position": advice_row.get("Position", "观察"),
                "quality": technical.get("quality", "待计算"),
                "technical_evidence": technical.get("evidence", "缺少历史K线证据"),
                "sample_to_wait": technical.get("sample_to_wait", "等待收盘价、成交量和动能同步确认"),
                "failure_action": technical.get("if_failed_action", "不满足样本则取消方向，改观望"),
                "final_action": technical.get("final_action", "观望"),
                "volume_gate": _kline_volume_gate(advice_row, technical),
            }
        )
    return table(
        rows,
        ["symbol", "name", "kline_group", "Position", "quality", "technical_evidence", "sample_to_wait", "failure_action", "final_action", "volume_gate"],
        ["代码", "名称", "K线研究分组", "Position", "信号质量", "核心技术证据", "等待样本", "失效条件", "明确操作", "Volume闸门"],
    )


def _kline_volume_gate(advice_row: dict[str, object], technical: dict[str, object]) -> str:
    position = str(advice_row.get("Position") or "")
    volume = advice_row.get("Volume", advice_row.get("volume", "0.000%"))
    amount = advice_row.get("suggested_amount", advice_row.get("建议金额", "0.00"))
    if "账户待更新" in position:
        return "账户未确认：Volume=0，建议金额=0；更新支付宝流水/持仓并重生成前不执行。"
    if str(technical.get("quality")) == "Low":
        return "低质量信号：Volume必须降为0或观望，不允许按单一K线执行。"
    return f"最高Volume={volume}；参考金额={amount}；仍受支付宝15:00收盘价规则约束。"


def _fallback_kline_group(position: str) -> str:
    if "买入" in position or "承接" in position or "低仓位" in position:
        return "建议买入技术候选"
    if "卖出" in position or "减仓" in position or "减暴露" in position or "降暴露" in position:
        return "建议卖出技术候选"
    return "中性观望候选"


def _needed_evidence(status: str, row: dict[str, object], validation: dict[str, str]) -> str:
    if status == "DataQualityReview":
        return "补齐60条以上历史样本、当天收盘价、成交额、来源一致性。"
    if status == "NeedsMoreEvidence":
        return f"{row.get('sample_to_wait', '')}；同时需要风险闸门从阻断变为通过。"
    return "保持现有证据链，继续监控失效条件。"


def _why_evidence_needed(status: str, validation: dict[str, str]) -> str:
    if status == "DataQualityReview":
        return f"当前样本 {validation.get('sample_rows', '未知')} 条，不能支撑统计判断。"
    if status == "NeedsMoreEvidence":
        return str(validation.get("conclusion") or "PFIOS风险闸门未通过或稳定性不足。")
    return "验证未否定当前方向。"


def _operation_for_evidence_status(row: dict[str, object], status: str) -> str:
    action = str(row.get("Position", ""))
    if "账户待更新" in action:
        return "账户未更新，当前验证只保留研究方向；Volume为0，更新支付宝流水/持仓并重生成报告前不执行。"
    if status == "DataQualityReview":
        return "观望，不新增操作；已有待确认订单继续等待。"
    if status == "NeedsMoreEvidence":
        if "买入" in action:
            return "证据不足，买入不进入执行；Volume=0，补足样本、账户和PFIOS验证后重算。"
        if "卖出" in action:
            return "证据不足，卖出仅保留风险观察；账户和趋势确认前Volume=0。"
        return "继续观望，等待样本满足。"
    return str(row.get("operation_rule") or "按当前明确操作执行。")


def _counter_case(row: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    if "买入" in action:
        return "这不是低吸机会，而是趋势性下跌或弱反弹。"
    if "卖出" in action:
        return "这不是卖点，而是真实趋势突破。"
    return "当前K线没有方向，只是区间内噪音。"


def _counter_conclusion(row: dict[str, object]) -> str:
    action = str(row.get("Position", ""))
    quality = str(row.get("quality", ""))
    if "账户待更新" in action:
        if "买入" in action:
            return "等待账户确认；当前买入动作取消为可执行项，Volume 0。"
        if "卖出" in action:
            return "等待账户确认；当前卖出动作暂停为可执行项，Volume 0。"
        return "账户待更新，维持观望。"
    if "买入" in action and quality == "Low":
        return "推翻买入，改观望。"
    if "买入" in action:
        return "保留买入候选；账户、PFIOS和尾盘量价通过后重算Volume。"
    if "卖出" in action and quality == "High":
        return "卖出暂停，避免卖在突破初期。"
    if "卖出" in action:
        return "维持卖出。"
    return "维持观望。"
