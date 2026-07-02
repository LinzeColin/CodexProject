import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


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


if __name__ == "__main__":
    unittest.main()
