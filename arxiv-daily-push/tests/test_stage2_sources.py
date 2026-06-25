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
    S2PGT05_CALIBRATION_MODEL_ID,
    S2PGT05_REQUIRED_BOARD_IDS,
    S2PGT05_REQUIRED_DECISIONS,
    S2PGT05_REQUIRED_SOURCE_DOMAINS,
    S2PGT04_DELTA_RESONANCE_MODEL_ID,
    S2PGT04_REQUIRED_DELTA_TYPES,
    S2PGT04_REQUIRED_RESONANCE_GROUPS,
    S2PGT03_REQUIRED_CROSS_CUTTING_BOARDS,
    S2PGT03_REQUIRED_PRIMARY_BOARDS,
    S2PGT03_REQUIRED_SOURCE_DOMAINS,
    S2PGT03_ROUTING_MODEL_ID,
    S2PGT02_KNOWLEDGE_GRAPH_MODEL_ID,
    S2PGT02_REQUIRED_GATES,
    S2PGT02_REQUIRED_IDENTIFIER_TYPES,
    S2PGT01_EVIDENCE_PACKET_MODEL_ID,
    S2PGT01_REQUIRED_EVIDENCE_LEVELS,
    S2PGT01_REQUIRED_SOURCE_DOMAINS,
    S2PFT05_D3_FULL_GOVERNANCE_MODEL_ID,
    S2PFT05_REQUIRED_COMPONENTS,
    S2PFT05_REQUIRED_QUOTA_ROLES,
    S2PFT04_REQUIRED_ZONE_IDS,
    S2PFT04_REQUIRED_ZONE_AUTHORITY_ROLES,
    S2PFT04_SPECIAL_ZONE_MODEL_ID,
    S2PFT03_KEY_CITY_COVERAGE_MODEL_ID,
    S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES,
    S2PFT03_REQUIRED_CITY_IDS,
    S2PFT02_HK_MO_PROFILE_MODEL_ID,
    S2PFT01_CHINA_PROVINCIAL_MODEL_ID,
    S2PDT04_D3_READINESS_MODEL_ID,
    S2PDT03_LEGAL_METADATA_MODEL_ID,
    S2PDT02_CHINA_C1_SOURCE_MODEL_ID,
    S2PDT01_CHINA_C0_SOURCE_MODEL_ID,
    S2PET01_US_TA_SOURCE_MODEL_ID,
    S2PET02_US_LG_BACKBONE_MODEL_ID,
    S2PET03_US_FM_BACKBONE_MODEL_ID,
    S2PET04_US_TP_D4_QUALIFICATION_MODEL_ID,
    S2PIT01_REQUIRED_CONTROL_DOMAINS,
    S2PIT02_RUNTIME_DASHBOARD_MODEL_ID,
    S2PIT01_USER_CENTER_MODEL_ID,
    S2PIT03_REQUIRED_READING_BOARDS,
    S2PIT03_REQUIRED_SOURCE_DOMAINS,
    S2PIT03_SOURCE_MODEL_VIEW_MODEL_ID,
    S2PIT04_CONTENT_LEDGER_MODEL_ID,
    S2PJT01_LIFECYCLE_STATE_MODEL_ID,
    S2PJT01_REQUIRED_LEDGER_TYPES,
    S2PJT01_REQUIRED_STATES,
    S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS,
    S2PJT02_REVIEW_SCHEDULE_MODEL_ID,
    S2PJT03_ACTION_ROI_MODEL_ID,
    S2PJT04_WEEKLY_REPORT_MODEL_ID,
    S2PJT05_MONTHLY_REPORT_MODEL_ID,
    S2PKT01_MAIL_CONTRACT_MODEL_ID,
    S2PKT02_M1_MAIL_MODEL_ID,
    S2PKT03_M2_MAIL_MODEL_ID,
    S2PHT05_CONTENT_QUALITY_MODEL_ID,
    S2PHT05_REQUIRED_GOLD_DIMENSIONS,
    S2PCT07_D2_QUALIFICATION_MODEL_ID,
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
    build_s2pct07_d2_source_domain_qualification_report,
    build_s2pgt05_cross_board_calibration_report,
    build_s2pgt04_delta_resonance_report,
    build_s2pgt03_source_board_routing_report,
    build_s2pgt02_knowledge_graph_spine_report,
    build_s2pgt01_evidence_packet_v2_compatibility_report,
    build_s2pft05_d3_full_governance_qualification_report,
    build_s2pft04_special_zone_discovery_report,
    build_s2pft03_key_city_coverage_report,
    build_s2pft02_hk_mo_independent_profile_report,
    build_s2pft01_china_provincial_template_coverage_report,
    build_s2pdt04_china_d3_readiness_review_report,
    build_s2pdt03_china_legal_metadata_relation_shadow_report,
    build_s2pdt02_china_c1_department_source_map_report,
    build_s2pdt01_china_c0_source_foundation_report,
    build_s2pet01_us_ta_source_foundation_report,
    build_s2pet02_us_lg_legal_backbone_report,
    build_s2pet03_us_fm_source_backbone_report,
    build_s2pet04_us_tp_d4_qualification_report,
    build_s2pit01_user_center_report,
    build_s2pit02_runtime_dashboard_report,
    build_s2pit03_source_model_view_report,
    build_s2pit04_content_ledger_report,
    build_s2pkt01_mail_contract_report,
    build_s2pkt02_m1_mail_report,
    build_s2pkt03_m2_mail_report,
    build_s2pjt01_lifecycle_state_report,
    build_s2pjt02_review_schedule_report,
    build_s2pjt03_action_asset_roi_report,
    build_s2pjt04_weekly_report,
    build_s2pjt05_monthly_report,
    build_s2pht05_content_quality_gate_report,
    build_s2pct04_top_journal_profile_report,
    build_s2pct03_lancet_daily_input,
    build_s2pct02_science_daily_input,
    build_s2p2_top_journal_daily_input,
    build_s2p1_preprint_replay_shadow_evidence,
    build_s2p1_preprint_daily_input,
    build_s2p1_preprint_promotion_report,
    run_s2pct05_engineering_signal_shadow,
    run_s2pct06_authoritative_report_shadow,
    run_s2pct07_d2_source_domain_qualification,
    run_s2pgt05_cross_board_calibration,
    run_s2pgt04_delta_resonance,
    run_s2pgt03_source_board_routing,
    run_s2pgt02_knowledge_graph_spine,
    run_s2pgt01_evidence_packet_v2_compatibility,
    run_s2pft05_d3_full_governance_qualification,
    run_s2pft04_special_zone_discovery,
    run_s2pft03_key_city_coverage,
    run_s2pft02_hk_mo_independent_profile,
    run_s2pft01_china_provincial_template_coverage,
    run_s2pdt04_china_d3_readiness_review,
    run_s2pdt03_china_legal_metadata_relation_shadow,
    run_s2pdt02_china_c1_department_source_map,
    run_s2pdt01_china_c0_source_foundation,
    run_s2pet01_us_ta_source_foundation,
    run_s2pet02_us_lg_legal_backbone,
    run_s2pet03_us_fm_source_backbone,
    run_s2pet04_us_tp_d4_qualification,
    run_s2pit01_user_center,
    run_s2pit02_runtime_dashboard,
    run_s2pit03_source_model_view,
    run_s2pit04_content_ledger,
    run_s2pkt01_mail_contract,
    run_s2pkt02_m1_mail,
    run_s2pkt03_m2_mail,
    run_s2pjt01_lifecycle_state,
    run_s2pjt02_review_schedule,
    run_s2pjt03_action_asset_roi,
    run_s2pjt04_weekly_report,
    run_s2pjt05_monthly_report,
    run_s2pht05_content_quality_gate,
    run_s2pct04_top_journal_profile_shadow,
    run_s2pct03_lancet_shadow_daily,
    run_s2pct02_science_shadow_daily,
    run_s2p2_top_journal_shadow_daily,
    run_s2p1_preprint_shadow_daily,
    validate_s2pct05_engineering_signal_report,
    validate_s2pct06_authoritative_report_source_report,
    validate_s2pct07_d2_source_domain_qualification_report,
    validate_s2pgt05_cross_board_calibration_report,
    validate_s2pgt04_delta_resonance_report,
    validate_s2pgt03_source_board_routing_report,
    validate_s2pgt02_knowledge_graph_spine_report,
    validate_s2pgt01_evidence_packet_v2_compatibility_report,
    validate_s2pft05_d3_full_governance_qualification_report,
    validate_s2pft04_special_zone_discovery_report,
    validate_s2pft03_key_city_coverage_report,
    validate_s2pft02_hk_mo_independent_profile_report,
    validate_s2pft01_china_provincial_template_coverage_report,
    validate_s2pdt04_china_d3_readiness_review_report,
    validate_s2pdt03_china_legal_metadata_relation_shadow_report,
    validate_s2pdt02_china_c1_department_source_map_report,
    validate_s2pdt01_china_c0_source_foundation_report,
    validate_s2pet01_us_ta_source_foundation_report,
    validate_s2pet02_us_lg_legal_backbone_report,
    validate_s2pet03_us_fm_source_backbone_report,
    validate_s2pet04_us_tp_d4_qualification_report,
    validate_s2pit01_user_center_report,
    validate_s2pit02_runtime_dashboard_report,
    validate_s2pit03_source_model_view_report,
    validate_s2pit04_content_ledger_report,
    validate_s2pkt01_mail_contract_report,
    validate_s2pkt02_m1_mail_report,
    validate_s2pkt03_m2_mail_report,
    validate_s2pjt01_lifecycle_state_report,
    validate_s2pjt02_review_schedule_report,
    validate_s2pjt03_action_asset_roi_report,
    validate_s2pjt04_weekly_report,
    validate_s2pjt05_monthly_report,
    validate_s2pht05_content_quality_gate_report,
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


def s2pit01_owner_controls() -> dict:
    return {
        "schema_version": 1,
        "config_version": "owner-controls-test",
        "task_id": "S2PIT01",
        "project": {"production_enabled": False},
        "cost_policy": {"paid_data_api_allowed": False, "paid_cloud_compute_allowed": False, "paid_openai_api_allowed": False},
        "runtime": {"max_fetch_concurrency": 1, "max_temp_cache_gb": 0.1, "window_a_resource_limits": {"max_online_arxiv_metadata": 10}},
        "intelligence_provider": {"paid_openai_api_allowed": False},
        "boards": [{"board_id": "B1", "enabled": True}],
        "sources": [{"source_id": "SRC-ARXIV", "enabled": True}],
        "email": {"enabled": True, "split_mode": "3+1", "send_order": ["M1", "M2", "M3", "M4"], "recipients": ["owner@example.com"]},
        "outputs": {"report_enabled": True, "production_acceptance_claimed": False},
        "queue": {"max_active_items": 10000},
        "scoring": {"weights": {"quality": 1.0}},
        "source_defaults": {"metadata_only": True},
        "iteration": {"review_enabled": True},
        "validation": {"rollback_config_version": "owner-controls-previous"},
    }


def s2pit01_owner_validation(status: str = "pass") -> dict:
    return {
        "model_id": "adp-owner-controls-v1",
        "status": status,
        "schema_valid": status == "pass",
        "config_version": "owner-controls-test",
        "task_id": "S2PIT01",
        "production_enabled": False,
        "owner_view_files": [
            "docs/owner/OWNER_CONSOLE.md",
            "docs/owner/SOURCE_CATALOG.md",
            "docs/owner/MODEL_AND_QUEUE.md",
            "docs/owner/CONTENT_LEDGER.csv",
        ],
        "rollback_config_version": "owner-controls-previous",
        "warnings": [],
        "errors": [] if status == "pass" else ["owner controls blocked"],
    }


def s2pit01_owner_preview() -> dict:
    return {
        "model_id": "adp-owner-controls-v1",
        "status": "pass",
        "days": 30,
        "config_version": "owner-controls-test",
        "schema_status": "pass",
        "enabled_sources": ["SRC-ARXIV"],
        "enabled_boards": ["B1"],
        "rollback_config_version": "owner-controls-previous",
        "warnings": [],
        "errors": [],
    }


def s2pit01_storage_inspect(status: str = "pass") -> dict:
    return {
        "model_id": "adp-sqlite-data-model-v1",
        "action": "inspect",
        "status": status,
        "db_path": "state/adp.sqlite3",
        "schema_version": 1 if status == "pass" else 0,
        "table_count": 18 if status == "pass" else 0,
        "blocking_reasons": [] if status == "pass" else ["database file does not exist"],
    }


def s2pit01_user_center_report() -> dict:
    return build_s2pit01_user_center_report(
        generated_at=GENERATED_AT,
        owner_controls=s2pit01_owner_controls(),
        owner_validation_report=s2pit01_owner_validation(),
        owner_impact_preview=s2pit01_owner_preview(),
        storage_inspect_report=s2pit01_storage_inspect(),
    )


def s2pit02_runtime_report(action: str, status: str = "pass") -> dict:
    return {
        "model_id": "adp-stage1-local-runtime-recovery-v1",
        "schema_version": 1,
        "acceptance_id": "ADP-ACC-S1-08-LOCAL-RUNTIME-RECOVERY",
        "action": action,
        "status": status,
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "real_scheduler_installed": False,
        "blocking_reasons": [] if status == "pass" else [f"{action} blocked"],
    }


def s2pit02_production_gate_state(**overrides: object) -> dict:
    state = {
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_restore_executed": False,
        "real_smtp_sent": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
    }
    state.update(overrides)
    return state


def s2pit02_runtime_dashboard_report() -> dict:
    return build_s2pit02_runtime_dashboard_report(
        generated_at=GENERATED_AT,
        user_center_report=s2pit01_user_center_report(),
        runtime_audit_report=s2pit02_runtime_report("runtime_audit"),
        watchdog_report=s2pit02_runtime_report("watchdog"),
        storage_inspect_report=s2pit01_storage_inspect(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pit03_source_domains() -> list[dict]:
    return [
        {
            "domain_id": domain,
            "label_zh": f"{domain} 数据源域",
            "health_status": "ready",
            "source_refs": [f"source:{domain.lower()}"],
            "evidence_refs": [f"docs/phase_records/{domain}.md"],
            "live_fetch_executed": False,
            "source_adapter_changed": False,
            "queue_mutation_allowed": False,
            "ranking_algorithm_changed": False,
            "public_schema_changed": False,
            "real_smtp_sent": False,
            "scheduler_enabled": False,
            "release_upload_allowed": False,
        }
        for domain in S2PIT03_REQUIRED_SOURCE_DOMAINS
    ]


def s2pit03_reading_boards() -> list[dict]:
    return [
        {
            "board_id": board,
            "label_zh": f"{board} 阅读板块",
            "health_status": "ready",
            "source_domain_refs": list(S2PIT03_REQUIRED_SOURCE_DOMAINS[:2]),
            "evidence_refs": [f"docs/phase_records/{board}.md"],
            "live_fetch_executed": False,
            "source_adapter_changed": False,
            "queue_mutation_allowed": False,
            "ranking_algorithm_changed": False,
            "public_schema_changed": False,
            "real_smtp_sent": False,
            "scheduler_enabled": False,
            "release_upload_allowed": False,
        }
        for board in S2PIT03_REQUIRED_READING_BOARDS
    ]


def s2pit03_parameter_records(count: int = 12) -> list[dict]:
    return [
        {
            "parameter_id": f"PARAM-TEST-{index:03d}",
            "display_name_zh": f"测试参数 {index}",
            "default_value": index,
            "value_range": "0..100",
            "rollback_value": 0,
            "impact": "影响队列解释和用户可读视图，不改变生产排名。",
            "code_refs": ["arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py"],
            "test_refs": ["arxiv-daily-push/tests/test_stage2_sources.py"],
            "evidence_refs": ["arxiv-daily-push/docs/governance/parameter_registry.csv"],
            "first_screen": index <= 12,
            "searchable": True,
            "disclosure_tier": "core" if index <= 6 else "advanced",
            "live_fetch_executed": False,
            "source_adapter_changed": False,
            "queue_mutation_allowed": False,
            "ranking_algorithm_changed": False,
            "public_schema_changed": False,
            "real_smtp_sent": False,
            "scheduler_enabled": False,
            "release_upload_allowed": False,
        }
        for index in range(1, count + 1)
    ]


def s2pit03_queue_view_records() -> list[dict]:
    return [
        {
            "content_id": f"content:{index}",
            "source_domain": S2PIT03_REQUIRED_SOURCE_DOMAINS[index % len(S2PIT03_REQUIRED_SOURCE_DOMAINS)],
            "board_id": S2PIT03_REQUIRED_READING_BOARDS[index % len(S2PIT03_REQUIRED_READING_BOARDS)],
            "status": "queued",
            "evidence_refs": [f"evidence:{index}"],
            "detail_ref": f"docs/owner/queue/{index}.md",
            "exportable": True,
            "live_fetch_executed": False,
            "source_adapter_changed": False,
            "queue_mutation_allowed": False,
            "ranking_algorithm_changed": False,
            "public_schema_changed": False,
            "real_smtp_sent": False,
            "scheduler_enabled": False,
            "release_upload_allowed": False,
        }
        for index in range(1, 7)
    ]


def s2pit03_source_model_view_report() -> dict:
    return build_s2pit03_source_model_view_report(
        generated_at=GENERATED_AT,
        user_center_report=s2pit01_user_center_report(),
        source_domain_records=s2pit03_source_domains(),
        reading_board_records=s2pit03_reading_boards(),
        parameter_records=s2pit03_parameter_records(),
        queue_view_records=s2pit03_queue_view_records(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pjt01_lifecycle_records() -> list[dict]:
    records = []
    for index, state in enumerate(S2PJT01_REQUIRED_STATES, start=1):
        content_id = f"content:{index}"
        ledger_type = S2PJT01_REQUIRED_LEDGER_TYPES[index - 1]
        records.append(
            {
                "content_id": content_id,
                "current_state": state,
                "state_history": [
                    {"state": "QUEUED", "changed_at": f"2026-06-24T0{index}:00:00+10:00"},
                    {"state": state, "changed_at": f"2026-06-24T1{index}:00:00+10:00"},
                ],
                "ledger_refs": [{"ledger_type": ledger_type, "ledger_id": f"{ledger_type}:{index}"}],
                "queue_mutation_allowed": False,
                "ranking_algorithm_changed": False,
                "public_schema_changed": False,
                "real_smtp_sent": False,
            }
        )
    return records


def s2pjt01_migration_plan(**overrides: object) -> dict:
    plan = {
        "schema_name": "private_lifecycle_state_v1",
        "dry_run_only": True,
        "rollback_supported": True,
        "db_migration_executed": False,
        "public_schema_changed": False,
        "count_conservation_checked": True,
        "count_conservation_strategy": "pre_post_state_count_match",
        "rollback_plan_ref": "docs/phase_records/PHASE_S2PJT01_LIFECYCLE_STATE.md#rollback",
    }
    plan.update(overrides)
    return plan


def s2pjt01_lifecycle_state_report() -> dict:
    return build_s2pjt01_lifecycle_state_report(
        generated_at=GENERATED_AT,
        runtime_dashboard_report=s2pit02_runtime_dashboard_report(),
        lifecycle_records=s2pjt01_lifecycle_records(),
        migration_plan=s2pjt01_migration_plan(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pjt02_review_records() -> list[dict]:
    return [
        {
            "content_id": "content:overdue",
            "anchor_date": "2026-06-22",
            "review_stage_days": 1,
            "due_date": "2026-06-23",
            "status": "pending",
            "queue_mutation_allowed": False,
            "scheduler_enabled": False,
            "real_smtp_sent": False,
            "public_schema_changed": False,
        },
        {
            "content_id": "content:today",
            "anchor_date": "2026-06-24",
            "review_stage_days": 1,
            "due_date": "2026-06-25",
            "status": "pending",
            "queue_mutation_allowed": False,
            "scheduler_enabled": False,
            "real_smtp_sent": False,
            "public_schema_changed": False,
        },
        {
            "content_id": "content:week",
            "anchor_date": "2026-06-24",
            "review_stage_days": 3,
            "due_date": "2026-06-27",
            "status": "pending",
            "queue_mutation_allowed": False,
            "scheduler_enabled": False,
            "real_smtp_sent": False,
            "public_schema_changed": False,
        },
        {
            "content_id": "content:future",
            "anchor_date": "2026-06-24",
            "review_stage_days": 14,
            "due_date": "2026-07-08",
            "status": "pending",
            "queue_mutation_allowed": False,
            "scheduler_enabled": False,
            "real_smtp_sent": False,
            "public_schema_changed": False,
        },
        {
            "content_id": "content:done",
            "anchor_date": "2026-05-26",
            "review_stage_days": 30,
            "due_date": "2026-06-25",
            "status": "completed",
            "completed_at": "2026-06-25T09:00:00+10:00",
            "queue_mutation_allowed": False,
            "scheduler_enabled": False,
            "real_smtp_sent": False,
            "public_schema_changed": False,
        },
    ]


def s2pjt02_schedule_policy(**overrides: object) -> dict:
    policy = {
        "review_intervals_days": list(S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS),
        "feedback_adjustment_supported": True,
        "dry_run_only": True,
        "expected_counts": {"due_today": 1, "due_next_7_days": 2, "overdue": 1, "completed": 1},
    }
    policy.update(overrides)
    return policy


def s2pjt02_review_schedule_report() -> dict:
    return build_s2pjt02_review_schedule_report(
        generated_at=GENERATED_AT,
        service_date="2026-06-25",
        lifecycle_state_report=s2pjt01_lifecycle_state_report(),
        review_records=s2pjt02_review_records(),
        schedule_policy=s2pjt02_schedule_policy(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pjt03_action_records() -> list[dict]:
    return [
        {
            "action_id": "act:15m",
            "content_id": "content:today",
            "horizon": "15m",
            "status": "completed",
            "expected_roi": {
                "value": "clarify one mechanism and one follow-up question",
                "assumptions": ["15 minute note is enough to preserve the paper's reusable method"],
                "confidence": 0.72,
            },
            "actual_roi": {
                "status": "not_calculable",
                "reason": "no verifiable cost/benefit evidence yet",
            },
        },
        {
            "action_id": "act:2h",
            "content_id": "content:today",
            "horizon": "2h",
            "status": "planned",
            "expected_roi": {
                "value": "build a reusable method checklist",
                "assumptions": ["method checklist can transfer to adjacent papers"],
                "confidence": 0.66,
            },
            "actual_roi": {"status": "not_calculable"},
        },
        {
            "action_id": "act:7d",
            "content_id": "content:week",
            "horizon": "7d",
            "status": "planned",
            "expected_roi": {
                "value": "compare three papers and extract a reusable framework",
                "assumptions": ["the comparison set remains stable for one week"],
                "confidence": 0.61,
            },
            "actual_roi": {"status": "not_calculable"},
        },
        {
            "action_id": "act:30d",
            "content_id": "content:done",
            "horizon": "30d",
            "status": "completed",
            "expected_roi": {
                "value": "convert method notes into a durable capability asset",
                "assumptions": ["asset reuse saves future review time"],
                "confidence": 0.7,
            },
            "actual_roi": {
                "status": "calculated",
                "verifiable_cost": 2.0,
                "verifiable_benefit": 5.0,
                "evidence_refs": ["local://asset/method-checklist-v1"],
            },
        },
    ]


def s2pjt03_capability_assets() -> list[dict]:
    return [
        {
            "asset_id": "asset:method-checklist-v1",
            "content_id": "content:done",
            "asset_type": "method_checklist",
            "evidence_refs": ["local://notes/method-checklist-v1.md"],
            "reuse_scenarios": ["future_paper_review", "weekly_synthesis"],
        }
    ]


def s2pjt03_action_roi_report() -> dict:
    return build_s2pjt03_action_asset_roi_report(
        generated_at=GENERATED_AT,
        service_date="2026-06-25",
        review_schedule_report=s2pjt02_review_schedule_report(),
        action_records=s2pjt03_action_records(),
        capability_assets=s2pjt03_capability_assets(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pit04_ledger_records() -> list[dict]:
    return [
        {
            "content_id": "content:today",
            "evidence_refs": ["local://evidence/content-today"],
            "run_id": "run:20260625:M1",
            "mail_id": "mail:M1:content-today",
            "mail_status": "previewed",
            "feedback_id": "feedback:content-today",
            "feedback_status": "pending",
            "lifecycle_state": "ACTION",
            "review_ids": ["review:content-today"],
            "action_ids": ["act:15m", "act:2h"],
            "asset_ids": [],
            "roi": {"status": "not_calculable", "evidence_refs": ["local://roi/not-yet"]},
            "real_smtp_sent": False,
            "scheduler_enabled": False,
            "release_upload_allowed": False,
            "db_migration_executed": False,
            "public_schema_changed": False,
            "queue_mutation_allowed": False,
            "source_adapter_changed": False,
            "email_frontstage_changed": False,
        },
        {
            "content_id": "content:week",
            "evidence_refs": ["local://evidence/content-week"],
            "run_id": "run:20260625:M2",
            "mail_id": "mail:M2:content-week",
            "mail_status": "ready_no_send",
            "feedback_id": "feedback:content-week",
            "feedback_status": "not_requested",
            "lifecycle_state": "REVIEW_DUE",
            "review_ids": ["review:content-week"],
            "action_ids": ["act:7d"],
            "asset_ids": [],
            "roi": {"status": "not_calculable", "evidence_refs": ["local://roi/not-yet"]},
            "real_smtp_sent": False,
            "scheduler_enabled": False,
            "release_upload_allowed": False,
            "db_migration_executed": False,
            "public_schema_changed": False,
            "queue_mutation_allowed": False,
            "source_adapter_changed": False,
            "email_frontstage_changed": False,
        },
        {
            "content_id": "content:done",
            "evidence_refs": ["local://evidence/content-done", "local://asset/method-checklist-v1"],
            "run_id": "run:20260625:M3",
            "mail_id": "mail:M3:content-done",
            "mail_status": "blocked_no_send",
            "feedback_id": "feedback:content-done",
            "feedback_status": "received",
            "lifecycle_state": "ASSET",
            "review_ids": ["review:content-done"],
            "action_ids": ["act:30d"],
            "asset_ids": ["asset:method-checklist-v1"],
            "roi": {"status": "calculated", "evidence_refs": ["local://asset/method-checklist-v1"]},
            "real_smtp_sent": False,
            "scheduler_enabled": False,
            "release_upload_allowed": False,
            "db_migration_executed": False,
            "public_schema_changed": False,
            "queue_mutation_allowed": False,
            "source_adapter_changed": False,
            "email_frontstage_changed": False,
        },
    ]


def s2pit04_content_ledger_report() -> dict:
    return build_s2pit04_content_ledger_report(
        generated_at=GENERATED_AT,
        runtime_dashboard_report=s2pit02_runtime_dashboard_report(),
        source_model_view_report=s2pit03_source_model_view_report(),
        lifecycle_state_report=s2pjt01_lifecycle_state_report(),
        review_schedule_report=s2pjt02_review_schedule_report(),
        action_roi_report=s2pjt03_action_roi_report(),
        ledger_records=s2pit04_ledger_records(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pht05_content_quality_gate_report() -> dict:
    return build_s2pht05_content_quality_gate_report(
        generated_at=GENERATED_AT,
        dependency_receipts=s2pht05_dependency_receipts(),
        gold_items=s2pht05_gold_items(),
        stage1_regression_checks=s2pht05_stage1_regression_checks(),
        manual_review_samples=s2pht05_manual_review_samples(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pkt01_mail_contracts() -> list[dict]:
    common = {
        "contract_id": "EMAIL_LEARNING_V1",
        "template_version": "1.0.0",
        "cross_cutting_boards": ["B4", "B5", "B6"],
        "reading_layers": ["plain_language_summary", "evidence_trace", "action_roi_transfer"],
        "evidence_labels": ["FACT", "INFERENCE", "OPINION", "OBSERVATION"],
        "feedback_actions": ["useful", "need_more_evidence", "save_for_review", "create_action"],
        "real_smtp_sent": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "db_migration_executed": False,
        "schema_migration_allowed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "ranking_algorithm_changed": False,
        "source_adapter_changed": False,
        "email_frontstage_changed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
    }
    return [
        {**common, "mail_product_id": "M1", "primary_board": "B1", "status": "previewed"},
        {**common, "mail_product_id": "M2", "primary_board": "B2", "status": "ready_no_send"},
        {**common, "mail_product_id": "M3", "primary_board": "B3", "status": "ready_no_send"},
        {**common, "mail_product_id": "M4", "primary_board": "B1-B6", "status": "blocked_no_send"},
    ]


def s2pkt01_mail_contract_report() -> dict:
    return build_s2pkt01_mail_contract_report(
        generated_at=GENERATED_AT,
        content_quality_report=s2pht05_content_quality_gate_report(),
        content_ledger_report=s2pit04_content_ledger_report(),
        action_roi_report=s2pjt03_action_roi_report(),
        mail_contracts=s2pkt01_mail_contracts(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pkt02_m1_mail_record() -> dict:
    common = {
        "content_ids": ["content:today"],
        "evidence_refs": ["local://evidence/content-today"],
    }
    return {
        "mail_product_id": "M1",
        "contract_id": "EMAIL_LEARNING_V1",
        "template_version": "1.0.0",
        "primary_board": "B1",
        "cross_cutting_boards": ["B4", "B5", "B6"],
        "source_content_ids": ["content:today"],
        "action_ids": ["act:15m", "act:2h"],
        "status": "previewed",
        "sections": [
            {**common, "section_id": "scientific_mechanism", "evidence_labels": ["FACT", "INFERENCE"]},
            {**common, "section_id": "evidence_chain", "evidence_labels": ["FACT", "OBSERVATION"]},
            {**common, "section_id": "counterevidence", "evidence_labels": ["INFERENCE", "OBSERVATION"]},
            {**common, "section_id": "personal_value", "evidence_labels": ["OPINION", "INFERENCE"]},
            {
                **common,
                "section_id": "action_path",
                "evidence_labels": ["FACT", "OPINION"],
                "action_ids": ["act:15m", "act:2h"],
            },
        ],
        "real_smtp_sent": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "db_migration_executed": False,
        "schema_migration_allowed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "ranking_algorithm_changed": False,
        "source_adapter_changed": False,
        "email_frontstage_changed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
    }


def s2pkt02_m1_mail_report() -> dict:
    return build_s2pkt02_m1_mail_report(
        generated_at=GENERATED_AT,
        mail_contract_report=s2pkt01_mail_contract_report(),
        content_quality_report=s2pht05_content_quality_gate_report(),
        content_ledger_report=s2pit04_content_ledger_report(),
        action_roi_report=s2pjt03_action_roi_report(),
        m1_mail_record=s2pkt02_m1_mail_record(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pkt03_m2_mail_record() -> dict:
    common = {
        "content_ids": ["content:week"],
        "evidence_refs": ["local://evidence/content-week"],
    }
    return {
        "mail_product_id": "M2",
        "contract_id": "EMAIL_LEARNING_V1",
        "template_version": "1.0.0",
        "primary_board": "B2",
        "cross_cutting_boards": ["B4", "B5", "B6"],
        "source_content_ids": ["content:week"],
        "action_ids": ["act:2h", "act:7d"],
        "status": "ready_no_send",
        "sections": [
            {**common, "section_id": "engineering_usability", "evidence_labels": ["FACT", "OBSERVATION"]},
            {**common, "section_id": "reproducibility", "evidence_labels": ["FACT", "OBSERVATION"]},
            {**common, "section_id": "product_industry_value", "evidence_labels": ["INFERENCE", "OPINION"]},
            {**common, "section_id": "limitations", "evidence_labels": ["INFERENCE", "OBSERVATION"]},
            {
                **common,
                "section_id": "action_path",
                "evidence_labels": ["FACT", "OPINION"],
                "action_ids": ["act:2h", "act:7d"],
            },
        ],
        "real_smtp_sent": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "db_migration_executed": False,
        "schema_migration_allowed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "ranking_algorithm_changed": False,
        "source_adapter_changed": False,
        "email_frontstage_changed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
    }


def s2pkt03_m2_mail_report() -> dict:
    return build_s2pkt03_m2_mail_report(
        generated_at=GENERATED_AT,
        mail_contract_report=s2pkt01_mail_contract_report(),
        content_quality_report=s2pht05_content_quality_gate_report(),
        content_ledger_report=s2pit04_content_ledger_report(),
        action_roi_report=s2pjt03_action_roi_report(),
        m2_mail_record=s2pkt03_m2_mail_record(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pjt04_weekly_items() -> list[dict]:
    return [
        {
            "content_id": "content:today",
            "title": "Mechanism note",
            "observed_date": "2026-06-23",
            "actual_state": "ACTION",
            "section_tags": ["weekly_mainline", "review_summary", "action_summary"],
            "evidence_refs": ["local://actions/act-15m"],
        },
        {
            "content_id": "content:week",
            "title": "Counterexample note",
            "observed_date": "2026-06-24",
            "actual_state": "REVIEW_DUE",
            "section_tags": ["counterevidence", "review_summary"],
            "evidence_refs": ["local://review/content-week"],
        },
        {
            "content_id": "content:done",
            "title": "Reusable method checklist",
            "observed_date": "2026-06-25",
            "actual_state": "ASSET",
            "section_tags": ["asset_summary", "action_summary", "next_week_focus"],
            "evidence_refs": ["local://asset/method-checklist-v1"],
        },
    ]


def s2pjt04_weekly_sections(**overrides: object) -> dict:
    sections = {
        "weekly_mainline": {"summary": "Mechanism notes define the week's primary learning line.", "content_ids": ["content:today"]},
        "counterevidence": {"summary": "A pending review item preserves counterevidence for next synthesis.", "content_ids": ["content:week"]},
        "review_summary": {"summary": "Two items remain tied to review state and due queue context.", "content_ids": ["content:today", "content:week"]},
        "action_summary": {"summary": "Short and long actions are linked to current ledger states.", "content_ids": ["content:today", "content:done"]},
        "asset_summary": {"summary": "The reusable method checklist is the durable asset for the week.", "content_ids": ["content:done"]},
        "next_week_focus": {"summary": "Next week should reuse the checklist and resolve the counterexample.", "content_ids": ["content:week", "content:done"]},
    }
    sections.update(overrides)
    return sections


def s2pjt04_next_week_focus() -> list[dict]:
    return [
        {
            "focus_id": "focus:counterexample-resolution",
            "source_content_ids": ["content:week", "content:done"],
            "priority": 4,
            "rationale": "Resolve the open counterexample using the reusable checklist.",
        }
    ]


def s2pjt04_weekly_report() -> dict:
    return build_s2pjt04_weekly_report(
        generated_at=GENERATED_AT,
        week_start="2026-06-22",
        week_end="2026-06-28",
        action_roi_report=s2pjt03_action_roi_report(),
        weekly_items=s2pjt04_weekly_items(),
        weekly_sections=s2pjt04_weekly_sections(),
        next_week_focus=s2pjt04_next_week_focus(),
        production_gate_state=s2pit02_production_gate_state(),
    )


def s2pjt05_cognitive_snapshots() -> dict:
    return {
        "month_start": {
            "summary": "At month start, the owner treated mechanisms and counterexamples as separate reading tracks.",
            "viewpoint_ids": ["vp:mechanism", "vp:counterexample"],
        },
        "month_end": {
            "summary": "At month end, the owner connected mechanisms, counterexamples, action windows, and reusable assets.",
            "viewpoint_ids": ["vp:mechanism-integrated", "vp:counterexample-resolution", "vp:asset-reuse"],
        },
        "changed_viewpoints": [
            {
                "viewpoint_id": "vp:mechanism-integrated",
                "before": "Mechanism notes were standalone observations.",
                "after": "Mechanism notes now drive action and asset reuse decisions.",
                "evidence_refs": ["local://weekly/content-today", "local://asset/method-checklist-v1"],
            }
        ],
    }


def s2pjt05_monthly_sections(**overrides: object) -> dict:
    sections = {
        "monthly_era_mainline": {"summary": "The monthly mainline links mechanisms to reusable action methods.", "content_ids": ["content:today"]},
        "cognitive_delta": {"summary": "The month-end view merges counterexamples with reusable methods.", "content_ids": ["content:today", "content:week"]},
        "capability_growth": {"summary": "The reusable method checklist became a durable capability asset.", "content_ids": ["content:done"]},
        "economic_conversion": {"summary": "One action produced verifiable positive ROI with local evidence.", "content_ids": ["content:done"]},
        "forecast_review": {"summary": "The counterexample forecast was reviewed against observed outcomes.", "content_ids": ["content:week"]},
        "next_month_focus": {"summary": "Next month prioritizes resolving counterexamples and reusing the checklist.", "content_ids": ["content:week", "content:done"]},
    }
    sections.update(overrides)
    return sections


def s2pjt05_capability_growth() -> list[dict]:
    return [
        {
            "asset_id": "asset:method-checklist-v1",
            "asset_type": "method_checklist",
            "growth_type": "reuse_ready",
            "source_content_ids": ["content:done"],
            "evidence_refs": ["local://asset/method-checklist-v1"],
        }
    ]


def s2pjt05_economic_conversions() -> list[dict]:
    return [
        {
            "conversion_id": "conversion:method-checklist-roi",
            "source_content_ids": ["content:done"],
            "actual_roi_status": "calculated",
            "verifiable_cost": 2.0,
            "verifiable_benefit": 5.0,
            "evidence_refs": ["local://asset/method-checklist-v1"],
        }
    ]


def s2pjt05_forecast_reviews() -> list[dict]:
    return [
        {
            "prediction_id": "prediction:counterexample-resolution",
            "source_content_ids": ["content:week"],
            "forecast": "Counterexample resolution will require the reusable checklist.",
            "outcome": "The weekly report routed the counterexample into next-week focus with the checklist.",
            "accuracy_score": 0.75,
            "evidence_refs": ["local://weekly/content-week"],
        }
    ]


def s2pjt05_next_month_focus() -> list[dict]:
    return [
        {
            "focus_id": "focus:method-transfer",
            "source_content_ids": ["content:week", "content:done"],
            "priority": 5,
            "rationale": "Convert counterexample resolution into reusable monthly method transfer.",
        }
    ]


def s2pht05_dependency_receipts() -> list[dict]:
    return [
        {
            "task_id": task_id,
            "status": "pass",
            "v7_2_revalidated": True,
            "evidence_refs": [f"docs/phase_records/PHASE_{task_id}_LOCAL_EVIDENCE.md"],
        }
        for task_id in ("S2PHT01", "S2PHT02", "S2PHT03", "S2PHT04")
    ]


def s2pht05_gold_items() -> list[dict]:
    items = []
    for index in range(10):
        items.append(
            {
                "gold_id": f"gold:item-{index + 1:02d}",
                "content_id": f"content:quality-{index + 1:02d}",
                "claim_text": "The mechanism claim is supported by cited evidence and bounded by counterevidence.",
                "claim_entailment": "supported" if index % 2 == 0 else "partially_supported",
                "dimension_scores": {dimension: 4.0 + (index % 2) * 0.5 for dimension in S2PHT05_REQUIRED_GOLD_DIMENSIONS},
                "evidence_refs": [f"local://quality/evidence/{index + 1:02d}"],
                "quote_locations": [
                    {
                        "source_ref": f"local://quality/source/{index + 1:02d}",
                        "location": f"section-{index + 1}",
                    }
                ],
                "template_similarity": 0.18 + index * 0.01,
                "counterevidence_refs": [f"local://quality/counterevidence/{index + 1:02d}"],
                "boundary_conditions": ["Only valid for local dry-run semantic evidence."],
                "personal_action": {
                    "action_id": f"action:quality-{index + 1:02d}",
                    "horizon": "7d",
                    "description": "Turn the mechanism into a reusable review checklist.",
                    "evidence_refs": [f"local://quality/action/{index + 1:02d}"],
                },
                "chinese_summary": "该条样本把机制、证据、反证、边界和个人行动连接起来。",
            }
        )
    return items


def s2pht05_stage1_regression_checks() -> list[dict]:
    return [
        {
            "check_id": check_id,
            "status": "pass",
            "evidence_refs": [f"governance/run_manifests/{check_id}.json"],
        }
        for check_id in ("arxiv_collection", "evidence_chain", "email_chain")
    ]


def s2pht05_manual_review_samples() -> list[dict]:
    return [
        {
            "review_id": "manual:quality-01",
            "gold_id": "gold:item-01",
            "reviewer_role": "semantic_quality_reviewer",
            "verdict": "pass",
            "evidence_refs": ["local://quality/manual-review/01"],
        },
        {
            "review_id": "manual:quality-02",
            "gold_id": "gold:item-02",
            "reviewer_role": "owner_experience_reviewer",
            "verdict": "pass",
            "evidence_refs": ["local://quality/manual-review/02"],
        },
    ]


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


def authoritative_report() -> dict:
    return build_s2pct06_authoritative_report_source_report(
        generated_at=GENERATED_AT,
        engineering_signal_report=engineering_signal_report(),
        technical_reports=authoritative_technical_reports(),
    )


def d2_replay_records(start: date = date(2026, 5, 1), count: int = 30) -> list[dict]:
    domains = ("top_journal", "engineering_signal", "authoritative_report")
    return [
        {
            "as_of_date": (start + timedelta(days=offset)).isoformat(),
            "domain": domains[offset % len(domains)],
            "status": "pass",
            "future_leakage_count": 0,
            "p0_p1_blocker_count": 0,
        }
        for offset in range(count)
    ]


def d2_shadow_records() -> list[dict]:
    return [
        {
            "domain": "top_journal",
            "status": "pass",
            "shadow_hours": 48,
            "production_affected": False,
            "real_smtp_sent": False,
        },
        {
            "domain": "engineering_signal",
            "status": "pass",
            "shadow_hours": 48,
            "production_affected": False,
            "real_smtp_sent": False,
        },
        {
            "domain": "authoritative_report",
            "status": "pass",
            "shadow_hours": 48,
            "production_affected": False,
            "real_smtp_sent": False,
        },
    ]


def d2_forced_event_records() -> list[dict]:
    return [
        {
            "event_type": "correction",
            "status": "pass",
            "forced_review_required": True,
            "updated_conclusion_state": "requires_revision",
        },
        {
            "event_type": "retraction",
            "status": "pass",
            "forced_review_required": True,
            "updated_conclusion_state": "invalidated",
        },
    ]


def d2_queue_explanation_records() -> list[dict]:
    return [
        {
            "candidate_id": "candidate:selected",
            "queue_state": "selected",
            "explanation": "highest evidence quality and current decision value",
        },
        {
            "candidate_id": "candidate:queued",
            "queue_state": "queued",
            "explanation": "valuable but not the top daily decision item",
        },
        {
            "candidate_id": "candidate:deferred",
            "queue_state": "deferred",
            "explanation": "awaits forced-event or source-domain review",
        },
    ]


def d2_qualification_report() -> dict:
    return build_s2pct07_d2_source_domain_qualification_report(
        generated_at=GENERATED_AT,
        profile_report=top_journal_profile_report(),
        engineering_signal_report=engineering_signal_report(),
        authoritative_report=authoritative_report(),
        replay_records=d2_replay_records(),
        shadow_records=d2_shadow_records(),
        forced_event_records=d2_forced_event_records(),
        queue_explanation_records=d2_queue_explanation_records(),
    )


def china_c0_source_foundation_report() -> dict:
    return build_s2pdt01_china_c0_source_foundation_report(
        generated_at=GENERATED_AT,
        d2_qualification_report=d2_qualification_report(),
        authority_records=china_c0_authority_records(),
    )


def china_c0_authority_records() -> list[dict]:
    return [
        {
            "source_id": "china-c0:law:constitution-amendment",
            "authority_type": "law_regulation",
            "authority_name": "全国人民代表大会",
            "official_domain": "npc.gov.cn",
            "source_url": "https://www.npc.gov.cn/npc/c30834/constitution-amendment.html",
            "document_number": "全国人民代表大会公告",
            "published_date": "2026-05-01",
            "attachment_trace": "html-metadata-only",
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c0-law"],
        },
        {
            "source_id": "china-c0:npc:committee-report",
            "authority_type": "npc_document",
            "authority_name": "全国人大常委会",
            "official_domain": "npc.gov.cn",
            "source_url": "https://www.npc.gov.cn/npc/c2/committee-report.html",
            "document_number": "委员长会议纪要",
            "published_date": "2026-05-02",
            "attachment_trace": "official-page-metadata",
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c0-npc"],
        },
        {
            "source_id": "china-c0:state-council:policy-notice",
            "authority_type": "state_council_document",
            "authority_name": "国务院",
            "official_domain": "gov.cn",
            "source_url": "https://www.gov.cn/zhengce/content/policy-notice.html",
            "document_number": "国发〔2026〕1号",
            "published_date": "2026-05-03",
            "attachment_trace": "state-council-html",
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c0-state-council"],
        },
        {
            "source_id": "china-c0:gazette:state-council-gazette",
            "authority_type": "gazette",
            "authority_name": "国务院公报",
            "official_domain": "gov.cn",
            "source_url": "https://www.gov.cn/gongbao/2026/issue.html",
            "document_number": "国务院公报2026年第1号",
            "published_date": "2026-05-04",
            "attachment_trace": "gazette-index-metadata",
            "identity_state": "official_gazette",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c0-gazette"],
        },
        {
            "source_id": "china-c0:spc-spp:judicial-interpretation",
            "authority_type": "supreme_court_procuratorate_document",
            "authority_name": "最高人民法院、最高人民检察院",
            "official_domain": "court.gov.cn",
            "source_url": "https://www.court.gov.cn/fabu/xiangqing/judicial-interpretation.html",
            "document_number": "法释〔2026〕1号",
            "published_date": "2026-05-05",
            "attachment_trace": "official-publication-page",
            "identity_state": "official_publication_portal",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c0-spc-spp"],
        },
    ]


def china_c1_department_records() -> list[dict]:
    return [
        {
            "source_id": "china-c1:macro:ndrc",
            "department_id": "ndrc",
            "department_name": "国家发展和改革委员会",
            "sector": "macro_policy",
            "official_domain": "ndrc.gov.cn",
            "source_url": "https://www.ndrc.gov.cn/xwdt/tzgg/index.html",
            "aliases": ["国家发改委", "发改委", "NDRC"],
            "industry_routes": ["macro", "investment", "price"],
            "board_routes": ["B2_policy", "B5_macro"],
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c1-ndrc"],
        },
        {
            "source_id": "china-c1:science:most",
            "department_id": "most",
            "department_name": "科学技术部",
            "sector": "science_technology",
            "official_domain": "most.gov.cn",
            "source_url": "https://www.most.gov.cn/kjbgz/index.html",
            "aliases": ["科技部", "MOST"],
            "industry_routes": ["science", "research", "technology_transfer"],
            "board_routes": ["B2_policy", "B3_frontier"],
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c1-most"],
        },
        {
            "source_id": "china-c1:industry:miit",
            "department_id": "miit",
            "department_name": "工业和信息化部",
            "sector": "industry_policy",
            "official_domain": "miit.gov.cn",
            "source_url": "https://www.miit.gov.cn/zwgk/zcwj/index.html",
            "aliases": ["工信部", "MIIT"],
            "industry_routes": ["manufacturing", "semiconductor", "telecom"],
            "board_routes": ["B2_policy", "B4_industry"],
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c1-miit"],
        },
        {
            "source_id": "china-c1:finance:pboc",
            "department_id": "pboc",
            "department_name": "中国人民银行",
            "sector": "finance",
            "official_domain": "pbc.gov.cn",
            "source_url": "https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html",
            "aliases": ["人民银行", "央行", "PBOC"],
            "industry_routes": ["monetary_policy", "credit", "financial_market"],
            "board_routes": ["B2_policy", "B5_finance"],
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c1-pboc"],
        },
        {
            "source_id": "china-c1:market:samr",
            "department_id": "samr",
            "department_name": "国家市场监督管理总局",
            "sector": "market_regulation",
            "official_domain": "samr.gov.cn",
            "source_url": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/index.html",
            "aliases": ["市场监管总局", "SAMR"],
            "industry_routes": ["market_regulation", "standards", "competition"],
            "board_routes": ["B2_policy", "B6_risk"],
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c1-samr"],
        },
        {
            "source_id": "china-c1:key-industry:nea",
            "department_id": "nea",
            "department_name": "国家能源局",
            "sector": "key_industry",
            "official_domain": "nea.gov.cn",
            "source_url": "https://www.nea.gov.cn/2026-01/01/c_1310000000.htm",
            "aliases": ["能源局", "NEA"],
            "industry_routes": ["energy", "power_grid", "renewables"],
            "board_routes": ["B2_policy", "B4_industry"],
            "identity_state": "official_publication_portal",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "evidence_refs": ["fixture:china-c1-nea"],
        },
    ]


def us_ta_agency_records() -> list[dict]:
    return [
        {
            "source_id": "us-ta:nsf:award-search",
            "agency_id": "NSF",
            "agency_name": "National Science Foundation",
            "signal_type": "grant_award",
            "record_title": "NSF award metadata record",
            "official_domain": "nsf.gov",
            "source_url": "https://www.nsf.gov/awardsearch/showAward?AWD_ID=2600001",
            "published_date": "2026-05-01",
            "identifier": "NSF-AWD-2600001",
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "queue_mutation_allowed": False,
            "evidence_refs": ["fixture:us-ta-nsf-award"],
        },
        {
            "source_id": "us-ta:darpa:program",
            "agency_id": "DARPA",
            "agency_name": "Defense Advanced Research Projects Agency",
            "signal_type": "program_announcement",
            "record_title": "DARPA program announcement metadata",
            "official_domain": "darpa.mil",
            "source_url": "https://www.darpa.mil/research/programs/example-program",
            "published_date": "2026-05-02",
            "identifier": "DARPA-PROGRAM-EXAMPLE",
            "identity_state": "official_publication_portal",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "queue_mutation_allowed": False,
            "evidence_refs": ["fixture:us-ta-darpa-program"],
        },
        {
            "source_id": "us-ta:doe:research",
            "agency_id": "DOE",
            "agency_name": "Department of Energy",
            "signal_type": "research_project",
            "record_title": "DOE research project metadata",
            "official_domain": "energy.gov",
            "source_url": "https://www.energy.gov/science/example-research-project",
            "published_date": "2026-05-03",
            "identifier": "DOE-SC-2600001",
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "queue_mutation_allowed": False,
            "evidence_refs": ["fixture:us-ta-doe-research"],
        },
        {
            "source_id": "us-ta:nih:project",
            "agency_id": "NIH",
            "agency_name": "National Institutes of Health",
            "signal_type": "research_project",
            "record_title": "NIH RePORTER project metadata",
            "official_domain": "nih.gov",
            "source_url": "https://reporter.nih.gov/project-details/2600001",
            "published_date": "2026-05-04",
            "identifier": "NIH-R01-2600001",
            "identity_state": "official_api_or_feed",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "queue_mutation_allowed": False,
            "evidence_refs": ["fixture:us-ta-nih-project"],
        },
        {
            "source_id": "us-ta:nasa:program",
            "agency_id": "NASA",
            "agency_name": "National Aeronautics and Space Administration",
            "signal_type": "program_announcement",
            "record_title": "NASA technology program metadata",
            "official_domain": "nasa.gov",
            "source_url": "https://www.nasa.gov/technology/example-program/",
            "published_date": "2026-05-05",
            "identifier": "NASA-TECH-2600001",
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "queue_mutation_allowed": False,
            "evidence_refs": ["fixture:us-ta-nasa-program"],
        },
        {
            "source_id": "us-ta:nist:standard",
            "agency_id": "NIST",
            "agency_name": "National Institute of Standards and Technology",
            "signal_type": "standard_reference",
            "record_title": "NIST standard reference metadata",
            "official_domain": "nist.gov",
            "source_url": "https://www.nist.gov/publications/example-standard-reference",
            "published_date": "2026-05-06",
            "identifier": "NIST-SP-2600",
            "identity_state": "official_publication_portal",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "queue_mutation_allowed": False,
            "evidence_refs": ["fixture:us-ta-nist-standard"],
        },
        {
            "source_id": "us-ta:uspto:patent",
            "agency_id": "USPTO",
            "agency_name": "United States Patent and Trademark Office",
            "signal_type": "patent_publication",
            "record_title": "USPTO patent publication metadata",
            "official_domain": "uspto.gov",
            "source_url": "https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsbasic.html",
            "published_date": "2026-05-07",
            "identifier": "US-2026-000001-A1",
            "identity_state": "official_publication_portal",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "queue_mutation_allowed": False,
            "evidence_refs": ["fixture:us-ta-uspto-patent"],
        },
        {
            "source_id": "us-ta:fda:reg-sci",
            "agency_id": "FDA",
            "agency_name": "Food and Drug Administration",
            "signal_type": "regulatory_science_notice",
            "record_title": "FDA regulatory science notice metadata",
            "official_domain": "fda.gov",
            "source_url": "https://www.fda.gov/science-research/example-regulatory-science-notice",
            "published_date": "2026-05-08",
            "identifier": "FDA-RSN-2600001",
            "identity_state": "official_domain",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "queue_mutation_allowed": False,
            "evidence_refs": ["fixture:us-ta-fda-reg-sci"],
        },
    ]


def us_ta_source_foundation_report() -> dict:
    return build_s2pet01_us_ta_source_foundation_report(
        generated_at=GENERATED_AT,
        agency_records=us_ta_agency_records(),
    )


def us_lg_legal_records() -> list[dict]:
    base = {
        "metadata_only": True,
        "pdf_downloaded": False,
        "full_text_extracted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "queue_mutation_allowed": False,
        "schema_migration_required": False,
        "legal_advice_provided": False,
        "live_source_fetch_executed": False,
    }
    rows = [
        (
            "us-lg:regulations:docket:doe-2026-0001",
            "regulations_gov",
            "docket",
            "DOE AI infrastructure rulemaking docket metadata",
            "regulations.gov",
            "https://www.regulations.gov/docket/DOE-2026-0001",
            "2026-05-09",
            "DOE-2026-0001",
            "official_publication_portal",
            ["fixture:us-lg-regulations-docket"],
        ),
        (
            "us-lg:fr:proposed-rule:2026-10001",
            "federal_register",
            "proposed_rule",
            "Federal Register proposed AI infrastructure rule metadata",
            "federalregister.gov",
            "https://www.federalregister.gov/documents/2026/05/10/2026-10001/example-proposed-rule",
            "2026-05-10",
            "2026-10001",
            "official_publication_portal",
            ["fixture:us-lg-fr-proposed-rule"],
        ),
        (
            "us-lg:fr:final-rule:2026-10002",
            "federal_register",
            "final_rule",
            "Federal Register final AI infrastructure rule metadata",
            "federalregister.gov",
            "https://www.federalregister.gov/documents/2026/06/10/2026-10002/example-final-rule",
            "2026-06-10",
            "2026-10002",
            "official_publication_portal",
            ["fixture:us-lg-fr-final-rule"],
        ),
        (
            "us-lg:govinfo:cfr:10-431",
            "govinfo",
            "cfr",
            "GovInfo CFR metadata for energy efficiency part",
            "govinfo.gov",
            "https://www.govinfo.gov/app/details/CFR-2026-title10-vol3/CFR-2026-title10-vol3-part431",
            "2026-06-11",
            "CFR-2026-title10-vol3-part431",
            "certified_government_text",
            ["fixture:us-lg-govinfo-cfr"],
        ),
        (
            "us-lg:congress:bill:hr2600",
            "congress_gov",
            "bill",
            "Congress.gov bill metadata for AI infrastructure act",
            "congress.gov",
            "https://www.congress.gov/bill/119th-congress/house-bill/2600",
            "2026-05-12",
            "H.R.2600-119",
            "official_publication_portal",
            ["fixture:us-lg-congress-bill"],
        ),
        (
            "us-lg:govinfo:plaw:119-1",
            "govinfo",
            "public_law",
            "GovInfo public law metadata",
            "govinfo.gov",
            "https://www.govinfo.gov/app/details/PLAW-119publ1",
            "2026-06-12",
            "PLAW-119publ1",
            "certified_government_text",
            ["fixture:us-lg-govinfo-public-law"],
        ),
        (
            "us-lg:congress:report:hrpt119-1",
            "congress_gov",
            "committee_report",
            "Congress.gov committee report metadata",
            "congress.gov",
            "https://www.congress.gov/congressional-report/119th-congress/house-report/1",
            "2026-05-20",
            "H.Rpt.119-1",
            "official_publication_portal",
            ["fixture:us-lg-congress-report"],
        ),
        (
            "us-lg:govinfo:certified-text:119-1",
            "govinfo",
            "certified_text",
            "GovInfo enrolled bill and certified text metadata",
            "govinfo.gov",
            "https://www.govinfo.gov/app/details/BILLS-119hr2600enr",
            "2026-06-01",
            "BILLS-119hr2600enr",
            "certified_government_text",
            ["fixture:us-lg-govinfo-certified-text"],
        ),
    ]
    return [
        {
            **base,
            "document_id": document_id,
            "source_system": source_system,
            "document_type": document_type,
            "document_title": document_title,
            "official_domain": official_domain,
            "source_url": source_url,
            "published_date": published_date,
            "document_identifier": document_identifier,
            "identity_state": identity_state,
            "evidence_refs": evidence_refs,
        }
        for (
            document_id,
            source_system,
            document_type,
            document_title,
            official_domain,
            source_url,
            published_date,
            document_identifier,
            identity_state,
            evidence_refs,
        ) in rows
    ]


def us_lg_relation_records() -> list[dict]:
    base = {
        "metadata_only": True,
        "production_affected": False,
        "schema_migration_required": False,
        "legal_advice_provided": False,
    }
    rows = [
        (
            "us-lg:relation:docket-fr-proposed",
            "docket_to_fr_document",
            "us-lg:regulations:docket:doe-2026-0001",
            "us-lg:fr:proposed-rule:2026-10001",
            "Regulations.gov docket metadata links to the Federal Register proposed rule metadata.",
            ["fixture:us-lg-relation-docket-fr"],
        ),
        (
            "us-lg:relation:fr-final-cfr",
            "fr_document_to_cfr",
            "us-lg:fr:final-rule:2026-10002",
            "us-lg:govinfo:cfr:10-431",
            "Federal Register final rule metadata links to the corresponding GovInfo CFR metadata.",
            ["fixture:us-lg-relation-fr-cfr"],
        ),
        (
            "us-lg:relation:bill-public-law",
            "bill_to_public_law",
            "us-lg:congress:bill:hr2600",
            "us-lg:govinfo:plaw:119-1",
            "Congress bill metadata links to the resulting GovInfo public law metadata.",
            ["fixture:us-lg-relation-bill-law"],
        ),
        (
            "us-lg:relation:bill-report",
            "bill_to_report",
            "us-lg:congress:bill:hr2600",
            "us-lg:congress:report:hrpt119-1",
            "Congress bill metadata links to the committee report metadata.",
            ["fixture:us-lg-relation-bill-report"],
        ),
        (
            "us-lg:relation:certified-public-law",
            "certified_text_to_public_law",
            "us-lg:govinfo:certified-text:119-1",
            "us-lg:govinfo:plaw:119-1",
            "GovInfo certified text metadata links to the public law metadata without downloading full text.",
            ["fixture:us-lg-relation-certified-law"],
        ),
    ]
    return [
        {
            **base,
            "relation_id": relation_id,
            "relation_type": relation_type,
            "source_document_id": source_document_id,
            "target_document_id": target_document_id,
            "relation_explanation": relation_explanation,
            "evidence_refs": evidence_refs,
        }
        for relation_id, relation_type, source_document_id, target_document_id, relation_explanation, evidence_refs in rows
    ]


def us_lg_legal_backbone_report() -> dict:
    return build_s2pet02_us_lg_legal_backbone_report(
        generated_at=GENERATED_AT,
        us_ta_source_foundation_report=us_ta_source_foundation_report(),
        legal_records=us_lg_legal_records(),
        relation_records=us_lg_relation_records(),
    )


def us_fm_finance_records() -> list[dict]:
    base = {
        "metadata_only": True,
        "pdf_downloaded": False,
        "full_text_extracted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "queue_mutation_allowed": False,
        "schema_migration_required": False,
        "investment_advice_provided": False,
        "trading_signal_generated": False,
        "automated_trading_enabled": False,
        "paid_market_data_used": False,
        "live_source_fetch_executed": False,
    }
    sec_forms = [
        ("8-K", "sec:company:8k", "Current report metadata", "company:0000320193", "company", ["asset:equity:US0378331005"]),
        ("10-K", "sec:company:10k", "Annual report metadata", "company:0000320193", "company", ["asset:equity:US0378331005"]),
        ("10-Q", "sec:company:10q", "Quarterly report metadata", "company:0000320193", "company", ["asset:equity:US0378331005"]),
        ("S-1", "sec:company:s1", "Registration statement metadata", "company:0000789019", "company", ["asset:equity:US5949181045"]),
        ("13D", "sec:ownership:13d", "Beneficial ownership 13D metadata", "company:0000320193", "company", ["asset:equity:US0378331005"]),
        ("13G", "sec:ownership:13g", "Beneficial ownership 13G metadata", "company:0000789019", "company", ["asset:equity:US5949181045"]),
        ("13F", "sec:manager:13f", "Institutional investment manager 13F metadata", "fund:0001067983", "fund", ["asset:equity:US0378331005"]),
        ("FORM-4", "sec:insider:form4", "Insider ownership Form 4 metadata", "company:0000320193", "company", ["asset:equity:US0378331005"]),
        ("N-PORT", "sec:fund:nport", "Registered fund portfolio metadata", "fund:0001000275", "fund", ["asset:fund:series-1", "asset:equity:US0378331005"]),
        ("N-CEN", "sec:fund:ncen", "Registered fund census metadata", "fund:0001000275", "fund", ["asset:fund:class-a"]),
    ]
    records = [
        {
            **base,
            "record_id": record_id,
            "source_system": "sec_edgar",
            "signal_type": "sec_fund_filing" if entity_type == "fund" else "sec_company_filing",
            "record_title": title,
            "official_domain": "sec.gov",
            "source_url": f"https://www.sec.gov/Archives/edgar/data/320193/0000320193-26-{index:06d}-index.html",
            "published_date": f"2026-05-{index:02d}",
            "record_identifier": f"SEC-{form_type}-2026-{index:04d}",
            "form_type": form_type,
            "cik": "0001000275" if entity_type == "fund" else "0000320193",
            "accession_number": f"0000320193-26-{index:06d}",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "related_entity_ids": related,
            "asset_class": "fund" if entity_type == "fund" else "equity",
            "identity_state": "official_publication_portal",
            "evidence_refs": [f"fixture:us-fm-sec-{form_type.lower()}"],
        }
        for index, (form_type, record_id, title, entity_id, entity_type, related) in enumerate(sec_forms, start=1)
    ]
    records.extend(
        [
            {
                **base,
                "record_id": "us-fm:fed:fomc",
                "source_system": "federal_reserve",
                "signal_type": "macro_policy_release",
                "record_title": "Federal Reserve FOMC statement metadata",
                "official_domain": "federalreserve.gov",
                "source_url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260501a.htm",
                "published_date": "2026-05-11",
                "record_identifier": "FED-FOMC-2026-05-01",
                "form_type": "",
                "cik": "",
                "accession_number": "",
                "entity_id": "macro:fed:fomc",
                "entity_type": "macro_release",
                "related_entity_ids": ["asset:rates:fed-funds", "asset:treasury:10y"],
                "asset_class": "rates",
                "identity_state": "official_domain",
                "evidence_refs": ["fixture:us-fm-fed-fomc"],
            },
            {
                **base,
                "record_id": "us-fm:treasury:auction",
                "source_system": "treasury",
                "signal_type": "treasury_market_data",
                "record_title": "Treasury auction metadata",
                "official_domain": "treasury.gov",
                "source_url": "https://home.treasury.gov/news/press-releases/example-auction",
                "published_date": "2026-05-12",
                "record_identifier": "TREAS-AUCTION-2026-05-12",
                "form_type": "",
                "cik": "",
                "accession_number": "",
                "entity_id": "asset:treasury:10y",
                "entity_type": "asset",
                "related_entity_ids": ["macro:fed:fomc"],
                "asset_class": "treasury",
                "identity_state": "official_domain",
                "evidence_refs": ["fixture:us-fm-treasury-auction"],
            },
            {
                **base,
                "record_id": "us-fm:cftc:cot",
                "source_system": "cftc",
                "signal_type": "derivatives_market_data",
                "record_title": "CFTC commitments of traders metadata",
                "official_domain": "cftc.gov",
                "source_url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
                "published_date": "2026-05-13",
                "record_identifier": "CFTC-COT-2026-05-13",
                "form_type": "",
                "cik": "",
                "accession_number": "",
                "entity_id": "asset:commodity:oil-futures",
                "entity_type": "asset",
                "related_entity_ids": ["asset:rates:fed-funds"],
                "asset_class": "derivatives",
                "identity_state": "official_publication_portal",
                "evidence_refs": ["fixture:us-fm-cftc-cot"],
            },
            {
                **base,
                "record_id": "us-fm:occ:bulletin",
                "source_system": "occ",
                "signal_type": "bank_supervision_notice",
                "record_title": "OCC bank supervision bulletin metadata",
                "official_domain": "occ.gov",
                "source_url": "https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-1.html",
                "published_date": "2026-05-14",
                "record_identifier": "OCC-BULLETIN-2026-1",
                "form_type": "",
                "cik": "",
                "accession_number": "",
                "entity_id": "sector:banking",
                "entity_type": "sector",
                "related_entity_ids": ["asset:rates:fed-funds"],
                "asset_class": "banking",
                "identity_state": "official_domain",
                "evidence_refs": ["fixture:us-fm-occ-bulletin"],
            },
            {
                **base,
                "record_id": "us-fm:fdic:notice",
                "source_system": "fdic",
                "signal_type": "deposit_insurance_notice",
                "record_title": "FDIC deposit insurance notice metadata",
                "official_domain": "fdic.gov",
                "source_url": "https://www.fdic.gov/news/financial-institution-letters/2026/fil2601.html",
                "published_date": "2026-05-15",
                "record_identifier": "FDIC-FIL-2026-01",
                "form_type": "",
                "cik": "",
                "accession_number": "",
                "entity_id": "sector:deposit-insurance",
                "entity_type": "sector",
                "related_entity_ids": ["sector:banking"],
                "asset_class": "banking",
                "identity_state": "official_domain",
                "evidence_refs": ["fixture:us-fm-fdic-notice"],
            },
            {
                **base,
                "record_id": "us-fm:cfpb:notice",
                "source_system": "cfpb",
                "signal_type": "consumer_finance_notice",
                "record_title": "CFPB consumer finance notice metadata",
                "official_domain": "consumerfinance.gov",
                "source_url": "https://www.consumerfinance.gov/about-us/newsroom/example-notice/",
                "published_date": "2026-05-16",
                "record_identifier": "CFPB-NOTICE-2026-01",
                "form_type": "",
                "cik": "",
                "accession_number": "",
                "entity_id": "sector:consumer-finance",
                "entity_type": "sector",
                "related_entity_ids": ["sector:banking"],
                "asset_class": "consumer_finance",
                "identity_state": "official_domain",
                "evidence_refs": ["fixture:us-fm-cfpb-notice"],
            },
        ]
    )
    return records


def us_fm_relation_records() -> list[dict]:
    base = {
        "metadata_only": True,
        "production_affected": False,
        "schema_migration_required": False,
        "trading_signal_generated": False,
    }
    rows = [
        ("us-fm:relation:8k-company", "filing_to_company", "sec:company:8k", "company:0000320193", "SEC 8-K metadata links to company CIK entity."),
        ("us-fm:relation:nport-fund", "filing_to_fund", "sec:fund:nport", "fund:0001000275", "SEC N-PORT metadata links to registered fund entity."),
        ("us-fm:relation:13f-asset", "filing_to_asset", "sec:manager:13f", "asset:equity:US0378331005", "SEC 13F metadata links to reported equity asset."),
        ("us-fm:relation:company-cik", "company_to_cik", "sec:company:10k", "company:0000320193", "Company filing metadata preserves CIK entity mapping."),
        ("us-fm:relation:fund-series", "fund_to_series_class", "sec:fund:ncen", "asset:fund:class-a", "Fund N-CEN metadata links to series/class asset entity."),
        ("us-fm:relation:macro-asset", "macro_release_to_asset_class", "us-fm:fed:fomc", "asset:rates:fed-funds", "Federal Reserve macro release metadata links to rate asset class without trading signals."),
    ]
    return [
        {
            **base,
            "relation_id": relation_id,
            "relation_type": relation_type,
            "source_record_id": source_record_id,
            "target_entity_id": target_entity_id,
            "relation_explanation": relation_explanation,
            "evidence_refs": [f"fixture:{relation_id}"],
        }
        for relation_id, relation_type, source_record_id, target_entity_id, relation_explanation in rows
    ]


def us_fm_source_backbone_report() -> dict:
    return build_s2pet03_us_fm_source_backbone_report(
        generated_at=GENERATED_AT,
        us_lg_legal_backbone_report=us_lg_legal_backbone_report(),
        finance_records=us_fm_finance_records(),
        relation_records=us_fm_relation_records(),
    )


def us_tp_policy_records() -> list[dict]:
    base = {
        "metadata_only": True,
        "production_affected": False,
        "public_schema_changed": False,
        "live_source_fetch_executed": False,
        "identity_state": "official_domain",
    }
    rows = [
        (
            "us-tp:ostp:ai-policy",
            "ostp",
            "technology_policy_notice",
            "OSTP AI and advanced technology policy metadata",
            "whitehouse.gov",
            "https://www.whitehouse.gov/ostp/news-updates/example-ai-policy/",
            "2026-05-01",
            "OSTP-TECH-2026-001",
            ["B4", "B6"],
            ["fixture:us-tp-ostp"],
        ),
        (
            "us-tp:bis:export-control",
            "bis",
            "export_control_notice",
            "BIS advanced computing export control notice metadata",
            "bis.gov",
            "https://www.bis.gov/press-release/example-export-control",
            "2026-05-02",
            "BIS-EXPORT-2026-001",
            ["B4", "B5"],
            ["fixture:us-tp-bis"],
        ),
        (
            "us-tp:ftc:competition",
            "ftc",
            "competition_policy_notice",
            "FTC technology competition policy metadata",
            "ftc.gov",
            "https://www.ftc.gov/news-events/news/press-releases/example-tech-competition",
            "2026-05-03",
            "FTC-TECH-2026-001",
            ["B4", "B5"],
            ["fixture:us-tp-ftc"],
        ),
        (
            "us-tp:fcc:spectrum",
            "fcc",
            "spectrum_policy_notice",
            "FCC spectrum policy metadata",
            "fcc.gov",
            "https://www.fcc.gov/document/example-spectrum-policy",
            "2026-05-04",
            "FCC-SPECTRUM-2026-001",
            ["B4"],
            ["fixture:us-tp-fcc"],
        ),
        (
            "us-tp:cisa:cyber",
            "cisa",
            "cybersecurity_advisory",
            "CISA cybersecurity advisory metadata",
            "cisa.gov",
            "https://www.cisa.gov/news-events/alerts/example-cyber-advisory",
            "2026-05-05",
            "CISA-CYBER-2026-001",
            ["B4", "B6"],
            ["fixture:us-tp-cisa"],
        ),
        (
            "us-tp:chips:notice",
            "chips_program",
            "semiconductor_program_notice",
            "CHIPS program semiconductor funding notice metadata",
            "chips.gov",
            "https://www.chips.gov/news/example-funding-notice",
            "2026-05-06",
            "CHIPS-NOTICE-2026-001",
            ["B4", "B6"],
            ["fixture:us-tp-chips"],
        ),
    ]
    return [
        {
            **base,
            "record_id": record_id,
            "source_system": source_system,
            "signal_type": signal_type,
            "record_title": record_title,
            "official_domain": official_domain,
            "source_url": source_url,
            "published_date": published_date,
            "record_identifier": record_identifier,
            "d4_component": "us_tp",
            "board_ids": board_ids,
            "evidence_refs": evidence_refs,
        }
        for (
            record_id,
            source_system,
            signal_type,
            record_title,
            official_domain,
            source_url,
            published_date,
            record_identifier,
            board_ids,
            evidence_refs,
        ) in rows
    ]


def d4_replay_records() -> list[dict]:
    return [
        {
            "as_of_date": f"2026-05-{day:02d}",
            "d4_components": ["us_ta", "us_lg", "us_fm", "us_tp"],
            "status": "pass",
            "route_gate": "pass",
            "budget_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "candidate_count": 4,
            "evidence_refs": [f"fixture:d4-replay-2026-05-{day:02d}"],
        }
        for day in range(1, 31)
    ]


def d4_shadow_records() -> list[dict]:
    return [
        {
            "shadow_date": f"2026-06-{day:02d}",
            "status": "pass",
            "candidate_count": 4,
            "email_preview_gate": "pass",
            "metadata_only": True,
            "real_smtp_sent": False,
            "production_affected": False,
            "evidence_refs": [f"fixture:d4-shadow-2026-06-{day:02d}"],
        }
        for day in (1, 2)
    ]


def d4_board_route_records() -> list[dict]:
    return [
        {
            "board_id": "B4",
            "source_systems": ["ostp", "bis", "fcc", "cisa", "chips_program"],
            "route_explanation": "B4 keeps US official technology policy and innovation signals first.",
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": ["fixture:d4-board-b4"],
        },
        {
            "board_id": "B5",
            "source_systems": ["bis", "ftc"],
            "route_explanation": "B5 captures legal, competition, export-control, and industrial-policy risk context.",
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": ["fixture:d4-board-b5"],
        },
        {
            "board_id": "B6",
            "source_systems": ["ostp", "cisa", "chips_program"],
            "route_explanation": "B6 captures action, capability, and implementation follow-up signals.",
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": ["fixture:d4-board-b6"],
        },
    ]


def d4_budget_records() -> list[dict]:
    rows = [
        ("US-TA", 35, "US-TA keeps the highest share because technology innovation priority must not be diluted."),
        ("US-LG", 15, "US-LG supplies legal backbone context without dominating technology policy."),
        ("US-FM", 30, "US-FM receives a large share for SEC, macro, market, and finance linkage."),
        ("US-TP", 20, "US-TP receives the policy share required for OSTP, BIS, FTC, FCC, CISA, and CHIPS signals."),
    ]
    return [
        {
            "segment": segment,
            "weight": weight,
            "budget_explanation": explanation,
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": [f"fixture:d4-budget-{segment.lower()}"],
        }
        for segment, weight, explanation in rows
    ]


def china_c1_department_source_map_report() -> dict:
    return build_s2pdt02_china_c1_department_source_map_report(
        generated_at=GENERATED_AT,
        c0_source_foundation_report=china_c0_source_foundation_report(),
        department_records=china_c1_department_records(),
    )


def china_legal_records() -> list[dict]:
    base = {
        "identity_state": "official_domain",
        "metadata_only": True,
        "pdf_downloaded": False,
        "full_text_extracted": False,
    }
    return [
        {
            **base,
            "legal_id": "cn-law:data-security-amendment-draft",
            "source_id": "china-c0:npc:committee-report",
            "title": "数据安全法修订草案",
            "legal_status": "draft",
            "version_label": "draft-for-comment",
            "official_domain": "npc.gov.cn",
            "source_url": "https://www.npc.gov.cn/npc/c2/data-security-amendment-draft.html",
            "published_date": "2026-05-01",
            "effective_date": "2026-05-01",
            "evidence_refs": ["fixture:legal-draft"],
        },
        {
            **base,
            "legal_id": "cn-law:data-security-amendment-formal",
            "source_id": "china-c0:law:constitution-amendment",
            "title": "数据安全法修订决定",
            "legal_status": "formal",
            "version_label": "promulgated",
            "official_domain": "npc.gov.cn",
            "source_url": "https://www.npc.gov.cn/npc/c30834/data-security-amendment-formal.html",
            "published_date": "2026-05-08",
            "effective_date": "2026-06-01",
            "evidence_refs": ["fixture:legal-formal"],
        },
        {
            **base,
            "legal_id": "cn-law:industrial-policy-amended",
            "source_id": "china-c1:industry:miit",
            "title": "产业政策管理办法修订条款",
            "legal_status": "amended",
            "version_label": "amended-version",
            "official_domain": "miit.gov.cn",
            "source_url": "https://www.miit.gov.cn/zwgk/zcwj/industrial-policy-amended.html",
            "published_date": "2026-05-10",
            "effective_date": "2026-06-10",
            "evidence_refs": ["fixture:legal-amended"],
        },
        {
            **base,
            "legal_id": "cn-law:legacy-market-rule-repealed",
            "source_id": "china-c1:market:samr",
            "title": "旧市场监管规则废止公告",
            "legal_status": "repealed",
            "version_label": "repealed",
            "official_domain": "samr.gov.cn",
            "source_url": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/legacy-market-rule-repealed.html",
            "published_date": "2026-05-12",
            "effective_date": "2026-05-12",
            "evidence_refs": ["fixture:legal-repealed"],
        },
        {
            **base,
            "legal_id": "cn-law:data-security-implementation-measures",
            "source_id": "china-c1:macro:ndrc",
            "title": "数据安全法实施办法",
            "legal_status": "implemented",
            "version_label": "implementation-measures",
            "official_domain": "ndrc.gov.cn",
            "source_url": "https://www.ndrc.gov.cn/xwdt/tzgg/data-security-implementation-measures.html",
            "published_date": "2026-05-15",
            "effective_date": "2026-07-01",
            "evidence_refs": ["fixture:legal-implemented"],
        },
        {
            **base,
            "legal_id": "cn-law:data-security-judicial-interpretation",
            "source_id": "china-c0:spc-spp:judicial-interpretation",
            "title": "数据安全案件司法解释",
            "legal_status": "interpreted",
            "version_label": "judicial-interpretation",
            "official_domain": "court.gov.cn",
            "source_url": "https://www.court.gov.cn/fabu/xiangqing/data-security-judicial-interpretation.html",
            "published_date": "2026-05-18",
            "effective_date": "2026-06-18",
            "identity_state": "official_publication_portal",
            "evidence_refs": ["fixture:legal-interpreted"],
        },
        {
            **base,
            "legal_id": "cn-law:ndrc-reprint-data-security-amendment",
            "source_id": "china-c1:macro:ndrc",
            "title": "国家发展改革委转载数据安全法修订决定",
            "legal_status": "formal",
            "version_label": "department-reprint",
            "official_domain": "ndrc.gov.cn",
            "source_url": "https://www.ndrc.gov.cn/xwdt/tzgg/reprint-data-security-amendment.html",
            "published_date": "2026-05-20",
            "effective_date": "2026-06-01",
            "evidence_refs": ["fixture:legal-reprint"],
        },
    ]


def china_legal_relation_records() -> list[dict]:
    base = {"metadata_only": True, "evidence_refs": ["fixture:legal-relation"]}
    return [
        {
            **base,
            "relation_id": "rel:draft-to-formal:data-security",
            "relation_type": "draft_to_formal",
            "source_legal_id": "cn-law:data-security-amendment-draft",
            "target_legal_id": "cn-law:data-security-amendment-formal",
            "relation_date": "2026-05-08",
            "forced_update_required": False,
        },
        {
            **base,
            "relation_id": "rel:amends:industrial-policy",
            "relation_type": "amends",
            "source_legal_id": "cn-law:data-security-amendment-formal",
            "target_legal_id": "cn-law:industrial-policy-amended",
            "relation_date": "2026-05-10",
            "forced_update_required": True,
        },
        {
            **base,
            "relation_id": "rel:repeals:legacy-market-rule",
            "relation_type": "repeals",
            "source_legal_id": "cn-law:industrial-policy-amended",
            "target_legal_id": "cn-law:legacy-market-rule-repealed",
            "relation_date": "2026-05-12",
            "forced_update_required": True,
        },
        {
            **base,
            "relation_id": "rel:implements:data-security",
            "relation_type": "implements",
            "source_legal_id": "cn-law:data-security-implementation-measures",
            "target_legal_id": "cn-law:data-security-amendment-formal",
            "relation_date": "2026-05-15",
            "forced_update_required": True,
        },
        {
            **base,
            "relation_id": "rel:interprets:data-security",
            "relation_type": "interprets",
            "source_legal_id": "cn-law:data-security-judicial-interpretation",
            "target_legal_id": "cn-law:data-security-amendment-formal",
            "relation_date": "2026-05-18",
            "forced_update_required": True,
        },
        {
            **base,
            "relation_id": "rel:reprint:ndrc-data-security",
            "relation_type": "reprint_of",
            "source_legal_id": "cn-law:ndrc-reprint-data-security-amendment",
            "target_legal_id": "cn-law:data-security-amendment-formal",
            "relation_date": "2026-05-20",
            "source_role": "reprint",
            "target_role": "original",
            "original_source_verified": True,
            "forced_update_required": False,
        },
    ]


def china_prior_conclusion_records() -> list[dict]:
    return [
        {
            "conclusion_id": "prior:amended-policy",
            "legal_id": "cn-law:industrial-policy-amended",
            "previous_state": "current",
            "updated_state": "requires_revision",
            "update_required": True,
            "rescore_required": True,
            "evidence_refs": ["fixture:prior-amended"],
        },
        {
            "conclusion_id": "prior:repealed-market-rule",
            "legal_id": "cn-law:legacy-market-rule-repealed",
            "previous_state": "current",
            "updated_state": "invalidated",
            "update_required": True,
            "rescore_required": True,
            "evidence_refs": ["fixture:prior-repealed"],
        },
    ]


def china_legal_metadata_relation_report() -> dict:
    return build_s2pdt03_china_legal_metadata_relation_shadow_report(
        generated_at=GENERATED_AT,
        c1_department_source_map_report=china_c1_department_source_map_report(),
        legal_records=china_legal_records(),
        relation_records=china_legal_relation_records(),
        prior_conclusion_records=china_prior_conclusion_records(),
    )


def china_d3_replay_records(start: date = date(2026, 5, 1), count: int = 30) -> list[dict]:
    boards = ("B2_policy", "B3_frontier", "B4_industry", "B5_macro", "B6_risk")
    return [
        {
            "as_of_date": (start + timedelta(days=offset)).isoformat(),
            "source_domain": "d3_china_official",
            "status": "pass",
            "future_leakage_count": 0,
            "p0_p1_blocker_count": 0,
            "authority_gate": "pass",
            "board_route_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "formal_production_inclusion": False,
            "evidence_refs": [f"fixture:d3-replay:{boards[offset % len(boards)]}:{offset + 1:02d}"],
        }
        for offset in range(count)
    ]


def china_d3_shadow_records() -> list[dict]:
    return [
        {
            "shadow_date": "2026-06-23",
            "source_domain": "d3_china_official",
            "status": "pass",
            "shadow_hours": 24,
            "authority_gate": "pass",
            "board_route_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "real_smtp_sent": False,
            "formal_production_inclusion": False,
            "d3_core_source_domain_accepted": False,
            "evidence_refs": ["fixture:d3-shadow:day-1"],
        },
        {
            "shadow_date": "2026-06-24",
            "source_domain": "d3_china_official",
            "status": "pass",
            "shadow_hours": 24,
            "authority_gate": "pass",
            "board_route_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "real_smtp_sent": False,
            "formal_production_inclusion": False,
            "d3_core_source_domain_accepted": False,
            "evidence_refs": ["fixture:d3-shadow:day-2"],
        },
    ]


def china_d3_board_route_records() -> list[dict]:
    return [
        {
            "board_id": "B2_policy",
            "source_ids": ["china-c0:state-council:policy-notice", "china-c1:macro:ndrc"],
            "route_explanation": "National policy notices and C1 policy departments route to the policy board.",
            "authority_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": ["fixture:d3-route:b2"],
        },
        {
            "board_id": "B3_frontier",
            "source_ids": ["china-c1:science:most"],
            "route_explanation": "Science and technology ministry updates route to frontier intelligence.",
            "authority_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": ["fixture:d3-route:b3"],
        },
        {
            "board_id": "B4_industry",
            "source_ids": ["china-c1:industry:miit", "china-c1:key-industry:nea"],
            "route_explanation": "Industry and key-sector official records route to industry intelligence.",
            "authority_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": ["fixture:d3-route:b4"],
        },
        {
            "board_id": "B5_macro",
            "source_ids": ["china-c1:macro:ndrc", "china-c1:finance:pboc"],
            "route_explanation": "Macro and finance official records route to macro-finance reading.",
            "authority_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": ["fixture:d3-route:b5"],
        },
        {
            "board_id": "B6_risk",
            "source_ids": ["china-c1:market:samr", "cn-law:legacy-market-rule-repealed"],
            "route_explanation": "Market regulation, repeal, and legal-change records route to risk review.",
            "authority_gate": "pass",
            "metadata_only": True,
            "production_affected": False,
            "evidence_refs": ["fixture:d3-route:b6"],
        },
    ]


MAINLAND_PROVINCIAL_FIXTURE_ROWS = (
    ("beijing", "北京市", "municipality", "beijing.gov.cn"),
    ("tianjin", "天津市", "municipality", "tj.gov.cn"),
    ("hebei", "河北省", "province", "hebei.gov.cn"),
    ("shanxi", "山西省", "province", "shanxi.gov.cn"),
    ("inner_mongolia", "内蒙古自治区", "autonomous_region", "nmg.gov.cn"),
    ("liaoning", "辽宁省", "province", "ln.gov.cn"),
    ("jilin", "吉林省", "province", "jl.gov.cn"),
    ("heilongjiang", "黑龙江省", "province", "hlj.gov.cn"),
    ("shanghai", "上海市", "municipality", "shanghai.gov.cn"),
    ("jiangsu", "江苏省", "province", "jiangsu.gov.cn"),
    ("zhejiang", "浙江省", "province", "zj.gov.cn"),
    ("anhui", "安徽省", "province", "ah.gov.cn"),
    ("fujian", "福建省", "province", "fujian.gov.cn"),
    ("jiangxi", "江西省", "province", "jiangxi.gov.cn"),
    ("shandong", "山东省", "province", "shandong.gov.cn"),
    ("henan", "河南省", "province", "henan.gov.cn"),
    ("hubei", "湖北省", "province", "hubei.gov.cn"),
    ("hunan", "湖南省", "province", "hunan.gov.cn"),
    ("guangdong", "广东省", "province", "gd.gov.cn"),
    ("guangxi", "广西壮族自治区", "autonomous_region", "gxzf.gov.cn"),
    ("hainan", "海南省", "province", "hainan.gov.cn"),
    ("chongqing", "重庆市", "municipality", "cq.gov.cn"),
    ("sichuan", "四川省", "province", "sc.gov.cn"),
    ("guizhou", "贵州省", "province", "guizhou.gov.cn"),
    ("yunnan", "云南省", "province", "yn.gov.cn"),
    ("tibet", "西藏自治区", "autonomous_region", "xizang.gov.cn"),
    ("shaanxi", "陕西省", "province", "shaanxi.gov.cn"),
    ("gansu", "甘肃省", "province", "gansu.gov.cn"),
    ("qinghai", "青海省", "province", "qinghai.gov.cn"),
    ("ningxia", "宁夏回族自治区", "autonomous_region", "nx.gov.cn"),
    ("xinjiang", "新疆维吾尔自治区", "autonomous_region", "xinjiang.gov.cn"),
)


def china_d3_readiness_report() -> dict:
    return build_s2pdt04_china_d3_readiness_review_report(
        generated_at=GENERATED_AT,
        c0_source_foundation_report=china_c0_source_foundation_report(),
        c1_department_source_map_report=china_c1_department_source_map_report(),
        legal_metadata_relation_report=china_legal_metadata_relation_report(),
        replay_records=china_d3_replay_records(),
        shadow_records=china_d3_shadow_records(),
        board_route_records=china_d3_board_route_records(),
    )


def china_provincial_records() -> list[dict]:
    records: list[dict] = []
    for index, (province_id, province_name, locality_type, domain) in enumerate(MAINLAND_PROVINCIAL_FIXTURE_ROWS):
        records.append(
            {
                "province_id": province_id,
                "province_name": province_name,
                "locality_type": locality_type,
                "official_domain": domain,
                "source_url": f"https://www.{domain}/",
                "core_department_roles": [
                    "government_portal",
                    "development_reform",
                    "science_technology",
                    "industry_information",
                    "finance",
                    "market_regulation",
                ],
                "health_tier": ("green", "yellow", "red")[index % 3],
                "health_explanation": "fixture health tier covers freshness, official identity, and local-department template completeness",
                "authority_gate": "pass",
                "identity_state": "official_domain",
                "metadata_only": True,
                "pdf_downloaded": False,
                "full_text_extracted": False,
                "production_affected": False,
                "real_smtp_sent": False,
                "evidence_refs": [f"fixture:s2pft01:{province_id}"],
            }
        )
    return records


def china_provincial_template_report() -> dict:
    return build_s2pft01_china_provincial_template_coverage_report(
        generated_at=GENERATED_AT,
        d3_readiness_review_report=china_d3_readiness_report(),
        provincial_records=china_provincial_records(),
    )


def hk_mo_jurisdiction_profiles() -> list[dict]:
    return [
        {
            "jurisdiction_id": "hong_kong",
            "jurisdiction_name": "Hong Kong Special Administrative Region",
            "legal_system_state": "common_law",
            "government_structure_model": "special_administrative_region_hksar_government",
            "language_profiles": ["zh_hant", "en"],
            "official_domain": "www.gov.hk",
            "source_url": "https://www.gov.hk/",
            "authority_gate": "pass",
            "template_source": "hk_independent_profile",
            "mainland_template_applied": False,
            "autonomy_basis": "Basic Law and HKSAR government structure",
            "legal_status_reference": "Hong Kong Basic Law",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "evidence_refs": ["fixture:s2pft02:hong_kong"],
        },
        {
            "jurisdiction_id": "macau",
            "jurisdiction_name": "Macao Special Administrative Region",
            "legal_system_state": "civil_law_portuguese_heritage",
            "government_structure_model": "special_administrative_region_macao_government",
            "language_profiles": ["zh_hant", "pt"],
            "official_domain": "www.gov.mo",
            "source_url": "https://www.gov.mo/",
            "authority_gate": "pass",
            "template_source": "macao_independent_profile",
            "mainland_template_applied": False,
            "autonomy_basis": "Basic Law and MSAR government structure",
            "legal_status_reference": "Macao Basic Law",
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "evidence_refs": ["fixture:s2pft02:macau"],
        },
    ]


KEY_CITY_FIXTURE_ROWS = (
    ("beijing", "北京市", "beijing", "national_municipality", "beijing.gov.cn"),
    ("shanghai", "上海市", "shanghai", "national_municipality", "shanghai.gov.cn"),
    ("shenzhen", "深圳市", "guangdong", "pearl_delta", "sz.gov.cn"),
    ("guangzhou", "广州市", "guangdong", "pearl_delta", "gz.gov.cn"),
    ("tianjin", "天津市", "tianjin", "national_municipality", "tj.gov.cn"),
    ("chongqing", "重庆市", "chongqing", "national_municipality", "cq.gov.cn"),
    ("hangzhou", "杭州市", "zhejiang", "yangtze_delta", "hangzhou.gov.cn"),
    ("nanjing", "南京市", "jiangsu", "yangtze_delta", "nanjing.gov.cn"),
    ("suzhou", "苏州市", "jiangsu", "yangtze_delta", "suzhou.gov.cn"),
    ("hefei", "合肥市", "anhui", "yangtze_delta", "hefei.gov.cn"),
    ("wuhan", "武汉市", "hubei", "central", "wuhan.gov.cn"),
    ("xian", "西安市", "shaanxi", "western", "xa.gov.cn"),
    ("chengdu", "成都市", "sichuan", "western", "chengdu.gov.cn"),
    ("changsha", "长沙市", "hunan", "central", "changsha.gov.cn"),
    ("wuxi", "无锡市", "jiangsu", "yangtze_delta", "wuxi.gov.cn"),
    ("dongguan", "东莞市", "guangdong", "pearl_delta", "dg.gov.cn"),
    ("foshan", "佛山市", "guangdong", "pearl_delta", "foshan.gov.cn"),
    ("zhuhai", "珠海市", "guangdong", "pearl_delta", "zhuhai.gov.cn"),
    ("shenyang", "沈阳市", "liaoning", "northeast", "shenyang.gov.cn"),
    ("ningbo", "宁波市", "zhejiang", "coastal", "ningbo.gov.cn"),
    ("qingdao", "青岛市", "shandong", "coastal", "qingdao.gov.cn"),
    ("xiamen", "厦门市", "fujian", "coastal", "xm.gov.cn"),
    ("dalian", "大连市", "liaoning", "coastal", "dl.gov.cn"),
    ("zhengzhou", "郑州市", "henan", "central", "zhengzhou.gov.cn"),
)


def hk_mo_profile_report() -> dict:
    return build_s2pft02_hk_mo_independent_profile_report(
        generated_at=GENERATED_AT,
        provincial_template_coverage_report=china_provincial_template_report(),
        jurisdiction_profiles=hk_mo_jurisdiction_profiles(),
    )


def key_city_records() -> list[dict]:
    records: list[dict] = []
    assert tuple(row[0] for row in KEY_CITY_FIXTURE_ROWS) == S2PFT03_REQUIRED_CITY_IDS
    for index, (city_id, city_name, province_id, region_group, domain) in enumerate(KEY_CITY_FIXTURE_ROWS):
        records.append(
            {
                "city_id": city_id,
                "city_name": city_name,
                "province_id": province_id,
                "region_group": region_group,
                "aliases": [city_name, city_id],
                "department_roles": list(S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES),
                "region_weight": 0.04 + (index % 4) * 0.001,
                "health_tier": ("green", "yellow", "red")[index % 3],
                "health_explanation": "fixture health tier covers official identity, city-department role completeness, and metadata freshness",
                "official_domain": domain,
                "source_url": f"https://www.{domain}/",
                "authority_gate": "pass",
                "metadata_only": True,
                "pdf_downloaded": False,
                "full_text_extracted": False,
                "production_affected": False,
                "real_smtp_sent": False,
                "evidence_refs": [f"fixture:s2pft03:{city_id}"],
            }
        )
    return records


SPECIAL_ZONE_FIXTURE_ROWS = (
    ("xiongan_new_area", "雄安新区", "national_new_area", ("beijing", "tianjin"), "xiongan.gov.cn", ("technology_innovation", "green_development")),
    ("shanghai_pudong_new_area", "上海浦东新区", "national_new_area", ("shanghai",), "pudong.gov.cn", ("finance", "technology_innovation")),
    ("shenzhen_qianhai", "深圳前海深港现代服务业合作区", "cooperation_zone", ("shenzhen",), "qh.sz.gov.cn", ("finance", "cross_border_cooperation")),
    ("hengqin_guangdong_macao", "横琴粤澳深度合作区", "cooperation_zone", ("zhuhai",), "hengqin.gov.cn", ("cross_border_cooperation", "digital_economy")),
    ("hainan_free_trade_port", "海南自由贸易港", "free_trade_port", ("guangzhou",), "hainan.gov.cn", ("free_trade", "industrial_upgrade")),
    ("shanghai_lingang", "上海临港新片区", "new_area_subzone", ("shanghai",), "lingang.gov.cn", ("advanced_manufacturing", "free_trade")),
    ("beijing_zhongguancun", "北京中关村国家自主创新示范区", "innovation_demonstration_zone", ("beijing",), "zgcgw.beijing.gov.cn", ("technology_innovation", "digital_economy")),
    ("suzhou_industrial_park", "苏州工业园区", "industrial_park", ("suzhou",), "sipac.gov.cn", ("advanced_manufacturing", "green_development")),
    ("tianjin_binhai_new_area", "天津滨海新区", "national_new_area", ("tianjin",), "bh.gov.cn", ("advanced_manufacturing", "finance")),
    ("chongqing_liangjiang_new_area", "重庆两江新区", "national_new_area", ("chongqing",), "ljxq.gov.cn", ("industrial_upgrade", "digital_economy")),
)


def key_city_coverage_report() -> dict:
    return build_s2pft03_key_city_coverage_report(
        generated_at=GENERATED_AT,
        hk_mo_profile_report=hk_mo_profile_report(),
        city_records=key_city_records(),
    )


def special_zone_records() -> list[dict]:
    records: list[dict] = []
    assert tuple(row[0] for row in SPECIAL_ZONE_FIXTURE_ROWS) == S2PFT04_REQUIRED_ZONE_IDS
    for index, (zone_id, zone_name, zone_type, parent_city_ids, domain, policy_focus_areas) in enumerate(SPECIAL_ZONE_FIXTURE_ROWS):
        records.append(
            {
                "zone_id": zone_id,
                "zone_name": zone_name,
                "zone_type": zone_type,
                "parent_city_ids": list(parent_city_ids),
                "authority_roles": list(S2PFT04_REQUIRED_ZONE_AUTHORITY_ROLES),
                "policy_focus_areas": list(policy_focus_areas),
                "health_tier": ("green", "yellow", "red")[index % 3],
                "health_explanation": "fixture health tier covers official zone authority, dedupe, parent-city mapping, and metadata freshness",
                "official_domain": domain,
                "source_url": f"https://www.{domain}/",
                "authority_gate": "pass",
                "dedupe_gate": "pass",
                "metadata_only": True,
                "pdf_downloaded": False,
                "full_text_extracted": False,
                "production_affected": False,
                "real_smtp_sent": False,
                "evidence_refs": [f"fixture:s2pft04:{zone_id}"],
            }
        )
    return records


def special_zone_discovery_report() -> dict:
    return build_s2pft04_special_zone_discovery_report(
        generated_at=GENERATED_AT,
        key_city_coverage_report=key_city_coverage_report(),
        zone_records=special_zone_records(),
    )


def d3_full_governance_records(start: date = date(2026, 5, 1), count: int = 30) -> list[dict]:
    replay_dates = [(start + timedelta(days=offset)).isoformat() for offset in range(count)]
    rows = (
        ("c0_core", "C0 national authoritative backbone", "central_authority", "green"),
        ("c1_department", "C1 central department source map", "provincial", "green"),
        ("c2_legal", "C2 legal relation and status guard", "hk_mo", "yellow"),
        ("c3_local", "C3 provincial and key-city local coverage", "key_city", "yellow"),
        ("c4_special_zone", "C4 special-zone vertical governance", "special_zone", "red"),
    )
    assert tuple(row[0] for row in rows) == S2PFT05_REQUIRED_COMPONENTS
    assert tuple(row[2] for row in rows) == S2PFT05_REQUIRED_QUOTA_ROLES
    return [
        {
            "component_id": component_id,
            "component_name": component_name,
            "quota_role": quota_role,
            "quota_gate": "pass",
            "quota_explanation": "fixture quota protects central authority priority while preserving local and special-zone coverage",
            "health_tier": health_tier,
            "health_explanation": "fixture health tier records freshness, official identity, source duplication, and fallback review pressure",
            "elimination_explanation": "low authority, stale, duplicated, or non-official records are excluded before any production consideration",
            "fallback_route": "fallback to C0/C1 authority evidence and manual review when local evidence is weak",
            "fallback_gate": "pass",
            "replay_dates": replay_dates,
            "metadata_only": True,
            "pdf_downloaded": False,
            "full_text_extracted": False,
            "production_affected": False,
            "real_smtp_sent": False,
            "evidence_refs": [f"fixture:s2pft05:{component_id}"],
        }
        for component_id, component_name, quota_role, health_tier in rows
    ]


def d3_full_governance_qualification_report() -> dict:
    return build_s2pft05_d3_full_governance_qualification_report(
        generated_at=GENERATED_AT,
        d3_readiness_review_report=china_d3_readiness_report(),
        provincial_template_coverage_report=china_provincial_template_report(),
        hk_mo_profile_report=hk_mo_profile_report(),
        key_city_coverage_report=key_city_coverage_report(),
        special_zone_discovery_report=special_zone_discovery_report(),
        governance_records=d3_full_governance_records(),
    )


def evidence_packet_domain_reports() -> list[dict]:
    rows = [
        ("d1_research_preprint", "S2PBT01", "ADP-ACC-S2P1T01-SOURCE-PROMOTION", "fixture:d1-preprint-shadow"),
        ("d2_authoritative_publication", "S2PCT07", "ACC-S2PCT07-D2", "fixture:d2-qualification"),
        ("d3_china_official", "S2PFT05", "ACC-S2PFT05-D3-FULL", "fixture:d3-full-governance"),
        ("d4_us_official", "S2PET04", "ACC-S2PET04-D4", "fixture:d4-readiness-contract"),
    ]
    assert tuple(row[0] for row in rows) == S2PGT01_REQUIRED_SOURCE_DOMAINS
    return [
        {
            "source_domain": source_domain,
            "task_id": task_id,
            "acceptance_id": acceptance_id,
            "status": "pass",
            "shadow_evidence_ready": True,
            "source_domain_qualified": True,
            "report_ref": report_ref,
            "production_affected": False,
            "schema_migration_required": False,
        }
        for source_domain, task_id, acceptance_id, report_ref in rows
    ]


def evidence_packet_records() -> list[dict]:
    rows = [
        ("d1_research_preprint", "arxiv", "arxiv.atom.v1", "arxiv:2606.00001", ["metadata", "abstract"], ["B1"]),
        ("d2_authoritative_publication", "rss", "top_journal.rss.v1", "nature:article-1", ["metadata"], ["B2"]),
        ("d3_china_official", "web", "china.official.metadata.v1", "cn.gov:policy-1", ["metadata", "cross_source_verification"], ["B3", "B5"]),
        ("d4_us_official", "web", "us.official.metadata.v1", "us.gov:signal-1", ["metadata", "full_text"], ["B4", "B6"]),
    ]
    return [
        {
            "source_domain": source_domain,
            "evidence_levels_available": levels,
            "board_routes": board_routes,
            "metadata_only": True,
            "schema_migration_required": False,
            "production_affected": False,
            "old_arxiv_compatible": source_domain == "d1_research_preprint",
            "full_text_reference": "metadata-only locator for public official page" if "full_text" in levels else "",
            "cross_source_refs": ["fixture:cross-source"] if "cross_source_verification" in levels else [],
            "source_item": {
                "source_id": source_id,
                "source_type": source_type,
                "source_adapter": adapter,
                "stable_id": source_id,
                "title": f"Fixture {source_domain} record",
                "retrieved_at": GENERATED_AT,
                "canonical_url": f"https://example.test/{source_id}",
                "metadata": {"summary": f"Fixture summary for {source_domain}"},
                "content_refs": [{"content_ref_id": f"content:{source_id}", "kind": "metadata"}],
                "license": "fixture",
            },
            "evidence_claims": [
                {
                    "claim_id": f"claim:{source_id}",
                    "source_id": source_id,
                    "claim_type": "metadata",
                    "priority": "P1",
                    "statement": "Fixture claim used for EvidencePacket V2 compatibility.",
                    "locator": {"stable_url": f"https://example.test/{source_id}"},
                    "support_status": "supported",
                    "extracted_at": GENERATED_AT,
                }
            ],
        }
        for source_domain, source_type, adapter, source_id, levels, board_routes in rows
    ]


def source_board_route_records() -> list[dict]:
    rows = [
        (
            "route:d1:arxiv:2606.00001",
            "d1_research_preprint",
            "arxiv:2606.00001",
            ["B1"],
            ["B4", "B5", "B6"],
            ["scientific_mechanism", "social_impact", "risk_counterevidence", "personal_roi_action"],
            "D1 arXiv research routes to scientific frontier reading with mandatory social, risk, and personal impact checks.",
        ),
        (
            "route:d2:nature:article-1",
            "d2_authoritative_publication",
            "nature:article-1",
            ["B2"],
            ["B4", "B5"],
            ["engineering_relevance", "social_impact", "risk_counterevidence"],
            "D2 authoritative publication routes to engineering and industry interpretation with social and risk checks.",
        ),
        (
            "route:d3:cn.gov:policy-1",
            "d3_china_official",
            "cn.gov:policy-1",
            ["B3"],
            ["B5", "B6"],
            ["policy_capital_context", "risk_counterevidence", "personal_roi_action"],
            "D3 official China policy routes to policy, capital, and geopolitical interpretation with risk and action checks.",
        ),
        (
            "route:d4:us.gov:signal-1",
            "d4_us_official",
            "us.gov:signal-1",
            ["B2", "B3"],
            ["B4", "B6"],
            ["engineering_relevance", "policy_capital_context", "social_impact", "personal_roi_action"],
            "D4 US official signal routes to engineering and policy interpretation with cross-cutting social and personal checks.",
        ),
    ]
    return [
        {
            "route_id": route_id,
            "source_domain": source_domain,
            "source_id": source_id,
            "primary_boards": primary_boards,
            "cross_cutting_boards": cross_cutting_boards,
            "reason_codes": reason_codes,
            "route_explanation": route_explanation,
            "evidence_refs": [f"claim:{source_id}", f"fixture:routing:{source_domain}"],
            "schema_migration_required": False,
            "production_affected": False,
        }
        for route_id, source_domain, source_id, primary_boards, cross_cutting_boards, reason_codes, route_explanation in rows
    ]


def delta_resonance_records() -> list[dict]:
    rows = [
        (
            "delta:d1:new-agent-risk",
            "d1_research_preprint",
            "arxiv:2606.00001",
            "route:d1:arxiv:2606.00001",
            "new_signal",
            "science_engineering",
            "supported",
            0.82,
            "New arXiv agent-risk result strengthens the science-to-engineering frontier signal.",
        ),
        (
            "delta:d2:changed-engineering-evidence",
            "d2_authoritative_publication",
            "nature:article-1",
            "route:d2:nature:article-1",
            "changed_signal",
            "science_engineering",
            "watch",
            0.58,
            "Authoritative publication changes the engineering interpretation but needs follow-up evidence.",
        ),
        (
            "delta:d3:support-policy-capital",
            "d3_china_official",
            "cn.gov:policy-1",
            "route:d3:cn.gov:policy-1",
            "supporting_signal",
            "policy_capital",
            "supported",
            0.74,
            "China official policy supports the policy-capital resonance for AI infrastructure.",
        ),
        (
            "delta:d4:refute-risk",
            "d4_us_official",
            "us.gov:signal-1",
            "route:d4:us.gov:signal-1",
            "refuting_signal",
            "risk_counterevidence",
            "refuted",
            0.66,
            "US official signal refutes an overbroad deployment assumption and must be kept as counterevidence.",
        ),
        (
            "delta:d1:frontier-personal-roi",
            "d1_research_preprint",
            "arxiv:2606.00001",
            "route:d1:arxiv:2606.00001",
            "frontier_shift",
            "personal_roi",
            "mixed",
            0.61,
            "Frontier shift is relevant to personal capability ROI but remains mixed until more evidence arrives.",
        ),
    ]
    return [
        {
            "delta_id": delta_id,
            "source_domain": source_domain,
            "source_id": source_id,
            "route_id": route_id,
            "delta_type": delta_type,
            "resonance_group": resonance_group,
            "support_status": support_status,
            "signal_strength": signal_strength,
            "delta_explanation": delta_explanation,
            "evidence_refs": [f"claim:{source_id}", f"fixture:delta:{delta_type}"],
            "schema_migration_required": False,
            "production_affected": False,
            "email_frontstage_changed": False,
        }
        for (
            delta_id,
            source_domain,
            source_id,
            route_id,
            delta_type,
            resonance_group,
            support_status,
            signal_strength,
            delta_explanation,
        ) in rows
    ]


def queue_candidate_records() -> list[dict]:
    rows = [
        ("candidate:b1:d1:new", "delta:d1:new-agent-risk", "B1", "d1_research_preprint", "arxiv:2606.00001", 91.0, 0),
        ("candidate:b2:d2:changed", "delta:d2:changed-engineering-evidence", "B2", "d2_authoritative_publication", "nature:article-1", 84.0, 2),
        ("candidate:b3:d3:support", "delta:d3:support-policy-capital", "B3", "d3_china_official", "cn.gov:policy-1", 79.0, 5),
        ("candidate:b4:d4:refute", "delta:d4:refute-risk", "B4", "d4_us_official", "us.gov:signal-1", 95.0, 0),
        ("candidate:b5:d1:personal", "delta:d1:frontier-personal-roi", "B5", "d1_research_preprint", "arxiv:2606.00001", 88.0, 10),
        ("candidate:b6:d1:waiting", "delta:d1:new-agent-risk", "B6", "d1_research_preprint", "arxiv:2606.00001", 86.0, 20),
    ]
    return [
        {
            "candidate_id": candidate_id,
            "delta_id": delta_id,
            "board_id": board_id,
            "source_domain": source_domain,
            "source_id": source_id,
            "raw_score": raw_score,
            "waiting_days": waiting_days,
            "candidate_explanation": f"{board_id} calibrated candidate linked to {delta_id}.",
            "evidence_refs": [f"fixture:queue:{candidate_id}", f"delta:{delta_id}"],
            "schema_migration_required": False,
            "public_schema_changed": False,
            "queue_mutation_allowed": False,
            "ranking_algorithm_changed": False,
            "production_affected": False,
            "email_frontstage_changed": False,
        }
        for candidate_id, delta_id, board_id, source_domain, source_id, raw_score, waiting_days in rows
    ]


def knowledge_graph_identity_records() -> list[dict]:
    return [
        {
            "record_id": "identity:arxiv-agent-risk",
            "source_id": "arxiv:2606.00001",
            "source_domain": "d1_research_preprint",
            "title": "Agent benchmark for portfolio risk automation",
            "identifiers": {"arxiv": "2606.00001", "doi": "10.48550/arXiv.2606.00001"},
            "evidence_refs": ["claim:arxiv:2606.00001"],
            "schema_migration_required": False,
            "production_affected": False,
        },
        {
            "record_id": "identity:pubmed-agent-risk",
            "source_id": "pubmed:39200001",
            "source_domain": "d2_authoritative_publication",
            "title": "Agent benchmark for portfolio risk automation",
            "identifiers": {"doi": "https://doi.org/10.48550/arxiv.2606.00001", "pmid": "39200001"},
            "evidence_refs": ["claim:pubmed:39200001"],
            "schema_migration_required": False,
            "production_affected": False,
        },
        {
            "record_id": "identity:cn-policy-ai",
            "source_id": "cn.gov:policy-1",
            "source_domain": "d3_china_official",
            "title": "人工智能产业政策通知",
            "identifiers": {"cn_document_number": "工信部科〔2026〕42号"},
            "evidence_refs": ["claim:cn:policy-1"],
            "schema_migration_required": False,
            "production_affected": False,
        },
        {
            "record_id": "identity:fr-ai-rule",
            "source_id": "fr:2026-12345",
            "source_domain": "d4_us_official",
            "title": "Federal Register AI disclosure rule",
            "identifiers": {"federal_register_document_number": "2026-12345", "cik": "0000320193"},
            "evidence_refs": ["claim:fr:2026-12345"],
            "schema_migration_required": False,
            "production_affected": False,
        },
    ]


def knowledge_graph_relation_records() -> list[dict]:
    return [
        {
            "relation_type": "same_as",
            "source_identifier": {"type": "arxiv", "value": "2606.00001"},
            "target_identifier": {"type": "pmid", "value": "39200001"},
            "evidence_refs": ["claim:doi-crosswalk:2606.00001"],
            "locator_refs": ["doi:10.48550/arxiv.2606.00001"],
            "support_status": "supported",
            "schema_migration_required": False,
            "production_affected": False,
        },
        {
            "relation_type": "references",
            "source_identifier": {"type": "cn_document_number", "value": "工信部科〔2026〕42号"},
            "target_identifier": {"type": "federal_register_document_number", "value": "2026-12345"},
            "evidence_refs": ["claim:cn-fr-cross-source"],
            "locator_refs": ["section:cross-source-policy-note"],
            "support_status": "cross_source_verified",
            "schema_migration_required": False,
            "production_affected": False,
        },
        {
            "relation_type": "implements",
            "source_identifier": {"type": "federal_register_document_number", "value": "2026-12345"},
            "target_identifier": {"type": "cik", "value": "0000320193"},
            "evidence_refs": ["claim:fr-cik-implementation"],
            "locator_refs": ["agency:SEC"],
            "support_status": "supported",
            "schema_migration_required": False,
            "production_affected": False,
        },
    ]


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

    def test_s2pct07_d2_qualification_calibrates_domains_without_accepting_production(self) -> None:
        report = build_s2pct07_d2_source_domain_qualification_report(
            generated_at=GENERATED_AT,
            profile_report=top_journal_profile_report(),
            engineering_signal_report=engineering_signal_report(),
            authoritative_report=authoritative_report(),
            replay_records=d2_replay_records(),
            shadow_records=d2_shadow_records(),
            forced_event_records=d2_forced_event_records(),
            queue_explanation_records=d2_queue_explanation_records(),
        )

        self.assertEqual(report["model_id"], S2PCT07_D2_QUALIFICATION_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PCT07-D2")
        self.assertEqual(report["task_id"], "S2PCT07")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d2_source_domain_qualification_ready"])
        self.assertEqual(report["upstream_gate"], "pass")
        self.assertEqual(report["domain_coverage_gate"], "pass")
        self.assertEqual(report["replay_gate"], "pass")
        self.assertEqual(report["shadow_gate"], "pass")
        self.assertEqual(report["forced_event_gate"], "pass")
        self.assertEqual(report["queue_explanation_gate"], "pass")
        self.assertEqual(report["type_calibration_gate"], "pass")
        self.assertFalse(report["d2_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["smtp_transport_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(validate_s2pct07_d2_source_domain_qualification_report(report))

    def test_s2pct07_d2_qualification_blocks_short_replay_and_missing_queue_explanation(self) -> None:
        queue_records = d2_queue_explanation_records()
        queue_records[-1] = dict(queue_records[-1], explanation="")

        report = build_s2pct07_d2_source_domain_qualification_report(
            generated_at=GENERATED_AT,
            profile_report=top_journal_profile_report(),
            engineering_signal_report=engineering_signal_report(),
            authoritative_report=authoritative_report(),
            replay_records=d2_replay_records(count=29),
            shadow_records=d2_shadow_records(),
            forced_event_records=d2_forced_event_records(),
            queue_explanation_records=queue_records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["replay_gate"], "blocked")
        self.assertEqual(report["queue_explanation_gate"], "blocked")
        self.assertFalse(report["d2_source_domain_accepted"])
        self.assertIn("30 unique dates", " ".join(report["blocking_reasons"]))
        self.assertIn("queue explanation records require", " ".join(report["blocking_reasons"]))

    def test_s2pct07_d2_qualification_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pct07_d2_source_domain_qualification(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                profile_report=top_journal_profile_report(),
                engineering_signal_report=engineering_signal_report(),
                authoritative_report=authoritative_report(),
                replay_records=d2_replay_records(),
                shadow_records=d2_shadow_records(),
                forced_event_records=d2_forced_event_records(),
                queue_explanation_records=d2_queue_explanation_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pct07_d2_source_domain_qualification_report(report))
            self.assertFalse(report["d2_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertTrue(Path(report["qualification_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pct07_d2_source_domain_qualification_report.json").is_file())

    def test_s2pdt01_china_c0_source_foundation_validates_authority_traceability_without_production(self) -> None:
        report = build_s2pdt01_china_c0_source_foundation_report(
            generated_at=GENERATED_AT,
            d2_qualification_report=d2_qualification_report(),
            authority_records=china_c0_authority_records(),
        )

        self.assertEqual(report["model_id"], S2PDT01_CHINA_C0_SOURCE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PDT01-C0")
        self.assertEqual(report["task_id"], "S2PDT01")
        self.assertEqual(report["legacy_task_id"], "S2P3T01")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d3_c0_source_foundation_ready"])
        self.assertEqual(report["upstream_d2_qualification_gate"], "pass")
        self.assertEqual(report["authority_taxonomy_gate"], "pass")
        self.assertEqual(report["official_identity_gate"], "pass")
        self.assertEqual(report["document_traceability_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertTrue(set(report["required_authority_types"]).issubset(set(report["authority_types_observed"])))
        self.assertEqual(report["authority_record_count"], 5)
        self.assertFalse(report["d3_core_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["bulk_scraping_allowed"])
        self.assertFalse(report["pdf_download_enabled"])
        self.assertFalse(report["full_text_download_enabled"])
        self.assertFalse(validate_s2pdt01_china_c0_source_foundation_report(report))

    def test_s2pdt01_china_c0_source_foundation_blocks_unofficial_missing_trace_and_pdf_download(self) -> None:
        records = china_c0_authority_records()
        records[0] = dict(
            records[0],
            source_url="https://mirror.example.com/law.html",
            document_number="",
            identity_state="mirror",
            pdf_downloaded=True,
        )

        report = build_s2pdt01_china_c0_source_foundation_report(
            generated_at=GENERATED_AT,
            d2_qualification_report=d2_qualification_report(),
            authority_records=records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["official_identity_gate"], "blocked")
        self.assertEqual(report["document_traceability_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["d3_core_source_domain_accepted"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("source_url must contain official_domain", joined)
        self.assertIn("traceability requires", joined)
        self.assertIn("metadata-only", joined)

    def test_s2pdt01_china_c0_source_foundation_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pdt01_china_c0_source_foundation(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                d2_qualification_report=d2_qualification_report(),
                authority_records=china_c0_authority_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pdt01_china_c0_source_foundation_report(report))
            self.assertFalse(report["d3_core_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["source_foundation_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pdt01_china_c0_source_foundation_report.json").is_file())

    def test_s2pet01_us_ta_source_foundation_validates_official_agency_trace_without_production(self) -> None:
        report = build_s2pet01_us_ta_source_foundation_report(
            generated_at=GENERATED_AT,
            agency_records=us_ta_agency_records(),
        )

        self.assertEqual(report["model_id"], S2PET01_US_TA_SOURCE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PET01-US-TA")
        self.assertEqual(report["task_id"], "S2PET01")
        self.assertEqual(report["legacy_task_id"], "S2P4T01")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d4_us_ta_source_foundation_ready"])
        self.assertEqual(report["agency_coverage_gate"], "pass")
        self.assertEqual(report["signal_type_gate"], "pass")
        self.assertEqual(report["official_identity_gate"], "pass")
        self.assertEqual(report["document_traceability_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertEqual(report["agency_record_count"], 8)
        self.assertTrue(set(report["required_agencies"]).issubset(set(report["agencies_observed"])))
        self.assertTrue(set(report["required_signal_types"]).issubset(set(report["signal_types_observed"])))
        self.assertFalse(report["d4_us_official_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["v7_2_contract_files_modified"])
        self.assertFalse(validate_s2pet01_us_ta_source_foundation_report(report))

    def test_s2pet01_us_ta_source_foundation_blocks_unofficial_missing_trace_and_side_effects(self) -> None:
        records = us_ta_agency_records()
        records[0] = dict(
            records[0],
            source_url="https://mirror.example.com/nsf-award",
            published_date="",
            identity_state="mirror",
            pdf_downloaded=True,
            production_affected=True,
        )

        report = build_s2pet01_us_ta_source_foundation_report(
            generated_at=GENERATED_AT,
            agency_records=records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["official_identity_gate"], "blocked")
        self.assertEqual(report["document_traceability_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["d4_us_official_source_domain_accepted"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("source_url must contain official_domain", joined)
        self.assertIn("traceability requires", joined)
        self.assertIn("metadata-only", joined)

    def test_s2pet01_us_ta_source_foundation_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pet01_us_ta_source_foundation(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                agency_records=us_ta_agency_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pet01_us_ta_source_foundation_report(report))
            self.assertFalse(report["d4_us_official_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["source_foundation_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pet01_us_ta_source_foundation_report.json").is_file())

    def test_s2pet02_us_lg_legal_backbone_validates_relations_without_production(self) -> None:
        report = build_s2pet02_us_lg_legal_backbone_report(
            generated_at=GENERATED_AT,
            us_ta_source_foundation_report=us_ta_source_foundation_report(),
            legal_records=us_lg_legal_records(),
            relation_records=us_lg_relation_records(),
        )

        self.assertEqual(report["model_id"], S2PET02_US_LG_BACKBONE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PET02-US-LG")
        self.assertEqual(report["task_id"], "S2PET02")
        self.assertEqual(report["legacy_task_id"], "S2P4T02")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d4_us_lg_legal_backbone_ready"])
        self.assertEqual(report["upstream_us_ta_source_foundation_gate"], "pass")
        self.assertEqual(report["source_system_coverage_gate"], "pass")
        self.assertEqual(report["document_type_gate"], "pass")
        self.assertEqual(report["official_identity_gate"], "pass")
        self.assertEqual(report["document_traceability_gate"], "pass")
        self.assertEqual(report["legal_relation_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertTrue(set(report["required_source_systems"]).issubset(set(report["source_systems_observed"])))
        self.assertTrue(set(report["required_document_types"]).issubset(set(report["document_types_observed"])))
        self.assertTrue(set(report["required_relation_types"]).issubset(set(report["relation_types_observed"])))
        self.assertFalse(report["d4_us_official_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["legal_advice_provided"])
        self.assertFalse(report["live_source_fetch_executed"])
        self.assertFalse(report["v7_2_contract_files_modified"])
        self.assertFalse(validate_s2pet02_us_lg_legal_backbone_report(report))

    def test_s2pet02_us_lg_legal_backbone_blocks_unofficial_missing_relation_and_side_effects(self) -> None:
        records = us_lg_legal_records()
        records[0] = dict(
            records[0],
            source_url="https://mirror.example.com/docket",
            published_date="",
            identity_state="mirror",
            pdf_downloaded=True,
            legal_advice_provided=True,
            production_affected=True,
        )
        relations = us_lg_relation_records()
        relations[0] = dict(relations[0], target_document_id="missing:fr-doc", evidence_refs=[])

        report = build_s2pet02_us_lg_legal_backbone_report(
            generated_at=GENERATED_AT,
            us_ta_source_foundation_report=us_ta_source_foundation_report(),
            legal_records=records,
            relation_records=relations,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["official_identity_gate"], "blocked")
        self.assertEqual(report["document_traceability_gate"], "blocked")
        self.assertEqual(report["legal_relation_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["d4_us_lg_legal_backbone_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("source_url must contain official_domain", joined)
        self.assertIn("traceability requires", joined)
        self.assertIn("relations require", joined)
        self.assertIn("metadata-only", joined)

    def test_s2pet02_us_lg_legal_backbone_requires_passing_s2pet01_upstream(self) -> None:
        upstream = dict(us_ta_source_foundation_report(), status="blocked", d4_us_ta_source_foundation_ready=False)

        report = build_s2pet02_us_lg_legal_backbone_report(
            generated_at=GENERATED_AT,
            us_ta_source_foundation_report=upstream,
            legal_records=us_lg_legal_records(),
            relation_records=us_lg_relation_records(),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["upstream_us_ta_source_foundation_gate"], "blocked")
        self.assertFalse(report["d4_us_lg_legal_backbone_ready"])
        self.assertIn("upstream S2PET01 report must pass", " ".join(report["blocking_reasons"]))

    def test_s2pet02_us_lg_legal_backbone_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pet02_us_lg_legal_backbone(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                us_ta_source_foundation_report=us_ta_source_foundation_report(),
                legal_records=us_lg_legal_records(),
                relation_records=us_lg_relation_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pet02_us_lg_legal_backbone_report(report))
            self.assertFalse(report["d4_us_official_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["legal_backbone_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pet02_us_lg_legal_backbone_report.json").is_file())

    def test_s2pet03_us_fm_source_backbone_validates_forms_and_relations_without_production(self) -> None:
        report = build_s2pet03_us_fm_source_backbone_report(
            generated_at=GENERATED_AT,
            us_lg_legal_backbone_report=us_lg_legal_backbone_report(),
            finance_records=us_fm_finance_records(),
            relation_records=us_fm_relation_records(),
        )

        self.assertEqual(report["model_id"], S2PET03_US_FM_BACKBONE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PET03-US-FM")
        self.assertEqual(report["task_id"], "S2PET03")
        self.assertEqual(report["legacy_task_id"], "S2P4T03")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d4_us_fm_source_backbone_ready"])
        self.assertEqual(report["upstream_us_lg_legal_backbone_gate"], "pass")
        self.assertEqual(report["source_system_coverage_gate"], "pass")
        self.assertEqual(report["signal_type_gate"], "pass")
        self.assertEqual(report["sec_form_coverage_gate"], "pass")
        self.assertEqual(report["identifier_gate"], "pass")
        self.assertEqual(report["official_identity_gate"], "pass")
        self.assertEqual(report["document_traceability_gate"], "pass")
        self.assertEqual(report["finance_relation_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertTrue(set(report["required_source_systems"]).issubset(set(report["source_systems_observed"])))
        self.assertTrue(set(report["required_sec_form_types"]).issubset(set(report["sec_form_types_observed"])))
        self.assertTrue(set(report["required_relation_types"]).issubset(set(report["relation_types_observed"])))
        self.assertFalse(report["d4_us_official_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["investment_advice_provided"])
        self.assertFalse(report["trading_signal_generated"])
        self.assertFalse(report["automated_trading_enabled"])
        self.assertFalse(report["paid_market_data_used"])
        self.assertFalse(report["v7_2_contract_files_modified"])
        self.assertFalse(validate_s2pet03_us_fm_source_backbone_report(report))

    def test_s2pet03_us_fm_source_backbone_blocks_missing_identifier_relation_and_trading_side_effects(self) -> None:
        records = us_fm_finance_records()
        records[0] = dict(
            records[0],
            source_url="https://mirror.example.com/sec-8k",
            cik="",
            accession_number="",
            identity_state="mirror",
            paid_market_data_used=True,
            trading_signal_generated=True,
            investment_advice_provided=True,
            production_affected=True,
        )
        relations = us_fm_relation_records()
        relations[0] = dict(relations[0], target_entity_id="missing:company", evidence_refs=[])

        report = build_s2pet03_us_fm_source_backbone_report(
            generated_at=GENERATED_AT,
            us_lg_legal_backbone_report=us_lg_legal_backbone_report(),
            finance_records=records,
            relation_records=relations,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["identifier_gate"], "blocked")
        self.assertEqual(report["official_identity_gate"], "blocked")
        self.assertEqual(report["finance_relation_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["d4_us_fm_source_backbone_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("source_url must contain official_domain", joined)
        self.assertIn("CIK, Accession", joined)
        self.assertIn("relations require", joined)
        self.assertIn("trading", joined)

    def test_s2pet03_us_fm_source_backbone_requires_passing_s2pet02_upstream(self) -> None:
        upstream = dict(us_lg_legal_backbone_report(), status="blocked", d4_us_lg_legal_backbone_ready=False)

        report = build_s2pet03_us_fm_source_backbone_report(
            generated_at=GENERATED_AT,
            us_lg_legal_backbone_report=upstream,
            finance_records=us_fm_finance_records(),
            relation_records=us_fm_relation_records(),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["upstream_us_lg_legal_backbone_gate"], "blocked")
        self.assertFalse(report["d4_us_fm_source_backbone_ready"])
        self.assertIn("upstream S2PET02 report must pass", " ".join(report["blocking_reasons"]))

    def test_s2pet03_us_fm_source_backbone_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pet03_us_fm_source_backbone(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                us_lg_legal_backbone_report=us_lg_legal_backbone_report(),
                finance_records=us_fm_finance_records(),
                relation_records=us_fm_relation_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pet03_us_fm_source_backbone_report(report))
            self.assertFalse(report["d4_us_official_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertFalse(report["automated_trading_enabled"])
            self.assertTrue(Path(report["finance_backbone_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pet03_us_fm_source_backbone_report.json").is_file())

    def test_s2pet04_us_tp_d4_qualification_validates_replay_shadow_routing_budget_without_production(self) -> None:
        report = build_s2pet04_us_tp_d4_qualification_report(
            generated_at=GENERATED_AT,
            us_ta_source_foundation_report=us_ta_source_foundation_report(),
            us_lg_legal_backbone_report=us_lg_legal_backbone_report(),
            us_fm_source_backbone_report=us_fm_source_backbone_report(),
            policy_records=us_tp_policy_records(),
            replay_records=d4_replay_records(),
            shadow_records=d4_shadow_records(),
            board_route_records=d4_board_route_records(),
            budget_records=d4_budget_records(),
        )

        self.assertEqual(report["model_id"], S2PET04_US_TP_D4_QUALIFICATION_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PET04-D4")
        self.assertEqual(report["task_id"], "S2PET04")
        self.assertEqual(report["legacy_task_id"], "S2P4T04")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d4_us_tp_and_qualification_ready"])
        self.assertEqual(report["upstream_s2pet01_s2pet03_gate"], "pass")
        self.assertEqual(report["us_tp_source_system_gate"], "pass")
        self.assertEqual(report["us_tp_signal_type_gate"], "pass")
        self.assertEqual(report["official_identity_gate"], "pass")
        self.assertEqual(report["d4_replay_gate"], "pass")
        self.assertEqual(report["d4_shadow_gate"], "pass")
        self.assertEqual(report["board_routing_gate"], "pass")
        self.assertEqual(report["budget_explanation_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertEqual(len(report["replay_dates_observed"]), 30)
        self.assertEqual(len(report["shadow_dates_observed"]), 2)
        self.assertEqual(report["budget_weight_total"], 100)
        self.assertTrue(set(report["required_source_systems"]).issubset(set(report["source_systems_observed"])))
        self.assertTrue(set(report["required_board_ids"]).issubset(set(report["board_ids_observed"])))
        self.assertFalse(report["d4_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["v7_2_contract_files_modified"])
        self.assertFalse(validate_s2pet04_us_tp_d4_qualification_report(report))

    def test_s2pet04_us_tp_d4_qualification_blocks_unofficial_budget_and_shadow_side_effects(self) -> None:
        policy_records = us_tp_policy_records()
        policy_records[0] = dict(
            policy_records[0],
            source_url="https://mirror.example.com/ostp",
            identity_state="mirror",
            production_affected=True,
        )
        replay_records = d4_replay_records()[:29]
        shadow_records = d4_shadow_records()
        shadow_records[0] = dict(shadow_records[0], real_smtp_sent=True, production_affected=True)
        board_records = d4_board_route_records()[:2]
        budget_records = d4_budget_records()
        budget_records[0] = dict(budget_records[0], weight=34)

        report = build_s2pet04_us_tp_d4_qualification_report(
            generated_at=GENERATED_AT,
            us_ta_source_foundation_report=us_ta_source_foundation_report(),
            us_lg_legal_backbone_report=us_lg_legal_backbone_report(),
            us_fm_source_backbone_report=us_fm_source_backbone_report(),
            policy_records=policy_records,
            replay_records=replay_records,
            shadow_records=shadow_records,
            board_route_records=board_records,
            budget_records=budget_records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["official_identity_gate"], "blocked")
        self.assertEqual(report["d4_replay_gate"], "blocked")
        self.assertEqual(report["d4_shadow_gate"], "blocked")
        self.assertEqual(report["board_routing_gate"], "blocked")
        self.assertEqual(report["budget_explanation_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["d4_us_tp_and_qualification_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("source_url must contain official_domain", joined)
        self.assertIn("30 dates", joined)
        self.assertIn("shadow rows require", joined)
        self.assertIn("budget weights", joined)
        self.assertIn("metadata-only", joined)

    def test_s2pet04_us_tp_d4_qualification_requires_s2pet01_to_s2pet03_upstream(self) -> None:
        upstream = dict(us_fm_source_backbone_report(), status="blocked", d4_us_fm_source_backbone_ready=False)

        report = build_s2pet04_us_tp_d4_qualification_report(
            generated_at=GENERATED_AT,
            us_ta_source_foundation_report=us_ta_source_foundation_report(),
            us_lg_legal_backbone_report=us_lg_legal_backbone_report(),
            us_fm_source_backbone_report=upstream,
            policy_records=us_tp_policy_records(),
            replay_records=d4_replay_records(),
            shadow_records=d4_shadow_records(),
            board_route_records=d4_board_route_records(),
            budget_records=d4_budget_records(),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["upstream_s2pet01_s2pet03_gate"], "blocked")
        self.assertFalse(report["d4_us_tp_and_qualification_ready"])
        self.assertIn("upstream S2PET01-S2PET03 reports must pass", " ".join(report["blocking_reasons"]))

    def test_s2pet04_us_tp_d4_qualification_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pet04_us_tp_d4_qualification(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                us_ta_source_foundation_report=us_ta_source_foundation_report(),
                us_lg_legal_backbone_report=us_lg_legal_backbone_report(),
                us_fm_source_backbone_report=us_fm_source_backbone_report(),
                policy_records=us_tp_policy_records(),
                replay_records=d4_replay_records(),
                shadow_records=d4_shadow_records(),
                board_route_records=d4_board_route_records(),
                budget_records=d4_budget_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pet04_us_tp_d4_qualification_report(report))
            self.assertFalse(report["d4_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["d4_qualification_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pet04_us_tp_d4_qualification_report.json").is_file())

    def test_s2pdt02_china_c1_department_source_map_validates_alias_routes_without_production(self) -> None:
        report = build_s2pdt02_china_c1_department_source_map_report(
            generated_at=GENERATED_AT,
            c0_source_foundation_report=china_c0_source_foundation_report(),
            department_records=china_c1_department_records(),
        )

        self.assertEqual(report["model_id"], S2PDT02_CHINA_C1_SOURCE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PDT02-C1")
        self.assertEqual(report["task_id"], "S2PDT02")
        self.assertEqual(report["legacy_task_id"], "S2P3T02")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d3_c1_department_source_map_ready"])
        self.assertEqual(report["upstream_c0_source_foundation_gate"], "pass")
        self.assertEqual(report["sector_coverage_gate"], "pass")
        self.assertEqual(report["official_identity_gate"], "pass")
        self.assertEqual(report["alias_gate"], "pass")
        self.assertEqual(report["industry_route_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertTrue(set(report["required_sectors"]).issubset(set(report["sectors_observed"])))
        self.assertEqual(report["department_record_count"], 6)
        self.assertFalse(report["d3_core_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["bulk_scraping_allowed"])
        self.assertFalse(report["pdf_download_enabled"])
        self.assertFalse(report["full_text_download_enabled"])
        self.assertFalse(validate_s2pdt02_china_c1_department_source_map_report(report))

    def test_s2pdt02_china_c1_department_source_map_blocks_unofficial_missing_alias_and_route(self) -> None:
        records = china_c1_department_records()
        records[0] = dict(
            records[0],
            source_url="https://mirror.example.com/ndrc.html",
            aliases=[],
            industry_routes=[],
            pdf_downloaded=True,
        )

        report = build_s2pdt02_china_c1_department_source_map_report(
            generated_at=GENERATED_AT,
            c0_source_foundation_report=china_c0_source_foundation_report(),
            department_records=records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["alias_gate"], "blocked")
        self.assertEqual(report["industry_route_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["d3_core_source_domain_accepted"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("source_url must contain official_domain", joined)
        self.assertIn("alias map", joined)
        self.assertIn("route map", joined)
        self.assertIn("metadata-only", joined)

    def test_s2pdt02_china_c1_department_source_map_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pdt02_china_c1_department_source_map(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                c0_source_foundation_report=china_c0_source_foundation_report(),
                department_records=china_c1_department_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pdt02_china_c1_department_source_map_report(report))
            self.assertFalse(report["d3_core_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["department_source_map_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pdt02_china_c1_department_source_map_report.json").is_file())

    def test_s2pdt03_china_legal_metadata_relation_validates_status_effectivity_reprint_and_updates_without_production(self) -> None:
        report = build_s2pdt03_china_legal_metadata_relation_shadow_report(
            generated_at=GENERATED_AT,
            c1_department_source_map_report=china_c1_department_source_map_report(),
            legal_records=china_legal_records(),
            relation_records=china_legal_relation_records(),
            prior_conclusion_records=china_prior_conclusion_records(),
        )

        self.assertEqual(report["model_id"], S2PDT03_LEGAL_METADATA_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PDT03-LEGAL")
        self.assertEqual(report["task_id"], "S2PDT03")
        self.assertEqual(report["legacy_task_id"], "S2P3T03")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d3_legal_metadata_relation_shadow_ready"])
        self.assertEqual(report["upstream_c1_department_source_map_gate"], "pass")
        self.assertEqual(report["legal_status_taxonomy_gate"], "pass")
        self.assertEqual(report["version_effectivity_gate"], "pass")
        self.assertEqual(report["reprint_relation_gate"], "pass")
        self.assertEqual(report["forced_update_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertTrue(set(report["required_legal_statuses"]).issubset(set(report["legal_statuses_observed"])))
        self.assertTrue(set(report["required_relation_types"]).issubset(set(report["relation_types_observed"])))
        self.assertEqual(report["legal_record_count"], 7)
        self.assertEqual(report["relation_record_count"], 6)
        self.assertFalse(report["legal_advice_provided"])
        self.assertFalse(report["v7_1_current_switched"])
        self.assertFalse(report["v7_2_mail_or_schema_prerun"])
        self.assertFalse(report["d3_core_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["bulk_scraping_allowed"])
        self.assertFalse(report["pdf_download_enabled"])
        self.assertFalse(report["full_text_download_enabled"])
        self.assertFalse(validate_s2pdt03_china_legal_metadata_relation_shadow_report(report))

    def test_s2pdt03_china_legal_metadata_relation_blocks_unknown_status_date_confusion_bad_reprint_and_missing_update(self) -> None:
        legal_records = china_legal_records()
        legal_records[0] = dict(legal_records[0], legal_status="unknown_status", effective_date="2026/05/01")
        relation_records = china_legal_relation_records()
        relation_records[-1] = dict(
            relation_records[-1],
            source_role="original",
            target_role="reprint",
            original_source_verified=False,
        )
        prior_conclusions = [
            dict(record, update_required=False, rescore_required=False, updated_state="")
            for record in china_prior_conclusion_records()
        ]

        report = build_s2pdt03_china_legal_metadata_relation_shadow_report(
            generated_at=GENERATED_AT,
            c1_department_source_map_report=china_c1_department_source_map_report(),
            legal_records=legal_records,
            relation_records=relation_records,
            prior_conclusion_records=prior_conclusions,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["legal_status_taxonomy_gate"], "blocked")
        self.assertEqual(report["version_effectivity_gate"], "blocked")
        self.assertEqual(report["reprint_relation_gate"], "blocked")
        self.assertEqual(report["forced_update_gate"], "blocked")
        self.assertFalse(report["d3_core_source_domain_accepted"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("unsupported statuses", joined)
        self.assertIn("date confusion", joined)
        self.assertIn("reprint relation guard", joined)
        self.assertIn("old conclusion update", joined)

    def test_s2pdt03_china_legal_metadata_relation_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pdt03_china_legal_metadata_relation_shadow(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                c1_department_source_map_report=china_c1_department_source_map_report(),
                legal_records=china_legal_records(),
                relation_records=china_legal_relation_records(),
                prior_conclusion_records=china_prior_conclusion_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pdt03_china_legal_metadata_relation_shadow_report(report))
            self.assertFalse(report["d3_core_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["legal_metadata_relation_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pdt03_china_legal_metadata_relation_shadow_report.json").is_file())

    def test_s2pdt04_china_d3_readiness_validates_replay_shadow_routes_without_production(self) -> None:
        report = build_s2pdt04_china_d3_readiness_review_report(
            generated_at=GENERATED_AT,
            c0_source_foundation_report=china_c0_source_foundation_report(),
            c1_department_source_map_report=china_c1_department_source_map_report(),
            legal_metadata_relation_report=china_legal_metadata_relation_report(),
            replay_records=china_d3_replay_records(),
            shadow_records=china_d3_shadow_records(),
            board_route_records=china_d3_board_route_records(),
        )

        self.assertEqual(report["model_id"], S2PDT04_D3_READINESS_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PDT04-D3-CORE")
        self.assertEqual(report["task_id"], "S2PDT04")
        self.assertEqual(report["legacy_task_id"], "S2P3T04")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["d3_core_readiness_review_ready"])
        self.assertEqual(report["upstream_source_evidence_gate"], "pass")
        self.assertEqual(report["d3_replay_gate"], "pass")
        self.assertEqual(report["d3_shadow_gate"], "pass")
        self.assertEqual(report["authority_gate"], "pass")
        self.assertEqual(report["board_routing_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertEqual(len(report["replay_dates_observed"]), 30)
        self.assertEqual(len(report["shadow_dates_observed"]), 2)
        self.assertTrue(set(report["required_board_ids"]).issubset(set(report["board_ids_observed"])))
        self.assertFalse(report["d3_core_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["v7_1_current_switched"])
        self.assertFalse(report["v7_2_mail_or_schema_prerun"])
        self.assertFalse(validate_s2pdt04_china_d3_readiness_review_report(report))

    def test_s2pdt04_china_d3_readiness_blocks_short_replay_missing_board_and_shadow_side_effects(self) -> None:
        shadow_records = china_d3_shadow_records()
        shadow_records[0] = dict(shadow_records[0], production_affected=True, real_smtp_sent=True)
        board_routes = [record for record in china_d3_board_route_records() if record["board_id"] != "B6_risk"]

        report = build_s2pdt04_china_d3_readiness_review_report(
            generated_at=GENERATED_AT,
            c0_source_foundation_report=china_c0_source_foundation_report(),
            c1_department_source_map_report=china_c1_department_source_map_report(),
            legal_metadata_relation_report=china_legal_metadata_relation_report(),
            replay_records=china_d3_replay_records(count=29),
            shadow_records=shadow_records,
            board_route_records=board_routes,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["d3_replay_gate"], "blocked")
        self.assertEqual(report["d3_shadow_gate"], "blocked")
        self.assertEqual(report["board_routing_gate"], "blocked")
        self.assertFalse(report["d3_core_source_domain_accepted"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("30 distinct", joined)
        self.assertIn("send SMTP", joined)
        self.assertIn("B6_risk", joined)

    def test_s2pdt04_china_d3_readiness_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pdt04_china_d3_readiness_review(
                state_dir=tmp,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                c0_source_foundation_report=china_c0_source_foundation_report(),
                c1_department_source_map_report=china_c1_department_source_map_report(),
                legal_metadata_relation_report=china_legal_metadata_relation_report(),
                replay_records=china_d3_replay_records(),
                shadow_records=china_d3_shadow_records(),
                board_route_records=china_d3_board_route_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pdt04_china_d3_readiness_review_report(report))
            self.assertFalse(report["d3_core_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["d3_readiness_review_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pdt04_china_d3_readiness_review_report.json").is_file())

    def test_s2pft01_china_provincial_template_coverage_validates_without_production(self) -> None:
        report = build_s2pft01_china_provincial_template_coverage_report(
            generated_at=GENERATED_AT,
            d3_readiness_review_report=china_d3_readiness_report(),
            provincial_records=china_provincial_records(),
        )

        self.assertEqual(report["model_id"], S2PFT01_CHINA_PROVINCIAL_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PFT01-PROVINCES")
        self.assertEqual(report["task_id"], "S2PFT01")
        self.assertEqual(report["legacy_task_id"], "S2P5T01")
        self.assertEqual(report["phase"], "S2PF")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["upstream_d3_readiness_gate"], "pass")
        self.assertEqual(report["provincial_coverage_gate"], "pass")
        self.assertEqual(report["core_department_template_gate"], "pass")
        self.assertEqual(report["health_tier_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertEqual(report["required_mainland_provincial_count"], 31)
        self.assertEqual(len(report["provincial_ids_observed"]), 31)
        self.assertTrue({"province", "autonomous_region", "municipality"}.issubset(set(report["locality_types_observed"])))
        self.assertTrue(report["s2pf_provincial_template_coverage_ready"])
        self.assertFalse(report["d3_full_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(report["v7_2_mail_or_schema_prerun"])
        self.assertFalse(report["hk_mo_profile_modeled"])
        self.assertFalse(report["city_coverage_modeled"])
        self.assertFalse(report["special_zone_discovery_enabled"])
        self.assertFalse(validate_s2pft01_china_provincial_template_coverage_report(report))

    def test_s2pft01_china_provincial_template_coverage_blocks_missing_province_and_side_effects(self) -> None:
        records = [record for record in china_provincial_records() if record["province_id"] != "xinjiang"]
        records[0] = dict(
            records[0],
            core_department_roles=["government_portal"],
            production_affected=True,
            real_smtp_sent=True,
        )
        report = build_s2pft01_china_provincial_template_coverage_report(
            generated_at=GENERATED_AT,
            d3_readiness_review_report=china_d3_readiness_report(),
            provincial_records=records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["provincial_coverage_gate"], "blocked")
        self.assertEqual(report["core_department_template_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["s2pf_provincial_template_coverage_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("xinjiang", joined)
        self.assertIn("core department", joined)
        self.assertIn("production", joined)

    def test_s2pft01_china_provincial_template_coverage_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pft01_china_provincial_template_coverage(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                d3_readiness_review_report=china_d3_readiness_report(),
                provincial_records=china_provincial_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pft01_china_provincial_template_coverage_report(report))
            self.assertFalse(report["d3_full_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["provincial_template_coverage_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pft01_china_provincial_template_coverage_report.json").is_file())

    def test_s2pft02_hk_mo_independent_profile_validates_without_production(self) -> None:
        report = build_s2pft02_hk_mo_independent_profile_report(
            generated_at=GENERATED_AT,
            provincial_template_coverage_report=china_provincial_template_report(),
            jurisdiction_profiles=hk_mo_jurisdiction_profiles(),
        )

        self.assertEqual(report["model_id"], S2PFT02_HK_MO_PROFILE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PFT02-HK-MO")
        self.assertEqual(report["task_id"], "S2PFT02")
        self.assertEqual(report["legacy_task_id"], "S2P5T02")
        self.assertEqual(report["phase"], "S2PF")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["upstream_provincial_template_gate"], "pass")
        self.assertEqual(report["jurisdiction_coverage_gate"], "pass")
        self.assertEqual(report["language_profile_gate"], "pass")
        self.assertEqual(report["legal_status_gate"], "pass")
        self.assertEqual(report["template_independence_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertEqual(set(report["jurisdiction_ids_observed"]), {"hong_kong", "macau"})
        self.assertTrue({"zh_hant", "en", "pt"}.issubset(set(report["language_profiles_observed"])))
        self.assertTrue(report["s2pf_hk_mo_profile_ready"])
        self.assertTrue(report["hk_mo_profile_modeled"])
        self.assertFalse(report["mainland_template_applied_to_hk_mo"])
        self.assertFalse(report["d3_full_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(report["v7_2_mail_or_schema_prerun"])
        self.assertFalse(report["city_coverage_modeled"])
        self.assertFalse(report["special_zone_discovery_enabled"])
        self.assertFalse(validate_s2pft02_hk_mo_independent_profile_report(report))

    def test_s2pft02_hk_mo_independent_profile_blocks_missing_mo_and_mainland_template(self) -> None:
        profiles = [profile for profile in hk_mo_jurisdiction_profiles() if profile["jurisdiction_id"] != "macau"]
        profiles[0] = dict(
            profiles[0],
            template_source="mainland_province_template",
            mainland_template_applied=True,
            production_affected=True,
            real_smtp_sent=True,
        )
        report = build_s2pft02_hk_mo_independent_profile_report(
            generated_at=GENERATED_AT,
            provincial_template_coverage_report=china_provincial_template_report(),
            jurisdiction_profiles=profiles,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["jurisdiction_coverage_gate"], "blocked")
        self.assertEqual(report["template_independence_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["s2pf_hk_mo_profile_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("macau", joined)
        self.assertIn("mainland", joined)
        self.assertIn("production", joined)

    def test_s2pft02_hk_mo_independent_profile_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pft02_hk_mo_independent_profile(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                provincial_template_coverage_report=china_provincial_template_report(),
                jurisdiction_profiles=hk_mo_jurisdiction_profiles(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pft02_hk_mo_independent_profile_report(report))
            self.assertFalse(report["d3_full_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["hk_mo_profile_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pft02_hk_mo_independent_profile_report.json").is_file())

    def test_s2pft03_key_city_coverage_validates_without_production(self) -> None:
        report = build_s2pft03_key_city_coverage_report(
            generated_at=GENERATED_AT,
            hk_mo_profile_report=hk_mo_profile_report(),
            city_records=key_city_records(),
        )

        self.assertEqual(report["model_id"], S2PFT03_KEY_CITY_COVERAGE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PFT03-CITIES")
        self.assertEqual(report["task_id"], "S2PFT03")
        self.assertEqual(report["legacy_task_id"], "S2P5T03")
        self.assertEqual(report["phase"], "S2PF")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["upstream_hk_mo_profile_gate"], "pass")
        self.assertEqual(report["city_coverage_gate"], "pass")
        self.assertEqual(report["city_alias_gate"], "pass")
        self.assertEqual(report["city_department_template_gate"], "pass")
        self.assertEqual(report["region_weight_gate"], "pass")
        self.assertEqual(report["health_tier_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertEqual(report["required_city_count"], 24)
        self.assertEqual(set(report["city_ids_observed"]), set(S2PFT03_REQUIRED_CITY_IDS))
        self.assertTrue(report["s2pf_key_city_coverage_ready"])
        self.assertTrue(report["city_coverage_modeled"])
        self.assertFalse(report["d3_full_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(report["v7_2_mail_or_schema_prerun"])
        self.assertFalse(report["special_zone_discovery_enabled"])
        self.assertFalse(validate_s2pft03_key_city_coverage_report(report))

    def test_s2pft03_key_city_coverage_blocks_missing_city_roles_and_side_effects(self) -> None:
        records = [record for record in key_city_records() if record["city_id"] != "zhengzhou"]
        records[0] = dict(
            records[0],
            department_roles=["government_portal"],
            production_affected=True,
            real_smtp_sent=True,
        )
        report = build_s2pft03_key_city_coverage_report(
            generated_at=GENERATED_AT,
            hk_mo_profile_report=hk_mo_profile_report(),
            city_records=records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["city_coverage_gate"], "blocked")
        self.assertEqual(report["city_department_template_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["s2pf_key_city_coverage_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("zhengzhou", joined)
        self.assertIn("department", joined)
        self.assertIn("production", joined)
        self.assertTrue(validate_s2pft03_key_city_coverage_report(report))

    def test_s2pft03_key_city_coverage_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pft03_key_city_coverage(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                hk_mo_profile_report=hk_mo_profile_report(),
                city_records=key_city_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pft03_key_city_coverage_report(report))
            self.assertFalse(report["d3_full_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["key_city_coverage_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pft03_key_city_coverage_report.json").is_file())

    def test_s2pft04_special_zone_discovery_validates_without_production(self) -> None:
        report = build_s2pft04_special_zone_discovery_report(
            generated_at=GENERATED_AT,
            key_city_coverage_report=key_city_coverage_report(),
            zone_records=special_zone_records(),
        )

        self.assertEqual(report["model_id"], S2PFT04_SPECIAL_ZONE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PFT04-ZONES")
        self.assertEqual(report["task_id"], "S2PFT04")
        self.assertEqual(report["legacy_task_id"], "S2P5T04")
        self.assertEqual(report["phase"], "S2PF")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["upstream_key_city_coverage_gate"], "pass")
        self.assertEqual(report["zone_coverage_gate"], "pass")
        self.assertEqual(report["zone_authority_role_gate"], "pass")
        self.assertEqual(report["zone_type_policy_gate"], "pass")
        self.assertEqual(report["parent_city_mapping_gate"], "pass")
        self.assertEqual(report["health_tier_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertEqual(report["required_zone_count"], 10)
        self.assertEqual(set(report["zone_ids_observed"]), set(S2PFT04_REQUIRED_ZONE_IDS))
        self.assertTrue(report["s2pf_special_zone_discovery_ready"])
        self.assertTrue(report["special_zone_discovery_modeled"])
        self.assertFalse(report["special_zone_discovery_enabled"])
        self.assertFalse(report["d3_full_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(report["v7_2_mail_or_schema_prerun"])
        self.assertFalse(validate_s2pft04_special_zone_discovery_report(report))

    def test_s2pft04_special_zone_discovery_blocks_missing_zone_roles_parent_and_side_effects(self) -> None:
        records = [record for record in special_zone_records() if record["zone_id"] != "chongqing_liangjiang_new_area"]
        records[0] = dict(
            records[0],
            authority_roles=["government_portal"],
            parent_city_ids=["not_a_key_city"],
            production_affected=True,
            real_smtp_sent=True,
        )
        report = build_s2pft04_special_zone_discovery_report(
            generated_at=GENERATED_AT,
            key_city_coverage_report=key_city_coverage_report(),
            zone_records=records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["zone_coverage_gate"], "blocked")
        self.assertEqual(report["zone_authority_role_gate"], "blocked")
        self.assertEqual(report["parent_city_mapping_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["s2pf_special_zone_discovery_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("chongqing_liangjiang_new_area", joined)
        self.assertIn("authority", joined)
        self.assertIn("parent_city", joined)
        self.assertIn("production", joined)
        self.assertTrue(validate_s2pft04_special_zone_discovery_report(report))

    def test_s2pft04_special_zone_discovery_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pft04_special_zone_discovery(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                key_city_coverage_report=key_city_coverage_report(),
                zone_records=special_zone_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pft04_special_zone_discovery_report(report))
            self.assertFalse(report["d3_full_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["special_zone_discovery_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pft04_special_zone_discovery_report.json").is_file())

    def test_s2pft05_d3_full_governance_qualification_validates_without_production_acceptance(self) -> None:
        report = build_s2pft05_d3_full_governance_qualification_report(
            generated_at=GENERATED_AT,
            d3_readiness_review_report=china_d3_readiness_report(),
            provincial_template_coverage_report=china_provincial_template_report(),
            hk_mo_profile_report=hk_mo_profile_report(),
            key_city_coverage_report=key_city_coverage_report(),
            special_zone_discovery_report=special_zone_discovery_report(),
            governance_records=d3_full_governance_records(),
        )

        self.assertEqual(report["model_id"], S2PFT05_D3_FULL_GOVERNANCE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PFT05-D3-FULL")
        self.assertEqual(report["task_id"], "S2PFT05")
        self.assertEqual(report["legacy_task_id"], "S2P5T05")
        self.assertEqual(report["phase"], "S2PF")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["s2pf_d3_full_governance_qualification_ready"])
        self.assertTrue(report["d3_full_source_domain_qualified"])
        self.assertEqual(report["upstream_d3_readiness_gate"], "pass")
        self.assertEqual(report["component_coverage_gate"], "pass")
        self.assertEqual(report["quota_balance_gate"], "pass")
        self.assertEqual(report["health_balance_gate"], "pass")
        self.assertEqual(report["elimination_explanation_gate"], "pass")
        self.assertEqual(report["fallback_route_gate"], "pass")
        self.assertEqual(report["d3_full_replay_gate"], "pass")
        self.assertEqual(report["metadata_only_gate"], "pass")
        self.assertEqual(set(report["components_observed"]), set(S2PFT05_REQUIRED_COMPONENTS))
        self.assertEqual(set(report["quota_roles_observed"]), set(S2PFT05_REQUIRED_QUOTA_ROLES))
        self.assertEqual(len(report["replay_dates_observed"]), 30)
        self.assertFalse(report["d3_full_source_domain_accepted"])
        self.assertFalse(report["formal_production_inclusion"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["production_restore_executed"])
        self.assertFalse(report["production_schedule_enabled"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(report["v7_2_mail_or_schema_prerun"])
        self.assertFalse(validate_s2pft05_d3_full_governance_qualification_report(report))

    def test_s2pft05_d3_full_governance_qualification_blocks_missing_quota_replay_and_side_effects(self) -> None:
        records = [record for record in d3_full_governance_records(count=29) if record["component_id"] != "c4_special_zone"]
        records[0] = dict(
            records[0],
            quota_gate="blocked",
            elimination_explanation="",
            fallback_gate="blocked",
            production_affected=True,
            real_smtp_sent=True,
        )
        report = build_s2pft05_d3_full_governance_qualification_report(
            generated_at=GENERATED_AT,
            d3_readiness_review_report=china_d3_readiness_report(),
            provincial_template_coverage_report=china_provincial_template_report(),
            hk_mo_profile_report=hk_mo_profile_report(),
            key_city_coverage_report=key_city_coverage_report(),
            special_zone_discovery_report=special_zone_discovery_report(),
            governance_records=records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["component_coverage_gate"], "blocked")
        self.assertEqual(report["quota_balance_gate"], "blocked")
        self.assertEqual(report["elimination_explanation_gate"], "blocked")
        self.assertEqual(report["fallback_route_gate"], "blocked")
        self.assertEqual(report["d3_full_replay_gate"], "blocked")
        self.assertEqual(report["metadata_only_gate"], "blocked")
        self.assertFalse(report["s2pf_d3_full_governance_qualification_ready"])
        self.assertFalse(report["d3_full_source_domain_accepted"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("c4_special_zone", joined)
        self.assertIn("quota", joined)
        self.assertIn("30 distinct", joined)
        self.assertIn("production", joined)
        self.assertTrue(validate_s2pft05_d3_full_governance_qualification_report(report))

    def test_s2pft05_d3_full_governance_qualification_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pft05_d3_full_governance_qualification(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                d3_readiness_review_report=china_d3_readiness_report(),
                provincial_template_coverage_report=china_provincial_template_report(),
                hk_mo_profile_report=hk_mo_profile_report(),
                key_city_coverage_report=key_city_coverage_report(),
                special_zone_discovery_report=special_zone_discovery_report(),
                governance_records=d3_full_governance_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pft05_d3_full_governance_qualification_report(report))
            self.assertFalse(report["d3_full_source_domain_accepted"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertTrue(Path(report["d3_full_governance_qualification_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pft05_d3_full_governance_qualification_report.json").is_file())

    def test_s2pgt01_evidence_packet_v2_compatibility_passes_four_domains_without_schema_or_production(self) -> None:
        report = build_s2pgt01_evidence_packet_v2_compatibility_report(
            generated_at=GENERATED_AT,
            source_domain_reports=evidence_packet_domain_reports(),
            packet_records=evidence_packet_records(),
        )

        self.assertEqual(report["model_id"], S2PGT01_EVIDENCE_PACKET_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PGT01-EVIDENCE-V2")
        self.assertEqual(report["task_id"], "S2PGT01")
        self.assertEqual(report["phase"], "S2PG")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["packet_version"], "EvidencePacketV2")
        self.assertEqual(set(report["source_domains_observed"]), set(S2PGT01_REQUIRED_SOURCE_DOMAINS))
        self.assertEqual(set(report["evidence_levels_observed"]), set(S2PGT01_REQUIRED_EVIDENCE_LEVELS))
        self.assertEqual(report["source_domain_gate"], "pass")
        self.assertEqual(report["packet_shape_gate"], "pass")
        self.assertEqual(report["evidence_level_gate"], "pass")
        self.assertEqual(report["old_arxiv_compatibility_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertTrue(report["s2pgt01_evidence_packet_v2_compatibility_ready"])
        self.assertFalse(report["schema_migration_required"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["smtp_transport_allowed"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["release_upload_allowed"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["production_affected"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(validate_s2pgt01_evidence_packet_v2_compatibility_report(report))

    def test_s2pgt01_evidence_packet_v2_compatibility_blocks_missing_d4_and_side_effects(self) -> None:
        domain_reports = [row for row in evidence_packet_domain_reports() if row["source_domain"] != "d4_us_official"]
        packet_records = evidence_packet_records()
        packet_records[0] = dict(packet_records[0], old_arxiv_compatible=False, production_affected=True)
        packet_records[1] = dict(packet_records[1], evidence_levels_available=["unsupported_level"])
        report = build_s2pgt01_evidence_packet_v2_compatibility_report(
            generated_at=GENERATED_AT,
            source_domain_reports=domain_reports,
            packet_records=packet_records,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["source_domain_gate"], "blocked")
        self.assertEqual(report["evidence_level_gate"], "blocked")
        self.assertEqual(report["old_arxiv_compatibility_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        self.assertFalse(report["s2pgt01_evidence_packet_v2_compatibility_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("d4_us_official", joined)
        self.assertIn("unsupported_level", joined)
        self.assertIn("old_arxiv_compatible", joined)
        self.assertIn("production_affected", joined)
        self.assertTrue(validate_s2pgt01_evidence_packet_v2_compatibility_report(report))

    def test_s2pgt01_evidence_packet_v2_compatibility_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pgt01_evidence_packet_v2_compatibility(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pgt01_evidence_packet_v2_compatibility_report(report))
            self.assertFalse(report["schema_migration_required"])
            self.assertFalse(report["public_schema_changed"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertTrue(Path(report["evidence_packet_v2_compatibility_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pgt01_evidence_packet_v2_compatibility_report.json").is_file())

    def test_s2pgt02_knowledge_graph_spine_passes_identity_relation_and_idempotent_gates(self) -> None:
        report = build_s2pgt02_knowledge_graph_spine_report(
            generated_at=GENERATED_AT,
            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            ),
            identity_records=knowledge_graph_identity_records(),
            relation_records=knowledge_graph_relation_records(),
        )
        repeated = build_s2pgt02_knowledge_graph_spine_report(
            generated_at=GENERATED_AT,
            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            ),
            identity_records=knowledge_graph_identity_records(),
            relation_records=knowledge_graph_relation_records(),
        )

        self.assertEqual(report["model_id"], S2PGT02_KNOWLEDGE_GRAPH_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PGT02-KG")
        self.assertEqual(report["task_id"], "S2PGT02")
        self.assertEqual(report["legacy_task_id"], "S2P6T01")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["required_gates"]), set(S2PGT02_REQUIRED_GATES))
        self.assertEqual(set(report["identifier_types_observed"]), set(S2PGT02_REQUIRED_IDENTIFIER_TYPES))
        self.assertEqual(report["identifier_coverage_gate"], "pass")
        self.assertEqual(report["canonical_dedupe_gate"], "pass")
        self.assertEqual(report["relation_evidence_gate"], "pass")
        self.assertEqual(report["idempotent_update_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["duplicate_canonical_count"], 0)
        self.assertEqual(report["graph_state_hash"], repeated["graph_state_hash"])
        self.assertTrue(report["s2pgt02_knowledge_graph_spine_ready"])
        self.assertFalse(report["schema_migration_required"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["production_affected"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(validate_s2pgt02_knowledge_graph_spine_report(report))

    def test_s2pgt02_knowledge_graph_spine_blocks_duplicate_canonical_and_missing_relation_evidence(self) -> None:
        identities = knowledge_graph_identity_records()
        identities[0] = dict(identities[0], canonical_id="kg:manual-a")
        identities[1] = dict(identities[1], canonical_id="kg:manual-b")
        relations = knowledge_graph_relation_records()
        relations[0] = dict(relations[0], evidence_refs=[], production_affected=True)
        report = build_s2pgt02_knowledge_graph_spine_report(
            generated_at=GENERATED_AT,
            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            ),
            identity_records=identities,
            relation_records=relations,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["canonical_dedupe_gate"], "blocked")
        self.assertEqual(report["relation_evidence_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        self.assertFalse(report["s2pgt02_knowledge_graph_spine_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("duplicate canonical declaration", joined)
        self.assertIn("evidence_refs", joined)
        self.assertIn("production_affected", joined)
        self.assertTrue(validate_s2pgt02_knowledge_graph_spine_report(report))

    def test_s2pgt02_knowledge_graph_spine_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pgt02_knowledge_graph_spine(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                    generated_at=GENERATED_AT,
                    source_domain_reports=evidence_packet_domain_reports(),
                    packet_records=evidence_packet_records(),
                ),
                identity_records=knowledge_graph_identity_records(),
                relation_records=knowledge_graph_relation_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pgt02_knowledge_graph_spine_report(report))
            self.assertFalse(report["schema_migration_required"])
            self.assertFalse(report["public_schema_changed"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertTrue(Path(report["knowledge_graph_spine_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pgt02_knowledge_graph_spine_report.json").is_file())

    def test_s2pgt03_source_board_routing_passes_multilabel_reason_and_side_effect_gates(self) -> None:
        report = build_s2pgt03_source_board_routing_report(
            generated_at=GENERATED_AT,
            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            ),
            route_records=source_board_route_records(),
        )
        repeated = build_s2pgt03_source_board_routing_report(
            generated_at=GENERATED_AT,
            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            ),
            route_records=source_board_route_records(),
        )

        self.assertEqual(report["model_id"], S2PGT03_ROUTING_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PGT03-ROUTING")
        self.assertEqual(report["task_id"], "S2PGT03")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["source_domains_observed"]), set(S2PGT03_REQUIRED_SOURCE_DOMAINS))
        self.assertEqual(set(report["primary_boards_observed"]), set(S2PGT03_REQUIRED_PRIMARY_BOARDS))
        self.assertEqual(set(report["cross_cutting_boards_observed"]), set(S2PGT03_REQUIRED_CROSS_CUTTING_BOARDS))
        self.assertEqual(report["source_domain_coverage_gate"], "pass")
        self.assertEqual(report["primary_board_coverage_gate"], "pass")
        self.assertEqual(report["cross_cutting_board_coverage_gate"], "pass")
        self.assertEqual(report["route_reason_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["routing_state_hash"], repeated["routing_state_hash"])
        self.assertTrue(report["s2pgt03_source_board_routing_ready"])
        self.assertFalse(report["schema_migration_required"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["production_affected"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(validate_s2pgt03_source_board_routing_report(report))

    def test_s2pgt03_source_board_routing_blocks_missing_cross_reason_and_side_effects(self) -> None:
        routes = source_board_route_records()
        routes[0] = dict(routes[0], cross_cutting_boards=[], reason_codes=[], production_affected=True)
        routes[1] = dict(routes[1], primary_boards=["B6"])
        report = build_s2pgt03_source_board_routing_report(
            generated_at=GENERATED_AT,
            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            ),
            route_records=routes,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["cross_cutting_board_coverage_gate"], "pass")
        self.assertEqual(report["route_reason_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        self.assertFalse(report["s2pgt03_source_board_routing_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("cross_cutting_boards", joined)
        self.assertIn("reason_codes", joined)
        self.assertIn("unsupported board B6", joined)
        self.assertIn("production_affected", joined)
        self.assertTrue(validate_s2pgt03_source_board_routing_report(report))

    def test_s2pgt03_source_board_routing_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pgt03_source_board_routing(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                    generated_at=GENERATED_AT,
                    source_domain_reports=evidence_packet_domain_reports(),
                    packet_records=evidence_packet_records(),
                ),
                route_records=source_board_route_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pgt03_source_board_routing_report(report))
            self.assertFalse(report["schema_migration_required"])
            self.assertFalse(report["public_schema_changed"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertTrue(Path(report["source_board_routing_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pgt03_source_board_routing_report.json").is_file())

    def test_s2pgt04_delta_resonance_passes_support_refute_and_resonance_gates(self) -> None:
        routing_report = build_s2pgt03_source_board_routing_report(
            generated_at=GENERATED_AT,
            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            ),
            route_records=source_board_route_records(),
        )
        report = build_s2pgt04_delta_resonance_report(
            generated_at=GENERATED_AT,
            routing_report=routing_report,
            delta_records=delta_resonance_records(),
        )
        repeated = build_s2pgt04_delta_resonance_report(
            generated_at=GENERATED_AT,
            routing_report=routing_report,
            delta_records=delta_resonance_records(),
        )

        self.assertEqual(report["model_id"], S2PGT04_DELTA_RESONANCE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PGT04-DELTA-RESONANCE")
        self.assertEqual(report["task_id"], "S2PGT04")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["delta_types_observed"]), set(S2PGT04_REQUIRED_DELTA_TYPES))
        self.assertEqual(set(report["resonance_groups_observed"]), set(S2PGT04_REQUIRED_RESONANCE_GROUPS))
        self.assertIn("supported", report["support_statuses_observed"])
        self.assertIn("refuted", report["support_statuses_observed"])
        self.assertEqual(report["upstream_routing_gate"], "pass")
        self.assertEqual(report["delta_type_coverage_gate"], "pass")
        self.assertEqual(report["support_refute_gate"], "pass")
        self.assertEqual(report["resonance_group_gate"], "pass")
        self.assertEqual(report["delta_reason_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["resonance_state_hash"], repeated["resonance_state_hash"])
        self.assertTrue(report["s2pgt04_delta_resonance_ready"])
        self.assertFalse(report["schema_migration_required"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["production_affected"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(report["email_frontstage_changed"])
        self.assertFalse(validate_s2pgt04_delta_resonance_report(report))

    def test_s2pgt04_delta_resonance_blocks_missing_refute_bad_strength_and_side_effects(self) -> None:
        routing_report = build_s2pgt03_source_board_routing_report(
            generated_at=GENERATED_AT,
            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                generated_at=GENERATED_AT,
                source_domain_reports=evidence_packet_domain_reports(),
                packet_records=evidence_packet_records(),
            ),
            route_records=source_board_route_records(),
        )
        deltas = delta_resonance_records()
        deltas = [delta for delta in deltas if delta["support_status"] != "refuted"]
        deltas[0] = dict(deltas[0], signal_strength=1.8, production_affected=True, email_frontstage_changed=True)
        deltas[1] = dict(deltas[1], route_id="route:missing", evidence_refs=[])
        report = build_s2pgt04_delta_resonance_report(
            generated_at=GENERATED_AT,
            routing_report=routing_report,
            delta_records=deltas,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["support_refute_gate"], "blocked")
        self.assertEqual(report["delta_reason_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        self.assertFalse(report["s2pgt04_delta_resonance_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("support_status refuted", joined)
        self.assertIn("signal_strength", joined)
        self.assertIn("route_id must reference", joined)
        self.assertIn("evidence_refs", joined)
        self.assertIn("production_affected", joined)
        self.assertIn("email_frontstage_changed", joined)
        self.assertTrue(validate_s2pgt04_delta_resonance_report(report))

    def test_s2pgt04_delta_resonance_persists_report_without_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pgt04_delta_resonance(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                routing_report=build_s2pgt03_source_board_routing_report(
                    generated_at=GENERATED_AT,
                    evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                        generated_at=GENERATED_AT,
                        source_domain_reports=evidence_packet_domain_reports(),
                        packet_records=evidence_packet_records(),
                    ),
                    route_records=source_board_route_records(),
                ),
                delta_records=delta_resonance_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pgt04_delta_resonance_report(report))
            self.assertFalse(report["schema_migration_required"])
            self.assertFalse(report["public_schema_changed"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["email_frontstage_changed"])
            self.assertTrue(Path(report["delta_resonance_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pgt04_delta_resonance_report.json").is_file())

    def test_s2pgt05_cross_board_calibration_passes_deterministic_balance_and_reason_gates(self) -> None:
        delta_report = build_s2pgt04_delta_resonance_report(
            generated_at=GENERATED_AT,
            routing_report=build_s2pgt03_source_board_routing_report(
                generated_at=GENERATED_AT,
                evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                    generated_at=GENERATED_AT,
                    source_domain_reports=evidence_packet_domain_reports(),
                    packet_records=evidence_packet_records(),
                ),
                route_records=source_board_route_records(),
            ),
            delta_records=delta_resonance_records(),
        )
        report = build_s2pgt05_cross_board_calibration_report(
            generated_at=GENERATED_AT,
            delta_resonance_report=delta_report,
            queue_candidate_records=queue_candidate_records(),
        )
        repeated = build_s2pgt05_cross_board_calibration_report(
            generated_at=GENERATED_AT,
            delta_resonance_report=delta_report,
            queue_candidate_records=queue_candidate_records(),
        )

        self.assertEqual(report["model_id"], S2PGT05_CALIBRATION_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PGT05-CALIBRATION")
        self.assertEqual(report["task_id"], "S2PGT05")
        self.assertEqual(report["legacy_task_id"], "S2P6T02")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["board_ids_observed"]), set(S2PGT05_REQUIRED_BOARD_IDS))
        self.assertEqual(set(report["source_domains_observed"]), set(S2PGT05_REQUIRED_SOURCE_DOMAINS))
        self.assertEqual(set(report["queue_decisions_observed"]), set(S2PGT05_REQUIRED_DECISIONS))
        self.assertEqual(report["upstream_delta_resonance_gate"], "pass")
        self.assertEqual(report["percentile_calibration_gate"], "pass")
        self.assertEqual(report["source_balance_gate"], "pass")
        self.assertEqual(report["waiting_credit_gate"], "pass")
        self.assertEqual(report["queue_reason_gate"], "pass")
        self.assertEqual(report["deterministic_order_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["calibrated_queue_hash"], repeated["calibrated_queue_hash"])
        self.assertEqual(len([row for row in report["calibrated_queue_records"] if row["queue_decision"] == "selected"]), 4)
        self.assertLessEqual(max(report["source_share_by_domain"].values()), 0.5)
        self.assertTrue(report["s2pgt05_calibration_ready"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["ranking_algorithm_changed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["email_frontstage_changed"])
        self.assertFalse(validate_s2pgt05_cross_board_calibration_report(report))

    def test_s2pgt05_cross_board_calibration_blocks_missing_board_bad_wait_and_side_effects(self) -> None:
        delta_report = build_s2pgt04_delta_resonance_report(
            generated_at=GENERATED_AT,
            routing_report=build_s2pgt03_source_board_routing_report(
                generated_at=GENERATED_AT,
                evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                    generated_at=GENERATED_AT,
                    source_domain_reports=evidence_packet_domain_reports(),
                    packet_records=evidence_packet_records(),
                ),
                route_records=source_board_route_records(),
            ),
            delta_records=delta_resonance_records(),
        )
        candidates = [candidate for candidate in queue_candidate_records() if candidate["board_id"] != "B6"]
        candidates[0] = dict(candidates[0], waiting_days=31, raw_score=120, queue_mutation_allowed=True, ranking_algorithm_changed=True)
        candidates[1] = dict(candidates[1], delta_id="delta:missing", evidence_refs=[])
        report = build_s2pgt05_cross_board_calibration_report(
            generated_at=GENERATED_AT,
            delta_resonance_report=delta_report,
            queue_candidate_records=candidates,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["percentile_calibration_gate"], "blocked")
        self.assertEqual(report["waiting_credit_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        self.assertFalse(report["s2pgt05_calibration_ready"])
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("missing board B6", joined)
        self.assertIn("waiting_days", joined)
        self.assertIn("raw_score", joined)
        self.assertIn("delta_id must reference", joined)
        self.assertIn("evidence_refs", joined)
        self.assertIn("queue_mutation_allowed", joined)
        self.assertIn("ranking_algorithm_changed", joined)
        self.assertTrue(validate_s2pgt05_cross_board_calibration_report(report))

    def test_s2pgt05_cross_board_calibration_persists_report_without_queue_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pgt05_cross_board_calibration(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                delta_resonance_report=build_s2pgt04_delta_resonance_report(
                    generated_at=GENERATED_AT,
                    routing_report=build_s2pgt03_source_board_routing_report(
                        generated_at=GENERATED_AT,
                        evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                            generated_at=GENERATED_AT,
                            source_domain_reports=evidence_packet_domain_reports(),
                            packet_records=evidence_packet_records(),
                        ),
                        route_records=source_board_route_records(),
                    ),
                    delta_records=delta_resonance_records(),
                ),
                queue_candidate_records=queue_candidate_records(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pgt05_cross_board_calibration_report(report))
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["ranking_algorithm_changed"])
            self.assertFalse(report["public_schema_changed"])
            self.assertFalse(report["production_affected"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["email_frontstage_changed"])
            self.assertTrue(Path(report["calibration_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pgt05_calibration_report.json").is_file())

    def test_s2pit01_user_center_passes_one_edit_two_click_and_no_production_gates(self) -> None:
        report = build_s2pit01_user_center_report(
            generated_at=GENERATED_AT,
            owner_controls=s2pit01_owner_controls(),
            owner_validation_report=s2pit01_owner_validation(),
            owner_impact_preview=s2pit01_owner_preview(),
            storage_inspect_report=s2pit01_storage_inspect(),
        )

        self.assertEqual(report["model_id"], S2PIT01_USER_CENTER_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PIT01-USER-CENTER")
        self.assertEqual(report["task_id"], "S2PIT01")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["s2pit01_user_center_ready"])
        self.assertEqual(set(report["control_domains_observed"]), set(S2PIT01_REQUIRED_CONTROL_DOMAINS))
        self.assertEqual(report["single_editable_fact_source"], "config/owner_controls.yaml")
        self.assertLessEqual(report["max_click_depth"], 2)
        self.assertEqual(report["owner_controls_gate"], "pass")
        self.assertEqual(report["storage_readability_gate"], "pass")
        self.assertEqual(report["one_edit_directory_gate"], "pass")
        self.assertEqual(report["compatible_config_gate"], "pass")
        self.assertFalse(report["owner_experience_accepted"])
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["v7_2_contract_files_changed"])
        self.assertFalse(validate_s2pit01_user_center_report(report))

    def test_s2pit01_user_center_blocks_duplicate_fact_source_deep_click_and_side_effect(self) -> None:
        entries = [
            {
                "domain_id": domain,
                "label_zh": domain,
                "click_path": ["00_用户中心", "too", "deep"],
                "editable_fact_source": "docs/owner/00_用户中心/manual.yaml" if domain == "profile" else "config/owner_controls.yaml",
                "compiled_config_path": "config/owner_controls.yaml",
                "config_sections": ["project"],
                "user_center_paths": ["docs/owner/00_用户中心/00_开始这里.md"],
                "generated_view_paths": [],
                "generated_view_editable": domain == "mail_review",
                "real_smtp_sent": domain == "budget_schedule",
            }
            for domain in S2PIT01_REQUIRED_CONTROL_DOMAINS
        ]

        report = build_s2pit01_user_center_report(
            generated_at=GENERATED_AT,
            owner_controls=s2pit01_owner_controls(),
            owner_validation_report=s2pit01_owner_validation(),
            owner_impact_preview=s2pit01_owner_preview(),
            storage_inspect_report=s2pit01_storage_inspect("blocked"),
            control_entries=entries,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["storage_readability_gate"], "blocked")
        self.assertEqual(report["one_edit_directory_gate"], "blocked")
        self.assertEqual(report["click_depth_gate"], "blocked")
        self.assertEqual(report["compatible_config_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("exactly one editable fact source", joined)
        self.assertIn("generated owner/user-center views", joined)
        self.assertIn("2 clicks", joined)
        self.assertIn("real_smtp_sent", joined)
        self.assertTrue(validate_s2pit01_user_center_report(report))

    def test_s2pit01_user_center_persists_report_without_storage_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pit01_user_center(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                owner_controls=s2pit01_owner_controls(),
                owner_validation_report=s2pit01_owner_validation(),
                owner_impact_preview=s2pit01_owner_preview(),
                storage_inspect_report=s2pit01_storage_inspect(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pit01_user_center_report(report))
            self.assertFalse(report["schema_migration_allowed"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["source_adapter_changed"])
            self.assertTrue(Path(report["user_center_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pit01_user_center_report.json").is_file())

    def test_s2pit02_runtime_dashboard_passes_local_state_and_no_production_gates(self) -> None:
        report = build_s2pit02_runtime_dashboard_report(
            generated_at=GENERATED_AT,
            user_center_report=s2pit01_user_center_report(),
            runtime_audit_report=s2pit02_runtime_report("runtime_audit"),
            watchdog_report=s2pit02_runtime_report("watchdog"),
            storage_inspect_report=s2pit01_storage_inspect(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PIT02_RUNTIME_DASHBOARD_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PIT02-RUNTIME-DASHBOARD")
        self.assertEqual(report["task_id"], "S2PIT02")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["owner_center_gate"], "pass")
        self.assertEqual(report["runtime_state_gate"], "pass")
        self.assertEqual(report["storage_state_gate"], "pass")
        self.assertEqual(report["production_boundary_gate"], "pass")
        self.assertEqual(report["dashboard_section_gate"], "pass")
        self.assertTrue(report["s2pit02_runtime_dashboard_ready"])
        self.assertIn("runtime", report["dashboard_sections"])
        self.assertIn("watchdog", report["dashboard_sections"]["runtime"]["runtime_actions_observed"])
        self.assertEqual(report["owner_status_path"], "docs/owner/00_用户中心/01_当前状态.md")
        self.assertFalse(report["stage2_production_accepted"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["release_upload_allowed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(validate_s2pit02_runtime_dashboard_report(report))

    def test_s2pit02_runtime_dashboard_blocks_stale_runtime_and_production_side_effect(self) -> None:
        report = build_s2pit02_runtime_dashboard_report(
            generated_at=GENERATED_AT,
            user_center_report={**s2pit01_user_center_report(), "status": "blocked"},
            runtime_audit_report={**s2pit02_runtime_report("runtime_audit", "blocked"), "real_scheduler_installed": True},
            watchdog_report=s2pit02_runtime_report("heartbeat"),
            storage_inspect_report=s2pit01_storage_inspect("blocked"),
            production_gate_state=s2pit02_production_gate_state(real_smtp_sent=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["owner_center_gate"], "blocked")
        self.assertEqual(report["runtime_state_gate"], "blocked")
        self.assertEqual(report["storage_state_gate"], "blocked")
        self.assertEqual(report["production_boundary_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("runtime_audit report must pass", joined)
        self.assertIn("real_scheduler_installed", joined)
        self.assertIn("watchdog report action must be watchdog", joined)
        self.assertIn("production_gate_state.real_smtp_sent", joined)
        self.assertTrue(validate_s2pit02_runtime_dashboard_report(report))

    def test_s2pit02_runtime_dashboard_persists_report_without_runtime_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pit02_runtime_dashboard(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                user_center_report=s2pit01_user_center_report(),
                runtime_audit_report=s2pit02_runtime_report("runtime_audit"),
                watchdog_report=s2pit02_runtime_report("watchdog"),
                storage_inspect_report=s2pit01_storage_inspect(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pit02_runtime_dashboard_report(report))
            self.assertFalse(report["schema_migration_allowed"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["source_adapter_changed"])
            self.assertTrue(Path(report["runtime_dashboard_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pit02_runtime_dashboard_report.json").is_file())

    def test_s2pit03_source_model_view_passes_source_board_parameter_and_queue_gates(self) -> None:
        report = build_s2pit03_source_model_view_report(
            generated_at=GENERATED_AT,
            user_center_report=s2pit01_user_center_report(),
            source_domain_records=s2pit03_source_domains(),
            reading_board_records=s2pit03_reading_boards(),
            parameter_records=s2pit03_parameter_records(),
            queue_view_records=s2pit03_queue_view_records(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PIT03_SOURCE_MODEL_VIEW_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PIT03-SOURCE-MODEL")
        self.assertEqual(report["task_id"], "S2PIT03")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["source_domains_observed"]), set(S2PIT03_REQUIRED_SOURCE_DOMAINS))
        self.assertEqual(set(report["reading_boards_observed"]), set(S2PIT03_REQUIRED_READING_BOARDS))
        self.assertLessEqual(len(report["first_screen_parameter_ids"]), 20)
        self.assertEqual(report["source_domain_gate"], "pass")
        self.assertEqual(report["reading_board_gate"], "pass")
        self.assertEqual(report["parameter_disclosure_gate"], "pass")
        self.assertEqual(report["queue_view_gate"], "pass")
        self.assertEqual(report["traceability_gate"], "pass")
        self.assertEqual(report["deterministic_view_gate"], "pass")
        self.assertTrue(report["s2pit03_source_model_view_ready"])
        self.assertFalse(report["source_adapter_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["ranking_algorithm_changed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(validate_s2pit03_source_model_view_report(report))

    def test_s2pit03_source_model_view_blocks_missing_coverage_overload_and_side_effects(self) -> None:
        source_domains = s2pit03_source_domains()[:-1]
        reading_boards = s2pit03_reading_boards()
        reading_boards[0] = {**reading_boards[0], "source_domain_refs": ["DX"], "real_smtp_sent": True}
        parameters = s2pit03_parameter_records(21)
        parameters = [{**parameter, "first_screen": True} for parameter in parameters]
        parameters[0] = {**parameters[0], "searchable": False, "code_refs": []}
        queue_records = s2pit03_queue_view_records()
        queue_records[0] = {**queue_records[0], "source_domain": "DX", "exportable": False, "detail_ref": ""}

        report = build_s2pit03_source_model_view_report(
            generated_at=GENERATED_AT,
            user_center_report={**s2pit01_user_center_report(), "status": "blocked"},
            source_domain_records=source_domains,
            reading_board_records=reading_boards,
            parameter_records=parameters,
            queue_view_records=queue_records,
            production_gate_state=s2pit02_production_gate_state(public_schema_changed=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["user_center_gate"], "blocked")
        self.assertEqual(report["source_domain_gate"], "blocked")
        self.assertEqual(report["reading_board_gate"], "blocked")
        self.assertEqual(report["parameter_disclosure_gate"], "blocked")
        self.assertEqual(report["queue_view_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("missing source domain", joined)
        self.assertIn("unknown source_domain_refs", joined)
        self.assertIn("first-screen parameters", joined)
        self.assertIn("must be searchable", joined)
        self.assertIn("source_domain must be D1-D4", joined)
        self.assertIn("public_schema_changed", joined)
        self.assertTrue(validate_s2pit03_source_model_view_report(report))

    def test_s2pit03_source_model_view_persists_report_without_production_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pit03_source_model_view(
                state_dir=tmp,
                date="2026-06-26",
                generated_at=GENERATED_AT,
                user_center_report=s2pit01_user_center_report(),
                source_domain_records=s2pit03_source_domains(),
                reading_board_records=s2pit03_reading_boards(),
                parameter_records=s2pit03_parameter_records(),
                queue_view_records=s2pit03_queue_view_records(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pit03_source_model_view_report(report))
            self.assertFalse(report["source_adapter_changed"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["public_schema_changed"])
            self.assertTrue(Path(report["source_model_view_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pit03_source_model_view_report.json").is_file())

    def test_s2pit04_content_ledger_passes_traceability_counts_and_no_send_gates(self) -> None:
        report = build_s2pit04_content_ledger_report(
            generated_at=GENERATED_AT,
            runtime_dashboard_report=s2pit02_runtime_dashboard_report(),
            source_model_view_report=s2pit03_source_model_view_report(),
            lifecycle_state_report=s2pjt01_lifecycle_state_report(),
            review_schedule_report=s2pjt02_review_schedule_report(),
            action_roi_report=s2pjt03_action_roi_report(),
            ledger_records=s2pit04_ledger_records(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PIT04_CONTENT_LEDGER_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PIT04-LEDGER")
        self.assertEqual(report["task_id"], "S2PIT04")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["runtime_dashboard_gate"], "pass")
        self.assertEqual(report["source_model_view_gate"], "pass")
        self.assertEqual(report["lifecycle_state_gate"], "pass")
        self.assertEqual(report["review_schedule_gate"], "pass")
        self.assertEqual(report["action_roi_gate"], "pass")
        self.assertEqual(report["ledger_record_gate"], "pass")
        self.assertEqual(report["traceability_gate"], "pass")
        self.assertEqual(report["count_conservation_gate"], "pass")
        self.assertEqual(report["deterministic_ledger_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["ledger_record_count"], 3)
        self.assertEqual(report["content_count"], 3)
        self.assertEqual(report["mail_status_counts"], {"previewed": 1, "ready_no_send": 1, "blocked_no_send": 1})
        self.assertEqual(report["feedback_status_counts"], {"pending": 1, "received": 1, "not_requested": 1})
        self.assertEqual(report["roi_status_counts"], {"not_calculable": 2, "calculated": 1})
        self.assertTrue(report["ledger_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pit04_content_ledger_ready"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["release_upload_allowed"])
        self.assertFalse(report["db_migration_executed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["email_frontstage_changed"])
        self.assertFalse(validate_s2pit04_content_ledger_report(report))

    def test_s2pit04_content_ledger_blocks_orphans_bad_status_and_side_effects(self) -> None:
        records = s2pit04_ledger_records()
        records[0] = {
            **records[0],
            "mail_id": "",
            "mail_status": "sent",
            "feedback_status": "unknown",
            "action_ids": ["act:missing"],
            "asset_ids": ["asset:missing"],
            "real_smtp_sent": True,
        }
        records[1] = {**records[1], "content_id": records[0]["content_id"], "roi": {"status": "calculated"}}
        report = build_s2pit04_content_ledger_report(
            generated_at=GENERATED_AT,
            runtime_dashboard_report={**s2pit02_runtime_dashboard_report(), "status": "blocked"},
            source_model_view_report={**s2pit03_source_model_view_report(), "status": "blocked"},
            lifecycle_state_report={**s2pjt01_lifecycle_state_report(), "status": "blocked"},
            review_schedule_report={**s2pjt02_review_schedule_report(), "status": "blocked"},
            action_roi_report={**s2pjt03_action_roi_report(), "status": "blocked"},
            ledger_records=records,
            production_gate_state=s2pit02_production_gate_state(scheduler_enabled=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["runtime_dashboard_gate"], "blocked")
        self.assertEqual(report["source_model_view_gate"], "blocked")
        self.assertEqual(report["lifecycle_state_gate"], "blocked")
        self.assertEqual(report["review_schedule_gate"], "blocked")
        self.assertEqual(report["action_roi_gate"], "blocked")
        self.assertEqual(report["ledger_record_gate"], "blocked")
        self.assertEqual(report["traceability_gate"], "blocked")
        self.assertEqual(report["count_conservation_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("S2PIT02 runtime dashboard report must pass", joined)
        self.assertIn("S2PIT03 source/model view report must pass", joined)
        self.assertIn("S2PJT01 lifecycle state report must pass", joined)
        self.assertIn("S2PJT02 review schedule report must pass", joined)
        self.assertIn("S2PJT03 action/asset/ROI report must pass", joined)
        self.assertIn("missing mail_id", joined)
        self.assertIn("mail_status must be previewed", joined)
        self.assertIn("feedback_status must be pending", joined)
        self.assertIn("action_id act:missing", joined)
        self.assertIn("asset_id asset:missing", joined)
        self.assertIn("calculated ROI must trace", joined)
        self.assertIn("duplicate ledger content_id", joined)
        self.assertIn("real_smtp_sent", joined)
        self.assertIn("production_gate_state.scheduler_enabled", joined)
        self.assertFalse(validate_s2pit04_content_ledger_report(report))

    def test_s2pit04_content_ledger_persists_report_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pit04_content_ledger(
                state_dir=tmp,
                date="2026-06-26",
                generated_at=GENERATED_AT,
                runtime_dashboard_report=s2pit02_runtime_dashboard_report(),
                source_model_view_report=s2pit03_source_model_view_report(),
                lifecycle_state_report=s2pjt01_lifecycle_state_report(),
                review_schedule_report=s2pjt02_review_schedule_report(),
                action_roi_report=s2pjt03_action_roi_report(),
                ledger_records=s2pit04_ledger_records(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pit04_content_ledger_report(report))
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertTrue(Path(report["content_ledger_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pit04_content_mail_review_action_roi_ledger_report.json").is_file())

    def test_s2pkt01_mail_contract_passes_shared_contract_board_hash_and_no_send_gates(self) -> None:
        report = build_s2pkt01_mail_contract_report(
            generated_at=GENERATED_AT,
            content_quality_report=s2pht05_content_quality_gate_report(),
            content_ledger_report=s2pit04_content_ledger_report(),
            action_roi_report=s2pjt03_action_roi_report(),
            mail_contracts=s2pkt01_mail_contracts(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PKT01_MAIL_CONTRACT_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PKT01-MAIL-CONTRACT")
        self.assertEqual(report["task_id"], "S2PKT01")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["content_quality_gate"], "pass")
        self.assertEqual(report["content_ledger_gate"], "pass")
        self.assertEqual(report["action_roi_gate"], "pass")
        self.assertEqual(report["shared_contract_gate"], "pass")
        self.assertEqual(report["board_differentiation_gate"], "pass")
        self.assertEqual(report["reading_layer_gate"], "pass")
        self.assertEqual(report["evidence_label_gate"], "pass")
        self.assertEqual(report["feedback_component_gate"], "pass")
        self.assertEqual(report["hash_status_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["email_contract_id"], "EMAIL_LEARNING_V1")
        self.assertEqual(report["template_version"], "1.0.0")
        self.assertEqual(report["mail_product_count"], 4)
        self.assertEqual(report["mail_status_counts"], {"ready_no_send": 2, "previewed": 1, "blocked_no_send": 1})
        self.assertTrue(report["mail_contract_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pkt01_mail_contract_ready"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["smtp_transport_allowed"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["release_upload_allowed"])
        self.assertFalse(report["db_migration_executed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["email_frontstage_changed"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertEqual([row["mail_product_id"] for row in report["mail_contracts"]], ["M1", "M2", "M3", "M4"])
        self.assertEqual([row["primary_board"] for row in report["mail_contracts"]], ["B1", "B2", "B3", "B1-B6"])
        self.assertTrue(all(row["mail_hash"].startswith("sha256:") for row in report["mail_contracts"]))
        self.assertFalse(validate_s2pkt01_mail_contract_report(report))

    def test_s2pkt01_mail_contract_blocks_missing_product_bad_layers_and_side_effects(self) -> None:
        contracts = s2pkt01_mail_contracts()
        contracts = contracts[:3]
        contracts[0] = {
            **contracts[0],
            "contract_id": "OLD_TEMPLATE",
            "mail_hash": "sha256:stale",
            "real_smtp_sent": True,
        }
        contracts[1] = {
            **contracts[1],
            "mail_product_id": "M1",
            "primary_board": "B2",
            "cross_cutting_boards": ["B4", "B5"],
            "reading_layers": ["plain_language_summary"],
            "evidence_labels": ["FACT"],
            "feedback_actions": ["useful"],
            "status": "sent",
        }
        contracts[2] = {
            **contracts[2],
            "primary_board": "B2",
            "scheduler_enabled": True,
        }
        report = build_s2pkt01_mail_contract_report(
            generated_at=GENERATED_AT,
            content_quality_report={**s2pht05_content_quality_gate_report(), "status": "blocked"},
            content_ledger_report={**s2pit04_content_ledger_report(), "status": "blocked"},
            action_roi_report={**s2pjt03_action_roi_report(), "status": "blocked"},
            mail_contracts=contracts,
            production_gate_state=s2pit02_production_gate_state(scheduler_enabled=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["content_quality_gate"], "blocked")
        self.assertEqual(report["content_ledger_gate"], "blocked")
        self.assertEqual(report["action_roi_gate"], "blocked")
        self.assertEqual(report["shared_contract_gate"], "blocked")
        self.assertEqual(report["board_differentiation_gate"], "blocked")
        self.assertEqual(report["reading_layer_gate"], "blocked")
        self.assertEqual(report["evidence_label_gate"], "blocked")
        self.assertEqual(report["feedback_component_gate"], "blocked")
        self.assertEqual(report["hash_status_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("S2PHT05 content quality report must pass", joined)
        self.assertIn("S2PIT04 content ledger report must pass", joined)
        self.assertIn("S2PJT03 action/asset/ROI report must pass", joined)
        self.assertIn("contract_id must be EMAIL_LEARNING_V1", joined)
        self.assertIn("missing mail products: M2, M4", joined)
        self.assertIn("duplicate mail products: M1", joined)
        self.assertIn("M1 primary_board must be B1", joined)
        self.assertIn("cross_cutting_boards must be B4/B5/B6", joined)
        self.assertIn("missing reading layer evidence_trace", joined)
        self.assertIn("missing evidence label INFERENCE", joined)
        self.assertIn("missing feedback action need_more_evidence", joined)
        self.assertIn("status must be ready_no_send", joined)
        self.assertIn("mail_hash must match contract fields", joined)
        self.assertIn("M1.real_smtp_sent", joined)
        self.assertIn("M3.scheduler_enabled", joined)
        self.assertIn("production_gate_state.scheduler_enabled", joined)
        self.assertFalse(validate_s2pkt01_mail_contract_report(report))

    def test_s2pkt01_mail_contract_persists_report_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pkt01_mail_contract(
                state_dir=tmp,
                date="2026-06-26",
                generated_at=GENERATED_AT,
                content_quality_report=s2pht05_content_quality_gate_report(),
                content_ledger_report=s2pit04_content_ledger_report(),
                action_roi_report=s2pjt03_action_roi_report(),
                mail_contracts=s2pkt01_mail_contracts(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pkt01_mail_contract_report(report))
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["smtp_transport_allowed"])
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["email_frontstage_changed"])
            self.assertTrue(Path(report["mail_contract_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pkt01_mail_contract_report.json").is_file())

    def test_s2pkt02_m1_mail_passes_section_action_and_no_send_gates(self) -> None:
        report = build_s2pkt02_m1_mail_report(
            generated_at=GENERATED_AT,
            mail_contract_report=s2pkt01_mail_contract_report(),
            content_quality_report=s2pht05_content_quality_gate_report(),
            content_ledger_report=s2pit04_content_ledger_report(),
            action_roi_report=s2pjt03_action_roi_report(),
            m1_mail_record=s2pkt02_m1_mail_record(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PKT02_M1_MAIL_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PKT02-M1")
        self.assertEqual(report["task_id"], "S2PKT02")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["mail_contract_gate"], "pass")
        self.assertEqual(report["content_quality_gate"], "pass")
        self.assertEqual(report["content_ledger_gate"], "pass")
        self.assertEqual(report["action_roi_gate"], "pass")
        self.assertEqual(report["m1_scope_gate"], "pass")
        self.assertEqual(report["section_coverage_gate"], "pass")
        self.assertEqual(report["evidence_counterevidence_gate"], "pass")
        self.assertEqual(report["personal_action_gate"], "pass")
        self.assertEqual(report["hash_status_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["mail_product_id"], "M1")
        self.assertEqual(report["primary_board"], "B1")
        self.assertEqual(report["cross_cutting_boards"], ["B4", "B5", "B6"])
        self.assertEqual(report["section_count"], 5)
        self.assertEqual(report["source_content_count"], 1)
        self.assertEqual(report["action_count"], 2)
        self.assertEqual(report["action_windows"], ["15m", "2h"])
        self.assertTrue(report["m1_mail_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pkt02_m1_mail_ready"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["smtp_transport_allowed"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["release_upload_allowed"])
        self.assertFalse(report["db_migration_executed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["email_frontstage_changed"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(validate_s2pkt02_m1_mail_report(report))

    def test_s2pkt02_m1_mail_blocks_scope_section_action_and_side_effect_drift(self) -> None:
        record = s2pkt02_m1_mail_record()
        record["mail_product_id"] = "M2"
        record["primary_board"] = "B2"
        record["cross_cutting_boards"] = ["B4", "B5"]
        record["source_content_ids"] = ["content:missing"]
        record["action_ids"] = ["act:missing"]
        record["m1_mail_hash"] = "sha256:stale"
        record["real_smtp_sent"] = True
        record["sections"] = [
            {
                "section_id": "scientific_mechanism",
                "content_ids": ["content:missing"],
                "evidence_refs": [],
                "evidence_labels": ["UNKNOWN"],
            },
            {
                "section_id": "action_path",
                "content_ids": ["content:missing"],
                "evidence_refs": ["local://bad"],
                "evidence_labels": ["FACT"],
                "action_ids": ["act:missing"],
            },
        ]
        report = build_s2pkt02_m1_mail_report(
            generated_at=GENERATED_AT,
            mail_contract_report={**s2pkt01_mail_contract_report(), "status": "blocked"},
            content_quality_report={**s2pht05_content_quality_gate_report(), "status": "blocked"},
            content_ledger_report={**s2pit04_content_ledger_report(), "status": "blocked"},
            action_roi_report={**s2pjt03_action_roi_report(), "status": "blocked"},
            m1_mail_record=record,
            production_gate_state=s2pit02_production_gate_state(real_smtp_sent=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["mail_contract_gate"], "blocked")
        self.assertEqual(report["content_quality_gate"], "blocked")
        self.assertEqual(report["content_ledger_gate"], "blocked")
        self.assertEqual(report["action_roi_gate"], "blocked")
        self.assertEqual(report["m1_scope_gate"], "blocked")
        self.assertEqual(report["section_coverage_gate"], "blocked")
        self.assertEqual(report["evidence_counterevidence_gate"], "blocked")
        self.assertEqual(report["personal_action_gate"], "blocked")
        self.assertEqual(report["hash_status_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("S2PKT01 mail contract report must pass", joined)
        self.assertIn("S2PHT05 content quality report must pass", joined)
        self.assertIn("S2PIT04 content ledger report must pass", joined)
        self.assertIn("S2PJT03 action/asset/ROI report must pass", joined)
        self.assertIn("mail_product_id must be M1", joined)
        self.assertIn("primary_board must be B1", joined)
        self.assertIn("cross_cutting_boards must be B4/B5/B6", joined)
        self.assertIn("source_content_id content:missing not traceable to S2PIT04", joined)
        self.assertIn("missing section counterevidence", joined)
        self.assertIn("evidence_refs must be non-empty", joined)
        self.assertIn("evidence label UNKNOWN is not allowed", joined)
        self.assertIn("action_id act:missing not traceable to S2PJT03", joined)
        self.assertIn("missing required action windows", joined)
        self.assertIn("m1_mail_hash must match", joined)
        self.assertIn("real_smtp_sent must be false", joined)
        self.assertIn("production_gate_state.real_smtp_sent", joined)
        self.assertFalse(validate_s2pkt02_m1_mail_report(report))

    def test_s2pkt02_m1_mail_persists_report_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pkt02_m1_mail(
                state_dir=tmp,
                date="2026-06-26",
                generated_at=GENERATED_AT,
                mail_contract_report=s2pkt01_mail_contract_report(),
                content_quality_report=s2pht05_content_quality_gate_report(),
                content_ledger_report=s2pit04_content_ledger_report(),
                action_roi_report=s2pjt03_action_roi_report(),
                m1_mail_record=s2pkt02_m1_mail_record(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pkt02_m1_mail_report(report))
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["smtp_transport_allowed"])
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["email_frontstage_changed"])
            self.assertTrue(Path(report["m1_mail_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pkt02_m1_mail_report.json").is_file())

    def test_s2pkt03_m2_mail_passes_engineering_product_and_no_send_gates(self) -> None:
        report = build_s2pkt03_m2_mail_report(
            generated_at=GENERATED_AT,
            mail_contract_report=s2pkt01_mail_contract_report(),
            content_quality_report=s2pht05_content_quality_gate_report(),
            content_ledger_report=s2pit04_content_ledger_report(),
            action_roi_report=s2pjt03_action_roi_report(),
            m2_mail_record=s2pkt03_m2_mail_record(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PKT03_M2_MAIL_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PKT03-M2")
        self.assertEqual(report["task_id"], "S2PKT03")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["mail_contract_gate"], "pass")
        self.assertEqual(report["content_quality_gate"], "pass")
        self.assertEqual(report["content_ledger_gate"], "pass")
        self.assertEqual(report["action_roi_gate"], "pass")
        self.assertEqual(report["m2_scope_gate"], "pass")
        self.assertEqual(report["section_coverage_gate"], "pass")
        self.assertEqual(report["engineering_reproducibility_gate"], "pass")
        self.assertEqual(report["product_limit_action_gate"], "pass")
        self.assertEqual(report["hash_status_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["mail_product_id"], "M2")
        self.assertEqual(report["primary_board"], "B2")
        self.assertEqual(report["cross_cutting_boards"], ["B4", "B5", "B6"])
        self.assertEqual(report["section_count"], 5)
        self.assertEqual(report["source_content_count"], 1)
        self.assertEqual(report["action_count"], 2)
        self.assertEqual(report["action_windows"], ["2h", "7d"])
        self.assertTrue(report["m2_mail_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pkt03_m2_mail_ready"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["smtp_transport_allowed"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["release_upload_allowed"])
        self.assertFalse(report["db_migration_executed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["email_frontstage_changed"])
        self.assertFalse(report["integrated_production_accepted"])
        self.assertFalse(validate_s2pkt03_m2_mail_report(report))

    def test_s2pkt03_m2_mail_blocks_scope_section_action_and_side_effect_drift(self) -> None:
        record = s2pkt03_m2_mail_record()
        record["mail_product_id"] = "M1"
        record["primary_board"] = "B1"
        record["cross_cutting_boards"] = ["B4", "B5"]
        record["source_content_ids"] = ["content:missing"]
        record["action_ids"] = ["act:missing"]
        record["m2_mail_hash"] = "sha256:stale"
        record["real_smtp_sent"] = True
        record["sections"] = [
            {
                "section_id": "engineering_usability",
                "content_ids": ["content:missing"],
                "evidence_refs": [],
                "evidence_labels": ["UNKNOWN"],
            },
            {
                "section_id": "action_path",
                "content_ids": ["content:missing"],
                "evidence_refs": ["local://bad"],
                "evidence_labels": ["FACT"],
                "action_ids": ["act:missing"],
            },
        ]
        report = build_s2pkt03_m2_mail_report(
            generated_at=GENERATED_AT,
            mail_contract_report={**s2pkt01_mail_contract_report(), "status": "blocked"},
            content_quality_report={**s2pht05_content_quality_gate_report(), "status": "blocked"},
            content_ledger_report={**s2pit04_content_ledger_report(), "status": "blocked"},
            action_roi_report={**s2pjt03_action_roi_report(), "status": "blocked"},
            m2_mail_record=record,
            production_gate_state=s2pit02_production_gate_state(real_smtp_sent=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["mail_contract_gate"], "blocked")
        self.assertEqual(report["content_quality_gate"], "blocked")
        self.assertEqual(report["content_ledger_gate"], "blocked")
        self.assertEqual(report["action_roi_gate"], "blocked")
        self.assertEqual(report["m2_scope_gate"], "blocked")
        self.assertEqual(report["section_coverage_gate"], "blocked")
        self.assertEqual(report["engineering_reproducibility_gate"], "blocked")
        self.assertEqual(report["product_limit_action_gate"], "blocked")
        self.assertEqual(report["hash_status_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("S2PKT01 mail contract report must pass", joined)
        self.assertIn("S2PHT05 content quality report must pass", joined)
        self.assertIn("S2PIT04 content ledger report must pass", joined)
        self.assertIn("S2PJT03 action/asset/ROI report must pass", joined)
        self.assertIn("mail_product_id must be M2", joined)
        self.assertIn("primary_board must be B2", joined)
        self.assertIn("cross_cutting_boards must be B4/B5/B6", joined)
        self.assertIn("source_content_id content:missing not traceable to S2PIT04", joined)
        self.assertIn("missing section reproducibility", joined)
        self.assertIn("evidence_refs must be non-empty", joined)
        self.assertIn("evidence label UNKNOWN is not allowed", joined)
        self.assertIn("action_id act:missing not traceable to S2PJT03", joined)
        self.assertIn("missing required action windows", joined)
        self.assertIn("m2_mail_hash must match", joined)
        self.assertIn("real_smtp_sent must be false", joined)
        self.assertIn("production_gate_state.real_smtp_sent", joined)
        self.assertFalse(validate_s2pkt03_m2_mail_report(report))

    def test_s2pkt03_m2_mail_persists_report_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pkt03_m2_mail(
                state_dir=tmp,
                date="2026-06-26",
                generated_at=GENERATED_AT,
                mail_contract_report=s2pkt01_mail_contract_report(),
                content_quality_report=s2pht05_content_quality_gate_report(),
                content_ledger_report=s2pit04_content_ledger_report(),
                action_roi_report=s2pjt03_action_roi_report(),
                m2_mail_record=s2pkt03_m2_mail_record(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pkt03_m2_mail_report(report))
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["smtp_transport_allowed"])
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["email_frontstage_changed"])
            self.assertTrue(Path(report["m2_mail_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pkt03_m2_mail_report.json").is_file())

    def test_s2pjt01_lifecycle_state_passes_local_model_and_no_migration_gates(self) -> None:
        report = build_s2pjt01_lifecycle_state_report(
            generated_at=GENERATED_AT,
            runtime_dashboard_report=s2pit02_runtime_dashboard_report(),
            lifecycle_records=s2pjt01_lifecycle_records(),
            migration_plan=s2pjt01_migration_plan(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PJT01_LIFECYCLE_STATE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PJT01-LIFECYCLE")
        self.assertEqual(report["task_id"], "S2PJT01")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["runtime_dashboard_gate"], "pass")
        self.assertEqual(report["state_coverage_gate"], "pass")
        self.assertEqual(report["append_only_history_gate"], "pass")
        self.assertEqual(report["count_conservation_gate"], "pass")
        self.assertEqual(report["ledger_mapping_gate"], "pass")
        self.assertEqual(report["migration_plan_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(set(report["states_observed"]) & set(S2PJT01_REQUIRED_STATES), set(S2PJT01_REQUIRED_STATES))
        self.assertEqual(set(report["ledger_types_observed"]), set(S2PJT01_REQUIRED_LEDGER_TYPES))
        self.assertEqual(sum(report["state_counts"].values()), report["content_count"])
        self.assertTrue(report["s2pjt01_lifecycle_state_ready"])
        self.assertFalse(report["db_migration_executed"])
        self.assertFalse(report["schema_migration_allowed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["review_scheduler_enabled"])
        self.assertFalse(report["actual_roi_calculation_enabled"])
        self.assertFalse(validate_s2pjt01_lifecycle_state_report(report))

    def test_s2pjt01_lifecycle_state_blocks_missing_state_history_and_side_effects(self) -> None:
        records = s2pjt01_lifecycle_records()
        records = [record for record in records if record["current_state"] != "MASTERED"]
        records[0] = dict(
            records[0],
            content_id=records[1]["content_id"],
            state_history=[
                {"state": "REVIEW_DUE", "changed_at": "2026-06-24T12:00:00+10:00"},
                {"state": "QUEUED", "changed_at": "2026-06-24T11:00:00+10:00"},
            ],
            queue_mutation_allowed=True,
        )
        report = build_s2pjt01_lifecycle_state_report(
            generated_at=GENERATED_AT,
            runtime_dashboard_report={**s2pit02_runtime_dashboard_report(), "status": "blocked"},
            lifecycle_records=records,
            migration_plan=s2pjt01_migration_plan(db_migration_executed=True, rollback_supported=False),
            production_gate_state=s2pit02_production_gate_state(real_smtp_sent=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["runtime_dashboard_gate"], "blocked")
        self.assertEqual(report["state_coverage_gate"], "blocked")
        self.assertEqual(report["append_only_history_gate"], "blocked")
        self.assertEqual(report["count_conservation_gate"], "blocked")
        self.assertEqual(report["migration_plan_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("S2PIT02 runtime dashboard report must pass", joined)
        self.assertIn("missing lifecycle state: MASTERED", joined)
        self.assertIn("duplicate content_id", joined)
        self.assertIn("timestamps must be non-decreasing", joined)
        self.assertIn("queue_mutation_allowed", joined)
        self.assertIn("migration_plan.db_migration_executed", joined)
        self.assertIn("production_gate_state.real_smtp_sent", joined)
        self.assertTrue(validate_s2pjt01_lifecycle_state_report(report))

    def test_s2pjt01_lifecycle_state_persists_report_without_db_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pjt01_lifecycle_state(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                runtime_dashboard_report=s2pit02_runtime_dashboard_report(),
                lifecycle_records=s2pjt01_lifecycle_records(),
                migration_plan=s2pjt01_migration_plan(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pjt01_lifecycle_state_report(report))
            self.assertFalse(report["db_migration_executed"])
            self.assertFalse(report["schema_migration_allowed"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertTrue(Path(report["lifecycle_state_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pjt01_lifecycle_state_report.json").is_file())

    def test_s2pjt02_review_schedule_passes_due_counts_and_no_scheduler_gates(self) -> None:
        report = build_s2pjt02_review_schedule_report(
            generated_at=GENERATED_AT,
            service_date="2026-06-25",
            lifecycle_state_report=s2pjt01_lifecycle_state_report(),
            review_records=s2pjt02_review_records(),
            schedule_policy=s2pjt02_schedule_policy(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PJT02_REVIEW_SCHEDULE_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PJT02-REVIEW")
        self.assertEqual(report["task_id"], "S2PJT02")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["lifecycle_state_gate"], "pass")
        self.assertEqual(report["schedule_policy_gate"], "pass")
        self.assertEqual(report["review_record_gate"], "pass")
        self.assertEqual(report["due_count_gate"], "pass")
        self.assertEqual(report["deterministic_queue_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["computed_counts"], {"due_today": 1, "due_next_7_days": 2, "overdue": 1, "completed": 1})
        self.assertEqual([row["content_id"] for row in report["due_today_queue"]], ["content:today"])
        self.assertEqual([row["content_id"] for row in report["overdue_queue"]], ["content:overdue"])
        self.assertEqual(set(report["review_intervals_days"]), set(S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS))
        self.assertTrue(report["due_queue_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pjt02_review_schedule_ready"])
        self.assertFalse(report["review_scheduler_enabled"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(validate_s2pjt02_review_schedule_report(report))

    def test_s2pjt02_review_schedule_blocks_bad_counts_due_date_and_side_effects(self) -> None:
        records = s2pjt02_review_records()
        records[0] = dict(records[0], due_date="2026-06-24", scheduler_enabled=True)
        records[1] = dict(records[1], content_id=records[2]["content_id"], review_stage_days=2)
        report = build_s2pjt02_review_schedule_report(
            generated_at=GENERATED_AT,
            service_date="2026-06-25",
            lifecycle_state_report={**s2pjt01_lifecycle_state_report(), "status": "blocked"},
            review_records=records,
            schedule_policy=s2pjt02_schedule_policy(
                review_intervals_days=[1, 3, 7],
                expected_counts={"due_today": 9, "due_next_7_days": 9, "overdue": 9, "completed": 9},
            ),
            production_gate_state=s2pit02_production_gate_state(real_smtp_sent=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["lifecycle_state_gate"], "blocked")
        self.assertEqual(report["schedule_policy_gate"], "blocked")
        self.assertEqual(report["review_record_gate"], "blocked")
        self.assertEqual(report["due_count_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("S2PJT01 lifecycle state report must pass", joined)
        self.assertIn("missing default review intervals", joined)
        self.assertIn("review_stage_days", joined)
        self.assertIn("due_date must equal", joined)
        self.assertIn("duplicate review content_id", joined)
        self.assertIn("scheduler_enabled", joined)
        self.assertIn("due_today count mismatch", joined)
        self.assertIn("production_gate_state.real_smtp_sent", joined)
        self.assertTrue(validate_s2pjt02_review_schedule_report(report))

    def test_s2pjt02_review_schedule_persists_report_without_scheduler_installation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pjt02_review_schedule(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                lifecycle_state_report=s2pjt01_lifecycle_state_report(),
                review_records=s2pjt02_review_records(),
                schedule_policy=s2pjt02_schedule_policy(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pjt02_review_schedule_report(report))
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["public_schema_changed"])
            self.assertTrue(Path(report["review_schedule_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pjt02_review_schedule_report.json").is_file())

    def test_s2pjt03_action_asset_roi_passes_expected_and_actual_roi_gates(self) -> None:
        report = build_s2pjt03_action_asset_roi_report(
            generated_at=GENERATED_AT,
            service_date="2026-06-25",
            review_schedule_report=s2pjt02_review_schedule_report(),
            action_records=s2pjt03_action_records(),
            capability_assets=s2pjt03_capability_assets(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PJT03_ACTION_ROI_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PJT03-ROI")
        self.assertEqual(report["task_id"], "S2PJT03")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["review_schedule_gate"], "pass")
        self.assertEqual(report["action_window_gate"], "pass")
        self.assertEqual(report["expected_roi_gate"], "pass")
        self.assertEqual(report["actual_roi_gate"], "pass")
        self.assertEqual(report["asset_trace_gate"], "pass")
        self.assertEqual(report["deterministic_ledger_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["action_counts"], {"15m": 1, "2h": 1, "7d": 1, "30d": 1})
        self.assertEqual(report["actual_roi_status_counts"], {"not_calculable": 3, "calculated": 1})
        calculated = [row for row in report["action_records"] if row["actual_roi_status"] == "calculated"][0]
        self.assertEqual(calculated["actual_roi_value"], 1.5)
        not_calculable = [row for row in report["action_records"] if row["actual_roi_status"] == "not_calculable"]
        self.assertTrue(all(row["actual_roi_value"] is None for row in not_calculable))
        self.assertTrue(report["ledger_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pjt03_action_roi_ready"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(validate_s2pjt03_action_asset_roi_report(report))

    def test_s2pjt03_action_asset_roi_blocks_fake_precision_and_missing_evidence(self) -> None:
        actions = s2pjt03_action_records()
        actions[0] = {
            **actions[0],
            "horizon": "1h",
            "expected_roi": {"value": "too vague", "assumptions": [], "confidence": 1.5},
            "actual_roi": {"status": "not_calculable", "value": 0.42},
        }
        actions[1] = {
            **actions[1],
            "action_id": actions[2]["action_id"],
            "actual_roi": {"status": "calculated", "verifiable_cost": 0, "verifiable_benefit": 10},
        }
        report = build_s2pjt03_action_asset_roi_report(
            generated_at=GENERATED_AT,
            service_date="2026-06-25",
            review_schedule_report={**s2pjt02_review_schedule_report(), "status": "blocked"},
            action_records=actions,
            capability_assets=[{"asset_id": "", "content_id": "", "asset_type": "", "evidence_refs": []}],
            production_gate_state=s2pit02_production_gate_state(queue_mutation_allowed=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["review_schedule_gate"], "blocked")
        self.assertEqual(report["action_window_gate"], "blocked")
        self.assertEqual(report["expected_roi_gate"], "blocked")
        self.assertEqual(report["actual_roi_gate"], "blocked")
        self.assertEqual(report["asset_trace_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("S2PJT02 review schedule report must pass", joined)
        self.assertIn("horizon must be one of", joined)
        self.assertIn("expected_roi.assumptions", joined)
        self.assertIn("expected_roi.confidence", joined)
        self.assertIn("not_calculable actual ROI must not include a precise value", joined)
        self.assertIn("calculated actual ROI requires verifiable_cost", joined)
        self.assertIn("calculated actual ROI requires evidence_refs", joined)
        self.assertIn("duplicate action_id", joined)
        self.assertIn("missing required action windows", joined)
        self.assertIn("evidence_refs must be a non-empty list", joined)
        self.assertIn("production_gate_state.queue_mutation_allowed", joined)
        self.assertTrue(validate_s2pjt03_action_asset_roi_report(report))

    def test_s2pjt03_action_asset_roi_persists_report_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pjt03_action_asset_roi(
                state_dir=tmp,
                date="2026-06-25",
                generated_at=GENERATED_AT,
                review_schedule_report=s2pjt02_review_schedule_report(),
                action_records=s2pjt03_action_records(),
                capability_assets=s2pjt03_capability_assets(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pjt03_action_asset_roi_report(report))
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["public_schema_changed"])
            self.assertTrue(Path(report["action_roi_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pjt03_action_asset_roi_ledger_report.json").is_file())

    def test_s2pjt04_weekly_report_passes_traceable_sections_and_next_focus(self) -> None:
        report = build_s2pjt04_weekly_report(
            generated_at=GENERATED_AT,
            week_start="2026-06-22",
            week_end="2026-06-28",
            action_roi_report=s2pjt03_action_roi_report(),
            weekly_items=s2pjt04_weekly_items(),
            weekly_sections=s2pjt04_weekly_sections(),
            next_week_focus=s2pjt04_next_week_focus(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PJT04_WEEKLY_REPORT_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PJT04-WEEKLY")
        self.assertEqual(report["task_id"], "S2PJT04")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["action_roi_gate"], "pass")
        self.assertEqual(report["week_window_gate"], "pass")
        self.assertEqual(report["section_trace_gate"], "pass")
        self.assertEqual(report["state_trace_gate"], "pass")
        self.assertEqual(report["no_duplication_gate"], "pass")
        self.assertEqual(report["next_focus_gate"], "pass")
        self.assertEqual(report["deterministic_report_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["state_counts"], {"ACTION": 1, "REVIEW_DUE": 1, "ASSET": 1})
        self.assertEqual(report["section_counts"]["weekly_mainline"], 1)
        self.assertEqual(report["section_counts"]["review_summary"], 2)
        self.assertTrue(report["weekly_report_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pjt04_weekly_report_ready"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(validate_s2pjt04_weekly_report(report))

    def test_s2pjt04_weekly_report_blocks_duplicate_untraced_and_bad_focus(self) -> None:
        items = s2pjt04_weekly_items()
        items[0] = {**items[0], "observed_date": "2026-06-01", "actual_state": "", "evidence_refs": []}
        items.append({**items[1], "title": "duplicate content"})
        items.append(
            {
                "content_id": "content:untraced",
                "title": "Untraced",
                "observed_date": "2026-06-25",
                "actual_state": "ACTION",
                "section_tags": ["weekly_mainline"],
                "evidence_refs": ["local://untraced"],
            }
        )
        report = build_s2pjt04_weekly_report(
            generated_at=GENERATED_AT,
            week_start="2026-06-22",
            week_end="2026-07-05",
            action_roi_report={**s2pjt03_action_roi_report(), "status": "blocked"},
            weekly_items=items,
            weekly_sections=s2pjt04_weekly_sections(asset_summary={"summary": "", "content_ids": []}),
            next_week_focus=[{"focus_id": "", "source_content_ids": ["content:missing"], "priority": 8, "rationale": ""}],
            production_gate_state=s2pit02_production_gate_state(real_smtp_sent=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["action_roi_gate"], "blocked")
        self.assertEqual(report["week_window_gate"], "blocked")
        self.assertEqual(report["section_trace_gate"], "blocked")
        self.assertEqual(report["state_trace_gate"], "blocked")
        self.assertEqual(report["no_duplication_gate"], "blocked")
        self.assertEqual(report["next_focus_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("S2PJT03 action/asset/ROI report must pass", joined)
        self.assertIn("weekly report window must not exceed", joined)
        self.assertIn("observed_date must be inside", joined)
        self.assertIn("actual_state is required", joined)
        self.assertIn("evidence_refs must be a non-empty list", joined)
        self.assertIn("duplicate weekly content_id", joined)
        self.assertIn("not traceable to S2PJT03", joined)
        self.assertIn("weekly_sections.asset_summary.content_ids must be non-empty", joined)
        self.assertIn("source_content_ids not in weekly_items", joined)
        self.assertIn("priority must be between 1 and 5", joined)
        self.assertIn("production_gate_state.real_smtp_sent", joined)
        self.assertTrue(validate_s2pjt04_weekly_report(report))

    def test_s2pjt04_weekly_report_persists_report_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pjt04_weekly_report(
                state_dir=tmp,
                date="2026-06-28",
                generated_at=GENERATED_AT,
                week_start="2026-06-22",
                week_end="2026-06-28",
                action_roi_report=s2pjt03_action_roi_report(),
                weekly_items=s2pjt04_weekly_items(),
                weekly_sections=s2pjt04_weekly_sections(),
                next_week_focus=s2pjt04_next_week_focus(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pjt04_weekly_report(report))
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["public_schema_changed"])
            self.assertTrue(Path(report["weekly_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pjt04_weekly_report.json").is_file())

    def test_s2pjt05_monthly_report_passes_cognitive_roi_and_forecast_gates(self) -> None:
        report = build_s2pjt05_monthly_report(
            generated_at=GENERATED_AT,
            month_start="2026-06-01",
            month_end="2026-06-30",
            weekly_reports=[s2pjt04_weekly_report()],
            cognitive_snapshots=s2pjt05_cognitive_snapshots(),
            monthly_sections=s2pjt05_monthly_sections(),
            capability_growth=s2pjt05_capability_growth(),
            economic_conversions=s2pjt05_economic_conversions(),
            forecast_reviews=s2pjt05_forecast_reviews(),
            next_month_focus=s2pjt05_next_month_focus(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PJT05_MONTHLY_REPORT_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PJT05-MONTHLY")
        self.assertEqual(report["task_id"], "S2PJT05")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["weekly_report_gate"], "pass")
        self.assertEqual(report["month_window_gate"], "pass")
        self.assertEqual(report["cognitive_delta_gate"], "pass")
        self.assertEqual(report["capability_growth_gate"], "pass")
        self.assertEqual(report["conversion_trace_gate"], "pass")
        self.assertEqual(report["forecast_review_gate"], "pass")
        self.assertEqual(report["section_trace_gate"], "pass")
        self.assertEqual(report["deterministic_report_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertIn("content:done", report["monthly_content_ids"])
        self.assertEqual(report["calculated_conversion_count"], 1)
        self.assertEqual(report["economic_conversions"][0]["actual_roi_value"], 1.5)
        self.assertTrue(report["monthly_report_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pjt05_monthly_report_ready"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["queue_mutation_allowed"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(validate_s2pjt05_monthly_report(report))

    def test_s2pjt05_monthly_report_blocks_missing_delta_fake_roi_and_bad_forecast(self) -> None:
        conversion = {
            "conversion_id": "conversion:bad",
            "source_content_ids": ["content:missing"],
            "actual_roi_status": "calculated",
            "verifiable_cost": 0,
            "verifiable_benefit": 10,
        }
        report = build_s2pjt05_monthly_report(
            generated_at=GENERATED_AT,
            month_start="2026-06-01",
            month_end="2026-07-15",
            weekly_reports=[{**s2pjt04_weekly_report(), "status": "blocked"}],
            cognitive_snapshots={"month_start": {"summary": "", "viewpoint_ids": []}, "month_end": {"summary": "", "viewpoint_ids": []}, "changed_viewpoints": []},
            monthly_sections=s2pjt05_monthly_sections(economic_conversion={"summary": "", "content_ids": []}),
            capability_growth=[{"asset_id": "", "asset_type": "", "source_content_ids": ["content:missing"], "evidence_refs": []}],
            economic_conversions=[conversion],
            forecast_reviews=[{"prediction_id": "", "source_content_ids": ["content:missing"], "forecast": "", "outcome": "", "accuracy_score": 2, "evidence_refs": []}],
            next_month_focus=[{"focus_id": "", "source_content_ids": ["content:missing"], "priority": 8, "rationale": ""}],
            production_gate_state=s2pit02_production_gate_state(scheduler_enabled=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["weekly_report_gate"], "blocked")
        self.assertEqual(report["month_window_gate"], "blocked")
        self.assertEqual(report["cognitive_delta_gate"], "blocked")
        self.assertEqual(report["capability_growth_gate"], "blocked")
        self.assertEqual(report["conversion_trace_gate"], "blocked")
        self.assertEqual(report["forecast_review_gate"], "blocked")
        self.assertEqual(report["section_trace_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("weekly report 0 must be a passing S2PJT04 report", joined)
        self.assertIn("monthly report window must not exceed", joined)
        self.assertIn("changed_viewpoints must be a non-empty list", joined)
        self.assertIn("source_content_ids not in monthly weekly evidence", joined)
        self.assertIn("calculated conversion requires verifiable_cost", joined)
        self.assertIn("calculated conversion requires evidence_refs", joined)
        self.assertIn("requires at least one verifiable calculated conversion", joined)
        self.assertIn("accuracy_score must be between 0 and 1", joined)
        self.assertIn("production_gate_state.scheduler_enabled", joined)
        self.assertTrue(validate_s2pjt05_monthly_report(report))

    def test_s2pjt05_monthly_report_persists_report_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pjt05_monthly_report(
                state_dir=tmp,
                date="2026-06-30",
                generated_at=GENERATED_AT,
                month_start="2026-06-01",
                month_end="2026-06-30",
                weekly_reports=[s2pjt04_weekly_report()],
                cognitive_snapshots=s2pjt05_cognitive_snapshots(),
                monthly_sections=s2pjt05_monthly_sections(),
                capability_growth=s2pjt05_capability_growth(),
                economic_conversions=s2pjt05_economic_conversions(),
                forecast_reviews=s2pjt05_forecast_reviews(),
                next_month_focus=s2pjt05_next_month_focus(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pjt05_monthly_report(report))
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertFalse(report["public_schema_changed"])
            self.assertTrue(Path(report["monthly_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pjt05_monthly_report.json").is_file())

    def test_s2pht05_content_quality_gate_passes_gold_semantic_and_regression_gates(self) -> None:
        report = build_s2pht05_content_quality_gate_report(
            generated_at=GENERATED_AT,
            dependency_receipts=s2pht05_dependency_receipts(),
            gold_items=s2pht05_gold_items(),
            stage1_regression_checks=s2pht05_stage1_regression_checks(),
            manual_review_samples=s2pht05_manual_review_samples(),
            production_gate_state=s2pit02_production_gate_state(),
        )

        self.assertEqual(report["model_id"], S2PHT05_CONTENT_QUALITY_MODEL_ID)
        self.assertEqual(report["acceptance_id"], "ACC-S2PHT05-CONTENT-GATE")
        self.assertEqual(report["task_id"], "S2PHT05")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["dependency_receipt_gate"], "pass")
        self.assertEqual(report["gold_dimension_gate"], "pass")
        self.assertEqual(report["entailment_gate"], "pass")
        self.assertEqual(report["quote_location_gate"], "pass")
        self.assertEqual(report["template_rate_gate"], "pass")
        self.assertEqual(report["counterevidence_gate"], "pass")
        self.assertEqual(report["personal_action_gate"], "pass")
        self.assertEqual(report["stage1_regression_gate"], "pass")
        self.assertEqual(report["manual_review_gate"], "pass")
        self.assertEqual(report["deterministic_gate"], "pass")
        self.assertEqual(report["no_side_effect_gate"], "pass")
        self.assertEqual(report["gold_item_count"], 10)
        self.assertLessEqual(report["max_template_similarity_observed"], 0.35)
        self.assertTrue(report["quality_gate_hash"].startswith("sha256:"))
        self.assertTrue(report["s2pht05_content_quality_gate_ready"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(report["scheduler_enabled"])
        self.assertFalse(report["public_schema_changed"])
        self.assertFalse(validate_s2pht05_content_quality_gate_report(report))

    def test_s2pht05_content_quality_gate_blocks_low_quality_and_side_effects(self) -> None:
        gold_items = s2pht05_gold_items()
        gold_items[0]["dimension_scores"]["mechanism_depth"] = 3.0
        gold_items[0]["claim_entailment"] = "unsupported"
        gold_items[0]["quote_locations"] = []
        gold_items[0]["template_similarity"] = 0.9
        gold_items[0]["counterevidence_refs"] = []
        gold_items[0]["personal_action"] = {"action_id": "", "evidence_refs": []}
        report = build_s2pht05_content_quality_gate_report(
            generated_at=GENERATED_AT,
            dependency_receipts=[{**s2pht05_dependency_receipts()[0], "v7_2_revalidated": False}],
            gold_items=gold_items[:9],
            stage1_regression_checks=[{**s2pht05_stage1_regression_checks()[0], "status": "blocked"}],
            manual_review_samples=[{**s2pht05_manual_review_samples()[0], "verdict": "blocked"}],
            production_gate_state=s2pit02_production_gate_state(real_smtp_sent=True),
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["dependency_receipt_gate"], "blocked")
        self.assertEqual(report["gold_dimension_gate"], "blocked")
        self.assertEqual(report["entailment_gate"], "blocked")
        self.assertEqual(report["quote_location_gate"], "blocked")
        self.assertEqual(report["template_rate_gate"], "blocked")
        self.assertEqual(report["counterevidence_gate"], "blocked")
        self.assertEqual(report["personal_action_gate"], "blocked")
        self.assertEqual(report["stage1_regression_gate"], "blocked")
        self.assertEqual(report["manual_review_gate"], "blocked")
        self.assertEqual(report["no_side_effect_gate"], "blocked")
        joined = " ".join(report["blocking_reasons"])
        self.assertIn("missing S2PHT05 dependency receipts", joined)
        self.assertIn("mechanism_depth score must be >=", joined)
        self.assertIn("claim_entailment must be supported", joined)
        self.assertIn("quote_locations must be non-empty", joined)
        self.assertIn("template_similarity exceeds", joined)
        self.assertIn("counterevidence_refs must be non-empty", joined)
        self.assertIn("personal_action.action_id is required", joined)
        self.assertIn("missing Stage 1 regression checks", joined)
        self.assertIn("manual review verdict must be pass", joined)
        self.assertIn("production_gate_state.real_smtp_sent", joined)
        self.assertTrue(validate_s2pht05_content_quality_gate_report(report))

    def test_s2pht05_content_quality_gate_persists_report_without_production_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_s2pht05_content_quality_gate(
                state_dir=tmp,
                date="2026-06-26",
                generated_at=GENERATED_AT,
                dependency_receipts=s2pht05_dependency_receipts(),
                gold_items=s2pht05_gold_items(),
                stage1_regression_checks=s2pht05_stage1_regression_checks(),
                manual_review_samples=s2pht05_manual_review_samples(),
                production_gate_state=s2pit02_production_gate_state(),
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(validate_s2pht05_content_quality_gate_report(report))
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["scheduler_enabled"])
            self.assertFalse(report["queue_mutation_allowed"])
            self.assertTrue(Path(report["content_quality_gate_report_path"]).is_file())
            self.assertTrue((Path(tmp) / "stage2_s2pht05_content_quality_gate_report.json").is_file())

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
            self.assertEqual(report["delivery_package"]["email_template_contract"], "EMAIL_LEARNING_V1")
            self.assertIn("【先把论文讲成人话】", Path(report["email_preview_paths"]["plain"]).read_text(encoding="utf-8"))

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
            self.assertEqual(report["delivery_package"]["email_template_contract"], "EMAIL_LEARNING_V1")
            self.assertIn("【先把论文讲成人话】", email_preview)
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
            self.assertEqual(report["delivery_package"]["email_template_contract"], "EMAIL_LEARNING_V1")
            self.assertIn("【先把论文讲成人话】", email_preview)
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
            self.assertEqual(report["delivery_package"]["email_template_contract"], "EMAIL_LEARNING_V1")
            self.assertIn("【先把论文讲成人话】", email_preview)
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

    def test_cli_stage2_d2_source_domain_qualification_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            profile_report_path = Path(tmp) / "profile-report.json"
            engineering_report_path = Path(tmp) / "engineering-report.json"
            authoritative_report_path = Path(tmp) / "authoritative-report.json"
            replay_records_path = Path(tmp) / "replay-records.json"
            shadow_records_path = Path(tmp) / "shadow-records.json"
            forced_event_records_path = Path(tmp) / "forced-event-records.json"
            queue_records_path = Path(tmp) / "queue-records.json"
            profile_report_path.write_text(json.dumps(top_journal_profile_report(), ensure_ascii=False), encoding="utf-8")
            engineering_report_path.write_text(json.dumps(engineering_signal_report(), ensure_ascii=False), encoding="utf-8")
            authoritative_report_path.write_text(json.dumps(authoritative_report(), ensure_ascii=False), encoding="utf-8")
            replay_records_path.write_text(json.dumps({"replay_records": d2_replay_records()}, ensure_ascii=False), encoding="utf-8")
            shadow_records_path.write_text(json.dumps({"shadow_records": d2_shadow_records()}, ensure_ascii=False), encoding="utf-8")
            forced_event_records_path.write_text(json.dumps({"forced_event_records": d2_forced_event_records()}, ensure_ascii=False), encoding="utf-8")
            queue_records_path.write_text(json.dumps({"queue_explanation_records": d2_queue_explanation_records()}, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-d2-source-domain-qualification",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--profile-report",
                    str(profile_report_path),
                    "--engineering-signal-report",
                    str(engineering_report_path),
                    "--authoritative-report",
                    str(authoritative_report_path),
                    "--replay-records",
                    str(replay_records_path),
                    "--shadow-records",
                    str(shadow_records_path),
                    "--forced-event-records",
                    str(forced_event_records_path),
                    "--queue-explanation-records",
                    str(queue_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PCT07_D2_QUALIFICATION_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PCT07")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d2_source_domain_qualification_ready"])
        self.assertFalse(payload["d2_source_domain_accepted"])

    def test_cli_stage2_china_c0_source_foundation_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            d2_report_path = Path(tmp) / "d2-qualification-report.json"
            authority_records_path = Path(tmp) / "authority-records.json"
            d2_report_path.write_text(json.dumps(d2_qualification_report(), ensure_ascii=False), encoding="utf-8")
            authority_records_path.write_text(json.dumps({"authority_records": china_c0_authority_records()}, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-china-c0-source-foundation",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--d2-qualification-report",
                    str(d2_report_path),
                    "--authority-records",
                    str(authority_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PDT01_CHINA_C0_SOURCE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PDT01")
        self.assertEqual(payload["legacy_task_id"], "S2P3T01")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d3_c0_source_foundation_ready"])
        self.assertFalse(payload["d3_core_source_domain_accepted"])

    def test_cli_stage2_us_ta_source_foundation_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            agency_records_path = Path(tmp) / "agency-records.json"
            agency_records_path.write_text(json.dumps({"agency_records": us_ta_agency_records()}, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-us-ta-source-foundation",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--agency-records",
                    str(agency_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PET01_US_TA_SOURCE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PET01")
        self.assertEqual(payload["legacy_task_id"], "S2P4T01")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d4_us_ta_source_foundation_ready"])
        self.assertFalse(payload["d4_us_official_source_domain_accepted"])

    def test_cli_stage2_us_lg_legal_backbone_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            us_ta_report_path = Path(tmp) / "us-ta-source-foundation-report.json"
            legal_records_path = Path(tmp) / "legal-records.json"
            relation_records_path = Path(tmp) / "relation-records.json"
            us_ta_report_path.write_text(json.dumps(us_ta_source_foundation_report(), ensure_ascii=False), encoding="utf-8")
            legal_records_path.write_text(json.dumps({"legal_records": us_lg_legal_records()}, ensure_ascii=False), encoding="utf-8")
            relation_records_path.write_text(json.dumps({"relation_records": us_lg_relation_records()}, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-us-lg-legal-backbone",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--us-ta-source-foundation-report",
                    str(us_ta_report_path),
                    "--legal-records",
                    str(legal_records_path),
                    "--relation-records",
                    str(relation_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PET02_US_LG_BACKBONE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PET02")
        self.assertEqual(payload["legacy_task_id"], "S2P4T02")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d4_us_lg_legal_backbone_ready"])
        self.assertFalse(payload["d4_us_official_source_domain_accepted"])

    def test_cli_stage2_us_fm_source_backbone_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            us_lg_report_path = Path(tmp) / "us-lg-legal-backbone-report.json"
            finance_records_path = Path(tmp) / "finance-records.json"
            relation_records_path = Path(tmp) / "relation-records.json"
            us_lg_report_path.write_text(json.dumps(us_lg_legal_backbone_report(), ensure_ascii=False), encoding="utf-8")
            finance_records_path.write_text(json.dumps({"finance_records": us_fm_finance_records()}, ensure_ascii=False), encoding="utf-8")
            relation_records_path.write_text(json.dumps({"relation_records": us_fm_relation_records()}, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-us-fm-source-backbone",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--us-lg-legal-backbone-report",
                    str(us_lg_report_path),
                    "--finance-records",
                    str(finance_records_path),
                    "--relation-records",
                    str(relation_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PET03_US_FM_BACKBONE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PET03")
        self.assertEqual(payload["legacy_task_id"], "S2P4T03")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d4_us_fm_source_backbone_ready"])
        self.assertFalse(payload["d4_us_official_source_domain_accepted"])
        self.assertFalse(payload["automated_trading_enabled"])

    def test_cli_stage2_us_tp_d4_qualification_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            us_ta_report_path = Path(tmp) / "us-ta-source-foundation-report.json"
            us_lg_report_path = Path(tmp) / "us-lg-legal-backbone-report.json"
            us_fm_report_path = Path(tmp) / "us-fm-source-backbone-report.json"
            policy_records_path = Path(tmp) / "policy-records.json"
            replay_records_path = Path(tmp) / "replay-records.json"
            shadow_records_path = Path(tmp) / "shadow-records.json"
            board_route_records_path = Path(tmp) / "board-route-records.json"
            budget_records_path = Path(tmp) / "budget-records.json"
            us_ta_report_path.write_text(json.dumps(us_ta_source_foundation_report(), ensure_ascii=False), encoding="utf-8")
            us_lg_report_path.write_text(json.dumps(us_lg_legal_backbone_report(), ensure_ascii=False), encoding="utf-8")
            us_fm_report_path.write_text(json.dumps(us_fm_source_backbone_report(), ensure_ascii=False), encoding="utf-8")
            policy_records_path.write_text(json.dumps({"policy_records": us_tp_policy_records()}, ensure_ascii=False), encoding="utf-8")
            replay_records_path.write_text(json.dumps({"replay_records": d4_replay_records()}, ensure_ascii=False), encoding="utf-8")
            shadow_records_path.write_text(json.dumps({"shadow_records": d4_shadow_records()}, ensure_ascii=False), encoding="utf-8")
            board_route_records_path.write_text(json.dumps({"board_route_records": d4_board_route_records()}, ensure_ascii=False), encoding="utf-8")
            budget_records_path.write_text(json.dumps({"budget_records": d4_budget_records()}, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-us-tp-d4-qualification",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--us-ta-source-foundation-report",
                    str(us_ta_report_path),
                    "--us-lg-legal-backbone-report",
                    str(us_lg_report_path),
                    "--us-fm-source-backbone-report",
                    str(us_fm_report_path),
                    "--policy-records",
                    str(policy_records_path),
                    "--replay-records",
                    str(replay_records_path),
                    "--shadow-records",
                    str(shadow_records_path),
                    "--board-route-records",
                    str(board_route_records_path),
                    "--budget-records",
                    str(budget_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PET04_US_TP_D4_QUALIFICATION_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PET04")
        self.assertEqual(payload["legacy_task_id"], "S2P4T04")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d4_us_tp_and_qualification_ready"])
        self.assertFalse(payload["d4_source_domain_accepted"])
        self.assertFalse(payload["real_smtp_sent"])

    def test_cli_stage2_china_c1_department_source_map_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            c0_report_path = Path(tmp) / "c0-source-foundation-report.json"
            department_records_path = Path(tmp) / "department-records.json"
            c0_report_path.write_text(json.dumps(china_c0_source_foundation_report(), ensure_ascii=False), encoding="utf-8")
            department_records_path.write_text(json.dumps({"department_records": china_c1_department_records()}, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-china-c1-department-source-map",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--c0-source-foundation-report",
                    str(c0_report_path),
                    "--department-records",
                    str(department_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PDT02_CHINA_C1_SOURCE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PDT02")
        self.assertEqual(payload["legacy_task_id"], "S2P3T02")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d3_c1_department_source_map_ready"])
        self.assertFalse(payload["d3_core_source_domain_accepted"])

    def test_cli_stage2_china_legal_metadata_relation_shadow_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            c1_report_path = Path(tmp) / "c1-department-source-map-report.json"
            legal_records_path = Path(tmp) / "legal-records.json"
            relation_records_path = Path(tmp) / "relation-records.json"
            prior_conclusion_records_path = Path(tmp) / "prior-conclusion-records.json"
            c1_report_path.write_text(json.dumps(china_c1_department_source_map_report(), ensure_ascii=False), encoding="utf-8")
            legal_records_path.write_text(json.dumps({"legal_records": china_legal_records()}, ensure_ascii=False), encoding="utf-8")
            relation_records_path.write_text(json.dumps({"relation_records": china_legal_relation_records()}, ensure_ascii=False), encoding="utf-8")
            prior_conclusion_records_path.write_text(
                json.dumps({"prior_conclusion_records": china_prior_conclusion_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-china-legal-metadata-relation-shadow",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--c1-department-source-map-report",
                    str(c1_report_path),
                    "--legal-records",
                    str(legal_records_path),
                    "--relation-records",
                    str(relation_records_path),
                    "--prior-conclusion-records",
                    str(prior_conclusion_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PDT03_LEGAL_METADATA_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PDT03")
        self.assertEqual(payload["legacy_task_id"], "S2P3T03")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d3_legal_metadata_relation_shadow_ready"])
        self.assertFalse(payload["d3_core_source_domain_accepted"])

    def test_cli_stage2_china_d3_readiness_review_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            c0_report_path = Path(tmp) / "c0-source-foundation-report.json"
            c1_report_path = Path(tmp) / "c1-department-source-map-report.json"
            legal_report_path = Path(tmp) / "legal-metadata-relation-report.json"
            replay_records_path = Path(tmp) / "d3-replay-records.json"
            shadow_records_path = Path(tmp) / "d3-shadow-records.json"
            board_route_records_path = Path(tmp) / "d3-board-route-records.json"
            c0_report_path.write_text(json.dumps(china_c0_source_foundation_report(), ensure_ascii=False), encoding="utf-8")
            c1_report_path.write_text(json.dumps(china_c1_department_source_map_report(), ensure_ascii=False), encoding="utf-8")
            legal_report_path.write_text(json.dumps(china_legal_metadata_relation_report(), ensure_ascii=False), encoding="utf-8")
            replay_records_path.write_text(json.dumps({"replay_records": china_d3_replay_records()}, ensure_ascii=False), encoding="utf-8")
            shadow_records_path.write_text(json.dumps({"shadow_records": china_d3_shadow_records()}, ensure_ascii=False), encoding="utf-8")
            board_route_records_path.write_text(
                json.dumps({"board_route_records": china_d3_board_route_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-china-d3-readiness-review",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-24",
                    "--generated-at",
                    GENERATED_AT,
                    "--c0-source-foundation-report",
                    str(c0_report_path),
                    "--c1-department-source-map-report",
                    str(c1_report_path),
                    "--legal-metadata-relation-report",
                    str(legal_report_path),
                    "--replay-records",
                    str(replay_records_path),
                    "--shadow-records",
                    str(shadow_records_path),
                    "--board-route-records",
                    str(board_route_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PDT04_D3_READINESS_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PDT04")
        self.assertEqual(payload["legacy_task_id"], "S2P3T04")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["d3_core_readiness_review_ready"])
        self.assertFalse(payload["d3_core_source_domain_accepted"])

    def test_cli_stage2_china_provincial_template_coverage_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            d3_report_path = Path(tmp) / "d3-readiness-review-report.json"
            provincial_records_path = Path(tmp) / "provincial-records.json"
            d3_report_path.write_text(json.dumps(china_d3_readiness_report(), ensure_ascii=False), encoding="utf-8")
            provincial_records_path.write_text(
                json.dumps({"provincial_records": china_provincial_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-china-provincial-template-coverage",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--d3-readiness-review-report",
                    str(d3_report_path),
                    "--provincial-records",
                    str(provincial_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PFT01_CHINA_PROVINCIAL_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PFT01")
        self.assertEqual(payload["legacy_task_id"], "S2P5T01")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["s2pf_provincial_template_coverage_ready"])
        self.assertFalse(payload["d3_full_source_domain_accepted"])

    def test_cli_stage2_hk_mo_independent_profile_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            provincial_report_path = Path(tmp) / "provincial-template-report.json"
            jurisdiction_profiles_path = Path(tmp) / "jurisdiction-profiles.json"
            provincial_report_path.write_text(json.dumps(china_provincial_template_report(), ensure_ascii=False), encoding="utf-8")
            jurisdiction_profiles_path.write_text(
                json.dumps({"jurisdiction_profiles": hk_mo_jurisdiction_profiles()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-hk-mo-independent-profile",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--provincial-template-coverage-report",
                    str(provincial_report_path),
                    "--jurisdiction-profiles",
                    str(jurisdiction_profiles_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PFT02_HK_MO_PROFILE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PFT02")
        self.assertEqual(payload["legacy_task_id"], "S2P5T02")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["s2pf_hk_mo_profile_ready"])
        self.assertTrue(payload["hk_mo_profile_modeled"])
        self.assertFalse(payload["d3_full_source_domain_accepted"])

    def test_cli_stage2_key_city_coverage_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            hk_mo_report_path = Path(tmp) / "hk-mo-profile-report.json"
            city_records_path = Path(tmp) / "city-records.json"
            hk_mo_report_path.write_text(json.dumps(hk_mo_profile_report(), ensure_ascii=False), encoding="utf-8")
            city_records_path.write_text(
                json.dumps({"city_records": key_city_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-key-city-coverage",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--hk-mo-profile-report",
                    str(hk_mo_report_path),
                    "--city-records",
                    str(city_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PFT03_KEY_CITY_COVERAGE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PFT03")
        self.assertEqual(payload["legacy_task_id"], "S2P5T03")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["required_city_count"], 24)
        self.assertTrue(payload["s2pf_key_city_coverage_ready"])
        self.assertTrue(payload["city_coverage_modeled"])
        self.assertFalse(payload["d3_full_source_domain_accepted"])

    def test_cli_stage2_special_zone_discovery_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            key_city_report_path = Path(tmp) / "key-city-coverage-report.json"
            zone_records_path = Path(tmp) / "zone-records.json"
            key_city_report_path.write_text(json.dumps(key_city_coverage_report(), ensure_ascii=False), encoding="utf-8")
            zone_records_path.write_text(
                json.dumps({"zone_records": special_zone_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-special-zone-discovery",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--key-city-coverage-report",
                    str(key_city_report_path),
                    "--zone-records",
                    str(zone_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PFT04_SPECIAL_ZONE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PFT04")
        self.assertEqual(payload["legacy_task_id"], "S2P5T04")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["required_zone_count"], 10)
        self.assertTrue(payload["s2pf_special_zone_discovery_ready"])
        self.assertTrue(payload["special_zone_discovery_modeled"])
        self.assertFalse(payload["special_zone_discovery_enabled"])
        self.assertFalse(payload["d3_full_source_domain_accepted"])

    def test_cli_stage2_d3_full_governance_qualification_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            d3_report_path = Path(tmp) / "d3-readiness-report.json"
            provincial_report_path = Path(tmp) / "provincial-report.json"
            hk_mo_report_path = Path(tmp) / "hk-mo-report.json"
            key_city_report_path = Path(tmp) / "key-city-report.json"
            zone_report_path = Path(tmp) / "zone-report.json"
            governance_records_path = Path(tmp) / "governance-records.json"
            d3_report_path.write_text(json.dumps(china_d3_readiness_report(), ensure_ascii=False), encoding="utf-8")
            provincial_report_path.write_text(json.dumps(china_provincial_template_report(), ensure_ascii=False), encoding="utf-8")
            hk_mo_report_path.write_text(json.dumps(hk_mo_profile_report(), ensure_ascii=False), encoding="utf-8")
            key_city_report_path.write_text(json.dumps(key_city_coverage_report(), ensure_ascii=False), encoding="utf-8")
            zone_report_path.write_text(json.dumps(special_zone_discovery_report(), ensure_ascii=False), encoding="utf-8")
            governance_records_path.write_text(
                json.dumps({"governance_records": d3_full_governance_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-d3-full-governance-qualification",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--d3-readiness-review-report",
                    str(d3_report_path),
                    "--provincial-template-coverage-report",
                    str(provincial_report_path),
                    "--hk-mo-profile-report",
                    str(hk_mo_report_path),
                    "--key-city-coverage-report",
                    str(key_city_report_path),
                    "--special-zone-discovery-report",
                    str(zone_report_path),
                    "--governance-records",
                    str(governance_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PFT05_D3_FULL_GOVERNANCE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PFT05")
        self.assertEqual(payload["legacy_task_id"], "S2P5T05")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["s2pf_d3_full_governance_qualification_ready"])
        self.assertTrue(payload["d3_full_source_domain_qualified"])
        self.assertFalse(payload["d3_full_source_domain_accepted"])
        self.assertFalse(payload["stage2_production_accepted"])

    def test_cli_stage2_evidence_packet_v2_compatibility_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            domain_reports_path = Path(tmp) / "source-domain-reports.json"
            packet_records_path = Path(tmp) / "packet-records.json"
            domain_reports_path.write_text(
                json.dumps({"source_domain_reports": evidence_packet_domain_reports()}, ensure_ascii=False),
                encoding="utf-8",
            )
            packet_records_path.write_text(
                json.dumps({"packet_records": evidence_packet_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-evidence-packet-v2-compatibility",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--source-domain-reports",
                    str(domain_reports_path),
                    "--packet-records",
                    str(packet_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PGT01_EVIDENCE_PACKET_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PGT01")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["packet_version"], "EvidencePacketV2")
        self.assertTrue(payload["s2pgt01_evidence_packet_v2_compatibility_ready"])
        self.assertFalse(payload["public_schema_changed"])
        self.assertFalse(payload["schema_migration_required"])
        self.assertFalse(payload["production_affected"])
        self.assertFalse(payload["real_smtp_sent"])

    def test_cli_stage2_knowledge_graph_spine_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            evidence_packet_path = Path(tmp) / "evidence-packet-report.json"
            identity_records_path = Path(tmp) / "identity-records.json"
            relation_records_path = Path(tmp) / "relation-records.json"
            evidence_packet_path.write_text(
                json.dumps(
                    build_s2pgt01_evidence_packet_v2_compatibility_report(
                        generated_at=GENERATED_AT,
                        source_domain_reports=evidence_packet_domain_reports(),
                        packet_records=evidence_packet_records(),
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            identity_records_path.write_text(
                json.dumps({"identity_records": knowledge_graph_identity_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            relation_records_path.write_text(
                json.dumps({"relation_records": knowledge_graph_relation_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-knowledge-graph-spine",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--evidence-packet-report",
                    str(evidence_packet_path),
                    "--identity-records",
                    str(identity_records_path),
                    "--relation-records",
                    str(relation_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PGT02_KNOWLEDGE_GRAPH_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PGT02")
        self.assertEqual(payload["legacy_task_id"], "S2P6T01")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["identifier_coverage_gate"], "pass")
        self.assertEqual(payload["canonical_dedupe_gate"], "pass")
        self.assertEqual(payload["relation_evidence_gate"], "pass")
        self.assertEqual(payload["idempotent_update_gate"], "pass")
        self.assertTrue(payload["s2pgt02_knowledge_graph_spine_ready"])
        self.assertFalse(payload["public_schema_changed"])
        self.assertFalse(payload["schema_migration_required"])
        self.assertFalse(payload["production_affected"])
        self.assertFalse(payload["real_smtp_sent"])

    def test_cli_stage2_source_board_routing_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            evidence_packet_path = Path(tmp) / "evidence-packet-report.json"
            route_records_path = Path(tmp) / "route-records.json"
            evidence_packet_path.write_text(
                json.dumps(
                    build_s2pgt01_evidence_packet_v2_compatibility_report(
                        generated_at=GENERATED_AT,
                        source_domain_reports=evidence_packet_domain_reports(),
                        packet_records=evidence_packet_records(),
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            route_records_path.write_text(
                json.dumps({"route_records": source_board_route_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-source-board-routing",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--evidence-packet-report",
                    str(evidence_packet_path),
                    "--route-records",
                    str(route_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PGT03_ROUTING_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PGT03")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["source_domain_coverage_gate"], "pass")
        self.assertEqual(payload["primary_board_coverage_gate"], "pass")
        self.assertEqual(payload["cross_cutting_board_coverage_gate"], "pass")
        self.assertEqual(payload["route_reason_gate"], "pass")
        self.assertTrue(payload["s2pgt03_source_board_routing_ready"])
        self.assertFalse(payload["public_schema_changed"])
        self.assertFalse(payload["schema_migration_required"])
        self.assertFalse(payload["production_affected"])
        self.assertFalse(payload["real_smtp_sent"])

    def test_cli_stage2_delta_resonance_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            routing_report_path = Path(tmp) / "routing-report.json"
            delta_records_path = Path(tmp) / "delta-records.json"
            routing_report_path.write_text(
                json.dumps(
                    build_s2pgt03_source_board_routing_report(
                        generated_at=GENERATED_AT,
                        evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                            generated_at=GENERATED_AT,
                            source_domain_reports=evidence_packet_domain_reports(),
                            packet_records=evidence_packet_records(),
                        ),
                        route_records=source_board_route_records(),
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            delta_records_path.write_text(
                json.dumps({"delta_records": delta_resonance_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-delta-resonance",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--routing-report",
                    str(routing_report_path),
                    "--delta-records",
                    str(delta_records_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PGT04_DELTA_RESONANCE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PGT04")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["upstream_routing_gate"], "pass")
        self.assertEqual(payload["delta_type_coverage_gate"], "pass")
        self.assertEqual(payload["support_refute_gate"], "pass")
        self.assertEqual(payload["resonance_group_gate"], "pass")
        self.assertTrue(payload["s2pgt04_delta_resonance_ready"])
        self.assertFalse(payload["public_schema_changed"])
        self.assertFalse(payload["schema_migration_required"])
        self.assertFalse(payload["production_affected"])
        self.assertFalse(payload["real_smtp_sent"])
        self.assertFalse(payload["email_frontstage_changed"])

    def test_cli_stage2_cross_board_calibration_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            delta_report_path = Path(tmp) / "delta-report.json"
            queue_candidates_path = Path(tmp) / "queue-candidates.json"
            delta_report_path.write_text(
                json.dumps(
                    build_s2pgt04_delta_resonance_report(
                        generated_at=GENERATED_AT,
                        routing_report=build_s2pgt03_source_board_routing_report(
                            generated_at=GENERATED_AT,
                            evidence_packet_report=build_s2pgt01_evidence_packet_v2_compatibility_report(
                                generated_at=GENERATED_AT,
                                source_domain_reports=evidence_packet_domain_reports(),
                                packet_records=evidence_packet_records(),
                            ),
                            route_records=source_board_route_records(),
                        ),
                        delta_records=delta_resonance_records(),
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            queue_candidates_path.write_text(
                json.dumps({"queue_candidate_records": queue_candidate_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            with redirect_stdout(buffer):
                result = main([
                    "stage2-cross-board-calibration",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--delta-resonance-report",
                    str(delta_report_path),
                    "--queue-candidates",
                    str(queue_candidates_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PGT05_CALIBRATION_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PGT05")
        self.assertEqual(payload["legacy_task_id"], "S2P6T02")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["upstream_delta_resonance_gate"], "pass")
        self.assertEqual(payload["percentile_calibration_gate"], "pass")
        self.assertEqual(payload["source_balance_gate"], "pass")
        self.assertEqual(payload["waiting_credit_gate"], "pass")
        self.assertEqual(payload["queue_reason_gate"], "pass")
        self.assertEqual(payload["deterministic_order_gate"], "pass")
        self.assertTrue(payload["s2pgt05_calibration_ready"])
        self.assertFalse(payload["public_schema_changed"])
        self.assertFalse(payload["queue_mutation_allowed"])
        self.assertFalse(payload["ranking_algorithm_changed"])
        self.assertFalse(payload["production_affected"])
        self.assertFalse(payload["real_smtp_sent"])
        self.assertFalse(payload["email_frontstage_changed"])

    def test_cli_stage2_user_center_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            storage_path = Path(tmp) / "storage-inspect.json"
            storage_path.write_text(json.dumps(s2pit01_storage_inspect(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-user-center",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--controls",
                    "arxiv-daily-push/config/owner_controls.yaml",
                    "--storage-inspect-report",
                    str(storage_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PIT01_USER_CENTER_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PIT01")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["one_edit_directory_gate"], "pass")
        self.assertEqual(payload["click_depth_gate"], "pass")
        self.assertTrue(payload["s2pit01_user_center_ready"])
        self.assertFalse(payload["schema_migration_allowed"])
        self.assertFalse(payload["source_adapter_changed"])
        self.assertFalse(payload["stage2_production_accepted"])

    def test_cli_stage2_runtime_dashboard_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            user_center_path = tmp_path / "user-center.json"
            runtime_path = tmp_path / "runtime-audit.json"
            watchdog_path = tmp_path / "watchdog.json"
            storage_path = tmp_path / "storage-inspect.json"
            gate_path = tmp_path / "production-gate.json"
            user_center_path.write_text(json.dumps(s2pit01_user_center_report(), ensure_ascii=False), encoding="utf-8")
            runtime_path.write_text(json.dumps(s2pit02_runtime_report("runtime_audit"), ensure_ascii=False), encoding="utf-8")
            watchdog_path.write_text(json.dumps(s2pit02_runtime_report("watchdog"), ensure_ascii=False), encoding="utf-8")
            storage_path.write_text(json.dumps(s2pit01_storage_inspect(), ensure_ascii=False), encoding="utf-8")
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-runtime-dashboard",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--user-center-report",
                    str(user_center_path),
                    "--runtime-audit-report",
                    str(runtime_path),
                    "--watchdog-report",
                    str(watchdog_path),
                    "--storage-inspect-report",
                    str(storage_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PIT02_RUNTIME_DASHBOARD_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PIT02")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["runtime_state_gate"], "pass")
        self.assertEqual(payload["production_boundary_gate"], "pass")
        self.assertTrue(payload["s2pit02_runtime_dashboard_ready"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_source_model_view_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            user_center_path = tmp_path / "user-center.json"
            source_domains_path = tmp_path / "source-domains.json"
            reading_boards_path = tmp_path / "reading-boards.json"
            parameters_path = tmp_path / "parameters.json"
            queue_view_path = tmp_path / "queue-view.json"
            gate_path = tmp_path / "production-gate.json"
            user_center_path.write_text(json.dumps(s2pit01_user_center_report(), ensure_ascii=False), encoding="utf-8")
            source_domains_path.write_text(
                json.dumps({"source_domain_records": s2pit03_source_domains()}, ensure_ascii=False),
                encoding="utf-8",
            )
            reading_boards_path.write_text(
                json.dumps({"reading_board_records": s2pit03_reading_boards()}, ensure_ascii=False),
                encoding="utf-8",
            )
            parameters_path.write_text(
                json.dumps({"parameter_records": s2pit03_parameter_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            queue_view_path.write_text(
                json.dumps({"queue_view_records": s2pit03_queue_view_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-source-model-view",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-26",
                    "--generated-at",
                    GENERATED_AT,
                    "--user-center-report",
                    str(user_center_path),
                    "--source-domains",
                    str(source_domains_path),
                    "--reading-boards",
                    str(reading_boards_path),
                    "--parameters",
                    str(parameters_path),
                    "--queue-view",
                    str(queue_view_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PIT03_SOURCE_MODEL_VIEW_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PIT03")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["parameter_disclosure_gate"], "pass")
        self.assertEqual(payload["queue_view_gate"], "pass")
        self.assertTrue(payload["s2pit03_source_model_view_ready"])
        self.assertFalse(payload["source_adapter_changed"])
        self.assertFalse(payload["queue_mutation_allowed"])

    def test_cli_stage2_content_ledger_view_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runtime_dashboard_path = tmp_path / "runtime-dashboard.json"
            source_model_path = tmp_path / "source-model.json"
            lifecycle_path = tmp_path / "lifecycle.json"
            review_path = tmp_path / "review.json"
            action_roi_path = tmp_path / "action-roi.json"
            ledger_path = tmp_path / "ledger-records.json"
            gate_path = tmp_path / "production-gate.json"
            runtime_dashboard_path.write_text(json.dumps(s2pit02_runtime_dashboard_report(), ensure_ascii=False), encoding="utf-8")
            source_model_path.write_text(json.dumps(s2pit03_source_model_view_report(), ensure_ascii=False), encoding="utf-8")
            lifecycle_path.write_text(json.dumps(s2pjt01_lifecycle_state_report(), ensure_ascii=False), encoding="utf-8")
            review_path.write_text(json.dumps(s2pjt02_review_schedule_report(), ensure_ascii=False), encoding="utf-8")
            action_roi_path.write_text(json.dumps(s2pjt03_action_roi_report(), ensure_ascii=False), encoding="utf-8")
            ledger_path.write_text(
                json.dumps({"ledger_records": s2pit04_ledger_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-content-ledger-view",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-26",
                    "--generated-at",
                    GENERATED_AT,
                    "--runtime-dashboard-report",
                    str(runtime_dashboard_path),
                    "--source-model-view-report",
                    str(source_model_path),
                    "--lifecycle-state-report",
                    str(lifecycle_path),
                    "--review-schedule-report",
                    str(review_path),
                    "--action-roi-report",
                    str(action_roi_path),
                    "--ledger-records",
                    str(ledger_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PIT04_CONTENT_LEDGER_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PIT04")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["ledger_record_count"], 3)
        self.assertTrue(payload["s2pit04_content_ledger_ready"])
        self.assertFalse(payload["real_smtp_sent"])
        self.assertFalse(payload["scheduler_enabled"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_mail_contract_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            content_quality_path = tmp_path / "content-quality.json"
            content_ledger_path = tmp_path / "content-ledger.json"
            action_roi_path = tmp_path / "action-roi.json"
            mail_contracts_path = tmp_path / "mail-contracts.json"
            gate_path = tmp_path / "production-gate.json"
            content_quality_path.write_text(json.dumps(s2pht05_content_quality_gate_report(), ensure_ascii=False), encoding="utf-8")
            content_ledger_path.write_text(json.dumps(s2pit04_content_ledger_report(), ensure_ascii=False), encoding="utf-8")
            action_roi_path.write_text(json.dumps(s2pjt03_action_roi_report(), ensure_ascii=False), encoding="utf-8")
            mail_contracts_path.write_text(
                json.dumps({"mail_contracts": s2pkt01_mail_contracts()}, ensure_ascii=False),
                encoding="utf-8",
            )
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-mail-contract",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-26",
                    "--generated-at",
                    GENERATED_AT,
                    "--content-quality-report",
                    str(content_quality_path),
                    "--content-ledger-report",
                    str(content_ledger_path),
                    "--action-roi-report",
                    str(action_roi_path),
                    "--mail-contracts",
                    str(mail_contracts_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PKT01_MAIL_CONTRACT_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PKT01")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["mail_product_count"], 4)
        self.assertTrue(payload["s2pkt01_mail_contract_ready"])
        self.assertFalse(payload["real_smtp_sent"])
        self.assertFalse(payload["smtp_transport_allowed"])
        self.assertFalse(payload["scheduler_enabled"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_m1_mail_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            mail_contract_path = tmp_path / "mail-contract-report.json"
            content_quality_path = tmp_path / "content-quality.json"
            content_ledger_path = tmp_path / "content-ledger.json"
            action_roi_path = tmp_path / "action-roi.json"
            m1_record_path = tmp_path / "m1-record.json"
            gate_path = tmp_path / "production-gate.json"
            mail_contract_path.write_text(json.dumps(s2pkt01_mail_contract_report(), ensure_ascii=False), encoding="utf-8")
            content_quality_path.write_text(json.dumps(s2pht05_content_quality_gate_report(), ensure_ascii=False), encoding="utf-8")
            content_ledger_path.write_text(json.dumps(s2pit04_content_ledger_report(), ensure_ascii=False), encoding="utf-8")
            action_roi_path.write_text(json.dumps(s2pjt03_action_roi_report(), ensure_ascii=False), encoding="utf-8")
            m1_record_path.write_text(json.dumps(s2pkt02_m1_mail_record(), ensure_ascii=False), encoding="utf-8")
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-m1-mail",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-26",
                    "--generated-at",
                    GENERATED_AT,
                    "--mail-contract-report",
                    str(mail_contract_path),
                    "--content-quality-report",
                    str(content_quality_path),
                    "--content-ledger-report",
                    str(content_ledger_path),
                    "--action-roi-report",
                    str(action_roi_path),
                    "--m1-mail-record",
                    str(m1_record_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PKT02_M1_MAIL_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PKT02")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["mail_product_id"], "M1")
        self.assertEqual(payload["section_count"], 5)
        self.assertEqual(payload["action_windows"], ["15m", "2h"])
        self.assertTrue(payload["s2pkt02_m1_mail_ready"])
        self.assertFalse(payload["real_smtp_sent"])
        self.assertFalse(payload["smtp_transport_allowed"])
        self.assertFalse(payload["scheduler_enabled"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_m2_mail_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            mail_contract_path = tmp_path / "mail-contract-report.json"
            content_quality_path = tmp_path / "content-quality.json"
            content_ledger_path = tmp_path / "content-ledger.json"
            action_roi_path = tmp_path / "action-roi.json"
            m2_record_path = tmp_path / "m2-record.json"
            gate_path = tmp_path / "production-gate.json"
            mail_contract_path.write_text(json.dumps(s2pkt01_mail_contract_report(), ensure_ascii=False), encoding="utf-8")
            content_quality_path.write_text(json.dumps(s2pht05_content_quality_gate_report(), ensure_ascii=False), encoding="utf-8")
            content_ledger_path.write_text(json.dumps(s2pit04_content_ledger_report(), ensure_ascii=False), encoding="utf-8")
            action_roi_path.write_text(json.dumps(s2pjt03_action_roi_report(), ensure_ascii=False), encoding="utf-8")
            m2_record_path.write_text(json.dumps(s2pkt03_m2_mail_record(), ensure_ascii=False), encoding="utf-8")
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-m2-mail",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-26",
                    "--generated-at",
                    GENERATED_AT,
                    "--mail-contract-report",
                    str(mail_contract_path),
                    "--content-quality-report",
                    str(content_quality_path),
                    "--content-ledger-report",
                    str(content_ledger_path),
                    "--action-roi-report",
                    str(action_roi_path),
                    "--m2-mail-record",
                    str(m2_record_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PKT03_M2_MAIL_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PKT03")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["mail_product_id"], "M2")
        self.assertEqual(payload["section_count"], 5)
        self.assertEqual(payload["action_windows"], ["2h", "7d"])
        self.assertTrue(payload["s2pkt03_m2_mail_ready"])
        self.assertFalse(payload["real_smtp_sent"])
        self.assertFalse(payload["smtp_transport_allowed"])
        self.assertFalse(payload["scheduler_enabled"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_lifecycle_state_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runtime_dashboard_path = tmp_path / "runtime-dashboard.json"
            lifecycle_records_path = tmp_path / "lifecycle-records.json"
            migration_plan_path = tmp_path / "migration-plan.json"
            gate_path = tmp_path / "production-gate.json"
            runtime_dashboard_path.write_text(json.dumps(s2pit02_runtime_dashboard_report(), ensure_ascii=False), encoding="utf-8")
            lifecycle_records_path.write_text(
                json.dumps({"lifecycle_records": s2pjt01_lifecycle_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            migration_plan_path.write_text(json.dumps(s2pjt01_migration_plan(), ensure_ascii=False), encoding="utf-8")
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-lifecycle-state",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--runtime-dashboard-report",
                    str(runtime_dashboard_path),
                    "--lifecycle-records",
                    str(lifecycle_records_path),
                    "--migration-plan",
                    str(migration_plan_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PJT01_LIFECYCLE_STATE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PJT01")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["state_coverage_gate"], "pass")
        self.assertEqual(payload["migration_plan_gate"], "pass")
        self.assertTrue(payload["s2pjt01_lifecycle_state_ready"])
        self.assertFalse(payload["db_migration_executed"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_review_schedule_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lifecycle_path = tmp_path / "lifecycle-state.json"
            review_records_path = tmp_path / "review-records.json"
            schedule_policy_path = tmp_path / "schedule-policy.json"
            gate_path = tmp_path / "production-gate.json"
            lifecycle_path.write_text(json.dumps(s2pjt01_lifecycle_state_report(), ensure_ascii=False), encoding="utf-8")
            review_records_path.write_text(
                json.dumps({"review_records": s2pjt02_review_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            schedule_policy_path.write_text(json.dumps(s2pjt02_schedule_policy(), ensure_ascii=False), encoding="utf-8")
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-review-schedule",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--lifecycle-state-report",
                    str(lifecycle_path),
                    "--review-records",
                    str(review_records_path),
                    "--schedule-policy",
                    str(schedule_policy_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PJT02_REVIEW_SCHEDULE_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PJT02")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["computed_counts"]["due_today"], 1)
        self.assertEqual(payload["computed_counts"]["due_next_7_days"], 2)
        self.assertTrue(payload["s2pjt02_review_schedule_ready"])
        self.assertFalse(payload["scheduler_enabled"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_action_roi_ledger_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            review_schedule_path = tmp_path / "review-schedule.json"
            action_records_path = tmp_path / "action-records.json"
            capability_assets_path = tmp_path / "capability-assets.json"
            gate_path = tmp_path / "production-gate.json"
            review_schedule_path.write_text(json.dumps(s2pjt02_review_schedule_report(), ensure_ascii=False), encoding="utf-8")
            action_records_path.write_text(
                json.dumps({"action_records": s2pjt03_action_records()}, ensure_ascii=False),
                encoding="utf-8",
            )
            capability_assets_path.write_text(
                json.dumps({"capability_assets": s2pjt03_capability_assets()}, ensure_ascii=False),
                encoding="utf-8",
            )
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-action-roi-ledger",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-25",
                    "--generated-at",
                    GENERATED_AT,
                    "--review-schedule-report",
                    str(review_schedule_path),
                    "--action-records",
                    str(action_records_path),
                    "--capability-assets",
                    str(capability_assets_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PJT03_ACTION_ROI_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PJT03")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["action_counts"]["15m"], 1)
        self.assertEqual(payload["actual_roi_status_counts"]["calculated"], 1)
        self.assertTrue(payload["s2pjt03_action_roi_ready"])
        self.assertFalse(payload["scheduler_enabled"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_weekly_report_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            action_roi_path = tmp_path / "action-roi.json"
            weekly_items_path = tmp_path / "weekly-items.json"
            weekly_sections_path = tmp_path / "weekly-sections.json"
            next_focus_path = tmp_path / "next-focus.json"
            gate_path = tmp_path / "production-gate.json"
            action_roi_path.write_text(json.dumps(s2pjt03_action_roi_report(), ensure_ascii=False), encoding="utf-8")
            weekly_items_path.write_text(
                json.dumps({"weekly_items": s2pjt04_weekly_items()}, ensure_ascii=False),
                encoding="utf-8",
            )
            weekly_sections_path.write_text(json.dumps(s2pjt04_weekly_sections(), ensure_ascii=False), encoding="utf-8")
            next_focus_path.write_text(
                json.dumps({"next_week_focus": s2pjt04_next_week_focus()}, ensure_ascii=False),
                encoding="utf-8",
            )
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-weekly-report",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-28",
                    "--generated-at",
                    GENERATED_AT,
                    "--week-start",
                    "2026-06-22",
                    "--week-end",
                    "2026-06-28",
                    "--action-roi-report",
                    str(action_roi_path),
                    "--weekly-items",
                    str(weekly_items_path),
                    "--weekly-sections",
                    str(weekly_sections_path),
                    "--next-week-focus",
                    str(next_focus_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PJT04_WEEKLY_REPORT_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PJT04")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["state_counts"]["ASSET"], 1)
        self.assertEqual(payload["section_counts"]["next_week_focus"], 2)
        self.assertTrue(payload["s2pjt04_weekly_report_ready"])
        self.assertFalse(payload["scheduler_enabled"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_monthly_report_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            weekly_reports_path = tmp_path / "weekly-reports.json"
            cognitive_snapshots_path = tmp_path / "cognitive-snapshots.json"
            monthly_sections_path = tmp_path / "monthly-sections.json"
            capability_growth_path = tmp_path / "capability-growth.json"
            economic_conversions_path = tmp_path / "economic-conversions.json"
            forecast_reviews_path = tmp_path / "forecast-reviews.json"
            next_focus_path = tmp_path / "next-month-focus.json"
            gate_path = tmp_path / "production-gate.json"
            weekly_reports_path.write_text(
                json.dumps({"weekly_reports": [s2pjt04_weekly_report()]}, ensure_ascii=False),
                encoding="utf-8",
            )
            cognitive_snapshots_path.write_text(json.dumps(s2pjt05_cognitive_snapshots(), ensure_ascii=False), encoding="utf-8")
            monthly_sections_path.write_text(json.dumps(s2pjt05_monthly_sections(), ensure_ascii=False), encoding="utf-8")
            capability_growth_path.write_text(
                json.dumps({"capability_growth": s2pjt05_capability_growth()}, ensure_ascii=False),
                encoding="utf-8",
            )
            economic_conversions_path.write_text(
                json.dumps({"economic_conversions": s2pjt05_economic_conversions()}, ensure_ascii=False),
                encoding="utf-8",
            )
            forecast_reviews_path.write_text(
                json.dumps({"forecast_reviews": s2pjt05_forecast_reviews()}, ensure_ascii=False),
                encoding="utf-8",
            )
            next_focus_path.write_text(
                json.dumps({"next_month_focus": s2pjt05_next_month_focus()}, ensure_ascii=False),
                encoding="utf-8",
            )
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-monthly-report",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-30",
                    "--generated-at",
                    GENERATED_AT,
                    "--month-start",
                    "2026-06-01",
                    "--month-end",
                    "2026-06-30",
                    "--weekly-reports",
                    str(weekly_reports_path),
                    "--cognitive-snapshots",
                    str(cognitive_snapshots_path),
                    "--monthly-sections",
                    str(monthly_sections_path),
                    "--capability-growth",
                    str(capability_growth_path),
                    "--economic-conversions",
                    str(economic_conversions_path),
                    "--forecast-reviews",
                    str(forecast_reviews_path),
                    "--next-month-focus",
                    str(next_focus_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PJT05_MONTHLY_REPORT_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PJT05")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["calculated_conversion_count"], 1)
        self.assertTrue(payload["s2pjt05_monthly_report_ready"])
        self.assertFalse(payload["scheduler_enabled"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_cli_stage2_content_quality_gate_outputs_json(self) -> None:
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dependency_path = tmp_path / "dependency-receipts.json"
            gold_path = tmp_path / "gold-items.json"
            regression_path = tmp_path / "stage1-regression-checks.json"
            manual_path = tmp_path / "manual-review-samples.json"
            gate_path = tmp_path / "production-gate.json"
            dependency_path.write_text(
                json.dumps({"dependency_receipts": s2pht05_dependency_receipts()}, ensure_ascii=False),
                encoding="utf-8",
            )
            gold_path.write_text(
                json.dumps({"gold_items": s2pht05_gold_items()}, ensure_ascii=False),
                encoding="utf-8",
            )
            regression_path.write_text(
                json.dumps({"stage1_regression_checks": s2pht05_stage1_regression_checks()}, ensure_ascii=False),
                encoding="utf-8",
            )
            manual_path.write_text(
                json.dumps({"manual_review_samples": s2pht05_manual_review_samples()}, ensure_ascii=False),
                encoding="utf-8",
            )
            gate_path.write_text(json.dumps(s2pit02_production_gate_state(), ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(buffer):
                result = main([
                    "stage2-content-quality-gate",
                    "--state-dir",
                    tmp,
                    "--date",
                    "2026-06-26",
                    "--generated-at",
                    GENERATED_AT,
                    "--dependency-receipts",
                    str(dependency_path),
                    "--gold-items",
                    str(gold_path),
                    "--stage1-regression-checks",
                    str(regression_path),
                    "--manual-review-samples",
                    str(manual_path),
                    "--production-gate-state",
                    str(gate_path),
                    "--no-write",
                    "--json",
                ])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], S2PHT05_CONTENT_QUALITY_MODEL_ID)
        self.assertEqual(payload["task_id"], "S2PHT05")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["gold_item_count"], 10)
        self.assertTrue(payload["s2pht05_content_quality_gate_ready"])
        self.assertFalse(payload["real_smtp_sent"])
        self.assertFalse(payload["integrated_production_accepted"])


if __name__ == "__main__":
    unittest.main()
