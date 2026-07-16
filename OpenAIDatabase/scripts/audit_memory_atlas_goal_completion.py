#!/usr/bin/env python3
"""Audit Memory Atlas goal completion without hiding external blockers."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_memory_atlas_acceptance import AcceptanceError, audit_acceptance  # noqa: E402
from memory_atlas_r8_acceptance import (  # noqa: E402
    FINAL_RECORD_PATHS,
    AcceptanceHistoryError,
    audit_final_records,
)
from preflight_cloudflare_pages_access import PreflightError, preflight as cloudflare_preflight  # noqa: E402


class GoalCompletionError(RuntimeError):
    pass


REQUIRED_LIVE_EVIDENCE_FIELDS = {
    "schema_version",
    "deployment_url",
    "git_commit",
    "cloudflare_pages_project",
    "access_hostname",
    "allowed_email",
    "verified_at",
    "operator",
    "access_challenge_verified",
    "allowed_user_app_load_verified",
    "memory_atlas_json_fetch_verified",
    "published_artifact_audited",
    "no_raw_sensitive_artifacts_verified",
}

FORBIDDEN_EVIDENCE_KEYS = {
    "token",
    "api_token",
    "cookie",
    "session",
    "password",
    "secret",
    "private_key",
    "account_id",
}

CANONICAL_LIVE_EVIDENCE_PATH = Path(
    "机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json"
)

POST_DEPLOY_RECORD_PATHS = frozenset(
    {
        "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
        "功能清单.md",
        "开发记录.md",
        "模型参数文件.md",
        CANONICAL_LIVE_EVIDENCE_PATH.as_posix(),
        "机器治理/证据与日志/final_delivery/v1_2_final_delivery_cleanup_status.json",
        *(path.as_posix() for path in FINAL_RECORD_PATHS),
    }
)


def add_check(checks: list[dict[str, str]], name: str, status: str, evidence: str) -> None:
    checks.append({"name": name, "status": status, "evidence": evidence})


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def current_git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def git_output(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate_live_git_commit(repo_root: Path, evidence_path: Path, deployed_commit: str) -> tuple[bool, str]:
    head = current_git_commit(repo_root)
    if not head:
        return False, "could not determine current Git HEAD"
    if deployed_commit == head:
        return True, "live evidence git commit matches current HEAD"

    try:
        parent = git_output(repo_root, "rev-parse", "HEAD^")
    except (OSError, subprocess.CalledProcessError):
        return False, "deployed commit must match current HEAD or its immediate parent"
    if deployed_commit != parent:
        return False, "deployed commit must match current HEAD or its immediate parent"

    try:
        evidence_relative_path = evidence_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return False, "parent-commit evidence must use the canonical repository path"
    if evidence_relative_path != CANONICAL_LIVE_EVIDENCE_PATH.as_posix():
        return False, "parent-commit evidence must use the canonical repository path"

    try:
        changed_paths = {
            path
            for path in git_output(
                repo_root,
                "-c",
                "core.quotePath=false",
                "diff",
                "--name-only",
                "--relative",
                f"{deployed_commit}..HEAD",
                "--",
                ".",
            ).splitlines()
            if path
        }
    except (OSError, subprocess.CalledProcessError):
        return False, "could not inspect the post-deploy evidence commit"

    if evidence_relative_path not in changed_paths:
        return False, "final evidence commit does not contain the canonical evidence file"
    disallowed_paths = sorted(changed_paths.difference(POST_DEPLOY_RECORD_PATHS))
    if disallowed_paths:
        return False, f"post-deploy commit contains non-record paths: {disallowed_paths}"
    return True, "deployed commit is the immediate parent and HEAD only adds final-delivery records"


def collect_json_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        keys = list(value.keys())
        for child in value.values():
            keys.extend(collect_json_keys(child))
        return keys
    if isinstance(value, list):
        keys: list[str] = []
        for child in value:
            keys.extend(collect_json_keys(child))
        return keys
    return []


def audit_live_evidence(repo_root: Path, evidence_path: Path | None, checks: list[dict[str, str]]) -> bool:
    if evidence_path is None:
        add_check(
            checks,
            "cloudflare_live_access_evidence",
            "EXTERNAL_BLOCKED",
            "missing live evidence; explicit Cloudflare deployment and Access verification are still required",
        )
        return False

    if not evidence_path.exists():
        add_check(checks, "cloudflare_live_access_evidence", "FAIL", f"missing evidence file: {evidence_path}")
        return False

    evidence = load_json(evidence_path)
    if not isinstance(evidence, dict):
        add_check(checks, "cloudflare_live_access_evidence", "FAIL", "evidence file must contain a JSON object")
        return False

    missing = sorted(REQUIRED_LIVE_EVIDENCE_FIELDS.difference(evidence))
    if missing:
        add_check(checks, "cloudflare_live_access_evidence", "FAIL", f"missing evidence fields: {missing}")
        return False

    evidence_keys = collect_json_keys(evidence)
    forbidden_present = sorted(
        {
            evidence_key
            for evidence_key in evidence_keys
            for forbidden_key in FORBIDDEN_EVIDENCE_KEYS
            if forbidden_key in evidence_key.lower()
        }
    )
    if forbidden_present:
        add_check(checks, "cloudflare_live_evidence_no_secrets", "FAIL", f"forbidden sensitive evidence keys: {forbidden_present}")
        return False
    add_check(checks, "cloudflare_live_evidence_no_secrets", "PASS", "live evidence file contains no forbidden secret-like keys")

    bool_fields = [
        "access_challenge_verified",
        "allowed_user_app_load_verified",
        "memory_atlas_json_fetch_verified",
        "published_artifact_audited",
        "no_raw_sensitive_artifacts_verified",
    ]
    false_fields = [field for field in bool_fields if evidence.get(field) is not True]
    if false_fields:
        add_check(checks, "cloudflare_live_access_evidence", "FAIL", f"live verification fields are not true: {false_fields}")
        return False

    git_commit_ok, git_commit_evidence = validate_live_git_commit(
        repo_root,
        evidence_path,
        str(evidence.get("git_commit", "")),
    )
    if not git_commit_ok:
        add_check(
            checks,
            "cloudflare_live_git_commit_matches",
            "FAIL",
            git_commit_evidence,
        )
        return False
    add_check(checks, "cloudflare_live_git_commit_matches", "PASS", git_commit_evidence)

    deployment_url = str(evidence.get("deployment_url", ""))
    if not deployment_url.startswith("https://"):
        add_check(checks, "cloudflare_live_access_evidence", "FAIL", "deployment_url must be https")
        return False

    add_check(
        checks,
        "cloudflare_live_access_evidence",
        "PASS",
        "operator evidence says Access challenge, allowed-user load, runtime JSON fetch, and publish artifact safety were verified",
    )
    return True


def audit_goal_completion(
    repo_root: Path,
    publish_dir: Path | None = None,
    require_local_apps: bool = False,
    live_evidence: Path | None = None,
    require_complete: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    checks: list[dict[str, str]] = []
    effective_publish_dir = publish_dir
    if publish_dir is not None:
        resolved_publish_dir = publish_dir if publish_dir.is_absolute() else repo_root / publish_dir
        if not resolved_publish_dir.exists():
            add_check(
                checks,
                "publish_dir_available",
                "FAIL",
                f"publish directory does not exist: {resolved_publish_dir}; build first for artifact audit, or omit --publish-dir after cleanup/local runtime install",
            )
            effective_publish_dir = None

    try:
        acceptance = audit_acceptance(repo_root, effective_publish_dir, require_local_apps)
    except AcceptanceError as exc:
        add_check(checks, "local_acceptance", "FAIL", str(exc))
        acceptance = None
    else:
        add_check(checks, "local_acceptance", "PASS", f"{len(acceptance['checks'])} acceptance checks passed")

    try:
        # audit_acceptance owns the publish artifact release audit. This call
        # verifies the Cloudflare contract without scanning the same artifact again.
        preflight = cloudflare_preflight(repo_root, None, require_live_env=False)
    except PreflightError as exc:
        add_check(checks, "cloudflare_preflight", "FAIL", str(exc))
        preflight = None
    else:
        add_check(checks, "cloudflare_preflight", "PASS", f"{len(preflight['checks'])} Cloudflare preflight checks passed")

    try:
        r8_acceptance = audit_final_records(repo_root)
    except (AcceptanceHistoryError, OSError, json.JSONDecodeError) as exc:
        add_check(checks, "r8_final_acceptance", "INCOMPLETE", str(exc))
        r8_ok = False
    else:
        add_check(
            checks,
            "r8_final_acceptance",
            "PASS",
            f"{r8_acceptance['verified_requirement_count']}/58 requirements and {r8_acceptance['stage_count']} stages verified",
        )
        r8_ok = True

    live_ok = audit_live_evidence(repo_root, live_evidence, checks)
    hard_failures = [check for check in checks if check["status"] == "FAIL"]
    if hard_failures:
        status = "FAIL"
    elif live_ok and r8_ok:
        status = "COMPLETE_WITH_OPERATOR_EVIDENCE"
    else:
        status = "LOCAL_PASS_EXTERNAL_AUTHORIZATION_REQUIRED"

    result = {
        "status": status,
        "checks": checks,
        "completion_rule": "Do not mark the thread goal complete until status is COMPLETE_WITH_OPERATOR_EVIDENCE or a live Cloudflare deployment and Access challenge have been independently verified.",
    }
    if require_complete and status != "COMPLETE_WITH_OPERATOR_EVIDENCE":
        raise GoalCompletionError(json.dumps(result, ensure_ascii=False, indent=2))
    if hard_failures:
        raise GoalCompletionError(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Memory Atlas goal completion state.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--publish-dir", type=Path)
    parser.add_argument("--require-local-apps", action="store_true")
    parser.add_argument("--live-evidence", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = audit_goal_completion(
            args.repo_root,
            publish_dir=args.publish_dir,
            require_local_apps=args.require_local_apps,
            live_evidence=args.live_evidence,
            require_complete=args.require_complete,
        )
    except GoalCompletionError as exc:
        print(exc)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
