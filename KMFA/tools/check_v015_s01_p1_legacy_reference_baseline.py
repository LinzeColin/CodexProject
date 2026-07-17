#!/usr/bin/env python3
"""Validate the v1.5 S01-P1 observed legacy reference baseline.

A successful validator run proves that the negative audit evidence is
internally consistent.  It must never be interpreted as S01-P1 acceptance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import plistlib
import re
import stat
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE"
MANIFEST_PATH = ARTIFACT_ROOT / "machine/s01_p1_legacy_reference_baseline_manifest.json"
ACCEPTANCE_PATH = ARTIFACT_ROOT / "machine/acceptance_matrix_public_safe.json"
SHA256_INVENTORY_PATH = ARTIFACT_ROOT / "machine/legacy_reference_sha256_public_safe.csv"
METADATA_BASELINE_PATH = REPO_ROOT / "KMFA/metadata/baseline/v015_s01_p1_legacy_reference_baseline.json"
REQUIRED_HUMAN_FILES = (
    ARTIFACT_ROOT / "human/legacy_reference_baseline_report_zh.md",
    ARTIFACT_ROOT / "human/risk_register_zh.md",
    ARTIFACT_ROOT / "human/rollback_plan_zh.md",
    ARTIFACT_ROOT / "human/test_results_zh.md",
)
EXPECTED_BLOCKERS = {
    "REAL_APP_SOURCE_NOT_FOUND",
    "BUILD_SYSTEM_NOT_FOUND",
    "PRODUCT_BACKEND_API_NOT_FOUND",
    "PRODUCT_DATABASE_BINDING_NOT_FOUND",
    "APP_BUILDER_INSTALLER_NOT_TRACKED",
    "TASKPACK_NAMED_STACK_NOT_SPECIFIED",
}
EXPECTED_ACCEPTANCE_CHECKS = {
    "taskpack_fingerprint_locked": ("PASS", None),
    "repository_commit_reconstructable": ("PASS", None),
    "tracked_metadata_reconstructable": ("PASS", None),
    "legacy_static_target_reconstructable": ("PASS", None),
    "installed_app_fingerprint_comparable": ("PASS", None),
    "desktop_screenshot_indexed": ("PASS", None),
    "mobile_screenshot_indexed": ("PASS", None),
    "raw_root_unchanged": ("PASS", None),
    "public_repo_safety": ("PASS", None),
    "real_application_runtime_identified": ("FAIL", "RUNTIME_NOT_FOUND"),
    "real_runtime_routes_inventoried": ("FAIL", "STATIC_SAMPLE_ONLY"),
    "full_app_reconstructable_from_tracked_source": ("FAIL", "APP_BUILDER_INSTALLER_NOT_TRACKED"),
}
EXPECTED_RELEASE_STATE_KEYS = {
    "delivery_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "formal_report_allowed",
    "github_upload_allowed",
    "app_reinstall_allowed",
}
EXPECTED_ARTIFACT_REFS = {
    "acceptance_matrix": "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/machine/acceptance_matrix_public_safe.json",
    "sha256_inventory": "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/machine/legacy_reference_sha256_public_safe.csv",
    "baseline_report": "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/human/legacy_reference_baseline_report_zh.md",
    "risk_register": "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/human/risk_register_zh.md",
    "rollback_plan": "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/human/rollback_plan_zh.md",
    "test_results": "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/human/test_results_zh.md",
    "metadata_baseline": "KMFA/metadata/baseline/v015_s01_p1_legacy_reference_baseline.json",
}
EXPECTED_PHASE_GATE_KEYS = {
    "task_execution_complete_count",
    "task_acceptance_passed_count",
    "task_acceptance_not_passed_count",
    "s01p1_acceptance_passed",
    "stage_01_review_performed",
    "next_phase_started",
    "github_upload_performed",
    "app_reinstall_performed",
}
EXPECTED_PRIVATE_EVIDENCE_IDS = {
    "S01P1T01_RUNTIME_FACTS",
    "S01P1T02_RUNTIME_READBACK",
    "S01P1T02_DESKTOP_SCREENSHOT",
    "S01P1T02_MOBILE_SCREENSHOT",
    "V014_FRESH_APP_LAUNCH_RECEIPT",
}


class ValidationError(RuntimeError):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_content_hash(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + _sha256_bytes(encoded)


def _git_bytes(args: list[str]) -> bytes:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        raise ValidationError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def _git_text(args: list[str]) -> str:
    return _git_bytes(args).decode("utf-8").strip()


def _commit_is_visible(oid: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{oid}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _git_archive_fingerprint(commit: str, path: str) -> tuple[int, int, str]:
    archive = _git_bytes(["archive", "--format=tar", commit, path])
    items: list[tuple[str, bytes]] = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as handle:
        for member in handle.getmembers():
            if member.isfile():
                stream = handle.extractfile(member)
                if stream is None:
                    raise ValidationError(f"cannot read archived member: {member.name}")
                items.append((member.name, stream.read()))
    aggregate = hashlib.sha256()
    total = 0
    for name, data in sorted(items):
        total += len(data)
        aggregate.update(f"{name}\0{len(data)}\0{_sha256_bytes(data)}\n".encode())
    return len(items), total, aggregate.hexdigest()


def _tree_fingerprint(root: Path) -> tuple[int, int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    aggregate = hashlib.sha256()
    total = 0
    for path in files:
        data = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        total += len(data)
        aggregate.update(f"{relative}\0{len(data)}\0{_sha256_bytes(data)}\n".encode())
    return len(files), total, aggregate.hexdigest()


def _validate_public_safety(errors: list[str]) -> None:
    forbidden = (
        "source_header_text",
        "raw_value\"",
        "normalized_value\"",
        "contract_number\"",
        "invoice_number\"",
        "bank_account_number\"",
        "connector_password",
        "credential_payload",
        "-----BEGIN PRIVATE KEY-----",
    )
    paths = [path for path in ARTIFACT_ROOT.rglob("*") if path.is_file()] + [METADATA_BASELINE_PATH]
    for path in paths:
        _require(path.suffix.lower() in {".json", ".csv", ".md"}, f"unexpected public artifact type: {path}", errors)
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            _require(token.lower() not in text, f"forbidden public token in {path}: {token}", errors)


def validate_v015_s01_p1_legacy_reference_baseline(
    manifest_path: Path = MANIFEST_PATH,
    *,
    acceptance_path: Path = ACCEPTANCE_PATH,
    sha256_inventory_path: Path = SHA256_INVENTORY_PATH,
    metadata_baseline_path: Path = METADATA_BASELINE_PATH,
    require_private_evidence: bool = False,
    require_installed_app: bool = False,
    require_raw_root: bool = False,
    require_remote_main: bool = False,
    source_package: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _read_json(manifest_path)
    acceptance = _read_json(acceptance_path)
    metadata = _read_json(metadata_baseline_path)

    _require(manifest.get("schema_version") == "kmfa.v015.s01_p1_legacy_reference_baseline.v1", "manifest schema mismatch", errors)
    _require(manifest.get("project_id") == "KMFA", "project mismatch", errors)
    _require(manifest.get("target_release") == "v1.5", "target release mismatch", errors)
    _require(manifest.get("roadmap_phase_id") == "S01-P1", "phase mismatch", errors)
    _require(manifest.get("execution_status") == "EXECUTION_COMPLETE", "execution status mismatch", errors)
    _require(manifest.get("acceptance_status") == "NOT_PASSED", "S01-P1 must remain NOT_PASSED", errors)
    _require(manifest.get("decision") == "NO_GO", "decision must remain NO_GO", errors)
    _require(manifest.get("baseline_kind") == "legacy_static_reference_not_v15_runtime", "baseline kind mismatch", errors)
    _require(manifest.get("legacy_reference_frozen") is True, "legacy reference must be frozen", errors)
    _require(manifest.get("content_hash") == _canonical_content_hash(manifest), "manifest content hash mismatch", errors)

    outcomes = manifest.get("task_outcomes", [])
    _require(len(outcomes) == 3, "task outcome count must be 3", errors)
    findings = {item.get("task_id"): item.get("terminal_finding") for item in outcomes}
    _require(findings.get("S01P1T01") == "RUNTIME_NOT_FOUND", "T01 finding mismatch", errors)
    _require(findings.get("S01P1T02") == "STATIC_SAMPLE_ONLY", "T02 finding mismatch", errors)
    _require(findings.get("S01P1T03") == "PARTIAL_REPO_REBUILDABLE_APP_RESTORE_ONLY", "T03 finding mismatch", errors)
    _require(all(item.get("acceptance_status") == "NOT_PASSED" for item in outcomes), "no S01-P1 task may claim acceptance", errors)

    gate = manifest.get("phase_gate", {})
    _require(set(gate) == EXPECTED_PHASE_GATE_KEYS, "phase gate key set mismatch", errors)
    _require(gate.get("task_execution_complete_count") == 3, "execution count mismatch", errors)
    _require(gate.get("task_acceptance_passed_count") == 0, "accepted task count must be zero", errors)
    _require(gate.get("task_acceptance_not_passed_count") == 3, "not-passed task count must be three", errors)
    _require(gate.get("s01p1_acceptance_passed") is False, "phase acceptance must be false", errors)
    for key in ("stage_01_review_performed", "next_phase_started", "github_upload_performed", "app_reinstall_performed"):
        _require(gate.get(key) is False, f"phase boundary drift: {key}", errors)

    _require(acceptance.get("evidence_validation_status") == "PASS", "evidence validation status mismatch", errors)
    _require(acceptance.get("schema_version") == "kmfa.v015.s01_p1_acceptance_matrix.v1", "acceptance schema mismatch", errors)
    _require(acceptance.get("project_id") == "KMFA", "acceptance project mismatch", errors)
    _require(acceptance.get("target_release") == "v1.5", "acceptance target release mismatch", errors)
    _require(acceptance.get("stage_id") == "S01", "acceptance stage mismatch", errors)
    _require(acceptance.get("phase_id") == "P1", "acceptance phase mismatch", errors)
    _require(acceptance.get("acceptance_id") == manifest.get("acceptance_id"), "acceptance ID mismatch", errors)
    _require(acceptance.get("phase_acceptance_status") == "NOT_PASSED", "acceptance matrix must remain NOT_PASSED", errors)
    _require(acceptance.get("quality_gate_passed") is False, "quality gate must remain false", errors)
    checks = acceptance.get("checks", [])
    pass_count = sum(item.get("result") == "PASS" for item in checks)
    fail_count = sum(item.get("result") == "FAIL" for item in checks)
    _require(len(checks) == acceptance.get("check_count") == 12, "acceptance check count mismatch", errors)
    _require(pass_count == acceptance.get("check_pass_count") == 9, "acceptance pass count mismatch", errors)
    _require(fail_count == acceptance.get("check_fail_count") == 3, "acceptance fail count mismatch", errors)
    checks_by_id = {str(item.get("check_id")): item for item in checks}
    _require(len(checks_by_id) == len(checks), "duplicate acceptance check ID", errors)
    _require(set(checks_by_id) == set(EXPECTED_ACCEPTANCE_CHECKS), "acceptance check ID set mismatch", errors)
    for check_id, (expected_result, expected_finding) in EXPECTED_ACCEPTANCE_CHECKS.items():
        item = checks_by_id.get(check_id, {})
        _require(item.get("result") == expected_result, f"acceptance result mismatch: {check_id}", errors)
        _require(item.get("finding") == expected_finding, f"acceptance finding mismatch: {check_id}", errors)

    repo = manifest.get("repository_baseline", {})
    commit = str(repo.get("commit", ""))
    _git_bytes(["cat-file", "-e", f"{commit}^{{commit}}"])
    _require(repo.get("origin_main_commit") == commit, "origin/main baseline mismatch", errors)
    _require(repo.get("github_main_commit_observed") == commit, "GitHub main baseline mismatch", errors)

    target = manifest.get("legacy_static_target", {})
    target_path = str(target.get("path", ""))
    target_bytes = _git_bytes(["show", f"{commit}:{target_path}"])
    _require(_sha256_bytes(target_bytes) == target.get("sha256"), "legacy target SHA-256 mismatch", errors)
    blob_oid = _git_text(["rev-parse", f"{commit}:{target_path}"])
    _require(blob_oid == target.get("git_blob_oid"), "legacy target blob mismatch", errors)
    _require(target.get("real_application_runtime") is False, "legacy target must not claim real runtime", errors)

    tracked = manifest.get("tracked_metadata_snapshot", {})
    tree_oid = _git_text(["rev-parse", f"{commit}:{tracked.get('path')}"])
    _require(tree_oid == tracked.get("git_tree_oid"), "metadata Git tree mismatch", errors)
    file_count, byte_count, aggregate = _git_archive_fingerprint(commit, str(tracked.get("path")))
    _require(file_count == tracked.get("regular_file_count"), "metadata file count mismatch", errors)
    _require(byte_count == tracked.get("regular_file_bytes"), "metadata byte count mismatch", errors)
    _require(aggregate == tracked.get("aggregate_sha256"), "metadata aggregate mismatch", errors)

    governance = manifest.get("governance_snapshot", {})
    governance_tree = _git_text(["rev-parse", f"{commit}:{governance.get('path')}"])
    _require(governance_tree == governance.get("git_tree_oid"), "governance Git tree mismatch", errors)

    _require(set(manifest.get("blockers", [])) == EXPECTED_BLOCKERS, "blocker set mismatch", errors)
    reconstructability = manifest.get("reconstructability", {})
    _require(reconstructability.get("repository_snapshot") is True, "repo reconstructability mismatch", errors)
    _require(reconstructability.get("installed_app_from_tracked_source") is False, "App must not claim tracked rebuild", errors)
    _require(reconstructability.get("real_v15_application_runtime") is False, "v1.5 runtime must remain absent", errors)
    _require(reconstructability.get("full_s01p1_baseline_acceptance") is False, "full acceptance must remain false", errors)

    release_state = manifest.get("release_state", {})
    _require(set(release_state) == EXPECTED_RELEASE_STATE_KEYS, "release state key set mismatch", errors)
    for key, value in release_state.items():
        _require(value is False, f"release boundary must remain false: {key}", errors)
    public_safety = manifest.get("public_repo_safety", {})
    for key in (
        "raw_file_name_committed",
        "raw_file_hash_committed",
        "raw_business_value_committed",
        "source_document_committed",
        "credential_committed",
        "private_evidence_payload_committed",
    ):
        _require(public_safety.get(key) is False, f"public safety boundary drift: {key}", errors)
    _require(public_safety.get("private_evidence_hash_index_committed") is True, "private evidence index flag mismatch", errors)
    raw_snapshot = manifest.get("raw_root_snapshot", {})
    for key in ("file_names_captured", "file_contents_read", "file_hashes_computed", "mutation_performed"):
        _require(raw_snapshot.get(key) is False, f"raw boundary drift: {key}", errors)

    private_evidence_rows = manifest.get("private_evidence_index", [])
    private_evidence_ids = [str(item.get("evidence_id")) for item in private_evidence_rows]
    _require(len(private_evidence_ids) == len(set(private_evidence_ids)), "duplicate private evidence ID", errors)
    _require(set(private_evidence_ids) == EXPECTED_PRIVATE_EVIDENCE_IDS, "private evidence ID set mismatch", errors)

    artifact_refs = manifest.get("artifact_refs", {})
    _require(artifact_refs == EXPECTED_ARTIFACT_REFS, "artifact refs mismatch", errors)
    for label, reference in artifact_refs.items():
        path = REPO_ROOT / str(reference)
        _require(path.is_file(), f"missing artifact ref {label}: {path}", errors)

    _require(metadata.get("schema_version") == "kmfa.metadata.v015.s01_p1_legacy_reference_baseline.v1", "metadata schema mismatch", errors)
    _require(metadata.get("project_id") == "KMFA", "metadata project mismatch", errors)
    _require(metadata.get("target_release") == "v1.5", "metadata target release mismatch", errors)
    _require(metadata.get("baseline_id") == "V015-S01-P1-LEGACY-REFERENCE-BASELINE", "metadata baseline ID mismatch", errors)
    _require(metadata.get("baseline_manifest_ref") == MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(), "metadata manifest ref mismatch", errors)
    _require(metadata.get("baseline_kind") == manifest.get("baseline_kind"), "metadata baseline kind mismatch", errors)
    _require(metadata.get("repository_commit") == commit, "metadata baseline commit mismatch", errors)
    _require(metadata.get("tracked_metadata_tree_oid") == tracked.get("git_tree_oid"), "metadata baseline tree mismatch", errors)
    _require(metadata.get("tracked_metadata_aggregate_sha256") == tracked.get("aggregate_sha256"), "metadata aggregate hash mismatch", errors)
    _require(metadata.get("legacy_static_target_sha256") == target.get("sha256"), "metadata target hash mismatch", errors)
    app_reference = manifest.get("installed_app_reference", {})
    _require(metadata.get("installed_app_aggregate_sha256") == app_reference.get("aggregate_sha256"), "metadata App hash mismatch", errors)
    _require(metadata.get("repository_reconstructable") is True, "metadata repo reconstructability mismatch", errors)
    _require(metadata.get("installed_app_reconstructable_from_tracked_source") is False, "metadata App rebuild flag mismatch", errors)
    _require(metadata.get("real_v15_runtime_present") is False, "metadata runtime flag mismatch", errors)
    _require(metadata.get("s01p1_acceptance_passed") is False, "metadata must keep phase acceptance false", errors)
    _require(metadata.get("decision") == "NO_GO", "metadata decision mismatch", errors)

    with sha256_inventory_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == 9, "SHA-256 inventory row count mismatch", errors)
    _require(all(len(row.get("sha256", "")) == 64 for row in rows), "invalid SHA-256 inventory value", errors)
    rows_by_id = {str(row.get("artifact_id")): row for row in rows}
    _require(len(rows_by_id) == len(rows), "duplicate SHA-256 inventory ID", errors)
    private_evidence = {item.get("evidence_id"): item for item in private_evidence_rows}
    selected_app = app_reference.get("selected_file_sha256", {})
    expected_inventory = {
        "V15_TASKPACK": (manifest["source_package"]["name"], str(manifest["source_package"]["bytes"]), manifest["source_package"]["sha256"], "external_source_package"),
        "TRACKED_METADATA": (tracked["path"], str(tracked["regular_file_bytes"]), tracked["aggregate_sha256"], "reconstructable_from_git_commit"),
        "LEGACY_STATIC_TARGET": (target_path, "", target["sha256"], "reconstructable_from_git_commit"),
        "APP_INFO_PLIST": ("Contents/Info.plist", "", selected_app.get("Contents/Info.plist"), "restore_only"),
        "APP_EXECUTABLE": ("Contents/MacOS/KMFA", "", selected_app.get("Contents/MacOS/KMFA"), "restore_only"),
        "APP_RUNTIME_MANIFEST": ("Contents/Resources/KMFA_RUNTIME_MANIFEST.json", "", selected_app.get("Contents/Resources/KMFA_RUNTIME_MANIFEST.json"), "restore_only"),
        "APP_LAUNCHER": ("Contents/Resources/KMFA_launcher.zsh", "", selected_app.get("Contents/Resources/KMFA_launcher.zsh"), "restore_only"),
        "DESKTOP_SCREENSHOT": ("S01P1T02_DESKTOP_SCREENSHOT", str(private_evidence["S01P1T02_DESKTOP_SCREENSHOT"]["bytes"]), private_evidence["S01P1T02_DESKTOP_SCREENSHOT"]["sha256"], "local_private_evidence"),
        "MOBILE_SCREENSHOT": ("S01P1T02_MOBILE_SCREENSHOT", str(private_evidence["S01P1T02_MOBILE_SCREENSHOT"]["bytes"]), private_evidence["S01P1T02_MOBILE_SCREENSHOT"]["sha256"], "local_private_evidence"),
    }
    _require(set(rows_by_id) == set(expected_inventory), "SHA-256 inventory IDs mismatch", errors)
    for artifact_id, (expected_path, expected_bytes, expected_sha256, expected_reconstructability) in expected_inventory.items():
        row = rows_by_id.get(artifact_id, {})
        _require(row.get("path_or_id") == expected_path, f"inventory path mismatch: {artifact_id}", errors)
        _require(row.get("bytes") == expected_bytes, f"inventory byte count mismatch: {artifact_id}", errors)
        _require(row.get("sha256") == expected_sha256, f"inventory SHA-256 mismatch: {artifact_id}", errors)
        _require(row.get("reconstructability") == expected_reconstructability, f"inventory reconstructability mismatch: {artifact_id}", errors)
        _require(row.get("public_safe") == "true", f"inventory public-safe flag mismatch: {artifact_id}", errors)

    for path in REQUIRED_HUMAN_FILES:
        _require(path.is_file() and path.stat().st_size > 0, f"missing human evidence: {path}", errors)
    _validate_public_safety(errors)

    if source_package is not None:
        package = manifest.get("source_package", {})
        _require(source_package.is_file(), f"source package missing: {source_package}", errors)
        if source_package.is_file():
            _require(source_package.stat().st_size == package.get("bytes"), "source package byte size mismatch", errors)
            _require(_sha256_file(source_package) == package.get("sha256"), "source package hash mismatch", errors)

    if require_private_evidence:
        for item in private_evidence_rows:
            path = REPO_ROOT / str(item.get("path", ""))
            _require(path.is_file(), f"private evidence missing: {path}", errors)
            if path.is_file():
                _require(path.stat().st_size == item.get("bytes"), f"private evidence size mismatch: {path}", errors)
                _require(_sha256_file(path) == item.get("sha256"), f"private evidence hash mismatch: {path}", errors)

    if require_installed_app:
        app = manifest.get("installed_app_reference", {})
        app_root = Path(str(app.get("path", "")))
        _require(app_root.is_dir(), f"installed App missing: {app_root}", errors)
        if app_root.is_dir():
            info = plistlib.loads((app_root / "Contents/Info.plist").read_bytes())
            _require(info.get("CFBundleIdentifier") == app.get("bundle_identifier"), "App bundle id mismatch", errors)
            _require(info.get("CFBundleShortVersionString") == app.get("short_version"), "App short version mismatch", errors)
            _require(info.get("CFBundleVersion") == app.get("build_version"), "App build version mismatch", errors)
            app_count, app_bytes, app_hash = _tree_fingerprint(app_root)
            _require(app_count == app.get("regular_file_count"), "App file count mismatch", errors)
            _require(app_bytes == app.get("regular_file_bytes"), "App byte count mismatch", errors)
            _require(app_hash == app.get("aggregate_sha256"), "App aggregate hash mismatch", errors)
            for relative, expected in app.get("selected_file_sha256", {}).items():
                _require(_sha256_file(app_root / relative) == expected, f"App selected file hash mismatch: {relative}", errors)
            active_target = (app_root / "Contents/Resources/KMFA_ACTIVE_TARGET_HTML").read_text(encoding="utf-8").strip()
            _require(active_target == target_path, "App active target mismatch", errors)
            signature = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app_root)], capture_output=True)
            _require(signature.returncode == 0, "App code signature validation failed", errors)

    if require_raw_root:
        raw = raw_snapshot
        raw_root = Path(str(raw.get("path", "")))
        _require(raw_root.is_dir(), f"raw root missing: {raw_root}", errors)
        if raw_root.is_dir():
            value = raw_root.stat()
            _require(value.st_dev == raw.get("device"), "raw root device drift", errors)
            _require(value.st_ino == raw.get("inode"), "raw root inode drift", errors)
            _require(stat.filemode(value.st_mode) == raw.get("mode"), "raw root mode drift", errors)
            _require(value.st_size == raw.get("size"), "raw root size drift", errors)
            _require(int(value.st_mtime) == raw.get("mtime_epoch"), "raw root mtime drift", errors)
            children = list(raw_root.iterdir())
            _require(sum(path.is_file() for path in children) == raw.get("top_level_file_count"), "raw top-level file count drift", errors)
            _require(sum(path.is_dir() for path in children) == raw.get("top_level_directory_count"), "raw top-level directory count drift", errors)

    if require_remote_main:
        remote_line = _git_text(["ls-remote", "origin", "refs/heads/main"])
        remote_commit = remote_line.split()[0] if remote_line else ""
        _require(bool(re.fullmatch(r"[0-9a-f]{40}", remote_commit)), "live remote main OID invalid", errors)
        _require(_commit_is_visible(remote_commit), "live remote main commit is not locally verifiable", errors)
        if _commit_is_visible(remote_commit):
            _require(_is_ancestor(commit, remote_commit), "historical v0.1.4 baseline is not an ancestor of live remote main", errors)

    if errors:
        raise ValidationError("\n".join(f"- {message}" for message in errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-installed-app", action="store_true")
    parser.add_argument("--require-raw-root", action="store_true")
    parser.add_argument("--require-remote-main", action="store_true")
    parser.add_argument("--source-package", type=Path)
    args = parser.parse_args()
    try:
        result = validate_v015_s01_p1_legacy_reference_baseline(
            require_private_evidence=args.require_private_evidence,
            require_installed_app=args.require_installed_app,
            require_raw_root=args.require_raw_root,
            require_remote_main=args.require_remote_main,
            source_package=args.source_package,
        )
    except (OSError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        print("FAIL: V015 S01P1 legacy reference baseline evidence invalid")
        print(exc)
        return 1
    print(
        "PASS: V015 S01P1 legacy reference evidence verified; "
        f"phase_acceptance={result['acceptance_status']}; decision={result['decision']}; "
        "accepted_tasks=0/3"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
