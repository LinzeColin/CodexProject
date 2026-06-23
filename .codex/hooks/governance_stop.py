#!/usr/bin/env python3
"""Lightweight Codex Stop Hook for CodexProject governance hints.

The Stop Hook is intentionally outside the expensive governance proof path.
It must not generate files, write receipts, run semantic validators, or block a
turn because a derived dashboard or attestation needs recomputation.
"""

from __future__ import annotations

import json
import sys
from typing import Any


SUGGESTED_COMMANDS = [
    "python3 scripts/lean_governance.py ci --changed-only --base-ref <base_ref>",
    "python3 -m unittest discover -s tests/governance -p 'test_*.py' -q",
]


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def read_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    read_payload()
    hint: dict[str, Any] = {
        "mode": "advisory",
        "message": (
            "Stop Hook is advisory only. Run explicit governance validation before PR, "
            "release, or high-risk governance changes; the hook does not inspect files."
        ),
        "suggested_commands": SUGGESTED_COMMANDS,
    }
    emit({"continue": True, "governance_hint": hint})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
