#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S6-P02-T073 acceptance: calibration + skill scores + append-only Forecast Ledger.

Acceptance (TASK_INDEX row 73): 任何用户可见概率有历史校准；失败记录不可删除。
  (any user-visible probability has historical calibration; failure records cannot be deleted.)

Deterministic. Re-derives from the TOOL (forecast_ledger) + fixtures -- never trusts the report.
Negative controls prove discrimination: a probability in a bin with no history is NOT calibration-backed;
deleting any ledger record (especially a failure) RAISES; and skill is reported honestly (a worse model
gets a negative BSS).
"""
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import forecast_ledger as FL

T073 = V01 / "evidence" / "ADP-S6-P02-T073"
spec = importlib.util.spec_from_file_location("bfl", str(T073 / "build_forecast_ledger.py"))
bfl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bfl)

fails = []
calib = FL.calibration(bfl.FORECASTS)

# =============================================================== 1) 任何用户可见概率有历史校准
# the reliability diagram has populated bins where predicted mean tracks observed frequency
populated = [b for b in calib["bins"] if b["n"] > 0]
if not populated:
    fails.append("calibration produced no populated bins")
for b in populated:
    if b["pred_mean"] is None or b["obs_rate"] is None:
        fails.append(f"bin {b['bin']} has data but no pred_mean/obs_rate")
    elif abs(b["pred_mean"] - b["obs_rate"]) > 0.05:
        fails.append(f"bin {b['bin']} is not well-calibrated: pred {b['pred_mean']} vs obs {b['obs_rate']}")
# a user-visible probability in a covered bin IS backed by historical calibration
for p in (0.2, 0.5, 0.8, 0.9):
    if not FL.has_calibration(p, calib):
        fails.append(f"probability {p} in a covered bin is not calibration-backed")
    if FL.calibration_of(p, calib) is None:
        fails.append(f"probability {p} has no historical observed rate")
# NEGATIVE CONTROL: a probability whose bin has NO history is NOT calibration-backed (not auto-passed)
if FL.has_calibration(0.35, calib):   # bin 3 -> no forecasts there
    fails.append("a probability in an empty bin was wrongly reported as calibration-backed (vacuous)")
if FL.calibration_of(0.35, calib) is not None:
    fails.append("an uncalibrated probability returned a historical rate")
# a non-numeric "probability" is not calibration-backed and does not crash
if FL.has_calibration(None, calib) or FL.calibration_of(None, calib) is not None:
    fails.append("a non-numeric probability was treated as calibration-backed / crashed")
print(f"calibration: {len(populated)} populated bins, pred~obs; covered probs backed, uncovered (0.35) & None not")

# =============================================================== 2) 失败记录不可删除
lg = bfl.build_ledger()
fail_ids_before = {r["forecast_id"] for r in FL.failures(lg)}
if "f2" not in fail_ids_before:
    fails.append("the failure record f2 was not preserved in the ledger")
# deleting a FAILURE record must raise (append-only, failures immutable)
try:
    FL.delete(lg, "f2")
    fails.append("a failure record was deleted (ledger is not append-only)")
except FL.AppendOnlyError:
    pass
# deleting ANY record is refused
try:
    FL.delete(lg, "f1")
    fails.append("a success record was deleted (ledger is not append-only)")
except FL.AppendOnlyError:
    pass
# the failure is still there after the delete attempt; both successes and failures kept
if {r["forecast_id"] for r in FL.failures(lg)} != fail_ids_before:
    fails.append("the failure set changed after a (refused) delete")
if not (FL.failures(lg) and FL.successes(lg)):
    fails.append("the ledger does not preserve both successes AND failures")
# TAMPER-EVIDENCE: a clean ledger verifies; directly popping a failure (bypassing delete) is DETECTED.
if not FL.verify_integrity(lg):
    fails.append("a clean append-only ledger failed its integrity check")
import copy as _copy
tampered = _copy.deepcopy(lg)
tampered["records"] = [r for r in tampered["records"] if r["forecast_id"] != "f2"]   # remove the failure
if FL.verify_integrity(tampered):
    fails.append("deleting a failure record (bypassing delete) was NOT detected by verify_integrity")
# mutating a failure's outcome to hide it also breaks integrity
mutated = _copy.deepcopy(lg)
for r in mutated["records"]:
    if r["forecast_id"] == "f2":
        r["outcome"] = "success"
if FL.verify_integrity(mutated):
    fails.append("mutating a failure into a success was NOT detected by verify_integrity")
print(f"ledger append-only: failure {sorted(fail_ids_before)} preserved; delete() raises; "
      f"tamper (pop/mutate a failure) breaks verify_integrity")

# =============================================================== 3) skill scores (honest)
bss = FL.brier_skill_score(bfl.MODEL_BRIERS, bfl.REF_BRIERS)
if not (bss is not None and bss > 0):
    fails.append(f"a model beating the reference should have positive skill, got {bss}")
# equal model -> zero skill
if FL.brier_skill_score(bfl.REF_BRIERS, bfl.REF_BRIERS) != 0:
    fails.append("a model equal to the reference should have zero skill")
# NEGATIVE CONTROL: a WORSE model -> negative skill, reported honestly (not clamped/hidden)
worse = FL.brier_skill_score([0.30, 0.30, 0.30], bfl.REF_BRIERS)
if not (worse is not None and worse < 0):
    fails.append(f"a worse-than-reference model should have negative skill, got {worse}")
ll = FL.logloss([f["prob"] for f in bfl.FORECASTS], [f["label"] for f in bfl.FORECASTS])
if ll is None or ll < 0:
    fails.append(f"logloss invalid: {ll}")
print(f"skill: BSS(model)={bss}>0, BSS(equal)=0, BSS(worse)={worse}<0 (honest); logloss={ll}")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
