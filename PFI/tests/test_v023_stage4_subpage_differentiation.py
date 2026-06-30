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

PHASE42_WORKSPACES = {
    "consumption": {
        "label": "消费管理",
        "routes": [
            "/consumption?tab=overview",
            "/consumption?tab=category",
            "/consumption?tab=budget",
            "/consumption?tab=subscription",
            "/consumption?tab=anomaly",
        ],
        "required_objects": {"消费总览", "分类分析", "预算", "订阅", "异常消费"},
    },
    "sync": {
        "label": "数据源与上传",
        "routes": [
            "/sources-upload?tab=upload",
            "/sources-upload?tab=import",
            "/sources-upload?tab=sources",
            "/sources-upload?tab=review",
            "/sources-upload?tab=history",
        ],
        "required_objects": {"上传中心", "导入中心", "数据源管理", "待复核", "导入历史"},
    },
    "insights": {
        "label": "报告与洞察",
        "routes": [
            "/reports?tab=monthly",
            "/reports?tab=quarterly",
            "/reports?tab=yearly",
            "/reports?tab=custom",
            "/reports?tab=export",
        ],
        "required_objects": {"月报", "季报", "年报", "自定义报告", "导出"},
    },
}

PHASE43_WORKSPACES = {
    "market_research": {
        "label": "市场与研究",
        "routes": [
            "/market-research?tab=market",
            "/market-research?tab=research",
            "/market-research?tab=company",
            "/market-research?tab=fund",
            "/market-research/strategy-lab",
        ],
        "required_objects": {"市场观察", "研究笔记", "公司研究", "基金研究", "策略实验室"},
        "legacy_aliases": {"/market/watch", "/market/research", "/market/lab"},
    },
    "settings": {
        "label": "设置",
        "routes": [
            "/settings?tab=account",
            "/settings?tab=data-system",
            "/settings?tab=privacy",
            "/settings?tab=feedback",
            "/settings?tab=backup",
        ],
        "required_objects": {"账户偏好", "数据与系统", "隐私与本地存储", "反馈偏好", "备份恢复"},
        "legacy_aliases": {"/settings/data"},
    },
    "recommendations": {
        "label": "建议与复盘",
        "routes": [
            "/review?tab=list",
            "/review?tab=detail",
            "/review?tab=decision",
            "/review?tab=history",
        ],
        "required_objects": {"建议列表", "建议详情", "决策记录", "复盘记录"},
        "legacy_aliases": set(),
    },
}

PHASE43_LEGACY_ALIAS_TARGETS = {
    "/market/watch": "/market-research?tab=market",
    "/market/research": "/market-research?tab=research",
    "/market/lab": "/market-research/strategy-lab",
    "/settings/data": "/settings?tab=data-system",
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
        self.assertIn("V023-S4-P4.1", payload["phaseIds"])
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

    def test_phase42_catalog_has_consumption_sync_insights_subpages(self) -> None:
        payload = load_stage4_pages()
        catalog = payload["phase42Subpages"]

        self.assertEqual(payload["version"], "v0.2.3")
        self.assertEqual(payload["stage"], "Stage 4")
        self.assertIn("V023-S4-P4.2", payload["phaseIds"])
        self.assertEqual(set(catalog), set(PHASE42_WORKSPACES))

        for workspace_id, expected in PHASE42_WORKSPACES.items():
            with self.subTest(workspace=workspace_id):
                pages = catalog[workspace_id]
                self.assertGreaterEqual(len(pages), 3)
                self.assertLessEqual(len(pages), 5)
                self.assertEqual([page["routeAlias"] for page in pages], expected["routes"])
                self.assertEqual({page["primaryObject"] for page in pages}, expected["required_objects"])

    def test_phase42_each_subpage_has_independent_object_action_gate_states_and_source(self) -> None:
        catalog = load_stage4_pages()["phase42Subpages"]

        for workspace_id, pages in catalog.items():
            signatures = set()
            for page in pages:
                with self.subTest(workspace=workspace_id, route=page.get("routeAlias")):
                    self.assertTrue(REQUIRED_PAGE_FIELDS <= set(page))
                    self.assertEqual(page["workspace"], workspace_id)
                    self.assertIn(PHASE42_WORKSPACES[workspace_id]["label"], page["breadcrumb"])
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

    def test_phase42_shell_uses_combined_stage4_catalog_without_touching_phase43(self) -> None:
        shell_text = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        catalog = load_stage4_pages()

        self.assertIn("stage4SubpageCatalog", shell_text)
        self.assertIn("phase42Subpages", shell_text)
        self.assertIn("/sources-upload?tab=upload", json.dumps(catalog, ensure_ascii=False))
        self.assertIn("/reports?tab=monthly", json.dumps(catalog, ensure_ascii=False))
        self.assertNotIn("market_research", catalog["phase42Subpages"])
        self.assertNotIn("settings", catalog["phase42Subpages"])
        self.assertNotIn("recommendations", catalog["phase42Subpages"])

    def test_phase43_catalog_has_market_settings_recommendations_subpages_and_v01_aliases(self) -> None:
        payload = load_stage4_pages()
        catalog = payload["phase43Subpages"]

        self.assertEqual(payload["version"], "v0.2.3")
        self.assertEqual(payload["stage"], "Stage 4")
        self.assertIn("V023-S4-P4.3", payload["phaseIds"])
        self.assertEqual(set(catalog), set(PHASE43_WORKSPACES))

        for workspace_id, expected in PHASE43_WORKSPACES.items():
            with self.subTest(workspace=workspace_id):
                pages = catalog[workspace_id]
                self.assertGreaterEqual(len(pages), 3)
                self.assertLessEqual(len(pages), 5)
                self.assertEqual([page["routeAlias"] for page in pages], expected["routes"])
                self.assertEqual({page["primaryObject"] for page in pages}, expected["required_objects"])
                self.assertEqual(
                    {
                        alias
                        for page in pages
                        for alias in page.get("legacyAliases", [])
                    },
                    expected["legacy_aliases"],
                )

    def test_phase43_each_subpage_has_independent_object_action_compat_states_and_source(self) -> None:
        catalog = load_stage4_pages()["phase43Subpages"]

        for workspace_id, pages in catalog.items():
            signatures = set()
            for page in pages:
                with self.subTest(workspace=workspace_id, route=page.get("routeAlias")):
                    self.assertTrue(REQUIRED_PAGE_FIELDS <= set(page))
                    self.assertEqual(page["workspace"], workspace_id)
                    self.assertIn(PHASE43_WORKSPACES[workspace_id]["label"], page["breadcrumb"])
                    self.assertGreaterEqual(len(page["breadcrumb"]), 2)
                    self.assertNotEqual(page["primaryObject"], page["primaryAction"])
                    self.assertNotEqual(page["emptyState"], page["errorState"])
                    self.assertIn("真实", page["emptyState"])
                    self.assertTrue(page["errorState"].startswith("无法"))
                    self.assertTrue(page["dataSource"])
                    self.assertGreaterEqual(len(page["sections"]), 3)
                    if page.get("legacyAliases"):
                        self.assertTrue(any(section["kind"] == "compat" for section in page["sections"]))
                    signature = (
                        page["layoutKind"],
                        page["primaryObject"],
                        page["primaryAction"],
                        tuple(section["kind"] for section in page["sections"]),
                    )
                    signatures.add(signature)
            self.assertEqual(len(signatures), len(pages))

    def test_phase43_shell_uses_combined_stage4_catalog_and_preserves_v01_alias_routes(self) -> None:
        shell_text = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        routes_payload = subprocess.run(
            [
                NODE,
                "-e",
                "const routes=require('./PFI/web/app/routes.js'); console.log(JSON.stringify(routes.legacyRouteAliasTargets));",
            ],
            cwd=ROOT.parent,
            check=True,
            text=True,
            capture_output=True,
        )
        legacy_targets = json.loads(routes_payload.stdout)
        catalog_text = json.dumps(load_stage4_pages(), ensure_ascii=False)

        self.assertIn("stage4SubpageCatalog", shell_text)
        self.assertIn("phase43Subpages", shell_text)
        for public_route, resolved_route in PHASE43_LEGACY_ALIAS_TARGETS.items():
            self.assertEqual(legacy_targets[public_route], resolved_route)
            self.assertIn(public_route, catalog_text)
            self.assertIn(resolved_route, catalog_text)

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

    def test_phase42_evidence_exists_before_later_stage4_phase_or_upload(self) -> None:
        evidence_root = ROOT / "reports" / "pfi_v023" / "stage_4" / "phase_4_2"
        evidence_path = evidence_root / "evidence.json"
        changed_files_path = evidence_root / "changed_files.txt"
        terminal_log_path = evidence_root / "terminal.log"
        browser_validation_path = evidence_root / "browser_validation.json"
        screenshot_paths = [
            evidence_root / "screenshots" / "consumption_subpages.png",
            evidence_root / "screenshots" / "sync_subpages.png",
            evidence_root / "screenshots" / "insights_subpages.png",
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
        self.assertEqual(evidence["phase_id"], "V023-S4-P4.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertTrue(evidence["allowed_files_obeyed"])
        self.assertTrue(evidence["no_mock_financial_data"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(evidence["phase42_summary"]["workspaces"], ["consumption", "sync", "insights"])
        self.assertEqual(evidence["phase42_summary"]["subpage_count"], 15)
        self.assertTrue(evidence["phase42_summary"]["data_gate_integrated"])
        self.assertTrue(browser_validation["consumption_subpages_differentiated"])
        self.assertTrue(browser_validation["sync_subpages_differentiated"])
        self.assertTrue(browser_validation["insights_subpages_differentiated"])
        self.assertTrue(browser_validation["url_state_breadcrumb_title_changed"])
        self.assertTrue(browser_validation["empty_and_error_states_present"])
        self.assertTrue(browser_validation["data_gate_integrated"])
        self.assertEqual(browser_validation["console_errors"], [])
        self.assertIn("Stage 4 Phase 4.3 market/settings/recommendations subpages", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", evidence["explicitly_not_done"])

    def test_phase43_evidence_exists_before_stage4_review_or_upload(self) -> None:
        evidence_root = ROOT / "reports" / "pfi_v023" / "stage_4" / "phase_4_3"
        evidence_path = evidence_root / "evidence.json"
        changed_files_path = evidence_root / "changed_files.txt"
        terminal_log_path = evidence_root / "terminal.log"
        browser_validation_path = evidence_root / "browser_validation.json"
        screenshot_paths = [
            evidence_root / "screenshots" / "market_research_subpages.png",
            evidence_root / "screenshots" / "settings_subpages.png",
            evidence_root / "screenshots" / "recommendations_subpages.png",
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
        self.assertEqual(evidence["phase_id"], "V023-S4-P4.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertTrue(evidence["allowed_files_obeyed"])
        self.assertTrue(evidence["no_mock_financial_data"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(evidence["phase43_summary"]["workspaces"], ["market_research", "settings", "recommendations"])
        self.assertEqual(evidence["phase43_summary"]["subpage_count"], 14)
        self.assertEqual(evidence["phase43_summary"]["v01_compat_routes"], PHASE43_LEGACY_ALIAS_TARGETS)
        self.assertTrue(browser_validation["market_research_subpages_differentiated"])
        self.assertTrue(browser_validation["settings_subpages_differentiated"])
        self.assertTrue(browser_validation["recommendations_subpages_differentiated"])
        self.assertTrue(browser_validation["url_state_breadcrumb_title_changed"])
        self.assertTrue(browser_validation["empty_and_error_states_present"])
        self.assertTrue(browser_validation["v01_alias_routes_differentiated"])
        self.assertEqual(browser_validation["console_errors"], [])
        self.assertIn("Stage 4 whole-stage review and fixes", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload before Stage 4 review", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
