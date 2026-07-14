"""纠错传播（R2）—— 版本/撤稿检测 → 影响图 → 重开知识项 → 强提醒（不变量 4）.

来源出新版/撤稿 → 找回受影响的声明、讲义、知识项与掌握度 → 重开 + 债务 + 提醒；
纠错提醒不受手动标记豁免（业务规则·手动状态编辑）。
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from . import store

_WITHDRAWN = re.compile(r"withdraw|retract", re.I)


def detect_and_propagate(conn: sqlite3.Connection) -> dict[str, Any]:
    """检测：任何有讲义的文档若出现比讲义所绑版本更新的版本（或撤稿信号）→ 纠错.

    幂等：同一 (讲义, 新版本) 只产生一次纠错。返回计数与明细。
    """
    rows = conn.execute(
        """SELECT l.id AS lesson_id, l.doc_version_id, v.doc_id, v.version_no AS bound_version,
                  nv.id AS new_version_id, nv.version_no AS new_version, nv.diff_note,
                  nv.metadata_json AS new_metadata
           FROM lessons l
           JOIN doc_versions v ON v.id = l.doc_version_id
           JOIN doc_versions nv ON nv.doc_id = v.doc_id AND nv.version_no > v.version_no
           WHERE l.archived_at IS NULL"""
    ).fetchall()

    created: list[dict[str, Any]] = []
    for row in rows:
        exists = conn.execute(
            """SELECT 1 FROM corrections WHERE doc_version_id=? AND affected_ids_json LIKE ?""",
            (row["new_version_id"], f'%{row["lesson_id"]}%'),
        ).fetchone()
        if exists:
            continue
        meta = json.loads(row["new_metadata"])
        withdrawn = bool(_WITHDRAWN.search(meta.get("comment") or "")) or bool(
            _WITHDRAWN.search(meta.get("title") or ""))
        kind = "retraction" if withdrawn else "version_update"

        affected = _affected_graph(conn, row["lesson_id"], row["doc_version_id"])
        diff_note = row["diff_note"] or f"v{row['bound_version']} -> v{row['new_version']}"

        conn.execute(
            """INSERT INTO corrections (doc_version_id, kind, affected_ids_json, diff_note, notified_at, created_at)
               VALUES (?, ?, ?, ?, NULL, ?)""",
            (row["new_version_id"], kind, json.dumps(affected, ensure_ascii=False),
             diff_note, store.utcnow_iso()),
        )
        correction_id = conn.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]

        # 重开知识项：讲义 status → reopened；学习事件记 correction_reopen（掌握度判定随之失效）
        conn.execute(
            "UPDATE lessons SET status='reopened', reopened_reason=? WHERE id=?",
            (f"{kind}: {diff_note}", row["lesson_id"]),
        )
        store.append_event(conn, item_id=row["lesson_id"], kind="correction_reopen",
                           payload={"correction_id": correction_id, "kind": kind,
                                    "new_version": row["new_version"], "diff_note": diff_note},
                           actor="system")
        # 受影响声明标记 superseded（不删除——事件只增不删）
        conn.execute(
            "UPDATE claims SET status='superseded_by_new_version' WHERE doc_version_id=?",
            (row["doc_version_id"],),
        )
        conn.execute(
            "INSERT INTO debts (kind, ref_id, note, opened_at) VALUES ('evidence_stale', ?, ?, ?)",
            (row["lesson_id"], f"{kind}：{diff_note}，需重新复习", store.utcnow_iso()),
        )
        created.append({"correction_id": int(correction_id), "lesson_id": row["lesson_id"],
                        "kind": kind, "diff_note": diff_note, "affected": affected})
    conn.commit()
    return {"corrections_created": len(created), "details": created}


def _affected_graph(conn: sqlite3.Connection, lesson_id: str, doc_version_id: str) -> dict[str, Any]:
    """影响图：受影响的声明/讲义/复习状态/应用记录 ID 全收."""
    claim_ids = [r["id"] for r in conn.execute(
        "SELECT id FROM claims WHERE doc_version_id=?", (doc_version_id,))]
    review = conn.execute("SELECT item_id FROM review_state WHERE item_id=?", (lesson_id,)).fetchone()
    applications = [int(r["id"]) for r in conn.execute(
        "SELECT id FROM applications WHERE item_id=?", (lesson_id,))]
    return {
        "lessons": [lesson_id],
        "claims": claim_ids,
        "review_states": [review["item_id"]] if review else [],
        "applications": applications,
    }


def unresolved(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """未解决纠错（强提醒数据源；resolve 需 Owner 重新复习后显式关闭）."""
    rows = conn.execute(
        "SELECT * FROM corrections WHERE resolved=0 ORDER BY created_at DESC"
    ).fetchall()
    out = []
    for row in rows:
        out.append({
            "id": row["id"], "kind": row["kind"], "diff_note": row["diff_note"],
            "affected": json.loads(row["affected_ids_json"]), "created_at": row["created_at"],
        })
    return out


def mark_notified(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE corrections SET notified_at=? WHERE notified_at IS NULL", (store.utcnow_iso(),))
    conn.commit()


def resolve(conn: sqlite3.Connection, correction_id: int) -> bool:
    """Owner 完成重新复习后关闭纠错；同时关联债务关闭."""
    row = conn.execute("SELECT * FROM corrections WHERE id=? AND resolved=0", (correction_id,)).fetchone()
    if row is None:
        return False
    conn.execute("UPDATE corrections SET resolved=1 WHERE id=?", (correction_id,))
    affected = json.loads(row["affected_ids_json"])
    for lesson_id in affected.get("lessons", []):
        conn.execute(
            "UPDATE debts SET status='closed', closed_at=? WHERE kind='evidence_stale' AND ref_id=? AND status='open'",
            (store.utcnow_iso(), lesson_id),
        )
    conn.commit()
    return True


def migrate_legacy(conn: sqlite3.Connection, repo_root) -> dict[str, Any]:
    """两项迁移（R2）：旧发送记录 → delivery 事件（不映射学会）；旧评分 → 只存档不复算."""
    from pathlib import Path

    repo_root = Path(repo_root)
    migrated = {"legacy_sent": 0, "legacy_scores": 0, "skipped": []}

    manifest_path = repo_root.parent / "governance" / "run_manifests" / \
        "ADP-S2PMT07-AUTHORIZED-CONTROLLED-REAL-RUN-ACCEPTANCE-20260701.json"
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        products = (payload.get("controlled_run_result") or {}).get("historical_sent_mail_products") or []
        for product in products:
            key = f"legacy_email:{product}:2026-07-01"
            if conn.execute("SELECT 1 FROM deliveries WHERE idempotency_key=?", (key,)).fetchone():
                migrated["skipped"].append(key)
                continue
            conn.execute(
                "INSERT INTO deliveries (idempotency_key, item_id, channel, rendered_path, authorized, result, at) "
                "VALUES (?, ?, 'legacy_email', NULL, 1, 'SENT_LEGACY_CONTROLLED_RUN', '2026-07-01T17:12:07+10:00')",
                (key, f"legacy:{product}"),
            )
            store.append_event(conn, item_id=f"legacy:{product}", kind="delivery",
                               payload={"idempotency_key": key, "migrated": True,
                                        "note": "旧受控运行发送记录，不映射任何学习状态（数据模型·迁移规则）"},
                               actor="migration", at="2026-07-01T17:12:07+10:00")
            migrated["legacy_sent"] += 1
    else:
        migrated["skipped"].append("controlled_run_manifest_missing")

    snapshot_ref = "用户中心/截至今日候选池.md"
    if not conn.execute(
        "SELECT 1 FROM legacy_archive WHERE kind='legacy_score_snapshot' AND ref=?", (snapshot_ref,)
    ).fetchone():
        pool_page = repo_root / snapshot_ref
        conn.execute(
            "INSERT INTO legacy_archive (kind, ref, payload_json, migrated_at) VALUES (?, ?, ?, ?)",
            ("legacy_score_snapshot", snapshot_ref,
             json.dumps({"exists": pool_page.exists(),
                         "note": "旧 V7 候选池评分快照按原文件存档引用，不复算、不进入 v0.3 排序",
                         "bytes": pool_page.stat().st_size if pool_page.exists() else 0},
                        ensure_ascii=False),
             store.utcnow_iso()),
        )
        migrated["legacy_scores"] += 1
    conn.commit()
    return migrated
