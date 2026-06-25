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
    build_s2pft04_special_zone_discovery_report,
    build_s2pft03_key_city_coverage_report,
    build_s2pft02_hk_mo_independent_profile_report,
    build_s2pft01_china_provincial_template_coverage_report,
    build_s2pdt04_china_d3_readiness_review_report,
    build_s2pdt03_china_legal_metadata_relation_shadow_report,
    build_s2pdt02_china_c1_department_source_map_report,
    build_s2pdt01_china_c0_source_foundation_report,
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
    run_s2pft04_special_zone_discovery,
    run_s2pft03_key_city_coverage,
    run_s2pft02_hk_mo_independent_profile,
    run_s2pft01_china_provincial_template_coverage,
    run_s2pdt04_china_d3_readiness_review,
    run_s2pdt03_china_legal_metadata_relation_shadow,
    run_s2pdt02_china_c1_department_source_map,
    run_s2pdt01_china_c0_source_foundation,
    run_s2pct04_top_journal_profile_shadow,
    run_s2pct03_lancet_shadow_daily,
    run_s2pct02_science_shadow_daily,
    run_s2p2_top_journal_shadow_daily,
    run_s2p1_preprint_shadow_daily,
    validate_s2pct05_engineering_signal_report,
    validate_s2pct06_authoritative_report_source_report,
    validate_s2pct07_d2_source_domain_qualification_report,
    validate_s2pft04_special_zone_discovery_report,
    validate_s2pft03_key_city_coverage_report,
    validate_s2pft02_hk_mo_independent_profile_report,
    validate_s2pft01_china_provincial_template_coverage_report,
    validate_s2pdt04_china_d3_readiness_review_report,
    validate_s2pdt03_china_legal_metadata_relation_shadow_report,
    validate_s2pdt02_china_c1_department_source_map_report,
    validate_s2pdt01_china_c0_source_foundation_report,
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


if __name__ == "__main__":
    unittest.main()
