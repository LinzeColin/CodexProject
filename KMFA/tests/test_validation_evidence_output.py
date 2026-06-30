import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.validation_evidence_output import (
    ValidationEvidenceError,
    build_validation_evidence,
    write_validation_evidence_outputs,
)


class ValidationEvidenceOutputTests(unittest.TestCase):
    def _zero_delta_result(self) -> dict:
        return {
            "record_type": "zero_delta_validation_result",
            "schema_version": "kmfa.zero_delta_validation_result.v1",
            "stage_phase": "S06-P1",
            "status": "failed",
            "zero_delta_passed": False,
            "zero_delta_cents": 0,
            "minimum_fail_difference_cents": 1,
            "mismatch_count": 1,
            "mismatches": [
                {
                    "record_type": "zero_delta_mismatch",
                    "schema_version": "kmfa.zero_delta_mismatch.v1",
                    "record_id": "SYN-PROJECT-S06P3-001",
                    "source": "A0_Q5_SYNTHETIC_BASELINE=>SYSTEM_RECOMPUTE_SYNTHETIC",
                    "field": "contract_amount_cents",
                    "authoritative_value_cents": 10000,
                    "system_value_cents": 9999,
                    "difference_cents": 1,
                }
            ],
            "raw_business_data_used": False,
            "public_safe_fixture_only": True,
        }

    def _queue_items(self) -> list[dict]:
        return [
            {
                "record_type": "cross_source_difference_queue_item",
                "schema_version": "kmfa.cross_source_difference_queue.v1",
                "stage_phase": "S06-P2",
                "queue_id": "CDQ-20260630-150000-s06p3test001",
                "project_ref": "SYN-PROJECT-S06P3-001",
                "field": "contract_amount_cents",
                "source_refs": [
                    {
                        "source_id": "SRC-S06P3-PDF-SYNTHETIC",
                        "source_type": "pdf",
                        "source_class": "raw_upload",
                        "source_anchor_ref": "sha256:synthetic-pdf-anchor",
                    },
                    {
                        "source_id": "SRC-S06P3-EXCEL-SYNTHETIC",
                        "source_type": "excel",
                        "source_class": "authorized_export",
                        "source_anchor_ref": "sha256:synthetic-excel-anchor",
                    },
                ],
                "difference_cents": 1,
                "status": "queued_for_manual_review",
                "resolution_policy": "manual_review_required",
                "auto_correction_allowed": False,
                "averaging_allowed": False,
                "rounding_mask_allowed": False,
                "auto_selection_allowed": False,
                "report_grade_a_allowed": False,
                "raw_business_data_used": False,
                "public_safe_fixture_only": True,
                "evidence_ref": "unit-test",
            }
        ]

    def _report_gate(self) -> dict:
        return {
            "record_type": "cross_source_difference_report_grade_gate",
            "schema_version": "kmfa.cross_source_difference_report_grade_gate.v1",
            "stage_phase": "S06-P2",
            "status": "blocked",
            "report_grade_a_allowed": False,
            "maximum_report_grade": "B",
            "hard_block_reason": "unresolved_critical_difference",
            "blocking_queue_ids": ["CDQ-20260630-150000-s06p3test001"],
            "raw_business_data_used": False,
            "public_safe_fixture_only": True,
        }

    def _seed_metadata_quality(self, metadata_quality_dir: Path) -> None:
        metadata_quality_dir.mkdir(parents=True)
        (metadata_quality_dir / "zero_delta_results.jsonl").write_text(
            json.dumps(
                {
                    "record_type": "protocol_header",
                    "schema_version": "kmfa.zero_delta_results.v1",
                    "stage_phase": "S02-P1",
                    "status": "protocol_defined_no_zero_delta_results_committed",
                    "allowed_record_types": ["zero_delta_result"],
                    "forbidden_plaintext": True,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (metadata_quality_dir / "data_quality_results.jsonl").write_text(
            json.dumps(
                {
                    "record_type": "protocol_header",
                    "schema_version": "kmfa.data_quality_results.v1",
                    "stage_phase": "S02-P3",
                    "status": "protocol_defined_no_quality_results_committed",
                    "allowed_record_types": ["data_quality_result"],
                    "allowed_quality_grades": ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5"],
                    "forbidden_plaintext": True,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (metadata_quality_dir / "source_difference_queue.jsonl").write_text(
            json.dumps(
                {
                    "record_type": "protocol_header",
                    "schema_version": "kmfa.source_difference_queue.v1",
                    "stage_phase": "S03-P3",
                    "status": "protocol_defined_no_difference_items_committed",
                    "allowed_record_types": ["source_difference_queue_item"],
                    "auto_selection_allowed": False,
                    "forbidden_plaintext": True,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (metadata_quality_dir / "mismatch_report.csv").write_text(
            "mismatch_id,source_id,file_hash,field_path,mapping_version,formula_version,status,evidence_ref\n",
            encoding="utf-8",
        )

    def test_builds_public_safe_stage_outputs_and_project_validation_status(self) -> None:
        evidence = build_validation_evidence(
            zero_delta_result=self._zero_delta_result(),
            queue_items=self._queue_items(),
            report_gate=self._report_gate(),
            evidence_time="2026-06-30T15:00:00+10:00",
            source_result_ref="unit/zero_delta_result.json",
            source_mismatch_report_ref="unit/mismatch_report.csv",
            source_queue_ref="unit/source_difference_queue.jsonl",
            source_gate_ref="unit/report_grade_gate.json",
        )

        zero_delta_output = evidence["zero_delta_result"]
        self.assertEqual(zero_delta_output["stage_phase"], "S06-P3")
        self.assertFalse(zero_delta_output["zero_delta_passed"])
        self.assertEqual(zero_delta_output["mismatch_count"], 1)
        self.assertNotIn("mismatches", zero_delta_output)
        self.assertFalse(zero_delta_output["raw_business_data_used"])
        self.assertTrue(zero_delta_output["forbidden_plaintext"])

        statuses = evidence["project_validation_statuses"]
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0]["project_ref"], "SYN-PROJECT-S06P3-001")
        self.assertEqual(statuses[0]["validation_status"], "blocked")
        self.assertIn("zero_delta_failed", statuses[0]["hard_blocks"])
        self.assertIn("unresolved_critical_difference", statuses[0]["hard_blocks"])
        self.assertFalse(statuses[0]["q5_allowed"])
        self.assertEqual(statuses[0]["quality_grade"], "Q4")

    def test_writes_metadata_quality_records_without_field_plaintext_or_raw_values(self) -> None:
        evidence = build_validation_evidence(
            zero_delta_result=self._zero_delta_result(),
            queue_items=self._queue_items(),
            report_gate=self._report_gate(),
            evidence_time="2026-06-30T15:00:00+10:00",
            source_result_ref="unit/zero_delta_result.json",
            source_mismatch_report_ref="unit/mismatch_report.csv",
            source_queue_ref="unit/source_difference_queue.jsonl",
            source_gate_ref="unit/report_grade_gate.json",
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "stage"
            metadata_quality_dir = Path(tmp) / "metadata" / "quality"
            self._seed_metadata_quality(metadata_quality_dir)

            write_validation_evidence_outputs(
                evidence,
                output_dir=output_dir,
                metadata_quality_dir=metadata_quality_dir,
            )

            zero_delta_records = [
                json.loads(line)
                for line in (metadata_quality_dir / "zero_delta_results.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            data_quality_records = [
                json.loads(line)
                for line in (metadata_quality_dir / "data_quality_results.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            queue_records = [
                json.loads(line)
                for line in (metadata_quality_dir / "source_difference_queue.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            mismatch_rows = list(
                csv.DictReader((metadata_quality_dir / "mismatch_report.csv").read_text(encoding="utf-8").splitlines())
            )

        self.assertEqual(zero_delta_records[-1]["record_type"], "zero_delta_result")
        self.assertEqual(data_quality_records[-1]["record_type"], "data_quality_result")
        self.assertEqual(queue_records[-1]["record_type"], "source_difference_queue_item")
        self.assertTrue(zero_delta_records[-1]["forbidden_plaintext"])
        self.assertTrue(data_quality_records[-1]["forbidden_plaintext"])
        self.assertTrue(queue_records[-1]["forbidden_plaintext"])
        self.assertTrue(mismatch_rows[0]["field_path"].startswith("field_ref:sha256:"))

        combined_output = json.dumps(
            {
                "zero_delta": zero_delta_records[-1],
                "data_quality": data_quality_records[-1],
                "queue": queue_records[-1],
                "mismatch": mismatch_rows,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        self.assertNotIn("contract_amount_cents", combined_output)
        self.assertNotIn("authoritative_value_cents", combined_output)
        self.assertNotIn("system_value_cents", combined_output)
        self.assertNotIn("10000", combined_output)
        self.assertNotIn("9999", combined_output)

    def test_rejects_raw_business_data_flags(self) -> None:
        result = self._zero_delta_result()
        result["raw_business_data_used"] = True

        with self.assertRaises(ValidationEvidenceError):
            build_validation_evidence(
                zero_delta_result=result,
                queue_items=self._queue_items(),
                report_gate=self._report_gate(),
                evidence_time="2026-06-30T15:00:00+10:00",
                source_result_ref="unit/zero_delta_result.json",
                source_mismatch_report_ref="unit/mismatch_report.csv",
                source_queue_ref="unit/source_difference_queue.jsonl",
                source_gate_ref="unit/report_grade_gate.json",
            )

    def test_cli_generates_stage_artifacts_and_metadata_quality(self) -> None:
        root = Path(__file__).resolve().parents[2]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            zero_delta_path = tmp_path / "zero_delta_source.json"
            queue_path = tmp_path / "queue_source.jsonl"
            gate_path = tmp_path / "gate_source.json"
            mismatch_source_path = tmp_path / "mismatch_source.csv"
            output_dir = tmp_path / "stage"
            metadata_quality_dir = tmp_path / "metadata" / "quality"
            self._seed_metadata_quality(metadata_quality_dir)

            zero_delta_path.write_text(json.dumps(self._zero_delta_result(), ensure_ascii=False), encoding="utf-8")
            queue_path.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in self._queue_items()) + "\n",
                encoding="utf-8",
            )
            gate_path.write_text(json.dumps(self._report_gate(), ensure_ascii=False), encoding="utf-8")
            mismatch_source_path.write_text(
                "record_id,source,field,authoritative_value_cents,system_value_cents,difference_cents\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "KMFA/tools/validation_evidence_output.py",
                    "--zero-delta-result",
                    str(zero_delta_path),
                    "--source-mismatch-report",
                    str(mismatch_source_path),
                    "--difference-queue",
                    str(queue_path),
                    "--report-gate",
                    str(gate_path),
                    "--output-dir",
                    str(output_dir),
                    "--metadata-quality-dir",
                    str(metadata_quality_dir),
                    "--evidence-time",
                    "2026-06-30T15:00:00+10:00",
                ],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            stage_zero_delta = json.loads((output_dir / "zero_delta_result.json").read_text(encoding="utf-8"))
            metadata_zero_delta = (metadata_quality_dir / "zero_delta_results.jsonl").read_text(encoding="utf-8")

        self.assertIn('"project_statuses": 1', result.stdout)
        self.assertEqual(stage_zero_delta["stage_phase"], "S06-P3")
        self.assertIn('"record_type": "zero_delta_result"', metadata_zero_delta)


if __name__ == "__main__":
    unittest.main()
