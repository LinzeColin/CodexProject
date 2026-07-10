from __future__ import annotations

import importlib
import inspect
import hashlib
import json
import plistlib
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestV024FinalDelivery(unittest.TestCase):
    def setUp(self) -> None:
        self.module = importlib.import_module("pfi_v02.stage_v024_final_delivery")

    def test_live_builder_cannot_accept_injected_completion_flags(self) -> None:
        parameters = inspect.signature(self.module.build_v024_final_delivery_payload).parameters

        self.assertEqual(set(parameters), {"pfi_root"})

    def test_final_delivery_passes_only_when_git_app_and_runtime_proofs_pass(self) -> None:
        git_audit = self._passing_git_audit()
        app_audit = self._passing_app_audit()
        evidence_audit = {"status": "pass", "issues": []}

        payload = self.module.evaluate_v024_final_delivery(git_audit, app_audit, evidence_audit)

        self.assertEqual(payload["schema"], "PFIV024FinalDeliveryPayloadV1")
        self.assertEqual(payload["acceptance_id"], "ACC-PFI-V024-FINAL-DELIVERY")
        self.assertEqual(payload["gate_result"], "pass")
        self.assertTrue(payload["product_goal_complete"])
        self.assertIsNone(payload["next_gate"])

    def test_final_delivery_fails_closed_for_each_delivery_boundary(self) -> None:
        cases = {
            "remote_sha_mismatch": (
                {**self._passing_git_audit(), "status": "fail", "issues": ["remote_main_mismatch"]},
                self._passing_app_audit(),
                {"status": "pass", "issues": []},
            ),
            "dirty_worktree": (
                {**self._passing_git_audit(), "status": "fail", "issues": ["worktree_not_clean"]},
                self._passing_app_audit(),
                {"status": "pass", "issues": []},
            ),
            "app_binding_drift": (
                self._passing_git_audit(),
                {**self._passing_app_audit(), "status": "fail", "issues": ["downloads:binding_mismatch"]},
                {"status": "pass", "issues": []},
            ),
            "runtime_failed": (
                self._passing_git_audit(),
                self._passing_app_audit(),
                {"status": "fail", "issues": ["runtime_acceptance_failed"]},
            ),
        }

        for name, (git_audit, app_audit, evidence_audit) in cases.items():
            with self.subTest(name=name):
                payload = self.module.evaluate_v024_final_delivery(git_audit, app_audit, evidence_audit)
                self.assertEqual(payload["gate_result"], "fail")
                self.assertFalse(payload["product_goal_complete"])
                self.assertEqual(payload["next_gate"], "PFI-V024-FINAL-DELIVERY")

    def test_app_audit_checks_all_entries_binding_versions_signing_and_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            pfi_root = (tmp_root / "checkout" / "PFI").resolve()
            source_app = pfi_root / "macos" / "PFI.app"
            app_paths = {
                "applications": tmp_root / "Applications" / "PFI.app",
                "downloads": tmp_root / "Downloads" / "PFI.app",
                "desktop": tmp_root / "Desktop" / "PFI.app",
            }
            self._write_app(source_app, pfi_root)
            self._write_app(app_paths["applications"], pfi_root)
            self._write_app(app_paths["downloads"], pfi_root)
            app_paths["desktop"].parent.mkdir(parents=True)
            app_paths["desktop"].symlink_to(app_paths["applications"])

            def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if command[0] == "/usr/bin/codesign":
                    return subprocess.CompletedProcess(command, 0, "", "")
                return subprocess.CompletedProcess(
                    command,
                    0,
                    (
                        f"PFI_APP_LAUNCH: project={pfi_root} command=./StartPFI.command "
                        f"command_path={pfi_root / 'StartPFI.command'} mode=spawn-command\n"
                    ),
                    "",
                )

            launcher_fingerprint = (
                "sha256:"
                + hashlib.sha256(
                    (app_paths["applications"] / "Contents" / "MacOS" / "PFI").read_bytes()
                ).hexdigest()
            )

            audit = self.module.audit_v024_installed_apps(
                pfi_root,
                app_paths=app_paths,
                command_runner=runner,
                expected_launcher_fingerprint=launcher_fingerprint,
            )

            self.assertEqual(audit["status"], "pass")
            self.assertEqual(audit["issues"], [])
            self.assertEqual(set(audit["entries"]), {"applications", "downloads", "desktop"})
            self.assertEqual(len(set(audit["launcher_fingerprints"])), 1)
            self.assertEqual(len(set(audit["launcher_code_fingerprints"])), 1)
            self.assertEqual(len(set(audit["plist_fingerprints"])), 1)

            old_launcher = self.module.audit_v024_installed_apps(
                pfi_root,
                app_paths=app_paths,
                command_runner=runner,
                expected_launcher_fingerprint="sha256:new-launcher",
            )

            (app_paths["downloads"] / "Contents" / "Resources" / "PFI_PROJECT_ROOT").write_text(
                "/wrong/PFI\n",
                encoding="utf-8",
            )
            drift = self.module.audit_v024_installed_apps(
                pfi_root,
                app_paths=app_paths,
                command_runner=runner,
                expected_launcher_fingerprint=launcher_fingerprint,
            )

        self.assertTrue(any("compiled_launcher_mismatch" in issue for issue in old_launcher["issues"]))
        self.assertEqual(drift["status"], "fail")
        self.assertTrue(any("binding_mismatch" in issue for issue in drift["issues"]))

    def test_git_audit_requires_live_remote_clean_tree_and_direct_product_parent(self) -> None:
        head = "a" * 40
        product_commit = "b" * 40
        responses = {
            ("git", "rev-parse", "--abbrev-ref", "HEAD"): "codex/pfi\n",
            ("git", "rev-parse", "--abbrev-ref", "@{upstream}"): "origin/main\n",
            ("git", "remote", "get-url", "origin"): "git@github.com:LinzeColin/CodexProject.git\n",
            ("git", "rev-parse", "HEAD^{commit}"): f"{head}\n",
            ("git", "rev-parse", "refs/remotes/origin/main^{commit}"): f"{head}\n",
            ("git", "rev-parse", "HEAD^1^{commit}"): f"{product_commit}\n",
            ("git", "status", "--porcelain=v1", "--untracked-files=all"): "",
            ("git", "rev-parse", "HEAD:PFI"): f"{'c' * 40}\n",
            ("git", "ls-remote", "origin", "refs/heads/main"): f"{head}\trefs/heads/main\n",
            ("git", "merge-base", "--is-ancestor", product_commit, head): "",
        }

        def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            key = tuple(command)
            return subprocess.CompletedProcess(command, 0 if key in responses else 1, responses.get(key, ""), "")

        with tempfile.TemporaryDirectory() as tmp:
            pfi_root = Path(tmp) / "PFI"
            pfi_root.mkdir()
            passing = self.module.audit_v024_git_delivery(
                pfi_root,
                product_commit=product_commit,
                command_runner=runner,
            )
            wrong_parent = self.module.audit_v024_git_delivery(
                pfi_root,
                product_commit="d" * 40,
                command_runner=runner,
            )

        self.assertEqual(passing["status"], "pass")
        self.assertTrue(passing["product_commit_is_parent"])
        self.assertEqual(wrong_parent["status"], "fail")
        self.assertIn("product_commit_not_direct_parent", wrong_parent["issues"])

    def test_delivery_evidence_rejects_wrong_commit_fingerprint_and_runtime(self) -> None:
        app_audit = self._passing_app_audit()
        evidence = self._passing_evidence(app_audit)
        runtime_audit = self._passing_runtime_audit(evidence["runtime_snapshot"])

        self.assertEqual(
            self.module.validate_v024_final_delivery_evidence(evidence, app_audit, runtime_audit),
            [],
        )

        evidence["product_commit"] = "not-a-commit"
        bad_commit = self.module.validate_v024_final_delivery_evidence(evidence, app_audit, runtime_audit)
        evidence = self._passing_evidence(app_audit)
        evidence["app_fingerprints"]["launcher_sha256"] = ["sha256:wrong"]
        bad_fingerprint = self.module.validate_v024_final_delivery_evidence(evidence, app_audit, runtime_audit)
        evidence = self._passing_evidence(app_audit)
        evidence["runtime_snapshot"]["status"] = "Blocked"
        bad_runtime = self.module.validate_v024_final_delivery_evidence(evidence, app_audit, runtime_audit)

        self.assertIn("product_commit_invalid", bad_commit)
        self.assertIn("app_fingerprint_mismatch", bad_fingerprint)
        self.assertIn("runtime_snapshot_failed", bad_runtime)

    def test_runtime_audit_executes_probe_and_rejects_self_reported_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pfi_root = (Path(tmp) / "PFI").resolve()
            pfi_root.mkdir()
            loaded_assets = {}
            for relative in (
                "web/styles/tokens.css",
                "web/app/version.js",
                "web/app/entry_audit.js",
                "web/app/routes.js",
                "web/app/shell.js",
            ):
                asset = pfi_root / relative
                asset.parent.mkdir(parents=True, exist_ok=True)
                asset.write_text(relative, encoding="utf-8")
                loaded_assets[relative] = hashlib.sha256(relative.encode("utf-8")).hexdigest()
            snapshot = {
                "schema": "PFIV024ReadOnlyRuntimeSnapshotV1",
                "status": "Pass",
                "mode": "read_only_no_pfi_data_or_reports_write",
                "summary": {"pass": 7, "fail": 0, "total": 7},
                "healthy_urls": ["http://127.0.0.1:8501/_stcore/health"],
                "disk_web_bundle_hash": "c" * 64,
                "runtime_web_bundle_hashes": {"app": "c" * 64, "localhost": "c" * 64},
                "app_localhost_same_bundle_hash": True,
                "runtime_disk_bundle_hash_match": True,
                "loaded_asset_sha256": loaded_assets,
                "loaded_asset_sha256_by_entry": {
                    "app": loaded_assets,
                    "localhost": loaded_assets,
                },
                "loaded_assets_match_disk": True,
                "project_roots": [str(pfi_root)],
                "app_paths": ["/Applications/PFI.app"],
                "build_ids": ["pfi-v024-stage2-phase22"],
                "ui_contract_versions": ["PFI-V024-STAGE2-ENTRY-CONSISTENCY"],
                "repair_labels": ["PFI v0.2.3 Repair"],
                "console_errors": [],
                "page_errors": [],
                "http_errors": [],
            }

            def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(command, 0, json.dumps(snapshot), "")

            audit = self.module.audit_v024_read_only_runtime(
                pfi_root,
                command_runner=runner,
                expected_bundle_hash="c" * 64,
            )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(audit["snapshot"], snapshot)

        app_audit = self._passing_app_audit()
        evidence = self._passing_evidence(app_audit)
        evidence["runtime_snapshot"] = {**snapshot, "healthy_urls": ["http://forged.invalid"]}
        issues = self.module.validate_v024_final_delivery_evidence(evidence, app_audit, audit)
        self.assertIn("runtime_snapshot_mismatch", issues)

    def test_runtime_shell_exposes_filename_bound_inline_assets(self) -> None:
        source = (ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

        for relative in (
            "web/styles/tokens.css",
            "web/app/version.js",
            "web/app/entry_audit.js",
            "web/app/routes.js",
            "web/app/shell.js",
        ):
            self.assertIn(f'data-pfi-source="{relative}"', source)

    def test_launcher_build_is_reproducible_before_app_signing(self) -> None:
        installer = (ROOT / "scripts" / "installPFIEntryApps.sh").read_text(encoding="utf-8")
        auditor = (ROOT / "src" / "pfi_v02" / "stage_v024_final_delivery.py").read_text(encoding="utf-8")

        self.assertIn('BUILT_LAUNCHER_BINARY="$BUILT_LAUNCHER_DIR/PFI"', installer)
        self.assertIn("-Wl,-no_uuid", installer)
        self.assertIn('"-Wl,-no_uuid"', auditor)

    def test_macho_fingerprint_hashes_sections_not_signature_envelope(self) -> None:
        otool_output = """Section
  sectname __text
   segname __TEXT
      addr 0x0000000000000000
      size 0x0000000000000004
    offset 8
     align 2^2
Section
  sectname __cstring
   segname __TEXT
      addr 0x0000000000000004
      size 0x0000000000000003
    offset 16
     align 2^0
"""

        def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, otool_output, "")

        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "PFI"
            binary.write_bytes(b"SIGNSIGN" + b"CODE" + b"pad!" + b"TXT" + b"tail")
            first = self.module._macho_section_fingerprint(binary, runner, Path(tmp))
            binary.write_bytes(b"DIFFSIGN" + b"CODE" + b"pad!" + b"TXT" + b"tail")
            signature_only_change = self.module._macho_section_fingerprint(binary, runner, Path(tmp))
            binary.write_bytes(b"DIFFSIGN" + b"FAIL" + b"pad!" + b"TXT" + b"tail")
            code_change = self.module._macho_section_fingerprint(binary, runner, Path(tmp))

        self.assertEqual(first, signature_only_change)
        self.assertNotEqual(first, code_change)

    def test_canonical_records_close_only_after_delivery_evidence_exists(self) -> None:
        project = (ROOT / "docs" / "governance" / "project.yaml").read_text(encoding="utf-8")
        roadmap = (ROOT / "docs" / "governance" / "roadmap.yaml").read_text(encoding="utf-8")
        evidence_path = ROOT / "docs" / "pfi_v024" / "FINAL_DELIVERY_EVIDENCE.json"

        if evidence_path.exists():
            delivery = (ROOT / "docs" / "pfi_v024" / "FINAL_DELIVERY.md").read_text(encoding="utf-8")
            self.assertIn('current_status: "v024_final_delivery_pending_live_verifier"', project)
            self.assertIn('next_gate_id: "PFI-V024-FINAL-DELIVERY"', roadmap)
            self.assertIn("completion_predicate:", project)
            self.assertIn("second_closeout_commit_allowed: false", roadmap)
            self.assertIn("ACC-PFI-V024-FINAL-DELIVERY", delivery)
            self.assertIn("pending_live_verifier", delivery)
            self.assertIn("future version 未开始", delivery)
            self.assertIn("不包含交易密码、券商订单、支付或自动真钱动作", delivery)
        else:
            self.assertIn('current_status: "v024_overall_rereview_pass_pending_final_delivery"', project)
            self.assertIn('next_gate_id: "PFI-V024-FINAL-DELIVERY"', roadmap)

    def _write_app(self, app_path: Path, pfi_root: Path) -> None:
        contents = app_path / "Contents"
        macos = contents / "MacOS"
        resources = contents / "Resources"
        macos.mkdir(parents=True)
        resources.mkdir(parents=True)
        with (contents / "Info.plist").open("wb") as handle:
            plistlib.dump(
                {
                    "CFBundleIdentifier": "com.linze.pfi",
                    "CFBundleShortVersionString": "0.2.3",
                    "CFBundleVersion": "20260629.1",
                },
                handle,
            )
        launcher = macos / "PFI"
        launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        launcher.chmod(0o755)
        (resources / "PFI_PROJECT_ROOT").write_text(f"{pfi_root}\n", encoding="utf-8")

    @staticmethod
    def _passing_git_audit() -> dict[str, object]:
        return {
            "status": "pass",
            "issues": [],
            "head": "a" * 40,
            "remote_main": "a" * 40,
            "origin_tracking": "a" * 40,
            "worktree_clean": True,
            "product_commit_is_ancestor": True,
            "product_commit_is_parent": True,
        }

    @staticmethod
    def _passing_app_audit() -> dict[str, object]:
        return {
            "status": "pass",
            "issues": [],
            "launcher_fingerprints": ["sha256:launcher"],
            "launcher_code_fingerprints": ["sha256:launcher-code"],
            "plist_fingerprints": ["sha256:plist"],
            "entries": {},
        }

    @staticmethod
    def _passing_evidence(app_audit: dict[str, object]) -> dict[str, object]:
        return {
            "schema": "PFIV024FinalDeliveryEvidenceV1",
            "acceptance_id": "ACC-PFI-V024-FINAL-DELIVERY",
            "target_version": "v0.2.4",
            "source_package_version": "v0.2.3-repair",
            "product_commit": "b" * 40,
            "install_command": "PFI/scripts/installPFIEntryApps.sh --all",
            "app_fingerprints": {
                "launcher_sha256": app_audit["launcher_fingerprints"],
                "launcher_code_sha256": app_audit["launcher_code_fingerprints"],
                "info_plist_sha256": app_audit["plist_fingerprints"],
            },
            "app_acceptance": {
                "schema": "PFIOSMacOSAppAcceptanceLiteV1",
                "status": "Pass",
                "summary": {"fail": 0},
            },
            "runtime_snapshot": {
                "schema": "PFIV024ReadOnlyRuntimeSnapshotV1",
                "status": "Pass",
                "mode": "read_only_no_pfi_data_or_reports_write",
                "summary": {"pass": 7, "fail": 0, "total": 7},
                "healthy_urls": ["http://127.0.0.1:8501/_stcore/health"],
                "disk_web_bundle_hash": "c" * 64,
                "runtime_web_bundle_hashes": {"app": "c" * 64, "localhost": "c" * 64},
                "app_localhost_same_bundle_hash": True,
                "runtime_disk_bundle_hash_match": True,
                "loaded_asset_sha256": {"web/app/shell.js": "d" * 64},
                "loaded_asset_sha256_by_entry": {
                    "app": {"web/app/shell.js": "d" * 64},
                    "localhost": {"web/app/shell.js": "d" * 64},
                },
                "loaded_assets_match_disk": True,
                "project_roots": [str(ROOT)],
                "app_paths": ["/Applications/PFI.app"],
                "build_ids": ["pfi-v024-stage2-phase22"],
                "ui_contract_versions": ["PFI-V024-STAGE2-ENTRY-CONSISTENCY"],
                "repair_labels": ["PFI v0.2.3 Repair"],
                "console_errors": [],
                "page_errors": [],
                "http_errors": [],
            },
            "protected_paths": {
                "before_metadata_sha256": "sha256:protected",
                "after_metadata_sha256": "sha256:protected",
                "mutated": False,
            },
            "independent_review": {"status": "approved", "findings": []},
        }

    @staticmethod
    def _passing_runtime_audit(snapshot: object) -> dict[str, object]:
        return {"status": "pass", "issues": [], "snapshot": snapshot, "stderr": ""}


if __name__ == "__main__":
    unittest.main()
