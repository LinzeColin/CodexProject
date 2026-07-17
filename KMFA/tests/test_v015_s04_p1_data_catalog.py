from __future__ import annotations

import copy
import hashlib
import unittest

from KMFA.tools import v015_s04_p1_data_catalog as catalog


class V015S04P1DataCatalogTests(unittest.TestCase):
    @staticmethod
    def registration(**overrides):
        value = {
            "source_id": "SRC-synthetic-ledger-5be21c67",
            "file_id": "FILE-synthetic-ledger-5be21c67",
            "import_run_id": "IMP-20260714-120000-synthetic-ledger-5be21c67",
            "file_hash": "sha256:" + hashlib.sha256(b"synthetic-ledger").hexdigest(),
            "period": "2026-06",
            "parser_version": "1.0.0",
        }
        value.update(overrides)
        return value

    def test_catalog_has_exact_taskpack_coverage_and_hierarchy(self) -> None:
        records = catalog.build_catalog_records()
        result = catalog.validate_catalog_records(records)
        self.assertEqual(result["catalog_record_count"], 21)
        self.assertEqual(result["source_system_count"], 7)
        self.assertEqual(result["hierarchy_level_count"], 9)
        self.assertEqual(
            {row["source_system"]["name"] for row in records},
            {"红圈", "金蝶", "WPS", "银行", "税务/数电票", "合同资料", "政策证据"},
        )

    def test_catalog_is_public_safe_and_blocks_formal_report_while_unbound(self) -> None:
        records = catalog.build_catalog_records()
        result = catalog.validate_catalog_records(records)
        self.assertFalse(result["formal_report_allowed"])
        self.assertEqual(result["formal_report_stop_reason"], "CORE_CATALOG_BINDINGS_INCOMPLETE")
        self.assertTrue(all(row["public_safe_template"] for row in records))
        self.assertTrue(all(not row["contains_private_digest"] for row in records))

    def test_catalog_rejects_missing_hierarchy_and_duplicate_identity(self) -> None:
        records = catalog.build_catalog_records()
        missing = copy.deepcopy(records)
        del missing[0]["owner_role"]
        with self.assertRaises(catalog.DataCatalogError):
            catalog.validate_catalog_records(missing)
        duplicate = copy.deepcopy(records)
        duplicate[1]["source_id"] = duplicate[0]["source_id"]
        with self.assertRaises(catalog.DataCatalogError):
            catalog.validate_catalog_records(duplicate)

    def test_status_vocabulary_matches_taskpack_exactly(self) -> None:
        self.assertEqual(
            catalog.SOURCE_STATUS_LABELS,
            {
                "READY": "已就绪",
                "PARTIAL": "部分可用",
                "FAILED_OR_NOT_APPLICABLE": "失败/不适用",
                "OUTDATED": "已过期",
                "MANUAL_REVIEW": "需要确认",
            },
        )

    def test_status_event_records_reason_operator_time_and_reports(self) -> None:
        event = catalog.build_status_event(
            source_id=self.registration()["source_id"],
            previous_status="PARTIAL",
            new_status="MANUAL_REVIEW",
            reason="synthetic missing mapping",
            operator_role="ROLE::DATA_REVIEWER",
            authority="CONTROL_REVIEWER",
            event_time="2026-07-14T12:00:00+10:00",
            affected_report_refs=["REPORT::MANAGEMENT"],
            backend_fact_ref="FACT::SYNTHETIC_IMPORT",
        )
        self.assertEqual(event["new_status_label"], "需要确认")
        self.assertEqual(event["storage_mode"], "APPEND_ONLY_METADATA")
        self.assertFalse(event["raw_fact_mutation_allowed"])
        self.assertFalse(event["frontend_direct_transition_allowed"])

    def test_frontend_cannot_directly_set_status(self) -> None:
        with self.assertRaises(catalog.DataCatalogError):
            catalog.build_status_event(
                source_id=self.registration()["source_id"],
                previous_status="PARTIAL",
                new_status="READY",
                reason="frontend direct action",
                operator_role="ROLE::FRONTEND_USER",
                authority="FRONTEND",
                event_time="2026-07-14T12:00:00+10:00",
                affected_report_refs=["REPORT::MANAGEMENT"],
                backend_fact_ref="FACT::SYNTHETIC_IMPORT",
                quality_fact_ref="QUALITY::SYNTHETIC_PASS",
            )

    def test_ready_requires_backend_authority_and_quality_fact(self) -> None:
        kwargs = {
            "source_id": self.registration()["source_id"],
            "previous_status": "PARTIAL",
            "new_status": "READY",
            "reason": "synthetic ready",
            "operator_role": "ROLE::QUALITY_ENGINE",
            "authority": "QUALITY_ENGINE",
            "event_time": "2026-07-14T12:00:00+10:00",
            "affected_report_refs": ["REPORT::MANAGEMENT"],
            "backend_fact_ref": "FACT::SYNTHETIC_IMPORT",
        }
        with self.assertRaises(catalog.DataCatalogError):
            catalog.build_status_event(**kwargs)
        event = catalog.build_status_event(**kwargs, quality_fact_ref="QUALITY::SYNTHETIC_PASS")
        self.assertEqual(event["new_status"], "READY")

    def test_status_event_rejects_missing_reports_and_timezone(self) -> None:
        base = {
            "source_id": self.registration()["source_id"],
            "previous_status": "PARTIAL",
            "new_status": "MANUAL_REVIEW",
            "reason": "synthetic review",
            "operator_role": "ROLE::DATA_REVIEWER",
            "authority": "CONTROL_REVIEWER",
            "event_time": "2026-07-14T12:00:00+10:00",
            "affected_report_refs": ["REPORT::MANAGEMENT"],
            "backend_fact_ref": "FACT::SYNTHETIC_IMPORT",
        }
        with self.assertRaises(catalog.DataCatalogError):
            catalog.build_status_event(**{**base, "affected_report_refs": []})
        with self.assertRaises(catalog.DataCatalogError):
            catalog.build_status_event(**{**base, "event_time": "2026-07-14T12:00:00"})

    def test_import_registration_requires_exact_six_fields(self) -> None:
        self.assertEqual(len(catalog.REQUIRED_IMPORT_FIELDS), 6)
        result = catalog.register_import(self.registration(), [])
        self.assertEqual(result["outcome"], "REGISTERED")
        self.assertEqual(set(result["record"]), set(catalog.REQUIRED_IMPORT_FIELDS))

    def test_exact_replay_is_idempotently_reused(self) -> None:
        candidate = self.registration()
        first = catalog.register_import(candidate, [])
        replay = catalog.register_import(candidate, [first["record"]])
        self.assertEqual(replay["outcome"], "REUSED")
        self.assertFalse(replay["new_record_created"])
        self.assertTrue(replay["duplicate_file_detected"])

    def test_same_file_new_parser_version_is_detected_and_coexists(self) -> None:
        first = catalog.register_import(self.registration(), [])
        candidate = self.registration(
            import_run_id="IMP-20260714-120100-synthetic-ledger-5be21c67",
            parser_version="1.1.0",
        )
        result = catalog.register_import(candidate, [first["record"]])
        self.assertEqual(result["outcome"], "REGISTERED_VERSION")
        self.assertTrue(result["duplicate_file_detected"])
        self.assertTrue(result["new_record_created"])

    def test_different_file_version_coexists(self) -> None:
        first = catalog.register_import(self.registration(), [])
        candidate = self.registration(
            file_id="FILE-synthetic-ledger-62900d1a",
            import_run_id="IMP-20260714-120200-synthetic-ledger-62900d1a",
            file_hash="sha256:" + hashlib.sha256(b"synthetic-ledger-v2").hexdigest(),
            parser_version="1.1.0",
        )
        result = catalog.register_import(candidate, [first["record"]])
        self.assertEqual(result["outcome"], "REGISTERED_VERSION")
        self.assertFalse(result["duplicate_file_detected"])
        self.assertEqual(result["coexisting_prior_version_count"], 1)

    def test_missing_source_or_hash_goes_to_quarantine(self) -> None:
        source = catalog.register_import(self.registration(source_id=""), [])
        digest = catalog.register_import(self.registration(file_hash=""), [])
        self.assertEqual(source["outcome"], "QUARANTINED")
        self.assertIn("MISSING_SOURCE_ID", source["reason_codes"])
        self.assertEqual(digest["outcome"], "QUARANTINED")
        self.assertIn("MISSING_FILE_HASH", digest["reason_codes"])
        self.assertIsNone(source["record"])

    def test_malformed_identity_period_or_parser_version_fails_closed(self) -> None:
        for override in (
            {"source_id": "source-1"},
            {"file_id": "file-1"},
            {"import_run_id": "run-1"},
            {"file_hash": "sha256:1234"},
            {"period": "2026-13"},
            {"parser_version": "v1"},
        ):
            with self.assertRaises(catalog.DataCatalogError, msg=override):
                catalog.register_import(self.registration(**override), [])

    def test_public_verification_summary_passes_without_exposing_digest(self) -> None:
        summary = catalog.public_verification_summary()
        bool_keys = [key for key, value in summary.items() if isinstance(value, bool)]
        self.assertTrue(all(summary[key] for key in bool_keys if key not in {"private_file_hash_exposed", "raw_fact_mutation_allowed"}))
        self.assertFalse(summary["private_file_hash_exposed"])
        self.assertFalse(summary["raw_fact_mutation_allowed"])
        self.assertNotIn("sha256:", catalog.canonical_json(summary))


if __name__ == "__main__":
    unittest.main()
