from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.video import (
    REAL_MP4_RENDER_MODEL_ID,
    generate_storyboard,
    render_lightweight_mp4,
    validate_mp4_render_report,
    validate_storyboard_against_narration,
    video_media_gate,
)


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

    def test_render_lightweight_mp4_records_real_artifact_with_fake_runner(self) -> None:
        daily_input = {
            "source_item": {
                "source_id": "arxiv:2607.00001",
                "title": "Agent systems for ROI learning",
                "metadata": {"arxiv": {"primary_category": "cs.AI"}},
            },
            "selection_audit": {"roi_total_score": 91.0},
            "queue_summary": {"queued_item_count": 3},
        }

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "adp-daily-video.mp4"

            def fake_runner(command: list[str]) -> dict:
                Path(command[-1]).write_bytes(b"\x00\x00\x00\x18ftypmp42fake-video")
                return {"returncode": 0}

            report = render_lightweight_mp4(
                daily_input,
                output_path=output,
                generated_at="2026-07-01T05:00:00+10:00",
                command_resolver=lambda command: "/usr/bin/ffmpeg" if command == "ffmpeg" else None,
                command_runner=fake_runner,
            )

            self.assertFalse(validate_mp4_render_report(report))
            self.assertEqual(report["model_id"], REAL_MP4_RENDER_MODEL_ID)
            self.assertEqual(report["status"], "rendered")
            self.assertTrue(report["mp4_rendered"])
            self.assertEqual(report["video_filename"], "adp-daily-video.mp4")
            self.assertFalse(report["video_attachment_allowed"])
            self.assertTrue(output.is_file())
            transcript = output.with_suffix(".txt").read_text(encoding="utf-8")
            self.assertIn("Read the email first", transcript)
            self.assertIn("optional cloud-generated file index", transcript)
            self.assertNotIn("ROI score", transcript)
            self.assertNotIn("91.0", transcript)
            self.assertNotIn("roi_total_score", transcript)

    def test_render_lightweight_mp4_blocks_without_ffmpeg(self) -> None:
        report = render_lightweight_mp4(
            {"source_item": {"source_id": "arxiv:2607.00001", "title": "Example"}},
            output_path="adp-daily-video.mp4",
            generated_at="2026-07-01T05:00:00+10:00",
            command_resolver=lambda command: None,
        )

        self.assertFalse(validate_mp4_render_report(report))
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["mp4_rendered"])
        self.assertIn("ffmpeg", " ".join(report["blocking_reasons"]))


if __name__ == "__main__":
    unittest.main()
