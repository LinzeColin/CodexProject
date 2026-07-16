from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
WEB_ROOT = PFI_ROOT / "web"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_8/whole_stage_review"
REVIEW_BASE = "2c7b25efd2916c909027333283b499a119d088e0"


class Stage8WholeReviewRemediationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        cls.shell = (WEB_ROOT / "app/shell.js").read_text(encoding="utf-8")
        cls.timeline = (WEB_ROOT / "app/components/jobTimeline.js").read_text(encoding="utf-8")
        cls.css = (WEB_ROOT / "styles/tokens.css").read_text(encoding="utf-8")
        cls.phase81 = (WEB_ROOT / "tests/v025/stage8_phase81_cdp.mjs").read_text(encoding="utf-8")
        cls.phase83 = (WEB_ROOT / "tests/v025/stage8_phase83_cdp.mjs").read_text(encoding="utf-8")
        finalizer_path = WEB_ROOT / "tests/v025/stage8_whole_review_finalize.py"
        spec = importlib.util.spec_from_file_location("stage8_whole_review_finalize", finalizer_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load Stage 8 finalizer")
        cls.finalizer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.finalizer)

    def test_non_home_pages_hide_home_questions_and_render_real_workspace_shapes(self) -> None:
        self.assertIn("data-stage8-home-only", self.index)
        self.assertIn("data-stage8-workspace-focus", self.index)
        self.assertRegex(
            self.shell,
            r"homeOnly\.hidden\s*=\s*!isHome",
        )
        self.assertIn("renderStage8WorkspaceFocus", self.shell)
        self.assertIn("actualDomSignature", self.phase81)
        signature_block = re.search(
            r"const layoutSignature = \[(.*?)\]\.join\(\"\|\"\);",
            self.phase81,
            re.S,
        )
        self.assertIsNotNone(signature_block)
        self.assertNotIn("expectedArchetype", signature_block.group(1))

    def test_global_click_feedback_never_auto_declares_success(self) -> None:
        listener = re.search(
            r"function bindClickSafeFeedback\(\) \{(.*?)\n\}",
            self.shell,
            re.S,
        )
        self.assertIsNotNone(listener)
        self.assertNotIn('setActionFeedback("success"', listener.group(1))
        self.assertNotIn('setActionFeedback("progress"', listener.group(1))
        self.assertNotIn("window.setTimeout", listener.group(1))

    def test_persisted_holding_soft_delete_requires_explicit_confirmation(self) -> None:
        self.assertIn("data-holdings-delete-dialog", self.index)
        self.assertIn("data-holdings-delete-confirm", self.index)
        binding = re.search(
            r"function bindHoldingsPersistenceEvents\(\) \{(.*?)\n\}",
            self.shell,
            re.S,
        )
        self.assertIsNotNone(binding)
        self.assertIn("requestHoldingSoftDelete", binding.group(1))
        self.assertNotIn("softDeleteHoldingRow", binding.group(1))
        self.assertIn("confirmHoldingSoftDelete", self.shell)

    def test_all_interactive_links_use_the_44px_stage8_gate(self) -> None:
        self.assertRegex(
            self.css,
            r":where\(\s*a\[href\],\s*button,",
        )
        self.assertIn("const required = 44;", self.phase83)
        self.assertNotIn('? 44 : 24', self.phase83)

    def test_job_timeline_storage_contains_only_opaque_state_and_counts(self) -> None:
        persist = re.search(r"function persist\(\) \{(.*?)\n  \}", self.timeline, re.S)
        self.assertIsNotNone(persist)
        self.assertNotIn("label: job.label", persist.group(1))
        self.assertNotIn("stageLabel: job.stageLabel", persist.group(1))
        self.assertIn('storageFields: Object.freeze(["id", "state", "startedAt", "updatedAt", "completedUnits", "totalUnits"])', self.timeline)

    def test_whole_review_has_normalized_roadmap_evidence_names(self) -> None:
        for name in (
            "design_tokens.json",
            "reduced_motion.json",
            "keyboard_flow.json",
            "axe_results.json",
            "contrast_results.json",
        ):
            with self.subTest(name=name):
                payload = json.loads((REVIEW_DIR / name).read_text(encoding="utf-8"))
                self.assertIsInstance(payload, dict)

    def test_current_browser_evidence_covers_distinct_primary_and_secondary_routes(self) -> None:
        browser = json.loads(
            (REVIEW_DIR / "final_browser/browser_validation.json").read_text(encoding="utf-8")
        )
        visual = json.loads(
            (REVIEW_DIR / "final_browser/visual_regression.json").read_text(encoding="utf-8")
        )
        wcag = json.loads(
            (REVIEW_DIR / "final_browser/wcag_audit.json").read_text(encoding="utf-8")
        )
        ax = json.loads(
            (REVIEW_DIR / "final_browser/accessibility_tree.json").read_text(encoding="utf-8")
        )
        self.assertEqual("pass", browser["status"])
        self.assertEqual((10, 10, 40), (
            browser["audited_primary_page_count"],
            browser["audited_secondary_page_count"],
            browser["screenshot_count"],
        ))
        self.assertEqual((20, 20, 40), (
            visual["unique_route_count"],
            wcag["unique_route_count"],
            visual["screenshot_count"],
        ))
        self.assertEqual(20, ax["unique_route_count"])
        self.assertEqual(0, max(row["near_black_ratio"] for row in visual["results"]))

    def test_axe_unavailability_is_truthful_and_substitute_is_explicit(self) -> None:
        axe = json.loads((REVIEW_DIR / "axe_results.json").read_text(encoding="utf-8"))
        self.assertEqual("not_run", axe["status"])
        self.assertIs(False, axe["axe_core_available"])
        self.assertIs(False, axe["axe_pass_claimed"])
        self.assertEqual("pass", axe["substitute_status"])

    def test_phase_commits_and_historical_artifacts_are_content_bound(self) -> None:
        binding = json.loads(
            (REVIEW_DIR / "phase_commit_binding.json").read_text(encoding="utf-8")
        )
        self.assertEqual("pass", binding["status"])
        self.assertIs(True, binding["linear_commit_chain"])
        self.assertEqual(12, binding["phase_task_count"])
        self.assertEqual(
            {"8.1", "8.2", "8.3"},
            set(binding["phase_commits"]),
        )
        for row in binding["phase_bindings"]:
            self.assertIs(True, row["all_artifact_hashes_match"])
            self.assertEqual(row["artifact_count"], row["artifact_hash_match_count"])

    def test_taskpack_normalization_preserves_phase_scope_truth(self) -> None:
        binding = json.loads(
            (REVIEW_DIR / "phase_evidence_amendment_binding.json").read_text(encoding="utf-8")
        )
        self.assertEqual("pass", binding["status"])
        self.assertIs(True, binding["all_normalized_evidence_schema_valid"])
        rows = {row["phase"]: row for row in binding["phase_evidence"]}
        self.assertIs(True, rows["8.1"]["allowed_files_obeyed"])
        self.assertIs(False, rows["8.2"]["allowed_files_obeyed"])
        self.assertIs(True, rows["8.3"]["allowed_files_obeyed"])
        self.assertTrue(all(row["immutable_original_preserved"] for row in rows.values()))

    def test_release_identity_binds_the_product_remediation_commit(self) -> None:
        release = json.loads(
            (REVIEW_DIR / "release_identity_binding.json").read_text(encoding="utf-8")
        )
        self.assertEqual("pass", release["status"])
        self.assertEqual(REVIEW_BASE, release["product_content_commit"])
        self.assertIs(True, release["embedded_manifest_equal"])

    def test_current_review_uses_no_finder_or_launchservices(self) -> None:
        contract = json.loads((REVIEW_DIR / "phase_contract.json").read_text(encoding="utf-8"))
        self.assertIs(False, contract["finder_used"])
        self.assertIs(False, contract["launchservices_used_in_current_review"])
        self.assertIs(False, contract["external_network_performed"])
        self.assertIs(False, contract["push_performed"])
        self.assertIs(False, contract["app_install_performed"])

    def test_finalizer_rejects_empty_or_non_exact_verification_commands(self) -> None:
        current = {
            "base_commit": REVIEW_BASE,
            "file_count": 1,
            "files": [{"path": "PFI/example", "sha256": "sha256:source"}],
            "content_manifest_sha256": "sha256:source-overlay",
        }
        commands = [
            {
                "command_id": command_id,
                "command": f"verify {command_id}",
                "subcommands": [f"verify {command_id}"],
                "exit_code": 0,
                "output_ref": output_ref,
                "output_sha256": "sha256:" + "a" * 64,
            }
            for command_id, output_ref in self.finalizer.REQUIRED_VERIFICATION_COMMANDS.items()
        ]
        valid = {
            "status": "pass",
            "overlay_stable_during_verification": True,
            "verified_overlay": current,
            "commands": commands,
        }
        self.assertEqual(3, len(self.finalizer._validate_verification_payload(valid, current)))
        with self.assertRaises(RuntimeError):
            self.finalizer._validate_verification_payload({**valid, "commands": []}, current)
        with self.assertRaises(RuntimeError):
            self.finalizer._validate_verification_payload(
                {**valid, "commands": [commands[0], commands[0], commands[2]]}, current
            )

    def test_finalizer_requires_exact_three_unique_reviewers_and_evidence_binding(self) -> None:
        overlay = {"file_count": 22, "content_manifest_sha256": "sha256:source"}
        evidence_overlay = {"file_count": 100, "content_manifest_sha256": "sha256:evidence"}
        rows = []
        for reviewer_id, initial_counts in self.finalizer.REQUIRED_REVIEWERS.items():
            result_text = f"ACCEPT — {reviewer_id} C0/I0/M0"
            rows.append({
                "reviewer_id": reviewer_id,
                "decision": "ACCEPT",
                "counts": {"critical": 0, "important": 0, "minor": 0},
                "initial_counts": initial_counts,
                "review_base": REVIEW_BASE,
                "reviewed_overlay_file_count": 22,
                "reviewed_overlay_sha256": "sha256:source",
                "reviewed_evidence_file_count": 100,
                "reviewed_evidence_sha256": "sha256:evidence",
                "result_text": result_text,
                "result_sha256": "sha256:" + hashlib.sha256(result_text.encode()).hexdigest(),
            })
        valid = {
            "status": "pass",
            "reviewers": rows,
            "contains_private_values": False,
            "finder_used": False,
            "launchservices_used": False,
            "external_network_performed": False,
        }
        self.assertEqual(
            3,
            len(self.finalizer._validate_reviewer_payload(valid, overlay, evidence_overlay)),
        )
        with self.assertRaises(RuntimeError):
            self.finalizer._validate_reviewer_payload(
                {**valid, "reviewers": [*rows, rows[0], "ignored-garbage"]},
                overlay,
                evidence_overlay,
            )
        tampered = json.loads(json.dumps(valid))
        tampered["reviewers"][0]["reviewed_evidence_sha256"] = "sha256:tampered"
        with self.assertRaises(RuntimeError):
            self.finalizer._validate_reviewer_payload(tampered, overlay, evidence_overlay)

    def test_reviewed_evidence_manifest_hashes_every_frozen_file(self) -> None:
        manifest = json.loads(
            (REVIEW_DIR / "reviewed_evidence_overlay.json").read_text(encoding="utf-8")
        )
        self.assertEqual("frozen", manifest["status"])
        self.assertGreater(manifest["file_count"], 50)
        records = bytearray()
        for row in manifest["files"]:
            path = REPO_ROOT / row["path"]
            actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(row["sha256"], actual)
            records.extend(f"{row['path']}\0{row['sha256']}\n".encode())
        self.assertEqual(manifest["file_count"], len(manifest["files"]))
        self.assertEqual(
            manifest["content_manifest_sha256"],
            "sha256:" + hashlib.sha256(records).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
