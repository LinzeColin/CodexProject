from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = ROOT / "OpenAIDatabase"
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import evaluate_memory_automation_c_e2e as evaluator  # noqa: E402
import memory_automation_c as automation_c  # noqa: E402


CONFIG = DATABASE_DIR / "config/evaluation/memory_automation_c_e2e_v1.json"
REPORT = DATABASE_DIR / "data/derived/evaluation/memory_gold/reports/automation_c_e2e_v1.json"
BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def mutation_details() -> dict[str, object]:
    return {
        "task_id": "TSK.OpenAIDatabase.PAM1.0009",
        "acceptance_id": "ACC.OpenAIDatabase.PAM1.0009",
        "transaction_id": "mut_" + "b" * 20,
        "operation": "add",
        "record_id": "mem_test_automation_c_0001",
        "idempotency_key": "memory-mutation:" + "a" * 64,
        "base_commit_sha": BASE_SHA,
        "source": {
            "type": "explicit_user",
            "ref": "user-message:synthetic:test",
            "observed_at": "2026-07-17T00:00:00Z",
            "evidence_hash": None,
        },
        "statement_sha256": "sha256:" + "3" * 64,
        "idempotent_replay": False,
        "manual_approval_required": False,
        "model_inference_persisted": 0,
        "generated_views_refresh_owner": "scripts/memory_automation_c.py",
        "production_live_acceptance_task": "TSK.OpenAIDatabase.PAM1.0019",
        "automation_c": {
            "transaction_required": True,
            "branch": "automation-c/memory-mut_" + "b" * 20,
            "base_branch": "main",
            "same_repository_only": True,
            "non_draft_pr_count": 1,
            "issue_mutations": 0,
            "direct_main_write": False,
            "required_ci": "Project Governance / governance",
            "settlement": "trusted_default_branch_api_only",
            "terminal_state": "PR=0/Issue=0/non-main=0",
            "live_transaction_glue_task": "TSK.OpenAIDatabase.PAM1.0017",
        },
    }


def mutation_plan(details: dict[str, object]) -> dict[str, object]:
    plan = evaluator.memory_cli.operation_plan(
        "mutate",
        details,
        write_capable=True,
        task_id="TSK.OpenAIDatabase.PAM1.0009",
        acceptance_id="ACC.OpenAIDatabase.PAM1.0009",
    )
    plan["required_idempotency_key"] = details["idempotency_key"]
    plan["required_write_guards"] = [
        "--apply",
        "--base-sha",
        "--idempotency-key",
        "exact_automation_c_branch",
    ]
    return plan


class MemoryAutomationCE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_tracked_seven_scenario_report_passes_every_hard_gate(self) -> None:
        evaluator.validate_config(self.config)
        self.assertEqual(self.report["status"], "PASS")
        self.assertTrue(all(self.report["hard_gates"].values()))
        self.assertEqual(self.report["metrics"]["scenario_count"], 7)
        self.assertEqual(self.report["metrics"]["passed_scenario_count"], 7)
        self.assertEqual(
            [row["scenario"] for row in self.report["cases"]],
            self.config["limits"]["required_scenarios"],
        )

    def test_success_failure_and_visibility_contracts_are_closed(self) -> None:
        cases = {row["scenario"]: row["observed"] for row in self.report["cases"]}
        for scenario in ("add", "update", "retire", "noop_duplicate"):
            self.assertEqual(cases[scenario]["terminal"], "MERGE_DELETE")
            self.assertEqual(cases[scenario]["profile_pass_count"], 5)
        self.assertTrue(cases["update"]["old_fact_invisible"])
        self.assertTrue(cases["retire"]["old_fact_invisible"])
        self.assertEqual(cases["dispute"]["terminal"], "CLOSE_DELETE")
        self.assertEqual(cases["invalid"]["terminal"], "PRECHECK_REJECT")
        self.assertEqual(cases["inference_rejected"]["terminal"], "PRECHECK_REJECT")
        for observed in cases.values():
            self.assertEqual(observed["final_audit"]["open_pr_count"], 0)
            self.assertEqual(observed["final_audit"]["open_issue_count"], 0)
            self.assertEqual(observed["final_audit"]["non_main_branch_count"], 0)

    def test_duplicate_replay_creates_no_second_record_pr_or_settlement(self) -> None:
        observed = next(
            row["observed"] for row in self.report["cases"] if row["scenario"] == "noop_duplicate"
        )
        self.assertEqual(observed["replay_write_count"], 0)
        self.assertEqual(observed["duplicate_record_count"], 0)
        self.assertEqual(observed["duplicate_pr_count"], 0)
        self.assertEqual(observed["duplicate_settlement_action"], "NOOP")

    def test_transaction_glue_binds_exact_marker_and_trusted_settlement(self) -> None:
        details = mutation_details()
        reservation = automation_c.build_reservation(
            details,
            expected_base_sha=BASE_SHA,
        )
        pr, created = automation_c.open_or_reuse_pr(None, reservation, head_sha=HEAD_SHA)
        reused, created_again = automation_c.open_or_reuse_pr(pr, reservation, head_sha=HEAD_SHA)
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(reused, pr)
        self.assertNotIn("user-message:synthetic:test", pr["body"])
        marker = automation_c.parse_transaction_marker(pr["body"])
        self.assertEqual(marker["head"], HEAD_SHA)
        self.assertEqual(marker["base"], BASE_SHA)
        decide = automation_c.load_settlement_decider(ROOT)
        decision = decide(
            automation_c.settlement_input(
                pr,
                reservation,
                workflow_conclusion="success",
                required_checks_pass=True,
            )
        )
        self.assertEqual(decision["action"], "MERGE_DELETE")

        tampered = copy.deepcopy(pr)
        tampered["body"] += pr["body"].splitlines()[0]
        with self.assertRaisesRegex(
            automation_c.AutomationCError,
            "transaction_marker_cardinality_invalid",
        ):
            automation_c.settlement_input(
                tampered,
                reservation,
                workflow_conclusion="success",
                required_checks_pass=True,
            )

    def test_plan_binding_and_idempotent_replay_fail_closed_without_second_pr(self) -> None:
        details = mutation_details()
        plan = mutation_plan(details)
        prepared = automation_c.prepare_from_plan(
            plan,
            head_sha=HEAD_SHA,
            repository=automation_c.REPOSITORY,
        )
        self.assertEqual(prepared["terminal_action"], "PR_TEMPLATE")
        self.assertIsNotNone(prepared["pull_request"])

        tampered = copy.deepcopy(plan)
        tampered["details"]["record_id"] = "mem_tampered_automation_c"
        with self.assertRaisesRegex(automation_c.AutomationCError, "mutation_plan_hash_mismatch"):
            automation_c.prepare_from_plan(
                tampered,
                head_sha=HEAD_SHA,
                repository=automation_c.REPOSITORY,
            )

        replay_details = copy.deepcopy(details)
        replay_details["idempotent_replay"] = True
        replay_details["automation_c"]["transaction_required"] = False
        replay_plan = mutation_plan(replay_details)
        replay = automation_c.prepare_from_plan(
            replay_plan,
            head_sha=HEAD_SHA,
            repository=automation_c.REPOSITORY,
        )
        self.assertTrue(replay["idempotent"])
        self.assertEqual(replay["terminal_action"], "NOOP")
        self.assertIsNone(replay["pull_request"])
        with self.assertRaisesRegex(automation_c.AutomationCError, "idempotent_transaction_pr_forbidden"):
            automation_c.open_or_reuse_pr(
                None,
                replay["reservation"],
                head_sha=HEAD_SHA,
            )


if __name__ == "__main__":
    unittest.main()
