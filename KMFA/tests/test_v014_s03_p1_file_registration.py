import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from KMFA.tools.v014_s03_p1_raw_file_registration import build_registration
from KMFA.tools.check_v014_s03_p1_file_registration import validate_v014_s03_p1_file_registration


class V014S03P1FileRegistrationTests(unittest.TestCase):
    def test_build_registration_keeps_raw_names_and_hashes_private(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            raw.mkdir()
            sensitive_csv = raw / "客户合同金额.csv"
            sensitive_csv.write_text("project,amount\nA,100\n", encoding="utf-8")
            xlsx = raw / "财务账龄.xlsx"
            xlsx.write_bytes(b"PK\x03\x04xlsx")
            xls = raw / "旧版台账.xls"
            xls.write_bytes(bytes.fromhex("d0cf11e0a1b11ae1") + b"ole")
            archive = raw / "上传包.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("inside/private.csv", "a,b\n1,2\n")

            private = root / "private"
            bundle = build_registration(raw, private, generated_at="2026-07-03T00:00:00+00:00")

            public = bundle["public_register"]
            public_text = json.dumps(public, ensure_ascii=False)
            self.assertEqual(public["scan_summary"]["file_count"], 4)
            self.assertEqual(public["scan_summary"]["supported_file_count"], 4)
            self.assertEqual(public["scan_summary"]["unsupported_file_count"], 0)
            self.assertEqual(public["scan_summary"]["wps_or_ole_guidance_count"], 1)
            self.assertNotIn("客户合同金额.csv", public_text)
            self.assertNotIn("财务账龄.xlsx", public_text)
            self.assertNotIn("inside/private.csv", public_text)
            self.assertNotIn("content_sha256", public_text)
            self.assertNotIn("relative_path", public_text)
            self.assertTrue(public["raw_root_status"]["read_only_scan_performed"])
            self.assertFalse(public["raw_root_status"]["write_performed"])
            self.assertTrue(public["raw_root_status"]["raw_root_stat_unchanged_after_scan"])
            for record in public["public_file_records"]:
                self.assertEqual(record["content_hash_status"], "computed_private_only")
                self.assertFalse(record["raw_filename_committed"])
                self.assertFalse(record["raw_hash_committed"])

            private_manifest = json.loads((private / "private_raw_file_manifest.json").read_text(encoding="utf-8"))
            private_text = json.dumps(private_manifest, ensure_ascii=False)
            self.assertIn("客户合同金额.csv", private_text)
            self.assertIn("content_sha256", private_text)
            self.assertEqual(private_manifest["entry_count"], 4)

    def test_repository_evidence_validator_passes(self) -> None:
        manifest = validate_v014_s03_p1_file_registration()
        self.assertEqual(manifest["phase_id"], "S03-P1")
        self.assertEqual(manifest["status"], "completed_validated_local_only_no_go_upload_deferred")
        self.assertEqual(manifest["next_recommended_phase"], "S03-P2")


if __name__ == "__main__":
    unittest.main()
