from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s20_p1_data_update as kernel


SELECTION = {
    "source_id": "SRC-local-upload-a1b2c3d4",
    "entity_id": "demo-north",
    "scope_id": "SEGMENT::PROJECT_COST",
    "period": "2026-07",
}
CSV = b"project,cost\nA,100\n"


class DataUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = kernel.DataUpdateStore(self.root / "runtime")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def preview(self) -> dict[str, object]:
        return self.store.create(SELECTION, "sample.csv", CSV)

    def test_options_cover_source_entity_account_segment_period_and_formats(self) -> None:
        value = kernel.options_contract()
        self.assertEqual(len(value["steps"]), 3)
        self.assertEqual({row["kind"] for row in value["scopes"]}, {"ACCOUNT", "SEGMENT"})
        self.assertIn(".xlsx", value["supported_extensions"])
        self.assertFalse(value["raw_write_allowed"])

    def test_upload_builds_human_preview_without_processing(self) -> None:
        value = self.preview()
        self.assertEqual(value["status"], "AWAITING_CONFIRMATION")
        self.assertEqual(value["current_step"], 2)
        self.assertEqual(value["preview"]["file_display_name"], "sample.csv")
        self.assertTrue(value["preview"]["user_confirmation_required"])
        self.assertFalse(value["preview"]["processing_allowed"])
        self.assertEqual(sum(row["origin"] == "AUTO_DETECTED" for row in value["preview"]["fields"]), 1)
        self.assertNotIn("private_source_relative_path", value)
        self.assertNotIn("file_hash", json.dumps(value))

    def test_exact_confirmation_commits_validates_and_only_lists_impact(self) -> None:
        value = self.preview()
        result = self.store.confirm(
            value["job_id"],
            preview_id=value["preview"]["preview_id"],
            confirm_token=value["preview"]["confirm_token"],
        )
        stages = {row["stage"]: row["status"] for row in result["progress"]}
        self.assertEqual(result["status"], "COMPLETED")
        self.assertTrue(result["result"]["validation_passed"])
        self.assertEqual(stages["IMPORT"], "COMPLETED")
        self.assertEqual(stages["VALIDATE"], "COMPLETED")
        self.assertEqual(stages["RECALCULATE"], "NOT_EXECUTED")
        self.assertEqual(stages["REPORT"], "NOT_EXECUTED")
        self.assertFalse(result["result"]["impact"]["recalculation_executed"])
        self.assertFalse(result["source_copy_present"])

    def test_wrong_confirmation_token_fails_closed(self) -> None:
        value = self.preview()
        with self.assertRaisesRegex(kernel.DataUpdateError, "PREVIEW_CONFIRMATION_MISMATCH"):
            self.store.confirm(value["job_id"], preview_id=value["preview"]["preview_id"], confirm_token="wrong")
        self.assertEqual(self.store.read(value["job_id"])["status"], "AWAITING_CONFIRMATION")

    def test_cancel_removes_isolated_upload_and_keeps_no_preview(self) -> None:
        value = self.preview()
        result = self.store.cancel(value["job_id"])
        self.assertEqual(result["status"], "CANCELLED")
        self.assertFalse(result["source_copy_present"])
        self.assertIsNone(result["preview"])
        self.assertFalse((self.store._job_dir(value["job_id"]) / "upload").exists())

    def test_broken_file_is_previewed_as_blocked_and_cannot_confirm(self) -> None:
        value = self.store.create(SELECTION, "broken.pdf", b"not-pdf")
        self.assertEqual(value["status"], "PREVIEW_BLOCKED")
        self.assertEqual(value["progress"][1]["status"], "FAILED")
        self.assertTrue(value["issues"][0]["blocks_processing"])
        with self.assertRaisesRegex(kernel.DataUpdateError, "JOB_NOT_CONFIRMABLE"):
            self.store.confirm(value["job_id"], preview_id="none", confirm_token="none")

    def test_interruption_is_invisible_and_refresh_resume_uses_checkpoint(self) -> None:
        value = self.preview()
        interrupted = self.store.confirm(
            value["job_id"],
            preview_id=value["preview"]["preview_id"],
            confirm_token=value["preview"]["confirm_token"],
            interrupt_at="AFTER_STAGE",
        )
        self.assertEqual(interrupted["status"], "INTERRUPTED")
        self.assertIsNone(interrupted["result"])
        restored = kernel.DataUpdateStore(self.root / "runtime").read(value["job_id"])
        self.assertEqual(restored, interrupted)
        resumed = kernel.DataUpdateStore(self.root / "runtime").resume(value["job_id"])
        self.assertEqual(resumed["status"], "COMPLETED")
        self.assertTrue(resumed["result"]["resumed_from_checkpoint"])

    def test_filename_traversal_and_raw_runtime_root_are_rejected(self) -> None:
        with self.assertRaisesRegex(kernel.DataUpdateError, "UPLOAD_FILENAME_INVALID"):
            self.store.create(SELECTION, "../escape.csv", CSV)
        with self.assertRaisesRegex(kernel.DataUpdateError, "RAW_ROOT_WRITE_REJECTED"):
            kernel.DataUpdateStore(Path.home() / "Downloads" / ("KMFA_" + "MetaData"))

    def test_public_verification_is_all_pass(self) -> None:
        value = kernel.public_verification()
        self.assertEqual((value["check_count"], value["pass_count"], value["fail_count"]), (59, 59, 0))

    def test_scope_stops_before_later_phases_and_external_actions(self) -> None:
        self.assertFalse(any(kernel.scope_boundary().values()))


if __name__ == "__main__":
    unittest.main()
