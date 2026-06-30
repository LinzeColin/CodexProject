import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from KMFA.tools.finance_file_adapter import (
    REQUIRED_FINANCE_CATEGORIES,
    build_default_finance_adapter,
    parse_xlsx_structure,
    validate_finance_adapter,
)


def write_minimal_xlsx(path: Path, headers: list[str]) -> None:
    cells = []
    for index, value in enumerate(headers, start=1):
        column = chr(ord("A") + index - 1)
        cells.append(f'<c r="{column}1" t="inlineStr"><is><t>{value}</t></is></c>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData><row r=\"1\">"
        + "".join(cells)
        + "</row></sheetData></worksheet>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "")
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Synthetic Finance" sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/></Relationships>',
        )
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


class FinanceFileAdapterTests(unittest.TestCase):
    def test_parse_xlsx_structure_keeps_only_hashes_and_private_refs(self) -> None:
        headers = ["SYNTHETIC_HEADER_ALPHA", "SYNTHETIC_HEADER_BETA", "SYNTHETIC_HEADER_GAMMA"]
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "synthetic.xlsx"
            write_minimal_xlsx(workbook_path, headers)

            record = parse_xlsx_structure(
                workbook_path,
                source_ref="SRC-FIN-OPERATING-001",
                finance_category="operating_analysis",
                private_source_ref="private://KMFA/S07-P1/source/SRC-FIN-OPERATING-001",
            )

        self.assertEqual(record["record_type"], "finance_file_readonly_structure")
        self.assertEqual(record["schema_version"], "kmfa.finance_file_structure.v1")
        self.assertEqual(record["stage_phase"], "S07-P1")
        self.assertEqual(record["finance_category"], "operating_analysis")
        self.assertEqual(record["file_format"], "xlsx")
        self.assertTrue(record["read_only_parse"])
        self.assertFalse(record["raw_layer_write_allowed"])
        self.assertRegex(record["file_hash"], r"^sha256:[a-f0-9]{64}$")
        self.assertEqual(record["source_file_private_ref"], "private://KMFA/S07-P1/source/SRC-FIN-OPERATING-001")
        self.assertEqual(len(record["sheets"]), 1)
        self.assertEqual(len(record["sheets"][0]["headers"]), 3)
        self.assertEqual(record["sheets"][0]["headers"][0]["column_ref"], "A")
        self.assertRegex(record["sheets"][0]["headers"][0]["source_header_hash"], r"^sha256:[a-f0-9]{64}$")

        public_payload = json.dumps(record, ensure_ascii=False, sort_keys=True)
        for header in headers:
            self.assertNotIn(header, public_payload)
        self.assertNotIn("original_filename", public_payload)
        self.assertNotIn("raw_value", public_payload)

    def test_default_finance_adapter_covers_required_categories_and_public_safe_candidates(self) -> None:
        manifest, candidates, field_report = build_default_finance_adapter(
            generated_at="2026-06-30T16:00:00+10:00"
        )
        validate_finance_adapter(manifest, candidates, field_report)

        self.assertEqual(set(REQUIRED_FINANCE_CATEGORIES), {
            "operating_analysis",
            "journal",
            "customer_aging",
            "cash",
            "tax",
            "invoice",
            "account",
            "loan",
            "r_and_d_expense",
        })
        self.assertEqual(set(manifest["finance_categories"]), set(REQUIRED_FINANCE_CATEGORIES))
        self.assertEqual(manifest["summary"]["source_category_count"], len(REQUIRED_FINANCE_CATEGORIES))
        self.assertGreaterEqual(manifest["summary"]["field_candidate_count"], len(REQUIRED_FINANCE_CATEGORIES))
        self.assertFalse(manifest["stage_scope"]["wps_scope_included"])
        self.assertFalse(manifest["stage_scope"]["redcircle_scope_included"])
        self.assertFalse(manifest["public_repo_safety"]["raw_business_values_committed"])
        self.assertFalse(manifest["public_repo_safety"]["source_header_plaintext_committed"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])

        candidate_payload = json.dumps(candidates, ensure_ascii=False, sort_keys=True)
        self.assertIn("source_header_hash", candidate_payload)
        self.assertIn("source_header_private_ref", candidate_payload)
        for forbidden in ("source_header_text", "raw_value", "normalized_value", "bank_account_number"):
            self.assertNotIn(forbidden, candidate_payload)

        categories_with_report = {record["finance_category"] for record in field_report}
        self.assertEqual(categories_with_report, set(REQUIRED_FINANCE_CATEGORIES))
        for record in field_report:
            self.assertEqual(record["record_type"], "finance_file_field_report")
            self.assertTrue(record["read_only_parse"])
            self.assertFalse(record["raw_layer_write_allowed"])
            self.assertIn(record["parse_status"], {"parsed_structure_from_xlsx", "requires_conversion_to_xlsx_or_csv"})


if __name__ == "__main__":
    unittest.main()
