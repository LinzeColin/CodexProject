from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from qbvs.backtest import compare_to_buy_hold, drawdown, normalize_ohlcv, performance_metrics
from qbvs.strategies import BehaviorStrategySpec, generate_signals


@dataclass(frozen=True)
class FundTradingRule:
    initial_cash: float = 100_000.0
    subscription_fee_rate: float = 0.0015
    redemption_fee_rate_short: float = 0.015
    redemption_fee_rate_long: float = 0.005
    short_holding_days: int = 7
    min_holding_days: int = 0
    buy_confirmation_days: int = 1
    sell_cash_delay_days: int = 2
    annualization: int = 252

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _Lot:
    quantity: float
    acquired_index: int


@dataclass
class _PendingBuy:
    quantity: float
    confirm_index: int
    acquired_index: int
    cost: float


@dataclass
class _PendingCash:
    amount: float
    settle_index: int


def default_alipay_fund_rule() -> FundTradingRule:
    return FundTradingRule()


def run_fund_target_weight_backtest(
    bars: pd.DataFrame,
    signals: pd.DataFrame,
    rule: FundTradingRule | None = None,
) -> dict[str, Any]:
    rule = rule or default_alipay_fund_rule()
    frame = normalize_ohlcv(bars)
    signal_frame = signals[["datetime", "target_weight"]].copy()
    signal_frame["datetime"] = pd.to_datetime(signal_frame["datetime"])
    frame = frame.merge(signal_frame, on="datetime", how="left")
    frame["target_weight"] = frame["target_weight"].ffill().fillna(0.0).clip(0.0, 1.0)
    frame["execution_weight"] = frame["target_weight"].shift(1).fillna(0.0)

    cash = float(rule.initial_cash)
    lots: list[_Lot] = []
    pending_buys: list[_PendingBuy] = []
    pending_cash: list[_PendingCash] = []
    rows: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []

    for index, row in enumerate(frame.itertuples(index=False)):
        nav = float(row.close)
        cash += _release_pending_cash(pending_cash, index)
        _confirm_pending_buys(pending_buys, lots, index)

        confirmed_quantity = sum(lot.quantity for lot in lots)
        pending_quantity = sum(item.quantity for item in pending_buys)
        pending_receivable = sum(item.amount for item in pending_cash)
        position_value = (confirmed_quantity + pending_quantity) * nav
        equity_before = cash + position_value + pending_receivable
        target_weight = float(row.execution_weight)
        target_value = equity_before * target_weight
        trade_value = target_value - position_value

        if trade_value > 1e-8 and nav > 0 and cash > 1e-8:
            gross_cash = min(trade_value, cash)
            net_investment = gross_cash / (1.0 + rule.subscription_fee_rate)
            fee = gross_cash - net_investment
            quantity = net_investment / nav
            cash -= gross_cash
            pending_buys.append(
                _PendingBuy(
                    quantity=quantity,
                    confirm_index=index + rule.buy_confirmation_days,
                    acquired_index=index,
                    cost=net_investment,
                )
            )
            trades.append(
                {
                    "datetime": row.datetime,
                    "side": "BUY_SUBSCRIBE",
                    "quantity": quantity,
                    "price": nav,
                    "notional": net_investment,
                    "commission_cost": fee,
                    "subscription_fee": fee,
                    "redemption_fee": 0.0,
                    "target_weight": target_weight,
                    "cash_delay_days": 0,
                    "confirmation_days": rule.buy_confirmation_days,
                }
            )
        elif trade_value < -1e-8 and nav > 0:
            desired_value = abs(trade_value)
            sold_quantity, gross_value, redemption_fee = _sell_lots(lots, desired_value, nav, index, rule)
            if sold_quantity > 1e-12:
                net_cash = gross_value - redemption_fee
                pending_cash.append(_PendingCash(amount=net_cash, settle_index=index + rule.sell_cash_delay_days))
                trades.append(
                    {
                        "datetime": row.datetime,
                        "side": "SELL_REDEEM",
                        "quantity": -sold_quantity,
                        "price": nav,
                        "notional": -gross_value,
                        "commission_cost": redemption_fee,
                        "subscription_fee": 0.0,
                        "redemption_fee": redemption_fee,
                        "target_weight": target_weight,
                        "cash_delay_days": rule.sell_cash_delay_days,
                        "confirmation_days": 0,
                    }
                )

        confirmed_quantity = sum(lot.quantity for lot in lots)
        pending_quantity = sum(item.quantity for item in pending_buys)
        pending_receivable = sum(item.amount for item in pending_cash)
        position_value = (confirmed_quantity + pending_quantity) * nav
        equity = cash + position_value + pending_receivable
        rows.append(
            {
                "datetime": row.datetime,
                "close": nav,
                "cash": cash,
                "position_value": position_value,
                "pending_receivable": pending_receivable,
                "equity": equity,
                "target_weight": target_weight,
                "actual_weight": (position_value / equity) if equity else 0.0,
            }
        )

    equity = pd.DataFrame(rows)
    trades_frame = pd.DataFrame(trades)
    equity["return"] = equity["equity"].pct_change().fillna(0.0)
    equity["drawdown"] = drawdown(equity["equity"])
    metrics = performance_metrics(equity, trades_frame, _CostAdapter(rule))
    metrics["subscription_fee_total"] = _sum_or_zero(trades_frame, "subscription_fee")
    metrics["redemption_fee_total"] = _sum_or_zero(trades_frame, "redemption_fee")
    metrics["pending_cash_delay_days"] = rule.sell_cash_delay_days
    metrics["buy_confirmation_days"] = rule.buy_confirmation_days
    return {"equity": equity, "trades": trades_frame, "metrics": metrics, "rule": rule.to_dict()}


def run_fund_buy_hold(bars: pd.DataFrame, rule: FundTradingRule | None = None) -> dict[str, Any]:
    frame = normalize_ohlcv(bars)
    signals = pd.DataFrame({"datetime": frame["datetime"], "target_weight": 1.0})
    return run_fund_target_weight_backtest(frame, signals, rule)


def validate_fund_strategy(
    frame: pd.DataFrame,
    spec: BehaviorStrategySpec,
    rule: FundTradingRule | None = None,
) -> dict[str, object]:
    bars = normalize_ohlcv(frame)
    signals = generate_signals(bars, spec)
    strategy = run_fund_target_weight_backtest(bars, signals, rule)
    benchmark = run_fund_buy_hold(bars, rule)
    comparison = compare_to_buy_hold(strategy["metrics"], benchmark["metrics"])
    return {
        "strategy_id": spec.strategy_id,
        "symbol": str(bars["symbol"].iloc[0]),
        "market": str(bars["market"].iloc[0]),
        "start": str(pd.Timestamp(bars["datetime"].iloc[0]).date()),
        "end": str(pd.Timestamp(bars["datetime"].iloc[-1]).date()),
        "bars": int(len(bars)),
        "engine": "alipay_fund_rules",
        **{f"strategy_{k}": v for k, v in strategy["metrics"].items()},
        **{f"buy_hold_{k}": v for k, v in benchmark["metrics"].items()},
        **comparison,
    }


def validate_fund_universe(
    data_by_symbol: dict[str, pd.DataFrame],
    specs: list[BehaviorStrategySpec],
    rule: FundTradingRule | None = None,
) -> pd.DataFrame:
    rows = []
    for spec in specs:
        for symbol, frame in data_by_symbol.items():
            try:
                rows.append(validate_fund_strategy(frame, spec, rule))
            except Exception as exc:
                rows.append({"strategy_id": spec.strategy_id, "symbol": symbol, "engine": "alipay_fund_rules", "error": str(exc)})
    return pd.DataFrame(rows)


def summarize_fund_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    if "error" in results.columns:
        valid = results[results["error"].fillna("").astype(str).str.len() == 0].copy()
    else:
        valid = results.copy()
    if valid.empty:
        return pd.DataFrame()
    grouped = valid.groupby("strategy_id", dropna=False)
    return grouped.agg(
        samples=("symbol", "count"),
        pass_rate=("passes_user_floor", "mean"),
        avg_total_gap=("total_return_gap", "mean"),
        median_total_gap=("total_return_gap", "median"),
        avg_annualized_gap=("annualized_return_gap", "mean"),
        avg_drawdown_improvement=("drawdown_improvement", "mean"),
        avg_strategy_return=("strategy_total_return", "mean"),
        avg_buy_hold_return=("buy_hold_total_return", "mean"),
        avg_var_5=("strategy_var_5", "mean"),
        avg_cvar_5=("strategy_cvar_5", "mean"),
        avg_turnover=("strategy_turnover", "mean"),
        avg_trades=("strategy_trade_count", "mean"),
        avg_subscription_fee=("strategy_subscription_fee_total", "mean"),
        avg_redemption_fee=("strategy_redemption_fee_total", "mean"),
    ).reset_index().sort_values(
        ["pass_rate", "avg_annualized_gap", "avg_drawdown_improvement", "avg_total_gap"],
        ascending=[False, False, False, False],
    )


def write_fund_rule_template(output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pd.Series(default_alipay_fund_rule().to_dict()).to_json(force_ascii=False, indent=2), encoding="utf-8")
    return path


def load_fund_rule(path: str | Path) -> FundTradingRule:
    import json

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return FundTradingRule(**data)


def _release_pending_cash(pending_cash: list[_PendingCash], index: int) -> float:
    released = sum(item.amount for item in pending_cash if item.settle_index <= index)
    pending_cash[:] = [item for item in pending_cash if item.settle_index > index]
    return released


def _confirm_pending_buys(pending_buys: list[_PendingBuy], lots: list[_Lot], index: int) -> None:
    for item in list(pending_buys):
        if item.confirm_index <= index:
            lots.append(_Lot(quantity=item.quantity, acquired_index=item.acquired_index))
            pending_buys.remove(item)


def _sell_lots(lots: list[_Lot], desired_value: float, nav: float, index: int, rule: FundTradingRule) -> tuple[float, float, float]:
    remaining_value = desired_value
    sold_quantity = 0.0
    gross_value = 0.0
    redemption_fee = 0.0
    for lot in list(lots):
        holding_days = index - lot.acquired_index
        if holding_days < rule.min_holding_days:
            continue
        available_value = lot.quantity * nav
        sell_value = min(available_value, remaining_value)
        if sell_value <= 1e-12:
            continue
        qty = sell_value / nav
        fee_rate = rule.redemption_fee_rate_short if holding_days < rule.short_holding_days else rule.redemption_fee_rate_long
        fee = sell_value * fee_rate
        lot.quantity -= qty
        sold_quantity += qty
        gross_value += sell_value
        redemption_fee += fee
        remaining_value -= sell_value
        if lot.quantity <= 1e-12:
            lots.remove(lot)
        if remaining_value <= 1e-8:
            break
    return sold_quantity, gross_value, redemption_fee


def _sum_or_zero(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return 0.0
    return float(frame[column].sum())


class _CostAdapter:
    def __init__(self, rule: FundTradingRule):
        self.initial_cash = rule.initial_cash
        self.annualization = rule.annualization
