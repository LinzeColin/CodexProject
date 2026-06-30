from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"

PHASE41_WORKSPACES = {
    "accounts": {
        "label": "账户与资产",
        "routes": ["/accounts?tab=overview", "/accounts?tab=list", "/accounts?tab=trend", "/accounts?tab=reconcile"],
        "required_objects": {"账户地图", "账户清单", "资产趋势", "账户对账"},
    },
    "ledger": {
        "label": "账本流水",
        "routes": ["/ledger?tab=list", "/ledger?tab=filter", "/ledger?tab=review", "/ledger?tab=export"],
        "required_objects": {"流水列表", "筛选搜索", "分类复核", "导出流水"},
    },
    "investment": {
        "label": "投资管理",
        "routes": ["/investment?tab=overview", "/investment?tab=holdings", "/investment?tab=trades", "/investment?tab=returns"],
        "required_objects": {"投资总览", "持仓", "交易记录", "收益分析"},
    },
}

REQUIRED_PAGE_FIELDS = {
    "routeAlias",
    "title",
    "breadcrumb",
    "layoutKind",
    "primaryObject",
    "primaryAction",
    "emptyState",
    "errorState",
    "dataSource",
    "sections",
}


def load_stage4_pages() -> dict[str, object]:
    module_path = ROOT / "web" / "app" / "pages" / "stage4Subpages.js"
    script = """
const pages = require('./PFI/web/app/pages/stage4Subpages.js');
console.log(JSON.stringify(pages));
"""
    completed = subprocess.run(
        [NODE, "-e", script],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV023Stage4SubpageDifferentiation(unittest.TestCase):
    def test_phase41_pages_module_exists_for_allowed_stage4_surface(self) -> None:
        module_path = ROOT / "web" / "app" / "pages" / "stage4Subpages.js"

        self.assertTrue(module_path.exists())

    def test_phase41_catalog_has_accounts_ledger_investment_subpages(self) -> None:
        payload = load_stage4_pages()
        catalog = payload["phase41Subpages"]

        self.assertEqual(payload["version"], "v0.2.3")
        self.assertEqual(payload["stage"], "Stage 4")
        self.assertEqual(payload["phaseId"], "V023-S4-P4.1")
        self.assertEqual(set(catalog), set(PHASE41_WORKSPACES))

        for workspace_id, expected in PHASE41_WORKSPACES.items():
            with self.subTest(workspace=workspace_id):
                pages = catalog[workspace_id]
                self.assertGreaterEqual(len(pages), 3)
                self.assertLessEqual(len(pages), 5)
                self.assertEqual([page["routeAlias"] for page in pages], expected["routes"])
                self.assertEqual({page["primaryObject"] for page in pages}, expected["required_objects"])

    def test_phase41_each_subpage_has_independent_object_action_states_and_source(self) -> None:
        catalog = load_stage4_pages()["phase41Subpages"]

        for workspace_id, pages in catalog.items():
            signatures = set()
            for page in pages:
                with self.subTest(workspace=workspace_id, route=page.get("routeAlias")):
                    self.assertTrue(REQUIRED_PAGE_FIELDS <= set(page))
                    self.assertEqual(page["workspace"], workspace_id)
                    self.assertIn(PHASE41_WORKSPACES[workspace_id]["label"], page["breadcrumb"])
                    self.assertGreaterEqual(len(page["breadcrumb"]), 2)
                    self.assertNotEqual(page["primaryObject"], page["primaryAction"])
                    self.assertNotEqual(page["emptyState"], page["errorState"])
                    self.assertIn("真实", page["emptyState"])
                    self.assertTrue(page["errorState"].startswith("无法"))
                    self.assertTrue(page["dataSource"])
                    self.assertGreaterEqual(len(page["sections"]), 3)
                    signature = (
                        page["layoutKind"],
                        page["primaryObject"],
                        page["primaryAction"],
                        tuple(section["kind"] for section in page["sections"]),
                    )
                    signatures.add(signature)
            self.assertEqual(len(signatures), len(pages))

    def test_phase41_shell_loads_pages_module_and_renders_route_specific_surface(self) -> None:
        shell_text = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn("loadStage4PagesCatalog", shell_text)
        self.assertIn("PFI_V023_STAGE4_PAGES", shell_text)
        self.assertIn("renderStage4SubpageSurface", shell_text)
        self.assertIn("data-stage4-subpage-surface", shell_text)
        self.assertIn("data-stage4-layout-kind", shell_text)
        self.assertIn("data-stage4-primary-object", shell_text)
        self.assertIn("data-stage4-primary-action", shell_text)
        self.assertIn("data-stage4-empty-state", shell_text)
        self.assertIn("data-stage4-error-state", shell_text)

    def test_phase41_routes_match_stage3_normalized_routes_without_touching_future_phase_workspaces(self) -> None:
        routes_payload = subprocess.run(
            [
                NODE,
                "-e",
                "const routes=require('./PFI/web/app/routes.js'); console.log(JSON.stringify(routes.officialPrimaryEntries));",
            ],
            cwd=ROOT.parent,
            check=True,
            text=True,
            capture_output=True,
        )
        primary_workspaces = {entry["workspace"] for entry in json.loads(routes_payload.stdout)}
        catalog = load_stage4_pages()["phase41Subpages"]

        self.assertTrue(set(PHASE41_WORKSPACES) <= primary_workspaces)
        self.assertNotIn("consumption", catalog)
        self.assertNotIn("sync", catalog)
        self.assertNotIn("insights", catalog)
        self.assertNotIn("market_research", catalog)
        self.assertNotIn("settings", catalog)
        self.assertNotIn("recommendations", catalog)

    def test_phase41_evidence_exists_before_later_stage4_phases_or_upload(self) -> None:
        evidence_root = ROOT / "reports" / "pfi_v023" / "stage_4" / "phase_4_1"
        evidence_path = evidence_root / "evidence.json"
        changed_files_path = evidence_root / "changed_files.txt"
        terminal_log_path = evidence_root / "terminal.log"
        browser_validation_path = evidence_root / "browser_validation.json"
        screenshot_paths = [
            evidence_root / "screenshots" / "accounts_subpages.png",
            evidence_root / "screenshots" / "ledger_subpages.png",
            evidence_root / "screenshots" / "investment_subpages.png",
        ]

        self.assertTrue(evidence_path.exists())
        self.assertTrue(changed_files_path.exists())
        self.assertTrue(terminal_log_path.exists())
        self.assertTrue(browser_validation_path.exists())
        for screenshot_path in screenshot_paths:
            self.assertTrue(screenshot_path.exists())

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        browser_validation = json.loads(browser_validation_path.read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in changed_files_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 4")
        self.assertEqual(evidence["phase_id"], "V023-S4-P4.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertTrue(evidence["allowed_files_obeyed"])
        self.assertTrue(evidence["no_mock_financial_data"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(evidence["phase41_summary"]["workspaces"], ["accounts", "ledger", "investment"])
        self.assertEqual(evidence["phase41_summary"]["subpage_count"], 12)
        self.assertTrue(browser_validation["accounts_subpages_differentiated"])
        self.assertTrue(browser_validation["ledger_subpages_differentiated"])
        self.assertTrue(browser_validation["investment_subpages_differentiated"])
        self.assertTrue(browser_validation["url_state_breadcrumb_title_changed"])
        self.assertTrue(browser_validation["empty_and_error_states_present"])
        self.assertEqual(browser_validation["console_errors"], [])
        self.assertIn("Stage 4 Phase 4.2 consumption/data/reports subpages", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
