from __future__ import annotations

import copy
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from KMFA.tools.build_v015_s02_p1_requirements_scope_lock import expected_core_outputs
from KMFA.tools.check_v015_s02_p1_requirements_scope_lock import (
    AGENTS_PATH,
    AMENDMENT_MANIFEST_PATH,
    EVENTS_PATH,
    EXPECTED_ARTIFACT_REFS,
    EXPECTED_BUSINESS_LINES,
    EXPECTED_DEPENDENCIES,
    EXPECTED_INTEGRITY_REFS,
    EXPECTED_RECEIPT_IDS,
    EXPECTED_SOURCE_MEMBERS,
    MODEL_SPEC_PATH,
    PHASE_BASE_COMMIT,
    PROJECT_GOVERNANCE_PATH,
    REPO_ROOT,
    ROADMAP_GOVERNANCE_PATH,
    S01P2_GAP_PATH,
    S01P2_MANIFEST_PATH,
    S01P2_MIGRATION_PATH,
    SOURCE_PACKAGE,
    SOURCE_PACKAGE_BYTES,
    SOURCE_PACKAGE_SHA256,
    ValidationError,
    _canonical_content_hash,
    _source_members,
    validate_v015_s02_p1_requirements_scope_lock,
)


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class TestV015S02P1RequirementsMerge(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.paths = {
            "manifest": root / "manifest.json",
            "requirements": root / "requirements.csv",
            "requirements_report": root / "requirements.md",
            "business": root / "business.csv",
            "scope": root / "scope.csv",
            "scope_report": root / "scope.md",
            "completion": root / "completion.md",
            "rollback": root / "rollback.md",
            "test_results": root / "tests.md",
            "receipts": root / "receipts.jsonl",
            "events": root / "events.jsonl",
            "project": root / "project.yaml",
            "roadmap": root / "roadmap.yaml",
            "agents": root / "AGENTS.md",
            "model_spec": root / "MODEL_SPEC.md",
        }
        core = expected_core_outputs()
        by_name = {path.name: payload for path, payload in core.items()}
        self.paths["requirements"].write_bytes(by_name["requirements_ledger_public_safe.csv"])
        self.paths["requirements_report"].write_bytes(by_name["requirements_ledger_zh.md"])
        self.paths["business"].write_bytes(by_name["business_line_matrix_public_safe.csv"])
        self.paths["scope"].write_bytes(by_name["scope_lock_dispositions_public_safe.csv"])
        self.paths["scope_report"].write_bytes(by_name["rebuild_scope_lock_zh.md"])
        for key in ("completion", "rollback", "test_results"):
            self.paths[key].write_text(f"# {key}\nS02-P1 public-safe evidence.\n", encoding="utf-8")
        receipts = [
            {"validation_id": item, "command": f"validate {item}", "result": "PENDING", "exit_code": None}
            for item in sorted(EXPECTED_RECEIPT_IDS)
        ]
        _write_jsonl(self.paths["receipts"], receipts)
        self.paths["project"].write_text(self._governance_text(project=True), encoding="utf-8")
        self.paths["roadmap"].write_text(self._governance_text(project=False), encoding="utf-8")
        self.paths["agents"].write_text(
            "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK\n"
            "next scoped gate S02-P2 only\n"
            "不得按单个 Stage 做 GitHub upload gate\n"
            f"{SOURCE_PACKAGE_SHA256}\n",
            encoding="utf-8",
        )
        self.paths["model_spec"].write_text(
            "FORM-KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-001\n"
            "requirement_count == 55\n"
            "business_line_count == 10\n"
            "migration_capability_count == 37\n"
            "s02_p2_entry_allowed == true\n"
            "product_implementation_allowed == false\n",
            encoding="utf-8",
        )
        _write_jsonl(self.paths["events"], [self._event(final=False)])
        self.artifact_overrides = {
            EXPECTED_ARTIFACT_REFS["requirements_ledger"]: self.paths["requirements"],
            EXPECTED_ARTIFACT_REFS["requirements_report"]: self.paths["requirements_report"],
            EXPECTED_ARTIFACT_REFS["business_line_matrix"]: self.paths["business"],
            EXPECTED_ARTIFACT_REFS["scope_lock"]: self.paths["scope"],
            EXPECTED_ARTIFACT_REFS["scope_lock_report"]: self.paths["scope_report"],
            EXPECTED_ARTIFACT_REFS["completion_record"]: self.paths["completion"],
            EXPECTED_ARTIFACT_REFS["rollback_plan"]: self.paths["rollback"],
            EXPECTED_ARTIFACT_REFS["test_results"]: self.paths["test_results"],
            EXPECTED_ARTIFACT_REFS["validation_results"]: self.paths["receipts"],
        }
        self.dependency_paths = {
            "amendment": AMENDMENT_MANIFEST_PATH,
            "s01p2_manifest": S01P2_MANIFEST_PATH,
            "gap": S01P2_GAP_PATH,
            "migration": S01P2_MIGRATION_PATH,
        }
        members, _, _ = _source_members(SOURCE_PACKAGE)
        manifest = self._manifest(members)
        _write_json(self.paths["manifest"], manifest)
        self.source_package: Path | None = SOURCE_PACKAGE

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _governance_text(*, project: bool) -> str:
        lines = [
            'target_version: "v1.5"' if project else 'target_release: "v1.5"',
            'current_stage_id: "S02"',
            'current_phase_id: "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK"',
            'run_mode: "IMPLEMENT"',
            'work_kind: "REQUIREMENTS_SCOPE_LOCK"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            'decision: "CONTINUE_TO_S02_P2_ONLY"',
            's02_p1_acceptance_status: "PASSED"',
            's02_p2_entry_allowed: true',
            's02_p3_entry_allowed: false',
            'product_implementation_allowed: false',
            'next_gate_id: "S02-P2"',
            's01_stage_review_lifecycle_status: "BLOCKED"',
            's01_stage_review_acceptance_status: "NOT_PASSED"',
            's01_stage_review_decision: "NO_GO"',
            's01_stage_review_s02_entry_allowed: false',
            's01_controlled_transition_amendment_acceptance_status: "PASSED"',
            's01_controlled_transition_amendment_decision: "GO_TO_S02_P1_ONLY"',
        ]
        if not project:
            lines[1:1] = ["active_stage_count: 24", "active_phase_count: 72", "active_task_count: 216"]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _event(*, final: bool) -> dict[str, object]:
        common: dict[str, object] = {
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S02",
            "phase_id": "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK",
            "roadmap_phase_id": "S02-P1",
            "task_id": "KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-20260713",
            "acceptance_id": "ACC-KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK",
            "run_mode": "IMPLEMENT",
            "work_kind": "REQUIREMENTS_SCOPE_LOCK",
            "stage_lifecycle_status": "IN_PROGRESS",
            "stage_acceptance_status": "PENDING",
            "s02_stage_passed": False,
            "s02_p2_started": False,
            "s02_p3_started": False,
            "product_implementation_allowed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "raw_business_content_read": False,
            "raw_inbox_mutated": False,
            "business_execution_performed": False,
            "next_taskpack_phase": "S02-P2",
        }
        if final:
            return {
                **common,
                "event_id": "EVENT-KMFA-20260713-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-FINAL-VALIDATION",
                "event_time": "2026-07-13T13:06:15+10:00",
                "event_type": "final_validation",
                "phase_acceptance_status": "PASSED",
                "final_validation_status": "PASS",
                "decision": "CONTINUE_TO_S02_P2_ONLY",
                "s02_p2_entry_allowed": True,
            }
        return {
            **common,
            "event_id": "EVENT-KMFA-20260713-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-EXECUTION",
            "event_time": "2026-07-13T13:01:38+10:00",
            "event_type": "phase_execution",
            "phase_acceptance_status": "PENDING_FINAL_VALIDATION",
            "final_validation_status": "PENDING",
            "decision": "PENDING_FINAL_VALIDATION",
            "s02_p2_entry_allowed": False,
        }

    def _manifest(self, members: dict[str, dict[str, object]]) -> dict[str, object]:
        dependency_rows = [
            {"dependency_id": dependency_id, **copy.deepcopy(expected)}
            for dependency_id, expected in EXPECTED_DEPENDENCIES.items()
        ]
        manifest: dict[str, object] = {
            "schema_version": "kmfa.v015.s02_p1_requirements_scope_lock.v1",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S02",
            "roadmap_phase_id": "S02-P1",
            "run_phase_id": "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK",
            "task_id": "KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-20260713",
            "acceptance_id": "ACC-KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK",
            "generated_at": "2026-07-13T13:02:00+10:00",
            "run_mode": "IMPLEMENT",
            "work_kind": "REQUIREMENTS_SCOPE_LOCK",
            "phase_base_commit": PHASE_BASE_COMMIT,
            "source_package": {
                "name": SOURCE_PACKAGE.name,
                "bytes": SOURCE_PACKAGE_BYTES,
                "sha256": SOURCE_PACKAGE_SHA256,
                "stage_count": 24,
                "phase_count": 72,
                "task_count": 216,
                "requirement_count": 55,
                "priority_counts": {"P0": 46, "P1": 8, "P2": 1},
                "members": members,
            },
            "dependency_evidence": {"count": 4, "dependencies": dependency_rows},
            "source_scope_policy": {
                "normative_keep_and_reverify_count": 15,
                "normative_rebuild_count": 15,
                "normative_deprecate_as_acceptance_baseline_count": 7,
                "evidence_qualified_capability_count": 37,
                "normative_list_counts_used_as_capability_counts": False,
                "deferred_requirement_ids": ["R052", "R053", "R054"],
            },
            "phase_scope": {
                "planning_only": True,
                "requirements_merge": True,
                "business_line_scope_lock": True,
                "v14_to_v15_scope_lock": True,
                "s02_p2_traceability_performed": False,
                "technology_stack_selection_allowed": False,
                "product_implementation_allowed": False,
            },
            "task_accounting": {"total": 3, "execution_complete": 3, "accepted": 3, "not_accepted": 0},
            "tasks": [
                {
                    "task_id": "S02P1T01",
                    "name": "建立唯一需求总账",
                    "output": "版本化需求总账。",
                    "execution_status": "EXECUTION_COMPLETE",
                    "acceptance_status": "PASSED",
                    "evidence_refs": [EXPECTED_ARTIFACT_REFS["requirements_ledger"], EXPECTED_ARTIFACT_REFS["requirements_report"]],
                },
                {
                    "task_id": "S02P1T02",
                    "name": "登记业务线 1–10",
                    "output": "业务线矩阵。",
                    "execution_status": "EXECUTION_COMPLETE",
                    "acceptance_status": "PASSED",
                    "evidence_refs": [EXPECTED_ARTIFACT_REFS["business_line_matrix"]],
                },
                {
                    "task_id": "S02P1T03",
                    "name": "锁定当前版本边界",
                    "output": "重构范围锁。",
                    "execution_status": "EXECUTION_COMPLETE",
                    "acceptance_status": "PASSED",
                    "evidence_refs": [EXPECTED_ARTIFACT_REFS["scope_lock"], EXPECTED_ARTIFACT_REFS["scope_lock_report"]],
                },
            ],
            "requirement_ledger_accounting": {
                "total": 55,
                "unique": 55,
                "p0": 46,
                "p1": 8,
                "p2": 1,
                "p0_p1_total": 54,
                "p0_p1_unique": 54,
                "duplicate_id_count": 0,
                "normalized_duplicate_count": 0,
                "unresolved_normative_conflict_count": 0,
                "resolved_normative_conflict_count": 1,
                "source_row_match_count": 55,
                "implementation_acceptance_claim_count": 0,
                "delivery_status": "SCOPE_LOCKED_NOT_IMPLEMENTED",
            },
            "business_line_accounting": {
                "total": 10,
                "unique": 10,
                "p0": 1,
                "p1": 7,
                "p2": 2,
                "required_input_complete": 10,
                "required_output_complete": 10,
                "human_review_boundary_complete": 10,
                "forbidden_automatic_action_complete": 10,
                "high_risk_automation_authorized_count": 0,
                "out_of_scope_business_line_count": 0,
            },
            "scope_lock_accounting": {
                "total": 37,
                "keep_governance_baseline": 12,
                "rebuild": 12,
                "defer": 8,
                "deprecate": 5,
                "product_acceptance_inherited_count": 0,
                "implementation_allowed_count": 0,
                "v15_product_capability_accepted_count": 0,
            },
            "conflict_control": {
                "total": 1,
                "resolved_normatively": 1,
                "implementation_open": 1,
                "unresolved_normative_conflicts": 0,
                "r007_disposition": "RESOLVED_BY_V15_PRECEDENCE_IMPLEMENTATION_OPEN",
            },
            "phase_result": {
                "execution_status": "EXECUTION_COMPLETE",
                "evidence_validation_status": "PENDING",
                "final_validation_status": "PENDING",
                "acceptance_status": "PENDING_FINAL_VALIDATION",
                "decision": "PENDING_FINAL_VALIDATION",
            },
            "stage_state": {
                "stage_id": "S02",
                "stage_lifecycle_status": "IN_PROGRESS",
                "stage_acceptance_status": "PENDING",
                "stage_passed": False,
                "completed_phase_count": 1,
                "total_phase_count": 3,
            },
            "next_entry_gate": {
                "next_allowed_taskpack_phase": "S02-P2",
                "s02_p2_entry_allowed": False,
                "s02_p2_started_in_current_run": False,
                "s02_p3_entry_allowed": False,
                "s03_plus_entry_allowed": False,
                "product_implementation_allowed": False,
            },
            "downstream_actions": {
                "s02_p2_started": False,
                "s02_p3_started": False,
                "s03_plus_started": False,
                "technology_stack_selected": False,
                "product_runtime_implementation_performed": False,
                "api_implementation_performed": False,
                "database_implementation_performed": False,
                "ui_implementation_performed": False,
                "raw_business_content_read": False,
                "raw_root_listed_or_inventoried": False,
                "raw_inbox_mutated": False,
                "business_execution_performed": False,
                "github_upload_performed": False,
                "app_reinstall_performed": False,
            },
            "artifact_refs": copy.deepcopy(EXPECTED_ARTIFACT_REFS),
            "artifact_integrity": [],
            "content_hash": "sha256:PENDING",
        }
        manifest["artifact_integrity"] = self._integrity_rows()
        manifest["content_hash"] = _canonical_content_hash(manifest)
        return manifest

    def _integrity_rows(self) -> list[dict[str, object]]:
        return [
            {
                "ref": ref,
                "bytes": self.artifact_overrides[ref].stat().st_size,
                "sha256": hashlib.sha256(self.artifact_overrides[ref].read_bytes()).hexdigest(),
            }
            for ref in sorted(EXPECTED_INTEGRITY_REFS)
        ]

    def _refresh_manifest(self) -> None:
        value = json.loads(self.paths["manifest"].read_text(encoding="utf-8"))
        value["artifact_integrity"] = self._integrity_rows()
        value["content_hash"] = _canonical_content_hash(value)
        _write_json(self.paths["manifest"], value)

    def _mutate_manifest(self, mutation, *, rehash: bool = True) -> None:
        value = json.loads(self.paths["manifest"].read_text(encoding="utf-8"))
        mutation(value)
        if rehash:
            value["content_hash"] = _canonical_content_hash(value)
        _write_json(self.paths["manifest"], value)

    def _mutate_csv(self, key: str, mutation) -> None:
        header, rows = _read_csv(self.paths[key])
        mutation(header, rows)
        _write_csv(self.paths[key], header, rows)
        self._refresh_manifest()

    def _mutate_receipts(self, mutation) -> None:
        rows = _read_jsonl(self.paths["receipts"])
        mutation(rows)
        _write_jsonl(self.paths["receipts"], rows)
        self._refresh_manifest()

    def _finalize(self) -> None:
        def update(value):
            value["generated_at"] = "2026-07-13T13:06:15+10:00"
            value["phase_result"] = {
                "execution_status": "EXECUTION_COMPLETE",
                "evidence_validation_status": "PASS",
                "final_validation_status": "PASS",
                "acceptance_status": "PASSED",
                "decision": "CONTINUE_TO_S02_P2_ONLY",
            }
            value["next_entry_gate"]["s02_p2_entry_allowed"] = True

        self._mutate_manifest(update)
        rows = _read_jsonl(self.paths["receipts"])
        for row in rows:
            row["result"] = "PASS"
            row["exit_code"] = 0
        _write_jsonl(self.paths["receipts"], rows)
        _write_jsonl(self.paths["events"], [self._event(final=False), self._event(final=True)])
        self._refresh_manifest()

    def _validate(
        self,
        *,
        strict: bool = False,
        require_source: bool = False,
        require_dependencies: bool = False,
        require_roadmap: bool = False,
        require_clean: bool = False,
    ):
        return validate_v015_s02_p1_requirements_scope_lock(
            self.paths["manifest"],
            requirements_path=self.paths["requirements"],
            business_lines_path=self.paths["business"],
            scope_lock_path=self.paths["scope"],
            validation_results_path=self.paths["receipts"],
            amendment_manifest_path=self.dependency_paths["amendment"],
            s01p2_manifest_path=self.dependency_paths["s01p2_manifest"],
            s01p2_gap_path=self.dependency_paths["gap"],
            s01p2_migration_path=self.dependency_paths["migration"],
            project_governance_path=self.paths["project"],
            roadmap_governance_path=self.paths["roadmap"],
            agents_path=self.paths["agents"],
            events_path=self.paths["events"],
            model_spec_path=self.paths["model_spec"],
            artifact_path_overrides=self.artifact_overrides,
            source_package=self.source_package,
            require_source_package=require_source,
            require_validation_receipts=strict,
            require_dependency_validators=require_dependencies,
            require_roadmap_sync=require_roadmap,
            require_clean_worktree=require_clean,
            repo_root=REPO_ROOT,
        )

    def _assert_rejected(self, *, strict: bool = False, **kwargs) -> None:
        with self.assertRaises(ValidationError):
            self._validate(strict=strict, **kwargs)

    def test_builder_and_validator_contract_is_available(self) -> None:
        self.assertTrue(callable(expected_core_outputs))
        self.assertTrue(callable(validate_v015_s02_p1_requirements_scope_lock))
        self.assertEqual(len(expected_core_outputs()), 5)

    def test_validates_pending_non_strict_cohort(self) -> None:
        result = self._validate(require_source=True)
        self.assertEqual(result["phase_result"]["acceptance_status"], "PENDING_FINAL_VALIDATION")

    def test_validates_final_strict_cohort(self) -> None:
        self._finalize()
        result = self._validate(strict=True, require_source=True)
        self.assertEqual(result["phase_result"]["decision"], "CONTINUE_TO_S02_P2_ONLY")

    def test_rejects_failed_dependency_validator(self) -> None:
        completed = subprocess.CompletedProcess([], 1, stdout="", stderr="dependency failed")
        with patch("KMFA.tools.check_v015_s02_p1_requirements_scope_lock.subprocess.run", return_value=completed):
            self._assert_rejected(require_dependencies=True)

    def test_rejects_failed_roadmap_sync(self) -> None:
        completed = subprocess.CompletedProcess([], 1, stdout="", stderr="roadmap failed")
        with patch("KMFA.tools.check_v015_s02_p1_requirements_scope_lock.subprocess.run", return_value=completed):
            self._assert_rejected(require_roadmap=True)

    def test_rejects_required_source_package_missing(self) -> None:
        self.source_package = None
        self._assert_rejected(require_source=True)

    def test_rejects_dirty_or_uncommitted_clean_gate(self) -> None:
        self._finalize()
        self._assert_rejected(strict=True, require_clean=True)

    def _apply_case(self, case: tuple) -> bool:
        kind = case[0]
        strict = False
        if kind == "manifest_set":
            path, new_value = case[1], case[2]

            def mutate(value):
                cursor = value
                for key in path[:-1]:
                    cursor = cursor[key]
                cursor[path[-1]] = new_value

            self._mutate_manifest(mutate)
        elif kind == "manifest_del":
            self._mutate_manifest(lambda value: value.pop(case[1]))
        elif kind == "manifest_add":
            self._mutate_manifest(lambda value: value.update({case[1]: case[2]}))
        elif kind == "manifest_bad_hash":
            self._mutate_manifest(lambda value: value.update({"content_hash": "sha256:" + "0" * 64}), rehash=False)
        elif kind in {"req_set", "business_set", "scope_set"}:
            key = {"req_set": "requirements", "business_set": "business", "scope_set": "scope"}[kind]
            id_field = {"requirements": "requirement_id", "business": "business_line_id", "scope": "capability_id"}[key]
            row_id, field, new_value = case[1], case[2], case[3]
            self._mutate_csv(key, lambda _header, rows: next(row for row in rows if row[id_field] == row_id).__setitem__(field, new_value))
        elif kind in {"req_drop", "business_drop", "scope_drop"}:
            key = {"req_drop": "requirements", "business_drop": "business", "scope_drop": "scope"}[kind]
            id_field = {"requirements": "requirement_id", "business": "business_line_id", "scope": "capability_id"}[key]
            row_id = case[1]
            self._mutate_csv(key, lambda _header, rows: rows.__setitem__(slice(None), [row for row in rows if row[id_field] != row_id]))
        elif kind in {"req_dup", "business_dup", "scope_dup"}:
            key = {"req_dup": "requirements", "business_dup": "business", "scope_dup": "scope"}[kind]
            id_field = {"requirements": "requirement_id", "business": "business_line_id", "scope": "capability_id"}[key]
            row_id = case[1]
            self._mutate_csv(key, lambda _header, rows: rows.append(copy.deepcopy(next(row for row in rows if row[id_field] == row_id))))
        elif kind == "header":
            key = case[1]
            def mutate_header(header, rows):
                old = header[0]
                header[0] = "unexpected_column"
                for row in rows:
                    row["unexpected_column"] = row.pop(old)

            self._mutate_csv(key, mutate_header)
        elif kind == "receipt_drop":
            self._mutate_receipts(lambda rows: rows.pop())
        elif kind == "receipt_dup":
            self._mutate_receipts(lambda rows: rows.append(copy.deepcopy(rows[0])))
        elif kind == "receipt_nonzero":
            self._mutate_receipts(lambda rows: rows[0].update(result="PASS", exit_code=1))
        elif kind == "receipt_pending_strict":
            self._finalize()
            self._mutate_receipts(lambda rows: rows[0].update(result="PENDING", exit_code=None))
            strict = True
        elif kind == "event_set":
            row_index, field, new_value = case[1], case[2], case[3]
            rows = _read_jsonl(self.paths["events"])
            rows[row_index][field] = new_value
            _write_jsonl(self.paths["events"], rows)
        elif kind == "event_final_set":
            field, new_value = case[1], case[2]
            self._finalize()
            rows = _read_jsonl(self.paths["events"])
            rows[1][field] = new_value
            _write_jsonl(self.paths["events"], rows)
            strict = True
        elif kind == "manifest_final_set":
            path, new_value = case[1], case[2]
            self._finalize()

            def mutate_final(value):
                cursor = value
                for key in path[:-1]:
                    cursor = cursor[key]
                cursor[path[-1]] = new_value

            self._mutate_manifest(mutate_final)
            strict = True
        elif kind == "event_final_only":
            _write_jsonl(self.paths["events"], [self._event(final=True)])
        elif kind == "event_reversed":
            _write_jsonl(self.paths["events"], [self._event(final=True), self._event(final=False)])
        elif kind == "text_replace":
            key, old, new = case[1], case[2], case[3]
            self.paths[key].write_text(self.paths[key].read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
        elif kind == "integrity_drop":
            self._mutate_manifest(lambda value: value["artifact_integrity"].pop())
        elif kind == "integrity_sha":
            self._mutate_manifest(lambda value: value["artifact_integrity"][0].update(sha256="0" * 64))
        elif kind == "dependency_file_drift":
            dependency_key, canonical = case[1], case[2]
            target = Path(self.temporary.name) / f"{dependency_key}.drift"
            shutil.copyfile(canonical, target)
            target.write_bytes(target.read_bytes() + b"\n")
            self.dependency_paths[dependency_key] = target
        else:
            raise AssertionError(f"unknown mutation kind: {kind}")
        return strict


MUTATION_CASES = [
    ("schema_drift", "manifest_set", ("schema_version",), "bad.schema"),
    ("missing_top_level_key", "manifest_del", "work_kind"),
    ("extra_top_level_key", "manifest_add", "unexpected", True),
    ("stage_id_drift", "manifest_set", ("stage_id",), "S03"),
    ("roadmap_phase_drift", "manifest_set", ("roadmap_phase_id",), "S02-P2"),
    ("run_phase_drift", "manifest_set", ("run_phase_id",), "V015_S02_P2"),
    ("task_id_drift", "manifest_set", ("task_id",), "wrong"),
    ("acceptance_id_drift", "manifest_set", ("acceptance_id",), "wrong"),
    ("base_commit_drift", "manifest_set", ("phase_base_commit",), "0" * 40),
    ("source_sha_drift", "manifest_set", ("source_package", "sha256"), "0" * 64),
    ("source_requirement_count_drift", "manifest_set", ("source_package", "requirement_count"), 54),
    ("source_priority_count_drift", "manifest_set", ("source_package", "priority_counts", "P0"), 45),
    ("source_member_sha_drift", "manifest_set", ("source_package", "members", "requirements", "sha256"), "0" * 64),
    ("dependency_count_drift", "manifest_set", ("dependency_evidence", "count"), 3),
    ("dependency_id_drift", "manifest_set", ("dependency_evidence", "dependencies", 0, "dependency_id"), "wrong"),
    ("dependency_sha_binding_drift", "manifest_set", ("dependency_evidence", "dependencies", 0, "sha256"), "0" * 64),
    ("dependency_content_hash_binding_drift", "manifest_set", ("dependency_evidence", "dependencies", 0, "content_hash"), "sha256:" + "0" * 64),
    ("source_scope_normative_keep_drift", "manifest_set", ("source_scope_policy", "normative_keep_and_reverify_count"), 12),
    ("source_scope_normative_rebuild_drift", "manifest_set", ("source_scope_policy", "normative_rebuild_count"), 12),
    ("source_scope_normative_deprecate_drift", "manifest_set", ("source_scope_policy", "normative_deprecate_as_acceptance_baseline_count"), 5),
    ("source_scope_capability_count_conflated", "manifest_set", ("source_scope_policy", "evidence_qualified_capability_count"), 40),
    ("source_scope_counts_conflated_true", "manifest_set", ("source_scope_policy", "normative_list_counts_used_as_capability_counts"), True),
    ("deferred_requirement_ids_drift", "manifest_set", ("source_scope_policy", "deferred_requirement_ids"), ["R052", "R053"]),
    ("requirements_header_drift", "header", "requirements"),
    ("requirements_missing_r001", "req_drop", "R001"),
    ("requirements_missing_r055", "req_drop", "R055"),
    ("requirements_duplicate_r001", "req_dup", "R001"),
    ("requirements_unknown_r056", "req_set", "R055", "requirement_id", "R056"),
    ("requirements_priority_drift", "req_set", "R001", "priority", "P1"),
    ("requirements_name_drift", "req_set", "R001", "requirement_name", "drift"),
    ("requirements_normative_text_drift", "req_set", "R001", "normative_requirement", "drift"),
    ("requirements_raw_root_detokenized", "req_set", "R005", "normative_requirement", "本机 /Users/example/Downloads/KMFA_MetaData 只读"),
    ("requirements_owner_email_detokenized", "req_set", "R046", "normative_requirement", "发送至 private@example.com"),
    ("requirements_source_sha_drift", "req_set", "R001", "source_member_sha256", "0" * 64),
    ("requirements_primary_stage_drift", "req_set", "R001", "primary_stage_refs", "S24"),
    ("requirements_task_refs_drift", "req_set", "R001", "task_refs", "S24P3T01"),
    ("requirements_acceptance_missing", "req_set", "R001", "acceptance_requirement", ""),
    ("requirements_acceptance_nonempty_drift", "req_set", "R001", "acceptance_requirement", "错误但非空的验收要求"),
    ("requirements_evidence_missing", "req_set", "R001", "evidence_requirement", ""),
    ("requirements_evidence_nonempty_drift", "req_set", "R001", "evidence_requirement", "错误但非空的证据要求"),
    ("requirements_current_status_drift", "req_set", "R001", "current_implementation_status", "PASSED"),
    ("requirements_gap_type_drift", "req_set", "R001", "implementation_gap_type", "NONE"),
    ("requirements_severity_drift", "req_set", "R001", "severity", "LOW"),
    ("requirements_gap_impact_drift", "req_set", "R001", "gap_impact", "none"),
    ("requirements_current_evidence_drift", "req_set", "R001", "current_evidence_refs", "KMFA/AGENTS.md"),
    ("requirements_migration_drift", "req_set", "R001", "migration_disposition", "KEEP"),
    ("r007_conflict_unresolved", "req_set", "R007", "conflict_status", "UNRESOLVED"),
    ("r007_false_implementation_closed", "req_set", "R007", "current_implementation_status", "PARTIAL_VERIFIED"),
    ("r007_target_stage_drift", "req_set", "R007", "resolution_target_stage", "S02"),
    ("non_r007_conflict_added", "req_set", "R008", "conflict_status", "UNRESOLVED"),
    ("requirement_false_acceptance", "req_set", "R008", "v15_requirement_accepted", "true"),
    ("requirement_implementation_authorized", "req_set", "R008", "implementation_allowed_by_s02_p1", "true"),
    ("requirement_public_safe_drift", "req_set", "R008", "public_safe_status", "PRIVATE"),
    ("requirement_normalized_duplicate_name", "req_set", "R002", "requirement_name", "系统名称与项目形态"),
    ("business_header_drift", "header", "business"),
    ("business_missing_bl01", "business_drop", "BL-01"),
    ("business_duplicate_bl01", "business_dup", "BL-01"),
    ("business_line_11_added", "business_set", "BL-10", "business_line_id", "BL-11"),
    ("business_priority_drift", "business_set", "BL-01", "priority", "P1"),
    ("business_name_drift", "business_set", "BL-01", "business_line_name", "drift"),
    ("business_manual_work_missing", "business_set", "BL-01", "first_manual_work_to_replace", ""),
    ("business_input_missing", "business_set", "BL-01", "input_classes", ""),
    ("business_output_missing", "business_set", "BL-01", "output_classes", ""),
    ("business_human_boundary_missing", "business_set", "BL-01", "human_review_boundary", ""),
    ("business_prohibited_actions_missing", "business_set", "BL-01", "prohibited_automatic_actions", ""),
    ("business_stage_invalid", "business_set", "BL-01", "recommended_stage_ids", "S25"),
    ("business_routing_claim_complete", "business_set", "BL-01", "routing_status", "TRACEABILITY_COMPLETE"),
    ("business_product_acceptance_inherited", "business_set", "BL-01", "product_acceptance_inherited", "true"),
    ("business_implementation_authorized", "business_set", "BL-01", "implementation_allowed_by_s02_p1", "true"),
    ("scope_header_drift", "header", "scope"),
    ("scope_missing_cap001", "scope_drop", "CAP-001"),
    ("scope_duplicate_cap001", "scope_dup", "CAP-001"),
    ("scope_unknown_cap038", "scope_set", "CAP-037", "capability_id", "CAP-038"),
    ("scope_class_drift", "scope_set", "CAP-001", "v15_scope_class", "REBUILD"),
    ("scope_historical_decision_drift", "scope_set", "CAP-001", "s01_p2_historical_decision", "REFACTOR"),
    ("scope_verification_status_drift", "scope_set", "CAP-001", "verification_status", "UNVERIFIED"),
    ("scope_source_evidence_drift", "scope_set", "CAP-001", "source_evidence_refs", "KMFA/AGENTS.md"),
    ("scope_rationale_drift", "scope_set", "CAP-001", "scope_rationale", "drift"),
    ("scope_target_stage_drift", "scope_set", "CAP-001", "target_stage", "S24"),
    ("scope_constraint_drift", "scope_set", "CAP-001", "preservation_constraint", "none"),
    ("scope_product_acceptance_inherited", "scope_set", "CAP-001", "product_acceptance_inherited", "true"),
    ("scope_implementation_authorized", "scope_set", "CAP-001", "implementation_allowed_by_s02_p1", "true"),
    ("scope_accounting_total_drift", "manifest_set", ("scope_lock_accounting", "total"), 40),
    ("scope_accounting_keep_drift", "manifest_set", ("scope_lock_accounting", "keep_governance_baseline"), 15),
    ("task_missing", "manifest_set", ("tasks",), []),
    ("task_failure", "manifest_set", ("tasks", 0, "acceptance_status"), "NOT_PASSED"),
    ("task_name_drift", "manifest_set", ("tasks", 0, "name"), "drift"),
    ("task_accounting_drift", "manifest_set", ("task_accounting", "accepted"), 2),
    ("phase_false_pass_pending", "manifest_set", ("phase_result", "acceptance_status"), "PASSED"),
    ("stage_marked_passed", "manifest_set", ("stage_state", "stage_passed"), True),
    ("stage_acceptance_passed", "manifest_set", ("stage_state", "stage_acceptance_status"), "PASSED"),
    ("next_gate_beyond_p2", "manifest_set", ("next_entry_gate", "next_allowed_taskpack_phase"), "S02-P3"),
    ("early_s02_p2_open", "manifest_set", ("next_entry_gate", "s02_p2_entry_allowed"), True),
    ("s02_p3_open", "manifest_set", ("next_entry_gate", "s02_p3_entry_allowed"), True),
    ("product_gate_open", "manifest_set", ("next_entry_gate", "product_implementation_allowed"), True),
    ("phase_scope_traceability_claim", "manifest_set", ("phase_scope", "s02_p2_traceability_performed"), True),
    ("phase_scope_stack_selection", "manifest_set", ("phase_scope", "technology_stack_selection_allowed"), True),
    ("downstream_runtime_claim", "manifest_set", ("downstream_actions", "product_runtime_implementation_performed"), True),
    ("downstream_raw_read_claim", "manifest_set", ("downstream_actions", "raw_business_content_read"), True),
    ("downstream_raw_inventory_claim", "manifest_set", ("downstream_actions", "raw_root_listed_or_inventoried"), True),
    ("downstream_raw_mutation_claim", "manifest_set", ("downstream_actions", "raw_inbox_mutated"), True),
    ("downstream_business_claim", "manifest_set", ("downstream_actions", "business_execution_performed"), True),
    ("downstream_upload_claim", "manifest_set", ("downstream_actions", "github_upload_performed"), True),
    ("downstream_reinstall_claim", "manifest_set", ("downstream_actions", "app_reinstall_performed"), True),
    ("artifact_ref_traversal", "manifest_set", ("artifact_refs", "requirements_ledger"), "../outside.csv"),
    ("integrity_row_missing", "integrity_drop"),
    ("integrity_sha_drift", "integrity_sha"),
    ("manifest_content_hash_drift", "manifest_bad_hash"),
    ("receipt_missing", "receipt_drop"),
    ("receipt_duplicate", "receipt_dup"),
    ("receipt_pass_nonzero", "receipt_nonzero"),
    ("receipt_pending_in_strict", "receipt_pending_strict"),
    ("execution_event_early_open", "event_set", 0, "s02_p2_entry_allowed", True),
    ("execution_event_false_pass", "event_set", 0, "phase_acceptance_status", "PASSED"),
    ("execution_event_time_missing", "event_set", 0, "event_time", ""),
    ("execution_event_time_naive", "event_set", 0, "event_time", "2026-07-13T13:01:38"),
    ("execution_event_type_drift", "event_set", 0, "event_type", "final_validation"),
    ("pending_manifest_precedes_execution", "manifest_set", ("generated_at",), "2026-07-13T13:00:00+10:00"),
    ("final_event_time_missing", "event_final_set", "event_time", ""),
    ("final_event_time_naive", "event_final_set", "event_time", "2026-07-13T13:06:15"),
    ("final_event_time_before_execution", "event_final_set", "event_time", "2026-07-13T13:00:00+10:00"),
    ("final_event_type_drift", "event_final_set", "event_type", "phase_execution"),
    ("final_manifest_generated_at_drift", "manifest_final_set", ("generated_at",), "2026-07-13T13:06:16+10:00"),
    ("final_event_without_execution", "event_final_only"),
    ("events_reversed", "event_reversed"),
    ("project_current_stage_drift", "text_replace", "project", 'current_stage_id: "S02"', 'current_stage_id: "S01"'),
    ("roadmap_current_phase_drift", "text_replace", "roadmap", 'current_phase_id: "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK"', 'current_phase_id: "S02-P2"'),
    ("roadmap_count_drift", "text_replace", "roadmap", "active_task_count: 216", "active_task_count: 215"),
    ("historical_s01_acceptance_drift", "text_replace", "project", 's01_stage_review_acceptance_status: "NOT_PASSED"', 's01_stage_review_acceptance_status: "PASSED"'),
    ("historical_amendment_drift", "text_replace", "project", 's01_controlled_transition_amendment_acceptance_status: "PASSED"', 's01_controlled_transition_amendment_acceptance_status: "NOT_PASSED"'),
    ("agents_single_upload_rule_missing", "text_replace", "agents", "不得按单个 Stage 做 GitHub upload gate", "upload per Stage"),
    ("model_formula_token_missing", "text_replace", "model_spec", "requirement_count == 55", "requirement_count == 54"),
    ("amendment_dependency_file_drift", "dependency_file_drift", "amendment", AMENDMENT_MANIFEST_PATH),
    ("gap_dependency_file_drift", "dependency_file_drift", "gap", S01P2_GAP_PATH),
    ("migration_dependency_file_drift", "dependency_file_drift", "migration", S01P2_MIGRATION_PATH),
]


def _make_mutation_test(case: tuple):
    name, *payload = case

    def test(self: TestV015S02P1RequirementsMerge) -> None:
        strict = self._apply_case(tuple(payload))
        self._assert_rejected(strict=strict)

    test.__name__ = f"test_mutation_{name}"
    return test


for _case in MUTATION_CASES:
    setattr(TestV015S02P1RequirementsMerge, f"test_mutation_{_case[0]}", _make_mutation_test(_case))


if __name__ == "__main__":
    unittest.main()
