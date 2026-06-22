"""Two-day Phase 11 simulation gate."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .production_preflight import PRODUCTION_REQUIRED_COMMANDS, PRODUCTION_SECRET_ENV_KEYS, build_production_preflight
from .scheduled_execution import run_scheduled_execution, validate_scheduled_execution_report
from .trial_ledger import update_trial_evidence_ledger, validate_trial_ledger_update_report


TWO_DAY_SIMULATION_MODEL_ID = "adp-two-day-simulation-v1"
TWO_DAY_SIMULATION_DAYS_REQUIRED = 2


def run_two_day_simulation(
    *,
    generated_at: str,
    start_date: str,
    path: Path | str | None = None,
) -> dict[str, Any]:
    """Run a no-network, no-real-side-effect two-day scheduled-path simulation."""

    root = Path(path or ".").resolve()
    dates, date_errors = _simulation_dates(start_date)
    if date_errors:
        return _blocked(generated_at=generated_at, start_date=start_date, reasons=date_errors)

    env = _simulation_env()
    preflight = build_production_preflight(
        root,
        generated_at=generated_at,
        env=env,
        command_resolver=_simulation_command_resolver,
        disk_free_gib=120.0,
        memory_total_gib=16.0,
        git_scan={"gate_id": "git_artifact_hygiene", "passed": True, "blocking_reasons": [], "violations": []},
    )
    ledger_state: Mapping[str, Any] | None = None
    scheduled_reports: list[dict[str, Any]] = []
    ledger_reports: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="adp_two_day_simulation_") as tmp:
        tmp_path = Path(tmp)
        for index, day in enumerate(dates, start=1):
            day_generated_at = f"{day.isoformat()}T05:00:00+10:00"
            daily_input = _daily_input(day, index=index, generated_at=day_generated_at)
            asset = tmp_path / f"adp-two-day-simulation-{day.isoformat()}.json"
            video_asset = tmp_path / f"adp-two-day-simulation-video-{day.isoformat()}.mp4"
            asset.write_text(json.dumps(daily_input, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            video_asset.write_bytes("\x00\x00\x00\x18ftypmp42simulation-video".encode("ascii"))
            scheduled = run_scheduled_execution(
                mode="daily-run",
                generated_at=day_generated_at,
                preflight_report=preflight,
                env=env,
                daily_input=daily_input,
                release_asset_paths=[asset, video_asset],
                smtp_factory=_FakeSMTP,
                release_command_resolver=lambda _name: "/usr/bin/gh",
                release_command_runner=lambda _command: {"returncode": 0},
            )
            ledger = update_trial_evidence_ledger(
                ledger_state,
                scheduled,
                generated_at=f"{day.isoformat()}T06:00:00+10:00",
                trial_id="adp-two-day-simulation",
                trial_ref=f"simulation://arxiv-daily-push/two-day/{start_date}",
                expected_days=TWO_DAY_SIMULATION_DAYS_REQUIRED,
                text_degradation_path_verified=True,
                video_degradation_path_verified=True,
                scheduler_enabled=True,
                manual_rerun_verified=True,
                scheduler_ref=f"simulation://arxiv-daily-push/scheduler/{start_date}",
                private_release_verified=True,
                release_ref=f"simulation://arxiv-daily-push/release/{start_date}",
                real_smtp_verified=True,
                email_ref=f"simulation://arxiv-daily-push/email/{start_date}",
                resource_pressure_ok=True,
                resource_ref=f"simulation://arxiv-daily-push/resource/{start_date}",
            )
            scheduled_reports.append(scheduled)
            ledger_reports.append(ledger)
            if ledger.get("ledger_updated") is True and isinstance(ledger.get("trial_evidence"), Mapping):
                ledger_state = ledger["trial_evidence"]

    gates = _simulation_gates(preflight, scheduled_reports, ledger_reports, ledger_state)
    blocking_reasons = [
        reason
        for gate in gates
        for reason in gate["blocking_reasons"]
        if gate.get("passed") is not True
    ]
    ready = not blocking_reasons
    report = {
        "simulation_id": f"two-day-simulation:arxiv-daily-push:{start_date}",
        "model_id": TWO_DAY_SIMULATION_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "start_date": start_date,
        "timezone": DEFAULT_TIMEZONE,
        "recipient": DEFAULT_RECIPIENT,
        "simulation_days_required": TWO_DAY_SIMULATION_DAYS_REQUIRED,
        "observed_day_count": len((ledger_state or {}).get("daily_runs") or []),
        "status": "pass" if ready else "blocked",
        "two_day_simulation_ready": ready,
        "accepted_for_production": False,
        "production_acceptance_claimed": False,
        "side_effects_performed": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "secret_values_logged": False,
        "codex_auth_read": False,
        "network_fetch_performed": False,
        "simulation_policy": {
            "smtp": "mocked",
            "release": "mocked",
            "preflight": "simulated_pass_with_no_secret_values",
            "local_temp_assets_removed": True,
            "production_acceptance_claimed": False,
        },
        "gates": gates,
        "blocking_reasons": blocking_reasons,
        "scheduled_execution_summaries": [_scheduled_summary(report) for report in scheduled_reports],
        "ledger_update_summaries": [_ledger_summary(report) for report in ledger_reports],
        "trial_evidence": dict(ledger_state or {}),
    }
    return _with_validation(report)


def validate_two_day_simulation_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != TWO_DAY_SIMULATION_MODEL_ID:
        errors.append("two-day simulation model_id must be adp-two-day-simulation-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("two-day simulation status must be pass or blocked")
    if report.get("two_day_simulation_ready") not in {True, False}:
        errors.append("two-day simulation requires two_day_simulation_ready boolean")
    if report.get("simulation_days_required") != TWO_DAY_SIMULATION_DAYS_REQUIRED:
        errors.append("two-day simulation requires exactly two simulation days")
    for key in (
        "accepted_for_production",
        "production_acceptance_claimed",
        "side_effects_performed",
        "real_smtp_sent",
        "real_release_uploaded",
        "secret_values_logged",
        "codex_auth_read",
        "network_fetch_performed",
    ):
        if report.get(key) is not False:
            errors.append(f"two-day simulation {key} must be false")
    gates = report.get("gates")
    if not isinstance(gates, list) or not gates:
        errors.append("two-day simulation requires gates list")
        return errors
    failed = [
        str(gate.get("gate_id"))
        for gate in gates
        if isinstance(gate, Mapping) and gate.get("passed") is not True
    ]
    if report.get("status") == "pass":
        if report.get("two_day_simulation_ready") is not True:
            errors.append("passing two-day simulation requires two_day_simulation_ready true")
        if report.get("observed_day_count") != TWO_DAY_SIMULATION_DAYS_REQUIRED:
            errors.append("passing two-day simulation requires two observed days")
        if failed:
            errors.append("passing two-day simulation cannot include failed gates: " + ", ".join(failed))
        if report.get("blocking_reasons"):
            errors.append("passing two-day simulation cannot include blocking_reasons")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked two-day simulation requires blocking_reasons")
    return errors


class _FakeSMTP:
    sent_messages: list[EmailMessage] = []

    def __init__(self, host: str, port: int, timeout: int) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def __enter__(self) -> "_FakeSMTP":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False

    def starttls(self) -> None:
        return None

    def login(self, username: str, password: str) -> None:
        return None

    def send_message(self, message: EmailMessage) -> dict[str, Any]:
        self.sent_messages.append(message)
        return {}


def _simulation_dates(start_date: str) -> tuple[list[date], list[str]]:
    try:
        first = date.fromisoformat(str(start_date or ""))
    except ValueError:
        return [], ["start_date must be ISO YYYY-MM-DD"]
    return [first, first + timedelta(days=1)], []


def _simulation_env() -> dict[str, str]:
    env = {key: f"configured-{key.lower()}" for key in PRODUCTION_SECRET_ENV_KEYS}
    env.update(
        {
            "ADP_SMTP_HOST": "smtp.example.invalid",
            "ADP_SMTP_PORT": "587",
            "ADP_SMTP_USERNAME": "sender@example.invalid",
            "ADP_SMTP_PASSWORD": "configured-adp-smtp-password",
            "ADP_RELEASE_TARGET": "simulation-target",
            "ADP_SCHEDULED_RUN_ENABLED": "true",
            "ADP_ALLOW_SMTP_SEND": "true",
            "ADP_ALLOW_RELEASE_UPLOAD": "true",
        }
    )
    return env


def _simulation_command_resolver(command: str) -> str | None:
    return f"/simulation/bin/{command}" if command in PRODUCTION_REQUIRED_COMMANDS else None


def _daily_input(day: date, *, index: int, generated_at: str) -> dict[str, Any]:
    stable_id = f"2606.{index:05d}"
    source_id = f"arxiv:{stable_id}"
    canonical = f"https://arxiv.org/abs/{stable_id}"
    primary_category = "stat.ML" if index % 2 else "q-fin.PM"
    return {
        "run_id": f"simulation-daily:{day.isoformat()}:{source_id}",
        "publication_id": f"pub:simulation:{day.isoformat()}:{source_id}",
        "date": day.isoformat(),
        "generated_at": generated_at,
        "timezone": DEFAULT_TIMEZONE,
        "source_item": {
            "source_id": source_id,
            "source_type": "arxiv",
            "source_adapter": "arxiv.atom.v1",
            "stable_id": stable_id,
            "title": f"Two-day simulation paper {index}",
            "retrieved_at": generated_at,
            "canonical_url": canonical,
            "metadata": {
                "arxiv": {
                    "primary_category": primary_category,
                    "categories": [primary_category],
                    "published": datetime.combine(day, datetime.min.time()).isoformat() + "Z",
                }
            },
            "content_refs": [{"ref_id": "abstract", "ref_type": "html", "uri": canonical}],
            "license": {"status": "unknown", "usage": "private_learning_link_only"},
        },
        "claims": [
            {
                "claim_type": "reported_result",
                "priority": "P0",
                "statement": f"The day {index} simulation abstract reports an evidence-grounded AI learning item.",
                "locator": {"locator_type": "abstract", "stable_url": canonical, "section": "abstract"},
                "support_status": "supported",
            },
            {
                "claim_type": "metadata",
                "priority": "P1",
                "statement": "The selected item is treated as an arXiv preprint.",
                "locator": {"locator_type": "metadata", "stable_url": canonical},
                "support_status": "supported",
            },
        ],
        "queue_summary": {
            "queue_model_id": "adp-candidate-queue-v1",
            "queued_item_count": 1,
            "top_queued": [
                {
                    "source_id": f"arxiv:queued-{index}",
                    "title": "Simulation queued all-arXiv high-value candidate",
                    "roi_total_score": 72.0,
                    "primary_category": "q-bio.NC" if index % 2 else "econ.EM",
                }
            ],
        },
    }


def _simulation_gates(
    preflight: Mapping[str, Any],
    scheduled_reports: Sequence[Mapping[str, Any]],
    ledger_reports: Sequence[Mapping[str, Any]],
    ledger_state: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    scheduled_errors = [
        f"scheduled[{index}]: {error}"
        for index, report in enumerate(scheduled_reports)
        for error in validate_scheduled_execution_report(report)
    ]
    ledger_errors = [
        f"ledger[{index}]: {error}"
        for index, report in enumerate(ledger_reports)
        for error in validate_trial_ledger_update_report(report)
    ]
    daily_runs = list((ledger_state or {}).get("daily_runs") or [])
    dates = [str(run.get("date") or "") for run in daily_runs if isinstance(run, Mapping)]
    source_ids = [str(run.get("source_id") or "") for run in daily_runs if isinstance(run, Mapping)]
    publication_ids = [str(run.get("publication_id") or "") for run in daily_runs if isinstance(run, Mapping)]
    secret_text = json.dumps(
        {
            "scheduled": scheduled_reports,
            "ledger": ledger_reports,
            "trial_evidence": ledger_state or {},
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return [
        _gate(
            "simulated_preflight_passed",
            preflight.get("production_run_allowed") is True,
            list(preflight.get("blocking_reasons") or ["simulated preflight did not pass"]),
        ),
        _gate(
            "two_scheduled_daily_runs_succeeded",
            len(scheduled_reports) == TWO_DAY_SIMULATION_DAYS_REQUIRED
            and all(report.get("status") == "succeeded" and report.get("production_evidence_ready") is True for report in scheduled_reports),
            ["both simulated scheduled daily-runs must succeed with production_evidence_ready=true"],
        ),
        _gate("scheduled_reports_valid", not scheduled_errors, scheduled_errors),
        _gate(
            "two_ledger_updates_passed",
            len(ledger_reports) == TWO_DAY_SIMULATION_DAYS_REQUIRED
            and all(report.get("ledger_updated") is True for report in ledger_reports),
            ["both simulated daily runs must append to the trial ledger"],
        ),
        _gate("ledger_reports_valid", not ledger_errors, ledger_errors),
        _gate(
            "two_unique_days_sources_publications",
            len(set(dates)) == TWO_DAY_SIMULATION_DAYS_REQUIRED
            and len(set(source_ids)) == TWO_DAY_SIMULATION_DAYS_REQUIRED
            and len(set(publication_ids)) == TWO_DAY_SIMULATION_DAYS_REQUIRED,
            ["simulation must produce two unique dates, source IDs, and publication IDs"],
        ),
        _gate(
            "no_secret_values_logged",
            "configured-adp-smtp-password" not in secret_text,
            ["simulation report must not include configured SMTP password value"],
        ),
        _gate("no_production_acceptance_claimed", True, []),
    ]


def _scheduled_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    daily = report.get("daily_run_report") if isinstance(report.get("daily_run_report"), Mapping) else {}
    refs = report.get("evidence_refs") if isinstance(report.get("evidence_refs"), Mapping) else {}
    return {
        "execution_id": report.get("execution_id"),
        "date": daily.get("date"),
        "status": report.get("status"),
        "exit_code": report.get("exit_code"),
        "production_evidence_ready": report.get("production_evidence_ready"),
        "source_id": daily.get("source_id"),
        "publication_id": daily.get("publication_id"),
        "release_ref_present": bool(refs.get("release_ref")),
        "email_ref_present": bool(refs.get("email_ref")),
        "resource_gate_ref_present": bool(refs.get("resource_gate_ref")),
    }


def _ledger_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    daily = report.get("daily_entry") if isinstance(report.get("daily_entry"), Mapping) else {}
    return {
        "ledger_update_id": report.get("ledger_update_id"),
        "status": report.get("status"),
        "ledger_updated": report.get("ledger_updated"),
        "observed_day_count": report.get("observed_day_count"),
        "accepted_for_production": report.get("accepted_for_production"),
        "date": daily.get("date"),
        "source_id": daily.get("source_id"),
        "publication_id": daily.get("publication_id"),
    }


def _gate(gate_id: str, passed: bool, reasons: Sequence[str]) -> dict[str, Any]:
    return {"gate_id": gate_id, "passed": bool(passed), "blocking_reasons": [] if passed else list(reasons)}


def _blocked(*, generated_at: str, start_date: str, reasons: Sequence[str]) -> dict[str, Any]:
    report = {
        "simulation_id": f"two-day-simulation:arxiv-daily-push:{start_date or 'invalid'}",
        "model_id": TWO_DAY_SIMULATION_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "start_date": start_date,
        "timezone": DEFAULT_TIMEZONE,
        "recipient": DEFAULT_RECIPIENT,
        "simulation_days_required": TWO_DAY_SIMULATION_DAYS_REQUIRED,
        "observed_day_count": 0,
        "status": "blocked",
        "two_day_simulation_ready": False,
        "accepted_for_production": False,
        "production_acceptance_claimed": False,
        "side_effects_performed": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "secret_values_logged": False,
        "codex_auth_read": False,
        "network_fetch_performed": False,
        "simulation_policy": {
            "smtp": "not_started",
            "release": "not_started",
            "preflight": "not_started",
            "local_temp_assets_removed": True,
            "production_acceptance_claimed": False,
        },
        "gates": [_gate("start_date_valid", False, list(reasons))],
        "blocking_reasons": list(reasons),
        "scheduled_execution_summaries": [],
        "ledger_update_summaries": [],
        "trial_evidence": {},
    }
    return _with_validation(report)


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_two_day_simulation_report(normalized)
    return normalized
