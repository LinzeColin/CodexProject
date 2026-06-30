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
        self.assertIn("Phase 6.2 UI wiring 未执行", doc_text)
        self.assertIn("GitHub main upload 未执行", doc_text)

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


if __name__ == "__main__":
    unittest.main()
