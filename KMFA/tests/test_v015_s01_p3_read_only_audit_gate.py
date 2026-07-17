import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from KMFA.tools.check_v015_s01_p3_read_only_audit_gate import (
    ACCEPTANCE_PATH,
    MANIFEST_PATH,
    METADATA_PATH,
    RISK_PATH,
    SIDE_EFFECT_PATH,
    STAGE_STATUS_PATH,
    ValidationError,
    _canonical_content_hash,
    _phase_paths,
    validate_v015_s01_p3_read_only_audit_gate,
)


class TestV015S01P3ReadOnlyAuditGate(unittest.TestCase):
    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def _write_csv(self, directory: str, name: str, rows: list[dict[str, str]]) -> Path:
        path = Path(directory) / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _write_json(self, directory: str, name: str, value: dict) -> Path:
        path = Path(directory) / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def _write_jsonl(self, directory: str, name: str, values: list[dict]) -> Path:
        path = Path(directory) / name
        path.write_text("".join(json.dumps(value, ensure_ascii=False) + "\n" for value in values), encoding="utf-8")
        return path

    def test_validates_negative_p3_evidence_without_phase_pass(self) -> None:
        result = validate_v015_s01_p3_read_only_audit_gate(
            require_source_package=True,
            require_local_environment=True,
            require_dependency_validators=True,
        )
        self.assertEqual(result["audit_conclusion"]["selected_value"], "RUNTIME_OBJECT_MISSING")
        self.assertEqual(result["acceptance_status"], "NOT_PASSED")
        self.assertEqual(result["phase_gate"]["task_acceptance_passed_count"], 2)
        self.assertFalse(result["phase_gate"]["stage_01_passed"])
        self.assertEqual(result["phase_gate"]["next_allowed_run"], "STAGE-01-REVIEW")

    def test_rejects_refactorable_conclusion(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["audit_conclusion"]["selected_value"] = "REFACTORABLE"
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_audit_blocked_conclusion(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["audit_conclusion"]["selected_value"] = "AUDIT_BLOCKED"
        manifest["audit_conclusion"]["audit_itself_blocked"] = True
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_static_button_acceptance_evidence(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["audit_conclusion"]["static_button_or_dom_used_as_acceptance"] = True
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_missing_risk(self) -> None:
        rows = self._read_csv(RISK_PATH)[:-1]
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_duplicate_risk_id(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[-1]["risk_id"] = rows[-2]["risk_id"]
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_arbitrary_noncritical_risk_id(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[0]["risk_id"] = "ARBITRARY-RISK-ID"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_risk_without_owner(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[0]["owner_role"] = ""
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_invalid_resolution_stage(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[0]["resolution_stages"] = "S01"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_closed_or_resolved_risk(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[0]["status"] = "RESOLVED"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_p0_without_stop_condition(self) -> None:
        rows = self._read_csv(RISK_PATH)
        next(row for row in rows if row["priority"] == "P0")["stop_condition"] = ""
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_frozen_phase_path_set_ignores_later_review_changes(self) -> None:
        paths = _phase_paths()
        self.assertEqual(len(paths), 29)
        self.assertNotIn("KMFA/AGENTS.md", paths)
        self.assertNotIn("KMFA/tools/check_v015_s01_stage_review.py", paths)

    def test_rejects_incomplete_high_risk_requirement_coverage(self) -> None:
        rows = self._read_csv(RISK_PATH)
        row = next(row for row in rows if "R026" in row["related_requirement_ids"].split(";"))
        row["related_requirement_ids"] = ";".join(item for item in row["related_requirement_ids"].split(";") if item != "R026")
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_recommended_resolution_stage_chain_gap(self) -> None:
        rows = self._read_csv(RISK_PATH)
        row = next(row for row in rows if "R004" in row["related_requirement_ids"].split(";"))
        row["resolution_stages"] = ";".join(
            stage for stage in row["resolution_stages"].split(";") if stage != "S06"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_unknown_capability(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[0]["related_capability_ids"] += ";CAP-999"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_missing_risk_evidence_path(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[0]["evidence_refs"] = "KMFA/does-not-exist"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_external_risk_evidence_path(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[0]["evidence_refs"] = "/etc/hosts"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_repository_root_risk_evidence_path(self) -> None:
        rows = self._read_csv(RISK_PATH)
        rows[0]["evidence_refs"] = "."
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "risks.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(risk_path=path, source_package=None)

    def test_rejects_zero_code_change_claim(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["tracked_diff_before_p3"]["zero_code_change_claim_allowed"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_zero_metadata_change_claim(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["tracked_diff_before_p3"]["zero_metadata_change_claim_allowed"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_zero_private_audit_writes(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["private_runtime_observation"]["expected_evidence_file_count"] = 0
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_raw_recursive_integrity_proven(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["raw_root"]["recursive_integrity"] = "PROVEN_UNCHANGED"
        side["raw_root"]["recursive_pre_snapshot_available"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_complete_historical_process_monitoring(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["process_observation"]["historical_process_monitoring"] = "COMPLETE"
        side["process_observation"]["complete_continuous_monitoring_available"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_denial_of_one_shot_app_launch(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["process_observation"]["expected_one_shot_app_launch"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_app_hash_drift(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["installed_app"]["aggregate_sha256_post_observed"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_raw_sentinel_mismatch(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["raw_root"]["shallow_sentinel_match"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_raw_sentinel_document_drift(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["raw_root"]["post_observed_sentinel"]["mtime_epoch"] += 1
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_observed_product_source_change(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["p3_observed_change_summary"]["product_runtime_source_change_count"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_t03_pass_claim(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["acceptance_status"] = "PASSED"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_s02_started_boundary(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["phase_boundaries"]["s02_started"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_empty_phase_boundaries(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["phase_boundaries"] = {}
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_missing_observed_change_summary(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side.pop("p3_observed_change_summary")
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_hidden_remote_main_drift(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["remote_repository_observation"]["remote_main_external_drift_detected"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_hidden_local_tracking_ref_change(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["remote_repository_observation"]["local_tracking_ref_changed_during_p3"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_false_fetch_attribution(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["remote_repository_observation"]["fetch_attribution"] = "CURRENT_TASK_CONFIRMED"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_zero_shared_git_ref_change_count(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["side_effect_classification"]["unexpected_shared_git_ref_change_count"] = 0
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_remote_main_oid_drift(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["remote_repository_observation"]["remote_main_oid_observed"] = "0" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_unverifiable_live_remote_oid(self) -> None:
        with patch("KMFA.tools.check_v015_s01_p3_read_only_audit_gate._remote_main_oid", return_value="f" * 40):
            with patch("KMFA.tools.check_v015_s01_p3_read_only_audit_gate._commit_is_visible", return_value=False):
                with self.assertRaises(ValidationError):
                    validate_v015_s01_p3_read_only_audit_gate(source_package=None, require_remote_observation=True)

    def test_rejects_current_task_push_claim(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["remote_repository_observation"]["current_task_push_performed"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)

    def test_rejects_phase_acceptance_pass(self) -> None:
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        acceptance["phase_acceptance_status"] = "PASSED"
        acceptance["quality_gate_passed"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "acceptance.json", acceptance)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(acceptance_path=path, source_package=None)

    def test_rejects_acceptance_check_identity_drift(self) -> None:
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        acceptance["checks"][-1]["check_id"] = "unrelated_check"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "acceptance.json", acceptance)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(acceptance_path=path, source_package=None)

    def test_rejects_acceptance_task_outcome_drift(self) -> None:
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        acceptance["task_outcomes"][-1]["acceptance_status"] = "PASSED"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "acceptance.json", acceptance)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(acceptance_path=path, source_package=None)

    def test_rejects_duplicate_acceptance_task_outcome(self) -> None:
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        duplicate = dict(acceptance["task_outcomes"][-1])
        duplicate["acceptance_status"] = "PASSED"
        acceptance["task_outcomes"].insert(0, duplicate)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "acceptance.json", acceptance)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(acceptance_path=path, source_package=None)

    def test_rejects_manifest_t03_pass_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["task_outcomes"][-1]["acceptance_status"] = "PASSED"
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_manifest_task_evidence_drift_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["task_outcomes"][0]["evidence"] = ""
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_manifest_dependency_ref_drift_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["dependencies"]["s01p1_manifest_ref"] = "/etc/hosts"
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_extra_manifest_phase_gate_key_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["phase_gate"]["raw_mutation_performed"] = True
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_duplicate_manifest_task_outcome_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        duplicate = dict(manifest["task_outcomes"][-1])
        duplicate["acceptance_status"] = "PASSED"
        manifest["task_outcomes"].insert(0, duplicate)
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_empty_artifact_refs_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["artifact_refs"] = {}
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_empty_release_state_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["release_state"] = {}
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_empty_public_safety_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["public_repo_safety"] = {}
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(path, source_package=None)

    def test_rejects_metadata_false_no_side_effect_proof(self) -> None:
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        metadata["no_side_effects_fully_proven"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "metadata.json", metadata)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(metadata_path=path, source_package=None)

    def test_rejects_metadata_false_no_unexpected_change_claim(self) -> None:
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        metadata["no_unexpected_change_detected"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "metadata.json", metadata)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(metadata_path=path, source_package=None)

    def test_rejects_stale_latest_p3_stage_status(self) -> None:
        records = [json.loads(line) for line in STAGE_STATUS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        latest_p3_index = max(
            index
            for index, record in enumerate(records)
            if record.get("phase_id") == "V015_S01_P3_READ_ONLY_AUDIT_GATE"
        )
        records[latest_p3_index]["fetch_attribution"] = "CURRENT_TASK_CONFIRMED"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_jsonl(directory, "stage_status.jsonl", records)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(stage_status_path=path, source_package=None)

    def test_rejects_minimal_latest_p3_stage_status(self) -> None:
        records = [json.loads(line) for line in STAGE_STATUS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        records.append({
            "phase_id": "V015_S01_P3_READ_ONLY_AUDIT_GATE",
            "terminal_finding": "UNEXPECTED_LOCAL_GIT_STATE_CHANGE_AND_INSUFFICIENT_PREAUDIT_TELEMETRY",
            "unexpected_worktree_product_change_count": 0,
            "unexpected_shared_git_ref_change_count": 1,
            "fetch_attribution": "UNVERIFIED_CONCURRENT_SHARED_REPOSITORY_CHANGE",
            "local_tracking_ref_oid_observed": "d0a098b7e1b38763ee07ad264b28ce54a7c06022",
            "remote_main_oid_observed": "d0a098b7e1b38763ee07ad264b28ce54a7c06022",
            "current_task_push_performed": False,
            "stage_01_passed": False,
            "s02_entry_allowed": False,
        })
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_jsonl(directory, "stage_status.jsonl", records)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(stage_status_path=path, source_package=None)

    def test_rejects_no_side_effects_proven_result(self) -> None:
        side = json.loads(SIDE_EFFECT_PATH.read_text(encoding="utf-8"))
        side["snapshot_status"] = "NO_SIDE_EFFECTS_PROVEN"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "side.json", side)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p3_read_only_audit_gate(side_effect_path=path, source_package=None)


if __name__ == "__main__":
    unittest.main()
