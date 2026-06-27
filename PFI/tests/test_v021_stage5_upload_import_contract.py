from __future__ import annotations

import unittest
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import (
    STAGE5_TASK_IDS,
    build_v021_stage5_contract,
)


class V021Stage5UploadImportContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.css = (self.root / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.web_source = "\n".join((self.html, self.js, self.css))

    def test_stage5_contract_covers_upload_and_import_tasks(self) -> None:
        contract = build_v021_stage5_contract()

        self.assertEqual(contract["schema"], "PFIV021FrontendOptimizationStage5ContractV1")
        self.assertEqual(tuple(contract["task_ids"]), STAGE5_TASK_IDS)
        self.assertEqual(contract["upload_center_contract"]["route"], "/sources-upload")
        self.assertEqual(contract["upload_center_contract"]["workspace"], "sync")
        self.assertEqual(contract["upload_center_contract"]["max_file_mb"], 50)
        self.assertIn("CSV", contract["upload_center_contract"]["accepted_file_types"])
        self.assertIn("ZIP", contract["upload_center_contract"]["accepted_file_types"])
        self.assertEqual(contract["import_center_contract"]["review_entry"]["target_workspace"], "ledger")

    def test_upload_center_has_click_drag_status_and_failure_markers(self) -> None:
        contract = build_v021_stage5_contract()["upload_center_contract"]

        for marker in contract["html_markers"]:
            self.assertIn(marker, self.html)
        self.assertIn('type="file"', self.html)
        self.assertIn("multiple", self.html)
        self.assertIn('accept=".csv,.zip,.xls,.xlsx,text/csv,application/zip"', self.html)
        self.assertIn("等待选择文件", self.html)
        self.assertIn("拖拽 CSV / ZIP / XLSX 到这里", self.html)
        self.assertIn("data-upload-state=\"idle\"", self.html)

    def test_upload_center_javascript_validates_and_renders_feedback(self) -> None:
        for required in (
            "const UPLOAD_ALLOWED_EXTENSIONS",
            "const UPLOAD_MAX_FILE_MB = 50",
            "function bindUploadCenterEvents",
            "function handleUploadSelection",
            "function validateUploadFile",
            "function renderUploadStatus",
            "dragenter",
            "dragover",
            "dragleave",
            "drop",
            "不支持的文件类型",
            "文件过大",
            "导入预检完成",
        ):
            self.assertIn(required, self.js)

    def test_import_center_has_batches_summary_and_review_entry(self) -> None:
        contract = build_v021_stage5_contract()["import_center_contract"]

        for marker in contract["html_markers"]:
            self.assertIn(marker, self.html)
        for required in (
            "function renderImportCenter",
            "function buildPendingBatchFromFiles",
            "function openImportReviewQueue",
            "data-import-summary-files",
            "data-import-summary-records",
            "data-import-summary-review",
            "data-import-summary-errors",
            "data-import-batches",
            "data-import-review-link",
            "进入账本复核",
        ):
            self.assertIn(required, self.web_source)
        self.assertIn('renderWorkspace("ledger"', self.js)

    def test_stage5_styles_are_responsive_and_not_execution_or_stage6_scope(self) -> None:
        for required in (
            ".upload-import-panel",
            ".upload-import-grid",
            ".upload-dropzone",
            ".upload-dropzone.is-dragover",
            ".upload-error",
            ".upload-file-list",
            ".import-summary",
            ".import-batches",
            ".import-batch",
        ):
            self.assertIn(required, self.css)

        for forbidden in (
            'data-action="trade"',
            'data-action="pay"',
            'data-action="broker-submit"',
            "CREATE TABLE position_adjustment",
            "holdings_persistence",
        ):
            self.assertNotIn(forbidden, self.web_source)
        self.assertIn("不做实盘自动下单", self.web_source)


if __name__ == "__main__":
    unittest.main()
