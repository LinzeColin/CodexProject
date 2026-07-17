from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from KMFA.tools import v015_s03_p1_read_only_root_guard as p1_guard
from KMFA.tools import v015_s03_p2_private_derived_runtime as runtime


SYNTHETIC_RETENTION_DAYS = {
    category: 1 for category in runtime.RETENTION_CATEGORIES
}


class _InjectedMonitor:
    name = "test_s03_p2_monitor"

    def __init__(
        self,
        *,
        event_poll: Optional[int] = None,
        action_poll: Optional[int] = None,
        action=None,
    ) -> None:
        self.event_poll = event_poll
        self.action_poll = action_poll
        self.action = action
        self.poll_count = 0
        self.started = False
        self.closed = False
        self.first_token: Optional[str] = None

    def start(self, watch_targets: dict[str, p1_guard.WatchTarget]) -> None:
        self.started = True
        self.first_token = next(iter(sorted(watch_targets)))

    def poll(self, timeout_seconds: float) -> list[p1_guard.MonitorEvent]:
        del timeout_seconds
        self.poll_count += 1
        if self.action_poll == self.poll_count and self.action is not None:
            self.action()
        if self.event_poll == self.poll_count:
            assert self.first_token is not None
            return [
                p1_guard.MonitorEvent(
                    path_token=self.first_token,
                    flags=("WRITE",),
                )
            ]
        return []

    def close(self) -> None:
        self.closed = True


class _ProductionInjectedMonitor(_InjectedMonitor):
    name = "darwin_kqueue_vnode_recursive"


class TestV015S03P2PrivateDerivedRuntime(unittest.TestCase):
    def _policy(self, root: Path) -> p1_guard.RootPolicy:
        return p1_guard.validate_policy_payload(
            {
                "schema_version": p1_guard.POLICY_SCHEMA_VERSION,
                "root": {
                    "root_id": "PRIMARY_RAW_ROOT",
                    "path": str(root.resolve()),
                },
                "source_scope_id": p1_guard.EXPECTED_SOURCE_SCOPE_ID,
                "max_depth": p1_guard.EXPECTED_MAX_DEPTH,
                "allowed_operations": list(
                    p1_guard.EXPECTED_ALLOWED_OPERATIONS
                ),
                "default_deny_extensions": True,
                "allowed_extensions": list(
                    p1_guard.EXPECTED_ALLOWED_EXTENSIONS
                ),
            }
        )

    def _copy_authorization(self, root: Path) -> runtime.CopyAuthorization:
        policy = self._policy(root)
        return runtime.validate_copy_authorization(
            runtime.copy_authorization_payload(policy),
            policy,
        )

    def _final_cleanup_evidence(
        self,
        phase_result: runtime.PhaseRunResult,
        base: Path,
    ) -> tuple[runtime.CleanupPlan, runtime.SyntheticCleanupRehearsalResult]:
        now_ns = 2_000_000_000_000_000_000
        canonical_plan = runtime.build_cleanup_plan(
            phase_result.runtime_contract.root,
            now_ns=now_ns,
        )
        fixture_root = base / "kmfa_s03_p2_cleanup_fixture"
        runtime.initialize_synthetic_cleanup_runtime(fixture_root)
        candidate = fixture_root / "cache" / "old.bin"
        self._private_file(candidate, b"synthetic rehearsal")
        self._age(candidate, now_ns=now_ns, days=120)
        fixture_plan = runtime.build_cleanup_plan(
            fixture_root,
            now_ns=now_ns,
            retention_days=SYNTHETIC_RETENTION_DAYS,
        )
        rehearsal = runtime.run_synthetic_cleanup_rehearsal(fixture_plan)
        return canonical_plan, rehearsal

    def _fixed_capture_phase(
        self,
        base: Path,
        payloads: dict[str, bytes],
    ) -> tuple[runtime.PhaseRunResult, Path, Path]:
        project_root = base / "fixed_project"
        (project_root / "KMFA").mkdir(parents=True)
        project_root = project_root.resolve()
        raw = base / "fixed_raw"
        raw.mkdir()
        for name, payload in payloads.items():
            (raw / name).write_bytes(payload)
        policy_payload = {
            "schema_version": p1_guard.POLICY_SCHEMA_VERSION,
            "root": {
                "root_id": "PRIMARY_RAW_ROOT",
                "path": str(raw.resolve()),
            },
            "source_scope_id": p1_guard.EXPECTED_SOURCE_SCOPE_ID,
            "max_depth": p1_guard.EXPECTED_MAX_DEPTH,
            "allowed_operations": list(p1_guard.EXPECTED_ALLOWED_OPERATIONS),
            "default_deny_extensions": True,
            "allowed_extensions": list(p1_guard.EXPECTED_ALLOWED_EXTENSIONS),
        }
        policy = p1_guard.validate_policy_payload(policy_payload)
        private_dir = project_root / runtime.FIXED_P1_PRIVATE_DIR_RELATIVE
        private_dir.mkdir(parents=True, mode=0o700)
        os.chmod(private_dir, 0o700)
        policy_path = private_dir / runtime.FIXED_P1_POLICY_FILENAME
        receipt_path = private_dir / runtime.FIXED_P1_RECEIPT_FILENAME
        policy_path.write_text(
            json.dumps(policy_payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        os.chmod(policy_path, 0o600)
        with patch.object(
            p1_guard,
            "DarwinKqueueVnodeMonitor",
            _ProductionInjectedMonitor,
        ):
            p1_result = p1_guard.run_read_only_root_guard(
                policy,
                monitor_timeout_seconds=p1_guard.CONTROLLED_WINDOW_SECONDS,
            )
            receipt_path.write_text(
                json.dumps(
                    p1_guard.build_private_receipt(p1_result),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            os.chmod(receipt_path, 0o600)
            with patch.object(runtime, "PROJECT_ROOT", project_root):
                phase = runtime.run_fixed_project_capture()
        return phase, raw, project_root

    @staticmethod
    def _private_file(path: Path, value: bytes = b"fixture") -> None:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        current = path.parent
        while current != current.parent:
            if current.exists():
                os.chmod(current, 0o700)
            if current.name in runtime.RUNTIME_LAYERS:
                break
            current = current.parent
        path.write_bytes(value)
        os.chmod(path, runtime.PRIVATE_FILE_MODE)

    @staticmethod
    def _age(path: Path, *, now_ns: int, days: int) -> None:
        old = now_ns - days * 24 * 60 * 60 * 1_000_000_000
        os.utime(path, ns=(old, old))

    def test_exact_nine_layers_are_created_with_mode_0700(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "local_runtime"
            contract = runtime.initialize_runtime(root)

            self.assertEqual(contract.layers, runtime.RUNTIME_LAYERS)
            self.assertTrue(contract.all_layers_present)
            self.assertTrue(contract.all_layer_modes_0700)
            self.assertEqual(stat.S_IMODE(os.lstat(root).st_mode), 0o700)
            self.assertEqual(
                sorted(path.name for path in root.iterdir() if path.is_dir()),
                sorted(runtime.RUNTIME_LAYERS),
            )
            for layer in runtime.RUNTIME_LAYERS:
                value = os.lstat(root / layer)
                self.assertFalse(stat.S_ISLNK(value.st_mode))
                self.assertEqual(stat.S_IMODE(value.st_mode), 0o700)

    def test_runtime_layer_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "local_runtime"
            root.mkdir(mode=0o700)
            outside = base / "outside"
            outside.mkdir(mode=0o700)
            (root / "content_mirror").symlink_to(
                outside,
                target_is_directory=True,
            )

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "PRIVATE_DIRECTORY_TYPE_INVALID",
            ):
                runtime.initialize_runtime(root)

    def test_runtime_rejects_unregistered_top_level_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "local_runtime"
            runtime.initialize_runtime(root)
            (root / "unregistered").mkdir(mode=0o700)

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "RUNTIME_ROOT_CONTENT_DRIFT",
            ):
                runtime.inspect_runtime_contract(root)

    def test_copy_creates_sha256_cas_then_reuses_without_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            payloads = {
                "alpha.xlsx": b"alpha workbook",
                "bundle.zip": b"zip bytes",
            }
            for name, payload in payloads.items():
                (raw / name).write_bytes(payload)
            private_root = base / "local_runtime"

            first_monitor = _InjectedMonitor()
            first = runtime.import_authorized_root(
                self._policy(raw),
                private_root,
                copy_authorization=self._copy_authorization(raw),
                monitor_backend=first_monitor,
                final_drain_seconds=0.0,
            )

            self.assertEqual(first.status, "PASS")
            self.assertEqual(first.source_file_count, 2)
            self.assertEqual(first.unique_blob_count, 2)
            self.assertEqual(first.created_count, 2)
            self.assertEqual(first.reused_count, 0)
            self.assertFalse(first.idempotent_reuse_without_rewrite)
            self.assertFalse(first.prohibited_raw_mutation_detected)
            self.assertTrue(first_monitor.started)
            self.assertTrue(first_monitor.closed)
            mtimes: dict[str, int] = {}
            for payload in payloads.values():
                digest = hashlib.sha256(payload).hexdigest()
                blob = (
                    private_root
                    / "content_mirror"
                    / "sha256"
                    / digest[:2]
                    / digest
                )
                self.assertEqual(blob.read_bytes(), payload)
                value = os.lstat(blob)
                self.assertTrue(stat.S_ISREG(value.st_mode))
                self.assertEqual(value.st_nlink, 1)
                self.assertEqual(stat.S_IMODE(value.st_mode), 0o400)
                mtimes[digest] = value.st_mtime_ns

            second = runtime.import_authorized_root(
                self._policy(raw),
                private_root,
                copy_authorization=self._copy_authorization(raw),
                monitor_backend=_InjectedMonitor(),
                final_drain_seconds=0.0,
            )
            self.assertEqual(second.created_count, 0)
            self.assertEqual(second.reused_count, 2)
            self.assertTrue(second.idempotent_reuse_without_rewrite)
            for digest, original_mtime in mtimes.items():
                blob = (
                    private_root
                    / "content_mirror"
                    / "sha256"
                    / digest[:2]
                    / digest
                )
                self.assertEqual(os.lstat(blob).st_mtime_ns, original_mtime)

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "FINAL_CAPTURE_BINDING_REQUIRED",
            ):
                runtime.combine_idempotency_runs(first, second)
            fixed_base = base / "final_capture"
            fixed_base.mkdir()
            phase_result, _, _ = self._fixed_capture_phase(
                fixed_base,
                payloads,
            )
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "IMPORT_MONITOR_PRODUCTION_ATTESTATION_REQUIRED",
            ):
                runtime.combine_idempotency_runs(
                    replace(
                        phase_result.first_import,
                        monitor_production_attested=False,
                    ),
                    phase_result.second_import,
                )
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "FINAL_CAPTURE_DRAIN_INVALID",
            ):
                runtime.combine_idempotency_runs(
                    replace(
                        phase_result.first_import,
                        final_drain_seconds=0.0,
                    ),
                    phase_result.second_import,
                )
            cleanup_plan, rehearsal = self._final_cleanup_evidence(
                phase_result,
                base,
            )
            projection = runtime.build_public_projection(
                phase_result,
                cleanup_plan=cleanup_plan,
                synthetic_rehearsal_result=rehearsal,
            )
            receipt = runtime.build_private_receipt(
                phase_result,
                projection,
                cleanup_plan=cleanup_plan,
                synthetic_rehearsal_result=rehearsal,
            )
            copy_projection = projection["content_addressed_copy"]
            self.assertEqual(
                set(copy_projection),
                {
                    "run_count",
                    "source_file_count",
                    "unique_blob_count",
                    "first_inventory_count",
                    "second_inventory_count",
                    "inventory_digest_set_stable",
                    "first_run_created_count",
                    "first_run_reused_count",
                    "second_run_created_count",
                    "second_run_reused_count",
                    "second_run_new_bytes",
                    "blob_count_stable",
                    "hash_match_both_runs",
                    "hash_algorithm",
                    "idempotent_reuse_without_rewrite",
                    "prohibited_raw_mutation_detected",
                    "quarantine_triggered",
                },
            )
            self.assertEqual(copy_projection["run_count"], 2)
            self.assertEqual(copy_projection["second_run_created_count"], 0)
            self.assertEqual(copy_projection["second_run_reused_count"], 2)
            self.assertEqual(copy_projection["second_run_new_bytes"], 0)
            self.assertTrue(copy_projection["blob_count_stable"])
            self.assertTrue(copy_projection["hash_match_both_runs"])
            self.assertTrue(copy_projection["inventory_digest_set_stable"])
            self.assertEqual(copy_projection["first_inventory_count"], 2)
            self.assertEqual(copy_projection["second_inventory_count"], 2)
            self.assertTrue(projection["cleanup"]["condition_based_retention"])
            self.assertEqual(projection["cleanup"]["candidate_count"], 0)
            self.assertTrue(projection["cleanup"]["synthetic_backup_verified"])
            self.assertTrue(projection["cleanup"]["synthetic_delete_verified"])
            self.assertTrue(projection["cleanup"]["synthetic_restore_verified"])
            self.assertTrue(projection["cleanup"]["synthetic_rehash_verified"])
            self.assertTrue(
                projection["p1_baseline_binding"]["fixed_project_entry"]
            )
            self.assertEqual(
                projection["p1_baseline_binding"]["final_drain_seconds"],
                p1_guard.FINAL_DRAIN_SECONDS,
            )
            private_baseline = receipt["p1_baseline_binding"]
            self.assertRegex(private_baseline["policy_sha256"], r"^sha256:[a-f0-9]{64}$")
            self.assertRegex(
                private_baseline["p1_receipt_sha256"],
                r"^sha256:[a-f0-9]{64}$",
            )
            self.assertEqual(len(private_baseline["final_snapshot_file_rows"]), 2)
            self.assertTrue(receipt["runtime_root_binding"]["same_identity_both_runs"])
            self.assertEqual(
                receipt["cleanup"]["evaluated_at_ns"],
                cleanup_plan.evaluated_at_ns,
            )
            self.assertEqual(receipt["cleanup"]["retention_days"], {})
            rebuilt_cleanup_plan = runtime.build_cleanup_plan(
                phase_result.runtime_contract.root,
                now_ns=receipt["cleanup"]["evaluated_at_ns"],
                retention_days=None,
            )
            self.assertEqual(
                rebuilt_cleanup_plan.plan_digest,
                receipt["cleanup"]["plan_digest"],
            )
            self.assertEqual(
                receipt["content_addressed_copy"]["run_count"],
                2,
            )
            self.assertEqual(
                [row["run_number"] for row in receipt["content_addressed_copy"]["runs"]],
                [1, 2],
            )
            self.assertTrue(
                all(
                    row["observation_scope"] == "raw_root_and_direct_files"
                    for row in receipt["content_addressed_copy"]["runs"]
                )
            )

    def test_duplicate_source_content_maps_to_one_blob(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            (raw / "a.xlsx").write_bytes(b"same")
            (raw / "b.xlsx").write_bytes(b"same")

            result = runtime.import_authorized_root(
                self._policy(raw),
                base / "local_runtime",
                copy_authorization=self._copy_authorization(raw),
                monitor_backend=_InjectedMonitor(),
                final_drain_seconds=0.0,
            )

            self.assertEqual(result.source_file_count, 2)
            self.assertEqual(result.unique_blob_count, 1)
            self.assertEqual(result.created_count, 1)
            self.assertEqual(result.reused_count, 1)
            self.assertEqual(result.cas_inventory.blob_count, 1)
            self.assertTrue(result.cas_inventory.source_digest_set_match)

    def test_cas_inventory_rejects_extra_duplicate_and_malformed_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            payload = b"source"
            (raw / "source.xlsx").write_bytes(payload)
            private_root = base / "local_runtime"
            first = runtime.import_authorized_root(
                self._policy(raw),
                private_root,
                copy_authorization=self._copy_authorization(raw),
                monitor_backend=_InjectedMonitor(),
                final_drain_seconds=0.0,
            )
            source_digest = hashlib.sha256(payload).hexdigest()

            incoming_junk = private_root / "content_mirror" / ".incoming" / "junk"
            incoming_junk.write_bytes(b"junk")
            os.chmod(incoming_junk, 0o600)
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CAS_INCOMING_NOT_EMPTY",
            ):
                runtime.inspect_cas_inventory(
                    private_root,
                    expected_source_digests=[source_digest],
                )
            incoming_junk.unlink()

            extra_payload = b"extra"
            extra_digest = hashlib.sha256(extra_payload).hexdigest()
            extra = (
                private_root
                / "content_mirror"
                / "sha256"
                / extra_digest[:2]
                / extra_digest
            )
            extra.parent.mkdir(mode=0o700)
            extra.write_bytes(extra_payload)
            os.chmod(extra, 0o400)
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CAS_INVENTORY_SOURCE_SET_MISMATCH",
            ):
                runtime.inspect_cas_inventory(
                    private_root,
                    expected_source_digests=[source_digest],
                )
            extra.unlink()
            extra.parent.rmdir()

            source_blob = (
                private_root
                / "content_mirror"
                / "sha256"
                / source_digest[:2]
                / source_digest
            )
            duplicate_name = source_digest[:2] + "f" * 62
            duplicate = source_blob.parent / duplicate_name
            os.link(source_blob, duplicate)
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CAS_BLOB_LINK_COUNT_INVALID",
            ):
                runtime.inspect_cas_inventory(
                    private_root,
                    expected_source_digests=[source_digest],
                )
            self.assertEqual(first.cas_inventory.content_digests, (source_digest,))

    def test_corrupt_existing_cas_blob_is_quarantined_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            payload = b"trusted source"
            (raw / "source.xlsx").write_bytes(payload)
            private_root = base / "local_runtime"
            runtime.initialize_runtime(private_root)
            digest = hashlib.sha256(payload).hexdigest()
            blob = (
                private_root
                / "content_mirror"
                / "sha256"
                / digest[:2]
                / digest
            )
            blob.parent.mkdir(parents=True, mode=0o700)
            os.chmod(blob.parent.parent, 0o700)
            os.chmod(blob.parent, 0o700)
            blob.write_bytes(b"corrupt")
            os.chmod(blob, 0o400)

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CAS_MISMATCH_QUARANTINED",
            ):
                runtime.import_authorized_root(
                    self._policy(raw),
                    private_root,
                    copy_authorization=self._copy_authorization(raw),
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=0.0,
                )

            self.assertFalse(blob.exists())
            quarantined = list((private_root / "quarantine").iterdir())
            self.assertEqual(len(quarantined), 1)
            self.assertEqual(quarantined[0].read_bytes(), b"corrupt")
            self.assertEqual((raw / "source.xlsx").read_bytes(), payload)

    def test_source_symlink_hardlink_and_unsupported_extension_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            outside = base / "outside.xlsx"
            outside.write_bytes(b"outside")

            raw_link = base / "raw_link"
            raw_link.mkdir()
            (raw_link / "link.xlsx").symlink_to(outside)
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "SOURCE_SYMLINK_FORBIDDEN",
            ):
                runtime.import_authorized_root(
                    self._policy(raw_link),
                    base / "runtime_link",
                    copy_authorization=self._copy_authorization(raw_link),
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=0.0,
                )

    def test_copy_requires_exact_s03_p2_authorization_and_negative_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            (raw / "source.xlsx").write_bytes(b"source")
            policy = self._policy(raw)

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "COPY_AUTHORIZATION_REQUIRED",
            ):
                runtime.import_authorized_root(
                    policy,
                    base / "missing_auth_runtime",
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=0.0,
                )
            payload = runtime.copy_authorization_payload(policy)
            payload["raw_parse_allowed"] = True
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "COPY_AUTHORIZATION_NOT_EXACT",
            ):
                runtime.validate_copy_authorization(payload, policy)
            drifted = replace(
                self._copy_authorization(raw),
                overwrite_existing_blob_allowed=True,
            )
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "COPY_AUTHORIZATION_INSTANCE_DRIFT",
            ):
                runtime.import_authorized_root(
                    policy,
                    base / "drifted_auth_runtime",
                    copy_authorization=drifted,
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=0.0,
                )
            self.assertFalse((base / "missing_auth_runtime").exists())
            self.assertFalse((base / "drifted_auth_runtime").exists())

            raw_hard = base / "raw_hard"
            raw_hard.mkdir()
            source = raw_hard / "a.xlsx"
            source.write_bytes(b"hard")
            os.link(source, raw_hard / "b.xlsx")
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "SOURCE_MULTILINK_FORBIDDEN",
            ):
                runtime.import_authorized_root(
                    self._policy(raw_hard),
                    base / "runtime_hard",
                    copy_authorization=self._copy_authorization(raw_hard),
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=0.0,
                )

            raw_bin = base / "raw_bin"
            raw_bin.mkdir()
            (raw_bin / "bad.bin").write_bytes(b"bad")
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "SOURCE_EXTENSION_FORBIDDEN",
            ):
                runtime.import_authorized_root(
                    self._policy(raw_bin),
                    base / "runtime_bin",
                    copy_authorization=self._copy_authorization(raw_bin),
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=0.0,
                )

    def test_monitor_event_stops_copy_and_source_remains_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            source = raw / "a.xlsx"
            source.write_bytes(b"immutable")
            before = p1_guard._prohibited_fingerprint_signature(os.lstat(source))
            monitor = _InjectedMonitor(event_poll=1)

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "SOURCE_MONITOR_EVENT_BEFORE_COPY",
            ):
                runtime.import_authorized_root(
                    self._policy(raw),
                    base / "local_runtime",
                    copy_authorization=self._copy_authorization(raw),
                    monitor_backend=monitor,
                    final_drain_seconds=0.0,
                )

            self.assertTrue(monitor.closed)
            self.assertEqual(
                p1_guard._prohibited_fingerprint_signature(os.lstat(source)),
                before,
            )
            self.assertEqual(source.read_bytes(), b"immutable")

    def test_fixed_capture_rejects_alternate_policy_and_p1_manifest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            phase, raw, _ = self._fixed_capture_phase(
                base,
                {"source.xlsx": b"baseline"},
            )
            baseline = phase.first_import.p1_baseline_binding
            assert baseline is not None
            no_op_first = runtime.import_authorized_root(
                baseline.policy,
                baseline.fixed_runtime_root,
                copy_authorization=phase.first_import.copy_authorization,
                p1_baseline_binding=baseline,
                monitor_backend=_InjectedMonitor(),
                final_drain_seconds=p1_guard.FINAL_DRAIN_SECONDS,
            )
            no_op_second = runtime.import_authorized_root(
                baseline.policy,
                baseline.fixed_runtime_root,
                copy_authorization=phase.first_import.copy_authorization,
                p1_baseline_binding=baseline,
                monitor_backend=_InjectedMonitor(),
                final_drain_seconds=p1_guard.FINAL_DRAIN_SECONDS,
            )
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "IMPORT_MONITOR_PRODUCTION_ATTESTATION_REQUIRED",
            ):
                runtime.combine_idempotency_runs(no_op_first, no_op_second)

            alternate_raw = base / "alternate_raw"
            alternate_raw.mkdir()
            (alternate_raw / "source.xlsx").write_bytes(b"baseline")
            alternate_policy = self._policy(alternate_raw)
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "P1_BASELINE_POLICY_DRIFT",
            ):
                runtime.import_authorized_root(
                    alternate_policy,
                    base / "alternate_runtime",
                    copy_authorization=self._copy_authorization(alternate_raw),
                    p1_baseline_binding=baseline,
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=p1_guard.FINAL_DRAIN_SECONDS,
                )

            (raw / "source.xlsx").write_bytes(b"drifted after P1")
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "P1_BASELINE_FILE_MANIFEST_DRIFT",
            ):
                runtime.import_authorized_root(
                    baseline.policy,
                    baseline.fixed_runtime_root,
                    copy_authorization=phase.first_import.copy_authorization,
                    p1_baseline_binding=baseline,
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=p1_guard.FINAL_DRAIN_SECONDS,
                )

    def test_runtime_root_swap_fails_and_never_writes_replacement_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            (raw / "source.xlsx").write_bytes(b"source")
            runtime_root = base / "local_runtime"
            replacement = base / "replacement"
            runtime.initialize_runtime(replacement)
            moved = base / "held_runtime"

            def swap_runtime_root() -> None:
                runtime_root.rename(moved)
                runtime_root.symlink_to(replacement, target_is_directory=True)

            monitor = _InjectedMonitor(
                action_poll=2,
                action=swap_runtime_root,
            )
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "RUNTIME_ROOT_PATH_IDENTITY_DRIFT",
            ):
                runtime.import_authorized_root(
                    self._policy(raw),
                    runtime_root,
                    copy_authorization=self._copy_authorization(raw),
                    monitor_backend=monitor,
                    final_drain_seconds=0.0,
                )
            self.assertEqual(list((replacement / "content_mirror").iterdir()), [])
            self.assertTrue((moved / "content_mirror" / "sha256").is_dir())

    def test_runtime_inside_raw_or_symlink_alias_is_rejected_before_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            (raw / "source.xlsx").write_bytes(b"source")
            inside = raw / "local_runtime"

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "RUNTIME_INSIDE_SOURCE_FORBIDDEN",
            ):
                runtime.import_authorized_root(
                    self._policy(raw),
                    inside,
                    copy_authorization=self._copy_authorization(raw),
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=0.0,
                )
            self.assertFalse(inside.exists())

            alias = base / "raw_alias"
            alias.symlink_to(raw, target_is_directory=True)
            alias_inside = alias / "derived"
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "RUNTIME_INSIDE_SOURCE_FORBIDDEN",
            ):
                runtime.import_authorized_root(
                    self._policy(raw),
                    alias_inside,
                    copy_authorization=self._copy_authorization(raw),
                    monitor_backend=_InjectedMonitor(),
                    final_drain_seconds=0.0,
                )
            self.assertFalse((raw / "derived").exists())

    def test_public_projection_contains_aggregates_but_no_private_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            raw = base / "raw"
            raw.mkdir()
            raw_name = "confidential-client.xlsx"
            (raw / raw_name).write_bytes(b"private-value")
            result = runtime.import_authorized_root(
                self._policy(raw),
                base / "local_runtime",
                copy_authorization=self._copy_authorization(raw),
                monitor_backend=_InjectedMonitor(),
                final_drain_seconds=0.0,
            )
            single_plan = runtime.build_cleanup_plan(
                result.runtime_contract.root,
                now_ns=2_000_000_000_000_000_000,
            )
            synthetic_claim = runtime.SyntheticCleanupRehearsalResult(
                status="PASS",
                backup_verified=True,
                delete_verified=True,
                restore_verified=True,
                rehash_verified=True,
                protected_violation_count=0,
                candidate_count=1,
            )

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "FINAL_EVIDENCE_REQUIRES_TWO_IMPORT_RUNS",
            ):
                runtime.build_public_projection(  # type: ignore[arg-type]
                    result,
                    cleanup_plan=single_plan,
                    synthetic_rehearsal_result=synthetic_claim,
                )
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "FINAL_EVIDENCE_REQUIRES_TWO_IMPORT_RUNS",
            ):
                runtime.build_private_receipt(  # type: ignore[arg-type]
                    result,
                    {},
                    cleanup_plan=single_plan,
                    synthetic_rehearsal_result=synthetic_claim,
                )
            fixed_base = base / "fixed_final"
            fixed_base.mkdir()
            phase_result, _, _ = self._fixed_capture_phase(
                fixed_base,
                {raw_name: b"private-value"},
            )
            cleanup_plan, rehearsal = self._final_cleanup_evidence(
                phase_result,
                base,
            )

            projection = runtime.build_public_projection(
                phase_result,
                cleanup_plan=cleanup_plan,
                synthetic_rehearsal_result=rehearsal,
                gitignore_attested=True,
            )
            serialized = json.dumps(projection, ensure_ascii=False, sort_keys=True)
            self.assertEqual(
                projection["schema_version"],
                runtime.PUBLIC_PROJECTION_SCHEMA_VERSION,
            )
            self.assertEqual(projection["directory_contract"]["layer_count"], 9)
            self.assertNotIn(str(raw), serialized)
            self.assertNotIn(raw_name, serialized)
            self.assertNotIn(result.items[0].path_token, serialized)
            self.assertNotIn(result.items[0].content_sha256, serialized)
            self.assertNotIn("private-value", serialized)
            receipt = runtime.build_private_receipt(
                phase_result,
                projection,
                cleanup_plan=cleanup_plan,
                synthetic_rehearsal_result=rehearsal,
            )
            canonical = json.dumps(
                projection,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            self.assertEqual(
                receipt["public_projection_sha256"],
                "sha256:" + hashlib.sha256(canonical).hexdigest(),
            )

    def test_private_json_writer_enforces_mode_0600(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private" / "receipt.json"
            runtime.write_private_json(path, {"status": "PASS"})
            self.assertEqual(stat.S_IMODE(os.lstat(path).st_mode), 0o600)
            self.assertEqual(json.loads(path.read_text())["status"], "PASS")

    def test_private_writer_rejects_hardlink_without_truncating_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            parent = base / "private"
            parent.mkdir(mode=0o700)
            outside = base / "outside"
            outside.write_bytes(b"must remain unchanged")
            os.chmod(outside, 0o600)
            alias = parent / "receipt.json"
            os.link(outside, alias)

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "PRIVATE_FILE_EXISTING_UNSAFE",
            ):
                runtime.write_private_json(alias, {"status": "PASS"})

            self.assertEqual(outside.read_bytes(), b"must remain unchanged")
            self.assertEqual(alias.read_bytes(), b"must remain unchanged")

    def test_canonical_cleanup_default_is_until_condition_no_auto_delete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            runtime.initialize_runtime(root)
            candidate = root / "cache" / "old.bin"
            self._private_file(candidate)
            now_ns = 2_000_000_000_000_000_000
            self._age(candidate, now_ns=now_ns, days=10_000)

            plan = runtime.build_cleanup_plan(root, now_ns=now_ns)

            self.assertEqual(plan.retention_days, {})
            self.assertEqual(plan.candidates, ())
            self.assertTrue(candidate.exists())

    def test_cleanup_plan_is_deterministic_and_protects_required_classes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic_runtime"
            runtime.initialize_synthetic_cleanup_runtime(root)
            now_ns = 2_000_000_000_000_000_000
            candidates = (
                root / "extracted" / "old.bin",
                root / "staging" / "old.bin",
                root / "cache" / "old.bin",
                root / "reports" / "drafts" / "old.json",
                root / "logs" / "operational" / "old.log",
                root / "backups" / "old.backup",
            )
            for path in candidates:
                self._private_file(path)
                self._age(path, now_ns=now_ns, days=120)
            protected = (
                root / "content_mirror" / "sha256" / "aa" / ("a" * 64),
                root / "facts" / "fact.json",
                root / "reports" / "published" / "report.json",
                root / "logs" / "audit" / "events.jsonl",
                root / "backups" / "newest.backup",
                root / "quarantine" / "held.blob",
            )
            for path in protected:
                self._private_file(path, b"protected")
            os.chmod(protected[0], 0o400)
            self._age(protected[4], now_ns=now_ns, days=1)

            first = runtime.build_cleanup_plan(
                root,
                now_ns=now_ns,
                retention_days=SYNTHETIC_RETENTION_DAYS,
            )
            second = runtime.build_cleanup_plan(
                root,
                now_ns=now_ns,
                retention_days=SYNTHETIC_RETENTION_DAYS,
            )

            self.assertEqual(first.plan_digest, second.plan_digest)
            self.assertEqual(first.candidates, second.candidates)
            self.assertEqual(first.protected_violation_count, 0)
            planned = {item.relative_path for item in first.candidates}
            self.assertEqual(
                planned,
                {path.relative_to(root).as_posix() for path in candidates},
            )
            self.assertTrue(all(path.exists() for path in candidates))
            self.assertTrue(all(path.exists() for path in protected))

    def test_real_runtime_cleanup_is_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "real_runtime"
            runtime.initialize_runtime(root)
            candidate = root / "cache" / "old.bin"
            self._private_file(candidate)
            now_ns = 2_000_000_000_000_000_000
            self._age(candidate, now_ns=now_ns, days=120)
            plan = runtime.build_cleanup_plan(
                root,
                now_ns=now_ns,
                retention_days=SYNTHETIC_RETENTION_DAYS,
            )

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "REAL_RUNTIME_CLEANUP_FORBIDDEN",
            ):
                runtime.prepare_cleanup_confirmation(plan)
            self.assertTrue(candidate.exists())

    def test_synthetic_marker_cannot_enable_cleanup_outside_designated_os_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            designated_temp = base / "designated_os_temp"
            designated_temp.mkdir()
            repository_area = base / "repository" / "KMFA" / "local_runtime"
            repository_area.parent.mkdir(parents=True)
            runtime.initialize_runtime(repository_area)
            marker = repository_area / "logs" / runtime._SYNTHETIC_MARKER_NAME
            marker.write_text(runtime._SYNTHETIC_MARKER_VALUE, encoding="ascii")
            os.chmod(marker, 0o600)
            candidate = repository_area / "cache" / "old.bin"
            self._private_file(candidate)
            now_ns = 2_000_000_000_000_000_000
            self._age(candidate, now_ns=now_ns, days=120)
            plan = runtime.build_cleanup_plan(
                repository_area,
                now_ns=now_ns,
                retention_days=SYNTHETIC_RETENTION_DAYS,
            )

            with patch.object(
                runtime.tempfile,
                "gettempdir",
                return_value=str(designated_temp),
            ):
                with self.assertRaisesRegex(
                    runtime.PrivateRuntimeError,
                    "SYNTHETIC_FIXTURE_OUTSIDE_OS_TEMP",
                ):
                    runtime.prepare_cleanup_confirmation(plan)
            self.assertTrue(candidate.exists())

    def test_forged_protected_candidate_fails_full_rebuild_before_delete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic_runtime"
            runtime.initialize_synthetic_cleanup_runtime(root)
            now_ns = 2_000_000_000_000_000_000
            cache_file = root / "cache" / "old.bin"
            protected_fact = root / "facts" / "fact.json"
            self._private_file(cache_file, b"cache")
            self._private_file(protected_fact, b"protected fact")
            self._age(cache_file, now_ns=now_ns, days=120)
            plan = runtime.build_cleanup_plan(
                root,
                now_ns=now_ns,
                retention_days=SYNTHETIC_RETENTION_DAYS,
            )
            fact_stat = os.lstat(protected_fact)
            forged_candidate = runtime.CleanupCandidate(
                relative_path="facts/fact.json",
                category="cache",
                size_bytes=int(fact_stat.st_size),
                device=int(fact_stat.st_dev),
                inode=int(fact_stat.st_ino),
                mode=int(fact_stat.st_mode),
                link_count=int(fact_stat.st_nlink),
                mtime_ns=int(fact_stat.st_mtime_ns),
                ctime_ns=int(fact_stat.st_ctime_ns),
            )
            forged = replace(
                plan,
                candidates=(forged_candidate,),
                total_candidate_bytes=forged_candidate.size_bytes,
            )
            forged_payload = runtime._plan_payload(
                root_device=forged.root_device,
                root_inode=forged.root_inode,
                candidates=forged.candidates,
                protected_count=forged.protected_count,
                protected_violation_count=forged.protected_violation_count,
                retention_days=forged.retention_days,
                evaluated_at_ns=forged.evaluated_at_ns,
            )
            forged = replace(
                forged,
                plan_digest=runtime._payload_digest(forged_payload),
            )

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CLEANUP_PLAN_STATE_MISMATCH",
            ):
                runtime.prepare_cleanup_confirmation(forged)
            self.assertEqual(protected_fact.read_bytes(), b"protected fact")
            self.assertTrue(cache_file.exists())

    def test_synthetic_cleanup_requires_exact_second_confirmation_and_is_one_use(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic_runtime"
            runtime.initialize_synthetic_cleanup_runtime(root)
            now_ns = 2_000_000_000_000_000_000
            candidate = root / "cache" / "old.bin"
            protected = root / "facts" / "fact.json"
            self._private_file(candidate, b"delete")
            self._private_file(protected, b"retain")
            self._age(candidate, now_ns=now_ns, days=120)
            plan = runtime.build_cleanup_plan(
                root,
                now_ns=now_ns,
                retention_days=SYNTHETIC_RETENTION_DAYS,
            )

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CLEANUP_CONFIRMATION_MISMATCH",
            ):
                runtime.execute_synthetic_cleanup(
                    plan,
                    confirmation_digest="sha256:" + "0" * 64,
                )
            self.assertTrue(candidate.exists())

            confirmation = runtime.prepare_cleanup_confirmation(plan)
            result = runtime.execute_synthetic_cleanup(
                plan,
                confirmation_digest=confirmation,
            )
            self.assertEqual(result.status, "PASS")
            self.assertEqual(result.deleted_count, 1)
            self.assertFalse(candidate.exists())
            self.assertTrue(protected.exists())

            with self.assertRaises(runtime.PrivateRuntimeError):
                runtime.execute_synthetic_cleanup(
                    plan,
                    confirmation_digest=confirmation,
                )

    def test_cleanup_candidate_drift_fails_before_any_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic_runtime"
            runtime.initialize_synthetic_cleanup_runtime(root)
            now_ns = 2_000_000_000_000_000_000
            first = root / "cache" / "first.bin"
            second = root / "staging" / "second.bin"
            for path in (first, second):
                self._private_file(path)
                self._age(path, now_ns=now_ns, days=120)
            plan = runtime.build_cleanup_plan(
                root,
                now_ns=now_ns,
                retention_days=SYNTHETIC_RETENTION_DAYS,
            )
            confirmation = runtime.prepare_cleanup_confirmation(plan)
            second.write_bytes(b"changed")
            os.chmod(second, 0o600)

            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CLEANUP_PLAN_STATE_MISMATCH",
            ):
                runtime.execute_synthetic_cleanup(
                    plan,
                    confirmation_digest=confirmation,
                )
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())

    def test_cleanup_planning_rejects_symlink_and_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            runtime.initialize_runtime(root)
            outside = Path(directory) / "outside"
            outside.write_bytes(b"outside")
            (root / "cache" / "link").symlink_to(outside)
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CLEANUP_FILE_TYPE_INVALID",
            ):
                runtime.build_cleanup_plan(root, now_ns=2_000_000_000_000_000_000)

            (root / "cache" / "link").unlink()
            first = root / "cache" / "first"
            first.write_bytes(b"same inode")
            os.chmod(first, 0o600)
            os.link(first, root / "cache" / "second")
            with self.assertRaisesRegex(
                runtime.PrivateRuntimeError,
                "CLEANUP_FILE_TYPE_INVALID",
            ):
                runtime.build_cleanup_plan(root, now_ns=2_000_000_000_000_000_000)


if __name__ == "__main__":
    unittest.main()
