from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s10_p2_source_adapters as builder


class SourceAdapterArtifactTests(unittest.TestCase):
    def test_s10_p1_dependency_is_exact(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 19)
        self.assertEqual(dependency["final_evidence_commit"], builder.PHASE_BASE_COMMIT)
        self.assertTrue(dependency["s10_p2_entry_allowed"])
        self.assertFalse(dependency["s10_p2_started"])

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_registry_and_coverage_match_taskpack(self) -> None:
        registry = json.loads(builder.REGISTRY_PATH.read_text(encoding="utf-8"))
        coverage = json.loads(builder.ADAPTER_COVERAGE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(registry["source_system_count"], 6)
        self.assertEqual(registry["adapter_template_count"], 15)
        self.assertEqual(coverage["redcircle_template_count"], 4)
        self.assertEqual(coverage["kingdee_template_count"], 4)
        self.assertEqual(coverage["wps_template_count"], 4)
        self.assertEqual(coverage["auxiliary_template_count"], 3)
        self.assertFalse(coverage["automatic_login_allowed"])

    def test_mapping_and_hierarchy_fail_closed(self) -> None:
        mapping = json.loads(builder.MAPPING_POLICY_PATH.read_text(encoding="utf-8"))
        hierarchy = json.loads(builder.HIERARCHY_VERIFICATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(mapping["template_selection"], "EXPLICIT_ONLY")
        self.assertFalse(mapping["guess_field_meaning_allowed"])
        self.assertTrue(mapping["mapping_change_requires_new_version"])
        self.assertEqual(hierarchy["accounting"], {"total": 42, "passed": 42, "failed": 0})
        self.assertTrue(hierarchy["unknown_account_quarantined"])
        self.assertTrue(hierarchy["account_binding_mismatch_quarantined"])
        self.assertEqual(hierarchy["raw_root_access_count"], 0)

    def test_manifest_and_task_matrix_move_together(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        tasks = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        accepted = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(tasks["phase_acceptance_status"], manifest["phase_acceptance_status"])
        self.assertEqual(tasks["task_accepted_count"], 3 if accepted else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 27 if accepted else 26)
        self.assertEqual(manifest["s10_p3_entry_allowed"], accepted)
        self.assertFalse(manifest["s10_p3_started"])
        self.assertFalse(manifest["s10_stage_review_entry_allowed"])

    def test_human_files_are_plain_chinese_and_scope_honest(self) -> None:
        implementation = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        example = builder.ADAPTER_EXAMPLE_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        for token in ("字段翻译层", "不会根据相似词自行猜字段", "没有自动登录", "没有访问原始财务资料"):
            self.assertIn(token, implementation)
        self.assertIn("账户没有确认所属公司和银行", example)
        self.assertIn("自动登录和实时连接留到后续独立阶段", risks)


if __name__ == "__main__":
    unittest.main()
