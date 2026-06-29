import csv
import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.a0_golden_fixture import build_a0_golden_fixture, validate_a0_golden_fixture


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
        file_id = f"A0-FILE-{index:03d}"
        files.append(
            {
                "a0_file_id": file_id,
                "file_format": "xlsx" if index == 1 else "pdf",
                "member_path_hash": "sha256:" + f"{index}".zfill(64),
                "source_package_hash": "sha256:" + "1" * 64,
            }
        )
    return {
        "record_type": "a0_file_registration_manifest",
        "schema_version": "kmfa.a0_file_registration.v1",
        "files": files,
    }


def sample_candidates(file_count: int = 2) -> list[dict]:
    return [
        {
            "candidate_id": f"A0-CAND-{index:03d}",
            "a0_file_id": f"A0-FILE-{index:03d}",
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
        self.assertEqual(manifest["field_summary"]["private_value_hash_recorded_count"], 0)
        self.assertEqual(manifest["field_summary"]["private_value_pending_count"], 10)
        self.assertTrue(all(item["quality_state"]["machine_candidate_quality_grade"] == "Q3" for item in fixture_records))
        self.assertTrue(all(item["quality_state"]["q4_human_confirmed"] is False for item in fixture_records))
        self.assertTrue(all(item["quality_state"]["q5_calculation_baseline_allowed"] is False for item in fixture_records))

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
                        "candidate_id": "A0-CAND-001",
                        "field_key": "contract_amount",
                        "source_file_ref": "A0-FILE-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B2",
                        "raw_value": "100.00",
                        "unit": "yuan",
                    },
                    {
                        "candidate_id": "A0-CAND-001",
                        "field_key": "total_expense",
                        "source_file_ref": "A0-FILE-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B3",
                        "raw_value": "60.00",
                        "unit": "yuan",
                    },
                    {
                        "candidate_id": "A0-CAND-001",
                        "field_key": "gross_profit",
                        "source_file_ref": "A0-FILE-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B4",
                        "raw_value": "40.00",
                        "unit": "yuan",
                    },
                    {
                        "candidate_id": "A0-CAND-001",
                        "field_key": "gross_margin",
                        "source_file_ref": "A0-FILE-001",
                        "page_ref": "",
                        "sheet_ref": "项目成本",
                        "cell_ref": "B5",
                        "raw_value": "40%",
                        "unit": "",
                    },
                    {
                        "candidate_id": "A0-CAND-001",
                        "field_key": "cost_category",
                        "source_file_ref": "A0-FILE-001",
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
                generated_at="2026-06-30T01:00:00+10:00",
            )

        validate_a0_golden_fixture(manifest, fixture_records, require_private_values=True)
        self.assertEqual(manifest["field_summary"]["private_value_hash_recorded_count"], 5)
        self.assertEqual(manifest["field_summary"]["private_value_pending_count"], 0)
        self.assertTrue(all(item["value_binding"]["raw_value_hash"].startswith("sha256:") for item in fixture_records))
        self.assertTrue(all(item["value_binding"]["normalized_value_hash"].startswith("sha256:") for item in fixture_records))
        serialized = json.dumps({"manifest": manifest, "fixture_records": fixture_records}, ensure_ascii=False)
        self.assertNotIn('"raw_value":', serialized)
        self.assertNotIn('"normalized_value":', serialized)
        self.assertNotIn("100.00", serialized)
        self.assertNotIn("材料", serialized)

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
