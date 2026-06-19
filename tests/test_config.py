import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from quantlab.config import get_env_value, read_env_file


class ConfigTests(unittest.TestCase):
    def test_read_env_file_parses_simple_key_values(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "\n".join(
                    [
                        "# comment",
                        "TUSHARE_TOKEN=test-token",
                        "ALPHA_VANTAGE_API_KEY='alpha-key'",
                        'POLYGON_API_KEY="polygon-key"',
                    ]
                ),
                encoding="utf-8",
            )

            values = read_env_file(path)

            self.assertEqual(values["TUSHARE_TOKEN"], "test-token")
            self.assertEqual(values["ALPHA_VANTAGE_API_KEY"], "alpha-key")
            self.assertEqual(values["POLYGON_API_KEY"], "polygon-key")

    def test_get_env_value_prefers_exported_environment_over_env_file(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("POLYGON_API_KEY=file-key\n", encoding="utf-8")
            old_key = os.environ.get("POLYGON_API_KEY")
            old_env_file = os.environ.get("QUANTLAB_ENV_FILE")
            os.environ["POLYGON_API_KEY"] = "exported-key"
            os.environ["QUANTLAB_ENV_FILE"] = str(path)
            try:
                self.assertEqual(get_env_value("POLYGON_API_KEY"), "exported-key")
            finally:
                if old_key is None:
                    os.environ.pop("POLYGON_API_KEY", None)
                else:
                    os.environ["POLYGON_API_KEY"] = old_key
                if old_env_file is None:
                    os.environ.pop("QUANTLAB_ENV_FILE", None)
                else:
                    os.environ["QUANTLAB_ENV_FILE"] = old_env_file

    def test_get_env_value_reads_configured_env_file(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("TUSHARE_TOKEN=file-token\n", encoding="utf-8")
            old_key = os.environ.pop("TUSHARE_TOKEN", None)
            old_env_file = os.environ.get("QUANTLAB_ENV_FILE")
            os.environ["QUANTLAB_ENV_FILE"] = str(path)
            try:
                self.assertEqual(get_env_value("TUSHARE_TOKEN"), "file-token")
            finally:
                if old_key is not None:
                    os.environ["TUSHARE_TOKEN"] = old_key
                if old_env_file is None:
                    os.environ.pop("QUANTLAB_ENV_FILE", None)
                else:
                    os.environ["QUANTLAB_ENV_FILE"] = old_env_file


if __name__ == "__main__":
    unittest.main()
