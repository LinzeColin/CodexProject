from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "finalize_delivery.py"


def load_finalize_module():
    spec = importlib.util.spec_from_file_location("finalize_delivery", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load finalize_delivery.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["finalize_delivery"] = module
    spec.loader.exec_module(module)
    return module


class FinalizeDeliveryTests(unittest.TestCase):
    def test_parser_defaults_to_current_delivery_paths(self) -> None:
        finalize_delivery = load_finalize_module()
        args = finalize_delivery.build_parser().parse_args([])
        self.assertEqual(args.base_url, "http://127.0.0.1:8772/")
        self.assertEqual(args.output_dir, "outputs/finance_ledger_20220605_20260603")
        self.assertEqual(args.ledger_db, "data/finance_ledger/finance_ledger.sqlite")

    def test_finalize_stops_on_first_failed_step(self) -> None:
        finalize_delivery = load_finalize_module()
        args = finalize_delivery.build_parser().parse_args(["--base-url", "http://127.0.0.1:9999/"])
        with mock.patch.object(finalize_delivery, "run_command") as run_command:
            run_command.return_value = {
                "command": ["fake"],
                "returncode": 1,
                "duration_seconds": 0,
                "stdout": "",
                "stderr": "failed",
                "ok": False,
            }
            result = finalize_delivery.finalize(args)
        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_step"], "browser_visual_acceptance")
        self.assertEqual(len(result["steps"]), 1)

    def test_http_404_still_means_local_server_is_available(self) -> None:
        finalize_delivery = load_finalize_module()
        error = finalize_delivery.urllib.error.HTTPError("http://127.0.0.1:8772/", 404, "not found", {}, None)
        with mock.patch.object(finalize_delivery.urllib.request, "urlopen", side_effect=error):
            self.assertTrue(finalize_delivery.url_available("http://127.0.0.1:8772/"))

    def test_classifies_permission_failure(self) -> None:
        finalize_delivery = load_finalize_module()
        result = finalize_delivery.classify_failure(
            {
                "command": ["python", "scripts/run_browser_visual_acceptance.py"],
                "stdout": "",
                "stderr": "PermissionError: [Errno 1] Operation not permitted",
            }
        )
        self.assertEqual(result["kind"], "sandbox_permission")

    def test_classifies_stale_browser_acceptance(self) -> None:
        finalize_delivery = load_finalize_module()
        result = finalize_delivery.classify_failure(
            {
                "command": ["python", "scripts/verify_browser_acceptance.py"],
                "stdout": "browser audit is older than current HTML pages",
                "stderr": "",
            }
        )
        self.assertEqual(result["kind"], "stale_browser_acceptance")

    def test_process_tail_reports_exited_process_output(self) -> None:
        finalize_delivery = load_finalize_module()
        process = mock.Mock()
        process.poll.return_value = 1
        process.communicate.return_value = ("stdout text", "stderr text")
        detail = finalize_delivery.process_tail(process)
        self.assertEqual(detail["returncode"], 1)
        self.assertEqual(detail["stdout"], "stdout text")
        self.assertEqual(detail["stderr"], "stderr text")

    def test_preflight_treats_stale_browser_audit_as_warning(self) -> None:
        finalize_delivery = load_finalize_module()
        args = finalize_delivery.build_parser().parse_args(["--preflight-only"])
        calls = [
            {
                "command": ["verify"],
                "returncode": 1,
                "duration_seconds": 0,
                "stdout": "browser audit is older than current HTML pages",
                "stderr": "",
                "ok": False,
            },
            {"command": ["audit_chatgpt"], "returncode": 0, "duration_seconds": 0, "stdout": "ok", "stderr": "", "ok": True},
            {"command": ["audit_goal"], "returncode": 0, "duration_seconds": 0, "stdout": "ok", "stderr": "", "ok": True},
            {"command": ["pytest"], "returncode": 0, "duration_seconds": 0, "stdout": "ok", "stderr": "", "ok": True},
            {"command": ["validate"], "returncode": 0, "duration_seconds": 0, "stdout": "ok", "stderr": "", "ok": True},
        ]
        with mock.patch.object(finalize_delivery, "run_command", side_effect=calls):
            result = finalize_delivery.finalize(args)
        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "preflight_only")
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual(result["warnings"][0]["name"], "browser_acceptance_freshness")


if __name__ == "__main__":
    unittest.main()
