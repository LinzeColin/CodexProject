from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from pfi_os.business import build_cashflow_command
from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.consumption import build_consumption_guard
from pfi_os.policy import build_policy_radar
from pfi_os.storage import atomic_write_json


@dataclass(frozen=True)
class RuntimeSummaryTarget:
    subsystem: str
    folder: str
    stem: str
    latest_name: str
    expected_schema: str
    builder: Callable[[], dict[str, Any]]


def refresh_runtime_summary_latest(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    artifact_limit: int = 300,
    lookback_days: int = 30,
    monthly_investable_budget: float = 0.0,
    cashflow_entry_path: Path | str | None = None,
    policy_entry_path: Path | str | None = None,
    consumption_event_path: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    Path(report_root).expanduser()
    cashflow_input = Path(cashflow_entry_path).expanduser() if cashflow_entry_path else None
    policy_input = Path(policy_entry_path).expanduser() if policy_entry_path else None
    consumption_input = Path(consumption_event_path).expanduser() if consumption_event_path else None
    snapshot_date = _clean_date(as_of or date.today().isoformat())
    targets = [
        RuntimeSummaryTarget(
            subsystem="Company CashFlow Command",
            folder="cashflow",
            stem="CompanyCashFlowRuntimeSummary",
            latest_name="CompanyCashFlowRuntimeSummary_latest.json",
            expected_schema="PFIOSCompanyCashFlowRuntimeSummaryV1",
            builder=lambda: build_cashflow_command(
                as_of=snapshot_date,
                project_root=root,
                entry_path=cashflow_input,
                lookback_days=lookback_days,
            ),
        ),
        RuntimeSummaryTarget(
            subsystem="Policy Intelligence Radar",
            folder="policy",
            stem="PolicyIntelligenceRuntimeSummary",
            latest_name="PolicyIntelligenceRuntimeSummary_latest.json",
            expected_schema="PFIOSPolicyIntelligenceRuntimeSummaryV1",
            builder=lambda: build_policy_radar(
                as_of=snapshot_date,
                project_root=root,
                entry_path=policy_input,
            ),
        ),
        RuntimeSummaryTarget(
            subsystem="Consumption Guard",
            folder="consumption",
            stem="ConsumptionGuardRuntimeSummary",
            latest_name="ConsumptionGuardRuntimeSummary_latest.json",
            expected_schema="PFIOSConsumptionGuardRuntimeSummaryV1",
            builder=lambda: build_consumption_guard(
                as_of=snapshot_date,
                project_root=root,
                event_path=consumption_input,
                lookback_days=lookback_days,
                monthly_investable_budget=monthly_investable_budget,
            ),
        ),
    ]
    rows = [_write_target(root, snapshot_date, target) for target in targets]
    status = "Pass" if all(row["status"] == "Pass" for row in rows) else "Blocked"
    return {
        "schema": "PFIOSRuntimeSummaryRefreshV1",
        "system": "PFI_OS",
        "subsystem": "Runtime Summary Latest Artifact Refresh",
        "as_of": snapshot_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "summary_count": len(rows),
        "runtime_summary_only": True,
        "public_upload_safety": (
            "Writes compact runtime summaries only; no full entries, opportunities, events, "
            "private holdings, raw imports, account credentials, or external execution state."
        ),
        "outputs": rows,
    }


def _write_target(root: Path, as_of: str, target: RuntimeSummaryTarget) -> dict[str, Any]:
    payload = target.builder()
    summary = dict(payload.get("runtime_summary", {}) if isinstance(payload.get("runtime_summary"), dict) else {})
    schema = str(summary.get("schema", ""))
    output_dir = root / "data" / target.folder
    output_dir.mkdir(parents=True, exist_ok=True)
    dated_path = output_dir / f"{target.stem}_{_date_stamp(as_of)}.json"
    latest_path = output_dir / target.latest_name
    summary["outputs"] = {
        "runtime_summary_json": _relative_path(dated_path, root),
        "latest_runtime_summary_json": _relative_path(latest_path, root),
    }
    status = "Pass" if schema == target.expected_schema else "Blocked"
    atomic_write_json(dated_path, summary)
    atomic_write_json(latest_path, summary)
    return {
        "subsystem": target.subsystem,
        "status": status,
        "schema": schema,
        "runtime_status": str(summary.get("status", "")),
        "runtime_summary_json": _relative_path(dated_path, root),
        "latest_runtime_summary_json": _relative_path(latest_path, root),
    }


def _clean_date(value: str) -> str:
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return date.today().isoformat()


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
