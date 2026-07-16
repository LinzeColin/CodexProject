#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T053 acceptance: first-batch high-value A2 pilots.

Acceptance (TASK_INDEX): 每个 A2 产生中央/省级之外的实质增量；无价值源不晋级。
Deterministic. Verifies each admitted A2 zone produces real INCREMENTAL value beyond the A0/A1
baseline (>=1 local-action signal type not in {policy, regulation, statistics}), carries an A2 pilot
profile + a 2016 cursor + its local-action signals, and that NO low-value source is promoted -- a
zone with no incremental value and a media source are provably rejected.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import a2_pilot as A2

man = json.loads((V01 / "evidence" / "ADP-S4-P04-T053" / "a2_pilot_manifest.json").read_text(encoding="utf-8"))
admitted = man["admitted"]
rejected = man["rejected"]
baseline = set(man["baseline_signals_A0_A1"])
fails = []
print(f"candidates={man['candidates']} admitted={man['admitted_count']} rejected={man['rejected_count']} "
      f"confirmed_signal_zones={sum(1 for a in admitted if a['reachable_server_side']=='confirmed_signals')}")

# --- 1) first batch of ~10 high-value A2 -----------------------------------------------------
if len(admitted) < 10:
    fails.append(f"first A2 batch has {len(admitted)} zones (< 10)")

# --- 2) every admitted A2 produces INCREMENTAL value beyond A0/A1 -----------------------------
for a in admitted:
    inc = a.get("incremental_signal_types") or []
    if not inc:
        fails.append(f"{a['source_id']}: admitted with NO incremental value")
    if any(s in baseline for s in inc):
        fails.append(f"{a['source_id']}: incremental set leaks a baseline signal {inc}")
    if a["authority_level"] != "A2":
        fails.append(f"{a['source_id']}: not marked A2")
    if not str(a.get("official_host", "")).endswith(".gov.cn"):
        fails.append(f"{a['source_id']}: not an official .gov.cn zone portal")

# --- 3) A2 pilot profile + local action signals + 2016 cursor for each ------------------------
for a in admitted:
    if not a.get("local_action_signals"):
        fails.append(f"{a['source_id']}: missing local action signals")
    if not a.get("zone_type"):
        fails.append(f"{a['source_id']}: missing zone_type (no pilot profile)")
    if (a.get("cursor_2016") or {}).get("start_month") != "2016-01":
        fails.append(f"{a['source_id']}: missing/incorrect 2016 cursor")

# --- 4) NO low-value source promoted (negative controls) -------------------------------------
if not any("no incremental value" in r["reason"] for r in rejected):
    fails.append("no zero-incremental zone rejected -> the value gate is untested (volume risk)")
if not any("not a verified official" in r["reason"] or "media" in r["reason"] for r in rejected):
    fails.append("no non-official/media source rejected -> official gate untested")
# discrimination: a zone that only re-posts A0/A1 policy has 0 incremental -> must be rejected
repost = next((c for c in A2.CANDIDATES if c["source_id"] == "policy-repost-zone"), None)
if repost and A2.incremental_signals(repost):
    fails.append("policy-repost negative control is not actually zero-incremental")
# re-derive from the tool (guard against a hand-edited manifest)
live = A2.select_pilot()
if len(live["admitted"]) != len(admitted) or len(live["rejected"]) != len(rejected):
    fails.append("manifest does not match tool re-derivation")

# --- 5) the 3 server-reachable zones carry confirmed live local-action signal evidence -------
confirmed = [a for a in admitted if a["reachable_server_side"] == "confirmed_signals"]
if len(confirmed) < 3:
    fails.append(f"expected >=3 zones with confirmed live signals, got {len(confirmed)}")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
