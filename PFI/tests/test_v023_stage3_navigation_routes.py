from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"

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

V01_ALIAS_LABELS = {"首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"}


class PFIHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._stack: list[dict[str, str]] = []
        self._active_button: dict[str, str] | None = None
        self._active_button_depth = 0
        self._aria_hidden_depth = 0
        self.primary_entries: list[dict[str, str]] = []
        self.mobile_entries: list[dict[str, str]] = []
        self.stylesheets: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "link" and data.get("rel") == "stylesheet":
            self.stylesheets.append(data.get("href", ""))
        if tag == "script" and data.get("src"):
            self.scripts.append(data["src"])
        if tag == "button" and data.get("data-primary-entry") == "true":
            self._active_button = {"kind": "primary", **data, "text": ""}
            self._active_button_depth = 1
            self._stack.append(self._active_button)
            return
        if tag == "button" and data.get("data-mobile-primary-entry") == "true":
            self._active_button = {"kind": "mobile", **data, "text": ""}
            self._active_button_depth = 1
            self._stack.append(self._active_button)
            return
        if self._active_button is not None:
            self._active_button_depth += 1
            if data.get("aria-hidden") == "true":
                self._aria_hidden_depth += 1
        self._stack.append({"kind": "", "text": ""})

    def handle_data(self, data: str) -> None:
        if self._active_button is not None and self._aria_hidden_depth == 0:
            self._active_button["text"] += data
        elif self._stack and self._active_button is None:
            self._stack[-1]["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        item = self._stack.pop()
        if self._active_button is not None:
            if self._aria_hidden_depth > 0:
                self._aria_hidden_depth -= 1
            self._active_button_depth -= 1
        if tag != "button":
            return
        if item.get("kind") == "primary":
            self.primary_entries.append(_clean_entry(item))
        if item.get("kind") == "mobile":
            self.mobile_entries.append(_clean_entry(item))
        if self._active_button_depth <= 0:
            self._active_button = None
            self._active_button_depth = 0


def _clean_entry(item: dict[str, str]) -> dict[str, str]:
    clean = dict(item)
    clean["text"] = " ".join(clean.get("text", "").split())
    return clean


def parse_index() -> PFIHTMLParser:
    parser = PFIHTMLParser()
    parser.feed((ROOT / "web" / "index.html").read_text(encoding="utf-8"))
    return parser


class TestV023Stage3NavigationRoutes(unittest.TestCase):
    def test_phase31_static_nav_has_exactly_10_primary_entries_in_taskpack_order(self) -> None:
        parser = parse_index()
        labels = [entry["text"] for entry in parser.primary_entries]
        workspaces = [entry["data-workspace"] for entry in parser.primary_entries]
        routes = [entry["data-route-alias"] for entry in parser.primary_entries]
        indexes = [entry["data-nav-index"] for entry in parser.primary_entries]

        self.assertEqual(labels, OFFICIAL_PRIMARY_LABELS)
        self.assertEqual(workspaces, OFFICIAL_PRIMARY_WORKSPACES)
        self.assertEqual(routes, OFFICIAL_PRIMARY_ROUTES)
        self.assertEqual(indexes, [str(item) for item in range(1, 11)])
        self.assertEqual(len(labels), 10)

    def test_phase31_v01_aliases_are_not_top_level_primary_entries(self) -> None:
        parser = parse_index()
        primary_labels = {entry["text"] for entry in parser.primary_entries}

        self.assertFalse(V01_ALIAS_LABELS & primary_labels)
        self.assertIn("市场与研究", primary_labels)
        self.assertEqual(parser.primary_entries[8]["text"], "市场与研究")

    def test_phase31_mobile_primary_entries_match_desktop_contract(self) -> None:
        parser = parse_index()
        labels = [entry["text"] for entry in parser.mobile_entries]
        workspaces = [entry["data-mobile-workspace"] for entry in parser.mobile_entries]
        routes = [entry["data-route-alias"] for entry in parser.mobile_entries]

        self.assertEqual(labels, OFFICIAL_PRIMARY_LABELS)
        self.assertEqual(workspaces, OFFICIAL_PRIMARY_WORKSPACES)
        self.assertEqual(routes, OFFICIAL_PRIMARY_ROUTES)
        self.assertEqual(len(labels), 10)
        self.assertNotIn("更多", labels)

    def test_phase31_routes_module_matches_static_html_contract(self) -> None:
        parser = parse_index()

        self.assertIn("./app/routes.js", parser.scripts)
        script = """
const routes = require('./PFI/web/app/routes.js');
console.log(JSON.stringify(routes.officialPrimaryEntries));
"""
        completed = subprocess.run(
            [NODE, "-e", script],
            cwd=ROOT.parent,
            check=True,
            text=True,
            capture_output=True,
        )
        payload = json.loads(completed.stdout)

        self.assertEqual([item["label"] for item in payload], OFFICIAL_PRIMARY_LABELS)
        self.assertEqual([item["workspace"] for item in payload], OFFICIAL_PRIMARY_WORKSPACES)
        self.assertEqual([item["routeAlias"] for item in payload], OFFICIAL_PRIMARY_ROUTES)

    def test_phase31_stage_evidence_exists_before_stage_review_or_upload(self) -> None:
        evidence_path = ROOT / "reports" / "pfi_v023" / "stage_3" / "phase_3_1" / "evidence.json"
        changed_files_path = ROOT / "reports" / "pfi_v023" / "stage_3" / "phase_3_1" / "changed_files.txt"
        terminal_log_path = ROOT / "reports" / "pfi_v023" / "stage_3" / "phase_3_1" / "terminal.log"
        browser_validation_path = ROOT / "reports" / "pfi_v023" / "stage_3" / "phase_3_1" / "browser_validation.json"
        screenshot_path = ROOT / "reports" / "pfi_v023" / "stage_3" / "phase_3_1" / "screenshots" / "primary_nav.png"

        self.assertTrue(evidence_path.exists())
        self.assertTrue(changed_files_path.exists())
        self.assertTrue(terminal_log_path.exists())
        self.assertTrue(browser_validation_path.exists())
        self.assertTrue(screenshot_path.exists())

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        browser_validation = json.loads(browser_validation_path.read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in changed_files_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 3")
        self.assertEqual(evidence["phase_id"], "V023-S3-P3.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(browser_validation["desktop_primary_count_is_10"])
        self.assertTrue(browser_validation["mobile_primary_count_is_10"])
        self.assertTrue(browser_validation["active_state_updates"])
        self.assertEqual(browser_validation["console_errors"], [])
        self.assertIn("Stage 3 review not run", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
