#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_v02.stage_v025_stage2_whole_review import verify_stage2_whole_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only PFI v0.2.5 Stage 2 whole-stage verifier")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--candidate")
    parser.add_argument("--task-pack")
    args = parser.parse_args()
    result = verify_stage2_whole_review(
        Path(args.repo_root),
        candidate=args.candidate,
        task_pack=args.task_pack,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
