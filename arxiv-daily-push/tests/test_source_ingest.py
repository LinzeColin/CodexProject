from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from arxiv_daily_push.arxiv_adapter import ArxivQuery
from arxiv_daily_push.cli import main
from arxiv_daily_push.source_ingest import SOURCE_INGEST_MODEL_ID, ingest_latest_arxiv, validate_source_batch


FIXTURE = Path(__file__).parent / "fixtures" / "arxiv_atom_sample.xml"


def fixture_fetcher(query: ArxivQuery) -> str:
    assert query.search_query == "cat:cs.AI"
    return FIXTURE.read_text(encoding="utf-8")


class SourceIngestTests(unittest.TestCase):
    def test_ingest_latest_arxiv_returns_unseen_source_items(self) -> None:
        batch = ingest_latest_arxiv(
            search_query="cat:cs.AI",
            generated_at="2026-07-01T05:00:00+10:00",
            max_results=1,
            fetcher=fixture_fetcher,
        )

        self.assertEqual(batch["model_id"], SOURCE_INGEST_MODEL_ID)
        self.assertEqual(batch["status"], "pass")
        self.assertEqual(batch["new_item_count"], 1)
        self.assertEqual(batch["new_items"][0]["source_id"], "arxiv:2401.00001")
        self.assertFalse(batch["source_policy"]["pdf_download_enabled"])
        self.assertFalse(validate_source_batch(batch))

    def test_ingest_latest_arxiv_blocks_when_all_items_seen(self) -> None:
        batch = ingest_latest_arxiv(
            search_query="cat:cs.AI",
            generated_at="2026-07-01T05:00:00+10:00",
            max_results=1,
            seen_source_ids=["arxiv:2401.00001"],
            fetcher=fixture_fetcher,
        )

        self.assertEqual(batch["status"], "blocked")
        self.assertEqual(batch["duplicate_source_ids"], ["arxiv:2401.00001"])
        self.assertIn("no unseen", " ".join(batch["blocking_reasons"]))
        self.assertFalse(validate_source_batch(batch))

    def test_ingest_latest_arxiv_blocks_network_errors(self) -> None:
        def failing_fetcher(query: ArxivQuery) -> str:
            raise TimeoutError("network timeout")

        batch = ingest_latest_arxiv(
            search_query="cat:cs.AI",
            generated_at="2026-07-01T05:00:00+10:00",
            max_results=1,
            fetcher=failing_fetcher,
        )

        self.assertEqual(batch["status"], "blocked")
        self.assertIn("network timeout", " ".join(batch["blocking_reasons"]))

    def test_ingest_latest_arxiv_blocks_window_a_over_sized_canary(self) -> None:
        batch = ingest_latest_arxiv(
            search_query="cat:cs.AI",
            generated_at="2026-07-01T05:00:00+10:00",
            max_results=11,
            fetcher=fixture_fetcher,
        )

        self.assertEqual(batch["status"], "blocked")
        self.assertIn("max_results", " ".join(batch["blocking_reasons"]))

    def test_cli_fetch_arxiv_latest_uses_ingest_payload(self) -> None:
        fake_batch = {
            "ingest_id": "source-ingest:arxiv-latest",
            "model_id": SOURCE_INGEST_MODEL_ID,
            "project_id": "arxiv-daily-push",
            "source_adapter": "arxiv.atom.v1",
            "generated_at": "2026-07-01T05:00:00+10:00",
            "status": "pass",
            "request": {"url": "https://export.arxiv.org/api/query", "search_query": "cat:cs.AI"},
            "source_policy": {
                "network_fetch_enabled": True,
                "pdf_download_enabled": False,
                "bulk_harvest_enabled": False,
            },
            "seen_source_ids": [],
            "duplicate_source_ids": [],
            "source_items": [],
            "new_items": [
                {
                    "source_id": "arxiv:2401.00001",
                    "source_type": "arxiv",
                    "source_adapter": "arxiv.atom.v1",
                    "stable_id": "2401.00001",
                    "title": "Example",
                    "retrieved_at": "2026-07-01T05:00:00+10:00",
                    "canonical_url": "https://arxiv.org/abs/2401.00001",
                    "metadata": {"arxiv": {}},
                    "content_refs": [{"ref_id": "abstract", "ref_type": "html", "uri": "https://arxiv.org/abs/2401.00001"}],
                    "license": {"status": "unknown", "usage": "private_learning_link_only"},
                }
            ],
            "new_item_count": 1,
            "blocking_reasons": [],
        }
        buffer = io.StringIO()
        with patch("arxiv_daily_push.cli.ingest_latest_arxiv", return_value=fake_batch):
            with redirect_stdout(buffer):
                result = main([
                    "fetch-arxiv-latest",
                    "--query",
                    "cat:cs.AI",
                    "--max-results",
                    "1",
                    "--generated-at",
                    "2026-07-01T05:00:00+10:00",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], SOURCE_INGEST_MODEL_ID)
        self.assertEqual(payload["new_item_count"], 1)


if __name__ == "__main__":
    unittest.main()
