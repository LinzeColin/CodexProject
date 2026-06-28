"""Stage 1 local Codex runner and migration-ready launchd package."""

from __future__ import annotations

import hashlib
import json
import os
import plistlib
import re
import shlex
import shutil
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .config import DEFAULT_TIMEZONE
from .doctor import disk_status
from .global_scan import (
    ALL_ARXIV_MAX_RESULTS_PER_CATEGORY,
    ROI_COMPONENT_WEIGHTS,
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
USER_CENTER_LEARNING_PAGE = Path("用户中心") / "复习行动与收益.md"
USER_CENTER_MAIL_STATUS_PAGES = (
    Path("用户中心") / "README.md",
    Path("用户中心") / "一看三查.md",
    Path("用户中心") / "邮件发送与队列状态.md",
)
REVIEW_REPORT_FILENAME = "stage2_s2pjt02_review_schedule_report.json"
ACTION_ROI_REPORT_FILENAME = "stage2_s2pjt03_action_asset_roi_ledger_report.json"
USER_CENTER_PENDING_VALUE = "待今日运行快照写入"
USER_CENTER_PENDING_PLANNED_SEND_TOTAL = "待确认"
USER_CENTER_SCORE_DETAIL_GATE_ID = "adp-user-center-six-factor-score-detail-gate-v1"
USER_CENTER_SNAPSHOT_FIELDS = (
    "今日到期复习",
    "未来 7 天复习",
    "已逾期复习",
    "已完成复习",
    "今日 15 分钟行动",
    "今日 2 小时行动",
    "今日 7 天行动",
    "今日 30 天行动",
    "新增能力资产",
    "可验证实际收益 / 转化",
)

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
    delivery_packages = _build_m1_m4_delivery_packages(
        daily_run,
        daily_input,
        release_report,
        generated_at=generated_at,
    )
    delivery_package = delivery_packages["M1"]
    planned_mail_delivery = _planned_mail_delivery_summary(delivery_package)
    user_center_sync = _sync_user_center_learning_snapshot(
        root=root,
        state=state,
        write=write,
        planned_mail_delivery=planned_mail_delivery,
        daily_input_report=daily_input_report,
    )
    user_center_sync_ready = user_center_sync.get("status") == "pass"
    historical_sent_reports = _historical_sent_mail_reports(content_ledger_path, date) if allow_smtp_send else {}
    notification_reports = _deliver_mail_product_notifications(
        delivery_packages=delivery_packages,
        generated_at=generated_at,
        date=date,
        allow_smtp_send=allow_smtp_send,
        user_center_sync_ready=user_center_sync_ready,
        historical_sent_reports=historical_sent_reports,
        env=environment,
        smtp_factory=smtp_factory,
    )
    notification_report = notification_reports["M1"]
    smtp_errors = [
        f"{product_id}: {error}"
        for product_id, report_item in notification_reports.items()
        for error in validate_smtp_delivery_report(report_item)
    ]
    mail_delivery_summary = _mail_delivery_summary(
        planned_mail_delivery=planned_mail_delivery,
        notification_reports=notification_reports,
    )
    user_center_send_count_sync = _sync_user_center_send_count(
        root=root,
        write=write,
        planned_mail_delivery=planned_mail_delivery,
        sent_mail_count=int(mail_delivery_summary["sent_mail_count"]),
        enabled=allow_smtp_send and user_center_sync_ready,
    )
    user_center_send_count_ready = user_center_send_count_sync.get("status") in {"pass", "skipped"}
    production_ready = (
        mail_delivery_summary["all_planned_products_sent"] is True
        and all(_stage1_text_ready(package) for package in delivery_packages.values())
        and user_center_sync_ready
        and user_center_send_count_ready
    )
    if write:
        _write_mail_product_artifacts(run_dir, delivery_packages=delivery_packages, notification_reports=notification_reports)
        _persist_queue(artifact_dir / "adp-candidate-queue.json", queue_state_path)

    blocking_reasons = (
        release_errors
        + smtp_errors
        + list(user_center_sync.get("blocking_reasons") or [])
        + list(user_center_send_count_sync.get("blocking_reasons") or [])
    )
    if release_report.get("status") == "blocked":
        blocking_reasons.extend(release_report.get("blocking_reasons") or ["release dry-run blocked"])
    if allow_smtp_send and production_ready is not True:
        blocking_reasons.extend(_unsent_mail_blocking_reasons(notification_reports))

    ledger_row = _content_ledger_row(
        date=date,
        generated_at=generated_at,
        daily_input=daily_input,
        daily_input_report=daily_input_report,
        run_dir=run_dir,
        notification_report=notification_report,
        notification_reports=notification_reports,
        mail_delivery_summary=mail_delivery_summary,
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
                "by_product": {
                    product_id: {
                        "plain": str(run_dir / f"email_preview_{product_id}.txt"),
                        "html": str(run_dir / f"email_preview_{product_id}.html"),
                    }
                    for product_id in M1_M4_MAIL_PRODUCTS
                },
            },
            "email_preview_written": write,
            "user_center_sync": user_center_sync,
            "user_center_sync_ready": user_center_sync_ready,
            "user_center_send_count_sync": user_center_send_count_sync,
            "planned_mail_delivery": planned_mail_delivery,
            "mail_delivery_summary": mail_delivery_summary,
            "notification_report": notification_report,
            "notification_reports": notification_reports,
            "historical_sent_reports": historical_sent_reports,
            "delivery_package": {
                key: value
                for key, value in delivery_package.items()
                if key != "notification"
            },
            "delivery_packages": {
                product_id: {key: value for key, value in package.items() if key != "notification"}
                for product_id, package in delivery_packages.items()
            },
            "release_report": release_report,
            "production_evidence_ready": production_ready,
            "real_smtp_sent": mail_delivery_summary["all_planned_products_sent"] is True,
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
        if report.get("user_center_sync_ready") is not True:
            errors.append("passing local daily report requires user_center_sync_ready")
        delivery_summary = report.get("mail_delivery_summary")
        if isinstance(delivery_summary, Mapping):
            planned_products = tuple(delivery_summary.get("planned_mail_products") or ())
            if planned_products != tuple(M1_M4_MAIL_PRODUCTS):
                errors.append("passing local daily report requires M1-M4 planned mail products")
            if report.get("real_smtp_sent") is True and delivery_summary.get("all_planned_products_sent") is not True:
                errors.append("real_smtp_sent requires all planned M1-M4 products sent")
        elif report.get("real_smtp_sent") is True:
            errors.append("real_smtp_sent requires mail_delivery_summary")
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


def _sync_user_center_learning_snapshot(
    *,
    root: Path,
    state: Path,
    write: bool,
    planned_mail_delivery: Mapping[str, Any],
    daily_input_report: Mapping[str, Any],
) -> dict[str, Any]:
    page = root / USER_CENTER_LEARNING_PAGE
    review_path = state / REVIEW_REPORT_FILENAME
    action_path = state / ACTION_ROI_REPORT_FILENAME
    mail_pages = [root / path for path in USER_CENTER_MAIL_STATUS_PAGES]
    report = {
        "status": "blocked",
        "page": str(page),
        "mail_status_pages": [str(path) for path in mail_pages],
        "review_report": str(review_path),
        "action_roi_report": str(action_path),
        "write_enabled": write,
        "blocking_reasons": [],
        "snapshot_values": {},
        "planned_mail_delivery": dict(planned_mail_delivery),
    }
    score_detail_gate = _candidate_score_detail_gate(daily_input_report)
    report["candidate_score_detail_gate"] = score_detail_gate
    report["candidate_score_detail_ready"] = score_detail_gate["status"] == "pass"
    if score_detail_gate["status"] != "pass":
        report["blocking_reasons"] = list(score_detail_gate["blocking_reasons"])
        return report
    if not write:
        report["blocking_reasons"] = ["user center sync requires write mode"]
        return report
    missing = [
        str(path)
        for path in (page, review_path, action_path, *mail_pages)
        if not path.exists()
    ]
    if missing:
        report["blocking_reasons"] = ["user center sync missing required files: " + ", ".join(missing)]
        return report
    try:
        review_report = _load_json(review_path)
        action_report = _load_json(action_path)
        values = _user_center_snapshot_values(review_report, action_report)
        if any(value == USER_CENTER_PENDING_VALUE for value in values.values()):
            report["blocking_reasons"] = ["user center sync has pending fields; real review/action/asset/ROI reports are incomplete"]
            report["snapshot_values"] = values
            return report
        current = page.read_text(encoding="utf-8")
        updated = _replace_user_center_snapshot_values(current, values)
        page.write_text(updated, encoding="utf-8")
        if _replace_user_center_snapshot_values(page.read_text(encoding="utf-8"), values) != updated:
            report["blocking_reasons"] = ["user center sync verification failed after write"]
            report["snapshot_values"] = values
            return report
        for mail_page in mail_pages:
            current_mail_page = mail_page.read_text(encoding="utf-8")
            updated_mail_page = _replace_user_center_planned_send_total(current_mail_page, planned_mail_delivery)
            mail_page.write_text(updated_mail_page, encoding="utf-8")
            if _replace_user_center_planned_send_total(mail_page.read_text(encoding="utf-8"), planned_mail_delivery) != updated_mail_page:
                report["blocking_reasons"] = [f"user center mail status verification failed after write: {mail_page}"]
                report["snapshot_values"] = values
                return report
    except (OSError, ValueError, json.JSONDecodeError) as error:
        report["blocking_reasons"] = [f"user center sync failed: {error}"]
        return report
    report["status"] = "pass"
    report["blocking_reasons"] = []
    report["snapshot_values"] = values
    return report


def _candidate_score_detail_gate(daily_input_report: Mapping[str, Any]) -> dict[str, Any]:
    candidates = _candidate_score_detail_candidates(daily_input_report)
    blocking_reasons: list[str] = []
    details: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        source_id = str(candidate.get("source_id") or f"candidate[{index}]")
        signals = candidate.get("roi_signals")
        weights = candidate.get("roi_component_weights")
        score_value = candidate.get("roi_total_score")
        if not isinstance(signals, Mapping):
            blocking_reasons.append(f"{source_id} missing roi_signals six-factor detail")
            continue
        if not isinstance(weights, Mapping):
            blocking_reasons.append(f"{source_id} missing roi_component_weights")
            continue
        try:
            score = _bounded_number(score_value, minimum=0.0, maximum=100.0)
        except ValueError:
            blocking_reasons.append(f"{source_id} roi_total_score must be a number between 0 and 100")
            continue
        component_scores: dict[str, float] = {}
        normalized_signals: dict[str, float] = {}
        for component, expected_weight in ROI_COMPONENT_WEIGHTS.items():
            try:
                signal = _bounded_number(signals.get(component), minimum=0.0, maximum=1.0)
            except ValueError:
                blocking_reasons.append(f"{source_id} roi_signals.{component} must be a number between 0 and 1")
                continue
            try:
                actual_weight = _bounded_number(weights.get(component), minimum=0.0, maximum=100.0)
            except ValueError:
                blocking_reasons.append(f"{source_id} roi_component_weights.{component} must be a number")
                continue
            if abs(actual_weight - float(expected_weight)) > 0.0001:
                blocking_reasons.append(f"{source_id} roi_component_weights.{component} must equal {expected_weight:g}")
                continue
            normalized_signals[component] = signal
            component_scores[component] = round(signal * float(expected_weight), 4)
        if set(component_scores) != set(ROI_COMPONENT_WEIGHTS):
            continue
        recomputed = round(sum(component_scores.values()), 4)
        if abs(recomputed - score) > 0.0001:
            blocking_reasons.append(f"{source_id} roi_total_score does not match six-factor score detail")
            continue
        details.append(
            {
                "source_id": source_id,
                "title": str(candidate.get("title") or ""),
                "roi_total_score": score,
                "roi_signals": normalized_signals,
                "roi_component_weights": dict(ROI_COMPONENT_WEIGHTS),
                "roi_component_scores": component_scores,
            }
        )
    if not candidates:
        blocking_reasons.append("daily input report has no generated candidates with six-factor score details")
    return {
        "gate_id": USER_CENTER_SCORE_DETAIL_GATE_ID,
        "status": "blocked" if blocking_reasons else "pass",
        "required_components": list(ROI_COMPONENT_WEIGHTS),
        "candidate_count": len(candidates),
        "checked_candidate_count": len(details),
        "candidate_score_details": details,
        "blocking_reasons": blocking_reasons,
    }


def _candidate_score_detail_candidates(daily_input_report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidates: list[Mapping[str, Any]] = []
    seen: set[str] = set()

    def add(candidate: Any) -> None:
        if not isinstance(candidate, Mapping):
            return
        source_id = str(candidate.get("source_id") or "")
        key = source_id or json.dumps(candidate, sort_keys=True, default=str)
        if key in seen:
            return
        seen.add(key)
        candidates.append(candidate)

    selection = daily_input_report.get("selection")
    if isinstance(selection, Mapping):
        add(selection.get("selected"))
        for candidate in selection.get("audits") or []:
            add(candidate)
    scan = daily_input_report.get("scan")
    if isinstance(scan, Mapping):
        for candidate in scan.get("candidates") or []:
            add(candidate)
    queue = daily_input_report.get("candidate_queue")
    if isinstance(queue, Mapping):
        for candidate in queue.get("items") or []:
            add(candidate)
    return candidates


def _bounded_number(value: Any, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean is not a score")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("not numeric") from error
    if number < minimum or number > maximum:
        raise ValueError("out of range")
    return number


def _planned_mail_delivery_summary(delivery_package: Mapping[str, Any]) -> dict[str, Any]:
    products = tuple(str(product) for product in delivery_package.get("mail_products_supported") or M1_M4_MAIL_PRODUCTS)
    if set(products) != set(M1_M4_MAIL_PRODUCTS):
        products = tuple(M1_M4_MAIL_PRODUCTS)
    current_product = str(delivery_package.get("mail_product_id") or "")
    return {
        "source": "EMAIL_LEARNING_V1_M1_M4_CONTRACT",
        "planned_send_total": len(M1_M4_MAIL_PRODUCTS),
        "planned_mail_products": list(M1_M4_MAIL_PRODUCTS),
        "current_mail_product_id": current_product,
        "current_mail_product_planned": current_product in M1_M4_MAIL_PRODUCTS,
        "daily_operation_accepted": False,
        "smtp_or_scheduler_enabled_by_this_gate": False,
    }


def _build_m1_m4_delivery_packages(
    daily_run: Mapping[str, Any],
    daily_input: Mapping[str, Any],
    release_report: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, dict[str, Any]]:
    return {
        product_id: build_daily_delivery_package(
            daily_run,
            daily_input,
            release_report,
            generated_at=generated_at,
            mail_product_id=product_id,
        )
        for product_id in M1_M4_MAIL_PRODUCTS
    }


def _deliver_mail_product_notifications(
    *,
    delivery_packages: Mapping[str, Mapping[str, Any]],
    generated_at: str,
    date: str,
    allow_smtp_send: bool,
    user_center_sync_ready: bool,
    historical_sent_reports: Mapping[str, Mapping[str, Any]],
    env: Mapping[str, str],
    smtp_factory: SmtpFactory | None,
) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for product_id in M1_M4_MAIL_PRODUCTS:
        package = delivery_packages[product_id]
        notification = package["notification"]
        if allow_smtp_send and product_id in historical_sent_reports:
            reports[product_id] = _historical_sent_notification_report(
                notification,
                generated_at=generated_at,
                date=date,
                product_id=product_id,
                historical_report=historical_sent_reports[product_id],
            )
            continue
        if allow_smtp_send and user_center_sync_ready is not True:
            reports[product_id] = _blocked_notification_report(
                notification,
                generated_at=generated_at,
                date=date,
                product_id=product_id,
                reason="user center sync not ready; real SMTP send blocked",
            )
            continue
        if allow_smtp_send and not _stage1_text_ready(package):
            reports[product_id] = _blocked_notification_report(
                notification,
                generated_at=generated_at,
                date=date,
                product_id=product_id,
                reason=f"{product_id} Email V1 package is not ready for real SMTP send",
            )
            continue
        report = deliver_notification(
            notification,
            generated_at=generated_at,
            cycle_id=date,
            product_id=product_id,
            allow_send=allow_smtp_send,
            env=env,
            smtp_factory=smtp_factory,
        )
        reports[product_id] = _with_delivery_attempt_fields(
            report,
            allow_send=allow_smtp_send,
            attempted=allow_smtp_send and report.get("status") != "blocked",
        )
    return reports


def _historical_sent_mail_reports(content_ledger_path: Path, date: str) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    if not content_ledger_path.exists():
        return reports
    try:
        lines = content_ledger_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return reports
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, Mapping) or str(row.get("date") or "") != date:
            continue
        status_by_product = row.get("email_status_by_product")
        ref_by_product = row.get("email_ref_by_product")
        if isinstance(status_by_product, Mapping):
            refs = ref_by_product if isinstance(ref_by_product, Mapping) else {}
            for product_id in M1_M4_MAIL_PRODUCTS:
                if status_by_product.get(product_id) == "sent":
                    reports[product_id] = {
                        "product_id": product_id,
                        "delivery_ref": str(refs.get(product_id) or row.get("email_ref") or f"local-ledger://{date}/{product_id}"),
                        "ledger_ref": str(content_ledger_path),
                    }
        elif row.get("email_status") == "sent":
            product_id = str(row.get("mail_product_id") or "M1")
            if product_id in M1_M4_MAIL_PRODUCTS:
                reports[product_id] = {
                    "product_id": product_id,
                    "delivery_ref": str(row.get("email_ref") or f"local-ledger://{date}/{product_id}"),
                    "ledger_ref": str(content_ledger_path),
                }
    return reports


def _historical_sent_notification_report(
    notification: Any,
    *,
    generated_at: str,
    date: str,
    product_id: str,
    historical_report: Mapping[str, Any],
) -> dict[str, Any]:
    report = deliver_notification(
        notification,
        generated_at=generated_at,
        cycle_id=date,
        product_id=product_id,
        allow_send=False,
        env={},
    )
    sent = dict(report)
    sent["status"] = "sent"
    sent["dry_run"] = False
    sent["real_smtp_send_enabled"] = False
    sent["delivery_ref"] = str(historical_report.get("delivery_ref") or f"local-ledger://{date}/{product_id}")
    sent["historical_delivery_evidence"] = True
    sent["historical_ledger_ref"] = str(historical_report.get("ledger_ref") or "")
    return _with_delivery_attempt_fields(sent, allow_send=False, attempted=False)


def _blocked_notification_report(
    notification: Any,
    *,
    generated_at: str,
    date: str,
    product_id: str,
    reason: str,
) -> dict[str, Any]:
    report = deliver_notification(
        notification,
        generated_at=generated_at,
        cycle_id=date,
        product_id=product_id,
        allow_send=False,
        env={},
    )
    blocked = dict(report)
    blocked["status"] = "blocked"
    blocked["dry_run"] = False
    blocked["real_smtp_send_enabled"] = False
    blocked["blocking_reasons"] = [reason]
    return _with_delivery_attempt_fields(blocked, allow_send=False, attempted=False)


def _with_delivery_attempt_fields(report: Mapping[str, Any], *, allow_send: bool, attempted: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized["allow_send"] = bool(allow_send)
    normalized["real_send_attempted"] = bool(attempted)
    return normalized


def _mail_delivery_summary(
    *,
    planned_mail_delivery: Mapping[str, Any],
    notification_reports: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    planned_products = [str(product) for product in planned_mail_delivery.get("planned_mail_products") or M1_M4_MAIL_PRODUCTS]
    statuses = {product_id: str(notification_reports.get(product_id, {}).get("status") or "missing") for product_id in planned_products}
    sent_products = [product_id for product_id, status in statuses.items() if status == "sent"]
    historical_sent_products = [
        product_id
        for product_id in sent_products
        if notification_reports.get(product_id, {}).get("historical_delivery_evidence") is True
    ]
    newly_sent_products = [
        product_id
        for product_id in sent_products
        if notification_reports.get(product_id, {}).get("real_send_attempted") is True
    ]
    blocked_products = [product_id for product_id, status in statuses.items() if status == "blocked"]
    dry_run_products = [product_id for product_id, status in statuses.items() if status == "dry_run"]
    missing_products = [product_id for product_id, status in statuses.items() if status == "missing"]
    return {
        "source": "EMAIL_LEARNING_V1_M1_M4_CONTRACT",
        "planned_send_total": int(planned_mail_delivery.get("planned_send_total") or len(planned_products)),
        "planned_mail_products": planned_products,
        "sent_mail_count": len(sent_products),
        "sent_mail_products": sent_products,
        "newly_sent_mail_products": newly_sent_products,
        "historical_sent_mail_products": historical_sent_products,
        "blocked_mail_products": blocked_products,
        "dry_run_mail_products": dry_run_products,
        "missing_mail_products": missing_products,
        "status_by_product": statuses,
        "delivery_ref_by_product": {
            product_id: str(notification_reports.get(product_id, {}).get("delivery_ref") or "")
            for product_id in planned_products
        },
        "all_planned_products_attempted": not missing_products,
        "all_planned_products_sent": len(sent_products) == len(planned_products) and not missing_products,
    }


def _sync_user_center_send_count(
    *,
    root: Path,
    write: bool,
    planned_mail_delivery: Mapping[str, Any],
    sent_mail_count: int,
    enabled: bool,
) -> dict[str, Any]:
    mail_pages = [root / path for path in USER_CENTER_MAIL_STATUS_PAGES]
    report = {
        "status": "skipped",
        "mail_status_pages": [str(path) for path in mail_pages],
        "write_enabled": write,
        "sent_mail_count": int(sent_mail_count),
        "planned_mail_delivery": dict(planned_mail_delivery),
        "blocking_reasons": [],
    }
    if not enabled:
        return report
    if not write:
        report["status"] = "blocked"
        report["blocking_reasons"] = ["user center sent count sync requires write mode"]
        return report
    missing = [str(path) for path in mail_pages if not path.exists()]
    if missing:
        report["status"] = "blocked"
        report["blocking_reasons"] = ["user center sent count sync missing required files: " + ", ".join(missing)]
        return report
    try:
        for mail_page in mail_pages:
            current = mail_page.read_text(encoding="utf-8")
            updated = _replace_user_center_planned_send_total(
                current,
                planned_mail_delivery,
                sent_mail_count=sent_mail_count,
            )
            mail_page.write_text(updated, encoding="utf-8")
            if (
                _replace_user_center_planned_send_total(
                    mail_page.read_text(encoding="utf-8"),
                    planned_mail_delivery,
                    sent_mail_count=sent_mail_count,
                )
                != updated
            ):
                report["status"] = "blocked"
                report["blocking_reasons"] = [f"user center sent count verification failed after write: {mail_page}"]
                return report
    except (OSError, ValueError) as error:
        report["status"] = "blocked"
        report["blocking_reasons"] = [f"user center sent count sync failed: {error}"]
        return report
    report["status"] = "pass"
    return report


def _write_mail_product_artifacts(
    run_dir: Path,
    *,
    delivery_packages: Mapping[str, Mapping[str, Any]],
    notification_reports: Mapping[str, Mapping[str, Any]],
) -> None:
    for product_id in M1_M4_MAIL_PRODUCTS:
        notification = delivery_packages[product_id]["notification"]
        (run_dir / f"email_preview_{product_id}.txt").write_text(notification.body, encoding="utf-8")
        (run_dir / f"email_preview_{product_id}.html").write_text(notification.html_body, encoding="utf-8")
        _write_json(run_dir / f"adp-smtp-delivery-report-{product_id}.json", notification_reports[product_id])
    m1_notification = delivery_packages["M1"]["notification"]
    (run_dir / "email_preview.txt").write_text(m1_notification.body, encoding="utf-8")
    (run_dir / "email_preview.html").write_text(m1_notification.html_body, encoding="utf-8")
    _write_json(run_dir / "adp-smtp-delivery-report.json", notification_reports["M1"])


def _unsent_mail_blocking_reasons(notification_reports: Mapping[str, Mapping[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for product_id in M1_M4_MAIL_PRODUCTS:
        report = notification_reports.get(product_id) or {}
        if report.get("status") == "sent":
            continue
        product_reasons = [str(reason) for reason in report.get("blocking_reasons") or [] if reason]
        if product_reasons:
            reasons.extend(f"{product_id}: {reason}" for reason in product_reasons)
        else:
            reasons.append(f"{product_id}: real SMTP send did not complete")
    return reasons


def _user_center_report_passed(report: Mapping[str, Any] | None, ready_key: str) -> bool:
    return bool(report and report.get("status") == "pass" and report.get(ready_key) is True)


def _user_center_count_value(value: Any) -> str:
    if isinstance(value, bool):
        return USER_CENTER_PENDING_VALUE
    if isinstance(value, int) and value >= 0:
        return f"{value} 项"
    return USER_CENTER_PENDING_VALUE


def _user_center_snapshot_values(
    review_report: Mapping[str, Any] | None,
    action_report: Mapping[str, Any] | None,
) -> dict[str, str]:
    values = {field: USER_CENTER_PENDING_VALUE for field in USER_CENTER_SNAPSHOT_FIELDS}
    if _user_center_report_passed(review_report, "s2pjt02_review_schedule_ready"):
        counts = review_report.get("computed_counts")
        if isinstance(counts, Mapping):
            values.update(
                {
                    "今日到期复习": _user_center_count_value(counts.get("due_today")),
                    "未来 7 天复习": _user_center_count_value(counts.get("due_next_7_days")),
                    "已逾期复习": _user_center_count_value(counts.get("overdue")),
                    "已完成复习": _user_center_count_value(counts.get("completed")),
                }
            )
    if _user_center_report_passed(action_report, "s2pjt03_action_roi_ready"):
        counts = action_report.get("action_counts")
        if isinstance(counts, Mapping):
            values.update(
                {
                    "今日 15 分钟行动": _user_center_count_value(counts.get("15m")),
                    "今日 2 小时行动": _user_center_count_value(counts.get("2h")),
                    "今日 7 天行动": _user_center_count_value(counts.get("7d")),
                    "今日 30 天行动": _user_center_count_value(counts.get("30d")),
                }
            )
        assets = action_report.get("capability_assets")
        if isinstance(assets, list):
            values["新增能力资产"] = _user_center_count_value(len(assets))
        roi_counts = action_report.get("actual_roi_status_counts")
        if isinstance(roi_counts, Mapping):
            values["可验证实际收益 / 转化"] = _user_center_count_value(roi_counts.get("calculated"))
    return values


def _replace_user_center_snapshot_values(text: str, values: Mapping[str, str]) -> str:
    lines = text.splitlines()
    changed_lines: list[str] = []
    seen: set[str] = set()
    row_re = re.compile(r"^\| (?P<field>[^|]+) \| (?P<value>[^|]+) \| (?P<source>[^|]+) \|$")
    for line in lines:
        match = row_re.match(line)
        if match:
            field = match.group("field").strip()
            if field in values:
                seen.add(field)
                line = f"| {field} | {values[field]} | {match.group('source').strip()} |"
        changed_lines.append(line)
    missing = [field for field in USER_CENTER_SNAPSHOT_FIELDS if field not in seen]
    if missing:
        raise ValueError("复习行动与收益.md missing snapshot rows: " + ", ".join(missing))
    return "\n".join(changed_lines) + ("\n" if text.endswith("\n") else "")


def _replace_user_center_planned_send_total(
    text: str,
    planned_mail_delivery: Mapping[str, Any],
    *,
    sent_mail_count: int | None = None,
) -> str:
    planned_total = int(planned_mail_delivery.get("planned_send_total") or 0)
    planned_products = ", ".join(str(product) for product in planned_mail_delivery.get("planned_mail_products") or [])
    if planned_total <= 0 or not planned_products:
        raise ValueError("planned mail delivery summary missing planned total or products")
    lines = text.splitlines()
    changed = False
    row_re = re.compile(r"^(?P<prefix>\| 今日已发送 / 总应发送 \| )(?P<value>[^|]+)(?P<suffix>\|.*)$")
    for index, line in enumerate(lines):
        match = row_re.match(line)
        if not match:
            continue
        current_value = match.group("value").strip()
        if sent_mail_count is None:
            sent_part = current_value.split("/", 1)[0].strip()
            if not sent_part or sent_part == USER_CENTER_PENDING_PLANNED_SEND_TOTAL:
                sent_part = "0"
        else:
            sent_part = str(max(0, int(sent_mail_count)))
        lines[index] = f"{match.group('prefix')}{sent_part} / {planned_total} {match.group('suffix').lstrip()}"
        changed = True
    if not changed:
        raise ValueError("mail status page missing 今日已发送 / 总应发送 row")
    updated = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    marker = f"计划来源：Email V1 每日 3+1（{planned_products}），总应发送 {planned_total} 封；这不是 Stage 2 生产验收通过声明。"
    if marker not in updated:
        updated = updated.rstrip() + "\n\n" + marker + "\n"
    if USER_CENTER_PENDING_PLANNED_SEND_TOTAL in "\n".join(
        line for line in updated.splitlines() if "今日已发送 / 总应发送" in line
    ):
        raise ValueError("mail status page still contains pending planned send total")
    return updated


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
    notification_reports: Mapping[str, Mapping[str, Any]],
    mail_delivery_summary: Mapping[str, Any],
    production_ready: bool,
) -> dict[str, Any]:
    source_item = daily_input["source_item"]
    queue = daily_input_report.get("candidate_queue") if isinstance(daily_input_report.get("candidate_queue"), Mapping) else {}
    status_by_product = dict(mail_delivery_summary.get("status_by_product") or {})
    ref_by_product = dict(mail_delivery_summary.get("delivery_ref_by_product") or {})
    return {
        "date": date,
        "generated_at": generated_at,
        "source_id": source_item.get("source_id", ""),
        "title": source_item.get("title", ""),
        "queue_item_count": len(queue.get("items") or []),
        "email_status": "sent" if mail_delivery_summary.get("all_planned_products_sent") is True else notification_report.get("status", ""),
        "email_ref": notification_report.get("delivery_ref", ""),
        "planned_mail_products": list(mail_delivery_summary.get("planned_mail_products") or M1_M4_MAIL_PRODUCTS),
        "planned_mail_count": int(mail_delivery_summary.get("planned_send_total") or len(M1_M4_MAIL_PRODUCTS)),
        "sent_mail_count": int(mail_delivery_summary.get("sent_mail_count") or 0),
        "email_status_by_product": status_by_product,
        "email_ref_by_product": ref_by_product,
        "smtp_delivery_report_by_product": {
            product_id: str(run_dir / f"adp-smtp-delivery-report-{product_id}.json")
            for product_id in notification_reports
        },
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
    daily_project_root = project_root if project_root.name == "arxiv-daily-push" else project_root / "arxiv-daily-push"
    generated_at = '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'
    service_date = '$(TZ=Australia/Sydney date +"%Y-%m-%d")'
    return (
        f"cd {shlex.quote(str(project_root))} && "
        f"ADP_LOCAL_DAILY_RUN_ENABLED=true PYTHONPATH=arxiv-daily-push/src "
        f"python3 -m arxiv_daily_push local-runner daily "
        f"--project-root {shlex.quote(str(daily_project_root))} "
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
