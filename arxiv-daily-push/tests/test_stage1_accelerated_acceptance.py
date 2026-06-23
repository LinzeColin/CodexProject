from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.stage1_accelerated_acceptance import (
    STAGE1_ACCELERATED_ACCEPTANCE_ID,
    build_stage1_accelerated_acceptance_report,
    validate_stage1_accelerated_acceptance_report,
)
from arxiv_daily_push.trial import TRIAL_ACCEPTANCE_MODE_ACCELERATED


GENERATED_AT = "2026-06-23T10:00:00Z"


def candidate(index: int) -> dict:
    source_id = f"arxiv:2606.{index:05d}"
    return {
        "candidate_id": f"candidate:{source_id}",
        "source_id": source_id,
        "stable_id": f"2606.{index:05d}",
        "title": f"Real arXiv candidate {index}",
        "primary_category": "cs.AI" if index % 2 else "q-fin.PM",
        "categories": ["cs.AI", "q-fin.PM"],
        "roi_total_score": 90.0 - index / 100.0,
        "source_item": {
            "source_id": source_id,
            "stable_id": f"2606.{index:05d}",
            "title": f"Real arXiv candidate {index}",
            "retrieved_at": GENERATED_AT,
            "metadata": {
                "arxiv": {
                    "published": "2026-06-22T00:00:00Z",
                    "updated": "2026-06-22T00:00:00Z",
                    "primary_category": "cs.AI",
                    "categories": ["cs.AI", "q-fin.PM"],
                }
            },
        },
    }


def live_dry_run(candidate_count: int = 32) -> dict:
    return {
        "model_id": "adp-live-all-arxiv-dry-run-v1",
        "project_id": "arxiv-daily-push",
        "generated_at": GENERATED_AT,
        "status": "pass",
        "live_dry_run_ready": True,
        "archive_count": 20,
        "verified_archive_count": 20,
        "failed_archive_count": 0,
        "max_results_per_category": 3,
        "pdf_download_enabled": False,
        "bulk_harvest_enabled": False,
        "production_schedule_enabled": False,
        "smtp_send_enabled": False,
        "release_upload_enabled": False,
        "scan": {
            "status": "pass",
            "archive_count": 20,
            "blocked_archive_count": 0,
            "candidate_count": candidate_count,
            "candidates": [candidate(index) for index in range(1, candidate_count + 1)],
        },
        "artifact_paths": {"live_all_arxiv_dry_run": "artifact://live-all-arxiv"},
        "blocking_reasons": [],
    }


def smtp_manifest() -> dict:
    return {
        "manifest_id": "ADP-S1P5T04-CONTROLLED-SMTP-EVIDENCE-20260623",
        "real_smtp_sent": True,
        "controlled_smtp_delivery_count": 2,
        "controlled_smtp_delivery_refs": [
            {
                "run_id": "28002478689",
                "artifact_id": "7811543123",
                "notification_status": "sent",
                "production_evidence_ready": True,
            },
            {
                "run_id": "28002478689",
                "artifact_id": "7816791617",
                "notification_status": "sent",
                "production_evidence_ready": True,
            },
        ],
    }


class Stage1AcceleratedAcceptanceTests(unittest.TestCase):
    def test_builds_accelerated_acceptance_from_real_arxiv_candidates_without_schedule_side_effects(self) -> None:
        report = build_stage1_accelerated_acceptance_report(
            live_dry_run(),
            smtp_manifest(),
            generated_at=GENERATED_AT,
            live_dry_run_ref="github-actions://run/artifact",
            controlled_smtp_ref="governance/run_manifests/smtp.json",
        )

        self.assertFalse(validate_stage1_accelerated_acceptance_report(report))
        self.assertEqual(report["acceptance_id"], STAGE1_ACCELERATED_ACCEPTANCE_ID)
        self.assertEqual(report["arxiv_production_acceptance_label"], "ARXIV_PRODUCTION_ACCEPTED")
        self.assertTrue(report["accepted_for_production"])
        self.assertFalse(report["production_schedule_enabled"])
        self.assertFalse(report["new_real_smtp_sent"])
        self.assertEqual(report["selected_sample_count"], 30)
        self.assertEqual(report["trial_report"]["acceptance_mode"], TRIAL_ACCEPTANCE_MODE_ACCELERATED)
        self.assertEqual(report["trial_report"]["daily_summary"]["coverage_count"], 30)

    def test_blocks_when_live_candidates_are_below_required_samples(self) -> None:
        report = build_stage1_accelerated_acceptance_report(
            live_dry_run(candidate_count=16),
            smtp_manifest(),
            generated_at=GENERATED_AT,
            expected_samples=30,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["accepted_for_production"])
        self.assertIn("real arXiv candidate count 16 is below required 30", report["blocking_reasons"])
        self.assertFalse(validate_stage1_accelerated_acceptance_report(report))

    def test_cli_writes_accelerated_acceptance_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            live_path = root / "live.json"
            smtp_path = root / "smtp.json"
            artifact_dir = root / "artifacts"
            live_path.write_text(json.dumps(live_dry_run(), ensure_ascii=False), encoding="utf-8")
            smtp_path.write_text(json.dumps(smtp_manifest(), ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "build-stage1-accelerated-acceptance",
                        "--live-dry-run",
                        str(live_path),
                        "--controlled-smtp-manifest",
                        str(smtp_path),
                        "--generated-at",
                        GENERATED_AT,
                        "--artifact-dir",
                        str(artifact_dir),
                        "--json",
                    ]
                )

            payload = json.loads(buffer.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(payload["status"], "pass")
            self.assertTrue(Path(payload["artifact_paths"]["accelerated_acceptance"]).is_file())
            self.assertTrue(Path(payload["artifact_paths"]["trial_input"]).is_file())
            self.assertTrue(Path(payload["artifact_paths"]["trial_report"]).is_file())


if __name__ == "__main__":
    unittest.main()
