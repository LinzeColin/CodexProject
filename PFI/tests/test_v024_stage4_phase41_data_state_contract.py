from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
PHASE41_DIR = ROOT / "reports" / "pfi_v024" / "stage_4" / "phase_4_1"

EXPECTED_STATUSES = [
    "ready",
    "confirmed_zero",
    "not_loaded",
    "source_missing",
    "path_error",
    "parse_failed",
    "outdated_snapshot",
    "permission_denied",
    "calculation_failed",
    "filtered_empty",
]

REQUIRED_FIELDS = [
    "metric_id",
    "value",
    "currency",
    "status",
    "source_id",
    "record_count",
    "as_of",
    "formula_id",
    "confidence",
    "blocking_reason_zh",
    "calculation_state",
]


def load_data_state_module():
    spec = importlib.util.find_spec("pfi_v02.stage_v024_stage4_data_state")
    if spec is None:
        raise AssertionError("PFI/src/pfi_v02/stage_v024_stage4_data_state.py is required for Stage 4 Phase 4.1")
    return importlib.import_module("pfi_v02.stage_v024_stage4_data_state")


class TestV024Stage4Phase41DataStateContract(unittest.TestCase):
    def test_phase41_contract_is_limited_to_state_machine_definition(self) -> None:
        module = load_data_state_module()
        contract = module.build_v024_stage4_phase41_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 4")
        self.assertEqual(contract["phase_id"], "4.1")
        self.assertEqual(contract["phase_name"], "状态机定义")
        self.assertTrue(contract["current_phase_only"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertTrue(contract["no_mock_financial_data"])
        self.assertFalse(contract["read_model_wiring_done"])
        self.assertFalse(contract["ui_core_cards_wiring_done"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertIn("Stage 4 Phase 4.2 read model 挂链", contract["explicitly_not_done"])

    def test_metric_state_schema_matches_taskpack_stage4_required_fields(self) -> None:
        module = load_data_state_module()
        schema = module.build_v024_metric_state_schema()

        self.assertEqual(schema["title"], "PFI v0.2.4 Stage 4 Metric Data State")
        self.assertEqual(schema["required"], REQUIRED_FIELDS)
        self.assertEqual(schema["properties"]["status"]["enum"], EXPECTED_STATUSES)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, schema["properties"])

    def test_non_ready_states_never_display_financial_zero(self) -> None:
        module = load_data_state_module()

        non_display_statuses = [status for status in EXPECTED_STATUSES if status not in {"ready", "confirmed_zero"}]
        for status in non_display_statuses:
            metric = module.build_v024_metric_state("net_worth_cny", status=status)
            self.assertIsNone(metric["value"], status)
            self.assertFalse(module.can_display_v024_financial_value(metric), status)
            rendered = module.render_v024_metric_value_zh(metric)
            self.assertNotIn("CNY 0.00", rendered, status)
            self.assertIn(metric["blocking_reason_zh"], rendered)

    def test_ready_and_confirmed_zero_require_real_evidence_chain(self) -> None:
        module = load_data_state_module()

        with self.assertRaisesRegex(ValueError, "source_id"):
            module.build_v024_metric_state("cash_balance_cny", status="ready", value=1200.0)
        with self.assertRaisesRegex(ValueError, "confirmed_zero"):
            module.build_v024_metric_state("cash_balance_cny", status="confirmed_zero", value=0)

        ready = module.build_v024_metric_state(
            "cash_balance_cny",
            status="ready",
            value=1200.0,
            source_id="read_model:cash_balance",
            record_count=8815,
            as_of="2026-07-01T08:00:00+10:00",
            formula_id="net_cash_balance_v1",
            confidence=0.98,
        )
        confirmed_zero = module.build_v024_metric_state(
            "investment_market_value_cny",
            status="confirmed_zero",
            value=0,
            source_id="read_model:holdings",
            record_count=0,
            as_of="2026-07-01T08:00:00+10:00",
            formula_id="investment_market_value_v1",
            confidence=1.0,
        )

        self.assertTrue(module.can_display_v024_financial_value(ready))
        self.assertTrue(module.can_display_v024_financial_value(confirmed_zero))
        self.assertIn("CNY 1,200.00", module.render_v024_metric_value_zh(ready))
        self.assertIn("CNY 0.00", module.render_v024_metric_value_zh(confirmed_zero))

    def test_chinese_blocking_reasons_cover_every_status(self) -> None:
        module = load_data_state_module()
        reasons = module.build_v024_blocking_reason_zh()

        self.assertEqual(list(reasons), EXPECTED_STATUSES)
        self.assertIn("未加载", reasons["not_loaded"])
        self.assertIn("未挂链", reasons["source_missing"])
        self.assertIn("路径", reasons["path_error"])
        self.assertIn("解析", reasons["parse_failed"])
        self.assertIn("过期", reasons["outdated_snapshot"])
        self.assertIn("权限", reasons["permission_denied"])
        self.assertIn("计算", reasons["calculation_failed"])
        self.assertIn("筛选", reasons["filtered_empty"])

    def test_javascript_contract_matches_python_statuses_and_rules(self) -> None:
        module = load_data_state_module()
        js_path = ROOT / "web" / "app" / "data_state.js"
        self.assertTrue(js_path.exists(), "PFI/web/app/data_state.js is required for Stage 4 Phase 4.1")

        script = """
const state = require('./PFI/web/app/data_state.js');
console.log(JSON.stringify({
  statuses: state.statuses,
  requiredFields: state.requiredFields,
  blockingReasonZh: state.blockingReasonZh,
  nonDisplayValue: state.renderMetricValueZh({ metric_id: 'net_worth_cny', status: 'not_loaded' }),
  confirmedZeroValue: state.renderMetricValueZh({
    metric_id: 'cash_balance_cny',
    value: 0,
    currency: 'CNY',
    status: 'confirmed_zero',
    source_id: 'read_model:cash',
    record_count: 0,
    as_of: '2026-07-01T08:00:00+10:00',
    formula_id: 'net_cash_balance_v1',
    confidence: 1
  })
}));
"""
        completed = subprocess.run(
            [NODE, "-e", script],
            cwd=ROOT.parent,
            check=True,
            text=True,
            capture_output=True,
        )
        payload = json.loads(completed.stdout)

        self.assertEqual(payload["statuses"], list(module.METRIC_DATA_STATUSES))
        self.assertEqual(payload["requiredFields"], REQUIRED_FIELDS)
        self.assertNotIn("CNY 0.00", payload["nonDisplayValue"])
        self.assertIn("未加载", payload["nonDisplayValue"])
        self.assertIn("CNY 0.00", payload["confirmedZeroValue"])

    def test_phase41_doc_and_evidence_are_present(self) -> None:
        doc_path = ROOT / "docs" / "pfi_v024" / "STAGE4_DATA_STATE_MACHINE.md"
        evidence_path = PHASE41_DIR / "evidence.json"
        changed_files_path = PHASE41_DIR / "changed_files.txt"
        terminal_log_path = PHASE41_DIR / "terminal.log"
        risk_path = PHASE41_DIR / "risk_and_rollback.md"

        for path in (doc_path, evidence_path, changed_files_path, terminal_log_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage4Phase41EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 4")
        self.assertEqual(evidence["phase_id"], "4.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertFalse(evidence["phase_4_2_started"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertEqual(evidence["changed_files"], changed_files)


if __name__ == "__main__":
    unittest.main()
