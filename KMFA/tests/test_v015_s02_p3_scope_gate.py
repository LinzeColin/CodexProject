import copy
import unittest

from KMFA.tools.v015_s02_p3_scope_gate import (
    BUSINESS_LINE_PATH,
    DEFAULT_SOURCE_PACKAGE,
    REQUIREMENTS_PATH,
    SCOPE_LOCK_PATH,
    build_change_control_protocol,
    build_prohibited_action_rows,
    build_scope_priority_rows,
    evaluate_change_record,
    load_s02_p3_task_contract,
    validate_change_control_protocol,
    validate_prohibited_action_rows,
    validate_scope_priority_rows,
)


class TestV015S02P3ScopeGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.task_contract = load_s02_p3_task_contract(DEFAULT_SOURCE_PACKAGE)
        cls.scope_rows = build_scope_priority_rows(
            REQUIREMENTS_PATH,
            BUSINESS_LINE_PATH,
            SCOPE_LOCK_PATH,
        )
        cls.prohibited_rows = build_prohibited_action_rows(BUSINESS_LINE_PATH)
        cls.protocol = build_change_control_protocol()

    def test_source_contract_is_exact(self) -> None:
        self.assertEqual(
            list(self.task_contract),
            ["S02P3T01", "S02P3T02", "S02P3T03"],
        )
        self.assertEqual(
            [row["name"] for row in self.task_contract.values()],
            ["锁定 P0/P1/P2 范围", "锁定禁止事项", "建立变更控制"],
        )
        self.assertEqual(
            self.task_contract["S02P3T03"]["stop"],
            "未登记变更不得合并。",
        )

    def test_scope_priority_table_covers_all_explicit_priority_objects(self) -> None:
        self.assertEqual(len(self.scope_rows), 103)
        counts: dict[tuple[str, str], int] = {}
        for row in self.scope_rows:
            key = (row["scope_item_type"], row["priority"])
            counts[key] = counts.get(key, 0) + 1
        self.assertEqual(
            counts,
            {
                ("REQUIREMENT", "P0"): 46,
                ("REQUIREMENT", "P1"): 8,
                ("REQUIREMENT", "P2"): 1,
                ("BUSINESS_LINE", "P0"): 1,
                ("BUSINESS_LINE", "P1"): 7,
                ("BUSINESS_LINE", "P2"): 2,
                ("CAPABILITY", "NA"): 37,
                ("POLICY", "NA"): 1,
            },
        )
        self.assertTrue(
            all(row["change_control_required"] for row in self.scope_rows)
        )
        self.assertTrue(
            all(not row["time_pressure_quality_tradeoff_allowed"] for row in self.scope_rows)
        )
        self.assertTrue(
            all(not row["implementation_authorized_by_s02_p3"] for row in self.scope_rows)
        )
        self.assertEqual(validate_scope_priority_rows(self.scope_rows), [])

    def test_scope_priority_special_routes_remain_deferred_without_omission(self) -> None:
        by_id = {row["scope_item_id"]: row for row in self.scope_rows}
        self.assertEqual(by_id["R004"]["delivery_route"], "V15_PROJECT_COST_FIRST")
        self.assertEqual(by_id["R018"]["delivery_route"], "V15_FILE_IMPORT_FIRST_AUTOMATION_LATER")
        self.assertEqual(by_id["R052"]["delivery_route"], "POST_STABILITY_SEPARATE_CONNECTOR")
        self.assertEqual(by_id["R053"]["delivery_route"], "FUTURE_SEPARATE_INITIATIVE")
        self.assertEqual(by_id["R054"]["delivery_route"], "POST_STABILITY_LOW_COUPLING_INTEGRATION")
        self.assertEqual(by_id["BL-01"]["delivery_route"], "V15_PROJECT_COST_FIRST")
        self.assertEqual(by_id["CAP-037"]["delivery_route"], "POST_STABILITY_SEPARATE_CONNECTOR")
        self.assertEqual(
            by_id["DEFERRED-POLICY-CONTRACT-SCANNING"]["delivery_route"],
            "FUTURE_SEPARATE_CONTRACT_SCANNING",
        )
        self.assertTrue(by_id["R053"]["in_scope_registry"])

    def test_scope_priority_validator_fails_closed(self) -> None:
        duplicate = copy.deepcopy(self.scope_rows)
        duplicate.append(copy.deepcopy(duplicate[0]))
        self.assertTrue(validate_scope_priority_rows(duplicate))

        quality_tradeoff = copy.deepcopy(self.scope_rows)
        quality_tradeoff[0]["time_pressure_quality_tradeoff_allowed"] = True
        self.assertTrue(validate_scope_priority_rows(quality_tradeoff))

        priority_swap = copy.deepcopy(self.scope_rows)
        first = next(row for row in priority_swap if row["scope_item_id"] == "R001")
        second = next(row for row in priority_swap if row["scope_item_id"] == "R018")
        first["priority"], second["priority"] = second["priority"], first["priority"]
        self.assertTrue(validate_scope_priority_rows(priority_swap))

    def test_prohibited_actions_cover_explicit_and_business_line_boundaries(self) -> None:
        explicit_families = {
            row["action_family"]
            for row in self.prohibited_rows
            if row["source_scope"] == "S02_P3_EXPLICIT"
        }
        self.assertEqual(
            explicit_families,
            {
                "PAYMENT",
                "TAX_FILING",
                "INVOICE_ISSUANCE",
                "PAYROLL_APPROVAL",
                "FULL_REPORT_EXTERNAL_SEND",
                "RAW_DATA_MUTATION",
            },
        )
        business_lines = {
            row["business_line_id"]
            for row in self.prohibited_rows
            if row["source_scope"] == "BUSINESS_LINE_MATRIX"
        }
        self.assertEqual(business_lines, {f"BL-{index:02d}" for index in range(1, 11)})
        self.assertTrue(all(row["hard_stop_required"] for row in self.prohibited_rows))
        self.assertTrue(all(not row["automatic_execution_allowed"] for row in self.prohibited_rows))
        self.assertTrue(all(not row["merge_allowed_on_detection"] for row in self.prohibited_rows))
        self.assertTrue(all(not row["stop_triggered_in_s02_p3"] for row in self.prohibited_rows))
        self.assertTrue(all(not row["change_control_can_override"] for row in self.prohibited_rows))
        self.assertTrue(all(not row["runtime_guard_implemented"] for row in self.prohibited_rows))
        self.assertTrue(all(not row["prohibited_action_implemented_in_s02_p3"] for row in self.prohibited_rows))
        self.assertEqual(validate_prohibited_action_rows(self.prohibited_rows), [])

    def test_prohibited_action_validator_fails_closed(self) -> None:
        missing = [
            row
            for row in copy.deepcopy(self.prohibited_rows)
            if row["action_family"] != "PAYMENT"
            or row["source_scope"] != "S02_P3_EXPLICIT"
        ]
        self.assertTrue(validate_prohibited_action_rows(missing))

        override = copy.deepcopy(self.prohibited_rows)
        override[0]["change_control_can_override"] = True
        self.assertTrue(validate_prohibited_action_rows(override))

        merge_open = copy.deepcopy(self.prohibited_rows)
        merge_open[0]["merge_allowed_on_detection"] = True
        self.assertTrue(validate_prohibited_action_rows(merge_open))

        semantic_drift = copy.deepcopy(self.prohibited_rows)
        target = next(
            row
            for row in semantic_drift
            if row["source_scope"] == "BUSINESS_LINE_MATRIX"
        )
        target["prohibited_action"] = "无关占位内容"
        target["detection_tokens"] = ["OTHER_HIGH_RISK_ACTION"]
        self.assertTrue(validate_prohibited_action_rows(semantic_drift))

    def test_change_control_protocol_is_auditable_and_fail_closed(self) -> None:
        self.assertEqual(
            set(self.protocol["auditable_domains"]),
            {"FRONTEND", "BACKEND", "FORMULA", "DATA_CONTRACT"},
        )
        self.assertEqual(
            set(self.protocol["change_types"]),
            {"REQUIREMENT", "FRONTEND", "BACKEND", "FORMULA", "DATA_CONTRACT"},
        )
        self.assertEqual(
            self.protocol["state_machine"]["merge_eligible_state"],
            "VALIDATED",
        )
        self.assertTrue(self.protocol["merge_gate"]["registration_required"])
        self.assertTrue(self.protocol["merge_gate"]["approval_required"])
        self.assertTrue(self.protocol["merge_gate"]["regression_scope_required"])
        self.assertFalse(self.protocol["merge_gate"]["unregistered_change_merge_allowed"])
        self.assertFalse(self.protocol["scope_integrity"]["time_pressure_quality_tradeoff_allowed"])
        self.assertFalse(self.protocol["runtime_or_ci_hook_implemented_in_s02_p3"])
        self.assertEqual(validate_change_control_protocol(self.protocol), [])

    def test_change_control_protocol_semantic_mutations_fail_closed(self) -> None:
        scope_integrity_mutations = {
            "priority_change_requires_justification": False,
            "p0_p1_silent_removal_allowed": True,
            "p2_silent_promotion_allowed": True,
            "prohibited_action_override_allowed": True,
        }
        for field, value in scope_integrity_mutations.items():
            with self.subTest(scope_integrity=field):
                protocol = copy.deepcopy(self.protocol)
                protocol["scope_integrity"][field] = value
                self.assertTrue(validate_change_control_protocol(protocol))

        for field, value in (
            ("append_only", False),
            ("silent_update_allowed", True),
            ("content_hash_required", False),
            ("actor_role_required", False),
            ("timestamp_required", False),
            ("reversal_event_required_after_approval", False),
        ):
            with self.subTest(audit_contract=field):
                protocol = copy.deepcopy(self.protocol)
                protocol["audit_event_contract"][field] = value
                self.assertTrue(validate_change_control_protocol(protocol))

        protocol = copy.deepcopy(self.protocol)
        protocol["required_change_fields"].remove("risk_level")
        self.assertTrue(validate_change_control_protocol(protocol))

    def _valid_change_record(self) -> dict[str, object]:
        return {
            "schema_version": "kmfa.v015.change_request.v1",
            "change_id": "CHG-KMFA-V015-0001",
            "requested_at": "2026-07-13T12:00:00+10:00",
            "requester_role": "product_owner",
            "change_type": "REQUIREMENT",
            "reason": "补足已登记 P0 需求的验收条件。",
            "affected_requirement_ids": ["R001"],
            "affected_scope_item_ids": ["R001", "BL-01"],
            "affected_stage_phase_task_refs": ["S14", "S20P1T01"],
            "affected_artifact_refs": ["KMFA/product/change_ref"],
            "impact_domains": ["FRONTEND", "BACKEND"],
            "before_version": "1.5.0-dev-s02p3",
            "after_version": "1.5.0-dev-future-change",
            "old_priority": "P0",
            "new_priority": "P0",
            "priority_change_justification": "优先级不变。",
            "time_pressure_only": False,
            "quality_tradeoff_allowed": False,
            "scope_disposition": "IN_SCOPE",
            "impact_summary": "更新页面与 API 的验收合同。",
            "security_impact": "权限回归必测。",
            "privacy_impact": "不新增敏感公开字段。",
            "precision_impact": "不改变金额精度。",
            "report_impact": "不授权正式报告。",
            "acceptance_impact": "R001 验收范围增加回归项。",
            "regression_scope": {
                "FRONTEND": ["user_flow", "accessibility", "runtime_e2e"],
                "BACKEND": [
                    "api_contract",
                    "persistence",
                    "authorization",
                    "error_path",
                ],
            },
            "risk_level": "HIGH",
            "approval_state": "APPROVED",
            "approver_role": "owner",
            "change_state": "VALIDATED",
            "implementation_refs": ["KMFA/product/change_ref"],
            "validation_refs": ["KMFA/tests/change_ref"],
            "evidence_refs": ["KMFA/stage_artifacts/change_ref"],
            "rollback_plan": "Revert the bounded change commit.",
            "audit_event_refs": ["EVENT-KMFA-CHANGE-0001"],
            "public_safe_status": "PUBLIC_SAFE",
        }

    def test_schema_complete_record_is_only_planning_merge_review_candidate(self) -> None:
        result = evaluate_change_record(self._valid_change_record(), self.protocol)
        self.assertTrue(result["registered"])
        self.assertTrue(result["impact_assessed"])
        self.assertTrue(result["priority_recorded"])
        self.assertTrue(result["regression_scope_complete"])
        self.assertTrue(result["approval_complete"])
        self.assertTrue(result["validation_complete"])
        self.assertTrue(result["planning_record_complete"])
        self.assertTrue(result["merge_review_candidate"])
        self.assertFalse(result["merge_eligible"])
        self.assertFalse(result["merge_enforcement_verified"])
        self.assertEqual(len(result["enforcement_limitations"]), 4)
        self.assertEqual(result["blocking_reasons"], [])

    def test_unregistered_unapproved_or_incomplete_change_cannot_merge(self) -> None:
        for key, value in (
            ("change_id", ""),
            ("approval_state", "DRAFT"),
            ("validation_refs", []),
            ("time_pressure_only", True),
            ("quality_tradeoff_allowed", True),
        ):
            record = self._valid_change_record()
            record[key] = value
            result = evaluate_change_record(record, self.protocol)
            self.assertFalse(result["merge_eligible"], key)
            self.assertFalse(result["merge_review_candidate"], key)
            self.assertTrue(result["blocking_reasons"], key)

        record = self._valid_change_record()
        record["regression_scope"] = {"FRONTEND": ["user_flow"]}
        result = evaluate_change_record(record, self.protocol)
        self.assertFalse(result["merge_eligible"])
        self.assertFalse(result["merge_review_candidate"])
        self.assertIn("REGRESSION_SCOPE_INCOMPLETE", result["blocking_reasons"])

        for field, value in (
            ("scope_disposition", ""),
            ("risk_level", ""),
            ("affected_requirement_ids", []),
        ):
            record = self._valid_change_record()
            record[field] = value
            result = evaluate_change_record(record, self.protocol)
            self.assertFalse(result["merge_eligible"], field)
            self.assertFalse(result["merge_review_candidate"], field)
            self.assertIn("REQUIRED_CHANGE_FIELD_MISSING", result["blocking_reasons"])

        record = self._valid_change_record()
        record["change_type"] = "FRONTEND"
        record["impact_domains"] = ["BACKEND"]
        record["regression_scope"] = {
            "BACKEND": ["api_contract", "persistence", "authorization", "error_path"]
        }
        result = evaluate_change_record(record, self.protocol)
        self.assertFalse(result["merge_eligible"])
        self.assertFalse(result["merge_review_candidate"])
        self.assertIn("CHANGE_TYPE_IMPACT_DOMAIN_MISMATCH", result["blocking_reasons"])

        record = self._valid_change_record()
        record["change_type"] = "FRONTEND"
        record["impact_domains"] = ["FRONTEND"]
        record["regression_scope"] = {"FRONTEND": ["placeholder"]}
        result = evaluate_change_record(record, self.protocol)
        self.assertFalse(result["merge_eligible"])
        self.assertFalse(result["merge_review_candidate"])
        self.assertIn("REGRESSION_SCOPE_INCOMPLETE", result["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
