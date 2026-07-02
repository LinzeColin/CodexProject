from pathlib import Path
import unittest

from KMFA.tools.check_v013_s00_app_entry import APP_PATH, MANIFEST_PATH, PROJECT_ROOT, validate_app_entry


class TestV013S00AppEntry(unittest.TestCase):
    def test_downloads_app_entry_is_bound_to_canonical_kmfa(self) -> None:
        result = validate_app_entry(APP_PATH, PROJECT_ROOT, MANIFEST_PATH)
        self.assertEqual(result["app_path"], "/Users/linzezhang/Downloads/KMFA.app")
        self.assertIn("kmfa_home_navigation.html", result["target_html"])
        self.assertTrue(result["icon_sha256"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
