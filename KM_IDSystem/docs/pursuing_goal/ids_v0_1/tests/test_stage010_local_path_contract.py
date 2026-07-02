import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_local_path_contract.py"
GIB = 1024**3


class Stage010LocalPathContractTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage010_local_path_contract", SCRIPT)
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

    def _default_paths(self, base: Path) -> dict[str, str]:
        return {
            "processed_path": str(base / "derived" / "processed"),
            "backup_path": str(base / "backups" / "raw-backup"),
            "manifest_path": str(base / "metadata" / "manifest.json"),
            "report_export_path": str(base / "exports" / "report.pdf"),
        }

    def test_valid_contract_accepts_file_uri_and_declared_output_roles_without_writes(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source.csv"
            source.write_text("real content must not be read", encoding="utf-8")
            ids_root = base / "IDS_DATA_ROOT"
            ids_root.mkdir()
            self._create_complete_slots(ids_root)
            paths = self._default_paths(base)

            report = module.evaluate_local_path_contract(
                source_uri=source.as_uri(),
                ids_data_root=str(ids_root),
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                **paths,
            )

            self.assertEqual(report["state"], "PATH_CONTRACT_OK")
            self.assertFalse(report["safe_mode"])
            self.assertEqual(report["stage"], "STAGE-010")
            self.assertEqual(report["acceptance_id"], "ACC-STAGE-010")
            self.assertEqual(report["entrance"], "IDS 系统运营入口")
            self.assertFalse(report["customer_visible"])
            self.assertEqual(report["source_uri"]["state"], "OK")
            self.assertEqual(report["storage_budget_state"], "BUDGET_OK")
            self.assertEqual(report["removable_drive_state"], "ONLINE_VALIDATED")
            for role in ["processed", "backup", "manifest", "report_export"]:
                self.assertEqual(report["path_roles"][role]["state"], "OK")
            for path in paths.values():
                self.assertFalse(Path(path).exists())
            serialized = json.dumps(report, ensure_ascii=False)
            self.assertNotIn("real content must not be read", serialized)
            self.assertTrue(report["does_not_create_ids_data_root"])
            self.assertTrue(report["does_not_scan_recursively"])
            self.assertTrue(report["does_not_generate_outputs"])
            self.assertTrue(report["does_not_write_runtime_data"])

    def test_invalid_source_uri_fails_closed_before_path_work(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            report = module.evaluate_local_path_contract(
                source_uri="https://example.com/source.csv",
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                **self._default_paths(base),
            )

        self.assertEqual(report["state"], "SOURCE_URI_INVALID")
        self.assertTrue(report["safe_mode"])
        self.assertIn("correct_source_uri", report["operator_actions"])
        self.assertIn("bulk_import", report["paused_workflows"])
        self.assertIsNone(report["source_uri"]["path"])
        self.assertTrue(report["does_not_open_source_files"])

    def test_missing_source_and_offline_root_are_not_ready_without_creating_root(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            missing_source = base / "missing.csv"
            missing_root = base / "MISSING_IDS_DATA_ROOT"

            report = module.evaluate_local_path_contract(
                source_uri=missing_source.as_uri(),
                ids_data_root=str(missing_root),
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                **self._default_paths(base),
            )

            self.assertFalse(missing_source.exists())
            self.assertFalse(missing_root.exists())

        self.assertEqual(report["state"], "SOURCE_PATH_NOT_READY")
        self.assertTrue(report["safe_mode"])
        self.assertEqual(report["source_uri"]["state"], "SOURCE_PATH_NOT_READY")
        self.assertEqual(report["removable_drive_state"], "OFFLINE")
        self.assertIn("reconnect_or_configure_ids_data_root", report["operator_actions"])
        self.assertTrue(report["requires_revalidation"])

    def test_unbounded_processed_output_blocks_before_writes(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source.csv"
            source.write_text("fixture", encoding="utf-8")
            paths = self._default_paths(base)
            paths["processed_path"] = "relative/processed"

            report = module.evaluate_local_path_contract(
                source_uri=source.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=None,
                job_kind="embedding",
                require_external_root=False,
                **paths,
            )

        self.assertEqual(report["state"], "PROCESSED_PATH_UNBOUNDED")
        self.assertTrue(report["safe_mode"])
        self.assertEqual(report["path_roles"]["processed"]["state"], "PROCESSED_PATH_UNBOUNDED")
        self.assertEqual(report["storage_budget_state"], "UNBOUNDED_OUTPUT_RISK")
        self.assertIn("declare_output_budget_or_cap", report["operator_actions"])
        self.assertTrue(report["does_not_generate_outputs"])

    def test_backup_manifest_and_report_export_paths_are_classified_independently(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source.csv"
            source.write_text("fixture", encoding="utf-8")
            paths = self._default_paths(base)

            backup = module.evaluate_local_path_contract(
                source_uri=source.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                require_external_root=False,
                **{**paths, "backup_path": str(source)},
            )
            manifest = module.evaluate_local_path_contract(
                source_uri=source.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                require_external_root=False,
                **{**paths, "manifest_path": str(base / "manifest.secret")},
            )
            report_export = module.evaluate_local_path_contract(
                source_uri=source.as_uri(),
                ids_data_root="",
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=20 * GIB,
                require_external_root=False,
                **{**paths, "report_export_path": ""},
            )

        self.assertEqual(backup["state"], "BACKUP_PATH_UNSAFE")
        self.assertEqual(backup["path_roles"]["backup"]["state"], "BACKUP_PATH_UNSAFE")
        self.assertEqual(manifest["state"], "MANIFEST_PATH_UNSAFE")
        self.assertEqual(manifest["path_roles"]["manifest"]["state"], "MANIFEST_PATH_UNSAFE")
        self.assertEqual(report_export["state"], "REPORT_EXPORT_PATH_UNSAFE")
        self.assertEqual(
            report_export["path_roles"]["report_export"]["state"],
            "REPORT_EXPORT_PATH_UNSAFE",
        )

    def test_cli_json_contract_is_stage010_operations_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source.csv"
            source.write_text("fixture", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-uri",
                    source.as_uri(),
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
        self.assertEqual(payload["schema_version"], "ids.stage010.local_path_contract.v1")
        self.assertEqual(payload["stage"], "STAGE-010")
        self.assertEqual(payload["acceptance_id"], "ACC-STAGE-010")
        self.assertEqual(payload["state"], "PATH_CONTRACT_OK")
        self.assertFalse(payload["customer_visible"])
        self.assertTrue(payload["bounded_preflight_only"])
        self.assertTrue(payload["does_not_start_services"])
        self.assertTrue(payload["does_not_scan_external_drive_contents"])
        self.assertTrue(payload["does_not_generate_outputs"])


if __name__ == "__main__":
    unittest.main()
