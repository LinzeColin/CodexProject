from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package_delivery.py"
sys.path.insert(0, str(ROOT / "scripts"))

from verify_browser_acceptance import DEFAULT_EXPECTED_COUNT


def load_package_module():
    spec = importlib.util.spec_from_file_location("package_delivery", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load package_delivery.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["package_delivery"] = module
    spec.loader.exec_module(module)
    return module


class PackageDeliveryTests(unittest.TestCase):
    def test_package_delivery_includes_manifest_and_requested_output_dir(self) -> None:
        package_delivery = load_package_module()
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
            base = Path(tmp).relative_to(ROOT)
            output_dir = base / "outputs" / "finance"
            reports = ROOT / output_dir / "reports"
            reports.mkdir(parents=True)
            audit = ROOT / output_dir / "audit"
            audit.mkdir(parents=True)
            (audit / "browser_visual_acceptance.json").write_text(
                json.dumps({"checked_count": DEFAULT_EXPECTED_COUNT, "failure_count": 0, "failures": [], "results": _browser_rows()}),
                encoding="utf-8",
            )
            (reports / "index.html").write_text("<html>portal</html>", encoding="utf-8")
            (reports / "operations_center.html").write_text("<html>ops</html>", encoding="utf-8")
            (reports / "dashboard.html").write_text("<html>dashboard</html>", encoding="utf-8")
            (reports / "review_workbench.html").write_text("<html>review</html>", encoding="utf-8")
            (reports / "user_manual_report.pdf").write_bytes(b"%PDF-test")
            ledger_db = base / "data" / "finance.sqlite"
            (ROOT / ledger_db).parent.mkdir(parents=True)
            (ROOT / ledger_db).write_bytes(b"sqlite")
            package_dir = base / "package"

            result = package_delivery.build_delivery_package(
                output_dir=output_dir,
                ledger_db=ledger_db,
                package_dir=package_dir,
                package_name="test_delivery.zip",
            )

            self.assertEqual(result["missing"], [])
            self.assertTrue(result["goal_audit_refreshed"])
            zip_path = Path(result["zip_path"])
            self.assertTrue(zip_path.exists())
            goal_audit = json.loads((ROOT / output_dir / "audit" / "goal_completion_audit.json").read_text(encoding="utf-8"))
            package_row = next(row for row in goal_audit["rows"] if row["requirement_id"] == "delivery_package")
            self.assertIn("test_delivery.zip", package_row["evidence"])
            with ZipFile(zip_path) as archive:
                names = set(archive.namelist())
                self.assertIn("economic_bleed_delivery/PACKAGE_MANIFEST.json", names)
                self.assertIn(f"economic_bleed_delivery/{output_dir}/audit/goal_completion_audit.json", names)
                self.assertIn(f"economic_bleed_delivery/{output_dir}/reports/index.html", names)
                self.assertIn(f"economic_bleed_delivery/{ledger_db}", names)
                manifest = json.loads(archive.read("economic_bleed_delivery/PACKAGE_MANIFEST.json").decode("utf-8"))
                self.assertEqual(manifest["entry_points"]["operations_center"], str(output_dir / "reports" / "operations_center.html"))
                packaged_goal_audit = json.loads(
                    archive.read(f"economic_bleed_delivery/{output_dir}/audit/goal_completion_audit.json").decode("utf-8")
                )
                packaged_package_row = next(row for row in packaged_goal_audit["rows"] if row["requirement_id"] == "delivery_package")
                self.assertIn("test_delivery.zip", packaged_package_row["evidence"])

    def test_package_delivery_fails_when_browser_acceptance_is_stale(self) -> None:
        package_delivery = load_package_module()
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
            base = Path(tmp).relative_to(ROOT)
            output_dir = base / "outputs" / "finance"
            output_root = ROOT / output_dir
            output_root.mkdir(parents=True)
            audit = output_root / "audit"
            audit.mkdir()
            audit_file = audit / "browser_visual_acceptance.json"
            audit_file.write_text(
                json.dumps({"checked_count": DEFAULT_EXPECTED_COUNT, "failure_count": 0, "failures": [], "results": _browser_rows()}),
                encoding="utf-8",
            )
            dashboard = output_root / "dashboard.html"
            dashboard.write_text("<html>new dashboard</html>", encoding="utf-8")
            os.utime(audit_file, (1_000, 1_000))
            os.utime(dashboard, (2_000, 2_000))
            ledger_db = base / "data" / "finance.sqlite"
            (ROOT / ledger_db).parent.mkdir(parents=True)
            (ROOT / ledger_db).write_bytes(b"sqlite")

            result = package_delivery.build_delivery_package(
                output_dir=output_dir,
                ledger_db=ledger_db,
                package_dir=base / "package",
                package_name="test_delivery.zip",
            )

            self.assertEqual(result["zip_path"], "")
            self.assertTrue(any("older than current HTML" in error for error in result["browser_acceptance_errors"]))


def _browser_rows() -> list[dict[str, object]]:
    return [
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


if __name__ == "__main__":
    unittest.main()
