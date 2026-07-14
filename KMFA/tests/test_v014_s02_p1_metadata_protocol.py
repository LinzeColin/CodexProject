import unittest

from KMFA.tools.check_v014_s02_p1_metadata_protocol import validate_v014_s02_p1_metadata_protocol


class TestV014S02P1MetadataProtocol(unittest.TestCase):
    def test_metadata_protocol_phase_is_closed_without_raw_inventory_or_upload(self) -> None:
        result = validate_v014_s02_p1_metadata_protocol()

        self.assertEqual(result["stage_id"], "S02")
        self.assertEqual(result["phase_id"], "S02-P1")
        self.assertEqual(result["metadata_protocol"]["required_directories"][0], "metadata/sources")
        self.assertEqual(len(result["metadata_protocol"]["required_directories"]), 7)
        self.assertEqual(
            result["metadata_protocol"]["required_identifiers"],
            ["import_run_id", "source_id", "file_hash", "formula_version", "mapping_version"],
        )
        self.assertTrue(result["phase_scope"]["metadata_protocol_only"])
        self.assertFalse(result["phase_scope"]["s02_p2_started"])
        self.assertFalse(result["phase_scope"]["s02_p3_started"])
        self.assertFalse(result["phase_scope"]["raw_inventory_performed"])
        self.assertFalse(result["phase_scope"]["github_upload_performed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_modified_by_this_phase"])
        self.assertFalse(result["public_repo_safety"]["raw_business_data_committed"])
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertEqual(result["next_recommended_phase"], "S02-P2")


if __name__ == "__main__":
    unittest.main()
