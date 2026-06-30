import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.a0_authority_baseline_lock import (
    build_authority_baseline_lock,
    validate_authority_baseline_lock,
)


FIELD_KEYS = [
    "contract_amount",
    "total_expense",
    "gross_profit",
    "gross_margin",
    "cost_category",
]


def fixture_record(candidate_id: str, file_id: str, field_key: str, *, locked_ready: bool) -> dict:
    fixture_id = f"A0-FIX-{candidate_id[-4:]}-{field_key}"
    return {
        "record_type": "a0_golden_fixture_candidate",
        "schema_version": "kmfa.a0_golden_fixture_candidate.v1",
        "candidate_id": candidate_id,
        "a0_file_id": file_id,
        "fixture_candidate_id": fixture_id,
        "field_key": field_key,
        "field_label": field_key,
        "field_required_for_a0": True,
        "source_binding": {
            "source_file_ref": file_id,
            "source_file_format": "pdf" if locked_ready else "xlsx",
            "source_anchor_status": "recorded_from_private_input" if locked_ready else "pending_private_source_unavailable",
            "source_package_hash": "sha256:" + "1" * 64,
            "source_public_inventory_path_hash": "sha256:" + "2" * 64,
            "page_ref": "pdf_text_all_pages" if locked_ready else None,
            "sheet_ref": None,
            "cell_ref": field_key if locked_ready else None,
        },
        "value_binding": {
            "raw_value_private_ref": f"private://KMFA/S05-P2/{fixture_id}/raw",
            "normalized_value_private_ref": f"private://KMFA/S05-P2/{fixture_id}/normalized",
            "raw_value_status": "hash_recorded_from_private_input" if locked_ready else "pending_private_source_unavailable",
            "normalized_value_status": "hash_recorded_from_private_input" if locked_ready else "pending_private_source_unavailable",
            "raw_value_hash": "sha256:" + "a" * 64 if locked_ready else None,
            "normalized_value_hash": "sha256:" + "b" * 64 if locked_ready else None,
            "normalized_value_kind": "money_cents",
            "raw_value_public_committed": False,
            "normalized_value_public_committed": False,
        },
        "quality_state": {
            "machine_candidate_quality_grade": "Q3",
            "q4_human_confirmed": False,
            "q4_human_confirmation_status": "pending_human_confirmation",
            "q5_calculation_baseline_allowed": False,
        },
        "public_repo_safety": {
            "raw_file_committed": False,
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
        },
    }


def sample_fixture_records() -> list[dict]:
    records = []
    for field_key in FIELD_KEYS:
        records.append(fixture_record("A0-CAND-PDF001", "A0-FILE-PDF001", field_key, locked_ready=True))
    for field_key in FIELD_KEYS:
        records.append(fixture_record("A0-CAND-XLS001", "A0-FILE-XLS001", field_key, locked_ready=False))
    return records


def sample_decision() -> dict:
    return {
        "record_type": "s05_p2_excel_owner_resolution_decision",
        "schema_version": "kmfa.s05_p2_excel_owner_resolution_decision.v1",
        "project_id": "KMFA",
        "stage_id": "S05",
        "phase_id": "S05-P2",
        "candidate_id": "A0-CAND-XLS001",
        "file_id": "A0-FILE-XLS001",
        "decision_code": "downgrade_to_cross_source_support",
        "actor_role": "authorized_delegate",
        "actor_ref": "unit_test_authorized_delegate",
        "decision_time": "2026-06-30T11:10:00+10:00",
        "field_keys": FIELD_KEYS,
        "candidate_role": "cross_source_support_only",
        "q5_exclusion_confirmed": True,
        "business_plaintext_committed": False,
        "raw_source_committed": False,
        "private_csv_committed": False,
        "q4_confirmation_claimed": False,
        "q5_baseline_claimed": False,
        "source_layer_write_allowed": False,
    }


class S05P3AuthorityBaselineLockTests(unittest.TestCase):
    def test_builds_public_safe_q5_lock_and_excludes_downgraded_excel_candidate(self) -> None:
        manifest, records = build_authority_baseline_lock(
            fixture_records=sample_fixture_records(),
            owner_decision=sample_decision(),
            locked_at="2026-06-30T12:00:00+10:00",
            locked_by_role="authorized_delegate",
            locked_by_ref="unit_test_s05p3_public_safe_lock",
        )

        validate_authority_baseline_lock(manifest, records)
        self.assertEqual(manifest["lock_summary"]["total_fixture_fields"], 10)
        self.assertEqual(manifest["lock_summary"]["q5_locked_field_count"], 5)
        self.assertEqual(manifest["lock_summary"]["excluded_field_count"], 5)
        self.assertEqual(manifest["lock_summary"]["formal_report_allowed"], False)
        self.assertEqual(manifest["lock_summary"]["excluded_candidate_ids"], ["A0-CAND-XLS001"])
        self.assertTrue(manifest["baseline_content_hash"].startswith("sha256:"))
        self.assertEqual(
            {item["lock_status"] for item in records},
            {"q5_locked_public_safe_hash_baseline", "excluded_cross_source_support_only"},
        )
        locked = [item for item in records if item["lock_status"] == "q5_locked_public_safe_hash_baseline"]
        self.assertTrue(all(item["quality_state"]["q4_human_confirmed"] is True for item in locked))
        self.assertTrue(all(item["quality_state"]["q5_calculation_baseline_allowed"] is True for item in locked))
        serialized = json.dumps({"manifest": manifest, "records": records}, ensure_ascii=False)
        self.assertNotIn('"raw_value":', serialized)
        self.assertNotIn('"normalized_value":', serialized)

    def test_rejects_q5_lock_without_hash_and_source_anchor(self) -> None:
        manifest, records = build_authority_baseline_lock(
            fixture_records=sample_fixture_records(),
            owner_decision=sample_decision(),
            locked_at="2026-06-30T12:00:00+10:00",
            locked_by_role="authorized_delegate",
            locked_by_ref="unit_test_s05p3_public_safe_lock",
        )
        excluded = next(item for item in records if item["lock_status"] == "excluded_cross_source_support_only")
        excluded["lock_status"] = "q5_locked_public_safe_hash_baseline"
        excluded["quality_state"]["q5_calculation_baseline_allowed"] = True

        with self.assertRaises(ValueError):
            validate_authority_baseline_lock(manifest, records)

    def test_rejects_public_plaintext_keys(self) -> None:
        manifest, records = build_authority_baseline_lock(
            fixture_records=sample_fixture_records(),
            owner_decision=sample_decision(),
            locked_at="2026-06-30T12:00:00+10:00",
            locked_by_role="authorized_delegate",
            locked_by_ref="unit_test_s05p3_public_safe_lock",
        )
        records[0]["raw_value"] = "must not be public"

        with self.assertRaises(ValueError):
            validate_authority_baseline_lock(manifest, records)

    def test_writes_machine_artifacts_without_business_plaintext(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            records_path = root / "records.jsonl"
            manifest, records = build_authority_baseline_lock(
                fixture_records=sample_fixture_records(),
                owner_decision=sample_decision(),
                locked_at="2026-06-30T12:00:00+10:00",
                locked_by_role="authorized_delegate",
                locked_by_ref="unit_test_s05p3_public_safe_lock",
                output_manifest=manifest_path,
                output_records=records_path,
            )

            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), manifest)
            self.assertEqual(len(records_path.read_text(encoding="utf-8").splitlines()), len(records))


if __name__ == "__main__":
    unittest.main()
