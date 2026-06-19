import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_agent_context_pack.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_agent_context_pack", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AgentContextPackTests(unittest.TestCase):
    def test_builds_fixed_agent_context_pack_from_derived_data(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            db = Path(temp_dir)
            (db / "data/derived/profile").mkdir(parents=True)
            (db / "data/derived/codex").mkdir(parents=True)
            (db / "data/processed/codex").mkdir(parents=True)
            (db / "data/derived/visualization").mkdir(parents=True)

            (db / "data/derived/profile/CORE_PROFILE.md").write_text(
                "\n".join(
                    [
                        "# Curated Core Profile",
                        "",
                        "## High-weight Core Personalization",
                        "",
                        "- 默认中文输出，复杂任务要给状态表和可验证结果。",
                        "  - importance: 高; validity: 长期; confidence: high; id: mem_a",
                    ]
                ),
                encoding="utf-8",
            )
            recommendations = {
                "schema_version": "codex_agent_recommendations.v1",
                "generated_at": "2026-06-17T10:26:01Z",
                "source": "real_codex_local_sessions_redacted_summary",
                "session_count": 2,
                "top_topics": [{"label": "真实数据", "count": 3}],
                "memory": {
                    "current": [
                        {
                            "id": "m1",
                            "title": "真实数据优先",
                            "statement": "不要使用 mock。",
                            "source": "real_codex_local_sessions",
                            "confidence": "high",
                            "importance": "高",
                            "reason": "测试信号。",
                            "evidence_count": 3,
                            "scope": "future agents",
                        }
                    ],
                    "added": [],
                    "modified": [],
                    "deleted": [],
                },
                "meta_data": {
                    "current": [
                        {
                            "id": "r1",
                            "title": "授权边界",
                            "statement": "写操作前确认授权。",
                            "source": "real_codex_local_sessions",
                            "confidence": "high",
                            "importance": "高",
                            "reason": "测试信号。",
                            "evidence_count": 2,
                            "scope": "future agents",
                        }
                    ],
                    "added": [],
                    "modified": [],
                    "deleted": [],
                },
            }
            (db / "data/derived/codex/codex_agent_recommendations.json").write_text(
                json.dumps(recommendations, ensure_ascii=False),
                encoding="utf-8",
            )
            (db / "data/processed/codex/codex_activity_snapshot.json").write_text(
                json.dumps(
                    {
                        "schema_version": "codex_activity_snapshot.v1",
                        "generated_at": "2026-06-17T10:26:01Z",
                        "source": "real_codex_local_data",
                        "backup_policy": "redacted_summary_only_no_raw_transcript_no_plaintext_secret",
                        "session_count": 2,
                        "message_count": 10,
                        "tool_call_count": 20,
                        "range_start": "2026-06-16",
                        "range_end": "2026-06-17",
                        "top_topics": [{"label": "真实数据", "count": 3}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (db / "data/derived/visualization/memory_atlas.json").write_text(
                json.dumps({"overview": {"node_count": 5, "edge_count": 7, "generated_at": "2026-06-17T10:26:02Z"}}, ensure_ascii=False),
                encoding="utf-8",
            )

            result = module.write_pack(db, module.DEFAULT_JSON_OUTPUT, module.DEFAULT_MARKDOWN_OUTPUT)
            payload = json.loads((db / "data/derived/agent_context/agent_context_pack.json").read_text(encoding="utf-8"))
            markdown = (db / "data/derived/agent_context/AGENT_CONTEXT.md").read_text(encoding="utf-8")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(payload["schema_version"], "agent_context_pack.v1")
        self.assertEqual(payload["behavior"]["session_count"], 2)
        self.assertGreaterEqual(len(payload["profile"]["core_profile_items"]), 1)
        self.assertEqual(payload["memory"]["current"][0]["title"], "真实数据优先")
        self.assertIn("Agent 启动规则", markdown)


if __name__ == "__main__":
    unittest.main()
