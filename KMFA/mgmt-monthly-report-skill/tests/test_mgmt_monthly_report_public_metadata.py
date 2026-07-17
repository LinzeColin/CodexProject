from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from KMFA.tools.v015_s03_p3_public_repository_safety import audit_public_metadata_bytes


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "KMFA" / "mgmt-monthly-report-skill" / "scripts" / "mgmt_monthly_report.py"
METADATA_ROOT = ROOT / "KMFA" / "metadata" / "mgmt-monthly-report-skill"

SPEC = importlib.util.spec_from_file_location("mgmt_monthly_report", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

PRIVATE_DERIVED_KEYS = {
    "expected_file_name",
    "extension",
    "file_name",
    "file_name_sha256",
    "file_sha256",
    "file_size_bytes",
    "matched_pattern",
    "matched_sheet_names_sha256",
    "output_dir_sha256",
    "sheet_names",
    "sheet_names_sha256",
}


def iter_items(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from iter_items(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_items(child)


def write_workbook(path: Path, sheet_names: tuple[str, ...] = ("Synthetic",)) -> None:
    sheets = "".join(
        f'<sheet name="{name}" sheetId="{index}"/>'
        for index, name in enumerate(sheet_names, start=1)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheets>{sheets}</sheets></workbook>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook)


class PublicMetadataV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.input_dir = self.root / "inputs"
        self.output_dir = self.root / "outputs"
        self.metadata_root = self.root / "metadata"
        self.input_dir.mkdir()
        self.output_dir.mkdir()

        fixtures = {
            "Synthetic 2026 回款表.xlsx": ("Synthetic",),
            "Synthetic 开票 纳税 资金汇总.xlsx": ("开票纳税汇总", "2026年销售回款", "2026年资金汇总"),
            "Synthetic 应收账款 合同登记.xlsx": ("Synthetic",),
            "Synthetic 应收账龄.xlsx": ("Synthetic",),
            "Synthetic 保证金2026.xlsx": ("Synthetic",),
            "Synthetic 三大项目.xlsx": ("Synthetic",),
            "Synthetic 红圈主合同.xlsx": ("Synthetic",),
        }
        for name, sheets in fixtures.items():
            write_workbook(self.input_dir / name, sheets)
        (self.output_dir / MODULE.OFFICIAL_EXCEL.format(period="202607")).write_bytes(b"synthetic")
        (self.output_dir / MODULE.OFFICIAL_PDF.format(period="202607")).write_bytes(b"synthetic")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _manifest(self) -> dict:
        return MODULE.build_manifest("202607", self.input_dir, self.output_dir, self.metadata_root)

    def test_manifest_contains_only_static_refs_status_and_aggregate_counts(self) -> None:
        manifest = self._manifest()
        self.assertEqual(manifest["schema_version"], "mgmt-monthly-report-public-safe-v2")
        self.assertEqual(
            [slot["source_group_ref"] for slot in manifest["input_slots"]],
            [f"SRC-MMR-V2-{index:03d}" for index in range(1, 8)],
        )
        self.assertEqual(
            [output["output_ref"] for output in manifest["outputs"]],
            ["OUT-MMR-V2-001", "OUT-MMR-V2-002"],
        )
        serialized = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        for name in (path.name for path in self.input_dir.iterdir()):
            self.assertNotIn(name, serialized)
        self.assertNotRegex(serialized, r"(?i)\b[0-9a-f]{64}\b")
        self.assertNotRegex(serialized, r"(?i)\.(?:xls|xlsx|pdf)\b")
        for key, value in iter_items(manifest):
            if value not in (None, "", False):
                self.assertNotIn(key, PRIVATE_DERIVED_KEYS)

    def test_sql_export_is_aggregate_only_and_executes_against_public_schema(self) -> None:
        export_sql = MODULE.render_sql_export(self._manifest())
        lowered = export_sql.casefold()
        for forbidden in (
            "file_sha256",
            "file_size_bytes",
            "sheet_names",
            "matched_pattern",
            ".xlsx",
            ".pdf",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("monthly_report_input_slot_aggregate", export_sql)
        self.assertIn("monthly_report_output_status", export_sql)
        MODULE.smoke_test_sql(METADATA_ROOT / "database" / "schema.sql", export_sql)

    def test_write_artifacts_cannot_reintroduce_private_derived_metadata(self) -> None:
        MODULE.ensure_metadata_dirs(self.metadata_root)
        shutil.copyfile(METADATA_ROOT / "database" / "schema.sql", self.metadata_root / "database" / "schema.sql")
        MODULE.write_artifacts(self._manifest(), self.metadata_root)

        findings = []
        for path in sorted(self.metadata_root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(self.metadata_root).as_posix()
            public_path = f"KMFA/metadata/mgmt-monthly-report-skill/{relative}"
            findings.extend(audit_public_metadata_bytes(public_path, path.read_bytes()))
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"(?i)\b[0-9a-f]{64}\b", text))
            for name in (candidate.name for candidate in self.input_dir.iterdir()):
                self.assertNotIn(name, text)
        self.assertEqual(findings, [])

    def test_tracked_metadata_passes_s03p3_public_safety_audit(self) -> None:
        findings = []
        for path in sorted(METADATA_ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            findings.extend(audit_public_metadata_bytes(relative, path.read_bytes()))
        self.assertEqual(findings, [])

    def test_tracked_indexes_and_sql_are_exact_public_manifest_projections(self) -> None:
        manifest = json.loads(
            (METADATA_ROOT / "run_manifests" / "202607_public_safe_run_manifest.json").read_text(encoding="utf-8")
        )
        source_index = json.loads(
            (METADATA_ROOT / "raw_index" / "202607_public_safe_source_index.json").read_text(encoding="utf-8")
        )
        output_index = json.loads(
            (METADATA_ROOT / "public_reports" / "202607_output_report_index.json").read_text(encoding="utf-8")
        )
        cleanup = json.loads(
            (METADATA_ROOT / "cleanup" / "202607_cleanup_audit.json").read_text(encoding="utf-8")
        )

        self.assertEqual(source_index["input_slots"], manifest["input_slots"])
        self.assertEqual(output_index["outputs"], manifest["outputs"])
        self.assertEqual(cleanup["output_statuses"], manifest["outputs"])
        self.assertEqual(
            (METADATA_ROOT / "database" / "202607_registry_export.sql").read_text(encoding="utf-8"),
            MODULE.render_sql_export(manifest),
        )


if __name__ == "__main__":
    unittest.main()
