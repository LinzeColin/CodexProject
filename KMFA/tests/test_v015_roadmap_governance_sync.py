import json
import re
import unittest

from KMFA.tools.v015_roadmap_governance_sync import (
    MD_END,
    MD_START,
    SOURCE_PACKAGE,
    YAML_END,
    YAML_START,
    expected_outputs,
    load_source,
)


class TestV015RoadmapGovernanceSync(unittest.TestCase):
    def _rendered(self, state: str) -> tuple[str, str]:
        outputs = expected_outputs(SOURCE_PACKAGE, validation_state=state)
        roadmap = next(value for path, value in outputs.items() if path.name == "roadmap.yaml")
        record = next(value for path, value in outputs.items() if path.name == "开发记录.md")
        return roadmap, record

    def test_source_counts_and_unique_ids(self) -> None:
        data, _ = load_source(SOURCE_PACKAGE)
        stages = data["stages"]
        phases = [phase for stage in stages for phase in stage["phases"]]
        tasks = [task for phase in phases for task in phase["tasks"]]
        task_ids = [
            f"{stage['id']}{phase['id']}{task['id']}"
            for stage in stages for phase in stage["phases"] for task in phase["tasks"]
        ]
        self.assertEqual((len(stages), len(phases), len(tasks)), (24, 72, 216))
        self.assertEqual(len(task_ids), len(set(task_ids)))
        self.assertEqual((task_ids[0], task_ids[-1]), ("S01P1T01", "S24P3T03"))

    def _assert_s07_p3_state(self, text: str, acceptance: str) -> None:
        final = acceptance == "PASSED"
        tokens = (
            'current_stage_id: "S07"',
            'current_phase_id: "V015_S07_P3_RELEASE_GATE"',
            'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
            'current_phase_is_taskpack_roadmap_phase: true',
            'current_task_is_taskpack_roadmap_task: true',
            'current_task_id: "KMFA-V015-S07-P3-RELEASE-GATE-20260715"',
            'current_acceptance_id: "ACC-KMFA-V015-S07-P3-RELEASE-GATE"',
            "governance_model_count: 10",
            "active_formula_count: 343",
            "active_parameter_count: 1622",
            'current_parameter_range: "PARAM-KMFA-1999..2007"',
            f'phase_acceptance_status: "{acceptance}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 100",
            's06_stage_review_acceptance_status: "PASSED"',
            "s07_entry_allowed: true",
            "s07_p1_entry_allowed: false",
            "s07_p1_started: true",
            's07_p1_acceptance_status: "PASSED"',
            "s07_p2_entry_allowed: false",
            "s07_p2_started: true",
            's07_p2_acceptance_status: "PASSED"',
            "s07_p3_entry_allowed: false",
            "s07_p3_started: true",
            f's07_p3_acceptance_status: "{acceptance}"',
            f"s07_stage_review_entry_allowed: {str(final).lower()}",
            "s07_p1_field_type_count: 5",
            "s07_p1_money_tolerance_cents: 0",
            "s07_p1_minimum_fail_difference_cents: 1",
            "s07_p1_private_project_count: 8",
            "s07_p1_private_accepted_field_count: 92",
            "s07_p1_private_formula_fail_count: 0",
            "s07_p1_difference_report_required_field_count: 12",
            "s07_p1_open_unconfirmed_item_count: 128",
            "s07_p1_open_items_may_be_treated_as_resolved: false",
            "s07_p2_private_conflict_candidate_count: 6",
            "s07_p3_human_status_label_count: 3",
            's07_p3_current_report_display_label_zh: "暂不可使用"',
            "s07_p3_current_formal_report_release_allowed: false",
            "s07_p3_private_regression_pass_rate_bps: 10000",
            "github_upload_performed: false",
            "app_reinstall_performed: false",
            "business_execution_performed: false",
        )
        for token in tokens:
            self.assertIn(token, text)

    def test_pending_and_passed_states_advance_only_s07_p3_gate(self) -> None:
        for state, decision, next_gate in (
            ("PENDING_FINAL_VALIDATION", "REMAIN_IN_S07_P3_FINAL_VALIDATION", "S07-P3-FINAL-VALIDATION"),
            ("PASSED", "CONTINUE_TO_S07_STAGE_REVIEW_ONLY", "S07-STAGE-REVIEW"),
        ):
            roadmap, record = self._rendered(state)
            self.assertEqual((roadmap.count(YAML_START), roadmap.count(YAML_END)), (1, 1))
            self.assertEqual((record.count(MD_START), record.count(MD_END)), (1, 1))
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                self._assert_s07_p3_state(text, state)
                self.assertIn(f'decision: "{decision}"', text)
                self.assertIn(f'next_gate_id: "{next_gate}"', text)
            self.assertNotIn("/" + "Users" + "/", generated)
            self.assertIn("128", record)
            self.assertIn("暂不可使用", record)
            self.assertRegex(generated, r'(?s)- stage_id: "S06".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertRegex(generated, r'(?s)- stage_id: "S07".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100')

    def test_s07_p3_phase_and_tasks_are_receipt_gated(self) -> None:
        for state in ("PENDING_FINAL_VALIDATION", "PASSED"):
            roadmap, record = self._rendered(state)
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            self.assertRegex(generated, rf'(?s)- phase_id: "S07-P3".*?acceptance_status: "{state}".*?execution_percentage: 100')
            for task_id in ("S07P3T01", "S07P3T02", "S07P3T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{state}"')
            generated_record = record.split(MD_START, 1)[1].split(MD_END, 1)[0]
            task_rows = [line for line in generated_record.splitlines() if re.match(r"^\| S\d{2} \|", line)]
            self.assertEqual(len(task_rows), 216)

    def test_s07_stage_review_pending_and_passed_states_are_distinct(self) -> None:
        for state, acceptance, lifecycle, stage_acceptance, decision, next_gate, s08_entry in (
            (
                "S07_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "IN_PROGRESS",
                "PENDING",
                "REMAIN_IN_S07_STAGE_REVIEW",
                "S07-STAGE-REVIEW-FINAL-VALIDATION",
                False,
            ),
            (
                "S07_STAGE_REVIEW_PASSED",
                "PASSED",
                "COMPLETED",
                "PASSED",
                "GO_TO_S08_P1_ONLY",
                "S08-P1",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_phase_id: "V015_S07_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S07-STAGE-REVIEW-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S07-STAGE-REVIEW"',
                    "active_formula_count: 344",
                    "active_parameter_count: 1628",
                    'current_parameter_range: "PARAM-KMFA-2008..2013"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_lifecycle_status: "{lifecycle}"',
                    f'stage_acceptance_status: "{stage_acceptance}"',
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s07_stage_review_started: true",
                    f"s07_stage_review_performed: {str(s08_entry).lower()}",
                    f"s08_p1_entry_allowed: {str(s08_entry).lower()}",
                    "s08_p1_started: false",
                    "s07_predecessor_receipt_count: 54",
                    "s07_cross_phase_contract_count: 20",
                    "s07_binding_check_count: 16",
                ):
                    self.assertIn(token, text)
            self.assertIn("128", record)
            self.assertIn("暂不可使用", record)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S07".*?status: "{lifecycle}".*?acceptance_status: "{stage_acceptance}".*?execution_percentage: 100',
            )

    def test_s08_p1_pending_and_passed_states_advance_only_p2_entry(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S08_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S08_P1_FINAL_VALIDATION",
                "S08-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S08_P1_PASSED",
                "PASSED",
                "CONTINUE_TO_S08_P2_ONLY",
                "S08-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S08"',
                    'current_phase_id: "V015_S08_P1_PROJECT_COMPOSITE_IDENTITY"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S08-P1-PROJECT-COMPOSITE-IDENTITY-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S08-P1-PROJECT-COMPOSITE-IDENTITY"',
                    "active_formula_count: 345",
                    "active_parameter_count: 1636",
                    'current_parameter_range: "PARAM-KMFA-2014..2021"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s08_p1_started: true",
                    f's08_p1_acceptance_status: "{acceptance}"',
                    f"s08_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s08_p2_started: false",
                    "s08_p3_entry_allowed: false",
                    "s08_stage_review_entry_allowed: false",
                    "s08_p1_component_count: 8",
                    "s08_p1_matching_weight_total_bps: 10000",
                    "s08_p1_name_fixture_count: 6",
                    "s08_p1_match_case_count: 5",
                    "s08_p1_raw_name_preserved_count: 6",
                    "s08_p1_irreversible_overwrite_count: 0",
                    "s08_p1_missing_contract_similarity_bps: 10000",
                    "s08_p1_amount_alone_decided_match: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S07".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S08".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S08-P1".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S08P1T01", "S08P1T02", "S08P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("128", record)
            self.assertIn("暂不可使用", record)

    def test_s08_p2_pending_and_passed_states_advance_only_p3_entry(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S08_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S08_P2_FINAL_VALIDATION",
                "S08-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S08_P2_PASSED",
                "PASSED",
                "CONTINUE_TO_S08_P3_ONLY",
                "S08-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S08"',
                    'current_phase_id: "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S08-P2-BUSINESS-ENTITY-HIERARCHY-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S08-P2-BUSINESS-ENTITY-HIERARCHY"',
                    "active_formula_count: 346",
                    "active_parameter_count: 1644",
                    'current_parameter_range: "PARAM-KMFA-2022..2029"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's08_p1_acceptance_status: "PASSED"',
                    "s08_p2_started: true",
                    f's08_p2_acceptance_status: "{acceptance}"',
                    f"s08_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s08_p3_started: false",
                    "s08_stage_review_entry_allowed: false",
                    "s08_p2_company_entity_count: 3",
                    "s08_p2_company_relationship_count: 2",
                    "s08_p2_entity_assignment_case_count: 3",
                    "s08_p2_entity_requires_confirmation_count: 2",
                    "s08_p2_unknown_entity_funds_aggregation_allowed: false",
                    "s08_p2_bank_count: 2",
                    "s08_p2_account_count: 3",
                    "s08_p2_masked_account_count: 3",
                    "s08_p2_public_full_account_value_count: 0",
                    "s08_p2_cross_entity_match_is_high_risk: true",
                    "s08_p2_cross_entity_funds_aggregation_allowed: false",
                    "s08_p2_counterparty_master_count: 2",
                    "s08_p2_multi_role_counterparty_count: 2",
                    "s08_p2_historical_name_count: 2",
                    "s08_p2_forced_counterparty_merge_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S08".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S08-P2".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S08P2T01", "S08P2T02", "S08P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("128", record)
            self.assertIn("暂不可使用", record)

    def test_s08_p3_pending_and_passed_states_advance_only_stage_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S08_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S08_P3_FINAL_VALIDATION",
                "S08-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S08_P3_PASSED",
                "PASSED",
                "CONTINUE_TO_S08_STAGE_REVIEW_ONLY",
                "S08-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S08"',
                    'current_phase_id: "V015_S08_P3_MATCHING_QUALITY_CONFIRMATION"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S08-P3-MATCHING-QUALITY-CONFIRMATION-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S08-P3-MATCHING-QUALITY-CONFIRMATION"',
                    "active_formula_count: 347",
                    "active_parameter_count: 1654",
                    'current_parameter_range: "PARAM-KMFA-2030..2039"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's08_p1_acceptance_status: "PASSED"',
                    's08_p2_acceptance_status: "PASSED"',
                    "s08_p3_entry_allowed: false",
                    "s08_p3_started: true",
                    f's08_p3_acceptance_status: "{acceptance}"',
                    f"s08_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s08_stage_review_started: false",
                    "s08_stage_review_performed: false",
                    's08_stage_review_acceptance_status: "PENDING"',
                    "product_implementation_allowed: false",
                    "s08_p3_match_state_count: 3",
                    "s08_p3_auto_match_min_bps: 8500",
                    "s08_p3_candidate_review_min_bps: 7000",
                    "s08_p3_thresholds_externalized: true",
                    "s08_p3_threshold_change_requires_regression: true",
                    "s08_p3_policy_regression_case_count: 5",
                    "s08_p3_policy_regression_fail_count: 0",
                    "s08_p3_confirmation_card_count: 2",
                    "s08_p3_confirmation_technical_term_occurrence_count: 0",
                    "s08_p3_control_event_count: 4",
                    "s08_p3_reversal_event_count: 1",
                    "s08_p3_rollback_event_count: 1",
                    "s08_p3_recalculation_receipt_count: 4",
                    "s08_p3_direct_fact_mutation_rejected: true",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S08".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S08-P3".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S08P3T01", "S08P3T02", "S08P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("128", record)
            self.assertIn("暂不可使用", record)

    def test_s08_stage_review_pending_and_passed_states_are_distinct(self) -> None:
        for state, acceptance, lifecycle, stage_acceptance, decision, next_gate, s09_entry in (
            (
                "S08_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "IN_PROGRESS",
                "PENDING",
                "REMAIN_IN_S08_STAGE_REVIEW",
                "S08-STAGE-REVIEW-FINAL-VALIDATION",
                False,
            ),
            (
                "S08_STAGE_REVIEW_PASSED",
                "PASSED",
                "COMPLETED",
                "PASSED",
                "GO_TO_S09_P1_ONLY",
                "S09-P1",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S08"',
                    'current_phase_id: "V015_S08_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S08-STAGE-REVIEW-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S08-STAGE-REVIEW"',
                    "active_formula_count: 348",
                    "active_parameter_count: 1660",
                    'current_parameter_range: "PARAM-KMFA-2040..2045"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_lifecycle_status: "{lifecycle}"',
                    f'stage_acceptance_status: "{stage_acceptance}"',
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s08_stage_review_started: true",
                    f"s08_stage_review_performed: {str(s09_entry).lower()}",
                    f"s09_p1_entry_allowed: {str(s09_entry).lower()}",
                    "s09_p1_started: false",
                    "s08_predecessor_receipt_count: 57",
                    "s08_cross_phase_contract_count: 22",
                    "s08_binding_check_count: 20",
                    "s08_fixed_review_finding_count: 3",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S08".*?status: "{lifecycle}".*?acceptance_status: "{stage_acceptance}".*?execution_percentage: 100',
            )
            self.assertIn("128", record)
            self.assertIn("暂不可使用", record)

    def test_s09_p1_pending_and_passed_states_advance_only_s09_p2_gate(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S09_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S09_P1_FINAL_VALIDATION",
                "S09-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S09_P1_PASSED",
                "PASSED",
                "CONTINUE_TO_S09_P2_ONLY",
                "S09-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S09"',
                    'current_phase_id: "V015_S09_P1_SCOPE_RULE_MODELING"',
                    'current_task_id: "KMFA-V015-S09-P1-SCOPE-RULE-MODELING-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S09-P1-SCOPE-RULE-MODELING"',
                    "active_formula_count: 349",
                    "active_parameter_count: 1669",
                    'current_parameter_range: "PARAM-KMFA-2046..2054"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s09_p1_started: true",
                    f's09_p1_acceptance_status: "{acceptance}"',
                    f"s09_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s09_p2_started: false",
                    "s09_p3_entry_allowed: false",
                    "s09_stage_review_entry_allowed: false",
                    "s09_p1_legal_ledger_count: 1",
                    "s09_p1_derived_view_count: 5",
                    "s09_p1_difference_type_count: 8",
                    "s09_p1_adjustment_event_count: 5",
                    "s09_p1_silent_offset_count: 0",
                    "s09_p1_unapproved_effective_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S08".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S09".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S09-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S09P1T01", "S09P1T02", "S09P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("唯一账本", record)
            self.assertIn("高风险", record)

    def test_s09_p2_pending_and_passed_states_advance_only_s09_p3_gate(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S09_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S09_P2_FINAL_VALIDATION",
                "S09-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S09_P2_PASSED",
                "PASSED",
                "CONTINUE_TO_S09_P3_ONLY",
                "S09-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S09"',
                    'current_phase_id: "V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE"',
                    'current_task_id: "KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-ENGINE-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-ENGINE"',
                    "active_formula_count: 350",
                    "active_parameter_count: 1679",
                    'current_parameter_range: "PARAM-KMFA-2055..2064"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's09_p1_acceptance_status: "PASSED"',
                    "s09_p2_started: true",
                    f's09_p2_acceptance_status: "{acceptance}"',
                    f"s09_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s09_p3_started: false",
                    "s09_stage_review_entry_allowed: false",
                    "s09_p2_conversion_rule_count: 2",
                    "s09_p2_conservation_residual_cents: 0",
                    "s09_p2_reconciliation_source_count: 4",
                    "s09_p2_reconciliation_difference_count: 2",
                    "s09_p2_silent_offset_count: 0",
                    "s09_p2_rerun_chain_layer_count: 4",
                    "s09_p2_persistent_same_source_blocked: true",
                    "s09_p2_cross_source_auto_winner_count: 0",
                    "s09_p2_source_snapshot_unchanged: true",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S09".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S09-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S09P2T01", "S09P2T02", "S09P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("整数分", record)
            self.assertIn("不静默", record)

    def test_s09_p3_pending_and_passed_states_stop_at_stage_review_gate(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S09_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S09_P3_FINAL_VALIDATION",
                "S09-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S09_P3_PASSED",
                "PASSED",
                "CONTINUE_TO_S09_STAGE_REVIEW_ONLY",
                "S09-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S09"',
                    'current_phase_id: "V015_S09_P3_HUMAN_READABLE_AUDIT"',
                    'current_task_id: "KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT"',
                    "active_formula_count: 351",
                    "active_parameter_count: 1689",
                    'current_parameter_range: "PARAM-KMFA-2065..2074"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's09_p1_acceptance_status: "PASSED"',
                    's09_p2_acceptance_status: "PASSED"',
                    "s09_p3_started: true",
                    f's09_p3_acceptance_status: "{acceptance}"',
                    f"s09_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s09_stage_review_started: false",
                    "s09_stage_review_performed: false",
                    "s10_p1_entry_allowed: false",
                    "s09_p3_manual_audience_count: 2",
                    "s09_p3_transformation_rule_count: 2",
                    "s09_p3_difference_rule_count: 8",
                    "s09_p3_human_rule_count: 10",
                    "s09_p3_report_included_difference_count: 1",
                    "s09_p3_report_technical_term_occurrence_count: 0",
                    "s09_p3_closure_required_step_count: 6",
                    "s09_p3_closure_event_count: 6",
                    "s09_p3_closure_feedback_count: 6",
                    "s09_p3_refresh_state_persisted: true",
                    "s09_p3_history_queryable: true",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S09".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S09-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S09P3T01", "S09P3T02", "S09P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("中文规则手册", record)
            self.assertIn("六步", record)

    def test_s09_stage_review_pending_and_passed_states_are_distinct(self) -> None:
        for state, acceptance, lifecycle, stage_acceptance, decision, next_gate, s10_entry in (
            (
                "S09_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "IN_PROGRESS",
                "PENDING",
                "REMAIN_IN_S09_STAGE_REVIEW",
                "S09-STAGE-REVIEW-FINAL-VALIDATION",
                False,
            ),
            (
                "S09_STAGE_REVIEW_PASSED",
                "PASSED",
                "COMPLETED",
                "PASSED",
                "GO_TO_S10_P1_ONLY",
                "S10-P1",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S09"',
                    'current_phase_id: "V015_S09_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    'current_task_id: "KMFA-V015-S09-STAGE-REVIEW-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S09-STAGE-REVIEW"',
                    "active_formula_count: 352",
                    "active_parameter_count: 1696",
                    'current_parameter_range: "PARAM-KMFA-2075..2081"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_lifecycle_status: "{lifecycle}"',
                    f'stage_acceptance_status: "{stage_acceptance}"',
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's09_p1_acceptance_status: "PASSED"',
                    's09_p2_acceptance_status: "PASSED"',
                    's09_p3_acceptance_status: "PASSED"',
                    "s09_stage_review_started: true",
                    f"s09_stage_review_performed: {str(s10_entry).lower()}",
                    f's09_stage_review_acceptance_status: "{acceptance}"',
                    f"s10_entry_allowed: {str(s10_entry).lower()}",
                    f"s10_p1_entry_allowed: {str(s10_entry).lower()}",
                    "s10_p1_started: false",
                    "s09_predecessor_phase_count: 3",
                    "s09_predecessor_task_accepted_count: 9",
                    "s09_predecessor_receipt_count: 60",
                    "s09_cross_phase_contract_count: 24",
                    "s09_binding_check_count: 30",
                    "s09_fixed_review_finding_count: 3",
                    "s09_open_review_finding_count: 0",
                    "s09_routed_residual_risk_count: 5",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S09".*?status: "{lifecycle}".*?acceptance_status: "{stage_acceptance}".*?execution_percentage: 100',
            )
            self.assertIn("口径转换", record)
            self.assertIn("差异", record)

    def test_s10_p1_pending_and_passed_states_advance_only_s10_p2_gate(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S10_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S10_P1_FINAL_VALIDATION",
                "S10-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S10_P1_PASSED",
                "PASSED",
                "CONTINUE_TO_S10_P2_ONLY",
                "S10-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S10"',
                    'current_phase_id: "V015_S10_P1_GENERAL_IMPORT"',
                    'current_task_id: "KMFA-V015-S10-P1-GENERAL-IMPORT-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S10-P1-GENERAL-IMPORT"',
                    "active_formula_count: 353",
                    "active_parameter_count: 1708",
                    'current_parameter_range: "PARAM-KMFA-2082..2093"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's09_stage_review_acceptance_status: "PASSED"',
                    "s10_p1_started: true",
                    f's10_p1_acceptance_status: "{acceptance}"',
                    f"s10_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s10_p2_started: false",
                    "s10_p3_entry_allowed: false",
                    "s10_stage_review_entry_allowed: false",
                    "s10_p1_supported_format_category_count: 6",
                    "s10_p1_supported_extension_count: 8",
                    "s10_p1_preview_required_field_count: 6",
                    "s10_p1_live_check_count: 32",
                    "s10_p1_live_check_failed_count: 0",
                    "s10_p1_bad_file_isolation_validated: true",
                    "s10_p1_path_traversal_rejected: true",
                    "s10_p1_compression_bomb_rejected: true",
                    "s10_p1_confirmation_required: true",
                    "s10_p1_idempotent_replay_validated: true",
                    "s10_p1_interruption_resume_validated: true",
                    "s10_p1_partial_commit_visible: false",
                    "s10_p1_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S09".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S10".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S10-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S10P1T01", "S10P1T02", "S10P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("路径穿越", record)
            self.assertIn("重复导入", record)

    def test_s10_p2_pending_and_passed_states_advance_only_s10_p3_gate(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S10_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S10_P2_FINAL_VALIDATION",
                "S10-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S10_P2_PASSED",
                "PASSED",
                "CONTINUE_TO_S10_P3_ONLY",
                "S10-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S10"',
                    'current_phase_id: "V015_S10_P2_SOURCE_ADAPTERS"',
                    'current_task_id: "KMFA-V015-S10-P2-SOURCE-ADAPTERS-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S10-P2-SOURCE-ADAPTERS"',
                    "active_formula_count: 354",
                    "active_parameter_count: 1721",
                    'current_parameter_range: "PARAM-KMFA-2094..2106"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's10_p1_acceptance_status: "PASSED"',
                    "s10_p2_started: true",
                    f's10_p2_acceptance_status: "{acceptance}"',
                    f"s10_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s10_p3_started: false",
                    "s10_stage_review_entry_allowed: false",
                    "s10_p2_source_system_count: 6",
                    "s10_p2_adapter_template_count: 15",
                    "s10_p2_redcircle_template_count: 4",
                    "s10_p2_kingdee_template_count: 4",
                    "s10_p2_wps_template_count: 4",
                    "s10_p2_auxiliary_template_count: 3",
                    "s10_p2_mapping_versioned_template_count: 15",
                    "s10_p2_live_check_count: 42",
                    "s10_p2_live_check_failed_count: 0",
                    "s10_p2_ambiguous_or_unknown_mapping_rejected: true",
                    "s10_p2_unknown_account_quarantined: true",
                    "s10_p2_source_hierarchy_complete: true",
                    "s10_p2_raw_root_access_count: 0",
                    "s10_p2_automatic_login_performed: false",
                    "s10_p2_live_connector_call_count: 0",
                    "s10_p2_credential_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S09".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S10".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S10-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S10P2T01", "S10P2T02", "S10P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("不猜", record)
            self.assertIn("账户不明", record)

    def test_s10_p3_pending_and_passed_states_advance_only_stage_review_gate(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S10_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S10_P3_FINAL_VALIDATION",
                "S10-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S10_P3_PASSED",
                "PASSED",
                "CONTINUE_TO_S10_STAGE_REVIEW_ONLY",
                "S10-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S10"',
                    'current_phase_id: "V015_S10_P3_AUTOMATIC_INGESTION_RESERVE"',
                    'current_task_id: "KMFA-V015-S10-P3-AUTOMATIC-INGESTION-RESERVE-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S10-P3-AUTOMATIC-INGESTION-RESERVE"',
                    "active_formula_count: 355",
                    "active_parameter_count: 1733",
                    'current_parameter_range: "PARAM-KMFA-2107..2118"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's10_p1_acceptance_status: "PASSED"',
                    's10_p2_acceptance_status: "PASSED"',
                    "s10_p3_entry_allowed: false",
                    "s10_p3_started: true",
                    f's10_p3_acceptance_status: "{acceptance}"',
                    f"s10_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s10_stage_review_started: false",
                    "s10_p3_future_source_count: 5",
                    "s10_p3_connector_operation_count: 6",
                    "s10_p3_schedule_frequency_count: 3",
                    "s10_p3_retry_budget: 3",
                    's10_p3_retry_delays_minutes: "15;60;240"',
                    "s10_p3_no_data_retry_count: 0",
                    "s10_p3_manual_import_available: true",
                    "s10_p3_activation_gate_count: 5",
                    "s10_p3_activation_criteria_count: 8",
                    "s10_p3_live_check_count: 48",
                    "s10_p3_live_check_failed_count: 0",
                    "s10_p3_automatic_connector_enabled_count: 0",
                    "s10_p3_raw_root_access_count: 0",
                    "s10_p3_live_connector_call_count: 0",
                    "s10_p3_credential_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S09".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S10".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S10-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S10P3T01", "S10P3T02", "S10P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("没有连接任何真实平台", record)
            self.assertIn("手工导入", record)
            self.assertIn("逐个通过安全评审", record)

    def test_s10_stage_review_pending_and_passed_states_open_only_s11_p1(self) -> None:
        for state, acceptance, decision, next_gate, performed, s11_entry in (
            (
                "S10_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S10_STAGE_REVIEW",
                "S10-STAGE-REVIEW-FINAL-VALIDATION",
                False,
                False,
            ),
            (
                "S10_STAGE_REVIEW_PASSED",
                "PASSED",
                "GO_TO_S11_P1_ONLY",
                "S11-P1",
                True,
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S10"',
                    'current_phase_id: "V015_S10_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    'current_phase_is_taskpack_roadmap_phase: false',
                    'current_task_is_taskpack_roadmap_task: false',
                    'current_task_id: "KMFA-V015-S10-STAGE-REVIEW-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S10-STAGE-REVIEW"',
                    "active_formula_count: 356",
                    "active_parameter_count: 1740",
                    'current_parameter_range: "PARAM-KMFA-2119..2125"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s10_stage_review_entry_allowed: false",
                    "s10_stage_review_started: true",
                    f"s10_stage_review_performed: {str(performed).lower()}",
                    f's10_stage_review_acceptance_status: "{acceptance}"',
                    f"s11_entry_allowed: {str(s11_entry).lower()}",
                    f"s11_p1_entry_allowed: {str(s11_entry).lower()}",
                    "s11_p1_started: false",
                    "s10_predecessor_phase_count: 3",
                    "s10_predecessor_task_accepted_count: 9",
                    "s10_predecessor_receipt_count: 57",
                    "s10_cross_phase_contract_count: 24",
                    "s10_live_check_count: 36",
                    "s10_fixed_review_finding_count: 3",
                    "s10_open_review_finding_count: 0",
                    "s10_routed_residual_risk_count: 5",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S10".*?status: "{"COMPLETED" if performed else "IN_PROGRESS"}".*?acceptance_status: "{"PASSED" if performed else "PENDING"}".*?execution_percentage: 100',
            )
            self.assertIn("没有", record)
            self.assertIn("GitHub", record)

    def test_s11_p1_pending_and_passed_states_advance_only_s11_p2_gate(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S11_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S11_P1_FINAL_VALIDATION",
                "S11-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S11_P1_PASSED",
                "PASSED",
                "CONTINUE_TO_S11_P2_ONLY",
                "S11-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S11"',
                    'current_phase_id: "V015_S11_P1_QUALITY_RULES"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_phase_is_taskpack_roadmap_phase: true',
                    'current_task_is_taskpack_roadmap_task: true',
                    'current_task_id: "KMFA-V015-S11-P1-QUALITY-RULES-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S11-P1-QUALITY-RULES"',
                    "active_formula_count: 357",
                    "active_parameter_count: 1753",
                    'current_parameter_range: "PARAM-KMFA-2126..2138"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s11_p1_entry_allowed: false",
                    "s11_p1_started: true",
                    f's11_p1_acceptance_status: "{acceptance}"',
                    f"s11_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s11_p2_started: false",
                    "s11_p3_entry_allowed: false",
                    "s11_p3_started: false",
                    "s11_stage_review_entry_allowed: false",
                    "s11_stage_review_started: false",
                    "s11_p1_quality_dimension_count: 8",
                    "s11_p1_quality_rule_count: 16",
                    "s11_p1_hard_gate_count: 7",
                    "s11_p1_human_status_count: 4",
                    "s11_p1_rule_weight_total_bps: 10000",
                    "s11_p1_pass_min_bps: 9500",
                    "s11_p1_not_usable_below_bps: 7500",
                    "s11_p1_live_check_count: 51",
                    "s11_p1_live_check_failed_count: 0",
                    "s11_p1_high_score_critical_failure_blocked: true",
                    "s11_p1_color_only_status_allowed: false",
                    "s11_p1_raw_root_access_count: 0",
                    "s11_p1_live_source_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S10".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S11".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S11-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S11P1T01", "S11P1T02", "S11P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("关键门禁", record)
            self.assertIn("已过期", record)
            self.assertIn("GitHub", record)

    def test_s11_p2_pending_and_passed_states_advance_only_s11_p3_gate(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S11_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S11_P2_FINAL_VALIDATION",
                "S11-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S11_P2_PASSED",
                "PASSED",
                "CONTINUE_TO_S11_P3_ONLY",
                "S11-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S11"',
                    'current_phase_id: "V015_S11_P2_CHECK_BOARD_DATA_MODEL"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_task_id: "KMFA-V015-S11-P2-CHECK-BOARD-DATA-MODEL-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S11-P2-CHECK-BOARD-DATA-MODEL"',
                    "active_formula_count: 358",
                    "active_parameter_count: 1769",
                    'current_parameter_range: "PARAM-KMFA-2139..2154"',
                    f'phase_acceptance_status: "{acceptance}"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's11_p1_acceptance_status: "PASSED"',
                    "s11_p2_entry_allowed: false",
                    "s11_p2_started: true",
                    f's11_p2_acceptance_status: "{acceptance}"',
                    f"s11_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s11_p3_started: false",
                    "s11_p2_hierarchy_level_count: 6",
                    "s11_p2_board_node_count: 34",
                    "s11_p2_board_leaf_count: 6",
                    "s11_p2_board_max_depth: 5",
                    "s11_p2_flat_leaf_at_root_count: 0",
                    "s11_p2_required_column_count: 7",
                    "s11_p2_view_operation_count: 4",
                    "s11_p2_human_status_count: 4",
                    "s11_p2_alert_type_count: 6",
                    "s11_p2_public_check_count: 83",
                    "s11_p2_public_check_failed_count: 0",
                    "s11_p2_missing_source_actionable_count: 1",
                    "s11_p2_automatic_selected_leaf_count: 1",
                    "s11_p2_backend_fact_only: true",
                    "s11_p2_frontend_status_mutation_allowed: false",
                    "s11_p2_raw_root_access_count: 0",
                    "s11_p2_live_source_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S11".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S11-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S11P2T01", "S11P2T02", "S11P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("六层", record)
            self.assertIn("后端", record)
            self.assertIn("GitHub", record)

    def test_s11_p3_pending_and_passed_states_advance_only_stage_review_gate(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S11_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S11_P3_FINAL_VALIDATION",
                "S11-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S11_P3_PASSED",
                "PASSED",
                "CONTINUE_TO_S11_STAGE_REVIEW_ONLY",
                "S11-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S11"',
                    'current_phase_id: "V015_S11_P3_CHECK_BOARD_INTERFACE"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_task_id: "KMFA-V015-S11-P3-CHECK-BOARD-INTERFACE-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S11-P3-CHECK-BOARD-INTERFACE"',
                    "active_formula_count: 359",
                    "active_parameter_count: 1787",
                    'current_parameter_range: "PARAM-KMFA-2155..2172"',
                    f'phase_acceptance_status: "{acceptance}"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's11_p1_acceptance_status: "PASSED"',
                    's11_p2_acceptance_status: "PASSED"',
                    "s11_p3_entry_allowed: false",
                    "s11_p3_started: true",
                    f's11_p3_acceptance_status: "{acceptance}"',
                    f"s11_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s11_stage_review_started: false",
                    "s12_entry_allowed: false",
                    "s11_p3_interface_row_count: 34",
                    "s11_p3_interface_leaf_count: 6",
                    "s11_p3_matrix_column_count: 6",
                    "s11_p3_filter_control_count: 4",
                    "s11_p3_action_kind_count: 4",
                    "s11_p3_context_field_count: 8",
                    "s11_p3_contrast_pair_count: 7",
                    "s11_p3_public_check_count: 65",
                    "s11_p3_public_check_failed_count: 0",
                    "s11_p3_large_yellow_surface_count: 0",
                    "s11_p3_large_status_surface_count: 0",
                    "s11_p3_frontend_status_write_count: 0",
                    "s11_p3_raw_root_access_count: 0",
                    "s11_p3_live_source_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S11".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S11-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S11P3T01", "S11P3T02", "S11P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("返回", record)
            self.assertIn("界面", record)
            self.assertIn("GitHub", record)

    def test_s11_stage_review_pending_and_passed_states_advance_only_s12_p1_gate(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s12_entry in (
            (
                "S11_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "PENDING",
                "REMAIN_IN_S11_STAGE_REVIEW",
                "S11-STAGE-REVIEW-FINAL-VALIDATION",
                False,
                False,
            ),
            (
                "S11_STAGE_REVIEW_PASSED",
                "PASSED",
                "PASSED",
                "GO_TO_S12_P1_ONLY",
                "S12-P1",
                True,
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S11"',
                    'current_phase_id: "V015_S11_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S11-STAGE-REVIEW-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S11-STAGE-REVIEW"',
                    "active_formula_count: 360",
                    "active_parameter_count: 1796",
                    'current_parameter_range: "PARAM-KMFA-2173..2181"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_acceptance_status: "{stage_status}"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's11_p1_acceptance_status: "PASSED"',
                    's11_p2_acceptance_status: "PASSED"',
                    's11_p3_acceptance_status: "PASSED"',
                    "s11_stage_review_entry_allowed: false",
                    "s11_stage_review_started: true",
                    f"s11_stage_review_performed: {str(performed).lower()}",
                    f's11_stage_review_acceptance_status: "{acceptance}"',
                    f"s12_entry_allowed: {str(s12_entry).lower()}",
                    f"s12_p1_entry_allowed: {str(s12_entry).lower()}",
                    "s12_p1_started: false",
                    "s11_predecessor_phase_count: 3",
                    "s11_predecessor_task_accepted_count: 9",
                    "s11_predecessor_receipt_count: 58",
                    "s11_cross_phase_contract_count: 28",
                    "s11_live_check_count: 45",
                    "s11_fixed_review_finding_count: 3",
                    "s11_open_review_finding_count: 0",
                    "s11_routed_residual_risk_count: 5",
                    "s11_reviewed_action_kind_count: 5",
                    "s11_stale_action_rejection_count: 1",
                    "s11_review_frontend_status_write_count: 0",
                    "s11_review_raw_root_access_count: 0",
                    "s11_review_live_source_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            lifecycle = "COMPLETED" if performed else "IN_PROGRESS"
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S11".*?status: "{lifecycle}".*?acceptance_status: "{stage_status}".*?execution_percentage: 100',
            )
            for task_id in ("S11P1T01", "S11P2T01", "S11P3T01"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?acceptance_status: "PASSED"')
            self.assertIn("旧处理请求", record)
            self.assertIn("S12", record)
            self.assertIn("GitHub", record)

    def test_s12_p1_pending_and_passed_states_advance_only_s12_p2_gate(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S12_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S12_P1_FINAL_VALIDATION",
                "S12-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S12_P1_PASSED",
                "PASSED",
                "CONTINUE_TO_S12_P2_ONLY",
                "S12-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S12"',
                    'current_phase_id: "V015_S12_P1_PROJECT_COST_FACTS"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_task_id: "KMFA-V015-S12-P1-PROJECT-COST-FACTS-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S12-P1-PROJECT-COST-FACTS"',
                    "active_formula_count: 361",
                    "active_parameter_count: 1810",
                    'current_parameter_range: "PARAM-KMFA-2182..2195"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s12_p1_entry_allowed: false",
                    "s12_p1_started: true",
                    f's12_p1_acceptance_status: "{acceptance}"',
                    f"s12_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s12_p2_started: false",
                    "s12_p3_entry_allowed: false",
                    "s12_p3_started: false",
                    "s12_stage_review_entry_allowed: false",
                    "s12_stage_review_started: false",
                    "s12_p1_income_layer_count: 5",
                    "s12_p1_income_fact_count: 7",
                    "s12_p1_unknown_income_basis_count: 1",
                    "s12_p1_unknown_income_merge_allowed: false",
                    "s12_p1_cost_category_count: 10",
                    "s12_p1_traceability_field_count: 7",
                    "s12_p1_allocated_cost_fact_count: 10",
                    "s12_p1_unallocated_cost_pool_count: 3",
                    "s12_p1_input_cost_cents: 70000",
                    "s12_p1_allocated_cost_cents: 55000",
                    "s12_p1_unallocated_cost_cents: 15000",
                    "s12_p1_conservation_delta_cents: 0",
                    "s12_p1_dropped_cost_fact_count: 0",
                    "s12_p1_average_allocation_count: 0",
                    "s12_p1_silent_classification_count: 0",
                    "s12_p1_public_check_count: 63",
                    "s12_p1_public_check_failed_count: 0",
                    "s12_p1_raw_root_access_count: 0",
                    "s12_p1_live_source_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S11".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S12".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S12-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S12P1T01", "S12P1T02", "S12P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("未归集池", record)
            self.assertIn("差额为 0 分", record)
            self.assertIn("GitHub", record)

    def test_s12_p2_pending_and_passed_states_advance_only_s12_p3_gate(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S12_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S12_P2_FINAL_VALIDATION",
                "S12-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S12_P2_PASSED",
                "PASSED",
                "CONTINUE_TO_S12_P3_ONLY",
                "S12-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S12"',
                    'current_phase_id: "V015_S12_P2_CORE_CALCULATIONS"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_task_id: "KMFA-V015-S12-P2-CORE-CALCULATIONS-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S12-P2-CORE-CALCULATIONS"',
                    "active_formula_count: 362",
                    "active_parameter_count: 1826",
                    'current_parameter_range: "PARAM-KMFA-2196..2211"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's12_p1_acceptance_status: "PASSED"',
                    "s12_p2_entry_allowed: false",
                    "s12_p2_started: true",
                    f's12_p2_acceptance_status: "{acceptance}"',
                    f"s12_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s12_p3_started: false",
                    "s12_stage_review_entry_allowed: false",
                    "s12_stage_review_started: false",
                    "s12_p2_margin_view_count: 3",
                    "s12_p2_margin_golden_difference_cents: 0",
                    "s12_p2_money_tolerance_cents: 0",
                    "s12_p2_contract_gross_profit_cents: 30000",
                    "s12_p2_settlement_gross_profit_cents: 20000",
                    "s12_p2_management_gross_profit_cents: 15000",
                    "s12_p2_cash_gross_profit_cents: 20000",
                    "s12_p2_capital_occupied_cents: 10000",
                    "s12_p2_uncollected_counted_as_cash_cents: 0",
                    "s12_p2_degraded_cash_case_count: 1",
                    "s12_p2_risk_policy_threshold_count: 4",
                    "s12_p2_default_risk_trigger_count: 4",
                    "s12_p2_relaxed_risk_trigger_count: 0",
                    "s12_p2_insufficient_data_case_count: 1",
                    "s12_p2_public_check_count: 48",
                    "s12_p2_public_check_failed_count: 0",
                    "s12_p2_raw_root_access_count: 0",
                    "s12_p2_live_source_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S12".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S12-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S12P2T01", "S12P2T02", "S12P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("毛利", record)
            self.assertIn("资料不足", record)
            self.assertIn("GitHub", record)

    def test_s12_p3_pending_and_passed_states_advance_only_stage_review_gate(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S12_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S12_P3_FINAL_VALIDATION",
                "S12-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S12_P3_PASSED",
                "PASSED",
                "GO_TO_S12_STAGE_REVIEW_ONLY",
                "S12-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S12"',
                    'current_phase_id: "V015_S12_P3_ENGINEERING_LOGIC"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_task_id: "KMFA-V015-S12-P3-ENGINEERING-LOGIC-20260715"',
                    'current_acceptance_id: "ACC-KMFA-V015-S12-P3-ENGINEERING-LOGIC"',
                    "active_formula_count: 363",
                    "active_parameter_count: 1842",
                    'current_parameter_range: "PARAM-KMFA-2212..2227"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's12_p1_acceptance_status: "PASSED"',
                    's12_p2_acceptance_status: "PASSED"',
                    "s12_p3_entry_allowed: false",
                    "s12_p3_started: true",
                    f's12_p3_acceptance_status: "{acceptance}"',
                    f"s12_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s12_stage_review_started: false",
                    "s12_p3_change_chain_node_count: 6",
                    "s12_p3_confirmed_change_amount_cents: 20000",
                    "s12_p3_unconfirmed_change_amount_cents: 15000",
                    "s12_p3_unsupported_change_recognized_cents: 0",
                    "s12_p3_settlement_difference_cents: -5000",
                    "s12_p3_invoice_collection_rate_bps: 7778",
                    "s12_p3_external_cost_record_count: 9",
                    "s12_p3_duplicate_record_count: 1",
                    "s12_p3_requires_confirmation_count: 1",
                    "s12_p3_cross_project_anomaly_count: 1",
                    "s12_p3_automatic_low_confidence_allocation_count: 0",
                    "s12_p3_recognized_project_cost_cents: 42000",
                    "s12_p3_inventory_conservation_delta_cents: 0",
                    "s12_p3_explanation_count: 6",
                    "s12_p3_explanation_match_count: 6",
                    "s12_p3_explanation_mismatch_count: 0",
                    "s12_p3_public_check_count: 63",
                    "s12_p3_public_check_failed_count: 0",
                    "s12_p3_raw_root_access_count: 0",
                    "s12_p3_live_source_read_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S12".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S12-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S12P3T01", "S12P3T02", "S12P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("变更", record)
            self.assertIn("低置信", record)
            self.assertIn("GitHub", record)

    def test_s12_stage_review_pending_and_passed_states_advance_only_s13_p1_gate(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s13_entry in (
            (
                "S12_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "PENDING",
                "REMAIN_IN_S12_STAGE_REVIEW",
                "S12-STAGE-REVIEW-FINAL-VALIDATION",
                False,
                False,
            ),
            (
                "S12_STAGE_REVIEW_PASSED",
                "PASSED",
                "PASSED",
                "GO_TO_S13_P1_ONLY",
                "S13-P1",
                True,
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S12"',
                    'current_phase_id: "V015_S12_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S12-STAGE-REVIEW-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S12-STAGE-REVIEW"',
                    "active_formula_count: 364",
                    "active_parameter_count: 1854",
                    'current_parameter_range: "PARAM-KMFA-2228..2239"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_acceptance_status: "{stage_status}"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's12_p1_acceptance_status: "PASSED"',
                    's12_p2_acceptance_status: "PASSED"',
                    's12_p3_acceptance_status: "PASSED"',
                    "s12_stage_review_entry_allowed: false",
                    "s12_stage_review_started: true",
                    f"s12_stage_review_performed: {str(performed).lower()}",
                    f's12_stage_review_acceptance_status: "{acceptance}"',
                    f"s13_entry_allowed: {str(s13_entry).lower()}",
                    f"s13_p1_entry_allowed: {str(s13_entry).lower()}",
                    "s13_p1_started: false",
                    "s12_predecessor_phase_count: 3",
                    "s12_predecessor_task_accepted_count: 9",
                    "s12_predecessor_receipt_count: 63",
                    "s12_predecessor_public_check_count: 174",
                    "s12_cross_phase_contract_count: 36",
                    "s12_live_check_count: 68",
                    "s12_fixed_review_finding_count: 4",
                    "s12_open_review_finding_count: 0",
                    "s12_review_explanation_count: 6",
                    "s12_review_explanation_mismatch_count: 0",
                    "s12_target_cost_conservation_delta_cents: 0",
                    "s12_excluded_candidate_leak_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            lifecycle = "COMPLETED" if performed else "IN_PROGRESS"
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S12".*?status: "{lifecycle}".*?acceptance_status: "{stage_status}".*?execution_percentage: 100',
            )
            for task_id in ("S12P1T01", "S12P2T01", "S12P3T01"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?acceptance_status: "PASSED"')
            self.assertIn("四个", record)
            self.assertIn("S13", record)
            self.assertIn("GitHub", record)

    def test_s13_p1_pending_and_passed_states_advance_only_s13_p2_gate(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S13_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S13_P1_FINAL_VALIDATION",
                "S13-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S13_P1_PASSED",
                "PASSED",
                "CONTINUE_TO_S13_P2_ONLY",
                "S13-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S13"',
                    'current_phase_id: "V015_S13_P1_INDICATOR_REGISTRY"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_task_id: "KMFA-V015-S13-P1-INDICATOR-REGISTRY-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S13-P1-INDICATOR-REGISTRY"',
                    "active_formula_count: 365",
                    "active_parameter_count: 1868",
                    'current_parameter_range: "PARAM-KMFA-2240..2253"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's12_stage_review_acceptance_status: "PASSED"',
                    "s13_entry_allowed: true",
                    "s13_p1_entry_allowed: false",
                    "s13_p1_started: true",
                    f's13_p1_acceptance_status: "{acceptance}"',
                    f"s13_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s13_p2_started: false",
                    "s13_p3_entry_allowed: false",
                    "s13_p3_started: false",
                    "s13_stage_review_entry_allowed: false",
                    "s13_p1_indicator_count: 8",
                    "s13_p1_indicator_domain_count: 8",
                    "s13_p1_parameter_version_count: 8",
                    "s13_p1_function_contract_count: 5",
                    "s13_p1_result_status_count: 6",
                    "s13_p1_public_check_count: 78",
                    "s13_p1_public_check_failed_count: 0",
                    "s13_p1_source_required_for_display: true",
                    "s13_p1_frontend_parameter_write_allowed: false",
                    "s13_p1_silent_exception_allowed: false",
                    "s13_p1_raw_root_access_count: 0",
                    "s13_p1_live_source_read_count: 0",
                    "s13_p1_health_score_computed: false",
                    "s13_p1_action_priority_computed: false",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S12".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S13".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S13-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S13P1T01", "S13P1T02", "S13P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("八类指标", record)
            self.assertIn("生产参数", record)
            self.assertIn("GitHub", record)

    def test_s13_p2_pending_and_passed_states_advance_only_s13_p3_gate(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S13_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S13_P2_FINAL_VALIDATION",
                "S13-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S13_P2_PASSED",
                "PASSED",
                "CONTINUE_TO_S13_P3_ONLY",
                "S13-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S13"',
                    'current_phase_id: "V015_S13_P2_BUSINESS_HEALTH_MODEL"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_task_id: "KMFA-V015-S13-P2-BUSINESS-HEALTH-MODEL-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S13-P2-BUSINESS-HEALTH-MODEL"',
                    "governance_model_count: 11",
                    "active_formula_count: 366",
                    "active_parameter_count: 1886",
                    'current_parameter_range: "PARAM-KMFA-2254..2271"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's13_p1_acceptance_status: "PASSED"',
                    "s13_p2_entry_allowed: false",
                    "s13_p2_started: true",
                    f's13_p2_acceptance_status: "{acceptance}"',
                    f"s13_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s13_p3_started: false",
                    "s13_stage_review_entry_allowed: false",
                    "s13_p2_health_dimension_count: 6",
                    "s13_p2_health_weight_total_bps: 10000",
                    "s13_p2_hard_gate_count: 6",
                    "s13_p2_health_state_count: 6",
                    "s13_p2_freshness_state_count: 3",
                    "s13_p2_scenario_count: 3",
                    "s13_p2_unexplained_change_count: 0",
                    "s13_p2_fact_layer_write_count: 0",
                    "s13_p2_public_check_count: 88",
                    "s13_p2_public_check_failed_count: 0",
                    "s13_p2_hard_gate_overrides_score: true",
                    "s13_p2_unexplained_score_display_allowed: false",
                    "s13_p2_fact_and_assumption_separated: true",
                    "s13_p2_health_model_implemented: true",
                    "s13_p2_synthetic_health_score_computed: true",
                    "s13_p2_real_business_health_score_computed: false",
                    "s13_p2_raw_root_access_count: 0",
                    "s13_p2_live_source_read_count: 0",
                    "s13_p2_action_priority_computed: false",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S13".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                r'(?s)- phase_id: "S13-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S13-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S13P2T01", "S13P2T02", "S13P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("硬门禁", record)
            self.assertIn("假设", record)
            self.assertIn("GitHub", record)

    def test_s13_p3_pending_and_passed_states_advance_only_stage_review_gate(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S13_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S13_P3_FINAL_VALIDATION",
                "S13-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S13_P3_PASSED",
                "PASSED",
                "GO_TO_S13_STAGE_REVIEW_ONLY",
                "S13-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S13"',
                    'current_phase_id: "V015_S13_P3_ACTION_PRIORITY"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    'current_task_id: "KMFA-V015-S13-P3-ACTION-PRIORITY-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S13-P3-ACTION-PRIORITY"',
                    "governance_model_count: 12",
                    "active_formula_count: 367",
                    "active_parameter_count: 1904",
                    'current_parameter_range: "PARAM-KMFA-2272..2289"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's13_p1_acceptance_status: "PASSED"',
                    's13_p2_acceptance_status: "PASSED"',
                    "s13_p3_entry_allowed: false",
                    "s13_p3_started: true",
                    f's13_p3_acceptance_status: "{acceptance}"',
                    f"s13_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s13_stage_review_started: false",
                    "s13_p3_ranking_factor_count: 6",
                    "s13_p3_ranking_weight_total_bps: 10000",
                    "s13_p3_action_domain_count: 5",
                    "s13_p3_candidate_state_count: 5",
                    "s13_p3_focus_item_count: 5",
                    "s13_p3_focus_min_items: 3",
                    "s13_p3_focus_max_items: 5",
                    "s13_p3_focus_domain_cap: 2",
                    "s13_p3_review_decision_count: 4",
                    "s13_p3_outcome_state_count: 3",
                    "s13_p3_public_check_count: 88",
                    "s13_p3_public_check_failed_count: 0",
                    "s13_p3_action_priority_model_implemented: true",
                    "s13_p3_synthetic_action_priority_computed: true",
                    "s13_p3_real_business_action_priority_computed: false",
                    "s13_p3_automatic_execution_count: 0",
                    "s13_p3_recommendation_fact_write_count: 0",
                    "s13_p3_automatic_parameter_change_count: 0",
                    "s13_p3_raw_root_access_count: 0",
                    "s13_p3_live_source_read_count: 0",
                    "s13_p3_real_business_action_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S13".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            for phase_id in ("S13-P1", "S13-P2"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
                )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S13-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S13P3T01", "S13P3T02", "S13P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("3 至 5 件", record)
            self.assertIn("不会自动执行", record)
            self.assertIn("GitHub", record)

    def test_s13_stage_review_pending_and_passed_states_are_distinct(self) -> None:
        for state, acceptance, lifecycle, stage_acceptance, decision, next_gate, s14_entry in (
            (
                "S13_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "IN_PROGRESS",
                "PENDING",
                "REMAIN_IN_S13_STAGE_REVIEW",
                "S13-STAGE-REVIEW-FINAL-VALIDATION",
                False,
            ),
            (
                "S13_STAGE_REVIEW_PASSED",
                "PASSED",
                "COMPLETED",
                "PASSED",
                "GO_TO_S14_P1_ONLY",
                "S14-P1",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            performed = acceptance == "PASSED"
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S13"',
                    'current_phase_id: "V015_S13_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S13-STAGE-REVIEW-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S13-STAGE-REVIEW"',
                    "active_formula_count: 368",
                    "active_parameter_count: 1916",
                    'current_parameter_range: "PARAM-KMFA-2290..2301"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_lifecycle_status: "{lifecycle}"',
                    f'stage_acceptance_status: "{stage_acceptance}"',
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s13_stage_review_started: true",
                    f"s13_stage_review_performed: {str(performed).lower()}",
                    f's13_stage_review_acceptance_status: "{acceptance}"',
                    f"s14_entry_allowed: {str(s14_entry).lower()}",
                    f"s14_p1_entry_allowed: {str(s14_entry).lower()}",
                    "s14_p1_started: false",
                    "s13_predecessor_receipt_count: 60",
                    "s13_predecessor_public_check_count: 254",
                    "s13_cross_phase_contract_count: 36",
                    "s13_live_check_count: 72",
                    "s13_fixed_review_finding_count: 4",
                    "s13_open_review_finding_count: 0",
                    "s13_source_binding_count: 7",
                    "s13_generated_action_candidate_count: 6",
                    "s13_review_focus_item_count: 5",
                    "s13_review_automatic_execution_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S13".*?status: "{lifecycle}".*?acceptance_status: "{stage_acceptance}".*?execution_percentage: 100',
            )
            for phase_id in ("S13-P1", "S13-P2", "S13-P3"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
                )
            self.assertIn("四个跨部分", record)
            self.assertIn("S14", record)
            self.assertIn("GitHub", record)

    def test_s14_p1_pending_and_passed_states_open_only_p2_after_acceptance(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S14_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S14_P1_FINAL_VALIDATION",
                "S14-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S14_P1_PASSED",
                "PASSED",
                "CONTINUE_TO_S14_P2_ONLY",
                "S14-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S14"',
                    'current_phase_id: "V015_S14_P1_INFORMATION_ARCHITECTURE"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S14-P1-INFORMATION-ARCHITECTURE-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S14-P1-INFORMATION-ARCHITECTURE"',
                    "governance_model_count: 12",
                    "active_formula_count: 369",
                    "active_parameter_count: 1934",
                    'current_parameter_range: "PARAM-KMFA-2302..2319"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s14_p1_entry_allowed: false",
                    "s14_p1_started: true",
                    f's14_p1_acceptance_status: "{acceptance}"',
                    f"s14_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s14_p2_started: false",
                    "s14_p3_entry_allowed: false",
                    "s14_stage_review_entry_allowed: false",
                    "s14_p1_primary_navigation_count: 7",
                    "s14_p1_page_type_count: 6",
                    "s14_p1_page_node_count: 18",
                    "s14_p1_breadcrumb_edge_count: 31",
                    "s14_p1_previous_task_coverage_bps: 10000",
                    "s14_p1_dead_end_count: 0",
                    "s14_p1_parent_cycle_count: 0",
                    "s14_p1_stacked_sidebar_used: false",
                    "s14_p1_card_sort_case_count: 21",
                    "s14_p1_card_sort_pass_count: 21",
                    "s14_p1_tree_test_case_count: 10",
                    "s14_p1_tree_test_pass_count: 10",
                    "s14_p1_disclosure_level_count: 3",
                    "s14_p1_default_visible_technical_term_count: 0",
                    "s14_p1_public_check_count: 42",
                    "s14_p1_public_check_failed_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S13".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S14".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S14-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S14P1T01", "S14P1T02", "S14P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("七项中文" if acceptance != "PASSED" else "七个中文", record)
            self.assertIn("S14-P2", record)

    def test_s14_p2_pending_and_passed_states_open_only_p3_after_acceptance(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S14_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S14_P2_FINAL_VALIDATION",
                "S14-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S14_P2_PASSED",
                "PASSED",
                "CONTINUE_TO_S14_P3_ONLY",
                "S14-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S14"',
                    'current_phase_id: "V015_S14_P2_DESIGN_SYSTEM"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S14-P2-DESIGN-SYSTEM-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S14-P2-DESIGN-SYSTEM"',
                    "governance_model_count: 12",
                    "active_formula_count: 370",
                    "active_parameter_count: 1952",
                    'current_parameter_range: "PARAM-KMFA-2320..2337"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's14_p1_acceptance_status: "PASSED"',
                    "s14_p2_entry_allowed: false",
                    "s14_p2_started: true",
                    f's14_p2_acceptance_status: "{acceptance}"',
                    f"s14_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s14_p3_started: false",
                    "s14_stage_review_entry_allowed: false",
                    "s14_p2_theme_count: 2",
                    "s14_p2_contrast_pair_count: 14",
                    "s14_p2_contrast_pass_count: 14",
                    "s14_p2_contrast_fail_count: 0",
                    "s14_p2_warning_area_limit_bps: 800",
                    "s14_p2_component_count: 11",
                    "s14_p2_required_component_state_count: 7",
                    "s14_p2_full_state_coverage_count: 11",
                    "s14_p2_no_feedback_component_count: 0",
                    "s14_p2_color_only_state_count: 0",
                    "s14_p2_maximum_motion_duration_ms: 220",
                    "s14_p2_blocking_animation_count: 0",
                    "s14_p2_decorative_animation_count: 0",
                    "s14_p2_reduced_motion_supported: true",
                    "s14_p2_visual_regression_viewport_count: 3",
                    "s14_p2_public_check_count: 60",
                    "s14_p2_public_check_failed_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S13".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S14".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                r'(?s)- phase_id: "S14-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S14-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S14P2T01", "S14P2T02", "S14P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("商务蓝", record)
            self.assertIn("S14-P3", record)

    def test_s14_p3_pending_and_passed_states_stop_at_stage_review_gate(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S14_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S14_P3_FINAL_VALIDATION",
                "S14-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S14_P3_PASSED",
                "PASSED",
                "CONTINUE_TO_S14_STAGE_REVIEW_ONLY",
                "S14-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S14"',
                    'current_phase_id: "V015_S14_P3_LANGUAGE_CONTENT"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S14-P3-LANGUAGE-CONTENT-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S14-P3-LANGUAGE-CONTENT"',
                    "governance_model_count: 12",
                    "active_formula_count: 371",
                    "active_parameter_count: 1970",
                    'current_parameter_range: "PARAM-KMFA-2338..2355"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's14_p1_acceptance_status: "PASSED"',
                    's14_p2_acceptance_status: "PASSED"',
                    "s14_p3_entry_allowed: false",
                    "s14_p3_started: true",
                    f's14_p3_acceptance_status: "{acceptance}"',
                    f"s14_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s14_stage_review_started: false",
                    "s14_stage_review_performed: false",
                    "s14_p3_dictionary_entry_count: 14",
                    "s14_p3_default_forbidden_term_hit_count: 0",
                    "s14_p3_forbidden_ai_copy_hit_count: 0",
                    "s14_p3_machine_pattern_hit_count: 0",
                    "s14_p3_format_case_count: 10",
                    "s14_p3_format_surface_mismatch_count: 0",
                    "s14_p3_display_underlying_mismatch_count: 0",
                    "s14_p3_content_rule_screen_count: 6",
                    "s14_p3_cognitive_walkthrough_case_count: 6",
                    "s14_p3_cognitive_walkthrough_pass_count: 6",
                    "s14_p3_ten_second_failure_count: 0",
                    "s14_p3_main_question_per_screen: 1",
                    "s14_p3_focus_item_min: 3",
                    "s14_p3_focus_item_max: 5",
                    "s14_p3_primary_next_step_per_screen: 1",
                    "s14_p3_public_check_count: 72",
                    "s14_p3_public_check_failed_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S14".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            for phase_id in ("S14-P1", "S14-P2"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
                )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S14-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S14P3T01", "S14P3T02", "S14P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("普通中文", record)
            self.assertIn("整体复审", record)

    def test_s14_stage_review_pending_and_passed_states_open_only_s15_p1(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s15_entry in (
            (
                "S14_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "PENDING",
                "REMAIN_IN_S14_STAGE_REVIEW",
                "S14-STAGE-REVIEW-FINAL-VALIDATION",
                False,
                False,
            ),
            (
                "S14_STAGE_REVIEW_PASSED",
                "PASSED",
                "PASSED",
                "GO_TO_S15_P1_ONLY",
                "S15-P1",
                True,
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S14"',
                    'current_phase_id: "V015_S14_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S14-STAGE-REVIEW-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S14-STAGE-REVIEW"',
                    "governance_model_count: 12",
                    "active_formula_count: 372",
                    "active_parameter_count: 1982",
                    'current_parameter_range: "PARAM-KMFA-2356..2367"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_acceptance_status: "{stage_status}"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's14_p1_acceptance_status: "PASSED"',
                    's14_p2_acceptance_status: "PASSED"',
                    's14_p3_acceptance_status: "PASSED"',
                    "s14_stage_review_entry_allowed: false",
                    "s14_stage_review_started: true",
                    f"s14_stage_review_performed: {str(performed).lower()}",
                    f's14_stage_review_acceptance_status: "{acceptance}"',
                    f"s15_entry_allowed: {str(s15_entry).lower()}",
                    f"s15_p1_entry_allowed: {str(s15_entry).lower()}",
                    "s15_p1_started: false",
                    "s14_predecessor_phase_count: 3",
                    "s14_predecessor_task_accepted_count: 9",
                    "s14_predecessor_receipt_count: 59",
                    "s14_predecessor_public_check_count: 174",
                    "s14_cross_phase_contract_count: 36",
                    "s14_live_check_count: 84",
                    "s14_fixed_review_finding_count: 4",
                    "s14_open_review_finding_count: 0",
                    "s14_routed_residual_risk_count: 5",
                    "s14_navigation_binding_count: 7",
                    "s14_screen_binding_count: 6",
                    "s14_theme_binding_count: 2",
                    "s14_integration_binding_count: 15",
                    "s14_route_mismatch_count: 0",
                    "s14_number_mismatch_count: 0",
                    "s14_language_mismatch_count: 0",
                    "s14_review_browser_viewport_count: 3",
                    "s14_review_browser_flow_count: 6",
                    "s14_review_raw_root_access_count: 0",
                    "s14_review_live_source_read_count: 0",
                    "s14_review_network_request_count: 0",
                    "s14_review_real_business_action_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            lifecycle = "COMPLETED" if performed else "IN_PROGRESS"
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S14".*?status: "{lifecycle}".*?acceptance_status: "{stage_status}".*?execution_percentage: 100',
            )
            for phase_id in ("S14-P1", "S14-P2", "S14-P3"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
                )
            self.assertIn("导航", record)
            self.assertIn("S15-P1", record)
            self.assertIn("GitHub", record)

    def test_s15_p1_pending_and_passed_states_open_only_s15_p2(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S15_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S15_P1_FINAL_VALIDATION",
                "S15-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S15_P1_PASSED",
                "PASSED",
                "CONTINUE_TO_S15_P2_ONLY",
                "S15-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S15"',
                    'current_phase_id: "V015_S15_P1_APP_SHELL"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S15-P1-APP-SHELL-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S15-P1-APP-SHELL"',
                    "governance_model_count: 12",
                    "active_formula_count: 373",
                    "active_parameter_count: 2000",
                    'current_parameter_range: "PARAM-KMFA-2368..2385"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's14_stage_review_acceptance_status: "PASSED"',
                    "s15_entry_allowed: true",
                    "s15_p1_entry_allowed: false",
                    "s15_p1_started: true",
                    f's15_p1_acceptance_status: "{acceptance}"',
                    f"s15_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s15_p2_started: false",
                    "s15_p3_started: false",
                    "s15_stage_review_started: false",
                    "s15_p1_primary_navigation_count: 7",
                    "s15_p1_deep_link_route_count: 18",
                    "s15_p1_context_dimension_count: 4",
                    "s15_p1_company_context_count: 3",
                    "s15_p1_context_persistence_mechanism_count: 2",
                    "s15_p1_context_restore_flow_count: 3",
                    "s15_p1_company_isolation_guard_count: 3",
                    "s15_p1_cross_company_leak_count: 0",
                    "s15_p1_fault_boundary_count: 4",
                    "s15_p1_recoverable_fault_count: 4",
                    "s15_p1_browser_viewport_count: 2",
                    "s15_p1_browser_flow_count: 6",
                    "s15_p1_visual_evidence_count: 4",
                    "s15_p1_public_check_count: 8",
                    "s15_p1_public_check_failed_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S14".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S15".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S15-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S15P1T01", "S15P1T02", "S15P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("应用外壳", record)
            self.assertIn("S15-P2", record)
            self.assertIn("GitHub", record)

    def test_s15_p2_pending_and_passed_open_only_s15_p3(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S15_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S15_P2_FINAL_VALIDATION",
                "S15-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S15_P2_PASSED",
                "PASSED",
                "CONTINUE_TO_S15_P3_ONLY",
                "S15-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S15"',
                    'current_phase_id: "V015_S15_P2_IDENTITY_ROLES"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S15-P2-IDENTITY-ROLES-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S15-P2-IDENTITY-ROLES"',
                    "governance_model_count: 12",
                    "active_formula_count: 374",
                    "active_parameter_count: 2018",
                    'current_parameter_range: "PARAM-KMFA-2386..2403"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's15_p1_acceptance_status: "PASSED"',
                    "s15_p2_entry_allowed: false",
                    "s15_p2_started: true",
                    f's15_p2_acceptance_status: "{acceptance}"',
                    f"s15_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s15_p3_started: false",
                    "s15_stage_review_started: false",
                    "s15_p2_public_user_count: 2",
                    "s15_p2_role_hat_count: 4",
                    "s15_p2_resource_domain_count: 5",
                    "s15_p2_permission_grant_count: 28",
                    "s15_p2_default_deny_enabled: true",
                    "s15_p2_approval_flow_count: 3",
                    "s15_p2_same_person_different_role_supported: true",
                    "s15_p2_same_role_self_approval_allowed: false",
                    "s15_p2_public_check_count: 12",
                    "s15_p2_public_check_failed_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S15".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                r'(?s)- phase_id: "S15-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S15-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S15P2T01", "S15P2T02", "S15P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("角色", record)
            self.assertIn("S15-P3", record)
            self.assertIn("GitHub", record)

    def test_s15_p3_pending_and_passed_stop_at_stage_review_gate(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S15_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S15_P3_FINAL_VALIDATION",
                "S15-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S15_P3_PASSED",
                "PASSED",
                "CONTINUE_TO_S15_STAGE_REVIEW_ONLY",
                "S15-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S15"',
                    'current_phase_id: "V015_S15_P3_APP_EXPERIENCE"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S15-P3-APP-EXPERIENCE-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S15-P3-APP-EXPERIENCE"',
                    "governance_model_count: 12",
                    "active_formula_count: 375",
                    "active_parameter_count: 2036",
                    'current_parameter_range: "PARAM-KMFA-2404..2421"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's15_p1_acceptance_status: "PASSED"',
                    's15_p2_acceptance_status: "PASSED"',
                    "s15_p3_entry_allowed: false",
                    "s15_p3_started: true",
                    f's15_p3_acceptance_status: "{acceptance}"',
                    f"s15_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s15_stage_review_started: false",
                    "s15_stage_review_performed: false",
                    "s15_p3_search_item_count: 8",
                    "s15_p3_search_kind_count: 4",
                    "s15_p3_notification_item_count: 4",
                    "s15_p3_notification_category_count: 4",
                    "s15_p3_preference_field_count: 4",
                    "s15_p3_table_column_option_count: 3",
                    "s15_p3_density_option_count: 2",
                    "s15_p3_sensitive_result_leak_count: 0",
                    "s15_p3_notification_without_action_count: 0",
                    "s15_p3_fact_layer_write_count: 0",
                    "s15_p3_other_user_preference_write_count: 0",
                    "s15_p3_browser_viewport_count: 2",
                    "s15_p3_browser_flow_count: 6",
                    "s15_p3_visual_evidence_count: 4",
                    "s15_p3_public_check_count: 16",
                    "s15_p3_public_check_failed_count: 0",
                    "s15_p3_raw_root_access_count: 0",
                    "s15_p3_live_source_read_count: 0",
                    "s15_p3_external_network_request_count: 0",
                    "s15_p3_real_identity_count: 0",
                    "s15_p3_credential_count: 0",
                    "s15_p3_real_business_action_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S15".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            for phase_id in ("S15-P1", "S15-P2"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
                )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S15-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S15P3T01", "S15P3T02", "S15P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("全局搜索", record)
            self.assertIn("通知", record)
            self.assertIn("GitHub", record)

    def test_s15_stage_review_pending_and_passed_open_only_s16_p1(self) -> None:
        for state, acceptance, lifecycle, stage_acceptance, decision, next_gate, performed, s16_entry in (
            (
                "S15_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "IN_PROGRESS",
                "PENDING",
                "REMAIN_IN_S15_STAGE_REVIEW",
                "S15-STAGE-REVIEW-FINAL-VALIDATION",
                False,
                False,
            ),
            (
                "S15_STAGE_REVIEW_PASSED",
                "PASSED",
                "COMPLETED",
                "PASSED",
                "GO_TO_S16_P1_ONLY",
                "S16-P1",
                True,
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S15"',
                    'current_phase_id: "V015_S15_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S15-STAGE-REVIEW-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S15-STAGE-REVIEW"',
                    "governance_model_count: 12",
                    "active_formula_count: 376",
                    "active_parameter_count: 2048",
                    'current_parameter_range: "PARAM-KMFA-2422..2433"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_lifecycle_status: "{lifecycle}"',
                    f'stage_acceptance_status: "{stage_acceptance}"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's15_p1_acceptance_status: "PASSED"',
                    's15_p2_acceptance_status: "PASSED"',
                    's15_p3_acceptance_status: "PASSED"',
                    "s15_stage_review_entry_allowed: false",
                    "s15_stage_review_started: true",
                    f"s15_stage_review_performed: {str(performed).lower()}",
                    f's15_stage_review_acceptance_status: "{acceptance}"',
                    f"s16_entry_allowed: {str(s16_entry).lower()}",
                    f"s16_p1_entry_allowed: {str(s16_entry).lower()}",
                    "s16_p1_started: false",
                    's16_p1_acceptance_status: "PENDING"',
                    "s15_predecessor_phase_count: 3",
                    "s15_predecessor_task_accepted_count: 9",
                    "s15_predecessor_receipt_count: 60",
                    "s15_predecessor_public_check_count: 36",
                    "s15_cross_phase_contract_count: 41",
                    "s15_live_check_count: 72",
                    "s15_fixed_review_finding_count: 4",
                    "s15_open_review_finding_count: 0",
                    "s15_routed_residual_risk_count: 5",
                    "s15_design_audit_score: 92",
                    "s15_review_browser_viewport_count: 3",
                    "s15_review_browser_flow_count: 8",
                    "s15_review_visual_evidence_count: 4",
                    "s15_review_raw_root_access_count: 0",
                    "s15_review_live_source_read_count: 0",
                    "s15_review_external_network_request_count: 0",
                    "s15_review_real_identity_count: 0",
                    "s15_review_real_business_action_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S15".*?status: "{lifecycle}".*?acceptance_status: "{stage_acceptance}".*?execution_percentage: 100',
            )
            for phase_id in ("S15-P1", "S15-P2", "S15-P3"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
                )
            self.assertIn("过期响应", record)
            self.assertIn("S16-P1", record)
            self.assertIn("GitHub", record)

    def test_s16_p1_pending_and_passed_open_only_s16_p2(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S16_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S16_P1_FINAL_VALIDATION",
                "S16-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S16_P1_PASSED",
                "PASSED",
                "GO_TO_S16_P2_ONLY",
                "S16-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S16"',
                    'current_phase_id: "V015_S16_P1_HOMEPAGE_FIRST_SCREEN"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S16-P1-HOMEPAGE-FIRST-SCREEN-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S16-P1-HOMEPAGE-FIRST-SCREEN"',
                    "governance_model_count: 12",
                    "active_formula_count: 377",
                    "active_parameter_count: 2066",
                    'current_parameter_range: "PARAM-KMFA-2434..2451"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's15_stage_review_acceptance_status: "PASSED"',
                    "s16_p1_entry_allowed: false",
                    "s16_p1_started: true",
                    f's16_p1_acceptance_status: "{acceptance}"',
                    f"s16_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s16_p2_started: false",
                    "s16_p3_started: false",
                    "s16_stage_review_started: false",
                    "s17_entry_allowed: false",
                    "s16_p1_summary_metric_count: 5",
                    "s16_p1_source_bound_metric_count: 5",
                    "s16_p1_cutoff_bound_metric_count: 5",
                    "s16_p1_completeness_bound_metric_count: 5",
                    "s16_p1_partial_missing_metric_count: 1",
                    "s16_p1_missing_as_zero_count: 0",
                    "s16_p1_focus_item_count: 5",
                    "s16_p1_primary_action_count: 5",
                    "s16_p1_automatic_execution_count: 0",
                    "s16_p1_trend_series_count: 3",
                    "s16_p1_trend_period_count: 4",
                    "s16_p1_trend_table_alternative_count: 3",
                    "s16_p1_project_portfolio_count: 4",
                    "s16_p1_browser_viewport_count: 2",
                    "s16_p1_browser_flow_count: 6",
                    "s16_p1_visual_evidence_count: 4",
                    "s16_p1_public_check_count: 50",
                    "s16_p1_public_check_failed_count: 0",
                    "s16_p1_raw_root_access_count: 0",
                    "s16_p1_live_source_read_count: 0",
                    "s16_p1_external_network_request_count: 0",
                    "s16_p1_real_identity_count: 0",
                    "s16_p1_credential_count: 0",
                    "s16_p1_real_business_action_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S15".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S16".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S16-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S16P1T01", "S16P1T02", "S16P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("资料不足", record)
            self.assertIn("S16-P2", record)
            self.assertIn("GitHub", record)

    def test_s16_p2_pending_and_passed_open_only_s16_p3(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            ("S16_P2_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S16_P2_FINAL_VALIDATION", "S16-P2-FINAL-VALIDATION", False),
            ("S16_P2_PASSED", "PASSED", "GO_TO_S16_P3_ONLY", "S16-P3", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S16"',
                    'current_phase_id: "V015_S16_P2_DRILLDOWN_EXPLANATION"',
                    'current_task_id: "KMFA-V015-S16-P2-DRILLDOWN-EXPLANATION-20260716"',
                    "active_formula_count: 378",
                    "active_parameter_count: 2084",
                    'current_parameter_range: "PARAM-KMFA-2452..2469"',
                    f'phase_acceptance_status: "{acceptance}"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's16_p1_acceptance_status: "PASSED"',
                    "s16_p2_started: true",
                    f's16_p2_acceptance_status: "{acceptance}"',
                    f"s16_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s16_p3_started: false",
                    "s16_p2_metric_count: 5",
                    "s16_p2_drilldown_route_count: 5",
                    "s16_p2_browser_flow_count: 7",
                    "s16_p2_public_check_count: 78",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S16".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S16-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            self.assertIn("指标下钻", record)
            self.assertIn("S16-P3", record)

    def test_s16_p3_pending_and_passed_open_only_stage_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            ("S16_P3_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S16_P3_FINAL_VALIDATION", "S16-P3-FINAL-VALIDATION", False),
            ("S16_P3_PASSED", "PASSED", "GO_TO_S16_STAGE_REVIEW_ONLY", "S16-STAGE-REVIEW", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S16"',
                    'current_phase_id: "V015_S16_P3_HOMEPAGE_USABILITY_ACCEPTANCE"',
                    'current_task_id: "KMFA-V015-S16-P3-HOMEPAGE-USABILITY-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S16-P3-HOMEPAGE-USABILITY"',
                    "governance_model_count: 12",
                    "active_formula_count: 379",
                    "active_parameter_count: 2102",
                    'current_parameter_range: "PARAM-KMFA-2470..2487"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's16_p2_acceptance_status: "PASSED"',
                    "s16_p3_started: true",
                    f's16_p3_acceptance_status: "{acceptance}"',
                    f"s16_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s16_stage_review_started: false",
                    "s17_entry_allowed: false",
                    "s16_p3_ten_second_case_count: 6",
                    "s16_p3_ten_second_case_pass_count: 6",
                    "s16_p3_ten_second_success_bps: 10000",
                    "s16_p3_ten_second_threshold_bps: 8000",
                    "s16_p3_priority_preview_count: 3",
                    "s16_p3_critical_task_count: 3",
                    "s16_p3_max_critical_task_clicks: 1",
                    "s16_p3_dead_end_count: 0",
                    "s16_p3_fault_state_count: 3",
                    "s16_p3_blank_page_count: 0",
                    "s16_p3_fake_business_value_count: 0",
                    "s16_p3_browser_flow_count: 8",
                    "s16_p3_visual_evidence_count: 5",
                    "s16_p3_public_check_count: 55",
                    "s16_p3_external_human_participant_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S16".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S16-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S16P3T01", "S16P3T02", "S16P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("前三项重点", record)
            self.assertIn("外部真人用户研究", record)

    def test_s16_stage_review_pending_and_passed_open_only_s17_p1(self) -> None:
        for state, acceptance, lifecycle, stage_acceptance, decision, next_gate, s17_entry in (
            (
                "S16_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "IN_PROGRESS",
                "PENDING",
                "REMAIN_IN_S16_STAGE_REVIEW",
                "S16-STAGE-REVIEW-FINAL-VALIDATION",
                False,
            ),
            (
                "S16_STAGE_REVIEW_PASSED",
                "PASSED",
                "COMPLETED",
                "PASSED",
                "GO_TO_S17_P1_ONLY",
                "S17-P1",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S16"',
                    'current_phase_id: "V015_S16_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S16-STAGE-REVIEW-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S16-STAGE-REVIEW"',
                    "governance_model_count: 12",
                    "active_formula_count: 380",
                    "active_parameter_count: 2120",
                    'current_parameter_range: "PARAM-KMFA-2488..2505"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_lifecycle_status: "{lifecycle}"',
                    f'stage_acceptance_status: "{stage_acceptance}"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's16_p3_acceptance_status: "PASSED"',
                    "s16_stage_review_started: true",
                    f"s16_stage_review_performed: {str(s17_entry).lower()}",
                    f's16_stage_review_acceptance_status: "{acceptance}"',
                    f"s17_entry_allowed: {str(s17_entry).lower()}",
                    f"s17_p1_entry_allowed: {str(s17_entry).lower()}",
                    "s17_p1_started: false",
                    "s16_review_predecessor_phase_count: 3",
                    "s16_review_predecessor_task_accepted_count: 9",
                    "s16_review_predecessor_receipt_count: 60",
                    "s16_review_predecessor_public_check_count: 183",
                    "s16_review_integration_binding_count: 45",
                    "s16_review_integration_binding_failed_count: 0",
                    "s16_review_public_check_count: 240",
                    "s16_review_public_check_failed_count: 0",
                    "s16_review_finding_count: 3",
                    "s16_review_fixed_finding_count: 3",
                    "s16_review_open_finding_count: 0",
                    "s16_review_technical_audit_score: 19",
                    "s16_review_browser_viewport_count: 3",
                    "s16_review_browser_flow_count: 10",
                    "s16_review_visual_evidence_count: 5",
                    "s16_review_minimum_ignored_stale_response_count: 1",
                    "s16_review_visible_fault_live_region_count: 1",
                    "s16_review_min_touch_target_px: 44",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S16".*?status: "{lifecycle}".*?acceptance_status: "{stage_acceptance}".*?execution_percentage: 100',
            )
            for phase_id in ("S16-P1", "S16-P2", "S16-P3"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
                )
            self.assertIn("S16 整体复审", record)
            self.assertIn("S17-P1", record)

    def test_s17_p1_pending_and_passed_open_only_s17_p2(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S17_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S17_P1_FINAL_VALIDATION",
                "S17-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S17_P1_PASSED",
                "PASSED",
                "GO_TO_S17_P2_ONLY",
                "S17-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S17"',
                    'current_phase_id: "V015_S17_P1_PROJECT_LIST"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S17-P1-PROJECT-LIST-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S17-P1-PROJECT-LIST"',
                    "governance_model_count: 13",
                    "active_formula_count: 381",
                    "active_parameter_count: 2140",
                    'current_parameter_range: "PARAM-KMFA-2506..2525"',
                    f'phase_acceptance_status: "{acceptance}"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's16_stage_review_acceptance_status: "PASSED"',
                    "s17_p1_started: true",
                    f's17_p1_acceptance_status: "{acceptance}"',
                    f"s17_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s17_p2_started: false",
                    "s17_p3_started: false",
                    "s17_p1_catalog_project_count: 18",
                    "s17_p1_default_visible_column_count: 8",
                    "s17_p1_filter_dimension_count: 7",
                    "s17_p1_hidden_composite_score_count: 0",
                    "s17_p1_export_source_required: true",
                    "s17_p1_fact_layer_write_count: 0",
                    "s17_p1_browser_flow_count: 8",
                    "s17_p1_visual_evidence_count: 4",
                    "s17_p1_public_check_count: 58",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S17".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S17-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for task_id in ("S17P1T01", "S17P1T02", "S17P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("项目总表", record)
            self.assertIn("S17-P2", record)

    def test_s17_p2_pending_and_passed_open_only_s17_p3(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S17_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S17_P2_FINAL_VALIDATION",
                "S17-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S17_P2_PASSED",
                "PASSED",
                "GO_TO_S17_P3_ONLY",
                "S17-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S17"',
                    'current_phase_id: "V015_S17_P2_PROJECT_DETAIL"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S17-P2-PROJECT-DETAIL-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S17-P2-PROJECT-DETAIL"',
                    "governance_model_count: 13",
                    "active_formula_count: 382",
                    "active_parameter_count: 2160",
                    'current_parameter_range: "PARAM-KMFA-2526..2545"',
                    f'phase_acceptance_status: "{acceptance}"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's17_p1_acceptance_status: "PASSED"',
                    "s17_p2_started: true",
                    f's17_p2_acceptance_status: "{acceptance}"',
                    f"s17_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s17_p3_started: false",
                    "s17_p2_detail_tab_count: 5",
                    "s17_p2_cost_category_count: 10",
                    "s17_p2_cost_trend_period_count: 4",
                    "s17_p2_document_count: 6",
                    "s17_p2_money_tolerance_cents: 0",
                    "s17_p2_engine_difference_cents: 0",
                    "s17_p2_chart_table_difference_cents: 0",
                    "s17_p2_section_overlap_count: 0",
                    "s17_p2_return_context_preserved: true",
                    "s17_p2_browser_flow_count: 9",
                    "s17_p2_visual_evidence_count: 5",
                    "s17_p2_public_check_count: 72",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S17".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            for phase_id in ("S17-P1", "S17-P2"):
                expected_acceptance = acceptance if phase_id == "S17-P2" else "PASSED"
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{expected_acceptance}".*?execution_percentage: 100',
                )
            for task_id in ("S17P2T01", "S17P2T02", "S17P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("项目是否赚钱", record)
            self.assertIn("S17-P3", record)

    def test_s17_p3_pending_and_passed_open_only_s17_overall_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S17_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S17_P3_FINAL_VALIDATION",
                "S17-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S17_P3_PASSED",
                "PASSED",
                "GO_TO_S17_OVERALL_REVIEW_ONLY",
                "S17-OVERALL-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S17"',
                    'current_phase_id: "V015_S17_P3_PROJECT_WORKFLOW"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S17-P3-PROJECT-WORKFLOW-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S17-P3-PROJECT-WORKFLOW"',
                    "governance_model_count: 13",
                    "active_formula_count: 383",
                    "active_parameter_count: 2180",
                    'current_parameter_range: "PARAM-KMFA-2546..2565"',
                    f'phase_acceptance_status: "{acceptance}"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's17_p1_acceptance_status: "PASSED"',
                    's17_p2_acceptance_status: "PASSED"',
                    "s17_p3_started: true",
                    f's17_p3_acceptance_status: "{acceptance}"',
                    f"s17_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s17_stage_review_started: false",
                    "s17_p3_candidate_count: 3",
                    "s17_p3_auto_allocation_min_confidence_bps: 9000",
                    "s17_p3_low_confidence_bps: 5200",
                    "s17_p3_source_data_write_count: 0",
                    "s17_p3_fact_layer_write_count: 0",
                    "s17_p3_reversible: true",
                    "s17_p3_variance_source_count: 2",
                    "s17_p3_event_count: 5",
                    "s17_p3_reversal_event_count: 1",
                    "s17_p3_money_tolerance_cents: 0",
                    "s17_p3_projection_difference_cents: 0",
                    "s17_p3_report_format_count: 3",
                    "s17_p3_evidence_group_count: 4",
                    "s17_p3_workbook_sheet_count: 5",
                    "s17_p3_browser_flow_count: 10",
                    "s17_p3_visual_evidence_count: 6",
                    "s17_p3_public_check_count: 69",
                    "s17_p3_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S17".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100',
            )
            for phase_id in ("S17-P1", "S17-P2", "S17-P3"):
                expected_acceptance = acceptance if phase_id == "S17-P3" else "PASSED"
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{expected_acceptance}".*?execution_percentage: 100',
                )
            for task_id in ("S17P3T01", "S17P3T02", "S17P3T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("可撤销", record)
            self.assertIn("S17 整体复审", record)

    def test_s17_stage_review_pending_and_passed_open_only_s18_p1(self) -> None:
        for state, acceptance, lifecycle, stage_acceptance, decision, next_gate, s18_entry in (
            (
                "S17_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "IN_PROGRESS",
                "PENDING",
                "REMAIN_IN_S17_STAGE_REVIEW",
                "S17-STAGE-REVIEW-FINAL-VALIDATION",
                False,
            ),
            (
                "S17_STAGE_REVIEW_PASSED",
                "PASSED",
                "COMPLETED",
                "PASSED",
                "GO_TO_S18_P1_ONLY",
                "S18-P1",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S17"',
                    'current_phase_id: "V015_S17_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S17-STAGE-REVIEW-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S17-STAGE-REVIEW"',
                    "governance_model_count: 13",
                    "active_formula_count: 384",
                    "active_parameter_count: 2200",
                    'current_parameter_range: "PARAM-KMFA-2566..2585"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_lifecycle_status: "{lifecycle}"',
                    f'stage_acceptance_status: "{stage_acceptance}"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's17_p3_acceptance_status: "PASSED"',
                    "s17_stage_review_started: true",
                    f"s17_stage_review_performed: {str(s18_entry).lower()}",
                    f's17_stage_review_acceptance_status: "{acceptance}"',
                    f"s18_entry_allowed: {str(s18_entry).lower()}",
                    f"s18_p1_entry_allowed: {str(s18_entry).lower()}",
                    "s18_p1_started: false",
                    "s17_review_predecessor_phase_count: 3",
                    "s17_review_predecessor_task_accepted_count: 9",
                    "s17_review_predecessor_receipt_count: 60",
                    "s17_review_predecessor_public_check_count: 199",
                    "s17_review_integration_binding_count: 40",
                    "s17_review_integration_binding_failed_count: 0",
                    "s17_review_public_check_count: 253",
                    "s17_review_public_check_failed_count: 0",
                    "s17_review_finding_count: 4",
                    "s17_review_fixed_finding_count: 4",
                    "s17_review_open_finding_count: 0",
                    "s17_review_technical_audit_score: 20",
                    "s17_review_browser_viewport_count: 3",
                    "s17_review_browser_flow_count: 10",
                    "s17_review_visual_evidence_count: 5",
                    "s17_review_money_difference_cents: 0",
                    "s17_review_scope_leak_count: 0",
                    "s17_review_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S17".*?status: "{lifecycle}".*?acceptance_status: "{stage_acceptance}".*?execution_percentage: 100',
            )
            for phase_id in ("S17-P1", "S17-P2", "S17-P3"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
                )
            self.assertIn("S17 整体复审", record)
            self.assertIn("S18-P1", record)

    def test_s18_p1_pending_and_passed_open_only_s18_p2(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            (
                "S18_P1_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S18_P1_FINAL_VALIDATION",
                "S18-P1-FINAL-VALIDATION",
                False,
            ),
            (
                "S18_P1_PASSED",
                "PASSED",
                "GO_TO_S18_P2_ONLY",
                "S18-P2",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S18"',
                    'current_phase_id: "V015_S18_P1_RECEIVABLES_COLLECTIONS"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S18-P1-RECEIVABLES-COLLECTIONS-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S18-P1-RECEIVABLES-COLLECTIONS"',
                    "governance_model_count: 14",
                    "active_formula_count: 385",
                    "active_parameter_count: 2220",
                    'current_parameter_range: "PARAM-KMFA-2586..2605"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's17_stage_review_acceptance_status: "PASSED"',
                    "s18_p1_started: true",
                    f's18_p1_acceptance_status: "{acceptance}"',
                    f"s18_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s18_p2_started: false",
                    "s18_p3_started: false",
                    "s18_p1_source_item_count: 8",
                    "s18_p1_invoice_item_count: 7",
                    "s18_p1_open_receivable_count: 6",
                    "s18_p1_unbilled_item_count: 1",
                    "s18_p1_aging_bucket_count: 5",
                    "s18_p1_priority_component_count: 5",
                    "s18_p1_priority_component_max_total: 107",
                    "s18_p1_high_priority_min_score: 65",
                    "s18_p1_medium_priority_min_score: 40",
                    "s18_p1_evidence_missing_count: 1",
                    "s18_p1_unsupported_recommendation_count: 0",
                    "s18_p1_automatic_customer_contact_count: 0",
                    "s18_p1_group_dimension_count: 4",
                    "s18_p1_group_difference_cents: 0",
                    "s18_p1_cross_company_leak_count: 0",
                    "s18_p1_browser_flow_count: 8",
                    "s18_p1_visual_evidence_count: 5",
                    "s18_p1_public_check_count: 50",
                    "s18_p1_money_tolerance_cents: 0",
                    "s18_p1_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S18".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S18-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            for phase_id in ("S18-P2", "S18-P3"):
                self.assertRegex(
                    generated,
                    rf'(?s)- phase_id: "{phase_id}".*?status: "NOT_STARTED".*?acceptance_status: "PENDING".*?execution_percentage: 0',
                )
            for task_id in ("S18P1T01", "S18P1T02", "S18P1T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("未开票", record)
            self.assertIn("S18-P2", record)

    def test_s18_p2_pending_and_passed_open_only_s18_p3(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            (
                "S18_P2_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S18_P2_FINAL_VALIDATION",
                "S18-P2-FINAL-VALIDATION",
                False,
            ),
            (
                "S18_P2_PASSED",
                "PASSED",
                "GO_TO_S18_P3_ONLY",
                "S18-P3",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S18"',
                    'current_phase_id: "V015_S18_P2_FUNDS_ACCOUNTS"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"',
                    "current_phase_is_taskpack_roadmap_phase: true",
                    "current_task_is_taskpack_roadmap_task: true",
                    'current_task_id: "KMFA-V015-S18-P2-FUNDS-ACCOUNTS-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S18-P2-FUNDS-ACCOUNTS"',
                    "governance_model_count: 15",
                    "active_formula_count: 386",
                    "active_parameter_count: 2240",
                    'current_parameter_range: "PARAM-KMFA-2606..2625"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 67",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's18_p1_acceptance_status: "PASSED"',
                    "s18_p2_started: true",
                    f's18_p2_acceptance_status: "{acceptance}"',
                    f"s18_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s18_p3_started: false",
                    "s18_p2_company_count: 3",
                    "s18_p2_bank_count: 3",
                    "s18_p2_known_account_count: 4",
                    "s18_p2_unknown_account_count: 1",
                    "s18_p2_excluded_unknown_account_count: 1",
                    "s18_p2_account_reconciliation_difference_cents: 0",
                    "s18_p2_bank_reconciliation_difference_cents: 0",
                    "s18_p2_unknown_amount_in_total_cents: 0",
                    "s18_p2_cross_company_leak_count: 0",
                    "s18_p2_forecast_scenario_count: 3",
                    "s18_p2_forecast_period_count: 4",
                    "s18_p2_forecast_presented_as_certainty_count: 0",
                    "s18_p2_assumption_fact_write_count: 0",
                    "s18_p2_scenario_difference_cents: 0",
                    "s18_p2_loan_count: 3",
                    "s18_p2_loan_due_within_90_days_count: 2",
                    "s18_p2_payment_execution_count: 0",
                    "s18_p2_payment_button_count: 0",
                    "s18_p2_browser_flow_count: 8",
                    "s18_p2_visual_evidence_count: 6",
                    "s18_p2_public_check_count: 61",
                    "s18_p2_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                r'(?s)- stage_id: "S18".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67',
            )
            self.assertRegex(
                generated,
                r'(?s)- phase_id: "S18-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                rf'(?s)- phase_id: "S18-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100',
            )
            self.assertRegex(
                generated,
                r'(?s)- phase_id: "S18-P3".*?status: "NOT_STARTED".*?acceptance_status: "PENDING".*?execution_percentage: 0',
            )
            for task_id in ("S18P2T01", "S18P2T02", "S18P2T03"):
                self.assertRegex(
                    generated,
                    rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"',
                )
            self.assertIn("账户", record)
            self.assertIn("资金缺口", record)
            self.assertIn("S18-P3", record)

    def test_s18_p3_pending_and_passed_open_only_s18_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            (
                "S18_P3_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "REMAIN_IN_S18_P3_FINAL_VALIDATION",
                "S18-P3-FINAL-VALIDATION",
                False,
            ),
            (
                "S18_P3_PASSED",
                "PASSED",
                "GO_TO_S18_STAGE_REVIEW_ONLY",
                "S18-STAGE-REVIEW",
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S18"',
                    'current_phase_id: "V015_S18_P3_RELATION_REPORTING"',
                    'current_task_id: "KMFA-V015-S18-P3-RELATION-REPORTING-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S18-P3-RELATION-REPORTING"',
                    "governance_model_count: 16",
                    "active_formula_count: 387",
                    "active_parameter_count: 2260",
                    'current_parameter_range: "PARAM-KMFA-2626..2645"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's18_p2_acceptance_status: "PASSED"',
                    "s18_p3_started: true",
                    f's18_p3_acceptance_status: "{acceptance}"',
                    f"s18_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s18_stage_review_started: false",
                    "s18_p3_project_count: 6",
                    "s18_p3_profit_cash_substitution_count: 0",
                    "s18_p3_scope_limitation_displayed_count: 6",
                    "s18_p3_profit_equation_difference_cents: 0",
                    "s18_p3_cash_occupancy_reconciliation_difference_cents: 0",
                    "s18_p3_alert_count: 5",
                    "s18_p3_alert_type_count: 3",
                    's18_p3_threshold_version: "1.5.0-s18p3-thresholds-v1"',
                    's18_p3_threshold_config_ref: "KMFA/config/v015_s18_p3_alert_thresholds.json"',
                    "s18_p3_thresholds_externalized: true",
                    "s18_p3_full_sensitive_detail_count: 0",
                    "s18_p3_notification_send_count: 0",
                    "s18_p3_report_page_row_count: 6",
                    "s18_p3_report_appendix_row_count: 6",
                    "s18_p3_report_page_export_difference_cents: 0",
                    "s18_p3_degraded_report_test_count: 1",
                    "s18_p3_unverified_numeric_visible_count: 0",
                    "s18_p3_browser_flow_count: 9",
                    "s18_p3_visual_evidence_count: 6",
                    "s18_p3_public_check_count: 76",
                    "s18_p3_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S18".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100')
            for phase_id in ("S18-P1", "S18-P2"):
                self.assertRegex(generated, rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertRegex(generated, rf'(?s)- phase_id: "S18-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100')
            for task_id in ("S18P3T01", "S18P3T02", "S18P3T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("利润", record)
            self.assertIn("未核验", record)
            self.assertIn("S18 整体复审", record)

    def test_s18_stage_review_pending_and_passed_open_only_s19_p1(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s19_entry in (
            (
                "S18_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "PENDING",
                "REMAIN_IN_S18_STAGE_REVIEW",
                "S18-STAGE-REVIEW-FINAL-VALIDATION",
                False,
                False,
            ),
            (
                "S18_STAGE_REVIEW_PASSED",
                "PASSED",
                "PASSED",
                "GO_TO_S19_P1_ONLY",
                "S19-P1",
                True,
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S18"',
                    'current_phase_id: "V015_S18_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S18-STAGE-REVIEW-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S18-STAGE-REVIEW"',
                    "governance_model_count: 16",
                    "active_formula_count: 388",
                    "active_parameter_count: 2280",
                    'current_parameter_range: "PARAM-KMFA-2646..2665"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_acceptance_status: "{stage_status}"',
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s18_stage_review_started: true",
                    f"s18_stage_review_performed: {str(performed).lower()}",
                    f's18_stage_review_acceptance_status: "{acceptance}"',
                    f"s19_entry_allowed: {str(s19_entry).lower()}",
                    f"s19_p1_entry_allowed: {str(s19_entry).lower()}",
                    "s19_p1_started: false",
                    "s18_review_predecessor_phase_count: 3",
                    "s18_review_predecessor_task_accepted_count: 9",
                    "s18_review_predecessor_receipt_count: 60",
                    "s18_review_predecessor_public_check_count: 187",
                    "s18_review_integration_binding_count: 41",
                    "s18_review_public_check_count: 246",
                    "s18_review_finding_count: 2",
                    "s18_review_fixed_finding_count: 2",
                    "s18_review_open_finding_count: 0",
                    "s18_review_money_difference_cents: 0",
                    "s18_review_scope_leak_count: 0",
                    "s18_review_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertIn("旧金额", record)
            self.assertIn("预警", record)
            self.assertIn("S19-P1", record)


    def test_s19_p1_pending_and_passed_open_only_s19_p2(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            ("S19_P1_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S19_P1_FINAL_VALIDATION", "S19-P1-FINAL-VALIDATION", False),
            ("S19_P1_PASSED", "PASSED", "GO_TO_S19_P2_ONLY", "S19-P2", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S19"',
                    'current_phase_id: "V015_S19_P1_TAX_INVOICE_FACTS"',
                    'current_task_id: "KMFA-V015-S19-P1-TAX-INVOICE-FACTS-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S19-P1-TAX-INVOICE-FACTS"',
                    "governance_model_count: 17",
                    "active_formula_count: 389",
                    "active_parameter_count: 2300",
                    'current_parameter_range: "PARAM-KMFA-2666..2685"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 33",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's18_stage_review_acceptance_status: "PASSED"',
                    "s19_p1_started: true",
                    f's19_p1_acceptance_status: "{acceptance}"',
                    f"s19_p2_entry_allowed: {str(p2_entry).lower()}",
                    "s19_p2_started: false",
                    "s19_p1_tax_invoice_fact_count: 8",
                    "s19_p1_matched_count: 4",
                    "s19_p1_review_count: 4",
                    "s19_p1_anomaly_count: 5",
                    "s19_p1_unknown_rate_count: 1",
                    "s19_p1_rate_inference_count: 0",
                    "s19_p1_automatic_tax_adjustment_count: 0",
                    "s19_p1_project_burden_count: 3",
                    "s19_p1_burden_equation_difference_cents: 0",
                    "s19_p1_formal_filing_conclusion_count: 0",
                    "s19_p1_cross_company_leak_count: 0",
                    "s19_p1_browser_flow_count: 7",
                    "s19_p1_visual_evidence_count: 5",
                    "s19_p1_public_check_count: 64",
                    "s19_p1_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S18".*?status: "COMPLETED".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertRegex(generated, r'(?s)- stage_id: "S19".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33')
            self.assertRegex(generated, rf'(?s)- phase_id: "S19-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100')
            for task_id in ("S19P1T01", "S19P1T02", "S19P1T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("未知税率", record)
            self.assertIn("S19-P2", record)

    def test_s19_p3_pending_and_passed_open_only_stage_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            ("S19_P3_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S19_P3_FINAL_VALIDATION", "S19-P3-FINAL-VALIDATION", False),
            ("S19_P3_PASSED", "PASSED", "GO_TO_S19_STAGE_REVIEW_ONLY", "S19-STAGE-REVIEW", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S19"',
                    'current_phase_id: "V015_S19_P3_TAX_POLICY_REPORTING"',
                    'current_task_id: "KMFA-V015-S19-P3-TAX-POLICY-REPORTING-20260716"',
                    'current_acceptance_id: "ACC-KMFA-V015-S19-P3-TAX-POLICY-REPORTING"',
                    "governance_model_count: 19",
                    "active_formula_count: 391",
                    "active_parameter_count: 2340",
                    'current_parameter_range: "PARAM-KMFA-2706..2725"',
                    f'phase_acceptance_status: "{acceptance}"',
                    'stage_lifecycle_status: "IN_PROGRESS"',
                    'stage_acceptance_status: "PENDING"',
                    "stage_execution_percentage: 100",
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    's19_p1_acceptance_status: "PASSED"',
                    's19_p2_acceptance_status: "PASSED"',
                    "s19_p3_started: true",
                    f's19_p3_acceptance_status: "{acceptance}"',
                    f"s19_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s19_stage_review_started: false",
                    "s19_p3_tax_review_invoice_count: 4",
                    "s19_p3_tax_anomaly_count: 5",
                    "s19_p3_tax_unknown_amount_item_count: 1",
                    "s19_p3_tax_alarm_copy_count: 0",
                    "s19_p3_policy_report_count: 3",
                    "s19_p3_policy_category_count: 6",
                    "s19_p3_policy_available_evidence_count: 7",
                    "s19_p3_policy_missing_evidence_count: 3",
                    "s19_p3_policy_review_evidence_count: 2",
                    "s19_p3_professional_review_role_count: 2",
                    "s19_p3_review_basis_count: 12",
                    "s19_p3_formal_filing_conclusion_count: 0",
                    "s19_p3_formal_eligibility_conclusion_count: 0",
                    "s19_p3_recognition_result_promise_count: 0",
                    "s19_p3_unauthorized_review_success_count: 0",
                    "s19_p3_cross_company_review_leak_count: 0",
                    "s19_p3_review_event_update_count: 0",
                    "s19_p3_review_event_delete_count: 0",
                    "s19_p3_browser_flow_count: 8",
                    "s19_p3_visual_evidence_count: 6",
                    "s19_p3_public_check_count: 72",
                    "s19_p3_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S19".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100')
            self.assertRegex(generated, rf'(?s)- phase_id: "S19-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100')
            for task_id in ("S19P3T01", "S19P3T02", "S19P3T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("普通中文", record)
            self.assertIn("S19 整体复审", record)

    def test_s19_stage_review_pending_and_passed_open_only_s20_p1(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s20_entry in (
            (
                "S19_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "PENDING",
                "REMAIN_IN_S19_STAGE_REVIEW",
                "S19-STAGE-REVIEW-FINAL-VALIDATION",
                False,
                False,
            ),
            (
                "S19_STAGE_REVIEW_PASSED",
                "PASSED",
                "PASSED",
                "GO_TO_S20_P1_ONLY",
                "S20-P1",
                True,
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S19"',
                    'current_phase_id: "V015_S19_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S19-STAGE-REVIEW-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S19-STAGE-REVIEW"',
                    "governance_model_count: 19",
                    "active_formula_count: 392",
                    "active_parameter_count: 2360",
                    'current_parameter_range: "PARAM-KMFA-2726..2745"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_acceptance_status: "{stage_status}"',
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s19_stage_review_started: true",
                    f"s19_stage_review_performed: {str(performed).lower()}",
                    f's19_stage_review_acceptance_status: "{acceptance}"',
                    f"s20_entry_allowed: {str(s20_entry).lower()}",
                    f"s20_p1_entry_allowed: {str(s20_entry).lower()}",
                    "s20_p1_started: false",
                    "product_implementation_allowed: false",
                    "s19_review_predecessor_phase_count: 3",
                    "s19_review_predecessor_task_accepted_count: 9",
                    "s19_review_predecessor_receipt_count: 60",
                    "s19_review_predecessor_public_check_count: 216",
                    "s19_review_integration_binding_count: 44",
                    "s19_review_integration_binding_failed_count: 0",
                    "s19_review_public_check_count: 278",
                    "s19_review_public_check_failed_count: 0",
                    "s19_review_finding_count: 2",
                    "s19_review_fixed_finding_count: 2",
                    "s19_review_open_finding_count: 0",
                    "s19_review_technical_audit_score: 20",
                    "s19_review_browser_viewport_count: 3",
                    "s19_review_browser_flow_count: 8",
                    "s19_review_visual_evidence_count: 5",
                    "s19_review_navigation_dead_end_count: 0",
                    "s19_review_tampered_event_accept_count: 0",
                    "s19_review_scope_leak_count: 0",
                    "s19_review_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S19".*?status: "{"COMPLETED" if performed else "IN_PROGRESS"}".*?acceptance_status: "{stage_status}".*?execution_percentage: 100',
            )
            self.assertIn("专业复核", record)
            self.assertIn("S20", record)

    def test_s20_p2_pending_and_passed_open_only_s20_p3(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            ("S20_P2_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S20_P2_FINAL_VALIDATION", "S20-P2-FINAL-VALIDATION", False),
            ("S20_P2_PASSED", "PASSED", "GO_TO_S20_P3_ONLY", "S20-P3", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S20"',
                    'current_phase_id: "V015_S20_P2_CONFIRMATION_WORKBENCH"',
                    'current_task_id: "KMFA-V015-S20-P2-CONFIRMATION-WORKBENCH-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S20-P2-CONFIRMATION-WORKBENCH"',
                    "governance_model_count: 19", "active_formula_count: 394", "active_parameter_count: 2400",
                    'current_parameter_range: "PARAM-KMFA-2766..2785"', "stage_execution_percentage: 67",
                    f'phase_acceptance_status: "{acceptance}"', f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's20_p1_acceptance_status: "PASSED"', "s20_p2_started: true",
                    f's20_p2_acceptance_status: "{acceptance}"', f"s20_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s20_p3_started: false", "s20_p2_business_issue_count: 6", "s20_p2_default_issue_count: 5",
                    "s20_p2_governance_log_count_in_main_list: 0", "s20_p2_detail_count: 5",
                    "s20_p2_high_impact_without_preview_success_count: 0", "s20_p2_raw_source_fact_mutation_count: 0",
                    "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S20".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67')
            self.assertRegex(generated, rf'(?s)- phase_id: "S20-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("人工确认", record)
            self.assertIn("S20-P3", record)

    def test_s20_p3_pending_and_passed_open_only_s20_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            ("S20_P3_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S20_P3_FINAL_VALIDATION", "S20-P3-FINAL-VALIDATION", False),
            ("S20_P3_PASSED", "PASSED", "GO_TO_S20_STAGE_REVIEW_ONLY", "S20-STAGE-REVIEW", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S20"',
                    'current_phase_id: "V015_S20_P3_RECALCULATION_PUBLICATION"',
                    'current_task_id: "KMFA-V015-S20-P3-RECALCULATION-PUBLICATION-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S20-P3-RECALCULATION-PUBLICATION"',
                    "governance_model_count: 19", "active_formula_count: 395", "active_parameter_count: 2420",
                    'current_parameter_range: "PARAM-KMFA-2786..2805"', "stage_execution_percentage: 100",
                    f'phase_acceptance_status: "{acceptance}"', f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's20_p2_acceptance_status: "PASSED"', "s20_p3_started: true",
                    f's20_p3_acceptance_status: "{acceptance}"', f"s20_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s20_stage_review_started: false", "s20_p3_impact_graph_node_count: 16",
                    "s20_p3_impact_graph_edge_count: 18", "s20_p3_synchronized_view_count: 4",
                    "s20_p3_difference_explanation_missing_count: 0", "s20_p3_public_check_count: 63",
                    "s20_p3_browser_flow_count: 8", "s20_p3_visual_evidence_count: 6",
                    "s20_p3_raw_source_unrelated_mutation_count: 0", "s20_p3_external_release_count: 0",
                    "s20_p3_cross_page_mismatch_publish_success_count: 0",
                    "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S20".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100')
            self.assertRegex(generated, rf'(?s)- phase_id: "S20-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("重算", record)
            self.assertIn("S20", record)

    def test_s20_stage_review_pending_and_passed_open_only_s21_p1(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s21_entry in (
            (
                "S20_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
                "PENDING_FINAL_VALIDATION",
                "PENDING",
                "REMAIN_IN_S20_STAGE_REVIEW",
                "S20-STAGE-REVIEW-FINAL-VALIDATION",
                False,
                False,
            ),
            (
                "S20_STAGE_REVIEW_PASSED",
                "PASSED",
                "PASSED",
                "GO_TO_S21_P1_ONLY",
                "S21-P1",
                True,
                True,
            ),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S20"',
                    'current_phase_id: "V015_S20_STAGE_REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false",
                    "current_task_is_taskpack_roadmap_task: false",
                    'current_task_id: "KMFA-V015-S20-STAGE-REVIEW-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S20-STAGE-REVIEW"',
                    "governance_model_count: 19",
                    "active_formula_count: 396",
                    "active_parameter_count: 2440",
                    'current_parameter_range: "PARAM-KMFA-2806..2825"',
                    f'phase_acceptance_status: "{acceptance}"',
                    f'stage_acceptance_status: "{stage_status}"',
                    f'decision: "{decision}"',
                    f'next_gate_id: "{next_gate}"',
                    "s20_stage_review_started: true",
                    f"s20_stage_review_performed: {str(performed).lower()}",
                    f's20_stage_review_acceptance_status: "{acceptance}"',
                    f"s21_entry_allowed: {str(s21_entry).lower()}",
                    f"s21_p1_entry_allowed: {str(s21_entry).lower()}",
                    "s21_p1_started: false",
                    "product_implementation_allowed: false",
                    "s20_review_predecessor_phase_count: 3",
                    "s20_review_predecessor_task_accepted_count: 9",
                    "s20_review_predecessor_receipt_count: 60",
                    "s20_review_predecessor_public_check_count: 177",
                    "s20_review_integration_binding_count: 44",
                    "s20_review_integration_binding_failed_count: 0",
                    "s20_review_public_check_count: 239",
                    "s20_review_public_check_failed_count: 0",
                    "s20_review_finding_count: 2",
                    "s20_review_fixed_finding_count: 2",
                    "s20_review_open_finding_count: 0",
                    "s20_review_technical_audit_score: 20",
                    "s20_review_browser_viewport_count: 3",
                    "s20_review_browser_flow_count: 8",
                    "s20_review_visual_evidence_count: 5",
                    "s20_review_navigation_dead_end_count: 0",
                    "s20_review_cross_journal_mismatch_accept_count: 0",
                    "s20_review_scope_leak_count: 0",
                    "s20_review_raw_root_access_count: 0",
                    "github_upload_performed: false",
                    "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(
                generated,
                rf'(?s)- stage_id: "S20".*?status: "{"COMPLETED" if performed else "IN_PROGRESS"}".*?acceptance_status: "{stage_status}".*?execution_percentage: 100',
            )
            self.assertIn("人工确认", record)
            self.assertIn("S21", record)

    def test_s21_p2_pending_and_passed_open_only_s21_p3(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            ("S21_P2_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S21_P2_FINAL_VALIDATION", "S21-P2-FINAL-VALIDATION", False),
            ("S21_P2_PASSED", "PASSED", "GO_TO_S21_P3_ONLY", "S21-P3", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S21"', 'current_phase_id: "V015_S21_P2_REPORT_GENERATION"',
                    'current_task_id: "KMFA-V015-S21-P2-REPORT-GENERATION-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S21-P2-REPORT-GENERATION"',
                    "governance_model_count: 19", "active_formula_count: 398", "active_parameter_count: 2480",
                    'current_parameter_range: "PARAM-KMFA-2846..2865"', "stage_execution_percentage: 67",
                    f'phase_acceptance_status: "{acceptance}"', f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's21_p1_acceptance_status: "PASSED"', "s21_p2_started: true",
                    f's21_p2_acceptance_status: "{acceptance}"', f"s21_p3_entry_allowed: {str(p3_entry).lower()}",
                    "s21_p3_started: false", "s21_p2_format_count: 3", "s21_p2_exact_numeric_value_count: 21",
                    "s21_p2_cross_format_difference_integer: 0", "s21_p2_public_check_count: 60",
                    "s21_p2_browser_flow_count: 8", "s21_p2_browser_visual_evidence_count: 5",
                    "s21_p2_pdf_visual_evidence_count: 2", "s21_p2_raw_root_access_count: 0",
                    "s21_p2_approval_publication_count: 0", "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S21".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67')
            for phase_id in ("S21-P1", "S21-P2"):
                expected_acceptance = acceptance if phase_id == "S21-P2" else "PASSED"
                self.assertRegex(generated, rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{expected_acceptance}".*?execution_percentage: 100')
            for task_id in ("S21P2T01", "S21P2T02", "S21P2T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("网页", record)
            self.assertIn("PDF", record)

    def test_s21_p3_pending_and_passed_open_only_stage_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            ("S21_P3_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S21_P3_FINAL_VALIDATION", "S21-P3-FINAL-VALIDATION", False),
            ("S21_P3_PASSED", "PASSED", "GO_TO_S21_STAGE_REVIEW_ONLY", "S21-STAGE-REVIEW", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S21"', 'current_phase_id: "V015_S21_P3_REPORT_WORKFLOW"',
                    'current_task_id: "KMFA-V015-S21-P3-REPORT-WORKFLOW-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S21-P3-REPORT-WORKFLOW"',
                    "governance_model_count: 19", "active_formula_count: 399", "active_parameter_count: 2500",
                    'current_parameter_range: "PARAM-KMFA-2866..2885"', "stage_execution_percentage: 100",
                    f'phase_acceptance_status: "{acceptance}"', f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's21_p1_acceptance_status: "PASSED"', 's21_p2_acceptance_status: "PASSED"',
                    "s21_p3_started: true", f's21_p3_acceptance_status: "{acceptance}"',
                    f"s21_stage_review_entry_allowed: {str(review_entry).lower()}", "s21_stage_review_started: false",
                    "s22_entry_allowed: false", "s22_p1_started: false", "s21_p3_workflow_action_count: 5",
                    "s21_p3_quality_gate_check_count: 15", "s21_p3_unexplained_difference_count: 0",
                    "s21_p3_report_center_filter_count: 6", "s21_p3_internal_publication_count: 1",
                    "s21_p3_public_link_count: 0", "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S21".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100')
            for phase_id in ("S21-P1", "S21-P2", "S21-P3"):
                expected_acceptance = acceptance if phase_id == "S21-P3" else "PASSED"
                self.assertRegex(generated, rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{expected_acceptance}".*?execution_percentage: 100')
            for task_id in ("S21P3T01", "S21P3T02", "S21P3T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("报告中心", record)
            self.assertIn("整体复审", record)

    def test_s21_stage_review_pending_and_passed_open_only_s22_p1(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s22_entry in (
            ("S21_STAGE_REVIEW_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "PENDING", "REMAIN_IN_S21_STAGE_REVIEW_FINAL_VALIDATION", "S21-STAGE-REVIEW-FINAL-VALIDATION", False, False),
            ("S21_STAGE_REVIEW_PASSED", "PASSED", "PASSED", "GO_TO_S22_P1_ONLY", "S22-P1", True, True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S21"', 'current_phase_id: "V015_S21_STAGE_REVIEW"',
                    'current_task_id: "KMFA-V015-S21-STAGE-REVIEW-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S21-STAGE-REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false", "current_task_is_taskpack_roadmap_task: false",
                    "governance_model_count: 19", "active_formula_count: 400", "active_parameter_count: 2520",
                    'current_parameter_range: "PARAM-KMFA-2886..2905"', "stage_execution_percentage: 100",
                    f'phase_acceptance_status: "{acceptance}"', f'stage_acceptance_status: "{stage_status}"',
                    f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's21_p1_acceptance_status: "PASSED"', 's21_p2_acceptance_status: "PASSED"', 's21_p3_acceptance_status: "PASSED"',
                    "s21_stage_review_started: true", f"s21_stage_review_performed: {str(performed).lower()}",
                    f"s22_entry_allowed: {str(s22_entry).lower()}", f"s22_p1_entry_allowed: {str(s22_entry).lower()}", "s22_p1_started: false",
                    "s21_review_predecessor_receipt_count: 60", "s21_review_predecessor_public_check_count: 168",
                    "s21_review_integration_binding_count: 44", "s21_review_integration_binding_failed_count: 0",
                    "s21_review_finding_count: 3", "s21_review_open_finding_count: 0",
                    "s21_review_filter_missing_count: 0", "s21_review_selected_case_mismatch_count: 0",
                    "s21_review_raw_external_release_count: 0", "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, rf'(?s)- stage_id: "S21".*?status: "{"COMPLETED" if s22_entry else "IN_PROGRESS"}".*?acceptance_status: "{stage_status}".*?execution_percentage: 100')
            for phase_id in ("S21-P1", "S21-P2", "S21-P3"):
                self.assertRegex(generated, rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertIn("44 项跨部分连接", record)
            self.assertIn("S22", record)

    def test_s22_p1_pending_and_passed_open_only_s22_p2(self) -> None:
        for state, acceptance, decision, next_gate, p2_entry in (
            ("S22_P1_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S22_P1_FINAL_VALIDATION", "S22-P1-FINAL-VALIDATION", False),
            ("S22_P1_PASSED", "PASSED", "GO_TO_S22_P2_ONLY", "S22-P2", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S22"', 'current_phase_id: "V015_S22_P1_NOTIFICATIONS"',
                    'current_task_id: "KMFA-V015-S22-P1-NOTIFICATIONS-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S22-P1-NOTIFICATIONS"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"', "governance_model_count: 20",
                    "active_formula_count: 401", "active_parameter_count: 2540",
                    'current_parameter_range: "PARAM-KMFA-2906..2925"', "stage_execution_percentage: 33",
                    f'phase_acceptance_status: "{acceptance}"', f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    "s22_p1_started: true", f's22_p1_acceptance_status: "{acceptance}"',
                    f"s22_p2_entry_allowed: {str(p2_entry).lower()}", "s22_p2_started: false", "s22_p3_started: false",
                    "s22_p1_rule_catalog_count: 7", "s22_p1_enabled_confirmed_rule_count: 6",
                    "s22_p1_unconfirmed_rule_enabled_count: 0", "s22_p1_alert_category_count: 5",
                    "s22_p1_public_check_count: 65", "s22_p1_browser_flow_count: 8",
                    "s22_p1_raw_external_release_count: 0", "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S22".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 33')
            self.assertRegex(generated, rf'(?s)- phase_id: "S22-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100')
            for task_id in ("S22P1T01", "S22P1T02", "S22P1T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("本地邮件沙箱", record)
            self.assertIn("S22-P2", record)

    def test_s22_p2_pending_and_passed_open_only_s22_p3(self) -> None:
        for state, acceptance, decision, next_gate, p3_entry in (
            ("S22_P2_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S22_P2_FINAL_VALIDATION", "S22-P2-FINAL-VALIDATION", False),
            ("S22_P2_PASSED", "PASSED", "GO_TO_S22_P3_ONLY", "S22-P3", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S22"', 'current_phase_id: "V015_S22_P2_SECURITY_AUDIT"',
                    'current_task_id: "KMFA-V015-S22-P2-SECURITY-AUDIT-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S22-P2-SECURITY-AUDIT"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"', "governance_model_count: 21",
                    "active_formula_count: 402", "active_parameter_count: 2560",
                    'current_parameter_range: "PARAM-KMFA-2926..2945"', "stage_execution_percentage: 67",
                    f'phase_acceptance_status: "{acceptance}"', f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's22_p1_acceptance_status: "PASSED"', "s22_p2_started: true", f's22_p2_acceptance_status: "{acceptance}"',
                    f"s22_p3_entry_allowed: {str(p3_entry).lower()}", "s22_p3_started: false",
                    "s22_p2_role_count: 4", "s22_p2_required_audit_action_type_count: 5",
                    "s22_p2_audit_action_type_count: 6", "s22_p2_audit_event_count: 10",
                    "s22_p2_secret_reference_count: 2", "s22_p2_credential_exposure_count: 0",
                    "s22_p2_attack_category_count: 5", "s22_p2_rejected_attack_count: 5",
                    "s22_p2_high_vulnerability_count: 0", "s22_p2_public_check_count: 60",
                    "s22_p2_browser_flow_count: 9", "s22_p2_raw_external_release_count: 0",
                    "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S22".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 67')
            self.assertRegex(generated, r'(?s)- phase_id: "S22-P1".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertRegex(generated, rf'(?s)- phase_id: "S22-P2".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100')
            for task_id in ("S22P2T01", "S22P2T02", "S22P2T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("审计链", record)
            self.assertIn("S22-P3", record)

    def test_s22_p3_pending_and_passed_open_only_stage_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            ("S22_P3_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S22_P3_FINAL_VALIDATION", "S22-P3-FINAL-VALIDATION", False),
            ("S22_P3_PASSED", "PASSED", "GO_TO_S22_STAGE_REVIEW_ONLY", "S22-STAGE-REVIEW", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S22"', 'current_phase_id: "V015_S22_P3_OPERATIONS_GOVERNANCE"',
                    'current_task_id: "KMFA-V015-S22-P3-OPERATIONS-GOVERNANCE-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S22-P3-OPERATIONS-GOVERNANCE"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"', "governance_model_count: 22",
                    "active_formula_count: 403", "active_parameter_count: 2580",
                    'current_parameter_range: "PARAM-KMFA-2946..2965"', "stage_execution_percentage: 100",
                    f'phase_acceptance_status: "{acceptance}"', f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's22_p1_acceptance_status: "PASSED"', 's22_p2_acceptance_status: "PASSED"',
                    "s22_p3_started: true", f's22_p3_acceptance_status: "{acceptance}"',
                    f"s22_stage_review_entry_allowed: {str(review_entry).lower()}",
                    "s22_stage_review_started: false", "s22_stage_review_performed: false",
                    "s23_entry_allowed: false", "s23_started: false",
                    "s22_p3_service_count: 6", "s22_p3_monitored_service_count: 6",
                    "s22_p3_unmonitored_service_count: 0", "s22_p3_health_failure_detected_count: 1",
                    "s22_p3_backup_dataset_type_count: 3", "s22_p3_restore_difference_count: 0",
                    "s22_p3_restore_permission_difference_count: 0", "s22_p3_backup_tamper_accept_count: 0",
                    "s22_p3_migration_surface_count: 4", "s22_p3_migration_idempotent_noop_count: 1",
                    "s22_p3_migration_rollback_difference_count: 0",
                    "s22_p3_irreversible_without_approval_accept_count: 0",
                    "s22_p3_public_check_count: 62", "s22_p3_raw_external_release_count: 0",
                    "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, r'(?s)- stage_id: "S22".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100')
            for phase_id in ("S22-P1", "S22-P2"):
                self.assertRegex(generated, rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertRegex(generated, rf'(?s)- phase_id: "S22-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100')
            for task_id in ("S22P3T01", "S22P3T02", "S22P3T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("零差异恢复", record)
            self.assertIn("S22 总体复审", record)

    def test_s22_stage_review_pending_and_passed_open_only_s23_p1(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s23_entry in (
            ("S22_STAGE_REVIEW_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "PENDING", "REMAIN_IN_S22_STAGE_REVIEW_FINAL_VALIDATION", "S22-STAGE-REVIEW-FINAL-VALIDATION", False, False),
            ("S22_STAGE_REVIEW_PASSED", "PASSED", "PASSED", "GO_TO_S23_P1_ONLY", "S23-P1", True, True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S22"', 'current_phase_id: "V015_S22_STAGE_REVIEW"',
                    'current_task_id: "KMFA-V015-S22-STAGE-REVIEW-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S22-STAGE-REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false", "current_task_is_taskpack_roadmap_task: false",
                    "governance_model_count: 22", "active_formula_count: 404", "active_parameter_count: 2600",
                    'current_parameter_range: "PARAM-KMFA-2966..2985"', "stage_execution_percentage: 100",
                    f'phase_acceptance_status: "{acceptance}"', f'stage_acceptance_status: "{stage_status}"',
                    f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's22_p1_acceptance_status: "PASSED"', 's22_p2_acceptance_status: "PASSED"', 's22_p3_acceptance_status: "PASSED"',
                    "s22_stage_review_started: true", f"s22_stage_review_performed: {str(performed).lower()}",
                    f"s23_entry_allowed: {str(s23_entry).lower()}", f"s23_p1_entry_allowed: {str(s23_entry).lower()}", "s23_p1_started: false",
                    "s22_review_predecessor_receipt_count: 60", "s22_review_predecessor_public_check_count: 187",
                    "s22_review_integration_binding_count: 48", "s22_review_integration_binding_failed_count: 0",
                    "s22_review_finding_count: 4", "s22_review_open_finding_count: 0",
                    "s22_review_unauthenticated_notification_accept_count: 0",
                    "s22_review_unauthenticated_audit_detail_count: 0", "s22_review_static_backup_source_count: 0",
                    "s22_review_operations_audit_missing_count: 0", "s22_review_navigation_dead_end_count: 0",
                    "s22_review_raw_external_release_count: 0", "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, rf'(?s)- stage_id: "S22".*?status: "{"COMPLETED" if s23_entry else "IN_PROGRESS"}".*?acceptance_status: "{stage_status}".*?execution_percentage: 100')
            for phase_id in ("S22-P1", "S22-P2", "S22-P3"):
                self.assertRegex(generated, rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertIn("48 项跨部分连接", record)
            self.assertIn("S23", record)

    def test_s23_p3_pending_and_passed_open_only_stage_review(self) -> None:
        for state, acceptance, decision, next_gate, review_entry in (
            ("S23_P3_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "REMAIN_IN_S23_P3_FINAL_VALIDATION", "S23-P3-FINAL-VALIDATION", False),
            ("S23_P3_PASSED", "PASSED", "GO_TO_S23_STAGE_REVIEW_ONLY", "S23-STAGE-REVIEW", True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S23"', 'current_phase_id: "V015_S23_P3_STABILITY_USABILITY"',
                    'current_task_id: "KMFA-V015-S23-P3-STABILITY-USABILITY-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S23-P3-STABILITY-USABILITY"',
                    'current_phase_kind: "TASKPACK_ROADMAP_PHASE"', "governance_model_count: 25",
                    "active_formula_count: 407", "active_parameter_count: 2660",
                    'current_parameter_range: "PARAM-KMFA-3026..3045"', "stage_execution_percentage: 100",
                    f'phase_acceptance_status: "{acceptance}"', f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            for token in (
                's23_p1_acceptance_status: "PASSED"', 's23_p2_acceptance_status: "PASSED"',
                "s23_p3_started: true", f's23_p3_acceptance_status: "{acceptance}"',
                f"s23_stage_review_entry_allowed: {str(review_entry).lower()}", "s23_stage_review_started: false",
                "s24_entry_allowed: false", "s24_started: false", "s23_p3_soak_cycle_count: 12",
                "s23_p3_silent_error_count: 0", "s23_p3_usability_task_count: 3",
                "s23_p3_accessibility_check_count: 34", "s23_p3_accessibility_fail_count: 0",
                "s23_p3_raw_external_release_count: 0",
            ):
                self.assertIn(token, header)
            self.assertRegex(generated, r'(?s)- stage_id: "S23".*?status: "IN_PROGRESS".*?acceptance_status: "PENDING".*?execution_percentage: 100')
            for phase_id in ("S23-P1", "S23-P2"):
                self.assertRegex(generated, rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertRegex(generated, rf'(?s)- phase_id: "S23-P3".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}".*?execution_percentage: 100')
            for task_id in ("S23P3T01", "S23P3T02", "S23P3T03"):
                self.assertRegex(generated, rf'(?s)- task_id: "{task_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "{acceptance}"')
            self.assertIn("真实浸泡", record)
            self.assertIn("S23 总体复审", record)

    def test_s23_stage_review_pending_and_passed_open_only_s24_p1(self) -> None:
        for state, acceptance, stage_status, decision, next_gate, performed, s24_entry in (
            ("S23_STAGE_REVIEW_PENDING_FINAL_VALIDATION", "PENDING_FINAL_VALIDATION", "PENDING", "REMAIN_IN_S23_STAGE_REVIEW_FINAL_VALIDATION", "S23-STAGE-REVIEW-FINAL-VALIDATION", False, False),
            ("S23_STAGE_REVIEW_PASSED", "PASSED", "PASSED", "GO_TO_S24_P1_ONLY", "S24-P1", True, True),
        ):
            roadmap, record = self._rendered(state)
            header = roadmap.split(YAML_START, 1)[0]
            generated = roadmap.split(YAML_START, 1)[1].split(YAML_END, 1)[0]
            for text in (header, generated):
                for token in (
                    'current_stage_id: "S23"', 'current_phase_id: "V015_S23_STAGE_REVIEW"',
                    'current_task_id: "KMFA-V015-S23-STAGE-REVIEW-20260717"',
                    'current_acceptance_id: "ACC-KMFA-V015-S23-STAGE-REVIEW"',
                    'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                    "current_phase_is_taskpack_roadmap_phase: false", "current_task_is_taskpack_roadmap_task: false",
                    "governance_model_count: 25", "active_formula_count: 408", "active_parameter_count: 2680",
                    'current_parameter_range: "PARAM-KMFA-3046..3065"', "stage_execution_percentage: 100",
                    f'phase_acceptance_status: "{acceptance}"', f'stage_acceptance_status: "{stage_status}"',
                    f'decision: "{decision}"', f'next_gate_id: "{next_gate}"',
                    's23_p1_acceptance_status: "PASSED"', 's23_p2_acceptance_status: "PASSED"', 's23_p3_acceptance_status: "PASSED"',
                    "s23_stage_review_started: true", f"s23_stage_review_performed: {str(performed).lower()}",
                    f"s24_entry_allowed: {str(s24_entry).lower()}", f"s24_p1_entry_allowed: {str(s24_entry).lower()}",
                    "s24_started: false", "s24_p1_started: false",
                    "s23_review_predecessor_receipt_count: 60", "s23_review_predecessor_public_check_count: 156",
                    "s23_review_integration_binding_count: 40", "s23_review_integration_binding_failed_count: 0",
                    "s23_review_finding_count: 2", "s23_review_open_finding_count: 0",
                    "s23_review_business_target_assertion_count: 11", "s23_review_business_target_assertion_fail_count: 0",
                    "s23_review_known_limitation_count: 2", "s23_review_raw_external_release_count: 0",
                    "github_upload_performed: false", "app_reinstall_performed: false",
                ):
                    self.assertIn(token, text)
            self.assertRegex(generated, rf'(?s)- stage_id: "S23".*?status: "{"COMPLETED" if s24_entry else "IN_PROGRESS"}".*?acceptance_status: "{stage_status}".*?execution_percentage: 100')
            for phase_id in ("S23-P1", "S23-P2", "S23-P3"):
                self.assertRegex(generated, rf'(?s)- phase_id: "{phase_id}".*?status: "EXECUTION_COMPLETE".*?acceptance_status: "PASSED".*?execution_percentage: 100')
            self.assertIn("40 项跨部分连接", record)
            self.assertIn("S24", record)

    def test_source_manifest_stays_exact(self) -> None:
        outputs = expected_outputs(SOURCE_PACKAGE, validation_state="PENDING_FINAL_VALIDATION")
        manifest = json.loads(next(value for path, value in outputs.items() if path.name == "source_manifest.json"))
        self.assertEqual((manifest["stage_count"], manifest["phase_count"], manifest["task_count"]), (24, 72, 216))


if __name__ == "__main__":
    unittest.main()
