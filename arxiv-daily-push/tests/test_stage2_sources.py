from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from arxiv_daily_push.cli import main
from arxiv_daily_push.preprint_adapter import ingest_latest_preprints
from arxiv_daily_push.stage2_sources import (
    S2P1_PREPRINT_REPLAY_MODEL_ID,
    S2P1_PREPRINT_PROMOTION_MODEL_ID,
    build_s2p1_preprint_replay_shadow_evidence,
    build_s2p1_preprint_daily_input,
    build_s2p1_preprint_promotion_report,
    run_s2p1_preprint_shadow_daily,
    validate_s2p1_preprint_replay_shadow_report,
    validate_s2p1_shadow_report,
)


FIXTURES = Path(__file__).parent / "fixtures"
BIORXIV = FIXTURES / "biorxiv_details_sample.json"
MEDRXIV = FIXTURES / "medrxiv_details_sample.json"
GENERATED_AT = "2026-06-24T09:30:00+10:00"


def batches() -> dict:
    return {
        "biorxiv": ingest_latest_preprints(
            server="biorxiv",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: BIORXIV.read_text(encoding="utf-8"),
        ),
        "medrxiv": ingest_latest_preprints(
            server="medrxiv",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: MEDRXIV.read_text(encoding="utf-8"),
        ),
    }


def replay_batches(start: date, count: int = 30) -> dict:
    batches_by_date = {}
    for offset in range(count):
        as_of = start + timedelta(days=offset)
        batches_by_date[as_of.isoformat()] = {
            "biorxiv": ingest_latest_preprints(
                server="biorxiv",
                generated_at=GENERATED_AT,
                fetcher=lambda _query, day=as_of, index=offset: _fixture_with_unique_record(BIORXIV, day=day, index=index, server="biorxiv"),
            ),
            "medrxiv": ingest_latest_preprints(
                server="medrxiv",
                generated_at=GENERATED_AT,
                fetcher=lambda _query, day=as_of, index=offset: _fixture_with_unique_record(MEDRXIV, day=day, index=index, server="medrxiv"),
            ),
        }
    return batches_by_date


def _fixture_with_unique_record(path: Path, *, day: date, index: int, server: str) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    record = payload["collection"][0]
    doi_suffix = (660000 if server == "biorxiv" else 770000) + index
    record["doi"] = f"10.1101/{day.strftime('%Y.%m.%d')}.{doi_suffix}"
    record["date"] = day.isoformat()
    record["title"] = f"{server} replay candidate {index + 1:02d}: AI learning optimization risk automation for health markets"
    record["abstract"] = (
        "This method and framework evaluates artificial intelligence agents, language model decision systems, "
        "benchmark datasets, risk controls, automation efficiency, cost optimization, privacy, security, "
        "health economics, portfolio allocation, and market simulation. The study explains failure modes, "
        "statistical evaluation, operational tradeoffs, and deployable learning value for high ROI research triage."
    )
    record["category"] = "artificial intelligence; health economics; risk optimization"
    record["server"] = server
    return json.dumps(payload)


class Stage2SourceTests(unittest.TestCase):
    def test_s2p1_gate_blocks_until_replay_and_shadow_are_attached(self) -> None:
        report = build_s2p1_preprint_promotion_report(generated_at=GENERATED_AT, source_batches=batches())

        self.assertEqual(report["model_id"], S2P1_PREPRINT_PROMOTION_MODEL_ID)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["source_gate_ready"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertIn("30-day terminal replay", " ".join(report["blocking_reasons"]))
        self.assertIn("48h shadow", " ".join(report["blocking_reasons"]))

    def test_s2p1_gate_passes_with_replay_and_shadow_evidence_contracts(self) -> None:
        replay = {
            "status": "pass",
            "unique_date_count": 30,
            "future_leakage_count": 0,
            "duplicate_selected_count": 0,
            "p0_p1_blocker_count": 0,
        }
        shadow = {
            "status": "pass",
            "shadow_hours": 48,
            "formal_production_inclusion": False,
            "production_affected": False,
        }

        report = build_s2p1_preprint_promotion_report(
            generated_at=GENERATED_AT,
            source_batches=batches(),
            replay_report=replay,
            shadow_report=shadow,
        )

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["source_gate_ready"])
        self.assertTrue(report["replay_gate_ready"])
        self.assertTrue(report["shadow_gate_ready"])

    def test_preprint_daily_input_uses_preprint_metadata_for_claims_and_queue(self) -> None:
        report = build_s2p1_preprint_daily_input(
            date="2026-06-24",
            generated_at=GENERATED_AT,
            source_batches=batches(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["daily_input_ready"])
        self.assertEqual(report["daily_input"]["source_item"]["source_type"], "preprint")
        self.assertIn("bioRxiv/medRxiv", report["daily_input"]["claims"][0]["statement"])
        self.assertGreaterEqual(len(report["candidate_queue"]["items"]), 1)

    def test_shadow_daily_persists_queue_ledger_and_email_preview_without_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2p1_preprint_shadow_daily(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=batches(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2p1_shadow_report(report))
            self.assertFalse(report["formal_production_inclusion"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertTrue(Path(report["candidate_queue_path"]).is_file())
            self.assertTrue(Path(report["content_ledger_path"]).is_file())
            self.assertTrue(Path(report["email_preview_paths"]["plain"]).is_file())
            self.assertIn("【今天讲透一个问题】", Path(report["email_preview_paths"]["plain"]).read_text(encoding="utf-8"))

    def test_replay_shadow_evidence_passes_30_dates_and_persists_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_s2p1_preprint_replay_shadow_evidence(
                state_dir=tmp,
                generated_at=GENERATED_AT,
                start_date="2026-05-01",
                count=30,
                source_batches_by_date=replay_batches(date(2026, 5, 1)),
            )

            self.assertEqual(report["model_id"], S2P1_PREPRINT_REPLAY_MODEL_ID)
            self.assertEqual(report["status"], "pass")
            self.assertTrue(report["s2p1_source_promotion_accepted"])
            self.assertFalse(report["stage2_production_accepted"])
            self.assertFalse(validate_s2p1_preprint_replay_shadow_report(report))
            replay = report["replay_report"]
            self.assertEqual(replay["success_count"], 30)
            self.assertEqual(replay["unique_date_count"], 30)
            self.assertEqual(replay["duplicate_selected_count"], 0)
            self.assertEqual(replay["future_leakage_count"], 0)
            self.assertEqual(replay["p0_p1_blocker_count"], 0)
            self.assertEqual(replay["queue_continuity_break_count"], 0)
            self.assertGreaterEqual(report["shadow_report"]["shadow_hours"], 48)
            self.assertEqual(report["promotion_report"]["status"], "pass")
            for path in report["artifact_paths"].values():
                self.assertTrue(Path(path).exists(), path)
            ledger_lines = Path(report["artifact_paths"]["ledger"]).read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(ledger_lines), 30)

    def test_cli_stage2_preprint_replay_shadow_outputs_json(self) -> None:
        fake_report = {
            "model_id": S2P1_PREPRINT_REPLAY_MODEL_ID,
            "status": "pass",
            "formal_production_inclusion": False,
            "github_cloud_schedule_enabled": False,
            "real_smtp_sent": False,
            "replay_report": {"status": "pass"},
            "shadow_report": {"status": "pass"},
            "promotion_report": {"status": "pass"},
            "blocking_reasons": [],
        }
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("arxiv_daily_push.cli.build_s2p1_preprint_replay_shadow_evidence", return_value=fake_report):
                with redirect_stdout(buffer):
                    result = main([
                        "stage2-preprint-replay-shadow",
                        "--state-dir",
                        tmp,
                        "--generated-at",
                        GENERATED_AT,
                        "--count",
                        "30",
                        "--no-write",
                        "--json",
                    ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2P1_PREPRINT_REPLAY_MODEL_ID)


if __name__ == "__main__":
    unittest.main()
