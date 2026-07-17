from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s09_p3_human_readable_audit as builder
from KMFA.tools import v015_s09_p3_human_readable_audit as kernel


class HumanReadableAuditGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.final = self.manifest["phase_acceptance_status"] == "PASSED"

    def test_primary_governance_surfaces_point_to_s09_p3(self) -> None:
        acceptance = "PASSED" if self.final else "PENDING_FINAL_VALIDATION"
        decision = "CONTINUE_TO_S09_STAGE_REVIEW_ONLY" if self.final else "REMAIN_IN_S09_P3_FINAL_VALIDATION"
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                kernel.RUN_PHASE_ID,
                kernel.TASK_ID,
                kernel.ACCEPTANCE_ID,
                f'phase_acceptance_status: "{acceptance}"',
                'stage_lifecycle_status: "IN_PROGRESS"',
                'stage_acceptance_status: "PENDING"',
                "stage_execution_percentage: 100",
                f'decision: "{decision}"',
                "s09_p3_started: true",
                f's09_p3_acceptance_status: "{acceptance}"',
                f"s09_stage_review_entry_allowed: {str(self.final).lower()}",
                "s09_stage_review_started: false",
                "active_formula_count: 351",
                "active_parameter_count: 1689",
                'current_parameter_range: "PARAM-KMFA-2065..2074"',
            ):
                self.assertIn(token, text, relative)

    def test_model_formula_and_parameter_registries_are_registered(self) -> None:
        model = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        model_doc = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        params = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("kmfa_v015_s09_p3_human_readable_audit", model)
        self.assertIn("kmfa_v015_s09_p3_human_readable_audit", model_doc)
        self.assertIn("FORM-KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT-001", formula)
        self.assertIn("PARAM-KMFA-2065", params)
        self.assertIn("PARAM-KMFA-2074", params)

    def test_parameter_rows_are_exact_and_active(self) -> None:
        path = builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row["parameter_id"].startswith("PARAM-KMFA-20") and 2065 <= int(row["parameter_id"].rsplit("-", 1)[1]) <= 2074]
        self.assertEqual(len(selected), 10)
        self.assertEqual({row["status"] for row in selected}, {"active"})
        self.assertEqual({row["formula_id"] for row in selected}, {"FORM-KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT-001"})

    def test_traceability_binds_requirement_to_code_tests_and_evidence(self) -> None:
        text = (builder.PROJECT_ROOT / "docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        row = next(line for line in text.splitlines() if line.startswith("REQ-KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT,"))
        for token in (
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            "v015_s09_p3_human_readable_audit.py",
            "test_v015_s09_p3_human_readable_audit.py",
            "V015_S09_P3_HUMAN_READABLE_AUDIT",
        ):
            self.assertIn(token, row)

    def test_feature_development_and_parameter_docs_are_human_readable(self) -> None:
        feature = (builder.PROJECT_ROOT / "功能清单.md").read_text(encoding="utf-8")
        development = (builder.PROJECT_ROOT / "开发记录.md").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        for token in ("FEAT-KMFA-284", "FEAT-KMFA-285", "FEAT-KMFA-286", "S09-P3"):
            self.assertIn(token, feature)
        self.assertIn("v1.5 S09-P3", development)
        self.assertIn("人类可读与审计", parameters)
        self.assertIn("PARAM-KMFA-2065..2074", parameters)

    def test_execution_and_final_events_match_phase_state(self) -> None:
        text = (builder.PROJECT_ROOT / "docs/governance/events.jsonl").read_text(encoding="utf-8")
        self.assertIn("V015-S09-P3-HUMAN-READABLE-AUDIT-EXECUTION", text)
        if self.final:
            self.assertIn("V015-S09-P3-HUMAN-READABLE-AUDIT-FINAL", text)
        else:
            self.assertNotIn("V015-S09-P3-HUMAN-READABLE-AUDIT-FINAL", text)


if __name__ == "__main__":
    unittest.main()
