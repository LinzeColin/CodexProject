from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"

STAGE5_PHASE51_SECTIONS = (
    "financial_state",
    "money_location",
    "data_health",
    "recent_changes",
)

STAGE5_PHASE52_ACTION_SOURCES = (
    "data_status",
    "review_task",
)

HOME_FORBIDDEN_VISIBLE_TERMS = (
    "Task Pack",
    "运行边界",
    "AI 控制台",
    "反馈控制台",
    "证据抽屉",
    "系统能力",
)


def load_stage5_home(payload: dict[str, object] | None = None) -> dict[str, object]:
    module_path = ROOT / "web" / "app" / "pages" / "home.js"
    script = """
const home = require('./PFI/web/app/pages/home.js');
const payload = JSON.parse(process.argv[1] || '{}');
console.log(JSON.stringify({
  contract: home.buildStage5Phase51Contract(),
  phase52Contract: home.buildStage5Phase52Contract(),
  view: home.buildStage5HomeViewModel(payload),
}));
"""
    completed = subprocess.run(
        [NODE, "-e", script, json.dumps(payload or {}, ensure_ascii=False)],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    self_output = completed.stdout
    return json.loads(self_output)


class TestV023Stage5HomeExperience(unittest.TestCase):
    def test_phase51_home_module_and_contract_are_limited_to_home_information_architecture(self) -> None:
        module_path = ROOT / "web" / "app" / "pages" / "home.js"
        self.assertTrue(module_path.exists(), "Stage 5 Phase 5.1 home module is required")

        payload = load_stage5_home()
        contract = payload["contract"]

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 5")
        self.assertEqual(contract["phase_id"], "V023-S5-P5.1")
        self.assertEqual(contract["phase_name"], "首页信息架构")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["uses_stage2_data_state_machine"])
        self.assertEqual(tuple(contract["home_sections"]), STAGE5_PHASE51_SECTIONS)
        self.assertIn("PFI/web/app/pages/home.js", contract["allowed_files"])
        self.assertIn("PFI/tests/test_v023_stage5_home_experience.py", contract["allowed_files"])
        self.assertIn("Phase 5.2 下一步动作生成", contract["explicitly_not_done"])
        self.assertIn("Stage 6 核心财务指标 read model 接入", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase52_contract_is_limited_to_next_action_generation(self) -> None:
        payload = load_stage5_home()
        contract = payload["phase52Contract"]

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 5")
        self.assertEqual(contract["phase_id"], "V023-S5-P5.2")
        self.assertEqual(contract["phase_name"], "下一步动作")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(tuple(contract["action_sources"]), STAGE5_PHASE52_ACTION_SOURCES)
        self.assertIn("由数据状态生成动作", contract["tasks"])
        self.assertIn("由待复核生成动作", contract["tasks"])
        self.assertIn("动作可跳转", contract["tasks"])
        self.assertIn("阻断动作可解释", contract["tasks"])
        self.assertIn("Phase 5.3 去 AI 痕迹全量清理", contract["explicitly_not_done"])
        self.assertIn("Stage 6 核心财务指标 read model 接入", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase51_view_model_answers_the_four_home_information_questions_without_financial_shortcuts(self) -> None:
        metric_states = [
            {
                "metric_id": "net_worth_cny",
                "label": "净资产",
                "value": None,
                "currency": "CNY",
                "status": "not_loaded",
                "source": None,
                "as_of": None,
                "evidence_hash": None,
                "message_zh": "未加载真实数据",
            },
            {
                "metric_id": "cash_balance_cny",
                "label": "现金余额",
                "value": 3200.5,
                "currency": "CNY",
                "status": "ready",
                "source": "read_model:cash",
                "as_of": "2026-06-30T09:00:00+10:00",
                "evidence_hash": "sha256:cash-real",
                "message_zh": "真实数据已加载",
            },
            {
                "metric_id": "investment_market_value_cny",
                "label": "投资市值",
                "value": None,
                "currency": "CNY",
                "status": "path_error",
                "source": None,
                "as_of": None,
                "evidence_hash": None,
                "message_zh": "数据路径不可用",
            },
        ]

        payload = load_stage5_home({"metric_states": metric_states, "recent_changes": []})
        view = payload["view"]

        self.assertEqual(view["schema"], "PFIV023Stage5HomeExperienceV1")
        self.assertEqual(view["phase_id"], "V023-S5-P5.1")
        self.assertEqual(tuple(section["id"] for section in view["sections"]), STAGE5_PHASE51_SECTIONS)
        self.assertEqual([card["metric_id"] for card in view["financial_state"]], [item["metric_id"] for item in metric_states])
        rendered_text = json.dumps(view, ensure_ascii=False)
        self.assertIn("CNY 3,200.50", rendered_text)
        self.assertIn("未加载真实数据", rendered_text)
        self.assertIn("数据路径不可用", rendered_text)
        self.assertNotIn("CNY 0.00", rendered_text)
        self.assertIn("现金余额", {item["label"] for item in view["money_location"]})
        self.assertTrue(view["data_health"]["uses_stage2_statuses"])
        self.assertEqual(view["recent_changes"][0]["state"], "empty")
        self.assertIn("真实变化记录", view["recent_changes"][0]["message"])

    def test_phase52_next_actions_are_generated_from_data_status_and_review_tasks(self) -> None:
        payload = load_stage5_home(
            {
                "metric_states": [
                    {
                        "metric_id": "net_worth_cny",
                        "label": "净资产",
                        "value": None,
                        "currency": "CNY",
                        "status": "not_mounted",
                        "source": None,
                        "as_of": None,
                        "evidence_hash": None,
                        "message_zh": "真实数据源未挂链",
                    },
                    {
                        "metric_id": "cash_balance_cny",
                        "label": "现金余额",
                        "value": None,
                        "currency": "CNY",
                        "status": "review_required",
                        "source": "read_model:cash",
                        "as_of": "2026-06-30T09:00:00+10:00",
                        "evidence_hash": "sha256:cash-review",
                        "message_zh": "需要人工复核",
                    },
                    {
                        "metric_id": "investment_market_value_cny",
                        "label": "投资市值",
                        "value": 1100,
                        "currency": "CNY",
                        "status": "ready",
                        "source": "read_model:holdings",
                        "as_of": "2026-06-30T09:00:00+10:00",
                        "evidence_hash": "sha256:holdings",
                        "message_zh": "真实数据已加载",
                    },
                ],
                "review_tasks": [
                    {
                        "task_id": "ledger-review-001",
                        "label": "复核低置信度流水",
                        "reason": "有 3 条流水需要人工确认分类",
                        "routeAlias": "/ledger?tab=review",
                        "targetWorkspace": "ledger",
                        "evidence_count": 3,
                    }
                ],
            }
        )
        view = payload["view"]
        actions = view["next_actions"]
        action_sources = {action["source_type"] for action in actions}

        self.assertIn("data_status", action_sources)
        self.assertIn("review_task", action_sources)
        self.assertTrue(all(action["routeAlias"].startswith("/") for action in actions))
        self.assertTrue(all(action["targetWorkspace"] for action in actions))
        self.assertTrue(all(action["explanation_zh"] for action in actions))
        self.assertTrue(all(action["generated_from"] for action in actions))

        data_actions = [action for action in actions if action["source_type"] == "data_status"]
        review_actions = [action for action in actions if action["source_type"] == "review_task"]

        self.assertEqual({action["source_metric_id"] for action in data_actions}, {"net_worth_cny", "cash_balance_cny"})
        self.assertTrue(any(action["blocked"] and "真实数据源未挂链" in action["explanation_zh"] for action in data_actions))
        self.assertEqual(review_actions[0]["source_task_id"], "ledger-review-001")
        self.assertEqual(review_actions[0]["routeAlias"], "/ledger?tab=review")
        self.assertEqual(review_actions[0]["targetWorkspace"], "ledger")
        self.assertIn("3 条流水", review_actions[0]["explanation_zh"])

    def test_phase52_next_actions_drive_home_tasks_and_action_cards(self) -> None:
        payload = load_stage5_home(
            {
                "metric_states": [
                    {
                        "metric_id": "month_spend_cny",
                        "label": "本月支出",
                        "value": None,
                        "currency": "CNY",
                        "status": "parse_error",
                        "source": None,
                        "as_of": None,
                        "evidence_hash": None,
                        "message_zh": "解析失败，请检查文件、行或字段",
                    }
                ],
                "review_tasks": [],
            }
        )
        view = payload["view"]

        self.assertGreaterEqual(len(view["next_actions"]), 1)
        self.assertEqual(view["next_actions"][0]["routeAlias"], "/sources-upload?tab=review")
        self.assertIn("解析失败", view["next_actions"][0]["explanation_zh"])
        self.assertIn("下一步动作", [card["title"] for card in view["home_features"]])
        self.assertTrue(any(task["source_type"] == "data_status" for task in view["home_tasks"]))
        self.assertNotIn("写死", json.dumps(view["next_actions"], ensure_ascii=False))

    def test_phase51_shell_loads_home_module_before_rendering_home(self) -> None:
        shell_text = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn("./app/pages/home.js", shell_text)
        self.assertIn("PFI_V023_STAGE5_HOME", shell_text)
        self.assertIn("applyStage5Phase51Home", shell_text)

    def test_phase51_home_surface_does_not_show_forbidden_home_artifacts(self) -> None:
        payload = load_stage5_home()
        visible_text = json.dumps(payload["view"], ensure_ascii=False)

        for term in HOME_FORBIDDEN_VISIBLE_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term, visible_text)
        for term in ("mo" + "ck", "sam" + "ple", "syn" + "thetic", "fix" + "ture", "de" + "mo", "fa" + "ke"):
            with self.subTest(term=term):
                self.assertNotIn(term, visible_text.lower())

    def test_phase51_doc_and_evidence_exist_before_candidate_pass(self) -> None:
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE5_HOME_EXPERIENCE.md"
        evidence_path = ROOT / "reports" / "pfi_v023" / "stage_5" / "phase_5_1" / "evidence.json"
        changed_files_path = ROOT / "reports" / "pfi_v023" / "stage_5" / "phase_5_1" / "changed_files.txt"
        terminal_log_path = ROOT / "reports" / "pfi_v023" / "stage_5" / "phase_5_1" / "terminal.log"

        self.assertTrue(doc_path.exists(), "Stage 5 home experience doc is required")
        self.assertTrue(evidence_path.exists(), "Stage 5 Phase 5.1 evidence is required")
        self.assertTrue(changed_files_path.exists(), "Stage 5 Phase 5.1 changed files record is required")
        self.assertTrue(terminal_log_path.exists(), "Stage 5 Phase 5.1 terminal log is required")

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 5")
        self.assertEqual(evidence["phase_id"], "V023-S5-P5.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertTrue(evidence["no_forbidden_financial_data"])
