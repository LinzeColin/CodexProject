from __future__ import annotations

import copy
import unittest
from collections import Counter
from pathlib import Path

from KMFA.tools.v015_s02_p2_requirement_trace import (
    SOURCE_EXPLICIT,
    STAGE_CLOSURE_DECISION,
    TRACE_COLUMNS,
    build_requirement_task_trace,
    validate_requirement_task_trace,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PACKAGE = (
    Path.home()
    / "Downloads"
    / "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
)
P1_MACHINE = (
    ROOT
    / "KMFA"
    / "stage_artifacts"
    / "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK"
    / "machine"
)


class TestV015S02P2RequirementTrace(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_requirement_task_trace(
            SOURCE_PACKAGE,
            P1_MACHINE / "requirements_ledger_public_safe.csv",
            P1_MACHINE / "business_line_matrix_public_safe.csv",
        )

    def mutated(self) -> list[dict[str, str]]:
        return copy.deepcopy(self.rows)

    def assert_error(self, rows: list[dict[str, str]], token: str) -> None:
        errors = validate_requirement_task_trace(rows)
        self.assertTrue(errors, "mutation must fail closed")
        self.assertTrue(
            any(token in error for error in errors),
            f"expected error token {token!r}; actual={errors}",
        )

    def test_baseline_has_exact_schema_counts_and_passes(self) -> None:
        self.assertEqual(134, len(self.rows))
        self.assertTrue(all(list(row) == TRACE_COLUMNS for row in self.rows))
        self.assertEqual(
            Counter({SOURCE_EXPLICIT: 132, STAGE_CLOSURE_DECISION: 2}),
            Counter(row["mapping_origin"] for row in self.rows),
        )
        self.assertEqual(55, len({row["requirement_id"] for row in self.rows}))
        self.assertEqual([], validate_requirement_task_trace(self.rows))

    def test_closure_bindings_are_exact(self) -> None:
        closure = {
            (row["requirement_id"], row["task_id"])
            for row in self.rows
            if row["mapping_origin"] == STAGE_CLOSURE_DECISION
        }
        self.assertEqual(
            {("R017", "S11P2T01"), ("R023", "S21P1T02")},
            closure,
        )

    def test_r051_routes_to_all_ten_business_lines(self) -> None:
        expected = ";".join(f"BL-{index:02d}" for index in range(1, 11))
        self.assertEqual(
            {expected},
            {
                row["business_line_refs"]
                for row in self.rows
                if row["requirement_id"] == "R051"
            },
        )

    def test_missing_p0_p1_requirement_task_fails(self) -> None:
        rows = [row for row in self.mutated() if row["requirement_id"] != "R001"]
        self.assert_error(rows, "requirement_coverage")

    def test_missing_stage_closure_fails(self) -> None:
        rows = [
            row
            for row in self.mutated()
            if not (
                row["requirement_id"] == "R017"
                and row["task_id"] == "S11P2T01"
            )
        ]
        self.assert_error(rows, "stage_closure")

    def test_forged_source_origin_fails(self) -> None:
        rows = self.mutated()
        row = next(item for item in rows if item["mapping_origin"] == SOURCE_EXPLICIT)
        row["mapping_origin"] = STAGE_CLOSURE_DECISION
        self.assert_error(rows, "mapping_origin")

    def test_r051_missing_business_line_fails(self) -> None:
        rows = self.mutated()
        for row in rows:
            if row["requirement_id"] == "R051":
                row["business_line_refs"] = row["business_line_refs"].replace(
                    ";BL-10", ""
                )
        self.assert_error(rows, "R051_business_lines")

    def test_nonexistent_task_fails(self) -> None:
        rows = self.mutated()
        rows[0]["task_id"] = "S99P1T01"
        rows[0]["stage_id"] = "S99"
        self.assert_error(rows, "unknown_task")

    def test_each_of_six_task_contract_fields_is_required(self) -> None:
        fields = (
            "task_name",
            "implementation_action",
            "implementation_output",
            "test_evidence_requirement",
            "acceptance_criterion",
            "stop_condition",
        )
        for field in fields:
            with self.subTest(field=field):
                rows = self.mutated()
                rows[0][field] = ""
                self.assert_error(rows, f"task_contract:{field}")

    def test_illegal_controlled_dimension_fails(self) -> None:
        rows = self.mutated()
        rows[0]["role_view_refs"] = "ADMIN"
        self.assert_error(rows, "illegal_dimension:role_view_refs")

    def test_not_applicable_dimension_requires_reason(self) -> None:
        rows = self.mutated()
        row = next(
            item
            for item in rows
            if "NOT_APPLICABLE" in item["role_view_refs"]
        )
        row["dimension_na_reason"] = ""
        self.assert_error(rows, "dimension_na_reason")

    def test_implementation_true_fails(self) -> None:
        rows = self.mutated()
        rows[0]["implementation_allowed_by_s02_p2"] = "true"
        self.assert_error(rows, "implementation_allowed_by_s02_p2")

    def test_r007_open_implementation_gap_is_preserved(self) -> None:
        rows = self.mutated()
        for row in rows:
            if row["requirement_id"] == "R007":
                row["resolution_target_stage"] = ""
        self.assert_error(rows, "R007_open_gap")

    def test_public_safe_token_regression_fails(self) -> None:
        rows = self.mutated()
        rows[0]["normative_requirement_public_safe"] = (
            str(Path("/") / "Users" / "example" / "Downloads" / "private.xlsx")
        )
        self.assert_error(rows, "public_safe")


if __name__ == "__main__":
    unittest.main()
