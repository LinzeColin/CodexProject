from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set

from backend.app.services.atomic_json_store import json_transaction, read_json, write_json_atomic


@dataclass
class PaperOrder:
    idempotency_key: str
    symbol: str
    side: str
    quantity: float
    price: float


@dataclass
class PaperBroker:
    cash: float = 10000.0
    positions: Dict[str, float] = field(default_factory=dict)
    seen_keys: Set[str] = field(default_factory=set)
    trade_log: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path, *, initial_cash: float = 10000.0) -> "PaperBroker":
        p = Path(path)
        if not p.exists():
            return cls(cash=initial_cash)
        data = read_json(p, default={})
        return cls.from_snapshot(data, initial_cash=initial_cash)

    @classmethod
    def from_snapshot(cls, data: dict, *, initial_cash: float = 10000.0) -> "PaperBroker":
        return cls(
            cash=float(data.get("cash", initial_cash)),
            positions={str(k): float(v) for k, v in data.get("positions", {}).items()},
            seen_keys=set(data.get("seen_keys", [])),
            trade_log=list(data.get("trade_log", [])),
        )

    @classmethod
    def submit_order_to_path(
        cls,
        path: str | Path,
        order: PaperOrder,
        *,
        initial_cash: float = 10000.0,
    ) -> tuple[dict, "PaperBroker"]:
        with json_transaction(path, default={}) as transaction:
            broker = cls.from_snapshot(transaction.data or {}, initial_cash=initial_cash)
            result = broker.submit_order(order)
            if result["status"] == "filled":
                transaction.write(broker.snapshot())
            return result, broker

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(p, self.snapshot())

    def submit_order(self, order: PaperOrder) -> dict:
        if order.idempotency_key in self.seen_keys:
            return {"status": "rejected", "reason": "duplicate idempotency key"}
        if order.quantity <= 0 or order.price <= 0:
            return {"status": "rejected", "reason": "invalid quantity or price"}
        notional = order.quantity * order.price
        if order.side == "buy":
            if notional > self.cash:
                return {"status": "rejected", "reason": "insufficient paper cash"}
            self.cash -= notional
            self.positions[order.symbol] = self.positions.get(order.symbol, 0.0) + order.quantity
        elif order.side == "sell":
            current = self.positions.get(order.symbol, 0.0)
            if order.quantity > current:
                return {"status": "rejected", "reason": "insufficient paper position"}
            self.positions[order.symbol] = current - order.quantity
            self.cash += notional
        else:
            return {"status": "rejected", "reason": "invalid side"}
        self.seen_keys.add(order.idempotency_key)
        event = {
            "idempotency_key": order.idempotency_key,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "price": order.price,
            "notional": round(notional, 2),
        }
        self.trade_log.append(event)
        return {"status": "filled", **self.snapshot()}

    def snapshot(self) -> dict:
        return {
            "cash": round(self.cash, 2),
            "positions": dict(self.positions),
            "seen_keys": sorted(self.seen_keys),
            "trade_log": list(self.trade_log),
            "trade_count": len(self.trade_log),
        }

    def portfolio_snapshot(self, mark_prices: Dict[str, float] | None = None) -> dict:
        mark_prices = mark_prices or {}
        position_rows = []
        positions_value = 0.0
        for symbol, quantity in sorted(self.positions.items()):
            mark_price = float(mark_prices.get(symbol, 0.0))
            market_value = quantity * mark_price
            positions_value += market_value
            position_rows.append(
                {
                    "symbol": symbol,
                    "quantity": quantity,
                    "mark_price": round(mark_price, 4),
                    "market_value": round(market_value, 2),
                }
            )
        return {
            "cash": round(self.cash, 2),
            "positions": position_rows,
            "positions_value": round(positions_value, 2),
            "total_equity": round(self.cash + positions_value, 2),
            "trade_count": len(self.trade_log),
            "latest_trade": self.trade_log[-1] if self.trade_log else None,
        }
