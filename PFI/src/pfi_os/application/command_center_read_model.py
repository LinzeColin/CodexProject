from __future__ import annotations

import json
from typing import Any

from pfi_os.application.operational_store import OperationalStore


def build_command_center_read_model(store: OperationalStore | None = None) -> dict[str, Any]:
    operational_store = store or OperationalStore()
    evidence_rows = [
        row
        for row in operational_store.table_rows("evidence_records")
        if str(row.get("evidence_class", "")) == "command_center_summary"
    ]
    if not evidence_rows:
        return empty_command_center_read_model()
    latest = sorted(evidence_rows, key=lambda row: (str(row.get("as_of", "")), str(row.get("created_at", ""))), reverse=True)[0]
    metadata = _json_dict(latest.get("metadata_json", "{}"))
    payload = metadata.get("command_center_read_model")
    if not isinstance(payload, dict):
        return empty_command_center_read_model()
    model = {**empty_command_center_read_model(), **payload}
    model["schema"] = "PFIOSCommandCenterReadModelV1"
    model["evidence_id"] = str(latest.get("evidence_id", ""))
    model["source_id"] = str(latest.get("source_id", ""))
    model["read_model"] = "OperationalStore -> command_center_summary evidence metadata -> PFIOSCommandCenterReadModelV1"
    model["safety_boundary"] = "Read-only UI payload; no market refresh, provider calls, broker actions, orders, payments, betting, or holdings mutation."
    return model


def empty_command_center_read_model() -> dict[str, Any]:
    return {
        "schema": "PFIOSCommandCenterReadModelV1",
        "source_schema": "",
        "system": "PFI_OS",
        "display_name": "PFI_OS",
        "subsystem": "Executive Command Center",
        "as_of": "",
        "generated_at": "",
        "command_status": "NeedsReview",
        "status_reason": "No operational command-center evidence is available.",
        "scorecards": [],
        "risk_gates": [],
        "action_queue": [],
        "latest_report": {},
        "evidence_sources": [],
        "runtime_summary_sources": [],
        "business_system_summary": [],
        "source_uri": "",
        "evidence_id": "",
        "source_id": "",
        "read_policy": "Operational Store read model; sanitized from command-center cache without private absolute paths.",
        "read_model": "OperationalStore -> command_center_summary evidence metadata -> PFIOSCommandCenterReadModelV1",
        "safety_boundary": "Read-only UI payload; no market refresh, provider calls, broker actions, orders, payments, betting, or holdings mutation.",
    }


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
