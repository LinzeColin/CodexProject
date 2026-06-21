#!/usr/bin/env python3
"""Report local and GitHub governance enforcement setup status."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def repo_full_name() -> str:
    remote = git_output("remote", "get-url", "origin")
    if remote.startswith("git@github.com:"):
        value = remote.removeprefix("git@github.com:").removesuffix(".git")
        return value
    if "github.com/" in remote:
        return remote.split("github.com/", 1)[1].removesuffix(".git")
    return "UNKNOWN"


def hook_status() -> dict[str, Any]:
    hooks_json = ROOT / ".codex" / "hooks.json"
    hook_script = ROOT / ".codex" / "hooks" / "governance_stop.py"
    config_template = ROOT / ".codex" / "config.template.toml"
    result = {
        "hooks_json_exists": hooks_json.is_file(),
        "governance_stop_exists": hook_script.is_file(),
        "config_template_enables_hooks": False,
        "trust_status": "UNVERIFIED",
        "notes": [
            "Codex project trust is a local app setting; this doctor can verify repository files but cannot prove the app has trusted them."
        ],
    }
    if config_template.exists():
        result["config_template_enables_hooks"] = "hooks = true" in config_template.read_text(encoding="utf-8")
    return result


def github_branch_status(owner_repo: str, token: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "repository": owner_repo,
        "branch": "main",
        "protected": "UNVERIFIED",
        "required_status_checks": "UNVERIFIED",
        "no_bypass": "UNVERIFIED",
    }
    if owner_repo == "UNKNOWN":
        result["error"] = "Cannot infer GitHub repository from origin remote"
        return result
    branch_url = f"https://api.github.com/repos/{owner_repo}/branches/main"
    protection_url = f"https://api.github.com/repos/{owner_repo}/branches/main/protection"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "codex-governance-setup-doctor"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(branch_url, headers=headers), timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            result["protected"] = bool(data.get("protected"))
    except (OSError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        result["branch_error"] = str(exc)
    if not token:
        result["protection_error"] = "UNVERIFIED: GITHUB_TOKEN or GH_TOKEN is required to read branch protection details"
        return result
    try:
        with urllib.request.urlopen(urllib.request.Request(protection_url, headers=headers), timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            checks = data.get("required_status_checks")
            result["required_status_checks"] = checks if checks else "NOT_CONFIGURED"
            result["no_bypass"] = "UNVERIFIED: ruleset bypass actors require authenticated ruleset inspection"
    except urllib.error.HTTPError as exc:
        result["protection_error"] = f"HTTP {exc.code}: {exc.reason}"
    except (OSError, json.JSONDecodeError) as exc:
        result["protection_error"] = str(exc)
    return result


def build_report(check_github: bool) -> dict[str, Any]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    owner_repo = repo_full_name()
    report = {
        "status": "PASS",
        "repository": owner_repo,
        "commit": git_output("rev-parse", "HEAD"),
        "hook": hook_status(),
        "branch_protection": github_branch_status(owner_repo, token) if check_github else {
            "repository": owner_repo,
            "branch": "main",
            "protected": "UNVERIFIED",
            "required_status_checks": "UNVERIFIED",
            "no_bypass": "UNVERIFIED",
            "note": "Run with --check-github and GITHUB_TOKEN/GH_TOKEN for authenticated branch protection details.",
        },
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--check-github", action="store_true", help="Attempt GitHub branch protection checks.")
    args = parser.parse_args(argv)
    report = build_report(args.check_github)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"repository: {report['repository']}")
        print(f"hook.trust_status: {report['hook']['trust_status']}")
        print(f"branch.required_status_checks: {report['branch_protection']['required_status_checks']}")
        print(f"branch.no_bypass: {report['branch_protection']['no_bypass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
