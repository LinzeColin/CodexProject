import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from .memory_test_support import write_canonical_memory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_memory_atlas_data.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_memory_atlas_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MemoryAtlasDataTests(unittest.TestCase):
    def test_source_date_epoch_is_deterministic_and_fail_closed(self):
        module = load_module()
        with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1784155570"}):
            first = module.build_timestamp()
            second = module.build_timestamp()
        self.assertEqual(first, second)
        self.assertEqual(first.isoformat(), "2026-07-15T22:46:10+00:00")

        with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "not-an-integer"}):
            with self.assertRaisesRegex(ValueError, "integer Unix timestamp"):
                module.build_timestamp()

    def test_builds_read_only_galaxy_contract_and_contribution(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as td:
            db = Path(td)
            active_path = db / "data/memory/active/active_memory.jsonl"
            write_jsonl(
                active_path,
                [
                    {
                        "id": "mem_core_0000",
                        "date": "2026-06-10",
                        "statement": "PRIVATE CORE DETAIL 默认交互方式应优先使用编号选择题、多选矩阵、当前步骤状态表。",
                        "memory_tier": "核心画像",
                        "category": "answering_rule",
                        "importance": "高",
                        "validity": "长期",
                        "confidence": "high",
                        "sensitivity": "private",
                        "retrieval_weight": "high",
                        "evidence": [{"source": "raw should not be copied"}],
                        "conversation_id": "conversation-1",
                    },
                    {
                        "id": "mem_codex_0000",
                        "date": "2026-06-12",
                        "statement": "Codex workflow 需要低上下文、高 ROI、可验证、可恢复。",
                        "memory_tier": "一般",
                        "category": "workflow",
                        "importance": "中",
                        "validity": "项目结束前",
                        "confidence": "medium",
                        "sensitivity": "private",
                        "retrieval_weight": "medium",
                    },
                    {
                        "id": "mem_short_0000",
                        "date": "2026-06-12",
                        "statement": "短期/敏感资料包含不应进入静态图谱的敏感原文 SECRET DETAIL；redacted_source_hash=abc123。",
                        "memory_tier": "临时",
                        "category": "temporary_or_sensitive",
                        "importance": "低",
                        "validity": "临时",
                        "confidence": "high",
                        "sensitivity": "sensitive",
                        "retrieval_weight": "low",
                    },
                ],
            )
            write_jsonl(
                db / "data/processed/conversations/conversation_manifest.jsonl",
                [
                    {
                        "conversation_id": "c1",
                        "created_at": "2026-06-10T00:00:00Z",
                        "updated_at": "2026-06-10T01:00:00Z",
                        "message_count": 8,
                        "user_message_count": 4,
                        "assistant_message_count": 4,
                    }
                ],
            )
            write_jsonl(
                db / "data/processed/codex/codex_session_manifest.jsonl",
                [
                    {
                        "session_id": "codex-session-1",
                        "thread_name": "Memory Atlas 真实 Codex 数据同步",
                        "day": "2026-06-13",
                        "updated_at": "2026-06-13T01:00:00Z",
                        "message_count": 18,
                        "user_message_count": 9,
                        "assistant_message_count": 9,
                        "tool_call_count": 7,
                        "error_event_count": 1,
                        "abort_count": 0,
                        "activity_score": 61,
                        "topics": [{"id": "codex_local", "label": "Codex 本地数据 / agent 工作流", "count": 3}],
                        "preference_signals": [{"id": "real_data_required", "label": "偏好真实数据和可验证证据，反感 mock/伪进度", "count": 2}],
                        "top_tools": [{"name": "functions.exec_command", "count": 7}],
                    }
                ],
            )
            write_jsonl(
                db / "data/processed/codex/codex_daily_activity.jsonl",
                [
                    {
                        "date": "2026-06-13",
                        "conversation_count": 1,
                        "message_count": 18,
                        "user_message_count": 9,
                        "assistant_message_count": 9,
                        "tool_call_count": 7,
                        "error_event_count": 1,
                        "abort_count": 0,
                        "activity_score": 61,
                        "activity_level": 5,
                    }
                ],
            )
            (db / "data/derived/codex").mkdir(parents=True)
            (db / "data/derived/codex/codex_agent_recommendations.json").write_text(
                json.dumps(
                    {
                        "schema_version": "codex_agent_recommendations.v1",
                        "session_count": 1,
                        "memory": {
                            "current": [
                                {
                                    "id": "codex_signal_real_data_required",
                                    "title": "真实数据优先",
                                    "statement": "用户明确要求使用真实 Codex 数据，不接受 mock。",
                                    "evidence_count": 2,
                                    "confidence": "medium",
                                    "importance": "中",
                                }
                            ],
                            "added": [],
                            "modified": [],
                            "deleted": [],
                        },
                        "meta_data": {
                            "current": [],
                            "added": [],
                            "modified": [],
                            "deleted": [],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            write_jsonl(
                db / "data/memory/candidates/run_20260610T000000Z.memory_candidates.jsonl",
                [
                    {
                        "id": "mem_candidate_old",
                        "date": "2026-06-10",
                        "category": "decision",
                    }
                ],
            )
            latest_candidate_path = db / "data/memory/candidates/run_20260612T000000Z.memory_candidates.jsonl"
            write_jsonl(
                latest_candidate_path,
                [
                    {
                        "id": "mem_candidate_new_1",
                        "date": "2026-06-12",
                        "category": "workflow",
                    },
                    {
                        "id": "mem_candidate_new_2",
                        "date": "2026-06-12",
                        "category": "workflow",
                    },
                ],
            )
            os.utime(latest_candidate_path, (1, 1))
            canonical_rows = [json.loads(line) for line in active_path.read_text(encoding="utf-8").splitlines()]
            canonical_rows.extend(
                {
                    **json.loads(line),
                    "status": "candidate",
                    "statement": json.loads(line).get("statement") or "Canonical candidate fixture",
                }
                for line in latest_candidate_path.read_text(encoding="utf-8").splitlines()
            )
            active_path = write_canonical_memory(db, canonical_rows)
            (db / "data/derived/project_index").mkdir(parents=True)
            (db / "data/derived/project_index/PROJECT_INDEX.md").write_text("# Project Index\n", encoding="utf-8")
            (db / "data/derived/decision_log").mkdir(parents=True)
            (db / "data/derived/decision_log/DECISION_LOG.md").write_text("# Decision Log\n", encoding="utf-8")
            (db / "data/derived/timeline").mkdir(parents=True)
            (db / "data/derived/timeline/TIMELINE.md").write_text("# Timeline\n", encoding="utf-8")

            before_hash = sha256_file(active_path)
            atlas = module.build_memory_atlas(db)
            after_hash = sha256_file(active_path)

        self.assertEqual(before_hash, after_hash)
        self.assertEqual(atlas["schema_version"], "memory_atlas.v1")
        self.assertEqual(atlas["overview"]["active_memory_count"], 3)
        self.assertEqual(atlas["overview"]["codex_session_count"], 1)
        self.assertEqual(atlas["overview"]["candidate_count_latest_snapshot"], 2)
        self.assertEqual(atlas["source_contract"]["mode"], "public_redacted_read_only_visualization")
        self.assertEqual(atlas["source_contract"]["export_profile"], "access_preview")
        self.assertTrue(atlas["source_contract"]["writeback_policy"]["frontend_can_request_writeback"])
        self.assertTrue(atlas["source_contract"]["writeback_policy"]["writeback_must_use_proposals"])
        self.assertFalse(atlas["source_contract"]["writeback_policy"]["direct_frontend_mutation_of_active_memory"])
        self.assertIn("conflict_detection", atlas["source_contract"]["writeback_policy"])
        self.assertNotIn("database_dir", atlas["source_contract"])
        self.assertNotIn("source_hashes", atlas["source_contract"])
        self.assertIn("galaxy", atlas["visual_layers"]["primary"])
        self.assertGreaterEqual(atlas["overview"]["node_count"], 3)
        self.assertGreaterEqual(atlas["overview"]["edge_count"], 3)
        daily = {row["date"]: row for row in atlas["contribution"]["daily"]}
        self.assertEqual(daily["2026-06-10"]["conversation_count"], 1)
        self.assertEqual(daily["2026-06-10"]["candidate_count"], 0)
        self.assertEqual(daily["2026-06-10"]["core_memory_count"], 1)
        self.assertIn("2026-06-11", daily)
        self.assertEqual(daily["2026-06-11"]["activity_level"], 0)
        self.assertEqual(daily["2026-06-12"]["candidate_count"], 2)
        self.assertEqual(daily["2026-06-13"]["tool_call_count"], 7)
        self.assertEqual(daily["2026-06-13"]["codex_session_count"], 1)
        self.assertIn("codex", {source["id"] for source in atlas["data_sources"]})
        self.assertEqual(atlas["agent_recommendations"]["session_count"], 1)
        codex_node = next(node for node in atlas["nodes"] if node.get("data_source") == "codex")
        self.assertEqual(codex_node["source_label"], "Codex 本地数据")
        self.assertIn("真实 Codex", codex_node["statement"])
        memory_node = next(node for node in atlas["nodes"] if node.get("memory_id") == "mem_core_0000")
        self.assertIn("核心画像 ·", memory_node["label"])
        self.assertIn("·", memory_node["label"])
        self.assertNotIn("proposal_ref", memory_node)
        self.assertNotIn("statement_policy", memory_node)
        self.assertNotIn("source_kind", memory_node)
        self.assertNotIn("retrieval_weight", memory_node)
        self.assertNotIn("sensitivity", memory_node)
        self.assertNotIn("evidence_count", memory_node)
        self.assertNotIn("source_ref", memory_node)
        self.assertNotIn("conversation_ref", memory_node)
        self.assertTrue(all("source_file" not in node for node in atlas["nodes"]))
        self.assertIn("roi", memory_node["metrics"])
        self.assertNotIn("retrieval_weight_score", memory_node["metrics"]["roi"])
        self.assertNotIn("sensitivity_penalty", memory_node["metrics"]["roi"])
        serialized = json.dumps(atlas, ensure_ascii=False)
        self.assertNotIn("PRIVATE CORE DETAIL", serialized)
        self.assertNotIn("SECRET DETAIL", serialized)
        self.assertNotIn("raw should not be copied", serialized)
        self.assertNotIn("\"evidence\"", serialized)
        self.assertNotIn("record_hash", serialized)
        self.assertNotIn("source_snapshot_hash", serialized)
        self.assertNotIn("record_index", serialized)
        self.assertNotIn("\"source_file\"", serialized)
        self.assertNotIn("json_pointer", serialized)

    def test_data_source_registry_keeps_future_sources_out_of_homepage_selector(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as td:
            db = Path(td)
            write_jsonl(
                db / "data/memory/active/active_memory.jsonl",
                [
                    {
                        "id": "mem_fixture_0001",
                        "date": "2026-06-10",
                        "statement": "Memory Atlas 需要作为多数据源可视化平台。",
                        "memory_tier": "核心画像",
                        "category": "project_context",
                        "importance": "高",
                        "validity": "长期",
                        "confidence": "high",
                        "sensitivity": "low",
                    }
                ],
            )
            registry = json.loads((ROOT / "config/data_sources/source_registry.json").read_text(encoding="utf-8"))
            write_json(db / "config/data_sources/source_registry.json", registry)
            write_canonical_memory(
                db,
                [json.loads(line) for line in (db / "data/memory/active/active_memory.jsonl").read_text(encoding="utf-8").splitlines()],
            )

            atlas = module.build_memory_atlas(db)

        source_by_id = {source["id"]: source for source in atlas["data_sources"]}
        self.assertEqual([source["id"] for source in atlas["data_sources"]], ["all", "memory_atlas", "codex"])
        self.assertEqual(source_by_id["all"]["label"], "总数据源")
        self.assertEqual(source_by_id["memory_atlas"]["label"], "ChatGPT")
        self.assertEqual(source_by_id["codex"]["label"], "Codex")
        for source_id in ["wechat", "xiaohongshu", "douyin"]:
            self.assertNotIn(source_id, source_by_id)
            self.assertFalse(any(node.get("data_source") == source_id for node in atlas["nodes"]))
        registry_contract = atlas["source_contract"]["data_source_registry"]
        self.assertIn("wechat", registry_contract["planned_source_ids"])
        self.assertIn("source_id", registry_contract["canonical_required_fields"])
        self.assertIn("fake", registry_contract["mock_policy"])

    def test_cli_writes_output(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as td:
            db = Path(td)
            write_jsonl(
                db / "data/memory/active/active_memory.jsonl",
                [
                    {
                        "id": "mem_fixture_0001",
                        "date": "2026-06-10",
                        "statement": "OpenAIDatabase 是长期记忆数据库。",
                        "memory_tier": "核心画像",
                        "category": "project_context",
                        "importance": "高",
                        "validity": "长期",
                        "confidence": "high",
                        "sensitivity": "private",
                    }
                ],
            )
            write_canonical_memory(
                db,
                [json.loads(line) for line in (db / "data/memory/active/active_memory.jsonl").read_text(encoding="utf-8").splitlines()],
            )
            out = db / "atlas.json"
            result = module.main(["--database-dir", str(db), "--output", str(out)])
            self.assertEqual(result, 0)
            self.assertTrue(out.exists())
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["overview"]["memory_node_count"], 1)
            first_generated_at = data["overview"]["generated_at"]
            os.utime(out, (1, 1))
            time.sleep(0.02)
            second_result = module.main(["--database-dir", str(db), "--output", str(out)])
            self.assertEqual(second_result, 0)
            refreshed = json.loads(out.read_text(encoding="utf-8"))
            self.assertNotEqual(refreshed["overview"]["generated_at"], first_generated_at)
            self.assertNotEqual(out.stat().st_mtime, 1)


if __name__ == "__main__":
    unittest.main()
