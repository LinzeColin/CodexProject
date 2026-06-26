from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from arxiv_daily_push.stage1_runtime import create_runtime_backup, restore_runtime_backup
from arxiv_daily_push.stage2_atomic_recovery import (
    S2PMT02_MANIFEST_FILENAME,
    build_restore_atomic_replacement_report,
    build_restore_path_safety_report,
    build_atomic_recovery_package,
    run_restore_drill,
    validate_atomic_recovery_report,
    validate_restore_atomic_replacement_report,
    validate_restore_path_safety_report,
    verify_atomic_recovery_manifest,
)
from arxiv_daily_push.storage import inspect_database, migrate_database


def _a001_probe(
    probe_id: str,
    restore: dict[str, object],
    target: Path,
    *,
    before_sha: str | None = None,
) -> dict[str, object]:
    after_sha = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
    return {
        "probe_id": probe_id,
        "observed_status": restore.get("status"),
        "blocking_reasons": restore.get("blocking_reasons") or [],
        "target_exists_after": target.exists(),
        "target_sha256_preserved": bool(before_sha and after_sha == before_sha),
        "production_side_effects_enabled": restore.get("production_side_effects_enabled"),
        "production_restore_executed": False,
        "real_smtp_sent": restore.get("real_smtp_sent"),
        "real_scheduler_installed": restore.get("real_scheduler_installed"),
        "real_release_uploaded": restore.get("real_release_uploaded"),
        "public_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
    }


def _stamp_database(path: Path, marker: str) -> str:
    migrate_database(path)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO development_iterations(iteration_id, task_id, status, evidence_ref, created_at) VALUES (?, ?, ?, ?, ?)",
            (f"iter-{marker}", f"task-{marker}", "pass", f"evidence-{marker}", "2026-07-02T06:00:00+10:00"),
        )
        conn.commit()
    finally:
        conn.close()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _temp_restore_files(target: Path) -> list[Path]:
    return sorted(target.parent.glob(f".{target.name}.*.tmp"))


def _a002_probe(
    probe_id: str,
    restore: dict[str, object],
    target: Path,
    *,
    backup_sha: str | None = None,
    before_sha: str | None = None,
) -> dict[str, object]:
    after_sha = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
    previous_backup_path = restore.get("previous_target_backup_path")
    previous_backup = Path(str(previous_backup_path)) if previous_backup_path else None
    previous_backup_sha = hashlib.sha256(previous_backup.read_bytes()).hexdigest() if previous_backup and previous_backup.exists() else None
    storage_report = inspect_database(target) if target.exists() else {"status": "missing"}
    return {
        "probe_id": probe_id,
        "observed_status": restore.get("status"),
        "blocking_reasons": restore.get("blocking_reasons") or [],
        "restored_database_ready": restore.get("restored_database_ready"),
        "target_exists_after": target.exists(),
        "target_sha256": after_sha,
        "target_sha256_matches_backup": bool(backup_sha and after_sha == backup_sha),
        "target_sha256_changed_from_before": bool(before_sha and after_sha and after_sha != before_sha),
        "target_sha256_preserved": bool(before_sha and after_sha == before_sha),
        "previous_target_backup_created": bool(previous_backup and previous_backup.exists()),
        "previous_target_backup_sha256_preserved": bool(before_sha and previous_backup_sha == before_sha),
        "storage_report_status": storage_report.get("status"),
        "temp_files_remaining": len(_temp_restore_files(target)),
        "production_side_effects_enabled": restore.get("production_side_effects_enabled"),
        "production_restore_executed": False,
        "real_smtp_sent": restore.get("real_smtp_sent"),
        "real_scheduler_installed": restore.get("real_scheduler_installed"),
        "real_release_uploaded": restore.get("real_release_uploaded"),
        "public_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
    }


class Stage2AtomicRecoveryTests(unittest.TestCase):
    def test_restore_path_safety_a001_uses_real_restore_probes_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside_db = root / "outside.sqlite3"
            migrate_database(outside_db)
            outside_sha = hashlib.sha256(outside_db.read_bytes()).hexdigest()
            probes: list[dict[str, object]] = []

            for probe_id, manifest_path_value in (
                ("relative_path_traversal", "../outside.sqlite3"),
                ("absolute_path_escape", str(outside_db)),
            ):
                backup_root = root / probe_id
                backup_root.mkdir()
                manifest_path = backup_root / "backup_manifest.json"
                manifest_path.write_text(
                    json.dumps(
                        {
                            "model_id": "adp-stage1-local-runtime-recovery-v1",
                            "files": [{"role": "database", "path": manifest_path_value, "sha256": outside_sha}],
                        }
                    ),
                    encoding="utf-8",
                )
                target = root / f"{probe_id}.sqlite3"
                restore = restore_runtime_backup(
                    manifest_path=manifest_path,
                    target_db_path=target,
                    generated_at="2026-07-02T06:10:00+10:00",
                    confirm_restore=True,
                )
                probes.append(_a001_probe(probe_id, restore, target))

            symlink_root = root / "symlink_escape"
            symlink_root.mkdir()
            symlink = symlink_root / "adp.sqlite3"
            symlink.symlink_to(outside_db)
            symlink_manifest = symlink_root / "backup_manifest.json"
            symlink_manifest.write_text(
                json.dumps(
                    {
                        "model_id": "adp-stage1-local-runtime-recovery-v1",
                        "files": [{"role": "database", "path": "adp.sqlite3", "sha256": outside_sha}],
                    }
                ),
                encoding="utf-8",
            )
            symlink_target = root / "symlink-restored.sqlite3"
            symlink_restore = restore_runtime_backup(
                manifest_path=symlink_manifest,
                target_db_path=symlink_target,
                generated_at="2026-07-02T06:11:00+10:00",
                confirm_restore=True,
            )
            probes.append(_a001_probe("symlink_escape", symlink_restore, symlink_target))

            preserve_root = root / "target_preserved_on_block"
            preserve_root.mkdir()
            target = root / "existing.sqlite3"
            migrate_database(target)
            before_sha = hashlib.sha256(target.read_bytes()).hexdigest()
            invalid_backup = preserve_root / "adp.sqlite3"
            invalid_backup.write_text("not a sqlite database", encoding="utf-8")
            preserve_manifest = preserve_root / "backup_manifest.json"
            preserve_manifest.write_text(
                json.dumps(
                    {
                        "model_id": "adp-stage1-local-runtime-recovery-v1",
                        "files": [
                            {
                                "role": "database",
                                "path": "adp.sqlite3",
                                "sha256": hashlib.sha256(invalid_backup.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            preserve_restore = restore_runtime_backup(
                manifest_path=preserve_manifest,
                target_db_path=target,
                generated_at="2026-07-02T06:12:00+10:00",
                confirm_restore=True,
                allow_overwrite=True,
            )
            probes.append(_a001_probe("target_preserved_on_block", preserve_restore, target, before_sha=before_sha))

            report = build_restore_path_safety_report(
                generated_at="2026-07-02T06:13:00+10:00",
                probes=probes,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["finding_id"], "A-001")
            self.assertEqual(report["task_id"], "S2PMT02-RESTORE-PATH-SAFETY-A001")
            self.assertEqual(report["probe_count"], 4)
            for gate, value in report["gates"].items():
                self.assertTrue(value, gate)
            self.assertFalse(report["production_restore_executed"])
            self.assertFalse(report["p0_closure_claimed"])
            self.assertFalse(report["stage2_integrated_production_accepted"])
            self.assertFalse(validate_restore_path_safety_report(report))

            tampered = {**report, "production_restore_executed": True}
            self.assertIn(
                "production_restore_executed must be false for A-001 restore path safety evidence",
                validate_restore_path_safety_report(tampered),
            )

    def test_restore_atomic_replacement_a002_uses_real_restore_probes_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "source.sqlite3"
            backup_sha = _stamp_database(source_db, "source")
            backup = create_runtime_backup(
                db_path=source_db,
                backup_dir=root / "backups",
                generated_at="2026-07-02T06:20:00+10:00",
            )
            self.assertEqual(backup["status"], "pass")
            backup_sha = backup["files"][0]["sha256"]
            probes: list[dict[str, object]] = []

            new_target = root / "new-target.sqlite3"
            new_restore = restore_runtime_backup(
                manifest_path=backup["backup_manifest_path"],
                target_db_path=new_target,
                generated_at="2026-07-02T06:21:00+10:00",
                confirm_restore=True,
            )
            probes.append(_a002_probe("valid_restore_new_target", new_restore, new_target, backup_sha=backup_sha))

            overwrite_target = root / "overwrite.sqlite3"
            before_sha = _stamp_database(overwrite_target, "old")
            overwrite_restore = restore_runtime_backup(
                manifest_path=backup["backup_manifest_path"],
                target_db_path=overwrite_target,
                generated_at="2026-07-02T06:22:00+10:00",
                confirm_restore=True,
                allow_overwrite=True,
            )
            probes.append(
                _a002_probe(
                    "valid_overwrite_with_previous_backup",
                    overwrite_restore,
                    overwrite_target,
                    backup_sha=backup_sha,
                    before_sha=before_sha,
                )
            )

            invalid_root = root / "invalid"
            invalid_root.mkdir()
            invalid_target = root / "invalid-target.sqlite3"
            invalid_before_sha = _stamp_database(invalid_target, "keep")
            invalid_backup = invalid_root / "adp.sqlite3"
            invalid_backup.write_text("not a sqlite database", encoding="utf-8")
            invalid_manifest = invalid_root / "backup_manifest.json"
            invalid_manifest.write_text(
                json.dumps(
                    {
                        "model_id": "adp-stage1-local-runtime-recovery-v1",
                        "files": [
                            {
                                "role": "database",
                                "path": "adp.sqlite3",
                                "sha256": hashlib.sha256(invalid_backup.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            invalid_restore = restore_runtime_backup(
                manifest_path=invalid_manifest,
                target_db_path=invalid_target,
                generated_at="2026-07-02T06:23:00+10:00",
                confirm_restore=True,
                allow_overwrite=True,
            )
            probes.append(
                _a002_probe(
                    "invalid_overwrite_preserves_target",
                    invalid_restore,
                    invalid_target,
                    backup_sha=backup_sha,
                    before_sha=invalid_before_sha,
                )
            )

            report = build_restore_atomic_replacement_report(
                generated_at="2026-07-02T06:24:00+10:00",
                probes=probes,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["finding_id"], "A-002")
            self.assertEqual(report["task_id"], "S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002")
            self.assertEqual(report["probe_count"], 3)
            for gate, value in report["gates"].items():
                self.assertTrue(value, gate)
            self.assertFalse(report["production_restore_executed"])
            self.assertFalse(report["p0_closure_claimed"])
            self.assertFalse(report["stage2_integrated_production_accepted"])
            self.assertFalse(validate_restore_atomic_replacement_report(report))

            tampered = {**report, "p0_closure_claimed": True}
            self.assertIn(
                "p0_closure_claimed must be false for A-002 restore atomic replacement evidence",
                validate_restore_atomic_replacement_report(tampered),
            )

    def test_package_verify_and_restore_drill_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact_dir = Path(tmp) / "artifacts"

            package = build_atomic_recovery_package(
                artifact_dir=artifact_dir,
                generated_at="2026-07-02T06:00:00+10:00",
                artifacts={
                    "queue/state.json": {"queue_items": 2, "watermark": "wm-1"},
                    "ledger/content.json": {"entries": ["claim:1"]},
                },
            )

            self.assertEqual(package["status"], "pass")
            self.assertFalse(package["production_side_effects_enabled"])
            self.assertFalse(package["production_restore_executed"])
            self.assertTrue(package["staging_clean"])
            self.assertEqual(package["atomic_write_count"], 2)
            self.assertFalse(validate_atomic_recovery_report(package))
            self.assertTrue((artifact_dir / S2PMT02_MANIFEST_FILENAME).exists())

            verify = verify_atomic_recovery_manifest(
                manifest_path=package["manifest_path"],
                generated_at="2026-07-02T06:01:00+10:00",
            )
            self.assertEqual(verify["status"], "pass")
            self.assertFalse(validate_atomic_recovery_report(verify))

            restore = run_restore_drill(
                manifest_path=package["manifest_path"],
                restore_dir=Path(tmp) / "restore-drill",
                generated_at="2026-07-02T06:02:00+10:00",
                confirm_restore=True,
            )
            self.assertEqual(restore["status"], "pass")
            self.assertTrue(restore["restore_drill_passed"])
            self.assertFalse(restore["production_restore_executed"])
            self.assertFalse(validate_atomic_recovery_report(restore))
            self.assertEqual(json.loads((Path(tmp) / "restore-drill" / "queue" / "state.json").read_text()), {"queue_items": 2, "watermark": "wm-1"})

    def test_verify_blocks_tampered_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = build_atomic_recovery_package(
                artifact_dir=Path(tmp) / "artifacts",
                generated_at="2026-07-02T06:00:00+10:00",
                artifacts={"ledger/content.json": {"entries": ["claim:1"]}},
            )
            tampered = Path(tmp) / "artifacts" / "ledger" / "content.json"
            tampered.write_text('{"entries":["claim:2"]}\n', encoding="utf-8")

            verify = verify_atomic_recovery_manifest(
                manifest_path=package["manifest_path"],
                generated_at="2026-07-02T06:01:00+10:00",
            )

            self.assertEqual(verify["status"], "blocked")
            self.assertIn("manifest file hash mismatch: ledger/content.json", verify["blocking_reasons"])

    def test_package_blocks_enabled_production_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = build_atomic_recovery_package(
                artifact_dir=Path(tmp) / "artifacts",
                generated_at="2026-07-02T06:00:00+10:00",
                artifacts={"queue/state.json": {"queue_items": 2}},
                environment={"ADP_PRODUCTION_ENABLED": "true"},
            )

            self.assertEqual(package["status"], "blocked")
            self.assertIn("ADP_PRODUCTION_ENABLED must not be true during S2PMT02", package["blocking_reasons"])

    def test_verify_blocks_invalid_manifest_path_without_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / S2PMT02_MANIFEST_FILENAME
            manifest_path.write_text(
                json.dumps(
                    {
                        "model_id": "adp-s2pmt02-atomic-storage-recovery-v1",
                        "acceptance_id": "ACC-S2PMT02-ATOMIC-RECOVERY",
                        "files": [{"path": "../outside.json", "sha256": "bad"}],
                    }
                ),
                encoding="utf-8",
            )

            verify = verify_atomic_recovery_manifest(
                manifest_path=manifest_path,
                generated_at="2026-07-02T06:01:00+10:00",
            )

            self.assertEqual(verify["status"], "blocked")
            self.assertTrue(any(reason.startswith("manifest file path is invalid:") for reason in verify["blocking_reasons"]))

    def test_restore_drill_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = build_atomic_recovery_package(
                artifact_dir=Path(tmp) / "artifacts",
                generated_at="2026-07-02T06:00:00+10:00",
                artifacts={"queue/state.json": {"queue_items": 2}},
            )

            restore = run_restore_drill(
                manifest_path=package["manifest_path"],
                restore_dir=Path(tmp) / "restore-drill",
                generated_at="2026-07-02T06:02:00+10:00",
            )

            self.assertEqual(restore["status"], "blocked")
            self.assertIn("confirm_restore is required for restore drill", restore["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
