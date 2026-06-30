#!/usr/bin/env python3
"""Extract an approved Agent Loop Task Pack into workflow files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)


def read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def extract_metadata(text: str) -> dict:
    match = META_RE.search(text)
    if not match:
        raise ValueError("missing AGENT_LOOP_METADATA wrapper")
    return json.loads(match.group(1))


def extract_title(text: str, metadata: dict) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()[:120] or "Approved Task Pack"
    task_id = metadata.get("roadmap_task_id") or "approved-taskpack"
    return str(task_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Task Pack file. Reads stdin when omitted.")
    parser.add_argument("--out-dir", default="agent-loop-work")
    args = parser.parse_args()

    text = read_input(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    metadata = extract_metadata(text)
    title = extract_title(text, metadata)

    (out_dir / "taskpack.md").write_text(text, encoding="utf-8")
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "title.txt").write_text(title + "\n", encoding="utf-8")
    print(f"TASKPACK_TITLE={title}")
    print(f"RISK_TIER={metadata.get('risk_tier', '')}")
    print(f"MAX_AUTOFIX_LOOPS={metadata.get('max_autofix_loops', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
