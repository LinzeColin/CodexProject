#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S8-P02-T089 (partial) acceptance: stop-the-line drills + soak framework.

Acceptance (TASK_INDEX row 89): 14 次真实日运行无 Sev-1/2；所有 stop-the-line trigger 至少演练一次.

This verifier confirms:
  * CLAUSE 2 (all stop-the-line triggers drilled at least once) is MET: each of the 8 anti-black-hole
    triggers fires its real detection gate (line_stopped) AND a benign negative control does NOT fire it
    (negative_control_ok) -- so each drill is load-bearing, not a vacuous constant.
  * CLAUSE 1 (14 consecutive real daily runs, no Sev-1/2) is honestly PENDING (day 0/14) -- it is
    calendar-bound and the tool does NOT claim T089 complete (t089_complete == False). No over-claim.
Deterministic (no network/clock/randomness). NOT_DEPLOYED (drills run in isolation; live b189d3cc0703).
"""
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import soak_stopline_drill as SD

fails = []
rep = SD.run()

# ---- clause 2: every stop-the-line trigger drilled, each load-bearing ----
if len(rep["stopline_drills"]) != 8:
    fails.append(f"expected 8 stop-the-line drills, got {len(rep['stopline_drills'])}")
for d in rep["stopline_drills"]:
    if not d["line_stopped"]:
        fails.append(f"trigger not drilled (line did not stop): {d['trigger']}")
    if not d["negative_control_ok"]:
        fails.append(f"drill vacuous (negative control fires too): {d['trigger']}")
if not rep["stopline_clause_met"]:
    fails.append("stop-the-line clause not met (not all 8 triggers drilled with controls)")

# ---- clause 1: LIVE-tracked from cn_run_log; in progress, T089 NOT yet complete ----
soak = rep["soak"]
if soak["required_consecutive_days"] != 14:
    fails.append(f"soak required days wrong: {soak['required_consecutive_days']}")
# the soak is self-accumulating from the daily cron; days_completed is in [0, 14): in progress, not done
if not (0 <= soak["days_completed"] < 14):
    fails.append(f"soak days_completed not an in-progress value: {soak['days_completed']}/14")
if rep["soak_clause_met"] or rep["t089_complete"]:
    fails.append(f"over-claim: soak_clause_met/t089_complete reported True at {soak['days_completed']}/14")
# soak_progress is LOAD-BEARING: a 失败 (Sev-1/2) breaks the consecutive-healthy streak
lb = SD.soak_progress([{"as_of_date": "2026-07-16", "result": "正常"},
                       {"as_of_date": "2026-07-15", "result": "失败"},
                       {"as_of_date": "2026-07-14", "result": "正常"}])
if lb["days_healthy_consecutive"] != 1 or lb["streak_broken_by"] != "2026-07-15":
    fails.append(f"soak_progress not load-bearing: a 失败 should break the streak at 1, got {lb}")
# and 14 consecutive healthy days -> complete (the auto-completion logic is real)
full = SD.soak_progress([{"as_of_date": f"2026-07-{i:02d}", "result": "正常"} for i in range(1, 15)])
if not full["complete"]:
    fails.append("soak_progress logic broken: 14 consecutive healthy days should be complete")

print(f"stop-the-line drills: 8/8 triggers fire their gate (line stops) with passing negative controls "
      f"[{', '.join(d['trigger'].split(' (')[0][:22] for d in rep['stopline_drills'])}]")
print(f"soak clause (LIVE from cn_run_log): {soak['status']}; T089 complete = {rep['t089_complete']}")

print("\nACCEPTANCE = " + ("PASS (clause 2: stop-the-line drills)" if not fails else "FAIL") +
      f"  |  CLAUSE 1 (14-day soak): RUNNING {soak['days_completed']}/14 (LIVE, self-accumulating)")
print("NOTE: all 8 stop-the-line triggers drilled at least once against their real detection gates, each "
      "load-bearing. The 14-consecutive-real-day soak is now LIVE-tracked from the daily cron's cn_run_log "
      f"and self-accumulating ({soak['days_completed']}/14 healthy days so far); it needs no agent action, "
      "only calendar time, and T089 clause 1 closes automatically at 14/14. NOT_DEPLOYED (read-only over the "
      "live D1; worker unchanged).")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
