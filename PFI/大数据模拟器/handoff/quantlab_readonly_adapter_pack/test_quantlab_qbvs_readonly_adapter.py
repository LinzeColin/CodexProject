from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from quantlab_qbvs_readonly_adapter import (
    build_independent_validation_record,
    read_qbvs_bundle,
    read_qbvs_campaign,
    read_qbvs_promotion_candidates,
)


class QBVSReadonlyAdapterTest(unittest.TestCase):
    def test_bundle_campaign_and_promotion_are_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "quantlab_bundle_manifest.json").write_text(json.dumps({
                "writes_quantlab_database": False,
                "writes_quantlab_source": False,
            }), encoding="utf-8")
            (bundle / "quantlab_ingestion_payload.json").write_text(json.dumps({
                "ingestion_mode": "external_evidence_only",
            }), encoding="utf-8")
            (bundle / "quantlab_candidate_strategies.csv").write_text(
                "strategy_id,requires_exact_validation,requires_fund_rule_review\ns1,true,false\n",
                encoding="utf-8",
            )
            evidence = read_qbvs_bundle(bundle)
            self.assertEqual(evidence["approval_state"], "review_only")
            self.assertTrue(evidence["requires_exact_rerun"])

            campaign = root / "campaign"
            campaign.mkdir()
            (campaign / "campaign_plan.json").write_text(json.dumps({
                "starts_background_processes": False,
            }), encoding="utf-8")
            (campaign / "campaign_status.csv").write_text("part,status\n1,pending\n", encoding="utf-8")
            campaign_evidence = read_qbvs_campaign(campaign)
            self.assertEqual(campaign_evidence["status_rows"], 1)

            promotion = root / "promotion.csv"
            promotion.write_text(
                "strategy_id,promotion_state,requires_quantlab_exact_rerun,requires_user_approval_before_strategy_library_write\ns1,external_candidate,true,true\n",
                encoding="utf-8",
            )
            promotion_evidence = read_qbvs_promotion_candidates(promotion)
            self.assertTrue(promotion_evidence["requires_user_approval"])

            record = build_independent_validation_record(evidence)
            self.assertEqual(record["status"], "ReviewOnly")


if __name__ == "__main__":
    unittest.main()
