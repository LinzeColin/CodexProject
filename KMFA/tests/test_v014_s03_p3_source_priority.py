import unittest

from KMFA.tools.check_v014_s03_p3_source_priority import (
    DIFFERENCE_QUEUE_PATH,
    PRIORITY_RECORDS_PATH,
    SAME_SOURCE_EVENTS_PATH,
    read_jsonl,
    validate_v014_s03_p3_source_priority,
)


class TestV014S03P3SourcePriority(unittest.TestCase):
    def test_source_priority_public_safe_policy_lock(self) -> None:
        manifest = validate_v014_s03_p3_source_priority()
        summary = manifest["source_priority_summary"]

        self.assertEqual(manifest["stage_id"], "S03")
        self.assertEqual(manifest["phase_id"], "S03-P3")
        self.assertEqual(manifest["status"], "completed_validated_local_only_no_go_upload_deferred")
        self.assertTrue(manifest["dependency"]["dependency_validated"])
        self.assertEqual(summary["source_priority_record_count"], 5)
        self.assertEqual(summary["source_priority_order_count"], 9)
        self.assertEqual(
            summary["source_priority_order"],
            [
                "raw_upload",
                "authorized_export",
                "raw_extracted_value",
                "staging_structured_row",
                "canonical_fact",
                "derived_metric",
                "report_reference",
                "frontend_display",
                "processed_data",
            ],
        )
        self.assertEqual(summary["same_source_inconsistency_actions"], ["invalidate_derived_cache", "request_rerun"])
        self.assertEqual(summary["same_source_policy_event_count"], 1)
        self.assertFalse(summary["same_source_cache_reuse_allowed"])
        self.assertEqual(summary["cross_source_difference_queue_item_count"], 1)
        self.assertEqual(summary["cross_source_resolution_policy"], "manual_review_required")
        self.assertFalse(summary["auto_selection_allowed"])
        self.assertTrue(summary["policy_fixture_only"])
        self.assertEqual(summary["business_conflict_observed_count"], 0)
        self.assertFalse(manifest["phase_scope"]["raw_root_read_performed_by_this_phase"])
        self.assertFalse(manifest["phase_scope"]["github_upload_performed"])
        self.assertEqual(manifest["next_recommended_phase"], "S03_STAGE_REVIEW")

    def test_priority_records_keep_processed_data_below_raw_and_authorized(self) -> None:
        records = read_jsonl(PRIORITY_RECORDS_PATH)
        self.assertEqual(len(records), 5)
        for record in records:
            self.assertEqual(record["source_check_status"], "人工复核")
            self.assertEqual(record["highest_priority_source_class"], "raw_upload")
            self.assertEqual(
                [candidate["source_class"] for candidate in record["candidate_refs"]],
                ["raw_upload", "authorized_export", "processed_data"],
            )
            self.assertEqual([candidate["priority_rank"] for candidate in record["candidate_refs"]], [10, 20, 90])
            self.assertTrue(record["processed_data_rank_after_raw_or_authorized"])
            self.assertTrue(record["manual_review_required"])
            self.assertFalse(record["auto_selection_allowed"])
            self.assertFalse(record["raw_root_read_performed_by_this_phase"])
            self.assertFalse(record["raw_layer_write_allowed"])
            self.assertFalse(record["raw_source_mutation_allowed"])
            self.assertFalse(record["raw_filename_committed"])
            self.assertFalse(record["raw_hash_committed"])
            self.assertFalse(record["raw_or_normalized_value_committed"])
            self.assertFalse(record["business_value_committed"])

    def test_same_source_and_cross_source_records_are_policy_fixtures_only(self) -> None:
        same_source_events = read_jsonl(SAME_SOURCE_EVENTS_PATH)
        difference_queue = read_jsonl(DIFFERENCE_QUEUE_PATH)

        self.assertEqual(len(same_source_events), 1)
        event = same_source_events[0]
        self.assertEqual(event["event_type"], "same_source_inconsistency")
        self.assertEqual(event["actions"], ["invalidate_derived_cache", "request_rerun"])
        self.assertFalse(event["cache_reuse_allowed"])
        self.assertTrue(event["policy_fixture_only"])
        self.assertFalse(event["business_conflict_observed"])
        self.assertFalse(event["raw_layer_write_allowed"])
        self.assertFalse(event["raw_source_mutation_allowed"])

        self.assertEqual(len(difference_queue), 1)
        queue_item = difference_queue[0]
        self.assertEqual(queue_item["status"], "queued_for_manual_review")
        self.assertEqual(queue_item["resolution_policy"], "manual_review_required")
        self.assertFalse(queue_item["auto_selection_allowed"])
        self.assertIsNone(queue_item["auto_selected_source_id"])
        self.assertTrue(queue_item["policy_fixture_only"])
        self.assertFalse(queue_item["business_conflict_observed"])
        self.assertEqual([ref["source_class"] for ref in queue_item["source_refs"]], ["raw_upload", "authorized_export"])


if __name__ == "__main__":
    unittest.main()
