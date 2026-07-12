import csv
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from KMFA.tools.a0_file_register import build_a0_registration, validate_a0_registration


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def inventory_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(1, 9):
        rows.append(
            {
                "数据包": "销售绩效考核",
                "文件路径": f"销售绩效考核/project-{index:02d}.pdf",
                "文件类型": "PDF",
                "大小KB": "12.3",
                "工作表数量": "0",
                "工作表摘要": "",
                "KMFA用途判断": "synthetic test only",
                "MVP状态": "人工复核",
                "阻塞/下一步": "test fixture",
                "指纹/CRC": f"crc-{index:08x}",
            }
        )
    rows.append(
        {
            "数据包": "销售绩效考核",
            "文件路径": "销售绩效考核/project-cost.xlsx",
            "文件类型": "Excel OOXML",
            "大小KB": "45.6",
            "工作表数量": "3",
            "工作表摘要": "overview; detail; cost",
            "KMFA用途判断": "synthetic test only",
            "MVP状态": "人工复核",
            "阻塞/下一步": "test fixture",
            "指纹/CRC": "abc123def4567890",
        }
    )
    return rows


class A0FileRegisterTests(unittest.TestCase):
    def test_builds_public_safe_a0_manifest_from_inventory_without_private_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = root / "inventory.csv"
            source_manifest = root / "source.csv"
            write_csv(
                inventory,
                [
                    "数据包",
                    "文件路径",
                    "文件类型",
                    "大小KB",
                    "工作表数量",
                    "工作表摘要",
                    "KMFA用途判断",
                    "MVP状态",
                    "阻塞/下一步",
                    "指纹/CRC",
                ],
                inventory_rows(),
            )
            write_csv(
                source_manifest,
                ["file", "bytes", "sha256", "rule"],
                [
                    {
                        "file": "PRIVATE_RAW_SOURCE_005.zip",
                        "bytes": "100",
                        "sha256": "0" * 64,
                        "rule": "private source zip; public repo metadata only",
                    }
                ],
            )

            manifest, candidates = build_a0_registration(
                inventory_csv=inventory,
                source_manifest_csv=source_manifest,
                generated_at="2026-06-30T00:00:00+10:00",
            )

        validate_a0_registration(manifest, candidates)
        self.assertEqual(manifest["file_summary"]["total_files"], 9)
        self.assertEqual(manifest["file_summary"]["pdf_files"], 8)
        self.assertEqual(manifest["file_summary"]["excel_files"], 1)
        self.assertEqual(manifest["file_summary"]["member_sha256_recorded_count"], 0)
        self.assertEqual(manifest["file_summary"]["member_sha256_pending_count"], 9)
        self.assertTrue(all(item["member_sha256_status"] == "pending_private_zip_unavailable" for item in manifest["files"]))
        self.assertTrue(all(candidate["machine_candidate_quality_grade"] == "Q3" for candidate in candidates))
        self.assertTrue(all(candidate["q4_human_locked"] is False for candidate in candidates))
        self.assertTrue(all(candidate["q5_formal_report_allowed"] is False for candidate in candidates))

    def test_computes_member_sha256_when_private_zip_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = root / "inventory.csv"
            source_manifest = root / "source.csv"
            zip_path = root / "PRIVATE_RAW_SOURCE_005.zip"
            rows = inventory_rows()
            write_csv(
                inventory,
                [
                    "数据包",
                    "文件路径",
                    "文件类型",
                    "大小KB",
                    "工作表数量",
                    "工作表摘要",
                    "KMFA用途判断",
                    "MVP状态",
                    "阻塞/下一步",
                    "指纹/CRC",
                ],
                rows,
            )
            with zipfile.ZipFile(zip_path, "w") as archive:
                for row in rows:
                    archive.writestr(str(row["文件路径"]), f"synthetic bytes for {row['文件路径']}")
            zip_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            write_csv(
                source_manifest,
                ["file", "bytes", "sha256", "rule"],
                [
                    {
                        "file": "PRIVATE_RAW_SOURCE_005.zip",
                        "bytes": str(zip_path.stat().st_size),
                        "sha256": zip_hash,
                        "rule": "private source zip; public repo metadata only",
                    }
                ],
            )

            manifest, candidates = build_a0_registration(
                inventory_csv=inventory,
                source_manifest_csv=source_manifest,
                source_zip=zip_path,
                generated_at="2026-06-30T00:00:00+10:00",
            )

        validate_a0_registration(manifest, candidates, require_member_sha256=True)
        self.assertEqual(manifest["file_summary"]["member_sha256_recorded_count"], 9)
        self.assertEqual(manifest["file_summary"]["member_sha256_pending_count"], 0)
        self.assertTrue(all(str(item["member_sha256"]).startswith("sha256:") for item in manifest["files"]))

    def test_rejects_wrong_a0_file_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = root / "inventory.csv"
            source_manifest = root / "source.csv"
            rows = inventory_rows()[:-1]
            write_csv(
                inventory,
                [
                    "数据包",
                    "文件路径",
                    "文件类型",
                    "大小KB",
                    "工作表数量",
                    "工作表摘要",
                    "KMFA用途判断",
                    "MVP状态",
                    "阻塞/下一步",
                    "指纹/CRC",
                ],
                rows,
            )
            write_csv(
                source_manifest,
                ["file", "bytes", "sha256", "rule"],
                [
                    {
                        "file": "PRIVATE_RAW_SOURCE_005.zip",
                        "bytes": "100",
                        "sha256": "0" * 64,
                        "rule": "private source zip; public repo metadata only",
                    }
                ],
            )

            with self.assertRaises(ValueError):
                build_a0_registration(
                    inventory_csv=inventory,
                    source_manifest_csv=source_manifest,
                    generated_at="2026-06-30T00:00:00+10:00",
                )


if __name__ == "__main__":
    unittest.main()
