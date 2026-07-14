"""单命令五环节（R1-10）—— adp run：发现 → 证据 → 选择 → 学习 → 排程 → 落 manifest.

发送不在 run 内自动发生（学会/发送分离，R1-7）；deliver 是独立显式命令且受授权约束。
同一日期重复 run = 幂等：第二次记「未运行」并给出原因（不变量 6 的运行面）。
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from . import config, store
from .arxiv_source import candidates_for_date, fetch_window
from .lesson import generate_lesson, validate_traceability
from .manifest import write_manifest
from .review import due_items
from .selection import select_daily

SYDNEY = ZoneInfo(config.TIMEZONE)


def run_once(conn: sqlite3.Connection, *, trigger: str = "manual",
             as_of: datetime | None = None, fetch: bool = True,
             fetch_days: int = 1) -> dict[str, Any]:
    started = time.monotonic()
    as_of = as_of or datetime.now(timezone.utc)
    as_of_date = as_of.astimezone(SYDNEY).strftime("%Y-%m-%d")
    run_id = f"{as_of.astimezone(SYDNEY).isoformat(timespec='seconds')}"
    degraded: list[str] = []
    counts: dict[str, Any] = {"扫描": 0, "过门": 0, "选中": 0, "讲义": 0, "到期复习": 0, "已交付": 0}

    existing = conn.execute(
        "SELECT run_id FROM selections WHERE as_of_date=?", (as_of_date,)
    ).fetchone()
    if existing:
        entry = {
            "run_id": run_id, "trigger": trigger, "result": "未运行",
            "side_effects_authorized": False, "counts": counts,
            "降级项": [], "弃权原因": None,
            "note": f"当日已有运行 {existing['run_id']}，幂等跳过",
            "duration_seconds": round(time.monotonic() - started, 1),
        }
        return write_manifest(conn, entry)

    thresholds = config.load_thresholds()

    # 1 发现 + 2 证据（声明抽取在入库时完成）
    if fetch:
        fetch_counts = fetch_window(conn, days=fetch_days, as_of=as_of)
        counts["抓取新增"] = fetch_counts["新版本"]
        degraded.extend(fetch_counts.get("降级项") or [])

    # 3 选择
    candidates = candidates_for_date(conn, as_of_date)
    selection = select_daily(conn, run_id=run_id, as_of_date=as_of_date,
                             candidates=candidates, thresholds=thresholds, as_of=as_of)
    counts["扫描"] = selection["scanned"]
    counts["过门"] = selection["passed_gates"]

    lesson_artifacts: list[str] = []
    abstain_reason = None
    if selection.get("abstain"):
        abstain_reason = selection["abstain_reason"]
    else:
        counts["选中"] = 1
        top = selection["top"]
        # 4 学习：生成讲义 + 逐句溯源校验
        lesson_id = f"L-{as_of_date}-{top['candidate']['stable_id']}"
        outcome = generate_lesson(
            conn, lesson_id=lesson_id,
            candidate_id=f"{top['candidate']['doc_id']}@{as_of_date}",
            doc_version_id=top["candidate"]["doc_version_id"], as_of_date=as_of_date,
        )
        counts["讲义"] = 1
        if outcome["degraded_reason"]:
            degraded.append(f"lesson_generation:{outcome['degraded_reason']}")
        trace = validate_traceability(conn, lesson_id)
        if not trace["ok"]:
            degraded.append(f"traceability_incomplete:{len(trace['missing'])}")
        lesson_artifacts.append(_export_lesson(conn, lesson_id))

    # 5 排程
    counts["到期复习"] = len(due_items(conn, at=as_of))

    # 备份（每日，30 份滚动——数据永不丢）
    try:
        store.backup(conn)
    except Exception as exc:
        degraded.append(f"backup_failed:{type(exc).__name__}")

    result = "弃权" if abstain_reason else ("降级" if degraded else "正常")
    entry = {
        "run_id": run_id, "trigger": trigger, "result": result,
        "side_effects_authorized": False, "counts": counts,
        "降级项": degraded, "弃权原因": abstain_reason,
        "selection": {
            "why": selection.get("why"), "why_not": selection.get("why_not"),
            "top_score": (selection.get("top") or {}).get("score") if not selection.get("abstain") else selection.get("top_score"),
        },
        "artifacts": lesson_artifacts,
        "duration_seconds": round(time.monotonic() - started, 1),
    }
    return write_manifest(conn, entry)


def _export_lesson(conn: sqlite3.Connection, lesson_id: str) -> str:
    """讲义导出为 JSON 工件（可入库 git 作为证据）."""
    import json

    row = conn.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
    lessons_dir = config.data_dir() / "lessons"
    lessons_dir.mkdir(parents=True, exist_ok=True)
    path = lessons_dir / f"{lesson_id}.json"
    payload = {key: row[key] for key in row.keys()}
    payload["sections_json"] = json.loads(payload["sections_json"])
    payload["claim_bindings_json"] = json.loads(payload["claim_bindings_json"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(path.relative_to(config.PROJECT_ROOT))
