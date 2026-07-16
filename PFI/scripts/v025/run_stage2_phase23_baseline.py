#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_v02.stage_v025_safe_sandbox import (
    build_sandbox_attestation,
    isolate_operational_sqlite,
    resolve_git_object_snapshot,
    run_git_object_read_parse_baseline,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PFI v0.2.5 Phase 2.3 redacted read-only baseline.")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--git-ref", default="HEAD")
    parser.add_argument("--iterations", type=int, default=3)
    args = parser.parse_args()

    snapshot = resolve_git_object_snapshot(args.repo_root, git_ref=args.git_ref)
    performance = run_git_object_read_parse_baseline(
        args.repo_root,
        git_ref=args.git_ref,
        iterations=args.iterations,
    )
    database = isolate_operational_sqlite(args.repo_root)
    sandbox = build_sandbox_attestation(snapshot, database)
    payload = {
        "schema": "PFIV025Phase23BaselineRunV1",
        "version": "v0.2.5",
        "stage": 2,
        "phase": "2.3",
        "status": "pass" if sandbox["status"] == "pass" and performance["status"] == "pass" else "blocked",
        "sandbox_attestation": sandbox,
        "database_before_after": database,
        "performance_baseline": performance,
        "private_values_included": False,
        "financial_fixture_fallback_used": False,
        "source_mutation_performed": bool(database["source_mutation_performed"]),
        "finder_used": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
