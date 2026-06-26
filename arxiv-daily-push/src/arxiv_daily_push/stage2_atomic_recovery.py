"""S2PMT02 local atomic storage and recovery evidence helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any


S2PMT02_ATOMIC_RECOVERY_MODEL_ID = "adp-s2pmt02-atomic-storage-recovery-v1"
S2PMT02_ACCEPTANCE_ID = "ACC-S2PMT02-ATOMIC-RECOVERY"
S2PMT02_TASK_ID = "S2PMT02"
S2PMT02_SCHEMA_VERSION = 1
S2PMT02_MANIFEST_FILENAME = "s2pmt02_atomic_manifest.json"
S2PMT02_STAGING_DIRNAME = ".s2pmt02_staging"
S2PMT02_MAX_ARTIFACT_BYTES = 10485760
S2PMT02_REQUIRED_GATES = (
    "atomic_temp_write",
    "manifest_hash",
    "restore_drill",
    "tamper_detection",
    "staging_cleanup",
    "no_production_side_effect",
)
S2PMT02_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "production_side_effects_enabled",
    "production_restore_executed",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "db_migration_executed",
)
S2PMT02_FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)\b(password|token|secret)\s*=\s*[^<\s][^\n]{3,}"),
)
S2PMT02_REQUIRED_DISABLED_ENV_FLAGS = (
    "ADP_PRODUCTION_ENABLED",
    "ADP_SCHEDULED_RUN_ENABLED",
    "ADP_ALLOW_SMTP_SEND",
    "ADP_ALLOW_RELEASE_UPLOAD",
)
S2PMT02_RESTORE_PATH_SAFETY_MODEL_ID = "adp-s2pmt02-restore-path-safety-a001-v1"
S2PMT02_RESTORE_PATH_SAFETY_TASK_ID = "S2PMT02-RESTORE-PATH-SAFETY-A001"
S2PMT02_RESTORE_PATH_SAFETY_FINDING_ID = "A-001"
S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PROBES = (
    "relative_path_traversal",
    "absolute_path_escape",
    "symlink_escape",
    "target_preserved_on_block",
)
S2PMT02_RESTORE_PATH_SAFETY_EXPECTED_REASONS = {
    "relative_path_traversal": "backup database path traversal is not allowed",
    "absolute_path_escape": "backup database path traversal is not allowed",
    "symlink_escape": "backup database path escapes backup root",
    "target_preserved_on_block": "restored database",
}
S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_GATES = (
    "required_probe_coverage",
    "path_traversal_blocked",
    "absolute_path_blocked",
    "symlink_escape_blocked",
    "target_preserved_on_block",
    "no_production_side_effect",
)
S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "production_side_effects_enabled",
    "production_restore_executed",
    "real_smtp_sent",
    "real_scheduler_installed",
    "real_release_uploaded",
    "public_schema_changed",
    "queue_mutation_allowed",
    "db_migration_executed",
)


class Stage2AtomicRecoveryError(ValueError):
    """Raised when S2PMT02 inputs cannot be represented safely."""


def build_atomic_recovery_package(
    *,
    artifact_dir: str | Path,
    artifacts: Mapping[str, Any],
    generated_at: str,
    environment: Mapping[str, str] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Write a local artifact package through temp files and atomic replace."""

    root = Path(artifact_dir)
    env = dict(environment or {})
    blocking_reasons = _disabled_flag_reasons(env)
    if not artifacts:
        blocking_reasons.append("at least one artifact is required")

    normalized: list[tuple[str, bytes]] = []
    for relative_path, payload in artifacts.items():
        try:
            path = _safe_relative_path(str(relative_path))
            data = _payload_bytes(payload)
        except Stage2AtomicRecoveryError as exc:
            blocking_reasons.append(str(exc))
            continue
        if len(data) > S2PMT02_MAX_ARTIFACT_BYTES:
            blocking_reasons.append(f"artifact exceeds max bytes: {path}")
        if _contains_secret(data):
            blocking_reasons.append(f"artifact may contain secret value: {path}")
        normalized.append((path, data))

    package_id = _id("s2pmt02-package", generated_at)
    staging_dir = root / S2PMT02_STAGING_DIRNAME / package_id
    written_files: list[dict[str, Any]] = []
    atomic_write_count = 0
    if write and not blocking_reasons:
        root.mkdir(parents=True, exist_ok=True)
        staging_dir.mkdir(parents=True, exist_ok=False)
        try:
            for relative_path, data in normalized:
                staging_path = staging_dir / relative_path
                final_path = root / relative_path
                staging_path.parent.mkdir(parents=True, exist_ok=True)
                final_path.parent.mkdir(parents=True, exist_ok=True)
                _write_bytes_durable(staging_path, data)
                os.replace(staging_path, final_path)
                atomic_write_count += 1
                written_files.append(_file_entry(final_path, relative_path))

            manifest = _manifest_payload(
                package_id=package_id,
                generated_at=generated_at,
                root=root,
                files=written_files,
            )
            manifest_path = root / S2PMT02_MANIFEST_FILENAME
            _write_json_atomic(manifest_path, manifest, staging_dir=staging_dir)
            manifest_sha256 = _sha256_file(manifest_path)
        finally:
            shutil.rmtree(staging_dir, ignore_errors=True)
    else:
        manifest_path = root / S2PMT02_MANIFEST_FILENAME
        manifest_sha256 = ""

    staging_clean = not staging_dir.exists()
    if write and not staging_clean:
        blocking_reasons.append("staging directory was not cleaned")

    return _base_report(
        action="package",
        generated_at=generated_at,
        artifact_dir=root,
        status="blocked" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        extra={
            "package_id": package_id,
            "write_enabled": write,
            "manifest_path": str(manifest_path) if write and not blocking_reasons else "",
            "manifest_sha256": manifest_sha256,
            "files": written_files,
            "atomic_write_count": atomic_write_count,
            "staging_clean": staging_clean,
            "gates": _gate_states(
                atomic_write_count=atomic_write_count,
                manifest_sha256=manifest_sha256,
                restore_drill_passed=False,
                tamper_detection_ready=bool(written_files),
                staging_clean=staging_clean,
            ),
        },
    )


def verify_atomic_recovery_manifest(*, manifest_path: str | Path, generated_at: str) -> dict[str, Any]:
    """Verify an S2PMT02 manifest and referenced file hashes."""

    manifest_file = Path(manifest_path)
    blocking_reasons: list[str] = []
    manifest: dict[str, Any] = {}
    files: list[dict[str, Any]] = []
    if not manifest_file.exists():
        blocking_reasons.append("atomic manifest does not exist")
    else:
        try:
            manifest = _read_json(manifest_file)
        except (json.JSONDecodeError, Stage2AtomicRecoveryError) as exc:
            blocking_reasons.append(f"atomic manifest is invalid JSON object: {exc}")
        if manifest:
            if manifest.get("model_id") != S2PMT02_ATOMIC_RECOVERY_MODEL_ID:
                blocking_reasons.append("atomic manifest model_id is invalid")
            if manifest.get("acceptance_id") != S2PMT02_ACCEPTANCE_ID:
                blocking_reasons.append("atomic manifest acceptance_id is invalid")
            files = [item for item in manifest.get("files") or [] if isinstance(item, Mapping)]
            if not files:
                blocking_reasons.append("atomic manifest must contain files")
            for item in files:
                try:
                    relative_path = _safe_relative_path(str(item.get("path") or ""))
                except Stage2AtomicRecoveryError as exc:
                    blocking_reasons.append(f"manifest file path is invalid: {exc}")
                    continue
                target = manifest_file.parent / relative_path
                if not target.exists():
                    blocking_reasons.append(f"manifest file missing: {relative_path}")
                    continue
                if _sha256_file(target) != item.get("sha256"):
                    blocking_reasons.append(f"manifest file hash mismatch: {relative_path}")
                if _contains_secret(target.read_bytes()):
                    blocking_reasons.append(f"manifest file may contain secret value: {relative_path}")

    return _base_report(
        action="verify",
        generated_at=generated_at,
        artifact_dir=manifest_file.parent,
        status="blocked" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        extra={
            "manifest_path": str(manifest_file),
            "manifest_sha256": _sha256_file(manifest_file) if manifest_file.exists() else "",
            "package_id": str(manifest.get("package_id") or ""),
            "verified_file_count": len(files),
            "gates": _gate_states(
                atomic_write_count=len(files),
                manifest_sha256=_sha256_file(manifest_file) if manifest_file.exists() else "",
                restore_drill_passed=False,
                tamper_detection_ready=True,
                staging_clean=not (manifest_file.parent / S2PMT02_STAGING_DIRNAME).exists(),
            ),
        },
    )


def run_restore_drill(
    *,
    manifest_path: str | Path,
    restore_dir: str | Path,
    generated_at: str,
    confirm_restore: bool = False,
    allow_overwrite: bool = False,
) -> dict[str, Any]:
    """Copy manifest files to an explicit drill directory and verify hashes."""

    manifest_file = Path(manifest_path)
    target_root = Path(restore_dir)
    blocking_reasons: list[str] = []
    if not confirm_restore:
        blocking_reasons.append("confirm_restore is required for restore drill")
    verify = verify_atomic_recovery_manifest(manifest_path=manifest_file, generated_at=generated_at)
    if verify.get("status") != "pass":
        blocking_reasons.extend(verify.get("blocking_reasons") or ["manifest verification did not pass"])

    manifest = _read_json(manifest_file) if manifest_file.exists() else {}
    restored_files: list[dict[str, Any]] = []
    if confirm_restore and not blocking_reasons:
        for item in manifest.get("files") or []:
            if not isinstance(item, Mapping):
                continue
            relative_path = _safe_relative_path(str(item.get("path") or ""))
            source = manifest_file.parent / relative_path
            target = target_root / relative_path
            if target.exists() and not allow_overwrite:
                blocking_reasons.append(f"restore target already exists: {relative_path}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if _sha256_file(target) != item.get("sha256"):
                blocking_reasons.append(f"restored file hash mismatch: {relative_path}")
            restored_files.append(_file_entry(target, relative_path))

    restore_drill_passed = not blocking_reasons and len(restored_files) == len([item for item in manifest.get("files") or [] if isinstance(item, Mapping)])
    return _base_report(
        action="restore_drill",
        generated_at=generated_at,
        artifact_dir=manifest_file.parent,
        status="blocked" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        extra={
            "manifest_path": str(manifest_file),
            "restore_dir": str(target_root),
            "confirm_restore": confirm_restore,
            "allow_overwrite": allow_overwrite,
            "restored_files": restored_files,
            "restored_file_count": len(restored_files),
            "restore_drill_passed": restore_drill_passed,
            "production_restore_executed": False,
            "gates": _gate_states(
                atomic_write_count=int(verify.get("verified_file_count") or 0),
                manifest_sha256=str(verify.get("manifest_sha256") or ""),
                restore_drill_passed=restore_drill_passed,
                tamper_detection_ready=True,
                staging_clean=not (manifest_file.parent / S2PMT02_STAGING_DIRNAME).exists(),
            ),
        },
    )


def build_restore_path_safety_report(
    *,
    generated_at: str,
    probes: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build A-001 evidence from real Stage 1 restore safety probes."""

    probe_rows = [dict(row) for row in probes]
    by_id = {str(row.get("probe_id") or ""): row for row in probe_rows}
    blocking_reasons: list[str] = []

    missing = [probe_id for probe_id in S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PROBES if probe_id not in by_id]
    if missing:
        blocking_reasons.append("missing required restore path safety probes: " + ", ".join(missing))

    expected_reason_observed: dict[str, bool] = {}
    blocked_as_expected: dict[str, bool] = {}
    target_preserved = False
    no_side_effect = True
    for probe_id in S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PROBES:
        row = by_id.get(probe_id, {})
        reasons = [str(reason) for reason in row.get("blocking_reasons") or []]
        expected_reason = S2PMT02_RESTORE_PATH_SAFETY_EXPECTED_REASONS[probe_id]
        reason_observed = any(expected_reason in reason for reason in reasons)
        status_blocked = row.get("observed_status") == "blocked"
        expected_reason_observed[probe_id] = reason_observed
        blocked_as_expected[probe_id] = status_blocked and reason_observed
        if not blocked_as_expected[probe_id]:
            blocking_reasons.append(f"{probe_id} did not block with expected reason")
        if probe_id in {"relative_path_traversal", "absolute_path_escape", "symlink_escape"} and row.get("target_exists_after") is not False:
            blocking_reasons.append(f"{probe_id} must not create a restore target")
        if probe_id == "target_preserved_on_block":
            target_preserved = row.get("target_exists_after") is True and row.get("target_sha256_preserved") is True
            if not target_preserved:
                blocking_reasons.append("target_preserved_on_block must preserve the existing target bytes")
        for flag in S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PRODUCTION_FALSE_FLAGS:
            if row.get(flag, False) is not False:
                no_side_effect = False
                blocking_reasons.append(f"{probe_id}.{flag} must be false")

    gates = {
        "required_probe_coverage": not missing,
        "path_traversal_blocked": blocked_as_expected.get("relative_path_traversal", False),
        "absolute_path_blocked": blocked_as_expected.get("absolute_path_escape", False),
        "symlink_escape_blocked": blocked_as_expected.get("symlink_escape", False),
        "target_preserved_on_block": target_preserved,
        "no_production_side_effect": no_side_effect,
    }

    report: dict[str, Any] = {
        "model_id": S2PMT02_RESTORE_PATH_SAFETY_MODEL_ID,
        "schema_version": S2PMT02_SCHEMA_VERSION,
        "task_id": S2PMT02_RESTORE_PATH_SAFETY_TASK_ID,
        "parent_task_id": S2PMT02_TASK_ID,
        "acceptance_id": S2PMT02_ACCEPTANCE_ID,
        "finding_id": S2PMT02_RESTORE_PATH_SAFETY_FINDING_ID,
        "generated_at": generated_at,
        "status": "blocked" if blocking_reasons else "pass",
        "blocking_reasons": blocking_reasons,
        "required_probes": list(S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PROBES),
        "probe_count": len(probe_rows),
        "probes": probe_rows,
        "expected_reason_observed": expected_reason_observed,
        "gates": gates,
        "production_side_effects_enabled": False,
        "production_restore_executed": False,
        "real_smtp_sent": False,
        "real_scheduler_installed": False,
        "real_release_uploaded": False,
        "public_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "p0_closure_claimed": False,
        "p1_closure_claimed": False,
        "stage2_integrated_production_accepted": False,
    }
    report["restore_path_safety_hash"] = _restore_path_safety_hash(report)
    return report


def validate_restore_path_safety_report(report: Mapping[str, Any]) -> list[str]:
    """Validate A-001 restore path safety evidence."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT02_RESTORE_PATH_SAFETY_MODEL_ID:
        errors.append("A-001 report model_id is invalid")
    if report.get("schema_version") != S2PMT02_SCHEMA_VERSION:
        errors.append("A-001 report schema_version must be 1")
    if report.get("task_id") != S2PMT02_RESTORE_PATH_SAFETY_TASK_ID:
        errors.append("A-001 report task_id is invalid")
    if report.get("parent_task_id") != S2PMT02_TASK_ID:
        errors.append("A-001 report parent_task_id is invalid")
    if report.get("acceptance_id") != S2PMT02_ACCEPTANCE_ID:
        errors.append("A-001 report acceptance_id is invalid")
    if report.get("finding_id") != S2PMT02_RESTORE_PATH_SAFETY_FINDING_ID:
        errors.append("A-001 report finding_id must be A-001")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("A-001 report status must be pass or blocked")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked A-001 report requires blocking_reasons")
    if tuple(report.get("required_probes") or ()) != S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PROBES:
        errors.append("A-001 report required_probes mismatch")
    probes = report.get("probes")
    if not isinstance(probes, list):
        errors.append("A-001 report probes must be a list")
        probes = []
    probe_ids = {str(row.get("probe_id") or "") for row in probes if isinstance(row, Mapping)}
    missing = [probe_id for probe_id in S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PROBES if probe_id not in probe_ids]
    if missing:
        errors.append("A-001 report missing probes: " + ", ".join(missing))
    gates = report.get("gates")
    if not isinstance(gates, Mapping):
        errors.append("A-001 report gates must be a mapping")
        gates = {}
    for gate in S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_GATES:
        if gate not in gates:
            errors.append(f"A-001 report missing gate {gate}")
        if report.get("status") == "pass" and gates.get(gate) is not True:
            errors.append(f"passing A-001 report requires {gate}=true")
    for flag in (
        *S2PMT02_RESTORE_PATH_SAFETY_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "current_pointer_changed",
        "v7_1_baseline_changed",
        "v7_2_contract_files_changed",
        "p0_closure_claimed",
        "p1_closure_claimed",
        "stage2_integrated_production_accepted",
    ):
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false for A-001 restore path safety evidence")
    if report.get("restore_path_safety_hash") != _restore_path_safety_hash(report):
        errors.append("A-001 restore_path_safety_hash mismatch")
    return errors


def validate_atomic_recovery_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PMT02 package, verify, or restore-drill reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT02_ATOMIC_RECOVERY_MODEL_ID:
        errors.append("S2PMT02 report model_id is invalid")
    if report.get("schema_version") != S2PMT02_SCHEMA_VERSION:
        errors.append("S2PMT02 report schema_version must be 1")
    if report.get("task_id") != S2PMT02_TASK_ID:
        errors.append("S2PMT02 report task_id is invalid")
    if report.get("acceptance_id") != S2PMT02_ACCEPTANCE_ID:
        errors.append("S2PMT02 report acceptance_id is invalid")
    if report.get("action") not in {"package", "verify", "restore_drill"}:
        errors.append("S2PMT02 report action is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PMT02 report status must be pass or blocked")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PMT02 report requires blocking_reasons")
    for key in S2PMT02_REQUIRED_PRODUCTION_FALSE_FLAGS:
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    gates = report.get("gates") if isinstance(report.get("gates"), Mapping) else {}
    for gate in S2PMT02_REQUIRED_GATES:
        if gate not in gates:
            errors.append(f"gates.{gate} is required")
    if report.get("status") == "pass" and report.get("action") == "package":
        if not report.get("manifest_path"):
            errors.append("passing package report requires manifest_path")
        if int(report.get("atomic_write_count") or 0) <= 0:
            errors.append("passing package report requires atomic writes")
        if report.get("staging_clean") is not True:
            errors.append("passing package report requires staging_clean true")
    if report.get("status") == "pass" and report.get("action") == "restore_drill":
        if report.get("restore_drill_passed") is not True:
            errors.append("passing restore_drill report requires restore_drill_passed true")
    return errors


def _base_report(
    *,
    action: str,
    generated_at: str,
    artifact_dir: Path,
    status: str,
    blocking_reasons: list[str],
    extra: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "model_id": S2PMT02_ATOMIC_RECOVERY_MODEL_ID,
        "schema_version": S2PMT02_SCHEMA_VERSION,
        "task_id": S2PMT02_TASK_ID,
        "acceptance_id": S2PMT02_ACCEPTANCE_ID,
        "action": action,
        "generated_at": generated_at,
        "artifact_dir": str(artifact_dir),
        "status": status,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "production_side_effects_enabled": False,
        "production_restore_executed": False,
        "real_smtp_sent": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
        "local_side_effect_scope": "explicit_artifact_or_restore_drill_paths_only",
        **dict(extra),
    }


def _restore_path_safety_hash(report: Mapping[str, Any]) -> str:
    payload = {
        "finding_id": report.get("finding_id"),
        "gates": report.get("gates"),
        "probe_count": report.get("probe_count"),
        "probes": report.get("probes"),
        "required_probes": report.get("required_probes"),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _manifest_payload(*, package_id: str, generated_at: str, root: Path, files: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "model_id": S2PMT02_ATOMIC_RECOVERY_MODEL_ID,
        "schema_version": S2PMT02_SCHEMA_VERSION,
        "task_id": S2PMT02_TASK_ID,
        "acceptance_id": S2PMT02_ACCEPTANCE_ID,
        "package_id": package_id,
        "generated_at": generated_at,
        "artifact_dir": str(root),
        "files": files,
        "total_bytes": sum(int(item["size_bytes"]) for item in files),
        "production_side_effects_enabled": False,
        "production_restore_executed": False,
    }


def _gate_states(
    *,
    atomic_write_count: int,
    manifest_sha256: str,
    restore_drill_passed: bool,
    tamper_detection_ready: bool,
    staging_clean: bool,
) -> dict[str, bool]:
    return {
        "atomic_temp_write": atomic_write_count > 0,
        "manifest_hash": bool(manifest_sha256),
        "restore_drill": restore_drill_passed,
        "tamper_detection": tamper_detection_ready,
        "staging_cleanup": staging_clean,
        "no_production_side_effect": True,
    }


def _safe_relative_path(value: str) -> str:
    if not value or value.startswith("/") or "\\" in value:
        raise Stage2AtomicRecoveryError("artifact paths must be non-empty relative POSIX paths")
    path = Path(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise Stage2AtomicRecoveryError("artifact paths must not contain empty, current, or parent components")
    return path.as_posix()


def _payload_bytes(payload: Any) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if isinstance(payload, Mapping):
        return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    raise Stage2AtomicRecoveryError("artifact payload must be bytes, string, or mapping")


def _write_json_atomic(path: Path, payload: Mapping[str, Any], *, staging_dir: Path) -> None:
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temp_path = staging_dir / (path.name + ".tmp")
    _write_bytes_durable(temp_path, data)
    os.replace(temp_path, path)


def _write_bytes_durable(path: Path, data: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _file_entry(path: Path, relative_path: str) -> dict[str, Any]:
    return {
        "path": relative_path,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Stage2AtomicRecoveryError(f"{path} must contain a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contains_secret(data: bytes) -> bool:
    text = data.decode("utf-8", errors="ignore")
    return any(pattern.search(text) for pattern in S2PMT02_FORBIDDEN_SECRET_PATTERNS)


def _disabled_flag_reasons(environment: Mapping[str, str]) -> list[str]:
    reasons: list[str] = []
    for key in S2PMT02_REQUIRED_DISABLED_ENV_FLAGS:
        if str(environment.get(key, "")).strip().lower() == "true":
            reasons.append(f"{key} must not be true during S2PMT02")
    return reasons


def _id(prefix: str, generated_at: str) -> str:
    digest = hashlib.sha256(f"{prefix}|{generated_at}|{S2PMT02_ATOMIC_RECOVERY_MODEL_ID}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"
