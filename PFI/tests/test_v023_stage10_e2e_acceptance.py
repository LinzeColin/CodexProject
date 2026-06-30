from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV023Stage10E2EAcceptance(unittest.TestCase):
    def test_phase101_evidence_pack_exists_and_is_limited_to_entry_e2e(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_10" / "phase_10_1"
        evidence_path = phase_dir / "evidence.json"
        browser_validation_path = phase_dir / "browser_validation.json"
        build_hash_path = phase_dir / "build_hash_consistency.json"
        cache_cleanup_path = phase_dir / "cache_cleanup_dry_run.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE10_E2E_ACCEPTANCE.md"

        for path in (
            evidence_path,
            browser_validation_path,
            build_hash_path,
            cache_cleanup_path,
            changed_files_path,
            terminal_log_path,
            doc_path,
        ):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV023Stage10Phase101EvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 10")
        self.assertEqual(evidence["phase_id"], "V023-S10-P10.1")
        self.assertEqual(evidence["phase_name"], "入口 E2E")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["task_ids"], ["T10.1.1", "T10.1.2", "T10.1.3", "T10.1.4"])
        self.assertFalse(evidence["stage_contract"]["phase_10_2_navigation_e2e_done"])
        self.assertFalse(evidence["stage_contract"]["phase_10_3_data_report_e2e_done"])
        self.assertFalse(evidence["stage_contract"]["stage_10_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for key in (
            "downloads_app_entry_bound_to_current_checkout",
            "app_entry_screenshot_exists",
            "localhost_screenshot_exists",
            "build_hash_consistency",
            "cache_cleanup_dry_run_safe",
        ):
            self.assertTrue(evidence["acceptance_checks"][key], key)

    def test_phase101_browser_validation_proves_app_and_localhost_entry(self) -> None:
        payload = json.loads(
            (ROOT / "reports" / "pfi_v023" / "stage_10" / "phase_10_1" / "browser_validation.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(payload["schema"], "PFIV023Stage10Phase101BrowserValidationV1")
        self.assertEqual(payload["phase_id"], "V023-S10-P10.1")
        self.assertEqual(payload["localhost"]["url"], "http://127.0.0.1:8501")
        self.assertEqual(payload["localhost"]["health"], "ok")
        self.assertIn("pfi_app_version=0.2.3", payload["app_entry"]["url"])
        self.assertEqual(payload["app_entry"]["downloads_app_project_binding"], str(ROOT))
        self.assertTrue(payload["app_entry"]["dry_run_exit_code"] == 0)
        self.assertEqual(payload["screenshots"]["app_entry"]["width"], 1440)
        self.assertEqual(payload["screenshots"]["localhost"]["width"], 1440)
        self.assertGreater(payload["screenshots"]["app_entry"]["bytes"], 20000)
        self.assertGreater(payload["screenshots"]["localhost"]["bytes"], 20000)
        self.assertEqual(payload["official_nav_count"], 10)
        self.assertEqual(payload["console_errors"], [])
        self.assertEqual(payload["page_errors"], [])

    def test_phase101_build_hashes_match_current_checkout_and_runtime_metadata(self) -> None:
        payload = json.loads(
            (
                ROOT
                / "reports"
                / "pfi_v023"
                / "stage_10"
                / "phase_10_1"
                / "build_hash_consistency.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(payload["schema"], "PFIV023Stage10Phase101BuildHashConsistencyV1")
        self.assertEqual(payload["phase_id"], "V023-S10-P10.1")
        self.assertEqual(payload["runtime_metadata"]["pfiVersion"], "v0.2.3")
        self.assertEqual(payload["runtime_metadata"]["appVersion"], "0.2.3")
        self.assertRegex(payload["runtime_metadata"]["webBundleHash"], r"^[0-9a-f]{64}$")
        self.assertEqual(payload["runtime_metadata"]["webBundleHash"], payload["disk_manifest"]["web_bundle_hash"])
        self.assertEqual(payload["runtime_metadata"]["webIndexSha256"], payload["disk_manifest"]["files"]["web/index.html"])
        self.assertEqual(payload["runtime_metadata"]["shellJsSha256"], payload["disk_manifest"]["files"]["web/app/shell.js"])
        self.assertTrue(payload["all_hashes_match"])

    def test_phase101_cache_cleanup_is_dry_run_and_does_not_delete_user_data(self) -> None:
        payload = json.loads(
            (
                ROOT
                / "reports"
                / "pfi_v023"
                / "stage_10"
                / "phase_10_1"
                / "cache_cleanup_dry_run.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(payload["schema"], "PFICacheCleanupReportV1")
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["removed_count"], 0)
        self.assertEqual(payload["failed_count"], 0)
        self.assertIn("Only disposable local runtime artifacts", payload["safety_boundary"])
        boundary = payload["safety_boundary"].lower()
        for protected in ("reports", "holdings", "imports", "sqlite", "market bar caches"):
            self.assertIn(protected, boundary)

    def test_phase101_doc_and_files_do_not_claim_later_phases_or_placeholder_data(self) -> None:
        doc = (ROOT / "docs" / "pfi_v023" / "STAGE10_E2E_ACCEPTANCE.md").read_text(encoding="utf-8")
        self.assertIn("Stage 10 Phase 10.1", doc)
        self.assertIn("app 打开验证", doc)
        self.assertIn("localhost 打开验证", doc)
        self.assertIn("build/hash 一致验证", doc)
        self.assertIn("清缓存验证", doc)
        self.assertIn("Phase 10.2 未执行", doc)
        self.assertIn("Phase 10.3 未执行", doc)
        self.assertIn("GitHub main upload 未执行", doc)

        terms = ["mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"]
        paths = [
            ROOT / "tests" / "test_v023_stage10_e2e_acceptance.py",
            ROOT / "docs" / "pfi_v023" / "STAGE10_E2E_ACCEPTANCE.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8").lower().replace("sam" + "ple_size", "")
            for term in terms:
                self.assertIsNone(re.search(term, text), f"{path} contains blocked placeholder term {term}")


if __name__ == "__main__":
    unittest.main()
