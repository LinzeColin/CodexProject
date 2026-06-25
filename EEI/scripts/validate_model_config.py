#!/usr/bin/env python3
"""Validate editable model/threshold JSON files before import."""
from __future__ import annotations
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
MOTION_DURATION_KEYS = (
    "instant",
    "local",
    "panel",
    "data_update",
    "lens_change",
    "reroot",
    "full_relayout_max",
)


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_parameter_catalog() -> dict[str, dict[str, str]]:
    with (ROOT / "data/parameter_catalog.csv").open(newline="", encoding="utf-8-sig") as handle:
        return {row["parameter_key"]: row for row in csv.DictReader(handle)}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def validate_profile(profile_path: Path) -> dict[str, Any]:
    profile = load(profile_path)
    schema = load(ROOT / "specs/model_config_schema.json")
    errors = sorted(Draft202012Validator(schema).iter_errors(profile), key=lambda e: list(e.path))
    if errors:
        for error in errors:
            print(f"PROFILE {list(error.path)}: {error.message}", file=sys.stderr)
        raise SystemExit(2)

    total = sum(float(v) for v in profile["weights"].values())
    if not math.isclose(total, 1.0, abs_tol=0.0001):
        fail(f"top-level weights sum to {total:.6f}; expected 1.0 ± 0.0001")

    for component, weights in profile.get("component_weights", {}).items():
        subtotal = sum(float(v) for v in weights.values())
        if not math.isclose(subtotal, 1.0, abs_tol=0.0001):
            fail(f"component_weights.{component} sum to {subtotal:.6f}; expected 1.0 ± 0.0001")

    for name in ("quality_adjustment", "coverage_adjustment"):
        subtotal = sum(float(v) for v in profile[name].values())
        if not math.isclose(subtotal, 1.0, abs_tol=0.0001):
            fail(f"{name} sums to {subtotal:.6f}; expected 1.0 ± 0.0001")
    return profile


def validate_thresholds(threshold_path: Path) -> dict[str, Any]:
    thresholds = load(threshold_path)
    if thresholds.get("schema_version") != "2.0":
        fail("threshold schema_version must be 2.0")
    if thresholds.get("calibration", {}).get("cadence_days") != 14:
        fail("calibration cadence must remain exactly 14 days")
    if thresholds.get("calibration", {}).get("auto_activate") is not False:
        fail("calibration proposals must not auto-activate")

    graph = thresholds.get("graph", {})
    if not 12 <= int(graph.get("home_max_nodes", 0)) <= 120:
        fail("graph.home_max_nodes must be between 12 and 120")
    if not 16 <= int(graph.get("home_max_edges", 0)) <= 240:
        fail("graph.home_max_edges must be between 16 and 240")

    visual = thresholds.get("visual", {})
    if float(visual.get("home_visual_surface_ratio", 0)) < 0.90:
        fail("visual.home_visual_surface_ratio cannot be below 0.90")
    if float(visual.get("system_visual_first_coverage", 0)) < 0.80:
        fail("visual.system_visual_first_coverage cannot be below 0.80")
    return thresholds


def validate_motion_tokens(motion_path: Path = ROOT / "config/ui/motion-tokens.json") -> dict[str, Any]:
    motion = load(motion_path)
    if motion.get("schema_version") != "1.0":
        fail("motion token schema_version must be 1.0")

    durations = motion.get("durations_ms")
    if not isinstance(durations, dict):
        fail("motion.durations_ms must be an object")
    catalog = load_parameter_catalog()
    for key in MOTION_DURATION_KEYS:
        parameter_key = f"motion.{key}"
        if parameter_key not in catalog:
            fail(f"parameter catalog missing {parameter_key}")
        if key not in durations:
            fail(f"motion.durations_ms.{key} is required")
        value = int(durations[key])
        row = catalog[parameter_key]
        minimum = int(row["min_value"])
        maximum = int(row["max_value"])
        step = int(row["step"])
        if not minimum <= value <= maximum:
            fail(f"motion.durations_ms.{key}={value} outside catalog range {minimum}..{maximum}")
        if (value - minimum) % step != 0:
            fail(f"motion.durations_ms.{key}={value} does not align to catalog step {step}")

    reduced_motion = motion.get("reduced_motion")
    if not isinstance(reduced_motion, dict):
        fail("motion.reduced_motion must be an object")
    if reduced_motion.get("respect_system") is not True:
        fail("motion.reduced_motion.respect_system must be true")
    if reduced_motion.get("disable_spatial_motion") is not True:
        fail("motion.reduced_motion.disable_spatial_motion must be true")
    return motion


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: validate_model_config.py PROFILE.json THRESHOLDS.json", file=sys.stderr)
        return 2
    profile_path, threshold_path = map(Path, argv[1:])
    profile = validate_profile(profile_path)
    thresholds = validate_thresholds(threshold_path)
    motion = validate_motion_tokens()
    print(json.dumps({
        "valid": True,
        "profile_key": profile["profile_key"],
        "profile_version": profile["version"],
        "threshold_profile_key": thresholds["threshold_profile_key"],
        "threshold_version": thresholds["version"],
        "weight_sum": round(sum(profile["weights"].values()), 6),
        "calibration_days": thresholds["calibration"]["cadence_days"],
        "motion_duration_count": len(motion["durations_ms"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
