from __future__ import annotations

import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from KMFA.tools import build_v015_s03_p2_private_derived_runtime as builder
from KMFA.tools import check_v015_s03_p2_private_derived_runtime as checker


def valid_projection() -> dict:
    return {
        "schema_version": builder.PUBLIC_PROJECTION_SCHEMA_VERSION,
        "project_id": "KMFA", "target_release": "v1.5",
        "stage_id": "S03", "phase_id": "S03-P2", "status": "PASS",
        "directory_contract": {
            "layer_count": 9, "all_layers_present": True,
            "all_layer_modes_0700": True, "private_files_mode_0600": True,
            "cas_blob_mode_0400": True, "gitignore_attested": True,
        },
        "copy_authorization": {
            "authorization_scope": "READ_ONLY_CONTENT_ADDRESSED_COPY",
            "copy_allowed": True, "raw_parse_allowed": False,
            "raw_value_extraction_allowed": False,
            "destination_must_be_private": True,
            "overwrite_existing_blob_allowed": False,
        },
        "p1_baseline_binding": {
            "fixed_project_entry": True, "policy_bound": True,
            "p1_receipt_strictly_reconstructed": True,
            "p1_final_snapshot_exact_match_both_runs": True,
            "raw_root_identity_match_both_runs": True,
            "final_drain_seconds": 0.25,
        },
        "runtime_root_binding": {
            "fixed_project_runtime": True, "held_dirfd_both_runs": True,
            "device_inode_stable": True, "pathname_identity_stable": True,
        },
        "content_addressed_copy": {
            "run_count": 2, "source_file_count": 5, "unique_blob_count": 5,
            "first_inventory_count": 5, "second_inventory_count": 5,
            "inventory_digest_set_stable": True,
            "first_run_created_count": 5, "first_run_reused_count": 0,
            "second_run_created_count": 0, "second_run_reused_count": 5,
            "created_count": 5, "reused_count": 0, "second_run_new_bytes": 0,
            "blob_count_stable": True, "hash_match_both_runs": True,
            "hash_algorithm": "sha256", "idempotent_reuse_without_rewrite": True,
            "prohibited_raw_mutation_detected": False, "quarantine_triggered": False,
        },
        "authorized_io": {
            "os_atime_side_effect_possible": True,
            "os_atime_side_effect_observed": False,
            "os_atime_restoration_performed": False,
            "absolute_zero_metadata_mutation_claimed": False,
        },
        "cleanup": {
            "mode": "DRY_RUN", "candidate_count": 0,
            "protected_count": 0, "protected_violation_count": 0,
            "synthetic_rehearsal_pass": True, "plan_deterministic": True,
            "destructive_execution_performed": False,
            "second_confirmation_required": True,
            "exact_plan_digest_required": True, "one_use_marker_required": True,
            "real_runtime_deletion_allowed": False,
            "condition_based_retention": True,
            "canonical_retention_basis": "UNTIL_CONDITION",
            "canonical_auto_delete_enabled": False,
            "synthetic_backup_verified": True, "synthetic_delete_verified": True,
            "synthetic_restore_verified": True, "synthetic_rehash_verified": True,
        },
        "privacy": {
            "raw_paths_in_projection": False, "raw_names_in_projection": False,
            "raw_hashes_in_projection": False, "raw_values_in_projection": False,
            "path_tokens_in_projection": False,
        },
    }


def valid_receipt(projection: dict) -> dict:
    digests = ["a", "b", "c", "d", "e"]
    items_first = [{
        "path_token": f"SRC-{index:03d}",
        "content_sha256": "sha256:" + character * 64,
        "size_bytes": index * 10, "status": "CREATED",
        "os_atime_side_effect_observed": False,
    } for index, character in enumerate(digests, start=1)]
    items_second = [dict(row, status="REUSED") for row in items_first]
    baseline_rows = [{
        "path_token": row["path_token"],
        "content_sha256": row["content_sha256"],
        "size_bytes": row["size_bytes"],
    } for row in items_first]
    inventory = {
        "blob_count": 5, "total_bytes": 150,
        "content_digests": ["sha256:" + character * 64 for character in digests],
        "source_digest_set_match": True,
    }
    return {
        "schema_version": builder.PRIVATE_RECEIPT_SCHEMA_VERSION,
        "project_id": "KMFA", "target_release": "v1.5",
        "stage_id": "S03", "phase_id": "S03-P2", "status": "PASS",
        "public_projection_sha256": builder._canonical_projection_digest(projection),
        "directory_contract": {
            "layers": list(builder.LAYERS), "directory_mode": "0700",
            "private_file_mode": "0600", "cas_blob_mode": "0400",
        },
        "copy_authorization": {
            "root_id": "PRIMARY_RAW_ROOT", "source_scope_id": "PRIMARY_RAW_SCOPE",
            "allowed_extensions": [".xlsx", ".zip"], "max_depth": 0,
            "authorization_scope": "READ_ONLY_CONTENT_ADDRESSED_COPY",
            "operation": "copy_to_private_content_addressed_mirror",
            "target_layer": "content_mirror", "copy_allowed": True,
            "raw_parse_allowed": False, "raw_value_extraction_allowed": False,
            "destination_must_be_private": True,
            "overwrite_existing_blob_allowed": False,
        },
        "p1_baseline_binding": {
            "fixed_project_entry": True,
            "policy_sha256": "sha256:" + "1" * 64,
            "p1_receipt_sha256": "sha256:" + "2" * 64,
            "raw_root_device": 1, "raw_root_inode": 2,
            "final_snapshot_file_rows": baseline_rows,
            "final_drain_seconds": 0.25,
        },
        "runtime_root_binding": {
            "device": 3, "inode": 4,
            "same_identity_both_runs": True,
            "pathname_identity_stable": True,
            "held_dirfd_both_runs": True,
        },
        "content_addressed_copy": {
            "hash_algorithm": "sha256",
            "run_count": 2, "source_file_count": 5, "unique_blob_count": 5,
            "blob_count_stable": True, "second_run_new_bytes": 0,
            "inventory_digest_set_stable": True,
            "first_inventory": dict(inventory),
            "second_inventory": dict(inventory),
            "runs": [
                {
                    "run_number": 1, "created_count": 5, "reused_count": 0,
                    "hash_match_all": True, "final_drain_seconds": 0.25,
                    "items": items_first,
                },
                {
                    "run_number": 2, "created_count": 0, "reused_count": 5,
                    "hash_match_all": True, "final_drain_seconds": 0.25,
                    "items": items_second,
                },
            ],
        },
        "monitor": {
            "production_backend_attested_all_runs": True,
            "prohibited_raw_mutation_detected": False,
        },
        "authorized_io": {
            "os_atime_side_effect_possible": True,
            "os_atime_side_effect_observed": False,
            "os_atime_restoration_performed": False,
            "absolute_zero_metadata_mutation_claimed": False,
        },
        "cleanup": {
            "mode": "DRY_RUN", "canonical_retention_basis": "UNTIL_CONDITION",
            "condition_based_retention": True,
            "retention_days": {}, "evaluated_at_ns": 1,
            "plan_digest": "sha256:" + "f" * 64,
            "candidate_count": 0, "candidates": [],
            "protected_count": 0, "protected_violation_count": 0,
            "synthetic_rehearsal": {
                "status": "PASS", "candidate_count": 1,
                "backup_verified": True, "delete_verified": True,
                "restore_verified": True, "rehash_verified": True,
                "protected_violation_count": 0,
            },
        },
    }


class TestV015S03P2PrivateDerivedRuntimeGovernance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = builder.verify_source_package()

    def test_source_package_and_exact_s03_p2_tasks(self) -> None:
        self.assertEqual(self.source["verified_member_count"], 21)
        self.assertEqual(
            (self.source["stage_count"], self.source["phase_count"], self.source["task_count"]),
            (24, 72, 216),
        )
        self.assertTrue(self.source["s03_p2_semantic_equal"])
        self.assertEqual(self.source["s03_p2_task_count"], 3)

    def test_nine_layer_contract_is_exact(self) -> None:
        self.assertEqual(
            builder.LAYERS,
            (
                "content_mirror", "extracted", "staging", "facts", "cache",
                "reports", "logs", "backups", "quarantine",
            ),
        )
        policy = builder._directory_policy()
        self.assertEqual(policy["layer_count"], 9)
        self.assertTrue(all(row["gitignored"] for row in policy["layers"]))
        self.assertFalse(policy["raw_layer"]["inside_runtime"])

    def test_lifecycle_is_condition_based_without_fabricated_days(self) -> None:
        policy = builder._lifecycle_policy()
        self.assertEqual(policy["policy_basis"], "CONDITION_BASED_NO_UNSUPPORTED_RETENTION_DAYS")
        self.assertNotIn("retention_days", str(policy))
        self.assertFalse(policy["real_irreversible_cleanup_performed"])
        self.assertEqual(len(policy["rules"]), 9)

    def test_projection_requires_two_bound_imports(self) -> None:
        value = valid_projection()
        builder._validate_projection(value)
        value["content_addressed_copy"]["run_count"] = 1
        with self.assertRaisesRegex(builder.BuildError, "exactly two"):
            builder._validate_projection(value)

    def test_copy_authorization_is_mandatory_and_exact(self) -> None:
        value = valid_projection()
        value["copy_authorization"]["raw_parse_allowed"] = True
        with self.assertRaisesRegex(builder.BuildError, "copy authorization drift"):
            builder._validate_projection(value)
        projection = valid_projection()
        receipt = valid_receipt(projection)
        receipt["copy_authorization"]["destination_must_be_private"] = False
        with self.assertRaisesRegex(builder.BuildError, "destination_must_be_private"):
            builder._validate_private_receipt(receipt, projection)

    def test_projection_rejects_zero_source_and_second_write(self) -> None:
        value = valid_projection()
        value["content_addressed_copy"]["source_file_count"] = 0
        with self.assertRaisesRegex(builder.BuildError, "source count"):
            builder._validate_projection(value)
        value = valid_projection()
        value["content_addressed_copy"]["second_run_created_count"] = 1
        with self.assertRaisesRegex(builder.BuildError, "created a new blob"):
            builder._validate_projection(value)

    def test_projection_requires_full_cleanup_rehearsal(self) -> None:
        value = valid_projection()
        value["cleanup"]["synthetic_rehash_verified"] = False
        with self.assertRaisesRegex(builder.BuildError, "synthetic_rehash_verified"):
            builder._validate_projection(value)
        value = valid_projection()
        value["cleanup"]["candidate_count"] = 1
        with self.assertRaisesRegex(builder.BuildError, "candidate_count"):
            builder._validate_projection(value)

    def test_private_receipt_binds_identical_two_run_manifest(self) -> None:
        projection = valid_projection()
        receipt = valid_receipt(projection)
        builder._validate_private_receipt(receipt, projection)
        receipt["content_addressed_copy"]["runs"][1]["items"][0]["content_sha256"] = "sha256:" + "c" * 64
        with self.assertRaisesRegex(builder.BuildError, "manifests drift"):
            builder._validate_private_receipt(receipt, projection)

    def test_private_receipt_rejects_single_run(self) -> None:
        projection = valid_projection()
        receipt = valid_receipt(projection)
        receipt["content_addressed_copy"]["run_count"] = 1
        with self.assertRaisesRegex(builder.BuildError, "two imports"):
            builder._validate_private_receipt(receipt, projection)

    def test_zero_final_drain_is_rejected_in_public_and_private_evidence(self) -> None:
        projection = valid_projection()
        projection["p1_baseline_binding"]["final_drain_seconds"] = 0.0
        with self.assertRaisesRegex(builder.BuildError, "baseline binding drift"):
            builder._validate_projection(projection)
        projection = valid_projection()
        receipt = valid_receipt(projection)
        receipt["content_addressed_copy"]["runs"][0]["final_drain_seconds"] = 0.0
        with self.assertRaisesRegex(builder.BuildError, "final drain drift"):
            builder._validate_private_receipt(receipt, projection)

    def test_alternate_p1_snapshot_manifest_is_rejected(self) -> None:
        projection = valid_projection()
        receipt = valid_receipt(projection)
        receipt["p1_baseline_binding"]["final_snapshot_file_rows"][0][
            "content_sha256"
        ] = "sha256:" + "9" * 64
        with self.assertRaisesRegex(builder.BuildError, "does not exactly match"):
            builder._validate_private_receipt(receipt, projection)

    def test_private_receipt_requires_production_monitor_both_runs(self) -> None:
        projection = valid_projection()
        receipt = valid_receipt(projection)
        receipt["monitor"]["production_backend_attested_all_runs"] = False
        with self.assertRaisesRegex(builder.BuildError, "production monitor"):
            builder._validate_private_receipt(receipt, projection)

    def test_private_receipt_requires_typed_synthetic_rehearsal_proof(self) -> None:
        projection = valid_projection()
        receipt = valid_receipt(projection)
        receipt["cleanup"]["synthetic_rehearsal"]["restore_verified"] = False
        with self.assertRaisesRegex(builder.BuildError, "restore_verified"):
            builder._validate_private_receipt(receipt, projection)

    def test_actual_cas_inventory_must_match_private_receipt(self) -> None:
        projection = valid_projection()
        receipt = valid_receipt(projection)
        observed = mock.Mock(
            source_digest_set_match=True,
            blob_count=1,
            total_bytes=30,
            content_digests=("a" * 64, "b" * 64),
        )
        with mock.patch.object(builder.runtime, "inspect_cas_inventory", return_value=observed):
            with self.assertRaisesRegex(builder.BuildError, "blob count drift"):
                builder._validate_actual_cas_inventory(builder.PROJECT_ROOT, receipt)

    def test_actual_cleanup_plan_accepts_canonical_empty_retention_mapping(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=builder.PROJECT_ROOT / ".codex_private_runtime"
        ) as directory:
            root = Path(directory)
            runtime_root = root / builder.LOCAL_RUNTIME_RELATIVE
            builder.runtime.initialize_runtime(runtime_root)
            now_ns = 1_000_000_000
            expected = builder.runtime.build_cleanup_plan(
                runtime_root,
                now_ns=now_ns,
                retention_days=None,
            )
            self.assertEqual(dict(expected.retention_days), {})
            receipt = {
                "cleanup": {
                    "evaluated_at_ns": now_ns,
                    "retention_days": {},
                    "plan_digest": expected.plan_digest,
                    "candidates": [],
                    "protected_violation_count": 0,
                }
            }
            builder._validate_actual_cleanup_plan(root, receipt)

    def test_private_copy_authorization_binds_frozen_p1_policy(self) -> None:
        receipt = valid_receipt(valid_projection())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy_path = root / builder.P1_PRIVATE_POLICY_RELATIVE
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text("{}\n", encoding="utf-8")
            policy_path.chmod(0o600)
            p1_receipt_path = root / builder.P1_PRIVATE_RECEIPT_RELATIVE
            p1_receipt_path.write_text("{}\n", encoding="utf-8")
            p1_receipt_path.chmod(0o600)
            policy = mock.Mock(
                root_id="PRIMARY_RAW_ROOT",
                source_scope_id="PRIMARY_RAW_SCOPE",
                max_depth=0,
            )
            rows = tuple(
                (
                    row["path_token"],
                    row["content_sha256"].removeprefix("sha256:"),
                    row["size_bytes"],
                )
                for row in receipt["p1_baseline_binding"]["final_snapshot_file_rows"]
            )
            fixed = mock.Mock(
                policy=policy,
                root_device=1,
                root_inode=2,
                file_rows=rows,
            )
            receipt["p1_baseline_binding"]["policy_sha256"] = builder._sha256(b"{}\n")
            receipt["p1_baseline_binding"]["p1_receipt_sha256"] = builder._sha256(b"{}\n")
            with mock.patch.object(builder.runtime, "load_fixed_p1_baseline", return_value=fixed):
                builder._validate_p1_policy_binding(root, receipt)
                receipt["copy_authorization"]["source_scope_id"] = "DRIFT"
                with self.assertRaisesRegex(builder.BuildError, "source scope"):
                    builder._validate_p1_policy_binding(root, receipt)

    def test_public_payload_rejects_raw_path_name_hash_and_plan_digest(self) -> None:
        payloads = (
            b'{"raw_' + b'path":"/' + b'Users/example"}',
            b'{"raw_' + b'name":"private.xlsx"}',
            b'{"source_' + b'sha256":"sha256:' + b"a" * 64 + b'"}',
            b'{"plan_' + b'sha256":"sha256:' + b"b" * 64 + b'"}',
        )
        for payload in payloads:
            errors: list[str] = []
            checker._validate_public_payload(payload, errors, label="mutation")
            self.assertTrue(errors)

    def test_task_matrix_contract_drift_fails(self) -> None:
        validation = {
            "expected": 15, "recorded": 15, "passed": 15,
            "pending": 0, "failed": 0, "all_exact_pass": True,
        }
        matrix = builder._task_matrix(self.source, valid_projection(), validation)
        matrix["tasks"][0]["source_contract"]["acceptance"] = "DRIFT"
        errors: list[str] = []
        checker._validate_matrix(matrix, errors, require_pass=True)
        self.assertTrue(any("source contract drift" in error for error in errors))

    def test_evidence_slot_coverage_is_exact(self) -> None:
        rows = builder._slot_rows()
        self.assertEqual(len(rows), 30)
        errors: list[str] = []
        checker._validate_slots(rows[:-1], errors)
        self.assertTrue(any("count drift" in error for error in errors))

    def test_validation_command_drift_fails_closed(self) -> None:
        rows = [{
            "schema_version": builder.VALIDATION_RECEIPT_SCHEMA_VERSION,
            "run_id": None, "validation_id": validation_id,
            "command": command, "result": "PENDING", "exit_code": None,
            "execution_sequence": sequence,
            "phase_base_commit": builder.PHASE_BASE_COMMIT,
        } for sequence, (validation_id, command) in enumerate(
            builder.EXPECTED_VALIDATION_RECEIPTS.items(), start=1,
        )]
        rows[0]["command"] += " --drift"
        errors: list[str] = []
        checker._validate_receipts(rows, errors, require_pass=False)
        self.assertTrue(any("command drift" in error for error in errors))

    def test_postcommit_clean_mode_accepts_only_one_immediate_parent_receipt_head(self) -> None:
        receipt_head = "a" * 40
        current_head = "b" * 40
        rows = [{"head_before": receipt_head, "head_after": receipt_head}]
        with mock.patch.object(
            checker.subprocess,
            "run",
            side_effect=(
                mock.Mock(returncode=0),
                mock.Mock(returncode=0, stdout=receipt_head + "\n"),
            ),
        ) as run:
            selected = checker._committed_validation_head(
                rows,
                current_head=current_head,
            )
        self.assertEqual(selected, receipt_head)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(
            run.call_args_list[0],
            mock.call(
                ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, receipt_head],
                cwd=checker.REPO_ROOT,
                capture_output=True,
                check=False,
            ),
        )
        self.assertEqual(
            run.call_args_list[1],
            mock.call(
                ["git", "rev-parse", "--verify", f"{current_head}^1^{{commit}}"],
                cwd=checker.REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            ),
        )

    def test_postcommit_clean_mode_rejects_divergent_or_mixed_receipt_heads(self) -> None:
        receipt_head = "a" * 40
        current_head = "b" * 40
        rows = [{"head_before": receipt_head, "head_after": receipt_head}]
        with mock.patch.object(
            checker.subprocess,
            "run",
            side_effect=(
                mock.Mock(returncode=0),
                mock.Mock(returncode=0, stdout="c" * 40 + "\n"),
            ),
        ):
            self.assertEqual(
                checker._committed_validation_head(rows, current_head=current_head),
                current_head,
            )
        mixed = [{"head_before": receipt_head, "head_after": "c" * 40}]
        with mock.patch.object(checker.subprocess, "run") as run:
            self.assertEqual(
                checker._committed_validation_head(mixed, current_head=current_head),
                current_head,
            )
        run.assert_not_called()

    def test_postcommit_clean_mode_rejects_receipt_before_phase_base(self) -> None:
        receipt_head = "a" * 40
        current_head = "b" * 40
        rows = [{"head_before": receipt_head, "head_after": receipt_head}]
        with mock.patch.object(
            checker.subprocess,
            "run",
            return_value=mock.Mock(returncode=1),
        ) as run:
            self.assertEqual(
                checker._committed_validation_head(rows, current_head=current_head),
                current_head,
            )
        run.assert_called_once()

    def test_postcommit_allowlist_excludes_unbound_paths(self) -> None:
        self.assertIn("KMFA/CHANGELOG.md", checker.POSTCOMMIT_ALLOWED_REFS)
        self.assertIn(
            "KMFA/stage_artifacts/V015_S03_P2_PRIVATE_DERIVED_RUNTIME/machine/validation_results.jsonl",
            checker.POSTCOMMIT_ALLOWED_REFS,
        )
        self.assertNotIn("KMFA/unbound_private_output.json", checker.POSTCOMMIT_ALLOWED_REFS)
        self.assertIn("scripts/lean_governance.py", builder.VALIDATION_SUBJECT_REFS)
        self.assertNotIn("scripts/lean_governance.py", checker.POSTCOMMIT_ALLOWED_REFS)

    def test_postcommit_changed_path_reader_preserves_unicode_paths(self) -> None:
        errors: list[str] = []
        with mock.patch.object(
            checker.subprocess,
            "run",
            return_value=mock.Mock(
                returncode=0,
                stdout="KMFA/功能清单.md\nKMFA/开发记录.md\n",
            ),
        ) as run:
            paths = checker._git_changed_paths("a" * 40, "b" * 40, errors, label="test")
        self.assertEqual(paths, {"KMFA/功能清单.md", "KMFA/开发记录.md"})
        self.assertFalse(errors)
        self.assertEqual(run.call_args.args[0][1:4], ["-c", "core.quotepath=false", "diff"])

    def test_postvalidation_jsonl_requires_exactly_one_append(self) -> None:
        previous = b'{"event_id":"old"}\n'
        final = {"event_id": "final"}
        current = previous + b'{"event_id":"final"}\n'
        self.assertTrue(checker._exact_jsonl_append(previous, current, [{"event_id": "old"}, final]))
        inserted = previous + b'{"event_id":"inserted"}\n' + b'{"event_id":"final"}\n'
        self.assertFalse(
            checker._exact_jsonl_append(
                previous,
                inserted,
                [{"event_id": "old"}, {"event_id": "inserted"}, final],
            )
        )
        modified = b'{"event_id":"rewritten"}\n' + b'{"event_id":"final"}\n'
        self.assertFalse(
            checker._exact_jsonl_append(previous, modified, [{"event_id": "rewritten"}, final])
        )

    def test_postvalidation_assurance_allows_only_bound_top_level_fields(self) -> None:
        previous = (
            'as_of_event_id: "old"\n'
            'source_snapshot_hash: "sha256:old"\n'
            'generator_version: "manual-1.5.0-dev-s03p2"\n'
        )
        allowed = previous.replace('"old"', '"new"').replace('"sha256:old"', '"sha256:new"')
        self.assertEqual(
            checker._normalize_postvalidation_assurance(previous),
            checker._normalize_postvalidation_assurance(allowed),
        )
        forbidden = allowed.replace("manual-1.5.0-dev-s03p2", "tampered")
        self.assertNotEqual(
            checker._normalize_postvalidation_assurance(previous),
            checker._normalize_postvalidation_assurance(forbidden),
        )

    def test_clean_mode_requires_every_strict_prerequisite(self) -> None:
        valid = {
            "require_validation_receipts": True,
            "require_private_evidence": True,
            "require_dependency_validator": True,
            "require_clean_worktree": True,
            "skip_exact_rebuild": False,
            "pre_receipt_final_governance": False,
        }
        checker._validate_mode_contract(**valid)
        for key, invalid_value in (
            ("require_validation_receipts", False),
            ("require_private_evidence", False),
            ("require_dependency_validator", False),
            ("skip_exact_rebuild", True),
            ("pre_receipt_final_governance", True),
        ):
            mutated = dict(valid, **{key: invalid_value})
            with self.subTest(key=key), self.assertRaises(checker.ValidationError):
                checker._validate_mode_contract(**mutated)

    def test_safe_reader_rejects_symlink_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text('{"private":true}', encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(builder.BuildError, "type/link unsafe"):
                builder._read_regular_bytes_no_follow(link, label="test")

    def test_public_writer_rejects_hardlink_without_truncation(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=builder.PROJECT_ROOT / ".codex_private_runtime"
        ) as directory:
            root = Path(directory)
            source = root / "source"
            source.write_text("protected\n", encoding="utf-8")
            target = root / "target"
            os.link(source, target)
            with self.assertRaisesRegex(builder.BuildError, "unsafe output"):
                builder._write_payload(target, b"replacement\n")
            self.assertEqual(source.read_text(encoding="utf-8"), "protected\n")

    def test_public_builder_never_copies_private_manifest(self) -> None:
        projection = valid_projection()
        receipt = valid_receipt(projection)
        serialized = builder._json_bytes(projection)
        for run in receipt["content_addressed_copy"]["runs"]:
            for item in run["items"]:
                self.assertNotIn(item["path_token"].encode(), serialized)
                self.assertNotIn(item["content_sha256"].encode(), serialized)

    def test_validation_subject_binds_all_executable_phase_code(self) -> None:
        for ref in (
            "KMFA/tools/v015_s03_p2_private_derived_runtime.py",
            "KMFA/tools/build_v015_s03_p2_private_derived_runtime.py",
            "KMFA/tools/check_v015_s03_p2_private_derived_runtime.py",
            "KMFA/tools/run_v015_s03_p2_validations.py",
            "KMFA/tests/test_v015_s03_p2_private_derived_runtime.py",
            "KMFA/tests/test_v015_s03_p2_private_derived_runtime_governance.py",
            "KMFA/tests/test_v015_s03_p2_validation_runner.py",
        ):
            self.assertIn(ref, builder.VALIDATION_SUBJECT_REFS)

    def test_top_level_yaml_identity_cannot_be_nested(self) -> None:
        payload = (
            'current_phase_id: "WRONG"\n'
            'nested:\n'
            '  current_phase_id: "V015_S03_P2_PRIVATE_DERIVED_RUNTIME"\n'
        )
        self.assertEqual(checker._top_level_yaml_scalar(payload, "current_phase_id"), "WRONG")


if __name__ == "__main__":
    unittest.main()
