#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P01-T078 -- Visual / Motion Regression CI gate over the T077 un-deletable-contract baseline.

Every UI PR is checked against the frozen T077 baseline (visual_baseline.detect_regression): a candidate
worker source is diffed element-by-element. Any change to the theme/motion identity BLOCKS the PR unless it
carries an explicit approved-change record (element + a non-empty reason + an approver) -- so an accidental
deletion of a theme or ambience layer is blocked, while an intentional edit passes only when documented.
Changes are categorised VISUAL vs MOTION/RECORDING so a motion/brand loss is surfaced specifically.

Deterministic; no network / clock / randomness. NOT_DEPLOYED: pure gate logic over source hashes.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import visual_baseline as VB   # T077: detect_regression, asset_hashes, THEMES

# aggregate roll-up hashes move whenever ANY element moves; approvals are granted per SPECIFIC element.
AGGREGATE = {"master_visual", "contract_root"}
# elements whose change is a MOTION / RECORDING regression: keyframes, ambience layers + their animation
# CSS (fx_layers/fx_css), hero video/markup/assembly/wiring/asset-bytes, the DOM producers, reduced-motion,
# and the client-side behaviour that RUNS the motions (theme_js: blurTextIn/animateGauge/syncHeroVideo) +
# the anti-flash theme bootstrap (head_init).
MOTION_ELEMENTS = {"reduced_motion", "keyframes", "fx_layers", "fx_css", "hero_markup", "dom_producers",
                   "hero_section_fn", "hero_video_assets", "hero_wiring", "theme_js", "head_init"}

# the frozen source-hash contract is EXACT: a theme/motion source change is a diff of 1 (no tolerance).
SOURCE_DIFF_TOLERANCE = 0          # source hashes: exact; any diff is a regression (this is the enforced gate)
# The screenshot/pixel layer is NOT compared in this task (no PNGs are captured here -- see known_gaps);
# this constant is the DOCUMENTED policy tolerance for the future screenshot layer over the T077 matrix.
PIXEL_DIFF_TOLERANCE = 0.001       # screenshot layer policy: <=0.1% pixels may differ (font AA / GPU)
PIXEL_LAYER_ENFORCED = False       # honest: no pixel comparison is performed in this source-level gate


def _category(element):
    if element in AGGREGATE:
        return "aggregate"
    return "motion" if element in MOTION_ELEMENTS else "visual"


def _valid_approvals(approvals):
    """An approval is valid only when it is a dict with an element and a non-empty reason AND approver
    (allowed diffs must be explained). Malformed entries are ignored (fail-safe: they do not unblock)."""
    out = {}
    if not isinstance(approvals, (list, tuple)):
        return out
    for a in approvals:
        if not isinstance(a, dict):
            continue                                     # a non-dict entry cannot approve anything
        el = a.get("element")
        if el and str(a.get("reason", "")).strip() and str(a.get("approver", "")).strip():
            out[el] = a
    return out


def run_ci(baseline_hashes, candidate_src, approvals=None):
    """Gate a candidate worker source against the frozen baseline. BLOCK if any specific theme/motion
    element changed without a valid approved-change record; PASS clean; PASS_APPROVED if every change is
    documented. Returns the decision, the changed elements (categorised), and what it blocked on."""
    reg = VB.detect_regression(baseline_hashes, candidate_src)
    changed = {c["element"] for c in reg["changes"]}
    specific = changed - AGGREGATE                       # aggregates roll up; approvals target specifics
    approved = _valid_approvals(approvals)
    unapproved = sorted(e for e in specific if e not in approved)
    decision = "BLOCK" if unapproved else ("PASS_APPROVED" if specific else "PASS")
    return {
        "decision": decision,
        "blocked": bool(unapproved),
        "changed": sorted(changed),
        "changed_by_category": {"visual": sorted(e for e in specific if _category(e) == "visual"),
                                "motion": sorted(e for e in specific if _category(e) == "motion")},
        "blocked_on": unapproved,
        "approved_changes": sorted(e for e in specific if e in approved),
        "approval_reasons": {e: approved[e].get("reason") for e in specific if e in approved},
        "recording_checks": {"motion_regressions": sorted(e for e in specific if _category(e) == "motion")},
        "thresholds": {"source_diff_tolerance": SOURCE_DIFF_TOLERANCE,
                       "pixel_diff_tolerance": PIXEL_DIFF_TOLERANCE,
                       "pixel_layer_enforced": PIXEL_LAYER_ENFORCED,
                       "note": "The ENFORCED gate is the exact source-hash diff (any change blocks unless "
                               "approved). The <=0.1% pixel tolerance is the DOCUMENTED policy for the "
                               "future screenshot layer over the T077 matrix; no pixel comparison is "
                               "performed in this source-level gate (no PNGs are captured here)."},
    }
