#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T051 acceptance: key city-level (A1) cohort.

Acceptance (TASK_INDEX): 每个城市有明确价值和官方原文；不为凑数量启用低价值源。
Deterministic. Verifies every admitted city has (1) a clear value (score + tier + rationale),
(2) a verified A1 official-original publisher identity, and (3) a 2016 cursor; and that the selection
is value-gated not volume-padded -- a low-value city and a media aggregator are provably REJECTED.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import city_cohort as C

T051 = V01 / "evidence" / "ADP-S4-P03-T051"
man = json.loads((T051 / "city_cohort_manifest.json").read_text(encoding="utf-8"))
admitted = man["admitted"]
rejected = man["rejected"]
fails = []
print(f"candidates={man['candidates']} admitted={man['admitted_count']} rejected={man['rejected_count']} "
      f"stop={man['stop_threshold']} waves={ {k: len(v) for k, v in man['waves'].items()} }")

# --- 1) every admitted city has a CLEAR VALUE (score >= stop, tier, rationale) --------------------
if not admitted:
    fails.append("no cities admitted")
for a in admitted:
    if not (a["value"] >= man["stop_threshold"]):
        fails.append(f"{a['source_id']}: admitted with value {a['value']} < stop {man['stop_threshold']}")
    if not a.get("tier") or not a.get("value_rationale"):
        fails.append(f"{a['source_id']}: missing tier/value_rationale (no clear value)")

# --- 2) every admitted city is a verified A1 OFFICIAL ORIGINAL PUBLISHER --------------------------
for a in admitted:
    if a["authority_level"] != "A1":
        fails.append(f"{a['source_id']}: admitted but not A1")
    if not str(a.get("official_host", "")).endswith(".gov.cn"):
        fails.append(f"{a['source_id']}: official_host is not a .gov.cn portal ({a.get('official_host')})")

# --- 3) every admitted city has a 2016 CURSOR ----------------------------------------------------
for a in admitted:
    cur = a.get("cursor_2016") or {}
    if cur.get("start_month") != "2016-01":
        fails.append(f"{a['source_id']}: 2016 cursor missing/incorrect ({cur.get('start_month')})")

# --- 4) NOT volume-padded: value-gate + official-only, with reachable NEGATIVE CONTROLS -----------
reasons = " ".join(r["reason"] for r in rejected)
if not any("< stop" in r["reason"] for r in rejected):
    fails.append("no low-value city was rejected -> stop_rule not exercised (volume-padding risk)")
if not any("media" in r["reason"] or "not a verified A1" in r["reason"] for r in rejected):
    fails.append("no non-official/media source was rejected -> A1-publisher gate not exercised")
# re-derive from the tool to confirm the manifest was not hand-edited to pass
live = C.select_cohort()
if len(live["admitted"]) != len(admitted):
    fails.append(f"manifest admitted count {len(admitted)} != tool re-derivation {len(live['admitted'])}")
# discrimination: a media source with a HIGH nominal value must still be rejected (value != admission)
media = next((c for c in C.CANDIDATES if c.get("category") == "media"), None)
if media:
    mv = C.value_score(media); idv = C.verify_official(media)
    if not (mv >= C.STOP_THRESHOLD and idv["authority_level"] != "A1"):
        fails.append("media negative control not discriminating (should be high-value yet non-A1)")
    else:
        print(f"negative control: media source value={mv} (>= stop) but authority={idv['authority_level']} -> rejected")

# waves cover all admitted
wave_ids = {sid for w in man["waves"].values() for sid in w}
if wave_ids != {a["source_id"] for a in admitted}:
    fails.append("onboarding waves do not cover exactly the admitted cohort")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
