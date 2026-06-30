from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
DATA_SOURCE_STATUSES = {
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


def load_stage8_module():
    spec = importlib.util.find_spec("pfi_v02.stage_v023_data_sources")
    if spec is None:
        raise AssertionError("PFI/src/pfi_v02/stage_v023_data_sources.py is required for Stage 8 Phase 8.1")
    return importlib.import_module("pfi_v02.stage_v023_data_sources")


def node_executable() -> str | None:
    candidates = [
        os.environ.get("PFI_NODE"),
        shutil.which("node"),
        "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def node_json(script: str, *args: str) -> dict[str, object]:
    node = node_executable()
    if not node:
        raise AssertionError("Node runtime is required for Stage 8 upload page contract tests")
    completed = subprocess.run(
        [node, "-e", script, *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV023Stage8DataSourceGate(unittest.TestCase):
    def test_phase81_contract_is_limited_to_data_source_model(self) -> None:
        module = load_stage8_module()
        contract = module.build_stage8_phase81_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 8")
        self.assertEqual(contract["phase_id"], "V023-S8-P8.1")
        self.assertEqual(contract["phase_name"], "数据源模型")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T8.1.1", "T8.1.2", "T8.1.3", "T8.1.4"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_data_sources.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/pages/upload.js", contract["allowed_files"])
        self.assertNotIn("PFI/web/app/shell.js", contract["changed_in_this_phase"])
        self.assertIn("Phase 8.2 检查板 UI", contract["explicitly_not_done"])
        self.assertIn("Phase 8.3 禁止假数据回退", contract["explicitly_not_done"])
        self.assertIn("Stage 8 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase81_data_source_gate_uses_real_stage6_read_model_and_blocks_missing_inputs(self) -> None:
        module = load_stage8_module()
        core_metrics = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json").read_text(encoding="utf-8"))
        payload = module.build_stage8_data_source_gate(core_metrics_read_model=core_metrics)

        self.assertEqual(payload["schema"], "PFIV023Stage8DataSourceGateV1")
        self.assertEqual(payload["phase_id"], "V023-S8-P8.1")
        self.assertEqual(payload["source_core_metrics"]["read_model_hash"], core_metrics["read_model_hash"])
        self.assertEqual(set(payload["data_source_statuses"]), DATA_SOURCE_STATUSES)
        sources = {item["data_source_id"]: item for item in payload["data_sources"]}
        self.assertIn("metadatabase_pfi_alipay_daily", sources)
        self.assertIn("account_balance_read_model", sources)
        self.assertIn("holding_market_value_read_model", sources)

        alipay = sources["metadatabase_pfi_alipay_daily"]
        self.assertEqual(alipay["status"], "ready")
        self.assertEqual(alipay["records"]["normalized_record_count"], 8815)
        self.assertEqual(alipay["records"]["raw_file_count"], 4)
        self.assertEqual(alipay["date_range"], {"start": "2022-06-06", "end": "2026-06-03"})
        self.assertEqual(alipay["last_updated"], "2026-06-03")
        self.assertEqual(alipay["blocked_metric_ids"], [])
        self.assertFalse(alipay["auto_import_enabled"])

        account = sources["account_balance_read_model"]
        self.assertEqual(account["status"], "not_mounted")
        self.assertIn("net_worth_cny", account["blocked_metric_ids"])
        self.assertIn("cash_balance_cny", account["blocked_metric_ids"])
        self.assertIsNone(account["records"]["normalized_record_count"])
        self.assertIn("未挂链", account["reason_zh"])
        self.assertNotIn("等待上传", account["reason_zh"])

        holding = sources["holding_market_value_read_model"]
        self.assertEqual(holding["status"], "not_mounted")
        self.assertIn("investment_market_value_cny", holding["blocked_metric_ids"])
        self.assertIn("net_worth_cny", holding["blocked_metric_ids"])

        text = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("CNY 0.00", text)
        self.assertNotIn("等待上传", text)

    def test_phase81_error_reason_catalog_is_chinese_specific_and_actionable(self) -> None:
        module = load_stage8_module()
        catalog = module.build_stage8_error_reason_catalog()

        self.assertEqual(catalog["schema"], "PFIV023Stage8ErrorReasonCatalogV1")
        reasons = {item["status"]: item for item in catalog["reasons"]}
        self.assertEqual(set(reasons), DATA_SOURCE_STATUSES)
        self.assertIn("路径", reasons["path_error"]["reason_zh"])
        self.assertIn("解析失败", reasons["parse_error"]["reason_zh"])
        self.assertIn("权限", reasons["permission_error"]["reason_zh"])
        self.assertIn("快照日期", reasons["outdated"]["reason_zh"])
        for item in reasons.values():
            self.assertRegex(item["reason_zh"], r"[\u4e00-\u9fff]")
            self.assertRegex(item["next_action_zh"], r"[\u4e00-\u9fff]")
            self.assertNotEqual(item["reason_zh"], "等待上传")

    def test_phase81_upload_page_model_surfaces_status_records_range_and_blockers(self) -> None:
        payload = json.loads((ROOT / "reports" / "pfi_v023" / "stage_8" / "phase_8_1" / "data_source_gate.json").read_text(encoding="utf-8"))
        script = """
const uploadPage = require('./PFI/web/app/pages/upload.js');
const payload = JSON.parse(process.argv[1]);
console.log(JSON.stringify(uploadPage.buildStage8Phase81DataSourceGateViewModel(payload)));
"""
        view = node_json(script, json.dumps(payload, ensure_ascii=False))

        self.assertEqual(view["schema"], "PFIV023Stage8DataSourceGatePageViewModelV1")
        self.assertEqual(view["phase_id"], "V023-S8-P8.1")
        self.assertEqual(view["data_source_count"], 3)
        self.assertEqual(view["ready_count"], 1)
        self.assertEqual(view["blocked_count"], 2)
        text = json.dumps(view, ensure_ascii=False)
        for term in ("status", "records", "date range", "last updated", "blocked metrics", "未挂链", "8,815", "2022-06-06", "2026-06-03"):
            self.assertIn(term, text)
        self.assertNotIn("等待上传", text)
        self.assertNotIn("CNY 0.00", text)

    def test_phase82_contract_is_limited_to_dashboard_ui(self) -> None:
        module = load_stage8_module()
        contract = module.build_stage8_phase82_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 8")
        self.assertEqual(contract["phase_id"], "V023-S8-P8.2")
        self.assertEqual(contract["phase_name"], "检查板 UI")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T8.2.1", "T8.2.2", "T8.2.3", "T8.2.4"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_data_sources.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/pages/upload.js", contract["allowed_files"])
        self.assertIn("PFI/reports/pfi_v023/stage_8/phase_8_2/*", contract["changed_in_this_phase"])
        self.assertNotIn("PFI/web/app/shell.js", contract["changed_in_this_phase"])
        self.assertIn("Phase 8.3 禁止假数据回退", contract["explicitly_not_done"])
        self.assertIn("Stage 8 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase82_dashboard_model_builds_matrix_import_parse_mapping_and_routes(self) -> None:
        module = load_stage8_module()
        core_metrics = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json").read_text(encoding="utf-8"))
        payload = module.build_stage8_dashboard_ui(core_metrics_read_model=core_metrics)

        self.assertEqual(payload["schema"], "PFIV023Stage8DashboardUIV1")
        self.assertEqual(payload["phase_id"], "V023-S8-P8.2")
        self.assertEqual(payload["phase_name"], "检查板 UI")
        self.assertEqual(payload["summary"]["source_count"], 3)
        self.assertEqual(payload["summary"]["ready_count"], 1)
        self.assertEqual(payload["summary"]["blocked_count"], 2)
        self.assertFalse(payload["summary"]["auto_import_enabled"])

        rows = {item["data_source_id"]: item for item in payload["data_source_matrix"]["rows"]}
        self.assertEqual(set(rows), {"metadatabase_pfi_alipay_daily", "account_balance_read_model", "holding_market_value_read_model"})
        alipay = rows["metadatabase_pfi_alipay_daily"]
        self.assertEqual(alipay["status"], "ready")
        self.assertEqual(alipay["records"]["normalized_record_count"], 8815)
        self.assertEqual(alipay["records"]["raw_file_count"], 4)
        self.assertEqual(alipay["date_range"], {"start": "2022-06-06", "end": "2026-06-03"})
        self.assertEqual(alipay["blocked_metric_ids"], [])

        account = rows["account_balance_read_model"]
        self.assertEqual(account["status"], "not_mounted")
        self.assertIn("net_worth_cny", account["blocked_metric_ids"])
        self.assertIn("cash_balance_cny", account["blocked_metric_ids"])
        self.assertIn("未挂链", account["reason_zh"])

        holding = rows["holding_market_value_read_model"]
        self.assertEqual(holding["status"], "not_mounted")
        self.assertIn("investment_market_value_cny", holding["blocked_metric_ids"])
        self.assertIn("未挂链", holding["parse_preview"]["detail_zh"])

        self.assertEqual(payload["upload_import_status"]["status"], "read_only_gate")
        self.assertFalse(payload["upload_import_status"]["auto_import_enabled"])
        self.assertGreaterEqual(len(payload["parse_preview"]["entries"]), 3)
        self.assertGreaterEqual(len(payload["field_mapping_entries"]), 3)
        route_targets = {item["route"] for item in payload["route_actions"]}
        for route in ("/reports", "/ledger/review", "/accounts/reconcile", "/investment/holdings"):
            self.assertIn(route, route_targets)
        self.assertFalse(payload["stage_contract"]["phase_8_3_no_fallback_done"])
        self.assertFalse(payload["stage_contract"]["stage_8_whole_review_done"])
        self.assertFalse(payload["stage_contract"]["github_main_upload_done"])

        text = json.dumps(payload, ensure_ascii=False)
        for term in ("status", "records", "date range", "last updated", "blocked metrics", "字段映射", "解析预览"):
            self.assertIn(term, text)
        self.assertNotIn("等待上传", text)
        self.assertNotIn("CNY 0.00", text)
        self.assertNotIn("toast", text.lower())

    def test_phase82_upload_page_dashboard_view_model_is_actionable(self) -> None:
        payload = json.loads((ROOT / "reports" / "pfi_v023" / "stage_8" / "phase_8_2" / "dashboard_ui.json").read_text(encoding="utf-8"))
        script = """
const uploadPage = require('./PFI/web/app/pages/upload.js');
const payload = JSON.parse(process.argv[1]);
console.log(JSON.stringify(uploadPage.buildStage8Phase82DashboardViewModel(payload)));
"""
        view = node_json(script, json.dumps(payload, ensure_ascii=False))

        self.assertEqual(view["schema"], "PFIV023Stage8DashboardPageViewModelV1")
        self.assertEqual(view["phase_id"], "V023-S8-P8.2")
        self.assertEqual(view["page"], "upload")
        self.assertEqual(view["source_count"], 3)
        self.assertEqual(view["ready_count"], 1)
        self.assertEqual(view["blocked_count"], 2)
        self.assertGreaterEqual(view["action_count"], 4)
        section_ids = {section["section_id"] for section in view["sections"]}
        for section_id in ("data-source-matrix", "import-status", "parse-preview", "field-mapping", "route-actions"):
            self.assertIn(section_id, section_ids)

        text = json.dumps(view, ensure_ascii=False)
        for term in ("status", "records", "date range", "last updated", "blocked metrics", "/reports", "/ledger/review", "/accounts/reconcile", "/investment/holdings"):
            self.assertIn(term, text)
        self.assertNotIn("等待上传", text)
        self.assertNotIn("CNY 0.00", text)
        self.assertNotIn("toast", text.lower())

    def test_phase83_contract_is_limited_to_no_fallback_evidence(self) -> None:
        module = load_stage8_module()
        contract = module.build_stage8_phase83_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 8")
        self.assertEqual(contract["phase_id"], "V023-S8-P8.3")
        self.assertEqual(contract["phase_name"], "禁止假数据回退")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T8.3.1", "T8.3.2", "T8.3.3", "T8.3.4"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_data_sources.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/pages/upload.js", contract["allowed_files"])
        self.assertIn("PFI/reports/pfi_v023/stage_8/phase_8_3/*", contract["changed_in_this_phase"])
        self.assertNotIn("PFI/web/app/shell.js", contract["changed_in_this_phase"])
        self.assertIn("Stage 8 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])
        self.assertIn("Stage 9 visual system", contract["explicitly_not_done"])

    def test_phase83_no_fallback_policy_blocks_auto_replacement_and_missing_zero(self) -> None:
        module = load_stage8_module()
        policy = module.build_stage8_no_fallback_policy()

        self.assertEqual(policy["schema"], "PFIV023Stage8NoFallbackPolicyV1")
        self.assertEqual(policy["phase_id"], "V023-S8-P8.3")
        self.assertFalse(policy["fallback_financial_data_allowed"])
        self.assertFalse(policy["auto_import_test_data_allowed"])
        self.assertFalse(policy["missing_data_renders_financial_zero"])
        self.assertGreaterEqual(len(policy["disallowed_financial_source_codes"]), 6)
        self.assertEqual(set(policy["covered_statuses"]), DATA_SOURCE_STATUSES)
        for behavior in policy["status_behaviors"]:
            if behavior["status"] not in {"ready", "confirmed_zero"}:
                self.assertFalse(behavior["can_display_financial_value"])
                self.assertEqual(behavior["replacement_action"], "block_with_reason")
        text = json.dumps(policy, ensure_ascii=False)
        self.assertNotIn("CNY 0.00", text)
        self.assertNotIn("等待上传", text)
        self.assertNotIn("toast", text.lower())

    def test_phase83_state_evidence_covers_failure_outdated_and_zero_proof_without_new_data(self) -> None:
        module = load_stage8_module()
        cases = module.build_stage8_no_fallback_state_evidence()

        self.assertEqual(cases["schema"], "PFIV023Stage8NoFallbackStateEvidenceV1")
        self.assertEqual(cases["phase_id"], "V023-S8-P8.3")
        self.assertFalse(cases["generates_personal_financial_data"])
        states = {item["status"]: item for item in cases["state_cases"]}
        for status in ("path_error", "parse_error", "outdated", "confirmed_zero"):
            self.assertIn(status, states)

        path_error = states["path_error"]
        self.assertFalse(path_error["can_display_financial_value"])
        self.assertIn("路径", path_error["reason_zh"])
        self.assertNotIn("CNY 0.00", path_error["display_text_zh"])

        parse_error = states["parse_error"]
        self.assertFalse(parse_error["can_display_financial_value"])
        self.assertIn("解析失败", parse_error["reason_zh"])
        self.assertIn("文件", parse_error["failure_detail_zh"])
        self.assertIn("字段", parse_error["failure_detail_zh"])

        outdated = states["outdated"]
        self.assertFalse(outdated["can_display_financial_value"])
        self.assertIn("快照日期", outdated["display_text_zh"])
        self.assertIn("2026-06-03", outdated["display_text_zh"])

        zero = states["confirmed_zero"]
        self.assertTrue(zero["can_display_financial_value"])
        self.assertTrue(zero["requires_evidence_chain"])
        self.assertEqual(zero["required_evidence_fields"], ["source", "as_of", "evidence_hash"])
        self.assertEqual(zero["current_confirmed_zero_metric_count"], 0)
        self.assertFalse(zero["current_personal_financial_zero_rendered"])
        self.assertTrue(zero["stage2_data_state_validates_zero_rule"])

        text = json.dumps(cases, ensure_ascii=False)
        self.assertNotIn("等待上传", text)
        self.assertNotIn("toast", text.lower())

    def test_phase83_upload_page_no_fallback_view_model_is_actionable(self) -> None:
        payload = json.loads((ROOT / "reports" / "pfi_v023" / "stage_8" / "phase_8_3" / "no_fallback_policy.json").read_text(encoding="utf-8"))
        cases = json.loads((ROOT / "reports" / "pfi_v023" / "stage_8" / "phase_8_3" / "state_evidence_cases.json").read_text(encoding="utf-8"))
        script = """
const uploadPage = require('./PFI/web/app/pages/upload.js');
const policy = JSON.parse(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
console.log(JSON.stringify(uploadPage.buildStage8Phase83NoFallbackViewModel(policy, cases)));
"""
        view = node_json(script, json.dumps(payload, ensure_ascii=False), json.dumps(cases, ensure_ascii=False))

        self.assertEqual(view["schema"], "PFIV023Stage8NoFallbackPageViewModelV1")
        self.assertEqual(view["phase_id"], "V023-S8-P8.3")
        self.assertEqual(view["page"], "upload")
        self.assertFalse(view["fallback_financial_data_allowed"])
        self.assertEqual(view["state_case_count"], 4)
        section_ids = {section["section_id"] for section in view["sections"]}
        for section_id in ("no-fallback-policy", "failure-state", "outdated-state", "zero-proof"):
            self.assertIn(section_id, section_ids)
        text = json.dumps(view, ensure_ascii=False)
        for term in ("path_error", "parse_error", "outdated", "confirmed_zero", "快照日期", "证据链"):
            self.assertIn(term, text)
        self.assertNotIn("等待上传", text)
        self.assertNotIn("toast", text.lower())

    def test_phase81_doc_and_evidence_exist_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_8" / "phase_8_1"
        evidence_path = phase_dir / "evidence.json"
        gate_path = phase_dir / "data_source_gate.json"
        page_model_path = phase_dir / "data_source_gate_page_model.json"
        catalog_path = phase_dir / "error_reason_catalog.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        screenshot_path = phase_dir / "screenshots" / "data_source_gate.png"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (evidence_path, gate_path, page_model_path, catalog_path, scan_path, screenshot_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        page_model = json.loads(page_model_path.read_text(encoding="utf-8"))
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 8")
        self.assertEqual(evidence["phase_id"], "V023-S8-P8.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertFalse(evidence["stage_contract"]["phase_8_2_dashboard_ui_done"])
        self.assertFalse(evidence["stage_contract"]["phase_8_3_no_fallback_done"])
        self.assertFalse(evidence["stage_contract"]["stage_8_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(gate["schema"], "PFIV023Stage8DataSourceGateV1")
        self.assertEqual(page_model["schema"], "PFIV023Stage8DataSourceGatePageViewModelV1")
        self.assertEqual(catalog["schema"], "PFIV023Stage8ErrorReasonCatalogV1")
        self.assertEqual(scan["violations"], [])
        self.assertGreater(screenshot_path.stat().st_size, 10000)

        doc_text = (ROOT / "docs" / "pfi_v023" / "STAGE8_DATA_SOURCE_GATE.md").read_text(encoding="utf-8")
        self.assertIn("Stage 8 Phase 8.1", doc_text)
        self.assertIn("数据源模型", doc_text)
        self.assertIn("Stage 8 Phase 8.2", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage8_data_source_gate.py -q", terminal_log)

    def test_phase82_doc_and_evidence_exist_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_8" / "phase_8_2"
        evidence_path = phase_dir / "evidence.json"
        dashboard_path = phase_dir / "dashboard_ui.json"
        page_model_path = phase_dir / "dashboard_page_model.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        screenshot_path = phase_dir / "screenshots" / "data_source_dashboard.png"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (evidence_path, dashboard_path, page_model_path, scan_path, screenshot_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
        page_model = json.loads(page_model_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 8")
        self.assertEqual(evidence["phase_id"], "V023-S8-P8.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertTrue(evidence["stage_contract"]["phase_8_2_dashboard_ui_done"])
        self.assertFalse(evidence["stage_contract"]["phase_8_3_no_fallback_done"])
        self.assertFalse(evidence["stage_contract"]["stage_8_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(dashboard["schema"], "PFIV023Stage8DashboardUIV1")
        self.assertEqual(page_model["schema"], "PFIV023Stage8DashboardPageViewModelV1")
        self.assertEqual(scan["violations"], [])
        self.assertGreater(screenshot_path.stat().st_size, 10000)

        doc_text = (ROOT / "docs" / "pfi_v023" / "STAGE8_DATA_SOURCE_GATE.md").read_text(encoding="utf-8")
        self.assertIn("Stage 8 Phase 8.2", doc_text)
        self.assertIn("数据源矩阵", doc_text)
        self.assertIn("上传/导入状态", doc_text)
        self.assertIn("解析预览", doc_text)
        self.assertIn("字段映射", doc_text)
        self.assertIn("Stage 8 Phase 8.3", doc_text)
        self.assertIn("Stage 8 Whole-stage Review", doc_text)
        self.assertNotIn("Stage 8 whole-stage review 未执行", doc_text)
        self.assertNotIn("GitHub main upload 未执行", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage8_data_source_gate.py -q", terminal_log)

    def test_phase83_doc_and_evidence_exist_before_stage_review(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_8" / "phase_8_3"
        evidence_path = phase_dir / "evidence.json"
        policy_path = phase_dir / "no_fallback_policy.json"
        cases_path = phase_dir / "state_evidence_cases.json"
        page_model_path = phase_dir / "no_fallback_page_model.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        failure_screenshot_path = phase_dir / "screenshots" / "failure_state.png"
        outdated_screenshot_path = phase_dir / "screenshots" / "outdated_state.png"
        zero_screenshot_path = phase_dir / "screenshots" / "zero_proof.png"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (
            evidence_path,
            policy_path,
            cases_path,
            page_model_path,
            scan_path,
            failure_screenshot_path,
            outdated_screenshot_path,
            zero_screenshot_path,
            changed_files_path,
            terminal_log_path,
        ):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        page_model = json.loads(page_model_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 8")
        self.assertEqual(evidence["phase_id"], "V023-S8-P8.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertTrue(evidence["stage_contract"]["phase_8_3_no_fallback_done"])
        self.assertFalse(evidence["stage_contract"]["stage_8_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(policy["schema"], "PFIV023Stage8NoFallbackPolicyV1")
        self.assertEqual(cases["schema"], "PFIV023Stage8NoFallbackStateEvidenceV1")
        self.assertEqual(page_model["schema"], "PFIV023Stage8NoFallbackPageViewModelV1")
        self.assertEqual(scan["violations"], [])
        for path in (failure_screenshot_path, outdated_screenshot_path, zero_screenshot_path):
            self.assertGreater(path.stat().st_size, 10000)

        doc_text = (ROOT / "docs" / "pfi_v023" / "STAGE8_DATA_SOURCE_GATE.md").read_text(encoding="utf-8")
        self.assertIn("Stage 8 Phase 8.3", doc_text)
        self.assertIn("禁止假数据回退", doc_text)
        self.assertIn("失败状态截图", doc_text)
        self.assertIn("过期状态截图", doc_text)
        self.assertIn("真为 0 状态证明", doc_text)
        self.assertIn("Stage 8 Whole-stage Review", doc_text)
        self.assertNotIn("Stage 8 whole-stage review 未执行", doc_text)
        self.assertNotIn("GitHub main upload 未执行", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage8_data_source_gate.py -q", terminal_log)

    def test_stage8_review_evidence_exists_before_stage_upload(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "stage_8" / "stage8_review"
        evidence_path = review_dir / "evidence.json"
        audit_path = review_dir / "review_audit.json"
        scan_path = review_dir / "no_source_term_scan.json"
        terminal_log_path = review_dir / "terminal.log"
        changed_files_path = review_dir / "changed_files.txt"

        for path in (evidence_path, audit_path, scan_path, terminal_log_path, changed_files_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 8")
        self.assertEqual(evidence["review_id"], "V023-S8-REVIEW")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["stage8_whole_stage_review"])
        self.assertTrue(evidence["findings_fixed"])
        self.assertFalse(evidence["stage9_started"])
        self.assertFalse(evidence["github_main_uploaded_before_review"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(
            set(evidence["phase_evidence"]),
            {"phase_8_1", "phase_8_2", "phase_8_3"},
        )
        for key in (
            "data_source_dashboard_exists",
            "source_matrix_has_status_records_range_updated_blockers",
            "upload_failure_reasons_actionable",
            "no_auto_test_data_import",
            "routes_to_reports_and_review",
            "failure_outdated_zero_evidence_exists",
            "no_forbidden_financial_data_terms",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)
        for key in (
            "no_waiting_upload_generic_state",
            "no_unlocatable_failure_reason",
            "no_auto_fallback_financial_data",
            "no_transient_notice_only_upload_feedback",
        ):
            self.assertTrue(evidence["stop_condition_checks"][key], key)

        self.assertEqual(audit["schema"], "PFIV023Stage8WholeStageReviewAuditV1")
        self.assertEqual(audit["review_id"], "V023-S8-REVIEW")
        self.assertEqual(
            audit["phase_status"],
            {
                "phase_8_1": "candidate_pass",
                "phase_8_2": "candidate_pass",
                "phase_8_3": "candidate_pass",
            },
        )
        summary = audit["data_source_summary"]
        self.assertEqual(summary["total_sources"], 3)
        self.assertEqual(summary["ready_count"], 1)
        self.assertEqual(summary["blocked_count"], 2)
        self.assertEqual(summary["alipay"]["normalized_record_count"], 8815)
        self.assertEqual(summary["alipay"]["raw_file_count"], 4)
        self.assertEqual(summary["alipay"]["date_range"], {"start": "2022-06-06", "end": "2026-06-03"})
        self.assertEqual(
            set(summary["blocked_metric_ids"]),
            {"net_worth_cny", "cash_balance_cny", "investment_market_value_cny"},
        )
        route_targets = set(audit["dashboard_route_targets"])
        for route in ("/reports", "/ledger/review", "/accounts/reconcile", "/investment/holdings"):
            self.assertIn(route, route_targets)
        self.assertEqual(
            set(audit["state_case_statuses"]),
            {"path_error", "parse_error", "outdated", "confirmed_zero"},
        )
        self.assertFalse(audit["no_fallback_policy"]["fallback_financial_data_allowed"])
        self.assertFalse(audit["no_fallback_policy"]["auto_import_test_data_allowed"])
        self.assertFalse(audit["no_fallback_policy"]["missing_data_renders_financial_zero"])
        self.assertEqual(audit["review_findings"], [])
        self.assertFalse(audit["stage9_started"])
        self.assertFalse(audit["github_main_uploaded_before_review"])
        self.assertEqual(scan["violations"], [])

        doc_text = (ROOT / "docs" / "pfi_v023" / "STAGE8_DATA_SOURCE_GATE.md").read_text(encoding="utf-8")
        self.assertIn("Stage 8 Whole-stage Review", doc_text)
        self.assertIn("PFI/reports/pfi_v023/stage_8/stage8_review/evidence.json", doc_text)
        self.assertIn("PFI/reports/pfi_v023/stage_8/stage8_review/review_audit.json", doc_text)
        self.assertNotIn("Stage 8 whole-stage review 未执行", doc_text)
        self.assertNotIn("GitHub main upload 未执行", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("Stage 8 whole-stage review", terminal_log)
        self.assertIn("PFI/tests/test_v023_stage8_data_source_gate.py -q", terminal_log)

    def test_phase81_files_do_not_contain_blocked_placeholder_terms(self) -> None:
        terms = ["mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"]
        paths = [
            ROOT / "src" / "pfi_v02" / "stage_v023_data_sources.py",
            ROOT / "web" / "app" / "pages" / "upload.js",
            ROOT / "tests" / "test_v023_stage8_data_source_gate.py",
            ROOT / "docs" / "pfi_v023" / "STAGE8_DATA_SOURCE_GATE.md",
        ]
        for path in paths:
            self.assertTrue(path.exists(), str(path))
            text = path.read_text(encoding="utf-8").lower().replace("sample_size", "")
            for term in terms:
                self.assertIsNone(re.search(term, text), f"{path} contains blocked placeholder term {term}")


if __name__ == "__main__":
    unittest.main()
