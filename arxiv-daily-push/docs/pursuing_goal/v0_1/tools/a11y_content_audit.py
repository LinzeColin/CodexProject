#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P04-T084 -- accessibility + content-hierarchy audit for the six-theme worker.

Acceptance (TASK_INDEX row 84): 关键任务键盘/触屏完成；证据/推断区分清晰；reduced-motion 不丢功能.
  (key tasks completable by keyboard/touch; evidence vs inference clearly distinguished; reduced-motion does
   not lose function.)

Deterministic checks over the worker source:
  1. KEYBOARD/TOUCH -- every interactive handler (onclick) sits on a NATIVE focusable element (button / a),
     never a div/span (which a keyboard can't reach); every <button> has an accessible name (text content or
     aria-label); EVERY control's touch target is measured (base button 44px = AAA; compact .btn-sm 34px =
     above the WCAG 2.5.8 AA 24px floor, below 44px AAA) and key tasks are completable (>= AA floor +
     keyboard). :focus-visible exists (from T080).
  2. 证据/推断区分 -- the central lesson renderer (lessonHTML) prepends a provenance marker labelling the
     generated lesson as inference (推断), while the source is a 原文 (evidence) link -- so a reader cannot
     mistake the auto-generated summary for the original.
  3. REDUCED-MOTION -- every base-CSS opacity:0 element that is CONTENT (not a decorative .fx layer) is
     restored to opacity:1 by the prefers-reduced-motion block, so reduced motion loses no content/function.
  4. reveal disclosure a11y -- the reveal button carries aria-controls and moves focus into the revealed box.

No network / clock / randomness.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import visual_baseline as VB


def _src(src):
    return src if src is not None else VB.WORKER.read_text(encoding="utf-8")


def interactive_native(src=None):
    """Every onclick handler must be on a <button> or <a> (native focusable), not a <div>/<span>."""
    src = _src(src)
    # find the element tag immediately preceding each onclick=
    bad = []
    for m in re.finditer(r"<(\w+)[^>]*\bonclick=", src):
        if m.group(1) not in ("button", "a"):
            bad.append(m.group(1))
    total = len(re.findall(r"\bonclick=", src))
    return {"onclick_count": total, "non_native_tags": sorted(set(bad)), "all_native": not bad}


def buttons_have_names(src=None):
    """Every <button ...>...</button> has an accessible name: non-empty text content OR an aria-label."""
    src = _src(src)
    missing = 0
    for m in re.finditer(r"<button\b([^>]*)>(.*?)</button>", src, re.S):
        attrs, inner = m.group(1), m.group(2)
        has_aria = "aria-label=" in attrs
        # strip template `${...}` and tags to see if there's literal/expr text
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if not has_aria and not text:
            missing += 1
    return {"buttons_without_name": missing, "all_named": missing == 0}


# WCAG 2.5.8 (AA) minimum target size is 24x24 CSS px; 44px is the AAA (2.5.5) enhanced target.
WCAG_AA_MIN_PX = 24
WCAG_AAA_MIN_PX = 44


def _rule_min_height(css, selector):
    """min-height (px) declared inside the rule block whose selector is exactly `selector`."""
    m = re.search(r"(?:^|[^-\w.#])" + re.escape(selector) + r"\{[^}]*min-height:(\d+)px", css)
    return int(m.group(1)) if m else None


def touch_and_focus(css=None):
    """Measure EVERY interactive control's touch target -- not just the base button. The base `button`
    rule sizes primary controls (grade / run / recall) at 44px, but the compact `.btn-sm` class sizes the
    reveal / study(加入复习队列) / undo KEY-TASK buttons -- so a blanket 44px claim would be false for those.

    Acceptance is "关键任务键盘/触屏完成" (completable): a control is completable when it clears the WCAG
    2.5.8 AA 24px floor AND is keyboard-operable (:focus-visible). The compact .btn-sm controls are 34px --
    above the AA floor and fully tappable/keyboard-operable, but below the 44px AAA target (disclosed).
    """
    css = css if css is not None else (VB._tmpl(VB.WORKER.read_text(encoding="utf-8"), "CSS") or "")
    base = _rule_min_height(css, "button")      # grade / run / primary recall controls
    btn_sm = _rule_min_height(css, ".btn-sm")   # reveal / study(加入复习队列) / undo compact key-task controls
    targets = [h for h in (base, btn_sm) if h is not None]
    smallest = min(targets) if targets else None
    return {"button_min_height_px": base,
            "btn_sm_min_height_px": btn_sm,
            "smallest_target_px": smallest,
            "primary_meets_aaa": base is not None and base >= WCAG_AAA_MIN_PX,
            "all_meet_wcag_aa": smallest is not None and smallest >= WCAG_AA_MIN_PX,
            "focus_visible": ":focus-visible" in css,
            # key tasks completable by touch (every control >= AA floor) AND keyboard (focus-visible)
            "key_task_completable": (base is not None and base >= WCAG_AAA_MIN_PX
                                     and smallest is not None and smallest >= WCAG_AA_MIN_PX
                                     and ":focus-visible" in css)}


def evidence_inference_distinct(src=None):
    """The generated lesson (inference) is labelled distinct from the sourced 原文 (evidence)."""
    src = _src(src)
    prov = re.search(r"const PROVENANCE_NOTE = '([^']*)'", src)
    note = prov.group(1) if prov else ""
    return {"provenance_note_defined": bool(prov),
            "note_marks_inference": ("推断" in note),
            "lessonHTML_uses_note": bool(re.search(r"function lessonHTML\(lesson\)\s*\{[^{}]*PROVENANCE_NOTE", src, re.S)),
            "source_evidence_link_present": ">原文</a>" in src}


def reduced_motion_preserves_content(src=None):
    """Every base-CSS opacity:0 CONTENT element is restored by the reduced-motion block; only decorative .fx
    layers (e.g. .meteor) may stay hidden."""
    src = _src(src)
    # the animated content classes (.fr/.bw) live in HERO_CSS; expand it so they are visible to the audit.
    css = (VB._tmpl(src, "CSS") or "").replace("${HERO_CSS}", VB._tmpl(src, "HERO_CSS") or "")
    rm = re.search(r"@media\(prefers-reduced-motion:reduce\)\{([^@]*)\}\}", css)
    rm_body = rm.group(1) if rm else ""
    # every rule block that sets opacity:0 (the element would be invisible without its animation)
    opacity0 = set()
    for m in re.finditer(r"([.#][^{}]*?)\{[^{}]*opacity:0\b[^{}]*\}", css):
        sel = m.group(1).strip()
        if "prefers-reduced-motion" not in sel:
            opacity0.add(sel)
    decoration = {s for s in opacity0 if "meteor" in s or ".fx" in s}   # .fx ambient layers = decoration
    content = opacity0 - decoration
    # a content selector is preserved if its class token appears in the reduced-motion restore body w/ opacity:1
    restored = set()
    for sel in content:
        token = sel.split()[-1].lstrip(".")   # e.g. '.fr' -> 'fr'
        if re.search(r"\.%s\b" % re.escape(token), rm_body) and "opacity:1" in rm_body:
            restored.add(sel)
    return {"opacity0_content": sorted(content), "opacity0_decoration": sorted(decoration),
            "content_restored": sorted(restored), "all_content_preserved": content == restored,
            "reduced_motion_disables_animation": "animation:none!important" in rm_body}


def reveal_disclosure_a11y(src=None):
    """The reveal button links to and moves focus into the revealed content (proper disclosure a11y)."""
    src = _src(src)
    return {"aria_controls": 'id="revealBtn" aria-controls="revealBox"' in src,
            "moves_focus": "b.focus();" in src and "getElementById('revealBox')" in src,
            "target_focusable": 'id="revealBox" tabindex="-1"' in src}


def preserves_contract(old_src, new_src):
    """The polish lives in page-body functions -> the six-theme visual/motion contract is byte-identical."""
    o = VB.asset_hashes(VB.extract_contract(old_src))
    changed = [c["element"] for c in VB.detect_regression(o, new_src)["changes"] if c["element"] not in ("master_visual", "contract_root")]
    return {"specific_changed": sorted(changed), "contract_byte_identical": not changed}
