"""Manual production trial bootstrap workflow validator."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


TRIAL_BOOTSTRAP_PLAN_ID = "adp-trial-bootstrap-v1"
TRIAL_BOOTSTRAP_WORKFLOW = ".github/workflows/arxiv-daily-push-production-trial.yml"
TRIAL_BOOTSTRAP_RUNBOOK = "arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md"
REQUIRED_BOOTSTRAP_SECRETS = ("ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD")
REQUIRED_BOOTSTRAP_VARS = ("ADP_RELEASE_TARGET",)


def build_trial_bootstrap_plan(path: Path | str | None = None, *, generated_at: str) -> dict[str, Any]:
    root = Path(path or ".").resolve()
    workflow_path = root / TRIAL_BOOTSTRAP_WORKFLOW
    runbook_path = root / TRIAL_BOOTSTRAP_RUNBOOK
    workflow_text = _read_text(workflow_path)
    runbook_text = _read_text(runbook_path)

    checks = [
        _check("workflow_file_exists", workflow_path.is_file(), f"{TRIAL_BOOTSTRAP_WORKFLOW} is missing"),
        _check("runbook_file_exists", runbook_path.is_file(), f"{TRIAL_BOOTSTRAP_RUNBOOK} is missing"),
        _check(
            "workflow_dispatch_only",
            "workflow_dispatch" in workflow_text and not re.search(r"^\s+schedule:", workflow_text, re.MULTILINE),
            "bootstrap workflow must be manual-only until production prerequisites pass",
        ),
        _check(
            "manual_confirmation_required",
            "confirm_production_trial" in workflow_text and "== 'true'" in workflow_text,
            "workflow must require explicit confirm_production_trial input before running on self-hosted runner",
        ),
        _check(
            "self_hosted_runner_targeted",
            "self-hosted" in workflow_text and "runner_label" in workflow_text,
            "workflow must target a private self-hosted runner label",
        ),
        _check(
            "preflight_first",
            _appears_before(workflow_text, "preflight-production", "Run project tests after preflight"),
            "production preflight must run before project tests or trial work",
        ),
        _check(
            "preflight_artifact_uploaded",
            "adp-production-preflight" in workflow_text and "actions/upload-artifact" in workflow_text,
            "workflow must upload the preflight JSON artifact",
        ),
        _check(
            "secret_names_only",
            all(f"secrets.{key}" in workflow_text for key in REQUIRED_BOOTSTRAP_SECRETS)
            and "auth.json" not in workflow_text,
            "workflow must map required secret names without reading Codex auth",
        ),
        _check(
            "release_target_declared",
            all(f"vars.{key}" in workflow_text for key in REQUIRED_BOOTSTRAP_VARS),
            "workflow must map release target through GitHub variables",
        ),
        _check(
            "no_release_or_smtp_side_effect",
            "gh release upload" not in workflow_text and "sendmail" not in workflow_text and "smtp://" not in workflow_text,
            "bootstrap must not upload Releases or send SMTP email",
        ),
        _check(
            "runbook_documents_30_day_path",
            "30-day" in runbook_text and "evaluate-trial" in runbook_text and "linzezhang35@gmail.com" in runbook_text,
            "runbook must document 30-day evidence, trial evaluation, and notification recipient",
        ),
    ]
    ready = all(check["passed"] for check in checks)
    return {
        "plan_id": "trial-bootstrap:arxiv-daily-push",
        "validator_id": TRIAL_BOOTSTRAP_PLAN_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "trial_bootstrap_ready": ready,
        "workflow_path": TRIAL_BOOTSTRAP_WORKFLOW,
        "runbook_path": TRIAL_BOOTSTRAP_RUNBOOK,
        "required_github_secrets": list(REQUIRED_BOOTSTRAP_SECRETS),
        "required_github_vars": list(REQUIRED_BOOTSTRAP_VARS),
        "manual_only_until_confirmed": True,
        "scheduled_production_enabled": False,
        "release_upload_enabled": False,
        "real_smtp_send_enabled": False,
        "secret_values_logged": False,
        "codex_auth_read": False,
        "checks": checks,
        "blocking_reasons": [
            reason
            for check in checks
            for reason in check["blocking_reasons"]
            if check["passed"] is not True
        ],
        "next_external_actions": [
            "install production commands on the private self-hosted runner",
            "configure GitHub SMTP secrets and Release target variable",
            "run workflow_dispatch with confirm_production_trial=true and mode=preflight-only",
            "start 30-day trial only after production preflight passes",
        ],
    }


def validate_trial_bootstrap_plan(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("validator_id") != TRIAL_BOOTSTRAP_PLAN_ID:
        errors.append("trial bootstrap validator_id must be adp-trial-bootstrap-v1")
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("trial bootstrap checks must be a non-empty list")
        return errors
    ready = bool(plan.get("trial_bootstrap_ready"))
    failed = [
        str(check.get("check_id"))
        for check in checks
        if isinstance(check, Mapping) and check.get("passed") is not True
    ]
    if ready and failed:
        errors.append("trial_bootstrap_ready cannot be true with failed checks: " + ", ".join(failed))
    if ready and plan.get("blocking_reasons"):
        errors.append("trial_bootstrap_ready cannot be true with blocking_reasons")
    if not ready and not plan.get("blocking_reasons"):
        errors.append("blocked trial bootstrap plan must include blocking_reasons")
    for key in ("scheduled_production_enabled", "release_upload_enabled", "real_smtp_send_enabled", "secret_values_logged", "codex_auth_read"):
        if plan.get(key) is not False:
            errors.append(f"{key} must be false for bootstrap planning")
    return errors


def _check(check_id: str, passed: bool, reason: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": bool(passed),
        "blocking_reasons": [] if passed else [reason],
    }


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _appears_before(text: str, first: str, second: str) -> bool:
    first_index = text.find(first)
    second_index = text.find(second)
    return first_index >= 0 and second_index >= 0 and first_index < second_index
