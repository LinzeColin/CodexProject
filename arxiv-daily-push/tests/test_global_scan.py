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
    build_live_all_arxiv_dry_run,
    build_all_arxiv_scan_plan,
    build_daily_delivery_package,
    release_links,
    validate_all_arxiv_daily_input_report,
    validate_live_all_arxiv_dry_run_report,
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


def atom_feed(source_id: str = "2607.00042") -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
  <id>https://export.arxiv.org/api/query</id>
  <updated>2026-07-01T05:00:00+10:00</updated>
  <entry>
    <id>http://arxiv.org/abs/{source_id}v1</id>
    <published>2026-07-01T00:00:00Z</published>
    <updated>2026-07-01T00:00:00Z</updated>
    <title>Agent benchmark for portfolio risk automation</title>
    <summary>{high_roi_summary("portfolio risk automation")}</summary>
    <author><name>Ada Example</name></author>
    <arxiv:primary_category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="q-fin.PM" scheme="http://arxiv.org/schemas/atom"/>
    <link href="http://arxiv.org/abs/{source_id}v1" rel="alternate" type="text/html"/>
  </entry>
</feed>
"""


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
        queries = {item["archive_id"]: item["query"] for item in plan["archives"]}
        self.assertIn("cat:q-fin.PM", queries["q-fin"])
        self.assertIn("cat:stat.ML", queries["stat"])
        self.assertIn("cat:nlin.CD", queries["nlin"])
        self.assertIn("cat:physics.optics", queries["physics"])
        self.assertIn("cat:cs.AI", queries["cs"])
        self.assertIn("cat:econ.EM", queries["econ"])
        self.assertIn("cat:eess.SY", queries["eess"])
        self.assertIn("cat:math.AG", queries["math"])
        self.assertNotEqual(queries["cs"], "cat:cs")
        self.assertNotEqual(queries["econ"], "cat:econ")
        self.assertNotEqual(queries["eess"], "cat:eess")
        self.assertNotEqual(queries["math"], "cat:math")
        self.assertNotEqual(queries["q-fin"], "cat:q-fin")
        self.assertNotEqual(queries["stat"], "cat:stat")
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

    def test_daily_input_reports_scan_blockers_before_roi_selection(self) -> None:
        batches = source_batches()
        batches["cs"]["blocking_reasons"] = ["arXiv ingest failed: TLS certificate failure"]

        report = build_all_arxiv_daily_input(
            date="2026-07-01",
            generated_at=GENERATED_AT,
            source_batches=batches,
        )

        self.assertFalse(validate_all_arxiv_daily_input_report(report))
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["daily_input_ready"])
        self.assertEqual(report["scan"]["status"], "blocked")
        self.assertIn("all-arxiv scan blocked: cs: arXiv ingest failed", report["blocking_reasons"][0])
        self.assertNotIn("minimum ROI selection threshold", " ".join(report["blocking_reasons"]))

    def test_daily_input_retries_transient_arxiv_errors(self) -> None:
        attempts = {"count": 0}

        def flaky_fetcher(_query):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("HTTP Error 429: Too Many Requests")
            return atom_feed()

        report = build_all_arxiv_daily_input(
            date="2026-07-01",
            generated_at=GENERATED_AT,
            max_results_per_category=1,
            fetcher=flaky_fetcher,
            transient_retry_count=1,
            transient_retry_delay_seconds=0,
        )

        self.assertFalse(validate_all_arxiv_daily_input_report(report))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["scan"]["category_reports"][0]["retry_attempts"], 1)
        self.assertGreaterEqual(attempts["count"], 21)

    def test_live_dry_run_retries_transient_arxiv_rate_limit(self) -> None:
        attempts = {"count": 0}

        def flaky_fetcher(_query):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("HTTP Error 429: Unknown Error")
            return atom_feed()

        report = build_live_all_arxiv_dry_run(
            generated_at=GENERATED_AT,
            date="2026-07-01",
            max_results_per_category=1,
            fetcher=flaky_fetcher,
            transient_retry_count=1,
            transient_retry_delay_seconds=0,
        )

        self.assertFalse(validate_live_all_arxiv_dry_run_report(report))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["verified_archive_count"], 20)
        self.assertEqual(report["failed_archive_count"], 0)
        self.assertEqual(report["scan"]["category_reports"][0]["retry_attempts"], 1)
        self.assertGreaterEqual(attempts["count"], 21)

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

    def test_delivery_package_requires_stage1_text_and_queue_summary(self) -> None:
        daily_input = {
            "date": "2026-07-01",
            "source_item": {
                "source_id": "arxiv:2607.00001",
                "title": "Foundation model agents for portfolio risk optimization",
                "canonical_url": "https://arxiv.org/abs/2607.00001",
                "metadata": {"arxiv": {"primary_category": "cs.AI", "summary": "A concise abstract."}},
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
                "frontstage": {
                    "decision": "读",
                    "evidence_level": "摘要级预印本",
                    "estimated_reading_time": "8-15分钟",
                    "one_line_takeaway": "这篇文章适合学习如何把模型能力转换成真实 ROI score。",
                    "first_principles_chain": ["问题定义", "ROI评分", "可观察输出", "失败条件"],
                    "domain_mappings": [{"paper_variable": "ROI score", "decision_mapping": "不要把 Release 资料包当阅读入口"}],
                    "key_questions": ["这是不是可复验判断，而不是 delivery policy？"],
                    "evidence_gaps": ["不要把 GitHub Release 或 12秒视频当作正文重点。"],
                    "default_action": "把 ROI 转成一个最小验证问题，不展示 roi_total_score。",
                },
                "sections": [{"title": "核心解释", "body": "这篇文章适合学习如何把模型能力转换成真实 ROI。"}],
            }
        }
        release_report = {
            "status": "created",
            "repo": "LinzeColin/CodexProject",
            "tag": "adp-daily-20260701",
            "release_ref": "github-release://LinzeColin/CodexProject/adp-daily-20260701",
            "assets": [{"name": "adp-daily-video.mp4"}],
        }

        links = release_links(release_report)
        package = build_daily_delivery_package(daily_run_payload, daily_input, release_report, generated_at=GENERATED_AT)

        self.assertIn("/releases/download/adp-daily-20260701/adp-daily-video.mp4", links["video_url"])
        self.assertFalse(package["video_link_ready"])
        self.assertFalse(package["video_required"])
        self.assertFalse(package["video_generation_required"])
        self.assertFalse(package["release_required"])
        self.assertTrue(package["email_contains_chinese_lesson"])
        self.assertFalse(package["email_contains_video_link"])
        self.assertTrue(package["email_contains_candidate_queue_summary"])
        self.assertTrue(package["email_contains_html"])
        self.assertEqual(
            package["notification"].subject,
            "20260701 -- arXiv Computer Science -- Computer Science -- Foundation model agents for portfolio risk optimization",
        )
        combined_body = package["notification"].body + package["notification"].html_body
        self.assertIn("【今天讲透一个问题】", package["notification"].body)
        self.assertIn("【为什么值得你看】", package["notification"].body)
        self.assertIn("【怎么转成可用判断】", package["notification"].body)
        self.assertIn("候选队列摘要", package["notification"].body)
        self.assertIn("已入队候选", package["notification"].body)
        self.assertNotIn("【视频入口】", package["notification"].body)
        self.assertNotIn("观看/下载", combined_body)
        self.assertNotIn("Release 资料包", combined_body)
        self.assertNotIn(links["release_url"], package["notification"].body)
        self.assertNotIn("GitHub Release", combined_body)
        self.assertNotIn("12秒视频", combined_body)
        self.assertNotIn("delivery policy", combined_body)
        self.assertNotIn("ROI score", combined_body)
        self.assertNotIn("ROI评分", combined_body)
        self.assertNotIn("roi_total_score", combined_body)
        self.assertNotIn("后台", combined_body)
        self.assertNotIn("日报", combined_body)
        self.assertNotIn("class=\"score\"", package["notification"].html_body)
        self.assertLessEqual(len(package["notification"].body), 1500)
        self.assertNotRegex(package["notification"].subject, r"\d(?:\.\d)?/5")

    def test_quant_finance_email_filters_frontstage_candidate_pollution(self) -> None:
        daily_input = {
            "date": "2026-07-01",
            "source_item": {
                "source_id": "arxiv:2607.00009",
                "title": "Optimal order in multi-agent systems and market fragility",
                "canonical_url": "https://arxiv.org/abs/2607.00009",
                "metadata": {
                    "arxiv": {
                        "primary_category": "q-fin.RM",
                        "summary": "A theory paper about agent power, response functions, order, fragility, and market risk.",
                    }
                },
            },
            "queue_summary": {
                "queued_item_count": 3,
                "top_queued": [
                    {"title": "Quantum algorithm for molecular light", "primary_category": "quant-ph", "roi_total_score": 91.0},
                    {"title": "West Nile virus and quantum life game", "primary_category": "q-bio.PE", "roi_total_score": 90.0},
                    {"title": "Market risk simulation benchmark for agent trading", "primary_category": "cs.AI", "roi_total_score": 89.0},
                ],
            },
        }
        daily_run_payload = {"lesson": {"language": "zh-CN", "sections": [{"title": "核心解释", "body": "中文讲解。"}]}}
        release_report = {
            "status": "created",
            "repo": "LinzeColin/CodexProject",
            "tag": "adp-daily-20260701",
            "release_ref": "github-release://LinzeColin/CodexProject/adp-daily-20260701",
            "assets": [{"name": "adp-daily-video.mp4"}],
        }

        package = build_daily_delivery_package(daily_run_payload, daily_input, release_report, generated_at=GENERATED_AT)

        self.assertEqual(
            package["notification"].subject,
            "20260701 -- arXiv Quantitative Finance -- Quant Finance -- Optimal order in multi-agent systems and market fragility",
        )
        self.assertNotIn("Quantum algorithm for molecular light", package["notification"].body)
        self.assertNotIn("West Nile virus", package["notification"].body)
        self.assertIn("Market risk simulation benchmark", package["notification"].body)
        self.assertIn("跨域候选", package["notification"].body)

    def test_release_video_link_requires_mp4_not_manifest(self) -> None:
        release_report = {
            "status": "created",
            "repo": "LinzeColin/CodexProject",
            "tag": "adp-daily-20260701",
            "release_ref": "github-release://LinzeColin/CodexProject/adp-daily-20260701",
            "assets": [{"name": "adp-video-artifact.json"}],
        }

        links = release_links(release_report)

        self.assertEqual(links["video_url"], "")

    def test_cli_plan_all_arxiv_scan_outputs_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["plan-all-arxiv-scan", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], ALL_ARXIV_SCAN_MODEL_ID)
        self.assertEqual(payload["archive_count"], 20)

    def test_live_all_arxiv_dry_run_requires_all_twenty_archive_buckets(self) -> None:
        items_by_archive = {}
        for index, archive in enumerate(ALL_ARXIV_ARCHIVES, start=1):
            archive_id = archive["archive_id"]
            items_by_archive[archive_id] = [
                source_item(
                    f"arxiv:2607.{index:05d}",
                    f"Live fetch validation for {archive_id}",
                    high_roi_summary(f"{archive_id} live fetch validation"),
                    f"{archive_id}.LG",
                    [archive_id],
                )
            ]

        report = build_live_all_arxiv_dry_run(
            generated_at=GENERATED_AT,
            source_batches=source_batches(**items_by_archive),
        )

        self.assertFalse(validate_live_all_arxiv_dry_run_report(report))
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["live_dry_run_ready"])
        self.assertEqual(report["archive_count"], 20)
        self.assertEqual(report["verified_archive_count"], 20)
        self.assertEqual(report["failed_archive_count"], 0)
        self.assertTrue(report["sample_daily_input"]["source_item"]["source_id"].startswith("arxiv:"))
        self.assertEqual(report["sample_daily_input"]["date"], "2026-07-01")
        self.assertFalse(report["production_schedule_enabled"])
        self.assertFalse(report["smtp_send_enabled"])
        self.assertFalse(report["release_upload_enabled"])

    def test_live_all_arxiv_dry_run_blocks_if_any_archive_bucket_fails(self) -> None:
        report = build_live_all_arxiv_dry_run(
            generated_at=GENERATED_AT,
            source_batches=source_batches(),
        )

        self.assertFalse(validate_live_all_arxiv_dry_run_report(report))
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["live_dry_run_ready"])
        self.assertEqual(report["archive_count"], 20)
        self.assertEqual(report["verified_archive_count"], 0)
        self.assertEqual(report["failed_archive_count"], 20)


if __name__ == "__main__":
    unittest.main()
