import csv
import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.a0_golden_fixture import (
    build_a0_golden_fixture,
    validate_a0_golden_fixture,
    validate_private_value_receipt,
)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in records) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def sample_a0_manifest(file_count: int = 2) -> dict:
    files = []
    for index in range(1, file_count + 1):
        file_id = f"A0-FILE-PUB-V2-{index:03d}"
        files.append(
            {
                "record_type": "a0_source_file_public_projection",
                "schema_version": "kmfa.a0_source_file.public_projection.v2",
                "a0_file_id": file_id,
                "file_format": "xlsx" if index == 1 else "pdf",
                "source_package_ref": "A0-SOURCE-PACKAGE-PUB-V2",
                "source_file_ref": f"A0-SOURCE-FILE-PUB-V2-{index:03d}",
            }
        )
    return {
        "record_type": "a0_file_registration_public_projection",
        "schema_version": "kmfa.a0_file_registration.public_projection.v2",
        "files": files,
    }


def sample_candidates(file_count: int = 2) -> list[dict]:
    return [
        {
            "record_type": "a0_project_candidate_public_projection",
            "schema_version": "kmfa.a0_project_candidate.public_projection.v2",
            "candidate_id": f"A0-CAND-PUB-V2-{index:03d}",
            "a0_file_id": f"A0-FILE-PUB-V2-{index:03d}",
        }
        for index in range(1, file_count + 1)
    ]


class A0GoldenFixtureTests(unittest.TestCase):
    def test_builds_public_safe_pending_fixture_candidates_without_private_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "a0_file_manifest.json"
            candidates_path = root / "a0_project_candidates.jsonl"
            write_json(manifest_path, sample_a0_manifest())
            write_jsonl(candidates_path, sample_candidates())

            manifest, fixture_records = build_a0_golden_fixture(
                a0_file_manifest=manifest_path,
                a0_project_candidates=candidates_path,
                generated_at="2026-06-30T01:00:00+10:00",
            )

        validate_a0_golden_fixture(manifest, fixture_records)
        self.assertEqual(manifest["field_summary"]["a0_project_candidates"], 2)
        self.assertEqual(manifest["field_summary"]["required_fields_per_candidate"], 5)
        self.assertEqual(manifest["field_summary"]["fixture_candidate_count"], 10)
        self.assertEqual(manifest["field_summary"]["private_binding_verified_count"], 0)
        self.assertTrue(all(item["quality_state"]["machine_candidate_quality_grade"] == "Q3" for item in fixture_records))
        self.assertTrue(all(item["quality_state"]["q4_human_confirmed"] is False for item in fixture_records))
        self.assertTrue(all(item["quality_state"]["q5_calculation_baseline_allowed"] is False for item in fixture_records))
        serialized = json.dumps(fixture_records, ensure_ascii=False)
        for forbidden in ("source_package_hash", "source_public_inventory_path_hash", "raw_value_hash", "normalized_value_hash"):
            self.assertNotIn(forbidden, serialized)

    def test_hashes_private_values_without_committing_plaintext(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "a0_file_manifest.json"
            candidates_path = root / "a0_project_candidates.jsonl"
            private_csv = root / "private_fields.csv"
            write_json(manifest_path, sample_a0_manifest(file_count=1))
            write_jsonl(candidates_path, sample_candidates(file_count=1))
            write_csv(
                private_csv,
                ["candidate_id", "field_key", "source_file_ref", "page_ref", "sheet_ref", "cell_ref", "raw_value", "unit"],
                [
                    {
                        "candidate_id": "A0-CAND-PUB-V2-001",
                        "field_key": "contract_amount",
                        "source_file_ref": "A0-SOURCE-FILE-PUB-V2-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B2",
                        "raw_value": "100.00",
                        "unit": "yuan",
                    },
                    {
                        "candidate_id": "A0-CAND-PUB-V2-001",
                        "field_key": "total_expense",
                        "source_file_ref": "A0-SOURCE-FILE-PUB-V2-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B3",
                        "raw_value": "60.00",
                        "unit": "yuan",
                    },
                    {
                        "candidate_id": "A0-CAND-PUB-V2-001",
                        "field_key": "gross_profit",
                        "source_file_ref": "A0-SOURCE-FILE-PUB-V2-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B4",
                        "raw_value": "40.00",
                        "unit": "yuan",
                    },
                    {
                        "candidate_id": "A0-CAND-PUB-V2-001",
                        "field_key": "gross_margin",
                        "source_file_ref": "A0-SOURCE-FILE-PUB-V2-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B5",
                        "raw_value": "40%",
                        "unit": "",
                    },
                    {
                        "candidate_id": "A0-CAND-PUB-V2-001",
                        "field_key": "cost_category",
                        "source_file_ref": "A0-SOURCE-FILE-PUB-V2-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B6",
                        "raw_value": "材料",
                        "unit": "",
                    },
                ],
            )

            manifest, fixture_records = build_a0_golden_fixture(
                a0_file_manifest=manifest_path,
                a0_project_candidates=candidates_path,
                private_fields_csv=private_csv,
                private_receipt_path=root / "private" / "fixture_receipt.json",
                generated_at="2026-06-30T01:00:00+10:00",
            )
            receipt_path = root / "private" / "fixture_receipt.json"
            validate_a0_golden_fixture(
                manifest,
                fixture_records,
                require_private_values=True,
                private_receipt_path=receipt_path,
            )
            private_receipt = validate_private_value_receipt(receipt_path, expected_count=5)
            serialized = json.dumps({"manifest": manifest, "fixture_records": fixture_records}, ensure_ascii=False)

        self.assertEqual(manifest["field_summary"]["private_binding_verified_count"], 5)
        self.assertTrue(all(item["value_binding"]["private_binding_receipt_status"] == "verified_private_receipt" for item in fixture_records))
        self.assertEqual(private_receipt["binding_count"], 5)
        self.assertIn("raw_value_sha256", private_receipt["bindings"][0])
        self.assertNotIn("raw_value_sha256", serialized)
        self.assertNotIn('"raw_value":', serialized)
        self.assertNotIn('"normalized_value":', serialized)
        self.assertNotIn("100.00", serialized)
        self.assertNotIn("材料", serialized)

    def test_private_fields_require_private_receipt_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "a0_file_manifest.json"
            candidates_path = root / "a0_project_candidates.jsonl"
            private_csv = root / "private_fields.csv"
            write_json(manifest_path, sample_a0_manifest(file_count=1))
            write_jsonl(candidates_path, sample_candidates(file_count=1))
            write_csv(
                private_csv,
                ["candidate_id", "field_key", "source_file_ref", "page_ref", "sheet_ref", "cell_ref", "raw_value", "unit"],
                [{
                    "candidate_id": "A0-CAND-PUB-V2-001",
                    "field_key": "contract_amount",
                    "source_file_ref": "A0-SOURCE-FILE-PUB-V2-001",
                    "page_ref": "1",
                    "sheet_ref": "",
                    "cell_ref": "",
                    "raw_value": "100",
                    "unit": "yuan",
                }],
            )
            with self.assertRaisesRegex(ValueError, "private_receipt_path"):
                build_a0_golden_fixture(
                    a0_file_manifest=manifest_path,
                    a0_project_candidates=candidates_path,
                    private_fields_csv=private_csv,
                )

    def test_rejects_public_raw_value_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "a0_file_manifest.json"
            candidates_path = root / "a0_project_candidates.jsonl"
            write_json(manifest_path, sample_a0_manifest(file_count=1))
            write_jsonl(candidates_path, sample_candidates(file_count=1))
            manifest, fixture_records = build_a0_golden_fixture(
                a0_file_manifest=manifest_path,
                a0_project_candidates=candidates_path,
                generated_at="2026-06-30T01:00:00+10:00",
            )

        fixture_records[0]["raw_value"] = "must not be public"
        with self.assertRaises(ValueError):
            validate_a0_golden_fixture(manifest, fixture_records)


if __name__ == "__main__":
    unittest.main()
