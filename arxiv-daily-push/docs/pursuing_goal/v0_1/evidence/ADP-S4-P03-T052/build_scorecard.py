#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T052 -- emit the A1 scorecard + promote/hold/disable decisions (deterministic)."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import a1_scorecard as SC

def main():
    sc = SC.build_scorecard()
    (HERE / "a1_scorecard.json").write_text(json.dumps(sc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"sources_scored={sc['sources_scored']} identity_rate={sc['official_identity_rate']} decisions={sc['decisions']}")

if __name__ == "__main__":
    main()
