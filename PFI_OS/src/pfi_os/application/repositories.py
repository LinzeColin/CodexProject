from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from pfi_os.application.operational_store import DataDomain, OperationalStore, TaskRecord


@dataclass(frozen=True)
class TaskQueueItem:
    task_id: str
    priority: str
    status: str
    owner_workspace: str
    action: str
    source_id: str
    evidence_id: str
    as_of: str
    human_review_required: bool


@dataclass(frozen=True)
class HoldingSnapshot:
    snapshot_id: str
    portfolio_id: str
    as_of: str
    source_id: str
    evidence_id: str
    data_domain: str
    holdings: tuple[dict[str, Any], ...]


class TaskRepository:
    def __init__(self, store: OperationalStore | None = None):
        self.store = store or OperationalStore()

    def upsert_review_task(
        self,
        *,
        source_id: str,
        evidence_id: str,
        as_of: str,
        owner_workspace: str,
        action: str,
        priority: str = "P1",
        status: str = "open",
        task_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> TaskQueueItem:
        record = TaskRecord(
            task_id=task_id or _stable_id("task", owner_workspace, source_id, evidence_id, action, as_of),
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace=owner_workspace,
            action=action,
            status=status,
            priority=priority,
            human_review_required=True,
            metadata=metadata or {},
        )
        self.store.upsert_task(record)
        return self.get(record.task_id)

    def set_status(self, task_id: str, status: str) -> TaskQueueItem:
        current = self.get(task_id)
        record = TaskRecord(
            task_id=current.task_id,
            source_id=current.source_id,
            evidence_id=current.evidence_id,
            as_of=current.as_of,
            owner_workspace=current.owner_workspace,
            action=current.action,
            status=status,
            priority=current.priority,
            human_review_required=current.human_review_required,
        )
        self.store.upsert_task(record)
        return self.get(task_id)

    def open_items(self, *, workspace: str | None = None) -> list[TaskQueueItem]:
        rows = [self._item(row) for row in self.store.table_rows("task_records")]
        open_rows = [row for row in rows if row.status.lower() in {"open", "queued", "running"}]
        if workspace:
            open_rows = [row for row in open_rows if row.owner_workspace == workspace]
        return sorted(open_rows, key=lambda row: (row.priority, row.task_id))

    def get(self, task_id: str) -> TaskQueueItem:
        for row in self.store.table_rows("task_records"):
            if row["task_id"] == task_id:
                return self._item(row)
        raise KeyError(task_id)

    @staticmethod
    def _item(row: dict[str, Any]) -> TaskQueueItem:
        return TaskQueueItem(
            task_id=str(row["task_id"]),
            priority=str(row["priority"]),
            status=str(row["status"]),
            owner_workspace=str(row["owner_workspace"]),
            action=str(row["action"]),
            source_id=str(row["source_id"]),
            evidence_id=str(row["evidence_id"]),
            as_of=str(row["as_of"]),
            human_review_required=bool(row["human_review_required"]),
        )


class HoldingSnapshotRepository:
    def __init__(self, store: OperationalStore | None = None):
        self.store = store or OperationalStore()

    def upsert_snapshot(
        self,
        *,
        source_id: str,
        evidence_id: str,
        as_of: str,
        portfolio_id: str,
        holdings: Iterable[dict[str, Any]],
        snapshot_id: str = "",
        domain: DataDomain = DataDomain.PRIVATE_USER,
    ) -> HoldingSnapshot:
        holding_rows = tuple(_clean_holding_row(row) for row in holdings)
        resolved_snapshot_id = snapshot_id or _stable_id("holdingSnapshot", portfolio_id, source_id, evidence_id, as_of)
        self.store.upsert_holding_snapshot(
            snapshot_id=resolved_snapshot_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            portfolio_id=portfolio_id,
            holdings=list(holding_rows),
            domain=domain,
        )
        return self.get(resolved_snapshot_id)

    def latest_for_portfolio(self, portfolio_id: str) -> HoldingSnapshot | None:
        matches = [self._snapshot(row) for row in self.store.table_rows("holding_snapshots") if row["portfolio_id"] == portfolio_id]
        if not matches:
            return None
        return sorted(matches, key=lambda row: (row.as_of, row.snapshot_id), reverse=True)[0]

    def get(self, snapshot_id: str) -> HoldingSnapshot:
        for row in self.store.table_rows("holding_snapshots"):
            if row["snapshot_id"] == snapshot_id:
                return self._snapshot(row)
        raise KeyError(snapshot_id)

    @staticmethod
    def _snapshot(row: dict[str, Any]) -> HoldingSnapshot:
        holdings = json.loads(str(row["holdings_json"] or "[]"))
        return HoldingSnapshot(
            snapshot_id=str(row["snapshot_id"]),
            portfolio_id=str(row["portfolio_id"]),
            as_of=str(row["as_of"]),
            source_id=str(row["source_id"]),
            evidence_id=str(row["evidence_id"]),
            data_domain=str(row["data_domain"]),
            holdings=tuple(holdings),
        )


def _clean_holding_row(row: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "symbol",
        "name",
        "market",
        "quantity",
        "cost_basis",
        "position_value",
        "unrealized_pnl",
        "weight",
        "updated_at",
        "source_system",
    }
    return {key: row.get(key, "") for key in allowed if key in row}


def _stable_id(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
