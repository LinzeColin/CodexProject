from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestV024OverallRereview(unittest.TestCase):
    def test_rereview_audits_stage_evidence_and_real_data(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")

        payload = module.build_v024_overall_rereview_payload(ROOT)

        self.assertEqual(payload["schema"], "PFIV024OverallRereviewPayloadV1")
        self.assertEqual(payload["acceptance_id"], "ACC-PFI-V024-OVERALL-REREVIEW")
        self.assertEqual(payload["gate_result"], "pass")
        self.assertEqual(payload["stage_evidence"]["expected_unit_count"], 40)
        self.assertEqual(payload["stage_evidence"]["complete_unit_count"], 40)
        self.assertEqual(payload["stage_evidence"]["whole_stage_pass_count"], 10)
        self.assertEqual(payload["stage_evidence"]["missing_artifacts"], [])
        self.assertEqual(payload["stage_evidence"]["json_parse_errors"], [])
        self.assertEqual(payload["stage_evidence"]["blocking_statuses"], [])
        self.assertEqual(len(payload["stage_evidence"]["manual_acceptance_pending_units"]), 2)
        self.assertEqual(
            set(payload["stage_evidence"]["manual_acceptance_pending_units"]),
            {
                "PFI/reports/pfi_v024/stage_8/phase_8_3/evidence.json",
                "PFI/reports/pfi_v024/stage_9/phase_9_3/evidence.json",
            },
        )
        for stage in (2, 3, 4, 5, 6, 7, 8):
            ui_evidence = payload["stage_evidence"]["ui_evidence"][f"stage_{stage}"]
            self.assertGreater(ui_evidence["screenshot_count"], 0, stage)
            self.assertGreater(ui_evidence["browser_validation_count"], 0, stage)
        for stage in (3, 5, 8):
            self.assertGreater(
                payload["stage_evidence"]["ui_evidence"][f"stage_{stage}"]["route_validation_count"],
                0,
                stage,
            )
        self.assertEqual(payload["data_boundary"]["status"], "ready")
        self.assertEqual(payload["data_boundary"]["raw_file_count"], 4)
        self.assertEqual(payload["data_boundary"]["transaction_count"], 8815)
        self.assertEqual(payload["data_boundary"]["as_of"], "2026-06-03")

    def test_rereview_separates_historical_upload_from_current_delivery(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")

        payload = module.build_v024_overall_rereview_payload(ROOT)

        self.assertTrue(payload["historical_closeout"]["overall_upload_complete"])
        self.assertFalse(payload["final_delivery"]["current_changes_uploaded"])
        self.assertFalse(payload["final_delivery"]["app_reinstalled"])
        self.assertFalse(payload["final_delivery"]["github_app_local_consistency_proven"])
        self.assertEqual(payload["final_delivery"]["status"], "pending")
        self.assertFalse(payload["product_goal_complete"])
        self.assertEqual(payload["next_gate"], "PFI-V024-FINAL-DELIVERY")

    def test_rereview_validation_never_pushes_or_installs(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")

        payload = module.build_v024_overall_rereview_payload(ROOT)
        commands = "\n".join(payload["validation_commands"])

        self.assertNotIn("git push", commands)
        self.assertNotIn("/Applications/PFI.app", commands)
        self.assertIn("GitHub upload", payload["explicitly_not_done"])
        self.assertIn("app reinstall", payload["explicitly_not_done"])

    def test_rereview_cannot_self_certify_final_delivery(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")

        parameters = inspect.signature(module.build_v024_overall_rereview_payload).parameters
        payload = module.build_v024_overall_rereview_payload(ROOT)

        self.assertEqual(set(parameters), {"pfi_root"})
        self.assertEqual(payload["final_delivery"]["status"], "pending")
        self.assertEqual(
            payload["final_delivery"]["blocking_requirements"],
            ["current_changes_uploaded", "app_reinstalled", "github_app_local_consistency_proven"],
        )
        self.assertFalse(payload["product_goal_complete"])

    def test_stage_evidence_audit_fails_closed_for_missing_units(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")
        with tempfile.TemporaryDirectory() as tmp:
            pfi_root = Path(tmp) / "PFI"
            pfi_root.mkdir()
            audit = module.audit_v024_stage_evidence(pfi_root)

        self.assertEqual(audit["expected_unit_count"], 40)
        self.assertEqual(audit["complete_unit_count"], 0)
        self.assertGreater(len(audit["missing_artifacts"]), 0)

    def test_evidence_unit_semantics_reject_wrong_schema_ids_and_empty_artifacts(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")
        unit_id = "stage_0/phase_0_1"
        spec = module.EXPECTED_EVIDENCE_UNIT_MANIFEST[unit_id]
        with tempfile.TemporaryDirectory() as tmp:
            unit_root = Path(tmp)
            for name in module.EVIDENCE_UNIT_FILES:
                (unit_root / name).write_text("verified\n", encoding="utf-8")
            evidence = {
                "schema": spec["schema"],
                "stage": spec["stage"],
                "phase": spec["phase"],
                "status": spec["status"],
            }
            (unit_root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
            self.assertEqual(module.validate_v024_evidence_unit(unit_id, unit_root), [])

            evidence["schema"] = "WrongSchema"
            (unit_root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
            wrong_schema = module.validate_v024_evidence_unit(unit_id, unit_root)
            evidence["schema"] = spec["schema"]
            evidence["phase"] = "9.9"
            (unit_root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
            wrong_phase = module.validate_v024_evidence_unit(unit_id, unit_root)
            (unit_root / "terminal.log").write_text("", encoding="utf-8")
            empty_artifact = module.validate_v024_evidence_unit(unit_id, unit_root)

        self.assertTrue(any(issue["kind"] == "schema_mismatch" for issue in wrong_schema))
        self.assertTrue(any(issue["kind"] == "phase_mismatch" for issue in wrong_phase))
        self.assertTrue(any(issue["kind"] == "empty_artifact" for issue in empty_artifact))

    def test_whole_stage_acceptance_checks_fail_closed(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")
        unit_id = "stage_0/whole_stage_review"
        spec = module.EXPECTED_EVIDENCE_UNIT_MANIFEST[unit_id]
        with tempfile.TemporaryDirectory() as tmp:
            unit_root = Path(tmp)
            for name in module.EVIDENCE_UNIT_FILES:
                (unit_root / name).write_text("verified\n", encoding="utf-8")
            acceptance = {key: True for key in spec["required_acceptance_keys"]}
            evidence = {
                "schema": spec["schema"],
                "stage": spec["stage"],
                "status": spec["status"],
                "acceptance_checks": acceptance,
            }
            (unit_root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
            self.assertEqual(module.validate_v024_evidence_unit(unit_id, unit_root), [])

            acceptance["official_nav_count_is_10"] = False
            (unit_root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
            issues = module.validate_v024_evidence_unit(unit_id, unit_root)

        self.assertTrue(any(issue["kind"] == "acceptance_failed" for issue in issues))

    def test_manual_acceptance_and_historical_upload_are_derived_from_evidence(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")

        current = module.audit_v024_historical_closeout(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            missing = module.audit_v024_historical_closeout(Path(tmp) / "PFI")

        self.assertTrue(current["all_verified"])
        self.assertTrue(current["stage_8_phase_8_3_user_confirmed"])
        self.assertTrue(current["stage_9_phase_9_3_user_confirmed"])
        self.assertTrue(current["overall_upload_complete"])
        self.assertFalse(missing["all_verified"])
        self.assertFalse(missing["stage_8_phase_8_3_user_confirmed"])
        self.assertFalse(missing["stage_9_phase_9_3_user_confirmed"])
        self.assertFalse(missing["overall_upload_complete"])

    def test_historical_closeout_rejects_missing_confirmation_or_upload_proof(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")
        relative_paths = [
            Path("stage_8/whole_stage_review/evidence.json"),
            Path("stage_9/whole_stage_review/evidence.json"),
            Path("stage_9/github_main_upload/evidence.json"),
            Path("overall_project_review/evidence.json"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            pfi_root = Path(tmp) / "PFI"
            report_root = pfi_root / "reports" / "pfi_v024"
            for relative in relative_paths:
                target = report_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / "reports" / "pfi_v024" / relative, target)

            stage8_path = report_root / relative_paths[0]
            stage8 = json.loads(stage8_path.read_text(encoding="utf-8"))
            stage8["phase_8_3_user_confirmed"] = False
            stage8_path.write_text(json.dumps(stage8), encoding="utf-8")
            missing_confirmation = module.audit_v024_historical_closeout(pfi_root)

            shutil.copy2(ROOT / "reports" / "pfi_v024" / relative_paths[0], stage8_path)
            upload_path = report_root / relative_paths[2]
            upload = json.loads(upload_path.read_text(encoding="utf-8"))
            upload["github_main_uploaded"] = False
            upload_path.write_text(json.dumps(upload), encoding="utf-8")
            missing_upload = module.audit_v024_historical_closeout(pfi_root)

        self.assertFalse(missing_confirmation["stage_8_phase_8_3_user_confirmed"])
        self.assertFalse(missing_confirmation["all_verified"])
        self.assertFalse(missing_upload["overall_upload_complete"])
        self.assertFalse(missing_upload["all_verified"])

    def test_real_data_contract_rejects_any_declared_snapshot_drift(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")
        payload = module.build_v024_overall_rereview_payload(ROOT)
        valid = dict(payload["data_boundary"])
        current_git_ref = module.resolve_v024_current_git_ref(ROOT)

        self.assertEqual(
            module.validate_v024_real_data_contract(
                valid,
                no_forbidden_financial_data=True,
                expected_git_ref=current_git_ref,
            ),
            [],
        )
        mutations = {
            "raw_file_count": 1,
            "transaction_count": 1,
            "as_of": "2026-06-02",
            "evidence_hash": "sha256:" + "0" * 64,
            "git_object_status": "unavailable",
            "git_ref": "f" * 40,
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                changed = dict(valid)
                changed[key] = value
                self.assertTrue(
                    module.validate_v024_real_data_contract(
                        changed,
                        no_forbidden_financial_data=True,
                        expected_git_ref=current_git_ref,
                    )
                )
        self.assertTrue(
            module.validate_v024_real_data_contract(
                valid,
                no_forbidden_financial_data=False,
                expected_git_ref=current_git_ref,
            )
        )

    def test_ui_validation_and_png_decode_fail_closed(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v024_overall_project_review")
        browser_id = "stage_2/phase_2_3/browser_validation.json"
        route_id = "stage_8/phase_8_1/route_click_validation.json"
        browser_source = ROOT / "reports" / "pfi_v024" / browser_id
        route_source = ROOT / "reports" / "pfi_v024" / route_id
        png_source = ROOT / "reports" / "pfi_v024" / "stage_8/phase_8_2/screenshots/mobile_responsive.png"

        self.assertEqual(module.validate_v024_ui_validation_file(browser_id, browser_source), [])
        self.assertEqual(module.validate_v024_ui_validation_file(route_id, route_source), [])
        self.assertEqual(module.validate_v024_png(png_source), [])

        with tempfile.TemporaryDirectory() as tmp:
            browser_path = Path(tmp) / "browser_validation.json"
            browser = json.loads(browser_source.read_text(encoding="utf-8"))
            browser["status"] = "fail"
            browser["console_errors"] = ["boom"]
            browser_path.write_text(json.dumps(browser), encoding="utf-8")

            route_path = Path(tmp) / "route_click_validation.json"
            route = json.loads(route_source.read_text(encoding="utf-8"))
            route["all_primary_routes_clicked"] = False
            route_path.write_text(json.dumps(route), encoding="utf-8")

            corrupt_png = Path(tmp) / "corrupt.png"
            corrupt_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 2048)

            browser_issues = module.validate_v024_ui_validation_file(browser_id, browser_path)
            route_issues = module.validate_v024_ui_validation_file(route_id, route_path)
            png_issues = module.validate_v024_png(corrupt_png)

        self.assertTrue(any(issue["kind"] == "ui_value_mismatch" for issue in browser_issues))
        self.assertTrue(any(issue["kind"] == "ui_expected_empty" for issue in browser_issues))
        self.assertTrue(any(issue["kind"] == "ui_value_mismatch" for issue in route_issues))
        self.assertTrue(any(issue["kind"] == "png_decode_error" for issue in png_issues))

    def test_historical_rereview_boundary_and_current_final_delivery_are_separate(self) -> None:
        run_contract = (ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md").read_text(encoding="utf-8")
        rereview = (ROOT / "docs" / "pfi_v024" / "OVERALL_REREVIEW.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")

        self.assertIn("v0.2.4 overall re-review", rereview)
        self.assertIn("PFI-V024-FINAL-DELIVERY", rereview)
        self.assertIn("product goal 未完成", rereview)
        self.assertNotIn("git push", rereview)

        for text in (run_contract, readme, handoff):
            self.assertIn("v0.2.4 final delivery", text)
            self.assertIn("ACC-PFI-V024-FINAL-DELIVERY", text)
            self.assertIn("pending_live_verifier", text)
            self.assertIn("PFI-V024-FINAL-DELIVERY", text)
            self.assertIn("live verifier", text)


if __name__ == "__main__":
    unittest.main()
