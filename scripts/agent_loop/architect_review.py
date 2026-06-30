#!/usr/bin/env python3
"""Optional ChatGPT-style Architect Review for Agent Loop.

If OPENAI_API_KEY is missing or the API call fails, this script writes an
explicit ARCHITECT_REVIEW=N/A report. It never generates a new Task Pack.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def read(path: str | None, limit: int = 60000) -> str:
    if not path:
        return ""
    file_path = Path(path)
    if not file_path.exists():
        return ""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return text[:limit]


def write_na(output: str, reason: str) -> int:
    Path(output).write_text(
        f"# Architect Review\n\nARCHITECT_REVIEW=N/A\n\nReason: {reason}\n",
        encoding="utf-8",
    )
    print("ARCHITECT_REVIEW=N/A")
    print(f"Reason: {reason}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taskpack", required=True)
    parser.add_argument("--diff")
    parser.add_argument("--validation")
    parser.add_argument("--codex-review")
    parser.add_argument("--output", default="architect-review.md")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return write_na(args.output, "OPENAI_API_KEY is not available")

    model = os.environ.get("OPENAI_ARCHITECT_MODEL", "gpt-4.1-mini")
    prompt = f"""You are the optional Architect Review for CodexProject Agent Loop.

Do not generate a new Task Pack. Review the approved Task Pack, final diff,
validation result, Codex review, and acceptance criteria.

Return Markdown with:
- ARCHITECT_REVIEW=PASS, FAIL, or N/A
- Unresolved P0/P1: yes/no
- Scope drift
- Validation gaps
- Security/privacy risks
- Merge recommendation

Approved Task Pack:
{read(args.taskpack)}

Diff:
{read(args.diff)}

Validation:
{read(args.validation)}

Codex Review:
{read(args.codex_review)}
"""
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": "You are a concise software architecture reviewer."},
            {"role": "user", "content": prompt},
        ],
        "max_output_tokens": 1600,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return write_na(args.output, f"OpenAI API review was not feasible: {type(exc).__name__}")

    output_text = data.get("output_text")
    if not output_text:
        chunks: list[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    chunks.append(content.get("text", ""))
        output_text = "\n".join(chunks).strip()
    if not output_text:
        return write_na(args.output, "OpenAI API response did not include review text")

    Path(args.output).write_text(output_text + "\n", encoding="utf-8")
    first_line = output_text.splitlines()[0] if output_text.splitlines() else "ARCHITECT_REVIEW=PASS"
    print(first_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
