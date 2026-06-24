from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/privacy_guard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("privacy_guard", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S3PDT01PrivacyTests(unittest.TestCase):
    def test_private_import_writes_only_redacted_derived_data_and_survives_raw_deletion(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            database = workspace / "OpenAIDatabase"
            database.mkdir()
            raw_dir = workspace / "private-source"
            raw_dir.mkdir()
            raw_path = raw_dir / "alice.private@example.com.json"
            secret = "sk-" + "testprivate1234567890"
            phone = "+8613800138000"
            local_path = "C:/Users/linze/Downloads/private/raw-export.zip"
            raw_path.write_text(
                json.dumps(
                    {
                        "email": "alice.private@example.com",
                        "phone": phone,
                        "api_key": secret,
                        "local_path": local_path,
                        "notes": "synthetic private import fixture",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = module.import_private_export(raw_path, database, "synthetic.redacted.json")
            output_path = database / result["output_path"]
            audit_path = database / module.PRIVACY_AUDIT_LOG
            output_text = output_path.read_text(encoding="utf-8")
            audit_text = audit_path.read_text(encoding="utf-8")

            for sensitive in {"alice.private@example.com", phone, secret, local_path}:
                self.assertNotIn(sensitive, output_text)
                self.assertNotIn(sensitive, audit_text)
            self.assertIn("[REDACTED_EMAIL]", output_text)
            self.assertIn("[REDACTED_PHONE]", output_text)
            self.assertIn("[REDACTED_SECRET]", output_text)
            self.assertIn("[REDACTED_LOCAL_PATH]", output_text)
            self.assertFalse((database / "data/raw").exists())
            self.assertFalse((database / "data/private_imports").exists())

            raw_path.unlink()
            recovered = json.loads(output_text)

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(recovered["raw_private_data_included"])
        self.assertFalse(recovered["plaintext_secrets_included"])
        self.assertFalse(recovered["local_absolute_paths_included"])
        self.assertEqual(recovered["redacted_payload"]["email"], "[REDACTED_EMAIL]")

    def test_private_import_rejects_raw_source_inside_tracked_derived_tree(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            raw_path = database / "data/derived/leaky/raw.json"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_text('{"email":"alice.private@example.com"}', encoding="utf-8")

            with self.assertRaises(module.PrivacyViolation):
                module.import_private_export(raw_path, database, "should_not_write.json")

        self.assertFalse((database / "data/derived/privacy_imports/should_not_write.json").exists())

    def test_repo_gitignore_and_current_scan_prevent_raw_private_git_leakage(self) -> None:
        module = load_module()
        ignore_contract = module.gitignore_declares_private_defaults(ROOT)
        scan = module.scan_repo_privacy(ROOT)

        self.assertTrue(ignore_contract["ok"], ignore_contract)
        self.assertEqual(scan["status"], "PASS", scan)
        self.assertEqual(scan["tracked_raw_private_file_count"], 0)
        self.assertEqual(scan["high_risk_secret_hit_count"], 0)


if __name__ == "__main__":
    unittest.main()
