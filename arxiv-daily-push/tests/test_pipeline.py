from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.pipeline import PipelineError, run_daily_dry_run
from arxiv_daily_push.state_machine import validate_run_record


FIXTURE = Path(__file__).parent / "fixtures" / "pipeline_input.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class PipelineTests(unittest.TestCase):
    def test_daily_dry_run_completes_run_record(self) -> None:
        data = load_fixture()
        payload = run_daily_dry_run(
            data["source_item"],
            data["claims"],
            run_id=data["run_id"],
            publication_id=data["publication_id"],
            date=data["date"],
            generated_at=data["generated_at"],
        )

        self.assertEqual(payload["status"], "succeeded")
        self.assertEqual(payload["run_record"]["current_state"], "completed")
        self.assertEqual(payload["run_record"]["status"], "succeeded")
        self.assertFalse(validate_run_record(payload["run_record"]))

    def test_daily_dry_run_blocks_failed_evidence_gate(self) -> None:
        data = load_fixture()
        data["claims"][0]["support_status"] = "unsupported"

        with self.assertRaises(PipelineError):
            run_daily_dry_run(
                data["source_item"],
                data["claims"],
                run_id=data["run_id"],
                publication_id=data["publication_id"],
                date=data["date"],
                generated_at=data["generated_at"],
            )

    def test_daily_dry_run_keeps_notification_as_preview(self) -> None:
        data = load_fixture()
        payload = run_daily_dry_run(
            data["source_item"],
            data["claims"],
            run_id=data["run_id"],
            publication_id=data["publication_id"],
            date=data["date"],
            generated_at=data["generated_at"],
        )

        self.assertIn("linzezhang35@gmail.com", payload["email_preview"]["recipient"])
        self.assertIn("daily dry-run pipeline completed", payload["email_preview"]["subject"])
        self.assertNotIn("smtp", json.dumps(payload["email_preview"], ensure_ascii=False).lower())

    def test_cli_runs_daily_dry_run_fixture(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["run-daily-dry-run", "--path", str(FIXTURE), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "succeeded")
        self.assertEqual(payload["run_record"]["current_state"], "completed")


if __name__ == "__main__":
    unittest.main()
