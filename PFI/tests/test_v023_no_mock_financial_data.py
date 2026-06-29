from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_data_state_module():
    spec = importlib.util.find_spec("pfi_v02.stage_v023_data_state")
    if spec is None:
        raise AssertionError("PFI/src/pfi_v02/stage_v023_data_state.py is required for Stage 2 Phase 2.1")
    return importlib.import_module("pfi_v02.stage_v023_data_state")


class TestV023NoMockFinancialData(unittest.TestCase):
    def test_stage2_contract_declares_strict_forbidden_financial_data_terms(self) -> None:
        module = load_data_state_module()
        contract = module.build_stage2_phase21_contract()

        self.assertTrue(contract["no_mock_financial_data"])
        self.assertEqual(
            contract["financial_data_forbidden_terms"],
            ["mock", "sample", "synthetic", "fixture", "demo", "fake"],
        )

    def test_scanner_flags_forbidden_financial_data_in_runtime_payloads(self) -> None:
        module = load_data_state_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_file = Path(temp_dir) / "finance_payload.js"
            bad_file.write_text("const netWorth = 'mock CNY 999.00';\n", encoding="utf-8")

            violations = module.scan_forbidden_financial_data_terms([bad_file])

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["term"], "mock")
        self.assertEqual(violations[0]["line"], 1)
        self.assertIn("finance_payload.js", violations[0]["path"])

    def test_scanner_allows_policy_documents_but_not_runtime_financial_payloads(self) -> None:
        module = load_data_state_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            policy_file = Path(temp_dir) / "DATA_TRUST_RULES.md"
            policy_file.write_text("禁止 mock/sample/synthetic/fixture/demo/fake 财务数据。\n", encoding="utf-8")
            runtime_file = Path(temp_dir) / "dataStatus.js"
            runtime_file.write_text("const balance = 'ready';\n", encoding="utf-8")

            violations = module.scan_forbidden_financial_data_terms([policy_file, runtime_file])

        self.assertEqual(violations, [])

    def test_stage2_phase21_runtime_files_do_not_ship_forbidden_financial_data_terms(self) -> None:
        module = load_data_state_module()
        runtime_files = [
            ROOT / "web" / "app" / "dataStatus.js",
        ]
        for path in runtime_files:
            self.assertTrue(path.exists(), str(path))

        violations = module.scan_forbidden_financial_data_terms(runtime_files)

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
