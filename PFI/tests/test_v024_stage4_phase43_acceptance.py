from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

from pfi_v02.stage_v024_stage4_data_state import (
    build_v024_metric_state,
    render_v024_metric_value_zh,
)


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
PHASE43_DIR = ROOT / "reports" / "pfi_v024" / "stage_4" / "phase_4_3"
SCREENSHOT_DIR = PHASE43_DIR / "screenshots"


class TestV024Stage4Phase43Acceptance(unittest.TestCase):
    def test_blocked_core_metrics_do_not_render_as_financial_zero(self) -> None:
        blocked_metrics = [
            build_v024_metric_state(
                "net_worth_cny",
                status="source_missing",
                source_id="read_model:accounts_holdings",
                formula_id="net_worth_v1",
                blocking_reason_zh="未挂链账户余额与持仓 read model，无法计算净资产",
            ),
            build_v024_metric_state(
                "cash_balance_cny",
                status="not_loaded",
                source_id="read_model:accounts",
                formula_id="cash_balance_v1",
                blocking_reason_zh="未加载账户余额真实数据",
            ),
            build_v024_metric_state(
                "investment_market_value_cny",
                status="filtered_empty",
                source_id="read_model:holdings",
                formula_id="investment_market_value_v1",
                blocking_reason_zh="当前筛选无持仓结果，不代表全局为零",
            ),
        ]

        for metric in blocked_metrics:
            rendered = render_v024_metric_value_zh(metric)
            self.assertNotIn("CNY 0.00", rendered)
            self.assertRegex(rendered, r"[\u4e00-\u9fff]")

    def test_confirmed_zero_requires_source_time_sample_and_formula(self) -> None:
        with self.assertRaisesRegex(ValueError, "confirmed_zero requires evidence"):
            build_v024_metric_state(
                "cash_balance_cny",
                status="confirmed_zero",
                value=0,
                source_id="read_model:accounts",
                formula_id="cash_balance_v1",
            )

        confirmed_zero = build_v024_metric_state(
            "cash_balance_cny",
            status="confirmed_zero",
            value=0,
            source_id="manual_balance_snapshot:cash:test-zero",
            record_count=1,
            as_of="2026-06-30",
            formula_id="cash_balance_v1",
            confidence=1.0,
            blocking_reason_zh="真实余额快照确认现金为零",
            calculation_state="confirmed",
        )

        self.assertEqual(render_v024_metric_value_zh(confirmed_zero), "CNY 0.00")
        self.assertEqual(confirmed_zero["source_id"], "manual_balance_snapshot:cash:test-zero")
        self.assertEqual(confirmed_zero["record_count"], 1)
        self.assertEqual(confirmed_zero["as_of"], "2026-06-30")
        self.assertEqual(confirmed_zero["formula_id"], "cash_balance_v1")

    def test_frontend_preserves_unknown_record_count_for_blocked_metrics(self) -> None:
        payload = {
            "read_model_hash": "sha256:phase43-null-record-count",
            "as_of": "2026-06-30",
            "core_metric_states": [
                {
                    "metric_id": "net_worth_cny",
                    "value": None,
                    "currency": "CNY",
                    "status": "source_missing",
                    "source_id": "read_model:accounts_holdings",
                    "record_count": None,
                    "as_of": None,
                    "formula_id": "net_worth_v1",
                    "confidence": None,
                    "blocking_reason_zh": "未挂链账户余额与持仓 read model，无法计算净资产",
                    "calculation_state": "blocked_by_missing_source",
                }
            ],
        }
        script = """
const state = require('./PFI/web/app/data_state.js');
const payload = JSON.parse(process.argv[1]);
const metric = state.buildSurfaceMetricViews(payload).surfaces.home.metrics[0];
console.log(JSON.stringify(metric));
"""
        completed = subprocess.run(
            [NODE, "-e", script, json.dumps(payload, ensure_ascii=False)],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        metric = json.loads(completed.stdout)

        self.assertIsNone(metric["record_count"])
        self.assertIsNone(metric["confidence"])
        self.assertNotIn("0 条记录", metric["display_detail"])
        self.assertNotIn("CNY 0.00", metric["display_value"])

    def test_phase43_browser_script_and_evidence_exist(self) -> None:
        script_path = ROOT / "scripts" / "validate_v024_stage4_phase43_chrome.py"
        evidence_path = PHASE43_DIR / "evidence.json"
        browser_path = PHASE43_DIR / "browser_validation.json"
        missing_path = SCREENSHOT_DIR / "data_missing_state.png"
        zero_path = SCREENSHOT_DIR / "confirmed_zero_gate.png"

        for path in (script_path, evidence_path, browser_path, missing_path, zero_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        browser = json.loads(browser_path.read_text(encoding="utf-8"))

        self.assertEqual(evidence["schema"], "PFIV024Stage4Phase43EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 4")
        self.assertEqual(evidence["phase_id"], "4.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["phase_4_1_complete"])
        self.assertTrue(evidence["phase_4_2_complete"])
        self.assertTrue(evidence["phase_4_3_complete"])
        self.assertFalse(evidence["stage_4_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertTrue(evidence["no_financial_zero_when_data_missing"])
        self.assertTrue(evidence["confirmed_zero_requires_evidence"])
        self.assertIn("Stage 4 whole-stage review", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])

        self.assertEqual(browser["status"], "pass")
        self.assertTrue(browser["no_financial_zero_when_data_missing"])
        self.assertTrue(browser["missing_state_reason_visible"])
        self.assertTrue(browser["confirmed_zero_gate_visible"])
        self.assertEqual(browser["console_errors"], [])
        self.assertIn("未挂链", browser["dom_assertions"]["data_missing_text"])
        self.assertIn("真实余额快照确认现金为零", browser["dom_assertions"]["confirmed_zero_text"])
        self.assertNotIn("CNY 0.00", browser["dom_assertions"]["data_missing_text"])

        for key, relative_path in browser["screenshots"].items():
            screenshot = PHASE43_DIR / relative_path
            self.assertTrue(screenshot.exists(), key)
            self.assertGreater(screenshot.stat().st_size, 10_000, key)


if __name__ == "__main__":
    unittest.main()
