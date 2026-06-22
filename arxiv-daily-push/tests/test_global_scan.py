from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.global_scan import (
    ALL_ARXIV_ARCHIVES,
    ALL_ARXIV_SCAN_MODEL_ID,
    build_all_arxiv_daily_input,
    build_all_arxiv_scan_plan,
    build_daily_delivery_package,
    release_links,
    validate_all_arxiv_daily_input_report,
    validate_all_arxiv_scan_plan,
)
from arxiv_daily_push.source_ingest import SOURCE_INGEST_MODEL_ID


GENERATED_AT = "2026-07-01T05:00:00+10:00"


def source_item(source_id: str, title: str, summary: str, primary: str, categories: list[str]) -> dict:
    stable_id = source_id.removeprefix("arxiv:")
    return {
        "source_id": source_id,
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": stable_id,
        "title": title,
        "retrieved_at": GENERATED_AT,
        "canonical_url": f"https://arxiv.org/abs/{stable_id}",
        "metadata": {
            "arxiv": {
                "summary": summary,
                "primary_category": primary,
                "categories": categories,
            }
        },
        "content_refs": [{"ref_type": "abstract", "url": f"https://arxiv.org/abs/{stable_id}"}],
        "license": {"name": "arXiv", "url": "https://arxiv.org/licenses"},
    }


def source_batch(archive_id: str, items: list[dict]) -> dict:
    query = f"cat:{archive_id}"
    status = "pass" if items else "blocked"
    return {
        "ingest_id": "source-ingest:arxiv-latest",
        "model_id": SOURCE_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": "arxiv.atom.v1",
        "generated_at": GENERATED_AT,
        "status": status,
        "request": {
            "base_url": "https://export.arxiv.org/api/query",
            "url": f"https://export.arxiv.org/api/query?search_query={query}",
            "search_query": query,
            "start": 0,
            "max_results": 3,
            "sort_by": "submittedDate",
            "sort_order": "descending",
        },
        "source_policy": {
            "network_fetch_enabled": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "max_results_per_call": 25,
            "polite_min_interval_seconds": 3,
        },
        "seen_source_ids": [],
        "duplicate_source_ids": [],
        "source_items": items,
        "new_items": items,
        "new_item_count": len(items),
        "blocking_reasons": [] if items else ["no unseen arXiv SourceItems returned for the configured query"],
    }


def source_batches(**items_by_archive: list[dict]) -> dict[str, dict]:
    batches = {}
    for archive in ALL_ARXIV_ARCHIVES:
        archive_id = archive["archive_id"]
        batches[archive_id] = source_batch(archive_id, items_by_archive.get(archive_id, []))
    return batches


def high_roi_summary(topic: str) -> str:
    return (
        f"We introduce a framework and benchmark dataset for agent based decision learning in {topic}. "
        "The method covers finance, portfolio risk, market simulation, automation, privacy, security, "
        "supply optimization, cost efficiency, evaluation, statistics, policy, and model robustness. "
        "It is designed for explainable learning value and cross-disciplinary deployment decisions."
    )


class GlobalScanTests(unittest.TestCase):
    def test_plan_covers_all_primary_arxiv_archives_without_cs_ai_default(self) -> None:
        plan = build_all_arxiv_scan_plan(max_results_per_category=3)

        self.assertEqual(plan["model_id"], ALL_ARXIV_SCAN_MODEL_ID)
        self.assertEqual(plan["scope"], "all_arxiv_primary_archives")
        self.assertEqual(plan["archive_count"], 20)
        self.assertGreaterEqual(plan["group_count"], 8)
        self.assertIn("q-fin", {item["archive_id"] for item in plan["archives"]})
        self.assertIn("quant-ph", {item["archive_id"] for item in plan["archives"]})
        self.assertNotEqual({item["query"] for item in plan["archives"]}, {"cat:cs.AI"})
        self.assertFalse(validate_all_arxiv_scan_plan(plan))

    def test_daily_input_selects_highest_roi_and_persists_queue_artifacts(self) -> None:
        finance = source_item(
            "arxiv:2607.00001",
            "Foundation model agents for portfolio risk optimization and market automation",
            high_roi_summary("quantitative finance and trading"),
            "q-fin.PM",
            ["q-fin.PM", "cs.AI", "stat.ML"],
        )
        energy = source_item(
            "arxiv:2607.00002",
            "Efficient control benchmark for energy market simulation",
            high_roi_summary("energy systems and market control"),
            "eess.SY",
            ["eess.SY", "econ.EM"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            report = build_all_arxiv_daily_input(
                date="2026-07-01",
                generated_at=GENERATED_AT,
                source_batches=source_batches(**{"q-fin": [finance], "eess": [energy]}),
                artifact_dir=tmp,
                queue_output_path=Path(tmp) / "queue.json",
            )

            self.assertFalse(validate_all_arxiv_daily_input_report(report))
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["scan"]["archive_count"], 20)
            self.assertEqual(report["scan"]["candidate_count"], 2)
            self.assertEqual(report["daily_input"]["source_item"]["source_id"], "arxiv:2607.00001")
            self.assertEqual(report["selection"]["selected"]["selection_source"], "new_scan")
            self.assertEqual(report["candidate_queue"]["items"][0]["source_id"], "arxiv:2607.00002")
            for path in report["artifact_paths"].values():
                self.assertTrue(Path(path).is_file())

    def test_daily_input_consumes_queue_when_no_new_high_value_candidate_exists(self) -> None:
        queued = source_item(
            "arxiv:2607.00003",
            "Agent benchmark for supply risk and portfolio automation",
            high_roi_summary("supply chain finance"),
            "cs.AI",
            ["cs.AI", "q-fin.RM"],
        )
        first = build_all_arxiv_daily_input(
            date="2026-07-01",
            generated_at=GENERATED_AT,
            source_batches=source_batches(**{"cs": [queued]}),
        )
        queue = first["candidate_queue"]
        queue["items"].append(first["selection"]["selected"])

        second = build_all_arxiv_daily_input(
            date="2026-07-02",
            generated_at="2026-07-02T05:00:00+10:00",
            queue=queue,
            source_batches=source_batches(),
        )

        self.assertEqual(second["status"], "pass")
        self.assertEqual(second["daily_input"]["source_item"]["source_id"], "arxiv:2607.00003")
        self.assertEqual(second["selection"]["selected"]["selection_source"], "candidate_queue")

    def test_delivery_package_requires_release_video_link_and_queue_summary(self) -> None:
        daily_input = {
            "date": "2026-07-01",
            "source_item": {
                "source_id": "arxiv:2607.00001",
                "title": "Foundation model agents for portfolio risk optimization",
                "canonical_url": "https://arxiv.org/abs/2607.00001",
            },
            "selection_audit": {"roi_total_score": 92.5},
            "queue_summary": {
                "queued_item_count": 1,
                "top_queued": [{"title": "Energy market benchmark", "primary_category": "eess.SY", "roi_total_score": 88.0}],
            },
        }
        daily_run_payload = {
            "lesson": {
                "language": "zh-CN",
                "sections": [{"title": "核心解释", "body": "这篇文章适合学习如何把模型能力转换成真实 ROI。"}],
            }
        }
        release_report = {
            "status": "created",
            "repo": "LinzeColin/CodexProject",
            "tag": "adp-daily-20260701",
            "release_ref": "github-release://LinzeColin/CodexProject/adp-daily-20260701",
            "assets": [{"name": "adp-video-artifact.json"}],
        }

        links = release_links(release_report)
        package = build_daily_delivery_package(daily_run_payload, daily_input, release_report, generated_at=GENERATED_AT)

        self.assertIn("/releases/tag/adp-daily-20260701", links["release_url"])
        self.assertIn("/releases/download/adp-daily-20260701/adp-video-artifact.json", links["video_url"])
        self.assertTrue(package["video_link_ready"])
        self.assertTrue(package["email_contains_chinese_lesson"])
        self.assertTrue(package["email_contains_video_link"])
        self.assertTrue(package["email_contains_candidate_queue_summary"])
        self.assertIn("视频观看/下载链接", package["notification"].body)
        self.assertIn("候选队列摘要", package["notification"].body)

    def test_cli_plan_all_arxiv_scan_outputs_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["plan-all-arxiv-scan", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], ALL_ARXIV_SCAN_MODEL_ID)
        self.assertEqual(payload["archive_count"], 20)


if __name__ == "__main__":
    unittest.main()
