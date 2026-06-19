from __future__ import annotations

import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.search_secret_import import import_search_secret, import_search_secret_bundle
from source_registry.web_search import search_provider_status


class SearchSecretImportTest(unittest.TestCase):
    def test_import_bing_key_writes_private_json_without_exposing_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "bing_key.txt"
            source.write_text("bing-secret-value-123", encoding="utf-8")
            target = root / "policy-search-secrets.json"
            result = import_search_secret("bing", value_file=source, search_secrets_file=target)
            payload = json.loads(target.read_text(encoding="utf-8"))
            status = next(item for item in search_provider_status(target) if item["provider"] == "bing")

            encoded = json.dumps(result, ensure_ascii=False)
            self.assertEqual(result["status"], "imported")
            self.assertEqual(payload["BING_SEARCH_API_KEY"], "bing-secret-value-123")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
            self.assertTrue(status["ready"])
            self.assertNotIn("bing-secret-value-123", encoded)
            self.assertNotIn(str(source), encoded)
            self.assertNotIn(str(target), encoded)

    def test_google_requires_engine_id_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = root / "google_key.txt"
            key.write_text("google-secret-value-123", encoding="utf-8")
            with self.assertRaises(ValueError):
                import_search_secret("google", value_file=key, search_secrets_file=root / "secrets.json")

    def test_google_imports_key_and_engine_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = root / "google_key.txt"
            cse = root / "google_cse.txt"
            target = root / "secrets.json"
            key.write_text("google-secret-value-123", encoding="utf-8")
            cse.write_text("google-cse-id-123", encoding="utf-8")
            result = import_search_secret("google", value_file=key, engine_id_file=cse, search_secrets_file=target)
            payload = json.loads(target.read_text(encoding="utf-8"))
        self.assertTrue(result["provider_ready_after_import"])
        self.assertEqual(payload["GOOGLE_SEARCH_API_KEY"], "google-secret-value-123")
        self.assertEqual(payload["GOOGLE_CSE_ID"], "google-cse-id-123")

    def test_import_from_environment_without_printing_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("POLICY_TEST_SERPAPI_KEY")
            os.environ["POLICY_TEST_SERPAPI_KEY"] = "serpapi-secret-value-123"
            try:
                result = import_search_secret("serpapi", value_env="POLICY_TEST_SERPAPI_KEY", search_secrets_file=Path(tmp) / "secrets.json")
            finally:
                if old is None:
                    os.environ.pop("POLICY_TEST_SERPAPI_KEY", None)
                else:
                    os.environ["POLICY_TEST_SERPAPI_KEY"] = old
        self.assertTrue(result["provider_ready_after_import"])
        self.assertNotIn("serpapi-secret-value-123", json.dumps(result, ensure_ascii=False))

    def test_cli_search_secret_import_outputs_sanitized_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "serpapi_key.txt"
            source.write_text("serpapi-secret-value-123", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "search-secret-import",
                        "--provider",
                        "serpapi",
                        "--value-file",
                        str(source),
                        "--search-secrets-file",
                        str(root / "policy-search-secrets.json"),
                        "--json",
                    ]
                )
            payload = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["provider"], "serpapi")
        self.assertTrue(payload["provider_ready_after_import"])
        self.assertNotIn("serpapi-secret-value-123", out.getvalue())
        self.assertNotIn(str(source), out.getvalue())

    def test_bulk_import_writes_multiple_providers_without_exposing_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "search_api_bundle.json"
            target = root / "policy-search-secrets.json"
            source.write_text(
                json.dumps(
                    {
                        "SERPAPI_API_KEY": "serpapi-secret-value-123",
                        "bing": {"api_key": "bing-secret-value-123"},
                        "google": {
                            "api_key": "google-secret-value-123",
                            "cse_id": "google-cse-id-123",
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = import_search_secret_bundle(source, search_secrets_file=target)
            payload = json.loads(target.read_text(encoding="utf-8"))

        encoded = json.dumps(result, ensure_ascii=False)
        self.assertEqual(result["imported_count"], 3)
        self.assertEqual(result["ready_count_after_import"], 3)
        self.assertEqual(payload["SERPAPI_API_KEY"], "serpapi-secret-value-123")
        self.assertEqual(payload["BING_SEARCH_API_KEY"], "bing-secret-value-123")
        self.assertEqual(payload["GOOGLE_SEARCH_API_KEY"], "google-secret-value-123")
        self.assertEqual(payload["GOOGLE_CSE_ID"], "google-cse-id-123")
        self.assertNotIn("serpapi-secret-value-123", encoded)
        self.assertNotIn("bing-secret-value-123", encoded)
        self.assertNotIn("google-secret-value-123", encoded)
        self.assertNotIn(str(source), encoded)

    def test_cli_search_secret_bulk_import_outputs_sanitized_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "search_api_bundle.json"
            source.write_text(
                json.dumps({"BING_SEARCH_API_KEY": "bing-secret-value-123"}),
                encoding="utf-8",
            )
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "search-secret-bulk-import",
                        "--source-file",
                        str(source),
                        "--search-secrets-file",
                        str(root / "policy-search-secrets.json"),
                        "--json",
                    ]
                )
            payload = json.loads(out.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["imported_count"], 1)
        self.assertEqual(payload["skipped_count"], 2)
        self.assertNotIn("bing-secret-value-123", out.getvalue())
        self.assertNotIn(str(source), out.getvalue())


if __name__ == "__main__":
    unittest.main()
