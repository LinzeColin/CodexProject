#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T053 -- emit the A2 first-batch pilot manifest (deterministic)."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import a2_pilot as A2

def main():
    r = A2.select_pilot()
    manifest = {
        "task": "ADP-S4-P04-T053",
        "cohort_id": "A2-PILOT-BATCH-1",
        "selection_principle": "admit only zones with incremental local-action value beyond the A0/A1 baseline AND a verified official identity; no-incremental or non-official zones are not promoted",
        "baseline_signals_A0_A1": r["baseline_signals"],
        "local_signal_taxonomy": A2.LOCAL_SIGNAL_TYPES,
        "candidates": r["candidates"], "admitted_count": len(r["admitted"]), "rejected_count": len(r["rejected"]),
        "admitted": r["admitted"], "rejected": r["rejected"],
        "note_reachability": ("Zone portals are largely JS/TLS-hardened server-side; onboarding/fetch is a later "
                              "batch. Three zones (Xiongan, SIP, Hengqin) are server-reachable NOW with confirmed "
                              "live local-action signal terms (recon: 9/17/6 signal terms)."),
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
                 "r2_ops": 0, "model_calls": 0, "human_maintenance": "incremental-value model + curated zones + recon"},
        "deployment": "SHADOW (A2 pilot profiles + 2016 cursors + local action signals; production untouched)",
    }
    (HERE / "a2_pilot_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"admitted={len(r['admitted'])} rejected={len(r['rejected'])} confirmed_signal_zones="
          f"{sum(1 for a in r['admitted'] if a['reachable_server_side']=='confirmed_signals')}")

if __name__ == "__main__":
    main()
