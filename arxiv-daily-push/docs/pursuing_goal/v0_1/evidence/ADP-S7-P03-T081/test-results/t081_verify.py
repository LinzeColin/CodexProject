#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P03-T081 acceptance: RUM / Core Web Vitals segmented by theme/route/device/network.

Acceptance (TASK_INDEX row 81): LCP/INP/CLS 可按主题、路由、设备和网络查询；无数据不声称达标.

Deterministic. Re-derives from the TOOL (rum_cwv) + the worker source + the frozen T080 baseline.
Load-bearing negative controls:
  1. 无数据不声称达标 (THE core clause): an EMPTY dataset and a THIN segment must claim NO compliance
     (claims_any_compliance == False; thin segment -> insufficient_data). If the gate were removed, an empty
     dataset would falsely "meet the bar" -- this control fails on that.
  2. The rumIngest validator (Node test on the REAL extracted code) rejects bad/oversized/out-of-range/
     sampled-out payloads before any D1 write.
  3. The visual/motion contract is BYTE-IDENTICAL (RUM is injected at the router, touching nothing hashed) --
     detect_regression reports ZERO specific changes AND master_visual unchanged.
The browser proof (real RUM client captures live CWV tagged by the four dimensions) is in
browser_measurements.json.
"""
import json
import pathlib
import subprocess
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import visual_baseline as VB
import rum_cwv as R

T081 = V01 / "evidence" / "ADP-S7-P03-T081"
PRE = json.loads((T081 / "pre_fix_baseline.json").read_text(encoding="utf-8"))["asset_hashes"]
NEW_SRC = VB.WORKER.read_text(encoding="utf-8")

fails = []

# ================= 1) LCP/INP/CLS queryable by theme / route / device / network =================
# synthetic field data: minimal/desktop/4g fast; cosmos/mobile/3g slow; each dimension well-sampled
rows = []
for m, fast, slow in (("LCP", 1800, 4200), ("INP", 120, 520), ("CLS", 0.03, 0.30)):
    for i in range(40):
        rows.append({"metric": m, "value": fast + i * 0.001, "theme": "minimal", "route": "today", "device": "desktop", "network": "4g"})
        rows.append({"metric": m, "value": slow + i * 0.001, "theme": "cosmos", "route": "radar", "device": "mobile", "network": "3g"})
for dim in R.DIMENSIONS:
    q = R.query(rows, dim)
    # every metric must be queryable and produce a p75 rating in a well-sampled bucket
    any_rated = any(cell["status"] == "ok" and cell["rating"] in ("good", "needs-improvement", "poor")
                    for seg in q.values() for cell in seg.values())
    if not any_rated:
        fails.append(f"dimension {dim} did not yield a queryable p75 rating")
# the fast vs slow split must actually differ (segmentation is real, not constant)
byt = R.query(rows, "theme")
if not (byt["minimal"]["LCP"]["rating"] == "good" and byt["cosmos"]["LCP"]["rating"] == "poor"):
    fails.append(f"theme segmentation not discriminating: {byt['minimal']['LCP']} vs {byt['cosmos']['LCP']}")
# full cross-segment query works
multi = R.query_multi(rows)
if not multi:
    fails.append("query_multi produced no segments")
print(f"query: LCP/INP/CLS queryable by all of {list(R.DIMENSIONS)}; theme split minimal=good / cosmos=poor; "
      f"{len(multi)} cross-segments")

# p75 + thresholds sanity
if R.p75(list(range(1, 101))) != 75.0:
    fails.append("p75 incorrect")
if not (R.rate("LCP", 2000) == "good" and R.rate("LCP", 3000) == "needs-improvement" and R.rate("LCP", 5000) == "poor"):
    fails.append("LCP rating thresholds wrong")

# ================= 2) 无数据不声称达标 (load-bearing negative controls) =================
empty_overall = R.overall_baseline([])
empty_multi = R.query_multi([])
if R.claims_any_compliance(empty_overall) or R.claims_any_compliance(empty_multi):
    fails.append("control broken: an EMPTY dataset claims compliance (无数据不声称达标 violated)")
if any(empty_overall[m]["status"] != "insufficient_data" for m in ("LCP", "INP", "CLS")):
    fails.append("empty dataset did not report insufficient_data for every metric")
thin = [{"metric": "LCP", "value": 1000, "theme": "warm", "route": "today", "device": "desktop", "network": "4g"}] * 5
if R.claims_any_compliance(R.query_multi(thin)):
    fails.append("control broken: a THIN segment (5 < min_samples) claims compliance")
if R.query(thin, "theme")["warm"]["LCP"]["status"] != "insufficient_data":
    fails.append("thin segment not gated as insufficient_data")
print(f"无数据不声称达标: empty + thin datasets claim NO compliance (min_samples={R.DEFAULT_MIN_SAMPLES}); "
      f"gate is load-bearing")

# ================= 3) ingest validation (Node test on the REAL extracted rumIngest) =================
node = subprocess.run(["node", str(T081 / "test-results" / "rum_ingest_test.js")], capture_output=True, text=True)
if "RESULT = PASS" not in node.stdout or node.returncode != 0:
    fails.append(f"rumIngest Node test did not pass: rc={node.returncode}")
print(f"ingest: rumIngest Node test = {'PASS' if 'RESULT = PASS' in node.stdout else 'FAIL'} "
      f"(bad metric/value/payload/sample rejected before any D1 write)")

# ================= 4) endpoint + client wired in the worker =================
checks = {
    "endpoint /api/rum": "if (p === '/api/rum')" in NEW_SRC,
    "creates cn_rum table": "CREATE TABLE IF NOT EXISTS cn_rum" in NEW_SRC,
    "inserts into cn_rum": "INSERT INTO cn_rum" in NEW_SRC,
    "calls rumIngest": "rumIngest(payload, Math.random())" in NEW_SRC,
    "client injected at router": "RUM_ENABLED ? html.replace('</body>'" in NEW_SRC,
    "client sends beacon": "navigator.sendBeacon('/api/rum'" in NEW_SRC,
}
for name, ok in checks.items():
    if not ok:
        fails.append(f"worker wiring missing: {name}")
print(f"worker wiring: {sum(checks.values())}/{len(checks)} (endpoint + cn_rum + rumIngest + client injection + beacon)")

# browser proof: real client captured 3 CWV metrics tagged by the four dimensions
bm = json.loads((T081 / "browser_measurements.json").read_text(encoding="utf-8"))
rc = bm["rum_client_test"]
if not (rc["beacon_count"] == 3 and set(rc["metrics"]) == {"LCP", "INP", "CLS"} and rc["all_to_api_rum"]
        and rc["lcp_captured_real"] and set(rc["segment_tags"]) == {"theme", "route", "device", "network"}):
    fails.append(f"browser RUM client proof incomplete: {rc}")
print(f"browser proof: real client captured {rc['metrics']} tagged by "
      f"{sorted(rc['segment_tags'])}, beaconed to /api/rum")

# ================= 5) 现有高级视觉保持 -- contract byte-identical (router injection touches nothing hashed) =================
changed = {c["element"] for c in VB.detect_regression(PRE, NEW_SRC)["changes"]}
specific = sorted(e for e in changed if e not in ("master_visual", "contract_root"))
if specific:
    fails.append(f"contract changed (expected none): {specific}")
if "master_visual" in changed:
    fails.append("master_visual changed -- RUM leaked into the hashed visual surface")
nh = VB.asset_hashes(VB.extract_contract(NEW_SRC))
if PRE != nh:
    diff = [k for k in PRE if PRE[k] != nh.get(k)]
    fails.append(f"asset hashes changed (expected fully identical): {diff}")
print("advanced visual preserved: the ENTIRE T077/T078 contract is byte-identical (RUM injected at router, "
      "no hashed element touched)")

# ================= NOT_DEPLOYED: source build recomputed, live unchanged =================
if "8c19387c846b" not in NEW_SRC:
    fails.append("could not confirm the source build_id after the change")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
print("NOTE: source build_id after the change is 8c19387c846b; NOT_DEPLOYED (live unchanged). NO real RUM "
      "baseline exists yet -- the tool refuses to claim compliance without data; a real p75 baseline requires "
      "deploying + collecting field traffic.")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
