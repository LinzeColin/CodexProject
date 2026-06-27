from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
from typing import Iterable

import pandas as pd

from qbvs.indicators import atr, bollinger, macd, rsi, sma


@dataclass(frozen=True)
class BehaviorStrategySpec:
    strategy_id: str
    base_weight: float
    dip_trigger: str
    sell_trigger: str
    trend_rule: str
    risk_rule: str
    boll_std: float = 2.2
    rsi_buy: float = 35.0
    rsi_sell: float = 75.0
    fast_ma: int = 20
    slow_ma: int = 60
    atr_window: int = 14

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def generate_strategy_specs(limit: int | None = None) -> list[BehaviorStrategySpec]:
    base_weights = [0.92, 0.95, 0.98, 0.99, 1.0]
    dip_triggers = ["none", "boll_lower", "rsi_35", "boll_or_rsi", "ma20_pullback", "two_day_drop"]
    sell_triggers = ["none", "rsi_high_trim", "boll_upper_trim", "weak_trend_trim"]
    trend_rules = ["none", "strong_trend_full", "ma_trend_full", "macd_trend_full"]
    risk_rules = ["none", "atr_96", "ma60_break_90", "drawdown_90"]
    specs: list[BehaviorStrategySpec] = []
    for base, dip, sell, trend, risk in product(base_weights, dip_triggers, sell_triggers, trend_rules, risk_rules):
        if dip == "none" and sell != "none":
            continue
        if base == 1.0 and trend != "none":
            continue
        strategy_id = f"bw{int(base*100)}_{dip}_{sell}_{trend}_{risk}"
        specs.append(
            BehaviorStrategySpec(
                strategy_id=strategy_id,
                base_weight=base,
                dip_trigger=dip,
                sell_trigger=sell,
                trend_rule=trend,
                risk_rule=risk,
            )
        )
        if limit and len(specs) >= limit:
            return specs
    return specs


def select_strategy_specs_by_id(strategy_ids: Iterable[str]) -> list[BehaviorStrategySpec]:
    requested = [str(strategy_id) for strategy_id in strategy_ids]
    by_id = {spec.strategy_id: spec for spec in generate_strategy_specs()}
    missing = [strategy_id for strategy_id in requested if strategy_id not in by_id]
    if missing:
        raise ValueError(f"unknown strategy_id values: {', '.join(missing)}")
    return [by_id[strategy_id] for strategy_id in requested]


def named_default_specs() -> list[BehaviorStrategySpec]:
    return [
        BehaviorStrategySpec("recommended_base99_boll_no_sell", 0.99, "boll_lower", "none", "strong_trend_full", "none"),
        BehaviorStrategySpec("conservative_base98_boll_no_sell", 0.98, "boll_lower", "none", "strong_trend_full", "none"),
        BehaviorStrategySpec("risk_base98_boll_atr96", 0.98, "boll_lower", "none", "strong_trend_full", "atr_96"),
        BehaviorStrategySpec("alipay_like_chase_dip_sell_rally", 0.90, "two_day_drop", "rsi_high_trim", "none", "none"),
    ]


def generate_signals(bars: pd.DataFrame, spec: BehaviorStrategySpec) -> pd.DataFrame:
    frame = bars.copy().sort_values("datetime").reset_index(drop=True)
    close = frame["close"].astype(float)
    returns = close.pct_change().fillna(0.0)
    bb = bollinger(close, 20, spec.boll_std)
    rsi14 = rsi(close, 14)
    ma_fast = sma(close, spec.fast_ma)
    ma_slow = sma(close, spec.slow_ma)
    macd_frame = macd(close)
    atr_pct = (atr(frame, spec.atr_window) / close).fillna(0.0)

    target = pd.Series(spec.base_weight, index=frame.index, dtype=float)
    target = _apply_dip_rule(target, spec, close, returns, bb, rsi14, ma_fast)
    target = _apply_trend_rule(target, spec, ma_fast, ma_slow, macd_frame)
    target = _apply_sell_rule(target, spec, bb, rsi14, ma_fast, ma_slow)
    target = _apply_risk_rule(target, spec, close, ma_slow, atr_pct)
    target = target.ffill().fillna(spec.base_weight).clip(0.0, 1.0)
    return pd.DataFrame({"datetime": frame["datetime"], "target_weight": target})


def _apply_dip_rule(
    target: pd.Series,
    spec: BehaviorStrategySpec,
    close: pd.Series,
    returns: pd.Series,
    bb: pd.DataFrame,
    rsi14: pd.Series,
    ma_fast: pd.Series,
) -> pd.Series:
    if spec.dip_trigger == "none":
        return target
    if spec.dip_trigger == "boll_lower":
        mask = close < bb["lower"]
    elif spec.dip_trigger == "rsi_35":
        mask = rsi14 < spec.rsi_buy
    elif spec.dip_trigger == "boll_or_rsi":
        mask = (close < bb["lower"]) | (rsi14 < spec.rsi_buy)
    elif spec.dip_trigger == "ma20_pullback":
        mask = (close < ma_fast) & (returns < 0)
    elif spec.dip_trigger == "two_day_drop":
        mask = (returns < 0) & (returns.shift(1) < 0)
    else:
        raise ValueError(f"unknown dip trigger: {spec.dip_trigger}")
    target.loc[mask.fillna(False)] = 1.0
    return target


def _apply_trend_rule(
    target: pd.Series,
    spec: BehaviorStrategySpec,
    ma_fast: pd.Series,
    ma_slow: pd.Series,
    macd_frame: pd.DataFrame,
) -> pd.Series:
    if spec.trend_rule == "none":
        return target
    if spec.trend_rule == "strong_trend_full":
        mask = (ma_fast > ma_slow) & (macd_frame["hist"] > 0)
    elif spec.trend_rule == "ma_trend_full":
        mask = ma_fast > ma_slow
    elif spec.trend_rule == "macd_trend_full":
        mask = macd_frame["hist"] > 0
    else:
        raise ValueError(f"unknown trend rule: {spec.trend_rule}")
    target.loc[mask.fillna(False)] = 1.0
    return target


def _apply_sell_rule(
    target: pd.Series,
    spec: BehaviorStrategySpec,
    bb: pd.DataFrame,
    rsi14: pd.Series,
    ma_fast: pd.Series,
    ma_slow: pd.Series,
) -> pd.Series:
    if spec.sell_trigger == "none":
        return target
    if spec.sell_trigger == "rsi_high_trim":
        mask = rsi14 > spec.rsi_sell
    elif spec.sell_trigger == "boll_upper_trim":
        mask = bb["upper"].notna() & (bb["mid"].notna()) & (bb["upper"] > bb["mid"])
        mask = mask & (rsi14 > 60)
    elif spec.sell_trigger == "weak_trend_trim":
        mask = ma_fast < ma_slow
    else:
        raise ValueError(f"unknown sell trigger: {spec.sell_trigger}")
    target.loc[mask.fillna(False)] = (target.loc[mask.fillna(False)] * 0.85).clip(0.0, 1.0)
    return target


def _apply_risk_rule(
    target: pd.Series,
    spec: BehaviorStrategySpec,
    close: pd.Series,
    ma_slow: pd.Series,
    atr_pct: pd.Series,
) -> pd.Series:
    if spec.risk_rule == "none":
        return target
    if spec.risk_rule == "atr_96":
        mask = atr_pct > atr_pct.rolling(120, min_periods=20).quantile(0.85)
        target.loc[mask.fillna(False)] = target.loc[mask.fillna(False)].clip(upper=0.96)
    elif spec.risk_rule == "ma60_break_90":
        mask = close < ma_slow
        target.loc[mask.fillna(False)] = target.loc[mask.fillna(False)].clip(upper=0.90)
    elif spec.risk_rule == "drawdown_90":
        peak = close.cummax()
        mask = close / peak - 1.0 < -0.15
        target.loc[mask.fillna(False)] = target.loc[mask.fillna(False)].clip(upper=0.90)
    else:
        raise ValueError(f"unknown risk rule: {spec.risk_rule}")
    return target


def specs_to_frame(specs: Iterable[BehaviorStrategySpec]) -> pd.DataFrame:
    return pd.DataFrame([spec.to_dict() for spec in specs])
