import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_memory_atlas_acceptance.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_memory_atlas_acceptance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_atlas() -> dict:
    return {
        "schema_version": "memory_atlas.v1",
        "source_contract": {
            "mode": "public_redacted_read_only_visualization",
            "writeback_policy": {
                "frontend_can_request_writeback": True,
                "writeback_must_use_proposals": True,
                "direct_frontend_mutation_of_active_memory": False,
            },
        },
        "nodes": [],
        "edges": [],
        "timeline": [],
        "contribution": {"daily": []},
        "metrics": [],
    }


class MemoryAtlasAcceptanceAuditTests(unittest.TestCase):
    def test_acceptance_audit_passes_for_current_repo_sources(self) -> None:
        module = load_module()

        result = module.audit_acceptance(ROOT)

        self.assertEqual(result["status"], "PASS")
        check_names = {check["name"] for check in result["checks"]}
        self.assertIn("chinese_user_facing_ui", check_names)
        self.assertIn("ci_acceptance_gate", check_names)
        self.assertIn("cloudflare_pages_access_preflight", check_names)
        self.assertIn("agent_ready_personalization_contract", check_names)
        self.assertIn("fixed_agent_context_pack_ready", check_names)
        self.assertIn("real_codex_snapshot_not_mock", check_names)
        self.assertIn("memory_atlas_visual_acceptance", check_names)
        self.assertIn("runtime_atlas_fetch", check_names)
        self.assertIn("multi_source_registry_ready", check_names)

    def test_acceptance_audit_rejects_unsafe_publish_dir(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            publish_dir = Path(temp_dir)
            (publish_dir / "index.html").write_text("<!doctype html><div id='root'></div>", encoding="utf-8")
            (publish_dir / "memory_atlas.json").write_text(
                json.dumps({**valid_atlas(), "source_ref": "/Users/example/OpenAI-export.zip"}),
                encoding="utf-8",
            )

            with self.assertRaises(module.AcceptanceError) as raised:
                module.audit_acceptance(ROOT, publish_dir)

        self.assertIn("publish_dir_release_safe", str(raised.exception))
        self.assertIn("forbidden JSON key 'source_ref'", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
