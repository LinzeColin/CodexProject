"""单命令五环节（R1-10）—— adp run：发现 → 证据 → 选择 → 学习 → 排程 → 落 manifest.

发送不在 run 内自动发生（学会/发送分离，R1-7）；deliver 是独立显式命令且受授权约束。
同一日期重复 run = 幂等：第二次记「未运行」并给出原因（不变量 6 的运行面）。
"""

from __future__ import annotations

import json
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

    # 对抗性验证修复：幂等检查与阈值加载也在 try 内（此前这里的异常会逃逸、
    # 不留任何「失败」manifest——违反不变量 9）。
    try:
        completed = _completed_run_for_date(conn, as_of_date)
        if completed:
            entry = {
                "run_id": run_id, "trigger": trigger, "result": "未运行",
                "side_effects_authorized": False, "counts": counts,
                "降级项": [], "弃权原因": None,
                "note": f"当日已有成功运行 {completed}，幂等跳过",
                "duration_seconds": round(time.monotonic() - started, 1),
            }
            return write_manifest(conn, entry)

        thresholds = config.load_thresholds()
        return _run_stages(conn, run_id=run_id, trigger=trigger, as_of=as_of,
                           as_of_date=as_of_date, fetch=fetch, fetch_days=fetch_days,
                           thresholds=thresholds, counts=counts, degraded=degraded,
                           started=started)
    except Exception as exc:  # 任何异常必须留下「失败」manifest（不变量 9）
        entry = {
            "run_id": run_id, "trigger": trigger, "result": "失败",
            "side_effects_authorized": False, "counts": counts,
            "降级项": degraded, "弃权原因": None,
            "note": f"{type(exc).__name__}: {exc}",
            "duration_seconds": round(time.monotonic() - started, 1),
        }
        return write_manifest(conn, entry)


def _completed_run_for_date(conn: sqlite3.Connection, as_of_date: str) -> str | None:
    """幂等键 = 当日是否已有**成功**运行（正常/降级/弃权）.

    对抗性验证修复：此前以 selections 行为键——一次中途崩溃的 run 已提交
    selections 行，会把这一天永久标记为「已运行」而没有任何成功产出。
    失败/未运行的 manifest 不阻止重跑。
    """
    for row in conn.execute(
        "SELECT run_id, manifest_json FROM run_manifests WHERE run_id LIKE ?",
        (f"{as_of_date}T%",),
    ):
        entry = json.loads(row["manifest_json"])
        if entry.get("result") in {"正常", "降级", "弃权"}:
            return row["run_id"]
    return None


def _run_stages(conn: sqlite3.Connection, *, run_id: str, trigger: str, as_of: datetime,
                as_of_date: str, fetch: bool, fetch_days: int, thresholds,
                counts: dict[str, Any], degraded: list[str], started: float) -> dict[str, Any]:
    # 1 发现 + 2 证据（声明抽取在入库时完成；新版本触发纠错传播）
    if fetch:
        fetch_counts = fetch_window(conn, days=fetch_days, as_of=as_of)
        counts["抓取新增"] = fetch_counts["新版本"]
        degraded.extend(fetch_counts.get("降级项") or [])
    from .corrections import detect_and_propagate

    corrections_report = detect_and_propagate(conn)
    counts["纠错"] = corrections_report["corrections_created"]

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
        # 2 证据（增强面）：只对选中篇做 OpenAlex/S2 增强，失败只降级（R2）
        if fetch:
            from .enrich import enrich_document

            enrichment = enrich_document(conn, top["candidate"]["doc_id"])
            degraded.extend(enrichment.get("degraded") or [])

    # 5 排程（上限读注册表 max_daily_reviews；复习保护债务只在 run 内登记一次）
    from .review import record_review_pressure

    counts["到期复习"] = len(due_items(conn, at=as_of, limit=thresholds.max_daily_reviews))
    counts["复习超限顺延"] = record_review_pressure(conn, at=as_of, limit=thresholds.max_daily_reviews)

    # 备份（每日，30 份滚动——数据永不丢）
    try:
        store.backup(conn)
    except Exception as exc:
        degraded.append(f"backup_failed:{type(exc).__name__}")

    # 心跳（R3-5）：launchd 看门狗读取此文件；超时会在系统页亮「失败」行
    (config.data_dir() / "heartbeat").write_text(
        json.dumps({"last_run": run_id, "at": store.utcnow_iso()}), encoding="utf-8"
    )

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
    row = conn.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
    lessons_dir = config.data_dir() / "lessons"
    lessons_dir.mkdir(parents=True, exist_ok=True)
    path = lessons_dir / f"{lesson_id}.json"
    payload = {key: row[key] for key in row.keys()}
    payload["sections_json"] = json.loads(payload["sections_json"])
    payload["claim_bindings_json"] = json.loads(payload["claim_bindings_json"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        # ADP_DATA_DIR 指向项目外（如测试临时目录）时 relative_to 会抛错并砸掉整个 run
        return str(path.relative_to(config.PROJECT_ROOT))
    except ValueError:
        return str(path)
