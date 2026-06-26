from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT
from pfi_os.consumption.guard import write_consumption_guard


PRIVATE_REVIEWED_INPUT_RELATIVE = "data/private/consumption/ConsumptionGuardReviewedInput.json"
PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE = "data/consumption/ConsumptionGuardReviewedInput.example.json"
REVIEWED_INPUT_SCHEMA_RELATIVE = "shared/schema/consumption_guard_reviewed_input.schema.json"
PRIVATE_REVIEWED_INPUT_PATH = PROJECT_ROOT / PRIVATE_REVIEWED_INPUT_RELATIVE
PUBLIC_REVIEWED_INPUT_EXAMPLE_PATH = PROJECT_ROOT / PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE


def refresh_consumption_from_reviewed_input(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    event_path: Path | str | None = None,
    output_dir: Path | str | None = None,
    lookback_days: int = 30,
    monthly_investable_budget: float = 0.0,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    snapshot_date = _clean_date(as_of or date.today().isoformat())
    source_path = Path(event_path).expanduser() if event_path else root / PRIVATE_REVIEWED_INPUT_RELATIVE
    target_dir = Path(output_dir).expanduser() if output_dir else root / "data" / "consumption"
    if not source_path.exists():
        return _blocked_missing_input(root, snapshot_date, source_path, target_dir, lookback_days, monthly_investable_budget)

    payload = write_consumption_guard(
        as_of=snapshot_date,
        project_root=root,
        event_path=source_path,
        output_dir=target_dir,
        lookback_days=lookback_days,
        monthly_investable_budget=monthly_investable_budget,
    )
    runtime = payload.get("runtime_summary", {}) if isinstance(payload.get("runtime_summary"), dict) else {}
    outputs = payload.get("outputs", {}) if isinstance(payload.get("outputs"), dict) else {}
    return {
        "schema": "PFIOSConsumptionGuardReviewedInputRefreshV1",
        "system": "PFI_OS",
        "subsystem": "Consumption Guard Reviewed Input Refresh",
        "as_of": snapshot_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": str(runtime.get("status", "Blocked")),
        "guard_status": str(payload.get("guard_status", "")),
        "input_status": "Present",
        "input_path": _relative_path(source_path, root),
        "output_dir": _relative_path(target_dir, root),
        "lookback_days": int(payload.get("lookback_days", lookback_days) or lookback_days),
        "monthly_investable_budget": float(payload.get("monthly_investable_budget", monthly_investable_budget) or 0.0),
        "summary": {
            "event_count": runtime.get("event_count"),
            "counted_records": runtime.get("counted_records"),
            "pending_review_records": runtime.get("pending_review_records"),
            "reviewed_missing_evidence_records": runtime.get("reviewed_missing_evidence_records"),
            "counted_spend": runtime.get("counted_spend"),
            "impulse_spend": runtime.get("impulse_spend"),
            "fixed_cost": runtime.get("fixed_cost"),
            "high_risk_event_count": runtime.get("high_risk_event_count"),
            "investable_cashflow_pressure": runtime.get("investable_cashflow_pressure"),
        },
        "outputs": {key: _relative_path(Path(value), root) for key, value in outputs.items() if value},
        "runtime_summary": runtime,
        "input_contract": _input_contract(),
        "safety_boundary": _safety_boundary(),
    }


def _blocked_missing_input(
    root: Path,
    as_of: str,
    source_path: Path,
    target_dir: Path,
    lookback_days: int,
    monthly_investable_budget: float,
) -> dict[str, Any]:
    return {
        "schema": "PFIOSConsumptionGuardReviewedInputRefreshV1",
        "system": "PFI_OS",
        "subsystem": "Consumption Guard Reviewed Input Refresh",
        "as_of": as_of,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "Blocked",
        "guard_status": "MissingReviewedInput",
        "input_status": "Missing",
        "input_path": _relative_path(source_path, root),
        "output_dir": _relative_path(target_dir, root),
        "lookback_days": int(lookback_days),
        "monthly_investable_budget": float(monthly_investable_budget or 0.0),
        "summary": {},
        "outputs": {},
        "runtime_summary": {},
        "input_contract": _input_contract(),
        "safety_boundary": _safety_boundary(),
        "next_action": "Create a local reviewed input file from the public example, keep it under data/private/consumption, then rerun this command.",
    }


def _input_contract() -> dict[str, str]:
    return {
        "default_private_input": PRIVATE_REVIEWED_INPUT_RELATIVE,
        "public_example": PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE,
        "schema": REVIEWED_INPUT_SCHEMA_RELATIVE,
        "counting_rule": "Only review_status=Reviewed and evidence_link/evidence_path present are counted.",
        "private_upload_rule": "The default reviewed input is under data/private/** and must not be committed.",
    }


def _safety_boundary() -> str:
    return (
        "Local reviewed JSON input only. No Alipay login, no bank login, no payroll or tax access, "
        "no payment-system login, no payment, no transfer, no refund, no account freeze, no broker action, "
        "and no real-money execution."
    )


def _clean_date(value: str) -> str:
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return date.today().isoformat()


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.expanduser().resolve().relative_to(root.expanduser().resolve()))
    except (OSError, ValueError):
        return str(path)
