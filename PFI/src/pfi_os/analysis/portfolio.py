from __future__ import annotations

import pandas as pd

from pfi_os.backtest import BacktestResult


def portfolio_attribution(result: BacktestResult) -> pd.DataFrame:
    if result.positions.empty:
        return pd.DataFrame()
    positions = result.positions.copy()
    equity = result.equity_curve[["datetime", "equity"]].copy()
    positions = positions.merge(equity, on="datetime", how="left")
    positions["weight"] = positions["position_value"] / positions["equity"].replace(0, pd.NA)
    grouped = positions.groupby("symbol", sort=True)
    rows = []
    for symbol, frame in grouped:
        close = pd.to_numeric(frame["close"], errors="coerce").dropna()
        price_return = float(close.iloc[-1] / close.iloc[0] - 1) if len(close) >= 2 and close.iloc[0] else 0.0
        rows.append(
            {
                "symbol": symbol,
                "avg_weight": float(frame["weight"].abs().mean()),
                "max_weight": float(frame["weight"].abs().max()),
                "ending_weight": float(frame["weight"].iloc[-1]) if not frame.empty else 0.0,
                "ending_position_value": float(frame["position_value"].iloc[-1]) if not frame.empty else 0.0,
                "price_return": price_return,
            }
        )
    attribution = pd.DataFrame(rows)
    if result.trades.empty:
        attribution["trade_count"] = 0
        attribution["execution_cost"] = 0.0
    else:
        trades = result.trades.groupby("symbol").agg(trade_count=("symbol", "size"), execution_cost=("execution_cost", "sum")).reset_index()
        attribution = attribution.merge(trades, on="symbol", how="left")
        attribution["trade_count"] = attribution["trade_count"].fillna(0).astype(int)
        attribution["execution_cost"] = attribution["execution_cost"].fillna(0.0)
    return attribution.sort_values(["ending_weight", "avg_weight"], ascending=False).reset_index(drop=True)


def portfolio_concentration_metrics(result: BacktestResult) -> dict[str, float]:
    attribution = portfolio_attribution(result)
    if attribution.empty:
        return {"max_symbol_weight": 0.0, "top3_ending_weight": 0.0, "symbol_count": 0.0, "cash_weight": 0.0, "gross_exposure": 0.0}
    ending_weights = attribution["ending_weight"].abs().sort_values(ascending=False)
    ending = result.equity_curve.iloc[-1] if not result.equity_curve.empty else {}
    equity = _safe_float(ending.get("equity", 0.0))
    cash = _safe_float(ending.get("cash", 0.0))
    position_value = _safe_float(ending.get("position_value", 0.0))
    return {
        "max_symbol_weight": float(ending_weights.iloc[0]),
        "top3_ending_weight": float(ending_weights.head(3).sum()),
        "symbol_count": float(len(attribution)),
        "cash_weight": cash / equity if equity else 0.0,
        "gross_exposure": abs(position_value) / equity if equity else 0.0,
    }


def portfolio_exposure_breakdown(result: BacktestResult) -> pd.DataFrame:
    latest = _latest_positions(result)
    if latest.empty:
        return pd.DataFrame(columns=["dimension", "bucket", "exposure_value", "exposure_weight"])
    equity = _ending_equity(result)
    latest["market_bucket"] = latest.apply(lambda row: _infer_market(str(row.get("symbol", "")), str(row.get("market", ""))), axis=1)
    latest["currency_bucket"] = latest["market_bucket"].map(_market_currency).fillna("Unknown")
    latest["theme_bucket"] = latest["symbol"].astype(str).map(_symbol_theme)
    rows = []
    for dimension, column in [
        ("市场", "market_bucket"),
        ("货币", "currency_bucket"),
        ("主题", "theme_bucket"),
    ]:
        grouped = latest.groupby(column, dropna=False)["position_value"].sum().reset_index()
        for _, row in grouped.iterrows():
            value = _safe_float(row["position_value"])
            rows.append(
                {
                    "dimension": dimension,
                    "bucket": str(row[column]),
                    "exposure_value": value,
                    "exposure_weight": value / equity if equity else 0.0,
                }
            )
    return pd.DataFrame(rows).sort_values(["dimension", "exposure_weight"], ascending=[True, False]).reset_index(drop=True)


def portfolio_stress_scenarios(result: BacktestResult, shocks: tuple[float, ...] = (-0.10, -0.20, -0.30, -0.50)) -> pd.DataFrame:
    ending = result.equity_curve.iloc[-1] if not result.equity_curve.empty else {}
    equity = _safe_float(ending.get("equity", 0.0))
    position_value = _safe_float(ending.get("position_value", 0.0))
    rows = []
    for shock in shocks:
        loss_amount = position_value * abs(float(shock))
        loss_ratio = loss_amount / equity if equity else 0.0
        ending_equity = equity - loss_amount
        rebound_needed = loss_ratio / max(1.0 - loss_ratio, 1e-12) if loss_ratio < 1.0 else float("inf")
        rows.append(
            {
                "shock": float(shock),
                "loss_amount": loss_amount,
                "account_loss_ratio": loss_ratio,
                "ending_equity_after_shock": ending_equity,
                "rebound_needed_to_recover": rebound_needed,
            }
        )
    return pd.DataFrame(rows)


def portfolio_single_symbol_loss(result: BacktestResult, shock: float = -0.50) -> pd.DataFrame:
    latest = _latest_positions(result)
    if latest.empty:
        return pd.DataFrame(columns=["symbol", "position_value", "shock", "loss_amount", "account_loss_ratio"])
    equity = _ending_equity(result)
    latest = latest.copy()
    latest["shock"] = float(shock)
    latest["loss_amount"] = pd.to_numeric(latest["position_value"], errors="coerce").fillna(0.0).abs() * abs(float(shock))
    latest["account_loss_ratio"] = latest["loss_amount"] / equity if equity else 0.0
    return latest[["symbol", "position_value", "shock", "loss_amount", "account_loss_ratio"]].sort_values("account_loss_ratio", ascending=False)


def _latest_positions(result: BacktestResult) -> pd.DataFrame:
    if result.positions.empty:
        return pd.DataFrame()
    positions = result.positions.copy()
    latest_dt = positions["datetime"].max()
    latest = positions[positions["datetime"] == latest_dt].copy()
    latest["position_value"] = pd.to_numeric(latest["position_value"], errors="coerce").fillna(0.0)
    return latest[latest["position_value"].abs() > 1e-8].reset_index(drop=True)


def _ending_equity(result: BacktestResult) -> float:
    if result.equity_curve.empty:
        return 0.0
    return _safe_float(result.equity_curve.iloc[-1].get("equity", 0.0))


def _infer_market(symbol: str, market: str) -> str:
    if market:
        return market
    upper = symbol.upper()
    if upper.endswith((".SH", ".SZ", ".BJ")):
        return "CN"
    if upper.endswith(".HK"):
        return "HK"
    return "US"


def _market_currency(market: str) -> str:
    return {"CN": "CNY", "HK": "HKD", "US": "USD"}.get(str(market), "Unknown")


def _symbol_theme(symbol: str) -> str:
    upper = symbol.upper()
    mapping = {
        "QQQ": "科技成长",
        "SPY": "美国宽基",
        "TLT": "利率债",
        "GLD": "黄金",
        "IWM": "小盘",
        "DIA": "蓝筹",
        "XLF": "金融",
        "XLK": "科技成长",
        "XLE": "能源周期",
        "XLV": "医疗",
    }
    return mapping.get(upper, "未分类")


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
