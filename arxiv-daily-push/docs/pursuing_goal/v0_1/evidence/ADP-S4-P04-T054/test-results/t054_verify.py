#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T054 acceptance: expand the A2 registry by marginal value.

Acceptance (TASK_INDEX): 新增 cohort 的 verified useful signal rate 不低于既有 A2 基线。
Deterministic. Verifies the new cohort's verified-useful-signal rate is >= the existing A2 baseline
(T053), that only first-line-signal official zones are added, and that a low-value/non-official
candidate is rejected. A negative control proves admitting the rejects WOULD drop the rate below
baseline -- so the gate genuinely protects the rate.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import a2_registry as R

man = json.loads((V01 / "evidence" / "ADP-S4-P04-T054" / "a2_expansion.json").read_text(encoding="utf-8"))
fails = []
baseline_rate = man["baseline"]["rate"]
new_rate = man["new_cohort_useful_signal_rate"]
admitted = man["admitted"]
rejected = man["rejected"]
print(f"baseline_rate={baseline_rate} new_rate={new_rate} meets_baseline={man['meets_baseline']} "
      f"admitted={man['admitted_count']} rejected={man['rejected_count']}")

# --- 1) new cohort useful-signal rate >= existing A2 baseline ---------------------------------
if not (new_rate >= baseline_rate):
    fails.append(f"new cohort rate {new_rate} < A2 baseline {baseline_rate}")
if not man["meets_baseline"]:
    fails.append("meets_baseline flag is False")

# --- 2) only first-line-signal OFFICIAL zones expanded ---------------------------------------
if not admitted:
    fails.append("no zones admitted to the expansion")
for a in admitted:
    if not a["verified_useful"]:
        fails.append(f"{a['source_id']}: admitted but not verified-useful")
    if not a["incremental_signal_types"]:
        fails.append(f"{a['source_id']}: admitted with no first-line signal")
    if a["authority_level"] != "A2":
        fails.append(f"{a['source_id']}: admitted but not A2")
    if not str(a["official_host"]).endswith(".gov.cn"):
        fails.append(f"{a['source_id']}: not an official .gov.cn zone")
    if (a.get("cursor_2016") or {}).get("start_month") != "2016-01":
        fails.append(f"{a['source_id']}: missing 2016 cursor")

# --- 3) deliverables present: cohorts + marginal value report + health -----------------------
if not man.get("marginal_value_report"):
    fails.append("missing marginal value report")
if not man.get("health"):
    fails.append("missing health report")
if any(not h["healthy"] for h in man["health"]):
    fails.append("an admitted zone is not healthy (0 first-line signals)")

# --- 4) low-value / non-official rejected, AND admitting them WOULD drop the rate (control) ---
if not any("baseline-only" in r["reason"] for r in rejected):
    fails.append("no baseline-only (zero-marginal) zone rejected -> the marginal gate is untested")
if not any("not a verified official" in r["reason"] for r in rejected):
    fails.append("no non-official source rejected -> the official gate is untested")
# NEGATIVE CONTROL: if every candidate (incl. the rejects) were admitted, the useful rate must fall < baseline
all_evals = R.expand()["marginal_value_report"]
would_be_members = [{"verified_useful": bool(
        next((c for c in R.EXPANSION_CANDIDATES if c["source_id"] == e["source_id"]), {}).get("category") != "media"
        and e["marginal_useful_signals"] >= 1)} for e in all_evals]
rate_if_all = R.useful_signal_rate(would_be_members)
print(f"negative control: rate if ALL candidates admitted = {rate_if_all} (must be < baseline {baseline_rate})")
if not (rate_if_all < baseline_rate):
    fails.append("admitting the rejected candidates would NOT drop the rate -> the gate is not protecting quality")
# re-derive from the tool
live = R.expand()
if live["admitted_count"] != man["admitted_count"] or live["new_cohort_useful_signal_rate"] != new_rate:
    fails.append("expansion manifest does not match tool re-derivation")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
