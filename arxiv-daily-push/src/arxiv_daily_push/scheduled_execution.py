"""Controlled scheduled production execution driver."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .daily_input import DAILY_INPUT_BUILDER_MODEL_ID, validate_daily_input_report
from .notifications import render_email
from .pipeline import PipelineError, run_daily_dry_run
from .production_preflight import validate_production_preflight
from .release_delivery import (
    DEFAULT_RELEASE_REPO,
    CommandResolver,
    CommandRunner,
    deliver_release,
    validate_release_delivery_report,
)
from .smtp_delivery import SmtpFactory, deliver_notification, validate_smtp_delivery_report


SCHEDULED_EXECUTION_MODEL_ID = "adp-scheduled-execution-v1"
SCHEDULED_EXECUTION_MODES = ("health-check", "daily-run", "watchdog")
SCHEDULED_RUN_ENV_KEY = "ADP_SCHEDULED_RUN_ENABLED"
SMTP_SEND_ENV_KEY = "ADP_ALLOW_SMTP_SEND"
RELEASE_UPLOAD_ENV_KEY = "ADP_ALLOW_RELEASE_UPLOAD"


def run_scheduled_execution(
    *,
    mode: str,
    generated_at: str,
    preflight_report: Mapping[str, Any],
    env: Mapping[str, str] | None = None,
    daily_input: Mapping[str, Any] | None = None,
    daily_input_path: str | Path | None = None,
    release_asset_paths: Sequence[str | Path] | None = None,
    previous_execution_report: Mapping[str, Any] | None = None,
    smtp_factory: SmtpFactory | None = None,
    release_command_resolver: CommandResolver | None = None,
    release_command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Execute one scheduled mode and return auditable evidence.

    The driver never enables real SMTP or Release side effects by default. Real
    side effects require explicit environment keys and still pass through the
    dedicated SMTP/Release validators.
    """

    environment = env if env is not None else os.environ
    normalized_mode = str(mode or "")
    base = _base_report(normalized_mode, generated_at, environment, preflight_report)

    if normalized_mode not in SCHEDULED_EXECUTION_MODES:
        return _blocked(base, [f"scheduled execution mode must be one of: {', '.join(SCHEDULED_EXECUTION_MODES)}"])

    preflight_errors = validate_production_preflight(preflight_report)
    if preflight_errors:
        return _blocked(base, [f"invalid preflight report: {preflight_errors[0]}"])
    if preflight_report.get("production_run_allowed") is not True:
        report = _blocked(base, list(preflight_report.get("blocking_reasons") or ["production preflight blocked"]))
        report["notification_report"] = _notification(
            "failure",
            normalized_mode,
            generated_at,
            "Scheduled production preflight blocked",
            environment,
            smtp_factory=smtp_factory,
        )
        return _with_validation(report)

    if normalized_mode == "health-check":
        report = dict(base)
        report["status"] = "succeeded"
        report["exit_code"] = 0
        report["notification_report"] = _notification(
            "success",
            normalized_mode,
            generated_at,
            "Scheduled health check passed",
            environment,
            smtp_factory=smtp_factory,
        )
        report["evidence_refs"]["resource_gate_ref"] = preflight_report["resource_evidence"]["resource_pressure_ok_ref"]
        return _with_validation(report)

    if normalized_mode == "watchdog":
        return _run_watchdog(
            base,
            generated_at,
            environment,
            previous_execution_report=previous_execution_report,
            smtp_factory=smtp_factory,
        )

    return _run_daily(
        base,
        generated_at,
        environment,
        daily_input=daily_input,
        daily_input_path=daily_input_path,
        release_asset_paths=release_asset_paths,
        smtp_factory=smtp_factory,
        release_command_resolver=release_command_resolver,
        release_command_runner=release_command_runner,
    )


def load_json_mapping(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def validate_scheduled_execution_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("validator_id") != SCHEDULED_EXECUTION_MODEL_ID:
        errors.append("scheduled execution validator_id must be adp-scheduled-execution-v1")
    if report.get("mode") not in SCHEDULED_EXECUTION_MODES:
        errors.append("scheduled execution mode is invalid")
    if report.get("status") not in {"succeeded", "blocked", "failed", "degraded"}:
        errors.append("scheduled execution status must be succeeded, blocked, failed, or degraded")
    if int(report.get("exit_code", 99)) not in {0, 2}:
        errors.append("scheduled execution exit_code must be 0 or 2")
    if report.get("status") == "succeeded" and report.get("exit_code") != 0:
        errors.append("succeeded scheduled execution requires exit_code 0")
    if report.get("status") in {"blocked", "failed", "degraded"} and report.get("exit_code") != 2:
        errors.append("blocked, failed, or degraded scheduled execution requires exit_code 2")
    policy = report.get("side_effect_policy")
    if not isinstance(policy, Mapping):
        errors.append("scheduled execution side_effect_policy is required")
    else:
        if policy.get("secret_values_logged") is not False:
            errors.append("scheduled execution must not log secret values")
        if policy.get("email_body_logged") is not False:
            errors.append("scheduled execution must not log email body text")
        if policy.get("gh_output_logged") is not False:
            errors.append("scheduled execution must not log gh stdout or stderr")
    if report.get("production_evidence_ready") is True:
        refs = report.get("evidence_refs")
        if not isinstance(refs, Mapping):
            errors.append("production evidence ready requires evidence_refs")
        else:
            for key in ("daily_run_ref", "release_ref", "email_ref", "resource_gate_ref"):
                if not str(refs.get(key) or "").strip():
                    errors.append(f"production evidence ready requires {key}")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked scheduled execution requires blocking_reasons")
    notification = report.get("notification_report")
    if isinstance(notification, Mapping):
        errors.extend(validate_smtp_delivery_report(notification))
    release = report.get("release_report")
    if isinstance(release, Mapping):
        errors.extend(validate_release_delivery_report(release))
    return errors


def _run_daily(
    base: dict[str, Any],
    generated_at: str,
    env: Mapping[str, str],
    *,
    daily_input: Mapping[str, Any] | None,
    daily_input_path: str | Path | None,
    release_asset_paths: Sequence[str | Path] | None,
    smtp_factory: SmtpFactory | None,
    release_command_resolver: CommandResolver | None,
    release_command_runner: CommandRunner | None,
) -> dict[str, Any]:
    if _env_true(env, SCHEDULED_RUN_ENV_KEY) is not True:
        report = _blocked(base, [f"{SCHEDULED_RUN_ENV_KEY} must be true before daily scheduled execution"])
        report["notification_report"] = _notification(
            "failure",
            "daily-run",
            generated_at,
            "Daily scheduled execution disabled",
            env,
            smtp_factory=smtp_factory,
        )
        return _with_validation(report)

    raw_payload = dict(daily_input or {})
    if not raw_payload and daily_input_path:
        raw_payload = load_json_mapping(daily_input_path)
    payload, input_reasons = _resolve_daily_input_payload(raw_payload)
    if input_reasons:
        report = _blocked(base, input_reasons)
        report["notification_report"] = _notification(
            "failure",
            "daily-run",
            generated_at,
            "Daily input package blocked",
            env,
            smtp_factory=smtp_factory,
        )
        return _with_validation(report)
    if not payload:
        report = _blocked(base, ["daily-run requires a daily input package with SourceItem and EvidenceClaim data"])
        report["notification_report"] = _notification(
            "failure",
            "daily-run",
            generated_at,
            "Daily input package missing",
            env,
            smtp_factory=smtp_factory,
        )
        return _with_validation(report)

    try:
        daily = run_daily_dry_run(
            payload["source_item"],
            payload["claims"],
            run_id=payload["run_id"],
            publication_id=payload["publication_id"],
            date=payload["date"],
            generated_at=payload.get("generated_at", generated_at),
            timezone=payload.get("timezone", "Australia/Sydney"),
        )
    except (KeyError, PipelineError) as error:
        report = dict(base)
        report["status"] = "failed"
        report["exit_code"] = 2
        report["blocking_reasons"] = [f"daily pipeline failed: {error}"]
        report["notification_report"] = _notification(
            "failure",
            "daily-run",
            generated_at,
            "Daily scheduled pipeline failed",
            env,
            smtp_factory=smtp_factory,
        )
        return _with_validation(report)

    assets = list(release_asset_paths or [])
    if not assets and daily_input_path:
        assets = [daily_input_path]
    release_report = deliver_release(
        tag=str(env.get("ADP_RELEASE_TAG") or f"adp-daily-{payload['date'].replace('-', '')}"),
        title=str(env.get("ADP_RELEASE_TITLE") or f"arXiv Daily Push {payload['date']}"),
        notes=f"Scheduled daily run evidence for {payload['date']}.",
        asset_paths=assets,
        generated_at=generated_at,
        target=env.get("ADP_RELEASE_TARGET"),
        repo=str(env.get("ADP_RELEASE_REPO") or DEFAULT_RELEASE_REPO),
        draft=_env_true(env, "ADP_RELEASE_DRAFT", default=True),
        allow_upload=_env_true(env, RELEASE_UPLOAD_ENV_KEY),
        env=env,
        command_resolver=release_command_resolver,
        command_runner=release_command_runner,
    )
    notification_report = _notification(
        "success" if release_report.get("status") == "created" else "degraded",
        "daily-run",
        generated_at,
        "Daily scheduled pipeline completed",
        env,
        smtp_factory=smtp_factory,
    )
    production_ready = release_report.get("status") == "created" and notification_report.get("status") == "sent"

    report = dict(base)
    report["status"] = "succeeded" if production_ready else "degraded"
    report["exit_code"] = 0 if production_ready else 2
    report["daily_run_report"] = {
        "status": daily["status"],
        "run_id": daily["run_record"]["run_id"],
        "publication_id": daily["publication_gate"]["publication"]["publication_id"],
        "run_record_status": daily["run_record"]["status"],
    }
    report["release_report"] = release_report
    report["notification_report"] = notification_report
    report["production_evidence_ready"] = production_ready
    report["evidence_refs"] = {
        "daily_run_ref": f"run-record://{daily['run_record']['run_id']}",
        "release_ref": str(release_report.get("release_ref") or ""),
        "email_ref": str(notification_report.get("delivery_ref") or ""),
        "resource_gate_ref": base["evidence_refs"]["resource_gate_ref"],
    }
    if not production_ready:
        report["blocking_reasons"] = [
            "daily pipeline completed but real SMTP and Release evidence are not both present",
        ]
    return _with_validation(report)


def _resolve_daily_input_payload(payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if not payload:
        return {}, []
    if payload.get("model_id") != DAILY_INPUT_BUILDER_MODEL_ID and "daily_input" not in payload:
        return dict(payload), []
    errors = validate_daily_input_report(payload)
    if errors:
        return {}, [f"daily input builder report invalid: {errors[0]}"]
    if payload.get("daily_input_ready") is not True or payload.get("status") != "pass":
        return {}, [
            "daily input builder blocked: " + reason
            for reason in (payload.get("blocking_reasons") or ["daily input not ready"])
        ]
    daily_input = payload.get("daily_input")
    if not isinstance(daily_input, Mapping):
        return {}, ["daily input builder report missing daily_input object"]
    return dict(daily_input), []


def _run_watchdog(
    base: dict[str, Any],
    generated_at: str,
    env: Mapping[str, str],
    *,
    previous_execution_report: Mapping[str, Any] | None,
    smtp_factory: SmtpFactory | None,
) -> dict[str, Any]:
    if not isinstance(previous_execution_report, Mapping):
        report = _blocked(base, ["watchdog requires previous daily execution evidence"])
        report["notification_report"] = _notification(
            "failure",
            "watchdog",
            generated_at,
            "Watchdog missing daily execution evidence",
            env,
            smtp_factory=smtp_factory,
        )
        return _with_validation(report)
    if previous_execution_report.get("production_evidence_ready") is not True:
        report = _blocked(base, ["previous daily execution is not production_evidence_ready"])
        report["notification_report"] = _notification(
            "failure",
            "watchdog",
            generated_at,
            "Watchdog detected incomplete daily execution evidence",
            env,
            smtp_factory=smtp_factory,
        )
        return _with_validation(report)
    report = dict(base)
    report["status"] = "succeeded"
    report["exit_code"] = 0
    report["watchdog"] = {"previous_daily_execution_ready": True}
    report["notification_report"] = _notification(
        "success",
        "watchdog",
        generated_at,
        "Watchdog verified daily execution evidence",
        env,
        smtp_factory=smtp_factory,
    )
    return _with_validation(report)


def _base_report(
    mode: str,
    generated_at: str,
    env: Mapping[str, str],
    preflight_report: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "execution_id": f"scheduled-execution:arxiv-daily-push:{mode}",
        "validator_id": SCHEDULED_EXECUTION_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "mode": mode,
        "status": "blocked",
        "exit_code": 2,
        "preflight_status": preflight_report.get("status", "unknown"),
        "scheduled_run_enabled": _env_true(env, SCHEDULED_RUN_ENV_KEY),
        "production_evidence_ready": False,
        "side_effect_policy": {
            "smtp_send_requested": _env_true(env, SMTP_SEND_ENV_KEY),
            "release_upload_requested": _env_true(env, RELEASE_UPLOAD_ENV_KEY),
            "secret_values_logged": False,
            "email_body_logged": False,
            "gh_output_logged": False,
            "codex_auth_read": False,
        },
        "evidence_refs": {
            "daily_run_ref": "",
            "release_ref": "",
            "email_ref": "",
            "resource_gate_ref": str(
                ((preflight_report.get("resource_evidence") or {}).get("resource_pressure_ok_ref") or "")
            ),
        },
        "blocking_reasons": [],
    }


def _notification(
    status: str,
    mode: str,
    generated_at: str,
    summary: str,
    env: Mapping[str, str],
    *,
    smtp_factory: SmtpFactory | None,
) -> dict[str, Any]:
    email = render_email(
        status,
        f"scheduled-{mode}",
        summary,
        date=generated_at[:10],
        phase="11",
        stage=f"scheduled_{mode}",
        claim_gate="production_execution_driver",
        next_action="inspect_scheduled_execution_report",
    )
    return deliver_notification(
        email,
        generated_at=generated_at,
        allow_send=_env_true(env, SMTP_SEND_ENV_KEY),
        env=env,
        smtp_factory=smtp_factory,
    )


def _blocked(base: Mapping[str, Any], reasons: Sequence[str]) -> dict[str, Any]:
    report = dict(base)
    report["status"] = "blocked"
    report["exit_code"] = 2
    report["blocking_reasons"] = list(reasons)
    return report


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_scheduled_execution_report(normalized)
    return normalized


def _env_true(env: Mapping[str, str], key: str, default: bool = False) -> bool:
    value = env.get(key)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
