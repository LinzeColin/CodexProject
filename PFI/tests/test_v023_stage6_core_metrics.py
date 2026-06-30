from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent

EXPECTED_METRIC_IDS = {
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "life_consumption_cny",
    "total_consumption_outflow_cny",
    "data_health",
}

REQUIRED_METRIC_FIELDS = {
    "metric_id",
    "label",
    "value",
    "currency",
    "status",
    "source",
    "as_of",
    "evidence_hash",
    "message_zh",
}

DISPLAY_STATUSES = {"ready", "confirmed_zero"}
BLOCKED_STATUSES = {
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


def load_read_model_module():
    spec = importlib.util.find_spec("pfi_v02.stage_v023_read_model")
    if spec is None:
        raise AssertionError("PFI/src/pfi_v02/stage_v023_read_model.py is required for Stage 6 Phase 6.1")
    return importlib.import_module("pfi_v02.stage_v023_read_model")


def load_core_metrics_module():
    spec = importlib.util.find_spec("pfi_v02.stage_v023_core_metrics")
    if spec is None:
        raise AssertionError("PFI/src/pfi_v02/stage_v023_core_metrics.py is required for Stage 6 Phase 6.1")
    return importlib.import_module("pfi_v02.stage_v023_core_metrics")


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
        raise AssertionError("Node runtime is required for Stage 6 page contract tests")
    completed = subprocess.run(
        [node, "-e", script, *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV023Stage6CoreMetrics(unittest.TestCase):
    def test_phase61_contract_is_limited_to_read_model_adapter(self) -> None:
        module = load_core_metrics_module()
        contract = module.build_stage6_phase61_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 6")
        self.assertEqual(contract["phase_id"], "V023-S6-P6.1")
        self.assertEqual(contract["phase_name"], "read model adapter")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["real_data_only_financial_metrics"])
        self.assertEqual(contract["task_ids"], ["T6.1.1", "T6.1.2", "T6.1.3", "T6.1.4"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_read_model.py", contract["allowed_files"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_core_metrics.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/data/coreMetrics.js", contract["allowed_files"])
        self.assertNotIn("PFI/web/app/pages/home.js", contract["changed_in_this_phase"])
        self.assertIn("Phase 6.2 UI wiring", contract["explicitly_not_done"])
        self.assertIn("Phase 6.3 cross-page consistency", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase61_input_discovers_current_metadatabase_real_files(self) -> None:
        module = load_read_model_module()
        read_input = module.build_stage6_read_model_input(project_root=ROOT)

        self.assertEqual(read_input["schema"], "PFIV023Stage6ReadModelInputV1")
        self.assertEqual(read_input["status"], "ready")
        self.assertEqual(read_input["data_root"], str(REPO_ROOT / "MetaDatabase" / "PFI"))
        self.assertEqual(read_input["source_type"], "metadatabase_pfi")
        self.assertTrue(Path(read_input["transactions_path"]).exists())
        self.assertTrue(Path(read_input["manifest_path"]).exists())
        self.assertEqual(read_input["raw_file_count"], 4)
        self.assertEqual(read_input["transaction_count"], 8815)
        self.assertEqual(read_input["date_range"], {"start": "2022-06-06", "end": "2026-06-03"})
        self.assertRegex(read_input["evidence_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_phase61_read_model_returns_real_or_blocked_metric_states(self) -> None:
        module = load_core_metrics_module()
        model = module.build_stage6_core_metrics_read_model(project_root=ROOT)

        self.assertEqual(model["schema"], "PFIV023Stage6CoreMetricsReadModelV1")
        self.assertEqual(model["stage"], "Stage 6")
        self.assertEqual(model["phase_id"], "V023-S6-P6.1")
        self.assertEqual(model["source"]["type"], "metadatabase_pfi")
        self.assertRegex(model["as_of"], r"^2026-06-03")
        self.assertRegex(model["read_model_hash"], r"^sha256:[0-9a-f]{64}$")

        metrics = {item["metric_id"]: item for item in model["core_metrics"]}
        self.assertEqual(set(metrics), EXPECTED_METRIC_IDS)
        for metric in metrics.values():
            self.assertEqual(set(metric), REQUIRED_METRIC_FIELDS)
            self.assertRegex(metric["message_zh"], r"[\u4e00-\u9fff]")
            if metric["status"] in DISPLAY_STATUSES:
                self.assertIsNotNone(metric["value"], metric["metric_id"])
                self.assertTrue(metric["source"], metric["metric_id"])
                self.assertTrue(metric["as_of"], metric["metric_id"])
                self.assertRegex(metric["evidence_hash"], r"^sha256:[0-9a-f]{64}$")
            else:
                self.assertIn(metric["status"], BLOCKED_STATUSES)
                self.assertIsNone(metric["value"], metric["metric_id"])

        self.assertEqual(metrics["life_consumption_cny"]["status"], "ready")
        self.assertGreater(metrics["life_consumption_cny"]["value"], 0)
        self.assertEqual(metrics["total_consumption_outflow_cny"]["status"], "ready")
        self.assertGreater(metrics["total_consumption_outflow_cny"]["value"], metrics["life_consumption_cny"]["value"])
        self.assertEqual(metrics["data_health"]["status"], "ready")
        self.assertEqual(metrics["data_health"]["value"], 8815)

        for metric_id in ("net_worth_cny", "cash_balance_cny", "investment_market_value_cny"):
            self.assertIn(metrics[metric_id]["status"], {"not_mounted", "not_loaded", "review_required"})
            self.assertIsNone(metrics[metric_id]["value"])
            self.assertRegex(metrics[metric_id]["message_zh"], r"未挂载|未加载|需要人工复核")

    def test_phase61_missing_data_maps_to_stage2_state_machine_without_zero_fallback(self) -> None:
        module = load_core_metrics_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            model = module.build_stage6_core_metrics_read_model(project_root=Path(temp_dir))

        self.assertEqual(model["source"]["status"], "not_mounted")
        for metric in model["core_metrics"]:
            self.assertIn(metric["status"], {"not_mounted", "path_error"})
            self.assertIsNone(metric["value"], metric["metric_id"])
            self.assertIsNone(metric["source"], metric["metric_id"])
            self.assertIsNone(metric["as_of"], metric["metric_id"])
            self.assertIsNone(metric["evidence_hash"], metric["metric_id"])
            self.assertRegex(metric["message_zh"], r"未挂载|路径")

    def test_runtime_consumption_fixed_flex_missing_policy_does_not_render_fake_zero(self) -> None:
        shell = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn("function formatOptionalCnyAmount", shell)
        self.assertIn("fixed_spend_cny_has_rule", shell)
        self.assertNotIn('${formatCnyAmount(consumption.fixed_spend_cny)} / ${formatCnyAmount(consumption.flex_spend_cny)}', shell)
        self.assertIn('"未配置"', shell)

    def test_phase61_javascript_contract_matches_python_adapter_contract(self) -> None:
        module = load_core_metrics_module()
        js_path = ROOT / "web" / "app" / "data" / "coreMetrics.js"
        self.assertTrue(js_path.exists(), "PFI/web/app/data/coreMetrics.js is required")
        text = js_path.read_text(encoding="utf-8")

        self.assertIn("PFI_STAGE6_CORE_METRICS", text)
        for metric_id in module.CORE_METRIC_IDS:
            self.assertIn(metric_id, text)
        for status in module.METRIC_DATA_STATUSES:
            self.assertIn(status, text)
        for field in REQUIRED_METRIC_FIELDS:
            self.assertIn(field, text)

        node = node_executable()
        if node:
            result = subprocess.run([node, "--check", str(js_path)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_phase61_evidence_and_docs_are_machine_readable(self) -> None:
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE6_CORE_METRICS.md"
        evidence_dir = ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1"
        evidence_path = evidence_dir / "evidence.json"
        core_metrics_path = evidence_dir / "core_metrics.json"
        audit_path = evidence_dir / "read_model_audit.json"
        changed_files_path = evidence_dir / "changed_files.txt"
        terminal_log_path = evidence_dir / "terminal.log"

        for path in (doc_path, evidence_path, core_metrics_path, audit_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        doc_text = doc_path.read_text(encoding="utf-8")
        self.assertIn("Stage 6 Phase 6.1", doc_text)
        self.assertIn("read model adapter", doc_text)

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        core_metrics = json.loads(core_metrics_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 6")
        self.assertEqual(evidence["phase_id"], "V023-S6-P6.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(core_metrics["schema"], "PFIV023Stage6CoreMetricsReadModelV1")
        self.assertEqual(audit["schema"], "PFIV023Stage6ReadModelAuditV1")
        self.assertTrue(evidence["real_data_only_financial_metrics"])
        self.assertFalse(evidence["stage_contract"]["phase_6_2_ui_wiring_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_read_model.py", changed_files)
        self.assertIn("PFI/src/pfi_v02/stage_v023_core_metrics.py", changed_files)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage6_core_metrics.py -q", terminal_log)
        self.assertIn("node --check PFI/web/app/data/coreMetrics.js", terminal_log)

    def test_phase61_new_runtime_files_do_not_contain_blocked_placeholder_terms(self) -> None:
        terms = ["mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"]
        paths = [
            ROOT / "src" / "pfi_v02" / "stage_v023_read_model.py",
            ROOT / "src" / "pfi_v02" / "stage_v023_core_metrics.py",
            ROOT / "web" / "app" / "data" / "coreMetrics.js",
            ROOT / "docs" / "pfi_v023" / "STAGE6_CORE_METRICS.md",
        ]
        for path in paths:
            self.assertTrue(path.exists(), str(path))
            text = path.read_text(encoding="utf-8").lower()
            for term in terms:
                self.assertIsNone(re.search(term, text), f"{path} contains blocked placeholder term {term}")

    def test_phase62_contract_is_limited_to_page_wiring(self) -> None:
        module = load_core_metrics_module()
        contract = module.build_stage6_phase62_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 6")
        self.assertEqual(contract["phase_id"], "V023-S6-P6.2")
        self.assertEqual(contract["phase_name"], "页面接入")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T6.2.1", "T6.2.2", "T6.2.3", "T6.2.4"])
        for path in (
            "PFI/web/app/pages/home.js",
            "PFI/web/app/pages/accounts.js",
            "PFI/web/app/pages/investment.js",
            "PFI/web/app/pages/consumption.js",
            "PFI/web/app/data/coreMetrics.js",
        ):
            self.assertIn(path, contract["allowed_files"])
            self.assertIn(path, contract["changed_in_this_phase"])
        self.assertNotIn("PFI/web/app/shell.js", contract["changed_in_this_phase"])
        self.assertNotIn("PFI/web/index.html", contract["changed_in_this_phase"])
        self.assertIn("Phase 6.3 cross-page consistency", contract["explicitly_not_done"])
        self.assertIn("Stage 6 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase62_page_modules_render_stage61_read_model_without_zero_fallback(self) -> None:
        core_metrics_path = ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json"
        script = """
const fs = require('fs');
const home = require('./PFI/web/app/pages/home.js');
const accounts = require('./PFI/web/app/pages/accounts.js');
const investment = require('./PFI/web/app/pages/investment.js');
const consumption = require('./PFI/web/app/pages/consumption.js');
const readModel = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
console.log(JSON.stringify({
  home: home.buildStage6Phase62HomeMetricViewModel(readModel),
  accounts: accounts.buildStage6Phase62AccountsViewModel(readModel),
  investment: investment.buildStage6Phase62InvestmentViewModel(readModel),
  consumption: consumption.buildStage6Phase62ConsumptionViewModel(readModel),
}));
"""
        payload = node_json(script, str(core_metrics_path))

        home_cards = {card["metric_id"]: card for card in payload["home"]["cards"]}
        self.assertEqual(set(home_cards), EXPECTED_METRIC_IDS)
        for metric_id in ("net_worth_cny", "cash_balance_cny", "investment_market_value_cny"):
            self.assertIsNone(home_cards[metric_id]["value"])
            self.assertIn(home_cards[metric_id]["status"], {"not_mounted", "not_loaded", "review_required"})
            self.assertRegex(home_cards[metric_id]["display_value"], r"未挂载|未加载|需要人工复核")
            self.assertNotIn("CNY 0.00", json.dumps(home_cards[metric_id], ensure_ascii=False))

        self.assertIn("CNY 1,545,600.44", home_cards["life_consumption_cny"]["display_value"])
        self.assertIn("CNY 1,727,278.37", home_cards["total_consumption_outflow_cny"]["display_value"])
        self.assertEqual(home_cards["data_health"]["display_value"], "8,815 records")

        accounts_cards = {card["metric_id"]: card for card in payload["accounts"]["cards"]}
        self.assertEqual(set(accounts_cards), {"net_worth_cny", "cash_balance_cny", "data_health"})
        self.assertIn("未挂载", accounts_cards["net_worth_cny"]["display_value"])
        self.assertIn("未挂载", accounts_cards["cash_balance_cny"]["display_value"])
        self.assertIn("2026-06-03", accounts_cards["data_health"]["detail"])

        investment_cards = {card["metric_id"]: card for card in payload["investment"]["cards"]}
        self.assertEqual(set(investment_cards), {"investment_market_value_cny", "data_health"})
        self.assertIn("未挂载", investment_cards["investment_market_value_cny"]["display_value"])

        consumption_cards = {card["metric_id"]: card for card in payload["consumption"]["cards"]}
        self.assertEqual(set(consumption_cards), {"life_consumption_cny", "total_consumption_outflow_cny", "data_health"})
        for metric_id in ("life_consumption_cny", "total_consumption_outflow_cny", "data_health"):
            self.assertEqual(consumption_cards[metric_id]["status"], "ready")
            self.assertTrue(consumption_cards[metric_id]["source"])
            self.assertEqual(consumption_cards[metric_id]["as_of"], "2026-06-03")
            self.assertRegex(consumption_cards[metric_id]["evidence_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_phase62_missing_data_view_models_preserve_chinese_blocking_states(self) -> None:
        script = """
const home = require('./PFI/web/app/pages/home.js');
const accounts = require('./PFI/web/app/pages/accounts.js');
const investment = require('./PFI/web/app/pages/investment.js');
const consumption = require('./PFI/web/app/pages/consumption.js');
const ids = [
  ['net_worth_cny', '净资产', 'CNY'],
  ['cash_balance_cny', '现金余额', 'CNY'],
  ['investment_market_value_cny', '投资市值', 'CNY'],
  ['life_consumption_cny', '生活消费', 'CNY'],
  ['total_consumption_outflow_cny', '消费总流出', 'CNY'],
  ['data_health', '数据健康', 'records'],
];
const readModel = {
  schema: 'PFIV023Stage6CoreMetricsReadModelV1',
  stage: 'Stage 6',
  phase_id: 'V023-S6-P6.1',
  source: { type: 'metadatabase_pfi', status: 'not_mounted' },
  as_of: null,
  read_model_hash: null,
  core_metrics: ids.map(([metric_id, label, currency]) => ({
    metric_id, label, value: null, currency, status: 'not_mounted',
    source: null, as_of: null, evidence_hash: null,
    message_zh: '未挂载真实个人财务数据源',
  })),
};
console.log(JSON.stringify({
  home: home.buildStage6Phase62HomeMetricViewModel(readModel),
  accounts: accounts.buildStage6Phase62AccountsViewModel(readModel),
  investment: investment.buildStage6Phase62InvestmentViewModel(readModel),
  consumption: consumption.buildStage6Phase62ConsumptionViewModel(readModel),
}));
"""
        payload = node_json(script)
        text = json.dumps(payload, ensure_ascii=False)

        self.assertIn("未挂载真实个人财务数据源", text)
        self.assertNotIn("CNY 0.00", text)
        for view in payload.values():
            for card in view["cards"]:
                self.assertIsNone(card["value"])
                self.assertEqual(card["status"], "not_mounted")
                self.assertIsNone(card["source"])
                self.assertIsNone(card["as_of"])
                self.assertIsNone(card["evidence_hash"])

    def test_phase62_evidence_and_docs_are_machine_readable(self) -> None:
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE6_CORE_METRICS.md"
        evidence_dir = ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_2"
        evidence_path = evidence_dir / "evidence.json"
        page_models_path = evidence_dir / "page_view_models.json"
        changed_files_path = evidence_dir / "changed_files.txt"
        terminal_log_path = evidence_dir / "terminal.log"

        for path in (doc_path, evidence_path, page_models_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        doc_text = doc_path.read_text(encoding="utf-8")
        self.assertIn("Stage 6 Phase 6.2", doc_text)
        self.assertIn("页面接入", doc_text)

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        page_models = json.loads(page_models_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 6")
        self.assertEqual(evidence["phase_id"], "V023-S6-P6.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertFalse(evidence["stage_contract"]["phase_6_3_consistency_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertIn("home", page_models)
        self.assertIn("accounts", page_models)
        self.assertIn("investment", page_models)
        self.assertIn("consumption", page_models)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage6_core_metrics.py -q", terminal_log)
        self.assertIn("node --check PFI/web/app/pages/accounts.js", terminal_log)

    def test_phase63_contract_is_limited_to_metric_consistency(self) -> None:
        module = load_core_metrics_module()
        contract = module.build_stage6_phase63_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 6")
        self.assertEqual(contract["phase_id"], "V023-S6-P6.3")
        self.assertEqual(contract["phase_name"], "指标一致性")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T6.3.1", "T6.3.2", "T6.3.3", "T6.3.4"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_core_metrics.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/data/coreMetrics.js", contract["allowed_files"])
        self.assertIn("PFI/tests/test_v023_stage6_core_metrics.py", contract["allowed_files"])
        self.assertNotIn("PFI/web/app/shell.js", contract["changed_in_this_phase"])
        self.assertNotIn("PFI/web/index.html", contract["changed_in_this_phase"])
        self.assertIn("Stage 6 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase63_home_accounts_report_share_same_metric_source_chain(self) -> None:
        module = load_core_metrics_module()
        core_metrics = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json").read_text(encoding="utf-8"))
        page_models = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_2" / "page_view_models.json").read_text(encoding="utf-8"))

        matrix = module.build_stage6_phase63_consistency_matrix(core_metrics, page_models)

        self.assertEqual(matrix["schema"], "PFIV023Stage6MetricConsistencyMatrixV1")
        self.assertEqual(matrix["phase_id"], "V023-S6-P6.3")
        self.assertEqual(matrix["source_core_metrics"]["read_model_hash"], core_metrics["read_model_hash"])
        self.assertEqual(matrix["source_core_metrics"]["as_of"], "2026-06-03")
        self.assertEqual(matrix["findings"], [])

        surfaces = matrix["surfaces"]
        self.assertEqual(set(surfaces), {"home", "accounts", "report"})
        for surface_name, surface in surfaces.items():
            self.assertEqual(surface["read_model_hash"], core_metrics["read_model_hash"], surface_name)
            self.assertEqual(surface["as_of"], core_metrics["as_of"], surface_name)
            for metric in surface["metrics"]:
                source_metric = next(item for item in core_metrics["core_metrics"] if item["metric_id"] == metric["metric_id"])
                self.assertEqual(metric["status"], source_metric["status"], metric["metric_id"])
                self.assertEqual(metric["value"], source_metric["value"], metric["metric_id"])
                self.assertEqual(metric["source"], source_metric["source"], metric["metric_id"])
                self.assertEqual(metric["as_of"], source_metric["as_of"], metric["metric_id"])
                self.assertEqual(metric["evidence_hash"], source_metric["evidence_hash"], metric["metric_id"])

        accounts_ids = {item["metric_id"] for item in surfaces["accounts"]["metrics"]}
        report_ids = {item["metric_id"] for item in surfaces["report"]["metrics"]}
        self.assertTrue({"net_worth_cny", "cash_balance_cny", "data_health"}.issubset(accounts_ids))
        self.assertEqual(report_ids, EXPECTED_METRIC_IDS)

    def test_phase63_metric_basis_copy_covers_cash_investment_and_consumption(self) -> None:
        module = load_core_metrics_module()
        basis = module.build_stage6_metric_basis_catalog()

        self.assertEqual(basis["schema"], "PFIV023Stage6MetricBasisCatalogV1")
        entries = basis["metrics"]
        for metric_id in ("cash_balance_cny", "investment_market_value_cny", "life_consumption_cny", "total_consumption_outflow_cny"):
            self.assertIn(metric_id, entries)
            self.assertRegex(entries[metric_id]["basis_zh"], r"[\u4e00-\u9fff]")
            self.assertIn("status_policy_zh", entries[metric_id])
            self.assertIn("as_of_hash_policy_zh", entries[metric_id])
        self.assertIn("账户余额 read model", entries["cash_balance_cny"]["basis_zh"])
        self.assertIn("持仓市值 read model", entries["investment_market_value_cny"]["basis_zh"])
        self.assertIn("生活消费流出减退款", entries["life_consumption_cny"]["basis_zh"])
        self.assertIn("基金申购", entries["total_consumption_outflow_cny"]["basis_zh"])

        script = """
const core = require('./PFI/web/app/data/coreMetrics.js');
const fs = require('fs');
const readModel = JSON.parse(fs.readFileSync('./PFI/reports/pfi_v023/stage_6/phase_6_1/core_metrics.json', 'utf8'));
const card = core.buildMetricCard(readModel, 'total_consumption_outflow_cny');
console.log(JSON.stringify(card));
"""
        card = node_json(script)
        self.assertIn("basis_zh", card)
        self.assertIn("基金申购", card["basis_zh"])
        self.assertIn("as_of 2026-06-03", card["detail"])

    def test_phase63_error_state_screenshot_and_source_term_scan_evidence_exist(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_3"
        evidence_path = phase_dir / "evidence.json"
        consistency_path = phase_dir / "consistency_matrix.json"
        basis_path = phase_dir / "metric_basis.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        error_view_path = phase_dir / "error_state_view_models.json"
        screenshot_path = phase_dir / "screenshots" / "error_states.png"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (evidence_path, consistency_path, basis_path, scan_path, error_view_path, screenshot_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        consistency = json.loads(consistency_path.read_text(encoding="utf-8"))
        basis = json.loads(basis_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        error_view = json.loads(error_view_path.read_text(encoding="utf-8"))

        self.assertEqual(evidence["phase_id"], "V023-S6-P6.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertEqual(consistency["findings"], [])
        self.assertEqual(basis["schema"], "PFIV023Stage6MetricBasisCatalogV1")
        self.assertEqual(scan["violations"], [])
        self.assertFalse(evidence["stage_contract"]["stage_6_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertGreater(screenshot_path.stat().st_size, 10000)
        self.assertIn("未挂载真实个人财务数据源", json.dumps(error_view, ensure_ascii=False))
        self.assertNotIn("CNY 0.00", json.dumps(error_view, ensure_ascii=False))

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage6_core_metrics.py -q", terminal_log)
        self.assertIn("blocked source term scan", terminal_log)

    def test_stage6_review_evidence_exists_before_stage_upload(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "stage_6" / "stage6_review"
        evidence_path = review_dir / "evidence.json"
        audit_path = review_dir / "review_audit.json"
        scan_path = review_dir / "no_source_term_scan.json"
        terminal_log_path = review_dir / "terminal.log"
        changed_files_path = review_dir / "changed_files.txt"

        self.assertTrue(evidence_path.exists(), "Stage 6 whole-stage review evidence is required before upload")
        self.assertTrue(audit_path.exists(), "Stage 6 whole-stage review audit is required before upload")
        self.assertTrue(scan_path.exists(), "Stage 6 whole-stage no-source-term scan is required")
        self.assertTrue(terminal_log_path.exists(), "Stage 6 whole-stage review terminal log is required")
        self.assertTrue(changed_files_path.exists(), "Stage 6 whole-stage review changed files record is required")

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 6")
        self.assertEqual(evidence["review_id"], "V023-S6-REVIEW")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["stage6_whole_stage_review"])
        self.assertTrue(evidence["findings_fixed"])
        self.assertFalse(evidence["stage7_started"])
        self.assertFalse(evidence["github_main_uploaded_before_review"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(audit["review_id"], "V023-S6-REVIEW")
        self.assertEqual(audit["phase_status"], {"phase_6_1": "candidate_pass", "phase_6_2": "candidate_pass", "phase_6_3": "candidate_pass"})
        self.assertEqual(audit["consistency_findings"], [])
        self.assertEqual(scan["violations"], [])
        self.assertTrue(audit["read_model_audit"]["real_metadatabase_pfi"])
        self.assertEqual(audit["read_model_audit"]["transaction_count"], 8815)
        self.assertEqual(audit["read_model_audit"]["raw_file_count"], 4)
        self.assertRegex(audit["read_model_audit"]["read_model_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(audit["metric_status"]["ready"], 3)
        self.assertEqual(audit["metric_status"]["blocked"], 3)
        self.assertIn("life_consumption_cny", audit["metric_status"]["ready_metric_ids"])
        self.assertIn("cash_balance_cny", audit["metric_status"]["blocked_metric_ids"])

        doc_text = (ROOT / "docs" / "pfi_v023" / "STAGE6_CORE_METRICS.md").read_text(encoding="utf-8")
        self.assertIn("Stage 6 Whole-stage Review", doc_text)
        self.assertNotIn("Stage 6 whole-stage review 未执行", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("Stage 6 whole-stage review", terminal_log)
        self.assertIn("PFI/tests/test_v023_stage6_core_metrics.py -q", terminal_log)


if __name__ == "__main__":
    unittest.main()
