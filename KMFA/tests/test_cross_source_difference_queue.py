import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.cross_source_difference_queue import (
    CrossSourceDifferenceQueueError,
    build_pdf_excel_difference_queue_item,
    evaluate_report_grade_gate,
    write_queue_jsonl,
)


class CrossSourceDifferenceQueueTests(unittest.TestCase):
    def _pdf_ref(self) -> dict[str, str]:
        return {
            "source_id": "SRC-S06P2-PDF-SYNTHETIC",
            "source_type": "pdf",
            "source_class": "raw_upload",
            "source_anchor_ref": "sha256:synthetic-pdf-anchor",
        }

    def _excel_ref(self) -> dict[str, str]:
        return {
            "source_id": "SRC-S06P2-EXCEL-SYNTHETIC",
            "source_type": "excel",
            "source_class": "authorized_export",
            "source_anchor_ref": "sha256:synthetic-excel-anchor",
        }

    def test_pdf_excel_same_project_conflict_enters_difference_queue(self) -> None:
        item = build_pdf_excel_difference_queue_item(
            project_ref="SYN-PROJECT-S06P2-001",
            field="contract_amount_cents",
            pdf_source_ref=self._pdf_ref(),
            excel_source_ref=self._excel_ref(),
            pdf_value_cents=10000,
            excel_value_cents=9999,
            event_time="2026-06-30T14:00:00+10:00",
            evidence_ref="unit-test",
        )

        self.assertEqual(item["record_type"], "cross_source_difference_queue_item")
        self.assertEqual(item["schema_version"], "kmfa.cross_source_difference_queue.v1")
        self.assertEqual(item["stage_phase"], "S06-P2")
        self.assertEqual(item["status"], "queued_for_manual_review")
        self.assertEqual(item["project_ref"], "SYN-PROJECT-S06P2-001")
        self.assertEqual(item["field"], "contract_amount_cents")
        self.assertEqual(item["difference_cents"], 1)
        self.assertEqual({ref["source_type"] for ref in item["source_refs"]}, {"pdf", "excel"})

    def test_no_auto_correction_average_rounding_or_auto_selection(self) -> None:
        item = build_pdf_excel_difference_queue_item(
            project_ref="SYN-PROJECT-S06P2-002",
            field="total_expense_cents",
            pdf_source_ref=self._pdf_ref(),
            excel_source_ref=self._excel_ref(),
            pdf_value_cents=20000,
            excel_value_cents=19999,
            event_time="2026-06-30T14:01:00+10:00",
            evidence_ref="unit-test",
        )

        self.assertFalse(item["auto_correction_allowed"])
        self.assertFalse(item["averaging_allowed"])
        self.assertFalse(item["rounding_mask_allowed"])
        self.assertFalse(item["auto_selection_allowed"])
        self.assertIsNone(item["auto_selected_source_id"])
        self.assertIsNone(item["resolved_value_cents"])
        self.assertEqual(item["resolution_policy"], "manual_review_required")

    def test_unclosed_difference_blocks_report_grade_a(self) -> None:
        item = build_pdf_excel_difference_queue_item(
            project_ref="SYN-PROJECT-S06P2-003",
            field="gross_profit_cents",
            pdf_source_ref=self._pdf_ref(),
            excel_source_ref=self._excel_ref(),
            pdf_value_cents=30000,
            excel_value_cents=29999,
            event_time="2026-06-30T14:02:00+10:00",
            evidence_ref="unit-test",
        )

        gate = evaluate_report_grade_gate([item])

        self.assertFalse(gate["report_grade_a_allowed"])
        self.assertEqual(gate["maximum_report_grade"], "B")
        self.assertEqual(gate["hard_block_reason"], "unresolved_critical_difference")
        self.assertEqual(gate["blocking_queue_ids"], [item["queue_id"]])

    def test_rejects_float_money_and_non_pdf_excel_sources(self) -> None:
        bad_float = json.loads("100.5")
        with self.assertRaises(CrossSourceDifferenceQueueError):
            build_pdf_excel_difference_queue_item(
                project_ref="SYN-PROJECT-S06P2-004",
                field="contract_amount_cents",
                pdf_source_ref=self._pdf_ref(),
                excel_source_ref=self._excel_ref(),
                pdf_value_cents=bad_float,
                excel_value_cents=10050,
                event_time="2026-06-30T14:03:00+10:00",
                evidence_ref="unit-test",
            )

        bad_excel_ref = dict(self._excel_ref(), source_type="csv")
        with self.assertRaises(CrossSourceDifferenceQueueError):
            build_pdf_excel_difference_queue_item(
                project_ref="SYN-PROJECT-S06P2-004",
                field="contract_amount_cents",
                pdf_source_ref=self._pdf_ref(),
                excel_source_ref=bad_excel_ref,
                pdf_value_cents=10000,
                excel_value_cents=9999,
                event_time="2026-06-30T14:03:00+10:00",
                evidence_ref="unit-test",
            )

    def test_cli_writes_public_safe_queue_and_report_grade_gate_evidence(self) -> None:
        root = Path(__file__).resolve().parents[2]
        fixture = {
            "project_ref": "SYN-PROJECT-S06P2-005",
            "field": "contract_amount_cents",
            "pdf_source_ref": self._pdf_ref(),
            "excel_source_ref": self._excel_ref(),
            "pdf_value_cents": 10000,
            "excel_value_cents": 9999,
            "event_time": "2026-06-30T14:04:00+10:00",
            "evidence_ref": "unit-test",
        }

        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            queue_path = Path(tmp) / "queue.jsonl"
            gate_path = Path(tmp) / "gate.json"
            fixture_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "KMFA/tools/cross_source_difference_queue.py",
                    "--fixture",
                    str(fixture_path),
                    "--queue-jsonl",
                    str(queue_path),
                    "--gate-json",
                    str(gate_path),
                ],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            queue_items = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]
            gate = json.loads(gate_path.read_text(encoding="utf-8"))

        self.assertIn('"status": "queued_for_manual_review"', result.stdout)
        self.assertEqual(len(queue_items), 1)
        self.assertEqual(queue_items[0]["difference_cents"], 1)
        self.assertFalse(gate["report_grade_a_allowed"])

    def test_write_queue_jsonl_rejects_auto_selection(self) -> None:
        item = build_pdf_excel_difference_queue_item(
            project_ref="SYN-PROJECT-S06P2-006",
            field="contract_amount_cents",
            pdf_source_ref=self._pdf_ref(),
            excel_source_ref=self._excel_ref(),
            pdf_value_cents=10000,
            excel_value_cents=9999,
            event_time="2026-06-30T14:05:00+10:00",
            evidence_ref="unit-test",
        )
        item["auto_selection_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CrossSourceDifferenceQueueError):
                write_queue_jsonl([item], Path(tmp) / "queue.jsonl")


if __name__ == "__main__":
    unittest.main()
