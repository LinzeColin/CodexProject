from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path
from typing import Any


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = DATABASE_DIR / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from migrate_memory_records import record_hash, validate_record  # noqa: E402
from plan_memory_shards import build_shard_plan, load_contract  # noqa: E402


def fixture_record(row: dict[str, Any]) -> dict[str, Any]:
    record_id = str(row["id"])
    status = str(row.get("status") or row.get("review_status") or "active")
    if status not in {"active", "candidate", "disputed", "retired"}:
        status = "candidate"
    day = str(row.get("date") or "2026-07-16")[:10]
    sensitivity = str(row.get("sensitivity") or "public")
    if sensitivity not in {"public", "private", "sensitive"}:
        sensitivity = "public"
    importance = {"高": "high", "中": "medium", "低": "low"}.get(
        str(row.get("importance")),
        str(row.get("importance") or "low"),
    )
    if importance not in {"high", "medium", "low"}:
        importance = "low"
    kind = str(row.get("category") or "fact")
    if kind not in {
        "answering_rule",
        "preference",
        "decision",
        "project_context",
        "workflow",
        "security_boundary",
        "fact",
        "negative_trigger",
    }:
        kind = "fact"
    verified = status == "active"
    result: dict[str, Any] = {
        "schema_version": "openai_database.memory_record.v2",
        "id": record_id,
        "memory_key": "memory:fixture:" + hashlib.sha256(record_id.encode()).hexdigest(),
        "kind": kind,
        "statement": str(row.get("statement") or record_id),
        "status": status,
        "scope": {"type": "global", "key": "fixture"},
        "source": {
            "type": "repository_evidence",
            "ref": str(row.get("source") or "synthetic-regression-fixture"),
            "observed_at": day + "T00:00:00Z",
            "evidence_hash": None,
        },
        "valid_time": {"from": day + "T00:00:00Z", "to": None},
        "recorded_time": {"recorded_at": day + "T00:00:00Z", "recorded_by": "migration"},
        "supersession": {"supersedes": [], "superseded_by": None, "reason": "Fixture has no supersession."},
        "conflict": {"state": "none", "with": [], "resolution": None},
        "confidence": str(row.get("confidence") or "high"),
        "importance": importance,
        "verification": {
            "state": "verified" if verified else "unverified",
            "method": "repository_hash" if verified else "none",
            "evidence_refs": ["fixture:" + record_id],
            "verified_at": day + "T00:00:00Z" if verified else None,
            "rationale": "Synthetic deterministic regression fixture.",
        },
        "aliases": [],
        "tags": [
            "legacy-tier:" + str(row.get("memory_tier") or "一般"),
            "legacy-validity:" + str(row.get("validity") or "长期"),
            "legacy-source-kind:fixture",
        ],
        "negative_triggers": [],
        "sensitivity": {
            "classification": sensitivity,
            "handling": "public_text" if sensitivity == "public" else "redacted_summary",
            "credential_present": False,
            "public_repository_allowed": True,
        },
        "hash": {
            "algorithm": "sha256",
            "canonicalization": "openai-memory-json-v1",
            "value": "",
        },
    }
    result["hash"]["value"] = record_hash(result)
    validate_record(result)
    return result


def write_canonical_memory(database_dir: Path, rows: list[dict[str, Any]]) -> Path:
    config_dir = database_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    contract_path = config_dir / "memory.sharding.json"
    shutil.copy2(DATABASE_DIR / "config/memory.sharding.json", contract_path)
    contract = load_contract(contract_path)
    plan = build_shard_plan([fixture_record(row) for row in rows], contract)
    records_dir = database_dir / "data/memory/records"
    records_dir.mkdir(parents=True, exist_ok=True)
    for shard in plan.shards:
        (records_dir / Path(shard.path).name).write_bytes(shard.payload)
    manifest = records_dir / "manifest.json"
    manifest.write_bytes(plan.manifest_bytes)
    return manifest
