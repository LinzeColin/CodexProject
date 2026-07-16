#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P01-T078 generator -- run the Visual/Motion Regression CI gate on simulated UI PRs against the
frozen T077 baseline, and write the report."""
import json
import pathlib
import re
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB
import visual_regression_ci as CI

BASELINE = VB.asset_hashes(VB.extract_contract())          # the frozen T077 baseline hashes
SRC = VB.WORKER.read_text(encoding="utf-8")


def _pr_delete_theme(src):
    return re.sub(r'\[data-theme="forest"\]\{--bg[^}]*\}', "", src, count=1)   # delete forest's colour identity


def _pr_delete_fx_layer(src):
    return src.replace('fx fx-cosmos', 'fx fx-GONE', 1)                # remove the cosmos ambience layer


def _pr_intentional_token(src):
    return src.replace("[data-theme=\"warm\"]{--bg:#f3eee1", "[data-theme=\"warm\"]{--bg:#f5f0e4", 1)  # tweak warm bg


def _pr_gut_motion(src):   # remove the client-side key-motion dispatch (techno blur / cosmos gauge) in THEME_JS
    return src.replace("if(n==='techno')blurTextIn();if(n==='cosmos')animateGauge();", "", 1)


def _pr_benign(src):
    return src.replace("if (p === '/api/run')", "if (p === '/api/run' )", 1)   # non-visual server edit


def build():
    prs = [
        {"name": "benign-server-edit", "src": _pr_benign(SRC), "approvals": []},
        {"name": "delete-theme (forest)", "src": _pr_delete_theme(SRC), "approvals": []},
        {"name": "delete-fx-layer (cosmos ambience)", "src": _pr_delete_fx_layer(SRC), "approvals": []},
        {"name": "gut-key-motion (THEME_JS blur/gauge dispatch)", "src": _pr_gut_motion(SRC), "approvals": []},
        {"name": "intentional-warm-bg (approved)", "src": _pr_intentional_token(SRC),
         "approvals": [{"element": "theme:warm", "reason": "brand refresh: warmer paper background per Owner",
                        "approver": "owner"}]},
        {"name": "intentional-warm-bg (unexplained approval)", "src": _pr_intentional_token(SRC),
         "approvals": [{"element": "theme:warm", "reason": "", "approver": "owner"}]},
        {"name": "delete-theme with wrong-element approval", "src": _pr_delete_theme(SRC),
         "approvals": [{"element": "theme:cosmos", "reason": "unrelated", "approver": "owner"}]},
    ]
    results = []
    for pr in prs:
        r = CI.run_ci(BASELINE, pr["src"], pr["approvals"])
        results.append({"pr": pr["name"], "decision": r["decision"], "blocked": r["blocked"],
                        "blocked_on": r["blocked_on"], "approved_changes": r["approved_changes"],
                        "changed_by_category": r["changed_by_category"]})
    return {"iteration": "ITER-20260716-ADP-V01-FINAL-EXECUTION", "task": "ADP-S7-P01-T078",
            "release_mode": "NOT_DEPLOYED", "baseline_from": "T077 visual_baseline contract",
            "thresholds": CI.run_ci(BASELINE, SRC)["thresholds"], "simulated_prs": results}


if __name__ == "__main__":
    rep = build()
    for r in rep["simulated_prs"]:
        print(f"  {r['decision']:14} {r['pr']}"
              + (f"  blocked_on={r['blocked_on']}" if r["blocked_on"] else "")
              + (f"  approved={r['approved_changes']}" if r["approved_changes"] else ""))
    out = V01 / "evidence" / "ADP-S7-P01-T078" / "visual_regression_ci_report.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)
