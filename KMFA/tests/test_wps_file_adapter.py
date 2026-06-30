import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from KMFA.tools.wps_file_adapter import (
    REQUIRED_WPS_EXPORT_TYPES,
    build_default_wps_adapter,
    classify_wps_file,
    parse_xlsx_structure,
    validate_wps_adapter,
)


def write_minimal_xlsx(path: Path, headers: list[str]) -> None:
    cells = []
    for index, value in enumerate(headers, start=1):
        column = chr(ord("A") + index - 1)
        cells.append(f'<c r="{column}1" t="inlineStr"><is><t>{value}</t></is></c>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData><row r="1">'
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
            '<sheets><sheet name="Synthetic WPS Export" sheetId="1" r:id="rId1"/></sheets></workbook>',
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


class WpsFileAdapterTests(unittest.TestCase):
    def test_parse_xlsx_structure_keeps_only_hashes_and_private_refs(self) -> None:
        headers = ["SYNTHETIC_WPS_HEADER_ALPHA", "SYNTHETIC_WPS_HEADER_BETA"]
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "synthetic_wps_export.xlsx"
            write_minimal_xlsx(workbook_path, headers)

            record = parse_xlsx_structure(
                workbook_path,
                source_ref="SRC-WPS-COLLECTION-001",
                export_type="collection",
                private_source_ref="private://KMFA/S07-P2/source/SRC-WPS-COLLECTION-001",
            )

        self.assertEqual(record["record_type"], "wps_file_readonly_structure")
        self.assertEqual(record["schema_version"], "kmfa.wps_file_structure.v1")
        self.assertEqual(record["stage_phase"], "S07-P2")
        self.assertEqual(record["export_type"], "collection")
        self.assertEqual(record["file_format"], "xlsx")
        self.assertTrue(record["read_only_parse"])
        self.assertFalse(record["raw_layer_write_allowed"])
        self.assertRegex(record["file_hash"], r"^sha256:[a-f0-9]{64}$")
        self.assertEqual(len(record["sheets"][0]["headers"]), 2)
        self.assertRegex(record["sheets"][0]["headers"][0]["source_header_hash"], r"^sha256:[a-f0-9]{64}$")

        public_payload = json.dumps(record, ensure_ascii=False, sort_keys=True)
        for header in headers:
            self.assertNotIn(header, public_payload)
        for forbidden in ("original_filename", "source_header_text", "raw_value", "normalized_value"):
            self.assertNotIn(forbidden, public_payload)

    def test_default_wps_adapter_covers_required_exports_guidance_and_versioned_rules(self) -> None:
        manifest, mappings, conversion_guidance, field_report, rule_versions = build_default_wps_adapter(
            generated_at="2026-06-30T17:00:00+10:00"
        )
        validate_wps_adapter(manifest, mappings, conversion_guidance, field_report, rule_versions)

        self.assertEqual(
            set(REQUIRED_WPS_EXPORT_TYPES),
            {"collection", "receivable_aging", "production_project_status", "deposit"},
        )
        self.assertEqual(set(manifest["wps_export_types"]), set(REQUIRED_WPS_EXPORT_TYPES))
        self.assertEqual(manifest["summary"]["source_export_type_count"], len(REQUIRED_WPS_EXPORT_TYPES))
        self.assertGreaterEqual(manifest["summary"]["field_mapping_count"], len(REQUIRED_WPS_EXPORT_TYPES))
        self.assertFalse(manifest["stage_scope"]["finance_scope_included"])
        self.assertTrue(manifest["stage_scope"]["wps_scope_included"])
        self.assertFalse(manifest["stage_scope"]["redcircle_scope_included"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])

        guidance_by_type = {item["export_type"]: item for item in conversion_guidance}
        self.assertEqual(set(guidance_by_type), set(REQUIRED_WPS_EXPORT_TYPES))
        for item in conversion_guidance:
            self.assertEqual(item["native_wps_parse_status"], "requires_conversion_to_xlsx_or_csv")
            self.assertIn(".xlsx", item["operator_guidance"])
            self.assertIn(".csv", item["operator_guidance"])

        rule_payload = json.dumps(rule_versions, ensure_ascii=False, sort_keys=True)
        self.assertIn("MAP-SRC-kmfa-wps-file-adapter-s07p2-v0.1.0", rule_payload)
        self.assertEqual(rule_versions["active_mapping_rule_version"], "MAP-SRC-kmfa-wps-file-adapter-s07p2-v0.1.0")

        mapping_payload = json.dumps(mappings, ensure_ascii=False, sort_keys=True)
        self.assertIn("mapping_rule_version_id", mapping_payload)
        self.assertIn("source_header_hash", mapping_payload)
        self.assertIn("source_header_private_ref", mapping_payload)
        for forbidden in ("source_header_text", "raw_value", "normalized_value", "bank_account_number"):
            self.assertNotIn(forbidden, mapping_payload)

        self.assertEqual({record["export_type"] for record in field_report}, set(REQUIRED_WPS_EXPORT_TYPES))
        self.assertTrue(all(record["read_only_parse"] for record in field_report))
        self.assertFalse(any(record["raw_layer_write_allowed"] for record in field_report))

    def test_classifies_native_wps_as_conversion_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.et"
            path.write_bytes(b"synthetic-wps-native-content")
            plan = classify_wps_file(path, source_ref="SRC-WPS-COLLECTION-001", export_type="collection")

        self.assertEqual(plan["file_format"], "wps")
        self.assertEqual(plan["container_type"], "wps_native")
        self.assertEqual(plan["parse_status"], "requires_conversion_to_xlsx_or_csv")
        self.assertIn("WPS", plan["operator_guidance"])
        self.assertIn(".xlsx", plan["operator_guidance"])
        self.assertIn(".csv", plan["operator_guidance"])
        self.assertRegex(plan["file_hash"], r"^sha256:[a-f0-9]{64}$")
        self.assertNotIn("synthetic.et", json.dumps(plan, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
