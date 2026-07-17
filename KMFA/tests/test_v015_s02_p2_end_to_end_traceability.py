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


if __name__ == "__main__":
    unittest.main()
