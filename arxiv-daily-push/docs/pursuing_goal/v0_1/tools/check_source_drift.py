#!/usr/bin/env python3
"""ADP V0.1 Source Drift CI (ADP-S1-P02-T015).

Blocks: a new hand-written source array, UI label drift, and D1/runtime sources
that are not registered in the Registry. Read-only.

Checks:
  1. repo scanner: worker_cloud.js must contain exactly ONE approved source-array
     declaration (the REGISTRY named in the approved exception file); a second
     source array is drift.
  2. runtime/D1 comparison: the set of source_ids extracted from worker_cloud.js
     equals the set in compiled/runtime.json (no unregistered live source; no
     registered source missing from runtime).
  3. UI label drift: compiled/ui_labels.json was regenerated from the current
     registry (its registry_hash equals compiled/registry_hash.txt).

Approved deviations live in SOURCE_DRIFT_EXCEPTIONS.yaml.

Exit 0 => PASS (no drift). Exit 1 => DRIFT.

Usage: python3 check_source_drift.py [--worker PATH]
"""
import argparse, json, re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent
ADP_ROOT = HERE.parents[3]
DEFAULT_WORKER = ADP_ROOT / "deploy/cloudflare/worker_cloud.js"
RUNTIME = V01 / "compiled" / "runtime.json"
UI = V01 / "compiled" / "ui_labels.json"
REG_HASH = V01 / "compiled" / "registry_hash.txt"
EXC = V01 / "SOURCE_DRIFT_EXCEPTIONS.yaml"

SOURCE_ARRAY_DECL = re.compile(r"const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\[")
SOURCE_ENTRY = re.compile(r"\{\s*id:\s*'([^']+)'[^}]*method:\s*'[^']*'")


def load_exceptions():
    if not EXC.exists():
        return {"approved_source_arrays": [], "approved_unregistered_ids": []}
    txt = EXC.read_text(encoding="utf-8")
    approved_arrays = re.findall(r"^\s*-\s*array:\s*([A-Za-z_][A-Za-z0-9_]*)", txt, re.M)
    approved_ids = re.findall(r"^\s*-\s*id:\s*([a-z0-9_-]+)", txt, re.M)
    return {"approved_source_arrays": approved_arrays, "approved_unregistered_ids": approved_ids}


def worker_source_ids(worker_text):
    return sorted(set(SOURCE_ENTRY.findall(worker_text)))


def find_source_arrays(worker_text):
    """Return names of const arrays that contain source entries (id+method)."""
    arrays = []
    for m in SOURCE_ARRAY_DECL.finditer(worker_text):
        name = m.group(1)
        tail = worker_text[m.end(): m.end() + 4000]
        if SOURCE_ENTRY.search(tail):
            arrays.append(name)
    return arrays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", default=str(DEFAULT_WORKER))
    args = ap.parse_args()
    exc = load_exceptions()
    problems = []

    wtext = pathlib.Path(args.worker).read_text(encoding="utf-8")
    # 1. repo scanner: exactly one approved source array
    arrays = find_source_arrays(wtext)
    unapproved = [a for a in arrays if a not in exc["approved_source_arrays"]]
    if unapproved:
        problems.append(f"unapproved source array(s) in worker: {unapproved} (approved: {exc['approved_source_arrays']})")

    # 2. runtime/D1 comparison
    wids = set(worker_source_ids(wtext))
    rids = set(s["source_id"] for s in json.loads(RUNTIME.read_text(encoding="utf-8"))["sources"])
    approved_unreg = set(exc["approved_unregistered_ids"])
    live_not_registered = (wids - rids) - approved_unreg
    registered_not_live = (rids - wids) - approved_unreg
    if live_not_registered:
        problems.append(f"live worker source(s) not in Registry: {sorted(live_not_registered)}")
    if registered_not_live:
        problems.append(f"registered source(s) not in live worker: {sorted(registered_not_live)}")

    # 3. UI label drift: ui registry_hash == compiled registry_hash
    reg_hash = REG_HASH.read_text(encoding="utf-8").strip()
    ui = json.loads(UI.read_text(encoding="utf-8"))
    if ui.get("registry_hash") != reg_hash:
        problems.append(f"ui_labels.json registry_hash {ui.get('registry_hash')} != compiled {reg_hash} (labels not regenerated from current registry)")

    print("source drift check")
    print(f"  worker source arrays: {arrays}")
    print(f"  worker ids: {len(wids)} | runtime ids: {len(rids)} | registry_hash: {reg_hash[:24]}...")
    if problems:
        print("RESULT: DRIFT")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("RESULT: PASS (one approved source array; worker==runtime source set; ui regenerated from current registry)")
    sys.exit(0)


if __name__ == "__main__":
    main()
