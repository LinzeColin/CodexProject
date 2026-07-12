#!/usr/bin/env python3
"""Offline preflight for Cloudflare Pages + Access Memory Atlas deployment."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_memory_atlas_release import AuditError as ReleaseAuditError  # noqa: E402
from audit_memory_atlas_release import audit_release  # noqa: E402
from memory_atlas_cloudflare_contract import (  # noqa: E402
    DEPLOYMENT_MODE,
    PAGES_DEPLOY_COMMAND,
    PROJECT_NAME,
    PUBLISH_DIR_ARG,
)


DOC_URLS = {
    "cloudflare_pages_direct_upload": "https://developers.cloudflare.com/pages/get-started/direct-upload/",
    "cloudflare_pages_ci_direct_upload": "https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/",
    "cloudflare_pages_configuration": "https://developers.cloudflare.com/pages/functions/wrangler-configuration/",
    "cloudflare_workers_static_assets": "https://developers.cloudflare.com/workers/static-assets/",
    "cloudflare_access_self_hosted": "https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/",
    "cloudflare_access_policies": "https://developers.cloudflare.com/cloudflare-one/access-controls/policies/",
    "wrangler_pages_commands": "https://developers.cloudflare.com/workers/wrangler/commands/pages/",
}

WRANGLER_PAGES_CONFIG = "pages_config"
WRANGLER_WORKERS_MIGRATION_CONFIG = "workers_assets_migration_ready"
WRANGLER_UNSUPPORTED_CONFIG = "unsupported_or_ambiguous"

FORBIDDEN_TEMPLATE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"sk-[A-Za-z0-9_-]{20,}",
        r"-----BEGIN (?:RSA |EC |OPENSSH |PRIVATE )?PRIVATE KEY-----",
        r"/Users/[A-Za-z0-9_.-]+/",
        r"OpenAI-export\.zip\s*:",
        r"chatgpt_memory_vault_codex_pack\.zip\s*:",
    ]
]


class PreflightError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add_check(checks: list[dict[str, str]], name: str, status: str, evidence: str) -> None:
    checks.append({"name": name, "status": status, "evidence": evidence})


def static_output_directory(config: dict[str, Any]) -> str:
    pages_directory = config.get("pages_build_output_dir")
    if isinstance(pages_directory, str) and pages_directory.strip():
        return pages_directory.strip().removeprefix("./")
    assets = config.get("assets")
    assets_directory = assets.get("directory") if isinstance(assets, dict) else None
    if isinstance(assets_directory, str) and assets_directory.strip():
        return assets_directory.strip().removeprefix("./")
    return ""


def wrangler_config_mode(config: dict[str, Any]) -> str:
    pages_directory = config.get("pages_build_output_dir")
    assets = config.get("assets")
    assets_directory = assets.get("directory") if isinstance(assets, dict) else None
    has_pages_config = isinstance(pages_directory, str) and bool(pages_directory.strip())
    has_workers_config = isinstance(assets_directory, str) and bool(assets_directory.strip())
    if has_pages_config == has_workers_config:
        return WRANGLER_UNSUPPORTED_CONFIG
    if has_pages_config:
        return WRANGLER_PAGES_CONFIG
    return WRANGLER_WORKERS_MIGRATION_CONFIG


def require(checks: list[dict[str, str]], name: str, condition: bool, success: str, failure: str) -> None:
    add_check(checks, name, "PASS" if condition else "FAIL", success if condition else failure)


def audit_templates(repo_root: Path, checks: list[dict[str, str]]) -> None:
    pages_template_path = repo_root / "config/cloudflare/pages_direct_upload.template.json"
    access_template_path = repo_root / "config/cloudflare/access_self_hosted_application.template.json"
    require(
        checks,
        "cloudflare_templates_present",
        pages_template_path.exists() and access_template_path.exists(),
        "Pages direct-upload and Access application templates exist",
        "missing config/cloudflare Pages or Access template",
    )
    if not pages_template_path.exists() or not access_template_path.exists():
        return

    pages_template = load_json(pages_template_path)
    access_template = load_json(access_template_path)
    template_text = pages_template_path.read_text(encoding="utf-8") + "\n" + access_template_path.read_text(encoding="utf-8")
    matched = [pattern.pattern for pattern in FORBIDDEN_TEMPLATE_PATTERNS if pattern.search(template_text)]
    require(checks, "cloudflare_templates_no_plaintext_secrets", not matched, "templates contain placeholders only", f"forbidden template patterns: {matched}")
    require(
        checks,
        "cloudflare_pages_template_contract",
        pages_template.get("project_name") == "openai-memory-atlas"
        and pages_template.get("source", {}).get("publish_dir") == "apps/memory-atlas/dist"
        and pages_template.get("deploy", {}).get("requires_explicit_user_authorization") is True
        and pages_template.get("post_deploy", {}).get("access_required") is True,
        "Pages template names project, publish dir, explicit authorization, and Access requirement",
        "Pages template is missing required deployment contract fields",
    )
    policy = access_template.get("policy", {})
    require(
        checks,
        "cloudflare_access_template_contract",
        access_template.get("application", {}).get("type") == "self_hosted_public_hostname"
        and policy.get("action") == "allow"
        and policy.get("deny_by_default") is True
        and "everyone" in policy.get("must_not_use_selectors", []),
        "Access template uses self-hosted public hostname, allowlist policy, and deny-by-default posture",
        "Access template is missing self-hosted allowlist or deny-by-default safety fields",
    )


def audit_docs(repo_root: Path, checks: list[dict[str, str]]) -> None:
    runbook = repo_root / "docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md"
    deployment_doc = repo_root / "docs/MEMORY_ATLAS_DEPLOYMENT.md"
    require(checks, "cloudflare_runbook_present", runbook.exists(), "Cloudflare runbook exists", "missing docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md")
    combined = ""
    if runbook.exists():
        combined += runbook.read_text(encoding="utf-8")
    if deployment_doc.exists():
        combined += "\n" + deployment_doc.read_text(encoding="utf-8")
    missing_urls = [url for url in DOC_URLS.values() if url not in combined]
    require(
        checks,
        "cloudflare_official_docs_linked",
        not missing_urls,
        "runbook links official Cloudflare Pages, Wrangler, and Access docs",
        f"missing official doc URLs: {missing_urls}",
    )
    require(
        checks,
        "cloudflare_manual_authorization_boundary",
        "明确授权" in combined and "wrangler pages deploy" in combined and "Access" in combined,
        "runbook keeps deploy as an explicitly authorized action",
        "runbook does not clearly preserve authorization boundary",
    )


def audit_delivery_mode(
    repo_root: Path,
    wrangler_mode: str,
    checks: list[dict[str, str]],
) -> None:
    expected_command = [
        "npx",
        "wrangler",
        "pages",
        "deploy",
        PUBLISH_DIR_ARG,
        "--project-name",
        PROJECT_NAME,
    ]
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            repo_root / "docs/MEMORY_ATLAS_DEPLOYMENT.md",
            repo_root / "docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md",
        ]
        if path.exists()
    )
    documented = all(
        marker in docs
        for marker in [
            DEPLOYMENT_MODE,
            "Pages Direct Upload",
            "Workers Static Assets",
            "wrangler pages deploy",
            "wrangler deploy",
        ]
    )
    require(
        checks,
        "cloudflare_delivery_mode_contract",
        DEPLOYMENT_MODE == "pages_direct_upload_with_workers_migration_ready_config"
        and wrangler_mode == WRANGLER_WORKERS_MIGRATION_CONFIG
        and PAGES_DEPLOY_COMMAND == expected_command
        and documented,
        "production uses explicit Pages Direct Upload while wrangler.jsonc remains Workers Static Assets migration-ready",
        "deployment helper, wrangler mode, or dual-mode documentation does not match the approved delivery contract",
    )


def audit_wrangler(repo_root: Path, checks: list[dict[str, str]]) -> str:
    config_path = repo_root / "wrangler.jsonc"
    require(checks, "wrangler_config_present", config_path.exists(), "wrangler.jsonc exists", "missing wrangler.jsonc")
    if not config_path.exists():
        return WRANGLER_UNSUPPORTED_CONFIG
    config = load_json(config_path)
    mode = wrangler_config_mode(config)
    require(
        checks,
        "wrangler_static_output_config",
        config.get("name") == "openai-memory-atlas"
        and static_output_directory(config) == "apps/memory-atlas/dist"
        and mode in {WRANGLER_PAGES_CONFIG, WRANGLER_WORKERS_MIGRATION_CONFIG}
        and isinstance(config.get("compatibility_date"), str)
        and bool(config.get("compatibility_date")),
        f"wrangler.jsonc names the Memory Atlas project and static output in {mode} mode",
        "wrangler.jsonc has an unsupported or ambiguous static output mode",
    )
    return mode


def audit_live_env(checks: list[dict[str, str]]) -> None:
    required = [
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_API_TOKEN",
        "MEMORY_ATLAS_ACCESS_HOSTNAME",
        "MEMORY_ATLAS_ALLOWED_EMAIL",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    require(checks, "cloudflare_live_env_present", not missing, "live deploy environment variables are present", f"missing env vars: {missing}")


def preflight(repo_root: Path, publish_dir: Path | None = None, require_live_env: bool = False) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    checks: list[dict[str, str]] = []
    wrangler_mode = audit_wrangler(repo_root, checks)
    audit_delivery_mode(repo_root, wrangler_mode, checks)
    audit_templates(repo_root, checks)
    audit_docs(repo_root, checks)

    if publish_dir is not None:
        try:
            release_result = audit_release(repo_root, publish_dir)
        except ReleaseAuditError as exc:
            add_check(checks, "cloudflare_publish_release_safe", "FAIL", str(exc))
        else:
            add_check(checks, "cloudflare_publish_release_safe", "PASS", f"{release_result['file_count']} publish files audited")
        add_check(checks, "cloudflare_publish_acceptance_safe", "INFO", "run scripts/audit_memory_atlas_acceptance.py with the same publish directory before deploy")

    if require_live_env:
        audit_live_env(checks)
    else:
        add_check(checks, "cloudflare_live_deploy_authorization", "INFO", "live deploy env not required; actual deploy still needs explicit user authorization")

    failed = [check for check in checks if check["status"] == "FAIL"]
    if failed:
        raise PreflightError(
            json.dumps(
                {"status": "FAIL", "deployment_mode": DEPLOYMENT_MODE, "checks": checks},
                ensure_ascii=False,
                indent=2,
            )
        )
    return {
        "status": "PASS",
        "deployment_mode": DEPLOYMENT_MODE,
        "wrangler_config_mode": wrangler_mode,
        "checks": checks,
        "docs": DOC_URLS,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight Cloudflare Pages + Access deployment readiness.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--publish-dir", type=Path)
    parser.add_argument("--require-live-env", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = preflight(args.repo_root, args.publish_dir, args.require_live_env)
    except PreflightError as exc:
        print(exc)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
