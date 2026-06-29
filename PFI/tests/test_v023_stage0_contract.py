from __future__ import annotations

import json
from pathlib import Path
import unittest

from pfi_v02.stage_v023_contract import (
    build_stage0_contract,
    current_stage0_baseline,
    deprecated_constraints,
    forbidden_financial_data_terms,
    official_nav,
)


ROOT = Path(__file__).resolve().parents[1]


class TestV023Stage0Contract(unittest.TestCase):
    def test_official_nav_is_exactly_ten_entries_with_market_research(self) -> None:
        self.assertEqual(
            official_nav,
            [
                "首页总览",
                "账户与资产",
                "账本流水",
                "投资管理",
                "消费管理",
                "数据源与上传",
                "建议与复盘",
                "报告与洞察",
                "市场与研究",
                "设置",
            ],
        )
        self.assertEqual(len(official_nav), 10)
        self.assertIn("市场与研究", official_nav)
        self.assertEqual(official_nav.index("市场与研究"), 8)

    def test_history_constraints_are_explicitly_deprecated(self) -> None:
        contract = build_stage0_contract()

        self.assertIn("9 个一级入口", deprecated_constraints)
        self.assertIn("市场与研究不得作为一级入口", deprecated_constraints)
        self.assertIn("9 个一级入口", contract["deprecated_constraints"])
        self.assertIn("市场与研究不得作为一级入口", contract["deprecated_constraints"])
        self.assertTrue(contract["one_stage_per_run"])
        self.assertTrue(contract["requires_user_acceptance"])
        self.assertTrue(contract["no_auto_closeout"])
        self.assertTrue(contract["stage0_only"])

    def test_no_mock_financial_data_contract_is_strict(self) -> None:
        contract = build_stage0_contract()

        self.assertTrue(contract["no_mock_financial_data"])
        for term in ("mock", "sample", "synthetic", "fixture", "demo", "fake", "测试样例"):
            self.assertIn(term, forbidden_financial_data_terms)
            self.assertIn(term, contract["forbidden_financial_data_terms"])
        self.assertIn("not_loaded", contract["metric_data_statuses"])
        self.assertIn("confirmed_zero", contract["metric_data_statuses"])
        self.assertIn("calculation_error", contract["metric_data_statuses"])

    def test_stage0_allowed_files_exclude_ui_business_changes(self) -> None:
        contract = build_stage0_contract()

        self.assertIn("PFI/docs/pfi_v023/*", contract["allowed_files"])
        self.assertIn("PFI/reports/pfi_v023/stage_0/*", contract["allowed_files"])
        self.assertNotIn("PFI/web/index.html", contract["allowed_files"])
        self.assertNotIn("PFI/web/app/shell.js", contract["allowed_files"])
        self.assertIn("UI visual rebuild", contract["explicitly_not_done"])
        self.assertIn("route implementation", contract["explicitly_not_done"])
        self.assertIn("data computation or read-model changes", contract["explicitly_not_done"])

    def test_stage0_documents_are_chinese_and_record_latest_contract(self) -> None:
        docs = {
            "README.md": ROOT / "docs" / "pfi_v023" / "README.md",
            "HISTORY_DEPRECATION_POLICY.md": ROOT / "docs" / "pfi_v023" / "HISTORY_DEPRECATION_POLICY.md",
            "DATA_TRUST_RULES.md": ROOT / "docs" / "pfi_v023" / "DATA_TRUST_RULES.md",
            "STAGE0_BASELINE.md": ROOT / "docs" / "pfi_v023" / "STAGE0_BASELINE.md",
        }
        for path in docs.values():
            self.assertTrue(path.exists(), str(path))
            text = path.read_text(encoding="utf-8")
            self.assertIn("v0.2.3", text)
        combined_docs = "\n".join(path.read_text(encoding="utf-8") for path in docs.values())
        self.assertIn("市场与研究", combined_docs)

        readme = docs["README.md"].read_text(encoding="utf-8")
        self.assertIn("PFI v0.2.3 人类产品体验恢复版", readme)
        self.assertIn("正式一级入口固定为 10 个", readme)
        self.assertIn("不得使用 mock、sample、synthetic、fixture、demo、fake", readme)

        deprecation = docs["HISTORY_DEPRECATION_POLICY.md"].read_text(encoding="utf-8")
        self.assertIn("一级入口 9 个", deprecation)
        self.assertIn("`市场与研究` 不得作为一级入口", deprecation)
        self.assertIn("作废", deprecation)

        data_rules = docs["DATA_TRUST_RULES.md"].read_text(encoding="utf-8")
        self.assertIn("非假零规则", data_rules)
        self.assertIn("confirmed_zero", data_rules)
        self.assertIn("not_loaded", data_rules)

    def test_current_baseline_records_existing_shell_without_mutating_ui(self) -> None:
        baseline = current_stage0_baseline(ROOT)

        self.assertTrue(baseline["web_index_exists"])
        self.assertTrue(baseline["shell_js_exists"])
        self.assertTrue(baseline["web_index_primary_entry_count_marker"])
        self.assertTrue(baseline["web_index_has_market_research"])
        self.assertTrue(baseline["shell_has_market_research"])
        self.assertTrue(baseline["shell_has_strategy_lab_keyword"])
        self.assertFalse(baseline["stage0_modifies_ui"])

    def test_evidence_pack_contract_is_declared(self) -> None:
        contract = build_stage0_contract()

        self.assertIn("PFI/reports/pfi_v023/stage_0/evidence.json", contract["evidence_files"])
        self.assertIn("PFI/reports/pfi_v023/stage_0/terminal.log", contract["evidence_files"])
        self.assertIn("PFI/reports/pfi_v023/stage_0/changed_files.txt", contract["evidence_files"])
        commands = [item["command"] for item in contract["validation_commands"]]
        self.assertIn("node --check PFI/web/app/shell.js", commands)
        self.assertIn("python3 -m pytest PFI/tests/test_v023_stage0_contract.py -q", commands)

    def test_evidence_pack_files_are_machine_readable(self) -> None:
        evidence_path = ROOT / "reports" / "pfi_v023" / "stage_0" / "evidence.json"
        changed_files_path = ROOT / "reports" / "pfi_v023" / "stage_0" / "changed_files.txt"
        terminal_log_path = ROOT / "reports" / "pfi_v023" / "stage_0" / "terminal.log"

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in changed_files_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 0")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["allowed_files_obeyed"])
        self.assertTrue(evidence["history_deprecation_policy_obeyed"])
        self.assertTrue(evidence["no_mock_financial_data"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertIn("PFI/src/pfi_v02/stage_v023_contract.py", changed_files)
        self.assertIn("PFI/tests/test_v023_stage0_contract.py", changed_files)
        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("python3 -m pytest PFI/tests/test_v023_stage0_contract.py -q", terminal_log)
        self.assertIn("node --check PFI/web/app/shell.js", terminal_log)


if __name__ == "__main__":
    unittest.main()
