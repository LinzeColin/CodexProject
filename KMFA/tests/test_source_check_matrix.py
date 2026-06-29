import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.source_check_matrix import (
    ALLOWED_STATUSES,
    append_status_event,
    build_source_matrix_row,
    build_status_event,
    validate_status,
)


class SourceCheckMatrixTests(unittest.TestCase):
    def sample_registration(self) -> dict:
        return {
            "import_run": {
                "import_run_id": "IMP-20260629-190500-project-cost-abcdef12",
                "source_id": "SRC-sales-export-12345678",
            },
            "raw_file_manifest": {
                "file_hash": "sha256:" + "1" * 64,
                "file_size_bytes": 42,
                "file_format": "csv",
                "source_package_ref": {
                    "source_id": "SRC-sales-export-12345678",
                    "source_package_hash": "sha256:" + "2" * 64,
                    "source_package_size_bytes": 42,
                    "source_package_storage_ref": "private://imports/IMP-20260629-190500-project-cost-abcdef12/sha256-x",
                },
            },
        }

    def test_builds_matrix_row_with_required_dimensions_and_no_plaintext_raw_fields(self) -> None:
        row = build_source_matrix_row(
            self.sample_registration(),
            source_system="sales-export",
            business_segment="project-cost",
            entity_ref="ENTITY-wuhan-kaiming",
            account_ref="ACCOUNT-cost-ledger",
            frequency="monthly",
            status="部分/阻塞",
            evidence_ref="unit-test",
        )

        self.assertEqual(row["record_type"], "source_check_matrix_row")
        self.assertRegex(row["matrix_id"], r"^SCM-[a-f0-9]{16}$")
        self.assertEqual(row["source_system"], "sales-export")
        self.assertEqual(row["business_segment"], "project-cost")
        self.assertEqual(row["source_package_ref"]["source_package_hash"], "sha256:" + "2" * 64)
        self.assertEqual(row["entity_ref"], "ENTITY-wuhan-kaiming")
        self.assertEqual(row["account_ref"], "ACCOUNT-cost-ledger")
        self.assertEqual(row["frequency"], "monthly")
        self.assertEqual(row["status"], "部分/阻塞")
        self.assertFalse(row["raw_layer_write_allowed"])
        self.assertNotIn("raw_rows", json.dumps(row, ensure_ascii=False))
        self.assertNotIn("original_filename", json.dumps(row, ensure_ascii=False))

    def test_allowed_statuses_are_exactly_taskpack_values(self) -> None:
        self.assertEqual(
            ALLOWED_STATUSES,
            ("已就绪", "部分/阻塞", "失败/不适用", "已过期", "人工复核"),
        )
        for status in ALLOWED_STATUSES:
            self.assertEqual(validate_status(status), status)
        with self.assertRaises(ValueError):
            validate_status("ready")

    def test_status_change_appends_metadata_event_without_mutating_row_or_raw_layer(self) -> None:
        row = build_source_matrix_row(
            self.sample_registration(),
            source_system="sales-export",
            business_segment="project-cost",
            entity_ref="ENTITY-wuhan-kaiming",
            account_ref="ACCOUNT-cost-ledger",
            frequency="monthly",
            status="部分/阻塞",
            evidence_ref="unit-test",
        )
        event = build_status_event(
            row,
            new_status="人工复核",
            reason_code="missing-account-owner",
            actor_ref="owner",
            event_time="2026-06-29T19:25:00+10:00",
            evidence_ref="unit-test",
        )

        self.assertEqual(row["status"], "部分/阻塞")
        self.assertEqual(event["previous_status"], "部分/阻塞")
        self.assertEqual(event["new_status"], "人工复核")
        self.assertFalse(event["raw_layer_write_allowed"])
        self.assertEqual(event["target_layer"], "metadata")
        self.assertRegex(event["event_id"], r"^SSE-20260629-192500-[a-f0-9]{12}$")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source_status_events.jsonl"
            append_status_event(path, event)
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(records, [event])

    def test_direct_cli_entrypoint_outputs_matrix_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registration_path = root / "registration.json"
            registration_path.write_text(json.dumps(self.sample_registration()), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "KMFA/tools/source_check_matrix.py",
                    "--registration-json",
                    str(registration_path),
                    "--source-system",
                    "sales-export",
                    "--business-segment",
                    "project-cost",
                    "--entity-ref",
                    "ENTITY-wuhan-kaiming",
                    "--account-ref",
                    "ACCOUNT-cost-ledger",
                    "--frequency",
                    "monthly",
                    "--status",
                    "部分/阻塞",
                    "--evidence-ref",
                    "unit-test",
                ],
                cwd=Path(__file__).resolve().parents[2],
                check=True,
                capture_output=True,
                text=True,
            )

        row = json.loads(result.stdout)
        self.assertEqual(row["record_type"], "source_check_matrix_row")
        self.assertEqual(row["status"], "部分/阻塞")


if __name__ == "__main__":
    unittest.main()
