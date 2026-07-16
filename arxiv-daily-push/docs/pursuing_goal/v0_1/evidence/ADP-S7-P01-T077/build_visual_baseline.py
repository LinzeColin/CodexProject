#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P01-T077 generator -- write the frozen six-theme visual + motion baseline manifest.

The manifest is the un-deletable-contract backbone: the 6x6x5 coverage matrix, the deterministic asset
hashes (per-theme + separate reduced-motion + fx-layers + keyframes), and the screenshot / interaction-
recording schema. Owner-facing screenshots are captured separately (representative sample) and referenced.
"""
import json
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB


def build():
    b = VB.build_baseline()
    return {"iteration": "ITER-20260716-ADP-V01-FINAL-EXECUTION", "task": "ADP-S7-P01-T077",
            "release_mode": "NOT_DEPLOYED", "live_build_id": "b189d3cc0703",
            "worker_source": "arxiv-daily-push/deploy/cloudflare/worker_cloud.js", **b}


if __name__ == "__main__":
    m = build()
    out = V01 / "evidence" / "ADP-S7-P01-T077" / "visual_baseline_manifest.json"
    out.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print("themes:", m["themes"])
    print("routes:", [m["route_labels"][r] for r in m["routes"]])
    print("viewports:", [v["name"] for v in m["viewports"]])
    print("matrix cells:", m["matrix_cells"])
    print("contract_root:", m["asset_hashes"]["contract_root"])
    print("per-theme hashes:")
    for t, h in m["asset_hashes"]["per_theme"].items():
        print(f"   {t:8} {h}")
    print("reduced_motion (separate):", m["asset_hashes"]["reduced_motion"])
    print("wrote", out)
