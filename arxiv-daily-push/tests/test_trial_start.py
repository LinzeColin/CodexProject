from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.production_preflight import PRODUCTION_PREFLIGHT_VALIDATOR_ID
from arxiv_daily_push.production_scheduler import build_production_scheduler_plan
from arxiv_daily_push.release_delivery import RELEASE_DELIVERY_MODEL_ID
from arxiv_daily_push.smtp_delivery import SMTP_DELIVERY_MODEL_ID
from arxiv_daily_push.source_ingest import SOURCE_INGEST_MODEL_ID
from arxiv_daily_push.trial_bootstrap import build_trial_bootstrap_plan
from arxiv_daily_push.trial_start import (
    TRIAL_START_MODEL_ID,
    build_trial_start_gate,
    validate_trial_start_report,
)


ROOT = Path(__file__).resolve().parents[2]


def preflight_report(*, passed: bool = True) -> dict:
    gates = [
        {"gate_id": gate_id, "passed": passed, "blocking_reasons": [] if passed else [f"{gate_id} blocked"]}
        for gate_id in (
            "required_commands",
            "secret_environment",
            "disk_pressure",
            "memory_pressure",
            "git_artifact_hygiene",
            "local_artifact_cache",
        )
    ]
    return {
        "preflight_id": "production-preflight:arxiv-daily-push",
        "validator_id": PRODUCTION_PREFLIGHT_VALIDATOR_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": "2026-07-01T04:45:00+10:00",
        "timezone": "Australia/Sydney",
        "recipient": "linzezhang35@gmail.com",
        "status": "pass" if passed else "blocked",
        "production_run_allowed": passed,
        "gates": gates,
        "blocking_reasons": [] if passed else ["preflight blocked"],
        "secret_policy": {
            "secret_values_logged": False,
            "secret_names_only": True,
            "codex_auth_read": False,
        },
        "resource_evidence": {
            "resource_pressure_ok": passed,
            "resource_pressure_ok_ref": "production-preflight://arxiv-daily-push/2026-07-01" if passed else "",
        },
    }


def source_batch(*, passed: bool = True) -> dict:
    item = {
        "source_id": "arxiv:2401.00001",
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": "2401.00001",
        "title": "Example",
        "retrieved_at": "2026-07-01T05:00:00+10:00",
        "canonical_url": "https://arxiv.org/abs/2401.00001",
        "metadata": {"arxiv": {}},
        "content_refs": [{"ref_id": "abstract", "ref_type": "html", "uri": "https://arxiv.org/abs/2401.00001"}],
        "license": {"status": "unknown", "usage": "private_learning_link_only"},
    }
    return {
        "ingest_id": "source-ingest:arxiv-latest",
        "model_id": SOURCE_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": "arxiv.atom.v1",
        "generated_at": "2026-07-01T05:00:00+10:00",
        "status": "pass" if passed else "blocked",
        "request": {"url": "https://export.arxiv.org/api/query", "search_query": "cat:cs.AI"},
        "source_policy": {
            "network_fetch_enabled": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "max_results_per_call": 25,
            "polite_min_interval_seconds": 3,
        },
        "seen_source_ids": [],
        "duplicate_source_ids": [],
        "source_items": [item] if passed else [],
        "new_items": [item] if passed else [],
        "new_item_count": 1 if passed else 0,
        "blocking_reasons": [] if passed else ["no unseen arXiv SourceItems returned for the configured query"],
    }


def smtp_report(*, sent: bool = True) -> dict:
    return {
        "delivery_id": "smtp-delivery:trial-start-probe",
        "validator_id": SMTP_DELIVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "project_name": "arXiv Daily Push",
        "generated_at": "2026-07-01T05:05:00+10:00",
        "recipient": "linzezhang35@gmail.com",
        "expected_recipient": "linzezhang35@gmail.com",
        "subject": "[arXiv Daily Push][SUCCESS][2026-07-01] probe",
        "status": "sent" if sent else "dry_run",
        "dry_run": not sent,
        "real_smtp_send_enabled": sent,
        "required_env_keys": ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
        "smtp_config": {
            "host_configured": sent,
            "port_configured": sent,
            "username_configured": sent,
            "password_configured": sent,
            "port_valid": True,
            "require_tls": True,
            "timeout_seconds": 30,
            "secret_values_logged": False,
        },
        "message": {
            "body_sha256": "0" * 64,
            "body_logged": False,
            "message_id": "smtp-delivery:trial-start-probe",
        },
        "delivery_ref": "smtp://message/trial-start-probe" if sent else "",
        "blocking_reasons": [],
    }


def release_report(*, created: bool = True) -> dict:
    return {
        "delivery_id": "release-delivery:trial-start-probe",
        "validator_id": RELEASE_DELIVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": "2026-07-01T05:06:00+10:00",
        "repo": "LinzeColin/CodexProject",
        "tag": "adp-trial-start-probe-20260701",
        "target": "abc123",
        "title": "arXiv Daily Push trial start probe",
        "status": "created" if created else "dry_run",
        "dry_run": not created,
        "release_upload_enabled": created,
        "draft": True,
        "private_channel_expected": True,
        "notes": {"notes_sha256": "1" * 64, "notes_logged": False},
        "asset_policy": {
            "max_asset_mib": 20,
            "forbidden_names": [".env"],
            "forbidden_suffixes": [".key"],
            "clobber_enabled": False,
            "secret_values_logged": False,
        },
        "assets": [{"path": "trial-start.json", "name": "trial-start.json", "size_bytes": 42, "sha256": "2" * 64}],
        "command": {
            "gh_required": True,
            "gh_available": True,
            "command_preview": "gh release create adp-trial-start-probe-20260701 ...",
            "stdout_logged": False,
            "stderr_logged": False,
        },
        "release_ref": "github-release://LinzeColin/CodexProject/adp-trial-start-probe-20260701" if created else "",
        "blocking_reasons": [],
    }


def refs() -> dict[str, str]:
    return {
        "default_branch_ref": "git://LinzeColin/CodexProject/main@abc123",
        "runner_ref": "github-runner://arxiv-daily-push/private-runner-01",
        "preflight_ref": "github-actions://adp/run-1/adp-production-preflight",
        "source_ingest_ref": "github-actions://adp/run-1/adp-scheduled-source-batch",
        "smtp_ref": "smtp://message/trial-start-probe",
        "release_ref": "github-release://LinzeColin/CodexProject/adp-trial-start-probe-20260701",
        "scheduler_ref": "github-actions://adp/arxiv-daily-push-scheduled/main",
        "trial_state_ref": "github-actions://adp/run-1/adp-trial-evidence-ledger-initial",
        "trial_start_ref": "github-actions://adp/run-1/adp-trial-start-gate",
    }


def gate_kwargs(**overrides) -> dict:
    kwargs = {
        "generated_at": "2026-07-01T05:10:00+10:00",
        "preflight_report": preflight_report(),
        "bootstrap_plan": build_trial_bootstrap_plan(ROOT, generated_at="2026-07-01T04:40:00+10:00"),
        "scheduler_plan": build_production_scheduler_plan(ROOT, generated_at="2026-07-01T04:41:00+10:00"),
        "source_batch": source_batch(),
        "smtp_delivery_report": smtp_report(),
        "release_delivery_report": release_report(),
        "confirm_start": True,
    }
    kwargs.update(refs())
    kwargs.update(overrides)
    return kwargs


class TrialStartTests(unittest.TestCase):
    def test_build_trial_start_gate_passes_with_all_durable_evidence(self) -> None:
        report = build_trial_start_gate(**gate_kwargs())

        self.assertEqual(report["model_id"], TRIAL_START_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["trial_start_ready"])
        self.assertFalse(report["side_effects_performed"])
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(validate_trial_start_report(report))

    def test_build_trial_start_gate_blocks_without_confirmation(self) -> None:
        report = build_trial_start_gate(**gate_kwargs(confirm_start=False))

        self.assertEqual(report["status"], "blocked")
        self.assertIn("confirm_start must be true", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_start_report(report))

    def test_build_trial_start_gate_blocks_missing_durable_refs(self) -> None:
        report = build_trial_start_gate(**gate_kwargs(runner_ref="runner-01"))

        self.assertEqual(report["status"], "blocked")
        self.assertIn("runner_ref must be a durable ref", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_start_report(report))

    def test_build_trial_start_gate_blocks_dry_run_smtp_probe(self) -> None:
        report = build_trial_start_gate(
            **gate_kwargs(
                smtp_delivery_report=smtp_report(sent=False),
                smtp_ref="smtp://message/trial-start-probe",
            )
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("real sent", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_start_report(report))

    def test_build_trial_start_gate_blocks_failed_preflight(self) -> None:
        report = build_trial_start_gate(**gate_kwargs(preflight_report=preflight_report(passed=False)))

        self.assertEqual(report["status"], "blocked")
        self.assertIn("production preflight must pass", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_start_report(report))

    def test_cli_plan_trial_start_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            inputs = {
                "preflight.json": preflight_report(),
                "bootstrap.json": build_trial_bootstrap_plan(ROOT, generated_at="2026-07-01T04:40:00+10:00"),
                "scheduler.json": build_production_scheduler_plan(ROOT, generated_at="2026-07-01T04:41:00+10:00"),
                "source.json": source_batch(),
                "smtp.json": smtp_report(),
                "release.json": release_report(),
            }
            for name, payload in inputs.items():
                (tmp_path / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            args = [
                "plan-trial-start",
                "--preflight-report",
                str(tmp_path / "preflight.json"),
                "--bootstrap-plan",
                str(tmp_path / "bootstrap.json"),
                "--scheduler-plan",
                str(tmp_path / "scheduler.json"),
                "--source-batch",
                str(tmp_path / "source.json"),
                "--smtp-delivery",
                str(tmp_path / "smtp.json"),
                "--release-delivery",
                str(tmp_path / "release.json"),
                "--generated-at",
                "2026-07-01T05:10:00+10:00",
                "--confirm-start",
                "--json",
            ]
            for key, value in refs().items():
                args.extend([f"--{key.replace('_', '-')}", value])
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(args)

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TRIAL_START_MODEL_ID)
        self.assertTrue(payload["trial_start_ready"])


if __name__ == "__main__":
    unittest.main()
