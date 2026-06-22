"""Manual GitHub workflow validator for trial start evidence collection."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .production_preflight import PRODUCTION_SECRET_ENV_KEYS


TRIAL_START_WORKFLOW_VALIDATOR_ID = "adp-trial-start-workflow-v1"
TRIAL_START_WORKFLOW = ".github/workflows/arxiv-daily-push-trial-start.yml"
TRIAL_START_WORKFLOW_RUNBOOK = "arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md"
REQUIRED_START_WORKFLOW_ARTIFACTS = (
    "adp-trial-start-preflight",
    "adp-trial-start-production-refs",
    "adp-trial-start-launch-readiness",
    "adp-trial-start-bootstrap-plan",
    "adp-trial-start-scheduler-plan",
    "adp-trial-start-all-arxiv-daily-input",
    "adp-trial-start-phase12-artifacts",
    "adp-trial-start-candidate-queue",
    "adp-trial-start-mp4-video",
    "adp-trial-start-smtp-delivery",
    "adp-trial-start-release-delivery",
    "adp-trial-start-gate",
)
REQUIRED_START_WORKFLOW_VARS = (
    "ADP_RELEASE_TARGET",
    "ADP_ARXIV_MAX_RESULTS_PER_CATEGORY",
    "ADP_CANDIDATE_QUEUE_INPUT_PATH",
    "ADP_RECENT_SOURCE_IDS",
    "ADP_ALLOW_SMTP_SEND",
    "ADP_ALLOW_RELEASE_UPLOAD",
)


def build_trial_start_workflow_plan(path: Path | str | None = None, *, generated_at: str) -> dict[str, Any]:
    root = Path(path or ".").resolve()
    workflow_path = root / TRIAL_START_WORKFLOW
    runbook_path = root / TRIAL_START_WORKFLOW_RUNBOOK
    workflow_text = _read_text(workflow_path)
    runbook_text = _read_text(runbook_path)
    checks = [
        _check("workflow_file_exists", workflow_path.is_file(), f"{TRIAL_START_WORKFLOW} is missing"),
        _check("runbook_file_exists", runbook_path.is_file(), f"{TRIAL_START_WORKFLOW_RUNBOOK} is missing"),
        _check(
            "workflow_dispatch_only",
            "workflow_dispatch" in workflow_text and "schedule:" not in workflow_text,
            "trial start workflow must be manual-only",
        ),
        _check(
            "manual_confirmation_required",
            "confirm_trial_start" in workflow_text and "confirm_trial_start == 'true'" in workflow_text,
            "workflow must require confirm_trial_start before starting cloud runner work",
        ),
        _check(
            "github_hosted_runner_targeted",
            "runs-on: ubuntu-latest" in workflow_text and "self-hosted" not in workflow_text,
            "workflow must target GitHub-hosted ubuntu-latest instead of a self-hosted runner",
        ),
        _check(
            "preflight_before_source_and_delivery",
            _appears_before(workflow_text, "preflight-production", "Build all-arXiv trial input")
            and _appears_before(workflow_text, "Stop if preflight blocked", "Run SMTP delivery probe")
            and _appears_before(workflow_text, "Stop if preflight blocked", "Run Release delivery probe"),
            "workflow must run and pass preflight before source, SMTP, or Release probes",
        ),
        _check(
            "production_refs_before_source_and_delivery",
            _appears_before(workflow_text, "plan-production-refs", "Build all-arXiv trial input")
            and _appears_before(workflow_text, "Stop if production refs blocked", "Run SMTP delivery probe")
            and _appears_before(workflow_text, "Stop if production refs blocked", "Run Release delivery probe"),
            "workflow must discover production refs before source, SMTP, or Release probes",
        ),
        _check(
            "launch_readiness_before_source_and_delivery",
            _appears_before(workflow_text, "plan-production-launch", "Build all-arXiv trial input")
            and _appears_before(workflow_text, "--production-refs-report", "Build all-arXiv trial input")
            and _appears_before(workflow_text, "Stop if launch readiness blocked", "Run SMTP delivery probe")
            and _appears_before(workflow_text, "Stop if launch readiness blocked", "Run Release delivery probe"),
            "workflow must pass launch readiness before source, SMTP, or Release probes",
        ),
        _check(
            "source_before_delivery",
            _appears_before(workflow_text, "build-all-arxiv-daily-input", "Run SMTP delivery probe")
            and _appears_before(workflow_text, "Stop if source ingest blocked", "Run Release delivery probe"),
            "workflow must pass all-arXiv Phase 12 source input before SMTP or Release probes",
        ),
        _check(
            "real_mp4_before_delivery",
            _appears_before(workflow_text, "render-lightweight-mp4", "Run Release delivery probe")
            and _appears_before(workflow_text, "Stop if MP4 render blocked", "Run SMTP delivery probe")
            and "adp-trial-start-mp4-video" in workflow_text
            and ".mp4" in workflow_text,
            "workflow must render and upload a real MP4 before SMTP or Release probes",
        ),
        _check(
            "legacy_cs_ai_default_absent",
            "cat:cs.AI" not in workflow_text and "ADP_ARXIV_QUERY" not in workflow_text,
            "trial start workflow must not default to the legacy cs.AI-only scan",
        ),
        _check(
            "trial_start_gate_invoked",
            "plan-trial-start" in workflow_text and "--confirm-start" in workflow_text,
            "workflow must invoke plan-trial-start with explicit confirmation",
        ),
        _check(
            "artifacts_uploaded",
            all(name in workflow_text for name in REQUIRED_START_WORKFLOW_ARTIFACTS)
            and workflow_text.count("actions/upload-artifact") >= len(REQUIRED_START_WORKFLOW_ARTIFACTS),
            "workflow must upload all trial start evidence artifacts",
        ),
        _check(
            "secret_names_only",
            all(f"secrets.{key}" in workflow_text for key in PRODUCTION_SECRET_ENV_KEYS if key.startswith("ADP_SMTP_"))
            and "auth.json" not in workflow_text,
            "workflow must map SMTP secret names without reading Codex auth",
        ),
        _check(
            "controlled_side_effect_enablement",
            "vars.ADP_ALLOW_SMTP_SEND" in workflow_text
            and "vars.ADP_ALLOW_RELEASE_UPLOAD" in workflow_text
            and "--allow-send" in workflow_text
            and "--allow-upload" in workflow_text,
            "workflow must expose SMTP and Release probes only through explicit GitHub variable gates",
        ),
        _check(
            "release_write_permission_declared",
            "contents: write" in workflow_text,
            "workflow must declare contents: write so controlled Release probes can create draft Releases",
        ),
        _check(
            "release_target_declared",
            "vars.ADP_RELEASE_TARGET" in workflow_text,
            "workflow must map Release target through GitHub variables",
        ),
        _check(
            "durable_refs_declared",
            all(
                token in workflow_text
                for token in (
                    "--default-branch-ref",
                    "--runner-ref",
                    "--preflight-ref",
                    "--source-ingest-ref",
                    "--smtp-ref",
                    "--release-ref",
                    "--scheduler-ref",
                    "--trial-state-ref",
                    "--trial-start-ref",
                )
            ),
            "workflow must pass every durable ref required by plan-trial-start",
        ),
        _check(
            "runbook_documents_workflow",
            "arxiv-daily-push-trial-start" in runbook_text
            and "adp-trial-start-gate" in runbook_text
            and "confirm_trial_start" in runbook_text,
            "runbook must document trial start workflow dispatch and artifacts",
        ),
    ]
    ready = all(check["passed"] for check in checks)
    return {
        "plan_id": "trial-start-workflow:arxiv-daily-push",
        "validator_id": TRIAL_START_WORKFLOW_VALIDATOR_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "trial_start_workflow_ready": ready,
        "workflow_path": TRIAL_START_WORKFLOW,
        "runbook_path": TRIAL_START_WORKFLOW_RUNBOOK,
        "required_artifacts": list(REQUIRED_START_WORKFLOW_ARTIFACTS),
        "required_github_secrets": [key for key in PRODUCTION_SECRET_ENV_KEYS if key.startswith("ADP_SMTP_")],
        "required_github_vars": list(REQUIRED_START_WORKFLOW_VARS),
        "manual_only": True,
        "default_side_effects_enabled": False,
        "requires_explicit_smtp_var": True,
        "requires_explicit_release_var": True,
        "required_github_permissions": ["actions: read", "contents: write"],
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
            "merge the workflow to the default branch",
            "use GitHub-hosted ubuntu-latest and configure required GitHub secrets",
            "run production refs discovery and launch readiness precheck on the default branch",
            "set ADP_ALLOW_SMTP_SEND and ADP_ALLOW_RELEASE_UPLOAD only for a controlled start probe",
            "run workflow_dispatch with confirm_trial_start=true and archive adp-trial-start-gate",
        ],
    }


def validate_trial_start_workflow_plan(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("validator_id") != TRIAL_START_WORKFLOW_VALIDATOR_ID:
        errors.append("trial start workflow validator_id must be adp-trial-start-workflow-v1")
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("trial start workflow checks must be a non-empty list")
        return errors
    ready = bool(plan.get("trial_start_workflow_ready"))
    failed = [
        str(check.get("check_id"))
        for check in checks
        if isinstance(check, Mapping) and check.get("passed") is not True
    ]
    if ready and failed:
        errors.append("trial_start_workflow_ready cannot be true with failed checks: " + ", ".join(failed))
    if ready and plan.get("blocking_reasons"):
        errors.append("trial_start_workflow_ready cannot be true with blocking_reasons")
    if not ready and not plan.get("blocking_reasons"):
        errors.append("blocked trial start workflow plan must include blocking_reasons")
    for key in ("manual_only", "requires_explicit_smtp_var", "requires_explicit_release_var"):
        if plan.get(key) is not True:
            errors.append(f"{key} must be true for trial start workflow")
    for key in ("default_side_effects_enabled", "secret_values_logged", "codex_auth_read"):
        if plan.get(key) is not False:
            errors.append(f"{key} must be false for trial start workflow")
    artifacts = plan.get("required_artifacts")
    if not isinstance(artifacts, list) or set(artifacts) != set(REQUIRED_START_WORKFLOW_ARTIFACTS):
        errors.append("trial start workflow required_artifacts must match the expected artifact set")
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
