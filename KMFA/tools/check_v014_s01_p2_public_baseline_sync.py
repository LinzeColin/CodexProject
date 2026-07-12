#!/usr/bin/env python3
"""Validate KMFA v1.4 S01-P2 public-safe baseline sync evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


S01P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/machine/"
    "s01_p1_read_only_scope_lock_manifest.json"
)
S01P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/machine/"
    "s01_p2_public_baseline_sync_manifest.json"
)
TASKPACK_BASELINE_MANIFEST_PATH = Path("KMFA/taskpack/v1_4/machine/source_package_manifest.json")
METADATA_BASELINE_MANIFEST_PATH = Path("KMFA/metadata/baseline/source_package_v1_4.json")
BASELINE_ROOT = Path("KMFA/taskpack/v1_4")
EVIDENCE_ROOT = Path("KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC")

REQUIRED_BASELINE_TARGETS = {
    "v1.4 taskpack": Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md"),
    "v1.4 roadmap": Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md"),
    "v1.4 README": Path("KMFA/taskpack/v1_4/README.source.md"),
    "v1.4 HTML entry": Path("KMFA/taskpack/v1_4/html_uiux/00_KMFA_HTML_human_flow_entry_v1_4.html"),
    "v1.4 HTML human-flow audit script": Path("KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py"),
    "v1.4 HTML human-flow audit report": Path(
        "KMFA/taskpack/v1_4/html_uiux/KMFA_HTML_human_flow_audit_report_v1_4.md"
    ),
    "v1.4 raw data roots policy": Path("KMFA/taskpack/v1_4/raw_data_protocol/KMFA_raw_data_roots_v1_4.yaml"),
    "v1.4 Codex read-only raw-data prompt": Path(
        "KMFA/taskpack/v1_4/raw_data_protocol/CODEX_read_only_raw_data_prompt_v1_4.md"
    ),
    "v1.2 HTML inheritance note retained for history": Path(
        "KMFA/taskpack/v1_4/history/KMFA_HTML_UIUX_inheritance_note_v1_2.md"
    ),
}
REQUIRED_EVIDENCE_FILES = [
    Path("KMFA/taskpack/v1_4/PUBLIC_SAFE_BASELINE.md"),
    TASKPACK_BASELINE_MANIFEST_PATH,
    METADATA_BASELINE_MANIFEST_PATH,
    Path("KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/human/s01_p2_completion_record.md"),
    Path("KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/human/risk_register.md"),
    Path("KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/human/rollback_plan.md"),
    Path("KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/human/test_results.md"),
    S01P2_MANIFEST_PATH,
]
FORBIDDEN_EXTENSIONS = {
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".mov",
}
FORBIDDEN_MANIFEST_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_path",
    "member_name",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def repo_tree_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def source_package_hashes(package_path: Path) -> set[str]:
    hashes: set[str] = set()
    with zipfile.ZipFile(package_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            hashes.add(sha256_bytes(zf.read(info)))
    return hashes


def validate_v014_s01_p2_public_baseline_sync(
    manifest_path: Path = S01P2_MANIFEST_PATH,
    *,
    require_source_package_present: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    s01p1 = read_json(S01P1_MANIFEST_PATH)
    manifest = read_json(manifest_path)
    baseline_manifest = read_json(TASKPACK_BASELINE_MANIFEST_PATH)
    metadata_manifest = read_json(METADATA_BASELINE_MANIFEST_PATH)

    require(manifest.get("schema_version") == "kmfa.v014_s01_p2_public_baseline_sync.v1", "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_phase") == "S01-P2", "stage_phase must be S01-P2", errors)
    require(
        manifest.get("task_id") == "KMFA-V014-S01-P2-PUBLIC-BASELINE-SYNC-20260703",
        "task_id mismatch",
        errors,
    )
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred",
        "status mismatch",
        errors,
    )

    dependency = manifest.get("dependency", {})
    require(dependency.get("required_phase") == "S01-P1", "dependency must be S01-P1", errors)
    require(dependency.get("dependency_status") == s01p1.get("status"), "S01-P1 dependency status mismatch", errors)
    require(s01p1.get("scope_lock", {}).get("next_phase") == "S01-P2", "S01-P1 next phase must be S01-P2", errors)

    phase_scope = manifest.get("phase_scope", {})
    require(phase_scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(phase_scope.get("business_code_modified") is False, "business code must not be modified", errors)
    require(phase_scope.get("product_runtime_modified") is False, "product runtime must not be modified", errors)
    require(phase_scope.get("s01_p3_started") is False, "S01-P3 must not be started", errors)
    require(phase_scope.get("stage_review_performed") is False, "Stage 1 review must not be performed", errors)
    require(phase_scope.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(phase_scope.get("next_phase") == "S01-P3", "next phase must be S01-P3", errors)
    require(phase_scope.get("next_phase_started") is False, "next phase must not be started", errors)

    baseline_sync = manifest.get("baseline_sync", {})
    require(baseline_sync.get("repo_baseline_root") == str(BASELINE_ROOT), "baseline root mismatch", errors)
    require(baseline_sync.get("metadata_baseline_manifest") == str(METADATA_BASELINE_MANIFEST_PATH), "metadata manifest path mismatch", errors)
    require(baseline_sync.get("taskpack_baseline_manifest") == str(TASKPACK_BASELINE_MANIFEST_PATH), "taskpack manifest path mismatch", errors)
    require(baseline_sync.get("copied_public_source_count") == 9, "public source sync count must be 9", errors)
    require(baseline_sync.get("raw_payload_extracted") is False, "raw payload must not be extracted", errors)
    require(baseline_sync.get("zip_internal_entry_names_committed") is False, "zip internal entry names must not be committed", errors)

    require(baseline_manifest == metadata_manifest, "taskpack and metadata source package manifests must match", errors)
    require(baseline_manifest.get("schema_version") == "kmfa.source_package_manifest.v014.v1", "baseline schema mismatch", errors)
    require(baseline_manifest.get("copied_public_source_count") == 9, "baseline public source count must be 9", errors)
    require(baseline_manifest.get("zip_internal_entry_names_committed") is False, "baseline must not commit zip internal entry names", errors)
    require(
        baseline_manifest.get("source_zip_sha256") == s01p1.get("source_package", {}).get("sha256"),
        "baseline source package hash must match S01-P1",
        errors,
    )
    require(
        baseline_manifest.get("html_human_flow_gate", {}).get("pass") == 54
        and baseline_manifest.get("html_human_flow_gate", {}).get("warn") == 0
        and baseline_manifest.get("html_human_flow_gate", {}).get("fail") == 0,
        "baseline HTML human-flow gate must be 54/0/0",
        errors,
    )

    p1_sources = {str(item.get("label")): item for item in s01p1.get("selected_public_sources", [])}
    manifest_sources = {str(item.get("label")): item for item in baseline_sync.get("selected_public_sources", [])}
    baseline_sources = {str(item.get("label")): item for item in baseline_manifest.get("selected_public_sources", [])}
    for label, target in REQUIRED_BASELINE_TARGETS.items():
        require(label in p1_sources, f"missing S01-P1 public source label: {label}", errors)
        require(label in manifest_sources, f"missing S01-P2 public source label: {label}", errors)
        require(label in baseline_sources, f"missing baseline public source label: {label}", errors)
        require(target.exists(), f"missing baseline file for {label}: {target}", errors)
        if target.exists() and label in p1_sources:
            require(sha256_file(target) == p1_sources[label].get("sha256"), f"baseline file hash mismatch for {label}", errors)
            require(target.stat().st_size == p1_sources[label].get("bytes"), f"baseline file byte size mismatch for {label}", errors)
        require(str(target) == manifest_sources.get(label, {}).get("target_path"), f"S01-P2 target path mismatch for {label}", errors)
        require(str(target) == baseline_sources.get(label, {}).get("target_path"), f"baseline target path mismatch for {label}", errors)

    if require_source_package_present:
        package_path = Path(str(s01p1.get("source_package", {}).get("path", "")))
        require(package_path.exists(), f"source package missing: {package_path}", errors)
        if package_path.exists():
            require(sha256_file(package_path) == s01p1.get("source_package", {}).get("sha256"), "source package sha256 mismatch", errors)
            public_hashes = {str(item.get("sha256")) for item in s01p1.get("selected_public_sources", [])}
            package_hashes = source_package_hashes(package_path)
            require(public_hashes.issubset(package_hashes), "source package does not contain all selected public source hashes", errors)

    gates = manifest.get("v14_gates", {})
    require(gates.get("raw_data_root") == "/Users/linzezhang/Downloads/KMFA_MetaData", "raw data root mismatch", errors)
    require(gates.get("raw_data_root_mode") == "read_only", "raw data mode mismatch", errors)
    require(gates.get("html_audit_pass") == 54, "HTML audit pass count must be 54", errors)
    require(gates.get("html_audit_warn") == 0, "HTML audit warn count must be 0", errors)
    require(gates.get("html_audit_fail") == 0, "HTML audit fail count must be 0", errors)
    require(
        gates.get("quality_over_time_rule") == "quality_gate_passed_can_finish_early_quality_gate_failed_blocks_delivery",
        "quality-over-time rule mismatch",
        errors,
    )

    raw_boundary = manifest.get("raw_data_boundary", {})
    for key, value in raw_boundary.items():
        require(value is False, f"raw_data_boundary.{key} must be false", errors)
    baseline_raw_boundary = baseline_manifest.get("raw_data_boundary", {})
    require(baseline_raw_boundary.get("raw_inbox_read_by_this_phase") is False, "baseline raw read must be false", errors)
    require(baseline_raw_boundary.get("raw_inbox_listed_by_this_phase") is False, "baseline raw listed must be false", errors)
    require(baseline_raw_boundary.get("raw_inbox_mutated_by_this_phase") is False, "baseline raw mutation must be false", errors)
    require(baseline_raw_boundary.get("raw_payload_extracted_from_delivery_zip") is False, "baseline raw extraction must be false", errors)

    release = manifest.get("release_state", {})
    for key in ("delivery_allowed", "formal_report_allowed", "business_decision_basis_allowed", "business_execution_allowed"):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_report_grade") == "D", "report grade must remain D", errors)
    require(release.get("release_permission") == "blocked", "release permission must remain blocked", errors)

    for evidence in REQUIRED_EVIDENCE_FILES:
        require(evidence.exists(), f"missing evidence file: {evidence}", errors)

    for path in repo_tree_files(BASELINE_ROOT) + repo_tree_files(EVIDENCE_ROOT):
        require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden raw/private extension committed: {path}", errors)

    for path in [
        S01P2_MANIFEST_PATH,
        TASKPACK_BASELINE_MANIFEST_PATH,
        METADATA_BASELINE_MANIFEST_PATH,
        Path("KMFA/taskpack/v1_4/PUBLIC_SAFE_BASELINE.md"),
        Path("KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/human/s01_p2_completion_record.md"),
        Path("KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/human/test_results.md"),
    ]:
        if path.exists():
            text = path.read_text(encoding="utf-8").lower()
            for forbidden in FORBIDDEN_MANIFEST_TEXT:
                require(forbidden.lower() not in text, f"forbidden manifest/evidence text {forbidden!r} in {path}", errors)

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=S01P2_MANIFEST_PATH)
    parser.add_argument("--require-source-package-present", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s01_p2_public_baseline_sync(
            args.manifest,
            require_source_package_present=args.require_source_package_present,
        )
    except ValidationError as exc:
        print("FAIL: KMFA v1.4 S01-P2 public-safe baseline sync validation failed")
        print(exc)
        return 1
    baseline = manifest["baseline_sync"]
    gates = manifest["v14_gates"]
    print(
        "PASS: KMFA v1.4 S01-P2 public-safe baseline sync validated "
        f"(task_id={manifest['task_id']}, public_sources={baseline['copied_public_source_count']}, "
        f"html_audit={gates['html_audit_pass']}/{gates['html_audit_warn']}/{gates['html_audit_fail']}, "
        f"github_upload={str(manifest['phase_scope']['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
