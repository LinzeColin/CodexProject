#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P01-T077 -- freeze the six-theme visual + key-motion baseline as an UN-DELETABLE contract.

The recently-restored six themes and their ambience/motion layer must never be silently deleted or
mutated. This module extracts that contract from the deployed worker source (deploy/cloudflare/
worker_cloud.js -- the live build b189d3cc0703) and pins it with deterministic asset hashes.

COMPLETENESS over the THEME + MOTION IDENTITY layer is the whole point. That look is driven by MANY things,
not just the colour-token block: the ~29 `[data-theme="X"]...` component rules, the `[data-fx=...]` /
`.fx-*` ambience-motion CSS, the `[data-hero=...]` rules, the HERO_CSS constant, the @keyframes, the
THEME_JS behaviour, the theme->nav/fx/hero/video mappings, the hero-section markup emitted by heroSection()
(hero video / cosmos dashboard DOM), and the visual DOM-producer functions those sections invoke
(blurChars -> techno blur-text-in, sparkSVG -> cosmos sparkline). So the contract is anchored on a MASTER
hash over that whole theme/motion surface (nothing in the theme/motion identity can change without changing
it), plus per-theme hashes for regression ATTRIBUTION (everything a theme owns), plus a SEPARATE
reduced-motion hash.

Scope note: this freezes the THEME/MOTION identity, not general page-content rendering (page bodies merely
consume theme tokens and are not part of the theme's visual contract). A deletion or any edit of a theme
rule, ambience-layer CSS/DOM, hero CSS/markup/video, a motion producer, the reduced-motion rule, a keyframe,
or a theme mapping changes a hash -> detect_regression flags it. This is the machine-verifiable backbone;
screenshots + recordings are Owner-facing evidence over the matrix this manifest enumerates.

release_mode NOT_DEPLOYED: reads the worker source only; no worker/production change. Deterministic
(no network, clock, or randomness).
"""
import hashlib
import pathlib
import re

THEMES = ("warm", "minimal", "fresh", "techno", "cosmos", "forest")
ROUTES = ("/", "/review", "/radar", "/system", "/history", "/search")
ROUTE_LABELS = {"/": "today", "/review": "queue", "/radar": "radar",
                "/system": "system", "/history": "history", "/search": "search"}
VIEWPORTS = (("mobile-sm", 320, 640), ("mobile", 375, 812), ("tablet", 768, 1024),
             ("desktop", 1280, 800), ("desktop-xl", 1440, 900))

# .../arxiv-daily-push/docs/pursuing_goal/v0_1/tools/visual_baseline.py -> parents[4] == arxiv-daily-push
WORKER = pathlib.Path(__file__).resolve().parents[4] / "deploy" / "cloudflare" / "worker_cloud.js"
ASSETS_MEDIA = WORKER.parent / "assets" / "media"   # self-hosted hero videos (/media/*.mp4)


def _asset_sha(web_path):
    """sha256 of a self-hosted asset's BYTES (e.g. /media/velorah.mp4 -> assets/media/velorah.mp4).
    Hashing the 64-char digest does not store the blob, so it respects the no-binaries rule while making a
    byte-swap of the same path detectable (a path-only hash would miss it)."""
    if not web_path or not web_path.startswith("/media/"):
        return f"<MISSING:asset:{web_path}>"
    f = ASSETS_MEDIA / web_path[len("/media/"):]
    return "sha256:" + hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else f"<MISSING:file:{web_path}>"


def _sha(s):
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()


def _tmpl(src, name):
    """Extract a `const NAME = ` ... ` ;` template-literal body verbatim -- handles both a plain const and
    an arrow function `const NAME = (...) => ` ... ` ;` (e.g. the PAGE shell). The non-greedy match stops at
    the statement's closing backtick-semicolon; nested `<option>` template backticks are not followed by a
    semicolon so they do not truncate it."""
    m = re.search(r"const\s+" + re.escape(name) + r"\s*=\s*(?:\([^)]*\)\s*=>\s*)?`(.*?)`\s*;", src, re.S)
    return m.group(1) if m else None


def _obj(src, name):
    m = re.search(r"const\s+" + re.escape(name) + r"\s*=\s*(\{.*?\})\s*;", src, re.S)
    return m.group(1) if m else None


def _hero_wiring(src):
    """The final render link: todayPage computes the hero (`const hero = heroSection(...)`) and passes it
    to PAGE (`PAGE('/', ..., { hero })`). Dropping `{ hero }` severs the chain -> no hero on the today page
    (a named key motion). Captured structurally (the heroSection call line + the count of hero passes), NOT
    by hashing todayPage's content, so a content edit does not falsely trip it."""
    m = re.search(r"const\s+hero\s*=\s*heroSection\([^;]*\);", src)
    line = m.group(0) if m else "<MISSING:hero_compute>"
    passes = len(re.findall(r",\s*\{\s*hero\s*\}\s*\)", src))   # PAGE('/', body, { hero }) occurrences
    return f"{line}|passes={passes}"


def _theme_options(src):
    """The `const THEME_OPTIONS = [['warm','暖纸学习'],...]` array -- the canonical enumeration of which
    six themes the `<select id=theme>` switcher OFFERS. Removing an entry deletes that theme from the
    product (its CSS/mappings survive only as unreachable dead code), so it is theme-identity data."""
    m = re.search(r"const\s+THEME_OPTIONS\s*=\s*(\[.*?\])\s*;", src, re.S)
    return m.group(1) if m else None


def _theme_option_keys(opts_text):
    return re.findall(r"\['(\w+)'", opts_text) if opts_text else []


def _theme_option_entry(opts_text, theme):
    m = re.search(r"\['" + re.escape(theme) + r"'[^\]]*\]", opts_text) if opts_text else None
    return m.group(0) if m else None


def _fn_body(src, name):
    """Extract a top-level `function NAME(...) { ... }` verbatim via brace matching. These functions emit
    visual DOM (e.g. blurChars -> the techno blur-text spans, sparkSVG -> the cosmos sparkline) but are not
    template literals, so they must be hashed explicitly or a key motion could be gutted undetected."""
    m = re.search(r"function\s+" + re.escape(name) + r"\s*\(", src)
    if not m:
        return None
    i = src.index("{", m.end())
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[m.start():j + 1]
    return None


# the visual DOM-producer functions the hero sections invoke, and the theme whose key motion each drives
DOM_PRODUCERS = {"blurChars": "techno", "sparkSVG": "cosmos"}


def _map(obj_text):
    if not obj_text:
        return {}
    return {k: v for k, v in re.findall(r"(\w+)\s*:\s*'([^']*)'", obj_text)}


def _theme_rules(src, theme):
    """EVERY css rule whose selector begins with `[data-theme="THEME"]` -- the token block AND all
    component/hero/nav overrides the theme owns. Sorted for order-independence."""
    return sorted(re.findall(r'\[data-theme="' + re.escape(theme) + r'"\][^{]*\{[^}]*\}', src))


def _fx_rules(src, fx):
    """The ambience-motion CSS for an fx: the `[data-fx="FX"]` visibility rule + all `.fx-FX ...` layer
    rules (the actual advanced-motion the baseline protects). 'none' has no ambience layer."""
    if not fx or fx == "none":
        return []
    vis = re.findall(r'\[data-fx="' + re.escape(fx) + r'"\][^{]*\{[^}]*\}', src)
    layer = re.findall(r'\.fx-' + re.escape(fx) + r'\b[^{]*\{[^}]*\}', src)
    return sorted(vis + layer)


def _reduced_motion(src):
    m = re.search(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{.*?\}\s*\}", src, re.S)
    return m.group(0) if m else None


def _hero_markup(src):
    """The hero-video and cosmos-dashboard markup skeletons emitted from heroSection() -- these live in
    LOCAL consts, not top-level template literals, but hold the `<video id=heroVideo>`, the `gaugeArc`,
    and the `.dash` grid that the interaction schema names as key motion. Hashed so deleting them is caught."""
    vid = re.search(r'<section class="hero hero-video".*?</section>', src, re.S)
    dash = re.search(r'<section class="hero hero-cosmic".*?</section>', src, re.S)
    return {"video": vid.group(0) if vid else None, "dash": dash.group(0) if dash else None}


def _keyframes(src):
    return sorted(re.findall(r"@keyframes\s+[A-Za-z0-9_]+\s*\{.*?\}\s*\}", src, re.S))


def _base_css(src):
    """The CSS constant with the rules already covered by other specific hashes stripped out (theme +
    component rules -> per_theme, ambience -> fx_css, keyframes, reduced-motion) so this hash attributes a
    change to the BASE styling (body, cards, layout) WITHOUT overlapping per_theme. The `${HERO_CSS}`
    injection token is DELIBERATELY retained: it is the sole point where the hero styling reaches any page,
    so removing it (hero renders unstyled) must move this hash. It does not overlap hero_css, which hashes
    the HERO_CSS constant's CONTENT, not the injection token."""
    css = _tmpl(src, "CSS") or ""
    css = re.sub(r'\[data-theme="[a-z]+"\][^{]*\{[^}]*\}', "", css)
    css = re.sub(r'\.fx-[a-z]+\b[^{]*\{[^}]*\}', "", css)
    css = re.sub(r'\[data-fx="[a-z]+"\][^{]*\{[^}]*\}', "", css)
    css = re.sub(r'@keyframes\s+[A-Za-z0-9_]+\s*\{.*?\}\s*\}', "", css, flags=re.S)
    return re.sub(r'@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{.*?\}\s*\}', "", css, flags=re.S)


def extract_contract(src=None):
    """Extract the full six-theme visual + motion contract from the worker source."""
    if src is None:
        src = WORKER.read_text(encoding="utf-8")
    nav = _map(_obj(src, "THEME_NAV"))
    fx = _map(_obj(src, "THEME_FX"))
    hero = _map(_obj(src, "THEME_HERO"))
    video = _map(_obj(src, "HERO_VIDEO"))
    hero_markup = _hero_markup(src)
    theme_options = _theme_options(src)
    themes = {}
    for t in THEMES:
        themes[t] = {"rules": _theme_rules(src, t), "nav": nav.get(t), "fx": fx.get(t),
                     "hero": hero.get(t), "video": video.get(t), "fx_rules": _fx_rules(src, fx.get(t)),
                     "option_entry": _theme_option_entry(theme_options, t)}
    return {"themes": themes, "nav": nav, "fx": fx, "hero": hero, "video": video,
            "reduced_motion": _reduced_motion(src), "keyframes": _keyframes(src),
            "hero_markup": hero_markup,
            "dom_producers": {fn: _fn_body(src, fn) for fn in DOM_PRODUCERS},
            # heroSection() assembles the hero DOM: `return video + dash` decides which hero is emitted.
            # Its body is render-wiring between PAGE's ${opts.hero} and the hashed hero fragments.
            "hero_section_fn": _fn_body(src, "heroSection"),
            # the self-hosted hero VIDEO bytes (not just the HERO_VIDEO paths) -- swapping bytes at the
            # same path would otherwise move no hash.
            "hero_video_assets": {t: _asset_sha(video.get(t)) for t in THEMES if video.get(t)},
            # the complete visual/motion source surfaces (the master-hash material)
            "css": _tmpl(src, "CSS"), "hero_css": _tmpl(src, "HERO_CSS"),
            "theme_js": _tmpl(src, "THEME_JS"), "head_init": _tmpl(src, "HEAD_INIT"),
            "fx_layers": _tmpl(src, "FX_LAYERS"),
            # the PAGE shell that WIRES the theme/motion identity into every served page (injects
            # ${CSS} ${HEAD_INIT} ${FX_LAYERS} ${THEME_JS} ${opts.hero}, the theme <select>, the html
            # data-theme default). A frozen ingredient PAGE stops injecting is inert -> hash it.
            "page_shell": _tmpl(src, "PAGE"),
            # the theme enumeration the switcher offers -- removing an entry deletes a theme from the UI
            "theme_options": theme_options, "theme_option_keys": _theme_option_keys(theme_options),
            # the final render link: todayPage passing the hero into PAGE (`{ hero }`)
            "hero_wiring": _hero_wiring(src),
            # the ambience-animation CSS (the .fx-* / [data-fx] rules that drive the moving layers). The
            # fx names are DERIVED from the THEME_FX mapping (not hardcoded) so fx_css stays in step with
            # _base_css's strip set even if a theme adds a new ambience layer.
            "fx_css": "\n".join(sorted(set(r for fxn in (set(fx.values()) - {"none", None})
                                           for r in _fx_rules(src, fxn)))),
            # the base styling (body/cards/layout) not attributed to any theme/fx/keyframe hash
            "base_css": _base_css(src)}


def _part(v, tag):
    return v if v is not None else f"<MISSING:{tag}>"


def asset_hashes(contract):
    """MASTER visual hash (whole surface -> nothing visual escapes) + per-theme attribution hashes +
    a SEPARATE reduced-motion hash + keyframes / fx-layers / hero-css hashes."""
    hm = contract["hero_markup"]
    prod = contract["dom_producers"]
    hsf = _part(contract["hero_section_fn"], "hero_section_fn")   # heroSection() render-wiring
    va = contract["hero_video_assets"]
    producer_by_theme = {theme: fn for fn, theme in DOM_PRODUCERS.items()}
    per_theme = {}
    for t in THEMES:
        c = contract["themes"][t]
        # the hero markup a theme actually renders: video markup for a video hero, dash markup for cosmos
        hero_dom = _part(hm["video"], "hero_video") if (c["hero"] == "video" or c["video"]) else (
            _part(hm["dash"], "hero_dash") if c["hero"] == "dash" else "")
        # the visual DOM-producer function that drives this theme's key motion (techno blur / cosmos spark)
        fn = producer_by_theme.get(t)
        producer_body = _part(prod.get(fn), f"producer:{fn}") if fn else ""
        # a themed hero (video or dash) is assembled by heroSection(); its byte-level video asset for video
        hero_wiring = hsf if c["hero"] != "none" else ""
        video_asset = _part(va.get(t), f"video_asset:{t}") if c["video"] else ""
        material = "\n".join(["\n".join(c["rules"]) or f"<MISSING:rules:{t}>",
                              _part(c["nav"], f"nav:{t}"), _part(c["fx"], f"fx:{t}"),
                              _part(c["hero"], f"hero:{t}"), _part(c["video"], f"video:{t}"),
                              "\n".join(c["fx_rules"]), hero_dom, producer_body,
                              _part(c["option_entry"], f"option:{t}"), hero_wiring, video_asset])
        per_theme[t] = _sha(material)
    producers_material = "\n".join(_part(prod[fn], f"producer:{fn}") for fn in DOM_PRODUCERS)
    video_assets_material = "\n".join(f"{t}={_part(va[t], f'video_asset:{t}')}" for t in sorted(va))
    master_material = "\n".join([
        _part(contract["css"], "css"), _part(contract["hero_css"], "hero_css"),
        _part(contract["theme_js"], "theme_js"), _part(contract["head_init"], "head_init"),
        _part(contract["fx_layers"], "fx_layers"), _part(contract["page_shell"], "page_shell"),
        _part(hm["video"], "hero_video"), _part(hm["dash"], "hero_dash"), producers_material, hsf,
        _part(contract["theme_options"], "theme_options"), video_assets_material,
        _part(contract["hero_wiring"], "hero_wiring"),
        str(contract["nav"]), str(contract["fx"]), str(contract["hero"]), str(contract["video"])])
    return {"per_theme": per_theme,
            "master_visual": _sha(master_material),          # completeness guarantee
            "reduced_motion": _sha(_part(contract["reduced_motion"], "reduced_motion")),
            "keyframes": _sha("\n".join(contract["keyframes"]) or "<MISSING:keyframes>"),
            "fx_layers": _sha(_part(contract["fx_layers"], "fx_layers")),
            "hero_css": _sha(_part(contract["hero_css"], "hero_css")),
            "hero_markup": _sha(_part(hm["video"], "hero_video") + "\n" + _part(hm["dash"], "hero_dash")),
            "dom_producers": _sha(producers_material),
            "hero_section_fn": _sha(hsf),                    # heroSection() assembly wiring
            "hero_video_assets": _sha(video_assets_material),  # the hero video BYTES
            "page_shell": _sha(_part(contract["page_shell"], "page_shell")),   # the theme/motion wiring
            "theme_options": _sha(_part(contract["theme_options"], "theme_options")),  # the theme enumeration
            "hero_wiring": _sha(_part(contract["hero_wiring"], "hero_wiring")),  # todayPage -> PAGE hero pass
            # SPECIFIC hashes for surfaces that otherwise only fed master_visual (so a change is ATTRIBUTED,
            # not just rolled into the aggregate): the client-side theme/motion behaviour (THEME_JS, which
            # runs blurTextIn/animateGauge/syncHeroVideo/reduced-motion), the anti-flash bootstrap
            # (HEAD_INIT), the whole CSS constant (base rules), and the ambience-animation CSS (.fx-* rules).
            "theme_js": _sha(_part(contract["theme_js"], "theme_js")),
            "head_init": _sha(_part(contract["head_init"], "head_init")),
            "base_css": _sha(_part(contract.get("base_css"), "base_css")),
            "fx_css": _sha(_part(contract.get("fx_css"), "fx_css")),
            "contract_root": _sha("|".join(per_theme[t] for t in THEMES))}


def theme_set_consistency(contract=None):
    """Cross-check the tool's hardcoded THEMES against the worker's actual theme-identity data structures:
    the switcher enumeration (THEME_OPTIONS) and the nav mapping (THEME_NAV) must offer exactly the same
    six themes. Catches a theme deleted from THEME_OPTIONS even if its CSS/mappings survive as dead code."""
    if contract is None:
        contract = extract_contract()
    option_keys = set(contract["theme_option_keys"])
    nav_keys = set(contract["nav"])
    themes = set(THEMES)
    return {"consistent": option_keys == themes == nav_keys,
            "themes": sorted(themes), "option_keys": sorted(option_keys), "nav_keys": sorted(nav_keys),
            "missing_from_options": sorted(themes - option_keys),
            "extra_in_options": sorted(option_keys - themes)}


def partition_consistency(src=None):
    """The base_css hash strips `[data-theme="X"]` and `.fx-X` / `[data-fx="X"]` rules assuming X is a
    REGISTERED theme / ambience name (covered by per_theme / fx_css). If a future theme or ambience layer
    appears in the CSS whose name is NOT registered, base_css would strip it while nothing else covers it
    -> a silent aggregate-only escape. This asserts every such name in the source IS registered, so the
    partition cannot diverge undetected."""
    if src is None:
        src = WORKER.read_text(encoding="utf-8")
    fx = _map(_obj(src, "THEME_FX"))
    registered_fx = set(fx.values()) - {"none", None}
    css_theme_names = set(re.findall(r'\[data-theme="([a-z]+)"\]', src))
    css_fx_names = set(re.findall(r'\.fx-([a-z]+)\b', src)) | set(re.findall(r'\[data-fx="([a-z]+)"\]', src))
    unregistered_themes = sorted(css_theme_names - set(THEMES))
    unregistered_fx = sorted(css_fx_names - registered_fx)
    return {"consistent": not unregistered_themes and not unregistered_fx,
            "registered_themes": sorted(THEMES), "registered_fx": sorted(registered_fx),
            "unregistered_themes": unregistered_themes, "unregistered_fx": unregistered_fx}


def baseline_matrix():
    contract = extract_contract()
    cells = []
    for t in THEMES:
        c = contract["themes"][t]
        for r in ROUTES:
            for vp, w, h in VIEWPORTS:
                cells.append({"theme": t, "route": r, "route_label": ROUTE_LABELS[r],
                              "viewport": vp, "width": w, "height": h,
                              "nav": c["nav"], "fx": c["fx"], "hero": c["hero"],
                              "has_video": bool(c["video"]),
                              "needs_reduced_motion_capture": c["fx"] != "none" or bool(c["video"])})
    return cells


def build_baseline():
    contract = extract_contract()
    hashes = asset_hashes(contract)
    cells = baseline_matrix()
    motion_themes = [t for t in THEMES if contract["themes"][t]["fx"] != "none"
                     or contract["themes"][t]["video"]]
    return {
        "themes": list(THEMES), "routes": list(ROUTES), "route_labels": ROUTE_LABELS,
        "viewports": [{"name": n, "width": w, "height": h} for n, w, h in VIEWPORTS],
        "matrix_cells": len(cells), "cells": cells, "asset_hashes": hashes,
        "reduced_motion_separate": True,
        "theme_set_consistency": theme_set_consistency(contract),
        "partition_consistency": partition_consistency(),
        "coverage": {"per_theme_rule_counts": {t: len(contract["themes"][t]["rules"]) for t in THEMES},
                     "fx_rule_counts": {t: len(contract["themes"][t]["fx_rules"]) for t in THEMES},
                     "keyframes": len(contract["keyframes"])},
        "screenshot_schema": {"per_cell": True, "count": len(cells),
                              "naming": "{theme}__{route_label}__{viewport}.png"},
        "interaction_recording_schema": {
            "motion_themes": motion_themes,
            "recordings": ["theme-switch (warm->each)", "hero-video play/pause on theme change",
                           "cosmos gauge count-up", "techno blur-text-in", "fx-layer ambience"],
            "reduced_motion_variant": "each recording re-run with prefers-reduced-motion: reduce "
                                      "(animations/transitions disabled; video paused)"},
        "owner_confirmation_required": True,   # S7 visual Owner gate: implementer does NOT self-confirm
    }


def detect_regression(baseline_hashes, new_src):
    """Recompute the contract hashes from a candidate worker source and diff against the frozen baseline.
    The MASTER visual hash catches ANY visual/motion change; the per-theme / reduced-motion / keyframes /
    fx-layers / hero-css hashes attribute it. Any difference is a regression (the contract moved)."""
    now = asset_hashes(extract_contract(new_src))
    changes = []
    for t in THEMES:
        if now["per_theme"][t] != baseline_hashes["per_theme"][t]:
            changes.append({"element": f"theme:{t}", "kind": "changed_or_deleted"})
    for key in ("master_visual", "reduced_motion", "keyframes", "fx_layers", "hero_css", "hero_markup",
                "dom_producers", "hero_section_fn", "hero_video_assets", "page_shell", "theme_options",
                "hero_wiring", "theme_js", "head_init", "base_css", "fx_css", "contract_root"):
        if now[key] != baseline_hashes[key]:
            changes.append({"element": key, "kind": "changed_or_deleted"})
    return {"regressed": bool(changes), "changes": changes}
