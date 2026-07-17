from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s20_p2_confirmation_workbench as p2
from KMFA.tools import v015_s20_p3_recalculation_publication as kernel


class RecalculationPublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.confirmation_path = root / "confirmation.jsonl"
        self.publication_path = root / "publication.jsonl"
        self.confirmation = p2.ConfirmationWorkbench(self.confirmation_path)
        self.workbench = kernel.RecalculationPublicationWorkbench(self.confirmation_path, self.publication_path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def confirm(self, issue_id: str = "ISSUE-S20P2-001", action_id: str = "USE_REGISTERED_PROJECT", suffix: str = "one") -> dict:
        preview = self.confirmation.preview(issue_id, action_id, actor_role="ROLE::DATA_STEWARD")
        return self.confirmation.confirm(
            issue_id, action_id, actor_id="steward", actor_role="ROLE::DATA_STEWARD",
            reason_zh="已核对业务依据并允许受影响链重算", preview_id=preview["preview_id"],
            preview_token=preview["preview_token"], idempotency_key=f"s20p3-confirm-{suffix}-001",
        )["event"]

    def start(self, event: dict, suffix: str = "one") -> dict:
        return self.workbench.start_recalculation(
            event["event_id"], actor_id="steward", actor_role="ROLE::DATA_STEWARD",
            idempotency_key=f"s20p3-recalculate-{suffix}-001",
        )

    def decide(self, job: dict, decision: str, suffix: str = "one", **kwargs) -> dict:
        preview = self.workbench.publication_preview(job["job_id"], decision, actor_role="ROLE::MANAGEMENT")
        return self.workbench.decide(
            job["job_id"], decision, actor_id="manager", actor_role="ROLE::MANAGEMENT",
            reason_zh="已核对数字、报告和四个页面的一致性", preview_id=preview["preview_id"],
            preview_token=preview["preview_token"], idempotency_key=f"s20p3-decision-{suffix}-001", **kwargs,
        )

    def test_active_confirmation_is_required(self) -> None:
        with self.assertRaisesRegex(kernel.RecalculationError, "ACTIVE_CONFIRMATION_REQUIRED"):
            self.workbench.start_recalculation(
                "CTRL-S20P2-0001", actor_id="steward", actor_role="ROLE::DATA_STEWARD",
                idempotency_key="s20p3-recalculate-missing-001",
            )

    def test_impact_graph_recalculates_only_registered_chain(self) -> None:
        event = self.confirm()
        before = self.workbench.current_publication()
        job = self.start(event)
        self.assertEqual(set(job["affected_by_type"]["FACT"]), {"FACT::PROJECT_REVENUE_CENTS", "FACT::PROJECT_COST_CENTS"})
        self.assertEqual(set(job["affected_by_type"]["METRIC"]), {"METRIC::PROJECT_MARGIN_CENTS", "METRIC::COLLECTION_RATIO_BPS"})
        self.assertEqual(job["candidate_snapshot"]["facts"]["unrelated_cash_cents"], before["facts"]["unrelated_cash_cents"])
        self.assertEqual(job["candidate_snapshot"]["facts"]["project_collection_cents"], before["facts"]["project_collection_cents"])

    def test_unknown_or_cyclic_impact_graph_fails_closed(self) -> None:
        with self.assertRaisesRegex(kernel.RecalculationError, "IMPACT_SCOPE_UNKNOWN"):
            kernel.analyze_impact(["CONTROL::UNKNOWN"])
        graph = kernel.impact_graph()
        graph["edges"].append(["PAGE::PROJECT", "CONTROL::PROJECT_ASSIGNMENT"])
        with self.assertRaisesRegex(kernel.RecalculationError, "IMPACT_SCOPE_UNKNOWN"):
            kernel.analyze_impact(["CONTROL::PROJECT_ASSIGNMENT"], graph)

    def test_recalculation_failure_keeps_old_publication(self) -> None:
        event = self.confirm()
        before = self.workbench.current_publication()["snapshot_hash"]
        with self.assertRaisesRegex(kernel.RecalculationError, "RECALCULATION_FAILED"):
            self.workbench.start_recalculation(
                event["event_id"], actor_id="steward", actor_role="ROLE::DATA_STEWARD",
                idempotency_key="s20p3-recalculate-failure-001", simulate_failure=True,
            )
        self.assertEqual(self.workbench.current_publication()["snapshot_hash"], before)
        self.assertEqual(self.workbench.jobs()["job_count"], 0)

    def test_comparison_explains_all_number_and_report_changes(self) -> None:
        comparison = self.start(self.confirm())["comparison"]
        self.assertGreaterEqual(comparison["numeric_change_count"], 3)
        self.assertEqual(comparison["report_change_count"], 4)
        self.assertEqual(comparison["difference_explanation_count"], comparison["numeric_change_count"] + 4)
        self.assertTrue(all(row["explanation_zh"] for row in comparison["numeric_changes"] + comparison["report_changes"]))

    def test_missing_difference_explanation_blocks_publication(self) -> None:
        comparison = self.start(self.confirm())["comparison"]
        comparison["numeric_changes"][0]["explanation_zh"] = ""
        with self.assertRaisesRegex(kernel.RecalculationError, "DIFFERENCE_EXPLANATION_REQUIRED"):
            kernel.assert_comparison_explained(comparison)

    def test_retain_choice_keeps_old_version(self) -> None:
        job = self.start(self.confirm())
        before = self.workbench.current_publication()["publication_version_id"]
        result = self.decide(job, "KEEP_CURRENT")
        self.assertEqual(result["event"]["event_type"], "PUBLICATION_RETAINED")
        self.assertEqual(result["current_publication"]["publication_version_id"], before)

    def test_publish_requires_exact_preview_and_is_idempotent(self) -> None:
        job = self.start(self.confirm())
        with self.assertRaisesRegex(kernel.RecalculationError, "PUBLICATION_PREVIEW_REQUIRED"):
            self.workbench.decide(
                job["job_id"], "PUBLISH_CANDIDATE", actor_id="manager", actor_role="ROLE::MANAGEMENT",
                reason_zh="不能绕过预览", idempotency_key="s20p3-publish-no-preview-001",
            )
        result = self.decide(job, "PUBLISH_CANDIDATE")
        repeated = self.workbench.decide(
            job["job_id"], "PUBLISH_CANDIDATE", actor_id="manager", actor_role="ROLE::MANAGEMENT",
            reason_zh="已核对数字、报告和四个页面的一致性",
            preview_id="ignored-after-idempotency", preview_token="ignored-after-idempotency",
            idempotency_key="s20p3-decision-one-001",
        )
        self.assertEqual(result["event"]["event_id"], repeated["event"]["event_id"])
        self.assertEqual(result["current_publication"]["publication_version_id"], "PUB-S20P3-0002")

    def test_page_mismatch_or_publication_failure_retains_old_version(self) -> None:
        job = self.start(self.confirm())
        before = self.workbench.current_publication()["publication_version_id"]
        candidate = copy.deepcopy(job["candidate_snapshot"])
        candidate["views"]["homepage"]["project_margin_cents"] += 1
        with self.assertRaisesRegex(kernel.RecalculationError, "PAGE_SYNC_BLOCKED"):
            self.decide(job, "PUBLISH_CANDIDATE", "mismatch", validation_candidate=candidate)
        self.assertEqual(self.workbench.current_publication()["publication_version_id"], before)
        with self.assertRaisesRegex(kernel.RecalculationError, "PUBLICATION_FAILED"):
            self.decide(job, "PUBLISH_CANDIDATE", "failure", simulate_failure=True)
        self.assertEqual(self.workbench.current_publication()["publication_version_id"], before)

    def test_publish_is_consistent_after_restart_and_history_detects_tamper(self) -> None:
        self.decide(self.start(self.confirm()), "PUBLISH_CANDIDATE")
        restarted = kernel.RecalculationPublicationWorkbench(self.confirmation_path, self.publication_path)
        current = restarted.current_publication()
        views = {view_id: restarted.view(view_id) for view_id in kernel.VIEW_IDS}
        self.assertEqual(len({row["publication_version_id"] for row in views.values()}), 1)
        self.assertEqual(len({row["shared_metric_fingerprint"] for row in views.values()}), 1)
        self.assertEqual(current["consistency"]["view_count"], 4)
        rows = self.publication_path.read_text(encoding="utf-8").splitlines()
        row = json.loads(rows[0])
        row["actor_id"] = "tampered"
        self.publication_path.write_text(json.dumps(row, ensure_ascii=False) + "\n" + "\n".join(rows[1:]) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(kernel.RecalculationError, "EVENT_TAMPERED"):
            restarted.history()

    def test_public_verification_is_63_of_63(self) -> None:
        report = kernel.public_verification()
        self.assertEqual((report["check_count"], report["pass_count"], report["fail_count"]), (63, 63, 0))


if __name__ == "__main__":
    unittest.main()
