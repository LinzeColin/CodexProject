import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/openai-memory-analysis/scripts/openai_memory_analysis.py"


def load_module():
    spec = importlib.util.spec_from_file_location("openai_memory_analysis", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OpenAIMemoryAnalysisTests(unittest.TestCase):
    def test_redaction_and_candidate_shape(self):
        module = load_module()
        token = "sk-" + "a" * 32
        cand = module.make_candidate(
            chunk=f"不要保存一次性 token api_key={token}",
            source="fixture",
            source_kind="fixture",
        )
        self.assertIsNotNone(cand)
        self.assertNotIn(token, json.dumps(cand, ensure_ascii=False))
        self.assertTrue(cand["date"])
        self.assertTrue(cand["source"])
        self.assertIn(cand["importance"], {"高", "中", "低"})
        self.assertIn(cand["validity"], {"长期", "半年", "项目结束前", "临时"})
        self.assertIn(cand["confidence"], {"high", "medium", "low"})
        self.assertTrue(cand["reason"])
        self.assertTrue(cand.get("secret_ref"))
        self.assertFalse(cand["credential_policy"]["plaintext_in_git"])

    def test_human_reports_include_dual_reviewer_passes(self):
        module = load_module()
        rows = [
            module.make_candidate(
                chunk="我希望以后默认中文输出，除专业术语外尽量全中文，目标是 ROI 最大化和个人能力成长最大化。",
                source="fixture",
                source_kind="fixture",
                timestamp=module.utc_now(),
            ),
            module.make_candidate(
                chunk="决定 OpenAIDatabase 作为长期记忆数据库，所有记忆都按核心画像、一般、临时三层备份。",
                source="fixture",
                source_kind="fixture",
                timestamp=module.utc_now(),
            ),
        ]
        rows = [row for row in rows if row]
        week_start = module.utc_now() - module.timedelta(days=1)
        human = module.build_human_memory_review(rows, [])
        weekly = module.build_weekly_report(rows, week_start)
        monthly = module.build_monthly_report(rows, module.utc_now().strftime("%Y-%m"))
        active_rows = module.build_active_memory_rows(rows, "run_fixture")
        chat = module.build_chat_report(rows, active_rows, rows[:1], week_start, module.utc_now().strftime("%Y-%m"))
        self.assertIn("本次资料内容结论", human)
        self.assertIn("本次资料与上一轮结论对比", human)
        self.assertIn("需要做什么", human)
        self.assertIn("潜在发展 / 投资 / 业务机会", human)
        self.assertIn("本周资料内容结论", weekly)
        self.assertIn("本周资料与上一轮结论对比", weekly)
        self.assertIn("本月资料内容结论", monthly)
        self.assertIn("本月资料与上一轮结论对比", monthly)
        self.assertIn("双 reviewer", human)
        self.assertIn("战略 / 机会 / ROI", weekly)
        self.assertIn("本月复盘面向用户", monthly)
        self.assertIn("本轮聊天框输出报告", chat)
        self.assertIn("周复盘", chat)
        self.assertIn("月复盘", chat)
        self.assertTrue(active_rows)
        self.assertIn("retrieval_weight", active_rows[0])
        self.assertNotIn("## Candidate:", weekly)

    def test_code_like_snippets_do_not_become_core_profile(self):
        module = load_module()
        cand = module.make_candidate(
            chunk="- 优先使用显式传入的 weights",
            source="fixture",
            source_kind="fixture",
            timestamp=module.utc_now(),
        )
        self.assertIsNotNone(cand)
        self.assertEqual(cand["memory_tier"], "临时")
        self.assertEqual(cand["importance"], "低")
        self.assertEqual(cand["validity"], "临时")
        self.assertEqual(
            module.normalized_memory_tier({"statement": "- 优先使用显式传入的 weights", "memory_tier": "核心画像"}),
            "临时",
        )

    def test_core_profile_curation_override(self):
        module = load_module()
        cand = module.make_candidate(
            chunk="默认交互方式：优先使用编号选择题、多选矩阵、默认推荐项、当前步骤状态表、下一步 A/B/C。",
            source="fixture",
            source_kind="fixture",
            timestamp=module.utc_now(),
        )
        self.assertIsNotNone(cand)
        with tempfile.TemporaryDirectory() as td:
            db_dir = Path(td)
            curation_dir = db_dir / "data/memory/curation"
            curation_dir.mkdir(parents=True)
            (curation_dir / "core_profile_review.json").write_text(
                json.dumps(
                    {
                        "overrides": {
                            cand["id"]: {
                                "status": "accepted_core_distilled",
                                "memory_tier": "核心画像",
                                "statement": "默认交互方式应优先使用结构化选择和步骤状态，避免大量自由文本输入。",
                                "review_reason": "测试覆盖人工审核蒸馏。",
                            }
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            active_rows = module.build_active_memory_rows([cand], "run_fixture", db_dir)
            self.assertEqual(active_rows[0]["memory_tier"], "核心画像")
            self.assertEqual(active_rows[0]["statement"], "默认交互方式应优先使用结构化选择和步骤状态，避免大量自由文本输入。")
            profile = module.build_core_profile_markdown(active_rows, module.load_curation_overrides(db_dir))
            self.assertIn("Curated Core Profile", profile)
            self.assertIn("结构化选择", profile)

    def test_self_test_cli(self):
        with tempfile.TemporaryDirectory() as td:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "self-test", "--out-dir", str(Path(td) / "self-test")],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        self.assertIn('"status": "PASS"', result.stdout)


if __name__ == "__main__":
    unittest.main()
