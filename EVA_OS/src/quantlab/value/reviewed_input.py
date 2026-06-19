from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from quantlab.config import PROJECT_ROOT, REPORT_ROOT_DIR
from quantlab.value.token_roi import write_token_roi_ledger


PRIVATE_REVIEWED_INPUT_RELATIVE = "data/private/value/TokenROIReviewedValueEvidence.json"
PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE = "data/value/TokenROIReviewedValueEvidence.example.json"
REVIEWED_INPUT_SCHEMA_RELATIVE = "shared/schema/token_roi_reviewed_value_evidence.schema.json"
PRIVATE_REVIEWED_INPUT_PATH = PROJECT_ROOT / PRIVATE_REVIEWED_INPUT_RELATIVE
PUBLIC_REVIEWED_INPUT_EXAMPLE_PATH = PROJECT_ROOT / PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE


def refresh_token_roi_from_reviewed_input(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    entry_path: Path | str | None = None,
    output_dir: Path | str | None = None,
    artifact_limit: int = 300,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    reports = Path(report_root).expanduser()
    snapshot_date = _clean_date(as_of or date.today().isoformat())
    source_path = Path(entry_path).expanduser() if entry_path else root / PRIVATE_REVIEWED_INPUT_RELATIVE
    target_dir = Path(output_dir).expanduser() if output_dir else root / "data" / "value"
    if not source_path.exists():
        return _blocked_missing_input(root, reports, snapshot_date, source_path, target_dir, artifact_limit)

    payload = write_token_roi_ledger(
        as_of=snapshot_date,
        project_root=root,
        report_root=reports,
        manual_entry_path=source_path,
        output_dir=target_dir,
        artifact_limit=artifact_limit,
    )
    runtime = payload.get("runtime_summary", {}) if isinstance(payload.get("runtime_summary"), dict) else {}
    outputs = payload.get("outputs", {}) if isinstance(payload.get("outputs"), dict) else {}
    return {
        "schema": "EVATokenROIReviewedValueEvidenceRefreshV1",
        "system": "EVA_OS",
        "subsystem": "Token ROI Reviewed Value Evidence Refresh",
        "as_of": snapshot_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": str(runtime.get("status", "Blocked")),
        "roi_status": _roi_status(runtime),
        "input_status": "Present",
        "input_path": _relative_path(source_path, root),
        "report_root": _public_path(reports, root),
        "output_dir": _relative_path(target_dir, root),
        "artifact_limit": int(artifact_limit),
        "summary": {
            "record_count": runtime.get("record_count"),
            "manual_record_count": runtime.get("manual_record_count"),
            "artifact_record_count": runtime.get("artifact_record_count"),
            "quantified_records": runtime.get("quantified_records"),
            "unquantified_records": runtime.get("unquantified_records"),
            "pending_manual_records": runtime.get("pending_manual_records"),
            "pending_financial_hypothesis_count": runtime.get("pending_financial_hypothesis_count"),
            "quantified_without_evidence_count": runtime.get("quantified_without_evidence_count"),
            "financial_totals": runtime.get("financial_totals", {}),
            "manual_input_totals": runtime.get("manual_input_totals", {}),
        },
        "outputs": {key: _relative_path(Path(value), root) for key, value in outputs.items() if value},
        "runtime_summary": runtime,
        "input_contract": _input_contract(),
        "safety_boundary": _safety_boundary(),
    }


def _blocked_missing_input(
    root: Path,
    reports: Path,
    as_of: str,
    source_path: Path,
    target_dir: Path,
    artifact_limit: int,
) -> dict[str, Any]:
    return {
        "schema": "EVATokenROIReviewedValueEvidenceRefreshV1",
        "system": "EVA_OS",
        "subsystem": "Token ROI Reviewed Value Evidence Refresh",
        "as_of": as_of,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "Blocked",
        "roi_status": "MissingReviewedInput",
        "input_status": "Missing",
        "input_path": _relative_path(source_path, root),
        "report_root": _public_path(reports, root),
        "output_dir": _relative_path(target_dir, root),
        "artifact_limit": int(artifact_limit),
        "summary": {},
        "outputs": {},
        "runtime_summary": {},
        "input_contract": _input_contract(),
        "safety_boundary": _safety_boundary(),
        "next_action": "Create a local reviewed value evidence file from the public example, keep it under data/private/value, then rerun this command.",
    }


def _input_contract() -> dict[str, str]:
    return {
        "default_private_input": PRIVATE_REVIEWED_INPUT_RELATIVE,
        "public_example": PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE,
        "schema": REVIEWED_INPUT_SCHEMA_RELATIVE,
        "promotion_rule": "Only review_status=Reviewed entries with real financial fields and evidence_link/source_path are counted as Quantified.",
        "private_upload_rule": "The default reviewed value evidence input is under data/private/** and must not be committed.",
        "output_rule": "Generated outputs can contain reviewed financial totals; inspect them before committing or sharing.",
    }


def _safety_boundary() -> str:
    return (
        "Local reviewed JSON input only. No fabricated revenue, no fabricated cost saving, no fabricated avoided loss, "
        "no fabricated asset reuse value, no live trading, no real orders, no broker action, no payment, no bank transfer, "
        "and no real-money execution."
    )


def _roi_status(runtime: dict[str, Any]) -> str:
    quantified = int(runtime.get("quantified_records", 0) or 0)
    pending = int(runtime.get("pending_manual_records", 0) or 0)
    if quantified <= 0:
        return "Unquantified"
    if pending > 0 or str(runtime.get("status", "")) != "Pass":
        return "PartlyQuantified"
    return "Quantified"


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


def _public_path(path: Path, root: Path) -> str:
    try:
        return str(path.expanduser().resolve().relative_to(root.expanduser().resolve()))
    except (OSError, ValueError):
        return "external_report_root"
