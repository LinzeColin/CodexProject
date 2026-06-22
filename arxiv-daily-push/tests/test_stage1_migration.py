from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.stage1_migration import (
    build_migration_package,
    validate_stage1_migration_report,
    verify_migration_package,
)
from arxiv_daily_push.storage import migrate_database, store_source_item


def sample_source_item() -> dict:
    return {
        "source_id": "arxiv:2401.00001",
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": "2401.00001",
        "title": "A Useful Migration Paper",
        "retrieved_at": "2026-07-01T05:00:00+10:00",
        "published_at": "2026-06-30T12:00:00Z",
        "updated_at": "2026-06-30T12:00:00Z",
        "canonical_url": "https://arxiv.org/abs/2401.00001",
        "metadata": {"authors": ["Example Author"], "categories": ["cs.AI"], "summary": "Migration evidence"},
        "content_refs": [{"ref_id": "abstract", "ref_type": "html", "uri": "https://arxiv.org/abs/2401.00001"}],
        "license": {"status": "unknown", "usage": "private_learning_link_only"},
    }


def prepare_project(root: Path) -> Path:
    (root / "config").mkdir(parents=True)
    (root / "VERSION").write_text("0.19.0\n", encoding="utf-8")
    (root / "config" / "owner_controls.yaml").write_text("project: arxiv-daily-push\n", encoding="utf-8")
    db_path = root / "adp.sqlite3"
    migrate_database(db_path)
    store_source_item(db_path, sample_source_item(), fetch_run_id="fetch-001")
    return db_path


class Stage1MigrationTests(unittest.TestCase):
    def test_export_and_verify_migration_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            db_path = prepare_project(root)
            package_dir = Path(tmp) / "package"

            report = build_migration_package(
                project_root=root,
                output_dir=package_dir,
                db_path=db_path,
                generated_at="2026-07-01T06:00:00+10:00",
                include_paths=[root / "config" / "owner_controls.yaml"],
                required_paths=["VERSION", "config/owner_controls.yaml"],
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(report["production_side_effects_enabled"])
            self.assertFalse(report["large_replay_executed"])
            self.assertTrue(Path(report["package_manifest_path"]).exists())
            self.assertFalse(validate_stage1_migration_report(report))
            self.assertTrue((package_dir / "backups").exists())
            self.assertNotIn("migration_manifest.json", {item["path"] for item in report["package_files"]})

            verify = verify_migration_package(
                manifest_path=report["package_manifest_path"],
                generated_at="2026-07-01T06:05:00+10:00",
            )
            self.assertEqual(verify["status"], "pass")
            self.assertFalse(validate_stage1_migration_report(verify))

    def test_verify_blocks_tampered_package_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            db_path = prepare_project(root)
            report = build_migration_package(
                project_root=root,
                output_dir=Path(tmp) / "package",
                db_path=db_path,
                generated_at="2026-07-01T06:00:00+10:00",
                required_paths=["VERSION", "config/owner_controls.yaml"],
            )

            restore_drill = Path(report["output_dir"]) / "RESTORE_DRILL.md"
            restore_drill.write_text(restore_drill.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
            verify = verify_migration_package(
                manifest_path=report["package_manifest_path"],
                generated_at="2026-07-01T06:05:00+10:00",
            )
            self.assertEqual(verify["status"], "blocked")
            self.assertIn("package file hash mismatch: RESTORE_DRILL.md", verify["blocking_reasons"])

    def test_export_blocks_enabled_production_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            db_path = prepare_project(root)
            report = build_migration_package(
                project_root=root,
                output_dir=Path(tmp) / "package",
                db_path=db_path,
                generated_at="2026-07-01T06:00:00+10:00",
                required_paths=["VERSION", "config/owner_controls.yaml"],
                environment={"ADP_PRODUCTION_ENABLED": "true"},
            )
            self.assertEqual(report["status"], "blocked")
            self.assertIn("ADP_PRODUCTION_ENABLED must not be true during S1-09", report["blocking_reasons"])

    def test_cli_migration_export_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            db_path = prepare_project(root)
            package_dir = Path(tmp) / "package"

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                export_result = main(
                    [
                        "migration",
                        "export",
                        "--project-root",
                        str(root),
                        "--db",
                        str(db_path),
                        "--output-dir",
                        str(package_dir),
                        "--generated-at",
                        "2026-07-01T06:00:00+10:00",
                        "--required-path",
                        "VERSION",
                        "--required-path",
                        "config/owner_controls.yaml",
                        "--json",
                    ]
                )
            self.assertEqual(export_result, 0)
            export = json.loads(buffer.getvalue())
            self.assertEqual(export["status"], "pass")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                verify_result = main(
                    [
                        "migration",
                        "verify",
                        "--manifest",
                        export["package_manifest_path"],
                        "--generated-at",
                        "2026-07-01T06:05:00+10:00",
                        "--json",
                    ]
                )
            self.assertEqual(verify_result, 0)
            self.assertEqual(json.loads(buffer.getvalue())["status"], "pass")


if __name__ == "__main__":
    unittest.main()
