from __future__ import annotations

import csv
import json
import struct
import unittest

from pypdf import PdfReader

from KMFA.tools import build_v015_s21_p2_report_generation as builder


class ReportGenerationArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_is_pending_or_final_and_stays_inside_s21_p2(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertIn(value["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual((value["run_phase_id"], value["roadmap_phase_id"], value["format_count"]), ("V015_S21_P2_REPORT_GENERATION", "S21-P2", 3))
        self.assertEqual((value["exact_numeric_value_count"], value["cross_format_difference_integer"]), (21, 0))
        self.assertFalse(value["s21_p3_started"])
        self.assertFalse(value["github_upload_performed"])
        self.assertFalse(value["app_reinstall_performed"])

    def test_html_pdf_csv_and_cross_format_contracts_are_complete(self) -> None:
        html = self.value(builder.HTML_CONTRACT_PATH)
        pdf = self.value(builder.PDF_CONTRACT_PATH)
        appendix = self.value(builder.APPENDIX_CONTRACT_PATH)
        consistency = self.value(builder.CONSISTENCY_PATH)
        self.assertEqual((html["responsive"], html["printable"], html["chapter_navigation_count"], html["raw_integer_marker_count"]), (True, True, 6, 21))
        self.assertGreaterEqual(pdf["page_count"], 2)
        self.assertTrue(pdf["page_number_present"] and pdf["professional_appendix_present"] and pdf["source_section_present"])
        self.assertEqual((appendix["row_count"], appendix["difference_integer"], appendix["executable_formula_cell_count"]), (21, 0, 0))
        self.assertEqual((consistency["status"], consistency["numeric_value_count"], consistency["difference_integer"]), ("PASS", 21, 0))

    def test_export_files_are_real_and_csv_values_are_exact(self) -> None:
        self.assertTrue(builder.HTML_PATH.read_bytes().startswith(b"<!doctype html>"))
        self.assertTrue(builder.PDF_PATH.read_bytes().startswith(b"%PDF"))
        self.assertGreaterEqual(len(PdfReader(str(builder.PDF_PATH)).pages), 2)
        with builder.CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 21)
        self.assertTrue(all(row["value_integer"].lstrip("-").isdigit() and int(row["difference_integer"]) == 0 for row in rows))

    def test_browser_and_pdf_visual_evidence_has_expected_dimensions(self) -> None:
        def size(path):
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            return struct.unpack(">II", data[16:24])

        browser_sizes = [size(path) for path in builder.SCREENSHOT_PATHS]
        pdf_sizes = [size(path) for path in builder.PDF_PREVIEW_PATHS]
        self.assertTrue(all(width >= 1000 and height >= 700 for width, height in browser_sizes[:3]))
        self.assertTrue(all(width == 390 and height >= 800 for width, height in browser_sizes[3:]))
        self.assertTrue(all(width >= 1200 and height >= 1700 for width, height in pdf_sizes))

    def test_public_checks_and_task_matrix_are_complete(self) -> None:
        checks = self.value(builder.PUBLIC_CHECKS_PATH)
        matrix = self.value(builder.TASK_MATRIX_PATH)
        self.assertEqual((checks["status"], checks["public_check_count"], checks["public_check_failed_count"]), ("PASS", 60, 0))
        self.assertEqual((matrix["phase_task_count"], len(matrix["tasks"])), (3, 3))
        self.assertTrue(all(row["status"] == "PASS" for row in matrix["tasks"]))


if __name__ == "__main__":
    unittest.main()
