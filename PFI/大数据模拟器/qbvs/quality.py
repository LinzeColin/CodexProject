from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd

from qbvs.backtest import normalize_ohlcv


@dataclass(frozen=True)
class QualityReport:
    quality_score: float
    quality_grade: str
    bars: int
    missing_close_ratio: float
    duplicate_datetime_count: int
    non_positive_close_count: int
    max_abs_daily_return: float
    median_abs_daily_return: float
    gap_ratio: float
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_ohlcv_quality(data: pd.DataFrame, symbol: str = "UNKNOWN", market: str = "UNKNOWN") -> QualityReport:
    raw = data.copy()
    missing_close_ratio = _missing_close_ratio(raw)
    duplicate_count = _duplicate_datetime_count(raw)
    try:
        frame = normalize_ohlcv(raw, symbol=symbol, market=market)
    except Exception as exc:
        return QualityReport(
            quality_score=0.0,
            quality_grade="F",
            bars=0,
            missing_close_ratio=missing_close_ratio,
            duplicate_datetime_count=duplicate_count,
            non_positive_close_count=0,
            max_abs_daily_return=0.0,
            median_abs_daily_return=0.0,
            gap_ratio=1.0,
            warnings=[f"normalization_failed: {exc}"],
        )
    close = frame["close"].astype(float)
    returns = close.pct_change().dropna().abs()
    non_positive = int((close <= 0).sum())
    gap_ratio = _calendar_gap_ratio(frame["datetime"])
    max_abs_return = float(returns.max()) if not returns.empty else 0.0
    median_abs_return = float(returns.median()) if not returns.empty else 0.0
    warnings = []
    score = 100.0
    if len(frame) < 120:
        warnings.append("too_few_bars_lt_120")
        score -= 25
    elif len(frame) < 252:
        warnings.append("short_history_lt_252")
        score -= 10
    if missing_close_ratio > 0:
        warnings.append("raw_missing_close")
        score -= min(30.0, missing_close_ratio * 100)
    if duplicate_count:
        warnings.append("duplicate_datetime")
        score -= min(20.0, duplicate_count * 2)
    if non_positive:
        warnings.append("non_positive_close")
        score -= min(30.0, non_positive * 5)
    if max_abs_return > 0.35:
        warnings.append("extreme_daily_return_gt_35pct")
        score -= 15
    if gap_ratio > 0.35:
        warnings.append("large_calendar_gap_ratio")
        score -= 20
    elif gap_ratio > 0.20:
        warnings.append("moderate_calendar_gap_ratio")
        score -= 8
    score = max(0.0, min(100.0, score))
    return QualityReport(
        quality_score=round(score, 2),
        quality_grade=_grade(score),
        bars=int(len(frame)),
        missing_close_ratio=float(missing_close_ratio),
        duplicate_datetime_count=duplicate_count,
        non_positive_close_count=non_positive,
        max_abs_daily_return=max_abs_return,
        median_abs_daily_return=median_abs_return,
        gap_ratio=float(gap_ratio),
        warnings=warnings,
    )


def infer_asset_class(symbol: str, market: str = "") -> str:
    text = f"{symbol} {market}".upper()
    if "ETF" in text or symbol.endswith((".SS", ".SZ")) and symbol[:3] in {"510", "511", "512", "513", "515", "516", "518", "159"}:
        return "ETF"
    if any(token in text for token in ["FX", "FOREX", "USD", "JPY", "EUR"]):
        return "FX"
    if any(token in text for token in ["GOLD", "GLD", "518880", "COMMODITY"]):
        return "COMMODITY"
    if market.upper() in {"CN_ETF", "US_ETF"}:
        return "ETF"
    if "HK" in market.upper() or symbol.endswith(".HK"):
        return "STOCK"
    if "STOCK" in market.upper() or market.upper() in {"US", "CN", "HK"}:
        return "STOCK"
    return "UNKNOWN"


def infer_tradability(symbol: str, market: str = "", source: str = "") -> str:
    text = f"{symbol} {market} {source}".upper()
    if "ALIPAY" in text or "MOOMOO" in text:
        return "CONFIRMED_SOURCE"
    if any(token in text for token in ["CN_ETF", "US_ETF", ".SS", ".SZ", ".HK", "SPY", "QQQ", "GLD", "TLT"]):
        return "LIKELY_TRADABLE_NEEDS_ACCOUNT_CHECK"
    return "UNKNOWN_NEEDS_CONFIRMATION"


def _missing_close_ratio(frame: pd.DataFrame) -> float:
    cols = {c.lower(): c for c in frame.columns}
    close_col = cols.get("close")
    if close_col is None:
        return 1.0
    return float(frame[close_col].isna().mean())


def _duplicate_datetime_count(frame: pd.DataFrame) -> int:
    cols = {c.lower(): c for c in frame.columns}
    dt_col = cols.get("datetime") or cols.get("date")
    if dt_col is None:
        return 0
    return int(pd.to_datetime(frame[dt_col], errors="coerce").duplicated().sum())


def _calendar_gap_ratio(datetimes: pd.Series) -> float:
    dates = pd.to_datetime(datetimes).sort_values()
    if len(dates) < 2:
        return 1.0
    diffs = dates.diff().dropna().dt.days
    large_gaps = (diffs > 10).sum()
    return float(large_gaps / max(1, len(diffs)))


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"
