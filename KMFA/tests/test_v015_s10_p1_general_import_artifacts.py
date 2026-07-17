from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s10_p1_general_import as builder


class GeneralImportArtifactTests(unittest.TestCase):
    def test_s09_review_dependency_is_exact(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 21)
        self.assertTrue(dependency["s10_p1_entry_allowed"])
        self.assertFalse(dependency["s10_p1_started"])

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_format_and_protocol_artifacts_cover_acceptance(self) -> None:
        formats = json.loads(builder.FORMAT_MATRIX_PATH.read_text(encoding="utf-8"))
        preview = json.loads(builder.PREVIEW_PROTOCOL_PATH.read_text(encoding="utf-8"))
        resume = json.loads(builder.RESUME_PROTOCOL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(formats["format_category_count"], 6)
        self.assertEqual(formats["extension_count"], 8)
        self.assertEqual(len(formats["archive_rejections"]), 8)
        self.assertFalse(preview["processing_before_confirmation_allowed"])
        self.assertFalse(preview["preview_writes_raw"])
        self.assertTrue(preview["changed_source_requires_new_preview"])
        self.assertTrue(resume["exact_replay_reuses_record"])
        self.assertFalse(resume["partial_commit_visible"])

    def test_live_recovery_evidence_is_all_pass(self) -> None:
        result = json.loads(builder.RECOVERY_VERIFICATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(result["accounting"], {"total": 32, "passed": 32, "failed": 0})
        self.assertTrue(all(row["status"] == "PASS" for row in result["checks"]))
        self.assertEqual(result["raw_root_access_count"], 0)
        self.assertFalse(result["s10_p2_started"])
        self.assertFalse(result["github_upload_performed"])

    def test_manifest_and_task_matrix_move_together(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        tasks = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        accepted = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(tasks["phase_acceptance_status"], manifest["phase_acceptance_status"])
        self.assertEqual(tasks["task_accepted_count"], 3 if accepted else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 26 if accepted else 25)
        self.assertEqual(manifest["s10_p2_entry_allowed"], accepted)
        self.assertFalse(manifest["s10_p2_started"])
        self.assertFalse(manifest["s10_p3_entry_allowed"])

    def test_human_files_are_plain_chinese_and_scope_honest(self) -> None:
        implementation = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        preview = builder.PREVIEW_EXAMPLE_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        for token in ("先识别并检查文件", "明确确认", "重复导入", "没有访问原始财务资料"):
            self.assertIn(token, implementation)
        self.assertIn("等待确认", preview)
        self.assertIn("来源适配留到 S10-P2", risks)


if __name__ == "__main__":
    unittest.main()
