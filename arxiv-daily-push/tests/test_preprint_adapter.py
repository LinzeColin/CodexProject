from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from arxiv_daily_push.cli import main
from arxiv_daily_push.preprint_adapter import (
    PREPRINT_INGEST_MODEL_ID,
    PreprintQuery,
    build_preprint_details_url,
    ingest_latest_preprints,
    parse_preprint_details,
    validate_preprint_source_batch,
)


FIXTURES = Path(__file__).parent / "fixtures"
BIORXIV = FIXTURES / "biorxiv_details_sample.json"
MEDRXIV = FIXTURES / "medrxiv_details_sample.json"
GENERATED_AT = "2026-06-24T09:30:00+10:00"


class PreprintAdapterTests(unittest.TestCase):
    def test_build_preprint_url_uses_public_details_endpoint(self) -> None:
        url = build_preprint_details_url(PreprintQuery(server="biorxiv", interval="2026-06-01/2026-06-23"))

        self.assertEqual(url, "https://api.biorxiv.org/details/biorxiv/2026-06-01/2026-06-23/0/json")

    def test_parse_biorxiv_details_to_preprint_source_item(self) -> None:
        items = parse_preprint_details(BIORXIV.read_text(encoding="utf-8"), server="biorxiv", retrieved_at=GENERATED_AT)

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["source_type"], "preprint")
        self.assertEqual(item["source_adapter"], "biorxiv.details.v1")
        self.assertEqual(item["source_id"], "biorxiv:10.1101-2026.06.23.660001")
        self.assertEqual(item["metadata"]["identity"]["canonical_document_id"], "doi:10.1101/2026.06.23.660001")
        self.assertEqual(item["metadata"]["preprint"]["version"], "1")
        self.assertEqual(item["license"]["status"], "cc_by_nc_nd")

    def test_ingest_medrxiv_allows_empty_or_duplicate_window_without_hard_failure(self) -> None:
        def fixture_fetcher(query: PreprintQuery) -> str:
            self.assertEqual(query.server, "medrxiv")
            return MEDRXIV.read_text(encoding="utf-8")

        batch = ingest_latest_preprints(
            server="medrxiv",
            generated_at=GENERATED_AT,
            interval="1d",
            seen_source_ids=["medrxiv:10.1101-2026.06.23.770001"],
            fetcher=fixture_fetcher,
        )

        self.assertEqual(batch["model_id"], PREPRINT_INGEST_MODEL_ID)
        self.assertEqual(batch["status"], "pass")
        self.assertEqual(batch["new_item_count"], 0)
        self.assertEqual(batch["duplicate_source_ids"], ["medrxiv:10.1101-2026.06.23.770001"])
        self.assertFalse(validate_preprint_source_batch(batch))

    def test_ingest_preprints_blocks_network_errors_fail_closed(self) -> None:
        def failing_fetcher(query: PreprintQuery) -> str:
            raise TimeoutError("metadata timeout")

        batch = ingest_latest_preprints(
            server="biorxiv",
            generated_at=GENERATED_AT,
            interval="1d",
            fetcher=failing_fetcher,
        )

        self.assertEqual(batch["status"], "blocked")
        self.assertIn("metadata timeout", " ".join(batch["blocking_reasons"]))

    def test_cli_fetch_preprint_latest_outputs_batch(self) -> None:
        fake_batch = ingest_latest_preprints(
            server="biorxiv",
            generated_at=GENERATED_AT,
            interval="1d",
            fetcher=lambda _query: BIORXIV.read_text(encoding="utf-8"),
        )
        buffer = io.StringIO()
        with patch("arxiv_daily_push.cli.ingest_latest_preprints", return_value=fake_batch):
            with redirect_stdout(buffer):
                result = main([
                    "fetch-preprint-latest",
                    "--server",
                    "biorxiv",
                    "--interval",
                    "1d",
                    "--generated-at",
                    GENERATED_AT,
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], PREPRINT_INGEST_MODEL_ID)
        self.assertEqual(payload["new_item_count"], 1)


if __name__ == "__main__":
    unittest.main()
