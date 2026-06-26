from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import DataDomain, EvidenceRecord, JobRecord, OperationalStore, TaskRecord
from pfi_os.application.source_ingestion import ingest_file_source


SCHEMA = "PFIOSVectorizedResearchCacheIngestionV1"
VECTORIZED_SOURCE_TYPE = "vectorized_research_cache"
VECTORIZED_EVIDENCE_CLASS = "vectorized_research_summary"
DEFAULT_VECTORIZED_CACHE = Path("data") / "vectorized" / "VectorizedResearch_latest.json"


def ingest_vectorized_research_cache(
    store: OperationalStore,
    *,
    project_root: Path | str,
    cache_path: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve(strict=False)
    resolved_cache = _resolve_cache_path(root, cache_path)
    if resolved_cache is None:
        return _skipped_result("No vectorized research latest cache found.")

    payload_text = resolved_cache.read_text(encoding="utf-8")
    payload = json.loads(payload_text)
    if payload.get("schema") != "PFIOSVectorizedResearchBatchV1":
        return _skipped_result("Vectorized research cache schema is not supported.")

    relative_uri = _relative_uri(root, resolved_cache)
    checksum = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    as_of = _payload_as_of(payload)
    read_model = _sanitize_vectorized_payload(payload, relative_uri)
    source_result = ingest_file_source(
        store,
        project_root=root,
        file_path=resolved_cache,
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type=VECTORIZED_SOURCE_TYPE,
        as_of=as_of,
        evidence_class="local_vectorized_research_cache",
        title="Vectorized research latest cache",
        metadata=_cache_metadata(payload, relative_uri, read_model),
    )
    evidence_id = _stable_id("ev_vectorized", source_result.source_id, as_of, read_model.get("status", ""))
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source_result.source_id,
            entity_id=str(payload.get("selected_symbol", "") or "PFI_OS"),
            as_of=as_of,
            evidence_class=VECTORIZED_EVIDENCE_CLASS,
            summary=_evidence_summary(payload),
            artifact_uri=relative_uri,
            model_version="DisabledProvider",
            strategy_version=str(payload.get("strategy_id", "")),
            metadata=_cache_metadata(payload, relative_uri, read_model),
        )
    )
    job_id = _stable_id("job_ingest_vectorized", source_result.source_id, as_of)
    store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_result.source_id,
            as_of=as_of,
            job_type="ingest_vectorized_research_cache",
            status="completed",
            phase="done",
            progress=1.0,
            artifact_uri=relative_uri,
            metadata=_cache_metadata(payload, relative_uri, read_model),
        )
    )
    task_id = _upsert_review_task(store, payload, source_id=source_result.source_id, evidence_id=evidence_id, as_of=as_of)
    return {
        "schema": SCHEMA,
        "status": "Ingested",
        "source_id": source_result.source_id,
        "evidence_id": evidence_id,
        "job_id": job_id,
        "task_id": task_id,
        "uri": relative_uri,
        "checksum": checksum,
    }


def build_vectorized_research_read_model(store: OperationalStore | None = None) -> dict[str, Any]:
    operational_store = store or OperationalStore()
    evidence_rows = [
        row
        for row in operational_store.table_rows("evidence_records")
        if str(row.get("evidence_class", "")) == VECTORIZED_EVIDENCE_CLASS
    ]
    if not evidence_rows:
        return empty_vectorized_research_read_model()
    latest = sorted(evidence_rows, key=lambda row: (str(row.get("as_of", "")), str(row.get("created_at", ""))), reverse=True)[0]
    metadata = _json_dict(latest.get("metadata_json", "{}"))
    payload = metadata.get("vectorized_read_model")
    if not isinstance(payload, dict):
        return empty_vectorized_research_read_model()
    model = {**empty_vectorized_research_read_model(), **payload}
    model["schema"] = "PFIOSVectorizedResearchBatchV1"
    model["evidence_id"] = str(latest.get("evidence_id", ""))
    model["source_id"] = str(latest.get("source_id", ""))
    model["read_model"] = "OperationalStore -> vectorized_research_summary evidence metadata -> PFIOSVectorizedResearchBatchV1"
    model["safety_boundary"] = (
        "Read-only vectorized research summary; no market refresh, broker calls, orders, holdings mutation, "
        "payments, betting, or live trading automation."
    )
    return model


def empty_vectorized_research_read_model() -> dict[str, Any]:
    return {
        "schema": "PFIOSVectorizedResearchBatchV1",
        "as_of": "",
        "generated_at": "",
        "mode": "read_model",
        "status": "Missing",
        "replay_path": "",
        "replay_status": "Missing",
        "row_count": 0,
        "symbol_count": 0,
        "available_symbols": [],
        "selected_symbol": "",
        "first_datetime": "",
        "last_datetime": "",
        "strategy_id": "",
        "parameter_grid": {},
        "parameter_run_count": 0,
        "scan_run_count": 0,
        "best_run": {},
        "stability": {"stability_status": "Missing", "parameter_coverage": 0.0},
        "missing_data_log": [],
        "assumptions": [],
        "summary_rows": [],
        "outputs": {},
        "source_uri": "",
        "evidence_id": "",
        "source_id": "",
        "read_policy": (
            "Operational Store read model; sanitized from VectorizedResearch_latest.json without private absolute paths."
        ),
        "read_model": "OperationalStore -> vectorized_research_summary evidence metadata -> PFIOSVectorizedResearchBatchV1",
        "safety_boundary": (
            "Read-only vectorized research summary; no market refresh, broker calls, orders, holdings mutation, "
            "payments, betting, or live trading automation."
        ),
    }


def _resolve_cache_path(root: Path, cache_path: Path | str | None) -> Path | None:
    if cache_path is not None:
        resolved = Path(cache_path).expanduser().resolve(strict=False)
        return resolved if resolved.exists() and resolved.is_file() else None
    preferred = (root / DEFAULT_VECTORIZED_CACHE).resolve(strict=False)
    return preferred if preferred.exists() and preferred.is_file() else None


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


def _cache_metadata(payload: dict[str, Any], relative_uri: str, read_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_adapter": VECTORIZED_SOURCE_TYPE,
        "schema": str(payload.get("schema", "")),
        "status": str(payload.get("status", "")),
        "selected_symbol": str(payload.get("selected_symbol", "")),
        "strategy_id": str(payload.get("strategy_id", "")),
        "summary_row_count": len(payload.get("summary_rows", []) or []),
        "artifact_uri": relative_uri,
        "vectorized_read_model": read_model,
    }


def _evidence_summary(payload: dict[str, Any]) -> str:
    status = str(payload.get("status", "") or "Missing")
    symbol = str(payload.get("selected_symbol", "") or "unknown")
    strategy = str(payload.get("strategy_id", "") or "unknown")
    return f"Vectorized research status {status}: {symbol} / {strategy}"


def _sanitize_vectorized_payload(payload: dict[str, Any], relative_uri: str) -> dict[str, Any]:
    return {
        "schema": "PFIOSVectorizedResearchBatchV1",
        "as_of": str(payload.get("as_of", "")),
        "generated_at": str(payload.get("generated_at", "")),
        "mode": str(payload.get("mode", "")),
        "status": str(payload.get("status", "") or "Missing"),
        "replay_path": _sanitize_value(payload.get("replay_path", "")),
        "replay_status": str(payload.get("replay_status", "")),
        "row_count": int(payload.get("row_count", 0) or 0),
        "symbol_count": int(payload.get("symbol_count", 0) or 0),
        "available_symbols": _sanitize_list(payload.get("available_symbols", []), limit=50),
        "selected_symbol": str(payload.get("selected_symbol", "")),
        "first_datetime": str(payload.get("first_datetime", "")),
        "last_datetime": str(payload.get("last_datetime", "")),
        "strategy_id": str(payload.get("strategy_id", "")),
        "parameter_grid": _sanitize_dict(payload.get("parameter_grid", {})) if isinstance(payload.get("parameter_grid"), dict) else {},
        "parameter_run_count": int(payload.get("parameter_run_count", 0) or 0),
        "scan_run_count": int(payload.get("scan_run_count", 0) or 0),
        "best_run": _sanitize_dict(payload.get("best_run", {})) if isinstance(payload.get("best_run"), dict) else {},
        "stability": _sanitize_dict(payload.get("stability", {})) if isinstance(payload.get("stability"), dict) else {},
        "missing_data_log": _sanitize_list(payload.get("missing_data_log", []), limit=20),
        "assumptions": _sanitize_list(payload.get("assumptions", []), limit=20),
        "summary_rows": _sanitize_rows(payload.get("summary_rows", []), limit=20),
        "outputs": _sanitize_dict(payload.get("outputs", {})) if isinstance(payload.get("outputs"), dict) else {},
        "source_uri": relative_uri,
        "read_policy": (
            "Operational Store read model; sanitized from VectorizedResearch_latest.json without private absolute paths."
        ),
        "safety_boundary": (
            "Read-only vectorized research summary; no market refresh, broker calls, orders, holdings mutation, "
            "payments, betting, or live trading automation."
        ),
    }


def _sanitize_rows(rows: Any, *, limit: int) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [_sanitize_dict(row) for row in rows[:limit] if isinstance(row, dict)]


def _sanitize_list(values: Any, *, limit: int) -> list[Any]:
    if not isinstance(values, list):
        return []
    sanitized: list[Any] = []
    for value in values[:limit]:
        if isinstance(value, dict):
            sanitized.append(_sanitize_dict(value))
        elif isinstance(value, list):
            sanitized.append(_sanitize_list(value, limit=limit))
        else:
            sanitized.append(_sanitize_value(value))
    return sanitized


def _sanitize_dict(row: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, dict):
            sanitized[str(key)] = _sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[str(key)] = _sanitize_list(value, limit=16)
        else:
            sanitized[str(key)] = _sanitize_value(value)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("/") or value.startswith("~") or "/Users/" in value or "/private/" in value:
            return "[redacted-private-uri]"
    return value


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
    task_id = _stable_id("task_vectorized", source_id, evidence_id, status)
    store.upsert_task(
        TaskRecord(
            task_id=task_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace="data_system",
            action=f"Review vectorized research latest cache status: {status}.",
            status="open",
            priority="P1",
            human_review_required=True,
            metadata={
                "source_adapter": VECTORIZED_SOURCE_TYPE,
                "selected_symbol": str(payload.get("selected_symbol", "")),
                "strategy_id": str(payload.get("strategy_id", "")),
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
