from __future__ import annotations

import json
import os
import hashlib
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterator


class DataDomain(str, Enum):
    PUBLIC_SHARED_RAW = "PUBLIC_SHARED_RAW"
    PUBLIC_SHARED_CANONICAL = "PUBLIC_SHARED_CANONICAL"
    PRIVATE_USER = "PRIVATE_USER"
    PRIVATE_DERIVED = "PRIVATE_DERIVED"
    SECRET = "SECRET"
    EPHEMERAL = "EPHEMERAL"


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    domain: DataDomain
    source_type: str
    uri: str
    as_of: str
    evidence_class: str
    observed_at: str = ""
    title: str = ""
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceVersion:
    version_id: str
    source_id: str
    domain: DataDomain
    source_type: str
    uri: str
    as_of: str
    evidence_class: str
    observed_at: str
    title: str = ""
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    source_id: str
    entity_id: str
    as_of: str
    evidence_class: str
    summary: str
    artifact_uri: str = ""
    model_version: str = "DisabledProvider"
    strategy_version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    source_id: str
    as_of: str
    job_type: str
    status: str = "queued"
    phase: str = "queued"
    progress: float = 0.0
    retry_count: int = 0
    error_message: str = ""
    artifact_uri: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    source_id: str
    evidence_id: str
    as_of: str
    owner_workspace: str
    action: str
    status: str = "open"
    priority: str = "P1"
    human_review_required: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


def default_data_home(env: dict[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    configured = str(values.get("PFI_DATA_HOME", "")).strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".pfi"


def default_operational_db_path(data_home: Path | str | None = None) -> Path:
    root = Path(data_home).expanduser() if data_home is not None else default_data_home()
    return root / "private" / "operational" / "pfi.sqlite"


def build_phase_a_data_foundation_contract(data_home: Path | str | None = None) -> dict[str, Any]:
    db_path = default_operational_db_path(data_home)
    return {
        "schema": "PFIOSPhaseADataFoundationContractV1",
        "operational_db_path": str(db_path),
        "data_home_layout": {
            "shared": ["raw", "canonical", "metadata"],
            "private": ["operational", "portfolio", "documents", "notes", "models", "derived"],
            "runtime": ["cache", "jobs", "exports", "backups", "logs"],
        },
        "domains": [item.value for item in DataDomain],
        "official_tables": [
            "source_records",
            "source_versions",
            "entity_records",
            "evidence_records",
            "job_records",
            "task_records",
            "holding_snapshots",
        ],
        "required_fact_fields": ["source_id", "as_of", "evidence_class"],
        "research_bus_role": "internal_event_compatibility_layer",
        "git_policy": "Operational SQLite, private user data, private derived data, secrets, and runtime logs stay outside Git.",
        "no_live_trading": True,
    }


class OperationalStore:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path).expanduser() if db_path is not None else default_operational_db_path()

    def initialize(self) -> Path:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
        return self.db_path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert_source(self, record: SourceRecord) -> SourceRecord:
        self._require_record(record.source_id, "source_id")
        self._require_record(record.as_of, "as_of")
        self._require_record(record.evidence_class, "evidence_class")
        now = _now()
        observed_at = record.observed_at or now
        with self.connect() as conn:
            existing = conn.execute("SELECT as_of FROM source_records WHERE source_id = ?", (record.source_id,)).fetchone()
            if existing is not None and _compare_as_of(record.as_of, str(existing["as_of"])) < 0:
                raise ValueError(
                    "PIT_INVALID_WRITE: source_records cannot be moved backwards in as_of; "
                    "write historical facts through source_versions/backfill flow."
                )
            conn.execute(
                """
                INSERT INTO source_records(
                    source_id, domain, source_type, uri, as_of, evidence_class,
                    observed_at, title, checksum, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    domain=excluded.domain,
                    source_type=excluded.source_type,
                    uri=excluded.uri,
                    as_of=excluded.as_of,
                    evidence_class=excluded.evidence_class,
                    observed_at=excluded.observed_at,
                    title=excluded.title,
                    checksum=excluded.checksum,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                (
                    record.source_id,
                    record.domain.value,
                    record.source_type,
                    record.uri,
                    record.as_of,
                    record.evidence_class,
                    observed_at,
                    record.title,
                    record.checksum,
                    _json(record.metadata),
                    now,
                    now,
                ),
            )
            version_id = _stable_version_id(record.source_id, record.as_of, record.checksum, record.uri)
            conn.execute(
                """
                INSERT OR IGNORE INTO source_versions(
                    version_id, source_id, domain, source_type, uri, as_of, evidence_class,
                    observed_at, title, checksum, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    record.source_id,
                    record.domain.value,
                    record.source_type,
                    record.uri,
                    record.as_of,
                    record.evidence_class,
                    observed_at,
                    record.title,
                    record.checksum,
                    _json(record.metadata),
                    now,
                ),
            )
        return record

    def upsert_entity(self, entity_id: str, *, entity_type: str, display_name: str, canonical_symbol: str = "", metadata: dict[str, Any] | None = None) -> None:
        self._require_record(entity_id, "entity_id")
        now = _now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO entity_records(entity_id, entity_type, display_name, canonical_symbol, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(entity_id) DO UPDATE SET
                    entity_type=excluded.entity_type,
                    display_name=excluded.display_name,
                    canonical_symbol=excluded.canonical_symbol,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                (entity_id, entity_type, display_name, canonical_symbol, _json(metadata or {}), now, now),
            )

    def record_evidence(self, record: EvidenceRecord) -> EvidenceRecord:
        self._require_record(record.evidence_id, "evidence_id")
        self._require_record(record.source_id, "source_id")
        self._require_record(record.as_of, "as_of")
        self._require_record(record.evidence_class, "evidence_class")
        now = _now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence_records(
                    evidence_id, source_id, entity_id, as_of, evidence_class, summary,
                    artifact_uri, model_version, strategy_version, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(evidence_id) DO UPDATE SET
                    source_id=excluded.source_id,
                    entity_id=excluded.entity_id,
                    as_of=excluded.as_of,
                    evidence_class=excluded.evidence_class,
                    summary=excluded.summary,
                    artifact_uri=excluded.artifact_uri,
                    model_version=excluded.model_version,
                    strategy_version=excluded.strategy_version,
                    metadata_json=excluded.metadata_json
                """,
                (
                    record.evidence_id,
                    record.source_id,
                    record.entity_id,
                    record.as_of,
                    record.evidence_class,
                    record.summary,
                    record.artifact_uri,
                    record.model_version,
                    record.strategy_version,
                    _json(record.metadata),
                    now,
                ),
            )
        return record

    def upsert_job(self, record: JobRecord) -> JobRecord:
        self._require_record(record.job_id, "job_id")
        self._require_record(record.source_id, "source_id")
        self._require_record(record.as_of, "as_of")
        now = _now()
        progress = min(max(float(record.progress), 0.0), 1.0)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO job_records(
                    job_id, source_id, as_of, job_type, status, phase, progress,
                    retry_count, error_message, artifact_uri, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    source_id=excluded.source_id,
                    as_of=excluded.as_of,
                    job_type=excluded.job_type,
                    status=excluded.status,
                    phase=excluded.phase,
                    progress=excluded.progress,
                    retry_count=excluded.retry_count,
                    error_message=excluded.error_message,
                    artifact_uri=excluded.artifact_uri,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                (
                    record.job_id,
                    record.source_id,
                    record.as_of,
                    record.job_type,
                    record.status,
                    record.phase,
                    progress,
                    int(record.retry_count),
                    record.error_message,
                    record.artifact_uri,
                    _json(record.metadata),
                    now,
                    now,
                ),
            )
        return record

    def upsert_task(self, record: TaskRecord) -> TaskRecord:
        self._require_record(record.task_id, "task_id")
        self._require_record(record.source_id, "source_id")
        self._require_record(record.evidence_id, "evidence_id")
        self._require_record(record.as_of, "as_of")
        now = _now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO task_records(
                    task_id, source_id, evidence_id, as_of, owner_workspace, action,
                    status, priority, human_review_required, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    source_id=excluded.source_id,
                    evidence_id=excluded.evidence_id,
                    as_of=excluded.as_of,
                    owner_workspace=excluded.owner_workspace,
                    action=excluded.action,
                    status=excluded.status,
                    priority=excluded.priority,
                    human_review_required=excluded.human_review_required,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                (
                    record.task_id,
                    record.source_id,
                    record.evidence_id,
                    record.as_of,
                    record.owner_workspace,
                    record.action,
                    record.status,
                    record.priority,
                    int(record.human_review_required),
                    _json(record.metadata),
                    now,
                    now,
                ),
            )
        return record

    def upsert_holding_snapshot(
        self,
        *,
        snapshot_id: str,
        source_id: str,
        evidence_id: str,
        as_of: str,
        portfolio_id: str,
        holdings: list[dict[str, Any]],
        domain: DataDomain = DataDomain.PRIVATE_USER,
    ) -> None:
        self._require_record(snapshot_id, "snapshot_id")
        self._require_record(source_id, "source_id")
        self._require_record(evidence_id, "evidence_id")
        self._require_record(as_of, "as_of")
        now = _now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO holding_snapshots(
                    snapshot_id, source_id, evidence_id, as_of, portfolio_id, data_domain,
                    holdings_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id) DO UPDATE SET
                    source_id=excluded.source_id,
                    evidence_id=excluded.evidence_id,
                    as_of=excluded.as_of,
                    portfolio_id=excluded.portfolio_id,
                    data_domain=excluded.data_domain,
                    holdings_json=excluded.holdings_json,
                    updated_at=excluded.updated_at
                """,
                (snapshot_id, source_id, evidence_id, as_of, portfolio_id, domain.value, _json(holdings), now, now),
            )

    def table_rows(self, table: str) -> list[dict[str, Any]]:
        if table not in OFFICIAL_TABLES:
            raise ValueError(f"Unknown operational table: {table}")
        with self.connect() as conn:
            rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        return [dict(row) for row in rows]

    def point_in_time_sources(self, as_of: str) -> list[dict[str, Any]]:
        self._require_record(as_of, "as_of")
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM source_versions").fetchall()
        deduped: dict[str, dict[str, Any]] = {}
        for row in rows:
            payload = dict(row)
            if _compare_as_of(str(payload["as_of"]), as_of) > 0:
                continue
            current = deduped.get(str(payload["source_id"]))
            if current is None or _compare_as_of(str(payload["as_of"]), str(current["as_of"])) > 0:
                deduped[str(payload["source_id"])] = payload
        return sorted(deduped.values(), key=lambda item: (str(item["source_type"]), str(item["source_id"]), str(item["version_id"])))

    @staticmethod
    def _require_record(value: str, field_name: str) -> None:
        if not str(value or "").strip():
            raise ValueError(f"{field_name} is required")


OFFICIAL_TABLES = {
    "source_records",
    "source_versions",
    "entity_records",
    "evidence_records",
    "job_records",
    "task_records",
    "holding_snapshots",
}


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS source_records (
  source_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  source_type TEXT NOT NULL,
  uri TEXT NOT NULL,
  as_of TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  checksum TEXT NOT NULL DEFAULT '',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_versions (
  version_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_records(source_id),
  domain TEXT NOT NULL,
  source_type TEXT NOT NULL,
  uri TEXT NOT NULL,
  as_of TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  checksum TEXT NOT NULL DEFAULT '',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_records (
  entity_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  canonical_symbol TEXT NOT NULL DEFAULT '',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_records (
  evidence_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_records(source_id),
  entity_id TEXT NOT NULL,
  as_of TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  summary TEXT NOT NULL,
  artifact_uri TEXT NOT NULL DEFAULT '',
  model_version TEXT NOT NULL DEFAULT '',
  strategy_version TEXT NOT NULL DEFAULT '',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_records (
  job_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_records(source_id),
  as_of TEXT NOT NULL,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL,
  phase TEXT NOT NULL,
  progress REAL NOT NULL DEFAULT 0,
  retry_count INTEGER NOT NULL DEFAULT 0,
  error_message TEXT NOT NULL DEFAULT '',
  artifact_uri TEXT NOT NULL DEFAULT '',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_records (
  task_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_records(source_id),
  evidence_id TEXT NOT NULL REFERENCES evidence_records(evidence_id),
  as_of TEXT NOT NULL,
  owner_workspace TEXT NOT NULL,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  priority TEXT NOT NULL,
  human_review_required INTEGER NOT NULL DEFAULT 1,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS holding_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_records(source_id),
  evidence_id TEXT NOT NULL REFERENCES evidence_records(evidence_id),
  as_of TEXT NOT NULL,
  portfolio_id TEXT NOT NULL,
  data_domain TEXT NOT NULL,
  holdings_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def _json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=_json_default)


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "__fspath__"):
        return os.fspath(value)
    if is_dataclass(value):
        return asdict(value)
    return str(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_as_of(value: str) -> datetime | None:
    clean = str(value or "").strip()
    if not clean:
        return None
    if clean.endswith("Z"):
        clean = f"{clean[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(f"{clean}T00:00:00+00:00")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _compare_as_of(left: str, right: str) -> int:
    left_dt = _parse_as_of(left)
    right_dt = _parse_as_of(right)
    if left_dt is not None and right_dt is not None:
        return (left_dt > right_dt) - (left_dt < right_dt)
    return (str(left) > str(right)) - (str(left) < str(right))


def _stable_version_id(source_id: str, as_of: str, checksum: str, uri: str) -> str:
    raw = "\x1f".join([str(source_id), str(as_of), str(checksum), str(uri)])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"sourceVersion_{digest}"
