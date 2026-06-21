from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.arxiv_adapter import ArxivAdapterError, ArxivQuery, build_query_url, parse_atom_feed
from arxiv_daily_push.cli import main
from arxiv_daily_push.contracts import validate_source_item


FIXTURE = Path(__file__).parent / "fixtures" / "arxiv_atom_sample.xml"


class ArxivAdapterTests(unittest.TestCase):
    def test_build_query_url_encodes_query_and_caps_results(self) -> None:
        url = build_query_url(ArxivQuery(search_query="cat:cs.AI AND ti:evidence", start=0, max_results=5))

        self.assertTrue(url.startswith("https://export.arxiv.org/api/query?"))
        self.assertIn("search_query=cat%3Acs.AI+AND+ti%3Aevidence", url)
        self.assertIn("max_results=5", url)
        self.assertIn("sortBy=submittedDate", url)

    def test_build_query_url_rejects_large_phase3_pull(self) -> None:
        with self.assertRaisesRegex(ArxivAdapterError, "max_results"):
            build_query_url(ArxivQuery(search_query="cat:cs.AI", max_results=500))

    def test_parse_atom_feed_maps_entry_to_generic_source_item(self) -> None:
        items = parse_atom_feed(FIXTURE.read_text(encoding="utf-8"), retrieved_at="2026-06-21T05:00:00+10:00")

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["source_id"], "arxiv:2401.00001")
        self.assertEqual(item["source_type"], "arxiv")
        self.assertEqual(item["source_adapter"], "arxiv.atom.v1")
        self.assertEqual(item["metadata"]["arxiv"]["versioned_id"], "2401.00001v2")
        self.assertEqual(item["metadata"]["arxiv"]["primary_category"], "cs.AI")
        self.assertEqual(item["metadata"]["arxiv"]["authors"], ["Ada Example", "Lin Test"])
        self.assertEqual(validate_source_item(item), [])

    def test_parse_atom_feed_raises_on_api_error_entry(self) -> None:
        xml = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors#bad</id><title>Error</title><summary>bad query</summary></entry></feed>"""

        with self.assertRaisesRegex(ArxivAdapterError, "bad query"):
            parse_atom_feed(xml, retrieved_at="2026-06-21T05:00:00+10:00")

    def test_cli_renders_arxiv_url_without_fetching(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["arxiv-url", "--query", "cat:cs.AI", "--max-results", "3"])

        self.assertEqual(result, 0)
        self.assertIn("max_results=3", buffer.getvalue())

    def test_cli_parses_arxiv_atom_fixture(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["parse-arxiv-atom", "--path", str(FIXTURE), "--retrieved-at", "2026-06-21T05:00:00+10:00"])

        self.assertEqual(result, 0)
        self.assertIn("arxiv:2401.00001", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
