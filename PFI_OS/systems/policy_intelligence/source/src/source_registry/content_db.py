from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .normalization import normalize_url

CONTENT_SCHEMA_VERSION = 6


def connect_content(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_content_database(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed')),
            mode TEXT NOT NULL DEFAULT 'manual',
            sources_considered INTEGER NOT NULL DEFAULT 0,
            pages_fetched INTEGER NOT NULL DEFAULT 0,
            documents_discovered INTEGER NOT NULL DEFAULT 0,
            new_documents INTEGER NOT NULL DEFAULT 0,
            analyzed_documents INTEGER NOT NULL DEFAULT 0,
            report_path TEXT,
            error_summary TEXT
        );

        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            authority_tier_snapshot TEXT,
            authority_score_snapshot INTEGER,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            canonical_url TEXT NOT NULL UNIQUE,
            document_type TEXT NOT NULL DEFAULT 'webpage',
            published_date TEXT,
            discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            first_seen_run_id TEXT NOT NULL,
            last_seen_run_id TEXT NOT NULL,
            content_hash TEXT,
            snapshot_path TEXT,
            text_excerpt TEXT,
            status TEXT NOT NULL DEFAULT 'discovered'
                CHECK(status IN ('discovered', 'fetched', 'analyzed', 'failed')),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS analyses (
            analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
            analysis_mode TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'zh-en',
            importance_score INTEGER NOT NULL CHECK(importance_score BETWEEN 0 AND 100),
            importance_reason TEXT NOT NULL,
            chinese_summary TEXT NOT NULL,
            english_summary TEXT NOT NULL,
            policy_points_json TEXT NOT NULL,
            business_impacts_json TEXT NOT NULL,
            risks_json TEXT NOT NULL,
            actions_json TEXT NOT NULL,
            raw_analysis TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(document_id, analysis_mode)
        );

        CREATE TABLE IF NOT EXISTS run_documents (
            run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
            document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
            relation TEXT NOT NULL CHECK(relation IN ('discovered', 'analyzed')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(run_id, document_id, relation)
        );

        CREATE TABLE IF NOT EXISTS interpretation_sources (
            interpretation_source_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            platform TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'interpretation',
            url_template TEXT NOT NULL,
            api_url_template TEXT,
            collector_type TEXT NOT NULL DEFAULT 'search_landing',
            max_results INTEGER NOT NULL DEFAULT 3,
            enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1)),
            auth_required INTEGER NOT NULL DEFAULT 0 CHECK(auth_required IN (0, 1)),
            authority_note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS interpretation_items (
            item_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
            document_id TEXT REFERENCES documents(document_id) ON DELETE CASCADE,
            interpretation_source_id TEXT NOT NULL REFERENCES interpretation_sources(interpretation_source_id) ON DELETE CASCADE,
            platform TEXT NOT NULL,
            item_type TEXT NOT NULL DEFAULT 'search_entry',
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            query TEXT NOT NULL,
            evidence_status TEXT NOT NULL DEFAULT 'search_landing',
            summary TEXT,
            author_name TEXT,
            author_url TEXT,
            published_at TEXT,
            duration_seconds INTEGER,
            view_count INTEGER,
            engagement_count INTEGER,
            content_excerpt TEXT,
            relevance_score INTEGER NOT NULL DEFAULT 0 CHECK(relevance_score BETWEEN 0 AND 100),
            raw_metadata_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(run_id, document_id, interpretation_source_id, url)
        );

        CREATE TABLE IF NOT EXISTS report_queue (
            document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
            analysis_mode TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending', 'generated', 'skipped')),
            primary_industry TEXT NOT NULL DEFAULT '待研判行业',
            industry_bucket TEXT NOT NULL DEFAULT '待研判行业',
            industry_rank INTEGER NOT NULL DEFAULT 999,
            administrative_level TEXT,
            level_rank INTEGER NOT NULL DEFAULT 99,
            sort_time TEXT,
            priority_score INTEGER NOT NULL DEFAULT 0,
            first_queued_run_id TEXT,
            generated_run_id TEXT,
            generated_report_path TEXT,
            generated_at TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(document_id, analysis_mode)
        );

        CREATE TABLE IF NOT EXISTS report_timeline (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            document_id TEXT REFERENCES documents(document_id) ON DELETE SET NULL,
            event_type TEXT NOT NULL,
            report_path TEXT,
            primary_industry TEXT,
            administrative_level TEXT,
            details_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS external_reference_gaps (
            gap_id TEXT PRIMARY KEY,
            document_id TEXT REFERENCES documents(document_id) ON DELETE CASCADE,
            interpretation_source_id TEXT REFERENCES interpretation_sources(interpretation_source_id) ON DELETE SET NULL,
            platform TEXT NOT NULL,
            gap_type TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            query TEXT NOT NULL,
            evidence_status TEXT NOT NULL,
            required_action TEXT NOT NULL,
            priority_score INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending', 'resolved', 'ignored')),
            first_seen_run_id TEXT NOT NULL,
            last_seen_run_id TEXT NOT NULL,
            reviewed_by TEXT,
            review_note TEXT,
            reviewed_at TEXT,
            raw_metadata_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(document_id, interpretation_source_id, url, gap_type)
        );
        """
    )
    _migrate_content_database(conn)
    conn.execute(
        """
        INSERT INTO metadata(key, value, updated_at)
        VALUES('schema_version', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
        """,
        (str(CONTENT_SCHEMA_VERSION),),
    )
    conn.commit()


def _migrate_content_database(conn: sqlite3.Connection) -> None:
    _add_columns(
        conn,
        "interpretation_sources",
        {
            "api_url_template": "TEXT",
            "collector_type": "TEXT NOT NULL DEFAULT 'search_landing'",
            "max_results": "INTEGER NOT NULL DEFAULT 3",
        },
    )
    _add_columns(
        conn,
        "interpretation_items",
        {
            "author_name": "TEXT",
            "author_url": "TEXT",
            "published_at": "TEXT",
            "duration_seconds": "INTEGER",
            "view_count": "INTEGER",
            "engagement_count": "INTEGER",
            "content_excerpt": "TEXT",
            "relevance_score": "INTEGER NOT NULL DEFAULT 0",
            "raw_metadata_json": "TEXT",
        },
    )
    _add_columns(
        conn,
        "report_queue",
        {
            "industry_rank": "INTEGER NOT NULL DEFAULT 999",
        },
    )
    _add_columns(
        conn,
        "external_reference_gaps",
        {
            "reviewed_by": "TEXT",
            "review_note": "TEXT",
            "reviewed_at": "TEXT",
            "raw_metadata_json": "TEXT",
        },
    )


def _add_columns(conn: sqlite3.Connection, table: str, columns: Mapping[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def begin_run(conn: sqlite3.Connection, run_id: str, mode: str) -> None:
    conn.execute(
        """
        INSERT INTO pipeline_runs(run_id, status, mode)
        VALUES(?, 'running', ?)
        """,
        (run_id, mode),
    )
    conn.commit()


def next_report_run_id(conn: sqlite3.Connection, now: datetime | None = None) -> str:
    date_part = (now or datetime.now()).strftime("%Y%m%d")
    rows = conn.execute(
        """
        SELECT run_id
        FROM pipeline_runs
        WHERE run_id GLOB ?
        """,
        (f"{date_part}[0-9][0-9]",),
    ).fetchall()
    existing = []
    for row in rows:
        run_id = str(row["run_id"])
        try:
            existing.append(int(run_id[-2:]))
        except ValueError:
            continue
    return f"{date_part}{(max(existing) if existing else 0) + 1:02d}"


def complete_run(
    conn: sqlite3.Connection,
    run_id: str,
    status: str,
    report_path: str | None,
    stats: Mapping[str, int],
    error_summary: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE pipeline_runs
        SET completed_at = CURRENT_TIMESTAMP,
            status = ?,
            sources_considered = ?,
            pages_fetched = ?,
            documents_discovered = ?,
            new_documents = ?,
            analyzed_documents = ?,
            report_path = ?,
            error_summary = ?
        WHERE run_id = ?
        """,
        (
            status,
            int(stats.get("sources_considered", 0)),
            int(stats.get("pages_fetched", 0)),
            int(stats.get("documents_discovered", 0)),
            int(stats.get("new_documents", 0)),
            int(stats.get("analyzed_documents", 0)),
            report_path,
            error_summary,
            run_id,
        ),
    )
    conn.commit()


def reconcile_orphaned_pipeline_runs(
    conn: sqlite3.Connection,
    *,
    reason: str = "orphaned running run reconciled; no active pipeline lock",
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT run_id, started_at
        FROM pipeline_runs
        WHERE status = 'running'
        ORDER BY started_at ASC
        """
    ).fetchall()
    items = [dict(row) for row in rows]
    if not items:
        return []
    conn.execute(
        """
        UPDATE pipeline_runs
        SET status = 'failed',
            completed_at = CURRENT_TIMESTAMP,
            error_summary = ?
        WHERE status = 'running'
        """,
        (reason,),
    )
    conn.commit()
    return items


def make_document_id(url: str) -> str:
    canonical = normalize_url(url)
    return "doc_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def content_hash(text: str | bytes) -> str:
    if isinstance(text, str):
        data = text.encode("utf-8")
    else:
        data = text
    return hashlib.sha256(data).hexdigest()


def upsert_document(conn: sqlite3.Connection, doc: Mapping[str, Any], run_id: str) -> tuple[str, bool]:
    canonical_url = normalize_url(str(doc["url"]))
    document_id = str(doc.get("document_id") or make_document_id(canonical_url))
    existing = conn.execute(
        "SELECT document_id FROM documents WHERE canonical_url = ?", (canonical_url,)
    ).fetchone()
    is_new = existing is None
    if is_new:
        conn.execute(
            """
            INSERT INTO documents (
                document_id,
                source_id,
                source_name,
                source_url,
                authority_tier_snapshot,
                authority_score_snapshot,
                title,
                url,
                canonical_url,
                document_type,
                published_date,
                first_seen_run_id,
                last_seen_run_id,
                content_hash,
                snapshot_path,
                text_excerpt,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                doc["source_id"],
                doc["source_name"],
                doc["source_url"],
                doc.get("authority_tier_snapshot"),
                doc.get("authority_score_snapshot"),
                doc["title"],
                canonical_url,
                canonical_url,
                doc.get("document_type") or "webpage",
                doc.get("published_date"),
                run_id,
                run_id,
                doc.get("content_hash"),
                doc.get("snapshot_path"),
                doc.get("text_excerpt"),
                doc.get("status") or "discovered",
            ),
        )
    else:
        document_id = existing["document_id"]
        conn.execute(
            """
            UPDATE documents
            SET last_seen_run_id = ?,
                title = COALESCE(NULLIF(?, ''), title),
                content_hash = COALESCE(?, content_hash),
                snapshot_path = COALESCE(?, snapshot_path),
                text_excerpt = COALESCE(?, text_excerpt),
                status = CASE WHEN ? = 'fetched' THEN 'fetched' ELSE status END,
                updated_at = CURRENT_TIMESTAMP
            WHERE document_id = ?
            """,
            (
                run_id,
                doc.get("title") or "",
                doc.get("content_hash"),
                doc.get("snapshot_path"),
                doc.get("text_excerpt"),
                doc.get("status"),
                document_id,
            ),
        )
    conn.execute(
        """
        INSERT OR IGNORE INTO run_documents(run_id, document_id, relation)
        VALUES(?, ?, 'discovered')
        """,
        (run_id, document_id),
    )
    conn.commit()
    return document_id, is_new


def upsert_analysis(conn: sqlite3.Connection, analysis: Mapping[str, Any], run_id: str) -> None:
    def as_json(value: Any) -> str:
        return json.dumps(value or [], ensure_ascii=False)

    conn.execute(
        """
        INSERT INTO analyses (
            document_id,
            analysis_mode,
            language,
            importance_score,
            importance_reason,
            chinese_summary,
            english_summary,
            policy_points_json,
            business_impacts_json,
            risks_json,
            actions_json,
            raw_analysis
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(document_id, analysis_mode) DO UPDATE SET
            importance_score = excluded.importance_score,
            importance_reason = excluded.importance_reason,
            chinese_summary = excluded.chinese_summary,
            english_summary = excluded.english_summary,
            policy_points_json = excluded.policy_points_json,
            business_impacts_json = excluded.business_impacts_json,
            risks_json = excluded.risks_json,
            actions_json = excluded.actions_json,
            raw_analysis = excluded.raw_analysis,
            created_at = CURRENT_TIMESTAMP
        """,
        (
            analysis["document_id"],
            analysis["analysis_mode"],
            analysis.get("language", "zh-en"),
            int(analysis["importance_score"]),
            analysis["importance_reason"],
            analysis["chinese_summary"],
            analysis["english_summary"],
            as_json(analysis.get("policy_points")),
            as_json(analysis.get("business_impacts")),
            as_json(analysis.get("risks")),
            as_json(analysis.get("actions")),
            analysis.get("raw_analysis"),
        ),
    )
    conn.execute(
        "UPDATE documents SET status = 'analyzed', updated_at = CURRENT_TIMESTAMP WHERE document_id = ?",
        (analysis["document_id"],),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO run_documents(run_id, document_id, relation)
        VALUES(?, ?, 'analyzed')
        """,
        (run_id, analysis["document_id"]),
    )
    conn.commit()


def documents_for_run(
    conn: sqlite3.Connection,
    run_id: str,
    analysis_mode: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT d.*, a.analysis_mode, a.importance_score, a.importance_reason,
               a.chinese_summary, a.english_summary, a.policy_points_json,
               a.business_impacts_json, a.risks_json, a.actions_json
        FROM documents d
        JOIN run_documents rd ON rd.document_id = d.document_id
        LEFT JOIN analyses a ON a.document_id = d.document_id
            AND a.analysis_mode = ?
        WHERE rd.run_id = ? AND rd.relation = 'discovered'
        ORDER BY COALESCE(a.importance_score, 0) DESC,
                 d.authority_score_snapshot DESC,
                 d.discovered_at ASC
        """,
        (analysis_mode, run_id),
    ).fetchall()
    return [dict(row) for row in rows]


def unanalyzed_documents_for_run(
    conn: sqlite3.Connection,
    run_id: str,
    limit: int,
    analysis_mode: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT d.*
        FROM documents d
        JOIN run_documents rd ON rd.document_id = d.document_id
        LEFT JOIN analyses a ON a.document_id = d.document_id AND a.analysis_mode = ?
        WHERE rd.run_id = ? AND rd.relation = 'discovered'
          AND a.analysis_id IS NULL
        ORDER BY d.authority_score_snapshot DESC, d.discovered_at ASC
        LIMIT ?
        """,
        (analysis_mode, run_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def document_by_id(conn: sqlite3.Connection, document_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM documents WHERE document_id = ?",
        (document_id,),
    ).fetchone()
    if not row:
        raise KeyError(f"document not found: {document_id}")
    return dict(row)


def document_with_analysis(
    conn: sqlite3.Connection,
    document_id: str,
    analysis_mode: str,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT d.*, a.analysis_mode, a.importance_score, a.importance_reason,
               a.chinese_summary, a.english_summary, a.policy_points_json,
               a.business_impacts_json, a.risks_json, a.actions_json
        FROM documents d
        LEFT JOIN analyses a ON a.document_id = d.document_id
            AND a.analysis_mode = ?
        WHERE d.document_id = ?
        """,
        (analysis_mode, document_id),
    ).fetchone()
    if not row:
        raise KeyError(f"document not found: {document_id}")
    return dict(row)


def all_documents(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM documents
        ORDER BY COALESCE(published_date, discovered_at) DESC,
                 authority_score_snapshot DESC,
                 title ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_report_queue_item(conn: sqlite3.Connection, item: Mapping[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO report_queue (
            document_id,
            analysis_mode,
            status,
            primary_industry,
            industry_bucket,
            industry_rank,
            administrative_level,
            level_rank,
            sort_time,
            priority_score,
            first_queued_run_id,
            updated_at
        )
        VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(document_id, analysis_mode) DO UPDATE SET
            primary_industry = excluded.primary_industry,
            industry_bucket = excluded.industry_bucket,
            industry_rank = excluded.industry_rank,
            administrative_level = excluded.administrative_level,
            level_rank = excluded.level_rank,
            sort_time = excluded.sort_time,
            priority_score = excluded.priority_score,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            item["document_id"],
            item["analysis_mode"],
            item.get("primary_industry") or "待研判行业",
            item.get("industry_bucket") or item.get("primary_industry") or "待研判行业",
            int(item.get("industry_rank", 999) or 999),
            item.get("administrative_level"),
            int(item.get("level_rank", 99) or 99),
            item.get("sort_time"),
            int(item.get("priority_score", 0) or 0),
            item.get("first_queued_run_id"),
        ),
    )
    conn.commit()


def mark_report_generated(
    conn: sqlite3.Connection,
    document_id: str,
    analysis_mode: str,
    run_id: str,
    report_path: str,
) -> None:
    conn.execute(
        """
        UPDATE report_queue
        SET status = 'generated',
            generated_run_id = ?,
            generated_report_path = ?,
            generated_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE document_id = ? AND analysis_mode = ?
        """,
        (run_id, report_path, document_id, analysis_mode),
    )
    conn.commit()


def mark_report_skipped(
    conn: sqlite3.Connection,
    document_id: str,
    analysis_mode: str,
) -> None:
    conn.execute(
        """
        UPDATE report_queue
        SET status = 'skipped',
            updated_at = CURRENT_TIMESTAMP
        WHERE document_id = ? AND analysis_mode = ? AND status = 'pending'
        """,
        (document_id, analysis_mode),
    )
    conn.commit()


def queued_reports(
    conn: sqlite3.Connection,
    analysis_mode: str,
    limit: int = 30,
    status: str = "pending",
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT q.*, d.title, d.source_name, d.authority_tier_snapshot,
               d.authority_score_snapshot, d.canonical_url, d.document_type,
               d.discovered_at, d.published_date
        FROM report_queue q
        JOIN documents d ON d.document_id = q.document_id
        WHERE q.analysis_mode = ? AND q.status = ?
        ORDER BY q.industry_rank ASC,
                 q.industry_bucket ASC,
                 COALESCE(q.sort_time, d.published_date, d.discovered_at) DESC,
                 q.level_rank ASC,
                 q.priority_score DESC,
                 d.authority_score_snapshot DESC,
                 d.title ASC
        LIMIT ?
        """,
        (analysis_mode, status, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def append_report_timeline(conn: sqlite3.Connection, event: Mapping[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO report_timeline (
            run_id,
            document_id,
            event_type,
            report_path,
            primary_industry,
            administrative_level,
            details_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["run_id"],
            event.get("document_id"),
            event["event_type"],
            event.get("report_path"),
            event.get("primary_industry"),
            event.get("administrative_level"),
            json.dumps(event.get("details") or {}, ensure_ascii=False),
        ),
    )
    conn.commit()


def report_timeline(conn: sqlite3.Connection, limit: int = 30) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT rt.*, d.title, d.source_name
        FROM report_timeline rt
        LEFT JOIN documents d ON d.document_id = rt.document_id
        ORDER BY rt.created_at DESC, rt.event_id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_external_reference_gap(conn: sqlite3.Connection, gap: Mapping[str, Any]) -> str:
    gap_id = str(gap.get("gap_id") or _external_reference_gap_id(gap))
    existing = conn.execute(
        "SELECT gap_id FROM external_reference_gaps WHERE gap_id = ?",
        (gap_id,),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE external_reference_gaps
            SET platform = ?,
                title = ?,
                query = ?,
                evidence_status = ?,
                required_action = ?,
                priority_score = ?,
                status = CASE
                    WHEN status = 'resolved' THEN 'pending'
                    ELSE status
                END,
                last_seen_run_id = ?,
                raw_metadata_json = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE gap_id = ?
            """,
            (
                gap.get("platform") or "unknown",
                gap.get("title") or "未命名外部参考缺口",
                gap.get("query") or "",
                gap.get("evidence_status") or "",
                gap["required_action"],
                int(gap.get("priority_score", 0) or 0),
                gap["run_id"],
                json.dumps(gap.get("raw_metadata") or {}, ensure_ascii=False),
                gap_id,
            ),
        )
        conn.commit()
        return gap_id
    conn.execute(
        """
        INSERT INTO external_reference_gaps (
            gap_id,
            document_id,
            interpretation_source_id,
            platform,
            gap_type,
            title,
            url,
            query,
            evidence_status,
            required_action,
            priority_score,
            status,
            first_seen_run_id,
            last_seen_run_id,
            raw_metadata_json,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(document_id, interpretation_source_id, url, gap_type) DO UPDATE SET
            platform = excluded.platform,
            title = excluded.title,
            query = excluded.query,
            evidence_status = excluded.evidence_status,
            required_action = excluded.required_action,
            priority_score = excluded.priority_score,
            status = CASE
                WHEN external_reference_gaps.status = 'resolved' THEN 'pending'
                ELSE external_reference_gaps.status
            END,
            last_seen_run_id = excluded.last_seen_run_id,
            raw_metadata_json = excluded.raw_metadata_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            gap_id,
            gap.get("document_id"),
            gap.get("interpretation_source_id"),
            gap.get("platform") or "unknown",
            gap["gap_type"],
            gap.get("title") or "未命名外部参考缺口",
            gap.get("url") or "",
            gap.get("query") or "",
            gap.get("evidence_status") or "",
            gap["required_action"],
            int(gap.get("priority_score", 0) or 0),
            gap["run_id"],
            gap["run_id"],
            json.dumps(gap.get("raw_metadata") or {}, ensure_ascii=False),
        ),
    )
    conn.commit()
    return gap_id


def upsert_external_reference_gaps(
    conn: sqlite3.Connection,
    gaps: list[Mapping[str, Any]],
) -> list[str]:
    gap_ids = [upsert_external_reference_gap(conn, gap) for gap in gaps]
    _resolve_stale_external_reference_gaps(conn, gaps, gap_ids)
    return gap_ids


def _resolve_stale_external_reference_gaps(
    conn: sqlite3.Connection,
    gaps: list[Mapping[str, Any]],
    current_gap_ids: list[str],
) -> None:
    for gap, gap_id in zip(gaps, current_gap_ids):
        conn.execute(
            """
            UPDATE external_reference_gaps
            SET status = 'ignored',
                reviewed_at = CURRENT_TIMESTAMP,
                review_note = COALESCE(review_note, 'auto-ignored: stale query/url superseded by latest recalculation'),
                updated_at = CURRENT_TIMESTAMP
            WHERE status = 'pending'
              AND gap_id != ?
              AND gap_type = ?
              AND ((document_id = ?) OR (document_id IS NULL AND ? IS NULL))
              AND ((interpretation_source_id = ?) OR (interpretation_source_id IS NULL AND ? IS NULL))
            """,
            (
                gap_id,
                str(gap.get("gap_type") or ""),
                gap.get("document_id"),
                gap.get("document_id"),
                gap.get("interpretation_source_id"),
                gap.get("interpretation_source_id"),
            ),
        )
    run_ids = sorted({str(gap.get("run_id") or "") for gap in gaps if gap.get("run_id")})
    for run_id in run_ids:
        ids_for_run = {
            gap_id
            for gap, gap_id in zip(gaps, current_gap_ids)
            if str(gap.get("run_id") or "") == run_id
        }
        if not ids_for_run:
            continue
        placeholders = ",".join("?" for _ in ids_for_run)
        conn.execute(
            f"""
            UPDATE external_reference_gaps
            SET status = 'resolved',
                reviewed_at = CURRENT_TIMESTAMP,
                review_note = COALESCE(review_note, 'auto-resolved: no longer present in latest run recalculation'),
                updated_at = CURRENT_TIMESTAMP
            WHERE last_seen_run_id = ?
              AND status = 'pending'
              AND gap_id NOT IN ({placeholders})
            """,
            [run_id, *sorted(ids_for_run)],
        )
    conn.commit()


def external_reference_gaps_for_run(
    conn: sqlite3.Connection,
    run_id: str,
    limit: int = 30,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT g.*, d.title AS document_title, src.name AS source_name
        FROM external_reference_gaps g
        LEFT JOIN documents d ON d.document_id = g.document_id
        LEFT JOIN interpretation_sources src
            ON src.interpretation_source_id = g.interpretation_source_id
        WHERE g.last_seen_run_id = ?
        ORDER BY g.priority_score DESC, g.updated_at DESC
        LIMIT ?
        """,
        (run_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def pending_external_reference_gaps(
    conn: sqlite3.Connection,
    limit: int = 30,
) -> list[dict[str, Any]]:
    return list_external_reference_gaps(conn, status="pending", limit=limit)


def list_external_reference_gaps(
    conn: sqlite3.Connection,
    status: str | None = "pending",
    required_action: str | None = None,
    gap_type: str | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    where = []
    params: list[Any] = []
    if status and status != "all":
        where.append("g.status = ?")
        params.append(status)
    if required_action:
        where.append("g.required_action = ?")
        params.append(required_action)
    if gap_type:
        where.append("g.gap_type = ?")
        params.append(gap_type)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT g.*, d.title AS document_title, src.name AS source_name
        FROM external_reference_gaps g
        LEFT JOIN documents d ON d.document_id = g.document_id
        LEFT JOIN interpretation_sources src
            ON src.interpretation_source_id = g.interpretation_source_id
        {where_sql}
        ORDER BY g.priority_score DESC, g.updated_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def external_reference_gap_summary(
    conn: sqlite3.Connection,
    status: str = "pending",
) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT gap_type, required_action, COUNT(*) AS count
        FROM external_reference_gaps
        WHERE status = ?
        GROUP BY gap_type, required_action
        ORDER BY count DESC, gap_type ASC
        """,
        (status,),
    ).fetchall()
    total = sum(int(row["count"] or 0) for row in rows)
    return {
        "pending_count": total,
        "by_type": {str(row["gap_type"]): int(row["count"] or 0) for row in rows},
        "by_action": {str(row["required_action"]): int(row["count"] or 0) for row in rows},
    }


def update_external_reference_gap_status(
    conn: sqlite3.Connection,
    gap_id: str,
    status: str,
    reviewer: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    if status not in {"pending", "resolved", "ignored"}:
        raise ValueError(f"invalid gap status: {status}")
    row = conn.execute(
        "SELECT gap_id FROM external_reference_gaps WHERE gap_id = ?",
        (gap_id,),
    ).fetchone()
    if not row:
        raise KeyError(f"external reference gap not found: {gap_id}")
    conn.execute(
        """
        UPDATE external_reference_gaps
        SET status = ?,
            reviewed_by = ?,
            review_note = ?,
            reviewed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE gap_id = ?
        """,
        (status, reviewer, note, gap_id),
    )
    updated = conn.execute(
        """
        SELECT g.*, d.title AS document_title, src.name AS source_name
        FROM external_reference_gaps g
        LEFT JOIN documents d ON d.document_id = g.document_id
        LEFT JOIN interpretation_sources src
            ON src.interpretation_source_id = g.interpretation_source_id
        WHERE g.gap_id = ?
        """,
        (gap_id,),
    ).fetchone()
    conn.commit()
    if not updated:
        raise KeyError(f"external reference gap not found: {gap_id}")
    return dict(updated)


def bulk_update_external_reference_gap_status(
    conn: sqlite3.Connection,
    *,
    status: str,
    from_status: str = "pending",
    required_action: str | None = None,
    gap_type: str | None = None,
    platform: str | None = None,
    reviewer: str | None = None,
    note: str | None = None,
    limit: int = 100,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    if status not in {"pending", "resolved", "ignored"}:
        raise ValueError(f"invalid gap status: {status}")
    candidates = _external_reference_gap_candidates(
        conn,
        from_status=from_status,
        required_action=required_action,
        gap_type=gap_type,
        platform=platform,
        limit=limit,
    )
    if dry_run or not candidates:
        return candidates
    ids = [str(row["gap_id"]) for row in candidates]
    placeholders = ",".join("?" for _ in ids)
    conn.execute(
        f"""
        UPDATE external_reference_gaps
        SET status = ?,
            reviewed_by = ?,
            review_note = ?,
            reviewed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE gap_id IN ({placeholders})
        """,
        [status, reviewer, note, *ids],
    )
    conn.commit()
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""
        SELECT g.*, d.title AS document_title, src.name AS source_name
        FROM external_reference_gaps g
        LEFT JOIN documents d ON d.document_id = g.document_id
        LEFT JOIN interpretation_sources src
            ON src.interpretation_source_id = g.interpretation_source_id
        WHERE g.gap_id IN ({placeholders})
        ORDER BY g.priority_score DESC, g.updated_at DESC
        """,
        ids,
    ).fetchall()
    return [dict(row) for row in rows]


def _external_reference_gap_candidates(
    conn: sqlite3.Connection,
    *,
    from_status: str = "pending",
    required_action: str | None = None,
    gap_type: str | None = None,
    platform: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    where = []
    params: list[Any] = []
    if from_status and from_status != "all":
        where.append("g.status = ?")
        params.append(from_status)
    if required_action:
        where.append("g.required_action = ?")
        params.append(required_action)
    if gap_type:
        where.append("g.gap_type = ?")
        params.append(gap_type)
    if platform:
        where.append("g.platform = ?")
        params.append(platform)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT g.*, d.title AS document_title, src.name AS source_name
        FROM external_reference_gaps g
        LEFT JOIN documents d ON d.document_id = g.document_id
        LEFT JOIN interpretation_sources src
            ON src.interpretation_source_id = g.interpretation_source_id
        {where_sql}
        ORDER BY g.priority_score DESC, g.updated_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_interpretation_source(conn: sqlite3.Connection, source: Mapping[str, Any]) -> str:
    source_id = str(source["interpretation_source_id"])
    conn.execute(
        """
        INSERT INTO interpretation_sources (
            interpretation_source_id,
            name,
            platform,
            source_type,
            url_template,
            api_url_template,
            collector_type,
            max_results,
            enabled,
            auth_required,
            authority_note,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(interpretation_source_id) DO UPDATE SET
            name = excluded.name,
            platform = excluded.platform,
            source_type = excluded.source_type,
            url_template = excluded.url_template,
            api_url_template = excluded.api_url_template,
            collector_type = excluded.collector_type,
            max_results = excluded.max_results,
            enabled = excluded.enabled,
            auth_required = excluded.auth_required,
            authority_note = excluded.authority_note,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            source_id,
            source["name"],
            source["platform"],
            source.get("source_type", "interpretation"),
            source["url_template"],
            source.get("api_url_template"),
            source.get("collector_type", "search_landing"),
            int(source.get("max_results", 3) or 3),
            int(bool(source.get("enabled", True))),
            int(bool(source.get("auth_required", False))),
            source.get("authority_note"),
        ),
    )
    conn.commit()
    return source_id


def list_interpretation_sources(conn: sqlite3.Connection, enabled: bool = True) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM interpretation_sources
        WHERE enabled = ?
        ORDER BY platform, name
        """,
        (int(enabled),),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_interpretation_item(conn: sqlite3.Connection, item: Mapping[str, Any]) -> str:
    item_id = str(item.get("item_id") or _interpretation_item_id(item))
    conn.execute(
        """
        INSERT INTO interpretation_items (
            item_id,
            run_id,
            document_id,
            interpretation_source_id,
            platform,
            item_type,
            title,
            url,
            query,
            evidence_status,
            summary,
            author_name,
            author_url,
            published_at,
            duration_seconds,
            view_count,
            engagement_count,
            content_excerpt,
            relevance_score,
            raw_metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id, document_id, interpretation_source_id, url) DO UPDATE SET
            title = excluded.title,
            query = excluded.query,
            evidence_status = excluded.evidence_status,
            summary = excluded.summary,
            author_name = excluded.author_name,
            author_url = excluded.author_url,
            published_at = excluded.published_at,
            duration_seconds = excluded.duration_seconds,
            view_count = excluded.view_count,
            engagement_count = excluded.engagement_count,
            content_excerpt = excluded.content_excerpt,
            relevance_score = excluded.relevance_score,
            raw_metadata_json = excluded.raw_metadata_json
        """,
        (
            item_id,
            item["run_id"],
            item.get("document_id"),
            item["interpretation_source_id"],
            item["platform"],
            item.get("item_type", "search_entry"),
            item["title"],
            item["url"],
            item["query"],
            item.get("evidence_status", "search_landing"),
            item.get("summary"),
            item.get("author_name"),
            item.get("author_url"),
            item.get("published_at"),
            item.get("duration_seconds"),
            item.get("view_count"),
            item.get("engagement_count"),
            item.get("content_excerpt"),
            int(item.get("relevance_score", 0) or 0),
            json.dumps(item.get("raw_metadata"), ensure_ascii=False)
            if item.get("raw_metadata") is not None
            else item.get("raw_metadata_json"),
        ),
    )
    conn.commit()
    return item_id


def interpretation_items_for_run(conn: sqlite3.Connection, run_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT ii.*, d.title AS document_title, src.name AS source_name,
               src.auth_required, src.authority_note
        FROM interpretation_items ii
        LEFT JOIN documents d ON d.document_id = ii.document_id
        JOIN interpretation_sources src
            ON src.interpretation_source_id = ii.interpretation_source_id
        WHERE ii.run_id = ?
        ORDER BY d.title, ii.platform, ii.title
        """,
        (run_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _interpretation_item_id(item: Mapping[str, Any]) -> str:
    raw = "|".join(
        [
            str(item.get("run_id", "")),
            str(item.get("document_id", "")),
            str(item.get("interpretation_source_id", "")),
            normalize_url(str(item.get("url", ""))),
        ]
    )
    return "mat_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _external_reference_gap_id(gap: Mapping[str, Any]) -> str:
    raw = "|".join(
        [
            str(gap.get("document_id", "")),
            str(gap.get("interpretation_source_id", "")),
            normalize_url(str(gap.get("url", ""))),
            str(gap.get("gap_type", "")),
        ]
    )
    return "gap_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
