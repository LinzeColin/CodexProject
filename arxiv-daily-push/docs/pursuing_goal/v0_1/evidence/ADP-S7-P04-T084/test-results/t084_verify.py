#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P04-T084 acceptance: polish evidence/inference, content hierarchy, accessibility, reduced-motion.

Acceptance (TASK_INDEX row 84): 关键任务键盘/触屏完成；证据/推断区分清晰；reduced-motion 不丢功能.

Deterministic. Re-derives from the TOOL (a11y_content_audit) + the worker + the pre-T084 baseline.
Load-bearing negative controls:
  1. 证据/推断区分 is T084-ADDED: the pre-fix worker has NO provenance marker on the lesson (a reader could
     mistake the generated inference for the sourced 原文) -- so the check is discriminating.
  2. reduced-motion 不丢功能: a synthetic reduced-motion block WITHOUT the `.fr,.bw{opacity:1}` restore leaves
     the content invisible -- so the restore is load-bearing (not vacuous).
  3. reveal disclosure a11y is T084-added (pre-fix lacks aria-controls / focus move).
The browser proof (the 推断 marker renders, reveal moves focus, buttons keyboard-focusable) is in
browser_measurements.json. The polish is page-body so the six-theme visual/motion contract is byte-identical.
"""
import json
import pathlib
import re
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB
import a11y_content_audit as A

T084 = V01 / "evidence" / "ADP-S7-P04-T084"
NEW_SRC = VB.WORKER.read_text(encoding="utf-8")
PRE_SRC = (T084 / "pre_fix_worker.js").read_text(encoding="utf-8")

fails = []

# ============ 1) 关键任务键盘/触屏完成 ============
nat = A.interactive_native(NEW_SRC)
if not nat["all_native"]:
    fails.append(f"an onclick handler is on a non-native (unfocusable) element: {nat['non_native_tags']}")
names = A.buttons_have_names(NEW_SRC)
if not names["all_named"]:
    fails.append(f"{names['buttons_without_name']} button(s) have no accessible name")
tf = A.touch_and_focus()
# Honest, per-control touch check: acceptance is "关键任务键盘/触屏完成" (COMPLETABLE) -- primary controls
# meet the 44px AAA target, and EVERY control (incl. the compact .btn-sm reveal/study/undo at 34px) clears
# the WCAG 2.5.8 AA 24px floor and is keyboard-operable. The 34px .btn-sm is disclosed in known_gaps.md; we
# do NOT overclaim a universal 44px.
if not (tf["key_task_completable"] and tf["primary_meets_aaa"] and tf["all_meet_wcag_aa"] and tf["focus_visible"]):
    fails.append(f"key tasks not touch/keyboard completable: {tf}")
# NEGATIVE CONTROL: if any interactive control drops below the WCAG AA 24px floor, completability must flip.
css_now = VB._tmpl(NEW_SRC, "CSS") or ""
shrunk = css_now.replace(".btn-sm{min-height:34px", ".btn-sm{min-height:18px")
if shrunk == css_now:
    fails.append("control weak: could not locate the .btn-sm min-height to shrink -- negative control vacuous")
if A.touch_and_focus(shrunk)["key_task_completable"]:
    fails.append("control broken: shrinking .btn-sm below the 24px AA floor still reports completable -- vacuous")
rev = A.reveal_disclosure_a11y(NEW_SRC)
if not (rev["aria_controls"] and rev["moves_focus"] and rev["target_focusable"]):
    fails.append(f"reveal disclosure a11y incomplete: {rev}")
if any(A.reveal_disclosure_a11y(PRE_SRC).values()):
    fails.append("control broken: the pre-fix worker already had the reveal disclosure a11y (not T084-added)")
print(f"keyboard/touch: {nat['onclick_count']} handlers all on native button/a; every button named; "
      f"primary/grade/run {tf['button_min_height_px']}px (>=44 AAA), compact reveal/study/undo "
      f"{tf['btn_sm_min_height_px']}px (>=24 WCAG AA floor, tappable+keyboard, <44 AAA -- disclosed); "
      f":focus-visible present; reveal moves focus into the revealed box")

# ============ 2) 证据/推断区分清晰 ============
ei = A.evidence_inference_distinct(NEW_SRC)
if not (ei["provenance_note_defined"] and ei["note_marks_inference"] and ei["lessonHTML_uses_note"] and ei["source_evidence_link_present"]):
    fails.append(f"evidence/inference not clearly distinguished: {ei}")
# NEGATIVE CONTROL: the pre-fix lesson has NO provenance marker (a reader could mistake inference for source)
if A.evidence_inference_distinct(PRE_SRC)["provenance_note_defined"]:
    fails.append("control broken: the pre-fix worker already marks inference (provenance not T084-added)")
print(f"evidence/inference: the generated lesson carries a 推断 provenance marker (central lessonHTML) "
      f"distinct from the 原文 (evidence) link; pre-fix had none")

# ============ 3) reduced-motion 不丢功能 ============
rm = A.reduced_motion_preserves_content(NEW_SRC)
if not (rm["all_content_preserved"] and rm["reduced_motion_disables_animation"]):
    fails.append(f"reduced-motion loses content or does not disable animation: {rm}")
if not rm["opacity0_content"]:
    fails.append("control weak: no opacity:0 content elements found -- the preserve check would be vacuous")
# NEGATIVE CONTROL: remove the `.fr,.bw{opacity:1...}` restore -> content is NOT preserved
poisoned = NEW_SRC.replace(".fr,.bw{opacity:1!important;transform:none!important;filter:none!important}", "")
if A.reduced_motion_preserves_content(poisoned)["all_content_preserved"]:
    fails.append("control broken: removing the reduced-motion restore still 'preserves' content -- check is vacuous")
print(f"reduced-motion: disables animation but RESTORES content {rm['content_restored']} to opacity:1 "
      f"(decoration {rm['opacity0_decoration']} may stay hidden); removing the restore fails the check")

# ============ 4) 现有高级视觉保持 -- polish is page-body, contract byte-identical ============
pc = A.preserves_contract(PRE_SRC, NEW_SRC)
if not pc["contract_byte_identical"]:
    fails.append(f"the six-theme visual/motion contract changed (expected none -- polish is page-body): {pc['specific_changed']}")
print("advanced visual preserved: the six-theme visual/motion contract is byte-identical (polish is page-body)")

# ============ browser proof ============
bm = json.loads((T084 / "browser_measurements.json").read_text(encoding="utf-8"))
b = bm["checks"]
if not (b["provenance_marker_renders"] and b["reveal_moves_focus"] and b["grade_buttons_focusable"] and b["reduced_motion_rule_in_cssom_restores_content"]):
    fails.append(f"browser proof incomplete: {b}")
print(f"browser proof: 推断 marker renders; reveal moves focus into the box; grade buttons keyboard-focusable; "
      f"reduced-motion rule restores .fr/.bw in the CSSOM")

# ============ NOT_DEPLOYED ============
if "452f7c5de919" not in NEW_SRC:
    fails.append("could not confirm the source build_id after the change")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: page-body a11y/content polish (provenance marker + reveal disclosure focus); worker build "
      "452f7c5de919; six-theme contract byte-identical; NOT_DEPLOYED (live unchanged).")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
