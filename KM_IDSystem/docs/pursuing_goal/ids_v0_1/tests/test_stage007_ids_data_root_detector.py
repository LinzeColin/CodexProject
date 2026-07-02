import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "detect_ids_data_root.py"


class Stage007IdsDataRootDetectorTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage007_ids_data_root", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _create_complete_slots(self, root: Path) -> None:
        for index in range(100):
            if index == 0:
                name = "00_ORIGINAL_RAW_DATA"
            elif index == 99:
                name = "99_ARCHIVE"
            else:
                name = f"{index:02d}_SLOT"
            (root / name).mkdir()

    def test_unconfigured_root_fails_closed_without_creating_directory(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            guessed = Path(tmp) / "IDS_DATA_ROOT"

            report = module.detect_ids_data_root("")

            self.assertEqual(report["state"], "NOT_CONFIGURED")
            self.assertTrue(report["safe_mode"])
            self.assertTrue(report["does_not_create_ids_data_root"])
            self.assertTrue(report["does_not_scan_recursively"])
            self.assertFalse(guessed.exists())

    def test_complete_00_99_structure_is_accepted_without_recursive_scan(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "IDS_DATA_ROOT"
            root.mkdir()
            self._create_complete_slots(root)
            nested = root / "00_ORIGINAL_RAW_DATA" / "real_material.txt"
            nested.write_text("placeholder fixture only", encoding="utf-8")

            report = module.detect_ids_data_root(str(root))

        self.assertEqual(report["state"], "STRUCTURE_COMPLETE")
        self.assertFalse(report["safe_mode"])
        self.assertEqual(report["missing_slots"], [])
        self.assertEqual(report["duplicate_slots"], [])
        self.assertEqual(report["malformed_entries"], [])
        self.assertTrue(report["raw_material_slot"]["present"])
        self.assertEqual(report["raw_material_slot"]["policy"], "read_only_required")
        self.assertTrue(report["does_not_scan_recursively"])
        self.assertNotIn("real_material.txt", json.dumps(report, ensure_ascii=False))

    def test_missing_and_duplicate_numeric_slots_enter_safe_mode(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            missing_root = Path(tmp) / "missing"
            missing_root.mkdir()
            self._create_complete_slots(missing_root)
            (missing_root / "42_SLOT").rmdir()

            duplicate_root = Path(tmp) / "duplicate"
            duplicate_root.mkdir()
            self._create_complete_slots(duplicate_root)
            (duplicate_root / "05_DUPLICATE").mkdir()

            missing = module.detect_ids_data_root(str(missing_root))
            duplicate = module.detect_ids_data_root(str(duplicate_root))

        self.assertEqual(missing["state"], "MISSING_NUMERIC_SLOTS")
        self.assertTrue(missing["safe_mode"])
        self.assertEqual(missing["missing_slots"], ["42"])
        self.assertEqual(duplicate["state"], "DUPLICATE_NUMERIC_SLOT")
        self.assertTrue(duplicate["safe_mode"])
        self.assertEqual(duplicate["duplicate_slots"], ["05"])

    def test_malformed_entries_file_path_and_permission_denied_are_safe_mode(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            malformed_root = Path(tmp) / "malformed"
            malformed_root.mkdir()
            self._create_complete_slots(malformed_root)
            (malformed_root / "README.txt").write_text("not a slot", encoding="utf-8")

            not_directory = Path(tmp) / "not-directory"
            not_directory.write_text("not a directory", encoding="utf-8")

            denied_root = Path(tmp) / "denied"
            denied_root.mkdir()

            malformed = module.detect_ids_data_root(str(malformed_root))
            not_dir = module.detect_ids_data_root(str(not_directory))
            with patch.object(module.os, "access", return_value=False):
                denied = module.detect_ids_data_root(str(denied_root))

        self.assertEqual(malformed["state"], "MALFORMED_TOP_LEVEL_ENTRY")
        self.assertTrue(malformed["safe_mode"])
        self.assertEqual(malformed["malformed_entries"], ["README.txt"])
        self.assertEqual(not_dir["state"], "ROOT_NOT_DIRECTORY")
        self.assertTrue(not_dir["safe_mode"])
        self.assertEqual(denied["state"], "ROOT_PERMISSION_DENIED")
        self.assertTrue(denied["safe_mode"])

    def test_cli_json_contract_is_operations_only(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--ids-data-root",
                "",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["stage"], "STAGE-007")
        self.assertEqual(payload["acceptance_id"], "ACC-STAGE-007")
        self.assertEqual(payload["entrance"], "IDS 系统运营入口")
        self.assertFalse(payload["customer_visible"])
        self.assertEqual(payload["state"], "NOT_CONFIGURED")
        self.assertTrue(payload["safe_mode"])
        self.assertTrue(payload["does_not_create_ids_data_root"])
        self.assertTrue(payload["does_not_scan_recursively"])


if __name__ == "__main__":
    unittest.main()
