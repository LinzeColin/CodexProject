import json
import unittest

from KMFA.tools.check_v014_s03_p2_source_check_matrix import validate_v014_s03_p2_source_check_matrix
from KMFA.tools.source_check_matrix import ALLOWED_STATUSES, REQUIRED_DIMENSIONS
from KMFA.tools.v014_s03_p2_source_check_matrix import build_v014_s03_p2_source_check_matrix


class V014S03P2SourceCheckMatrixTests(unittest.TestCase):
    def sample_public_register(self) -> dict:
        return {
            "source_package": {
                "public_source_package_id": "SRC-PKG-UNIT",
                "source_package_type": "local_raw_directory",
            },
            "public_file_records": [
                {
                    "public_file_id": "RAW-FILE-000001",
                    "file_format": "zip",
                    "extension": ".zip",
                    "container_type": "zip_archive",
                    "file_size_bytes": 100,
                    "size_bucket": "lt_1mb",
                    "private_manifest_record_ref": "private://unit/RAW-FILE-000001",
                    "path_status": "private_only",
                    "content_hash_status": "computed_private_only",
                },
                {
                    "public_file_id": "RAW-FILE-000002",
                    "file_format": "xlsx",
                    "extension": ".xlsx",
                    "container_type": "xlsx_unknown_magic",
                    "file_size_bytes": 200,
                    "size_bucket": "lt_1mb",
                    "private_manifest_record_ref": "private://unit/RAW-FILE-000002",
                    "path_status": "private_only",
                    "content_hash_status": "computed_private_only",
                },
            ],
        }

    def test_builds_public_safe_rows_and_metadata_events(self) -> None:
        result = build_v014_s03_p2_source_check_matrix(self.sample_public_register())
        rows = result["matrix_rows"]
        events = result["status_events"]

        self.assertEqual(len(rows), 2)
        self.assertEqual(len(events), 2)
        for row in rows:
            self.assertEqual(row["record_type"], "source_check_matrix_row")
            self.assertEqual(row["stage_phase"], "S03-P2")
            self.assertEqual(row["status"], "人工复核")
            self.assertEqual(row["allowed_statuses"], list(ALLOWED_STATUSES))
            for dimension in REQUIRED_DIMENSIONS:
                self.assertIn(dimension, row)
            public_text = json.dumps(row, ensure_ascii=False)
            self.assertNotIn("content_sha256", public_text)
            self.assertNotIn("relative_path", public_text)
            self.assertNotIn("original_filename", public_text)
            self.assertFalse(row["raw_layer_write_allowed"])
            self.assertFalse(row["raw_source_mutation_allowed"])
            self.assertFalse(row["raw_filename_committed"])
            self.assertFalse(row["raw_hash_committed"])

        for event in events:
            self.assertEqual(event["target_layer"], "metadata")
            self.assertTrue(event["append_only"])
            self.assertIsNone(event["previous_status"])
            self.assertIn(event["new_status"], ALLOWED_STATUSES)
            self.assertFalse(event["raw_layer_write_allowed"])
            self.assertFalse(event["raw_source_mutation_allowed"])

    def test_repository_evidence_validator_passes(self) -> None:
        manifest = validate_v014_s03_p2_source_check_matrix()
        self.assertEqual(manifest["phase_id"], "S03-P2")
        self.assertEqual(manifest["source_check_matrix_summary"]["matrix_row_count"], 5)
        self.assertEqual(manifest["source_check_matrix_summary"]["status_event_count"], 5)
        self.assertEqual(manifest["release_state"]["current_data_quality_grade"], "Q2")
        self.assertFalse(manifest["phase_scope"]["github_upload_performed"])


if __name__ == "__main__":
    unittest.main()
