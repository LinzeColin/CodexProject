#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T055 acceptance: A2 production gate.

Acceptance (TASK_INDEX): 0 个仅因数量目标晋级；每个晋级 source 有实际 30 日健康证据。
Deterministic. Verifies that NO A2 zone is promoted for a count target (promotion requires health,
never value/coverage alone) and that EVERY promoted source carries >= 30-day health evidence. Since
no A2 zone has 30-day health yet, the honest outcome is 0 promotions -- but the gate is non-vacuous:
a control proves it WOULD promote a >=30-day-health source and would NOT promote a high-value source
that lacks it.
"""
import sys, json, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import a2_production_gate as G

led = json.loads((V01 / "evidence" / "ADP-S4-P04-T055" / "a2_promotion_ledger.json").read_text(encoding="utf-8"))
ledger = led["promotion_ledger"]
promoted = [r for r in ledger if r["decision"] == "promote"]
fails = []
print(f"scored={led['a2_zones_scored']} decisions={led['decisions']} "
      f"promoted_for_volume={led['promoted_for_volume']} required_days={led['health_days_required']}")

# --- 1) 0 promoted just for volume -----------------------------------------------------------
if led["promoted_for_volume"] != 0:
    fails.append(f"{led['promoted_for_volume']} sources promoted for a count target")

# --- 2) every PROMOTED source has >= 30-day health -------------------------------------------
for r in promoted:
    if r["health_days"] < led["health_days_required"]:
        fails.append(f"{r['source_id']}: promoted with only {r['health_days']}d health (< 30)")
if led["promoted_without_health"] != 0:
    fails.append(f"{led['promoted_without_health']} promoted without 30-day health")

# --- 3) NON-VACUITY control: the gate genuinely enforces the 30-day threshold -----------------
demo = {"source_id": "demo", "name": "demo", "tier": "x", "value": 4, "reach": "x"}
d_hi_health = G.decide(demo, health_days=35)          # >=30d health -> MUST promote
d_hi_value_low_health = G.decide(demo, health_days=5)  # high value, <30d health -> MUST NOT promote
print(f"control: health=35 -> {d_hi_health['decision']} | health=5 -> {d_hi_value_low_health['decision']}")
if d_hi_health["decision"] != "promote":
    fails.append("gate does NOT promote a >=30-day-health source -> the health gate is broken/vacuous")
if d_hi_value_low_health["decision"] == "promote":
    fails.append("gate promotes a high-value source WITHOUT 30-day health -> volume/value promotion leak")

# --- 4) deliverables: promotion ledger + cost/quality evidence + rollback --------------------
if not ledger:
    fails.append("empty promotion ledger")
if not led.get("cost_quality_evidence"):
    fails.append("missing cost/quality evidence")
if "revert" not in led.get("rollback", "").lower() and "flag" not in led.get("rollback", "").lower():
    fails.append("no rollback path stated")
if led["deployment"] != "NOT_DEPLOYED":
    fails.append("gate is not NOT_DEPLOYED (decisions must be reversible)")
if not all(r.get("reversible") for r in ledger):
    fails.append("a ledger decision is not reversible")
# every held zone has a concrete reason (days_to_promotion), not silently dropped
for r in ledger:
    if r["decision"] != "promote" and "days_to_promotion" not in r:
        fails.append(f"{r['source_id']}: held without a days_to_promotion reason")

# --- 5) re-derive from the tool (guard against a hand-edited ledger) --------------------------
# deep per-entry comparison (not just aggregate counts) so a fabricated promoted row cannot slip in
live = G.build_ledger()
if live["decisions"] != led["decisions"] or live["a2_zones_scored"] != led["a2_zones_scored"]:
    fails.append("ledger does not match tool re-derivation (aggregate)")
live_by_id = {r["source_id"]: (r["decision"], r["health_days"]) for r in live["promotion_ledger"]}
for r in ledger:
    got = (r["decision"], r["health_days"])
    exp = live_by_id.get(r["source_id"])
    if exp != got:
        fails.append(f"{r['source_id']}: committed decision/health {got} != tool {exp} (hand-edit?)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
