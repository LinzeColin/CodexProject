#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P03-T076 acceptance: full-horizon Shadow closeout & go/stop release decision.

Acceptance (TASK_INDEX row 76): Brier skill 为正且稳定、校准可接受、用户领先价值明确；否则停止.
  (Brier skill positive AND stable, calibration acceptable, user lead value clear; otherwise STOP.)
Objective: only a forecaster with SUSTAINED skill across the full horizon may be shown to users.
Deliverables: shadow closeout, release decision, rollback/disable flag.

Deterministic. Re-derives from the TOOL (horizon_shadow_closeout) + the real S6-P03 shadow, and
RE-COMPUTES the Brier skill and the ECE with its OWN formulas -- it never trusts the report.

Load-bearing controls -- the gate must be able to STOP, not rubber-stamp GO:
  * the real shadow -> GO (all three criteria pass);
  * a shadow whose skill regresses in one window -> STOP (skill criterion);
  * a miscalibrated forecast -> STOP (calibration criterion);
  * zero lead / no net value -> STOP (lead criterion).
Each degenerate input flips exactly ONE criterion, proving each independently gates.
"""
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import horizon_shadow_closeout as HC

T076 = V01 / "evidence" / "ADP-S6-P03-T076"
spec = importlib.util.spec_from_file_location("bhc", str(T076 / "build_horizon_shadow_closeout.py"))
bhc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bhc)

fails = []
rep = bhc.build()
sh = bhc.gather_shadow()


def bss(model_briers, ref_briers):                # verifier's OWN skill formula (independent)
    mb = sum(model_briers) / len(model_briers); rb = sum(ref_briers) / len(ref_briers)
    return None if rb == 0 else 1 - mb / rb


def ece(forecasts, n_bins=10):                    # verifier's OWN ECE (independent, count-weighted)
    bins = {}
    for f in forecasts:
        if f["label"] not in (0, 1):
            continue
        b = min(n_bins - 1, int(min(1.0, max(0.0, f["prob"])) * n_bins))
        bins.setdefault(b, []).append(f)
    n = sum(len(v) for v in bins.values())
    if not n:
        return None
    return sum(len(v) * abs(sum(x["prob"] for x in v) / len(v) - sum(x["label"] for x in v) / len(v))
               for v in bins.values()) / n


# ================================================ 1) Brier skill 为正且稳定 (sustained, re-derived)
per = [bss([w["model_brier"]], [w["baseline_brier"]]) for w in sh["windows"]]
agg = bss([w["model_brier"] for w in sh["windows"]], [w["baseline_brier"] for w in sh["windows"]])
print(f"skill: {len(sh['windows'])} windows, per-window BSS={[round(b,3) for b in per]}, aggregate={round(agg,4)}")
if not (agg > 0):
    fails.append("aggregate Brier skill is not positive")
if not (min(per) > 0):
    fails.append(f"Brier skill not sustained -- a window regresses (min BSS {min(per):.4f} <= 0)")
if not rep["skill"]["skill_ok"]:
    fails.append("tool skill_ok is False despite positive+sustained skill")
# independent re-derivation must match the tool
if abs(rep["skill"]["aggregate_bss"] - agg) > 1e-6:
    fails.append("tool aggregate BSS disagrees with the independent re-derivation")

# ================================================ 2) 校准可接受 (ECE, re-derived independently)
my_ece = ece(sh["forecasts"])
print(f"calibration: ECE(re-derived)={round(my_ece,4)} tool={rep['calibration']['ece']} "
      f"tol={rep['calibration']['tol']} max_bin={rep['calibration']['max_reliability_error']}")
if abs(my_ece - rep["calibration"]["ece"]) > 1e-6:
    fails.append("tool ECE disagrees with the independent re-derivation")
if not rep["calibration"]["acceptable"]:
    fails.append("calibration reported not acceptable for the real shadow")

# ================================================ 3) 用户领先价值明确
lv = rep["lead_value"]
if not (lv["lead_days"] > 0 and lv["net_human_value"] > 0 and lv["clear"]):
    fails.append("user lead value is not clear for the real shadow")
print(f"lead value: lead_days={lv['lead_days']} net_value={lv['net_human_value']} clear={lv['clear']}")

# ================================================ 4) go/stop decision honest -- the gate can GO and STOP
dec = rep["release_decision"]
if not (dec["decision"] == "GO" and dec["show_to_users"] and not dec["disable_flag"]):
    fails.append(f"real shadow should GO (all criteria pass), got {dec}")
print(f"REAL DECISION: {dec['decision']} show={dec['show_to_users']} disable={dec['disable_flag']}")

# --- degenerate shadows: each flips exactly ONE criterion -> STOP + disable_flag + the right reason ---
good_windows = sh["windows"]
good_forecasts = sh["forecasts"]

# (a) skill regresses in one window (model worse than baseline there) -> STOP on skill
bad_skill = [dict(w) for w in good_windows]
bad_skill[0] = {**bad_skill[0], "model_brier": 0.40, "baseline_brier": 0.25}   # BSS = -0.6 < 0
r_a = HC.closeout(bad_skill, good_forecasts, lead_days=90, correct_catches=19, false_alarms=5, tol=0.15)["release_decision"]
if not (r_a["decision"] == "STOP" and r_a["disable_flag"] and r_a["failed_criteria"] == ["brier_skill_not_positive_and_stable"]):
    fails.append(f"control broken: a regressing skill window must STOP on skill only, got {r_a}")

# (b) miscalibrated forecast (predict 0.9, observe ~0.3) -> STOP on calibration only
bad_calib = [{"prob": 0.9, "label": 1 if i < 3 else 0} for i in range(10)]   # pred 0.9 obs 0.3 -> ECE 0.6
r_b = HC.closeout(good_windows, bad_calib, lead_days=90, correct_catches=19, false_alarms=5, tol=0.15)["release_decision"]
if not (r_b["decision"] == "STOP" and r_b["disable_flag"] and r_b["failed_criteria"] == ["calibration_not_acceptable"]):
    fails.append(f"control broken: a miscalibrated forecast must STOP on calibration only, got {r_b}")

# (c) no lead value (net value <= 0) -> STOP on lead only
r_c = HC.closeout(good_windows, good_forecasts, lead_days=90, correct_catches=2, false_alarms=9, tol=0.15)["release_decision"]
if not (r_c["decision"] == "STOP" and r_c["disable_flag"] and r_c["failed_criteria"] == ["user_lead_value_not_clear"]):
    fails.append(f"control broken: no net lead value must STOP on lead only, got {r_c}")

# (d) zero lead time -> STOP on lead
r_d = HC.closeout(good_windows, good_forecasts, lead_days=0, correct_catches=19, false_alarms=5, tol=0.15)["release_decision"]
if not (r_d["decision"] == "STOP" and "user_lead_value_not_clear" in r_d["failed_criteria"]):
    fails.append(f"control broken: zero lead time must STOP on lead, got {r_d}")
print("gate discriminates: real->GO; regressing-skill->STOP(skill); miscalibrated->STOP(calib); "
      "no-value->STOP(lead); zero-lead->STOP(lead)")

# ================================================ reproducible
if bhc.build()["release_decision"] != dec:
    fails.append("closeout decision is not reproducible")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
