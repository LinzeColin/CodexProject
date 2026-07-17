from __future__ import annotations

import copy
import csv
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from KMFA.tools.check_v015_s01_controlled_transition_amendment import (
    AGENTS_PATH,
    BLOCKER_DISPOSITIONS_PATH,
    CONTRACT_PATH,
    EVENTS_PATH,
    EXPECTED_ARTIFACT_REFS,
    EXPECTED_CLAUSES,
    EXPECTED_CLAUSE_IDS,
    EXPECTED_RECEIPT_IDS,
    MANIFEST_PATH,
    MODEL_SPEC_PATH,
    PROJECT_GOVERNANCE_PATH,
    ROADMAP_GOVERNANCE_PATH,
    STAGE_REVIEW_MANIFEST_PATH,
    ValidationError,
    _canonical_content_hash,
    validate_v015_s01_controlled_transition_amendment,
)


class TestV015S01ControlledTransitionAmendment(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.paths = {
            "manifest": root / "manifest.json",
            "contract": root / "contract.json",
            "blockers": root / "blockers.csv",
            "receipts": root / "validation.jsonl",
            "report": root / "report.md",
            "rollback": root / "rollback.md",
            "test_results": root / "test_results.md",
            "stage_review": root / "stage_review_manifest.json",
            "project": root / "project.yaml",
            "roadmap": root / "roadmap.yaml",
            "agents": root / "AGENTS.md",
            "events": root / "events.jsonl",
            "model_spec": root / "MODEL_SPEC.md",
        }
        self.paths["stage_review"].write_bytes(STAGE_REVIEW_MANIFEST_PATH.read_bytes())
        stage_ref = "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/machine/stage1_review_manifest.json"
        self._write_json(
            self.paths["contract"],
            {
                "schema_version": "kmfa.v015.s01_controlled_transition_contract.v1",
                "project_id": "KMFA",
                "target_release": "v1.5",
                "bridge_id": "S01-CTA",
                "clauses": [
                    {
                        "clause_id": clause_id,
                        "name": EXPECTED_CLAUSES[clause_id][0],
                        "result": "PASS",
                        "observed": EXPECTED_CLAUSES[clause_id][1],
                        "evidence_refs": [stage_ref],
                    }
                    for clause_id in sorted(EXPECTED_CLAUSE_IDS)
                ],
            },
        )
        blocker_rows = []
        for index in range(1, 6):
            blocker_rows.append(
                {
                    "finding_id": f"S01REV-IB-{index:03d}",
                    "historical_class": "INHERITED_ACCEPTANCE_BLOCKER" if index < 5 else "INHERITED_TRANSITION_BLOCKER",
                    "historical_status": "OPEN_BLOCKING",
                    "current_disposition": "CARRIED_OPEN" if index < 5 else "RESOLVED_BY_AMENDMENT",
                    "blocks_s01_acceptance": "true" if index < 5 else "false",
                    "blocks_runtime_implementation": "true" if index < 5 else "false",
                    "blocks_s02_p1_planning_under_amendment": "false",
                    "resolution_or_deferred_gate": "deferred revalidation" if index < 5 else "resolved by this amendment",
                    "evidence_refs": stage_ref,
                }
            )
        self._write_csv(self.paths["blockers"], blocker_rows)
        for key in ("report", "rollback", "test_results"):
            self.paths[key].write_text(f"# {key}\npublic-safe evidence\n", encoding="utf-8")
        receipts = [
            {"validation_id": item, "command": f"validate {item}", "result": "PENDING", "exit_code": None}
            for item in sorted(EXPECTED_RECEIPT_IDS)
        ]
        self._write_jsonl(self.paths["receipts"], receipts)
        self.paths["project"].write_text(
            '\n'.join(
                [
                    'target_version: "v1.5"',
                    'development_version: "1.5.0-dev-s01-transition-amendment"',
                    'current_status: "v15_s01_controlled_transition_amendment_passed_s02_p1_only"',
                    'current_stage_id: "S01"',
                    'current_phase_id: "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"',
                    'run_mode: "IMPLEMENT"',
                    'work_kind: "CONTROLLED_TRANSITION_AMENDMENT"',
                    'stage_lifecycle_status: "BLOCKED"',
                    'stage_acceptance_status: "NOT_PASSED"',
                    'decision: "NO_GO"',
                    'amendment_acceptance_status: "PASSED"',
                    'taskpack_stage_gate_s02_entry_allowed: false',
                    's02_p1_planning_entry_allowed_by_amendment: true',
                    'next_gate_id: "S02-P1"',
                ]
            ) + '\n',
            encoding="utf-8",
        )
        self.paths["roadmap"].write_text(
            '\n'.join(
                [
                    'target_release: "v1.5"',
                    'active_stage_count: 24',
                    'active_phase_count: 72',
                    'active_task_count: 216',
                    'current_stage_id: "S01"',
                    'current_phase_id: "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"',
                    'stage_lifecycle_status: "BLOCKED"',
                    'stage_acceptance_status: "NOT_PASSED"',
                    'decision: "NO_GO"',
                    'taskpack_stage_gate_s02_entry_allowed: false',
                    's02_p1_planning_entry_allowed_by_amendment: true',
                    'next_gate_id: "S02-P1"',
                ]
            ) + '\n',
            encoding="utf-8",
        )
        self.paths["agents"].write_text(
            "V015_S01_CONTROLLED_TRANSITION_AMENDMENT\n"
            "S01 remains BLOCKED / NOT_PASSED / NO_GO\n"
            "下一独立 Run 仅可执行 S02-P1\n"
            "不得按单个 Stage 做 GitHub upload gate\n"
            "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8\n",
            encoding="utf-8",
        )
        self.paths["model_spec"].write_text(
            "FORM-KMFA-V015-S01-CONTROLLED-TRANSITION-AMENDMENT-001\n"
            "bridge_task_count == 3\n"
            "carried_open_acceptance_blocker_count == 4\n"
            "resolved_transition_blocker_count == 1\n"
            "s02_p1_planning_entry_allowed_by_amendment == true\n",
            encoding="utf-8",
        )
        self._write_jsonl(self.paths["events"], [self._event(final=False)])

        dependency = json.loads(self.paths["stage_review"].read_text(encoding="utf-8"))
        manifest = {
            "schema_version": "kmfa.v015.s01_controlled_transition_amendment.v1",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "bridge_id": "S01-CTA",
            "task_id": "KMFA-V015-S01-CONTROLLED-TRANSITION-AMENDMENT-20260713",
            "acceptance_id": "ACC-KMFA-V015-S01-CONTROLLED-TRANSITION-AMENDMENT",
            "generated_at": "2026-07-13T12:00:00+10:00",
            "run_mode": "IMPLEMENT",
            "work_kind": "CONTROLLED_TRANSITION_AMENDMENT",
            "amendment_base_commit": "08ce4b2b7c2491b2685bab2f33c32f57de519b1b",
            "source_package": {
                "name": "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip",
                "bytes": 118652,
                "sha256": "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8",
                "stage_count": 24,
                "phase_count": 72,
                "task_count": 216,
            },
            "dependency_evidence": {
                "count": 1,
                "stage_review_manifest_ref": stage_ref,
                "stage_review_manifest_bytes": self.paths["stage_review"].stat().st_size,
                "stage_review_manifest_sha256": hashlib.sha256(self.paths["stage_review"].read_bytes()).hexdigest(),
                "stage_review_manifest_content_hash": dependency["content_hash"],
                "stage_review_result_commit": "08ce4b2b7c2491b2685bab2f33c32f57de519b1b",
            },
            "authority": {
                "existing_full_rebuild_objective_is_scope_authority": True,
                "additional_owner_authorization_required": False,
                "taskpack_stage_gate_overridden": False,
                "taskpack_stage_gate_satisfied": False,
                "historical_evidence_mutated": False,
                "roadmap_counts_mutated": False,
                "bridge_counted_as_taskpack_phase": False,
            },
            "historical_stage_snapshot": {
                "stage_lifecycle_status": "BLOCKED",
                "stage_acceptance_status": "NOT_PASSED",
                "decision": "NO_GO",
                "s02_entry_allowed": False,
                "task_total": 9,
                "task_accepted": 5,
                "task_not_accepted": 4,
                "triggered_stop_conditions": 3,
                "audit_conclusion": "RUNTIME_OBJECT_MISSING",
                "existing_runtime_refactor_authorized": False,
            },
            "change_control_basis": {
                "p3_greenfield_change_control_required": True,
                "transition_mode": "GREENFIELD_PLANNING_ONLY",
                "risk_id": "RISK-P3-RUN-001",
                "risk_resolution_stages": ["S02", "S15", "S20"],
                "runtime_business_flow_stop_preserved": True,
                "greenfield_rebuild_planning_authorized": True,
                "greenfield_rebuild_implementation_authorized": False,
                "technology_stack_selection_allowed": False,
            },
            "bridge_tasks": [
                {
                    "task_id": "S01CTA-T01",
                    "name": "冻结 authority 与 Stage 负面历史",
                    "execution_status": "EXECUTION_COMPLETE",
                    "acceptance_status": "PASSED",
                    "output": "FULL REBUILD scope authority and immutable Stage review dependency binding",
                    "evidence_refs": [stage_ref],
                },
                {
                    "task_id": "S01CTA-T02",
                    "name": "建立 planning-only transition edge",
                    "execution_status": "EXECUTION_COMPLETE",
                    "acceptance_status": "PASSED",
                    "output": "five blocker dispositions and twelve transition clauses",
                    "evidence_refs": [EXPECTED_ARTIFACT_REFS["transition_contract"], EXPECTED_ARTIFACT_REFS["blocker_dispositions"]],
                },
                {
                    "task_id": "S01CTA-T03",
                    "name": "验证下一入口与非动作边界",
                    "execution_status": "EXECUTION_COMPLETE",
                    "acceptance_status": "PASSED",
                    "output": "S02-P1 planning-only next-entry gate with all downstream actions false",
                    "evidence_refs": [EXPECTED_ARTIFACT_REFS["report"], EXPECTED_ARTIFACT_REFS["test_results"]],
                },
            ],
            "bridge_task_accounting": {"total": 3, "accepted": 3, "not_accepted": 0},
            "blocker_disposition_accounting": {
                "historical_total": 5,
                "carried_open_acceptance_blockers": 4,
                "resolved_transition_blockers": 1,
                "historical_rows_mutated": 0,
                "s02_p1_planning_blockers": 0,
                "runtime_implementation_blockers": 4,
            },
            "risk_carry_forward": {
                "total": 24,
                "p0": 18,
                "p1": 6,
                "p0_plan_gap_count": 0,
                "resolved_by_amendment": 0,
                "all_remain_open_with_plan": True,
            },
            "amendment_result": {
                "execution_status": "EXECUTION_COMPLETE",
                "evidence_validation_status": "PENDING",
                "final_validation_status": "PENDING",
                "acceptance_status": "PENDING_FINAL_VALIDATION",
                "decision": "PENDING_FINAL_VALIDATION",
                "amendment_is_stage_pass": False,
                "stage_acceptance_recomputed": False,
            },
            "next_entry_gate": {
                "next_allowed_taskpack_phase": "S02-P1",
                "s02_p1_planning_entry_allowed_by_amendment": False,
                "s02_p1_started_in_amendment_run": False,
                "s02_p1_product_implementation_allowed": False,
                "s02_p2_entry_allowed": False,
                "s02_p3_entry_allowed": False,
                "s03_plus_entry_allowed": False,
                "product_implementation_allowed": False,
            },
            "future_obligation": {
                "s01_deferred_revalidation_required": True,
                "revalidation_requires_tracked_runtime": True,
                "revalidation_requires_real_routes": True,
                "revalidation_requires_tracked_builder_installer": True,
                "revalidation_requires_complete_preaudit_telemetry": True,
                "revalidation_deadline": "BEFORE_S24_RELEASE_ACCEPTANCE_FINAL_OVERALL_REVIEW_GITHUB_UPLOAD_APP_REINSTALL",
                "historical_records_append_only": True,
                "new_evidence_required_to_change_acceptance": True,
            },
            "downstream_actions": {
                "s02_started": False,
                "technology_stack_selected": False,
                "product_runtime_implementation_performed": False,
                "api_implementation_performed": False,
                "database_implementation_performed": False,
                "ui_implementation_performed": False,
                "raw_business_content_read": False,
                "business_execution_performed": False,
                "github_upload_performed": False,
                "app_reinstall_performed": False,
                "raw_inbox_mutated": False,
            },
            "artifact_refs": dict(EXPECTED_ARTIFACT_REFS),
            "artifact_integrity": [],
        }
        path_map = self._artifact_path_map()
        manifest["artifact_integrity"] = [
            {"ref": ref, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for ref, path in path_map.items()
            if ref != EXPECTED_ARTIFACT_REFS["manifest"]
        ]
        manifest["content_hash"] = _canonical_content_hash(manifest)
        self._write_json(self.paths["manifest"], manifest)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _event(*, final: bool) -> dict:
        return {
            "event_id": (
                "EVENT-KMFA-20260713-V015-S01-CONTROLLED-TRANSITION-AMENDMENT-FINAL-VALIDATION"
                if final else "EVENT-KMFA-20260713-V015-S01-CONTROLLED-TRANSITION-AMENDMENT-EXECUTION"
            ),
            "project_id": "KMFA",
            "phase_id": "V015_S01_CONTROLLED_TRANSITION_AMENDMENT",
            "run_mode": "IMPLEMENT",
            "work_kind": "CONTROLLED_TRANSITION_AMENDMENT",
            "amendment_execution_status": "EXECUTION_COMPLETE",
            "amendment_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
            "final_validation_status": "PASS" if final else "PENDING",
            "historical_stage_lifecycle_status": "BLOCKED",
            "historical_stage_acceptance_status": "NOT_PASSED",
            "historical_stage_decision": "NO_GO",
            "taskpack_stage_gate_s02_entry_allowed": False,
            "s02_p1_planning_entry_allowed_by_amendment": final,
            "s02_started": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "next_taskpack_phase": "S02-P1",
        }

    def _artifact_path_map(self) -> dict[str, Path]:
        return {
            EXPECTED_ARTIFACT_REFS["manifest"]: self.paths["manifest"],
            EXPECTED_ARTIFACT_REFS["transition_contract"]: self.paths["contract"],
            EXPECTED_ARTIFACT_REFS["blocker_dispositions"]: self.paths["blockers"],
            EXPECTED_ARTIFACT_REFS["report"]: self.paths["report"],
            EXPECTED_ARTIFACT_REFS["rollback_plan"]: self.paths["rollback"],
            EXPECTED_ARTIFACT_REFS["test_results"]: self.paths["test_results"],
            EXPECTED_ARTIFACT_REFS["validation_results"]: self.paths["receipts"],
        }

    @staticmethod
    def _write_json(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    @staticmethod
    def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _validate(
        self,
        *,
        strict: bool = False,
        clean: bool = False,
        source_package: Path | None = None,
        require_source_package: bool = False,
        require_dependency_validator: bool = False,
    ) -> dict:
        return validate_v015_s01_controlled_transition_amendment(
            self.paths["manifest"],
            contract_path=self.paths["contract"],
            blocker_dispositions_path=self.paths["blockers"],
            validation_results_path=self.paths["receipts"],
            stage_review_manifest_path=self.paths["stage_review"],
            project_governance_path=self.paths["project"],
            roadmap_governance_path=self.paths["roadmap"],
            agents_path=self.paths["agents"],
            events_path=self.paths["events"],
            model_spec_path=self.paths["model_spec"],
            artifact_path_overrides=self._artifact_path_map(),
            source_package=source_package,
            require_source_package=require_source_package,
            require_dependency_validator=require_dependency_validator,
            require_validation_receipts=strict,
            require_clean_worktree=clean,
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

    def _read_csv(self) -> list[dict[str, str]]:
        with self.paths["blockers"].open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def _assert_rejected(self, *, strict: bool = False, clean: bool = False) -> None:
        with self.assertRaises(ValidationError):
            self._validate(strict=strict, clean=clean)

    def _promote_strict(self) -> None:
        receipts = [json.loads(line) for line in self.paths["receipts"].read_text(encoding="utf-8").splitlines()]
        for row in receipts:
            row.update(result="PASS", exit_code=0)
        self._write_jsonl(self.paths["receipts"], receipts)
        self._write_jsonl(self.paths["events"], [self._event(final=False), self._event(final=True)])

        def promote(value: dict) -> None:
            value["amendment_result"].update(
                evidence_validation_status="PASS",
                final_validation_status="PASS",
                acceptance_status="PASSED",
                decision="GO_TO_S02_P1_ONLY",
            )
            value["next_entry_gate"]["s02_p1_planning_entry_allowed_by_amendment"] = True
            receipt_ref = EXPECTED_ARTIFACT_REFS["validation_results"]
            row = next(item for item in value["artifact_integrity"] if item["ref"] == receipt_ref)
            row.update(
                bytes=self.paths["receipts"].stat().st_size,
                sha256=hashlib.sha256(self.paths["receipts"].read_bytes()).hexdigest(),
            )

        self._mutate_manifest(promote)

    def _set_successor_governance(
        self,
        phase_id: str = "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK",
        stage_id: str = "S02",
    ) -> None:
        history = [
            's01_stage_review_lifecycle_status: "BLOCKED"',
            's01_stage_review_acceptance_status: "NOT_PASSED"',
            's01_stage_review_decision: "NO_GO"',
            "s01_stage_review_s02_entry_allowed: false",
            's01_controlled_transition_amendment_acceptance_status: "PASSED"',
            's01_controlled_transition_amendment_decision: "GO_TO_S02_P1_ONLY"',
            "s01_controlled_transition_s02_p1_entry_allowed: true",
            "s01_controlled_transition_product_implementation_allowed: false",
        ]
        self.paths["project"].write_text(
            "\n".join(
                [
                    'target_version: "v1.5"',
                    f'current_stage_id: "{stage_id}"',
                    f'current_phase_id: "{phase_id}"',
                    *history,
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.paths["roadmap"].write_text(
            "\n".join(
                [
                    'target_release: "v1.5"',
                    "active_stage_count: 24",
                    "active_phase_count: 72",
                    "active_task_count: 216",
                    f'current_stage_id: "{stage_id}"',
                    f'current_phase_id: "{phase_id}"',
                    *history,
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.paths["agents"].write_text(
            "S01 remains BLOCKED / NOT_PASSED / NO_GO\n"
            "下一独立 Run 仅可执行当前合法 successor 的下一 Phase\n"
            "不得按单个 Stage 做 GitHub upload gate\n"
            "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8\n",
            encoding="utf-8",
        )

    def test_validates_pending_non_strict_amendment(self) -> None:
        result = self._validate()
        self.assertEqual(result["amendment_result"]["acceptance_status"], "PENDING_FINAL_VALIDATION")
        self.assertEqual(result["historical_stage_snapshot"]["stage_acceptance_status"], "NOT_PASSED")
        self.assertFalse(result["next_entry_gate"]["s02_p1_planning_entry_allowed_by_amendment"])

    def test_validates_strict_pass_amendment(self) -> None:
        self._promote_strict()
        self._validate(strict=True)

    def test_accepts_s02_p1_successor_with_frozen_amendment_history(self) -> None:
        self._promote_strict()
        self._set_successor_governance()
        self._validate(strict=True)

    def test_accepts_later_legal_successors_with_frozen_amendment_history(self) -> None:
        self._promote_strict()
        for phase_id, stage_id in (
            ("V015_S02_P2_TRACEABILITY", "S02"),
            ("V015_S02_P3_REVIEW", "S02"),
            ("V015_S03_P1_ARCHITECTURE", "S03"),
            ("V015_S24_P3_FINAL", "S24"),
        ):
            with self.subTest(phase_id=phase_id):
                self._set_successor_governance(phase_id, stage_id)
                self._validate(strict=True)

    def test_rejects_successor_missing_historical_amendment_field(self) -> None:
        self._promote_strict()
        self._set_successor_governance()
        for path_name in ("project", "roadmap"):
            with self.subTest(path=path_name):
                original = self.paths[path_name].read_text(encoding="utf-8")
                self.paths[path_name].write_text(
                    original.replace(
                        's01_controlled_transition_amendment_decision: "GO_TO_S02_P1_ONLY"\n',
                        "",
                    ),
                    encoding="utf-8",
                )
                self._assert_rejected(strict=True)
                self.paths[path_name].write_text(original, encoding="utf-8")

    def test_rejects_successor_rewriting_s01_negative_history(self) -> None:
        self._promote_strict()
        self._set_successor_governance()
        text = self.paths["roadmap"].read_text(encoding="utf-8").replace(
            's01_stage_review_acceptance_status: "NOT_PASSED"',
            's01_stage_review_acceptance_status: "PASSED"',
        )
        self.paths["roadmap"].write_text(text, encoding="utf-8")
        self._assert_rejected(strict=True)

    def test_rejects_successor_stage_phase_mismatch(self) -> None:
        self._promote_strict()
        self._set_successor_governance("V015_S03_P1_ARCHITECTURE", "S02")
        self._assert_rejected(strict=True)

    def test_rejects_illegal_successor_phase(self) -> None:
        self._promote_strict()
        self._set_successor_governance("V015_S25_P1_OUT_OF_SCOPE", "S25")
        self._assert_rejected(strict=True)

    def test_rejects_schema_drift(self) -> None:
        self._mutate_manifest(lambda value: value.update(schema_version="wrong"))
        self._assert_rejected()

    def test_rejects_extra_top_level_key(self) -> None:
        self._mutate_manifest(lambda value: value.update(extra=True))
        self._assert_rejected()

    def test_rejects_invalid_content_hash(self) -> None:
        value = json.loads(self.paths["manifest"].read_text(encoding="utf-8"))
        value["content_hash"] = "sha256:" + "0" * 64
        self._write_json(self.paths["manifest"], value)
        self._assert_rejected()

    def test_rejects_base_commit_drift(self) -> None:
        self._mutate_manifest(lambda value: value.update(amendment_base_commit="0" * 40))
        self._assert_rejected()

    def test_rejects_source_hash_drift(self) -> None:
        self._mutate_manifest(lambda value: value["source_package"].update(sha256="0" * 64))
        self._assert_rejected()

    def test_rejects_source_count_drift(self) -> None:
        self._mutate_manifest(lambda value: value["source_package"].update(task_count=215))
        self._assert_rejected()

    def test_rejects_missing_required_source_package(self) -> None:
        with self.assertRaises(ValidationError):
            self._validate(require_source_package=True)

    def test_rejects_required_source_package_hash_drift(self) -> None:
        package = Path(self.temporary.name) / "source.zip"
        package.write_bytes(b"wrong source package")
        with self.assertRaises(ValidationError):
            self._validate(source_package=package, require_source_package=True)

    def test_rejects_dependency_ref_drift(self) -> None:
        self._mutate_manifest(lambda value: value["dependency_evidence"].update(stage_review_manifest_ref="KMFA/other.json"))
        self._assert_rejected()

    def test_rejects_dependency_sha_drift(self) -> None:
        self._mutate_manifest(lambda value: value["dependency_evidence"].update(stage_review_manifest_sha256="0" * 64))
        self._assert_rejected()

    def test_rejects_dependency_content_hash_drift(self) -> None:
        self._mutate_manifest(lambda value: value["dependency_evidence"].update(stage_review_manifest_content_hash="sha256:" + "0" * 64))
        self._assert_rejected()

    def test_rejects_dependency_byte_drift(self) -> None:
        self._mutate_manifest(lambda value: value["dependency_evidence"].update(stage_review_manifest_bytes=1))
        self._assert_rejected()

    def test_rejects_dependency_stage_pass_rewrite(self) -> None:
        dependency = json.loads(self.paths["stage_review"].read_text(encoding="utf-8"))
        dependency["stage_gate"]["stage_acceptance_status"] = "PASSED"
        dependency["content_hash"] = _canonical_content_hash(dependency)
        self._write_json(self.paths["stage_review"], dependency)
        self._assert_rejected()

    def test_accepts_passing_external_dependency_validator(self) -> None:
        completed = subprocess.CompletedProcess([], 0, stdout="PASS", stderr="")
        with patch(
            "KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run",
            return_value=completed,
        ):
            self._validate(require_dependency_validator=True)

    def test_rejects_failed_external_dependency_validator(self) -> None:
        completed = subprocess.CompletedProcess([], 1, stdout="", stderr="dependency failed")
        with patch(
            "KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run",
            return_value=completed,
        ):
            with self.assertRaises(ValidationError):
                self._validate(require_dependency_validator=True)

    def test_rejects_additional_owner_authorization(self) -> None:
        self._mutate_manifest(lambda value: value["authority"].update(additional_owner_authorization_required=True))
        self._assert_rejected()

    def test_rejects_taskpack_gate_override(self) -> None:
        self._mutate_manifest(lambda value: value["authority"].update(taskpack_stage_gate_overridden=True))
        self._assert_rejected()

    def test_rejects_historical_evidence_mutation(self) -> None:
        self._mutate_manifest(lambda value: value["authority"].update(historical_evidence_mutated=True))
        self._assert_rejected()

    def test_rejects_bridge_counted_as_taskpack_phase(self) -> None:
        self._mutate_manifest(lambda value: value["authority"].update(bridge_counted_as_taskpack_phase=True))
        self._assert_rejected()

    def test_rejects_greenfield_change_control_mode_drift(self) -> None:
        self._mutate_manifest(lambda value: value["change_control_basis"].update(transition_mode="GREENFIELD_IMPLEMENTATION"))
        self._assert_rejected()

    def test_rejects_greenfield_implementation_authorization(self) -> None:
        self._mutate_manifest(lambda value: value["change_control_basis"].update(greenfield_rebuild_implementation_authorized=True))
        self._assert_rejected()

    def test_rejects_technology_stack_selection_authorization(self) -> None:
        self._mutate_manifest(lambda value: value["change_control_basis"].update(technology_stack_selection_allowed=True))
        self._assert_rejected()

    def test_rejects_historical_stage_lifecycle_pass(self) -> None:
        self._mutate_manifest(lambda value: value["historical_stage_snapshot"].update(stage_lifecycle_status="PASSED"))
        self._assert_rejected()

    def test_rejects_historical_stage_acceptance_pass(self) -> None:
        self._mutate_manifest(lambda value: value["historical_stage_snapshot"].update(stage_acceptance_status="PASSED"))
        self._assert_rejected()

    def test_rejects_historical_go_decision(self) -> None:
        self._mutate_manifest(lambda value: value["historical_stage_snapshot"].update(decision="GO"))
        self._assert_rejected()

    def test_rejects_historical_broad_s02_entry(self) -> None:
        self._mutate_manifest(lambda value: value["historical_stage_snapshot"].update(s02_entry_allowed=True))
        self._assert_rejected()

    def test_rejects_historical_task_count_drift(self) -> None:
        self._mutate_manifest(lambda value: value["historical_stage_snapshot"].update(task_accepted=6))
        self._assert_rejected()

    def test_rejects_missing_bridge_task(self) -> None:
        self._mutate_manifest(lambda value: value["bridge_tasks"].pop())
        self._assert_rejected()

    def test_rejects_duplicate_bridge_task(self) -> None:
        self._mutate_manifest(lambda value: value["bridge_tasks"].__setitem__(2, copy.deepcopy(value["bridge_tasks"][1])))
        self._assert_rejected()

    def test_rejects_bridge_task_failure(self) -> None:
        self._mutate_manifest(lambda value: value["bridge_tasks"][0].update(acceptance_status="NOT_PASSED"))
        self._assert_rejected()

    def test_rejects_bridge_task_terminal_finding_drift(self) -> None:
        self._mutate_manifest(lambda value: value["bridge_tasks"][1].update(output="OTHER"))
        self._assert_rejected()

    def test_rejects_bridge_task_name_drift(self) -> None:
        self._mutate_manifest(lambda value: value["bridge_tasks"][1].update(name="其他任务"))
        self._assert_rejected()

    def test_rejects_external_bridge_task_evidence(self) -> None:
        self._mutate_manifest(lambda value: value["bridge_tasks"][0].update(evidence_refs=["/etc/hosts"]))
        self._assert_rejected()

    def test_rejects_bridge_task_accounting_drift(self) -> None:
        self._mutate_manifest(lambda value: value["bridge_task_accounting"].update(accepted=2))
        self._assert_rejected()

    def test_rejects_blocker_summary_drift(self) -> None:
        self._mutate_manifest(lambda value: value["blocker_disposition_accounting"].update(resolved_transition_blockers=0))
        self._assert_rejected()

    def test_rejects_risk_carry_forward_resolution_claim(self) -> None:
        self._mutate_manifest(lambda value: value["risk_carry_forward"].update(resolved_by_amendment=1))
        self._assert_rejected()

    def test_rejects_risk_plan_gap(self) -> None:
        self._mutate_manifest(lambda value: value["risk_carry_forward"].update(p0_plan_gap_count=1))
        self._assert_rejected()

    def test_rejects_missing_blocker_row(self) -> None:
        rows = self._read_csv()[:-1]
        self._write_csv(self.paths["blockers"], rows)
        self._assert_rejected()

    def test_rejects_duplicate_blocker_row(self) -> None:
        rows = self._read_csv()
        rows[-1] = copy.deepcopy(rows[-2])
        self._write_csv(self.paths["blockers"], rows)
        self._assert_rejected()

    def test_rejects_acceptance_blocker_closed(self) -> None:
        rows = self._read_csv()
        rows[0]["current_disposition"] = "RESOLVED_BY_AMENDMENT"
        self._write_csv(self.paths["blockers"], rows)
        self._assert_rejected()

    def test_rejects_transition_blocker_still_open(self) -> None:
        rows = self._read_csv()
        rows[-1]["current_disposition"] = "CARRIED_OPEN"
        self._write_csv(self.paths["blockers"], rows)
        self._assert_rejected()

    def test_rejects_blocker_allowing_runtime_implementation(self) -> None:
        rows = self._read_csv()
        rows[0]["blocks_runtime_implementation"] = "false"
        self._write_csv(self.paths["blockers"], rows)
        self._assert_rejected()

    def test_rejects_blocker_preventing_scoped_planning(self) -> None:
        rows = self._read_csv()
        rows[0]["blocks_s02_p1_planning_under_amendment"] = "true"
        self._write_csv(self.paths["blockers"], rows)
        self._assert_rejected()

    def test_rejects_external_blocker_evidence(self) -> None:
        rows = self._read_csv()
        rows[0]["evidence_refs"] = "/etc/hosts"
        self._write_csv(self.paths["blockers"], rows)
        self._assert_rejected()

    def test_rejects_missing_blocker_deferred_gate(self) -> None:
        rows = self._read_csv()
        rows[0]["resolution_or_deferred_gate"] = ""
        self._write_csv(self.paths["blockers"], rows)
        self._assert_rejected()

    def test_rejects_contract_schema_drift(self) -> None:
        self._mutate_json("contract", lambda value: value.update(schema_version="wrong"))
        self._assert_rejected()

    def test_rejects_missing_contract_clause(self) -> None:
        self._mutate_json("contract", lambda value: value["clauses"].pop())
        self._assert_rejected()

    def test_rejects_duplicate_contract_clause(self) -> None:
        self._mutate_json("contract", lambda value: value["clauses"].__setitem__(11, copy.deepcopy(value["clauses"][10])))
        self._assert_rejected()

    def test_rejects_failed_contract_clause(self) -> None:
        self._mutate_json("contract", lambda value: value["clauses"][0].update(result="FAIL"))
        self._assert_rejected()

    def test_rejects_empty_contract_observation(self) -> None:
        self._mutate_json("contract", lambda value: value["clauses"][1].update(observed=""))
        self._assert_rejected()

    def test_rejects_contract_clause_name_drift(self) -> None:
        self._mutate_json("contract", lambda value: value["clauses"][1].update(name="other"))
        self._assert_rejected()

    def test_rejects_external_contract_evidence(self) -> None:
        self._mutate_json("contract", lambda value: value["clauses"][2].update(evidence_refs=["/etc/hosts"]))
        self._assert_rejected()

    def test_rejects_amendment_as_stage_pass(self) -> None:
        self._mutate_manifest(lambda value: value["amendment_result"].update(amendment_is_stage_pass=True))
        self._assert_rejected()

    def test_rejects_stage_acceptance_recomputation(self) -> None:
        self._mutate_manifest(lambda value: value["amendment_result"].update(stage_acceptance_recomputed=True))
        self._assert_rejected()

    def test_rejects_wrong_amendment_decision(self) -> None:
        self._mutate_manifest(lambda value: value["amendment_result"].update(decision="GO"))
        self._assert_rejected()

    def test_rejects_mixed_pending_and_final_result_cohort(self) -> None:
        self._mutate_manifest(lambda value: value["amendment_result"].update(evidence_validation_status="PASS"))
        self._assert_rejected()

    def test_rejects_next_phase_beyond_s02_p1(self) -> None:
        self._mutate_manifest(lambda value: value["next_entry_gate"].update(next_allowed_taskpack_phase="S02-P2"))
        self._assert_rejected()

    def test_rejects_s02_p1_not_allowed(self) -> None:
        self._promote_strict()
        self._mutate_manifest(lambda value: value["next_entry_gate"].update(s02_p1_planning_entry_allowed_by_amendment=False))
        self._assert_rejected()

    def test_rejects_s02_p2_entry(self) -> None:
        self._mutate_manifest(lambda value: value["next_entry_gate"].update(s02_p2_entry_allowed=True))
        self._assert_rejected()

    def test_rejects_s02_p3_entry(self) -> None:
        self._mutate_manifest(lambda value: value["next_entry_gate"].update(s02_p3_entry_allowed=True))
        self._assert_rejected()

    def test_rejects_s03_plus_entry(self) -> None:
        self._mutate_manifest(lambda value: value["next_entry_gate"].update(s03_plus_entry_allowed=True))
        self._assert_rejected()

    def test_rejects_product_implementation_permission(self) -> None:
        self._mutate_manifest(lambda value: value["next_entry_gate"].update(product_implementation_allowed=True))
        self._assert_rejected()

    def test_rejects_s02_p1_product_implementation_permission(self) -> None:
        self._mutate_manifest(lambda value: value["next_entry_gate"].update(s02_p1_product_implementation_allowed=True))
        self._assert_rejected()

    def test_rejects_missing_future_revalidation_obligation(self) -> None:
        self._mutate_manifest(lambda value: value["future_obligation"].update(s01_deferred_revalidation_required=False))
        self._assert_rejected()

    def test_rejects_future_revalidation_deadline_drift(self) -> None:
        self._mutate_manifest(lambda value: value["future_obligation"].update(revalidation_deadline="NONE"))
        self._assert_rejected()

    def test_rejects_s02_started_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(s02_started=True))
        self._assert_rejected()

    def test_rejects_technology_stack_selected_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(technology_stack_selected=True))
        self._assert_rejected()

    def test_rejects_product_runtime_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(product_runtime_implementation_performed=True))
        self._assert_rejected()

    def test_rejects_api_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(api_implementation_performed=True))
        self._assert_rejected()

    def test_rejects_database_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(database_implementation_performed=True))
        self._assert_rejected()

    def test_rejects_ui_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(ui_implementation_performed=True))
        self._assert_rejected()

    def test_rejects_business_execution_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(business_execution_performed=True))
        self._assert_rejected()

    def test_rejects_github_upload_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(github_upload_performed=True))
        self._assert_rejected()

    def test_rejects_app_reinstall_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(app_reinstall_performed=True))
        self._assert_rejected()

    def test_rejects_raw_mutation_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(raw_inbox_mutated=True))
        self._assert_rejected()

    def test_rejects_raw_business_content_read_claim(self) -> None:
        self._mutate_manifest(lambda value: value["downstream_actions"].update(raw_business_content_read=True))
        self._assert_rejected()

    def test_rejects_empty_artifact_refs(self) -> None:
        self._mutate_manifest(lambda value: value.update(artifact_refs={}))
        self._assert_rejected()

    def test_rejects_missing_integrity_row(self) -> None:
        self._mutate_manifest(lambda value: value["artifact_integrity"].pop())
        self._assert_rejected()

    def test_rejects_integrity_hash_drift(self) -> None:
        self._mutate_manifest(lambda value: value["artifact_integrity"][0].update(sha256="0" * 64))
        self._assert_rejected()

    def test_rejects_pending_receipt_in_strict_mode(self) -> None:
        self._assert_rejected(strict=True)

    def test_rejects_missing_receipt(self) -> None:
        rows = [json.loads(line) for line in self.paths["receipts"].read_text(encoding="utf-8").splitlines()][:-1]
        self._write_jsonl(self.paths["receipts"], rows)
        self._assert_rejected()

    def test_rejects_duplicate_receipt(self) -> None:
        rows = [json.loads(line) for line in self.paths["receipts"].read_text(encoding="utf-8").splitlines()]
        rows[-1] = copy.deepcopy(rows[-2])
        self._write_jsonl(self.paths["receipts"], rows)
        self._assert_rejected()

    def test_rejects_pass_receipt_nonzero_exit(self) -> None:
        rows = [json.loads(line) for line in self.paths["receipts"].read_text(encoding="utf-8").splitlines()]
        rows[0].update(result="PASS", exit_code=1)
        self._write_jsonl(self.paths["receipts"], rows)
        self._assert_rejected()

    def test_rejects_stale_project_governance(self) -> None:
        text = self.paths["project"].read_text(encoding="utf-8").replace('current_phase_id: "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"', 'current_phase_id: "V015_S01_STAGE_REVIEW"')
        self.paths["project"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_stale_roadmap_governance(self) -> None:
        text = self.paths["roadmap"].read_text(encoding="utf-8").replace('next_gate_id: "S02-P1"', 'next_gate_id: "S02-P2"')
        self.paths["roadmap"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_stale_agents(self) -> None:
        text = self.paths["agents"].read_text(encoding="utf-8").replace("BLOCKED / NOT_PASSED / NO_GO", "PASSED")
        self.paths["agents"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_missing_single_upload_rule(self) -> None:
        text = self.paths["agents"].read_text(encoding="utf-8").replace("不得按单个 Stage 做 GitHub upload gate", "")
        self.paths["agents"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_stale_model_spec(self) -> None:
        text = self.paths["model_spec"].read_text(encoding="utf-8").replace("resolved_transition_blocker_count == 1", "resolved_transition_blocker_count == 0")
        self.paths["model_spec"].write_text(text, encoding="utf-8")
        self._assert_rejected()

    def test_rejects_stale_event(self) -> None:
        event = self._event(final=False)
        event["historical_stage_acceptance_status"] = "PASSED"
        self._write_jsonl(self.paths["events"], [event])
        self._assert_rejected()

    def test_rejects_pending_execution_event_with_passed_acceptance(self) -> None:
        event = self._event(final=False)
        event["amendment_acceptance_status"] = "PASSED"
        self._write_jsonl(self.paths["events"], [event])
        self._assert_rejected()

    def test_rejects_pending_execution_event_with_planning_open(self) -> None:
        event = self._event(final=False)
        event["s02_p1_planning_entry_allowed_by_amendment"] = True
        self._write_jsonl(self.paths["events"], [event])
        self._assert_rejected()

    def test_rejects_final_event_without_execution_event(self) -> None:
        self._promote_strict()
        self._write_jsonl(self.paths["events"], [self._event(final=True)])
        self._assert_rejected(strict=True)

    def test_rejects_reversed_execution_and_final_events(self) -> None:
        self._promote_strict()
        self._write_jsonl(self.paths["events"], [self._event(final=True), self._event(final=False)])
        self._assert_rejected(strict=True)

    def test_rejects_nonfinal_event_in_strict_mode(self) -> None:
        self._promote_strict()
        events = [self._event(final=False)]
        events[0]["final_validation_status"] = "PASS"
        self._write_jsonl(self.paths["events"], events)
        self._assert_rejected(strict=True)

    def test_validates_future_compatible_clean_gate(self) -> None:
        self._promote_strict()
        result_commit = "1" * 40

        def fake_run(command, **kwargs):
            if command[:3] == ["git", "status", "--short"]:
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
            if command[:3] == ["git", "log", "-1"]:
                return subprocess.CompletedProcess(command, 0, stdout=result_commit + "\n", stderr="")
            if command[:3] == ["git", "merge-base", "--is-ancestor"]:
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
            if command[:2] == ["git", "show"]:
                return subprocess.CompletedProcess(command, 0, stdout=self.paths["manifest"].read_bytes(), stderr=b"")
            raise AssertionError(command)

        with patch("KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run", side_effect=fake_run):
            self._validate(strict=True, clean=True)

    def test_rejects_dirty_clean_gate(self) -> None:
        with patch(
            "KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout=" M KMFA/file\n", stderr=""),
        ):
            self._assert_rejected(clean=True)

    def test_rejects_missing_result_commit(self) -> None:
        outputs = [
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        ]
        with patch("KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run", side_effect=outputs):
            self._assert_rejected(clean=True)

    def test_rejects_base_as_result_commit(self) -> None:
        base = "08ce4b2b7c2491b2685bab2f33c32f57de519b1b"
        outputs = [
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout=base + "\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout=self.paths["manifest"].read_bytes(), stderr=b""),
        ]
        with patch("KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run", side_effect=outputs):
            self._assert_rejected(clean=True)

    def test_rejects_result_commit_ancestry_failure(self) -> None:
        outputs = [
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="1" * 40 + "\n", stderr=""),
            subprocess.CompletedProcess([], 1, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout=self.paths["manifest"].read_bytes(), stderr=b""),
        ]
        with patch("KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run", side_effect=outputs):
            self._assert_rejected(clean=True)

    def test_rejects_result_not_ancestor_of_head(self) -> None:
        outputs = [
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="1" * 40 + "\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 1, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout=self.paths["manifest"].read_bytes(), stderr=b""),
        ]
        with patch("KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run", side_effect=outputs):
            self._assert_rejected(clean=True)

    def test_rejects_committed_manifest_blob_drift(self) -> None:
        outputs = [
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="1" * 40 + "\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout=b"different", stderr=b""),
        ]
        with patch("KMFA.tools.check_v015_s01_controlled_transition_amendment.subprocess.run", side_effect=outputs):
            self._assert_rejected(clean=True)


if __name__ == "__main__":
    unittest.main()
