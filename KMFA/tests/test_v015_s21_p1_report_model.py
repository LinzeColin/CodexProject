from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s21_p1_report_model as model


class ReportModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "report_models.jsonl"
        self.journal = model.ReportModelJournal(self.path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create(self, **overrides):
        value = {
            "company_id": "demo-north",
            "period_kind": "MONTHLY",
            "period_key": "2026-07",
            "source_bindings": model.default_source_bindings(),
            "formula_bindings": model.default_formula_bindings(),
            "created_by": "测试负责人",
            "idempotency_key": "unit-create-001",
            "recorded_at": "2026-07-17T00:00:00+00:00",
        }
        value.update(overrides)
        return self.journal.create(**value)

    def test_all_period_kinds_have_exact_closed_ranges(self) -> None:
        cases = {
            ("WEEKLY", "2026-W29"): ("2026-07-13", "2026-07-19"),
            ("MONTHLY", "2026-02"): ("2026-02-01", "2026-02-28"),
            ("QUARTERLY", "2026-Q3"): ("2026-07-01", "2026-09-30"),
            ("HALF_YEAR", "2026-H1"): ("2026-01-01", "2026-06-30"),
            ("YEARLY", "2026"): ("2026-01-01", "2026-12-31"),
        }
        for (kind, key), expected in cases.items():
            with self.subTest(kind=kind):
                period = model.period_contract(kind, key)
                self.assertEqual((period["start_date"], period["end_date"]), expected)
                self.assertTrue(period["period_label_zh"])

    def test_invalid_periods_fail_closed(self) -> None:
        for kind, key in (("MONTHLY", "2026-13"), ("WEEKLY", "2026-W99"), ("QUARTERLY", "2026-Q5"), ("YEARLY", "26")):
            with self.subTest(kind=kind, key=key), self.assertRaises(model.ReportModelError):
                model.period_contract(kind, key)

    def test_required_sections_are_split_by_audience(self) -> None:
        sections = model.section_contract()
        self.assertEqual([row["title_zh"] for row in sections], ["经营摘要", "项目经营", "财务与资金", "税务与政策", "重点事项", "专业附表"])
        self.assertEqual(sum(row["audience"] == "MANAGEMENT" for row in sections), 5)
        self.assertEqual(sum(row["audience"] == "PROFESSIONAL" for row in sections), 1)
        self.assertTrue(all(not row["backend_check_board_content_allowed"] and not row["technical_log_content_allowed"] for row in sections))

    def test_complete_and_incomplete_trust_copy(self) -> None:
        complete = model.trust_and_limitations(model.default_source_bindings())
        incomplete = model.trust_and_limitations(model.default_source_bindings(missing=("finance_and_funds",), pending=("tax_and_policy",)))
        self.assertTrue(complete["complete_report_claim_allowed"])
        self.assertFalse(incomplete["complete_report_claim_allowed"])
        self.assertIn("不能称为完整报告", incomplete["explanation_zh"])
        self.assertEqual((incomplete["missing_input_count"], incomplete["pending_input_count"]), (1, 1))
        self.assertEqual(incomplete["technical_grade_abbreviation_count"], 0)

    def test_create_binds_inputs_formulas_and_sections(self) -> None:
        report = self.create()
        self.assertEqual(report["report_version_id"], "REPORT-DEMO-NORTH-MONTHLY-2026-07-V0001")
        self.assertEqual((len(report["source_bindings"]), len(report["formula_bindings"])), (6, 2))
        self.assertTrue(report["source_binding_fingerprint"].startswith("sha256:"))
        self.assertTrue(report["formula_binding_fingerprint"].startswith("sha256:"))
        self.assertEqual((report["management_section_count"], report["professional_section_count"]), (5, 1))
        self.assertFalse(report["history_overwrite_allowed"])

    def test_same_period_requires_revision_and_preserves_first(self) -> None:
        first = self.create()
        with self.assertRaisesRegex(model.ReportModelError, "修订"):
            self.create(idempotency_key="unit-overwrite-002")
        revision = self.journal.revise(
            first["report_version_id"], revision_reason_zh="补充经营说明并保留初版",
            created_by="测试负责人", idempotency_key="unit-revise-001",
            recorded_at="2026-07-17T00:01:00+00:00",
        )
        self.assertEqual(revision["version_number"], 2)
        self.assertEqual(revision["supersedes_version_id"], first["report_version_id"])
        self.assertEqual(self.journal.get(first["report_version_id"])["event_hash"], first["event_hash"])
        self.assertEqual(self.journal.list()["report_version_count"], 2)

    def test_create_and_revision_are_idempotent(self) -> None:
        first = self.create()
        self.assertEqual(self.create()["event_hash"], first["event_hash"])
        revision = self.journal.revise(
            first["report_version_id"], revision_reason_zh="补充经营说明并保留初版",
            created_by="测试负责人", idempotency_key="unit-revise-001",
        )
        retry = self.journal.revise(
            first["report_version_id"], revision_reason_zh="补充经营说明并保留初版",
            created_by="测试负责人", idempotency_key="unit-revise-001",
        )
        self.assertEqual(retry["event_hash"], revision["event_hash"])
        self.assertEqual(self.journal.list()["report_version_count"], 2)

    def test_stale_revision_and_idempotency_conflict_fail(self) -> None:
        first = self.create()
        self.journal.revise(
            first["report_version_id"], revision_reason_zh="补充经营说明并保留初版",
            created_by="测试负责人", idempotency_key="unit-revise-001",
        )
        with self.assertRaisesRegex(model.ReportModelError, "最新版本"):
            self.journal.revise(
                first["report_version_id"], revision_reason_zh="再次从旧版本错误修订",
                created_by="测试负责人", idempotency_key="unit-revise-002",
            )
        with self.assertRaises(model.ReportModelError) as context:
            self.journal.revise(
                first["report_version_id"], revision_reason_zh="不同内容复用同一请求编号",
                created_by="测试负责人", idempotency_key="unit-revise-001",
            )
        self.assertEqual(context.exception.code, "IDEMPOTENCY_CONFLICT")

    def test_missing_source_cannot_claim_available_version(self) -> None:
        broken = model.default_source_bindings()
        broken[0]["version_ref"] = None
        with self.assertRaises(model.ReportModelError) as context:
            self.create(source_bindings=broken)
        self.assertEqual(context.exception.code, "SOURCE_VERSION_REQUIRED")

    def test_audience_payload_hides_backend_and_technical_log(self) -> None:
        report = self.create()
        management = self.journal.audience(report["report_version_id"], "MANAGEMENT")
        professional = self.journal.audience(report["report_version_id"], "PROFESSIONAL")
        self.assertEqual((management["section_count"], professional["section_count"]), (5, 1))
        self.assertEqual(management["data_check_board_backend_content_count"], 0)
        self.assertEqual(management["technical_log_content_count"], 0)
        visible = json.dumps(management["sections"], ensure_ascii=False).casefold()
        self.assertFalse(any(term in visible for term in model.VISIBLE_TECHNICAL_TERMS))

    def test_history_tamper_is_rejected(self) -> None:
        self.create()
        row = json.loads(self.path.read_text(encoding="utf-8"))
        row["period"]["period_key"] = "2026-08"
        self.path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        with self.assertRaises(model.ReportModelError) as context:
            self.journal.read()
        self.assertEqual(context.exception.code, "HISTORY_CORRUPTED")

    def test_p2_p3_and_external_actions_are_out_of_scope(self) -> None:
        report = self.create()
        self.assertFalse(report["html_generation_performed"])
        self.assertFalse(report["pdf_generation_performed"])
        self.assertFalse(report["spreadsheet_generation_performed"])
        self.assertFalse(report["approval_or_publication_performed"])

    def test_public_verification_is_complete(self) -> None:
        result = model.verify_phase()
        self.assertEqual((result["status"], result["public_check_count"], result["public_check_failed_count"]), ("PASS", 55, 0))


if __name__ == "__main__":
    unittest.main()
