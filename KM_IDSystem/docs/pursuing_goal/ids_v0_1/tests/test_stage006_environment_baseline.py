import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_environment_baseline.py"


class Stage006EnvironmentBaselineTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage006_environment_baseline", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_missing_ids_data_root_fails_closed_without_creating_directory(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "ids-data-root"

            report = module.evaluate_ids_data_root(str(missing))

            self.assertEqual(report["state"], "OFFLINE")
            self.assertTrue(report["safe_mode"])
            self.assertIn("bulk_import", report["paused_workflows"])
            self.assertIn("embedding", report["paused_workflows"])
            self.assertFalse(missing.exists())

    def test_unconfigured_and_path_changed_states_are_safe_mode(self):
        module = self._load_module()

        unconfigured = module.evaluate_ids_data_root(None)
        changed = module.evaluate_ids_data_root(
            "/Volumes/IDS-A", expected_path="/Volumes/IDS-B"
        )

        self.assertEqual(unconfigured["state"], "NOT_CONFIGURED")
        self.assertTrue(unconfigured["safe_mode"])
        self.assertEqual(changed["state"], "PATH_CHANGED")
        self.assertTrue(changed["requires_operator_confirmation"])
        self.assertTrue(changed["safe_mode"])

    def test_reconnected_path_requires_revalidation_before_resume(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            report = module.evaluate_ids_data_root(tmp, previous_state="OFFLINE")

        self.assertEqual(report["state"], "RECONNECTED")
        self.assertTrue(report["requires_revalidation"])
        self.assertTrue(report["safe_mode"])

    def test_storage_budget_blocks_low_internal_free_space(self):
        module = self._load_module()

        ok = module.evaluate_storage_budget(
            total_bytes=1000 * 1024**3,
            free_bytes=300 * 1024**3,
            min_free_gib=100,
            warn_free_gib=200,
            max_used_percent=85,
        )
        blocked = module.evaluate_storage_budget(
            total_bytes=1000 * 1024**3,
            free_bytes=50 * 1024**3,
            min_free_gib=100,
            warn_free_gib=200,
            max_used_percent=85,
        )

        self.assertEqual(ok["state"], "OK")
        self.assertFalse(ok["safe_mode"])
        self.assertEqual(blocked["state"], "BLOCKED")
        self.assertTrue(blocked["safe_mode"])
        self.assertIn("internal_disk_low_free_space", blocked["reasons"])

    def test_cli_json_contract_is_operations_only(self):
        result = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--ids-data-root",
                "",
                "--internal-total-gib",
                "1000",
                "--internal-free-gib",
                "300",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["entrance"], "IDS 系统运营入口")
        self.assertFalse(payload["customer_visible"])
        self.assertEqual(payload["ids_data_root"]["state"], "NOT_CONFIGURED")
        self.assertIn("ocr", payload["ids_data_root"]["paused_workflows"])


if __name__ == "__main__":
    unittest.main()
