from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.build_v015_s02_p2_end_to_end_traceability import (
    DEFAULT_SOURCE_PACKAGE,
    expected_core_outputs,
)
from KMFA.tools.check_v015_s02_p2_end_to_end_traceability import (
    MANIFEST_PATH,
    ValidationError,
    _canonical_content_hash,
    _validate_governance,
    validate_v015_s02_p2_end_to_end_traceability,
)


class TestV015S02P2EndToEndTraceability(unittest.TestCase):
    def test_builder_and_validator_contract_is_available(self) -> None:
        self.assertTrue(callable(expected_core_outputs))
        self.assertTrue(callable(validate_v015_s02_p2_end_to_end_traceability))

    def test_core_outputs_are_exact_and_public_safe(self) -> None:
        outputs = expected_core_outputs(source_package=DEFAULT_SOURCE_PACKAGE)
        self.assertEqual(7, len(outputs))
        self.assertEqual(
            {
                "requirement_task_traceability_public_safe.csv",
                "data_report_lineage_field_contract_public_safe.json",
                "lineage_layer_edge_contract_public_safe.csv",
                "source_domain_lineage_coverage_public_safe.csv",
                "formula_test_traceability_public_safe.csv",
                "formula_parameter_traceability_public_safe.csv",
                "end_to_end_traceability_zh.md",
            },
            {path.name for path in outputs},
        )
        combined = b"\n".join(outputs.values())
        self.assertNotIn(b"/Users/", combined)
        self.assertNotIn(b"KMFA_MetaData", combined)
        self.assertEqual(
            outputs,
            expected_core_outputs(source_package=DEFAULT_SOURCE_PACKAGE),
        )

    def test_core_accounting_is_fail_closed(self) -> None:
        outputs = expected_core_outputs(source_package=DEFAULT_SOURCE_PACKAGE)
        by_name = {path.name: payload for path, payload in outputs.items()}
        requirements = list(
            csv.DictReader(
                io.StringIO(
                    by_name[
                        "requirement_task_traceability_public_safe.csv"
                    ].decode("utf-8")
                )
            )
        )
        formulas = list(
            csv.DictReader(
                io.StringIO(
                    by_name["formula_test_traceability_public_safe.csv"].decode(
                        "utf-8"
                    )
                )
            )
        )
        parameters = list(
            csv.DictReader(
                io.StringIO(
                    by_name[
                        "formula_parameter_traceability_public_safe.csv"
                    ].decode("utf-8")
                )
            )
        )
        lineage = json.loads(
            by_name[
                "data_report_lineage_field_contract_public_safe.json"
            ].decode("utf-8")
        )
        self.assertEqual((len(requirements), len(formulas), len(parameters)), (134, 22, 38))
        self.assertEqual(lineage["actual_lineage_record_count"], 0)
        self.assertFalse(lineage["lineage_full_check_complete"])
        self.assertFalse(lineage["formal_report_allowed"])
        self.assertTrue(all(row["runtime_enablement"] == "false" for row in formulas))
        self.assertTrue(all(row["runtime_enablement"] == "false" for row in parameters))

    def test_strict_validator_rebuilds_and_accepts_final_evidence(self) -> None:
        result = validate_v015_s02_p2_end_to_end_traceability()
        self.assertEqual(result["phase_result"]["acceptance_status"], "PASSED")
        self.assertEqual(result["trace_accounting"]["normalized_binding_count"], 134)
        self.assertEqual(result["lineage_accounting"]["actual_lineage_record_count"], 0)
        self.assertEqual(result["formula_accounting"]["runtime_enabled_count"], 0)

    def _assert_manifest_mutation_rejected(self, mutate) -> None:
        value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        mutate(value)
        value["content_hash"] = _canonical_content_hash(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValidationError):
                validate_v015_s02_p2_end_to_end_traceability(path)

    def test_manifest_mutations_fail_closed(self) -> None:
        cases = {
            "product_scope": lambda value: value["phase_scope"].update(
                product_implementation_allowed=True
            ),
            "trace_count": lambda value: value["trace_accounting"].update(
                normalized_binding_count=133
            ),
            "actual_lineage": lambda value: value["lineage_accounting"].update(
                actual_lineage_record_count=1
            ),
            "formula_count": lambda value: value["formula_accounting"].update(
                formula_count=15
            ),
            "next_phase_started": lambda value: value["next_entry_gate"].update(
                s02_p3_started_in_current_run=True
            ),
            "downstream_key_drop": lambda value: value.update(
                downstream_actions={}
            ),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                self._assert_manifest_mutation_rejected(mutate)

    def test_p3_active_governance_is_a_legal_strict_predecessor_successor(self) -> None:
        common = {
            "current_stage_id": "S02",
            "current_phase_id": "V015_S02_P3_SCOPE_GATE",
            "current_task_id": "KMFA-V015-S02-P3-SCOPE-GATE-20260713",
            "current_acceptance_id": "ACC-KMFA-V015-S02-P3-SCOPE-GATE",
            "decision": "CONTINUE_TO_S02_STAGE_REVIEW_ONLY",
            "stage_lifecycle_status": "IN_PROGRESS",
            "stage_acceptance_status": "PENDING",
            "s02_p1_acceptance_status": "PASSED",
            "s02_p2_acceptance_status": "PASSED",
            "s02_p3_acceptance_status": "PASSED",
            "s02_p3_entry_allowed": "false",
            "s02_p3_started": "true",
            "s02_stage_review_entry_allowed": "true",
            "s02_stage_review_started_in_p3_run": "false",
            "s03_entry_allowed": "false",
            "product_implementation_allowed": "false",
            "next_gate_id": "S02-STAGE-REVIEW",
            "s01_stage_review_lifecycle_status": "BLOCKED",
            "s01_stage_review_acceptance_status": "NOT_PASSED",
            "s01_stage_review_decision": "NO_GO",
            "s01_controlled_transition_amendment_acceptance_status": "PASSED",
            "s01_controlled_transition_amendment_decision": "GO_TO_S02_P1_ONLY",
        }

        def yaml_text(values: dict[str, str]) -> str:
            return "\n".join(f'{key}: "{value}"' for key, value in values.items())

        project = yaml_text(common)
        roadmap = yaml_text(
            {
                **common,
                "active_stage_count": "24",
                "active_phase_count": "72",
                "active_task_count": "216",
            }
        )
        agents = "\n".join(
            (
                "V015_S02_P2_END_TO_END_TRACEABILITY",
                "S02-P3 only",
                "不得按单个 Stage 做 GitHub upload gate",
                "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8",
            )
        )
        model_spec = "\n".join(
            (
                "FORM-KMFA-V015-S02-P2-END-TO-END-TRACEABILITY-001",
                "normalized_trace_binding_count == 134",
                "actual_lineage_record_count == 0",
                "formula_model_count == 22",
                "s02_p3_entry_allowed == true",
            )
        )
        errors: list[str] = []
        _validate_governance(
            errors,
            project_text=project,
            roadmap_text=roadmap,
            agents_text=agents,
            model_spec_text=model_spec,
        )
        self.assertEqual(errors, [])

        errors = []
        _validate_governance(
            errors,
            project_text=project.replace(
                's02_p2_acceptance_status: "PASSED"',
                's02_p2_acceptance_status: "PENDING"',
            ),
            roadmap_text=roadmap,
            agents_text=agents,
            model_spec_text=model_spec,
        )
        self.assertTrue(any("S02-P2 historical acceptance" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
