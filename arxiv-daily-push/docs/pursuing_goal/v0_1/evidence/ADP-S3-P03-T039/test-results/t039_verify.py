#!/usr/bin/env python3
"""ADP-S3-P03-T039 acceptance: A0 14-day shadow value-cost comparison + shadow discipline.

Acceptance (TASK_INDEX): 至少 14 个完整周期；不以单日样本决策；未达门槛继续 Shadow。
Deterministic. The 14-cycle report is representative; the literal 14 days accrue over real calendar
time (SHADOW). Verifies the media-vs-A0 comparison AND the shadow discipline (never decide < 14 cycles;
continue if thresholds unmet; SHADOW never switches).
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T039 = V01 / "evidence" / "ADP-S3-P03-T039"
sys.path.insert(0, str(V01 / "tools"))
import a0_shadow as SH  # noqa: E402

reports = [SH.DayReport(**d) for d in json.loads((T039 / "shadow_reports_14.json").read_text(encoding="utf-8"))]
fails = []

acc = SH.accumulate(reports)
print(f"cycles {acc['cycles']} | A0 authoritativeness {acc['a0_stream']['authoritativeness']} pollution {acc['a0_stream']['pollution']} "
      f"cost/accepted {acc['a0_stream']['cost_per_accepted']:.3f}")
print(f"media authoritativeness {acc['media_stream']['authoritativeness']} pollution {acc['media_stream']['pollution']}")
print("recommendation:", acc["recommendation"])

# --- 1) value-cost comparison: A0 stream >> media stream -----------------------------------
if not (acc["a0_stream"]["authoritativeness"] >= 0.99):
    fails.append("A0 stream authoritativeness < 99%")
if not (acc["a0_stream"]["pollution"] <= 0.01):
    fails.append("A0 stream pollution > 1%")
if not (acc["media_stream"]["authoritativeness"] < 0.5 and acc["media_stream"]["pollution"] > 0.5):
    fails.append("media stream not shown as low-authority / high-pollution")
# miss / false-positive analysis + cost per accepted item present
if "coverage_misses" not in acc["a0_stream"] or "false_positives" not in acc["a0_stream"]:
    fails.append("miss / false-positive analysis missing")
if "cost_per_accepted" not in acc["a0_stream"]:
    fails.append("cost per accepted item missing")

# --- 2) >= 14 complete cycles required; never decide on a single day ------------------------
if not (acc["cycles"] >= 14 and acc["recommendation"] == "READY_FOR_OWNER_S3_EXIT_GATE"):
    fails.append(f"14 cycles + thresholds should recommend readiness, got {acc['recommendation']}")
single = SH.accumulate(reports[:1])
print("\nsingle-day accumulate ->", single["recommendation"], "|", single["reason"])
if single["recommendation"] != "CONTINUE_SHADOW":
    fails.append("a single day was allowed to decide (must CONTINUE_SHADOW)")
thirteen = SH.accumulate(reports[:13])
if thirteen["recommendation"] != "CONTINUE_SHADOW":
    fails.append("13 cycles was allowed to decide (must be >= 14)")

# --- 3) thresholds not met -> continue shadow ----------------------------------------------
polluted = list(reports)
polluted[0] = SH.DayReport(**{**reports[0].__dict__, "a0_authoritative": 4, "a0_polluted": 4})  # inject pollution
acc_bad = SH.accumulate(polluted)
print("thresholds-unmet accumulate ->", acc_bad["recommendation"], "| met:", acc_bad["thresholds_met"])
if acc_bad["recommendation"] != "CONTINUE_SHADOW":
    fails.append("thresholds unmet but did not CONTINUE_SHADOW")

# --- 4) SHADOW never switches --------------------------------------------------------------
if acc["release_mode"] != "SHADOW":
    fails.append("release_mode not SHADOW")
if "gated by the Owner" not in acc["note"]:
    fails.append("does not defer the switch to the Owner S3 Exit gate")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
