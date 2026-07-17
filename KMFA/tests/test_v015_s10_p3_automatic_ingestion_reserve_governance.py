from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s10_p3_automatic_ingestion_reserve as builder
from KMFA.tools import check_v015_s10_p3_automatic_ingestion_reserve as checker
from KMFA.tools import v015_s10_p3_automatic_ingestion_reserve as kernel


class AutomaticIngestionReserveGovernanceTests(unittest.TestCase):
    def test_manifest_governance_is_current_and_review_is_separate(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        accepted = manifest["phase_acceptance_status"] == "PASSED"
        checker._check_manifest(pre_final=not accepted)
        self.assertEqual(manifest["run_phase_id"], kernel.RUN_PHASE_ID)
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["s10_stage_review_entry_allowed"], accepted)
        self.assertFalse(manifest["s10_stage_review_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_governance_mirrors_and_registries_are_complete(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        checker._check_governance(pre_final=manifest["phase_acceptance_status"] != "PASSED")

    def test_scope_dependency_taskpack_and_public_boundary(self) -> None:
        checker._check_scope()
        checker._check_dependency()
        checker._check_taskpack_source()
        checker._check_public_boundary()

    def test_no_raw_connector_credential_or_release_action(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["raw_root_access_count"], 0)
        self.assertFalse(manifest["raw_business_content_read"])
        self.assertFalse(manifest["source_mutation_performed"])
        self.assertEqual(manifest["live_connector_call_count"], 0)
        self.assertEqual(manifest["credential_read_count"], 0)
        self.assertEqual(manifest["automatic_connector_enabled_count"], 0)
        self.assertFalse(manifest["formal_report_generated"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertFalse(manifest["business_execution_performed"])


if __name__ == "__main__":
    unittest.main()
