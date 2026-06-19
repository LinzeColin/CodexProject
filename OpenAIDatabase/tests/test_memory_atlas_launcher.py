from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install_memory_atlas_app.py"


class MemoryAtlasLauncherTests(unittest.TestCase):
    def test_installer_creates_macos_app_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "Memory Atlas.app"
            subprocess.run(
                [
                    sys.executable,
                    str(INSTALLER),
                    "--repo-root",
                    str(REPO_ROOT),
                    "--target",
                    str(target),
                    "--skip-runtime",
                ],
                check=True,
                text=True,
                capture_output=True,
            )

            info_plist = target / "Contents" / "Info.plist"
            executable = target / "Contents" / "MacOS" / "memory-atlas-launcher"
            icon = target / "Contents" / "Resources" / "MemoryAtlas.icns"

            self.assertTrue(info_plist.exists())
            self.assertTrue(executable.exists())
            self.assertTrue(os.access(executable, os.X_OK))
            icon_expected = shutil.which("iconutil") is not None
            try:
                import PIL  # noqa: F401
            except Exception:
                icon_expected = False
            if icon_expected:
                self.assertTrue(icon.exists())
                self.assertGreater(icon.stat().st_size, 1024)

            with info_plist.open("rb") as handle:
                plist = plistlib.load(handle)

            self.assertEqual(plist["CFBundleName"], "Memory Atlas")
            self.assertEqual(plist["CFBundleExecutable"], "memory-atlas-launcher")
            if icon_expected:
                self.assertEqual(plist["CFBundleIconFile"], "MemoryAtlas")
            self.assertEqual(plist["CFBundlePackageType"], "APPL")
            self.assertIn("Documents", plist["NSDocumentsFolderUsageDescription"])

            launcher_text = executable.read_text(encoding="utf-8")
            self.assertIn(str(REPO_ROOT), launcher_text)
            self.assertIn("scripts/build_memory_atlas_data.py", launcher_text)
            self.assertIn("隐私与安全性 > 文件和文件夹", launcher_text)
            self.assertIn("on run argv", launcher_text)
            self.assertIn("display notification", launcher_text)
            self.assertIn("Application Support/OpenAIDatabase/MemoryAtlas", launcher_text)
            self.assertIn("launching.html", launcher_text)
            self.assertIn("记忆星图启动中", launcher_text)
            self.assertIn('open "$STATUS_FILE"', launcher_text)
            self.assertNotIn('open "$URL"', launcher_text)
            self.assertIn("Status page will redirect to the ready app.", launcher_text)
            self.assertIn('npm ci --prefix "$APP_DIR"', launcher_text)
            self.assertIn('--cache "$npm_cache"', launcher_text)
            self.assertIn('rm -rf "$npm_cache"', launcher_text)
            self.assertIn('(cd "$APP_DIR" && npm run build -- --emptyOutDir)', launcher_text)
            self.assertNotIn('npm run build --prefix "$APP_DIR"', launcher_text)
            self.assertNotIn('node "$APP_DIR/node_modules/typescript/bin/tsc" -b', launcher_text)
            self.assertIn("scripts/audit_memory_atlas_release.py", launcher_text)
            self.assertIn("scripts/audit_memory_atlas_acceptance.py", launcher_text)
            self.assertLess(
                launcher_text.index('mv "$staged_runtime" "$RUNTIME_DIR"'),
                launcher_text.index('--publish-dir "$RUNTIME_DIR"'),
            )
            self.assertNotIn('Memory Atlas 验收审计失败，请查看日志：$LOG_FILE。"\n    exit 1\n  fi\n  stop_managed_server', launcher_text)
            self.assertIn("memory_atlas_server.py", launcher_text)
            self.assertIn("__memory_atlas_runtime_state", launcher_text)
            self.assertIn("__memory_atlas_heartbeat", launcher_text)
            self.assertIn("__memory_atlas_release", launcher_text)
            self.assertIn("/memory_atlas.json", launcher_text)
            self.assertIn("MEMORY_ATLAS_TTL_SECONDS", launcher_text)
            self.assertIn("MEMORY_ATLAS_IDLE_SECONDS", launcher_text)
            self.assertIn("server.pid", launcher_text)
            self.assertIn("is_managed_server", launcher_text)
            self.assertIn("stop_port_managed_server", launcher_text)
            self.assertNotIn("schedule_auto_shutdown", launcher_text)
            self.assertIn('rm -rf "$APP_DIR/node_modules"', launcher_text)
            self.assertTrue((target / "Contents" / "PkgInfo").exists())


if __name__ == "__main__":
    unittest.main()
