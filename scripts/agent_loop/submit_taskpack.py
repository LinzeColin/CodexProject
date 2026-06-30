#!/usr/bin/env python3
"""Submit an approved Agent Loop Task Pack through local GitHub CLI.

This script uses existing `gh` authentication. It does not ask for, store, or
print tokens.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)
WORKFLOW_FILE = ".github/workflows/agent-loop-run-approved-taskpack.yml"
DISPATCH_PAYLOAD_LIMIT_BYTES = 60000


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_taskpack(path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    if "AGENT_LOOP_METADATA" not in text:
        raise SystemExit("Task Pack must contain AGENT_LOOP_METADATA")
    return text


def extract_metadata(text: str) -> dict:
    match = META_RE.search(text)
    if not match:
        raise SystemExit("missing AGENT_LOOP_METADATA wrapper")
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"metadata JSON parse failed: {exc}") from exc
    if not isinstance(metadata, dict):
        raise SystemExit("metadata must be a JSON object")
    return metadata


def extract_title(text: str, metadata: dict) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title[:120]
    return str(metadata.get("roadmap_task_id") or "Approved Task Pack")[:120]


def validate_taskpack(taskpack_path: str) -> None:
    validator = repo_root() / "scripts" / "agent_loop" / "validate_taskpack.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--taskpack", taskpack_path],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def require_gh() -> None:
    if not shutil.which("gh"):
        raise SystemExit(
            "GitHub CLI `gh` is not installed. Install GitHub CLI and run `gh auth login`; do not create a PAT for this script."
        )
    result = subprocess.run(
        ["gh", "auth", "status"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            "GitHub CLI is not authenticated. Run `gh auth login` with your normal GitHub account; do not paste tokens into this script."
        )


def run_gh(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def ensure_labels(repo: str, risk: str, dry_run_local: bool) -> None:
    labels = [
        ("source:chatgpt-approved", "0e8a16", "Approved ChatGPT Task Pack"),
        ("agent:run", "5319e7", "Agent Loop run"),
        (f"risk:{risk}", "fbca04", f"Agent Loop risk tier {risk}"),
    ]
    for name, color, description in labels:
        if dry_run_local:
            print(f"DRY_RUN_LOCAL would ensure label: {name}")
            continue
        result = run_gh(
            [
                "label",
                "create",
                name,
                "--repo",
                repo,
                "--color",
                color,
                "--description",
                description,
            ]
        )
        if result.returncode != 0 and "already exists" not in result.stdout.lower():
            print(result.stdout, end="")
            raise SystemExit(result.returncode)


def submit_issue(repo: str, taskpack_path: str, text: str, metadata: dict, title: str, dry_run_local: bool) -> None:
    risk = str(metadata["risk_tier"])
    labels = ["source:chatgpt-approved", f"risk:{risk}"]
    if len(text.encode("utf-8")) > 60000:
        print("WARNING: issue body is large and may approach GitHub limits.")
    ensure_labels(repo, risk, dry_run_local)
    if dry_run_local:
        print("DRY_RUN_LOCAL would create issue with labels: " + ", ".join(labels))
        print("DRY_RUN_LOCAL would add label agent:run after issue creation")
        print(f"DRY_RUN_LOCAL title: [Agent Loop] {title}")
        return

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(text)
        body_file = handle.name
    try:
        result = run_gh(
            [
                "issue",
                "create",
                "--repo",
                repo,
                "--title",
                f"[Agent Loop] {title}",
                "--body-file",
                body_file,
                "--label",
                labels[0],
                "--label",
                labels[1],
            ]
        )
    finally:
        Path(body_file).unlink(missing_ok=True)
    print(result.stdout, end="")
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    issue_url = result.stdout.strip().splitlines()[-1]
    edit = run_gh(["issue", "edit", issue_url, "--repo", repo, "--add-label", "agent:run"])
    print(edit.stdout, end="")
    if edit.returncode != 0:
        raise SystemExit(edit.returncode)
    print(f"ISSUE_URL={issue_url}")


def submit_dispatch(repo: str, text: str, metadata: dict, title: str, dry_run_local: bool) -> None:
    risk = str(metadata["risk_tier"])
    payload = {
        "event_type": "agent_loop_taskpack",
        "client_payload": {
            "taskpack": text,
            "source": "chatgpt-approved",
            "title": title,
            "risk_tier": risk,
        },
    }
    payload_text = json.dumps(payload, ensure_ascii=False)
    payload_bytes = len(payload_text.encode("utf-8"))
    if payload_bytes > DISPATCH_PAYLOAD_LIMIT_BYTES:
        raise SystemExit(
            f"repository_dispatch payload is {payload_bytes} bytes, above safe limit {DISPATCH_PAYLOAD_LIMIT_BYTES}. "
            "Use issue mode instead."
        )
    if dry_run_local:
        print(f"DRY_RUN_LOCAL would POST repos/{repo}/dispatches")
        print(f"DRY_RUN_LOCAL event_type=agent_loop_taskpack risk_tier={risk} bytes={payload_bytes}")
        return
    result = run_gh(["api", f"repos/{repo}/dispatches", "--method", "POST", "--input", "-"], input_text=payload_text)
    print(result.stdout, end="")
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print("DISPATCH_SENT=agent_loop_taskpack")
    print(f"Check Actions: https://github.com/{repo}/actions/workflows/agent-loop-run-approved-taskpack.yml")


def submit_workflow(repo: str, text: str, dry_run: bool, dry_run_local: bool, ref: str) -> None:
    payload = {"taskpack": text, "dry_run": dry_run}
    payload_text = json.dumps(payload, ensure_ascii=False)
    if dry_run_local:
        print(f"DRY_RUN_LOCAL would run workflow {WORKFLOW_FILE} on ref {ref}")
        print(f"DRY_RUN_LOCAL workflow dry_run={dry_run}")
        return
    result = run_gh(
        ["workflow", "run", WORKFLOW_FILE, "--repo", repo, "--ref", ref, "--json"],
        input_text=payload_text,
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print("WORKFLOW_DISPATCH_SENT=1")
    print(f"Check runs: gh run list --repo {repo} --workflow {WORKFLOW_FILE}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit an approved Agent Loop Task Pack.")
    parser.add_argument("--taskpack", required=True, help="Path to approved dual-plane Task Pack Markdown.")
    parser.add_argument("--mode", required=True, choices=["issue", "dispatch", "workflow"])
    parser.add_argument("--repo", default="LinzeColin/CodexProject")
    parser.add_argument("--ref", default="main", help="Workflow ref for workflow mode.")
    parser.add_argument("--dry-run", action="store_true", help="Set workflow input dry_run=true in workflow mode.")
    parser.add_argument("--dry-run-local", action="store_true", help="Validate and print intended action without calling GitHub.")
    args = parser.parse_args()

    text = read_taskpack(args.taskpack)
    validate_taskpack(args.taskpack)
    metadata = extract_metadata(text)
    title = extract_title(text, metadata)

    print(f"TASKPACK_TITLE={title}")
    print(f"PROJECT={metadata.get('project')}")
    print(f"RISK_TIER={metadata.get('risk_tier')}")

    if not args.dry_run_local:
        require_gh()

    if args.mode == "issue":
        submit_issue(args.repo, args.taskpack, text, metadata, title, args.dry_run_local)
    elif args.mode == "dispatch":
        submit_dispatch(args.repo, text, metadata, title, args.dry_run_local)
    else:
        submit_workflow(args.repo, text, args.dry_run, args.dry_run_local, args.ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
