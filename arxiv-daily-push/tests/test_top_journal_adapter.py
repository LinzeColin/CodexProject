from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from arxiv_daily_push.cli import main
from arxiv_daily_push.top_journal_adapter import (
    LANCET_ONLINE_FIRST_RSS_URL,
    SCIENCE_RSS_URL,
    TOP_JOURNAL_INGEST_MODEL_ID,
    TopJournalQuery,
    build_top_journal_rss_url,
    ingest_latest_top_journal,
    parse_top_journal_rss,
    validate_top_journal_source_batch,
)


FIXTURES = Path(__file__).parent / "fixtures"
NATURE_RSS = FIXTURES / "nature_rss_sample.xml"
SCIENCE_RSS = FIXTURES / "science_rss_sample.xml"
LANCET_RSS = FIXTURES / "lancet_rss_sample.xml"
GENERATED_AT = "2026-06-24T09:30:00+10:00"


class TopJournalAdapterTests(unittest.TestCase):
    def test_build_nature_url_uses_official_public_rss(self) -> None:
        self.assertEqual(build_top_journal_rss_url(TopJournalQuery(journal="nature")), "https://www.nature.com/nature.rss")

    def test_build_science_url_uses_official_public_feed(self) -> None:
        self.assertEqual(build_top_journal_rss_url(TopJournalQuery(journal="science")), SCIENCE_RSS_URL)

    def test_build_lancet_url_uses_official_public_online_first_feed(self) -> None:
        self.assertEqual(build_top_journal_rss_url(TopJournalQuery(journal="lancet")), LANCET_ONLINE_FIRST_RSS_URL)

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

    def test_parse_science_rss_classifies_allowed_article_types_and_filters_news(self) -> None:
        items = parse_top_journal_rss(SCIENCE_RSS.read_text(encoding="utf-8"), journal="science", retrieved_at=GENERATED_AT)

        self.assertEqual(
            [item["source_id"] for item in items],
            [
                "science:10.1126/science.ads7910",
                "science:10.1126/science.adx1369",
                "science:10.1126/science.aei4111",
                "science:10.1126/science.aef0941",
            ],
        )
        self.assertEqual(
            [item["metadata"]["top_journal"]["article_type"] for item in items],
            ["research_article", "report", "review", "perspective"],
        )
        item = items[0]
        self.assertEqual(item["source_type"], "rss")
        self.assertEqual(item["source_adapter"], "science.rss.v1")
        self.assertEqual(item["metadata"]["identity"]["canonical_document_id"], "science:10.1126/science.ads7910")
        self.assertEqual(item["metadata"]["top_journal"]["journal"], "Science")
        self.assertEqual(item["metadata"]["top_journal"]["article_type_raw"], "Research Article")
        self.assertEqual(item["license"]["usage"], "metadata_and_link_only_no_fulltext_download")
        self.assertNotIn("pdf", json.dumps(item["content_refs"]).lower())

    def test_parse_lancet_rss_classifies_medical_article_types_and_filters_correspondence(self) -> None:
        items = parse_top_journal_rss(LANCET_RSS.read_text(encoding="utf-8"), journal="lancet", retrieved_at=GENERATED_AT)

        self.assertEqual(
            [item["source_id"] for item in items],
            [
                "lancet:10.1016/s0140-6736(26)01256-0",
                "lancet:10.1016/s0140-6736(26)01156-6",
                "lancet:10.1016/s0140-6736(26)01025-1",
            ],
        )
        self.assertEqual(
            [item["metadata"]["top_journal"]["article_type"] for item in items],
            ["article", "review", "series"],
        )
        item = items[0]
        self.assertEqual(item["source_type"], "rss")
        self.assertEqual(item["source_adapter"], "lancet.rss.v1")
        self.assertEqual(item["metadata"]["identity"]["canonical_document_id"], "lancet:10.1016/s0140-6736(26)01256-0")
        self.assertEqual(item["metadata"]["top_journal"]["journal"], "The Lancet")
        self.assertEqual(item["metadata"]["top_journal"]["article_type_raw"], "Articles")
        self.assertEqual(item["metadata"]["top_journal"]["index_alignment_gate"], "pass")
        self.assertEqual(item["metadata"]["top_journal"]["medical_indexing"]["pubmed_relation_gate"], "doi_query_ready")
        self.assertIn("pubmed.ncbi.nlm.nih.gov", item["metadata"]["top_journal"]["medical_indexing"]["pubmed_doi_query_url"])
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

    def test_ingest_science_allows_duplicate_doi_window_without_hard_failure(self) -> None:
        batch = ingest_latest_top_journal(
            journal="science",
            generated_at=GENERATED_AT,
            seen_source_ids=["science:10.1126/science.ads7910"],
            fetcher=lambda _query: SCIENCE_RSS.read_text(encoding="utf-8"),
        )

        self.assertEqual(batch["model_id"], TOP_JOURNAL_INGEST_MODEL_ID)
        self.assertEqual(batch["status"], "pass")
        self.assertEqual(batch["new_item_count"], 3)
        self.assertEqual(batch["duplicate_source_ids"], ["science:10.1126/science.ads7910"])
        self.assertFalse(validate_top_journal_source_batch(batch))

    def test_ingest_lancet_allows_duplicate_doi_window_without_hard_failure(self) -> None:
        batch = ingest_latest_top_journal(
            journal="lancet",
            generated_at=GENERATED_AT,
            seen_source_ids=["lancet:10.1016/s0140-6736(26)01256-0"],
            fetcher=lambda _query: LANCET_RSS.read_text(encoding="utf-8"),
        )

        self.assertEqual(batch["model_id"], TOP_JOURNAL_INGEST_MODEL_ID)
        self.assertEqual(batch["status"], "pass")
        self.assertEqual(batch["new_item_count"], 2)
        self.assertEqual(batch["duplicate_source_ids"], ["lancet:10.1016/s0140-6736(26)01256-0"])
        self.assertEqual(batch["source_policy"]["pubmed_relation_mode"], "doi_query_reference_only")
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

    def test_cli_fetch_top_journal_latest_outputs_science_batch(self) -> None:
        fake_batch = ingest_latest_top_journal(
            journal="science",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: SCIENCE_RSS.read_text(encoding="utf-8"),
        )
        buffer = io.StringIO()
        with patch("arxiv_daily_push.cli.ingest_latest_top_journal", return_value=fake_batch):
            with redirect_stdout(buffer):
                result = main([
                    "fetch-top-journal-latest",
                    "--journal",
                    "science",
                    "--generated-at",
                    GENERATED_AT,
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TOP_JOURNAL_INGEST_MODEL_ID)
        self.assertEqual(payload["journal"], "science")
        self.assertEqual(payload["new_item_count"], 4)

    def test_cli_fetch_top_journal_latest_outputs_lancet_batch(self) -> None:
        fake_batch = ingest_latest_top_journal(
            journal="lancet",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: LANCET_RSS.read_text(encoding="utf-8"),
        )
        buffer = io.StringIO()
        with patch("arxiv_daily_push.cli.ingest_latest_top_journal", return_value=fake_batch):
            with redirect_stdout(buffer):
                result = main([
                    "fetch-top-journal-latest",
                    "--journal",
                    "lancet",
                    "--generated-at",
                    GENERATED_AT,
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TOP_JOURNAL_INGEST_MODEL_ID)
        self.assertEqual(payload["journal"], "lancet")
        self.assertEqual(payload["new_item_count"], 3)


if __name__ == "__main__":
    unittest.main()
