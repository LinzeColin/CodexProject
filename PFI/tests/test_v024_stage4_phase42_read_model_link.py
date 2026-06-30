from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
PHASE42_DIR = ROOT / "reports" / "pfi_v024" / "stage_4" / "phase_4_2"

REQUIRED_METRIC_FIELDS = [
    "metric_id",
    "value",
    "currency",
    "status",
    "source_id",
    "record_count",
    "as_of",
    "formula_id",
    "confidence",
    "blocking_reason_zh",
    "calculation_state",
]

EXPECTED_SURFACES = ["home", "accounts", "investment", "consumption", "insights"]
EXPECTED_CORE_METRICS = {
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "consumption_outflow_cny",
    "report_summary_status",
}


def load_read_model_status_module():
    spec = importlib.util.find_spec("pfi_os.application.read_model_status")
    if spec is None:
        raise AssertionError("PFI/src/pfi_os/application/read_model_status.py is required for Stage 4 Phase 4.2")
    return importlib.import_module("pfi_os.application.read_model_status")


class TestV024Stage4Phase42ReadModelLink(unittest.TestCase):
    def test_phase42_contract_is_limited_to_read_model_linking(self) -> None:
        module = load_read_model_status_module()
        contract = module.build_v024_stage4_phase42_contract()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 4")
        self.assertEqual(contract["phase_id"], "4.2")
        self.assertEqual(contract["phase_name"], "read model 挂链")
        self.assertTrue(contract["current_phase_only"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertTrue(contract["read_model_wiring_done"])
        self.assertTrue(contract["ui_core_cards_wiring_done"])
        self.assertFalse(contract["phase_4_3_started"])
        self.assertFalse(contract["stage_4_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertEqual(contract["shared_surfaces"], EXPECTED_SURFACES)
        self.assertIn("Stage 4 Phase 4.3 验收", contract["explicitly_not_done"])

    def test_read_model_status_uses_real_metadatabase_and_preserves_blocked_states(self) -> None:
        module = load_read_model_status_module()
        payload = module.build_v024_read_model_status(project_root=ROOT)

        self.assertEqual(payload["schema"], "PFIV024Stage4ReadModelStatusV1")
        self.assertEqual(payload["target_version"], "v0.2.4")
        self.assertEqual(payload["source_package_version"], "v0.2.3-repair")
        self.assertEqual(payload["stage"], "Stage 4")
        self.assertEqual(payload["phase_id"], "4.2")
        self.assertRegex(payload["read_model_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(payload["source"]["data_root"], str(REPO_ROOT / "MetaDatabase" / "PFI"))
        self.assertEqual(payload["source"]["status"], "ready")
        self.assertEqual(payload["source"]["record_count"], 8815)
        self.assertEqual(payload["source"]["raw_file_count"], 4)
        self.assertEqual(payload["source"]["as_of"], "2026-06-03")

        metrics = {item["metric_id"]: item for item in payload["core_metric_states"]}
        self.assertEqual(set(metrics), EXPECTED_CORE_METRICS)
        for metric in metrics.values():
            self.assertEqual(list(metric), REQUIRED_METRIC_FIELDS)
            self.assertRegex(metric["blocking_reason_zh"], r"[\u4e00-\u9fff]")
            if metric["status"] not in {"ready", "confirmed_zero"}:
                self.assertIsNone(metric["value"], metric["metric_id"])

        consumption = metrics["consumption_outflow_cny"]
        self.assertEqual(consumption["status"], "ready")
        self.assertGreater(consumption["value"], 0)
        self.assertEqual(consumption["currency"], "CNY")
        self.assertEqual(consumption["record_count"], 8815)
        self.assertEqual(consumption["as_of"], "2026-06-03")
        self.assertEqual(consumption["formula_id"], "total_consumption_outflow_v1")
        self.assertIn("MetaDatabase/PFI", consumption["source_id"])

        for metric_id in ("net_worth_cny", "cash_balance_cny", "investment_market_value_cny"):
            self.assertEqual(metrics[metric_id]["status"], "source_missing")
            self.assertIsNone(metrics[metric_id]["value"])
            self.assertIn("未挂链", metrics[metric_id]["blocking_reason_zh"])

    def test_all_required_surfaces_share_the_same_metric_state_objects(self) -> None:
        module = load_read_model_status_module()
        payload = module.build_v024_read_model_status(project_root=ROOT)
        views = module.build_v024_surface_state_views(payload)

        self.assertEqual(views["schema"], "PFIV024Stage4SurfaceStateViewsV1")
        self.assertEqual(list(views["surfaces"]), EXPECTED_SURFACES)
        source_metrics = {item["metric_id"]: item for item in payload["core_metric_states"]}
        comparable_fields = [
            "metric_id",
            "value",
            "currency",
            "status",
            "source_id",
            "record_count",
            "as_of",
            "formula_id",
            "confidence",
            "blocking_reason_zh",
            "calculation_state",
        ]

        for surface_id in EXPECTED_SURFACES:
            surface = views["surfaces"][surface_id]
            self.assertEqual(surface["read_model_hash"], payload["read_model_hash"])
            self.assertEqual(surface["as_of"], payload["as_of"])
            for metric in surface["metrics"]:
                source = source_metrics[metric["metric_id"]]
                for field in comparable_fields:
                    self.assertEqual(metric[field], source[field], f"{surface_id}:{metric['metric_id']}:{field}")

    def test_frontend_and_runtime_are_wired_to_shared_read_model_status(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        shell = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        streamlit = (ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        runtime_api = (ROOT / "src" / "pfi_v02" / "stage_v021_runtime_api.py").read_text(encoding="utf-8")

        self.assertLess(html.index("./app/data_state.js"), html.index("./app/shell.js"))
        self.assertIn('id="pfi-read-model-status"', html)
        self.assertIn("data_state_path", streamlit)
        self.assertIn("/api/read-model-status", runtime_api)
        self.assertIn('runtimeApiJson("/api/read-model-status")', shell)
        self.assertIn("applyV024ReadModelStatusToSurfaces", shell)
        self.assertIn("PFI_V024_STAGE4_DATA_STATE", shell)
        self.assertNotIn('["待复核交易", hasConsumption ? String(consumption.review_count || 0) : "0"', shell)

    def test_javascript_surface_view_model_never_renders_blocked_metrics_as_zero(self) -> None:
        module = load_read_model_status_module()
        payload = module.build_v024_read_model_status(project_root=ROOT)
        script = """
const state = require('./PFI/web/app/data_state.js');
const payload = JSON.parse(process.argv[1]);
const views = state.buildSurfaceMetricViews(payload);
console.log(JSON.stringify({
  surfaces: Object.keys(views.surfaces),
  home: views.surfaces.home.metrics,
  accounts: views.surfaces.accounts.metrics,
  insights: views.surfaces.insights.metrics,
}));
"""
        completed = subprocess.run(
            [NODE, "-e", script, json.dumps(payload, ensure_ascii=False)],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        views = json.loads(completed.stdout)

        self.assertEqual(views["surfaces"], EXPECTED_SURFACES)
        home = {item["metric_id"]: item for item in views["home"]}
        self.assertIn("CNY", home["consumption_outflow_cny"]["display_value"])
        for metric_id in ("net_worth_cny", "cash_balance_cny", "investment_market_value_cny"):
            self.assertIn("未挂链", home[metric_id]["display_value"])
            self.assertNotIn("CNY 0.00", json.dumps(home[metric_id], ensure_ascii=False))

    def test_phase42_evidence_pack_is_machine_readable(self) -> None:
        expected_files = [
            PHASE42_DIR / "data_source_scan.json",
            PHASE42_DIR / "read_model_status.json",
            PHASE42_DIR / "core_metric_states.json",
            PHASE42_DIR / "page_metric_states.json",
            PHASE42_DIR / "evidence.json",
            PHASE42_DIR / "terminal.log",
            PHASE42_DIR / "changed_files.txt",
            PHASE42_DIR / "risk_and_rollback.md",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads((PHASE42_DIR / "evidence.json").read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in (PHASE42_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage4Phase42EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 4")
        self.assertEqual(evidence["phase_id"], "4.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["phase_4_1_complete"])
        self.assertTrue(evidence["phase_4_2_complete"])
        self.assertFalse(evidence["phase_4_3_started"])
        self.assertFalse(evidence["stage_4_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertEqual(evidence["changed_files"], changed_files)


if __name__ == "__main__":
    unittest.main()
