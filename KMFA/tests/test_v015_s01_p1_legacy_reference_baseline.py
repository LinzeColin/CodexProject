import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from KMFA.tools.check_v015_s01_p1_legacy_reference_baseline import (
    ACCEPTANCE_PATH,
    MANIFEST_PATH,
    METADATA_BASELINE_PATH,
    SHA256_INVENTORY_PATH,
    ValidationError,
    _canonical_content_hash,
    _git_text as real_git_text,
    validate_v015_s01_p1_legacy_reference_baseline,
)


class TestV015S01P1LegacyReferenceBaseline(unittest.TestCase):
    def _write_json(self, directory: str, name: str, value: dict) -> Path:
        path = Path(directory) / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_validates_negative_legacy_reference_without_phase_pass(self) -> None:
        result = validate_v015_s01_p1_legacy_reference_baseline()

        self.assertEqual(result["target_release"], "v1.5")
        self.assertEqual(result["acceptance_status"], "NOT_PASSED")
        self.assertEqual(result["decision"], "NO_GO")
        self.assertEqual(result["baseline_kind"], "legacy_static_reference_not_v15_runtime")
        self.assertEqual(result["phase_gate"]["task_acceptance_passed_count"], 0)
        self.assertFalse(result["phase_gate"]["s01p1_acceptance_passed"])
        self.assertFalse(result["reconstructability"]["installed_app_from_tracked_source"])
        self.assertFalse(result["reconstructability"]["real_v15_application_runtime"])

    def test_rejects_false_phase_acceptance_claim(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["acceptance_status"] = "PASSED"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(path)

    def test_rejects_acceptance_check_identity_or_finding_drift(self) -> None:
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        acceptance["checks"][-1]["check_id"] = "unrelated_check"
        acceptance["checks"][-1]["finding"] = "UNRELATED_FINDING"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "acceptance.json"
            path.write_text(json.dumps(acceptance, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(acceptance_path=path)

    def test_rejects_acceptance_document_identity_drift(self) -> None:
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        acceptance["schema_version"] = "wrong"
        acceptance["project_id"] = "OTHER"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "acceptance.json"
            path.write_text(json.dumps(acceptance, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(acceptance_path=path)

    def test_rejects_metadata_app_hash_drift(self) -> None:
        metadata = json.loads(METADATA_BASELINE_PATH.read_text(encoding="utf-8"))
        metadata["installed_app_aggregate_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(metadata_baseline_path=path)

    def test_rejects_metadata_document_identity_drift(self) -> None:
        metadata = json.loads(METADATA_BASELINE_PATH.read_text(encoding="utf-8"))
        metadata["schema_version"] = "wrong"
        metadata["project_id"] = "OTHER"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(metadata_baseline_path=path)

    def test_rejects_empty_release_state_even_with_recomputed_manifest_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["release_state"] = {}
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(path)

    def test_rejects_empty_artifact_refs_even_with_recomputed_manifest_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["artifact_refs"] = {}
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(path)

    def test_rejects_extra_phase_gate_key_even_with_recomputed_manifest_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["phase_gate"]["s02_started"] = True
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(path)

    def test_rejects_not_passed_task_count_drift(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["phase_gate"]["task_acceptance_not_passed_count"] = 2
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "manifest.json", manifest)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(path)

    def test_rejects_unverifiable_live_remote_oid(self) -> None:
        def fake_git_text(args: list[str]) -> str:
            if args[:2] == ["ls-remote", "origin"]:
                return "f" * 40 + "\trefs/heads/main"
            return real_git_text(args)

        with patch("KMFA.tools.check_v015_s01_p1_legacy_reference_baseline._git_text", side_effect=fake_git_text):
            with patch("KMFA.tools.check_v015_s01_p1_legacy_reference_baseline._commit_is_visible", return_value=False):
                with self.assertRaises(ValidationError):
                    validate_v015_s01_p1_legacy_reference_baseline(require_remote_main=True)

    def test_rejects_missing_private_evidence_ids_even_with_recomputed_manifest_hash(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["private_evidence_index"] = [
            item
            for item in manifest["private_evidence_index"]
            if item["evidence_id"] in {"S01P1T02_DESKTOP_SCREENSHOT", "S01P1T02_MOBILE_SCREENSHOT"}
        ]
        manifest["content_hash"] = _canonical_content_hash(manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(path)

    def test_rejects_sha256_inventory_drift(self) -> None:
        with SHA256_INVENTORY_PATH.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
            fieldnames = list(rows[0])
        rows[0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(ValidationError):
                validate_v015_s01_p1_legacy_reference_baseline(sha256_inventory_path=path)


if __name__ == "__main__":
    unittest.main()
