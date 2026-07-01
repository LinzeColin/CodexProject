from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"

HOME_QUESTION_IDS = ("money", "location", "change", "problems", "next_step", "evidence")
HOME_QUESTION_TITLES = ("钱", "位置", "变化", "问题", "下一步", "依据")
MECHANICAL_HOME_TERMS = ("功能面板", "PFI 功能入口", "功能已准备", "进入操作面板")


def load_v024_home(payload: dict[str, object] | None = None) -> dict[str, object]:
    script = """
const home = require('./PFI/web/app/pages/home.js');
const payload = JSON.parse(process.argv[1] || '{}');
console.log(JSON.stringify({
  contract: home.buildV024Stage5Phase51Contract(),
  view: home.buildV024Stage5Phase51HomeViewModel(payload),
}));
"""
    completed = subprocess.run(
        [NODE, "-e", script, json.dumps(payload or {}, ensure_ascii=False)],
        cwd=ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage5Phase51HomeRebuild(unittest.TestCase):
    def test_phase51_contract_is_v024_home_rebuild_only(self) -> None:
        payload = load_v024_home()
        contract = payload["contract"]

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 5")
        self.assertEqual(contract["phase_id"], "5.1")
        self.assertEqual(contract["phase_name"], "首页重建")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(tuple(contract["home_question_ids"]), HOME_QUESTION_IDS)
        self.assertIn("T5.1.1 首页只保留六个核心问题", contract["tasks"])
        self.assertIn("T5.1.2 移除功能面板机械层", contract["tasks"])
        self.assertIn("T5.1.3 增加下一步任务流", contract["tasks"])
        self.assertIn("T5.1.4 接入数据状态卡", contract["tasks"])
        self.assertIn("Phase 5.2 二级页面差异化", contract["explicitly_not_done"])
        self.assertIn("Phase 5.3 交互状态", contract["explicitly_not_done"])
        self.assertIn("Stage 5 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])

    def test_home_view_answers_six_questions_from_stage4_read_model_status(self) -> None:
        read_model_path = ROOT / "reports" / "pfi_v024" / "stage_4" / "phase_4_2" / "read_model_status.json"
        read_model_status = json.loads(read_model_path.read_text(encoding="utf-8"))
        payload = load_v024_home({"read_model_status": read_model_status})
        view = payload["view"]

        self.assertEqual(view["schema"], "PFIV024Stage5Phase51HomeViewV1")
        self.assertEqual(view["target_version"], "v0.2.4")
        self.assertEqual(view["source_package_version"], "v0.2.3-repair")
        self.assertEqual(view["phase_id"], "5.1")
        self.assertEqual(tuple(item["id"] for item in view["questions"]), HOME_QUESTION_IDS)
        self.assertEqual(tuple(item["title"] for item in view["questions"]), HOME_QUESTION_TITLES)

        rendered = json.dumps(view, ensure_ascii=False)
        self.assertIn("MetaDatabase/PFI", rendered)
        self.assertIn("8815", rendered)
        self.assertIn("2026-06-03", rendered)
        self.assertIn("未挂链账户余额与持仓 read model，无法计算净资产", rendered)
        self.assertIn("CNY 1,727,278.37", rendered)
        self.assertNotIn("CNY 0.00", rendered)

        self.assertEqual(view["data_state_cards"][0]["surface"], "home")
        self.assertGreaterEqual(len(view["data_state_cards"][0]["metrics"]), 5)
        self.assertTrue(view["next_task_flow"])
        self.assertTrue(all(item["routeAlias"].startswith("/") for item in view["next_task_flow"]))
        self.assertTrue(all(item["targetWorkspace"] for item in view["next_task_flow"]))

    def test_static_home_surface_removes_mechanical_layer_and_loads_home_module(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

        self.assertIn('data-v024-stage5-home="phase_5_1"', html)
        self.assertIn('data-home-question-grid', html)
        self.assertIn('data-home-state-card', html)
        self.assertIn('id="pfi-read-model-status"', html)
        self.assertLess(html.index("./app/pages/home.js"), html.index("./app/shell.js"))
        for title in HOME_QUESTION_TITLES:
            with self.subTest(title=title):
                self.assertIn(f">{title}<", html)
        for term in MECHANICAL_HOME_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term, html)

    def test_phase51_evidence_pack_exists_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v024" / "stage_5" / "phase_5_1"
        evidence_path = phase_dir / "evidence.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        risk_path = phase_dir / "risk_and_rollback.md"
        doc_path = ROOT / "docs" / "pfi_v024" / "STAGE5_HOME_REBUILD.md"

        for path in (evidence_path, changed_files_path, terminal_log_path, risk_path, doc_path):
            with self.subTest(path=path.name):
                self.assertTrue(path.exists(), f"{path} is required")

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema"], "PFIV024Stage5Phase51EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 5")
        self.assertEqual(evidence["phase_id"], "5.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_5_1_complete"])
        self.assertFalse(evidence["phase_5_2_started"])
        self.assertFalse(evidence["phase_5_3_started"])
        self.assertFalse(evidence["stage_5_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertTrue(evidence["no_forbidden_financial_data"])


if __name__ == "__main__":
    unittest.main()
