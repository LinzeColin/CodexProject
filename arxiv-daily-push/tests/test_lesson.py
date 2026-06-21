from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.evidence_gate import build_claim_ledger
from arxiv_daily_push.lesson import LessonGenerationError, generate_lesson, validate_lesson_against_ledger


FIXTURE = Path(__file__).parent / "fixtures" / "lesson_input.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class LessonGenerationTests(unittest.TestCase):
    def test_generate_lesson_uses_supported_claim_ids(self) -> None:
        data = load_fixture()

        lesson = generate_lesson(data["source_item"], data["claims"], generated_at=data["generated_at"])
        ledger = build_claim_ledger(data["source_item"], data["claims"], extracted_at=data["generated_at"])

        self.assertEqual(lesson["language"], "zh-CN")
        self.assertTrue(lesson["lesson_id"].startswith("lesson:arxiv:2401.00001:"))
        self.assertFalse(validate_lesson_against_ledger(lesson, ledger))
        for section in lesson["sections"]:
            for claim_id in section["claim_ids"]:
                self.assertIn(claim_id, lesson["claim_ids"])
                self.assertIn(f"[{claim_id}]", section["body"])

    def test_unverified_non_p0_claim_is_excluded_from_lesson(self) -> None:
        data = load_fixture()

        lesson = generate_lesson(data["source_item"], data["claims"], generated_at=data["generated_at"])
        ledger = build_claim_ledger(data["source_item"], data["claims"], extracted_at=data["generated_at"])
        unverified_claim_ids = {
            claim["claim_id"] for claim in ledger["claims"] if claim["support_status"] != "supported"
        }

        self.assertTrue(unverified_claim_ids)
        self.assertFalse(unverified_claim_ids.intersection(lesson["claim_ids"]))
        self.assertNotIn("practical deployment status", json.dumps(lesson, ensure_ascii=False))

    def test_blocked_ledger_prevents_lesson_generation(self) -> None:
        data = load_fixture()
        data["claims"][0]["support_status"] = "unsupported"

        with self.assertRaises(LessonGenerationError):
            generate_lesson(data["source_item"], data["claims"], generated_at=data["generated_at"])

    def test_lesson_validation_rejects_unknown_section_claim(self) -> None:
        data = load_fixture()
        lesson = generate_lesson(data["source_item"], data["claims"], generated_at=data["generated_at"])
        ledger = build_claim_ledger(data["source_item"], data["claims"], extracted_at=data["generated_at"])
        lesson["sections"][0]["claim_ids"].append("claim:missing")

        errors = validate_lesson_against_ledger(lesson, ledger)

        self.assertIn("claims absent from Lesson.claim_ids", " ".join(errors))

    def test_cli_generates_lesson_fixture(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["generate-lesson", "--path", str(FIXTURE), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["language"], "zh-CN")
        self.assertEqual(len(payload["sections"]), 3)
        self.assertIn("Claim Ledger", json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
