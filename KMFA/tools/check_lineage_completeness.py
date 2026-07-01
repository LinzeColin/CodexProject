#!/usr/bin/env python3
"""Validate the KMFA public-safe lineage completeness review gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("KMFA/metadata/lineage/lineage_completeness_review.json")

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "private://",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "recipient_email",
    "smtp",
    "sk-",
    "-----BEGIN",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} contains a non-object JSONL row")
        rows.append(value)
    return rows


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_false(label: str, actual: Any) -> None:
    if actual is not False:
        raise ValueError(f"{label}: expected false, got {actual!r}")


def _require_non_empty_list(label: str, value: Any) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}: expected non-empty list")
    return value


def _require_false_flags(label: str, payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{label}: expected non-empty object")
    for key, value in payload.items():
        _require_false(f"{label}.{key}", value)


def _require_existing_refs(refs: Any) -> None:
    missing = [ref for ref in _require_non_empty_list("source_refs", refs) if not isinstance(ref, str) or not Path(ref).exists()]
    if missing:
        raise ValueError("missing lineage refs: " + ", ".join(map(str, missing)))


def _validate_no_forbidden_public_text(payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for text in FORBIDDEN_PUBLIC_TEXT:
        if text in encoded:
            raise ValueError(f"forbidden public text found: {text}")


def validate_lineage_completeness_review(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, int]:
    manifest = _read_json(manifest_path)

    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.lineage_completeness_review.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("review_id", manifest.get("review_id"), "KMFA-LINEAGE-COMPLETENESS-REVIEW-20260702")
    _require_equal("status", manifest.get("status"), "blocked_not_complete")
    _require_equal("blocker_ids", manifest.get("blocker_ids"), ["LINEAGE_FULL_CHECK_NOT_COMPLETE"])
    _require_false("lineage_full_check_complete", manifest.get("lineage_full_check_complete"))
    _require_false("lineage_full_check_performed", manifest.get("lineage_full_check_performed"))
    _require_false("delivery_allowed", manifest.get("delivery_allowed"))
    _require_false("official_report_release_allowed", manifest.get("official_report_release_allowed"))
    _require_false("business_decision_basis_allowed", manifest.get("business_decision_basis_allowed"))
    _require_false("github_upload_allowed", manifest.get("github_upload_allowed"))
    _require_false("external_connector_allowed", manifest.get("external_connector_allowed"))
    _require_false("business_execution_allowed", manifest.get("business_execution_allowed"))
    _require_false_flags("public_repo_safety", manifest.get("public_repo_safety", {}))
    _require_existing_refs(manifest.get("source_refs"))

    expected_counts = {
        "field_lineage_records": len(_read_jsonl(Path("KMFA/metadata/lineage/field_lineage.jsonl"))),
        "metric_lineage_records": len(_read_jsonl(Path("KMFA/metadata/lineage/metric_lineage.jsonl"))),
        "report_lineage_records": len(_read_jsonl(Path("KMFA/metadata/lineage/report_lineage.jsonl"))),
        "manual_rerun_steps": len(_read_jsonl(Path("KMFA/metadata/lineage/manual_rerun_steps.jsonl"))),
        "manual_rerun_consistency_checks": len(_read_jsonl(Path("KMFA/metadata/lineage/manual_rerun_consistency_checks.jsonl"))),
    }
    counts = manifest.get("lineage_counts")
    if not isinstance(counts, dict):
        raise ValueError("lineage_counts: expected object")
    for key, expected in expected_counts.items():
        _require_equal(f"lineage_counts.{key}", counts.get(key), expected)

    gates = _require_non_empty_list("minimum_required_full_lineage_gates", manifest.get("minimum_required_full_lineage_gates"))
    if len(gates) != 4:
        raise ValueError("minimum_required_full_lineage_gates must contain four gate names")
    _validate_no_forbidden_public_text(manifest)
    return expected_counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA public-safe lineage completeness review.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)

    try:
        counts = validate_lineage_completeness_review(args.manifest)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA lineage completeness gate is safely blocked "
        f"(field={counts['field_lineage_records']}, "
        f"metric={counts['metric_lineage_records']}, "
        f"report={counts['report_lineage_records']}, "
        f"rerun_steps={counts['manual_rerun_steps']}, "
        "delivery_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
