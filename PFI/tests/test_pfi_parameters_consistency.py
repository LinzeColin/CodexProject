from __future__ import annotations

import re
import unittest
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import BASE_CURRENCY
from pfi_v02.stage_v022_database_governance import (
    V022_STAGE1_REQUIRED_PARAMETER_DOMAINS,
    V022_STAGE1_TASK_IDS,
    V022_STAGE3_TASK_IDS,
    V022_STAGE4_TASK_IDS,
    V022_STAGE6_TASK_IDS,
    V022_STAGE7_TASK_IDS,
    V022_STAGE8_TASK_IDS,
    V022_STAGE9_TASK_IDS,
    V022_STAGE10_TASK_IDS,
    V022_STAGE11_TASK_IDS,
    V022_STAGE12_TASK_IDS,
    V022_STAGE13_TASK_IDS,
    build_v022_stage1_contract,
    load_v022_parameter_catalog,
)


ROOT = Path(__file__).resolve().parents[1]


class TestPFIParametersConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        cls.parameter_text = (ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        cls.index_html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        cls.changelog_text = (ROOT / "config" / "parameter_changelog.md").read_text(encoding="utf-8")

    def test_stage1_contract_matches_roadmap_tasks(self) -> None:
        contract = build_v022_stage1_contract()

        self.assertEqual(contract["stage"], "Stage 1")
        self.assertEqual(contract["task_ids"], V022_STAGE1_TASK_IDS)
        self.assertIn("PFI/config/pfi_parameters.yaml", contract["deliverables"])
        self.assertIn("PFI/tests/test_pfi_parameters_consistency.py", contract["deliverables"])
        self.assertEqual(contract["machine_readable_parameter_file"]["path"], "PFI/config/pfi_parameters.yaml")
        self.assertIn("JSON-compatible YAML", contract["machine_readable_parameter_file"]["format"])

    def test_machine_readable_catalog_has_chinese_domain_directory(self) -> None:
        self.assertEqual(self.catalog["schema"], "PFIParametersV022Stage13")
        self.assertEqual(self.catalog["current_stage"], "Stage 13 - 后置触发型复核")
        self.assertEqual(self.catalog["parameter_version"], "v0.2.2")
        self.assertEqual(self.catalog["stage1_task_ids"], list(V022_STAGE1_TASK_IDS))
        self.assertEqual(
            self.catalog["stage2_task_ids"],
            ["S2-P1-T1", "S2-P1-T2", "S2-P1-T3", "S2-P2-T1", "S2-P2-T2", "S2-P2-T3"],
        )
        self.assertEqual(self.catalog["stage3_task_ids"], list(V022_STAGE3_TASK_IDS))
        self.assertEqual(self.catalog["stage4_task_ids"], list(V022_STAGE4_TASK_IDS))
        self.assertEqual(
            self.catalog["stage5_task_ids"],
            ["S5-P1-T1", "S5-P1-T2", "S5-P2-T1", "S5-P2-T2", "S5-P2-T3", "S5-P3-T1", "S5-P3-T2", "S5-P3-T3", "S5-P3-T4"],
        )
        self.assertEqual(self.catalog["stage6_task_ids"], list(V022_STAGE6_TASK_IDS))
        self.assertEqual(self.catalog["stage7_task_ids"], list(V022_STAGE7_TASK_IDS))
        self.assertEqual(self.catalog["stage8_task_ids"], list(V022_STAGE8_TASK_IDS))
        self.assertEqual(self.catalog["stage9_task_ids"], list(V022_STAGE9_TASK_IDS))
        self.assertEqual(self.catalog["stage10_task_ids"], list(V022_STAGE10_TASK_IDS))
        self.assertEqual(self.catalog["stage11_task_ids"], list(V022_STAGE11_TASK_IDS))
        self.assertEqual(self.catalog["stage12_task_ids"], list(V022_STAGE12_TASK_IDS))
        self.assertEqual(self.catalog["stage13_task_ids"], list(V022_STAGE13_TASK_IDS))

        domains = {item["key"]: item for item in self.catalog["domains"]}
        self.assertEqual(set(domains), set(V022_STAGE1_REQUIRED_PARAMETER_DOMAINS))
        for key, item in domains.items():
            with self.subTest(domain=key):
                self.assertRegex(item["label_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(item["description_zh"], r"[\u4e00-\u9fff]")
                self.assertIn(item["label_zh"], self.parameter_text)

    def test_markdown_and_yaml_core_parameters_are_consistent(self) -> None:
        params = self.catalog["parameters"]

        self.assertEqual(params["currency"]["base_currency"]["value"], BASE_CURRENCY)
        self.assertEqual(params["currency"]["base_currency"]["value"], "CNY")
        self.assertEqual(params["currency"]["frontend_fx_badge_pair"]["value"], "AUD/CNY")
        self.assertEqual(params["fx"]["frontend_badge_format"]["value"], "AUD/CNY=4.69（YYYY/MM/DD HH:MM）")
        self.assertEqual(params["fx"]["snapshot_time_local"]["value"], "06:00")
        self.assertFalse(params["fx"]["default_network_refresh"]["value"])
        self.assertTrue(params["fx"]["explicit_refresh_requires_allow_network"]["value"])

        for expected in ("base_currency | `CNY`", "fx_badge_pair | `AUD/CNY`", "fx_badge_format | `AUD/CNY=4.69"):
            self.assertIn(expected, self.parameter_text)
        self.assertIn("每次运行默认联网 | `false`", self.parameter_text)

    def test_frontend_display_values_stay_consistent_with_stage1_catalog(self) -> None:
        params = self.catalog["parameters"]
        pair = params["currency"]["frontend_fx_badge_pair"]["value"]
        rate = params["fx"]["frontend_badge_example_rate"]["value"]
        snapshot_time = params["fx"]["snapshot_time_local"]["value"]

        self.assertIn(f"{pair}={rate:.2f}", self.index_html)
        self.assertIn(snapshot_time, self.index_html)
        self.assertRegex(self.index_html, re.compile(r"AUD/CNY=4\.69（\d{4}/\d{2}/\d{2} 06:00）"))
        self.assertIn('data-fx-cache-state="cached"', self.index_html)
        self.assertEqual(params["fx"]["stage2_target_pair"]["value"], "AUD/CNY")
        self.assertEqual(params["fx"]["stage2_target_pair"]["value"], pair)

    def test_formulas_have_chinese_explanations_and_aliases(self) -> None:
        required_fields = {"formula_id", "name_zh", "purpose_zh", "inputs", "outputs", "logic_zh", "example_zh", "variable_aliases"}
        formulas = self.catalog["formulas"]

        self.assertGreaterEqual(len(formulas), 7)
        for formula in formulas:
            with self.subTest(formula=formula["formula_id"]):
                self.assertTrue(required_fields.issubset(formula))
                self.assertRegex(formula["name_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(formula["purpose_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(formula["logic_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(formula["example_zh"], r"[\u4e00-\u9fff]")
                self.assertTrue(formula["inputs"])
                self.assertTrue(formula["outputs"])
                self.assertTrue(formula["variable_aliases"])
                self.assertIn(formula["formula_id"], self.parameter_text)
                for alias in formula["variable_aliases"].values():
                    self.assertRegex(alias, r"[\u4e00-\u9fff]")

    def test_thresholds_have_required_explanation_fields(self) -> None:
        thresholds = {item["key"]: item for item in self.catalog["threshold_index"]}
        required = {
            "confidence.review_threshold": "70 分",
            "consumption_model.large_spend_cny_threshold": "CNY 2000",
            "consumption_model.large_spend_aud_original_threshold": "AUD 500",
            "time.night_window": "22:00-06:00",
            "time.cashflow_windows_days": "7/21/30/60/90/180/360 天",
            "investment_model.concentration_watch_threshold_pct": "35%",
            "investment_model.concentration_high_risk_threshold_pct": "50%",
        }

        for key, value in required.items():
            with self.subTest(threshold=key):
                self.assertIn(key, thresholds)
                self.assertEqual(thresholds[key]["current_value"], value)
                self.assertRegex(thresholds[key]["why_zh"], r"[\u4e00-\u9fff]")
                self.assertTrue(thresholds[key]["impact_surfaces"])
                self.assertIn("user_editable", thresholds[key])
                self.assertIn(key, self.parameter_text)

    def test_variable_dictionary_exposes_user_readable_aliases(self) -> None:
        aliases = {}
        for formula in self.catalog["formulas"]:
            aliases.update(formula["variable_aliases"])

        self.assertEqual(aliases["gross_consumption_cny"], "消费总流出金额")
        self.assertEqual(aliases["living_consumption_cny"], "生活消费金额")
        self.assertEqual(aliases["confidence_score"], "置信度评分")
        self.assertEqual(aliases["future_cash_balance"], "未来现金余额")
        self.assertIn("gross_consumption_cny = 消费总流出金额", self.parameter_text)
        self.assertIn("future_cash_balance = 未来现金余额", self.parameter_text)

    def test_parameter_changelog_records_stage1_changes(self) -> None:
        for task_id in V022_STAGE1_TASK_IDS:
            self.assertIn(task_id, self.changelog_text)
        self.assertIn("PFI/config/pfi_parameters.yaml", self.changelog_text)
        self.assertIn("字段中文说明", self.changelog_text)
        self.assertIn("Markdown/YAML/前端显示", self.changelog_text)


if __name__ == "__main__":
    unittest.main()
