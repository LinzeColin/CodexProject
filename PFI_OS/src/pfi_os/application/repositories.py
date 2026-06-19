from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from pfi_os.application.operational_store import (
    DataDomain,
    EvidenceRecord,
    JobRecord,
    OperationalStore,
    TaskRecord,
)


@dataclass(frozen=True)
class EntityProfile:
    entity_id: str
    entity_type: str
    display_name: str
    canonical_symbol: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_id: str
    entity_id: str
    as_of: str
    evidence_class: str
    summary: str
    artifact_uri: str
    model_version: str
    strategy_version: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class JobRunItem:
    job_id: str
    source_id: str
    as_of: str
    job_type: str
    status: str
    phase: str
    progress: float
    retry_count: int
    error_message: str
    artifact_uri: str
    metadata: dict[str, Any]


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


class EntityRepository:
    def __init__(self, store: OperationalStore | None = None):
        self.store = store or OperationalStore()

    def upsert_entity(
        self,
        entity_id: str,
        *,
        entity_type: str,
        display_name: str,
        canonical_symbol: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> EntityProfile:
        _require_text(entity_id, "entity_id")
        _require_text(entity_type, "entity_type")
        _require_text(display_name, "display_name")
        self.store.upsert_entity(
            entity_id,
            entity_type=entity_type,
            display_name=display_name,
            canonical_symbol=canonical_symbol,
            metadata=metadata or {},
        )
        return self.get(entity_id)

    def get(self, entity_id: str) -> EntityProfile:
        for row in self.store.table_rows("entity_records"):
            if row["entity_id"] == entity_id:
                return self._profile(row)
        raise KeyError(entity_id)

    def by_symbol(self, symbol: str) -> EntityProfile | None:
        clean = str(symbol or "").strip().upper()
        if not clean:
            return None
        for row in self.store.table_rows("entity_records"):
            values = {str(row.get("entity_id", "")).upper(), str(row.get("canonical_symbol", "")).upper()}
            if clean in values:
                return self._profile(row)
        return None

    def search(self, *, text: str = "", entity_type: str = "", limit: int = 50) -> list[EntityProfile]:
        query = str(text or "").strip().lower()
        type_filter = str(entity_type or "").strip().lower()
        rows = [self._profile(row) for row in self.store.table_rows("entity_records")]
        if query:
            rows = [
                row
                for row in rows
                if query in row.entity_id.lower()
                or query in row.display_name.lower()
                or query in row.canonical_symbol.lower()
            ]
        if type_filter:
            rows = [row for row in rows if row.entity_type.lower() == type_filter]
        return sorted(rows, key=lambda row: (row.entity_type, row.display_name, row.entity_id))[: max(int(limit), 0)]

    @staticmethod
    def _profile(row: dict[str, Any]) -> EntityProfile:
        return EntityProfile(
            entity_id=str(row["entity_id"]),
            entity_type=str(row["entity_type"]),
            display_name=str(row["display_name"]),
            canonical_symbol=str(row["canonical_symbol"]),
            metadata=_json_dict(row.get("metadata_json", "{}")),
        )


class EvidenceRepository:
    def __init__(self, store: OperationalStore | None = None):
        self.store = store or OperationalStore()

    def record(
        self,
        *,
        source_id: str,
        entity_id: str,
        as_of: str,
        evidence_class: str,
        summary: str,
        evidence_id: str = "",
        artifact_uri: str = "",
        model_version: str = "DisabledProvider",
        strategy_version: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceItem:
        _require_text(source_id, "source_id")
        _require_text(entity_id, "entity_id")
        _require_text(as_of, "as_of")
        _require_text(evidence_class, "evidence_class")
        _require_text(summary, "summary")
        resolved_id = evidence_id or _stable_id("evidence", source_id, entity_id, as_of, evidence_class, summary, artifact_uri)
        self.store.record_evidence(
            EvidenceRecord(
                evidence_id=resolved_id,
                source_id=source_id,
                entity_id=entity_id,
                as_of=as_of,
                evidence_class=evidence_class,
                summary=summary,
                artifact_uri=artifact_uri,
                model_version=model_version,
                strategy_version=strategy_version,
                metadata=metadata or {},
            )
        )
        return self.get(resolved_id)

    def get(self, evidence_id: str) -> EvidenceItem:
        for row in self.store.table_rows("evidence_records"):
            if row["evidence_id"] == evidence_id:
                return self._item(row)
        raise KeyError(evidence_id)

    def latest_for_entity(self, entity_id: str, *, evidence_class: str = "") -> EvidenceItem | None:
        rows = self.search(entity_id=entity_id, evidence_class=evidence_class, limit=1)
        return rows[0] if rows else None

    def search(
        self,
        *,
        entity_id: str = "",
        source_id: str = "",
        evidence_class: str = "",
        text: str = "",
        limit: int = 50,
    ) -> list[EvidenceItem]:
        rows = [self._item(row) for row in self.store.table_rows("evidence_records")]
        if entity_id:
            rows = [row for row in rows if row.entity_id == entity_id]
        if source_id:
            rows = [row for row in rows if row.source_id == source_id]
        if evidence_class:
            rows = [row for row in rows if row.evidence_class == evidence_class]
        query = str(text or "").strip().lower()
        if query:
            rows = [
                row
                for row in rows
                if query in row.summary.lower()
                or query in row.evidence_class.lower()
                or query in row.entity_id.lower()
                or query in row.artifact_uri.lower()
            ]
        return sorted(rows, key=lambda row: (row.as_of, row.evidence_id), reverse=True)[: max(int(limit), 0)]

    @staticmethod
    def _item(row: dict[str, Any]) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=str(row["evidence_id"]),
            source_id=str(row["source_id"]),
            entity_id=str(row["entity_id"]),
            as_of=str(row["as_of"]),
            evidence_class=str(row["evidence_class"]),
            summary=str(row["summary"]),
            artifact_uri=str(row["artifact_uri"]),
            model_version=str(row["model_version"]),
            strategy_version=str(row["strategy_version"]),
            metadata=_json_dict(row.get("metadata_json", "{}")),
        )


class JobRepository:
    def __init__(self, store: OperationalStore | None = None):
        self.store = store or OperationalStore()

    def upsert_job(
        self,
        *,
        source_id: str,
        as_of: str,
        job_type: str,
        job_id: str = "",
        status: str = "queued",
        phase: str = "queued",
        progress: float = 0.0,
        retry_count: int = 0,
        error_message: str = "",
        artifact_uri: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> JobRunItem:
        _require_text(source_id, "source_id")
        _require_text(as_of, "as_of")
        _require_text(job_type, "job_type")
        resolved_id = job_id or _stable_id("job", source_id, as_of, job_type)
        self.store.upsert_job(
            JobRecord(
                job_id=resolved_id,
                source_id=source_id,
                as_of=as_of,
                job_type=job_type,
                status=status,
                phase=phase,
                progress=progress,
                retry_count=retry_count,
                error_message=error_message,
                artifact_uri=artifact_uri,
                metadata=metadata or {},
            )
        )
        return self.get(resolved_id)

    def start(
        self,
        *,
        source_id: str,
        as_of: str,
        job_type: str,
        job_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> JobRunItem:
        return self.upsert_job(
            source_id=source_id,
            as_of=as_of,
            job_type=job_type,
            job_id=job_id,
            status="running",
            phase="started",
            progress=0.0,
            metadata=metadata,
        )

    def complete(self, job_id: str, *, artifact_uri: str = "", metadata: dict[str, Any] | None = None) -> JobRunItem:
        current = self.get(job_id)
        merged_metadata = {**current.metadata, **(metadata or {})}
        return self.upsert_job(
            source_id=current.source_id,
            as_of=current.as_of,
            job_type=current.job_type,
            job_id=current.job_id,
            status="completed",
            phase="done",
            progress=1.0,
            retry_count=current.retry_count,
            artifact_uri=artifact_uri or current.artifact_uri,
            metadata=merged_metadata,
        )

    def fail(self, job_id: str, *, error_message: str, phase: str = "error") -> JobRunItem:
        current = self.get(job_id)
        return self.upsert_job(
            source_id=current.source_id,
            as_of=current.as_of,
            job_type=current.job_type,
            job_id=current.job_id,
            status="failed",
            phase=phase,
            progress=current.progress,
            retry_count=current.retry_count + 1,
            error_message=error_message,
            artifact_uri=current.artifact_uri,
            metadata=current.metadata,
        )

    def active_jobs(self, *, job_type: str = "") -> list[JobRunItem]:
        rows = [self._item(row) for row in self.store.table_rows("job_records")]
        rows = [row for row in rows if row.status.lower() in {"queued", "running", "retrying"}]
        if job_type:
            rows = [row for row in rows if row.job_type == job_type]
        return sorted(rows, key=lambda row: (row.as_of, row.job_id), reverse=True)

    def get(self, job_id: str) -> JobRunItem:
        for row in self.store.table_rows("job_records"):
            if row["job_id"] == job_id:
                return self._item(row)
        raise KeyError(job_id)

    @staticmethod
    def _item(row: dict[str, Any]) -> JobRunItem:
        return JobRunItem(
            job_id=str(row["job_id"]),
            source_id=str(row["source_id"]),
            as_of=str(row["as_of"]),
            job_type=str(row["job_type"]),
            status=str(row["status"]),
            phase=str(row["phase"]),
            progress=float(row["progress"]),
            retry_count=int(row["retry_count"]),
            error_message=str(row["error_message"]),
            artifact_uri=str(row["artifact_uri"]),
            metadata=_json_dict(row.get("metadata_json", "{}")),
        )


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


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _require_text(value: str, field_name: str) -> None:
    if not str(value or "").strip():
        raise ValueError(f"{field_name} is required")
