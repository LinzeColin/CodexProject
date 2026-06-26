from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from source_registry.web_search import collect_search_results


class WebSearchTest(unittest.TestCase):
    def test_missing_provider_key_is_safe_status(self) -> None:
        old_values = {
            name: os.environ.pop(name, None)
            for name in (
                "SERPAPI_API_KEY",
                "SERPAPI_KEY",
                "BING_SEARCH_API_KEY",
                "AZURE_BING_SEARCH_KEY",
                "GOOGLE_SEARCH_API_KEY",
                "GOOGLE_API_KEY",
                "GOOGLE_CSE_ID",
            )
        }
        try:
            results, status = collect_search_results(
                provider="serpapi",
                query="人工智能 政策解读",
                max_results=5,
                timeout=1,
            )
            self.assertEqual(results, [])
            self.assertEqual(status, "missing_api_key:serpapi")
        finally:
            for name, value in old_values.items():
                if value is not None:
                    os.environ[name] = value

    def test_json_secret_file_is_read_after_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret_path = Path(tmp) / "search-secrets.json"
            secret_path.write_text('{"GOOGLE_SEARCH_API_KEY":"key-from-file"}', encoding="utf-8")
            old_key = os.environ.pop("GOOGLE_SEARCH_API_KEY", None)
            old_google_key = os.environ.pop("GOOGLE_API_KEY", None)
            old_engine = os.environ.pop("GOOGLE_CSE_ID", None)
            try:
                results, status = collect_search_results(
                    provider="google",
                    query="半导体 政策解读",
                    max_results=5,
                    timeout=1,
                    secrets_file=secret_path,
                )
                self.assertEqual(results, [])
                self.assertEqual(status, "missing_google_cse_id")
            finally:
                if old_key is not None:
                    os.environ["GOOGLE_SEARCH_API_KEY"] = old_key
                if old_google_key is not None:
                    os.environ["GOOGLE_API_KEY"] = old_google_key
                if old_engine is not None:
                    os.environ["GOOGLE_CSE_ID"] = old_engine


if __name__ == "__main__":
    unittest.main()
