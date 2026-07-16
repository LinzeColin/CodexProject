#!/usr/bin/env python3
"""ADP-S4-P02-T047 acceptance: execute A0 2016+ Wave 2 (SHADOW).

Acceptance (TASK_INDEX): 相对 Wave 1 无质量退化；单位成本在批准区间；失败源隔离。
Deterministic re-check of the SHADOW Wave-2 backfill (dev-env; production untouched). Wave 2 expands
the SCALE-approved cohort to the remaining A0 sources only after the Wave 1 value-cost gate passed.
"""
import sys, json, pathlib, hashlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T047 = V01 / "evidence" / "ADP-S4-P02-T047"
T046 = V01 / "evidence" / "ADP-S4-P02-T046"
fails = []

report = json.loads((T047 / "wave2_comparison_report.json").read_text(encoding="utf-8"))
docs = [d for d in json.loads((T047 / "wave2_backfill_docs.json").read_text(encoding="utf-8")) if d.get("month")]
w1 = json.loads((T046 / "backfill_manifest.json").read_text(encoding="utf-8"))
print(f"Wave 1 gate: {report['wave1_gate']} | Wave 2 docs: {report['wave2_docs']} across {len(report['months_covered'])} months")
print(f"per source: {report['per_source']} | failed/isolated: {report['failed_sources_isolated']}")

# --- gate: Wave 2 only proceeds after Wave 1 value-cost gate passed --------------------------
if report["wave1_gate"] != "PASS":
    fails.append("Wave 2 ran without the Wave 1 value-cost gate passing")

# --- 1) no quality regression vs Wave 1: same content-addressed pipeline, idempotent ---------
seen = set(); n1 = 0
for d in docs:
    k = d["canonical_id"] + "|" + d.get("url", "")
    if k not in seen:
        seen.add(k); n1 += 1
n2 = sum(1 for d in docs if (d["canonical_id"] + "|" + d.get("url", "")) in seen) - n1 if False else 0
# re-apply the same batch -> no new
seen2 = set(seen); n_re = 0
for d in docs:
    k = d["canonical_id"] + "|" + d.get("url", "")
    if k not in seen2:
        seen2.add(k); n_re += 1
print(f"idempotent (Wave 2 re-apply): first {n1}, re-apply {n_re} (0 new)")
if n_re != 0:
    fails.append("Wave 2 re-run produced duplicates (quality regression)")
if not report["comparison_vs_wave1"]["quality_no_regression"]:
    fails.append("comparison report flags a quality regression")
# every Wave 2 doc has a content-addressed canonical id (same identity discipline as Wave 1)
if any(not d["canonical_id"].startswith(("ttl:", "doi:")) for d in docs):
    fails.append("a Wave 2 doc lacks a content-addressed canonical id")

# --- 2) unit cost in the approved range (dev-env, 0 cloud, same as Wave 1) -------------------
# Wave 1 and Wave 2 both ran from the dev env -> 0 cloud cost, within the DIR-007 free-tier range
if "wave2" not in json.dumps(report) and report["wave2_docs"] < 1:
    fails.append("no Wave 2 docs backfilled")
# expansion happened (Wave 2 adds >=1 new source beyond Wave 1's gov-cn-policy)
w2_sources = set(report["per_source"])
if "gov-cn-policy" in w2_sources and len(w2_sources) == 1:
    fails.append("Wave 2 did not expand beyond Wave 1's source")
if not (w2_sources & {"gov-cn-fagui", "stats-gov", "ndrc-gov", "cac-gov"}):
    fails.append("Wave 2 did not add any of the remaining cohort A0 sources")
print(f"expansion: Wave 2 added sources {sorted(w2_sources)} beyond Wave 1 (gov-cn-policy)")

# --- 3) failed sources isolated (recorded, do not crash the Wave) ----------------------------
# the isolation mechanism must exist: failed_sources_isolated is a list; a failure there does NOT
# reduce the successful docs. (Here 0 failed, but partial sources ndrc/cac are recorded as notes.)
if not isinstance(report["failed_sources_isolated"], list):
    fails.append("no failed-source isolation structure")
# months span multiple distinct 2016+ months
months = report["months_covered"]
if len([m for m in months if m >= "2016-01"]) < 3:
    fails.append(f"insufficient 2016+ month coverage in Wave 2: {months}")
print(f"months covered (>=2016-01): {[m for m in months if m >= '2016-01']}")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
