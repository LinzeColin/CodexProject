#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P02-T079 acceptance: fix mobile overflow / data-dense layouts at 360/390/430.

Acceptance (TASK_INDEX row 79): 无全页横向滚动；局部表格横滚受控；现有高级视觉保持.
  (no full-page horizontal scroll; local table horizontal scroll is controlled; existing advanced visuals
   are preserved.)

Deterministic. Re-derives from the TOOL (mobile_overflow_audit) + the worker source + the frozen pre-fix
baseline. Load-bearing negative controls (this is what makes the audit non-vacuous):
  1. The T079 guards are DISCRIMINATING: the REAL pre-fix CSS (origin/main, saved as pre_fix_worker.js) must
     FAIL the audit (0/3), and stripping the T079 markers from the fixed CSS must also FAIL it -- so a "pass"
     cannot come from pre-existing rules the audit merely happens to match.
  2. The theme/motion identity is preserved (only base_css changed, re-derived by diffing the fixed worker
     against the pre-fix baseline via the T077/T078 contract).
  3. The responsive fix would BLOCK the T078 gate WITHOUT its documented approval (the gate is real).
Empirical render proof at 360/390/430 (documentElement.scrollWidth <= innerWidth) is in render_measurements.json.
"""
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
PRE_SRC = (T079 / "pre_fix_worker.js").read_text(encoding="utf-8")
PRE_CSS = VB._tmpl(PRE_SRC, "CSS")

fails = []

# ================================================ 1) 无全页横向滚动 (every T079-added overflow guard present)
guards = MO.audit(NEW_CSS)
for source, present in guards.items():
    if not present:
        fails.append(f"T079 overflow guard missing: {source}")
struct = MO.structural_guards(NEW_CSS)
for source, present in struct.items():
    if not present:
        fails.append(f"relied-upon pre-existing structural guard missing: {source}")
if NEW_CSS.count("{") != NEW_CSS.count("}"):
    fails.append("the base CSS is not brace-balanced after the fix")
print(f"T079 guards: {sum(guards.values())}/{len(guards)} present (long-text / media / table-local-scroll)")
print(f"pre-existing structural guards relied on: {sum(struct.values())}/{len(struct)} present")

# ---- NEGATIVE CONTROL 1a: the REAL pre-fix CSS must FAIL the audit (guards are genuinely T079-added) ----
pre_guards = MO.audit(PRE_CSS)
if any(pre_guards.values()):
    fails.append(f"control broken: the pre-fix CSS already satisfies a T079 guard (audit not discriminating): {pre_guards}")
# ---- NEGATIVE CONTROL 1b: stripping the T079 markers from the fixed CSS must also FAIL the audit ----
stripped_guards = MO.audit(MO.strip_t079_guards(NEW_CSS))
if any(stripped_guards.values()):
    fails.append(f"control broken: audit still passes after stripping T079 markers: {stripped_guards}")
print(f"negative control: pre-fix CSS scores {sum(pre_guards.values())}/{len(pre_guards)}; "
      f"stripped CSS scores {sum(stripped_guards.values())}/{len(stripped_guards)} (both must be 0)")

# ================================================ 2) 局部表格横滚受控 (table scrolls locally, no page band-aid)
ts = MO.table_scroll_is_local(NEW_CSS)
if not (ts["has_media_rule"] and ts["display_block"] and ts["overflow_x_auto"]):
    fails.append(f"a wide table does not scroll locally: {ts}")
if not ts["no_page_overflow_hidden_bandaid"]:
    fails.append("control broken: a page-level overflow-x:hidden band-aid is used instead of local scroll")
print("table scroll: local (display:block + overflow-x:auto), no page-level overflow-hidden band-aid")

# ================================================ 3) 现有高级视觉保持 (only base_css changed; motion/themes identical)
changed = {c["element"] for c in VB.detect_regression(PRE, NEW_SRC)["changes"]}
specific = sorted(e for e in changed if e not in ("master_visual", "contract_root"))
if specific != ["base_css"]:
    fails.append(f"the fix changed more than base_css (advanced visual not preserved): {specific}")
nh = VB.asset_hashes(VB.extract_contract(NEW_SRC))
if PRE["per_theme"] != nh["per_theme"]:
    fails.append("a per-theme hash changed -- a theme's visual identity was altered")
for k in ("theme_js", "keyframes", "fx_layers", "fx_css", "reduced_motion", "hero_markup",
          "dom_producers", "hero_section_fn", "hero_video_assets", "head_init", "hero_css"):
    if PRE[k] != nh[k]:
        fails.append(f"a motion element changed ({k}) -- advanced motion not preserved")
print(f"advanced visual preserved: specific change = {specific}; all 6 themes + every motion element byte-identical")

# the responsive fix is a real change: WITHOUT the documented approval the T078 gate BLOCKS it
if CI.run_ci(PRE, NEW_SRC)["decision"] != "BLOCK":
    fails.append("control broken: the responsive fix must BLOCK the gate without a documented approval")
appr = [{"element": "base_css", "reason": "T079 responsive overflow fix", "approver": "owner"}]
if CI.run_ci(PRE, NEW_SRC, appr)["decision"] != "PASS_APPROVED":
    fails.append("the documented responsive fix did not pass the gate as an approved change")
print("gate: fix BLOCKs without approval, PASS_APPROVED with a documented base_css approval")

# ================================================ deliverable: test matrix over 360/390/430
matrix = MO.test_matrix()
if not (len(matrix) == 15 and {m["width"] for m in matrix} == {360, 390, 430}):
    fails.append("test matrix does not cover 360/390/430 x the data-dense elements")

# ---- empirical render proof present (real browser at 360/390/430; no full-page scroll; counterfactual) ----
rm = json.loads((T079 / "render_measurements.json").read_text(encoding="utf-8"))
widths = {r["width"] for r in rm["fixed_css_renders"]}
if widths != {360, 390, 430} or any(r["hasPageHScroll"] for r in rm["fixed_css_renders"]):
    fails.append("render proof missing or shows a full-page horizontal scroll at some width")
if not rm["counterfactual_pre_fix_css"]["hasPageHScroll"]:
    fails.append("counterfactual broken: the pre-fix CSS should have shown a full-page scroll")
print(f"render proof: no full-page scroll at {sorted(widths)}; counterfactual pre-fix CSS DID scroll "
      f"({rm['counterfactual_pre_fix_css']['docScrollWidth']}px) -> fix is load-bearing")

# ================================================ NOT_DEPLOYED: live build unchanged (source not deployed)
if "b189d3cc0703" not in NEW_SRC and "9690390a9fc8" not in NEW_SRC:
    fails.append("could not confirm the build_id state")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: source build_id after the fix is 9690390a9fc8; the LIVE site still serves b189d3cc0703 "
      "(NOT_DEPLOYED). Empirical render proof at 360/390/430 is in render_measurements.json.")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
