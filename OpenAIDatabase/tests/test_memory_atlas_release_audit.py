import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_memory_atlas_release.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_memory_atlas_release", SCRIPT)
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


class MemoryAtlasReleaseAuditTests(unittest.TestCase):
    def test_release_audit_passes_for_static_redacted_output(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            publish_dir = Path(temp_dir)
            (publish_dir / "index.html").write_text("<!doctype html><div id='root'></div>", encoding="utf-8")
            (publish_dir / "assets").mkdir()
            (publish_dir / "assets/app.js").write_text("console.log('memory atlas')", encoding="utf-8")
            (publish_dir / "memory_atlas.json").write_text(json.dumps(valid_atlas()), encoding="utf-8")

            result = module.audit_release(ROOT, publish_dir)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["file_count"], 3)

    def test_release_audit_rejects_raw_or_sensitive_output(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            publish_dir = Path(temp_dir)
            (publish_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
            (publish_dir / "memory_atlas.json").write_text(
                json.dumps({**valid_atlas(), "evidence": [{"source": "raw should not ship"}]}),
                encoding="utf-8",
            )
            (publish_dir / "OpenAI-export.zip").write_bytes(b"not really a zip")

            with self.assertRaises(module.AuditError) as raised:
                module.audit_release(ROOT, publish_dir)

        message = str(raised.exception)
        self.assertIn("forbidden publish suffix", message)
        self.assertIn("forbidden JSON key 'evidence'", message)


if __name__ == "__main__":
    unittest.main()
