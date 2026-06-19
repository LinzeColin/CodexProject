from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_goal_completion.py"


def load_goal_module():
    spec = importlib.util.spec_from_file_location("audit_goal_completion", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load audit_goal_completion.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_goal_completion"] = module
    spec.loader.exec_module(module)
    return module


class GoalCompletionAuditTests(unittest.TestCase):
    def build_fixture(self, tmp: str) -> tuple[object, Path, Path, Path, Path]:
        audit = load_goal_module()
        output = Path(tmp) / "out"
        reports = output / "reports"
        audit_dir = output / "audit"
        data_dir = output / "data"
        review_dir = output / "review"
        reports.mkdir(parents=True)
        audit_dir.mkdir()
        data_dir.mkdir()
        review_dir.mkdir()
        for name in [
            "weekly_report.pdf",
            "monthly_report.pdf",
            "quarterly_report.pdf",
            "half_year_report.pdf",
            "yearly_report.pdf",
            "annual_bill_cycle_report.pdf",
            "reference_model_benchmark_report.pdf",
            "visual_quality_acceptance_report.pdf",
            "manual_review_report.pdf",
        ]:
            (reports / name).write_bytes(b"%PDF-" + b"x" * 25_000)
        for name in [
            "index.html",
            "operations_center.html",
            "acceptance_workbench.html",
            "reference_model_lab.html",
            "dashboard.html",
            "behavior_analysis.html",
            "transaction_explorer.html",
            "tag_library.html",
            "review_workbench.html",
        ]:
            (reports / name).write_text("<html>" + ("x" * 6_000) + "</html>", encoding="utf-8")
        for name in ["reference_models.json", "reference_source_log.json", "reference_source_log.csv"]:
            (audit_dir / name).write_text("[]", encoding="utf-8")
        (audit_dir / "chatgpt_reference_audit.json").write_text(
            json.dumps(
                {
                    "status": "missing",
                    "candidate_count": 0,
                    "gap_summary": {"blocked_missing_chatgpt_source": 10},
                }
            ),
            encoding="utf-8",
        )
        (audit_dir / "browser_visual_acceptance.json").write_text(
            json.dumps({"checked_count": 18, "failure_count": 0, "generated_at": "2026-06-05T10:00:00+1000"}),
            encoding="utf-8",
        )
        ledger = Path(tmp) / "ledger.sqlite"
        ledger.write_bytes(b"x" * 200_000)
        (data_dir / "consumption.sqlite").write_bytes(b"x" * 200_000)
        (review_dir / "manual_review_queue.csv").write_text("id\n1\n", encoding="utf-8")
        return audit, output, ledger, audit_dir, reports

    def run_fixture(self, audit: object, output: Path, ledger: Path) -> dict[str, object]:
        return audit.run_audit(Namespace(output_dir=str(output), ledger_db=str(ledger), json=False))

    def user_acceptance_row(self, audit_dir: Path) -> dict[str, str]:
        payload = json.loads((audit_dir / "goal_completion_audit.json").read_text(encoding="utf-8"))
        return next(row for row in payload["rows"] if row["requirement_id"] == "user_expectation_acceptance")

    def goal_row(self, audit_dir: Path, requirement_id: str) -> dict[str, str]:
        payload = json.loads((audit_dir / "goal_completion_audit.json").read_text(encoding="utf-8"))
        return next(row for row in payload["rows"] if row["requirement_id"] == requirement_id)

    def write_acceptance(self, audit_dir: Path, choices: list[dict[str, str]]) -> None:
        (audit_dir / "user_acceptance_decisions.json").write_text(
            json.dumps({"generated_at": "2026-06-05T10:00:00+1000", "choices": choices}, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_audit_marks_missing_user_inputs_without_completing_goal(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
            audit, output, ledger, audit_dir, reports = self.build_fixture(tmp)

            result = self.run_fixture(audit, output, ledger)

            payload = json.loads((audit_dir / "goal_completion_audit.json").read_text(encoding="utf-8"))
            row = self.user_acceptance_row(audit_dir)
            self.assertFalse(result["goal_complete"])
            self.assertEqual(row["status"], "needs_user_input")
            self.assertIn("no exported user acceptance decision file", row["detail"])
            self.assertGreaterEqual(payload["summary"]["counts"].get("needs_user_input", 0), 1)
            self.assertTrue((reports / "goal_completion_audit_report.pdf").exists())

    def test_user_acceptance_is_met_only_when_all_choices_are_a_and_final_acceptance_is_a(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
            audit, output, ledger, audit_dir, _reports = self.build_fixture(tmp)
            self.write_acceptance(
                audit_dir,
                [
                    {"id": "taxonomy", "choice": "A"},
                    {"id": "reports", "choice": "A"},
                    {"id": "final_acceptance", "choice": "A"},
                ],
            )

            result = self.run_fixture(audit, output, ledger)
            row = self.user_acceptance_row(audit_dir)

            self.assertFalse(result["goal_complete"])
            self.assertEqual(row["status"], "met")
            self.assertIn("strict_acceptance=true", row["detail"])
            self.assertIn("final_acceptance=A", row["detail"])

    def test_user_acceptance_stays_open_when_any_choice_is_b_or_c(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
            audit, output, ledger, audit_dir, _reports = self.build_fixture(tmp)
            self.write_acceptance(
                audit_dir,
                [
                    {"id": "taxonomy", "choice": "A"},
                    {"id": "chatgpt_reference", "choice": "B"},
                    {"id": "final_acceptance", "choice": "A"},
                ],
            )

            self.run_fixture(audit, output, ledger)
            row = self.user_acceptance_row(audit_dir)

            self.assertEqual(row["status"], "needs_user_input")
            self.assertIn("strict_acceptance=false", row["detail"])
            self.assertIn("chatgpt_reference=B", row["detail"])

    def test_user_acceptance_stays_open_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
            audit, output, ledger, audit_dir, _reports = self.build_fixture(tmp)
            (audit_dir / "user_acceptance_decisions.json").write_text("{not-json", encoding="utf-8")

            self.run_fixture(audit, output, ledger)
            row = self.user_acceptance_row(audit_dir)

            self.assertEqual(row["status"], "needs_user_input")
            self.assertIn("invalid JSON", row["detail"])

    def test_chatgpt_reference_a_accepts_current_reference_boundary_without_completing_final_goal(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
            audit, output, ledger, audit_dir, _reports = self.build_fixture(tmp)
            self.write_acceptance(
                audit_dir,
                [
                    {"id": "taxonomy", "choice": "A"},
                    {"id": "risk_tags", "choice": "A"},
                    {"id": "reports", "choice": "A"},
                    {"id": "dashboard", "choice": "A"},
                    {"id": "large_review", "choice": "A"},
                    {"id": "tags", "choice": "A"},
                    {"id": "downstream", "choice": "A"},
                    {"id": "chatgpt_reference", "choice": "A"},
                    {"id": "final_acceptance", "choice": "B"},
                ],
            )

            result = self.run_fixture(audit, output, ledger)
            chatgpt_row = self.goal_row(audit_dir, "chatgpt_reference_comparison")
            user_row = self.user_acceptance_row(audit_dir)

            self.assertFalse(result["goal_complete"])
            self.assertEqual(chatgpt_row["status"], "met")
            self.assertIn("chatgpt_reference=A", chatgpt_row["detail"])
            self.assertEqual(user_row["status"], "needs_user_input")
            self.assertIn("final_acceptance=B", user_row["detail"])


if __name__ == "__main__":
    unittest.main()
