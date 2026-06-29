from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_STATUSES = [
    "ready",
    "confirmed_zero",
    "not_loaded",
    "not_mounted",
    "path_error",
    "permission_error",
    "parse_error",
    "outdated",
    "filter_empty",
    "calculation_error",
    "review_required",
]

REQUIRED_FIELDS = [
    "metric_id",
    "label",
    "value",
    "currency",
    "status",
    "source",
    "as_of",
    "evidence_hash",
    "message_zh",
]


def load_data_state_module():
    spec = importlib.util.find_spec("pfi_v02.stage_v023_data_state")
    if spec is None:
        raise AssertionError("PFI/src/pfi_v02/stage_v023_data_state.py is required for Stage 2 Phase 2.1")
    return importlib.import_module("pfi_v02.stage_v023_data_state")


class TestV023Stage2DataStateMachine(unittest.TestCase):
    def test_phase21_contract_is_limited_to_data_state_contract(self) -> None:
        module = load_data_state_module()
        contract = module.build_stage2_phase21_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 2")
        self.assertEqual(contract["phase_id"], "V023-S2-P2.1")
        self.assertEqual(contract["phase_name"], "数据状态合同")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["taskpack_restored"])
        self.assertTrue(contract["no_mock_financial_data"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_data_state.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/dataStatus.js", contract["allowed_files"])
        self.assertNotIn("PFI/web/index.html", contract["allowed_files"])
        self.assertNotIn("PFI/web/app/shell.js", contract["allowed_files"])
        self.assertIn("真实数据源路径审计", contract["explicitly_not_done"])
        self.assertIn("页面门禁接入", contract["explicitly_not_done"])

    def test_metric_schema_matches_taskpack_required_fields_and_statuses(self) -> None:
        module = load_data_state_module()
        schema = module.build_metric_data_state_schema()

        self.assertEqual(schema["title"], "PFI v0.2.3 Metric Data State")
        self.assertEqual(schema["required"], REQUIRED_FIELDS)
        self.assertEqual(schema["properties"]["status"]["enum"], EXPECTED_STATUSES)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, schema["properties"])

    def test_non_display_states_never_render_financial_zero(self) -> None:
        module = load_data_state_module()

        non_display_statuses = [status for status in EXPECTED_STATUSES if status not in {"ready", "confirmed_zero"}]
        for status in non_display_statuses:
            metric = module.build_metric_state("net_worth_cny", "净资产", status=status)
            self.assertIsNone(metric["value"], status)
            self.assertFalse(module.can_display_financial_value(metric), status)
            rendered = module.render_metric_value_zh(metric)
            self.assertNotIn("CNY 0.00", rendered, status)
            self.assertIn(metric["message_zh"], rendered)

    def test_ready_and_confirmed_zero_require_full_evidence_chain(self) -> None:
        module = load_data_state_module()

        with self.assertRaisesRegex(ValueError, "source"):
            module.build_metric_state("cash_balance_cny", "现金余额", status="ready", value=1200.0)
        with self.assertRaisesRegex(ValueError, "confirmed_zero"):
            module.build_metric_state("cash_balance_cny", "现金余额", status="confirmed_zero", value=0)

        ready = module.build_metric_state(
            "cash_balance_cny",
            "现金余额",
            status="ready",
            value=1200.0,
            source="read_model:cash_balance",
            as_of="2026-06-30T00:00:00+10:00",
            evidence_hash="sha256:cash",
        )
        confirmed_zero = module.build_metric_state(
            "investment_market_value_cny",
            "投资市值",
            status="confirmed_zero",
            value=0,
            source="read_model:holdings",
            as_of="2026-06-30T00:00:00+10:00",
            evidence_hash="sha256:holdings",
        )

        self.assertTrue(module.can_display_financial_value(ready))
        self.assertTrue(module.can_display_financial_value(confirmed_zero))
        self.assertIn("CNY 1,200.00", module.render_metric_value_zh(ready))
        self.assertIn("CNY 0.00", module.render_metric_value_zh(confirmed_zero))

    def test_chinese_status_copy_covers_every_taskpack_state(self) -> None:
        module = load_data_state_module()
        copy = module.build_status_copy_zh()

        self.assertEqual(list(copy), EXPECTED_STATUSES)
        for status, message in copy.items():
            self.assertIsInstance(message, str)
            self.assertGreaterEqual(len(message), 4, status)
            self.assertNotEqual(message.lower(), status)
        self.assertIn("未加载", copy["not_loaded"])
        self.assertIn("路径", copy["path_error"])
        self.assertIn("权限", copy["permission_error"])
        self.assertIn("解析", copy["parse_error"])
        self.assertIn("快照", copy["outdated"])

    def test_core_metric_contract_returns_safe_not_loaded_defaults(self) -> None:
        module = load_data_state_module()
        metrics = module.build_core_metric_states_not_loaded()
        metric_ids = [item["metric_id"] for item in metrics]

        self.assertIn("net_worth_cny", metric_ids)
        self.assertIn("cash_balance_cny", metric_ids)
        self.assertIn("investment_market_value_cny", metric_ids)
        self.assertEqual(len(metric_ids), len(set(metric_ids)))
        for metric in metrics:
            self.assertEqual(set(metric), set(REQUIRED_FIELDS))
            self.assertEqual(metric["status"], "not_loaded")
            self.assertIsNone(metric["value"])
            self.assertIsNone(metric["source"])
            self.assertIsNone(metric["as_of"])
            self.assertIsNone(metric["evidence_hash"])

    def test_javascript_data_status_contract_matches_python_contract(self) -> None:
        module = load_data_state_module()
        js_path = ROOT / "web" / "app" / "dataStatus.js"
        self.assertTrue(js_path.exists(), "PFI/web/app/dataStatus.js is required")
        text = js_path.read_text(encoding="utf-8")

        self.assertIn("PFI_STAGE2_DATA_STATUS", text)
        for status in module.METRIC_DATA_STATUSES:
            self.assertIn(status, text)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, text)
        self.assertNotIn("CNY 0.00", text)
        self.assertNotIn("mock", text.lower())
        self.assertNotIn("sample", text.lower())

    def test_stage2_phase21_doc_and_evidence_are_machine_readable(self) -> None:
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE2_DATA_TRUST.md"
        evidence_path = ROOT / "reports" / "pfi_v023" / "stage_2" / "phase_2_1" / "evidence.json"
        changed_files_path = ROOT / "reports" / "pfi_v023" / "stage_2" / "phase_2_1" / "changed_files.txt"
        terminal_log_path = ROOT / "reports" / "pfi_v023" / "stage_2" / "phase_2_1" / "terminal.log"

        self.assertTrue(doc_path.exists())
        self.assertTrue(evidence_path.exists())
        self.assertTrue(changed_files_path.exists())
        self.assertTrue(terminal_log_path.exists())

        doc_text = doc_path.read_text(encoding="utf-8")
        self.assertIn("Stage 2 Phase 2.1", doc_text)
        self.assertIn("真实数据状态机", doc_text)
        self.assertIn("未加载真实数据时不显示 CNY 0.00", doc_text)
        self.assertIn("本 phase 不做真实数据源路径审计", doc_text)

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in changed_files_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 2")
        self.assertEqual(evidence["phase_id"], "V023-S2-P2.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["allowed_files_obeyed"])
        self.assertTrue(evidence["no_mock_financial_data"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertIn("PFI/src/pfi_v02/stage_v023_data_state.py", changed_files)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("python3 -m pytest PFI/tests/test_v023_stage2_data_state_machine.py -q", terminal_log)
        self.assertIn("node --check PFI/web/app/dataStatus.js", terminal_log)


if __name__ == "__main__":
    unittest.main()
