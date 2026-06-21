from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.ranking import (
    COMPONENT_WEIGHTS,
    RankingError,
    audit_candidate,
    select_daily_candidate,
    selection_payload,
    validate_ranking_weights,
)


FIXTURE = Path(__file__).parent / "fixtures" / "ranking_candidates.json"


def load_candidates() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["candidates"]


class RankingTests(unittest.TestCase):
    def test_weights_sum_to_100_points(self) -> None:
        self.assertEqual(validate_ranking_weights(), [])
        self.assertAlmostEqual(sum(COMPONENT_WEIGHTS.values()), 100.0)

    def test_candidate_audit_matches_golden_score(self) -> None:
        audit = audit_candidate(load_candidates()[0])

        self.assertTrue(audit["eligible"])
        self.assertEqual(audit["source_id"], "arxiv:2401.00001")
        self.assertEqual(audit["total_score"], 85.5)
        self.assertEqual(audit["component_scores"]["frontier_signal"], 18.0)
        self.assertEqual(audit["component_scores"]["evidence_reliability"], 20.0)

    def test_metadata_conflict_blocks_before_ranking(self) -> None:
        audit = audit_candidate(load_candidates()[1])

        self.assertFalse(audit["eligible"])
        self.assertEqual(audit["total_score"], 0.0)
        self.assertIn("arXiv metadata_conflicts is non-empty", audit["blocking_reasons"])

    def test_missing_p0_claim_blocks_candidate(self) -> None:
        candidate = load_candidates()[0]
        candidate["evidence_claims"] = []

        audit = audit_candidate(candidate)

        self.assertFalse(audit["eligible"])
        self.assertIn("P0 evidence is required before ranking", audit["blocking_reasons"])

    def test_recent_selection_blocks_duplicate_source(self) -> None:
        with self.assertRaisesRegex(RankingError, "No eligible"):
            select_daily_candidate(load_candidates()[:1], recent_source_ids=["arxiv:2401.00001"])

    def test_selection_payload_keeps_ineligible_audits(self) -> None:
        payload = selection_payload(load_candidates())

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["selected"]["source_id"], "arxiv:2401.00001")
        self.assertEqual([audit["source_id"] for audit in payload["audits"]], ["arxiv:2401.00001", "arxiv:2401.00002"])

    def test_cli_ranks_candidates_from_fixture(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["rank-candidates", "--path", str(FIXTURE), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["selected"]["source_id"], "arxiv:2401.00001")
        self.assertEqual(payload["selected"]["total_score"], 85.5)


if __name__ == "__main__":
    unittest.main()
