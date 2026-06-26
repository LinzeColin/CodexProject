from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.config_setup import build_config_setup, write_config_setup


class ConfigSetupTest(unittest.TestCase):
    def test_build_config_setup_uses_safe_paths_and_empty_templates(self) -> None:
        setup = build_config_setup(secure_dir="/tmp/policy-safe")
        self.assertEqual(setup["env_exports"]["SEARCH_SECRETS_FILE"], "/tmp/policy-safe/policy-search-secrets.json")
        self.assertIn("SERPAPI_API_KEY", setup["search_template"])
        self.assertEqual(setup["search_template"]["SERPAPI_API_KEY"], "")
        self.assertIn("bilibili", setup["platform_auth_template"]["platforms"])
        self.assertIn("search_api_bundle_example_path", setup)
        self.assertIn("platform_auth_bundle_example_path", setup)
        self.assertEqual(setup["search_api_bundle_template"]["bing"]["api_key"], "")
        self.assertIn("chrome_profile_dir", setup["platform_auth_bundle_template"]["platforms"]["bilibili"])
        weibo = setup["platform_auth_template"]["platforms"]["weibo"]
        self.assertEqual(weibo["validation_url"], "https://weibo.com/")
        self.assertIn("首页", weibo["success_markers"])
        self.assertIn("验证码", weibo["captcha_markers"])
        bilibili = setup["platform_auth_template"]["platforms"]["bilibili"]
        self.assertEqual(bilibili["allowed_capabilities"], ["video_detail", "public_subtitle"])
        self.assertNotIn("validation_url", bilibili)
        encoded = json.dumps(setup, ensure_ascii=False)
        self.assertNotIn("password", encoded.lower())

    def test_write_config_setup_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "secure"
            setup = write_config_setup(secure_dir=root, dry_run=True)
            self.assertFalse(Path(setup["search_secrets_path"]).exists())
            self.assertFalse(Path(setup["platform_auth_path"]).exists())
            self.assertEqual(setup["writes"][0]["action"], "create")

    def test_write_config_setup_creates_private_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "secure"
            setup = write_config_setup(secure_dir=root)
            search_path = Path(setup["search_secrets_path"])
            auth_path = Path(setup["platform_auth_path"])
            search_bundle = Path(setup["search_api_bundle_example_path"])
            platform_bundle = Path(setup["platform_auth_bundle_example_path"])
            self.assertTrue(search_path.exists())
            self.assertTrue(auth_path.exists())
            self.assertTrue(search_bundle.exists())
            self.assertTrue(platform_bundle.exists())
            self.assertEqual(json.loads(search_path.read_text(encoding="utf-8"))["BING_SEARCH_API_KEY"], "")
            self.assertIn("platforms", json.loads(auth_path.read_text(encoding="utf-8")))
            self.assertIn("bing", json.loads(search_bundle.read_text(encoding="utf-8")))
            self.assertIn("bilibili", json.loads(platform_bundle.read_text(encoding="utf-8"))["platforms"])
            self.assertFalse((root / "cookies" / "bilibili_cookie.txt").exists())

    def test_cli_setup_config_outputs_public_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "secure"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(Path(tmp) / "source_registry.sqlite"),
                        "setup-config",
                        "--secure-dir",
                        str(root),
                        "--dry-run",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertTrue(payload["dry_run"])
            self.assertIn("SEARCH_SECRETS_FILE", payload["env_exports"])
            self.assertIn("search_api_bundle_example_path", payload)
            self.assertIn("platform_auth_bundle_example_path", payload)
            self.assertNotIn("search_template", payload)
            self.assertNotIn("search_api_bundle_template", payload)
            self.assertNotIn("platform_auth_bundle_template", payload)


if __name__ == "__main__":
    unittest.main()
