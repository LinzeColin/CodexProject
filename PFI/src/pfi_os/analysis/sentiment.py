from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SentimentInstrument:
    symbol: str
    name: str
    market: str
    role: str = "观察对象"


@dataclass(frozen=True)
class SentimentResult:
    symbol: str
    name: str
    market: str
    role: str
    latest_date: str
    close: float
    one_day_return: float
    twenty_day_return: float
    rsi14: float
    price_vs_ma20: float
    volatility20: float
    max_drawdown60: float
    sentiment_score: float
    sentiment_state: str
    research_reading: str
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
            "twenty_day_return": self.twenty_day_return,
            "rsi14": self.rsi14,
            "price_vs_ma20": self.price_vs_ma20,
            "volatility20": self.volatility20,
            "max_drawdown60": self.max_drawdown60,
            "sentiment_score": self.sentiment_score,
            "sentiment_state": self.sentiment_state,
            "research_reading": self.research_reading,
            "data_points": self.data_points,
        }


def default_sentiment_universe(market: str) -> list[SentimentInstrument]:
    normalized = market.upper()
    if normalized == "CN":
        return [
            SentimentInstrument("000001", "上证指数", "CN", "大盘"),
            SentimentInstrument("399001", "深证成指", "CN", "大盘"),
            SentimentInstrument("399006", "创业板指", "CN", "成长"),
            SentimentInstrument("510300", "沪深300ETF", "CN", "宽基"),
            SentimentInstrument("518880", "黄金ETF", "CN", "避险"),
        ]
    if normalized == "HK":
        return [
            SentimentInstrument("^HSI", "恒生指数", "HK", "大盘"),
            SentimentInstrument("3033.HK", "恒生科技ETF", "HK", "成长"),
            SentimentInstrument("2800.HK", "盈富基金", "HK", "宽基"),
            SentimentInstrument("2840.HK", "SPDR 金 ETF", "HK", "避险"),
        ]
    return [
        SentimentInstrument("SPY", "S&P 500 ETF", "US", "大盘"),
        SentimentInstrument("QQQ", "NASDAQ 100 ETF", "US", "成长"),
        SentimentInstrument("^VIX", "VIX 波动率", "US", "波动"),
        SentimentInstrument("GLD", "黄金 ETF", "US", "避险"),
        SentimentInstrument("TLT", "长期美债 ETF", "US", "利率"),
    ]


def sentiment_from_bars(
    bars: pd.DataFrame,
    symbol: str,
    name: str = "",
    market: str = "",
    role: str = "观察对象",
) -> SentimentResult:
    if bars.empty or "close" not in bars.columns:
        raise ValueError(f"{symbol} 没有可用于情绪分析的行情数据。")
    data = bars.copy()
    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce")
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    data = data.dropna(subset=["datetime", "close"]).sort_values("datetime")
    if len(data) < 30:
        raise ValueError(f"{symbol} 数据不足，至少需要 30 个交易日。")
    close = data["close"]
    returns = close.pct_change().dropna()
    latest_close = float(close.iloc[-1])
    latest_date = data["datetime"].iloc[-1].date().isoformat()
    one_day_return = float(close.iloc[-1] / close.iloc[-2] - 1) if len(close) >= 2 else 0.0
    base_20 = close.iloc[-21] if len(close) >= 21 else close.iloc[0]
    twenty_day_return = float(latest_close / base_20 - 1) if base_20 else 0.0
    ma20 = float(close.tail(20).mean())
    price_vs_ma20 = float(latest_close / ma20 - 1) if ma20 else 0.0
    volatility20 = float(returns.tail(20).std(ddof=0) * np.sqrt(252)) if len(returns) >= 2 else 0.0
    max_drawdown60 = _max_drawdown(close.tail(60))
    rsi14 = _rsi(close, 14)
    score = sentiment_score(
        one_day_return=one_day_return,
        twenty_day_return=twenty_day_return,
        price_vs_ma20=price_vs_ma20,
        rsi14=rsi14,
        volatility20=volatility20,
        max_drawdown60=max_drawdown60,
        is_volatility_symbol=_is_volatility_symbol(symbol, name),
    )
    state = sentiment_state(score)
    return SentimentResult(
        symbol=symbol,
        name=name or symbol,
        market=market,
        role=role,
        latest_date=latest_date,
        close=latest_close,
        one_day_return=one_day_return,
        twenty_day_return=twenty_day_return,
        rsi14=rsi14,
        price_vs_ma20=price_vs_ma20,
        volatility20=volatility20,
        max_drawdown60=max_drawdown60,
        sentiment_score=score,
        sentiment_state=state,
        research_reading=sentiment_research_reading(state, rsi14, twenty_day_return, max_drawdown60),
        data_points=int(len(data)),
    )


def sentiment_score(
    one_day_return: float,
    twenty_day_return: float,
    price_vs_ma20: float,
    rsi14: float,
    volatility20: float,
    max_drawdown60: float,
    is_volatility_symbol: bool = False,
) -> float:
    if is_volatility_symbol:
        raw = 50.0 - _clip(one_day_return * 100, -8, 8) * 2.0 - _clip(twenty_day_return * 100, -20, 20) * 0.8
        raw += _clip((60 - rsi14), -25, 25) * 0.35
        return float(round(_clip(raw, 0, 100), 2))
    raw = 50.0
    raw += _clip(twenty_day_return * 100, -20, 20) * 0.9
    raw += _clip(price_vs_ma20 * 100, -12, 12) * 1.1
    raw += _clip(one_day_return * 100, -8, 8) * 1.2
    raw += _clip(rsi14 - 50, -35, 35) * 0.35
    raw -= _clip((volatility20 - 0.25) * 100, 0, 40) * 0.22
    raw += _clip(max_drawdown60 * 100, -30, 0) * 0.35
    return float(round(_clip(raw, 0, 100), 2))


def sentiment_state(score: float) -> str:
    if score < 25:
        return "极度低迷"
    if score < 45:
        return "偏冷"
    if score <= 55:
        return "中性"
    if score <= 75:
        return "偏热"
    return "过热"


def sentiment_research_reading(state: str, rsi14: float, twenty_day_return: float, max_drawdown60: float) -> str:
    if state == "过热":
        return "短期情绪拥挤，研究上应重点检查追高风险、估值证据和回撤承受能力。"
    if state == "偏热":
        if rsi14 >= 70:
            return "趋势偏强但 RSI 偏高，适合观察是否出现拥挤或分歧。"
        return "趋势仍偏强，需结合基本面、成交和成本压力判断证据是否充分。"
    if state == "中性":
        return "情绪处在中性区间，单靠情绪指标不足以形成高置信研究结论。"
    if state == "偏冷":
        if max_drawdown60 <= -0.15:
            return "价格处于明显回撤后，需区分恐慌错杀和趋势走弱。"
        return "短期情绪偏弱，适合补充数据质量、行业催化和反方观点。"
    if twenty_day_return < -0.10:
        return "情绪极冷且短期下跌明显，研究上必须先识别流动性、基本面和外部冲击风险。"
    return "情绪极冷，可能反映恐慌或数据异常，需要更多证据确认。"


def sentiment_summary(rows: pd.DataFrame) -> dict[str, object]:
    if rows.empty:
        return {
            "object_count": 0,
            "average_score": 0.0,
            "hot_count": 0,
            "cold_count": 0,
            "latest_date": "",
        }
    scores = pd.to_numeric(rows["sentiment_score"], errors="coerce").dropna()
    states = rows["sentiment_state"].fillna("").astype(str)
    return {
        "object_count": int(len(rows)),
        "average_score": float(round(scores.mean(), 2)) if not scores.empty else 0.0,
        "hot_count": int(states.isin(["偏热", "过热"]).sum()),
        "cold_count": int(states.isin(["偏冷", "极度低迷"]).sum()),
        "latest_date": str(rows["latest_date"].max()) if "latest_date" in rows else "",
    }


def _rsi(close: pd.Series, window: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    value = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50.0
    return float(round(value, 2))


def _max_drawdown(close: pd.Series) -> float:
    if close.empty:
        return 0.0
    peak = close.cummax()
    drawdown = close / peak - 1
    return float(drawdown.min())


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _is_volatility_symbol(symbol: str, name: str) -> bool:
    text = f"{symbol} {name}".lower()
    return "vix" in text or "波动" in text
