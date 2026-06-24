"""Stage 1 local Codex runner and migration-ready launchd package."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_escape
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .config import DEFAULT_TIMEZONE
from .doctor import disk_status
from .global_scan import (
    ALL_ARXIV_MAX_RESULTS_PER_CATEGORY,
    build_all_arxiv_daily_input,
    build_daily_delivery_package,
    validate_all_arxiv_daily_input_report,
)
from .pipeline import PipelineError, run_daily_dry_run
from .production_preflight import (
    MIN_PRODUCTION_FREE_DISK_GIB,
    MIN_PRODUCTION_MEMORY_GIB,
    PRODUCTION_PREFLIGHT_VALIDATOR_ID,
    validate_production_preflight,
)
from .release_delivery import DEFAULT_RELEASE_REPO, deliver_release, validate_release_delivery_report
from .scheduled_execution import LOCAL_DAILY_RUN_ENV_KEY, SMTP_SEND_ENV_KEY
from .smtp_delivery import SMTP_SECRET_ENV_KEYS, SmtpFactory, deliver_notification, validate_smtp_delivery_report
from .source_ingest import FetchAtom


LOCAL_RUNNER_MODEL_ID = "adp-stage1-local-codex-runner-v1"
LOCAL_RUNNER_SCHEMA_VERSION = 1
LOCAL_RUNNER_ACCEPTANCE_ID = "ADP-ACC-S1P5T05-LOCAL-PRODUCTION-MIGRATION-PREP"
LOCAL_RUNNER_REQUIRED_COMMANDS = ("python3", "git")
LOCAL_RUNNER_OPTIONAL_COMMANDS = ("gh",)
LOCAL_RUNNER_QUEUE_FILENAME = "candidate_queue.json"
LOCAL_RUNNER_CONTENT_LEDGER_FILENAME = "local_content_ledger.jsonl"
LOCAL_RUNNER_LATEST_FILENAME = "latest_local_run.json"
LOCAL_RUNNER_REPORT_FILENAME = "adp-local-runner-report.json"
LOCAL_RUNNER_SECRET_NAMES = (*SMTP_SECRET_ENV_KEYS,)
LOCAL_LAUNCHD_LABEL = "com.linze.adp.local.daily"
LOCAL_LAUNCHD_HEALTH_LABEL = "com.linze.adp.local.health"
LOCAL_LAUNCHD_WATCHDOG_LABEL = "com.linze.adp.local.watchdog"
LOCAL_ENV_DEFAULT_PATH = "$HOME/.config/arxiv-daily-push/local-runner.env"
LOCAL_RUNNER_MAX_LATEST_AGE_HOURS = 26.0

CommandResolver = Callable[[str], str | None]


def build_local_preflight(
    *,
    project_root: str | Path,
    state_dir: str | Path,
    generated_at: str,
    env: Mapping[str, str] | None = None,
    require_smtp: bool = False,
    command_resolver: CommandResolver | None = None,
    disk_free_gib: float | None = None,
    memory_total_gib: float | None = None,
) -> dict[str, Any]:
    """Build a local-machine preflight report accepted by the production driver validator."""

    root = Path(project_root).resolve()
    state = Path(state_dir).resolve()
    environment = env if env is not None else os.environ
    resolver = command_resolver or shutil.which
    gates = [
        _command_gate(resolver),
        _state_dir_gate(state),
        _secret_gate(environment, require_smtp=require_smtp),
        _disk_gate(root, disk_free_gib=disk_free_gib),
        _memory_gate(memory_total_gib=memory_total_gib),
    ]
    status = "pass" if all(gate["passed"] for gate in gates) else "blocked"
    return {
        "preflight_id": "local-preflight:arxiv-daily-push",
        "validator_id": PRODUCTION_PREFLIGHT_VALIDATOR_ID,
        "project_id": "arxiv-daily-push",
        "runner_strategy": "local_codex_runner",
        "generated_at": generated_at,
        "timezone": DEFAULT_TIMEZONE,
        "status": status,
        "production_run_allowed": status == "pass",
        "project_root": str(root),
        "state_dir": str(state),
        "gates": gates,
        "blocking_reasons": [
            reason
            for gate in gates
            for reason in gate.get("blocking_reasons", [])
            if gate.get("passed") is not True
        ],
        "secret_policy": {
            "secret_values_logged": False,
            "secret_names_only": True,
            "codex_auth_read": False,
            "storage_policy": "environment_or_keychain_only",
        },
        "resource_evidence": {
            "resource_pressure_ok": status == "pass",
            "resource_pressure_ok_ref": _resource_ref(generated_at) if status == "pass" else "",
        },
        "github_cloud_schedule_required": False,
        "github_cloud_schedule_enabled": False,
    }


def run_local_daily(
    *,
    project_root: str | Path,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    env: Mapping[str, str] | None = None,
    allow_smtp_send: bool = False,
    max_results_per_category: int = ALL_ARXIV_MAX_RESULTS_PER_CATEGORY,
    fetcher: FetchAtom | None = None,
    source_batches: Mapping[str, Mapping[str, Any]] | None = None,
    polite_delay_seconds: float = 0.0,
    write: bool = True,
    smtp_factory: SmtpFactory | None = None,
    command_resolver: CommandResolver | None = None,
    disk_free_gib: float | None = None,
    memory_total_gib: float | None = None,
) -> dict[str, Any]:
    """Run one local Stage 1 daily path and persist migration-ready evidence."""

    root = Path(project_root).resolve()
    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "")
    artifact_dir = run_dir / "artifacts"
    queue_state_path = state / LOCAL_RUNNER_QUEUE_FILENAME
    content_ledger_path = state / LOCAL_RUNNER_CONTENT_LEDGER_FILENAME
    environment = dict(os.environ if env is None else env)
    environment[LOCAL_DAILY_RUN_ENV_KEY] = "true"
    if allow_smtp_send:
        environment[SMTP_SEND_ENV_KEY] = "true"
    if write:
        state.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=True, exist_ok=True)
        artifact_dir.mkdir(parents=True, exist_ok=True)

    preflight = build_local_preflight(
        project_root=root,
        state_dir=state,
        generated_at=generated_at,
        env=environment,
        require_smtp=allow_smtp_send,
        command_resolver=command_resolver,
        disk_free_gib=disk_free_gib,
        memory_total_gib=memory_total_gib,
    )
    if write:
        _write_json(run_dir / "adp-local-preflight.json", preflight)
    preflight_errors = validate_production_preflight(preflight)
    if preflight.get("production_run_allowed") is not True or preflight_errors:
        return _write_or_return(
            _base_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=list(preflight.get("blocking_reasons") or preflight_errors),
                preflight=preflight,
            ),
            run_dir,
            write=write,
        )

    queue = _load_json(queue_state_path) if queue_state_path.exists() else None
    daily_input_report = build_all_arxiv_daily_input(
        date=date,
        generated_at=generated_at,
        queue=queue,
        max_results_per_category=max_results_per_category,
        fetcher=fetcher,
        source_batches=source_batches,
        artifact_dir=artifact_dir if write else None,
        queue_output_path=artifact_dir / "adp-candidate-queue.json" if write else None,
        polite_delay_seconds=polite_delay_seconds,
        transient_retry_delay_seconds=0,
    )
    if write:
        _write_json(run_dir / "adp-daily-input-report.json", daily_input_report)
    daily_errors = validate_all_arxiv_daily_input_report(daily_input_report)
    if daily_errors or daily_input_report.get("daily_input_ready") is not True:
        return _write_or_return(
            _base_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=daily_errors or list(daily_input_report.get("blocking_reasons") or ["daily input blocked"]),
                preflight=preflight,
                daily_input_report=daily_input_report,
            ),
            run_dir,
            write=write,
        )

    daily_input = daily_input_report["daily_input"]
    try:
        daily_run = run_daily_dry_run(
            daily_input["source_item"],
            daily_input["claims"],
            run_id=daily_input["run_id"],
            publication_id=daily_input["publication_id"],
            date=daily_input["date"],
            generated_at=daily_input.get("generated_at", generated_at),
            timezone=daily_input.get("timezone", DEFAULT_TIMEZONE),
        )
    except (KeyError, PipelineError) as error:
        return _write_or_return(
            _base_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=[f"local daily pipeline failed: {error}"],
                preflight=preflight,
                daily_input_report=daily_input_report,
            ),
            run_dir,
            write=write,
        )
    if write:
        _write_json(run_dir / "adp-daily-run.json", daily_run)

    asset_paths = _artifact_asset_paths(daily_input_report)
    release_report = deliver_release(
        tag=f"adp-local-daily-{date.replace('-', '')}",
        title=f"arXiv Daily Push local evidence {date}",
        notes=f"Local Codex runner text-only evidence for arXiv Daily Push {date}.",
        asset_paths=asset_paths,
        generated_at=generated_at,
        repo=DEFAULT_RELEASE_REPO,
        allow_upload=False,
        env=environment,
    )
    release_errors = validate_release_delivery_report(release_report)
    if write:
        _write_json(run_dir / "adp-release-dry-run.json", release_report)
    delivery_package = build_daily_delivery_package(daily_run, daily_input, release_report, generated_at=generated_at)
    notification = delivery_package["notification"]
    notification_report = deliver_notification(
        notification,
        generated_at=generated_at,
        allow_send=allow_smtp_send and _stage1_text_ready(delivery_package),
        env=environment,
        smtp_factory=smtp_factory,
    )
    smtp_errors = validate_smtp_delivery_report(notification_report)
    production_ready = notification_report.get("status") == "sent" and _stage1_text_ready(delivery_package)
    if write:
        (run_dir / "email_preview.txt").write_text(notification.body, encoding="utf-8")
        (run_dir / "email_preview.html").write_text(notification.html_body, encoding="utf-8")
        _write_json(run_dir / "adp-smtp-delivery-report.json", notification_report)
        _persist_queue(artifact_dir / "adp-candidate-queue.json", queue_state_path)

    blocking_reasons = release_errors + smtp_errors
    if release_report.get("status") == "blocked":
        blocking_reasons.extend(release_report.get("blocking_reasons") or ["release dry-run blocked"])
    if allow_smtp_send and notification_report.get("status") != "sent":
        blocking_reasons.extend(notification_report.get("blocking_reasons") or ["real SMTP send did not complete"])

    ledger_row = _content_ledger_row(
        date=date,
        generated_at=generated_at,
        daily_input=daily_input,
        daily_input_report=daily_input_report,
        run_dir=run_dir,
        notification_report=notification_report,
        production_ready=production_ready,
    )
    if write:
        _append_jsonl(content_ledger_path, ledger_row)

    report = _base_report(
        status="blocked" if blocking_reasons else "pass",
        date=date,
        generated_at=generated_at,
        state=state,
        run_dir=run_dir,
        blocking_reasons=blocking_reasons,
        preflight=preflight,
        daily_input_report=daily_input_report,
    )
    report.update(
        {
            "daily_run_status": daily_run["status"],
            "daily_run_ref": f"local-run://{date}/{daily_input['run_id']}",
            "selected_source_id": daily_input["source_item"]["source_id"],
            "selected_title": daily_input["source_item"]["title"],
            "candidate_queue_persisted": write and queue_state_path.exists(),
            "candidate_queue_path": str(queue_state_path),
            "content_ledger_path": str(content_ledger_path),
            "content_ledger_row": ledger_row,
            "email_preview_paths": {
                "plain": str(run_dir / "email_preview.txt"),
                "html": str(run_dir / "email_preview.html"),
            },
            "email_preview_written": write,
            "notification_report": notification_report,
            "delivery_package": {
                key: value
                for key, value in delivery_package.items()
                if key != "notification"
            },
            "release_report": release_report,
            "production_evidence_ready": production_ready,
            "real_smtp_sent": notification_report.get("status") == "sent",
        }
    )
    return _write_or_return(report, run_dir, write=write)


def build_launchd_package(
    *,
    project_root: str | Path,
    state_dir: str | Path,
    artifact_dir: str | Path,
    generated_at: str,
    write: bool = True,
) -> dict[str, Any]:
    """Build macOS launchd templates and owner scripts without installing them."""

    root = Path(project_root).resolve()
    state = Path(state_dir).resolve()
    out = Path(artifact_dir).resolve()
    plists = {
        f"{LOCAL_LAUNCHD_HEALTH_LABEL}.plist": _launchd_plist(
            label=LOCAL_LAUNCHD_HEALTH_LABEL,
            command=_local_health_command(root, state),
            hour=4,
            minute=45,
            stdout_path="/tmp/adp-local-health.out",
            stderr_path="/tmp/adp-local-health.err",
        ),
        f"{LOCAL_LAUNCHD_LABEL}.plist": _launchd_plist(
            label=LOCAL_LAUNCHD_LABEL,
            command=_local_daily_command(root, state),
            hour=5,
            minute=0,
            stdout_path="/tmp/adp-local-daily.out",
            stderr_path="/tmp/adp-local-daily.err",
        ),
        f"{LOCAL_LAUNCHD_WATCHDOG_LABEL}.plist": _launchd_plist(
            label=LOCAL_LAUNCHD_WATCHDOG_LABEL,
            command=_local_watchdog_command(root, state),
            hour=5,
            minute=10,
            stdout_path="/tmp/adp-local-watchdog.out",
            stderr_path="/tmp/adp-local-watchdog.err",
        ),
    }
    install = _install_script(list(plists))
    uninstall = _uninstall_script()
    env_example = _env_example()
    readme = _launchd_readme(generated_at)
    files = dict(plists)
    files.update(
        {
            "local-runner.env.example": env_example,
            "install-local-launchd.sh": install,
            "uninstall-local-launchd.sh": uninstall,
            "README_LOCAL_LAUNCHD.md": readme,
        }
    )
    if write:
        out.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            target = out / name
            target.write_text(content, encoding="utf-8")
            if name.endswith(".sh"):
                target.chmod(0o755)
    file_inventory = [
        {"path": str(out / name), "name": name, "sha256": _sha256_text(content), "bytes": len(content.encode("utf-8"))}
        for name, content in files.items()
    ]
    return {
        "model_id": LOCAL_RUNNER_MODEL_ID,
        "schema_version": LOCAL_RUNNER_SCHEMA_VERSION,
        "acceptance_id": LOCAL_RUNNER_ACCEPTANCE_ID,
        "action": "launchd_package",
        "status": "pass",
        "generated_at": generated_at,
        "platform": "macos",
        "label": LOCAL_LAUNCHD_LABEL,
        "labels": [LOCAL_LAUNCHD_HEALTH_LABEL, LOCAL_LAUNCHD_LABEL, LOCAL_LAUNCHD_WATCHDOG_LABEL],
        "project_root": str(root),
        "state_dir": str(state),
        "artifact_dir": str(out),
        "write_enabled": write,
        "applied": False,
        "real_scheduler_installed": False,
        "github_cloud_schedule_required": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "release_upload_enabled": False,
        "video_generated": False,
        "secret_values_logged": False,
        "codex_auth_read": False,
        "secret_values_written": False,
        "files": file_inventory,
        "required_local_env_file": LOCAL_ENV_DEFAULT_PATH,
        "scheduled_modes": [
            {"mode": "health-check", "local_time": "04:45", "label": LOCAL_LAUNCHD_HEALTH_LABEL},
            {"mode": "daily-run", "local_time": "05:00", "label": LOCAL_LAUNCHD_LABEL},
            {"mode": "watchdog", "local_time": "05:10", "label": LOCAL_LAUNCHD_WATCHDOG_LABEL},
        ],
        "blocking_reasons": [],
    }


def build_operation_readiness(
    *,
    project_root: str | Path,
    state_dir: str | Path,
    generated_at: str,
    env: Mapping[str, str] | None = None,
    require_smtp: bool = True,
    require_scheduler: bool = True,
    launchd_dir: str | Path | None = None,
    max_latest_age_hours: float = LOCAL_RUNNER_MAX_LATEST_AGE_HOURS,
    command_resolver: CommandResolver | None = None,
    disk_free_gib: float | None = None,
    memory_total_gib: float | None = None,
) -> dict[str, Any]:
    """Audit whether Stage 1 can be treated as long-running daily email ops."""

    root = Path(project_root).resolve()
    state = Path(state_dir).resolve()
    environment = dict(os.environ if env is None else env)
    preflight = build_local_preflight(
        project_root=root,
        state_dir=state,
        generated_at=generated_at,
        env=environment,
        require_smtp=require_smtp,
        command_resolver=command_resolver,
        disk_free_gib=disk_free_gib,
        memory_total_gib=memory_total_gib,
    )
    gates = [
        _readiness_gate("local_preflight", preflight.get("status") == "pass", list(preflight.get("blocking_reasons") or []), {"preflight_status": preflight.get("status")}),
        _smtp_readiness_gate(environment, require_smtp=require_smtp),
        _scheduler_readiness_gate(environment, require_scheduler=require_scheduler),
        _latest_run_gate(state, generated_at, require_smtp=require_smtp, max_latest_age_hours=max_latest_age_hours),
    ]
    if launchd_dir is not None:
        gates.append(_launchd_package_gate(Path(launchd_dir)))
    stable = all(gate["passed"] for gate in gates)
    return {
        "model_id": LOCAL_RUNNER_MODEL_ID,
        "schema_version": LOCAL_RUNNER_SCHEMA_VERSION,
        "acceptance_id": LOCAL_RUNNER_ACCEPTANCE_ID,
        "action": "operation_readiness",
        "status": "pass" if stable else "blocked",
        "generated_at": generated_at,
        "timezone": DEFAULT_TIMEZONE,
        "runner_strategy": "local_codex_runner",
        "recommended_runner": "local_macos_launchd_with_codex_local_python",
        "codex_automation_runner": False,
        "github_cloud_schedule_required": False,
        "github_cloud_schedule_enabled": False,
        "stable_daily_email_ready": stable,
        "require_smtp": bool(require_smtp),
        "require_scheduler": bool(require_scheduler),
        "project_root": str(root),
        "state_dir": str(state),
        "preflight": preflight,
        "gates": gates,
        "blocking_reasons": [reason for gate in gates for reason in gate.get("blocking_reasons", []) if gate.get("passed") is not True],
        "real_smtp_sent": False,
        "release_upload_enabled": False,
        "video_generated": False,
        "secret_values_logged": False,
        "codex_auth_read": False,
        "next_owner_actions": _readiness_owner_actions(gates),
    }


def validate_local_runner_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != LOCAL_RUNNER_MODEL_ID:
        errors.append("local runner model_id must be adp-stage1-local-codex-runner-v1")
    if report.get("schema_version") != LOCAL_RUNNER_SCHEMA_VERSION:
        errors.append("local runner schema_version must be 1")
    if report.get("acceptance_id") != LOCAL_RUNNER_ACCEPTANCE_ID:
        errors.append("local runner acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("local runner status must be pass or blocked")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked local runner report requires blocking_reasons")
    for key in ("github_cloud_schedule_required", "github_cloud_schedule_enabled", "video_generated", "release_upload_enabled"):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for Stage 1 local runner prep")
    if report.get("secret_values_logged") is not False:
        errors.append("local runner must not log secret values")
    if report.get("action") == "daily_run" and report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing local daily report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing local daily report requires email_preview_written")
        if report.get("candidate_queue_persisted") is not True:
            errors.append("passing local daily report requires candidate_queue_persisted")
    if report.get("action") == "launchd_package":
        if report.get("applied") is not False or report.get("real_scheduler_installed") is not False:
            errors.append("launchd package must not be applied by the generator")
        labels = report.get("labels")
        if not isinstance(labels, list) or LOCAL_LAUNCHD_LABEL not in labels or LOCAL_LAUNCHD_HEALTH_LABEL not in labels or LOCAL_LAUNCHD_WATCHDOG_LABEL not in labels:
            errors.append("launchd package must include health, daily, and watchdog labels")
    if report.get("action") == "operation_readiness":
        if report.get("stable_daily_email_ready") is True and report.get("status") != "pass":
            errors.append("stable_daily_email_ready requires pass status")
        gates = report.get("gates")
        if not isinstance(gates, list) or not gates:
            errors.append("operation readiness requires non-empty gates")
        if report.get("codex_automation_runner") is not False:
            errors.append("operation readiness must not claim Codex Automation as the Stage 1 daily runner")
    return errors


def _base_report(
    *,
    status: str,
    date: str,
    generated_at: str,
    state: Path,
    run_dir: Path,
    blocking_reasons: list[str],
    preflight: Mapping[str, Any],
    daily_input_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "model_id": LOCAL_RUNNER_MODEL_ID,
        "schema_version": LOCAL_RUNNER_SCHEMA_VERSION,
        "acceptance_id": LOCAL_RUNNER_ACCEPTANCE_ID,
        "action": "daily_run",
        "status": status,
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "runner_strategy": "local_codex_runner",
        "state_dir": str(state),
        "run_dir": str(run_dir),
        "daily_input_ready": bool(daily_input_report and daily_input_report.get("daily_input_ready") is True),
        "preflight_status": preflight.get("status"),
        "production_evidence_ready": False,
        "github_cloud_schedule_required": False,
        "github_cloud_schedule_enabled": False,
        "release_upload_enabled": False,
        "video_generated": False,
        "secret_values_logged": False,
        "codex_auth_read": False,
        "blocking_reasons": blocking_reasons,
    }


def _write_or_return(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_local_runner_report(normalized)
    if write:
        _write_json(run_dir / LOCAL_RUNNER_REPORT_FILENAME, normalized)
        _write_json(run_dir.parent.parent / LOCAL_RUNNER_LATEST_FILENAME, normalized)
    return normalized


def _command_gate(resolver: CommandResolver) -> dict[str, Any]:
    required = [{"command": command, "available": resolver(command) is not None} for command in LOCAL_RUNNER_REQUIRED_COMMANDS]
    optional = [{"command": command, "available": resolver(command) is not None} for command in LOCAL_RUNNER_OPTIONAL_COMMANDS]
    missing = [item["command"] for item in required if item["available"] is not True]
    return _gate(
        "local_required_commands",
        not missing,
        [f"missing local runtime commands: {', '.join(missing)}"] if missing else [],
        {"required_commands": required, "optional_commands": optional, "gh_required_for_daily_runner": False},
    )


def _state_dir_gate(state: Path) -> dict[str, Any]:
    exists_or_parent = state.exists() or state.parent.exists()
    reasons = [] if exists_or_parent else [f"state parent does not exist: {state.parent}"]
    return _gate(
        "local_state_directory",
        exists_or_parent,
        reasons,
        {"state_dir": str(state), "created_by_runner_if_missing": True},
    )


def _secret_gate(env: Mapping[str, str], *, require_smtp: bool) -> dict[str, Any]:
    keys = [{"name": key, "present": bool(env.get(key))} for key in LOCAL_RUNNER_SECRET_NAMES]
    missing = [item["name"] for item in keys if item["present"] is not True]
    passed = not require_smtp or not missing
    reasons = [f"missing required SMTP environment keys for real local send: {', '.join(missing)}"] if not passed else []
    return _gate(
        "local_smtp_secret_names",
        passed,
        reasons,
        {
            "keys": keys,
            "required_for_real_send": bool(require_smtp),
            "values_logged": False,
            "storage_policy": "environment_or_keychain_only",
        },
    )


def _disk_gate(root: Path, *, disk_free_gib: float | None) -> dict[str, Any]:
    free_gib = float(disk_free_gib) if disk_free_gib is not None else float(disk_status(root)["free_gib"])
    passed = free_gib >= MIN_PRODUCTION_FREE_DISK_GIB
    return _gate(
        "local_disk_pressure",
        passed,
        [f"free disk {free_gib:.2f} GiB is below required {MIN_PRODUCTION_FREE_DISK_GIB:.2f} GiB"] if not passed else [],
        {"free_gib": round(free_gib, 2), "min_required_gib": MIN_PRODUCTION_FREE_DISK_GIB},
    )


def _memory_gate(*, memory_total_gib: float | None) -> dict[str, Any]:
    total = float(memory_total_gib) if memory_total_gib is not None else _memory_total_gib()
    passed = total >= MIN_PRODUCTION_MEMORY_GIB
    return _gate(
        "local_memory_pressure",
        passed,
        [f"memory {total:.2f} GiB is below required {MIN_PRODUCTION_MEMORY_GIB:.2f} GiB"] if not passed else [],
        {"total_gib": round(total, 2), "min_required_gib": MIN_PRODUCTION_MEMORY_GIB},
    )


def _gate(gate_id: str, passed: bool, blocking_reasons: list[str], extra: Mapping[str, Any]) -> dict[str, Any]:
    return {"gate_id": gate_id, "passed": bool(passed), "blocking_reasons": list(blocking_reasons), **dict(extra)}


def _artifact_asset_paths(report: Mapping[str, Any]) -> list[str]:
    paths = report.get("artifact_paths") if isinstance(report.get("artifact_paths"), Mapping) else {}
    return [str(path) for path in paths.values() if path]


def _stage1_text_ready(delivery_package: Mapping[str, Any]) -> bool:
    return (
        delivery_package.get("email_contains_chinese_lesson") is True
        and delivery_package.get("email_contains_candidate_queue_summary") is True
        and delivery_package.get("email_contains_html") is True
        and delivery_package.get("video_required") is False
        and delivery_package.get("video_generation_required") is False
        and delivery_package.get("release_required") is False
        and delivery_package.get("email_contains_video_link") is False
    )


def _persist_queue(source: Path, target: Path) -> None:
    if source.exists():
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _content_ledger_row(
    *,
    date: str,
    generated_at: str,
    daily_input: Mapping[str, Any],
    daily_input_report: Mapping[str, Any],
    run_dir: Path,
    notification_report: Mapping[str, Any],
    production_ready: bool,
) -> dict[str, Any]:
    source_item = daily_input["source_item"]
    queue = daily_input_report.get("candidate_queue") if isinstance(daily_input_report.get("candidate_queue"), Mapping) else {}
    return {
        "date": date,
        "generated_at": generated_at,
        "source_id": source_item.get("source_id", ""),
        "title": source_item.get("title", ""),
        "queue_item_count": len(queue.get("items") or []),
        "email_status": notification_report.get("status", ""),
        "email_ref": notification_report.get("delivery_ref", ""),
        "production_evidence_ready": bool(production_ready),
        "run_dir": str(run_dir),
        "daily_input_report": str(run_dir / "adp-daily-input-report.json"),
        "email_preview_plain": str(run_dir / "email_preview.txt"),
        "smtp_delivery_report": str(run_dir / "adp-smtp-delivery-report.json"),
    }


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _generated_at_shell() -> str:
    return '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'


def _service_date_shell() -> str:
    return '$(TZ=Australia/Sydney date +"%Y-%m-%d")'


def _env_setup_shell() -> str:
    return (
        f'env_file="${{ADP_LOCAL_ENV_FILE:-{LOCAL_ENV_DEFAULT_PATH}}}"; '
        'if [ -f "$env_file" ]; then set -a; . "$env_file"; set +a; fi; '
    )


def _local_health_command(project_root: Path, state_dir: Path) -> str:
    generated_at = _generated_at_shell()
    return (
        _env_setup_shell()
        + f"mkdir -p {shlex.quote(str(state_dir / 'health'))}; "
        + f"cd {shlex.quote(str(project_root))} && "
        + "PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push local-runner preflight "
        + f"--project-root {shlex.quote(str(project_root))} "
        + f"--state-dir {shlex.quote(str(state_dir))} "
        + f"--generated-at \"{generated_at}\" --require-smtp --json "
        + f"> {shlex.quote(str(state_dir / 'health' / 'latest-preflight.json'))}"
    )


def _local_daily_command(project_root: Path, state_dir: Path) -> str:
    generated_at = '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'
    service_date = _service_date_shell()
    return (
        _env_setup_shell()
        + 'smtp_flag=""; if [ "${ADP_ALLOW_SMTP_SEND:-false}" = "true" ]; then smtp_flag="--allow-smtp-send"; fi; '
        f"cd {shlex.quote(str(project_root))} && "
        f"ADP_LOCAL_DAILY_RUN_ENABLED=true PYTHONPATH=arxiv-daily-push/src "
        f"python3 -m arxiv_daily_push local-runner daily "
        f"--state-dir {shlex.quote(str(state_dir))} "
        f"--date \"{service_date}\" --generated-at \"{generated_at}\" $smtp_flag --json"
    )


def _local_watchdog_command(project_root: Path, state_dir: Path) -> str:
    generated_at = _generated_at_shell()
    return (
        _env_setup_shell()
        + f"mkdir -p {shlex.quote(str(state_dir / 'watchdog'))}; "
        + f"cd {shlex.quote(str(project_root))} && "
        + "PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push local-runner readiness "
        + f"--project-root {shlex.quote(str(project_root))} "
        + f"--state-dir {shlex.quote(str(state_dir))} "
        + f"--generated-at \"{generated_at}\" --require-smtp --require-scheduler --json "
        + f"> {shlex.quote(str(state_dir / 'watchdog' / 'latest-readiness.json'))}"
    )


def _launchd_plist(*, label: str, command: str, hour: int, minute: int, stdout_path: str, stderr_path: str) -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
            '<plist version="1.0"><dict>',
            f"<key>Label</key><string>{label}</string>",
            "<key>Disabled</key><true/>",
            f"<key>StartCalendarInterval</key><dict><key>Hour</key><integer>{hour}</integer><key>Minute</key><integer>{minute}</integer></dict>",
            "<key>RunAtLoad</key><false/>",
            f"<key>StandardOutPath</key><string>{stdout_path}</string>",
            f"<key>StandardErrorPath</key><string>{stderr_path}</string>",
            f"<key>ProgramArguments</key><array><string>/bin/zsh</string><string>-lc</string><string>{xml_escape(command)}</string></array>",
            "</dict></plist>",
            "",
        ]
    )


def _install_script(plist_names: list[str]) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
        'mkdir -p "$HOME/Library/LaunchAgents"',
    ]
    for name in plist_names:
        label = name.removesuffix(".plist")
        lines.extend(
            [
                f"cp \"$script_dir/{name}\" \"$HOME/Library/LaunchAgents/{name}\"",
                f"launchctl bootstrap gui/$(id -u) \"$HOME/Library/LaunchAgents/{name}\" 2>/dev/null || launchctl kickstart -k gui/$(id -u)/{label}",
                f"launchctl enable gui/$(id -u)/{label}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _uninstall_script() -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f"for label in {LOCAL_LAUNCHD_HEALTH_LABEL} {LOCAL_LAUNCHD_LABEL} {LOCAL_LAUNCHD_WATCHDOG_LABEL}; do",
            '  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true',
            '  rm -f "$HOME/Library/LaunchAgents/$label.plist"',
            "done",
            "",
        ]
    )


def _env_example() -> str:
    return "\n".join(
        [
            "# Copy to ~/.config/arxiv-daily-push/local-runner.env and fill locally.",
            "# Do not commit this file with real values.",
            "ADP_ALLOW_SMTP_SEND=false",
            "ADP_SMTP_HOST=",
            "ADP_SMTP_PORT=587",
            "ADP_SMTP_USERNAME=",
            "ADP_SMTP_PASSWORD=",
            "ADP_LOCAL_SCHEDULER_INSTALLED=false",
            "ADP_LOCAL_SCHEDULER_EVIDENCE_REF=",
            "",
        ]
    )


def _launchd_readme(generated_at: str) -> str:
    return (
        "# ADP Local launchd Package\n\n"
        f"- generated_at: `{generated_at}`\n"
        "- default state: generated only, not installed\n"
        "- jobs: 04:45 health preflight, 05:00 daily email path, 05:10 readiness watchdog\n"
        "- runner: local Mac + Codex/local Python\n"
        "- GitHub role: code, PR/CI, evidence backup only\n\n"
        f"Secrets must stay in `{LOCAL_ENV_DEFAULT_PATH}` or a Keychain-backed shell setup. Do not paste SMTP values into plist, scripts, Git, or logs.\n"
        "Real email send requires `ADP_ALLOW_SMTP_SEND=true` plus all SMTP environment keys in the local env file.\n"
    )


def _readiness_gate(gate_id: str, passed: bool, blocking_reasons: list[str], extra: Mapping[str, Any]) -> dict[str, Any]:
    return {"gate_id": gate_id, "passed": bool(passed), "blocking_reasons": list(blocking_reasons), **dict(extra)}


def _smtp_readiness_gate(env: Mapping[str, str], *, require_smtp: bool) -> dict[str, Any]:
    keys = [{"name": key, "present": bool(env.get(key))} for key in LOCAL_RUNNER_SECRET_NAMES]
    missing = [item["name"] for item in keys if item["present"] is not True]
    allow_send = str(env.get(SMTP_SEND_ENV_KEY, "")).strip().lower() == "true"
    reasons: list[str] = []
    if require_smtp and not allow_send:
        reasons.append(f"{SMTP_SEND_ENV_KEY} must be true for stable daily email operation")
    if require_smtp and missing:
        reasons.append("missing required SMTP environment keys for stable daily email operation: " + ", ".join(missing))
    return _readiness_gate(
        "local_smtp_send_enablement",
        not reasons,
        reasons,
        {"required": bool(require_smtp), "allow_send": allow_send, "keys": keys, "secret_values_logged": False},
    )


def _scheduler_readiness_gate(env: Mapping[str, str], *, require_scheduler: bool) -> dict[str, Any]:
    installed = str(env.get("ADP_LOCAL_SCHEDULER_INSTALLED", "")).strip().lower() == "true"
    evidence_ref = str(env.get("ADP_LOCAL_SCHEDULER_EVIDENCE_REF", "")).strip()
    reasons: list[str] = []
    if require_scheduler and not installed:
        reasons.append("ADP_LOCAL_SCHEDULER_INSTALLED must be true after launchd install is verified")
    if require_scheduler and not evidence_ref:
        reasons.append("ADP_LOCAL_SCHEDULER_EVIDENCE_REF is required after launchd install verification")
    return _readiness_gate(
        "local_scheduler_install_evidence",
        not reasons,
        reasons,
        {"required": bool(require_scheduler), "installed": installed, "evidence_ref": evidence_ref},
    )


def _latest_run_gate(state: Path, generated_at: str, *, require_smtp: bool, max_latest_age_hours: float) -> dict[str, Any]:
    latest_path = state / LOCAL_RUNNER_LATEST_FILENAME
    reasons: list[str] = []
    latest: dict[str, Any] | None = None
    age_hours: float | None = None
    if not latest_path.exists():
        reasons.append(f"{LOCAL_RUNNER_LATEST_FILENAME} does not exist")
    else:
        try:
            latest = _load_json(latest_path)
        except (json.JSONDecodeError, ValueError) as error:
            reasons.append(f"{LOCAL_RUNNER_LATEST_FILENAME} is not valid JSON: {error}")
        if latest:
            if latest.get("status") != "pass":
                reasons.append("latest local daily run is not pass")
            if latest.get("candidate_queue_persisted") is not True:
                reasons.append("latest local daily run did not persist candidate queue")
            if require_smtp and latest.get("real_smtp_sent") is not True:
                reasons.append("latest local daily run has no real SMTP sent evidence")
            age_hours = _age_hours(str(latest.get("generated_at") or ""), generated_at)
            if age_hours is None:
                reasons.append("latest local daily generated_at is not parseable")
            elif age_hours > max_latest_age_hours:
                reasons.append(f"latest local daily run is stale: {age_hours:.2f}h > {max_latest_age_hours:.2f}h")
    return _readiness_gate(
        "latest_local_daily_evidence",
        not reasons,
        reasons,
        {
            "latest_path": str(latest_path),
            "latest_generated_at": latest.get("generated_at") if latest else "",
            "age_hours": round(age_hours, 2) if age_hours is not None else None,
            "max_latest_age_hours": max_latest_age_hours,
        },
    )


def _launchd_package_gate(launchd_dir: Path) -> dict[str, Any]:
    required = [
        f"{LOCAL_LAUNCHD_HEALTH_LABEL}.plist",
        f"{LOCAL_LAUNCHD_LABEL}.plist",
        f"{LOCAL_LAUNCHD_WATCHDOG_LABEL}.plist",
        "local-runner.env.example",
        "install-local-launchd.sh",
        "uninstall-local-launchd.sh",
        "README_LOCAL_LAUNCHD.md",
    ]
    missing = [name for name in required if not (launchd_dir / name).exists()]
    return _readiness_gate(
        "launchd_package_files",
        not missing,
        [f"launchd package missing files: {', '.join(missing)}"] if missing else [],
        {"launchd_dir": str(launchd_dir), "required_files": required},
    )


def _readiness_owner_actions(gates: list[Mapping[str, Any]]) -> list[str]:
    actions: list[str] = []
    failed = {str(gate.get("gate_id")) for gate in gates if gate.get("passed") is not True}
    if "local_smtp_send_enablement" in failed:
        actions.append("configure local SMTP environment or Keychain-backed env file and set ADP_ALLOW_SMTP_SEND=true")
    if "local_scheduler_install_evidence" in failed or "launchd_package_files" in failed:
        actions.append("generate/install the local launchd package, then record ADP_LOCAL_SCHEDULER_INSTALLED=true and ADP_LOCAL_SCHEDULER_EVIDENCE_REF locally")
    if "latest_local_daily_evidence" in failed:
        actions.append("run one confirmed local-runner daily execution with real SMTP send before treating daily operation as stable")
    if "local_preflight" in failed:
        actions.append("fix local preflight blockers before enabling unattended daily execution")
    return actions


def _age_hours(older_iso: str, newer_iso: str) -> float | None:
    older = _parse_datetime(older_iso)
    newer = _parse_datetime(newer_iso)
    if older is None or newer is None:
        return None
    return max(0.0, (newer - older).total_seconds() / 3600.0)


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _resource_ref(generated_at: str) -> str:
    token = "".join(character if character.isalnum() else "-" for character in generated_at).strip("-")
    return f"local-preflight://arxiv-daily-push/{token or 'current'}"


def _memory_total_gib() -> float:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        return float(page_size * pages) / (1024**3)
    except (AttributeError, OSError, ValueError):
        return 0.0
