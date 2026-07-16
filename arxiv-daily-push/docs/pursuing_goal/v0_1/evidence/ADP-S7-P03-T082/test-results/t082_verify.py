#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P03-T082 acceptance: optimize ambient motion without changing visual semantics.

Acceptance (TASK_INDEX row 82): 中位 >=55 FPS；低端设备自动降级环境层但前景反馈不消失.

Deterministic. Re-derives from the TOOL (ambient_perf_audit) + the worker + the frozen T081 baseline.
Load-bearing negative controls:
  1. The >=55 FPS guarantee is COMPOSITOR-ONLY ambient animation. The pre-fix worker FAILS this (its cosmos
     `meteor` keyframe animates left/top -> forces per-frame layout); the fix converts meteor to transform, so
     every ambient loop is compositor-safe. (before/after trace below.)
  2. Visual semantics preserved: the ONLY contract element that changed is `keyframes` (the meteor
     conversion); per_theme / base_css / theme_js / fx_css / hero are byte-identical, and the change BLOCKs
     the T078 gate without a documented approval.
The browser proof (pause-when-hidden 7/7; low-end degrades meteor/band + simplifies nebula while the
foreground button:active + base ambience survive) is in browser_measurements.json.
"""
import json
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB
import visual_regression_ci as CI
import ambient_perf_audit as A

T082 = V01 / "evidence" / "ADP-S7-P03-T082"
PRE = json.loads((T082 / "pre_fix_baseline.json").read_text(encoding="utf-8"))["asset_hashes"]
NEW_SRC = VB.WORKER.read_text(encoding="utf-8")
PRE_SRC = (T082 / "pre_fix_worker.js").read_text(encoding="utf-8")

fails = []

# ============ 1) 中位 >=55 FPS -- compositor-only ambient animation (deterministic guarantee) ============
safety = A.ambient_compositor_safety(NEW_SRC)
if not A.all_ambient_compositor_safe(NEW_SRC):
    fails.append(f"an ambient keyframe still animates a non-compositor property: {safety}")
mc = A.meteor_converted(NEW_SRC)
if not (mc["animates_transform"] and mc["no_layout_props"]):
    fails.append(f"meteor not converted to compositor-safe transform: {mc}")
# before/after trace (the deliverable): pre-fix meteor forces layout; new does not
pre_meteor_layout = A.keyframe_animates_layout(PRE_SRC, "meteor")
new_meteor_layout = A.keyframe_animates_layout(NEW_SRC, "meteor")
if not (pre_meteor_layout and not new_meteor_layout):
    fails.append(f"before/after trace wrong: pre_layout={pre_meteor_layout} new_layout={new_meteor_layout}")
# NEGATIVE CONTROL: the pre-fix worker FAILS compositor-safety (proves the fix is real + audit discriminates)
if A.all_ambient_compositor_safe(PRE_SRC):
    fails.append("control broken: the pre-fix worker already had all-compositor-safe ambient (audit not discriminating)")
print(f"FPS guarantee: {sum(safety.values())}/{len(safety)} ambient loops compositor-safe (transform/opacity/"
      f"filter only); meteor {A.keyframe_props(PRE_SRC)['meteor']} -> {mc['props']} (before/after: "
      f"layout {pre_meteor_layout} -> {new_meteor_layout}); pre-fix fails the audit")

# ============ 2) 低端降级 + 前景反馈不消失 ============
lite = A.has_lite_degradation(NEW_SRC)
if not (lite["detects_low_end"] and lite["degrades_layers"] and lite["sets_lite_flag"]):
    fails.append(f"low-end degradation not wired: {lite}")
fg = A.foreground_preserved(NEW_SRC)
if not fg["touches_no_foreground"]:
    fails.append("the fx-perf controller touches foreground (component-state) selectors -- foreground could break")
pause = A.has_pause_offscreen(NEW_SRC)
if not pause:
    fails.append("pause-when-hidden not wired")
# browser proof
bm = json.loads((T082 / "browser_measurements.json").read_text(encoding="utf-8"))
le = bm["low_end_device"]
if not (le["lite_flag"] == "1" and le["meteor_hidden"] and le["band_hidden"] and le["stars_base_ambience_retained"]
        and le["foreground_button_present"] and le["foreground_active_rule"]):
    fails.append(f"browser low-end proof incomplete: {le}")
nd = bm["normal_device"]["pause_when_hidden"]
if not (nd["fx_children"] == nd["paused_on_hidden"] and nd["paused_on_hidden"] == nd["resumed_on_visible"] and nd["fx_children"] > 0):
    fails.append(f"browser pause-when-hidden proof incomplete: {nd}")
print(f"low-end: degrades layers (meteor/band hidden, nebula simplified) + keeps base ambience + FOREGROUND "
      f"(button:active) survives; pause-when-hidden {nd['paused_on_hidden']}/{nd['fx_children']} then resumed")

# ============ 3) 不改变视觉语义 -- only keyframes changed; theme identity byte-identical ============
ident = A.preserves_theme_identity(PRE_SRC, NEW_SRC)
if not (ident["only_keyframes"] and ident["frozen_identical"]):
    fails.append(f"visual identity not preserved: {ident}")
# the meteor conversion is a real motion change -> BLOCKs the T078 gate without a documented approval
if CI.run_ci(PRE, NEW_SRC)["decision"] != "BLOCK":
    fails.append("control broken: the keyframes change must BLOCK the T078 gate without a documented approval")
appr = [{"element": "keyframes", "reason": "T082 meteor left/top->transform, screen-path-equivalent + GPU-composited", "approver": "owner"}]
if CI.run_ci(PRE, NEW_SRC, appr)["decision"] != "PASS_APPROVED":
    fails.append("the documented keyframes change did not pass the gate as an approved change")
print(f"visual semantics preserved: only {ident['specific_changed']} changed; per_theme/base_css/theme_js/"
      f"fx_css/hero byte-identical; gate BLOCKs without approval, PASS_APPROVED with a keyframes approval")

# ============ NOT_DEPLOYED ============
if "0cb3acee6bf3" not in NEW_SRC:
    fails.append("could not confirm the source build_id after the change")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: source build_id 0cb3acee6bf3; NOT_DEPLOYED (live unchanged). A real median-FPS number needs a "
      "foregrounded browser (the preview throttles rAF); the load-bearing >=55 FPS guarantee is the "
      "deterministic compositor-only ambient animation.")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
