from __future__ import annotations


def build_trading_advice(
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    signals: list[dict[str, object]],
    positions: list[dict[str, object]],
    holdings: list[dict[str, str]] | None = None,
    pending_orders: list[dict[str, str]] | None = None,
    account_summary: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    factor_by_symbol = {str(item["symbol"]): item for item in factors}
    holding_by_symbol = {str(item.get("symbol", "")): item for item in holdings or []}
    pending_by_symbol = _pending_index(pending_orders or [], "symbol")
    event_text = "；".join(item["title"] for item in events)
    advice_rows: list[dict[str, object]] = []

    for position in positions:
        symbol = str(position["symbol"])
        factor = factor_by_symbol.get(symbol, {})
        signal = str(position.get("internal_signal", "watch"))
        weight = float(position.get("risk_adjusted_weight", 0))
        momentum = float(factor.get("momentum_5d", 0))
        volume_ratio = float(factor.get("volume_ratio_5d", 0))
        pe = float(factor.get("pe", 0))
        name = str(position["name"])
        holding = _match_holding(symbol, name, holding_by_symbol, holdings or [])
        current_weight, current_weight_basis = _holding_weight(holding, account_summary or {})
        holding_return = _holding_return(holding)
        holding_amount = _holding_amount(holding)
        holding_return_amount = _holding_return_amount(holding, holding_amount, holding_return)
        decision = _alipay_decision(
            signal,
            weight,
            momentum,
            volume_ratio,
            current_weight,
            holding_return,
            str(position.get("asset_class", "")),
            name,
            symbol,
        )
        pending = _match_pending(symbol, name, pending_by_symbol, pending_orders or [])
        decision = _apply_pending_order_guard(decision, pending)
        decision = _apply_account_update_guard(decision, account_summary or {})

        confidence = _confidence(signal, momentum, volume_ratio, pe)
        advice_rows.append(
            {
                "symbol": symbol,
                "Name": name,
                "name": name,
                "industry": position["industry"],
                "Position": decision["action"],
                "action": decision["action"],
                "Volume": decision["volume"],
                "suggested_weight": decision["volume"],
                "holding_amount": holding_amount,
                "holding_return_amount": holding_return_amount,
                "current_weight": current_weight,
                "current_weight_basis": current_weight_basis,
                "holding_return_pct": holding_return,
                "pending_order_amount": pending.get("amount", 0.0),
                "pending_order_side": pending.get("side", ""),
                "account_update_status": (account_summary or {}).get("alipay_update_status", ""),
                "trade_deadline": "15:00 前按当日收盘价估算；15:00 后顺延下一交易日",
                "confidence": confidence,
                "entry_condition": decision["entry_condition"],
                "exit_condition": decision["exit_condition"],
                "risk_note": _risk_note(pe, event_text, decision["action"], momentum, current_weight, holding_return),
                "evidence": position.get("reason", ""),
                "volume_basis": decision.get("volume_basis", ""),
            }
        )
    return advice_rows


def _alipay_decision(
    signal: str,
    target_weight: float,
    momentum: float,
    volume_ratio: float,
    current_weight: float,
    holding_return: float,
    asset_class: str,
    name: str = "",
    symbol: str = "",
) -> dict[str, object]:
    if asset_class == "FX":
        return _decision("观望-汇率背景", 0.0, "汇率只用于判断资产换算风险，不生成账户操作结论。", "汇率波动影响海外资产净值。")
    if asset_class == "Index" and not _is_user_tradable_index(name, symbol):
        return _decision("观望-指数背景", 0.0, "指数用于市场背景，不直接生成支付宝账户操作结论。", "指数与可交易 ETF 可能存在跟踪误差。")

    # Alipay confirms before-15:00 fund orders at the same-day close, so size rules
    # are expressed as capped operation ranges instead of market orders.
    if momentum >= 0.018 and current_weight > 0:
        sell_size, basis = _sell_volume(
            momentum=momentum,
            volume_ratio=volume_ratio,
            current_weight=current_weight,
            holding_return=holding_return,
        )
        return _decision(
            "建议卖出-上涨减仓",
            sell_size,
            f"当日上涨 {momentum * 100:.3f}%，且已有持仓；按收盘价确认规则，优先考虑把浮盈或过高现仓部分兑现。Volume依据：{basis}",
            "若上涨来自放量突破而非脉冲，过早卖出可能错失趋势延续；尾盘放量站稳且 PFIOS 风险闸门未否定时暂停卖出并重算。",
            basis,
        )

    if momentum <= -0.018:
        buy_size, basis = _buy_volume(
            target_weight=target_weight,
            momentum=momentum,
            volume_ratio=volume_ratio,
            current_weight=current_weight,
            holding_return=holding_return,
        )
        return _decision(
            "建议买入-下跌承接",
            buy_size,
            f"当日下跌 {momentum * 100:.3f}%，符合你按收盘价下跌时分批补仓的习惯；金额必须受现仓、收益率和待确认订单约束。Volume依据：{basis}",
            "若下跌伴随放量和负面事件，买入假设失效；跌破关键均线时停止把该线索用于决策。",
            basis,
        )

    if signal == "buy" and target_weight > 0 and current_weight < 0.06 and momentum < 0.018:
        gap = max(0.0, min(target_weight, 0.08) - current_weight)
        buy_size = round(max(0.005, min(gap * 0.45, 0.035)), 6)
        basis = (
            f"目标权重{target_weight * 100:.3f}%，现仓{current_weight * 100:.3f}%，"
            f"补足缺口的45%，单次上限3.500%。"
        )
        return _decision(
            "建议买入-低仓位补足",
            buy_size,
            f"趋势偏强但未过热，且当前持仓偏低；可按小额补足方式提高有效暴露。Volume依据：{basis}",
            "若尾盘涨幅扩大到过热区间，取消当日买入建议并等待下一次回落确认。",
            basis,
        )

    if signal == "avoid" and current_weight > 0:
        sell_size = round(min(current_weight, max(0.01, current_weight * 0.35), 0.04), 6)
        basis = f"现仓{current_weight * 100:.3f}%，转弱降风险按现仓35%计算，单次上限4.000%。"
        return _decision(
            "建议卖出-转弱降仓",
            sell_size,
            f"价格转弱且已有持仓，列入降低风险暴露观察。Volume依据：{basis}",
            "若快速修复，保留重新评估机会；不把单日噪音写成结论。",
            basis,
        )

    return _decision(
        "观望",
        0.0,
        "涨跌幅、持仓收益率和当前现仓没有形成明确研究结论。",
        "维持观察本身是风险控制；等待收盘价方向和后续证据更清晰。",
    )


def _is_user_tradable_index(name: str, symbol: str) -> bool:
    text = f"{name} {symbol}"
    return any(token in text for token in ["中证银行", "科创50", "399986", "000688"])


def _buy_volume(
    target_weight: float,
    momentum: float,
    volume_ratio: float,
    current_weight: float,
    holding_return: float,
) -> tuple[float, str]:
    target_cap = min(max(target_weight, 0.02), 0.06)
    if current_weight >= 0.12:
        target_cap = min(target_cap, 0.02)
    drawdown_component = min(max(abs(momentum) - 0.018, 0.0) * 0.75, 0.025)
    loss_component = min(max(abs(min(holding_return, 0.0)) - 0.02, 0.0) * 0.35, 0.025)
    underweight_component = min(max(0.08 - current_weight, 0.0) * 0.30, 0.02)
    volume_penalty = 0.0
    if volume_ratio >= 1.8:
        volume_penalty = 0.02
    elif volume_ratio >= 1.25:
        volume_penalty = 0.01
    raw = 0.008 + drawdown_component + loss_component + underweight_component - volume_penalty
    volume = round(max(0.005, min(raw, target_cap)), 6)
    basis = (
        f"跌幅项{drawdown_component * 100:.3f}%、亏损项{loss_component * 100:.3f}%、"
        f"低仓项{underweight_component * 100:.3f}%、放量扣减{volume_penalty * 100:.3f}%、"
        f"目标/风险上限{target_cap * 100:.3f}%。"
    )
    return volume, basis


def _sell_volume(
    momentum: float,
    volume_ratio: float,
    current_weight: float,
    holding_return: float,
) -> tuple[float, str]:
    rise_component = min(max(momentum - 0.018, 0.0) * 0.70, 0.025)
    profit_component = min(max(holding_return - 0.02, 0.0) * 0.45, 0.035)
    concentration_component = min(max(current_weight - 0.08, 0.0) * 0.45, 0.025)
    breakout_penalty = 0.015 if volume_ratio >= 1.5 and momentum >= 0.035 else 0.0
    raw = 0.01 + rise_component + profit_component + concentration_component - breakout_penalty
    volume = round(max(0.005, min(raw, current_weight, 0.08)), 6)
    basis = (
        f"涨幅项{rise_component * 100:.3f}%、收益项{profit_component * 100:.3f}%、"
        f"集中度项{concentration_component * 100:.3f}%、突破扣减{breakout_penalty * 100:.3f}%、"
        f"现仓/单次上限{min(current_weight, 0.08) * 100:.3f}%。"
    )
    return volume, basis


def _decision(action: str, volume: float, entry: str, exit_condition: str, volume_basis: str = "") -> dict[str, object]:
    return {
        "action": action,
        "volume": round(volume, 6),
        "entry_condition": entry,
        "exit_condition": exit_condition,
        "volume_basis": volume_basis,
    }


def _apply_pending_order_guard(decision: dict[str, object], pending: dict[str, object]) -> dict[str, object]:
    if not pending:
        return decision
    side = str(pending.get("side", ""))
    amount = float(pending.get("amount", 0.0) or 0.0)
    action = str(decision.get("action", ""))
    if amount <= 0:
        return decision
    is_buy_action = any(token in action for token in ["买入", "补仓", "承接", "低仓位"])
    is_sell_action = any(token in action for token in ["卖出", "减仓", "减暴露", "降暴露"])
    if (is_buy_action and ("买" in side or "定投" in side)) or (is_sell_action and "卖" in side):
        return _decision(
            "等待确认",
            0.0,
            f"支付宝已有待确认{side}订单 {amount:.2f} 元；先等待确认份额、净值和手续费。",
            "确认后再根据真实持仓金额、收益率和可用现金重新判断。",
        )
    return decision


def _apply_account_update_guard(decision: dict[str, object], account_summary: dict[str, object]) -> dict[str, object]:
    if not account_summary.get("alipay_update_missing") and not account_summary.get("alipay_execution_blocked"):
        return decision
    action = str(decision.get("action", ""))
    is_buy_action = any(token in action for token in ["买入", "补仓", "承接", "低仓位"])
    is_sell_action = any(token in action for token in ["卖出", "减仓", "减暴露", "降暴露"])
    if not is_buy_action and not is_sell_action:
        return decision
    direction = "买入" if is_buy_action else "卖出"
    missing_dates = ", ".join(str(item) for item in account_summary.get("alipay_missing_dates", []) if item) or "报告日"
    block_reason = str(account_summary.get("alipay_execution_block_reason") or f"{missing_dates} 支付宝流水/持仓未更新")
    original_entry = str(decision.get("entry_condition", ""))
    original_exit = str(decision.get("exit_condition", ""))
    return _decision(
        f"账户待更新-{direction}候选",
        0.0,
        f"今日支付宝流水/持仓未更新或未确认（{block_reason}）；保留{direction}研究方向，但本次可执行金额设为0。更新交易明细、持仓截图或CSV并确认后，需重新计算持仓金额、持有收益率、待确认订单和Volume。原研究依据：{original_entry}",
        f"账户更新确认前禁止按本报告执行实际{direction}。确认后若行情、持仓收益率、待确认订单和事件方向仍一致，再重新生成报告确认。原风险条件：{original_exit}",
    )


def _pending_index(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        raw_key = str(row.get(key, ""))
        index_key = _normalize_name(raw_key) if key == "name" else raw_key
        if not index_key:
            continue
        current = result.setdefault(index_key, {"amount": 0.0, "side": ""})
        current["amount"] = float(current.get("amount", 0.0)) + _safe_float(row.get("order_amount", 0))
        side = str(row.get("side", ""))
        if side and side not in str(current.get("side", "")):
            current["side"] = (str(current.get("side", "")) + "/" + side).strip("/")
    return result


def _match_holding(
    symbol: str,
    name: str,
    holding_by_symbol: dict[str, dict[str, str]],
    holdings: list[dict[str, str]],
) -> dict[str, str]:
    if symbol in holding_by_symbol:
        return holding_by_symbol[symbol]
    matches = _name_matches(name, holdings)
    if not matches:
        return {}
    return _combine_holdings(matches)


def _match_pending(
    symbol: str,
    name: str,
    pending_by_symbol: dict[str, dict[str, object]],
    pending_orders: list[dict[str, str]],
) -> dict[str, object]:
    if symbol in pending_by_symbol:
        return pending_by_symbol[symbol]
    matches = _name_matches(name, pending_orders)
    if not matches:
        return {}
    amount = sum(_safe_float(row.get("order_amount", 0)) for row in matches)
    sides = []
    for row in matches:
        side = str(row.get("side", ""))
        if side and side not in sides:
            sides.append(side)
    return {"amount": amount, "side": "/".join(sides)}


def _name_matches(target_name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    target = _normalize_name(target_name)
    exact = [row for row in rows if _normalize_name(str(row.get("name", "") or row.get("Name", ""))) == target]
    if exact:
        return exact
    target_core = _core_name(target)
    substring = [
        row
        for row in rows
        if _is_substring_match(target_core, _core_name(_normalize_name(str(row.get("name", "") or row.get("Name", "")))))
    ]
    if substring:
        return substring
    scored = []
    for row in rows:
        candidate = _core_name(_normalize_name(str(row.get("name", "") or row.get("Name", ""))))
        score = _name_similarity(target, candidate)
        if score >= 0.58:
            scored.append((score, row))
    if not scored:
        return []
    best = max(score for score, _ in scored)
    return [row for score, row in scored if score >= max(0.58, best - 0.05)]


def _combine_holdings(rows: list[dict[str, str]]) -> dict[str, str]:
    amount = sum(_holding_amount(row) for row in rows)
    return_amount = sum(_holding_return_amount(row, _holding_amount(row), _holding_return(row)) for row in rows)
    weight = sum(_holding_weight(row, {})[0] for row in rows)
    cost_basis = amount - return_amount
    return_pct = return_amount / cost_basis if cost_basis > 0 else 0.0
    return {
        "name": " / ".join(str(row.get("name", "") or row.get("Name", "")) for row in rows if row.get("name") or row.get("Name")),
        "amount": str(amount),
        "holding_return_amount": str(return_amount),
        "holding_return_pct": str(return_pct),
        "weight": str(weight),
    }


def _is_substring_match(target: str, candidate: str) -> bool:
    if not target or not candidate:
        return False
    return len(target) >= 2 and (target in candidate or candidate in target)


def _name_similarity(left: str, right: str) -> float:
    left_tokens = _bigrams(_core_name(left))
    right_tokens = _bigrams(_core_name(right))
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    return overlap / max(1, min(len(left_tokens), len(right_tokens)))


def _bigrams(value: str) -> set[str]:
    compact = value
    if len(compact) < 2:
        return {compact} if compact else set()
    return {compact[idx : idx + 2] for idx in range(len(compact) - 1)}


def _core_name(value: str) -> str:
    compact = value
    for token in [
        "易方达",
        "博时",
        "华夏",
        "天弘",
        "国泰",
        "南方",
        "华安",
        "摩根",
        "前海开源",
        "华泰柏瑞",
        "诺安",
        "中金",
        "基金",
        "联接",
        "ETF",
        "指数",
        "主题",
        "混合",
        "股票",
        "增强",
        "发起式",
        "精选",
        "灵活配置",
        "QDII",
        "(QDII)",
        "中证",
        "标普",
        "100",
        "500",
        "A",
        "C",
    ]:
        compact = compact.replace(token, "")
    return compact


def _holding_weight(holding: dict[str, str], account_summary: dict[str, object]) -> tuple[float, str]:
    for key in ["weight", "holding_weight", "position_pct", "position_weight"]:
        value = holding.get(key)
        if value not in {"", None}:
            parsed = _pct_or_float(value)
            if parsed > 0:
                return parsed, "支付宝持仓权重字段"
    amount = _holding_amount(holding)
    total = _safe_float(account_summary.get("total_holding_amount", 0))
    if amount > 0 and total > 0:
        label = str(account_summary.get("source_label") or "账户总金额")
        if str(account_summary.get("source_status")) != "confirmed_positions":
            label += "候选估算"
        return amount / total, f"持仓金额/账户总金额（{label}）"
    return 0.0, "无匹配持仓"


def _holding_return(holding: dict[str, str]) -> float:
    for key in ["holding_return_pct", "return_pct", "profit_pct", "gain_pct"]:
        value = holding.get(key)
        if value not in {"", None}:
            return _pct_or_float(value)
    return 0.0


def _holding_amount(holding: dict[str, str]) -> float:
    for key in ["amount", "holding_amount", "market_value", "position_amount"]:
        value = holding.get(key)
        if value not in {"", None}:
            return _safe_float(value)
    return 0.0


def _holding_return_amount(holding: dict[str, str], amount: float, return_pct: float) -> float:
    for key in ["holding_return_amount", "return_amount", "profit_amount", "gain_amount"]:
        value = holding.get(key)
        if value not in {"", None}:
            return _safe_float(value)
    return amount * return_pct / (1 + return_pct) if amount and return_pct > -1 else 0.0


def _pct_or_float(value: object) -> float:
    text = str(value).strip()
    if text.endswith("%"):
        return float(text[:-1]) / 100
    return float(text)


def _safe_float(value: object) -> float:
    try:
        return float(str(value).replace(",", "").replace("元", "").strip() or 0)
    except ValueError:
        return 0.0


def _normalize_name(value: str) -> str:
    return "".join(value.split()).upper()


def _confidence(signal: str, momentum: float, volume_ratio: float, pe: float) -> str:
    score = 0
    if signal == "buy":
        score += 2
    if momentum > 0.03:
        score += 1
    if volume_ratio > 1.1:
        score += 1
    if pe and pe > 40:
        score -= 1
    if score >= 3:
        return "中高"
    if score >= 1:
        return "中"
    return "低"


def _entry_condition(signal: str, momentum: float, volume_ratio: float) -> str:
    if signal == "buy":
        return f"延续强于自选池且成交量不低于近5日均量；当前涨跌线索 {momentum * 100:.3f}%，量能倍率 {volume_ratio:.3f}。"
    if signal == "avoid":
        return "短线弱于自选池，除非出现放量修复或明确正面事件，否则不参与。"
    return "当前未达到承接观察条件；若成交额进入自选池前列且价格转强，再加入候选池。"


def _risk_note(pe: float, event_text: str, action: str, momentum: float, current_weight: float, holding_return: float) -> str:
    notes = []
    if "账户待更新" in action:
        notes.append("账户更新风险：今日支付宝流水或持仓未更新/未确认，买卖候选只能作为研究方向，本次Volume归零，账户确认后必须重算。")
    if "买入" in action or "承接" in action or "低仓位" in action:
        notes.append("买入风险：若尾盘继续放量下跌、负面事件确认或待确认买单未完成，应取消买入并重新计算。")
    elif "卖出" in action or "减暴露" in action or "降暴露" in action:
        notes.append("卖出风险：若上涨由真实突破驱动，过早卖出会降低后续趋势收益。")
    else:
        notes.append("观察风险：等待可能错过单日机会，但可避免按无效价格追涨杀跌。")
    if current_weight > 0:
        notes.append(f"当前持仓约 {current_weight * 100:.3f}%，持有收益率约 {holding_return * 100:.3f}%。")
    if abs(momentum) > 0.04:
        notes.append("当日波动已较大，15:00 前提交任何账户操作都需防止情绪化追涨杀跌。")
    if pe > 40:
        notes.append("估值偏高，需控制研究权重和回撤风险。")
    if event_text:
        notes.append("事件催化使用新闻、公告和政府文件解读链路；若系统链路方向与当前买卖方向相反，则取消、暂停或改观望。")
    return " ".join(notes)
