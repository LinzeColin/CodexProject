from __future__ import annotations

from datetime import date
from decimal import Decimal
import inspect
from pathlib import Path
import unittest

from pfi_v02.stage_v022_database_governance import (
    V022_STAGE3_TASK_IDS,
    V022_STAGE4_TASK_IDS,
    build_v022_stage3_contract,
    load_v022_parameter_catalog,
)
from pfi_v02.stage_v022_source_profile import (
    ACCOUNT_ROLE_SCHEMA_FIELDS,
    SOURCE_PROFILE_SCHEMA_FIELDS,
    STAGE3_ACCOUNT_ROLES,
    STAGE3_CAPABILITIES,
    STAGE3_SOURCE_TYPES,
    RoleAwareLedgerEvent,
    build_custom_source_profile,
    build_stage3_account_roles,
    build_stage3_profile_contract,
    build_stage3_source_profiles,
    compute_consumption_total_cny,
    other_source_template,
    roles_for_account,
)


ROOT = Path(__file__).resolve().parents[1]


class TestV022Stage3SourceAccountProfiles(unittest.TestCase):
    def test_stage3_contract_locks_task_ids_and_scope(self) -> None:
        contract = build_v022_stage3_contract()

        self.assertEqual(contract["stage"], "Stage 3")
        self.assertEqual(contract["task_ids"], V022_STAGE3_TASK_IDS)
        self.assertIn("PFI/src/pfi_v02/stage_v022_source_profile.py", contract["deliverables"])
        self.assertIn("PFI/tests/test_v022_stage3_source_account_profiles.py", contract["deliverables"])
        self.assertIn("不实现 Stage 4 economic_event_id", contract["non_goals"][0])
        for task_id in ("S3-P1-T1", "S3-P1-T2", "S3-P1-T3", "S3-P2-T1", "S3-P2-T2", "S3-P2-T3"):
            self.assertIn(task_id, contract["task_ids"])

    def test_source_profile_schema_supports_required_types_and_capabilities(self) -> None:
        profile_contract = build_stage3_profile_contract()
        profiles = build_stage3_source_profiles()

        self.assertEqual(profile_contract["source_profile_schema_fields"], SOURCE_PROFILE_SCHEMA_FIELDS)
        self.assertEqual(set(STAGE3_SOURCE_TYPES), {"wallet", "bank", "broker", "fund_platform", "bullion_platform", "payment_platform", "manual_snapshot", "other"})
        self.assertEqual(
            set(STAGE3_CAPABILITIES),
            {"cash_ledger", "investment_trade", "fund_trade", "bullion_trade", "balance_snapshot", "fee", "refund", "transfer"},
        )
        self.assertEqual({profile.source_type for profile in profiles}, set(STAGE3_SOURCE_TYPES))
        for profile in profiles:
            with self.subTest(profile=profile.source_id):
                payload = profile.to_dict()
                self.assertTrue(set(SOURCE_PROFILE_SCHEMA_FIELDS).issubset(payload))
                self.assertTrue(profile.role_effective_date_required)
                self.assertTrue(profile.capabilities)
                self.assertTrue(set(profile.capabilities).issubset(STAGE3_CAPABILITIES))

    def test_other_source_template_allows_future_source_without_core_code_change(self) -> None:
        template = other_source_template()
        custom = build_custom_source_profile(
            source_id="new_super_wallet",
            source_label_zh="新增超级钱包",
            source_type="other",
            supported_file_types=("csv", "json"),
            capabilities=("cash_ledger", "refund", "transfer"),
            account_roles_allowed=("main_wallet", "consumption_account"),
        )
        profiles = build_stage3_source_profiles(extra_profiles=(custom,))

        self.assertEqual(template.source_id, "other_source_template")
        self.assertEqual(template.source_type, "other")
        self.assertIn("new_super_wallet", {profile.source_id for profile in profiles})
        self.assertEqual(custom.role_effective_date_required, True)

    def test_account_roles_are_multi_role_and_time_bounded(self) -> None:
        role_contract = build_stage3_profile_contract()
        assignments = build_stage3_account_roles()

        self.assertEqual(role_contract["account_role_schema_fields"], ACCOUNT_ROLE_SCHEMA_FIELDS)
        self.assertTrue(role_contract["multiple_roles_per_account"])
        self.assertEqual(role_contract["unknown_role_policy"], "进入复核队列")
        self.assertTrue(set(role_contract["account_roles"]).issubset(STAGE3_ACCOUNT_ROLES))

        roles = roles_for_account("acct_cba_main", date(2026, 6, 28), assignments)
        self.assertIn("main_wallet", roles)
        self.assertIn("consumption_account", roles)
        self.assertIn("investment_funding_source", roles)
        self.assertIn("income_account", roles)

        old_roles = roles_for_account("acct_alipay_daily", date(2024, 1, 1), assignments)
        current_roles = roles_for_account("acct_alipay_daily", date(2026, 6, 28), assignments)
        self.assertIn("income_account", old_roles)
        self.assertNotIn("income_account", current_roles)
        for assignment in assignments:
            payload = assignment.to_dict()
            self.assertIn("role_effective_from", payload)
            self.assertIn("role_effective_to", payload)

    def test_consumption_calculation_uses_event_flags_and_roles_not_source_names(self) -> None:
        events = (
            RoleAwareLedgerEvent("evt_1", "acct_cba_main", date(2026, 6, 28), "consumption", Decimal("120.00"), True),
            RoleAwareLedgerEvent("evt_2", "acct_moomoo_au", date(2026, 6, 28), "investment_buy", Decimal("900.00"), True),
            RoleAwareLedgerEvent("evt_3", "acct_cba_main", date(2026, 6, 28), "internal_transfer", Decimal("300.00"), False),
        )

        self.assertEqual(compute_consumption_total_cny(events), Decimal("120.00"))
        source = inspect.getsource(compute_consumption_total_cny)
        for forbidden in ("alipay", "wechat", "bank", "cba", "moomoo"):
            self.assertNotIn(forbidden, source.lower())
        self.assertIn("affects_consumption", source)
        self.assertIn("consumption_account", source)

    def test_parameter_catalog_records_stage3_schema(self) -> None:
        catalog = load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        params = catalog["parameters"]

        self.assertEqual(catalog["schema"], "PFIParametersV022Stage13")
        self.assertEqual(catalog["current_stage"], "Stage 13 - 后置触发型复核")
        self.assertEqual(catalog["stage3_task_ids"], list(V022_STAGE3_TASK_IDS))
        self.assertEqual(catalog["stage4_task_ids"], list(V022_STAGE4_TASK_IDS))
        self.assertEqual(params["data_sources"]["source_profile_schema"]["source_types"], list(STAGE3_SOURCE_TYPES))
        self.assertEqual(params["data_sources"]["source_profile_schema"]["capabilities"], list(STAGE3_CAPABILITIES))
        self.assertEqual(params["data_sources"]["other_source_template"]["source_id"], "other_source_template")
        self.assertTrue(params["account_roles"]["account_role_schema"]["multiple_roles_per_account"])
        self.assertTrue(params["account_roles"]["account_role_schema"]["role_effective_date_required"])
        self.assertIn("role_effective_from", params["account_roles"]["account_role_schema"]["required_fields"])
        self.assertIn("role_effective_to", params["account_roles"]["account_role_schema"]["required_fields"])

    def test_human_docs_record_stage3_profile_and_role_gate(self) -> None:
        docs = [
            ROOT / "docs" / "pfi_v022" / "STAGE3_SOURCE_ACCOUNT_PROFILE.md",
            ROOT / "模型参数文件.md",
            ROOT / "功能清单.md",
            ROOT / "开发记录.md",
        ]
        for path in docs:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Stage 3 - 数据源、账户角色与可扩展结构", text)
                self.assertIn("other_source_template", text)
                self.assertIn("role_effective_from", text)
                self.assertIn("role_effective_to", text)
                self.assertIn("S3-P1-T1", text)
                self.assertIn("S3-P2-T3", text)


if __name__ == "__main__":
    unittest.main()
