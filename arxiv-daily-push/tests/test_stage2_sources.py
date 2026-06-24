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
from arxiv_daily_push.top_journal_adapter import ingest_latest_top_journal
from arxiv_daily_push.stage2_sources import (
    S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID,
    S2PCT05_ENGINEERING_SIGNAL_MODEL_ID,
    S2PCT04_JOURNAL_PROFILE_MODEL_ID,
    S2PCT03_LANCET_SHADOW_MODEL_ID,
    S2PCT02_SCIENCE_SHADOW_MODEL_ID,
    S2P1_PREPRINT_REPLAY_MODEL_ID,
    S2P1_PREPRINT_PROMOTION_MODEL_ID,
    S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
    build_s2pct05_engineering_signal_report,
    build_s2pct06_authoritative_report_source_report,
    build_s2pct04_top_journal_profile_report,
    build_s2pct03_lancet_daily_input,
    build_s2pct02_science_daily_input,
    build_s2p2_top_journal_daily_input,
    build_s2p1_preprint_replay_shadow_evidence,
    build_s2p1_preprint_daily_input,
    build_s2p1_preprint_promotion_report,
    run_s2pct05_engineering_signal_shadow,
    run_s2pct06_authoritative_report_shadow,
    run_s2pct04_top_journal_profile_shadow,
    run_s2pct03_lancet_shadow_daily,
    run_s2pct02_science_shadow_daily,
    run_s2p2_top_journal_shadow_daily,
    run_s2p1_preprint_shadow_daily,
    validate_s2pct05_engineering_signal_report,
    validate_s2pct06_authoritative_report_source_report,
    validate_s2pct04_top_journal_profile_report,
    validate_s2p1_preprint_replay_shadow_report,
    validate_s2p1_shadow_report,
    validate_s2pct03_lancet_shadow_report,
    validate_s2pct02_science_shadow_report,
    validate_s2p2_top_journal_shadow_report,
)


FIXTURES = Path(__file__).parent / "fixtures"
BIORXIV = FIXTURES / "biorxiv_details_sample.json"
MEDRXIV = FIXTURES / "medrxiv_details_sample.json"
NATURE_RSS = FIXTURES / "nature_rss_sample.xml"
SCIENCE_RSS = FIXTURES / "science_rss_sample.xml"
LANCET_RSS = FIXTURES / "lancet_rss_sample.xml"
TOP_JOURNAL_EVENTS = FIXTURES / "top_journal_publication_events.json"
TOP_JOURNAL_PRIOR_PROFILE_STATE = FIXTURES / "top_journal_prior_profile_state.json"
TOP_JOURNAL_ENGINEERING_SIGNALS = FIXTURES / "top_journal_engineering_signals.json"
AUTHORITATIVE_TECHNICAL_REPORTS = FIXTURES / "authoritative_technical_reports.json"
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


def top_journal_batches() -> dict:
    return {
        "nature": ingest_latest_top_journal(
            journal="nature",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: NATURE_RSS.read_text(encoding="utf-8"),
        )
    }


def science_batches() -> dict:
    return {
        "science": ingest_latest_top_journal(
            journal="science",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: SCIENCE_RSS.read_text(encoding="utf-8"),
        )
    }


def lancet_batches() -> dict:
    return {
        "lancet": ingest_latest_top_journal(
            journal="lancet",
            generated_at=GENERATED_AT,
            fetcher=lambda _query: LANCET_RSS.read_text(encoding="utf-8"),
        )
    }


def all_top_journal_batches() -> dict:
    combined = {}
    combined.update(top_journal_batches())
    combined.update(science_batches())
    combined.update(lancet_batches())
    return combined


def top_journal_publication_events() -> list:
    return json.loads(TOP_JOURNAL_EVENTS.read_text(encoding="utf-8"))["events"]


def top_journal_prior_profile_state() -> dict:
    return json.loads(TOP_JOURNAL_PRIOR_PROFILE_STATE.read_text(encoding="utf-8"))


def top_journal_profile_report() -> dict:
    return build_s2pct04_top_journal_profile_report(
        generated_at=GENERATED_AT,
        source_batches=all_top_journal_batches(),
        publication_events=top_journal_publication_events(),
        prior_profile_state=top_journal_prior_profile_state(),
    )


def top_journal_engineering_signals() -> list:
    return json.loads(TOP_JOURNAL_ENGINEERING_SIGNALS.read_text(encoding="utf-8"))["signals"]


def engineering_signal_report() -> dict:
    return build_s2pct05_engineering_signal_report(
        generated_at=GENERATED_AT,
        profile_report=top_journal_profile_report(),
        engineering_signals=top_journal_engineering_signals(),
    )


def authoritative_technical_reports() -> list:
    return json.loads(AUTHORITATIVE_TECHNICAL_REPORTS.read_text(encoding="utf-8"))["reports"]


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

    def test_top_journal_daily_input_uses_nature_metadata_for_claims_and_queue(self) -> None:
        report = build_s2p2_top_journal_daily_input(
            date="2026-06-24",
            generated_at=GENERATED_AT,
            source_batches=top_journal_batches(),
        )

        self.assertEqual(report["model_id"], S2P2_TOP_JOURNAL_SHADOW_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["daily_input_ready"])
        self.assertTrue(report["daily_input"]["source_item"]["source_id"].startswith("nature:s41586-"))
        self.assertEqual(report["daily_input"]["source_item"]["source_type"], "rss")
        self.assertIn("Nature", report["daily_input"]["claims"][0]["statement"])
        self.assertEqual(report["daily_input"]["stage2_shadow"]["task_id"], "S2PCT01")

    def test_science_daily_input_uses_article_type_metadata_for_claims_and_queue(self) -> None:
        report = build_s2pct02_science_daily_input(
            date="2026-06-24",
            generated_at=GENERATED_AT,
            source_batches=science_batches(),
        )

        self.assertEqual(report["model_id"], S2PCT02_SCIENCE_SHADOW_MODEL_ID)
        self.assertEqual(report["task_id"], "S2PCT02")
        self.assertEqual(report["legacy_task_id"], "S2P2T02")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["daily_input_ready"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["d2_source_domain_accepted"])
        self.assertFalse(report["stage2_production_accepted"])
        source_item = report["daily_input"]["source_item"]
        self.assertTrue(source_item["source_id"].startswith("science:10.1126/science."))
        self.assertEqual(source_item["source_type"], "rss")
        self.assertIn(source_item["metadata"]["top_journal"]["article_type"], {"research_article", "report", "review", "perspective"})
        self.assertIn("Science", report["daily_input"]["claims"][0]["statement"])
        self.assertEqual(report["daily_input"]["stage2_shadow"]["task_id"], "S2PCT02")

    def test_lancet_daily_input_uses_medical_indexing_metadata_for_claims_and_queue(self) -> None:
        report = build_s2pct03_lancet_daily_input(
            date="2026-06-24",
            generated_at=GENERATED_AT,
            source_batches=lancet_batches(),
        )

        self.assertEqual(report["model_id"], S2PCT03_LANCET_SHADOW_MODEL_ID)
        self.assertEqual(report["task_id"], "S2PCT03")
        self.assertEqual(report["legacy_task_id"], "S2P2T03")
        self.assertEqual(report["acceptance_id"], "ACC-S2PCT03-LANCET")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["daily_input_ready"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["d2_source_domain_accepted"])
        self.assertFalse(report["stage2_production_accepted"])
        source_item = report["daily_input"]["source_item"]
        self.assertTrue(source_item["source_id"].startswith("lancet:10.1016/s0140-6736"))
        self.assertEqual(source_item["source_type"], "rss")
        self.assertIn(source_item["metadata"]["top_journal"]["article_type"], {"article", "review", "series"})
        self.assertEqual(source_item["metadata"]["top_journal"]["index_alignment_gate"], "pass")
        self.assertEqual(source_item["metadata"]["top_journal"]["medical_indexing"]["pubmed_relation_gate"], "doi_query_ready")
        self.assertIn("The Lancet", report["daily_input"]["claims"][0]["statement"])
        self.assertEqual(report["daily_input"]["stage2_shadow"]["task_id"], "S2PCT03")

    def test_s2pct04_profile_report_classifies_taxonomy_relations_and_forced_updates(self) -> None:
        report = build_s2pct04_top_journal_profile_report(
            generated_at=GENERATED_AT,
            source_batches=all_top_journal_batches(),
            publication_events=top_journal_publication_events(),
            prior_profile_state=top_journal_prior_profile_state(),
        )

        self.assertEqual(report["model_id"], S2PCT04_JOURNAL_PROFILE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PCT04-JOURNAL-PROFILE")
        self.assertEqual(report["task_id"], "S2PCT04")
        self.assertEqual(report["legacy_task_id"], "S2P2T04")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["profile_taxonomy_gate"], "pass")
        self.assertEqual(report["publication_relation_gate"], "pass")
        self.assertEqual(report["forced_event_update_gate"], "pass")
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["d2_source_domain_accepted"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertTrue(set(report["required_profile_kinds"]).issubset(set(report["profile_kinds_observed"])))
        relation_types = {edge["relation_type"] for edge in report["publication_relation_edges"]}
        self.assertTrue({"original_publication", "discusses", "corrects", "retracts"}.issubset(relation_types))
        updates = {update["event_type"]: update for update in report["forced_event_updates"]}
        self.assertEqual(updates["correction"]["updated_conclusion_state"], "requires_revision")
        self.assertEqual(updates["retraction"]["updated_conclusion_state"], "invalidated")
        self.assertTrue(updates["correction"]["forced_review_required"])
        self.assertTrue(updates["retraction"]["forced_review_required"])
        self.assertFalse(validate_s2pct04_top_journal_profile_report(report))

    def test_s2pct04_profile_report_blocks_forced_event_without_known_target(self) -> None:
        events = top_journal_publication_events()
        events[-1] = dict(events[-1], target_canonical_document_id="science:10.1126/science.unknown")

        report = build_s2pct04_top_journal_profile_report(
            generated_at=GENERATED_AT,
            source_batches=all_top_journal_batches(),
            publication_events=events,
            prior_profile_state=top_journal_prior_profile_state(),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["forced_event_update_gate"], "blocked")
        self.assertIn("target_canonical_document_id is unknown", " ".join(report["blocking_reasons"]))

    def test_s2pct05_engineering_signal_report_validates_officiality_relations_versions_and_reproducibility(self) -> None:
        report = build_s2pct05_engineering_signal_report(
            generated_at=GENERATED_AT,
            profile_report=top_journal_profile_report(),
            engineering_signals=top_journal_engineering_signals(),
        )

        self.assertEqual(report["model_id"], S2PCT05_ENGINEERING_SIGNAL_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PCT05-ENGINEERING-SIGNALS")
        self.assertEqual(report["task_id"], "S2PCT05")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["profile_gate"], "pass")
        self.assertEqual(report["engineering_signal_taxonomy_gate"], "pass")
        self.assertEqual(report["officiality_gate"], "pass")
        self.assertEqual(report["version_traceability_gate"], "pass")
        self.assertEqual(report["paper_relation_gate"], "pass")
        self.assertEqual(report["reproducibility_state_gate"], "pass")
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["d2_source_domain_accepted"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertTrue(set(report["required_signal_types"]).issubset(set(report["signal_types_observed"])))
        self.assertEqual(report["engineering_signal_count"], 5)
        self.assertFalse(validate_s2pct05_engineering_signal_report(report))

    def test_s2pct05_engineering_signal_report_blocks_unofficial_unknown_relation(self) -> None:
        signals = top_journal_engineering_signals()
        signals[0] = dict(
            signals[0],
            canonical_document_id="science:10.1126/science.unknown",
            officiality_state="mirror",
        )

        report = build_s2pct05_engineering_signal_report(
            generated_at=GENERATED_AT,
            profile_report=top_journal_profile_report(),
            engineering_signals=signals,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["engineering_signal_taxonomy_gate"], "blocked")
        self.assertEqual(report["officiality_gate"], "blocked")
        self.assertEqual(report["paper_relation_gate"], "blocked")
        self.assertIn("officiality_state is not accepted", " ".join(report["blocking_reasons"]))
        self.assertIn("canonical_document_id is unknown", " ".join(report["blocking_reasons"]))
        self.assertIn("official_code_repository", " ".join(report["blocking_reasons"]))

    def test_s2pct06_authoritative_report_source_report_validates_type_identity_interest_and_evidence(self) -> None:
        report = build_s2pct06_authoritative_report_source_report(
            generated_at=GENERATED_AT,
            engineering_signal_report=engineering_signal_report(),
            technical_reports=authoritative_technical_reports(),
        )

        self.assertEqual(report["model_id"], S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PCT06-REPORTS")
        self.assertEqual(report["task_id"], "S2PCT06")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["engineering_signal_gate"], "pass")
        self.assertEqual(report["report_taxonomy_gate"], "pass")
        self.assertEqual(report["publisher_identity_gate"], "pass")
        self.assertEqual(report["interest_relation_gate"], "pass")
        self.assertEqual(report["evidence_level_gate"], "pass")
        self.assertEqual(report["traceability_gate"], "pass")
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["d2_source_domain_accepted"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["marketing_material_accepted"])
        self.assertTrue(set(report["required_report_types"]).issubset(set(report["report_types_observed"])))
        self.assertEqual(report["authoritative_report_count"], 4)
        self.assertFalse(validate_s2pct06_authoritative_report_source_report(report))

    def test_s2pct06_authoritative_report_source_report_blocks_unknown_signal_and_marketing_identity(self) -> None:
        reports = authoritative_technical_reports()
        reports[0] = dict(
            reports[0],
            related_signal_ids=["eng-signal:unknown"],
            publisher_identity_state="marketing_page",
            interest_disclosure="",
        )

        report = build_s2pct06_authoritative_report_source_report(
            generated_at=GENERATED_AT,
            engineering_signal_report=engineering_signal_report(),
            technical_reports=reports,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["report_taxonomy_gate"], "blocked")
        self.assertEqual(report["publisher_identity_gate"], "blocked")
        self.assertEqual(report["interest_relation_gate"], "blocked")
        self.assertEqual(report["traceability_gate"], "blocked")
        self.assertIn("publisher_identity_state is not accepted", " ".join(report["blocking_reasons"]))
        self.assertIn("interest_disclosure is required", " ".join(report["blocking_reasons"]))
        self.assertIn("related_signal_ids unknown", " ".join(report["blocking_reasons"]))

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

    def test_top_journal_shadow_daily_persists_queue_ledger_and_email_preview_without_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2p2_top_journal_shadow_daily(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=top_journal_batches(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2p2_top_journal_shadow_report(report))
            self.assertFalse(report["formal_production_inclusion"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertTrue(report["selected_source_id"].startswith("nature:s41586-"))
            self.assertTrue(Path(report["candidate_queue_path"]).is_file())
            self.assertTrue(Path(report["content_ledger_path"]).is_file())
            self.assertTrue(Path(report["email_preview_paths"]["plain"]).is_file())
            email_preview = Path(report["email_preview_paths"]["plain"]).read_text(encoding="utf-8")
            self.assertIn("【今天讲透一个问题】", email_preview)
            self.assertIn("Nature", email_preview)

    def test_science_shadow_daily_persists_queue_ledger_and_email_preview_without_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pct02_science_shadow_daily(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=science_batches(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pct02_science_shadow_report(report))
            self.assertFalse(report["formal_production_inclusion"])
            self.assertFalse(report["d2_source_domain_accepted"])
            self.assertFalse(report["stage2_production_accepted"])
            self.assertFalse(report["integrated_production_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertTrue(report["selected_source_id"].startswith("science:10.1126/science."))
            self.assertTrue(Path(report["candidate_queue_path"]).is_file())
            self.assertTrue(Path(report["content_ledger_path"]).is_file())
            self.assertTrue(Path(report["email_preview_paths"]["plain"]).is_file())
            email_preview = Path(report["email_preview_paths"]["plain"]).read_text(encoding="utf-8")
            self.assertIn("【今天讲透一个问题】", email_preview)
            self.assertIn("Science", email_preview)

    def test_lancet_shadow_daily_persists_queue_ledger_and_email_preview_without_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pct03_lancet_shadow_daily(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=lancet_batches(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pct03_lancet_shadow_report(report))
            self.assertFalse(report["formal_production_inclusion"])
            self.assertFalse(report["d2_source_domain_accepted"])
            self.assertFalse(report["stage2_production_accepted"])
            self.assertFalse(report["integrated_production_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertTrue(report["selected_source_id"].startswith("lancet:10.1016/s0140-6736"))
            self.assertTrue(Path(report["candidate_queue_path"]).is_file())
            self.assertTrue(Path(report["content_ledger_path"]).is_file())
            self.assertTrue(Path(report["email_preview_paths"]["plain"]).is_file())
            email_preview = Path(report["email_preview_paths"]["plain"]).read_text(encoding="utf-8")
            self.assertIn("【今天讲透一个问题】", email_preview)
            self.assertIn("The Lancet", email_preview)

    def test_s2pct04_profile_shadow_persists_report_and_forced_event_ledger_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pct04_top_journal_profile_shadow(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=all_top_journal_batches(),
                publication_events=top_journal_publication_events(),
                prior_profile_state=top_journal_prior_profile_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pct04_top_journal_profile_report(report))
            self.assertFalse(report["formal_production_inclusion"])
            self.assertFalse(report["d2_source_domain_accepted"])
            self.assertFalse(report["stage2_production_accepted"])
            self.assertFalse(report["integrated_production_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertTrue(Path(report["profile_report_path"]).is_file())
            self.assertTrue(Path(report["profile_ledger_path"]).is_file())
            ledger_lines = Path(report["profile_ledger_path"]).read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(ledger_lines), 2)

    def test_s2pct05_engineering_signal_shadow_persists_report_and_ledger_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pct05_engineering_signal_shadow(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                profile_report=top_journal_profile_report(),
                engineering_signals=top_journal_engineering_signals(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pct05_engineering_signal_report(report))
            self.assertFalse(report["formal_production_inclusion"])
            self.assertFalse(report["d2_source_domain_accepted"])
            self.assertFalse(report["stage2_production_accepted"])
            self.assertFalse(report["integrated_production_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertTrue(Path(report["engineering_signal_report_path"]).is_file())
            self.assertTrue(Path(report["engineering_signal_ledger_path"]).is_file())
            ledger_lines = Path(report["engineering_signal_ledger_path"]).read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(ledger_lines), 5)

    def test_s2pct06_authoritative_report_shadow_persists_report_and_ledger_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pct06_authoritative_report_shadow(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                engineering_signal_report=engineering_signal_report(),
                technical_reports=authoritative_technical_reports(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pct06_authoritative_report_source_report(report))
            self.assertFalse(report["formal_production_inclusion"])
            self.assertFalse(report["d2_source_domain_accepted"])
            self.assertFalse(report["stage2_production_accepted"])
            self.assertFalse(report["integrated_production_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["marketing_material_accepted"])
            self.assertTrue(Path(report["authoritative_report_path"]).is_file())
            self.assertTrue(Path(report["authoritative_report_ledger_path"]).is_file())
            ledger_lines = Path(report["authoritative_report_ledger_path"]).read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(ledger_lines), 4)

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

    def test_cli_stage2_top_journal_shadow_daily_outputs_json(self) -> None:
        fake_report = {
            "model_id": S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
            "task_id": "S2PCT01",
            "status": "pass",
            "daily_input_ready": True,
            "email_preview_written": True,
            "selected_source_id": "nature:s41586-026-10807-x",
            "formal_production_inclusion": False,
            "github_cloud_schedule_enabled": False,
            "real_smtp_sent": False,
            "production_affected": False,
            "blocking_reasons": [],
        }
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            nature_batch_path = Path(tmp) / "nature.json"
            nature_batch_path.write_text(json.dumps(top_journal_batches()["nature"], ensure_ascii=False), encoding="utf-8")
            with patch("arxiv_daily_push.cli.run_s2p2_top_journal_shadow_daily", return_value=fake_report):
                with redirect_stdout(buffer):
                    result = main([
                        "stage2-top-journal-shadow-daily",
                        "--state-dir",
                        tmp,
                        "--date",
                        "2026-06-24",
                        "--generated-at",
                        GENERATED_AT,
                        "--nature-batch",
                        str(nature_batch_path),
                        "--no-write",
                        "--json",
                    ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2P2_TOP_JOURNAL_SHADOW_MODEL_ID)

    def test_cli_stage2_science_shadow_daily_outputs_json(self) -> None:
        fake_report = {
            "model_id": S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            "acceptance_id": "ACC-S2PCT02-SCIENCE",
            "task_id": "S2PCT02",
            "status": "pass",
            "daily_input_ready": True,
            "email_preview_written": True,
            "selected_source_id": "science:10.1126/science.ads7910",
            "formal_production_inclusion": False,
            "github_cloud_schedule_enabled": False,
            "real_smtp_sent": False,
            "production_affected": False,
            "d2_source_domain_accepted": False,
            "stage2_production_accepted": False,
            "integrated_production_accepted": False,
            "daily_report": {
                "daily_input": {
                    "source_item": {
                        "source_id": "science:10.1126/science.ads7910",
                        "metadata": {"top_journal": {"article_type": "research_article"}},
                    }
                }
            },
            "blocking_reasons": [],
        }
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            science_batch_path = Path(tmp) / "science.json"
            science_batch_path.write_text(json.dumps(science_batches()["science"], ensure_ascii=False), encoding="utf-8")
            with patch("arxiv_daily_push.cli.run_s2pct02_science_shadow_daily", return_value=fake_report):
                with redirect_stdout(buffer):
                    result = main([
                        "stage2-science-shadow-daily",
                        "--state-dir",
                        tmp,
                        "--date",
                        "2026-06-24",
                        "--generated-at",
                        GENERATED_AT,
                        "--science-batch",
                        str(science_batch_path),
                        "--no-write",
                        "--json",
                    ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PCT02_SCIENCE_SHADOW_MODEL_ID)

    def test_cli_stage2_lancet_shadow_daily_outputs_json(self) -> None:
        fake_report = {
            "model_id": S2PCT03_LANCET_SHADOW_MODEL_ID,
            "acceptance_id": "ACC-S2PCT03-LANCET",
            "task_id": "S2PCT03",
            "status": "pass",
            "daily_input_ready": True,
            "email_preview_written": True,
            "selected_source_id": "lancet:10.1016/s0140-6736(26)01256-0",
            "formal_production_inclusion": False,
            "github_cloud_schedule_enabled": False,
            "real_smtp_sent": False,
            "production_affected": False,
            "d2_source_domain_accepted": False,
            "stage2_production_accepted": False,
            "integrated_production_accepted": False,
            "daily_report": {
                "daily_input": {
                    "source_item": {
                        "source_id": "lancet:10.1016/s0140-6736(26)01256-0",
                        "metadata": {
                            "top_journal": {
                                "article_type": "article",
                                "index_alignment_gate": "pass",
                                "medical_indexing": {"pubmed_relation_gate": "doi_query_ready"},
                            }
                        },
                    }
                }
            },
            "blocking_reasons": [],
        }
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            lancet_batch_path = Path(tmp) / "lancet.json"
            lancet_batch_path.write_text(json.dumps(lancet_batches()["lancet"], ensure_ascii=False), encoding="utf-8")
            with patch("arxiv_daily_push.cli.run_s2pct03_lancet_shadow_daily", return_value=fake_report):
                with redirect_stdout(buffer):
                    result = main([
                        "stage2-lancet-shadow-daily",
                        "--state-dir",
                        tmp,
                        "--date",
                        "2026-06-24",
                        "--generated-at",
                        GENERATED_AT,
                        "--lancet-batch",
                        str(lancet_batch_path),
                        "--no-write",
                        "--json",
                    ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PCT03_LANCET_SHADOW_MODEL_ID)

    def test_cli_stage2_top_journal_profile_shadow_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            nature_batch_path = Path(tmp) / "nature.json"
            science_batch_path = Path(tmp) / "science.json"
            lancet_batch_path = Path(tmp) / "lancet.json"
            nature_batch_path.write_text(json.dumps(top_journal_batches()["nature"], ensure_ascii=False), encoding="utf-8")
            science_batch_path.write_text(json.dumps(science_batches()["science"], ensure_ascii=False), encoding="utf-8")
            lancet_batch_path.write_text(json.dumps(lancet_batches()["lancet"], ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-top-journal-profile-shadow",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--nature-batch",
                    str(nature_batch_path),
                    "--science-batch",
                    str(science_batch_path),
                    "--lancet-batch",
                    str(lancet_batch_path),
                    "--publication-events",
                    str(TOP_JOURNAL_EVENTS),
                    "--prior-profile-state",
                    str(TOP_JOURNAL_PRIOR_PROFILE_STATE),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PCT04_JOURNAL_PROFILE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PCT04")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["forced_event_update_count"], 2)

    def test_cli_stage2_engineering_signals_shadow_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            profile_report_path = Path(tmp) / "profile-report.json"
            profile_report_path.write_text(json.dumps(top_journal_profile_report(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-engineering-signals-shadow",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--profile-report",
                    str(profile_report_path),
                    "--engineering-signals",
                    str(TOP_JOURNAL_ENGINEERING_SIGNALS),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PCT05_ENGINEERING_SIGNAL_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PCT05")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["engineering_signal_count"], 5)

    def test_cli_stage2_authoritative_reports_shadow_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            engineering_report_path = Path(tmp) / "engineering-report.json"
            engineering_report_path.write_text(json.dumps(engineering_signal_report(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-authoritative-reports-shadow",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--engineering-signal-report",
                    str(engineering_report_path),
                    "--technical-reports",
                    str(AUTHORITATIVE_TECHNICAL_REPORTS),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PCT06")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["authoritative_report_count"], 4)


if __name__ == "__main__":
    unittest.main()
