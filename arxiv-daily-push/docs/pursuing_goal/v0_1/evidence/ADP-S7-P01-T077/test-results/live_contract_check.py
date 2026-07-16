#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P01-T077 -- verify the LIVE production site serves the full six-theme visual/motion contract.

This is the Owner-facing "the baseline reflects production" evidence in place of pixel screenshots (which
are flaky and would bloat the governance repo as binaries): it curls the live today page and confirms the
served bytes contain every theme's colour tokens, every ambience (fx) layer, the reduced-motion rule, the
theme->nav/fx/hero mappings, and the hero video assets. NOT_DEPLOYED: read-only GET, no production change.
"""
import re
import subprocess
import sys

URL = "https://adp.linzezhang.com/"
html = subprocess.run(["curl", "-s", "--max-time", "25", URL], capture_output=True, text=True).stdout
checks = {}
for t in ("warm", "minimal", "fresh", "techno", "cosmos", "forest"):
    checks[f"theme-token[{t}]"] = bool(re.search(r'\[data-theme="' + t + r'"\]\{[^}]*--bg:', html))
checks["fx-cosmos layer"] = "fx fx-cosmos" in html
checks["fx-minimal layer"] = "fx fx-minimal" in html
checks["fx-techno layer"] = "fx fx-techno" in html
checks["forest-slopes layer"] = "forest-slopes" in html
checks["reduced-motion rule"] = "prefers-reduced-motion" in html
checks["THEME_NAV mapping"] = bool(re.search(r'"warm":"sidebar"', html))
checks["THEME_FX mapping"] = bool(re.search(r'"cosmos":"cosmos"', html))
checks["THEME_HERO mapping"] = bool(re.search(r'"techno":"video"', html))
# The hero video PATHS also appear in the always-inlined THEME_JS HEROVIDEO map, so their presence alone
# does NOT prove the hero renders. Assert the hero SECTIONS are actually emitted into the today DOM
# (both are always present, CSS-hidden for hero=none themes) -- this catches a severed hero wiring.
checks["hero-video section rendered"] = 'id="heroVideo"' in html
checks["cosmos dashboard rendered"] = "hero-cosmic" in html and 'id="gaugeArc"' in html
checks["hero video paths served"] = all(v in html for v in ("velorah.mp4", "voyage.mp4", "aethera.mp4"))
checks["live build == T040"] = "b189d3cc0703" in subprocess.run(
    ["curl", "-s", "--max-time", "15", URL + "build.json"], capture_output=True, text=True).stdout

print(f"served bytes: {len(html)}")
for k, v in checks.items():
    print(("  OK  " if v else " MISS ") + k)
ok = all(checks.values())
print("\nLIVE CONTRACT COMPLETE:", ok)
sys.exit(0 if ok else 1)
