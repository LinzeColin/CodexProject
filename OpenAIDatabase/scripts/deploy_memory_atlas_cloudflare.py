#!/usr/bin/env python3
"""Authorized Cloudflare Pages deploy helper for Memory Atlas.

Default mode is dry-run. The script will not write to Cloudflare unless both
`--execute` and the exact local authorization environment variable are present.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_memory_atlas_goal_completion import current_git_commit  # noqa: E402


AUTH_ENV = "MEMORY_ATLAS_CLOUDFLARE_AUTHORIZED"
AUTH_VALUE = "I_AUTHORIZE_THIS_DEPLOY"
LOCAL_RUNTIME_ENV = "MEMORY_ATLAS_LOCAL_RUNTIME_CANDIDATE"
PROJECT_NAME = "openai-memory-atlas"
PUBLISH_DIR = Path("apps/memory-atlas/dist")
PUBLISH_DIR_ARG = PUBLISH_DIR.as_posix()


class DeploymentError(RuntimeError):
    pass


def run_command(command: list[str], repo_root: Path, execute: bool) -> dict[str, Any]:
    if not execute:
        return {"command": command, "status": "DRY_RUN"}
    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
    return {
        "command": command,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def assert_authorized(args: argparse.Namespace) -> None:
    if not args.execute:
        return
    if os.environ.get(AUTH_ENV) != AUTH_VALUE:
        raise DeploymentError(
            f"missing explicit local authorization: export {AUTH_ENV}={AUTH_VALUE!r} before --execute"
        )
    required_env = [
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_API_TOKEN",
        "MEMORY_ATLAS_ACCESS_HOSTNAME",
        "MEMORY_ATLAS_ALLOWED_EMAIL",
        LOCAL_RUNTIME_ENV,
    ]
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        raise DeploymentError(f"missing live deployment env vars: {missing}")


def parse_deployment_url(output: str) -> str:
    candidates = re.findall(r"https://[A-Za-z0-9_.-]+\.pages\.dev[^\s]*", output)
    return candidates[0].rstrip(".,)") if candidates else ""


def portable_output_path(path: Path | None, repo_root: Path) -> str:
    if path is None:
        return ""
    candidate = path.expanduser()
    if not candidate.is_absolute():
        return candidate.as_posix()
    try:
        return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return f"<external>/{candidate.name}"


def sanitized_evidence(args: argparse.Namespace, repo_root: Path, deployment_url: str) -> dict[str, Any]:
    if not args.write_evidence:
        return {}
    if not args.evidence_out:
        raise DeploymentError("cannot write evidence without --evidence-out")
    if not deployment_url:
        raise DeploymentError("cannot write evidence without a deployment URL")
    verification_flags = {
        "access_challenge_verified": args.access_challenge_verified,
        "allowed_user_app_load_verified": args.allowed_user_app_load_verified,
        "memory_atlas_json_fetch_verified": args.memory_atlas_json_fetch_verified,
        "published_artifact_audited": args.published_artifact_audited,
        "no_raw_sensitive_artifacts_verified": args.no_raw_sensitive_artifacts_verified,
    }
    not_verified = [name for name, value in verification_flags.items() if value is not True]
    if not_verified:
        raise DeploymentError(f"refusing to write completion evidence; verification flags missing: {not_verified}")
    return {
        "schema_version": "memory_atlas.cloudflare_live_evidence.v1",
        "deployment_url": deployment_url,
        "git_commit": current_git_commit(repo_root),
        "cloudflare_pages_project": PROJECT_NAME,
        "access_hostname": os.environ.get("MEMORY_ATLAS_ACCESS_HOSTNAME", args.access_hostname),
        "allowed_email": os.environ.get("MEMORY_ATLAS_ALLOWED_EMAIL", args.allowed_email),
        "verified_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "operator": args.operator,
        **verification_flags,
        "notes": "Sanitized operator evidence only. No Cloudflare tokens, account IDs, cookies, sessions, or private keys.",
    }


def deploy(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve()
    assert_authorized(args)
    commands = [
        ["python3", "scripts/materialize_memory_atlas_release.py", "verify", "--database-dir", "."],
        ["npm", "ci", "--prefix", "apps/memory-atlas"],
        ["npm", "run", "build", "--prefix", "apps/memory-atlas"],
        [
            "python3",
            "scripts/audit_memory_atlas_snapshot_parity.py",
            "--database-dir",
            ".",
            "--local-runtime-env",
            LOCAL_RUNTIME_ENV,
            "--pages-candidate",
            f"{PUBLISH_DIR_ARG}/memory_atlas.json",
        ],
        ["python3", "scripts/audit_memory_atlas_release.py", "--publish-dir", PUBLISH_DIR_ARG],
        ["python3", "scripts/audit_memory_atlas_visual_acceptance.py"],
        ["python3", "scripts/audit_memory_atlas_acceptance.py", "--publish-dir", PUBLISH_DIR_ARG],
        ["python3", "scripts/preflight_cloudflare_pages_access.py", "--publish-dir", PUBLISH_DIR_ARG, "--require-live-env"],
        ["npx", "wrangler", "pages", "deploy", PUBLISH_DIR_ARG, "--project-name", PROJECT_NAME],
    ]

    results: list[dict[str, Any]] = []
    deployment_output = ""
    for command in commands:
        result = run_command(command, repo_root, args.execute)
        results.append(result)
        if result["status"] == "FAIL":
            raise DeploymentError(json.dumps({"status": "FAIL", "failed_command": result}, ensure_ascii=False, indent=2))
        if args.execute and command[:4] == ["npx", "wrangler", "pages", "deploy"]:
            deployment_output = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"

    deployment_url = args.deployment_url or parse_deployment_url(deployment_output)
    evidence = sanitized_evidence(args, repo_root, deployment_url)
    if evidence and args.evidence_out:
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "DRY_RUN" if not args.execute else "DEPLOY_COMMANDS_COMPLETED",
        "authorization_required_for_execute": f"export {AUTH_ENV}={AUTH_VALUE!r}",
        "project_name": PROJECT_NAME,
        "publish_dir": PUBLISH_DIR_ARG,
        "commands": results,
        "deployment_url": deployment_url,
        "evidence_out": portable_output_path(args.evidence_out, repo_root),
        "evidence_ready": bool(evidence),
        "next_required_manual_verification": [
            "Open protected hostname before authentication and confirm Cloudflare Access challenge.",
            "Authenticate as allowed user and confirm app loads.",
            "Confirm /memory_atlas.json fetch works.",
            "Confirm no raw exports, SQLite/JSONL memory, local keys, cookies, sessions, auth files, or plaintext secrets are published.",
            "Run audit_memory_atlas_goal_completion.py with --live-evidence and --require-complete.",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or execute authorized Memory Atlas Cloudflare Pages deployment.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--execute", action="store_true", help="Actually run build, audits, preflight, and wrangler deploy.")
    parser.add_argument("--deployment-url", default="", help="Deployment URL to use when writing evidence if Wrangler output parsing is unavailable.")
    parser.add_argument("--write-evidence", action="store_true", help="Write sanitized live evidence after manual verification flags are provided.")
    parser.add_argument("--evidence-out", type=Path, help="Path for sanitized live evidence JSON. Do not place secrets here.")
    parser.add_argument("--operator", default="authorized operator")
    parser.add_argument("--access-hostname", default="")
    parser.add_argument("--allowed-email", default="")
    parser.add_argument("--access-challenge-verified", action="store_true")
    parser.add_argument("--allowed-user-app-load-verified", action="store_true")
    parser.add_argument("--memory-atlas-json-fetch-verified", action="store_true")
    parser.add_argument("--published-artifact-audited", action="store_true")
    parser.add_argument("--no-raw-sensitive-artifacts-verified", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = deploy(args)
    except DeploymentError as exc:
        print(exc)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
