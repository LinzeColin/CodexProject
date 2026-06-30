#!/usr/bin/env python3
"""Enforce Agent Loop T1/T2 merge policy."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)


def load_metadata(taskpack: str) -> dict:
    text = Path(taskpack).read_text(encoding="utf-8")
    match = META_RE.search(text)
    if not match:
        raise ValueError("missing metadata wrapper")
    return json.loads(match.group(1))


def read_optional(path: str | None) -> str:
    if not path:
        return ""
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="ignore")


def review_has_blocker(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    if re.search(r"unresolved\s+p0\s*/\s*p1\s*:\s*(no|false)", lower):
        return False
    if re.search(r"unresolved\s+p[01]\s*:\s*(no|false)", lower):
        return False
    if re.search(r"unresolved\s+p0\s*/\s*p1\s*:\s*(yes|true)", lower):
        return True
    if re.search(r"unresolved\s+p[01]\s*:\s*(yes|true)", lower):
        return True
    if re.search(r"\bp[01]\b", lower) and not re.search(r"unresolved\s+p[01]\s*:\s*(no|false)", lower):
        return True
    return False


def plan_mentions_rollback(plan: str) -> bool:
    return bool(re.search(r"^##\s+rollback", plan, re.I | re.M)) or "rollback" in plan.lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taskpack", required=True)
    parser.add_argument("--plan")
    parser.add_argument("--taskpack-status", choices=["PASS", "FAIL"], required=True)
    parser.add_argument("--plan-status", choices=["PASS", "FAIL", "N/A"], required=True)
    parser.add_argument("--validation-status", choices=["PASS", "FAIL"], required=True)
    parser.add_argument("--changed-files-status", choices=["PASS", "FAIL"], required=True)
    parser.add_argument("--review-file", action="append", default=[])
    parser.add_argument("--block-merge", action="store_true")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    metadata = load_metadata(args.taskpack)
    errors: list[str] = []
    tier = metadata.get("risk_tier")
    plan_text = read_optional(args.plan)

    if args.block_merge:
        errors.append("BLOCK_MERGE=true")
    if args.taskpack_status != "PASS":
        errors.append("Task Pack validation failed")
    if args.validation_status != "PASS":
        errors.append("implementation validation failed")
    if args.changed_files_status != "PASS":
        errors.append("changed-files policy failed")
    if metadata.get("auto_merge") is not True:
        errors.append("auto_merge is not true")
    if metadata.get("production_deploy") is not False:
        errors.append("production deploy attempted or authorized outside bootstrap policy")

    if tier not in {"T1", "T2"}:
        errors.append("risk_tier must be T1 or T2")
    if tier == "T2":
        if not args.plan or not plan_text:
            errors.append("T2 requires plan evidence")
        if args.plan_status != "PASS":
            errors.append("T2 plan validation failed")
        if metadata.get("plan_required") is not True:
            errors.append("T2 requires plan_required true")
        if not plan_mentions_rollback(plan_text):
            errors.append("T2 requires rollback in plan")
    elif metadata.get("plan_required") is True and args.plan_status != "PASS":
        errors.append("Task Pack requires plan validation")

    for review_path in args.review_file:
        if review_has_blocker(read_optional(review_path)):
            errors.append(f"unresolved P0/P1 issue in {review_path}")

    result = {
        "risk_tier": tier,
        "merge_allowed": not errors,
        "block_merge": bool(errors),
        "errors": errors,
    }
    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if errors:
        print("MERGE_POLICY=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("MERGE_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
