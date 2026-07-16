#!/usr/bin/env python3
"""ADP-S3-P03-T038 acceptance: media-lead -> official-original resolver + event grouping + abstain.

Acceptance (TASK_INDEX): 50 个媒体线索中有原文则绑定原文，无原文则 UNKNOWN/ABSTAIN；不冒充官方。
Deterministic. 50 leads = 28 resolvable to an official original (20 by cited 发文字号, 8 by referenced
title, with reposts of the same doc) + 22 real board3 news leads with no official original (ABSTAIN).
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T038 = V01 / "evidence" / "ADP-S3-P03-T038"
sys.path.insert(0, str(V01 / "tools"))
import media_resolver as M  # noqa: E402

data = json.loads((T038 / "media_leads_50.json").read_text(encoding="utf-8"))
leads, official, expected = data["leads"], data["official_index"], data["expected"]
fails = []

res = M.resolve_all(leads, official)
s = res["summary"]
print(f"leads {s['leads']} | bound {s['bound']} | abstained {s['abstained']} | events {s['events']} | impersonations {s['impersonations']}")

# --- 1) each lead: an original exists -> bind to it; none -> ABSTAIN ------------------------
correct = 0
for r, (exp_status, exp_cid) in zip(res["resolutions"], expected):
    got = "bound" if r["resolved"] else "ABSTAIN"
    if got == exp_status and (not exp_cid or r["official_canonical_id"] == exp_cid):
        correct += 1
    else:
        if len(fails) < 4:
            fails.append(f"{r['lead_id']}: got {got}/{r['official_canonical_id']} != {exp_status}/{exp_cid}")
print(f"lead resolution correct: {correct}/50")
if correct != 50:
    fails.append(f"only {correct}/50 leads resolved as expected")

# --- 2) NEVER impersonate official: an ABSTAIN lead never carries A0 ------------------------
for r in res["resolutions"]:
    if not r["resolved"]:
        if r["authority"] == "A0" or r["impersonates_official"]:
            fails.append(f"{r['lead_id']}: abstained lead impersonates official")
        if r["status"] != "ABSTAIN":
            fails.append(f"{r['lead_id']}: unresolved lead status {r['status']} != ABSTAIN")
if s["impersonations"] != 0:
    fails.append(f"{s['impersonations']} leads impersonate official (must be 0)")
# bound leads carry the official authority + point to the official canonical id
for r in res["resolutions"]:
    if r["resolved"] and (r["authority"] != "A0" or not r["official_canonical_id"]):
        fails.append(f"{r['lead_id']}: bound lead missing official authority/canonical_id")

# --- 3) reposts of the same event merge into one canonical event ---------------------------
ev_by_cid = {e["canonical_id"]: e for e in res["events"]}
# doc 1 is referenced by multiple leads (docnum reposts + a title lead) -> repost_count > 1
d1 = ev_by_cid.get("doi:gov/1")
print("event doi:gov/1 repost_count:", d1["repost_count"] if d1 else None)
if not d1 or d1["repost_count"] < 2:
    fails.append("reposts of the same official event did not merge (doi:gov/1 repost_count < 2)")
if not d1["official_backed"]:
    fails.append("bound event not marked official_backed")
# an abstained event stays not-official-backed
abstain_events = [e for e in res["events"] if not e["official_backed"]]
if any(e["authority"] == "A0" for e in abstain_events):
    fails.append("an abstained event carries A0")
print(f"official-backed events: {sum(1 for e in res['events'] if e['official_backed'])} | abstained events: {len(abstain_events)}")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
