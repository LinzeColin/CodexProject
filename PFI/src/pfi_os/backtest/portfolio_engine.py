from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from pfi_os.approvals import StrategyApprovalRegistry
from pfi_os.backtest.engine import BacktestConfig, BacktestResult
from pfi_os.backtest.metrics import drawdown_curve, performance_metrics
from pfi_os.strategies.base import Strategy


@dataclass
class PortfolioBacktestEngine:
    config: BacktestConfig

    def run(self, data: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        StrategyApprovalRegistry().require_approved(strategy)
        bars = data.copy().sort_values(["datetime", "symbol"]).reset_index(drop=True)
        required = {"datetime", "symbol", "open", "close"}
        missing = required - set(bars.columns)
        if missing:
            raise ValueError(f"Portfolio data missing columns: {sorted(missing)}")

        strategy_result = strategy.generate_signals(bars)
        signals = strategy_result.signals.copy().sort_values(["datetime", "symbol"]).reset_index(drop=True)
        bars = bars.merge(signals[["datetime", "symbol", "target_weight"]], on=["datetime", "symbol"], how="left")
        bars["target_weight"] = bars["target_weight"].fillna(0.0)
        if not self.config.allow_short:
            bars["target_weight"] = bars["target_weight"].clip(lower=0.0)
        bars["target_weight"] = _normalize_weights(bars)
        bars["execution_weight"] = bars.groupby("symbol")["target_weight"].shift(1).fillna(0.0)

        cash = self.config.initial_cash
        quantities: dict[str, float] = {}
        rows = []
        trade_rows = []
        position_rows = []

        for dt, day in bars.groupby("datetime", sort=True):
            day = day.sort_values("symbol")
            open_prices = day.set_index("symbol")["open"].astype(float)
            close_prices = day.set_index("symbol")["close"].astype(float)
            equity_before = cash + sum(quantities.get(symbol, 0.0) * open_prices.get(symbol, 0.0) for symbol in open_prices.index)

            for row in day.itertuples(index=False):
                symbol = row.symbol
                open_price = float(row.open)
                if open_price <= 0:
                    continue
                target_weight = float(row.execution_weight)
                current_qty = quantities.get(symbol, 0.0)
                current_value = current_qty * open_price
                target_value = equity_before * target_weight
                trade_value = target_value - current_value
                if abs(trade_value) <= 1e-8:
                    continue
                side = 1 if trade_value > 0 else -1
                execution_bps = self.config.slippage_bps + self.config.market_impact_bps
                slip_price = open_price * (1 + side * execution_bps / 10_000)
                trade_qty = trade_value / slip_price
                if not self.config.allow_short and trade_qty < -current_qty:
                    trade_qty = -current_qty
                notional = trade_qty * slip_price
                commission_cost = max(abs(notional) * self.config.commission_rate, self.config.min_commission)
                slippage_cost = abs(notional) * self.config.slippage_bps / 10_000
                market_impact_cost = abs(notional) * self.config.market_impact_bps / 10_000
                execution_cost = commission_cost + slippage_cost + market_impact_cost
                cash -= notional + commission_cost
                quantities[symbol] = current_qty + trade_qty
                trade_rows.append(
                    {
                        "datetime": dt,
                        "symbol": symbol,
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

            position_value = 0.0
            for symbol, close_price in close_prices.items():
                symbol_frame = day[day["symbol"] == symbol]
                qty = quantities.get(symbol, 0.0)
                value = qty * float(close_price)
                position_value += value
                position_rows.append(
                    {
                        "datetime": dt,
                        "symbol": symbol,
                        "market": str(symbol_frame["market"].iloc[0]) if "market" in symbol_frame.columns and not symbol_frame.empty else "",
                        "quantity": qty,
                        "close": float(close_price),
                        "position_value": value,
                    }
                )

            equity = cash + position_value
            rows.append(
                {
                    "datetime": dt,
                    "cash": cash,
                    "position_value": position_value,
                    "equity": equity,
                    "gross_exposure": abs(position_value) / equity if equity else 0.0,
                }
            )

        equity_curve = pd.DataFrame(rows)
        equity_curve["return"] = equity_curve["equity"].pct_change().fillna(0.0)
        equity_curve["drawdown"] = drawdown_curve(equity_curve["equity"])
        trades = pd.DataFrame(trade_rows)
        positions = pd.DataFrame(position_rows)
        metrics = performance_metrics(equity_curve, trades, self.config.initial_cash, self.config.annualization)
        metadata: dict[str, Any] = {
            "strategy": strategy_result.metadata,
            "backtest": {
                "initial_cash": self.config.initial_cash,
                "commission_rate": self.config.commission_rate,
                "min_commission": self.config.min_commission,
                "slippage_bps": self.config.slippage_bps,
                "market_impact_bps": self.config.market_impact_bps,
                "allow_short": self.config.allow_short,
                "mode": "portfolio",
            },
        }
        return BacktestResult(equity_curve, trades, positions, signals, metrics, metadata)


def _normalize_weights(bars: pd.DataFrame) -> pd.Series:
    weights = bars["target_weight"].astype(float).copy()
    gross = weights.abs().groupby(bars["datetime"]).transform("sum")
    oversized = gross > 1.0
    weights.loc[oversized] = weights.loc[oversized] / gross.loc[oversized]
    return weights
