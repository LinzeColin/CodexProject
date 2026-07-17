from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s08_p1_project_composite_identity as subject


class ProjectCompositeIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = subject.synthetic_acceptance_cases()

    def test_weights_match_taskpack_and_sum_to_one_hundred_percent(self) -> None:
        self.assertEqual(
            subject.COMPONENT_WEIGHTS_BPS,
            {
                "contract_number": 2000,
                "project_name": 1800,
                "counterparty": 1500,
                "company_entity": 1000,
                "time_evidence": 1200,
                "amount_evidence": 1200,
                "responsible_person": 600,
                "source_version": 700,
            },
        )
        self.assertEqual(sum(subject.COMPONENT_WEIGHTS_BPS.values()), 10000)

    def test_missing_contract_is_renormalized_and_does_not_block_valid_match(self) -> None:
        result = self.cases["match_cases"]["missing_contract_renormalized"]
        self.assertEqual(result["available_weight_bps"], 8000)
        self.assertEqual(result["matched_weight_bps"], 8000)
        self.assertEqual(result["renormalized_similarity_bps"], 10000)
        self.assertTrue(result["missing_weight_renormalized"])
        self.assertEqual(result["match_decision"], "AUTO_MATCH")
        self.assertTrue(result["auto_merge_allowed"])

    def test_perfect_similarity_with_too_little_evidence_requires_manual_confirmation(self) -> None:
        result = self.cases["match_cases"]["low_coverage_fail_closed"]
        self.assertEqual(result["available_weight_bps"], 5500)
        self.assertEqual(result["renormalized_similarity_bps"], 10000)
        self.assertTrue(result["manual_review_required"])
        self.assertFalse(result["auto_merge_allowed"])
        self.assertIn("可比较证据覆盖不足。", result["manual_review_reasons_zh"])

    def test_time_and_amount_distinguish_same_name_projects(self) -> None:
        result = self.cases["match_cases"]["same_name_time_amount_conflict"]
        self.assertIn("time_evidence", result["mismatched_components"])
        self.assertIn("amount_evidence", result["mismatched_components"])
        self.assertTrue(result["manual_review_required"])
        self.assertFalse(result["auto_merge_allowed"])

    def test_company_conflict_always_requires_manual_confirmation(self) -> None:
        result = self.cases["match_cases"]["company_conflict"]
        self.assertEqual(result["hard_conflict_components"], ["company_entity"])
        self.assertTrue(result["manual_review_required"])
        self.assertFalse(result["auto_merge_allowed"])

    def test_amount_alone_never_decides_project_identity(self) -> None:
        result = self.cases["match_cases"]["amount_only"]
        self.assertEqual(result["renormalized_similarity_bps"], 10000)
        self.assertTrue(result["manual_review_required"])
        self.assertFalse(result["auto_merge_allowed"])
        self.assertFalse(result["amount_alone_decided_match"])
        self.assertIn("金额只能辅助判断，不能单独决定项目身份。", result["manual_review_reasons_zh"])

    def test_raw_name_is_preserved_and_every_change_is_explained(self) -> None:
        result = subject.normalize_name(" 星河能源（系统） 改造项目 ", category="project_name")
        self.assertEqual(result["raw_name"], " 星河能源（系统） 改造项目 ")
        self.assertEqual(result["standard_name"], "星河能源系统改造项目")
        self.assertTrue(result["raw_name_preserved"])
        self.assertFalse(result["irreversible_overwrite_performed"])
        self.assertEqual(result["transformation_count"], len(result["transformations"]))
        self.assertTrue(all(step["explanation_zh"] for step in result["transformations"]))

    def test_abbreviation_typo_and_historical_name_rules_are_explicit(self) -> None:
        expected = {
            "星河改造": "NAME-ABBR-001",
            "星河能原系统改造项目": "NAME-TYPO-001",
            "星河能源一期升级工程": "NAME-HISTORY-001",
        }
        for raw, rule_id in expected.items():
            with self.subTest(raw=raw):
                result = subject.normalize_name(raw, category="project_name")
                self.assertEqual(result["standard_name"], "星河能源系统改造项目")
                self.assertIn(rule_id, result["applied_rule_ids"])

    def test_company_legal_suffix_is_removed_without_overwriting_raw_name(self) -> None:
        result = subject.normalize_name("北辰建设有限责任公司", category="counterparty")
        self.assertEqual(result["standard_name"], "北辰建设")
        self.assertEqual(result["raw_name"], "北辰建设有限责任公司")
        self.assertTrue(any(step["kind"] == "legal_suffix" for step in result["transformations"]))

    def test_full_width_and_letter_case_normalization_is_deterministic(self) -> None:
        result = subject.normalize_name("ＡＬＰＨＡ 项目", category="project_name")
        self.assertEqual(result["standard_name"], "alpha项目")

    def test_ambiguous_curated_rules_fail_closed(self) -> None:
        rules = (
            subject.NameRule("R1", "abbreviation", "同一简称", "标准项目甲", "规则甲"),
            subject.NameRule("R2", "abbreviation", "同一简称", "标准项目乙", "规则乙"),
        )
        with self.assertRaises(subject.ProjectIdentityError) as caught:
            subject.normalize_name("同一简称", category="project_name", rules=rules)
        self.assertEqual(caught.exception.code, "AMBIGUOUS_NAME_RULES")

    def test_float_amount_is_rejected(self) -> None:
        with self.assertRaises(subject.ProjectIdentityError) as caught:
            subject.build_project_evidence(
                record_ref="BAD-AMOUNT",
                evidence={"amount_evidence": {"contract_amount_cents": 1.25}},
            )
        self.assertEqual(caught.exception.code, "INTEGER_CENTS_REQUIRED")

    def test_invalid_project_period_is_rejected(self) -> None:
        with self.assertRaises(subject.ProjectIdentityError) as caught:
            subject.build_project_evidence(
                record_ref="BAD-PERIOD",
                evidence={"time_evidence": {"start_date": "2026-05-02", "finish_date": "2026-05-01"}},
            )
        self.assertEqual(caught.exception.code, "INVALID_PROJECT_PERIOD")

    def test_input_evidence_is_not_mutated(self) -> None:
        evidence = {
            "project_name": " 星河改造 ",
            "amount_evidence": {"contract_amount_cents": 100},
        }
        before = copy.deepcopy(evidence)
        profile = subject.build_project_evidence(record_ref="IMMUTABLE", evidence=evidence)
        self.assertEqual(evidence, before)
        self.assertEqual(profile["original_evidence"], before)
        self.assertFalse(profile["source_mutation_performed"])

    def test_acceptance_projection_covers_all_required_boundaries(self) -> None:
        self.assertEqual(len(self.cases["name_fixtures"]), 6)
        self.assertEqual(set(self.cases["match_cases"]), {
            "missing_contract_renormalized",
            "low_coverage_fail_closed",
            "same_name_time_amount_conflict",
            "company_conflict",
            "amount_only",
        })
        self.assertTrue(self.cases["decision_policy"]["amount_evidence_auxiliary_only"])


if __name__ == "__main__":
    unittest.main()
