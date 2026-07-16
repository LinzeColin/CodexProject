#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P04-T055 -- emit the A2 production-gate promotion ledger (deterministic)."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import a2_production_gate as G

def main():
    l = G.build_ledger()
    (HERE / "a2_promotion_ledger.json").write_text(json.dumps(l, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"scored={l['a2_zones_scored']} decisions={l['decisions']} "
          f"promoted_for_volume={l['promoted_for_volume']} promoted_without_health={l['promoted_without_health']}")

if __name__ == "__main__":
    main()
