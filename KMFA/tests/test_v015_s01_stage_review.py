import copy
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.check_v015_s01_stage_review import (
    AGENTS_PATH,
    CONTRACTS_PATH,
    EVENTS_PATH,
    EXPECTED_ARTIFACT_REFS,
    EXPECTED_VALIDATION_IDS,
    FINDINGS_PATH,
    MANIFEST_PATH,
    MATRIX_PATH,
    MODEL_SPEC_PATH,
    PROJECT_GOVERNANCE_PATH,
    ROADMAP_GOVERNANCE_PATH,
    ROADMAP_SOURCE_PATH,
    SOURCE_MANIFEST_PATH,
    ValidationError,
    _canonical_content_hash,
    _validate_frozen_canonical_manifest,
    validate_v015_s01_stage_review,
)


class TestV015S01StageReview(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.paths = {
            "manifest": root / "manifest.json",
            "matrix": root / "matrix.json",
            "findings": root / "findings.csv",
            "contracts": root / "contracts.json",
            "receipts": root / "validation.jsonl",
            "roadmap": root / "roadmap.json",
            "source_manifest": root / "source_manifest.json",
            "project": root / "project.yaml",
            "roadmap_governance": root / "roadmap.yaml",
            "agents": root / "AGENTS.md",
            "events": root / "events.jsonl",
            "model_spec": root / "MODEL_SPEC.md",
        }
        self.paths["matrix"].write_bytes(MATRIX_PATH.read_bytes())
        self.paths["findings"].write_bytes(FINDINGS_PATH.read_bytes())
        self.paths["contracts"].write_bytes(CONTRACTS_PATH.read_bytes())
        self.paths["roadmap"].write_bytes(ROADMAP_SOURCE_PATH.read_bytes())
        self.paths["source_manifest"].write_bytes(SOURCE_MANIFEST_PATH.read_bytes())
        self.paths["project"].write_bytes(PROJECT_GOVERNANCE_PATH.read_bytes())
        self.paths["roadmap_governance"].write_bytes(ROADMAP_GOVERNANCE_PATH.read_bytes())
        self.paths["agents"].write_bytes(AGENTS_PATH.read_bytes())
        self.paths["events"].write_bytes(EVENTS_PATH.read_bytes())
        self.paths["model_spec"].write_bytes(MODEL_SPEC_PATH.read_bytes())
        receipts = [
            {"validation_id": validation_id, "command": f"validate {validation_id}", "result": "PENDING", "exit_code": None}
            for validation_id in sorted(EXPECTED_VALIDATION_IDS)
        ]
        self._write_jsonl(self.paths["receipts"], receipts)

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest.pop("review_run_mode", None)
        manifest["run_mode"] = "IMPLEMENT"
        manifest["stage_gate"]["final_validation_status"] = "PENDING"
        manifest["artifact_refs"] = dict(EXPECTED_ARTIFACT_REFS)
        path_map = {
            EXPECTED_ARTIFACT_REFS["review_matrix"]: self.paths["matrix"],
            EXPECTED_ARTIFACT_REFS["review_findings"]: self.paths["findings"],
            EXPECTED_ARTIFACT_REFS["cross_phase_contracts"]: self.paths["contracts"],
            EXPECTED_ARTIFACT_REFS["review_report"]: MANIFEST_PATH.parent.parent / "human/stage1_review_report_zh.md",
            EXPECTED_ARTIFACT_REFS["rollback_plan"]: MANIFEST_PATH.parent.parent / "human/rollback_plan_zh.md",
            EXPECTED_ARTIFACT_REFS["test_results"]: MANIFEST_PATH.parent.parent / "human/test_results_zh.md",
            EXPECTED_ARTIFACT_REFS["validation_results"]: self.paths["receipts"],
        }
        manifest["artifact_integrity"] = [
            {"ref": ref, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for ref, path in path_map.items()
        ]
        manifest["content_hash"] = _canonical_content_hash(manifest)
        self._write_json(self.paths["manifest"], manifest)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _write_json(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    def _validate(self, *, strict: bool = False) -> dict:
        return validate_v015_s01_stage_review(
            self.paths["manifest"],
            matrix_path=self.paths["matrix"],
            findings_path=self.paths["findings"],
            contracts_path=self.paths["contracts"],
            validation_results_path=self.paths["receipts"],
            roadmap_source_path=self.paths["roadmap"],
            source_manifest_path=self.paths["source_manifest"],
            project_governance_path=self.paths["project"],
            roadmap_governance_path=self.paths["roadmap_governance"],
            agents_path=self.paths["agents"],
            events_path=self.paths["events"],
            model_spec_path=self.paths["model_spec"],
            source_package=None,
            require_validation_receipts=strict,
        )

    def _mutate_manifest(self, mutation) -> None:
        value = json.loads(self.paths["manifest"].read_text(encoding="utf-8"))
        mutation(value)
        value["content_hash"] = _canonical_content_hash(value)
        self._write_json(self.paths["manifest"], value)

    def _mutate_json(self, key: str, mutation) -> None:
        value = json.loads(self.paths[key].read_text(encoding="utf-8"))
        mutation(value)
        self._write_json(self.paths[key], value)

    def _assert_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self._validate()

    def test_validates_fail_closed_stage_review_with_pending_final_receipts(self) -> None:
        result = self._validate()
        self.assertEqual(result["stage_gate"]["stage_lifecycle_status"], "BLOCKED")
        self.assertEqual(result["stage_gate"]["stage_acceptance_status"], "NOT_PASSED")
        self.assertFalse(result["stage_gate"]["s02_entry_allowed"])

    def test_canonical_manifest_is_frozen_to_result_commit(self) -> None:
        errors: list[str] = []
        _validate_frozen_canonical_manifest(
            MANIFEST_PATH,
            json.loads(MANIFEST_PATH.read_text(encoding="utf-8")),
            errors,
        )
        self.assertEqual(errors, [])

    def test_validates_exact_pass_receipts_in_strict_mode(self) -> None:
        rows = [json.loads(line) for line in self.paths["receipts"].read_text(encoding="utf-8").splitlines()]
        for row in rows:
            row.update(result="PASS", exit_code=0)
        self._write_jsonl(self.paths["receipts"], rows)
        events = [json.loads(line) for line in self.paths["events"].read_text(encoding="utf-8").splitlines() if line.strip()]
        latest_index = max(index for index, row in enumerate(events) if row.get("phase_id") == "V015_S01_STAGE_REVIEW")
        events[latest_index].update(
            event_id="EVENT-KMFA-20260713-V015-S01-STAGE-REVIEW-FINAL-VALIDATION",
            evidence_validation_status="PASS",
            review_defect_count=17,
            inherited_blocker_count=5,
        )
        self._write_jsonl(self.paths["events"], events)
        def promote_final(value: dict) -> None:
            value["stage_gate"]["final_validation_status"] = "PASS"
            receipt_ref = EXPECTED_ARTIFACT_REFS["validation_results"]
            receipt_integrity = next(row for row in value["artifact_integrity"] if row["ref"] == receipt_ref)
            receipt_integrity.update(
                bytes=self.paths["receipts"].stat().st_size,
                sha256=hashlib.sha256(self.paths["receipts"].read_bytes()).hexdigest(),
            )
        self._mutate_manifest(promote_final)
        self._validate(strict=True)

    def test_rejects_stage_lifecycle_pass(self) -> None:
        self._mutate_manifest(lambda value: value["stage_gate"].update(stage_lifecycle_status="PASSED"))
        self._assert_rejected()

    def test_rejects_stage_acceptance_pass(self) -> None:
        self._mutate_manifest(lambda value: value["stage_gate"].update(stage_acceptance_status="PASSED"))
        self._assert_rejected()

    def test_rejects_go_decision(self) -> None:
        self._mutate_manifest(lambda value: value["stage_gate"].update(decision="GO"))
        self._assert_rejected()

    def test_rejects_s02_entry(self) -> None:
        self._mutate_manifest(lambda value: value["stage_gate"].update(s02_entry_allowed=True))
        self._assert_rejected()

    def test_rejects_non_implement_run_mode(self) -> None:
        self._mutate_manifest(lambda value: value.update(run_mode="REVIEW"))
        self._assert_rejected()

    def test_rejects_wrong_work_kind(self) -> None:
        self._mutate_manifest(lambda value: value.update(work_kind="PRODUCT_IMPLEMENTATION"))
        self._assert_rejected()

    def test_rejects_invalid_manifest_content_hash(self) -> None:
        value = json.loads(self.paths["manifest"].read_text(encoding="utf-8"))
        value["content_hash"] = "sha256:" + "0" * 64
        self._write_json(self.paths["manifest"], value)
        self._assert_rejected()

    def test_rejects_task_accounting_drift(self) -> None:
        self._mutate_manifest(lambda value: value["task_accounting"].update(accepted=6))
        self._assert_rejected()

    def test_rejects_review_finding_summary_drift(self) -> None:
        self._mutate_manifest(lambda value: value["review_findings"].update(review_defect_open=1))
        self._assert_rejected()

    def test_rejects_open_risk_plan_drift(self) -> None:
        self._mutate_manifest(lambda value: value["open_risk_plan"].update(p0_plan_gap_count=1))
        self._assert_rejected()

    def test_rejects_wrong_next_run(self) -> None:
        self._mutate_manifest(lambda value: value["next_gate"].update(next_allowed_run="S02"))
        self._assert_rejected()

    def test_rejects_false_request_for_additional_owner_authorization(self) -> None:
        self._mutate_manifest(lambda value: value["next_gate"].update(additional_owner_authorization_requested=True))
        self._assert_rejected()

    def test_rejects_product_runtime_implementation_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(product_runtime_implementation_performed=True))
        self._assert_rejected()

    def test_rejects_github_upload_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(github_upload_performed=True))
        self._assert_rejected()

    def test_rejects_phase_manifest_hash_drift(self) -> None:
        self._mutate_manifest(lambda value: value["phase_evidence"][0].update(manifest_content_hash="sha256:" + "0" * 64))
        self._assert_rejected()

    def test_rejects_phase_manifest_byte_drift(self) -> None:
        self._mutate_manifest(lambda value: value["phase_evidence"][1].update(manifest_bytes=1))
        self._assert_rejected()

    def test_rejects_duplicate_matrix_task(self) -> None:
        self._mutate_json("matrix", lambda value: value["tasks"].__setitem__(8, copy.deepcopy(value["tasks"][7])))
        self._assert_rejected()

    def test_rejects_missing_matrix_task(self) -> None:
        self._mutate_json("matrix", lambda value: value["tasks"].pop())
        self._assert_rejected()

    def test_rejects_matrix_task_status_drift(self) -> None:
        self._mutate_json("matrix", lambda value: value["tasks"][0].update(acceptance_status="PASSED"))
        self._assert_rejected()

    def test_rejects_matrix_stop_count_drift(self) -> None:
        self._mutate_json("matrix", lambda value: value.update(triggered_stop_condition_count=2))
        self._assert_rejected()

    def test_rejects_external_matrix_evidence(self) -> None:
        self._mutate_json("matrix", lambda value: value["tasks"][0].update(evidence_refs=["/etc/hosts"]))
        self._assert_rejected()

    def test_rejects_matrix_stage_result_pass(self) -> None:
        self._mutate_json("matrix", lambda value: value["stage_result"].update(stage_acceptance_status="PASSED"))
        self._assert_rejected()

    def test_rejects_missing_review_finding(self) -> None:
        rows = self._read_findings()[:-1]
        self._write_findings(rows)
        self._assert_rejected()

    def test_rejects_open_review_defect(self) -> None:
        rows = self._read_findings()
        rows[0]["status"] = "OPEN"
        self._write_findings(rows)
        self._assert_rejected()

    def test_rejects_review_defect_without_mutation_test(self) -> None:
        rows = self._read_findings()
        rows[0]["mutation_test_id"] = ""
        self._write_findings(rows)
        self._assert_rejected()

    def test_rejects_unbound_mutation_test_id(self) -> None:
        rows = self._read_findings()
        rows[0]["mutation_test_id"] = "test_method_that_does_not_exist"
        self._write_findings(rows)
        self._assert_rejected()

    def test_rejects_falsely_closed_inherited_blocker(self) -> None:
        rows = self._read_findings()
        next(row for row in rows if row["finding_id"] == "S01REV-IB-001")["status"] = "FIXED_VALIDATED"
        self._write_findings(rows)
        self._assert_rejected()

    def test_rejects_external_finding_evidence(self) -> None:
        rows = self._read_findings()
        rows[0]["evidence_refs"] = "/etc/hosts"
        self._write_findings(rows)
        self._assert_rejected()

    def test_rejects_missing_cross_phase_contract(self) -> None:
        self._mutate_json("contracts", lambda value: value["contracts"].pop())
        self._assert_rejected()

    def test_rejects_failed_cross_phase_contract(self) -> None:
        self._mutate_json("contracts", lambda value: value["contracts"][0].update(result="FAIL"))
        self._assert_rejected()

    def test_rejects_old_review_defect_contract_count(self) -> None:
        self._mutate_json("contracts", lambda value: value["contracts"][13].update(observed="13 fixed/0 open"))
        self._assert_rejected()

    def test_rejects_artifact_hash_drift(self) -> None:
        self._mutate_manifest(lambda value: value["artifact_integrity"][0].update(sha256="0" * 64))
        self._assert_rejected()

    def test_rejects_missing_receipt_or_test_result_integrity(self) -> None:
        original = json.loads(self.paths["manifest"].read_text(encoding="utf-8"))
        for ref in (EXPECTED_ARTIFACT_REFS["test_results"], EXPECTED_ARTIFACT_REFS["validation_results"]):
            with self.subTest(ref=ref):
                value = copy.deepcopy(original)
                value["artifact_integrity"] = [row for row in value["artifact_integrity"] if row["ref"] != ref]
                value["content_hash"] = _canonical_content_hash(value)
                self._write_json(self.paths["manifest"], value)
                self._assert_rejected()

    def test_rejects_empty_artifact_refs(self) -> None:
        self._mutate_manifest(lambda value: value.update(artifact_refs={}))
        self._assert_rejected()

    def test_rejects_pending_receipt_in_strict_mode(self) -> None:
        with self.assertRaises(ValidationError):
            self._validate(strict=True)

    def test_rejects_missing_validation_receipt(self) -> None:
        rows = [json.loads(line) for line in self.paths["receipts"].read_text(encoding="utf-8").splitlines()][:-1]
        self._write_jsonl(self.paths["receipts"], rows)
        self._assert_rejected()

    def test_rejects_pass_receipt_with_nonzero_exit(self) -> None:
        rows = [json.loads(line) for line in self.paths["receipts"].read_text(encoding="utf-8").splitlines()]
        rows[0].update(result="PASS", exit_code=1)
        self._write_jsonl(self.paths["receipts"], rows)
        self._assert_rejected()

    def test_rejects_incomplete_v15_roadmap(self) -> None:
        self._mutate_json("roadmap", lambda value: value["stages"].pop())
        self._assert_rejected()

    def test_rejects_roadmap_declared_count_drift(self) -> None:
        self._mutate_json("roadmap", lambda value: value.update(task_count=215))
        self._assert_rejected()

    def test_rejects_source_manifest_hash_drift(self) -> None:
        self._mutate_json("source_manifest", lambda value: value.update(source_package_sha256="0" * 64))
        self._assert_rejected()

    def test_rejects_stale_canonical_project_governance(self) -> None:
        text = self.paths["project"].read_text(encoding="utf-8").replace('target_version: "v1.5"', 'target_version: "v1.4"')
        self.paths["project"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_stale_canonical_roadmap_governance(self) -> None:
        text = self.paths["roadmap_governance"].read_text(encoding="utf-8").replace(
            'current_phase_id: "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"',
            'current_phase_id: "S18_GITHUB_UPLOAD"',
            1,
        )
        self.paths["roadmap_governance"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_stale_agents_current_state(self) -> None:
        text = self.paths["agents"].read_text(encoding="utf-8").replace(
            "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8",
            "0" * 64,
        )
        self.paths["agents"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_allows_agents_current_description_to_advance(self) -> None:
        text = self.paths["agents"].read_text(encoding="utf-8").replace(
            "V015_S01_CONTROLLED_TRANSITION_AMENDMENT",
            "S02-P1",
        )
        self.paths["agents"].write_text(text, encoding="utf-8")
        self._validate()

    def test_allows_legal_s02_p1_governance_successor(self) -> None:
        for key in ("project", "roadmap_governance"):
            text = self.paths[key].read_text(encoding="utf-8")
            text = text.replace('current_stage_id: "S01"', 'current_stage_id: "S02"')
            text = text.replace(
                'current_phase_id: "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"',
                'current_phase_id: "S02-P1"',
            )
            self.paths[key].write_text(text, encoding="utf-8")
        self._validate()

    def test_rejects_historical_stage_review_conclusion_drift_after_transition(self) -> None:
        text = self.paths["project"].read_text(encoding="utf-8").replace(
            's01_stage_review_acceptance_status: "NOT_PASSED"',
            's01_stage_review_acceptance_status: "PASSED"',
        )
        self.paths["project"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_canonical_roadmap_count_drift(self) -> None:
        text = self.paths["roadmap_governance"].read_text(encoding="utf-8").replace(
            "active_task_count: 216",
            "active_task_count: 215",
        )
        self.paths["roadmap_governance"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_nested_active_roadmap_count_drift(self) -> None:
        text = self.paths["roadmap_governance"].read_text(encoding="utf-8").replace(
            "  task_count: 216",
            "  task_count: 215",
        )
        self.paths["roadmap_governance"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_stale_canonical_project_roadmap_events(self) -> None:
        rows = [json.loads(line) for line in self.paths["events"].read_text(encoding="utf-8").splitlines() if line.strip()]
        latest_index = max(index for index, row in enumerate(rows) if row.get("phase_id") == "V015_S01_STAGE_REVIEW")
        rows[latest_index]["run_mode"] = "REVIEW"
        self._write_jsonl(self.paths["events"], rows)
        self._assert_rejected()

    def test_rejects_earlier_stage_review_event_history_drift(self) -> None:
        rows = [json.loads(line) for line in self.paths["events"].read_text(encoding="utf-8").splitlines() if line.strip()]
        first_index = next(index for index, row in enumerate(rows) if row.get("phase_id") == "V015_S01_STAGE_REVIEW")
        rows[first_index]["decision"] = "GO"
        self._write_jsonl(self.paths["events"], rows)
        self._assert_rejected()

    def test_rejects_stage_review_event_non_gate_content_drift(self) -> None:
        rows = [json.loads(line) for line in self.paths["events"].read_text(encoding="utf-8").splitlines() if line.strip()]
        final = next(row for row in rows if row.get("event_id") == "EVENT-KMFA-20260713-V015-S01-STAGE-REVIEW-FINAL-VALIDATION")
        final["summary"] = "rewritten historical summary"
        self._write_jsonl(self.paths["events"], rows)
        self._assert_rejected()

    def test_rejects_stale_model_spec_review_count(self) -> None:
        text = self.paths["model_spec"].read_text(encoding="utf-8").replace("17 个 review defects", "15 个 review defects")
        self.paths["model_spec"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_missing_v15_single_upload_rule(self) -> None:
        text = self.paths["agents"].read_text(encoding="utf-8").replace("不得按单个 Stage 做 GitHub upload gate", "")
        self.paths["agents"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def _read_findings(self) -> list[dict[str, str]]:
        with self.paths["findings"].open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def _write_findings(self, rows: list[dict[str, str]]) -> None:
        with self.paths["findings"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
