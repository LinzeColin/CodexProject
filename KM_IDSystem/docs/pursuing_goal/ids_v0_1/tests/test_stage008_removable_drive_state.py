import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_removable_drive_state.py"


class Stage008RemovableDriveStateTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage008_removable_drive_state", SCRIPT)
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

    def test_unconfigured_and_absent_roots_enter_non_resumable_safe_mode(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            absent = Path(tmp) / "IDS_DATA_ROOT"

            unconfigured = module.evaluate_removable_drive_state("")
            offline = module.evaluate_removable_drive_state(str(absent))

        self.assertEqual(unconfigured["state"], "NOT_CONFIGURED")
        self.assertEqual(offline["state"], "OFFLINE")
        self.assertTrue(unconfigured["safe_mode"])
        self.assertTrue(offline["safe_mode"])
        self.assertFalse(unconfigured["resume_allowed"])
        self.assertFalse(offline["resume_allowed"])
        self.assertIn("bulk_import", offline["paused_workflows"])
        self.assertFalse(absent.exists())

    def test_reconnected_complete_root_requires_explicit_revalidation(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "IDS_DATA_ROOT"
            root.mkdir()
            self._create_complete_slots(root)

            report = module.evaluate_removable_drive_state(
                str(root),
                previous_state="OFFLINE",
            )

        self.assertEqual(report["state"], "RECONNECTED_NEEDS_REVALIDATION")
        self.assertTrue(report["safe_mode"])
        self.assertTrue(report["requires_revalidation"])
        self.assertFalse(report["resume_allowed"])
        self.assertIn("revalidate_path_permission_structure", report["operator_actions"])

    def test_validated_root_can_enter_online_validated_without_auto_import(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "IDS_DATA_ROOT"
            root.mkdir()
            self._create_complete_slots(root)

            report = module.evaluate_removable_drive_state(
                str(root),
                storage_total_bytes=1000 * 1024**3,
                storage_free_bytes=300 * 1024**3,
            )

        self.assertEqual(report["state"], "ONLINE_VALIDATED")
        self.assertFalse(report["safe_mode"])
        self.assertTrue(report["resume_allowed"])
        self.assertFalse(report["auto_resume"])
        self.assertEqual(report["paused_workflows"], [])
        self.assertTrue(report["bounded_preflight_only"])

    def test_path_permission_structure_and_storage_failures_map_to_state_machine(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            complete = base / "complete"
            complete.mkdir()
            self._create_complete_slots(complete)

            denied = base / "denied"
            denied.mkdir()

            missing = base / "missing"
            missing.mkdir()
            self._create_complete_slots(missing)
            (missing / "42_SLOT").rmdir()

            def access_side_effect(path, mode):
                return Path(path) != denied

            with patch.object(module.root_detector.os, "access", side_effect=access_side_effect):
                path_changed = module.evaluate_removable_drive_state(
                    str(complete),
                    expected_path=str(base / "expected"),
                )
                permission_denied = module.evaluate_removable_drive_state(str(denied))
                structure_invalid = module.evaluate_removable_drive_state(str(missing))
                storage_blocked = module.evaluate_removable_drive_state(
                    str(complete),
                    storage_total_bytes=1000 * 1024**3,
                    storage_free_bytes=50 * 1024**3,
                )

        self.assertEqual(path_changed["state"], "PATH_CHANGED")
        self.assertEqual(permission_denied["state"], "PERMISSION_DENIED")
        self.assertEqual(structure_invalid["state"], "STRUCTURE_INVALID")
        self.assertEqual(storage_blocked["state"], "STORAGE_BLOCKED")
        for report in [path_changed, permission_denied, structure_invalid, storage_blocked]:
            self.assertTrue(report["safe_mode"])
            self.assertFalse(report["resume_allowed"])
            self.assertFalse(report["does_not_scan_recursively"] is False)

    def test_cli_json_contract_is_operations_only(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--ids-data-root",
                "",
                "--storage-total-gib",
                "1000",
                "--storage-free-gib",
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
        self.assertEqual(payload["stage"], "STAGE-008")
        self.assertEqual(payload["acceptance_id"], "ACC-STAGE-008")
        self.assertEqual(payload["entrance"], "IDS 系统运营入口")
        self.assertFalse(payload["customer_visible"])
        self.assertEqual(payload["state"], "NOT_CONFIGURED")
        self.assertTrue(payload["safe_mode"])
        self.assertFalse(payload["resume_allowed"])
        self.assertFalse(payload["auto_resume"])
        self.assertTrue(payload["does_not_create_ids_data_root"])
        self.assertTrue(payload["does_not_scan_recursively"])

    def test_phase3_scenario_report_covers_transitions_storage_and_safe_mode_pauses(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            online = base / "online"
            online.mkdir()
            self._create_complete_slots(online)

            offline = base / "offline"

            denied = base / "denied"
            denied.mkdir()

            missing = base / "missing"
            missing.mkdir()
            self._create_complete_slots(missing)
            (missing / "42_SLOT").rmdir()

            def access_side_effect(path, mode):
                return Path(path) != denied

            with patch.object(module.root_detector.os, "access", side_effect=access_side_effect):
                report = module.build_stage008_scenario_report(
                    online_root=str(online),
                    offline_root=str(offline),
                    reconnected_root=str(online),
                    permission_denied_root=str(denied),
                    path_changed_current=str(online),
                    path_changed_expected=str(base / "expected"),
                    structure_invalid_root=str(missing),
                    storage_total_bytes=1000 * 1024**3,
                    storage_ok_free_bytes=300 * 1024**3,
                    storage_low_free_bytes=50 * 1024**3,
                    storage_high_used_free_bytes=120 * 1024**3,
                )

        scenarios = report["removable_drive_scenarios"]
        storage = report["storage_scenarios"]

        self.assertTrue(report["overall_valid"])
        self.assertEqual(report["schema_version"], "ids.stage008.phase3_scenarios.v1")
        self.assertFalse(report["customer_visible"])
        self.assertTrue(report["does_not_start_services"])
        self.assertTrue(report["does_not_create_ids_data_root"])
        self.assertTrue(report["does_not_scan_recursively"])
        self.assertTrue(report["does_not_scan_external_drive_contents"])
        self.assertEqual(scenarios["online"]["state"], "ONLINE_VALIDATED")
        self.assertFalse(scenarios["online"]["safe_mode"])
        self.assertFalse(scenarios["online"]["auto_resume"])
        self.assertEqual(scenarios["offline"]["state"], "OFFLINE")
        self.assertEqual(scenarios["reconnected"]["state"], "RECONNECTED_NEEDS_REVALIDATION")
        self.assertTrue(scenarios["reconnected"]["requires_revalidation"])
        self.assertFalse(scenarios["reconnected"]["resume_allowed"])
        self.assertEqual(scenarios["permission_denied"]["state"], "PERMISSION_DENIED")
        self.assertEqual(scenarios["path_changed"]["state"], "PATH_CHANGED")
        self.assertTrue(scenarios["path_changed"]["requires_operator_confirmation"])
        self.assertEqual(scenarios["structure_invalid"]["state"], "STRUCTURE_INVALID")
        self.assertEqual(storage["ok"]["state"], "ONLINE_VALIDATED")
        self.assertEqual(storage["low_free_space"]["state"], "STORAGE_BLOCKED")
        self.assertEqual(storage["high_waterline"]["state"], "STORAGE_BLOCKED")
        for workflow in ["bulk_import", "ocr", "embedding", "index_rebuild", "raw_material_cleanup"]:
            self.assertIn(workflow, report["safe_mode_pauses"])


if __name__ == "__main__":
    unittest.main()
