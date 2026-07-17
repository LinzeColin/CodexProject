from __future__ import annotations

import csv
import io
import json
import unittest

from KMFA.tools import build_v015_s03_p3_public_repository_safety as builder


class S03P3PublicRepositorySafetyGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.outputs = builder.expected_outputs(final_validation=False)

    def _json(self, relative) -> object:
        return json.loads(self.outputs[builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / relative])

    def test_manifest_keeps_stage_review_and_later_work_closed(self) -> None:
        manifest = self._json(builder.MANIFEST_RELATIVE)
        self.assertEqual(manifest["phase_execution_status"], "EXECUTION_COMPLETE")
        self.assertEqual(manifest["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["stage_lifecycle_status"], "IN_PROGRESS")
        self.assertEqual(manifest["stage_acceptance_status"], "PENDING")
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["decision"], "REMAIN_IN_S03_P3")
        self.assertFalse(manifest["s03_stage_review_entry_allowed"])
        self.assertFalse(manifest["s03_stage_review_started"])
        self.assertFalse(manifest["s04_p1_entry_allowed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["raw_root_access_count_by_phase"], 0)

    def test_task_matrix_and_evidence_slots_are_complete(self) -> None:
        tasks = self._json(builder.TASK_MATRIX_RELATIVE)
        self.assertEqual([row["task_id"] for row in tasks], ["S03P3T01", "S03P3T02", "S03P3T03"])
        slots_payload = self.outputs[
            builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / builder.EVIDENCE_SLOTS_RELATIVE
        ].decode()
        slots = [json.loads(line) for line in slots_payload.splitlines() if line]
        self.assertEqual(len(slots), 30)
        self.assertEqual(sum(row["status"] == "N/A_WITH_RATIONALE" for row in slots), 15)
        self.assertTrue(all(row["artifact_ref"] for row in slots if row["status"] == "PRESENT"))
        self.assertTrue(all(row["artifact_ref"] is None for row in slots if row["status"] == "N/A_WITH_RATIONALE"))
        self.assertTrue(all(row["public_safe"] is True for row in slots))

    def test_field_table_is_exact_six_allow_four_deny(self) -> None:
        payload = self.outputs[
            builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / builder.FIELD_AUDIT_RELATIVE
        ].decode()
        rows = list(csv.DictReader(io.StringIO(payload)))
        self.assertEqual(sum(row["classification"] == "ALLOW" for row in rows), 6)
        self.assertEqual(sum(row["classification"] == "DENY" for row in rows), 4)
        self.assertTrue(all(row["unknown_field_policy"] == "DENY" for row in rows))
        self.assertTrue(all(row["raw_private_hash_allowed"] == "false" for row in rows))

    def test_dual_plane_projection_is_public_safe_and_truthful(self) -> None:
        dual = self._json(builder.DUAL_PLANE_RELATIVE)
        self.assertEqual(dual["run_id"], builder.RUN_ID)
        self.assertEqual(dual["public_projection_summary"]["run_id"], builder.RUN_ID)
        self.assertFalse(dual["public_projection_summary"]["plaintext_or_raw_private_values_public"])
        self.assertTrue(
            dual["public_projection_summary"][
                "keyed_opaque_token_values_bound_in_public_projection"
            ]
        )
        self.assertNotIn("opaque_tokens", dual["public_projection_summary"])
        builder.safety.validate_public_metadata_envelope(dual["public_projection"])
        self.assertEqual(dual["public_projection"]["run_id"], builder.RUN_ID)
        self.assertEqual(len(dual["public_projection"]["opaque_tokens"]), 5)
        self.assertTrue(
            all(
                row["token"].startswith("hmac-sha256:")
                for row in dual["public_projection"]["opaque_tokens"]
            )
        )
        self.assertEqual(dual["raw_root_access_count_by_phase"], 0)
        self.assertTrue(dual["verification"]["exact_private_to_public_rebuild"])
        self.assertTrue(dual["verification"]["declared_attack_model_pass"])
        self.assertFalse(dual["verification"]["information_theoretic_non_reconstruction_claimed"])
        self.assertTrue(dual["same_run_evidence_summary"]["private_evidence_gitignored"])
        self.assertFalse(dual["same_run_evidence_summary"]["private_evidence_tracked"])

    def test_every_changed_metadata_ref_has_one_explicit_safe_class(self) -> None:
        payload = self.outputs[
            builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / builder.METADATA_CLASSIFICATION_RELATIVE
        ].decode()
        rows = list(csv.DictReader(io.StringIO(payload)))
        expected = sorted(ref for ref in builder.phase_changed_refs() if ref.startswith("KMFA/metadata/"))
        self.assertEqual([row["metadata_ref"] for row in rows], expected)
        self.assertTrue(all(row["metadata_class"] in builder.safety.COMMITTABLE_METADATA_CLASSES for row in rows))
        self.assertTrue(all(row["structured_public_detail_finding_count"] == "0" for row in rows))
        self.assertTrue(all(row["classification_policy"] == "EXPLICIT_SIX_CLASS_FAIL_CLOSED" for row in rows))

    def test_every_changed_test_file_is_bound_to_a_validation_receipt(self) -> None:
        commands = "\n".join(builder.EXPECTED_VALIDATION_RECEIPTS.values())
        changed_tests = sorted(
            ref
            for ref in builder.phase_changed_refs()
            if "/tests/test_" in ref and ref.endswith(".py")
        )
        self.assertTrue(changed_tests)
        for ref in changed_tests:
            module = ref[:-3].replace("/", ".")
            test_root = ref.rsplit("/", 1)[0]
            self.assertTrue(
                module in commands or test_root in commands,
                msg=f"changed test is missing from validation receipts: {ref}",
            )

    def test_legacy_stage_evidence_allowlist_is_exact_and_closed(self) -> None:
        changed_legacy = {
            ref
            for ref in builder.phase_changed_refs()
            if ref.startswith("KMFA/stage_artifacts/")
            and not ref.startswith(
                "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/"
            )
        }
        self.assertEqual(changed_legacy, builder.ALLOWED_LEGACY_STAGE_EVIDENCE_REFS)
        self.assertTrue(all(builder._allowed_phase_ref(ref) for ref in changed_legacy))
        self.assertFalse(
            builder._allowed_phase_ref(
                "KMFA/stage_artifacts/UNRELATED_LEGACY_EVIDENCE/machine/leak.json"
            )
        )

    def test_history_boundary_does_not_overclaim(self) -> None:
        manifest = self._json(builder.MANIFEST_RELATIVE)
        census = self._json(builder.LEGACY_CENSUS_RELATIVE)
        for record in (manifest["history_boundary"], census):
            self.assertFalse(record["reachable_history_clean"])
            self.assertFalse(record["history_rewrite_performed"])
            self.assertFalse(record["final_github_upload_allowed_by_this_phase"])

    def test_public_outputs_do_not_disclose_synthetic_private_values_or_local_paths(self) -> None:
        combined = b"\n".join(self.outputs.values())
        self.assertIsNone(builder.ABSOLUTE_TEXT_PATTERN.search(combined.decode("utf-8")))
        for forbidden in (
            b"/" + b"Users/",
            b"synthetic-" + b"source-ledger",
            b"synthetic-" + b"customer-alpha",
            b"1274300" + b".19",
            b"SYNTHETICONLY",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
