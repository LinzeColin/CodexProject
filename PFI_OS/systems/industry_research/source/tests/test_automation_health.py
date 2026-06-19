from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.accounting.alipay_ledger import UpdateSummary
from src.monitoring.automation_health import _automation_prompt_check, _policy_bridge_check, _snapshot_check, build_automation_health, format_automation_health, write_automation_health_log
from src.monitoring.automation_health import _alipay_check, _moomoo_checks, _week_status_check


class AutomationHealthTest(unittest.TestCase):
    def test_automation_prompt_check_passes_current_required_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt = "Volume依据; fixed 8% style sizing; Translate internal PFIOS labels to Chinese; No internal local paths in PDF body; local request/report paths; Do not backfill or regenerate reports dated before TODAY"
            for automation_id in ["ai", "ai-1", "ai-2", "ai-3", "ai-4", "ai-4k"]:
                self._write_automation(root, automation_id, prompt)

            check = _automation_prompt_check(root)

        self.assertEqual(check["status"], "pass")
        self.assertEqual(check["details"]["missing"], [])
        self.assertEqual(check["details"]["issues"], [])

    def test_automation_prompt_check_rejects_stale_prompt_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_prompt = "Volume依据; fixed 8% style sizing; Translate internal PFIOS labels to Chinese; No internal local paths in PDF body; local request/report paths; Do not backfill or regenerate reports dated before TODAY"
            for automation_id in ["ai", "ai-2", "ai-3", "ai-4", "ai-4k"]:
                self._write_automation(root, automation_id, current_prompt)
            self._write_automation(root, "ai-1", "separate crawler request path; Do not backfill or regenerate reports dated before TODAY")

            check = _automation_prompt_check(root)

        self.assertEqual(check["status"], "fail")
        self.assertIn("missing_prompt_term:ai-1:Volume依据", check["details"]["issues"])
        self.assertIn("forbidden_prompt_term:ai-1:separate crawler request path", check["details"]["issues"])

    def test_snapshot_check_warns_for_fallback_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_sample_inputs(root)
            with patch("src.monitoring.automation_health.ROOT", root):
                check = _snapshot_check("2026-06-04", strict_opend=False, min_opend_coverage=0.0)
        self.assertEqual(check["status"], "warn")
        self.assertEqual(check["details"]["source_counts"]["Moomoo OpenD"], 1)
        self.assertEqual(check["details"]["source_counts"]["Yahoo Finance (US)"], 1)
        self.assertEqual(check["details"]["opend_diagnostic_counts"]["ok"], 1)
        self.assertEqual(check["details"]["opend_diagnostic_counts"]["quote_permission"], 1)
        self.assertEqual(check["details"]["opend_permission_symbols"], ["512620"])
        self.assertEqual(check["details"]["fallback_symbols"], ["512620"])

    def test_snapshot_check_fails_in_strict_opend_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_sample_inputs(root)
            with patch("src.monitoring.automation_health.ROOT", root):
                check = _snapshot_check("2026-06-04", strict_opend=True, min_opend_coverage=0.0)
        self.assertEqual(check["status"], "fail")
        self.assertIn("strict_opend", str(check["details"]))

    def test_snapshot_check_preflight_warns_for_stale_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_sample_inputs(root)
            with patch("src.monitoring.automation_health.ROOT", root):
                strict_check = _snapshot_check("2026-06-05", strict_opend=False, min_opend_coverage=0.0)
                preflight_check = _snapshot_check("2026-06-05", strict_opend=False, min_opend_coverage=0.0, preflight=True)

        self.assertEqual(strict_check["status"], "fail")
        self.assertIn("stale_snapshot", strict_check["details"]["issues"])
        self.assertEqual(preflight_check["status"], "warn")
        self.assertTrue(preflight_check["details"]["preflight"])

    def test_weekend_without_due_reports_does_not_fail_on_stale_snapshot(self) -> None:
        week = self._check("week_report_status", "pass")
        week["details"] = {"due_bad": []}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_sample_inputs(root)
            with patch("src.monitoring.automation_health.ROOT", root), \
                patch("src.monitoring.automation_health._runtime_checks", return_value=[self._check("runtime_dependencies", "pass")]), \
                patch("src.monitoring.automation_health._automation_prompt_check", return_value=self._check("automation_prompt_sync", "pass")), \
                patch("src.monitoring.automation_health._moomoo_checks", return_value=[self._check("opend_port", "pass")]), \
                patch("src.monitoring.automation_health._alipay_check", return_value=self._check("alipay_update", "pass")), \
                patch("src.monitoring.automation_health._policy_bridge_check", return_value=self._check("policy_bridge", "pass")), \
                patch("src.monitoring.automation_health._week_status_check", return_value=week), \
                patch("src.monitoring.automation_health._current_day_report_artifact_exists", return_value=False):
                payload = build_automation_health("2026-06-05", run_quality=False)

        snapshot = next(check for check in payload["checks"] if check["name"] == "quote_snapshot")
        self.assertEqual(snapshot["status"], "warn")
        self.assertEqual(payload["status"], "warn")
        self.assertFalse(snapshot["details"]["require_actionable_snapshot"])
        self.assertIn("stale_snapshot", snapshot["details"]["issues"])

    def test_overall_health_promotes_warn_without_failures(self) -> None:
        with patch("src.monitoring.automation_health._runtime_checks", return_value=[self._check("runtime_dependencies", "pass")]), \
            patch("src.monitoring.automation_health._automation_prompt_check", return_value=self._check("automation_prompt_sync", "pass")), \
            patch("src.monitoring.automation_health._moomoo_checks", return_value=[self._check("opend_port", "pass")]), \
            patch("src.monitoring.automation_health._snapshot_check", return_value=self._check("quote_snapshot", "warn")), \
            patch("src.monitoring.automation_health._alipay_check", return_value=self._check("alipay_update", "warn")), \
            patch("src.monitoring.automation_health._policy_bridge_check", return_value=self._check("policy_bridge", "pass")), \
            patch("src.monitoring.automation_health._week_status_check", return_value=self._check("week_report_status", "pass")):
            payload = build_automation_health("2026-06-04", run_quality=False)
        self.assertEqual(payload["status"], "warn")
        rendered = format_automation_health(payload)
        self.assertIn("AUTOMATION_HEALTH: 2026-06-04 status=warn", rendered)
        self.assertIn("WARN: quote_snapshot", rendered)
        self.assertIn("WARN: trade_execution_readiness", rendered)

    def test_trade_execution_readiness_warns_for_report_but_not_execution(self) -> None:
        alipay = self._check("alipay_update", "warn")
        alipay["details"] = {
            "execution_blocked": True,
            "missing_count": 0,
            "execution_status": "needs_confirmation",
            "block_reason": "OCR candidate requires confirmation",
        }
        snapshot = self._check("quote_snapshot", "warn")
        snapshot["details"] = {"opend_coverage": 0.25, "source_counts": {"Moomoo OpenD": 1, "Yahoo Finance": 3}}
        week = self._check("week_report_status", "pass")
        week["details"] = {"due_bad": []}

        with patch("src.monitoring.automation_health._runtime_checks", return_value=[self._check("runtime_dependencies", "pass")]), \
            patch("src.monitoring.automation_health._automation_prompt_check", return_value=self._check("automation_prompt_sync", "pass")), \
            patch("src.monitoring.automation_health._moomoo_checks", return_value=[self._check("opend_port", "pass")]), \
            patch("src.monitoring.automation_health._snapshot_check", return_value=snapshot), \
            patch("src.monitoring.automation_health._alipay_check", return_value=alipay), \
            patch("src.monitoring.automation_health._policy_bridge_check", return_value=self._check("policy_bridge", "pass")), \
            patch("src.monitoring.automation_health._week_status_check", return_value=week):
            payload = build_automation_health("2026-06-04", run_quality=False)

        readiness = next(check for check in payload["checks"] if check["name"] == "trade_execution_readiness")
        self.assertEqual(payload["status"], "warn")
        self.assertEqual(readiness["status"], "warn")
        self.assertFalse(readiness["details"]["execution_ready"])
        self.assertIn("alipay_execution_blocked", readiness["details"]["blockers"])

    def test_trade_execution_readiness_can_be_required_as_failure(self) -> None:
        alipay = self._check("alipay_update", "warn")
        alipay["details"] = {
            "execution_blocked": True,
            "missing_count": 0,
            "execution_status": "needs_confirmation",
            "block_reason": "OCR candidate requires confirmation",
        }
        snapshot = self._check("quote_snapshot", "pass")
        snapshot["details"] = {"opend_coverage": 1.0, "source_counts": {"Moomoo OpenD": 4}}
        week = self._check("week_report_status", "pass")
        week["details"] = {"due_bad": []}

        with patch("src.monitoring.automation_health._runtime_checks", return_value=[self._check("runtime_dependencies", "pass")]), \
            patch("src.monitoring.automation_health._automation_prompt_check", return_value=self._check("automation_prompt_sync", "pass")), \
            patch("src.monitoring.automation_health._moomoo_checks", return_value=[self._check("opend_port", "pass")]), \
            patch("src.monitoring.automation_health._snapshot_check", return_value=snapshot), \
            patch("src.monitoring.automation_health._alipay_check", return_value=alipay), \
            patch("src.monitoring.automation_health._policy_bridge_check", return_value=self._check("policy_bridge", "pass")), \
            patch("src.monitoring.automation_health._week_status_check", return_value=week):
            payload = build_automation_health("2026-06-04", run_quality=False, require_execution_ready=True)

        readiness = next(check for check in payload["checks"] if check["name"] == "trade_execution_readiness")
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(readiness["status"], "fail")
        self.assertFalse(readiness["details"]["execution_ready"])

    def test_execution_ready_required_uses_separate_health_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("src.monitoring.automation_health.ROOT", root):
                normal_path = write_automation_health_log(
                    {"date": "2026-06-04", "status": "warn", "require_execution_ready": False, "checks": []}
                )
                strict_path = write_automation_health_log(
                    {"date": "2026-06-04", "status": "fail", "require_execution_ready": True, "checks": []}
                )

        self.assertEqual(normal_path.name, "automation_health_2026-06-04.json")
        self.assertEqual(strict_path.name, "automation_health_2026-06-04_execution_ready_required.json")

    def test_moomoo_opend_port_warns_in_preflight_but_fails_strict(self) -> None:
        class FakeAppPath:
            def exists(self) -> bool:
                return True

            def __str__(self) -> str:
                return "/Applications/moomoo.app"

        with patch("src.monitoring.automation_health.MOOMOO_APP_PATH", FakeAppPath()), \
            patch("src.monitoring.automation_health._load_opend_config", return_value={"opend": {"host": "127.0.0.1", "port": 11111}}), \
            patch("src.monitoring.automation_health._port_open", return_value=False), \
            patch("src.monitoring.automation_health._find_watchlist_db", return_value=Path("/tmp/WatchlistGroup.db")), \
            patch("src.monitoring.automation_health._read_watchlist_rows", return_value=[{"symbol": "TEST"}]):
            preflight = _moomoo_checks(preflight=True)
            strict = _moomoo_checks(preflight=False)

        self.assertEqual(next(row for row in preflight if row["name"] == "opend_port")["status"], "warn")
        self.assertEqual(next(row for row in strict if row["name"] == "opend_port")["status"], "fail")

    def test_week_status_missing_today_warns_in_preflight_but_fails_strict(self) -> None:
        payload = {
            "week_folder": "/tmp/week",
            "status_counts": {"missing": 1},
            "folder_issues": [],
            "reports": [
                {
                    "report_date": "2026-06-05",
                    "report_kind": "pre_open",
                    "status": "missing",
                    "pdf_name": "1. 05062026_盘前报告.pdf",
                    "issues": ["Missing PDF"],
                }
            ],
        }
        with patch("src.monitoring.automation_health.week_report_status", return_value=payload):
            preflight = _week_status_check("2026-06-05", run_quality=False, preflight=True)
            strict = _week_status_check("2026-06-05", run_quality=False, preflight=False)

        self.assertEqual(preflight["status"], "warn")
        self.assertTrue(preflight["details"]["preflight"])
        self.assertEqual(strict["status"], "fail")

    def test_alipay_check_warns_when_update_needs_confirmation(self) -> None:
        summary = UpdateSummary(
            start_date="2026-06-04",
            end_date="2026-06-04",
            updated_dates=["2026-06-04"],
            missing_dates=[],
            log_rows=[
                {
                    "date": "2026-06-04",
                    "updated_at": "2026-06-04T22:58:32+10:00",
                    "status": "needs_confirmation",
                    "source_type": "video",
                    "source_path": "/tmp/alipay.mp4",
                }
            ],
        )
        with patch("src.monitoring.automation_health.summarize_updates", return_value=summary):
            check = _alipay_check("2026-06-04")

        self.assertEqual(check["status"], "warn")
        self.assertTrue(check["details"]["execution_blocked"])
        self.assertEqual(check["details"]["execution_status"], "needs_confirmation")
        self.assertIn("execution amounts are blocked", check["summary"])

    def test_alipay_check_missing_record_does_not_claim_update_exists(self) -> None:
        summary = UpdateSummary(
            start_date="2026-06-06",
            end_date="2026-06-06",
            updated_dates=[],
            missing_dates=[],
            log_rows=[],
        )
        with patch("src.monitoring.automation_health.summarize_updates", return_value=summary):
            check = _alipay_check("2026-06-06")

        self.assertEqual(check["status"], "warn")
        self.assertEqual(check["details"]["execution_status"], "missing")
        self.assertIn("missing or unconfirmed", check["summary"])
        self.assertNotIn("update exists", check["summary"])

    def test_policy_bridge_missing_warns_before_current_report_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("src.monitoring.automation_health.POLICY_STATUS_DIR", root / "status"), \
                patch("src.monitoring.automation_health.POLICY_EVENT_DIR", root / "events"), \
                patch("src.monitoring.automation_health._current_day_report_artifact_exists", return_value=False):
                check = _policy_bridge_check("2026-06-05", preflight=False)

        self.assertEqual(check["status"], "warn")
        self.assertIn("missing_policy_bridge_status", check["details"]["issues"])

    def test_policy_bridge_missing_fails_after_current_report_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("src.monitoring.automation_health.POLICY_STATUS_DIR", root / "status"), \
                patch("src.monitoring.automation_health.POLICY_EVENT_DIR", root / "events"), \
                patch("src.monitoring.automation_health._current_day_report_artifact_exists", return_value=True):
                check = _policy_bridge_check("2026-06-05", preflight=False)

        self.assertEqual(check["status"], "fail")
        self.assertIn("missing_policy_bridge_status", check["details"]["issues"])

    def test_policy_bridge_timeout_fails_strict_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_dir = root / "status"
            event_dir = root / "events"
            status_dir.mkdir()
            event_dir.mkdir()
            (status_dir / "policy_bridge_status_2026-06-04.json").write_text(
                '{"refresh":{"status":"timeout","reason":"policy pipeline exceeded"},"matched_event_count":2}',
                encoding="utf-8",
            )
            (event_dir / "policy_events_2026-06-04.csv").write_text(
                "\n".join(
                    [
                        "date,type,policy_match_basis,source_url",
                        "2026-06-04,government_policy_bridge,theme_match,https://www.gov.cn/policy.html",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("src.monitoring.automation_health.POLICY_STATUS_DIR", status_dir), \
                patch("src.monitoring.automation_health.POLICY_EVENT_DIR", event_dir), \
                patch("src.monitoring.automation_health._current_day_report_artifact_exists", return_value=True):
                check = _policy_bridge_check("2026-06-04", preflight=False)

        self.assertEqual(check["status"], "fail")
        self.assertIn("policy_refresh_not_confirmed", check["details"]["issues"])

    def test_policy_bridge_matched_events_require_original_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_dir = root / "status"
            event_dir = root / "events"
            status_dir.mkdir()
            event_dir.mkdir()
            (status_dir / "policy_bridge_status_2026-06-04.json").write_text(
                '{"refresh":{"status":"refreshed"},"matched_event_count":1}',
                encoding="utf-8",
            )
            (event_dir / "policy_events_2026-06-04.csv").write_text(
                "\n".join(
                    [
                        "date,type,policy_match_basis,source_url",
                        "2026-06-04,government_policy_bridge,theme_match,local://status-only",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("src.monitoring.automation_health.POLICY_STATUS_DIR", status_dir), \
                patch("src.monitoring.automation_health.POLICY_EVENT_DIR", event_dir), \
                patch("src.monitoring.automation_health._current_day_report_artifact_exists", return_value=True):
                check = _policy_bridge_check("2026-06-04", preflight=False)

        self.assertEqual(check["status"], "fail")
        self.assertIn("policy_events_without_original_source", check["details"]["issues"])

    def test_policy_bridge_matched_events_require_verified_crawler_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_dir = root / "status"
            event_dir = root / "events"
            status_dir.mkdir()
            event_dir.mkdir()
            (status_dir / "policy_bridge_status_2026-06-04.json").write_text(
                '{"refresh":{"status":"refreshed"},"matched_event_count":1}',
                encoding="utf-8",
            )
            (event_dir / "policy_events_2026-06-04.csv").write_text(
                "\n".join(
                    [
                        "date,type,policy_match_basis,source_url,policy_original_fetch_status,policy_request_path,policy_operation_impact,policy_report_path",
                        "2026-06-04,government_policy_bridge,theme_match,https://www.gov.cn/policy.html,missing,,,",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("src.monitoring.automation_health.POLICY_STATUS_DIR", status_dir), \
                patch("src.monitoring.automation_health.POLICY_EVENT_DIR", event_dir), \
                patch("src.monitoring.automation_health._current_day_report_artifact_exists", return_value=True):
                check = _policy_bridge_check("2026-06-04", preflight=False)

        self.assertEqual(check["status"], "fail")
        self.assertIn("policy_event_without_verified_original_fetch_status", check["details"]["issues"])
        self.assertIn("policy_event_without_separate_crawler_request", check["details"]["issues"])
        self.assertIn("policy_event_without_operation_impact", check["details"]["issues"])
        self.assertIn("policy_event_without_policy_report_path", check["details"]["issues"])

    def _write_sample_inputs(self, root: Path) -> None:
        sample = root / "data" / "sample"
        sample.mkdir(parents=True)
        (sample / "watchlist_moomoo.csv").write_text(
            "\n".join(
                [
                    "group_name,stock_id,symbol,code,name,eng_name,exchange,region,currency_code,instrument_type,asset_class,research_group",
                    "全部,1,QQQ,QQQ,纳指ETF,,US,4,55,4,ETF,美股科技",
                    "全部,2,512620,512620,农业ETF,,SSE,2,13,4,ETF,农业",
                ]
            ),
            encoding="utf-8",
        )
        (sample / "watchlist_snapshot.csv").write_text(
            "\n".join(
                [
                    "date,symbol,quote_code,name,exchange,asset_class,research_group,close,daily_change_pct,open,high,low,volume,turnover,snapshot_note,source_name,source_url",
                    "2026-06-04,QQQ,US.QQQ,纳指ETF,US,ETF,美股科技,100,0.01,99,101,98,1000,100000,moomoo,Moomoo OpenD,opend://127.0.0.1",
                    "2026-06-04,512620,SH.512620,农业ETF,SSE,ETF,农业,1,0.02,1,1,1,1000,1000,fallback,Yahoo Finance (US),https://finance.yahoo.com",
                ]
            ),
            encoding="utf-8",
        )
        (sample / "opend_quote_diagnostics_2026-06-04.csv").write_text(
            "\n".join(
                [
                    "date,symbol,quote_code,name,exchange,asset_class,opend_status,opend_error_category,opend_error,fallback_status,fallback_source_name,fallback_source_time,diagnosis",
                    "2026-06-04,QQQ,US.QQQ,纳指ETF,US,ETF,ok,ok,,not_needed,,,OpenD returned quote",
                    "2026-06-04,512620,SH.512620,农业ETF,SSE,ETF,failed,quote_permission,No permission to get quotes,used,Yahoo Finance (US),2026-06-04 07:00:00 UTC,OpenD permission missing",
                ]
            ),
            encoding="utf-8",
        )

    def _write_automation(self, root: Path, automation_id: str, prompt: str) -> None:
        path = root / automation_id / "automation.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "version = 1",
                    f'id = "{automation_id}"',
                    'kind = "cron"',
                    f'name = "{automation_id}"',
                    f'prompt = "{prompt}"',
                    'status = "ACTIVE"',
                    'model = "gpt-5.5"',
                    'reasoning_effort = "xhigh"',
                ]
            ),
            encoding="utf-8",
        )

    def _check(self, name: str, status: str) -> dict[str, object]:
        return {"name": name, "status": status, "summary": name, "details": {}}


if __name__ == "__main__":
    unittest.main()
