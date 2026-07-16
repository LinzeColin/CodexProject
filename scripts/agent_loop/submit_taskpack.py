#!/usr/bin/env python3
"""Publish one external-authenticated Automation C PR without creating Issues."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path


META_RE = re.compile(
    r"<!--\s*AGENT_LOOP_METADATA\s*(.*?)\s*END_AGENT_LOOP_METADATA\s*-->",
    re.DOTALL,
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
BRANCH_RE = re.compile(r"^automation-c/[A-Za-z0-9][A-Za-z0-9._/-]{0,180}$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_taskpack(path: Path) -> tuple[str, dict]:
    text = path.read_text(encoding="utf-8")
    match = META_RE.search(text)
    if match is None:
        raise SystemExit("Task Pack must contain AGENT_LOOP_METADATA")
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"metadata JSON parse failed: {exc}") from exc
    if not isinstance(metadata, dict):
        raise SystemExit("metadata must be a JSON object")
    return text, metadata


def validate_taskpack(path: Path) -> None:
    process = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "agent_loop" / "validate_taskpack.py"),
            "--taskpack",
            str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    print(process.stdout, end="")
    if process.returncode != 0:
        raise SystemExit(process.returncode)


def require_gh() -> None:
    if shutil.which("gh") is None:
        raise SystemExit("GitHub CLI `gh` is required; do not add a repository PAT")
    process = subprocess.run(
        ["gh", "auth", "status"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise SystemExit("Run `gh auth login` with the external publisher identity")


def gh_json(*args: str) -> object:
    process = subprocess.run(
        ["gh", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise SystemExit(process.stdout.strip() or f"gh command failed: {' '.join(args)}")
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("GitHub CLI returned non-JSON output") from exc


def ref_sha(repo: str, branch: str) -> str:
    encoded = urllib.parse.quote(f"heads/{branch}", safe="/")
    payload = gh_json("api", f"repos/{repo}/git/ref/{encoded}")
    if not isinstance(payload, dict):
        raise SystemExit(f"unexpected ref response for {branch}")
    sha = payload.get("object", {}).get("sha")
    if not isinstance(sha, str) or SHA_RE.fullmatch(sha) is None:
        raise SystemExit(f"invalid ref SHA returned for {branch}")
    return sha


def validate_transaction_branch(branch: str) -> None:
    if BRANCH_RE.fullmatch(branch) is None:
        raise SystemExit(
            "head must be a reserved same-repository branch under automation-c/"
        )
    if (
        ".." in branch
        or "//" in branch
        or "@{" in branch
        or branch.endswith((".", "/", ".lock"))
    ):
        raise SystemExit("head is not a valid Automation C transaction branch")


def precheck_zero_open(repo: str) -> None:
    pulls = gh_json("api", f"repos/{repo}/pulls?state=open&per_page=100")
    issues = gh_json("api", f"repos/{repo}/issues?state=open&per_page=100")
    if not isinstance(pulls, list) or not isinstance(issues, list):
        raise SystemExit("unexpected GitHub precheck response")
    standalone_issues = [item for item in issues if "pull_request" not in item]
    if pulls or standalone_issues:
        raise SystemExit(
            f"Automation C single-flight precheck failed: open_pr={len(pulls)} open_issue={len(standalone_issues)}"
        )


def title_from(text: str, task_id: str) -> str:
    for line in text.splitlines():
        if line.startswith("# ") and line[2:].strip():
            return f"[{task_id}] {line[2:].strip()}"[:240]
    return f"[{task_id}] approved Task Pack"


def pr_body(text: str, task_id: str, acceptance_id: str, head_sha: str, base_sha: str) -> str:
    marker = (
        "<!-- AUTOMATION_C_TRANSACTION_V1\n"
        f"task_id={task_id}\n"
        f"acceptance_id={acceptance_id}\n"
        f"head_sha={head_sha}\n"
        f"base_sha={base_sha}\n"
        "END_AUTOMATION_C_TRANSACTION_V1 -->\n"
    )
    return (
        marker
        + "\n# Automation C Transaction\n\n"
        + "This same-repository, non-draft PR was created by an external authenticated publisher. "
        + "Project Governance must pass on the exact head and base before trusted settlement.\n\n"
        + text
    )


def publish(repo: str, head: str, base: str, body: str, title: str) -> str:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(body)
        body_path = Path(handle.name)
    try:
        process = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                repo,
                "--head",
                head,
                "--base",
                base,
                "--title",
                title,
                "--body-file",
                str(body_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    finally:
        body_path.unlink(missing_ok=True)
    if process.returncode != 0:
        raise SystemExit(process.stdout.strip() or "gh pr create failed")
    return process.stdout.strip().splitlines()[-1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create one Automation C PR from an already-pushed same-repository branch."
    )
    parser.add_argument("--taskpack", required=True, type=Path)
    parser.add_argument("--head", required=True, help="Existing same-repository transaction branch")
    parser.add_argument("--base", default="main")
    parser.add_argument("--repo", default="LinzeColin/CodexProject")
    parser.add_argument("--dry-run-local", action="store_true")
    parser.add_argument("--confirm-publish", action="store_true")
    args = parser.parse_args()

    if args.base != "main":
        raise SystemExit("base must be main")
    validate_transaction_branch(args.head)
    validate_taskpack(args.taskpack)
    text, metadata = read_taskpack(args.taskpack)
    if args.repo != metadata.get("repository"):
        raise SystemExit("--repo must exactly match Task Pack metadata repository")
    task_id = str(metadata["roadmap_task_id"])
    acceptance_id = str(metadata["acceptance_id"])
    print(f"TASK_ID={task_id}")
    print(f"ACCEPTANCE_ID={acceptance_id}")
    print("ISSUE_MUTATION=0")
    if args.dry_run_local:
        print(f"DRY_RUN_LOCAL head={args.head} base=main repo={args.repo}")
        return 0
    if not args.confirm_publish:
        raise SystemExit("--confirm-publish is required for the external GitHub write")
    require_gh()
    precheck_zero_open(args.repo)
    head_sha = ref_sha(args.repo, args.head)
    base_sha = ref_sha(args.repo, args.base)
    body = pr_body(text, task_id, acceptance_id, head_sha, base_sha)
    url = publish(args.repo, args.head, args.base, body, title_from(text, task_id))
    print(f"PR_URL={url}")
    print(f"EXPECTED_HEAD_SHA={head_sha}")
    print(f"EXPECTED_BASE_SHA={base_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
