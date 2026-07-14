import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = ROOT.parent
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CHECKER = ROOT / "scripts" / "check_batch031_040_review.py"
CONTRACT = PURSUE_ROOT / "batch_review" / "stage031_040_batch_review_contract.json"
REVIEW = PURSUE_ROOT / "BATCH031_040_REVIEW_GATE.md"
BATCH = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Batch031040ReviewGateTests(unittest.TestCase):
    def _load_checker(self):
        self.assertTrue(CHECKER.is_file(), f"missing batch checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "batch031_040_review_checker", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_batch_review_artifacts_exist(self):
        self.assertTrue(REVIEW.is_file(), f"missing review evidence: {REVIEW}")
        self.assertTrue(CONTRACT.is_file(), f"missing review contract: {CONTRACT}")
        self.assertTrue(CHECKER.is_file(), f"missing review checker: {CHECKER}")

    def test_contract_binds_exact_ten_stage_source_and_review_matrix(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(
            "ids.v0_1.batch031_040.review_contract.v1",
            contract["schema_version"],
        )
        self.assertEqual("IDS-V0_1-BATCH-031-040", contract["batch_id"])
        self.assertEqual(
            "IDS-V0_1-BATCH-031-040-REVIEW-GATE", contract["task_id"]
        )
        stages = contract["stage_reviews"]
        self.assertEqual(
            [f"STAGE-{stage:03d}" for stage in range(31, 41)],
            [stage["stage_id"] for stage in stages],
        )
        self.assertEqual(
            [f"ACC-STAGE-{stage:03d}" for stage in range(31, 41)],
            [stage["acceptance_id"] for stage in stages],
        )
        for stage in stages:
            with self.subTest(stage=stage["stage_id"]):
                self.assertEqual("completed_reviewed_local", stage["status"])
                self.assertEqual("passed", stage["review_status"])
                self.assertRegex(stage["source_member_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(stage["review_artifact_sha256"], r"^[0-9a-f]{64}$")
                self.assertTrue(stage["review_artifact_ref"].endswith("_STAGE_REVIEW.md"))
                self.assertTrue(stage["checker_ref"].startswith("KM_IDSystem/scripts/"))
                self.assertTrue(stage["test_refs"])

    def test_checker_reverifies_sources_stages_and_cross_stage_interfaces(self):
        report = self._load_checker().build_batch031_040_review_report()
        self.assertTrue(report["review_valid"], report)
        self.assertTrue(all(report["source_checks"].values()), report)
        self.assertTrue(all(report["stage_checks"].values()), report)
        self.assertTrue(all(report["cross_stage_checks"].values()), report)
        self.assertTrue(all(report["governance_checks"].values()), report)
        self.assertTrue(all(report["source_binding_checks"].values()), report)
        self.assertEqual(10, report["reviewed_stage_count"])
        self.assertEqual(
            "PASS_REVIEWED_READY_FOR_UPLOAD_GATE_NO_GITHUB_UPLOAD",
            report["result"],
        )
        self.assertEqual(
            "IDS-V0_1-BATCH-031-040-UPLOAD-GATE", report["next_gate"]
        )

    def test_unknown_contract_fields_fail_closed(self):
        checker = self._load_checker()
        contract = checker.load_contract()
        tampered = copy.deepcopy(contract)
        tampered["production_runtime_enabled"] = True
        blocked = checker.build_batch031_040_review_report(contract=tampered)
        self.assertFalse(blocked["review_valid"], blocked)
        self.assertEqual("FAIL_CLOSED", blocked["result"])
        self.assertEqual(
            "IDS-V0_1-BATCH-031-040-REVIEW-GATE", blocked["next_gate"]
        )
        self.assertFalse(blocked["github_upload_allowed"])

        nested = copy.deepcopy(contract)
        nested["stage_reviews"][0]["production_runtime_enabled"] = True
        blocked_nested = checker.build_batch031_040_review_report(contract=nested)
        self.assertFalse(blocked_nested["review_valid"], blocked_nested)
        self.assertFalse(
            blocked_nested["contract_shape_checks"]["stage_review_shapes_exact"]
        )

        malformed_identity = copy.deepcopy(contract)
        malformed_identity["stage_reviews"][0]["stage_id"] = "STAGE-INVALID"
        blocked_identity = checker.build_batch031_040_review_report(
            contract=malformed_identity
        )
        self.assertFalse(blocked_identity["review_valid"], blocked_identity)
        self.assertEqual("FAIL_CLOSED", blocked_identity["result"])
        self.assertFalse(blocked_identity["stage_checks"]["STAGE-031"])

    def test_any_failed_stage_review_blocks_batch(self):
        checker = self._load_checker()
        stage_results = {f"STAGE-{stage:03d}": True for stage in range(31, 41)}
        stage_results["STAGE-036"] = False
        blocked = checker.build_batch031_040_review_report(
            stage_result_overrides=stage_results
        )
        self.assertFalse(blocked["review_valid"], blocked)
        self.assertFalse(blocked["stage_checks"]["STAGE-036"])
        self.assertEqual("FAIL_CLOSED", blocked["result"])
        self.assertFalse(blocked["push_allowed"])

    def test_review_document_records_findings_and_stop_boundaries(self):
        text = REVIEW.read_text(encoding="utf-8")
        for term in (
            "IDS-V0_1-BATCH-031-040-REVIEW-GATE",
            "STAGE-031..STAGE-040",
            "BATCH031-040-REVIEW-F1",
            "ACC-STAGE-031..ACC-STAGE-040",
            "push_allowed=false",
            "No GitHub upload",
            "NO_APP_REINSTALL",
            "NO_STAGE041_THIS_RUN",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "IDS-V0_1-BATCH-031-040-UPLOAD-GATE",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_governance_routes_to_separate_upload_gate_without_enabling_push(self):
        batch = BATCH.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        self.assertIn('status: "reviewed_ready_for_upload_no_github_upload"', batch)
        self.assertIn(
            'review_task_id: "IDS-V0_1-BATCH-031-040-REVIEW-GATE"', batch
        )
        self.assertIn('push_allowed: false', batch)
        self.assertIn(
            'next_allowed_task_id: "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"',
            batch,
        )
        self.assertIn(
            'current_phase_id: "IDS-V0_1-BATCH-031-040-REVIEW-GATE"',
            roadmap,
        )
        self.assertIn(
            'current_task_id: "IDS-V0_1-BATCH-031-040-REVIEW-GATE"',
            roadmap,
        )
        self.assertIn(
            'next_gate_id: "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"', roadmap
        )

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            event
            for event in events
            if event.get("event_id")
            == "EVT-IDS-V0_1-BATCH031-040-REVIEW-20260714-001"
        ]
        self.assertEqual(1, len(matching), matching)
        self.assertEqual("batch_review", matching[0]["event_type"])
        self.assertEqual(
            "IDS-V0_1-BATCH-031-040-REVIEW-GATE", matching[0]["task_id"]
        )

    def test_cli_emits_reviewed_no_upload_report(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(CHECKER)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        self.assertEqual("", completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["review_valid"], report)
        self.assertFalse(report["push_allowed"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])


if __name__ == "__main__":
    unittest.main()
