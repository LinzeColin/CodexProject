from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.arxiv_adapter import ArxivQuery
from arxiv_daily_push.cli import main
from arxiv_daily_push.daily_input import (
    DAILY_INPUT_BUILDER_MODEL_ID,
    build_daily_input_package,
    validate_daily_input_report,
)
from arxiv_daily_push.source_ingest import ingest_latest_arxiv


FIXTURE = Path(__file__).parent / "fixtures" / "arxiv_atom_sample.xml"


def fixture_fetcher(query: ArxivQuery) -> str:
    assert query.search_query == "cat:cs.AI"
    return FIXTURE.read_text(encoding="utf-8")


def source_batch() -> dict:
    return ingest_latest_arxiv(
        search_query="cat:cs.AI",
        generated_at="2026-07-01T05:00:00+10:00",
        max_results=1,
        fetcher=fixture_fetcher,
    )


class DailyInputTests(unittest.TestCase):
    def test_build_daily_input_from_arxiv_source_batch(self) -> None:
        report = build_daily_input_package(
            source_batch(),
            date="2026-07-01",
            generated_at="2026-07-01T05:00:00+10:00",
        )

        self.assertEqual(report["model_id"], DAILY_INPUT_BUILDER_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["daily_input_ready"])
        self.assertEqual(report["selection"]["status"], "pass")
        self.assertFalse(report["source_policy"]["pdf_download_enabled"])
        self.assertFalse(report["source_policy"]["bulk_harvest_enabled"])
        daily_input = report["daily_input"]
        self.assertEqual(daily_input["source_item"]["source_id"], "arxiv:2401.00001")
        self.assertEqual(daily_input["claims"][0]["priority"], "P0")
        self.assertIn(
            "This synthetic fixture describes an evidence-grounded AI system.",
            daily_input["claims"][0]["locator"]["quote"],
        )
        self.assertFalse(validate_daily_input_report(report))

    def test_build_daily_input_blocks_without_arxiv_summary(self) -> None:
        batch = source_batch()
        blocked_batch = copy.deepcopy(batch)
        blocked_batch["new_items"][0]["metadata"]["arxiv"]["summary"] = ""

        report = build_daily_input_package(
            blocked_batch,
            date="2026-07-01",
            generated_at="2026-07-01T05:00:00+10:00",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["daily_input_ready"])
        self.assertIn("summary", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_daily_input_report(report))

    def test_build_daily_input_blocks_when_selected_source_was_recent(self) -> None:
        report = build_daily_input_package(
            source_batch(),
            date="2026-07-01",
            generated_at="2026-07-01T05:00:00+10:00",
            recent_source_ids=["arxiv:2401.00001"],
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("already selected recently", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_daily_input_report(report))

    def test_cli_build_daily_input_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            batch_path = Path(tmp) / "source-batch.json"
            batch_path.write_text(json.dumps(source_batch()), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "build-daily-input",
                        "--source-batch",
                        str(batch_path),
                        "--date",
                        "2026-07-01",
                        "--generated-at",
                        "2026-07-01T05:00:00+10:00",
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], DAILY_INPUT_BUILDER_MODEL_ID)
        self.assertTrue(payload["daily_input_ready"])


if __name__ == "__main__":
    unittest.main()
