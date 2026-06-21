import importlib.util
import json
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    script = ROOT / f"scripts/{name}.py"
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_minimal_database(root: Path) -> None:
    shutil.copytree(ROOT / ".codex", root / ".codex")
    shutil.copytree(ROOT / "config/context_sources", root / "config/context_sources")
    shutil.copytree(ROOT / "config/codex", root / "config/codex")
    shutil.copytree(ROOT / "config/evaluation", root / "config/evaluation")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "docs/PERSONAL_CONTEXT_ARCHITECTURE.md", root / "docs/PERSONAL_CONTEXT_ARCHITECTURE.md")
    shutil.copytree(ROOT / "data/run_logs", root / "data/run_logs")
    (root / "data/derived/profile").mkdir(parents=True, exist_ok=True)
    (root / "data/derived/profile/CORE_PROFILE.md").write_text(
        "\n".join(
            [
                "# Curated Core Profile",
                "",
                "## High-weight Core Personalization",
                "",
                "- 默认中文输出，复杂任务要给状态表和可验证结果。",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        root / "data/derived/codex/codex_agent_recommendations.json",
        {
            "schema_version": "codex_agent_recommendations.v1",
            "generated_at": "2026-06-21T00:00:00Z",
            "top_topics": [{"label": "Personalization", "count": 3}],
            "memory": {
                "current": [
                    {
                        "id": "m1",
                        "title": "真实数据优先",
                        "statement": "使用真实可验证证据。",
                        "confidence": "high",
                        "importance": "高",
                        "evidence_count": 3,
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
                        "title": "同步规则",
                        "statement": "profile/preference/taste/history/pattern 变化必须同步源文件。",
                        "confidence": "high",
                        "importance": "高",
                        "evidence_count": 2,
                    }
                ],
                "added": [],
                "modified": [],
                "deleted": [],
            },
        },
    )
    write_json(
        root / "data/processed/codex/codex_activity_snapshot.json",
        {
            "schema_version": "codex_activity_snapshot.v1",
            "generated_at": "2026-06-21T00:00:00Z",
            "source": "real_codex_local_data",
            "session_count": 1,
            "message_count": 2,
            "tool_call_count": 1,
            "range_start": "2026-06-20",
            "range_end": "2026-06-21",
            "top_topics": [{"label": "Personalization", "count": 3}],
        },
    )
    write_json(root / "data/derived/visualization/memory_atlas.json", {"overview": {"node_count": 1, "edge_count": 0}})


class PersonalizationArchitectureTests(unittest.TestCase):
    def test_runtime_codex_config_is_project_config_not_manifest(self) -> None:
        runtime_config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))

        self.assertEqual(runtime_config["project_doc_max_bytes"], 24576)
        self.assertFalse(runtime_config["features"]["memories"])
        self.assertFalse(runtime_config["sandbox_workspace_write"]["network_access"])
        self.assertNotIn("project", runtime_config)
        self.assertNotIn("personalization", runtime_config)
        self.assertNotIn("logs", runtime_config)
        self.assertNotIn("rules", runtime_config)

    def test_codex_toml_configs_parse_and_require_sync_targets(self) -> None:
        template = tomllib.loads((ROOT / "config/codex/config.template.toml").read_text(encoding="utf-8"))
        project = tomllib.loads((ROOT / "config/codex/project.config.toml").read_text(encoding="utf-8"))
        required = {"profile", "preference", "taste", "history", "pattern"}

        self.assertEqual(template["codex_user_config_template"]["manifest_kind"], "user_personalization_manifest")
        self.assertEqual(project["project"]["manifest_kind"], "project_personalization_manifest")
        self.assertFalse(template["privacy"]["commit_raw_exports"])
        self.assertFalse(project["rules"]["raw_private_data_in_git"])
        self.assertTrue(required.issubset(set(template["sync"]["required_update_targets"])))
        self.assertTrue(required.issubset(set(project["rules"]["required_update_targets"])))

    def test_startup_route_is_minimal_and_records_context_used(self) -> None:
        route_resources = load_script("route_agent_resources")
        route_result = route_resources.route_resources(ROOT, "startup")

        self.assertEqual(route_result["status"], "PASS")
        self.assertEqual(
            route_result["read_order"],
            ["AGENTS.md", "data/derived/personalization/codex_personalization.md"],
        )
        self.assertNotIn("docs/PERSONAL_CONTEXT_ARCHITECTURE.md", route_result["read_order"])
        self.assertNotIn("data/derived/agent_context/AGENT_CONTEXT.md", route_result["read_order"])
        self.assertEqual([row["source"] for row in route_result["context_used"]], route_result["read_order"])
        self.assertTrue(route_result["resource_policy"]["reason_required"])
        self.assertLessEqual(route_result["resource_policy"]["max_chars"], 6000)
        conditional_paths = [row["path"] for row in route_result["conditional_resources"]]
        self.assertIn("data/derived/profile/CORE_PROFILE.md", conditional_paths)

    def test_builds_exports_routes_and_evaluates_architecture(self) -> None:
        build_exports = load_script("build_personalization_exports")
        route_resources = load_script("route_agent_resources")
        evaluator = load_script("evaluate_personalization_context")
        with tempfile.TemporaryDirectory() as temp_dir:
            db = Path(temp_dir)
            write_minimal_database(db)

            export_result = build_exports.write_exports(db)
            route_result = route_resources.route_resources(db, "taste_profile")
            eval_result = evaluator.evaluate(db)
            chatgpt_export = (db / "data/derived/personalization/chatgpt_personalization.md").read_text(encoding="utf-8")
            machine_export = json.loads((db / "data/derived/personalization/personalization_export.json").read_text(encoding="utf-8"))

        self.assertEqual(export_result["status"], "PASS")
        self.assertEqual(route_result["status"], "PASS")
        self.assertEqual(eval_result["status"], "PASS")
        self.assertEqual(eval_result["log"], "not_appended_default_ci_safe")
        self.assertIn("Core Profile", chatgpt_export)
        self.assertIn("Preferences And Taste", chatgpt_export)
        self.assertTrue({"profile", "preference", "taste", "history", "pattern"}.issubset(machine_export["sync_required_targets"]))
        self.assertEqual(set(machine_export["run_log_categories"]), {"sync_runs", "export_runs", "evaluation_runs", "agent_runs"})

    def test_evaluator_rejects_invalid_task_run_evidence(self) -> None:
        evaluator = load_script("evaluate_personalization_context")
        with tempfile.TemporaryDirectory() as temp_dir:
            db = Path(temp_dir)
            write_minimal_database(db)
            log_path = db / "data/run_logs/agent_runs/invalid.jsonl"
            log_path.write_text(
                json.dumps(
                    {
                        "task_id": "TASK-BAD-001",
                        "run_type": "agent_run",
                        "status": "PASS",
                        "context_used": [{"source": "AGENTS.md", "reason": "test"}],
                        "tools_used": [{"tool": "python", "operation": "bad", "result": "success"}],
                        "tests_run": [
                            {
                                "command": "python3 bad.py",
                                "exit_code": 1,
                                "result": "PASS",
                                "evidence": "missing-evidence.txt",
                            }
                        ],
                        "failure_recovery": [],
                        "base_commit": "test",
                        "result_commit": "test",
                        "residual_risks": [],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            eval_result = evaluator.evaluate(db)

        self.assertEqual(eval_result["status"], "FAIL")
        self.assertTrue(
            any("tests_run_pass_without_exit_code_zero" in failure for failure in eval_result["failures"])
        )
        self.assertTrue(any("tests_run_missing_evidence_file" in failure for failure in eval_result["failures"]))


if __name__ == "__main__":
    unittest.main()
