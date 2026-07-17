from __future__ import annotations

import json
import struct
import unittest
import zipfile
from pathlib import Path

from KMFA.tools import build_v015_s17_p3_project_workflow as build
from KMFA.tools import v015_s17_p3_project_workflow as workflow


class ProjectWorkflowArtifactTests(unittest.TestCase):
    def test_machine_and_human_evidence_are_complete(self) -> None:
        paths = (
            build.MANIFEST_PATH,
            build.SOURCE_CONTRACT_PATH,
            build.UNALLOCATED_CONTRACT_PATH,
            build.VARIANCE_CONTRACT_PATH,
            build.REPORT_CONTRACT_PATH,
            build.BROWSER_CONTRACT_PATH,
            build.PUBLIC_CHECKS_PATH,
            build.TASK_MATRIX_PATH,
            build.REPORT_PAYLOAD_PATH,
            build.EVIDENCE_INDEX_PATH,
            build.WORKBOOK_INSPECTION_PATH,
            build.IMPLEMENTATION_REPORT_PATH,
            build.USER_GUIDE_PATH,
            build.TEST_RESULTS_PATH,
            build.RISKS_ROLLBACK_PATH,
        )
        for path in paths:
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 100, path)

    def test_html_pdf_xlsx_and_evidence_index_are_real(self) -> None:
        self.assertIn("项目成本专题报告", build.HTML_PATH.read_text(encoding="utf-8"))
        self.assertIn("允许差异 0 分", build.HTML_PATH.read_text(encoding="utf-8"))
        self.assertTrue(build.PDF_PATH.read_bytes().startswith(b"%PDF-"))
        self.assertGreater(build.PDF_PATH.stat().st_size, 10_000)
        self.assertTrue(zipfile.is_zipfile(build.XLSX_PATH))
        with zipfile.ZipFile(build.XLSX_PATH) as archive:
            names = set(archive.namelist())
            self.assertIn("xl/workbook.xml", names)
            workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
            for sheet_name in ("项目摘要", "成本明细", "处理记录", "差异分析", "校验与来源"):
                self.assertIn(sheet_name, workbook_xml)
        evidence = json.loads(build.EVIDENCE_INDEX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(evidence), {"source_facts", "processing_event_refs", "calculation_refs", "report_refs"})
        self.assertEqual(evidence["report_refs"], ["HTML", "PDF", "XLSX"])

    def test_workbook_formulas_values_and_error_scan_pass(self) -> None:
        value = json.loads(build.WORKBOOK_INSPECTION_PATH.read_text(encoding="utf-8"))
        summary = value["summary"]["values"]
        self.assertEqual(summary[5][1], 2_345_520)
        self.assertEqual(summary[6][1], 934_480)
        self.assertEqual(summary[11][1], 0)
        self.assertEqual(summary[12][1], "通过：允许差异 0 分")
        self.assertIn("matched 0 entries", value["errors"])
        cost_rows = value["costs"]["values"]
        self.assertTrue(all(row[5] == "通过" for row in cost_rows[4:] if row[0]))

    def test_all_spreadsheet_and_pdf_previews_are_visible_pngs(self) -> None:
        for path in (*build.WORKBOOK_PREVIEW_PATHS, build.PDF_PREVIEW_PATH):
            self.assertTrue(path.is_file(), path)
            data = path.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", data[16:24])
            self.assertGreater(width, 500)
            self.assertGreater(height, 200)

    def test_browser_screenshots_cover_six_human_flows(self) -> None:
        self.assertEqual(len(build.SCREENSHOT_PATHS), workflow.VISUAL_EVIDENCE_COUNT)
        for path in build.SCREENSHOT_PATHS:
            self.assertTrue(path.is_file(), path)
            data = path.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", data[16:24])
            self.assertGreaterEqual(width, 390)
            self.assertGreater(height, 500)

    def test_report_contract_and_task_matrix_are_zero_difference(self) -> None:
        contract = json.loads(build.REPORT_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["format_count"], 3)
        self.assertEqual(contract["workbook_engine"], "@oai/artifact-tool")
        self.assertEqual(contract["workbook_sheet_count"], 5)
        self.assertEqual(contract["workbook_preview_count"], 5)
        self.assertEqual(contract["pdf_preview_count"], 1)
        self.assertEqual(contract["page_golden_difference_cents"], 0)
        self.assertEqual(contract["category_page_difference_cents"], 0)
        self.assertEqual(contract["money_tolerance_cents"], 0)
        self.assertEqual(contract["report_sync_status"], "PASS")
        matrix = json.loads(build.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(matrix["overall_status"], "PASS")
        self.assertEqual([row["status"] for row in matrix["tasks"]], ["PASS", "PASS", "PASS"])

    def test_public_artifacts_contain_no_private_paths_or_real_actions(self) -> None:
        forbidden = ("/Users/", "/Volumes/", "KMFA_MetaData", "private://", "file://")
        for path in (*build.MACHINE_ROOT.glob("*.json"), build.HTML_PATH, *build.HUMAN_ROOT.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{token} in {path}")
        manifest = json.loads(build.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["raw_root_access_count"], 0)
        self.assertEqual(manifest["source_data_write_count"], 0)
        self.assertEqual(manifest["fact_layer_write_count"], 0)
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertFalse(manifest["formal_business_report"])


if __name__ == "__main__":
    unittest.main()
