#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T049 acceptance: A1 provincial-portal adapter FAMILY.

Acceptance (TASK_INDEX): 至少 3 种不同省级站点模板通过；特殊逻辑限制在 profile。
Deterministic, offline (real captured fixtures under ../fixtures; no network here). Proves ONE
generic connector class + declarative SiteProfiles covers >=3 provincial portals across >=2 template
families, and that province-specific logic is confined to the profiles/hooks -- the connector class
body itself contains ZERO province literals.
"""
import sys, json, re, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import adapter_a1_province as A

FX = V01 / "evidence" / "ADP-S4-P03-T049" / "fixtures"
ART_URL = {
    "jiangsu-gov": "http://www.jiangsu.gov.cn/art/2026/7/14/art_46144_11803435.html",
    "shandong-gov": "http://www.shandong.gov.cn/art/2026/7/9/art_94237_10361274.html",
    "beijing-gov": "https://www.beijing.gov.cn/zhengce/zhengcefagui/202607/t20260715_4764203.html",
}
FXNAME = {"jiangsu-gov": "jiangsu", "shandong-gov": "shandong", "beijing-gov": "beijing"}
fails = []

# --- run the family contract over every profile's real fixtures ------------------------------
results = []
for sid in A.PROFILES:
    base = FXNAME[sid]
    listing = (FX / f"{base}_list.html").read_text(encoding="utf-8")
    article = (FX / f"{base}_article.html").read_text(encoding="utf-8")
    r = A.run_contract(sid, listing, article, ART_URL[sid])
    results.append(r)
    print(f"[{sid}] family={r['template_family']} pass={r['passed']} level={r['authority_level']} "
          f"discover={r['discovered']} docnum={r['doc_number']} date={r['doc_date']} atts={r['attachments']}")
    print(f"    raw='{r['raw_title'][:40]}...' -> clean='{r['clean_title'][:40]}...'")
    for k, v in r["checks"].items():
        if not v:
            fails.append(f"{sid}: check '{k}' failed")

passed = [r for r in results if r["passed"]]
families = {r["template_family"] for r in passed}
print(f"\nprofiles passing: {len(passed)}/{len(results)} | template families: {sorted(families)}")

# --- acceptance 1: >= 3 distinct provincial site templates pass ------------------------------
if len(passed) < 3:
    fails.append(f"only {len(passed)} provincial templates pass (< 3)")
if len({r['source_id'] for r in passed}) < 3:
    fails.append("fewer than 3 distinct provincial sources pass")
if len(families) < 2:
    fails.append(f"only {len(families)} template family covered (expect >= 2, proving a FAMILY not one-off)")

# --- acceptance 2: special logic confined to profile -----------------------------------------
# the generic connector class body must contain ZERO province literals; all province specifics live
# in PROFILES (below the class) and in generic, province-agnostic named hooks (above the class).
src = (V01 / "tools" / "adapter_a1_province.py").read_text(encoding="utf-8")
m = re.search(r"class A1ProvinceConnector\b.*?(?=\n# ---|\nPROFILES =|\ndef build_family)", src, re.S)
class_body = m.group(0) if m else ""
PROVINCE_LITERALS = ["江苏", "山东", "北京", "jiangsu", "shandong", "beijing",
                     "苏政", "鲁科", "京科", "art-cms", "beijing-zhengce"]
leaked = [lit for lit in PROVINCE_LITERALS if lit in class_body]
print(f"connector class body province literals: {leaked or 'NONE'}")
if leaked:
    fails.append(f"connector class body leaks province-specific literals: {leaked}")
# and every profile references a NAMED hook that exists (hooks are the only special-logic locus)
for sid, p in A.PROFILES.items():
    if p.title_hook not in A.TITLE_HOOKS:
        fails.append(f"{sid}: title_hook '{p.title_hook}' not registered")

# --- write the contract report ----------------------------------------------------------------
report = {
    "task": "ADP-S4-P03-T049",
    "acceptance": ">=3 provincial site templates pass; special logic confined to profile",
    "profiles_total": len(results), "profiles_passed": len(passed),
    "template_families": sorted(families),
    "connector_class_province_literals": leaked,
    "results": results,
    "all_passed": not fails,
    "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0,
             "r2_bytes": 0, "r2_ops": 0, "model_calls": 0,
             "human_maintenance": "dev-env fixture capture + family/profile authoring"},
    "deployment": "NOT_DEPLOYED (adapter family + profiles; production worker/cron untouched)",
}
(FX.parent / "contract_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
