#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml

parser = argparse.ArgumentParser(description="Validate and compile the human-editable v4.2 model overlay.")
parser.add_argument("input", nargs="?", default="config/model_runtime_defaults.yaml")
parser.add_argument("--output", default="artifacts/model_runtime_defaults.compiled.json")
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

obj = yaml.safe_load(Path(args.input).read_text(encoding="utf-8"))
weights = obj.get("weights", {})
if not weights or not math.isclose(sum(float(value) for value in weights.values()), 1.0, abs_tol=1e-4):
    raise SystemExit("weights must sum to 1.0 ± 0.0001")
if any(float(value) < 0 or float(value) > 0.70 for value in weights.values()):
    raise SystemExit("each top-level weight must be within 0..0.70")

for key, value in obj.get("half_life_days", {}).items():
    if not 30 <= int(value) <= 1825:
        raise SystemExit(f"invalid half-life {key}={value}")

for key, value in obj.get("thresholds", {}).items():
    if key.startswith("visible_"):
        continue
    if not 0 <= float(value) <= 100:
        raise SystemExit(f"invalid score threshold {key}={value}")

visual = obj.get("visual", {})
if float(visual.get("home_visual_surface_ratio", 0)) < 0.90:
    raise SystemExit("home_visual_surface_ratio must be >= 0.90")
if float(visual.get("system_visual_first_coverage", 0)) < 0.80:
    raise SystemExit("system_visual_first_coverage must be >= 0.80")

calibration = obj.get("calibration", {})
if int(calibration.get("cadence_days", 0)) != 14:
    raise SystemExit("calibration cadence must remain exactly 14 days")
if calibration.get("auto_activate") is not False:
    raise SystemExit("calibration proposals must not auto-activate")

compiled = {
    "schema_version": "1.1",
    "compiled_from": args.input,
    "config": obj,
    "production_boundary": "dry-run overlay only; Codex must implement transactional DB/API activation",
}
text = json.dumps(compiled, ensure_ascii=False, indent=2)
if args.dry_run:
    print(text)
else:
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")
    print(output)
