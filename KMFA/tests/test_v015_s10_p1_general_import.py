from __future__ import annotations

import copy
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

from KMFA.tools import v015_s10_p1_general_import as importer


class GeneralImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.context = {
            "source_id": "SRC-test-upload-1234abcd",
            "source_label": "测试文件",
            "entity_label": "测试主体",
            "business_segment": "项目成本",
            "period": "2026-06",
            "parser_version": "1.0.0",
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _csv(self, name: str = "sample.csv") -> Path:
        path = self.root / name
        path.write_text("project,cost\nA,100\n", encoding="utf-8")
        return path

    def _zip(self, name: str = "sample.zip") -> Path:
        path = self.root / name
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("nested/data.csv", "project,cost\nA,100\n")
        return path

    def _preview_and_confirmation(self, path: Path, **context: str):
        supplied = {**self.context, **context}
        preview = importer.build_import_preview(importer.inspect_file(path), **supplied)
        event = importer.confirm_import_preview(
            preview,
            preview_id=preview["preview_id"],
            preview_fingerprint=preview["preview_fingerprint"],
            decision="CONFIRM",
            operator_role="ROLE::FINANCE",
            occurred_at="2026-07-15T22:00:00+10:00",
        )
        return preview, event

    def test_public_verification_has_32_real_passing_checks(self) -> None:
        result = importer.public_verification()
        self.assertEqual(result["accounting"], {"total": 32, "passed": 32, "failed": 0})
        self.assertTrue(all(row["status"] == "PASS" for row in result["checks"]))
        self.assertEqual({row["check_id"] for row in result["checks"]}, set(importer.CHECK_IDS))
        self.assertEqual(result["raw_root_access_count"], 0)

    def test_supported_format_matrix_and_guidance(self) -> None:
        csv_file = self._csv()
        zip_file = self._zip()
        pdf = self.root / "sample.pdf"
        pdf.write_bytes(b"%PDF-1.7\nsynthetic\n%%EOF\n")
        xls = self.root / "sample.xls"
        xls.write_bytes(importer.OLE_MAGIC + b"SYNTHETIC")
        wps = self.root / "sample.et"
        wps.write_bytes(importer.OLE_MAGIC + b"SYNTHETIC")
        xlsx = self.root / "sample.xlsx"
        importer._write_minimal_xlsx(xlsx)
        actual = {
            importer.inspect_file(path)["format_code"]
            for path in (csv_file, zip_file, pdf, xls, wps, xlsx)
        }
        self.assertEqual(actual, set(importer.FORMAT_LABELS_ZH))
        for path in (csv_file, zip_file, pdf, xls, wps, xlsx):
            inspected = importer.inspect_file(path)
            self.assertTrue(inspected["format_guidance_zh"])
            self.assertTrue(inspected["file_hash"].startswith("sha256:"))

    def test_archive_path_traversal_symlink_and_bomb_are_rejected_before_extraction(self) -> None:
        cases = []
        traversal = self.root / "traversal.zip"
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("../escape.csv", "a,b\n1,2\n")
        cases.append((traversal, importer.DEFAULT_ARCHIVE_POLICY, "ARCHIVE_PATH_TRAVERSAL_REJECTED"))

        symlink = self.root / "symlink.zip"
        with zipfile.ZipFile(symlink, "w") as archive:
            info = zipfile.ZipInfo("link.csv")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "target.csv")
        cases.append((symlink, importer.DEFAULT_ARCHIVE_POLICY, "ARCHIVE_SYMLINK_REJECTED"))

        bomb = self.root / "bomb.zip"
        with zipfile.ZipFile(bomb, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("large.csv", b"0" * 250000)
        cases.append((bomb, importer.ArchivePolicy(max_compression_ratio=5), "ARCHIVE_COMPRESSION_BOMB_REJECTED"))

        for index, (path, policy, expected_code) in enumerate(cases):
            with self.subTest(expected_code=expected_code):
                destination = self.root / f"extract-{index}"
                with self.assertRaises(importer.GeneralImportError) as caught:
                    importer._extract_zip_atomic(path, destination, policy)
                self.assertEqual(caught.exception.code, expected_code)
                self.assertFalse(destination.exists())
                self.assertFalse(destination.with_name(f".{destination.name}.extracting").exists())

    def test_bad_file_is_quarantined_without_blocking_good_files(self) -> None:
        bad = self.root / "bad.pdf"
        bad.write_bytes(b"not-a-pdf")
        batch = importer.inspect_batch(
            (self._csv(), bad, self._zip()),
            (self.context, self.context, self.context),
        )
        self.assertEqual(batch["preview_ready_count"], 2)
        self.assertEqual(batch["quarantined_count"], 1)
        self.assertFalse(batch["batch_aborted_by_single_bad_file"])
        self.assertEqual(batch["quarantined"][0]["reason_code"], "PDF_STRUCTURE_REJECTED")

    def test_preview_is_human_readable_and_confirmation_is_mandatory(self) -> None:
        preview = importer.build_import_preview(importer.inspect_file(self._csv()), **self.context)
        self.assertEqual(preview["preview_status"], "READY_FOR_CONFIRMATION")
        self.assertTrue(preview["user_confirmation_required"])
        self.assertFalse(preview["processing_allowed"])
        self.assertFalse(preview["source_mutation_performed"])
        for field in importer.REQUIRED_PREVIEW_FIELDS:
            self.assertIn(field, preview)
        with self.assertRaises(importer.GeneralImportError):
            importer.process_confirmed_import(
                self._csv(), preview, {}, private_root=self.root / "private-unconfirmed"
            )
        self.assertFalse((self.root / "private-unconfirmed").exists())

    def test_missing_context_and_tampering_fail_closed(self) -> None:
        inspection = importer.inspect_file(self._csv())
        preview = importer.build_import_preview(inspection, **{**self.context, "entity_label": None})
        with self.assertRaises(importer.GeneralImportError) as caught:
            importer.confirm_import_preview(
                preview,
                preview_id=preview["preview_id"],
                preview_fingerprint=preview["preview_fingerprint"],
                decision="CONFIRM",
                operator_role="ROLE::FINANCE",
                occurred_at="2026-07-15T22:00:00+10:00",
            )
        self.assertEqual(caught.exception.code, "PREVIEW_CONTEXT_INCOMPLETE")
        changed = copy.deepcopy(preview)
        changed["period"]["value"] = "2026-07"
        with self.assertRaises(importer.GeneralImportError) as caught:
            importer.confirm_import_preview(
                changed,
                preview_id=preview["preview_id"],
                preview_fingerprint=preview["preview_fingerprint"],
                decision="CONFIRM",
                operator_role="ROLE::FINANCE",
                occurred_at="2026-07-15T22:00:00+10:00",
            )
        self.assertEqual(caught.exception.code, "PREVIEW_FINGERPRINT_MISMATCH")

    def test_source_change_after_preview_requires_new_preview(self) -> None:
        source = self._csv()
        preview, event = self._preview_and_confirmation(source)
        source.write_text("project,cost\nA,101\n", encoding="utf-8")
        with self.assertRaises(importer.GeneralImportError) as caught:
            importer.process_confirmed_import(source, preview, event, private_root=self.root / "private")
        self.assertEqual(caught.exception.code, "SOURCE_CHANGED_AFTER_PREVIEW")
        self.assertFalse((self.root / "private").exists())

    def test_interruption_is_invisible_then_resume_commits_once(self) -> None:
        source = self._zip()
        preview, event = self._preview_and_confirmation(source)
        private = self.root / "private"
        with self.assertRaises(importer.ImportInterrupted):
            importer.process_confirmed_import(
                source, preview, event, private_root=private, interrupt_at="AFTER_STAGE"
            )
        self.assertEqual(importer.list_committed_imports(private), [])
        result = importer.process_confirmed_import(source, preview, event, private_root=private)
        self.assertEqual(result["outcome"], "COMMITTED")
        self.assertTrue(result["resumed_from_checkpoint"])
        self.assertEqual(len(importer.list_committed_imports(private)), 1)
        self.assertTrue((private / str(result["record"]["private_extracted_relative_path"])).is_dir())

    def test_interruption_before_commit_keeps_partial_work_invisible(self) -> None:
        source = self._csv()
        preview, event = self._preview_and_confirmation(source)
        private = self.root / "private"
        with self.assertRaises(importer.ImportInterrupted):
            importer.process_confirmed_import(
                source, preview, event, private_root=private, interrupt_at="BEFORE_COMMIT"
            )
        self.assertEqual(importer.list_committed_imports(private), [])
        result = importer.process_confirmed_import(source, preview, event, private_root=private)
        self.assertEqual(result["outcome"], "COMMITTED")
        self.assertTrue(result["resumed_from_checkpoint"])

    def test_exact_replay_reuses_record_and_new_parser_version_coexists(self) -> None:
        source = self._csv()
        private = self.root / "private"
        preview, event = self._preview_and_confirmation(source)
        first = importer.process_confirmed_import(source, preview, event, private_root=private)
        replay = importer.process_confirmed_import(source, preview, event, private_root=private)
        self.assertEqual(replay["outcome"], "REUSED")
        self.assertEqual(replay["record"], first["record"])
        self.assertEqual(replay["visible_committed_count"], 1)

        preview_v2, event_v2 = self._preview_and_confirmation(source, parser_version="1.1.0")
        second = importer.process_confirmed_import(source, preview_v2, event_v2, private_root=private)
        self.assertEqual(second["outcome"], "COMMITTED")
        self.assertEqual(second["visible_committed_count"], 2)
        self.assertNotEqual(first["record"]["idempotency_key"], second["record"]["idempotency_key"])

    def test_corrupt_committed_object_fails_closed(self) -> None:
        source = self._csv()
        private = self.root / "private"
        preview, event = self._preview_and_confirmation(source)
        committed = importer.process_confirmed_import(source, preview, event, private_root=private)
        object_path = private / committed["record"]["private_object_relative_path"]
        object_path.write_bytes(b"corrupt")
        with self.assertRaises(importer.GeneralImportError) as caught:
            importer.process_confirmed_import(source, preview, event, private_root=private)
        self.assertEqual(caught.exception.code, "COMMITTED_OBJECT_HASH_MISMATCH")


if __name__ == "__main__":
    unittest.main()
