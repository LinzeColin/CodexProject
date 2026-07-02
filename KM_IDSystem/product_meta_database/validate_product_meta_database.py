#!/usr/bin/env python3
"""Validate the IDS ProductMetaDatabase static skeleton."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PRODUCT_ID = "IDS"
SUBSYSTEM = "ProductMetaDatabase"
STAGE = "STAGE-002"
ACCEPTANCE_ID = "ACC-STAGE-002"


def _load_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return payload


def _relative_contract_files(root: Path) -> list[str]:
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_file():
            files.append(path.relative_to(root).as_posix())
    return files


def _json_without_marker_definitions(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict):
        payload = dict(payload)
        payload.pop("blocked_content_markers", None)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _scan_forbidden_markers(root: Path, contract_files: list[str], markers: list[str]) -> list[str]:
    hits: list[str] = []
    for relative_path in contract_files:
        path = root / relative_path
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            hits.append(f"{relative_path}:binary")
            continue
        if relative_path == "governance_rules/product_metadata_rules.json":
            text = _json_without_marker_definitions(text)
        for marker in markers:
            if marker in text:
                hits.append(f"{relative_path}:{marker}")
    return hits


def _forbidden_runtime_paths_present(root: Path, blocked_subpaths: list[str]) -> bool:
    for subpath in blocked_subpaths:
        candidate = root / subpath.rstrip("/")
        if candidate.exists():
            return True
    return False


def validate_repository(root: Path | str | None = None) -> dict[str, Any]:
    product_meta_root = Path(root) if root is not None else Path(__file__).resolve().parent
    product_meta_root = product_meta_root.resolve()

    rules = _load_json(product_meta_root, "governance_rules/product_metadata_rules.json")
    required_contracts = rules.get("required_contracts", {})
    if not isinstance(required_contracts, dict):
        raise ValueError("governance_rules.required_contracts must be an object")

    loaded_contracts = {
        name: _load_json(product_meta_root, relative_path)
        for name, relative_path in required_contracts.items()
    }

    schema = loaded_contracts["product_metadata_schema"]
    manifest = loaded_contracts["product_manifest_template"]
    taskpack_input = loaded_contracts["taskpack_input"]

    lineage_properties = (
        schema.get("properties", {})
        .get("lineage", {})
        .get("properties", {})
    )
    future_lineage_fields = sorted(lineage_properties)

    contract_files = _relative_contract_files(product_meta_root)
    max_file_bytes = max((product_meta_root / path).stat().st_size for path in contract_files)
    blocked_subpaths = list(rules.get("blocked_subpaths", []))
    blocked_markers = list(rules.get("blocked_content_markers", []))
    forbidden_markers = _scan_forbidden_markers(product_meta_root, contract_files, blocked_markers)

    issues: list[str] = []
    expected_pairs = {
        "product_id": PRODUCT_ID,
        "subsystem": SUBSYSTEM,
        "stage": STAGE,
        "acceptance_id": ACCEPTANCE_ID,
    }
    for key, expected in expected_pairs.items():
        for contract_name, payload in {
            "manifest": manifest,
            "rules": rules,
            "taskpack_input": taskpack_input,
        }.items():
            if payload.get(key) != expected:
                issues.append(f"{contract_name}.{key} != {expected}")

    if manifest.get("schema_ref") != required_contracts["product_metadata_schema"]:
        issues.append("manifest.schema_ref does not match required contract")
    if manifest.get("governance_rules_ref") != required_contracts["governance_rules"]:
        issues.append("manifest.governance_rules_ref does not match required contract")
    if manifest.get("taskpack_input_ref") != required_contracts["taskpack_input"]:
        issues.append("manifest.taskpack_input_ref does not match required contract")

    external_api_policy = rules.get("external_api_policy")
    raw_material_policy = rules.get("raw_material_policy")
    if external_api_policy != "denied":
        issues.append("external_api_policy must be denied")
    if raw_material_policy != "forbidden":
        issues.append("raw_material_policy must be forbidden")
    if forbidden_markers:
        issues.append("forbidden markers detected")
    if max_file_bytes > int(rules.get("max_contract_file_bytes", 0)):
        issues.append("contract file exceeds max_contract_file_bytes")

    forbidden_runtime_paths_present = _forbidden_runtime_paths_present(product_meta_root, blocked_subpaths)
    if forbidden_runtime_paths_present:
        issues.append("forbidden runtime subpath exists inside ProductMetaDatabase")

    return {
        "valid": not issues,
        "issues": issues,
        "product_id": PRODUCT_ID,
        "subsystem": SUBSYSTEM,
        "stage": STAGE,
        "acceptance_id": ACCEPTANCE_ID,
        "external_api_policy": external_api_policy,
        "raw_material_policy": raw_material_policy,
        "contracts": sorted(required_contracts),
        "contract_files": contract_files,
        "future_lineage_fields": future_lineage_fields,
        "forbidden_markers": forbidden_markers,
        "forbidden_runtime_paths_present": forbidden_runtime_paths_present,
        "max_contract_file_bytes": max_file_bytes,
    }


def main() -> int:
    report = validate_repository()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
