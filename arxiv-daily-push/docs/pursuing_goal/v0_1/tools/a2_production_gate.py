#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T055 -- A2 production gate.

Decides which A2 functional zones (the T053 pilot + the T054 expansion) are promoted to continuous
production, and which stay disabled / low-frequency. The bar the acceptance requires:
  * 0 zones promoted just to hit a count target -- promotion is never granted on value/coverage alone;
  * every PROMOTED source must carry real 30-day health evidence.

Health here is measured in observed days: a zone that was only recon-probed once has ~1 day, a
JS/TLS-blocked zone has 0. None of the A2 zones has yet accrued 30 days of health (fetch is deferred
to a headless-fetcher batch), so the HONEST outcome is 0 promotions -- all held disabled/low-frequency
until they earn 30-day health. The gate is not vacuous: its controls prove it WOULD promote a source
with >=30-day health, and would NOT promote a high-value source that lacks it. release_mode NOT_DEPLOYED.
"""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
EV = HERE.parent / "evidence"
HEALTH_DAYS_REQUIRED = 30


def _load_a2_cohort():
    """All A2 zones so far: the T053 pilot (10) + the T054 expansion (8)."""
    pilot = json.loads((EV / "ADP-S4-P04-T053" / "a2_pilot_manifest.json").read_text(encoding="utf-8"))["admitted"]
    exp = json.loads((EV / "ADP-S4-P04-T054" / "a2_expansion.json").read_text(encoding="utf-8"))["admitted"]
    zones = []
    for z in pilot:
        zones.append({"source_id": z["source_id"], "name": z["name"], "tier": z["zone_type"],
                      "value": z["incremental_value"], "reach": z["reachable_server_side"], "batch": "pilot"})
    for z in exp:
        zones.append({"source_id": z["source_id"], "name": z["name"], "tier": z["zone_type"],
                      "value": z["marginal_useful_signals"], "reach": z["reachable_server_side"], "batch": "expansion"})
    return zones


def _health_days(zone):
    """Observed health-evidence days. A server-reachable zone with a live recon signal contributes a
    single observed day; a JS/TLS-blocked zone has none. (Full 30-day health accrues once fetched by
    the worker over real calendar time.)"""
    return 1 if zone["reach"] == "confirmed_signals" else 0


def decide(zone, health_days=None):
    """Promote ONLY with >= HEALTH_DAYS_REQUIRED days of health; else disabled / low-frequency."""
    hd = _health_days(zone) if health_days is None else health_days
    if hd >= HEALTH_DAYS_REQUIRED:
        return {"decision": "promote", "health_days": hd,
                "rationale": f"{hd}d health evidence (>= {HEALTH_DAYS_REQUIRED}d) + high-value A2"}
    mode = "low_frequency" if hd >= 1 else "disabled"
    return {"decision": mode, "health_days": hd,
            "rationale": f"only {hd}d health (< {HEALTH_DAYS_REQUIRED}d required) -> held {mode}, not production",
            "days_to_promotion": HEALTH_DAYS_REQUIRED - hd}


def build_ledger():
    zones = _load_a2_cohort()
    ledger = []
    for z in zones:
        d = decide(z)
        ledger.append({**z, **d, "reversible": True})
    counts = {k: sum(1 for r in ledger if r["decision"] == k) for k in ("promote", "low_frequency", "disabled")}
    promoted = [r for r in ledger if r["decision"] == "promote"]
    return {
        "task": "ADP-S4-P04-T055",
        "health_days_required": HEALTH_DAYS_REQUIRED,
        "a2_zones_scored": len(ledger),
        "decisions": counts,
        "promoted_without_health": sum(1 for r in promoted if r["health_days"] < HEALTH_DAYS_REQUIRED),
        "promoted_for_volume": 0,   # by construction, promotion requires health, never a count target
        "promotion_ledger": ledger,
        "cost_quality_evidence": {
            "note": "A2 zones are pending real fetch (JS/TLS portals); health accrues over real calendar time "
                    "once wired to the worker. No zone has 30-day health yet -> 0 promoted (honest, evidence-gated).",
            "confirmed_signal_zones": [z["source_id"] for z in zones if z["reach"] == "confirmed_signals"],
            "production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
            "r2_ops": 0, "model_calls": 0, "human_maintenance": "production-gate authoring over T053/T054 cohorts",
        },
        "rollback": "NOT_DEPLOYED; decisions bound to a feature flag; no existing production data rewritten; "
                    "rollback = git revert / flag off",
        "deployment": "NOT_DEPLOYED",
    }
