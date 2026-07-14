"""adp CLI —— fetch / select / learn / review / deliver 五命令 + run/web/replay/export.

用法: var/venv/bin/python -m adp <command>（cwd = arxiv-daily-push/）。
旧 362KB CLI 冻结于 arxiv_daily_push.cli，与本入口无共享状态。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from . import config, store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="adp", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="建库（WAL+FTS5）")
    p_fetch = sub.add_parser("fetch", help="发现：抓取增量（真实网络，只读 API）")
    p_fetch.add_argument("--days", type=int, default=1)
    p_run = sub.add_parser("run", help="单命令五环节 + 落 manifest")
    p_run.add_argument("--trigger", default="manual")
    p_run.add_argument("--as-of", help="ISO 时间（回放/补跑用），默认当前")
    p_run.add_argument("--no-fetch", action="store_true", help="只用库内已有数据（回放）")
    p_run.add_argument("--fetch-days", type=int, default=1)
    sub.add_parser("select", help="选择：只跑硬门+打分（不生成讲义）")
    p_learn = sub.add_parser("learn", help="学习：为最近入选生成讲义")
    p_learn.add_argument("--lesson-id")
    sub.add_parser("review", help="排程：列出到期复习项")
    p_grade = sub.add_parser("grade", help="记录一次回忆自评（1忘了 2困难 3良好 4轻松）")
    p_grade.add_argument("item_id")
    p_grade.add_argument("grade", type=int, choices=[1, 2, 3, 4])
    p_deliver = sub.add_parser("deliver", help="交付：幂等邮件镜像（无授权=失败关闭+预览）")
    p_deliver.add_argument("--lesson-id")
    p_replay = sub.add_parser("replay", help="30 天回放 + 弃权线重校（R1-3）")
    p_replay.add_argument("--days", type=int, default=30)
    p_web = sub.add_parser("web", help="启动网页（127.0.0.1:8787）")
    p_web.add_argument("--port", type=int, default=8787)
    sub.add_parser("export", help="一键导出全部数据（JSONL）")
    p_backfill = sub.add_parser("backfill", help="按真实历史日期补跑（数据须已在库内）")
    p_backfill.add_argument("date", help="YYYY-MM-DD（Sydney）")
    sub.add_parser("migrate-legacy", help="R2 迁移：旧发送记录→delivery 事件；旧评分→只存档")
    sub.add_parser("corrections", help="检测版本/撤稿并传播纠错（run 内已自动执行）")

    args = parser.parse_args(argv)
    conn = store.connect()
    try:
        if args.command == "init":
            print(json.dumps({"db": str(config.data_dir() / 'adp.sqlite3'), "schema": store.SCHEMA_VERSION}))
            return 0
        if args.command == "fetch":
            from .arxiv_source import fetch_window

            counts = fetch_window(conn, days=args.days)
            print(json.dumps(counts, ensure_ascii=False))
            return 0
        if args.command == "run":
            from .run import run_once

            as_of = datetime.fromisoformat(args.as_of) if args.as_of else None
            if as_of and as_of.tzinfo is None:
                as_of = as_of.replace(tzinfo=timezone.utc)
            entry = run_once(conn, trigger=args.trigger, as_of=as_of,
                             fetch=not args.no_fetch, fetch_days=args.fetch_days)
            print(json.dumps(entry, ensure_ascii=False, indent=1))
            return 0 if entry["result"] in {"正常", "降级", "弃权", "未运行"} else 2
        if args.command == "select":
            # 复审修复：select 是只读预览（评估+解释，不落 selections 行），
            # 否则会毒化当日 run 的幂等检查、静默跳过整个学习日。
            from .arxiv_source import candidates_for_date
            from .run import SYDNEY
            from .selection import build_context, evaluate_candidates, explain_choice, seen_version_ids

            as_of = datetime.now(timezone.utc)
            day = as_of.astimezone(SYDNEY).strftime("%Y-%m-%d")
            thresholds = config.load_thresholds()
            scored, rejected = evaluate_candidates(
                candidates_for_date(conn, day), build_context(conn, as_of=as_of), thresholds,
                gate_context={"seen_version_ids": seen_version_ids(conn),
                              "source_health": "active"},
            )
            preview: dict = {"dry_run": True, "as_of_date": day,
                             "scanned": len(scored) + len(rejected), "passed_gates": len(scored)}
            if scored and scored[0]["score"] >= thresholds.abstain_threshold:
                why, why_not = explain_choice(scored[0], scored[1] if len(scored) > 1 else None)
                preview.update({"top_title": scored[0]["candidate"]["title"],
                                "top_score": scored[0]["score"], "why": why, "why_not": why_not})
            else:
                preview.update({"abstain": True,
                                "top_score": scored[0]["score"] if scored else None})
            print(json.dumps(preview, ensure_ascii=False, indent=1))
            return 0
        if args.command == "learn":
            from .lesson import generate_lesson, validate_traceability

            selection = conn.execute(
                "SELECT * FROM selections WHERE abstain=0 ORDER BY as_of_date DESC LIMIT 1"
            ).fetchone()
            if not selection:
                print("no selection to learn from", file=sys.stderr)
                return 2
            candidate = conn.execute("SELECT * FROM candidates WHERE id=?", (selection["candidate_id"],)).fetchone()
            version = conn.execute(
                "SELECT id FROM doc_versions WHERE doc_id=? ORDER BY version_no DESC LIMIT 1",
                (candidate["doc_id"],),
            ).fetchone()
            lesson_id = args.lesson_id or f"L-{selection['as_of_date']}-{candidate['doc_id'].split(':')[-1]}"
            outcome = generate_lesson(conn, lesson_id=lesson_id, candidate_id=candidate["id"],
                                      doc_version_id=version["id"], as_of_date=selection["as_of_date"])
            outcome["traceability"] = validate_traceability(conn, lesson_id)
            outcome.pop("sections")
            print(json.dumps(outcome, ensure_ascii=False, indent=1))
            return 0
        if args.command == "review":
            from .review import due_items

            limit = config.load_thresholds().max_daily_reviews
            print(json.dumps(due_items(conn, limit=limit), ensure_ascii=False, indent=1))
            return 0
        if args.command == "grade":
            from .review import grade_recall

            outcome = grade_recall(conn, args.item_id, args.grade, config.load_thresholds())
            print(json.dumps(outcome, ensure_ascii=False, indent=1))
            return 0
        if args.command == "deliver":
            from .delivery import deliver_lesson

            lesson = args.lesson_id or _latest_lesson_id(conn)
            if not lesson:
                print("no lesson to deliver", file=sys.stderr)
                return 2
            receipt = deliver_lesson(conn, lesson)
            print(json.dumps(receipt, ensure_ascii=False, indent=1))
            return 0
        if args.command == "replay":
            from .selection import replay_30d

            report = replay_30d(conn, config.load_thresholds(),
                                as_of=datetime.now(timezone.utc), days=args.days)
            out = config.data_dir() / "replay_30d.json"
            out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
            summary = {k: v for k, v in report.items() if k != "rows"}
            summary["rows_written"] = len(report["rows"])
            summary["path"] = str(out)
            print(json.dumps(summary, ensure_ascii=False, indent=1))
            return 0
        if args.command == "web":
            from .webapp import main as web_main

            web_main(port=args.port)
            return 0
        if args.command == "export":
            return _export(conn)
        if args.command == "backfill":
            from .run import run_once

            as_of = datetime.fromisoformat(f"{args.date}T07:00:00+10:00")
            entry = run_once(conn, trigger="backfill_replay", as_of=as_of, fetch=False)
            print(json.dumps(entry, ensure_ascii=False, indent=1))
            return 0
        if args.command == "migrate-legacy":
            from .corrections import migrate_legacy

            print(json.dumps(migrate_legacy(conn, config.PROJECT_ROOT), ensure_ascii=False, indent=1))
            return 0
        if args.command == "corrections":
            from .corrections import detect_and_propagate, unresolved

            report = detect_and_propagate(conn)
            report["unresolved"] = unresolved(conn)
            print(json.dumps(report, ensure_ascii=False, indent=1))
            return 0
    finally:
        conn.close()
    return 1


def _latest_lesson_id(conn) -> str | None:
    row = conn.execute("SELECT id FROM lessons ORDER BY as_of_date DESC LIMIT 1").fetchone()
    return row["id"] if row else None


def _export(conn) -> int:
    """一键导出：全部表 → data/export/*.jsonl（通用格式，数据永不丢）."""
    export_dir = config.data_dir() / "export"
    export_dir.mkdir(parents=True, exist_ok=True)
    tables = [r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'fts_%' AND name NOT LIKE 'sqlite_%'"
    )]
    manifest = {}
    for table in tables:
        rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table}")]
        path = export_dir / f"{table}.jsonl"
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        manifest[table] = len(rows)
    print(json.dumps({"exported": manifest, "dir": str(export_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
