import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CHECKER = ROOT / "scripts" / "check_worker_queue_stage_review.py"
REVIEW = PURSUE_ROOT / "STAGE038_STAGE_REVIEW.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage038WorkerQueueStageReviewTests(unittest.TestCase):
    def _load_checker(self):
        self.assertTrue(CHECKER.is_file(), f"missing Stage038 review checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage038_worker_queue_stage_review", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_review_report_closes_acc_stage038_without_upload(self):
        report = self._load_checker().build_stage038_review_report()

        self.assertTrue(report["review_valid"], report)
        self.assertEqual("IDS-V0_1-STAGE038-REVIEW", report["task_id"])
        self.assertEqual("ACC-STAGE-038", report["acceptance_id"])
        self.assertEqual("completed_reviewed_local", report["stage_review_status"])
        self.assertEqual("IDS-STAGE039-P1-GATE", report["next_gate"])
        self.assertEqual("PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED", report["result"])
        self.assertTrue(all(report["review_checks"].values()), report)
        self.assertFalse(report["production_runtime_activation_performed"])
        self.assertFalse(report["raw_metadata_content_accessed"])
        self.assertFalse(report["fake_ids_business_data_used"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])

    def test_review_sources_are_git_tracked_and_match_index(self):
        binding = self._load_checker().build_stage038_review_report()[
            "review_source_binding"
        ]
        self.assertTrue(binding["all_sources_git_tracked"], binding)
        self.assertTrue(binding["all_sources_match_git_index"], binding)
        self.assertTrue(all(binding["observed_source_sha256"].values()), binding)
        self.assertIn("review_artifact", binding["git_tracked_sources"])
        self.assertIn("review_checker", binding["git_tracked_sources"])
        self.assertIn("phase4_checker", binding["git_tracked_sources"])
        self.assertIn("governance_validator", binding["git_tracked_sources"])

    def test_invalid_governance_evidence_fails_closed_at_review_gate(self):
        module = self._load_checker()
        valid = module.build_stage038_review_report()
        tampered = json.loads(json.dumps(valid["review_governance_report"]))
        tampered["valid"] = False
        blocked = module.build_stage038_review_report(
            review_governance_report=tampered
        )

        self.assertFalse(blocked["review_valid"], blocked)
        self.assertEqual("FAIL_CLOSED", blocked["result"])
        self.assertEqual("blocked_invalid_review_evidence", blocked["stage_review_status"])
        self.assertEqual("IDS-STAGE038-REVIEW-GATE", blocked["next_gate"])
        self.assertFalse(blocked["github_upload_allowed"])

    def test_review_artifact_and_governance_route_only_to_stage039(self):
        self.assertTrue(REVIEW.is_file(), f"missing review artifact: {REVIEW}")
        review_text = REVIEW.read_text(encoding="utf-8")
        for term in (
            "IDS-V0_1-STAGE038-REVIEW",
            "ACC-STAGE-038",
            "completed_reviewed_local",
            "IDS-STAGE039-P1-GATE",
            "STAGE038-REVIEW-F1",
            "STAGE038-REVIEW-F2",
            "STAGE038-REVIEW-F3",
            "STAGE038-REVIEW-F4",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE039_THIS_RUN",
        ):
            with self.subTest(term=term):
                self.assertIn(term, review_text)

        module = self._load_checker()
        batch = module._parse_yaml_text(BATCH_LOCK.read_text(encoding="utf-8"))
        roadmap = module._parse_yaml_text(ROADMAP.read_text(encoding="utf-8"))
        stage = batch["stage_progress"]["STAGE-038"]
        self.assertEqual("stage038_completed_reviewed_local", batch["status"])
        self.assertEqual("completed_reviewed_local", stage["status"])
        self.assertEqual("passed", stage["review_status"])
        self.assertEqual("STAGE-039", stage["next_stage"])
        self.assertEqual("IDS-STAGE039-P1-GATE", stage["next_gate"])
        self.assertEqual("IDS-V0_1-STAGE038-REVIEW", stage["current_task_id"])
        self.assertFalse(batch["upload_gate"]["push_allowed"])
        self.assertEqual(
            "IDS-V0_1-STAGE039-P1",
            batch["decision"]["next_allowed_task_id"],
        )
        self.assertEqual("IDS-STAGE038-REVIEW", roadmap["current_phase_id"])
        self.assertEqual("IDS-STAGE039-P1-GATE", roadmap["next_gate_id"])

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            event
            for event in events
            if event.get("event_id")
            == "EVT-IDS-V0_1-STAGE038-REVIEW-20260713-001"
        ]
        self.assertEqual(1, len(matching), matching)
        event = matching[0]
        self.assertEqual("stage_review", event["event_type"])
        self.assertEqual("IDS-V0_1-STAGE038-REVIEW", event["task_id"])
        self.assertIn("review_valid=true", event["notes"])
        self.assertIn("push_allowed=false", event["notes"])

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
        self.assertEqual("IDS-STAGE039-P1-GATE", payload["next_gate"])


if __name__ == "__main__":
    unittest.main()
