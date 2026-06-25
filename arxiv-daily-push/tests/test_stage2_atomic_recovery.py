from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from arxiv_daily_push.stage2_atomic_recovery import (
    S2PMT02_MANIFEST_FILENAME,
    build_atomic_recovery_package,
    run_restore_drill,
    validate_atomic_recovery_report,
    verify_atomic_recovery_manifest,
)


class Stage2AtomicRecoveryTests(unittest.TestCase):
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
