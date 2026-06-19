import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .config import settings


def _sqlite_path(database_url: Optional[str] = None) -> str:
    url = database_url or settings.database_url
    if not url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:/// URLs are supported in the MVP")
    return url.replace("sqlite:///", "", 1)


@contextmanager
def connect(database_url: Optional[str] = None):
    path = _sqlite_path(database_url)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            country TEXT,
            team_type TEXT NOT NULL DEFAULT 'national',
            fifa_rank INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            season TEXT,
            region TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER REFERENCES competitions(id),
            home_team_id INTEGER NOT NULL REFERENCES teams(id),
            away_team_id INTEGER NOT NULL REFERENCES teams(id),
            match_time TEXT NOT NULL,
            venue TEXT,
            status TEXT NOT NULL DEFAULT 'scheduled',
            home_score INTEGER,
            away_score INTEGER,
            importance INTEGER NOT NULL DEFAULT 3,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS team_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL REFERENCES teams(id),
            matches_played INTEGER NOT NULL DEFAULT 0,
            recent_points INTEGER NOT NULL DEFAULT 0,
            recent_goals_for REAL NOT NULL DEFAULT 0,
            recent_goals_against REAL NOT NULL DEFAULT 0,
            home_win_rate REAL,
            away_win_rate REAL,
            injury_impact REAL NOT NULL DEFAULT 0,
            fatigue_index REAL NOT NULL DEFAULT 0,
            news_sentiment REAL NOT NULL DEFAULT 0,
            trend_score REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER REFERENCES teams(id),
            match_id INTEGER REFERENCES matches(id),
            title TEXT NOT NULL,
            url TEXT,
            source TEXT,
            sentiment REAL NOT NULL DEFAULT 0,
            published_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS model_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            weights_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL REFERENCES matches(id),
            model_version TEXT NOT NULL,
            home_win_probability REAL NOT NULL,
            draw_probability REAL NOT NULL,
            away_win_probability REAL NOT NULL,
            recommended_result TEXT NOT NULL,
            confidence_level TEXT NOT NULL,
            missing_data_warnings TEXT NOT NULL,
            disclaimer TEXT NOT NULL,
            generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS prediction_factors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            formula TEXT NOT NULL,
            weight REAL NOT NULL,
            value REAL NOT NULL,
            effect TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS prediction_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL REFERENCES predictions(id),
            actual_result TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            evaluated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS crawl_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            base_url TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'public',
            terms_note TEXT,
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS crawl_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES crawl_sources(id),
            status TEXT NOT NULL DEFAULT 'queued',
            started_at TEXT,
            finished_at TEXT,
            summary TEXT
        );
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL REFERENCES crawl_jobs(id),
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER REFERENCES matches(id),
            title TEXT NOT NULL,
            content_markdown TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS refresh_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT,
            sources_checked INTEGER NOT NULL DEFAULT 0,
            articles_inserted INTEGER NOT NULL DEFAULT 0,
            matches_refreshed INTEGER NOT NULL DEFAULT 0,
            reports_created INTEGER NOT NULL DEFAULT 0,
            summary TEXT
        );
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO model_versions(version, description, weights_json)
        VALUES (?, ?, ?)
        """,
        (
            settings.model_version,
            "Explainable MVP rules model using form, attack, defense, ranking, home advantage, injuries, fatigue, news, and trends.",
            '{"recent_form":1.4,"attack":0.9,"defense":0.8,"ranking":0.7,"home_advantage":0.35,"injury":0.8,"fatigue":0.5,"news":0.25,"trend":0.2}',
        ),
    )


def rows(conn: sqlite3.Connection, query: str, params: Iterable[Any] = ()) -> List[Dict[str, Any]]:
    return [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]


def row(conn: sqlite3.Connection, query: str, params: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    result = conn.execute(query, tuple(params)).fetchone()
    return dict(result) if result else None
