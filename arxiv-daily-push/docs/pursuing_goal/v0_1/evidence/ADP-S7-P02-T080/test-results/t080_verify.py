#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P02-T080 acceptance: component states, Undo, and cross-theme state persistence.

Acceptance (TASK_INDEX row 80): 点击 100ms 内反馈；切主题不丢阅读位置、答案、筛选和展开状态.

Deterministic. Re-derives from the TOOL (component_state_audit) + the worker + the frozen T079 baseline.
Load-bearing negative controls (this is what makes the checks non-vacuous):
  1. STATE MATRIX + UNDO are DISCRIMINATING: the pre-fix T079 worker must FAIL both (0 states, undo not
     deferred) -- so a pass cannot come from anything that pre-existed.
  2. PERSISTENCE check is real: a synthetic applyTheme with a location.reload injected must FAIL no_reload.
  3. Only base_css changed on the T077/T078 contract (every theme/motion hash byte-identical), and the fix
     BLOCKs the T078 gate without a documented approval.
Empirical proof: the Node undo behavioural test (undo writes nothing) and the in-app-browser persistence +
state-CSS render are in browser_measurements.json / test-results/undo_behavior_test.js.
"""
import json
import pathlib
import subprocess
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB
import visual_regression_ci as CI
import component_state_audit as CS

T080 = V01 / "evidence" / "ADP-S7-P02-T080"
PRE = json.loads((T080 / "pre_fix_baseline.json").read_text(encoding="utf-8"))["asset_hashes"]
NEW_SRC = VB.WORKER.read_text(encoding="utf-8")
NEW_CSS = VB._tmpl(NEW_SRC, "CSS")
PRE_SRC = (T080 / "pre_fix_worker.js").read_text(encoding="utf-8")
PRE_CSS = VB._tmpl(PRE_SRC, "CSS")

fails = []

# ============ 1) 点击 100ms 内反馈 -- component state matrix + native :active + <=100ms transition ============
sm = CS.state_matrix(NEW_CSS)
for state, present in sm.items():
    if not present:
        fails.append(f"component state missing: {state}")
fb = CS.feedback_within_100ms(NEW_CSS)
if not fb["within_100ms"]:
    fails.append(f"click feedback not within 100ms: {fb}")
print(f"state matrix: {sum(sm.values())}/{len(sm)} present; feedback within 100ms "
      f"(:active native + transform transition {fb['transform_transition_s']}s)")

# ---- NEGATIVE CONTROL 1: the pre-fix (T079) worker must FAIL the state matrix (states are T080-added) ----
pre_sm = CS.state_matrix(PRE_CSS)
if any(pre_sm.values()):
    fails.append(f"control broken: the pre-fix CSS already has a component state (audit not discriminating): {pre_sm}")
print(f"negative control: pre-fix CSS scores {sum(pre_sm.values())}/{len(pre_sm)} states (must be 0)")

# ============ Undo -- the write is deferred behind a cancelable window; undo writes nothing ============
undo = CS.undo_defers_write(NEW_SRC)
for k, v in undo.items():
    if not v:
        fails.append(f"undo property not satisfied: {k}")
# ---- NEGATIVE CONTROL 2: the pre-fix worker wrote synchronously on click -> undo checks must FAIL ----
pre_undo = CS.undo_defers_write(PRE_SRC)
if any(pre_undo.values()):
    fails.append(f"control broken: the pre-fix worker already deferred the write: {pre_undo}")
# the Node behavioural test on the REAL extracted client code must have PASSED
node = subprocess.run(["node", str(T080 / "test-results" / "undo_behavior_test.js")],
                      capture_output=True, text=True)
if "RESULT = PASS" not in node.stdout or node.returncode != 0:
    fails.append(f"undo behavioural test did not pass: rc={node.returncode}")
print(f"undo: click defers write, undo writes nothing (pre-fix scored {sum(pre_undo.values())}/5); "
      f"Node behavioural test = {'PASS' if 'RESULT = PASS' in node.stdout else 'FAIL'}")

# error states wired (no more silent hang on a failed fetch)
err = CS.error_states_wired(NEW_SRC)
if not (err["grade_commit_try_catch"] and err["run_try_catch"]):
    fails.append(f"error states not wired: {err}")

# ============ 2) 切主题不丢...状态 -- applyTheme swaps attributes only; no reload/navigate/rebuild ============
pt = CS.applytheme_preserves_state(NEW_SRC)
for k in ("found", "no_reload", "no_navigate", "no_innerHTML_rebuild", "persists_choice"):
    if not pt[k]:
        fails.append(f"applyTheme persistence property not satisfied: {k} ({pt})")
# ---- NEGATIVE CONTROL 3: a synthetic applyTheme WITH a reload must FAIL no_reload (check is real) ----
poisoned = NEW_SRC.replace("function applyTheme(n){if(!isTheme(n))n='warm';",
                           "function applyTheme(n){if(!isTheme(n))n='warm';location.reload();", 1)
if CS.applytheme_preserves_state(poisoned)["no_reload"]:
    fails.append("control broken: the persistence check does not detect an injected location.reload")
print(f"persistence: applyTheme swaps attributes only (no reload/navigate/rebuild); poisoned-reload control detected")

# the in-app-browser proof: every state preserved across all six theme switches + state CSS computes
bm = json.loads((T080 / "browser_measurements.json").read_text(encoding="utf-8"))
if not bm["persistence_test"]["all_state_preserved_every_theme"]:
    fails.append("browser proof: some state was lost on a theme switch")
if bm["persistence_test"]["theme_switches"] != 6:
    fails.append("browser proof did not cover all six themes")
if not all(bm["state_css_computed"].values()):
    fails.append(f"browser proof: a component-state CSS rule did not compute: {bm['state_css_computed']}")
print(f"browser proof: state preserved across {bm['persistence_test']['theme_switches']} theme switches; "
      f"all state CSS computes")

# ============ 3) 现有高级视觉保持 -- only base_css changed; motion/themes identical ============
pv = CS.preserves_advanced_visual(PRE_SRC, NEW_SRC)
if not (pv["only_base_css"] and pv["per_theme_identical"] and pv["motion_identical"]):
    fails.append(f"advanced visual not preserved: {pv}")
if CI.run_ci(PRE, NEW_SRC)["decision"] != "BLOCK":
    fails.append("control broken: the change must BLOCK the T078 gate without a documented approval")
appr = [{"element": "base_css", "reason": "T080 component-state matrix", "approver": "owner"}]
if CI.run_ci(PRE, NEW_SRC, appr)["decision"] != "PASS_APPROVED":
    fails.append("the documented change did not pass the gate as an approved change")
print(f"advanced visual preserved: specific change = {pv['specific_changed']}; 6 themes + every motion "
      f"byte-identical; gate BLOCKs without approval, PASS_APPROVED with one")

# ============ NOT_DEPLOYED: source build recomputed, live unchanged ============
if "40a46aa2baee" not in NEW_SRC:
    fails.append("could not confirm the source build_id after the fix")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: source build_id after the fix is 40a46aa2baee; NOT_DEPLOYED (live still serves the previous "
      "build). Empirical proofs: browser_measurements.json + test-results/undo_behavior_test.js.")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
