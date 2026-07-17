import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import build_v015_s03_stage_review as builder
from KMFA.tools import check_v015_s03_stage_review as checker


class TestV015S03StageReview(unittest.TestCase):
    def test_source_package_locks_s03_and_quality_contract(self) -> None:
        source, tasks, slots = builder.verify_source_package()

        self.assertEqual((source["stage_count"], source["phase_count"], source["task_count"]), (24, 72, 216))
        self.assertEqual((source["s03_phase_count"], source["s03_task_count"]), (3, 9))
        self.assertFalse(source["formal_stage_review_task_present"])
        self.assertEqual(len(tasks), 9)
        self.assertEqual(tasks[0]["task_id"], "S03P1T01")
        self.assertEqual(tasks[-1]["task_id"], "S03P3T03")
        self.assertEqual(len(slots), 10)

    def test_phase_evidence_binds_three_passed_phases_and_receipts(self) -> None:
        manifest = json.loads((builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / builder.MANIFEST_RELATIVE).read_text())

        checker._validate_phase_evidence(manifest)
        self.assertEqual(manifest["task_accounting"], {"accepted": 9, "total": 9})
        self.assertEqual([row["phase_id"] for row in manifest["phase_evidence"]], ["S03-P1", "S03-P2", "S03-P3"])

    def test_review_closes_two_findings_and_routes_six_risks(self) -> None:
        manifest = json.loads((builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / builder.MANIFEST_RELATIVE).read_text())

        checker._validate_contracts_and_evidence(manifest)
        self.assertEqual(manifest["review_findings"], {"total": 2, "fixed_validated": 2, "open": 0, "blocking_open": 0})
        self.assertEqual(manifest["open_risks"], {"total": 6, "routed": 6, "plan_gap_count": 0, "blocking": 0})
        self.assertEqual(manifest["cross_phase_accounting"], {"total": 14, "passed": 14, "failed": 0, "blocking_failed": 0})

    def test_runtime_permission_guard_detects_nested_mode_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "local_runtime"
            root.mkdir(mode=0o700)
            os.chmod(root, 0o700)
            for layer in builder.RUNTIME_LAYERS:
                path = root / layer
                path.mkdir(mode=0o700)
                os.chmod(path, 0o700)
            nested = root / "reports" / "review"
            nested.mkdir(mode=0o700)
            os.chmod(nested, 0o700)

            valid = builder.runtime_directory_summary(root, check_gitignore=False)
            self.assertEqual(valid["invalid_directory_count"], 0)
            self.assertTrue(valid["all_directories_mode_0700"])

            os.chmod(nested, 0o755)
            invalid = builder.runtime_directory_summary(root, check_gitignore=False)
            self.assertEqual(invalid["invalid_directory_count"], 1)
            self.assertFalse(invalid["all_directories_mode_0700"])
            self.assertEqual(stat.S_IMODE(nested.stat().st_mode), 0o755)

    def test_current_private_runtime_is_0700_and_ignored(self) -> None:
        summary = builder.runtime_directory_summary()

        self.assertEqual(summary["layer_count"], 9)
        self.assertEqual(summary["invalid_directory_count"], 0)
        self.assertTrue(summary["all_directories_mode_0700"])
        self.assertTrue(summary["all_layers_gitignored"])
        self.assertFalse(summary["private_file_content_read"])
        self.assertFalse(summary["raw_inbox_accessed"])

    def test_stage_boundary_never_uploads_reinstalls_or_starts_s04(self) -> None:
        manifest_path = builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / builder.MANIFEST_RELATIVE
        results_path = builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / builder.VALIDATION_RESULTS_RELATIVE
        manifest = json.loads(manifest_path.read_text())
        rows = [json.loads(line) for line in results_path.read_text().splitlines() if line.strip()]
        final, _ = builder.validation_status(rows)

        self.assertEqual(manifest["stage_gate"]["stage_acceptance_status"], "PASSED" if final else "PENDING")
        self.assertEqual(manifest["stage_gate"]["decision"], "GO_TO_S04_P1_ONLY" if final else "REMAIN_IN_S03_STAGE_REVIEW")
        self.assertEqual(manifest["next_entry_gate"]["s04_p1_entry_allowed"], final)
        self.assertFalse(manifest["next_entry_gate"]["s04_p1_started"])
        self.assertFalse(manifest["next_entry_gate"]["github_upload_allowed"])
        self.assertFalse(manifest["next_entry_gate"]["app_reinstall_allowed"])
        self.assertTrue(all(value is False for value in manifest["downstream_actions"].values()))

    def test_validation_subject_refs_decode_non_ascii_paths(self) -> None:
        refs = builder.validation_subject_refs()

        self.assertIn("KMFA/tools/check_v015_s03_stage_review.py", refs)
        self.assertNotIn("KMFA/功能清单.md", refs)
        self.assertTrue(all(not ref.startswith('"') and "\\345" not in ref for ref in refs))

        changed = checker._git_diff_paths(builder.REVIEW_BASE_COMMIT, "HEAD")
        self.assertIn("KMFA/功能清单.md", changed)
        self.assertTrue(all(not ref.startswith('"') and "\\345" not in ref for ref in changed))

    def test_absolute_path_scanner_does_not_flag_boundary_slashes(self) -> None:
        self.assertIsNone(builder._ABSOLUTE_PATH_RE.search(b"raw/private/public contracts"))
        absolute_fixture = b"path=" + b"/" + b"Users/example/private.txt"
        self.assertIsNotNone(builder._ABSOLUTE_PATH_RE.search(absolute_fixture))

    def test_review_scope_covers_governance_sync_implementation(self) -> None:
        self.assertIn(
            "KMFA/tools/v015_roadmap_governance_sync.py",
            checker.ALLOWED_REVIEW_PREFIXES,
        )

    def test_validator_matches_current_pending_or_final_state(self) -> None:
        rows = checker._read_jsonl(checker.VALIDATION_RESULTS_PATH)
        final, _ = builder.validation_status(rows)

        result = checker.validate(
            pre_receipt=not final,
            skip_exact_rebuild=False,
            require_clean_commit=False,
        )
        self.assertEqual(result["stage_gate"]["evidence_validation_status"], "PASS" if final else "PENDING")


if __name__ == "__main__":
    unittest.main()
