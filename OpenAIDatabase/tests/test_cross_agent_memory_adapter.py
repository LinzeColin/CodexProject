from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts/build_personalization_exports.py"
EVALUATOR = ROOT / "scripts/evaluate_personalization_context.py"


def load_script(name: str, path: Path):
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def projection_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("## "):
            break
        if line.startswith("- ") and ": " in line:
            key, value = line[2:].split(": ", 1)
            metadata[key] = value
    return metadata


def write_fixture(root: Path) -> None:
    for relative in (
        "config/context_sources/three_layer_context.json",
        "config/context_sources/resource_routes.json",
        "config/evaluation/personalization_harness.json",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)

    context = json.loads((root / "config/context_sources/three_layer_context.json").read_text(encoding="utf-8"))
    for layer in context["layers"]:
        for relative in layer.get("canonical_files", []):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".json":
                path.write_text("{}\n", encoding="utf-8")
            elif path.suffix == ".jsonl":
                path.write_text("{}\n", encoding="utf-8")
            else:
                path.write_text(f"# {path.stem}\n", encoding="utf-8")

    (root / "data/derived/profile/CORE_PROFILE.md").write_text(
        "\n".join(
            [
                "# Curated Core Profile",
                "",
                "## High-weight Core Personalization",
                "",
                "- 默认中文输出，复杂任务必须给出可验证证据。",
                "- 一次只执行一个项目、一个 Task、一个 Acceptance。",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        root / "data/derived/codex/codex_agent_recommendations.json",
        {
            "schema_version": "codex_agent_recommendations.v1",
            "generated_at": "2026-07-13T00:00:00Z",
            "top_topics": [{"label": "Shared memory", "count": 2}],
            "memory": {
                "current": [
                    {
                        "id": "memory-1",
                        "title": "唯一事实源",
                        "statement": "OpenAIDatabase 是长期用户记忆控制面。",
                        "confidence": "high",
                        "importance": "高",
                        "evidence_count": 2,
                    }
                ],
                "added": [],
                "modified": [],
                "deleted": [],
            },
            "meta_data": {"current": [], "added": [], "modified": [], "deleted": []},
        },
    )
    write_json(
        root / "data/processed/codex/codex_activity_snapshot.json",
        {
            "schema_version": "codex_activity_snapshot.v1",
            "generated_at": "2026-07-13T00:00:00Z",
            "source": "synthetic_redacted_fixture",
            "session_count": 1,
            "message_count": 1,
            "tool_call_count": 1,
            "range_start": "2026-07-13",
            "range_end": "2026-07-13",
            "top_topics": [{"label": "Shared memory", "count": 2}],
        },
    )
    write_json(root / "data/derived/visualization/memory_atlas.json", {"overview": {"node_count": 1, "edge_count": 0}})
    write_json(
        root / "config/data_sources/source_registry.json",
        {
            "schema_version": "memory_atlas.source_registry.v1",
            "contract_version": "test",
            "sources": [],
            "canonical_event_contract": {"required_fields": []},
        },
    )
    write_json(root / "data/derived/personalization/personalization_export.json", {})


class CrossAgentMemoryAdapterTests(unittest.TestCase):
    def test_claude_route_is_minimal_and_deeper_context_is_conditional(self) -> None:
        router = load_script("route_agent_resources_cross_agent_test", ROOT / "scripts/route_agent_resources.py")
        result = router.route_resources(ROOT, "claude_personalization")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["read_order"],
            ["data/derived/personalization/claude_personalization.md"],
        )
        conditional = {row["path"] for row in result["conditional_resources"]}
        self.assertIn("data/derived/agent_context/AGENT_CONTEXT.md", conditional)
        self.assertIn("data/derived/profile/CORE_PROFILE.md", conditional)
        self.assertTrue(all("raw" not in path and "private" not in path for path in result["read_order"]))

    def test_shared_identity_determinism_source_change_privacy_and_size(self) -> None:
        generator = load_script("build_personalization_exports_cross_agent_test", GENERATOR)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            write_fixture(database)
            with patch.object(
                generator,
                "now_utc",
                side_effect=[
                    "2026-07-13T00:00:00Z",
                    "2026-07-13T00:00:01Z",
                    "2026-07-13T00:00:02Z",
                ],
            ):
                first = generator.write_exports(database)
                first_manifest = json.loads(
                    (database / generator.MEMORY_BUNDLE_MANIFEST).read_text(encoding="utf-8")
                )
                first_outputs = {
                    provider: (database / path).read_text(encoding="utf-8")
                    for provider, path in generator.PROVIDER_EXPORTS.items()
                }
                first_hashes = {provider: sha256_text(text) for provider, text in first_outputs.items()}

                second = generator.write_exports(database)
                second_manifest = json.loads(
                    (database / generator.MEMORY_BUNDLE_MANIFEST).read_text(encoding="utf-8")
                )
                second_outputs = {
                    provider: (database / path).read_text(encoding="utf-8")
                    for provider, path in generator.PROVIDER_EXPORTS.items()
                }

                profile = database / "data/derived/profile/CORE_PROFILE.md"
                profile.write_text(profile.read_text(encoding="utf-8") + "\n- 新的稳定偏好。\n", encoding="utf-8")
                third = generator.write_exports(database)

            self.assertEqual(first["bundle_id"], second["bundle_id"])
            self.assertEqual(first["canonical_source_hash"], second["canonical_source_hash"])
            self.assertEqual(first_outputs, second_outputs)
            self.assertEqual(first_manifest["generated_at"], second_manifest["generated_at"])
            self.assertEqual(
                first_hashes,
                {
                    provider: item["projection_hash"]
                    for provider, item in first_manifest["projections"].items()
                },
            )
            self.assertNotEqual(first["bundle_id"], third["bundle_id"])
            self.assertNotEqual(first["canonical_source_hash"], third["canonical_source_hash"])

            identities = {
                (
                    projection_metadata(text)["bundle_id"],
                    projection_metadata(text)["canonical_source_hash"],
                )
                for text in first_outputs.values()
            }
            self.assertEqual(identities, {(first["bundle_id"], first["canonical_source_hash"])})
            self.assertEqual(set(first_manifest["projections"]), {"chatgpt", "codex", "claude"})
            self.assertEqual(first_manifest["schema_version"], generator.BUNDLE_SCHEMA_VERSION)
            self.assertEqual(first_manifest["generator_version"], generator.BUNDLE_GENERATOR_VERSION)
            self.assertNotIn("repo_head", first_manifest)
            self.assertNotIn("working_tree_dirty", first_manifest)
            self.assertEqual(
                first_manifest["projection_input_files"],
                [record["path"] for record in first_manifest["projection_input_records"]],
            )
            for provider, text in first_outputs.items():
                metadata = projection_metadata(text)
                self.assertEqual(metadata["provider"], provider)
                self.assertIn("Derived / Read-only / Regenerate, do not hand edit", text)
                self.assertEqual(first_manifest["projections"][provider]["projection_hash"], sha256_text(text))
            self.assertLessEqual(len(first_outputs["claude"].encode("utf-8")), 4096)

            combined = "\n".join(first_outputs.values()) + json.dumps(first_manifest, ensure_ascii=False)
            harness = json.loads((database / "config/evaluation/personalization_harness.json").read_text(encoding="utf-8"))
            for pattern in harness["forbidden_plaintext_patterns"]:
                self.assertNotIn(pattern, combined)
            self.assertNotIn("/Users/", combined)
            self.assertFalse(first_manifest["raw_private_data_included"])
            self.assertFalse(first_manifest["plaintext_secrets_included"])
            self.assertTrue(all(not Path(path).is_absolute() for path in first_manifest["source_files"]))

    def test_auxiliary_projection_input_changes_bundle_but_not_canonical_hash(self) -> None:
        generator = load_script("build_personalization_exports_auxiliary_input_test", GENERATOR)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            write_fixture(database)
            events_path = database / "data/derived/behavior_intelligence/events.json"
            write_json(events_path, {"event_count": 1})

            first = generator.write_exports(database)
            first_chatgpt = (database / generator.CHATGPT_EXPORT).read_text(encoding="utf-8")
            first_manifest = json.loads(
                (database / generator.MEMORY_BUNDLE_MANIFEST).read_text(encoding="utf-8")
            )

            write_json(events_path, {"event_count": 2})
            second = generator.write_exports(database)
            second_chatgpt = (database / generator.CHATGPT_EXPORT).read_text(encoding="utf-8")
            second_manifest = json.loads(
                (database / generator.MEMORY_BUNDLE_MANIFEST).read_text(encoding="utf-8")
            )

            self.assertEqual(first["canonical_source_hash"], second["canonical_source_hash"])
            self.assertNotEqual(first_manifest["projection_input_hash"], second_manifest["projection_input_hash"])
            self.assertNotEqual(first["bundle_id"], second["bundle_id"])
            self.assertNotEqual(first_chatgpt, second_chatgpt)

    def test_evaluator_recomputes_bundle_source_proof_and_rejects_tampering(self) -> None:
        generator = load_script("build_personalization_exports_source_proof_test", GENERATOR)
        evaluator = load_script("evaluate_personalization_context_source_proof_test", EVALUATOR)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            write_fixture(database)
            generator.write_exports(database)
            manifest = json.loads(
                (database / generator.MEMORY_BUNDLE_MANIFEST).read_text(encoding="utf-8")
            )

            self.assertEqual(evaluator.validate_bundle_source_proof(database, manifest), [])

            tampered = json.loads(json.dumps(manifest))
            tampered["source_records"][0]["content_hash"] = "sha256:" + ("0" * 64)
            self.assertIn(
                "manifest_source_records_mismatch",
                evaluator.validate_bundle_source_proof(database, tampered),
            )

            write_json(database / "data/derived/behavior_intelligence/events.json", {"event_count": 1})
            stale_failures = evaluator.validate_bundle_source_proof(database, manifest)
            self.assertIn("manifest_projection_input_hash_mismatch", stale_failures)
            self.assertIn("manifest_projection_input_records_mismatch", stale_failures)
            self.assertIn("manifest_bundle_id_mismatch", stale_failures)

    def test_private_source_path_is_rejected(self) -> None:
        generator = load_script("build_personalization_exports_private_path_test", GENERATOR)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            write_fixture(database)
            config_path = database / generator.CONTEXT_CONFIG
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["layers"][0]["canonical_files"].append("data/private/forbidden.json")
            write_json(config_path, config)

            with self.assertRaisesRegex(ValueError, "raw/private path"):
                generator.write_exports(database)


if __name__ == "__main__":
    unittest.main()
