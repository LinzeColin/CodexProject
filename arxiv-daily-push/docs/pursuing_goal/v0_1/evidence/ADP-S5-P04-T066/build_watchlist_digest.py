#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures + report for ADP-S5-P04-T066 (Watchlist + Change-only Digest).

Two periods exercise every acceptance path: day-1 baseline emits notifications; day-2 has a NOISE-ONLY
re-render (must NOT notify), a genuine new VERSION (must notify), a brand-new ITEM (must notify), and an
unwatched item (must not). Re-running day-2 with the returned state must emit ZERO new notifications. A
watch whose source is quiet raises a silence signal. Fixtures are literals so the verifier re-derives.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import watchlist_digest as WD

WATCHES = [
    WD.make_watch("W1", "agency", "国务院办公厅"),
    WD.make_watch("W2", "region", "江苏"),
    WD.make_watch("W3", "doc_number", "苏政办函〔2026〕39号"),
    WD.make_watch("W4", "topic", "数据共享"),
    WD.make_watch("W5", "entity", "国家统计局"),   # matches nothing -> silence signal
]

# ---- day 1 baseline ----------------------------------------------------------------------------
DAY1 = [
    {"canonical_id": "doc-1", "agency": "国务院办公厅", "topic": ["数据共享"], "doc_number": "国办发〔2026〕1号",
     "title": "关于推进政务数据共享的意见", "url": "https://gov/doc-1", "body": "第一条 建立数据共享机制。", "status": "published"},
    {"canonical_id": "doc-2", "region": "江苏", "doc_number": "苏政办函〔2026〕39号",
     "title": "江苏省数据管理办法", "url": "https://js/doc-2", "body": "第一条 省级数据平台上线。", "status": "published"},
]

# ---- day 2: noise-only re-render + genuine new version + new item + unwatched ------------------
DAY2 = [
    # doc-1 re-rendered with template NOISE only -> same substantive hash -> NO notification
    {"canonical_id": "doc-1", "agency": "国务院办公厅", "topic": ["数据共享"], "doc_number": "国办发〔2026〕1号",
     "title": "关于推进政务数据共享的意见", "url": "https://gov/doc-1",
     "body": "第一条 建立数据共享机制。\n责任编辑：张三\n版权所有 © 2026", "status": "published"},
    # doc-2 substantive change -> new content_hash -> notification (W2, W3)
    {"canonical_id": "doc-2", "region": "江苏", "doc_number": "苏政办函〔2026〕39号",
     "title": "江苏省数据管理办法", "url": "https://js/doc-2", "body": "第一条 省级数据平台上线。第二条 新增考核。", "status": "published"},
    # doc-3 brand-new item -> notification (W1, W4)
    {"canonical_id": "doc-3", "agency": "国务院办公厅", "topic": ["数据共享"], "doc_number": "国办发〔2026〕2号",
     "title": "数据共享考核办法", "url": "https://gov/doc-3", "body": "第一条 建立考核制度。", "status": "published"},
    # unwatched item -> matches no watch -> no notification
    {"canonical_id": "doc-9", "agency": "某市政府", "region": "某市", "doc_number": "某〔2026〕9号",
     "title": "某市通知", "url": "https://x/doc-9", "body": "无关内容。", "status": "published"},
]


def main():
    st = WD.new_state()
    r1 = WD.run_digest(st, DAY1, WATCHES, "2026-W28-day1")
    r2 = WD.run_digest(r1["state"], DAY2, WATCHES, "2026-W28-day2")
    r2_rerun = WD.run_digest(r2["state"], DAY2, WATCHES, "2026-W28-day2")   # dedup: expect 0 new
    report = {
        "day1_notifications": [(n["watch_id"], n["canonical_id"]) for n in r1["notifications"]],
        "day1_silence": [s["watch_id"] for s in r1["silence_signals"]],
        "day2_notifications": [(n["watch_id"], n["canonical_id"]) for n in r2["notifications"]],
        "day2_rerun_notifications": [(n["watch_id"], n["canonical_id"]) for n in r2_rerun["notifications"]],
        "day2_silence": [s["watch_id"] for s in r2["silence_signals"]],
    }
    (HERE / "watchlist_digest_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("day1 notifications:", report["day1_notifications"])
    print("day1 silence:", report["day1_silence"])
    print("day2 notifications:", report["day2_notifications"])
    print("day2 RERUN notifications (expect []):", report["day2_rerun_notifications"])
    print("day2 silence:", report["day2_silence"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
