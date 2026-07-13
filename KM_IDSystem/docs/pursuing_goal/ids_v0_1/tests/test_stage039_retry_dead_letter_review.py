import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CHECKER = ROOT / "scripts" / "check_retry_dead_letter_stage_review.py"
REVIEW = PURSUE_ROOT / "STAGE039_STAGE_REVIEW.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage039RetryDeadLetterStageReviewTests(unittest.TestCase):
    def _load_checker(self):
        self.assertTrue(CHECKER.is_file(), f"missing Stage039 review checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage039_retry_dead_letter_stage_review", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_review_closes_acc_stage039_without_upload_or_production(self):
        report = self._load_checker().build_stage039_review_report()

        self.assertTrue(report["review_valid"], report)
        self.assertEqual("IDS-V0_1-STAGE039-REVIEW", report["task_id"])
        self.assertEqual("ACC-STAGE-039", report["acceptance_id"])
        self.assertEqual("completed_reviewed_local", report["stage_review_status"])
        self.assertEqual("IDS-STAGE040-P1-GATE", report["next_gate"])
        self.assertEqual("PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED", report["result"])
        self.assertTrue(all(report["review_checks"].values()), report)
        self.assertFalse(report["production_runtime_activation_performed"])
        self.assertFalse(report["raw_metadata_content_accessed"])
        self.assertFalse(report["fake_ids_business_data_used"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])

    def test_governance_registry_repairs_are_machine_checked(self):
        report = self._load_checker().build_stage039_review_report()
        checks = report["registry_repair_checks"]

        self.assertTrue(checks)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(8, report["registry_counts"]["model_count"])
        self.assertEqual(8, report["registry_counts"]["formula_count"])
        self.assertEqual(55, report["registry_counts"]["parameter_count"])
        self.assertEqual(7, report["registry_counts"]["active_model_count"])
        self.assertEqual(7, report["registry_counts"]["active_formula_count"])
        self.assertEqual(49, report["registry_counts"]["active_parameter_count"])

    def test_manual_rerun_truth_distinguishes_contract_from_implementation(self):
        report = self._load_checker().build_stage039_review_report()
        truth = report["manual_rerun_truth"]

        self.assertTrue(truth["new_linked_identity_required"])
        self.assertTrue(truth["candidate_only"])
        self.assertFalse(truth["job_created"])
        self.assertFalse(truth["persisted"])
        self.assertFalse(truth["terminal_job_reopen_allowed"])
        self.assertTrue(report["review_checks"]["manual_rerun_truth_exact"])

    def test_invalid_registry_evidence_fails_closed(self):
        module = self._load_checker()
        valid = module.build_stage039_review_report()
        tampered = dict(valid["registry_repair_checks"])
        tampered["planned_registry_statuses_exact"] = False
        blocked = module.build_stage039_review_report(
            registry_repair_checks=tampered
        )

        self.assertFalse(blocked["review_valid"], blocked)
        self.assertEqual("FAIL_CLOSED", blocked["result"])
        self.assertEqual("blocked_invalid_review_evidence", blocked["stage_review_status"])
        self.assertEqual("IDS-STAGE039-REVIEW-GATE", blocked["next_gate"])
        self.assertFalse(blocked["github_upload_allowed"])

    def test_review_sources_match_index_and_governance_routes_to_stage040(self):
        module = self._load_checker()
        report = module.build_stage039_review_report()
        binding = report["review_source_binding"]
        self.assertTrue(binding["all_sources_git_tracked"], binding)
        self.assertTrue(binding["all_sources_match_git_index"], binding)

        self.assertTrue(REVIEW.is_file())
        review_text = REVIEW.read_text(encoding="utf-8")
        for term in (
            "STAGE039-REVIEW-F1",
            "STAGE039-REVIEW-F2",
            "STAGE039-REVIEW-F3",
            "STAGE039-REVIEW-F4",
            "completed_reviewed_local",
            "IDS-STAGE040-P1-GATE",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE040_THIS_RUN",
        ):
            with self.subTest(term=term):
                self.assertIn(term, review_text)

        batch = module._parse_yaml_text(BATCH_LOCK.read_text(encoding="utf-8"))
        roadmap = module._parse_yaml_text(ROADMAP.read_text(encoding="utf-8"))
        stage = batch["stage_progress"]["STAGE-039"]
        self.assertEqual("stage039_completed_reviewed_local", batch["status"])
        self.assertEqual("completed_reviewed_local", stage["status"])
        self.assertEqual("passed", stage["review_status"])
        self.assertEqual("STAGE-040", stage["next_stage"])
        self.assertEqual("IDS-STAGE040-P1-GATE", stage["next_gate"])
        self.assertFalse(batch["upload_gate"]["push_allowed"])
        self.assertEqual("IDS-STAGE039-REVIEW", roadmap["current_phase_id"])
        self.assertEqual("IDS-STAGE040-P1-GATE", roadmap["next_gate_id"])

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            event
            for event in events
            if event.get("event_id")
            == "EVT-IDS-V0_1-STAGE039-REVIEW-20260713-001"
        ]
        self.assertEqual(1, len(matching), matching)
        self.assertEqual("stage_review", matching[0]["event_type"])
        self.assertEqual("IDS-V0_1-STAGE039-REVIEW", matching[0]["task_id"])

    def test_cli_emits_reviewed_local_report(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(CHECKER)],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        self.assertEqual("", completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["review_valid"], payload)
        self.assertEqual("completed_reviewed_local", payload["stage_review_status"])
        self.assertEqual("IDS-STAGE040-P1-GATE", payload["next_gate"])


if __name__ == "__main__":
    unittest.main()
