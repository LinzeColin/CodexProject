from __future__ import annotations

from copy import deepcopy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from KMFA.tools import build_v015_s03_p3_public_repository_safety as builder
from KMFA.tools import check_v015_s03_p3_public_repository_safety as checker
from KMFA.tools import v015_s03_p3_public_repository_safety as safety


FINAL_EVENT_TIME = "2026-07-14T10:00:00+10:00"
FINAL_CHANGED_REFS = ("KMFA/example_public_safe.json",)


def _final_shared() -> dict[str, object]:
    receipt_count = len(builder.EXPECTED_VALIDATION_RECEIPTS)
    return {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S03",
        "phase_id": builder.RUN_PHASE_ID,
        "roadmap_phase_id": "S03-P3",
        "task_id": builder.TASK_ID,
        "acceptance_id": builder.ACCEPTANCE_ID,
        "run_mode": "IMPLEMENT",
        "work_kind": "PUBLIC_REPOSITORY_SAFETY",
        "fact_level": "EXTRACTED",
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "final_validation_status": "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3,
        "stage_task_accepted_count": 9,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3,
        "decision": "CONTINUE_TO_S03_STAGE_REVIEW_ONLY",
        "s03_p3_started": True,
        "s03_p3_acceptance_status": "PASSED",
        "s03_stage_review_entry_allowed": True,
        "s03_stage_review_started": False,
        "s03_stage_review_performed": False,
        "s04_p1_entry_allowed": False,
        "product_implementation_allowed": False,
        "reachable_history_clean": False,
        "history_rewrite_performed": False,
        "final_github_upload_allowed": False,
        "github_upload_performed_by_current_run": False,
        "app_reinstall_performed_by_current_run": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "raw_business_content_read": False,
        "raw_business_interpretation_performed": False,
        "business_execution_performed": False,
        "raw_root_access_count_by_phase": 0,
        "protected_submission_class_count": 5,
        "committable_metadata_class_count": 6,
        "forbidden_public_detail_class_count": 4,
        "owner_plaintext_exception_effective": False,
        "current_submission_gate_pass": True,
        "public_reconstruction_success_count": 0,
        "validation_run_id": "1" * 32,
        "validation_head": "2" * 40,
        "validation_subject_sha256": "sha256:" + "3" * 64,
        "validation_receipt_count": receipt_count,
        "validation_pass_count": receipt_count,
        "validation_failed_count": 0,
        "evidence_ref": checker.FINAL_EVIDENCE_REF,
    }


def _final_governance_fixture() -> tuple[
    dict[str, object], dict[str, object], dict[str, object], dict[str, object]
]:
    shared = _final_shared()
    event = {
        **shared,
        "event_id": checker.FINAL_EVENT_ID,
        "event_type": "final_validation",
        "status": checker.FINAL_RECORD_STATUS,
        "event_time": FINAL_EVENT_TIME,
    }
    development = {
        **shared,
        "event_id": checker.FINAL_DEVELOPMENT_EVENT_ID,
        "iteration_id": checker.FINAL_ITERATION_ID,
        "event_type": "final_validation",
        "status": checker.FINAL_RECORD_STATUS,
        "summary": checker.FINAL_DEVELOPMENT_SUMMARY,
        "event_time": FINAL_EVENT_TIME,
        "result_commit": checker.FINAL_RESULT_COMMIT,
        "files_changed": list(FINAL_CHANGED_REFS),
    }
    status = {
        **shared,
        "schema_version": "kmfa.stage_status.v1",
        "status_record_id": checker.FINAL_STATUS_RECORD_ID,
        "record_type": "phase_status",
        "status": checker.FINAL_RECORD_STATUS,
        "event_time": FINAL_EVENT_TIME,
        "version": checker.FINAL_VERSION,
        "updated_at": FINAL_EVENT_TIME,
    }
    assurance = {
        "project_id": "KMFA",
        "as_of_event_id": checker.FINAL_DEVELOPMENT_EVENT_ID,
        "source_snapshot_hash": shared["validation_subject_sha256"],
        "source_base_commit": shared["validation_head"],
        "source_tree_hash": shared["validation_subject_sha256"],
        "snapshot_event_time": FINAL_EVENT_TIME,
        "generator_version": checker.FINAL_ASSURANCE_GENERATOR_VERSION,
        "final_commit_binding": checker.FINAL_ASSURANCE_BINDING,
        "historical_pre_v2_atime_effect_unknown": True,
        "os_atime_observation_scope": "S03_P2_RAW_ROOT_AND_DIRECT_FILES_EACH_COPY_RUN",
    }
    return event, development, status, assurance


class S03P3PublicRepositorySafetyCheckerTests(unittest.TestCase):
    def test_phase_metadata_public_detail_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "KMFA/metadata/baseline/unsafe.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps({"amount": 1}), encoding="utf-8")
            with (
                mock.patch.object(builder, "REPO_ROOT", root),
                mock.patch.object(safety, "REPO_ROOT", root),
            ):
                with self.assertRaisesRegex(builder.BuildError, "public-detail audit failed"):
                    builder._phase_metadata_rows(("KMFA/metadata/baseline/unsafe.json",))

    def test_changed_structured_gate_covers_tools_tests_and_docs(self) -> None:
        cases = {
            "KMFA/tools/fixtures/source.json": b'{"source_filename":"ledger.xlsx"}',
            "KMFA/tests/fixtures/report.json": b'{"customer_name":"Real Party"}',
            "KMFA/docs/source.csv": b"amount_yuan\n100\n",
            "KMFA/tools/fixtures/flow.yaml": b"record: {customer_name: Real Party}\n",
        }
        for ref, payload in cases.items():
            with (
                self.subTest(ref=ref),
                mock.patch.object(builder, "_public_ref_exists", return_value=True),
                mock.patch.object(builder, "_read_public_ref", return_value=payload),
                self.assertRaisesRegex(builder.BuildError, "changed structured public file"),
            ):
                builder._audit_changed_public_structured_files((ref,))

    def test_clean_gate_rejects_receipts_from_final_head(self) -> None:
        head = "a" * 40
        parent = "b" * 40
        with mock.patch.object(checker, "_git", side_effect=("", head, parent)):
            with self.assertRaisesRegex(checker.CheckError, "distinct second commit"):
                checker._validate_clean_commit({"phase_changed_refs": []}, head)

    def test_clean_gate_requires_exactly_two_phase_commits(self) -> None:
        head = "a" * 40
        parent = "b" * 40
        with mock.patch.object(checker, "_git", side_effect=("", head, parent, "1")):
            with self.assertRaisesRegex(checker.CheckError, "exactly implementation and evidence commits"):
                checker._validate_clean_commit({"phase_changed_refs": []}, parent)

    def test_private_evidence_gate_rejects_same_summary_with_swapped_full_projection(self) -> None:
        token_key = "to" + "ken"
        live_projection = {"opaque_tokens": [{token_key: "hmac-sha256:" + "1" * 64}]}
        tracked_projection = {"opaque_tokens": [{token_key: "hmac-sha256:" + "2" * 64}]}
        live = {
            "private_evidence_gitignored": True,
            "private_evidence_tracked": False,
            "receipt_count": 1,
            "public_projection": live_projection,
            "verification": {"exact_private_to_public_rebuild": True},
        }
        tracked = {
            "same_run_evidence_summary": {
                "private_evidence_gitignored": True,
                "private_evidence_tracked": False,
                "receipt_count": 1,
            },
            "public_projection": tracked_projection,
            "verification": {"exact_private_to_public_rebuild": True},
        }
        with (
            mock.patch.object(checker.safety, "private_evidence_summary", return_value=deepcopy(live)),
            mock.patch.object(checker, "_regular_single_link"),
            mock.patch.object(checker, "_read_json", return_value=tracked),
            self.assertRaisesRegex(checker.CheckError, "public projection does not bind"),
        ):
            checker._validate_private_evidence(0)

    def test_receipts_require_exact_schema_sequence_time_and_digests(self) -> None:
        run_id = "1" * 32
        head = "2" * 40
        subject = builder.validation_subject_sha256(changed_refs=[])
        rows = []
        for sequence, (validation_id, command) in enumerate(builder.EXPECTED_VALIDATION_RECEIPTS.items(), start=1):
            rows.append(
                {
                    "schema_version": builder.VALIDATION_RECEIPT_SCHEMA_VERSION,
                    "run_id": run_id,
                    "validation_id": validation_id,
                    "command": command,
                    "result": "PASS",
                    "exit_code": 0,
                    "execution_sequence": sequence,
                    "started_at": "2026-07-14T10:00:00+10:00",
                    "ended_at": "2026-07-14T10:00:01+10:00",
                    "duration_ms": 1000,
                    "phase_base_commit": builder.PHASE_BASE_COMMIT,
                    "head_before": head,
                    "head_after": head,
                    "validation_subject_sha256": subject,
                    "stdout_sha256": "sha256:" + "3" * 64,
                    "stderr_sha256": "sha256:" + "4" * 64,
                }
            )
        rows[0]["execution_sequence"] = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipts.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            os.chmod(path, 0o600)
            manifest = {
                "validation_run_id": run_id,
                "phase_changed_refs": [],
                "validation_subject_sha256": subject,
            }
            with mock.patch.object(checker, "PRIVATE_RECEIPTS_PATH", path):
                with self.assertRaisesRegex(checker.CheckError, "sequence drifted"):
                    checker._validate_receipts(manifest, clean_head=None)

    def _validate_final_fixture(
        self,
        event: dict[str, object],
        development: dict[str, object],
        status: dict[str, object],
        assurance: dict[str, object],
        *,
        assurance_counts: tuple[int | None, int | None] = (
            checker.FINAL_ASSURANCE_ACTIVE_PARAMETER_COUNT,
            checker.FINAL_ASSURANCE_ACTIVE_FORMULA_COUNT,
        ),
        assurance_header_keys: set[str] | None = None,
        assurance_evidence_refs: set[str] | None = None,
    ) -> None:
        shared = _final_shared()
        if assurance_header_keys is None:
            assurance_header_keys = set(assurance) | {"dimensions"}
        if assurance_evidence_refs is None:
            assurance_evidence_refs = set(checker.FINAL_ASSURANCE_EVIDENCE_REFS)
        with (
            mock.patch.object(checker, "_validate_phase_governance_shape"),
            mock.patch.object(checker, "_last_jsonl_row", side_effect=(event, development, status)),
            mock.patch.object(checker, "_top_level_yaml_scalars", return_value=assurance),
            mock.patch.object(checker, "_assurance_header_keys", return_value=assurance_header_keys),
            mock.patch.object(
                checker,
                "_assurance_s03p3_semantics",
                return_value=(*assurance_counts, assurance_evidence_refs),
            ),
            mock.patch.object(builder, "phase_changed_refs", return_value=FINAL_CHANGED_REFS),
        ):
            checker._validate_final_governance(
                validation_run_id=str(shared["validation_run_id"]),
                receipt_head=str(shared["validation_head"]),
                subject_digest=str(shared["validation_subject_sha256"]),
                receipt_count=int(shared["validation_receipt_count"]),
            )

    def test_final_governance_exact_schema_and_semantics_pass(self) -> None:
        self._validate_final_fixture(*_final_governance_fixture())

    def test_final_governance_rejects_semantic_mutation(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        status["decision"] = "REMAIN_IN_S03_P3"
        with self.assertRaisesRegex(checker.CheckError, "stage_status.jsonl.decision"):
            self._validate_final_fixture(event, development, status, assurance)

    def test_final_governance_rejects_missing_required_key(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        del status["record_type"]
        with self.assertRaisesRegex(checker.CheckError, "missing keys.*record_type"):
            self._validate_final_fixture(event, development, status, assurance)

    def test_final_governance_rejects_extra_key(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        event["comment"] = "not part of the final event schema"
        with self.assertRaisesRegex(checker.CheckError, "extra keys.*comment"):
            self._validate_final_fixture(event, development, status, assurance)

    def test_final_governance_rejects_sensitive_key_before_extra_key_check(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        development["private" + "_key"] = "not-even-a-real-secret"
        with self.assertRaisesRegex(checker.CheckError, "sensitive field/value.*private_key"):
            self._validate_final_fixture(event, development, status, assurance)

    def test_final_governance_rejects_local_path_value(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        development["summary"] = "/Users/example/private/source.xls"
        with self.assertRaisesRegex(checker.CheckError, "sensitive field/value.*summary"):
            self._validate_final_fixture(event, development, status, assurance)

    def test_final_governance_rejects_event_time_mismatch(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        status["event_time"] = "2026-07-14T10:00:01+10:00"
        with self.assertRaisesRegex(checker.CheckError, "event time mismatch.*stage_status"):
            self._validate_final_fixture(event, development, status, assurance)

    def test_final_governance_rejects_changed_ref_mutation(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        development["files_changed"] = []
        with self.assertRaisesRegex(checker.CheckError, "development_events.jsonl.files_changed"):
            self._validate_final_fixture(event, development, status, assurance)

    def test_final_assurance_rejects_extra_header_key(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        header_keys = set(assurance) | {"dimensions", "unexpected"}
        with self.assertRaisesRegex(checker.CheckError, "assurance header schema drift.*unexpected"):
            self._validate_final_fixture(
                event,
                development,
                status,
                assurance,
                assurance_header_keys=header_keys,
            )

    def test_final_assurance_rejects_sensitive_scalar_key(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        assurance["private" + "_key"] = "not-even-a-real-secret"
        with self.assertRaisesRegex(checker.CheckError, "sensitive field/value.*private_key"):
            self._validate_final_fixture(event, development, status, assurance)

    def test_final_assurance_rejects_active_count_mutation(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        with self.assertRaisesRegex(checker.CheckError, "active parameter count drift"):
            self._validate_final_fixture(
                event,
                development,
                status,
                assurance,
                assurance_counts=(checker.FINAL_ASSURANCE_ACTIVE_PARAMETER_COUNT - 1, 327),
            )

    def test_final_assurance_requires_s03p3_evidence_refs(self) -> None:
        event, development, status, assurance = _final_governance_fixture()
        missing = "KMFA/tools/run_v015_s03_p3_validations.py"
        evidence_refs = set(checker.FINAL_ASSURANCE_EVIDENCE_REFS) - {missing}
        with self.assertRaisesRegex(checker.CheckError, "evidence refs missing.*run_v015_s03_p3"):
            self._validate_final_fixture(
                event,
                development,
                status,
                assurance,
                assurance_evidence_refs=evidence_refs,
            )

    def test_legacy_census_requires_all_current_tree_counts_zero(self) -> None:
        census = {
            "current_tree_absolute_local_path_count": 0,
            "current_tree_absolute_local_path_file_count": 0,
            "legacy_schema_review_finding_count": 0,
            "legacy_schema_review_file_count": 0,
            "reachable_history_clean": False,
        }
        checker._validate_legacy_census_contract(census)
        for key in (
            "current_tree_absolute_local_path_count",
            "current_tree_absolute_local_path_file_count",
            "legacy_schema_review_finding_count",
            "legacy_schema_review_file_count",
        ):
            mutated = deepcopy(census)
            mutated[key] = 1
            with self.subTest(key=key), self.assertRaisesRegex(checker.CheckError, key):
                checker._validate_legacy_census_contract(mutated)

    def test_protection_contract_requires_current_submission_gate_true(self) -> None:
        protection = {
            "owner_plaintext_exception_effective": False,
            "current_submission_gate_pass": True,
            "repository_scans": {
                scope: {"pass": True, "finding_count": 0}
                for scope in ("head", "index", "worktree")
            },
        }
        checker._validate_protection_contract(protection)
        protection["current_submission_gate_pass"] = False
        with self.assertRaisesRegex(checker.CheckError, "current submission protection gate failed"):
            checker._validate_protection_contract(protection)


if __name__ == "__main__":
    unittest.main()
