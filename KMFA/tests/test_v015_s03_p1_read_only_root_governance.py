from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from KMFA.tools import build_v015_s03_p1_read_only_root_governance as builder
from KMFA.tools import check_v015_s03_p1_read_only_root_governance as checker


class TestV015S03P1ReadOnlyRootGovernance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = builder.verify_source_package()

    def test_source_package_verifies_21_members_and_exact_tasks(self) -> None:
        self.assertEqual(self.source["verified_member_count"], 21)
        self.assertEqual(
            (self.source["stage_count"], self.source["phase_count"], self.source["task_count"]),
            (24, 72, 216),
        )
        self.assertTrue(self.source["s03_p1_semantic_equal"])
        self.assertEqual(self.source["s03_p1_task_count"], 3)

    def test_minimal_read_contract_is_exact_and_default_deny(self) -> None:
        self.assertEqual(builder.EXPECTED_ALLOWED_OPERATIONS, ("list", "read", "stat", "hash"))
        self.assertEqual(builder.EXPECTED_ALLOWED_EXTENSIONS, (".xlsx", ".zip"))
        self.assertEqual(builder.EXPECTED_MUTATION_CLASSES, ("CREATE", "DELETE", "MODIFY", "RENAME"))

    def test_public_payload_rejects_path_email_and_secret(self) -> None:
        path_payload = b'root = "' + b"/" + b'Users/example/raw"'
        email_payload = b'owner = "person' + b"@" + b'example.com"'
        secret_payload = b'api_' + b'key = "12345678"'
        for payload, expected in (
            (path_payload, "public-safe token leak"),
            (email_payload, "email leak"),
            (secret_payload, "secret-like assignment"),
        ):
            errors: list[str] = []
            checker._validate_public_payload(payload, errors, label="mutation")
            self.assertTrue(any(expected in item for item in errors))

        public_token_errors: list[str] = []
        checker._validate_public_payload(
            b'raw_root_token: "PRIMARY_RAW_ROOT"',
            public_token_errors,
            label="public root token",
        )
        self.assertEqual(public_token_errors, [])

    def test_open_risk_owner_write_truth_uses_nested_guard(self) -> None:
        payload = builder._risks_markdown(
            {"receipt": {"guard": {"root_owner_write_bit": True}}}
        ).decode("utf-8")
        self.assertIn("owner write bit observed=`true`", payload)

    def test_top_level_yaml_identity_cannot_be_satisfied_by_nested_token(self) -> None:
        payload = (
            'current_phase_id: "WRONG"\n'
            'nested:\n'
            '  current_phase_id: "V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE"\n'
        )
        self.assertEqual(checker._top_level_yaml_scalar(payload, "current_phase_id"), "WRONG")

    def test_task_matrix_missing_task_fails_closed(self) -> None:
        matrix = {
            "tasks": [],
            "phase_acceptance_status": "PENDING",
            "decision": "REMAIN_IN_S03_P1",
        }
        errors: list[str] = []
        checker._validate_matrix(matrix, errors)
        self.assertTrue(any("three Tasks" in item for item in errors))

    def test_task_contract_drift_fails_closed(self) -> None:
        rows = []
        for task in builder.TASKS:
            contract = {key: task[key] for key in ("name", "action", "output", "acceptance", "evidence", "stop")}
            rows.append({
                "task_id": task["task_id"], "source_contract": contract,
                "execution_status": "EXECUTION_COMPLETE", "acceptance_status": "PASSED",
                "current_result": "TASK_ACCEPTED",
            })
        rows[0]["source_contract"]["acceptance"] = "DRIFT"
        errors: list[str] = []
        checker._validate_matrix(
            {"tasks": rows, "phase_acceptance_status": "PASSED", "decision": "CONTINUE_TO_S03_P2_ONLY"},
            errors,
        )
        self.assertTrue(any("source contract drift" in item for item in errors))

    def test_evidence_slot_omission_fails_closed(self) -> None:
        rows = builder._slot_rows()[:-1]
        errors: list[str] = []
        checker._validate_evidence_slots(rows, errors)
        self.assertTrue(any("30" in item or "slots drift" in item for item in errors))

    def test_evidence_slot_na_requires_rationale(self) -> None:
        rows = builder._slot_rows()
        target = next(row for row in rows if row["status"] == "N/A_WITH_RATIONALE")
        target["not_applicable_reason"] = ""
        errors: list[str] = []
        checker._validate_evidence_slots(rows, errors)
        self.assertTrue(any("missing rationale" in item for item in errors))

    def test_validation_command_drift_fails_closed(self) -> None:
        rows = [
            {"validation_id": key, "command": command, "result": "PASS", "exit_code": 0}
            for key, command in builder.EXPECTED_VALIDATION_RECEIPTS.items()
        ]
        rows[0]["command"] += " --drift"
        errors: list[str] = []
        checker._validate_receipts(rows, require_pass=True, errors=errors)
        self.assertTrue(any("command drift" in item for item in errors))

    def test_write_mode_never_reuses_existing_public_pass_receipts(self) -> None:
        private_root = builder.PROJECT_ROOT / ".codex_private_runtime"
        with tempfile.TemporaryDirectory(dir=private_root) as directory:
            output_root = Path(directory)
            existing = output_root / builder.VALIDATION_RESULTS_RELATIVE
            existing.parent.mkdir(parents=True)
            existing.write_text("not-json\n", encoding="utf-8")
            rows = builder._validation_rows(
                output_root,
                None,
                project_root=builder.PROJECT_ROOT,
                reuse_public_results=False,
            )
            self.assertEqual(len(rows), len(builder.EXPECTED_VALIDATION_RECEIPTS))
            self.assertTrue(all(row["result"] == "PENDING" for row in rows))

    def test_policy_mutation_or_os_immutability_overclaim_fails_closed(self) -> None:
        registry = {
            "schema_version": "kmfa.metadata.v015.s03_p1.read_only_root_registry.public_safe.v2",
            "root_id": builder.ROOT_ID,
            "path_binding": {"visibility": "PRIVATE_ONLY", "exact_path_registered": True, "public_path_value": None},
            "allowed_operations": list(builder.EXPECTED_ALLOWED_OPERATIONS),
            "forbidden_operations_performed": ["write"],
            "permission_observation": {"readable": True, "permission_known": True, "os_level_immutable_claimed": True},
            "prohibited_raw_mutation_detected": True,
            "prohibited_mutation_scope": list(builder.EXPECTED_PROHIBITED_MUTATION_SCOPE),
            "os_atime_side_effect_possible": False,
            "os_atime_side_effect_observed": "unknown",
            "absolute_zero_metadata_mutation_claimed": True,
            "os_atime_restoration_performed": True,
            "production_raw_mutation_api_present": True,
            "raw_root_mutated": False,
        }
        allowlist = {
            "authorization_model": "DEFAULT_DENY_EXACT_ROOT_AND_FILE_TYPE",
            "source_rules": [], "full_disk_scan_allowed": False,
            "arbitrary_root_cli_override_allowed": False,
        }
        guard_public = {
            "schema_version": "kmfa.v015.s03_p1.write_protection_validation.public_safe.v2",
            "guard_status": "FAIL", "event_monitor_status": "FAIL",
            "event_monitor_backend": checker.guard.DarwinKqueueVnodeMonitor.name,
            "event_monitor_production_attested": True,
            "controlled_window_seconds": checker.guard.CONTROLLED_WINDOW_SECONDS,
            "final_drain_seconds": checker.guard.FINAL_DRAIN_SECONDS,
            "prohibited_raw_mutation_detected": True,
            "prohibited_mutation_scope": list(builder.EXPECTED_PROHIBITED_MUTATION_SCOPE),
            "os_atime_side_effect_possible": False,
            "os_atime_side_effect_observed": "unknown",
            "absolute_zero_metadata_mutation_claimed": True,
            "os_atime_restoration_performed": True,
            "production_raw_mutation_api_present": True,
            "raw_mutation_detected": False,
            "os_level_immutable_claimed": True,
            "mutation_class_contract": list(builder.EXPECTED_MUTATION_CLASSES),
        }
        errors: list[str] = []
        checker._validate_policies(registry, allowlist, guard_public, errors)
        self.assertTrue(any("forbidden operation" in item for item in errors))
        self.assertTrue(any("immutable overclaim" in item for item in errors))
        self.assertTrue(any("prohibited mutation" in item for item in errors))
        self.assertTrue(any("atime possibility" in item for item in errors))
        self.assertTrue(any("absolute-zero" in item for item in errors))
        self.assertTrue(any("atime restoration" in item for item in errors))
        self.assertTrue(any("production raw mutation API" in item for item in errors))
        self.assertTrue(any("ambiguous raw mutation field forbidden" in item for item in errors))

    def test_dynamic_atime_projection_and_final_ledgers_are_not_pre_run_subjects(self) -> None:
        for key in ("public_registry", "write_guard", "open_risks"):
            self.assertIn(key, builder.VALIDATION_MUTABLE_ARTIFACT_KEYS)
            self.assertNotIn(builder.ARTIFACT_REFS[key], builder.VALIDATION_SUBJECT_REFS)
        self.assertTrue(builder.POST_VALIDATION_GOVERNANCE_REFS.isdisjoint(builder.VALIDATION_SUBJECT_REFS))

    def test_validation_subject_keeps_all_executable_validation_code_bound(self) -> None:
        for ref in (
            "KMFA/tools/v015_s03_p1_read_only_root_guard.py",
            "KMFA/tools/build_v015_s03_p1_read_only_root_governance.py",
            "KMFA/tools/check_v015_s03_p1_read_only_root_governance.py",
            "KMFA/tools/run_v015_s03_p1_validations.py",
            "KMFA/tests/test_v015_s03_p1_read_only_root_guard.py",
            "KMFA/tests/test_v015_s03_p1_read_only_root_governance.py",
            "KMFA/tests/test_v015_s03_p1_validation_runner.py",
            "KMFA/tools/check_no_float_money.py",
            "KMFA/tools/no_omission_check.py",
            "scripts/lean_governance.py",
            "scripts/validate_governance_sync.py",
            "scripts/validate_project_governance.py",
            "scripts/validate_semantic_extractors.py",
            "KMFA/tools/v015_roadmap_governance_sync.py",
            "KMFA/tests/test_v015_roadmap_governance_sync.py",
            "KMFA/docs/governance/MODEL_SPEC.md",
        ):
            self.assertIn(ref, builder.VALIDATION_SUBJECT_REFS)

    def test_type_check_rejects_symlink_before_content_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.json"
            outside.write_text('{"sensitive": true}', encoding="utf-8")
            link = root / "artifact.json"
            link.symlink_to(outside)
            errors: list[str] = []
            self.assertFalse(checker._regular_single_link(link, errors, label="artifact"))
            self.assertTrue(any("type/link unsafe" in item for item in errors))

    def test_safe_reader_rejects_final_component_swap_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "subject.py"
            replacement = root / "replacement.py"
            target.write_bytes(b"expected")
            replacement.write_bytes(b"outside-sensitive")
            real_open = os.open

            def swap_then_open(path: os.PathLike[str] | str, flags: int, *args: object, **kwargs: object) -> int:
                target.unlink()
                replacement.rename(target)
                return real_open(path, flags, *args, **kwargs)

            with mock.patch.object(builder.os, "open", side_effect=swap_then_open), mock.patch.object(
                builder.os,
                "read",
                side_effect=AssertionError("content read must not occur after identity swap"),
            ):
                with self.assertRaisesRegex(builder.BuildError, "identity changed before read"):
                    builder._read_regular_bytes_no_follow(target, label="subject")

    def test_safe_reader_rejects_symlink_and_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_bytes(b"{}")
            symlink = root / "symlink.json"
            symlink.symlink_to(source)
            hardlink = root / "hardlink.json"
            os.link(source, hardlink)
            with self.assertRaisesRegex(builder.BuildError, "type/link unsafe"):
                builder._read_regular_bytes_no_follow(symlink, label="subject")
            with self.assertRaisesRegex(builder.BuildError, "type/link unsafe"):
                builder._read_regular_bytes_no_follow(hardlink, label="subject")

    def test_pending_authority_rejects_prewritten_final_and_ambiguous_raw_field(self) -> None:
        prewritten_final = {
            "event_id": "PREWRITTEN-FINAL",
            "status_record_id": "PREWRITTEN-FINAL",
            "status": "completed",
            "phase_execution_status": "EXECUTION_COMPLETE",
            "phase_acceptance_status": "PASSED",
            "final_validation_status": "PASS",
            "decision": "CONTINUE_TO_S03_P2_ONLY",
            "s03_p2_entry_allowed": True,
            "s03_p2_started": False,
            "raw_inbox_mutated": False,
            "event_time": "2026-07-13T16:28:26+10:00",
        }
        errors: list[str] = []
        with mock.patch.object(checker, "_regular_single_link", return_value=True), mock.patch.object(
            checker,
            "_read_jsonl",
            return_value=[prewritten_final],
        ):
            checker._validate_pending_governance_authority(errors)
        self.assertTrue(any("pending governance authority identity drift" in item for item in errors))
        self.assertTrue(any("phase_acceptance_status" in item for item in errors))
        self.assertTrue(any("ambiguous field forbidden" in item for item in errors))

    def test_final_authority_supersedes_only_truthful_pending_rows(self) -> None:
        expected = {
            checker.FINAL_EVENT_ID: [checker.PENDING_EVENT_ID],
            checker.FINAL_DEVELOPMENT_EVENT_ID: [checker.PENDING_DEVELOPMENT_EVENT_ID],
            checker.FINAL_STAGE_STATUS_RECORD_ID: [checker.PENDING_STAGE_STATUS_RECORD_ID],
        }
        self.assertEqual(
            {identity: supersedes for _, _, identity, _, supersedes in checker.FINAL_LEDGER_SOURCES},
            expected,
        )

    def test_pre_receipt_final_governance_requires_truthful_final_shape(self) -> None:
        rows = {}
        for path, identity_key, identity, supersedes_key, supersedes in checker.FINAL_LEDGER_SOURCES:
            rows[path] = {
                identity_key: identity,
                supersedes_key: supersedes,
                "correction_reason": checker.FINAL_CORRECTION_REASON,
                "status": checker.FINAL_CORRECTION_STATUS,
                "phase_execution_status": "EXECUTION_COMPLETE",
                "phase_acceptance_status": "PASSED",
                "final_validation_status": "PASS",
                "decision": "CONTINUE_TO_S03_P2_ONLY",
                "s03_p2_entry_allowed": True,
                "s03_p2_started": False,
                "prohibited_raw_mutation_detected": False,
                "prohibited_mutation_scope": list(builder.EXPECTED_PROHIBITED_MUTATION_SCOPE),
                "os_atime_side_effect_possible": True,
                "os_atime_side_effect_observed": False,
                "historical_pre_v2_atime_effect_unknown": True,
                "os_atime_observation_scope": "FINAL_V2_REPLAY_ONLY",
                "absolute_zero_metadata_mutation_claimed": False,
                "os_atime_restoration_performed": False,
                "production_raw_mutation_api_present": False,
                "validation_run_id": "a" * 32,
                "validation_receipt_count": len(builder.EXPECTED_VALIDATION_RECEIPTS),
                "open_risk_count": 4,
                "event_time": "2026-07-13T18:04:00+10:00",
            }

        def read_rows(path):
            return [rows[path]]

        errors: list[str] = []
        with mock.patch.object(checker, "_regular_single_link", return_value=True), mock.patch.object(
            checker,
            "_read_jsonl",
            side_effect=read_rows,
        ):
            checker._validate_pre_receipt_final_governance_authority(errors)
        self.assertEqual(errors, [])
        rows[checker.FINAL_LEDGER_SOURCES[0][0]]["validation_run_id"] = "invalid"
        errors = []
        with mock.patch.object(checker, "_regular_single_link", return_value=True), mock.patch.object(
            checker,
            "_read_jsonl",
            side_effect=read_rows,
        ):
            checker._validate_pre_receipt_final_governance_authority(errors)
        self.assertTrue(any("prior run_id invalid" in item for item in errors))

    def test_immutable_formula_definition_has_no_acceptance_mutable_status(self) -> None:
        text = checker._read_text_no_follow(
            checker.PROJECT_ROOT / "docs/governance/formula_registry.yaml",
            label="formula registry",
        )
        token = 'formula_id: "FORM-KMFA-V015-S03-P1-READ-ONLY-ROOT-GUARD-001"'
        start = text.index(token)
        end = text.find("\n  - formula_id:", start + len(token))
        block = text[start: end if end >= 0 else None]
        self.assertIn('definition_status: "ACTIVE"', block)
        self.assertIn('evaluation_mode: "RECEIPT_BOUND_POST_VALIDATION"', block)
        self.assertNotIn("evaluation_status:", block)

    def test_receipt_runner_revalidates_one_existing_v2_guard_without_second_raw_replay(self) -> None:
        self.assertNotIn("live_raw_guard_replay", builder.EXPECTED_VALIDATION_RECEIPTS)
        command = builder.EXPECTED_VALIDATION_RECEIPTS["live_raw_guard_receipt_freshness"]
        self.assertIn("--private-evidence-only", command)
        self.assertIn("--max-private-evidence-age-seconds 7200", command)
        self.assertNotIn("v015_s03_p1_read_only_root_guard.py", command)
        checker_command = builder.EXPECTED_VALIDATION_RECEIPTS["checker_core_private_dependency"]
        self.assertIn("--pre-receipt-final-governance", checker_command)

    def test_private_evidence_freshness_window_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = 2_000_000_000.0
            paths = []
            for relative, mode in (
                (builder.PRIVATE_RECEIPT_RELATIVE, 0o600),
                (builder.PRIVATE_PROJECTION_RELATIVE, 0o644),
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"{}")
                path.chmod(mode)
                os.utime(path, (now - 10, now - 10))
                paths.append(path)
            errors: list[str] = []
            with mock.patch.object(checker, "PROJECT_ROOT", root):
                checker._validate_private_evidence_freshness(
                    errors,
                    max_age_seconds=7200,
                    now_seconds=now,
                )
            self.assertEqual(errors, [])
            os.utime(paths[0], (now - 8000, now - 8000))
            errors = []
            with mock.patch.object(checker, "PROJECT_ROOT", root):
                checker._validate_private_evidence_freshness(
                    errors,
                    max_age_seconds=7200,
                    now_seconds=now,
                )
            self.assertTrue(any("outside freshness window" in item for item in errors))
            paths[0].chmod(0o644)
            os.utime(paths[0], (now - 10, now - 10))
            errors = []
            with mock.patch.object(checker, "PROJECT_ROOT", root):
                checker._validate_private_evidence_freshness(
                    errors,
                    max_age_seconds=7200,
                    now_seconds=now,
                )
            self.assertTrue(any("type/link/mode unsafe" in item for item in errors))

    def test_frozen_s02_dependency_remains_exact(self) -> None:
        checker.validate_frozen_s02_dependency()

    def test_diff_check_rejects_unfrozen_base(self) -> None:
        with self.assertRaisesRegex(checker.ValidationError, "frozen S03-P1 base"):
            checker.run_structured_public_diff_check("HEAD")

    def test_diff_allowlist_is_exact_and_excludes_unexpected_artifact(self) -> None:
        unexpected = (
            "KMFA/stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/"
            "machine/unexpected.bin"
        )
        self.assertNotIn(unexpected, checker.ALLOWED_DIFF_PATHS)
        self.assertTrue(set(builder.ARTIFACT_REFS.values()).issubset(checker.ALLOWED_DIFF_PATHS))

    def test_builder_writer_rejects_hardlink_and_symlink_without_mutating_source(self) -> None:
        private_root = builder.PROJECT_ROOT / ".codex_private_runtime"
        with tempfile.TemporaryDirectory(dir=private_root) as directory:
            root = Path(directory)
            source = root / "source.bin"
            source.write_bytes(b"protected")
            hardlink = root / "hardlink.bin"
            os.link(source, hardlink)
            with self.assertRaisesRegex(builder.BuildError, "link count is unsafe"):
                builder._write_payload_no_follow(
                    hardlink,
                    b"replacement",
                    forbidden_identities=frozenset(),
                )
            self.assertEqual(source.read_bytes(), b"protected")
            hardlink.unlink()
            symlink = root / "symlink.bin"
            symlink.symlink_to(source)
            with self.assertRaises(OSError):
                builder._write_payload_no_follow(
                    symlink,
                    b"replacement",
                    forbidden_identities=frozenset(),
                )
            self.assertEqual(source.read_bytes(), b"protected")


if __name__ == "__main__":
    unittest.main()
