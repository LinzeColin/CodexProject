import unittest

from KMFA.tools.check_v014_s02_p2_immutability_policy import validate_v014_s02_p2_immutability_policy


class TestV014S02P2ImmutabilityPolicy(unittest.TestCase):
    def test_immutability_policy_phase_is_closed_without_raw_read_or_upload(self) -> None:
        result = validate_v014_s02_p2_immutability_policy()

        self.assertEqual(result["stage_id"], "S02")
        self.assertEqual(result["phase_id"], "S02-P2")
        self.assertTrue(result["phase_scope"]["immutability_policy_only"])
        self.assertFalse(result["phase_scope"]["s02_p3_started"])
        self.assertFalse(result["phase_scope"]["stage2_review_performed"])
        self.assertFalse(result["phase_scope"]["github_upload_performed"])
        self.assertFalse(result["phase_scope"]["raw_inventory_performed"])
        self.assertFalse(result["phase_scope"]["raw_value_matching_performed"])
        self.assertTrue(result["immutability_policy"]["raw_manifest_append_only"])
        self.assertEqual(result["immutability_policy"]["raw_manifest_immutable_field_count"], 5)
        self.assertTrue(result["immutability_policy"]["derived_versions_append_only"])
        self.assertFalse(result["immutability_policy"]["derived_overwrite_old_version_allowed"])
        self.assertTrue(result["immutability_policy"]["control_events_append_only"])
        self.assertFalse(result["immutability_policy"]["control_events_raw_layer_write_allowed"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_listed_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_inventory_by_this_phase"])
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["github_main_upload_allowed"])
        self.assertEqual(result["release_state"]["current_go_no_go"], "NO_GO")
        self.assertEqual(result["next_recommended_phase"], "S02-P3")


if __name__ == "__main__":
    unittest.main()
