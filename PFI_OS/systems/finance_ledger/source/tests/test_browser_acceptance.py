from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.verify_browser_acceptance import DEFAULT_EXPECTED_COUNT, validate_audit_freshness, validate_payload


def make_payload(*, failure_count: int = 0) -> dict:
    rows = [
        {
            "page": f"page-{idx}.html",
            "viewport": {"name": "desktop" if idx % 2 == 0 else "mobile", "width": 1440, "height": 1000},
            "marker_ok": True,
            "visual_ok": True,
            "overflow_x": 0,
            "text_length": 1000,
        }
        for idx in range(DEFAULT_EXPECTED_COUNT)
    ]
    return {
        "checked_count": DEFAULT_EXPECTED_COUNT,
        "failure_count": failure_count,
        "failures": [] if failure_count == 0 else [rows[0]],
        "results": rows,
    }


class BrowserAcceptanceTests(unittest.TestCase):
    def test_valid_payload_passes(self):
        self.assertEqual(validate_payload(make_payload(), expected_count=DEFAULT_EXPECTED_COUNT), [])

    def test_failure_count_fails(self):
        errors = validate_payload(make_payload(failure_count=1), expected_count=DEFAULT_EXPECTED_COUNT)
        self.assertTrue(any("failure_count" in error for error in errors))

    def test_missing_result_key_fails(self):
        payload = make_payload()
        payload["results"][0].pop("visual_ok")
        errors = validate_payload(payload, expected_count=DEFAULT_EXPECTED_COUNT)
        self.assertTrue(any("visual_ok" in error for error in errors))

    def test_stale_audit_fails_freshness_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit = root / "browser_visual_acceptance.json"
            html_root = root / "html"
            html_root.mkdir()
            audit.write_text(json.dumps(make_payload()), encoding="utf-8")
            page = html_root / "dashboard.html"
            page.write_text("<html></html>", encoding="utf-8")
            os.utime(audit, (1_000, 1_000))
            os.utime(page, (2_000, 2_000))
            errors = validate_audit_freshness(audit, html_root)
            self.assertTrue(any("older than current HTML" in error for error in errors))

    def test_fresh_audit_passes_freshness_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit = root / "browser_visual_acceptance.json"
            html_root = root / "html"
            html_root.mkdir()
            page = html_root / "dashboard.html"
            page.write_text("<html></html>", encoding="utf-8")
            audit.write_text(json.dumps(make_payload()), encoding="utf-8")
            os.utime(page, (1_000, 1_000))
            os.utime(audit, (2_000, 2_000))
            errors = validate_audit_freshness(audit, html_root)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
