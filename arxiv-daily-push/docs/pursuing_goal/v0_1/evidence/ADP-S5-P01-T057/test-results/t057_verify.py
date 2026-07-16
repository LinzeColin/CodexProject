#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T057 acceptance: Canonical Event aggregation.

Acceptance (TASK_INDEX): 20 个同事件页面只产生 1 个提醒；所有证据仍可展开。
Deterministic. Verifies that 20 pages about the SAME event aggregate to exactly 1 canonical event
(1 alert), that all 20 members stay individually expandable, that the primary is the authoritative
official original, and -- as a no-over-merge control -- that pages about a DIFFERENT event stay a
separate event.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import canonical_event as CE

T057 = V01 / "evidence" / "ADP-S5-P01-T057"
pages = json.loads((T057 / "event_fixture.json").read_text(encoding="utf-8"))
fails = []
agg = CE.aggregate(pages)
events = agg["events"]
print(f"pages_in={agg['pages_in']} alerts={agg['alert_count']} largest_event={agg['largest_event_members']}")
for e in events:
    print(f"  {str(e['event_key']['value'])[:26]:28} members={e['member_count']} primary={e['primary']['authority_level']}")

EVENT1 = "苏政办函〔2026〕39号"
EVENT2 = "鲁科字〔2023〕143号"
e1_pages = [p for p in pages if p.get("doc_number") == EVENT1 or p.get("references") == EVENT1]
e1_event = next((e for e in events if e["event_key"]["value"] == EVENT1), None)

# --- 1) 20 same-event pages -> exactly 1 alert -----------------------------------------------
if len(e1_pages) != 20:
    fails.append(f"fixture event-1 has {len(e1_pages)} pages (expected 20)")
if e1_event is None:
    fails.append("event-1 was not formed")
elif e1_event["member_count"] != 20:
    fails.append(f"event-1 has {e1_event['member_count']} members (expected 20)")
# the 20 pages must contribute exactly ONE alert, not 20
e1_alerts = sum(1 for e in events if e["event_key"]["value"] == EVENT1)
if e1_alerts != 1:
    fails.append(f"the 20 same-event pages produced {e1_alerts} alerts (expected 1)")

# --- 2) all evidence still expandable --------------------------------------------------------
if e1_event:
    members = CE.expand(e1_event)
    if len(members) != 20:
        fails.append(f"expand(event-1) returned {len(members)} members (expected 20)")
    if len({m["page_id"] for m in members}) != 20:
        fails.append("event-1 members are not all individually retrievable (duplicate/missing page_id)")
    fixture_ids = {p["page_id"] for p in e1_pages}
    if {m["page_id"] for m in members} != fixture_ids:
        fails.append("expanded members do not match the 20 source pages exactly")

# --- 3) primary selection = the authoritative official ORIGINAL ------------------------------
if e1_event:
    prim = e1_event["primary"]
    if prim["doc_number"] != EVENT1:
        fails.append(f"event-1 primary is not the original ({prim.get('doc_number')})")
    if prim["authority_level"] != "A1":
        fails.append(f"event-1 primary authority {prim['authority_level']} != A1 (a media repost was chosen)")

# --- 4) NO OVER-MERGE control: a different event stays separate -------------------------------
e2_event = next((e for e in events if e["event_key"]["value"] == EVENT2), None)
if e2_event is None:
    fails.append("event-2 (different 文号) was not formed -> merge failure")
if e1_event and e2_event and e1_event["event_id"] == e2_event["event_id"]:
    fails.append("event-1 and event-2 collapsed into the same event (over-merge)")
# event-1 must NOT contain any event-2 page
if e1_event:
    e2_ids = {p["page_id"] for p in pages if p.get("doc_number") == EVENT2 or p.get("references") == EVENT2}
    if {m["page_id"] for m in CE.expand(e1_event)} & e2_ids:
        fails.append("event-1 absorbed an event-2 page (over-merge)")

# --- 5) re-derivation guard ------------------------------------------------------------------
live = CE.aggregate(pages)
if live["alert_count"] != agg["alert_count"] or live["largest_event_members"] != agg["largest_event_members"]:
    fails.append("aggregation not deterministic across runs")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
