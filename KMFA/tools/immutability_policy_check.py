#!/usr/bin/env python3
"""Validate the KMFA S02-P2 immutability policy.

This check validates raw manifest constraints, derived-data versioning rules,
and frontend/control-event write boundaries without importing raw business
files or storing sensitive plaintext.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "metadata"

REQUIRED_FILES = [
    ROOT / "docs" / "governance" / "IMMUTABILITY_POLICY.md",
    METADATA / "imports" / "raw_manifest_schema.json",
    METADATA / "imports" / "raw_manifest_policy.yaml",
    METADATA / "lineage" / "derived_data_policy.yaml",
    METADATA / "lineage" / "derived_data_versions.jsonl",
    METADATA / "approvals" / "control_event_policy.yaml",
    METADATA / "approvals" / "control_events.jsonl",
]

RAW_MANIFEST_IMMUTABLE_FIELDS = {
    "import_run_id",
    "source_id",
    "file_hash",
    "storage_ref",
    "original_filename_hash",
}

FORBIDDEN_KEYS = {
    "raw_file_bytes",
    "raw_value",
    "original_value",
    "plaintext_content",
    "full_file_text",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}

FORBIDDEN_SUFFIXES = {
    ".zip",
    ".xls",
    ".xlsx",
    ".pdf",
    ".sqlite",
    ".db",
    ".sqlite-shm",
    ".sqlite-wal",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)} is not parseable JSON/YAML subset: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must be a JSON object")
    return data


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"{path.relative_to(ROOT)}:{line_no} invalid JSONL: {exc}")
        if not isinstance(record, dict):
            fail(f"{path.relative_to(ROOT)}:{line_no} must be a JSON object")
        records.append(record)
    if not records:
        fail(f"{path.relative_to(ROOT)} must contain a protocol header")
    return records


def walk_json(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS and key not in {"forbidden_fields"}:
                fail(f"forbidden key {key!r} at {label}")
            walk_json(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_json(child, f"{label}[{index}]")


def check_required_files() -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"missing immutability policy file: {path.relative_to(ROOT)}")


def check_raw_manifest_policy() -> None:
    schema = load_json(METADATA / "imports" / "raw_manifest_schema.json")
    policy = load_json(METADATA / "imports" / "raw_manifest_policy.yaml")

    immutable_schema = set(schema.get("immutable_fields") or [])
    immutable_policy = set(policy.get("immutable_fields") or [])
    missing_schema = sorted(RAW_MANIFEST_IMMUTABLE_FIELDS - immutable_schema)
    missing_policy = sorted(RAW_MANIFEST_IMMUTABLE_FIELDS - immutable_policy)
    if missing_schema:
        fail("raw_manifest_schema missing immutable fields: " + ", ".join(missing_schema))
    if missing_policy:
        fail("raw_manifest_policy missing immutable fields: " + ", ".join(missing_policy))
    if schema.get("raw_file_bytes_public_repo_allowed") is not False:
        fail("raw manifest schema must forbid raw file bytes in public repo")
    if schema.get("raw_extracted_values_public_repo_allowed") is not False:
        fail("raw manifest schema must forbid raw extracted values in public repo")
    if policy.get("append_only") is not True:
        fail("raw manifest policy must be append-only")
    if policy.get("mutates_original_file") is not False:
        fail("raw manifest policy must not mutate original files")
    if policy.get("mutates_original_extracted_value") is not False:
        fail("raw manifest policy must not mutate original extracted values")

    records = iter_jsonl(METADATA / "imports" / "raw_file_manifest.jsonl")
    header = records[0]
    if header.get("raw_file_bytes_public_repo_allowed") is not False:
        fail("raw_file_manifest.jsonl header must forbid raw file bytes")
    if "file_hash" not in header.get("required_identifiers", []):
        fail("raw_file_manifest.jsonl header must require file_hash")


def check_derived_policy() -> None:
    policy = load_json(METADATA / "lineage" / "derived_data_policy.yaml")
    if policy.get("append_only") is not True:
        fail("derived data policy must be append-only")
    if policy.get("overwrite_old_version_allowed") is not False:
        fail("derived data policy must forbid overwriting old versions")
    for action in ["invalidate_version", "rerun_version", "compare_versions"]:
        if action not in policy.get("allowed_actions", []):
            fail(f"derived data policy missing action: {action}")
    if policy.get("raw_layer_write_allowed") is not False:
        fail("derived data policy must forbid raw layer writes")

    header = iter_jsonl(METADATA / "lineage" / "derived_data_versions.jsonl")[0]
    if header.get("append_only") is not True:
        fail("derived_data_versions header must be append-only")
    if header.get("overwrite_old_version_allowed") is not False:
        fail("derived_data_versions header must forbid overwriting")


def check_control_event_policy() -> None:
    policy = load_json(METADATA / "approvals" / "control_event_policy.yaml")
    if policy.get("append_only") is not True:
        fail("control event policy must be append-only")
    if policy.get("raw_layer_write_allowed") is not False:
        fail("control event policy must forbid raw layer writes")
    for layer in ["raw", "raw_file_manifest_immutable_fields", "original_extracted_values"]:
        if layer not in policy.get("forbidden_target_layers", []):
            fail(f"control event policy missing forbidden layer: {layer}")
    for event_type in ["mapping_rule", "resolution_event", "approval_event", "comment"]:
        if event_type not in policy.get("allowed_event_types", []):
            fail(f"control event policy missing allowed event type: {event_type}")

    header = iter_jsonl(METADATA / "approvals" / "control_events.jsonl")[0]
    if header.get("raw_layer_write_allowed") is not False:
        fail("control_events header must forbid raw layer writes")
    if header.get("append_only") is not True:
        fail("control_events header must be append-only")


def check_privacy_boundary() -> None:
    bad_suffixes = []
    for path in ROOT.rglob("*"):
        if ".codex_private_runtime" in path.relative_to(ROOT).parts:
            continue
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            bad_suffixes.append(str(path.relative_to(ROOT)))
    if bad_suffixes:
        fail("forbidden raw/sensitive file-like artifacts: " + ", ".join(bad_suffixes[:20]))

    structured_files = [
        METADATA / "imports" / "raw_manifest_schema.json",
        METADATA / "imports" / "raw_manifest_policy.yaml",
        METADATA / "lineage" / "derived_data_policy.yaml",
        METADATA / "approvals" / "control_event_policy.yaml",
    ]
    for path in structured_files:
        walk_json(load_json(path), str(path.relative_to(ROOT)))
    for path in [
        METADATA / "lineage" / "derived_data_versions.jsonl",
        METADATA / "approvals" / "control_events.jsonl",
    ]:
        for record in iter_jsonl(path):
            walk_json(record, str(path.relative_to(ROOT)))


def main() -> int:
    check_required_files()
    check_raw_manifest_policy()
    check_derived_policy()
    check_control_event_policy()
    check_privacy_boundary()
    print(
        "PASS: KMFA immutability policy check passed "
        "(raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
