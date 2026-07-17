from __future__ import annotations

import copy
import csv
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from KMFA.tools.v015_s02_p2_formula_trace import (
    EXPECTED_CONTROL_KIND_COUNTS,
    EXPECTED_DEFINITION_IDS,
    EXPECTED_PARAMETER_COUNT,
    EXPECTED_RAW_STATUS_COUNTS,
    SOURCE_PACKAGE_NAME,
    build_formula_trace,
    build_parameter_trace,
    summarize_legacy_governance,
    validate_formula_parameter_trace,
)


SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME


class TestV015S02P2FormulaTrace(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SOURCE_PACKAGE.is_file():
            raise AssertionError(f"authoritative TaskPack source missing: {SOURCE_PACKAGE}")
        cls.formulas = build_formula_trace(SOURCE_PACKAGE)
        cls.parameters = build_parameter_trace(SOURCE_PACKAGE)

    def test_exact_source_universe_and_status_normalization(self) -> None:
        self.assertEqual(len(self.formulas), 22)
        self.assertEqual(
            {row["definition_id"] for row in self.formulas}, EXPECTED_DEFINITION_IDS
        )
        self.assertEqual(
            Counter(row["raw_status"] for row in self.formulas),
            Counter(EXPECTED_RAW_STATUS_COUNTS),
        )
        proposed = [row for row in self.formulas if row["raw_status"] == "PROPOSED"]
        verification_required = [
            row for row in self.formulas if row["raw_status"] == "VERIFIED_REQUIRED"
        ]
        self.assertEqual(len(proposed), 17)
        self.assertEqual(len(verification_required), 5)
        self.assertTrue(
            all(row["normalized_status"] == "PLANNED_NOT_ENABLED" for row in proposed)
        )
        self.assertTrue(
            all(
                row["normalized_status"] == "VERIFICATION_REQUIRED_NOT_ENABLED"
                for row in verification_required
            )
        )
        self.assertTrue(
            all(row["source_status_in_declared_vocabulary"] is False for row in verification_required)
        )

    def test_trace_is_complete_but_planning_only(self) -> None:
        for row in self.formulas:
            with self.subTest(definition_id=row["definition_id"]):
                self.assertTrue(row["source_refs"])
                self.assertTrue(row["planned_fixture_refs"])
                self.assertTrue(row["planned_report_refs"])
                self.assertEqual(row["fixture_status"], "PLANNED_NOT_IMPLEMENTED")
                self.assertEqual(row["report_status"], "PLANNED_NOT_IMPLEMENTED")
                self.assertEqual(row["executable_fixture_refs"], [])
                self.assertEqual(row["test_execution_refs"], [])
                self.assertEqual(row["report_artifact_refs"], [])
                self.assertIs(row["runtime_implementation_present"], False)
                self.assertIs(row["runtime_enablement"], False)
                self.assertIs(row["product_implementation_claimed"], False)
                self.assertIs(row["legacy_active_status_inherited"], False)
        self.assertEqual(
            validate_formula_parameter_trace(self.formulas, self.parameters), []
        )

    def test_source_test_descriptions_are_not_executable_fixtures(self) -> None:
        by_id = {row["definition_id"]: row for row in self.formulas}
        self.assertEqual(len(by_id["AMT-NORMALIZE-001"]["source_test_descriptions"]), 7)
        self.assertEqual(by_id["AMT-NORMALIZE-001"]["executable_fixture_refs"], [])
        self.assertEqual(
            sum(bool(row["source_test_descriptions"]) for row in self.formulas), 1
        )
        self.assertTrue(all(not row["executable_fixture_refs"] for row in self.formulas))

    def test_exact_parameter_threshold_universe(self) -> None:
        self.assertEqual(len(self.parameters), EXPECTED_PARAMETER_COUNT)
        self.assertEqual(
            Counter(row["control_kind"] for row in self.parameters),
            Counter(EXPECTED_CONTROL_KIND_COUNTS),
        )
        self.assertTrue(
            all(not isinstance(row["declared_value"], float) for row in self.parameters)
        )
        unknown = [row for row in self.parameters if row["unknown_parameter"]]
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0]["parent_definition_ids"], ["CASH-RUNWAY-001"])
        self.assertEqual(unknown[0]["declared_value"], "1")
        self.assertEqual(
            unknown[0]["control_kind"], "INLINE_LITERAL_REQUIRES_EXTERNALIZATION"
        )
        self.assertIs(unknown[0]["default_usage_allowed"], False)
        self.assertIn("UNKNOWN_INLINE_LITERAL", unknown[0]["blocking_reasons"])

    def test_status_vocabulary_mismatch_fails_closed(self) -> None:
        formulas = copy.deepcopy(self.formulas)
        target = next(row for row in formulas if row["raw_status"] == "VERIFIED_REQUIRED")
        target["source_status_in_declared_vocabulary"] = True
        errors = validate_formula_parameter_trace(formulas, self.parameters)
        self.assertTrue(any("status-vocabulary mismatch" in item for item in errors), errors)

    def test_missing_source_fixture_or_report_cannot_enable(self) -> None:
        for field in ("source_refs", "planned_fixture_refs", "planned_report_refs"):
            with self.subTest(field=field):
                formulas = copy.deepcopy(self.formulas)
                formulas[0][field] = []
                formulas[0]["runtime_enablement"] = True
                errors = validate_formula_parameter_trace(formulas, self.parameters)
                self.assertTrue(any("missing" in item for item in errors), errors)
                self.assertTrue(any("runtime enablement" in item for item in errors), errors)

    def test_unknown_parameter_cannot_use_implicit_default(self) -> None:
        parameters = copy.deepcopy(self.parameters)
        unknown = next(row for row in parameters if row["unknown_parameter"])
        unknown["default_usage_allowed"] = True
        errors = validate_formula_parameter_trace(self.formulas, parameters)
        self.assertTrue(any("silent/default runtime use" in item for item in errors), errors)

    def test_binary_float_fails_closed(self) -> None:
        parameters = copy.deepcopy(self.parameters)
        parameters[0]["declared_value"] = 0.2
        errors = validate_formula_parameter_trace(self.formulas, parameters)
        self.assertTrue(any("binary float" in item for item in errors), errors)

    def test_source_default_cannot_be_silently_activated(self) -> None:
        parameters = copy.deepcopy(self.parameters)
        source_default = next(row for row in parameters if row["control_kind"] == "DEFAULT")
        source_default["default_usage_allowed"] = True
        errors = validate_formula_parameter_trace(self.formulas, parameters)
        self.assertTrue(any("silent/default runtime use" in item for item in errors), errors)

    def test_legacy_active_status_cannot_be_inherited(self) -> None:
        formulas = copy.deepcopy(self.formulas)
        formulas[0]["legacy_active_status_inherited"] = True
        formulas[0]["runtime_enablement"] = True
        errors = validate_formula_parameter_trace(formulas, self.parameters)
        self.assertTrue(any("legacy active status" in item for item in errors), errors)
        self.assertTrue(any("runtime enablement" in item for item in errors), errors)

    def test_count_duplicate_and_status_drift_fail_closed(self) -> None:
        formulas = copy.deepcopy(self.formulas[:-1])
        errors = validate_formula_parameter_trace(formulas, self.parameters)
        self.assertTrue(any("count must be 22" in item for item in errors), errors)
        self.assertTrue(any("universe drift" in item for item in errors), errors)

        formulas = copy.deepcopy(self.formulas)
        formulas[0]["raw_status"] = "VERIFIED"
        errors = validate_formula_parameter_trace(formulas, self.parameters)
        self.assertTrue(any("status counts drifted" in item for item in errors), errors)
        self.assertTrue(any("unknown source status" in item for item in errors), errors)

        parameters = copy.deepcopy(self.parameters)
        parameters[1]["control_id"] = parameters[0]["control_id"]
        errors = validate_formula_parameter_trace(self.formulas, parameters)
        self.assertTrue(any("duplicate parameter" in item for item in errors), errors)

    def test_product_claim_always_fails_closed(self) -> None:
        formulas = copy.deepcopy(self.formulas)
        formulas[0]["product_implementation_claimed"] = True
        errors = validate_formula_parameter_trace(formulas, self.parameters)
        self.assertTrue(any("product implementation claim" in item for item in errors), errors)

    def test_list_fields_reject_stringified_or_malformed_json(self) -> None:
        for bad_value in ('["taskpack://forged"]', "[malformed"):
            with self.subTest(bad_value=bad_value):
                formulas = copy.deepcopy(self.formulas)
                formulas[0]["source_refs"] = bad_value
                errors = validate_formula_parameter_trace(formulas, self.parameters)
                self.assertTrue(any("source_refs must be a list[str]" in item for item in errors), errors)

        parameters = copy.deepcopy(self.parameters)
        parameters[0]["planned_fixture_refs"] = "fixture-contract://forged"
        errors = validate_formula_parameter_trace(self.formulas, parameters)
        self.assertTrue(
            any("planned_fixture_refs must be a list[str]" in item for item in errors),
            errors,
        )

    def test_public_safe_and_ref_scheme_mutations_fail_closed(self) -> None:
        formulas = copy.deepcopy(self.formulas)
        formulas[0]["planned_fixture_refs"] = ["leak@example.com"]
        errors = validate_formula_parameter_trace(formulas, self.parameters)
        self.assertTrue(any("public-safe email leak" in item for item in errors), errors)
        self.assertTrue(any("illegal ref scheme" in item for item in errors), errors)

        parameters = copy.deepcopy(self.parameters)
        parameters[0]["source_refs"] = ["file:///Users/example/private.yaml"]
        errors = validate_formula_parameter_trace(self.formulas, parameters)
        self.assertTrue(any("public-safe path/raw token leak" in item for item in errors), errors)
        self.assertTrue(any("illegal ref scheme" in item for item in errors), errors)

    def test_boolean_fields_reject_csv_string_values(self) -> None:
        formulas = copy.deepcopy(self.formulas)
        formulas[0]["runtime_enablement"] = "false"
        errors = validate_formula_parameter_trace(formulas, self.parameters)
        self.assertTrue(any("runtime_enablement must be bool" in item for item in errors), errors)

        parameters = copy.deepcopy(self.parameters)
        parameters[0]["requires_confirmation"] = "true"
        errors = validate_formula_parameter_trace(self.formulas, parameters)
        self.assertTrue(any("requires_confirmation must be bool" in item for item in errors), errors)

    def test_authoritative_expression_pointer_and_binding_drift_fail_closed(self) -> None:
        mutations = {
            "expression": "FORGED_EXPRESSION",
            "source_pointer": "/forged",
            "requirement_refs": ["R999"],
        }
        for field, bad_value in mutations.items():
            with self.subTest(field=field):
                formulas = copy.deepcopy(self.formulas)
                formulas[0][field] = bad_value
                errors = validate_formula_parameter_trace(formulas, self.parameters)
                self.assertTrue(
                    any(
                        f"{field} differs from authoritative source" in item
                        for item in errors
                    ),
                    errors,
                )

    def test_legacy_governance_is_summary_only(self) -> None:
        summary = summarize_legacy_governance()
        self.assertEqual(summary["scope_class"], "LEGACY_GOVERNANCE_EVIDENCE_ONLY")
        self.assertEqual(summary["formula_count"], 322)
        self.assertEqual(summary["formula_status_counts"], {"active": 322})
        self.assertEqual(
            summary["formula_fact_level_counts"], {"EXTRACTED": 296, "MISSING": 26}
        )
        self.assertEqual(summary["parameter_count"], 1460)
        self.assertEqual(summary["parameter_status_counts"], {"active": 1460})
        self.assertEqual(summary["model_count"], 8)
        self.assertEqual(summary["current_model_count_including_s02_p2_governance"], 9)
        self.assertEqual(summary["traceability_row_count"], 501)
        self.assertEqual(summary["traceability_formula_covered_count"], 292)
        self.assertEqual(summary["traceability_formula_missing_count"], 30)
        self.assertEqual(summary["traceability_parameter_covered_count"], 882)
        self.assertEqual(summary["traceability_parameter_missing_count"], 578)
        self.assertEqual(summary["formula_explicit_source_refs_count"], 0)
        self.assertEqual(summary["formula_explicit_fixture_refs_count"], 0)
        self.assertEqual(summary["formula_explicit_report_refs_count"], 0)
        self.assertEqual(summary["formula_without_report_like_evidence_count"], 3)
        self.assertEqual(summary["parameter_precommit_pending_count"], 1437)
        self.assertEqual(summary["parameter_pending_local_commit_evidence_count"], 1424)
        self.assertEqual(summary["v15_source_definition_overlap_count"], 0)
        self.assertIs(summary["runtime_enablement_inherited"], False)
        self.assertIs(summary["product_implementation_claimed"], False)

    def test_p3_governance_only_ids_do_not_inflate_legacy_summary(self) -> None:
        source = Path("KMFA/docs/governance")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "KMFA/docs/governance"
            target.mkdir(parents=True)
            for name in (
                "formula_registry.yaml",
                "parameter_registry.csv",
                "model_registry.yaml",
                "TRACEABILITY_MATRIX.csv",
            ):
                shutil.copy2(source / name, target / name)

            before = summarize_legacy_governance(directory)

            with (target / "formula_registry.yaml").open("a", encoding="utf-8") as handle:
                handle.write(
                    '\n  - formula_id: "FORM-KMFA-V015-S02-P3-SCOPE-GATE-001"\n'
                    '    model_id: "MOD-KMFA-V015-S02-P3-SCOPE-GATE-001"\n'
                    '    status: "active"\n'
                    '    fact_level: "EXTRACTED"\n'
                )
            with (target / "model_registry.yaml").open("a", encoding="utf-8") as handle:
                handle.write(
                    '\n  - model_id: "MOD-KMFA-V015-S02-P3-SCOPE-GATE-001"\n'
                    '    status: "active"\n'
                )

            parameter_path = target / "parameter_registry.csv"
            with parameter_path.open(encoding="utf-8-sig", newline="") as handle:
                parameter_reader = csv.DictReader(handle)
                parameter_fields = parameter_reader.fieldnames or []
                parameter_rows = list(parameter_reader)
            parameter_rows.append(
                {
                    **{field: "" for field in parameter_fields},
                    "parameter_id": "PARAM-KMFA-P3-SYNTHETIC",
                    "model_id": "MOD-KMFA-V015-S02-P3-SCOPE-GATE-001",
                    "formula_id": "FORM-KMFA-V015-S02-P3-SCOPE-GATE-001",
                    "status": "active",
                    "fact_level": "EXTRACTED",
                }
            )
            with parameter_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=parameter_fields)
                writer.writeheader()
                writer.writerows(parameter_rows)

            trace_path = target / "TRACEABILITY_MATRIX.csv"
            with trace_path.open(encoding="utf-8-sig", newline="") as handle:
                trace_reader = csv.DictReader(handle)
                trace_fields = trace_reader.fieldnames or []
                trace_rows = list(trace_reader)
            trace_rows.append(
                {
                    **{field: "" for field in trace_fields},
                    "requirement_id": "REQ-KMFA-V015-S02-P3-SCOPE-GATE",
                    "model_id": "MOD-KMFA-V015-S02-P3-SCOPE-GATE-001",
                    "formula_id": "FORM-KMFA-V015-S02-P3-SCOPE-GATE-001",
                    "parameter_id": "PARAM-KMFA-P3-SYNTHETIC",
                }
            )
            with trace_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=trace_fields)
                writer.writeheader()
                writer.writerows(trace_rows)

            summary = summarize_legacy_governance(directory)
            self.assertEqual(summary["formula_count"], 322)
            self.assertEqual(summary["parameter_count"], 1460)
            self.assertEqual(summary["model_count"], 8)
            self.assertEqual(summary["traceability_row_count"], 501)
            self.assertEqual(
                summary["current_formula_count_including_s02_p2_governance"],
                before["current_formula_count_including_s02_p2_governance"] + 1,
            )
            self.assertEqual(
                summary["current_parameter_count_including_s02_p2_governance"],
                before["current_parameter_count_including_s02_p2_governance"] + 1,
            )
            self.assertEqual(
                summary["current_model_count_including_s02_p2_governance"],
                before["current_model_count_including_s02_p2_governance"] + 1,
            )
            self.assertEqual(
                summary["current_traceability_row_count_including_s02_p2_governance"],
                before["current_traceability_row_count_including_s02_p2_governance"] + 1,
            )


if __name__ == "__main__":
    unittest.main()
