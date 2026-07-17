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
import argparse
import json
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


# ── ADP-V02-P05: a real entry point ────────────────────────────────────────────────────────────────
# Until now this module had NO __main__: running `python3 visual_regression_ci.py` exited 0 with zero
# output, so anything that "ran the gate" as a script got a vacuous pass. The gate only ever existed
# for callers that imported run_ci() and supplied a baseline themselves. This makes it runnable and
# gives it a load-bearing exit code (non-zero on BLOCK), and points it at the CURRENT baseline.
def _current_baseline_path():
    """Prefer the V0.2 re-frozen baseline (bound to the live build); fall back to the T077 freeze.

    The T077 manifest is bound to live build b189d3cc0703 and is STALE: the approved+deployed
    T079/T080 (base_css) and T082 (keyframes) changes mean it BLOCKs unconditionally -- even against
    HEAD -- which is a gate that carries no information.
    """
    v01 = pathlib.Path(__file__).resolve().parents[1]
    refreeze = v01.parent / "v0_2" / "evidence" / "ADP-V02-P05-VISUAL-REFREEZE" / "visual_baseline_manifest.json"
    if refreeze.exists():
        return refreeze, "v0_2 re-freeze (bound to the live build)"
    return (v01 / "evidence" / "ADP-S7-P01-T077" / "visual_baseline_manifest.json",
            "T077 freeze (STALE vs production -- expect unconditional BLOCK)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gate the worker's six-theme visual/motion contract against the frozen baseline.")
    ap.add_argument("--baseline", help="path to a visual_baseline_manifest.json (default: current)")
    ap.add_argument("--candidate", help="path to a candidate worker_cloud.js (default: the committed worker)")
    ap.add_argument("--approvals", help="path to a JSON list of {element,reason,approver} approved-change records")
    ap.add_argument("--json", action="store_true", help="emit the full report as JSON")
    args = ap.parse_args(argv)

    if args.baseline:
        bpath, which = pathlib.Path(args.baseline), "explicit --baseline"
    else:
        bpath, which = _current_baseline_path()
    baseline = json.loads(bpath.read_text(encoding="utf-8"))["asset_hashes"]
    src = pathlib.Path(args.candidate).read_text(encoding="utf-8") if args.candidate else VB.WORKER.read_text("utf-8")
    approvals = json.loads(pathlib.Path(args.approvals).read_text(encoding="utf-8")) if args.approvals else None

    rep = run_ci(baseline, src, approvals)

    # Compensating controls for the AGGREGATE-only escape: run_ci computes `specific = changed -
    # AGGREGATE`, so a change that moves ONLY master_visual/contract_root is not blocked. Adding an
    # UNREGISTERED theme/ambience (e.g. `[data-theme="neon"]{...}`) does exactly that: base_css strips
    # it as if it were registered, per_theme does not cover it, and only the aggregate moves -> PASS.
    # VB.partition_consistency() is the check that catches it, and nothing was calling it. Same for a
    # theme deleted from the switcher (theme_set_consistency). Wire both into the gate's verdict.
    contract = VB.extract_contract(src)
    partition = VB.partition_consistency(src)
    theme_set = VB.theme_set_consistency(contract)
    rep["partition_consistency"] = partition
    rep["theme_set_consistency"] = theme_set
    consistency_ok = partition["consistent"] and theme_set["consistent"]
    # The gate's verdict is run_ci's decision AND the consistency controls. Report it as one value so a
    # reader never sees "decision: PASS" next to a non-zero exit.
    rep["gate_result"] = "BLOCK" if (rep["decision"] == "BLOCK" or not consistency_ok) else rep["decision"]

    if args.json:
        # 机器消费者必须看到与 exit code 一致的判决:此前 JSON 仍带 run_ci 的原始
        # decision/blocked/blocked_on,在「仅一致性失败」时会显示 PASS 而 exit 却是 1。
        rep["decision_run_ci_only"] = rep["decision"]
        rep["decision"] = rep["gate_result"]
        rep["blocked"] = rep["gate_result"] == "BLOCK"
        if not consistency_ok:
            rep["blocked_on"] = sorted(set(rep.get("blocked_on") or []) | {
                k for k, ok in (("partition_consistency", partition["consistent"]),
                                ("theme_set_consistency", theme_set["consistent"])) if not ok})
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"baseline: {which} -> {bpath.name}")
        print(f"GATE: {rep['gate_result']}   (run_ci decision: {rep['decision']})")
        if rep.get("blocked_on"):
            print(f"blocked_on: {rep['blocked_on']}")
        for el in rep.get("changed", []):      # run_ci 的键是 `changed`(list[str]);写成 `changes` 时这段永不执行
            print(f"  changed: {el}")
        if not partition["consistent"]:
            print(f"partition_consistency: FAIL unregistered_themes={partition['unregistered_themes']} "
                  f"unregistered_fx={partition['unregistered_fx']}  <- aggregate-only escape")
        if not theme_set["consistent"]:
            print(f"theme_set_consistency: FAIL themes={theme_set['themes']} "
                  f"option_keys={theme_set['option_keys']} nav_keys={theme_set['nav_keys']} "
                  f"missing_from_options={theme_set['missing_from_options']} "
                  f"extra_in_options={theme_set['extra_in_options']}")
    # LOAD-BEARING exit code: BLOCK must fail the caller, not exit 0 like the old bare run did.
    return 1 if (rep["decision"] == "BLOCK" or not consistency_ok) else 0


if __name__ == "__main__":
    sys.exit(main())
