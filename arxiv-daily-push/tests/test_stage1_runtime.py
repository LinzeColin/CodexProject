from __future__ import annotations

import io
import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.stage1_runtime import (
    build_runtime_audit,
    build_scheduler_plan,
    create_runtime_backup,
    restore_runtime_backup,
    run_tick,
    run_watchdog,
    validate_stage1_runtime_report,
)
from arxiv_daily_push.storage import inspect_database, migrate_database


class Stage1RuntimeTests(unittest.TestCase):
    def test_tick_writes_heartbeat_and_watchdog_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "state"
            tick = run_tick(state_dir=state_dir, generated_at="2026-07-01T05:00:00+10:00")

            self.assertEqual(tick["status"], "pass")
            self.assertFalse(tick["production_side_effects_enabled"])
            self.assertTrue((state_dir / "heartbeat.json").exists())
            self.assertTrue((state_dir / "checkpoint.json").exists())
            self.assertFalse(validate_stage1_runtime_report(tick))

            watchdog = run_watchdog(state_dir=state_dir, generated_at="2026-07-01T05:30:00+10:00")
            self.assertEqual(watchdog["status"], "pass")
            self.assertFalse(validate_stage1_runtime_report(watchdog))

    def test_watchdog_blocks_stale_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "state"
            state_dir.mkdir()
            (state_dir / "heartbeat.json").write_text(
                json.dumps(
                    {
                        "generated_at": "2026-07-01T01:00:00+10:00",
                        "production_side_effects_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            watchdog = run_watchdog(state_dir=state_dir, generated_at="2026-07-01T05:00:00+10:00")

            self.assertEqual(watchdog["status"], "blocked")
            self.assertIn("heartbeat is stale", watchdog["blocking_reasons"])
            self.assertFalse(validate_stage1_runtime_report(watchdog))

    def test_runtime_audit_blocks_enabled_production_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "state"
            state_dir.mkdir()
            audit = build_runtime_audit(
                state_dir=state_dir,
                generated_at="2026-07-01T05:00:00+10:00",
                environment={"ADP_PRODUCTION_ENABLED": "true"},
            )

            self.assertEqual(audit["status"], "blocked")
            self.assertIn("ADP_PRODUCTION_ENABLED must not be true during S1-08", audit["blocking_reasons"])
            self.assertFalse(validate_stage1_runtime_report(audit))

    def test_backup_and_restore_round_trip_sqlite_database(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "adp.sqlite3"
            support = root / "owner_controls.yaml"
            support.write_text("project: arXiv Daily Push\n", encoding="utf-8")
            migrate_database(db_path)

            backup = create_runtime_backup(
                db_path=db_path,
                backup_dir=root / "backups",
                generated_at="2026-07-01T05:00:00+10:00",
                include_paths=[support],
            )

            self.assertEqual(backup["status"], "pass")
            self.assertTrue(Path(backup["backup_manifest_path"]).exists())
            self.assertEqual(backup["files"][0]["role"], "database")
            self.assertFalse(validate_stage1_runtime_report(backup))

            restored_db = root / "restored" / "adp.sqlite3"
            restore = restore_runtime_backup(
                manifest_path=backup["backup_manifest_path"],
                target_db_path=restored_db,
                generated_at="2026-07-01T05:05:00+10:00",
                confirm_restore=True,
            )

            self.assertEqual(restore["status"], "pass")
            self.assertTrue(restore["restored_database_ready"])
            self.assertEqual(inspect_database(restored_db)["status"], "pass")
            self.assertFalse(validate_stage1_runtime_report(restore))

    def test_restore_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "adp.sqlite3"
            migrate_database(db_path)
            backup = create_runtime_backup(
                db_path=db_path,
                backup_dir=root / "backups",
                generated_at="2026-07-01T05:00:00+10:00",
            )

            restore = restore_runtime_backup(
                manifest_path=backup["backup_manifest_path"],
                target_db_path=root / "restore.sqlite3",
                generated_at="2026-07-01T05:05:00+10:00",
            )

            self.assertEqual(restore["status"], "blocked")
            self.assertIn("confirm_restore is required", restore["blocking_reasons"])

    def test_restore_rejects_manifest_paths_outside_backup_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            backup_root = root / "backup"
            backup_root.mkdir()
            outside_db = root / "outside.sqlite3"
            migrate_database(outside_db)
            outside_sha = hashlib.sha256(outside_db.read_bytes()).hexdigest()

            for manifest_path_value in ("../outside.sqlite3", str(outside_db)):
                manifest = {
                    "model_id": "adp-stage1-local-runtime-recovery-v1",
                    "files": [{"role": "database", "path": manifest_path_value, "sha256": outside_sha}],
                }
                manifest_path = backup_root / "backup_manifest.json"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                target = root / f"restored-{len(manifest_path_value)}.sqlite3"

                restore = restore_runtime_backup(
                    manifest_path=manifest_path,
                    target_db_path=target,
                    generated_at="2026-07-01T05:05:00+10:00",
                    confirm_restore=True,
                )

                self.assertEqual(restore["status"], "blocked")
                self.assertIn("backup database path traversal is not allowed", restore["blocking_reasons"])
                self.assertFalse(target.exists())

    def test_restore_rejects_symlink_escape_from_backup_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            backup_root = root / "backup"
            backup_root.mkdir()
            outside_db = root / "outside.sqlite3"
            migrate_database(outside_db)
            backup_link = backup_root / "adp.sqlite3"
            backup_link.symlink_to(outside_db)
            manifest = {
                "model_id": "adp-stage1-local-runtime-recovery-v1",
                "files": [
                    {
                        "role": "database",
                        "path": "adp.sqlite3",
                        "sha256": hashlib.sha256(outside_db.read_bytes()).hexdigest(),
                    }
                ],
            }
            manifest_path = backup_root / "backup_manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            target = root / "restored.sqlite3"

            restore = restore_runtime_backup(
                manifest_path=manifest_path,
                target_db_path=target,
                generated_at="2026-07-01T05:05:00+10:00",
                confirm_restore=True,
            )

            self.assertEqual(restore["status"], "blocked")
            self.assertIn("backup database path escapes backup root", restore["blocking_reasons"])
            self.assertFalse(target.exists())

    def test_restore_validation_failure_preserves_existing_target_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "adp.sqlite3"
            migrate_database(target)
            original_bytes = target.read_bytes()
            backup_root = root / "backup"
            backup_root.mkdir()
            invalid_backup = backup_root / "adp.sqlite3"
            invalid_backup.write_text("not a sqlite database", encoding="utf-8")
            manifest = {
                "model_id": "adp-stage1-local-runtime-recovery-v1",
                "files": [
                    {
                        "role": "database",
                        "path": "adp.sqlite3",
                        "sha256": hashlib.sha256(invalid_backup.read_bytes()).hexdigest(),
                    }
                ],
            }
            manifest_path = backup_root / "backup_manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            restore = restore_runtime_backup(
                manifest_path=manifest_path,
                target_db_path=target,
                generated_at="2026-07-01T05:05:00+10:00",
                confirm_restore=True,
                allow_overwrite=True,
            )

            self.assertEqual(restore["status"], "blocked")
            self.assertEqual(target.read_bytes(), original_bytes)
            self.assertEqual(inspect_database(target)["status"], "pass")

    def test_scheduler_install_and_uninstall_are_template_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = build_scheduler_plan(
                action="scheduler_install",
                platform="macos",
                project_root=root / "repo",
                state_dir=root / "state",
                generated_at="2026-07-01T05:00:00+10:00",
                artifact_dir=root / "templates",
                write=True,
            )
            uninstall = build_scheduler_plan(
                action="scheduler_uninstall",
                platform="linux",
                project_root=root / "repo",
                state_dir=root / "state",
                generated_at="2026-07-01T05:00:00+10:00",
            )

            self.assertEqual(install["status"], "pass")
            self.assertTrue(install["dry_run_only"])
            self.assertFalse(install["applied"])
            self.assertTrue(install["written_paths"])
            self.assertEqual(uninstall["status"], "pass")
            self.assertTrue(uninstall["templates"])
            self.assertFalse(validate_stage1_runtime_report(install))
            self.assertFalse(validate_stage1_runtime_report(uninstall))

    def test_cli_tick_watchdog_backup_restore_and_scheduler(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            db_path = root / "adp.sqlite3"
            migrate_database(db_path)

            for argv in (
                ["tick", "--state-dir", str(state_dir), "--generated-at", "2026-07-01T05:00:00+10:00", "--json"],
                ["watchdog", "--state-dir", str(state_dir), "--generated-at", "2026-07-01T05:30:00+10:00", "--json"],
                ["runtime-audit", "--state-dir", str(state_dir), "--db", str(db_path), "--generated-at", "2026-07-01T05:31:00+10:00", "--json"],
                [
                    "scheduler",
                    "install",
                    "--platform",
                    "macos",
                    "--project-root",
                    str(root),
                    "--state-dir",
                    str(state_dir),
                    "--artifact-dir",
                    str(root / "templates"),
                    "--write",
                    "--generated-at",
                    "2026-07-01T05:32:00+10:00",
                    "--json",
                ],
            ):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    result = main(argv)
                self.assertEqual(result, 0)
                payload = json.loads(buffer.getvalue())
                self.assertEqual(payload["status"], "pass")
                self.assertFalse(payload["production_side_effects_enabled"])

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "backup",
                        "--db",
                        str(db_path),
                        "--backup-dir",
                        str(root / "backups"),
                        "--generated-at",
                        "2026-07-01T05:33:00+10:00",
                        "--json",
                    ]
                )
            self.assertEqual(result, 0)
            backup = json.loads(buffer.getvalue())

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "restore",
                        "--manifest",
                        backup["backup_manifest_path"],
                        "--target-db",
                        str(root / "restored.sqlite3"),
                        "--confirm-restore",
                        "--generated-at",
                        "2026-07-01T05:34:00+10:00",
                        "--json",
                    ]
                )
            self.assertEqual(result, 0)
            restore = json.loads(buffer.getvalue())
            self.assertTrue(restore["restored_database_ready"])


if __name__ == "__main__":
    unittest.main()
