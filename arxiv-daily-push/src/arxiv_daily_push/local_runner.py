"""Stage 1 local Codex runner and migration-ready launchd package."""

from __future__ import annotations

import hashlib
import json
import os
import plistlib
import shlex
import shutil
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
from .mail_templates import EMAIL_LEARNING_V1_CONTRACT_ID, M1_M4_MAIL_PRODUCTS
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
    command = _local_daily_command(root, state)
    plist = _launchd_plist(command)
    install = _install_script(out / f"{LOCAL_LAUNCHD_LABEL}.plist")
    uninstall = _uninstall_script()
    readme = _launchd_readme(generated_at)
    files = {
        f"{LOCAL_LAUNCHD_LABEL}.plist": plist,
        "install-local-launchd.sh": install,
        "uninstall-local-launchd.sh": uninstall,
        "README_LOCAL_LAUNCHD.md": readme,
    }
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
        "blocking_reasons": [],
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
        and delivery_package.get("email_template_contract") == EMAIL_LEARNING_V1_CONTRACT_ID
        and delivery_package.get("mail_product_id") in M1_M4_MAIL_PRODUCTS
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


def _local_daily_command(project_root: Path, state_dir: Path) -> str:
    generated_at = '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'
    service_date = '$(TZ=Australia/Sydney date +"%Y-%m-%d")'
    return (
        f"cd {shlex.quote(str(project_root))} && "
        f"ADP_LOCAL_DAILY_RUN_ENABLED=true PYTHONPATH=arxiv-daily-push/src "
        f"python3 -m arxiv_daily_push local-runner daily "
        f"--state-dir {shlex.quote(str(state_dir))} "
        f"--date \"{service_date}\" --generated-at \"{generated_at}\" --json"
    )


def _launchd_plist(command: str) -> str:
    payload = {
        "Label": LOCAL_LAUNCHD_LABEL,
        "Disabled": True,
        "StartCalendarInterval": {"Hour": 5, "Minute": 0},
        "RunAtLoad": False,
        "StandardOutPath": "/tmp/adp-local-daily.out",
        "StandardErrorPath": "/tmp/adp-local-daily.err",
        "ProgramArguments": ["/bin/zsh", "-lc", command],
    }
    return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False).decode("utf-8")


def _install_script(plist_path: Path) -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f"cp {shlex.quote(str(plist_path))} \"$HOME/Library/LaunchAgents/{LOCAL_LAUNCHD_LABEL}.plist\"",
            f"launchctl bootstrap gui/$(id -u) \"$HOME/Library/LaunchAgents/{LOCAL_LAUNCHD_LABEL}.plist\"",
            f"launchctl enable gui/$(id -u)/{LOCAL_LAUNCHD_LABEL}",
            "",
        ]
    )


def _uninstall_script() -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f"launchctl bootout gui/$(id -u) \"$HOME/Library/LaunchAgents/{LOCAL_LAUNCHD_LABEL}.plist\" 2>/dev/null || true",
            f"rm -f \"$HOME/Library/LaunchAgents/{LOCAL_LAUNCHD_LABEL}.plist\"",
            "",
        ]
    )


def _launchd_readme(generated_at: str) -> str:
    return (
        "# ADP Local launchd Package\n\n"
        f"- generated_at: `{generated_at}`\n"
        "- default state: generated only, not installed\n"
        "- runner: local Mac + Codex/local Python\n"
        "- GitHub role: code, PR/CI, evidence backup only\n\n"
        "Secrets must stay in local environment or Keychain-backed shell setup. Do not paste SMTP values into plist, scripts, Git, or logs.\n"
    )


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
