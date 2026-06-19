from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import DataDomain, OperationalStore, SourceRecord


PUBLIC_DOMAINS = {DataDomain.PUBLIC_SHARED_RAW, DataDomain.PUBLIC_SHARED_CANONICAL}
PRIVATE_DOMAINS = {DataDomain.PRIVATE_USER, DataDomain.PRIVATE_DERIVED, DataDomain.SECRET}


@dataclass(frozen=True)
class SourceIngestionResult:
    schema: str
    status: str
    source_id: str
    domain: str
    uri: str
    checksum: str
    byte_size: int
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ingest_file_source(
    store: OperationalStore,
    *,
    project_root: Path | str,
    file_path: Path | str,
    domain: DataDomain,
    source_type: str,
    as_of: str,
    evidence_class: str,
    title: str = "",
    source_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> SourceIngestionResult:
    root = _resolve(project_root)
    path = _resolve(file_path)
    _require_text(source_type, "source_type")
    _require_text(as_of, "as_of")
    _require_text(evidence_class, "evidence_class")
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(str(path))

    uri = _source_uri(root, path, domain)
    content = path.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()
    resolved_source_id = source_id or _stable_id("source", domain.value, source_type, uri, as_of, checksum)
    provenance = {
        "source_adapter": "file_source",
        "project_relative": _is_relative_to(path, root),
        "byte_size": len(content),
        "checksum_algorithm": "sha256",
    }
    source = SourceRecord(
        source_id=resolved_source_id,
        domain=domain,
        source_type=source_type,
        uri=uri,
        as_of=as_of,
        evidence_class=evidence_class,
        title=title,
        checksum=checksum,
        metadata={**provenance, **(metadata or {})},
    )
    store.upsert_source(source)
    return SourceIngestionResult(
        schema="PFIOSFileSourceIngestionV1",
        status="Ingested",
        source_id=resolved_source_id,
        domain=domain.value,
        uri=uri,
        checksum=checksum,
        byte_size=len(content),
        provenance=provenance,
    )


def _source_uri(root: Path, path: Path, domain: DataDomain) -> str:
    inside_project = _is_relative_to(path, root)
    if domain in PUBLIC_DOMAINS:
        if not inside_project:
            raise ValueError("PUBLIC_SOURCE_OUTSIDE_PROJECT: public file sources must use project-relative URIs.")
        return path.relative_to(root).as_posix()
    if domain in PRIVATE_DOMAINS:
        if inside_project:
            raise ValueError("PRIVATE_SOURCE_INSIDE_PUBLIC_REPO: private and secret file sources must stay outside public Git.")
        return str(path)
    if domain == DataDomain.EPHEMERAL:
        raise ValueError("EPHEMERAL_SOURCE_NOT_INGESTIBLE: ephemeral runtime files are not valid source registry facts.")
    raise ValueError(f"Unsupported data domain: {domain}")


def _resolve(path: Path | str) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _stable_id(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _require_text(value: str, field_name: str) -> None:
    if not str(value or "").strip():
        raise ValueError(f"{field_name} is required")
