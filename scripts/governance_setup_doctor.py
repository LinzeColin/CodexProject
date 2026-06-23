#!/usr/bin/env python3
"""Report local and GitHub governance enforcement setup status."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "project-governance.yml"
BAD_STATUSES = {"FAIL", "NOT_CONFIGURED"}
UNKNOWN_STATUSES = {"UNVERIFIED"}


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
    hooks_text = hooks_json.read_text(encoding="utf-8") if hooks_json.exists() else ""
    hooks_enabled = False
    stop_hook_configured = False
    try:
        hooks_data = json.loads(hooks_text) if hooks_text else {}
        stop_hooks = hooks_data.get("hooks", {}).get("Stop", []) if isinstance(hooks_data, dict) else []
        hooks_enabled = bool(stop_hooks)
        stop_hook_configured = "governance_stop.py" in hooks_text
    except json.JSONDecodeError:
        hooks_enabled = False
        stop_hook_configured = False
    script_executable = hook_script.is_file() and os.access(hook_script, os.R_OK)
    python_ok = sys.version_info >= (3, 11)
    result = {
        "hooks_json_exists": hooks_json.is_file(),
        "governance_stop_exists": hook_script.is_file(),
        "config_template_enables_hooks": False,
        "repository_trusted": "UNVERIFIED",
        "hooks_enabled": "VERIFIED" if hooks_enabled and stop_hook_configured else "UNVERIFIED",
        "stop_hook_loaded": "UNVERIFIED",
        "governance_script_executable": "VERIFIED" if script_executable else "UNVERIFIED",
        "python_environment": "VERIFIED" if python_ok else "UNVERIFIED",
        "trust_status": "UNVERIFIED",
        "notes": [
            "Codex project trust and loaded-hook state are local app settings; this doctor can verify repository hook files but cannot prove the app has trusted or loaded them."
        ],
    }
    if config_template.exists():
        result["config_template_enables_hooks"] = "hooks = true" in config_template.read_text(encoding="utf-8")
    return result


def workflow_entry_gate_status() -> dict[str, Any]:
    text = WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.exists() else ""
    changed_scope_base_ref = (
        "GOVERNANCE_BASE_REF: ${{ github.event_name == 'pull_request' && "
        "github.event.pull_request.base.sha || github.event.before || inputs.base_ref || '' }}"
    )

    checks = {
        "workflow_exists": WORKFLOW.is_file(),
        "pull_request_changed_only_enforce_sync_semantic": (
            "github.event_name == 'pull_request'" in text
            and "--changed-only --enforce-sync --semantic" in text
        ),
        "pull_request_changed_only_uses_pr_base_sha": (
            "github.event_name == 'pull_request'" in text
            and "github.event.pull_request.base.sha" in text
            and changed_scope_base_ref in text
            and "--changed-only --enforce-sync --semantic" in text
        ),
        "main_push_changed_only_uses_event_before": (
            "github.event_name == 'push'" in text
            and changed_scope_base_ref in text
            and "--changed-only --enforce-sync --semantic" in text
        ),
        "pull_request_skips_information_quality": (
            "Validate information quality" in text
            and "github.event_name == 'workflow_dispatch' && inputs.scope == 'changed-only'" in text
        ),
        "full_governance_runs_only_on_schedule_or_manual_all": (
            "github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && inputs.scope == 'all')" in text
            and "--all --semantic --drift-report" in text
            and "github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && inputs.scope == 'all')" not in text
        ),
        "manual_changed_only_accepts_base_ref": (
            "inputs.scope == 'changed-only'" in text
            and "GOVERNANCE_BASE_REF: ${{ inputs.base_ref || '' }}" in text
        ),
        "manual_project_scope_requires_project": (
            "inputs.scope == 'project'" in text
            and "project input is required when scope=project" in text
        ),
        "ci_attestation_validated": (
            "scripts/validate_ci_attestation.py write" in text
            and "scripts/validate_ci_attestation.py validate" in text
            and "github.event_name == 'workflow_dispatch' && inputs.scope == 'all'" in text
        ),
        "ci_attestation_uploaded_as_artifact": (
            "actions/upload-artifact@v4" in text
            and "project-governance-ci-attestation-" in text
            and "if-no-files-found: error" in text
            and "github.event_name == 'workflow_dispatch' && inputs.scope == 'all'" in text
        ),
        "setup_doctor_runs_in_ci": "scripts/governance_setup_doctor.py --json --check-github" in text,
        "generated_assurance_views_checked": "ASSURANCE_STATUS.yaml" in text and "governance/binding_backlog.yaml" in text,
        "required_failures_not_masked": re.search(r"(?m)^\s*continue-on-error\s*:", text) is None,
    }
    missing = sorted(name for name, ok in checks.items() if not ok)
    return {
        "status": "PASS" if not missing else "FAIL",
        "workflow": str(WORKFLOW.relative_to(ROOT)),
        "checks": checks,
        "missing": missing,
    }


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


def is_bad_status(value: Any) -> bool:
    text = str(value).upper()
    return any(status in text for status in BAD_STATUSES)


def is_unknown_status(value: Any) -> bool:
    text = str(value).upper()
    return any(status in text for status in UNKNOWN_STATUSES)


def flatten_statuses(prefix: str, value: Any) -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        items: list[tuple[str, Any]] = []
        for key, child in value.items():
            items.extend(flatten_statuses(f"{prefix}.{key}" if prefix else str(key), child))
        return items
    if isinstance(value, list):
        items = []
        for idx, child in enumerate(value):
            items.extend(flatten_statuses(f"{prefix}[{idx}]", child))
        return items
    if isinstance(value, (str, bool)):
        return [(prefix, value)]
    return []


def evaluate_report(report: dict[str, Any], strict_local: bool, strict_github: bool) -> dict[str, Any]:
    local_paths = {
        "hook.repository_trusted",
        "hook.hooks_enabled",
        "hook.stop_hook_loaded",
        "hook.governance_script_executable",
        "hook.python_environment",
        "hook.trust_status",
        "workflow_entry_gates.status",
    }
    github_paths = {
        "branch_protection.protected",
        "branch_protection.required_status_checks",
        "branch_protection.no_bypass",
    }
    failures: list[str] = []
    warnings: list[str] = []
    for path, value in flatten_statuses("", report):
        if path == "status":
            continue
        in_local = path in local_paths
        in_github = path in github_paths
        strict = (strict_local and in_local) or (strict_github and in_github)
        if is_bad_status(value):
            if strict or path == "workflow_entry_gates.status":
                failures.append(f"{path}={value}")
            else:
                warnings.append(f"{path}={value}")
        elif is_unknown_status(value):
            if strict:
                failures.append(f"{path}={value}")
            else:
                warnings.append(f"{path}={value}")
    status = "FAIL" if failures else "WARN" if warnings else "PASS"
    return {"status": status, "failures": sorted(set(failures)), "warnings": sorted(set(warnings))}


def build_report(check_github: bool, strict_local: bool = False, strict_github: bool = False) -> dict[str, Any]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    owner_repo = repo_full_name()
    report = {
        "repository": owner_repo,
        "commit": git_output("rev-parse", "HEAD"),
        "hook": hook_status(),
        "workflow_entry_gates": workflow_entry_gate_status(),
        "branch_protection": github_branch_status(owner_repo, token) if check_github else {
            "repository": owner_repo,
            "branch": "main",
            "protected": "UNVERIFIED",
            "required_status_checks": "UNVERIFIED",
            "no_bypass": "UNVERIFIED",
            "note": "Run with --check-github and GITHUB_TOKEN/GH_TOKEN for authenticated branch protection details.",
        },
    }
    evaluation = evaluate_report(report, strict_local, strict_github)
    report["status"] = evaluation["status"]
    report["strict_local"] = strict_local
    report["strict_github"] = strict_github
    report["failures"] = evaluation["failures"]
    report["warnings"] = evaluation["warnings"]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--check-github", action="store_true", help="Attempt GitHub branch protection checks.")
    parser.add_argument("--strict-local", action="store_true", help="Fail if local hook trust or entry-gate state is unverified.")
    parser.add_argument("--strict-github", action="store_true", help="Fail if GitHub branch protection/required/no-bypass state is unverified.")
    parser.add_argument("--strict-all", action="store_true", help="Enable both strict local and strict GitHub checks.")
    args = parser.parse_args(argv)
    strict_local = bool(args.strict_local or args.strict_all)
    strict_github = bool(args.strict_github or args.strict_all)
    report = build_report(args.check_github or strict_github, strict_local, strict_github)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"repository: {report['repository']}")
        print(f"hook.trust_status: {report['hook']['trust_status']}")
        print(f"workflow_entry_gates.status: {report['workflow_entry_gates']['status']}")
        print(f"branch.required_status_checks: {report['branch_protection']['required_status_checks']}")
        print(f"branch.no_bypass: {report['branch_protection']['no_bypass']}")
        if report["failures"]:
            print("failures:")
            for item in report["failures"]:
                print(f"- {item}")
        if report["warnings"]:
            print("warnings:")
            for item in report["warnings"]:
                print(f"- {item}")
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
