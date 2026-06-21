from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.video import generate_storyboard, validate_storyboard_against_narration, video_media_gate


FIXTURE = Path(__file__).parent / "fixtures" / "video_input.json"


def load_narration() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["narration"]


class VideoStoryboardTests(unittest.TestCase):
    def test_generate_storyboard_is_dry_run_only(self) -> None:
        narration = load_narration()

        storyboard = generate_storyboard(narration, generated_at="2026-06-21T05:35:00+10:00", path=Path("."))

        self.assertTrue(storyboard["constraints"]["dry_run_only"])
        self.assertFalse(storyboard["constraints"]["video_render_allowed"])
        self.assertFalse(storyboard["constraints"]["media_write_allowed"])
        self.assertFalse(storyboard["constraints"]["asset_download_allowed"])
        self.assertEqual(len(storyboard["scenes"]), len(narration["segments"]))
        self.assertFalse(validate_storyboard_against_narration(storyboard, narration))

    def test_media_gate_blocks_real_render_outputs(self) -> None:
        gate = video_media_gate(Path("."))

        self.assertTrue(gate["dry_run_ready"])
        self.assertFalse(gate["video_render_allowed"])
        self.assertFalse(gate["media_write_allowed"])
        self.assertFalse(gate["asset_download_allowed"])
        self.assertIn("real video rendering disabled", " ".join(gate["blocking_reasons"]))

    def test_storyboard_rejects_media_paths(self) -> None:
        narration = load_narration()
        storyboard = generate_storyboard(narration, generated_at="2026-06-21T05:35:00+10:00")
        storyboard["scenes"][0]["media_path"] = "media/video/scene-01.mp4"

        errors = validate_storyboard_against_narration(storyboard, narration)

        self.assertIn("media paths are forbidden", " ".join(errors))

    def test_storyboard_rejects_non_lesson_claims(self) -> None:
        narration = load_narration()
        storyboard = generate_storyboard(narration, generated_at="2026-06-21T05:35:00+10:00")
        storyboard["scenes"][0]["claim_ids"].append("claim:not-in-narration")

        errors = validate_storyboard_against_narration(storyboard, narration)

        self.assertIn("subset of Narration.claim_ids", " ".join(errors))

    def test_cli_generates_storyboard_fixture(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "generate-storyboard",
                    "--path",
                    str(FIXTURE),
                    "--generated-at",
                    "2026-06-21T05:35:00+10:00",
                    "--json",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertFalse(payload["constraints"]["video_render_allowed"])
        self.assertEqual(len(payload["scenes"]), 2)


if __name__ == "__main__":
    unittest.main()
