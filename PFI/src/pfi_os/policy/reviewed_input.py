from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT
from pfi_os.policy.radar import write_policy_radar


PRIVATE_REVIEWED_INPUT_RELATIVE = "data/private/policy/PolicyReviewedInput.json"
PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE = "data/policy/PolicyReviewedInput.example.json"
REVIEWED_INPUT_SCHEMA_RELATIVE = "shared/schema/policy_reviewed_input.schema.json"
PRIVATE_REVIEWED_INPUT_PATH = PROJECT_ROOT / PRIVATE_REVIEWED_INPUT_RELATIVE
PUBLIC_REVIEWED_INPUT_EXAMPLE_PATH = PROJECT_ROOT / PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE


def refresh_policy_from_reviewed_input(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    entry_path: Path | str | None = None,
    output_dir: Path | str | None = None,
    opportunity_limit: int = 300,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    snapshot_date = _clean_date(as_of or date.today().isoformat())
    source_path = Path(entry_path).expanduser() if entry_path else root / PRIVATE_REVIEWED_INPUT_RELATIVE
    target_dir = Path(output_dir).expanduser() if output_dir else root / "data" / "policy"
    if not source_path.exists():
        return _blocked_missing_input(root, snapshot_date, source_path, target_dir, opportunity_limit)

    payload = write_policy_radar(
        as_of=snapshot_date,
        project_root=root,
        entry_path=source_path,
        output_dir=target_dir,
        opportunity_limit=opportunity_limit,
    )
    runtime = payload.get("runtime_summary", {}) if isinstance(payload.get("runtime_summary"), dict) else {}
    outputs = payload.get("outputs", {}) if isinstance(payload.get("outputs"), dict) else {}
    return {
        "schema": "PFIOSPolicyReviewedInputRefreshV1",
        "system": "PFI_OS",
        "subsystem": "Policy Intelligence Reviewed Input Refresh",
        "as_of": snapshot_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": str(runtime.get("status", "Blocked")),
        "policy_status": str(payload.get("policy_status", "")),
        "input_status": "Present",
        "input_path": _relative_path(source_path, root),
        "output_dir": _relative_path(target_dir, root),
        "opportunity_limit": int(opportunity_limit),
        "summary": {
            "opportunity_count": runtime.get("opportunity_count"),
            "actionable_count": runtime.get("actionable_count"),
            "watch_count": runtime.get("watch_count"),
            "observe_count": runtime.get("observe_count"),
            "missing_evidence_count": runtime.get("missing_evidence_count"),
            "pending_review_count": runtime.get("pending_review_count"),
            "authoritative_source_records": runtime.get("authoritative_source_records"),
            "max_impact_score": runtime.get("max_impact_score"),
        },
        "outputs": {key: _relative_path(Path(value), root) for key, value in outputs.items() if value},
        "runtime_summary": runtime,
        "input_contract": _input_contract(),
        "safety_boundary": _safety_boundary(),
    }


def _blocked_missing_input(root: Path, as_of: str, source_path: Path, target_dir: Path, opportunity_limit: int) -> dict[str, Any]:
    return {
        "schema": "PFIOSPolicyReviewedInputRefreshV1",
        "system": "PFI_OS",
        "subsystem": "Policy Intelligence Reviewed Input Refresh",
        "as_of": as_of,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "Blocked",
        "policy_status": "MissingReviewedInput",
        "input_status": "Missing",
        "input_path": _relative_path(source_path, root),
        "output_dir": _relative_path(target_dir, root),
        "opportunity_limit": int(opportunity_limit),
        "summary": {},
        "outputs": {},
        "runtime_summary": {},
        "input_contract": _input_contract(),
        "safety_boundary": _safety_boundary(),
        "next_action": "Create a local reviewed input file from the public example, keep it under data/private/policy, then rerun this command.",
    }


def _input_contract() -> dict[str, str]:
    return {
        "default_private_input": PRIVATE_REVIEWED_INPUT_RELATIVE,
        "public_example": PUBLIC_REVIEWED_INPUT_EXAMPLE_RELATIVE,
        "schema": REVIEWED_INPUT_SCHEMA_RELATIVE,
        "promotion_rule": "Only Reviewed opportunities with Official/Regulator/Government/Exchange source type, source_url/evidence_path, and high impact can become Actionable.",
        "private_upload_rule": "The default reviewed input is under data/private/** and must not be committed.",
    }


def _safety_boundary() -> str:
    return (
        "Local reviewed JSON input only. No live policy scraping, no government-portal login, no application submission, "
        "no payment, no legal/tax/compliance/subsidy conclusion, no investment conclusion, and no trading execution."
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
