#!/usr/bin/env python3
"""Build a deterministic, value-redacted legacy-memory migration profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CONTRACT = Path("config/memory.profiling.json")
ENTRY_SCHEMA = "openai_database.memory_migration_map_entry.v1"
REPORT_SCHEMA = "openai_database.memory_quality_report.v1"
ID_RE = re.compile(r"^mem_[0-9a-f]{16}$")
LOCAL_PATH_RE = re.compile(r"^(?:/|~(?:/|$)|[A-Za-z]:[\\/])")
CREDENTIAL_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(
        r"\b(?:password|passwd|pwd|api[_-]?key|secret|token|session|cookie)"
        r"\s*[:=]\s*[^\s,;]{8,}",
        re.I,
    ),
)
KIND_MAP = {
    "answering_rule": "answering_rule",
    "preference": "preference",
    "decision": "decision",
    "project_context": "project_context",
    "workflow": "workflow",
    "security_boundary": "security_boundary",
    "fact": "fact",
    "deprecated_info": "fact",
    "temporary_or_sensitive": "fact",
}
IMPORTANCE_MAP = {"高": "high", "中": "medium", "低": "low"}
SOURCE_TYPE_MAP = {"openai_export": "raw_import", "codex_pack": "raw_import"}
TARGET_STATUS = {
    "migrate-active": "active",
    "migrate-candidate": "candidate",
    "retire": "retired",
}


class ProfileError(RuntimeError):
    """A fail-closed validation error safe to report without record values."""


def duplicate_key_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProfileError("duplicate JSON key detected")
        result[key] = value
    return result


def reject_float(_: str) -> None:
    raise ProfileError("floating-point JSON values are not allowed")


def reject_constant(_: str) -> None:
    raise ProfileError("non-standard JSON numeric value detected")


def load_json_bytes(raw: bytes, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=duplicate_key_guard,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except ProfileError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ProfileError(f"invalid JSON in {label}") from exc


def normalize(value: Any) -> Any:
    if isinstance(value, float):
        raise ProfileError("floating-point values are not allowed")
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ProfileError("non-string object key detected")
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise ProfileError("Unicode-normalized duplicate object key detected")
            normalized[normalized_key] = normalize(item)
        return normalized
    return value


def canonical_bytes(value: Any, *, final_lf: bool = False, pretty: bool = False) -> bytes:
    value = normalize(value)
    if pretty:
        text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    else:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return (text + ("\n" if final_lf else "")).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def record_sha256(record: dict[str, Any]) -> str:
    return sha256_bytes(canonical_bytes(record))


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from iter_strings(item)


def contains_credential_shape(value: Any) -> bool:
    return any(pattern.search(text) for text in iter_strings(value) for pattern in CREDENTIAL_PATTERNS)


def normalize_statement(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\[REDACTED:[^\]]+\]", "[redacted]", text, flags=re.I)
    text = re.sub(r"\s+", " ", text.strip().casefold())
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text[:500]


def safe_repo_path(database_dir: Path, relative: str, *, must_exist: bool) -> Path:
    candidate_rel = Path(relative)
    if candidate_rel.is_absolute() or ".." in candidate_rel.parts or not candidate_rel.parts:
        raise ProfileError("absolute or traversal path rejected")
    candidate = database_dir.joinpath(candidate_rel)
    cursor = database_dir
    if cursor.is_symlink():
        raise ProfileError("database directory symlink rejected")
    for part in candidate_rel.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise ProfileError("symlink path rejected")
    if must_exist and not candidate.is_file():
        raise ProfileError(f"required input file missing: {relative}")
    return candidate


def safe_glob(database_dir: Path, pattern: str) -> list[Path]:
    pattern_path = Path(pattern)
    if pattern_path.is_absolute() or ".." in pattern_path.parts:
        raise ProfileError("absolute or traversal glob rejected")
    paths = sorted(database_dir.glob(pattern), key=lambda path: path.as_posix())
    for path in paths:
        relative = path.relative_to(database_dir).as_posix()
        safe_repo_path(database_dir, relative, must_exist=True)
    return paths


def descriptor(database_dir: Path, path: Path, file_id: str, role: str) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "file_id": file_id,
        "role": role,
        "path": path.relative_to(database_dir).as_posix(),
        "bytes": len(raw),
        "lines": len(raw.splitlines()),
        "sha256": sha256_bytes(raw),
    }


def collection_sha256(descriptors: list[dict[str, Any]]) -> str:
    digest_rows = [
        {key: row[key] for key in ("path", "bytes", "lines", "sha256")}
        for row in descriptors
    ]
    return sha256_bytes(canonical_bytes(digest_rows))


def read_jsonl(
    database_dir: Path,
    path: Path,
    file_id: str,
    id_field: str,
) -> list[tuple[str, int, dict[str, Any]]]:
    raw = path.read_bytes()
    relative = path.relative_to(database_dir).as_posix()
    if raw and not raw.endswith(b"\n"):
        raise ProfileError(f"missing final LF in {relative}")
    rows: list[tuple[str, int, dict[str, Any]]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            raise ProfileError(f"blank JSONL line in {relative}")
        payload = load_json_bytes(line, f"{relative}:{line_number}")
        if not isinstance(payload, dict):
            raise ProfileError(f"non-object JSONL row in {relative}")
        payload = normalize(payload)
        legacy_id = payload.get(id_field)
        if not isinstance(legacy_id, str) or not ID_RE.fullmatch(legacy_id):
            raise ProfileError(f"missing or malformed legacy ID in {relative}")
        if legacy_id in seen:
            raise ProfileError(f"duplicate legacy ID within {relative}")
        seen.add(legacy_id)
        if contains_credential_shape(payload):
            raise ProfileError(f"credential-shaped material detected: path={relative}; id={legacy_id}")
        rows.append((file_id, line_number, payload))
    return rows


def validate_baseline(
    role: str,
    contract: dict[str, Any],
    descriptors: list[dict[str, Any]],
    record_count: int,
) -> None:
    expected_records = contract.get("record_count", contract.get("override_count"))
    observed = {
        "file_count": len(descriptors),
        "record_count": record_count,
        "bytes": sum(int(row["bytes"]) for row in descriptors),
        "collection_sha256": collection_sha256(descriptors),
    }
    expected = {
        "file_count": int(contract["file_count"]),
        "record_count": int(expected_records),
        "bytes": int(contract["bytes"]),
        "collection_sha256": str(contract["collection_sha256"]),
    }
    if observed != expected:
        raise ProfileError(f"{role} baseline drift detected")


def locator(file_id: str, line: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {"file_id": file_id, "line": line, "record_sha256": record_sha256(payload)}


def values_equal(left: Any, right: Any) -> bool:
    return canonical_bytes(left) == canonical_bytes(right)


def age_bucket(age_days: int, thresholds: list[int]) -> str:
    first, second, third = thresholds
    if age_days <= first:
        return f"0-{first}"
    if age_days <= second:
        return f"{first + 1}-{second}"
    if age_days <= third:
        return f"{second + 1}-{third}"
    return f">{third}"


def opaque_scope(record: dict[str, Any], contract: dict[str, Any]) -> dict[str, str] | None:
    active_gate = contract["disposition_contract"]["active_gate"]
    if record.get("curation_status") == active_gate["curation_status"]:
        return dict(contract["source_contract"]["active_curated_scope"])
    opaque = record.get("conversation_id") or record.get("source")
    if not isinstance(opaque, str) or not opaque:
        return None
    return {
        "type": str(contract["source_contract"]["fallback_scope_type"]),
        "key": "sha256:" + sha256_bytes(unicodedata.normalize("NFC", opaque).encode("utf-8")),
    }


def memory_key(kind: str, scope: dict[str, str], statement: str, prefix: str) -> str:
    normalized = normalize_statement(statement)
    material = "\0".join((kind, scope["type"], scope["key"], normalized)).encode("utf-8")
    return prefix + sha256_bytes(material)


def finding_types(rows: Iterable[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(finding.get("type"))
            for row in rows
            for finding in (row.get("security_findings") or [])
            if isinstance(finding, dict) and finding.get("type")
        }
    )


def build_profile(database_dir: Path, contract: dict[str, Any]) -> tuple[bytes, bytes, dict[str, Any]]:
    input_contract = contract["inputs"]
    active_path = safe_repo_path(database_dir, input_contract["active"]["path"], must_exist=True)
    candidate_paths = safe_glob(database_dir, input_contract["candidates"]["glob"])
    curation_path = safe_repo_path(database_dir, input_contract["curation"]["path"], must_exist=True)
    secret_paths = safe_glob(database_dir, input_contract["secret_refs"]["glob"])

    active_descriptors = [descriptor(database_dir, active_path, "A001", "active")]
    candidate_descriptors = [
        descriptor(database_dir, path, f"C{index:03d}", "candidate")
        for index, path in enumerate(candidate_paths, start=1)
    ]
    curation_descriptors = [descriptor(database_dir, curation_path, "U001", "curation")]
    secret_descriptors = [
        descriptor(database_dir, path, f"S{index:03d}", "secret_ref")
        for index, path in enumerate(secret_paths, start=1)
    ]

    active_rows = read_jsonl(database_dir, active_path, "A001", "id")
    candidate_rows: list[tuple[str, int, dict[str, Any]]] = []
    for row, path in zip(candidate_descriptors, candidate_paths):
        candidate_rows.extend(read_jsonl(database_dir, path, row["file_id"], "id"))
    secret_rows: list[tuple[str, int, dict[str, Any]]] = []
    for row, path in zip(secret_descriptors, secret_paths):
        secret_rows.extend(read_jsonl(database_dir, path, row["file_id"], "memory_id"))

    curation_raw = curation_path.read_bytes()
    curation_payload = load_json_bytes(curation_raw, input_contract["curation"]["path"])
    if not isinstance(curation_payload, dict) or not isinstance(curation_payload.get("overrides"), dict):
        raise ProfileError("invalid curation override contract")
    curation_payload = normalize(curation_payload)
    if contains_credential_shape(curation_payload):
        raise ProfileError("credential-shaped material detected in curation input")
    overrides: dict[str, dict[str, Any]] = curation_payload["overrides"]
    for legacy_id, override in overrides.items():
        if not ID_RE.fullmatch(legacy_id) or not isinstance(override, dict):
            raise ProfileError("malformed curation override")

    validate_baseline("active", input_contract["active"], active_descriptors, len(active_rows))
    validate_baseline("candidates", input_contract["candidates"], candidate_descriptors, len(candidate_rows))
    validate_baseline("curation", input_contract["curation"], curation_descriptors, len(overrides))
    validate_baseline("secret_refs", input_contract["secret_refs"], secret_descriptors, len(secret_rows))

    active_by_id = {row[2]["id"]: row for row in active_rows}
    candidates_by_id: dict[str, list[tuple[str, int, dict[str, Any]]]] = defaultdict(list)
    for row in candidate_rows:
        candidates_by_id[row[2]["id"]].append(row)
    secrets_by_id: dict[str, list[tuple[str, int, dict[str, Any]]]] = defaultdict(list)
    for row in secret_rows:
        secrets_by_id[row[2]["memory_id"]].append(row)

    legacy_ids = sorted(set(active_by_id) | set(candidates_by_id) | set(secrets_by_id) | set(overrides))
    expected_id_count = int(contract["identity"]["expected_unique_id_count"])
    if len(legacy_ids) != expected_id_count:
        raise ProfileError("unique legacy ID baseline drift detected")

    material_fields = list(contract["material_consistency_fields"])
    thresholds = [int(value) for value in contract["quality_contract"]["age_bucket_days"]]
    as_of = date.fromisoformat(str(contract["profile_as_of_date"]))
    credential_finding_types = set(contract["security"]["credential_finding_types"])
    allowed_source_kinds = set(contract["source_contract"]["allowed_source_kinds"])
    raw_actions = set(contract["disposition_contract"]["raw_evidence_actions"])
    retire_actions = set(contract["disposition_contract"]["retire_actions"])
    retire_categories = set(contract["disposition_contract"]["retire_categories"])
    retire_validities = set(contract["disposition_contract"]["retire_validities"])
    active_gate = contract["disposition_contract"]["active_gate"]

    contexts: dict[str, dict[str, Any]] = {}
    semantic_groups: dict[str, list[str]] = defaultdict(list)
    exact_candidate_hashes = Counter(record_sha256(row[2]) for row in candidate_rows)

    for legacy_id in legacy_ids:
        active_row = active_by_id.get(legacy_id)
        candidate_history = candidates_by_id.get(legacy_id, [])
        secret_history = secrets_by_id.get(legacy_id, [])
        representative = active_row[2] if active_row else (candidate_history[-1][2] if candidate_history else None)
        conflict_codes: set[str] = set()

        if representative is not None:
            for field in material_fields:
                candidate_values = {
                    sha256_bytes(canonical_bytes(row[2].get(field))) for row in candidate_history
                }
                if len(candidate_values) > 1:
                    conflict_codes.add(f"candidate_{field}_changed")
                if active_row and candidate_values:
                    active_value_hash = sha256_bytes(canonical_bytes(active_row[2].get(field)))
                    if active_value_hash not in candidate_values:
                        override = overrides.get(legacy_id) or {}
                        lifecycle_retirement = (
                            (
                                active_row[2].get("action") in retire_actions
                                or active_row[2].get("category") in retire_categories
                                or active_row[2].get("validity") in retire_validities
                            )
                            and field in {"category", "validity"}
                        )
                        if field not in override and not lifecycle_retirement:
                            conflict_codes.add(f"unexplained_active_{field}_change")

        source_kind = representative.get("source_kind") if representative else None
        unsupported_codes: set[str] = set()
        if representative is None:
            unsupported_codes.add("record_body_missing")
        else:
            if source_kind not in allowed_source_kinds:
                unsupported_codes.add("unsupported_source_kind")
            if representative.get("action") not in {"add", "backup", "deprecate", "ignore"}:
                unsupported_codes.add("unsupported_action")
            if representative.get("category") not in KIND_MAP:
                unsupported_codes.add("unsupported_category")
            if representative.get("importance") not in IMPORTANCE_MAP:
                unsupported_codes.add("unsupported_importance")
            source_ref = representative.get("source")
            if not isinstance(source_ref, str) or not source_ref:
                unsupported_codes.add("source_ref_missing")
            elif LOCAL_PATH_RE.search(source_ref):
                unsupported_codes.add("absolute_local_source_ref")
            if not representative.get("evidence"):
                unsupported_codes.add("evidence_missing")

        scope = opaque_scope(representative, contract) if representative else None
        if representative is not None and scope is None:
            unsupported_codes.add("scope_source_missing")
        kind = KIND_MAP.get(str(representative.get("category"))) if representative else None
        normalized = normalize_statement(str(representative.get("statement", ""))) if representative else ""
        if representative is not None and not normalized:
            unsupported_codes.add("statement_missing")

        all_records = [row[2] for row in candidate_history + secret_history]
        if active_row:
            all_records.append(active_row[2])
        types = finding_types(all_records)
        credential_flag = bool(set(types) & credential_finding_types)
        credential_flag = credential_flag or bool(secret_history)
        credential_flag = credential_flag or bool(representative and representative.get("secret_ref"))
        credential_flag = credential_flag or bool(representative and representative.get("sensitivity") == "secret")

        semantic_key = ""
        if kind and normalized:
            semantic_key = sha256_bytes((kind + "\0" + normalized).encode("utf-8"))
            semantic_groups[semantic_key].append(legacy_id)

        contexts[legacy_id] = {
            "active": active_row,
            "candidates": candidate_history,
            "secrets": secret_history,
            "override": overrides.get(legacy_id),
            "representative": representative,
            "conflict_codes": sorted(conflict_codes),
            "unsupported_codes": sorted(unsupported_codes),
            "scope": scope,
            "kind": kind,
            "normalized_statement": normalized,
            "semantic_key": semantic_key,
            "finding_types": types,
            "credential_flag": credential_flag,
        }

    entries: list[dict[str, Any]] = []
    disposition_counts = Counter()
    reason_counts = Counter()
    age_counts = Counter()
    finding_type_counts = Counter()
    material_conflict_ids = 0
    curation_explained_change_ids = 0

    for legacy_id in legacy_ids:
        context = contexts[legacy_id]
        record = context["representative"]
        semantic_group_size = len(semantic_groups.get(context["semantic_key"], [])) if context["semantic_key"] else 0
        conflict_codes = list(context["conflict_codes"])
        if semantic_group_size > 1:
            conflict_codes.append("semantic_duplicate_group")
        conflict_codes = sorted(set(conflict_codes))
        if conflict_codes:
            material_conflict_ids += 1
        if context["override"] and context["active"] and context["candidates"]:
            changed = any(
                not values_equal(context["active"][2].get(field), context["candidates"][-1][2].get(field))
                for field in material_fields
            )
            curation_explained_change_ids += int(changed and not conflict_codes)

        if context["credential_flag"]:
            disposition = "prohibited"
            reason_code = "credential_or_secret_reference"
        elif conflict_codes or context["unsupported_codes"]:
            disposition = "owner-decision"
            reason_code = "material_conflict_or_unsupported_source"
        elif record.get("action") in raw_actions:
            disposition = "raw-evidence-only"
            reason_code = "legacy_backup_evidence_not_memory_truth"
        elif (
            record.get("action") in retire_actions
            or record.get("category") in retire_categories
            or record.get("validity") in retire_validities
        ):
            disposition = "retire"
            reason_code = "legacy_non_durable_or_deprecated"
        elif (
            record.get("action") == active_gate["action"]
            and record.get("curation_status") == active_gate["curation_status"]
            and record.get("memory_tier") == active_gate["memory_tier"]
            and bool(record.get("source"))
            and bool(record.get("evidence"))
            and not context["finding_types"]
            and semantic_group_size == 1
        ):
            disposition = "migrate-active"
            reason_code = "curated_verified_durable_core"
        else:
            disposition = "migrate-candidate"
            reason_code = "supported_record_requires_verification"

        disposition_counts[disposition] += 1
        reason_counts[reason_code] += 1
        finding_type_counts.update(context["finding_types"])

        age_days: int | None = None
        bucket: str | None = None
        if record and isinstance(record.get("date"), str):
            try:
                age_days = (as_of - date.fromisoformat(record["date"])).days
            except ValueError:
                age_days = None
            if age_days is not None and age_days >= 0:
                bucket = age_bucket(age_days, thresholds)
                age_counts[bucket] += 1

        scope = context["scope"]
        target_plan: dict[str, Any] | None = None
        if disposition in TARGET_STATUS and record and context["kind"] and scope:
            target_plan = {
                "kind": context["kind"],
                "memory_key": memory_key(
                    context["kind"],
                    scope,
                    str(record.get("statement", "")),
                    str(contract["identity"]["memory_key_prefix"]),
                ),
                "scope": scope,
                "status": TARGET_STATUS[disposition],
                "verification_state": "verified" if disposition == "migrate-active" else "unverified",
            }

        active_locator = []
        if context["active"]:
            active_locator.append(locator(*context["active"]))
        candidate_locators = [locator(*row) for row in context["candidates"]]
        secret_locators = [locator(*row) for row in context["secrets"]]
        curation_locator = []
        if context["override"]:
            curation_locator.append(
                {"file_id": "U001", "record_sha256": record_sha256(context["override"])}
            )

        row_hashes = [item["record_sha256"] for item in candidate_locators]
        entry = {
            "schema_version": ENTRY_SCHEMA,
            "legacy_id": legacy_id,
            "source_occurrences": {
                "active": active_locator,
                "candidates": candidate_locators,
                "curation": curation_locator,
                "secret_refs": secret_locators,
            },
            "fingerprints": {
                "candidate_history_sha256": sha256_bytes(canonical_bytes(sorted(row_hashes))),
                "representative_record_sha256": record_sha256(record) if record else None,
                "statement_fingerprint": (
                    "sha256:" + sha256_bytes(context["normalized_statement"].encode("utf-8"))
                    if context["normalized_statement"]
                    else None
                ),
            },
            "quality": {
                "candidate_occurrence_count": len(candidate_locators),
                "candidate_unique_record_hash_count": len(set(row_hashes)),
                "candidate_snapshot_duplicate_count": max(0, len(candidate_locators) - 1),
                "curation_override_present": bool(context["override"]),
                "semantic_duplicate_group_size": semantic_group_size,
                "material_conflict_codes": conflict_codes,
                "unsupported_or_ambiguous_codes": context["unsupported_codes"],
            },
            "freshness": {
                "age_as_of": contract["profile_as_of_date"],
                "age_bucket": bucket,
                "age_days": age_days,
                "age_only_changes_disposition": False,
            },
            "sensitivity": {
                "classification": record.get("sensitivity") if record else "unknown",
                "credential_or_secret_reference_present": context["credential_flag"],
                "finding_types": context["finding_types"],
                "matched_values_included": False,
            },
            "migration": {
                "disposition": disposition,
                "reason_code": reason_code,
                "target_plan": target_plan,
            },
        }
        entries.append(entry)

    allowed_dispositions = list(contract["disposition_contract"]["allowed"])
    full_disposition_counts = {name: disposition_counts.get(name, 0) for name in allowed_dispositions}
    expected_dispositions = contract["quality_contract"]["expected_disposition_counts"]
    if full_disposition_counts != expected_dispositions:
        raise ProfileError(
            "disposition baseline drift detected: observed="
            + json.dumps(full_disposition_counts, sort_keys=True)
        )
    if sum(full_disposition_counts.values()) != len(legacy_ids):
        raise ProfileError("exactly-one disposition gate failed")

    map_bytes = b"".join(canonical_bytes(entry, final_lf=True) for entry in entries)
    max_bytes = int(contract["outputs"]["max_file_bytes"])
    if len(map_bytes) > max_bytes:
        raise ProfileError("migration map exceeds output size gate")

    all_descriptors = active_descriptors + candidate_descriptors + curation_descriptors + secret_descriptors
    active_payloads = [row[2] for row in active_rows]
    active_count = len(active_payloads)

    def coverage(field: str, predicate: Any = None) -> dict[str, int]:
        if predicate is None:
            numerator = sum(row.get(field) not in (None, "", [], {}) for row in active_payloads)
        else:
            numerator = sum(bool(predicate(row)) for row in active_payloads)
        return {
            "numerator": numerator,
            "denominator": active_count,
            "basis_points": (numerator * 10000 // active_count) if active_count else 10000,
        }

    samples: dict[str, list[str]] = {}
    sample_count = int(contract["quality_contract"]["per_nonempty_class_sample_count"])
    for name in allowed_dispositions:
        ids = [entry["legacy_id"] for entry in entries if entry["migration"]["disposition"] == name]
        samples[name] = ids[:sample_count]

    semantic_duplicate_groups = [ids for ids in semantic_groups.values() if len(ids) > 1]
    report = {
        "schema_version": REPORT_SCHEMA,
        "task_id": contract["task_id"],
        "acceptance_id": contract["acceptance_id"],
        "profile_as_of_date": contract["profile_as_of_date"],
        "status": "PASS",
        "artifact_kind": "FULL_CI_ARTIFACT_QUALITY_REPORT",
        "record_values_included": False,
        "input_inventory": {
            "files": all_descriptors,
            "collection_sha256": sha256_bytes(
                canonical_bytes(
                    [
                        {key: row[key] for key in ("path", "bytes", "lines", "sha256")}
                        for row in all_descriptors
                    ]
                )
            ),
            "active_records": len(active_rows),
            "candidate_record_occurrences": len(candidate_rows),
            "curation_overrides": len(overrides),
            "secret_ref_records": len(secret_rows),
            "record_occurrences": len(active_rows) + len(candidate_rows) + len(secret_rows),
            "unique_legacy_ids": len(legacy_ids),
        },
        "coverage": {
            "active_source": coverage("source"),
            "active_valid_time": coverage("date"),
            "active_recorded_time": coverage("activated_at"),
            "active_evidence": coverage("evidence"),
            "old_id_disposition": {
                "numerator": len(entries),
                "denominator": len(legacy_ids),
                "basis_points": 10000,
            },
        },
        "dispositions": {
            "counts": full_disposition_counts,
            "reason_code_counts": dict(sorted(reason_counts.items())),
            "samples": samples,
            "sample_policy": "one legacy ID per non-empty class; no record value",
        },
        "duplicates_and_conflicts": {
            "candidate_snapshot_duplicate_occurrences": sum(
                max(0, len(rows) - 1) for rows in candidates_by_id.values()
            ),
            "candidate_exact_duplicate_row_occurrences": sum(
                max(0, count - 1) for count in exact_candidate_hashes.values()
            ),
            "semantic_duplicate_group_count": len(semantic_duplicate_groups),
            "material_conflict_id_count": material_conflict_ids,
            "curation_explained_change_id_count": curation_explained_change_ids,
            "curation_demoted_duplicate_count": sum(
                1 for value in overrides.values() if value.get("status") == "demoted_duplicate"
            ),
        },
        "freshness": {
            "age_bucket_days": thresholds,
            "age_bucket_counts": dict(sorted(age_counts.items())),
            "age_only_changes_disposition": False,
        },
        "security_and_privacy": {
            "credential_or_secret_id_count": sum(
                1 for context in contexts.values() if context["credential_flag"]
            ),
            "finding_type_counts": dict(sorted(finding_type_counts.items())),
            "matched_values_included": False,
            "raw_instruction_trust": "none",
            "absolute_local_source_ref_id_count": sum(
                "absolute_local_source_ref" in context["unsupported_codes"]
                for context in contexts.values()
            ),
        },
        "migration_map": {
            "path": contract["outputs"]["migration_map"],
            "bytes": len(map_bytes),
            "line_count": len(entries),
            "sha256": sha256_bytes(map_bytes),
        },
        "current_task_effects": contract["current_task_effects"],
        "hard_gates": {
            "credential_or_secret_id_count_zero": not any(
                context["credential_flag"] for context in contexts.values()
            ),
            "each_old_id_exactly_one_disposition": len(entries) == len(legacy_ids),
            "material_conflict_id_count_zero": material_conflict_ids == 0,
            "owner_decision_count_zero": full_disposition_counts["owner-decision"] == 0,
            "record_values_included_zero": True,
            "migration_map_lte_max_file_bytes": len(map_bytes) <= max_bytes,
        },
    }
    report_bytes = canonical_bytes(report, final_lf=True, pretty=True)
    if len(report_bytes) > max_bytes:
        raise ProfileError("quality report exceeds output size gate")
    summary = {
        "status": "PASS",
        "writes_files": False,
        "unique_legacy_ids": len(legacy_ids),
        "record_occurrences": len(active_rows) + len(candidate_rows) + len(secret_rows),
        "disposition_counts": full_disposition_counts,
        "owner_decision_count": full_disposition_counts["owner-decision"],
        "credential_or_secret_id_count": report["security_and_privacy"]["credential_or_secret_id_count"],
        "migration_map_bytes": len(map_bytes),
        "migration_map_sha256": sha256_bytes(map_bytes),
        "quality_report_bytes": len(report_bytes),
        "quality_report_sha256": sha256_bytes(report_bytes),
        "canonical_memory_writes": 0,
    }
    return map_bytes, report_bytes, summary


def atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or (path.exists() and path.is_symlink()):
        raise ProfileError("symlink output path rejected")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", default=".")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Build and validate in memory without writes.")
    mode.add_argument("--write", action="store_true", help="Atomically write only the two derived deliverables.")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    database_dir = Path(args.database_dir).resolve()
    if not database_dir.is_dir() or database_dir.is_symlink():
        raise ProfileError("invalid database directory")
    contract_path = safe_repo_path(database_dir, str(args.contract), must_exist=True)
    contract = load_json_bytes(contract_path.read_bytes(), str(args.contract))
    if not isinstance(contract, dict) or contract.get("schema_version") != "openai_database.memory_profiling_contract.v1":
        raise ProfileError("invalid profiling contract")
    map_bytes, report_bytes, summary = build_profile(database_dir, contract)
    if args.write:
        map_path = safe_repo_path(database_dir, contract["outputs"]["migration_map"], must_exist=False)
        report_path = safe_repo_path(database_dir, contract["outputs"]["quality_report"], must_exist=False)
        atomic_write(map_path, map_bytes)
        atomic_write(report_path, report_bytes)
        summary["writes_files"] = True
    return summary


def main(argv: list[str] | None = None) -> int:
    try:
        result = run(argv)
    except ProfileError as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "writes_files": False, "reason": str(exc)}, sort_keys=True))
        return 2
    except Exception as exc:  # pragma: no cover - final non-disclosure shield
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "writes_files": False,
                    "reason": f"unexpected internal error: {type(exc).__name__}",
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
