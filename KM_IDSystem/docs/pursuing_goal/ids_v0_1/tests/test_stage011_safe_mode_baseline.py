import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_safe_mode_baseline.py"
REAL_SOURCE = Path(__file__).resolve()
GIB = 1024**3


class Stage011SafeModeBaselineTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage011_safe_mode_baseline", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _default_paths(self, base: Path) -> dict[str, str]:
        return {
            "processed_path": str(base / "derived" / "processed"),
            "backup_path": str(base / "backups" / "raw-backup"),
            "manifest_path": str(base / "metadata" / "manifest.json"),
            "report_export_path": str(base / "exports" / "report.pdf"),
        }

    def _create_complete_slots(self, root: Path) -> None:
        for index in range(100):
            if index == 0:
                name = "00_ORIGINAL_RAW_DATA"
            elif index == 99:
                name = "99_ARCHIVE"
            else:
                name = f"{index:02d}_SLOT"
            (root / name).mkdir()

    def test_clear_bounded_preflight_is_operations_only_without_reading_source(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            paths = self._default_paths(base)

            report = module.evaluate_safe_mode_baseline(
                source_uri=REAL_SOURCE.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                job_kind="bounded_preflight",
                require_external_root=False,
                index_state="OK",
                api_budget_state="OK",
                **paths,
            )

            self.assertEqual(report["schema_version"], "ids.stage011.safe_mode_baseline.v1")
            self.assertEqual(report["stage"], "STAGE-011")
            self.assertEqual(report["phase"], "Phase 2")
            self.assertEqual(report["acceptance_id"], "ACC-STAGE-011")
            self.assertEqual(report["state"], "SAFE_MODE_CLEAR")
            self.assertFalse(report["safe_mode"])
            self.assertFalse(report["customer_visible"])
            self.assertEqual(report["entrance"], "IDS 系统运营入口")
            self.assertEqual(report["local_path_contract_state"], "PATH_CONTRACT_OK")
            self.assertEqual(report["storage_budget_state"], "BUDGET_OK")
            self.assertEqual(report["index_state"], "OK")
            self.assertEqual(report["api_budget_state"], "OK")
            self.assertTrue(report["bounded_preflight_only"])
            self.assertFalse(report["auto_resume"])
            for path in paths.values():
                self.assertFalse(Path(path).exists())
            serialized = json.dumps(report, ensure_ascii=False)
            self.assertNotIn("Stage011SafeModeBaselineTests", serialized)
            for flag in [
                "does_not_start_services",
                "does_not_create_ids_data_root",
                "does_not_scan_recursively",
                "does_not_scan_external_drive_contents",
                "does_not_open_source_files",
                "does_not_hash_source_files",
                "does_not_read_raw_metadata",
                "does_not_generate_outputs",
                "does_not_write_runtime_data",
                "does_not_write_manifests",
                "does_not_copy_backups",
                "does_not_call_external_apis",
            ]:
                self.assertTrue(report[flag], flag)

    def test_missing_ids_data_root_enters_safe_mode_without_auto_resume(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            report = module.evaluate_safe_mode_baseline(
                source_uri=REAL_SOURCE.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                job_kind="bulk_import",
                require_external_root=True,
                index_state="OK",
                api_budget_state="OK",
                **self._default_paths(base),
            )

        self.assertEqual(report["state"], "SAFE_MODE_ROOT_NOT_CONFIGURED")
        self.assertTrue(report["safe_mode"])
        self.assertFalse(report["auto_resume"])
        self.assertTrue(report["requires_revalidation"])
        self.assertIn("bulk_import", report["paused_workflows"])
        self.assertIn("ocr", report["paused_workflows"])
        self.assertIn("embedding", report["paused_workflows"])
        self.assertIn("index_rebuild", report["paused_workflows"])
        self.assertIn("manifest_generation", report["paused_workflows"])
        self.assertIn("report_export", report["paused_workflows"])
        self.assertIn("configure_ids_data_root", report["operator_actions"])

    def test_storage_path_index_and_api_budget_states_fail_closed_distinctly(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            paths = self._default_paths(base)

            low_storage = module.evaluate_safe_mode_baseline(
                source_uri=REAL_SOURCE.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=50 * GIB,
                planned_output_bytes=1 * GIB,
                job_kind="bounded_preflight",
                require_external_root=False,
                index_state="OK",
                api_budget_state="OK",
                **paths,
            )
            invalid_path = module.evaluate_safe_mode_baseline(
                source_uri="https://www.iana.org/domains/reserved",
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                job_kind="bounded_preflight",
                require_external_root=False,
                index_state="OK",
                api_budget_state="OK",
                **paths,
            )
            index_failed = module.evaluate_safe_mode_baseline(
                source_uri=REAL_SOURCE.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                job_kind="bounded_preflight",
                require_external_root=False,
                index_state="FAILED",
                api_budget_state="OK",
                **paths,
            )
            api_exceeded = module.evaluate_safe_mode_baseline(
                source_uri=REAL_SOURCE.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                job_kind="bounded_preflight",
                require_external_root=False,
                index_state="OK",
                api_budget_state="EXCEEDED",
                **paths,
            )

        self.assertEqual(low_storage["state"], "SAFE_MODE_STORAGE_BLOCKED")
        self.assertEqual(invalid_path["state"], "SAFE_MODE_PATH_BLOCKED")
        self.assertEqual(index_failed["state"], "SAFE_MODE_INDEX_FAILED")
        self.assertEqual(api_exceeded["state"], "SAFE_MODE_API_BUDGET_EXCEEDED")
        for report in [low_storage, invalid_path, index_failed, api_exceeded]:
            self.assertTrue(report["safe_mode"])
            self.assertFalse(report["auto_resume"])
            self.assertTrue(report["requires_operator_confirmation"])
            self.assertTrue(report["does_not_call_external_apis"])

    def test_cli_json_contract_is_stage011_operations_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-uri",
                    REAL_SOURCE.as_uri(),
                    "--processed-path",
                    str(base / "derived" / "processed"),
                    "--backup-path",
                    str(base / "backups" / "raw-backup"),
                    "--manifest-path",
                    str(base / "metadata" / "manifest.json"),
                    "--report-export-path",
                    str(base / "exports" / "report.pdf"),
                    "--internal-total-gib",
                    "1000",
                    "--internal-free-gib",
                    "300",
                    "--planned-output-gib",
                    "20",
                    "--job-kind",
                    "bounded_preflight",
                    "--index-state",
                    "OK",
                    "--api-budget-state",
                    "OK",
                    "--no-require-external-root",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "ids.stage011.safe_mode_baseline.v1")
        self.assertEqual(payload["stage"], "STAGE-011")
        self.assertEqual(payload["phase"], "Phase 2")
        self.assertEqual(payload["acceptance_id"], "ACC-STAGE-011")
        self.assertEqual(payload["state"], "SAFE_MODE_CLEAR")
        self.assertFalse(payload["customer_visible"])
        self.assertTrue(payload["bounded_preflight_only"])
        self.assertTrue(payload["does_not_start_services"])
        self.assertTrue(payload["does_not_scan_external_drive_contents"])
        self.assertTrue(payload["does_not_read_raw_metadata"])
        self.assertTrue(payload["does_not_generate_outputs"])
        self.assertTrue(payload["does_not_call_external_apis"])

    def test_phase3_scenario_report_covers_safe_mode_edges_and_paused_workflows(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            output_paths = self._default_paths(base)

            online_root = base / "online_IDS_DATA_ROOT"
            online_root.mkdir()
            self._create_complete_slots(online_root)

            offline_root = base / "offline_IDS_DATA_ROOT"

            reconnected_root = base / "reconnected_IDS_DATA_ROOT"
            reconnected_root.mkdir()
            self._create_complete_slots(reconnected_root)

            permission_denied_root = base / "permission_denied_IDS_DATA_ROOT"
            permission_denied_root.mkdir()
            self._create_complete_slots(permission_denied_root)

            def access_side_effect(path, mode):
                return Path(path) != permission_denied_root

            with patch.object(module.path_contract.os, "access", side_effect=access_side_effect):
                report = module.build_stage011_scenario_report(
                    valid_source_uri=REAL_SOURCE.as_uri(),
                    online_root=str(online_root),
                    offline_root=str(offline_root),
                    reconnected_root=str(reconnected_root),
                    permission_denied_root=str(permission_denied_root),
                    path_changed_current=str(online_root),
                    path_changed_expected=str(base / "expected_IDS_DATA_ROOT"),
                    processed_path=output_paths["processed_path"],
                    backup_path=output_paths["backup_path"],
                    manifest_path=output_paths["manifest_path"],
                    report_export_path=output_paths["report_export_path"],
                    storage_total_bytes=1000 * GIB,
                    storage_ok_free_bytes=300 * GIB,
                    storage_low_free_bytes=50 * GIB,
                    planned_output_ok_bytes=20 * GIB,
                    planned_output_too_large_bytes=250 * GIB,
                    invalid_source_uri="https://www.iana.org/domains/reserved",
                )

            for path in output_paths.values():
                self.assertFalse(Path(path).exists())
            self.assertFalse(offline_root.exists())

        states = report["scenario_states"]

        self.assertTrue(report["overall_valid"])
        self.assertEqual(report["schema_version"], "ids.stage011.phase3_scenarios.v1")
        self.assertEqual(report["stage"], "STAGE-011")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-011")
        self.assertFalse(report["customer_visible"])
        self.assertEqual(states["clear"], "SAFE_MODE_CLEAR")
        self.assertEqual(states["drive_offline"], "SAFE_MODE_DRIVE_OFFLINE")
        self.assertEqual(states["drive_reconnected"], "SAFE_MODE_REVALIDATION_REQUIRED")
        self.assertEqual(states["permission_denied"], "SAFE_MODE_PERMISSION_DENIED")
        self.assertEqual(states["path_changed"], "SAFE_MODE_REVALIDATION_REQUIRED")
        self.assertEqual(states["storage_low_free"], "SAFE_MODE_STORAGE_BLOCKED")
        self.assertEqual(states["unbounded_output_missing_cap"], "SAFE_MODE_STORAGE_BLOCKED")
        self.assertEqual(states["path_blocked"], "SAFE_MODE_PATH_BLOCKED")
        self.assertEqual(states["index_failed"], "SAFE_MODE_INDEX_FAILED")
        self.assertEqual(states["api_budget_exceeded"], "SAFE_MODE_API_BUDGET_EXCEEDED")
        for workflow in [
            "bulk_import",
            "ocr",
            "embedding",
            "index_rebuild",
            "raw_material_cleanup",
            "backup_copy",
            "manifest_generation",
            "report_export",
            "external_api_calls",
        ]:
            self.assertIn(workflow, report["safe_mode_pauses"])
        for scenario in report["safe_mode_scenarios"].values():
            self.assertFalse(scenario["auto_resume"])
            self.assertTrue(scenario["bounded_preflight_only"])
            self.assertTrue(scenario["does_not_read_raw_metadata"])
            self.assertTrue(scenario["does_not_call_external_apis"])
            self.assertTrue(scenario["does_not_generate_outputs"])
            self.assertTrue(scenario["does_not_write_runtime_data"])
            self.assertTrue(scenario["does_not_scan_external_drive_contents"])
            self.assertTrue(scenario["does_not_open_source_files"])
            self.assertTrue(scenario["does_not_hash_source_files"])


if __name__ == "__main__":
    unittest.main()
