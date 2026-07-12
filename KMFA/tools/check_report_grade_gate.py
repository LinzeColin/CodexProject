#!/usr/bin/env python3
"""Validate the KMFA S02-P3 quality/report grade gate protocol.

This check validates policy definitions and release-gate invariants only. It
does not run real zero-delta, lineage completeness, business import, or report
generation because those are later roadmap stages.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "metadata"

QUALITY_ORDER = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5"]
REPORT_ORDER = ["A", "B", "C", "D"]

REQUIRED_FILES = [
    ROOT / "docs" / "governance" / "QUALITY_GATE_POLICY.md",
    METADATA / "quality" / "quality_grade_policy.yaml",
    METADATA / "quality" / "data_quality_results.jsonl",
    METADATA / "reports" / "report_grade_policy.yaml",
    METADATA / "reports" / "report_release_gate.yaml",
    METADATA / "reports" / "report_manifest.jsonl",
]

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


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{rel(path)} is not parseable JSON/YAML subset: {exc}")
    if not isinstance(data, dict):
        fail(f"{rel(path)} must be a JSON object")
    return data


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"{rel(path)}:{line_no} invalid JSONL: {exc}")
        if not isinstance(record, dict):
            fail(f"{rel(path)}:{line_no} must be a JSON object")
        records.append(record)
    if not records:
        fail(f"{rel(path)} must contain a protocol header")
    return records


def walk_json(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                fail(f"forbidden key {key!r} at {label}")
            walk_json(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_json(child, f"{label}[{index}]")


def is_ignored_untracked_private_runtime(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    if ".codex_private_runtime" not in parts and "private_runtime" not in parts:
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


def check_required_files() -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"missing quality gate file: {rel(path)}")


def check_quality_grades() -> None:
    policy = load_json(METADATA / "quality" / "quality_grade_policy.yaml")
    if policy.get("append_only") is not True:
        fail("quality grade policy must be append-only")
    if policy.get("forbidden_plaintext") is not True:
        fail("quality grade policy must set forbidden_plaintext=true")
    grades = policy.get("quality_grades")
    if not isinstance(grades, list):
        fail("quality grade policy missing quality_grades list")
    by_grade = {item.get("grade"): item for item in grades if isinstance(item, dict)}
    if list(by_grade) != QUALITY_ORDER:
        fail("quality grades must be ordered exactly: " + ", ".join(QUALITY_ORDER))
    for grade in ["Q0", "Q1", "Q2"]:
        item = by_grade[grade]
        if item.get("formal_internal_report_allowed") is not False:
            fail(f"{grade} must not allow formal internal reports")
        if item.get("internal_review_report_allowed") is not False:
            fail(f"{grade} must not allow internal review reports")
        if item.get("preview_allowed") is not False:
            fail(f"{grade} must not allow previews")
        if item.get("decision_use_allowed") is not False:
            fail(f"{grade} must not allow decision use")
    if by_grade["Q3"].get("preview_allowed") is not True:
        fail("Q3 must allow preview only")
    if by_grade["Q3"].get("formal_internal_report_allowed") is not False:
        fail("Q3 must not allow formal internal reports")
    if by_grade["Q4"].get("internal_review_report_allowed") is not True:
        fail("Q4 must allow internal review reports")
    if by_grade["Q4"].get("formal_internal_report_allowed") is not False:
        fail("Q4 must not allow formal internal reports")
    if by_grade["Q5"].get("formal_internal_report_allowed") is not True:
        fail("Q5 must allow formal internal reports")


def check_report_grades() -> None:
    policy = load_json(METADATA / "reports" / "report_grade_policy.yaml")
    grades = policy.get("report_grades")
    if not isinstance(grades, list):
        fail("report grade policy missing report_grades list")
    by_grade = {item.get("grade"): item for item in grades if isinstance(item, dict)}
    if list(by_grade) != REPORT_ORDER:
        fail("report grades must be ordered exactly: " + ", ".join(REPORT_ORDER))
    grade_a = by_grade["A"]
    if grade_a.get("minimum_quality_grade") != "Q5":
        fail("A reports must require Q5")
    for key in [
        "zero_delta_required",
        "critical_differences_closed_required",
        "human_confirmation_required",
    ]:
        if grade_a.get(key) is not True:
            fail(f"A reports must require {key}")
    if grade_a.get("release_permission") != "formal_internal_report":
        fail("A reports must map to formal_internal_report")

    grade_b = by_grade["B"]
    if grade_b.get("minimum_quality_grade") != "Q4":
        fail("B reports must require Q4 or higher")
    if grade_b.get("critical_differences_explainable_required") is not True:
        fail("B reports must require explainable critical differences")
    if grade_b.get("limitations_required") is not True:
        fail("B reports must require explicit limitations")
    if grade_b.get("release_permission") != "internal_review_report":
        fail("B reports must map to internal_review_report")

    grade_c = by_grade["C"]
    if grade_c.get("minimum_quality_grade") != "Q3":
        fail("C reports must require Q3")
    if grade_c.get("preview_only") is not True:
        fail("C reports must be preview only")
    if grade_c.get("release_permission") != "preview_only":
        fail("C reports must map to preview_only")

    grade_d = by_grade["D"]
    if grade_d.get("business_decision_basis_allowed") is not False:
        fail("D reports must not be business decision basis")
    if grade_d.get("release_permission") != "blocked_decision_use":
        fail("D reports must map to blocked_decision_use")


def check_release_gate() -> None:
    gate = load_json(METADATA / "reports" / "report_release_gate.yaml")
    mapping = gate.get("quality_to_report_gate")
    if not isinstance(mapping, list):
        fail("report release gate missing quality_to_report_gate list")
    by_quality = {item.get("quality_grade"): item for item in mapping if isinstance(item, dict)}
    if list(by_quality) != QUALITY_ORDER:
        fail("quality_to_report_gate must cover Q0-Q5 in order")
    for grade in ["Q0", "Q1", "Q2"]:
        if by_quality[grade].get("maximum_report_grade") != "D":
            fail(f"{grade} must be capped at D")
        if by_quality[grade].get("release_permission") != "blocked":
            fail(f"{grade} must be blocked")
    expected = {
        "Q3": ("C", "preview_only"),
        "Q4": ("B", "internal_review_report"),
        "Q5": ("A", "formal_internal_report"),
    }
    for grade, (report_grade, permission) in expected.items():
        item = by_quality[grade]
        if item.get("maximum_report_grade") != report_grade:
            fail(f"{grade} must be capped at {report_grade}")
        if item.get("release_permission") != permission:
            fail(f"{grade} must map to {permission}")
    if gate.get("missing_gate_evidence_policy") != "block_release":
        fail("missing gate evidence must block release")
    for block in ["unresolved_critical_difference", "zero_delta_failed", "missing_required_lineage"]:
        if block not in gate.get("hard_blocks", []):
            fail(f"release gate missing hard block: {block}")


def check_metadata_headers() -> None:
    data_quality_header = iter_jsonl(METADATA / "quality" / "data_quality_results.jsonl")[0]
    report_header = iter_jsonl(METADATA / "reports" / "report_manifest.jsonl")[0]
    if data_quality_header.get("allowed_quality_grades") != QUALITY_ORDER:
        fail("data_quality_results header must list Q0-Q5")
    if data_quality_header.get("forbidden_plaintext") is not True:
        fail("data_quality_results header must set forbidden_plaintext=true")
    if report_header.get("allowed_report_grades") != REPORT_ORDER:
        fail("report_manifest header must list A-D")
    if report_header.get("quality_gate_required") is not True:
        fail("report_manifest header must require quality gate")
    if report_header.get("forbidden_plaintext") is not True:
        fail("report_manifest header must set forbidden_plaintext=true")


def check_privacy_boundary() -> None:
    bad_suffixes = []
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            if is_ignored_untracked_private_runtime(path):
                continue
            bad_suffixes.append(str(path.relative_to(ROOT)))
    if bad_suffixes:
        fail("forbidden raw/sensitive file-like artifacts: " + ", ".join(bad_suffixes[:20]))
    structured_files = [
        METADATA / "quality" / "quality_grade_policy.yaml",
        METADATA / "reports" / "report_grade_policy.yaml",
        METADATA / "reports" / "report_release_gate.yaml",
    ]
    for path in structured_files:
        walk_json(load_json(path), rel(path))
    for path in [
        METADATA / "quality" / "data_quality_results.jsonl",
        METADATA / "reports" / "report_manifest.jsonl",
    ]:
        for record in iter_jsonl(path):
            walk_json(record, rel(path))


def main() -> int:
    check_required_files()
    check_quality_grades()
    check_report_grades()
    check_release_gate()
    check_metadata_headers()
    check_privacy_boundary()
    print(
        "PASS: KMFA report grade gate check passed "
        "(quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
