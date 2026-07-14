"""R6 · 本机 ↔ Cloudflare 混合部署（本机为主，云端只做门面/镜像/回传队列）.

- push：本地 SQLite → D1 只读镜像（单向，wrangler d1 execute --remote，复用 Owner 已授权的 wrangler 会话）
- pull：D1 events_inbox → 本机 grade_recall（显式防重键 cloud:<id>，云评分过本机 FSRS）
- snapshot：每周备份上传 R2（账户未启用 R2 时降级本地并如实报告）
故障模型：云端挂 → 本机闭环无感；push/pull 失败只降级不阻塞。
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from . import config, store

DEPLOY_DIR = config.PROJECT_ROOT / "deploy" / "cloudflare"
OWNER_KEY_PATH = config.DATA_DIR / "authorization" / "cloud_owner_key.txt"


def _wrangler(args: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(["npx", "wrangler", *args], cwd=DEPLOY_DIR,
                          capture_output=True, text=True, timeout=timeout)


def _sql_quote(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def build_push_sql(conn: sqlite3.Connection) -> str:
    """从本地库导出镜像表的整体重建 SQL（幂等：先清后插）."""
    from .review import learning_state

    statements: list[str] = [
        "DELETE FROM lessons_mirror;", "DELETE FROM selections_mirror;",
        "DELETE FROM manifests_mirror;", "DELETE FROM review_mirror;",
    ]
    for row in conn.execute(
        """SELECT l.id, l.as_of_date, l.sections_json, l.generator, l.status, l.template_ver,
                  d.title, d.canonical_url
           FROM lessons l JOIN doc_versions v ON v.id = l.doc_version_id
           JOIN documents d ON d.id = v.doc_id
           WHERE l.archived_at IS NULL ORDER BY l.as_of_date DESC LIMIT 60"""
    ):
        statements.append(
            "INSERT INTO lessons_mirror (id, as_of_date, doc_title, canonical_url, sections_json, generator, status, template_ver) VALUES ("
            + ", ".join(_sql_quote(v) for v in (
                row["id"], row["as_of_date"], row["title"], row["canonical_url"],
                row["sections_json"], row["generator"], row["status"], row["template_ver"]))
            + ");")
    for row in conn.execute("SELECT * FROM selections ORDER BY as_of_date DESC LIMIT 60"):
        statements.append(
            "INSERT INTO selections_mirror (run_id, as_of_date, score, why, why_not_next, abstain, abstain_reason) VALUES ("
            + ", ".join(_sql_quote(v) for v in (
                row["run_id"], row["as_of_date"], row["score"], row["why"],
                row["why_not_next"], row["abstain"], row["abstain_reason"]))
            + ");")
    from .manifest import read_manifests

    for m in read_manifests(30):
        statements.append(
            "INSERT OR REPLACE INTO manifests_mirror (run_id, result, trigger_kind, counts_json, note) VALUES ("
            + ", ".join(_sql_quote(v) for v in (
                m["run_id"], m["result"], m.get("trigger", ""),
                json.dumps(m.get("counts", {}), ensure_ascii=False),
                m.get("note") or m.get("弃权原因") or "；".join(m.get("降级项") or [])))
            + ");")
    for row in conn.execute("SELECT item_id, due_at, stability, difficulty FROM review_state"):
        state = learning_state(conn, row["item_id"])
        statements.append(
            "INSERT INTO review_mirror (item_id, due_at, stability, difficulty, evidence_state, manual_state) VALUES ("
            + ", ".join(_sql_quote(v) for v in (
                row["item_id"], row["due_at"], row["stability"], row["difficulty"],
                state["evidence_state"], state["manual_state"]))
            + ");")
    statements.append(
        "INSERT OR REPLACE INTO mirror_meta (key, value) VALUES ('pushed_at', "
        + _sql_quote(store.utcnow_iso()) + ");")
    # 访问钥匙哈希同步（明文只在本机 data/authorization/cloud_owner_key.txt；轮换=重生成后再 push）
    if OWNER_KEY_PATH.exists():
        import hashlib

        digest = hashlib.sha256(OWNER_KEY_PATH.read_text(encoding="utf-8").strip().encode()).hexdigest()
        statements.append(
            "INSERT OR REPLACE INTO mirror_meta (key, value) VALUES ('owner_key_sha256', "
            + _sql_quote(digest) + ");")
    return "\n".join(statements) + "\n"


def push(conn: sqlite3.Connection) -> dict[str, Any]:
    sql = build_push_sql(conn)
    sql_path = config.data_dir() / "mirror_push.sql"
    sql_path.write_text(sql, encoding="utf-8")
    proc = _wrangler(["d1", "execute", "adp-mirror", "--remote", "--yes",
                      "--file", str(sql_path)])
    ok = proc.returncode == 0
    return {"ok": ok, "statements": sql.count(";"),
            "detail": (proc.stderr or proc.stdout).strip()[-400:] if not ok else "pushed"}


def pull(conn: sqlite3.Connection) -> dict[str, Any]:
    """消费云端回忆评分：cloud:<inbox_id> 防重键 → 本机 FSRS → 标记 applied."""
    from .review import grade_recall

    proc = _wrangler(["d1", "execute", "adp-mirror", "--remote", "--yes", "--json",
                      "--command", "SELECT id, lesson_id, grade, created_at FROM events_inbox WHERE applied=0 ORDER BY id"])
    if proc.returncode != 0:
        return {"ok": False, "detail": (proc.stderr or proc.stdout).strip()[-400:]}
    try:
        payload = json.loads(proc.stdout)
        rows = payload[0]["results"] if payload else []
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        return {"ok": False, "detail": f"parse:{type(exc).__name__}"}

    thresholds = config.load_thresholds()
    applied: list[int] = []
    skipped: list[int] = []
    from datetime import datetime, timezone

    for row in rows:
        at = datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00"))
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        outcome = grade_recall(conn, row["lesson_id"], int(row["grade"]), thresholds,
                               at=at, idempotency_key=f"cloud:{row['id']}")
        (skipped if outcome.get("duplicate") else applied).append(int(row["id"]))
    for inbox_id in applied + skipped:
        _wrangler(["d1", "execute", "adp-mirror", "--remote", "--yes",
                   "--command", f"UPDATE events_inbox SET applied=1 WHERE id={int(inbox_id)}"])
    return {"ok": True, "applied": applied, "duplicates": skipped}


def snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    """每周快照：本地备份 → R2（未启用则降级本地并如实报告）."""
    backup_path = store.backup(conn)
    key = f"weekly/{backup_path.name}"
    proc = _wrangler(["r2", "object", "put", f"adp-snapshots/{key}",
                      "--file", str(backup_path), "--remote"], timeout=300)
    if proc.returncode == 0:
        return {"ok": True, "r2_key": key, "local": str(backup_path)}
    return {"ok": False, "degraded": "r2_not_enabled_or_failed",
            "local": str(backup_path),
            "owner_step": "Cloudflare Dashboard → R2 → Enable（一次性），然后重跑 adp mirror snapshot",
            "detail": (proc.stderr or proc.stdout).strip()[-300:]}
