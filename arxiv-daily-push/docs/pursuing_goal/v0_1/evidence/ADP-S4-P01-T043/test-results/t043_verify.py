#!/usr/bin/env python3
"""ADP-S4-P01-T043 acceptance: Source-Year-Month gap detector.

Acceptance (TASK_INDEX): 每个 enabled source/year/month 有 count 或解释；0 个静默未解释空洞。
Deterministic. Uses the real 500-item coverage (20 sources x 127 months). Also proves the detector
ALERTS on an unexplained hole (it does not trivially explain everything away).
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T043 = V01 / "evidence" / "ADP-S4-P01-T043"
sys.path.insert(0, str(V01 / "tools"))
import gap_detector as G  # noqa: E402

items = json.loads((T043 / "coverage_items.json").read_text(encoding="utf-8"))
months = G.month_range("2016-01", "2026-07")
sources = G.infer_source_windows(items)
fails = []

rep = G.detect(items, sources, months)
print(f"coverage grid: {rep['sources']} sources x {rep['months']} months = {rep['cells']} cells")
print("reason counts:", rep["reason_counts"])
print("unexplained:", rep["unexplained"], "| every_cell_has_count_or_reason:", rep["every_cell_has_count_or_reason"])

# --- 1) every enabled source/year/month has a count OR a reason; 0 unexplained --------------
if rep["unexplained"] != 0:
    fails.append(f"{rep['unexplained']} silently-unexplained holes (must be 0)")
if not rep["every_cell_has_count_or_reason"]:
    fails.append("some cell has neither a count nor a reason")
# every reason is a known category; counts sum to total cells
known = {"covered", "source_not_yet_active", "no_publications", "not_backfilled", "fetch_failed"}
if any(k not in known for k in rep["reason_counts"] if k != "UNEXPLAINED"):
    fails.append("an unknown gap reason appeared")
if sum(rep["reason_counts"].values()) != rep["cells"]:
    fails.append("reason counts do not sum to the number of cells")
# coverage (covered cells) matches the real items with a source window
covered = rep["reason_counts"].get("covered", 0)
if covered <= 0:
    fails.append("no covered cells (coverage table empty)")
print(f"coverage table: {covered} covered cells; deliverable = coverage table + gap reasons + alerts")

# --- 2) the detector ALERTS on an unexplained hole (does not silently explain everything) ----
# inject a source with NO activity window -> an empty cell it cannot explain -> UNEXPLAINED alert
bad_sources = dict(sources); bad_sources["ghost-source"] = {"active_from": None, "active_to": None}
bad = G.detect(items, bad_sources, months)
print(f"\ninjected ghost-source (no window): unexplained={bad['unexplained']} alert_count={bad['alert_count']}")
if bad["unexplained"] == 0 or bad["alert_count"] == 0:
    fails.append("detector did NOT alert on an unexplained hole (it trivially explains everything)")
if bad["every_cell_has_count_or_reason"]:
    fails.append("detector wrongly claims all-explained when an unexplained hole exists")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
