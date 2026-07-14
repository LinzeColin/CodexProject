#!/usr/bin/env python3
"""Canonicalize a KMFA attendance JSON snapshot and compute a deterministic hash."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

VOLATILE_KEYS = {
    "run_id",
    "run_uuid",
    "acquired_at",
    "created_at",
    "updated_at",
    "generated_at",
    "local_path",
    "absolute_path",
    "access" + "_token",
    "signature",
    "request_nonce",
    "request_id",
    "trace_id",
}


def scrub(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in sorted(obj.items()) if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    return obj


def canonical_bytes(obj: Any) -> bytes:
    stable = scrub(obj)
    return json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--sha-out", required=True)
    args = parser.parse_args()
    src = Path(args.input_json)
    obj = json.loads(src.read_text(encoding="utf-8"))
    data = canonical_bytes(obj)
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_bytes(data)
    Path(args.sha_out).write_text(digest + "\n", encoding="utf-8")
    print(json.dumps({"input": str(src), "out": args.out, "sha256": digest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
