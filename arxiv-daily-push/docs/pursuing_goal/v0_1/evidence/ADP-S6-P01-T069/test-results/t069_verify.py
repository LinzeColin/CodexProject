#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P01-T069 acceptance: prediction target catalog + Outcome Rule + event labels.

Acceptance (TASK_INDEX row 69): 每个目标可由未来官方证据结算；模糊目标不得进入回测。
  (every target is settleable by future OFFICIAL evidence; ambiguous targets may NOT enter the backtest.)

Deterministic. Re-derives from the TOOL (prediction_targets) + fixtures -- never trusts the report.
Negative controls prove discrimination: an ambiguous target is rejected AND settle() refuses it; a media
look-alike does NOT settle (official-only); a future-observed official doc does NOT leak into the label.
"""
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import prediction_targets as PT

T069 = V01 / "evidence" / "ADP-S6-P01-T069"
spec = importlib.util.spec_from_file_location("bpt", str(T069 / "build_prediction_targets.py"))
bpt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bpt)

fails = []
adm = PT.admit_targets(bpt.CATALOG)
admitted_ids = [t["target_id"] for t in adm["admitted"]]
rejected_ids = [r["target_id"] for r in adm["rejected"]]
print("admitted:", admitted_ids, "rejected:", rejected_ids)

# =============================================================== 1) 每个目标可由未来官方证据结算
if admitted_ids != ["G1", "G2", "G3"]:
    fails.append(f"admitted set wrong: {admitted_ids}")
# every admitted target must be settleable, and settling it against official evidence gives a DEFINITE label
for t in adm["admitted"]:
    if not PT.is_settleable(t):
        fails.append(f"{t['target_id']} admitted but not settleable")

g1_yes = PT.settle(bpt.CATALOG[0], [bpt.E_OFFICIAL_MATCH, bpt.E_FUTURE_MATCH], bpt.ORIGIN)
g1_no = PT.settle(bpt.CATALOG[0], [bpt.E_MEDIA_MATCH, bpt.E_FUTURE_MATCH], bpt.ORIGIN)
if g1_yes["label"] != 1:
    fails.append(f"G1 with an official match should settle 1, got {g1_yes['label']}")
if g1_no["label"] != 0:
    fails.append(f"G1 with only a media/future match should settle 0, got {g1_no['label']}")
# G2 count threshold and G3 status transition settle definitely
if PT.settle(bpt.CATALOG[1], [bpt.E_STATS_1, bpt.E_STATS_2, bpt.E_FUTURE_MATCH], bpt.ORIGIN)["label"] != 1:
    fails.append("G2 with two official statistics releases should settle 1")
# G2's 365-day window ends 2027-01-01; elapse it with a later unrelated official observation so that
# a single matching release settles a definite 0 (not pending).
G2_ELAPSE = {"canonical_id": "e0", "authority_level": "A0", "agency": "某部", "topics": ["其他"],
             "status": "published", "observed_at": "2027-02-01"}
if PT.settle(bpt.CATALOG[1], [bpt.E_STATS_1, G2_ELAPSE], bpt.ORIGIN)["label"] != 0:
    fails.append("G2 with only one release (window elapsed) should settle 0")
if PT.settle(bpt.CATALOG[2], [bpt.E_STATUS, bpt.E_FUTURE_MATCH], bpt.ORIGIN)["label"] != 1:
    fails.append("G3 with a revoked transition should settle 1")
# 'pending' when the settlement window has not elapsed and no match yet
pend = PT.settle(bpt.CATALOG[0], [bpt.E_STATS_1], bpt.ORIGIN)   # newest obs 2026-02-10 < window end, no match
if pend["label"] != "pending":
    fails.append(f"an unelapsed window with no match should be pending, got {pend['label']}")
print(f"settleable: G1 official=1 / media-only=0; G2 two=1/one=0; G3 revoked=1; unelapsed=pending")

# =============================================================== 2) 模糊目标不得进入回测
for bid in ("B1", "B2", "B3"):
    t = next(x for x in bpt.CATALOG if x["target_id"] == bid)
    if PT.is_settleable(t):
        fails.append(f"{bid} (ambiguous) was judged settleable")
    if bid not in rejected_ids or bid in admitted_ids:
        fails.append(f"{bid} was not rejected from the backtest")
    # settling a non-settleable target must RAISE (it can never be backtested)
    try:
        PT.settle(t, [bpt.E_OFFICIAL_MATCH], bpt.ORIGIN)
        fails.append(f"settle() did not refuse the ambiguous target {bid}")
    except ValueError:
        pass
print(f"ambiguous rejected: {rejected_ids} (subjective / empty-field / no-horizon) — settle() refuses each")

# =============================================================== 3) official-only + no leakage (controls)
# NEGATIVE CONTROL (official-only): a MEDIA doc matching the predicate in-window does NOT settle 1
media_only = PT.settle(bpt.CATALOG[0], [bpt.E_MEDIA_MATCH,
                       {**bpt.E_FUTURE_MATCH}], bpt.ORIGIN)   # media in-window + a future official (elapses window)
if media_only["label"] == 1:
    fails.append("a media look-alike settled the target -> official-only rule broken")
# NEGATIVE CONTROL (no leakage): the SAME official matching doc observed IN-window settles 1, but
# observed AFTER the window settles 0 -> the observed_at window is load-bearing.
in_win = {**bpt.E_OFFICIAL_MATCH, "observed_at": "2026-03-01"}
after_win = {**bpt.E_OFFICIAL_MATCH, "observed_at": "2026-09-01"}
if PT.settle(bpt.CATALOG[0], [in_win], bpt.ORIGIN)["label"] != 1:
    fails.append("an in-window official match did not settle 1")
lk = PT.settle(bpt.CATALOG[0], [after_win, {**bpt.E_FUTURE_MATCH, "canonical_id": "z", "topics": []}], bpt.ORIGIN)
if lk["label"] == 1:
    fails.append("a future-observed official doc leaked into the label (settled 1)")
# reproducible
if PT.settle(bpt.CATALOG[0], [in_win], bpt.ORIGIN) != PT.settle(bpt.CATALOG[0], [in_win], bpt.ORIGIN):
    fails.append("settle() is not reproducible")
print("controls: media does not settle; future-observed official does not leak (in-window=1, after-window=0)")

# BOUNDARY CONTROL: G1 horizon 180d from 2026-01-01 -> window end 2026-06-30. A match observed exactly
# on the end date counts (settles 1); one day later does NOT (leaks -> stays 0/pending).
on_end = {**bpt.E_OFFICIAL_MATCH, "observed_at": "2026-06-30"}
day_after = {**bpt.E_OFFICIAL_MATCH, "observed_at": "2026-07-01"}
if PT.settle(bpt.CATALOG[0], [on_end], bpt.ORIGIN)["label"] != 1:
    fails.append("a match observed exactly on the window end did not settle 1")
after = PT.settle(bpt.CATALOG[0], [day_after], bpt.ORIGIN)
if after["label"] == 1:
    fails.append("a match observed one day after the window end leaked into a 1")
# malformed / missing observed_at must not crash and must not settle 1
if PT.settle(bpt.CATALOG[0], [{**bpt.E_OFFICIAL_MATCH, "observed_at": "not-a-date"}], bpt.ORIGIN)["label"] == 1:
    fails.append("a malformed observed_at wrongly settled 1")
if PT.settle(bpt.CATALOG[0], [{**bpt.E_OFFICIAL_MATCH, "observed_at": None}], bpt.ORIGIN)["label"] == 1:
    fails.append("a None observed_at wrongly settled 1")
print("boundary: exactly-on-end counts (1); one-day-after does not leak; malformed/None observed_at safe")

# TYPE-SAFETY CONTROLS: wrong-typed evidence/targets must not spuriously settle or admit.
# (1) a doc whose `topics` is a STRING must NOT substring-match (no spurious 1)
str_topics = {**bpt.E_OFFICIAL_MATCH, "topics": "数据共享政策"}   # substring-superset of "数据共享"
if PT.settle(bpt.CATALOG[0], [str_topics], bpt.ORIGIN)["label"] == 1:
    fails.append("a string topics field substring-matched and spuriously settled 1")
# (2) a bool horizon / bool n must NOT be settleable
if PT.is_settleable(PT.make_target("x", "d", True, "p",
        {"type": "official_doc_exists", "agency": "国务院办公厅", "topic": "数据共享"})):
    fails.append("a bool horizon_days was judged settleable")
if PT.is_settleable(PT.make_target("x", "d", 180, "p",
        {"type": "count_at_least", "agency": "国家统计局", "topic": "统计", "n": True})):
    fails.append("a bool count threshold n was judged settleable")
# (3) a non-dict settlement must return False (not crash) and be rejected
if PT.is_settleable(PT.make_target("x", "d", 180, "p", "is_important")):
    fails.append("a non-dict settlement was judged settleable")
if PT.is_settleable(PT.make_target("x", "d", 180, "p", None)):
    fails.append("a None settlement was judged settleable")
bad = PT.admit_targets([PT.make_target("NB", "d", 180, "p", "is_important")])
if [r["target_id"] for r in bad["rejected"]] != ["NB"] or bad["admitted"]:
    fails.append("a non-dict settlement target was not cleanly rejected")
print("type-safety: string-topics no spurious match; bool horizon/n not settleable; non-dict settlement rejected (no crash)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
