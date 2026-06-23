"""Stage 1 migration package builder and verifier."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .stage1_runtime import (
    STAGE1_RUNTIME_REQUIRED_DISABLED_FLAGS,
    build_runtime_audit,
    create_runtime_backup,
    run_tick,
    run_watchdog,
    validate_stage1_runtime_report,
)
from .storage import inspect_database


STAGE1_MIGRATION_MODEL_ID = "adp-stage1-migration-package-v1"
STAGE1_MIGRATION_SCHEMA_VERSION = 1
STAGE1_MIGRATION_ACCEPTANCE_ID = "ADP-ACC-S1-09-MIGRATION-PACKAGE"
STAGE1_MIGRATION_MAX_PACKAGE_BYTES = 104857600
STAGE1_MIGRATION_REQUIRED_SECRET_NAMES = (
    "ADP_SMTP_HOST",
    "ADP_SMTP_PORT",
    "ADP_SMTP_USERNAME",
    "ADP_SMTP_PASSWORD",
    "ADP_SMTP_TO",
)
STAGE1_MIGRATION_REQUIRED_RELATIVE_PATHS = (
    "arxiv-daily-push/VERSION",
    "arxiv-daily-push/pyproject.toml",
    "arxiv-daily-push/config/owner_controls.yaml",
    "arxiv-daily-push/docs/pursuing_goal/BASELINE_LOCK.md",
    "arxiv-daily-push/src/arxiv_daily_push/storage.py",
    "arxiv-daily-push/src/arxiv_daily_push/stage1_runtime.py",
    "arxiv-daily-push/src/arxiv_daily_push/local_runner.py",
    "arxiv-daily-push/src/arxiv_daily_push/stage1_b1_report.py",
    "arxiv-daily-push/src/arxiv_daily_push/stage1_queue.py",
    "arxiv-daily-push/docs/runbooks/LOCAL_CODEX_RUNNER_RUNBOOK.md",
    "arxiv-daily-push/tests/test_storage.py",
    "arxiv-daily-push/tests/test_stage1_runtime.py",
    "arxiv-daily-push/tests/test_local_runner.py",
    "arxiv-daily-push/tests/test_stage1_b1_report.py",
    "arxiv-daily-push/tests/test_stage1_queue.py",
)
STAGE1_MIGRATION_PACKAGE_FILES = (
    "migration_manifest.json",
    "LOW_RESOURCE_SMOKE.json",
    "NEW_MACHINE_BOOTSTRAP_CHECKLIST.md",
    "SECRET_NAMES_CHECKLIST.md",
    "LOCAL_RUNNER_RUNBOOK.md",
    "RESTORE_DRILL.md",
)
_SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)\b(password|token|secret)\s*=\s*[^<\s][^\n]{3,}"),
)


def build_migration_package(
    *,
    project_root: str | Path,
    output_dir: str | Path,
    db_path: str | Path,
    generated_at: str,
    include_paths: list[str | Path] | None = None,
    required_paths: list[str] | None = None,
    write: bool = True,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a low-resource Stage 1 migration package and smoke report."""

    root = Path(project_root)
    out = Path(output_dir)
    db = Path(db_path)
    env = dict(os.environ if environment is None else environment)
    required = tuple(required_paths or STAGE1_MIGRATION_REQUIRED_RELATIVE_PATHS)
    includes = [Path(path) for path in include_paths or []]
    blocking_reasons: list[str] = []

    for key in STAGE1_RUNTIME_REQUIRED_DISABLED_FLAGS:
        if _truthy(env.get(key)):
            blocking_reasons.append(f"{key} must not be true during S1-09")

    required_inventory = _required_inventory(root, required)
    missing_required = [item["path"] for item in required_inventory if not item["exists"]]
    if missing_required:
        blocking_reasons.append("required migration source files are missing")

    storage_report = inspect_database(db)
    if storage_report.get("status") != "pass":
        blocking_reasons.append("Stage 1 SQLite database inspection did not pass")

    projected_input_bytes = _sum_existing_file_sizes([root / item["path"] for item in required_inventory if item["exists"]], includes, [db])
    if projected_input_bytes > STAGE1_MIGRATION_MAX_PACKAGE_BYTES:
        blocking_reasons.append(
            f"migration package inputs are {projected_input_bytes} bytes, above {STAGE1_MIGRATION_MAX_PACKAGE_BYTES}"
        )

    state_dir = out / "runtime_state"
    if write:
        state_dir.mkdir(parents=True, exist_ok=True)
    runtime_audit = build_runtime_audit(state_dir=state_dir, db_path=db, generated_at=generated_at, environment=env)
    tick = run_tick(state_dir=state_dir, generated_at=generated_at, write=write)
    watchdog = run_watchdog(state_dir=state_dir, generated_at=generated_at)
    runtime_reports = [runtime_audit, tick, watchdog]
    for report in runtime_reports:
        errors = validate_stage1_runtime_report(report)
        if errors or report.get("status") != "pass":
            blocking_reasons.append(f"runtime {report.get('action')} did not pass")

    backup = None
    if storage_report.get("status") == "pass" and not any(_truthy(env.get(key)) for key in STAGE1_RUNTIME_REQUIRED_DISABLED_FLAGS):
        backup = create_runtime_backup(
            db_path=db,
            backup_dir=out / "backups",
            generated_at=generated_at,
            include_paths=includes,
        )
        errors = validate_stage1_runtime_report(backup)
        if errors or backup.get("status") != "pass":
            blocking_reasons.append("runtime backup did not pass")

    package_docs = _package_documents(generated_at=generated_at, required_inventory=required_inventory)
    package_files: list[dict[str, Any]] = []
    if write:
        out.mkdir(parents=True, exist_ok=True)
        _write_json(out / "LOW_RESOURCE_SMOKE.json", _smoke_report(runtime_reports, storage_report, backup))
        for filename, content in package_docs.items():
            (out / filename).write_text(content, encoding="utf-8")

        manifest_preview = _manifest_payload(
            out=out,
            generated_at=generated_at,
            required_inventory=required_inventory,
            storage_report=storage_report,
            runtime_reports=runtime_reports,
            backup=backup,
            blocking_reasons=blocking_reasons,
            package_files=[],
        )
        _write_json(out / "migration_manifest.json", manifest_preview)
        package_files = _package_file_inventory(
            out,
            tuple(filename for filename in STAGE1_MIGRATION_PACKAGE_FILES if filename != "migration_manifest.json"),
        )
        manifest = {**manifest_preview, "package_files": package_files}
        _write_json(out / "migration_manifest.json", manifest)

    secret_findings = _scan_output_secrets(out, STAGE1_MIGRATION_PACKAGE_FILES) if write else []
    if secret_findings:
        blocking_reasons.append("migration package contains possible secret values")

    report = {
        "model_id": STAGE1_MIGRATION_MODEL_ID,
        "schema_version": STAGE1_MIGRATION_SCHEMA_VERSION,
        "acceptance_id": STAGE1_MIGRATION_ACCEPTANCE_ID,
        "action": "migration_export",
        "status": "blocked" if blocking_reasons else "pass",
        "generated_at": generated_at,
        "project_root": str(root),
        "output_dir": str(out),
        "db_path": str(db),
        "write_enabled": write,
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_schedule_enabled": False,
        "video_generated": False,
        "large_replay_executed": False,
        "required_secret_names": list(STAGE1_MIGRATION_REQUIRED_SECRET_NAMES),
        "required_inventory": required_inventory,
        "missing_required_paths": missing_required,
        "storage_report": storage_report,
        "runtime_reports": runtime_reports,
        "backup_report": backup,
        "package_manifest_path": str(out / "migration_manifest.json") if write else "",
        "package_files": package_files,
        "secret_scan_findings": secret_findings,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }
    return report


def verify_migration_package(*, manifest_path: str | Path, generated_at: str) -> dict[str, Any]:
    """Verify a Stage 1 migration package manifest without side effects."""

    manifest_file = Path(manifest_path)
    blocking_reasons: list[str] = []
    manifest: dict[str, Any] = {}
    if not manifest_file.exists():
        blocking_reasons.append("migration manifest does not exist")
    else:
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            blocking_reasons.append("migration manifest is not valid JSON")

    if manifest:
        if manifest.get("model_id") != STAGE1_MIGRATION_MODEL_ID:
            blocking_reasons.append("migration manifest model_id is invalid")
        if manifest.get("acceptance_id") != STAGE1_MIGRATION_ACCEPTANCE_ID:
            blocking_reasons.append("migration manifest acceptance_id is invalid")
        if manifest.get("production_side_effects_enabled") is not False:
            blocking_reasons.append("migration manifest must not enable production side effects")
        for file_entry in manifest.get("package_files") or []:
            rel_path = str(file_entry.get("path") or "")
            expected_hash = str(file_entry.get("sha256") or "")
            target = manifest_file.parent / rel_path
            if not target.exists():
                blocking_reasons.append(f"package file missing: {rel_path}")
                continue
            if expected_hash and _sha256_file(target) != expected_hash:
                blocking_reasons.append(f"package file hash mismatch: {rel_path}")
        secret_findings = _scan_output_secrets(manifest_file.parent, [entry.get("path") for entry in manifest.get("package_files") or []])
        if secret_findings:
            blocking_reasons.append("migration package contains possible secret values")
    else:
        secret_findings = []

    return {
        "model_id": STAGE1_MIGRATION_MODEL_ID,
        "schema_version": STAGE1_MIGRATION_SCHEMA_VERSION,
        "acceptance_id": STAGE1_MIGRATION_ACCEPTANCE_ID,
        "action": "migration_verify",
        "status": "blocked" if blocking_reasons else "pass",
        "generated_at": generated_at,
        "manifest_path": str(manifest_file),
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_schedule_enabled": False,
        "video_generated": False,
        "large_replay_executed": False,
        "secret_scan_findings": secret_findings,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def validate_stage1_migration_report(report: dict[str, Any]) -> list[str]:
    """Return validation errors for migration package reports."""

    errors: list[str] = []
    if report.get("model_id") != STAGE1_MIGRATION_MODEL_ID:
        errors.append("migration report model_id is invalid")
    if report.get("schema_version") != STAGE1_MIGRATION_SCHEMA_VERSION:
        errors.append("migration report schema_version must be 1")
    if report.get("acceptance_id") != STAGE1_MIGRATION_ACCEPTANCE_ID:
        errors.append("migration report acceptance_id is invalid")
    for key in (
        "production_side_effects_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_schedule_enabled",
        "video_generated",
        "large_replay_executed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    if report.get("status") == "pass" and report.get("blocking_reasons"):
        errors.append("passing migration report must not contain blocking_reasons")
    if report.get("action") == "migration_export" and report.get("status") == "pass" and not report.get("package_manifest_path"):
        errors.append("passing migration export requires package_manifest_path")
    if report.get("action") == "migration_verify" and not report.get("manifest_path"):
        errors.append("migration verify requires manifest_path")
    return errors


def _manifest_payload(
    *,
    out: Path,
    generated_at: str,
    required_inventory: list[dict[str, Any]],
    storage_report: dict[str, Any],
    runtime_reports: list[dict[str, Any]],
    backup: dict[str, Any] | None,
    blocking_reasons: list[str],
    package_files: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "model_id": STAGE1_MIGRATION_MODEL_ID,
        "schema_version": STAGE1_MIGRATION_SCHEMA_VERSION,
        "acceptance_id": STAGE1_MIGRATION_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "blocked" if blocking_reasons else "pass",
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_schedule_enabled": False,
        "video_generated": False,
        "large_replay_executed": False,
        "max_package_bytes": STAGE1_MIGRATION_MAX_PACKAGE_BYTES,
        "required_secret_names": list(STAGE1_MIGRATION_REQUIRED_SECRET_NAMES),
        "required_inventory": required_inventory,
        "storage_status": storage_report.get("status"),
        "runtime_statuses": {str(item.get("action")): item.get("status") for item in runtime_reports},
        "backup_manifest_path": backup.get("backup_manifest_path") if backup else "",
        "package_files": package_files,
        "restore_entrypoint": str(out / "RESTORE_DRILL.md"),
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def _package_documents(*, generated_at: str, required_inventory: list[dict[str, Any]]) -> dict[str, str]:
    required_lines = "\n".join(f"- `{item['path']}`: {'OK' if item['exists'] else 'MISSING'}" for item in required_inventory)
    secret_lines = "\n".join(f"- `{name}`" for name in STAGE1_MIGRATION_REQUIRED_SECRET_NAMES)
    return {
        "NEW_MACHINE_BOOTSTRAP_CHECKLIST.md": (
            "# Stage 1 New Machine Bootstrap Checklist\n\n"
            f"- generated_at: `{generated_at}`\n"
            "- scope: arXiv Daily Push Stage 1 B1/arXiv only\n"
            "- production acceptance: not claimed\n\n"
            "## Required Checks\n\n"
            "- OS, Python, Git, SSL, network, browser, and power policy checked on the new machine.\n"
            "- Free SSD is at least 60 GB before heavy validation.\n"
            "- GitHub cloud production schedule remains disabled; daily production uses the local Codex runner.\n"
            "- Gmail SMTP credentials are configured as secret names only; values are never written here.\n"
            "- Restore drill uses the backup manifest and explicit `--confirm-restore`.\n\n"
            "## Required Source Files\n\n"
            f"{required_lines}\n"
        ),
        "SECRET_NAMES_CHECKLIST.md": (
            "# Secret Names Checklist\n\n"
            "This file lists required secret names only. Do not paste values into this repository or migration package.\n\n"
            f"{secret_lines}\n"
        ),
        "LOCAL_RUNNER_RUNBOOK.md": (
            "# Local Runner Runbook\n\n"
            "1. Keep GitHub scheduled production disabled; GitHub is for code, PR/CI, evidence backup, and status records.\n"
            "2. Store Gmail SMTP values only in the local environment or Keychain-backed shell setup.\n"
            "3. Run one smoke path with `adp local-runner daily --state-dir <state> --date <YYYY-MM-DD> --generated-at <ISO> --json`.\n"
            "4. Inspect `<state>/runs/<YYYYMMDD>/email_preview.txt`, `adp-local-runner-report.json`, and `<state>/candidate_queue.json`.\n"
            "5. Generate launchd templates with `adp local-runner launchd-package`; install only after owner approval.\n"
            "6. On 2026-06-30 migration day, copy the repository, migration package, and state directory to the new computer, then run preflight and smoke before enabling launchd.\n"
        ),
        "RESTORE_DRILL.md": (
            "# Restore Drill\n\n"
            "1. Copy the migration package to the new machine.\n"
            "2. Verify `migration_manifest.json` hashes with `adp migration verify`.\n"
            "3. Restore the SQLite backup to an explicit new path using `adp restore --confirm-restore`.\n"
            "4. Run `adp storage inspect` on the restored database.\n"
            "5. Run `adp runtime-audit`, `adp tick`, `adp watchdog`, and `adp local-runner preflight` with an explicit state directory.\n"
            "6. Keep GitHub cloud production schedule, Release upload, and video disabled; real SMTP requires explicit local env and owner approval.\n"
        ),
    }


def _smoke_report(
    runtime_reports: list[dict[str, Any]],
    storage_report: dict[str, Any],
    backup: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "model_id": STAGE1_MIGRATION_MODEL_ID,
        "storage_status": storage_report.get("status"),
        "runtime_statuses": {str(item.get("action")): item.get("status") for item in runtime_reports},
        "backup_status": backup.get("status") if backup else "not_run",
        "production_side_effects_enabled": False,
        "large_replay_executed": False,
    }


def _required_inventory(root: Path, required_paths: tuple[str, ...]) -> list[dict[str, Any]]:
    inventory = []
    for rel_path in required_paths:
        target = root / rel_path
        inventory.append(
            {
                "path": rel_path,
                "exists": target.exists(),
                "bytes": target.stat().st_size if target.exists() and target.is_file() else 0,
                "sha256": _sha256_file(target) if target.exists() and target.is_file() else "",
            }
        )
    return inventory


def _package_file_inventory(out: Path, filenames: tuple[str, ...]) -> list[dict[str, Any]]:
    inventory = []
    for filename in filenames:
        target = out / filename
        if not target.exists():
            continue
        inventory.append({"path": filename, "bytes": target.stat().st_size, "sha256": _sha256_file(target)})
    return inventory


def _scan_output_secrets(out: Path, filenames: tuple[str, ...] | list[Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for filename in filenames:
        if not filename:
            continue
        target = out / str(filename)
        if not target.exists() or not target.is_file():
            continue
        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in _SECRET_VALUE_PATTERNS:
            if pattern.search(content):
                findings.append({"path": str(filename), "pattern": pattern.pattern})
    return findings


def _sum_existing_file_sizes(paths: list[Path], includes: list[Path], extra: list[Path]) -> int:
    total = 0
    seen: set[Path] = set()
    for path in [*paths, *includes, *extra]:
        candidate = path.resolve() if path.exists() else path
        if candidate in seen or not path.exists() or not path.is_file():
            continue
        seen.add(candidate)
        total += path.stat().st_size
    return total


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
