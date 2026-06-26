from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import DataDomain, EvidenceRecord, OperationalStore, SourceRecord, default_data_home


PRIVATE_REVIEWED_INPUT_SOURCE_TYPE = "private_reviewed_input_ledger"
PRIVATE_REVIEWED_INPUT_EVIDENCE_CLASS = "private_reviewed_input_entry"


def append_private_reviewed_input_entry(
    store: OperationalStore,
    *,
    ledger: str,
    entry: dict[str, Any],
    entry_id_key: str,
    as_of_key: str,
) -> dict[str, Any]:
    clean_ledger = _clean_ledger(ledger)
    entry_id = str(entry.get(entry_id_key, "")).strip()
    if not entry_id:
        raise ValueError(f"{entry_id_key} is required for private reviewed input entry.")
    as_of = str(entry.get(as_of_key, "") or entry.get("created_at", "") or "missing")
    source = _source_record(clean_ledger, as_of=as_of)
    store.upsert_source(source)
    evidence_id = _stable_id("ev_private_reviewed_input", clean_ledger, entry_id)
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source.source_id,
            entity_id=clean_ledger,
            as_of=as_of,
            evidence_class=PRIVATE_REVIEWED_INPUT_EVIDENCE_CLASS,
            summary=f"Private reviewed input entry for {clean_ledger}: {entry_id}",
            artifact_uri=source.uri,
            model_version="DisabledProvider",
            metadata={
                "source_adapter": PRIVATE_REVIEWED_INPUT_SOURCE_TYPE,
                "ledger": clean_ledger,
                "entry_id_key": entry_id_key,
                "entry_id": entry_id,
                "entry": entry,
                "privacy_boundary": (
                    "Private user-entered ledger data stored in Operational Store; not written to public Git data files."
                ),
            },
        )
    )
    return {
        "schema": "PFIOSPrivateReviewedInputEntryV1",
        "status": "Stored",
        "ledger": clean_ledger,
        "source_id": source.source_id,
        "evidence_id": evidence_id,
        "entry_id": entry_id,
    }


def load_private_reviewed_input_entries(store: OperationalStore, *, ledger: str) -> list[dict[str, Any]]:
    clean_ledger = _clean_ledger(ledger)
    rows = [
        row
        for row in store.table_rows("evidence_records")
        if str(row.get("evidence_class", "")) == PRIVATE_REVIEWED_INPUT_EVIDENCE_CLASS
        and str(row.get("entity_id", "")) == clean_ledger
    ]
    entries: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: (str(item.get("as_of", "")), str(item.get("created_at", "")))):
        metadata = _json_dict(row.get("metadata_json", "{}"))
        entry = metadata.get("entry")
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def private_reviewed_input_output_dir(ledger: str, *, data_home: Path | str | None = None) -> Path:
    clean_ledger = _clean_ledger(ledger)
    root = Path(data_home).expanduser() if data_home is not None else default_data_home()
    return root / "private" / "derived" / clean_ledger


def private_reviewed_input_contract(data_home: Path | str | None = None) -> dict[str, Any]:
    root = Path(data_home).expanduser() if data_home is not None else default_data_home()
    return {
        "schema": "PFIOSPrivateReviewedInputContractV1",
        "source_type": PRIVATE_REVIEWED_INPUT_SOURCE_TYPE,
        "evidence_class": PRIVATE_REVIEWED_INPUT_EVIDENCE_CLASS,
        "domain": DataDomain.PRIVATE_USER.value,
        "operational_store_only": True,
        "public_git_ledgers": [],
        "private_output_root": str(root / "private" / "derived"),
        "supported_ledgers": ["company_cashflow", "policy_radar", "consumption_guard"],
    }


def _source_record(ledger: str, *, as_of: str) -> SourceRecord:
    source_id = _stable_id("src_private_reviewed_input", ledger)
    return SourceRecord(
        source_id=source_id,
        domain=DataDomain.PRIVATE_USER,
        source_type=PRIVATE_REVIEWED_INPUT_SOURCE_TYPE,
        uri=f"operational://private-reviewed-input/{ledger}",
        as_of=as_of,
        evidence_class=PRIVATE_REVIEWED_INPUT_EVIDENCE_CLASS,
        title=f"Private reviewed input ledger: {ledger}",
        metadata={
            "source_adapter": PRIVATE_REVIEWED_INPUT_SOURCE_TYPE,
            "ledger": ledger,
            "privacy_boundary": "Private user-entered ledger data stays outside public Git.",
        },
    )


def _clean_ledger(value: str) -> str:
    clean = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if clean not in {"company_cashflow", "policy_radar", "consumption_guard"}:
        raise ValueError(f"Unsupported private reviewed input ledger: {value}")
    return clean


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
