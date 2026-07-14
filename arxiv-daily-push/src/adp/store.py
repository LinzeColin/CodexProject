"""SQLite 存储 —— 事件只增不删，当前状态由查询得出（数据模型.md 原则 1）.

14 张核心表 + FTS5 全文检索（documents/claims/lessons）。
删除只是标记（archived_at）；每域稳定 ID；跨表引用只用 ID。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY, board_id TEXT NOT NULL, name TEXT NOT NULL,
  policy_snapshot_json TEXT NOT NULL DEFAULT '{}',
  health TEXT NOT NULL DEFAULT 'active',
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  weight REAL NOT NULL DEFAULT 100, archived_at TEXT
);

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
  stable_id TEXT NOT NULL, canonical_url TEXT NOT NULL,
  title TEXT NOT NULL, content_hash TEXT NOT NULL,
  first_seen_at TEXT NOT NULL, archived_at TEXT
);

CREATE TABLE IF NOT EXISTS doc_versions (
  id TEXT PRIMARY KEY, doc_id TEXT NOT NULL REFERENCES documents(id),
  version_no INTEGER NOT NULL, versioned_id TEXT NOT NULL,
  published_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  metadata_json TEXT NOT NULL, diff_note TEXT NOT NULL DEFAULT '',
  retrieved_at TEXT NOT NULL,
  UNIQUE (doc_id, version_no)
);

CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY, doc_version_id TEXT NOT NULL REFERENCES doc_versions(id),
  type TEXT NOT NULL CHECK (type IN ('paper_fact','author_claim','inference','hypothesis','action')),
  text TEXT NOT NULL, locator_json TEXT NOT NULL, confidence REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'active', archived_at TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
  id TEXT PRIMARY KEY, doc_id TEXT NOT NULL REFERENCES documents(id),
  board_id TEXT NOT NULL, as_of_date TEXT NOT NULL,
  features_json TEXT NOT NULL DEFAULT '{}',
  gate_results_json TEXT NOT NULL DEFAULT '{}',
  archived_at TEXT,
  UNIQUE (doc_id, as_of_date)
);

CREATE TABLE IF NOT EXISTS selections (
  run_id TEXT NOT NULL, as_of_date TEXT NOT NULL, candidate_id TEXT,
  score REAL, contributions_json TEXT NOT NULL DEFAULT '{}',
  why TEXT NOT NULL DEFAULT '', why_not_next TEXT NOT NULL DEFAULT '',
  runner_up_id TEXT, runner_up_score REAL,
  abstain INTEGER NOT NULL DEFAULT 0, abstain_reason TEXT,
  params_json TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (run_id)
);

CREATE TABLE IF NOT EXISTS lessons (
  id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL,
  doc_version_id TEXT NOT NULL REFERENCES doc_versions(id),
  as_of_date TEXT NOT NULL, sections_json TEXT NOT NULL,
  claim_bindings_json TEXT NOT NULL, template_ver TEXT NOT NULL,
  generator TEXT NOT NULL, created_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open', reopened_reason TEXT, archived_at TEXT
);

CREATE TABLE IF NOT EXISTS learning_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN
    ('recall_reveal','self_grade','manual_mark','manual_undo','delivery',
     'correction_reopen','transfer_result','skip')),
  grade INTEGER, payload_json TEXT NOT NULL DEFAULT '{}',
  actor TEXT NOT NULL DEFAULT 'owner', at TEXT NOT NULL,
  undone_by INTEGER
);

CREATE TABLE IF NOT EXISTS review_state (
  item_id TEXT PRIMARY KEY, card_json TEXT NOT NULL,
  stability REAL, difficulty REAL, due_at TEXT,
  fsrs_params_ver TEXT NOT NULL, updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT, item_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('practice','asset','outcome')),
  payload_json TEXT NOT NULL DEFAULT '{}', outcome TEXT, at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS debts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL CHECK (kind IN ('contradiction','overdue','unapplied','evidence_stale')),
  ref_id TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open', opened_at TEXT NOT NULL, closed_at TEXT
);

CREATE TABLE IF NOT EXISTS corrections (
  id INTEGER PRIMARY KEY AUTOINCREMENT, doc_version_id TEXT NOT NULL,
  kind TEXT NOT NULL, affected_ids_json TEXT NOT NULL DEFAULT '[]',
  diff_note TEXT NOT NULL DEFAULT '', notified_at TEXT, resolved INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_manifests (
  run_id TEXT PRIMARY KEY, manifest_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS config_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT NOT NULL,
  old_json TEXT NOT NULL, new_json TEXT NOT NULL,
  proposal_src TEXT NOT NULL, replay_ref TEXT, receipt TEXT NOT NULL, at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deliveries (
  idempotency_key TEXT PRIMARY KEY, item_id TEXT NOT NULL,
  channel TEXT NOT NULL, rendered_path TEXT, authorized INTEGER NOT NULL,
  result TEXT NOT NULL, at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS legacy_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
  ref TEXT NOT NULL, payload_json TEXT NOT NULL, migrated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enrichments (
  id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT NOT NULL,
  payload_json TEXT NOT NULL, fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_item ON learning_events(item_id, at);
CREATE INDEX IF NOT EXISTS idx_versions_doc ON doc_versions(doc_id, version_no);
CREATE INDEX IF NOT EXISTS idx_claims_docver ON claims(doc_version_id);
CREATE INDEX IF NOT EXISTS idx_candidates_date ON candidates(as_of_date);
"""

_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_documents USING fts5(doc_id UNINDEXED, title, summary);
CREATE VIRTUAL TABLE IF NOT EXISTS fts_claims USING fts5(claim_id UNINDEXED, text);
CREATE VIRTUAL TABLE IF NOT EXISTS fts_lessons USING fts5(lesson_id UNINDEXED, body);
"""


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or (config.data_dir() / "adp.sqlite3")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    try:
        conn.executescript(_FTS)
    except sqlite3.OperationalError:  # FTS5 缺失时降级：检索功能不可用，闭环不阻塞
        pass
    conn.execute(
        "INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()
    return conn


def upsert_source(conn: sqlite3.Connection, *, source_id: str, board_id: str, name: str,
                  policy_snapshot: dict[str, Any] | None = None) -> None:
    conn.execute(
        """INSERT INTO sources (id, board_id, name, policy_snapshot_json)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET policy_snapshot_json = excluded.policy_snapshot_json""",
        (source_id, board_id, name, json.dumps(policy_snapshot or {}, ensure_ascii=False)),
    )


def record_source_health(conn: sqlite3.Connection, source_id: str, *, ok: bool) -> str:
    """来源健康事件：连续 3 天失败自动停用（功能清单·发现域）."""
    row = conn.execute("SELECT consecutive_failures FROM sources WHERE id=?", (source_id,)).fetchone()
    failures = 0 if ok else (int(row["consecutive_failures"]) + 1 if row else 1)
    health = "active" if ok else ("disabled_auto" if failures >= 3 else "degraded")
    conn.execute(
        "UPDATE sources SET consecutive_failures=?, health=? WHERE id=?",
        (failures, health, source_id),
    )
    return health


def ingest_document(conn: sqlite3.Connection, item: dict[str, Any]) -> tuple[str, str, bool, bool]:
    """标准化文档入库；返回 (doc_id, doc_version_id, is_new_doc, is_new_version).

    去重/版本链: 同 stable_id 只有一个 document；同版本号幂等跳过（不变量 6 的发现域面）。
    """
    meta = item["metadata"]["arxiv"]
    stable_id = item["stable_id"]
    doc_id = item["source_id"]
    versioned_id = meta["versioned_id"]
    version_no = _version_no(versioned_id)
    content_hash = _content_hash(item)

    existing = conn.execute("SELECT id FROM documents WHERE id=?", (doc_id,)).fetchone()
    is_new_doc = existing is None
    if is_new_doc:
        conn.execute(
            """INSERT INTO documents (id, source_id, stable_id, canonical_url, title, content_hash, first_seen_at)
               VALUES (?, 'SRC-ARXIV', ?, ?, ?, ?, ?)""",
            (doc_id, stable_id, item["canonical_url"], item["title"], content_hash, item["retrieved_at"]),
        )
        try:
            conn.execute(
                "INSERT INTO fts_documents (doc_id, title, summary) VALUES (?, ?, ?)",
                (doc_id, item["title"], meta.get("summary", "")),
            )
        except sqlite3.OperationalError:
            pass

    version_id = f"{doc_id}#v{version_no}"
    existing_version = conn.execute("SELECT id FROM doc_versions WHERE id=?", (version_id,)).fetchone()
    is_new_version = existing_version is None
    if is_new_version:
        prior = conn.execute(
            "SELECT MAX(version_no) AS v FROM doc_versions WHERE doc_id=?", (doc_id,)
        ).fetchone()
        diff_note = ""
        if prior and prior["v"] is not None and version_no > int(prior["v"]):
            diff_note = f"new version v{prior['v']} -> v{version_no}"
        conn.execute(
            """INSERT INTO doc_versions
               (id, doc_id, version_no, versioned_id, published_at, updated_at, metadata_json, diff_note, retrieved_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (version_id, doc_id, version_no, versioned_id, meta.get("published", ""),
             meta.get("updated", ""), json.dumps(meta, ensure_ascii=False), diff_note, item["retrieved_at"]),
        )
    return doc_id, version_id, is_new_doc, is_new_version


def append_event(conn: sqlite3.Connection, *, item_id: str, kind: str, grade: int | None = None,
                 payload: dict[str, Any] | None = None, actor: str = "owner", at: str | None = None) -> int:
    cursor = conn.execute(
        "INSERT INTO learning_events (item_id, kind, grade, payload_json, actor, at) VALUES (?, ?, ?, ?, ?, ?)",
        (item_id, kind, grade, json.dumps(payload or {}, ensure_ascii=False), actor, at or utcnow_iso()),
    )
    return int(cursor.lastrowid)


def events_for(conn: sqlite3.Connection, item_id: str) -> list[sqlite3.Row]:
    return list(conn.execute(
        "SELECT * FROM learning_events WHERE item_id=? ORDER BY id", (item_id,)
    ))


def search(conn: sqlite3.Connection, table: str, query: str, limit: int = 20) -> list[sqlite3.Row]:
    """三步到原文的第一步：FTS 检索（documents/claims/lessons）."""
    assert table in {"fts_documents", "fts_claims", "fts_lessons"}
    try:
        return list(conn.execute(
            f"SELECT * FROM {table} WHERE {table} MATCH ? LIMIT ?", (query, limit)
        ))
    except sqlite3.OperationalError:
        return []


def _version_no(versioned_id: str) -> int:
    import re

    match = re.search(r"v(\d+)$", versioned_id)
    return int(match.group(1)) if match else 1


def _content_hash(item: dict[str, Any]) -> str:
    import hashlib

    meta = item["metadata"]["arxiv"]
    basis = json.dumps(
        {"title": item["title"], "summary": meta.get("summary", ""), "updated": meta.get("updated", "")},
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def backup(conn: sqlite3.Connection, dest_dir: Path | None = None, keep: int = 30) -> Path:
    """每日备份，30 份滚动（数据永不丢）."""
    dest = (dest_dir or (config.data_dir() / "backups"))
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = dest / f"adp-{stamp}.sqlite3"
    mirror = sqlite3.connect(target)
    with mirror:
        conn.backup(mirror)
    mirror.close()
    existing = sorted(dest.glob("adp-*.sqlite3"))
    for stale in existing[:-keep]:
        stale.unlink()
    return target
