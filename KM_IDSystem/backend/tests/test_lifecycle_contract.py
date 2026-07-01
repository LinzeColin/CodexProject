import importlib
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


class OpMeLifecycleContractTests(unittest.TestCase):
    def test_shell_scripts_are_lf_and_parse_under_bash(self) -> None:
        scripts = [
            PROJECT_ROOT / "scripts" / "run_local_services.sh",
            PROJECT_ROOT / "scripts" / "stop_local_services.sh",
            PROJECT_ROOT / "scripts" / "smoke_test.sh",
            PROJECT_ROOT / "scripts" / "dev.sh",
        ]
        for script in scripts:
            with self.subTest(script=str(script.relative_to(PROJECT_ROOT))):
                data = script.read_bytes()
                self.assertNotIn(b"\r\n", data)
                bash_path = str(script.relative_to(PROJECT_ROOT)).replace("\\", "/")
                result = subprocess.run(
                    ["bash", "-n", bash_path],
                    cwd=PROJECT_ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_runtime_entrypoints_fail_fast_instead_of_installing_dependencies(self) -> None:
        scripts = [
            PROJECT_ROOT / "scripts" / "run_local_services.sh",
            PROJECT_ROOT / "scripts" / "dev.sh",
            PROJECT_ROOT / "scripts" / "smoke_test.sh",
        ]
        for path in scripts:
            with self.subTest(script=str(path.relative_to(PROJECT_ROOT))):
                script = path.read_text(encoding="utf-8")
                install_lines = [
                    line.strip()
                    for line in script.splitlines()
                    if "pip install" in line or "npm install" in line
                ]

                self.assertTrue(install_lines)
                self.assertTrue(
                    all(line.startswith("fail ") or line.startswith("echo ") for line in install_lines),
                    install_lines,
                )
                self.assertIn("依赖未安装", script)
                self.assertIn("python3 -m venv .venv", script)
                self.assertIn("npm install", script)

    def test_stop_script_removes_stale_pid_files_without_touching_user_data(self) -> None:
        stop_script = (PROJECT_ROOT / "scripts" / "stop_local_services.sh").read_text(encoding="utf-8")
        self.assertIn("pid_cwd()", stop_script)
        self.assertIn('stop_pid_file frontend "npm"', stop_script)

        tmp_parent = PROJECT_ROOT / "tmp"
        tmp_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_parent) as tmp:
            data_dir = Path(tmp)
            (data_dir / "backend.pid").write_text("999999\n", encoding="utf-8")
            (data_dir / "frontend.pid").write_text("not-a-pid\n", encoding="utf-8")
            data_dir_for_bash = data_dir.relative_to(PROJECT_ROOT).as_posix()

            result = subprocess.run(
                ["bash", "-c", f"OPME_DATA_DIR={shlex.quote(data_dir_for_bash)} scripts/stop_local_services.sh"],
                cwd=PROJECT_ROOT,
                env=os.environ.copy(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertFalse((data_dir / "backend.pid").exists())
            self.assertFalse((data_dir / "frontend.pid").exists())

    def test_sqlite_persistence_can_recover_from_temp_runtime_directory(self) -> None:
        if str(BACKEND_ROOT) not in sys.path:
            sys.path.insert(0, str(BACKEND_ROOT))
        from app.core import config
        from app.services import db

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = tmp_path / "data"
            report_dir = tmp_path / "reports"
            database_path = data_dir / "opme-test.sqlite"

            with (
                patch.object(config, "DATA_DIR", data_dir),
                patch.object(config, "REPORT_DIR", report_dir),
                patch.object(config, "DATABASE_PATH", database_path),
                patch.object(db, "DATABASE_PATH", database_path),
            ):
                config.ensure_runtime_dirs()
                db.init_db()
                case_id = db.create_case(
                    "gear",
                    "生命周期恢复测试",
                    {"wear_depth": 1.6},
                    None,
                    {"risk_level": "warning", "risk_score": 42},
                )

                recovered = db.get_case(case_id)
                dashboard = db.dashboard_summary()
                database_exists = database_path.exists()

        self.assertEqual(recovered["title"], "生命周期恢复测试")
        self.assertEqual(recovered["result"]["risk_score"], 42)
        self.assertGreaterEqual(dashboard["total_cases"], 1)
        self.assertTrue(database_exists)
        self.assertFalse((PROJECT_ROOT / "data" / "opme-test.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
