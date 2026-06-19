import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/preflight_cloudflare_pages_access.py"


def load_module():
    spec = importlib.util.spec_from_file_location("preflight_cloudflare_pages_access", SCRIPT)
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
        "visual_layers": {
            "primary": "galaxy",
            "secondary": ["notion_map", "roi_dashboard", "obsidian_graph", "timeline", "contribution_grid"],
        },
        "nodes": [],
        "edges": [],
        "timeline": [],
        "contribution": {"daily": []},
        "metrics": [],
    }


class CloudflarePagesAccessPreflightTests(unittest.TestCase):
    def test_preflight_passes_for_repo_without_live_env(self) -> None:
        module = load_module()

        result = module.preflight(ROOT)

        self.assertEqual(result["status"], "PASS")
        names = {check["name"] for check in result["checks"]}
        self.assertIn("cloudflare_pages_template_contract", names)
        self.assertIn("cloudflare_access_template_contract", names)
        self.assertIn("cloudflare_live_deploy_authorization", names)

    def test_preflight_requires_live_env_when_requested(self) -> None:
        module = load_module()

        with self.assertRaises(module.PreflightError) as raised:
            module.preflight(ROOT, require_live_env=True)

        self.assertIn("cloudflare_live_env_present", str(raised.exception))

    def test_preflight_rejects_unsafe_publish_dir(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            publish_dir = Path(temp_dir)
            (publish_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
            (publish_dir / "memory_atlas.json").write_text(
                json.dumps({**valid_atlas(), "database_dir": "/Users/example/OpenAIDatabase"}),
                encoding="utf-8",
            )

            with self.assertRaises(module.PreflightError) as raised:
                module.preflight(ROOT, publish_dir)

        self.assertIn("cloudflare_publish_release_safe", str(raised.exception))
        self.assertIn("forbidden JSON key 'database_dir'", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
