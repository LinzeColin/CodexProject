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
    candidate_order = 1 if candidate_id.endswith("001") else 2
    field_order = FIELD_KEYS.index(field_key) + 1
    fixture_id = f"A0-FIX-PUB-V2-{candidate_order:03d}-{field_order:02d}"
    return {
        "record_type": "a0_golden_fixture_candidate_public_projection",
        "schema_version": "kmfa.a0_golden_fixture_candidate.public_projection.v2",
        "candidate_id": candidate_id,
        "a0_file_id": file_id,
        "fixture_candidate_id": fixture_id,
        "field_key": field_key,
        "field_label": field_key,
        "field_required_for_a0": True,
        "source_binding": {
            "source_package_ref": "A0-SOURCE-PACKAGE-PUB-V2",
            "source_file_ref": "A0-SOURCE-FILE-PUB-V2-001" if locked_ready else "A0-SOURCE-FILE-PUB-V2-002",
            "source_file_format": "pdf" if locked_ready else "xlsx",
            "source_anchor_publication_status": "private_only_not_committed",
            "private_binding_required": True,
            "private_binding_receipt_status": "required_not_verified",
        },
        "value_binding": {
            "normalized_value_kind": "money_cents",
            "private_binding_required": True,
            "private_binding_receipt_status": "required_not_verified",
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
        records.append(fixture_record("A0-CAND-PUB-V2-001", "A0-FILE-PUB-V2-001", field_key, locked_ready=True))
    for field_key in FIELD_KEYS:
        records.append(fixture_record("A0-CAND-PUB-V2-002", "A0-FILE-PUB-V2-002", field_key, locked_ready=False))
    return records


def sample_decision() -> dict:
    return {
        "record_type": "s05_p2_excel_owner_resolution_decision",
        "schema_version": "kmfa.s05_p2_excel_owner_resolution_decision.v1",
        "project_id": "KMFA",
        "stage_id": "S05",
        "phase_id": "S05-P2",
        "candidate_id": "A0-CAND-PUB-V2-002",
        "file_id": "A0-FILE-PUB-V2-002",
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


def write_private_receipt(path: Path, records: list[dict]) -> None:
    bindings = [
        {
            "fixture_candidate_id": item["fixture_candidate_id"],
            "candidate_id": item["candidate_id"],
            "a0_file_id": item["a0_file_id"],
            "source_file_ref": item["source_binding"]["source_file_ref"],
            "field_key": item["field_key"],
            "page_ref": "1",
            "sheet_ref": None,
            "cell_ref": item["field_key"],
            "raw_value_sha256": "a" * 64,
            "normalized_value_sha256": "b" * 64,
            "normalized_value_kind": "money_cents",
        }
        for item in records
    ]
    path.write_text(
        json.dumps(
            {
                "record_type": "a0_fixture_private_binding_receipt",
                "schema_version": "kmfa.private.a0_fixture_binding_receipt.v2",
                "classification": "private_sensitive_do_not_commit",
                "generated_at": "2026-06-30T11:59:00+10:00",
                "binding_count": len(bindings),
                "bindings": bindings,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


class S05P3AuthorityBaselineLockTests(unittest.TestCase):
    def test_builds_public_safe_q5_lock_and_excludes_downgraded_excel_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture_records = sample_fixture_records()
            receipt_path = Path(tmp) / "fixture_receipt.json"
            write_private_receipt(receipt_path, fixture_records)
            manifest, records = build_authority_baseline_lock(
                fixture_records=fixture_records,
                owner_decision=sample_decision(),
                private_fixture_receipt_path=receipt_path,
                locked_at="2026-06-30T12:00:00+10:00",
                locked_by_role="authorized_delegate",
                locked_by_ref="unit_test_s05p3_public_safe_lock",
            )

        validate_authority_baseline_lock(manifest, records)
        self.assertEqual(manifest["lock_summary"]["total_fixture_fields"], 10)
        self.assertEqual(manifest["lock_summary"]["q5_locked_field_count"], 5)
        self.assertEqual(manifest["lock_summary"]["excluded_field_count"], 5)
        self.assertEqual(manifest["lock_summary"]["formal_report_allowed"], False)
        self.assertEqual(
            {item["lock_status"] for item in records},
            {"q5_locked_private_receipt_verified", "excluded_cross_source_support_only"},
        )
        locked = [item for item in records if item["lock_status"] == "q5_locked_private_receipt_verified"]
        self.assertTrue(all(item["quality_state"]["q4_human_confirmed"] is True for item in locked))
        self.assertTrue(all(item["quality_state"]["q5_calculation_baseline_allowed"] is True for item in locked))
        serialized = json.dumps({"manifest": manifest, "records": records}, ensure_ascii=False)
        self.assertNotIn('"raw_value":', serialized)
        self.assertNotIn('"normalized_value":', serialized)
        self.assertNotIn("raw_value_hash", serialized)
        self.assertNotIn("normalized_value_hash", serialized)
        self.assertNotIn("source_package_hash", serialized)

    def test_rejects_q5_lock_without_hash_and_source_anchor(self) -> None:
        manifest, records = build_authority_baseline_lock(
            fixture_records=sample_fixture_records(),
            owner_decision=sample_decision(),
            locked_at="2026-06-30T12:00:00+10:00",
            locked_by_role="authorized_delegate",
            locked_by_ref="unit_test_s05p3_public_safe_lock",
        )
        pending = next(item for item in records if item["lock_status"] == "private_binding_revalidation_required")
        pending["lock_status"] = "q5_locked_private_receipt_verified"
        pending["quality_state"]["q5_calculation_baseline_allowed"] = True

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
            self.assertEqual(manifest["lock_summary"]["q5_locked_field_count"], 0)
            self.assertEqual(manifest["lock_summary"]["private_binding_revalidation_required_count"], 5)


if __name__ == "__main__":
    unittest.main()
