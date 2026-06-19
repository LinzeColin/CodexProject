from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .normalization import canonical_domain, make_source_id, normalize_url
from .scoring import SCORING_VERSION, score_source, tier_for_score

SCHEMA_VERSION = 1


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            country_code TEXT NOT NULL DEFAULT 'CN',
            country_name TEXT NOT NULL DEFAULT 'China',
            region TEXT,
            administrative_level TEXT NOT NULL DEFAULT 'unknown',
            source_type TEXT NOT NULL DEFAULT 'other',
            parent_authority TEXT,
            sponsor_unit TEXT,
            supervisor_unit TEXT,
            official_url TEXT NOT NULL,
            canonical_domain TEXT NOT NULL,
            publishes_original_documents INTEGER NOT NULL DEFAULT 1,
            crawl_enabled INTEGER NOT NULL DEFAULT 0,
            crawl_priority INTEGER NOT NULL DEFAULT 50,
            review_status TEXT NOT NULL DEFAULT 'unreviewed'
                CHECK (review_status IN (
                    'unreviewed',
                    'system_scored',
                    'user_confirmed',
                    'rejected',
                    'needs_review'
                )),
            status TEXT NOT NULL DEFAULT 'candidate'
                CHECK (status IN ('candidate', 'active', 'inactive', 'rejected')),
            first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TEXT,
            last_crawl_success_at TEXT,
            last_crawl_error_at TEXT,
            crawl_failure_count INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS source_evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
            evidence_type TEXT NOT NULL,
            evidence_value TEXT NOT NULL,
            evidence_url TEXT NOT NULL DEFAULT '',
            confidence INTEGER NOT NULL DEFAULT 100
                CHECK (confidence BETWEEN 0 AND 100),
            verified_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_id, evidence_type, evidence_value, evidence_url)
        );

        CREATE TABLE IF NOT EXISTS authority_scores (
            score_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
            system_score INTEGER NOT NULL CHECK (system_score BETWEEN 0 AND 100),
            final_score INTEGER CHECK (final_score BETWEEN 0 AND 100),
            tier_system TEXT NOT NULL CHECK (tier_system IN ('A', 'B', 'C', 'D', 'E')),
            tier_final TEXT CHECK (tier_final IN ('A', 'B', 'C', 'D', 'E')),
            identity_evidence_score INTEGER NOT NULL CHECK (identity_evidence_score BETWEEN 0 AND 30),
            institution_level_score INTEGER NOT NULL CHECK (institution_level_score BETWEEN 0 AND 25),
            original_publisher_score INTEGER NOT NULL CHECK (original_publisher_score BETWEEN 0 AND 20),
            traceability_score INTEGER NOT NULL CHECK (traceability_score BETWEEN 0 AND 15),
            stability_score INTEGER NOT NULL CHECK (stability_score BETWEEN 0 AND 10),
            scoring_version TEXT NOT NULL DEFAULT 'authority-v1',
            scoring_details_json TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            scored_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_authority_scores_one_active
            ON authority_scores(source_id)
            WHERE active = 1;

        CREATE TABLE IF NOT EXISTS source_aliases (
            alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
            alias_type TEXT NOT NULL,
            alias_value TEXT NOT NULL,
            alias_url TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_id, alias_type, alias_value, alias_url)
        );

        CREATE TABLE IF NOT EXISTS source_review_log (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
            action TEXT NOT NULL,
            old_final_score INTEGER,
            new_final_score INTEGER,
            old_review_status TEXT,
            new_review_status TEXT,
            reviewer TEXT,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE VIEW IF NOT EXISTS source_authority_current AS
            SELECT
                s.source_id,
                s.name,
                s.country_code,
                s.country_name,
                s.region,
                s.administrative_level,
                s.source_type,
                s.parent_authority,
                s.sponsor_unit,
                s.supervisor_unit,
                s.official_url,
                s.canonical_domain,
                s.crawl_enabled,
                s.crawl_priority,
                s.review_status,
                s.status,
                a.system_score,
                a.final_score,
                COALESCE(a.final_score, a.system_score) AS effective_score,
                a.tier_system,
                a.tier_final,
                COALESCE(a.tier_final, a.tier_system) AS effective_tier,
                a.identity_evidence_score,
                a.institution_level_score,
                a.original_publisher_score,
                a.traceability_score,
                a.stability_score,
                a.scoring_version,
                a.scored_at
            FROM sources s
            LEFT JOIN authority_scores a
                ON a.source_id = s.source_id AND a.active = 1;
        """
    )
    conn.execute(
        """
        INSERT INTO metadata(key, value, updated_at)
        VALUES('schema_version', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
        """,
        (str(SCHEMA_VERSION),),
    )
    conn.commit()


def upsert_source(conn: sqlite3.Connection, source: Mapping[str, Any]) -> str:
    official_url = normalize_url(str(source.get("official_url") or source.get("url") or ""))
    if not official_url:
        raise ValueError("source official_url is required")

    country_code = str(source.get("country_code") or "CN").upper()
    source_id = str(source.get("source_id") or make_source_id(country_code, official_url, str(source.get("name") or "")))
    domain = canonical_domain(official_url)
    conn.execute(
        """
        INSERT INTO sources (
            source_id,
            name,
            country_code,
            country_name,
            region,
            administrative_level,
            source_type,
            parent_authority,
            sponsor_unit,
            supervisor_unit,
            official_url,
            canonical_domain,
            publishes_original_documents,
            crawl_enabled,
            crawl_priority,
            review_status,
            status,
            notes,
            last_seen_at,
            updated_at
        )
        VALUES (
            :source_id,
            :name,
            :country_code,
            :country_name,
            :region,
            :administrative_level,
            :source_type,
            :parent_authority,
            :sponsor_unit,
            :supervisor_unit,
            :official_url,
            :canonical_domain,
            :publishes_original_documents,
            :crawl_enabled,
            :crawl_priority,
            :review_status,
            :status,
            :notes,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT(source_id) DO UPDATE SET
            name = excluded.name,
            country_code = excluded.country_code,
            country_name = excluded.country_name,
            region = excluded.region,
            administrative_level = excluded.administrative_level,
            source_type = excluded.source_type,
            parent_authority = excluded.parent_authority,
            sponsor_unit = excluded.sponsor_unit,
            supervisor_unit = excluded.supervisor_unit,
            official_url = excluded.official_url,
            canonical_domain = excluded.canonical_domain,
            publishes_original_documents = excluded.publishes_original_documents,
            crawl_enabled = excluded.crawl_enabled,
            crawl_priority = excluded.crawl_priority,
            status = excluded.status,
            notes = excluded.notes,
            last_seen_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """,
        {
            "source_id": source_id,
            "name": str(source.get("name") or "").strip(),
            "country_code": country_code,
            "country_name": str(source.get("country_name") or "China"),
            "region": source.get("region"),
            "administrative_level": str(source.get("administrative_level") or "unknown"),
            "source_type": str(source.get("source_type") or "other"),
            "parent_authority": source.get("parent_authority"),
            "sponsor_unit": source.get("sponsor_unit"),
            "supervisor_unit": source.get("supervisor_unit"),
            "official_url": official_url,
            "canonical_domain": domain,
            "publishes_original_documents": int(bool(source.get("publishes_original_documents", True))),
            "crawl_enabled": int(bool(source.get("crawl_enabled", False))),
            "crawl_priority": int(source.get("crawl_priority") or 50),
            "review_status": str(source.get("review_status") or "unreviewed"),
            "status": str(source.get("status") or "candidate"),
            "notes": source.get("notes"),
        },
    )
    return source_id


def add_evidence(
    conn: sqlite3.Connection,
    source_id: str,
    evidence_type: str,
    evidence_value: str,
    evidence_url: str | None = None,
    confidence: int = 100,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO source_evidence (
            source_id,
            evidence_type,
            evidence_value,
            evidence_url,
            confidence,
            verified_at
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            source_id,
            evidence_type,
            evidence_value,
            normalize_url(evidence_url) if evidence_url else "",
            confidence,
        ),
    )


def add_alias(
    conn: sqlite3.Connection,
    source_id: str,
    alias_type: str,
    alias_value: str,
    alias_url: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO source_aliases (
            source_id,
            alias_type,
            alias_value,
            alias_url
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            source_id,
            alias_type,
            alias_value,
            normalize_url(alias_url) if alias_url else "",
        ),
    )


def score_one(conn: sqlite3.Connection, source_id: str, preserve_final: bool = True) -> dict[str, Any]:
    source = dict(_get_required_source(conn, source_id))
    evidence = [
        dict(row)
        for row in conn.execute(
        "SELECT * FROM source_evidence WHERE source_id = ?", (source_id,)
        ).fetchall()
    ]
    alias_count = conn.execute(
        "SELECT COUNT(*) AS count FROM source_aliases WHERE source_id = ?",
        (source_id,),
    ).fetchone()["count"]
    previous = conn.execute(
        "SELECT * FROM authority_scores WHERE source_id = ? AND active = 1",
        (source_id,),
    ).fetchone()
    breakdown = score_source(source, evidence, alias_count=alias_count)
    final_score = previous["final_score"] if previous and preserve_final else None
    tier_final = tier_for_score(final_score)

    conn.execute(
        "UPDATE authority_scores SET active = 0 WHERE source_id = ? AND active = 1",
        (source_id,),
    )
    conn.execute(
        """
        INSERT INTO authority_scores (
            source_id,
            system_score,
            final_score,
            tier_system,
            tier_final,
            identity_evidence_score,
            institution_level_score,
            original_publisher_score,
            traceability_score,
            stability_score,
            scoring_version,
            scoring_details_json,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            source_id,
            breakdown.total,
            final_score,
            tier_for_score(breakdown.total),
            tier_final,
            breakdown.identity_evidence_score,
            breakdown.institution_level_score,
            breakdown.original_publisher_score,
            breakdown.traceability_score,
            breakdown.stability_score,
            SCORING_VERSION,
            json.dumps(breakdown.details, ensure_ascii=False, sort_keys=True),
        ),
    )
    conn.execute(
        """
        UPDATE sources
        SET review_status = CASE
                WHEN review_status = 'user_confirmed' THEN review_status
                ELSE 'system_scored'
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE source_id = ?
        """,
        (source_id,),
    )
    conn.commit()
    return get_current_authority(conn, source_id)


def score_all(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT source_id FROM sources ORDER BY crawl_priority, name").fetchall()
    return [score_one(conn, row["source_id"]) for row in rows]


def review_source(
    conn: sqlite3.Connection,
    source_id: str,
    final_score: int | None,
    status: str,
    reviewer: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    if status not in {"user_confirmed", "rejected", "needs_review", "unreviewed", "system_scored"}:
        raise ValueError(f"unsupported review status: {status}")
    if final_score is not None and not 0 <= final_score <= 100:
        raise ValueError("final_score must be between 0 and 100")
    _get_required_source(conn, source_id)
    current = get_current_authority(conn, source_id)
    if current.get("system_score") is None:
        current = score_one(conn, source_id, preserve_final=False)

    old_final = current.get("final_score")
    old_status = current.get("review_status")
    tier_final = tier_for_score(final_score)
    conn.execute(
        """
        UPDATE authority_scores
        SET final_score = ?,
            tier_final = ?
        WHERE source_id = ? AND active = 1
        """,
        (final_score, tier_final, source_id),
    )
    conn.execute(
        """
        UPDATE sources
        SET review_status = ?,
            status = CASE WHEN ? = 'rejected' THEN 'rejected' ELSE status END,
            crawl_enabled = CASE WHEN ? = 'rejected' THEN 0 ELSE crawl_enabled END,
            updated_at = CURRENT_TIMESTAMP
        WHERE source_id = ?
        """,
        (status, status, status, source_id),
    )
    conn.execute(
        """
        INSERT INTO source_review_log (
            source_id,
            action,
            old_final_score,
            new_final_score,
            old_review_status,
            new_review_status,
            reviewer,
            note
        )
        VALUES (?, 'manual_review', ?, ?, ?, ?, ?, ?)
        """,
        (source_id, old_final, final_score, old_status, status, reviewer, note),
    )
    conn.commit()
    return get_current_authority(conn, source_id)


def get_current_authority(conn: sqlite3.Connection, source_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM source_authority_current WHERE source_id = ?",
        (source_id,),
    ).fetchone()
    if not row:
        raise KeyError(f"source not found: {source_id}")
    return dict(row)


def source_snapshot(conn: sqlite3.Connection, source_id: str) -> dict[str, Any]:
    current = get_current_authority(conn, source_id)
    return {
        "source_id": current["source_id"],
        "source_name": current["name"],
        "source_url": current["official_url"],
        "authority_tier_snapshot": current["effective_tier"],
        "authority_score_snapshot": current["effective_score"],
        "authority_score_system": current["system_score"],
        "authority_score_final": current["final_score"],
        "source_type": current["source_type"],
        "sponsor_unit": current["sponsor_unit"],
        "supervisor_unit": current["supervisor_unit"],
        "review_status": current["review_status"],
        "scoring_version": current["scoring_version"],
        "scored_at": current["scored_at"],
    }


def list_sources(
    conn: sqlite3.Connection,
    crawl_enabled: bool | None = None,
    min_score: int | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if crawl_enabled is not None:
        clauses.append("crawl_enabled = ?")
        params.append(int(crawl_enabled))
    if min_score is not None:
        clauses.append("effective_score >= ?")
        params.append(min_score)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT *
        FROM source_authority_current
        {where}
        ORDER BY effective_score DESC NULLS LAST, crawl_priority ASC, name ASC
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def seed_sources(conn: sqlite3.Connection, sources: Iterable[Mapping[str, Any]]) -> list[str]:
    source_ids: list[str] = []
    for source in sources:
        source_id = upsert_source(conn, source)
        for evidence in source.get("evidence", []) or []:
            add_evidence(
                conn,
                source_id,
                str(evidence["type"]),
                str(evidence["value"]),
                evidence.get("url"),
                int(evidence.get("confidence", 100)),
            )
        for alias in source.get("aliases", []) or []:
            add_alias(
                conn,
                source_id,
                str(alias["type"]),
                str(alias["value"]),
                alias.get("url"),
            )
        source_ids.append(source_id)
    conn.commit()
    for source_id in source_ids:
        score_one(conn, source_id)
    return source_ids


def _get_required_source(conn: sqlite3.Connection, source_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM sources WHERE source_id = ?", (source_id,)).fetchone()
    if not row:
        raise KeyError(f"source not found: {source_id}")
    return row
