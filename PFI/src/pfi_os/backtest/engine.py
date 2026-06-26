from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from pfi_os.approvals import StrategyApprovalRegistry
from pfi_os.backtest.metrics import drawdown_curve, performance_metrics
from pfi_os.strategies.base import Strategy


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 100_000.0
    commission_rate: float = 0.001
    min_commission: float = 0.0
    slippage_bps: float = 5.0
    market_impact_bps: float = 0.0
    allow_short: bool = False
    annualization: int = 252


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame
    trades: pd.DataFrame
    positions: pd.DataFrame
    signals: pd.DataFrame
    metrics: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


class BacktestEngine:
    """Single-symbol target-weight backtest engine.

    Signals generated on bar t are executed at bar t+1 open to avoid same-bar lookahead.
    """

    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()

    def run(self, data: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        StrategyApprovalRegistry().require_approved(strategy)
        bars = data.copy().sort_values("datetime").reset_index(drop=True)
        strategy_result = strategy.generate_signals(bars)
        signals = strategy_result.signals.copy().sort_values("datetime").reset_index(drop=True)
        if _uses_order_signals(signals):
            return self._run_order_signals(bars, signals, strategy_result.metadata)
        bars = bars.merge(signals[["datetime", "target_weight"]], on="datetime", how="left")
        bars["target_weight"] = bars["target_weight"].fillna(0.0)
        bars["execution_weight"] = bars["target_weight"].shift(1).fillna(0.0)

        cash = self.config.initial_cash
        quantity = 0.0
        rows = []
        trade_rows = []
        position_rows = []

        for i, row in bars.iterrows():
            open_price = float(row.open)
            close_price = float(row.close)
            target_weight = float(row.execution_weight)
            if not self.config.allow_short:
                target_weight = max(0.0, target_weight)

            equity_before = cash + quantity * open_price
            target_value = equity_before * target_weight
            current_value = quantity * open_price
            trade_value = target_value - current_value

            if abs(trade_value) > 1e-8 and open_price > 0:
                side = 1 if trade_value > 0 else -1
                execution_bps = self.config.slippage_bps + self.config.market_impact_bps
                slip_price = open_price * (1 + side * execution_bps / 10_000)
                trade_qty = trade_value / slip_price
                if not self.config.allow_short and trade_qty < -quantity:
                    trade_qty = -quantity
                notional = trade_qty * slip_price
                commission_cost = max(abs(notional) * self.config.commission_rate, self.config.min_commission)
                slippage_cost = abs(notional) * self.config.slippage_bps / 10_000
                market_impact_cost = abs(notional) * self.config.market_impact_bps / 10_000
                execution_cost = commission_cost + slippage_cost + market_impact_cost
                cash -= notional + commission_cost
                quantity += trade_qty
                trade_rows.append(
                    {
                        "datetime": row.datetime,
                        "symbol": row.symbol,
                        "side": "BUY" if trade_qty > 0 else "SELL",
                        "quantity": trade_qty,
                        "price": slip_price,
                        "notional": notional,
                        "cost": commission_cost,
                        "commission_cost": commission_cost,
                        "slippage_cost": slippage_cost,
                        "market_impact_cost": market_impact_cost,
                        "execution_cost": execution_cost,
                        "target_weight": target_weight,
                    }
                )

            equity = cash + quantity * close_price
            position_value = quantity * close_price
            actual_weight = position_value / equity if equity else 0.0
            rows.append(
                {
                    "datetime": row.datetime,
                    "cash": cash,
                    "position_value": position_value,
                    "equity": equity,
                    "target_weight": target_weight,
                    "actual_weight": actual_weight,
                    "close": close_price,
                }
            )
            position_rows.append(
                {
                    "datetime": row.datetime,
                    "symbol": row.symbol,
                    "quantity": quantity,
                    "close": close_price,
                    "position_value": position_value,
                    "cash": cash,
                    "equity": equity,
                }
            )

        equity_curve = pd.DataFrame(rows)
        equity_curve["return"] = equity_curve["equity"].pct_change().fillna(0.0)
        equity_curve["drawdown"] = drawdown_curve(equity_curve["equity"])
        trades = pd.DataFrame(trade_rows)
        positions = pd.DataFrame(position_rows)
        metrics = performance_metrics(equity_curve, trades, self.config.initial_cash, self.config.annualization)
        metadata = {
            "strategy": strategy_result.metadata,
            "backtest": {
                "initial_cash": self.config.initial_cash,
                "commission_rate": self.config.commission_rate,
                "min_commission": self.config.min_commission,
                "slippage_bps": self.config.slippage_bps,
                "market_impact_bps": self.config.market_impact_bps,
                "allow_short": self.config.allow_short,
            },
        }
        return BacktestResult(equity_curve, trades, positions, signals, metrics, metadata)

    def _run_order_signals(self, bars: pd.DataFrame, signals: pd.DataFrame, strategy_metadata: dict[str, Any]) -> BacktestResult:
        order_columns = [
            "datetime",
            "order_value",
            "sell_fraction",
            "action",
            "daily_return",
            "position_return",
            "target_weight",
        ]
        available_columns = [column for column in order_columns if column in signals.columns]
        bars = bars.merge(signals[available_columns], on="datetime", how="left")
        if "order_value" not in bars:
            bars["order_value"] = 0.0
        if "sell_fraction" not in bars:
            bars["sell_fraction"] = 0.0
        if "target_weight" not in bars:
            bars["target_weight"] = 0.0
        bars["order_value"] = bars["order_value"].fillna(0.0)
        bars["sell_fraction"] = bars["sell_fraction"].fillna(0.0).clip(0.0, 1.0)
        bars["target_weight"] = bars["target_weight"].fillna(0.0)

        cash = self.config.initial_cash
        quantity = 0.0
        avg_cost = 0.0
        last_buy_date = None
        rows = []
        trade_rows = []
        position_rows = []

        for row in bars.itertuples(index=False):
            close_price = float(row.close)
            if close_price <= 0:
                continue
            trade_qty = 0.0
            requested_notional = 0.0
            sell_fraction = float(getattr(row, "sell_fraction", 0.0) or 0.0)
            order_value = float(getattr(row, "order_value", 0.0) or 0.0)
            current_date = pd.Timestamp(row.datetime).date()

            if sell_fraction > 0 and quantity > 0 and current_date != last_buy_date:
                trade_qty = -quantity * min(1.0, sell_fraction)
                side = -1
                slip_price = close_price * (1 + side * (self.config.slippage_bps + self.config.market_impact_bps) / 10_000)
                requested_notional = abs(trade_qty * slip_price)
            elif order_value > 0:
                side = 1
                slip_price = close_price * (1 + side * (self.config.slippage_bps + self.config.market_impact_bps) / 10_000)
                requested_notional = float(int(order_value))
                commission_estimate = max(requested_notional * self.config.commission_rate, self.config.min_commission)
                if cash >= requested_notional + commission_estimate:
                    trade_qty = requested_notional / slip_price
                else:
                    trade_qty = 0.0
                    requested_notional = 0.0
            else:
                slip_price = close_price

            if abs(trade_qty) > 1e-8:
                notional = trade_qty * slip_price
                commission_cost = max(abs(notional) * self.config.commission_rate, self.config.min_commission)
                slippage_cost = abs(notional) * self.config.slippage_bps / 10_000
                market_impact_cost = abs(notional) * self.config.market_impact_bps / 10_000
                execution_cost = commission_cost + slippage_cost + market_impact_cost
                cash -= notional + commission_cost
                if trade_qty > 0:
                    previous_value = quantity * avg_cost
                    quantity += trade_qty
                    avg_cost = (previous_value + abs(notional)) / quantity if quantity else 0.0
                    last_buy_date = current_date
                else:
                    quantity += trade_qty
                    if quantity <= 1e-8:
                        quantity = 0.0
                        avg_cost = 0.0
                trade_rows.append(
                    {
                        "datetime": row.datetime,
                        "symbol": row.symbol,
                        "side": "BUY" if trade_qty > 0 else "SELL",
                        "quantity": trade_qty,
                        "price": slip_price,
                        "notional": notional,
                        "requested_notional": requested_notional,
                        "cost": commission_cost,
                        "commission_cost": commission_cost,
                        "slippage_cost": slippage_cost,
                        "market_impact_cost": market_impact_cost,
                        "execution_cost": execution_cost,
                        "target_weight": float(getattr(row, "target_weight", 0.0) or 0.0),
                        "order_value": order_value,
                        "sell_fraction": sell_fraction,
                    }
                )

            equity = cash + quantity * close_price
            position_value = quantity * close_price
            actual_weight = position_value / equity if equity else 0.0
            rows.append(
                {
                    "datetime": row.datetime,
                    "cash": cash,
                    "position_value": position_value,
                    "equity": equity,
                    "target_weight": float(getattr(row, "target_weight", 0.0) or 0.0),
                    "actual_weight": actual_weight,
                    "close": close_price,
                }
            )
            position_rows.append(
                {
                    "datetime": row.datetime,
                    "symbol": row.symbol,
                    "quantity": quantity,
                    "close": close_price,
                    "position_value": position_value,
                    "cash": cash,
                    "equity": equity,
                    "avg_cost": avg_cost,
                }
            )

        equity_curve = pd.DataFrame(rows)
        equity_curve["return"] = equity_curve["equity"].pct_change().fillna(0.0)
        equity_curve["drawdown"] = drawdown_curve(equity_curve["equity"])
        trades = pd.DataFrame(trade_rows)
        positions = pd.DataFrame(position_rows)
        metrics = performance_metrics(equity_curve, trades, self.config.initial_cash, self.config.annualization)
        metadata = {
            "strategy": strategy_metadata,
            "backtest": {
                "initial_cash": self.config.initial_cash,
                "commission_rate": self.config.commission_rate,
                "min_commission": self.config.min_commission,
                "slippage_bps": self.config.slippage_bps,
                "market_impact_bps": self.config.market_impact_bps,
                "allow_short": self.config.allow_short,
                "execution_model": "order_value_and_sell_fraction_at_close_proxy",
            },
        }
        return BacktestResult(equity_curve, trades, positions, signals, metrics, metadata)


def _uses_order_signals(signals: pd.DataFrame) -> bool:
    return any(column in signals.columns for column in ["order_value", "sell_fraction"])
