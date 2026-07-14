#!/usr/bin/env python3
"""Validate the KMFA S02-P1 metadata protocol.

The check intentionally validates structure, identifier definitions, parseable
metadata placeholders, and public-repo privacy boundaries. It does not validate
business imports because S02-P1 only defines the protocol.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "metadata"

REQUIRED_DIRS = [
    "sources",
    "imports",
    "schema_maps",
    "quality",
    "lineage",
    "reports",
    "approvals",
    "protocol",
]

REQUIRED_FILES = [
    "sources/source_registry.yaml",
    "sources/source_priority_policy.yaml",
    "sources/source_priority_events.jsonl",
    "imports/import_runs.jsonl",
    "imports/raw_file_manifest.jsonl",
    "schema_maps/source_mapping_versions.yaml",
    "quality/data_quality_results.jsonl",
    "quality/zero_delta_results.jsonl",
    "quality/mismatch_report.csv",
    "quality/source_difference_queue.jsonl",
    "lineage/field_lineage.jsonl",
    "lineage/metric_lineage.jsonl",
    "lineage/report_lineage.jsonl",
    "approvals/resolution_events.jsonl",
    "approvals/human_signoff_log.jsonl",
    "reports/report_manifest.jsonl",
    "protocol/metadata_protocol.yaml",
    "protocol/directory_manifest.json",
    "protocol/field_dictionary.csv",
]

REQUIRED_IDENTIFIERS = {
    "import_run_id",
    "source_id",
    "file_hash",
    "formula_version",
    "mapping_version",
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

FORBIDDEN_KEYS = {
    "raw_value",
    "original_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json_file(path: Path) -> dict[str, Any]:
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
        fail(f"{path.relative_to(ROOT)} must contain a protocol header record")
    return records


def check_required_paths() -> None:
    for rel in REQUIRED_DIRS:
        path = METADATA / rel
        if not path.is_dir():
            fail(f"missing metadata directory: metadata/{rel}")
    for rel in REQUIRED_FILES:
        path = METADATA / rel
        if not path.is_file():
            fail(f"missing metadata protocol file: metadata/{rel}")


def check_identifier_protocol() -> None:
    protocol = load_json_file(METADATA / "protocol" / "metadata_protocol.yaml")
    identifiers = protocol.get("identifiers")
    if not isinstance(identifiers, dict):
        fail("metadata_protocol.yaml missing identifiers object")
    missing = sorted(REQUIRED_IDENTIFIERS - set(identifiers))
    if missing:
        fail("metadata_protocol.yaml missing identifiers: " + ", ".join(missing))
    for identifier, spec in identifiers.items():
        if identifier not in REQUIRED_IDENTIFIERS:
            continue
        if not isinstance(spec, dict):
            fail(f"{identifier} spec must be an object")
        regex = spec.get("regex")
        example = spec.get("example")
        if not isinstance(regex, str) or not regex:
            fail(f"{identifier} missing regex")
        if not isinstance(example, str) or not example:
            fail(f"{identifier} missing example")
        if not re.match(regex, example):
            fail(f"{identifier} example does not match regex")

    policy = protocol.get("metadata_storage_policy")
    if not isinstance(policy, dict):
        fail("metadata_protocol.yaml missing metadata_storage_policy")
    if policy.get("public_repo_sensitive_plaintext_allowed") is not False:
        fail("public_repo_sensitive_plaintext_allowed must be false")


def check_jsonl_and_csv_files() -> None:
    jsonl_protocol_files = [METADATA / rel for rel in REQUIRED_FILES if rel.endswith(".jsonl")]
    for path in jsonl_protocol_files:
        records = iter_jsonl(path)
        for record in records:
            if record.get("forbidden_plaintext") is not True and "raw_file_manifest" not in path.name:
                fail(f"{path.relative_to(ROOT)} protocol header must set forbidden_plaintext=true")

    for rel in ["quality/mismatch_report.csv", "protocol/field_dictionary.csv"]:
        path = METADATA / rel
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                fail(f"{path.relative_to(ROOT)} is empty")
        if not header or any(not col.strip() for col in header):
            fail(f"{path.relative_to(ROOT)} has an invalid CSV header")


def check_manifest_alignment() -> None:
    manifest = load_json_file(METADATA / "protocol" / "directory_manifest.json")
    dirs = set(manifest.get("directories") or [])
    files = set(manifest.get("required_files") or [])
    expected_dirs = {f"metadata/{item}" for item in REQUIRED_DIRS if item != "protocol"}
    expected_files = {f"metadata/{item}" for item in REQUIRED_FILES}
    missing_dirs = sorted(expected_dirs - dirs)
    missing_files = sorted(expected_files - files)
    if missing_dirs:
        fail("directory_manifest.json missing directories: " + ", ".join(missing_dirs))
    if missing_files:
        fail("directory_manifest.json missing files: " + ", ".join(missing_files))
    if manifest.get("raw_sensitive_data_public_repo_allowed") is not False:
        fail("directory_manifest raw_sensitive_data_public_repo_allowed must be false")
    if manifest.get("business_records_committed") is not False:
        fail("S02-P1 must not commit business records")


def walk_json(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                fail(f"forbidden metadata key {key!r} at {path}")
            walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            walk_json(child, f"{path}[{idx}]")


def is_ignored_untracked_private_runtime(path: Path) -> bool:
    if "private_runtime" not in path.relative_to(METADATA).parts:
        return False
    repo_root = ROOT.parent
    repo_rel = path.relative_to(repo_root).as_posix()
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", repo_rel],
        cwd=repo_root,
        check=False,
    ).returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", repo_rel],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    return ignored and not tracked


def check_privacy_boundary() -> None:
    bad_suffixes = []
    for path in METADATA.rglob("*"):
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            if is_ignored_untracked_private_runtime(path):
                continue
            bad_suffixes.append(str(path.relative_to(ROOT)))
    if bad_suffixes:
        fail("forbidden raw/sensitive file-like artifacts: " + ", ".join(bad_suffixes))

    json_subset_yaml_files = [
        METADATA / "protocol" / "metadata_protocol.yaml",
        METADATA / "sources" / "source_registry.yaml",
        METADATA / "sources" / "source_priority_policy.yaml",
        METADATA / "schema_maps" / "source_mapping_versions.yaml",
    ]
    for path in list(METADATA.rglob("*.json")) + json_subset_yaml_files:
        walk_json(load_json_file(path), str(path.relative_to(ROOT)))
    for path in METADATA.rglob("*.jsonl"):
        for record in iter_jsonl(path):
            walk_json(record, str(path.relative_to(ROOT)))


def main() -> int:
    check_required_paths()
    check_identifier_protocol()
    check_jsonl_and_csv_files()
    check_manifest_alignment()
    check_privacy_boundary()
    print(
        "PASS: KMFA metadata protocol check passed "
        f"(dirs={len(REQUIRED_DIRS)}, files={len(REQUIRED_FILES)}, identifiers={len(REQUIRED_IDENTIFIERS)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
