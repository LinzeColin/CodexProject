#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P01-T078 acceptance: Visual/Motion Regression CI gate.

Acceptance (TASK_INDEX row 78): 删除任一主题/氛围层的模拟 PR 会被阻断；允许的像素差有说明.
  (a simulated PR that deletes any theme/ambience layer is BLOCKED; allowed pixel diffs are explained.)
Deliverables: visual diff thresholds, recording checks, approved-change process.

Deterministic. Re-derives from the TOOL (visual_regression_ci over the T077 baseline). Load-bearing:
  * a theme deletion and an ambience-layer deletion each BLOCK (the objective);
  * the gate does NOT over-block a benign non-visual edit (discrimination);
  * an approved change passes ONLY with a documented reason + approver, and only for its own element
    (the approved-change process; "allowed diffs are explained");
  * a motion/recording regression is surfaced in recording_checks.
"""
import importlib.util
import pathlib
import re
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB
import visual_regression_ci as CI

fails = []
BASELINE = VB.asset_hashes(VB.extract_contract())   # independently derived T077 baseline
src = VB.WORKER.read_text(encoding="utf-8")

delete_theme = re.sub(r'\[data-theme="forest"\]\{--bg[^}]*\}', "", src, count=1)   # delete forest's colour identity
delete_fx = src.replace('fx fx-cosmos', 'fx fx-GONE', 1)
delete_keyframe = src.replace("@keyframes frise", "@keyframes ZZ_frise", 1)
tweak_warm = src.replace('[data-theme="warm"]{--bg:#f3eee1', '[data-theme="warm"]{--bg:#f5f0e4', 1)
benign = src.replace("if (p === '/api/run')", "if (p === '/api/run' )", 1)

# ================================================ 1) 删除任一主题/氛围层的模拟 PR 会被阻断
r_theme = CI.run_ci(BASELINE, delete_theme)
if not (r_theme["decision"] == "BLOCK" and "theme:forest" in r_theme["blocked_on"]):
    fails.append(f"a theme-deletion PR was not blocked: {r_theme['decision']} {r_theme['blocked_on']}")
r_fx = CI.run_ci(BASELINE, delete_fx)
if not (r_fx["decision"] == "BLOCK" and "fx_layers" in r_fx["blocked_on"]):
    fails.append(f"an ambience-layer deletion PR was not blocked: {r_fx['decision']} {r_fx['blocked_on']}")
# discrimination: a benign non-visual edit must PASS (the gate does not block everything)
r_benign = CI.run_ci(BASELINE, benign)
if r_benign["decision"] != "PASS":
    fails.append(f"the gate over-blocked a benign non-visual edit: {r_benign['decision']} {r_benign['blocked_on']}")
print(f"blocking: delete-theme -> {r_theme['decision']} (on {r_theme['blocked_on'][:2]}...); "
      f"delete-fx-layer -> {r_fx['decision']} (on {r_fx['blocked_on']}); benign -> {r_benign['decision']}")

# ================================================ 2) approved-change process + 允许的像素差有说明
ok_appr = [{"element": "theme:warm", "reason": "brand refresh per Owner", "approver": "owner"}]
r_ok = CI.run_ci(BASELINE, tweak_warm, ok_appr)
if not (r_ok["decision"] == "PASS_APPROVED" and r_ok["approved_changes"] == ["theme:warm"]
        and r_ok["approval_reasons"].get("theme:warm")):
    fails.append(f"a documented approved change did not pass with its reason recorded: {r_ok}")
# an approval WITHOUT a reason must NOT unblock (allowed diffs must be explained)
r_noreason = CI.run_ci(BASELINE, tweak_warm, [{"element": "theme:warm", "reason": "", "approver": "owner"}])
if r_noreason["decision"] != "BLOCK":
    fails.append("control broken: an approval with no reason must still BLOCK (diffs must be explained)")
# an approval WITHOUT an approver must NOT unblock
r_noapprover = CI.run_ci(BASELINE, tweak_warm, [{"element": "theme:warm", "reason": "x", "approver": ""}])
if r_noapprover["decision"] != "BLOCK":
    fails.append("control broken: an approval with no approver must still BLOCK")
# an approval for the WRONG element must NOT unblock a different change
r_wrong = CI.run_ci(BASELINE, delete_theme, [{"element": "theme:cosmos", "reason": "x", "approver": "o"}])
if r_wrong["decision"] != "BLOCK":
    fails.append("control broken: an approval for element X must not unblock a change to element Y")
print(f"approved-change: documented -> {r_ok['decision']} (reason recorded); no-reason -> {r_noreason['decision']}; "
      f"no-approver -> {r_noapprover['decision']}; wrong-element -> {r_wrong['decision']}")

# ================================================ deliverable: visual diff thresholds documented
th = CI.run_ci(BASELINE, src)["thresholds"]
if not (th["source_diff_tolerance"] == 0 and 0 < th["pixel_diff_tolerance"] < 1 and th["note"]):
    fails.append("visual diff thresholds not documented (source exact + explained pixel tolerance)")
print(f"thresholds: source exact ({th['source_diff_tolerance']}), pixel tolerance {th['pixel_diff_tolerance']} explained")

# ================================================ deliverable: recording checks (motion regressions)
r_kf = CI.run_ci(BASELINE, delete_keyframe)
if not (r_kf["decision"] == "BLOCK" and "keyframes" in r_kf["recording_checks"]["motion_regressions"]):
    fails.append("a keyframe (motion) regression was not surfaced as a recording check")
if "fx_layers" not in r_fx["recording_checks"]["motion_regressions"]:
    fails.append("an ambience-layer loss was not categorised as a motion/recording regression")
# a pure VISUAL change (a colour token) is NOT mis-categorised as motion
if r_ok := CI.run_ci(BASELINE, tweak_warm):
    if "theme:warm" not in r_ok["changed_by_category"]["visual"]:
        fails.append("a colour-token change was not categorised as a visual change")
print(f"recording checks: keyframe -> motion regression {r_kf['recording_checks']['motion_regressions']}; "
      f"fx-layer -> motion; colour token -> visual")

# ================================================ MOTION LAYER: THEME_JS / HEAD_INIT / ambience CSS
# The client-side behaviour that RUNS the key motions lives in THEME_JS; the anti-flash bootstrap in
# HEAD_INIT. These previously fed only the aggregate master_visual (no specific hash) -> a motion deletion
# PASSED. They must now BLOCK and land in the motion/recording channel.
r_js = CI.run_ci(BASELINE, src.replace("if(n==='techno')blurTextIn();if(n==='cosmos')animateGauge();", "", 1))
if not (r_js["decision"] == "BLOCK" and "theme_js" in r_js["recording_checks"]["motion_regressions"]):
    fails.append("control broken: gutting THEME_JS motion dispatch did not BLOCK as a motion regression")
r_hi = CI.run_ci(BASELINE, src.replace("r.setAttribute('data-theme',s);r.setAttribute('data-nav',m[s]);", "", 1))
if not (r_hi["decision"] == "BLOCK" and "head_init" in r_hi["recording_checks"]["motion_regressions"]):
    fails.append("control broken: gutting the HEAD_INIT theme bootstrap did not BLOCK as a motion regression")
# the ambience-animation CSS (.fx-cosmos .stars{animation}) is a MOTION regression, not just visual
r_fxcss = CI.run_ci(BASELINE, src.replace(".fx-cosmos .stars{", ".fx-cosmos .stars{opacity:0;", 1))
if not (r_fxcss["decision"] == "BLOCK" and "fx_css" in r_fxcss["recording_checks"]["motion_regressions"]):
    fails.append("control broken: an ambience-animation CSS change was not surfaced as a motion regression")
# a BASE-CSS change (body/cards) blocks and is categorised visual (not motion, not overlapping per_theme)
r_base = CI.run_ci(BASELINE, src.replace("body{margin:0;background:var(--bg)", "body{margin:8px;background:var(--bg)", 1))
if not (r_base["decision"] == "BLOCK" and r_base["blocked_on"] == ["base_css"]):
    fails.append(f"control broken: a base-CSS change did not block cleanly on base_css: {r_base['blocked_on']}")
# deleting the ${HERO_CSS} injection token (the sole path hero styling reaches any page) must BLOCK -- it
# is the wiring, retained in base_css. A clean deletion previously moved only master_visual -> PASS.
r_herocss = CI.run_ci(BASELINE, src.replace("${HERO_CSS}", "", 1))
if not (r_herocss["decision"] == "BLOCK" and "base_css" in r_herocss["blocked_on"]):
    fails.append(f"control broken: removing the ${{HERO_CSS}} injection escaped the gate: {r_herocss}")
# a HERO_CSS CONTENT change still flags hero_css (not base_css) -- the two do not overlap
r_hccontent = CI.run_ci(BASELINE, src.replace("const HERO_CSS = `", "const HERO_CSS = `/*x*/", 1))
if "hero_css" not in r_hccontent["blocked_on"]:
    fails.append("control broken: a HERO_CSS content change did not flag hero_css")
print(f"motion layer: THEME_JS -> {r_js['decision']}(motion); HEAD_INIT -> {r_hi['decision']}(motion); "
      f"ambience CSS -> motion {r_fxcss['recording_checks']['motion_regressions']}; base-CSS -> {r_base['blocked_on']}")

# ================================================ malformed approvals fail SAFE (BLOCK, not crash)
for bad in (["stringentry"], [None], {"element": "x"}, "notalist", None):
    try:
        if CI.run_ci(BASELINE, delete_theme, bad)["decision"] != "BLOCK":
            fails.append(f"control broken: malformed approvals {bad!r} did not fail-safe to BLOCK")
    except Exception as e:
        fails.append(f"run_ci crashed on malformed approvals {bad!r}: {type(e).__name__}")
print("malformed approvals fail-safe to BLOCK (no crash)")

# ================================================ partition consistency (no silent future divergence)
# base_css strips [data-theme=X]/.fx-X assuming X is registered. If a NEW theme/ambience name appears in
# the CSS but is not registered, base_css would strip it while nothing covers it -> an aggregate-only
# escape. partition_consistency asserts every such name is registered, so the partition cannot diverge.
pc = VB.partition_consistency()
if not pc["consistent"]:
    fails.append(f"partition inconsistent -- an unregistered theme/fx name is in the CSS: {pc}")
# non-vacuous: an injected unregistered ambience name (.fx-aurora) must be flagged inconsistent
pc_bad = VB.partition_consistency(src.replace(".fx-cosmos .stars{", ".fx-aurora .stars{ } .fx-cosmos .stars{", 1))
if pc_bad["consistent"] or "aurora" not in pc_bad["unregistered_fx"]:
    fails.append("control broken: an unregistered .fx-aurora ambience name was not flagged")
print(f"partition consistency: registered themes {len(pc['registered_themes'])}, fx {pc['registered_fx']}; "
      f"unregistered .fx-aurora flagged")

# ================================================ reproducible
if CI.run_ci(BASELINE, delete_theme) != CI.run_ci(BASELINE, delete_theme):
    fails.append("the CI gate is not reproducible")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
