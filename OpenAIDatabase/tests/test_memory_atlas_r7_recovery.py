from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Any
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_memory_atlas_github_recovery.py"
SOURCE_PACKAGE_ROOT = Path("docs/source_packages/memory_atlas_v1_2")
RAW_MANIFEST = Path("机器治理/证据与日志/raw_archive_manifests/raw_manifest.v1_2_r7.jsonl")
RAW_LEDGER = Path("机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl")
CURRENT_RELEASE = Path("机器治理/发布快照/memory_atlas_current_release.json")
RELEASE_ID = "memory-atlas-v1-2-r7-test"
RELEASE_ROOT = Path("data/releases/memory_atlas/v1_2") / RELEASE_ID


def load_module():
    spec = importlib.util.spec_from_file_location("audit_memory_atlas_github_recovery", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def assert_portable(test: unittest.TestCase, value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_portable(test, item)
        return
    if isinstance(value, list):
        for item in value:
            assert_portable(test, item)
        return
    if not isinstance(value, str) or not value:
        return
    test.assertNotIn("/private/", value)
    test.assertNotIn("/Users/", value)
    test.assertNotRegex(value, r"(^|[\s(=])/(?!/)")
    test.assertNotRegex(value, r"^[A-Za-z]:[\\/]")


class RecoveryFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo = root / "repo"
        self.database = self.repo / "OpenAIDatabase"
        self.output_dir = root / "recovery-work"
        self.frontend_commands: list[list[str]] = []
        self.snapshot_bytes = (
            json.dumps(
                {
                    "schema_version": "memory_atlas.visualization.v1_2",
                    "overview": {
                        "active_memory_count": 2,
                        "codex_session_count": 1,
                        "conversation_count": 3,
                        "edge_count": 1,
                        "node_count": 2,
                    },
                    "nodes": [{"id": "one"}, {"id": "two"}],
                    "edges": [{"source": "one", "target": "two"}],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")

    def create(self) -> str:
        self.database.mkdir(parents=True)
        self._write_source_package()
        self._write_public_raw()
        self._write_release()
        self._write_frontend_fixture()
        self._write_public_raw_auditor()

        run_git(self.repo, "init", "-q")
        run_git(self.repo, "config", "user.name", "Recovery Test")
        run_git(self.repo, "config", "user.email", "recovery@example.invalid")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-qm", "fixture")
        commit = run_git(self.repo, "rev-parse", "HEAD")

        untracked = self.database / "untracked-private-input.txt"
        untracked.write_text("must never enter recovery archive\n", encoding="utf-8")
        return commit

    def commit_change(self, message: str) -> str:
        run_git(self.repo, "add", "-u")
        run_git(self.repo, "commit", "-qm", message)
        return run_git(self.repo, "rev-parse", "HEAD")

    def _write_source_package(self) -> None:
        package_root = self.database / SOURCE_PACKAGE_ROOT
        package_root.mkdir(parents=True)
        roadmap_name = "v1.2_四线14Stage升级_Roadmap.md"
        archive_name = "Memory_Atlas_v1.2_四线14Stage升级_TaskPack.zip"
        roadmap = package_root / roadmap_name
        archive_part = package_root / f"{archive_name}.part"
        roadmap.write_text("# Memory Atlas v1.2 test roadmap\n", encoding="utf-8")
        with zipfile.ZipFile(archive_part, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("TaskPack/README.md", "tracked task pack fixture\n")
        files = [
            {
                "original_name": roadmap_name,
                "storage_name": roadmap_name,
                "restore_mode": "copy",
                "sha256": sha256_file(roadmap),
                "size": roadmap.stat().st_size,
            },
            {
                "original_name": archive_name,
                "storage_name": archive_part.name,
                "restore_mode": "copy_part_to_original_name",
                "sha256": sha256_file(archive_part),
                "size": archive_part.stat().st_size,
            },
        ]
        write_json(
            package_root / "SOURCE_MANIFEST.json",
            {
                "schema_version": "memory_atlas.source_package_manifest.v1",
                "source_package_id": "memory-atlas-v1.2-four-line-14-stage",
                "files": files,
            },
        )

    def _write_public_raw(self) -> None:
        raw_root = self.database / "data/public_raw"
        raw_files = {
            "chatgpt/export-a.json": b'{"text":"ordinary chat transcript"}\n',
            "codex/sessions/session-a.jsonl": b'{"text":"ordinary codex transcript"}\n',
            "agents/codex-reviewer/event-a.json": b'{"text":"ordinary reviewer event"}\n',
        }
        rows: list[dict[str, Any]] = []
        for relative, payload in raw_files.items():
            path = raw_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            source_id = "agent:codex-reviewer" if relative.startswith("agents/") else relative.split("/", 1)[0]
            rows.append(
                {
                    "source_id": source_id,
                    "relative_path": relative,
                    "sha256": sha256_bytes(payload),
                    "size_bytes": len(payload),
                    "imported_at": "2026-07-11T00:00:00Z",
                }
            )
        write_jsonl(self.database / RAW_MANIFEST, rows)
        write_jsonl(self.database / RAW_LEDGER, rows)

    def _write_release(self) -> None:
        release_snapshot = self.database / RELEASE_ROOT / "memory_atlas.json"
        release_snapshot.parent.mkdir(parents=True, exist_ok=True)
        release_snapshot.write_bytes(self.snapshot_bytes)
        derived_snapshot = self.database / "data/derived/visualization/memory_atlas.json"
        derived_snapshot.parent.mkdir(parents=True, exist_ok=True)
        derived_snapshot.write_bytes(self.snapshot_bytes)

        package_manifest = json.loads(
            (self.database / SOURCE_PACKAGE_ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8")
        )
        source_package_files = [
            {
                "original_name": item["original_name"],
                "relative_path": (SOURCE_PACKAGE_ROOT / item["storage_name"]).as_posix(),
                "sha256": item["sha256"],
                "size_bytes": item["size"],
                "verified": True,
            }
            for item in package_manifest["files"]
        ]
        source_manifest_path = self.database / SOURCE_PACKAGE_ROOT / "SOURCE_MANIFEST.json"
        manifest = {
            "schema_version": "memory_atlas.release_manifest.v1",
            "release_id": RELEASE_ID,
            "snapshot": {
                "relative_path": (RELEASE_ROOT / "memory_atlas.json").as_posix(),
                "sha256": sha256_bytes(self.snapshot_bytes),
                "size_bytes": len(self.snapshot_bytes),
                "counts": {
                    "active_memory_count": 2,
                    "codex_session_count": 1,
                    "conversation_count": 3,
                    "edge_count": 1,
                    "node_count": 2,
                },
            },
            "raw_manifest": {
                "relative_path": RAW_MANIFEST.as_posix(),
                "sha256": sha256_file(self.database / RAW_MANIFEST),
                "size_bytes": (self.database / RAW_MANIFEST).stat().st_size,
            },
            "source_packages": {
                "manifest_path": (SOURCE_PACKAGE_ROOT / "SOURCE_MANIFEST.json").as_posix(),
                "manifest_sha256": sha256_file(source_manifest_path),
                "manifest_size_bytes": source_manifest_path.stat().st_size,
                "files": source_package_files,
            },
        }
        release_manifest = self.database / RELEASE_ROOT / "release_manifest.json"
        write_json(release_manifest, manifest)
        write_json(
            self.database / CURRENT_RELEASE,
            {
                "schema_version": "memory_atlas.current_release.v1",
                "release_id": RELEASE_ID,
                "release_manifest_path": (RELEASE_ROOT / "release_manifest.json").as_posix(),
                "snapshot_path": (RELEASE_ROOT / "memory_atlas.json").as_posix(),
                "snapshot_sha256": sha256_bytes(self.snapshot_bytes),
            },
        )

    def _write_frontend_fixture(self) -> None:
        app = self.database / "apps/memory-atlas"
        write_json(
            app / "package.json",
            {"name": "recovery-fixture", "private": True, "scripts": {"build": "fixture-build"}},
        )
        write_json(
            app / "package-lock.json",
            {"name": "recovery-fixture", "lockfileVersion": 3, "requires": True, "packages": {}},
        )

    def _write_public_raw_auditor(self) -> None:
        helper = self.database / "scripts/recovery_audit_fixture_helper.py"
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_text(
            "def public_raw_files(database_dir):\n"
            "    return [p for p in (database_dir / 'data/public_raw').rglob('*') if p.is_file()]\n",
            encoding="utf-8",
        )
        path = self.database / "scripts/audit_memory_atlas_public_raw.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "from pathlib import Path\n\n"
            "from recovery_audit_fixture_helper import public_raw_files\n\n"
            "def audit_public_raw(database_dir: Path, max_file_bytes: int = 40 * 1024 * 1024):\n"
            "    files = public_raw_files(database_dir)\n"
            "    return {'status': 'PASS', 'raw_file_count': len(files), 'finding_count': 0}\n",
            encoding="utf-8",
        )

    def frontend_runner(self, argv: list[str], *, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
        self.frontend_commands.append(list(argv))
        recovered_database = cwd.parents[1]
        if (recovered_database / "untracked-private-input.txt").exists():
            raise AssertionError("untracked working-tree input entered the archive")
        if argv[:2] == ["npm", "run"]:
            dist = cwd / "dist/memory_atlas.json"
            dist.parent.mkdir(parents=True, exist_ok=True)
            dist.write_bytes(self.snapshot_bytes)
        return {
            "status": "PASS",
            "command": list(argv),
            "returncode": 0,
            "stdout_tail": "",
            "stderr_tail": "",
        }


class MemoryAtlasR7RecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.fixture = RecoveryFixture(Path(self.temp.name))
        self.commit = self.fixture.create()
        self.module = load_module()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def rehearse(self, commit: str | None = None, runner=None) -> dict[str, Any]:
        selected_runner = runner or self.fixture.frontend_runner
        with mock.patch.object(self.module, "run_frontend_command", side_effect=selected_runner):
            return self.module.rehearse_recovery(
                repo_root=self.fixture.repo,
                commit=commit or self.commit,
                output_dir=self.fixture.output_dir,
            )

    def test_plan_and_rehearsal_use_exact_commit_tracked_archive_and_portable_results(self) -> None:
        plan = self.module.build_recovery_plan(self.fixture.repo, self.commit)
        flattened = [item for command in plan for item in command]
        self.assertIn("archive", flattened)
        self.assertIn(self.commit, flattened)
        self.assertEqual(plan[-2][0:2], ["npm", "ci"])
        self.assertEqual(plan[-1], ["npm", "run", "build"])
        assert_portable(self, plan)

        result = self.rehearse()

        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["commit"], self.commit)
        self.assertEqual(result["archive"]["source"], "git_tracked_files_only")
        self.assertGreater(result["archive"]["tracked_file_count"], 0)
        self.assertEqual(result["source_packages"]["restored_file_count"], 2)
        self.assertEqual(result["raw_integrity"]["raw_file_count"], 3)
        self.assertEqual(result["raw_integrity"]["ledger_entry_count"], 3)
        self.assertEqual(result["release"]["snapshot_sha256"], sha256_bytes(self.fixture.snapshot_bytes))
        self.assertEqual(result["pages_parity"]["status"], "PASS")
        self.assertEqual(
            self.fixture.frontend_commands,
            [["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], ["npm", "run", "build"]],
        )
        self.assertTrue(result["cleanup"]["output_dir_removed"])
        self.assertFalse(self.fixture.output_dir.exists())
        assert_portable(self, result)

    def test_rejects_symbolic_or_abbreviated_commit_before_creating_workspace(self) -> None:
        for commit in ("HEAD", self.commit[:12]):
            with self.subTest(commit=commit):
                result = self.rehearse(commit=commit)
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["failure"]["code"], "EXACT_COMMIT_REQUIRED")
                self.assertFalse(self.fixture.output_dir.exists())

    def test_existing_output_directory_is_preserved_and_not_misreported_as_cleanup_failure(self) -> None:
        self.fixture.output_dir.mkdir()
        sentinel = self.fixture.output_dir / "caller-owned.txt"
        sentinel.write_text("preserve\n", encoding="utf-8")

        result = self.rehearse()

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure"]["code"], "OUTPUT_DIR_EXISTS")
        self.assertTrue(sentinel.is_file())
        self.assertFalse(result["cleanup"]["workspace_created"])
        self.assertTrue(result["cleanup"]["preexisting_output_preserved"])

    def test_missing_source_package_fails_closed_and_cleans_workspace(self) -> None:
        package = self.fixture.database / SOURCE_PACKAGE_ROOT / "Memory_Atlas_v1.2_四线14Stage升级_TaskPack.zip.part"
        package.unlink()
        commit = self.fixture.commit_change("remove source package")

        result = self.rehearse(commit=commit)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure"]["code"], "SOURCE_PACKAGE_MISSING")
        self.assertTrue(result["cleanup"]["output_dir_removed"])
        self.assertFalse(self.fixture.output_dir.exists())
        assert_portable(self, result)

    def test_empty_ledger_fails_closed_before_build(self) -> None:
        (self.fixture.database / RAW_LEDGER).write_text("", encoding="utf-8")
        commit = self.fixture.commit_change("empty ledger")

        result = self.rehearse(commit=commit)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure"]["code"], "RAW_LEDGER_EMPTY")
        self.assertEqual(self.fixture.frontend_commands, [])
        self.assertFalse(self.fixture.output_dir.exists())

    def test_release_pointer_must_use_the_canonical_release_id_directory(self) -> None:
        pointer_path = self.fixture.database / CURRENT_RELEASE
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        source_manifest = self.fixture.database / RELEASE_ROOT / "release_manifest.json"
        alias_manifest = self.fixture.database / RELEASE_ROOT / "release_manifest-alias.json"
        alias_manifest.write_bytes(source_manifest.read_bytes())
        run_git(self.fixture.repo, "add", alias_manifest.relative_to(self.fixture.repo).as_posix())
        pointer["release_manifest_path"] = (RELEASE_ROOT / alias_manifest.name).as_posix()
        write_json(pointer_path, pointer)
        commit = self.fixture.commit_change("redirect release pointer")

        result = self.rehearse(commit=commit)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure"]["code"], "RELEASE_MANIFEST_PATH_MISMATCH")
        self.assertEqual(self.fixture.frontend_commands, [])
        self.assertFalse(self.fixture.output_dir.exists())

    def test_pages_snapshot_mismatch_fails_after_build_and_cleans_workspace(self) -> None:
        def mismatching_runner(argv: list[str], *, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
            result = self.fixture.frontend_runner(argv, cwd=cwd, env=env)
            if argv[:2] == ["npm", "run"]:
                (cwd / "dist/memory_atlas.json").write_text('{"mismatch":true}\n', encoding="utf-8")
            return result

        result = self.rehearse(runner=mismatching_runner)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure"]["code"], "PAGES_SNAPSHOT_MISMATCH")
        self.assertFalse(self.fixture.output_dir.exists())
        assert_portable(self, result)

    def test_build_failure_is_bounded_fail_closed_and_cleans_workspace(self) -> None:
        def failing_runner(argv: list[str], *, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
            if argv[:2] == ["npm", "run"]:
                return {
                    "status": "FAIL",
                    "command": list(argv),
                    "returncode": 2,
                    "stdout_tail": "",
                    "stderr_tail": (
                        "x" * (self.module.OUTPUT_TAIL_BYTES * 2)
                        + "\n/private/recovery-work/source.ts: fixture build failed"
                    ),
                }
            return self.fixture.frontend_runner(argv, cwd=cwd, env=env)

        result = self.rehearse(runner=failing_runner)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure"]["code"], "FRONTEND_BUILD_FAILED")
        self.assertLessEqual(len(result["failure"]["stderr_tail"].encode("utf-8")), self.module.OUTPUT_TAIL_BYTES)
        self.assertNotIn("/private/", result["failure"]["stderr_tail"])
        self.assertFalse(self.fixture.output_dir.exists())
        assert_portable(self, result)


if __name__ == "__main__":
    unittest.main()
