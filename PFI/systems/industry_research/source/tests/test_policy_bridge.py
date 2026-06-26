from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.integrations import policy_system_bridge
from src.reporting.analysis import _policy_support_score


class PolicyBridgeTest(unittest.TestCase):
    def test_failed_refresh_status_is_not_reused_as_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status_dir = Path(tmp)
            status_path = status_dir / "policy_bridge_status_2026-06-04.json"
            status_path.write_text(
                json.dumps({"refresh": {"status": "failed", "reason": "boom", "report_path": ""}}),
                encoding="utf-8",
            )
            with patch.object(policy_system_bridge, "STATUS_DIR", status_dir):
                self.assertEqual(policy_system_bridge._recent_refresh_status("2026-06-04"), {})

    def test_cached_refreshed_status_is_reused_as_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status_dir = Path(tmp)
            status_path = status_dir / "policy_bridge_status_2026-06-04.json"
            status_path.write_text(
                json.dumps({"refresh": {"status": "cached_refreshed", "reason": "prior cache", "report_path": "/tmp/report.md"}}),
                encoding="utf-8",
            )
            with patch.object(policy_system_bridge, "STATUS_DIR", status_dir):
                status = policy_system_bridge._recent_refresh_status("2026-06-04")

        self.assertEqual(status["status"], "cached_refreshed")
        self.assertIn("using policy bridge cache", status["reason"])

    def test_refresh_disabled_does_not_downgrade_recent_confirmed_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status_dir = Path(tmp)
            status_path = status_dir / "policy_bridge_status_2026-06-04.json"
            status_path.write_text(
                json.dumps({"refresh": {"status": "cached_refreshed", "reason": "prior cache", "report_path": "/tmp/report.md"}}),
                encoding="utf-8",
            )
            with patch.object(policy_system_bridge, "STATUS_DIR", status_dir), patch.dict(
                "os.environ", {"AI_RESEARCH_POLICY_REFRESH": "0"}, clear=False
            ):
                status = policy_system_bridge._refresh_policy_system_if_enabled("2026-06-04")

        self.assertEqual(status["status"], "cached_refreshed")
        self.assertIn("using policy bridge cache", status["reason"])

    def test_unfresh_policy_bridge_status_cannot_add_policy_support_score(self) -> None:
        item = {"symbol": "SH.600000", "name": "测试银行", "research_group": "银行"}
        events = [
            {
                "type": "government_policy_bridge",
                "related_symbols": "SH.600000",
                "industry": "银行",
                "title": "政策系统解析：测试政策",
                "summary": "匹配对象：测试银行",
                "impact": "positive",
                "policy_importance_score": "96",
                "policy_bridge_status": "cached_failed",
            }
        ]
        self.assertEqual(_policy_support_score(item, events), 0)

    def test_policy_support_score_requires_original_source_url(self) -> None:
        item = {"symbol": "SH.600000", "name": "测试银行", "research_group": "银行"}
        event = {
            "type": "government_policy_bridge",
            "related_symbols": "SH.600000",
            "industry": "银行",
            "title": "政策系统解析：测试政策",
            "summary": "匹配对象：测试银行",
            "impact": "positive",
            "policy_importance_score": "96",
            "policy_bridge_status": "refreshed",
        }
        self.assertEqual(_policy_support_score(item, [event]), 0)
        self.assertGreater(
            _policy_support_score(item, [{**event, "source_url": "https://www.gov.cn/test-policy.html"}]),
            0,
        )

    def test_refresh_passes_ai_research_request_file_to_policy_pipeline(self) -> None:
        captured_env = {}
        captured_timeout = {}

        class FakeProcess:
            returncode = 0
            pid = 123456

            def communicate(self, timeout=None):
                captured_timeout["timeout"] = timeout
                return ("ok", None)

        def fake_popen(*args, **kwargs):
            captured_env.update(kwargs.get("env") or {})
            return FakeProcess()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "scripts" / "run_policy_report.sh"
            script.parent.mkdir(parents=True)
            script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            request = root / "request.json"
            request.write_text("{}", encoding="utf-8")
            with patch.object(policy_system_bridge, "DEFAULT_POLICY_ROOT", root), patch.object(
                policy_system_bridge, "STATUS_DIR", root / "status"
            ), patch("src.integrations.policy_system_bridge.subprocess.Popen", fake_popen), patch(
                "src.integrations.policy_system_bridge._latest_policy_report_path", return_value="/tmp/report.pdf"
            ), patch.dict("os.environ", {"AI_RESEARCH_POLICY_REFRESH": "1"}, clear=False):
                status = policy_system_bridge._refresh_policy_system_if_enabled("2026-06-04", request)

        self.assertEqual(status["status"], "refreshed")
        self.assertEqual(captured_env["AI_RESEARCH_POLICY_REQUEST_FILE"], str(request))
        self.assertEqual(captured_env["FETCH_INTERPRETATION_RESULTS"], "1")
        self.assertEqual(captured_env["FETCH_SEARCH_RESULT_PAGES"], "1")
        self.assertEqual(captured_timeout["timeout"], 240)

    def test_refresh_uses_recent_policy_report_cache_before_launching_pipeline(self) -> None:
        def fail_popen(*args, **kwargs):
            raise AssertionError("policy pipeline should not launch when recent verified cache exists")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "scripts" / "run_policy_report.sh"
            report = root / "reports" / "policy_report.md"
            db = root / "data" / "policy_documents.sqlite"
            script.parent.mkdir(parents=True)
            report.parent.mkdir(parents=True)
            db.parent.mkdir(parents=True)
            script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            report.write_text("verified policy cache", encoding="utf-8")
            db.write_bytes(b"sqlite-cache")
            request = root / "request.json"
            request.write_text("{}", encoding="utf-8")
            with patch.object(policy_system_bridge, "DEFAULT_POLICY_ROOT", root), patch.object(
                policy_system_bridge, "STATUS_DIR", root / "status"
            ), patch("src.integrations.policy_system_bridge.subprocess.Popen", fail_popen), patch.dict(
                "os.environ", {"AI_RESEARCH_POLICY_REFRESH": "1"}, clear=False
            ):
                status = policy_system_bridge._refresh_policy_system_if_enabled("2026-06-04", request)

        self.assertEqual(status["status"], "cached_refreshed")
        self.assertEqual(status["report_path"], str(report))
        self.assertIn("recent policy system report", status["reason"])

    def test_refresh_timeout_still_fails_without_recent_policy_report_cache(self) -> None:
        class TimeoutProcess:
            returncode = None
            pid = 123456

            def communicate(self, timeout=None):
                raise subprocess.TimeoutExpired(cmd="policy", timeout=timeout)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "scripts" / "run_policy_report.sh"
            db = root / "data" / "policy_documents.sqlite"
            script.parent.mkdir(parents=True)
            db.parent.mkdir(parents=True)
            script.write_text("#!/usr/bin/env bash\nsleep 999\n", encoding="utf-8")
            db.write_bytes(b"sqlite-cache")
            request = root / "request.json"
            request.write_text("{}", encoding="utf-8")
            with patch.object(policy_system_bridge, "DEFAULT_POLICY_ROOT", root), patch.object(
                policy_system_bridge, "STATUS_DIR", root / "status"
            ), patch("src.integrations.policy_system_bridge.subprocess.Popen", return_value=TimeoutProcess()), patch(
                "src.integrations.policy_system_bridge._terminate_process_group"
            ), patch.dict("os.environ", {"AI_RESEARCH_POLICY_REFRESH": "1", "AI_RESEARCH_POLICY_TIMEOUT_SECONDS": "1"}, clear=False):
                status = policy_system_bridge._refresh_policy_system_if_enabled("2026-06-04", request)

        self.assertEqual(status["status"], "timeout")

    def test_policy_request_requires_separate_original_source_crawl(self) -> None:
        factors = [
            {
                "symbol": "512620",
                "name": "农业ETF天弘",
                "exchange": "SSE",
                "asset_class": "ETF",
                "research_group": "农业/周期",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(policy_system_bridge, "REQUEST_DIR", Path(tmp)):
                path = policy_system_bridge._write_policy_request("2026-06-04", factors)
                payload = json.loads(path.read_text(encoding="utf-8"))
        task = payload["crawler_task"]
        self.assertEqual(task["mode"], "separate_policy_catalyst_crawl")
        self.assertTrue(task["must_verify_original_text"])
        self.assertTrue(task["must_flag_misread_risk"])
        self.assertTrue(task["must_link_operation_impact"])
        self.assertIn("不能提高买入分", task["fallback_rule"])
        self.assertIn("原文抓取状态", payload["required_output"])
        self.assertIn("公告/新闻原文来源", payload["required_output"])
        self.assertIn("独立爬虫任务报告路径", payload["required_output"])

    def test_generic_information_disclosure_document_does_not_match_robot_theme(self) -> None:
        factors = [{"symbol": "300024", "name": "机器人", "exchange": "SZSE", "research_group": "机器人"}]
        theme_index = policy_system_bridge._theme_index(factors)
        keywords = policy_system_bridge._keywords_for_themes(theme_index)
        row = {
            "title": "国务院办公厅关于印发《政府信息公开信息处理费管理办法》的通知",
            "primary_industry": "政务公开",
            "industry_bucket": "政府信息公开",
            "chinese_summary": "对待研判行业相关企业，文件可能影响合规要求。",
            "policy_points_json": "[]",
            "business_impacts_json": "[]",
        }

        self.assertEqual(policy_system_bridge._matched_theme(row, theme_index, keywords), {})

    def test_hard_theme_policy_document_matches_relevant_theme(self) -> None:
        factors = [{"symbol": "512620", "name": "农业ETF天弘", "exchange": "SSE", "research_group": "农业/周期"}]
        theme_index = policy_system_bridge._theme_index(factors)
        keywords = policy_system_bridge._keywords_for_themes(theme_index)
        row = {
            "title": "两部门负责人就《加快农业农村现代化十五五规划》答记者问",
            "primary_industry": "农业农村",
            "industry_bucket": "农业",
            "chinese_summary": "农业农村现代化政策细则。",
            "policy_points_json": "[\"加快农业农村现代化\"]",
            "business_impacts_json": "[\"影响农业产业链\"]",
        }

        matched = policy_system_bridge._matched_theme(row, theme_index, keywords)

        self.assertEqual(matched["theme"], "农业/周期")
        self.assertIn("农业", matched["basis"])

    def test_outdated_macro_plan_is_low_value_after_its_window(self) -> None:
        row = {
            "title": "中华人民共和国国民经济和社会发展第十四个五年规划和2035年远景目标纲要",
        }

        self.assertTrue(policy_system_bridge._is_low_value_policy_document(row, "2026-06-04"))

    def test_outdated_macro_plan_short_name_is_low_value_after_its_window(self) -> None:
        row = {
            "title": "国务院办公厅关于印发“十四五”现代物流发展规划的通知",
        }

        self.assertTrue(policy_system_bridge._is_low_value_policy_document(row, "2026-06-04"))

    def test_current_macro_plan_is_not_filtered_as_low_value(self) -> None:
        row = {
            "title": "中华人民共和国国民经济和社会发展第十五个五年规划纲要",
        }

        self.assertFalse(policy_system_bridge._is_low_value_policy_document(row, "2026-06-04"))


if __name__ == "__main__":
    unittest.main()
