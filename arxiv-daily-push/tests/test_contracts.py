from __future__ import annotations

import unittest

from arxiv_daily_push.contracts import stable_content_hash, validate_evidence_claim, validate_source_item


class ContractTests(unittest.TestCase):
    def test_source_item_contract_accepts_arxiv_without_arxiv_only_shape(self) -> None:
        item = {
            "source_id": "arxiv:2401.00001",
            "source_type": "arxiv",
            "source_adapter": "arxiv.v1",
            "stable_id": "2401.00001",
            "title": "A Useful Paper",
            "retrieved_at": "2026-06-21T05:00:00+10:00",
            "canonical_url": "https://arxiv.org/abs/2401.00001",
            "metadata": {"authors": ["Example Author"], "categories": ["cs.AI"]},
            "content_refs": [{"ref_id": "abs", "ref_type": "abstract", "uri": "https://arxiv.org/abs/2401.00001"}],
            "license": {"status": "unknown", "usage": "private_learning"},
        }

        self.assertEqual(validate_source_item(item), [])

    def test_source_item_contract_accepts_future_source_type(self) -> None:
        item = {
            "source_id": "github:owner/repo#1",
            "source_type": "github",
            "source_adapter": "github.issues.v1",
            "stable_id": "owner/repo#1",
            "title": "Issue title",
            "retrieved_at": "2026-06-21T05:00:00+10:00",
            "canonical_url": "https://github.com/owner/repo/issues/1",
            "metadata": {"repository": "owner/repo"},
            "content_refs": [{"ref_id": "issue", "ref_type": "html", "uri": "https://github.com/owner/repo/issues/1"}],
            "license": {"status": "unknown", "usage": "future_source_test"},
        }

        self.assertEqual(validate_source_item(item), [])

    def test_p0_claim_requires_locator_evidence(self) -> None:
        claim = {
            "claim_id": "claim-001",
            "source_id": "arxiv:2401.00001",
            "claim_type": "reported_result",
            "priority": "P0",
            "statement": "The paper reports a measurable result.",
            "locator": {"locator_type": "paper"},
            "support_status": "supported",
            "extracted_at": "2026-06-21T05:10:00+10:00",
        }

        self.assertEqual(
            validate_evidence_claim(claim),
            ["EvidenceClaim P0 locator must include stable_url, page, section, table, figure, or quote"],
        )

    def test_stable_content_hash_is_order_independent(self) -> None:
        self.assertEqual(stable_content_hash({"b": 2, "a": 1}), stable_content_hash({"a": 1, "b": 2}))


if __name__ == "__main__":
    unittest.main()
