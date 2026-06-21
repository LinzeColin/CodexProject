from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.evidence_gate import build_claim_ledger, gate_publication


FIXTURE = Path(__file__).parent / "fixtures" / "claim_ledger_input.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class EvidenceGateTests(unittest.TestCase):
    def test_gate_publication_allows_supported_p0_claims(self) -> None:
        data = load_fixture()

        result = gate_publication(
            data["source_item"],
            data["claims"],
            run_id=data["run_id"],
            publication_id=data["publication_id"],
            publication_type=data["publication_type"],
            created_at=data["created_at"],
        )

        self.assertTrue(result["publish_allowed"])
        self.assertEqual(result["publication"]["status"], "ready")
        self.assertEqual(result["p0_claim_count"], 1)
        self.assertTrue(result["ledger"]["claims"][0]["claim_id"].startswith("claim:arxiv:2401.00001:0:"))

    def test_missing_p0_locator_blocks_publication(self) -> None:
        data = load_fixture()
        data["claims"][0]["locator"] = {"locator_type": "abstract"}

        result = gate_publication(
            data["source_item"],
            data["claims"],
            run_id=data["run_id"],
            publication_id=data["publication_id"],
            publication_type=data["publication_type"],
            created_at=data["created_at"],
        )

        self.assertFalse(result["publish_allowed"])
        self.assertEqual(result["publication"]["status"], "blocked")
        self.assertIn("EvidenceClaim P0 locator must include", result["blocking_reasons"][0])

    def test_unsupported_p0_blocks_publication(self) -> None:
        data = load_fixture()
        data["claims"][0]["support_status"] = "unsupported"

        result = gate_publication(
            data["source_item"],
            data["claims"],
            run_id=data["run_id"],
            publication_id=data["publication_id"],
            publication_type=data["publication_type"],
            created_at=data["created_at"],
        )

        self.assertFalse(result["publish_allowed"])
        self.assertIn("P0 support_status must be supported", " ".join(result["blocking_reasons"]))

    def test_arxiv_peer_review_claim_requires_independent_evidence(self) -> None:
        data = load_fixture()
        data["claims"][0]["statement"] = "This arXiv paper is peer reviewed."

        result = gate_publication(
            data["source_item"],
            data["claims"],
            run_id=data["run_id"],
            publication_id=data["publication_id"],
            publication_type=data["publication_type"],
            created_at=data["created_at"],
        )

        self.assertFalse(result["publish_allowed"])
        self.assertIn("peer-review status needs independent", " ".join(result["blocking_reasons"]))

    def test_metadata_conflict_blocks_publication(self) -> None:
        data = load_fixture()
        data["source_item"]["metadata"]["arxiv"]["metadata_conflicts"] = ["title mismatch"]

        ledger = build_claim_ledger(data["source_item"], data["claims"], extracted_at=data["created_at"])

        self.assertEqual(ledger["status"], "blocked")
        self.assertIn("arXiv metadata_conflicts is non-empty", ledger["blocking_reasons"])

    def test_cli_gates_publication_fixture(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["gate-publication", "--path", str(FIXTURE), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertTrue(payload["publish_allowed"])
        self.assertEqual(payload["publication"]["status"], "ready")


if __name__ == "__main__":
    unittest.main()
