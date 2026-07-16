#!/usr/bin/env python3
"""ADP-S4-P01-T044 acceptance: Source-Year unit-cost + maintenance dashboard.

Acceptance (TASK_INDEX): 未知成本不得用 0；可计算每千 artifact 和每个 accepted material event 成本。
Deterministic. Real 500-item throughput; costs measured for a couple source-years, UNKNOWN for the rest.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T044 = V01 / "evidence" / "ADP-S4-P01-T044"
sys.path.insert(0, str(V01 / "tools"))
import cost_dashboard as C  # noqa: E402

items = json.loads((T044 / "cost_items.json").read_text(encoding="utf-8"))
measured = {
    ("arxiv-all", 2025): {"fetch_subrequests": 120, "storage_bytes": 450000, "model_calls": 0, "failures": 1, "manual_interventions": 0},
    ("nejm", 2026): {"fetch_subrequests": 30, "storage_bytes": 90000, "model_calls": 0, "failures": 0, "manual_interventions": 0},
}
fails = []
d = C.dashboard(items, measured)
print(f"source-years {d['source_years']} | computable {d['computable_rows']} | unknown-cost {d['rows_with_unknown_cost']} | unknown cells {d['unknown_cost_cells']} | zero cells {d['zero_cost_cells']}")

# --- 1) UNKNOWN cost is NEVER shown as 0 ----------------------------------------------------
for r in d["rows"]:
    for f in C.COST_FIELDS + C.OPS_FIELDS:
        if r[f] == 0 and (r["source_id"], r["year"]) not in measured:
            fails.append(f"{r['source_id']}|{r['year']} field {f} is 0 but was not measured (must be UNKNOWN)")
if not d["no_unknown_cost_shown_as_zero"]:
    fails.append("dashboard claims an unknown cost was shown as 0")
# a measured genuine 0 (model_calls=0) is allowed and is NOT UNKNOWN
arxiv = next(r for r in d["rows"] if r["source_id"] == "arxiv-all" and r["year"] == 2025)
if arxiv["model_calls"] != 0:
    fails.append("a measured genuine 0 (model_calls) was not preserved as 0")
# an unmeasured source-year has UNKNOWN costs (not 0)
unk = next(r for r in d["rows"] if not r["cost_computable"])
if not all(unk[f] == C.UNKNOWN for f in C.COST_FIELDS):
    fails.append("an unmeasured source-year does not have UNKNOWN costs")
if unk["cost_per_1000_artifacts"]["fetch_subrequests"] != C.UNKNOWN:
    fails.append("derived unit cost from an UNKNOWN input is not UNKNOWN")
print(f"unknown row {unk['source_id']}|{unk['year']}: costs {[unk[f] for f in C.COST_FIELDS]} -> per-1000 fetch {unk['cost_per_1000_artifacts']['fetch_subrequests']} (UNKNOWN, not 0)")

# --- 2) computable: cost per 1000 artifacts + per accepted event for measured rows ----------
for key in measured:
    r = next(x for x in d["rows"] if (x["source_id"], x["year"]) == key)
    p1000 = r["cost_per_1000_artifacts"]; pacc = r["cost_per_accepted_event"]
    print(f"computable {key[0]}|{key[1]}: artifacts={r['artifacts']} accepted={r['accepted_events']} "
          f"per1000(fetch={p1000['fetch_subrequests']},storage={p1000['storage_bytes']}) "
          f"per_accepted(fetch={pacc['fetch_subrequests']})")
    if not isinstance(p1000["fetch_subrequests"], (int, float)):
        fails.append(f"{key}: cost per 1000 artifacts not computable")
    if r["accepted_events"] > 0 and not isinstance(pacc["fetch_subrequests"], (int, float)):
        fails.append(f"{key}: cost per accepted event not computable")
    # verify the number: 120 subrequests / 22 artifacts * 1000
    if key == ("arxiv-all", 2025):
        exp = round(120 / r["artifacts"] * 1000, 4)
        if p1000["fetch_subrequests"] != exp:
            fails.append(f"cost per 1000 artifacts wrong: {p1000['fetch_subrequests']} != {exp}")

# throughput + failure/manual metrics present
if "artifacts" not in d["rows"][0] or "failures" not in d["rows"][0] or "manual_interventions" not in d["rows"][0]:
    fails.append("throughput / failure / manual-intervention metrics missing")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
