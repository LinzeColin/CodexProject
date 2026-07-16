#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P02-T080 -- component-state / undo / cross-theme-persistence audit for the six-theme worker.

Acceptance (TASK_INDEX row 80): 点击 100ms 内反馈；切主题不丢阅读位置、答案、筛选和展开状态.
  (click feedback within 100ms; a theme switch does not lose reading position, answers, filters, expand
   state.)

Three deterministic, DISCRIMINATING checks (each proven load-bearing by a negative control in the verifier
-- the pre-fix T079 worker must FAIL them):

  1. STATE MATRIX -- every component state has a base-CSS rule: pressed (button:active), disabled
     (:disabled + [aria-disabled]), loading (button[aria-busy]), focus (:focus-visible), success/error
     ([data-state=ok]/[data-state=err]), undo (button.undo). Plus 100ms feedback: :active is native (fires
     on pointerdown, <16ms) and the transform transition is <= 100ms so the pressed state is visible in
     budget.
  2. UNDO defers the write -- the grade() CLICK handler no longer writes synchronously; it opens a
     cancelable countdown (_pend timer) and the /api/grade POST lives in a deferred gradeCommit(); gradeUndo()
     clears the timer and performs NO fetch, so an undo writes nothing (honours 不得改写既有生产数据).
  3. THEME SWITCH preserves state -- applyTheme() only swaps attributes + syncs hero/gauge; it never reloads,
     navigates, or rebuilds content DOM, so scroll / input values / details[open] survive a theme change.

release_mode NOT_DEPLOYED: reads the worker source only; the fix is committed to source but not deployed.
Deterministic; no network / clock / randomness.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import visual_baseline as VB   # reuse T077 extract_contract / detect_regression / _tmpl


# ---- component state matrix (base-CSS rules; each is T080-added, absent from the pre-fix worker) ----
STATE_RULES = {
    "pressed (button:active)": lambda css: "button:active{" in css,
    "disabled (:disabled + [aria-disabled])": lambda css: "button:disabled" in css and 'button[aria-disabled="true"]' in css,
    "loading (button[aria-busy])": lambda css: 'button[aria-busy="true"]' in css,
    "focus (:focus-visible)": lambda css: ":focus-visible" in css,
    "success ([data-state=ok])": lambda css: '[data-state="ok"]' in css,
    "error ([data-state=err])": lambda css: '[data-state="err"]' in css,
    "undo (button.undo)": lambda css: "button.undo{" in css,
}


def _css(css):
    return css if css is not None else (VB._tmpl(VB.WORKER.read_text(encoding="utf-8"), "CSS") or "")


def _src(src):
    return src if src is not None else VB.WORKER.read_text(encoding="utf-8")


def state_matrix(css=None):
    """Every component state has a base-CSS rule. Returns {state: bool}."""
    css = _css(css)
    return {name: bool(pred(css)) for name, pred in STATE_RULES.items()}


def feedback_within_100ms(css=None):
    """:active is native (pointerdown, <16ms); the transform transition must be <=100ms so the pressed state
    is fully visible within the 100ms budget."""
    css = _css(css)
    has_active = "button:active{" in css
    m = re.search(r"button\{transition:transform ([\d.]+)s", css)
    dur = float(m.group(1)) if m else None
    return {"has_active": has_active, "transform_transition_s": dur,
            "within_100ms": has_active and dur is not None and dur <= 0.1}


def _fn_bodies(src, sig):
    """All brace-matched bodies of a function whose text starts with `sig` (e.g. 'function gradeUndo()')."""
    bodies, start = [], 0
    while True:
        i = src.find(sig, start)
        if i < 0:
            break
        j = src.find("{", i)
        depth = 0
        for k in range(j, len(src)):
            if src[k] == "{":
                depth += 1
            elif src[k] == "}":
                depth -= 1
                if depth == 0:
                    bodies.append(src[j:k + 1])
                    start = k + 1
                    break
        else:
            break
    return bodies


def undo_defers_write(src=None):
    """The grade() click handler defers the write behind a cancelable undo window; undo performs no fetch."""
    src = _src(src)
    undo_bodies = _fn_bodies(src, "function gradeUndo()")
    return {
        "click_handler_not_async": src.count("async function grade(g,btn)") == 0 and src.count("function grade(g,btn)") >= 1,
        "cancelable_window": "_pend=setInterval(function(){left--;" in src,
        "deferred_commit_writes": src.count("async function gradeCommit(g,btn)") >= 1 and "fetch('/api/grade/" in src,
        "undo_cancels_timer": "function gradeUndo(){if(_pend){clearInterval(_pend)" in src,
        "undo_writes_nothing": bool(undo_bodies) and all("fetch" not in b for b in undo_bodies),
    }


def error_states_wired(src=None):
    """grade and run set [data-state=err] on a failed fetch (no more silent hang)."""
    src = _src(src)
    return {
        "grade_commit_try_catch": "async function gradeCommit(g,btn)" in src and 'r.setAttribute(\'data-state\',\'err\')' in src.replace('"', "'"),
        "run_try_catch": "async function run(b)" in src and 'catch(e)' in (_fn_bodies(src, "async function run(b)")[0] if _fn_bodies(src, "async function run(b)") else ""),
    }


def applytheme_preserves_state(src=None):
    """applyTheme swaps attributes + syncs hero/gauge only; it never reloads/navigates/rebuilds content, so
    scroll / inputs / details[open] survive a theme switch."""
    src = _src(src)
    bodies = _fn_bodies(src, "function applyTheme(n)")
    body = bodies[0] if bodies else ""
    return {
        "found": bool(body),
        "no_reload": bool(body) and "location.reload" not in body,
        "no_navigate": bool(body) and "location.href" not in body,
        "no_innerHTML_rebuild": bool(body) and "innerHTML" not in body,
        "persists_choice": bool(body) and "lsSet('adp-theme',n)" in body,
    }


def preserves_advanced_visual(old_src, new_src):
    """The fix must change ONLY base_css on the T077/T078 contract -- every theme/motion hash byte-identical."""
    base = VB.asset_hashes(VB.extract_contract(old_src))
    changed = {c["element"] for c in VB.detect_regression(base, new_src)["changes"]}
    specific = sorted(e for e in changed if e not in ("master_visual", "contract_root"))
    nh = VB.asset_hashes(VB.extract_contract(new_src))
    motion_keys = ("theme_js", "keyframes", "fx_layers", "fx_css", "reduced_motion", "hero_markup",
                   "dom_producers", "hero_section_fn", "hero_video_assets", "head_init", "hero_css")
    return {"specific_changed": specific, "only_base_css": specific == ["base_css"],
            "per_theme_identical": base["per_theme"] == nh["per_theme"],
            "motion_identical": all(base[k] == nh[k] for k in motion_keys)}
