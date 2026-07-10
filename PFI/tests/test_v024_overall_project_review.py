from __future__ import annotations

import importlib
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "reports" / "pfi_v024" / "overall_project_review"
EXPECTED_STAGES = [f"Stage {index}" for index in range(10)]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestV024OverallProjectReview(unittest.TestCase):
    def test_overall_contract_closes_stage_0_to_9_without_future_version(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")
        payload = module.build_v024_overall_project_review_payload(ROOT)

        self.assertEqual(payload["schema"], "PFIV024OverallProjectReviewPayloadV1")
        self.assertEqual(payload["target_version"], "v0.2.4")
        self.assertEqual(payload["source_package_version"], "v0.2.3-repair")
        self.assertEqual(payload["review_id"], "v024_overall_project_review")
        self.assertEqual(payload["stage_count"], 10)
        self.assertEqual(payload["stage_sequence"], EXPECTED_STAGES)
        self.assertTrue(payload["stage_8_phase_8_3_user_confirmed"])
        self.assertTrue(payload["stage_9_phase_9_3_user_confirmed"])
        self.assertEqual(payload["user_confirmation_source"], "chat_reply_1")
        self.assertTrue(payload["stage_9_github_main_uploaded"])
        self.assertTrue(payload["overall_project_review_complete"])
        self.assertTrue(payload["github_main_uploaded"])
        self.assertTrue(payload["remote_main_verification_required"])
        self.assertFalse(payload["future_version_started"])
        self.assertFalse(payload["app_bundle_reinstall_executed"])
        self.assertFalse(payload["data_logic_changes_made"])
        self.assertFalse(payload["formal_fake_financial_data_added"])
        expected_storage_mode = "filesystem" if (ROOT.parent / "MetaDatabase" / "PFI").exists() else "git_tree"
        self.assertEqual(payload["data_boundary"]["source_status"], "ready")
        self.assertEqual(payload["data_boundary"]["storage_mode"], expected_storage_mode)
        self.assertEqual(payload["data_boundary"]["alipay_raw_file_count"], 4)
        self.assertEqual(payload["data_boundary"]["alipay_normalized_row_count"], 8815)
        self.assertIn("git push origin HEAD:main", payload["validation_commands"])
        self.assertIn("git ls-remote origin refs/heads/main", payload["validation_commands"])

    def test_overall_filesystem_presence_uses_normalized_data_audit(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            pfi_root = repo_root / "PFI"
            (pfi_root / "src" / "pfi_v02").mkdir(parents=True)
            data_root = repo_root / "MetaDatabase" / "PFI" / "alipay_daily"
            (data_root / "processed").mkdir(parents=True)
            (data_root / "raw").mkdir(parents=True)
            (data_root / "processed" / "alipay_import_manifest.json").write_text(
                json.dumps({"transaction_count": 1, "date_start": "2026-01-01", "date_end": "2026-01-01"}),
                encoding="utf-8",
            )
            (data_root / "processed" / "alipay_transactions.csv").write_text(
                "event_type,amount\nCASH,-1\n",
                encoding="utf-8",
            )
            (data_root / "raw" / "source.csv").write_text("source\nlocal\n", encoding="utf-8")

            payload = module.build_v024_overall_project_review_payload(pfi_root)

        self.assertEqual(payload["data_boundary"]["source_status"], "ready")
        self.assertEqual(payload["data_boundary"]["storage_mode"], "filesystem")
        self.assertTrue(payload["data_boundary"]["pfi_worktree_metadb_present"])

    def test_overall_artifacts_and_audit_are_machine_readable(self) -> None:
        expected_files = [
            ROOT / "docs" / "pfi_v024" / "OVERALL_PROJECT_REVIEW.md",
            REVIEW_DIR / "evidence.json",
            REVIEW_DIR / "review_audit.json",
            REVIEW_DIR / "changed_files.txt",
            REVIEW_DIR / "terminal.log",
            REVIEW_DIR / "risk_and_rollback.md",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = read_json(REVIEW_DIR / "evidence.json")
        audit = read_json(REVIEW_DIR / "review_audit.json")
        changed_files = [
            line.strip()
            for line in (REVIEW_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024OverallProjectReviewEvidenceV1")
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["review_scope"], ["Stage 0-9", "Stage 8-9 accepted manual gates", "overall project delivery gate"])
        self.assertEqual(evidence["stage_sequence"], EXPECTED_STAGES)
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(audit["schema"], "PFIV024OverallProjectReviewAuditV1")
        self.assertEqual(audit["blocker_count"], 0)
        checks = {item["id"]: item["status"] for item in audit["checks"]}
        for check_id in (
            "stage_0_to_9_evidence_chain_complete",
            "stage_8_manual_acceptance_not_blocking",
            "stage_9_manual_acceptance_not_blocking",
            "stage_9_github_main_uploaded",
            "remote_main_verification_required",
            "no_mock_sample_synthetic_fixture_demo_fake_financial_data",
            "future_version_not_started",
        ):
            self.assertEqual(checks[check_id], "pass", check_id)

    def test_overall_binds_current_stage_evidence_and_uploads(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        stage8_upload = read_json(ROOT / "reports" / "pfi_v024" / "stage_8" / "github_main_upload" / "evidence.json")
        stage9_upload = read_json(ROOT / "reports" / "pfi_v024" / "stage_9" / "github_main_upload" / "evidence.json")
        stage8_review = read_json(ROOT / "reports" / "pfi_v024" / "stage_8" / "whole_stage_review" / "evidence.json")
        stage9_review = read_json(ROOT / "reports" / "pfi_v024" / "stage_9" / "whole_stage_review" / "evidence.json")
        guardrails = read_json(ROOT / "reports" / "pfi_v024" / "stage_9" / "phase_9_1" / "regression_guardrails.json")

        self.assertTrue(stage8_upload["github_main_uploaded"])
        self.assertTrue(stage9_upload["github_main_uploaded"])
        self.assertTrue(stage8_review["phase_8_3_user_confirmed"])
        self.assertTrue(stage9_review["phase_9_3_user_confirmed"])
        self.assertTrue(guardrails["all_guardrails_passed"])
        self.assertTrue(evidence["acceptance_checks"]["ten_primary_entries_verified"])
        self.assertTrue(evidence["acceptance_checks"]["market_research_primary_entry_verified"])
        self.assertTrue(evidence["acceptance_checks"]["stage_8_user_confirmed_by_reply_1"])
        self.assertTrue(evidence["acceptance_checks"]["stage_9_user_confirmed_by_reply_1"])
        self.assertTrue(evidence["acceptance_checks"]["stage_9_upload_remote_verified"])
        self.assertTrue(evidence["acceptance_checks"]["all_guardrails_passed"])

    def test_docs_status_stop_after_overall_upload(self) -> None:
        docs = [
            ROOT / "README.md",
            ROOT / "HANDOFF.md",
            ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md",
            ROOT / "docs" / "pfi_v024" / "OVERALL_PROJECT_REVIEW.md",
            ROOT / "CHANGELOG.md",
            ROOT / "功能清单.md",
            ROOT / "开发记录.md",
            ROOT / "模型参数文件.md",
        ]
        for path in docs:
            text = path.read_text(encoding="utf-8")
            self.assertIn("v0.2.4 overall project review", text, str(path))
            self.assertIn("Stage 8.3 用户验收已由用户回复 `1` 确认", text, str(path))
            self.assertIn("Stage 9.3 用户验收已由用户回复 `1` 确认", text, str(path))
            self.assertIn("future version 未开始", text, str(path))

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Overall project review: pass", readme)
        self.assertIn("GitHub main upload after overall review: complete", readme)
        self.assertNotIn("future version started", readme)

        model_parameters = (ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        self.assertIn("MOD-PFI-001", model_parameters)
        self.assertNotIn("MOD-PFI-V024-OVERALL", model_parameters)


if __name__ == "__main__":
    unittest.main()
