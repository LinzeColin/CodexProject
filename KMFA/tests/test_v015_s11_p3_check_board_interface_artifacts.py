from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s11_p3_check_board_interface as builder
from KMFA.tools import v015_s11_p3_check_board_interface as ui


class CheckBoardInterfaceArtifactTests(unittest.TestCase):
    def test_deterministic_outputs_match_builder(self) -> None:
        builder.check_outputs()

    def test_manifest_and_task_matrix_match_pending_or_final_state(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        accepted = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(manifest["run_phase_id"], ui.RUN_PHASE_ID)
        self.assertEqual(manifest["interface_row_count"], 34)
        self.assertEqual(manifest["interface_leaf_count"], 6)
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["stage_phase_pass_count"], 3 if accepted else 2)
        self.assertEqual(manifest["stage_task_accepted_count"], 9 if accepted else 6)
        self.assertEqual(matrix["task_accepted_count"], 3 if accepted else 0)
        self.assertEqual(manifest["s11_stage_review_entry_allowed"], accepted)
        self.assertFalse(manifest["s11_stage_review_started"])
        self.assertFalse(manifest["s12_entry_allowed"])

    def test_public_contracts_are_complete_and_readable(self) -> None:
        interface = json.loads(builder.INTERFACE_CONTRACT_PATH.read_text(encoding="utf-8"))
        action = json.loads(builder.ACTION_CONTRACT_PATH.read_text(encoding="utf-8"))
        accessibility = json.loads(builder.ACCESSIBILITY_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(interface["matrix_columns_zh"], ["检查项目", "状态", "影响报告", "更新时间", "负责人", "下一步"])
        self.assertEqual(interface["large_yellow_surface_count"], 0)
        self.assertFalse(interface["internal_field_names_visible_by_default"])
        self.assertEqual({row["kind"] for row in action["action_kinds"]}, set(ui.ACTION_KINDS))
        self.assertEqual(action["frontend_status_write_count"], 0)
        self.assertTrue(action["restore_keyboard_focus"])
        self.assertEqual(accessibility["target"], "WCAG_2_1_AA")

    def test_html_export_is_self_contained_and_current(self) -> None:
        html = builder.HTML_PATH.read_text(encoding="utf-8")
        self.assertEqual(html, ui.render_html())
        self.assertIn("数据检查板", html)
        self.assertIn("点击状态查看详情", html)
        self.assertIn("完成并返回原位置", html)
        self.assertNotRegex(html, r'(?:src|href)=["\']https?://')

    def test_visual_screenshot_is_png_with_desktop_dimensions(self) -> None:
        data = builder.SCREENSHOT_PATH.read_bytes()
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        width, height = struct.unpack(">II", data[16:24])
        self.assertGreaterEqual(width, 1400)
        self.assertGreaterEqual(height, 900)

    def test_product_and_design_baselines_exist(self) -> None:
        product = (builder.PROJECT_ROOT / "PRODUCT.md").read_text(encoding="utf-8")
        design = (builder.PROJECT_ROOT / "DESIGN.md").read_text(encoding="utf-8")
        sidecar = json.loads((builder.PROJECT_ROOT / ".impeccable/design.json").read_text(encoding="utf-8"))
        self.assertIn("## Register\n\nproduct", product)
        self.assertIn("## 6. Do's and Don'ts", design)
        self.assertEqual(sidecar["schemaVersion"], 2)
        self.assertEqual(sidecar["narrative"]["northStar"], "可信经营台")


if __name__ == "__main__":
    unittest.main()
