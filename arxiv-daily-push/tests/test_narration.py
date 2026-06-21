from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.config import runtime_parameters
from arxiv_daily_push.narration import NarrationError, generate_narration_plan, validate_narration_plan


FIXTURE = Path(__file__).parent / "fixtures" / "narration_input.json"


def load_lesson() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["lesson"]


class NarrationTests(unittest.TestCase):
    def test_generate_narration_plan_is_dry_run_only(self) -> None:
        lesson = load_lesson()

        narration = generate_narration_plan(lesson, generated_at="2026-06-21T05:30:00+10:00", path=Path("."))

        self.assertEqual(narration["tts_mode"], "dry_run")
        self.assertFalse(narration["audio_synthesis_allowed"])
        self.assertFalse(narration["resource_gate"]["audio_write_allowed"])
        self.assertFalse(narration["resource_gate"]["model_download_allowed"])
        self.assertTrue(narration["resource_gate"]["dry_run_ready"])
        self.assertEqual(len(narration["segments"]), len(lesson["sections"]))
        self.assertFalse(validate_narration_plan(narration, lesson))

    def test_real_tts_mode_is_blocked(self) -> None:
        with self.assertRaises(NarrationError):
            generate_narration_plan(load_lesson(), generated_at="2026-06-21T05:30:00+10:00", tts_mode="real")

    def test_dry_run_rejects_audio_paths(self) -> None:
        lesson = load_lesson()
        narration = generate_narration_plan(lesson, generated_at="2026-06-21T05:30:00+10:00")
        narration["segments"][0]["audio_path"] = "media/audio/seg-01.wav"

        errors = validate_narration_plan(narration, lesson)

        self.assertIn("audio_path is forbidden", " ".join(errors))

    def test_runtime_parameters_expose_tts_dry_run_policy(self) -> None:
        params = runtime_parameters()

        self.assertEqual(params["tts_required_commands"], ["ffmpeg"])
        self.assertFalse(params["real_tts_synthesis_enabled"])

    def test_cli_generates_narration_fixture(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "generate-narration",
                    "--path",
                    str(FIXTURE),
                    "--generated-at",
                    "2026-06-21T05:30:00+10:00",
                    "--json",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["tts_mode"], "dry_run")
        self.assertFalse(payload["audio_synthesis_allowed"])
        self.assertIn("resource_gate", payload)


if __name__ == "__main__":
    unittest.main()
