from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.source_ingest import SOURCE_INGEST_MODEL_ID
from arxiv_daily_push.stage1_real_replay import (
    STAGE1_REAL_REPLAY_ACCEPTANCE_ID,
    STAGE1_REAL_REPLAY_MODEL_ID,
    build_real_historical_arxiv_replay,
    build_submitted_date_query,
    validate_real_historical_arxiv_replay_report,
)


GENERATED_AT = "2026-06-23T21:45:00+10:00"


def high_value_summary(topic: str) -> str:
    return (
        f"This paper introduces a framework and benchmark dataset for agent learning, model evaluation, "
        f"decision automation, finance, market risk, privacy, security, cost efficiency, policy simulation, "
        f"optimization, and robust statistics in {topic}. The abstract is suitable for evidence-bound "
        "teaching because it states variables, mechanisms, outputs, and failure conditions."
    )


def source_item(index: int, as_of: date, *, future: bool = False) -> dict:
    stable_id = f"2606.{index:05d}"
    category = ["q-fin.RM", "cs.LG", "stat.ML", "eess.SY", "math.OC"][index % 5]
    updated = as_of + timedelta(days=2) if future else as_of
    return {
        "source_id": f"arxiv:{stable_id}",
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": stable_id,
        "title": f"Real historical replay candidate {index:02d} for market risk automation",
        "retrieved_at": f"{as_of.isoformat()}T05:00:00+10:00",
        "canonical_url": f"https://arxiv.org/abs/{stable_id}",
        "metadata": {
            "arxiv": {
                "versioned_id": f"{stable_id}v1",
                "summary": high_value_summary(f"as-of date {as_of.isoformat()}"),
                "primary_category": category,
                "categories": [category, "cs.AI"],
                "authors": [f"Author {index}"],
                "published": f"{as_of.isoformat()}T00:00:00Z",
                "updated": f"{updated.isoformat()}T00:00:00Z",
                "acknowledgement": "Thank you to arXiv for use of its open access interoperability.",
            }
        },
        "content_refs": [{"ref_type": "abstract", "uri": f"https://arxiv.org/abs/{stable_id}"}],
        "license": {"status": "unknown", "usage": "private_learning_link_only"},
        "evidence_refs": [f"https://arxiv.org/abs/{stable_id}"],
    }


def source_batch(as_of: date, index: int, *, future: bool = False) -> dict:
    item = source_item(index, as_of, future=future)
    queued = source_item(index + 1000, as_of)
    items = [item] if future else [item, queued]
    return {
        "ingest_id": "source-ingest:arxiv-latest",
        "model_id": SOURCE_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": "arxiv.atom.v1",
        "generated_at": f"{as_of.isoformat()}T05:00:00+10:00",
        "status": "pass",
        "request": {
            "base_url": "https://export.arxiv.org/api/query",
            "url": "https://export.arxiv.org/api/query?search_query=submittedDate",
            "search_query": build_submitted_date_query(as_of, lookback_days=7),
            "start": 0,
            "max_results": 10,
            "sort_by": "submittedDate",
            "sort_order": "descending",
        },
        "source_policy": {
            "network_fetch_enabled": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "max_results_per_call": 10,
            "polite_min_interval_seconds": 3,
        },
        "seen_source_ids": [],
        "duplicate_source_ids": [],
        "source_items": items,
        "new_items": items,
        "new_item_count": len(items),
        "blocking_reasons": [],
    }


def batches(start: date, count: int = 30) -> dict[str, dict]:
    return {
        (start + timedelta(days=index)).isoformat(): source_batch(start + timedelta(days=index), index + 1)
        for index in range(count)
    }


class Stage1RealReplayTests(unittest.TestCase):
    def test_real_historical_replay_passes_thirty_as_of_dates(self) -> None:
        start = date(2026, 5, 25)
        with tempfile.TemporaryDirectory() as tmp:
            report = build_real_historical_arxiv_replay(
                generated_at=GENERATED_AT,
                start_date=start.isoformat(),
                end_date=(start + timedelta(days=29)).isoformat(),
                source_batches_by_date=batches(start),
                artifact_dir=tmp,
                write=True,
                polite_delay_seconds=0,
            )

            self.assertFalse(validate_real_historical_arxiv_replay_report(report))
            self.assertEqual(report["model_id"], STAGE1_REAL_REPLAY_MODEL_ID)
            self.assertEqual(report["acceptance_id"], STAGE1_REAL_REPLAY_ACCEPTANCE_ID)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["success_count"], 30)
            self.assertEqual(report["unique_as_of_date_count"], 30)
            self.assertEqual(report["unique_selected_source_count"], 30)
            self.assertEqual(report["real_arxiv_source_id_count"], 30)
            self.assertEqual(report["future_leakage_count"], 0)
            self.assertEqual(report["duplicate_lead_count"], 0)
            self.assertEqual(report["queue_continuity_break_count"], 0)
            self.assertEqual(report["unsupported_p0_p1_count"], 0)
            self.assertTrue(report["quality_gates"]["thirty_of_thirty_success"])
            self.assertTrue(report["quality_gates"]["candidate_queue_continuous"])
            self.assertTrue(report["quality_gates"]["email_previews_generated"])
            self.assertEqual(report["artifact_summary"]["file_count"], 7)
            for item in report["artifact_summary"]["files"]:
                self.assertTrue(Path(item["path"]).is_file())

    def test_real_historical_replay_blocks_future_only_candidate(self) -> None:
        start = date(2026, 5, 25)
        payload = batches(start, count=30)
        payload[start.isoformat()] = source_batch(start, 1, future=True)

        report = build_real_historical_arxiv_replay(
            generated_at=GENERATED_AT,
            start_date=start.isoformat(),
            end_date=(start + timedelta(days=29)).isoformat(),
            source_batches_by_date=payload,
            polite_delay_seconds=0,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("no new or queued candidate", " ".join(report["blocking_reasons"]))
        self.assertFalse(report["quality_gates"]["thirty_of_thirty_success"])

    def test_cli_real_historical_replay_rejects_bad_date_range(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "real-historical-arxiv-replay",
                    "--generated-at",
                    GENERATED_AT,
                    "--start-date",
                    "2026-05-25",
                    "--end-date",
                    "2026-05-26",
                    "--count",
                    "30",
                    "--polite-delay-seconds",
                    "0",
                    "--json",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("date range must produce exactly 30 dates", " ".join(payload["blocking_reasons"]))

    def test_real_backfill_workflow_runs_on_cloud_without_production_side_effects(self) -> None:
        workflow = Path(".github/workflows/arxiv-daily-push-real-backfill.yml").read_text(encoding="utf-8")

        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("real-historical-arxiv-replay", workflow)
        self.assertIn("adp-s1p5t03-real-arxiv-30-day-backfill", workflow)
        self.assertIn('ADP_PRODUCTION_ENABLED: "false"', workflow)
        self.assertIn('ADP_SCHEDULED_RUN_ENABLED: "false"', workflow)
        self.assertIn('ADP_ALLOW_SMTP_SEND: "false"', workflow)
        self.assertIn('ADP_ALLOW_RELEASE_UPLOAD: "false"', workflow)
        self.assertNotIn('ADP_PRODUCTION_ENABLED: "true"', workflow)
        self.assertNotIn('ADP_SCHEDULED_RUN_ENABLED: "true"', workflow)
        self.assertNotIn('ADP_ALLOW_SMTP_SEND: "true"', workflow)
        self.assertNotIn('ADP_ALLOW_RELEASE_UPLOAD: "true"', workflow)
        self.assertNotIn("run-scheduled-production", workflow)
        self.assertNotIn("manual-delivery-test", workflow)


if __name__ == "__main__":
    unittest.main()
