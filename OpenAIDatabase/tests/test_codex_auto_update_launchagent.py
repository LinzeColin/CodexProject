import importlib.util
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install_codex_weekly_sync.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("install_codex_weekly_sync", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CodexAutoUpdateLaunchAgentTests(unittest.TestCase):
    def test_launchagent_runs_monday_and_friday_at_0300(self) -> None:
        module = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            plist_path = Path(temp_dir) / "com.linze.openai-database.codex-daily-sync.plist"

            result = module.install_agent(ROOT, plist_path, load=False)

            with plist_path.open("rb") as handle:
                plist = plistlib.load(handle)
            self.assertEqual(plist["Label"], "com.linze.openai-database.codex-daily-sync")
            self.assertEqual(
                plist["StartCalendarInterval"],
                [{"Hour": 3, "Minute": 0, "Weekday": 1}, {"Hour": 3, "Minute": 0, "Weekday": 5}],
            )
            self.assertIn("run_codex_memory_auto_update.py", plist["ProgramArguments"][1])
            self.assertIn("--publish-runtime", plist["ProgramArguments"])
            self.assertEqual(result["schedule"], "每周一和周五 03:00 本地时间")

    def test_non_git_runtime_source_omits_commit_and_push(self) -> None:
        module = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "run_codex_memory_auto_update.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            plist_path = repo_root / "agent.plist"

            result = module.install_agent(repo_root, plist_path, load=False)

            with plist_path.open("rb") as handle:
                plist = plistlib.load(handle)
            self.assertNotIn("--commit", plist["ProgramArguments"])
            self.assertNotIn("--push", plist["ProgramArguments"])
            self.assertFalse(result["git_backup"]["enabled"])


if __name__ == "__main__":
    unittest.main()
