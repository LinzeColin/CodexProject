from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s11_p1_quality_rules as builder


class QualityRuleArtifactTests(unittest.TestCase):
    def test_s10_review_dependency_is_exact(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 22)
        self.assertTrue(dependency["s11_p1_entry_allowed"])
        self.assertFalse(dependency["s11_p1_started"])

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_catalog_covers_all_rules_and_flow_bindings(self) -> None:
        catalog = json.loads(builder.RULE_CATALOG_PATH.read_text(encoding="utf-8"))
        coverage = json.loads(builder.COVERAGE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["dimensions"]), 8)
        self.assertEqual(len(catalog["rules"]), 16)
        self.assertEqual(coverage["dimension_count"], 8)
        self.assertEqual(coverage["rule_count"], 16)
        self.assertEqual(coverage["hard_gate_count"], 7)
        self.assertEqual(coverage["rule_weight_total_bps"], 10000)
        self.assertTrue(coverage["all_rules_bind_severity"])
        self.assertTrue(coverage["all_rules_bind_process_impact"])
        self.assertTrue(all(row["rule_count"] == 2 for row in coverage["dimensions"]))

    def test_status_and_score_models_are_human_first(self) -> None:
        statuses = json.loads(builder.STATUS_MODEL_PATH.read_text(encoding="utf-8"))
        policy = json.loads(builder.SCORE_POLICY_PATH.read_text(encoding="utf-8"))
        self.assertEqual([row["label_zh"] for row in statuses["statuses"]], ["已通过", "需确认", "不可使用", "已过期"])
        self.assertEqual(statuses["technical_detail_location"], "professional_detail")
        self.assertFalse(statuses["color_is_only_information"])
        self.assertTrue(statuses["text_label_required"])
        self.assertTrue(statuses["symbol_required"])
        self.assertEqual(policy["pass_min_bps"], 9500)
        self.assertEqual(policy["not_usable_below_bps"], 7500)
        self.assertEqual(policy["precedence"][0], "HARD_GATE_FAILURE")
        self.assertTrue(policy["hard_gate_overrides_score"])

    def test_synthetic_scenarios_prove_hard_gate_precedence(self) -> None:
        evidence = json.loads(builder.SCENARIO_RESULTS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(evidence["scenario_count"], 5)
        self.assertEqual(evidence["accounting"], {"total": 51, "passed": 51, "failed": 0})
        scenarios = evidence["scenarios"]
        critical = scenarios["high_score_critical_failure"]
        self.assertNotIn("technical_status", critical)
        self.assertEqual(critical["display"]["label_zh"], "不可使用")
        self.assertEqual(critical["professional_detail"]["score_bps"], 9375)
        self.assertEqual(critical["professional_detail"]["hard_gate_failure_count"], 1)
        self.assertFalse(critical["quality_flow_allowed"])
        self.assertEqual(scenarios["review_required"]["display"]["label_zh"], "需确认")
        self.assertEqual(scenarios["outdated_source"]["display"]["label_zh"], "已过期")

    def test_manifest_and_task_matrix_move_together(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        tasks = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        accepted = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(tasks["phase_acceptance_status"], manifest["phase_acceptance_status"])
        self.assertEqual(tasks["task_accepted_count"], 3 if accepted else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 29 if accepted else 28)
        self.assertEqual(manifest["s11_p2_entry_allowed"], accepted)
        self.assertFalse(manifest["s11_p2_started"])
        self.assertFalse(manifest["s11_p3_entry_allowed"])
        self.assertFalse(manifest["s11_stage_review_entry_allowed"])

    def test_human_files_are_plain_chinese_and_scope_honest(self) -> None:
        implementation = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.STATUS_GUIDE_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        for token in ("质量门卫", "不可使用", "关键门禁", "没有读取原始财务资料"):
            self.assertIn(token, implementation)
        for token in ("已通过", "需确认", "不可使用", "已过期", "不能只靠红黄绿"):
            self.assertIn(token, guide)
        self.assertIn("不负责 S11-P2", risks)
        self.assertIn("不触碰原始文件", risks)


if __name__ == "__main__":
    unittest.main()
