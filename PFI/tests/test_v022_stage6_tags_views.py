from __future__ import annotations

import importlib
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022Stage6TagsViews(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_tags_views")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 6 tag/view module is missing: {exc}")

    def test_stage6_contract_locks_phase_task_acceptance_and_validation(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        build_contract = getattr(governance, "build_v022_stage6_contract", None)
        self.assertIsNotNone(build_contract, "build_v022_stage6_contract() is required")

        contract = build_contract()

        self.assertEqual(contract["schema"], "PFIV022TagViewStage6ContractV1")
        self.assertEqual(contract["stage"], "Stage 6")
        self.assertEqual(
            tuple(contract["task_ids"]),
            (
                "S6-P1-T1",
                "S6-P1-T2",
                "S6-P1-T3",
                "S6-P2-T1",
                "S6-P2-T2",
                "S6-P2-T3",
                "S6-P3-T1",
                "S6-P3-T2",
                "S6-P3-T3",
            ),
        )
        for required in (
            "pfi_tags",
            "pfi_tag_assignments",
            "pfi_tag_rules",
            "pfi_tag_history",
            "自定义视图",
            "PFI/tests/test_v022_stage6_tags_views.py",
            "Stage 7 现金流窗口不在本轮实现",
        ):
            self.assertIn(required, str(contract))

    def test_tag_registry_schema_persists_default_tags_and_groups(self) -> None:
        module = self._module()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "stage6_tags.sqlite"
            store = module.Stage6TagViewStore(db_path)
            store.initialize_schema()
            store.seed_default_tags()

            reopened = module.Stage6TagViewStore(db_path)
            tags = {tag["tag_id"]: tag for tag in reopened.list_tags(include_disabled=True)}

        self.assertGreaterEqual(len(tags), 40)
        self.assertIn("tag_consumption_night", tags)
        self.assertIn("tag_investment_chase_candidate", tags)
        self.assertIn("tag_quality_low_confidence", tags)
        groups = {tag["group_zh"] for tag in tags.values()}
        self.assertTrue({"通用", "消费", "投资", "数据质量", "现金流", "复盘"}.issubset(groups))
        for tag in tags.values():
            with self.subTest(tag=tag["tag_id"]):
                self.assertRegex(tag["label_zh"], r"[\u4e00-\u9fff]")
                self.assertIn(tag["scope"], {"transaction", "economic_event", "holding", "account", "report"})
                self.assertIn(tag["tag_type"], {"default", "custom"})
                self.assertIsInstance(tag["is_system_default"], bool)
                self.assertIsInstance(tag["is_editable"], bool)
                self.assertIsInstance(tag["is_enabled"], bool)

    def test_custom_tag_lifecycle_assignment_and_history_are_persistent(self) -> None:
        module = self._module()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "stage6_tags.sqlite"
            store = module.Stage6TagViewStore(db_path)
            store.initialize_schema()
            store.seed_default_tags()
            custom = store.create_custom_tag("家人相关", scope="transaction")
            renamed = store.rename_tag(custom["tag_id"], "家庭支持")
            store.assign_tags(
                target_type="transaction",
                target_id="txn_wechat_001",
                tag_ids=(renamed["tag_id"], "tag_consumption_large", "tag_general_manual_reviewed"),
                assigned_by="owner",
            )
            store.disable_tag(renamed["tag_id"], reason_zh="本月暂不使用")
            store.delete_custom_tag(renamed["tag_id"], reason_zh="合并到家庭责任")

            reopened = module.Stage6TagViewStore(db_path)
            assignments = reopened.get_assignments("transaction", "txn_wechat_001")
            history = reopened.list_tag_history(renamed["tag_id"])
            with self.assertRaises(ValueError):
                reopened.delete_custom_tag("tag_consumption_night")

        self.assertEqual(
            {item["tag_id"] for item in assignments},
            {renamed["tag_id"], "tag_consumption_large", "tag_general_manual_reviewed"},
        )
        self.assertGreaterEqual(len(history), 4)
        actions = [item["action"] for item in history]
        self.assertIn("create", actions)
        self.assertIn("rename", actions)
        self.assertIn("disable", actions)
        self.assertIn("delete", actions)
        self.assertIn("old_value", history[1])
        self.assertIn("new_value", history[1])

    def test_tag_rules_auto_apply_and_filter_ledger_by_tag_combination(self) -> None:
        module = self._module()
        records = (
            {
                "record_id": "txn_night_large",
                "amount_cny": Decimal("2500.00"),
                "local_time": "23:15",
                "l1_category": "娱乐社交",
                "event_type": "consumption",
                "account_roles": ("consumer_wallet",),
            },
            {
                "record_id": "txn_subscription",
                "amount_cny": Decimal("88.00"),
                "local_time": "09:00",
                "l1_category": "订阅服务",
                "event_type": "consumption",
                "account_roles": ("consumer_wallet",),
            },
            {
                "record_id": "txn_invest_deposit",
                "amount_cny": Decimal("5000.00"),
                "local_time": "10:00",
                "l1_category": "投资资金流出",
                "event_type": "investment_deposit",
                "account_roles": ("investment_funding_source",),
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            store = module.Stage6TagViewStore(Path(tmpdir) / "stage6_tags.sqlite")
            store.initialize_schema()
            store.seed_default_tags()
            applied = store.apply_tag_rules(records)
            filtered = store.filter_ledger_by_tags(
                records,
                required_tag_ids=("tag_consumption_night", "tag_consumption_large"),
                match="all",
            )

        self.assertIn("tag_consumption_night", applied["txn_night_large"])
        self.assertIn("tag_consumption_large", applied["txn_night_large"])
        self.assertIn("tag_consumption_subscription", applied["txn_subscription"])
        self.assertIn("tag_investment_deposit", applied["txn_invest_deposit"])
        self.assertEqual([item["record_id"] for item in filtered], ["txn_night_large"])

    def test_tag_driven_report_and_custom_views_are_saved_and_renderable_html(self) -> None:
        module = self._module()
        records = (
            {"record_id": "txn_001", "amount_cny": Decimal("68.00"), "event_type": "consumption"},
            {"record_id": "txn_002", "amount_cny": Decimal("2000.00"), "event_type": "investment_buy"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "stage6_tags.sqlite"
            store = module.Stage6TagViewStore(db_path)
            store.initialize_schema()
            store.seed_default_tags()
            store.assign_tags("transaction", "txn_001", ("tag_consumption_subscription", "tag_general_recurring"))
            store.assign_tags("transaction", "txn_002", ("tag_investment_buy", "tag_investment_chase_candidate"))
            report = store.build_tag_report(records)
            view = store.save_custom_view(
                name_zh="订阅检查",
                required_tag_ids=("tag_consumption_subscription", "tag_general_recurring"),
                description_zh="检查周期性订阅扣费",
            )
            html = store.render_custom_views_html()
            reopened = module.Stage6TagViewStore(db_path)
            views = reopened.list_custom_views()

        self.assertEqual(report["schema"], "PFIV022Stage6TagDrivenReportV1")
        self.assertEqual(report["by_tag"]["tag_consumption_subscription"]["record_count"], 1)
        self.assertEqual(report["by_tag"]["tag_investment_buy"]["amount_cny"], Decimal("2000.00"))
        self.assertEqual(view["name_zh"], "订阅检查")
        self.assertEqual(views[0]["name_zh"], "订阅检查")
        self.assertIn("订阅检查", html)
        self.assertIn("标签筛选", html)
        self.assertIn("自定义视图", html)
        self.assertIn("tag_consumption_subscription", html)

    def test_stage6_docs_and_parameter_catalog_record_tag_view_governance(self) -> None:
        expected_docs = (
            ROOT / "docs" / "pfi_v022" / "STAGE6_TAGS_CUSTOM_VIEWS.md",
            ROOT / "docs" / "pfi_v022" / "ROADMAP_LOCK.md",
            ROOT / "web" / "pfi_v022_tag_views.html",
            ROOT / "模型参数文件.md",
            ROOT / "功能清单.md",
            ROOT / "开发记录.md",
        )
        for path in expected_docs:
            self.assertTrue(path.exists(), f"{path} must exist for Stage 6")
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Stage 6 - 标签系统与自定义视图", text)
                self.assertIn("S6-P1-T1", text)
                self.assertIn("pfi_tags", text)
                self.assertIn("pfi_tag_assignments", text)
                self.assertIn("pfi_tag_history", text)
                self.assertIn("自定义视图", text)

        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        catalog = governance.load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        self.assertEqual(catalog["schema"], "PFIParametersV022Stage10")
        self.assertEqual(catalog["current_stage"], "Stage 10 - 报告、建议与复盘")
        self.assertEqual(catalog["stage6_task_ids"], list(governance.V022_STAGE6_TASK_IDS))
        tags = catalog["parameters"]["tags"]
        self.assertIn("default_tag_library", tags)
        self.assertIn("custom_view_defaults", tags)
        self.assertIn("tag_rule_dimensions", tags)


if __name__ == "__main__":
    unittest.main()
