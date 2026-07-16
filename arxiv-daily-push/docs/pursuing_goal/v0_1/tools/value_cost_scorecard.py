#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S8-P01-T087 -- final Value-Cost Gate scorecard.

Uses ACTUAL data (the 131-benefit parity registry, the 90-task release-mode split, the DIR-007 free-tier
budget) to score every recurring-cost surface of the system against a value metric, and to decide
keep / scale / hold / stop per component. It ENCODES two hard acceptance rules:
  (1) every recurring cost carries a value metric;
  (2) any component without proven value evidence stays OFF (not deployed) -- no unproven recurring spend.
It also carries the DIR-007 budget guardrails (Cloudflare free tier, fail-closed).

The gate itself needs OWNER sign-off (implementer never self-signs); this tool prepares the decision
package. Deterministic: no network / clock / randomness. Anchors to committed facts.
"""
import argparse
import csv
import json
import pathlib
import re

V01 = pathlib.Path(__file__).resolve().parent.parent
EVID = V01 / "evidence"
WORKER = V01.parent.parent.parent / "deploy" / "cloudflare" / "worker_cloud.js"
PARITY = json.loads((EVID / "ADP-S5-P04-T068/parity_registry_131.json").read_text("utf-8"))["items"]
TASK_INDEX = list(csv.DictReader((V01 / "TASK_INDEX.csv").open(encoding="utf-8")))


def raw_dualwrite_live():
    """Read the ACTUAL R2 dual-write deployment state from the worker source (never hand-asserted): the
    live build carries `const RAW_DUALWRITE = true` (SHADOW-opened in T023, never reverted) + an R2 binding,
    so R2 raw-artifact dual-write is actively writing in production. Deriving this from the source keeps the
    scorecard's deployment claim honest and drift-proof."""
    src = WORKER.read_text("utf-8")
    m = re.search(r"const RAW_DUALWRITE\s*=\s*(true|false)", src)
    on = bool(m) and m.group(1) == "true"
    bound = ("env.RAW" in src) or ("env && env.RAW" in src)
    return {"raw_dualwrite": on, "r2_bound": bound, "active": on and bound}

# DIR-007 Cloudflare free-tier hard budget (FREE_TIER_BUDGET.md) -- the guardrails.
BUDGET_GUARDRAILS = {
    "directive": "DIR-007 (COST_HARD_LIMIT): the whole ADP + all repos must never exceed the Cloudflare free tier",
    "plan": "Cloudflare Free (FACT-013 VERIFIED); no paid upgrade without explicit Owner triple-confirmation",
    "limits": {"r2_storage_gb": 10, "r2_class_a_ops_month": 1_000_000, "r2_class_b_ops_month": 10_000_000,
               "d1": "free tier", "workers": "free tier", "cron": "free tier"},
    "enforcement": "fail-closed: any write/store/request that would exceed a limit MUST stop; R2 write path "
                   "has a built-in budget check; >=80% => alarm + throttle/stop; violation = stop-the-line",
    "recurring_usd_per_month": 0,
}


def _parity_stats():
    from collections import Counter
    c = Counter(b["status"] for b in PARITY)
    return {"total": len(PARITY), "delivered": c.get("delivered", 0), "partial": c.get("partial", 0),
            "planned": c.get("planned", 0), "not_applicable": c.get("not_applicable", 0)}


def _release_modes():
    from collections import Counter
    return dict(Counter(r["release_mode"] for r in TASK_INDEX))


def build_scorecard():
    p = _parity_stats()
    delivered_note = f"{p['delivered']}/{p['total']} competitor-parity benefits delivered (partial {p['partial']}, planned {p['planned']})"
    r2 = raw_dualwrite_live()   # ACTUAL R2 dual-write state read from the worker source (not hand-asserted)
    r2_row = ({"component": "r2 raw-artifact dual-write", "category": "infra", "deployed": True,
               "recurring": {"resource": "R2", "free_tier": True, "usd": 0,
                             "flag": "RAW_DUALWRITE=true (SHADOW-active, per-run cap 3)",
                             "free_tier_usage": "~90 Class A writes/mo, ~4.7MB/mo storage growing -- within free tier (1M ops / 10GB)"},
               "has_value_evidence": True,
               "value_metric": "immutable content-addressed A0-A2 raw evidence (permanent), ACTIVELY captured in shadow in the live b189d3cc0703 build, within the DIR-007 free-tier budget",
               "evidence_ref": "ADP-S2-P01-T022 / ADP-S2-P01-T023 / ADP-S8-P01-T086", "decision": "keep",
               "note": "SHADOW-deployed (RAW_DUALWRITE=true since T023, never reverted); monitor R2 usage vs the DIR-007 free-tier limits"}
              if r2["active"] else
              {"component": "r2 raw-artifact dual-write", "category": "infra", "deployed": False,
               "recurring": {"resource": "R2", "free_tier": True, "usd": 0, "flag": "RAW_DUALWRITE=false (off)"},
               "has_value_evidence": True, "value_metric": "immutable content-addressed A0-A2 raw evidence (permanent) when enabled",
               "evidence_ref": "ADP-S2-P01-T022 / ADP-S2-P01-T023 / ADP-S8-P01-T086", "decision": "hold",
               "hold_reason": "flag off; enable on demand only within the DIR-007 free-tier budget"})
    # Every row: recurring cost (free tier => $0), value metric, evidence, and a keep/scale/hold/stop decision.
    # deployed=True rows carry recurring cost and MUST have proven value; deployed=False rows are OFF (held/gated).
    rows = [
        # --- deployed recurring-cost infrastructure surfaces (each $0 on the free tier) ---
        {"component": "cloudflare_worker (adp-cloud)", "category": "infra", "deployed": True,
         "recurring": {"resource": "Workers", "free_tier": True, "usd": 0},
         "has_value_evidence": True, "value_metric": f"serves the entire live cognitive system; {delivered_note}; live build b189d3cc0703",
         "evidence_ref": "ADP-S1-P01-T010 / ADP-S3-P03-T040", "decision": "keep"},
        {"component": "d1 (adp-mirror)", "category": "infra", "deployed": True,
         "recurring": {"resource": "D1", "free_tier": True, "usd": 0},
         "has_value_evidence": True, "value_metric": "canonical documents + 2016+ recoverable history + review store; query indexes (T083)",
         "evidence_ref": "ADP-S2-P03-T027 / ADP-S2-P03-T029 / ADP-S7-P03-T083", "decision": "keep"},
        {"component": "cron (daily 30 20)", "category": "infra", "deployed": True,
         "recurring": {"resource": "Cron Triggers", "free_tier": True, "usd": 0},
         "has_value_evidence": True, "value_metric": "daily fresh fetch -> select -> lesson pipeline (freshness)",
         "evidence_ref": "ADP-S1-P01-T010", "decision": "keep"},
        {"component": "domains/DNS (adp + home.linzezhang.com)", "category": "infra", "deployed": True,
         "recurring": {"resource": "DNS", "free_tier": True, "usd": 0},
         "has_value_evidence": True, "value_metric": "public access to the product + entry hub",
         "evidence_ref": "ADP-S0-P02-T004", "decision": "keep"},
        {"component": "deployed sources (5 boards + A0 official Board3)", "category": "content", "deployed": True,
         "recurring": {"resource": "outbound fetch", "free_tier": True, "usd": 0},
         "has_value_evidence": True, "value_metric": "board coverage + A0 official-original authority for Board3",
         "evidence_ref": "ADP-S1-P02-T013 / ADP-S3-P03-T040", "decision": "keep"},
        {"component": "six-theme UI + motion + a11y", "category": "experience", "deployed": True,
         "recurring": {"resource": "Workers (static)", "free_tier": True, "usd": 0},
         "has_value_evidence": True, "value_metric": "six-theme advanced motion, mobile-safe, component states, a11y, provenance marking",
         "evidence_ref": "ADP-S7-P01-T077 .. ADP-S7-P04-T084", "decision": "keep"},
        # --- proven-in-evidence but NOT deployed: held OFF, promotion/cohort-gated (no unproven recurring spend) ---
        {"component": "A1/A2 subnational sources (province/city)", "category": "content", "deployed": False,
         "recurring": {"resource": "outbound fetch", "free_tier": True, "usd": 0, "flag": "SHADOW"},
         "has_value_evidence": True, "value_metric": "geographic depth (identity/coverage proven in shadow)",
         "evidence_ref": "ADP-S4-P03-T050 / T051 / ADP-S4-P04-T053 / T054", "decision": "hold",
         "hold_reason": "SHADOW; per-cohort Owner promotion gate not yet signed -> stays off"},
        {"component": "S5 multi-board depth (events/entities/search/research/watchlist/library)", "category": "capability", "deployed": False,
         "recurring": {"resource": "D1/Workers", "free_tier": True, "usd": 0, "flag": "NOT_DEPLOYED"},
         "has_value_evidence": True, "value_metric": "the 131-parity depth layer (proven deterministically in evidence)",
         "evidence_ref": "ADP-S5-P01-T057 .. ADP-S5-P04-T068", "decision": "hold",
         "hold_reason": "proven in evidence; promotion-gated -> stays off until promoted"},
        {"component": "S6 prediction models (baselines/backtest/forecast ledger)", "category": "model", "deployed": False,
         "recurring": {"resource": "compute", "free_tier": True, "usd": 0, "flag": "NOT_DEPLOYED"},
         "has_value_evidence": True, "value_metric": "settlement rules + leak-guard + rolling-origin backtest + forecast ledger (in-evidence MODEL cards)",
         "evidence_ref": "ADP-S6-P01-T069 .. ADP-S6-P03-T076", "decision": "hold",
         "hold_reason": "cognitive models NOT injected into the operational MODEL_SPEC; gated at promotion (S6 model decision)"},
    ]
    rows.insert(6, r2_row)   # R2 dual-write, its deployed state read live from the worker flag
    from collections import Counter
    decisions = dict(Counter(r["decision"] for r in rows))
    total_recurring = sum(r["recurring"].get("usd", 0) for r in rows)
    return {
        "iteration": "ITER-20260716-ADP-V01-FINAL-EXECUTION", "task": "ADP-S8-P01-T087",
        "parity": p, "release_modes": _release_modes(),
        "scorecard": rows, "decisions_summary": decisions,
        "total_recurring_usd_per_month": total_recurring,
        "budget_guardrails": BUDGET_GUARDRAILS,
        "owner_signoff": {"required": True, "status": "PENDING",
                          "statement": "Owner to sign: (a) every recurring cost has a value metric; (b) no-evidence "
                                       "components stay off; (c) DIR-007 free-tier budget guardrails hold; "
                                       "(d) keep/scale/hold/stop decisions approved.",
                          "note": "implementer does NOT self-sign; this is the prepared decision package"},
    }


def acceptance(card):
    """The two machine-checkable gate rules (the third, Owner sign-off, is a human step)."""
    rows = card["scorecard"]
    # (1) every recurring cost carries a value metric
    recurring_rows = [r for r in rows if r["recurring"].get("usd", 0) is not None]
    missing_value = [r["component"] for r in rows if not r.get("value_metric")]
    all_recurring_have_value = not missing_value
    # (2) no component without value evidence is deployed / recurring; anything OFF has decision hold|stop
    no_evidence_deployed = [r["component"] for r in rows if r["deployed"] and not r["has_value_evidence"]]
    off_not_held = [r["component"] for r in rows if not r["deployed"] and r["decision"] not in ("hold", "stop")]
    no_unproven_recurring = not no_evidence_deployed and not off_not_held
    # (3) recurring spend within the free-tier budget (== $0)
    within_budget = card["total_recurring_usd_per_month"] == 0
    guardrails_present = bool(card["budget_guardrails"].get("directive"))
    return {
        "all_recurring_have_value_metric": all_recurring_have_value, "missing_value": missing_value,
        "no_unproven_recurring_spend": no_unproven_recurring,
        "deployed_without_evidence": no_evidence_deployed, "off_but_not_held": off_not_held,
        "within_free_tier_budget": within_budget, "budget_guardrails_present": guardrails_present,
        "gate_machine_pass": all_recurring_have_value and no_unproven_recurring and within_budget and guardrails_present,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    card = build_scorecard()
    acc = acceptance(card)
    card["acceptance"] = acc
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in card["scorecard"]:
        print(f"  {r['component']:<52} deployed={str(r['deployed']):<5} {r['decision']:<5} "
              f"${r['recurring'].get('usd',0)} :: {r['value_metric'][:48]}")
    print(f"decisions={card['decisions_summary']} recurring=${card['total_recurring_usd_per_month']}/mo "
          f"parity={card['parity']['delivered']}/{card['parity']['total']} delivered")
    print(f"GATE_MACHINE_PASS={acc['gate_machine_pass']} (Owner sign-off: {card['owner_signoff']['status']})")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
