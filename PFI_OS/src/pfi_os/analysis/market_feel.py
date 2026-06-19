from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pfi_os.indicators import atr, bollinger_bands, macd, rsi, sma, volatility


@dataclass(frozen=True)
class MarketFeelResult:
    symbol: str
    name: str
    market: str
    role: str
    latest_date: str
    close: float
    one_day_return: float
    five_day_return: float
    twenty_day_return: float
    sixty_day_return: float
    rsi14: float
    macd_hist: float
    price_vs_ma20: float
    price_vs_ma60: float
    bollinger_position: float
    atr14_ratio: float
    volatility20: float
    volume_ratio20: float
    max_drawdown60: float
    support20: float
    resistance20: float
    price_vs_support20: float
    price_vs_resistance20: float
    trend_state: str
    momentum_state: str
    risk_state: str
    volume_state: str
    market_feel_score: float
    training_conclusion: str
    explanation: str
    analysis: str
    practice_prompt: str
    data_points: int

    def to_row(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "role": self.role,
            "latest_date": self.latest_date,
            "close": self.close,
            "one_day_return": self.one_day_return,
            "five_day_return": self.five_day_return,
            "twenty_day_return": self.twenty_day_return,
            "sixty_day_return": self.sixty_day_return,
            "rsi14": self.rsi14,
            "macd_hist": self.macd_hist,
            "price_vs_ma20": self.price_vs_ma20,
            "price_vs_ma60": self.price_vs_ma60,
            "bollinger_position": self.bollinger_position,
            "atr14_ratio": self.atr14_ratio,
            "volatility20": self.volatility20,
            "volume_ratio20": self.volume_ratio20,
            "max_drawdown60": self.max_drawdown60,
            "support20": self.support20,
            "resistance20": self.resistance20,
            "price_vs_support20": self.price_vs_support20,
            "price_vs_resistance20": self.price_vs_resistance20,
            "trend_state": self.trend_state,
            "momentum_state": self.momentum_state,
            "risk_state": self.risk_state,
            "volume_state": self.volume_state,
            "market_feel_score": self.market_feel_score,
            "training_conclusion": self.training_conclusion,
            "explanation": self.explanation,
            "analysis": self.analysis,
            "practice_prompt": self.practice_prompt,
            "data_points": self.data_points,
        }


@dataclass(frozen=True)
class MarketFeelTrainingCase:
    result: MarketFeelResult
    answer_horizon: int
    hidden_start_date: str
    hidden_end_date: str
    actual_return: float
    actual_direction: str
    actual_return_interval: str
    technical_expected_direction: str
    technical_alignment: str
    pre_result_analysis: str
    post_result_review: str
    fairness_note: str

    def to_row(self) -> dict[str, object]:
        row = self.result.to_row()
        row.update(
            {
                "answer_horizon": self.answer_horizon,
                "hidden_start_date": self.hidden_start_date,
                "hidden_end_date": self.hidden_end_date,
                "actual_return": self.actual_return,
                "actual_direction": self.actual_direction,
                "actual_return_interval": self.actual_return_interval,
                "technical_expected_direction": self.technical_expected_direction,
                "technical_alignment": self.technical_alignment,
                "pre_result_analysis": self.pre_result_analysis,
                "post_result_review": self.post_result_review,
                "fairness_note": self.fairness_note,
            }
        )
        return row


def market_feel_from_bars(
    bars: pd.DataFrame,
    symbol: str,
    name: str = "",
    market: str = "",
    role: str = "训练对象",
) -> MarketFeelResult:
    data = _prepare_bars(bars, symbol)
    if len(data) < 60:
        raise ValueError(f"{symbol} 数据不足，盘感训练至少需要 60 个交易日。")

    close = data["close"]
    latest_close = float(close.iloc[-1])
    latest_date = data["datetime"].iloc[-1].date().isoformat()
    returns = close.pct_change().dropna()
    ma20 = sma(close, 20)
    ma60 = sma(close, 60)
    rsi14_series = rsi(close, 14).fillna(50.0)
    macd_frame = macd(close).fillna(0.0)
    bands = bollinger_bands(close, 20, 2.0)
    atr14_series = atr(data, 14).fillna(0.0)
    volatility20_series = volatility(close, 20).fillna(0.0)

    one_day_return = _period_return(close, 1)
    five_day_return = _period_return(close, 5)
    twenty_day_return = _period_return(close, 20)
    sixty_day_return = _period_return(close, 60)
    latest_ma20 = _last_valid(ma20, latest_close)
    latest_ma60 = _last_valid(ma60, latest_close)
    rsi14 = _last_valid(rsi14_series, 50.0)
    macd_hist = _last_valid(macd_frame["macd_hist"], 0.0)
    price_vs_ma20 = latest_close / latest_ma20 - 1 if latest_ma20 else 0.0
    price_vs_ma60 = latest_close / latest_ma60 - 1 if latest_ma60 else 0.0
    bollinger_position = _bollinger_position(latest_close, bands)
    atr14_ratio = _last_valid(atr14_series, 0.0) / latest_close if latest_close else 0.0
    volatility20 = _last_valid(volatility20_series, 0.0)
    volume_ratio20 = _volume_ratio20(data)
    max_drawdown60 = _max_drawdown(close.tail(60))
    support20 = float(data["low"].tail(20).min())
    resistance20 = float(data["high"].tail(20).max())
    price_vs_support20 = latest_close / support20 - 1 if support20 else 0.0
    price_vs_resistance20 = latest_close / resistance20 - 1 if resistance20 else 0.0

    trend_state = classify_trend(price_vs_ma20, price_vs_ma60, twenty_day_return, sixty_day_return)
    momentum_state = classify_momentum(rsi14, macd_hist, bollinger_position)
    risk_state = classify_risk(atr14_ratio, volatility20, max_drawdown60)
    volume_state = classify_volume(volume_ratio20, one_day_return, twenty_day_return)
    score = market_feel_score(
        price_vs_ma20=price_vs_ma20,
        price_vs_ma60=price_vs_ma60,
        twenty_day_return=twenty_day_return,
        sixty_day_return=sixty_day_return,
        rsi14=rsi14,
        macd_hist=macd_hist,
        bollinger_position=bollinger_position,
        atr14_ratio=atr14_ratio,
        volatility20=volatility20,
        volume_ratio20=volume_ratio20,
        max_drawdown60=max_drawdown60,
    )
    conclusion = market_feel_conclusion(score, trend_state, momentum_state, risk_state)
    explanation = market_feel_explanation(trend_state, momentum_state, risk_state, volume_state)
    analysis = market_feel_analysis(
        latest_close=latest_close,
        price_vs_ma20=price_vs_ma20,
        price_vs_ma60=price_vs_ma60,
        rsi14=rsi14,
        macd_hist=macd_hist,
        bollinger_position=bollinger_position,
        atr14_ratio=atr14_ratio,
        volatility20=volatility20,
        volume_ratio20=volume_ratio20,
        max_drawdown60=max_drawdown60,
        support20=support20,
        resistance20=resistance20,
        price_vs_support20=price_vs_support20,
        price_vs_resistance20=price_vs_resistance20,
    )
    practice_prompt = market_feel_practice_prompt(trend_state, momentum_state, risk_state)

    return MarketFeelResult(
        symbol=symbol,
        name=name or symbol,
        market=market,
        role=role,
        latest_date=latest_date,
        close=latest_close,
        one_day_return=one_day_return,
        five_day_return=five_day_return,
        twenty_day_return=twenty_day_return,
        sixty_day_return=sixty_day_return,
        rsi14=rsi14,
        macd_hist=macd_hist,
        price_vs_ma20=price_vs_ma20,
        price_vs_ma60=price_vs_ma60,
        bollinger_position=bollinger_position,
        atr14_ratio=atr14_ratio,
        volatility20=volatility20,
        volume_ratio20=volume_ratio20,
        max_drawdown60=max_drawdown60,
        support20=support20,
        resistance20=resistance20,
        price_vs_support20=price_vs_support20,
        price_vs_resistance20=price_vs_resistance20,
        trend_state=trend_state,
        momentum_state=momentum_state,
        risk_state=risk_state,
        volume_state=volume_state,
        market_feel_score=score,
        training_conclusion=conclusion,
        explanation=explanation,
        analysis=analysis,
        practice_prompt=practice_prompt,
        data_points=int(len(data)),
    )


def market_feel_training_case(
    bars: pd.DataFrame,
    symbol: str,
    name: str = "",
    market: str = "",
    role: str = "训练对象",
    answer_horizon: int = 5,
) -> MarketFeelTrainingCase:
    horizon = max(1, int(answer_horizon))
    data = _prepare_bars(bars, symbol)
    if len(data) < 60 + horizon:
        raise ValueError(f"{symbol} 数据不足，盘感训练至少需要 60 个可见交易日和 {horizon} 个答案交易日。")
    context = data.iloc[:-horizon].copy()
    hidden = data.iloc[-horizon:].copy()
    result = market_feel_from_bars(context, symbol=symbol, name=name, market=market, role=role)
    final_close = float(hidden["close"].iloc[-1])
    actual_return = final_close / result.close - 1 if result.close else 0.0
    actual_direction = market_feel_direction_from_return(actual_return)
    actual_return_interval = market_feel_return_interval(actual_return)
    expected_direction = market_feel_expected_direction(result)
    alignment = market_feel_alignment(expected_direction, actual_direction)
    pre_result_analysis = (
        f"事前技术分析：以下判断只使用截至 {result.latest_date} 的已知价格、成交量和指标，不读取随后 {horizon} 个交易日结果。"
        f"{result.analysis}"
    )
    post_result_review = market_feel_post_result_review(result, actual_direction, actual_return, expected_direction, alignment)
    fairness_note = (
        "训练说明：答案揭示后的复盘只比较事前技术判断与实际走势差异，不能倒推当时不存在的技术理由；"
        "若需要解释技术面失效，必须补充新闻、财报、估值、资金流、宏观、政策或行业相对强弱等独立证据。"
    )
    return MarketFeelTrainingCase(
        result=result,
        answer_horizon=horizon,
        hidden_start_date=hidden["datetime"].iloc[0].date().isoformat(),
        hidden_end_date=hidden["datetime"].iloc[-1].date().isoformat(),
        actual_return=float(actual_return),
        actual_direction=actual_direction,
        actual_return_interval=actual_return_interval,
        technical_expected_direction=expected_direction,
        technical_alignment=alignment,
        pre_result_analysis=pre_result_analysis,
        post_result_review=post_result_review,
        fairness_note=fairness_note,
    )


def market_feel_indicator_rows(result: MarketFeelResult) -> list[dict[str, str]]:
    return [
        _indicator_row("趋势", "1日涨跌", result.one_day_return, "percent", "最新一个交易日的价格变化，用来观察短线冲击。"),
        _indicator_row("趋势", "20日涨跌", result.twenty_day_return, "percent", "约一个月趋势强弱，和 MA20 一起判断短期结构。"),
        _indicator_row("趋势", "60日涨跌", result.sixty_day_return, "percent", "约一个季度趋势强弱，判断中期方向是否配合。"),
        _indicator_row("趋势", "相对 MA20", result.price_vs_ma20, "percent", "价格在 MA20 上方说明短期结构偏强，在下方说明短期承压。"),
        _indicator_row("趋势", "相对 MA60", result.price_vs_ma60, "percent", "价格在 MA60 上方说明中期结构偏强，在下方说明中期承压。"),
        _indicator_row("动能", "RSI14", result.rsi14, "number", "高于 70 容易拥挤，低于 30 容易低迷；需要结合趋势和成交判断。"),
        _indicator_row("动能", "MACD 柱", result.macd_hist, "number", "柱体为正说明短期动能偏强，为负说明动能偏弱。"),
        _indicator_row("动能", "Bollinger 位置", result.bollinger_position, "number", "0 接近下轨，1 接近上轨；越靠近两端越要关注回归或突破。"),
        _indicator_row("风险", "ATR14/价格", result.atr14_ratio, "percent", "衡量近 14 日平均波动幅度占价格比例，越高说明短线扰动越大。"),
        _indicator_row("风险", "20日年化波动", result.volatility20, "percent", "衡量近 20 日收益率波动，越高说明结论不确定性越高。"),
        _indicator_row("风险", "60日最大回撤", result.max_drawdown60, "percent", "近 60 日从高点到低点的最大跌幅，用来识别压力强度。"),
        _indicator_row("量价", "成交量比", result.volume_ratio20, "number", "最新成交量相对 20 日均量，>1 表示放量，<1 表示缩量。"),
        _indicator_row("结构", "20日支撑", result.support20, "number", "近 20 日低点区域，用于观察价格离近期需求区有多远。"),
        _indicator_row("结构", "20日压力", result.resistance20, "number", "近 20 日高点区域，用于观察价格距离近期供给区有多远。"),
        _indicator_row("结构", "距支撑", result.price_vs_support20, "percent", "价格相对近 20 日低点的距离；距离越近，越需要看跌破或企稳证据。"),
        _indicator_row("结构", "距压力", result.price_vs_resistance20, "percent", "价格相对近 20 日高点的距离；接近 0 表示逼近近期压力或突破位置。"),
    ]


def market_feel_chart_frame(bars: pd.DataFrame) -> pd.DataFrame:
    data = _prepare_bars(bars, "训练对象")
    close = data["close"]
    data["ma20"] = sma(close, 20)
    data["ma60"] = sma(close, 60)
    data["support20"] = data["low"].rolling(20).min()
    data["resistance20"] = data["high"].rolling(20).max()
    band_frame = bollinger_bands(close, 20, 2.0)
    data["bb_upper"] = band_frame["bb_upper"]
    data["bb_lower"] = band_frame["bb_lower"]
    data["rsi14"] = rsi(close, 14)
    macd_frame = macd(close)
    data["macd"] = macd_frame["macd"]
    data["macd_signal"] = macd_frame["macd_signal"]
    data["macd_hist"] = macd_frame["macd_hist"]
    return data.tail(260).reset_index(drop=True)


def classify_trend(price_vs_ma20: float, price_vs_ma60: float, twenty_day_return: float, sixty_day_return: float) -> str:
    if price_vs_ma20 > 0.02 and price_vs_ma60 > 0.04 and twenty_day_return > 0 and sixty_day_return > 0:
        return "多头结构"
    if price_vs_ma20 > 0 and twenty_day_return > 0:
        return "短期改善"
    if price_vs_ma20 < -0.02 and price_vs_ma60 < -0.04 and twenty_day_return < 0 and sixty_day_return < 0:
        return "空头结构"
    if price_vs_ma20 < 0 and twenty_day_return < 0:
        return "短期承压"
    return "震荡结构"


def classify_momentum(rsi14: float, macd_hist: float, bollinger_position: float) -> str:
    if rsi14 >= 75 or bollinger_position >= 1.05:
        return "动能拥挤"
    if rsi14 <= 25 or bollinger_position <= -0.05:
        return "动能低迷"
    if rsi14 >= 58 and macd_hist > 0:
        return "动能偏强"
    if rsi14 <= 42 and macd_hist < 0:
        return "动能偏弱"
    return "动能中性"


def classify_risk(atr14_ratio: float, volatility20: float, max_drawdown60: float) -> str:
    if max_drawdown60 <= -0.18 or volatility20 >= 0.42 or atr14_ratio >= 0.045:
        return "风险升温"
    if max_drawdown60 <= -0.10 or volatility20 >= 0.30 or atr14_ratio >= 0.03:
        return "风险偏高"
    return "风险平稳"


def classify_volume(volume_ratio20: float, one_day_return: float, twenty_day_return: float) -> str:
    if volume_ratio20 >= 1.35 and one_day_return > 0 and twenty_day_return >= 0:
        return "放量确认"
    if volume_ratio20 >= 1.35 and one_day_return < 0:
        return "放量承压"
    if volume_ratio20 <= 0.65:
        return "缩量观望"
    return "量能正常"


def market_feel_score(
    *,
    price_vs_ma20: float,
    price_vs_ma60: float,
    twenty_day_return: float,
    sixty_day_return: float,
    rsi14: float,
    macd_hist: float,
    bollinger_position: float,
    atr14_ratio: float,
    volatility20: float,
    volume_ratio20: float,
    max_drawdown60: float,
) -> float:
    raw = 50.0
    raw += _clip(price_vs_ma20 * 100, -12, 12) * 1.0
    raw += _clip(price_vs_ma60 * 100, -18, 18) * 0.65
    raw += _clip(twenty_day_return * 100, -18, 18) * 0.75
    raw += _clip(sixty_day_return * 100, -28, 28) * 0.35
    raw += _clip(rsi14 - 50, -30, 30) * 0.28
    raw += 4.0 if macd_hist > 0 else -4.0 if macd_hist < 0 else 0.0
    raw -= max(0.0, bollinger_position - 1.0) * 8.0
    raw -= max(0.0, -bollinger_position) * 8.0
    raw -= _clip((atr14_ratio - 0.025) * 100, 0, 8) * 1.3
    raw -= _clip((volatility20 - 0.28) * 100, 0, 30) * 0.25
    raw += _clip((volume_ratio20 - 1.0) * 10, -4, 4) if twenty_day_return >= 0 else -_clip((volume_ratio20 - 1.0) * 10, 0, 4)
    raw += _clip(max_drawdown60 * 100, -25, 0) * 0.28
    return float(round(_clip(raw, 0, 100), 2))


def market_feel_conclusion(score: float, trend_state: str, momentum_state: str, risk_state: str) -> str:
    if risk_state == "风险升温":
        return "研究结论：风险优先。先判断下跌是否来自基本面、流动性或外部冲击，再降低对单一技术信号的信任度。"
    if score >= 72 and momentum_state == "动能拥挤":
        return "研究结论：结构偏强但短线拥挤。训练重点是区分趋势延续和高位钝化，不把强势本身当成充分证据。"
    if score >= 66:
        return "研究结论：技术结构偏强。训练重点是验证趋势、量能和回撤是否互相支持。"
    if score <= 30 and trend_state in {"空头结构", "短期承压"}:
        return "研究结论：技术结构偏弱。训练重点是识别风险释放是否结束，以及是否存在反弹失败。"
    if momentum_state == "动能低迷":
        return "研究结论：短期低迷。训练重点是区分恐慌错杀、正常回撤和趋势恶化。"
    return "研究结论：证据中性。当前更适合练习读图和记录假设，不宜把单个指标放大为高置信结论。"


def market_feel_explanation(trend_state: str, momentum_state: str, risk_state: str, volume_state: str) -> str:
    return (
        f"讲解：先看趋势结构，当前为{trend_state}；再看 RSI、MACD 和 Bollinger 的动能位置，当前为{momentum_state}；"
        f"第三步看 ATR、波动和回撤，当前为{risk_state}；最后用成交量确认价格变化，当前为{volume_state}。"
    )


def market_feel_analysis(
    *,
    latest_close: float,
    price_vs_ma20: float,
    price_vs_ma60: float,
    rsi14: float,
    macd_hist: float,
    bollinger_position: float,
    atr14_ratio: float,
    volatility20: float,
    volume_ratio20: float,
    max_drawdown60: float,
    support20: float,
    resistance20: float,
    price_vs_support20: float,
    price_vs_resistance20: float,
) -> str:
    trend_reading = _trend_reading(price_vs_ma20, price_vs_ma60)
    momentum_reading = _momentum_reading(rsi14, macd_hist, bollinger_position)
    risk_reading = _risk_reading(atr14_ratio, volatility20, max_drawdown60)
    volume_reading = _volume_reading(volume_ratio20)
    return (
        f"分析：最新收盘价 {latest_close:,.2f}，相对 MA20 {price_vs_ma20:.2%}，相对 MA60 {price_vs_ma60:.2%}；"
        f"RSI14 为 {rsi14:.2f}，MACD 柱为 {macd_hist:.4f}，Bollinger 位置为 {bollinger_position:.2f}；"
        f"ATR14/价格 {atr14_ratio:.2%}，20日年化波动 {volatility20:.2%}，成交量比 {volume_ratio20:.2f}，60日最大回撤 {max_drawdown60:.2%}；"
        f"20日支撑 {support20:,.2f}，20日压力 {resistance20:,.2f}，距支撑 {price_vs_support20:.2%}，距压力 {price_vs_resistance20:.2%}。"
        f"技术判断：{trend_reading}；{momentum_reading}；{risk_reading}；{volume_reading}。"
    )


def market_feel_practice_prompt(trend_state: str, momentum_state: str, risk_state: str) -> str:
    return (
        f"训练题：先独立判断这张图更像趋势延续、震荡修复还是风险释放；"
        f"再用三个证据复核：趋势={trend_state}，动能={momentum_state}，风险={risk_state}。"
    )


def market_feel_direction_from_return(value: float, neutral_threshold: float = 0.005) -> str:
    if value > neutral_threshold:
        return "上涨"
    if value < -neutral_threshold:
        return "下跌"
    return "震荡"


def market_feel_return_interval(value: float) -> str:
    if value <= -0.05:
        return "-5.00%以下"
    if value <= -0.02:
        return "-5.00%至-2.00%"
    if value < 0:
        return "-2.00%至0.00%"
    if value < 0.02:
        return "0.00%至2.00%"
    if value < 0.05:
        return "2.00%至5.00%"
    return "5.00%以上"


def market_feel_expected_direction(result: MarketFeelResult) -> str:
    if result.risk_state == "风险升温":
        return "震荡"
    if result.market_feel_score >= 64 and result.trend_state in {"多头结构", "短期改善"} and result.momentum_state != "动能拥挤":
        return "上涨"
    if result.market_feel_score <= 38 and result.trend_state in {"空头结构", "短期承压"}:
        return "下跌"
    if result.trend_state == "多头结构" and result.momentum_state in {"动能偏强", "动能中性"}:
        return "上涨"
    if result.trend_state == "空头结构" and result.momentum_state in {"动能偏弱", "动能中性"}:
        return "下跌"
    return "震荡"


def market_feel_alignment(expected_direction: str, actual_direction: str) -> str:
    if expected_direction == "震荡":
        return "技术面中性，不做方向一致性判定"
    if expected_direction == actual_direction:
        return "技术面与实际方向一致"
    return "技术面与实际方向不一致"


def market_feel_post_result_review(
    result: MarketFeelResult,
    actual_direction: str,
    actual_return: float,
    expected_direction: str,
    alignment: str,
) -> str:
    base = (
        f"结果复盘：随后区间实际为{actual_direction}，区间收益率 {actual_return:.2%}；"
        f"事前技术面倾向为{expected_direction}，一致性为：{alignment}。"
    )
    if alignment == "技术面与实际方向一致":
        return (
            base
            +
            "这只说明本次样本中趋势、动能、风险和量价证据与随后走势同向，并不证明指标长期有效。"
            "下一步应检查同类形态在更多样本、不同市场和扣除成本后的稳定性。"
        )
    if alignment == "技术面与实际方向不一致":
        return (
            base
            +
            "不一致时不能倒推技术理由。应按独立证据补查四类原因："
            "事实面包括公告、财报、政策、行业消息和突发事件；"
            "基本面包括盈利预期、现金流、竞争格局和产业周期；"
            "价值面包括估值分位、风险溢价和预期收益变化；"
            "交易面包括资金流、流动性、指数权重、成交拥挤、汇率和市场整体风险偏好。"
            "若这些证据缺失，应把结论降级为需要更多证据。"
        )
    return (
        base
        +
        "技术面本身给出的是中性或冲突信号，因此训练重点不是判断对错，而是识别哪些证据不足。"
        "后续应优先补充基本面、估值、资金流和市场环境证据。"
    )


def _prepare_bars(bars: pd.DataFrame, symbol: str) -> pd.DataFrame:
    required = {"datetime", "close"}
    missing = required.difference(bars.columns)
    if bars.empty or missing:
        raise ValueError(f"{symbol} 没有可用于盘感训练的行情数据。")
    data = bars.copy()
    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        if column not in data.columns:
            data[column] = data["close"] if column != "volume" else 0.0
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["datetime", "close"]).sort_values("datetime")
    data["open"] = data["open"].fillna(data["close"])
    data["high"] = data["high"].fillna(data[["open", "close"]].max(axis=1))
    data["low"] = data["low"].fillna(data[["open", "close"]].min(axis=1))
    data["volume"] = data["volume"].fillna(0.0)
    return data


def _period_return(close: pd.Series, periods: int) -> float:
    if len(close) <= periods:
        return 0.0
    base = float(close.iloc[-periods - 1])
    return float(close.iloc[-1] / base - 1) if base else 0.0


def _last_valid(series: pd.Series, default: float = 0.0) -> float:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    if valid.empty:
        return float(default)
    return float(valid.iloc[-1])


def _bollinger_position(latest_close: float, bands: pd.DataFrame) -> float:
    upper = _last_valid(bands["bb_upper"], latest_close)
    lower = _last_valid(bands["bb_lower"], latest_close)
    width = upper - lower
    if abs(width) < 1e-12:
        return 0.5
    return float((latest_close - lower) / width)


def _volume_ratio20(data: pd.DataFrame) -> float:
    if "volume" not in data.columns or data["volume"].tail(20).mean() <= 0:
        return 0.0
    return float(data["volume"].iloc[-1] / data["volume"].tail(20).mean())


def _max_drawdown(close: pd.Series) -> float:
    if close.empty:
        return 0.0
    peak = close.cummax()
    drawdown = close / peak - 1
    return float(drawdown.min())


def _indicator_row(module: str, indicator: str, value: float, value_type: str, explanation: str) -> dict[str, str]:
    formatted = f"{float(value):.2%}" if value_type == "percent" else f"{float(value):,.2f}"
    return {"模块": module, "指标": indicator, "数值": formatted, "说明": explanation}


def _trend_reading(price_vs_ma20: float, price_vs_ma60: float) -> str:
    if price_vs_ma20 > 0 and price_vs_ma60 > 0:
        return "价格同时站上 MA20 和 MA60，短中期结构偏强"
    if price_vs_ma20 < 0 and price_vs_ma60 < 0:
        return "价格同时低于 MA20 和 MA60，短中期结构承压"
    if price_vs_ma20 > 0 > price_vs_ma60:
        return "价格修复到 MA20 上方但仍低于 MA60，属于短线改善、中期未确认"
    if price_vs_ma20 < 0 < price_vs_ma60:
        return "价格跌破 MA20 但仍高于 MA60，属于短线回落、中期尚未破坏"
    return "价格贴近均线，趋势证据不强"


def _momentum_reading(rsi14: float, macd_hist: float, bollinger_position: float) -> str:
    if rsi14 >= 70 or bollinger_position >= 1.0:
        return "RSI 或 Bollinger 显示短线偏拥挤，需要警惕高位钝化和回撤"
    if rsi14 <= 30 or bollinger_position <= 0.0:
        return "RSI 或 Bollinger 显示短线偏低迷，需要区分错杀和趋势恶化"
    if macd_hist > 0:
        return "MACD 柱为正，短期动能正在改善"
    if macd_hist < 0:
        return "MACD 柱为负，短期动能仍偏弱"
    return "动能读数接近中性，单独解释力有限"


def _risk_reading(atr14_ratio: float, volatility20: float, max_drawdown60: float) -> str:
    if max_drawdown60 <= -0.18 or volatility20 >= 0.42 or atr14_ratio >= 0.045:
        return "ATR、波动或回撤提示风险升温，技术结论需要降级处理"
    if max_drawdown60 <= -0.10 or volatility20 >= 0.30 or atr14_ratio >= 0.03:
        return "风险指标偏高，适合继续观察确认而不是提高结论置信度"
    return "波动和回撤处于相对可控区间，技术结构的可读性较好"


def _volume_reading(volume_ratio20: float) -> str:
    if volume_ratio20 >= 1.35:
        return "成交量明显放大，价格变化更需要结合方向判断是确认还是承压"
    if volume_ratio20 <= 0.65:
        return "成交量偏低，当前价格信号的确认力度不足"
    return "成交量接近常态，未给出明显额外确认或否定"


def _clip(value: float, low: float, high: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return max(low, min(high, float(value)))
