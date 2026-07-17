from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s11_p2_check_board_data_model as builder
from KMFA.tools import v015_s11_p2_check_board_data_model as kernel


class CheckBoardDataModelArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.board = json.loads(builder.BOARD_MODEL_PATH.read_text(encoding="utf-8"))
        self.projections = json.loads(builder.PROJECTION_EXAMPLES_PATH.read_text(encoding="utf-8"))
        self.flow = json.loads(builder.AUTOMATIC_FLOW_PATH.read_text(encoding="utf-8"))

    def test_deterministic_outputs_are_current(self) -> None:
        builder.check_outputs()

    def test_source_contract_matches_exact_taskpack_phase(self) -> None:
        source = json.loads(builder.SOURCE_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(source["roadmap_phase_id"], "S11-P2")
        self.assertEqual(source["phase_name_zh"], "检查板数据模型")
        self.assertEqual(source["task_ids"], ["S11P2T01", "S11P2T02", "S11P2T03"])
        self.assertEqual(source["stop_conditions_zh"], [
            "不得把所有文件堆在同一层。", "状态无解释则失败。", "前端不可直接把失败改为已就绪。"
        ])

    def test_hierarchy_and_columns_are_materialized(self) -> None:
        hierarchy = json.loads(builder.HIERARCHY_CONTRACT_PATH.read_text(encoding="utf-8"))
        columns = json.loads(builder.COLUMN_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(hierarchy["level_count"], 6)
        self.assertEqual(hierarchy["leaf_depth"], 5)
        self.assertFalse(hierarchy["all_files_in_one_flat_level_allowed"])
        self.assertEqual(tuple(columns["required_columns"]), kernel.REQUIRED_COLUMNS)
        self.assertTrue(columns["every_status_requires_reason"])
        self.assertTrue(columns["missing_source_requires_direct_action"])

    def test_board_sample_has_full_parent_chains(self) -> None:
        self.assertEqual((self.board["node_count"], self.board["leaf_count"], self.board["max_depth"]), (34, 6, 5))
        self.assertEqual(self.board["flat_leaf_at_root_count"], 0)
        leaves = [row for row in self.board["nodes"] if row["is_leaf"]]
        self.assertTrue(all(len(row["hierarchy_path"]) == 6 for row in leaves))
        self.assertTrue(all(set(row["display_columns"]) == set(kernel.REQUIRED_COLUMNS) for row in self.board["nodes"]))

    def test_projection_examples_prove_expand_search_and_filter(self) -> None:
        examples = self.projections["examples"]
        self.assertLess(examples["collapsed"]["visible_row_count"], examples["expanded"]["visible_row_count"])
        self.assertEqual(examples["search"]["matched_leaf_count"], 1)
        self.assertEqual(examples["outdated_filter"]["matched_leaf_count"], 1)
        self.assertEqual(examples["alert_filter"]["matched_leaf_count"], 5)
        self.assertTrue(examples["search"]["auto_expanded_for_query"])

    def test_automatic_flow_is_backend_owned_and_actionable(self) -> None:
        contract = json.loads(builder.STATE_FLOW_CONTRACT_PATH.read_text(encoding="utf-8"))
        transition = self.flow["transition"]
        self.assertTrue(contract["backend_fact_only"])
        self.assertFalse(contract["frontend_status_mutation_allowed"])
        self.assertEqual(transition["before_status_zh"], "不可使用")
        self.assertEqual(transition["after_status_zh"], "已通过")
        self.assertFalse(transition["before_auto_selected"])
        self.assertTrue(transition["after_auto_selected"])
        self.assertFalse(transition["frontend_state_write_applied"])

    def test_manifest_keeps_later_work_closed_until_acceptance(self) -> None:
        accepted = self.manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(self.manifest["s11_p3_entry_allowed"], accepted)
        self.assertFalse(self.manifest["s11_p3_started"])
        self.assertFalse(self.manifest["s11_stage_review_entry_allowed"])
        self.assertFalse(self.manifest["formal_report_generated"])
        self.assertFalse(self.manifest["github_upload_performed"])
        self.assertFalse(self.manifest["app_reinstall_performed"])
        self.assertEqual(self.manifest["raw_root_access_count"], 0)
        self.assertEqual(self.manifest["live_source_read_count"], 0)

    def test_public_artifacts_contain_no_private_or_live_material(self) -> None:
        paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
        paths.extend((builder.HIERARCHY_CONTRACT_PATH, builder.COLUMN_CONTRACT_PATH, builder.STATE_FLOW_CONTRACT_PATH))
        payload = "\n".join(path.read_text(encoding="utf-8") for path in paths).casefold()
        for forbidden in ("/users/", "/volumes/", "/home/", "file://", "kmfa_metadata", "private://", ".xlsx", ".xls", ".zip", "password"):
            self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
