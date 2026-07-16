#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P02-T079 generator -- audit the mobile-overflow fix (discriminating guards + negative controls),
build the test matrix, and run it through the T078 CI gate as a documented approved change (base_css only;
theme/motion identity preserved)."""
import json
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB
import visual_regression_ci as CI
import mobile_overflow_audit as MO

T079 = V01 / "evidence" / "ADP-S7-P02-T079"
PRE = json.loads((T079 / "pre_fix_baseline.json").read_text(encoding="utf-8"))["asset_hashes"]
NEW_SRC = VB.WORKER.read_text(encoding="utf-8")
NEW_CSS = VB._tmpl(NEW_SRC, "CSS")
PRE_CSS = VB._tmpl((T079 / "pre_fix_worker.js").read_text(encoding="utf-8"), "CSS")


def build():
    guards = MO.audit(NEW_CSS)
    struct = MO.structural_guards(NEW_CSS)
    tscroll = MO.table_scroll_is_local(NEW_CSS)
    # negative controls: pre-fix CSS and stripped CSS must both fail the audit (guards are load-bearing)
    neg_prefix = MO.audit(PRE_CSS)
    neg_stripped = MO.audit(MO.strip_t079_guards(NEW_CSS))
    # theme/motion preservation: diff the (fixed) worker against the frozen pre-fix baseline hashes
    changed = {c["element"] for c in VB.detect_regression(PRE, NEW_SRC)["changes"]}
    specific = sorted(e for e in changed if e not in ("master_visual", "contract_root"))
    nh = VB.asset_hashes(VB.extract_contract(NEW_SRC))
    motion_keys = ("theme_js", "keyframes", "fx_layers", "fx_css", "reduced_motion", "hero_markup",
                   "dom_producers", "hero_section_fn", "hero_video_assets", "head_init", "hero_css")
    preserve = {"specific_changed": specific, "only_base_css": specific == ["base_css"],
                "per_theme_identical": PRE["per_theme"] == nh["per_theme"],
                "motion_identical": all(PRE[k] == nh[k] for k in motion_keys)}
    approval = [{"element": "base_css", "approver": "owner",
                 "reason": "T079 responsive mobile-overflow fix: overflow-wrap on cards, local table scroll "
                           "at <=520px, media max-width -- base layout only, no theme/motion change"}]
    gate = CI.run_ci(PRE, NEW_SRC, approval)
    gate_unapproved = CI.run_ci(PRE, NEW_SRC)
    render = json.loads((T079 / "render_measurements.json").read_text(encoding="utf-8"))
    return {"iteration": "ITER-20260716-ADP-V01-FINAL-EXECUTION", "task": "ADP-S7-P02-T079",
            "release_mode": "NOT_DEPLOYED",
            "live_build_id_unchanged": "b189d3cc0703", "source_build_id_after_fix": "9690390a9fc8",
            "t079_guards": guards, "preexisting_structural_guards": struct,
            "negative_controls": {"prefix_css_audit": neg_prefix, "stripped_css_audit": neg_stripped,
                                  "prefix_all_false": not any(neg_prefix.values()),
                                  "stripped_all_false": not any(neg_stripped.values())},
            "table_scroll_local": tscroll, "advanced_visual_preserved": preserve,
            "gate_with_approval": {"decision": gate["decision"], "approved": gate["approved_changes"]},
            "gate_without_approval": {"decision": gate_unapproved["decision"],
                                      "blocked_on": gate_unapproved["blocked_on"]},
            "empirical_render": {"widths": [r["width"] for r in render["fixed_css_renders"]],
                                 "any_page_hscroll": any(r["hasPageHScroll"] for r in render["fixed_css_renders"]),
                                 "counterfactual_prefix_scrolls": render["counterfactual_pre_fix_css"]["hasPageHScroll"]},
            "test_matrix": MO.test_matrix()}


if __name__ == "__main__":
    rep = build()
    print("t079 guards:", rep["t079_guards"])
    print("structural guards:", rep["preexisting_structural_guards"])
    print("negative controls (both must be all-false):", rep["negative_controls"]["prefix_all_false"],
          rep["negative_controls"]["stripped_all_false"])
    print("table scroll local:", rep["table_scroll_local"])
    print("advanced visual preserved:", rep["advanced_visual_preserved"])
    print("gate with approval:", rep["gate_with_approval"], "| without:", rep["gate_without_approval"])
    print("empirical render:", rep["empirical_render"])
    out = T079 / "mobile_overflow_report.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)
