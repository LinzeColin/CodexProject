#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T057 -- build a same-event page fixture + aggregate into canonical events.

Event 1 uses a REAL backfilled document number (苏政办函〔2026〕39号, from the T050 Jiangsu backfill)
as its original, with 19 interpretations / reposts / reactions that cite that 文号 -- 20 pages, one
event. Event 2 uses a different real 文号 (鲁科字〔2023〕143号) -- it must stay a separate event, not
merge. A singleton news page (no reference) stays its own event. Deterministic.
"""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import canonical_event as CE

EVENT1_DOCNUM = "苏政办函〔2026〕39号"
EVENT2_DOCNUM = "鲁科字〔2023〕143号"

def _members_for(docnum, base_url, n_interp, n_repost, n_reaction):
    pages = []
    for i in range(n_interp):
        pages.append({"page_id": f"interp-{docnum}-{i}", "url": f"{base_url}/interp/{i}", "kind": "interpretation",
                      "source_id": "gov-cn-policy", "authority_level": "A1", "references": docnum,
                      "title": f"《{docnum}》政策解读 {i}"})
    for i in range(n_repost):
        pages.append({"page_id": f"repost-{docnum}-{i}", "url": f"https://news.example.com/{docnum}/{i}", "kind": "repost",
                      "source_id": "media-x", "authority_level": "media", "references": docnum,
                      "title": f"转载：{docnum} {i}"})
    for i in range(n_reaction):
        pages.append({"page_id": f"react-{docnum}-{i}", "url": f"https://forum.example.com/{docnum}/{i}", "kind": "reaction",
                      "source_id": "forum-y", "authority_level": "media", "references": docnum,
                      "title": f"讨论：{docnum} {i}"})
    return pages

def main():
    pages = []
    # --- Event 1: 1 official original + 19 members = 20 pages ---
    pages.append({"page_id": "orig-jiangsu", "url": "http://www.jiangsu.gov.cn/art/2026/7/14/art_46144_11803435.html",
                  "kind": "original", "source_id": "jiangsu-gov", "authority_level": "A1",
                  "doc_number": EVENT1_DOCNUM, "title": "省政府办公厅关于印发江苏省低温雨雪冰冻灾害应急预案的通知"})
    pages += _members_for(EVENT1_DOCNUM, "http://www.jiangsu.gov.cn", n_interp=6, n_repost=8, n_reaction=5)  # 19
    # --- Event 2: a DIFFERENT event (must not merge) ---
    pages.append({"page_id": "orig-shandong", "url": "http://www.shandong.gov.cn/art/2026/7/9/art_94237_10361274.html",
                  "kind": "original", "source_id": "shandong-gov", "authority_level": "A1",
                  "doc_number": EVENT2_DOCNUM, "title": "山东省科学技术厅关于开展...的通知"})
    pages += _members_for(EVENT2_DOCNUM, "http://www.shandong.gov.cn", n_interp=2, n_repost=3, n_reaction=1)  # 6
    # --- a singleton unrelated news page (its own event) ---
    pages.append({"page_id": "solo-news", "url": "https://news.example.com/solo", "kind": "repost",
                  "source_id": "media-z", "authority_level": "media", "title": "无关新闻"})

    (HERE / "event_fixture.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    agg = CE.aggregate(pages)
    report = {
        "task": "ADP-S5-P01-T057",
        "pages_in": agg["pages_in"], "alert_count": agg["alert_count"],
        "largest_event_members": agg["largest_event_members"],
        "events": [{"event_id": e["event_id"], "event_key": e["event_key"], "member_count": e["member_count"],
                    "roles": e["roles"], "primary": e["primary"]} for e in agg["events"]],
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
                 "r2_ops": 0, "model_calls": 0, "human_maintenance": "event-aggregation authoring"},
        "deployment": "NOT_DEPLOYED",
    }
    (HERE / "event_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"pages_in={agg['pages_in']} alerts={agg['alert_count']} largest_event={agg['largest_event_members']}")
    for e in agg["events"]:
        print(f"  {e['event_key']['value'][:28]:30} members={e['member_count']} primary={e['primary']['authority_level']} roles={e['roles']}")

if __name__ == "__main__":
    main()
