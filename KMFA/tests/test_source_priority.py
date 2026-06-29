import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.source_priority import (
    SOURCE_PRIORITY_ORDER,
    append_metadata_record,
    build_cross_source_difference_queue_item,
    build_same_source_inconsistency_event,
    rank_source_candidate,
    sort_source_candidates,
)


class SourcePriorityTests(unittest.TestCase):
    def test_raw_upload_and_authorized_export_rank_before_processed_data(self) -> None:
        self.assertEqual(
            SOURCE_PRIORITY_ORDER,
            (
                "raw_upload",
                "authorized_export",
                "raw_extracted_value",
                "staging_structured_row",
                "canonical_fact",
                "derived_metric",
                "report_reference",
                "frontend_display",
                "processed_data",
            ),
        )

        candidates = [
            {"source_id": "SRC-frontend-99999999", "source_class": "frontend_display"},
            {"source_id": "SRC-report-88888888", "source_class": "report_reference"},
            {"source_id": "SRC-derived-77777777", "source_class": "derived_metric"},
            {"source_id": "SRC-fact-66666666", "source_class": "canonical_fact"},
            {"source_id": "SRC-staging-55555555", "source_class": "staging_structured_row"},
            {"source_id": "SRC-extracted-44444444", "source_class": "raw_extracted_value"},
            {"source_id": "SRC-processed-33333333", "source_class": "processed_data"},
            {"source_id": "SRC-raw-11111111", "source_class": "raw_upload"},
            {"source_id": "SRC-authorized-22222222", "source_class": "authorized_export"},
        ]

        ranked = sort_source_candidates(candidates)

        self.assertEqual([item["source_class"] for item in ranked], list(SOURCE_PRIORITY_ORDER))
        self.assertEqual(rank_source_candidate({"source_id": "SRC-processed-33333333", "source_class": "processed_data"})["priority_rank"], 90)
        self.assertEqual(rank_source_candidate({"source_id": "SRC-raw-11111111", "source_class": "raw_upload"})["priority_rank"], 10)
        self.assertEqual(rank_source_candidate({"source_id": "SRC-authorized-22222222", "source_class": "authorized_export"})["priority_rank"], 20)
        with self.assertRaises(ValueError):
            rank_source_candidate({"source_id": "SRC-unknown-44444444", "source_class": "manual_note"})

    def test_same_source_inconsistency_invalidates_cache_and_requests_rerun(self) -> None:
        event = build_same_source_inconsistency_event(
            source_id="SRC-sales-export-12345678",
            primary_ref="manifest:sha256-aaa",
            conflicting_ref="matrix:SCM-bbb",
            field_path="project_cost.total_amount",
            reason_code="same-source-reference-mismatch",
            event_time="2026-06-29T19:45:00+10:00",
            evidence_ref="unit-test",
        )

        self.assertEqual(event["record_type"], "source_priority_event")
        self.assertEqual(event["event_type"], "same_source_inconsistency")
        self.assertEqual(event["actions"], ["invalidate_derived_cache", "request_rerun"])
        self.assertEqual(event["target_layer"], "metadata")
        self.assertFalse(event["raw_layer_write_allowed"])
        self.assertFalse(event["raw_source_mutation_allowed"])
        self.assertRegex(event["event_id"], r"^SPE-20260629-194500-[a-f0-9]{12}$")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source_priority_events.jsonl"
            append_metadata_record(path, event)
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(records, [event])

    def test_cross_source_conflict_enters_difference_queue_without_auto_selection(self) -> None:
        item = build_cross_source_difference_queue_item(
            conflict_scope="project_cost.total_amount",
            source_refs=[
                {"source_id": "SRC-sales-export-12345678", "source_class": "authorized_export"},
                {"source_id": "SRC-pdf-import-87654321", "source_class": "raw_upload"},
            ],
            reason_code="cross-source-conflict",
            event_time="2026-06-29T19:46:00+10:00",
            evidence_ref="unit-test",
        )

        self.assertEqual(item["record_type"], "source_difference_queue_item")
        self.assertEqual(item["status"], "queued_for_manual_review")
        self.assertEqual(item["resolution_policy"], "manual_review_required")
        self.assertFalse(item["auto_selection_allowed"])
        self.assertIsNone(item["auto_selected_source_id"])
        self.assertEqual(item["target_layer"], "metadata")
        self.assertFalse(item["raw_layer_write_allowed"])
        self.assertEqual(
            [ref["source_class"] for ref in item["source_refs"]],
            ["raw_upload", "authorized_export"],
        )

    def test_direct_cli_entrypoint_outputs_priority_event_json(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "KMFA/tools/source_priority.py",
                "same-source-event",
                "--source-id",
                "SRC-sales-export-12345678",
                "--primary-ref",
                "manifest:sha256-aaa",
                "--conflicting-ref",
                "matrix:SCM-bbb",
                "--field-path",
                "project_cost.total_amount",
                "--reason-code",
                "same-source-reference-mismatch",
                "--event-time",
                "2026-06-29T19:45:00+10:00",
                "--evidence-ref",
                "unit-test",
            ],
            cwd=Path(__file__).resolve().parents[2],
            check=True,
            capture_output=True,
            text=True,
        )

        event = json.loads(result.stdout)
        self.assertEqual(event["record_type"], "source_priority_event")
        self.assertEqual(event["actions"], ["invalidate_derived_cache", "request_rerun"])


if __name__ == "__main__":
    unittest.main()
