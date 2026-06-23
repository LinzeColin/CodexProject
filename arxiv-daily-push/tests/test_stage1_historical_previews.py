from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.stage1_historical_previews import (
    STAGE1_HISTORICAL_PREVIEW_ACCEPTANCE_ID,
    STAGE1_HISTORICAL_PREVIEW_MODEL_ID,
    build_historical_b1_previews,
    build_historical_b1_previews_report,
    validate_historical_b1_previews,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_stage1_b1_report import daily_input_report


def historical_input_rows(count: int = 30) -> list[dict]:
    base = daily_input_report()
    rows: list[dict] = []
    start = date(2026, 5, 1)
    for index in range(count):
        row = copy.deepcopy(base)
        local_date = start + timedelta(days=index)
        ymd = local_date.isoformat()
        stable_id = f"2605.{index + 1:05d}v1"
        source_id = f"arxiv:{stable_id}"
        url = f"https://arxiv.org/abs/{stable_id}"
        summary = f"Historical input fixture {index + 1:02d} validates B1 report evidence."
        daily_input = row["daily_input"]
        daily_input["date"] = ymd
        daily_input["generated_at"] = f"{ymd}T05:00:00+10:00"
        daily_input["run_id"] = f"historical:{ymd}:{stable_id}"
        daily_input["publication_id"] = f"pub:historical:{ymd}:{stable_id}"
        source_item = daily_input["source_item"]
        source_item["source_id"] = source_id
        source_item["stable_id"] = stable_id
        source_item["title"] = f"Historical B1 Input Fixture {index + 1:02d}"
        source_item["canonical_url"] = url
        source_item["retrieved_at"] = f"{ymd}T05:00:00+10:00"
        source_item["content_refs"] = [{"ref_type": "arxiv_atom_summary", "stable_url": url, "section": "summary"}]
        source_item["evidence_refs"] = [url]
        arxiv = source_item["metadata"]["arxiv"]
        arxiv["id"] = stable_id
        arxiv["versioned_id"] = stable_id
        arxiv["published"] = f"{ymd}T00:00:00Z"
        arxiv["updated"] = f"{ymd}T00:00:00Z"
        arxiv["summary"] = summary
        daily_input["claims"][0]["claim_id"] = f"claim:{source_id}:abstract-summary"
        daily_input["claims"][0]["source_id"] = source_id
        daily_input["claims"][0]["statement"] = f"The arXiv Atom summary states: {summary}"
        daily_input["claims"][0]["locator"]["stable_url"] = url
        daily_input["claims"][0]["locator"]["quote"] = summary
        daily_input["claims"][1]["claim_id"] = f"claim:{source_id}:primary-category"
        daily_input["claims"][1]["source_id"] = source_id
        daily_input["claims"][1]["statement"] = "The arXiv Atom metadata lists primary category cs.AI."
        daily_input["claims"][1]["locator"]["stable_url"] = url
        rows.append(row)
    return rows


class Stage1HistoricalPreviewTests(unittest.TestCase):
    def test_build_historical_b1_previews_generates_30_independent_packages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_historical_b1_previews(
                generated_at="2026-06-23T08:00:00+10:00",
                start_date="2026-05-01",
                artifact_dir=tmp,
                write=True,
            )

            self.assertEqual(report["model_id"], STAGE1_HISTORICAL_PREVIEW_MODEL_ID)
            self.assertEqual(report["acceptance_id"], STAGE1_HISTORICAL_PREVIEW_ACCEPTANCE_ID)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["preview_count"], 30)
            self.assertEqual(report["unique_source_id_count"], 30)
            self.assertEqual(report["unique_content_hash_count"], 30)
            self.assertEqual(report["unique_email_id_count"], 30)
            self.assertEqual(report["package_status_counts"], {"pass": 30})
            self.assertEqual(len(report["content_ledger_rows"]), 30)
            self.assertFalse(report["side_effect_policy"]["real_smtp_sent"])
            self.assertFalse(report["side_effect_policy"]["release_uploaded"])
            self.assertFalse(report["side_effect_policy"]["video_generated"])
            self.assertFalse(report["side_effect_policy"]["network_fetch_performed"])
            self.assertFalse(report["side_effect_policy"]["scheduler_enabled"])
            self.assertFalse(validate_historical_b1_previews(report))
            self.assertEqual(report["artifact_summary"]["artifact_files_written"], 150)
            self.assertTrue(Path(report["artifact_summary"]["manifest_path"]).is_file())
            first_email = Path(report["preview_records"][0]["artifact_files"]["email_plain"]["path"]).read_text(
                encoding="utf-8"
            )
            self.assertIn("【先看结论】", first_email)
            self.assertIn("候选队列", first_email)
            self.assertNotIn("ROI", first_email)
            self.assertNotIn(".mp4", first_email)
            self.assertNotIn("delivery_policy", first_email)

    def test_historical_b1_previews_block_when_under_required_count(self) -> None:
        report = build_historical_b1_previews(
            generated_at="2026-06-23T08:00:00+10:00",
            preview_count=29,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("preview_count must be at least 30", report["blocking_reasons"])
        self.assertTrue(report["quality_gates"]["no_real_smtp_send"])
        self.assertFalse(report["side_effect_policy"]["video_generated"])

    def test_cli_historical_b1_previews_writes_manifest_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "historical-b1-previews",
                        "--generated-at",
                        "2026-06-23T08:00:00+10:00",
                        "--artifact-dir",
                        tmp,
                        "--write",
                        "--json",
                    ]
                )

            payload = json.loads(buffer.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["preview_count"], 30)
            self.assertEqual(payload["artifact_summary"]["artifact_files_written"], 150)
            self.assertTrue(Path(payload["artifact_summary"]["manifest_path"]).is_file())

    def test_input_mode_blocks_future_information_leakage(self) -> None:
        rows = historical_input_rows()
        rows[0]["daily_input"]["source_item"]["metadata"]["arxiv"]["published"] = "2026-06-30T00:00:00Z"

        report = build_historical_b1_previews_report(
            rows,
            generated_at="2026-06-23T08:00:00+10:00",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["future_leakage_count"], 1)
        self.assertIn("future leakage detected", " ".join(report["blocking_reasons"]))

    def test_cli_historical_b1_previews_reads_jsonl_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "historical-inputs.jsonl"
            artifact_dir = tmp_path / "artifacts"
            input_path.write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in historical_input_rows()) + "\n",
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "historical-b1-previews",
                        "--input",
                        str(input_path),
                        "--generated-at",
                        "2026-06-23T08:00:00+10:00",
                        "--artifact-dir",
                        str(artifact_dir),
                        "--write",
                        "--json",
                    ]
                )

            payload = json.loads(buffer.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["preview_count"], 30)
            self.assertEqual(payload["future_leakage_count"], 0)
            self.assertTrue(Path(payload["artifact_manifest"]["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
