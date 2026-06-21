from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from arxiv_daily_push.handoff import HandoffError, build_handoff, validate_handoff
from arxiv_daily_push.pipeline import run_daily_dry_run


FIXTURE = Path(__file__).parent / "fixtures" / "pipeline_input.json"


def pipeline_payload() -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return run_daily_dry_run(
        data["source_item"],
        data["claims"],
        run_id=data["run_id"],
        publication_id=data["publication_id"],
        date=data["date"],
        generated_at=data["generated_at"],
    )


class HandoffTests(unittest.TestCase):
    def test_build_handoff_keeps_external_side_effects_disabled(self) -> None:
        handoff = build_handoff(pipeline_payload(), generated_at="2026-06-21T05:45:00+10:00")

        self.assertFalse(handoff["runner_gate"]["scheduler_enabled"])
        self.assertFalse(handoff["release_gate"]["release_upload_allowed"])
        self.assertFalse(handoff["email_transport_gate"]["real_smtp_send_enabled"])
        self.assertFalse(validate_handoff(handoff))

    def test_handoff_requires_completed_run_record(self) -> None:
        payload = pipeline_payload()
        payload["run_record"]["current_state"] = "publication_ready"

        with self.assertRaises(HandoffError):
            build_handoff(payload, generated_at="2026-06-21T05:45:00+10:00")

    def test_handoff_validation_rejects_enabled_scheduler(self) -> None:
        handoff = build_handoff(pipeline_payload(), generated_at="2026-06-21T05:45:00+10:00")
        handoff["runner_gate"]["scheduler_enabled"] = True

        self.assertIn("scheduler_enabled must be false", " ".join(validate_handoff(handoff)))

    def test_cli_builds_handoff_from_pipeline_payload(self) -> None:
        from arxiv_daily_push.cli import main
        import io
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pipeline.json"
            path.write_text(json.dumps(pipeline_payload(), ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["build-handoff", "--path", str(path), "--generated-at", "2026-06-21T05:45:00+10:00", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertFalse(payload["release_gate"]["release_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
