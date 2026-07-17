from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import run_v015_s20_p3_recalculation_publication as runtime
from KMFA.tools import v015_s20_p1_data_update as p1
from KMFA.tools import v015_s20_p2_confirmation_workbench as p2
from KMFA.tools import v015_s20_p3_recalculation_publication as p3


class S20StageReviewIntegrationTests(unittest.TestCase):
    def test_three_pages_have_continuous_human_navigation(self) -> None:
        html = runtime.render_html()
        for token in (
            'aria-label="数据更新流程步骤"', "1 数据更新", "2 人工确认", "3 重算发布",
            'href="/data-update"', 'href="/confirmation-workbench"', 'href="/recalculation-publication"',
            ".s20-journey", "min-height:44px",
        ):
            self.assertIn(token, html)
        self.assertEqual(html.count('aria-label="数据更新流程步骤"'), 3)

    def test_p1_and_p2_share_source_identifiers(self) -> None:
        source_ids = {row["value"] for row in p1.SOURCE_OPTIONS}
        issues = p2.ConfirmationWorkbench(Path(tempfile.gettempdir()) / "s20-review-unused.jsonl").list_issues()
        self.assertTrue(all(row["source_id"] in source_ids for row in issues["issues"]))

    def test_recalculation_replay_rejects_wrong_confirmation_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            confirmation_path = root / "confirmation.jsonl"
            publication_path = root / "publication.jsonl"
            confirmation = p2.ConfirmationWorkbench(confirmation_path)
            preview = confirmation.preview("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_role="ROLE::DATA_STEWARD")
            event = confirmation.confirm(
                "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="steward",
                actor_role="ROLE::DATA_STEWARD", reason_zh="已核对业务依据和影响",
                preview_id=preview["preview_id"], preview_token=preview["preview_token"],
                idempotency_key="review-confirm-project-001",
            )["event"]
            workbench = p3.RecalculationPublicationWorkbench(confirmation_path, publication_path)
            workbench.start_recalculation(
                event["event_id"], actor_id="steward", actor_role="ROLE::DATA_STEWARD",
                idempotency_key="review-recalculate-project-001",
            )
            value = json.loads(publication_path.read_text(encoding="utf-8").splitlines()[0])
            value["trigger_control_event_hash"] = "sha256:" + "0" * 64
            value["event_hash"] = p3._fingerprint(p3._event_body(value))
            publication_path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(p3.RecalculationError, "CONFIRMATION_BINDING_INVALID"):
                p3.RecalculationPublicationWorkbench(confirmation_path, publication_path).current_publication()

    def test_end_to_end_contract_publishes_four_consistent_views(self) -> None:
        from KMFA.tools import v015_s20_stage_review_contract as contract

        rows = contract.integration_bindings()
        self.assertEqual(len(rows), 44)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))
        self.assertIn("P3-SAME-FINGERPRINT", {row["binding_id"] for row in rows})


if __name__ == "__main__":
    unittest.main()
