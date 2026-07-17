from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from KMFA.tools import v015_s06_p1_authoritative_source_registration as subject


def synthetic_private_payload() -> dict:
    records = []
    families = list(subject.FIELD_FAMILIES)
    for index in range(1, 10):
        source_ref = f"S06P1-SRC-{index:03d}"
        candidates = [
            {
                "source_ref": source_ref,
                "source_locator": (
                    f"PAGE_1:LINE_{family}" if index <= 8 else f"SHEET_1:CELL_{family}"
                ),
                "field_family": family,
                "raw_text": f"private synthetic {family}",
                "candidate_role": (
                    "IDENTITY_COMPONENT" if family == "PROJECT_IDENTITY"
                    else "TOP_LEVEL_CATEGORY" if family == "COST_CATEGORY"
                    else "PRIMARY_FIELD"
                ),
                "candidate_status": "CANDIDATE_NOT_FINAL",
            }
            for family in families
        ]
        if index <= 8:
            inspection = {
                "format": "PDF",
                "template_class": "PDF_CURRENT_COMPACT" if index <= 3 else "PDF_LEGACY_DETAILED",
                "field_candidates": candidates,
                "quarantined_components": [],
                "textless_page_count": 0,
            }
            role = "AUTHORITATIVE_PROJECT_COST_PDF"
            suffix = ".pdf"
        else:
            inspection = {
                "format": "XLSX",
                "template_classes": ["XLSX_FORMULA_SUMMARY", "XLSX_MANUAL_DETAIL", "XLSX_IMAGE_EMBEDDED"],
                "field_candidates": candidates,
                "quarantined_components": [],
                "formula_cell_count": 4,
                "cached_formula_display_count": 4,
                "media_count": 2,
            }
            role = "AUTHORITATIVE_PROJECT_COST_WORKBOOK"
            suffix = ".xlsx"
        records.append({
            "source_ref": source_ref,
            "private_member_name": f"private_source_{index}{suffix}",
            "private_member_name_sha256": f"name-hash-{index}",
            "private_member_sha256": f"content-hash-{index}",
            "private_member_size_bytes": 100 + index,
            "source_role": role,
            "integrity_status": "READABLE_HASHED",
            "inspection": inspection,
        })
    return {
        "schema_version": subject.PRIVATE_SCHEMA_VERSION,
        "source_count": 9,
        "pdf_count": 8,
        "workbook_count": 1,
        "source_records": records,
        "raw_root_stat_unchanged": True,
        "package_stat_unchanged": True,
        "package_hash_unchanged": True,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
        "s06_p2_started": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "ocr_final_fact_count": 0,
        "golden_value_confirmed_count": 0,
    }


class ArchiveSelectionTests(unittest.TestCase):
    def _archive(self, root: Path, name: str, *, pdfs: int = 8, workbooks: int = 1) -> Path:
        target = root / name
        with zipfile.ZipFile(target, "w") as archive:
            for index in range(pdfs):
                archive.writestr(f"source-{index + 1}.pdf", b"%PDF-1.4 synthetic")
            for index in range(workbooks):
                archive.writestr(f"source-{index + 1}.xlsx", b"PK synthetic")
            archive.writestr("__MACOSX/._metadata", b"ignored")
        return target

    def test_shape_counts_only_business_members(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            archive = self._archive(Path(value), "authority.zip")
            self.assertEqual(subject.inspect_archive_shape(archive), {
                "source_count": 9,
                "pdf_count": 8,
                "workbook_count": 1,
                "hidden_member_count": 1,
            })

    def test_unique_shape_selects_one_archive(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            expected = self._archive(root, "authority.zip")
            self._archive(root, "other.zip", pdfs=1, workbooks=0)
            selected, status, count = subject.resolve_authority_package(root)
            self.assertEqual((selected, status, count), (expected, "PUBLIC_SHAPE_UNIQUE_MATCH", 1))

    def test_ambiguous_shape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            self._archive(root, "one.zip")
            self._archive(root, "two.zip")
            self.assertEqual(subject.resolve_authority_package(root)[1:], ("PUBLIC_SHAPE_AMBIGUOUS", 2))


class CandidateAndProjectionTests(unittest.TestCase):
    def test_requirement_field_families_are_detected(self) -> None:
        text = "项目名称 合同编号 合同额 资金运用及各项支出 毛利 12.30% 原材料"
        self.assertEqual(subject._families_for_text(text), set(subject.FIELD_FAMILIES))

    def test_gross_profit_row_with_percent_creates_margin_candidate(self) -> None:
        self.assertEqual(subject._families_for_text("毛利 1200.00 15.00%"), {"GROSS_PROFIT", "GROSS_MARGIN"})

    def test_margin_header_is_not_a_gross_profit_candidate(self) -> None:
        self.assertEqual(subject._families_for_text("毛利率"), {"GROSS_MARGIN"})

    def test_pdf_contract_line_is_not_total_expenditure(self) -> None:
        self.assertEqual(
            subject._pdf_families_for_line("一、合同额 98,368.00 占总成本比例"),
            {"CONTRACT_AMOUNT"},
        )

    def test_pdf_nested_cost_detail_is_not_promoted(self) -> None:
        self.assertEqual(subject._pdf_families_for_line("2.差旅费 640.00"), set())
        self.assertEqual(
            subject._pdf_families_for_line("（二）租赁费 1,279.00 3.79%"),
            {"COST_CATEGORY"},
        )

    def test_workbook_header_binding_is_exact(self) -> None:
        self.assertNotIn(subject._normalize("开票金额"), subject.WORKBOOK_HEADER_SEMANTICS)
        self.assertEqual(
            subject.WORKBOOK_HEADER_SEMANTICS[subject._normalize("毛利润")],
            ("GROSS_PROFIT", None),
        )

    def test_projection_covers_all_sources_fields_and_templates(self) -> None:
        projection = subject.public_projection(synthetic_private_payload())
        self.assertEqual(projection["registration"]["source_count"], 9)
        self.assertEqual(projection["registration"]["pdf_count"], 8)
        self.assertEqual(projection["registration"]["workbook_count"], 1)
        self.assertEqual(projection["coverage"]["covered_field_family_count"], 6)
        self.assertEqual(projection["template"]["observed_template_class_count"], 5)
        self.assertTrue(projection["template"]["all_observed_template_classes_have_strategy"])
        self.assertTrue(projection["template"]["formula_and_display_values_separated"])
        self.assertTrue(projection["coverage"]["candidate_semantic_quality_passed"])
        self.assertEqual(projection["coverage"]["contract_total_locator_collision_count"], 0)

    def test_public_projection_drops_private_names_hashes_text_and_values(self) -> None:
        projection = subject.public_projection(synthetic_private_payload())
        rendered = json.dumps(projection, ensure_ascii=False)
        self.assertNotIn("private_source_", rendered)
        self.assertNotIn("content-hash-", rendered)
        self.assertNotIn("private synthetic", rendered)
        self.assertNotIn("PAGE_1:LINE_", rendered)
        self.assertNotIn("SHEET_1:CELL_", rendered)
        self.assertEqual(projection["registration"]["public_raw_name_count"], 0)
        self.assertEqual(projection["registration"]["public_raw_hash_count"], 0)
        self.assertEqual(projection["registration"]["public_raw_text_count"], 0)
        self.assertEqual(projection["registration"]["public_raw_value_count"], 0)

    def test_unknown_template_is_quarantine_only(self) -> None:
        payload = synthetic_private_payload()
        payload["source_records"][0]["inspection"]["template_class"] = "UNRECOGNIZED_PDF_TEMPLATE"
        projection = subject.public_projection(payload)
        self.assertEqual(projection["template"]["unknown_template_source_count"], 1)
        self.assertFalse(projection["template"]["all_observed_template_classes_have_strategy"])
        unknown = next(row for row in projection["template"]["observed_template_classes"] if row["template_class"].startswith("UNRECOGNIZED"))
        self.assertEqual(unknown["parser_strategy"], "QUARANTINE_ONLY")


class BoundaryTests(unittest.TestCase):
    def test_raw_mutation_fails_closed(self) -> None:
        payload = synthetic_private_payload()
        payload["raw_mutation_performed"] = True
        with self.assertRaises(subject.RegistrationError):
            subject.validate_private_payload(payload)

    def test_raw_stat_drift_fails_closed(self) -> None:
        payload = synthetic_private_payload()
        payload["package_stat_unchanged"] = False
        with self.assertRaises(subject.RegistrationError):
            subject.validate_private_payload(payload)

    def test_ocr_or_golden_fact_is_not_allowed_in_p1(self) -> None:
        for key in ("ocr_final_fact_count", "golden_value_confirmed_count"):
            payload = synthetic_private_payload()
            payload[key] = 1
            with self.assertRaises(subject.RegistrationError):
                subject.validate_private_payload(payload)

    def test_contract_and_total_cannot_share_one_locator(self) -> None:
        payload = synthetic_private_payload()
        collision = dict(payload["source_records"][0]["inspection"]["field_candidates"][1])
        collision["field_family"] = "TOTAL_EXPENDITURE"
        collision["candidate_role"] = "PRIMARY_FIELD"
        payload["source_records"][0]["inspection"]["field_candidates"].append(collision)
        with self.assertRaises(subject.RegistrationError):
            subject.validate_private_payload(payload)


if __name__ == "__main__":
    unittest.main()
