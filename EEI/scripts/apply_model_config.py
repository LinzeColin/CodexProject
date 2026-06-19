#!/usr/bin/env python3
"""Create a deterministic import preview for a model configuration.

This task pack intentionally does not write to a production database. Codex must
replace the adapter after the schema/API implementation exists. Without
--dry-run this command refuses to proceed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--thresholds", required=True, type=Path)
    parser.add_argument("--reason", default="dry-run review")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    subprocess.run([
        sys.executable,
        str(ROOT / "scripts/validate_model_config.py"),
        str(args.profile),
        str(args.thresholds),
    ], check=True, stdout=subprocess.DEVNULL)

    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    bundle = {
        "mode": "dry-run" if args.dry_run else "refused",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reason": args.reason,
        "profile_key": profile["profile_key"],
        "profile_version": profile["version"],
        "threshold_profile_key": thresholds["threshold_profile_key"],
        "threshold_version": thresholds["version"],
        "profile_sha256": canonical_hash(profile),
        "thresholds_sha256": canonical_hash(thresholds),
        "affected_modules": [
            "business_atlas", "supply_chain", "capital", "control",
            "policy", "strategic_signals", "watchlist", "changes"
        ],
        "expected_flow": [
            "validate", "preview", "save immutable version", "append operation log",
            "queue incremental recomputation", "validate snapshot", "atomic activate", "broadcast SSE"
        ]
    }
    out = ROOT / "artifacts/model_config_import_preview.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)

    if not args.dry_run:
        print("REFUSED: task pack has no production database adapter; use --dry-run and let Codex implement the API/DB transaction first.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
