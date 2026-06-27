from __future__ import annotations

import unittest

from pfi_v02.stage1_ia import (
    FORBIDDEN_PRIMARY_ENTRY_MARKERS,
    LEGACY_COMPATIBILITY_ENTRY,
    build_stage1_ia_contract,
    primary_entry_labels,
    v01_compatibility_entry_labels,
)


class Stage1IAContractTest(unittest.TestCase):
    def test_stage1_primary_entries_are_exactly_the_v02_target(self) -> None:
        self.assertEqual(
            primary_entry_labels(),
            (
                "首页总览",
                "账户与资产",
                "账本流水",
                "投资管理",
                "消费管理",
                "数据源与同步",
                "建议与复盘",
                "报告与洞察",
            ),
        )

    def test_each_entry_has_user_facing_second_level_areas(self) -> None:
        contract = build_stage1_ia_contract()
        entries = contract["primary_entries"]

        self.assertEqual(len(entries), 8)
        for entry in entries:
            self.assertGreaterEqual(len(entry["second_level_areas"]), 8, entry["label"])
            self.assertGreaterEqual(len(entry["acceptance_markers"]), 4, entry["label"])
            self.assertNotIn(entry["label"], FORBIDDEN_PRIMARY_ENTRY_MARKERS)

    def test_home_contract_contains_required_owner_summary_markers(self) -> None:
        home = build_stage1_ia_contract()["primary_entries"][0]
        markers = set(home["acceptance_markers"])

        for marker in ["净资产", "账户地图", "投资快照", "消费快照", "数据健康", "今日建议"]:
            self.assertIn(marker, markers)

    def test_account_and_ledger_contracts_separate_sources_accounts_assets_and_events(self) -> None:
        entries = {entry["label"]: entry for entry in build_stage1_ia_contract()["primary_entries"]}

        account_markers = " ".join(entries["账户与资产"]["acceptance_markers"])
        ledger_markers = " ".join(entries["账本流水"]["acceptance_markers"])

        self.assertIn("DataSource != Account", account_markers)
        self.assertIn("Account != AssetInstrument", account_markers)
        for marker in ["消费", "投资", "转账", "退款", "费用", "估值", "汇率"]:
            self.assertIn(marker, ledger_markers)

    def test_investment_management_preserves_strategy_lab_and_big_data_simulator(self) -> None:
        entries = {entry["label"]: entry for entry in build_stage1_ia_contract()["primary_entries"]}
        investment_text = " ".join(entries["投资管理"]["second_level_areas"] + entries["投资管理"]["acceptance_markers"])

        for marker in ["Moomoo", "支付宝基金", "中国券商", "ABC Bullion", "策略实验室", "盘感训练", "大数据模拟器"]:
            self.assertIn(marker, investment_text)
        self.assertNotIn("QBVS", investment_text)
        self.assertEqual(LEGACY_COMPATIBILITY_ENTRY["existing_path"], "QBVS")
        self.assertEqual(LEGACY_COMPATIBILITY_ENTRY["current_root"], "CodexProject/QBVS")
        self.assertEqual(LEGACY_COMPATIBILITY_ENTRY["runtime_path"], "QBVS/qbvs")
        self.assertIn("independent", LEGACY_COMPATIBILITY_ENTRY["policy"].lower())

    def test_v01_primary_entries_remain_as_compatibility_aliases(self) -> None:
        self.assertEqual(v01_compatibility_entry_labels(), ("首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"))
        self.assertEqual(
            tuple(build_stage1_ia_contract()["v01_compatibility_entries"]),
            ("首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"),
        )

    def test_consumption_data_recommendation_and_report_entries_cover_stage1_acceptance(self) -> None:
        entries = {entry["label"]: entry for entry in build_stage1_ia_contract()["primary_entries"]}

        consumption_text = " ".join(entries["消费管理"]["acceptance_markers"])
        data_text = " ".join(entries["数据源与同步"]["acceptance_markers"])
        recommendation_text = " ".join(entries["建议与复盘"]["acceptance_markers"])
        report_text = " ".join(entries["报告与洞察"]["acceptance_markers"])

        for marker in ["支付宝", "微信", "CBA", "银行卡", "信用卡", "订阅", "转账不计消费"]:
            self.assertIn(marker, consumption_text)
        for marker in ["数据源列表", "凭证", "同步", "导入", "对账", "待复核", "外部只读接口"]:
            self.assertIn(marker, data_text)
        for marker in ["证据", "动作", "状态", "复盘"]:
            self.assertIn(marker, recommendation_text)
        for marker in ["月度", "投资", "消费", "数据质量", "Context Export", "证据链"]:
            self.assertIn(marker, report_text)

    def test_contract_excludes_product_l1_forbidden_entries_and_execution(self) -> None:
        contract = build_stage1_ia_contract()
        labels = primary_entry_labels()

        self.assertNotIn("Alpha", labels)
        self.assertNotIn("System", labels)
        self.assertNotIn("Development", labels)
        self.assertNotIn("系统与开发", labels)
        self.assertIn("no trading password", contract["non_execution_boundary"])
        self.assertIn("no automatic real-money order", contract["non_execution_boundary"])


if __name__ == "__main__":
    unittest.main()
