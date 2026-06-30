from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import unittest

import pfi_v02.stage_v024_stage3_navigation as navigation


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_3" / "phase_3_1"

OFFICIAL_PRIMARY_LABELS = [
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

OFFICIAL_PRIMARY_WORKSPACES = [
    "home",
    "accounts",
    "ledger",
    "investment",
    "consumption",
    "sync",
    "recommendations",
    "insights",
    "market_research",
    "settings",
]

OFFICIAL_PRIMARY_ROUTES = [
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

V01_ALIAS_CONTRACT = [
    {
        "taskId": "T3.1.2",
        "label": "首页",
        "targetWorkspace": "home",
        "routeAlias": "/home/today",
        "resolvedRouteAlias": "/home",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "市场",
        "targetWorkspace": "market_research",
        "routeAlias": "/market/watch",
        "resolvedRouteAlias": "/market-research?tab=market",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "研究",
        "targetWorkspace": "market_research",
        "routeAlias": "/market/research",
        "resolvedRouteAlias": "/market-research?tab=research",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "持仓",
        "targetWorkspace": "investment",
        "routeAlias": "/investment/holdings",
        "resolvedRouteAlias": "/investment?tab=holdings",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "策略实验室",
        "targetWorkspace": "market_research",
        "routeAlias": "/market/lab",
        "resolvedRouteAlias": "/market-research/strategy-lab",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
    {
        "taskId": "T3.1.2",
        "label": "数据与系统",
        "targetWorkspace": "settings",
        "routeAlias": "/settings/data",
        "resolvedRouteAlias": "/settings?tab=data-system",
        "aliasClass": "secondary_or_command_alias",
        "primaryEntryAllowed": False,
    },
]


class PFIHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._active_entry: dict[str, str] | None = None
        self._active_depth = 0
        self._aria_hidden_depth = 0
        self.primary_entries: list[dict[str, str]] = []
        self.mobile_entries: list[dict[str, str]] = []
        self.command_entries: list[dict[str, str]] = []
        self.no_js_links: list[dict[str, str]] = []
        self.scripts: list[str] = []
        self.body_attrs: dict[str, str] = {}
        self._noscript_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "body":
            self.body_attrs = data
        if tag == "script" and data.get("src"):
            self.scripts.append(data["src"])
        if tag == "noscript":
            self._noscript_depth += 1
        if tag == "button" and data.get("data-primary-entry") == "true":
            self._start_entry("primary", data)
            return
        if tag == "button" and data.get("data-mobile-primary-entry") == "true":
            self._start_entry("mobile", data)
            return
        if tag == "button" and data.get("data-command-route"):
            self._start_entry("command", data)
            return
        if tag == "a" and self._noscript_depth > 0 and data.get("data-no-js-route"):
            self._start_entry("no_js", data)
            return
        if self._active_entry is not None:
            self._active_depth += 1
            if data.get("aria-hidden") == "true":
                self._aria_hidden_depth += 1

    def handle_data(self, data: str) -> None:
        if self._active_entry is not None and self._aria_hidden_depth == 0:
            self._active_entry["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "noscript" and self._noscript_depth > 0:
            self._noscript_depth -= 1
        if self._active_entry is None:
            return
        if self._aria_hidden_depth > 0:
            self._aria_hidden_depth -= 1
        self._active_depth -= 1
        if self._active_depth > 0:
            return
        clean = dict(self._active_entry)
        clean["text"] = " ".join(clean["text"].split())
        kind = clean.pop("kind")
        if kind == "primary":
            self.primary_entries.append(clean)
        if kind == "mobile":
            self.mobile_entries.append(clean)
        if kind == "command":
            self.command_entries.append(clean)
        if kind == "no_js":
            self.no_js_links.append(clean)
        self._active_entry = None

    def _start_entry(self, kind: str, data: dict[str, str]) -> None:
        self._active_entry = {"kind": kind, **data, "text": ""}
        self._active_depth = 1


def parse_index() -> PFIHTMLParser:
    parser = PFIHTMLParser()
    parser.feed((ROOT / "web" / "index.html").read_text(encoding="utf-8"))
    return parser


def load_navigation_js_contract() -> dict[str, object]:
    script = """
const nav = require('./PFI/web/app/navigation.js');
console.log(JSON.stringify({
  ...nav,
  resolvedMarketAlias: nav.resolveLegacyRouteAlias('/market/watch'),
  resolvedAccountsRoute: nav.resolveLegacyRouteAlias('/accounts'),
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


class TestV024Stage3Phase31NavigationContract(unittest.TestCase):
    def test_phase31_python_contract_freezes_10_primary_entries_and_alias_policy(self) -> None:
        contract = navigation.build_v024_stage3_phase31_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 3")
        self.assertEqual(contract["phase_id"], "3.1")
        self.assertEqual(contract["phase_name"], "导航合同")
        self.assertEqual(contract["task_ids"], ["T3.1.1", "T3.1.2", "T3.1.3", "T3.1.4"])
        self.assertEqual([item["label"] for item in contract["official_primary_entries"]], OFFICIAL_PRIMARY_LABELS)
        self.assertEqual([item["workspace"] for item in contract["official_primary_entries"]], OFFICIAL_PRIMARY_WORKSPACES)
        self.assertEqual([item["routeAlias"] for item in contract["official_primary_entries"]], OFFICIAL_PRIMARY_ROUTES)
        self.assertEqual([item["index"] for item in contract["official_primary_entries"]], list(range(1, 11)))
        self.assertEqual(contract["legacy_alias_entries"], V01_ALIAS_CONTRACT)
        self.assertEqual(contract["active_state_rules"]["nav_index_sequence"], list(range(1, 11)))
        self.assertTrue(contract["active_state_rules"]["single_active_primary_entry"])
        self.assertFalse(contract["active_state_rules"]["legacy_alias_primary_entry_allowed"])
        self.assertTrue(contract["phase_3_1_complete"])
        self.assertFalse(contract["phase_3_2_complete"])
        self.assertFalse(contract["phase_3_3_complete"])
        self.assertFalse(contract["stage_3_candidate_complete"])
        self.assertFalse(contract["stage_3_complete"])
        self.assertFalse(contract["browser_history_validation_done"])
        self.assertFalse(contract["github_main_upload_allowed"])
        self.assertEqual(contract["max_phases_per_run"], 1)

    def test_phase31_navigation_js_exports_v024_contract_without_overwriting_v023_history(self) -> None:
        payload = load_navigation_js_contract()

        self.assertEqual(payload["version"], "v0.2.4")
        self.assertEqual(payload["sourcePackageVersion"], "v0.2.3-repair")
        self.assertEqual(payload["stage"], "Stage 3")
        self.assertEqual(payload["phaseId"], "3.1")
        self.assertEqual(payload["phaseName"], "导航合同")
        self.assertEqual([item["label"] for item in payload["officialPrimaryEntries"]], OFFICIAL_PRIMARY_LABELS)
        self.assertEqual([item["workspace"] for item in payload["officialPrimaryEntries"]], OFFICIAL_PRIMARY_WORKSPACES)
        self.assertEqual([item["routeAlias"] for item in payload["officialPrimaryEntries"]], OFFICIAL_PRIMARY_ROUTES)
        self.assertEqual(payload["legacyAliasEntries"], V01_ALIAS_CONTRACT)
        self.assertEqual(payload["resolvedMarketAlias"], "/market-research?tab=market")
        self.assertEqual(payload["resolvedAccountsRoute"], "/accounts")

    def test_phase31_static_html_loads_navigation_contract_and_keeps_only_10_primary_entries(self) -> None:
        parser = parse_index()

        self.assertEqual(parser.body_attrs["data-pfi-target-version"], "v0.2.4")
        self.assertEqual(parser.body_attrs["data-pfi-stage"], "Stage 3")
        self.assertEqual(parser.body_attrs["data-pfi-phase"], "3.1")
        self.assertIn("./app/navigation.js", parser.scripts)
        self.assertLess(parser.scripts.index("./app/navigation.js"), parser.scripts.index("./app/routes.js"))

        desktop_labels = [entry["text"] for entry in parser.primary_entries]
        desktop_workspaces = [entry["data-workspace"] for entry in parser.primary_entries]
        desktop_routes = [entry["data-route-alias"] for entry in parser.primary_entries]
        desktop_indexes = [entry["data-nav-index"] for entry in parser.primary_entries]
        mobile_labels = [entry["text"] for entry in parser.mobile_entries]

        self.assertEqual(desktop_labels, OFFICIAL_PRIMARY_LABELS)
        self.assertEqual(desktop_workspaces, OFFICIAL_PRIMARY_WORKSPACES)
        self.assertEqual(desktop_routes, OFFICIAL_PRIMARY_ROUTES)
        self.assertEqual(desktop_indexes, [str(index) for index in range(1, 11)])
        self.assertEqual(mobile_labels, OFFICIAL_PRIMARY_LABELS)
        self.assertEqual(len(desktop_labels), 10)
        self.assertEqual(len(mobile_labels), 10)
        self.assertEqual(parser.primary_entries[8]["text"], "市场与研究")
        self.assertFalse({"首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"} & set(desktop_labels))

    def test_phase31_legacy_entries_remain_as_command_aliases_not_peer_primary_entries(self) -> None:
        parser = parse_index()
        command_aliases = {
            entry["text"]: {
                "workspace": entry["data-command-workspace"],
                "routeAlias": entry["data-command-route"],
            }
            for entry in parser.command_entries
        }

        for alias in V01_ALIAS_CONTRACT:
            self.assertEqual(
                command_aliases[alias["label"]],
                {"workspace": alias["targetWorkspace"], "routeAlias": alias["routeAlias"]},
            )

        no_js_labels = [entry["text"] for entry in parser.no_js_links]
        self.assertEqual(no_js_labels, OFFICIAL_PRIMARY_LABELS)
        self.assertNotIn("市场", no_js_labels)
        self.assertNotIn("研究", no_js_labels)

    def test_phase31_streamlit_embed_inlines_navigation_before_routes_and_shell(self) -> None:
        streamlit_text = (ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

        self.assertIn('navigation_path = ROOT / "web" / "app" / "navigation.js"', streamlit_text)
        self.assertIn("navigation_js = navigation_path.read_text", streamlit_text)
        self.assertLess(streamlit_text.index("navigation_js"), streamlit_text.index("routes_js"))
        self.assertIn('<script src="./app/navigation.js"></script>', streamlit_text)

    def test_phase31_evidence_pack_exists_and_records_boundaries(self) -> None:
        evidence_path = EVIDENCE_DIR / "evidence.json"
        changed_files_path = EVIDENCE_DIR / "changed_files.txt"
        terminal_path = EVIDENCE_DIR / "terminal.log"
        risk_path = EVIDENCE_DIR / "risk_and_rollback.md"
        doc_path = ROOT / "docs" / "pfi_v024" / "STAGE3_NAVIGATION_ROUTING.md"

        for path in (evidence_path, changed_files_path, terminal_path, risk_path, doc_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage3Phase31NavigationEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 3")
        self.assertEqual(evidence["phase_id"], "3.1")
        self.assertEqual(evidence["phase_name"], "导航合同")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["acceptance_checks"]["official_primary_entries_count_is_10"])
        self.assertTrue(evidence["acceptance_checks"]["market_research_is_formal_primary"])
        self.assertTrue(evidence["acceptance_checks"]["v01_entries_are_alias_or_command_only"])
        self.assertTrue(evidence["acceptance_checks"]["no_bottom_or_sidebar_16_peer_entries"])
        self.assertFalse(evidence["phase_3_2_complete"])
        self.assertFalse(evidence["phase_3_3_complete"])
        self.assertFalse(evidence["stage_3_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 3 Phase 3.2 route implementation", evidence["explicitly_not_done"])
        self.assertIn("Stage 3 Phase 3.3 browser history validation", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
