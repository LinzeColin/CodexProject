from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import DataDomain, EvidenceRecord, JobRecord, OperationalStore, SourceRecord, TaskRecord


SCHEMA = "PFIOSHomepageCacheIngestionV1"
RETIRED_COMMAND_CENTER_FRAGMENTS = (
    "Token" + " ROI",
    "E" + "VA" + "Token",
    "E" + "VA" + "CommandCenter",
    "E" + "VA" + "_OS",
    "E" + "VA" + " OS",
)


def ingest_command_center_cache(
    store: OperationalStore,
    *,
    project_root: Path | str,
    cache_path: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve(strict=False)
    resolved_cache = _resolve_cache_path(root, cache_path)
    if resolved_cache is None:
        return {
            "schema": SCHEMA,
            "status": "Skipped",
            "reason": "No command-center latest cache found.",
            "source_id": "",
            "evidence_id": "",
            "task_id": "",
        }

    payload_text = resolved_cache.read_text(encoding="utf-8")
    payload = json.loads(payload_text)
    relative_uri = _relative_uri(root, resolved_cache)
    checksum = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    as_of = _payload_as_of(payload)
    source_id = _stable_id("src_command_center", relative_uri, as_of, checksum)
    evidence_id = _stable_id("ev_command_center", source_id, as_of, payload.get("command_status", ""))
    source = SourceRecord(
        source_id=source_id,
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="command_center_cache",
        uri=relative_uri,
        as_of=as_of,
        evidence_class="local_operational_cache",
        title="PFI command center latest cache",
        checksum=checksum,
        metadata=_cache_metadata(payload, relative_uri),
    )
    store.upsert_source(source)
    evidence = EvidenceRecord(
        evidence_id=evidence_id,
        source_id=source_id,
        entity_id="PFI_OS",
        as_of=as_of,
        evidence_class="command_center_summary",
        summary=_evidence_summary(payload),
        artifact_uri=relative_uri,
        model_version="DisabledProvider",
        metadata=_cache_metadata(payload, relative_uri),
    )
    store.record_evidence(evidence)
    job_id = _stable_id("job_ingest_homepage", source_id, as_of)
    store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_id,
            as_of=as_of,
            job_type="ingest_command_center_cache",
            status="completed",
            phase="done",
            progress=1.0,
            artifact_uri=relative_uri,
            metadata=_cache_metadata(payload, relative_uri),
        )
    )
    task_id = _upsert_first_action_task(store, payload, source_id=source_id, evidence_id=evidence_id, as_of=as_of)
    return {
        "schema": SCHEMA,
        "status": "Ingested",
        "source_id": source_id,
        "evidence_id": evidence_id,
        "job_id": job_id,
        "task_id": task_id,
        "uri": relative_uri,
        "checksum": checksum,
    }


def _resolve_cache_path(root: Path, cache_path: Path | str | None) -> Path | None:
    if cache_path is not None:
        return Path(cache_path).expanduser().resolve(strict=False)
    command_center = root / "data" / "commandCenter"
    preferred = command_center / "PFICommandCenter_latest.json"
    if preferred.exists():
        return preferred.resolve(strict=False)
    return None


def _relative_uri(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _payload_as_of(payload: dict[str, Any]) -> str:
    generated_at = str(payload.get("generated_at", "")).strip()
    if generated_at:
        return generated_at
    as_of = str(payload.get("as_of", "")).strip()
    return as_of or "missing"


def _cache_metadata(payload: dict[str, Any], relative_uri: str) -> dict[str, Any]:
    scorecards = _sanitize_rows(payload.get("scorecards", []), limit=12)
    risk_gates = _sanitize_rows(payload.get("risk_gates", []), limit=12)
    action_queue = _sanitize_rows(payload.get("action_queue", []), limit=12)
    return {
        "source_adapter": "command_center_cache",
        "schema": str(_sanitize_value(payload.get("schema", ""))),
        "command_status": str(_sanitize_value(payload.get("command_status", ""))),
        "scorecard_count": len(scorecards),
        "risk_gate_count": len(risk_gates),
        "action_count": len(action_queue),
        "artifact_uri": relative_uri,
        "command_center_read_model": _sanitize_command_center_payload(payload, relative_uri),
    }


def _evidence_summary(payload: dict[str, Any]) -> str:
    status = str(payload.get("command_status", "") or "Missing")
    reason = str(payload.get("status_reason", "") or "No status reason recorded.")
    return f"Command center status {status}: {reason}"


def _sanitize_command_center_payload(payload: dict[str, Any], relative_uri: str) -> dict[str, Any]:
    return {
        "schema": "PFIOSCommandCenterReadModelV1",
        "source_schema": str(_sanitize_value(payload.get("schema", ""))),
        "system": str(_sanitize_value(payload.get("system", ""))),
        "display_name": str(_sanitize_value(payload.get("display_name", ""))),
        "subsystem": str(_sanitize_value(payload.get("subsystem", ""))),
        "as_of": str(_sanitize_value(payload.get("as_of", ""))),
        "generated_at": str(_sanitize_value(payload.get("generated_at", ""))),
        "command_status": str(_sanitize_value(payload.get("command_status", "NeedsReview"))),
        "status_reason": str(_sanitize_value(payload.get("status_reason", ""))),
        "scorecards": _sanitize_rows(payload.get("scorecards", []), limit=12),
        "risk_gates": _sanitize_rows(payload.get("risk_gates", []), limit=12),
        "action_queue": _sanitize_rows(payload.get("action_queue", []), limit=12),
        "latest_report": _sanitize_dict(payload.get("latest_report", {})),
        "evidence_sources": _sanitize_rows(payload.get("evidence_sources", []), limit=16),
        "runtime_summary_sources": _sanitize_rows(payload.get("runtime_summary_sources", []), limit=16),
        "business_system_summary": _sanitize_rows(payload.get("business_system_summary", []), limit=12),
        "source_uri": relative_uri,
        "read_policy": "Operational Store read model; sanitized from command-center cache without private absolute paths.",
    }


def _sanitize_rows(rows: Any, *, limit: int) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    sanitized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or _contains_retired_reference(row):
            continue
        sanitized.append(_sanitize_dict(row))
        if len(sanitized) >= limit:
            break
    return sanitized


def _sanitize_dict(row: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, dict):
            sanitized[str(key)] = _sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[str(key)] = [
                _sanitize_dict(item) if isinstance(item, dict) else _sanitize_value(item)
                for item in value[:16]
            ]
        else:
            sanitized[str(key)] = _sanitize_value(value)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("/Users/") or value.startswith("/private/") or value.startswith("~"):
            return "[redacted-private-uri]"
        if _contains_retired_reference(value):
            return "[retired-legacy-reference-hidden]"
    return value


def _contains_retired_reference(value: Any) -> bool:
    if isinstance(value, str):
        return any(fragment in value for fragment in RETIRED_COMMAND_CENTER_FRAGMENTS)
    if isinstance(value, dict):
        return any(_contains_retired_reference(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_retired_reference(item) for item in value)
    return False


def _upsert_first_action_task(
    store: OperationalStore,
    payload: dict[str, Any],
    *,
    source_id: str,
    evidence_id: str,
    as_of: str,
) -> str:
    actions = [
        row
        for row in payload.get("action_queue", []) or []
        if isinstance(row, dict) and not _contains_retired_reference(row)
    ]
    if not actions:
        return ""
    first = actions[0]
    task_id = _stable_id("task_command_center", source_id, evidence_id, str(first.get("action", "")))
    store.upsert_task(
        TaskRecord(
            task_id=task_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace="home",
            action=str(first.get("action", "") or "Review command center action queue."),
            status=str(first.get("status", "") or "open").lower(),
            priority=str(first.get("priority", "") or "P1"),
            human_review_required=True,
            metadata={
                "source_adapter": "command_center_cache",
                "source": str(first.get("source", "")),
                "owner": str(first.get("owner", "")),
            },
        )
    )
    return task_id


def _stable_id(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
