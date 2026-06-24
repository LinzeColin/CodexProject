import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from app.core.config import DATABASE_PATH, ensure_runtime_dirs


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    ensure_runtime_dirs()
    conn = sqlite3.connect(db_path or DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def managed_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    with managed_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              role TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cases (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              module TEXT NOT NULL,
              title TEXT NOT NULL,
              input_json TEXT NOT NULL,
              uploaded_file_name TEXT,
              result_json TEXT NOT NULL,
              report_path TEXT,
              report_status TEXT NOT NULL DEFAULT 'pending',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reports (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              case_id INTEGER NOT NULL,
              path TEXT NOT NULL,
              status TEXT NOT NULL,
              message TEXT NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(case_id) REFERENCES cases(id)
            );

            CREATE TABLE IF NOT EXISTS model_provider_configs (
              provider TEXT PRIMARY KEY,
              base_url TEXT NOT NULL DEFAULT '',
              model TEXT NOT NULL DEFAULT '',
              api_key TEXT NOT NULL DEFAULT '',
              enabled INTEGER NOT NULL DEFAULT 0,
              priority INTEGER NOT NULL DEFAULT 100,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS model_call_logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              case_id INTEGER,
              provider TEXT NOT NULL,
              model TEXT NOT NULL,
              status TEXT NOT NULL,
              latency_ms INTEGER NOT NULL DEFAULT 0,
              error TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(case_id) REFERENCES cases(id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              actor TEXT NOT NULL,
              action TEXT NOT NULL,
              entity_type TEXT NOT NULL,
              entity_id TEXT NOT NULL,
              details_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_documents (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              category TEXT NOT NULL,
              source_path TEXT,
              summary TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO model_provider_configs
            (provider, base_url, model, api_key, enabled, priority, updated_at)
            VALUES (?, ?, ?, '', 0, ?, ?)
            """,
            [
                ("deepseek", "https://api.deepseek.com/v1", "deepseek-chat", 10, utc_now()),
                ("qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus", 20, utc_now()),
                ("doubao", "", "doubao-lite", 30, utc_now()),
            ],
        )
        conn.executemany(
            "INSERT OR IGNORE INTO users (username, role, created_at) VALUES (?, ?, ?)",
            [
                ("admin", "admin", utc_now()),
                ("engineer", "engineer", utc_now()),
                ("viewer", "viewer", utc_now()),
            ],
        )


def row_to_case(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "module": row["module"],
        "title": row["title"],
        "input_data": json.loads(row["input_json"]),
        "uploaded_file_name": row["uploaded_file_name"],
        "result": json.loads(row["result_json"]),
        "report_path": row["report_path"],
        "report_status": row["report_status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_case(
    module: str,
    title: str,
    input_data: Dict[str, Any],
    uploaded_file_name: Optional[str],
    result: Dict[str, Any],
) -> int:
    now = utc_now()
    with managed_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO cases
            (module, title, input_json, uploaded_file_name, result_json, report_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                module,
                title,
                json.dumps(input_data, ensure_ascii=False),
                uploaded_file_name,
                json.dumps(result, ensure_ascii=False),
                now,
                now,
            ),
        )
        case_id = int(cur.lastrowid)
    add_audit_log("system", "create_case", "case", str(case_id), {"module": module, "title": title})
    return case_id


def update_case_report(case_id: int, report_path: Optional[str], status: str) -> None:
    with managed_connection() as conn:
        conn.execute(
            "UPDATE cases SET report_path = ?, report_status = ?, updated_at = ? WHERE id = ?",
            (report_path, status, utc_now(), case_id),
        )


def get_case(case_id: int) -> Optional[Dict[str, Any]]:
    with managed_connection() as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    return row_to_case(row) if row else None


def list_cases(limit: int = 50) -> List[Dict[str, Any]]:
    with managed_connection() as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [row_to_case(row) for row in rows]


def add_report(case_id: int, path: str, status: str, message: str) -> None:
    with managed_connection() as conn:
        conn.execute(
            "INSERT INTO reports (case_id, path, status, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (case_id, path, status, message, utc_now()),
        )
    add_audit_log("system", "generate_report", "case", str(case_id), {"status": status, "path": path})


def get_model_configs() -> List[Dict[str, Any]]:
    with managed_connection() as conn:
        rows = conn.execute(
            "SELECT provider, base_url, model, api_key, enabled, priority, updated_at FROM model_provider_configs ORDER BY priority ASC"
        ).fetchall()
    return [
        {
            "provider": row["provider"],
            "base_url": row["base_url"],
            "model": row["model"],
            "api_key": row["api_key"],
            "enabled": bool(row["enabled"]),
            "priority": row["priority"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def replace_model_configs(configs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    with managed_connection() as conn:
        for item in configs:
            conn.execute(
                """
                INSERT INTO model_provider_configs
                (provider, base_url, model, api_key, enabled, priority, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider) DO UPDATE SET
                  base_url=excluded.base_url,
                  model=excluded.model,
                  api_key=excluded.api_key,
                  enabled=excluded.enabled,
                  priority=excluded.priority,
                  updated_at=excluded.updated_at
                """,
                (
                    item["provider"],
                    item.get("base_url", ""),
                    item.get("model", ""),
                    item.get("api_key", ""),
                    1 if item.get("enabled", False) else 0,
                    int(item.get("priority", 100)),
                    utc_now(),
                ),
            )
    add_audit_log("admin", "update_model_settings", "settings", "models", {"providers": [c["provider"] for c in configs]})
    return get_model_configs()


def add_model_call_log(case_id: Optional[int], provider: str, model: str, status: str, latency_ms: int, error: Optional[str]) -> None:
    with managed_connection() as conn:
        conn.execute(
            """
            INSERT INTO model_call_logs (case_id, provider, model, status, latency_ms, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (case_id, provider, model, status, latency_ms, error, utc_now()),
        )


def add_audit_log(actor: str, action: str, entity_type: str, entity_id: str, details: Dict[str, Any]) -> None:
    with managed_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs (actor, action, entity_type, entity_id, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (actor, action, entity_type, entity_id, json.dumps(details, ensure_ascii=False), utc_now()),
        )


def dashboard_summary() -> Dict[str, Any]:
    cases = list_cases(limit=8)
    with managed_connection() as conn:
        total_cases = conn.execute("SELECT COUNT(*) AS n FROM cases").fetchone()["n"]
        report_count = conn.execute("SELECT COUNT(*) AS n FROM cases WHERE report_status = 'ready'").fetchone()["n"]
        risk_rows = conn.execute("SELECT result_json FROM cases").fetchall()
        module_rows = conn.execute("SELECT module, COUNT(*) AS n FROM cases GROUP BY module").fetchall()
    risk_distribution = {"normal": 0, "warning": 0, "critical": 0}
    for row in risk_rows:
        risk = json.loads(row["result_json"]).get("risk_level", "normal")
        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
    module_distribution = {row["module"]: row["n"] for row in module_rows}
    configs = get_model_configs()
    model_health = [
        {
            "provider": item["provider"],
            "model": item["model"],
            "enabled": item["enabled"],
            "status": "configured" if item["enabled"] and item["api_key"] else "offline_rules",
        }
        for item in configs
    ]
    critical = risk_distribution.get("critical", 0)
    warning = risk_distribution.get("warning", 0)
    return {
        "total_cases": total_cases,
        "report_count": report_count,
        "risk_distribution": risk_distribution,
        "module_distribution": module_distribution,
        "recent_cases": [
            {
                "id": c["id"],
                "module": c["module"],
                "title": c["title"],
                "risk_level": c["result"].get("risk_level"),
                "risk_score": c["result"].get("risk_score"),
                "report_status": c["report_status"],
                "created_at": c["created_at"],
            }
            for c in cases
        ],
        "model_health": model_health,
        "kpis": {
            "critical_cases": critical,
            "warning_cases": warning,
            "normal_cases": risk_distribution.get("normal", 0),
            "pdf_coverage": round(report_count / total_cases * 100, 1) if total_cases else 0,
        },
    }
