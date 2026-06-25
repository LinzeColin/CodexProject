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


if __name__ == "__main__":
    unittest.main()
