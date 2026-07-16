#!/usr/bin/env python3
"""ADP-S4-P02-T045 acceptance: A0 backfill cohort selection by user value.

Acceptance (TASK_INDEX): 每个 source 有权威角色、历史起点、预期文档类型和停止规则。
Deterministic. Also checks: selection is by user value (not Registry order), a priority model +
cohort manifest + expected benefit exist, and a live-blocked source is deferred (not in Wave 1).
"""
import sys, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import cohort_selector as C  # noqa: E402

fails = []
cohort = C.select_cohort()
print("cohort:", cohort["cohort_id"], "| members:", [(m["source_id"], m["value_score"]) for m in cohort["members"]])
print("deferred:", [(d["source_id"], d.get("deferred_reason", "")[:30]) for d in cohort["deferred"]])

# --- 1) every source has authority role + history start + expected doc types + stop rule ----
for m in cohort["members"]:
    if not m.get("authority_role"):
        fails.append(f"{m['source_id']}: missing authority_role")
    if not m.get("history_start"):
        fails.append(f"{m['source_id']}: missing history_start")
    if not m.get("expected_doc_types"):
        fails.append(f"{m['source_id']}: missing expected_doc_types")
    sr = m.get("stop_rule") or {}
    if not (sr.get("until_month") and sr.get("stop_when")):
        fails.append(f"{m['source_id']}: missing/incomplete stop_rule")
    if "expected_benefit" not in m:
        fails.append(f"{m['source_id']}: missing expected_benefit")
print("every member has authority_role + history_start + expected_doc_types + stop_rule + expected_benefit:",
      all(m.get("authority_role") and m.get("history_start") and m.get("expected_doc_types")
          and (m.get("stop_rule") or {}).get("until_month") and "expected_benefit" in m for m in cohort["members"]))

# --- 2) selection is by user value (highest first), NOT registry order ----------------------
scores = [m["value_score"] for m in cohort["members"]]
if scores != sorted(scores, reverse=True):
    fails.append(f"members not ordered by descending value: {scores}")
# the top pick is the highest-value central source, not the first in the registry dict
if cohort["members"][0]["source_id"] != "gov-cn-policy":
    fails.append("top cohort member is not the highest-value central source")

# --- 3) priority model + cohort manifest + expected benefit present --------------------------
if not cohort.get("priority_weights") or "by user value" not in cohort["selection"]:
    fails.append("priority model / value-based selection missing")
if cohort["member_count"] != len(cohort["members"]):
    fails.append("cohort manifest member_count mismatch")

# --- 4) a live-blocked source is deferred (not blindly opened) -------------------------------
member_ids = {m["source_id"] for m in cohort["members"]}
if "nda-gov" in member_ids:
    fails.append("live-blocked nda-gov was put in Wave 1 (should be deferred)")
if not any(d["source_id"] == "nda-gov" for d in cohort["deferred"]):
    fails.append("nda-gov not recorded as deferred with a reason")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
