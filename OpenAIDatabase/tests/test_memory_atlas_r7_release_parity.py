from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER = ROOT / "scripts/materialize_memory_atlas_release.py"
PARITY_AUDITOR = ROOT / "scripts/audit_memory_atlas_snapshot_parity.py"
INSTALLER = ROOT / "scripts/install_memory_atlas_app.py"


def load_module(name: str, script: Path):
    if not script.exists():
        raise AssertionError(f"missing required script: {script.name}")
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def make_database(root: Path) -> tuple[Path, Path]:
    snapshot_path = root / "data/derived/visualization/memory_atlas.json"
    write_json(
        snapshot_path,
        {
            "schema_version": "memory_atlas.v1",
            "overview": {
                "active_memory_count": 7,
                "codex_session_count": 3,
                "conversation_count": 11,
                "edge_count": 23,
                "memory_node_count": 5,
                "node_count": 13,
                "theme_node_count": 1,
            },
            "nodes": [],
            "edges": [],
        },
    )

    raw_manifest_path = root / "machine/raw_manifests/raw_manifest.r7.jsonl"
    raw_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    raw_manifest_path.write_text(
        '{"relative_path":"chatgpt/v1/conversations-000.jsonl","sha256":"abc","size_bytes":12}\n',
        encoding="utf-8",
    )

    package_root = root / "docs/source_packages/memory_atlas_v1_2"
    roadmap = package_root / "roadmap.md"
    taskpack = package_root / "taskpack.zip.part"
    roadmap.parent.mkdir(parents=True, exist_ok=True)
    roadmap.write_bytes(b"authoritative roadmap\n")
    taskpack.write_bytes(b"authoritative task pack\n")
    write_json(
        package_root / "SOURCE_MANIFEST.json",
        {
            "schema_version": "memory_atlas.source_package_manifest.v1",
            "files": [
                {
                    "original_name": "roadmap.md",
                    "storage_name": roadmap.name,
                    "size": roadmap.stat().st_size,
                    "sha256": sha256(roadmap),
                },
                {
                    "original_name": "taskpack.zip",
                    "storage_name": taskpack.name,
                    "size": taskpack.stat().st_size,
                    "sha256": sha256(taskpack),
                },
            ],
        },
    )
    return snapshot_path, raw_manifest_path


def assert_relative_paths(testcase: unittest.TestCase, value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.endswith("_path") and isinstance(nested, str):
                path = Path(nested)
                testcase.assertFalse(path.is_absolute(), f"absolute path in {key}")
                testcase.assertNotIn("..", path.parts, f"escaping path in {key}")
            assert_relative_paths(testcase, nested)
    elif isinstance(value, list):
        for nested in value:
            assert_relative_paths(testcase, nested)


class MemoryAtlasR7ReleaseTests(unittest.TestCase):
    def test_materialize_release_records_hashes_counts_and_relative_paths(self) -> None:
        module = load_module("materialize_memory_atlas_release_create", MATERIALIZER)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)

            result = module.materialize_release(database_dir, "r7-test-001", snapshot_path, raw_manifest_path)
            manifest_path = database_dir / result["release_manifest_path"]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            pointer = json.loads(
                (database_dir / "机器治理/发布快照/memory_atlas_current_release.json").read_text(encoding="utf-8")
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(manifest["release_id"], "r7-test-001")
            self.assertEqual(manifest["snapshot"]["sha256"], sha256(snapshot_path))
            self.assertEqual(manifest["snapshot"]["counts"]["node_count"], 13)
            self.assertEqual(manifest["snapshot"]["counts"]["edge_count"], 23)
            self.assertEqual(manifest["raw_manifest"]["sha256"], sha256(raw_manifest_path))
            self.assertEqual(len(manifest["source_packages"]["files"]), 2)
            self.assertTrue(all(entry["verified"] for entry in manifest["source_packages"]["files"]))
            self.assertEqual(pointer["release_id"], "r7-test-001")
            self.assertEqual(pointer["snapshot_sha256"], sha256(snapshot_path))
            assert_relative_paths(self, manifest)
            assert_relative_paths(self, pointer)
            self.assertNotIn(str(database_dir), json.dumps(manifest, ensure_ascii=False))
            self.assertNotIn(str(database_dir), json.dumps(pointer, ensure_ascii=False))

            verified = module.verify_current_release(database_dir)

            self.assertEqual(verified["status"], "PASS")
            self.assertEqual(verified["snapshot_sha256"], sha256(snapshot_path))
            assert_relative_paths(self, verified)

    def test_release_id_is_idempotent_for_same_bytes_and_immutable_for_drift(self) -> None:
        module = load_module("materialize_memory_atlas_release_immutable", MATERIALIZER)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)
            first = module.materialize_release(database_dir, "r7-test-immutable", snapshot_path, raw_manifest_path)
            release_snapshot = database_dir / first["snapshot_path"]
            original_release_bytes = release_snapshot.read_bytes()

            second = module.materialize_release(database_dir, "r7-test-immutable", snapshot_path, raw_manifest_path)
            self.assertFalse(second["created"])

            snapshot_path.write_bytes(snapshot_path.read_bytes() + b" ")
            with self.assertRaises(module.ReleaseError):
                module.materialize_release(database_dir, "r7-test-immutable", snapshot_path, raw_manifest_path)

            self.assertEqual(release_snapshot.read_bytes(), original_release_bytes)

    def test_release_rejects_unsafe_id_and_absolute_manifest_pointer(self) -> None:
        module = load_module("materialize_memory_atlas_release_paths", MATERIALIZER)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)
            with self.assertRaises(module.ReleaseError):
                module.materialize_release(database_dir, "../escape", snapshot_path, raw_manifest_path)

            module.materialize_release(database_dir, "r7-test-paths", snapshot_path, raw_manifest_path)
            pointer_path = database_dir / "机器治理/发布快照/memory_atlas_current_release.json"
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            pointer["release_manifest_path"] = "/private/source/release_manifest.json"
            write_json(pointer_path, pointer)

            result = module.verify_current_release(database_dir)

            self.assertEqual(result["status"], "FAIL")
            self.assertIn("release_manifest_path must be repository-relative", result["errors"])
            self.assertNotIn("/private/source", json.dumps(result))

    def test_failed_manifest_write_removes_partial_release_directory(self) -> None:
        module = load_module("materialize_memory_atlas_release_atomic", MATERIALIZER)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)
            release_dir = database_dir / "data/releases/memory_atlas/v1_2/r7-test-atomic"

            with patch.object(module, "write_json_atomic", side_effect=OSError("simulated write failure")):
                with self.assertRaises(OSError):
                    module.materialize_release(database_dir, "r7-test-atomic", snapshot_path, raw_manifest_path)

            self.assertFalse(release_dir.exists())

    def test_relative_release_manifest_symlink_cannot_escape_repository(self) -> None:
        module = load_module("materialize_memory_atlas_release_symlink", MATERIALIZER)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database_dir = root / "database"
            snapshot_path, raw_manifest_path = make_database(database_dir)
            release = module.materialize_release(database_dir, "r7-test-symlink", snapshot_path, raw_manifest_path)
            manifest_path = database_dir / release["release_manifest_path"]
            external_manifest = root / "external-release-manifest.json"
            external_manifest.write_bytes(manifest_path.read_bytes())
            manifest_path.unlink()
            manifest_path.symlink_to(external_manifest)

            result = module.verify_current_release(database_dir)

            self.assertEqual(result["status"], "FAIL")
            self.assertIn("release_manifest_path resolves outside repository", result["errors"])
            self.assertNotIn(str(root), json.dumps(result))

    def test_release_manifest_byte_drift_fails_verification_and_reuse(self) -> None:
        module = load_module("materialize_memory_atlas_release_manifest_drift", MATERIALIZER)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)
            release = module.materialize_release(database_dir, "r7-test-manifest-drift", snapshot_path, raw_manifest_path)
            manifest_path = database_dir / release["release_manifest_path"]
            manifest_path.write_bytes(manifest_path.read_bytes() + b" ")

            verified = module.verify_current_release(database_dir)

            self.assertEqual(verified["status"], "FAIL")
            self.assertIn("release manifest hash mismatch", verified["errors"])
            with self.assertRaises(module.ReleaseError):
                module.materialize_release(database_dir, "r7-test-manifest-drift", snapshot_path, raw_manifest_path)


class MemoryAtlasR7ParityTests(unittest.TestCase):
    def test_exact_release_derived_local_and_pages_parity_passes(self) -> None:
        materializer = load_module("materialize_memory_atlas_release_for_parity", MATERIALIZER)
        auditor = load_module("audit_memory_atlas_snapshot_parity_pass", PARITY_AUDITOR)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)
            materializer.materialize_release(database_dir, "r7-parity-pass", snapshot_path, raw_manifest_path)
            local_runtime = database_dir / "tmp/local-runtime"
            pages_candidate = database_dir / "apps/memory-atlas/dist"
            local_runtime.mkdir(parents=True)
            pages_candidate.mkdir(parents=True)
            (local_runtime / "memory_atlas.json").write_bytes(snapshot_path.read_bytes())
            (pages_candidate / "memory_atlas.json").write_bytes(snapshot_path.read_bytes())

            result = auditor.audit_snapshot_parity(database_dir, local_runtime, pages_candidate)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["expected_sha256"], sha256(snapshot_path))
            self.assertEqual(set(result["candidates"]), {"release", "derived", "local_runtime", "pages"})
            self.assertTrue(all(item["status"] == "MATCH" for item in result["candidates"].values()))
            self.assertNotIn(str(database_dir), json.dumps(result))

    def test_one_byte_mismatch_and_missing_candidate_fail_closed(self) -> None:
        materializer = load_module("materialize_memory_atlas_release_for_failure", MATERIALIZER)
        auditor = load_module("audit_memory_atlas_snapshot_parity_fail", PARITY_AUDITOR)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)
            materializer.materialize_release(database_dir, "r7-parity-fail", snapshot_path, raw_manifest_path)
            local_runtime = database_dir / "tmp/local-runtime/memory_atlas.json"
            pages_candidate = database_dir / "apps/memory-atlas/dist/memory_atlas.json"
            local_runtime.parent.mkdir(parents=True)
            pages_candidate.parent.mkdir(parents=True)
            local_runtime.write_bytes(snapshot_path.read_bytes())
            pages_candidate.write_bytes(snapshot_path.read_bytes() + b" ")

            mismatch = auditor.audit_snapshot_parity(database_dir, local_runtime, pages_candidate)
            pages_candidate.unlink()
            missing = auditor.audit_snapshot_parity(database_dir, local_runtime, pages_candidate)

            self.assertEqual(mismatch["status"], "FAIL")
            self.assertEqual(mismatch["mismatched_candidates"], ["pages"])
            self.assertEqual(mismatch["missing_candidates"], [])
            self.assertEqual(missing["status"], "FAIL")
            self.assertEqual(missing["missing_candidates"], ["pages"])


class MemoryAtlasR7InstallerTests(unittest.TestCase):
    def test_default_runtime_snapshot_is_verified_pinned_release(self) -> None:
        materializer = load_module("materialize_memory_atlas_release_for_installer", MATERIALIZER)
        installer = load_module("install_memory_atlas_app_r7_default", INSTALLER)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)
            release = materializer.materialize_release(database_dir, "r7-installer", snapshot_path, raw_manifest_path)

            with patch.object(installer, "refresh_memory_atlas_snapshot") as refresh:
                selected = installer.resolve_runtime_snapshot(database_dir, explicit_refresh=False)

            refresh.assert_not_called()
            self.assertEqual(selected["source"], "pinned_release")
            self.assertEqual(selected["release_id"], "r7-installer")
            self.assertEqual(selected["snapshot_sha256"], release["snapshot_sha256"])
            self.assertEqual(selected["path"], database_dir.resolve() / release["snapshot_path"])

    def test_explicit_refresh_preserves_local_sync_without_moving_release(self) -> None:
        materializer = load_module("materialize_memory_atlas_release_for_refresh", MATERIALIZER)
        installer = load_module("install_memory_atlas_app_r7_refresh", INSTALLER)
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            snapshot_path, raw_manifest_path = make_database(database_dir)
            materializer.materialize_release(database_dir, "r7-installer-refresh", snapshot_path, raw_manifest_path)
            pointer_path = database_dir / "机器治理/发布快照/memory_atlas_current_release.json"
            pointer_before = pointer_path.read_bytes()

            with patch.object(installer, "refresh_memory_atlas_snapshot") as refresh:
                selected = installer.resolve_runtime_snapshot(database_dir, explicit_refresh=True)

            refresh.assert_called_once_with(database_dir.resolve())
            self.assertEqual(selected["source"], "explicit_local_refresh")
            self.assertEqual(selected["path"], snapshot_path.resolve())
            self.assertEqual(pointer_path.read_bytes(), pointer_before)

    def test_launcher_refreshes_only_on_explicit_flag_and_records_release_metadata(self) -> None:
        installer = load_module("install_memory_atlas_app_r7_launcher", INSTALLER)
        launcher = installer.build_launcher_script(ROOT, ROOT)
        launch_block = launcher[launcher.index('echo "=== $(date') :]

        self.assertIn('if [[ "${MEMORY_ATLAS_REFRESH:-0}" == "1" ]]; then', launch_block)
        self.assertIn("copy_latest_snapshot_to_runtime", launch_block)
        self.assertIn("elif runtime_is_stale; then", launch_block)
        self.assertIn('prepare_runtime "pinned_release"', launch_block)
        self.assertNotIn("copy_latest_snapshot_to_runtime; then", launch_block.split("elif runtime_is_stale; then", 1)[1])
        self.assertIn("scripts/materialize_memory_atlas_release.py", launcher)
        self.assertIn('"snapshot_source"', launcher)
        self.assertIn('"release_id"', launcher)
        self.assertIn('"snapshot_sha256"', launcher)
        stale_block = launcher.split("runtime_is_stale() {", 1)[1].split("stop_managed_server() {", 1)[0]
        self.assertIn("PINNED_RELEASE_ID", stale_block)
        self.assertIn("PINNED_SNAPSHOT_SHA256", stale_block)
        self.assertIn('snapshot_source', stale_block)
        self.assertIn("hashlib.sha256", stale_block)

    def test_runtime_build_metadata_rehashes_copied_snapshot(self) -> None:
        installer = load_module("install_memory_atlas_app_r7_build_info", INSTALLER)
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir) / "runtime"
            runtime_dir.mkdir()
            snapshot_path = runtime_dir / "memory_atlas.json"
            write_json(snapshot_path, {"overview": {"generated_at": "2026-07-11T00:00:00Z"}})
            actual_sha256 = sha256(snapshot_path)

            with self.assertRaises(RuntimeError):
                installer.write_runtime_build_info(
                    ROOT,
                    runtime_dir,
                    snapshot_source="pinned_release",
                    release_id="r7-build-info",
                    snapshot_sha256="0" * 64,
                )
            self.assertFalse((runtime_dir / "memory_atlas_build.json").exists())

            installer.write_runtime_build_info(
                ROOT,
                runtime_dir,
                snapshot_source="pinned_release",
                release_id="r7-build-info",
                snapshot_sha256=actual_sha256,
            )
            build_info = json.loads((runtime_dir / "memory_atlas_build.json").read_text(encoding="utf-8"))

            self.assertEqual(build_info["snapshot_source"], "pinned_release")
            self.assertEqual(build_info["release_id"], "r7-build-info")
            self.assertEqual(build_info["snapshot_sha256"], actual_sha256)


if __name__ == "__main__":
    unittest.main()
