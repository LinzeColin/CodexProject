#!/usr/bin/env python3
"""ADP V0.1 task runner -- one task, one result, dependency-aware, never self-PASS.

Given a task_id, it:
  1. looks the task up in TASK_INDEX.csv (must exist, exactly one);
  2. lists its declared dependencies and checks each dependency has an evidence
     bundle that passes validate_evidence (i.e. dependency is at least
     READY_FOR_INDEPENDENT_VERIFICATION);
  3. validates the task's own evidence bundle;
  4. prints a single status for the single task.

Statuses: BLOCKED_BY_DEPS / INCOMPLETE / READY_FOR_INDEPENDENT_VERIFICATION.
It NEVER prints PASS -- PASS/FAIL is an independent reviewer's decision. It does
not mutate anything.

Usage:
  python3 task_runner.py <task_id>
"""
import argparse, csv, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
INDEX = HERE.parent / "TASK_INDEX.csv"
EVID = HERE.parent / "evidence"

sys.path.insert(0, str(HERE))
import validate_evidence as ve  # noqa: E402


def load_index():
    with open(INDEX, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    by_id = {}
    for r in rows:
        by_id[(r.get("task_id") or "").strip()] = r
    return by_id


def deps_of(row):
    raw = (row.get("dependencies") or "").strip()
    return [d.strip() for d in raw.replace(",", ";").split(";") if d.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id")
    args = ap.parse_args()

    by_id = load_index()
    if args.task_id not in by_id:
        print(f"task_id: {args.task_id}")
        print("STATUS: UNKNOWN_TASK (not in TASK_INDEX.csv)")
        sys.exit(2)

    row = by_id[args.task_id]
    deps = deps_of(row)
    print(f"task_id: {args.task_id}")
    print(f"stage/phase: {row.get('stage_id')}/{row.get('phase_id')}  size={row.get('size')}  release_mode={row.get('release_mode')}")
    print(f"title: {row.get('title')}")
    print(f"dependencies ({len(deps)}): {deps or '(none)'}")

    # 1. dependency readiness
    unmet = []
    for d in deps:
        if d not in by_id:
            unmet.append(f"{d} (not in index)")
            continue
        probs = ve.validate(d, str(EVID))
        if probs:
            unmet.append(d)
    if unmet:
        print("STATUS: BLOCKED_BY_DEPS")
        for d in unmet:
            print(f"  - dependency not READY: {d}")
        sys.exit(1)

    # 2. this task's own evidence
    probs = ve.validate(args.task_id, str(EVID))
    if probs:
        print("STATUS: INCOMPLETE")
        for p in probs:
            print("  - " + p)
        sys.exit(1)

    print("STATUS: READY_FOR_INDEPENDENT_VERIFICATION")
    print("  one task, one result; dependencies satisfied; evidence complete.")
    print("  NOTE: this runner never issues PASS -- an independent context must judge PASS/FAIL.")
    sys.exit(0)


if __name__ == "__main__":
    main()
