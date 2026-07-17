from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools import v015_s11_p2_check_board_data_model as model


class CheckBoardDataModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.facts = model.public_backend_facts()
        self.board = model.derive_board_model(self.facts)
        self.leaves = {row["backend_fact_ref"]: row for row in self.board["nodes"] if row["is_leaf"]}

    def test_public_verification_is_complete(self) -> None:
        verification = model.public_verification()
        self.assertEqual(verification["accounting"], {"total": 83, "passed": 83, "failed": 0})

    def test_six_level_hierarchy_never_flattens_files_at_root(self) -> None:
        self.assertEqual([row[0] for row in model.HIERARCHY_LEVELS], [
            "SOURCE_SYSTEM", "BUSINESS_SEGMENT", "FILE_PACKAGE", "ENTITY", "BANK_OR_ACCOUNT", "REPORT_OR_SHEET"
        ])
        self.assertEqual(self.board["max_depth"], 5)
        self.assertEqual(self.board["flat_leaf_at_root_count"], 0)
        self.assertTrue(all(row["depth"] == 5 and len(row["hierarchy_path"]) == 6 for row in self.leaves.values()))

    def test_every_node_has_valid_parent_and_required_columns(self) -> None:
        node_ids = {row["node_id"] for row in self.board["nodes"]}
        for row in self.board["nodes"]:
            if row["depth"]:
                self.assertIn(row["parent_node_id"], node_ids)
            else:
                self.assertIsNone(row["parent_node_id"])
            self.assertEqual(set(row["display_columns"]), set(model.REQUIRED_COLUMNS))
            self.assertTrue(row["display"]["reason_zh"])
            self.assertTrue(row["next_action_zh"])

    def test_expand_and_collapse_are_projection_only(self) -> None:
        collapsed = model.project_board(self.board, {})
        first_root = self.board["root_node_ids"][0]
        expanded = model.project_board(self.board, {"expanded_node_ids": [first_root]})
        collapsed_again = model.project_board(self.board, {"expanded_node_ids": []})
        self.assertEqual(collapsed["visible_row_count"], len(self.board["root_node_ids"]))
        self.assertGreater(expanded["visible_row_count"], collapsed["visible_row_count"])
        self.assertEqual(collapsed_again["projection_fingerprint"], collapsed["projection_fingerprint"])
        self.assertEqual(expanded["backend_state_mutation_count"], 0)

    def test_search_and_filters_keep_full_ancestor_path(self) -> None:
        search = model.project_board(self.board, {"search_text": "应收检查表"})
        outdated = model.project_board(self.board, {"status_filters": ["已过期"]})
        owner = model.project_board(self.board, {"owner_filters": ["资金负责人"]})
        alerts = model.project_board(self.board, {"alert_only": True})
        self.assertEqual((search["matched_leaf_count"], search["visible_row_count"]), (1, 6))
        self.assertEqual((outdated["matched_leaf_count"], outdated["visible_row_count"]), (1, 6))
        self.assertEqual((owner["matched_leaf_count"], owner["visible_row_count"]), (1, 6))
        self.assertEqual(alerts["matched_leaf_count"], 5)
        self.assertTrue(all(row["auto_expanded_for_query"] for row in (search, outdated, owner, alerts)))

    def test_missing_source_explains_impact_owner_and_action(self) -> None:
        row = self.leaves["QBF-003"]
        self.assertEqual(row["display"]["label_zh"], "不可使用")
        self.assertIn("缺少", row["blocker_reason_zh"])
        self.assertIn("补充", row["next_action_zh"])
        self.assertEqual(row["owner_role_zh"], "回款负责人")
        self.assertEqual([alert["alert_type"] for alert in row["alerts"]], ["MISSING_SOURCE"])

    def test_quality_pass_is_the_only_auto_selection_path(self) -> None:
        self.assertTrue(self.leaves["QBF-001"]["auto_selected"])
        for fact_id in ("QBF-002", "QBF-003", "QBF-004", "QBF-005", "QBF-006"):
            self.assertFalse(self.leaves[fact_id]["auto_selected"])
        self.assertEqual(self.leaves["QBF-005"]["professional_detail"]["score_bps"], 9375)
        self.assertEqual(self.leaves["QBF-005"]["display"]["label_zh"], "不可使用")

    def test_missing_to_imported_pass_transition_updates_automatically(self) -> None:
        before, after = model.public_transition_facts()
        event = model.derive_transition(before, after)
        self.assertEqual((event["before_status_zh"], event["after_status_zh"]), ("不可使用", "已通过"))
        self.assertEqual((event["before_auto_selected"], event["after_auto_selected"]), (False, True))
        self.assertEqual(event["after_alert_types"], [])
        self.assertTrue(event["automatic_update_applied"])
        self.assertFalse(event["frontend_state_write_applied"])
        self.assertFalse(event["raw_source_mutation_performed"])

    def test_frontend_cannot_override_status_or_ready_state(self) -> None:
        for key, value in (("status_override", "已通过"), ("ready", True), ("auto_selected", True), ("quality_snapshot", {})):
            with self.subTest(key=key):
                with self.assertRaisesRegex(model.CheckBoardModelError, "FRONTEND_STATE_MUTATION_FORBIDDEN"):
                    model.project_board(self.board, {key: value})

    def test_parent_status_is_derived_from_worst_descendant(self) -> None:
        roots = {row["label_zh"]: row for row in self.board["nodes"] if row["depth"] == 0}
        self.assertEqual(roots["财务文件源"]["display"]["label_zh"], "需确认")
        self.assertEqual(roots["业务系统导出源"]["display"]["label_zh"], "不可使用")
        self.assertFalse(roots["财务文件源"]["auto_selected"])
        self.assertIn("下级项", roots["财务文件源"]["blocker_reason_zh"])

    def test_backend_fact_validation_fails_closed(self) -> None:
        cases = []
        unknown_field = copy.deepcopy(self.facts[0])
        unknown_field["status"] = "已通过"
        cases.append(unknown_field)
        boolean_revision = copy.deepcopy(self.facts[0])
        boolean_revision["fact_revision"] = True
        cases.append(boolean_revision)
        missing_quality = copy.deepcopy(self.facts[0])
        missing_quality["quality_snapshot"] = None
        cases.append(missing_quality)
        short_path = copy.deepcopy(self.facts[0])
        short_path["hierarchy_path"] = short_path["hierarchy_path"][:-1]
        cases.append(short_path)
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(model.CheckBoardModelError):
                    model.validate_backend_fact(case)

    def test_duplicate_fact_or_leaf_path_is_rejected(self) -> None:
        duplicate_id = copy.deepcopy(self.facts)
        duplicate_id[1]["fact_id"] = duplicate_id[0]["fact_id"]
        with self.assertRaisesRegex(model.CheckBoardModelError, "FACT_ID_DUPLICATE"):
            model.derive_board_model(duplicate_id)
        duplicate_path = copy.deepcopy(self.facts)
        duplicate_path[1]["hierarchy_path"] = copy.deepcopy(duplicate_path[0]["hierarchy_path"])
        with self.assertRaisesRegex(model.CheckBoardModelError, "LEAF_PATH_DUPLICATE"):
            model.derive_board_model(duplicate_path)

    def test_transition_rejects_stale_or_identity_drift(self) -> None:
        before, after = model.public_transition_facts()
        stale = copy.deepcopy(after)
        stale["fact_revision"] = 1
        with self.assertRaisesRegex(model.CheckBoardModelError, "TRANSITION_REVISION_INVALID"):
            model.derive_transition(before, stale)
        drift = copy.deepcopy(after)
        drift["hierarchy_path"][-1] = "其他检查表"
        with self.assertRaisesRegex(model.CheckBoardModelError, "TRANSITION_IDENTITY_DRIFT"):
            model.derive_transition(before, drift)

    def test_outputs_are_deterministic_and_public_safe(self) -> None:
        second = model.derive_board_model(model.public_backend_facts())
        self.assertEqual(self.board["model_fingerprint"], second["model_fingerprint"])
        payload = json.dumps([self.board, model.public_verification()], ensure_ascii=False, sort_keys=True).casefold()
        for forbidden in ("/users/", "/volumes/", "file://", "kmfa_metadata", "private://", ".xlsx", ".xls", ".zip", "password"):
            self.assertNotIn(forbidden, payload)
        self.assertEqual(self.board["raw_root_access_count"], 0)
        self.assertEqual(self.board["live_source_read_count"], 0)
        self.assertFalse(self.board["github_upload_performed"])
        self.assertFalse(self.board["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
