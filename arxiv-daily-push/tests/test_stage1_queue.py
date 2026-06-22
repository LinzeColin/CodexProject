import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.owner_controls import load_owner_controls
from arxiv_daily_push.stage1_queue import (
    STAGE1_CONTENT_LEDGER_COLUMNS,
    STAGE1_QUEUE_MODEL_ID,
    build_stage1_queue_report,
    score_research_item,
    validate_stage1_queue_report,
)


ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "config" / "owner_controls.yaml"


def _signals(value: float = 1.0) -> dict[str, float]:
    return {
        "relevance": value,
        "novelty": value,
        "evidence_quality": value,
        "technical_breakthrough": value,
        "conversion_economic_value": value,
        "impact_scale": value,
        "timeliness_version_change": value,
        "diversity_coverage": value,
    }


def _item(index: int, **overrides):
    payload = {
        "item_id": f"item-{index:05d}",
        "document_id": f"doc-{index:05d}",
        "event_id": f"event-{index:05d}",
        "theme_cluster_id": "theme-ai",
        "board_id": "B1",
        "source_id": "SRC-ARXIV",
        "title": f"Fixture paper {index}",
        "event_date": "2026-06-22",
        "industry_tags": ["artificial_intelligence"],
        "signals": _signals(0.5),
        "event_delta": 0.5,
        "urgency": 0.5,
        "cross_board_linkage": 0.5,
        "waiting_days": 0,
        "source_balance": 1.0,
        "first_seen_at": "2026-06-22T08:00:00+10:00",
    }
    payload.update(overrides)
    return payload


class Stage1QueueTests(unittest.TestCase):
    def setUp(self):
        self.controls = load_owner_controls(CONTROLS)

    def test_research_score_uses_frozen_weighted_signals(self):
        score = score_research_item(_item(1, signals=_signals(1.0)), self.controls)
        self.assertEqual(score["model_id"], STAGE1_QUEUE_MODEL_ID)
        self.assertEqual(score["score"], 100.0)
        missing = score_research_item(_item(2, signals={"relevance": 1.0}), self.controls)
        self.assertEqual(missing["score"], 22.0)
        self.assertIn("novelty", missing["missing_components"])

    def test_queue_keeps_10000_and_evicts_10001st_deterministically(self):
        items = [_item(index) for index in range(10001)]
        report = build_stage1_queue_report(
            items,
            self.controls,
            as_of_date="2026-06-22",
            generated_at="2026-06-22T21:00:00+10:00",
            run_id="test-10001",
        )
        self.assertEqual(validate_stage1_queue_report(report), [])
        self.assertEqual(report["active_count"], 10000)
        evicted = [row for row in report["content_ledger_rows"] if row["reason_code"] == "EVICTED_CAPACITY"]
        self.assertEqual(len(evicted), 1)
        self.assertEqual(evicted[0]["item_id"], "item-10000")
        last_active = [row for row in report["content_ledger_rows"] if row["current_rank"] == "10000"][0]
        self.assertEqual(last_active["item_id"], "item-09999")

    def test_event_age_365_days_is_inclusive_and_366_is_evicted(self):
        report = build_stage1_queue_report(
            [
                _item(1, event_date="2025-06-22"),
                _item(2, event_date="2025-06-21"),
            ],
            self.controls,
            as_of_date="2026-06-22",
            generated_at="2026-06-22T21:00:00+10:00",
            run_id="test-age",
        )
        by_item = {row["item_id"]: row for row in report["content_ledger_rows"]}
        self.assertEqual(by_item["item-00001"]["queue_state"], "queued")
        self.assertEqual(by_item["item-00002"]["reason_code"], "EVICTED_AGE")

    def test_soft_quota_borrowing_and_source_share_cap(self):
        quota_report = build_stage1_queue_report(
            [_item(index) for index in range(3501)],
            self.controls,
            as_of_date="2026-06-22",
            generated_at="2026-06-22T21:00:00+10:00",
            run_id="test-quota",
        )
        self.assertEqual(quota_report["quota_report"]["B1"]["over_soft_quota"], 1)
        self.assertTrue(quota_report["quota_report"]["B1"]["borrowed_unused_capacity"])

        source_items = [_item(index, source_id="SRC-A") for index in range(9)]
        source_items.extend(_item(100 + index, source_id="SRC-B") for index in range(6))
        source_items.extend(_item(200 + index, source_id="SRC-C") for index in range(6))
        cap_report = build_stage1_queue_report(
            source_items,
            self.controls,
            as_of_date="2026-06-22",
            generated_at="2026-06-22T21:00:00+10:00",
            run_id="test-source-cap",
        )
        active = [row for row in cap_report["content_ledger_rows"] if row["queue_state"] == "queued"]
        src_a = [row for row in active if row["source_id"] == "SRC-A"]
        self.assertLessEqual(len(src_a) / len(active), 0.40)
        self.assertEqual(cap_report["reason_counts"]["EVICTED_SOURCE_CAP"], 1)

    def test_reactivation_retraction_and_superseded_reason_codes(self):
        report = build_stage1_queue_report(
            [
                _item(1, version_event_type="PUBLISHED_AS"),
                _item(2, lifecycle_status="RETRACTED"),
                _item(3, lifecycle_status="SUPERSEDED"),
            ],
            self.controls,
            as_of_date="2026-06-22",
            generated_at="2026-06-22T21:00:00+10:00",
            run_id="test-lifecycle",
        )
        by_item = {row["item_id"]: row for row in report["content_ledger_rows"]}
        self.assertEqual(by_item["item-00001"]["reason_code"], "REACTIVATED_VERSION")
        self.assertEqual(by_item["item-00002"]["reason_code"], "RETRACTED_OR_WITHDRAWN")
        self.assertEqual(by_item["item-00003"]["reason_code"], "SUPERSEDED_OR_REPLACED")

    def test_content_ledger_columns_previous_values_and_csv(self):
        previous = [{"item_id": "item-00001", "current_score": "41", "current_rank": "7"}]
        report = build_stage1_queue_report(
            [_item(1)],
            self.controls,
            as_of_date="2026-06-22",
            generated_at="2026-06-22T21:00:00+10:00",
            run_id="test-ledger",
            previous_entries=previous,
        )
        row = report["content_ledger_rows"][0]
        self.assertEqual(tuple(row.keys()), STAGE1_CONTENT_LEDGER_COLUMNS)
        self.assertEqual(row["previous_score"], "41")
        self.assertEqual(row["previous_rank"], "7")
        csv_rows = list(csv.DictReader(io.StringIO(report["content_ledger_csv"])))
        self.assertEqual(csv_rows[0]["run_id"], "test-ledger")
        self.assertEqual(list(csv_rows[0].keys()), list(STAGE1_CONTENT_LEDGER_COLUMNS))

    def test_stage1_queue_cli_outputs_valid_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "items.json"
            fixture.write_text(json.dumps({"items": [_item(1), _item(2)]}), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "stage1-queue",
                        "--input",
                        str(fixture),
                        "--controls",
                        str(CONTROLS),
                        "--as-of-date",
                        "2026-06-22",
                        "--generated-at",
                        "2026-06-22T21:00:00+10:00",
                        "--run-id",
                        "test-cli",
                        "--json",
                    ]
                )
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["active_count"], 2)


if __name__ == "__main__":
    unittest.main()
