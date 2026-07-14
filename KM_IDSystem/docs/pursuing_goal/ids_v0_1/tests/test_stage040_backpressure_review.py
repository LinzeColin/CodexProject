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
POLICY_CONTRACT = (
    PURSUE_ROOT
    / "backpressure_policy"
    / "stage040_backpressure_policy_contract.json"
)
RUNTIME_CHECKER = ROOT / "scripts" / "check_backpressure_runtime.py"
REVIEW_CHECKER = ROOT / "scripts" / "check_backpressure_stage_review.py"
REVIEW = PURSUE_ROOT / "STAGE040_STAGE_REVIEW.md"
BATCH = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
CONTROL_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md"
)


class Stage040BackpressureStageReviewTests(unittest.TestCase):
    def _load_module(self, path: Path, name: str):
        self.assertTrue(path.is_file(), f"missing module: {path}")
        spec = importlib.util.spec_from_file_location(name, path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _review_checker(self):
        return self._load_module(REVIEW_CHECKER, "stage040_backpressure_review")

    def test_review_artifacts_exist(self):
        self.assertTrue(REVIEW.is_file(), f"missing review artifact: {REVIEW}")
        self.assertTrue(
            REVIEW_CHECKER.is_file(), f"missing review checker: {REVIEW_CHECKER}"
        )

    def test_invalid_control_metadata_fails_closed_without_echo_or_exception(self):
        module = self._load_module(RUNTIME_CHECKER, "stage040_runtime_for_review")
        contract = module.load_contract()
        valid_job = module.build_control_job(CONTROL_REF)

        invalid_observation = module.evaluate_backpressure(
            valid_job,
            {"unexpected": object()},
            contract=contract,
            now_epoch_seconds=1,
        )
        self.assertEqual(
            "REQUIRE_MANUAL_REVIEW", invalid_observation["decision_action"]
        )
        self.assertEqual(
            "INVALID_PRESSURE_OBSERVATION", invalid_observation["reason_code"]
        )
        self.assertIsNone(invalid_observation["observed_at_epoch_seconds"])
        json.dumps(invalid_observation)

        for invalid_refs in (
            [{"private_payload": "SENTINEL"}],
            ["PRIVATE_SENTINEL_NOT_A_REF"],
        ):
            with self.subTest(invalid_refs=invalid_refs):
                invalid_job = copy.deepcopy(valid_job)
                invalid_job["input_refs"] = invalid_refs
                result = module.evaluate_backpressure(
                    invalid_job,
                    {},
                    contract=contract,
                    now_epoch_seconds=1,
                )
                self.assertEqual("REQUIRE_MANUAL_REVIEW", result["decision_action"])
                self.assertEqual("INVALID_CONTRACT_OR_JOB", result["reason_code"])
                self.assertEqual([], result["input_refs"])
                self.assertNotIn("SENTINEL", json.dumps(result))

    def test_phase1_status_and_fairness_contracts_do_not_overclaim(self):
        contract = json.loads(POLICY_CONTRACT.read_text(encoding="utf-8"))
        projection = contract["human_status_projection"]
        self.assertEqual(
            {
                "QUEUED_OR_RETRY_WAIT": "已暂停",
                "CLAIMED_OR_RUNNING": "暂停中",
            },
            projection["PAUSE_RESOURCE_GATE"],
        )
        fairness = contract["fairness_contract"]
        self.assertFalse(fairness["starvation_prevention_proved"])
        self.assertEqual("NOT_IMPLEMENTED_IN_STAGE040", fairness["scheduler_algorithm"])
        self.assertEqual(
            "PHASE2_ADMISSION_GUARD_ONLY", fairness["per_job_type_concurrency"]
        )
        self.assertNotIn("starvation_allowed", fairness)

    def test_review_reverifies_external_sources_and_all_four_phases(self):
        report = self._review_checker().build_stage040_review_report()
        self.assertTrue(report["source_integrity_valid"], report)
        self.assertTrue(all(report["source_integrity_checks"].values()), report)
        self.assertEqual(
            {
                "phase1_contract_valid": True,
                "phase2_slice_valid": True,
                "phase3_contract_valid": True,
                "phase4_contract_valid": True,
            },
            report["phase_results"],
        )

    def test_review_finding_repairs_are_machine_checked_and_fail_closed(self):
        checker = self._review_checker()
        report = checker.build_stage040_review_report()
        self.assertEqual(3, report["finding_count"])
        self.assertEqual({"Critical": 1, "Important": 2, "Minor": 0}, report["finding_counts"])
        self.assertTrue(all(report["finding_checks"].values()), report)

        tampered = dict(report["finding_checks"])
        tampered["invalid_metadata_is_structured_and_redacted"] = False
        blocked = checker.build_stage040_review_report(finding_checks=tampered)
        self.assertFalse(blocked["review_valid"], blocked)
        self.assertEqual("FAIL_CLOSED", blocked["result"])
        self.assertEqual("IDS-STAGE040-REVIEW-GATE", blocked["next_gate"])
        self.assertFalse(blocked["github_upload_allowed"])

    def test_governance_closes_stage_only_to_separate_batch_review(self):
        batch = BATCH.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        self.assertIn('status: "stage040_completed_reviewed_local"', batch)
        self.assertIn('review_status: "passed"', batch)
        self.assertIn('current_task_id: "IDS-V0_1-STAGE040-REVIEW"', batch)
        self.assertIn(
            'next_allowed_task_id: "IDS-V0_1-BATCH-031-040-REVIEW-GATE"',
            batch,
        )
        self.assertIn('push_allowed: false', batch)
        self.assertIn('current_phase_id: "IDS-STAGE040-REVIEW"', roadmap)
        self.assertIn('current_task_id: "IDS-V0_1-STAGE040-REVIEW"', roadmap)
        self.assertIn(
            'next_gate_id: "IDS-V0_1-BATCH-031-040-REVIEW-GATE"', roadmap
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
            == "EVT-IDS-V0_1-STAGE040-REVIEW-20260714-001"
        ]
        self.assertEqual(1, len(matching), matching)
        self.assertEqual("stage_review", matching[0]["event_type"])

    def test_review_document_and_report_preserve_safety_boundaries(self):
        text = REVIEW.read_text(encoding="utf-8")
        for term in (
            "STAGE040-REVIEW-F1",
            "STAGE040-REVIEW-F2",
            "STAGE040-REVIEW-F3",
            "completed_reviewed_local",
            "NO_BATCH_REVIEW_THIS_RUN",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE041_THIS_RUN",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

        report = self._review_checker().build_stage040_review_report()
        self.assertTrue(report["review_valid"], report)
        self.assertEqual("PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED", report["result"])
        self.assertEqual("completed_reviewed_local", report["stage_review_status"])
        self.assertEqual(
            "IDS-V0_1-BATCH-031-040-REVIEW-GATE", report["next_gate"]
        )
        for field in (
            "production_runtime_activation_performed",
            "raw_metadata_content_accessed",
            "fake_ids_business_data_used",
            "batch_review_performed",
            "github_upload_allowed",
            "app_reinstall_allowed",
            "stage041_started",
        ):
            with self.subTest(field=field):
                self.assertFalse(report[field])

    def test_cli_emits_reviewed_local_report(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(REVIEW_CHECKER)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        self.assertEqual("", completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["review_valid"], report)
        self.assertEqual(
            "IDS-V0_1-BATCH-031-040-REVIEW-GATE", report["next_gate"]
        )


if __name__ == "__main__":
    unittest.main()
