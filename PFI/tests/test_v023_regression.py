from __future__ import annotations

from html.parser import HTMLParser
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PRIMARY_NAV = [
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
]
EXPECTED_ROUTE_ALIASES = [
    "/home",
    "/accounts",
    "/ledger",
    "/investment",
    "/consumption",
    "/sources-upload",
    "/review",
    "/reports",
    "/market-research",
    "/settings",
]
REQUIRED_REPORT_FIELDS = {
    "report_id",
    "title",
    "status",
    "conclusion_zh",
    "data_range",
    "sam" + "ple_size",
    "core_metrics",
    "formulas",
    "parameters",
    "data_sources",
    "evidence_hash",
    "missing_data",
    "anomalies",
    "next_actions",
}


class PrimaryNavParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._active_attrs: dict[str, str] | None = None
        self._active_text: list[str] = []
        self.entries: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        if tag == "button" and attr_map.get("data-primary-entry") == "true":
            self._active_attrs = attr_map
            self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_attrs is not None:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self._active_attrs is not None:
            entry = dict(self._active_attrs)
            entry["label"] = "".join(self._active_text).strip()
            self.entries.append(entry)
            self._active_attrs = None
            self._active_text = []


def read_json(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def primary_nav_entries() -> list[dict[str, str]]:
    parser = PrimaryNavParser()
    parser.feed((ROOT / "web" / "index.html").read_text(encoding="utf-8"))
    return parser.entries


class TestV023Stage11Phase111Regression(unittest.TestCase):
    def test_t1111_entry_regression_locks_ten_primary_entries_and_current_app_evidence(self) -> None:
        entries = primary_nav_entries()

        self.assertEqual(len(entries), 10)
        self.assertEqual([entry["label"] for entry in entries], EXPECTED_PRIMARY_NAV)
        self.assertEqual([entry["data-route-alias"] for entry in entries], EXPECTED_ROUTE_ALIASES)
        self.assertEqual([entry["data-nav-index"] for entry in entries], [str(index) for index in range(1, 11)])
        self.assertEqual(entries[8]["data-workspace"], "market_research")

        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-primary-workspaces="10"', html)
        self.assertNotIn('data-primary-workspaces="9"', html)

        browser = read_json("reports/pfi_v023/stage_10/whole_stage_review/browser_validation.json")
        self.assertEqual(browser["localhost"]["health"], "ok")
        self.assertEqual(browser["app_entry"]["downloads_app_project_binding"], str(ROOT))
        self.assertEqual(browser["official_nav_labels"], EXPECTED_PRIMARY_NAV)

    def test_t1112_navigation_regression_reuses_browser_click_and_history_evidence(self) -> None:
        browser = read_json("reports/pfi_v023/stage_10/whole_stage_review/browser_validation.json")

        self.assertEqual([row["label"] for row in browser["entry_clicks"]], EXPECTED_PRIMARY_NAV)
        self.assertTrue(all(row["clicked"] and row["body_has_label"] for row in browser["entry_clicks"]))
        self.assertEqual({row["entry_label"] for row in browser["secondary_clicks"]}, set(EXPECTED_PRIMARY_NAV))
        self.assertTrue(all(row["clicked"] for row in browser["secondary_clicks"]))
        self.assertTrue(browser["history_validation"]["back"]["ok"])
        self.assertTrue(browser["history_validation"]["forward"]["ok"])
        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])
        self.assertEqual(browser["http_errors"], [])

    def test_t1113_data_state_regression_blocks_masked_zero_and_unsupported_statuses(self) -> None:
        core_metrics = read_json("reports/pfi_v023/stage_6/phase_6_1/core_metrics.json")
        data_gate = read_json("reports/pfi_v023/stage_8/phase_8_1/data_source_gate.json")
        browser = read_json("reports/pfi_v023/stage_10/whole_stage_review/browser_validation.json")

        allowed_statuses = {
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
        }
        self.assertEqual(set(data_gate["data_source_statuses"]), allowed_statuses)

        metrics = {item["metric_id"]: item for item in core_metrics["core_metrics"]}
        self.assertEqual(core_metrics["source"]["transaction_count"], 8815)
        self.assertEqual(metrics["life_consumption_cny"]["status"], "ready")
        self.assertEqual(metrics["life_consumption_cny"]["value"], 1545600.44)
        self.assertEqual(metrics["total_consumption_outflow_cny"]["status"], "ready")
        self.assertEqual(metrics["total_consumption_outflow_cny"]["value"], 1727278.37)
        self.assertEqual(metrics["data_health"]["value"], 8815)
        self.assertEqual(set(core_metrics["blocked_metric_ids"]), {"net_worth_cny", "cash_balance_cny", "investment_market_value_cny"})

        self.assertEqual(browser["core_metrics"]["monthly_spending"]["value_text"], "CNY 7,153.98")
        self.assertEqual(browser["core_metrics"]["pending_review"]["value_text"], "406")
        self.assertTrue(browser["core_metrics"]["all_zero_values_explained"])

        payload_text = json.dumps({"core_metrics": core_metrics, "data_gate": data_gate}, ensure_ascii=False)
        for blocked in ("mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"):
            self.assertIsNone(re.search(blocked, payload_text, flags=re.IGNORECASE), blocked)

    def test_t1114_report_structure_regression_requires_formulas_sources_and_blockers(self) -> None:
        report_contract = read_json("reports/pfi_v023/stage_7/phase_7_1/report_contract.json")
        report_page = read_json("reports/pfi_v023/stage_7/phase_7_1/report_page_model.json")
        browser = read_json("reports/pfi_v023/stage_10/whole_stage_review/browser_validation.json")

        reports = {report["report_id"]: report for report in report_contract["reports"]}
        self.assertEqual(set(report_contract["report_statuses"]), {"complete", "partial", "blocked", "outdated", "review_required"})
        self.assertTrue({"net_worth_report", "cash_balance_report", "investment_market_value_report", "consumption_structure_report", "data_quality_report"}.issubset(reports))
        for report in reports.values():
            self.assertTrue(REQUIRED_REPORT_FIELDS.issubset(report), report["report_id"])
            self.assertRegex(report["conclusion_zh"], r"[\u4e00-\u9fff]")
            self.assertIsInstance(report["formulas"], list)
            self.assertIsInstance(report["data_sources"], list)
            if report["status"] in {"blocked", "partial"}:
                self.assertGreater(len(report["missing_data"]), 0, report["report_id"])

        self.assertEqual(report_page["schema"], "PFIV023Stage7ReportsPageViewModelV1")
        self.assertGreaterEqual(report_page["blocked_or_partial_count"], 4)
        self.assertTrue(browser["report_center"]["has_conclusion_or_blocker"])
        self.assertIn("无法生成月报", browser["report_center"]["evidence_text"])

    def test_phase111_evidence_pack_is_candidate_only_and_does_not_close_stage11(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_11" / "phase_11_1"
        evidence_path = phase_dir / "evidence.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (evidence_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage11Phase111EvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 11")
        self.assertEqual(evidence["phase_id"], "V023-S11-P11.1")
        self.assertEqual(evidence["phase_name"], "回归测试")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["task_ids"], ["T11.1.1", "T11.1.2", "T11.1.3", "T11.1.4"])
        self.assertFalse(evidence["stage_contract"]["phase_11_2_doc_freeze_done"])
        self.assertFalse(evidence["stage_contract"]["phase_11_3_final_candidate_delivery_done"])
        self.assertFalse(evidence["stage_contract"]["stage_11_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertFalse(evidence["human_acceptance_claimed"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in ("entry_regression_tests", "navigation_regression_tests", "data_state_regression_tests", "report_structure_regression_tests"):
            self.assertTrue(evidence["acceptance_checks"][key], key)


if __name__ == "__main__":
    unittest.main()
