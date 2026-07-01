from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"

STATE_KINDS = ("loading", "success", "error", "empty")
ACTIONABLE_EMPTY_TERMS = ("打开", "查看", "检查", "接入", "重试", "返回")


def load_phase53_payload() -> dict[str, object]:
    script = """
const pages = require('./PFI/web/app/pages/stage5Subpages.js');
const ux = require('./PFI/web/app/ux_state.js');
const catalog = pages.buildV024Stage5Phase52Catalog();
const flatPages = pages.flattenV024Stage5Phase52Pages(catalog);
const uxCatalog = ux.buildV024Stage5UxStateCatalog(catalog);
console.log(JSON.stringify({
  contract: ux.buildV024Stage5Phase53Contract(),
  uxCatalog,
  validation: ux.validateV024Stage5UxStateCatalog(uxCatalog),
  firstPageState: ux.buildV024Stage5PageStateModel(flatPages[0]),
}));
"""
    completed = subprocess.run(
        [NODE, "-e", script],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage5Phase53InteractionStates(unittest.TestCase):
    def test_phase53_contract_is_limited_to_interaction_states(self) -> None:
        payload = load_phase53_payload()
        contract = payload["contract"]

        self.assertEqual(contract["schema"], "PFIV024Stage5Phase53ContractV1")
        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 5")
        self.assertEqual(contract["phase_id"], "5.3")
        self.assertEqual(contract["phase_name"], "交互状态")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["phase_5_1_complete"])
        self.assertTrue(contract["phase_5_2_complete"])
        self.assertEqual(tuple(contract["required_state_kinds"]), STATE_KINDS)
        self.assertIn("T5.3.1 loading/success/error 状态", contract["tasks"])
        self.assertIn("T5.3.2 空状态中文可行动", contract["tasks"])
        self.assertIn("T5.3.3 后退/前进验收", contract["tasks"])
        self.assertIn("Stage 5 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])

    def test_every_stage5_subpage_has_actionable_loading_success_error_empty_states(self) -> None:
        payload = load_phase53_payload()
        ux_catalog = payload["uxCatalog"]
        validation = payload["validation"]

        self.assertEqual(validation["schema"], "PFIV024Stage5Phase53UxStateValidationV1")
        self.assertEqual(validation["status"], "pass")
        self.assertEqual(validation["total_page_count"], 45)
        self.assertEqual(validation["missing_state_pages"], [])
        self.assertEqual(validation["non_actionable_empty_pages"], [])
        self.assertEqual(validation["non_actionable_error_pages"], [])

        for workspace, pages in ux_catalog.items():
            self.assertGreaterEqual(len(pages), 3, workspace)
            for page in pages:
                self.assertEqual(tuple(page["stateKinds"]), STATE_KINDS)
                self.assertTrue(page["routeAlias"].startswith("/"))
                self.assertTrue(page["targetWorkspace"])
                self.assertTrue(page["primaryObject"])
                states = page["states"]
                for kind in STATE_KINDS:
                    with self.subTest(route=page["routeAlias"], kind=kind):
                        state = states[kind]
                        self.assertEqual(state["kind"], kind)
                        self.assertTrue(state["message_zh"])
                        self.assertNotIn("TODO", state["message_zh"])
                        self.assertTrue(state["action"]["label"])
                        self.assertTrue(state["action"]["routeAlias"].startswith("/"))
                        self.assertEqual(state["action"]["targetWorkspace"], page["targetWorkspace"])
                empty_label = states["empty"]["action"]["label"]
                error_label = states["error"]["action"]["label"]
                self.assertTrue(any(term in empty_label for term in ACTIONABLE_EMPTY_TERMS), empty_label)
                self.assertTrue(any(term in error_label for term in ACTIONABLE_EMPTY_TERMS), error_label)

    def test_history_acceptance_contract_covers_route_state_and_back_forward(self) -> None:
        payload = load_phase53_payload()
        validation = payload["validation"]
        history = validation["history_acceptance"]

        self.assertEqual(history["status"], "pass")
        self.assertTrue(history["route_alias_from_location"])
        self.assertTrue(history["push_state"])
        self.assertTrue(history["replace_state"])
        self.assertTrue(history["hashchange_listener"])
        self.assertTrue(history["popstate_listener"])
        self.assertTrue(history["route_state_preserved"])
        self.assertEqual(history["total_route_aliases"], 45)
        self.assertEqual(history["duplicate_route_aliases"], [])

    def test_static_and_streamlit_runtimes_load_ux_state_before_shell(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        shell = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        streamlit = (ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

        self.assertLess(html.index("./app/pages/stage5Subpages.js"), html.index("./app/ux_state.js"))
        self.assertLess(html.index("./app/ux_state.js"), html.index("./app/shell.js"))
        self.assertIn("PFI_V024_STAGE5_UX_STATE", shell)
        self.assertIn("loadStage5UxState", shell)
        self.assertIn("buildV024Stage5UxStateCatalog", shell)
        self.assertIn('setAttribute("data-stage5-ux-state", "phase_5_3")', shell)
        self.assertIn('setAttribute("data-stage5-state", kind)', shell)
        self.assertIn('if (kind === "loading") return "加载中"', shell)
        self.assertIn("data-stage5-empty-action", shell)
        self.assertIn("data-stage5-error-action", shell)
        self.assertIn("data-stage5-history-ready", shell)
        self.assertIn("ux_state_path", streamlit)
        self.assertIn("ux_state_js", streamlit)

    def test_phase53_evidence_pack_exists_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v024" / "stage_5" / "phase_5_3"
        evidence_path = phase_dir / "evidence.json"
        ux_validation_path = phase_dir / "ux_state_validation.json"
        history_validation_path = phase_dir / "history_validation.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        risk_path = phase_dir / "risk_and_rollback.md"
        doc_path = ROOT / "docs" / "pfi_v024" / "STAGE5_INTERACTION_STATES.md"

        for path in (
            evidence_path,
            ux_validation_path,
            history_validation_path,
            changed_files_path,
            terminal_log_path,
            risk_path,
            doc_path,
        ):
            with self.subTest(path=path.name):
                self.assertTrue(path.exists(), f"{path} is required")

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        ux_validation = json.loads(ux_validation_path.read_text(encoding="utf-8"))
        history_validation = json.loads(history_validation_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema"], "PFIV024Stage5Phase53EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 5")
        self.assertEqual(evidence["phase_id"], "5.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_5_1_complete"])
        self.assertTrue(evidence["phase_5_2_complete"])
        self.assertTrue(evidence["phase_5_3_complete"])
        self.assertFalse(evidence["stage_5_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertTrue(evidence["no_forbidden_financial_data"])
        self.assertEqual(ux_validation["status"], "pass")
        self.assertEqual(history_validation["status"], "pass")
        self.assertEqual(ux_validation["total_page_count"], evidence["total_page_count"])


if __name__ == "__main__":
    unittest.main()
