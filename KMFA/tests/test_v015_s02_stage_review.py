from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from KMFA.tools import build_v015_s02_stage_review as builder
from KMFA.tools import check_v015_s02_stage_review as checker


class TestV015S02StageReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.roadmap = checker._read_json(checker.ROADMAP_SOURCE_PATH)

    def test_validator_exists(self) -> None:
        self.assertTrue(callable(checker.validate_v015_s02_stage_review))

    def test_source_package_verifies_all_21_members(self) -> None:
        snapshot, tasks, slots = builder._verify_source_package(builder.DEFAULT_SOURCE_PACKAGE)
        errors: list[str] = []
        checker._validate_source_package(builder.DEFAULT_SOURCE_PACKAGE, snapshot, errors)
        self.assertEqual(errors, [])
        self.assertEqual((len(tasks), len(slots)), (9, 10))

    def test_source_manifest_count_mutation_fails_closed(self) -> None:
        snapshot, _, _ = builder._verify_source_package(builder.DEFAULT_SOURCE_PACKAGE)
        snapshot["verified_member_count"] = 20
        errors: list[str] = []
        checker._validate_source_package(builder.DEFAULT_SOURCE_PACKAGE, snapshot, errors)
        self.assertTrue(any("21/21" in item for item in errors))

    def test_matrix_missing_task_fails_closed(self) -> None:
        matrix = checker._read_json(checker.MATRIX_PATH)
        matrix["tasks"] = matrix["tasks"][:-1]
        errors: list[str] = []
        checker._validate_matrix(matrix, self.roadmap, errors)
        self.assertTrue(any("nine unique Tasks" in item or "Task ID set" in item for item in errors))

    def test_matrix_source_evidence_clause_mutation_fails_closed(self) -> None:
        matrix = checker._read_json(checker.MATRIX_PATH)
        matrix["tasks"][0]["source_contract"]["evidence"] = "DRIFT"
        errors: list[str] = []
        checker._validate_matrix(matrix, self.roadmap, errors)
        self.assertTrue(any("source contract drift" in item for item in errors))

    def test_task_evidence_missing_slot_fails_closed(self) -> None:
        evidence = checker._read_json(checker.TASK_EVIDENCE_PATH)
        evidence["tasks"][0]["slots"] = evidence["tasks"][0]["slots"][:-1]
        errors: list[str] = []
        checker._validate_task_evidence(evidence, self.roadmap, errors)
        self.assertTrue(any("evidence-slot coverage drift" in item for item in errors))

    def test_stage_gate_or_s03_started_mutation_fails_closed(self) -> None:
        manifest = checker._read_json(checker.MATRIX_PATH)
        manifest["stage_gate"] = dict(checker.EXPECTED_STAGE_GATE, final_validation_status="PASS")
        manifest["next_entry_gate"] = {
            "next_allowed_run": "S03-P1", "s03_p1_entry_allowed": True,
            "s03_p1_started": False, "s03_plus_entry_allowed": False,
            "product_implementation_allowed": False,
        }
        manifest["downstream_actions"]["s03_p1_started"] = True
        manifest["stage_gate"]["stage_acceptance_status"] = "PENDING"
        errors: list[str] = []
        checker._validate_stage_boundary(manifest, errors, label="mutation")
        self.assertTrue(any("Stage gate drift" in item for item in errors))
        self.assertTrue(any("downstream action true" in item for item in errors))

    def test_receipt_command_drift_fails_closed(self) -> None:
        rows = [
            {"validation_id": validation_id, "command": command, "result": "PASS", "exit_code": 0}
            for validation_id, command in builder.EXPECTED_VALIDATION_RECEIPTS.items()
        ]
        rows[0]["command"] += " --drift"
        errors: list[str] = []
        checker._validate_receipts(rows, require_pass=True, errors=errors)
        self.assertTrue(any("exact command drift" in item for item in errors))

    def test_contract_failure_is_blocking_but_pass_contract_policy_may_be_true(self) -> None:
        contracts = checker._read_json(checker.CONTRACTS_PATH)
        passed = copy.deepcopy(contracts)
        passed["contracts"][0]["blocking"] = True
        errors: list[str] = []
        checker._validate_contracts(passed, errors)
        self.assertEqual(errors, [])
        failed = copy.deepcopy(contracts)
        failed["contracts"][0]["status"] = "FAIL"
        errors = []
        checker._validate_contracts(failed, errors)
        self.assertTrue(any("not PASS" in item for item in errors))

    def test_open_p1_finding_fails_closed(self) -> None:
        matrix = checker._read_json(checker.MATRIX_PATH)
        manifest = matrix
        findings = checker._read_csv(checker.FINDINGS_PATH)
        risks = checker._read_csv(checker.RISKS_PATH)
        findings[0]["status"] = "OPEN"
        findings[0]["blocks_stage_acceptance"] = "true"
        errors: list[str] = []
        checker._validate_findings_and_risks(manifest, matrix, findings, risks, errors)
        self.assertTrue(any("zero blocking" in item for item in errors))

    def test_incomplete_risk_route_fails_closed(self) -> None:
        matrix = checker._read_json(checker.MATRIX_PATH)
        manifest = matrix
        findings = checker._read_csv(checker.FINDINGS_PATH)
        risks = checker._read_csv(checker.RISKS_PATH)
        risks[0]["plan_complete"] = "false"
        risks[0]["follow_up_stage_task"] = ""
        errors: list[str] = []
        checker._validate_findings_and_risks(manifest, matrix, findings, risks, errors)
        self.assertTrue(any("risk route incomplete" in item for item in errors))

    def test_actual_lineage_or_runtime_claim_mutation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replacements: dict[str, Path] = {}
            for phase_id, source in checker.PHASE_MANIFESTS.items():
                target = root / (phase_id + ".json")
                value = checker._read_json(source)
                if phase_id == "S02-P2":
                    value["lineage_accounting"]["actual_lineage_record_count"] = 1
                if phase_id == "S02-P3":
                    value["change_control_accounting"]["runtime_or_ci_hook_implemented"] = True
                target.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                replacements[phase_id] = target
            with patch.dict(checker.PHASE_MANIFESTS, replacements, clear=True):
                errors: list[str] = []
                checker._validate_cross_phase_live_truth({}, errors)
            self.assertTrue(any("actual-lineage" in item for item in errors))
            self.assertTrue(any("runtime/CI" in item for item in errors))

    def test_public_safe_absolute_path_mutations_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            absolute_path = "/" + "Users/example/raw"
            path.write_text(json.dumps({"path": absolute_path}) + "\n", encoding="utf-8")
            errors: list[str] = []
            checker._validate_public_safe([path], errors)
            self.assertTrue(any("public-safe token leak" in item for item in errors))
        errors = []
        python_payload = b'raw_root = b"' + b"/" + b'Users/" + b"example/raw"'
        checker._validate_public_safe_payload(
            python_payload, errors, label="added Python",
        )
        self.assertTrue(any("public-safe token leak" in item for item in errors))

    def test_diff_check_rejects_unfrozen_base(self) -> None:
        with self.assertRaisesRegex(checker.ValidationError, "frozen REVIEW_BASE_COMMIT"):
            checker.run_structured_public_diff_check("HEAD")


if __name__ == "__main__":
    unittest.main()
