from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s21_p2_report_generation as model


class ReportGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.report = model.demo_report_model()
        cls.payload = model.build_report_payload(cls.report)
        cls.journal = model.ReportExportJournal(cls.root / "exports.jsonl", cls.root / "bundles")
        cls.export = cls.journal.create(
            cls.report, idempotency_key="unit-export-001", recorded_at="2026-07-17T00:01:00+00:00"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_payload_reconciles_income_cost_profit_and_collections(self) -> None:
        headline = self.payload["headline"]
        self.assertEqual(headline["revenue_cents"] - headline["cost_cents"], headline["gross_profit_cents"])
        self.assertEqual(headline["revenue_cents"] - headline["collection_cents"], headline["receivable_cents"])
        self.assertEqual((headline["gross_margin_bps"], len(model.canonical_numeric_values(self.payload))), (2479, 21))

    def test_payload_binds_predecessor_version_sources_and_formulas(self) -> None:
        self.assertEqual(self.payload["report_version_id"], self.report["report_version_id"])
        self.assertEqual(self.payload["source_binding_fingerprint"], self.report["source_binding_fingerprint"])
        self.assertEqual(self.payload["formula_binding_fingerprint"], self.report["formula_binding_fingerprint"])
        self.assertEqual(len(self.payload["source_bindings"]), 6)

    def test_incomplete_or_non_public_report_is_rejected(self) -> None:
        incomplete = json.loads(json.dumps(self.report))
        incomplete["trust_and_limitations"]["complete_report_claim_allowed"] = False
        with self.assertRaisesRegex(model.ReportGenerationError, "关键资料不完整"):
            model.build_report_payload(incomplete)
        private = json.loads(json.dumps(self.report))
        private["data_classification"] = "PRIVATE"
        with self.assertRaisesRegex(model.ReportGenerationError, "公开合成"):
            model.build_report_payload(private)

    def test_html_is_responsive_printable_navigable_and_source_bound(self) -> None:
        text = model.render_report_html(self.payload)
        for token in ("@media print", "@media(max-width:800px)", 'aria-label="章节导航"', 'id="sources"', self.report["report_version_id"]):
            self.assertIn(token, text)
        self.assertEqual(text.count("data-raw-integer="), 21)

    def test_csv_preserves_exact_integer_values_and_zero_differences(self) -> None:
        text = model.render_appendix_csv(self.payload)
        rows = list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))
        actual = {row["record_id"]: int(row["value_integer"]) for row in rows}
        self.assertTrue(text.startswith("\ufeff"))
        self.assertEqual(actual, model.canonical_numeric_values(self.payload))
        self.assertTrue(all(int(row["difference_integer"]) == 0 for row in rows))
        self.assertTrue(all(row["formula_explanation_zh"] and row["source_ref"] for row in rows))

    def test_pdf_has_pages_headers_sources_and_all_numeric_tokens(self) -> None:
        pdf_path, _ = self.journal.file_path(self.export["export_id"], "PDF")
        text = "".join(model.extract_pdf_text(pdf_path).split())
        self.assertIn("第1页", text)
        self.assertIn("专业附表与来源", text)
        for key, value in model.canonical_numeric_values(self.payload).items():
            self.assertTrue(f"RAW_INTEGER:{key}={value}" in text or f"RAW_INTEGER:{key}{value}" in text)

    def test_bundle_cross_format_check_is_zero_difference(self) -> None:
        result = self.export["cross_format_consistency"]
        self.assertEqual((result["status"], result["numeric_value_count"], result["difference_integer"]), ("PASS", 21, 0))
        self.assertEqual(set(self.export["files"]), set(model.FORMATS))

    def test_export_is_idempotent_and_history_is_append_only(self) -> None:
        same = self.journal.create(self.report, idempotency_key="unit-export-001")
        self.assertEqual(same["event_hash"], self.export["event_hash"])
        self.assertEqual(self.journal.list()["export_count"], 1)
        self.assertEqual(self.export["previous_event_hash"], "GENESIS")

    def test_unknown_export_and_format_fail_closed(self) -> None:
        with self.assertRaisesRegex(model.ReportGenerationError, "没有找到"):
            self.journal.get("EXPORT-NOT-FOUND")
        with self.assertRaisesRegex(model.ReportGenerationError, "没有找到"):
            self.journal.file_path(self.export["export_id"], "XLSX")

    def test_public_verification_has_exactly_sixty_passes(self) -> None:
        result = model.verify_phase()
        self.assertEqual((result["status"], result["public_check_count"], result["public_check_pass_count"], result["public_check_failed_count"]), ("PASS", 60, 60, 0))


if __name__ == "__main__":
    unittest.main()
