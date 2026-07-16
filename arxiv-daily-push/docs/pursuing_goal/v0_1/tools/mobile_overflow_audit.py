#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P02-T079 -- mobile-overflow audit for the six-theme worker at 360/390/430 widths.

Every source of horizontal overflow in a data-dense page must be neutralised so the page never scrolls
sideways as a whole, while a wide TABLE is allowed to scroll LOCALLY inside its card.

The audit is deliberately DISCRIMINATING (a plain substring scan over-counts, because markers like
`min-width:0` / `box-sizing:border-box` already exist in the pre-fix CSS -- an audit that credited those to
T079 would still "pass" if the T079 additions were reverted). So it separates:

  * T079_GUARDS -- the guards T079 actually ADDED, each checked IN CONTEXT and each ABSENT from the pre-fix
    CSS (proven by the negative control in the verifier: strip these markers and the audit must fail):
      - long unbroken text (URLs / 文号 / DOIs / relations) -> overflow-wrap:break-word ON the .card rule
      - content media (img / svg / video)                   -> main img,main svg,main video{max-width:100%}
      - data-dense tables (数据源/运行历史/复习队列/往期)      -> table becomes a scrollable block at <=520px
  * PREEXISTING_STRUCTURAL -- guards T079 RELIES ON but did not add (verified present, reported separately,
    never credited to T079): flex children can shrink (.itemrow .body{min-width:0}) and border-box sizing.

release_mode NOT_DEPLOYED: reads the worker source only; the fix is committed to source but not deployed
(the live build is unchanged). Deterministic; no network / clock / randomness.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import visual_baseline as VB   # reuse T077 extract_contract / detect_regression

WIDTHS = (360, 390, 430)       # the mobile widths in scope


def _card_has(css, decl):
    """True iff `decl` appears INSIDE a `.card{...}` rule (contextual, not floating elsewhere in the CSS)."""
    return any(decl in m.group(1) for m in re.finditer(r"\.card\{([^}]*)\}", css))


# T079-load-bearing guards -- each keyed to a predicate that proves the guard is present in the RIGHT place.
T079_GUARDS = {
    "long-text wraps (.card overflow-wrap:break-word)": lambda css: _card_has(css, "overflow-wrap:break-word"),
    "media fits (main img,svg,video max-width:100%)": lambda css: "main img,main svg,main video{max-width:100%}" in css,
    "table local scroll (@media<=520px display:block+overflow-x:auto)":
        lambda css: "@media(max-width:520px){table{display:block;overflow-x:auto" in css,
}

# guards T079 relies on but did NOT add -- verified present, reported separately, never credited to T079.
PREEXISTING_STRUCTURAL = {
    "flex child shrink (.itemrow .body min-width:0)": ".itemrow .body{flex:1;min-width:0}",
    "border-box sizing (*{box-sizing:border-box})": "*{box-sizing:border-box}",
}


def _css(css):
    return css if css is not None else (VB._tmpl(VB.WORKER.read_text(encoding="utf-8"), "CSS") or "")


def audit(css=None):
    """Confirm every T079-added overflow guard is present in the right context. Returns {name: bool}."""
    css = _css(css)
    return {name: bool(pred(css)) for name, pred in T079_GUARDS.items()}


def structural_guards(css=None):
    """Confirm the pre-existing structural guards T079 relies on are present. Returns {name: bool}."""
    css = _css(css)
    return {name: (marker in css) for name, marker in PREEXISTING_STRUCTURAL.items()}


def strip_t079_guards(css):
    """Remove exactly the T079-added guards from the CSS -- used as a negative control: the stripped CSS
    must FAIL audit(), proving the guards are load-bearing T079 additions rather than pre-existing rules the
    audit merely happens to match."""
    css = css.replace("main img,main svg,main video{max-width:100%}", "")
    css = re.sub(r"@media\(max-width:520px\)\{table\{[^}]*\}\}", "", css)
    # drop overflow-wrap:break-word only from within .card rules
    css = re.sub(r"(\.card\{[^}]*?);?overflow-wrap:break-word", r"\1", css)
    return css


def table_scroll_is_local(css=None):
    """A wide table must scroll inside its own block (overflow-x:auto), not push the page. It must NOT use
    a page-level `overflow-x:hidden` band-aid (which would clip content instead of scrolling it)."""
    css = _css(css)
    m = re.search(r"@media\(max-width:520px\)\{table\{([^}]*)\}", css)
    body = m.group(1) if m else ""
    return {"has_media_rule": bool(m), "display_block": "display:block" in body,
            "overflow_x_auto": "overflow-x:auto" in body,
            "no_page_overflow_hidden_bandaid": "body{overflow-x:hidden" not in css and "html{overflow-x:hidden" not in css}


def test_matrix():
    """The width x data-dense-element matrix with the guard that keeps each within the viewport."""
    elements = [("long URL / 原文链接", "overflow-wrap:break-word", "wraps"),
                ("文号 / DOI / 机构号", "overflow-wrap:break-word", "wraps"),
                ("数据源 / 运行历史 / 复习队列 / 往期 表格", "table{display:block;overflow-x:auto}", "local scroll"),
                ("跨源关系 / diff 文本", "overflow-wrap:break-word", "wraps"),
                ("内容图片 / SVG / 视频", "max-width:100%", "fits")]
    return [{"width": w, "element": el, "guard": g, "behaviour": b}
            for w in WIDTHS for el, g, b in elements]


def preserves_advanced_visual(old_src, new_src):
    """The responsive fix must change ONLY the base CSS -- every theme/motion identity hash byte-identical.
    Returns the changed specific elements (should be exactly ['base_css'])."""
    base = VB.asset_hashes(VB.extract_contract(old_src))
    changed = {c["element"] for c in VB.detect_regression(base, new_src)["changes"]}
    specific = sorted(e for e in changed if e not in ("master_visual", "contract_root"))
    oh, nh = base, VB.asset_hashes(VB.extract_contract(new_src))
    motion_keys = ("theme_js", "keyframes", "fx_layers", "fx_css", "reduced_motion", "hero_markup",
                   "dom_producers", "hero_section_fn", "hero_video_assets", "head_init", "hero_css")
    return {"specific_changed": specific, "only_base_css": specific == ["base_css"],
            "per_theme_identical": oh["per_theme"] == nh["per_theme"],
            "motion_identical": all(oh[k] == nh[k] for k in motion_keys)}
