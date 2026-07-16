#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P04-T066 acceptance: Watchlist + Change-only Digest.

Acceptance (TASK_INDEX row 66): 重跑不重复通知；无变化不打扰；每条变化可定位。
  (a re-run does not duplicate notifications; no change means no disturbance; every change is locatable.)

Deterministic. Re-derives from the TOOL (watchlist_digest) + fixtures -- never trusts the report.
Negative controls prove discrimination: a stateless digest WOULD re-notify (so dedup is non-trivial);
the suppressed noise-only re-render genuinely has the SAME substantive hash (so 'no change' is real);
and a change with no locatable item would fail the locator check.
"""
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import watchlist_digest as WD
import version_engine as VE

T066 = V01 / "evidence" / "ADP-S5-P04-T066"
spec = importlib.util.spec_from_file_location("bwd", str(T066 / "build_watchlist_digest.py"))
bwd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bwd)

fails = []
st = WD.new_state()
r1 = WD.run_digest(st, bwd.DAY1, bwd.WATCHES, "day1")
r2 = WD.run_digest(r1["state"], bwd.DAY2, bwd.WATCHES, "day2")

d1 = sorted((n["watch_id"], n["canonical_id"]) for n in r1["notifications"])
d2 = sorted((n["watch_id"], n["canonical_id"]) for n in r2["notifications"])
print("day1:", d1)
print("day2:", d2)

# ---- correctness of the change-only selection -------------------------------------------------
if d1 != [("W1", "doc-1"), ("W2", "doc-2"), ("W3", "doc-2"), ("W4", "doc-1")]:
    fails.append(f"day1 notifications wrong: {d1}")
if d2 != [("W1", "doc-3"), ("W2", "doc-2"), ("W3", "doc-2"), ("W4", "doc-3")]:
    fails.append(f"day2 notifications wrong: {d2}")

# =============================================================== 1) 重跑不重复通知 (rerun no duplicates)
rerun = WD.run_digest(r2["state"], bwd.DAY2, bwd.WATCHES, "day2")
if rerun["notifications"]:
    fails.append(f"re-run produced duplicate notifications: {[n['canonical_id'] for n in rerun['notifications']]}")
# NEGATIVE CONTROL: dedup is non-trivial -- a STATELESS digest (fresh state, no dedup memory) re-emits
# every watch match, while the state-carrying re-run emits none.
stateless = WD.run_digest(WD.new_state(), bwd.DAY2, bwd.WATCHES, "day2")
if not stateless["notifications"]:
    fails.append("stateless digest emitted nothing -> dedup test is vacuous")
if len(stateless["notifications"]) <= len(rerun["notifications"]):
    fails.append("a stateless digest did not emit more than the deduped re-run -> dedup is not doing anything")
print(f"rerun: {len(rerun['notifications'])} new (expect 0); stateless (no memory) re-emits "
      f"{len(stateless['notifications'])} (dedup non-trivial)")

# =============================================================== 2) 无变化不打扰 (no change no notify)
# doc-1 on day2 is a NOISE-ONLY re-render -> it must NOT appear in day2 notifications
if any(n["canonical_id"] == "doc-1" for n in r2["notifications"]):
    fails.append("a noise-only re-render (doc-1) produced a notification (无变化不打扰 violated)")
# and the suppression is meaningful: doc-1's day1 and day2 substantive hashes are EQUAL (真 noise-only)
h1 = VE.content_hash(next(i for i in bwd.DAY1 if i["canonical_id"] == "doc-1"))
h2 = VE.content_hash(next(i for i in bwd.DAY2 if i["canonical_id"] == "doc-1"))
if h1 != h2:
    fails.append("control broken: doc-1 day2 is not actually a noise-only re-render (hashes differ)")
# while the genuine change (doc-2) DOES differ, proving discrimination
g1 = VE.content_hash(next(i for i in bwd.DAY1 if i["canonical_id"] == "doc-2"))
g2 = VE.content_hash(next(i for i in bwd.DAY2 if i["canonical_id"] == "doc-2"))
if g1 == g2:
    fails.append("control broken: doc-2 was supposed to change substantively but its hash is unchanged")
# feeding an UNCHANGED corpus (day1 again) after day1 -> zero new notifications
noop = WD.run_digest(r1["state"], bwd.DAY1, bwd.WATCHES, "day1b")
if noop["notifications"]:
    fails.append(f"an unchanged corpus produced notifications: {[n['canonical_id'] for n in noop['notifications']]}")
print(f"no-change: doc-1 noise-only hash equal={h1==h2} -> suppressed; doc-2 changed hash differ={g1!=g2}; unchanged corpus -> 0 new")

# =============================================================== 3) 每条变化可定位 (every change locatable)
for n in r1["notifications"] + r2["notifications"]:
    loc = n.get("locator") or {}
    if not all(k in loc for k in ("canonical_id", "content_hash", "matched_facet", "matched_value")):
        fails.append(f"notification missing locator fields: {n}")
    src = bwd.DAY1 if n["period"] == "day1" else bwd.DAY2
    if not WD.notification_is_locatable(n, src):
        fails.append(f"notification not locatable to a real changed item: {n['watch_id']}/{n['canonical_id']}")
print(f"locatable: all {len(r1['notifications'])+len(r2['notifications'])} notifications carry a locator resolving to the changed item")

# NEGATIVE CONTROL: the locatability check genuinely discriminates (is not a stub). A notification whose
# content_hash no longer matches the item, or whose item is absent, must be reported NOT locatable.
sample = r2["notifications"][0]
stale = {**sample, "locator": {**sample["locator"], "content_hash": "sha256:deadbeef"}}
if WD.notification_is_locatable(stale, bwd.DAY2):
    fails.append("a stale/wrong-version locator was accepted -> locatability check is a stub")
missing = {**sample, "locator": {**sample["locator"], "canonical_id": "doc-does-not-exist"}}
if WD.notification_is_locatable(missing, bwd.DAY2):
    fails.append("a locator to a missing item was accepted -> locatability check is a stub")
print("locatable control: a wrong-version hash and a missing canonical_id are both rejected (not a stub)")

# =============================================================== 4) source silence signal
if [s["watch_id"] for s in r1["silence_signals"]] != ["W5"]:
    fails.append(f"day1 silence should be [W5], got {[s['watch_id'] for s in r1['silence_signals']]}")
if "W5" not in [s["watch_id"] for s in r2["silence_signals"]]:
    fails.append("day2 silence should include W5 (its watched source is quiet)")
print(f"silence: day1={[s['watch_id'] for s in r1['silence_signals']]}, day2={[s['watch_id'] for s in r2['silence_signals']]}")

# caller state must not be mutated in place (run_digest returns a fresh state)
before = set(r1["state"]["seen"])
_ = WD.run_digest(r1["state"], bwd.DAY2, bwd.WATCHES, "dayX")
if set(r1["state"]["seen"]) != before:
    fails.append("run_digest mutated the caller's state in place")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
