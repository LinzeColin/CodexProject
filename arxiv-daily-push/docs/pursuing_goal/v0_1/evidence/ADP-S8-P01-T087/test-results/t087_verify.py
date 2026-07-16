#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S8-P01-T087 acceptance: final Value-Cost Gate.

Acceptance (TASK_INDEX row 87): 所有 recurring cost 有价值指标；没有证据的组件保持关闭；Owner 签署.

Deterministic (no network/clock/randomness). Re-derives the scorecard from committed facts (the 131
parity registry, the 90-task release-mode split, DIR-007) and checks the two MACHINE rules; the third
(Owner sign-off) is a human step and is asserted to be PENDING (implementer never self-signs).

Load-bearing negative controls:
  1. every recurring cost must carry a value metric -- adding a recurring row with an empty value_metric
     must flip all_recurring_have_value_metric False.
  2. no component without value evidence may be deployed -- adding a deployed row with
     has_value_evidence=False must flip no_unproven_recurring_spend False; likewise an OFF row whose
     decision is not hold/stop must flip it.
"""
import copy
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import value_cost_scorecard as SC

fails = []
card = SC.build_scorecard()
acc = SC.acceptance(card)

# ---- machine gate rules ----
if not acc["gate_machine_pass"]:
    fails.append(f"gate machine rules did not pass: {acc}")
if not acc["all_recurring_have_value_metric"]:
    fails.append(f"a recurring cost has no value metric: {acc['missing_value']}")
if not acc["no_unproven_recurring_spend"]:
    fails.append(f"an unproven component is deployed / an off component is not held: {acc['deployed_without_evidence']} / {acc['off_but_not_held']}")
if not (acc["within_free_tier_budget"] and card["total_recurring_usd_per_month"] == 0):
    fails.append("recurring spend is not within the free-tier budget ($0)")
if not acc["budget_guardrails_present"]:
    fails.append("DIR-007 budget guardrails missing")
# every deployed row has value evidence; every off row is held/stopped
for r in card["scorecard"]:
    if r["deployed"] and not r["has_value_evidence"]:
        fails.append(f"deployed component without value evidence: {r['component']}")
    if not r["deployed"] and r["decision"] not in ("hold", "stop"):
        fails.append(f"off component not held/stopped: {r['component']} -> {r['decision']}")
# HONESTY: the R2 dual-write deployment claim must match the ACTUAL worker flag, not a hand-assertion
# (a 4-lens/skeptic review caught the row falsely claiming R2 "off" while RAW_DUALWRITE=true is live).
live_r2 = SC.raw_dualwrite_live()
r2row = next(r for r in card["scorecard"] if r["component"].startswith("r2 raw-artifact"))
if r2row["deployed"] != live_r2["active"]:
    fails.append(f"scorecard misrepresents R2 deployment: row deployed={r2row['deployed']} but the worker's "
                 f"actual RAW_DUALWRITE active={live_r2['active']}")
if live_r2["active"] and (not r2row["deployed"] or "SHADOW-active" not in r2row["recurring"].get("flag", "")):
    fails.append("R2 is SHADOW-active in the live worker but the scorecard does not honestly present it as deployed/active")
# data anchors: parity + release-mode split are from committed facts
if card["parity"]["total"] != 131 or card["parity"]["delivered"] != 92:
    fails.append(f"parity anchor drifted: {card['parity']}")
if sum(card["release_modes"].values()) != 90:
    fails.append(f"release-mode split does not cover 90 tasks: {card['release_modes']}")
# Owner sign-off is a human step -- must be PENDING, never self-signed
if card["owner_signoff"]["status"] != "PENDING":
    fails.append(f"Owner sign-off must be PENDING (never self-signed): {card['owner_signoff']['status']}")
# determinism
if SC.acceptance(SC.build_scorecard()) != acc:
    fails.append("scorecard is non-deterministic")
print(f"scorecard: {card['decisions_summary']} decisions, ${card['total_recurring_usd_per_month']}/mo recurring "
      f"(free tier), {card['parity']['delivered']}/{card['parity']['total']} parity delivered; every recurring "
      f"cost has a value metric; every off component held/gated; DIR-007 guardrails present; Owner sign-off PENDING")

# ---- NC1: a recurring cost with no value metric must fail rule (1) ----
c1 = copy.deepcopy(card)
c1["scorecard"].append({"component": "phantom_paid_feature", "category": "x", "deployed": True,
                        "recurring": {"resource": "x", "free_tier": True, "usd": 0},
                        "has_value_evidence": True, "value_metric": "", "decision": "keep"})
if SC.acceptance(c1)["all_recurring_have_value_metric"]:
    fails.append("control broken: a recurring row with no value metric still passed rule (1) -- vacuous")

# ---- NC2a: a deployed component without value evidence must fail rule (2) ----
c2 = copy.deepcopy(card)
c2["scorecard"].append({"component": "phantom_unproven_deployed", "category": "x", "deployed": True,
                        "recurring": {"resource": "x", "free_tier": True, "usd": 0},
                        "has_value_evidence": False, "value_metric": "claims value but no evidence", "decision": "keep"})
if SC.acceptance(c2)["no_unproven_recurring_spend"]:
    fails.append("control broken: an unproven deployed component still passed rule (2) -- vacuous")
# ---- NC2b: an OFF component whose decision is not hold/stop must fail rule (2) ----
c3 = copy.deepcopy(card)
c3["scorecard"].append({"component": "phantom_off_but_kept", "category": "x", "deployed": False,
                        "recurring": {"resource": "x", "free_tier": True, "usd": 0},
                        "has_value_evidence": True, "value_metric": "v", "decision": "keep"})
if SC.acceptance(c3)["no_unproven_recurring_spend"]:
    fails.append("control broken: an OFF component marked keep (not held) still passed rule (2) -- vacuous")
print("NC1 (recurring w/o value metric) -> rule(1) fails; NC2a (deployed w/o evidence) & NC2b (off but kept) "
      "-> rule(2) fails: all controls load-bearing")

print("\nACCEPTANCE = " + ("PASS (machine rules)" if not fails else "FAIL") +
      "  |  OWNER SIGN-OFF: PENDING (required to close the gate)")
print("NOTE: the two machine-checkable gate rules hold (every recurring cost has a value metric; no unproven "
      "recurring spend -- all off components held/gated); DIR-007 free-tier guardrails present; recurring $0/mo. "
      "The gate CLOSES only on Owner sign-off (owner_signoff.status PENDING). NOT_DEPLOYED (live b189d3cc0703).")
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
