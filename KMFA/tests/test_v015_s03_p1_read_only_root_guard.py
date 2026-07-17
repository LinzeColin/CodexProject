from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from KMFA.tools import v015_s03_p1_read_only_root_guard as guard


class _InjectedMonitor:
    name = "test_injected_monitor"

    def __init__(
        self,
        action=None,
        *,
        emit_event: bool = False,
        start_action=None,
    ) -> None:
        self._action = action
        self._start_action = start_action
        self._emit_event = emit_event
        self._first_path_token: Optional[str] = None
        self.started = False
        self.closed = False
        self.poll_timeouts: list[float] = []

    def start(self, watch_targets: dict[str, guard.WatchTarget]) -> None:
        self.started = True
        self._first_path_token = next(iter(sorted(watch_targets)))
        if self._start_action is not None:
            action = self._start_action
            self._start_action = None
            action()

    def poll(self, timeout_seconds: float) -> list[guard.MonitorEvent]:
        self.poll_timeouts.append(timeout_seconds)
        if self._action is not None:
            action = self._action
            self._action = None
            action()
        if self._emit_event:
            assert self._first_path_token is not None
            self._emit_event = False
            return [
                guard.MonitorEvent(
                    path_token=self._first_path_token,
                    flags=("WRITE",),
                )
            ]
        return []

    def close(self) -> None:
        self.closed = True


class TestV015S03P1ReadOnlyRootGuard(unittest.TestCase):
    def _policy(
        self,
        root: Path,
        *,
        allowed_operations: Optional[list[str]] = None,
        allowed_extensions: Optional[list[str]] = None,
        source_scope_id: str = guard.EXPECTED_SOURCE_SCOPE_ID,
        max_depth: int = guard.EXPECTED_MAX_DEPTH,
        resolve_root: bool = True,
    ) -> guard.RootPolicy:
        root_path = root.resolve() if resolve_root else root.absolute()
        return guard.validate_policy_payload(
            {
                "schema_version": guard.POLICY_SCHEMA_VERSION,
                "root": {
                    "root_id": "PRIMARY_RAW_ROOT",
                    "path": str(root_path),
                },
                "source_scope_id": source_scope_id,
                "max_depth": max_depth,
                "allowed_operations": allowed_operations
                or list(guard.EXPECTED_ALLOWED_OPERATIONS),
                "default_deny_extensions": True,
                "allowed_extensions": allowed_extensions
                or list(guard.EXPECTED_ALLOWED_EXTENSIONS),
            }
        )

    @staticmethod
    def _write_fixture(root: Path, relative_path: str, content: bytes) -> Path:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_clean_root_passes_setup_pre_post_and_monitor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_fixture(root, "a.xlsx", b"alpha")
            monitor = _InjectedMonitor()

            result = guard.run_read_only_root_guard(
                self._policy(root),
                monitor_backend=monitor,
            )

            self.assertEqual(result.status, "PASS")
            self.assertTrue(result.setup_to_pre["equal"])
            self.assertTrue(result.pre_to_post["equal"])
            self.assertFalse(result.prohibited_raw_mutation_detected)
            self.assertTrue(monitor.started)
            self.assertTrue(monitor.closed)
            self.assertEqual(monitor.poll_timeouts, [0.0, guard.FINAL_DRAIN_SECONDS])

    def test_missing_policy_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-policy.json"
            with self.assertRaisesRegex(guard.PolicyError, "POLICY_FILE_MISSING"):
                guard.load_policy(missing)

    def test_unreadable_policy_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            policy_path = Path(directory) / "policy.json"
            policy_path.write_text("{}", encoding="utf-8")
            with patch.object(guard.os, "open", side_effect=PermissionError()):
                with self.assertRaisesRegex(
                    guard.PolicyError,
                    "POLICY_FILE_UNREADABLE",
                ):
                    guard.load_policy(policy_path)

    def test_missing_or_unreadable_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory).resolve() / "missing-root"
            policy = self._policy(missing)
            with self.assertRaisesRegex(guard.RootBoundaryError, "ROOT_MISSING"):
                guard.capture_snapshot(policy)

            root = Path(directory).resolve()
            readable_policy = self._policy(root)
            with patch.object(guard.os, "access", return_value=False):
                with self.assertRaisesRegex(
                    guard.RootBoundaryError,
                    "ROOT_NOT_READABLE",
                ):
                    guard.capture_snapshot(readable_policy)

    def test_root_and_child_symlinks_are_rejected_without_following(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / "root"
            root.mkdir()
            self._write_fixture(root, "a.xlsx", b"alpha")
            root_link = base / "root-link"
            root_link.symlink_to(root, target_is_directory=True)

            root_link_policy = self._policy(root_link, resolve_root=False)
            with self.assertRaisesRegex(guard.RootBoundaryError, "ROOT_SYMLINK"):
                guard.capture_snapshot(root_link_policy)

            outside = self._write_fixture(base, "outside.xlsx", b"outside")
            (root / "link.xlsx").symlink_to(outside)
            with self.assertRaisesRegex(guard.SnapshotError, "SYMLINK_FORBIDDEN"):
                guard.capture_snapshot(self._policy(root))

    def test_root_swap_is_anchored_and_never_hashes_outside_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / "root"
            root.mkdir()
            inside_bytes = b"INSIDE-ONLY"
            outside_bytes = b"OUTSIDE-MUST-NOT-BE-READ"
            self._write_fixture(root, "inside.xlsx", inside_bytes)
            outside = base / "outside"
            outside.mkdir()
            self._write_fixture(outside, "outside.xlsx", outside_bytes)
            moved = base / "root-moved"
            real_scandir = os.scandir
            real_hash = guard._hash_regular_descriptor
            swapped = False
            observed_hashes: list[str] = []

            def swap_then_scan(descriptor):
                nonlocal swapped
                if not swapped:
                    swapped = True
                    root.rename(moved)
                    root.symlink_to(outside, target_is_directory=True)
                return real_scandir(descriptor)

            def record_hash(descriptor, expected):
                value = real_hash(descriptor, expected)
                observed_hashes.append(value[0])
                return value

            try:
                with patch.object(guard.os, "scandir", side_effect=swap_then_scan):
                    with patch.object(
                        guard,
                        "_hash_regular_descriptor",
                        side_effect=record_hash,
                    ):
                        with self.assertRaisesRegex(
                            guard.SnapshotError,
                            "DIRECTORY_CHANGED_DURING_SCAN|ROOT_PATH_IDENTITY_DRIFT",
                        ):
                            guard.capture_snapshot(self._policy(root))
                self.assertIn(
                    observed_hashes,
                    ([], [hashlib.sha256(inside_bytes).hexdigest()]),
                )
                self.assertNotIn(
                    hashlib.sha256(outside_bytes).hexdigest(),
                    observed_hashes,
                )
            finally:
                if root.is_symlink():
                    root.unlink()
                if moved.exists():
                    moved.rename(root)

    def test_default_deny_rejects_unsupported_extension(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_fixture(root, "unsupported.bin", b"binary")
            with self.assertRaisesRegex(guard.SnapshotError, "UNSUPPORTED_EXTENSION"):
                guard.capture_snapshot(self._policy(root))

    def test_unregistered_source_scope_and_depth_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.assertRaisesRegex(guard.PolicyError, "SOURCE_SCOPE_UNREGISTERED"):
                self._policy(root, source_scope_id="UNREGISTERED_SCOPE")

            self._write_fixture(root, "nested/a.xlsx", b"nested")
            with self.assertRaisesRegex(guard.SnapshotError, "MAX_DEPTH_EXCEEDED"):
                guard.capture_snapshot(self._policy(root))

    def test_output_inside_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / "root"
            root.mkdir()
            with self.assertRaisesRegex(guard.RootBoundaryError, "OUTPUT_INSIDE_ROOT"):
                guard.validate_output_paths(root, [root / "receipt.json"])

            guard.validate_output_paths(root, [base / "receipt.json"])

    def test_capture_rejects_special_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            special = root / "special.xlsx"
            os.mkfifo(special)
            with self.assertRaisesRegex(guard.SnapshotError, "SPECIAL_FILE_FORBIDDEN"):
                guard.capture_snapshot(self._policy(root))

    def test_receipt_output_hardlink_to_raw_is_rejected_before_truncate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / "root"
            root.mkdir()
            raw_file = self._write_fixture(root, "source.xlsx", b"RAW-BYTES")
            output = base / "private-receipt.json"
            os.link(raw_file, output)
            before = os.stat(raw_file, follow_symlinks=False)

            with self.assertRaisesRegex(
                guard.GuardError,
                "OUTPUT_RAW_IDENTITY_FORBIDDEN",
            ):
                guard.run_read_only_root_guard(
                    self._policy(root),
                    monitor_backend=_InjectedMonitor(),
                    private_receipt_path=output,
                )

            after = os.stat(raw_file, follow_symlinks=False)
            self.assertEqual(raw_file.read_bytes(), b"RAW-BYTES")
            self.assertEqual((after.st_dev, after.st_ino), (before.st_dev, before.st_ino))

    def test_receipt_writer_enforces_exact_private_and_public_modes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / "root"
            root.mkdir()
            private = base / "private.json"
            public = base / "public.json"
            private.write_text("stale", encoding="utf-8")
            public.write_text("stale", encoding="utf-8")
            os.chmod(private, 0o644)
            os.chmod(public, 0o600)
            private_expectation, public_expectation = guard.validate_output_paths(
                root,
                [private, public],
            )

            guard._write_json_receipt(
                private_expectation,
                {"status": "PASS"},
                mode=0o600,
                forbidden_raw_identities=frozenset(),
            )
            guard._write_json_receipt(
                public_expectation,
                {"status": "PASS"},
                mode=0o644,
                forbidden_raw_identities=frozenset(),
            )

            self.assertEqual(os.stat(private).st_mode & 0o777, 0o600)
            self.assertEqual(os.stat(public).st_mode & 0o777, 0o644)

    def test_output_parent_swap_cannot_create_file_in_raw(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / "root"
            root.mkdir()
            raw_file = self._write_fixture(root, "source.xlsx", b"RAW")
            safe_parent = base / "safe-output"
            safe_parent.mkdir()
            moved_parent = base / "safe-output-moved"
            output = safe_parent / "private.json"

            def swap_parent() -> None:
                safe_parent.rename(moved_parent)
                safe_parent.symlink_to(root, target_is_directory=True)

            try:
                with self.assertRaisesRegex(guard.GuardError, "OUTPUT_PARENT_"):
                    guard.run_read_only_root_guard(
                        self._policy(root),
                        monitor_backend=_InjectedMonitor(swap_parent),
                        private_receipt_path=output,
                    )
                self.assertEqual(raw_file.read_bytes(), b"RAW")
                self.assertFalse((root / "private.json").exists())
            finally:
                if safe_parent.is_symlink():
                    safe_parent.unlink()
                if moved_parent.exists():
                    moved_parent.rename(safe_parent)

    def _run_with_mutation(self, root: Path, action) -> guard.GuardRunResult:
        return guard.run_read_only_root_guard(
            self._policy(root),
            monitor_backend=_InjectedMonitor(action),
        )

    def test_added_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_fixture(root, "a.xlsx", b"alpha")
            result = self._run_with_mutation(
                root,
                lambda: self._write_fixture(root, "added.xlsx", b"added"),
            )
            self.assertEqual(result.status, "FAIL")
            self.assertTrue(result.pre_to_post["added_path_tokens"])

    def test_deleted_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            victim = self._write_fixture(root, "victim.xlsx", b"victim")
            result = self._run_with_mutation(root, victim.unlink)
            self.assertEqual(result.status, "FAIL")
            self.assertTrue(result.pre_to_post["deleted_path_tokens"])

    def test_renamed_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = self._write_fixture(root, "before.xlsx", b"same")
            target = root / "after.xlsx"
            result = self._run_with_mutation(root, lambda: source.rename(target))
            self.assertEqual(result.status, "FAIL")
            self.assertTrue(result.pre_to_post["added_path_tokens"])
            self.assertTrue(result.pre_to_post["deleted_path_tokens"])

    def test_content_modification_preserving_size_and_mtime_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target = self._write_fixture(root, "value.xlsx", b"AAAA")
            original = os.stat(target, follow_symlinks=False)

            def mutate_preserving_size_and_mtime() -> None:
                target.write_bytes(b"BBBB")
                os.utime(
                    target,
                    ns=(original.st_atime_ns, original.st_mtime_ns),
                    follow_symlinks=False,
                )

            result = self._run_with_mutation(root, mutate_preserving_size_and_mtime)
            self.assertEqual(result.status, "FAIL")
            self.assertTrue(result.pre_to_post["content_changed_path_tokens"])

    def test_metadata_only_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target = self._write_fixture(root, "mode.xlsx", b"same")
            original_mode = os.stat(target, follow_symlinks=False).st_mode & 0o777

            def change_mode() -> None:
                os.chmod(target, original_mode ^ 0o100, follow_symlinks=False)

            try:
                result = self._run_with_mutation(root, change_mode)
                self.assertEqual(result.status, "FAIL")
                self.assertTrue(result.pre_to_post["metadata_changed_path_tokens"])
            finally:
                os.chmod(target, original_mode, follow_symlinks=False)

    def test_monitor_event_alone_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_fixture(root, "a.xlsx", b"alpha")
            monitor = _InjectedMonitor(emit_event=True)
            with patch.object(
                guard,
                "capture_snapshot",
                wraps=guard.capture_snapshot,
            ) as capture:
                result = guard.run_read_only_root_guard(
                    self._policy(root),
                    monitor_backend=monitor,
                )
            self.assertEqual(result.status, "FAIL")
            self.assertIsNone(result.post_snapshot)
            self.assertEqual(
                result.pre_to_post["stop_reason"],
                "VNODE_EVENT_DETECTED_BEFORE_POST",
            )
            self.assertTrue(result.prohibited_raw_mutation_detected)
            self.assertEqual(capture.call_count, 2)
            self.assertEqual(monitor.poll_timeouts, [0.0])

    def test_monitor_start_time_mutation_stops_before_post_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_fixture(root, "a.xlsx", b"alpha")
            monitor = _InjectedMonitor(
                start_action=lambda: self._write_fixture(
                    root,
                    "start-added.xlsx",
                    b"start-drift",
                )
            )
            with patch.object(
                guard,
                "capture_snapshot",
                wraps=guard.capture_snapshot,
            ) as capture:
                result = guard.run_read_only_root_guard(
                    self._policy(root),
                    monitor_backend=monitor,
                )

            self.assertEqual(result.status, "FAIL")
            self.assertFalse(result.setup_to_pre["equal"])
            self.assertIsNone(result.post_snapshot)
            self.assertEqual(
                result.pre_to_post["stop_reason"],
                "SETUP_PRE_DRIFT_BEFORE_POST",
            )
            self.assertEqual(capture.call_count, 2)
            self.assertEqual(monitor.poll_timeouts, [0.0])

    def test_public_projection_excludes_paths_tokens_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_fixture(root, "a.xlsx", b"alpha")
            if sys.platform != "darwin" or not hasattr(guard.select, "kqueue"):
                self.skipTest("production projection requires Darwin kqueue")
            result = guard.run_read_only_root_guard(
                self._policy(root),
                monitor_timeout_seconds=guard.CONTROLLED_WINDOW_SECONDS,
            )
            public = guard.build_public_projection(result)
            private = guard.build_private_receipt(result)
            public_text = json.dumps(public, ensure_ascii=False, sort_keys=True)
            private_text = json.dumps(private, ensure_ascii=False, sort_keys=True)

            self.assertEqual(public["schema_version"], guard.PUBLIC_RECEIPT_SCHEMA_VERSION)
            self.assertEqual(private["schema_version"], guard.PRIVATE_RECEIPT_SCHEMA_VERSION)
            self.assertNotIn(str(root), public_text)
            self.assertNotIn(str(root), private_text)
            self.assertNotIn('"path_token":', public_text)
            self.assertNotIn('"content_sha256":', public_text)
            self.assertNotIn('"snapshot_sha256":', public_text)
            self.assertIn("path_token", private_text)
            self.assertIn("content_sha256", private_text)
            self.assertFalse(public["privacy"]["root_path_committed"])
            self.assertFalse(public["privacy"]["path_tokens_committed"])
            self.assertFalse(public["privacy"]["content_hashes_committed"])
            self.assertTrue(public["guard"]["root_readable"])
            self.assertTrue(public["guard"]["root_permission_known"])
            self.assertIsInstance(public["guard"]["root_owner_write_bit"], bool)
            self.assertFalse(
                public["guard"]["prohibited_raw_mutation_detected"]
            )
            self.assertTrue(public["guard"]["os_atime_side_effect_possible"])
            self.assertFalse(public["guard"]["os_atime_restoration_performed"])
            self.assertFalse(
                public["guard"]["absolute_zero_metadata_mutation_claimed"]
            )
            self.assertNotIn("raw_mutation_detected", public["guard"])
            self.assertNotIn("raw_mutation_detected", private["guard"])
            self.assertTrue(public["monitor"]["production_backend_attested"])
            self.assertEqual(
                public["monitor"]["controlled_window_seconds"],
                guard.CONTROLLED_WINDOW_SECONDS,
            )
            self.assertEqual(
                public["monitor"]["final_drain_seconds"],
                guard.FINAL_DRAIN_SECONDS,
            )

            rebuilt = guard.public_projection_from_private_receipt(private)
            self.assertEqual(rebuilt, public)

            tampered_content = copy.deepcopy(private)
            file_entry = next(
                entry
                for entry in tampered_content["snapshots"]["setup"]["entries"]
                if entry["kind"] == "file"
            )
            file_entry["content_sha256"] = "0" * 64
            with self.assertRaisesRegex(guard.GuardError, "PRIVATE_RECEIPT_INVALID"):
                guard.public_projection_from_private_receipt(tampered_content)

            duplicate_token = copy.deepcopy(private)
            duplicate_entry = copy.deepcopy(
                duplicate_token["snapshots"]["setup"]["entries"][0]
            )
            duplicate_token["snapshots"]["setup"]["entries"].append(duplicate_entry)
            duplicate_token["snapshots"]["setup"]["entry_count"] += 1
            duplicate_token["snapshots"]["setup"][
                "file_count" if duplicate_entry["kind"] == "file" else "directory_count"
            ] += 1
            with self.assertRaisesRegex(guard.GuardError, "PRIVATE_RECEIPT_INVALID"):
                guard.public_projection_from_private_receipt(duplicate_token)

            comparison_tamper = copy.deepcopy(private)
            comparison_tamper["comparisons"]["setup_to_pre"]["status"] = "FAIL"
            with self.assertRaisesRegex(guard.GuardError, "PRIVATE_RECEIPT_INVALID"):
                guard.public_projection_from_private_receipt(comparison_tamper)

    def test_old_root_and_file_atime_are_observed_without_false_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            if sys.platform != "darwin" or not hasattr(guard.select, "kqueue"):
                self.skipTest("atime production evidence requires Darwin kqueue")
            root = Path(directory).resolve()
            source = self._write_fixture(root, "a.xlsx", b"alpha")
            old_atime_ns = 946684800 * 1_000_000_000
            source_before = os.stat(source, follow_symlinks=False)
            root_before = os.stat(root, follow_symlinks=False)
            os.utime(
                source,
                ns=(old_atime_ns, source_before.st_mtime_ns),
                follow_symlinks=False,
            )
            os.utime(
                root,
                ns=(old_atime_ns, root_before.st_mtime_ns),
                follow_symlinks=False,
            )

            result = guard.run_read_only_root_guard(
                self._policy(root),
                monitor_timeout_seconds=guard.CONTROLLED_WINDOW_SECONDS,
            )

            self.assertEqual(result.status, "PASS")
            self.assertFalse(result.prohibited_raw_mutation_detected)
            self.assertTrue(result.os_atime_side_effect_observed)
            self.assertGreaterEqual(result.os_atime_side_effect_count, 2)
            root_token = guard._path_token("PRIMARY_RAW_ROOT", ".")
            setup_root = next(
                entry
                for entry in result.setup_snapshot.entries
                if entry.path_token == root_token
            )
            setup_file = next(
                entry
                for entry in result.setup_snapshot.entries
                if entry.kind == "file"
            )
            self.assertTrue(setup_root.os_atime_side_effect_observed)
            self.assertTrue(setup_file.os_atime_side_effect_observed)

            private = guard.build_private_receipt(result)
            public = guard.build_public_projection(result)
            self.assertFalse(
                public["guard"]["prohibited_raw_mutation_detected"]
            )
            self.assertTrue(public["guard"]["os_atime_side_effect_possible"])
            self.assertTrue(public["guard"]["os_atime_side_effect_observed"])
            self.assertFalse(public["guard"]["os_atime_restoration_performed"])
            self.assertFalse(private["guard"]["os_atime_restoration_performed"])
            self.assertFalse(
                public["guard"]["absolute_zero_metadata_mutation_claimed"]
            )
            self.assertEqual(
                private["guard"]["os_atime_side_effect_count"],
                result.os_atime_side_effect_count,
            )

            forged_false = copy.deepcopy(private)
            forged_false["guard"]["os_atime_side_effect_observed"] = False
            with self.assertRaisesRegex(
                guard.GuardError,
                "PRIVATE_RECEIPT_INVALID",
            ):
                guard.public_projection_from_private_receipt(forged_false)

            forged_private_restoration = copy.deepcopy(private)
            forged_private_restoration["guard"][
                "os_atime_restoration_performed"
            ] = True
            with self.assertRaisesRegex(
                guard.GuardError,
                "PRIVATE_RECEIPT_INVALID",
            ):
                guard.public_projection_from_private_receipt(
                    forged_private_restoration
                )

            forged_public_restoration = copy.deepcopy(public)
            forged_public_restoration["guard"][
                "os_atime_restoration_performed"
            ] = True
            with self.assertRaisesRegex(
                guard.GuardError,
                "PUBLIC_PROJECTION_INVALID",
            ):
                guard.validate_public_projection(forged_public_restoration)

    def test_synthetic_and_forged_monitor_receipts_cannot_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_fixture(root, "a.xlsx", b"alpha")
            result = guard.run_read_only_root_guard(
                self._policy(root),
                monitor_backend=_InjectedMonitor(),
            )
            private = guard.build_private_receipt(result)

            with self.assertRaisesRegex(
                guard.GuardError,
                "PRODUCTION_MONITOR_REQUIRED",
            ):
                guard.build_public_projection(result)

            forged_backend = copy.deepcopy(private)
            forged_backend["monitor"]["backend"] = "darwin_kqueue_bypass"
            forged_backend["monitor"]["production_backend_attested"] = True
            forged_backend["monitor"][
                "controlled_window_seconds"
            ] = guard.CONTROLLED_WINDOW_SECONDS
            with self.assertRaisesRegex(
                guard.GuardError,
                "PRODUCTION_MONITOR_REQUIRED",
            ):
                guard.public_projection_from_private_receipt(forged_backend)

            zero_second_attested = copy.deepcopy(private)
            zero_second_attested["monitor"][
                "backend"
            ] = guard.DarwinKqueueVnodeMonitor.name
            zero_second_attested["monitor"]["production_backend_attested"] = True
            zero_second_attested["monitor"]["controlled_window_seconds"] = 0.0
            with self.assertRaisesRegex(
                guard.GuardError,
                "PRIVATE_RECEIPT_INVALID",
            ):
                guard.public_projection_from_private_receipt(zero_second_attested)

    def test_public_projection_rebuild_rejects_private_receipt_path_leak(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self._write_fixture(root, "a.xlsx", b"alpha")
            result = guard.run_read_only_root_guard(
                self._policy(root),
                monitor_backend=_InjectedMonitor(),
            )
            private = guard.build_private_receipt(result)
            private["plaintext_path"] = str(root)
            with self.assertRaisesRegex(
                guard.GuardError,
                "PRIVATE_RECEIPT_PATH_LEAK",
            ):
                guard.public_projection_from_private_receipt(private)

    def test_default_private_runtime_paths_are_frozen(self) -> None:
        base = Path(
            "KMFA/.codex_private_runtime/"
            "V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE"
        )
        self.assertEqual(guard.DEFAULT_PRIVATE_RUNTIME_DIR, base)
        self.assertEqual(guard.DEFAULT_POLICY_PATH, base / "private_root_policy.json")
        self.assertEqual(
            guard.DEFAULT_PRIVATE_RECEIPT_PATH,
            base / "private_guard_receipt.json",
        )
        self.assertEqual(
            guard.DEFAULT_PUBLIC_PROJECTION_PATH,
            base / "public_guard_projection.json",
        )
        self.assertEqual(
            guard.DEFAULT_FAILURE_SENTINEL_PATH,
            base / "public_guard_failure_sentinel.json",
        )
        self.assertEqual(guard.CONTROLLED_WINDOW_SECONDS, 0.25)
        self.assertEqual(guard.FINAL_DRAIN_SECONDS, 0.25)

    def test_cli_invalidates_stale_pass_and_writes_public_fail_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory).resolve() / "private-runtime"
            runtime.mkdir()
            policy_path = runtime / "missing-policy.json"
            private_path = runtime / "private.json"
            public_path = runtime / "public.json"
            sentinel_path = runtime / "sentinel.json"
            private_path.write_text('{"status":"PASS"}', encoding="utf-8")
            public_path.write_text('{"status":"PASS"}', encoding="utf-8")
            sentinel_path.write_text('{"status":"STALE"}', encoding="utf-8")

            with patch.multiple(
                guard,
                DEFAULT_POLICY_PATH=policy_path,
                DEFAULT_PRIVATE_RECEIPT_PATH=private_path,
                DEFAULT_PUBLIC_PROJECTION_PATH=public_path,
                DEFAULT_FAILURE_SENTINEL_PATH=sentinel_path,
            ):
                with patch.object(sys, "stderr", new_callable=io.StringIO):
                    return_code = guard.main([])

            self.assertEqual(return_code, 2)
            self.assertFalse(private_path.exists())
            self.assertFalse(public_path.exists())
            self.assertTrue(sentinel_path.is_file())
            sentinel = json.loads(sentinel_path.read_text(encoding="utf-8"))
            self.assertEqual(sentinel["status"], "FAIL")
            self.assertEqual(sentinel["failure_codes"], ["POLICY_FILE_MISSING"])
            self.assertTrue(sentinel["stale_pass_invalidated"])
            self.assertEqual(os.stat(sentinel_path).st_mode & 0o777, 0o644)
            self.assertNotIn(str(runtime), json.dumps(sentinel, sort_keys=True))

    def test_cli_never_truncates_hardlinked_stale_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            runtime = base / "private-runtime"
            runtime.mkdir()
            raw = self._write_fixture(base, "synthetic-raw.xlsx", b"RAW-UNCHANGED")
            private_path = runtime / "private.json"
            os.link(raw, private_path)
            public_path = runtime / "public.json"
            public_path.write_text('{"status":"PASS"}', encoding="utf-8")
            sentinel_path = runtime / "sentinel.json"

            with patch.multiple(
                guard,
                DEFAULT_POLICY_PATH=runtime / "missing-policy.json",
                DEFAULT_PRIVATE_RECEIPT_PATH=private_path,
                DEFAULT_PUBLIC_PROJECTION_PATH=public_path,
                DEFAULT_FAILURE_SENTINEL_PATH=sentinel_path,
            ):
                with patch.object(sys, "stderr", new_callable=io.StringIO):
                    return_code = guard.main([])

            self.assertEqual(return_code, 2)
            self.assertEqual(raw.read_bytes(), b"RAW-UNCHANGED")
            self.assertTrue(private_path.exists())
            self.assertEqual(
                (os.stat(raw).st_dev, os.stat(raw).st_ino),
                (os.stat(private_path).st_dev, os.stat(private_path).st_ino),
            )
            self.assertFalse(public_path.exists())
            sentinel = json.loads(sentinel_path.read_text(encoding="utf-8"))
            self.assertEqual(
                sentinel["failure_codes"],
                ["STALE_OUTPUT_HARDLINK_FORBIDDEN"],
            )

    def test_allowed_operations_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.assertRaisesRegex(guard.PolicyError, "ALLOWED_OPERATIONS_DRIFT"):
                self._policy(
                    root,
                    allowed_operations=["list", "read", "stat", "hash", "write"],
                )


if __name__ == "__main__":
    unittest.main()
