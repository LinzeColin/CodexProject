import csv
import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.check_v015_s01_p2_implementation_spec_gap_inventory import (
    ACCEPTANCE_PATH,
    GAP_PATH,
    GIT_PLAN_PATH,
    MANIFEST_PATH,
    MIGRATION_PATH,
    SOURCE_PACKAGE,
    ValidationError,
    _canonical_content_hash,
    validate_v015_s01_p2_implementation_spec_gap_inventory,
)


class TestV015S01P2ImplementationSpecGapInventory(unittest.TestCase):
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

    def test_validates_complete_p2_without_claiming_stage_pass(self) -> None:
        result = validate_v015_s01_p2_implementation_spec_gap_inventory(
            require_source_package=True,
            require_raw_root=True,
        )
        self.assertEqual(result["acceptance_status"], "PASSED")
        self.assertEqual(result["requirement_gap_inventory"]["total"], 55)
        self.assertFalse(result["phase_gate"]["stage_01_passed"])
        self.assertEqual(result["phase_gate"]["next_allowed_run"], "S01-P3")

    def test_rejects_missing_requirement(self) -> None:
        rows = self._read_csv(GAP_PATH)
        rows = [row for row in rows if row["requirement_id"] != "R055"]
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "gap.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(gap_path=path, source_package=None)

    def test_rejects_duplicate_requirement(self) -> None:
        rows = self._read_csv(GAP_PATH)
        rows[-1]["requirement_id"] = "R054"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "gap.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(gap_path=path, source_package=None)

    def test_rejects_gap_without_impact_or_evidence(self) -> None:
        rows = self._read_csv(GAP_PATH)
        rows[0]["impact"] = ""
        rows[0]["evidence_refs"] = ""
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "gap.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(gap_path=path, source_package=None)

    def test_rejects_invalid_recommended_stage(self) -> None:
        rows = self._read_csv(GAP_PATH)
        rows[0]["recommended_stage"] = "S25"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "gap.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(gap_path=path, source_package=None)

    def test_rejects_taskpack_requirement_name_drift(self) -> None:
        rows = self._read_csv(GAP_PATH)
        rows[0]["requirement_name"] = "错误名称"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "gap.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(
                    gap_path=path,
                    source_package=SOURCE_PACKAGE,
                    require_source_package=True,
                )

    def test_rejects_keep_without_verified_evidence(self) -> None:
        rows = self._read_csv(MIGRATION_PATH)
        keep = next(row for row in rows if row["decision"] == "KEEP")
        keep["verification_status"] = "NOT_VERIFIED"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "migration.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(migration_path=path, source_package=None)

    def test_rejects_deprecating_precision_invariant(self) -> None:
        rows = self._read_csv(MIGRATION_PATH)
        protected = next(row for row in rows if row["capability_id"] == "CAP-001")
        protected["decision"] = "DEPRECATE"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "migration.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(migration_path=path, source_package=None)

    def test_rejects_keep_for_static_launcher(self) -> None:
        rows = self._read_csv(MIGRATION_PATH)
        static = next(row for row in rows if row["capability_id"] == "CAP-025")
        static["decision"] = "KEEP"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "migration.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(migration_path=path, source_package=None)

    def test_rejects_destructive_selected_recovery_command(self) -> None:
        plan = json.loads(GIT_PLAN_PATH.read_text(encoding="utf-8"))
        plan["one_command_code_recovery"]["command"] = "git reset --hard d6f379ad"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "plan.json", plan)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(git_plan_path=path, source_package=None)

    def test_rejects_recovery_command_not_pinned_to_v014(self) -> None:
        plan = json.loads(GIT_PLAN_PATH.read_text(encoding="utf-8"))
        plan["one_command_code_recovery"]["command"] = "git switch --detach HEAD"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "plan.json", plan)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(git_plan_path=path, source_package=None)

    def test_rejects_destructive_final_merge_plan(self) -> None:
        plan = json.loads(GIT_PLAN_PATH.read_text(encoding="utf-8"))
        plan["final_merge_and_single_upload"][6] += " --force"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "plan.json", plan)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(git_plan_path=path, source_package=None)

    def test_rejects_baseline_commit_drift(self) -> None:
        plan = json.loads(GIT_PLAN_PATH.read_text(encoding="utf-8"))
        plan["repository"]["v014_public_safe_baseline_commit"] = "0" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "plan.json", plan)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(git_plan_path=path, source_package=None)

    def test_rejects_started_next_phase(self) -> None:
        plan = json.loads(GIT_PLAN_PATH.read_text(encoding="utf-8"))
        plan["current_phase_boundaries"]["next_phase_started"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "plan.json", plan)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(git_plan_path=path, source_package=None)

    def test_rejects_false_stage_acceptance(self) -> None:
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        acceptance["stage_01_passed"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "acceptance.json", acceptance)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(acceptance_path=path, source_package=None)

    def test_rejects_acceptance_check_identity_drift(self) -> None:
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        acceptance["checks"][-1]["check_id"] = "unrelated_check"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "acceptance.json", acceptance)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(acceptance_path=path, source_package=None)

    def test_rejects_manifest_count_drift_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["requirement_gap_inventory"]["severity_counts"]["CRITICAL"] = 25
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(path, source_package=None)

    def test_rejects_manifest_boundary_drift_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["phase_gate"]["next_allowed_run"] = "S02-P1"
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(path, source_package=None)

    def test_rejects_duplicate_task_outcome_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["task_outcomes"].insert(0, dict(manifest["task_outcomes"][-1]))
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(path, source_package=None)

    def test_rejects_task_evidence_drift_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["task_outcomes"][0]["evidence"] = ""
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(path, source_package=None)

    def test_rejects_empty_artifact_refs_even_with_recomputed_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["artifact_refs"] = {}
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(path, source_package=None)

    def test_rejects_unknown_capability_id(self) -> None:
        rows = self._read_csv(MIGRATION_PATH)
        rows[11]["capability_id"] = "CAP-999"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "migration.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(migration_path=path, source_package=None)

    def test_rejects_external_evidence_ref(self) -> None:
        rows = self._read_csv(GAP_PATH)
        rows[0]["evidence_refs"] = "/etc/hosts"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "gaps.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(gap_path=path, source_package=None)

    def test_rejects_repository_root_evidence_ref(self) -> None:
        rows = self._read_csv(GAP_PATH)
        rows[0]["evidence_refs"] = "."
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_csv(directory, "gaps.csv", rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(gap_path=path, source_package=None)

    def test_rejects_extra_current_phase_boundary(self) -> None:
        plan = json.loads(GIT_PLAN_PATH.read_text(encoding="utf-8"))
        plan["current_phase_boundaries"]["business_execution_performed"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "plan.json", plan)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(git_plan_path=path, source_package=None)

    def test_rejects_baseline_dependency_ref_drift(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["baseline_dependency"]["s01p1_manifest_ref"] = "/etc/hosts"
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(path, source_package=None)

    def test_rejects_extra_manifest_phase_gate_key(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["phase_gate"]["business_execution_performed"] = True
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(path, source_package=None)

    def test_rejects_phase_execution_count_drift(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["phase_gate"]["task_execution_complete_count"] = 2
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p2_implementation_spec_gap_inventory(path, source_package=None)


if __name__ == "__main__":
    unittest.main()
