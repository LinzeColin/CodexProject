"""Fail-closed scheduled production workflow contract validator."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


PRODUCTION_SCHEDULER_VALIDATOR_ID = "adp-production-scheduler-v1"
PRODUCTION_SCHEDULER_WORKFLOW = ".github/workflows/arxiv-daily-push-scheduled.yml"
PRODUCTION_SCHEDULER_RUNBOOK = "arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md"
SCHEDULER_TIMEZONE = "Australia/Sydney"
REQUIRED_SCHEDULES = (
    {"mode": "health-check", "local_time": "04:45", "cron": "45 4 * * *"},
    {"mode": "daily-run", "local_time": "05:00", "cron": "0 5 * * *"},
    {"mode": "watchdog", "local_time": "05:10", "cron": "10 5 * * *"},
)
REQUIRED_SCHEDULER_SECRETS = ("ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD")
REQUIRED_SCHEDULER_VARS = (
    "ADP_PRODUCTION_ENABLED",
    "ADP_SCHEDULED_RUN_ENABLED",
    "ADP_DAILY_INPUT_PATH",
    "ADP_ARXIV_MAX_RESULTS_PER_CATEGORY",
    "ADP_CANDIDATE_QUEUE_INPUT_PATH",
    "ADP_RECENT_SOURCE_IDS",
    "ADP_TRIAL_EVIDENCE_INPUT_PATH",
    "ADP_TRIAL_ID",
    "ADP_TRIAL_REF",
    "ADP_TEXT_DEGRADATION_VERIFIED",
    "ADP_ALLOW_SMTP_SEND",
)


def build_production_scheduler_plan(path: Path | str | None = None, *, generated_at: str) -> dict[str, Any]:
    root = Path(path or ".").resolve()
    workflow_path = root / PRODUCTION_SCHEDULER_WORKFLOW
    runbook_path = root / PRODUCTION_SCHEDULER_RUNBOOK
    workflow_text = _read_text(workflow_path)
    runbook_text = _read_text(runbook_path)
    checks = [
        _check("workflow_file_exists", workflow_path.is_file(), f"{PRODUCTION_SCHEDULER_WORKFLOW} is missing"),
        _check("runbook_file_exists", runbook_path.is_file(), f"{PRODUCTION_SCHEDULER_RUNBOOK} is missing"),
        _check(
            "timezone_schedule_declared",
            all(_has_schedule(workflow_text, item["cron"], SCHEDULER_TIMEZONE) for item in REQUIRED_SCHEDULES),
            "workflow must declare 04:45, 05:00, and 05:10 Australia/Sydney schedules",
        ),
        _check(
            "manual_rerun_supported",
            "workflow_dispatch" in workflow_text and "confirm_scheduled_production" in workflow_text,
            "workflow must support manual rerun with explicit confirmation",
        ),
        _check(
            "production_enabled_gate",
            "vars.ADP_PRODUCTION_ENABLED" in workflow_text and "should_run=\"false\"" in workflow_text,
            "scheduled workflow must skip by default unless ADP_PRODUCTION_ENABLED is true",
        ),
        _check(
            "github_hosted_runner_targeted",
            "runs-on: ubuntu-latest" in workflow_text and "self-hosted" not in workflow_text,
            "scheduled production work must target GitHub-hosted ubuntu-latest instead of a self-hosted runner",
        ),
        _check(
            "preflight_before_scheduled_mode",
            _appears_before(workflow_text, "preflight-production", "Run scheduled mode"),
            "production preflight must run before any scheduled mode work",
        ),
        _check(
            "preflight_artifact_uploaded",
            "adp-scheduled-preflight" in workflow_text and "actions/upload-artifact" in workflow_text,
            "workflow must upload scheduled preflight evidence",
        ),
        _check(
            "scheduled_execution_driver_present",
            "run-scheduled-production" in workflow_text and "adp-scheduled-execution" in workflow_text,
            "workflow must invoke the scheduled execution driver and upload execution evidence",
        ),
        _check(
            "daily_input_builder_present",
            "build-all-arxiv-daily-input" in workflow_text
            and "adp-phase12-delivery-artifacts" in workflow_text
            and "adp-candidate-queue" in workflow_text
            and "adp-scheduled-daily-input" in workflow_text,
            "workflow must build and upload all-arXiv Phase 12 daily input, delivery artifacts, and queue evidence when no override path is configured",
        ),
        _check(
            "stage1_text_delivery_present",
            "build-all-arxiv-daily-input" in workflow_text
            and "adp-phase12-delivery-artifacts" in workflow_text
            and "adp-text-delivery-policy.json" in workflow_text
            and "render-lightweight-mp4" not in workflow_text
            and "adp-scheduled-mp4-video" not in workflow_text
            and ".mp4" not in workflow_text,
            "workflow must build Stage 1 text delivery artifacts without MP4 rendering",
        ),
        _check(
            "candidate_queue_persistence_present",
            "Resolve candidate queue state" in workflow_text
            and "ADP_CANDIDATE_QUEUE_INPUT_PATH" in workflow_text
            and "gh run download" in workflow_text
            and "adp-candidate-queue" in workflow_text,
            "workflow must restore and persist candidate queue state across scheduled daily runs",
        ),
        _check(
            "legacy_cs_ai_default_absent",
            "cat:cs.AI" not in workflow_text and "ADP_ARXIV_QUERY" not in workflow_text,
            "scheduled production workflow must not default to the legacy cs.AI-only scan",
        ),
        _check(
            "trial_ledger_update_present",
            "update-trial-ledger" in workflow_text and "adp-trial-ledger-update" in workflow_text,
            "workflow must build and upload a trial ledger update artifact after daily-run evidence",
        ),
        _check(
            "trial_ledger_state_persistence_present",
            "export-trial-ledger-state" in workflow_text
            and "adp-trial-evidence-ledger" in workflow_text
            and "gh run download" in workflow_text
            and "actions: read" in workflow_text,
            "workflow must restore and upload trial evidence ledger state across scheduled runs",
        ),
        _check(
            "secret_names_only",
            all(f"secrets.{key}" in workflow_text for key in REQUIRED_SCHEDULER_SECRETS)
            and "auth.json" not in workflow_text,
            "workflow must map required secret names without reading Codex auth",
        ),
        _check(
            "release_upload_not_required",
            "ADP_RELEASE_TARGET" not in workflow_text and "ADP_ALLOW_RELEASE_UPLOAD" not in workflow_text,
            "Stage 1 scheduled workflow must not require GitHub Release variables",
        ),
        _check(
            "read_only_contents_permission_declared",
            "contents: read" in workflow_text and "contents: write" not in workflow_text,
            "Stage 1 scheduled workflow must keep contents permission read-only",
        ),
        _check(
            "scheduled_side_effects_disabled",
            "--allow-send" not in workflow_text
            and "--allow-upload" not in workflow_text
            and "gh release create" not in workflow_text
            and "gh release upload" not in workflow_text,
            "scheduler gate must not send SMTP or upload Releases before controlled enablement",
        ),
        _check(
            "runbook_documents_schedule",
            "arxiv-daily-push-scheduled" in runbook_text
            and "04:45" in runbook_text
            and "05:00" in runbook_text
            and "05:10" in runbook_text,
            "runbook must document the scheduled workflow, health check, daily run, and watchdog",
        ),
    ]
    ready = all(check["passed"] for check in checks)
    return {
        "plan_id": "production-scheduler:arxiv-daily-push",
        "validator_id": PRODUCTION_SCHEDULER_VALIDATOR_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "scheduler_contract_ready": ready,
        "workflow_path": PRODUCTION_SCHEDULER_WORKFLOW,
        "runbook_path": PRODUCTION_SCHEDULER_RUNBOOK,
        "timezone": SCHEDULER_TIMEZONE,
        "schedule_slots": list(REQUIRED_SCHEDULES),
        "required_github_secrets": list(REQUIRED_SCHEDULER_SECRETS),
        "required_github_vars": list(REQUIRED_SCHEDULER_VARS),
        "required_github_permissions": ["actions: read", "contents: read"],
        "scheduled_production_enabled": False,
        "scheduled_run_enabled": False,
        "release_upload_enabled": False,
        "real_smtp_send_enabled": False,
        "side_effect_enablement_vars": ["ADP_ALLOW_SMTP_SEND"],
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
            "merge the workflow to the default branch before schedule triggers can run",
            "configure ADP_PRODUCTION_ENABLED only after all-arXiv Phase 12 scan, queue, ROI ranking, SMTP and GitHub-hosted runner prerequisites pass",
            "configure ADP_SCHEDULED_RUN_ENABLED only after daily all-arXiv execution evidence is implemented and verified",
            "retain adp-trial-evidence-ledger artifacts so 30-day trial evidence can accumulate across runs",
            "keep SMTP sending disabled until its explicit production enablement phase",
        ],
    }


def validate_production_scheduler_plan(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("validator_id") != PRODUCTION_SCHEDULER_VALIDATOR_ID:
        errors.append("production scheduler validator_id must be adp-production-scheduler-v1")
    slots = plan.get("schedule_slots")
    if not isinstance(slots, list) or len(slots) != len(REQUIRED_SCHEDULES):
        errors.append("production scheduler must include the required schedule slots")
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("production scheduler checks must be a non-empty list")
        return errors
    ready = bool(plan.get("scheduler_contract_ready"))
    failed = [
        str(check.get("check_id"))
        for check in checks
        if isinstance(check, Mapping) and check.get("passed") is not True
    ]
    if ready and failed:
        errors.append("scheduler_contract_ready cannot be true with failed checks: " + ", ".join(failed))
    if ready and plan.get("blocking_reasons"):
        errors.append("scheduler_contract_ready cannot be true with blocking_reasons")
    if not ready and not plan.get("blocking_reasons"):
        errors.append("blocked production scheduler plan must include blocking_reasons")
    for key in (
        "scheduled_production_enabled",
        "scheduled_run_enabled",
        "release_upload_enabled",
        "real_smtp_send_enabled",
        "secret_values_logged",
        "codex_auth_read",
    ):
        if plan.get(key) is not False:
            errors.append(f"{key} must be false for scheduler gate planning")
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


def _has_schedule(text: str, cron: str, timezone: str) -> bool:
    pattern = rf"cron:\s*[\"']{re.escape(cron)}[\"'][\s\S]{{0,120}}timezone:\s*[\"']{re.escape(timezone)}[\"']"
    return re.search(pattern, text) is not None


def _appears_before(text: str, first: str, second: str) -> bool:
    first_index = text.find(first)
    second_index = text.find(second)
    return first_index >= 0 and second_index >= 0 and first_index < second_index
