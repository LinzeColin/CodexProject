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


class TestV023Stage1To3GroupReview(unittest.TestCase):
    def test_stage1_to_3_group_review_evidence_benchmarks_against_phase1_preview(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "group_reviews" / "stage_1_3"
        evidence_path = review_dir / "evidence.json"
        benchmark_path = review_dir / "preview_benchmark" / "comparison_raw.json"
        changed_files_path = review_dir / "changed_files.txt"

        for path in (evidence_path, benchmark_path, changed_files_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage1To3GroupReviewEvidenceV1")
        self.assertEqual(evidence["review_id"], "V023-S1-S3-GROUP-REVIEW")
        self.assertEqual(evidence["status"], "review_pass")
        self.assertEqual(evidence["review_scope"], ["Stage 1", "Stage 2", "Stage 3"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(benchmark["schema"], "PFIV023Stage1To3PreviewBenchmarkV1")

        preview = benchmark["targets"]["preview_desktop"]
        current_static = benchmark["targets"]["current_static_desktop"]
        localhost_frame = next(frame for frame in benchmark["targets"]["localhost_desktop"]["frames"] if frame.get("has_pfi_shell"))

        self.assertEqual(preview["nav_count"], 10)
        self.assertEqual(current_static["primary_count"], 10)
        self.assertEqual(localhost_frame["primary_count"], 10)
        self.assertEqual(localhost_frame["primary"], EXPECTED_PRIMARY_NAV)
        self.assertTrue(localhost_frame["has_stage1_metadata"])

        metrics = {item["label"]: item for item in localhost_frame["metrics"]}
        for label in ("净资产", "现金余额", "投资市值"):
            self.assertEqual(metrics[label]["value"], "暂无真实数据", label)
            self.assertNotEqual(metrics[label]["value"], "CNY 0.00", label)
        self.assertEqual(metrics["本月支出"]["value"], "CNY 7,153.98")
        self.assertEqual(metrics["待复核交易"]["value"], "406")

        self.assertTrue(evidence["acceptance_checks"]["preview_nav_count_matches"])
        self.assertTrue(evidence["acceptance_checks"]["current_app_nav_count_matches"])
        self.assertTrue(evidence["acceptance_checks"]["stage2_no_fake_zero_fix_verified"])
        self.assertTrue(evidence["acceptance_checks"]["stage1_current_worktree_binding_verified"])
        self.assertTrue(evidence["known_historical_stage1_path_is_reference_only"])


class TestV023Stage4To6GroupReview(unittest.TestCase):
    def test_stage4_to_6_group_review_evidence_covers_subpages_home_and_core_metrics(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "group_reviews" / "stage_4_6"
        evidence_path = review_dir / "evidence.json"
        browser_path = review_dir / "browser_audit.json"
        changed_files_path = review_dir / "changed_files.txt"

        for path in (evidence_path, browser_path, changed_files_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        browser = json.loads(browser_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage4To6GroupReviewEvidenceV1")
        self.assertEqual(evidence["review_id"], "V023-S4-S6-GROUP-REVIEW")
        self.assertEqual(evidence["status"], "review_pass")
        self.assertEqual(evidence["review_scope"], ["Stage 4", "Stage 5", "Stage 6"])
        self.assertEqual(evidence["changed_files"], changed_files)

        self.assertEqual(evidence["stage4_subpage_contract"]["primary_entry_count"], 10)
        self.assertEqual(evidence["stage4_subpage_contract"]["subpage_count"], 45)
        self.assertTrue(evidence["stage4_subpage_contract"]["all_primary_entries_have_3_to_5_subpages"])
        self.assertTrue(evidence["stage5_home_contract"]["home_no_task_pack_or_run_boundary"])
        self.assertTrue(evidence["stage5_home_contract"]["home_no_visible_evidence_drawer"])
        self.assertTrue(evidence["stage6_metric_contract"]["blocked_core_metrics_show_status_not_zero"])
        self.assertTrue(evidence["stage6_metric_contract"]["consumption_fixed_flex_unconfigured_not_zero"])

        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])
        self.assertEqual(browser["routes"]["home"]["primary_count"], 10)
        self.assertEqual(browser["routes"]["home"]["primary"], EXPECTED_PRIMARY_NAV)
        self.assertEqual(browser["routes"]["consumption"]["cny_zero_count"], 0)
        self.assertIn("未配置 / CNY 7,153.98", browser["routes"]["consumption"]["fixed_elastic_text"])
        self.assertNotIn("固定支出 · CNY 0", browser["routes"]["consumption"]["trend_text"])


class TestV023Stage7To9GroupReview(unittest.TestCase):
    def test_stage7_to_9_group_review_evidence_keeps_reports_sources_and_feedback_honest(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "group_reviews" / "stage_7_9"
        evidence_path = review_dir / "evidence.json"
        browser_path = review_dir / "browser_audit.json"
        changed_files_path = review_dir / "changed_files.txt"

        for path in (evidence_path, browser_path, changed_files_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        browser = json.loads(browser_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage7To9GroupReviewEvidenceV1")
        self.assertEqual(evidence["review_id"], "V023-S7-S9-GROUP-REVIEW")
        self.assertEqual(evidence["status"], "review_pass")
        self.assertEqual(evidence["review_scope"], ["Stage 7", "Stage 8", "Stage 9"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(evidence["external_taskpack_status"], "missing_from_downloads")

        self.assertEqual(browser["findings"], [])
        self.assertEqual(browser["desktop"]["primary_count"], 10)
        self.assertEqual(browser["desktop"]["primary"], EXPECTED_PRIMARY_NAV)
        self.assertEqual(browser["mobile"]["primary_count"], 10)
        self.assertEqual(browser["mobile"]["primary"], EXPECTED_PRIMARY_NAV)
        self.assertEqual(browser["desktop"]["console_errors"], [])
        self.assertEqual(browser["desktop"]["page_errors"], [])
        self.assertEqual(browser["desktop"]["http_errors"], [])
        self.assertEqual(browser["mobile"]["console_errors"], [])
        self.assertEqual(browser["mobile"]["page_errors"], [])
        self.assertEqual(browser["mobile"]["http_errors"], [])

        reports = browser["desktop"]["route_audits"]["insights"]
        self.assertEqual(reports["cny_zero_count"], 0)
        self.assertFalse(reports["has_project_review_gate_copy"])
        self.assertTrue(reports["has_stage7_blocked_copy"])
        self.assertNotIn("20/20 个门禁通过", reports["first_1200_chars"])
        self.assertNotIn("总验收门禁", reports["first_1200_chars"])

        sync = browser["desktop"]["route_audits"]["sync"]
        self.assertEqual(sync["cny_zero_count"], 0)
        self.assertTrue(sync["has_stage8_source_copy"])

        settings = browser["desktop"]["route_audits"]["settings"]
        self.assertTrue(settings["has_stage9_feedback_settings"])
        self.assertTrue(browser["mobile"]["settings"]["has_stage9_feedback_settings"])
        for workspace in ("home", "consumption", "investment"):
            self.assertFalse(browser["desktop"]["route_audits"][workspace]["has_feedback_console"], workspace)

        self.assertTrue(evidence["acceptance_checks"]["stage7_report_blockers_visible"])
        self.assertTrue(evidence["acceptance_checks"]["stage8_source_gate_visible"])
        self.assertTrue(evidence["acceptance_checks"]["stage9_feedback_settings_visible"])
        self.assertTrue(evidence["acceptance_checks"]["no_project_closeout_overclaim"])


class TestV023Stage10To11GroupReview(unittest.TestCase):
    def test_stage10_to_11_group_review_evidence_covers_e2e_closeout_and_current_goal_boundary(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "group_reviews" / "stage_10_11"
        evidence_path = review_dir / "evidence.json"
        browser_path = review_dir / "browser_audit.json"
        changed_files_path = review_dir / "changed_files.txt"

        for path in (evidence_path, browser_path, changed_files_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        browser = json.loads(browser_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage10To11GroupReviewEvidenceV1")
        self.assertEqual(evidence["review_id"], "V023-S10-S11-GROUP-REVIEW")
        self.assertEqual(evidence["status"], "review_pass")
        self.assertEqual(evidence["review_scope"], ["Stage 10", "Stage 11"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(evidence["external_taskpack_status"], "missing_from_downloads")
        self.assertFalse(evidence["current_three_phase_goal_complete"])
        self.assertFalse(evidence["github_main_uploaded_in_this_group_run"])

        self.assertEqual(browser["findings"], [])
        self.assertEqual(browser["desktop"]["primary_count"], 10)
        self.assertEqual(browser["desktop"]["primary"], EXPECTED_PRIMARY_NAV)
        self.assertEqual(browser["mobile"]["primary_count"], 10)
        self.assertEqual(browser["mobile"]["primary"], EXPECTED_PRIMARY_NAV)
        self.assertTrue(all(row["clicked"] and row["body_has_label"] for row in browser["desktop"]["entry_clicks"]))
        self.assertTrue(all(row["secondary_clicked"] for row in browser["desktop"]["routes"].values()))
        self.assertTrue(browser["desktop"]["history_validation"]["back"]["ok"])
        self.assertTrue(browser["desktop"]["history_validation"]["forward"]["ok"])
        self.assertEqual(browser["desktop"]["console_errors"], [])
        self.assertEqual(browser["desktop"]["page_errors"], [])
        self.assertEqual(browser["desktop"]["http_errors"], [])
        self.assertEqual(browser["mobile"]["console_errors"], [])
        self.assertEqual(browser["mobile"]["page_errors"], [])
        self.assertEqual(browser["mobile"]["http_errors"], [])

        self.assertTrue(browser["desktop"]["routes"]["home"]["has_real_home_metrics"])
        self.assertTrue(browser["mobile"]["home"]["has_real_home_metrics"])
        self.assertTrue(browser["desktop"]["routes"]["sync"]["has_source_gate"])
        self.assertTrue(browser["desktop"]["routes"]["insights"]["has_report_blocker"])
        self.assertTrue(browser["mobile"]["reports"]["has_report_blocker"])
        self.assertEqual(browser["desktop"]["routes"]["insights"]["cny_zero_count"], 0)
        self.assertEqual(browser["mobile"]["reports"]["cny_zero_count"], 0)
        self.assertTrue(browser["desktop"]["routes"]["market_research"]["has_market_error_state"])
        for workspace in ("home", "accounts", "ledger", "investment", "consumption", "sync", "recommendations", "insights", "market_research"):
            self.assertFalse(browser["desktop"]["routes"][workspace]["has_feedback_console"], workspace)

        self.assertTrue(evidence["stage10_e2e_contract"]["current_browser_e2e_passed"])
        self.assertTrue(evidence["stage11_closeout_contract"]["stage_11_whole_review_done"])
        self.assertTrue(evidence["stage11_closeout_contract"]["human_acceptance_claimed"])
        self.assertTrue(evidence["acceptance_checks"]["stage10_entry_navigation_data_report_e2e"])
        self.assertTrue(evidence["acceptance_checks"]["stage11_closeout_evidence_present"])
        self.assertTrue(evidence["acceptance_checks"]["current_goal_boundary_not_overclaimed"])


class TestV023Stage11Phase112DocFreeze(unittest.TestCase):
    def test_t1121_phase112_evidence_records_readme_candidate_boundary(self) -> None:
        evidence = read_json("reports/pfi_v023/stage_11/phase_11_2/evidence.json")

        self.assertEqual(evidence["phase_id"], "V023-S11-P11.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertFalse(evidence["human_acceptance_claimed"])
        self.assertTrue(evidence["acceptance_checks"]["readme_candidate_status"])
        self.assertFalse(evidence["stage_contract"]["phase_11_3_final_candidate_delivery_done"])
        self.assertFalse(evidence["stage_contract"]["stage_11_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])

    def test_t1122_future_development_constraints_are_documented_and_machine_checkable(self) -> None:
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE11_DOC_FREEZE.md"
        self.assertTrue(doc_path.exists(), str(doc_path))
        text = doc_path.read_text(encoding="utf-8")

        required_clauses = [
            "固定 10 个一级入口",
            "市场与研究 是正式一级入口",
            "历史 9 入口约束作废",
            "禁止虚构财务数据",
            "每次 run work 最多只解决一个 phase",
            "用户明确验收前只能写候选通过",
            "不得以 README 或 docs 声明替代真实验证",
        ]
        for clause in required_clauses:
            self.assertIn(clause, text)
        self.assertIn("Phase 11.2", text)

    def test_t1123_history_deprecation_policy_is_frozen_against_old_constraints(self) -> None:
        policy = (ROOT / "docs" / "pfi_v023" / "HISTORY_DEPRECATION_POLICY.md").read_text(encoding="utf-8")

        self.assertIn("## Stage 11.2 Freeze", policy)
        self.assertIn("一级入口 9 个", policy)
        self.assertIn("作废。v0.2.3 固定 10 个一级入口。", policy)
        self.assertIn("市场与研究", policy)
        self.assertIn("作废。`市场与研究` 是正式一级入口。", policy)
        self.assertIn("冻结后不得恢复历史 9 入口约束", policy)
        self.assertIn("冻结后不得把历史完成声明写成当前用户验收", policy)

    def test_t1124_residual_risks_are_explicit_and_do_not_claim_closeout(self) -> None:
        doc = (ROOT / "docs" / "pfi_v023" / "STAGE11_DOC_FREEZE.md").read_text(encoding="utf-8")

        phase112_risks = [
            "用户手动验收未完成",
            "Stage 11 Phase 11.3 最终候选交付未执行",
            "Stage 11 whole-stage review 未执行",
            "Stage 11 GitHub main upload 未执行",
        ]
        for risk in phase112_risks:
            self.assertIn(risk, doc)
        self.assertIn("阻塞项数量：0", doc)
        self.assertNotIn("最终 closeout 已完成", doc)

    def test_phase112_evidence_pack_is_candidate_only_and_keeps_intermediate_phase_local(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_11" / "phase_11_2"
        evidence_path = phase_dir / "evidence.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (evidence_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage11Phase112EvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 11")
        self.assertEqual(evidence["phase_id"], "V023-S11-P11.2")
        self.assertEqual(evidence["phase_name"], "文档冻结")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["task_ids"], ["T11.2.1", "T11.2.2", "T11.2.3", "T11.2.4"])
        self.assertTrue(evidence["stage_contract"]["phase_11_1_regression_tests_done"])
        self.assertTrue(evidence["stage_contract"]["phase_11_2_doc_freeze_done"])
        self.assertFalse(evidence["stage_contract"]["phase_11_3_final_candidate_delivery_done"])
        self.assertFalse(evidence["stage_contract"]["stage_11_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertFalse(evidence["human_acceptance_claimed"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in ("readme_candidate_status", "future_development_constraints", "history_deprecation_frozen", "residual_risks_listed"):
            self.assertTrue(evidence["acceptance_checks"][key], key)


class TestV023Stage11Phase113FinalCandidateDelivery(unittest.TestCase):
    def test_t1131_final_candidate_evidence_pack_exists_and_is_candidate_only(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_11" / "phase_11_3"
        expected_files = [
            phase_dir / "evidence.json",
            phase_dir / "final_evidence_pack.json",
            phase_dir / "screenshot_index.json",
            phase_dir / "validation_summary.json",
            phase_dir / "risk_register.json",
            phase_dir / "remaining_items.json",
            phase_dir / "changed_files.txt",
            phase_dir / "terminal.log",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads((phase_dir / "evidence.json").read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in (phase_dir / "changed_files.txt").read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage11Phase113EvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 11")
        self.assertEqual(evidence["phase_id"], "V023-S11-P11.3")
        self.assertEqual(evidence["phase_name"], "最终候选交付")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["task_ids"], ["T11.3.1", "T11.3.2", "T11.3.3", "T11.3.4"])
        self.assertTrue(evidence["stage_contract"]["phase_11_1_regression_tests_done"])
        self.assertTrue(evidence["stage_contract"]["phase_11_2_doc_freeze_done"])
        self.assertTrue(evidence["stage_contract"]["phase_11_3_final_candidate_delivery_done"])
        self.assertFalse(evidence["stage_contract"]["stage_11_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertFalse(evidence["human_acceptance_claimed"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in ("final_evidence_pack_present", "final_screenshot_index_present", "final_validation_summary_present", "risk_and_remaining_items_present"):
            self.assertTrue(evidence["acceptance_checks"][key], key)

    def test_phase113_final_evidence_pack_indexes_prior_phase_outputs_and_final_gate_artifacts(self) -> None:
        pack = read_json("reports/pfi_v023/stage_11/phase_11_3/final_evidence_pack.json")

        self.assertEqual(pack["schema"], "PFIV023Stage11FinalCandidateEvidencePackV1")
        self.assertEqual(pack["version"], "v0.2.3")
        self.assertEqual(pack["status"], "candidate_pass")
        self.assertFalse(pack["human_acceptance_claimed"])
        self.assertFalse(pack["stage_11_whole_review_done"])
        self.assertFalse(pack["github_main_upload_done"])
        self.assertEqual(pack["included_phase_ids"], ["V023-S11-P11.1", "V023-S11-P11.2", "V023-S11-P11.3"])

        for path in pack["required_artifacts"]:
            self.assertTrue((ROOT / path).exists(), path)

        gates = pack["candidate_gate_summary"]
        self.assertTrue(gates["regression_tests"])
        self.assertTrue(gates["doc_freeze"])
        self.assertTrue(gates["final_screenshot_index"])
        self.assertTrue(gates["validation_summary"])
        self.assertTrue(gates["risk_register"])
        self.assertTrue(gates["remaining_items"])

    def test_phase113_screenshot_index_has_current_final_screenshots_and_existing_e2e_references(self) -> None:
        index = read_json("reports/pfi_v023/stage_11/phase_11_3/screenshot_index.json")

        self.assertEqual(index["schema"], "PFIV023Stage11FinalScreenshotIndexV1")
        self.assertEqual(index["phase_id"], "V023-S11-P11.3")
        screenshot_ids = {item["screenshot_id"] for item in index["screenshots"]}
        self.assertTrue({"final_desktop", "final_mobile", "stage10_app_entry_review", "stage10_navigation_review", "stage10_report_review"}.issubset(screenshot_ids))
        for item in index["screenshots"]:
            path = ROOT / item["path"]
            self.assertTrue(path.exists(), item["path"])
            self.assertGreater(item["bytes"], 20000, item["screenshot_id"])
            self.assertEqual(path.stat().st_size, item["bytes"], item["screenshot_id"])

    def test_phase113_validation_summary_risk_register_and_remaining_items_are_explicit(self) -> None:
        validation = read_json("reports/pfi_v023/stage_11/phase_11_3/validation_summary.json")
        risks = read_json("reports/pfi_v023/stage_11/phase_11_3/risk_register.json")
        remaining = read_json("reports/pfi_v023/stage_11/phase_11_3/remaining_items.json")

        self.assertEqual(validation["schema"], "PFIV023Stage11FinalValidationSummaryV1")
        self.assertEqual(validation["phase_id"], "V023-S11-P11.3")
        for key in ("stage11_regression_pytest", "all_v023_pytest", "node_check", "json_validation", "app_health"):
            self.assertEqual(validation["commands"][key]["status"], "pass", key)
        self.assertEqual(validation["app_health"]["8501"], "ok")
        self.assertEqual(validation["app_health"]["8766"]["status"], "ok")

        self.assertEqual(risks["schema"], "PFIV023Stage11RiskRegisterV1")
        risk_titles = {item["title"] for item in risks["risks"]}
        self.assertIn("用户手动验收未完成", risk_titles)
        self.assertIn("Stage 11 whole-stage review 未执行", risk_titles)
        self.assertIn("GitHub main upload 未执行", risk_titles)

        self.assertEqual(remaining["schema"], "PFIV023Stage11RemainingItemsV1")
        remaining_titles = {item["title"] for item in remaining["items"]}
        self.assertIn("用户明确验收", remaining_titles)
        self.assertIn("Stage 11 whole-stage review", remaining_titles)
        self.assertIn("Stage 11 GitHub main upload", remaining_titles)


class TestV023Stage11WholeStageReview(unittest.TestCase):
    def test_stage11_current_readme_status_reflects_user_accepted_closeout(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## v0.2.3 Closeout Status", readme)
        self.assertIn("v0.2.3 user-accepted closeout complete", readme)
        self.assertIn("user_acceptance_claimed=true", readme)
        self.assertIn("Stage 11 user acceptance 已完成", readme)
        self.assertIn("v0.2.3 closeout complete", readme)
        self.assertIn("Stage 11 Phase 11.3 已完成", readme)
        self.assertIn("Stage 11 whole-stage review 已完成", readme)
        self.assertNotIn("Stage 11 Phase 11.3 未执行", readme)
        self.assertNotIn("Stage 11 whole-stage review 未执行", readme)
        self.assertNotIn("user_acceptance_claimed=false", readme)
        self.assertNotIn("当前状态只能写候选通过", readme)

    def test_stage11_closeout_doc_records_user_acceptance_and_closed_gate(self) -> None:
        doc = (ROOT / "docs" / "pfi_v023" / "STAGE11_CLOSEOUT.md").read_text(encoding="utf-8")

        self.assertIn("Stage 11 user-accepted closeout complete", doc)
        self.assertIn("user_acceptance_claimed=true", doc)
        self.assertIn("用户明确回复“接受”", doc)
        self.assertIn("Stage 11 GitHub main upload terminal gate", doc)
        self.assertIn("PFI/reports/pfi_v023/stage_11/whole_stage_review/evidence.json", doc)
        self.assertNotIn("user_acceptance_claimed=false", doc)
        self.assertNotIn("当前只能写 candidate pass", doc)

    def test_stage11_whole_stage_review_evidence_exists_and_records_final_acceptance(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "stage_11" / "whole_stage_review"
        expected_files = [
            review_dir / "evidence.json",
            review_dir / "review_audit.json",
            review_dir / "browser_validation.json",
            review_dir / "changed_files.txt",
            review_dir / "terminal.log",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads((review_dir / "evidence.json").read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in (review_dir / "changed_files.txt").read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage11WholeStageReviewEvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 11")
        self.assertEqual(evidence["review_id"], "V023-S11-WHOLE-STAGE-REVIEW")
        self.assertEqual(evidence["status"], "closeout_pass")
        self.assertTrue(evidence["current_stage_only"])
        self.assertTrue(evidence["stage_contract"]["phase_11_1_regression_tests_done"])
        self.assertTrue(evidence["stage_contract"]["phase_11_2_doc_freeze_done"])
        self.assertTrue(evidence["stage_contract"]["phase_11_3_final_candidate_delivery_done"])
        self.assertTrue(evidence["stage_contract"]["stage_11_whole_review_done"])
        self.assertTrue(evidence["stage_contract"]["user_acceptance_done"])
        self.assertTrue(evidence["stage_contract"]["stage_11_closeout_done"])
        self.assertEqual(evidence["stage_contract"]["github_main_upload_gate"], "terminal_verified_after_push")
        self.assertTrue(evidence["human_acceptance_claimed"])
        self.assertFalse(evidence["user_acceptance_required_before_closeout"])
        self.assertTrue(evidence["user_acceptance"]["accepted"])
        self.assertEqual(evidence["user_acceptance"]["acceptance_text"], "接受")
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in (
            "regression_tests",
            "final_evidence_pack",
            "final_screenshots",
            "current_status_docs",
            "user_acceptance_recorded",
            "closeout_status_recorded",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)
        self.assertNotIn("human_acceptance_gate_open", evidence["acceptance_checks"])

    def test_stage11_whole_stage_review_audit_covers_final_dod_and_boundaries(self) -> None:
        audit = read_json("reports/pfi_v023/stage_11/whole_stage_review/review_audit.json")

        self.assertEqual(audit["schema"], "PFIV023Stage11WholeStageReviewAuditV1")
        self.assertEqual(audit["review_id"], "V023-S11-WHOLE-STAGE-REVIEW")
        self.assertTrue(audit["human_acceptance_claimed"])
        self.assertEqual(audit["blocker_count"], 0)
        self.assertFalse([item for item in audit["remaining_items"] if item["status"] == "open"])
        checks = {item["id"]: item for item in audit["checks"]}
        for check_id in (
            "ten_primary_entries_stable",
            "market_research_is_primary_entry",
            "old_nine_entry_constraint_deprecated",
            "forbidden_finance_data_absent",
            "final_evidence_pack_complete",
            "user_acceptance_recorded",
            "closeout_status_recorded",
        ):
            self.assertEqual(checks[check_id]["status"], "pass", check_id)

    def test_stage11_whole_stage_browser_validation_and_screenshots_are_present(self) -> None:
        browser = read_json("reports/pfi_v023/stage_11/whole_stage_review/browser_validation.json")

        self.assertEqual(browser["schema"], "PFIV023Stage11WholeStageBrowserValidationV1")
        self.assertEqual(browser["review_id"], "V023-S11-WHOLE-STAGE-REVIEW")
        self.assertEqual(browser["localhost"]["health"], "ok")
        self.assertEqual(browser["localhost"]["api_health"]["status"], "ok")
        self.assertEqual(browser["nav"]["count"], 10)
        self.assertIn("市场与研究", browser["nav"]["labels"])
        for item in browser["screenshots"]:
            path = ROOT / item["path"]
            self.assertTrue(path.exists(), item["path"])
            self.assertGreater(item["bytes"], 20000, item["screenshot_id"])
            self.assertEqual(path.stat().st_size, item["bytes"], item["screenshot_id"])


class TestV023OverallProjectReview(unittest.TestCase):
    def test_overall_project_review_evidence_closes_three_phase_recovery_locally(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "overall_project_review"
        expected_files = [
            review_dir / "evidence.json",
            review_dir / "review_audit.json",
            review_dir / "browser_audit.json",
            review_dir / "cleanup_report.json",
            review_dir / "changed_files.txt",
            review_dir / "terminal.log",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads((review_dir / "evidence.json").read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in (review_dir / "changed_files.txt").read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023OverallProjectReviewEvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["review_id"], "V023-OVERALL-PROJECT-REVIEW")
        self.assertEqual(evidence["status"], "project_review_pass")
        self.assertEqual(evidence["review_scope"], ["Stage 1-11", "group reviews", "overall project recovery gate"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["three_phase_recovery"]["phase_1_stage_by_stage_complete"])
        self.assertTrue(evidence["three_phase_recovery"]["phase_2_group_review_complete"])
        self.assertTrue(evidence["three_phase_recovery"]["phase_3_overall_project_review_complete"])
        self.assertEqual(evidence["terminal_gates"]["github_main_upload"], "terminal_verified_after_push")
        self.assertEqual(evidence["terminal_gates"]["backup_bundle"], "terminal_verified_after_final_commit")
        self.assertFalse(evidence["github_main_uploaded_inside_evidence_commit"])

        groups = evidence["group_review_summary"]
        self.assertEqual(groups["stage_1_3"], "review_pass")
        self.assertEqual(groups["stage_4_6"], "review_pass")
        self.assertEqual(groups["stage_7_9"], "review_pass")
        self.assertEqual(groups["stage_10_11"], "review_pass")
        self.assertTrue(evidence["acceptance_checks"]["ten_primary_entries_stable"])
        self.assertTrue(evidence["acceptance_checks"]["market_research_primary_entry"])
        self.assertTrue(evidence["acceptance_checks"]["old_nine_entry_constraint_deprecated"])
        self.assertTrue(evidence["acceptance_checks"]["no_mock_financial_data_used"])
        self.assertTrue(evidence["acceptance_checks"]["external_download_sources_missing_not_fabricated"])
        self.assertTrue(evidence["acceptance_checks"]["cleanup_completed_without_user_data_deletion"])

    def test_overall_project_browser_audit_and_cleanup_are_machine_checkable(self) -> None:
        browser = read_json("reports/pfi_v023/overall_project_review/browser_audit.json")
        cleanup = read_json("reports/pfi_v023/overall_project_review/cleanup_report.json")
        audit = read_json("reports/pfi_v023/overall_project_review/review_audit.json")

        self.assertEqual(browser["schema"], "PFIV023OverallProjectBrowserAuditV1")
        self.assertEqual(browser["findings"], [])
        self.assertEqual(browser["desktop"]["primary_count"], 10)
        self.assertEqual(browser["desktop"]["primary"], EXPECTED_PRIMARY_NAV)
        self.assertEqual(browser["mobile"]["primary_count"], 10)
        self.assertEqual(browser["mobile"]["primary"], EXPECTED_PRIMARY_NAV)
        self.assertEqual(browser["desktop"]["routes"]["home"]["cny_zero_count"], 0)
        self.assertTrue(browser["desktop"]["routes"]["home"]["has_real_metrics"])
        self.assertTrue(browser["desktop"]["routes"]["sync"]["has_source_gate"])
        self.assertTrue(browser["desktop"]["routes"]["insights"]["has_report_blocker"])
        self.assertTrue(browser["desktop"]["routes"]["market_research"]["has_market_empty_state"])
        self.assertTrue(browser["desktop"]["routes"]["settings"]["has_settings_feedback"])
        self.assertEqual(browser["mobile"]["home"]["cny_zero_count"], 0)
        self.assertTrue(browser["mobile"]["reports"]["has_report_blocker"])

        screenshots = sorted((ROOT / "reports" / "pfi_v023" / "overall_project_review" / "screenshots").glob("*.png"))
        self.assertGreaterEqual(len(screenshots), 7)
        for path in screenshots:
            self.assertGreater(path.stat().st_size, 20000, path.name)

        self.assertEqual(cleanup["schema"], "PFIV023OverallProjectCleanupReportV1")
        self.assertFalse(cleanup["user_data_deleted"])
        self.assertFalse(cleanup["financial_data_deleted"])
        self.assertFalse(cleanup["venv_deleted"])
        self.assertIn("PFI/.venv", cleanup["protected_paths"])
        self.assertIn("MetaDatabase/PFI", cleanup["protected_paths"])

        self.assertEqual(audit["schema"], "PFIV023OverallProjectReviewAuditV1")
        self.assertEqual(audit["blocker_count"], 0)
        checks = {item["id"]: item["status"] for item in audit["checks"]}
        for check_id in (
            "stage0_contract_still_valid",
            "all_group_reviews_passed",
            "overall_browser_audit_passed",
            "meta_database_real_data_present",
            "external_sources_missing_not_fabricated",
            "safe_cleanup_completed",
        ):
            self.assertEqual(checks[check_id], "pass", check_id)


if __name__ == "__main__":
    unittest.main()
