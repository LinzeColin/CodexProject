from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import DataDomain, EvidenceRecord, JobRecord, OperationalStore, SourceRecord, TaskRecord


SCHEMA = "PFIOSMacOSRuntimeCacheIngestionV1"
RUNTIME_SOURCE_TYPE = "macos_runtime_acceptance_cache"
RUNTIME_EVIDENCE_CLASS = "macos_runtime_acceptance_summary"
DEFAULT_RUNTIME_CACHE = Path("data") / "systemAudit" / "MacOSRuntimeAcceptance_latest.json"


def ingest_macos_runtime_acceptance_cache(
    store: OperationalStore,
    *,
    project_root: Path | str,
    cache_path: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve(strict=False)
    resolved_cache = _resolve_cache_path(root, cache_path)
    if resolved_cache is None:
        return _skipped_result("No macOS runtime acceptance latest cache found.")

    payload_text = resolved_cache.read_text(encoding="utf-8")
    payload = json.loads(payload_text)
    if payload.get("schema") != "PFIOSMacOSRuntimeAcceptanceV1":
        return _skipped_result("macOS runtime acceptance cache schema is not supported.")

    relative_uri = _relative_uri(root, resolved_cache)
    checksum = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    as_of = str(payload.get("generated_at", "") or "missing")
    read_model = _sanitize_runtime_payload(payload, relative_uri)
    source_id = _stable_id("src_macos_runtime", RUNTIME_SOURCE_TYPE, relative_uri, as_of, checksum)
    store.upsert_source(
        SourceRecord(
            source_id=source_id,
            domain=DataDomain.PRIVATE_DERIVED,
            source_type=RUNTIME_SOURCE_TYPE,
            uri=relative_uri,
            as_of=as_of,
            evidence_class="local_runtime_acceptance_cache",
            title="macOS runtime acceptance latest cache",
            checksum=checksum,
            metadata=_cache_metadata(payload, relative_uri, read_model),
        )
    )
    evidence_id = _stable_id("ev_macos_runtime", source_id, as_of, read_model.get("status", ""))
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source_id,
            entity_id="PFI_OS",
            as_of=as_of,
            evidence_class=RUNTIME_EVIDENCE_CLASS,
            summary=_evidence_summary(payload),
            artifact_uri=relative_uri,
            model_version="DisabledProvider",
            metadata=_cache_metadata(payload, relative_uri, read_model),
        )
    )
    job_id = _stable_id("job_ingest_macos_runtime", source_id, as_of)
    store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_id,
            as_of=as_of,
            job_type="ingest_macos_runtime_acceptance_cache",
            status="completed",
            phase="done",
            progress=1.0,
            artifact_uri=relative_uri,
            metadata=_cache_metadata(payload, relative_uri, read_model),
        )
    )
    task_id = _upsert_review_task(store, payload, source_id=source_id, evidence_id=evidence_id, as_of=as_of)
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


def build_macos_runtime_acceptance_read_model(store: OperationalStore | None = None) -> dict[str, Any]:
    operational_store = store or OperationalStore()
    evidence_rows = [
        row
        for row in operational_store.table_rows("evidence_records")
        if str(row.get("evidence_class", "")) == RUNTIME_EVIDENCE_CLASS
    ]
    if not evidence_rows:
        return empty_macos_runtime_acceptance_read_model()
    latest = sorted(evidence_rows, key=lambda row: (str(row.get("as_of", "")), str(row.get("created_at", ""))), reverse=True)[0]
    metadata = _json_dict(latest.get("metadata_json", "{}"))
    payload = metadata.get("macos_runtime_read_model")
    if not isinstance(payload, dict):
        return empty_macos_runtime_acceptance_read_model()
    model = {**empty_macos_runtime_acceptance_read_model(), **payload}
    model["schema"] = "PFIOSMacOSRuntimeAcceptanceV1"
    model["evidence_id"] = str(latest.get("evidence_id", ""))
    model["source_id"] = str(latest.get("source_id", ""))
    model["read_model"] = (
        "OperationalStore -> macos_runtime_acceptance_summary evidence metadata -> PFIOSMacOSRuntimeAcceptanceV1"
    )
    return model


def empty_macos_runtime_acceptance_read_model() -> dict[str, Any]:
    return {
        "schema": "PFIOSMacOSRuntimeAcceptanceV1",
        "system": "PFI_OS",
        "subsystem": "macOS Runtime Acceptance",
        "generated_at": "",
        "status": "Missing",
        "summary": {"pass": 0, "fail": 0, "info": 0, "total": 0},
        "pre_existing_healthy_ports": [],
        "post_healthy_ports": [],
        "started_by_acceptance": False,
        "launch_method": "Missing",
        "checks": [],
        "runtime_contract": {},
        "heavy_smoke_policy": (
            "Runtime acceptance does not run scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, "
            "browser automation, market-data refresh, broker connections, orders, payments, or holdings writes."
        ),
        "safety_boundary": "Read-only runtime evidence display; runtime acceptance remains Terminal-only and is not allowlisted in the UI.",
        "next_action": "Run runtime acceptance from Terminal after confirming no active workbench session is in use.",
        "source_uri": "",
        "evidence_id": "",
        "source_id": "",
        "read_policy": (
            "Operational Store private read model; sanitized from MacOSRuntimeAcceptance_latest.json without raw local paths, "
            "PIDs, screenshots, browser paths, or logs."
        ),
        "read_model": (
            "OperationalStore -> macos_runtime_acceptance_summary evidence metadata -> PFIOSMacOSRuntimeAcceptanceV1"
        ),
    }


def _resolve_cache_path(root: Path, cache_path: Path | str | None) -> Path | None:
    if cache_path is not None:
        resolved = Path(cache_path).expanduser().resolve(strict=False)
        return resolved if resolved.exists() and resolved.is_file() else None
    preferred = (root / DEFAULT_RUNTIME_CACHE).resolve(strict=False)
    return preferred if preferred.exists() and preferred.is_file() else None


def _relative_uri(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _cache_metadata(payload: dict[str, Any], relative_uri: str, read_model: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    return {
        "source_adapter": RUNTIME_SOURCE_TYPE,
        "schema": str(payload.get("schema", "")),
        "status": str(payload.get("status", "")),
        "generated_at": str(payload.get("generated_at", "")),
        "summary": _sanitize_summary(summary),
        "artifact_uri": relative_uri,
        "macos_runtime_read_model": read_model,
    }


def _evidence_summary(payload: dict[str, Any]) -> str:
    status = str(payload.get("status", "") or "Missing")
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    passed = int(summary.get("pass", 0) or 0)
    total = int(summary.get("total", 0) or 0)
    return f"macOS runtime acceptance status {status}: {passed}/{total} checks passed"


def _sanitize_runtime_payload(payload: dict[str, Any], relative_uri: str) -> dict[str, Any]:
    return {
        "schema": "PFIOSMacOSRuntimeAcceptanceV1",
        "system": str(payload.get("system", "PFI_OS") or "PFI_OS"),
        "subsystem": str(payload.get("subsystem", "macOS Runtime Acceptance") or "macOS Runtime Acceptance"),
        "generated_at": str(payload.get("generated_at", "")),
        "status": str(payload.get("status", "") or "Missing"),
        "summary": _sanitize_summary(payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}),
        "pre_existing_healthy_ports": _sanitize_ports(payload.get("pre_existing_healthy_ports", [])),
        "post_healthy_ports": _sanitize_ports(payload.get("post_healthy_ports", [])),
        "started_by_acceptance": bool(payload.get("started_by_acceptance")),
        "launch_method": str(payload.get("launch_method", "") or "Missing"),
        "checks": _sanitize_rows(payload.get("checks", []), limit=24),
        "runtime_contract": _sanitize_dict(payload.get("runtime_contract", {})) if isinstance(payload.get("runtime_contract"), dict) else {},
        "heavy_smoke_policy": _sanitize_value(payload.get("heavy_smoke_policy", "")),
        "safety_boundary": _sanitize_value(payload.get("safety_boundary", "")),
        "next_action": _sanitize_value(payload.get("next_action", "")),
        "source_uri": relative_uri,
        "read_policy": (
            "Operational Store private read model; sanitized from MacOSRuntimeAcceptance_latest.json without raw local paths, "
            "PIDs, screenshots, browser paths, or logs."
        ),
    }


def _sanitize_summary(summary: dict[str, Any]) -> dict[str, int]:
    return {
        "pass": int(summary.get("pass", 0) or 0),
        "fail": int(summary.get("fail", 0) or 0),
        "info": int(summary.get("info", 0) or 0),
        "total": int(summary.get("total", 0) or 0),
    }


def _sanitize_ports(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []
    ports: list[int] = []
    for value in values[:10]:
        try:
            port = int(value)
        except (TypeError, ValueError):
            continue
        if 1 <= port <= 65535:
            ports.append(port)
    return ports


def _sanitize_rows(rows: Any, *, limit: int) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [_sanitize_dict(row) for row in rows[:limit] if isinstance(row, dict)]


def _sanitize_dict(row: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in row.items():
        key_text = str(key)
        if "pid" in key_text.lower():
            sanitized[key_text] = "[redacted-runtime-id]"
        elif isinstance(value, dict):
            sanitized[key_text] = _sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key_text] = [
                _sanitize_dict(item) if isinstance(item, dict) else _sanitize_value(item)
                for item in value[:16]
            ]
        else:
            sanitized[key_text] = _sanitize_value(value)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        if _looks_private(value) or _looks_like_runtime_log(value):
            return "[redacted-runtime-evidence]"
    return value


def _looks_private(value: str) -> bool:
    private_markers = ("/Users/", "/private/", "/Applications/", ".app/", "browser_executable", "screenshot")
    return value.startswith("/") or value.startswith("~") or any(marker in value for marker in private_markers)


def _looks_like_runtime_log(value: str) -> bool:
    return bool(re.search(r"\b(pid|PID|process_id|raw_log|stdout|stderr)\b", value))


def _upsert_review_task(
    store: OperationalStore,
    payload: dict[str, Any],
    *,
    source_id: str,
    evidence_id: str,
    as_of: str,
) -> str:
    status = str(payload.get("status", "") or "Missing")
    if status == "Pass":
        return ""
    task_id = _stable_id("task_macos_runtime", source_id, evidence_id, status)
    store.upsert_task(
        TaskRecord(
            task_id=task_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace="local_runtime",
            action=f"Review macOS runtime acceptance latest cache status: {status}.",
            status="open",
            priority="P1",
            human_review_required=True,
            metadata={
                "source_adapter": RUNTIME_SOURCE_TYPE,
                "status": status,
                "launch_method": str(payload.get("launch_method", "")),
            },
        )
    )
    return task_id


def _skipped_result(reason: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": "Skipped",
        "reason": reason,
        "source_id": "",
        "evidence_id": "",
        "job_id": "",
        "task_id": "",
    }


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _stable_id(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
