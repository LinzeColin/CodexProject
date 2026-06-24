from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from arxiv_daily_push.cli import main
from arxiv_daily_push.top_journal_adapter import (
    TOP_JOURNAL_INGEST_MODEL_ID,
    TopJournalQuery,
    build_top_journal_rss_url,
    ingest_latest_top_journal,
    parse_top_journal_rss,
    validate_top_journal_source_batch,
)


FIXTURES = Path(__file__).parent / "fixtures"
NATURE_RSS = FIXTURES / "nature_rss_sample.xml"
GENERATED_AT = "2026-06-24T09:30:00+10:00"


class TopJournalAdapterTests(unittest.TestCase):
    def test_build_nature_url_uses_official_public_rss(self) -> None:
        self.assertEqual(build_top_journal_rss_url(TopJournalQuery(journal="nature")), "https://www.nature.com/nature.rss")

    def test_parse_nature_rss_to_metadata_only_source_items(self) -> None:
        items = parse_top_journal_rss(NATURE_RSS.read_text(encoding="utf-8"), journal="nature", retrieved_at=GENERATED_AT)

        self.assertEqual([item["source_id"] for item in items], ["nature:s41586-026-10807-x", "nature:s41586-026-10799-8"])
        item = items[0]
        self.assertEqual(item["source_type"], "rss")
        self.assertEqual(item["source_adapter"], "nature.rss.v1")
        self.assertEqual(item["metadata"]["identity"]["canonical_document_id"], "nature:s41586-026-10807-x")
        self.assertEqual(item["metadata"]["top_journal"]["journal"], "Nature")
        self.assertEqual(item["license"]["usage"], "metadata_and_link_only_no_fulltext_download")
        self.assertNotIn("pdf", json.dumps(item["content_refs"]).lower())

    def test_ingest_nature_allows_duplicate_window_without_hard_failure(self) -> None:
        batch = ingest_latest_top_journal(
            journal="nature",
            generated_at=GENERATED_AT,
            seen_source_ids=["nature:s41586-026-10807-x"],
            fetcher=lambda _query: NATURE_RSS.read_text(encoding="utf-8"),
        )

        self.assertEqual(batch["model_id"], TOP_JOURNAL_INGEST_MODEL_ID)
        self.assertEqual(batch["status"], "pass")
        self.assertEqual(batch["new_item_count"], 1)
        self.assertEqual(batch["duplicate_source_ids"], ["nature:s41586-026-10807-x"])
        self.assertFalse(validate_top_journal_source_batch(batch))

    def test_ingest_nature_blocks_invalid_xml_fail_closed(self) -> None:
        batch = ingest_latest_top_journal(
            journal="nature",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: "<rss>",
        )

        self.assertEqual(batch["status"], "blocked")
        self.assertIn("Invalid top-journal RSS XML", " ".join(batch["blocking_reasons"]))

    def test_cli_fetch_top_journal_latest_outputs_batch(self) -> None:
        fake_batch = ingest_latest_top_journal(
            journal="nature",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: NATURE_RSS.read_text(encoding="utf-8"),
        )
        buffer = io.StringIO()
        with patch("arxiv_daily_push.cli.ingest_latest_top_journal", return_value=fake_batch):
            with redirect_stdout(buffer):
                result = main([
                    "fetch-top-journal-latest",
                    "--journal",
                    "nature",
                    "--generated-at",
                    GENERATED_AT,
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TOP_JOURNAL_INGEST_MODEL_ID)
        self.assertEqual(payload["new_item_count"], 2)


if __name__ == "__main__":
    unittest.main()
