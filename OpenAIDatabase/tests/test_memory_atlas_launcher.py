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
            app_support = Path(temp_dir) / "app-support"
            env = os.environ.copy()
            env["MEMORY_ATLAS_APP_SUPPORT_ROOT"] = str(app_support)
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
                env=env,
            )

            info_plist = target / "Contents" / "Info.plist"
            executable = target / "Contents" / "MacOS" / "memory-atlas-launcher"
            icon = target / "Contents" / "Resources" / "MemoryAtlas.icns"
            source_workspace = app_support / "source"

            self.assertTrue(info_plist.exists())
            self.assertTrue(executable.exists())
            self.assertTrue(os.access(executable, os.X_OK))
            self.assertTrue(source_workspace.exists())
            self.assertTrue((source_workspace / "apps/memory-atlas/package.json").exists())
            self.assertTrue((source_workspace / "scripts/sync_codex_memory_data.py").exists())
            self.assertTrue((source_workspace / "memory_atlas_source_workspace.json").exists())
            self.assertFalse((source_workspace / ".git").exists())
            self.assertFalse((source_workspace / ".local_keys").exists())
            self.assertFalse((source_workspace / "apps/memory-atlas/node_modules").exists())
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
            self.assertIn("Application Support", plist["NSDocumentsFolderUsageDescription"])

            launcher_text = executable.read_text(encoding="utf-8")
            self.assertIn(str(REPO_ROOT), launcher_text)
            self.assertIn(str(source_workspace), launcher_text)
            self.assertIn("ORIGINAL_REPO_ROOT", launcher_text)
            self.assertIn("INSTALLED_GIT_COMMIT", launcher_text)
            self.assertIn("scripts/sync_codex_memory_data.py", launcher_text)
            self.assertIn("--build-atlas", launcher_text)
            self.assertIn("refresh_latest_snapshot", launcher_text)
            self.assertIn("copy_latest_snapshot_to_runtime", launcher_text)
            self.assertIn("snapshot_generated_at", launcher_text)
            self.assertIn("正在刷新最新脱敏数据快照", launcher_text)
            self.assertIn("重新安装运行副本", launcher_text)
            self.assertNotIn("隐私与安全性 > 文件和文件夹", launcher_text)
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
            prepare_block = launcher_text[
                launcher_text.index("prepare_runtime()") : launcher_text.index('echo "=== $(date')
            ]
            self.assertLess(
                prepare_block.index('mv "$staged_runtime" "$RUNTIME_DIR"'),
                prepare_block.index('--publish-dir "$RUNTIME_DIR"'),
            )
            self.assertNotIn('Memory Atlas 验收审计失败，请查看日志：$LOG_FILE。"\n    exit 1\n  fi\n  stop_managed_server', launcher_text)
            self.assertIn("memory_atlas_server.py", launcher_text)
            self.assertIn("__memory_atlas_runtime_state", launcher_text)
            self.assertIn("__memory_atlas_heartbeat", launcher_text)
            self.assertIn("__memory_atlas_release", launcher_text)
            self.assertIn("request_shutdown", launcher_text)
            self.assertIn("release_requested", launcher_text)
            self.assertIn("active_thread_count", launcher_text)
            self.assertIn("allow_reuse_address = True", launcher_text)
            self.assertIn("window.addEventListener(\"beforeunload\"", (REPO_ROOT / "apps/memory-atlas/src/App.tsx").read_text(encoding="utf-8"))
            self.assertIn("/memory_atlas.json", launcher_text)
            self.assertIn("MEMORY_ATLAS_TTL_SECONDS", launcher_text)
            self.assertIn("MEMORY_ATLAS_IDLE_SECONDS", launcher_text)
            self.assertIn("server.pid", launcher_text)
            self.assertIn("is_managed_server", launcher_text)
            self.assertIn('"-m http.server"', launcher_text)
            self.assertIn("stop_port_managed_server", launcher_text)
            self.assertNotIn("last_seen_at = time.time() - max", launcher_text)
            self.assertNotIn("schedule_auto_shutdown", launcher_text)
            self.assertIn('rm -rf "$APP_DIR/node_modules"', launcher_text)
            self.assertTrue((target / "Contents" / "PkgInfo").exists())


if __name__ == "__main__":
    unittest.main()
