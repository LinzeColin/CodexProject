#!/usr/bin/env python3
"""ADP V0.1 evidence-bundle schema validator.

Checks that a task's evidence bundle at evidence/<task_id>/ is complete and
machine-acceptable. Enforces the anti-black-hole rules:
  - missing any required evidence  -> status can only be INCOMPLETE (never PASS);
  - the implementer may NOT self-sign a Stage Gate PASS. This validator therefore
    NEVER prints PASS; the strongest status it can emit is
    READY_FOR_INDEPENDENT_VERIFICATION.

Required evidence files (per the task package template):
  TASK_REPORT.md, changed_files.txt, commands.log, cost_value.json, known_gaps.md

Semantic checks:
  - TASK_REPORT.md must contain the completion marker
    IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION;
  - TASK_REPORT.md must NOT contain an implementer-issued Stage Gate PASS;
  - cost_value.json must parse and carry release_mode +
    recurring_cloud_cost_delta_usd_month (UNKNOWN != 0 is a documentation rule);
  - changed_files.txt must be non-empty.

Exit 0 => READY_FOR_INDEPENDENT_VERIFICATION; exit 1 => INCOMPLETE.

Usage:
  python3 validate_evidence.py <task_id> [--root EVIDENCE_DIR]
"""
import argparse, json, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent / "evidence"
REQUIRED = ["TASK_REPORT.md", "changed_files.txt", "commands.log", "cost_value.json", "known_gaps.md"]
MARKER = "IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION"
# an implementer self-signing a gate PASS looks like a Verifier line asserting PASS
SELF_SIGN_PATTERNS = ["verifier: pass", "verdict: pass", "stage gate: pass", "gate=pass", "gate: pass"]


def validate(task_id, root):
    bundle = pathlib.Path(root) / task_id
    problems = []
    if not bundle.is_dir():
        return [f"evidence bundle not found: {bundle}"]

    present = {p.name for p in bundle.iterdir() if p.is_file()}
    for req in REQUIRED:
        if req not in present:
            problems.append(f"missing required evidence: {req}")

    report = bundle / "TASK_REPORT.md"
    if report.exists():
        text = report.read_text(encoding="utf-8")
        if MARKER not in text:
            problems.append(f"TASK_REPORT.md missing completion marker {MARKER}")
        low = text.lower()
        for pat in SELF_SIGN_PATTERNS:
            if pat in low:
                problems.append(f"TASK_REPORT.md appears to self-sign a Stage Gate PASS ('{pat}') -- implementer must not self-sign")

    cost = bundle / "cost_value.json"
    if cost.exists():
        try:
            obj = json.loads(cost.read_text(encoding="utf-8"))
            if "release_mode" not in obj:
                problems.append("cost_value.json missing release_mode")
            if "recurring_cloud_cost_delta_usd_month" not in obj:
                problems.append("cost_value.json missing recurring_cloud_cost_delta_usd_month")
        except Exception as e:
            problems.append(f"cost_value.json does not parse: {e}")

    cf = bundle / "changed_files.txt"
    if cf.exists() and not cf.read_text(encoding="utf-8").strip():
        problems.append("changed_files.txt is empty")

    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    args = ap.parse_args()

    problems = validate(args.task_id, args.root)
    print(f"task_id: {args.task_id}")
    print(f"evidence root: {args.root}")
    if problems:
        print("STATUS: INCOMPLETE")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("STATUS: READY_FOR_INDEPENDENT_VERIFICATION")
    print("  (validator does NOT issue PASS; PASS/FAIL is an independent reviewer's decision)")
    sys.exit(0)


if __name__ == "__main__":
    main()
