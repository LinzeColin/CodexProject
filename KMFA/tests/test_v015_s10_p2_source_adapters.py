from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s10_p1_general_import as general_import
from KMFA.tools import v015_s10_p2_source_adapters as adapters


class SourceAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inspection = {
            "inspection_status": "SAFE_TO_PREVIEW",
            "file_hash": "sha256:" + "a" * 64,
            "format_code": "EXCEL_XLSX",
            "raw_root_access_count": 0,
        }
        self.account_bindings = {
            "ACCOUNT::A001": {"entity_id": "ENTITY::A001", "bank_id": "BANK::A001"},
            "ACCOUNT::B001": {"entity_id": "ENTITY::B001", "bank_id": "BANK::B001"},
        }

    @staticmethod
    def sheet(template_id: str, *, sheet_id: str = "SHEET-1", context=None):
        template = adapters.TEMPLATE_BY_ID[template_id]
        headers = [field.aliases[0] for field in template.fields]
        row = {header: f"测试值-{index}" for index, header in enumerate(headers, start=1)}
        supplied_context = {"entity_id": "ENTITY::A001", "period": "2026-06"}
        if template.source_system == "BANK":
            supplied_context.update({"bank_id": "BANK::A001", "account_id": "ACCOUNT::A001"})
        supplied_context.update(context or {})
        return {
            "sheet_id": sheet_id,
            "template_id": template.template_id,
            "mapping_version": template.mapping_version,
            "headers": headers,
            "rows": [row],
            "context": supplied_context,
        }

    def test_registry_covers_exact_s10_p2_sources_and_templates(self) -> None:
        self.assertEqual(
            adapters.TEMPLATE_COUNTS,
            {"REDCIRCLE": 4, "KINGDEE": 4, "WPS": 4, "BANK": 1, "TAX_EINVOICE": 1, "CONTRACT_LEDGER": 1},
        )
        registry = adapters.template_registry_public_safe()
        self.assertEqual(registry["source_system_count"], 6)
        self.assertEqual(registry["adapter_template_count"], 15)
        self.assertEqual(registry["mapping_versioned_template_count"], 15)
        self.assertFalse(registry["automatic_login_allowed"])
        self.assertFalse(registry["live_connector_call_allowed"])

    def test_public_verification_has_42_real_passing_checks(self) -> None:
        result = adapters.public_verification()
        self.assertEqual(result["accounting"], {"total": 42, "passed": 42, "failed": 0})
        self.assertEqual({row["check_id"] for row in result["checks"]}, set(adapters.CHECK_IDS))
        self.assertTrue(all(row["status"] == "PASS" for row in result["checks"]))
        self.assertEqual(result["raw_root_access_count"], 0)

    def test_all_redcircle_and_kingdee_templates_adapt_explicit_samples(self) -> None:
        for template in adapters.TEMPLATES:
            if template.source_system not in {"REDCIRCLE", "KINGDEE"}:
                continue
            with self.subTest(template=template.template_id):
                result = adapters.adapt_workbook(
                    self.inspection,
                    source_system=template.source_system,
                    sheets=[self.sheet(template.template_id)],
                )
                self.assertEqual(result["adaptation_status"], "READY")
                self.assertEqual(result["adapted_record_count"], 1)
                self.assertEqual(result["records"][0]["mapping_version"], "1.0.0")

    def test_wps_bank_tax_and_contract_templates_preserve_hierarchy(self) -> None:
        for template in adapters.TEMPLATES:
            if template.source_system in {"REDCIRCLE", "KINGDEE"}:
                continue
            bindings = self.account_bindings if template.source_system == "BANK" else {}
            result = adapters.adapt_workbook(
                self.inspection,
                source_system=template.source_system,
                sheets=[self.sheet(template.template_id)],
                account_bindings=bindings,
            )
            record = result["records"][0]
            self.assertEqual(record["entity_id"], "ENTITY::A001")
            self.assertEqual(record["period"], "2026-06")
            self.assertFalse(record["source_mutation_performed"])

    def test_unknown_template_version_is_quarantined_without_guessing(self) -> None:
        sheet = self.sheet("kingdee.voucher.v1")
        sheet["mapping_version"] = "9.9.9"
        result = adapters.adapt_workbook(self.inspection, source_system="KINGDEE", sheets=[sheet])
        self.assertEqual(result["adaptation_status"], "QUARANTINED")
        self.assertEqual(result["quarantined_sheets"][0]["reason_code"], "UNSUPPORTED_MAPPING_VERSION")
        self.assertFalse(adapters.mapping_version_policy_public_safe()["guess_field_meaning_allowed"])

    def test_unknown_template_and_source_mismatch_are_quarantined(self) -> None:
        unknown = self.sheet("wps.collection.v1")
        unknown["template_id"] = "wps.unknown.v1"
        result = adapters.adapt_workbook(self.inspection, source_system="WPS", sheets=[unknown])
        self.assertEqual(result["quarantined_sheets"][0]["reason_code"], "UNKNOWN_TEMPLATE")
        mismatch = adapters.adapt_workbook(
            self.inspection,
            source_system="REDCIRCLE",
            sheets=[self.sheet("wps.collection.v1")],
        )
        self.assertEqual(mismatch["quarantined_sheets"][0]["reason_code"], "SOURCE_SYSTEM_TEMPLATE_MISMATCH")

    def test_missing_and_ambiguous_headers_fail_closed(self) -> None:
        template = adapters.TEMPLATE_BY_ID["redcircle.collection.v1"]
        missing = self.sheet(template.template_id)
        missing_header = template.fields[0].aliases[0]
        missing["headers"].remove(missing_header)
        missing["rows"][0].pop(missing_header)
        result = adapters.adapt_workbook(self.inspection, source_system="REDCIRCLE", sheets=[missing])
        self.assertEqual(result["quarantined_sheets"][0]["reason_code"], "REQUIRED_SOURCE_FIELD_MISSING")

        ambiguous = self.sheet(template.template_id)
        second_alias = template.fields[0].aliases[1]
        ambiguous["headers"].append(second_alias)
        ambiguous["rows"][0][second_alias] = "另一个测试日期"
        result = adapters.adapt_workbook(self.inspection, source_system="REDCIRCLE", sheets=[ambiguous])
        self.assertEqual(result["quarantined_sheets"][0]["reason_code"], "AMBIGUOUS_SOURCE_FIELD")

    def test_unknown_header_is_not_guessed_and_only_hash_is_in_public_summary(self) -> None:
        sheet = self.sheet("kingdee.report.v1")
        sheet["headers"].append("未经登记的列")
        sheet["rows"][0]["未经登记的列"] = "不应自动映射"
        result = adapters.adapt_workbook(self.inspection, source_system="KINGDEE", sheets=[sheet])
        summary = result["adapted_sheets"][0]["mapping_summary"]
        self.assertEqual(summary["unmapped_header_count"], 1)
        self.assertEqual(len(summary["unmapped_header_hashes"]), 1)
        self.assertFalse(summary["field_meaning_guessed"])
        self.assertNotIn("未经登记的列", str(summary))

    def test_multi_sheet_and_multi_entity_are_supported(self) -> None:
        result = adapters.adapt_workbook(
            self.inspection,
            source_system="WPS",
            sheets=[
                self.sheet("wps.collection.v1", sheet_id="SHEET-A"),
                self.sheet("wps.collection.v1", sheet_id="SHEET-B", context={"entity_id": "ENTITY::B001"}),
            ],
        )
        self.assertEqual(result["adapted_sheet_count"], 2)
        self.assertEqual(result["adapted_record_count"], 2)
        self.assertEqual({row["entity_id"] for row in result["records"]}, {"ENTITY::A001", "ENTITY::B001"})

    def test_multi_bank_multi_account_bindings_are_checked(self) -> None:
        result = adapters.adapt_workbook(
            self.inspection,
            source_system="BANK",
            sheets=[
                self.sheet("bank.statement.v1", sheet_id="BANK-A"),
                self.sheet(
                    "bank.statement.v1",
                    sheet_id="BANK-B",
                    context={"entity_id": "ENTITY::B001", "bank_id": "BANK::B001", "account_id": "ACCOUNT::B001"},
                ),
            ],
            account_bindings=self.account_bindings,
        )
        self.assertEqual({row["bank_id"] for row in result["records"]}, {"BANK::A001", "BANK::B001"})
        self.assertEqual({row["account_id"] for row in result["records"]}, {"ACCOUNT::A001", "ACCOUNT::B001"})

    def test_unknown_or_wrong_account_subject_is_quarantined(self) -> None:
        unknown = self.sheet("bank.statement.v1", context={"account_id": "ACCOUNT::MISSING"})
        result = adapters.adapt_workbook(
            self.inspection, source_system="BANK", sheets=[unknown], account_bindings=self.account_bindings
        )
        self.assertEqual(result["quarantined_sheets"][0]["reason_code"], "ACCOUNT_SUBJECT_UNKNOWN")
        wrong = self.sheet("bank.statement.v1", context={"entity_id": "ENTITY::B001"})
        result = adapters.adapt_workbook(
            self.inspection, source_system="BANK", sheets=[wrong], account_bindings=self.account_bindings
        )
        self.assertEqual(result["quarantined_sheets"][0]["reason_code"], "ACCOUNT_SUBJECT_BINDING_MISMATCH")

    def test_bad_sheet_and_bad_row_are_isolated(self) -> None:
        good = self.sheet("wps.deposit.v1", sheet_id="GOOD")
        bad = self.sheet("wps.deposit.v1", sheet_id="BAD")
        bad["mapping_version"] = "2.0.0"
        result = adapters.adapt_workbook(self.inspection, source_system="WPS", sheets=[good, bad])
        self.assertEqual(result["adapted_record_count"], 1)
        self.assertEqual(result["quarantined_sheet_count"], 1)

        bad_row = copy.deepcopy(good["rows"][0])
        bad_row[good["headers"][0]] = ""
        good["rows"].append(bad_row)
        result = adapters.adapt_workbook(self.inspection, source_system="WPS", sheets=[good])
        self.assertEqual(result["adapted_record_count"], 1)
        self.assertEqual(result["quarantined_row_count"], 1)

    def test_period_and_entity_context_are_required(self) -> None:
        for field, value, expected in (
            ("period", "", "PERIOD_REQUIRED"),
            ("period", "2026-13", "PERIOD_INVALID"),
            ("entity_id", "", "ENTITY_ID_REQUIRED"),
            ("entity_id", "ENTITY::UNKNOWN", "ENTITY_ID_UNCONFIRMED"),
        ):
            with self.subTest(field=field, value=value):
                sheet = self.sheet("contract-ledger.contract.v1", context={field: value})
                result = adapters.adapt_workbook(
                    self.inspection, source_system="CONTRACT_LEDGER", sheets=[sheet]
                )
                self.assertEqual(result["quarantined_sheets"][0]["reason_code"], expected)

    def test_s10_p1_real_synthetic_inspection_can_feed_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "synthetic.csv"
            path.write_text("项目编号,项目名称\nP-001,测试项目\n", encoding="utf-8")
            inspection = general_import.inspect_file(path)
            result = adapters.adapt_workbook(
                inspection,
                source_system="REDCIRCLE",
                sheets=[self.sheet("redcircle.operating.v1")],
            )
        self.assertEqual(result["adaptation_status"], "READY")
        self.assertEqual(result["format_code"], "CSV")
        self.assertEqual(result["raw_root_access_count"], 0)

    def test_adapter_does_not_mutate_inputs_or_perform_external_actions(self) -> None:
        sheet = self.sheet("tax-einvoice.invoice.v1")
        before = copy.deepcopy(sheet)
        result = adapters.adapt_workbook(
            self.inspection,
            source_system="TAX_EINVOICE",
            sheets=[sheet],
        )
        self.assertEqual(sheet, before)
        self.assertFalse(result["automatic_login_performed"])
        self.assertEqual(result["live_connector_call_count"], 0)
        self.assertEqual(result["credential_read_count"], 0)
        self.assertFalse(result["source_mutation_performed"])
        self.assertFalse(result["business_execution_performed"])


if __name__ == "__main__":
    unittest.main()
