#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P03-T082 -- ambient-motion performance audit (optimize without changing visual semantics).

Acceptance (TASK_INDEX row 82): 中位 >=55 FPS；低端设备自动降级环境层但前景反馈不消失.
  (median >=55 FPS; low-end devices auto-degrade the ambient layers but the foreground feedback does not
   disappear.)

The load-bearing guarantee for >=55 FPS is COMPOSITOR-ONLY ambient animation: every infinite-loop (ambient)
keyframe must animate ONLY compositor-safe properties (transform / opacity / filter). Properties like
left/top/width/height trigger layout+paint every frame and cause jank. The single pre-fix offender was the
cosmos `meteor` keyframe (left/top); T082 converts it to a screen-path-equivalent transform:translate (the
.fx container is viewport-fixed, so left:-12%->100% == translateX 0->112vw and top:8%->64% == translateY
0->56vh). Pause-when-hidden + low-end degradation run in a router-injected FX_PERF controller that never
touches the foreground (component-state) selectors.

Deterministic; pure functions over the worker source. No network / clock / randomness.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import visual_baseline as VB

COMPOSITOR_SAFE = {"transform", "opacity", "filter"}   # animatable off the main thread (no layout/paint jank)
LAYOUT_TRIGGERS = {"left", "top", "right", "bottom", "width", "height", "margin", "margin-left",
                   "margin-top", "padding", "inset"}   # animating these forces layout every frame


def _src(src):
    return src if src is not None else VB.WORKER.read_text(encoding="utf-8")


def keyframe_props(src=None):
    """{keyframe_name: sorted[props it animates]} for every @keyframes in the worker."""
    src = _src(src)
    out = {}
    for m in re.finditer(r"@keyframes\s+([A-Za-z0-9_]+)\s*\{(.*?)\}\s*\}", src, re.S):
        out[m.group(1)] = sorted(set(re.findall(r"[;{]\s*([a-z-]+)\s*:", m.group(2))))
    return out


def ambient_loops(src=None):
    """Names of keyframes driven by an INFINITE animation (the continuous ambient loops)."""
    src = _src(src)
    css = VB._tmpl(src, "CSS") or ""
    names = set()
    for m in re.finditer(r"animation:\s*([^;}]*infinite[^;}]*)", css):
        for tok in re.findall(r"[A-Za-z0-9_]+", m.group(1)):
            if tok in keyframe_props(src):
                names.add(tok)
    return names


def ambient_compositor_safety(src=None):
    """Each ambient-loop keyframe -> whether it animates ONLY compositor-safe properties. The load-bearing
    >=55 FPS guarantee: all True means no ambient loop forces per-frame layout/paint."""
    props = keyframe_props(src)
    return {name: set(props.get(name, [])) <= COMPOSITOR_SAFE for name in sorted(ambient_loops(src))}


def all_ambient_compositor_safe(src=None):
    saf = ambient_compositor_safety(src)
    return bool(saf) and all(saf.values())


def keyframe_animates_layout(src, name):
    """True iff keyframe `name` animates any layout-triggering property (the jank source)."""
    return bool(set(keyframe_props(src).get(name, [])) & LAYOUT_TRIGGERS)


def meteor_converted(src=None):
    """The meteor keyframe must animate transform (not left/top) after T082."""
    src = _src(src)
    props = set(keyframe_props(src).get("meteor", []))
    return {"animates_transform": "transform" in props,
            "no_layout_props": not (props & LAYOUT_TRIGGERS),
            "props": sorted(props)}


def has_pause_offscreen(src=None):
    """The FX_PERF controller pauses ambient animation when the page is hidden (offscreen/background)."""
    src = _src(src)
    m = re.search(r"const FX_PERF_JS = `(.*?)`;", src, re.S)
    body = m.group(1) if m else ""
    return bool(body) and "visibilitychange" in body and "animationPlayState" in body and "paused" in body


def has_lite_degradation(src=None):
    """The FX_PERF controller degrades the heaviest ambient layers on low-end devices."""
    src = _src(src)
    m = re.search(r"const FX_PERF_JS = `(.*?)`;", src, re.S)
    body = m.group(1) if m else ""
    return {"detects_low_end": bool(body) and ("deviceMemory" in body and "hardwareConcurrency" in body and "saveData" in body),
            "degrades_layers": bool(body) and (".meteor" in body and ".band" in body and ".neb" in body),
            "sets_lite_flag": bool(body) and "data-fx-lite" in body}


def foreground_preserved(src=None):
    """The FX_PERF controller must NEVER touch foreground (component-state) selectors -- degradation only
    affects the ambient layers, so button feedback (T080) survives on low-end devices."""
    src = _src(src)
    m = re.search(r"const FX_PERF_JS = `(.*?)`;", src, re.S)
    body = m.group(1) if m else ""
    forbidden = ("button", ".gradeRow", ".btn", "grade(", "data-state", "aria-busy", ".picked", ".undo")
    return {"found": bool(body), "touches_no_foreground": bool(body) and not any(f in body for f in forbidden)}


def preserves_theme_identity(old_src, new_src):
    """The only contract element that may change is `keyframes` (the meteor conversion); the 6 themes'
    identity (per_theme), the base layout (base_css), the theme engine (theme_js), fx layers (fx_css) and
    every hero element stay byte-identical."""
    o = VB.asset_hashes(VB.extract_contract(old_src))
    n = VB.asset_hashes(VB.extract_contract(new_src))
    specific = sorted(e for e in o if o[e] != n.get(e) and e not in ("master_visual", "contract_root"))
    frozen = ("per_theme", "base_css", "theme_js", "fx_css", "reduced_motion", "hero_markup",
              "dom_producers", "hero_section_fn", "hero_video_assets", "head_init", "hero_css",
              "page_shell", "theme_options")
    return {"specific_changed": specific, "only_keyframes": specific == ["keyframes"],
            "frozen_identical": all(o[k] == n[k] for k in frozen)}
