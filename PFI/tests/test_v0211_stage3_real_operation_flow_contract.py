from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

import pfi_v02.stage_v0211_ui_recovery as recovery


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._ignored_depth:
            self._ignored_depth += 1
            return
        if tag in {"script", "style"}:
            self._ignored_depth += 1
            return
        attr_map = {key: value or "" for key, value in attrs}
        if "hidden" in attr_map:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        clean = " ".join(data.split())
        if clean:
            self.parts.append(clean)


def visible_text(html: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html)
    return "\n".join(parser.parts)


class V0211Stage3RealOperationFlowContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")

    def test_contract_locks_stage3_scope_and_non_goals(self) -> None:
        self.assertTrue(hasattr(recovery, "build_v0211_stage3_contract"))
        contract = recovery.build_v0211_stage3_contract()

        self.assertEqual(contract["stage"], "S3 真实操作流")
        self.assertEqual(contract["task_id"], "V0211-S3-T01")
        self.assertEqual(contract["current_stage_only"], True)
        self.assertIn("上传、解析预览、字段映射、待复核和确认入库路径", "\n".join(contract["delivery_focus"]))
        self.assertIn("账本筛选、分类、复核和导出路径", "\n".join(contract["delivery_focus"]))
        self.assertIn("持仓编辑表单和设置保存路径", "\n".join(contract["delivery_focus"]))
        self.assertIn("不把生产保存写进 localStorage、sessionStorage 或 IndexedDB", "\n".join(contract["forbidden_work"]))
        self.assertIn("不声明 Stage 4 持久化与同步完成", "\n".join(contract["stage3_non_goals"]))
        self.assertIn("不声明 Stage 5 真实图表与最终验收完成", "\n".join(contract["stage3_non_goals"]))

    def test_operation_flow_panels_exist_with_chinese_state_surfaces(self) -> None:
        required_html_markers = (
            "data-stage3-upload-flow",
            "data-upload-preview",
            "data-field-mapping-panel",
            "data-import-confirm",
            "data-review-queue-entry",
            "data-ledger-operation-flow",
            "data-ledger-filter",
            "data-ledger-category-select",
            "data-ledger-review-save",
            "data-ledger-export",
            "data-holdings-operation-flow",
            "data-holding-edit-form",
            "data-holdings-save-action",
            "data-holdings-draft-label",
            "data-settings-operation-flow",
            "data-settings-save",
            "data-settings-reset",
            "data-settings-save-status",
        )
        for marker in required_html_markers:
            self.assertIn(marker, self.html)

        required_js_functions = (
            "renderStage3UploadFlow",
            "confirmStage3Import",
            "renderLedgerOperationFlow",
            "saveLedgerReview",
            "exportLedgerReview",
            "renderSettingsOperationFlow",
            "saveSettingsOperationFlow",
        )
        for function_name in required_js_functions:
            self.assertIn(function_name, self.js)

    def test_browser_cache_is_not_the_production_holdings_save_path(self) -> None:
        save_function = re.search(r"async function saveHoldingsEdits\(\)[\s\S]*?\n}", self.js)
        self.assertIsNotNone(save_function)
        save_source = save_function.group(0)

        self.assertIn("saveHoldingsToBackend(rows)", save_source)
        self.assertNotIn("localStorage.setItem", save_source)
        self.assertNotIn("sessionStorage", save_source)
        self.assertNotIn("indexedDB", save_source)
        self.assertIn('runtimeApiJson("/api/holdings"', self.js)
        self.assertIn("未提交草稿", self.html)
        self.assertIn("saveUnsubmittedHoldingsDraft", self.js)

    def test_visible_shell_has_no_formal_fake_data_or_developer_pollution(self) -> None:
        text = visible_text(self.html)
        forbidden_visible = (
            "Task Pack",
            "Demo",
            "Prototype",
            "runtime",
            "Boundary",
            "Evidence",
            "Source",
            "Model",
            "测试数据",
            "样例数据",
            "模拟数据",
            "fixture",
            "mock",
            "fake",
            "synthetic",
        )
        for phrase in forbidden_visible:
            self.assertNotIn(phrase, text)

        for phrase in (
            "上传中心",
            "导入中心",
            "解析预览",
            "字段映射",
            "确认入库",
            "账本筛选",
            "分类复核",
            "导出流水",
            "持仓编辑",
            "未提交草稿",
            "保存设置",
        ):
            self.assertIn(phrase, self.html)


if __name__ == "__main__":
    unittest.main()
