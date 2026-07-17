#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-V02-P05 — re-freeze the six-theme visual/motion baseline onto the LIVE build.

WHY: T077 froze the contract against live build b189d3cc0703. Since then T079 (mobile overflow),
T080 (component states) and T082 (ambient-motion perf) each changed exactly one contract element,
were each independently reviewed and approved, and are now DEPLOYED. So `run_ci` against the frozen
T077 manifest BLOCKs on ['base_css','keyframes'] *unconditionally* -- including against HEAD itself.
A gate that blocks on everything is not a gate: it protects nothing, because its verdict no longer
carries information. (Same failure class as T086's always-true check and the T040 canary's vacuous
board3 gate.)

WHAT THIS IS NOT: a rubber stamp. Re-freezing is only legitimate if EVERY drifted element is
attributable to an already-approved, already-deployed change. This tool refuses to emit a new
baseline unless the drift set is exactly the attributable set below -- so an unexplained element
(i.e. a real regression someone slipped in) ABORTS the re-freeze instead of being blessed.

Deterministic: reads the committed worker; no network, no clock.
"""
import argparse
import json
import pathlib
import sys

V01 = pathlib.Path(__file__).resolve().parents[2] / "v0_1"
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB  # noqa: E402

FROZEN_T077 = V01 / "evidence" / "ADP-S7-P01-T077" / "visual_baseline_manifest.json"
OUT = pathlib.Path(__file__).resolve().parents[1] / "evidence" / "ADP-V02-P05-VISUAL-REFREEZE" / "visual_baseline_manifest.json"

# Every element allowed to have drifted since T077, and the approved+deployed task that changed it.
# master_visual is the aggregate over the whole theme/motion surface, so it necessarily moves when
# any component moves; it is attributable only because its components are.
ATTRIBUTION = {
    "base_css": "T079 (mobile overflow: .card overflow-wrap, img/svg/video max-width, <=520px table scroll) "
                "+ T080 (component-state matrix: :active/:disabled/[aria-busy]/:focus-visible/[data-state]/undo). "
                "Both documented base-CSS-only, independently reviewed, and deployed.",
    "keyframes": "T082 (ambient-motion perf: the cosmos meteor keyframe converted from layout-animating "
                 "left/top to a screen-path-equivalent transform:translate so every ambient loop is "
                 "compositor-safe). Documented as the ONLY contract element T082 changed; reviewed and deployed.",
    "master_visual": "aggregate hash over the whole theme/motion surface -- moves iff a component moves; "
                     "attributable because base_css and keyframes are.",
}


def drift(baseline_hashes, current):
    keys = sorted(set(baseline_hashes) | set(current))
    return [k for k in keys if baseline_hashes.get(k) != current.get(k)]


def build(live_build_id, allow=None):
    src = VB.WORKER.read_text("utf-8")
    current = VB.asset_hashes(VB.extract_contract(src))
    frozen = json.loads(FROZEN_T077.read_text(encoding="utf-8"))
    old = frozen["asset_hashes"]

    moved = drift(old, current)
    allowed = set(allow or ATTRIBUTION)
    unexplained = [k for k in moved if k not in allowed]

    # per-theme identity is the thing the Owner actually signed off at T077: surface it explicitly.
    themes_identical = old.get("per_theme") == current.get("per_theme")

    contract = VB.extract_contract(src)
    report = {
        "task": "ADP-V02-P05-VISUAL-REFREEZE",
        "supersedes": {"task": frozen["task"], "live_build_id": frozen["live_build_id"]},
        "iteration": "ITER-20260719-ADP-V02-INTEGRATE",
        "live_build_id": live_build_id,
        "release_mode": "PRODUCTION",
        "worker_source": frozen["worker_source"],
        "themes": frozen["themes"],
        "routes": frozen.get("routes"),
        "route_labels": frozen.get("route_labels"),
        "viewports": frozen.get("viewports"),
        "matrix_cells": frozen.get("matrix_cells"),
        "cells": frozen.get("cells"),
        "coverage": frozen.get("coverage"),
        # Carried forward from T077 -- this baseline is now the authoritative one, so anything T077
        # recorded that a consumer might read must NOT silently vanish here.
        "owner_confirmation_required": frozen.get("owner_confirmation_required"),
        "screenshot_schema": frozen.get("screenshot_schema"),
        "interaction_recording_schema": frozen.get("interaction_recording_schema"),
        "reduced_motion_separate": frozen.get("reduced_motion_separate"),
        # Recomputed LIVE (not copied): these are the compensating controls for the aggregate-only
        # escape -- an unregistered theme/ambience moves only master_visual, which run_ci excludes from
        # `specific`. visual_regression_ci's gate now fails on these too.
        "partition_consistency": VB.partition_consistency(src),
        "theme_set_consistency": VB.theme_set_consistency(contract),
        "drifted_since_t077": moved,
        "unexplained_drift": unexplained,
        "attribution": {k: ATTRIBUTION[k] for k in moved if k in ATTRIBUTION},
        "per_theme_identity_unchanged_since_t077": themes_identical,
        "asset_hashes": current,
    }
    return report, unexplained, themes_identical


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-build-id", required=True, help="the build id currently serving production")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    report, unexplained, themes_identical = build(args.live_build_id)

    print("drifted since T077:", report["drifted_since_t077"])
    print("per-theme identity unchanged since T077:", themes_identical)
    for k, why in report["attribution"].items():
        print(f"  {k}: {why[:88]}...")

    if unexplained:
        print("\nABORT: unexplained drift -- refusing to re-freeze:", unexplained)
        print("An element moved that no approved+deployed task accounts for. Re-freezing would "
              "silently bless it. Investigate before re-freezing.")
        return 2
    if not themes_identical:
        print("\nABORT: per-theme hashes changed since T077 -- that is the Owner-signed six-theme "
              "identity itself; re-freezing would bless a theme change without an Owner visual gate.")
        return 2

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("\nwrote", OUT)
    print("\nRE-FREEZE OK: every drifted element is attributable to an approved+deployed task; "
          "the six-theme identity itself is byte-identical to what the Owner signed at T077.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
