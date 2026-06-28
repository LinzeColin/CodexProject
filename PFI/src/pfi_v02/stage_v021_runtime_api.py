from __future__ import annotations

import json
import os
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pfi_v02.stage_v021_holdings_persistence import (
    V021HoldingsPersistenceService,
    V021HoldingSnapshot,
)


V021_RUNTIME_API_SCHEMA = "PFIV021RuntimeAPIV1"
DEFAULT_RUNTIME_API_HOST = "127.0.0.1"
DEFAULT_RUNTIME_API_PORT = 8766
FX_TO_CNY = {
    "CNY": 1.0,
    "AUD": 4.6874,
    "USD": 1.52 * 4.6874,
    "HKD": 0.195 * 4.6874,
}

_SERVER_LOCK = threading.Lock()
_SERVER_STATE: dict[str, Any] = {}


def load_v021_holdings_payload(*, db_path: Path | str | None = None) -> dict[str, Any]:
    service = V021HoldingsPersistenceService(db_path)
    rows = [_snapshot_to_frontend(row) for row in service.list_snapshots(include_deleted=True)]
    return {
        "schema": V021_RUNTIME_API_SCHEMA,
        "rows": rows,
        "summary": service.persistence_summary(),
    }


def save_v021_holdings_payload(payload: dict[str, Any], *, db_path: Path | str | None = None) -> dict[str, Any]:
    service = V021HoldingsPersistenceService(db_path)
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")

    for raw_row in rows:
        snapshot = _snapshot_from_frontend(raw_row)
        existing = service.get_snapshot(snapshot.snapshot_id)
        if snapshot.soft_deleted:
            if existing is not None and not existing.soft_deleted:
                service.soft_delete_snapshot(snapshot.snapshot_id, reason="用户在持仓编辑页软删除")
            continue

        service.upsert_snapshot(snapshot)
        if existing is None:
            service.create_adjustment(
                snapshot_id=snapshot.snapshot_id,
                portfolio_id=snapshot.portfolio_id,
                instrument_id=snapshot.instrument_id,
                adjustment_type="ADD",
                changes=snapshot.to_dict(),
                reason="用户在持仓编辑页新增",
            )
            continue

        changes = _snapshot_changes(existing, snapshot)
        if changes:
            service.create_adjustment(
                snapshot_id=snapshot.snapshot_id,
                portfolio_id=snapshot.portfolio_id,
                instrument_id=snapshot.instrument_id,
                adjustment_type="UPDATE",
                changes=changes,
                reason="用户在持仓编辑页保存修改",
            )
        elif existing.soft_deleted and not snapshot.soft_deleted:
            service.create_adjustment(
                snapshot_id=snapshot.snapshot_id,
                portfolio_id=snapshot.portfolio_id,
                instrument_id=snapshot.instrument_id,
                adjustment_type="RESTORE",
                changes={"soft_deleted": False},
                reason="用户在持仓编辑页恢复持仓",
            )

    return load_v021_holdings_payload(db_path=db_path)


def build_v021_operational_read_model(*, db_path: Path | str | None = None) -> dict[str, Any]:
    service = V021HoldingsPersistenceService(db_path)
    snapshots = service.list_snapshots()
    investment_value = round(sum(_snapshot_market_value_cny(item) for item in snapshots), 2)
    investment_cost = round(sum(_snapshot_cost_cny(item) for item in snapshots), 2)
    unrealized_pnl = round(investment_value - investment_cost, 2)
    cash_cny = _cash_position_from_snapshots(snapshots)
    total_assets = round(investment_value + cash_cny, 2)
    total_liabilities = 0.0
    net_worth = round(total_assets - total_liabilities, 2)
    adjustment_count = len(service.list_adjustments())

    return {
        "schema": "PFIV021OperationalReadModelV1",
        "accounts": {
            "cash_cny": cash_cny,
            "net_worth_cny": net_worth,
            "total_assets_cny": total_assets,
            "total_liabilities_cny": total_liabilities,
        },
        "investment": {
            "market_value_cny": investment_value,
            "cost_basis_cny": investment_cost,
            "total_return_cny": unrealized_pnl,
            "unrealized_pnl_cny": unrealized_pnl,
            "cash_position_cny": cash_cny,
            "holding_count": len(snapshots),
            "adjustment_count": adjustment_count,
        },
        "consumption": {
            "has_real_transactions": False,
            "empty_state": "消费趋势需要先导入真实流水，当前不伪造支出或预算。",
        },
    }


def build_v021_operational_trends(*, db_path: Path | str | None = None) -> dict[str, Any]:
    model = build_v021_operational_read_model(db_path=db_path)
    accounts = model["accounts"]
    investment = model["investment"]
    cost_basis = float(investment["cost_basis_cny"])
    market_value = float(investment["market_value_cny"])
    total_return = float(investment["total_return_cny"])
    cash_position = float(investment["cash_position_cny"])
    periods = ["成本基准", "当前"]
    has_holdings = investment["holding_count"] > 0

    payload = {
        "schema": "PFIV021OperationalTrendReadModelV1",
        "readModel": model,
        "trends": {
            "accounts": {
                "scope": "账户与资产",
                "title": "现金、净资产、总资产与负债趋势",
                "unit": "CNY",
                "source": "SQLite 运行读模型",
                "emptyState": "账户趋势需要先保存持仓或导入账户流水。",
                "periods": periods if has_holdings else [],
                "series": [
                    _series("cash_cny", "现金", "--pfi-teal", [cash_position, cash_position] if has_holdings else []),
                    _series("net_worth_cny", "净资产", "--pfi-blue", [cost_basis + cash_position, accounts["net_worth_cny"]] if has_holdings else []),
                    _series("total_assets_cny", "总资产", "--pfi-amber", [cost_basis + cash_position, accounts["total_assets_cny"]] if has_holdings else []),
                    _series("total_liabilities_cny", "总负债", "--pfi-red", [0.0, accounts["total_liabilities_cny"]] if has_holdings else []),
                ],
            },
            "investment": {
                "scope": "投资管理",
                "title": "投资市值、收益、未实现盈亏与现金仓位趋势",
                "unit": "CNY",
                "source": "SQLite 运行读模型",
                "emptyState": "投资趋势需要先保存持仓，当前不伪造收益。",
                "periods": periods if has_holdings else [],
                "series": [
                    _series("market_value_cny", "投资市值", "--pfi-blue", [cost_basis, market_value] if has_holdings else []),
                    _series("total_return_cny", "总收益", "--pfi-teal", [0.0, total_return] if has_holdings else []),
                    _series("unrealized_pnl_cny", "未实现盈亏", "--pfi-amber", [0.0, total_return] if has_holdings else []),
                    _series("cash_position_cny", "现金仓位", "--pfi-red", [cash_position, cash_position] if has_holdings else []),
                ],
            },
            "consumption": {
                "scope": "消费管理",
                "title": "本月支出、预算剩余、固定/弹性支出与现金流预测",
                "unit": "CNY",
                "source": "SQLite 运行读模型",
                "emptyState": model["consumption"]["empty_state"],
                "periods": [],
                "series": [
                    _series("month_spend_cny", "本月支出", "--pfi-blue", []),
                    _series("budget_remaining_cny", "预算剩余", "--pfi-teal", []),
                    _series("fixed_spend_cny", "固定支出", "--pfi-amber", []),
                    _series("flex_spend_cny", "弹性支出", "--pfi-red", []),
                    _series("cashflow_forecast_cny", "现金流预测", "--pfi-blue", []),
                ],
            },
        },
    }
    payload.update(payload["trends"])
    return payload


def ensure_v021_runtime_api_server(
    *,
    db_path: Path | str | None = None,
    host: str = DEFAULT_RUNTIME_API_HOST,
    port: int | None = None,
) -> str:
    requested_port = int(os.environ.get("PFI_V021_RUNTIME_API_PORT", port or DEFAULT_RUNTIME_API_PORT))
    with _SERVER_LOCK:
        existing = _SERVER_STATE.get("server")
        if existing is not None:
            return str(_SERVER_STATE["base_url"])

        handler = _handler_factory(db_path)
        server = ThreadingHTTPServer((host, requested_port), handler)
        thread = threading.Thread(target=server.serve_forever, name="pfi-v021-runtime-api", daemon=True)
        thread.start()
        base_url = f"http://{host}:{server.server_port}"
        _SERVER_STATE.update({"server": server, "thread": thread, "base_url": base_url, "db_path": db_path})
        return base_url


def _handler_factory(db_path: Path | str | None):
    class V021RuntimeApiHandler(BaseHTTPRequestHandler):
        server_version = "PFI-V021-RuntimeAPI/1.0"

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._send_json({"ok": True})

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            try:
                if path == "/health":
                    self._send_json({"status": "ok", "schema": V021_RUNTIME_API_SCHEMA})
                    return
                if path == "/api/holdings":
                    self._send_json(load_v021_holdings_payload(db_path=db_path))
                    return
                if path == "/api/trends":
                    self._send_json(build_v021_operational_trends(db_path=db_path))
                    return
                self._send_json({"error": "not_found", "message": "未找到接口"}, status=404)
            except Exception as exc:  # pragma: no cover - exercised through browser runtime
                self._send_json({"error": "server_error", "message": str(exc)}, status=500)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            try:
                payload = self._read_json()
                if path == "/api/holdings":
                    self._send_json(save_v021_holdings_payload(payload, db_path=db_path))
                    return
                self._send_json({"error": "not_found", "message": "未找到接口"}, status=404)
            except Exception as exc:  # pragma: no cover - exercised through browser runtime
                self._send_json({"error": "server_error", "message": str(exc)}, status=500)

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(raw or "{}")
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

    return V021RuntimeApiHandler


def _snapshot_from_frontend(row: Any) -> V021HoldingSnapshot:
    if not isinstance(row, dict):
        raise ValueError("holding row must be an object")
    snapshot_id = _clean(row.get("snapshotId") or row.get("snapshot_id") or "")
    instrument_id = _clean(row.get("instrumentId") or row.get("instrument_id") or "")
    if not snapshot_id:
        snapshot_id = f"v021-manual-{instrument_id or 'holding'}"
    if not instrument_id:
        instrument_id = "待补标的"
    return V021HoldingSnapshot(
        snapshot_id=snapshot_id,
        portfolio_id=_clean(row.get("portfolioId") or row.get("portfolio_id") or "manual"),
        instrument_id=instrument_id,
        display_name=_clean(row.get("displayName") or row.get("display_name") or instrument_id),
        quantity=_non_negative(row.get("quantity")),
        average_cost=_non_negative(row.get("averageCost") if "averageCost" in row else row.get("average_cost")),
        market_price=_non_negative(row.get("marketPrice") if "marketPrice" in row else row.get("market_price")),
        currency=_clean(row.get("currency") or "CNY").upper(),
        source_id=_clean(row.get("sourceId") or row.get("source_id") or "manual_review"),
        as_of=_clean(row.get("asOf") or row.get("as_of") or "2026-06-28"),
        soft_deleted=bool(row.get("softDeleted") or row.get("soft_deleted")),
        metadata=row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
    )


def _snapshot_to_frontend(snapshot: V021HoldingSnapshot) -> dict[str, Any]:
    return {
        "snapshotId": snapshot.snapshot_id,
        "portfolioId": snapshot.portfolio_id,
        "instrumentId": snapshot.instrument_id,
        "displayName": snapshot.display_name,
        "quantity": snapshot.quantity,
        "averageCost": snapshot.average_cost,
        "marketPrice": snapshot.market_price,
        "marketValue": snapshot.market_value,
        "currency": snapshot.currency,
        "sourceId": snapshot.source_id,
        "asOf": snapshot.as_of,
        "softDeleted": snapshot.soft_deleted,
        "metadata": snapshot.metadata,
    }


def _snapshot_changes(existing: V021HoldingSnapshot, new: V021HoldingSnapshot) -> dict[str, Any]:
    fields = ("portfolio_id", "instrument_id", "display_name", "quantity", "average_cost", "market_price", "currency", "source_id", "as_of", "soft_deleted")
    changes: dict[str, Any] = {}
    for field in fields:
        old_value = getattr(existing, field)
        new_value = getattr(new, field)
        if old_value != new_value:
            changes[field] = {"before": old_value, "after": new_value}
    return changes


def _snapshot_market_value_cny(snapshot: V021HoldingSnapshot) -> float:
    return round(snapshot.market_value * _fx_rate(snapshot.currency), 2)


def _snapshot_cost_cny(snapshot: V021HoldingSnapshot) -> float:
    return round(snapshot.quantity * snapshot.average_cost * _fx_rate(snapshot.currency), 2)


def _cash_position_from_snapshots(snapshots: list[V021HoldingSnapshot]) -> float:
    total = 0.0
    for snapshot in snapshots:
        cash_value = snapshot.metadata.get("cash_cny") if isinstance(snapshot.metadata, dict) else None
        if cash_value is not None:
            total += _non_negative(cash_value)
    return round(total, 2)


def _fx_rate(currency: str) -> float:
    return FX_TO_CNY.get(str(currency or "CNY").upper(), 1.0)


def _series(series_id: str, label: str, color: str, values: list[float]) -> dict[str, Any]:
    return {"id": series_id, "label": label, "color": color, "unit": "CNY", "values": [round(float(item), 2) for item in values]}


def _non_negative(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return numeric if numeric >= 0 else 0.0


def _clean(value: Any) -> str:
    return str(value or "").strip()
