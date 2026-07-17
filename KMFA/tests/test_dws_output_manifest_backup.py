import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "automation" / "backup_dws_output_manifest.py"
PROMPT = ROOT / "metadata" / "dws_outputs_backup" / "codex_automation.prompt.md"
MANIFEST_ROOT = ROOT / "metadata" / "dws_outputs_backup"

MODULE_SPEC = importlib.util.spec_from_file_location("backup_dws_output_manifest", SCRIPT)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError("cannot load DWS manifest publisher")
PUBLISHER = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(PUBLISHER)


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def _init_git_main(root: Path) -> tuple[Path, Path]:
    remote = root / "remote.git"
    repo = root / "repo"
    init = _run("git", "init", "--bare", "--initial-branch=main", str(remote), cwd=root)
    if init.returncode != 0:
        raise AssertionError(init.stderr)
    clone = _run("git", "clone", str(remote), str(repo), cwd=root)
    if clone.returncode != 0:
        raise AssertionError(clone.stderr)
    for key, value in (("user.name", "KMFA Test"), ("user.email", "kmfa-test@example.invalid")):
        configured = _run("git", "config", key, value, cwd=repo)
        if configured.returncode != 0:
            raise AssertionError(configured.stderr)
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    committed = _run("git", "add", "README.md", cwd=repo)
    if committed.returncode != 0:
        raise AssertionError(committed.stderr)
    committed = _run("git", "commit", "-m", "fixture", cwd=repo)
    if committed.returncode != 0:
        raise AssertionError(committed.stderr)
    pushed = _run("git", "push", "-u", "origin", "main", cwd=repo)
    if pushed.returncode != 0:
        raise AssertionError(pushed.stderr)
    return repo, remote


def _write_dws_fixture(root: Path, *, validation_ok: bool = True) -> tuple[Path, Path, Path, Path]:
    dws = root / "dws-non-git"
    reports = dws / "reports"
    reports.mkdir(parents=True)
    package = root / "DWS_Outputs.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("DWS_Outputs/example/_manifest/status.md", "ok")
        archive.writestr("DWS_Outputs/example/chat_records/chat_records.csv", "id\n1\n")
    summary = reports / "daily_summary.json"
    summary.write_text(
        json.dumps(
            {
                "run_id": "20260711T190202",
                "automation_name": "每日钉钉DWS归档",
                "run_source": "codex_automation",
                "run_started": "2026-07-11T19:02:03+10:00",
                "run_ended": "2026-07-11T19:03:28+10:00",
                "success": True,
                "group_count": 9,
                "downloads_temp_output_removed": True,
                "missing_total": 102,
                "exhausted_total": 0,
                "mirror_archive_size_bytes": package.stat().st_size,
                "data_archive_size_before": 1000,
                "data_archive_size_after": 1200,
                "cold_archive_root": str(root / "DWS_Archive"),
                "private_group_payload": {"must_not": "be committed"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    validation = reports / "dws_output_validation_latest.json"
    validation.write_text(
        json.dumps(
            {
                "ok": validation_ok,
                "mirror": {
                    "ok": validation_ok,
                    "path": str(package),
                    "file_count": 2,
                    "errors": [] if validation_ok else ["fixture_failure"],
                },
                "cold_storage": {"ok": validation_ok, "errors": [] if validation_ok else ["fixture_failure"]},
                "local_output_root": {"ok": validation_ok, "errors": [] if validation_ok else ["fixture_failure"]},
                "groups": [{"group": "private group", "ok": validation_ok, "errors": []}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return dws, package, summary, validation


class DwsOutputManifestBackupTests(unittest.TestCase):
    def test_non_git_dws_cwd_pushes_manifest_to_main_when_notion_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo, remote = _init_git_main(root)
            dws, package, summary, validation = _write_dws_fixture(root)
            unrelated = repo / "unrelated.tmp"
            unrelated.write_text("preserve\n", encoding="utf-8")

            result = _run(
                "python3",
                str(SCRIPT),
                "--dws-project",
                str(dws),
                "--repo-root",
                str(repo),
                "--source-package",
                str(package),
                "--summary-json",
                str(summary),
                "--validation-json",
                str(validation),
                "--notion-status",
                "pending",
                "--timestamp",
                "2026-07-11T19:04:12+10:00",
                "--push",
                cwd=dws,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PUSHED")
            self.assertTrue(payload["committed"])
            self.assertTrue(payload["pushed"])
            self.assertEqual(payload["notion_status"], "pending")
            self.assertTrue(unrelated.exists())
            self.assertEqual(_run("git", "status", "--short", "--", "unrelated.tmp", cwd=repo).stdout.strip(), "?? unrelated.tmp")

            checkout = root / "checkout"
            cloned = _run("git", "clone", "--branch", "main", str(remote), str(checkout), cwd=root)
            self.assertEqual(cloned.returncode, 0, cloned.stderr)
            latest = json.loads(
                (checkout / "KMFA" / "metadata" / "dws_outputs_backup" / "latest" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            run_manifest = checkout / "KMFA" / "metadata" / "dws_outputs_backup" / "runs" / "20260711T190202.json"
            self.assertTrue(run_manifest.is_file())
            self.assertEqual(latest["schema_version"], "kmfa.dws_outputs_backup.public_safe.v2")
            self.assertEqual(latest["record_type"], "dws_outputs_backup_public_summary")
            self.assertEqual(latest["backup_type"], "metadata_only")
            self.assertEqual(latest["source_package_ref"], "SOURCE-PACKAGE-DWS-PRIVATE")
            self.assertEqual(latest["local_resource_ref"], "LOCAL-RESOURCE-DWS-PRIVATE")
            self.assertTrue(latest["private_receipt_required"])
            self.assertFalse(latest["raw_resource_committed"])
            self.assertEqual(latest["run_status"]["run_id"], "20260711T190202")
            self.assertEqual(latest["notion_sync"]["status"], "pending")
            self.assertFalse(latest["notion_sync"]["blocks_manifest_backup"])
            self.assertEqual(latest["validation_status"]["group_checks"], "pass")
            public_payload = json.dumps(latest, ensure_ascii=False)
            self.assertNotIn(str(root), public_payload)
            self.assertNotIn(str(package), public_payload)
            self.assertNotIn(package.name, public_payload)
            self.assertNotIn(hashlib.sha256(package.read_bytes()).hexdigest(), public_payload)
            self.assertNotIn("private group", public_payload)
            self.assertNotIn("private_group_payload", public_payload)
            self.assertNotIn("must_not", public_payload)
            self.assertFalse(any(path.suffix == ".zip" for path in checkout.rglob("*.zip")))
            commit_subject = _run("git", "log", "-1", "--pretty=%s", cwd=checkout).stdout.strip()
            self.assertEqual(commit_subject, "KMFA metadata: backup DWS output manifest 2026-07-11 1904")

    def test_failed_structure_validation_blocks_manifest_write_and_push(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo, remote = _init_git_main(root)
            dws, package, summary, validation = _write_dws_fixture(root, validation_ok=False)
            before = _run("git", "rev-parse", "refs/heads/main", cwd=remote).stdout.strip()

            result = _run(
                "python3",
                str(SCRIPT),
                "--dws-project",
                str(dws),
                "--repo-root",
                str(repo),
                "--source-package",
                str(package),
                "--summary-json",
                str(summary),
                "--validation-json",
                str(validation),
                "--notion-status",
                "pending",
                "--push",
                cwd=dws,
            )

            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "VALIDATION_FAILED")
            self.assertNotIn(str(root), result.stdout + result.stderr)
            self.assertFalse((repo / "KMFA" / "metadata" / "dws_outputs_backup").exists())
            after = _run("git", "rev-parse", "refs/heads/main", cwd=remote).stdout.strip()
            self.assertEqual(after, before)

    def test_default_timestamp_uses_run_end_and_retry_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo, remote = _init_git_main(root)
            dws, package, summary, validation = _write_dws_fixture(root)
            command = (
                "python3",
                str(SCRIPT),
                "--dws-project",
                str(dws),
                "--repo-root",
                str(repo),
                "--source-package",
                str(package),
                "--summary-json",
                str(summary),
                "--validation-json",
                str(validation),
                "--notion-status",
                "pending",
                "--push",
            )

            first = _run(*command, cwd=dws)
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            first_payload = json.loads(first.stdout)
            self.assertTrue(first_payload["committed"])
            first_head = _run("git", "rev-parse", "refs/heads/main", cwd=remote).stdout.strip()

            second = _run(*command, cwd=dws)
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            second_payload = json.loads(second.stdout)
            self.assertFalse(second_payload["committed"])
            second_head = _run("git", "rev-parse", "refs/heads/main", cwd=remote).stdout.strip()
            self.assertEqual(second_head, first_head)
            self.assertEqual(
                _run("git", "log", "-1", "--pretty=%s", cwd=repo).stdout.strip(),
                "KMFA metadata: backup DWS output manifest 2026-07-11 1903",
            )

    def test_tracked_prompt_makes_notion_non_blocking_and_preserves_schedule_ownership(self) -> None:
        self.assertTrue(PROMPT.is_file())
        prompt = PROMPT.read_text(encoding="utf-8")

        self.assertIn("Notion pending must not block the GitHub manifest-only backup", prompt)
        self.assertIn("backup_dws_output_manifest.py", prompt)
        self.assertIn("--repo-root \"${CODEXPROJECT_REPO_ROOT}\"", prompt)
        self.assertIn("--source-package \"${DWS_SOURCE_PACKAGE}\"", prompt)
        self.assertIn("Do not change the automation RRULE or schedule", prompt)
        self.assertNotIn("Only after archive, validation, and sync goals are complete", prompt)
        self.assertNotIn("/Users/", prompt)

    def test_public_schema_rejects_absolute_paths_private_hashes_and_group_names(self) -> None:
        summary = {
            "run_id": "20260711T190202",
            "run_started": "2026-07-11T19:02:03+10:00",
            "run_ended": "2026-07-11T19:03:28+10:00",
            "success": True,
            "group_count": 9,
        }
        baseline = PUBLISHER.build_manifest(summary, "pending", summary["run_ended"])

        mutations = []
        absolute_path = copy.deepcopy(baseline)
        absolute_path["local_resource_ref"] = "/private/runtime/dws"
        mutations.append(absolute_path)
        private_hash = copy.deepcopy(baseline)
        private_hash["source_package_ref"] = "a" * 64
        mutations.append(private_hash)
        group_names = copy.deepcopy(baseline)
        group_names["run_status"]["groups"] = ["synthetic-private-group"]
        mutations.append(group_names)

        for manifest in mutations:
            with self.subTest(manifest=manifest):
                with self.assertRaises(PUBLISHER.BackupError) as raised:
                    PUBLISHER.validate_public_manifest(manifest)
                self.assertEqual(raised.exception.status, "PUBLIC_SAFETY_BLOCKED")

    def test_all_tracked_dws_manifests_conform_to_public_safe_v2(self) -> None:
        paths = [MANIFEST_ROOT / "latest" / "manifest.json", *sorted((MANIFEST_ROOT / "runs").glob("*.json"))]
        self.assertEqual(len(paths), 5)
        for path in paths:
            with self.subTest(path=path):
                manifest = json.loads(path.read_text(encoding="utf-8"))
                PUBLISHER.validate_public_manifest(manifest)
                payload = json.dumps(manifest, ensure_ascii=False)
                self.assertNotRegex(payload, r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
                self.assertNotIn("group_names", payload)
                self.assertNotIn("groups", manifest.get("run_status", {}))


if __name__ == "__main__":
    unittest.main()
