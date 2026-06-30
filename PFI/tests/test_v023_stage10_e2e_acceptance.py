from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV023Stage10E2EAcceptance(unittest.TestCase):
    def test_phase101_evidence_pack_exists_and_is_limited_to_entry_e2e(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_10" / "phase_10_1"
        evidence_path = phase_dir / "evidence.json"
        browser_validation_path = phase_dir / "browser_validation.json"
        build_hash_path = phase_dir / "build_hash_consistency.json"
        cache_cleanup_path = phase_dir / "cache_cleanup_dry_run.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE10_E2E_ACCEPTANCE.md"

        for path in (
            evidence_path,
            browser_validation_path,
            build_hash_path,
            cache_cleanup_path,
            changed_files_path,
            terminal_log_path,
            doc_path,
        ):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage10Phase101EvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 10")
        self.assertEqual(evidence["phase_id"], "V023-S10-P10.1")
        self.assertEqual(evidence["phase_name"], "入口 E2E")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["task_ids"], ["T10.1.1", "T10.1.2", "T10.1.3", "T10.1.4"])
        self.assertFalse(evidence["stage_contract"]["phase_10_2_navigation_e2e_done"])
        self.assertFalse(evidence["stage_contract"]["phase_10_3_data_report_e2e_done"])
        self.assertFalse(evidence["stage_contract"]["stage_10_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in (
            "downloads_app_entry_bound_to_current_checkout",
            "app_entry_screenshot_exists",
            "localhost_screenshot_exists",
            "build_hash_consistency",
            "cache_cleanup_dry_run_safe",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)

    def test_phase101_browser_validation_proves_app_and_localhost_entry(self) -> None:
        payload = json.loads(
            (ROOT / "reports" / "pfi_v023" / "stage_10" / "phase_10_1" / "browser_validation.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(payload["schema"], "PFIV023Stage10Phase101BrowserValidationV1")
        self.assertEqual(payload["phase_id"], "V023-S10-P10.1")
        self.assertEqual(payload["localhost"]["url"], "http://127.0.0.1:8501")
        self.assertEqual(payload["localhost"]["health"], "ok")
        self.assertIn("pfi_app_version=0.2.3", payload["app_entry"]["url"])
        self.assertEqual(payload["app_entry"]["downloads_app_project_binding"], str(ROOT))
        self.assertTrue(payload["app_entry"]["dry_run_exit_code"] == 0)
        self.assertEqual(payload["screenshots"]["app_entry"]["width"], 1440)
        self.assertEqual(payload["screenshots"]["localhost"]["width"], 1440)
        self.assertGreater(payload["screenshots"]["app_entry"]["bytes"], 20000)
        self.assertGreater(payload["screenshots"]["localhost"]["bytes"], 20000)
        self.assertEqual(payload["official_nav_count"], 10)
        self.assertEqual(payload["console_errors"], [])
        self.assertEqual(payload["page_errors"], [])

    def test_phase101_build_hashes_match_current_checkout_and_runtime_metadata(self) -> None:
        payload = json.loads(
            (
                ROOT
                / "reports"
                / "pfi_v023"
                / "stage_10"
                / "phase_10_1"
                / "build_hash_consistency.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(payload["schema"], "PFIV023Stage10Phase101BuildHashConsistencyV1")
        self.assertEqual(payload["phase_id"], "V023-S10-P10.1")
        self.assertEqual(payload["runtime_metadata"]["pfiVersion"], "v0.2.3")
        self.assertEqual(payload["runtime_metadata"]["appVersion"], "0.2.3")
        self.assertRegex(payload["runtime_metadata"]["webBundleHash"], r"^[0-9a-f]{64}$")
        self.assertEqual(payload["runtime_metadata"]["webBundleHash"], payload["disk_manifest"]["web_bundle_hash"])
        self.assertEqual(payload["runtime_metadata"]["webIndexSha256"], payload["disk_manifest"]["files"]["web/index.html"])
        self.assertEqual(payload["runtime_metadata"]["shellJsSha256"], payload["disk_manifest"]["files"]["web/app/shell.js"])
        self.assertTrue(payload["all_hashes_match"])

    def test_phase101_cache_cleanup_is_dry_run_and_does_not_delete_user_data(self) -> None:
        payload = json.loads(
            (
                ROOT
                / "reports"
                / "pfi_v023"
                / "stage_10"
                / "phase_10_1"
                / "cache_cleanup_dry_run.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(payload["schema"], "PFICacheCleanupReportV1")
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["removed_count"], 0)
        self.assertEqual(payload["failed_count"], 0)
        self.assertIn("Only disposable local runtime artifacts", payload["safety_boundary"])
        boundary = payload["safety_boundary"].lower()
        for protected in ("reports", "holdings", "imports", "sqlite", "market bar caches"):
            self.assertIn(protected, boundary)

    def test_phase101_doc_and_files_do_not_claim_later_phases_or_placeholder_data(self) -> None:
        doc = (ROOT / "docs" / "pfi_v023" / "STAGE10_E2E_ACCEPTANCE.md").read_text(encoding="utf-8")
        self.assertIn("Stage 10 Phase 10.1", doc)
        self.assertIn("app 打开验证", doc)
        self.assertIn("localhost 打开验证", doc)
        self.assertIn("build/hash 一致验证", doc)
        self.assertIn("清缓存验证", doc)
        self.assertIn("Stage 10 Phase 10.2", doc)
        self.assertIn("Stage 10 Phase 10.3", doc)
        self.assertIn("GitHub main upload 未执行", doc)

        terms = ["mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"]
        paths = [
            ROOT / "tests" / "test_v023_stage10_e2e_acceptance.py",
            ROOT / "docs" / "pfi_v023" / "STAGE10_E2E_ACCEPTANCE.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8").lower().replace("sam" + "ple_size", "")
            for term in terms:
                self.assertIsNone(re.search(term, text), f"{path} contains blocked placeholder term {term}")

    def test_phase102_navigation_evidence_pack_exists_and_is_limited_to_navigation_e2e(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_10" / "phase_10_2"
        evidence_path = phase_dir / "evidence.json"
        browser_validation_path = phase_dir / "browser_validation.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        mobile_screenshot = phase_dir / "screenshots" / "mobile_basic.png"

        for path in (
            evidence_path,
            browser_validation_path,
            changed_files_path,
            terminal_log_path,
            mobile_screenshot,
        ):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage10Phase102EvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 10")
        self.assertEqual(evidence["phase_id"], "V023-S10-P10.2")
        self.assertEqual(evidence["phase_name"], "导航和页面 E2E")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["task_ids"], ["T10.2.1", "T10.2.2", "T10.2.3", "T10.2.4"])
        self.assertTrue(evidence["stage_contract"]["phase_10_1_entry_e2e_done"])
        self.assertTrue(evidence["stage_contract"]["phase_10_2_navigation_e2e_done"])
        self.assertFalse(evidence["stage_contract"]["phase_10_3_data_report_e2e_done"])
        self.assertFalse(evidence["stage_contract"]["stage_10_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in (
            "ten_first_level_entries_clickable",
            "secondary_main_paths_clickable",
            "browser_back_forward_works",
            "mobile_basic_screenshot_exists",
            "no_browser_page_errors",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)

    def test_phase102_browser_validation_proves_navigation_secondary_and_history(self) -> None:
        payload = json.loads(
            (ROOT / "reports" / "pfi_v023" / "stage_10" / "phase_10_2" / "browser_validation.json").read_text(
                encoding="utf-8"
            )
        )

        expected_nav = [
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
        self.assertEqual(payload["schema"], "PFIV023Stage10Phase102BrowserValidationV1")
        self.assertEqual(payload["phase_id"], "V023-S10-P10.2")
        self.assertEqual(payload["localhost"]["url"], "http://127.0.0.1:8501")
        self.assertEqual(payload["localhost"]["health"], "ok")
        self.assertEqual([row["label"] for row in payload["entry_clicks"]], expected_nav)
        self.assertTrue(all(row["clicked"] for row in payload["entry_clicks"]))
        self.assertTrue(all(row["active_label_visible"] for row in payload["entry_clicks"]))
        self.assertTrue(all(row["screenshot"]["bytes"] > 20000 for row in payload["entry_clicks"]))
        self.assertGreaterEqual(len(payload["secondary_clicks"]), 10)
        self.assertEqual({row["entry_label"] for row in payload["secondary_clicks"]}, set(expected_nav))
        self.assertTrue(all(row["clicked"] for row in payload["secondary_clicks"]))
        self.assertTrue(all(row["screenshot"]["bytes"] > 20000 for row in payload["secondary_clicks"]))
        self.assertEqual(payload["history_validation"]["back"]["ok"], True)
        self.assertEqual(payload["history_validation"]["forward"]["ok"], True)
        self.assertGreater(payload["mobile_basic"]["screenshot"]["bytes"], 20000)
        self.assertEqual(payload["console_errors"], [])
        self.assertEqual(payload["page_errors"], [])
        self.assertEqual(payload["http_errors"], [])

    def test_phase103_data_report_evidence_pack_exists_and_is_limited_to_data_report_e2e(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_10" / "phase_10_3"
        evidence_path = phase_dir / "evidence.json"
        browser_validation_path = phase_dir / "browser_validation.json"
        core_metrics_path = phase_dir / "core_metrics_state.json"
        data_check_path = phase_dir / "data_check_board.json"
        report_center_path = phase_dir / "report_center.json"
        error_state_path = phase_dir / "error_state_paths.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        screenshots = [
            phase_dir / "screenshots" / "core_metrics.png",
            phase_dir / "screenshots" / "data_check_board.png",
            phase_dir / "screenshots" / "report_center.png",
            phase_dir / "screenshots" / "error_state_path.png",
        ]

        for path in (
            evidence_path,
            browser_validation_path,
            core_metrics_path,
            data_check_path,
            report_center_path,
            error_state_path,
            changed_files_path,
            terminal_log_path,
            *screenshots,
        ):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage10Phase103EvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 10")
        self.assertEqual(evidence["phase_id"], "V023-S10-P10.3")
        self.assertEqual(evidence["phase_name"], "数据和报告 E2E")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["task_ids"], ["T10.3.1", "T10.3.2", "T10.3.3", "T10.3.4"])
        self.assertTrue(evidence["stage_contract"]["phase_10_1_entry_e2e_done"])
        self.assertTrue(evidence["stage_contract"]["phase_10_2_navigation_e2e_done"])
        self.assertTrue(evidence["stage_contract"]["phase_10_3_data_report_e2e_done"])
        self.assertFalse(evidence["stage_contract"]["stage_10_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in (
            "core_metrics_not_masked_by_zero",
            "data_check_board_visible",
            "report_center_conclusion_or_blocker_visible",
            "error_state_path_explains_blocker",
            "no_browser_page_errors",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)

    def test_phase103_browser_validation_proves_data_report_and_error_states(self) -> None:
        payload = json.loads(
            (ROOT / "reports" / "pfi_v023" / "stage_10" / "phase_10_3" / "browser_validation.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(payload["schema"], "PFIV023Stage10Phase103BrowserValidationV1")
        self.assertEqual(payload["phase_id"], "V023-S10-P10.3")
        self.assertEqual(payload["localhost"]["url"], "http://127.0.0.1:8501")
        self.assertEqual(payload["localhost"]["health"], "ok")
        self.assertGreater(payload["screenshots"]["core_metrics"]["bytes"], 20000)
        self.assertGreater(payload["screenshots"]["data_check_board"]["bytes"], 20000)
        self.assertGreater(payload["screenshots"]["report_center"]["bytes"], 20000)
        self.assertGreater(payload["screenshots"]["error_state_path"]["bytes"], 20000)
        self.assertEqual(payload["console_errors"], [])
        self.assertEqual(payload["page_errors"], [])
        self.assertEqual(payload["http_errors"], [])

        metric_labels = {row["label"] for row in payload["core_metrics"]["metrics"]}
        self.assertTrue({"净资产", "现金余额", "投资市值", "本月支出", "待复核交易", "数据源状态"}.issubset(metric_labels))
        self.assertEqual(payload["core_metrics"]["monthly_spending"]["value_text"], "CNY 7,153.98")
        self.assertIn("MetaDatabase 真实支付宝流水", payload["core_metrics"]["monthly_spending"]["source_note"])
        self.assertEqual(payload["core_metrics"]["pending_review"]["value_text"], "406")
        self.assertIn("8815 条真实流水", payload["core_metrics"]["pending_review"]["source_note"])
        self.assertTrue(all(row["zero_explanation_present"] for row in payload["core_metrics"]["zero_value_metrics"]))

        self.assertEqual(payload["data_check_board"]["workspace"], "sync")
        self.assertTrue(payload["data_check_board"]["contains_data_source_status"])
        self.assertTrue(payload["data_check_board"]["contains_review_queue"])
        self.assertIn("真实", payload["data_check_board"]["evidence_text"])

        self.assertEqual(payload["report_center"]["workspace"], "insights")
        self.assertTrue(payload["report_center"]["has_conclusion"])
        self.assertTrue(payload["report_center"]["has_blocker_or_waiting_state"])
        self.assertIn("真实数据", payload["report_center"]["evidence_text"])

        self.assertEqual(payload["error_state_path"]["workspace"], "market_research")
        self.assertTrue(payload["error_state_path"]["has_explanatory_empty_state"])
        self.assertTrue(payload["error_state_path"]["has_next_action"])


if __name__ == "__main__":
    unittest.main()
