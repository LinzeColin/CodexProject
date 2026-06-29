import hashlib
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from KMFA.tools.file_import_register import (
    UnsafeArchiveError,
    build_import_registration,
    safe_extract_zip,
)


class FileImportRegisterTests(unittest.TestCase):
    def test_registers_supported_files_with_hash_batch_and_private_storage_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "项目成本.csv"
            csv_path.write_bytes("project,cost\nA,100\n".encode("utf-8"))

            registration = build_import_registration(
                csv_path,
                batch_slug="project-cost",
                source_slug="sales-performance",
                received_at="2026-06-29T18:55:00+10:00",
            )

        expected_hash = hashlib.sha256("project,cost\nA,100\n".encode("utf-8")).hexdigest()
        manifest = registration["raw_file_manifest"]
        import_run = registration["import_run"]
        source = registration["source"]

        self.assertEqual(manifest["file_hash"], f"sha256:{expected_hash}")
        self.assertEqual(manifest["file_size_bytes"], 19)
        self.assertEqual(manifest["file_format"], "csv")
        self.assertEqual(manifest["manifest_status"], "registered")
        self.assertEqual(manifest["storage_ref"].split("/")[0], "private:")
        self.assertNotIn("项目成本.csv", json.dumps(registration, ensure_ascii=False))
        self.assertRegex(manifest["original_filename_hash"], r"^sha256:[a-f0-9]{64}$")
        self.assertRegex(
            import_run["import_run_id"],
            r"^IMP-20260629-185500-project-cost-[a-f0-9]{8}$",
        )
        self.assertRegex(source["source_id"], r"^SRC-sales-performance-[a-f0-9]{8}$")
        self.assertEqual(import_run["record_type"], "import_run")
        self.assertEqual(source["record_type"], "source_registry_entry")

    def test_identifies_ole_and_wps_formats_with_actionable_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xls_path = root / "legacy.xls"
            xls_path.write_bytes(bytes.fromhex("d0cf11e0a1b11ae1") + b"legacy-ole")
            wps_path = root / "spreadsheet.et"
            wps_path.write_bytes(b"wps-et-content")

            ole_registration = build_import_registration(
                xls_path,
                batch_slug="legacy-finance",
                source_slug="finance",
                received_at="2026-06-29T18:56:00+10:00",
            )
            wps_registration = build_import_registration(
                wps_path,
                batch_slug="wps-export",
                source_slug="wps",
                received_at="2026-06-29T18:57:00+10:00",
            )

        self.assertEqual(ole_registration["raw_file_manifest"]["file_format"], "xls")
        self.assertEqual(ole_registration["raw_file_manifest"]["container_type"], "ole_compound")
        self.assertIn("转换为 .xlsx 或 .csv", ole_registration["operator_guidance"])
        self.assertEqual(wps_registration["raw_file_manifest"]["file_format"], "wps")
        self.assertEqual(wps_registration["raw_file_manifest"]["container_type"], "wps_native")
        self.assertIn("WPS 导出为 .xlsx 或 .csv", wps_registration["operator_guidance"])

    def test_safe_extract_zip_allows_nested_members_and_blocks_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "safe.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("nested/report.csv", "a,b\n1,2\n")

            extract_dir = root / "extract"
            members = safe_extract_zip(zip_path, extract_dir)

            self.assertEqual(members[0]["member_path"], "nested/report.csv")
            self.assertTrue((extract_dir / "nested" / "report.csv").is_file())

            bad_zip = root / "bad.zip"
            with zipfile.ZipFile(bad_zip, "w") as archive:
                archive.writestr("../escape.csv", "no")

            with self.assertRaises(UnsafeArchiveError):
                safe_extract_zip(bad_zip, root / "bad_extract")


if __name__ == "__main__":
    unittest.main()
