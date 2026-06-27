from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from pfi_os.application.operational_store import default_operational_db_path


V021_HOLDINGS_PERSISTENCE_SCHEMA = "PFIV021HoldingsPersistenceV1"
V021_HOLDINGS_TABLE = "v021_holding_snapshots"
V021_ADJUSTMENTS_TABLE = "v021_position_adjustments"
V021_ALLOWED_ADJUSTMENT_TYPES = ("ADD", "UPDATE", "SOFT_DELETE", "RESTORE")


@dataclass(frozen=True)
class V021HoldingSnapshot:
    snapshot_id: str
    portfolio_id: str
    instrument_id: str
    display_name: str
    quantity: float
    average_cost: float
    market_price: float
    currency: str
    source_id: str
    as_of: str
    soft_deleted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for field_name in ("snapshot_id", "portfolio_id", "instrument_id", "display_name", "currency", "source_id", "as_of"):
            if not str(getattr(self, field_name) or "").strip():
                raise ValueError(f"{field_name} is required")
        if self.quantity < 0:
            raise ValueError("quantity must be non-negative")
        if self.average_cost < 0:
            raise ValueError("average_cost must be non-negative")
        if self.market_price < 0:
            raise ValueError("market_price must be non-negative")

    @property
    def market_value(self) -> float:
        return round(float(self.quantity) * float(self.market_price), 6)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["market_value"] = self.market_value
        return payload


@dataclass(frozen=True)
class V021PositionAdjustment:
    adjustment_id: str
    snapshot_id: str
    portfolio_id: str
    instrument_id: str
    adjustment_type: str
    changes: dict[str, Any]
    reason: str
    status: str = "open"
    human_review_required: bool = True
    soft_deleted: bool = False
    created_at: str = ""

    def validate(self) -> None:
        for field_name in ("adjustment_id", "snapshot_id", "portfolio_id", "instrument_id", "adjustment_type", "reason"):
            if not str(getattr(self, field_name) or "").strip():
                raise ValueError(f"{field_name} is required")
        if self.adjustment_type not in V021_ALLOWED_ADJUSTMENT_TYPES:
            raise ValueError(f"adjustment_type must be one of {', '.join(V021_ALLOWED_ADJUSTMENT_TYPES)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class V021HoldingsPersistenceService:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path).expanduser() if db_path is not None else default_operational_db_path()

    def initialize(self) -> Path:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(V021_HOLDINGS_SCHEMA_SQL)
        return self.db_path

    def upsert_snapshot(self, snapshot: V021HoldingSnapshot) -> V021HoldingSnapshot:
        snapshot.validate()
        self.initialize()
        now = _now()
        with self._connect() as conn:
            conn.execute(
                f"""
                INSERT INTO {V021_HOLDINGS_TABLE}(
                    snapshot_id, portfolio_id, instrument_id, display_name, quantity,
                    average_cost, market_price, market_value, currency, source_id, as_of,
                    soft_deleted, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id) DO UPDATE SET
                    portfolio_id=excluded.portfolio_id,
                    instrument_id=excluded.instrument_id,
                    display_name=excluded.display_name,
                    quantity=excluded.quantity,
                    average_cost=excluded.average_cost,
                    market_price=excluded.market_price,
                    market_value=excluded.market_value,
                    currency=excluded.currency,
                    source_id=excluded.source_id,
                    as_of=excluded.as_of,
                    soft_deleted=excluded.soft_deleted,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.portfolio_id,
                    snapshot.instrument_id,
                    snapshot.display_name,
                    float(snapshot.quantity),
                    float(snapshot.average_cost),
                    float(snapshot.market_price),
                    snapshot.market_value,
                    snapshot.currency,
                    snapshot.source_id,
                    snapshot.as_of,
                    int(snapshot.soft_deleted),
                    _json(snapshot.metadata),
                    now,
                    now,
                ),
            )
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> V021HoldingSnapshot | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(f"SELECT * FROM {V021_HOLDINGS_TABLE} WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
        return _snapshot_from_row(row) if row else None

    def list_snapshots(self, *, include_deleted: bool = False) -> list[V021HoldingSnapshot]:
        self.initialize()
        where = "" if include_deleted else "WHERE soft_deleted = 0"
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM {V021_HOLDINGS_TABLE} {where} ORDER BY portfolio_id, instrument_id, snapshot_id"
            ).fetchall()
        return [_snapshot_from_row(row) for row in rows]

    def soft_delete_snapshot(self, snapshot_id: str, *, reason: str) -> V021PositionAdjustment:
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None:
            raise KeyError(f"snapshot not found: {snapshot_id}")
        deleted = replace(snapshot, soft_deleted=True)
        self.upsert_snapshot(deleted)
        return self.create_adjustment(
            snapshot_id=snapshot.snapshot_id,
            portfolio_id=snapshot.portfolio_id,
            instrument_id=snapshot.instrument_id,
            adjustment_type="SOFT_DELETE",
            changes={"soft_deleted": True},
            reason=reason,
        )

    def create_adjustment(
        self,
        *,
        snapshot_id: str,
        portfolio_id: str,
        instrument_id: str,
        adjustment_type: str,
        changes: dict[str, Any],
        reason: str,
        adjustment_id: str = "",
        status: str = "open",
    ) -> V021PositionAdjustment:
        adjustment = V021PositionAdjustment(
            adjustment_id=adjustment_id or _stable_adjustment_id(snapshot_id, adjustment_type, changes, reason),
            snapshot_id=snapshot_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            adjustment_type=adjustment_type,
            changes=changes,
            reason=reason,
            status=status,
            created_at=_now(),
        )
        adjustment.validate()
        self.initialize()
        now = _now()
        with self._connect() as conn:
            conn.execute(
                f"""
                INSERT INTO {V021_ADJUSTMENTS_TABLE}(
                    adjustment_id, snapshot_id, portfolio_id, instrument_id, adjustment_type,
                    changes_json, reason, status, human_review_required, soft_deleted,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(adjustment_id) DO UPDATE SET
                    snapshot_id=excluded.snapshot_id,
                    portfolio_id=excluded.portfolio_id,
                    instrument_id=excluded.instrument_id,
                    adjustment_type=excluded.adjustment_type,
                    changes_json=excluded.changes_json,
                    reason=excluded.reason,
                    status=excluded.status,
                    human_review_required=excluded.human_review_required,
                    soft_deleted=excluded.soft_deleted,
                    updated_at=excluded.updated_at
                """,
                (
                    adjustment.adjustment_id,
                    adjustment.snapshot_id,
                    adjustment.portfolio_id,
                    adjustment.instrument_id,
                    adjustment.adjustment_type,
                    _json(adjustment.changes),
                    adjustment.reason,
                    adjustment.status,
                    int(adjustment.human_review_required),
                    int(adjustment.soft_deleted),
                    adjustment.created_at,
                    now,
                ),
            )
        return adjustment

    def update_adjustment(self, adjustment_id: str, *, reason: str | None = None, status: str | None = None) -> V021PositionAdjustment:
        existing = self.get_adjustment(adjustment_id)
        if existing is None:
            raise KeyError(f"adjustment not found: {adjustment_id}")
        updated = replace(
            existing,
            reason=reason if reason is not None else existing.reason,
            status=status if status is not None else existing.status,
        )
        updated.validate()
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                f"""
                UPDATE {V021_ADJUSTMENTS_TABLE}
                SET reason = ?, status = ?, updated_at = ?
                WHERE adjustment_id = ?
                """,
                (updated.reason, updated.status, _now(), updated.adjustment_id),
            )
        return updated

    def soft_delete_adjustment(self, adjustment_id: str) -> V021PositionAdjustment:
        existing = self.get_adjustment(adjustment_id)
        if existing is None:
            raise KeyError(f"adjustment not found: {adjustment_id}")
        deleted = replace(existing, soft_deleted=True, status="deleted")
        with self._connect() as conn:
            conn.execute(
                f"""
                UPDATE {V021_ADJUSTMENTS_TABLE}
                SET soft_deleted = 1, status = ?, updated_at = ?
                WHERE adjustment_id = ?
                """,
                (deleted.status, _now(), deleted.adjustment_id),
            )
        return deleted

    def get_adjustment(self, adjustment_id: str) -> V021PositionAdjustment | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(f"SELECT * FROM {V021_ADJUSTMENTS_TABLE} WHERE adjustment_id = ?", (adjustment_id,)).fetchone()
        return _adjustment_from_row(row) if row else None

    def list_adjustments(self, *, include_deleted: bool = False) -> list[V021PositionAdjustment]:
        self.initialize()
        where = "" if include_deleted else "WHERE soft_deleted = 0"
        with self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM {V021_ADJUSTMENTS_TABLE} {where} ORDER BY created_at, adjustment_id").fetchall()
        return [_adjustment_from_row(row) for row in rows]

    def persistence_summary(self) -> dict[str, Any]:
        snapshots = self.list_snapshots()
        adjustments = self.list_adjustments()
        return {
            "schema": V021_HOLDINGS_PERSISTENCE_SCHEMA,
            "db_path": str(self.db_path),
            "snapshot_count": len(snapshots),
            "adjustment_count": len(adjustments),
            "market_value_total": round(sum(item.market_value for item in snapshots), 2),
            "tables": (V021_HOLDINGS_TABLE, V021_ADJUSTMENTS_TABLE),
            "execution_boundary": {
                "sqlite_operational_store": True,
                "public_git_private_data": False,
                "broker_connection": False,
                "order_submission": False,
                "payment_submission": False,
                "automatic_live_trading": False,
            },
        }

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def build_v021_demo_holding_snapshots(as_of: str = "2026-06-27") -> tuple[V021HoldingSnapshot, ...]:
    return (
        V021HoldingSnapshot("v021-snap-spy", "core", "SPY", "SPY ETF", 8.0, 520.0, 548.0, "USD", "manual_review", as_of),
        V021HoldingSnapshot("v021-snap-510300", "core", "510300", "沪深300ETF", 1200.0, 3.72, 3.91, "CNY", "manual_review", as_of),
        V021HoldingSnapshot("v021-snap-gold", "core", "ABC_GOLD", "ABC Bullion 黄金", 1.0, 3900.0, 4200.0, "AUD", "manual_review", as_of),
    )


def seed_v021_demo_holdings(service: V021HoldingsPersistenceService, snapshots: Iterable[V021HoldingSnapshot] | None = None) -> dict[str, Any]:
    rows = tuple(snapshots or build_v021_demo_holding_snapshots())
    for snapshot in rows:
        service.upsert_snapshot(snapshot)
    return service.persistence_summary()


V021_HOLDINGS_SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS {V021_HOLDINGS_TABLE} (
  snapshot_id TEXT PRIMARY KEY,
  portfolio_id TEXT NOT NULL,
  instrument_id TEXT NOT NULL,
  display_name TEXT NOT NULL,
  quantity REAL NOT NULL,
  average_cost REAL NOT NULL,
  market_price REAL NOT NULL,
  market_value REAL NOT NULL,
  currency TEXT NOT NULL,
  source_id TEXT NOT NULL,
  as_of TEXT NOT NULL,
  soft_deleted INTEGER NOT NULL DEFAULT 0,
  metadata_json TEXT NOT NULL DEFAULT '{{}}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS {V021_ADJUSTMENTS_TABLE} (
  adjustment_id TEXT PRIMARY KEY,
  snapshot_id TEXT NOT NULL,
  portfolio_id TEXT NOT NULL,
  instrument_id TEXT NOT NULL,
  adjustment_type TEXT NOT NULL,
  changes_json TEXT NOT NULL DEFAULT '{{}}',
  reason TEXT NOT NULL,
  status TEXT NOT NULL,
  human_review_required INTEGER NOT NULL DEFAULT 1,
  soft_deleted INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(snapshot_id) REFERENCES {V021_HOLDINGS_TABLE}(snapshot_id)
);
"""


def _snapshot_from_row(row: sqlite3.Row) -> V021HoldingSnapshot:
    return V021HoldingSnapshot(
        snapshot_id=str(row["snapshot_id"]),
        portfolio_id=str(row["portfolio_id"]),
        instrument_id=str(row["instrument_id"]),
        display_name=str(row["display_name"]),
        quantity=float(row["quantity"]),
        average_cost=float(row["average_cost"]),
        market_price=float(row["market_price"]),
        currency=str(row["currency"]),
        source_id=str(row["source_id"]),
        as_of=str(row["as_of"]),
        soft_deleted=bool(row["soft_deleted"]),
        metadata=_loads(row["metadata_json"]),
    )


def _adjustment_from_row(row: sqlite3.Row) -> V021PositionAdjustment:
    return V021PositionAdjustment(
        adjustment_id=str(row["adjustment_id"]),
        snapshot_id=str(row["snapshot_id"]),
        portfolio_id=str(row["portfolio_id"]),
        instrument_id=str(row["instrument_id"]),
        adjustment_type=str(row["adjustment_type"]),
        changes=_loads(row["changes_json"]),
        reason=str(row["reason"]),
        status=str(row["status"]),
        human_review_required=bool(row["human_review_required"]),
        soft_deleted=bool(row["soft_deleted"]),
        created_at=str(row["created_at"]),
    )


def _json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _loads(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stable_adjustment_id(snapshot_id: str, adjustment_type: str, changes: dict[str, Any], reason: str) -> str:
    raw = "|".join([snapshot_id, adjustment_type, _json(changes), reason])
    import hashlib

    return f"v021-adj-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"
