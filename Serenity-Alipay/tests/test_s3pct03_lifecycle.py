from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import app.core.moomoo_lifecycle as moomoo_lifecycle
import app.core.packaging as packaging
from app.core.moomoo_lifecycle import OpenDLifecycle, ProcessInfo, cleanup_started_processes, ensure_opend
from app.core.moomoo_smoke import SocketProbe, WorkbenchProbe
from app.core.packaging import build_delivery_package
from tests.helpers import temp_settings


class SerenityS3PCT03LifecycleTests(unittest.TestCase):
    def _settings(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return temp_settings(Path(temp_dir.name))

    def test_opend_auto_wake_records_tool_owned_process_and_cleans_it(self) -> None:
        settings = self._settings()
        app_path = "/Applications/MoomooOpenD/moomoo_OpenD.app"
        started_process = ProcessInfo(
            pid="200",
            command="/Applications/MoomooOpenD/moomoo_OpenD.app/Contents/MacOS/moomoo_OpenD",
        )
        snapshots = [[], [started_process], []]
        commands: list[list[str]] = []

        def fake_snapshot() -> list[ProcessInfo]:
            if snapshots:
                return snapshots.pop(0)
            return []

        def fake_run(command, **kwargs):
            commands.append(list(command))
            return SimpleNamespace(stdout="", returncode=0)

        workbench = WorkbenchProbe(
            path="/Applications/MoomooOpenD",
            exists=True,
            start_script=None,
            check_script=None,
            quote_script=None,
            config_path=None,
            sdk_vendor_path=None,
            opend_vendor_path=None,
            moomoo_opend_app_path=app_path,
        )

        with (
            patch.object(moomoo_lifecycle, "process_snapshot", side_effect=fake_snapshot),
            patch.object(
                moomoo_lifecycle,
                "probe_socket",
                return_value=SocketProbe("127.0.0.1", 11111, False, "closed"),
            ),
            patch.object(moomoo_lifecycle, "_wait_for_socket", return_value=True),
            patch.object(moomoo_lifecycle, "discover_workbenches", return_value=[workbench]),
            patch.object(moomoo_lifecycle.subprocess, "run", side_effect=fake_run),
        ):
            lifecycle = ensure_opend(
                settings,
                auto_start=True,
                cleanup_if_started=True,
                wait_seconds=0.1,
                include_user_codex=False,
            )
            cleanup = cleanup_started_processes(lifecycle)

        self.assertTrue(lifecycle.start_attempted)
        self.assertTrue(lifecycle.started_by_tool)
        self.assertTrue(lifecycle.socket_is_reachable)
        self.assertEqual(lifecycle.started_processes, [started_process])
        self.assertEqual(commands, [["open", app_path], ["kill", "-TERM", "200"]])
        self.assertTrue(cleanup["cleanup_attempted"])
        self.assertEqual(cleanup["cleanup_result"], "terminated_started_processes:200")
        self.assertEqual(cleanup["after_processes"], [])

    def test_cleanup_contract_never_kills_user_owned_opend(self) -> None:
        existing_process = ProcessInfo(
            pid="300",
            command="/Applications/MoomooOpenD/moomoo_OpenD.app/Contents/MacOS/moomoo_OpenD",
        )
        lifecycle = OpenDLifecycle(
            socket_was_reachable=True,
            socket_is_reachable=True,
            auto_start_requested=True,
            start_attempted=False,
            started_by_tool=False,
            start_command=None,
            cleanup_requested=True,
            cleanup_attempted=False,
            cleanup_result=None,
            before_processes=[existing_process],
            after_processes=[existing_process],
            started_processes=[],
            detail="existing user-owned OpenD stayed outside tool ownership",
        )

        with (
            patch.object(moomoo_lifecycle, "process_snapshot", return_value=[existing_process]),
            patch.object(moomoo_lifecycle.subprocess, "run") as run_mock,
        ):
            result = cleanup_started_processes(lifecycle)

        self.assertFalse(result["cleanup_attempted"])
        self.assertEqual(result["cleanup_result"], "not_started_by_tool")
        run_mock.assert_not_called()

    def test_delivery_package_atomic_failure_preserves_previous_zip_and_removes_tmp(self) -> None:
        settings = self._settings()
        (settings.root_dir / "README.md").write_text("readme", encoding="utf-8")
        zip_path = settings.root_dir / "outputs" / "package" / "serenity_daily_analysis_delivery.zip"
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        real_zipfile = zipfile.ZipFile
        with real_zipfile(zip_path, "w") as archive:
            archive.writestr("previous.txt", "still valid")

        class FailingZipFile:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("zip writer failed")

        with patch.object(packaging.zipfile, "ZipFile", FailingZipFile):
            with self.assertRaisesRegex(RuntimeError, "zip writer failed"):
                build_delivery_package(settings)

        with real_zipfile(zip_path) as archive:
            self.assertEqual(archive.read("previous.txt"), b"still valid")
        self.assertEqual(list(zip_path.parent.glob("*.tmp")), [])
        self.assertEqual(list(zip_path.parent.glob(".*.tmp")), [])

    def test_launchd_tick_contract_keeps_wrapper_non_destructive(self) -> None:
        script = (Path(__file__).resolve().parents[1] / "scripts" / "serenity_launchd_tick.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('export SERENITY_OPEND_WAIT_SECONDS="${SERENITY_OPEND_WAIT_SECONDS:-75}"', script)
        self.assertIn("-m app.cli automation-tick --no-dry-run --send-mail --local --json", script)
        self.assertIn("STATUS=$?", script)
        self.assertIn("launchd tick exit_status=$STATUS", script)
        self.assertIn("exit 0", script)


if __name__ == "__main__":
    unittest.main()
