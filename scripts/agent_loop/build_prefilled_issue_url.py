#!/usr/bin/env python3
"""Build a prefilled GitHub issue URL for an approved Task Pack."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlencode


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)
LONG_URL_WARNING_BYTES = 8000


def read_taskpack(path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    if "AGENT_LOOP_METADATA" not in text:
        raise SystemExit("Task Pack must contain AGENT_LOOP_METADATA")
    return text


def extract_metadata(text: str) -> dict:
    match = META_RE.search(text)
    if not match:
        raise SystemExit("missing AGENT_LOOP_METADATA wrapper")
    return json.loads(match.group(1))


def extract_title(text: str, metadata: dict) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title[:120]
    return str(metadata.get("roadmap_task_id") or "Approved Task Pack")[:120]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a GitHub issue form URL for a Task Pack.")
    parser.add_argument("--taskpack", required=True)
    parser.add_argument("--repo", default="LinzeColin/CodexProject")
    parser.add_argument("--template", default="codex-task.yml")
    args = parser.parse_args()

    text = read_taskpack(args.taskpack)
    metadata = extract_metadata(text)
    title = extract_title(text, metadata)
    risk = str(metadata.get("risk_tier", "T1"))
    labels = f"source:chatgpt-approved,agent:run,risk:{risk}"
    query = urlencode(
        {
            "template": args.template,
            "title": f"[Agent Loop] {title}",
            "labels": labels,
            "taskpack": text,
        }
    )
    url = f"https://github.com/{args.repo}/issues/new?{query}"
    print(url)
    url_bytes = len(url.encode("utf-8"))
    print(f"URL_BYTES={url_bytes}")
    if url_bytes > LONG_URL_WARNING_BYTES:
        print(
            "WARNING: URL is likely too long for reliable browser handling. "
            "Use `python3 scripts/agent_loop/submit_taskpack.py --mode issue` instead."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
