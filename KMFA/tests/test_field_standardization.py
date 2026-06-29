import json
import subprocess
import sys
import unittest

from KMFA.tools.field_standardization import (
    CANONICAL_FIELDS,
    FieldStandardizationError,
    build_mapping_record,
    resolve_field_alias,
    standardize_date,
    standardize_period,
    standardize_record,
)


SOURCE_ID = "SRC-finance-ledger-a1b2c3d4"
IMPORT_RUN_ID = "IMP-20260629-181500-finance-a1b2c3d4"
MAPPING_VERSION = "MAP-SRC-finance-ledger-a1b2c3d4-v0.1.0"
EVIDENCE_REF = "KMFA/stage_artifacts/S04_P2_field_standardization/human/test_results.md"


class FieldStandardizationTests(unittest.TestCase):
    def test_standardizes_date_period_identity_and_contract_fields(self) -> None:
        row = {
            "日期": "2026年6月29日",
            "所属期间": "2026年6月",
            "主体": " 武汉  开明 ",
            "项目名称": " A 项目 ",
            "客户": " 客户A ",
            "合同号": " kmfa - 2026 - 001 ",
        }
        result = standardize_record(
            row,
            source_id=SOURCE_ID,
            import_run_id=IMPORT_RUN_ID,
            mapping_version=MAPPING_VERSION,
            evidence_ref=EVIDENCE_REF,
            event_time="2026-06-29T22:45:00+10:00",
        )
        fields = result["standardized_fields"]
        self.assertEqual(fields["document_date"], "2026-06-29")
        self.assertEqual(fields["period_month"], "2026-06")
        self.assertEqual(fields["company_entity"], "武汉 开明")
        self.assertEqual(fields["project_name"], "A 项目")
        self.assertEqual(fields["counterparty"], "客户A")
        self.assertEqual(fields["contract_number"], "KMFA-2026-001")
        self.assertTrue(result["quality_passed"])
        self.assertEqual(result["quality_statuses"], [])

    def test_alias_dictionary_maps_chinese_headers_to_canonical_fields(self) -> None:
        self.assertEqual(resolve_field_alias("客户/对手方"), "counterparty")
        self.assertEqual(resolve_field_alias("合同编号"), "contract_number")
        self.assertEqual(resolve_field_alias("会计期间"), "period_month")
        record = build_mapping_record(
            source_id=SOURCE_ID,
            mapping_version=MAPPING_VERSION,
            source_field_alias="工程名称",
            evidence_ref=EVIDENCE_REF,
        )
        self.assertEqual(record["canonical_field"], "project_name")
        self.assertEqual(record["canonical_field_label_zh"], "项目名称")
        self.assertFalse(record["raw_layer_write_allowed"])
        self.assertIn("source_field_alias_hash", record)

    def test_missing_fields_enter_quality_status_without_silent_skip(self) -> None:
        result = standardize_record(
            {"日期": "20260629", "期间": "202606"},
            source_id=SOURCE_ID,
            import_run_id=IMPORT_RUN_ID,
            mapping_version=MAPPING_VERSION,
            evidence_ref=EVIDENCE_REF,
            event_time="2026-06-29T22:45:00+10:00",
        )
        missing_fields = {status["canonical_field"] for status in result["quality_statuses"]}
        self.assertEqual(missing_fields, set(CANONICAL_FIELDS) - {"document_date", "period_month"})
        for status in result["quality_statuses"]:
            self.assertEqual(status["record_type"], "field_quality_status")
            self.assertEqual(status["status"], "field_missing_requires_review")
            self.assertEqual(status["quality_grade"], "Q1")
            self.assertFalse(status["field_skipped_silently"])
            self.assertFalse(status["raw_layer_write_allowed"])
            self.assertNotIn("raw_value", status)
            self.assertNotIn("original_value", status)
        self.assertFalse(result["quality_passed"])

    def test_invalid_dates_and_blank_values_are_quality_statuses(self) -> None:
        result = standardize_record(
            {
                "日期": "2026-13-01",
                "期间": "2026-00",
                "主体": "-",
                "项目": "项目A",
                "客户": "客户A",
                "合同编号": "HT-001",
            },
            source_id=SOURCE_ID,
            import_run_id=IMPORT_RUN_ID,
            mapping_version=MAPPING_VERSION,
            evidence_ref=EVIDENCE_REF,
            event_time="2026-06-29T22:45:00+10:00",
        )
        issues = {(status["canonical_field"], status["issue_type"]) for status in result["quality_statuses"]}
        self.assertIn(("document_date", "invalid_field_value"), issues)
        self.assertIn(("period_month", "invalid_field_value"), issues)
        self.assertIn(("company_entity", "missing_required_field"), issues)
        self.assertFalse(result["quality_passed"])
        with self.assertRaises(FieldStandardizationError):
            standardize_date("2026-13-01")
        with self.assertRaises(FieldStandardizationError):
            standardize_period("2026-00")

    def test_cli_entrypoints(self) -> None:
        alias_result = subprocess.run(
            [
                sys.executable,
                "KMFA/tools/field_standardization.py",
                "map-alias",
                "--source-id",
                SOURCE_ID,
                "--mapping-version",
                MAPPING_VERSION,
                "--source-field-alias",
                "客户名称",
                "--evidence-ref",
                EVIDENCE_REF,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(alias_result.stdout)["canonical_field"], "counterparty")

        row_result = subprocess.run(
            [
                sys.executable,
                "KMFA/tools/field_standardization.py",
                "standardize-row",
                "--row-json",
                json.dumps(
                    {
                        "日期": "2026/6/29",
                        "期间": "2026-06",
                        "公司主体": "主体A",
                        "项目名称": "项目A",
                        "对手方": "客户A",
                        "合同编号": "ht-001",
                    },
                    ensure_ascii=False,
                ),
                "--source-id",
                SOURCE_ID,
                "--import-run-id",
                IMPORT_RUN_ID,
                "--mapping-version",
                MAPPING_VERSION,
                "--evidence-ref",
                EVIDENCE_REF,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(row_result.stdout)
        self.assertTrue(payload["quality_passed"])
        self.assertEqual(payload["standardized_fields"]["contract_number"], "HT-001")


if __name__ == "__main__":
    unittest.main()
