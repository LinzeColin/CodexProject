"""Stage 2 source-promotion gates and local shadow artifacts."""

from __future__ import annotations

import json
import hashlib
import re
import time
from collections.abc import Iterable, Mapping, Sequence
from datetime import date as Date
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import DEFAULT_TIMEZONE
from .global_scan import (
    CANDIDATE_QUEUE_MAX_ITEMS,
    CANDIDATE_QUEUE_MODEL_ID,
    ROI_RANKING_MODEL_ID,
    build_daily_delivery_package,
    candidate_from_source_item,
    normalize_candidate_queue,
    select_roi_candidate,
    update_candidate_queue,
)
from .pipeline import PipelineError, run_daily_dry_run
from .preprint_adapter import (
    PREPRINT_INGEST_MODEL_ID,
    SUPPORTED_PREPRINT_SERVERS,
    ingest_latest_preprints,
    validate_preprint_source_batch,
)
from .top_journal_adapter import (
    LANCET_ACCEPTED_ARTICLE_TYPES,
    SCIENCE_ACCEPTED_ARTICLE_TYPES,
    TOP_JOURNAL_INGEST_MODEL_ID,
    ingest_latest_top_journal,
    validate_top_journal_source_batch,
)


S2P1_PREPRINT_PROMOTION_MODEL_ID = "adp-s2p1-preprint-source-promotion-v1"
S2P1_PREPRINT_SHADOW_MODEL_ID = "adp-s2p1-preprint-shadow-daily-v1"
S2P1_PREPRINT_REPLAY_MODEL_ID = "adp-s2p1-preprint-terminal-replay-v1"
S2P1_PREPRINT_SHADOW_EVIDENCE_MODEL_ID = "adp-s2p1-preprint-shadow-evidence-v1"
S2P1_ACCEPTANCE_ID = "ADP-ACC-S2P1T01-SOURCE-PROMOTION"
S2P1_TASK_ID = "S2P1T01"
S2P1_REQUIRED_SERVERS = ("biorxiv", "medrxiv")
S2P1_REPLAY_REQUIRED_DATES = 30
S2P1_SHADOW_REQUIRED_HOURS = 48
S2P1_QUEUE_FILENAME = "stage2_s2p1_preprint_queue.json"
S2P1_LEDGER_FILENAME = "stage2_s2p1_preprint_ledger.jsonl"
S2P1_REPLAY_REPORT_FILENAME = "stage2_s2p1_preprint_replay_report.json"
S2P1_SHADOW_EVIDENCE_FILENAME = "stage2_s2p1_preprint_shadow_48h_report.json"
S2P1_PROMOTION_REPORT_FILENAME = "stage2_s2p1_preprint_promotion_report.json"
S2P2_TOP_JOURNAL_SHADOW_MODEL_ID = "adp-s2pct01-top-journal-shadow-daily-v1"
S2P2_ACCEPTANCE_ID = "ACC-S2PCT01-NATURE"
S2P2_TASK_ID = "S2PCT01"
S2P2_LEGACY_TASK_ID = "S2P2T01"
S2P2_REQUIRED_JOURNALS = ("nature",)
S2P2_QUEUE_FILENAME = "stage2_s2p2_top_journal_queue.json"
S2P2_LEDGER_FILENAME = "stage2_s2p2_top_journal_ledger.jsonl"
S2PCT02_SCIENCE_SHADOW_MODEL_ID = "adp-s2pct02-science-shadow-daily-v1"
S2PCT02_ACCEPTANCE_ID = "ACC-S2PCT02-SCIENCE"
S2PCT02_TASK_ID = "S2PCT02"
S2PCT02_LEGACY_TASK_ID = "S2P2T02"
S2PCT02_REQUIRED_JOURNALS = ("science",)
S2PCT02_QUEUE_FILENAME = "stage2_s2pct02_science_queue.json"
S2PCT02_LEDGER_FILENAME = "stage2_s2pct02_science_ledger.jsonl"
S2PCT03_LANCET_SHADOW_MODEL_ID = "adp-s2pct03-lancet-shadow-daily-v1"
S2PCT03_ACCEPTANCE_ID = "ACC-S2PCT03-LANCET"
S2PCT03_TASK_ID = "S2PCT03"
S2PCT03_LEGACY_TASK_ID = "S2P2T03"
S2PCT03_REQUIRED_JOURNALS = ("lancet",)
S2PCT03_QUEUE_FILENAME = "stage2_s2pct03_lancet_queue.json"
S2PCT03_LEDGER_FILENAME = "stage2_s2pct03_lancet_ledger.jsonl"
S2PCT04_JOURNAL_PROFILE_MODEL_ID = "adp-s2pct04-top-journal-profile-v1"
S2PCT04_ACCEPTANCE_ID = "ACC-S2PCT04-JOURNAL-PROFILE"
S2PCT04_TASK_ID = "S2PCT04"
S2PCT04_LEGACY_TASK_ID = "S2P2T04"
S2PCT04_REQUIRED_JOURNALS = ("nature", "science", "lancet")
S2PCT04_REQUIRED_PROFILE_KINDS = ("research", "review", "editorial", "news", "correction", "retraction")
S2PCT04_FORCED_EVENT_TYPES = ("correction", "retraction")
S2PCT04_LEDGER_FILENAME = "stage2_s2pct04_profile_ledger.jsonl"
S2PCT05_ENGINEERING_SIGNAL_MODEL_ID = "adp-s2pct05-engineering-signals-v1"
S2PCT05_ACCEPTANCE_ID = "ACC-S2PCT05-ENGINEERING-SIGNALS"
S2PCT05_TASK_ID = "S2PCT05"
S2PCT05_REQUIRED_SIGNAL_TYPES = (
    "official_code_repository",
    "official_release",
    "model_card",
    "benchmark_result",
    "standard_or_spec",
)
S2PCT05_ALLOWED_RELATION_TYPES = (
    "implements_paper",
    "version_of",
    "documents_model",
    "evaluates",
    "standardizes",
)
S2PCT05_ALLOWED_OFFICIALITY_STATES = ("official", "publisher_linked", "standards_body")
S2PCT05_ALLOWED_REPRODUCIBILITY_STATES = ("reproducible", "partial", "claimed", "not_applicable")
S2PCT05_LEDGER_FILENAME = "stage2_s2pct05_engineering_signal_ledger.jsonl"
S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID = "adp-s2pct06-authoritative-reports-v1"
S2PCT06_ACCEPTANCE_ID = "ACC-S2PCT06-REPORTS"
S2PCT06_TASK_ID = "S2PCT06"
S2PCT06_REQUIRED_REPORT_TYPES = (
    "research_institution_report",
    "lab_technical_report",
    "industry_technical_report",
    "product_technical_note",
)
S2PCT06_ALLOWED_PUBLISHER_TYPES = (
    "research_institution",
    "public_lab",
    "industry_research_lab",
    "company_product_org",
)
S2PCT06_ALLOWED_IDENTITY_STATES = (
    "official_domain",
    "institutional_repository",
    "publisher_signed",
    "standards_or_government_affiliated",
)
S2PCT06_ALLOWED_INTEREST_RELATIONS = (
    "independent_research",
    "sponsor_disclosed",
    "vendor_authored",
    "product_owner_authored",
)
S2PCT06_ALLOWED_EVIDENCE_LEVELS = (
    "primary_research_report",
    "technical_whitepaper",
    "methodology_note",
    "product_technical_note",
)
S2PCT06_LEDGER_FILENAME = "stage2_s2pct06_authoritative_report_ledger.jsonl"
S2PCT07_D2_QUALIFICATION_MODEL_ID = "adp-s2pct07-d2-source-domain-qualification-v1"
S2PCT07_ACCEPTANCE_ID = "ACC-S2PCT07-D2"
S2PCT07_TASK_ID = "S2PCT07"
S2PCT07_REQUIRED_DOMAINS = ("top_journal", "engineering_signal", "authoritative_report")
S2PCT07_REQUIRED_REPLAY_DATES = 30
S2PCT07_REQUIRED_SHADOW_HOURS = 48
S2PCT07_REQUIRED_FORCED_EVENT_TYPES = ("correction", "retraction")
S2PCT07_REQUIRED_QUEUE_EXPLANATION_STATES = ("selected", "queued", "deferred")
S2PCT07_QUALIFICATION_REPORT_FILENAME = "stage2_s2pct07_d2_source_domain_qualification_report.json"
S2PDT01_CHINA_C0_SOURCE_MODEL_ID = "adp-s2pdt01-china-c0-source-foundation-v1"
S2PDT01_ACCEPTANCE_ID = "ACC-S2PDT01-C0"
S2PDT01_TASK_ID = "S2PDT01"
S2PDT01_LEGACY_TASK_ID = "S2P3T01"
S2PDT01_REQUIRED_AUTHORITY_TYPES = (
    "law_regulation",
    "npc_document",
    "state_council_document",
    "gazette",
    "supreme_court_procuratorate_document",
)
S2PDT01_REQUIRED_TRACE_FIELDS = ("authority_name", "official_domain", "document_number", "published_date")
S2PDT01_ALLOWED_IDENTITY_STATES = ("official_domain", "official_gazette", "official_publication_portal")
S2PDT01_REPORT_FILENAME = "stage2_s2pdt01_china_c0_source_foundation_report.json"
S2PDT02_CHINA_C1_SOURCE_MODEL_ID = "adp-s2pdt02-china-c1-department-source-map-v1"
S2PDT02_ACCEPTANCE_ID = "ACC-S2PDT02-C1"
S2PDT02_TASK_ID = "S2PDT02"
S2PDT02_LEGACY_TASK_ID = "S2P3T02"
S2PDT02_REQUIRED_SECTORS = (
    "macro_policy",
    "science_technology",
    "industry_policy",
    "finance",
    "market_regulation",
    "key_industry",
)
S2PDT02_REQUIRED_ROUTE_FIELDS = ("aliases", "industry_routes", "official_domain", "source_url")
S2PDT02_ALLOWED_IDENTITY_STATES = ("official_domain", "official_publication_portal")
S2PDT02_REPORT_FILENAME = "stage2_s2pdt02_china_c1_department_source_map_report.json"
S2PDT03_LEGAL_METADATA_MODEL_ID = "adp-s2pdt03-china-legal-metadata-relation-shadow-v1"
S2PDT03_ACCEPTANCE_ID = "ACC-S2PDT03-LEGAL"
S2PDT03_TASK_ID = "S2PDT03"
S2PDT03_LEGACY_TASK_ID = "S2P3T03"
S2PDT03_REQUIRED_LEGAL_STATUSES = ("draft", "formal", "amended", "repealed", "implemented", "interpreted")
S2PDT03_REQUIRED_RELATION_TYPES = ("draft_to_formal", "amends", "repeals", "implements", "interprets", "reprint_of")
S2PDT03_REQUIRED_DATE_FIELDS = ("published_date", "effective_date")
S2PDT03_REQUIRED_FORCED_UPDATE_FIELDS = ("update_required", "rescore_required", "updated_state")
S2PDT03_ALLOWED_IDENTITY_STATES = ("official_domain", "official_gazette", "official_publication_portal")
S2PDT03_REPORT_FILENAME = "stage2_s2pdt03_china_legal_metadata_relation_shadow_report.json"
S2PDT04_D3_READINESS_MODEL_ID = "adp-s2pdt04-china-d3-readiness-review-v1"
S2PDT04_ACCEPTANCE_ID = "ACC-S2PDT04-D3-CORE"
S2PDT04_TASK_ID = "S2PDT04"
S2PDT04_LEGACY_TASK_ID = "S2P3T04"
S2PDT04_REQUIRED_REPLAY_DATES = 30
S2PDT04_REQUIRED_SHADOW_DAYS = 2
S2PDT04_REQUIRED_BOARD_IDS = ("B2_policy", "B3_frontier", "B4_industry", "B5_macro", "B6_risk")
S2PDT04_REQUIRED_ROUTE_FIELDS = ("board_id", "source_ids", "route_explanation", "authority_gate", "metadata_only")
S2PDT04_REPORT_FILENAME = "stage2_s2pdt04_china_d3_readiness_review_report.json"
S2PET01_US_TA_SOURCE_MODEL_ID = "adp-s2pet01-us-ta-source-foundation-v1"
S2PET01_ACCEPTANCE_ID = "ACC-S2PET01-US-TA"
S2PET01_TASK_ID = "S2PET01"
S2PET01_LEGACY_TASK_ID = "S2P4T01"
S2PET01_REQUIRED_AGENCIES = ("NSF", "DARPA", "DOE", "NIH", "NASA", "NIST", "USPTO", "FDA")
S2PET01_REQUIRED_SIGNAL_TYPES = (
    "grant_award",
    "program_announcement",
    "research_project",
    "standard_reference",
    "patent_publication",
    "regulatory_science_notice",
)
S2PET01_ALLOWED_IDENTITY_STATES = ("official_domain", "official_api_or_feed", "official_publication_portal")
S2PET01_REQUIRED_TRACE_FIELDS = ("agency_id", "agency_name", "official_domain", "source_url", "published_date")
S2PET01_REPORT_FILENAME = "stage2_s2pet01_us_ta_source_foundation_report.json"
S2PET02_US_LG_BACKBONE_MODEL_ID = "adp-s2pet02-us-lg-legal-backbone-v1"
S2PET02_ACCEPTANCE_ID = "ACC-S2PET02-US-LG"
S2PET02_TASK_ID = "S2PET02"
S2PET02_LEGACY_TASK_ID = "S2P4T02"
S2PET02_REQUIRED_SOURCE_SYSTEMS = ("federal_register", "regulations_gov", "govinfo", "congress_gov")
S2PET02_REQUIRED_DOCUMENT_TYPES = (
    "docket",
    "proposed_rule",
    "final_rule",
    "cfr",
    "bill",
    "public_law",
    "committee_report",
    "certified_text",
)
S2PET02_REQUIRED_RELATION_TYPES = (
    "docket_to_fr_document",
    "fr_document_to_cfr",
    "bill_to_public_law",
    "bill_to_report",
    "certified_text_to_public_law",
)
S2PET02_ALLOWED_IDENTITY_STATES = (
    "official_domain",
    "official_api_or_feed",
    "official_publication_portal",
    "certified_government_text",
)
S2PET02_REQUIRED_TRACE_FIELDS = ("source_system", "official_domain", "source_url", "published_date", "document_identifier")
S2PET02_REQUIRED_RELATION_FIELDS = ("relation_id", "relation_type", "source_document_id", "target_document_id", "evidence_refs")
S2PET02_REPORT_FILENAME = "stage2_s2pet02_us_lg_legal_backbone_report.json"
S2PET03_US_FM_BACKBONE_MODEL_ID = "adp-s2pet03-us-fm-source-backbone-v1"
S2PET03_ACCEPTANCE_ID = "ACC-S2PET03-US-FM"
S2PET03_TASK_ID = "S2PET03"
S2PET03_LEGACY_TASK_ID = "S2P4T03"
S2PET03_REQUIRED_SOURCE_SYSTEMS = ("sec_edgar", "federal_reserve", "treasury", "cftc", "occ", "fdic", "cfpb")
S2PET03_REQUIRED_SEC_FORM_TYPES = ("8-K", "10-K", "10-Q", "S-1", "13D", "13G", "13F", "FORM-4", "N-PORT", "N-CEN")
S2PET03_REQUIRED_SIGNAL_TYPES = (
    "sec_company_filing",
    "sec_fund_filing",
    "macro_policy_release",
    "treasury_market_data",
    "derivatives_market_data",
    "bank_supervision_notice",
    "deposit_insurance_notice",
    "consumer_finance_notice",
)
S2PET03_REQUIRED_RELATION_TYPES = (
    "filing_to_company",
    "filing_to_fund",
    "filing_to_asset",
    "company_to_cik",
    "fund_to_series_class",
    "macro_release_to_asset_class",
)
S2PET03_ALLOWED_IDENTITY_STATES = ("official_domain", "official_api_or_feed", "official_publication_portal")
S2PET03_REQUIRED_TRACE_FIELDS = ("source_system", "official_domain", "source_url", "published_date", "record_identifier")
S2PET03_REQUIRED_IDENTIFIER_FIELDS = ("cik", "accession_number")
S2PET03_REQUIRED_RELATION_FIELDS = ("relation_id", "relation_type", "source_record_id", "target_entity_id", "evidence_refs")
S2PET03_REPORT_FILENAME = "stage2_s2pet03_us_fm_source_backbone_report.json"
S2PET04_US_TP_D4_QUALIFICATION_MODEL_ID = "adp-s2pet04-us-tp-d4-qualification-v1"
S2PET04_ACCEPTANCE_ID = "ACC-S2PET04-D4"
S2PET04_TASK_ID = "S2PET04"
S2PET04_LEGACY_TASK_ID = "S2P4T04"
S2PET04_REQUIRED_SOURCE_SYSTEMS = ("ostp", "bis", "ftc", "fcc", "cisa", "chips_program")
S2PET04_REQUIRED_SIGNAL_TYPES = (
    "technology_policy_notice",
    "export_control_notice",
    "competition_policy_notice",
    "spectrum_policy_notice",
    "cybersecurity_advisory",
    "semiconductor_program_notice",
)
S2PET04_REQUIRED_D4_COMPONENTS = ("us_ta", "us_lg", "us_fm", "us_tp")
S2PET04_REQUIRED_BOARD_IDS = ("B4", "B5", "B6")
S2PET04_REQUIRED_BUDGET_SEGMENTS = ("US-TA", "US-LG", "US-FM", "US-TP")
S2PET04_REQUIRED_BUDGET_WEIGHTS = (35, 15, 30, 20)
S2PET04_REQUIRED_REPLAY_DATES = 30
S2PET04_REQUIRED_SHADOW_DAYS = 2
S2PET04_ALLOWED_IDENTITY_STATES = ("official_domain", "official_api_or_feed", "official_publication_portal")
S2PET04_REQUIRED_POLICY_FIELDS = ("source_system", "signal_type", "official_domain", "source_url", "published_date", "record_identifier")
S2PET04_REPORT_FILENAME = "stage2_s2pet04_us_tp_d4_qualification_report.json"
S2PFT01_CHINA_PROVINCIAL_MODEL_ID = "adp-s2pft01-china-provincial-template-coverage-v1"
S2PFT01_ACCEPTANCE_ID = "ACC-S2PFT01-PROVINCES"
S2PFT01_TASK_ID = "S2PFT01"
S2PFT01_LEGACY_TASK_ID = "S2P5T01"
S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS = (
    "beijing",
    "tianjin",
    "hebei",
    "shanxi",
    "inner_mongolia",
    "liaoning",
    "jilin",
    "heilongjiang",
    "shanghai",
    "jiangsu",
    "zhejiang",
    "anhui",
    "fujian",
    "jiangxi",
    "shandong",
    "henan",
    "hubei",
    "hunan",
    "guangdong",
    "guangxi",
    "hainan",
    "chongqing",
    "sichuan",
    "guizhou",
    "yunnan",
    "tibet",
    "shaanxi",
    "gansu",
    "qinghai",
    "ningxia",
    "xinjiang",
)
S2PFT01_REQUIRED_LOCALITY_TYPES = ("province", "autonomous_region", "municipality")
S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES = (
    "government_portal",
    "development_reform",
    "science_technology",
    "industry_information",
    "finance",
    "market_regulation",
)
S2PFT01_ALLOWED_HEALTH_TIERS = ("green", "yellow", "red")
S2PFT01_ALLOWED_IDENTITY_STATES = ("official_domain", "official_publication_portal")
S2PFT01_REPORT_FILENAME = "stage2_s2pft01_china_provincial_template_coverage_report.json"
S2PFT02_HK_MO_PROFILE_MODEL_ID = "adp-s2pft02-hk-mo-independent-profile-v1"
S2PFT02_ACCEPTANCE_ID = "ACC-S2PFT02-HK-MO"
S2PFT02_TASK_ID = "S2PFT02"
S2PFT02_LEGACY_TASK_ID = "S2P5T02"
S2PFT02_REQUIRED_JURISDICTION_IDS = ("hong_kong", "macau")
S2PFT02_REQUIRED_LANGUAGE_PROFILES = ("zh_hant", "en", "pt")
S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES = ("common_law", "civil_law_portuguese_heritage")
S2PFT02_REQUIRED_PROFILE_FIELDS = (
    "jurisdiction_id",
    "jurisdiction_name",
    "legal_system_state",
    "government_structure_model",
    "official_domain",
    "source_url",
    "authority_gate",
    "metadata_only",
)
S2PFT02_FORBIDDEN_TEMPLATE_STATES = ("mainland_province_template", "mainland_city_template")
S2PFT02_REPORT_FILENAME = "stage2_s2pft02_hk_mo_independent_profile_report.json"
S2PFT03_KEY_CITY_COVERAGE_MODEL_ID = "adp-s2pft03-key-city-coverage-v1"
S2PFT03_ACCEPTANCE_ID = "ACC-S2PFT03-CITIES"
S2PFT03_TASK_ID = "S2PFT03"
S2PFT03_LEGACY_TASK_ID = "S2P5T03"
S2PFT03_REQUIRED_CITY_IDS = (
    "beijing",
    "shanghai",
    "shenzhen",
    "guangzhou",
    "tianjin",
    "chongqing",
    "hangzhou",
    "nanjing",
    "suzhou",
    "hefei",
    "wuhan",
    "xian",
    "chengdu",
    "changsha",
    "wuxi",
    "dongguan",
    "foshan",
    "zhuhai",
    "shenyang",
    "ningbo",
    "qingdao",
    "xiamen",
    "dalian",
    "zhengzhou",
)
S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES = (
    "party_committee",
    "government_portal",
    "development_reform",
    "science_technology",
    "industry_information",
    "finance",
    "commerce",
    "market_regulation",
    "data",
    "financial_regulation",
)
S2PFT03_ALLOWED_REGION_GROUPS = ("national_municipality", "yangtze_delta", "pearl_delta", "central", "western", "northeast", "coastal")
S2PFT03_ALLOWED_HEALTH_TIERS = ("green", "yellow", "red")
S2PFT03_REPORT_FILENAME = "stage2_s2pft03_key_city_coverage_report.json"
S2PFT04_SPECIAL_ZONE_MODEL_ID = "adp-s2pft04-special-zone-discovery-v1"
S2PFT04_ACCEPTANCE_ID = "ACC-S2PFT04-ZONES"
S2PFT04_TASK_ID = "S2PFT04"
S2PFT04_LEGACY_TASK_ID = "S2P5T04"
S2PFT04_REQUIRED_ZONE_IDS = (
    "xiongan_new_area",
    "shanghai_pudong_new_area",
    "shenzhen_qianhai",
    "hengqin_guangdong_macao",
    "hainan_free_trade_port",
    "shanghai_lingang",
    "beijing_zhongguancun",
    "suzhou_industrial_park",
    "tianjin_binhai_new_area",
    "chongqing_liangjiang_new_area",
)
S2PFT04_REQUIRED_ZONE_AUTHORITY_ROLES = (
    "zone_governing_committee",
    "government_portal",
    "development_reform",
    "commerce",
    "science_technology",
    "industry_information",
    "market_regulation",
    "data_or_digital",
    "customs",
    "taxation",
    "financial_regulation",
)
S2PFT04_ALLOWED_ZONE_TYPES = (
    "national_new_area",
    "free_trade_port",
    "cooperation_zone",
    "innovation_demonstration_zone",
    "industrial_park",
    "new_area_subzone",
)
S2PFT04_ALLOWED_POLICY_FOCUS_AREAS = (
    "technology_innovation",
    "advanced_manufacturing",
    "free_trade",
    "finance",
    "digital_economy",
    "cross_border_cooperation",
    "green_development",
    "industrial_upgrade",
)
S2PFT04_ALLOWED_HEALTH_TIERS = ("green", "yellow", "red")
S2PFT04_REPORT_FILENAME = "stage2_s2pft04_special_zone_discovery_report.json"
S2PFT05_D3_FULL_GOVERNANCE_MODEL_ID = "adp-s2pft05-d3-full-governance-qualification-v1"
S2PFT05_ACCEPTANCE_ID = "ACC-S2PFT05-D3-FULL"
S2PFT05_TASK_ID = "S2PFT05"
S2PFT05_LEGACY_TASK_ID = "S2P5T05"
S2PFT05_REQUIRED_COMPONENTS = ("c0_core", "c1_department", "c2_legal", "c3_local", "c4_special_zone")
S2PFT05_REQUIRED_QUOTA_ROLES = ("central_authority", "provincial", "hk_mo", "key_city", "special_zone")
S2PFT05_REQUIRED_GOVERNANCE_GATES = ("quota_balance", "health_balance", "elimination_explanation", "fallback_route")
S2PFT05_REQUIRED_REPLAY_DATES = 30
S2PFT05_ALLOWED_HEALTH_TIERS = ("green", "yellow", "red")
S2PFT05_REPORT_FILENAME = "stage2_s2pft05_d3_full_governance_qualification_report.json"
S2PGT01_EVIDENCE_PACKET_MODEL_ID = "adp-s2pgt01-evidence-packet-v2-compatibility-v1"
S2PGT01_ACCEPTANCE_ID = "ACC-S2PGT01-EVIDENCE-V2"
S2PGT01_TASK_ID = "S2PGT01"
S2PGT01_PACKET_VERSION = "EvidencePacketV2"
S2PGT01_REQUIRED_SOURCE_DOMAINS = (
    "d1_research_preprint",
    "d2_authoritative_publication",
    "d3_china_official",
    "d4_us_official",
)
S2PGT01_REQUIRED_EVIDENCE_LEVELS = (
    "metadata",
    "abstract",
    "full_text",
    "cross_source_verification",
)
S2PGT01_REQUIRED_PACKET_FIELDS = (
    "packet_id",
    "packet_version",
    "source_domain",
    "source_id",
    "source_type",
    "source_adapter",
    "canonical_url",
    "title",
    "evidence_levels_available",
    "claim_ids",
    "content_ref_ids",
    "support_statuses",
    "locator_refs",
    "board_routes",
    "metadata_only",
    "schema_migration_required",
    "production_affected",
)
S2PGT01_REPORT_FILENAME = "stage2_s2pgt01_evidence_packet_v2_compatibility_report.json"
S2PGT02_KNOWLEDGE_GRAPH_MODEL_ID = "adp-s2pgt02-knowledge-graph-spine-v1"
S2PGT02_ACCEPTANCE_ID = "ACC-S2PGT02-KG"
S2PGT02_TASK_ID = "S2PGT02"
S2PGT02_LEGACY_TASK_ID = "S2P6T01"
S2PGT02_REQUIRED_IDENTIFIER_TYPES = (
    "doi",
    "pmid",
    "arxiv",
    "cn_document_number",
    "federal_register_document_number",
    "cik",
)
S2PGT02_ALLOWED_RELATION_TYPES = (
    "same_as",
    "cites",
    "updates",
    "supersedes",
    "implements",
    "references",
)
S2PGT02_REQUIRED_RELATION_FIELDS = (
    "relation_id",
    "relation_type",
    "source_canonical_id",
    "target_canonical_id",
    "evidence_refs",
    "support_status",
    "idempotency_key",
)
S2PGT02_REQUIRED_GATES = (
    "identifier_coverage_gate",
    "canonical_dedupe_gate",
    "relation_evidence_gate",
    "idempotent_update_gate",
    "no_side_effect_gate",
)
S2PGT02_REPORT_FILENAME = "stage2_s2pgt02_knowledge_graph_spine_report.json"
S2PGT03_ROUTING_MODEL_ID = "adp-s2pgt03-source-board-routing-v1"
S2PGT03_ACCEPTANCE_ID = "ACC-S2PGT03-ROUTING"
S2PGT03_TASK_ID = "S2PGT03"
S2PGT03_REQUIRED_SOURCE_DOMAINS = (
    "d1_research_preprint",
    "d2_authoritative_publication",
    "d3_china_official",
    "d4_us_official",
)
S2PGT03_REQUIRED_PRIMARY_BOARDS = ("B1", "B2", "B3")
S2PGT03_REQUIRED_CROSS_CUTTING_BOARDS = ("B4", "B5", "B6")
S2PGT03_ALLOWED_REASON_CODES = (
    "scientific_mechanism",
    "engineering_relevance",
    "policy_capital_context",
    "social_impact",
    "risk_counterevidence",
    "personal_roi_action",
)
S2PGT03_REQUIRED_ROUTE_FIELDS = (
    "route_id",
    "source_domain",
    "source_id",
    "primary_boards",
    "cross_cutting_boards",
    "reason_codes",
    "route_explanation",
    "evidence_refs",
)
S2PGT03_REQUIRED_GATES = (
    "source_domain_coverage_gate",
    "primary_board_coverage_gate",
    "cross_cutting_board_coverage_gate",
    "route_reason_gate",
    "no_side_effect_gate",
)
S2PGT03_SOURCE_DOMAIN_BOARD_RULES = {
    "d1_research_preprint": {
        "primary": ("B1", "B2"),
        "conditional": ("B3",),
        "mandatory_checks": ("B4", "B5", "B6"),
    },
    "d2_authoritative_publication": {
        "primary": ("B1", "B2"),
        "conditional": ("B3",),
        "mandatory_checks": ("B4", "B5", "B6"),
    },
    "d3_china_official": {
        "primary": ("B3",),
        "conditional": ("B1", "B2"),
        "mandatory_checks": ("B4", "B5", "B6"),
    },
    "d4_us_official": {
        "primary": ("B2", "B3"),
        "conditional": ("B1",),
        "mandatory_checks": ("B4", "B5", "B6"),
    },
}
S2PGT03_REPORT_FILENAME = "stage2_s2pgt03_source_board_routing_report.json"
S2PGT04_DELTA_RESONANCE_MODEL_ID = "adp-s2pgt04-delta-resonance-v1"
S2PGT04_ACCEPTANCE_ID = "ACC-S2PGT04-DELTA-RESONANCE"
S2PGT04_TASK_ID = "S2PGT04"
S2PGT04_REQUIRED_DELTA_TYPES = (
    "new_signal",
    "changed_signal",
    "supporting_signal",
    "refuting_signal",
    "frontier_shift",
)
S2PGT04_REQUIRED_RESONANCE_GROUPS = (
    "science_engineering",
    "policy_capital",
    "risk_counterevidence",
    "personal_roi",
)
S2PGT04_ALLOWED_SUPPORT_STATUSES = ("supported", "refuted", "mixed", "watch")
S2PGT04_REQUIRED_DELTA_FIELDS = (
    "delta_id",
    "source_domain",
    "source_id",
    "route_id",
    "delta_type",
    "resonance_group",
    "support_status",
    "signal_strength",
    "delta_explanation",
    "evidence_refs",
)
S2PGT04_REQUIRED_GATES = (
    "upstream_routing_gate",
    "delta_type_coverage_gate",
    "support_refute_gate",
    "resonance_group_gate",
    "delta_reason_gate",
    "no_side_effect_gate",
)
S2PGT04_REPORT_FILENAME = "stage2_s2pgt04_delta_resonance_report.json"
S2PGT05_CALIBRATION_MODEL_ID = "adp-s2pgt05-cross-board-calibration-v1"
S2PGT05_ACCEPTANCE_ID = "ACC-S2PGT05-CALIBRATION"
S2PGT05_TASK_ID = "S2PGT05"
S2PGT05_LEGACY_TASK_ID = "S2P6T02"
S2PGT05_REQUIRED_BOARD_IDS = ("B1", "B2", "B3", "B4", "B5", "B6")
S2PGT05_REQUIRED_SOURCE_DOMAINS = (
    "d1_research_preprint",
    "d2_authoritative_publication",
    "d3_china_official",
    "d4_us_official",
)
S2PGT05_REQUIRED_DECISIONS = ("selected", "queued", "deferred")
S2PGT05_REQUIRED_CANDIDATE_FIELDS = (
    "candidate_id",
    "delta_id",
    "board_id",
    "source_domain",
    "source_id",
    "raw_score",
    "waiting_days",
    "evidence_refs",
)
S2PGT05_SELECTED_COUNT = 4
S2PGT05_WAITLIST_COUNT = 1
S2PGT05_MAX_SOURCE_SHARE = 0.5
S2PGT05_MAX_WAITING_DAYS = 30
S2PGT05_MAX_WAITING_CREDIT = 0.15
S2PGT05_REQUIRED_GATES = (
    "upstream_delta_resonance_gate",
    "percentile_calibration_gate",
    "source_balance_gate",
    "waiting_credit_gate",
    "queue_reason_gate",
    "deterministic_order_gate",
    "no_side_effect_gate",
)
S2PGT05_REPORT_FILENAME = "stage2_s2pgt05_calibration_report.json"
S2PIT01_USER_CENTER_MODEL_ID = "adp-s2pit01-user-center-v1"
S2PIT01_ACCEPTANCE_ID = "ACC-S2PIT01-USER-CENTER"
S2PIT01_TASK_ID = "S2PIT01"
S2PIT01_REQUIRED_CONTROL_DOMAINS = ("profile", "mail_review", "source_boards", "budget_schedule")
S2PIT01_REQUIRED_CONFIG_SECTIONS = (
    "project",
    "cost_policy",
    "runtime",
    "intelligence_provider",
    "boards",
    "sources",
    "email",
    "outputs",
    "queue",
    "scoring",
    "source_defaults",
    "iteration",
    "validation",
)
S2PIT01_REQUIRED_USER_CENTER_PATHS = (
    "用户中心/README.md",
    "用户中心/一看三查.md",
)
S2PIT01_REQUIRED_GATES = (
    "owner_controls_gate",
    "storage_readability_gate",
    "one_edit_directory_gate",
    "control_domain_gate",
    "click_depth_gate",
    "compatible_config_gate",
    "no_side_effect_gate",
)
S2PIT01_MAX_CLICK_DEPTH = 2
S2PIT01_EDITABLE_FACT_SOURCE = "config/owner_controls.yaml"
S2PIT01_REPORT_FILENAME = "stage2_s2pit01_user_center_report.json"
S2PIT02_RUNTIME_DASHBOARD_MODEL_ID = "adp-s2pit02-runtime-dashboard-v1"
S2PIT02_ACCEPTANCE_ID = "ACC-S2PIT02-RUNTIME-DASHBOARD"
S2PIT02_TASK_ID = "S2PIT02"
S2PIT02_REQUIRED_SECTIONS = ("owner_center", "runtime", "storage", "production_boundaries", "next_actions")
S2PIT02_REQUIRED_RUNTIME_ACTIONS = ("runtime_audit", "watchdog")
S2PIT02_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "v7_2_contract_files_changed",
)
S2PIT02_OWNER_STATUS_PATH = "用户中心/邮件发送与队列状态.md"
S2PIT02_REQUIRED_OWNER_STATUS_SUMMARY_FIELDS = (
    "sent_today",
    "expected_today",
    "total_candidate_pool",
    "generated_report_or_preview_count",
    "pending_candidate_count",
    "historical_send_record_count",
    "review_action_snapshot_state",
)
S2PIT02_REQUIRED_OWNER_STATUS_STATES = (
    "sent",
    "blocked_not_sent",
    "queued_or_pending",
)
S2PIT02_REPORT_FILENAME = "stage2_s2pit02_runtime_dashboard_report.json"
S2PIT03_SOURCE_MODEL_VIEW_MODEL_ID = "adp-s2pit03-source-model-view-v1"
S2PIT03_ACCEPTANCE_ID = "ACC-S2PIT03-SOURCE-MODEL"
S2PIT03_TASK_ID = "S2PIT03"
S2PIT03_REQUIRED_SOURCE_DOMAINS = ("D1", "D2", "D3", "D4")
S2PIT03_REQUIRED_READING_BOARDS = ("B1", "B2", "B3", "B4", "B5", "B6")
S2PIT03_REQUIRED_PARAMETER_FIELDS = (
    "parameter_id",
    "default_value",
    "value_range",
    "rollback_value",
    "impact",
    "code_refs",
    "test_refs",
)
S2PIT03_MAX_FIRST_SCREEN_PARAMETERS = 20
S2PIT03_REQUIRED_GATES = (
    "user_center_gate",
    "source_domain_gate",
    "reading_board_gate",
    "parameter_disclosure_gate",
    "queue_view_gate",
    "traceability_gate",
    "deterministic_view_gate",
    "no_side_effect_gate",
)
S2PIT03_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PIT03_REPORT_FILENAME = "stage2_s2pit03_source_model_view_report.json"
S2PIT04_CONTENT_LEDGER_MODEL_ID = "adp-s2pit04-content-mail-review-action-roi-ledger-v1"
S2PIT04_ACCEPTANCE_ID = "ACC-S2PIT04-LEDGER"
S2PIT04_TASK_ID = "S2PIT04"
S2PIT04_REQUIRED_RECORD_FIELDS = (
    "content_id",
    "evidence_refs",
    "run_id",
    "mail_id",
    "feedback_id",
    "lifecycle_state",
    "review_ids",
    "action_ids",
    "asset_ids",
    "roi",
)
S2PIT04_ALLOWED_MAIL_STATUSES = ("previewed", "ready_no_send", "blocked_no_send")
S2PIT04_ALLOWED_FEEDBACK_STATUSES = ("pending", "received", "not_requested")
S2PIT04_REQUIRED_GATES = (
    "runtime_dashboard_gate",
    "source_model_view_gate",
    "lifecycle_state_gate",
    "review_schedule_gate",
    "action_roi_gate",
    "ledger_record_gate",
    "traceability_gate",
    "count_conservation_gate",
    "deterministic_ledger_gate",
    "no_side_effect_gate",
)
S2PIT04_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PIT04_REPORT_FILENAME = "stage2_s2pit04_content_mail_review_action_roi_ledger_report.json"
S2PKT01_MAIL_CONTRACT_MODEL_ID = "adp-s2pkt01-mail-contract-v1"
S2PKT01_ACCEPTANCE_ID = "ACC-S2PKT01-MAIL-CONTRACT"
S2PKT01_TASK_ID = "S2PKT01"
S2PKT01_EMAIL_CONTRACT_ID = "EMAIL_LEARNING_V1"
S2PKT01_TEMPLATE_VERSION = "1.0.0"
S2PKT01_MAIL_PRODUCTS = ("M1", "M2", "M3", "M4")
S2PKT01_PRIMARY_BOARD_BY_MAIL = {
    "M1": "B1",
    "M2": "B2",
    "M3": "B3",
    "M4": "B1-B6",
}
S2PKT01_CROSS_CUTTING_BOARDS = ("B4", "B5", "B6")
S2PKT01_READING_LAYERS = (
    "plain_language_summary",
    "evidence_trace",
    "action_roi_transfer",
)
S2PKT01_EVIDENCE_LABELS = ("FACT", "INFERENCE", "OPINION", "OBSERVATION")
S2PKT01_FEEDBACK_ACTIONS = (
    "useful",
    "need_more_evidence",
    "save_for_review",
    "create_action",
)
S2PKT01_ALLOWED_MAIL_STATUSES = ("ready_no_send", "previewed", "blocked_no_send")
S2PKT01_REQUIRED_CONTRACT_FIELDS = (
    "mail_product_id",
    "contract_id",
    "template_version",
    "primary_board",
    "cross_cutting_boards",
    "reading_layers",
    "evidence_labels",
    "feedback_actions",
    "status",
)
S2PKT01_REQUIRED_GATES = (
    "content_quality_gate",
    "content_ledger_gate",
    "action_roi_gate",
    "shared_contract_gate",
    "board_differentiation_gate",
    "reading_layer_gate",
    "evidence_label_gate",
    "feedback_component_gate",
    "hash_status_gate",
    "no_side_effect_gate",
)
S2PKT01_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PKT01_REPORT_FILENAME = "stage2_s2pkt01_mail_contract_report.json"
S2PKT02_M1_MAIL_MODEL_ID = "adp-s2pkt02-m1-mail-v1"
S2PKT02_ACCEPTANCE_ID = "ACC-S2PKT02-M1"
S2PKT02_TASK_ID = "S2PKT02"
S2PKT02_MAIL_PRODUCT_ID = "M1"
S2PKT02_PRIMARY_BOARD = "B1"
S2PKT02_REQUIRED_SECTIONS = (
    "scientific_mechanism",
    "evidence_chain",
    "counterevidence",
    "personal_value",
    "action_path",
)
S2PKT02_REQUIRED_ACTION_WINDOWS = ("15m", "2h")
S2PKT02_REQUIRED_GATES = (
    "mail_contract_gate",
    "content_quality_gate",
    "content_ledger_gate",
    "action_roi_gate",
    "m1_scope_gate",
    "section_coverage_gate",
    "evidence_counterevidence_gate",
    "personal_action_gate",
    "hash_status_gate",
    "no_side_effect_gate",
)
S2PKT02_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PKT02_REPORT_FILENAME = "stage2_s2pkt02_m1_mail_report.json"
S2PKT03_M2_MAIL_MODEL_ID = "adp-s2pkt03-m2-mail-v1"
S2PKT03_ACCEPTANCE_ID = "ACC-S2PKT03-M2"
S2PKT03_TASK_ID = "S2PKT03"
S2PKT03_MAIL_PRODUCT_ID = "M2"
S2PKT03_PRIMARY_BOARD = "B2"
S2PKT03_REQUIRED_SECTIONS = (
    "engineering_usability",
    "reproducibility",
    "product_industry_value",
    "limitations",
    "action_path",
)
S2PKT03_REQUIRED_ACTION_WINDOWS = ("2h", "7d")
S2PKT03_REQUIRED_GATES = (
    "mail_contract_gate",
    "content_quality_gate",
    "content_ledger_gate",
    "action_roi_gate",
    "m2_scope_gate",
    "section_coverage_gate",
    "engineering_reproducibility_gate",
    "product_limit_action_gate",
    "hash_status_gate",
    "no_side_effect_gate",
)
S2PKT03_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PKT03_REPORT_FILENAME = "stage2_s2pkt03_m2_mail_report.json"
S2PKT04_M3_MAIL_MODEL_ID = "adp-s2pkt04-m3-mail-v1"
S2PKT04_ACCEPTANCE_ID = "ACC-S2PKT04-M3"
S2PKT04_TASK_ID = "S2PKT04"
S2PKT04_MAIL_PRODUCT_ID = "M3"
S2PKT04_PRIMARY_BOARD = "B3"
S2PKT04_REQUIRED_SECTIONS = (
    "legal_status",
    "capital_impact",
    "geopolitical_context",
    "personal_impact",
    "action_path",
)
S2PKT04_REQUIRED_ACTION_WINDOWS = ("2h", "30d")
S2PKT04_REQUIRED_GATES = (
    "mail_contract_gate",
    "content_quality_gate",
    "content_ledger_gate",
    "action_roi_gate",
    "m3_scope_gate",
    "section_coverage_gate",
    "legal_capital_geo_gate",
    "personal_impact_action_gate",
    "hash_status_gate",
    "no_side_effect_gate",
)
S2PKT04_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PKT04_REPORT_FILENAME = "stage2_s2pkt04_m3_mail_report.json"
S2PKT05_M4_MAIL_MODEL_ID = "adp-s2pkt05-m4-mail-v1"
S2PKT05_ACCEPTANCE_ID = "ACC-S2PKT05-M4"
S2PKT05_TASK_ID = "S2PKT05"
S2PKT05_MAIL_PRODUCT_ID = "M4"
S2PKT05_PRIMARY_BOARD = "B1-B6"
S2PKT05_REQUIRED_TERMINAL_MAILS = ("M1", "M2", "M3")
S2PKT05_REQUIRED_SECTIONS = (
    "cross_source_resonance",
    "contradictions",
    "era_mainline",
    "personal_action_mix",
    "review_reminders",
)
S2PKT05_DEFAULT_STAGGERED_WINDOWS = ("M1=07:30", "M2=11:30", "M3=17:00", "M4=21:30")
S2PKT05_REQUIRED_GATES = (
    "mail_contract_gate",
    "m1_terminal_gate",
    "m2_terminal_gate",
    "m3_terminal_gate",
    "m4_scope_gate",
    "staggered_schedule_gate",
    "watermark_gate",
    "duplicate_suppression_gate",
    "section_coverage_gate",
    "cross_board_synthesis_gate",
    "action_review_gate",
    "hash_status_gate",
    "no_side_effect_gate",
)
S2PKT05_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PKT05_REPORT_FILENAME = "stage2_s2pkt05_m4_mail_report.json"
S2PJT01_LIFECYCLE_STATE_MODEL_ID = "adp-s2pjt01-lifecycle-state-v1"
S2PJT01_ACCEPTANCE_ID = "ACC-S2PJT01-LIFECYCLE"
S2PJT01_TASK_ID = "S2PJT01"
S2PJT01_REQUIRED_STATES = ("REVIEW_DUE", "ACTION", "ASSET", "CONVERSION", "MASTERED")
S2PJT01_REQUIRED_LEDGER_TYPES = ("review", "action", "asset", "conversion", "mastery")
S2PJT01_REQUIRED_GATES = (
    "runtime_dashboard_gate",
    "state_coverage_gate",
    "append_only_history_gate",
    "count_conservation_gate",
    "ledger_mapping_gate",
    "migration_plan_gate",
    "no_side_effect_gate",
)
S2PJT01_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PJT01_REPORT_FILENAME = "stage2_s2pjt01_lifecycle_state_report.json"
S2PJT02_REVIEW_SCHEDULE_MODEL_ID = "adp-s2pjt02-review-schedule-v1"
S2PJT02_ACCEPTANCE_ID = "ACC-S2PJT02-REVIEW"
S2PJT02_TASK_ID = "S2PJT02"
S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS = (1, 3, 7, 14, 30, 90)
S2PJT02_REQUIRED_COUNT_BUCKETS = ("due_today", "due_next_7_days", "overdue", "completed")
S2PJT02_REQUIRED_GATES = (
    "lifecycle_state_gate",
    "schedule_policy_gate",
    "review_record_gate",
    "due_count_gate",
    "deterministic_queue_gate",
    "no_side_effect_gate",
)
S2PJT02_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PJT02_REPORT_FILENAME = "stage2_s2pjt02_review_schedule_report.json"
S2PJT03_ACTION_ROI_MODEL_ID = "adp-s2pjt03-action-asset-roi-ledger-v1"
S2PJT03_ACCEPTANCE_ID = "ACC-S2PJT03-ROI"
S2PJT03_TASK_ID = "S2PJT03"
S2PJT03_REQUIRED_ACTION_WINDOWS = ("15m", "2h", "7d", "30d")
S2PJT03_ALLOWED_ACTION_STATUSES = ("planned", "completed", "deferred")
S2PJT03_ALLOWED_ACTUAL_ROI_STATUSES = ("not_calculable", "calculated")
S2PJT03_REQUIRED_GATES = (
    "review_schedule_gate",
    "action_window_gate",
    "expected_roi_gate",
    "actual_roi_gate",
    "asset_trace_gate",
    "deterministic_ledger_gate",
    "no_side_effect_gate",
)
S2PJT03_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PJT03_REPORT_FILENAME = "stage2_s2pjt03_action_asset_roi_ledger_report.json"
S2PJT04_WEEKLY_REPORT_MODEL_ID = "adp-s2pjt04-weekly-report-v1"
S2PJT04_ACCEPTANCE_ID = "ACC-S2PJT04-WEEKLY"
S2PJT04_TASK_ID = "S2PJT04"
S2PJT04_REQUIRED_SECTIONS = (
    "weekly_mainline",
    "counterevidence",
    "review_summary",
    "action_summary",
    "asset_summary",
    "next_week_focus",
)
S2PJT04_MAX_WEEK_WINDOW_DAYS = 6
S2PJT04_REQUIRED_GATES = (
    "action_roi_gate",
    "week_window_gate",
    "section_trace_gate",
    "state_trace_gate",
    "no_duplication_gate",
    "next_focus_gate",
    "deterministic_report_gate",
    "no_side_effect_gate",
)
S2PJT04_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PJT04_REPORT_FILENAME = "stage2_s2pjt04_weekly_report.json"
S2PJT05_MONTHLY_REPORT_MODEL_ID = "adp-s2pjt05-monthly-report-v1"
S2PJT05_ACCEPTANCE_ID = "ACC-S2PJT05-MONTHLY"
S2PJT05_TASK_ID = "S2PJT05"
S2PJT05_REQUIRED_SECTIONS = (
    "monthly_era_mainline",
    "cognitive_delta",
    "capability_growth",
    "economic_conversion",
    "forecast_review",
    "next_month_focus",
)
S2PJT05_MAX_MONTH_WINDOW_DAYS = 30
S2PJT05_MIN_VERIFIABLE_CONVERSIONS = 1
S2PJT05_REQUIRED_GATES = (
    "weekly_report_gate",
    "month_window_gate",
    "cognitive_delta_gate",
    "capability_growth_gate",
    "conversion_trace_gate",
    "forecast_review_gate",
    "section_trace_gate",
    "deterministic_report_gate",
    "no_side_effect_gate",
)
S2PJT05_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PJT05_REPORT_FILENAME = "stage2_s2pjt05_monthly_report.json"
S2PHT05_CONTENT_QUALITY_MODEL_ID = "adp-s2pht05-content-quality-gate-v1"
S2PHT05_ACCEPTANCE_ID = "ACC-S2PHT05-CONTENT-GATE"
S2PHT05_TASK_ID = "S2PHT05"
S2PHT05_REQUIRED_DEPENDENCY_TASKS = ("S2PHT01", "S2PHT02", "S2PHT03", "S2PHT04")
S2PHT05_REQUIRED_GOLD_DIMENSIONS = (
    "mechanism_depth",
    "evidence_traceability",
    "claim_entailment",
    "quote_location",
    "counterevidence",
    "boundary_conditions",
    "personal_actionability",
    "template_novelty",
    "regression_compatibility",
    "chinese_clarity",
)
S2PHT05_MIN_GOLD_ITEMS = 10
S2PHT05_MIN_DIMENSION_SCORE = 4.0
S2PHT05_MAX_TEMPLATE_SIMILARITY = 0.35
S2PHT05_MIN_MANUAL_REVIEW_SAMPLES = 2
S2PHT05_REQUIRED_STAGE1_REGRESSION_CHECKS = ("arxiv_collection", "evidence_chain", "email_chain")
S2PHT05_ALLOWED_ENTAILMENT_STATES = ("supported", "partially_supported")
S2PHT05_REQUIRED_GATES = (
    "dependency_receipt_gate",
    "gold_dimension_gate",
    "entailment_gate",
    "quote_location_gate",
    "template_rate_gate",
    "counterevidence_gate",
    "personal_action_gate",
    "stage1_regression_gate",
    "manual_review_gate",
    "deterministic_gate",
    "no_side_effect_gate",
)
S2PHT05_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "stage2_production_accepted",
    "integrated_production_accepted",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "db_migration_executed",
    "schema_migration_allowed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "ranking_algorithm_changed",
    "source_adapter_changed",
    "email_frontstage_changed",
    "v7_1_current_switched",
    "v7_2_contract_files_changed",
)
S2PHT05_REPORT_FILENAME = "stage2_s2pht05_content_quality_gate_report.json"


def build_s2p1_preprint_promotion_report(
    *,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    replay_report: Mapping[str, Any] | None = None,
    shadow_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate source-level promotion gates for bioRxiv and medRxiv."""

    source_reports = []
    blocking_reasons: list[str] = []
    canonical_ids: set[str] = set()
    duplicate_canonical_ids: set[str] = set()
    for server in S2P1_REQUIRED_SERVERS:
        batch = source_batches.get(server)
        if not isinstance(batch, Mapping):
            source_reports.append({"server": server, "status": "blocked", "blocking_reasons": ["missing source batch"]})
            blocking_reasons.append(f"{server}: missing source batch")
            continue
        errors = validate_preprint_source_batch(batch)
        license_errors = _license_gate_errors(batch)
        version_errors = _version_gate_errors(batch)
        identity_ids = _canonical_ids(batch)
        for canonical_id in identity_ids:
            if canonical_id in canonical_ids:
                duplicate_canonical_ids.add(canonical_id)
            canonical_ids.add(canonical_id)
        reasons = errors + license_errors + version_errors
        source_reports.append(
            {
                "server": server,
                "status": "pass" if not reasons and batch.get("status") == "pass" else "blocked",
                "source_adapter": batch.get("source_adapter", ""),
                "source_item_count": len(batch.get("source_items") or []),
                "new_item_count": int(batch.get("new_item_count") or 0),
                "terminal_status": batch.get("terminal_status", ""),
                "identity_gate": "pass" if identity_ids else "blocked",
                "version_gate": "pass" if not version_errors else "blocked",
                "license_gate": "pass" if not license_errors else "blocked",
                "blocking_reasons": reasons,
            }
        )
        blocking_reasons.extend(f"{server}: {reason}" for reason in reasons)
    if duplicate_canonical_ids:
        blocking_reasons.append("duplicate canonical preprint documents: " + ", ".join(sorted(duplicate_canonical_ids)))

    replay_gate = _replay_gate(replay_report)
    shadow_gate = _shadow_gate(shadow_report)
    blocking_reasons.extend(replay_gate["blocking_reasons"])
    blocking_reasons.extend(shadow_gate["blocking_reasons"])
    source_gate_ready = all(item["status"] == "pass" for item in source_reports) and not duplicate_canonical_ids
    ready = source_gate_ready and replay_gate["status"] == "pass" and shadow_gate["status"] == "pass"
    return {
        "model_id": S2P1_PREPRINT_PROMOTION_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "source_gate_ready": source_gate_ready,
        "replay_gate_ready": replay_gate["status"] == "pass",
        "shadow_gate_ready": shadow_gate["status"] == "pass",
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "video_required": False,
        "source_reports": source_reports,
        "replay_gate": replay_gate,
        "shadow_gate": shadow_gate,
        "canonical_document_count": len(canonical_ids),
        "duplicate_canonical_ids": sorted(duplicate_canonical_ids),
        "blocking_reasons": blocking_reasons,
    }


def build_s2p1_preprint_daily_input(
    *,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a shadow daily input from bioRxiv/medRxiv SourceBatches."""

    scan = _preprint_scan(source_batches, generated_at=generated_at)
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    if scan["status"] == "blocked":
        return _blocked_daily_input(date, generated_at, queue_state, scan, scan["blocking_reasons"])
    selection = select_roi_candidate(scan["candidates"], queue_state["items"], recent_source_ids=recent_source_ids)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        return _blocked_daily_input(date, generated_at, queue_state, scan, list(selection.get("blocking_reasons") or []), selection=selection)
    updated_queue = update_candidate_queue(
        existing_items=queue_state["items"],
        new_candidates=scan["candidates"],
        selected_source_id=str(selected["source_id"]),
        generated_at=generated_at,
        max_items=max_queue_items,
    )
    daily_input = _daily_input_from_selection(selected, date=date, generated_at=generated_at, queue=updated_queue)
    return {
        "model_id": S2P1_PREPRINT_SHADOW_MODEL_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "pass",
        "daily_input_ready": True,
        "formal_production_inclusion": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "blocking_reasons": [],
    }


def run_s2p1_preprint_shadow_daily(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    write: bool = True,
) -> dict[str, Any]:
    """Run one no-send Stage 2 shadow daily path and persist local evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2p1-preprint-shadow"
    queue_path = state / S2P1_QUEUE_FILENAME
    ledger_path = state / S2P1_LEDGER_FILENAME
    queue_state = queue if queue is not None else _load_json(queue_path) if queue_path.exists() else None
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)

    daily_report = build_s2p1_preprint_daily_input(
        date=date,
        generated_at=generated_at,
        source_batches=source_batches,
        queue=queue_state,
        recent_source_ids=recent_source_ids,
    )
    if write:
        _write_json(run_dir / "adp-s2p1-preprint-daily-input-report.json", daily_report)
    if daily_report.get("daily_input_ready") is not True:
        return _write_or_return(
            _base_shadow_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=list(daily_report.get("blocking_reasons") or ["preprint daily input blocked"]),
                daily_report=daily_report,
            ),
            run_dir,
            write=write,
        )
    daily_input = daily_report["daily_input"]
    try:
        daily_run = run_daily_dry_run(
            daily_input["source_item"],
            daily_input["claims"],
            run_id=daily_input["run_id"],
            publication_id=daily_input["publication_id"],
            date=daily_input["date"],
            generated_at=generated_at,
            timezone=DEFAULT_TIMEZONE,
        )
    except (KeyError, PipelineError) as error:
        return _write_or_return(
            _base_shadow_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=[f"preprint shadow pipeline failed: {error}"],
                daily_report=daily_report,
            ),
            run_dir,
            write=write,
        )
    delivery_package = build_daily_delivery_package(
        daily_run,
        daily_input,
        {"status": "skipped", "release_ref": "", "assets": []},
        generated_at=generated_at,
    )
    notification = delivery_package["notification"]
    ledger_row = {
        "date": date,
        "generated_at": generated_at,
        "task_id": S2P1_TASK_ID,
        "source_id": daily_input["source_item"]["source_id"],
        "canonical_document_id": _canonical_document_id(daily_input["source_item"]),
        "title": daily_input["source_item"]["title"],
        "shadow_mode": True,
        "formal_production_inclusion": False,
        "email_state": "preview_only",
        "run_dir": str(run_dir),
        "queue_item_count": len(daily_report["candidate_queue"].get("items") or []),
    }
    if write:
        _write_json(run_dir / "adp-s2p1-preprint-daily-run.json", daily_run)
        _write_json(run_dir / "adp-s2p1-preprint-delivery-package.json", {k: v for k, v in delivery_package.items() if k != "notification"})
        _write_json(queue_path, daily_report["candidate_queue"])
        (run_dir / "email_preview.txt").write_text(notification.body, encoding="utf-8")
        (run_dir / "email_preview.html").write_text(notification.html_body, encoding="utf-8")
        _append_jsonl(ledger_path, ledger_row)
    report = _base_shadow_report(
        status="pass",
        date=date,
        generated_at=generated_at,
        state=state,
        run_dir=run_dir,
        blocking_reasons=[],
        daily_report=daily_report,
    )
    report.update(
        {
            "daily_run_status": daily_run["status"],
            "selected_source_id": daily_input["source_item"]["source_id"],
            "selected_title": daily_input["source_item"]["title"],
            "candidate_queue_path": str(queue_path),
            "content_ledger_path": str(ledger_path),
            "content_ledger_row": ledger_row,
            "email_preview_written": write,
            "email_preview_paths": {
                "plain": str(run_dir / "email_preview.txt"),
                "html": str(run_dir / "email_preview.html"),
            },
            "delivery_package": {k: v for k, v in delivery_package.items() if k != "notification"},
            "real_smtp_sent": False,
            "production_affected": False,
        }
    )
    return _write_or_return(report, run_dir, write=write)


def validate_s2p1_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2P1_PREPRINT_SHADOW_MODEL_ID:
        errors.append("S2P1 shadow report model_id must be adp-s2p1-preprint-shadow-daily-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2P1 shadow report status must be pass or blocked")
    for key in ("formal_production_inclusion", "github_cloud_schedule_enabled", "real_smtp_sent", "production_affected"):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2P1 shadow daily")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2P1 shadow report requires blocking_reasons")
    if report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing S2P1 shadow report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing S2P1 shadow report requires email_preview_written")
    return errors


def build_s2p2_top_journal_daily_input(
    *,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a no-send shadow daily input from top-journal public metadata."""

    scan = _top_journal_scan(source_batches, generated_at=generated_at)
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    if scan["status"] == "blocked":
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            scan["blocking_reasons"],
            model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
            task_id=S2P2_TASK_ID,
        )
    selection = select_roi_candidate(scan["candidates"], queue_state["items"], recent_source_ids=recent_source_ids)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            list(selection.get("blocking_reasons") or []),
            selection=selection,
            model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
            task_id=S2P2_TASK_ID,
        )
    updated_queue = update_candidate_queue(
        existing_items=queue_state["items"],
        new_candidates=scan["candidates"],
        selected_source_id=str(selected["source_id"]),
        generated_at=generated_at,
        max_items=max_queue_items,
    )
    daily_input = _daily_input_from_selection(
        selected,
        date=date,
        generated_at=generated_at,
        queue=updated_queue,
        run_label="s2p2-top-journal",
        scan_scope="s2p2_top_journal_shadow",
        source_count=len(S2P2_REQUIRED_JOURNALS),
        task_id=S2P2_TASK_ID,
    )
    return {
        "model_id": S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
        "task_id": S2P2_TASK_ID,
        "legacy_task_id": S2P2_LEGACY_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "pass",
        "daily_input_ready": True,
        "formal_production_inclusion": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "blocking_reasons": [],
    }


def run_s2p2_top_journal_shadow_daily(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    write: bool = True,
) -> dict[str, Any]:
    """Run one no-send Stage 2 top-journal shadow daily path and persist evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2p2-top-journal-shadow"
    queue_path = state / S2P2_QUEUE_FILENAME
    ledger_path = state / S2P2_LEDGER_FILENAME
    queue_state = queue if queue is not None else _load_json(queue_path) if queue_path.exists() else None
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)

    daily_report = build_s2p2_top_journal_daily_input(
        date=date,
        generated_at=generated_at,
        source_batches=source_batches,
        queue=queue_state,
        recent_source_ids=recent_source_ids,
    )
    if write:
        _write_json(run_dir / "adp-s2p2-top-journal-daily-input-report.json", daily_report)
    if daily_report.get("daily_input_ready") is not True:
        return _write_or_return_s2p2(
            _base_shadow_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=list(daily_report.get("blocking_reasons") or ["top-journal daily input blocked"]),
                daily_report=daily_report,
                model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
                acceptance_id=S2P2_ACCEPTANCE_ID,
                task_id=S2P2_TASK_ID,
            ),
            run_dir,
            write=write,
        )
    daily_input = daily_report["daily_input"]
    try:
        daily_run = run_daily_dry_run(
            daily_input["source_item"],
            daily_input["claims"],
            run_id=daily_input["run_id"],
            publication_id=daily_input["publication_id"],
            date=daily_input["date"],
            generated_at=generated_at,
            timezone=DEFAULT_TIMEZONE,
        )
    except (KeyError, PipelineError) as error:
        return _write_or_return_s2p2(
            _base_shadow_report(
                status="blocked",
                date=date,
                generated_at=generated_at,
                state=state,
                run_dir=run_dir,
                blocking_reasons=[f"top-journal shadow pipeline failed: {error}"],
                daily_report=daily_report,
                model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
                acceptance_id=S2P2_ACCEPTANCE_ID,
                task_id=S2P2_TASK_ID,
            ),
            run_dir,
            write=write,
        )
    delivery_package = build_daily_delivery_package(
        daily_run,
        daily_input,
        {"status": "skipped", "release_ref": "", "assets": []},
        generated_at=generated_at,
    )
    notification = delivery_package["notification"]
    ledger_row = {
        "date": date,
        "generated_at": generated_at,
        "task_id": S2P2_TASK_ID,
        "legacy_task_id": S2P2_LEGACY_TASK_ID,
        "source_id": daily_input["source_item"]["source_id"],
        "canonical_document_id": _canonical_document_id(daily_input["source_item"]),
        "title": daily_input["source_item"]["title"],
        "shadow_mode": True,
        "formal_production_inclusion": False,
        "email_state": "preview_only",
        "run_dir": str(run_dir),
        "queue_item_count": len(daily_report["candidate_queue"].get("items") or []),
    }
    if write:
        _write_json(run_dir / "adp-s2p2-top-journal-daily-run.json", daily_run)
        _write_json(run_dir / "adp-s2p2-top-journal-delivery-package.json", {k: v for k, v in delivery_package.items() if k != "notification"})
        _write_json(queue_path, daily_report["candidate_queue"])
        (run_dir / "email_preview.txt").write_text(notification.body, encoding="utf-8")
        (run_dir / "email_preview.html").write_text(notification.html_body, encoding="utf-8")
        _append_jsonl(ledger_path, ledger_row)
    report = _base_shadow_report(
        status="pass",
        date=date,
        generated_at=generated_at,
        state=state,
        run_dir=run_dir,
        blocking_reasons=[],
        daily_report=daily_report,
        model_id=S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
        acceptance_id=S2P2_ACCEPTANCE_ID,
        task_id=S2P2_TASK_ID,
    )
    report.update(
        {
            "daily_run_status": daily_run["status"],
            "selected_source_id": daily_input["source_item"]["source_id"],
            "selected_title": daily_input["source_item"]["title"],
            "candidate_queue_path": str(queue_path),
            "content_ledger_path": str(ledger_path),
            "content_ledger_row": ledger_row,
            "email_preview_written": write,
            "email_preview_paths": {
                "plain": str(run_dir / "email_preview.txt"),
                "html": str(run_dir / "email_preview.html"),
            },
            "delivery_package": {k: v for k, v in delivery_package.items() if k != "notification"},
            "real_smtp_sent": False,
            "production_affected": False,
        }
    )
    return _write_or_return_s2p2(report, run_dir, write=write)


def validate_s2p2_top_journal_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2P2_TOP_JOURNAL_SHADOW_MODEL_ID:
        errors.append("S2PC shadow report model_id must be adp-s2pct01-top-journal-shadow-daily-v1")
    if report.get("task_id") != S2P2_TASK_ID:
        errors.append("S2PC shadow report task_id must be S2PCT01")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2P2 shadow report status must be pass or blocked")
    for key in ("formal_production_inclusion", "github_cloud_schedule_enabled", "real_smtp_sent", "production_affected"):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2P2 top-journal shadow daily")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2P2 shadow report requires blocking_reasons")
    if report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing S2P2 shadow report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing S2P2 shadow report requires email_preview_written")
        source_id = str(report.get("selected_source_id") or "")
        if not source_id.startswith("nature:s41586-"):
            errors.append("passing S2P2 shadow report requires selected Nature main-journal source_id")
    return errors


def build_s2pct02_science_daily_input(
    *,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a no-send S2PCT02 Science shadow daily input from public metadata."""

    scan = _top_journal_scan(
        source_batches,
        generated_at=generated_at,
        required_journals=S2PCT02_REQUIRED_JOURNALS,
        model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
        scan_id="s2pct02-science-scan:shadow",
        no_candidate_message="no eligible new Science main-journal candidates for shadow daily input",
    )
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    if scan["status"] == "blocked":
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            scan["blocking_reasons"],
            model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            task_id=S2PCT02_TASK_ID,
        )
    selection = select_roi_candidate(scan["candidates"], queue_state["items"], recent_source_ids=recent_source_ids)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            list(selection.get("blocking_reasons") or []),
            selection=selection,
            model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            task_id=S2PCT02_TASK_ID,
        )
    updated_queue = update_candidate_queue(
        existing_items=queue_state["items"],
        new_candidates=scan["candidates"],
        selected_source_id=str(selected["source_id"]),
        generated_at=generated_at,
        max_items=max_queue_items,
    )
    daily_input = _daily_input_from_selection(
        selected,
        date=date,
        generated_at=generated_at,
        queue=updated_queue,
        run_label="s2pct02-science",
        scan_scope="s2pct02_science_shadow",
        source_count=len(S2PCT02_REQUIRED_JOURNALS),
        task_id=S2PCT02_TASK_ID,
    )
    return {
        "model_id": S2PCT02_SCIENCE_SHADOW_MODEL_ID,
        "task_id": S2PCT02_TASK_ID,
        "legacy_task_id": S2PCT02_LEGACY_TASK_ID,
        "phase": "S2PC",
        "acceptance_id": S2PCT02_ACCEPTANCE_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "pass",
        "daily_input_ready": True,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "blocking_reasons": [],
    }


def run_s2pct02_science_shadow_daily(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    write: bool = True,
) -> dict[str, Any]:
    """Run one no-send S2PCT02 Science shadow daily path and persist evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct02-science-shadow"
    queue_path = state / S2PCT02_QUEUE_FILENAME
    ledger_path = state / S2PCT02_LEDGER_FILENAME
    queue_state = queue if queue is not None else _load_json(queue_path) if queue_path.exists() else None
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)

    daily_report = build_s2pct02_science_daily_input(
        date=date,
        generated_at=generated_at,
        source_batches=source_batches,
        queue=queue_state,
        recent_source_ids=recent_source_ids,
    )
    if write:
        _write_json(run_dir / "adp-s2pct02-science-daily-input-report.json", daily_report)
    if daily_report.get("daily_input_ready") is not True:
        report = _base_shadow_report(
            status="blocked",
            date=date,
            generated_at=generated_at,
            state=state,
            run_dir=run_dir,
            blocking_reasons=list(daily_report.get("blocking_reasons") or ["Science daily input blocked"]),
            daily_report=daily_report,
            model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            acceptance_id=S2PCT02_ACCEPTANCE_ID,
            task_id=S2PCT02_TASK_ID,
        )
        report["legacy_task_id"] = S2PCT02_LEGACY_TASK_ID
        return _write_or_return_s2pct02(report, run_dir, write=write)
    daily_input = daily_report["daily_input"]
    try:
        daily_run = run_daily_dry_run(
            daily_input["source_item"],
            daily_input["claims"],
            run_id=daily_input["run_id"],
            publication_id=daily_input["publication_id"],
            date=daily_input["date"],
            generated_at=generated_at,
            timezone=DEFAULT_TIMEZONE,
        )
    except (KeyError, PipelineError) as error:
        report = _base_shadow_report(
            status="blocked",
            date=date,
            generated_at=generated_at,
            state=state,
            run_dir=run_dir,
            blocking_reasons=[f"Science shadow pipeline failed: {error}"],
            daily_report=daily_report,
            model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
            acceptance_id=S2PCT02_ACCEPTANCE_ID,
            task_id=S2PCT02_TASK_ID,
        )
        report["legacy_task_id"] = S2PCT02_LEGACY_TASK_ID
        return _write_or_return_s2pct02(report, run_dir, write=write)
    delivery_package = build_daily_delivery_package(
        daily_run,
        daily_input,
        {"status": "skipped", "release_ref": "", "assets": []},
        generated_at=generated_at,
    )
    notification = delivery_package["notification"]
    ledger_row = {
        "date": date,
        "generated_at": generated_at,
        "task_id": S2PCT02_TASK_ID,
        "legacy_task_id": S2PCT02_LEGACY_TASK_ID,
        "source_id": daily_input["source_item"]["source_id"],
        "canonical_document_id": _canonical_document_id(daily_input["source_item"]),
        "title": daily_input["source_item"]["title"],
        "shadow_mode": True,
        "formal_production_inclusion": False,
        "email_state": "preview_only",
        "run_dir": str(run_dir),
        "queue_item_count": len(daily_report["candidate_queue"].get("items") or []),
    }
    if write:
        _write_json(run_dir / "adp-s2pct02-science-daily-run.json", daily_run)
        _write_json(run_dir / "adp-s2pct02-science-delivery-package.json", {k: v for k, v in delivery_package.items() if k != "notification"})
        _write_json(queue_path, daily_report["candidate_queue"])
        (run_dir / "email_preview.txt").write_text(notification.body, encoding="utf-8")
        (run_dir / "email_preview.html").write_text(notification.html_body, encoding="utf-8")
        _append_jsonl(ledger_path, ledger_row)
    report = _base_shadow_report(
        status="pass",
        date=date,
        generated_at=generated_at,
        state=state,
        run_dir=run_dir,
        blocking_reasons=[],
        daily_report=daily_report,
        model_id=S2PCT02_SCIENCE_SHADOW_MODEL_ID,
        acceptance_id=S2PCT02_ACCEPTANCE_ID,
        task_id=S2PCT02_TASK_ID,
    )
    report.update(
        {
            "legacy_task_id": S2PCT02_LEGACY_TASK_ID,
            "daily_run_status": daily_run["status"],
            "selected_source_id": daily_input["source_item"]["source_id"],
            "selected_title": daily_input["source_item"]["title"],
            "candidate_queue_path": str(queue_path),
            "content_ledger_path": str(ledger_path),
            "content_ledger_row": ledger_row,
            "email_preview_written": write,
            "email_preview_paths": {
                "plain": str(run_dir / "email_preview.txt"),
                "html": str(run_dir / "email_preview.html"),
            },
            "delivery_package": {k: v for k, v in delivery_package.items() if k != "notification"},
            "real_smtp_sent": False,
            "production_affected": False,
            "d2_source_domain_accepted": False,
            "stage2_production_accepted": False,
            "integrated_production_accepted": False,
        }
    )
    return _write_or_return_s2pct02(report, run_dir, write=write)


def validate_s2pct02_science_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT02_SCIENCE_SHADOW_MODEL_ID:
        errors.append("S2PCT02 shadow report model_id must be adp-s2pct02-science-shadow-daily-v1")
    if report.get("task_id") != S2PCT02_TASK_ID:
        errors.append("S2PCT02 shadow report task_id must be S2PCT02")
    if report.get("acceptance_id") != S2PCT02_ACCEPTANCE_ID:
        errors.append("S2PCT02 shadow report acceptance_id must be ACC-S2PCT02-SCIENCE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT02 shadow report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "production_affected",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT02 Science shadow daily")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT02 shadow report requires blocking_reasons")
    if report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing S2PCT02 shadow report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing S2PCT02 shadow report requires email_preview_written")
        source_item = (
            report.get("daily_report", {}).get("daily_input", {}).get("source_item", {})
            if isinstance(report.get("daily_report"), Mapping)
            else {}
        )
        if not isinstance(source_item, Mapping):
            source_item = {}
        source_id = str(report.get("selected_source_id") or source_item.get("source_id") or "")
        if not source_id.startswith("science:10.1126/science."):
            errors.append("passing S2PCT02 shadow report requires selected Science main-journal source_id")
        top_journal = source_item.get("metadata", {}).get("top_journal", {}) if isinstance(source_item.get("metadata"), Mapping) else {}
        article_type = str(top_journal.get("article_type") or "") if isinstance(top_journal, Mapping) else ""
        if article_type not in SCIENCE_ACCEPTED_ARTICLE_TYPES:
            errors.append("passing S2PCT02 shadow report requires Science article_type classification")
    return errors


def build_s2pct03_lancet_daily_input(
    *,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    max_queue_items: int = CANDIDATE_QUEUE_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a no-send S2PCT03 The Lancet shadow daily input from public metadata."""

    scan = _top_journal_scan(
        source_batches,
        generated_at=generated_at,
        required_journals=S2PCT03_REQUIRED_JOURNALS,
        model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
        scan_id="s2pct03-lancet-scan:shadow",
        no_candidate_message="no eligible new The Lancet main-journal candidates for shadow daily input",
    )
    queue_state = normalize_candidate_queue(queue, generated_at=generated_at)
    if scan["status"] == "blocked":
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            scan["blocking_reasons"],
            model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
            task_id=S2PCT03_TASK_ID,
        )
    selection = select_roi_candidate(scan["candidates"], queue_state["items"], recent_source_ids=recent_source_ids)
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        return _blocked_daily_input(
            date,
            generated_at,
            queue_state,
            scan,
            list(selection.get("blocking_reasons") or []),
            selection=selection,
            model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
            task_id=S2PCT03_TASK_ID,
        )
    updated_queue = update_candidate_queue(
        existing_items=queue_state["items"],
        new_candidates=scan["candidates"],
        selected_source_id=str(selected["source_id"]),
        generated_at=generated_at,
        max_items=max_queue_items,
    )
    daily_input = _daily_input_from_selection(
        selected,
        date=date,
        generated_at=generated_at,
        queue=updated_queue,
        run_label="s2pct03-lancet",
        scan_scope="s2pct03_lancet_shadow",
        source_count=len(S2PCT03_REQUIRED_JOURNALS),
        task_id=S2PCT03_TASK_ID,
    )
    return {
        "model_id": S2PCT03_LANCET_SHADOW_MODEL_ID,
        "task_id": S2PCT03_TASK_ID,
        "legacy_task_id": S2PCT03_LEGACY_TASK_ID,
        "phase": "S2PC",
        "acceptance_id": S2PCT03_ACCEPTANCE_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "pass",
        "daily_input_ready": True,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": updated_queue,
        "selection": selection,
        "daily_input": daily_input,
        "blocking_reasons": [],
    }


def run_s2pct03_lancet_shadow_daily(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    queue: Mapping[str, Any] | None = None,
    recent_source_ids: Sequence[str] = (),
    write: bool = True,
) -> dict[str, Any]:
    """Run one no-send S2PCT03 The Lancet shadow daily path and persist evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct03-lancet-shadow"
    queue_path = state / S2PCT03_QUEUE_FILENAME
    ledger_path = state / S2PCT03_LEDGER_FILENAME
    queue_state = queue if queue is not None else _load_json(queue_path) if queue_path.exists() else None
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)

    daily_report = build_s2pct03_lancet_daily_input(
        date=date,
        generated_at=generated_at,
        source_batches=source_batches,
        queue=queue_state,
        recent_source_ids=recent_source_ids,
    )
    if write:
        _write_json(run_dir / "adp-s2pct03-lancet-daily-input-report.json", daily_report)
    if daily_report.get("daily_input_ready") is not True:
        report = _base_shadow_report(
            status="blocked",
            date=date,
            generated_at=generated_at,
            state=state,
            run_dir=run_dir,
            blocking_reasons=list(daily_report.get("blocking_reasons") or ["The Lancet daily input blocked"]),
            daily_report=daily_report,
            model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
            acceptance_id=S2PCT03_ACCEPTANCE_ID,
            task_id=S2PCT03_TASK_ID,
        )
        report["legacy_task_id"] = S2PCT03_LEGACY_TASK_ID
        return _write_or_return_s2pct03(report, run_dir, write=write)
    daily_input = daily_report["daily_input"]
    try:
        daily_run = run_daily_dry_run(
            daily_input["source_item"],
            daily_input["claims"],
            run_id=daily_input["run_id"],
            publication_id=daily_input["publication_id"],
            date=daily_input["date"],
            generated_at=generated_at,
            timezone=DEFAULT_TIMEZONE,
        )
    except (KeyError, PipelineError) as error:
        report = _base_shadow_report(
            status="blocked",
            date=date,
            generated_at=generated_at,
            state=state,
            run_dir=run_dir,
            blocking_reasons=[f"The Lancet shadow pipeline failed: {error}"],
            daily_report=daily_report,
            model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
            acceptance_id=S2PCT03_ACCEPTANCE_ID,
            task_id=S2PCT03_TASK_ID,
        )
        report["legacy_task_id"] = S2PCT03_LEGACY_TASK_ID
        return _write_or_return_s2pct03(report, run_dir, write=write)
    delivery_package = build_daily_delivery_package(
        daily_run,
        daily_input,
        {"status": "skipped", "release_ref": "", "assets": []},
        generated_at=generated_at,
    )
    notification = delivery_package["notification"]
    ledger_row = {
        "date": date,
        "generated_at": generated_at,
        "task_id": S2PCT03_TASK_ID,
        "legacy_task_id": S2PCT03_LEGACY_TASK_ID,
        "source_id": daily_input["source_item"]["source_id"],
        "canonical_document_id": _canonical_document_id(daily_input["source_item"]),
        "title": daily_input["source_item"]["title"],
        "shadow_mode": True,
        "formal_production_inclusion": False,
        "email_state": "preview_only",
        "run_dir": str(run_dir),
        "queue_item_count": len(daily_report["candidate_queue"].get("items") or []),
    }
    if write:
        _write_json(run_dir / "adp-s2pct03-lancet-daily-run.json", daily_run)
        _write_json(run_dir / "adp-s2pct03-lancet-delivery-package.json", {k: v for k, v in delivery_package.items() if k != "notification"})
        _write_json(queue_path, daily_report["candidate_queue"])
        (run_dir / "email_preview.txt").write_text(notification.body, encoding="utf-8")
        (run_dir / "email_preview.html").write_text(notification.html_body, encoding="utf-8")
        _append_jsonl(ledger_path, ledger_row)
    report = _base_shadow_report(
        status="pass",
        date=date,
        generated_at=generated_at,
        state=state,
        run_dir=run_dir,
        blocking_reasons=[],
        daily_report=daily_report,
        model_id=S2PCT03_LANCET_SHADOW_MODEL_ID,
        acceptance_id=S2PCT03_ACCEPTANCE_ID,
        task_id=S2PCT03_TASK_ID,
    )
    report.update(
        {
            "legacy_task_id": S2PCT03_LEGACY_TASK_ID,
            "daily_run_status": daily_run["status"],
            "selected_source_id": daily_input["source_item"]["source_id"],
            "selected_title": daily_input["source_item"]["title"],
            "candidate_queue_path": str(queue_path),
            "content_ledger_path": str(ledger_path),
            "content_ledger_row": ledger_row,
            "email_preview_written": write,
            "email_preview_paths": {
                "plain": str(run_dir / "email_preview.txt"),
                "html": str(run_dir / "email_preview.html"),
            },
            "delivery_package": {k: v for k, v in delivery_package.items() if k != "notification"},
            "real_smtp_sent": False,
            "production_affected": False,
            "d2_source_domain_accepted": False,
            "stage2_production_accepted": False,
            "integrated_production_accepted": False,
        }
    )
    return _write_or_return_s2pct03(report, run_dir, write=write)


def validate_s2pct03_lancet_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT03_LANCET_SHADOW_MODEL_ID:
        errors.append("S2PCT03 shadow report model_id must be adp-s2pct03-lancet-shadow-daily-v1")
    if report.get("task_id") != S2PCT03_TASK_ID:
        errors.append("S2PCT03 shadow report task_id must be S2PCT03")
    if report.get("acceptance_id") != S2PCT03_ACCEPTANCE_ID:
        errors.append("S2PCT03 shadow report acceptance_id must be ACC-S2PCT03-LANCET")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT03 shadow report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "production_affected",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT03 The Lancet shadow daily")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT03 shadow report requires blocking_reasons")
    if report.get("status") == "pass":
        if report.get("daily_input_ready") is not True:
            errors.append("passing S2PCT03 shadow report requires daily_input_ready")
        if report.get("email_preview_written") is not True:
            errors.append("passing S2PCT03 shadow report requires email_preview_written")
        source_item = (
            report.get("daily_report", {}).get("daily_input", {}).get("source_item", {})
            if isinstance(report.get("daily_report"), Mapping)
            else {}
        )
        if not isinstance(source_item, Mapping):
            source_item = {}
        source_id = str(report.get("selected_source_id") or source_item.get("source_id") or "")
        if not source_id.startswith("lancet:10.1016/s0140-6736"):
            errors.append("passing S2PCT03 shadow report requires selected The Lancet main-journal DOI source_id")
        top_journal = source_item.get("metadata", {}).get("top_journal", {}) if isinstance(source_item.get("metadata"), Mapping) else {}
        article_type = str(top_journal.get("article_type") or "") if isinstance(top_journal, Mapping) else ""
        if article_type not in LANCET_ACCEPTED_ARTICLE_TYPES:
            errors.append("passing S2PCT03 shadow report requires Lancet article_type classification")
        if isinstance(top_journal, Mapping):
            if top_journal.get("index_alignment_gate") != "pass":
                errors.append("passing S2PCT03 shadow report requires Lancet index_alignment_gate")
            medical_indexing = top_journal.get("medical_indexing")
            if not isinstance(medical_indexing, Mapping):
                errors.append("passing S2PCT03 shadow report requires medical_indexing")
            elif medical_indexing.get("pubmed_relation_gate") not in {"doi_query_ready", "pmid_present"}:
                errors.append("passing S2PCT03 shadow report requires PubMed DOI relationship gate")
    return errors


def build_s2pct04_top_journal_profile_report(
    *,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    publication_events: Sequence[Mapping[str, Any]] = (),
    prior_profile_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build metadata-only profile/relation evidence across completed D2 top journals."""

    source_profiles, relation_edges, source_reports, source_errors = _top_journal_profiles_from_batches(
        source_batches,
        generated_at=generated_at,
    )
    known_targets = {str(profile.get("canonical_document_id") or "") for profile in source_profiles}
    prior_index = _prior_profile_state_index(prior_profile_state)
    known_targets.update(prior_index)
    event_profiles, event_edges, forced_updates, event_reports, event_errors = _top_journal_profiles_from_publication_events(
        publication_events,
        generated_at=generated_at,
        known_targets=known_targets,
        prior_index=prior_index,
    )
    profiles = source_profiles + event_profiles
    relation_edges = relation_edges + event_edges
    observed_profile_kinds = sorted({str(profile.get("profile_kind") or "") for profile in profiles if profile.get("profile_kind")})
    missing_profile_kinds = [kind for kind in S2PCT04_REQUIRED_PROFILE_KINDS if kind not in observed_profile_kinds]
    duplicate_profile_ids = _duplicate_values(str(profile.get("profile_id") or "") for profile in profiles)
    relation_errors = _publication_relation_errors(profiles, relation_edges)
    forced_event_errors = _forced_event_update_errors(event_profiles, forced_updates)
    blocking_reasons = source_errors + event_errors + relation_errors + forced_event_errors
    if missing_profile_kinds:
        blocking_reasons.append(f"missing required top-journal profile kinds: {', '.join(missing_profile_kinds)}")
    if duplicate_profile_ids:
        blocking_reasons.append("duplicate top-journal profile ids: " + ", ".join(duplicate_profile_ids))
    taxonomy_gate = "pass" if not missing_profile_kinds and not duplicate_profile_ids else "blocked"
    relation_gate = "pass" if not relation_errors and relation_edges else "blocked"
    forced_gate = "pass" if not forced_event_errors and _forced_event_kinds(forced_updates) == set(S2PCT04_FORCED_EVENT_TYPES) else "blocked"
    if forced_gate == "blocked" and not forced_event_errors:
        blocking_reasons.append("correction and retraction forced-event updates are both required")
    status = "pass" if not blocking_reasons and taxonomy_gate == relation_gate == forced_gate == "pass" else "blocked"
    return {
        "model_id": S2PCT04_JOURNAL_PROFILE_MODEL_ID,
        "acceptance_id": S2PCT04_ACCEPTANCE_ID,
        "task_id": S2PCT04_TASK_ID,
        "legacy_task_id": S2PCT04_LEGACY_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "profile_taxonomy_gate": taxonomy_gate,
        "publication_relation_gate": relation_gate,
        "forced_event_update_gate": forced_gate,
        "required_profile_kinds": list(S2PCT04_REQUIRED_PROFILE_KINDS),
        "profile_kinds_observed": observed_profile_kinds,
        "source_reports": source_reports,
        "event_reports": event_reports,
        "source_profile_count": len(source_profiles),
        "publication_event_count": len(publication_events),
        "relation_edge_count": len(relation_edges),
        "forced_event_update_count": len(forced_updates),
        "source_profiles": profiles,
        "publication_relation_edges": relation_edges,
        "forced_event_updates": forced_updates,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "production_affected": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "blocking_reasons": blocking_reasons,
    }


def run_s2pct04_top_journal_profile_shadow(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_batches: Mapping[str, Mapping[str, Any]],
    publication_events: Sequence[Mapping[str, Any]] = (),
    prior_profile_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PCT04 metadata-only top-journal profile/relation evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct04-top-journal-profile-shadow"
    ledger_path = state / S2PCT04_LEDGER_FILENAME
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pct04_top_journal_profile_report(
        generated_at=generated_at,
        source_batches=source_batches,
        publication_events=publication_events,
        prior_profile_state=prior_profile_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "profile_report_path": str(run_dir / "adp-s2pct04-top-journal-profile-report.json"),
            "profile_ledger_path": str(ledger_path),
            "profile_ledger_row_count": len(report.get("forced_event_updates") or []),
        }
    )
    if write:
        for row in report.get("forced_event_updates") or []:
            if isinstance(row, Mapping):
                _append_jsonl(ledger_path, row)
    return _write_or_return_s2pct04(report, run_dir, write=write)


def validate_s2pct04_top_journal_profile_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT04_JOURNAL_PROFILE_MODEL_ID:
        errors.append("S2PCT04 profile report model_id must be adp-s2pct04-top-journal-profile-v1")
    if report.get("task_id") != S2PCT04_TASK_ID:
        errors.append("S2PCT04 profile report task_id must be S2PCT04")
    if report.get("legacy_task_id") != S2PCT04_LEGACY_TASK_ID:
        errors.append("S2PCT04 profile report legacy_task_id must be S2P2T04")
    if report.get("acceptance_id") != S2PCT04_ACCEPTANCE_ID:
        errors.append("S2PCT04 profile report acceptance_id must be ACC-S2PCT04-JOURNAL-PROFILE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT04 profile report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT04 top-journal profile shadow")
    profiles = report.get("source_profiles")
    edges = report.get("publication_relation_edges")
    updates = report.get("forced_event_updates")
    if not isinstance(profiles, list):
        errors.append("S2PCT04 source_profiles must be a list")
        profiles = []
    if not isinstance(edges, list):
        errors.append("S2PCT04 publication_relation_edges must be a list")
        edges = []
    if not isinstance(updates, list):
        errors.append("S2PCT04 forced_event_updates must be a list")
        updates = []
    observed = set(report.get("profile_kinds_observed") or [])
    missing = [kind for kind in S2PCT04_REQUIRED_PROFILE_KINDS if kind not in observed]
    if missing:
        errors.append("S2PCT04 profile taxonomy missing required kinds: " + ", ".join(missing))
    profile_ids: set[str] = set()
    for index, profile in enumerate(profiles):
        if not isinstance(profile, Mapping):
            errors.append(f"source_profiles[{index}] must be an object")
            continue
        profile_id = str(profile.get("profile_id") or "")
        if not profile_id:
            errors.append(f"source_profiles[{index}].profile_id is required")
        if profile_id in profile_ids:
            errors.append(f"duplicate S2PCT04 profile_id: {profile_id}")
        profile_ids.add(profile_id)
        if profile.get("metadata_only") is not True:
            errors.append(f"source_profiles[{index}].metadata_only must be true")
        if profile.get("profile_kind") not in S2PCT04_REQUIRED_PROFILE_KINDS:
            errors.append(f"source_profiles[{index}].profile_kind is not supported")
        if not profile.get("canonical_document_id"):
            errors.append(f"source_profiles[{index}].canonical_document_id is required")
        if profile.get("profile_kind") in S2PCT04_FORCED_EVENT_TYPES and not profile.get("target_canonical_document_id"):
            errors.append(f"source_profiles[{index}] forced event requires target_canonical_document_id")
    for index, edge in enumerate(edges):
        if not isinstance(edge, Mapping):
            errors.append(f"publication_relation_edges[{index}] must be an object")
            continue
        if not edge.get("relation_type"):
            errors.append(f"publication_relation_edges[{index}].relation_type is required")
        if not edge.get("source_canonical_document_id"):
            errors.append(f"publication_relation_edges[{index}].source_canonical_document_id is required")
        if edge.get("target_required") is True and not edge.get("target_canonical_document_id"):
            errors.append(f"publication_relation_edges[{index}] required target_canonical_document_id is missing")
        if edge.get("metadata_only") is not True:
            errors.append(f"publication_relation_edges[{index}].metadata_only must be true")
    update_kinds = _forced_event_kinds(updates)
    if update_kinds != set(S2PCT04_FORCED_EVENT_TYPES):
        errors.append("S2PCT04 forced_event_updates must include correction and retraction")
    for index, update in enumerate(updates):
        if not isinstance(update, Mapping):
            errors.append(f"forced_event_updates[{index}] must be an object")
            continue
        if update.get("event_type") not in S2PCT04_FORCED_EVENT_TYPES:
            errors.append(f"forced_event_updates[{index}].event_type must be correction or retraction")
        if not update.get("target_canonical_document_id"):
            errors.append(f"forced_event_updates[{index}].target_canonical_document_id is required")
        if update.get("forced_review_required") is not True:
            errors.append(f"forced_event_updates[{index}].forced_review_required must be true")
        if update.get("updated_conclusion_state") not in {"requires_revision", "invalidated"}:
            errors.append(f"forced_event_updates[{index}].updated_conclusion_state is invalid")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT04 profile report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in ("profile_taxonomy_gate", "publication_relation_gate", "forced_event_update_gate"):
            if report.get(key) != "pass":
                errors.append(f"passing S2PCT04 profile report requires {key}=pass")
    return errors


def build_s2pct05_engineering_signal_report(
    *,
    generated_at: str,
    profile_report: Mapping[str, Any],
    engineering_signals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build metadata-only public engineering signal evidence after S2PCT04."""

    profile_errors = validate_s2pct04_top_journal_profile_report(profile_report)
    profile_gate = "pass" if not profile_errors and profile_report.get("status") == "pass" else "blocked"
    known_documents = _s2pct05_known_documents(profile_report)
    normalized_signals, signal_reports, signal_errors = _s2pct05_normalize_engineering_signals(
        engineering_signals,
        known_documents=known_documents,
        generated_at=generated_at,
    )
    observed_signal_types = sorted({str(signal.get("signal_type") or "") for signal in normalized_signals if signal.get("signal_type")})
    missing_signal_types = [signal_type for signal_type in S2PCT05_REQUIRED_SIGNAL_TYPES if signal_type not in observed_signal_types]
    duplicate_signal_ids = _duplicate_values(str(signal.get("signal_id") or "") for signal in normalized_signals)
    officiality_errors = _s2pct05_officiality_errors(normalized_signals) + [
        reason for reason in signal_errors if "officiality" in reason
    ]
    version_errors = _s2pct05_version_errors(normalized_signals) + [
        reason for reason in signal_errors if "version_reference" in reason
    ]
    relation_errors = _s2pct05_relation_errors(normalized_signals, known_documents) + [
        reason for reason in signal_errors if "canonical_document_id" in reason or "paper_relation_type" in reason
    ]
    reproducibility_errors = _s2pct05_reproducibility_errors(normalized_signals) + [
        reason for reason in signal_errors if "reproducibility" in reason or "metric_name" in reason
    ]
    officiality_gate = "pass" if not officiality_errors else "blocked"
    version_gate = "pass" if not version_errors else "blocked"
    relation_gate = "pass" if not relation_errors else "blocked"
    reproducibility_gate = "pass" if not reproducibility_errors else "blocked"
    blocking_reasons = list(profile_errors) + signal_errors
    if profile_gate != "pass":
        blocking_reasons.append("S2PCT04 profile report must pass before S2PCT05 engineering signals")
    if missing_signal_types:
        blocking_reasons.append("missing required engineering signal types: " + ", ".join(missing_signal_types))
    if duplicate_signal_ids:
        blocking_reasons.append("duplicate engineering signal ids: " + ", ".join(duplicate_signal_ids))
    for gate_errors in (officiality_errors, version_errors, relation_errors, reproducibility_errors):
        for reason in gate_errors:
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)
    taxonomy_gate = "pass" if not missing_signal_types and not duplicate_signal_ids else "blocked"
    status = (
        "pass"
        if not blocking_reasons
        and profile_gate == taxonomy_gate == officiality_gate == version_gate == relation_gate == reproducibility_gate == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PCT05_ENGINEERING_SIGNAL_MODEL_ID,
        "acceptance_id": S2PCT05_ACCEPTANCE_ID,
        "task_id": S2PCT05_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "profile_gate": profile_gate,
        "engineering_signal_taxonomy_gate": taxonomy_gate,
        "officiality_gate": officiality_gate,
        "version_traceability_gate": version_gate,
        "paper_relation_gate": relation_gate,
        "reproducibility_state_gate": reproducibility_gate,
        "required_signal_types": list(S2PCT05_REQUIRED_SIGNAL_TYPES),
        "signal_types_observed": observed_signal_types,
        "engineering_signal_count": len(normalized_signals),
        "known_document_count": len(known_documents),
        "signal_reports": signal_reports,
        "engineering_signals": normalized_signals,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "blocking_reasons": blocking_reasons,
    }


def run_s2pct05_engineering_signal_shadow(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    profile_report: Mapping[str, Any],
    engineering_signals: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PCT05 metadata-only engineering signal evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct05-engineering-signals-shadow"
    ledger_path = state / S2PCT05_LEDGER_FILENAME
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pct05_engineering_signal_report(
        generated_at=generated_at,
        profile_report=profile_report,
        engineering_signals=engineering_signals,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "engineering_signal_report_path": str(run_dir / "adp-s2pct05-engineering-signal-report.json"),
            "engineering_signal_ledger_path": str(ledger_path),
            "engineering_signal_ledger_row_count": len(report.get("engineering_signals") or []),
        }
    )
    if write:
        for row in report.get("engineering_signals") or []:
            if isinstance(row, Mapping):
                _append_jsonl(ledger_path, row)
    return _write_or_return_s2pct05(report, run_dir, write=write)


def validate_s2pct05_engineering_signal_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT05_ENGINEERING_SIGNAL_MODEL_ID:
        errors.append("S2PCT05 engineering signal report model_id must be adp-s2pct05-engineering-signals-v1")
    if report.get("task_id") != S2PCT05_TASK_ID:
        errors.append("S2PCT05 engineering signal report task_id must be S2PCT05")
    if report.get("acceptance_id") != S2PCT05_ACCEPTANCE_ID:
        errors.append("S2PCT05 engineering signal report acceptance_id must be ACC-S2PCT05-ENGINEERING-SIGNALS")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT05 engineering signal report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT05 engineering signal shadow")
    signals = report.get("engineering_signals")
    if not isinstance(signals, list):
        errors.append("S2PCT05 engineering_signals must be a list")
        signals = []
    observed = set(report.get("signal_types_observed") or [])
    missing = [signal_type for signal_type in S2PCT05_REQUIRED_SIGNAL_TYPES if signal_type not in observed]
    if missing:
        errors.append("S2PCT05 signal taxonomy missing required types: " + ", ".join(missing))
    signal_ids: set[str] = set()
    for index, signal in enumerate(signals):
        if not isinstance(signal, Mapping):
            errors.append(f"engineering_signals[{index}] must be an object")
            continue
        signal_id = str(signal.get("signal_id") or "")
        if not signal_id:
            errors.append(f"engineering_signals[{index}].signal_id is required")
        if signal_id in signal_ids:
            errors.append(f"duplicate S2PCT05 signal_id: {signal_id}")
        signal_ids.add(signal_id)
        if signal.get("signal_type") not in S2PCT05_REQUIRED_SIGNAL_TYPES:
            errors.append(f"engineering_signals[{index}].signal_type is not supported")
        if signal.get("metadata_only") is not True:
            errors.append(f"engineering_signals[{index}].metadata_only must be true")
        if signal.get("officiality_state") not in S2PCT05_ALLOWED_OFFICIALITY_STATES:
            errors.append(f"engineering_signals[{index}].officiality_state is not accepted")
        if signal.get("paper_relation_type") not in S2PCT05_ALLOWED_RELATION_TYPES:
            errors.append(f"engineering_signals[{index}].paper_relation_type is not supported")
        if not signal.get("canonical_document_id"):
            errors.append(f"engineering_signals[{index}].canonical_document_id is required")
        if not signal.get("version_reference"):
            errors.append(f"engineering_signals[{index}].version_reference is required")
        if signal.get("reproducibility_state") not in S2PCT05_ALLOWED_REPRODUCIBILITY_STATES:
            errors.append(f"engineering_signals[{index}].reproducibility_state is invalid")
        if not signal.get("evidence_refs"):
            errors.append(f"engineering_signals[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT05 engineering signal report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "profile_gate",
            "engineering_signal_taxonomy_gate",
            "officiality_gate",
            "version_traceability_gate",
            "paper_relation_gate",
            "reproducibility_state_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PCT05 engineering signal report requires {key}=pass")
    return errors


def build_s2pct06_authoritative_report_source_report(
    *,
    generated_at: str,
    engineering_signal_report: Mapping[str, Any],
    technical_reports: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build metadata-only authoritative technical report evidence after S2PCT05."""

    engineering_errors = validate_s2pct05_engineering_signal_report(engineering_signal_report)
    engineering_gate = "pass" if not engineering_errors and engineering_signal_report.get("status") == "pass" else "blocked"
    known_signals = _s2pct06_known_signals(engineering_signal_report)
    known_documents = {
        str(signal.get("canonical_document_id") or "")
        for signal in known_signals.values()
        if signal.get("canonical_document_id")
    }
    normalized_reports, source_reports, report_errors = _s2pct06_normalize_reports(
        technical_reports,
        known_signals=known_signals,
        known_documents=known_documents,
        generated_at=generated_at,
    )
    observed_report_types = sorted(
        {str(report.get("report_type") or "") for report in normalized_reports if report.get("report_type")}
    )
    missing_report_types = [
        report_type for report_type in S2PCT06_REQUIRED_REPORT_TYPES if report_type not in observed_report_types
    ]
    duplicate_report_ids = _duplicate_values(str(report.get("report_id") or "") for report in normalized_reports)
    publisher_identity_errors = _s2pct06_publisher_identity_errors(normalized_reports) + [
        reason
        for reason in report_errors
        if "publisher_identity" in reason or "publisher_type" in reason or "publisher" in reason
    ]
    interest_errors = _s2pct06_interest_relation_errors(normalized_reports) + [
        reason for reason in report_errors if "interest_relation" in reason or "interest_disclosure" in reason
    ]
    evidence_errors = _s2pct06_evidence_level_errors(normalized_reports) + [
        reason for reason in report_errors if "evidence_level" in reason
    ]
    traceability_errors = _s2pct06_traceability_errors(normalized_reports, known_signals, known_documents) + [
        reason
        for reason in report_errors
        if "related_signal_ids" in reason or "canonical_document_id" in reason
    ]
    publisher_identity_gate = "pass" if not publisher_identity_errors else "blocked"
    interest_relation_gate = "pass" if not interest_errors else "blocked"
    evidence_level_gate = "pass" if not evidence_errors else "blocked"
    traceability_gate = "pass" if not traceability_errors else "blocked"
    blocking_reasons = list(engineering_errors) + report_errors
    if engineering_gate != "pass":
        blocking_reasons.append("S2PCT05 engineering signal report must pass before S2PCT06 authoritative reports")
    if missing_report_types:
        blocking_reasons.append("missing required authoritative report types: " + ", ".join(missing_report_types))
    if duplicate_report_ids:
        blocking_reasons.append("duplicate authoritative report ids: " + ", ".join(duplicate_report_ids))
    for gate_errors in (publisher_identity_errors, interest_errors, evidence_errors, traceability_errors):
        for reason in gate_errors:
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)
    report_taxonomy_gate = "pass" if not missing_report_types and not duplicate_report_ids else "blocked"
    status = (
        "pass"
        if not blocking_reasons
        and engineering_gate
        == report_taxonomy_gate
        == publisher_identity_gate
        == interest_relation_gate
        == evidence_level_gate
        == traceability_gate
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID,
        "acceptance_id": S2PCT06_ACCEPTANCE_ID,
        "task_id": S2PCT06_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "engineering_signal_gate": engineering_gate,
        "report_taxonomy_gate": report_taxonomy_gate,
        "publisher_identity_gate": publisher_identity_gate,
        "interest_relation_gate": interest_relation_gate,
        "evidence_level_gate": evidence_level_gate,
        "traceability_gate": traceability_gate,
        "required_report_types": list(S2PCT06_REQUIRED_REPORT_TYPES),
        "report_types_observed": observed_report_types,
        "authoritative_report_count": len(normalized_reports),
        "known_signal_count": len(known_signals),
        "known_document_count": len(known_documents),
        "source_reports": source_reports,
        "authoritative_reports": normalized_reports,
        "formal_production_inclusion": False,
        "d2_source_domain_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "marketing_material_accepted": False,
        "blocking_reasons": blocking_reasons,
    }


def run_s2pct06_authoritative_report_shadow(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    engineering_signal_report: Mapping[str, Any],
    technical_reports: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PCT06 metadata-only authoritative report source evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct06-authoritative-reports-shadow"
    ledger_path = state / S2PCT06_LEDGER_FILENAME
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pct06_authoritative_report_source_report(
        generated_at=generated_at,
        engineering_signal_report=engineering_signal_report,
        technical_reports=technical_reports,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "authoritative_report_path": str(run_dir / "adp-s2pct06-authoritative-report-source-report.json"),
            "authoritative_report_ledger_path": str(ledger_path),
            "authoritative_report_ledger_row_count": len(report.get("authoritative_reports") or []),
        }
    )
    if write:
        for row in report.get("authoritative_reports") or []:
            if isinstance(row, Mapping):
                _append_jsonl(ledger_path, row)
    return _write_or_return_s2pct06(report, run_dir, write=write)


def validate_s2pct06_authoritative_report_source_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT06_AUTHORITATIVE_REPORT_MODEL_ID:
        errors.append("S2PCT06 authoritative report model_id must be adp-s2pct06-authoritative-reports-v1")
    if report.get("task_id") != S2PCT06_TASK_ID:
        errors.append("S2PCT06 authoritative report task_id must be S2PCT06")
    if report.get("acceptance_id") != S2PCT06_ACCEPTANCE_ID:
        errors.append("S2PCT06 authoritative report acceptance_id must be ACC-S2PCT06-REPORTS")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT06 authoritative report status must be pass or blocked")
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "marketing_material_accepted",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT06 authoritative report shadow")
    reports = report.get("authoritative_reports")
    if not isinstance(reports, list):
        errors.append("S2PCT06 authoritative_reports must be a list")
        reports = []
    observed = set(report.get("report_types_observed") or [])
    missing = [report_type for report_type in S2PCT06_REQUIRED_REPORT_TYPES if report_type not in observed]
    if missing:
        errors.append("S2PCT06 report taxonomy missing required types: " + ", ".join(missing))
    report_ids: set[str] = set()
    for index, item in enumerate(reports):
        if not isinstance(item, Mapping):
            errors.append(f"authoritative_reports[{index}] must be an object")
            continue
        report_id = str(item.get("report_id") or "")
        if not report_id:
            errors.append(f"authoritative_reports[{index}].report_id is required")
        if report_id in report_ids:
            errors.append(f"duplicate S2PCT06 report_id: {report_id}")
        report_ids.add(report_id)
        if item.get("report_type") not in S2PCT06_REQUIRED_REPORT_TYPES:
            errors.append(f"authoritative_reports[{index}].report_type is not supported")
        if item.get("publisher_type") not in S2PCT06_ALLOWED_PUBLISHER_TYPES:
            errors.append(f"authoritative_reports[{index}].publisher_type is not supported")
        if item.get("publisher_identity_state") not in S2PCT06_ALLOWED_IDENTITY_STATES:
            errors.append(f"authoritative_reports[{index}].publisher_identity_state is not accepted")
        if item.get("interest_relation") not in S2PCT06_ALLOWED_INTEREST_RELATIONS:
            errors.append(f"authoritative_reports[{index}].interest_relation is not accepted")
        if item.get("evidence_level") not in S2PCT06_ALLOWED_EVIDENCE_LEVELS:
            errors.append(f"authoritative_reports[{index}].evidence_level is not accepted")
        if item.get("metadata_only") is not True:
            errors.append(f"authoritative_reports[{index}].metadata_only must be true")
        if item.get("marketing_material_accepted") is not False:
            errors.append(f"authoritative_reports[{index}].marketing_material_accepted must be false")
        if not item.get("source_url"):
            errors.append(f"authoritative_reports[{index}].source_url is required")
        if not item.get("version_reference"):
            errors.append(f"authoritative_reports[{index}].version_reference is required")
        if not item.get("publisher_identity_evidence"):
            errors.append(f"authoritative_reports[{index}].publisher_identity_evidence is required")
        if not item.get("interest_disclosure"):
            errors.append(f"authoritative_reports[{index}].interest_disclosure is required")
        if not item.get("canonical_document_id"):
            errors.append(f"authoritative_reports[{index}].canonical_document_id is required")
        if not item.get("related_signal_ids"):
            errors.append(f"authoritative_reports[{index}].related_signal_ids is required")
        if not item.get("evidence_refs"):
            errors.append(f"authoritative_reports[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT06 authoritative report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "engineering_signal_gate",
            "report_taxonomy_gate",
            "publisher_identity_gate",
            "interest_relation_gate",
            "evidence_level_gate",
            "traceability_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PCT06 authoritative report requires {key}=pass")
    return errors


def build_s2pct07_d2_source_domain_qualification_report(
    *,
    generated_at: str,
    profile_report: Mapping[str, Any],
    engineering_signal_report: Mapping[str, Any],
    authoritative_report: Mapping[str, Any],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    forced_event_records: Sequence[Mapping[str, Any]],
    queue_explanation_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Calibrate D2 source-domain readiness without granting production acceptance."""

    profile_errors = validate_s2pct04_top_journal_profile_report(profile_report)
    engineering_errors = validate_s2pct05_engineering_signal_report(engineering_signal_report)
    report_errors = validate_s2pct06_authoritative_report_source_report(authoritative_report)
    upstream_gate = (
        "pass"
        if not profile_errors
        and not engineering_errors
        and not report_errors
        and profile_report.get("status") == engineering_signal_report.get("status") == authoritative_report.get("status") == "pass"
        else "blocked"
    )
    domain_matrix, domain_errors = _s2pct07_domain_matrix(
        profile_report=profile_report,
        engineering_signal_report=engineering_signal_report,
        authoritative_report=authoritative_report,
    )
    replay_gate = _s2pct07_replay_gate(replay_records)
    shadow_gate = _s2pct07_shadow_gate(shadow_records)
    forced_event_gate = _s2pct07_forced_event_gate(forced_event_records)
    queue_explanation_gate = _s2pct07_queue_explanation_gate(queue_explanation_records)
    type_calibration = _s2pct07_type_calibration(domain_matrix)
    blocking_reasons = [
        *profile_errors,
        *engineering_errors,
        *report_errors,
        *domain_errors,
        *replay_gate["blocking_reasons"],
        *shadow_gate["blocking_reasons"],
        *forced_event_gate["blocking_reasons"],
        *queue_explanation_gate["blocking_reasons"],
        *type_calibration["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PCT07 requires passing S2PCT04, S2PCT05, and S2PCT06 upstream reports")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == replay_gate["status"]
        == shadow_gate["status"]
        == forced_event_gate["status"]
        == queue_explanation_gate["status"]
        == type_calibration["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PCT07_D2_QUALIFICATION_MODEL_ID,
        "acceptance_id": S2PCT07_ACCEPTANCE_ID,
        "task_id": S2PCT07_TASK_ID,
        "phase": "S2PC",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_gate": upstream_gate,
        "domain_coverage_gate": "pass" if not domain_errors else "blocked",
        "replay_gate": replay_gate["status"],
        "shadow_gate": shadow_gate["status"],
        "forced_event_gate": forced_event_gate["status"],
        "queue_explanation_gate": queue_explanation_gate["status"],
        "type_calibration_gate": type_calibration["status"],
        "required_domains": list(S2PCT07_REQUIRED_DOMAINS),
        "domain_coverage_matrix": domain_matrix,
        "type_calibration": type_calibration,
        "replay_summary": replay_gate,
        "shadow_summary": shadow_gate,
        "forced_event_summary": forced_event_gate,
        "queue_explanation_summary": queue_explanation_gate,
        "d2_source_domain_qualification_ready": status == "pass",
        "d2_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "marketing_material_accepted": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pct07_d2_source_domain_qualification(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    profile_report: Mapping[str, Any],
    engineering_signal_report: Mapping[str, Any],
    authoritative_report: Mapping[str, Any],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    forced_event_records: Sequence[Mapping[str, Any]],
    queue_explanation_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PCT07 D2 qualification evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pct07-d2-source-domain-qualification"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pct07_d2_source_domain_qualification_report(
        generated_at=generated_at,
        profile_report=profile_report,
        engineering_signal_report=engineering_signal_report,
        authoritative_report=authoritative_report,
        replay_records=replay_records,
        shadow_records=shadow_records,
        forced_event_records=forced_event_records,
        queue_explanation_records=queue_explanation_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "qualification_report_path": str(run_dir / "adp-s2pct07-d2-source-domain-qualification-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pct07-d2-source-domain-qualification-report.json", report)
        _write_json(state / S2PCT07_QUALIFICATION_REPORT_FILENAME, report)
    return report


def validate_s2pct07_d2_source_domain_qualification_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PCT07_D2_QUALIFICATION_MODEL_ID:
        errors.append("S2PCT07 qualification model_id must be adp-s2pct07-d2-source-domain-qualification-v1")
    if report.get("task_id") != S2PCT07_TASK_ID:
        errors.append("S2PCT07 qualification task_id must be S2PCT07")
    if report.get("acceptance_id") != S2PCT07_ACCEPTANCE_ID:
        errors.append("S2PCT07 qualification acceptance_id must be ACC-S2PCT07-D2")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PCT07 qualification status must be pass or blocked")
    for key in (
        "d2_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "marketing_material_accepted",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PCT07 qualification evidence")
    matrix = report.get("domain_coverage_matrix")
    if not isinstance(matrix, Mapping):
        errors.append("S2PCT07 domain_coverage_matrix must be an object")
        matrix = {}
    missing_domains = [domain for domain in S2PCT07_REQUIRED_DOMAINS if domain not in matrix]
    if missing_domains:
        errors.append("S2PCT07 domain coverage missing required domains: " + ", ".join(missing_domains))
    for domain in S2PCT07_REQUIRED_DOMAINS:
        row = matrix.get(domain)
        if not isinstance(row, Mapping):
            errors.append(f"S2PCT07 domain_coverage_matrix.{domain} must be an object")
            continue
        if row.get("coverage_gate") != "pass":
            errors.append(f"S2PCT07 domain_coverage_matrix.{domain}.coverage_gate must pass")
        if int(row.get("evidence_count") or 0) < 1:
            errors.append(f"S2PCT07 domain_coverage_matrix.{domain}.evidence_count must be positive")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PCT07 qualification report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_gate",
            "domain_coverage_gate",
            "replay_gate",
            "shadow_gate",
            "forced_event_gate",
            "queue_explanation_gate",
            "type_calibration_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PCT07 qualification requires {key}=pass")
        if report.get("d2_source_domain_qualification_ready") is not True:
            errors.append("passing S2PCT07 qualification requires d2_source_domain_qualification_ready=true")
    return errors


def build_s2pdt01_china_c0_source_foundation_report(
    *,
    generated_at: str,
    d2_qualification_report: Mapping[str, Any],
    authority_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build C0 China official source foundation evidence without production inclusion."""

    d2_errors = validate_s2pct07_d2_source_domain_qualification_report(d2_qualification_report)
    d2_gate = (
        "pass"
        if not d2_errors
        and d2_qualification_report.get("status") == "pass"
        and d2_qualification_report.get("d2_source_domain_qualification_ready") is True
        else "blocked"
    )
    authority_rows, authority_errors = _s2pdt01_authority_rows(authority_records)
    taxonomy_gate = _s2pdt01_taxonomy_gate(authority_rows)
    identity_gate = _s2pdt01_identity_gate(authority_rows)
    traceability_gate = _s2pdt01_traceability_gate(authority_rows)
    metadata_gate = _s2pdt01_metadata_gate(authority_rows)
    blocking_reasons = [
        *d2_errors,
        *authority_errors,
        *taxonomy_gate["blocking_reasons"],
        *identity_gate["blocking_reasons"],
        *traceability_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if d2_gate != "pass":
        blocking_reasons.append("S2PDT01 requires passing S2PCT07 D2 qualification readiness")
    status = (
        "pass"
        if not blocking_reasons
        and d2_gate
        == taxonomy_gate["status"]
        == identity_gate["status"]
        == traceability_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PDT01_CHINA_C0_SOURCE_MODEL_ID,
        "acceptance_id": S2PDT01_ACCEPTANCE_ID,
        "task_id": S2PDT01_TASK_ID,
        "legacy_task_id": S2PDT01_LEGACY_TASK_ID,
        "phase": "S2PD",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_d2_qualification_gate": d2_gate,
        "authority_taxonomy_gate": taxonomy_gate["status"],
        "official_identity_gate": identity_gate["status"],
        "document_traceability_gate": traceability_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_authority_types": list(S2PDT01_REQUIRED_AUTHORITY_TYPES),
        "authority_types_observed": taxonomy_gate["authority_types_observed"],
        "required_trace_fields": list(S2PDT01_REQUIRED_TRACE_FIELDS),
        "authority_records": authority_rows,
        "authority_record_count": len(authority_rows),
        "taxonomy_summary": taxonomy_gate,
        "identity_summary": identity_gate,
        "traceability_summary": traceability_gate,
        "metadata_summary": metadata_gate,
        "d3_c0_source_foundation_ready": status == "pass",
        "d3_core_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pdt01_china_c0_source_foundation(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    d2_qualification_report: Mapping[str, Any],
    authority_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PDT01 China C0 source foundation evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pdt01-china-c0-source-foundation"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pdt01_china_c0_source_foundation_report(
        generated_at=generated_at,
        d2_qualification_report=d2_qualification_report,
        authority_records=authority_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "source_foundation_report_path": str(run_dir / "adp-s2pdt01-china-c0-source-foundation-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pdt01-china-c0-source-foundation-report.json", report)
        _write_json(state / S2PDT01_REPORT_FILENAME, report)
    return report


def validate_s2pdt01_china_c0_source_foundation_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PDT01_CHINA_C0_SOURCE_MODEL_ID:
        errors.append("S2PDT01 C0 model_id must be adp-s2pdt01-china-c0-source-foundation-v1")
    if report.get("task_id") != S2PDT01_TASK_ID:
        errors.append("S2PDT01 C0 task_id must be S2PDT01")
    if report.get("legacy_task_id") != S2PDT01_LEGACY_TASK_ID:
        errors.append("S2PDT01 C0 legacy_task_id must be S2P3T01")
    if report.get("acceptance_id") != S2PDT01_ACCEPTANCE_ID:
        errors.append("S2PDT01 C0 acceptance_id must be ACC-S2PDT01-C0")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PDT01 C0 status must be pass or blocked")
    for key in (
        "d3_core_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PDT01 C0 source foundation")
    records = report.get("authority_records")
    if not isinstance(records, list):
        errors.append("S2PDT01 authority_records must be a list")
        records = []
    observed = set(report.get("authority_types_observed") or [])
    missing = [authority_type for authority_type in S2PDT01_REQUIRED_AUTHORITY_TYPES if authority_type not in observed]
    if missing:
        errors.append("S2PDT01 C0 taxonomy missing required authority types: " + ", ".join(missing))
    source_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"authority_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "")
        if not source_id:
            errors.append(f"authority_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PDT01 source_id: {source_id}")
        source_ids.add(source_id)
        if record.get("authority_type") not in S2PDT01_REQUIRED_AUTHORITY_TYPES:
            errors.append(f"authority_records[{index}].authority_type is not supported")
        if record.get("identity_state") not in S2PDT01_ALLOWED_IDENTITY_STATES:
            errors.append(f"authority_records[{index}].identity_state is not accepted")
        if record.get("metadata_only") is not True:
            errors.append(f"authority_records[{index}].metadata_only must be true")
        if record.get("pdf_downloaded") is not False:
            errors.append(f"authority_records[{index}].pdf_downloaded must be false")
        if record.get("full_text_extracted") is not False:
            errors.append(f"authority_records[{index}].full_text_extracted must be false")
        for field in S2PDT01_REQUIRED_TRACE_FIELDS:
            if not record.get(field):
                errors.append(f"authority_records[{index}].{field} is required")
        if not record.get("source_url"):
            errors.append(f"authority_records[{index}].source_url is required")
        if not record.get("attachment_trace"):
            errors.append(f"authority_records[{index}].attachment_trace is required")
        if not record.get("evidence_refs"):
            errors.append(f"authority_records[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PDT01 C0 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_d2_qualification_gate",
            "authority_taxonomy_gate",
            "official_identity_gate",
            "document_traceability_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PDT01 C0 report requires {key}=pass")
        if report.get("d3_c0_source_foundation_ready") is not True:
            errors.append("passing S2PDT01 C0 report requires d3_c0_source_foundation_ready=true")
    return errors


def build_s2pdt02_china_c1_department_source_map_report(
    *,
    generated_at: str,
    c0_source_foundation_report: Mapping[str, Any],
    department_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build China C1 central department source-map evidence without production inclusion."""

    c0_errors = validate_s2pdt01_china_c0_source_foundation_report(c0_source_foundation_report)
    c0_gate = (
        "pass"
        if not c0_errors
        and c0_source_foundation_report.get("status") == "pass"
        and c0_source_foundation_report.get("d3_c0_source_foundation_ready") is True
        else "blocked"
    )
    department_rows, department_errors = _s2pdt02_department_rows(department_records)
    sector_gate = _s2pdt02_sector_gate(department_rows)
    identity_gate = _s2pdt02_identity_gate(department_rows)
    alias_gate = _s2pdt02_alias_gate(department_rows)
    route_gate = _s2pdt02_route_gate(department_rows)
    metadata_gate = _s2pdt02_metadata_gate(department_rows)
    blocking_reasons = [
        *c0_errors,
        *department_errors,
        *sector_gate["blocking_reasons"],
        *identity_gate["blocking_reasons"],
        *alias_gate["blocking_reasons"],
        *route_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if c0_gate != "pass":
        blocking_reasons.append("S2PDT02 requires passing S2PDT01 China C0 source foundation")
    status = (
        "pass"
        if not blocking_reasons
        and c0_gate
        == sector_gate["status"]
        == identity_gate["status"]
        == alias_gate["status"]
        == route_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PDT02_CHINA_C1_SOURCE_MODEL_ID,
        "acceptance_id": S2PDT02_ACCEPTANCE_ID,
        "task_id": S2PDT02_TASK_ID,
        "legacy_task_id": S2PDT02_LEGACY_TASK_ID,
        "phase": "S2PD",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_c0_source_foundation_gate": c0_gate,
        "sector_coverage_gate": sector_gate["status"],
        "official_identity_gate": identity_gate["status"],
        "alias_gate": alias_gate["status"],
        "industry_route_gate": route_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_sectors": list(S2PDT02_REQUIRED_SECTORS),
        "sectors_observed": sector_gate["sectors_observed"],
        "required_route_fields": list(S2PDT02_REQUIRED_ROUTE_FIELDS),
        "department_records": department_rows,
        "department_record_count": len(department_rows),
        "sector_summary": sector_gate,
        "identity_summary": identity_gate,
        "alias_summary": alias_gate,
        "route_summary": route_gate,
        "metadata_summary": metadata_gate,
        "d3_c1_department_source_map_ready": status == "pass",
        "d3_core_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pdt02_china_c1_department_source_map(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    c0_source_foundation_report: Mapping[str, Any],
    department_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PDT02 China C1 department source-map evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pdt02-china-c1-department-source-map"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pdt02_china_c1_department_source_map_report(
        generated_at=generated_at,
        c0_source_foundation_report=c0_source_foundation_report,
        department_records=department_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "department_source_map_report_path": str(run_dir / "adp-s2pdt02-china-c1-department-source-map-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pdt02-china-c1-department-source-map-report.json", report)
        _write_json(state / S2PDT02_REPORT_FILENAME, report)
    return report


def validate_s2pdt02_china_c1_department_source_map_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PDT02_CHINA_C1_SOURCE_MODEL_ID:
        errors.append("S2PDT02 C1 model_id must be adp-s2pdt02-china-c1-department-source-map-v1")
    if report.get("task_id") != S2PDT02_TASK_ID:
        errors.append("S2PDT02 C1 task_id must be S2PDT02")
    if report.get("legacy_task_id") != S2PDT02_LEGACY_TASK_ID:
        errors.append("S2PDT02 C1 legacy_task_id must be S2P3T02")
    if report.get("acceptance_id") != S2PDT02_ACCEPTANCE_ID:
        errors.append("S2PDT02 C1 acceptance_id must be ACC-S2PDT02-C1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PDT02 C1 status must be pass or blocked")
    for key in (
        "d3_core_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PDT02 C1 department source map")
    records = report.get("department_records")
    if not isinstance(records, list):
        errors.append("S2PDT02 department_records must be a list")
        records = []
    observed = set(report.get("sectors_observed") or [])
    missing = [sector for sector in S2PDT02_REQUIRED_SECTORS if sector not in observed]
    if missing:
        errors.append("S2PDT02 C1 sector coverage missing required sectors: " + ", ".join(missing))
    source_ids: set[str] = set()
    department_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"department_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "")
        department_id = str(record.get("department_id") or "")
        if not source_id:
            errors.append(f"department_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PDT02 source_id: {source_id}")
        source_ids.add(source_id)
        if not department_id:
            errors.append(f"department_records[{index}].department_id is required")
        if department_id in department_ids:
            errors.append(f"duplicate S2PDT02 department_id: {department_id}")
        department_ids.add(department_id)
        if record.get("sector") not in S2PDT02_REQUIRED_SECTORS:
            errors.append(f"department_records[{index}].sector is not supported")
        if record.get("identity_state") not in S2PDT02_ALLOWED_IDENTITY_STATES:
            errors.append(f"department_records[{index}].identity_state is not accepted")
        if record.get("metadata_only") is not True:
            errors.append(f"department_records[{index}].metadata_only must be true")
        if record.get("pdf_downloaded") is not False:
            errors.append(f"department_records[{index}].pdf_downloaded must be false")
        if record.get("full_text_extracted") is not False:
            errors.append(f"department_records[{index}].full_text_extracted must be false")
        for field in ("department_name", "official_domain", "source_url"):
            if not record.get(field):
                errors.append(f"department_records[{index}].{field} is required")
        for field in ("aliases", "industry_routes", "evidence_refs"):
            if not record.get(field):
                errors.append(f"department_records[{index}].{field} is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PDT02 C1 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_c0_source_foundation_gate",
            "sector_coverage_gate",
            "official_identity_gate",
            "alias_gate",
            "industry_route_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PDT02 C1 report requires {key}=pass")
        if report.get("d3_c1_department_source_map_ready") is not True:
            errors.append("passing S2PDT02 C1 report requires d3_c1_department_source_map_ready=true")
    return errors


def build_s2pdt03_china_legal_metadata_relation_shadow_report(
    *,
    generated_at: str,
    c1_department_source_map_report: Mapping[str, Any],
    legal_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
    prior_conclusion_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build China legal status/version/reprint relation evidence without production inclusion."""

    c1_errors = validate_s2pdt02_china_c1_department_source_map_report(c1_department_source_map_report)
    c1_gate = (
        "pass"
        if not c1_errors
        and c1_department_source_map_report.get("status") == "pass"
        and c1_department_source_map_report.get("d3_c1_department_source_map_ready") is True
        else "blocked"
    )
    legal_rows, legal_errors = _s2pdt03_legal_rows(legal_records)
    relation_rows, relation_errors = _s2pdt03_relation_rows(relation_records, legal_rows)
    prior_rows, prior_errors = _s2pdt03_prior_conclusion_rows(prior_conclusion_records, legal_rows)
    status_gate = _s2pdt03_legal_status_gate(legal_rows)
    effectivity_gate = _s2pdt03_version_effectivity_gate(legal_rows, relation_rows)
    reprint_gate = _s2pdt03_reprint_relation_gate(relation_rows)
    forced_update_gate = _s2pdt03_forced_update_gate(relation_rows, prior_rows)
    metadata_gate = _s2pdt03_metadata_gate(legal_rows, relation_rows)
    blocking_reasons = [
        *c1_errors,
        *legal_errors,
        *relation_errors,
        *prior_errors,
        *status_gate["blocking_reasons"],
        *effectivity_gate["blocking_reasons"],
        *reprint_gate["blocking_reasons"],
        *forced_update_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if c1_gate != "pass":
        blocking_reasons.append("S2PDT03 requires passing S2PDT02 China C1 department source map")
    status = (
        "pass"
        if not blocking_reasons
        and c1_gate
        == status_gate["status"]
        == effectivity_gate["status"]
        == reprint_gate["status"]
        == forced_update_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PDT03_LEGAL_METADATA_MODEL_ID,
        "acceptance_id": S2PDT03_ACCEPTANCE_ID,
        "task_id": S2PDT03_TASK_ID,
        "legacy_task_id": S2PDT03_LEGACY_TASK_ID,
        "phase": "S2PD",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_c1_department_source_map_gate": c1_gate,
        "legal_status_taxonomy_gate": status_gate["status"],
        "version_effectivity_gate": effectivity_gate["status"],
        "reprint_relation_gate": reprint_gate["status"],
        "forced_update_gate": forced_update_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_legal_statuses": list(S2PDT03_REQUIRED_LEGAL_STATUSES),
        "legal_statuses_observed": status_gate["legal_statuses_observed"],
        "required_relation_types": list(S2PDT03_REQUIRED_RELATION_TYPES),
        "relation_types_observed": effectivity_gate["relation_types_observed"],
        "required_date_fields": list(S2PDT03_REQUIRED_DATE_FIELDS),
        "required_forced_update_fields": list(S2PDT03_REQUIRED_FORCED_UPDATE_FIELDS),
        "legal_records": legal_rows,
        "relation_records": relation_rows,
        "prior_conclusion_records": prior_rows,
        "legal_record_count": len(legal_rows),
        "relation_record_count": len(relation_rows),
        "prior_conclusion_record_count": len(prior_rows),
        "legal_status_summary": status_gate,
        "version_effectivity_summary": effectivity_gate,
        "reprint_relation_summary": reprint_gate,
        "forced_update_summary": forced_update_gate,
        "metadata_summary": metadata_gate,
        "d3_legal_metadata_relation_shadow_ready": status == "pass",
        "legal_advice_provided": False,
        "v7_1_current_switched": False,
        "v7_2_mail_or_schema_prerun": False,
        "d3_core_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pdt03_china_legal_metadata_relation_shadow(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    c1_department_source_map_report: Mapping[str, Any],
    legal_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
    prior_conclusion_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PDT03 legal metadata relation evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pdt03-china-legal-metadata-relation-shadow"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pdt03_china_legal_metadata_relation_shadow_report(
        generated_at=generated_at,
        c1_department_source_map_report=c1_department_source_map_report,
        legal_records=legal_records,
        relation_records=relation_records,
        prior_conclusion_records=prior_conclusion_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "legal_metadata_relation_report_path": str(run_dir / "adp-s2pdt03-china-legal-metadata-relation-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pdt03-china-legal-metadata-relation-report.json", report)
        _write_json(state / S2PDT03_REPORT_FILENAME, report)
    return report


def validate_s2pdt03_china_legal_metadata_relation_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PDT03_LEGAL_METADATA_MODEL_ID:
        errors.append("S2PDT03 legal model_id must be adp-s2pdt03-china-legal-metadata-relation-shadow-v1")
    if report.get("task_id") != S2PDT03_TASK_ID:
        errors.append("S2PDT03 legal task_id must be S2PDT03")
    if report.get("legacy_task_id") != S2PDT03_LEGACY_TASK_ID:
        errors.append("S2PDT03 legal legacy_task_id must be S2P3T03")
    if report.get("acceptance_id") != S2PDT03_ACCEPTANCE_ID:
        errors.append("S2PDT03 legal acceptance_id must be ACC-S2PDT03-LEGAL")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PDT03 legal status must be pass or blocked")
    for key in (
        "legal_advice_provided",
        "v7_1_current_switched",
        "v7_2_mail_or_schema_prerun",
        "d3_core_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PDT03 legal metadata relation shadow")
    records = report.get("legal_records")
    if not isinstance(records, list):
        errors.append("S2PDT03 legal_records must be a list")
        records = []
    relations = report.get("relation_records")
    if not isinstance(relations, list):
        errors.append("S2PDT03 relation_records must be a list")
        relations = []
    prior_records = report.get("prior_conclusion_records")
    if not isinstance(prior_records, list):
        errors.append("S2PDT03 prior_conclusion_records must be a list")
        prior_records = []
    legal_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"legal_records[{index}] must be an object")
            continue
        legal_id = str(record.get("legal_id") or "")
        if not legal_id:
            errors.append(f"legal_records[{index}].legal_id is required")
        if legal_id in legal_ids:
            errors.append(f"duplicate S2PDT03 legal_id: {legal_id}")
        legal_ids.add(legal_id)
        if record.get("legal_status") not in S2PDT03_REQUIRED_LEGAL_STATUSES:
            errors.append(f"legal_records[{index}].legal_status is not supported")
        if record.get("identity_state") not in S2PDT03_ALLOWED_IDENTITY_STATES:
            errors.append(f"legal_records[{index}].identity_state is not accepted")
        for field in ("source_id", "title", "official_domain", "source_url", *S2PDT03_REQUIRED_DATE_FIELDS):
            if not record.get(field):
                errors.append(f"legal_records[{index}].{field} is required")
        if record.get("metadata_only") is not True:
            errors.append(f"legal_records[{index}].metadata_only must be true")
        if record.get("pdf_downloaded") is not False:
            errors.append(f"legal_records[{index}].pdf_downloaded must be false")
        if record.get("full_text_extracted") is not False:
            errors.append(f"legal_records[{index}].full_text_extracted must be false")
        if not record.get("evidence_refs"):
            errors.append(f"legal_records[{index}].evidence_refs is required")
    relation_ids: set[str] = set()
    for index, relation in enumerate(relations):
        if not isinstance(relation, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_id = str(relation.get("relation_id") or "")
        if not relation_id:
            errors.append(f"relation_records[{index}].relation_id is required")
        if relation_id in relation_ids:
            errors.append(f"duplicate S2PDT03 relation_id: {relation_id}")
        relation_ids.add(relation_id)
        if relation.get("relation_type") not in S2PDT03_REQUIRED_RELATION_TYPES:
            errors.append(f"relation_records[{index}].relation_type is not supported")
        for field in ("source_legal_id", "target_legal_id", "relation_date"):
            if not relation.get(field):
                errors.append(f"relation_records[{index}].{field} is required")
        if relation.get("metadata_only") is not True:
            errors.append(f"relation_records[{index}].metadata_only must be true")
        if not relation.get("evidence_refs"):
            errors.append(f"relation_records[{index}].evidence_refs is required")
    observed_statuses = set(report.get("legal_statuses_observed") or [])
    missing_statuses = [status for status in S2PDT03_REQUIRED_LEGAL_STATUSES if status not in observed_statuses]
    if missing_statuses:
        errors.append("S2PDT03 legal status coverage missing required statuses: " + ", ".join(missing_statuses))
    observed_relations = set(report.get("relation_types_observed") or [])
    missing_relations = [relation for relation in S2PDT03_REQUIRED_RELATION_TYPES if relation not in observed_relations]
    if missing_relations:
        errors.append("S2PDT03 legal relation coverage missing required relation types: " + ", ".join(missing_relations))
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PDT03 legal report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_c1_department_source_map_gate",
            "legal_status_taxonomy_gate",
            "version_effectivity_gate",
            "reprint_relation_gate",
            "forced_update_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PDT03 legal report requires {key}=pass")
        if report.get("d3_legal_metadata_relation_shadow_ready") is not True:
            errors.append("passing S2PDT03 legal report requires d3_legal_metadata_relation_shadow_ready=true")
    return errors


def build_s2pdt04_china_d3_readiness_review_report(
    *,
    generated_at: str,
    c0_source_foundation_report: Mapping[str, Any],
    c1_department_source_map_report: Mapping[str, Any],
    legal_metadata_relation_report: Mapping[str, Any],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    board_route_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build China D3 core replay/shadow/routing readiness without production inclusion."""

    c0_errors = validate_s2pdt01_china_c0_source_foundation_report(c0_source_foundation_report)
    c1_errors = validate_s2pdt02_china_c1_department_source_map_report(c1_department_source_map_report)
    legal_errors = validate_s2pdt03_china_legal_metadata_relation_shadow_report(legal_metadata_relation_report)
    c0_gate = (
        "pass"
        if not c0_errors
        and c0_source_foundation_report.get("status") == "pass"
        and c0_source_foundation_report.get("d3_c0_source_foundation_ready") is True
        else "blocked"
    )
    c1_gate = (
        "pass"
        if not c1_errors
        and c1_department_source_map_report.get("status") == "pass"
        and c1_department_source_map_report.get("d3_c1_department_source_map_ready") is True
        else "blocked"
    )
    legal_gate = (
        "pass"
        if not legal_errors
        and legal_metadata_relation_report.get("status") == "pass"
        and legal_metadata_relation_report.get("d3_legal_metadata_relation_shadow_ready") is True
        else "blocked"
    )
    replay_rows, replay_errors = _s2pdt04_replay_rows(replay_records)
    shadow_rows, shadow_errors = _s2pdt04_shadow_rows(shadow_records)
    route_rows, route_errors = _s2pdt04_board_route_rows(board_route_records)
    replay_gate = _s2pdt04_replay_gate(replay_rows)
    shadow_gate = _s2pdt04_shadow_gate(shadow_rows)
    authority_gate = _s2pdt04_authority_gate(replay_rows, shadow_rows, route_rows)
    route_gate = _s2pdt04_board_routing_gate(route_rows)
    metadata_gate = _s2pdt04_metadata_gate(replay_rows, shadow_rows, route_rows)
    upstream_gate = "pass" if c0_gate == c1_gate == legal_gate == "pass" else "blocked"
    blocking_reasons = [
        *c0_errors,
        *c1_errors,
        *legal_errors,
        *replay_errors,
        *shadow_errors,
        *route_errors,
        *replay_gate["blocking_reasons"],
        *shadow_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *route_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PDT04 requires passing S2PDT01 C0, S2PDT02 C1, and S2PDT03 legal metadata reports")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == replay_gate["status"]
        == shadow_gate["status"]
        == authority_gate["status"]
        == route_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PDT04_D3_READINESS_MODEL_ID,
        "acceptance_id": S2PDT04_ACCEPTANCE_ID,
        "task_id": S2PDT04_TASK_ID,
        "legacy_task_id": S2PDT04_LEGACY_TASK_ID,
        "phase": "S2PD",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_source_evidence_gate": upstream_gate,
        "upstream_c0_source_foundation_gate": c0_gate,
        "upstream_c1_department_source_map_gate": c1_gate,
        "upstream_legal_metadata_relation_gate": legal_gate,
        "d3_replay_gate": replay_gate["status"],
        "d3_shadow_gate": shadow_gate["status"],
        "authority_gate": authority_gate["status"],
        "board_routing_gate": route_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_replay_dates": S2PDT04_REQUIRED_REPLAY_DATES,
        "replay_dates_observed": replay_gate["replay_dates_observed"],
        "required_shadow_days": S2PDT04_REQUIRED_SHADOW_DAYS,
        "shadow_dates_observed": shadow_gate["shadow_dates_observed"],
        "required_board_ids": list(S2PDT04_REQUIRED_BOARD_IDS),
        "board_ids_observed": route_gate["board_ids_observed"],
        "required_route_fields": list(S2PDT04_REQUIRED_ROUTE_FIELDS),
        "replay_records": replay_rows,
        "shadow_records": shadow_rows,
        "board_route_records": route_rows,
        "replay_record_count": len(replay_rows),
        "shadow_record_count": len(shadow_rows),
        "board_route_record_count": len(route_rows),
        "replay_summary": replay_gate,
        "shadow_summary": shadow_gate,
        "authority_summary": authority_gate,
        "board_routing_summary": route_gate,
        "metadata_summary": metadata_gate,
        "d3_core_readiness_review_ready": status == "pass",
        "d3_core_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_mail_or_schema_prerun": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pdt04_china_d3_readiness_review(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    c0_source_foundation_report: Mapping[str, Any],
    c1_department_source_map_report: Mapping[str, Any],
    legal_metadata_relation_report: Mapping[str, Any],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    board_route_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PDT04 China D3 readiness review evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pdt04-china-d3-readiness-review"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pdt04_china_d3_readiness_review_report(
        generated_at=generated_at,
        c0_source_foundation_report=c0_source_foundation_report,
        c1_department_source_map_report=c1_department_source_map_report,
        legal_metadata_relation_report=legal_metadata_relation_report,
        replay_records=replay_records,
        shadow_records=shadow_records,
        board_route_records=board_route_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "d3_readiness_review_report_path": str(run_dir / "adp-s2pdt04-china-d3-readiness-review-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pdt04-china-d3-readiness-review-report.json", report)
        _write_json(state / S2PDT04_REPORT_FILENAME, report)
    return report


def validate_s2pdt04_china_d3_readiness_review_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PDT04_D3_READINESS_MODEL_ID:
        errors.append("S2PDT04 D3 readiness model_id must be adp-s2pdt04-china-d3-readiness-review-v1")
    if report.get("task_id") != S2PDT04_TASK_ID:
        errors.append("S2PDT04 D3 readiness task_id must be S2PDT04")
    if report.get("legacy_task_id") != S2PDT04_LEGACY_TASK_ID:
        errors.append("S2PDT04 D3 readiness legacy_task_id must be S2P3T04")
    if report.get("acceptance_id") != S2PDT04_ACCEPTANCE_ID:
        errors.append("S2PDT04 D3 readiness acceptance_id must be ACC-S2PDT04-D3-CORE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PDT04 D3 readiness status must be pass or blocked")
    for key in (
        "d3_core_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_mail_or_schema_prerun",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PDT04 D3 readiness review")
    replay_records = report.get("replay_records")
    if not isinstance(replay_records, list):
        errors.append("S2PDT04 replay_records must be a list")
        replay_records = []
    shadow_records = report.get("shadow_records")
    if not isinstance(shadow_records, list):
        errors.append("S2PDT04 shadow_records must be a list")
        shadow_records = []
    route_records = report.get("board_route_records")
    if not isinstance(route_records, list):
        errors.append("S2PDT04 board_route_records must be a list")
        route_records = []
    observed_dates = set(report.get("replay_dates_observed") or [])
    if len(observed_dates) < S2PDT04_REQUIRED_REPLAY_DATES:
        errors.append("S2PDT04 replay coverage requires at least 30 distinct dates")
    observed_shadow_dates = set(report.get("shadow_dates_observed") or [])
    if len(observed_shadow_dates) < S2PDT04_REQUIRED_SHADOW_DAYS:
        errors.append("S2PDT04 shadow coverage requires at least 2 distinct dates")
    observed_boards = set(report.get("board_ids_observed") or [])
    missing_boards = [board for board in S2PDT04_REQUIRED_BOARD_IDS if board not in observed_boards]
    if missing_boards:
        errors.append("S2PDT04 board routing missing required boards: " + ", ".join(missing_boards))
    for index, record in enumerate(replay_records):
        if not isinstance(record, Mapping):
            errors.append(f"replay_records[{index}] must be an object")
            continue
        if not _is_iso_date(str(record.get("as_of_date") or "")):
            errors.append(f"replay_records[{index}].as_of_date must be YYYY-MM-DD")
        if record.get("status") != "pass":
            errors.append(f"replay_records[{index}].status must be pass")
        for key in ("future_leakage_count", "p0_p1_blocker_count"):
            if int(record.get(key) or 0) != 0:
                errors.append(f"replay_records[{index}].{key} must be 0")
        for key in ("authority_gate", "board_route_gate"):
            if record.get(key) != "pass":
                errors.append(f"replay_records[{index}].{key} must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"replay_records[{index}].metadata_only must be true")
    for index, record in enumerate(shadow_records):
        if not isinstance(record, Mapping):
            errors.append(f"shadow_records[{index}] must be an object")
            continue
        if not _is_iso_date(str(record.get("shadow_date") or "")):
            errors.append(f"shadow_records[{index}].shadow_date must be YYYY-MM-DD")
        if record.get("status") != "pass":
            errors.append(f"shadow_records[{index}].status must be pass")
        if record.get("production_affected") is not False:
            errors.append(f"shadow_records[{index}].production_affected must be false")
        if record.get("real_smtp_sent") is not False:
            errors.append(f"shadow_records[{index}].real_smtp_sent must be false")
    for index, record in enumerate(route_records):
        if not isinstance(record, Mapping):
            errors.append(f"board_route_records[{index}] must be an object")
            continue
        for field in S2PDT04_REQUIRED_ROUTE_FIELDS:
            if field not in record:
                errors.append(f"board_route_records[{index}].{field} is required")
        if record.get("board_id") not in S2PDT04_REQUIRED_BOARD_IDS:
            errors.append(f"board_route_records[{index}].board_id is not supported")
        if not record.get("source_ids"):
            errors.append(f"board_route_records[{index}].source_ids is required")
        if not record.get("route_explanation"):
            errors.append(f"board_route_records[{index}].route_explanation is required")
        if record.get("authority_gate") != "pass":
            errors.append(f"board_route_records[{index}].authority_gate must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"board_route_records[{index}].metadata_only must be true")
        if record.get("production_affected") is not False:
            errors.append(f"board_route_records[{index}].production_affected must be false")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PDT04 D3 readiness report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_source_evidence_gate",
            "d3_replay_gate",
            "d3_shadow_gate",
            "authority_gate",
            "board_routing_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PDT04 D3 readiness report requires {key}=pass")
        if report.get("d3_core_readiness_review_ready") is not True:
            errors.append("passing S2PDT04 D3 readiness report requires d3_core_readiness_review_ready=true")
    return errors


def build_s2pet01_us_ta_source_foundation_report(
    *,
    generated_at: str,
    agency_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build US-TA official technology agency source foundation evidence without production inclusion."""

    agency_rows, row_errors = _s2pet01_agency_rows(agency_records)
    agency_gate = _s2pet01_agency_coverage_gate(agency_rows)
    signal_gate = _s2pet01_signal_type_gate(agency_rows)
    identity_gate = _s2pet01_identity_gate(agency_rows)
    traceability_gate = _s2pet01_traceability_gate(agency_rows)
    metadata_gate = _s2pet01_metadata_gate(agency_rows)
    blocking_reasons = [
        *row_errors,
        *agency_gate["blocking_reasons"],
        *signal_gate["blocking_reasons"],
        *identity_gate["blocking_reasons"],
        *traceability_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    status = (
        "pass"
        if not blocking_reasons
        and agency_gate["status"]
        == signal_gate["status"]
        == identity_gate["status"]
        == traceability_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PET01_US_TA_SOURCE_MODEL_ID,
        "acceptance_id": S2PET01_ACCEPTANCE_ID,
        "task_id": S2PET01_TASK_ID,
        "legacy_task_id": S2PET01_LEGACY_TASK_ID,
        "phase": "S2PE",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "agency_coverage_gate": agency_gate["status"],
        "signal_type_gate": signal_gate["status"],
        "official_identity_gate": identity_gate["status"],
        "document_traceability_gate": traceability_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_agencies": list(S2PET01_REQUIRED_AGENCIES),
        "agencies_observed": agency_gate["agencies_observed"],
        "required_signal_types": list(S2PET01_REQUIRED_SIGNAL_TYPES),
        "signal_types_observed": signal_gate["signal_types_observed"],
        "required_trace_fields": list(S2PET01_REQUIRED_TRACE_FIELDS),
        "agency_records": agency_rows,
        "agency_record_count": len(agency_rows),
        "agency_summary": agency_gate,
        "signal_summary": signal_gate,
        "identity_summary": identity_gate,
        "traceability_summary": traceability_gate,
        "metadata_summary": metadata_gate,
        "d4_us_ta_source_foundation_ready": status == "pass",
        "d4_us_official_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "public_schema_changed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_modified": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pet01_us_ta_source_foundation(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    agency_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PET01 US-TA official source foundation evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pet01-us-ta-source-foundation"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pet01_us_ta_source_foundation_report(
        generated_at=generated_at,
        agency_records=agency_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "source_foundation_report_path": str(run_dir / "adp-s2pet01-us-ta-source-foundation-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pet01-us-ta-source-foundation-report.json", report)
        _write_json(state / S2PET01_REPORT_FILENAME, report)
    return report


def validate_s2pet01_us_ta_source_foundation_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PET01_US_TA_SOURCE_MODEL_ID:
        errors.append("S2PET01 US-TA model_id must be adp-s2pet01-us-ta-source-foundation-v1")
    if report.get("task_id") != S2PET01_TASK_ID:
        errors.append("S2PET01 US-TA task_id must be S2PET01")
    if report.get("legacy_task_id") != S2PET01_LEGACY_TASK_ID:
        errors.append("S2PET01 US-TA legacy_task_id must be S2P4T01")
    if report.get("acceptance_id") != S2PET01_ACCEPTANCE_ID:
        errors.append("S2PET01 US-TA acceptance_id must be ACC-S2PET01-US-TA")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PET01 US-TA status must be pass or blocked")
    for key in (
        "d4_us_official_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "public_schema_changed",
        "v7_1_current_switched",
        "v7_2_contract_files_modified",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PET01 US-TA source foundation")
    records = report.get("agency_records")
    if not isinstance(records, list):
        errors.append("S2PET01 agency_records must be a list")
        records = []
    observed_agencies = set(report.get("agencies_observed") or [])
    missing_agencies = [agency for agency in S2PET01_REQUIRED_AGENCIES if agency not in observed_agencies]
    if missing_agencies:
        errors.append("S2PET01 missing required agencies: " + ", ".join(missing_agencies))
    observed_signals = set(report.get("signal_types_observed") or [])
    missing_signals = [signal_type for signal_type in S2PET01_REQUIRED_SIGNAL_TYPES if signal_type not in observed_signals]
    if missing_signals:
        errors.append("S2PET01 missing required signal types: " + ", ".join(missing_signals))
    source_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"agency_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "")
        if not source_id:
            errors.append(f"agency_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PET01 source_id: {source_id}")
        source_ids.add(source_id)
        if record.get("agency_id") not in S2PET01_REQUIRED_AGENCIES:
            errors.append(f"agency_records[{index}].agency_id is not supported")
        if record.get("signal_type") not in S2PET01_REQUIRED_SIGNAL_TYPES:
            errors.append(f"agency_records[{index}].signal_type is not supported")
        if record.get("identity_state") not in S2PET01_ALLOWED_IDENTITY_STATES:
            errors.append(f"agency_records[{index}].identity_state is not accepted")
        if record.get("metadata_only") is not True:
            errors.append(f"agency_records[{index}].metadata_only must be true")
        if record.get("pdf_downloaded") is not False:
            errors.append(f"agency_records[{index}].pdf_downloaded must be false")
        if record.get("full_text_extracted") is not False:
            errors.append(f"agency_records[{index}].full_text_extracted must be false")
        if record.get("production_affected") is not False:
            errors.append(f"agency_records[{index}].production_affected must be false")
        if record.get("real_smtp_sent") is not False:
            errors.append(f"agency_records[{index}].real_smtp_sent must be false")
        if record.get("queue_mutation_allowed") is not False:
            errors.append(f"agency_records[{index}].queue_mutation_allowed must be false")
        for field in S2PET01_REQUIRED_TRACE_FIELDS:
            if not record.get(field):
                errors.append(f"agency_records[{index}].{field} is required")
        if not record.get("record_title"):
            errors.append(f"agency_records[{index}].record_title is required")
        if not record.get("evidence_refs"):
            errors.append(f"agency_records[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PET01 US-TA report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "agency_coverage_gate",
            "signal_type_gate",
            "official_identity_gate",
            "document_traceability_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PET01 US-TA report requires {key}=pass")
        if report.get("d4_us_ta_source_foundation_ready") is not True:
            errors.append("passing S2PET01 US-TA report requires d4_us_ta_source_foundation_ready=true")
    return errors


def build_s2pet02_us_lg_legal_backbone_report(
    *,
    generated_at: str,
    us_ta_source_foundation_report: Mapping[str, Any],
    legal_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build US-LG legal backbone metadata and cross-document relation evidence without production inclusion."""

    us_ta_errors = validate_s2pet01_us_ta_source_foundation_report(us_ta_source_foundation_report)
    us_ta_gate = (
        "pass"
        if not us_ta_errors
        and us_ta_source_foundation_report.get("status") == "pass"
        and us_ta_source_foundation_report.get("d4_us_ta_source_foundation_ready") is True
        else "blocked"
    )
    legal_rows, legal_row_errors = _s2pet02_legal_rows(legal_records)
    relation_rows, relation_row_errors = _s2pet02_relation_rows(relation_records)
    source_gate = _s2pet02_source_system_gate(legal_rows)
    document_gate = _s2pet02_document_type_gate(legal_rows)
    identity_gate = _s2pet02_legal_identity_gate(legal_rows)
    traceability_gate = _s2pet02_legal_traceability_gate(legal_rows)
    relation_gate = _s2pet02_relation_gate(legal_rows, relation_rows)
    metadata_gate = _s2pet02_legal_metadata_gate(legal_rows, relation_rows)
    upstream_reasons = [f"upstream S2PET01: {error}" for error in us_ta_errors]
    if us_ta_gate != "pass":
        upstream_reasons.append("upstream S2PET01 report must pass before S2PET02 US-LG legal backbone evidence")
    blocking_reasons = [
        *upstream_reasons,
        *legal_row_errors,
        *relation_row_errors,
        *source_gate["blocking_reasons"],
        *document_gate["blocking_reasons"],
        *identity_gate["blocking_reasons"],
        *traceability_gate["blocking_reasons"],
        *relation_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    status = (
        "pass"
        if not blocking_reasons
        and us_ta_gate
        == source_gate["status"]
        == document_gate["status"]
        == identity_gate["status"]
        == traceability_gate["status"]
        == relation_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PET02_US_LG_BACKBONE_MODEL_ID,
        "acceptance_id": S2PET02_ACCEPTANCE_ID,
        "task_id": S2PET02_TASK_ID,
        "legacy_task_id": S2PET02_LEGACY_TASK_ID,
        "phase": "S2PE",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_us_ta_source_foundation_gate": us_ta_gate,
        "source_system_coverage_gate": source_gate["status"],
        "document_type_gate": document_gate["status"],
        "official_identity_gate": identity_gate["status"],
        "document_traceability_gate": traceability_gate["status"],
        "legal_relation_gate": relation_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_source_systems": list(S2PET02_REQUIRED_SOURCE_SYSTEMS),
        "source_systems_observed": source_gate["source_systems_observed"],
        "required_document_types": list(S2PET02_REQUIRED_DOCUMENT_TYPES),
        "document_types_observed": document_gate["document_types_observed"],
        "required_relation_types": list(S2PET02_REQUIRED_RELATION_TYPES),
        "relation_types_observed": relation_gate["relation_types_observed"],
        "required_trace_fields": list(S2PET02_REQUIRED_TRACE_FIELDS),
        "required_relation_fields": list(S2PET02_REQUIRED_RELATION_FIELDS),
        "legal_records": legal_rows,
        "relation_records": relation_rows,
        "legal_record_count": len(legal_rows),
        "relation_record_count": len(relation_rows),
        "source_system_summary": source_gate,
        "document_type_summary": document_gate,
        "identity_summary": identity_gate,
        "traceability_summary": traceability_gate,
        "relation_summary": relation_gate,
        "metadata_summary": metadata_gate,
        "d4_us_lg_legal_backbone_ready": status == "pass",
        "d4_us_official_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "public_schema_changed": False,
        "legal_advice_provided": False,
        "live_source_fetch_executed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_modified": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pet02_us_lg_legal_backbone(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    us_ta_source_foundation_report: Mapping[str, Any],
    legal_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PET02 US-LG legal backbone evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pet02-us-lg-legal-backbone"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pet02_us_lg_legal_backbone_report(
        generated_at=generated_at,
        us_ta_source_foundation_report=us_ta_source_foundation_report,
        legal_records=legal_records,
        relation_records=relation_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "legal_backbone_report_path": str(run_dir / "adp-s2pet02-us-lg-legal-backbone-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pet02-us-lg-legal-backbone-report.json", report)
        _write_json(state / S2PET02_REPORT_FILENAME, report)
    return report


def validate_s2pet02_us_lg_legal_backbone_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PET02_US_LG_BACKBONE_MODEL_ID:
        errors.append("S2PET02 US-LG model_id must be adp-s2pet02-us-lg-legal-backbone-v1")
    if report.get("task_id") != S2PET02_TASK_ID:
        errors.append("S2PET02 US-LG task_id must be S2PET02")
    if report.get("legacy_task_id") != S2PET02_LEGACY_TASK_ID:
        errors.append("S2PET02 US-LG legacy_task_id must be S2P4T02")
    if report.get("acceptance_id") != S2PET02_ACCEPTANCE_ID:
        errors.append("S2PET02 US-LG acceptance_id must be ACC-S2PET02-US-LG")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PET02 US-LG status must be pass or blocked")
    for key in (
        "d4_us_official_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "public_schema_changed",
        "legal_advice_provided",
        "live_source_fetch_executed",
        "v7_1_current_switched",
        "v7_2_contract_files_modified",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PET02 US-LG legal backbone")
    records = report.get("legal_records")
    if not isinstance(records, list):
        errors.append("S2PET02 legal_records must be a list")
        records = []
    relations = report.get("relation_records")
    if not isinstance(relations, list):
        errors.append("S2PET02 relation_records must be a list")
        relations = []
    observed_sources = set(report.get("source_systems_observed") or [])
    missing_sources = [system for system in S2PET02_REQUIRED_SOURCE_SYSTEMS if system not in observed_sources]
    if missing_sources:
        errors.append("S2PET02 missing required source systems: " + ", ".join(missing_sources))
    observed_documents = set(report.get("document_types_observed") or [])
    missing_documents = [document_type for document_type in S2PET02_REQUIRED_DOCUMENT_TYPES if document_type not in observed_documents]
    if missing_documents:
        errors.append("S2PET02 missing required document types: " + ", ".join(missing_documents))
    observed_relations = set(report.get("relation_types_observed") or [])
    missing_relations = [relation_type for relation_type in S2PET02_REQUIRED_RELATION_TYPES if relation_type not in observed_relations]
    if missing_relations:
        errors.append("S2PET02 missing required relation types: " + ", ".join(missing_relations))
    document_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"legal_records[{index}] must be an object")
            continue
        document_id = str(record.get("document_id") or "")
        if not document_id:
            errors.append(f"legal_records[{index}].document_id is required")
        if document_id in document_ids:
            errors.append(f"duplicate S2PET02 document_id: {document_id}")
        document_ids.add(document_id)
        if record.get("source_system") not in S2PET02_REQUIRED_SOURCE_SYSTEMS:
            errors.append(f"legal_records[{index}].source_system is not supported")
        if record.get("document_type") not in S2PET02_REQUIRED_DOCUMENT_TYPES:
            errors.append(f"legal_records[{index}].document_type is not supported")
        if record.get("identity_state") not in S2PET02_ALLOWED_IDENTITY_STATES:
            errors.append(f"legal_records[{index}].identity_state is not accepted")
        if record.get("metadata_only") is not True:
            errors.append(f"legal_records[{index}].metadata_only must be true")
        if record.get("pdf_downloaded") is not False:
            errors.append(f"legal_records[{index}].pdf_downloaded must be false")
        if record.get("full_text_extracted") is not False:
            errors.append(f"legal_records[{index}].full_text_extracted must be false")
        if record.get("production_affected") is not False:
            errors.append(f"legal_records[{index}].production_affected must be false")
        if record.get("legal_advice_provided") is not False:
            errors.append(f"legal_records[{index}].legal_advice_provided must be false")
        for field in S2PET02_REQUIRED_TRACE_FIELDS:
            if not record.get(field):
                errors.append(f"legal_records[{index}].{field} is required")
        if not record.get("document_title"):
            errors.append(f"legal_records[{index}].document_title is required")
        if not record.get("evidence_refs"):
            errors.append(f"legal_records[{index}].evidence_refs is required")
    relation_ids: set[str] = set()
    for index, relation in enumerate(relations):
        if not isinstance(relation, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_id = str(relation.get("relation_id") or "")
        if not relation_id:
            errors.append(f"relation_records[{index}].relation_id is required")
        if relation_id in relation_ids:
            errors.append(f"duplicate S2PET02 relation_id: {relation_id}")
        relation_ids.add(relation_id)
        if relation.get("relation_type") not in S2PET02_REQUIRED_RELATION_TYPES:
            errors.append(f"relation_records[{index}].relation_type is not supported")
        if relation.get("source_document_id") not in document_ids:
            errors.append(f"relation_records[{index}].source_document_id must reference legal_records")
        if relation.get("target_document_id") not in document_ids:
            errors.append(f"relation_records[{index}].target_document_id must reference legal_records")
        if not relation.get("evidence_refs"):
            errors.append(f"relation_records[{index}].evidence_refs is required")
        if relation.get("metadata_only") is not True:
            errors.append(f"relation_records[{index}].metadata_only must be true")
        if relation.get("production_affected") is not False:
            errors.append(f"relation_records[{index}].production_affected must be false")
        if relation.get("schema_migration_required") is not False:
            errors.append(f"relation_records[{index}].schema_migration_required must be false")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PET02 US-LG report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_us_ta_source_foundation_gate",
            "source_system_coverage_gate",
            "document_type_gate",
            "official_identity_gate",
            "document_traceability_gate",
            "legal_relation_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PET02 US-LG report requires {key}=pass")
        if report.get("d4_us_lg_legal_backbone_ready") is not True:
            errors.append("passing S2PET02 US-LG report requires d4_us_lg_legal_backbone_ready=true")
    return errors


def build_s2pet03_us_fm_source_backbone_report(
    *,
    generated_at: str,
    us_lg_legal_backbone_report: Mapping[str, Any],
    finance_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build US-FM finance, market, and macro metadata evidence without trading or production inclusion."""

    us_lg_errors = validate_s2pet02_us_lg_legal_backbone_report(us_lg_legal_backbone_report)
    us_lg_gate = (
        "pass"
        if not us_lg_errors
        and us_lg_legal_backbone_report.get("status") == "pass"
        and us_lg_legal_backbone_report.get("d4_us_lg_legal_backbone_ready") is True
        else "blocked"
    )
    finance_rows, finance_row_errors = _s2pet03_finance_rows(finance_records)
    relation_rows, relation_row_errors = _s2pet03_finance_relation_rows(relation_records)
    source_gate = _s2pet03_source_system_gate(finance_rows)
    signal_gate = _s2pet03_signal_type_gate(finance_rows)
    sec_form_gate = _s2pet03_sec_form_gate(finance_rows)
    identifier_gate = _s2pet03_identifier_gate(finance_rows)
    identity_gate = _s2pet03_official_identity_gate(finance_rows)
    traceability_gate = _s2pet03_traceability_gate(finance_rows)
    relation_gate = _s2pet03_relation_gate(finance_rows, relation_rows)
    metadata_gate = _s2pet03_metadata_gate(finance_rows, relation_rows)
    upstream_reasons = [f"upstream S2PET02: {error}" for error in us_lg_errors]
    if us_lg_gate != "pass":
        upstream_reasons.append("upstream S2PET02 report must pass before S2PET03 US-FM source backbone evidence")
    blocking_reasons = [
        *upstream_reasons,
        *finance_row_errors,
        *relation_row_errors,
        *source_gate["blocking_reasons"],
        *signal_gate["blocking_reasons"],
        *sec_form_gate["blocking_reasons"],
        *identifier_gate["blocking_reasons"],
        *identity_gate["blocking_reasons"],
        *traceability_gate["blocking_reasons"],
        *relation_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    status = (
        "pass"
        if not blocking_reasons
        and us_lg_gate
        == source_gate["status"]
        == signal_gate["status"]
        == sec_form_gate["status"]
        == identifier_gate["status"]
        == identity_gate["status"]
        == traceability_gate["status"]
        == relation_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PET03_US_FM_BACKBONE_MODEL_ID,
        "acceptance_id": S2PET03_ACCEPTANCE_ID,
        "task_id": S2PET03_TASK_ID,
        "legacy_task_id": S2PET03_LEGACY_TASK_ID,
        "phase": "S2PE",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_us_lg_legal_backbone_gate": us_lg_gate,
        "source_system_coverage_gate": source_gate["status"],
        "signal_type_gate": signal_gate["status"],
        "sec_form_coverage_gate": sec_form_gate["status"],
        "identifier_gate": identifier_gate["status"],
        "official_identity_gate": identity_gate["status"],
        "document_traceability_gate": traceability_gate["status"],
        "finance_relation_gate": relation_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_source_systems": list(S2PET03_REQUIRED_SOURCE_SYSTEMS),
        "source_systems_observed": source_gate["source_systems_observed"],
        "required_signal_types": list(S2PET03_REQUIRED_SIGNAL_TYPES),
        "signal_types_observed": signal_gate["signal_types_observed"],
        "required_sec_form_types": list(S2PET03_REQUIRED_SEC_FORM_TYPES),
        "sec_form_types_observed": sec_form_gate["sec_form_types_observed"],
        "required_relation_types": list(S2PET03_REQUIRED_RELATION_TYPES),
        "relation_types_observed": relation_gate["relation_types_observed"],
        "required_trace_fields": list(S2PET03_REQUIRED_TRACE_FIELDS),
        "required_identifier_fields": list(S2PET03_REQUIRED_IDENTIFIER_FIELDS),
        "required_relation_fields": list(S2PET03_REQUIRED_RELATION_FIELDS),
        "finance_records": finance_rows,
        "relation_records": relation_rows,
        "finance_record_count": len(finance_rows),
        "relation_record_count": len(relation_rows),
        "source_system_summary": source_gate,
        "signal_summary": signal_gate,
        "sec_form_summary": sec_form_gate,
        "identifier_summary": identifier_gate,
        "identity_summary": identity_gate,
        "traceability_summary": traceability_gate,
        "relation_summary": relation_gate,
        "metadata_summary": metadata_gate,
        "d4_us_fm_source_backbone_ready": status == "pass",
        "d4_us_official_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "public_schema_changed": False,
        "investment_advice_provided": False,
        "trading_signal_generated": False,
        "automated_trading_enabled": False,
        "paid_market_data_used": False,
        "live_source_fetch_executed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_modified": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pet03_us_fm_source_backbone(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    us_lg_legal_backbone_report: Mapping[str, Any],
    finance_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PET03 US-FM source backbone evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pet03-us-fm-source-backbone"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pet03_us_fm_source_backbone_report(
        generated_at=generated_at,
        us_lg_legal_backbone_report=us_lg_legal_backbone_report,
        finance_records=finance_records,
        relation_records=relation_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "finance_backbone_report_path": str(run_dir / "adp-s2pet03-us-fm-source-backbone-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pet03-us-fm-source-backbone-report.json", report)
        _write_json(state / S2PET03_REPORT_FILENAME, report)
    return report


def validate_s2pet03_us_fm_source_backbone_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PET03_US_FM_BACKBONE_MODEL_ID:
        errors.append("S2PET03 US-FM model_id must be adp-s2pet03-us-fm-source-backbone-v1")
    if report.get("task_id") != S2PET03_TASK_ID:
        errors.append("S2PET03 US-FM task_id must be S2PET03")
    if report.get("legacy_task_id") != S2PET03_LEGACY_TASK_ID:
        errors.append("S2PET03 US-FM legacy_task_id must be S2P4T03")
    if report.get("acceptance_id") != S2PET03_ACCEPTANCE_ID:
        errors.append("S2PET03 US-FM acceptance_id must be ACC-S2PET03-US-FM")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PET03 US-FM status must be pass or blocked")
    for key in (
        "d4_us_official_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "public_schema_changed",
        "investment_advice_provided",
        "trading_signal_generated",
        "automated_trading_enabled",
        "paid_market_data_used",
        "live_source_fetch_executed",
        "v7_1_current_switched",
        "v7_2_contract_files_modified",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PET03 US-FM source backbone")
    records = report.get("finance_records")
    if not isinstance(records, list):
        errors.append("S2PET03 finance_records must be a list")
        records = []
    relations = report.get("relation_records")
    if not isinstance(relations, list):
        errors.append("S2PET03 relation_records must be a list")
        relations = []
    observed_sources = set(report.get("source_systems_observed") or [])
    missing_sources = [system for system in S2PET03_REQUIRED_SOURCE_SYSTEMS if system not in observed_sources]
    if missing_sources:
        errors.append("S2PET03 missing required source systems: " + ", ".join(missing_sources))
    observed_signals = set(report.get("signal_types_observed") or [])
    missing_signals = [signal for signal in S2PET03_REQUIRED_SIGNAL_TYPES if signal not in observed_signals]
    if missing_signals:
        errors.append("S2PET03 missing required signal types: " + ", ".join(missing_signals))
    observed_forms = set(report.get("sec_form_types_observed") or [])
    missing_forms = [form_type for form_type in S2PET03_REQUIRED_SEC_FORM_TYPES if form_type not in observed_forms]
    if missing_forms:
        errors.append("S2PET03 missing required SEC form types: " + ", ".join(missing_forms))
    observed_relations = set(report.get("relation_types_observed") or [])
    missing_relations = [relation_type for relation_type in S2PET03_REQUIRED_RELATION_TYPES if relation_type not in observed_relations]
    if missing_relations:
        errors.append("S2PET03 missing required relation types: " + ", ".join(missing_relations))
    record_ids: set[str] = set()
    entity_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"finance_records[{index}] must be an object")
            continue
        record_id = str(record.get("record_id") or "")
        if not record_id:
            errors.append(f"finance_records[{index}].record_id is required")
        if record_id in record_ids:
            errors.append(f"duplicate S2PET03 record_id: {record_id}")
        record_ids.add(record_id)
        entity_id = str(record.get("entity_id") or "")
        if entity_id:
            entity_ids.add(entity_id)
        for related in record.get("related_entity_ids") or []:
            if related:
                entity_ids.add(str(related))
        if record.get("source_system") not in S2PET03_REQUIRED_SOURCE_SYSTEMS:
            errors.append(f"finance_records[{index}].source_system is not supported")
        if record.get("signal_type") not in S2PET03_REQUIRED_SIGNAL_TYPES:
            errors.append(f"finance_records[{index}].signal_type is not supported")
        if record.get("source_system") == "sec_edgar" and record.get("form_type") not in S2PET03_REQUIRED_SEC_FORM_TYPES:
            errors.append(f"finance_records[{index}].form_type is not supported for SEC EDGAR")
        if record.get("identity_state") not in S2PET03_ALLOWED_IDENTITY_STATES:
            errors.append(f"finance_records[{index}].identity_state is not accepted")
        for field in S2PET03_REQUIRED_TRACE_FIELDS:
            if not record.get(field):
                errors.append(f"finance_records[{index}].{field} is required")
        if record.get("source_system") == "sec_edgar":
            for field in S2PET03_REQUIRED_IDENTIFIER_FIELDS:
                if not record.get(field):
                    errors.append(f"finance_records[{index}].{field} is required for SEC EDGAR")
        if not record.get("record_title"):
            errors.append(f"finance_records[{index}].record_title is required")
        if not record.get("evidence_refs"):
            errors.append(f"finance_records[{index}].evidence_refs is required")
        for key in (
            "metadata_only",
            "pdf_downloaded",
            "full_text_extracted",
            "production_affected",
            "investment_advice_provided",
            "trading_signal_generated",
            "automated_trading_enabled",
            "paid_market_data_used",
            "live_source_fetch_executed",
        ):
            expected = True if key == "metadata_only" else False
            if record.get(key) is not expected:
                errors.append(f"finance_records[{index}].{key} must be {str(expected).lower()}")
    relation_ids: set[str] = set()
    for index, relation in enumerate(relations):
        if not isinstance(relation, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_id = str(relation.get("relation_id") or "")
        if not relation_id:
            errors.append(f"relation_records[{index}].relation_id is required")
        if relation_id in relation_ids:
            errors.append(f"duplicate S2PET03 relation_id: {relation_id}")
        relation_ids.add(relation_id)
        if relation.get("relation_type") not in S2PET03_REQUIRED_RELATION_TYPES:
            errors.append(f"relation_records[{index}].relation_type is not supported")
        if relation.get("source_record_id") not in record_ids:
            errors.append(f"relation_records[{index}].source_record_id must reference finance_records")
        if relation.get("target_entity_id") not in entity_ids:
            errors.append(f"relation_records[{index}].target_entity_id must reference finance record entities")
        if not relation.get("evidence_refs"):
            errors.append(f"relation_records[{index}].evidence_refs is required")
        if relation.get("metadata_only") is not True:
            errors.append(f"relation_records[{index}].metadata_only must be true")
        if relation.get("production_affected") is not False:
            errors.append(f"relation_records[{index}].production_affected must be false")
        if relation.get("schema_migration_required") is not False:
            errors.append(f"relation_records[{index}].schema_migration_required must be false")
        if relation.get("trading_signal_generated") is not False:
            errors.append(f"relation_records[{index}].trading_signal_generated must be false")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PET03 US-FM report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_us_lg_legal_backbone_gate",
            "source_system_coverage_gate",
            "signal_type_gate",
            "sec_form_coverage_gate",
            "identifier_gate",
            "official_identity_gate",
            "document_traceability_gate",
            "finance_relation_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PET03 US-FM report requires {key}=pass")
        if report.get("d4_us_fm_source_backbone_ready") is not True:
            errors.append("passing S2PET03 US-FM report requires d4_us_fm_source_backbone_ready=true")
    return errors


def build_s2pet04_us_tp_d4_qualification_report(
    *,
    generated_at: str,
    us_ta_source_foundation_report: Mapping[str, Any],
    us_lg_legal_backbone_report: Mapping[str, Any],
    us_fm_source_backbone_report: Mapping[str, Any],
    policy_records: Sequence[Mapping[str, Any]],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    board_route_records: Sequence[Mapping[str, Any]],
    budget_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build US-TP and D4 qualification evidence without production inclusion."""

    us_ta_errors = validate_s2pet01_us_ta_source_foundation_report(us_ta_source_foundation_report)
    us_lg_errors = validate_s2pet02_us_lg_legal_backbone_report(us_lg_legal_backbone_report)
    us_fm_errors = validate_s2pet03_us_fm_source_backbone_report(us_fm_source_backbone_report)
    upstream_gate = (
        "pass"
        if not us_ta_errors
        and not us_lg_errors
        and not us_fm_errors
        and us_ta_source_foundation_report.get("status") == "pass"
        and us_ta_source_foundation_report.get("d4_us_ta_source_foundation_ready") is True
        and us_lg_legal_backbone_report.get("status") == "pass"
        and us_lg_legal_backbone_report.get("d4_us_lg_legal_backbone_ready") is True
        and us_fm_source_backbone_report.get("status") == "pass"
        and us_fm_source_backbone_report.get("d4_us_fm_source_backbone_ready") is True
        else "blocked"
    )
    policy_rows, policy_errors = _s2pet04_policy_rows(policy_records)
    replay_rows, replay_errors = _s2pet04_replay_rows(replay_records)
    shadow_rows, shadow_errors = _s2pet04_shadow_rows(shadow_records)
    route_rows, route_errors = _s2pet04_board_route_rows(board_route_records)
    budget_rows, budget_errors = _s2pet04_budget_rows(budget_records)
    source_gate = _s2pet04_source_system_gate(policy_rows)
    signal_gate = _s2pet04_signal_type_gate(policy_rows)
    identity_gate = _s2pet04_official_identity_gate(policy_rows)
    replay_gate = _s2pet04_replay_gate(replay_rows)
    shadow_gate = _s2pet04_shadow_gate(shadow_rows)
    route_gate = _s2pet04_board_route_gate(route_rows)
    budget_gate = _s2pet04_budget_gate(budget_rows)
    metadata_gate = _s2pet04_metadata_gate(policy_rows, replay_rows, shadow_rows, route_rows, budget_rows)
    upstream_reasons = [f"upstream S2PET01: {error}" for error in us_ta_errors]
    upstream_reasons.extend(f"upstream S2PET02: {error}" for error in us_lg_errors)
    upstream_reasons.extend(f"upstream S2PET03: {error}" for error in us_fm_errors)
    if upstream_gate != "pass":
        upstream_reasons.append("upstream S2PET01-S2PET03 reports must pass before S2PET04 D4 qualification evidence")
    blocking_reasons = [
        *upstream_reasons,
        *policy_errors,
        *replay_errors,
        *shadow_errors,
        *route_errors,
        *budget_errors,
        *source_gate["blocking_reasons"],
        *signal_gate["blocking_reasons"],
        *identity_gate["blocking_reasons"],
        *replay_gate["blocking_reasons"],
        *shadow_gate["blocking_reasons"],
        *route_gate["blocking_reasons"],
        *budget_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == source_gate["status"]
        == signal_gate["status"]
        == identity_gate["status"]
        == replay_gate["status"]
        == shadow_gate["status"]
        == route_gate["status"]
        == budget_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PET04_US_TP_D4_QUALIFICATION_MODEL_ID,
        "acceptance_id": S2PET04_ACCEPTANCE_ID,
        "task_id": S2PET04_TASK_ID,
        "legacy_task_id": S2PET04_LEGACY_TASK_ID,
        "phase": "S2PE",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_s2pet01_s2pet03_gate": upstream_gate,
        "us_tp_source_system_gate": source_gate["status"],
        "us_tp_signal_type_gate": signal_gate["status"],
        "official_identity_gate": identity_gate["status"],
        "d4_replay_gate": replay_gate["status"],
        "d4_shadow_gate": shadow_gate["status"],
        "board_routing_gate": route_gate["status"],
        "budget_explanation_gate": budget_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_source_systems": list(S2PET04_REQUIRED_SOURCE_SYSTEMS),
        "source_systems_observed": source_gate["source_systems_observed"],
        "required_signal_types": list(S2PET04_REQUIRED_SIGNAL_TYPES),
        "signal_types_observed": signal_gate["signal_types_observed"],
        "required_d4_components": list(S2PET04_REQUIRED_D4_COMPONENTS),
        "d4_components_observed": replay_gate["d4_components_observed"],
        "required_board_ids": list(S2PET04_REQUIRED_BOARD_IDS),
        "board_ids_observed": route_gate["board_ids_observed"],
        "required_budget_segments": list(S2PET04_REQUIRED_BUDGET_SEGMENTS),
        "required_budget_weights": list(S2PET04_REQUIRED_BUDGET_WEIGHTS),
        "budget_segments_observed": budget_gate["budget_segments_observed"],
        "budget_weight_total": budget_gate["budget_weight_total"],
        "required_replay_dates": S2PET04_REQUIRED_REPLAY_DATES,
        "replay_dates_observed": replay_gate["replay_dates_observed"],
        "required_shadow_days": S2PET04_REQUIRED_SHADOW_DAYS,
        "shadow_dates_observed": shadow_gate["shadow_dates_observed"],
        "policy_records": policy_rows,
        "replay_records": replay_rows,
        "shadow_records": shadow_rows,
        "board_route_records": route_rows,
        "budget_records": budget_rows,
        "policy_record_count": len(policy_rows),
        "replay_record_count": len(replay_rows),
        "shadow_record_count": len(shadow_rows),
        "board_route_record_count": len(route_rows),
        "budget_record_count": len(budget_rows),
        "source_system_summary": source_gate,
        "signal_summary": signal_gate,
        "identity_summary": identity_gate,
        "replay_summary": replay_gate,
        "shadow_summary": shadow_gate,
        "board_route_summary": route_gate,
        "budget_summary": budget_gate,
        "metadata_summary": metadata_gate,
        "d4_us_tp_and_qualification_ready": status == "pass",
        "d4_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "public_schema_changed": False,
        "live_source_fetch_executed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_modified": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pet04_us_tp_d4_qualification(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    us_ta_source_foundation_report: Mapping[str, Any],
    us_lg_legal_backbone_report: Mapping[str, Any],
    us_fm_source_backbone_report: Mapping[str, Any],
    policy_records: Sequence[Mapping[str, Any]],
    replay_records: Sequence[Mapping[str, Any]],
    shadow_records: Sequence[Mapping[str, Any]],
    board_route_records: Sequence[Mapping[str, Any]],
    budget_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PET04 US-TP and D4 qualification evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pet04-us-tp-d4-qualification"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pet04_us_tp_d4_qualification_report(
        generated_at=generated_at,
        us_ta_source_foundation_report=us_ta_source_foundation_report,
        us_lg_legal_backbone_report=us_lg_legal_backbone_report,
        us_fm_source_backbone_report=us_fm_source_backbone_report,
        policy_records=policy_records,
        replay_records=replay_records,
        shadow_records=shadow_records,
        board_route_records=board_route_records,
        budget_records=budget_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "d4_qualification_report_path": str(run_dir / "adp-s2pet04-us-tp-d4-qualification-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pet04-us-tp-d4-qualification-report.json", report)
        _write_json(state / S2PET04_REPORT_FILENAME, report)
    return report


def validate_s2pet04_us_tp_d4_qualification_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PET04_US_TP_D4_QUALIFICATION_MODEL_ID:
        errors.append("S2PET04 model_id must be adp-s2pet04-us-tp-d4-qualification-v1")
    if report.get("task_id") != S2PET04_TASK_ID:
        errors.append("S2PET04 task_id must be S2PET04")
    if report.get("legacy_task_id") != S2PET04_LEGACY_TASK_ID:
        errors.append("S2PET04 legacy_task_id must be S2P4T04")
    if report.get("acceptance_id") != S2PET04_ACCEPTANCE_ID:
        errors.append("S2PET04 acceptance_id must be ACC-S2PET04-D4")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PET04 status must be pass or blocked")
    for key in (
        "d4_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "public_schema_changed",
        "live_source_fetch_executed",
        "v7_1_current_switched",
        "v7_2_contract_files_modified",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PET04 D4 qualification")
    for key in ("policy_records", "replay_records", "shadow_records", "board_route_records", "budget_records"):
        if not isinstance(report.get(key), list):
            errors.append(f"S2PET04 {key} must be a list")
    missing_sources = [system for system in S2PET04_REQUIRED_SOURCE_SYSTEMS if system not in set(report.get("source_systems_observed") or [])]
    if missing_sources:
        errors.append("S2PET04 missing required source systems: " + ", ".join(missing_sources))
    missing_signals = [signal for signal in S2PET04_REQUIRED_SIGNAL_TYPES if signal not in set(report.get("signal_types_observed") or [])]
    if missing_signals:
        errors.append("S2PET04 missing required signal types: " + ", ".join(missing_signals))
    missing_components = [component for component in S2PET04_REQUIRED_D4_COMPONENTS if component not in set(report.get("d4_components_observed") or [])]
    if missing_components:
        errors.append("S2PET04 missing D4 components in replay: " + ", ".join(missing_components))
    if len(set(report.get("replay_dates_observed") or [])) < S2PET04_REQUIRED_REPLAY_DATES:
        errors.append("S2PET04 D4 qualification requires at least 30 replay dates")
    if len(set(report.get("shadow_dates_observed") or [])) < S2PET04_REQUIRED_SHADOW_DAYS:
        errors.append("S2PET04 D4 qualification requires at least 2 shadow dates")
    missing_boards = [board for board in S2PET04_REQUIRED_BOARD_IDS if board not in set(report.get("board_ids_observed") or [])]
    if missing_boards:
        errors.append("S2PET04 missing board routes: " + ", ".join(missing_boards))
    missing_budget = [segment for segment in S2PET04_REQUIRED_BUDGET_SEGMENTS if segment not in set(report.get("budget_segments_observed") or [])]
    if missing_budget:
        errors.append("S2PET04 missing budget segments: " + ", ".join(missing_budget))
    if report.get("budget_weight_total") != 100:
        errors.append("S2PET04 budget weights must total 100")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PET04 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_s2pet01_s2pet03_gate",
            "us_tp_source_system_gate",
            "us_tp_signal_type_gate",
            "official_identity_gate",
            "d4_replay_gate",
            "d4_shadow_gate",
            "board_routing_gate",
            "budget_explanation_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PET04 report requires {key}=pass")
        if report.get("d4_us_tp_and_qualification_ready") is not True:
            errors.append("passing S2PET04 report requires d4_us_tp_and_qualification_ready=true")
    return errors


def build_s2pft01_china_provincial_template_coverage_report(
    *,
    generated_at: str,
    d3_readiness_review_report: Mapping[str, Any],
    provincial_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build mainland provincial template coverage evidence without production inclusion."""

    d3_errors = validate_s2pdt04_china_d3_readiness_review_report(d3_readiness_review_report)
    d3_gate = (
        "pass"
        if not d3_errors
        and d3_readiness_review_report.get("status") == "pass"
        and d3_readiness_review_report.get("d3_core_readiness_review_ready") is True
        else "blocked"
    )
    province_rows, row_errors = _s2pft01_provincial_rows(provincial_records)
    coverage_gate = _s2pft01_provincial_coverage_gate(province_rows)
    department_gate = _s2pft01_core_department_gate(province_rows)
    health_gate = _s2pft01_health_tier_gate(province_rows)
    authority_gate = _s2pft01_provincial_authority_gate(province_rows)
    metadata_gate = _s2pft01_provincial_metadata_gate(province_rows)
    blocking_reasons = [
        *d3_errors,
        *row_errors,
        *coverage_gate["blocking_reasons"],
        *department_gate["blocking_reasons"],
        *health_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if d3_gate != "pass":
        blocking_reasons.append("S2PFT01 requires passing S2PDT04 China D3 readiness review evidence")
    status = (
        "pass"
        if not blocking_reasons
        and d3_gate
        == coverage_gate["status"]
        == department_gate["status"]
        == health_gate["status"]
        == authority_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PFT01_CHINA_PROVINCIAL_MODEL_ID,
        "acceptance_id": S2PFT01_ACCEPTANCE_ID,
        "task_id": S2PFT01_TASK_ID,
        "legacy_task_id": S2PFT01_LEGACY_TASK_ID,
        "phase": "S2PF",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_d3_readiness_gate": d3_gate,
        "provincial_coverage_gate": coverage_gate["status"],
        "core_department_template_gate": department_gate["status"],
        "health_tier_gate": health_gate["status"],
        "authority_gate": authority_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_mainland_provincial_ids": list(S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS),
        "required_mainland_provincial_count": len(S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS),
        "provincial_ids_observed": coverage_gate["provincial_ids_observed"],
        "provincial_record_count": len(province_rows),
        "required_locality_types": list(S2PFT01_REQUIRED_LOCALITY_TYPES),
        "locality_types_observed": coverage_gate["locality_types_observed"],
        "required_core_department_roles": list(S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES),
        "health_tiers_observed": health_gate["health_tiers_observed"],
        "provincial_records": province_rows,
        "provincial_coverage_summary": coverage_gate,
        "core_department_template_summary": department_gate,
        "health_tier_summary": health_gate,
        "authority_summary": authority_gate,
        "metadata_summary": metadata_gate,
        "s2pf_provincial_template_coverage_ready": status == "pass",
        "d3_full_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "v7_2_mail_or_schema_prerun": False,
        "hk_mo_profile_modeled": False,
        "city_coverage_modeled": False,
        "special_zone_discovery_enabled": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pft01_china_provincial_template_coverage(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    d3_readiness_review_report: Mapping[str, Any],
    provincial_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PFT01 China provincial template coverage evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pft01-china-provincial-template-coverage"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pft01_china_provincial_template_coverage_report(
        generated_at=generated_at,
        d3_readiness_review_report=d3_readiness_review_report,
        provincial_records=provincial_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "provincial_template_coverage_report_path": str(
                run_dir / "adp-s2pft01-china-provincial-template-coverage-report.json"
            ),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pft01-china-provincial-template-coverage-report.json", report)
        _write_json(state / S2PFT01_REPORT_FILENAME, report)
    return report


def validate_s2pft01_china_provincial_template_coverage_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PFT01_CHINA_PROVINCIAL_MODEL_ID:
        errors.append("S2PFT01 provincial model_id must be adp-s2pft01-china-provincial-template-coverage-v1")
    if report.get("task_id") != S2PFT01_TASK_ID:
        errors.append("S2PFT01 provincial task_id must be S2PFT01")
    if report.get("legacy_task_id") != S2PFT01_LEGACY_TASK_ID:
        errors.append("S2PFT01 provincial legacy_task_id must be S2P5T01")
    if report.get("acceptance_id") != S2PFT01_ACCEPTANCE_ID:
        errors.append("S2PFT01 provincial acceptance_id must be ACC-S2PFT01-PROVINCES")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PFT01 provincial status must be pass or blocked")
    for key in (
        "d3_full_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
        "v7_2_mail_or_schema_prerun",
        "hk_mo_profile_modeled",
        "city_coverage_modeled",
        "special_zone_discovery_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PFT01 provincial template coverage")
    provincial_records = report.get("provincial_records")
    if not isinstance(provincial_records, list):
        errors.append("S2PFT01 provincial_records must be a list")
        provincial_records = []
    observed_ids = set(report.get("provincial_ids_observed") or [])
    missing_ids = [province_id for province_id in S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS if province_id not in observed_ids]
    if missing_ids:
        errors.append("S2PFT01 missing mainland provincial ids: " + ", ".join(missing_ids))
    observed_types = set(report.get("locality_types_observed") or [])
    missing_types = [locality_type for locality_type in S2PFT01_REQUIRED_LOCALITY_TYPES if locality_type not in observed_types]
    if missing_types:
        errors.append("S2PFT01 missing locality types: " + ", ".join(missing_types))
    for index, record in enumerate(provincial_records):
        if not isinstance(record, Mapping):
            errors.append(f"provincial_records[{index}] must be an object")
            continue
        if record.get("province_id") not in S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS:
            errors.append(f"provincial_records[{index}].province_id is not supported")
        if record.get("locality_type") not in S2PFT01_REQUIRED_LOCALITY_TYPES:
            errors.append(f"provincial_records[{index}].locality_type is not supported")
        if not record.get("province_name"):
            errors.append(f"provincial_records[{index}].province_name is required")
        for field in ("official_domain", "source_url", "health_explanation"):
            if not record.get(field):
                errors.append(f"provincial_records[{index}].{field} is required")
        if record.get("identity_state") not in S2PFT01_ALLOWED_IDENTITY_STATES:
            errors.append(f"provincial_records[{index}].identity_state is not supported")
        if record.get("health_tier") not in S2PFT01_ALLOWED_HEALTH_TIERS:
            errors.append(f"provincial_records[{index}].health_tier is not supported")
        missing_roles = [
            role for role in S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES if role not in set(record.get("core_department_roles") or [])
        ]
        if missing_roles:
            errors.append(f"provincial_records[{index}] missing core roles: " + ", ".join(missing_roles))
        if record.get("authority_gate") != "pass":
            errors.append(f"provincial_records[{index}].authority_gate must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"provincial_records[{index}].metadata_only must be true")
        for field in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if record.get(field) is not False:
                errors.append(f"provincial_records[{index}].{field} must be false")
        if not record.get("evidence_refs"):
            errors.append(f"provincial_records[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PFT01 provincial report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_d3_readiness_gate",
            "provincial_coverage_gate",
            "core_department_template_gate",
            "health_tier_gate",
            "authority_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PFT01 provincial report requires {key}=pass")
        if report.get("s2pf_provincial_template_coverage_ready") is not True:
            errors.append("passing S2PFT01 provincial report requires s2pf_provincial_template_coverage_ready=true")
    return errors


def build_s2pft02_hk_mo_independent_profile_report(
    *,
    generated_at: str,
    provincial_template_coverage_report: Mapping[str, Any],
    jurisdiction_profiles: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build Hong Kong and Macau independent profile evidence without production inclusion."""

    upstream_errors = validate_s2pft01_china_provincial_template_coverage_report(provincial_template_coverage_report)
    upstream_gate = (
        "pass"
        if not upstream_errors
        and provincial_template_coverage_report.get("status") == "pass"
        and provincial_template_coverage_report.get("s2pf_provincial_template_coverage_ready") is True
        else "blocked"
    )
    profiles, profile_errors = _s2pft02_jurisdiction_profiles(jurisdiction_profiles)
    jurisdiction_gate = _s2pft02_jurisdiction_coverage_gate(profiles)
    language_gate = _s2pft02_language_gate(profiles)
    legal_gate = _s2pft02_legal_status_gate(profiles)
    independence_gate = _s2pft02_template_independence_gate(profiles)
    authority_gate = _s2pft02_authority_gate(profiles)
    metadata_gate = _s2pft02_metadata_gate(profiles)
    blocking_reasons = [
        *upstream_errors,
        *profile_errors,
        *jurisdiction_gate["blocking_reasons"],
        *language_gate["blocking_reasons"],
        *legal_gate["blocking_reasons"],
        *independence_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PFT02 requires passing S2PFT01 provincial template coverage evidence")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == jurisdiction_gate["status"]
        == language_gate["status"]
        == legal_gate["status"]
        == independence_gate["status"]
        == authority_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PFT02_HK_MO_PROFILE_MODEL_ID,
        "acceptance_id": S2PFT02_ACCEPTANCE_ID,
        "task_id": S2PFT02_TASK_ID,
        "legacy_task_id": S2PFT02_LEGACY_TASK_ID,
        "phase": "S2PF",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_provincial_template_gate": upstream_gate,
        "jurisdiction_coverage_gate": jurisdiction_gate["status"],
        "language_profile_gate": language_gate["status"],
        "legal_status_gate": legal_gate["status"],
        "template_independence_gate": independence_gate["status"],
        "authority_gate": authority_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_jurisdiction_ids": list(S2PFT02_REQUIRED_JURISDICTION_IDS),
        "jurisdiction_ids_observed": jurisdiction_gate["jurisdiction_ids_observed"],
        "jurisdiction_profile_count": len(profiles),
        "required_language_profiles": list(S2PFT02_REQUIRED_LANGUAGE_PROFILES),
        "language_profiles_observed": language_gate["language_profiles_observed"],
        "required_profile_fields": list(S2PFT02_REQUIRED_PROFILE_FIELDS),
        "allowed_legal_system_states": list(S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES),
        "legal_system_states_observed": legal_gate["legal_system_states_observed"],
        "jurisdiction_profiles": profiles,
        "jurisdiction_coverage_summary": jurisdiction_gate,
        "language_profile_summary": language_gate,
        "legal_status_summary": legal_gate,
        "template_independence_summary": independence_gate,
        "authority_summary": authority_gate,
        "metadata_summary": metadata_gate,
        "s2pf_hk_mo_profile_ready": status == "pass",
        "d3_full_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "v7_2_mail_or_schema_prerun": False,
        "hk_mo_profile_modeled": status == "pass",
        "mainland_template_applied_to_hk_mo": False,
        "city_coverage_modeled": False,
        "special_zone_discovery_enabled": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pft02_hk_mo_independent_profile(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    provincial_template_coverage_report: Mapping[str, Any],
    jurisdiction_profiles: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PFT02 Hong Kong/Macau profile evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pft02-hk-mo-independent-profile"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pft02_hk_mo_independent_profile_report(
        generated_at=generated_at,
        provincial_template_coverage_report=provincial_template_coverage_report,
        jurisdiction_profiles=jurisdiction_profiles,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "hk_mo_profile_report_path": str(run_dir / "adp-s2pft02-hk-mo-independent-profile-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pft02-hk-mo-independent-profile-report.json", report)
        _write_json(state / S2PFT02_REPORT_FILENAME, report)
    return report


def validate_s2pft02_hk_mo_independent_profile_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PFT02_HK_MO_PROFILE_MODEL_ID:
        errors.append("S2PFT02 HK/MO model_id must be adp-s2pft02-hk-mo-independent-profile-v1")
    if report.get("task_id") != S2PFT02_TASK_ID:
        errors.append("S2PFT02 HK/MO task_id must be S2PFT02")
    if report.get("legacy_task_id") != S2PFT02_LEGACY_TASK_ID:
        errors.append("S2PFT02 HK/MO legacy_task_id must be S2P5T02")
    if report.get("acceptance_id") != S2PFT02_ACCEPTANCE_ID:
        errors.append("S2PFT02 HK/MO acceptance_id must be ACC-S2PFT02-HK-MO")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PFT02 HK/MO status must be pass or blocked")
    for key in (
        "d3_full_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
        "v7_2_mail_or_schema_prerun",
        "mainland_template_applied_to_hk_mo",
        "city_coverage_modeled",
        "special_zone_discovery_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PFT02 HK/MO profile evidence")
    profiles = report.get("jurisdiction_profiles")
    if not isinstance(profiles, list):
        errors.append("S2PFT02 jurisdiction_profiles must be a list")
        profiles = []
    observed_ids = set(report.get("jurisdiction_ids_observed") or [])
    missing_ids = [jurisdiction_id for jurisdiction_id in S2PFT02_REQUIRED_JURISDICTION_IDS if jurisdiction_id not in observed_ids]
    if missing_ids:
        errors.append("S2PFT02 missing jurisdiction ids: " + ", ".join(missing_ids))
    observed_languages = set(report.get("language_profiles_observed") or [])
    missing_languages = [
        language_profile for language_profile in S2PFT02_REQUIRED_LANGUAGE_PROFILES if language_profile not in observed_languages
    ]
    if missing_languages:
        errors.append("S2PFT02 missing language profiles: " + ", ".join(missing_languages))
    observed_legal_states = set(report.get("legal_system_states_observed") or [])
    for state in S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES:
        if state not in observed_legal_states:
            errors.append(f"S2PFT02 missing legal system state: {state}")
    for index, profile in enumerate(profiles):
        if not isinstance(profile, Mapping):
            errors.append(f"jurisdiction_profiles[{index}] must be an object")
            continue
        if profile.get("jurisdiction_id") not in S2PFT02_REQUIRED_JURISDICTION_IDS:
            errors.append(f"jurisdiction_profiles[{index}].jurisdiction_id is not supported")
        for field in S2PFT02_REQUIRED_PROFILE_FIELDS:
            if profile.get(field) in (None, "", []):
                errors.append(f"jurisdiction_profiles[{index}].{field} is required")
        if profile.get("legal_system_state") not in S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES:
            errors.append(f"jurisdiction_profiles[{index}].legal_system_state is not supported")
        if profile.get("template_source") in S2PFT02_FORBIDDEN_TEMPLATE_STATES:
            errors.append(f"jurisdiction_profiles[{index}].template_source must not be mainland template")
        if profile.get("mainland_template_applied") is not False:
            errors.append(f"jurisdiction_profiles[{index}].mainland_template_applied must be false")
        if profile.get("authority_gate") != "pass":
            errors.append(f"jurisdiction_profiles[{index}].authority_gate must be pass")
        if profile.get("metadata_only") is not True:
            errors.append(f"jurisdiction_profiles[{index}].metadata_only must be true")
        for field in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if profile.get(field) is not False:
                errors.append(f"jurisdiction_profiles[{index}].{field} must be false")
        if not profile.get("language_profiles"):
            errors.append(f"jurisdiction_profiles[{index}].language_profiles is required")
        if not profile.get("evidence_refs"):
            errors.append(f"jurisdiction_profiles[{index}].evidence_refs is required")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PFT02 HK/MO report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_provincial_template_gate",
            "jurisdiction_coverage_gate",
            "language_profile_gate",
            "legal_status_gate",
            "template_independence_gate",
            "authority_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PFT02 HK/MO report requires {key}=pass")
        if report.get("s2pf_hk_mo_profile_ready") is not True:
            errors.append("passing S2PFT02 HK/MO report requires s2pf_hk_mo_profile_ready=true")
        if report.get("hk_mo_profile_modeled") is not True:
            errors.append("passing S2PFT02 HK/MO report requires hk_mo_profile_modeled=true")
    return errors


def build_s2pft03_key_city_coverage_report(
    *,
    generated_at: str,
    hk_mo_profile_report: Mapping[str, Any],
    city_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build first key-city metadata coverage evidence without production inclusion."""

    upstream_errors = validate_s2pft02_hk_mo_independent_profile_report(hk_mo_profile_report)
    upstream_gate = (
        "pass"
        if not upstream_errors
        and hk_mo_profile_report.get("status") == "pass"
        and hk_mo_profile_report.get("s2pf_hk_mo_profile_ready") is True
        else "blocked"
    )
    city_rows, row_errors = _s2pft03_city_rows(city_records)
    coverage_gate = _s2pft03_city_coverage_gate(city_rows)
    alias_gate = _s2pft03_city_alias_gate(city_rows)
    department_gate = _s2pft03_city_department_gate(city_rows)
    region_gate = _s2pft03_region_weight_gate(city_rows)
    health_gate = _s2pft03_city_health_gate(city_rows)
    authority_gate = _s2pft03_city_authority_gate(city_rows)
    metadata_gate = _s2pft03_city_metadata_gate(city_rows)
    blocking_reasons = [
        *upstream_errors,
        *row_errors,
        *coverage_gate["blocking_reasons"],
        *alias_gate["blocking_reasons"],
        *department_gate["blocking_reasons"],
        *region_gate["blocking_reasons"],
        *health_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PFT03 requires passing S2PFT02 Hong Kong/Macau profile evidence")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == coverage_gate["status"]
        == alias_gate["status"]
        == department_gate["status"]
        == region_gate["status"]
        == health_gate["status"]
        == authority_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PFT03_KEY_CITY_COVERAGE_MODEL_ID,
        "acceptance_id": S2PFT03_ACCEPTANCE_ID,
        "task_id": S2PFT03_TASK_ID,
        "legacy_task_id": S2PFT03_LEGACY_TASK_ID,
        "phase": "S2PF",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_hk_mo_profile_gate": upstream_gate,
        "city_coverage_gate": coverage_gate["status"],
        "city_alias_gate": alias_gate["status"],
        "city_department_template_gate": department_gate["status"],
        "region_weight_gate": region_gate["status"],
        "health_tier_gate": health_gate["status"],
        "authority_gate": authority_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_city_ids": list(S2PFT03_REQUIRED_CITY_IDS),
        "required_city_count": len(S2PFT03_REQUIRED_CITY_IDS),
        "city_ids_observed": coverage_gate["city_ids_observed"],
        "city_record_count": len(city_rows),
        "required_city_department_roles": list(S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES),
        "allowed_region_groups": list(S2PFT03_ALLOWED_REGION_GROUPS),
        "region_groups_observed": region_gate["region_groups_observed"],
        "allowed_health_tiers": list(S2PFT03_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": health_gate["health_tiers_observed"],
        "city_records": city_rows,
        "city_coverage_summary": coverage_gate,
        "city_alias_summary": alias_gate,
        "city_department_template_summary": department_gate,
        "region_weight_summary": region_gate,
        "health_tier_summary": health_gate,
        "authority_summary": authority_gate,
        "metadata_summary": metadata_gate,
        "s2pf_key_city_coverage_ready": status == "pass",
        "d3_full_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "v7_2_mail_or_schema_prerun": False,
        "city_coverage_modeled": status == "pass",
        "special_zone_discovery_enabled": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pft03_key_city_coverage(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    hk_mo_profile_report: Mapping[str, Any],
    city_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PFT03 key-city coverage evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pft03-key-city-coverage"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pft03_key_city_coverage_report(
        generated_at=generated_at,
        hk_mo_profile_report=hk_mo_profile_report,
        city_records=city_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "key_city_coverage_report_path": str(run_dir / "adp-s2pft03-key-city-coverage-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pft03-key-city-coverage-report.json", report)
        _write_json(state / S2PFT03_REPORT_FILENAME, report)
    return report


def validate_s2pft03_key_city_coverage_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PFT03_KEY_CITY_COVERAGE_MODEL_ID:
        errors.append("S2PFT03 city model_id must be adp-s2pft03-key-city-coverage-v1")
    if report.get("task_id") != S2PFT03_TASK_ID:
        errors.append("S2PFT03 city task_id must be S2PFT03")
    if report.get("legacy_task_id") != S2PFT03_LEGACY_TASK_ID:
        errors.append("S2PFT03 city legacy_task_id must be S2P5T03")
    if report.get("acceptance_id") != S2PFT03_ACCEPTANCE_ID:
        errors.append("S2PFT03 city acceptance_id must be ACC-S2PFT03-CITIES")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PFT03 city status must be pass or blocked")
    for key in (
        "d3_full_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
        "v7_2_mail_or_schema_prerun",
        "special_zone_discovery_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PFT03 key-city coverage")
    city_records = report.get("city_records")
    if not isinstance(city_records, list):
        errors.append("S2PFT03 city_records must be a list")
        city_records = []
    observed_ids = set(report.get("city_ids_observed") or [])
    missing_ids = [city_id for city_id in S2PFT03_REQUIRED_CITY_IDS if city_id not in observed_ids]
    if missing_ids:
        errors.append("S2PFT03 missing city ids: " + ", ".join(missing_ids))
    for index, record in enumerate(city_records):
        if not isinstance(record, Mapping):
            errors.append(f"city_records[{index}] must be an object")
            continue
        if record.get("city_id") not in S2PFT03_REQUIRED_CITY_IDS:
            errors.append(f"city_records[{index}].city_id is not supported")
        if not record.get("city_name"):
            errors.append(f"city_records[{index}].city_name is required")
        if record.get("region_group") not in S2PFT03_ALLOWED_REGION_GROUPS:
            errors.append(f"city_records[{index}].region_group is not supported")
        if record.get("health_tier") not in S2PFT03_ALLOWED_HEALTH_TIERS:
            errors.append(f"city_records[{index}].health_tier is not supported")
        if not record.get("health_explanation"):
            errors.append(f"city_records[{index}].health_explanation is required")
        if not record.get("aliases"):
            errors.append(f"city_records[{index}].aliases is required")
        missing_roles = [
            role for role in S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES if role not in set(record.get("department_roles") or [])
        ]
        if missing_roles:
            errors.append(f"city_records[{index}] missing city roles: " + ", ".join(missing_roles))
        if record.get("authority_gate") != "pass":
            errors.append(f"city_records[{index}].authority_gate must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"city_records[{index}].metadata_only must be true")
        for field in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if record.get(field) is not False:
                errors.append(f"city_records[{index}].{field} must be false")
        if not record.get("official_domain") or not record.get("source_url") or not record.get("evidence_refs"):
            errors.append(f"city_records[{index}] requires official_domain, source_url, and evidence_refs")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PFT03 city report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_hk_mo_profile_gate",
            "city_coverage_gate",
            "city_alias_gate",
            "city_department_template_gate",
            "region_weight_gate",
            "health_tier_gate",
            "authority_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PFT03 city report requires {key}=pass")
        if report.get("s2pf_key_city_coverage_ready") is not True:
            errors.append("passing S2PFT03 city report requires s2pf_key_city_coverage_ready=true")
        if report.get("city_coverage_modeled") is not True:
            errors.append("passing S2PFT03 city report requires city_coverage_modeled=true")
    return errors


def build_s2pft04_special_zone_discovery_report(
    *,
    generated_at: str,
    key_city_coverage_report: Mapping[str, Any],
    zone_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build special-zone metadata discovery evidence without production inclusion."""

    upstream_errors = validate_s2pft03_key_city_coverage_report(key_city_coverage_report)
    upstream_gate = (
        "pass"
        if not upstream_errors
        and key_city_coverage_report.get("status") == "pass"
        and key_city_coverage_report.get("s2pf_key_city_coverage_ready") is True
        else "blocked"
    )
    zone_rows, row_errors = _s2pft04_zone_rows(zone_records)
    parent_city_ids = set(key_city_coverage_report.get("city_ids_observed") or S2PFT03_REQUIRED_CITY_IDS)
    coverage_gate = _s2pft04_zone_coverage_gate(zone_rows)
    authority_role_gate = _s2pft04_zone_authority_role_gate(zone_rows)
    type_policy_gate = _s2pft04_zone_type_policy_gate(zone_rows)
    parent_city_gate = _s2pft04_parent_city_gate(zone_rows, parent_city_ids=parent_city_ids)
    health_gate = _s2pft04_zone_health_gate(zone_rows)
    authority_gate = _s2pft04_zone_authority_gate(zone_rows)
    metadata_gate = _s2pft04_zone_metadata_gate(zone_rows)
    blocking_reasons = [
        *upstream_errors,
        *row_errors,
        *coverage_gate["blocking_reasons"],
        *authority_role_gate["blocking_reasons"],
        *type_policy_gate["blocking_reasons"],
        *parent_city_gate["blocking_reasons"],
        *health_gate["blocking_reasons"],
        *authority_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PFT04 requires passing S2PFT03 key-city coverage evidence")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == coverage_gate["status"]
        == authority_role_gate["status"]
        == type_policy_gate["status"]
        == parent_city_gate["status"]
        == health_gate["status"]
        == authority_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PFT04_SPECIAL_ZONE_MODEL_ID,
        "acceptance_id": S2PFT04_ACCEPTANCE_ID,
        "task_id": S2PFT04_TASK_ID,
        "legacy_task_id": S2PFT04_LEGACY_TASK_ID,
        "phase": "S2PF",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_key_city_coverage_gate": upstream_gate,
        "zone_coverage_gate": coverage_gate["status"],
        "zone_authority_role_gate": authority_role_gate["status"],
        "zone_type_policy_gate": type_policy_gate["status"],
        "parent_city_mapping_gate": parent_city_gate["status"],
        "health_tier_gate": health_gate["status"],
        "authority_gate": authority_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_zone_ids": list(S2PFT04_REQUIRED_ZONE_IDS),
        "required_zone_count": len(S2PFT04_REQUIRED_ZONE_IDS),
        "zone_ids_observed": coverage_gate["zone_ids_observed"],
        "zone_record_count": len(zone_rows),
        "required_zone_authority_roles": list(S2PFT04_REQUIRED_ZONE_AUTHORITY_ROLES),
        "allowed_zone_types": list(S2PFT04_ALLOWED_ZONE_TYPES),
        "zone_types_observed": type_policy_gate["zone_types_observed"],
        "allowed_policy_focus_areas": list(S2PFT04_ALLOWED_POLICY_FOCUS_AREAS),
        "policy_focus_areas_observed": type_policy_gate["policy_focus_areas_observed"],
        "allowed_health_tiers": list(S2PFT04_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": health_gate["health_tiers_observed"],
        "parent_city_ids_observed": parent_city_gate["parent_city_ids_observed"],
        "zone_records": zone_rows,
        "zone_coverage_summary": coverage_gate,
        "zone_authority_role_summary": authority_role_gate,
        "zone_type_policy_summary": type_policy_gate,
        "parent_city_mapping_summary": parent_city_gate,
        "health_tier_summary": health_gate,
        "authority_summary": authority_gate,
        "metadata_summary": metadata_gate,
        "s2pf_special_zone_discovery_ready": status == "pass",
        "d3_full_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "v7_2_mail_or_schema_prerun": False,
        "special_zone_discovery_modeled": status == "pass",
        "special_zone_discovery_enabled": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pft04_special_zone_discovery(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    key_city_coverage_report: Mapping[str, Any],
    zone_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PFT04 special-zone discovery evidence without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pft04-special-zone-discovery"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pft04_special_zone_discovery_report(
        generated_at=generated_at,
        key_city_coverage_report=key_city_coverage_report,
        zone_records=zone_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "special_zone_discovery_report_path": str(run_dir / "adp-s2pft04-special-zone-discovery-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pft04-special-zone-discovery-report.json", report)
        _write_json(state / S2PFT04_REPORT_FILENAME, report)
    return report


def validate_s2pft04_special_zone_discovery_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PFT04_SPECIAL_ZONE_MODEL_ID:
        errors.append("S2PFT04 zone model_id must be adp-s2pft04-special-zone-discovery-v1")
    if report.get("task_id") != S2PFT04_TASK_ID:
        errors.append("S2PFT04 zone task_id must be S2PFT04")
    if report.get("legacy_task_id") != S2PFT04_LEGACY_TASK_ID:
        errors.append("S2PFT04 zone legacy_task_id must be S2P5T04")
    if report.get("acceptance_id") != S2PFT04_ACCEPTANCE_ID:
        errors.append("S2PFT04 zone acceptance_id must be ACC-S2PFT04-ZONES")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PFT04 zone status must be pass or blocked")
    for key in (
        "d3_full_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
        "v7_2_mail_or_schema_prerun",
        "special_zone_discovery_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PFT04 special-zone discovery")
    zone_records = report.get("zone_records")
    if not isinstance(zone_records, list):
        errors.append("S2PFT04 zone_records must be a list")
        zone_records = []
    observed_ids = set(report.get("zone_ids_observed") or [])
    missing_ids = [zone_id for zone_id in S2PFT04_REQUIRED_ZONE_IDS if zone_id not in observed_ids]
    if missing_ids:
        errors.append("S2PFT04 missing zone ids: " + ", ".join(missing_ids))
    for index, record in enumerate(zone_records):
        if not isinstance(record, Mapping):
            errors.append(f"zone_records[{index}] must be an object")
            continue
        if record.get("zone_id") not in S2PFT04_REQUIRED_ZONE_IDS:
            errors.append(f"zone_records[{index}].zone_id is not supported")
        if not record.get("zone_name"):
            errors.append(f"zone_records[{index}].zone_name is required")
        if record.get("zone_type") not in S2PFT04_ALLOWED_ZONE_TYPES:
            errors.append(f"zone_records[{index}].zone_type is not supported")
        focus_areas = set(record.get("policy_focus_areas") or [])
        if not focus_areas or not focus_areas.issubset(set(S2PFT04_ALLOWED_POLICY_FOCUS_AREAS)):
            errors.append(f"zone_records[{index}].policy_focus_areas are required and must be supported")
        missing_roles = [
            role for role in S2PFT04_REQUIRED_ZONE_AUTHORITY_ROLES if role not in set(record.get("authority_roles") or [])
        ]
        if missing_roles:
            errors.append(f"zone_records[{index}] missing zone roles: " + ", ".join(missing_roles))
        if not record.get("parent_city_ids"):
            errors.append(f"zone_records[{index}].parent_city_ids is required")
        if record.get("health_tier") not in S2PFT04_ALLOWED_HEALTH_TIERS:
            errors.append(f"zone_records[{index}].health_tier is not supported")
        if not record.get("health_explanation"):
            errors.append(f"zone_records[{index}].health_explanation is required")
        if record.get("authority_gate") != "pass":
            errors.append(f"zone_records[{index}].authority_gate must be pass")
        if record.get("dedupe_gate") != "pass":
            errors.append(f"zone_records[{index}].dedupe_gate must be pass")
        if record.get("metadata_only") is not True:
            errors.append(f"zone_records[{index}].metadata_only must be true")
        for field in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if record.get(field) is not False:
                errors.append(f"zone_records[{index}].{field} must be false")
        if not record.get("official_domain") or not record.get("source_url") or not record.get("evidence_refs"):
            errors.append(f"zone_records[{index}] requires official_domain, source_url, and evidence_refs")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PFT04 zone report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_key_city_coverage_gate",
            "zone_coverage_gate",
            "zone_authority_role_gate",
            "zone_type_policy_gate",
            "parent_city_mapping_gate",
            "health_tier_gate",
            "authority_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PFT04 zone report requires {key}=pass")
        if report.get("s2pf_special_zone_discovery_ready") is not True:
            errors.append("passing S2PFT04 zone report requires s2pf_special_zone_discovery_ready=true")
        if report.get("special_zone_discovery_modeled") is not True:
            errors.append("passing S2PFT04 zone report requires special_zone_discovery_modeled=true")
    return errors


def build_s2pft05_d3_full_governance_qualification_report(
    *,
    generated_at: str,
    d3_readiness_review_report: Mapping[str, Any],
    provincial_template_coverage_report: Mapping[str, Any],
    hk_mo_profile_report: Mapping[str, Any],
    key_city_coverage_report: Mapping[str, Any],
    special_zone_discovery_report: Mapping[str, Any],
    governance_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build D3 full governance qualification evidence without production inclusion."""

    d3_errors = validate_s2pdt04_china_d3_readiness_review_report(d3_readiness_review_report)
    provincial_errors = validate_s2pft01_china_provincial_template_coverage_report(provincial_template_coverage_report)
    hk_mo_errors = validate_s2pft02_hk_mo_independent_profile_report(hk_mo_profile_report)
    city_errors = validate_s2pft03_key_city_coverage_report(key_city_coverage_report)
    zone_errors = validate_s2pft04_special_zone_discovery_report(special_zone_discovery_report)
    upstream_gate = (
        "pass"
        if not d3_errors
        and not provincial_errors
        and not hk_mo_errors
        and not city_errors
        and not zone_errors
        and d3_readiness_review_report.get("status") == "pass"
        and d3_readiness_review_report.get("d3_core_readiness_review_ready") is True
        and provincial_template_coverage_report.get("s2pf_provincial_template_coverage_ready") is True
        and hk_mo_profile_report.get("s2pf_hk_mo_profile_ready") is True
        and key_city_coverage_report.get("s2pf_key_city_coverage_ready") is True
        and special_zone_discovery_report.get("s2pf_special_zone_discovery_ready") is True
        else "blocked"
    )
    governance_rows, row_errors = _s2pft05_governance_rows(governance_records)
    component_gate = _s2pft05_component_gate(governance_rows)
    quota_gate = _s2pft05_quota_gate(governance_rows)
    health_gate = _s2pft05_health_balance_gate(governance_rows)
    elimination_gate = _s2pft05_elimination_gate(governance_rows)
    fallback_gate = _s2pft05_fallback_gate(governance_rows)
    replay_gate = _s2pft05_replay_gate(governance_rows)
    metadata_gate = _s2pft05_metadata_gate(governance_rows)
    blocking_reasons = [
        *d3_errors,
        *provincial_errors,
        *hk_mo_errors,
        *city_errors,
        *zone_errors,
        *row_errors,
        *component_gate["blocking_reasons"],
        *quota_gate["blocking_reasons"],
        *health_gate["blocking_reasons"],
        *elimination_gate["blocking_reasons"],
        *fallback_gate["blocking_reasons"],
        *replay_gate["blocking_reasons"],
        *metadata_gate["blocking_reasons"],
    ]
    if upstream_gate != "pass":
        blocking_reasons.append("S2PFT05 requires passing S2PDT04 and S2PFT01-S2PFT04 evidence reports")
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate
        == component_gate["status"]
        == quota_gate["status"]
        == health_gate["status"]
        == elimination_gate["status"]
        == fallback_gate["status"]
        == replay_gate["status"]
        == metadata_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PFT05_D3_FULL_GOVERNANCE_MODEL_ID,
        "acceptance_id": S2PFT05_ACCEPTANCE_ID,
        "task_id": S2PFT05_TASK_ID,
        "legacy_task_id": S2PFT05_LEGACY_TASK_ID,
        "phase": "S2PF",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_d3_readiness_gate": upstream_gate,
        "component_coverage_gate": component_gate["status"],
        "quota_balance_gate": quota_gate["status"],
        "health_balance_gate": health_gate["status"],
        "elimination_explanation_gate": elimination_gate["status"],
        "fallback_route_gate": fallback_gate["status"],
        "d3_full_replay_gate": replay_gate["status"],
        "metadata_only_gate": metadata_gate["status"],
        "required_components": list(S2PFT05_REQUIRED_COMPONENTS),
        "components_observed": component_gate["components_observed"],
        "required_quota_roles": list(S2PFT05_REQUIRED_QUOTA_ROLES),
        "quota_roles_observed": quota_gate["quota_roles_observed"],
        "required_governance_gates": list(S2PFT05_REQUIRED_GOVERNANCE_GATES),
        "required_replay_dates": S2PFT05_REQUIRED_REPLAY_DATES,
        "replay_dates_observed": replay_gate["replay_dates_observed"],
        "allowed_health_tiers": list(S2PFT05_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": health_gate["health_tiers_observed"],
        "governance_records": governance_rows,
        "governance_record_count": len(governance_rows),
        "component_summary": component_gate,
        "quota_summary": quota_gate,
        "health_summary": health_gate,
        "elimination_summary": elimination_gate,
        "fallback_summary": fallback_gate,
        "replay_summary": replay_gate,
        "metadata_summary": metadata_gate,
        "s2pf_d3_full_governance_qualification_ready": status == "pass",
        "d3_full_source_domain_qualified": status == "pass",
        "d3_full_source_domain_accepted": False,
        "formal_production_inclusion": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "schema_migration_allowed": False,
        "bulk_scraping_allowed": False,
        "pdf_download_enabled": False,
        "full_text_download_enabled": False,
        "paid_api_used": False,
        "paywall_bypass_allowed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "v7_2_mail_or_schema_prerun": False,
        "production_restore_executed": False,
        "production_schedule_enabled": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pft05_d3_full_governance_qualification(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    d3_readiness_review_report: Mapping[str, Any],
    provincial_template_coverage_report: Mapping[str, Any],
    hk_mo_profile_report: Mapping[str, Any],
    key_city_coverage_report: Mapping[str, Any],
    special_zone_discovery_report: Mapping[str, Any],
    governance_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PFT05 D3 full governance qualification without production inclusion."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pft05-d3-full-governance-qualification"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pft05_d3_full_governance_qualification_report(
        generated_at=generated_at,
        d3_readiness_review_report=d3_readiness_review_report,
        provincial_template_coverage_report=provincial_template_coverage_report,
        hk_mo_profile_report=hk_mo_profile_report,
        key_city_coverage_report=key_city_coverage_report,
        special_zone_discovery_report=special_zone_discovery_report,
        governance_records=governance_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "d3_full_governance_qualification_report_path": str(
                run_dir / "adp-s2pft05-d3-full-governance-qualification-report.json"
            ),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pft05-d3-full-governance-qualification-report.json", report)
        _write_json(state / S2PFT05_REPORT_FILENAME, report)
    return report


def validate_s2pft05_d3_full_governance_qualification_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PFT05_D3_FULL_GOVERNANCE_MODEL_ID:
        errors.append("S2PFT05 D3 governance model_id must be adp-s2pft05-d3-full-governance-qualification-v1")
    if report.get("task_id") != S2PFT05_TASK_ID:
        errors.append("S2PFT05 D3 governance task_id must be S2PFT05")
    if report.get("legacy_task_id") != S2PFT05_LEGACY_TASK_ID:
        errors.append("S2PFT05 D3 governance legacy_task_id must be S2P5T05")
    if report.get("acceptance_id") != S2PFT05_ACCEPTANCE_ID:
        errors.append("S2PFT05 D3 governance acceptance_id must be ACC-S2PFT05-D3-FULL")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PFT05 D3 governance status must be pass or blocked")
    for key in (
        "d3_full_source_domain_accepted",
        "formal_production_inclusion",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "bulk_scraping_allowed",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
        "v7_2_mail_or_schema_prerun",
        "production_restore_executed",
        "production_schedule_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PFT05 D3 full governance qualification")
    records = report.get("governance_records")
    if not isinstance(records, list):
        errors.append("S2PFT05 governance_records must be a list")
        records = []
    observed_components = set(report.get("components_observed") or [])
    missing_components = [component for component in S2PFT05_REQUIRED_COMPONENTS if component not in observed_components]
    if missing_components:
        errors.append("S2PFT05 missing components: " + ", ".join(missing_components))
    observed_quota_roles = set(report.get("quota_roles_observed") or [])
    missing_quota_roles = [role for role in S2PFT05_REQUIRED_QUOTA_ROLES if role not in observed_quota_roles]
    if missing_quota_roles:
        errors.append("S2PFT05 missing quota roles: " + ", ".join(missing_quota_roles))
    if len(set(report.get("replay_dates_observed") or [])) < S2PFT05_REQUIRED_REPLAY_DATES:
        errors.append("S2PFT05 full D3 governance requires at least 30 replay dates")
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"governance_records[{index}] must be an object")
            continue
        if record.get("component_id") not in S2PFT05_REQUIRED_COMPONENTS:
            errors.append(f"governance_records[{index}].component_id is not supported")
        quota_role = record.get("quota_role")
        if quota_role not in S2PFT05_REQUIRED_QUOTA_ROLES:
            errors.append(f"governance_records[{index}].quota_role is not supported")
        for field in ("component_name", "quota_explanation", "elimination_explanation", "fallback_route", "evidence_refs"):
            if not record.get(field):
                errors.append(f"governance_records[{index}].{field} is required")
        if record.get("quota_gate") != "pass":
            errors.append(f"governance_records[{index}].quota_gate must be pass")
        if record.get("health_tier") not in S2PFT05_ALLOWED_HEALTH_TIERS:
            errors.append(f"governance_records[{index}].health_tier is not supported")
        if not record.get("health_explanation"):
            errors.append(f"governance_records[{index}].health_explanation is required")
        if record.get("fallback_gate") != "pass":
            errors.append(f"governance_records[{index}].fallback_gate must be pass")
        replay_dates = record.get("replay_dates")
        if not replay_dates:
            errors.append(f"governance_records[{index}].replay_dates is required")
        else:
            for replay_date in replay_dates:
                if not _is_iso_date(str(replay_date)):
                    errors.append(f"governance_records[{index}].replay_dates must contain YYYY-MM-DD values")
                    break
        if record.get("metadata_only") is not True:
            errors.append(f"governance_records[{index}].metadata_only must be true")
        for field in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if record.get(field) is not False:
                errors.append(f"governance_records[{index}].{field} must be false")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PFT05 D3 governance report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "upstream_d3_readiness_gate",
            "component_coverage_gate",
            "quota_balance_gate",
            "health_balance_gate",
            "elimination_explanation_gate",
            "fallback_route_gate",
            "d3_full_replay_gate",
            "metadata_only_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PFT05 D3 governance report requires {key}=pass")
        if report.get("s2pf_d3_full_governance_qualification_ready") is not True:
            errors.append("passing S2PFT05 D3 governance report requires s2pf_d3_full_governance_qualification_ready=true")
        if report.get("d3_full_source_domain_qualified") is not True:
            errors.append("passing S2PFT05 D3 governance report requires d3_full_source_domain_qualified=true")
    return errors


def build_s2pgt01_evidence_packet_v2_compatibility_report(
    *,
    generated_at: str,
    source_domain_reports: Sequence[Mapping[str, Any]],
    packet_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a private EvidencePacket V2 compatibility report without schema migration."""

    domain_rows, domain_errors = _s2pgt01_domain_rows(source_domain_reports)
    packet_rows, packet_errors = _s2pgt01_packet_rows(packet_records)
    domain_gate = _s2pgt01_domain_gate(domain_rows)
    packet_gate = _s2pgt01_packet_gate(packet_rows)
    level_gate = _s2pgt01_evidence_level_gate(packet_rows)
    compatibility_gate = _s2pgt01_compatibility_gate(packet_rows)
    side_effect_gate = _s2pgt01_no_side_effect_gate(packet_rows)
    blocking_reasons = [
        *domain_errors,
        *packet_errors,
        *domain_gate["blocking_reasons"],
        *packet_gate["blocking_reasons"],
        *level_gate["blocking_reasons"],
        *compatibility_gate["blocking_reasons"],
        *side_effect_gate["blocking_reasons"],
    ]
    status = (
        "pass"
        if not blocking_reasons
        and domain_gate["status"]
        == packet_gate["status"]
        == level_gate["status"]
        == compatibility_gate["status"]
        == side_effect_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PGT01_EVIDENCE_PACKET_MODEL_ID,
        "acceptance_id": S2PGT01_ACCEPTANCE_ID,
        "task_id": S2PGT01_TASK_ID,
        "phase": "S2PG",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "packet_version": S2PGT01_PACKET_VERSION,
        "required_source_domains": list(S2PGT01_REQUIRED_SOURCE_DOMAINS),
        "source_domains_observed": domain_gate["source_domains_observed"],
        "required_evidence_levels": list(S2PGT01_REQUIRED_EVIDENCE_LEVELS),
        "evidence_levels_observed": level_gate["evidence_levels_observed"],
        "required_packet_fields": list(S2PGT01_REQUIRED_PACKET_FIELDS),
        "source_domain_gate": domain_gate["status"],
        "packet_shape_gate": packet_gate["status"],
        "evidence_level_gate": level_gate["status"],
        "old_arxiv_compatibility_gate": compatibility_gate["status"],
        "no_side_effect_gate": side_effect_gate["status"],
        "source_domain_reports": domain_rows,
        "evidence_packets": packet_rows,
        "evidence_packet_count": len(packet_rows),
        "schema_migration_required": False,
        "public_schema_changed": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "v7_2_contract_files_changed": False,
        "s2pgt01_evidence_packet_v2_compatibility_ready": status == "pass",
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pgt01_evidence_packet_v2_compatibility(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    source_domain_reports: Sequence[Mapping[str, Any]],
    packet_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PGT01 EvidencePacket V2 compatibility evidence without side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pgt01-evidence-packet-v2-compatibility"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pgt01_evidence_packet_v2_compatibility_report(
        generated_at=generated_at,
        source_domain_reports=source_domain_reports,
        packet_records=packet_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "evidence_packet_v2_compatibility_report_path": str(
                run_dir / "adp-s2pgt01-evidence-packet-v2-compatibility-report.json"
            ),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pgt01-evidence-packet-v2-compatibility-report.json", report)
        _write_json(state / S2PGT01_REPORT_FILENAME, report)
    return report


def validate_s2pgt01_evidence_packet_v2_compatibility_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PGT01_EVIDENCE_PACKET_MODEL_ID:
        errors.append("S2PGT01 model_id must be adp-s2pgt01-evidence-packet-v2-compatibility-v1")
    if report.get("task_id") != S2PGT01_TASK_ID:
        errors.append("S2PGT01 task_id must be S2PGT01")
    if report.get("acceptance_id") != S2PGT01_ACCEPTANCE_ID:
        errors.append("S2PGT01 acceptance_id must be ACC-S2PGT01-EVIDENCE-V2")
    if report.get("packet_version") != S2PGT01_PACKET_VERSION:
        errors.append("S2PGT01 packet_version must be EvidencePacketV2")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PGT01 status must be pass or blocked")
    for key in (
        "schema_migration_required",
        "public_schema_changed",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "production_affected",
        "real_smtp_sent",
        "v7_2_contract_files_changed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PGT01 compatibility")
    domains = set(report.get("source_domains_observed") or [])
    missing_domains = [domain for domain in S2PGT01_REQUIRED_SOURCE_DOMAINS if domain not in domains]
    if missing_domains:
        errors.append("S2PGT01 missing source domains: " + ", ".join(missing_domains))
    levels = set(report.get("evidence_levels_observed") or [])
    missing_levels = [level for level in S2PGT01_REQUIRED_EVIDENCE_LEVELS if level not in levels]
    if missing_levels:
        errors.append("S2PGT01 missing evidence levels: " + ", ".join(missing_levels))
    packets = report.get("evidence_packets")
    if not isinstance(packets, list) or not packets:
        errors.append("S2PGT01 evidence_packets must be a non-empty list")
        packets = []
    for index, packet in enumerate(packets):
        if not isinstance(packet, Mapping):
            errors.append(f"evidence_packets[{index}] must be an object")
            continue
        for field in S2PGT01_REQUIRED_PACKET_FIELDS:
            if packet.get(field) in (None, "", []):
                errors.append(f"evidence_packets[{index}].{field} is required")
        if packet.get("packet_version") != S2PGT01_PACKET_VERSION:
            errors.append(f"evidence_packets[{index}].packet_version must be EvidencePacketV2")
        if packet.get("source_domain") not in S2PGT01_REQUIRED_SOURCE_DOMAINS:
            errors.append(f"evidence_packets[{index}].source_domain is not supported")
        evidence_levels = set(packet.get("evidence_levels_available") or [])
        unsupported = sorted(evidence_levels - set(S2PGT01_REQUIRED_EVIDENCE_LEVELS))
        if unsupported:
            errors.append(f"evidence_packets[{index}].evidence_levels_available has unsupported levels: {', '.join(unsupported)}")
        if "metadata" not in evidence_levels:
            errors.append(f"evidence_packets[{index}].evidence_levels_available must include metadata")
        for key in ("schema_migration_required", "production_affected"):
            if packet.get(key) is not False:
                errors.append(f"evidence_packets[{index}].{key} must be false")
        if packet.get("source_domain") == "d1_research_preprint" and packet.get("old_arxiv_compatible") is not True:
            errors.append(f"evidence_packets[{index}].old_arxiv_compatible must be true for D1/arXiv compatibility")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PGT01 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "source_domain_gate",
            "packet_shape_gate",
            "evidence_level_gate",
            "old_arxiv_compatibility_gate",
            "no_side_effect_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PGT01 report requires {key}=pass")
        if report.get("s2pgt01_evidence_packet_v2_compatibility_ready") is not True:
            errors.append("passing S2PGT01 report requires s2pgt01_evidence_packet_v2_compatibility_ready=true")
    return errors


def build_s2pgt02_knowledge_graph_spine_report(
    *,
    generated_at: str,
    evidence_packet_report: Mapping[str, Any],
    identity_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a private cross-source identity and relation graph report."""

    packet_errors = validate_s2pgt01_evidence_packet_v2_compatibility_report(evidence_packet_report)
    identity_rows, identifier_index, identity_errors = _s2pgt02_identity_rows(identity_records)
    canonical_entities, canonical_lookup, canonical_errors = _s2pgt02_canonical_entities(identity_rows)
    relation_rows, relation_errors = _s2pgt02_relation_rows(relation_records, canonical_lookup)
    identifier_gate = _s2pgt02_identifier_gate(identity_rows)
    canonical_gate = _s2pgt02_canonical_gate(canonical_entities, canonical_errors)
    relation_gate = _s2pgt02_relation_evidence_gate(relation_rows)
    idempotent_gate = _s2pgt02_idempotent_update_gate(canonical_entities, relation_rows)
    side_effect_gate = _s2pgt02_no_side_effect_gate([*identity_rows, *relation_rows])
    graph_state_hash = _s2pgt02_graph_state_hash(canonical_entities, relation_rows)
    blocking_reasons = [
        *(f"S2PGT01: {error}" for error in packet_errors),
        *identity_errors,
        *canonical_errors,
        *relation_errors,
        *identifier_gate["blocking_reasons"],
        *canonical_gate["blocking_reasons"],
        *relation_gate["blocking_reasons"],
        *idempotent_gate["blocking_reasons"],
        *side_effect_gate["blocking_reasons"],
    ]
    if evidence_packet_report.get("status") != "pass":
        blocking_reasons.append("S2PGT02 requires passing S2PGT01 EvidencePacket V2 compatibility evidence")
    status = (
        "pass"
        if not blocking_reasons
        and identifier_gate["status"]
        == canonical_gate["status"]
        == relation_gate["status"]
        == idempotent_gate["status"]
        == side_effect_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PGT02_KNOWLEDGE_GRAPH_MODEL_ID,
        "acceptance_id": S2PGT02_ACCEPTANCE_ID,
        "task_id": S2PGT02_TASK_ID,
        "legacy_task_id": S2PGT02_LEGACY_TASK_ID,
        "phase": "S2PG",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_s2pgt01_status": evidence_packet_report.get("status"),
        "required_identifier_types": list(S2PGT02_REQUIRED_IDENTIFIER_TYPES),
        "identifier_types_observed": identifier_gate["identifier_types_observed"],
        "allowed_relation_types": list(S2PGT02_ALLOWED_RELATION_TYPES),
        "required_relation_fields": list(S2PGT02_REQUIRED_RELATION_FIELDS),
        "required_gates": list(S2PGT02_REQUIRED_GATES),
        "identifier_coverage_gate": identifier_gate["status"],
        "canonical_dedupe_gate": canonical_gate["status"],
        "relation_evidence_gate": relation_gate["status"],
        "idempotent_update_gate": idempotent_gate["status"],
        "no_side_effect_gate": side_effect_gate["status"],
        "duplicate_canonical_count": canonical_gate["duplicate_canonical_count"],
        "relation_count": len(relation_rows),
        "canonical_entity_count": len(canonical_entities),
        "identifier_index": identifier_index,
        "canonical_entities": canonical_entities,
        "knowledge_graph_relations": relation_rows,
        "graph_state_hash": graph_state_hash,
        "idempotent_update_hash": idempotent_gate["idempotent_update_hash"],
        "schema_migration_required": False,
        "public_schema_changed": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "v7_2_contract_files_changed": False,
        "s2pgt02_knowledge_graph_spine_ready": status == "pass",
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pgt02_knowledge_graph_spine(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    evidence_packet_report: Mapping[str, Any],
    identity_records: Sequence[Mapping[str, Any]],
    relation_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PGT02 private knowledge-graph evidence without side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pgt02-knowledge-graph-spine"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pgt02_knowledge_graph_spine_report(
        generated_at=generated_at,
        evidence_packet_report=evidence_packet_report,
        identity_records=identity_records,
        relation_records=relation_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "knowledge_graph_spine_report_path": str(run_dir / "adp-s2pgt02-knowledge-graph-spine-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pgt02-knowledge-graph-spine-report.json", report)
        _write_json(state / S2PGT02_REPORT_FILENAME, report)
    return report


def validate_s2pgt02_knowledge_graph_spine_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PGT02_KNOWLEDGE_GRAPH_MODEL_ID:
        errors.append("S2PGT02 model_id must be adp-s2pgt02-knowledge-graph-spine-v1")
    if report.get("task_id") != S2PGT02_TASK_ID:
        errors.append("S2PGT02 task_id must be S2PGT02")
    if report.get("legacy_task_id") != S2PGT02_LEGACY_TASK_ID:
        errors.append("S2PGT02 legacy_task_id must be S2P6T01")
    if report.get("acceptance_id") != S2PGT02_ACCEPTANCE_ID:
        errors.append("S2PGT02 acceptance_id must be ACC-S2PGT02-KG")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PGT02 status must be pass or blocked")
    for key in (
        "schema_migration_required",
        "public_schema_changed",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "production_affected",
        "real_smtp_sent",
        "v7_2_contract_files_changed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PGT02 knowledge graph spine")
    observed = set(report.get("identifier_types_observed") or [])
    missing = [identifier_type for identifier_type in S2PGT02_REQUIRED_IDENTIFIER_TYPES if identifier_type not in observed]
    if missing:
        errors.append("S2PGT02 missing identifier types: " + ", ".join(missing))
    entities = report.get("canonical_entities")
    if not isinstance(entities, list) or not entities:
        errors.append("S2PGT02 canonical_entities must be a non-empty list")
        entities = []
    entity_ids = set()
    for index, entity in enumerate(entities):
        if not isinstance(entity, Mapping):
            errors.append(f"canonical_entities[{index}] must be an object")
            continue
        canonical_id = str(entity.get("canonical_id") or "")
        if not canonical_id:
            errors.append(f"canonical_entities[{index}].canonical_id is required")
        if canonical_id in entity_ids:
            errors.append(f"canonical_entities[{index}].canonical_id must be unique")
        entity_ids.add(canonical_id)
        if not entity.get("identifiers"):
            errors.append(f"canonical_entities[{index}].identifiers is required")
        if not entity.get("evidence_refs"):
            errors.append(f"canonical_entities[{index}].evidence_refs is required")
    relations = report.get("knowledge_graph_relations")
    if not isinstance(relations, list) or not relations:
        errors.append("S2PGT02 knowledge_graph_relations must be a non-empty list")
        relations = []
    relation_ids = set()
    idempotency_keys = set()
    for index, relation in enumerate(relations):
        if not isinstance(relation, Mapping):
            errors.append(f"knowledge_graph_relations[{index}] must be an object")
            continue
        for field in S2PGT02_REQUIRED_RELATION_FIELDS:
            if relation.get(field) in (None, "", []):
                errors.append(f"knowledge_graph_relations[{index}].{field} is required")
        if relation.get("relation_type") not in S2PGT02_ALLOWED_RELATION_TYPES:
            errors.append(f"knowledge_graph_relations[{index}].relation_type is not supported")
        if relation.get("source_canonical_id") not in entity_ids:
            errors.append(f"knowledge_graph_relations[{index}].source_canonical_id must exist")
        if relation.get("target_canonical_id") not in entity_ids:
            errors.append(f"knowledge_graph_relations[{index}].target_canonical_id must exist")
        relation_id = str(relation.get("relation_id") or "")
        if relation_id in relation_ids:
            errors.append(f"knowledge_graph_relations[{index}].relation_id must be unique")
        relation_ids.add(relation_id)
        idempotency_key = str(relation.get("idempotency_key") or "")
        if idempotency_key in idempotency_keys:
            errors.append(f"knowledge_graph_relations[{index}].idempotency_key must be unique")
        idempotency_keys.add(idempotency_key)
    if report.get("duplicate_canonical_count") != 0:
        errors.append("S2PGT02 duplicate_canonical_count must be 0")
    expected_hash = _s2pgt02_graph_state_hash(entities, relations)
    if report.get("graph_state_hash") != expected_hash:
        errors.append("S2PGT02 graph_state_hash must match canonical entities and relations")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PGT02 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in (
            "identifier_coverage_gate",
            "canonical_dedupe_gate",
            "relation_evidence_gate",
            "idempotent_update_gate",
            "no_side_effect_gate",
        ):
            if report.get(key) != "pass":
                errors.append(f"passing S2PGT02 report requires {key}=pass")
        if report.get("s2pgt02_knowledge_graph_spine_ready") is not True:
                errors.append("passing S2PGT02 report requires s2pgt02_knowledge_graph_spine_ready=true")
    return errors


def build_s2pgt03_source_board_routing_report(
    *,
    generated_at: str,
    evidence_packet_report: Mapping[str, Any],
    route_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build private D1-D4 to B1-B6 multi-label routing evidence."""

    packet_errors = validate_s2pgt01_evidence_packet_v2_compatibility_report(evidence_packet_report)
    packet_index = _s2pgt03_packet_index(evidence_packet_report.get("evidence_packets") or [])
    route_rows, route_errors = _s2pgt03_route_rows(route_records, packet_index)
    source_domain_gate = _s2pgt03_source_domain_coverage_gate(route_rows)
    primary_gate = _s2pgt03_primary_board_coverage_gate(route_rows)
    cross_gate = _s2pgt03_cross_cutting_board_coverage_gate(route_rows)
    reason_gate = _s2pgt03_route_reason_gate(route_rows)
    side_effect_gate = _s2pgt03_no_side_effect_gate(route_rows)
    routing_state_hash = _s2pgt03_routing_state_hash(route_rows)
    blocking_reasons = [
        *(f"S2PGT01: {error}" for error in packet_errors),
        *route_errors,
        *source_domain_gate["blocking_reasons"],
        *primary_gate["blocking_reasons"],
        *cross_gate["blocking_reasons"],
        *reason_gate["blocking_reasons"],
        *side_effect_gate["blocking_reasons"],
    ]
    if evidence_packet_report.get("status") != "pass":
        blocking_reasons.append("S2PGT03 requires passing S2PGT01 EvidencePacket V2 compatibility evidence")
    status = (
        "pass"
        if not blocking_reasons
        and source_domain_gate["status"]
        == primary_gate["status"]
        == cross_gate["status"]
        == reason_gate["status"]
        == side_effect_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PGT03_ROUTING_MODEL_ID,
        "acceptance_id": S2PGT03_ACCEPTANCE_ID,
        "task_id": S2PGT03_TASK_ID,
        "phase": "S2PG",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_s2pgt01_status": evidence_packet_report.get("status"),
        "required_source_domains": list(S2PGT03_REQUIRED_SOURCE_DOMAINS),
        "source_domains_observed": source_domain_gate["source_domains_observed"],
        "required_primary_boards": list(S2PGT03_REQUIRED_PRIMARY_BOARDS),
        "primary_boards_observed": primary_gate["primary_boards_observed"],
        "required_cross_cutting_boards": list(S2PGT03_REQUIRED_CROSS_CUTTING_BOARDS),
        "cross_cutting_boards_observed": cross_gate["cross_cutting_boards_observed"],
        "allowed_reason_codes": list(S2PGT03_ALLOWED_REASON_CODES),
        "required_route_fields": list(S2PGT03_REQUIRED_ROUTE_FIELDS),
        "required_gates": list(S2PGT03_REQUIRED_GATES),
        "source_domain_board_rules": _s2pgt03_serializable_board_rules(),
        "source_domain_coverage_gate": source_domain_gate["status"],
        "primary_board_coverage_gate": primary_gate["status"],
        "cross_cutting_board_coverage_gate": cross_gate["status"],
        "route_reason_gate": reason_gate["status"],
        "no_side_effect_gate": side_effect_gate["status"],
        "route_count": len(route_rows),
        "routed_source_ids": sorted({str(row.get("source_id")) for row in route_rows if row.get("source_id")}),
        "routing_records": route_rows,
        "routing_state_hash": routing_state_hash,
        "schema_migration_required": False,
        "public_schema_changed": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "v7_2_contract_files_changed": False,
        "s2pgt03_source_board_routing_ready": status == "pass",
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pgt03_source_board_routing(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    evidence_packet_report: Mapping[str, Any],
    route_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PGT03 private route evidence without production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pgt03-source-board-routing"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pgt03_source_board_routing_report(
        generated_at=generated_at,
        evidence_packet_report=evidence_packet_report,
        route_records=route_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "source_board_routing_report_path": str(run_dir / "adp-s2pgt03-source-board-routing-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pgt03-source-board-routing-report.json", report)
        _write_json(state / S2PGT03_REPORT_FILENAME, report)
    return report


def validate_s2pgt03_source_board_routing_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PGT03_ROUTING_MODEL_ID:
        errors.append("S2PGT03 model_id must be adp-s2pgt03-source-board-routing-v1")
    if report.get("task_id") != S2PGT03_TASK_ID:
        errors.append("S2PGT03 task_id must be S2PGT03")
    if report.get("acceptance_id") != S2PGT03_ACCEPTANCE_ID:
        errors.append("S2PGT03 acceptance_id must be ACC-S2PGT03-ROUTING")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PGT03 status must be pass or blocked")
    for key in (
        "schema_migration_required",
        "public_schema_changed",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "production_affected",
        "real_smtp_sent",
        "v7_2_contract_files_changed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PGT03 routing")
    domains = set(report.get("source_domains_observed") or [])
    missing_domains = [domain for domain in S2PGT03_REQUIRED_SOURCE_DOMAINS if domain not in domains]
    if missing_domains:
        errors.append("S2PGT03 missing source domains: " + ", ".join(missing_domains))
    primary_boards = set(report.get("primary_boards_observed") or [])
    missing_primary = [board for board in S2PGT03_REQUIRED_PRIMARY_BOARDS if board not in primary_boards]
    if missing_primary:
        errors.append("S2PGT03 missing primary boards: " + ", ".join(missing_primary))
    cross_boards = set(report.get("cross_cutting_boards_observed") or [])
    missing_cross = [board for board in S2PGT03_REQUIRED_CROSS_CUTTING_BOARDS if board not in cross_boards]
    if missing_cross:
        errors.append("S2PGT03 missing cross-cutting boards: " + ", ".join(missing_cross))
    routes = report.get("routing_records")
    if not isinstance(routes, list) or not routes:
        errors.append("S2PGT03 routing_records must be a non-empty list")
        routes = []
    route_ids: set[str] = set()
    for index, route in enumerate(routes):
        if not isinstance(route, Mapping):
            errors.append(f"routing_records[{index}] must be an object")
            continue
        for field in S2PGT03_REQUIRED_ROUTE_FIELDS:
            if route.get(field) in (None, "", []):
                errors.append(f"routing_records[{index}].{field} is required")
        route_id = str(route.get("route_id") or "")
        if route_id in route_ids:
            errors.append(f"routing_records[{index}].route_id must be unique")
        route_ids.add(route_id)
        source_domain = str(route.get("source_domain") or "")
        allowed = _s2pgt03_allowed_boards_for_source_domain(source_domain)
        for board in route.get("primary_boards") or []:
            if board not in S2PGT03_REQUIRED_PRIMARY_BOARDS:
                errors.append(f"routing_records[{index}].primary_boards contains unsupported board {board}")
            if board not in allowed:
                errors.append(f"routing_records[{index}].primary_boards contains board {board} outside source-domain mapping")
        for board in route.get("cross_cutting_boards") or []:
            if board not in S2PGT03_REQUIRED_CROSS_CUTTING_BOARDS:
                errors.append(f"routing_records[{index}].cross_cutting_boards contains unsupported board {board}")
        for reason_code in route.get("reason_codes") or []:
            if reason_code not in S2PGT03_ALLOWED_REASON_CODES:
                errors.append(f"routing_records[{index}].reason_codes contains unsupported reason {reason_code}")
    if report.get("routing_state_hash") != _s2pgt03_routing_state_hash(routes):
        errors.append("S2PGT03 routing_state_hash must match routing_records")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PGT03 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in S2PGT03_REQUIRED_GATES:
            if report.get(key) != "pass":
                errors.append(f"passing S2PGT03 report requires {key}=pass")
        if report.get("s2pgt03_source_board_routing_ready") is not True:
            errors.append("passing S2PGT03 report requires s2pgt03_source_board_routing_ready=true")
    return errors


def build_s2pgt04_delta_resonance_report(
    *,
    generated_at: str,
    routing_report: Mapping[str, Any],
    delta_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build private support/refute/frontier delta and resonance evidence."""

    routing_errors = validate_s2pgt03_source_board_routing_report(routing_report)
    route_index = _s2pgt04_route_index(routing_report.get("routing_records") or [])
    delta_rows, delta_errors = _s2pgt04_delta_rows(delta_records, route_index)
    upstream_gate = _s2pgt04_upstream_routing_gate(routing_report, routing_errors)
    delta_type_gate = _s2pgt04_delta_type_coverage_gate(delta_rows)
    support_refute_gate = _s2pgt04_support_refute_gate(delta_rows)
    resonance_group_gate = _s2pgt04_resonance_group_gate(delta_rows)
    reason_gate = _s2pgt04_delta_reason_gate(delta_rows)
    side_effect_gate = _s2pgt04_no_side_effect_gate(delta_rows)
    resonance_state_hash = _s2pgt04_resonance_state_hash(delta_rows)
    blocking_reasons = [
        *upstream_gate["blocking_reasons"],
        *delta_errors,
        *delta_type_gate["blocking_reasons"],
        *support_refute_gate["blocking_reasons"],
        *resonance_group_gate["blocking_reasons"],
        *reason_gate["blocking_reasons"],
        *side_effect_gate["blocking_reasons"],
    ]
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate["status"]
        == delta_type_gate["status"]
        == support_refute_gate["status"]
        == resonance_group_gate["status"]
        == reason_gate["status"]
        == side_effect_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PGT04_DELTA_RESONANCE_MODEL_ID,
        "acceptance_id": S2PGT04_ACCEPTANCE_ID,
        "task_id": S2PGT04_TASK_ID,
        "phase": "S2PG",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_s2pgt03_status": routing_report.get("status"),
        "required_delta_types": list(S2PGT04_REQUIRED_DELTA_TYPES),
        "delta_types_observed": delta_type_gate["delta_types_observed"],
        "required_resonance_groups": list(S2PGT04_REQUIRED_RESONANCE_GROUPS),
        "resonance_groups_observed": resonance_group_gate["resonance_groups_observed"],
        "allowed_support_statuses": list(S2PGT04_ALLOWED_SUPPORT_STATUSES),
        "support_statuses_observed": support_refute_gate["support_statuses_observed"],
        "required_delta_fields": list(S2PGT04_REQUIRED_DELTA_FIELDS),
        "required_gates": list(S2PGT04_REQUIRED_GATES),
        "upstream_routing_gate": upstream_gate["status"],
        "delta_type_coverage_gate": delta_type_gate["status"],
        "support_refute_gate": support_refute_gate["status"],
        "resonance_group_gate": resonance_group_gate["status"],
        "delta_reason_gate": reason_gate["status"],
        "no_side_effect_gate": side_effect_gate["status"],
        "delta_count": len(delta_rows),
        "resonance_links": _s2pgt04_resonance_links(delta_rows),
        "delta_records": delta_rows,
        "resonance_state_hash": resonance_state_hash,
        "schema_migration_required": False,
        "public_schema_changed": False,
        "queue_mutation_allowed": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "v7_2_contract_files_changed": False,
        "email_frontstage_changed": False,
        "s2pgt04_delta_resonance_ready": status == "pass",
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pgt04_delta_resonance(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    routing_report: Mapping[str, Any],
    delta_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PGT04 private delta/resonance evidence without side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pgt04-delta-resonance"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pgt04_delta_resonance_report(
        generated_at=generated_at,
        routing_report=routing_report,
        delta_records=delta_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "delta_resonance_report_path": str(run_dir / "adp-s2pgt04-delta-resonance-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pgt04-delta-resonance-report.json", report)
        _write_json(state / S2PGT04_REPORT_FILENAME, report)
    return report


def validate_s2pgt04_delta_resonance_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PGT04_DELTA_RESONANCE_MODEL_ID:
        errors.append("S2PGT04 model_id must be adp-s2pgt04-delta-resonance-v1")
    if report.get("task_id") != S2PGT04_TASK_ID:
        errors.append("S2PGT04 task_id must be S2PGT04")
    if report.get("acceptance_id") != S2PGT04_ACCEPTANCE_ID:
        errors.append("S2PGT04 acceptance_id must be ACC-S2PGT04-DELTA-RESONANCE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PGT04 status must be pass or blocked")
    for key in (
        "schema_migration_required",
        "public_schema_changed",
        "queue_mutation_allowed",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "production_affected",
        "real_smtp_sent",
        "v7_2_contract_files_changed",
        "email_frontstage_changed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PGT04 delta resonance")
    delta_types = set(report.get("delta_types_observed") or [])
    missing_delta_types = [delta_type for delta_type in S2PGT04_REQUIRED_DELTA_TYPES if delta_type not in delta_types]
    if missing_delta_types:
        errors.append("S2PGT04 missing delta types: " + ", ".join(missing_delta_types))
    groups = set(report.get("resonance_groups_observed") or [])
    missing_groups = [group for group in S2PGT04_REQUIRED_RESONANCE_GROUPS if group not in groups]
    if missing_groups:
        errors.append("S2PGT04 missing resonance groups: " + ", ".join(missing_groups))
    support_statuses = set(report.get("support_statuses_observed") or [])
    if "supported" not in support_statuses or "refuted" not in support_statuses:
        errors.append("S2PGT04 requires both supported and refuted support statuses")
    deltas = report.get("delta_records")
    if not isinstance(deltas, list) or not deltas:
        errors.append("S2PGT04 delta_records must be a non-empty list")
        deltas = []
    delta_ids: set[str] = set()
    for index, delta in enumerate(deltas):
        if not isinstance(delta, Mapping):
            errors.append(f"delta_records[{index}] must be an object")
            continue
        for field in S2PGT04_REQUIRED_DELTA_FIELDS:
            if delta.get(field) in (None, "", []):
                errors.append(f"delta_records[{index}].{field} is required")
        delta_id = str(delta.get("delta_id") or "")
        if delta_id in delta_ids:
            errors.append(f"delta_records[{index}].delta_id must be unique")
        delta_ids.add(delta_id)
        if delta.get("delta_type") not in S2PGT04_REQUIRED_DELTA_TYPES:
            errors.append(f"delta_records[{index}].delta_type is not supported")
        if delta.get("resonance_group") not in S2PGT04_REQUIRED_RESONANCE_GROUPS:
            errors.append(f"delta_records[{index}].resonance_group is not supported")
        if delta.get("support_status") not in S2PGT04_ALLOWED_SUPPORT_STATUSES:
            errors.append(f"delta_records[{index}].support_status is not supported")
        strength = delta.get("signal_strength")
        if not isinstance(strength, (int, float)) or isinstance(strength, bool) or not 0 <= float(strength) <= 1:
            errors.append(f"delta_records[{index}].signal_strength must be between 0 and 1")
    if report.get("resonance_state_hash") != _s2pgt04_resonance_state_hash(deltas):
        errors.append("S2PGT04 resonance_state_hash must match delta_records")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PGT04 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in S2PGT04_REQUIRED_GATES:
            if report.get(key) != "pass":
                errors.append(f"passing S2PGT04 report requires {key}=pass")
        if report.get("s2pgt04_delta_resonance_ready") is not True:
            errors.append("passing S2PGT04 report requires s2pgt04_delta_resonance_ready=true")
    return errors


def build_s2pgt05_cross_board_calibration_report(
    *,
    generated_at: str,
    delta_resonance_report: Mapping[str, Any],
    queue_candidate_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build private cross-board calibration and explainable queue evidence."""

    delta_errors = validate_s2pgt04_delta_resonance_report(delta_resonance_report)
    delta_index = _s2pgt05_delta_index(delta_resonance_report.get("delta_records") or [])
    candidate_rows, candidate_errors = _s2pgt05_candidate_rows(queue_candidate_records, delta_index)
    calibrated_rows = _s2pgt05_calibrated_rows(candidate_rows)
    queue_rows = _s2pgt05_queue_rows(calibrated_rows)
    upstream_gate = _s2pgt05_upstream_delta_gate(delta_resonance_report, delta_errors)
    percentile_gate = _s2pgt05_percentile_calibration_gate(queue_rows)
    source_balance_gate = _s2pgt05_source_balance_gate(queue_rows)
    waiting_credit_gate = _s2pgt05_waiting_credit_gate(queue_rows)
    queue_reason_gate = _s2pgt05_queue_reason_gate(queue_rows)
    deterministic_gate = _s2pgt05_deterministic_order_gate(queue_rows)
    side_effect_gate = _s2pgt05_no_side_effect_gate(queue_rows)
    calibrated_queue_hash = _s2pgt05_queue_state_hash(queue_rows)
    blocking_reasons = [
        *upstream_gate["blocking_reasons"],
        *candidate_errors,
        *percentile_gate["blocking_reasons"],
        *source_balance_gate["blocking_reasons"],
        *waiting_credit_gate["blocking_reasons"],
        *queue_reason_gate["blocking_reasons"],
        *deterministic_gate["blocking_reasons"],
        *side_effect_gate["blocking_reasons"],
    ]
    status = (
        "pass"
        if not blocking_reasons
        and upstream_gate["status"]
        == percentile_gate["status"]
        == source_balance_gate["status"]
        == waiting_credit_gate["status"]
        == queue_reason_gate["status"]
        == deterministic_gate["status"]
        == side_effect_gate["status"]
        == "pass"
        else "blocked"
    )
    return {
        "model_id": S2PGT05_CALIBRATION_MODEL_ID,
        "acceptance_id": S2PGT05_ACCEPTANCE_ID,
        "task_id": S2PGT05_TASK_ID,
        "legacy_task_id": S2PGT05_LEGACY_TASK_ID,
        "phase": "S2PG",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "upstream_s2pgt04_status": delta_resonance_report.get("status"),
        "required_board_ids": list(S2PGT05_REQUIRED_BOARD_IDS),
        "board_ids_observed": percentile_gate["board_ids_observed"],
        "required_source_domains": list(S2PGT05_REQUIRED_SOURCE_DOMAINS),
        "source_domains_observed": source_balance_gate["source_domains_observed"],
        "required_decisions": list(S2PGT05_REQUIRED_DECISIONS),
        "queue_decisions_observed": queue_reason_gate["queue_decisions_observed"],
        "required_candidate_fields": list(S2PGT05_REQUIRED_CANDIDATE_FIELDS),
        "required_gates": list(S2PGT05_REQUIRED_GATES),
        "selected_count_target": S2PGT05_SELECTED_COUNT,
        "waitlist_count_target": S2PGT05_WAITLIST_COUNT,
        "max_source_share": S2PGT05_MAX_SOURCE_SHARE,
        "max_waiting_days": S2PGT05_MAX_WAITING_DAYS,
        "max_waiting_credit": S2PGT05_MAX_WAITING_CREDIT,
        "upstream_delta_resonance_gate": upstream_gate["status"],
        "percentile_calibration_gate": percentile_gate["status"],
        "source_balance_gate": source_balance_gate["status"],
        "waiting_credit_gate": waiting_credit_gate["status"],
        "queue_reason_gate": queue_reason_gate["status"],
        "deterministic_order_gate": deterministic_gate["status"],
        "no_side_effect_gate": side_effect_gate["status"],
        "selected_source_counts": source_balance_gate["selected_source_counts"],
        "source_share_by_domain": source_balance_gate["source_share_by_domain"],
        "candidate_count": len(queue_rows),
        "calibrated_queue_records": queue_rows,
        "calibrated_queue_hash": calibrated_queue_hash,
        "schema_migration_required": False,
        "public_schema_changed": False,
        "queue_mutation_allowed": False,
        "ranking_algorithm_changed": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "v7_2_contract_files_changed": False,
        "email_frontstage_changed": False,
        "s2pgt05_calibration_ready": status == "pass",
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pgt05_cross_board_calibration(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    delta_resonance_report: Mapping[str, Any],
    queue_candidate_records: Sequence[Mapping[str, Any]],
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PGT05 private calibration evidence without mutating queues."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pgt05-calibration"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pgt05_cross_board_calibration_report(
        generated_at=generated_at,
        delta_resonance_report=delta_resonance_report,
        queue_candidate_records=queue_candidate_records,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "calibration_report_path": str(run_dir / "adp-s2pgt05-calibration-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pgt05-calibration-report.json", report)
        _write_json(state / S2PGT05_REPORT_FILENAME, report)
    return report


def validate_s2pgt05_cross_board_calibration_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PGT05_CALIBRATION_MODEL_ID:
        errors.append("S2PGT05 model_id must be adp-s2pgt05-cross-board-calibration-v1")
    if report.get("task_id") != S2PGT05_TASK_ID:
        errors.append("S2PGT05 task_id must be S2PGT05")
    if report.get("legacy_task_id") != S2PGT05_LEGACY_TASK_ID:
        errors.append("S2PGT05 legacy_task_id must be S2P6T02")
    if report.get("acceptance_id") != S2PGT05_ACCEPTANCE_ID:
        errors.append("S2PGT05 acceptance_id must be ACC-S2PGT05-CALIBRATION")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PGT05 status must be pass or blocked")
    for key in (
        "schema_migration_required",
        "public_schema_changed",
        "queue_mutation_allowed",
        "ranking_algorithm_changed",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "production_affected",
        "real_smtp_sent",
        "v7_2_contract_files_changed",
        "email_frontstage_changed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PGT05 calibration")
    boards = set(report.get("board_ids_observed") or [])
    missing_boards = [board for board in S2PGT05_REQUIRED_BOARD_IDS if board not in boards]
    if missing_boards:
        errors.append("S2PGT05 missing boards: " + ", ".join(missing_boards))
    source_domains = set(report.get("source_domains_observed") or [])
    missing_domains = [domain for domain in S2PGT05_REQUIRED_SOURCE_DOMAINS if domain not in source_domains]
    if missing_domains:
        errors.append("S2PGT05 missing source domains: " + ", ".join(missing_domains))
    decisions = set(report.get("queue_decisions_observed") or [])
    missing_decisions = [decision for decision in S2PGT05_REQUIRED_DECISIONS if decision not in decisions]
    if missing_decisions:
        errors.append("S2PGT05 missing queue decisions: " + ", ".join(missing_decisions))
    rows = report.get("calibrated_queue_records")
    if not isinstance(rows, list) or not rows:
        errors.append("S2PGT05 calibrated_queue_records must be a non-empty list")
        rows = []
    candidate_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"calibrated_queue_records[{index}] must be an object")
            continue
        for field in (*S2PGT05_REQUIRED_CANDIDATE_FIELDS, "percentile_score", "waiting_credit", "calibrated_score", "queue_decision", "queue_reason_code", "queue_reason"):
            if row.get(field) in (None, "", []):
                errors.append(f"calibrated_queue_records[{index}].{field} is required")
        candidate_id = str(row.get("candidate_id") or "")
        if candidate_id in candidate_ids:
            errors.append(f"calibrated_queue_records[{index}].candidate_id must be unique")
        candidate_ids.add(candidate_id)
        if row.get("board_id") not in S2PGT05_REQUIRED_BOARD_IDS:
            errors.append(f"calibrated_queue_records[{index}].board_id is not supported")
        if row.get("source_domain") not in S2PGT05_REQUIRED_SOURCE_DOMAINS:
            errors.append(f"calibrated_queue_records[{index}].source_domain is not supported")
        if row.get("queue_decision") not in S2PGT05_REQUIRED_DECISIONS:
            errors.append(f"calibrated_queue_records[{index}].queue_decision is not supported")
        for score_field in ("raw_score", "percentile_score", "calibrated_score"):
            value = row.get(score_field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"calibrated_queue_records[{index}].{score_field} must be numeric")
        if not isinstance(row.get("waiting_days"), int) or isinstance(row.get("waiting_days"), bool):
            errors.append(f"calibrated_queue_records[{index}].waiting_days must be an integer")
    selected_rows = [row for row in rows if isinstance(row, Mapping) and row.get("queue_decision") == "selected"]
    if len(selected_rows) != S2PGT05_SELECTED_COUNT:
        errors.append(f"S2PGT05 selected queue count must be {S2PGT05_SELECTED_COUNT}")
    source_balance = _s2pgt05_source_balance_gate(rows)
    if source_balance["status"] != "pass":
        errors.extend(source_balance["blocking_reasons"])
    if report.get("calibrated_queue_hash") != _s2pgt05_queue_state_hash(rows):
        errors.append("S2PGT05 calibrated_queue_hash must match calibrated_queue_records")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PGT05 report requires blocking_reasons")
    if report.get("status") == "pass":
        for key in S2PGT05_REQUIRED_GATES:
            if report.get(key) != "pass":
                errors.append(f"passing S2PGT05 report requires {key}=pass")
        if report.get("s2pgt05_calibration_ready") is not True:
            errors.append("passing S2PGT05 report requires s2pgt05_calibration_ready=true")
    return errors


def build_s2pit01_user_center_report(
    *,
    generated_at: str,
    owner_controls: Mapping[str, Any],
    owner_validation_report: Mapping[str, Any],
    owner_impact_preview: Mapping[str, Any],
    storage_inspect_report: Mapping[str, Any],
    control_entries: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the S2PIT01 Chinese user-center and one-edit-entry evidence report."""

    controls = dict(owner_controls)
    rows, row_errors = _s2pit01_control_rows(control_entries or _s2pit01_default_control_entries())
    owner_errors = [str(error) for error in owner_validation_report.get("errors") or []]
    storage_reasons = [str(reason) for reason in storage_inspect_report.get("blocking_reasons") or []]
    owner_gate = "pass" if owner_validation_report.get("status") == "pass" and not owner_errors else "blocked"
    storage_gate = (
        "pass"
        if storage_inspect_report.get("model_id") == "adp-sqlite-data-model-v1"
        and storage_inspect_report.get("action") == "inspect"
        and storage_inspect_report.get("status") == "pass"
        and int(storage_inspect_report.get("schema_version") or 0) >= 1
        else "blocked"
    )
    editable_sources = sorted({str(row.get("editable_fact_source") or "") for row in rows if row.get("editable_fact_source")})
    one_edit_errors: list[str] = []
    if editable_sources != [S2PIT01_EDITABLE_FACT_SOURCE]:
        one_edit_errors.append("S2PIT01 requires exactly one editable fact source: config/owner_controls.yaml")
    if any(row.get("generated_view_editable") is not False for row in rows):
        one_edit_errors.append("S2PIT01 generated owner/user-center views must remain non-editable facts")
    domains = sorted({str(row.get("domain_id") or "") for row in rows})
    missing_domains = [domain for domain in S2PIT01_REQUIRED_CONTROL_DOMAINS if domain not in domains]
    control_errors = list(row_errors)
    if missing_domains:
        control_errors.append("S2PIT01 missing control domains: " + ", ".join(missing_domains))
    user_center_paths_observed = sorted(
        {path for row in rows for path in row.get("user_center_paths", []) if isinstance(path, str)}
    )
    missing_user_center_paths = [
        path for path in S2PIT01_REQUIRED_USER_CENTER_PATHS if path not in set(user_center_paths_observed)
    ]
    path_errors = [
        "S2PIT01 missing user-center paths: " + ", ".join(missing_user_center_paths)
    ] if missing_user_center_paths else []
    sections_observed = sorted({section for row in rows for section in row.get("config_sections", []) if isinstance(section, str)})
    missing_sections = [section for section in S2PIT01_REQUIRED_CONFIG_SECTIONS if section not in sections_observed]
    missing_control_keys = [section for section in S2PIT01_REQUIRED_CONFIG_SECTIONS if section not in controls]
    compatible_errors: list[str] = []
    if missing_sections:
        compatible_errors.append("S2PIT01 missing compiled config sections: " + ", ".join(missing_sections))
    if missing_control_keys:
        compatible_errors.append("S2PIT01 owner_controls missing sections: " + ", ".join(missing_control_keys))
    if any(row.get("compiled_config_path") != S2PIT01_EDITABLE_FACT_SOURCE for row in rows):
        compatible_errors.append("S2PIT01 every control domain must compile to config/owner_controls.yaml")
    click_errors: list[str] = []
    max_click_depth = max((int(row.get("click_depth") or 0) for row in rows), default=0)
    if max_click_depth > S2PIT01_MAX_CLICK_DEPTH:
        click_errors.append(f"S2PIT01 common controls must be reachable within {S2PIT01_MAX_CLICK_DEPTH} clicks")
    no_side_effect_errors = _s2pit01_no_side_effect_errors(rows)
    blocking_reasons = [
        *owner_errors,
        *storage_reasons,
        *one_edit_errors,
        *control_errors,
        *path_errors,
        *compatible_errors,
        *click_errors,
        *no_side_effect_errors,
    ]
    gates = {
        "owner_controls_gate": owner_gate,
        "storage_readability_gate": storage_gate,
        "one_edit_directory_gate": "pass" if not one_edit_errors else "blocked",
        "control_domain_gate": "pass" if not control_errors and not missing_domains else "blocked",
        "click_depth_gate": "pass" if not click_errors else "blocked",
        "compatible_config_gate": "pass" if not compatible_errors else "blocked",
        "no_side_effect_gate": "pass" if not no_side_effect_errors else "blocked",
    }
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    return {
        "model_id": S2PIT01_USER_CENTER_MODEL_ID,
        "acceptance_id": S2PIT01_ACCEPTANCE_ID,
        "task_id": S2PIT01_TASK_ID,
        "legacy_task_id": None,
        "phase": "S2PI",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        **gates,
        "required_control_domains": list(S2PIT01_REQUIRED_CONTROL_DOMAINS),
        "control_domains_observed": domains,
        "required_config_sections": list(S2PIT01_REQUIRED_CONFIG_SECTIONS),
        "config_sections_observed": sections_observed,
        "required_user_center_paths": list(S2PIT01_REQUIRED_USER_CENTER_PATHS),
        "user_center_paths_observed": user_center_paths_observed,
        "editable_fact_sources": editable_sources,
        "single_editable_fact_source": editable_sources[0] if len(editable_sources) == 1 else "",
        "max_click_depth": max_click_depth,
        "max_allowed_click_depth": S2PIT01_MAX_CLICK_DEPTH,
        "control_entries": rows,
        "owner_validation_report": dict(owner_validation_report),
        "owner_impact_preview": dict(owner_impact_preview),
        "storage_inspect_summary": {
            "model_id": storage_inspect_report.get("model_id"),
            "action": storage_inspect_report.get("action"),
            "status": storage_inspect_report.get("status"),
            "schema_version": storage_inspect_report.get("schema_version"),
            "table_count": storage_inspect_report.get("table_count"),
            "db_path": storage_inspect_report.get("db_path"),
        },
        "s2pit01_user_center_ready": status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "schema_migration_allowed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "ranking_algorithm_changed": False,
        "source_adapter_changed": False,
        "email_frontstage_changed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pit01_user_center(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    owner_controls: Mapping[str, Any],
    owner_validation_report: Mapping[str, Any],
    owner_impact_preview: Mapping[str, Any],
    storage_inspect_report: Mapping[str, Any],
    control_entries: Sequence[Mapping[str, Any]] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PIT01 user-center evidence without changing owner controls or storage."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pit01-user-center"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pit01_user_center_report(
        generated_at=generated_at,
        owner_controls=owner_controls,
        owner_validation_report=owner_validation_report,
        owner_impact_preview=owner_impact_preview,
        storage_inspect_report=storage_inspect_report,
        control_entries=control_entries,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "user_center_report_path": str(run_dir / "adp-s2pit01-user-center-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pit01-user-center-report.json", report)
        _write_json(state / S2PIT01_REPORT_FILENAME, report)
    return report


def validate_s2pit01_user_center_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PIT01_USER_CENTER_MODEL_ID:
        errors.append("S2PIT01 model_id must be adp-s2pit01-user-center-v1")
    if report.get("task_id") != S2PIT01_TASK_ID:
        errors.append("S2PIT01 task_id must be S2PIT01")
    if report.get("acceptance_id") != S2PIT01_ACCEPTANCE_ID:
        errors.append("S2PIT01 acceptance_id must be ACC-S2PIT01-USER-CENTER")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PIT01 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "production_affected",
        "real_smtp_sent",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "schema_migration_allowed",
        "public_schema_changed",
        "queue_schema_changed",
        "queue_mutation_allowed",
        "ranking_algorithm_changed",
        "source_adapter_changed",
        "email_frontstage_changed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PIT01 user-center evidence")
    rows = report.get("control_entries")
    if not isinstance(rows, list) or not rows:
        errors.append("S2PIT01 control_entries must be a non-empty list")
        rows = []
    domains = {str(row.get("domain_id") or "") for row in rows if isinstance(row, Mapping)}
    missing_domains = [domain for domain in S2PIT01_REQUIRED_CONTROL_DOMAINS if domain not in domains]
    if missing_domains:
        errors.append("S2PIT01 missing control domains: " + ", ".join(missing_domains))
    if report.get("single_editable_fact_source") != S2PIT01_EDITABLE_FACT_SOURCE:
        errors.append("S2PIT01 single_editable_fact_source must be config/owner_controls.yaml")
    if int(report.get("max_click_depth") or 0) > S2PIT01_MAX_CLICK_DEPTH:
        errors.append(f"S2PIT01 max_click_depth must be <= {S2PIT01_MAX_CLICK_DEPTH}")
    missing_paths = [path for path in S2PIT01_REQUIRED_USER_CENTER_PATHS if path not in set(report.get("user_center_paths_observed") or [])]
    if missing_paths:
        errors.append("S2PIT01 missing user-center paths: " + ", ".join(missing_paths))
    for gate in S2PIT01_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PIT01 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PIT01 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pit01_user_center_ready") is not True:
        errors.append("passing S2PIT01 report requires s2pit01_user_center_ready=true")
    return errors


def _s2pit02_owner_status_summary(owner_status_summary: Mapping[str, Any] | None) -> dict[str, Any]:
    summary = dict(owner_status_summary or {})
    summary["status_states_observed"] = list(summary.get("status_states_observed") or [])
    summary["status_states_not_proven"] = list(summary.get("status_states_not_proven") or [])
    summary["evidence_refs"] = list(summary.get("evidence_refs") or [])
    return summary


def _validate_s2pit02_owner_status_summary(summary: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    missing_fields = [field for field in S2PIT02_REQUIRED_OWNER_STATUS_SUMMARY_FIELDS if field not in summary]
    if missing_fields:
        errors.append("S2PIT02 owner status summary missing fields: " + ", ".join(missing_fields))

    numeric_fields = (
        "sent_today",
        "expected_today",
        "total_candidate_pool",
        "generated_report_or_preview_count",
        "pending_candidate_count",
        "historical_send_record_count",
        "selected_candidate_count",
        "review_action_pending_field_count",
    )
    numbers: dict[str, int] = {}
    for field in numeric_fields:
        if field not in summary:
            continue
        value = summary.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"S2PIT02 owner status summary {field} must be a non-negative integer")
            continue
        numbers[field] = value

    if {"total_candidate_pool", "generated_report_or_preview_count", "pending_candidate_count"} <= set(numbers):
        if numbers["total_candidate_pool"] != (
            numbers["generated_report_or_preview_count"] + numbers["pending_candidate_count"]
        ):
            errors.append("S2PIT02 owner status candidate counts must conserve total_candidate_pool")
    if {"sent_today", "expected_today"} <= set(numbers) and numbers["sent_today"] > numbers["expected_today"]:
        errors.append("S2PIT02 owner status sent_today must not exceed expected_today")

    observed_states = set(summary.get("status_states_observed") or [])
    missing_states = [state for state in S2PIT02_REQUIRED_OWNER_STATUS_STATES if state not in observed_states]
    if missing_states:
        errors.append("S2PIT02 owner status summary missing status states: " + ", ".join(missing_states))

    if summary.get("review_action_snapshot_state") != "pending_daily_snapshot":
        errors.append("S2PIT02 owner status review_action_snapshot_state must be pending_daily_snapshot until real daily reports sync")
    evidence_refs = set(summary.get("evidence_refs") or [])
    if S2PIT02_OWNER_STATUS_PATH not in evidence_refs:
        errors.append(f"S2PIT02 owner status evidence_refs must include {S2PIT02_OWNER_STATUS_PATH}")
    return errors


def build_s2pit02_runtime_dashboard_report(
    *,
    generated_at: str,
    user_center_report: Mapping[str, Any],
    runtime_audit_report: Mapping[str, Any],
    watchdog_report: Mapping[str, Any],
    storage_inspect_report: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
    owner_status_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PIT02 runtime/state dashboard evidence."""

    production_gate = dict(production_gate_state or {})
    owner_summary = _s2pit02_owner_status_summary(owner_status_summary)
    owner_status_errors = _validate_s2pit02_owner_status_summary(owner_summary)
    owner_status_gate = "pass" if not owner_status_errors else "blocked"
    user_errors = validate_s2pit01_user_center_report(user_center_report)
    user_gate = "pass" if user_center_report.get("status") == "pass" and not user_errors else "blocked"
    runtime_errors: list[str] = []
    runtime_gate = "pass"
    for action, report in (("runtime_audit", runtime_audit_report), ("watchdog", watchdog_report)):
        if report.get("model_id") != "adp-stage1-local-runtime-recovery-v1":
            runtime_errors.append(f"{action} report model_id must be adp-stage1-local-runtime-recovery-v1")
        if report.get("action") != action:
            runtime_errors.append(f"{action} report action must be {action}")
        if report.get("status") != "pass":
            runtime_errors.append(f"{action} report must pass")
        for key in ("production_side_effects_enabled", "real_smtp_sent", "real_release_uploaded", "real_scheduler_installed"):
            if report.get(key) is not False:
                runtime_errors.append(f"{action}.{key} must be false")
    if runtime_errors:
        runtime_gate = "blocked"
    storage_errors: list[str] = []
    storage_gate = "pass"
    if storage_inspect_report.get("model_id") != "adp-sqlite-data-model-v1":
        storage_errors.append("storage inspect model_id must be adp-sqlite-data-model-v1")
    if storage_inspect_report.get("action") != "inspect":
        storage_errors.append("storage inspect action must be inspect")
    if storage_inspect_report.get("status") != "pass":
        storage_errors.append("storage inspect report must pass")
    if int(storage_inspect_report.get("schema_version") or 0) < 1:
        storage_errors.append("storage inspect schema_version must be >= 1")
    if storage_errors:
        storage_gate = "blocked"
    production_errors: list[str] = []
    for key in (
        *S2PIT02_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_restore_executed",
        "v7_1_current_switched",
    ):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")
    production_gate_status = "pass" if not production_errors else "blocked"
    sections = {
        "owner_center": {
            "task_id": user_center_report.get("task_id"),
            "status": user_center_report.get("status"),
            "single_editable_fact_source": user_center_report.get("single_editable_fact_source"),
            "owner_status_path": S2PIT02_OWNER_STATUS_PATH,
            "owner_status_summary": owner_summary,
        },
        "runtime": {
            "runtime_audit_status": runtime_audit_report.get("status"),
            "watchdog_status": watchdog_report.get("status"),
            "runtime_actions_observed": [runtime_audit_report.get("action"), watchdog_report.get("action")],
        },
        "storage": {
            "status": storage_inspect_report.get("status"),
            "schema_version": storage_inspect_report.get("schema_version"),
            "table_count": storage_inspect_report.get("table_count"),
            "db_path": storage_inspect_report.get("db_path"),
        },
        "production_boundaries": {
            "stage2_production_accepted": False,
            "integrated_production_accepted": False,
            "real_smtp_sent": False,
            "scheduler_enabled": False,
            "release_upload_allowed": False,
            "public_schema_changed": False,
            "queue_schema_changed": False,
            "v7_2_contract_files_changed": False,
        },
        "next_actions": {
            "next_task_id": "S2PJT01_REVIEW_ACTION_ROI_STATE_MODEL_LOCAL_ONLY",
            "blocking_policy": "P0/P1 and S2PMT07 still block integrated production acceptance",
        },
    }
    missing_sections = [section for section in S2PIT02_REQUIRED_SECTIONS if section not in sections]
    section_gate = "pass" if not missing_sections else "blocked"
    blocking_reasons = [
        *user_errors,
        *owner_status_errors,
        *runtime_errors,
        *storage_errors,
        *production_errors,
        *(f"missing dashboard section: {section}" for section in missing_sections),
    ]
    gates = {
        "owner_center_gate": user_gate,
        "owner_status_count_gate": owner_status_gate,
        "runtime_state_gate": runtime_gate,
        "storage_state_gate": storage_gate,
        "production_boundary_gate": production_gate_status,
        "dashboard_section_gate": section_gate,
    }
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    return {
        "model_id": S2PIT02_RUNTIME_DASHBOARD_MODEL_ID,
        "acceptance_id": S2PIT02_ACCEPTANCE_ID,
        "task_id": S2PIT02_TASK_ID,
        "phase": "S2PI",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        **gates,
        "required_sections": list(S2PIT02_REQUIRED_SECTIONS),
        "required_runtime_actions": list(S2PIT02_REQUIRED_RUNTIME_ACTIONS),
        "dashboard_sections": sections,
        "owner_status_path": S2PIT02_OWNER_STATUS_PATH,
        "owner_status_summary": owner_summary,
        "s2pit02_runtime_dashboard_ready": status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
        "real_smtp_sent": False,
        "smtp_transport_allowed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "schema_migration_allowed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "ranking_algorithm_changed": False,
        "source_adapter_changed": False,
        "email_frontstage_changed": False,
        "v7_1_current_switched": False,
        "v7_2_contract_files_changed": False,
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pit02_runtime_dashboard(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    user_center_report: Mapping[str, Any],
    runtime_audit_report: Mapping[str, Any],
    watchdog_report: Mapping[str, Any],
    storage_inspect_report: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
    owner_status_summary: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PIT02 local runtime dashboard evidence without runtime side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pit02-runtime-dashboard"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pit02_runtime_dashboard_report(
        generated_at=generated_at,
        user_center_report=user_center_report,
        runtime_audit_report=runtime_audit_report,
        watchdog_report=watchdog_report,
        storage_inspect_report=storage_inspect_report,
        production_gate_state=production_gate_state,
        owner_status_summary=owner_status_summary,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "runtime_dashboard_report_path": str(run_dir / "adp-s2pit02-runtime-dashboard-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pit02-runtime-dashboard-report.json", report)
        _write_json(state / S2PIT02_REPORT_FILENAME, report)
    return report


def validate_s2pit02_runtime_dashboard_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PIT02_RUNTIME_DASHBOARD_MODEL_ID:
        errors.append("S2PIT02 model_id must be adp-s2pit02-runtime-dashboard-v1")
    if report.get("task_id") != S2PIT02_TASK_ID:
        errors.append("S2PIT02 task_id must be S2PIT02")
    if report.get("acceptance_id") != S2PIT02_ACCEPTANCE_ID:
        errors.append("S2PIT02 acceptance_id must be ACC-S2PIT02-RUNTIME-DASHBOARD")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PIT02 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PIT02_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
        "schema_migration_allowed",
        "queue_mutation_allowed",
        "ranking_algorithm_changed",
        "source_adapter_changed",
        "email_frontstage_changed",
        "v7_1_current_switched",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PIT02 runtime dashboard evidence")
    sections = report.get("dashboard_sections")
    if not isinstance(sections, Mapping):
        errors.append("S2PIT02 dashboard_sections must be a mapping")
        sections = {}
    missing_sections = [section for section in S2PIT02_REQUIRED_SECTIONS if section not in sections]
    if missing_sections:
        errors.append("S2PIT02 missing dashboard sections: " + ", ".join(missing_sections))
    runtime = sections.get("runtime", {}) if isinstance(sections, Mapping) else {}
    actions = set(runtime.get("runtime_actions_observed") or []) if isinstance(runtime, Mapping) else set()
    missing_actions = [action for action in S2PIT02_REQUIRED_RUNTIME_ACTIONS if action not in actions]
    if missing_actions:
        errors.append("S2PIT02 missing runtime actions: " + ", ".join(missing_actions))
    if report.get("owner_status_path") != S2PIT02_OWNER_STATUS_PATH:
        errors.append(f"S2PIT02 owner_status_path must be {S2PIT02_OWNER_STATUS_PATH}")
    owner_summary = report.get("owner_status_summary")
    if not isinstance(owner_summary, Mapping):
        errors.append("S2PIT02 owner_status_summary must be a mapping")
    else:
        errors.extend(_validate_s2pit02_owner_status_summary(owner_summary))
    for gate in (
        "owner_center_gate",
        "owner_status_count_gate",
        "runtime_state_gate",
        "storage_state_gate",
        "production_boundary_gate",
        "dashboard_section_gate",
    ):
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PIT02 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PIT02 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pit02_runtime_dashboard_ready") is not True:
        errors.append("passing S2PIT02 report requires s2pit02_runtime_dashboard_ready=true")
    return errors


def _s2pit03_view_hash(
    *,
    source_domain_records: Sequence[Mapping[str, Any]],
    reading_board_records: Sequence[Mapping[str, Any]],
    parameter_records: Sequence[Mapping[str, Any]],
    queue_view_records: Sequence[Mapping[str, Any]],
) -> str:
    payload = {
        "source_domain_records": list(source_domain_records),
        "reading_board_records": list(reading_board_records),
        "parameter_records": list(parameter_records),
        "queue_view_records": list(queue_view_records),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_s2pit03_source_model_view_report(
    *,
    generated_at: str,
    user_center_report: Mapping[str, Any],
    source_domain_records: Sequence[Mapping[str, Any]],
    reading_board_records: Sequence[Mapping[str, Any]],
    parameter_records: Sequence[Mapping[str, Any]],
    queue_view_records: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PIT03 source/model/parameter/queue view evidence."""

    production_gate = dict(production_gate_state or {})
    user_errors = validate_s2pit01_user_center_report(user_center_report)
    user_gate = "pass" if user_center_report.get("status") == "pass" and not user_errors else "blocked"

    source_records = [dict(row) for row in source_domain_records]
    source_domains = sorted({str(row.get("domain_id") or "") for row in source_records})
    missing_domains = [domain for domain in S2PIT03_REQUIRED_SOURCE_DOMAINS if domain not in source_domains]
    source_errors: list[str] = []
    for row in source_records:
        domain = str(row.get("domain_id") or "")
        if domain and domain not in S2PIT03_REQUIRED_SOURCE_DOMAINS:
            source_errors.append(f"unknown source domain: {domain}")
        if row.get("health_status") not in {"pass", "ready"}:
            source_errors.append(f"source domain {domain or '<missing>'} health_status must be pass or ready")
        if not row.get("source_refs"):
            source_errors.append(f"source domain {domain or '<missing>'} requires source_refs")
        if not row.get("evidence_refs"):
            source_errors.append(f"source domain {domain or '<missing>'} requires evidence_refs")
    source_errors.extend(f"missing source domain: {domain}" for domain in missing_domains)

    board_records = [dict(row) for row in reading_board_records]
    board_ids = sorted({str(row.get("board_id") or "") for row in board_records})
    missing_boards = [board for board in S2PIT03_REQUIRED_READING_BOARDS if board not in board_ids]
    board_errors: list[str] = []
    for row in board_records:
        board = str(row.get("board_id") or "")
        if board and board not in S2PIT03_REQUIRED_READING_BOARDS:
            board_errors.append(f"unknown reading board: {board}")
        if row.get("health_status") not in {"pass", "ready"}:
            board_errors.append(f"reading board {board or '<missing>'} health_status must be pass or ready")
        refs = {str(ref) for ref in row.get("source_domain_refs") or []}
        if not refs:
            board_errors.append(f"reading board {board or '<missing>'} requires source_domain_refs")
        elif not refs.issubset(set(S2PIT03_REQUIRED_SOURCE_DOMAINS)):
            board_errors.append(f"reading board {board or '<missing>'} has unknown source_domain_refs")
        if not row.get("evidence_refs"):
            board_errors.append(f"reading board {board or '<missing>'} requires evidence_refs")
    board_errors.extend(f"missing reading board: {board}" for board in missing_boards)

    parameters = [dict(row) for row in parameter_records]
    parameter_errors: list[str] = []
    parameter_ids = [str(row.get("parameter_id") or "") for row in parameters]
    if not parameters:
        parameter_errors.append("S2PIT03 requires parameter records")
    if len({pid for pid in parameter_ids if pid}) != len([pid for pid in parameter_ids if pid]):
        parameter_errors.append("S2PIT03 parameter_id values must be unique")
    first_screen = [row for row in parameters if row.get("first_screen") is True]
    if not first_screen:
        parameter_errors.append("S2PIT03 requires at least one first-screen parameter")
    if len(first_screen) > S2PIT03_MAX_FIRST_SCREEN_PARAMETERS:
        parameter_errors.append(f"S2PIT03 first-screen parameters must be <= {S2PIT03_MAX_FIRST_SCREEN_PARAMETERS}")
    for index, row in enumerate(parameters):
        parameter_id = str(row.get("parameter_id") or f"index:{index}")
        for field in S2PIT03_REQUIRED_PARAMETER_FIELDS:
            value = row.get(field)
            if value is None or value == "" or value == []:
                parameter_errors.append(f"parameter {parameter_id} missing {field}")
        if row.get("searchable") is not True:
            parameter_errors.append(f"parameter {parameter_id} must be searchable")
        if row.get("disclosure_tier") not in {"core", "advanced", "engineering"}:
            parameter_errors.append(f"parameter {parameter_id} disclosure_tier must be core, advanced, or engineering")

    queue_records = [dict(row) for row in queue_view_records]
    queue_errors: list[str] = []
    if not queue_records:
        queue_errors.append("S2PIT03 requires queue view records")
    for index, row in enumerate(queue_records):
        item_id = str(row.get("content_id") or row.get("queue_id") or f"index:{index}")
        if str(row.get("source_domain") or "") not in S2PIT03_REQUIRED_SOURCE_DOMAINS:
            queue_errors.append(f"queue item {item_id} source_domain must be D1-D4")
        if str(row.get("board_id") or "") not in S2PIT03_REQUIRED_READING_BOARDS:
            queue_errors.append(f"queue item {item_id} board_id must be B1-B6")
        if not row.get("evidence_refs"):
            queue_errors.append(f"queue item {item_id} requires evidence_refs")
        if not row.get("detail_ref"):
            queue_errors.append(f"queue item {item_id} requires detail_ref")
        if row.get("exportable") is not True:
            queue_errors.append(f"queue item {item_id} must be exportable")

    trace_errors: list[str] = []
    for label, rows in (
        ("source_domain", source_records),
        ("reading_board", board_records),
        ("parameter", parameters),
        ("queue", queue_records),
    ):
        for index, row in enumerate(rows):
            if not row.get("evidence_refs"):
                trace_errors.append(f"{label}[{index}] missing evidence_refs")
    for row in parameters:
        parameter_id = str(row.get("parameter_id") or "<missing>")
        if not row.get("code_refs") or not row.get("test_refs"):
            trace_errors.append(f"parameter {parameter_id} requires code_refs and test_refs")

    side_effect_errors: list[str] = []
    for key in (*S2PIT03_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            side_effect_errors.append(f"production_gate_state.{key} must be false")
    for label, rows in (
        ("source_domain", source_records),
        ("reading_board", board_records),
        ("parameter", parameters),
        ("queue", queue_records),
    ):
        for index, row in enumerate(rows):
            for key in (
                "live_fetch_executed",
                "source_adapter_changed",
                "queue_mutation_allowed",
                "ranking_algorithm_changed",
                "public_schema_changed",
                "real_smtp_sent",
                "scheduler_enabled",
                "release_upload_allowed",
            ):
                if row.get(key, False) is not False:
                    side_effect_errors.append(f"{label}[{index}].{key} must be false")

    view_hash = _s2pit03_view_hash(
        source_domain_records=source_records,
        reading_board_records=board_records,
        parameter_records=parameters,
        queue_view_records=queue_records,
    )
    gates = {
        "user_center_gate": user_gate,
        "source_domain_gate": "pass" if not source_errors else "blocked",
        "reading_board_gate": "pass" if not board_errors else "blocked",
        "parameter_disclosure_gate": "pass" if not parameter_errors else "blocked",
        "queue_view_gate": "pass" if not queue_errors else "blocked",
        "traceability_gate": "pass" if not trace_errors else "blocked",
        "deterministic_view_gate": "pass",
        "no_side_effect_gate": "pass" if not side_effect_errors else "blocked",
    }
    blocking_reasons = [
        *user_errors,
        *source_errors,
        *board_errors,
        *parameter_errors,
        *queue_errors,
        *trace_errors,
        *side_effect_errors,
    ]
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    return {
        "model_id": S2PIT03_SOURCE_MODEL_VIEW_MODEL_ID,
        "acceptance_id": S2PIT03_ACCEPTANCE_ID,
        "task_id": S2PIT03_TASK_ID,
        "phase": "S2PI",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        **gates,
        "required_source_domains": list(S2PIT03_REQUIRED_SOURCE_DOMAINS),
        "source_domains_observed": source_domains,
        "required_reading_boards": list(S2PIT03_REQUIRED_READING_BOARDS),
        "reading_boards_observed": board_ids,
        "source_domain_records": source_records,
        "reading_board_records": board_records,
        "parameter_records": parameters,
        "parameter_count": len(parameters),
        "first_screen_parameter_ids": [str(row.get("parameter_id") or "") for row in first_screen],
        "max_first_screen_parameters": S2PIT03_MAX_FIRST_SCREEN_PARAMETERS,
        "queue_view_records": queue_records,
        "queue_view_count": len(queue_records),
        "view_hash": view_hash,
        "s2pit03_source_model_view_ready": status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pit03_source_model_view(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    user_center_report: Mapping[str, Any],
    source_domain_records: Sequence[Mapping[str, Any]],
    reading_board_records: Sequence[Mapping[str, Any]],
    parameter_records: Sequence[Mapping[str, Any]],
    queue_view_records: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PIT03 local source/model/parameter/queue view evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pit03-source-model-view"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pit03_source_model_view_report(
        generated_at=generated_at,
        user_center_report=user_center_report,
        source_domain_records=source_domain_records,
        reading_board_records=reading_board_records,
        parameter_records=parameter_records,
        queue_view_records=queue_view_records,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "source_model_view_report_path": str(run_dir / "adp-s2pit03-source-model-view-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pit03-source-model-view-report.json", report)
        _write_json(state / S2PIT03_REPORT_FILENAME, report)
    return report


def validate_s2pit03_source_model_view_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PIT03_SOURCE_MODEL_VIEW_MODEL_ID:
        errors.append("S2PIT03 model_id must be adp-s2pit03-source-model-view-v1")
    if report.get("task_id") != S2PIT03_TASK_ID:
        errors.append("S2PIT03 task_id must be S2PIT03")
    if report.get("acceptance_id") != S2PIT03_ACCEPTANCE_ID:
        errors.append("S2PIT03 acceptance_id must be ACC-S2PIT03-SOURCE-MODEL")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PIT03 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PIT03_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PIT03 source/model view evidence")
    missing_domains = [
        domain for domain in S2PIT03_REQUIRED_SOURCE_DOMAINS if domain not in set(report.get("source_domains_observed") or [])
    ]
    if missing_domains:
        errors.append("S2PIT03 missing source domains: " + ", ".join(missing_domains))
    missing_boards = [
        board for board in S2PIT03_REQUIRED_READING_BOARDS if board not in set(report.get("reading_boards_observed") or [])
    ]
    if missing_boards:
        errors.append("S2PIT03 missing reading boards: " + ", ".join(missing_boards))
    parameters = report.get("parameter_records")
    if not isinstance(parameters, list) or not parameters:
        errors.append("S2PIT03 parameter_records must be a non-empty list")
        parameters = []
    if int(report.get("parameter_count") or 0) != len(parameters):
        errors.append("S2PIT03 parameter_count must match parameter_records")
    first_screen_ids = report.get("first_screen_parameter_ids") or []
    if not first_screen_ids:
        errors.append("S2PIT03 first_screen_parameter_ids must be non-empty")
    if len(first_screen_ids) > S2PIT03_MAX_FIRST_SCREEN_PARAMETERS:
        errors.append(f"S2PIT03 first_screen_parameter_ids must be <= {S2PIT03_MAX_FIRST_SCREEN_PARAMETERS}")
    queue_records = report.get("queue_view_records")
    if not isinstance(queue_records, list) or not queue_records:
        errors.append("S2PIT03 queue_view_records must be a non-empty list")
        queue_records = []
    expected_hash = _s2pit03_view_hash(
        source_domain_records=report.get("source_domain_records") or [],
        reading_board_records=report.get("reading_board_records") or [],
        parameter_records=parameters,
        queue_view_records=queue_records,
    )
    if report.get("view_hash") != expected_hash:
        errors.append("S2PIT03 view_hash must match source, board, parameter, and queue records")
    for gate in S2PIT03_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PIT03 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PIT03 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pit03_source_model_view_ready") is not True:
        errors.append("passing S2PIT03 report requires s2pit03_source_model_view_ready=true")
    return errors


def _s2pit04_ledger_hash(records: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {
            "action_ids": [str(item) for item in row.get("action_ids") or []],
            "asset_ids": [str(item) for item in row.get("asset_ids") or []],
            "content_id": str(row.get("content_id") or ""),
            "feedback_id": str(row.get("feedback_id") or ""),
            "feedback_status": str(row.get("feedback_status") or ""),
            "lifecycle_state": str(row.get("lifecycle_state") or ""),
            "mail_id": str(row.get("mail_id") or ""),
            "mail_status": str(row.get("mail_status") or ""),
            "review_ids": [str(item) for item in row.get("review_ids") or []],
            "roi_status": str((row.get("roi") or {}).get("status") or ""),
            "run_id": str(row.get("run_id") or ""),
        }
        for row in records
    ]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pit04_content_ledger_report(
    *,
    generated_at: str,
    runtime_dashboard_report: Mapping[str, Any],
    source_model_view_report: Mapping[str, Any],
    lifecycle_state_report: Mapping[str, Any],
    review_schedule_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    ledger_records: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only content/mail/review/action/ROI ledger reconciliation evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []

    runtime_errors = validate_s2pit02_runtime_dashboard_report(runtime_dashboard_report)
    runtime_gate = (
        "pass"
        if runtime_dashboard_report.get("status") == "pass"
        and runtime_dashboard_report.get("s2pit02_runtime_dashboard_ready") is True
        and not runtime_errors
        else "blocked"
    )
    if runtime_gate != "pass":
        blocking_reasons.append("S2PIT02 runtime dashboard report must pass")
        blocking_reasons.extend(runtime_errors)

    source_errors = validate_s2pit03_source_model_view_report(source_model_view_report)
    source_gate = (
        "pass"
        if source_model_view_report.get("status") == "pass"
        and source_model_view_report.get("s2pit03_source_model_view_ready") is True
        and not source_errors
        else "blocked"
    )
    if source_gate != "pass":
        blocking_reasons.append("S2PIT03 source/model view report must pass")
        blocking_reasons.extend(source_errors)

    lifecycle_errors = validate_s2pjt01_lifecycle_state_report(lifecycle_state_report)
    lifecycle_gate = (
        "pass"
        if lifecycle_state_report.get("status") == "pass"
        and lifecycle_state_report.get("s2pjt01_lifecycle_state_ready") is True
        and not lifecycle_errors
        else "blocked"
    )
    if lifecycle_gate != "pass":
        blocking_reasons.append("S2PJT01 lifecycle state report must pass")
        blocking_reasons.extend(lifecycle_errors)

    review_errors = validate_s2pjt02_review_schedule_report(review_schedule_report)
    review_gate = (
        "pass"
        if review_schedule_report.get("status") == "pass"
        and review_schedule_report.get("s2pjt02_review_schedule_ready") is True
        and not review_errors
        else "blocked"
    )
    if review_gate != "pass":
        blocking_reasons.append("S2PJT02 review schedule report must pass")
        blocking_reasons.extend(review_errors)

    action_errors = validate_s2pjt03_action_asset_roi_report(action_roi_report)
    action_gate = (
        "pass"
        if action_roi_report.get("status") == "pass"
        and action_roi_report.get("s2pjt03_action_roi_ready") is True
        and not action_errors
        else "blocked"
    )
    if action_gate != "pass":
        blocking_reasons.append("S2PJT03 action/asset/ROI report must pass")
        blocking_reasons.extend(action_errors)

    review_content_ids = {str(row.get("content_id") or "") for row in review_schedule_report.get("review_records") or []}
    action_ids = {str(row.get("action_id") or "") for row in action_roi_report.get("action_records") or []}
    calculated_roi_content_ids = {
        str(row.get("content_id") or "")
        for row in action_roi_report.get("action_records") or []
        if row.get("actual_roi_status") == "calculated"
    }
    asset_ids = {str(row.get("asset_id") or "") for row in action_roi_report.get("capability_assets") or []}
    normalized_records: list[dict[str, Any]] = []
    record_errors: list[str] = []
    trace_errors: list[str] = []
    side_effect_errors: list[str] = []
    content_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    mail_status_counts = {status: 0 for status in S2PIT04_ALLOWED_MAIL_STATUSES}
    feedback_status_counts = {status: 0 for status in S2PIT04_ALLOWED_FEEDBACK_STATUSES}
    roi_status_counts = {status: 0 for status in S2PJT03_ALLOWED_ACTUAL_ROI_STATUSES}

    if not ledger_records:
        record_errors.append("S2PIT04 requires ledger_records")
    for index, record in enumerate(ledger_records):
        row = dict(record)
        content_id = str(row.get("content_id") or "")
        mail_status = str(row.get("mail_status") or "")
        feedback_status = str(row.get("feedback_status") or "")
        roi = row.get("roi") if isinstance(row.get("roi"), Mapping) else {}
        roi_status = str(roi.get("status") or "")
        for field in S2PIT04_REQUIRED_RECORD_FIELDS:
            value = row.get(field)
            if field == "asset_ids":
                if value is None:
                    record_errors.append(f"ledger record {content_id or index} missing {field}")
                continue
            if value is None or value == "" or value == [] or value == {}:
                record_errors.append(f"ledger record {content_id or index} missing {field}")
        if content_id:
            if content_id in content_ids:
                duplicate_ids.add(content_id)
            content_ids.add(content_id)
            if content_id not in review_content_ids:
                trace_errors.append(f"{content_id} is not traceable to S2PJT02 review records")
        if mail_status not in S2PIT04_ALLOWED_MAIL_STATUSES:
            record_errors.append(f"{content_id or index} mail_status must be previewed, ready_no_send, or blocked_no_send")
        else:
            mail_status_counts[mail_status] += 1
        if feedback_status not in S2PIT04_ALLOWED_FEEDBACK_STATUSES:
            record_errors.append(f"{content_id or index} feedback_status must be pending, received, or not_requested")
        else:
            feedback_status_counts[feedback_status] += 1
        if roi_status not in S2PJT03_ALLOWED_ACTUAL_ROI_STATUSES:
            record_errors.append(f"{content_id or index} roi.status must be not_calculable or calculated")
        else:
            roi_status_counts[roi_status] += 1
        for action_id in [str(item) for item in row.get("action_ids") or []]:
            if action_id not in action_ids:
                trace_errors.append(f"{content_id or index} action_id {action_id} is not traceable to S2PJT03")
        for asset_id in [str(item) for item in row.get("asset_ids") or []]:
            if asset_id not in asset_ids:
                trace_errors.append(f"{content_id or index} asset_id {asset_id} is not traceable to S2PJT03")
        if roi_status == "calculated" and content_id not in calculated_roi_content_ids:
            trace_errors.append(f"{content_id or index} calculated ROI must trace to S2PJT03 calculated actual ROI")
        if not isinstance(row.get("evidence_refs"), list) or not row.get("evidence_refs"):
            trace_errors.append(f"{content_id or index} evidence_refs must be a non-empty list")
        if not row.get("run_id") or not row.get("mail_id") or not row.get("feedback_id"):
            trace_errors.append(f"{content_id or index} requires run_id, mail_id, and feedback_id")
        for key in (
            "real_smtp_sent",
            "scheduler_enabled",
            "release_upload_allowed",
            "db_migration_executed",
            "public_schema_changed",
            "queue_mutation_allowed",
            "source_adapter_changed",
            "email_frontstage_changed",
        ):
            if row.get(key, False) is not False:
                side_effect_errors.append(f"{content_id or index}.{key} must be false")
        normalized_records.append(row)
    if duplicate_ids:
        record_errors.append("duplicate ledger content_id: " + ", ".join(sorted(duplicate_ids)))

    count_errors: list[str] = []
    if len(content_ids) != len(normalized_records):
        count_errors.append("ledger content_id count must equal record count")
    if not any(status_counts > 0 for status_counts in roi_status_counts.values()):
        count_errors.append("ledger must include ROI status counts")

    production_errors: list[str] = []
    for key in (*S2PIT04_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "runtime_dashboard_gate": runtime_gate,
        "source_model_view_gate": source_gate,
        "lifecycle_state_gate": lifecycle_gate,
        "review_schedule_gate": review_gate,
        "action_roi_gate": action_gate,
        "ledger_record_gate": "pass" if not record_errors else "blocked",
        "traceability_gate": "pass" if not trace_errors else "blocked",
        "count_conservation_gate": "pass" if not count_errors else "blocked",
        "deterministic_ledger_gate": "pass",
        "no_side_effect_gate": "pass" if not side_effect_errors and not production_errors else "blocked",
    }
    blocking_reasons.extend(record_errors)
    blocking_reasons.extend(trace_errors)
    blocking_reasons.extend(count_errors)
    blocking_reasons.extend(side_effect_errors)
    blocking_reasons.extend(production_errors)
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    ledger_hash = _s2pit04_ledger_hash(normalized_records)

    return {
        "model_id": S2PIT04_CONTENT_LEDGER_MODEL_ID,
        "acceptance_id": S2PIT04_ACCEPTANCE_ID,
        "task_id": S2PIT04_TASK_ID,
        "phase": "S2PI",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        **gates,
        "required_record_fields": list(S2PIT04_REQUIRED_RECORD_FIELDS),
        "allowed_mail_statuses": list(S2PIT04_ALLOWED_MAIL_STATUSES),
        "allowed_feedback_statuses": list(S2PIT04_ALLOWED_FEEDBACK_STATUSES),
        "content_count": len(content_ids),
        "ledger_record_count": len(normalized_records),
        "mail_status_counts": mail_status_counts,
        "feedback_status_counts": feedback_status_counts,
        "roi_status_counts": roi_status_counts,
        "ledger_records": normalized_records,
        "ledger_hash": ledger_hash,
        "s2pit04_content_ledger_ready": status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pit04_content_ledger(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    runtime_dashboard_report: Mapping[str, Any],
    source_model_view_report: Mapping[str, Any],
    lifecycle_state_report: Mapping[str, Any],
    review_schedule_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    ledger_records: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PIT04 local content/mail/review/action/ROI ledger evidence."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pit04-content-ledger"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pit04_content_ledger_report(
        generated_at=generated_at,
        runtime_dashboard_report=runtime_dashboard_report,
        source_model_view_report=source_model_view_report,
        lifecycle_state_report=lifecycle_state_report,
        review_schedule_report=review_schedule_report,
        action_roi_report=action_roi_report,
        ledger_records=ledger_records,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "content_ledger_report_path": str(run_dir / "adp-s2pit04-content-ledger-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pit04-content-ledger-report.json", report)
        _write_json(state / S2PIT04_REPORT_FILENAME, report)
    return report


def validate_s2pit04_content_ledger_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PIT04_CONTENT_LEDGER_MODEL_ID:
        errors.append("S2PIT04 model_id must be adp-s2pit04-content-mail-review-action-roi-ledger-v1")
    if report.get("task_id") != S2PIT04_TASK_ID:
        errors.append("S2PIT04 task_id must be S2PIT04")
    if report.get("acceptance_id") != S2PIT04_ACCEPTANCE_ID:
        errors.append("S2PIT04 acceptance_id must be ACC-S2PIT04-LEDGER")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PIT04 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PIT04_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PIT04 local ledger evidence")
    records = report.get("ledger_records")
    if not isinstance(records, list) or not records:
        errors.append("S2PIT04 ledger_records must be a non-empty list")
        records = []
    if int(report.get("ledger_record_count") or 0) != len(records):
        errors.append("S2PIT04 ledger_record_count must match ledger_records")
    if int(report.get("content_count") or 0) != len({str(row.get("content_id") or "") for row in records}):
        errors.append("S2PIT04 content_count must match unique ledger content_ids")
    if report.get("ledger_hash") != _s2pit04_ledger_hash(records):
        errors.append("S2PIT04 ledger_hash must match ledger_records")
    for gate in S2PIT04_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PIT04 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PIT04 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pit04_content_ledger_ready") is not True:
        errors.append("passing S2PIT04 report requires s2pit04_content_ledger_ready=true")
    return errors


def _s2pkt01_contract_payload(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for row in records:
        payload.append(
            {
                "contract_id": str(row.get("contract_id") or ""),
                "cross_cutting_boards": [str(item) for item in row.get("cross_cutting_boards") or []],
                "evidence_labels": [str(item) for item in row.get("evidence_labels") or []],
                "feedback_actions": [str(item) for item in row.get("feedback_actions") or []],
                "mail_product_id": str(row.get("mail_product_id") or ""),
                "primary_board": str(row.get("primary_board") or ""),
                "reading_layers": [str(item) for item in row.get("reading_layers") or []],
                "status": str(row.get("status") or ""),
                "template_version": str(row.get("template_version") or ""),
            }
        )
    return sorted(payload, key=lambda item: item["mail_product_id"])


def _s2pkt01_mail_contract_hash(records: Sequence[Mapping[str, Any]]) -> str:
    encoded = json.dumps(_s2pkt01_contract_payload(records), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _s2pkt01_product_hash(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(_s2pkt01_contract_payload([record])[0], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pkt01_mail_contract_report(
    *,
    generated_at: str,
    content_quality_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    mail_contracts: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only M1-M4 shared mail contract readiness evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []

    quality_errors = validate_s2pht05_content_quality_gate_report(content_quality_report)
    content_quality_gate = (
        "pass"
        if content_quality_report.get("status") == "pass"
        and content_quality_report.get("s2pht05_content_quality_gate_ready") is True
        and not quality_errors
        else "blocked"
    )
    if content_quality_gate != "pass":
        blocking_reasons.append("S2PHT05 content quality report must pass")
        blocking_reasons.extend(quality_errors)

    ledger_errors = validate_s2pit04_content_ledger_report(content_ledger_report)
    content_ledger_gate = (
        "pass"
        if content_ledger_report.get("status") == "pass"
        and content_ledger_report.get("s2pit04_content_ledger_ready") is True
        and not ledger_errors
        else "blocked"
    )
    if content_ledger_gate != "pass":
        blocking_reasons.append("S2PIT04 content ledger report must pass")
        blocking_reasons.extend(ledger_errors)

    action_errors = validate_s2pjt03_action_asset_roi_report(action_roi_report)
    action_roi_gate = (
        "pass"
        if action_roi_report.get("status") == "pass"
        and action_roi_report.get("s2pjt03_action_roi_ready") is True
        and not action_errors
        else "blocked"
    )
    if action_roi_gate != "pass":
        blocking_reasons.append("S2PJT03 action/asset/ROI report must pass")
        blocking_reasons.extend(action_errors)

    normalized_contracts: list[dict[str, Any]] = []
    contract_errors: list[str] = []
    board_errors: list[str] = []
    reading_errors: list[str] = []
    evidence_errors: list[str] = []
    feedback_errors: list[str] = []
    hash_status_errors: list[str] = []
    side_effect_errors: list[str] = []
    seen_products: set[str] = set()
    duplicate_products: set[str] = set()
    status_counts = {status: 0 for status in S2PKT01_ALLOWED_MAIL_STATUSES}

    if not mail_contracts:
        contract_errors.append("S2PKT01 requires mail_contracts")
    for index, contract in enumerate(mail_contracts):
        row = dict(contract)
        product_id = str(row.get("mail_product_id") or "")
        for field in S2PKT01_REQUIRED_CONTRACT_FIELDS:
            value = row.get(field)
            if value is None or value == "" or value == []:
                contract_errors.append(f"mail contract {product_id or index} missing {field}")
        if product_id:
            if product_id in seen_products:
                duplicate_products.add(product_id)
            seen_products.add(product_id)
            if product_id not in S2PKT01_MAIL_PRODUCTS:
                contract_errors.append(f"{product_id} must be one of M1, M2, M3, M4")
            expected_board = S2PKT01_PRIMARY_BOARD_BY_MAIL.get(product_id)
            if expected_board and row.get("primary_board") != expected_board:
                board_errors.append(f"{product_id} primary_board must be {expected_board}")
        if row.get("contract_id") != S2PKT01_EMAIL_CONTRACT_ID:
            contract_errors.append(f"{product_id or index} contract_id must be EMAIL_LEARNING_V1")
        if row.get("template_version") != S2PKT01_TEMPLATE_VERSION:
            contract_errors.append(f"{product_id or index} template_version must be {S2PKT01_TEMPLATE_VERSION}")
        cross_boards = [str(item) for item in row.get("cross_cutting_boards") or []]
        if tuple(cross_boards) != S2PKT01_CROSS_CUTTING_BOARDS:
            board_errors.append(f"{product_id or index} cross_cutting_boards must be B4/B5/B6")
        reading_layers = [str(item) for item in row.get("reading_layers") or []]
        for layer in S2PKT01_READING_LAYERS:
            if layer not in reading_layers:
                reading_errors.append(f"{product_id or index} missing reading layer {layer}")
        evidence_labels = [str(item) for item in row.get("evidence_labels") or []]
        for label in S2PKT01_EVIDENCE_LABELS:
            if label not in evidence_labels:
                evidence_errors.append(f"{product_id or index} missing evidence label {label}")
        feedback_actions = [str(item) for item in row.get("feedback_actions") or []]
        for action in S2PKT01_FEEDBACK_ACTIONS:
            if action not in feedback_actions:
                feedback_errors.append(f"{product_id or index} missing feedback action {action}")
        status = str(row.get("status") or "")
        if status not in S2PKT01_ALLOWED_MAIL_STATUSES:
            hash_status_errors.append(f"{product_id or index} status must be ready_no_send, previewed, or blocked_no_send")
        else:
            status_counts[status] += 1
        product_hash = _s2pkt01_product_hash(row)
        if row.get("mail_hash") not in (None, "", product_hash):
            hash_status_errors.append(f"{product_id or index} mail_hash must match contract fields")
        row["mail_hash"] = product_hash
        for key in (
            "real_smtp_sent",
            "scheduler_enabled",
            "release_upload_allowed",
            "db_migration_executed",
            "public_schema_changed",
            "queue_mutation_allowed",
            "source_adapter_changed",
            "email_frontstage_changed",
        ):
            if row.get(key, False) is not False:
                side_effect_errors.append(f"{product_id or index}.{key} must be false")
        normalized_contracts.append(row)

    missing_products = [product_id for product_id in S2PKT01_MAIL_PRODUCTS if product_id not in seen_products]
    if missing_products:
        contract_errors.append("missing mail products: " + ", ".join(missing_products))
    if duplicate_products:
        contract_errors.append("duplicate mail products: " + ", ".join(sorted(duplicate_products)))
    if len(seen_products) == len(S2PKT01_MAIL_PRODUCTS):
        primary_boards = {str(row.get("primary_board") or "") for row in normalized_contracts}
        if len(primary_boards) < 4:
            board_errors.append("M1-M4 must keep distinct board scopes")

    production_errors: list[str] = []
    for key in (*S2PKT01_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "content_quality_gate": content_quality_gate,
        "content_ledger_gate": content_ledger_gate,
        "action_roi_gate": action_roi_gate,
        "shared_contract_gate": "pass" if not contract_errors else "blocked",
        "board_differentiation_gate": "pass" if not board_errors else "blocked",
        "reading_layer_gate": "pass" if not reading_errors else "blocked",
        "evidence_label_gate": "pass" if not evidence_errors else "blocked",
        "feedback_component_gate": "pass" if not feedback_errors else "blocked",
        "hash_status_gate": "pass" if not hash_status_errors else "blocked",
        "no_side_effect_gate": "pass" if not side_effect_errors and not production_errors else "blocked",
    }
    blocking_reasons.extend(contract_errors)
    blocking_reasons.extend(board_errors)
    blocking_reasons.extend(reading_errors)
    blocking_reasons.extend(evidence_errors)
    blocking_reasons.extend(feedback_errors)
    blocking_reasons.extend(hash_status_errors)
    blocking_reasons.extend(side_effect_errors)
    blocking_reasons.extend(production_errors)
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    contract_hash = _s2pkt01_mail_contract_hash(normalized_contracts)

    return {
        "model_id": S2PKT01_MAIL_CONTRACT_MODEL_ID,
        "acceptance_id": S2PKT01_ACCEPTANCE_ID,
        "task_id": S2PKT01_TASK_ID,
        "phase": "S2PK",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        **gates,
        "email_contract_id": S2PKT01_EMAIL_CONTRACT_ID,
        "template_version": S2PKT01_TEMPLATE_VERSION,
        "required_mail_products": list(S2PKT01_MAIL_PRODUCTS),
        "required_reading_layers": list(S2PKT01_READING_LAYERS),
        "required_evidence_labels": list(S2PKT01_EVIDENCE_LABELS),
        "required_feedback_actions": list(S2PKT01_FEEDBACK_ACTIONS),
        "allowed_mail_statuses": list(S2PKT01_ALLOWED_MAIL_STATUSES),
        "mail_product_count": len(seen_products),
        "mail_status_counts": status_counts,
        "mail_contracts": sorted(normalized_contracts, key=lambda row: str(row.get("mail_product_id") or "")),
        "mail_contract_hash": contract_hash,
        "s2pkt01_mail_contract_ready": status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pkt01_mail_contract(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    content_quality_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    mail_contracts: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PKT01 local M1-M4 mail contract evidence without sending mail."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pkt01-mail-contract"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pkt01_mail_contract_report(
        generated_at=generated_at,
        content_quality_report=content_quality_report,
        content_ledger_report=content_ledger_report,
        action_roi_report=action_roi_report,
        mail_contracts=mail_contracts,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "mail_contract_report_path": str(run_dir / "adp-s2pkt01-mail-contract-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pkt01-mail-contract-report.json", report)
        _write_json(state / S2PKT01_REPORT_FILENAME, report)
    return report


def validate_s2pkt01_mail_contract_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PKT01_MAIL_CONTRACT_MODEL_ID:
        errors.append("S2PKT01 model_id must be adp-s2pkt01-mail-contract-v1")
    if report.get("task_id") != S2PKT01_TASK_ID:
        errors.append("S2PKT01 task_id must be S2PKT01")
    if report.get("acceptance_id") != S2PKT01_ACCEPTANCE_ID:
        errors.append("S2PKT01 acceptance_id must be ACC-S2PKT01-MAIL-CONTRACT")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PKT01 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PKT01_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PKT01 local mail contract evidence")
    records = report.get("mail_contracts")
    if not isinstance(records, list) or not records:
        errors.append("S2PKT01 mail_contracts must be a non-empty list")
        records = []
    if int(report.get("mail_product_count") or 0) != len({str(row.get("mail_product_id") or "") for row in records}):
        errors.append("S2PKT01 mail_product_count must match unique mail_product_id values")
    if report.get("mail_contract_hash") != _s2pkt01_mail_contract_hash(records):
        errors.append("S2PKT01 mail_contract_hash must match mail_contracts")
    for row in records:
        expected_hash = _s2pkt01_product_hash(row)
        if row.get("mail_hash") != expected_hash:
            errors.append(f"{row.get('mail_product_id') or 'mail'} mail_hash must match contract fields")
    for gate in S2PKT01_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PKT01 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PKT01 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pkt01_mail_contract_ready") is not True:
        errors.append("passing S2PKT01 report requires s2pkt01_mail_contract_ready=true")
    return errors


def _s2pkt02_m1_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    sections = []
    for section in record.get("sections") or []:
        section_map = section if isinstance(section, Mapping) else {}
        sections.append(
            {
                "action_ids": [str(item) for item in section_map.get("action_ids") or []],
                "content_ids": [str(item) for item in section_map.get("content_ids") or []],
                "evidence_labels": [str(item) for item in section_map.get("evidence_labels") or []],
                "evidence_refs": [str(item) for item in section_map.get("evidence_refs") or []],
                "section_id": str(section_map.get("section_id") or ""),
            }
        )
    sections = sorted(sections, key=lambda item: item["section_id"])
    return {
        "action_ids": [str(item) for item in record.get("action_ids") or []],
        "contract_id": str(record.get("contract_id") or ""),
        "cross_cutting_boards": [str(item) for item in record.get("cross_cutting_boards") or []],
        "mail_product_id": str(record.get("mail_product_id") or ""),
        "primary_board": str(record.get("primary_board") or ""),
        "sections": sections,
        "source_content_ids": [str(item) for item in record.get("source_content_ids") or []],
        "status": str(record.get("status") or ""),
        "template_version": str(record.get("template_version") or ""),
    }


def _s2pkt02_m1_mail_hash(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(_s2pkt02_m1_payload(record), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pkt02_m1_mail_report(
    *,
    generated_at: str,
    mail_contract_report: Mapping[str, Any],
    content_quality_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    m1_mail_record: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PKT02 M1 science/theory frontier mail evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []

    mail_contract_errors = validate_s2pkt01_mail_contract_report(mail_contract_report)
    mail_contract_gate = (
        "pass"
        if mail_contract_report.get("status") == "pass"
        and mail_contract_report.get("s2pkt01_mail_contract_ready") is True
        and not mail_contract_errors
        else "blocked"
    )
    if mail_contract_gate != "pass":
        blocking_reasons.append("S2PKT01 mail contract report must pass")
        blocking_reasons.extend(mail_contract_errors)

    quality_errors = validate_s2pht05_content_quality_gate_report(content_quality_report)
    content_quality_gate = (
        "pass"
        if content_quality_report.get("status") == "pass"
        and content_quality_report.get("s2pht05_content_quality_gate_ready") is True
        and not quality_errors
        else "blocked"
    )
    if content_quality_gate != "pass":
        blocking_reasons.append("S2PHT05 content quality report must pass")
        blocking_reasons.extend(quality_errors)

    ledger_errors = validate_s2pit04_content_ledger_report(content_ledger_report)
    content_ledger_gate = (
        "pass"
        if content_ledger_report.get("status") == "pass"
        and content_ledger_report.get("s2pit04_content_ledger_ready") is True
        and not ledger_errors
        else "blocked"
    )
    if content_ledger_gate != "pass":
        blocking_reasons.append("S2PIT04 content ledger report must pass")
        blocking_reasons.extend(ledger_errors)

    action_errors = validate_s2pjt03_action_asset_roi_report(action_roi_report)
    action_roi_gate = (
        "pass"
        if action_roi_report.get("status") == "pass"
        and action_roi_report.get("s2pjt03_action_roi_ready") is True
        and not action_errors
        else "blocked"
    )
    if action_roi_gate != "pass":
        blocking_reasons.append("S2PJT03 action/asset/ROI report must pass")
        blocking_reasons.extend(action_errors)

    record = dict(m1_mail_record)
    scope_errors: list[str] = []
    section_errors: list[str] = []
    evidence_errors: list[str] = []
    personal_action_errors: list[str] = []
    hash_status_errors: list[str] = []
    side_effect_errors: list[str] = []

    contracts = [row for row in mail_contract_report.get("mail_contracts") or [] if isinstance(row, Mapping)]
    m1_contract = next((row for row in contracts if row.get("mail_product_id") == S2PKT02_MAIL_PRODUCT_ID), {})
    if not m1_contract:
        scope_errors.append("S2PKT02 requires M1 contract from S2PKT01")
    if record.get("mail_product_id") != S2PKT02_MAIL_PRODUCT_ID:
        scope_errors.append("S2PKT02 m1_mail_record.mail_product_id must be M1")
    if record.get("contract_id") != S2PKT01_EMAIL_CONTRACT_ID:
        scope_errors.append("S2PKT02 M1 contract_id must be EMAIL_LEARNING_V1")
    if record.get("template_version") != S2PKT01_TEMPLATE_VERSION:
        scope_errors.append(f"S2PKT02 M1 template_version must be {S2PKT01_TEMPLATE_VERSION}")
    if record.get("primary_board") != S2PKT02_PRIMARY_BOARD:
        scope_errors.append("S2PKT02 M1 primary_board must be B1")
    cross_boards = [str(item) for item in record.get("cross_cutting_boards") or []]
    if tuple(cross_boards) != S2PKT01_CROSS_CUTTING_BOARDS:
        scope_errors.append("S2PKT02 M1 cross_cutting_boards must be B4/B5/B6")
    for field in ("contract_id", "template_version", "primary_board", "cross_cutting_boards"):
        if m1_contract and record.get(field) != m1_contract.get(field):
            scope_errors.append(f"S2PKT02 M1 {field} must match S2PKT01 M1 contract")

    status = str(record.get("status") or "")
    if status not in S2PKT01_ALLOWED_MAIL_STATUSES:
        hash_status_errors.append("S2PKT02 M1 status must be ready_no_send, previewed, or blocked_no_send")

    ledger_content_ids = {str(row.get("content_id") or "") for row in content_ledger_report.get("ledger_records") or []}
    action_records = [row for row in action_roi_report.get("action_records") or [] if isinstance(row, Mapping)]
    action_horizon_by_id = {str(row.get("action_id") or ""): str(row.get("horizon") or "") for row in action_records}
    source_content_ids = [str(item) for item in record.get("source_content_ids") or []]
    if not source_content_ids:
        section_errors.append("S2PKT02 M1 source_content_ids must be non-empty")
    for content_id in source_content_ids:
        if content_id not in ledger_content_ids:
            section_errors.append(f"S2PKT02 M1 source_content_id {content_id} not traceable to S2PIT04")

    sections = [section for section in record.get("sections") or [] if isinstance(section, Mapping)]
    section_ids = [str(section.get("section_id") or "") for section in sections]
    for section_id in S2PKT02_REQUIRED_SECTIONS:
        if section_id not in section_ids:
            section_errors.append(f"S2PKT02 M1 missing section {section_id}")
    for section in sections:
        section_id = str(section.get("section_id") or "section")
        content_ids = [str(item) for item in section.get("content_ids") or []]
        evidence_refs = [str(item) for item in section.get("evidence_refs") or []]
        evidence_labels = [str(item) for item in section.get("evidence_labels") or []]
        section_action_ids = [str(item) for item in section.get("action_ids") or []]
        if not content_ids:
            section_errors.append(f"{section_id} content_ids must be non-empty")
        for content_id in content_ids:
            if content_id not in source_content_ids:
                section_errors.append(f"{section_id} content_id {content_id} not in M1 source_content_ids")
        if not evidence_refs:
            evidence_errors.append(f"{section_id} evidence_refs must be non-empty")
        for label in evidence_labels:
            if label not in S2PKT01_EVIDENCE_LABELS:
                evidence_errors.append(f"{section_id} evidence label {label} is not allowed")
        if section_id == "scientific_mechanism" and "FACT" not in evidence_labels:
            evidence_errors.append("scientific_mechanism requires FACT evidence label")
        if section_id == "evidence_chain" and "OBSERVATION" not in evidence_labels:
            evidence_errors.append("evidence_chain requires OBSERVATION evidence label")
        if section_id == "counterevidence" and "INFERENCE" not in evidence_labels:
            evidence_errors.append("counterevidence requires INFERENCE evidence label")
        if section_id == "personal_value" and not ({"OPINION", "INFERENCE"} & set(evidence_labels)):
            personal_action_errors.append("personal_value requires OPINION or INFERENCE label")
        if section_id == "action_path" and not section_action_ids:
            personal_action_errors.append("action_path requires action_ids")
        for action_id in section_action_ids:
            if action_id not in action_horizon_by_id:
                personal_action_errors.append(f"{section_id} action_id {action_id} not traceable to S2PJT03")

    action_ids = [str(item) for item in record.get("action_ids") or []]
    action_windows = sorted({action_horizon_by_id.get(action_id, "") for action_id in action_ids if action_id in action_horizon_by_id})
    for action_id in action_ids:
        if action_id not in action_horizon_by_id:
            personal_action_errors.append(f"S2PKT02 M1 action_id {action_id} not traceable to S2PJT03")
    missing_windows = [window for window in S2PKT02_REQUIRED_ACTION_WINDOWS if window not in action_windows]
    if missing_windows:
        personal_action_errors.append("S2PKT02 M1 missing required action windows: " + ", ".join(missing_windows))

    m1_hash = _s2pkt02_m1_mail_hash(record)
    if record.get("m1_mail_hash") not in (None, "", m1_hash):
        hash_status_errors.append("S2PKT02 M1 m1_mail_hash must match M1 mail fields")
    record["m1_mail_hash"] = m1_hash

    for key in (
        "real_smtp_sent",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "db_migration_executed",
        "schema_migration_allowed",
        "public_schema_changed",
        "queue_schema_changed",
        "queue_mutation_allowed",
        "ranking_algorithm_changed",
        "source_adapter_changed",
        "email_frontstage_changed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
    ):
        if record.get(key, False) is not False:
            side_effect_errors.append(f"S2PKT02 M1 {key} must be false")

    production_errors: list[str] = []
    for key in (*S2PKT02_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "mail_contract_gate": mail_contract_gate,
        "content_quality_gate": content_quality_gate,
        "content_ledger_gate": content_ledger_gate,
        "action_roi_gate": action_roi_gate,
        "m1_scope_gate": "pass" if not scope_errors else "blocked",
        "section_coverage_gate": "pass" if not section_errors else "blocked",
        "evidence_counterevidence_gate": "pass" if not evidence_errors else "blocked",
        "personal_action_gate": "pass" if not personal_action_errors else "blocked",
        "hash_status_gate": "pass" if not hash_status_errors else "blocked",
        "no_side_effect_gate": "pass" if not side_effect_errors and not production_errors else "blocked",
    }
    blocking_reasons.extend(scope_errors)
    blocking_reasons.extend(section_errors)
    blocking_reasons.extend(evidence_errors)
    blocking_reasons.extend(personal_action_errors)
    blocking_reasons.extend(hash_status_errors)
    blocking_reasons.extend(side_effect_errors)
    blocking_reasons.extend(production_errors)
    report_status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"

    return {
        "model_id": S2PKT02_M1_MAIL_MODEL_ID,
        "acceptance_id": S2PKT02_ACCEPTANCE_ID,
        "task_id": S2PKT02_TASK_ID,
        "phase": "S2PK",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": report_status,
        **gates,
        "email_contract_id": S2PKT01_EMAIL_CONTRACT_ID,
        "template_version": S2PKT01_TEMPLATE_VERSION,
        "mail_product_id": S2PKT02_MAIL_PRODUCT_ID,
        "primary_board": S2PKT02_PRIMARY_BOARD,
        "cross_cutting_boards": list(S2PKT01_CROSS_CUTTING_BOARDS),
        "required_sections": list(S2PKT02_REQUIRED_SECTIONS),
        "required_action_windows": list(S2PKT02_REQUIRED_ACTION_WINDOWS),
        "source_content_count": len(set(source_content_ids)),
        "section_count": len(set(section_ids)),
        "action_count": len(set(action_ids)),
        "action_windows": action_windows,
        "m1_mail_record": record,
        "m1_mail_hash": m1_hash,
        "s2pkt02_m1_mail_ready": report_status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pkt02_m1_mail(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    mail_contract_report: Mapping[str, Any],
    content_quality_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    m1_mail_record: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PKT02 local M1 mail evidence without production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pkt02-m1-mail"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pkt02_m1_mail_report(
        generated_at=generated_at,
        mail_contract_report=mail_contract_report,
        content_quality_report=content_quality_report,
        content_ledger_report=content_ledger_report,
        action_roi_report=action_roi_report,
        m1_mail_record=m1_mail_record,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "m1_mail_report_path": str(run_dir / "adp-s2pkt02-m1-mail-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pkt02-m1-mail-report.json", report)
        _write_json(state / S2PKT02_REPORT_FILENAME, report)
    return report


def validate_s2pkt02_m1_mail_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PKT02_M1_MAIL_MODEL_ID:
        errors.append("S2PKT02 model_id must be adp-s2pkt02-m1-mail-v1")
    if report.get("task_id") != S2PKT02_TASK_ID:
        errors.append("S2PKT02 task_id must be S2PKT02")
    if report.get("acceptance_id") != S2PKT02_ACCEPTANCE_ID:
        errors.append("S2PKT02 acceptance_id must be ACC-S2PKT02-M1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PKT02 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PKT02_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PKT02 local M1 mail evidence")
    record = report.get("m1_mail_record")
    if not isinstance(record, Mapping):
        errors.append("S2PKT02 m1_mail_record must be an object")
        record = {}
    if report.get("m1_mail_hash") != _s2pkt02_m1_mail_hash(record):
        errors.append("S2PKT02 m1_mail_hash must match m1_mail_record")
    if int(report.get("section_count") or 0) != len(
        {str(section.get("section_id") or "") for section in record.get("sections") or [] if isinstance(section, Mapping)}
    ):
        errors.append("S2PKT02 section_count must match unique section_ids")
    if int(report.get("source_content_count") or 0) != len({str(item) for item in record.get("source_content_ids") or []}):
        errors.append("S2PKT02 source_content_count must match source_content_ids")
    if int(report.get("action_count") or 0) != len({str(item) for item in record.get("action_ids") or []}):
        errors.append("S2PKT02 action_count must match action_ids")
    for gate in S2PKT02_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PKT02 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PKT02 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pkt02_m1_mail_ready") is not True:
        errors.append("passing S2PKT02 report requires s2pkt02_m1_mail_ready=true")
    return errors



def _s2pkt03_m2_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    sections = []
    for section in record.get("sections") or []:
        section_map = section if isinstance(section, Mapping) else {}
        sections.append(
            {
                "action_ids": [str(item) for item in section_map.get("action_ids") or []],
                "content_ids": [str(item) for item in section_map.get("content_ids") or []],
                "evidence_labels": [str(item) for item in section_map.get("evidence_labels") or []],
                "evidence_refs": [str(item) for item in section_map.get("evidence_refs") or []],
                "section_id": str(section_map.get("section_id") or ""),
            }
        )
    sections = sorted(sections, key=lambda item: item["section_id"])
    return {
        "action_ids": [str(item) for item in record.get("action_ids") or []],
        "contract_id": str(record.get("contract_id") or ""),
        "cross_cutting_boards": [str(item) for item in record.get("cross_cutting_boards") or []],
        "mail_product_id": str(record.get("mail_product_id") or ""),
        "primary_board": str(record.get("primary_board") or ""),
        "sections": sections,
        "source_content_ids": [str(item) for item in record.get("source_content_ids") or []],
        "status": str(record.get("status") or ""),
        "template_version": str(record.get("template_version") or ""),
    }


def _s2pkt03_m2_mail_hash(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(_s2pkt03_m2_payload(record), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pkt03_m2_mail_report(
    *,
    generated_at: str,
    mail_contract_report: Mapping[str, Any],
    content_quality_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    m2_mail_record: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PKT03 M2 engineering/product/industry frontier mail evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []

    mail_contract_errors = validate_s2pkt01_mail_contract_report(mail_contract_report)
    mail_contract_gate = (
        "pass"
        if mail_contract_report.get("status") == "pass"
        and mail_contract_report.get("s2pkt01_mail_contract_ready") is True
        and not mail_contract_errors
        else "blocked"
    )
    if mail_contract_gate != "pass":
        blocking_reasons.append("S2PKT01 mail contract report must pass")
        blocking_reasons.extend(mail_contract_errors)

    quality_errors = validate_s2pht05_content_quality_gate_report(content_quality_report)
    content_quality_gate = (
        "pass"
        if content_quality_report.get("status") == "pass"
        and content_quality_report.get("s2pht05_content_quality_gate_ready") is True
        and not quality_errors
        else "blocked"
    )
    if content_quality_gate != "pass":
        blocking_reasons.append("S2PHT05 content quality report must pass")
        blocking_reasons.extend(quality_errors)

    ledger_errors = validate_s2pit04_content_ledger_report(content_ledger_report)
    content_ledger_gate = (
        "pass"
        if content_ledger_report.get("status") == "pass"
        and content_ledger_report.get("s2pit04_content_ledger_ready") is True
        and not ledger_errors
        else "blocked"
    )
    if content_ledger_gate != "pass":
        blocking_reasons.append("S2PIT04 content ledger report must pass")
        blocking_reasons.extend(ledger_errors)

    action_errors = validate_s2pjt03_action_asset_roi_report(action_roi_report)
    action_roi_gate = (
        "pass"
        if action_roi_report.get("status") == "pass"
        and action_roi_report.get("s2pjt03_action_roi_ready") is True
        and not action_errors
        else "blocked"
    )
    if action_roi_gate != "pass":
        blocking_reasons.append("S2PJT03 action/asset/ROI report must pass")
        blocking_reasons.extend(action_errors)

    record = dict(m2_mail_record)
    scope_errors: list[str] = []
    section_errors: list[str] = []
    evidence_errors: list[str] = []
    personal_action_errors: list[str] = []
    hash_status_errors: list[str] = []
    side_effect_errors: list[str] = []

    contracts = [row for row in mail_contract_report.get("mail_contracts") or [] if isinstance(row, Mapping)]
    m2_contract = next((row for row in contracts if row.get("mail_product_id") == S2PKT03_MAIL_PRODUCT_ID), {})
    if not m2_contract:
        scope_errors.append("S2PKT03 requires M2 contract from S2PKT01")
    if record.get("mail_product_id") != S2PKT03_MAIL_PRODUCT_ID:
        scope_errors.append("S2PKT03 m2_mail_record.mail_product_id must be M2")
    if record.get("contract_id") != S2PKT01_EMAIL_CONTRACT_ID:
        scope_errors.append("S2PKT03 M2 contract_id must be EMAIL_LEARNING_V1")
    if record.get("template_version") != S2PKT01_TEMPLATE_VERSION:
        scope_errors.append(f"S2PKT03 M2 template_version must be {S2PKT01_TEMPLATE_VERSION}")
    if record.get("primary_board") != S2PKT03_PRIMARY_BOARD:
        scope_errors.append("S2PKT03 M2 primary_board must be B2")
    cross_boards = [str(item) for item in record.get("cross_cutting_boards") or []]
    if tuple(cross_boards) != S2PKT01_CROSS_CUTTING_BOARDS:
        scope_errors.append("S2PKT03 M2 cross_cutting_boards must be B4/B5/B6")
    for field in ("contract_id", "template_version", "primary_board", "cross_cutting_boards"):
        if m2_contract and record.get(field) != m2_contract.get(field):
            scope_errors.append(f"S2PKT03 M2 {field} must match S2PKT01 M2 contract")

    status = str(record.get("status") or "")
    if status not in S2PKT01_ALLOWED_MAIL_STATUSES:
        hash_status_errors.append("S2PKT03 M2 status must be ready_no_send, previewed, or blocked_no_send")

    ledger_content_ids = {str(row.get("content_id") or "") for row in content_ledger_report.get("ledger_records") or []}
    action_records = [row for row in action_roi_report.get("action_records") or [] if isinstance(row, Mapping)]
    action_horizon_by_id = {str(row.get("action_id") or ""): str(row.get("horizon") or "") for row in action_records}
    source_content_ids = [str(item) for item in record.get("source_content_ids") or []]
    if not source_content_ids:
        section_errors.append("S2PKT03 M2 source_content_ids must be non-empty")
    for content_id in source_content_ids:
        if content_id not in ledger_content_ids:
            section_errors.append(f"S2PKT03 M2 source_content_id {content_id} not traceable to S2PIT04")

    sections = [section for section in record.get("sections") or [] if isinstance(section, Mapping)]
    section_ids = [str(section.get("section_id") or "") for section in sections]
    for section_id in S2PKT03_REQUIRED_SECTIONS:
        if section_id not in section_ids:
            section_errors.append(f"S2PKT03 M2 missing section {section_id}")
    for section in sections:
        section_id = str(section.get("section_id") or "section")
        content_ids = [str(item) for item in section.get("content_ids") or []]
        evidence_refs = [str(item) for item in section.get("evidence_refs") or []]
        evidence_labels = [str(item) for item in section.get("evidence_labels") or []]
        section_action_ids = [str(item) for item in section.get("action_ids") or []]
        if not content_ids:
            section_errors.append(f"{section_id} content_ids must be non-empty")
        for content_id in content_ids:
            if content_id not in source_content_ids:
                section_errors.append(f"{section_id} content_id {content_id} not in M2 source_content_ids")
        if not evidence_refs:
            evidence_errors.append(f"{section_id} evidence_refs must be non-empty")
        for label in evidence_labels:
            if label not in S2PKT01_EVIDENCE_LABELS:
                evidence_errors.append(f"{section_id} evidence label {label} is not allowed")
        if section_id == "engineering_usability" and "FACT" not in evidence_labels:
            evidence_errors.append("engineering_usability requires FACT evidence label")
        if section_id == "reproducibility" and not ({"FACT", "OBSERVATION"} <= set(evidence_labels)):
            evidence_errors.append("reproducibility requires FACT and OBSERVATION evidence labels")
        if section_id == "product_industry_value" and not ({"INFERENCE", "OPINION"} & set(evidence_labels)):
            personal_action_errors.append("product_industry_value requires INFERENCE or OPINION label")
        if section_id == "limitations" and not ({"INFERENCE", "OBSERVATION"} & set(evidence_labels)):
            personal_action_errors.append("limitations requires INFERENCE or OBSERVATION label")
        if section_id == "action_path" and not section_action_ids:
            personal_action_errors.append("action_path requires action_ids")
        for action_id in section_action_ids:
            if action_id not in action_horizon_by_id:
                personal_action_errors.append(f"{section_id} action_id {action_id} not traceable to S2PJT03")

    action_ids = [str(item) for item in record.get("action_ids") or []]
    action_windows = sorted({action_horizon_by_id.get(action_id, "") for action_id in action_ids if action_id in action_horizon_by_id})
    for action_id in action_ids:
        if action_id not in action_horizon_by_id:
            personal_action_errors.append(f"S2PKT03 M2 action_id {action_id} not traceable to S2PJT03")
    missing_windows = [window for window in S2PKT03_REQUIRED_ACTION_WINDOWS if window not in action_windows]
    if missing_windows:
        personal_action_errors.append("S2PKT03 M2 missing required action windows: " + ", ".join(missing_windows))

    m2_hash = _s2pkt03_m2_mail_hash(record)
    if record.get("m2_mail_hash") not in (None, "", m2_hash):
        hash_status_errors.append("S2PKT03 M2 m2_mail_hash must match M2 mail fields")
    record["m2_mail_hash"] = m2_hash

    for key in (
        "real_smtp_sent",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "db_migration_executed",
        "schema_migration_allowed",
        "public_schema_changed",
        "queue_schema_changed",
        "queue_mutation_allowed",
        "ranking_algorithm_changed",
        "source_adapter_changed",
        "email_frontstage_changed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
    ):
        if record.get(key, False) is not False:
            side_effect_errors.append(f"S2PKT03 M2 {key} must be false")

    production_errors: list[str] = []
    for key in (*S2PKT03_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "mail_contract_gate": mail_contract_gate,
        "content_quality_gate": content_quality_gate,
        "content_ledger_gate": content_ledger_gate,
        "action_roi_gate": action_roi_gate,
        "m2_scope_gate": "pass" if not scope_errors else "blocked",
        "section_coverage_gate": "pass" if not section_errors else "blocked",
        "engineering_reproducibility_gate": "pass" if not evidence_errors else "blocked",
        "product_limit_action_gate": "pass" if not personal_action_errors else "blocked",
        "hash_status_gate": "pass" if not hash_status_errors else "blocked",
        "no_side_effect_gate": "pass" if not side_effect_errors and not production_errors else "blocked",
    }
    blocking_reasons.extend(scope_errors)
    blocking_reasons.extend(section_errors)
    blocking_reasons.extend(evidence_errors)
    blocking_reasons.extend(personal_action_errors)
    blocking_reasons.extend(hash_status_errors)
    blocking_reasons.extend(side_effect_errors)
    blocking_reasons.extend(production_errors)
    report_status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"

    return {
        "model_id": S2PKT03_M2_MAIL_MODEL_ID,
        "acceptance_id": S2PKT03_ACCEPTANCE_ID,
        "task_id": S2PKT03_TASK_ID,
        "phase": "S2PK",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": report_status,
        **gates,
        "email_contract_id": S2PKT01_EMAIL_CONTRACT_ID,
        "template_version": S2PKT01_TEMPLATE_VERSION,
        "mail_product_id": S2PKT03_MAIL_PRODUCT_ID,
        "primary_board": S2PKT03_PRIMARY_BOARD,
        "cross_cutting_boards": list(S2PKT01_CROSS_CUTTING_BOARDS),
        "required_sections": list(S2PKT03_REQUIRED_SECTIONS),
        "required_action_windows": list(S2PKT03_REQUIRED_ACTION_WINDOWS),
        "source_content_count": len(set(source_content_ids)),
        "section_count": len(set(section_ids)),
        "action_count": len(set(action_ids)),
        "action_windows": action_windows,
        "m2_mail_record": record,
        "m2_mail_hash": m2_hash,
        "s2pkt03_m2_mail_ready": report_status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pkt03_m2_mail(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    mail_contract_report: Mapping[str, Any],
    content_quality_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    m2_mail_record: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PKT03 local M2 mail evidence without production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pkt03-m2-mail"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pkt03_m2_mail_report(
        generated_at=generated_at,
        mail_contract_report=mail_contract_report,
        content_quality_report=content_quality_report,
        content_ledger_report=content_ledger_report,
        action_roi_report=action_roi_report,
        m2_mail_record=m2_mail_record,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "m2_mail_report_path": str(run_dir / "adp-s2pkt03-m2-mail-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pkt03-m2-mail-report.json", report)
        _write_json(state / S2PKT03_REPORT_FILENAME, report)
    return report


def validate_s2pkt03_m2_mail_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PKT03_M2_MAIL_MODEL_ID:
        errors.append("S2PKT03 model_id must be adp-s2pkt03-m2-mail-v1")
    if report.get("task_id") != S2PKT03_TASK_ID:
        errors.append("S2PKT03 task_id must be S2PKT03")
    if report.get("acceptance_id") != S2PKT03_ACCEPTANCE_ID:
        errors.append("S2PKT03 acceptance_id must be ACC-S2PKT03-M2")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PKT03 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PKT03_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PKT03 local M2 mail evidence")
    record = report.get("m2_mail_record")
    if not isinstance(record, Mapping):
        errors.append("S2PKT03 m2_mail_record must be an object")
        record = {}
    if report.get("m2_mail_hash") != _s2pkt03_m2_mail_hash(record):
        errors.append("S2PKT03 m2_mail_hash must match m2_mail_record")
    if int(report.get("section_count") or 0) != len(
        {str(section.get("section_id") or "") for section in record.get("sections") or [] if isinstance(section, Mapping)}
    ):
        errors.append("S2PKT03 section_count must match unique section_ids")
    if int(report.get("source_content_count") or 0) != len({str(item) for item in record.get("source_content_ids") or []}):
        errors.append("S2PKT03 source_content_count must match source_content_ids")
    if int(report.get("action_count") or 0) != len({str(item) for item in record.get("action_ids") or []}):
        errors.append("S2PKT03 action_count must match action_ids")
    for gate in S2PKT03_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PKT03 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PKT03 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pkt03_m2_mail_ready") is not True:
        errors.append("passing S2PKT03 report requires s2pkt03_m2_mail_ready=true")
    return errors



def _s2pkt04_m3_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    sections = []
    for section in record.get("sections") or []:
        section_map = section if isinstance(section, Mapping) else {}
        sections.append(
            {
                "action_ids": [str(item) for item in section_map.get("action_ids") or []],
                "content_ids": [str(item) for item in section_map.get("content_ids") or []],
                "evidence_labels": [str(item) for item in section_map.get("evidence_labels") or []],
                "evidence_refs": [str(item) for item in section_map.get("evidence_refs") or []],
                "section_id": str(section_map.get("section_id") or ""),
            }
        )
    sections = sorted(sections, key=lambda item: item["section_id"])
    return {
        "action_ids": [str(item) for item in record.get("action_ids") or []],
        "contract_id": str(record.get("contract_id") or ""),
        "cross_cutting_boards": [str(item) for item in record.get("cross_cutting_boards") or []],
        "mail_product_id": str(record.get("mail_product_id") or ""),
        "primary_board": str(record.get("primary_board") or ""),
        "sections": sections,
        "source_content_ids": [str(item) for item in record.get("source_content_ids") or []],
        "status": str(record.get("status") or ""),
        "template_version": str(record.get("template_version") or ""),
    }


def _s2pkt04_m3_mail_hash(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(_s2pkt04_m3_payload(record), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pkt04_m3_mail_report(
    *,
    generated_at: str,
    mail_contract_report: Mapping[str, Any],
    content_quality_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    m3_mail_record: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PKT04 M3 policy/capital/geopolitical frontier mail evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []

    mail_contract_errors = validate_s2pkt01_mail_contract_report(mail_contract_report)
    mail_contract_gate = (
        "pass"
        if mail_contract_report.get("status") == "pass"
        and mail_contract_report.get("s2pkt01_mail_contract_ready") is True
        and not mail_contract_errors
        else "blocked"
    )
    if mail_contract_gate != "pass":
        blocking_reasons.append("S2PKT01 mail contract report must pass")
        blocking_reasons.extend(mail_contract_errors)

    quality_errors = validate_s2pht05_content_quality_gate_report(content_quality_report)
    content_quality_gate = (
        "pass"
        if content_quality_report.get("status") == "pass"
        and content_quality_report.get("s2pht05_content_quality_gate_ready") is True
        and not quality_errors
        else "blocked"
    )
    if content_quality_gate != "pass":
        blocking_reasons.append("S2PHT05 content quality report must pass")
        blocking_reasons.extend(quality_errors)

    ledger_errors = validate_s2pit04_content_ledger_report(content_ledger_report)
    content_ledger_gate = (
        "pass"
        if content_ledger_report.get("status") == "pass"
        and content_ledger_report.get("s2pit04_content_ledger_ready") is True
        and not ledger_errors
        else "blocked"
    )
    if content_ledger_gate != "pass":
        blocking_reasons.append("S2PIT04 content ledger report must pass")
        blocking_reasons.extend(ledger_errors)

    action_errors = validate_s2pjt03_action_asset_roi_report(action_roi_report)
    action_roi_gate = (
        "pass"
        if action_roi_report.get("status") == "pass"
        and action_roi_report.get("s2pjt03_action_roi_ready") is True
        and not action_errors
        else "blocked"
    )
    if action_roi_gate != "pass":
        blocking_reasons.append("S2PJT03 action/asset/ROI report must pass")
        blocking_reasons.extend(action_errors)

    record = dict(m3_mail_record)
    scope_errors: list[str] = []
    section_errors: list[str] = []
    evidence_errors: list[str] = []
    personal_action_errors: list[str] = []
    hash_status_errors: list[str] = []
    side_effect_errors: list[str] = []

    contracts = [row for row in mail_contract_report.get("mail_contracts") or [] if isinstance(row, Mapping)]
    m3_contract = next((row for row in contracts if row.get("mail_product_id") == S2PKT04_MAIL_PRODUCT_ID), {})
    if not m3_contract:
        scope_errors.append("S2PKT04 requires M3 contract from S2PKT01")
    if record.get("mail_product_id") != S2PKT04_MAIL_PRODUCT_ID:
        scope_errors.append("S2PKT04 m3_mail_record.mail_product_id must be M3")
    if record.get("contract_id") != S2PKT01_EMAIL_CONTRACT_ID:
        scope_errors.append("S2PKT04 M3 contract_id must be EMAIL_LEARNING_V1")
    if record.get("template_version") != S2PKT01_TEMPLATE_VERSION:
        scope_errors.append(f"S2PKT04 M3 template_version must be {S2PKT01_TEMPLATE_VERSION}")
    if record.get("primary_board") != S2PKT04_PRIMARY_BOARD:
        scope_errors.append("S2PKT04 M3 primary_board must be B3")
    cross_boards = [str(item) for item in record.get("cross_cutting_boards") or []]
    if tuple(cross_boards) != S2PKT01_CROSS_CUTTING_BOARDS:
        scope_errors.append("S2PKT04 M3 cross_cutting_boards must be B4/B5/B6")
    for field in ("contract_id", "template_version", "primary_board", "cross_cutting_boards"):
        if m3_contract and record.get(field) != m3_contract.get(field):
            scope_errors.append(f"S2PKT04 M3 {field} must match S2PKT01 M3 contract")

    status = str(record.get("status") or "")
    if status not in S2PKT01_ALLOWED_MAIL_STATUSES:
        hash_status_errors.append("S2PKT04 M3 status must be ready_no_send, previewed, or blocked_no_send")

    ledger_content_ids = {str(row.get("content_id") or "") for row in content_ledger_report.get("ledger_records") or []}
    action_records = [row for row in action_roi_report.get("action_records") or [] if isinstance(row, Mapping)]
    action_horizon_by_id = {str(row.get("action_id") or ""): str(row.get("horizon") or "") for row in action_records}
    source_content_ids = [str(item) for item in record.get("source_content_ids") or []]
    if not source_content_ids:
        section_errors.append("S2PKT04 M3 source_content_ids must be non-empty")
    for content_id in source_content_ids:
        if content_id not in ledger_content_ids:
            section_errors.append(f"S2PKT04 M3 source_content_id {content_id} not traceable to S2PIT04")

    sections = [section for section in record.get("sections") or [] if isinstance(section, Mapping)]
    section_ids = [str(section.get("section_id") or "") for section in sections]
    for section_id in S2PKT04_REQUIRED_SECTIONS:
        if section_id not in section_ids:
            section_errors.append(f"S2PKT04 M3 missing section {section_id}")
    for section in sections:
        section_id = str(section.get("section_id") or "section")
        content_ids = [str(item) for item in section.get("content_ids") or []]
        evidence_refs = [str(item) for item in section.get("evidence_refs") or []]
        evidence_labels = [str(item) for item in section.get("evidence_labels") or []]
        section_action_ids = [str(item) for item in section.get("action_ids") or []]
        if not content_ids:
            section_errors.append(f"{section_id} content_ids must be non-empty")
        for content_id in content_ids:
            if content_id not in source_content_ids:
                section_errors.append(f"{section_id} content_id {content_id} not in M3 source_content_ids")
        if not evidence_refs:
            evidence_errors.append(f"{section_id} evidence_refs must be non-empty")
        for label in evidence_labels:
            if label not in S2PKT01_EVIDENCE_LABELS:
                evidence_errors.append(f"{section_id} evidence label {label} is not allowed")
        if section_id == "legal_status" and "FACT" not in evidence_labels:
            evidence_errors.append("legal_status requires FACT evidence label")
        if section_id == "capital_impact" and not ({"FACT", "INFERENCE"} & set(evidence_labels)):
            evidence_errors.append("capital_impact requires FACT or INFERENCE evidence label")
        if section_id == "geopolitical_context" and not ({"FACT", "OBSERVATION"} & set(evidence_labels)):
            evidence_errors.append("geopolitical_context requires FACT or OBSERVATION label")
        if section_id == "personal_impact" and not ({"INFERENCE", "OPINION"} & set(evidence_labels)):
            personal_action_errors.append("personal_impact requires INFERENCE or OPINION label")
        if section_id == "action_path" and not section_action_ids:
            personal_action_errors.append("action_path requires action_ids")
        for action_id in section_action_ids:
            if action_id not in action_horizon_by_id:
                personal_action_errors.append(f"{section_id} action_id {action_id} not traceable to S2PJT03")

    action_ids = [str(item) for item in record.get("action_ids") or []]
    action_windows = sorted({action_horizon_by_id.get(action_id, "") for action_id in action_ids if action_id in action_horizon_by_id})
    for action_id in action_ids:
        if action_id not in action_horizon_by_id:
            personal_action_errors.append(f"S2PKT04 M3 action_id {action_id} not traceable to S2PJT03")
    missing_windows = [window for window in S2PKT04_REQUIRED_ACTION_WINDOWS if window not in action_windows]
    if missing_windows:
        personal_action_errors.append("S2PKT04 M3 missing required action windows: " + ", ".join(missing_windows))

    m3_hash = _s2pkt04_m3_mail_hash(record)
    if record.get("m3_mail_hash") not in (None, "", m3_hash):
        hash_status_errors.append("S2PKT04 M3 m3_mail_hash must match M3 mail fields")
    record["m3_mail_hash"] = m3_hash

    for key in (
        "real_smtp_sent",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "db_migration_executed",
        "schema_migration_allowed",
        "public_schema_changed",
        "queue_schema_changed",
        "queue_mutation_allowed",
        "ranking_algorithm_changed",
        "source_adapter_changed",
        "email_frontstage_changed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
    ):
        if record.get(key, False) is not False:
            side_effect_errors.append(f"S2PKT04 M3 {key} must be false")

    production_errors: list[str] = []
    for key in (*S2PKT04_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "mail_contract_gate": mail_contract_gate,
        "content_quality_gate": content_quality_gate,
        "content_ledger_gate": content_ledger_gate,
        "action_roi_gate": action_roi_gate,
        "m3_scope_gate": "pass" if not scope_errors else "blocked",
        "section_coverage_gate": "pass" if not section_errors else "blocked",
        "legal_capital_geo_gate": "pass" if not evidence_errors else "blocked",
        "personal_impact_action_gate": "pass" if not personal_action_errors else "blocked",
        "hash_status_gate": "pass" if not hash_status_errors else "blocked",
        "no_side_effect_gate": "pass" if not side_effect_errors and not production_errors else "blocked",
    }
    blocking_reasons.extend(scope_errors)
    blocking_reasons.extend(section_errors)
    blocking_reasons.extend(evidence_errors)
    blocking_reasons.extend(personal_action_errors)
    blocking_reasons.extend(hash_status_errors)
    blocking_reasons.extend(side_effect_errors)
    blocking_reasons.extend(production_errors)
    report_status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"

    return {
        "model_id": S2PKT04_M3_MAIL_MODEL_ID,
        "acceptance_id": S2PKT04_ACCEPTANCE_ID,
        "task_id": S2PKT04_TASK_ID,
        "phase": "S2PK",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": report_status,
        **gates,
        "email_contract_id": S2PKT01_EMAIL_CONTRACT_ID,
        "template_version": S2PKT01_TEMPLATE_VERSION,
        "mail_product_id": S2PKT04_MAIL_PRODUCT_ID,
        "primary_board": S2PKT04_PRIMARY_BOARD,
        "cross_cutting_boards": list(S2PKT01_CROSS_CUTTING_BOARDS),
        "required_sections": list(S2PKT04_REQUIRED_SECTIONS),
        "required_action_windows": list(S2PKT04_REQUIRED_ACTION_WINDOWS),
        "source_content_count": len(set(source_content_ids)),
        "section_count": len(set(section_ids)),
        "action_count": len(set(action_ids)),
        "action_windows": action_windows,
        "m3_mail_record": record,
        "m3_mail_hash": m3_hash,
        "s2pkt04_m3_mail_ready": report_status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pkt04_m3_mail(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    mail_contract_report: Mapping[str, Any],
    content_quality_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    m3_mail_record: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PKT04 local M3 mail evidence without production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pkt04-m3-mail"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pkt04_m3_mail_report(
        generated_at=generated_at,
        mail_contract_report=mail_contract_report,
        content_quality_report=content_quality_report,
        content_ledger_report=content_ledger_report,
        action_roi_report=action_roi_report,
        m3_mail_record=m3_mail_record,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "m3_mail_report_path": str(run_dir / "adp-s2pkt04-m3-mail-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pkt04-m3-mail-report.json", report)
        _write_json(state / S2PKT04_REPORT_FILENAME, report)
    return report


def validate_s2pkt04_m3_mail_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PKT04_M3_MAIL_MODEL_ID:
        errors.append("S2PKT04 model_id must be adp-s2pkt04-m3-mail-v1")
    if report.get("task_id") != S2PKT04_TASK_ID:
        errors.append("S2PKT04 task_id must be S2PKT04")
    if report.get("acceptance_id") != S2PKT04_ACCEPTANCE_ID:
        errors.append("S2PKT04 acceptance_id must be ACC-S2PKT04-M3")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PKT04 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PKT04_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PKT04 local M3 mail evidence")
    record = report.get("m3_mail_record")
    if not isinstance(record, Mapping):
        errors.append("S2PKT04 m3_mail_record must be an object")
        record = {}
    if report.get("m3_mail_hash") != _s2pkt04_m3_mail_hash(record):
        errors.append("S2PKT04 m3_mail_hash must match m3_mail_record")
    if int(report.get("section_count") or 0) != len(
        {str(section.get("section_id") or "") for section in record.get("sections") or [] if isinstance(section, Mapping)}
    ):
        errors.append("S2PKT04 section_count must match unique section_ids")
    if int(report.get("source_content_count") or 0) != len({str(item) for item in record.get("source_content_ids") or []}):
        errors.append("S2PKT04 source_content_count must match source_content_ids")
    if int(report.get("action_count") or 0) != len({str(item) for item in record.get("action_ids") or []}):
        errors.append("S2PKT04 action_count must match action_ids")
    for gate in S2PKT04_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PKT04 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PKT04 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pkt04_m3_mail_ready") is not True:
        errors.append("passing S2PKT04 report requires s2pkt04_m3_mail_ready=true")
    return errors


def _s2pkt05_m4_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    sections = []
    for section in record.get("sections") or []:
        section_map = section if isinstance(section, Mapping) else {}
        sections.append(
            {
                "action_ids": [str(item) for item in section_map.get("action_ids") or []],
                "content_ids": [str(item) for item in section_map.get("content_ids") or []],
                "evidence_labels": [str(item) for item in section_map.get("evidence_labels") or []],
                "evidence_refs": [str(item) for item in section_map.get("evidence_refs") or []],
                "review_content_ids": [str(item) for item in section_map.get("review_content_ids") or []],
                "section_id": str(section_map.get("section_id") or ""),
            }
        )
    sections = sorted(sections, key=lambda item: item["section_id"])
    terminal_inputs = []
    for item in record.get("terminal_inputs") or []:
        item_map = item if isinstance(item, Mapping) else {}
        terminal_inputs.append(
            {
                "mail_hash": str(item_map.get("mail_hash") or ""),
                "mail_product_id": str(item_map.get("mail_product_id") or ""),
                "ready": bool(item_map.get("ready")),
                "status": str(item_map.get("status") or ""),
                "task_id": str(item_map.get("task_id") or ""),
            }
        )
    terminal_inputs = sorted(terminal_inputs, key=lambda item: item["mail_product_id"])
    schedule_windows = []
    for item in record.get("schedule_windows") or []:
        item_map = item if isinstance(item, Mapping) else {}
        schedule_windows.append(
            {
                "mail_product_id": str(item_map.get("mail_product_id") or ""),
                "time": str(item_map.get("time") or ""),
            }
        )
    schedule_windows = sorted(schedule_windows, key=lambda item: item["mail_product_id"])
    watermark = record.get("watermark") if isinstance(record.get("watermark"), Mapping) else {}
    return {
        "action_ids": [str(item) for item in record.get("action_ids") or []],
        "contract_id": str(record.get("contract_id") or ""),
        "cross_cutting_boards": [str(item) for item in record.get("cross_cutting_boards") or []],
        "cycle_id": str(record.get("cycle_id") or ""),
        "duplicate_count": int(record.get("duplicate_count") or 0),
        "legacy_five_mail_active": bool(record.get("legacy_five_mail_active")),
        "mail_product_id": str(record.get("mail_product_id") or ""),
        "primary_board": str(record.get("primary_board") or ""),
        "review_content_ids": [str(item) for item in record.get("review_content_ids") or []],
        "schedule_windows": schedule_windows,
        "sections": sections,
        "silent_drop_count": int(record.get("silent_drop_count") or 0),
        "status": str(record.get("status") or ""),
        "template_version": str(record.get("template_version") or ""),
        "terminal_inputs": terminal_inputs,
        "watermark": {
            "cycle_id": str(watermark.get("cycle_id") or ""),
            "late_arrival_policy": str(watermark.get("late_arrival_policy") or ""),
            "terminal_mail_products": [str(item) for item in watermark.get("terminal_mail_products") or []],
        },
    }


def _s2pkt05_m4_mail_hash(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(_s2pkt05_m4_payload(record), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pkt05_m4_mail_report(
    *,
    generated_at: str,
    mail_contract_report: Mapping[str, Any],
    m1_mail_report: Mapping[str, Any],
    m2_mail_report: Mapping[str, Any],
    m3_mail_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    review_schedule_report: Mapping[str, Any],
    m4_orchestration_record: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PKT05 M4 3+1 orchestration and watermark evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []

    mail_contract_errors = validate_s2pkt01_mail_contract_report(mail_contract_report)
    mail_contract_gate = (
        "pass"
        if mail_contract_report.get("status") == "pass"
        and mail_contract_report.get("s2pkt01_mail_contract_ready") is True
        and not mail_contract_errors
        else "blocked"
    )
    if mail_contract_gate != "pass":
        blocking_reasons.append("S2PKT01 mail contract report must pass")
        blocking_reasons.extend(mail_contract_errors)

    terminal_specs = (
        ("M1", m1_mail_report, validate_s2pkt02_m1_mail_report, "s2pkt02_m1_mail_ready", "m1_mail_hash", "S2PKT02"),
        ("M2", m2_mail_report, validate_s2pkt03_m2_mail_report, "s2pkt03_m2_mail_ready", "m2_mail_hash", "S2PKT03"),
        ("M3", m3_mail_report, validate_s2pkt04_m3_mail_report, "s2pkt04_m3_mail_ready", "m3_mail_hash", "S2PKT04"),
    )
    terminal_errors_by_mail: dict[str, list[str]] = {}
    terminal_hash_by_mail: dict[str, str] = {}
    terminal_gate_by_mail: dict[str, str] = {}
    for mail_id, report, validator, ready_key, hash_key, task_id in terminal_specs:
        errors = validator(report)
        terminal_hash_by_mail[mail_id] = str(report.get(hash_key) or "")
        if report.get("status") == "pass" and report.get(ready_key) is True and report.get("mail_product_id") == mail_id and not errors:
            terminal_gate_by_mail[mail_id] = "pass"
        else:
            terminal_gate_by_mail[mail_id] = "blocked"
            terminal_errors_by_mail[mail_id] = [f"{task_id} {mail_id} mail report must pass and be terminal"]
            terminal_errors_by_mail[mail_id].extend(errors)
            blocking_reasons.extend(terminal_errors_by_mail[mail_id])

    ledger_errors = validate_s2pit04_content_ledger_report(content_ledger_report)
    ledger_content_ids = {str(row.get("content_id") or "") for row in content_ledger_report.get("ledger_records") or []}
    if content_ledger_report.get("status") != "pass" or content_ledger_report.get("s2pit04_content_ledger_ready") is not True or ledger_errors:
        blocking_reasons.append("S2PIT04 content ledger report must pass")
        blocking_reasons.extend(ledger_errors)

    action_errors = validate_s2pjt03_action_asset_roi_report(action_roi_report)
    action_records = [row for row in action_roi_report.get("action_records") or [] if isinstance(row, Mapping)]
    action_horizon_by_id = {str(row.get("action_id") or ""): str(row.get("horizon") or "") for row in action_records}
    if action_roi_report.get("status") != "pass" or action_roi_report.get("s2pjt03_action_roi_ready") is not True or action_errors:
        blocking_reasons.append("S2PJT03 action/asset/ROI report must pass")
        blocking_reasons.extend(action_errors)

    review_errors = validate_s2pjt02_review_schedule_report(review_schedule_report)
    review_content_ids = {str(row.get("content_id") or "") for row in review_schedule_report.get("due_queue_records") or []}
    if review_schedule_report.get("status") != "pass" or review_schedule_report.get("s2pjt02_review_schedule_ready") is not True or review_errors:
        blocking_reasons.append("S2PJT02 review schedule report must pass")
        blocking_reasons.extend(review_errors)

    record = dict(m4_orchestration_record)
    scope_errors: list[str] = []
    schedule_errors: list[str] = []
    watermark_errors: list[str] = []
    duplicate_errors: list[str] = []
    section_errors: list[str] = []
    synthesis_errors: list[str] = []
    action_review_errors: list[str] = []
    hash_status_errors: list[str] = []
    side_effect_errors: list[str] = []

    contracts = [row for row in mail_contract_report.get("mail_contracts") or [] if isinstance(row, Mapping)]
    m4_contract = next((row for row in contracts if row.get("mail_product_id") == S2PKT05_MAIL_PRODUCT_ID), {})
    if not m4_contract:
        scope_errors.append("S2PKT05 requires M4 contract from S2PKT01")
    if record.get("mail_product_id") != S2PKT05_MAIL_PRODUCT_ID:
        scope_errors.append("S2PKT05 m4_orchestration_record.mail_product_id must be M4")
    if record.get("contract_id") != S2PKT01_EMAIL_CONTRACT_ID:
        scope_errors.append("S2PKT05 M4 contract_id must be EMAIL_LEARNING_V1")
    if record.get("template_version") != S2PKT01_TEMPLATE_VERSION:
        scope_errors.append(f"S2PKT05 M4 template_version must be {S2PKT01_TEMPLATE_VERSION}")
    if record.get("primary_board") != S2PKT05_PRIMARY_BOARD:
        scope_errors.append("S2PKT05 M4 primary_board must be B1-B6")
    cross_boards = [str(item) for item in record.get("cross_cutting_boards") or []]
    if tuple(cross_boards) != S2PKT01_CROSS_CUTTING_BOARDS:
        scope_errors.append("S2PKT05 M4 cross_cutting_boards must be B4/B5/B6")
    for field in ("contract_id", "template_version", "primary_board", "cross_cutting_boards"):
        if m4_contract and record.get(field) != m4_contract.get(field):
            scope_errors.append(f"S2PKT05 M4 {field} must match S2PKT01 M4 contract")

    status = str(record.get("status") or "")
    if status not in S2PKT01_ALLOWED_MAIL_STATUSES:
        hash_status_errors.append("S2PKT05 M4 status must be ready_no_send, previewed, or blocked_no_send")

    terminal_inputs = [row for row in record.get("terminal_inputs") or [] if isinstance(row, Mapping)]
    terminal_input_by_mail = {str(row.get("mail_product_id") or ""): row for row in terminal_inputs}
    for mail_id in S2PKT05_REQUIRED_TERMINAL_MAILS:
        terminal = terminal_input_by_mail.get(mail_id)
        if not terminal:
            watermark_errors.append(f"S2PKT05 M4 missing terminal input {mail_id}")
            continue
        if terminal.get("status") != "pass" or terminal.get("ready") is not True:
            watermark_errors.append(f"S2PKT05 M4 terminal input {mail_id} must be pass and ready")
        if terminal.get("mail_hash") != terminal_hash_by_mail.get(mail_id):
            watermark_errors.append(f"S2PKT05 M4 terminal input {mail_id} hash must match upstream mail report")

    schedule_by_mail = {
        str(row.get("mail_product_id") or ""): str(row.get("time") or "")
        for row in record.get("schedule_windows") or []
        if isinstance(row, Mapping)
    }
    expected_schedule = dict(item.split("=", 1) for item in S2PKT05_DEFAULT_STAGGERED_WINDOWS)
    for mail_id, expected_time in expected_schedule.items():
        if schedule_by_mail.get(mail_id) != expected_time:
            schedule_errors.append(f"S2PKT05 {mail_id} scheduled window must be {expected_time}")
    if len(set(schedule_by_mail.values())) != len(schedule_by_mail):
        schedule_errors.append("S2PKT05 scheduled windows must be staggered and unique")

    cycle_id = str(record.get("cycle_id") or "")
    watermark = record.get("watermark") if isinstance(record.get("watermark"), Mapping) else {}
    watermark_mail_products = [str(item) for item in watermark.get("terminal_mail_products") or []]
    if not cycle_id:
        watermark_errors.append("S2PKT05 M4 cycle_id is required")
    if watermark.get("cycle_id") != cycle_id:
        watermark_errors.append("S2PKT05 M4 watermark.cycle_id must match cycle_id")
    if tuple(watermark_mail_products) != S2PKT05_REQUIRED_TERMINAL_MAILS:
        watermark_errors.append("S2PKT05 M4 watermark must wait for M1/M2/M3 terminal products")
    if str(watermark.get("late_arrival_policy") or "") != "revision_required_no_send":
        watermark_errors.append("S2PKT05 M4 late_arrival_policy must be revision_required_no_send")

    if int(record.get("duplicate_count") or 0) != 0:
        duplicate_errors.append("S2PKT05 M4 duplicate_count must be 0")
    if int(record.get("silent_drop_count") or 0) != 0:
        duplicate_errors.append("S2PKT05 M4 silent_drop_count must be 0")
    if record.get("legacy_five_mail_active", False) is not False:
        duplicate_errors.append("S2PKT05 M4 legacy_five_mail_active must be false")

    sections = [section for section in record.get("sections") or [] if isinstance(section, Mapping)]
    section_ids = [str(section.get("section_id") or "") for section in sections]
    for section_id in S2PKT05_REQUIRED_SECTIONS:
        if section_id not in section_ids:
            section_errors.append(f"S2PKT05 M4 missing section {section_id}")
    for section in sections:
        section_id = str(section.get("section_id") or "section")
        content_ids = [str(item) for item in section.get("content_ids") or []]
        evidence_refs = [str(item) for item in section.get("evidence_refs") or []]
        evidence_labels = [str(item) for item in section.get("evidence_labels") or []]
        section_action_ids = [str(item) for item in section.get("action_ids") or []]
        section_review_ids = [str(item) for item in section.get("review_content_ids") or []]
        if not content_ids:
            section_errors.append(f"{section_id} content_ids must be non-empty")
        for content_id in content_ids:
            if content_id not in ledger_content_ids:
                section_errors.append(f"{section_id} content_id {content_id} not traceable to S2PIT04")
        if not evidence_refs:
            synthesis_errors.append(f"{section_id} evidence_refs must be non-empty")
        for label in evidence_labels:
            if label not in S2PKT01_EVIDENCE_LABELS:
                synthesis_errors.append(f"{section_id} evidence label {label} is not allowed")
        if section_id in {"cross_source_resonance", "contradictions", "era_mainline"} and not ({"FACT", "INFERENCE", "OBSERVATION"} & set(evidence_labels)):
            synthesis_errors.append(f"{section_id} requires FACT, INFERENCE, or OBSERVATION label")
        if section_id == "personal_action_mix" and not section_action_ids:
            action_review_errors.append("personal_action_mix requires action_ids")
        if section_id == "review_reminders" and not section_review_ids:
            action_review_errors.append("review_reminders requires review_content_ids")
        for action_id in section_action_ids:
            if action_id not in action_horizon_by_id:
                action_review_errors.append(f"{section_id} action_id {action_id} not traceable to S2PJT03")
        for review_id in section_review_ids:
            if review_id not in review_content_ids:
                action_review_errors.append(f"{section_id} review_content_id {review_id} not traceable to S2PJT02 due queue")

    action_ids = [str(item) for item in record.get("action_ids") or []]
    for action_id in action_ids:
        if action_id not in action_horizon_by_id:
            action_review_errors.append(f"S2PKT05 M4 action_id {action_id} not traceable to S2PJT03")
    record_review_ids = [str(item) for item in record.get("review_content_ids") or []]
    for review_id in record_review_ids:
        if review_id not in review_content_ids:
            action_review_errors.append(f"S2PKT05 M4 review_content_id {review_id} not traceable to S2PJT02 due queue")

    m4_hash = _s2pkt05_m4_mail_hash(record)
    if record.get("m4_mail_hash") not in (None, "", m4_hash):
        hash_status_errors.append("S2PKT05 M4 m4_mail_hash must match M4 orchestration fields")
    record["m4_mail_hash"] = m4_hash

    for key in (
        "real_smtp_sent",
        "smtp_transport_allowed",
        "scheduler_enabled",
        "release_upload_allowed",
        "db_migration_executed",
        "schema_migration_allowed",
        "public_schema_changed",
        "queue_schema_changed",
        "queue_mutation_allowed",
        "ranking_algorithm_changed",
        "source_adapter_changed",
        "email_frontstage_changed",
        "v7_1_current_switched",
        "v7_2_contract_files_changed",
    ):
        if record.get(key, False) is not False:
            side_effect_errors.append(f"S2PKT05 M4 {key} must be false")

    production_errors: list[str] = []
    for key in (*S2PKT05_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "mail_contract_gate": mail_contract_gate,
        "m1_terminal_gate": terminal_gate_by_mail.get("M1", "blocked"),
        "m2_terminal_gate": terminal_gate_by_mail.get("M2", "blocked"),
        "m3_terminal_gate": terminal_gate_by_mail.get("M3", "blocked"),
        "m4_scope_gate": "pass" if not scope_errors else "blocked",
        "staggered_schedule_gate": "pass" if not schedule_errors else "blocked",
        "watermark_gate": "pass" if not watermark_errors else "blocked",
        "duplicate_suppression_gate": "pass" if not duplicate_errors else "blocked",
        "section_coverage_gate": "pass" if not section_errors else "blocked",
        "cross_board_synthesis_gate": "pass" if not synthesis_errors else "blocked",
        "action_review_gate": "pass" if not action_review_errors else "blocked",
        "hash_status_gate": "pass" if not hash_status_errors else "blocked",
        "no_side_effect_gate": "pass" if not side_effect_errors and not production_errors else "blocked",
    }
    blocking_reasons.extend(scope_errors)
    blocking_reasons.extend(schedule_errors)
    blocking_reasons.extend(watermark_errors)
    blocking_reasons.extend(duplicate_errors)
    blocking_reasons.extend(section_errors)
    blocking_reasons.extend(synthesis_errors)
    blocking_reasons.extend(action_review_errors)
    blocking_reasons.extend(hash_status_errors)
    blocking_reasons.extend(side_effect_errors)
    blocking_reasons.extend(production_errors)
    report_status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"

    return {
        "model_id": S2PKT05_M4_MAIL_MODEL_ID,
        "acceptance_id": S2PKT05_ACCEPTANCE_ID,
        "task_id": S2PKT05_TASK_ID,
        "phase": "S2PK",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": report_status,
        **gates,
        "email_contract_id": S2PKT01_EMAIL_CONTRACT_ID,
        "template_version": S2PKT01_TEMPLATE_VERSION,
        "mail_product_id": S2PKT05_MAIL_PRODUCT_ID,
        "primary_board": S2PKT05_PRIMARY_BOARD,
        "cross_cutting_boards": list(S2PKT01_CROSS_CUTTING_BOARDS),
        "required_terminal_mails": list(S2PKT05_REQUIRED_TERMINAL_MAILS),
        "required_sections": list(S2PKT05_REQUIRED_SECTIONS),
        "default_staggered_windows": list(S2PKT05_DEFAULT_STAGGERED_WINDOWS),
        "terminal_mail_count": len(set(terminal_input_by_mail) & set(S2PKT05_REQUIRED_TERMINAL_MAILS)),
        "section_count": len(set(section_ids)),
        "action_count": len(set(action_ids)),
        "review_reminder_count": len(set(record_review_ids)),
        "cycle_id": cycle_id,
        "m4_orchestration_record": record,
        "m4_mail_hash": m4_hash,
        "s2pkt05_m4_mail_ready": report_status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pkt05_m4_mail(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    mail_contract_report: Mapping[str, Any],
    m1_mail_report: Mapping[str, Any],
    m2_mail_report: Mapping[str, Any],
    m3_mail_report: Mapping[str, Any],
    content_ledger_report: Mapping[str, Any],
    action_roi_report: Mapping[str, Any],
    review_schedule_report: Mapping[str, Any],
    m4_orchestration_record: Mapping[str, Any],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PKT05 local M4 3+1 orchestration evidence without sending mail."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pkt05-m4-mail"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pkt05_m4_mail_report(
        generated_at=generated_at,
        mail_contract_report=mail_contract_report,
        m1_mail_report=m1_mail_report,
        m2_mail_report=m2_mail_report,
        m3_mail_report=m3_mail_report,
        content_ledger_report=content_ledger_report,
        action_roi_report=action_roi_report,
        review_schedule_report=review_schedule_report,
        m4_orchestration_record=m4_orchestration_record,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "m4_mail_report_path": str(run_dir / "adp-s2pkt05-m4-mail-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pkt05-m4-mail-report.json", report)
        _write_json(state / S2PKT05_REPORT_FILENAME, report)
    return report


def validate_s2pkt05_m4_mail_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PKT05_M4_MAIL_MODEL_ID:
        errors.append("S2PKT05 model_id must be adp-s2pkt05-m4-mail-v1")
    if report.get("task_id") != S2PKT05_TASK_ID:
        errors.append("S2PKT05 task_id must be S2PKT05")
    if report.get("acceptance_id") != S2PKT05_ACCEPTANCE_ID:
        errors.append("S2PKT05 acceptance_id must be ACC-S2PKT05-M4")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PKT05 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PKT05_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PKT05 local M4 mail orchestration evidence")
    record = report.get("m4_orchestration_record")
    if not isinstance(record, Mapping):
        errors.append("S2PKT05 m4_orchestration_record must be an object")
        record = {}
    if report.get("m4_mail_hash") != _s2pkt05_m4_mail_hash(record):
        errors.append("S2PKT05 m4_mail_hash must match m4_orchestration_record")
    if int(report.get("section_count") or 0) != len(
        {str(section.get("section_id") or "") for section in record.get("sections") or [] if isinstance(section, Mapping)}
    ):
        errors.append("S2PKT05 section_count must match unique section_ids")
    if int(report.get("action_count") or 0) != len({str(item) for item in record.get("action_ids") or []}):
        errors.append("S2PKT05 action_count must match action_ids")
    if int(report.get("review_reminder_count") or 0) != len({str(item) for item in record.get("review_content_ids") or []}):
        errors.append("S2PKT05 review_reminder_count must match review_content_ids")
    for gate in S2PKT05_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PKT05 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PKT05 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pkt05_m4_mail_ready") is not True:
        errors.append("passing S2PKT05 report requires s2pkt05_m4_mail_ready=true")
    return errors


def _state_history_states(record: Mapping[str, Any]) -> list[str]:
    states: list[str] = []
    for entry in record.get("state_history") or []:
        if isinstance(entry, Mapping):
            state = str(entry.get("state") or "")
        else:
            state = str(entry or "")
        if state:
            states.append(state)
    return states


def _state_history_timestamps(record: Mapping[str, Any]) -> list[str]:
    timestamps: list[str] = []
    for entry in record.get("state_history") or []:
        if isinstance(entry, Mapping) and entry.get("changed_at"):
            timestamps.append(str(entry["changed_at"]))
    return timestamps


def build_s2pjt01_lifecycle_state_report(
    *,
    generated_at: str,
    runtime_dashboard_report: Mapping[str, Any],
    lifecycle_records: Sequence[Mapping[str, Any]],
    migration_plan: Mapping[str, Any] | None = None,
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build S2PJT01 local-only review/action/ROI lifecycle state evidence."""

    migration = dict(migration_plan or {})
    production_gate = dict(production_gate_state or {})
    runtime_errors = validate_s2pit02_runtime_dashboard_report(runtime_dashboard_report)
    runtime_gate = (
        "pass"
        if runtime_dashboard_report.get("status") == "pass"
        and runtime_dashboard_report.get("s2pit02_runtime_dashboard_ready") is True
        and not runtime_errors
        else "blocked"
    )
    blocking_reasons: list[str] = []
    if runtime_gate != "pass":
        blocking_reasons.append("S2PIT02 runtime dashboard report must pass")
        blocking_reasons.extend(runtime_errors)

    content_ids: set[str] = set()
    duplicate_content_ids: set[str] = set()
    states_observed: set[str] = set()
    state_counts = {state: 0 for state in S2PJT01_REQUIRED_STATES}
    append_only_errors: list[str] = []
    side_effect_errors: list[str] = []
    ledger_types_observed: set[str] = set()

    for index, record in enumerate(lifecycle_records):
        content_id = str(record.get("content_id") or "")
        current_state = str(record.get("current_state") or "")
        if not content_id:
            append_only_errors.append(f"record {index} missing content_id")
        elif content_id in content_ids:
            duplicate_content_ids.add(content_id)
        content_ids.add(content_id)
        history_states = _state_history_states(record)
        states_observed.update(history_states)
        if current_state:
            states_observed.add(current_state)
        if current_state in state_counts:
            state_counts[current_state] += 1
        if not history_states:
            append_only_errors.append(f"{content_id or index} state_history must be non-empty")
        elif history_states[-1] != current_state:
            append_only_errors.append(f"{content_id or index} final state_history entry must equal current_state")
        timestamps = _state_history_timestamps(record)
        if timestamps and timestamps != sorted(timestamps):
            append_only_errors.append(f"{content_id or index} state_history timestamps must be non-decreasing")
        for ledger_ref in record.get("ledger_refs") or []:
            if isinstance(ledger_ref, Mapping) and ledger_ref.get("ledger_type"):
                ledger_types_observed.add(str(ledger_ref["ledger_type"]))
        for key in ("queue_mutation_allowed", "ranking_algorithm_changed", "public_schema_changed", "real_smtp_sent"):
            if record.get(key, False) is not False:
                side_effect_errors.append(f"{content_id or index}.{key} must be false")

    missing_states = [state for state in S2PJT01_REQUIRED_STATES if state not in states_observed]
    missing_ledgers = [ledger for ledger in S2PJT01_REQUIRED_LEDGER_TYPES if ledger not in ledger_types_observed]
    if duplicate_content_ids:
        append_only_errors.append("duplicate content_id: " + ", ".join(sorted(duplicate_content_ids)))
    count_conservation_errors: list[str] = []
    if sum(state_counts.values()) != len(content_ids):
        count_conservation_errors.append("state count sum must equal unique content count")
    migration_errors: list[str] = []
    if migration.get("dry_run_only") is not True:
        migration_errors.append("migration_plan.dry_run_only must be true")
    if migration.get("rollback_supported") is not True:
        migration_errors.append("migration_plan.rollback_supported must be true")
    if migration.get("db_migration_executed", False) is not False:
        migration_errors.append("migration_plan.db_migration_executed must be false")
    if migration.get("public_schema_changed", False) is not False:
        migration_errors.append("migration_plan.public_schema_changed must be false")
    if migration.get("count_conservation_checked") is not True:
        migration_errors.append("migration_plan.count_conservation_checked must be true")

    production_errors: list[str] = []
    for key in (*S2PJT01_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "runtime_dashboard_gate": runtime_gate,
        "state_coverage_gate": "pass" if not missing_states else "blocked",
        "append_only_history_gate": "pass" if not append_only_errors else "blocked",
        "count_conservation_gate": "pass" if not count_conservation_errors else "blocked",
        "ledger_mapping_gate": "pass" if not missing_ledgers else "blocked",
        "migration_plan_gate": "pass" if not migration_errors else "blocked",
        "no_side_effect_gate": "pass" if not side_effect_errors and not production_errors else "blocked",
    }
    blocking_reasons.extend(f"missing lifecycle state: {state}" for state in missing_states)
    blocking_reasons.extend(append_only_errors)
    blocking_reasons.extend(count_conservation_errors)
    blocking_reasons.extend(f"missing ledger type: {ledger}" for ledger in missing_ledgers)
    blocking_reasons.extend(migration_errors)
    blocking_reasons.extend(side_effect_errors)
    blocking_reasons.extend(production_errors)
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"

    return {
        "model_id": S2PJT01_LIFECYCLE_STATE_MODEL_ID,
        "acceptance_id": S2PJT01_ACCEPTANCE_ID,
        "task_id": S2PJT01_TASK_ID,
        "phase": "S2PJ",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        **gates,
        "required_states": list(S2PJT01_REQUIRED_STATES),
        "states_observed": sorted(states_observed),
        "required_ledger_types": list(S2PJT01_REQUIRED_LEDGER_TYPES),
        "ledger_types_observed": sorted(ledger_types_observed),
        "content_count": len(content_ids),
        "state_counts": state_counts,
        "count_conservation_strategy": migration.get("count_conservation_strategy", "pre_post_state_count_match"),
        "migration_plan": migration,
        "lifecycle_records": [dict(record) for record in lifecycle_records],
        "s2pjt01_lifecycle_state_ready": status == "pass",
        "review_scheduler_enabled": False,
        "actual_roi_calculation_enabled": False,
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pjt01_lifecycle_state(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    runtime_dashboard_report: Mapping[str, Any],
    lifecycle_records: Sequence[Mapping[str, Any]],
    migration_plan: Mapping[str, Any] | None = None,
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PJT01 lifecycle state evidence without migration or production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pjt01-lifecycle-state"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pjt01_lifecycle_state_report(
        generated_at=generated_at,
        runtime_dashboard_report=runtime_dashboard_report,
        lifecycle_records=lifecycle_records,
        migration_plan=migration_plan,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "lifecycle_state_report_path": str(run_dir / "adp-s2pjt01-lifecycle-state-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pjt01-lifecycle-state-report.json", report)
        _write_json(state / S2PJT01_REPORT_FILENAME, report)
    return report


def validate_s2pjt01_lifecycle_state_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PJT01_LIFECYCLE_STATE_MODEL_ID:
        errors.append("S2PJT01 model_id must be adp-s2pjt01-lifecycle-state-v1")
    if report.get("task_id") != S2PJT01_TASK_ID:
        errors.append("S2PJT01 task_id must be S2PJT01")
    if report.get("acceptance_id") != S2PJT01_ACCEPTANCE_ID:
        errors.append("S2PJT01 acceptance_id must be ACC-S2PJT01-LIFECYCLE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PJT01 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PJT01_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
        "review_scheduler_enabled",
        "actual_roi_calculation_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PJT01 local lifecycle state evidence")
    records = report.get("lifecycle_records")
    if not isinstance(records, list) or not records:
        errors.append("S2PJT01 lifecycle_records must be a non-empty list")
    missing_states = [state for state in S2PJT01_REQUIRED_STATES if state not in set(report.get("states_observed") or [])]
    if missing_states:
        errors.append("S2PJT01 missing lifecycle states: " + ", ".join(missing_states))
    missing_ledgers = [ledger for ledger in S2PJT01_REQUIRED_LEDGER_TYPES if ledger not in set(report.get("ledger_types_observed") or [])]
    if missing_ledgers:
        errors.append("S2PJT01 missing ledger types: " + ", ".join(missing_ledgers))
    state_counts = report.get("state_counts")
    if not isinstance(state_counts, Mapping):
        errors.append("S2PJT01 state_counts must be a mapping")
        state_counts = {}
    if sum(int(value or 0) for value in state_counts.values()) != int(report.get("content_count") or 0):
        errors.append("S2PJT01 state_counts must conserve content_count")
    migration = report.get("migration_plan")
    if not isinstance(migration, Mapping):
        errors.append("S2PJT01 migration_plan must be a mapping")
        migration = {}
    if migration.get("dry_run_only") is not True:
        errors.append("S2PJT01 migration_plan.dry_run_only must be true")
    if migration.get("rollback_supported") is not True:
        errors.append("S2PJT01 migration_plan.rollback_supported must be true")
    if migration.get("db_migration_executed", False) is not False:
        errors.append("S2PJT01 migration_plan.db_migration_executed must be false")
    if migration.get("public_schema_changed", False) is not False:
        errors.append("S2PJT01 migration_plan.public_schema_changed must be false")
    for gate in S2PJT01_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PJT01 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PJT01 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pjt01_lifecycle_state_ready") is not True:
        errors.append("passing S2PJT01 report requires s2pjt01_lifecycle_state_ready=true")
    return errors


def _parse_iso_date(value: Any) -> Date | None:
    try:
        return Date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _s2pjt02_queue_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {
            "content_id": str(row.get("content_id") or ""),
            "due_date": str(row.get("due_date") or ""),
            "review_stage_days": int(row.get("review_stage_days") or 0),
            "status": str(row.get("status") or ""),
        }
        for row in rows
    ]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pjt02_review_schedule_report(
    *,
    generated_at: str,
    service_date: str,
    lifecycle_state_report: Mapping[str, Any],
    review_records: Sequence[Mapping[str, Any]],
    schedule_policy: Mapping[str, Any] | None = None,
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PJT02 review schedule and due queue evidence."""

    policy = dict(schedule_policy or {})
    production_gate = dict(production_gate_state or {})
    service_day = _parse_iso_date(service_date)
    blocking_reasons: list[str] = []
    lifecycle_errors = validate_s2pjt01_lifecycle_state_report(lifecycle_state_report)
    lifecycle_gate = (
        "pass"
        if lifecycle_state_report.get("status") == "pass"
        and lifecycle_state_report.get("s2pjt01_lifecycle_state_ready") is True
        and not lifecycle_errors
        else "blocked"
    )
    if lifecycle_gate != "pass":
        blocking_reasons.append("S2PJT01 lifecycle state report must pass")
        blocking_reasons.extend(lifecycle_errors)
    if service_day is None:
        blocking_reasons.append("service_date must be YYYY-MM-DD")

    intervals = tuple(int(day) for day in (policy.get("review_intervals_days") or S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS))
    missing_intervals = [day for day in S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS if day not in intervals]
    policy_errors: list[str] = []
    if missing_intervals:
        policy_errors.append("missing default review intervals: " + ", ".join(str(day) for day in missing_intervals))
    if policy.get("feedback_adjustment_supported", True) is not True:
        policy_errors.append("schedule_policy.feedback_adjustment_supported must be true")
    if policy.get("dry_run_only", True) is not True:
        policy_errors.append("schedule_policy.dry_run_only must be true")

    record_errors: list[str] = []
    content_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    normalized_records: list[dict[str, Any]] = []
    for index, record in enumerate(review_records):
        content_id = str(record.get("content_id") or "")
        status = str(record.get("status") or "")
        anchor = _parse_iso_date(record.get("anchor_date"))
        due = _parse_iso_date(record.get("due_date"))
        stage_days = int(record.get("review_stage_days") or 0)
        if not content_id:
            record_errors.append(f"record {index} missing content_id")
        elif content_id in content_ids:
            duplicate_ids.add(content_id)
        content_ids.add(content_id)
        if stage_days not in S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS:
            record_errors.append(f"{content_id or index} review_stage_days must be one of default intervals")
        if anchor is None:
            record_errors.append(f"{content_id or index} anchor_date must be YYYY-MM-DD")
        if due is None:
            record_errors.append(f"{content_id or index} due_date must be YYYY-MM-DD")
        if anchor is not None and due is not None and due != anchor + timedelta(days=stage_days):
            record_errors.append(f"{content_id or index} due_date must equal anchor_date + review_stage_days")
        if status not in {"pending", "completed"}:
            record_errors.append(f"{content_id or index} status must be pending or completed")
        for key in ("queue_mutation_allowed", "scheduler_enabled", "real_smtp_sent", "public_schema_changed"):
            if record.get(key, False) is not False:
                record_errors.append(f"{content_id or index}.{key} must be false")
        normalized_records.append(
            {
                **dict(record),
                "content_id": content_id,
                "status": status,
                "review_stage_days": stage_days,
                "due_date": str(record.get("due_date") or ""),
            }
        )
    if duplicate_ids:
        record_errors.append("duplicate review content_id: " + ", ".join(sorted(duplicate_ids)))

    due_today_queue: list[dict[str, Any]] = []
    due_next_7_days_queue: list[dict[str, Any]] = []
    overdue_queue: list[dict[str, Any]] = []
    completed_records: list[dict[str, Any]] = []
    if service_day is not None:
        for record in normalized_records:
            due = _parse_iso_date(record.get("due_date"))
            if record.get("status") == "completed":
                completed_records.append(record)
                continue
            if due is None:
                continue
            if due < service_day:
                overdue_queue.append(record)
            if due == service_day:
                due_today_queue.append(record)
            if service_day <= due <= service_day + timedelta(days=7):
                due_next_7_days_queue.append(record)
    sort_key = lambda row: (str(row.get("due_date") or ""), str(row.get("content_id") or ""))
    due_today_queue = sorted(due_today_queue, key=sort_key)
    due_next_7_days_queue = sorted(due_next_7_days_queue, key=sort_key)
    overdue_queue = sorted(overdue_queue, key=sort_key)
    completed_records = sorted(completed_records, key=sort_key)
    computed_counts = {
        "due_today": len(due_today_queue),
        "due_next_7_days": len(due_next_7_days_queue),
        "overdue": len(overdue_queue),
        "completed": len(completed_records),
    }
    supplied_counts = dict(policy.get("expected_counts") or computed_counts)
    count_errors = [
        f"{bucket} count mismatch"
        for bucket in S2PJT02_REQUIRED_COUNT_BUCKETS
        if int(supplied_counts.get(bucket, -1)) != computed_counts[bucket]
    ]

    production_errors: list[str] = []
    for key in (*S2PJT02_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "lifecycle_state_gate": lifecycle_gate,
        "schedule_policy_gate": "pass" if not policy_errors else "blocked",
        "review_record_gate": "pass" if not record_errors else "blocked",
        "due_count_gate": "pass" if not count_errors else "blocked",
        "deterministic_queue_gate": "pass",
        "no_side_effect_gate": "pass" if not production_errors else "blocked",
    }
    blocking_reasons.extend(policy_errors)
    blocking_reasons.extend(record_errors)
    blocking_reasons.extend(count_errors)
    blocking_reasons.extend(production_errors)
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    due_queue_records = [*overdue_queue, *due_today_queue, *due_next_7_days_queue]
    due_queue_hash = _s2pjt02_queue_hash(due_queue_records)

    return {
        "model_id": S2PJT02_REVIEW_SCHEDULE_MODEL_ID,
        "acceptance_id": S2PJT02_ACCEPTANCE_ID,
        "task_id": S2PJT02_TASK_ID,
        "phase": "S2PJ",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "service_date": service_date,
        "status": status,
        **gates,
        "required_review_intervals_days": list(S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS),
        "review_intervals_days": list(intervals),
        "required_count_buckets": list(S2PJT02_REQUIRED_COUNT_BUCKETS),
        "computed_counts": computed_counts,
        "supplied_expected_counts": supplied_counts,
        "due_today_queue": due_today_queue,
        "due_next_7_days_queue": due_next_7_days_queue,
        "overdue_queue": overdue_queue,
        "completed_records": completed_records,
        "due_queue_records": due_queue_records,
        "due_queue_hash": due_queue_hash,
        "schedule_policy": policy,
        "review_records": normalized_records,
        "s2pjt02_review_schedule_ready": status == "pass",
        "review_scheduler_enabled": False,
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pjt02_review_schedule(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    lifecycle_state_report: Mapping[str, Any],
    review_records: Sequence[Mapping[str, Any]],
    schedule_policy: Mapping[str, Any] | None = None,
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PJT02 review schedule evidence without installing a scheduler."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pjt02-review-schedule"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pjt02_review_schedule_report(
        generated_at=generated_at,
        service_date=date,
        lifecycle_state_report=lifecycle_state_report,
        review_records=review_records,
        schedule_policy=schedule_policy,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "review_schedule_report_path": str(run_dir / "adp-s2pjt02-review-schedule-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pjt02-review-schedule-report.json", report)
        _write_json(state / S2PJT02_REPORT_FILENAME, report)
    return report


def validate_s2pjt02_review_schedule_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PJT02_REVIEW_SCHEDULE_MODEL_ID:
        errors.append("S2PJT02 model_id must be adp-s2pjt02-review-schedule-v1")
    if report.get("task_id") != S2PJT02_TASK_ID:
        errors.append("S2PJT02 task_id must be S2PJT02")
    if report.get("acceptance_id") != S2PJT02_ACCEPTANCE_ID:
        errors.append("S2PJT02 acceptance_id must be ACC-S2PJT02-REVIEW")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PJT02 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PJT02_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
        "review_scheduler_enabled",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PJT02 local review schedule evidence")
    missing_intervals = [day for day in S2PJT02_DEFAULT_REVIEW_INTERVAL_DAYS if day not in set(report.get("review_intervals_days") or [])]
    if missing_intervals:
        errors.append("S2PJT02 missing default review intervals: " + ", ".join(str(day) for day in missing_intervals))
    records = report.get("review_records")
    if not isinstance(records, list) or not records:
        errors.append("S2PJT02 review_records must be a non-empty list")
    computed_counts = report.get("computed_counts")
    if not isinstance(computed_counts, Mapping):
        errors.append("S2PJT02 computed_counts must be a mapping")
        computed_counts = {}
    for bucket in S2PJT02_REQUIRED_COUNT_BUCKETS:
        if bucket not in computed_counts:
            errors.append(f"S2PJT02 computed_counts missing {bucket}")
    queue_records = report.get("due_queue_records")
    if not isinstance(queue_records, list):
        errors.append("S2PJT02 due_queue_records must be a list")
        queue_records = []
    if report.get("due_queue_hash") != _s2pjt02_queue_hash(queue_records):
        errors.append("S2PJT02 due_queue_hash must match due_queue_records")
    for gate in S2PJT02_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PJT02 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PJT02 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pjt02_review_schedule_ready") is not True:
        errors.append("passing S2PJT02 report requires s2pjt02_review_schedule_ready=true")
    return errors


def _s2pjt03_ledger_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {
            "action_id": str(row.get("action_id") or ""),
            "actual_roi_status": str(row.get("actual_roi_status") or ""),
            "content_id": str(row.get("content_id") or ""),
            "expected_roi_confidence": row.get("expected_roi_confidence"),
            "expected_roi_value": row.get("expected_roi_value"),
            "horizon": str(row.get("horizon") or ""),
            "status": str(row.get("status") or ""),
        }
        for row in rows
    ]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pjt03_action_asset_roi_report(
    *,
    generated_at: str,
    service_date: str,
    review_schedule_report: Mapping[str, Any],
    action_records: Sequence[Mapping[str, Any]],
    capability_assets: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PJT03 action, asset, and ROI ledger evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []
    review_errors = validate_s2pjt02_review_schedule_report(review_schedule_report)
    review_gate = (
        "pass"
        if review_schedule_report.get("status") == "pass"
        and review_schedule_report.get("s2pjt02_review_schedule_ready") is True
        and not review_errors
        else "blocked"
    )
    if review_gate != "pass":
        blocking_reasons.append("S2PJT02 review schedule report must pass")
        blocking_reasons.extend(review_errors)
    if _parse_iso_date(service_date) is None:
        blocking_reasons.append("service_date must be YYYY-MM-DD")

    action_errors: list[str] = []
    expected_roi_errors: list[str] = []
    actual_roi_errors: list[str] = []
    action_ids: set[str] = set()
    duplicate_action_ids: set[str] = set()
    normalized_actions: list[dict[str, Any]] = []
    for index, action in enumerate(action_records):
        action_id = str(action.get("action_id") or "")
        content_id = str(action.get("content_id") or "")
        horizon = str(action.get("horizon") or "")
        status = str(action.get("status") or "")
        expected = action.get("expected_roi")
        actual = action.get("actual_roi")
        if not action_id:
            action_errors.append(f"action {index} missing action_id")
        elif action_id in action_ids:
            duplicate_action_ids.add(action_id)
        action_ids.add(action_id)
        if not content_id:
            action_errors.append(f"{action_id or index} missing content_id")
        if horizon not in S2PJT03_REQUIRED_ACTION_WINDOWS:
            action_errors.append(f"{action_id or index} horizon must be one of {', '.join(S2PJT03_REQUIRED_ACTION_WINDOWS)}")
        if status not in S2PJT03_ALLOWED_ACTION_STATUSES:
            action_errors.append(f"{action_id or index} status must be planned, completed, or deferred")
        if not isinstance(expected, Mapping):
            expected_roi_errors.append(f"{action_id or index} expected_roi must be a mapping")
            expected = {}
        assumptions = expected.get("assumptions") if isinstance(expected, Mapping) else None
        confidence = expected.get("confidence") if isinstance(expected, Mapping) else None
        if expected.get("value") in (None, ""):
            expected_roi_errors.append(f"{action_id or index} expected_roi.value is required")
        if not isinstance(assumptions, list) or not assumptions or not all(str(item).strip() for item in assumptions):
            expected_roi_errors.append(f"{action_id or index} expected_roi.assumptions must be a non-empty list")
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = -1.0
        if not 0.0 <= confidence_value <= 1.0:
            expected_roi_errors.append(f"{action_id or index} expected_roi.confidence must be between 0 and 1")

        if not isinstance(actual, Mapping):
            actual = {"status": "not_calculable"}
        actual_status = str(actual.get("status") or "not_calculable")
        if actual_status not in S2PJT03_ALLOWED_ACTUAL_ROI_STATUSES:
            actual_roi_errors.append(f"{action_id or index} actual_roi.status must be not_calculable or calculated")
        cost = actual.get("verifiable_cost")
        benefit = actual.get("verifiable_benefit")
        evidence_refs = actual.get("evidence_refs")
        has_verifiable_cost_benefit = isinstance(cost, (int, float)) and cost > 0 and isinstance(benefit, (int, float))
        has_evidence = isinstance(evidence_refs, list) and bool(evidence_refs) and all(str(ref).strip() for ref in evidence_refs)
        if actual_status == "calculated":
            if not has_verifiable_cost_benefit:
                actual_roi_errors.append(f"{action_id or index} calculated actual ROI requires verifiable_cost > 0 and verifiable_benefit")
            if not has_evidence:
                actual_roi_errors.append(f"{action_id or index} calculated actual ROI requires evidence_refs")
        else:
            if actual.get("value") not in (None, ""):
                actual_roi_errors.append(f"{action_id or index} not_calculable actual ROI must not include a precise value")

        actual_value = None
        if actual_status == "calculated" and has_verifiable_cost_benefit:
            actual_value = round((float(benefit) - float(cost)) / float(cost), 6)
        normalized_actions.append(
            {
                **dict(action),
                "action_id": action_id,
                "content_id": content_id,
                "horizon": horizon,
                "status": status,
                "expected_roi_value": expected.get("value") if isinstance(expected, Mapping) else None,
                "expected_roi_confidence": confidence_value if 0.0 <= confidence_value <= 1.0 else None,
                "expected_roi_assumptions": assumptions if isinstance(assumptions, list) else [],
                "actual_roi_status": actual_status,
                "actual_roi_value": actual_value,
            }
        )
    if duplicate_action_ids:
        action_errors.append("duplicate action_id: " + ", ".join(sorted(duplicate_action_ids)))

    missing_windows = [window for window in S2PJT03_REQUIRED_ACTION_WINDOWS if window not in {row.get("horizon") for row in normalized_actions}]
    if missing_windows:
        action_errors.append("missing required action windows: " + ", ".join(missing_windows))

    asset_errors: list[str] = []
    normalized_assets: list[dict[str, Any]] = []
    for index, asset in enumerate(capability_assets):
        asset_id = str(asset.get("asset_id") or "")
        content_id = str(asset.get("content_id") or "")
        asset_type = str(asset.get("asset_type") or "")
        evidence_refs = asset.get("evidence_refs")
        if not asset_id:
            asset_errors.append(f"asset {index} missing asset_id")
        if not content_id:
            asset_errors.append(f"{asset_id or index} missing content_id")
        if not asset_type:
            asset_errors.append(f"{asset_id or index} missing asset_type")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            asset_errors.append(f"{asset_id or index} evidence_refs must be a non-empty list")
        normalized_assets.append({**dict(asset), "asset_id": asset_id, "content_id": content_id, "asset_type": asset_type})
    if not normalized_assets:
        asset_errors.append("at least one capability asset is required")

    production_errors: list[str] = []
    for key in (*S2PJT03_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    action_counts = {window: 0 for window in S2PJT03_REQUIRED_ACTION_WINDOWS}
    for action in normalized_actions:
        if action.get("horizon") in action_counts:
            action_counts[str(action["horizon"])] += 1
    actual_roi_counts = {status: 0 for status in S2PJT03_ALLOWED_ACTUAL_ROI_STATUSES}
    for action in normalized_actions:
        if action.get("actual_roi_status") in actual_roi_counts:
            actual_roi_counts[str(action["actual_roi_status"])] += 1

    gates = {
        "review_schedule_gate": review_gate,
        "action_window_gate": "pass" if not action_errors else "blocked",
        "expected_roi_gate": "pass" if not expected_roi_errors else "blocked",
        "actual_roi_gate": "pass" if not actual_roi_errors else "blocked",
        "asset_trace_gate": "pass" if not asset_errors else "blocked",
        "deterministic_ledger_gate": "pass",
        "no_side_effect_gate": "pass" if not production_errors else "blocked",
    }
    blocking_reasons.extend(action_errors)
    blocking_reasons.extend(expected_roi_errors)
    blocking_reasons.extend(actual_roi_errors)
    blocking_reasons.extend(asset_errors)
    blocking_reasons.extend(production_errors)
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    ledger_hash = _s2pjt03_ledger_hash(normalized_actions)

    return {
        "model_id": S2PJT03_ACTION_ROI_MODEL_ID,
        "acceptance_id": S2PJT03_ACCEPTANCE_ID,
        "task_id": S2PJT03_TASK_ID,
        "phase": "S2PJ",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "service_date": service_date,
        "status": status,
        **gates,
        "required_action_windows": list(S2PJT03_REQUIRED_ACTION_WINDOWS),
        "action_counts": action_counts,
        "actual_roi_status_counts": actual_roi_counts,
        "action_records": normalized_actions,
        "capability_assets": normalized_assets,
        "ledger_hash": ledger_hash,
        "s2pjt03_action_roi_ready": status == "pass",
        "actual_roi_policy": "calculate_only_with_verifiable_cost_benefit_and_evidence_refs",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pjt03_action_asset_roi(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    review_schedule_report: Mapping[str, Any],
    action_records: Sequence[Mapping[str, Any]],
    capability_assets: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PJT03 action, asset, and ROI ledger evidence without production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pjt03-action-asset-roi"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pjt03_action_asset_roi_report(
        generated_at=generated_at,
        service_date=date,
        review_schedule_report=review_schedule_report,
        action_records=action_records,
        capability_assets=capability_assets,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "action_roi_report_path": str(run_dir / "adp-s2pjt03-action-asset-roi-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pjt03-action-asset-roi-report.json", report)
        _write_json(state / S2PJT03_REPORT_FILENAME, report)
    return report


def validate_s2pjt03_action_asset_roi_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PJT03_ACTION_ROI_MODEL_ID:
        errors.append("S2PJT03 model_id must be adp-s2pjt03-action-asset-roi-ledger-v1")
    if report.get("task_id") != S2PJT03_TASK_ID:
        errors.append("S2PJT03 task_id must be S2PJT03")
    if report.get("acceptance_id") != S2PJT03_ACCEPTANCE_ID:
        errors.append("S2PJT03 acceptance_id must be ACC-S2PJT03-ROI")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PJT03 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PJT03_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PJT03 local action/ROI evidence")
    action_records = report.get("action_records")
    if not isinstance(action_records, list) or not action_records:
        errors.append("S2PJT03 action_records must be a non-empty list")
        action_records = []
    missing_windows = [window for window in S2PJT03_REQUIRED_ACTION_WINDOWS if window not in {row.get("horizon") for row in action_records}]
    if missing_windows:
        errors.append("S2PJT03 missing action windows: " + ", ".join(missing_windows))
    if report.get("ledger_hash") != _s2pjt03_ledger_hash(action_records):
        errors.append("S2PJT03 ledger_hash must match action_records")
    assets = report.get("capability_assets")
    if not isinstance(assets, list) or not assets:
        errors.append("S2PJT03 capability_assets must be a non-empty list")
    for action in action_records:
        if action.get("actual_roi_status") == "not_calculable" and action.get("actual_roi_value") is not None:
            errors.append(f"{action.get('action_id')} not_calculable actual ROI must not include actual_roi_value")
        if action.get("actual_roi_status") == "calculated" and action.get("actual_roi_value") is None:
            errors.append(f"{action.get('action_id')} calculated actual ROI requires actual_roi_value")
        if action.get("expected_roi_confidence") is None:
            errors.append(f"{action.get('action_id')} expected ROI confidence is required")
        if not action.get("expected_roi_assumptions"):
            errors.append(f"{action.get('action_id')} expected ROI assumptions are required")
    for gate in S2PJT03_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PJT03 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PJT03 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pjt03_action_roi_ready") is not True:
        errors.append("passing S2PJT03 report requires s2pjt03_action_roi_ready=true")
    return errors


def _s2pjt04_weekly_hash(
    weekly_items: Sequence[Mapping[str, Any]],
    weekly_sections: Mapping[str, Any],
    next_week_focus: Sequence[Mapping[str, Any]],
) -> str:
    payload = {
        "items": [
            {
                "actual_state": str(item.get("actual_state") or ""),
                "content_id": str(item.get("content_id") or ""),
                "observed_date": str(item.get("observed_date") or ""),
                "section_tags": sorted(str(tag) for tag in item.get("section_tags", []) if str(tag).strip()),
            }
            for item in weekly_items
        ],
        "sections": {
            str(key): sorted(str(content_id) for content_id in value.get("content_ids", []) if str(content_id).strip())
            for key, value in sorted(weekly_sections.items())
            if isinstance(value, Mapping)
        },
        "next_week_focus": [
            {
                "focus_id": str(item.get("focus_id") or ""),
                "priority": item.get("priority"),
                "source_content_ids": sorted(str(content_id) for content_id in item.get("source_content_ids", []) if str(content_id).strip()),
            }
            for item in next_week_focus
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pjt04_weekly_report(
    *,
    generated_at: str,
    week_start: str,
    week_end: str,
    action_roi_report: Mapping[str, Any],
    weekly_items: Sequence[Mapping[str, Any]],
    weekly_sections: Mapping[str, Any],
    next_week_focus: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PJT04 weekly synthesis and attention reallocation evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []
    action_roi_errors = validate_s2pjt03_action_asset_roi_report(action_roi_report)
    action_roi_gate = (
        "pass"
        if action_roi_report.get("status") == "pass"
        and action_roi_report.get("s2pjt03_action_roi_ready") is True
        and not action_roi_errors
        else "blocked"
    )
    if action_roi_gate != "pass":
        blocking_reasons.append("S2PJT03 action/asset/ROI report must pass")
        blocking_reasons.extend(action_roi_errors)

    start = _parse_iso_date(week_start)
    end = _parse_iso_date(week_end)
    week_errors: list[str] = []
    if start is None:
        week_errors.append("week_start must be YYYY-MM-DD")
    if end is None:
        week_errors.append("week_end must be YYYY-MM-DD")
    if start is not None and end is not None:
        if end < start:
            week_errors.append("week_end must be on or after week_start")
        if (end - start).days > S2PJT04_MAX_WEEK_WINDOW_DAYS:
            week_errors.append("weekly report window must not exceed 7 inclusive days")

    traceable_content_ids = {
        str(row.get("content_id") or "")
        for row in action_roi_report.get("action_records", [])
        if isinstance(row, Mapping) and row.get("content_id")
    }
    traceable_content_ids.update(
        str(row.get("content_id") or "")
        for row in action_roi_report.get("capability_assets", [])
        if isinstance(row, Mapping) and row.get("content_id")
    )
    item_errors: list[str] = []
    state_errors: list[str] = []
    duplicate_content_ids: set[str] = set()
    seen_content_ids: set[str] = set()
    normalized_items: list[dict[str, Any]] = []
    for index, item in enumerate(weekly_items):
        content_id = str(item.get("content_id") or "")
        actual_state = str(item.get("actual_state") or "")
        observed = _parse_iso_date(item.get("observed_date"))
        evidence_refs = item.get("evidence_refs")
        section_tags = [str(tag) for tag in item.get("section_tags", []) if str(tag).strip()]
        if not content_id:
            item_errors.append(f"item {index} missing content_id")
        elif content_id in seen_content_ids:
            duplicate_content_ids.add(content_id)
        seen_content_ids.add(content_id)
        if content_id and traceable_content_ids and content_id not in traceable_content_ids:
            item_errors.append(f"{content_id} is not traceable to S2PJT03 action or asset ledger")
        if observed is None:
            item_errors.append(f"{content_id or index} observed_date must be YYYY-MM-DD")
        elif start is not None and end is not None and not (start <= observed <= end):
            item_errors.append(f"{content_id or index} observed_date must be inside the weekly window")
        if not actual_state:
            state_errors.append(f"{content_id or index} actual_state is required")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            item_errors.append(f"{content_id or index} evidence_refs must be a non-empty list")
        if not section_tags:
            item_errors.append(f"{content_id or index} section_tags must be non-empty")
        normalized_items.append(
            {
                **dict(item),
                "content_id": content_id,
                "actual_state": actual_state,
                "observed_date": str(item.get("observed_date") or ""),
                "section_tags": section_tags,
            }
        )
    if not normalized_items:
        item_errors.append("weekly_items must be a non-empty list")
    if duplicate_content_ids:
        item_errors.append("duplicate weekly content_id: " + ", ".join(sorted(duplicate_content_ids)))

    item_ids = {item["content_id"] for item in normalized_items if item.get("content_id")}
    section_errors: list[str] = []
    normalized_sections: dict[str, dict[str, Any]] = {}
    for section in S2PJT04_REQUIRED_SECTIONS:
        value = weekly_sections.get(section) if isinstance(weekly_sections, Mapping) else None
        if not isinstance(value, Mapping):
            section_errors.append(f"weekly_sections.{section} must be a mapping")
            continue
        content_ids = [str(content_id) for content_id in value.get("content_ids", []) if str(content_id).strip()]
        if not content_ids:
            section_errors.append(f"weekly_sections.{section}.content_ids must be non-empty")
        missing = [content_id for content_id in content_ids if content_id not in item_ids]
        if missing:
            section_errors.append(f"weekly_sections.{section}.content_ids not in weekly_items: " + ", ".join(missing))
        summary = str(value.get("summary") or "")
        if not summary:
            section_errors.append(f"weekly_sections.{section}.summary is required")
        normalized_sections[section] = {**dict(value), "content_ids": content_ids, "summary": summary}

    focus_errors: list[str] = []
    normalized_focus: list[dict[str, Any]] = []
    for index, focus in enumerate(next_week_focus):
        focus_id = str(focus.get("focus_id") or "")
        source_content_ids = [str(content_id) for content_id in focus.get("source_content_ids", []) if str(content_id).strip()]
        rationale = str(focus.get("rationale") or "")
        try:
            priority = int(focus.get("priority"))
        except (TypeError, ValueError):
            priority = 0
        if not focus_id:
            focus_errors.append(f"focus {index} missing focus_id")
        if not source_content_ids:
            focus_errors.append(f"{focus_id or index} source_content_ids must be non-empty")
        missing = [content_id for content_id in source_content_ids if content_id not in item_ids]
        if missing:
            focus_errors.append(f"{focus_id or index} source_content_ids not in weekly_items: " + ", ".join(missing))
        if not rationale:
            focus_errors.append(f"{focus_id or index} rationale is required")
        if not 1 <= priority <= 5:
            focus_errors.append(f"{focus_id or index} priority must be between 1 and 5")
        normalized_focus.append({**dict(focus), "focus_id": focus_id, "source_content_ids": source_content_ids, "priority": priority})
    if not normalized_focus:
        focus_errors.append("next_week_focus must be a non-empty list")

    production_errors: list[str] = []
    for key in (*S2PJT04_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    state_counts: dict[str, int] = {}
    for item in normalized_items:
        state = str(item.get("actual_state") or "")
        if state:
            state_counts[state] = state_counts.get(state, 0) + 1
    section_counts = {
        section: len(normalized_sections.get(section, {}).get("content_ids", []))
        for section in S2PJT04_REQUIRED_SECTIONS
    }

    gates = {
        "action_roi_gate": action_roi_gate,
        "week_window_gate": "pass" if not week_errors else "blocked",
        "section_trace_gate": "pass" if not section_errors and not item_errors else "blocked",
        "state_trace_gate": "pass" if not state_errors else "blocked",
        "no_duplication_gate": "pass" if not duplicate_content_ids else "blocked",
        "next_focus_gate": "pass" if not focus_errors else "blocked",
        "deterministic_report_gate": "pass",
        "no_side_effect_gate": "pass" if not production_errors else "blocked",
    }
    blocking_reasons.extend(week_errors)
    blocking_reasons.extend(item_errors)
    blocking_reasons.extend(state_errors)
    blocking_reasons.extend(section_errors)
    blocking_reasons.extend(focus_errors)
    blocking_reasons.extend(production_errors)
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    weekly_report_hash = _s2pjt04_weekly_hash(normalized_items, normalized_sections, normalized_focus)

    return {
        "model_id": S2PJT04_WEEKLY_REPORT_MODEL_ID,
        "acceptance_id": S2PJT04_ACCEPTANCE_ID,
        "task_id": S2PJT04_TASK_ID,
        "phase": "S2PJ",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "week_start": week_start,
        "week_end": week_end,
        "status": status,
        **gates,
        "required_sections": list(S2PJT04_REQUIRED_SECTIONS),
        "weekly_items": normalized_items,
        "weekly_sections": normalized_sections,
        "next_week_focus": normalized_focus,
        "state_counts": state_counts,
        "section_counts": section_counts,
        "weekly_report_hash": weekly_report_hash,
        "s2pjt04_weekly_report_ready": status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pjt04_weekly_report(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    week_start: str,
    week_end: str,
    action_roi_report: Mapping[str, Any],
    weekly_items: Sequence[Mapping[str, Any]],
    weekly_sections: Mapping[str, Any],
    next_week_focus: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PJT04 weekly report evidence without production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pjt04-weekly-report"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pjt04_weekly_report(
        generated_at=generated_at,
        week_start=week_start,
        week_end=week_end,
        action_roi_report=action_roi_report,
        weekly_items=weekly_items,
        weekly_sections=weekly_sections,
        next_week_focus=next_week_focus,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "weekly_report_path": str(run_dir / "adp-s2pjt04-weekly-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pjt04-weekly-report.json", report)
        _write_json(state / S2PJT04_REPORT_FILENAME, report)
    return report


def validate_s2pjt04_weekly_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PJT04_WEEKLY_REPORT_MODEL_ID:
        errors.append("S2PJT04 model_id must be adp-s2pjt04-weekly-report-v1")
    if report.get("task_id") != S2PJT04_TASK_ID:
        errors.append("S2PJT04 task_id must be S2PJT04")
    if report.get("acceptance_id") != S2PJT04_ACCEPTANCE_ID:
        errors.append("S2PJT04 acceptance_id must be ACC-S2PJT04-WEEKLY")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PJT04 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PJT04_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PJT04 local weekly report evidence")
    items = report.get("weekly_items")
    if not isinstance(items, list) or not items:
        errors.append("S2PJT04 weekly_items must be a non-empty list")
        items = []
    content_ids = [str(item.get("content_id") or "") for item in items if isinstance(item, Mapping)]
    if len([content_id for content_id in content_ids if content_id]) != len(set(content_id for content_id in content_ids if content_id)):
        errors.append("S2PJT04 weekly_items must not duplicate content_id")
    sections = report.get("weekly_sections")
    if not isinstance(sections, Mapping):
        errors.append("S2PJT04 weekly_sections must be a mapping")
        sections = {}
    for section in S2PJT04_REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(f"S2PJT04 weekly_sections missing {section}")
    focus = report.get("next_week_focus")
    if not isinstance(focus, list) or not focus:
        errors.append("S2PJT04 next_week_focus must be a non-empty list")
        focus = []
    if report.get("weekly_report_hash") != _s2pjt04_weekly_hash(items, sections, focus):
        errors.append("S2PJT04 weekly_report_hash must match weekly items, sections, and next_week_focus")
    for gate in S2PJT04_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PJT04 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PJT04 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pjt04_weekly_report_ready") is not True:
        errors.append("passing S2PJT04 report requires s2pjt04_weekly_report_ready=true")
    return errors


def _s2pjt05_monthly_hash(
    weekly_reports: Sequence[Mapping[str, Any]],
    monthly_sections: Mapping[str, Any],
    cognitive_delta: Mapping[str, Any],
    capability_growth: Sequence[Mapping[str, Any]],
    economic_conversions: Sequence[Mapping[str, Any]],
    forecast_reviews: Sequence[Mapping[str, Any]],
    next_month_focus: Sequence[Mapping[str, Any]],
) -> str:
    payload = {
        "weekly_report_hashes": sorted(str(report.get("weekly_report_hash") or "") for report in weekly_reports),
        "sections": {
            str(key): sorted(str(content_id) for content_id in value.get("content_ids", []) if str(content_id).strip())
            for key, value in sorted(monthly_sections.items())
            if isinstance(value, Mapping)
        },
        "cognitive_delta": {
            "start_viewpoint_ids": sorted(str(item) for item in cognitive_delta.get("start_viewpoint_ids", []) if str(item).strip()),
            "end_viewpoint_ids": sorted(str(item) for item in cognitive_delta.get("end_viewpoint_ids", []) if str(item).strip()),
            "changed_viewpoints": sorted(str(item.get("viewpoint_id") or "") for item in cognitive_delta.get("changed_viewpoints", []) if isinstance(item, Mapping)),
        },
        "capability_growth": sorted(str(item.get("asset_id") or "") for item in capability_growth),
        "economic_conversions": sorted(str(item.get("conversion_id") or "") for item in economic_conversions),
        "forecast_reviews": sorted(str(item.get("prediction_id") or "") for item in forecast_reviews),
        "next_month_focus": sorted(str(item.get("focus_id") or "") for item in next_month_focus),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pjt05_monthly_report(
    *,
    generated_at: str,
    month_start: str,
    month_end: str,
    weekly_reports: Sequence[Mapping[str, Any]],
    cognitive_snapshots: Mapping[str, Any],
    monthly_sections: Mapping[str, Any],
    capability_growth: Sequence[Mapping[str, Any]],
    economic_conversions: Sequence[Mapping[str, Any]],
    forecast_reviews: Sequence[Mapping[str, Any]],
    next_month_focus: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PJT05 monthly cognitive delta, capability, ROI, and forecast evidence."""

    production_gate = dict(production_gate_state or {})
    blocking_reasons: list[str] = []
    start = _parse_iso_date(month_start)
    end = _parse_iso_date(month_end)
    month_errors: list[str] = []
    if start is None:
        month_errors.append("month_start must be YYYY-MM-DD")
    if end is None:
        month_errors.append("month_end must be YYYY-MM-DD")
    if start is not None and end is not None:
        if end < start:
            month_errors.append("month_end must be on or after month_start")
        if (end - start).days > S2PJT05_MAX_MONTH_WINDOW_DAYS:
            month_errors.append("monthly report window must not exceed 31 inclusive days")

    weekly_errors: list[str] = []
    normalized_weekly_reports: list[dict[str, Any]] = []
    monthly_content_ids: set[str] = set()
    for index, report in enumerate(weekly_reports):
        errors = validate_s2pjt04_weekly_report(report)
        if report.get("status") != "pass" or report.get("s2pjt04_weekly_report_ready") is not True or errors:
            weekly_errors.append(f"weekly report {index} must be a passing S2PJT04 report")
            weekly_errors.extend(errors)
        week_start = _parse_iso_date(report.get("week_start"))
        week_end = _parse_iso_date(report.get("week_end"))
        if week_start is None or week_end is None:
            weekly_errors.append(f"weekly report {index} week_start/week_end must be YYYY-MM-DD")
        elif start is not None and end is not None and not (start <= week_start <= end and start <= week_end <= end):
            weekly_errors.append(f"weekly report {index} must be inside the monthly window")
        for item in report.get("weekly_items", []):
            if isinstance(item, Mapping) and item.get("content_id"):
                monthly_content_ids.add(str(item.get("content_id")))
        normalized_weekly_reports.append(dict(report))
    if not normalized_weekly_reports:
        weekly_errors.append("weekly_reports must be a non-empty list")

    start_snapshot = cognitive_snapshots.get("month_start") if isinstance(cognitive_snapshots, Mapping) else None
    end_snapshot = cognitive_snapshots.get("month_end") if isinstance(cognitive_snapshots, Mapping) else None
    cognitive_errors: list[str] = []
    if not isinstance(start_snapshot, Mapping):
        cognitive_errors.append("cognitive_snapshots.month_start must be a mapping")
        start_snapshot = {}
    if not isinstance(end_snapshot, Mapping):
        cognitive_errors.append("cognitive_snapshots.month_end must be a mapping")
        end_snapshot = {}
    start_viewpoints = [str(item) for item in start_snapshot.get("viewpoint_ids", []) if str(item).strip()]
    end_viewpoints = [str(item) for item in end_snapshot.get("viewpoint_ids", []) if str(item).strip()]
    if not str(start_snapshot.get("summary") or ""):
        cognitive_errors.append("cognitive_snapshots.month_start.summary is required")
    if not str(end_snapshot.get("summary") or ""):
        cognitive_errors.append("cognitive_snapshots.month_end.summary is required")
    if not start_viewpoints:
        cognitive_errors.append("cognitive_snapshots.month_start.viewpoint_ids must be non-empty")
    if not end_viewpoints:
        cognitive_errors.append("cognitive_snapshots.month_end.viewpoint_ids must be non-empty")
    changed_viewpoints = cognitive_snapshots.get("changed_viewpoints", []) if isinstance(cognitive_snapshots, Mapping) else []
    normalized_changes: list[dict[str, Any]] = []
    if not isinstance(changed_viewpoints, list) or not changed_viewpoints:
        cognitive_errors.append("cognitive_snapshots.changed_viewpoints must be a non-empty list")
        changed_viewpoints = []
    for index, change in enumerate(changed_viewpoints):
        if not isinstance(change, Mapping):
            cognitive_errors.append(f"changed_viewpoint {index} must be a mapping")
            continue
        viewpoint_id = str(change.get("viewpoint_id") or "")
        before = str(change.get("before") or "")
        after = str(change.get("after") or "")
        evidence_refs = change.get("evidence_refs")
        if not viewpoint_id:
            cognitive_errors.append(f"changed_viewpoint {index} missing viewpoint_id")
        if not before or not after:
            cognitive_errors.append(f"{viewpoint_id or index} before and after are required")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            cognitive_errors.append(f"{viewpoint_id or index} evidence_refs must be a non-empty list")
        normalized_changes.append({**dict(change), "viewpoint_id": viewpoint_id, "before": before, "after": after})
    cognitive_delta = {
        "start_summary": str(start_snapshot.get("summary") or ""),
        "end_summary": str(end_snapshot.get("summary") or ""),
        "start_viewpoint_ids": start_viewpoints,
        "end_viewpoint_ids": end_viewpoints,
        "changed_viewpoints": normalized_changes,
    }

    asset_errors: list[str] = []
    normalized_assets: list[dict[str, Any]] = []
    for index, asset in enumerate(capability_growth):
        asset_id = str(asset.get("asset_id") or "")
        asset_type = str(asset.get("asset_type") or "")
        source_content_ids = [str(content_id) for content_id in asset.get("source_content_ids", []) if str(content_id).strip()]
        evidence_refs = asset.get("evidence_refs")
        if not asset_id:
            asset_errors.append(f"capability {index} missing asset_id")
        if not asset_type:
            asset_errors.append(f"{asset_id or index} asset_type is required")
        if not source_content_ids:
            asset_errors.append(f"{asset_id or index} source_content_ids must be non-empty")
        missing = [content_id for content_id in source_content_ids if content_id not in monthly_content_ids]
        if missing:
            asset_errors.append(f"{asset_id or index} source_content_ids not in monthly weekly evidence: " + ", ".join(missing))
        if not isinstance(evidence_refs, list) or not evidence_refs:
            asset_errors.append(f"{asset_id or index} evidence_refs must be a non-empty list")
        normalized_assets.append({**dict(asset), "asset_id": asset_id, "asset_type": asset_type, "source_content_ids": source_content_ids})
    if not normalized_assets:
        asset_errors.append("capability_growth must be a non-empty list")

    conversion_errors: list[str] = []
    normalized_conversions: list[dict[str, Any]] = []
    calculated_conversion_count = 0
    for index, conversion in enumerate(economic_conversions):
        conversion_id = str(conversion.get("conversion_id") or "")
        source_content_ids = [str(content_id) for content_id in conversion.get("source_content_ids", []) if str(content_id).strip()]
        evidence_refs = conversion.get("evidence_refs")
        actual_status = str(conversion.get("actual_roi_status") or "not_calculable")
        if not conversion_id:
            conversion_errors.append(f"conversion {index} missing conversion_id")
        if not source_content_ids:
            conversion_errors.append(f"{conversion_id or index} source_content_ids must be non-empty")
        missing = [content_id for content_id in source_content_ids if content_id not in monthly_content_ids]
        if missing:
            conversion_errors.append(f"{conversion_id or index} source_content_ids not in monthly weekly evidence: " + ", ".join(missing))
        if actual_status not in S2PJT03_ALLOWED_ACTUAL_ROI_STATUSES:
            conversion_errors.append(f"{conversion_id or index} actual_roi_status must be not_calculable or calculated")
        cost = conversion.get("verifiable_cost")
        benefit = conversion.get("verifiable_benefit")
        has_verifiable_cost_benefit = isinstance(cost, (int, float)) and cost > 0 and isinstance(benefit, (int, float))
        has_evidence = isinstance(evidence_refs, list) and bool(evidence_refs) and all(str(ref).strip() for ref in evidence_refs)
        actual_value = None
        if actual_status == "calculated":
            if not has_verifiable_cost_benefit:
                conversion_errors.append(f"{conversion_id or index} calculated conversion requires verifiable_cost > 0 and verifiable_benefit")
            if not has_evidence:
                conversion_errors.append(f"{conversion_id or index} calculated conversion requires evidence_refs")
            if has_verifiable_cost_benefit:
                actual_value = round((float(benefit) - float(cost)) / float(cost), 6)
                calculated_conversion_count += 1
        elif conversion.get("actual_roi_value") not in (None, ""):
            conversion_errors.append(f"{conversion_id or index} not_calculable conversion must not include actual_roi_value")
        normalized_conversions.append(
            {
                **dict(conversion),
                "conversion_id": conversion_id,
                "source_content_ids": source_content_ids,
                "actual_roi_status": actual_status,
                "actual_roi_value": actual_value,
            }
        )
    if not normalized_conversions:
        conversion_errors.append("economic_conversions must be a non-empty list")
    if calculated_conversion_count < S2PJT05_MIN_VERIFIABLE_CONVERSIONS:
        conversion_errors.append("monthly report requires at least one verifiable calculated conversion")

    forecast_errors: list[str] = []
    normalized_forecasts: list[dict[str, Any]] = []
    for index, forecast in enumerate(forecast_reviews):
        prediction_id = str(forecast.get("prediction_id") or "")
        source_content_ids = [str(content_id) for content_id in forecast.get("source_content_ids", []) if str(content_id).strip()]
        evidence_refs = forecast.get("evidence_refs")
        try:
            accuracy_score = float(forecast.get("accuracy_score"))
        except (TypeError, ValueError):
            accuracy_score = -1.0
        if not prediction_id:
            forecast_errors.append(f"forecast {index} missing prediction_id")
        if not str(forecast.get("forecast") or ""):
            forecast_errors.append(f"{prediction_id or index} forecast is required")
        if not str(forecast.get("outcome") or ""):
            forecast_errors.append(f"{prediction_id or index} outcome is required")
        if not 0.0 <= accuracy_score <= 1.0:
            forecast_errors.append(f"{prediction_id or index} accuracy_score must be between 0 and 1")
        if not source_content_ids:
            forecast_errors.append(f"{prediction_id or index} source_content_ids must be non-empty")
        missing = [content_id for content_id in source_content_ids if content_id not in monthly_content_ids]
        if missing:
            forecast_errors.append(f"{prediction_id or index} source_content_ids not in monthly weekly evidence: " + ", ".join(missing))
        if not isinstance(evidence_refs, list) or not evidence_refs:
            forecast_errors.append(f"{prediction_id or index} evidence_refs must be a non-empty list")
        normalized_forecasts.append({**dict(forecast), "prediction_id": prediction_id, "source_content_ids": source_content_ids, "accuracy_score": accuracy_score if 0.0 <= accuracy_score <= 1.0 else None})
    if not normalized_forecasts:
        forecast_errors.append("forecast_reviews must be a non-empty list")

    focus_errors: list[str] = []
    normalized_focus: list[dict[str, Any]] = []
    for index, focus in enumerate(next_month_focus):
        focus_id = str(focus.get("focus_id") or "")
        source_content_ids = [str(content_id) for content_id in focus.get("source_content_ids", []) if str(content_id).strip()]
        rationale = str(focus.get("rationale") or "")
        try:
            priority = int(focus.get("priority"))
        except (TypeError, ValueError):
            priority = 0
        if not focus_id:
            focus_errors.append(f"focus {index} missing focus_id")
        if not source_content_ids:
            focus_errors.append(f"{focus_id or index} source_content_ids must be non-empty")
        missing = [content_id for content_id in source_content_ids if content_id not in monthly_content_ids]
        if missing:
            focus_errors.append(f"{focus_id or index} source_content_ids not in monthly weekly evidence: " + ", ".join(missing))
        if not rationale:
            focus_errors.append(f"{focus_id or index} rationale is required")
        if not 1 <= priority <= 5:
            focus_errors.append(f"{focus_id or index} priority must be between 1 and 5")
        normalized_focus.append({**dict(focus), "focus_id": focus_id, "source_content_ids": source_content_ids, "priority": priority})
    if not normalized_focus:
        focus_errors.append("next_month_focus must be a non-empty list")

    section_errors: list[str] = []
    normalized_sections: dict[str, dict[str, Any]] = {}
    for section in S2PJT05_REQUIRED_SECTIONS:
        value = monthly_sections.get(section) if isinstance(monthly_sections, Mapping) else None
        if not isinstance(value, Mapping):
            section_errors.append(f"monthly_sections.{section} must be a mapping")
            continue
        content_ids = [str(content_id) for content_id in value.get("content_ids", []) if str(content_id).strip()]
        if not content_ids:
            section_errors.append(f"monthly_sections.{section}.content_ids must be non-empty")
        missing = [content_id for content_id in content_ids if content_id not in monthly_content_ids]
        if missing:
            section_errors.append(f"monthly_sections.{section}.content_ids not in monthly weekly evidence: " + ", ".join(missing))
        summary = str(value.get("summary") or "")
        if not summary:
            section_errors.append(f"monthly_sections.{section}.summary is required")
        normalized_sections[section] = {**dict(value), "content_ids": content_ids, "summary": summary}

    production_errors: list[str] = []
    for key in (*S2PJT05_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "weekly_report_gate": "pass" if not weekly_errors else "blocked",
        "month_window_gate": "pass" if not month_errors else "blocked",
        "cognitive_delta_gate": "pass" if not cognitive_errors else "blocked",
        "capability_growth_gate": "pass" if not asset_errors else "blocked",
        "conversion_trace_gate": "pass" if not conversion_errors else "blocked",
        "forecast_review_gate": "pass" if not forecast_errors and not focus_errors else "blocked",
        "section_trace_gate": "pass" if not section_errors else "blocked",
        "deterministic_report_gate": "pass",
        "no_side_effect_gate": "pass" if not production_errors else "blocked",
    }
    blocking_reasons.extend(weekly_errors)
    blocking_reasons.extend(month_errors)
    blocking_reasons.extend(cognitive_errors)
    blocking_reasons.extend(asset_errors)
    blocking_reasons.extend(conversion_errors)
    blocking_reasons.extend(forecast_errors)
    blocking_reasons.extend(focus_errors)
    blocking_reasons.extend(section_errors)
    blocking_reasons.extend(production_errors)
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    monthly_report_hash = _s2pjt05_monthly_hash(
        normalized_weekly_reports,
        normalized_sections,
        cognitive_delta,
        normalized_assets,
        normalized_conversions,
        normalized_forecasts,
        normalized_focus,
    )

    return {
        "model_id": S2PJT05_MONTHLY_REPORT_MODEL_ID,
        "acceptance_id": S2PJT05_ACCEPTANCE_ID,
        "task_id": S2PJT05_TASK_ID,
        "phase": "S2PJ",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "month_start": month_start,
        "month_end": month_end,
        "status": status,
        **gates,
        "required_sections": list(S2PJT05_REQUIRED_SECTIONS),
        "monthly_content_ids": sorted(monthly_content_ids),
        "weekly_reports": normalized_weekly_reports,
        "monthly_sections": normalized_sections,
        "cognitive_delta": cognitive_delta,
        "capability_growth": normalized_assets,
        "economic_conversions": normalized_conversions,
        "forecast_reviews": normalized_forecasts,
        "next_month_focus": normalized_focus,
        "calculated_conversion_count": calculated_conversion_count,
        "monthly_report_hash": monthly_report_hash,
        "s2pjt05_monthly_report_ready": status == "pass",
        "actual_roi_policy": "monthly_actual_roi_requires_verifiable_cost_benefit_and_evidence_refs",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pjt05_monthly_report(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    month_start: str,
    month_end: str,
    weekly_reports: Sequence[Mapping[str, Any]],
    cognitive_snapshots: Mapping[str, Any],
    monthly_sections: Mapping[str, Any],
    capability_growth: Sequence[Mapping[str, Any]],
    economic_conversions: Sequence[Mapping[str, Any]],
    forecast_reviews: Sequence[Mapping[str, Any]],
    next_month_focus: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PJT05 monthly report evidence without production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pjt05-monthly-report"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pjt05_monthly_report(
        generated_at=generated_at,
        month_start=month_start,
        month_end=month_end,
        weekly_reports=weekly_reports,
        cognitive_snapshots=cognitive_snapshots,
        monthly_sections=monthly_sections,
        capability_growth=capability_growth,
        economic_conversions=economic_conversions,
        forecast_reviews=forecast_reviews,
        next_month_focus=next_month_focus,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "monthly_report_path": str(run_dir / "adp-s2pjt05-monthly-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pjt05-monthly-report.json", report)
        _write_json(state / S2PJT05_REPORT_FILENAME, report)
    return report


def validate_s2pjt05_monthly_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PJT05_MONTHLY_REPORT_MODEL_ID:
        errors.append("S2PJT05 model_id must be adp-s2pjt05-monthly-report-v1")
    if report.get("task_id") != S2PJT05_TASK_ID:
        errors.append("S2PJT05 task_id must be S2PJT05")
    if report.get("acceptance_id") != S2PJT05_ACCEPTANCE_ID:
        errors.append("S2PJT05 acceptance_id must be ACC-S2PJT05-MONTHLY")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PJT05 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PJT05_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PJT05 local monthly report evidence")
    weekly_reports = report.get("weekly_reports")
    if not isinstance(weekly_reports, list) or not weekly_reports:
        errors.append("S2PJT05 weekly_reports must be a non-empty list")
        weekly_reports = []
    sections = report.get("monthly_sections")
    if not isinstance(sections, Mapping):
        errors.append("S2PJT05 monthly_sections must be a mapping")
        sections = {}
    for section in S2PJT05_REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(f"S2PJT05 monthly_sections missing {section}")
    cognitive_delta = report.get("cognitive_delta")
    if not isinstance(cognitive_delta, Mapping):
        errors.append("S2PJT05 cognitive_delta must be a mapping")
        cognitive_delta = {}
    for key in ("start_summary", "end_summary", "start_viewpoint_ids", "end_viewpoint_ids", "changed_viewpoints"):
        if not cognitive_delta.get(key):
            errors.append(f"S2PJT05 cognitive_delta.{key} is required")
    capability_growth = report.get("capability_growth")
    if not isinstance(capability_growth, list) or not capability_growth:
        errors.append("S2PJT05 capability_growth must be a non-empty list")
        capability_growth = []
    economic_conversions = report.get("economic_conversions")
    if not isinstance(economic_conversions, list) or not economic_conversions:
        errors.append("S2PJT05 economic_conversions must be a non-empty list")
        economic_conversions = []
    if report.get("calculated_conversion_count", 0) < S2PJT05_MIN_VERIFIABLE_CONVERSIONS:
        errors.append("S2PJT05 requires at least one verifiable calculated conversion")
    forecast_reviews = report.get("forecast_reviews")
    if not isinstance(forecast_reviews, list) or not forecast_reviews:
        errors.append("S2PJT05 forecast_reviews must be a non-empty list")
        forecast_reviews = []
    next_month_focus = report.get("next_month_focus")
    if not isinstance(next_month_focus, list) or not next_month_focus:
        errors.append("S2PJT05 next_month_focus must be a non-empty list")
        next_month_focus = []
    if report.get("monthly_report_hash") != _s2pjt05_monthly_hash(
        weekly_reports,
        sections,
        cognitive_delta,
        capability_growth,
        economic_conversions,
        forecast_reviews,
        next_month_focus,
    ):
        errors.append("S2PJT05 monthly_report_hash must match monthly evidence")
    for conversion in economic_conversions:
        if conversion.get("actual_roi_status") == "not_calculable" and conversion.get("actual_roi_value") is not None:
            errors.append(f"{conversion.get('conversion_id')} not_calculable conversion must not include actual_roi_value")
        if conversion.get("actual_roi_status") == "calculated" and conversion.get("actual_roi_value") is None:
            errors.append(f"{conversion.get('conversion_id')} calculated conversion requires actual_roi_value")
    for gate in S2PJT05_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PJT05 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PJT05 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pjt05_monthly_report_ready") is not True:
        errors.append("passing S2PJT05 report requires s2pjt05_monthly_report_ready=true")
    return errors


def _s2pht05_content_quality_hash(
    dependency_receipts: Sequence[Mapping[str, Any]],
    gold_items: Sequence[Mapping[str, Any]],
    stage1_regression_checks: Sequence[Mapping[str, Any]],
    manual_review_samples: Sequence[Mapping[str, Any]],
) -> str:
    payload = {
        "dependencies": sorted(
            [
            {
                "task_id": str(receipt.get("task_id") or ""),
                "status": str(receipt.get("status") or ""),
                "evidence_refs": sorted(str(ref) for ref in receipt.get("evidence_refs", []) if str(ref).strip()),
            }
            for receipt in dependency_receipts
            ],
            key=lambda value: value["task_id"],
        ),
        "gold_items": sorted(
            [
            {
                "gold_id": str(item.get("gold_id") or item.get("item_id") or ""),
                "content_id": str(item.get("content_id") or ""),
                "dimension_scores": {
                    dimension: float(item.get("dimension_scores", {}).get(dimension, 0.0))
                    for dimension in S2PHT05_REQUIRED_GOLD_DIMENSIONS
                    if isinstance(item.get("dimension_scores"), Mapping)
                },
                "claim_entailment": str(item.get("claim_entailment") or ""),
                "quote_locations": sorted(str(location.get("location") or location.get("source_ref") or "") for location in item.get("quote_locations", []) if isinstance(location, Mapping)),
                "template_similarity": float(item.get("template_similarity") or 0.0),
                "counterevidence_refs": sorted(str(ref) for ref in item.get("counterevidence_refs", []) if str(ref).strip()),
            }
            for item in gold_items
            ],
            key=lambda value: value["gold_id"],
        ),
        "stage1_regression": sorted(
            [
            {
                "check_id": str(check.get("check_id") or ""),
                "status": str(check.get("status") or ""),
                "evidence_refs": sorted(str(ref) for ref in check.get("evidence_refs", []) if str(ref).strip()),
            }
            for check in stage1_regression_checks
            ],
            key=lambda value: value["check_id"],
        ),
        "manual_review": sorted(
            [
            {
                "review_id": str(sample.get("review_id") or ""),
                "gold_id": str(sample.get("gold_id") or sample.get("item_id") or ""),
                "verdict": str(sample.get("verdict") or ""),
                "evidence_refs": sorted(str(ref) for ref in sample.get("evidence_refs", []) if str(ref).strip()),
            }
            for sample in manual_review_samples
            ],
            key=lambda value: value["review_id"],
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_s2pht05_content_quality_gate_report(
    *,
    generated_at: str,
    dependency_receipts: Sequence[Mapping[str, Any]],
    gold_items: Sequence[Mapping[str, Any]],
    stage1_regression_checks: Sequence[Mapping[str, Any]],
    manual_review_samples: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local-only S2PHT05 semantic content quality gate evidence."""

    production_gate = dict(production_gate_state or {})
    dependency_errors: list[str] = []
    normalized_dependencies: list[dict[str, Any]] = []
    observed_dependencies: set[str] = set()
    for index, receipt in enumerate(dependency_receipts):
        task_id = str(receipt.get("task_id") or "")
        status = str(receipt.get("status") or "")
        evidence_refs = [str(ref) for ref in receipt.get("evidence_refs", []) if str(ref).strip()]
        if task_id not in S2PHT05_REQUIRED_DEPENDENCY_TASKS:
            dependency_errors.append(f"dependency_receipts[{index}].task_id must be one of S2PHT01-S2PHT04")
        if status != "pass":
            dependency_errors.append(f"{task_id or index} dependency status must be pass")
        if not evidence_refs:
            dependency_errors.append(f"{task_id or index} dependency evidence_refs must be non-empty")
        if receipt.get("v7_2_revalidated") is not True:
            dependency_errors.append(f"{task_id or index} dependency must record v7_2_revalidated=true")
        observed_dependencies.add(task_id)
        normalized_dependencies.append({**dict(receipt), "task_id": task_id, "status": status, "evidence_refs": evidence_refs})
    missing_dependencies = [task_id for task_id in S2PHT05_REQUIRED_DEPENDENCY_TASKS if task_id not in observed_dependencies]
    if missing_dependencies:
        dependency_errors.append("missing S2PHT05 dependency receipts: " + ", ".join(missing_dependencies))

    gold_errors: list[str] = []
    entailment_errors: list[str] = []
    quote_errors: list[str] = []
    template_errors: list[str] = []
    counterevidence_errors: list[str] = []
    action_errors: list[str] = []
    normalized_gold_items: list[dict[str, Any]] = []
    gold_ids: set[str] = set()
    min_dimension_scores = {dimension: 5.0 for dimension in S2PHT05_REQUIRED_GOLD_DIMENSIONS}
    max_template_similarity_observed = 0.0
    for index, item in enumerate(gold_items):
        gold_id = str(item.get("gold_id") or item.get("item_id") or "")
        content_id = str(item.get("content_id") or "")
        if not gold_id:
            gold_errors.append(f"gold_items[{index}].gold_id is required")
        if gold_id in gold_ids:
            gold_errors.append(f"duplicate S2PHT05 gold_id: {gold_id}")
        gold_ids.add(gold_id)
        if not content_id:
            gold_errors.append(f"{gold_id or index} content_id is required")
        evidence_refs = [str(ref) for ref in item.get("evidence_refs", []) if str(ref).strip()]
        if not evidence_refs:
            gold_errors.append(f"{gold_id or index} evidence_refs must be non-empty")
        if not str(item.get("claim_text") or ""):
            entailment_errors.append(f"{gold_id or index} claim_text is required")
        entailment = str(item.get("claim_entailment") or "")
        if entailment not in S2PHT05_ALLOWED_ENTAILMENT_STATES:
            entailment_errors.append(f"{gold_id or index} claim_entailment must be supported or partially_supported")
        dimensions = item.get("dimension_scores")
        if not isinstance(dimensions, Mapping):
            gold_errors.append(f"{gold_id or index} dimension_scores must be a mapping")
            dimensions = {}
        normalized_scores: dict[str, float] = {}
        for dimension in S2PHT05_REQUIRED_GOLD_DIMENSIONS:
            try:
                score = float(dimensions.get(dimension))
            except (TypeError, ValueError):
                score = -1.0
            normalized_scores[dimension] = score
            min_dimension_scores[dimension] = min(min_dimension_scores[dimension], score)
            if score < S2PHT05_MIN_DIMENSION_SCORE:
                gold_errors.append(f"{gold_id or index} {dimension} score must be >= {S2PHT05_MIN_DIMENSION_SCORE:g}")
        quote_locations = item.get("quote_locations")
        if not isinstance(quote_locations, list) or not quote_locations:
            quote_errors.append(f"{gold_id or index} quote_locations must be non-empty")
            quote_locations = []
        for location_index, location in enumerate(quote_locations):
            if not isinstance(location, Mapping):
                quote_errors.append(f"{gold_id or index} quote_locations[{location_index}] must be a mapping")
                continue
            if not str(location.get("source_ref") or "") or not str(location.get("location") or ""):
                quote_errors.append(f"{gold_id or index} quote_locations[{location_index}] requires source_ref and location")
        try:
            template_similarity = float(item.get("template_similarity"))
        except (TypeError, ValueError):
            template_similarity = 1.0
        max_template_similarity_observed = max(max_template_similarity_observed, template_similarity)
        if template_similarity > S2PHT05_MAX_TEMPLATE_SIMILARITY:
            template_errors.append(f"{gold_id or index} template_similarity exceeds {S2PHT05_MAX_TEMPLATE_SIMILARITY:g}")
        counter_refs = [str(ref) for ref in item.get("counterevidence_refs", []) if str(ref).strip()]
        if not counter_refs:
            counterevidence_errors.append(f"{gold_id or index} counterevidence_refs must be non-empty")
        boundary_conditions = [str(value) for value in item.get("boundary_conditions", []) if str(value).strip()]
        if not boundary_conditions:
            counterevidence_errors.append(f"{gold_id or index} boundary_conditions must be non-empty")
        personal_action = item.get("personal_action")
        if not isinstance(personal_action, Mapping):
            action_errors.append(f"{gold_id or index} personal_action must be a mapping")
            personal_action = {}
        action_refs = [str(ref) for ref in personal_action.get("evidence_refs", []) if str(ref).strip()]
        for field in ("action_id", "horizon", "description"):
            if not str(personal_action.get(field) or ""):
                action_errors.append(f"{gold_id or index} personal_action.{field} is required")
        if not action_refs:
            action_errors.append(f"{gold_id or index} personal_action.evidence_refs must be non-empty")
        if not str(item.get("chinese_summary") or ""):
            gold_errors.append(f"{gold_id or index} chinese_summary is required")
        normalized_gold_items.append(
            {
                **dict(item),
                "gold_id": gold_id,
                "content_id": content_id,
                "dimension_scores": normalized_scores,
                "evidence_refs": evidence_refs,
                "claim_entailment": entailment,
                "quote_locations": [dict(location) for location in quote_locations if isinstance(location, Mapping)],
                "template_similarity": template_similarity,
                "counterevidence_refs": counter_refs,
                "boundary_conditions": boundary_conditions,
                "personal_action": {**dict(personal_action), "evidence_refs": action_refs},
            }
        )
    if len(normalized_gold_items) < S2PHT05_MIN_GOLD_ITEMS:
        gold_errors.append(f"S2PHT05 requires at least {S2PHT05_MIN_GOLD_ITEMS} gold items")

    regression_errors: list[str] = []
    normalized_regressions: list[dict[str, Any]] = []
    observed_regressions: set[str] = set()
    for index, check in enumerate(stage1_regression_checks):
        check_id = str(check.get("check_id") or "")
        status = str(check.get("status") or "")
        evidence_refs = [str(ref) for ref in check.get("evidence_refs", []) if str(ref).strip()]
        if check_id not in S2PHT05_REQUIRED_STAGE1_REGRESSION_CHECKS:
            regression_errors.append(f"stage1_regression_checks[{index}].check_id is not required")
        if status != "pass":
            regression_errors.append(f"{check_id or index} stage1 regression status must be pass")
        if not evidence_refs:
            regression_errors.append(f"{check_id or index} stage1 regression evidence_refs must be non-empty")
        observed_regressions.add(check_id)
        normalized_regressions.append({**dict(check), "check_id": check_id, "status": status, "evidence_refs": evidence_refs})
    missing_regressions = [check_id for check_id in S2PHT05_REQUIRED_STAGE1_REGRESSION_CHECKS if check_id not in observed_regressions]
    if missing_regressions:
        regression_errors.append("missing Stage 1 regression checks: " + ", ".join(missing_regressions))

    manual_errors: list[str] = []
    normalized_manual_samples: list[dict[str, Any]] = []
    for index, sample in enumerate(manual_review_samples):
        review_id = str(sample.get("review_id") or "")
        gold_id = str(sample.get("gold_id") or sample.get("item_id") or "")
        evidence_refs = [str(ref) for ref in sample.get("evidence_refs", []) if str(ref).strip()]
        if not review_id:
            manual_errors.append(f"manual_review_samples[{index}].review_id is required")
        if gold_id not in gold_ids:
            manual_errors.append(f"{review_id or index} manual review gold_id must reference a gold item")
        if str(sample.get("verdict") or "") != "pass":
            manual_errors.append(f"{review_id or index} manual review verdict must be pass")
        if not str(sample.get("reviewer_role") or ""):
            manual_errors.append(f"{review_id or index} reviewer_role is required")
        if not evidence_refs:
            manual_errors.append(f"{review_id or index} manual review evidence_refs must be non-empty")
        normalized_manual_samples.append({**dict(sample), "review_id": review_id, "gold_id": gold_id, "evidence_refs": evidence_refs})
    if len(normalized_manual_samples) < S2PHT05_MIN_MANUAL_REVIEW_SAMPLES:
        manual_errors.append(f"S2PHT05 requires at least {S2PHT05_MIN_MANUAL_REVIEW_SAMPLES} manual review samples")

    production_errors: list[str] = []
    for key in (*S2PHT05_REQUIRED_PRODUCTION_FALSE_FLAGS, "production_restore_executed"):
        if production_gate.get(key, False) is not False:
            production_errors.append(f"production_gate_state.{key} must be false")

    gates = {
        "dependency_receipt_gate": "pass" if not dependency_errors else "blocked",
        "gold_dimension_gate": "pass" if not gold_errors else "blocked",
        "entailment_gate": "pass" if not entailment_errors else "blocked",
        "quote_location_gate": "pass" if not quote_errors else "blocked",
        "template_rate_gate": "pass" if not template_errors else "blocked",
        "counterevidence_gate": "pass" if not counterevidence_errors else "blocked",
        "personal_action_gate": "pass" if not action_errors else "blocked",
        "stage1_regression_gate": "pass" if not regression_errors else "blocked",
        "manual_review_gate": "pass" if not manual_errors else "blocked",
        "deterministic_gate": "pass",
        "no_side_effect_gate": "pass" if not production_errors else "blocked",
    }
    blocking_reasons = [
        *dependency_errors,
        *gold_errors,
        *entailment_errors,
        *quote_errors,
        *template_errors,
        *counterevidence_errors,
        *action_errors,
        *regression_errors,
        *manual_errors,
        *production_errors,
    ]
    status = "pass" if not blocking_reasons and all(value == "pass" for value in gates.values()) else "blocked"
    quality_gate_hash = _s2pht05_content_quality_hash(
        normalized_dependencies,
        normalized_gold_items,
        normalized_regressions,
        normalized_manual_samples,
    )
    return {
        "model_id": S2PHT05_CONTENT_QUALITY_MODEL_ID,
        "acceptance_id": S2PHT05_ACCEPTANCE_ID,
        "task_id": S2PHT05_TASK_ID,
        "phase": "S2PH",
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        **gates,
        "required_dependency_tasks": list(S2PHT05_REQUIRED_DEPENDENCY_TASKS),
        "required_gold_dimensions": list(S2PHT05_REQUIRED_GOLD_DIMENSIONS),
        "required_gold_item_count": S2PHT05_MIN_GOLD_ITEMS,
        "minimum_dimension_score": S2PHT05_MIN_DIMENSION_SCORE,
        "max_template_similarity_allowed": S2PHT05_MAX_TEMPLATE_SIMILARITY,
        "minimum_manual_review_samples": S2PHT05_MIN_MANUAL_REVIEW_SAMPLES,
        "required_stage1_regression_checks": list(S2PHT05_REQUIRED_STAGE1_REGRESSION_CHECKS),
        "dependency_receipts": normalized_dependencies,
        "gold_items": normalized_gold_items,
        "stage1_regression_checks": normalized_regressions,
        "manual_review_samples": normalized_manual_samples,
        "gold_item_count": len(normalized_gold_items),
        "manual_review_sample_count": len(normalized_manual_samples),
        "min_dimension_scores": min_dimension_scores,
        "max_template_similarity_observed": max_template_similarity_observed,
        "quality_gate_hash": quality_gate_hash,
        "s2pht05_content_quality_gate_ready": status == "pass",
        "owner_experience_accepted": False,
        "stage2_production_accepted": False,
        "integrated_production_accepted": False,
        "production_affected": False,
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
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def run_s2pht05_content_quality_gate(
    *,
    state_dir: str | Path,
    date: str,
    generated_at: str,
    dependency_receipts: Sequence[Mapping[str, Any]],
    gold_items: Sequence[Mapping[str, Any]],
    stage1_regression_checks: Sequence[Mapping[str, Any]],
    manual_review_samples: Sequence[Mapping[str, Any]],
    production_gate_state: Mapping[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Persist S2PHT05 content quality gate evidence without production side effects."""

    state = Path(state_dir).resolve()
    run_dir = state / "runs" / date.replace("-", "") / "s2pht05-content-quality-gate"
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
    report = build_s2pht05_content_quality_gate_report(
        generated_at=generated_at,
        dependency_receipts=dependency_receipts,
        gold_items=gold_items,
        stage1_regression_checks=stage1_regression_checks,
        manual_review_samples=manual_review_samples,
        production_gate_state=production_gate_state,
    )
    report.update(
        {
            "date": date,
            "timezone": DEFAULT_TIMEZONE,
            "state_dir": str(state),
            "run_dir": str(run_dir),
            "content_quality_gate_report_path": str(run_dir / "adp-s2pht05-content-quality-gate-report.json"),
        }
    )
    if write:
        _write_json(run_dir / "adp-s2pht05-content-quality-gate-report.json", report)
        _write_json(state / S2PHT05_REPORT_FILENAME, report)
    return report


def validate_s2pht05_content_quality_gate_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2PHT05_CONTENT_QUALITY_MODEL_ID:
        errors.append("S2PHT05 model_id must be adp-s2pht05-content-quality-gate-v1")
    if report.get("task_id") != S2PHT05_TASK_ID:
        errors.append("S2PHT05 task_id must be S2PHT05")
    if report.get("acceptance_id") != S2PHT05_ACCEPTANCE_ID:
        errors.append("S2PHT05 acceptance_id must be ACC-S2PHT05-CONTENT-GATE")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PHT05 status must be pass or blocked")
    for key in (
        "owner_experience_accepted",
        *S2PHT05_REQUIRED_PRODUCTION_FALSE_FLAGS,
        "production_affected",
        "smtp_transport_allowed",
    ):
        if report.get(key) is not False:
            errors.append(f"{key} must be false for S2PHT05 local content quality gate evidence")
    dependencies = report.get("dependency_receipts")
    if not isinstance(dependencies, list):
        errors.append("S2PHT05 dependency_receipts must be a list")
        dependencies = []
    observed_dependencies = {str(receipt.get("task_id") or "") for receipt in dependencies if isinstance(receipt, Mapping)}
    missing_dependencies = [task_id for task_id in S2PHT05_REQUIRED_DEPENDENCY_TASKS if task_id not in observed_dependencies]
    if missing_dependencies:
        errors.append("S2PHT05 dependency_receipts missing: " + ", ".join(missing_dependencies))
    gold_items = report.get("gold_items")
    if not isinstance(gold_items, list) or len(gold_items) < S2PHT05_MIN_GOLD_ITEMS:
        errors.append(f"S2PHT05 gold_items must include at least {S2PHT05_MIN_GOLD_ITEMS} items")
        gold_items = []
    for index, item in enumerate(gold_items):
        if not isinstance(item, Mapping):
            errors.append(f"gold_items[{index}] must be a mapping")
            continue
        scores = item.get("dimension_scores")
        if not isinstance(scores, Mapping):
            errors.append(f"gold_items[{index}].dimension_scores must be a mapping")
            scores = {}
        for dimension in S2PHT05_REQUIRED_GOLD_DIMENSIONS:
            try:
                score = float(scores.get(dimension))
            except (TypeError, ValueError):
                score = -1.0
            if score < S2PHT05_MIN_DIMENSION_SCORE:
                errors.append(f"{item.get('gold_id') or index} {dimension} score must be >= {S2PHT05_MIN_DIMENSION_SCORE:g}")
        if item.get("claim_entailment") not in S2PHT05_ALLOWED_ENTAILMENT_STATES:
            errors.append(f"{item.get('gold_id') or index} claim_entailment must be supported or partially_supported")
        if not item.get("quote_locations"):
            errors.append(f"{item.get('gold_id') or index} quote_locations must be non-empty")
        if float(item.get("template_similarity") or 1.0) > S2PHT05_MAX_TEMPLATE_SIMILARITY:
            errors.append(f"{item.get('gold_id') or index} template_similarity exceeds {S2PHT05_MAX_TEMPLATE_SIMILARITY:g}")
        if not item.get("counterevidence_refs"):
            errors.append(f"{item.get('gold_id') or index} counterevidence_refs must be non-empty")
        if not item.get("boundary_conditions"):
            errors.append(f"{item.get('gold_id') or index} boundary_conditions must be non-empty")
        personal_action = item.get("personal_action")
        if not isinstance(personal_action, Mapping) or not personal_action.get("action_id") or not personal_action.get("evidence_refs"):
            errors.append(f"{item.get('gold_id') or index} personal_action must include action_id and evidence_refs")
    regression_checks = report.get("stage1_regression_checks")
    if not isinstance(regression_checks, list):
        errors.append("S2PHT05 stage1_regression_checks must be a list")
        regression_checks = []
    observed_regressions = {str(check.get("check_id") or "") for check in regression_checks if isinstance(check, Mapping)}
    missing_regressions = [check_id for check_id in S2PHT05_REQUIRED_STAGE1_REGRESSION_CHECKS if check_id not in observed_regressions]
    if missing_regressions:
        errors.append("S2PHT05 missing Stage 1 regression checks: " + ", ".join(missing_regressions))
    manual_samples = report.get("manual_review_samples")
    if not isinstance(manual_samples, list) or len(manual_samples) < S2PHT05_MIN_MANUAL_REVIEW_SAMPLES:
        errors.append(f"S2PHT05 manual_review_samples must include at least {S2PHT05_MIN_MANUAL_REVIEW_SAMPLES} samples")
        manual_samples = []
    if report.get("quality_gate_hash") != _s2pht05_content_quality_hash(dependencies, gold_items, regression_checks, manual_samples):
        errors.append("S2PHT05 quality_gate_hash must match quality evidence")
    for gate in S2PHT05_REQUIRED_GATES:
        if report.get("status") == "pass" and report.get(gate) != "pass":
            errors.append(f"passing S2PHT05 report requires {gate}=pass")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PHT05 report requires blocking_reasons")
    if report.get("status") == "pass" and report.get("s2pht05_content_quality_gate_ready") is not True:
        errors.append("passing S2PHT05 report requires s2pht05_content_quality_gate_ready=true")
    return errors


def fetch_s2p2_top_journal_batches(*, generated_at: str, max_records: int = 3) -> dict[str, dict[str, Any]]:
    return {
        journal: ingest_latest_top_journal(
            journal=journal,
            generated_at=generated_at,
            max_records=max_records,
        )
        for journal in S2P2_REQUIRED_JOURNALS
    }


def fetch_s2pct02_science_batches(*, generated_at: str, max_records: int = 3) -> dict[str, dict[str, Any]]:
    return {
        journal: ingest_latest_top_journal(
            journal=journal,
            generated_at=generated_at,
            max_records=max_records,
        )
        for journal in S2PCT02_REQUIRED_JOURNALS
    }


def fetch_s2pct03_lancet_batches(*, generated_at: str, max_records: int = 3) -> dict[str, dict[str, Any]]:
    return {
        journal: ingest_latest_top_journal(
            journal=journal,
            generated_at=generated_at,
            max_records=max_records,
        )
        for journal in S2PCT03_REQUIRED_JOURNALS
    }


def fetch_s2p1_preprint_batches(
    *,
    generated_at: str,
    interval: str = "1d",
    max_records: int = 3,
) -> dict[str, dict[str, Any]]:
    return {
        server: ingest_latest_preprints(
            server=server,
            generated_at=generated_at,
            interval=interval,
            max_records=max_records,
        )
        for server in S2P1_REQUIRED_SERVERS
    }


def build_s2p1_preprint_replay_shadow_evidence(
    *,
    state_dir: str | Path,
    generated_at: str,
    start_date: str | None = None,
    end_date: str | None = None,
    count: int = S2P1_REPLAY_REQUIRED_DATES,
    lookback_days: int = 7,
    max_records: int = 3,
    source_batches_by_date: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
    fetcher: Any | None = None,
    write: bool = True,
    polite_delay_seconds: float = 0.0,
) -> dict[str, Any]:
    """Build terminal replay plus 48h no-production shadow evidence for S2P1T01."""

    state = Path(state_dir).resolve()
    if write:
        state.mkdir(parents=True, exist_ok=True)
    dates = _replay_dates(start_date=start_date, end_date=end_date, count=count, generated_at=generated_at)
    if not dates:
        replay_report = _blocked_replay_report(generated_at, state, ["date range produced no replay dates"], requested_count=count)
        shadow_report = _shadow_evidence_report(generated_at=generated_at, state=state, daily_reports=[], replay_report=replay_report)
        return _combined_replay_shadow_report(generated_at, state, replay_report, shadow_report, {}, write=write)
    if lookback_days < 1:
        replay_report = _blocked_replay_report(generated_at, state, ["lookback_days must be >= 1"], requested_count=count)
        shadow_report = _shadow_evidence_report(generated_at=generated_at, state=state, daily_reports=[], replay_report=replay_report)
        return _combined_replay_shadow_report(generated_at, state, replay_report, shadow_report, {}, write=write)

    daily_reports: list[dict[str, Any]] = []
    selected_source_ids: list[str] = []
    selected_canonical_ids: list[str] = []
    source_batches_by_server: dict[str, Mapping[str, Any]] = {}
    blocking_reasons: list[str] = []
    queue_state = _load_json(state / S2P1_QUEUE_FILENAME) if (state / S2P1_QUEUE_FILENAME).exists() else None
    for index, as_of in enumerate(dates, start=1):
        source_batches = (
            source_batches_by_date.get(as_of.isoformat(), {})
            if isinstance(source_batches_by_date, Mapping)
            else _fetch_replay_source_batches(
                as_of=as_of,
                generated_at=generated_at,
                lookback_days=lookback_days,
                max_records=max_records,
                fetcher=fetcher,
            )
        )
        if not isinstance(source_batches, Mapping):
            source_batches = {}
        for server in S2P1_REQUIRED_SERVERS:
            batch = source_batches.get(server)
            if isinstance(batch, Mapping):
                source_batches_by_server[server] = batch
        report = run_s2p1_preprint_shadow_daily(
            state_dir=state,
            date=as_of.isoformat(),
            generated_at=generated_at,
            source_batches=source_batches,
            queue=queue_state,
            recent_source_ids=selected_source_ids,
            write=write,
        )
        report["replay_day_index"] = index
        report["accelerated_historical_shadow"] = True
        report["as_of_date"] = as_of.isoformat()
        daily_reports.append(report)
        queue_candidate = report.get("daily_report", {}).get("candidate_queue") if isinstance(report.get("daily_report"), Mapping) else None
        if isinstance(queue_candidate, Mapping):
            queue_state = queue_candidate
        if report.get("status") != "pass":
            blocking_reasons.extend(f"{as_of.isoformat()}: {reason}" for reason in report.get("blocking_reasons") or ["shadow daily blocked"])
        else:
            source_id = str(report.get("selected_source_id") or "")
            canonical_id = str((report.get("content_ledger_row") or {}).get("canonical_document_id") or "")
            if source_id:
                selected_source_ids.append(source_id)
            if canonical_id:
                selected_canonical_ids.append(canonical_id)
        if polite_delay_seconds > 0 and index < len(dates) and source_batches_by_date is None:
            time.sleep(float(polite_delay_seconds))

    replay_report = _replay_report(
        generated_at=generated_at,
        state=state,
        requested_count=count,
        dates=dates,
        daily_reports=daily_reports,
        selected_source_ids=selected_source_ids,
        selected_canonical_ids=selected_canonical_ids,
        blocking_reasons=blocking_reasons,
    )
    shadow_report = _shadow_evidence_report(generated_at=generated_at, state=state, daily_reports=daily_reports, replay_report=replay_report)
    promotion_report = build_s2p1_preprint_promotion_report(
        generated_at=generated_at,
        source_batches=source_batches_by_server,
        replay_report=replay_report,
        shadow_report=shadow_report,
    )
    return _combined_replay_shadow_report(generated_at, state, replay_report, shadow_report, promotion_report, write=write)


def validate_s2p1_preprint_replay_shadow_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != S2P1_PREPRINT_REPLAY_MODEL_ID:
        errors.append("S2P1 replay-shadow report model_id must be adp-s2p1-preprint-terminal-replay-v1")
    replay = report.get("replay_report") if isinstance(report.get("replay_report"), Mapping) else {}
    shadow = report.get("shadow_report") if isinstance(report.get("shadow_report"), Mapping) else {}
    promotion = report.get("promotion_report") if isinstance(report.get("promotion_report"), Mapping) else {}
    if replay.get("status") != "pass":
        errors.append("embedded S2P1 replay_report must pass")
    if shadow.get("status") != "pass":
        errors.append("embedded S2P1 shadow_report must pass")
    if promotion.get("status") != "pass":
        errors.append("embedded S2P1 promotion_report must pass")
    if report.get("formal_production_inclusion") is not False:
        errors.append("formal_production_inclusion must be false")
    if report.get("github_cloud_schedule_enabled") is not False:
        errors.append("github_cloud_schedule_enabled must be false")
    if report.get("real_smtp_sent") is not False:
        errors.append("real_smtp_sent must be false")
    return errors


def _fetch_replay_source_batches(
    *,
    as_of: Date,
    generated_at: str,
    lookback_days: int,
    max_records: int,
    fetcher: Any | None,
) -> dict[str, dict[str, Any]]:
    start = as_of - timedelta(days=int(lookback_days) - 1)
    interval = f"{start.isoformat()}/{as_of.isoformat()}"
    return {
        server: ingest_latest_preprints(
            server=server,
            generated_at=generated_at,
            interval=interval,
            max_records=max_records,
            fetcher=fetcher,
        )
        for server in S2P1_REQUIRED_SERVERS
    }


def _replay_report(
    *,
    generated_at: str,
    state: Path,
    requested_count: int,
    dates: Sequence[Date],
    daily_reports: Sequence[Mapping[str, Any]],
    selected_source_ids: Sequence[str],
    selected_canonical_ids: Sequence[str],
    blocking_reasons: Sequence[str],
) -> dict[str, Any]:
    daily_records = [_daily_replay_record(as_of, report) for as_of, report in zip(dates, daily_reports, strict=False)]
    future_leakage = [record for record in daily_records if record.get("future_leakage")]
    duplicate_selected = _duplicate_values(selected_source_ids)
    duplicate_canonical = _duplicate_values(selected_canonical_ids)
    queue_breaks = [
        record
        for record in daily_records
        if record.get("status") == "pass" and not (record.get("queue_persisted") and record.get("ledger_persisted") and record.get("email_preview_persisted"))
    ]
    p0_p1_records = [record for record in daily_records if int(record.get("p0_p1_blocker_count") or 0) > 0]
    reasons = list(blocking_reasons)
    if len({date.isoformat() for date in dates}) < S2P1_REPLAY_REQUIRED_DATES:
        reasons.append("S2P1 replay requires 30 unique dates")
    if len(daily_reports) < requested_count:
        reasons.append("S2P1 replay did not produce all requested daily reports")
    if duplicate_selected:
        reasons.append("S2P1 replay duplicate selected source IDs: " + ", ".join(duplicate_selected))
    if duplicate_canonical:
        reasons.append("S2P1 replay duplicate canonical document IDs: " + ", ".join(duplicate_canonical))
    if future_leakage:
        reasons.append("S2P1 replay has future-dated selected preprints")
    if queue_breaks:
        reasons.append("S2P1 replay queue/ledger/email persistence continuity failed")
    if p0_p1_records:
        reasons.append("S2P1 replay has P0/P1 blockers")
    status = "pass" if not reasons else "blocked"
    return {
        "model_id": S2P1_PREPRINT_REPLAY_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "state_dir": str(state),
        "required_replay_count": S2P1_REPLAY_REQUIRED_DATES,
        "requested_replay_count": int(requested_count),
        "replay_count": len(daily_reports),
        "success_count": len([report for report in daily_reports if report.get("status") == "pass"]),
        "unique_date_count": len({date.isoformat() for date in dates}),
        "unique_selected_source_count": len(set(selected_source_ids)),
        "unique_selected_canonical_count": len(set(selected_canonical_ids)),
        "real_preprint_source_id_count": len([source_id for source_id in selected_source_ids if _is_preprint_source_id(source_id)]),
        "future_leakage_count": len(future_leakage),
        "duplicate_selected_count": len(duplicate_selected),
        "duplicate_canonical_count": len(duplicate_canonical),
        "queue_continuity_break_count": len(queue_breaks),
        "p0_p1_blocker_count": len(p0_p1_records),
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "video_generated": False,
        "daily_records": daily_records,
        "blocking_reasons": sorted(set(reasons)),
    }


def _daily_replay_record(as_of: Date, report: Mapping[str, Any]) -> dict[str, Any]:
    source_item = (
        report.get("daily_report", {}).get("daily_input", {}).get("source_item", {})
        if isinstance(report.get("daily_report"), Mapping)
        else {}
    )
    if not isinstance(source_item, Mapping):
        source_item = {}
    selected_source_id = str(report.get("selected_source_id") or source_item.get("source_id") or "")
    source_date = _source_item_preprint_date(source_item)
    validation_errors = report.get("validation_errors") if isinstance(report.get("validation_errors"), list) else []
    blocking_reasons = [str(reason) for reason in report.get("blocking_reasons") or []]
    p0_p1_blockers = [
        reason
        for reason in [*blocking_reasons, *[str(error) for error in validation_errors]]
        if "P0" in reason or "P1" in reason or "claim" in reason.lower() or "validation" in reason.lower()
    ]
    return {
        "date": as_of.isoformat(),
        "status": str(report.get("status") or "blocked"),
        "selected_source_id": selected_source_id,
        "selected_title": str(report.get("selected_title") or source_item.get("title") or ""),
        "canonical_document_id": str((report.get("content_ledger_row") or {}).get("canonical_document_id") or _canonical_document_id(source_item)),
        "source_preprint_date": source_date,
        "future_leakage": bool(source_date and source_date > as_of.isoformat()),
        "queue_persisted": Path(str(report.get("candidate_queue_path") or "")).is_file(),
        "ledger_persisted": Path(str(report.get("content_ledger_path") or "")).is_file(),
        "email_preview_persisted": Path(str((report.get("email_preview_paths") or {}).get("plain") or "")).is_file(),
        "daily_input_ready": bool(report.get("daily_input_ready") is True),
        "daily_run_status": str(report.get("daily_run_status") or ""),
        "p0_p1_blocker_count": len(p0_p1_blockers),
        "blocking_reasons": blocking_reasons,
    }


def _shadow_evidence_report(
    *,
    generated_at: str,
    state: Path,
    daily_reports: Sequence[Mapping[str, Any]],
    replay_report: Mapping[str, Any],
) -> dict[str, Any]:
    dates = [str(report.get("date") or report.get("as_of_date") or "") for report in daily_reports if str(report.get("date") or report.get("as_of_date") or "")]
    shadow_hours = _shadow_hours_from_dates(dates)
    reasons: list[str] = []
    if replay_report.get("status") != "pass":
        reasons.append("S2P1 shadow evidence requires passing replay report")
    if shadow_hours < S2P1_SHADOW_REQUIRED_HOURS:
        reasons.append("S2P1 shadow requires at least 48 hours")
    if any(report.get("status") != "pass" for report in daily_reports):
        reasons.append("S2P1 shadow daily reports must all pass")
    if any(report.get("formal_production_inclusion") is not False for report in daily_reports):
        reasons.append("S2P1 shadow daily formal_production_inclusion must be false")
    if any(report.get("real_smtp_sent") is not False for report in daily_reports):
        reasons.append("S2P1 shadow daily must not send SMTP")
    if any(report.get("production_affected") is not False for report in daily_reports):
        reasons.append("S2P1 shadow daily must not affect production")
    return {
        "model_id": S2P1_PREPRINT_SHADOW_EVIDENCE_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if not reasons else "blocked",
        "state_dir": str(state),
        "shadow_hours": shadow_hours,
        "shadow_tick_count": len(daily_reports),
        "accelerated_historical_shadow": True,
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "production_affected": False,
        "video_required": False,
        "daily_report_refs": [str(report.get("run_dir") or "") for report in daily_reports],
        "blocking_reasons": reasons,
    }


def _combined_replay_shadow_report(
    generated_at: str,
    state: Path,
    replay_report: Mapping[str, Any],
    shadow_report: Mapping[str, Any],
    promotion_report: Mapping[str, Any],
    *,
    write: bool,
) -> dict[str, Any]:
    status = "pass" if replay_report.get("status") == shadow_report.get("status") == promotion_report.get("status") == "pass" else "blocked"
    artifact_paths = {
        "replay_report": str(state / S2P1_REPLAY_REPORT_FILENAME),
        "shadow_report": str(state / S2P1_SHADOW_EVIDENCE_FILENAME),
        "promotion_report": str(state / S2P1_PROMOTION_REPORT_FILENAME),
        "queue": str(state / S2P1_QUEUE_FILENAME),
        "ledger": str(state / S2P1_LEDGER_FILENAME),
    }
    report = {
        "model_id": S2P1_PREPRINT_REPLAY_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": status,
        "s2p1_source_promotion_accepted": status == "pass",
        "stage2_production_accepted": False,
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "real_release_uploaded": False,
        "video_generated": False,
        "replay_report": replay_report,
        "shadow_report": shadow_report,
        "promotion_report": promotion_report,
        "artifact_paths": artifact_paths,
        "blocking_reasons": sorted(set([*replay_report.get("blocking_reasons", []), *shadow_report.get("blocking_reasons", []), *promotion_report.get("blocking_reasons", [])])),
    }
    report["validation_errors"] = validate_s2p1_preprint_replay_shadow_report(report) if status == "pass" else []
    if write:
        _write_json(state / S2P1_REPLAY_REPORT_FILENAME, replay_report)
        _write_json(state / S2P1_SHADOW_EVIDENCE_FILENAME, shadow_report)
        _write_json(state / S2P1_PROMOTION_REPORT_FILENAME, promotion_report)
        _write_json(state / "stage2_s2p1_preprint_replay_shadow_report.json", report)
    return report


def _blocked_replay_report(generated_at: str, state: Path, reasons: Sequence[str], *, requested_count: int) -> dict[str, Any]:
    return {
        "model_id": S2P1_PREPRINT_REPLAY_MODEL_ID,
        "acceptance_id": S2P1_ACCEPTANCE_ID,
        "task_id": S2P1_TASK_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "blocked",
        "state_dir": str(state),
        "required_replay_count": S2P1_REPLAY_REQUIRED_DATES,
        "requested_replay_count": int(requested_count),
        "replay_count": 0,
        "success_count": 0,
        "unique_date_count": 0,
        "future_leakage_count": 0,
        "duplicate_selected_count": 0,
        "p0_p1_blocker_count": 0,
        "blocking_reasons": list(reasons),
    }


def _replay_dates(*, start_date: str | None, end_date: str | None, count: int, generated_at: str) -> list[Date]:
    if count < 1:
        return []
    if start_date:
        start = _parse_date(start_date)
        return [start + timedelta(days=offset) for offset in range(count)]
    end = _parse_date(end_date) if end_date else _parse_date(str(generated_at)[:10])
    start = end - timedelta(days=count - 1)
    return [start + timedelta(days=offset) for offset in range(count)]


def _parse_date(value: str) -> Date:
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _source_item_preprint_date(item: Mapping[str, Any]) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
    preprint = metadata.get("preprint") if isinstance(metadata.get("preprint"), Mapping) else {}
    raw = str(preprint.get("date") or "").strip()
    return raw[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", raw) else ""


def _duplicate_values(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        elif value:
            seen.add(value)
    return sorted(duplicates)


def _shadow_hours_from_dates(dates: Sequence[str]) -> float:
    parsed = sorted(_parse_date(item[:10]) for item in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", item[:10]))
    if len(parsed) < 2:
        return 0.0
    return float(((parsed[-1] - parsed[0]).days + 1) * 24)


def _is_preprint_source_id(source_id: str) -> bool:
    return source_id.startswith(("biorxiv:", "medrxiv:"))


def _preprint_scan(source_batches: Mapping[str, Mapping[str, Any]], *, generated_at: str) -> dict[str, Any]:
    source_reports: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_candidate_ids: set[str] = set()
    for server in S2P1_REQUIRED_SERVERS:
        batch = source_batches.get(server)
        if not isinstance(batch, Mapping):
            reason = f"{server}: missing preprint source batch"
            source_reports.append({"server": server, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        batch_errors = validate_preprint_source_batch(batch)
        source_reports.append(
            {
                "server": server,
                "status": "blocked" if batch_errors or batch.get("status") == "blocked" else "pass",
                "source_item_count": len(batch.get("source_items") or []),
                "new_item_count": int(batch.get("new_item_count") or 0),
                "blocking_reasons": batch_errors or list(batch.get("blocking_reasons") or []),
            }
        )
        if batch_errors or batch.get("status") == "blocked":
            errors.extend(f"{server}: {reason}" for reason in (batch_errors or batch.get("blocking_reasons") or []))
            continue
        for source_item in batch.get("new_items") or []:
            if not isinstance(source_item, Mapping):
                continue
            candidate, candidate_errors = candidate_from_source_item(source_item, generated_at=generated_at)
            errors.extend(candidate_errors)
            if not candidate:
                continue
            if candidate["source_id"] in seen_candidate_ids:
                continue
            seen_candidate_ids.add(candidate["source_id"])
            candidates.append(candidate)
    blocking_reasons = errors if errors else [] if candidates else ["no eligible new bioRxiv/medRxiv candidates for shadow daily input"]
    return {
        "scan_id": "s2p1-preprint-scan:shadow",
        "model_id": S2P1_PREPRINT_SHADOW_MODEL_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons else "blocked",
        "source_count": len(source_reports),
        "candidate_count": len(candidates),
        "source_reports": source_reports,
        "candidates": candidates,
        "blocking_reasons": blocking_reasons,
    }


def _top_journal_scan(
    source_batches: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
    required_journals: Sequence[str] = S2P2_REQUIRED_JOURNALS,
    model_id: str = S2P2_TOP_JOURNAL_SHADOW_MODEL_ID,
    scan_id: str = "s2p2-top-journal-scan:shadow",
    no_candidate_message: str = "no eligible new Nature main-journal candidates for shadow daily input",
) -> dict[str, Any]:
    source_reports: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_candidate_ids: set[str] = set()
    for journal in required_journals:
        batch = source_batches.get(journal)
        if not isinstance(batch, Mapping):
            reason = f"{journal}: missing top-journal source batch"
            source_reports.append({"journal": journal, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        batch_errors = validate_top_journal_source_batch(batch)
        source_reports.append(
            {
                "journal": journal,
                "status": "blocked" if batch_errors or batch.get("status") == "blocked" else "pass",
                "source_item_count": len(batch.get("source_items") or []),
                "new_item_count": int(batch.get("new_item_count") or 0),
                "blocking_reasons": batch_errors or list(batch.get("blocking_reasons") or []),
            }
        )
        if batch_errors or batch.get("status") == "blocked":
            errors.extend(f"{journal}: {reason}" for reason in (batch_errors or batch.get("blocking_reasons") or []))
            continue
        for source_item in batch.get("new_items") or []:
            if not isinstance(source_item, Mapping):
                continue
            candidate, candidate_errors = candidate_from_source_item(source_item, generated_at=generated_at)
            errors.extend(candidate_errors)
            if not candidate:
                continue
            if candidate["source_id"] in seen_candidate_ids:
                continue
            seen_candidate_ids.add(candidate["source_id"])
            candidates.append(candidate)
    blocking_reasons = errors if errors else [] if candidates else [no_candidate_message]
    return {
        "scan_id": scan_id,
        "model_id": model_id,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons else "blocked",
        "source_count": len(source_reports),
        "candidate_count": len(candidates),
        "source_reports": source_reports,
        "candidates": candidates,
        "blocking_reasons": blocking_reasons,
    }


def _daily_input_from_selection(
    selected: Mapping[str, Any],
    *,
    date: str,
    generated_at: str,
    queue: Mapping[str, Any],
    run_label: str = "s2p1-preprint",
    scan_scope: str = "s2p1_biorxiv_medrxiv_shadow",
    source_count: int = len(S2P1_REQUIRED_SERVERS),
    task_id: str = S2P1_TASK_ID,
) -> dict[str, Any]:
    source_item = dict(selected["source_item"])
    stable_id = _safe_id(str(source_item.get("stable_id") or selected.get("source_id") or "unknown"))
    queue_items = queue.get("items") if isinstance(queue.get("items"), list) else []
    return {
        "run_id": f"daily:{date}:{run_label}:{stable_id}",
        "publication_id": f"pub:daily:{date}:{run_label}:{stable_id}",
        "date": date,
        "generated_at": generated_at,
        "timezone": DEFAULT_TIMEZONE,
        "source_item": source_item,
        "claims": [dict(claim) for claim in selected["evidence_claims"]],
        "selection_audit": {
            "model_id": ROI_RANKING_MODEL_ID,
            "selection_source": selected.get("selection_source", ""),
            "roi_total_score": selected["roi_total_score"],
            "roi_signals": dict(selected["roi_signals"]),
        },
        "scan_summary": {
            "scope": scan_scope,
            "source_count": int(source_count),
        },
        "queue_summary": {
            "queue_model_id": CANDIDATE_QUEUE_MODEL_ID,
            "queued_item_count": len(queue_items),
            "top_queued": [
                {
                    "source_id": item.get("source_id", ""),
                    "title": item.get("title", ""),
                    "roi_total_score": item.get("roi_total_score", 0.0),
                    "primary_category": item.get("primary_category", ""),
                }
                for item in queue_items[:5]
            ],
        },
        "stage2_shadow": {
            "task_id": task_id,
            "formal_production_inclusion": False,
            "real_smtp_allowed": False,
        },
    }


def _blocked_daily_input(
    date: str,
    generated_at: str,
    queue: Mapping[str, Any],
    scan: Mapping[str, Any],
    reasons: Sequence[str],
    *,
    selection: Mapping[str, Any] | None = None,
    model_id: str = S2P1_PREPRINT_SHADOW_MODEL_ID,
    task_id: str = S2P1_TASK_ID,
) -> dict[str, Any]:
    return {
        "model_id": model_id,
        "task_id": task_id,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": "blocked",
        "daily_input_ready": False,
        "formal_production_inclusion": False,
        "shadow_mode": True,
        "scan": scan,
        "candidate_queue": queue,
        "selection": dict(selection or {"model_id": ROI_RANKING_MODEL_ID, "status": "blocked", "selected": None}),
        "daily_input": {},
        "blocking_reasons": list(reasons),
    }


def _base_shadow_report(
    *,
    status: str,
    date: str,
    generated_at: str,
    state: Path,
    run_dir: Path,
    blocking_reasons: list[str],
    daily_report: Mapping[str, Any],
    model_id: str = S2P1_PREPRINT_SHADOW_MODEL_ID,
    acceptance_id: str = S2P1_ACCEPTANCE_ID,
    task_id: str = S2P1_TASK_ID,
) -> dict[str, Any]:
    return {
        "model_id": model_id,
        "acceptance_id": acceptance_id,
        "task_id": task_id,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "date": date,
        "timezone": DEFAULT_TIMEZONE,
        "status": status,
        "state_dir": str(state),
        "run_dir": str(run_dir),
        "daily_input_ready": bool(daily_report.get("daily_input_ready") is True),
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "real_smtp_sent": False,
        "production_affected": False,
        "video_required": False,
        "daily_report": daily_report,
        "blocking_reasons": blocking_reasons,
    }


def _write_or_return(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_s2p1_shadow_report(normalized)
    if write:
        _write_json(run_dir / "adp-s2p1-preprint-shadow-report.json", normalized)
    return normalized


def _write_or_return_s2p2(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_s2p2_top_journal_shadow_report(normalized)
    if write:
        _write_json(run_dir / "adp-s2p2-top-journal-shadow-report.json", normalized)
    return normalized


def _write_or_return_s2pct02(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized.setdefault("d2_source_domain_accepted", False)
    normalized.setdefault("stage2_production_accepted", False)
    normalized.setdefault("integrated_production_accepted", False)
    normalized["validation_errors"] = validate_s2pct02_science_shadow_report(normalized)
    if write:
        _write_json(run_dir / "adp-s2pct02-science-shadow-report.json", normalized)
    return normalized


def _write_or_return_s2pct03(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    normalized.setdefault("d2_source_domain_accepted", False)
    normalized.setdefault("stage2_production_accepted", False)
    normalized.setdefault("integrated_production_accepted", False)
    normalized["validation_errors"] = validate_s2pct03_lancet_shadow_report(normalized)
    if write:
        _write_json(run_dir / "adp-s2pct03-lancet-shadow-report.json", normalized)
    return normalized


def _write_or_return_s2pct04(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
    ):
        normalized.setdefault(key, False)
    normalized["validation_errors"] = validate_s2pct04_top_journal_profile_report(normalized)
    if write:
        report_path = Path(str(normalized.get("profile_report_path") or run_dir / "adp-s2pct04-top-journal-profile-report.json"))
        _write_json(report_path, normalized)
    return normalized


def _write_or_return_s2pct05(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
    ):
        normalized.setdefault(key, False)
    normalized["validation_errors"] = validate_s2pct05_engineering_signal_report(normalized)
    if write:
        report_path = Path(str(normalized.get("engineering_signal_report_path") or run_dir / "adp-s2pct05-engineering-signal-report.json"))
        _write_json(report_path, normalized)
    return normalized


def _write_or_return_s2pct06(report: dict[str, Any], run_dir: Path, *, write: bool) -> dict[str, Any]:
    normalized = dict(report)
    for key in (
        "formal_production_inclusion",
        "d2_source_domain_accepted",
        "stage2_production_accepted",
        "integrated_production_accepted",
        "github_cloud_schedule_enabled",
        "real_smtp_sent",
        "real_release_uploaded",
        "production_affected",
        "pdf_download_enabled",
        "full_text_download_enabled",
        "paid_api_used",
        "paywall_bypass_allowed",
        "marketing_material_accepted",
    ):
        normalized.setdefault(key, False)
    normalized["validation_errors"] = validate_s2pct06_authoritative_report_source_report(normalized)
    if write:
        report_path = Path(str(normalized.get("authoritative_report_path") or run_dir / "adp-s2pct06-authoritative-report-source-report.json"))
        _write_json(report_path, normalized)
    return normalized


def _s2pct05_known_documents(profile_report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    documents: dict[str, Mapping[str, Any]] = {}
    for profile in profile_report.get("source_profiles") or []:
        if not isinstance(profile, Mapping):
            continue
        canonical_id = str(profile.get("canonical_document_id") or "")
        if canonical_id:
            documents[canonical_id] = profile
    return documents


def _s2pct05_normalize_engineering_signals(
    engineering_signals: Sequence[Mapping[str, Any]],
    *,
    known_documents: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    normalized: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, signal in enumerate(engineering_signals):
        if not isinstance(signal, Mapping):
            reason = f"engineering_signals[{index}] must be an object"
            reports.append({"index": index, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        item = _s2pct05_normalize_signal(signal, generated_at=generated_at)
        item_errors = _s2pct05_signal_errors(item, known_documents=known_documents)
        reports.append(
            {
                "signal_id": item.get("signal_id", ""),
                "signal_type": item.get("signal_type", ""),
                "status": "blocked" if item_errors else "pass",
                "blocking_reasons": item_errors,
            }
        )
        errors.extend(item_errors)
        if not item_errors:
            normalized.append(item)
    return normalized, reports, errors


def _s2pct05_normalize_signal(signal: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    signal_type = _s2pct05_signal_type(str(signal.get("signal_type") or signal.get("type") or ""))
    canonical_id = str(signal.get("canonical_document_id") or signal.get("paper_canonical_document_id") or "")
    url = _s2pct05_signal_url(signal)
    version_reference = _s2pct05_version_reference(signal)
    signal_id = str(signal.get("signal_id") or "")
    if not signal_id and signal_type and canonical_id:
        signal_id = f"eng-signal:{signal_type}:{_safe_id(canonical_id)}:{_safe_id(version_reference or url or 'unversioned')}"
    return {
        "signal_id": signal_id,
        "signal_type": signal_type,
        "title": str(signal.get("title") or signal.get("name") or ""),
        "canonical_document_id": canonical_id,
        "paper_relation_type": _profile_token(str(signal.get("paper_relation_type") or signal.get("relation_type") or "")),
        "provider": str(signal.get("provider") or signal.get("publisher") or signal.get("organization") or ""),
        "source_url": url,
        "repository_url": str(signal.get("repository_url") or ""),
        "version_reference": version_reference,
        "release_tag": str(signal.get("release_tag") or ""),
        "commit_sha": str(signal.get("commit_sha") or ""),
        "benchmark_name": str(signal.get("benchmark_name") or ""),
        "metric_name": str(signal.get("metric_name") or ""),
        "standard_id": str(signal.get("standard_id") or ""),
        "officiality_state": _profile_token(str(signal.get("officiality_state") or signal.get("officiality_verdict") or "")),
        "officiality_evidence_type": _profile_token(str(signal.get("officiality_evidence_type") or "")),
        "reproducibility_state": _profile_token(str(signal.get("reproducibility_state") or "")),
        "reproducibility_evidence": str(signal.get("reproducibility_evidence") or ""),
        "metadata_only": True,
        "production_eligible": False,
        "generated_at": generated_at,
        "evidence_refs": list(signal.get("evidence_refs") or []),
    }


def _s2pct05_signal_errors(signal: Mapping[str, Any], *, known_documents: Mapping[str, Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    signal_id = str(signal.get("signal_id") or "engineering-signal")
    signal_type = str(signal.get("signal_type") or "")
    canonical_id = str(signal.get("canonical_document_id") or "")
    if not signal.get("signal_id"):
        errors.append(f"{signal_id}: signal_id is required")
    if signal_type not in S2PCT05_REQUIRED_SIGNAL_TYPES:
        errors.append(f"{signal_id}: signal_type is not supported")
    if not canonical_id:
        errors.append(f"{signal_id}: canonical_document_id is required")
    elif canonical_id not in known_documents:
        errors.append(f"{signal_id}: canonical_document_id is unknown: {canonical_id}")
    if signal.get("paper_relation_type") not in S2PCT05_ALLOWED_RELATION_TYPES:
        errors.append(f"{signal_id}: paper_relation_type is not supported")
    if signal.get("officiality_state") not in S2PCT05_ALLOWED_OFFICIALITY_STATES:
        errors.append(f"{signal_id}: officiality_state is not accepted")
    if not signal.get("source_url"):
        errors.append(f"{signal_id}: source_url is required")
    if not signal.get("version_reference"):
        errors.append(f"{signal_id}: version_reference is required")
    if signal.get("reproducibility_state") not in S2PCT05_ALLOWED_REPRODUCIBILITY_STATES:
        errors.append(f"{signal_id}: reproducibility_state is invalid")
    if not signal.get("evidence_refs"):
        errors.append(f"{signal_id}: evidence_refs are required")
    errors.extend(_s2pct05_type_specific_errors(signal))
    return errors


def _s2pct05_type_specific_errors(signal: Mapping[str, Any]) -> list[str]:
    signal_id = str(signal.get("signal_id") or "engineering-signal")
    signal_type = str(signal.get("signal_type") or "")
    errors: list[str] = []
    if signal_type == "official_code_repository" and not signal.get("repository_url"):
        errors.append(f"{signal_id}: official_code_repository requires repository_url")
    if signal_type == "official_release" and not signal.get("release_tag"):
        errors.append(f"{signal_id}: official_release requires release_tag")
    if signal_type == "model_card" and "model" not in str(signal.get("source_url") or "").lower():
        errors.append(f"{signal_id}: model_card source_url must identify a model-card or model page")
    if signal_type == "benchmark_result" and not signal.get("benchmark_name"):
        errors.append(f"{signal_id}: benchmark_result requires benchmark_name")
    if signal_type == "standard_or_spec" and not signal.get("standard_id"):
        errors.append(f"{signal_id}: standard_or_spec requires standard_id")
    return errors


def _s2pct05_signal_type(raw: str) -> str:
    token = _profile_token(raw)
    aliases = {
        "code": "official_code_repository",
        "code_repository": "official_code_repository",
        "repository": "official_code_repository",
        "repo": "official_code_repository",
        "official_repo": "official_code_repository",
        "release": "official_release",
        "official_release": "official_release",
        "modelcard": "model_card",
        "model_card": "model_card",
        "benchmark": "benchmark_result",
        "benchmark_result": "benchmark_result",
        "standard": "standard_or_spec",
        "standards": "standard_or_spec",
        "spec": "standard_or_spec",
        "specification": "standard_or_spec",
        "standard_or_spec": "standard_or_spec",
    }
    return aliases.get(token, token)


def _s2pct05_signal_url(signal: Mapping[str, Any]) -> str:
    for key in ("source_url", "url", "repository_url", "release_url", "model_card_url", "benchmark_url", "standard_url"):
        value = str(signal.get(key) or "")
        if value:
            return value
    return ""


def _s2pct05_version_reference(signal: Mapping[str, Any]) -> str:
    for key in ("version_reference", "release_tag", "version", "model_card_version", "standard_version", "commit_sha"):
        value = str(signal.get(key) or "")
        if value:
            return value
    return ""


def _s2pct05_officiality_errors(signals: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for signal in signals:
        if signal.get("officiality_state") not in S2PCT05_ALLOWED_OFFICIALITY_STATES:
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: officiality_state is not accepted")
        if not signal.get("officiality_evidence_type"):
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: officiality_evidence_type is required")
    return errors


def _s2pct05_version_errors(signals: Sequence[Mapping[str, Any]]) -> list[str]:
    return [
        f"{signal.get('signal_id', 'engineering-signal')}: version_reference is required"
        for signal in signals
        if not signal.get("version_reference")
    ]


def _s2pct05_relation_errors(
    signals: Sequence[Mapping[str, Any]],
    known_documents: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    for signal in signals:
        canonical_id = str(signal.get("canonical_document_id") or "")
        if canonical_id not in known_documents:
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: canonical_document_id is unknown: {canonical_id}")
        if signal.get("paper_relation_type") not in S2PCT05_ALLOWED_RELATION_TYPES:
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: paper_relation_type is not supported")
    return errors


def _s2pct05_reproducibility_errors(signals: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for signal in signals:
        if signal.get("reproducibility_state") not in S2PCT05_ALLOWED_REPRODUCIBILITY_STATES:
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: reproducibility_state is invalid")
        if signal.get("signal_type") == "benchmark_result" and not signal.get("metric_name"):
            errors.append(f"{signal.get('signal_id', 'engineering-signal')}: benchmark_result requires metric_name")
    return errors


def _s2pct06_known_signals(engineering_signal_report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    signals: dict[str, Mapping[str, Any]] = {}
    for signal in engineering_signal_report.get("engineering_signals") or []:
        if not isinstance(signal, Mapping):
            continue
        signal_id = str(signal.get("signal_id") or "")
        if signal_id:
            signals[signal_id] = signal
    return signals


def _s2pct06_normalize_reports(
    technical_reports: Sequence[Mapping[str, Any]],
    *,
    known_signals: Mapping[str, Mapping[str, Any]],
    known_documents: set[str],
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    normalized: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, report in enumerate(technical_reports):
        if not isinstance(report, Mapping):
            reason = f"technical_reports[{index}] must be an object"
            source_reports.append({"index": index, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        item = _s2pct06_normalize_report(report, generated_at=generated_at)
        item_errors = _s2pct06_report_errors(item, known_signals=known_signals, known_documents=known_documents)
        source_reports.append(
            {
                "report_id": item.get("report_id", ""),
                "report_type": item.get("report_type", ""),
                "publisher": item.get("publisher", ""),
                "status": "blocked" if item_errors else "pass",
                "blocking_reasons": item_errors,
            }
        )
        errors.extend(item_errors)
        if not item_errors:
            normalized.append(item)
    return normalized, source_reports, errors


def _s2pct06_normalize_report(report: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    report_type = _s2pct06_report_type(str(report.get("report_type") or report.get("type") or ""))
    publisher_type = _s2pct06_publisher_type(str(report.get("publisher_type") or report.get("organization_type") or ""))
    canonical_id = str(report.get("canonical_document_id") or report.get("paper_canonical_document_id") or "")
    related_signal_ids = [str(value) for value in report.get("related_signal_ids") or report.get("signal_ids") or [] if str(value)]
    source_url = _s2pct06_report_url(report)
    version_reference = _s2pct06_report_version_reference(report)
    report_id = str(report.get("report_id") or "")
    if not report_id and report_type and source_url:
        report_id = f"auth-report:{report_type}:{_safe_id(source_url)}"
    return {
        "report_id": report_id,
        "report_type": report_type,
        "title": str(report.get("title") or report.get("name") or ""),
        "publisher": str(report.get("publisher") or report.get("organization") or ""),
        "publisher_type": publisher_type,
        "publisher_identity_state": _profile_token(str(report.get("publisher_identity_state") or report.get("identity_state") or "")),
        "publisher_identity_evidence": str(report.get("publisher_identity_evidence") or report.get("identity_evidence") or ""),
        "source_url": source_url,
        "landing_page_url": str(report.get("landing_page_url") or ""),
        "publication_date": str(report.get("publication_date") or report.get("date") or ""),
        "version_reference": version_reference,
        "canonical_document_id": canonical_id,
        "related_signal_ids": related_signal_ids,
        "interest_relation": _profile_token(str(report.get("interest_relation") or report.get("conflict_of_interest_state") or "")),
        "interest_disclosure": str(report.get("interest_disclosure") or report.get("conflict_of_interest_statement") or ""),
        "evidence_level": _s2pct06_evidence_level(str(report.get("evidence_level") or report.get("evidence_type") or "")),
        "product_name": str(report.get("product_name") or ""),
        "methodology_summary": str(report.get("methodology_summary") or ""),
        "metadata_only": True,
        "marketing_material_accepted": False,
        "production_eligible": False,
        "generated_at": generated_at,
        "evidence_refs": list(report.get("evidence_refs") or []),
    }


def _s2pct06_report_errors(
    report: Mapping[str, Any],
    *,
    known_signals: Mapping[str, Mapping[str, Any]],
    known_documents: set[str],
) -> list[str]:
    errors: list[str] = []
    report_id = str(report.get("report_id") or "authoritative-report")
    report_type = str(report.get("report_type") or "")
    canonical_id = str(report.get("canonical_document_id") or "")
    related_signal_ids = [str(value) for value in report.get("related_signal_ids") or []]
    if not report.get("report_id"):
        errors.append(f"{report_id}: report_id is required")
    if report_type not in S2PCT06_REQUIRED_REPORT_TYPES:
        errors.append(f"{report_id}: report_type is not supported")
    if not report.get("publisher"):
        errors.append(f"{report_id}: publisher is required")
    if report.get("publisher_type") not in S2PCT06_ALLOWED_PUBLISHER_TYPES:
        errors.append(f"{report_id}: publisher_type is not supported")
    if report.get("publisher_identity_state") not in S2PCT06_ALLOWED_IDENTITY_STATES:
        errors.append(f"{report_id}: publisher_identity_state is not accepted")
    if not report.get("publisher_identity_evidence"):
        errors.append(f"{report_id}: publisher_identity_evidence is required")
    if report.get("interest_relation") not in S2PCT06_ALLOWED_INTEREST_RELATIONS:
        errors.append(f"{report_id}: interest_relation is not accepted")
    if not report.get("interest_disclosure"):
        errors.append(f"{report_id}: interest_disclosure is required")
    if report.get("evidence_level") not in S2PCT06_ALLOWED_EVIDENCE_LEVELS:
        errors.append(f"{report_id}: evidence_level is not accepted")
    if not report.get("source_url"):
        errors.append(f"{report_id}: source_url is required")
    if not report.get("version_reference"):
        errors.append(f"{report_id}: version_reference is required")
    if not canonical_id:
        errors.append(f"{report_id}: canonical_document_id is required")
    elif canonical_id not in known_documents:
        errors.append(f"{report_id}: canonical_document_id is unknown: {canonical_id}")
    if not related_signal_ids:
        errors.append(f"{report_id}: related_signal_ids are required")
    unknown_signal_ids = [signal_id for signal_id in related_signal_ids if signal_id not in known_signals]
    if unknown_signal_ids:
        errors.append(f"{report_id}: related_signal_ids unknown: {', '.join(unknown_signal_ids)}")
    if related_signal_ids and canonical_id:
        mismatched = [
            signal_id
            for signal_id in related_signal_ids
            if str(known_signals.get(signal_id, {}).get("canonical_document_id") or "") != canonical_id
        ]
        if mismatched:
            errors.append(f"{report_id}: related_signal_ids do not trace to canonical_document_id: {', '.join(mismatched)}")
    if not report.get("evidence_refs"):
        errors.append(f"{report_id}: evidence_refs are required")
    errors.extend(_s2pct06_type_specific_errors(report))
    return errors


def _s2pct06_type_specific_errors(report: Mapping[str, Any]) -> list[str]:
    report_id = str(report.get("report_id") or "authoritative-report")
    report_type = str(report.get("report_type") or "")
    errors: list[str] = []
    if report_type == "product_technical_note" and not report.get("product_name"):
        errors.append(f"{report_id}: product_technical_note requires product_name")
    if report_type in {"research_institution_report", "lab_technical_report"} and report.get("publisher_type") == "company_product_org":
        errors.append(f"{report_id}: research/lab reports cannot use company_product_org publisher_type")
    if report_type == "industry_technical_report" and report.get("interest_relation") == "independent_research":
        errors.append(f"{report_id}: industry_technical_report requires disclosed industry interest relation")
    if report_type in {"research_institution_report", "lab_technical_report", "industry_technical_report"} and not report.get("methodology_summary"):
        errors.append(f"{report_id}: methodology_summary is required")
    return errors


def _s2pct06_report_type(raw: str) -> str:
    token = _profile_token(raw)
    aliases = {
        "research_report": "research_institution_report",
        "research_institution_report": "research_institution_report",
        "institution_report": "research_institution_report",
        "lab_report": "lab_technical_report",
        "laboratory_report": "lab_technical_report",
        "lab_technical_report": "lab_technical_report",
        "industry_report": "industry_technical_report",
        "industry_technical_report": "industry_technical_report",
        "technical_report": "industry_technical_report",
        "product_note": "product_technical_note",
        "product_technical_note": "product_technical_note",
        "technical_note": "product_technical_note",
    }
    return aliases.get(token, token)


def _s2pct06_publisher_type(raw: str) -> str:
    token = _profile_token(raw)
    aliases = {
        "institute": "research_institution",
        "research_institute": "research_institution",
        "research_institution": "research_institution",
        "public_lab": "public_lab",
        "government_lab": "public_lab",
        "national_lab": "public_lab",
        "industry_lab": "industry_research_lab",
        "industry_research_lab": "industry_research_lab",
        "corporate_research": "industry_research_lab",
        "company": "company_product_org",
        "company_product_org": "company_product_org",
        "vendor": "company_product_org",
    }
    return aliases.get(token, token)


def _s2pct06_evidence_level(raw: str) -> str:
    token = _profile_token(raw)
    aliases = {
        "primary_report": "primary_research_report",
        "primary_research_report": "primary_research_report",
        "research_report": "primary_research_report",
        "whitepaper": "technical_whitepaper",
        "technical_whitepaper": "technical_whitepaper",
        "methodology": "methodology_note",
        "methodology_note": "methodology_note",
        "product_note": "product_technical_note",
        "product_technical_note": "product_technical_note",
    }
    return aliases.get(token, token)


def _s2pct06_report_url(report: Mapping[str, Any]) -> str:
    for key in ("source_url", "url", "landing_page_url", "report_url", "technical_note_url"):
        value = str(report.get(key) or "")
        if value:
            return value
    return ""


def _s2pct06_report_version_reference(report: Mapping[str, Any]) -> str:
    for key in ("version_reference", "version", "publication_date", "date", "report_number", "revision"):
        value = str(report.get(key) or "")
        if value:
            return value
    return ""


def _s2pct06_publisher_identity_errors(reports: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for report in reports:
        report_id = str(report.get("report_id") or "authoritative-report")
        if report.get("publisher_type") not in S2PCT06_ALLOWED_PUBLISHER_TYPES:
            errors.append(f"{report_id}: publisher_type is not supported")
        if report.get("publisher_identity_state") not in S2PCT06_ALLOWED_IDENTITY_STATES:
            errors.append(f"{report_id}: publisher_identity_state is not accepted")
        if not report.get("publisher_identity_evidence"):
            errors.append(f"{report_id}: publisher_identity_evidence is required")
    return errors


def _s2pct06_interest_relation_errors(reports: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for report in reports:
        report_id = str(report.get("report_id") or "authoritative-report")
        if report.get("interest_relation") not in S2PCT06_ALLOWED_INTEREST_RELATIONS:
            errors.append(f"{report_id}: interest_relation is not accepted")
        if not report.get("interest_disclosure"):
            errors.append(f"{report_id}: interest_disclosure is required")
    return errors


def _s2pct06_evidence_level_errors(reports: Sequence[Mapping[str, Any]]) -> list[str]:
    return [
        f"{report.get('report_id', 'authoritative-report')}: evidence_level is not accepted"
        for report in reports
        if report.get("evidence_level") not in S2PCT06_ALLOWED_EVIDENCE_LEVELS
    ]


def _s2pct06_traceability_errors(
    reports: Sequence[Mapping[str, Any]],
    known_signals: Mapping[str, Mapping[str, Any]],
    known_documents: set[str],
) -> list[str]:
    errors: list[str] = []
    for report in reports:
        report_id = str(report.get("report_id") or "authoritative-report")
        canonical_id = str(report.get("canonical_document_id") or "")
        if canonical_id not in known_documents:
            errors.append(f"{report_id}: canonical_document_id is unknown: {canonical_id}")
        related_signal_ids = [str(value) for value in report.get("related_signal_ids") or []]
        if not related_signal_ids:
            errors.append(f"{report_id}: related_signal_ids are required")
            continue
        unknown_signal_ids = [signal_id for signal_id in related_signal_ids if signal_id not in known_signals]
        if unknown_signal_ids:
            errors.append(f"{report_id}: related_signal_ids unknown: {', '.join(unknown_signal_ids)}")
    return errors


def _s2pct07_domain_matrix(
    *,
    profile_report: Mapping[str, Any],
    engineering_signal_report: Mapping[str, Any],
    authoritative_report: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    matrix = {
        "top_journal": {
            "coverage_gate": "pass" if profile_report.get("status") == "pass" else "blocked",
            "evidence_count": len(profile_report.get("source_profiles") or []),
            "type_count": len(set(profile_report.get("profile_kinds_observed") or [])),
            "required_types": list(S2PCT04_REQUIRED_PROFILE_KINDS),
            "observed_types": sorted(set(str(value) for value in profile_report.get("profile_kinds_observed") or [])),
        },
        "engineering_signal": {
            "coverage_gate": "pass" if engineering_signal_report.get("status") == "pass" else "blocked",
            "evidence_count": len(engineering_signal_report.get("engineering_signals") or []),
            "type_count": len(set(engineering_signal_report.get("signal_types_observed") or [])),
            "required_types": list(S2PCT05_REQUIRED_SIGNAL_TYPES),
            "observed_types": sorted(set(str(value) for value in engineering_signal_report.get("signal_types_observed") or [])),
        },
        "authoritative_report": {
            "coverage_gate": "pass" if authoritative_report.get("status") == "pass" else "blocked",
            "evidence_count": len(authoritative_report.get("authoritative_reports") or []),
            "type_count": len(set(authoritative_report.get("report_types_observed") or [])),
            "required_types": list(S2PCT06_REQUIRED_REPORT_TYPES),
            "observed_types": sorted(set(str(value) for value in authoritative_report.get("report_types_observed") or [])),
        },
    }
    errors: list[str] = []
    for domain in S2PCT07_REQUIRED_DOMAINS:
        row = matrix[domain]
        missing = sorted(set(row["required_types"]) - set(row["observed_types"]))
        row["missing_types"] = missing
        if row["coverage_gate"] != "pass":
            errors.append(f"{domain}: upstream coverage gate is blocked")
        if int(row["evidence_count"] or 0) < 1:
            errors.append(f"{domain}: evidence_count must be positive")
        if missing:
            errors.append(f"{domain}: missing required types: {', '.join(missing)}")
    return matrix, errors


def _s2pct07_replay_gate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = {str(record.get("as_of_date") or record.get("date") or "")[:10] for record in records if isinstance(record, Mapping)}
    passing = [record for record in records if isinstance(record, Mapping) and record.get("status") == "pass"]
    future_leakage = [record for record in records if isinstance(record, Mapping) and int(record.get("future_leakage_count") or 0) > 0]
    p0_p1 = [record for record in records if isinstance(record, Mapping) and int(record.get("p0_p1_blocker_count") or 0) > 0]
    domains = {str(record.get("domain") or "") for record in records if isinstance(record, Mapping)}
    reasons: list[str] = []
    if len(dates) < S2PCT07_REQUIRED_REPLAY_DATES:
        reasons.append("S2PCT07 D2 replay requires 30 unique dates")
    if len(passing) < len(records) or not records:
        reasons.append("S2PCT07 D2 replay records must all pass")
    missing_domains = sorted(set(S2PCT07_REQUIRED_DOMAINS) - domains)
    if missing_domains:
        reasons.append("S2PCT07 D2 replay missing domains: " + ", ".join(missing_domains))
    if future_leakage:
        reasons.append("S2PCT07 D2 replay has future leakage")
    if p0_p1:
        reasons.append("S2PCT07 D2 replay has P0/P1 blockers")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_unique_dates": S2PCT07_REQUIRED_REPLAY_DATES,
        "unique_date_count": len(dates),
        "record_count": len(records),
        "passing_record_count": len(passing),
        "domains_observed": sorted(domain for domain in domains if domain),
        "future_leakage_count": len(future_leakage),
        "p0_p1_blocker_count": len(p0_p1),
        "blocking_reasons": reasons,
    }


def _s2pct07_shadow_gate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    hours = max([float(record.get("shadow_hours") or 0.0) for record in records if isinstance(record, Mapping)] or [0.0])
    passing = [record for record in records if isinstance(record, Mapping) and record.get("status") == "pass"]
    production_affected = [record for record in records if isinstance(record, Mapping) and record.get("production_affected") is not False]
    smtp_sent = [record for record in records if isinstance(record, Mapping) and record.get("real_smtp_sent") is not False]
    reasons: list[str] = []
    if hours < S2PCT07_REQUIRED_SHADOW_HOURS:
        reasons.append("S2PCT07 D2 shadow requires at least 48 hours")
    if len(passing) < len(records) or not records:
        reasons.append("S2PCT07 D2 shadow records must all pass")
    if production_affected:
        reasons.append("S2PCT07 D2 shadow must not affect production")
    if smtp_sent:
        reasons.append("S2PCT07 D2 shadow must not send SMTP")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_shadow_hours": S2PCT07_REQUIRED_SHADOW_HOURS,
        "shadow_hours": hours,
        "record_count": len(records),
        "passing_record_count": len(passing),
        "production_affected_count": len(production_affected),
        "real_smtp_sent_count": len(smtp_sent),
        "blocking_reasons": reasons,
    }


def _s2pct07_forced_event_gate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    event_types = {str(record.get("event_type") or "") for record in records if isinstance(record, Mapping)}
    passing = [record for record in records if isinstance(record, Mapping) and record.get("status") == "pass"]
    no_updates = [
        record
        for record in records
        if isinstance(record, Mapping)
        and not (record.get("forced_review_required") is True and str(record.get("updated_conclusion_state") or ""))
    ]
    reasons: list[str] = []
    missing = sorted(set(S2PCT07_REQUIRED_FORCED_EVENT_TYPES) - event_types)
    if missing:
        reasons.append("S2PCT07 forced-event calibration missing event types: " + ", ".join(missing))
    if len(passing) < len(records) or not records:
        reasons.append("S2PCT07 forced-event records must all pass")
    if no_updates:
        reasons.append("S2PCT07 forced-event records must force review and update conclusion state")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_event_types": list(S2PCT07_REQUIRED_FORCED_EVENT_TYPES),
        "event_types_observed": sorted(event_type for event_type in event_types if event_type),
        "record_count": len(records),
        "passing_record_count": len(passing),
        "forced_update_count": len(records) - len(no_updates),
        "blocking_reasons": reasons,
    }


def _s2pct07_queue_explanation_gate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    states = {str(record.get("queue_state") or record.get("decision") or "") for record in records if isinstance(record, Mapping)}
    missing_explanation = [
        record
        for record in records
        if isinstance(record, Mapping)
        and (not str(record.get("explanation") or "") or not str(record.get("candidate_id") or record.get("source_id") or ""))
    ]
    reasons: list[str] = []
    missing_states = sorted(set(S2PCT07_REQUIRED_QUEUE_EXPLANATION_STATES) - states)
    if missing_states:
        reasons.append("S2PCT07 queue explanation missing states: " + ", ".join(missing_states))
    if missing_explanation:
        reasons.append("S2PCT07 queue explanation records require candidate_id/source_id and explanation")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_queue_states": list(S2PCT07_REQUIRED_QUEUE_EXPLANATION_STATES),
        "queue_states_observed": sorted(state for state in states if state),
        "record_count": len(records),
        "explained_record_count": len(records) - len(missing_explanation),
        "blocking_reasons": reasons,
    }


def _s2pct07_type_calibration(matrix: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    reasons: list[str] = []
    for domain in S2PCT07_REQUIRED_DOMAINS:
        row = matrix.get(domain) if isinstance(matrix.get(domain), Mapping) else {}
        required = set(row.get("required_types") or [])
        observed = set(row.get("observed_types") or [])
        coverage = (len(observed & required) / len(required)) if required else 0.0
        rows.append(
            {
                "domain": domain,
                "required_type_count": len(required),
                "observed_required_type_count": len(observed & required),
                "coverage_ratio": round(coverage, 4),
            }
        )
        if coverage < 1.0:
            reasons.append(f"{domain}: type coverage ratio must be 1.0")
    ratios = [float(row["coverage_ratio"]) for row in rows]
    spread = max(ratios) - min(ratios) if ratios else 1.0
    if spread > 0.0:
        reasons.append("S2PCT07 cross-type calibration spread must be 0 after required coverage")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_coverage_ratio": 1.0,
        "coverage_rows": rows,
        "coverage_spread": round(spread, 4),
        "blocking_reasons": reasons,
    }


def _s2pdt01_authority_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    source_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"authority_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "").strip()
        authority_type = str(record.get("authority_type") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        row = {
            "source_id": source_id,
            "authority_type": authority_type,
            "authority_name": str(record.get("authority_name") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "document_number": str(record.get("document_number") or "").strip(),
            "published_date": str(record.get("published_date") or "").strip(),
            "attachment_trace": str(record.get("attachment_trace") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not source_id:
            errors.append(f"authority_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PDT01 source_id: {source_id}")
        source_ids.add(source_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"authority_records[{index}].source_url must contain official_domain")
        rows.append(row)
    if not rows:
        errors.append("S2PDT01 requires at least one C0 authority record")
    return rows, errors


def _s2pdt01_taxonomy_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("authority_type") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT01_REQUIRED_AUTHORITY_TYPES) - observed)
    unsupported = sorted(observed - set(S2PDT01_REQUIRED_AUTHORITY_TYPES))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT01 C0 taxonomy missing authority types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT01 C0 taxonomy has unsupported authority types: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_authority_types": list(S2PDT01_REQUIRED_AUTHORITY_TYPES),
        "authority_types_observed": sorted(authority_type for authority_type in observed if authority_type),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt01_identity_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PDT01_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PDT01 C0 identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PDT01_ALLOWED_IDENTITY_STATES),
        "verified_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt01_traceability_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_rows = []
    for row in rows:
        if not isinstance(row, Mapping):
            missing_rows.append(row)
            continue
        if any(not row.get(field) for field in S2PDT01_REQUIRED_TRACE_FIELDS) or not row.get("attachment_trace") or not row.get("evidence_refs"):
            missing_rows.append(row)
    reasons: list[str] = []
    if missing_rows:
        reasons.append("S2PDT01 C0 traceability requires authority_name, official_domain, document_number, published_date, attachment_trace, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_trace_fields": list(S2PDT01_REQUIRED_TRACE_FIELDS),
        "traceable_record_count": len(rows) - len(missing_rows),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt01_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PDT01 C0 records must be metadata-only with pdf_downloaded=false and full_text_extracted=false")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(rows) - len(violations),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_department_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    source_ids: set[str] = set()
    department_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"department_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "").strip()
        department_id = str(record.get("department_id") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        aliases = [str(alias).strip() for alias in record.get("aliases") or [] if str(alias).strip()]
        industry_routes = [str(route).strip() for route in record.get("industry_routes") or [] if str(route).strip()]
        board_routes = [str(route).strip() for route in record.get("board_routes") or [] if str(route).strip()]
        row = {
            "source_id": source_id,
            "department_id": department_id,
            "department_name": str(record.get("department_name") or "").strip(),
            "sector": str(record.get("sector") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "aliases": aliases,
            "industry_routes": industry_routes,
            "board_routes": board_routes,
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not source_id:
            errors.append(f"department_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PDT02 source_id: {source_id}")
        source_ids.add(source_id)
        if not department_id:
            errors.append(f"department_records[{index}].department_id is required")
        if department_id in department_ids:
            errors.append(f"duplicate S2PDT02 department_id: {department_id}")
        department_ids.add(department_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"department_records[{index}].source_url must contain official_domain")
        rows.append(row)
    if not rows:
        errors.append("S2PDT02 requires at least one C1 department record")
    return rows, errors


def _s2pdt02_sector_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("sector") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT02_REQUIRED_SECTORS) - observed)
    unsupported = sorted(observed - set(S2PDT02_REQUIRED_SECTORS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT02 C1 sector coverage missing sectors: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT02 C1 sector coverage has unsupported sectors: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_sectors": list(S2PDT02_REQUIRED_SECTORS),
        "sectors_observed": sorted(sector for sector in observed if sector),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_identity_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PDT02_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PDT02 C1 identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PDT02_ALLOWED_IDENTITY_STATES),
        "verified_department_count": len(rows) - len(invalid),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_alias_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing = [row for row in rows if not isinstance(row, Mapping) or not row.get("aliases")]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT02 C1 alias map requires at least one alias for every department")
    return {
        "status": "pass" if not reasons else "blocked",
        "aliased_department_count": len(rows) - len(missing),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_route_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing = [row for row in rows if not isinstance(row, Mapping) or not row.get("industry_routes") or not row.get("board_routes")]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT02 C1 route map requires industry_routes and board_routes for every department")
    return {
        "status": "pass" if not reasons else "blocked",
        "routed_department_count": len(rows) - len(missing),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt02_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PDT02 C1 records must be metadata-only with pdf_downloaded=false and full_text_extracted=false")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_department_count": len(rows) - len(violations),
        "department_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt03_legal_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    legal_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"legal_records[{index}] must be an object")
            continue
        legal_id = str(record.get("legal_id") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        row = {
            "legal_id": legal_id,
            "source_id": str(record.get("source_id") or "").strip(),
            "title": str(record.get("title") or "").strip(),
            "legal_status": str(record.get("legal_status") or "").strip(),
            "version_label": str(record.get("version_label") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "published_date": str(record.get("published_date") or "").strip(),
            "effective_date": str(record.get("effective_date") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not legal_id:
            errors.append(f"legal_records[{index}].legal_id is required")
        if legal_id in legal_ids:
            errors.append(f"duplicate S2PDT03 legal_id: {legal_id}")
        legal_ids.add(legal_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"legal_records[{index}].source_url must contain official_domain")
        if not _is_iso_date(row["published_date"]):
            errors.append(f"legal_records[{index}].published_date must be YYYY-MM-DD")
        if not _is_iso_date(row["effective_date"]):
            errors.append(f"legal_records[{index}].effective_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PDT03 requires at least one legal metadata record")
    return rows, errors


def _s2pdt03_relation_rows(
    records: Sequence[Mapping[str, Any]],
    legal_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    relation_ids: set[str] = set()
    legal_ids = {str(row.get("legal_id") or "") for row in legal_rows if isinstance(row, Mapping)}
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_id = str(record.get("relation_id") or "").strip()
        source_legal_id = str(record.get("source_legal_id") or "").strip()
        target_legal_id = str(record.get("target_legal_id") or "").strip()
        row = {
            "relation_id": relation_id,
            "relation_type": str(record.get("relation_type") or "").strip(),
            "source_legal_id": source_legal_id,
            "target_legal_id": target_legal_id,
            "relation_date": str(record.get("relation_date") or "").strip(),
            "source_role": str(record.get("source_role") or "").strip(),
            "target_role": str(record.get("target_role") or "").strip(),
            "original_source_verified": record.get("original_source_verified") is True,
            "forced_update_required": record.get("forced_update_required") is True,
            "metadata_only": record.get("metadata_only") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not relation_id:
            errors.append(f"relation_records[{index}].relation_id is required")
        if relation_id in relation_ids:
            errors.append(f"duplicate S2PDT03 relation_id: {relation_id}")
        relation_ids.add(relation_id)
        if source_legal_id not in legal_ids:
            errors.append(f"relation_records[{index}].source_legal_id must reference legal_records")
        if target_legal_id not in legal_ids:
            errors.append(f"relation_records[{index}].target_legal_id must reference legal_records")
        if source_legal_id and target_legal_id and source_legal_id == target_legal_id:
            errors.append(f"relation_records[{index}] source_legal_id and target_legal_id must differ")
        if not _is_iso_date(row["relation_date"]):
            errors.append(f"relation_records[{index}].relation_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PDT03 requires at least one legal relation record")
    return rows, errors


def _s2pdt03_prior_conclusion_rows(
    records: Sequence[Mapping[str, Any]],
    legal_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    conclusion_ids: set[str] = set()
    legal_ids = {str(row.get("legal_id") or "") for row in legal_rows if isinstance(row, Mapping)}
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"prior_conclusion_records[{index}] must be an object")
            continue
        conclusion_id = str(record.get("conclusion_id") or "").strip()
        legal_id = str(record.get("legal_id") or "").strip()
        row = {
            "conclusion_id": conclusion_id,
            "legal_id": legal_id,
            "previous_state": str(record.get("previous_state") or "").strip(),
            "updated_state": str(record.get("updated_state") or "").strip(),
            "update_required": record.get("update_required") is True,
            "rescore_required": record.get("rescore_required") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not conclusion_id:
            errors.append(f"prior_conclusion_records[{index}].conclusion_id is required")
        if conclusion_id in conclusion_ids:
            errors.append(f"duplicate S2PDT03 conclusion_id: {conclusion_id}")
        conclusion_ids.add(conclusion_id)
        if legal_id not in legal_ids:
            errors.append(f"prior_conclusion_records[{index}].legal_id must reference legal_records")
        rows.append(row)
    if not rows:
        errors.append("S2PDT03 requires at least one prior conclusion update record")
    return rows, errors


def _s2pdt03_legal_status_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("legal_status") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT03_REQUIRED_LEGAL_STATUSES) - observed)
    unsupported = sorted(observed - set(S2PDT03_REQUIRED_LEGAL_STATUSES))
    invalid_identity = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PDT03_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT03 legal status coverage missing statuses: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT03 legal status coverage has unsupported statuses: " + ", ".join(unsupported))
    if invalid_identity:
        reasons.append("S2PDT03 legal identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_legal_statuses": list(S2PDT03_REQUIRED_LEGAL_STATUSES),
        "legal_statuses_observed": sorted(status for status in observed if status),
        "accepted_identity_count": len(rows) - len(invalid_identity),
        "legal_record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt03_version_effectivity_gate(
    legal_rows: Sequence[Mapping[str, Any]],
    relation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    relation_types = {str(row.get("relation_type") or "") for row in relation_rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT03_REQUIRED_RELATION_TYPES) - relation_types)
    unsupported = sorted(relation_types - set(S2PDT03_REQUIRED_RELATION_TYPES))
    date_confused = [
        row
        for row in legal_rows
        if not isinstance(row, Mapping)
        or not _is_iso_date(str(row.get("published_date") or ""))
        or not _is_iso_date(str(row.get("effective_date") or ""))
    ]
    relation_date_confused = [
        row
        for row in relation_rows
        if not isinstance(row, Mapping) or not _is_iso_date(str(row.get("relation_date") or ""))
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT03 version/effectivity relation coverage missing relation types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT03 version/effectivity relation coverage has unsupported relation types: " + ", ".join(unsupported))
    if date_confused or relation_date_confused:
        reasons.append("S2PDT03 date confusion guard requires YYYY-MM-DD published/effective/relation dates")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_relation_types": list(S2PDT03_REQUIRED_RELATION_TYPES),
        "relation_types_observed": sorted(relation_type for relation_type in relation_types if relation_type),
        "date_checked_legal_record_count": len(legal_rows) - len(date_confused),
        "date_checked_relation_record_count": len(relation_rows) - len(relation_date_confused),
        "blocking_reasons": reasons,
    }


def _s2pdt03_reprint_relation_gate(relation_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reprints = [row for row in relation_rows if isinstance(row, Mapping) and row.get("relation_type") == "reprint_of"]
    invalid = [
        row
        for row in reprints
        if row.get("source_role") != "reprint"
        or row.get("target_role") != "original"
        or row.get("original_source_verified") is not True
    ]
    reasons: list[str] = []
    if not reprints:
        reasons.append("S2PDT03 reprint relation guard requires at least one reprint_of relation")
    if invalid:
        reasons.append("S2PDT03 reprint relation guard requires source_role=reprint, target_role=original, and original_source_verified=true")
    return {
        "status": "pass" if not reasons else "blocked",
        "reprint_relation_count": len(reprints),
        "verified_reprint_relation_count": len(reprints) - len(invalid),
        "blocking_reasons": reasons,
    }


def _s2pdt03_forced_update_gate(
    relation_rows: Sequence[Mapping[str, Any]],
    prior_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    forced_relations = [
        row
        for row in relation_rows
        if isinstance(row, Mapping)
        and row.get("relation_type") in {"amends", "repeals", "implements", "interprets"}
        and row.get("forced_update_required") is True
    ]
    updatable_legal_ids = {
        str(row.get("source_legal_id") or "")
        for row in forced_relations
        if isinstance(row, Mapping) and str(row.get("source_legal_id") or "")
    }
    updatable_legal_ids.update(
        str(row.get("target_legal_id") or "")
        for row in forced_relations
        if isinstance(row, Mapping) and str(row.get("target_legal_id") or "")
    )
    valid_prior_updates = [
        row
        for row in prior_rows
        if isinstance(row, Mapping)
        and row.get("legal_id") in updatable_legal_ids
        and row.get("update_required") is True
        and row.get("rescore_required") is True
        and str(row.get("updated_state") or "")
    ]
    missing_fields = [
        row
        for row in prior_rows
        if not isinstance(row, Mapping)
        or row.get("update_required") is not True
        or row.get("rescore_required") is not True
        or not str(row.get("updated_state") or "")
    ]
    reasons: list[str] = []
    if len(forced_relations) < 4:
        reasons.append("S2PDT03 forced-update gate requires amend/repeal/implement/interpret relations with forced_update_required=true")
    if not valid_prior_updates:
        reasons.append("S2PDT03 status changes must trigger rescore and old conclusion update")
    if missing_fields:
        reasons.append("S2PDT03 prior conclusions require update_required, rescore_required, and updated_state")
    return {
        "status": "pass" if not reasons else "blocked",
        "forced_relation_count": len(forced_relations),
        "prior_update_count": len(valid_prior_updates),
        "affected_legal_ids": sorted(updatable_legal_ids),
        "blocking_reasons": reasons,
    }


def _s2pdt03_metadata_gate(
    legal_rows: Sequence[Mapping[str, Any]],
    relation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    legal_violations = [
        row
        for row in legal_rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
    ]
    relation_violations = [
        row for row in relation_rows if not isinstance(row, Mapping) or row.get("metadata_only") is not True
    ]
    evidence_missing = [
        row
        for row in [*legal_rows, *relation_rows]
        if not isinstance(row, Mapping) or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if legal_violations or relation_violations:
        reasons.append("S2PDT03 legal records and relations must stay metadata-only with no PDF/full-text extraction")
    if evidence_missing:
        reasons.append("S2PDT03 legal records and relations require evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_legal_record_count": len(legal_rows) - len(legal_violations),
        "metadata_only_relation_record_count": len(relation_rows) - len(relation_violations),
        "evidence_backed_record_count": len(legal_rows) + len(relation_rows) - len(evidence_missing),
        "blocking_reasons": reasons,
    }


def _s2pdt04_replay_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"replay_records[{index}] must be an object")
            continue
        row = {
            "as_of_date": str(record.get("as_of_date") or "").strip(),
            "source_domain": str(record.get("source_domain") or record.get("domain") or "d3_china_official").strip(),
            "status": str(record.get("status") or "").strip(),
            "future_leakage_count": int(record.get("future_leakage_count") or 0),
            "p0_p1_blocker_count": int(record.get("p0_p1_blocker_count") or 0),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "board_route_gate": str(record.get("board_route_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "formal_production_inclusion": record.get("formal_production_inclusion") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not _is_iso_date(row["as_of_date"]):
            errors.append(f"replay_records[{index}].as_of_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PDT04 requires at least one replay record")
    return rows, errors


def _s2pdt04_shadow_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"shadow_records[{index}] must be an object")
            continue
        row = {
            "shadow_date": str(record.get("shadow_date") or record.get("date") or "").strip(),
            "source_domain": str(record.get("source_domain") or record.get("domain") or "d3_china_official").strip(),
            "status": str(record.get("status") or "").strip(),
            "shadow_hours": int(record.get("shadow_hours") or 24),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "board_route_gate": str(record.get("board_route_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "formal_production_inclusion": record.get("formal_production_inclusion") is True,
            "d3_core_source_domain_accepted": record.get("d3_core_source_domain_accepted") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not _is_iso_date(row["shadow_date"]):
            errors.append(f"shadow_records[{index}].shadow_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PDT04 requires at least one shadow record")
    return rows, errors


def _s2pdt04_board_route_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    board_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"board_route_records[{index}] must be an object")
            continue
        board_id = str(record.get("board_id") or "").strip()
        row = {
            "board_id": board_id,
            "source_ids": list(record.get("source_ids") or []),
            "route_explanation": str(record.get("route_explanation") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not board_id:
            errors.append(f"board_route_records[{index}].board_id is required")
        if board_id in board_ids:
            errors.append(f"duplicate S2PDT04 board_id: {board_id}")
        board_ids.add(board_id)
        rows.append(row)
    if not rows:
        errors.append("S2PDT04 requires at least one board route record")
    return rows, errors


def _s2pdt04_replay_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = sorted({str(row.get("as_of_date") or "") for row in rows if isinstance(row, Mapping) and _is_iso_date(str(row.get("as_of_date") or ""))})
    bad_status = [row for row in rows if not isinstance(row, Mapping) or row.get("status") != "pass"]
    leakage = [row for row in rows if not isinstance(row, Mapping) or int(row.get("future_leakage_count") or 0) != 0]
    blockers = [row for row in rows if not isinstance(row, Mapping) or int(row.get("p0_p1_blocker_count") or 0) != 0]
    production = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("production_affected") is not False
        or row.get("formal_production_inclusion") is not False
    ]
    reasons: list[str] = []
    if len(dates) < S2PDT04_REQUIRED_REPLAY_DATES:
        reasons.append("S2PDT04 D3 replay requires at least 30 distinct as-of dates")
    if bad_status:
        reasons.append("S2PDT04 D3 replay records must all status=pass")
    if leakage:
        reasons.append("S2PDT04 D3 replay requires future_leakage_count=0")
    if blockers:
        reasons.append("S2PDT04 D3 replay requires p0_p1_blocker_count=0")
    if production:
        reasons.append("S2PDT04 D3 replay must not affect production or formal inclusion")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_replay_dates": S2PDT04_REQUIRED_REPLAY_DATES,
        "replay_dates_observed": dates,
        "replay_date_count": len(dates),
        "blocking_reasons": reasons,
    }


def _s2pdt04_shadow_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = sorted({str(row.get("shadow_date") or "") for row in rows if isinstance(row, Mapping) and _is_iso_date(str(row.get("shadow_date") or ""))})
    bad_status = [row for row in rows if not isinstance(row, Mapping) or row.get("status") != "pass"]
    production = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
        or row.get("formal_production_inclusion") is not False
        or row.get("d3_core_source_domain_accepted") is not False
    ]
    reasons: list[str] = []
    if len(dates) < S2PDT04_REQUIRED_SHADOW_DAYS:
        reasons.append("S2PDT04 D3 shadow requires at least 2 distinct shadow dates")
    if bad_status:
        reasons.append("S2PDT04 D3 shadow records must all status=pass")
    if production:
        reasons.append("S2PDT04 D3 shadow must not affect production, send SMTP, or accept D3 core")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_shadow_days": S2PDT04_REQUIRED_SHADOW_DAYS,
        "shadow_dates_observed": dates,
        "shadow_day_count": len(dates),
        "shadow_record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt04_authority_gate(
    replay_rows: Sequence[Mapping[str, Any]],
    shadow_rows: Sequence[Mapping[str, Any]],
    route_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    records = [*replay_rows, *shadow_rows, *route_rows]
    bad_authority = [
        row
        for row in records
        if not isinstance(row, Mapping) or row.get("authority_gate") != "pass" or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if bad_authority:
        reasons.append("S2PDT04 authority gate requires authority_gate=pass and evidence_refs on replay, shadow, and board routes")
    return {
        "status": "pass" if not reasons else "blocked",
        "authority_checked_record_count": len(records) - len(bad_authority),
        "record_count": len(records),
        "blocking_reasons": reasons,
    }


def _s2pdt04_board_routing_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("board_id") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PDT04_REQUIRED_BOARD_IDS) - observed)
    unsupported = sorted(observed - set(S2PDT04_REQUIRED_BOARD_IDS))
    incomplete = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or not row.get("source_ids")
        or not row.get("route_explanation")
        or row.get("authority_gate") != "pass"
        or row.get("metadata_only") is not True
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PDT04 board routing missing required boards: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PDT04 board routing has unsupported boards: " + ", ".join(unsupported))
    if incomplete:
        reasons.append("S2PDT04 board routes require source_ids, route_explanation, authority_gate=pass, and metadata_only=true")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_board_ids": list(S2PDT04_REQUIRED_BOARD_IDS),
        "board_ids_observed": sorted(board for board in observed if board),
        "route_record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pdt04_metadata_gate(
    replay_rows: Sequence[Mapping[str, Any]],
    shadow_rows: Sequence[Mapping[str, Any]],
    route_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    records = [*replay_rows, *shadow_rows, *route_rows]
    violations = [
        row
        for row in records
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
    ]
    evidence_missing = [row for row in records if not isinstance(row, Mapping) or not row.get("evidence_refs")]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PDT04 D3 readiness records must be metadata-only and production_affected=false")
    if evidence_missing:
        reasons.append("S2PDT04 D3 readiness records require evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(records) - len(violations),
        "evidence_backed_record_count": len(records) - len(evidence_missing),
        "record_count": len(records),
        "blocking_reasons": reasons,
    }


def _s2pet01_agency_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    source_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"agency_records[{index}] must be an object")
            continue
        source_id = str(record.get("source_id") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        row = {
            "source_id": source_id,
            "agency_id": str(record.get("agency_id") or "").strip().upper(),
            "agency_name": str(record.get("agency_name") or "").strip(),
            "signal_type": str(record.get("signal_type") or "").strip(),
            "record_title": str(record.get("record_title") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "published_date": str(record.get("published_date") or "").strip(),
            "identifier": str(record.get("identifier") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "queue_mutation_allowed": record.get("queue_mutation_allowed") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not source_id:
            errors.append(f"agency_records[{index}].source_id is required")
        if source_id in source_ids:
            errors.append(f"duplicate S2PET01 source_id: {source_id}")
        source_ids.add(source_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"agency_records[{index}].source_url must contain official_domain")
        rows.append(row)
    if not rows:
        errors.append("S2PET01 requires at least one US-TA agency record")
    return rows, errors


def _s2pet01_agency_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("agency_id") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET01_REQUIRED_AGENCIES) - observed)
    unsupported = sorted(observed - set(S2PET01_REQUIRED_AGENCIES))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET01 US-TA missing required agencies: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET01 US-TA has unsupported agencies: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_agencies": list(S2PET01_REQUIRED_AGENCIES),
        "agencies_observed": sorted(agency for agency in observed if agency),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet01_signal_type_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("signal_type") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET01_REQUIRED_SIGNAL_TYPES) - observed)
    unsupported = sorted(observed - set(S2PET01_REQUIRED_SIGNAL_TYPES))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET01 US-TA missing required signal types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET01 US-TA has unsupported signal types: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_signal_types": list(S2PET01_REQUIRED_SIGNAL_TYPES),
        "signal_types_observed": sorted(signal for signal in observed if signal),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet01_identity_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PET01_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PET01 US-TA identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PET01_ALLOWED_IDENTITY_STATES),
        "verified_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet01_traceability_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_rows = []
    for row in rows:
        if not isinstance(row, Mapping):
            missing_rows.append(row)
            continue
        if any(not row.get(field) for field in S2PET01_REQUIRED_TRACE_FIELDS) or not row.get("record_title") or not row.get("evidence_refs"):
            missing_rows.append(row)
    reasons: list[str] = []
    if missing_rows:
        reasons.append("S2PET01 US-TA traceability requires agency_id, agency_name, official_domain, source_url, published_date, record_title, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_trace_fields": list(S2PET01_REQUIRED_TRACE_FIELDS),
        "traceable_record_count": len(rows) - len(missing_rows),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet01_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
        or row.get("queue_mutation_allowed") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PET01 US-TA records must be metadata-only with no PDF/full-text, production, SMTP, or queue side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(rows) - len(violations),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet02_legal_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    document_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"legal_records[{index}] must be an object")
            continue
        document_id = str(record.get("document_id") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        row = {
            "document_id": document_id,
            "source_system": str(record.get("source_system") or "").strip(),
            "document_type": str(record.get("document_type") or "").strip(),
            "document_title": str(record.get("document_title") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "published_date": str(record.get("published_date") or "").strip(),
            "document_identifier": str(record.get("document_identifier") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "queue_mutation_allowed": record.get("queue_mutation_allowed") is True,
            "schema_migration_required": record.get("schema_migration_required") is True,
            "legal_advice_provided": record.get("legal_advice_provided") is True,
            "live_source_fetch_executed": record.get("live_source_fetch_executed") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not document_id:
            errors.append(f"legal_records[{index}].document_id is required")
        if document_id in document_ids:
            errors.append(f"duplicate S2PET02 document_id: {document_id}")
        document_ids.add(document_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"legal_records[{index}].source_url must contain official_domain")
        rows.append(row)
    if not rows:
        errors.append("S2PET02 requires at least one US-LG legal record")
    return rows, errors


def _s2pet02_relation_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    relation_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_id = str(record.get("relation_id") or "").strip()
        row = {
            "relation_id": relation_id,
            "relation_type": str(record.get("relation_type") or "").strip(),
            "source_document_id": str(record.get("source_document_id") or "").strip(),
            "target_document_id": str(record.get("target_document_id") or "").strip(),
            "relation_explanation": str(record.get("relation_explanation") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "schema_migration_required": record.get("schema_migration_required") is True,
            "legal_advice_provided": record.get("legal_advice_provided") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not relation_id:
            errors.append(f"relation_records[{index}].relation_id is required")
        if relation_id in relation_ids:
            errors.append(f"duplicate S2PET02 relation_id: {relation_id}")
        relation_ids.add(relation_id)
        rows.append(row)
    if not rows:
        errors.append("S2PET02 requires at least one legal relation record")
    return rows, errors


def _s2pet02_source_system_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("source_system") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET02_REQUIRED_SOURCE_SYSTEMS) - observed)
    unsupported = sorted(observed - set(S2PET02_REQUIRED_SOURCE_SYSTEMS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET02 US-LG missing required source systems: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET02 US-LG has unsupported source systems: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_source_systems": list(S2PET02_REQUIRED_SOURCE_SYSTEMS),
        "source_systems_observed": sorted(system for system in observed if system),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet02_document_type_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("document_type") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET02_REQUIRED_DOCUMENT_TYPES) - observed)
    unsupported = sorted(observed - set(S2PET02_REQUIRED_DOCUMENT_TYPES))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET02 US-LG missing required document types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET02 US-LG has unsupported document types: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_document_types": list(S2PET02_REQUIRED_DOCUMENT_TYPES),
        "document_types_observed": sorted(document_type for document_type in observed if document_type),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet02_legal_identity_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PET02_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PET02 US-LG identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PET02_ALLOWED_IDENTITY_STATES),
        "verified_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet02_legal_traceability_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_rows = []
    for row in rows:
        if not isinstance(row, Mapping):
            missing_rows.append(row)
            continue
        if any(not row.get(field) for field in S2PET02_REQUIRED_TRACE_FIELDS) or not row.get("document_title") or not row.get("evidence_refs"):
            missing_rows.append(row)
    reasons: list[str] = []
    if missing_rows:
        reasons.append("S2PET02 US-LG traceability requires source_system, official_domain, source_url, published_date, document_identifier, document_title, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_trace_fields": list(S2PET02_REQUIRED_TRACE_FIELDS),
        "traceable_record_count": len(rows) - len(missing_rows),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet02_relation_gate(
    legal_rows: Sequence[Mapping[str, Any]],
    relation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    document_ids = {str(row.get("document_id") or "") for row in legal_rows if isinstance(row, Mapping)}
    observed = {str(row.get("relation_type") or "") for row in relation_rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET02_REQUIRED_RELATION_TYPES) - observed)
    unsupported = sorted(observed - set(S2PET02_REQUIRED_RELATION_TYPES))
    invalid_refs = [
        row
        for row in relation_rows
        if not isinstance(row, Mapping)
        or row.get("source_document_id") not in document_ids
        or row.get("target_document_id") not in document_ids
        or not row.get("evidence_refs")
        or not row.get("relation_explanation")
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET02 US-LG missing required relation types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET02 US-LG has unsupported relation types: " + ", ".join(unsupported))
    if invalid_refs:
        reasons.append("S2PET02 US-LG relations require valid source/target document ids, explanation, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_relation_types": list(S2PET02_REQUIRED_RELATION_TYPES),
        "relation_types_observed": sorted(relation_type for relation_type in observed if relation_type),
        "verified_relation_count": len(relation_rows) - len(invalid_refs),
        "relation_count": len(relation_rows),
        "blocking_reasons": reasons,
    }


def _s2pet02_legal_metadata_gate(
    legal_rows: Sequence[Mapping[str, Any]],
    relation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    legal_violations = [
        row
        for row in legal_rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
        or row.get("queue_mutation_allowed") is not False
        or row.get("schema_migration_required") is not False
        or row.get("legal_advice_provided") is not False
        or row.get("live_source_fetch_executed") is not False
    ]
    relation_violations = [
        row
        for row in relation_rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
        or row.get("schema_migration_required") is not False
        or row.get("legal_advice_provided") is not False
    ]
    reasons: list[str] = []
    if legal_violations or relation_violations:
        reasons.append("S2PET02 US-LG records must be metadata-only with no PDF/full-text, legal-advice, live-fetch, production, SMTP, schema, or queue side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_legal_record_count": len(legal_rows) - len(legal_violations),
        "metadata_only_relation_record_count": len(relation_rows) - len(relation_violations),
        "legal_record_count": len(legal_rows),
        "relation_record_count": len(relation_rows),
        "blocking_reasons": reasons,
    }


def _s2pet03_finance_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    record_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"finance_records[{index}] must be an object")
            continue
        record_id = str(record.get("record_id") or "").strip()
        official_domain = str(record.get("official_domain") or "").strip().lower()
        source_url = str(record.get("source_url") or "").strip()
        row = {
            "record_id": record_id,
            "source_system": str(record.get("source_system") or "").strip(),
            "signal_type": str(record.get("signal_type") or "").strip(),
            "record_title": str(record.get("record_title") or "").strip(),
            "official_domain": official_domain,
            "source_url": source_url,
            "published_date": str(record.get("published_date") or "").strip(),
            "record_identifier": str(record.get("record_identifier") or "").strip(),
            "form_type": str(record.get("form_type") or "").strip(),
            "cik": str(record.get("cik") or "").strip(),
            "accession_number": str(record.get("accession_number") or "").strip(),
            "entity_id": str(record.get("entity_id") or "").strip(),
            "entity_type": str(record.get("entity_type") or "").strip(),
            "related_entity_ids": [str(item) for item in record.get("related_entity_ids") or [] if item],
            "asset_class": str(record.get("asset_class") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "queue_mutation_allowed": record.get("queue_mutation_allowed") is True,
            "schema_migration_required": record.get("schema_migration_required") is True,
            "investment_advice_provided": record.get("investment_advice_provided") is True,
            "trading_signal_generated": record.get("trading_signal_generated") is True,
            "automated_trading_enabled": record.get("automated_trading_enabled") is True,
            "paid_market_data_used": record.get("paid_market_data_used") is True,
            "live_source_fetch_executed": record.get("live_source_fetch_executed") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not record_id:
            errors.append(f"finance_records[{index}].record_id is required")
        if record_id in record_ids:
            errors.append(f"duplicate S2PET03 record_id: {record_id}")
        record_ids.add(record_id)
        if official_domain and source_url and official_domain not in source_url.lower():
            errors.append(f"finance_records[{index}].source_url must contain official_domain")
        rows.append(row)
    if not rows:
        errors.append("S2PET03 requires at least one US-FM finance record")
    return rows, errors


def _s2pet03_finance_relation_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    relation_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_id = str(record.get("relation_id") or "").strip()
        row = {
            "relation_id": relation_id,
            "relation_type": str(record.get("relation_type") or "").strip(),
            "source_record_id": str(record.get("source_record_id") or "").strip(),
            "target_entity_id": str(record.get("target_entity_id") or "").strip(),
            "relation_explanation": str(record.get("relation_explanation") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "schema_migration_required": record.get("schema_migration_required") is True,
            "trading_signal_generated": record.get("trading_signal_generated") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not relation_id:
            errors.append(f"relation_records[{index}].relation_id is required")
        if relation_id in relation_ids:
            errors.append(f"duplicate S2PET03 relation_id: {relation_id}")
        relation_ids.add(relation_id)
        rows.append(row)
    if not rows:
        errors.append("S2PET03 requires at least one finance relation record")
    return rows, errors


def _s2pet03_source_system_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("source_system") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET03_REQUIRED_SOURCE_SYSTEMS) - observed)
    unsupported = sorted(observed - set(S2PET03_REQUIRED_SOURCE_SYSTEMS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET03 US-FM missing required source systems: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET03 US-FM has unsupported source systems: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_source_systems": list(S2PET03_REQUIRED_SOURCE_SYSTEMS),
        "source_systems_observed": sorted(system for system in observed if system),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet03_signal_type_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("signal_type") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET03_REQUIRED_SIGNAL_TYPES) - observed)
    unsupported = sorted(observed - set(S2PET03_REQUIRED_SIGNAL_TYPES))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET03 US-FM missing required signal types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET03 US-FM has unsupported signal types: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_signal_types": list(S2PET03_REQUIRED_SIGNAL_TYPES),
        "signal_types_observed": sorted(signal for signal in observed if signal),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet03_sec_form_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {
        str(row.get("form_type") or "")
        for row in rows
        if isinstance(row, Mapping) and row.get("source_system") == "sec_edgar"
    }
    missing = sorted(set(S2PET03_REQUIRED_SEC_FORM_TYPES) - observed)
    unsupported = sorted(observed - set(S2PET03_REQUIRED_SEC_FORM_TYPES))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET03 US-FM missing required SEC form types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET03 US-FM has unsupported SEC form types: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_sec_form_types": list(S2PET03_REQUIRED_SEC_FORM_TYPES),
        "sec_form_types_observed": sorted(form_type for form_type in observed if form_type),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet03_identifier_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    sec_rows = [row for row in rows if isinstance(row, Mapping) and row.get("source_system") == "sec_edgar"]
    invalid = [
        row
        for row in sec_rows
        if any(not row.get(field) for field in S2PET03_REQUIRED_IDENTIFIER_FIELDS)
        or not row.get("record_identifier")
        or not row.get("entity_id")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PET03 US-FM SEC rows require CIK, Accession, record identifier, and entity_id")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_identifier_fields": list(S2PET03_REQUIRED_IDENTIFIER_FIELDS),
        "verified_sec_identifier_count": len(sec_rows) - len(invalid),
        "sec_record_count": len(sec_rows),
        "blocking_reasons": reasons,
    }


def _s2pet03_official_identity_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("identity_state") not in S2PET03_ALLOWED_IDENTITY_STATES
        or not str(row.get("official_domain") or "")
        or not str(row.get("source_url") or "")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PET03 US-FM identity requires accepted identity_state, official_domain, and source_url")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PET03_ALLOWED_IDENTITY_STATES),
        "verified_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet03_traceability_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_rows = []
    for row in rows:
        if not isinstance(row, Mapping):
            missing_rows.append(row)
            continue
        if any(not row.get(field) for field in S2PET03_REQUIRED_TRACE_FIELDS) or not row.get("record_title") or not row.get("evidence_refs"):
            missing_rows.append(row)
    reasons: list[str] = []
    if missing_rows:
        reasons.append("S2PET03 US-FM traceability requires source_system, official_domain, source_url, published_date, record_identifier, record_title, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_trace_fields": list(S2PET03_REQUIRED_TRACE_FIELDS),
        "traceable_record_count": len(rows) - len(missing_rows),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pet03_relation_gate(
    finance_rows: Sequence[Mapping[str, Any]],
    relation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    record_ids = {str(row.get("record_id") or "") for row in finance_rows if isinstance(row, Mapping)}
    entity_ids: set[str] = set()
    for row in finance_rows:
        if not isinstance(row, Mapping):
            continue
        if row.get("entity_id"):
            entity_ids.add(str(row.get("entity_id")))
        for related in row.get("related_entity_ids") or []:
            if related:
                entity_ids.add(str(related))
    observed = {str(row.get("relation_type") or "") for row in relation_rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET03_REQUIRED_RELATION_TYPES) - observed)
    unsupported = sorted(observed - set(S2PET03_REQUIRED_RELATION_TYPES))
    invalid_refs = [
        row
        for row in relation_rows
        if not isinstance(row, Mapping)
        or row.get("source_record_id") not in record_ids
        or row.get("target_entity_id") not in entity_ids
        or not row.get("evidence_refs")
        or not row.get("relation_explanation")
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET03 US-FM missing required relation types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET03 US-FM has unsupported relation types: " + ", ".join(unsupported))
    if invalid_refs:
        reasons.append("S2PET03 US-FM relations require valid source record ids, target entities, explanation, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_relation_types": list(S2PET03_REQUIRED_RELATION_TYPES),
        "relation_types_observed": sorted(relation_type for relation_type in observed if relation_type),
        "verified_relation_count": len(relation_rows) - len(invalid_refs),
        "relation_count": len(relation_rows),
        "blocking_reasons": reasons,
    }


def _s2pet03_metadata_gate(
    finance_rows: Sequence[Mapping[str, Any]],
    relation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    finance_violations = [
        row
        for row in finance_rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
        or row.get("queue_mutation_allowed") is not False
        or row.get("schema_migration_required") is not False
        or row.get("investment_advice_provided") is not False
        or row.get("trading_signal_generated") is not False
        or row.get("automated_trading_enabled") is not False
        or row.get("paid_market_data_used") is not False
        or row.get("live_source_fetch_executed") is not False
    ]
    relation_violations = [
        row
        for row in relation_rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
        or row.get("schema_migration_required") is not False
        or row.get("trading_signal_generated") is not False
    ]
    reasons: list[str] = []
    if finance_violations or relation_violations:
        reasons.append("S2PET03 US-FM records must be metadata-only with no PDF/full-text, investment-advice, trading, paid-market-data, live-fetch, production, SMTP, schema, or queue side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_finance_record_count": len(finance_rows) - len(finance_violations),
        "metadata_only_relation_record_count": len(relation_rows) - len(relation_violations),
        "finance_record_count": len(finance_rows),
        "relation_record_count": len(relation_rows),
        "blocking_reasons": reasons,
    }


def _s2pet04_policy_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    record_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"policy_records[{index}] must be an object")
            continue
        record_id = str(record.get("record_id") or "").strip()
        official_domain = str(record.get("official_domain") or "").lower().strip()
        source_url = str(record.get("source_url") or "").lower().strip()
        row = {
            "record_id": record_id,
            "source_system": str(record.get("source_system") or "").strip(),
            "signal_type": str(record.get("signal_type") or "").strip(),
            "record_title": str(record.get("record_title") or "").strip(),
            "official_domain": official_domain,
            "source_url": str(record.get("source_url") or "").strip(),
            "published_date": str(record.get("published_date") or "").strip(),
            "record_identifier": str(record.get("record_identifier") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "d4_component": str(record.get("d4_component") or "").strip(),
            "board_ids": list(record.get("board_ids") or []),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "public_schema_changed": record.get("public_schema_changed") is True,
            "live_source_fetch_executed": record.get("live_source_fetch_executed") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not record_id:
            errors.append(f"policy_records[{index}].record_id is required")
        if record_id in record_ids:
            errors.append(f"duplicate S2PET04 policy record_id: {record_id}")
        record_ids.add(record_id)
        if official_domain and source_url and official_domain not in source_url:
            errors.append(f"policy_records[{index}].source_url must contain official_domain")
        rows.append(row)
    if not rows:
        errors.append("S2PET04 requires at least one US-TP policy record")
    return rows, errors


def _s2pet04_replay_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"replay_records[{index}] must be an object")
            continue
        row = {
            "as_of_date": str(record.get("as_of_date") or "").strip(),
            "d4_components": list(record.get("d4_components") or []),
            "status": str(record.get("status") or "").strip(),
            "route_gate": str(record.get("route_gate") or "").strip(),
            "budget_gate": str(record.get("budget_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "candidate_count": int(record.get("candidate_count") or 0),
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not _is_iso_date(row["as_of_date"]):
            errors.append(f"replay_records[{index}].as_of_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PET04 requires replay records")
    return rows, errors


def _s2pet04_shadow_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"shadow_records[{index}] must be an object")
            continue
        row = {
            "shadow_date": str(record.get("shadow_date") or "").strip(),
            "status": str(record.get("status") or "").strip(),
            "candidate_count": int(record.get("candidate_count") or 0),
            "email_preview_gate": str(record.get("email_preview_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "production_affected": record.get("production_affected") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not _is_iso_date(row["shadow_date"]):
            errors.append(f"shadow_records[{index}].shadow_date must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        errors.append("S2PET04 requires shadow records")
    return rows, errors


def _s2pet04_board_route_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"board_route_records[{index}] must be an object")
            continue
        row = {
            "board_id": str(record.get("board_id") or "").strip(),
            "source_systems": list(record.get("source_systems") or []),
            "route_explanation": str(record.get("route_explanation") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        rows.append(row)
    if not rows:
        errors.append("S2PET04 requires board route records")
    return rows, errors


def _s2pet04_budget_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"budget_records[{index}] must be an object")
            continue
        row = {
            "segment": str(record.get("segment") or "").strip(),
            "weight": int(record.get("weight") or 0),
            "budget_explanation": str(record.get("budget_explanation") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "production_affected": record.get("production_affected") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        rows.append(row)
    if not rows:
        errors.append("S2PET04 requires budget records")
    return rows, errors


def _s2pet04_source_system_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("source_system") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET04_REQUIRED_SOURCE_SYSTEMS) - observed)
    unsupported = sorted(observed - set(S2PET04_REQUIRED_SOURCE_SYSTEMS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET04 missing required source systems: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET04 has unsupported source systems: " + ", ".join(unsupported))
    return {"status": "pass" if not reasons else "blocked", "source_systems_observed": sorted(system for system in observed if system), "blocking_reasons": reasons}


def _s2pet04_signal_type_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("signal_type") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET04_REQUIRED_SIGNAL_TYPES) - observed)
    unsupported = sorted(observed - set(S2PET04_REQUIRED_SIGNAL_TYPES))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET04 missing required signal types: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET04 has unsupported signal types: " + ", ".join(unsupported))
    return {"status": "pass" if not reasons else "blocked", "signal_types_observed": sorted(signal for signal in observed if signal), "blocking_reasons": reasons}


def _s2pet04_official_identity_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("source_system") not in S2PET04_REQUIRED_SOURCE_SYSTEMS
        or row.get("signal_type") not in S2PET04_REQUIRED_SIGNAL_TYPES
        or row.get("identity_state") not in S2PET04_ALLOWED_IDENTITY_STATES
        or any(not row.get(field) for field in S2PET04_REQUIRED_POLICY_FIELDS)
        or not row.get("record_title")
        or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PET04 policy records require official source identity, trace fields, title, and evidence refs")
    return {"status": "pass" if not reasons else "blocked", "verified_record_count": len(rows) - len(invalid), "record_count": len(rows), "blocking_reasons": reasons}


def _s2pet04_replay_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = sorted({str(row.get("as_of_date") or "") for row in rows if isinstance(row, Mapping) and _is_iso_date(str(row.get("as_of_date") or ""))})
    components = sorted({str(component) for row in rows if isinstance(row, Mapping) for component in (row.get("d4_components") or [])})
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("status") != "pass"
        or row.get("route_gate") != "pass"
        or row.get("budget_gate") != "pass"
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
        or not row.get("evidence_refs")
    ]
    missing_components = sorted(set(S2PET04_REQUIRED_D4_COMPONENTS) - set(components))
    reasons: list[str] = []
    if len(dates) < S2PET04_REQUIRED_REPLAY_DATES:
        reasons.append("S2PET04 D4 replay requires at least 30 dates")
    if missing_components:
        reasons.append("S2PET04 D4 replay missing components: " + ", ".join(missing_components))
    if invalid:
        reasons.append("S2PET04 replay rows require pass route/budget gates, metadata-only, no production, and evidence refs")
    return {"status": "pass" if not reasons else "blocked", "replay_dates_observed": dates, "d4_components_observed": components, "blocking_reasons": reasons}


def _s2pet04_shadow_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = sorted({str(row.get("shadow_date") or "") for row in rows if isinstance(row, Mapping) and _is_iso_date(str(row.get("shadow_date") or ""))})
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("status") != "pass"
        or row.get("email_preview_gate") != "pass"
        or row.get("candidate_count", 0) <= 0
        or row.get("metadata_only") is not True
        or row.get("real_smtp_sent") is not False
        or row.get("production_affected") is not False
        or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if len(dates) < S2PET04_REQUIRED_SHADOW_DAYS:
        reasons.append("S2PET04 shadow requires at least 2 dates")
    if invalid:
        reasons.append("S2PET04 shadow rows require pass email preview gate, candidates, metadata-only, no SMTP, no production, and evidence refs")
    return {"status": "pass" if not reasons else "blocked", "shadow_dates_observed": dates, "blocking_reasons": reasons}


def _s2pet04_board_route_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("board_id") or "") for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET04_REQUIRED_BOARD_IDS) - observed)
    unsupported = sorted(observed - set(S2PET04_REQUIRED_BOARD_IDS))
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or not row.get("source_systems")
        or not row.get("route_explanation")
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
        or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET04 missing board routes: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PET04 has unsupported board routes: " + ", ".join(unsupported))
    if invalid:
        reasons.append("S2PET04 board routes require source systems, explanation, metadata-only, no production, and evidence refs")
    return {"status": "pass" if not reasons else "blocked", "board_ids_observed": sorted(board for board in observed if board), "blocking_reasons": reasons}


def _s2pet04_budget_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("segment") or "") for row in rows if isinstance(row, Mapping)}
    weights = {str(row.get("segment") or ""): int(row.get("weight") or 0) for row in rows if isinstance(row, Mapping)}
    missing = sorted(set(S2PET04_REQUIRED_BUDGET_SEGMENTS) - observed)
    expected = dict(zip(S2PET04_REQUIRED_BUDGET_SEGMENTS, S2PET04_REQUIRED_BUDGET_WEIGHTS))
    invalid_weights = [segment for segment, weight in expected.items() if weights.get(segment) != weight]
    invalid_rows = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or not row.get("budget_explanation")
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
        or not row.get("evidence_refs")
    ]
    total = sum(weights.get(segment, 0) for segment in S2PET04_REQUIRED_BUDGET_SEGMENTS)
    reasons: list[str] = []
    if missing:
        reasons.append("S2PET04 missing budget segments: " + ", ".join(missing))
    if invalid_weights or total != 100:
        reasons.append("S2PET04 budget weights must match US-TA 35, US-LG 15, US-FM 30, US-TP 20 and total 100")
    if invalid_rows:
        reasons.append("S2PET04 budget records require explanations, metadata-only, no production, and evidence refs")
    return {"status": "pass" if not reasons else "blocked", "budget_segments_observed": sorted(segment for segment in observed if segment), "budget_weight_total": total, "blocking_reasons": reasons}


def _s2pet04_metadata_gate(
    policy_rows: Sequence[Mapping[str, Any]],
    replay_rows: Sequence[Mapping[str, Any]],
    shadow_rows: Sequence[Mapping[str, Any]],
    route_rows: Sequence[Mapping[str, Any]],
    budget_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    policy_violations = [
        row
        for row in policy_rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
        or row.get("public_schema_changed") is not False
        or row.get("live_source_fetch_executed") is not False
    ]
    other_rows = [*replay_rows, *shadow_rows, *route_rows, *budget_rows]
    other_violations = [
        row
        for row in other_rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("production_affected") is not False
    ]
    reasons: list[str] = []
    if policy_violations or other_violations:
        reasons.append("S2PET04 records must be metadata-only with no live fetch, public schema, or production side effects")
    return {"status": "pass" if not reasons else "blocked", "metadata_only_record_count": len(policy_rows) + len(other_rows) - len(policy_violations) - len(other_violations), "record_count": len(policy_rows) + len(other_rows), "blocking_reasons": reasons}


def _s2pft01_provincial_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    province_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"provincial_records[{index}] must be an object")
            continue
        province_id = str(record.get("province_id") or "").strip()
        row = {
            "province_id": province_id,
            "province_name": str(record.get("province_name") or "").strip(),
            "locality_type": str(record.get("locality_type") or "").strip(),
            "official_domain": str(record.get("official_domain") or "").strip(),
            "source_url": str(record.get("source_url") or "").strip(),
            "core_department_roles": list(record.get("core_department_roles") or []),
            "health_tier": str(record.get("health_tier") or "").strip(),
            "health_explanation": str(record.get("health_explanation") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "identity_state": str(record.get("identity_state") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not province_id:
            errors.append(f"provincial_records[{index}].province_id is required")
        if province_id in province_ids:
            errors.append(f"duplicate S2PFT01 province_id: {province_id}")
        province_ids.add(province_id)
        rows.append(row)
    if not rows:
        errors.append("S2PFT01 requires at least one provincial record")
    return rows, errors


def _s2pft01_provincial_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("province_id") or "") for row in rows if isinstance(row, Mapping)}
    observed_types = {
        str(row.get("locality_type") or "") for row in rows if isinstance(row, Mapping) and str(row.get("locality_type") or "")
    }
    missing = [province_id for province_id in S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS if province_id not in observed]
    unsupported = sorted(observed - set(S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS))
    missing_types = [locality_type for locality_type in S2PFT01_REQUIRED_LOCALITY_TYPES if locality_type not in observed_types]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT01 provincial coverage missing mainland provincial ids: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PFT01 provincial coverage has unsupported ids: " + ", ".join(unsupported))
    if missing_types:
        reasons.append("S2PFT01 provincial coverage missing locality types: " + ", ".join(missing_types))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_mainland_provincial_ids": list(S2PFT01_REQUIRED_MAINLAND_PROVINCIAL_IDS),
        "provincial_ids_observed": sorted(province_id for province_id in observed if province_id),
        "required_locality_types": list(S2PFT01_REQUIRED_LOCALITY_TYPES),
        "locality_types_observed": sorted(observed_types),
        "missing_mainland_provincial_ids": missing,
        "unsupported_provincial_ids": unsupported,
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft01_core_department_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    incomplete: list[Mapping[str, Any]] = []
    for row in rows:
        roles = set(row.get("core_department_roles") or []) if isinstance(row, Mapping) else set()
        if not set(S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES).issubset(roles):
            incomplete.append(row)
    reasons: list[str] = []
    if incomplete:
        reasons.append("S2PFT01 provincial records must include all required core department roles")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_core_department_roles": list(S2PFT01_REQUIRED_CORE_DEPARTMENT_ROLES),
        "complete_template_record_count": len(rows) - len(incomplete),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft01_health_tier_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    tiers = sorted(
        {
            str(row.get("health_tier") or "")
            for row in rows
            if isinstance(row, Mapping) and str(row.get("health_tier") or "")
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("health_tier") not in S2PFT01_ALLOWED_HEALTH_TIERS
        or not row.get("health_explanation")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT01 health tier requires allowed tier and health_explanation on every provincial record")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_health_tiers": list(S2PFT01_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": tiers,
        "healthy_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft01_provincial_authority_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("authority_gate") != "pass"
        or row.get("identity_state") not in S2PFT01_ALLOWED_IDENTITY_STATES
        or not row.get("official_domain")
        or not row.get("source_url")
        or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT01 authority gate requires official identity, domain, source_url, authority_gate=pass, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_identity_states": list(S2PFT01_ALLOWED_IDENTITY_STATES),
        "authority_checked_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft01_provincial_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PFT01 provincial records must stay metadata-only with no PDF/full-text, production, or SMTP side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(rows) - len(violations),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft02_jurisdiction_profiles(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    profiles: list[dict[str, Any]] = []
    errors: list[str] = []
    jurisdiction_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"jurisdiction_profiles[{index}] must be an object")
            continue
        jurisdiction_id = str(record.get("jurisdiction_id") or "").strip()
        profile = {
            "jurisdiction_id": jurisdiction_id,
            "jurisdiction_name": str(record.get("jurisdiction_name") or "").strip(),
            "legal_system_state": str(record.get("legal_system_state") or "").strip(),
            "government_structure_model": str(record.get("government_structure_model") or "").strip(),
            "language_profiles": list(record.get("language_profiles") or []),
            "official_domain": str(record.get("official_domain") or "").strip(),
            "source_url": str(record.get("source_url") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "template_source": str(record.get("template_source") or "").strip(),
            "mainland_template_applied": record.get("mainland_template_applied") is True,
            "autonomy_basis": str(record.get("autonomy_basis") or "").strip(),
            "legal_status_reference": str(record.get("legal_status_reference") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not jurisdiction_id:
            errors.append(f"jurisdiction_profiles[{index}].jurisdiction_id is required")
        if jurisdiction_id in jurisdiction_ids:
            errors.append(f"duplicate S2PFT02 jurisdiction_id: {jurisdiction_id}")
        jurisdiction_ids.add(jurisdiction_id)
        profiles.append(profile)
    if not profiles:
        errors.append("S2PFT02 requires at least one jurisdiction profile")
    return profiles, errors


def _s2pft02_jurisdiction_coverage_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(profile.get("jurisdiction_id") or "") for profile in profiles if isinstance(profile, Mapping)}
    missing = [jurisdiction_id for jurisdiction_id in S2PFT02_REQUIRED_JURISDICTION_IDS if jurisdiction_id not in observed]
    unsupported = sorted(observed - set(S2PFT02_REQUIRED_JURISDICTION_IDS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT02 HK/MO profile missing jurisdiction ids: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PFT02 HK/MO profile has unsupported jurisdiction ids: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_jurisdiction_ids": list(S2PFT02_REQUIRED_JURISDICTION_IDS),
        "jurisdiction_ids_observed": sorted(jurisdiction_id for jurisdiction_id in observed if jurisdiction_id),
        "missing_jurisdiction_ids": missing,
        "unsupported_jurisdiction_ids": unsupported,
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_language_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(language)
            for profile in profiles
            if isinstance(profile, Mapping)
            for language in list(profile.get("language_profiles") or [])
            if str(language)
        }
    )
    missing = [language for language in S2PFT02_REQUIRED_LANGUAGE_PROFILES if language not in set(observed)]
    missing_per_profile = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping) or not profile.get("language_profiles")
    ]
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT02 HK/MO profile missing language profiles: " + ", ".join(missing))
    if missing_per_profile:
        reasons.append("S2PFT02 each jurisdiction profile requires language_profiles")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_language_profiles": list(S2PFT02_REQUIRED_LANGUAGE_PROFILES),
        "language_profiles_observed": observed,
        "complete_language_profile_count": len(profiles) - len(missing_per_profile),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_legal_status_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(profile.get("legal_system_state") or "")
            for profile in profiles
            if isinstance(profile, Mapping) and str(profile.get("legal_system_state") or "")
        }
    )
    invalid = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping)
        or profile.get("legal_system_state") not in S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES
        or not profile.get("government_structure_model")
        or not profile.get("autonomy_basis")
        or not profile.get("legal_status_reference")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT02 legal status requires allowed legal system, government structure, autonomy basis, and legal status reference")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_legal_system_states": list(S2PFT02_ALLOWED_LEGAL_SYSTEM_STATES),
        "legal_system_states_observed": observed,
        "legal_status_checked_record_count": len(profiles) - len(invalid),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_template_independence_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping)
        or profile.get("mainland_template_applied") is not False
        or profile.get("template_source") in S2PFT02_FORBIDDEN_TEMPLATE_STATES
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT02 HK/MO profiles must not reuse mainland province or city templates")
    return {
        "status": "pass" if not reasons else "blocked",
        "forbidden_template_states": list(S2PFT02_FORBIDDEN_TEMPLATE_STATES),
        "independent_profile_count": len(profiles) - len(invalid),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_authority_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping)
        or profile.get("authority_gate") != "pass"
        or not profile.get("official_domain")
        or not profile.get("source_url")
        or not profile.get("evidence_refs")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT02 authority gate requires official_domain, source_url, authority_gate=pass, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "authority_checked_record_count": len(profiles) - len(invalid),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft02_metadata_gate(profiles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        profile
        for profile in profiles
        if not isinstance(profile, Mapping)
        or profile.get("metadata_only") is not True
        or profile.get("pdf_downloaded") is not False
        or profile.get("full_text_extracted") is not False
        or profile.get("production_affected") is not False
        or profile.get("real_smtp_sent") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PFT02 HK/MO profiles must stay metadata-only with no PDF/full-text, production, or SMTP side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(profiles) - len(violations),
        "record_count": len(profiles),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    city_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"city_records[{index}] must be an object")
            continue
        city_id = str(record.get("city_id") or "").strip()
        try:
            region_weight = float(record.get("region_weight", 0))
        except (TypeError, ValueError):
            region_weight = 0.0
        row = {
            "city_id": city_id,
            "city_name": str(record.get("city_name") or "").strip(),
            "province_id": str(record.get("province_id") or "").strip(),
            "region_group": str(record.get("region_group") or "").strip(),
            "aliases": list(record.get("aliases") or []),
            "department_roles": list(record.get("department_roles") or []),
            "region_weight": region_weight,
            "health_tier": str(record.get("health_tier") or "").strip(),
            "health_explanation": str(record.get("health_explanation") or "").strip(),
            "official_domain": str(record.get("official_domain") or "").strip(),
            "source_url": str(record.get("source_url") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not city_id:
            errors.append(f"city_records[{index}].city_id is required")
        if city_id in city_ids:
            errors.append(f"duplicate S2PFT03 city_id: {city_id}")
        city_ids.add(city_id)
        rows.append(row)
    if not rows:
        errors.append("S2PFT03 requires at least one city record")
    return rows, errors


def _s2pft03_city_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("city_id") or "") for row in rows if isinstance(row, Mapping)}
    missing = [city_id for city_id in S2PFT03_REQUIRED_CITY_IDS if city_id not in observed]
    unsupported = sorted(observed - set(S2PFT03_REQUIRED_CITY_IDS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT03 key-city coverage missing city ids: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PFT03 key-city coverage has unsupported city ids: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_city_ids": list(S2PFT03_REQUIRED_CITY_IDS),
        "city_ids_observed": sorted(city_id for city_id in observed if city_id),
        "missing_city_ids": missing,
        "unsupported_city_ids": unsupported,
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_alias_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [row for row in rows if not isinstance(row, Mapping) or not row.get("city_name") or not row.get("aliases")]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT03 key-city records require city_name and aliases")
    return {
        "status": "pass" if not reasons else "blocked",
        "alias_checked_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_department_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_by_city: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        roles = set(row.get("department_roles") or [])
        missing = [role for role in S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES if role not in roles]
        if missing:
            missing_by_city[str(row.get("city_id") or "")] = missing
    reasons: list[str] = []
    if missing_by_city:
        reasons.append("S2PFT03 key-city records missing required department roles")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_city_department_roles": list(S2PFT03_REQUIRED_CITY_DEPARTMENT_ROLES),
        "complete_department_record_count": len(rows) - len(missing_by_city),
        "record_count": len(rows),
        "missing_roles_by_city": missing_by_city,
        "blocking_reasons": reasons,
    }


def _s2pft03_region_weight_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(row.get("region_group") or "")
            for row in rows
            if isinstance(row, Mapping) and str(row.get("region_group") or "")
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("region_group") not in S2PFT03_ALLOWED_REGION_GROUPS
        or not (0 < float(row.get("region_weight") or 0) <= 1)
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT03 key-city records require allowed region_group and region_weight in (0, 1]")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_region_groups": list(S2PFT03_ALLOWED_REGION_GROUPS),
        "region_groups_observed": observed,
        "region_weight_total": round(sum(float(row.get("region_weight") or 0) for row in rows if isinstance(row, Mapping)), 6),
        "weighted_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_health_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(row.get("health_tier") or "")
            for row in rows
            if isinstance(row, Mapping) and str(row.get("health_tier") or "")
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("health_tier") not in S2PFT03_ALLOWED_HEALTH_TIERS
        or not row.get("health_explanation")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT03 key-city records require allowed health_tier and health_explanation")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_health_tiers": list(S2PFT03_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": observed,
        "healthy_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_authority_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("authority_gate") != "pass"
        or not row.get("official_domain")
        or not row.get("source_url")
        or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT03 key-city authority gate requires official_domain, source_url, authority_gate=pass, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "authority_checked_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft03_city_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PFT03 key-city records must stay metadata-only with no PDF/full-text, production, or SMTP side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(rows) - len(violations),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft04_zone_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    zone_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"zone_records[{index}] must be an object")
            continue
        zone_id = str(record.get("zone_id") or "").strip()
        row = {
            "zone_id": zone_id,
            "zone_name": str(record.get("zone_name") or "").strip(),
            "zone_type": str(record.get("zone_type") or "").strip(),
            "parent_city_ids": list(record.get("parent_city_ids") or []),
            "authority_roles": list(record.get("authority_roles") or []),
            "policy_focus_areas": list(record.get("policy_focus_areas") or []),
            "health_tier": str(record.get("health_tier") or "").strip(),
            "health_explanation": str(record.get("health_explanation") or "").strip(),
            "official_domain": str(record.get("official_domain") or "").strip(),
            "source_url": str(record.get("source_url") or "").strip(),
            "authority_gate": str(record.get("authority_gate") or "").strip(),
            "dedupe_gate": str(record.get("dedupe_gate") or "").strip(),
            "metadata_only": record.get("metadata_only") is True,
            "pdf_downloaded": record.get("pdf_downloaded") is True,
            "full_text_extracted": record.get("full_text_extracted") is True,
            "production_affected": record.get("production_affected") is True,
            "real_smtp_sent": record.get("real_smtp_sent") is True,
            "evidence_refs": list(record.get("evidence_refs") or []),
        }
        if not zone_id:
            errors.append(f"zone_records[{index}].zone_id is required")
        if zone_id in zone_ids:
            errors.append(f"duplicate S2PFT04 zone_id: {zone_id}")
        zone_ids.add(zone_id)
        rows.append(row)
    if not rows:
        errors.append("S2PFT04 requires at least one special-zone record")
    return rows, errors


def _s2pft04_zone_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = {str(row.get("zone_id") or "") for row in rows if isinstance(row, Mapping)}
    missing = [zone_id for zone_id in S2PFT04_REQUIRED_ZONE_IDS if zone_id not in observed]
    unsupported = sorted(observed - set(S2PFT04_REQUIRED_ZONE_IDS))
    reasons: list[str] = []
    if missing:
        reasons.append("S2PFT04 special-zone discovery missing zone ids: " + ", ".join(missing))
    if unsupported:
        reasons.append("S2PFT04 special-zone discovery has unsupported zone ids: " + ", ".join(unsupported))
    return {
        "status": "pass" if not reasons else "blocked",
        "required_zone_ids": list(S2PFT04_REQUIRED_ZONE_IDS),
        "zone_ids_observed": sorted(zone_id for zone_id in observed if zone_id),
        "missing_zone_ids": missing,
        "unsupported_zone_ids": unsupported,
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft04_zone_authority_role_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_by_zone: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        roles = set(row.get("authority_roles") or [])
        missing = [role for role in S2PFT04_REQUIRED_ZONE_AUTHORITY_ROLES if role not in roles]
        if missing:
            missing_by_zone[str(row.get("zone_id") or "")] = missing
    reasons: list[str] = []
    if missing_by_zone:
        reasons.append("S2PFT04 special-zone records missing required authority roles")
    return {
        "status": "pass" if not reasons else "blocked",
        "required_zone_authority_roles": list(S2PFT04_REQUIRED_ZONE_AUTHORITY_ROLES),
        "complete_authority_role_record_count": len(rows) - len(missing_by_zone),
        "record_count": len(rows),
        "missing_roles_by_zone": missing_by_zone,
        "blocking_reasons": reasons,
    }


def _s2pft04_zone_type_policy_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    zone_types = sorted(
        {
            str(row.get("zone_type") or "")
            for row in rows
            if isinstance(row, Mapping) and str(row.get("zone_type") or "")
        }
    )
    policy_areas = sorted(
        {
            str(policy_area)
            for row in rows
            if isinstance(row, Mapping)
            for policy_area in list(row.get("policy_focus_areas") or [])
            if str(policy_area)
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("zone_type") not in S2PFT04_ALLOWED_ZONE_TYPES
        or not set(row.get("policy_focus_areas") or [])
        or not set(row.get("policy_focus_areas") or []).issubset(set(S2PFT04_ALLOWED_POLICY_FOCUS_AREAS))
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT04 special-zone records require allowed zone_type and policy_focus_areas")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_zone_types": list(S2PFT04_ALLOWED_ZONE_TYPES),
        "zone_types_observed": zone_types,
        "allowed_policy_focus_areas": list(S2PFT04_ALLOWED_POLICY_FOCUS_AREAS),
        "policy_focus_areas_observed": policy_areas,
        "typed_policy_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft04_parent_city_gate(rows: Sequence[Mapping[str, Any]], *, parent_city_ids: set[str]) -> dict[str, Any]:
    observed = sorted(
        {
            str(city_id)
            for row in rows
            if isinstance(row, Mapping)
            for city_id in list(row.get("parent_city_ids") or [])
            if str(city_id)
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or not set(row.get("parent_city_ids") or [])
        or not set(row.get("parent_city_ids") or []).issubset(parent_city_ids)
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT04 special-zone records require parent_city_ids mapped to S2PFT03 observed cities")
    return {
        "status": "pass" if not reasons else "blocked",
        "parent_city_ids_observed": observed,
        "supported_parent_city_ids": sorted(parent_city_ids),
        "mapped_zone_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft04_zone_health_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted(
        {
            str(row.get("health_tier") or "")
            for row in rows
            if isinstance(row, Mapping) and str(row.get("health_tier") or "")
        }
    )
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("health_tier") not in S2PFT04_ALLOWED_HEALTH_TIERS
        or not row.get("health_explanation")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT04 special-zone records require allowed health_tier and health_explanation")
    return {
        "status": "pass" if not reasons else "blocked",
        "allowed_health_tiers": list(S2PFT04_ALLOWED_HEALTH_TIERS),
        "health_tiers_observed": observed,
        "healthy_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft04_zone_authority_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("authority_gate") != "pass"
        or row.get("dedupe_gate") != "pass"
        or not row.get("official_domain")
        or not row.get("source_url")
        or not row.get("evidence_refs")
    ]
    reasons: list[str] = []
    if invalid:
        reasons.append("S2PFT04 special-zone authority gate requires official_domain, source_url, authority_gate=pass, dedupe_gate=pass, and evidence_refs")
    return {
        "status": "pass" if not reasons else "blocked",
        "authority_checked_record_count": len(rows) - len(invalid),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft04_zone_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    violations = [
        row
        for row in rows
        if not isinstance(row, Mapping)
        or row.get("metadata_only") is not True
        or row.get("pdf_downloaded") is not False
        or row.get("full_text_extracted") is not False
        or row.get("production_affected") is not False
        or row.get("real_smtp_sent") is not False
    ]
    reasons: list[str] = []
    if violations:
        reasons.append("S2PFT04 special-zone records must stay metadata-only with no PDF/full-text, production, or SMTP side effects")
    return {
        "status": "pass" if not reasons else "blocked",
        "metadata_only_record_count": len(rows) - len(violations),
        "record_count": len(rows),
        "blocking_reasons": reasons,
    }


def _s2pft05_governance_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    component_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"governance_records[{index}] must be an object")
            continue
        row = dict(record)
        component_id = str(row.get("component_id") or "")
        if not component_id:
            errors.append(f"governance_records[{index}].component_id is required")
        elif component_id in component_ids:
            errors.append(f"duplicate S2PFT05 component_id: {component_id}")
        component_ids.add(component_id)
        rows.append(row)
    return rows, errors


def _s2pft05_component_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("component_id")) for row in rows if row.get("component_id")})
    missing = [component for component in S2PFT05_REQUIRED_COMPONENTS if component not in set(observed)]
    return {
        "status": "pass" if not missing else "blocked",
        "components_observed": observed,
        "blocking_reasons": [f"S2PFT05 missing required components: {', '.join(missing)}"] if missing else [],
    }


def _s2pft05_quota_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("quota_role")) for row in rows if row.get("quota_role")})
    blocking: list[str] = []
    missing = [role for role in S2PFT05_REQUIRED_QUOTA_ROLES if role not in set(observed)]
    if missing:
        blocking.append("S2PFT05 missing quota roles: " + ", ".join(missing))
    for row in rows:
        if row.get("quota_gate") != "pass":
            blocking.append(f"S2PFT05 quota gate failed for {row.get('component_id')}")
        if not row.get("quota_explanation"):
            blocking.append(f"S2PFT05 quota explanation missing for {row.get('component_id')}")
    return {
        "status": "pass" if not blocking else "blocked",
        "quota_roles_observed": observed,
        "blocking_reasons": blocking,
    }


def _s2pft05_health_balance_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("health_tier")) for row in rows if row.get("health_tier")})
    blocking: list[str] = []
    if not observed:
        blocking.append("S2PFT05 health tiers are required")
    unsupported = [tier for tier in observed if tier not in S2PFT05_ALLOWED_HEALTH_TIERS]
    if unsupported:
        blocking.append("S2PFT05 unsupported health tiers: " + ", ".join(unsupported))
    for row in rows:
        if not row.get("health_explanation"):
            blocking.append(f"S2PFT05 health explanation missing for {row.get('component_id')}")
    return {
        "status": "pass" if not blocking else "blocked",
        "health_tiers_observed": observed,
        "blocking_reasons": blocking,
    }


def _s2pft05_elimination_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking = [
        f"S2PFT05 elimination explanation missing for {row.get('component_id')}"
        for row in rows
        if not row.get("elimination_explanation")
    ]
    return {
        "status": "pass" if not blocking else "blocked",
        "blocking_reasons": blocking,
    }


def _s2pft05_fallback_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    for row in rows:
        if not row.get("fallback_route"):
            blocking.append(f"S2PFT05 fallback route missing for {row.get('component_id')}")
        if row.get("fallback_gate") != "pass":
            blocking.append(f"S2PFT05 fallback gate failed for {row.get('component_id')}")
    return {
        "status": "pass" if not blocking else "blocked",
        "blocking_reasons": blocking,
    }


def _s2pft05_replay_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    replay_dates = sorted(
        {
            str(replay_date)
            for row in rows
            for replay_date in (row.get("replay_dates") or [])
            if _is_iso_date(str(replay_date))
        }
    )
    blocking: list[str] = []
    if len(replay_dates) < S2PFT05_REQUIRED_REPLAY_DATES:
        blocking.append(f"S2PFT05 full D3 replay requires {S2PFT05_REQUIRED_REPLAY_DATES} distinct dates")
    for row in rows:
        row_dates = row.get("replay_dates") or []
        if not row_dates:
            blocking.append(f"S2PFT05 replay dates missing for {row.get('component_id')}")
        elif any(not _is_iso_date(str(replay_date)) for replay_date in row_dates):
            blocking.append(f"S2PFT05 replay dates invalid for {row.get('component_id')}")
    return {
        "status": "pass" if not blocking else "blocked",
        "replay_dates_observed": replay_dates,
        "blocking_reasons": blocking,
    }


def _s2pft05_metadata_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    for row in rows:
        if row.get("metadata_only") is not True:
            blocking.append(f"S2PFT05 metadata_only must be true for {row.get('component_id')}")
        for key in ("pdf_downloaded", "full_text_extracted", "production_affected", "real_smtp_sent"):
            if row.get(key) is not False:
                blocking.append(f"S2PFT05 {key} must be false for {row.get('component_id')}")
    return {
        "status": "pass" if not blocking else "blocked",
        "blocking_reasons": blocking,
    }


def _s2pgt01_domain_rows(reports: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, report in enumerate(reports):
        if not isinstance(report, Mapping):
            errors.append(f"source_domain_reports[{index}] must be an object")
            continue
        domain = str(report.get("source_domain") or report.get("source_domain_id") or "").strip()
        status = str(report.get("status") or "").strip()
        row = {
            "source_domain": domain,
            "task_id": str(report.get("task_id") or ""),
            "acceptance_id": str(report.get("acceptance_id") or ""),
            "status": status,
            "shadow_evidence_ready": report.get("shadow_evidence_ready") is True,
            "source_domain_qualified": report.get("source_domain_qualified") is True,
            "report_ref": str(report.get("report_ref") or report.get("evidence_ref") or ""),
            "production_affected": report.get("production_affected") is True,
            "schema_migration_required": report.get("schema_migration_required") is True,
        }
        if domain not in S2PGT01_REQUIRED_SOURCE_DOMAINS:
            errors.append(f"source_domain_reports[{index}].source_domain is not supported")
        if status != "pass":
            errors.append(f"source_domain_reports[{index}].status must be pass")
        if not (row["shadow_evidence_ready"] or row["source_domain_qualified"]):
            errors.append(f"source_domain_reports[{index}] requires shadow_evidence_ready or source_domain_qualified")
        if not row["report_ref"]:
            errors.append(f"source_domain_reports[{index}].report_ref is required")
        if row["production_affected"]:
            errors.append(f"source_domain_reports[{index}].production_affected must be false")
        if row["schema_migration_required"]:
            errors.append(f"source_domain_reports[{index}].schema_migration_required must be false")
        rows.append(row)
    return rows, errors


def _s2pgt01_packet_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"packet_records[{index}] must be an object")
            continue
        source_item = record.get("source_item") if isinstance(record.get("source_item"), Mapping) else record
        claims = record.get("evidence_claims") if isinstance(record.get("evidence_claims"), Sequence) else record.get("claims")
        claim_rows = [claim for claim in (claims or []) if isinstance(claim, Mapping)]
        source_id = str(source_item.get("source_id") or record.get("source_id") or "").strip()
        source_domain = str(record.get("source_domain") or source_item.get("source_domain") or "").strip()
        packet_id = str(record.get("packet_id") or f"{S2PGT01_PACKET_VERSION}:{source_domain}:{source_id}").strip()
        levels = _s2pgt01_levels(record, source_item)
        content_refs = source_item.get("content_refs") if isinstance(source_item.get("content_refs"), list) else []
        locator_refs = _s2pgt01_locator_refs(claim_rows)
        row = {
            "packet_id": packet_id,
            "packet_version": str(record.get("packet_version") or S2PGT01_PACKET_VERSION),
            "source_domain": source_domain,
            "source_id": source_id,
            "source_type": str(source_item.get("source_type") or record.get("source_type") or ""),
            "source_adapter": str(source_item.get("source_adapter") or record.get("source_adapter") or ""),
            "canonical_url": str(source_item.get("canonical_url") or record.get("canonical_url") or ""),
            "title": str(source_item.get("title") or record.get("title") or ""),
            "evidence_levels_available": levels,
            "claim_ids": [str(claim.get("claim_id") or "") for claim in claim_rows if claim.get("claim_id")],
            "content_ref_ids": [str(ref.get("content_ref_id") or ref.get("ref_id") or ref.get("url") or ref) for ref in content_refs],
            "support_statuses": sorted({str(claim.get("support_status") or "") for claim in claim_rows if claim.get("support_status")}),
            "locator_refs": locator_refs,
            "board_routes": [str(route) for route in (record.get("board_routes") or []) if str(route)],
            "metadata_only": record.get("metadata_only") is not False,
            "old_arxiv_compatible": (
                record.get("old_arxiv_compatible") is True
                if "old_arxiv_compatible" in record
                else source_domain == "d1_research_preprint"
            ),
            "schema_migration_required": record.get("schema_migration_required") is True,
            "production_affected": record.get("production_affected") is True,
        }
        if not packet_id or packet_id in seen:
            errors.append(f"packet_records[{index}].packet_id must be unique")
        seen.add(packet_id)
        rows.append(row)
    return rows, errors


def _s2pgt01_levels(record: Mapping[str, Any], source_item: Mapping[str, Any]) -> list[str]:
    raw_levels = record.get("evidence_levels_available") or record.get("evidence_levels") or []
    levels = {str(level).strip() for level in raw_levels if str(level).strip()}
    metadata = source_item.get("metadata") if isinstance(source_item.get("metadata"), Mapping) else {}
    if source_item.get("title") or metadata:
        levels.add("metadata")
    if metadata.get("abstract") or metadata.get("summary") or source_item.get("summary"):
        levels.add("abstract")
    if record.get("full_text_reference") or record.get("full_text_locator"):
        levels.add("full_text")
    if record.get("cross_source_refs") or record.get("cross_source_verification"):
        levels.add("cross_source_verification")
    return sorted(levels)


def _s2pgt01_locator_refs(claims: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for claim in claims:
        locator = claim.get("locator") if isinstance(claim.get("locator"), Mapping) else {}
        for key in ("stable_url", "page", "section", "table", "figure", "quote"):
            value = locator.get(key)
            if value:
                refs.append(f"{key}:{value}")
    return refs


def _s2pgt01_domain_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("source_domain")) for row in rows if row.get("source_domain")})
    blocking = [f"S2PGT01 missing source domain {domain}" for domain in S2PGT01_REQUIRED_SOURCE_DOMAINS if domain not in observed]
    return {
        "status": "pass" if not blocking else "blocked",
        "source_domains_observed": observed,
        "blocking_reasons": blocking,
    }


def _s2pgt01_packet_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    if not rows:
        blocking.append("S2PGT01 requires at least one EvidencePacket V2 row")
    for index, row in enumerate(rows):
        for field in S2PGT01_REQUIRED_PACKET_FIELDS:
            if row.get(field) in (None, "", []):
                blocking.append(f"evidence_packets[{index}].{field} is required")
        if row.get("packet_version") != S2PGT01_PACKET_VERSION:
            blocking.append(f"evidence_packets[{index}].packet_version must be EvidencePacketV2")
        if row.get("source_domain") not in S2PGT01_REQUIRED_SOURCE_DOMAINS:
            blocking.append(f"evidence_packets[{index}].source_domain is not supported")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt01_evidence_level_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({level for row in rows for level in (row.get("evidence_levels_available") or [])})
    blocking = [f"S2PGT01 missing evidence level {level}" for level in S2PGT01_REQUIRED_EVIDENCE_LEVELS if level not in observed]
    unsupported = sorted(set(observed) - set(S2PGT01_REQUIRED_EVIDENCE_LEVELS))
    blocking.extend(f"S2PGT01 unsupported evidence level {level}" for level in unsupported)
    for index, row in enumerate(rows):
        if "metadata" not in set(row.get("evidence_levels_available") or []):
            blocking.append(f"evidence_packets[{index}] must include metadata level")
    return {
        "status": "pass" if not blocking else "blocked",
        "evidence_levels_observed": observed,
        "blocking_reasons": blocking,
    }


def _s2pgt01_compatibility_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    d1_rows = [row for row in rows if row.get("source_domain") == "d1_research_preprint"]
    if not d1_rows:
        blocking.append("S2PGT01 requires at least one D1 old arXiv-compatible packet")
    for index, row in enumerate(d1_rows):
        if row.get("old_arxiv_compatible") is not True:
            blocking.append(f"D1 packet {index} must be old_arxiv_compatible=true")
        if not row.get("claim_ids") or not row.get("locator_refs"):
            blocking.append(f"D1 packet {index} requires claim_ids and locator_refs")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt01_no_side_effect_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    for index, row in enumerate(rows):
        if row.get("schema_migration_required") is not False:
            blocking.append(f"evidence_packets[{index}].schema_migration_required must be false")
        if row.get("production_affected") is not False:
            blocking.append(f"evidence_packets[{index}].production_affected must be false")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt02_identity_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[str]], list[str]]:
    rows: list[dict[str, Any]] = []
    identifier_index: dict[str, list[str]] = {}
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"identity_records[{index}] must be an object")
            continue
        identifiers, identifier_errors = _s2pgt02_identifiers(record.get("identifiers") or {})
        errors.extend(f"identity_records[{index}].{error}" for error in identifier_errors)
        source_id = str(record.get("source_id") or "").strip()
        row = {
            "record_id": str(record.get("record_id") or source_id or f"identity:{index}"),
            "source_id": source_id,
            "source_domain": str(record.get("source_domain") or "").strip(),
            "title": str(record.get("title") or ""),
            "identifiers": identifiers,
            "declared_canonical_id": str(record.get("canonical_id") or "").strip(),
            "evidence_refs": [str(ref) for ref in (record.get("evidence_refs") or []) if str(ref)],
            "schema_migration_required": record.get("schema_migration_required") is True,
            "production_affected": record.get("production_affected") is True,
        }
        if not row["source_id"]:
            errors.append(f"identity_records[{index}].source_id is required")
        if not row["source_domain"]:
            errors.append(f"identity_records[{index}].source_domain is required")
        if not identifiers:
            errors.append(f"identity_records[{index}].identifiers is required")
        if not row["evidence_refs"]:
            errors.append(f"identity_records[{index}].evidence_refs is required")
        if row["schema_migration_required"]:
            errors.append(f"identity_records[{index}].schema_migration_required must be false")
        if row["production_affected"]:
            errors.append(f"identity_records[{index}].production_affected must be false")
        for identifier in identifiers:
            identifier_index.setdefault(identifier, []).append(row["record_id"])
        rows.append(row)
    return rows, {key: sorted(value) for key, value in sorted(identifier_index.items())}, errors


def _s2pgt02_identifiers(raw: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if not isinstance(raw, Mapping):
        return [], ["identifiers must be an object"]
    identifiers: list[str] = []
    for identifier_type, values in raw.items():
        normalized_type = str(identifier_type or "").strip()
        if normalized_type not in S2PGT02_REQUIRED_IDENTIFIER_TYPES:
            errors.append(f"unsupported identifier type {normalized_type}")
            continue
        value_list = values if isinstance(values, list) else [values]
        for value in value_list:
            normalized = _s2pgt02_normalized_identifier(normalized_type, str(value or ""))
            if normalized:
                identifiers.append(normalized)
    return sorted(set(identifiers)), errors


def _s2pgt02_normalized_identifier(identifier_type: str, value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if identifier_type == "doi":
        text = text.lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/").removeprefix("doi:")
    elif identifier_type == "pmid":
        text = re.sub(r"\D+", "", text)
    elif identifier_type == "arxiv":
        text = text.lower().removeprefix("arxiv:")
    elif identifier_type == "cn_document_number":
        text = re.sub(r"\s+", "", text).upper()
    elif identifier_type == "federal_register_document_number":
        text = re.sub(r"\s+", "", text).lower()
    elif identifier_type == "cik":
        digits = re.sub(r"\D+", "", text)
        text = digits.lstrip("0") or digits
    return f"{identifier_type}:{text}" if text else ""


def _s2pgt02_canonical_entities(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str], list[str]]:
    parent: dict[str, str] = {}
    declared_by_identifier: dict[str, set[str]] = {}
    errors: list[str] = []

    def find(item: str) -> str:
        parent.setdefault(item, item)
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        canonical_root = min(left_root, right_root)
        parent[left_root] = canonical_root
        parent[right_root] = canonical_root

    for row in rows:
        identifiers = [str(identifier) for identifier in row.get("identifiers") or []]
        for identifier in identifiers:
            find(identifier)
            if row.get("declared_canonical_id"):
                declared_by_identifier.setdefault(identifier, set()).add(str(row.get("declared_canonical_id")))
        for identifier in identifiers[1:]:
            union(identifiers[0], identifier)

    for identifier, declared_ids in sorted(declared_by_identifier.items()):
        if len(declared_ids) > 1:
            errors.append(f"S2PGT02 duplicate canonical declaration for {identifier}: {', '.join(sorted(declared_ids))}")

    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        identifiers = [str(identifier) for identifier in row.get("identifiers") or []]
        if not identifiers:
            continue
        root = min(find(identifier) for identifier in identifiers)
        groups.setdefault(root, []).append(row)

    canonical_lookup: dict[str, str] = {}
    entities: list[dict[str, Any]] = []
    for root, group_rows in sorted(groups.items()):
        identifiers = sorted({identifier for row in group_rows for identifier in (row.get("identifiers") or [])})
        canonical_id = "kg:" + _s2pgt02_slug(identifiers[0] if identifiers else root)
        for identifier in identifiers:
            canonical_lookup[identifier] = canonical_id
        entities.append(
            {
                "canonical_id": canonical_id,
                "identifiers": identifiers,
                "identifier_types": sorted({identifier.split(":", 1)[0] for identifier in identifiers}),
                "source_ids": sorted({str(row.get("source_id")) for row in group_rows if row.get("source_id")}),
                "source_domains": sorted({str(row.get("source_domain")) for row in group_rows if row.get("source_domain")}),
                "titles": sorted({str(row.get("title")) for row in group_rows if row.get("title")}),
                "evidence_refs": sorted({str(ref) for row in group_rows for ref in (row.get("evidence_refs") or [])}),
            }
        )
    return entities, canonical_lookup, errors


def _s2pgt02_relation_rows(records: Sequence[Mapping[str, Any]], canonical_lookup: Mapping[str, str]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_relations: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"relation_records[{index}] must be an object")
            continue
        relation_type = str(record.get("relation_type") or "").strip()
        source_canonical_id = _s2pgt02_resolve_canonical(record.get("source_identifier"), canonical_lookup)
        target_canonical_id = _s2pgt02_resolve_canonical(record.get("target_identifier"), canonical_lookup)
        evidence_refs = [str(ref) for ref in (record.get("evidence_refs") or []) if str(ref)]
        relation_id = str(record.get("relation_id") or f"{relation_type}:{source_canonical_id}->{target_canonical_id}").strip()
        idempotency_key = str(record.get("idempotency_key") or relation_id).strip()
        row = {
            "relation_id": relation_id,
            "relation_type": relation_type,
            "source_canonical_id": source_canonical_id,
            "target_canonical_id": target_canonical_id,
            "evidence_refs": evidence_refs,
            "locator_refs": [str(ref) for ref in (record.get("locator_refs") or []) if str(ref)],
            "support_status": str(record.get("support_status") or ""),
            "idempotency_key": idempotency_key,
            "schema_migration_required": record.get("schema_migration_required") is True,
            "production_affected": record.get("production_affected") is True,
        }
        if relation_type not in S2PGT02_ALLOWED_RELATION_TYPES:
            errors.append(f"relation_records[{index}].relation_type is not supported")
        if not source_canonical_id:
            errors.append(f"relation_records[{index}].source_identifier does not resolve")
        if not target_canonical_id:
            errors.append(f"relation_records[{index}].target_identifier does not resolve")
        if not evidence_refs:
            errors.append(f"relation_records[{index}].evidence_refs is required")
        if not row["support_status"]:
            errors.append(f"relation_records[{index}].support_status is required")
        if relation_id in seen_relations:
            errors.append(f"relation_records[{index}].relation_id must be unique")
        seen_relations.add(relation_id)
        if row["schema_migration_required"]:
            errors.append(f"relation_records[{index}].schema_migration_required must be false")
        if row["production_affected"]:
            errors.append(f"relation_records[{index}].production_affected must be false")
        rows.append(row)
    return rows, errors


def _s2pgt02_resolve_canonical(identifier: Any, canonical_lookup: Mapping[str, str]) -> str:
    if isinstance(identifier, Mapping):
        identifier_type = str(identifier.get("type") or identifier.get("identifier_type") or "")
        value = str(identifier.get("value") or identifier.get("identifier_value") or "")
        return canonical_lookup.get(_s2pgt02_normalized_identifier(identifier_type, value), "")
    text = str(identifier or "").strip()
    if not text:
        return ""
    if text.startswith("kg:"):
        return text
    if ":" in text:
        return canonical_lookup.get(text, "")
    return ""


def _s2pgt02_identifier_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(identifier).split(":", 1)[0] for row in rows for identifier in (row.get("identifiers") or [])})
    blocking = [f"S2PGT02 missing identifier type {identifier_type}" for identifier_type in S2PGT02_REQUIRED_IDENTIFIER_TYPES if identifier_type not in observed]
    return {"status": "pass" if not blocking else "blocked", "identifier_types_observed": observed, "blocking_reasons": blocking}


def _s2pgt02_canonical_gate(entities: Sequence[Mapping[str, Any]], canonical_errors: Sequence[str]) -> dict[str, Any]:
    canonical_ids = [str(entity.get("canonical_id") or "") for entity in entities]
    duplicate_count = len(canonical_ids) - len(set(canonical_ids))
    blocking = list(canonical_errors)
    if duplicate_count:
        blocking.append(f"S2PGT02 duplicate canonical ids: {duplicate_count}")
    if not entities:
        blocking.append("S2PGT02 requires at least one canonical entity")
    return {"status": "pass" if not blocking else "blocked", "duplicate_canonical_count": duplicate_count + len(canonical_errors), "blocking_reasons": blocking}


def _s2pgt02_relation_evidence_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    if not rows:
        blocking.append("S2PGT02 requires at least one knowledge graph relation")
    for index, row in enumerate(rows):
        for field in S2PGT02_REQUIRED_RELATION_FIELDS:
            if row.get(field) in (None, "", []):
                blocking.append(f"knowledge_graph_relations[{index}].{field} is required")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt02_idempotent_update_gate(entities: Sequence[Mapping[str, Any]], relations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    keys = [str(row.get("idempotency_key") or "") for row in relations]
    duplicates = sorted({key for key in keys if key and keys.count(key) > 1})
    blocking = [f"S2PGT02 duplicate idempotency key {key}" for key in duplicates]
    return {
        "status": "pass" if not blocking else "blocked",
        "idempotent_update_hash": _s2pgt02_graph_state_hash(entities, relations),
        "blocking_reasons": blocking,
    }


def _s2pgt02_no_side_effect_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    for index, row in enumerate(rows):
        if row.get("schema_migration_required") is not False:
            blocking.append(f"s2pgt02_rows[{index}].schema_migration_required must be false")
        if row.get("production_affected") is not False:
            blocking.append(f"s2pgt02_rows[{index}].production_affected must be false")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt02_graph_state_hash(entities: Sequence[Mapping[str, Any]], relations: Sequence[Mapping[str, Any]]) -> str:
    payload = {
        "canonical_entities": sorted([dict(entity) for entity in entities], key=lambda item: str(item.get("canonical_id") or "")),
        "knowledge_graph_relations": sorted([dict(row) for row in relations], key=lambda item: str(item.get("relation_id") or "")),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _s2pgt02_slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


def _s2pgt03_packet_index(packets: Sequence[Any]) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        source_id = str(packet.get("source_id") or "").strip()
        if source_id:
            index[source_id] = packet
    return index


def _s2pgt03_route_rows(
    records: Sequence[Mapping[str, Any]],
    packet_index: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    route_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"route_records[{index}] must be an object")
            continue
        source_domain = str(record.get("source_domain") or "").strip()
        source_id = str(record.get("source_id") or "").strip()
        primary_boards = _s2pgt03_board_list(record.get("primary_boards"))
        cross_boards = _s2pgt03_board_list(record.get("cross_cutting_boards"))
        reason_codes = sorted({str(reason) for reason in (record.get("reason_codes") or []) if str(reason)})
        evidence_refs = [str(ref) for ref in (record.get("evidence_refs") or []) if str(ref)]
        route_id = str(record.get("route_id") or f"route:{source_domain}:{source_id}").strip()
        packet = packet_index.get(source_id)
        row = {
            "route_id": route_id,
            "source_domain": source_domain,
            "source_id": source_id,
            "primary_boards": primary_boards,
            "cross_cutting_boards": cross_boards,
            "reason_codes": reason_codes,
            "route_explanation": str(record.get("route_explanation") or "").strip(),
            "evidence_refs": evidence_refs,
            "packet_board_routes": sorted({str(board) for board in ((packet or {}).get("board_routes") or []) if str(board)}),
            "packet_ref": str((packet or {}).get("packet_id") or source_id),
            "schema_migration_required": record.get("schema_migration_required") is True,
            "production_affected": record.get("production_affected") is True,
        }
        if not source_domain:
            errors.append(f"route_records[{index}].source_domain is required")
        elif source_domain not in S2PGT03_REQUIRED_SOURCE_DOMAINS:
            errors.append(f"route_records[{index}].source_domain is not supported")
        if not source_id:
            errors.append(f"route_records[{index}].source_id is required")
        elif source_id not in packet_index:
            errors.append(f"route_records[{index}].source_id must reference an EvidencePacket source_id")
        elif packet and packet.get("source_domain") != source_domain:
            errors.append(f"route_records[{index}].source_domain must match EvidencePacket source_domain")
        if not primary_boards:
            errors.append(f"route_records[{index}].primary_boards is required")
        if not cross_boards:
            errors.append(f"route_records[{index}].cross_cutting_boards is required")
        if not reason_codes:
            errors.append(f"route_records[{index}].reason_codes is required")
        if not row["route_explanation"]:
            errors.append(f"route_records[{index}].route_explanation is required")
        if not evidence_refs:
            errors.append(f"route_records[{index}].evidence_refs is required")
        if route_id in route_ids:
            errors.append(f"route_records[{index}].route_id must be unique")
        route_ids.add(route_id)
        allowed = _s2pgt03_allowed_boards_for_source_domain(source_domain)
        for board in primary_boards:
            if board not in S2PGT03_REQUIRED_PRIMARY_BOARDS:
                errors.append(f"route_records[{index}].primary_boards contains unsupported board {board}")
            elif board not in allowed:
                errors.append(f"route_records[{index}].primary_boards contains board {board} outside source-domain mapping")
        for board in cross_boards:
            if board not in S2PGT03_REQUIRED_CROSS_CUTTING_BOARDS:
                errors.append(f"route_records[{index}].cross_cutting_boards contains unsupported board {board}")
        for reason_code in reason_codes:
            if reason_code not in S2PGT03_ALLOWED_REASON_CODES:
                errors.append(f"route_records[{index}].reason_codes contains unsupported reason {reason_code}")
        if row["schema_migration_required"]:
            errors.append(f"route_records[{index}].schema_migration_required must be false")
        if row["production_affected"]:
            errors.append(f"route_records[{index}].production_affected must be false")
        rows.append(row)
    return rows, errors


def _s2pgt03_board_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return sorted({str(board).strip() for board in values if str(board or "").strip()})


def _s2pgt03_allowed_boards_for_source_domain(source_domain: str) -> set[str]:
    rules = S2PGT03_SOURCE_DOMAIN_BOARD_RULES.get(source_domain) or {}
    return {
        str(board)
        for group in ("primary", "conditional")
        for board in rules.get(group, ())
    }


def _s2pgt03_serializable_board_rules() -> dict[str, dict[str, list[str]]]:
    return {
        domain: {key: list(values) for key, values in rules.items()}
        for domain, rules in sorted(S2PGT03_SOURCE_DOMAIN_BOARD_RULES.items())
    }


def _s2pgt03_source_domain_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("source_domain")) for row in rows if row.get("source_domain")})
    blocking = [f"S2PGT03 missing source domain {domain}" for domain in S2PGT03_REQUIRED_SOURCE_DOMAINS if domain not in observed]
    return {"status": "pass" if not blocking else "blocked", "source_domains_observed": observed, "blocking_reasons": blocking}


def _s2pgt03_primary_board_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(board) for row in rows for board in (row.get("primary_boards") or [])})
    blocking = [f"S2PGT03 missing primary board {board}" for board in S2PGT03_REQUIRED_PRIMARY_BOARDS if board not in observed]
    return {"status": "pass" if not blocking else "blocked", "primary_boards_observed": observed, "blocking_reasons": blocking}


def _s2pgt03_cross_cutting_board_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(board) for row in rows for board in (row.get("cross_cutting_boards") or [])})
    blocking = [f"S2PGT03 missing cross-cutting board {board}" for board in S2PGT03_REQUIRED_CROSS_CUTTING_BOARDS if board not in observed]
    return {"status": "pass" if not blocking else "blocked", "cross_cutting_boards_observed": observed, "blocking_reasons": blocking}


def _s2pgt03_route_reason_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    if not rows:
        blocking.append("S2PGT03 requires at least one routing record")
    for index, row in enumerate(rows):
        for field in S2PGT03_REQUIRED_ROUTE_FIELDS:
            if row.get(field) in (None, "", []):
                blocking.append(f"routing_records[{index}].{field} is required")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt03_no_side_effect_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    for index, row in enumerate(rows):
        if row.get("schema_migration_required") is not False:
            blocking.append(f"routing_records[{index}].schema_migration_required must be false")
        if row.get("production_affected") is not False:
            blocking.append(f"routing_records[{index}].production_affected must be false")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt03_routing_state_hash(routes: Sequence[Mapping[str, Any]]) -> str:
    payload = {"routing_records": sorted([dict(route) for route in routes], key=lambda item: str(item.get("route_id") or ""))}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _s2pgt04_route_index(routes: Sequence[Any]) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for route in routes:
        if not isinstance(route, Mapping):
            continue
        route_id = str(route.get("route_id") or "").strip()
        if route_id:
            index[route_id] = route
    return index


def _s2pgt04_delta_rows(
    records: Sequence[Mapping[str, Any]],
    route_index: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    delta_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"delta_records[{index}] must be an object")
            continue
        route_id = str(record.get("route_id") or "").strip()
        route = route_index.get(route_id)
        source_domain = str(record.get("source_domain") or "").strip()
        source_id = str(record.get("source_id") or "").strip()
        delta_type = str(record.get("delta_type") or "").strip()
        resonance_group = str(record.get("resonance_group") or "").strip()
        support_status = str(record.get("support_status") or "").strip()
        evidence_refs = [str(ref) for ref in (record.get("evidence_refs") or []) if str(ref)]
        signal_strength, strength_error = _s2pgt04_signal_strength(record.get("signal_strength"))
        delta_id = str(record.get("delta_id") or f"delta:{route_id}:{delta_type}:{resonance_group}").strip()
        row = {
            "delta_id": delta_id,
            "source_domain": source_domain,
            "source_id": source_id,
            "route_id": route_id,
            "delta_type": delta_type,
            "resonance_group": resonance_group,
            "support_status": support_status,
            "signal_strength": signal_strength,
            "delta_explanation": str(record.get("delta_explanation") or "").strip(),
            "evidence_refs": evidence_refs,
            "route_primary_boards": list((route or {}).get("primary_boards") or []),
            "route_cross_cutting_boards": list((route or {}).get("cross_cutting_boards") or []),
            "schema_migration_required": record.get("schema_migration_required") is True,
            "production_affected": record.get("production_affected") is True,
            "email_frontstage_changed": record.get("email_frontstage_changed") is True,
        }
        for field in S2PGT04_REQUIRED_DELTA_FIELDS:
            if row.get(field) in (None, "", []):
                errors.append(f"delta_records[{index}].{field} is required")
        if strength_error:
            errors.append(f"delta_records[{index}].signal_strength must be between 0 and 1")
        if delta_id in delta_ids:
            errors.append(f"delta_records[{index}].delta_id must be unique")
        delta_ids.add(delta_id)
        if route_id and route_id not in route_index:
            errors.append(f"delta_records[{index}].route_id must reference an S2PGT03 route_id")
        if route:
            if source_id != route.get("source_id"):
                errors.append(f"delta_records[{index}].source_id must match route source_id")
            if source_domain != route.get("source_domain"):
                errors.append(f"delta_records[{index}].source_domain must match route source_domain")
        if delta_type and delta_type not in S2PGT04_REQUIRED_DELTA_TYPES:
            errors.append(f"delta_records[{index}].delta_type is not supported")
        if resonance_group and resonance_group not in S2PGT04_REQUIRED_RESONANCE_GROUPS:
            errors.append(f"delta_records[{index}].resonance_group is not supported")
        if support_status and support_status not in S2PGT04_ALLOWED_SUPPORT_STATUSES:
            errors.append(f"delta_records[{index}].support_status is not supported")
        if row["schema_migration_required"]:
            errors.append(f"delta_records[{index}].schema_migration_required must be false")
        if row["production_affected"]:
            errors.append(f"delta_records[{index}].production_affected must be false")
        if row["email_frontstage_changed"]:
            errors.append(f"delta_records[{index}].email_frontstage_changed must be false")
        rows.append(row)
    return rows, errors


def _s2pgt04_signal_strength(value: Any) -> tuple[float | None, bool]:
    if isinstance(value, bool):
        return None, True
    try:
        strength = float(value)
    except (TypeError, ValueError):
        return None, True
    if not 0 <= strength <= 1:
        return strength, True
    return round(strength, 4), False


def _s2pgt04_upstream_routing_gate(
    routing_report: Mapping[str, Any],
    routing_errors: Sequence[str],
) -> dict[str, Any]:
    blocking = [f"S2PGT03: {error}" for error in routing_errors]
    if routing_report.get("status") != "pass":
        blocking.append("S2PGT04 requires passing S2PGT03 source-board routing evidence")
    if routing_report.get("s2pgt03_source_board_routing_ready") is not True:
        blocking.append("S2PGT04 requires s2pgt03_source_board_routing_ready=true")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt04_delta_type_coverage_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("delta_type")) for row in rows if row.get("delta_type")})
    blocking = [f"S2PGT04 missing delta type {delta_type}" for delta_type in S2PGT04_REQUIRED_DELTA_TYPES if delta_type not in observed]
    return {"status": "pass" if not blocking else "blocked", "delta_types_observed": observed, "blocking_reasons": blocking}


def _s2pgt04_support_refute_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("support_status")) for row in rows if row.get("support_status")})
    blocking: list[str] = []
    for required in ("supported", "refuted"):
        if required not in observed:
            blocking.append(f"S2PGT04 missing support_status {required}")
    return {"status": "pass" if not blocking else "blocked", "support_statuses_observed": observed, "blocking_reasons": blocking}


def _s2pgt04_resonance_group_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("resonance_group")) for row in rows if row.get("resonance_group")})
    blocking = [f"S2PGT04 missing resonance group {group}" for group in S2PGT04_REQUIRED_RESONANCE_GROUPS if group not in observed]
    return {"status": "pass" if not blocking else "blocked", "resonance_groups_observed": observed, "blocking_reasons": blocking}


def _s2pgt04_delta_reason_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    if not rows:
        blocking.append("S2PGT04 requires at least one delta record")
    for index, row in enumerate(rows):
        for field in S2PGT04_REQUIRED_DELTA_FIELDS:
            if row.get(field) in (None, "", []):
                blocking.append(f"delta_records[{index}].{field} is required")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt04_no_side_effect_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    for index, row in enumerate(rows):
        if row.get("schema_migration_required") is not False:
            blocking.append(f"delta_records[{index}].schema_migration_required must be false")
        if row.get("production_affected") is not False:
            blocking.append(f"delta_records[{index}].production_affected must be false")
        if row.get("email_frontstage_changed") is not False:
            blocking.append(f"delta_records[{index}].email_frontstage_changed must be false")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt04_resonance_links(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for row in rows:
        group = str(row.get("resonance_group") or "")
        delta_id = str(row.get("delta_id") or "")
        if group and delta_id:
            grouped.setdefault(group, []).append(delta_id)
    return [
        {"resonance_group": group, "delta_ids": sorted(delta_ids), "delta_count": len(delta_ids)}
        for group, delta_ids in sorted(grouped.items())
    ]


def _s2pgt04_resonance_state_hash(deltas: Sequence[Mapping[str, Any]]) -> str:
    payload = {"delta_records": sorted([dict(delta) for delta in deltas], key=lambda item: str(item.get("delta_id") or ""))}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _s2pgt05_delta_index(deltas: Sequence[Any]) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for delta in deltas:
        if not isinstance(delta, Mapping):
            continue
        delta_id = str(delta.get("delta_id") or "").strip()
        if delta_id:
            index[delta_id] = delta
    return index


def _s2pgt05_candidate_rows(
    records: Sequence[Mapping[str, Any]],
    delta_index: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    candidate_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"queue_candidate_records[{index}] must be an object")
            continue
        delta_id = str(record.get("delta_id") or "").strip()
        delta = delta_index.get(delta_id)
        board_id = str(record.get("board_id") or "").strip()
        source_domain = str(record.get("source_domain") or "").strip()
        source_id = str(record.get("source_id") or "").strip()
        raw_score, raw_error = _s2pgt05_bounded_float(record.get("raw_score"), 0.0, 100.0)
        waiting_days, waiting_error = _s2pgt05_waiting_days(record.get("waiting_days"))
        evidence_refs = [str(ref) for ref in (record.get("evidence_refs") or []) if str(ref)]
        candidate_id = str(record.get("candidate_id") or f"candidate:{delta_id}:{board_id}").strip()
        row = {
            "candidate_id": candidate_id,
            "delta_id": delta_id,
            "board_id": board_id,
            "source_domain": source_domain,
            "source_id": source_id,
            "raw_score": raw_score,
            "waiting_days": waiting_days,
            "evidence_refs": evidence_refs,
            "candidate_explanation": str(record.get("candidate_explanation") or "").strip(),
            "signal_strength": float((delta or {}).get("signal_strength") or 0.0),
            "support_status": str((delta or {}).get("support_status") or ""),
            "schema_migration_required": record.get("schema_migration_required") is True,
            "public_schema_changed": record.get("public_schema_changed") is True,
            "queue_mutation_allowed": record.get("queue_mutation_allowed") is True,
            "ranking_algorithm_changed": record.get("ranking_algorithm_changed") is True,
            "production_affected": record.get("production_affected") is True,
            "email_frontstage_changed": record.get("email_frontstage_changed") is True,
        }
        for field in S2PGT05_REQUIRED_CANDIDATE_FIELDS:
            if row.get(field) in (None, "", []):
                errors.append(f"queue_candidate_records[{index}].{field} is required")
        if candidate_id in candidate_ids:
            errors.append(f"queue_candidate_records[{index}].candidate_id must be unique")
        candidate_ids.add(candidate_id)
        if delta_id and delta_id not in delta_index:
            errors.append(f"queue_candidate_records[{index}].delta_id must reference an S2PGT04 delta_id")
        if delta:
            if source_id != delta.get("source_id"):
                errors.append(f"queue_candidate_records[{index}].source_id must match delta source_id")
            if source_domain != delta.get("source_domain"):
                errors.append(f"queue_candidate_records[{index}].source_domain must match delta source_domain")
        if board_id and board_id not in S2PGT05_REQUIRED_BOARD_IDS:
            errors.append(f"queue_candidate_records[{index}].board_id is not supported")
        if source_domain and source_domain not in S2PGT05_REQUIRED_SOURCE_DOMAINS:
            errors.append(f"queue_candidate_records[{index}].source_domain is not supported")
        if raw_error:
            errors.append(f"queue_candidate_records[{index}].raw_score must be between 0 and 100")
        if waiting_error:
            errors.append(f"queue_candidate_records[{index}].waiting_days must be an integer between 0 and {S2PGT05_MAX_WAITING_DAYS}")
        for flag in (
            "schema_migration_required",
            "public_schema_changed",
            "queue_mutation_allowed",
            "ranking_algorithm_changed",
            "production_affected",
            "email_frontstage_changed",
        ):
            if row[flag]:
                errors.append(f"queue_candidate_records[{index}].{flag} must be false")
        rows.append(row)
    return rows, errors


def _s2pgt05_bounded_float(value: Any, minimum: float, maximum: float) -> tuple[float, bool]:
    if isinstance(value, bool):
        return 0.0, True
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0, True
    if not minimum <= parsed <= maximum:
        return parsed, True
    return round(parsed, 6), False


def _s2pgt05_waiting_days(value: Any) -> tuple[int, bool]:
    if isinstance(value, bool):
        return 0, True
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0, True
    if parsed < 0 or parsed > S2PGT05_MAX_WAITING_DAYS:
        return parsed, True
    return parsed, False


def _s2pgt05_calibrated_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_board: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        by_board.setdefault(str(row.get("board_id") or ""), []).append(row)
    percentile_by_candidate: dict[str, float] = {}
    for board_rows in by_board.values():
        ordered = sorted(
            board_rows,
            key=lambda item: (float(item.get("raw_score") or 0.0), str(item.get("candidate_id") or "")),
        )
        denominator = max(len(ordered) - 1, 1)
        for rank, item in enumerate(ordered):
            percentile_by_candidate[str(item.get("candidate_id") or "")] = 1.0 if len(ordered) == 1 else round(rank / denominator, 6)
    calibrated: list[dict[str, Any]] = []
    for row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        percentile = percentile_by_candidate.get(candidate_id, 0.0)
        waiting_credit = round((int(row.get("waiting_days") or 0) / S2PGT05_MAX_WAITING_DAYS) * S2PGT05_MAX_WAITING_CREDIT, 6)
        signal_strength = float(row.get("signal_strength") or 0.0)
        support_penalty = 0.08 if row.get("support_status") == "refuted" else 0.0
        calibrated_score = round((0.65 * percentile) + (0.20 * signal_strength) + waiting_credit - support_penalty, 6)
        calibrated.append(
            {
                **dict(row),
                "percentile_score": percentile,
                "waiting_credit": waiting_credit,
                "support_penalty": support_penalty,
                "calibrated_score": calibrated_score,
            }
        )
    return calibrated


def _s2pgt05_queue_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda item: (
            -float(item.get("calibrated_score") or 0.0),
            str(item.get("source_domain") or ""),
            str(item.get("board_id") or ""),
            str(item.get("candidate_id") or ""),
        ),
    )
    max_per_source = max(1, int(S2PGT05_SELECTED_COUNT * S2PGT05_MAX_SOURCE_SHARE))
    selected_ids: set[str] = set()
    source_counts: dict[str, int] = {}
    rows_with_decisions: list[dict[str, Any]] = []
    cap_blocked_ids: set[str] = set()
    for item in ordered:
        source_domain = str(item.get("source_domain") or "")
        candidate_id = str(item.get("candidate_id") or "")
        if len(selected_ids) < S2PGT05_SELECTED_COUNT and source_counts.get(source_domain, 0) < max_per_source:
            selected_ids.add(candidate_id)
            source_counts[source_domain] = source_counts.get(source_domain, 0) + 1
        elif source_counts.get(source_domain, 0) >= max_per_source:
            cap_blocked_ids.add(candidate_id)
    queued_remaining = S2PGT05_WAITLIST_COUNT
    for rank, item in enumerate(ordered, start=1):
        row = dict(item)
        candidate_id = str(row.get("candidate_id") or "")
        if candidate_id in selected_ids:
            row["queue_decision"] = "selected"
            row["queue_reason_code"] = "selected_after_percentile_waiting_and_balance"
            row["queue_reason"] = "Selected after board-percentile calibration, waiting credit, signal strength, and source-balance cap."
        elif candidate_id in cap_blocked_ids:
            row["queue_decision"] = "deferred"
            row["queue_reason_code"] = "deferred_source_balance_cap"
            row["queue_reason"] = "Deferred because selecting it would exceed the per-source selected share cap."
        elif queued_remaining > 0:
            row["queue_decision"] = "queued"
            row["queue_reason_code"] = "queued_next_best_calibrated"
            row["queue_reason"] = "Queued as the next best calibrated candidate after selected slots were filled."
            queued_remaining -= 1
        else:
            row["queue_decision"] = "deferred"
            row["queue_reason_code"] = "deferred_below_selected_and_waitlist"
            row["queue_reason"] = "Deferred because selected and waitlist slots were filled by higher calibrated candidates."
        row["calibrated_rank"] = rank
        rows_with_decisions.append(row)
    return rows_with_decisions


def _s2pgt05_upstream_delta_gate(
    delta_resonance_report: Mapping[str, Any],
    delta_errors: Sequence[str],
) -> dict[str, Any]:
    blocking = [f"S2PGT04: {error}" for error in delta_errors]
    if delta_resonance_report.get("status") != "pass":
        blocking.append("S2PGT05 requires passing S2PGT04 delta resonance evidence")
    if delta_resonance_report.get("s2pgt04_delta_resonance_ready") is not True:
        blocking.append("S2PGT05 requires s2pgt04_delta_resonance_ready=true")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt05_percentile_calibration_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("board_id") or "") for row in rows if row.get("board_id")})
    blocking = [f"S2PGT05 missing board {board}" for board in S2PGT05_REQUIRED_BOARD_IDS if board not in observed]
    for index, row in enumerate(rows):
        percentile = row.get("percentile_score")
        if not isinstance(percentile, (int, float)) or isinstance(percentile, bool) or not 0 <= float(percentile) <= 1:
            blocking.append(f"calibrated_queue_records[{index}].percentile_score must be between 0 and 1")
    return {"status": "pass" if not blocking else "blocked", "board_ids_observed": observed, "blocking_reasons": blocking}


def _s2pgt05_source_balance_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("source_domain") or "") for row in rows if row.get("source_domain")})
    blocking = [f"S2PGT05 missing source domain {domain}" for domain in S2PGT05_REQUIRED_SOURCE_DOMAINS if domain not in observed]
    selected = [row for row in rows if row.get("queue_decision") == "selected"]
    counts: dict[str, int] = {}
    for row in selected:
        domain = str(row.get("source_domain") or "")
        counts[domain] = counts.get(domain, 0) + 1
    shares = {
        domain: round(count / max(len(selected), 1), 6)
        for domain, count in sorted(counts.items())
    }
    for domain, share in shares.items():
        if share > S2PGT05_MAX_SOURCE_SHARE:
            blocking.append(f"S2PGT05 selected source share for {domain} exceeds {S2PGT05_MAX_SOURCE_SHARE}")
    if len(selected) != S2PGT05_SELECTED_COUNT:
        blocking.append(f"S2PGT05 selected queue count must be {S2PGT05_SELECTED_COUNT}")
    return {
        "status": "pass" if not blocking else "blocked",
        "source_domains_observed": observed,
        "selected_source_counts": dict(sorted(counts.items())),
        "source_share_by_domain": shares,
        "blocking_reasons": blocking,
    }


def _s2pgt05_waiting_credit_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    for index, row in enumerate(rows):
        waiting_days = row.get("waiting_days")
        waiting_credit = row.get("waiting_credit")
        if not isinstance(waiting_days, int) or isinstance(waiting_days, bool) or not 0 <= waiting_days <= S2PGT05_MAX_WAITING_DAYS:
            blocking.append(f"calibrated_queue_records[{index}].waiting_days must be 0..{S2PGT05_MAX_WAITING_DAYS}")
        if not isinstance(waiting_credit, (int, float)) or isinstance(waiting_credit, bool) or not 0 <= float(waiting_credit) <= S2PGT05_MAX_WAITING_CREDIT:
            blocking.append(f"calibrated_queue_records[{index}].waiting_credit must be 0..{S2PGT05_MAX_WAITING_CREDIT}")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt05_queue_reason_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = sorted({str(row.get("queue_decision") or "") for row in rows if row.get("queue_decision")})
    blocking = [f"S2PGT05 missing queue decision {decision}" for decision in S2PGT05_REQUIRED_DECISIONS if decision not in observed]
    if not rows:
        blocking.append("S2PGT05 requires at least one calibrated queue record")
    for index, row in enumerate(rows):
        if not row.get("queue_reason_code"):
            blocking.append(f"calibrated_queue_records[{index}].queue_reason_code is required")
        if not row.get("queue_reason"):
            blocking.append(f"calibrated_queue_records[{index}].queue_reason is required")
    return {"status": "pass" if not blocking else "blocked", "queue_decisions_observed": observed, "blocking_reasons": blocking}


def _s2pgt05_deterministic_order_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ranks = [row.get("calibrated_rank") for row in rows if isinstance(row, Mapping)]
    expected = list(range(1, len(rows) + 1))
    blocking: list[str] = []
    if ranks != expected:
        blocking.append("S2PGT05 calibrated ranks must be deterministic and contiguous")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt05_no_side_effect_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blocking: list[str] = []
    for index, row in enumerate(rows):
        for flag in (
            "schema_migration_required",
            "public_schema_changed",
            "queue_mutation_allowed",
            "ranking_algorithm_changed",
            "production_affected",
            "email_frontstage_changed",
        ):
            if row.get(flag) is not False:
                blocking.append(f"calibrated_queue_records[{index}].{flag} must be false")
    return {"status": "pass" if not blocking else "blocked", "blocking_reasons": blocking}


def _s2pgt05_queue_state_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = {"calibrated_queue_records": sorted([dict(row) for row in rows], key=lambda item: str(item.get("candidate_id") or ""))}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _s2pit01_default_control_entries() -> list[dict[str, Any]]:
    common_paths = list(S2PIT01_REQUIRED_USER_CENTER_PATHS)
    return [
        {
            "domain_id": "profile",
            "label_zh": "画像与目标",
            "click_path": ["用户中心", "画像与目标"],
            "editable_fact_source": S2PIT01_EDITABLE_FACT_SOURCE,
            "compiled_config_path": S2PIT01_EDITABLE_FACT_SOURCE,
            "config_sections": ["project", "cost_policy", "intelligence_provider", "validation"],
            "user_center_paths": common_paths,
            "generated_view_paths": ["docs/owner/OWNER_CONSOLE.md"],
            "generated_view_editable": False,
        },
        {
            "domain_id": "mail_review",
            "label_zh": "邮件与复习",
            "click_path": ["用户中心", "邮件与复习"],
            "editable_fact_source": S2PIT01_EDITABLE_FACT_SOURCE,
            "compiled_config_path": S2PIT01_EDITABLE_FACT_SOURCE,
            "config_sections": ["email", "outputs", "iteration"],
            "user_center_paths": common_paths,
            "generated_view_paths": ["docs/owner/OWNER_CONSOLE.md", "docs/owner/CONTENT_LEDGER.csv"],
            "generated_view_editable": False,
        },
        {
            "domain_id": "source_boards",
            "label_zh": "来源与板块",
            "click_path": ["用户中心", "来源与板块"],
            "editable_fact_source": S2PIT01_EDITABLE_FACT_SOURCE,
            "compiled_config_path": S2PIT01_EDITABLE_FACT_SOURCE,
            "config_sections": ["sources", "boards", "source_defaults"],
            "user_center_paths": common_paths,
            "generated_view_paths": ["docs/owner/SOURCE_CATALOG.md"],
            "generated_view_editable": False,
        },
        {
            "domain_id": "budget_schedule",
            "label_zh": "预算与调度",
            "click_path": ["用户中心", "预算与调度"],
            "editable_fact_source": S2PIT01_EDITABLE_FACT_SOURCE,
            "compiled_config_path": S2PIT01_EDITABLE_FACT_SOURCE,
            "config_sections": ["runtime", "queue", "scoring", "validation"],
            "user_center_paths": common_paths,
            "generated_view_paths": ["docs/owner/MODEL_AND_QUEUE.md"],
            "generated_view_editable": False,
        },
    ]


def _s2pit01_control_rows(entries: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_domains: set[str] = set()
    for index, entry in enumerate(entries):
        domain_id = str(entry.get("domain_id") or "")
        label_zh = str(entry.get("label_zh") or "")
        click_path = [str(item) for item in entry.get("click_path") or []]
        config_sections = [str(item) for item in entry.get("config_sections") or []]
        user_center_paths = [str(item) for item in entry.get("user_center_paths") or []]
        generated_view_paths = [str(item) for item in entry.get("generated_view_paths") or []]
        if not domain_id:
            errors.append(f"control_entries[{index}].domain_id is required")
        if domain_id in seen_domains:
            errors.append(f"control_entries[{index}].domain_id must be unique")
        seen_domains.add(domain_id)
        if domain_id and domain_id not in S2PIT01_REQUIRED_CONTROL_DOMAINS:
            errors.append(f"control_entries[{index}].domain_id is not supported")
        if not label_zh:
            errors.append(f"control_entries[{index}].label_zh is required")
        if not click_path:
            errors.append(f"control_entries[{index}].click_path is required")
        if not config_sections:
            errors.append(f"control_entries[{index}].config_sections is required")
        rows.append(
            {
                "domain_id": domain_id,
                "label_zh": label_zh,
                "click_path": click_path,
                "click_depth": len(click_path),
                "editable_fact_source": str(entry.get("editable_fact_source") or ""),
                "compiled_config_path": str(entry.get("compiled_config_path") or ""),
                "config_sections": config_sections,
                "user_center_paths": user_center_paths,
                "generated_view_paths": generated_view_paths,
                "generated_view_editable": bool(entry.get("generated_view_editable")),
                "production_affected": bool(entry.get("production_affected")),
                "real_smtp_sent": bool(entry.get("real_smtp_sent")),
                "scheduler_enabled": bool(entry.get("scheduler_enabled")),
                "schema_migration_allowed": bool(entry.get("schema_migration_allowed")),
                "public_schema_changed": bool(entry.get("public_schema_changed")),
                "queue_mutation_allowed": bool(entry.get("queue_mutation_allowed")),
                "v7_2_contract_files_changed": bool(entry.get("v7_2_contract_files_changed")),
            }
        )
    return rows, errors


def _s2pit01_no_side_effect_errors(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows):
        for field in (
            "production_affected",
            "real_smtp_sent",
            "scheduler_enabled",
            "schema_migration_allowed",
            "public_schema_changed",
            "queue_mutation_allowed",
            "v7_2_contract_files_changed",
        ):
            if row.get(field) is True:
                errors.append(f"control_entries[{index}].{field} must be false for S2PIT01")
    return errors


def _is_iso_date(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        Date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _top_journal_profiles_from_batches(
    source_batches: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    profiles: list[dict[str, Any]] = []
    relation_edges: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []
    errors: list[str] = []
    for journal in S2PCT04_REQUIRED_JOURNALS:
        batch = source_batches.get(journal)
        if not isinstance(batch, Mapping):
            reason = f"{journal}: missing completed top-journal source batch for S2PCT04 profile modeling"
            source_reports.append({"journal": journal, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        batch_errors = validate_top_journal_source_batch(batch)
        blocked = bool(batch_errors or batch.get("status") == "blocked")
        source_reports.append(
            {
                "journal": journal,
                "status": "blocked" if blocked else "pass",
                "source_item_count": len(batch.get("source_items") or []),
                "new_item_count": int(batch.get("new_item_count") or 0),
                "blocking_reasons": batch_errors or list(batch.get("blocking_reasons") or []),
            }
        )
        if blocked:
            errors.extend(f"{journal}: {reason}" for reason in (batch_errors or batch.get("blocking_reasons") or []))
            continue
        for source_item in batch.get("source_items") or []:
            if not isinstance(source_item, Mapping):
                continue
            profile, edge, profile_errors = _top_journal_profile_from_source_item(source_item, generated_at=generated_at)
            errors.extend(profile_errors)
            if profile_errors:
                continue
            profiles.append(profile)
            relation_edges.append(edge)
    return profiles, relation_edges, source_reports, errors


def _top_journal_profile_from_source_item(
    source_item: Mapping[str, Any],
    *,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    metadata = source_item.get("metadata") if isinstance(source_item.get("metadata"), Mapping) else {}
    top_journal = metadata.get("top_journal") if isinstance(metadata.get("top_journal"), Mapping) else {}
    if not isinstance(top_journal, Mapping) or not top_journal:
        return {}, {}, [f"{source_item.get('source_id', 'source')}: top_journal metadata missing"]
    canonical_id = _canonical_document_id(source_item)
    source_id = str(source_item.get("source_id") or canonical_id)
    article_type = str(top_journal.get("article_type") or "")
    profile_kind = _top_journal_profile_kind(article_type)
    if not profile_kind:
        errors.append(f"{source_id}: unsupported top-journal profile article_type {article_type!r}")
    journal = str(top_journal.get("journal_id") or "")
    if journal not in S2PCT04_REQUIRED_JOURNALS:
        errors.append(f"{source_id}: journal must be one of {list(S2PCT04_REQUIRED_JOURNALS)}")
    profile = {
        "profile_id": f"profile:{canonical_id}",
        "source_id": source_id,
        "canonical_document_id": canonical_id,
        "journal": journal,
        "journal_display": str(top_journal.get("journal") or journal),
        "title": str(source_item.get("title") or ""),
        "article_type": article_type,
        "article_type_raw": str(top_journal.get("article_type_raw") or article_type),
        "profile_kind": profile_kind,
        "profile_role": _top_journal_profile_role(profile_kind),
        "publication_status": "active",
        "generated_at": generated_at,
        "metadata_only": True,
        "production_eligible": False,
        "evidence_refs": list(source_item.get("evidence_refs") or []),
    }
    relation = {
        "edge_id": f"relation:{canonical_id}:original-publication",
        "relation_type": "original_publication",
        "source_canonical_document_id": canonical_id,
        "target_canonical_document_id": canonical_id,
        "target_required": False,
        "event_type": "original_publication",
        "metadata_only": True,
        "evidence_refs": list(source_item.get("evidence_refs") or []),
    }
    return profile, relation, errors


def _top_journal_profiles_from_publication_events(
    publication_events: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
    known_targets: set[str],
    prior_index: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    profiles: list[dict[str, Any]] = []
    relation_edges: list[dict[str, Any]] = []
    forced_updates: list[dict[str, Any]] = []
    event_reports: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, event in enumerate(publication_events):
        if not isinstance(event, Mapping):
            reason = f"publication_events[{index}] must be an object"
            event_reports.append({"index": index, "status": "blocked", "blocking_reasons": [reason]})
            errors.append(reason)
            continue
        profile, edge, profile_errors = _top_journal_profile_from_publication_event(
            event,
            generated_at=generated_at,
            known_targets=known_targets,
        )
        event_reports.append(
            {
                "event_id": str(event.get("event_id") or event.get("source_id") or f"publication-event-{index}"),
                "status": "blocked" if profile_errors else "pass",
                "profile_kind": profile.get("profile_kind", ""),
                "relation_type": edge.get("relation_type", ""),
                "blocking_reasons": profile_errors,
            }
        )
        errors.extend(profile_errors)
        if profile_errors:
            continue
        profiles.append(profile)
        relation_edges.append(edge)
        if profile.get("profile_kind") in S2PCT04_FORCED_EVENT_TYPES:
            forced_updates.append(_forced_event_update_from_profile(profile, prior_index=prior_index))
    return profiles, relation_edges, forced_updates, event_reports, errors


def _top_journal_profile_from_publication_event(
    event: Mapping[str, Any],
    *,
    generated_at: str,
    known_targets: set[str],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    event_id = str(event.get("event_id") or event.get("source_id") or "")
    source_id = str(event.get("source_id") or event_id)
    canonical_id = str(event.get("canonical_document_id") or source_id)
    journal = str(event.get("journal") or "")
    title = str(event.get("title") or "")
    article_type = str(event.get("article_type") or event.get("event_type") or event.get("profile_kind") or "")
    profile_kind = _top_journal_profile_kind(article_type)
    target_id = str(event.get("target_canonical_document_id") or "")
    relation_type = str(event.get("relation_type") or _default_relation_type(profile_kind))
    target_required = relation_type != "original_publication" or profile_kind in S2PCT04_FORCED_EVENT_TYPES
    if not event_id:
        errors.append("publication event requires event_id or source_id")
    if journal not in S2PCT04_REQUIRED_JOURNALS:
        errors.append(f"{event_id or source_id}: journal must be one of {list(S2PCT04_REQUIRED_JOURNALS)}")
    if not canonical_id:
        errors.append(f"{event_id or source_id}: canonical_document_id is required")
    if not title:
        errors.append(f"{event_id or source_id}: title is required")
    if not profile_kind:
        errors.append(f"{event_id or source_id}: unsupported publication event article_type {article_type!r}")
    if target_required and not target_id:
        errors.append(f"{event_id or source_id}: target_canonical_document_id is required for {relation_type}")
    if target_id and target_id not in known_targets:
        errors.append(f"{event_id or source_id}: target_canonical_document_id is unknown: {target_id}")
    profile = {
        "profile_id": f"profile:{canonical_id}",
        "event_id": event_id,
        "source_id": source_id,
        "canonical_document_id": canonical_id,
        "target_canonical_document_id": target_id,
        "journal": journal,
        "journal_display": str(event.get("journal_display") or journal.title()),
        "title": title,
        "article_type": _profile_token(article_type),
        "article_type_raw": article_type,
        "profile_kind": profile_kind,
        "profile_role": _top_journal_profile_role(profile_kind),
        "publication_status": profile_kind if profile_kind in S2PCT04_FORCED_EVENT_TYPES else "active",
        "generated_at": generated_at,
        "observed_at": str(event.get("observed_at") or generated_at),
        "metadata_only": True,
        "production_eligible": False,
        "evidence_refs": list(event.get("evidence_refs") or []),
    }
    edge = {
        "edge_id": f"relation:{canonical_id}:{relation_type}:{target_id or canonical_id}",
        "event_id": event_id,
        "relation_type": relation_type,
        "source_canonical_document_id": canonical_id,
        "target_canonical_document_id": target_id or canonical_id,
        "target_required": target_required,
        "event_type": profile_kind,
        "metadata_only": True,
        "evidence_refs": list(event.get("evidence_refs") or []),
    }
    return profile, edge, errors


def _top_journal_profile_kind(article_type: str) -> str:
    token = _profile_token(article_type)
    if token in {"research", "research_article", "research_article_feed_item", "report", "article", "articles"}:
        return "research"
    if token in {"review", "seminar", "series", "commission", "commissions", "clinical_rounds"}:
        return "review"
    if token in {"editorial", "commentary", "opinion", "perspective", "perspectives", "viewpoint", "viewpoints"}:
        return "editorial"
    if token in {"news", "news_feature", "news_and_views", "news_analysis"}:
        return "news"
    if token in {"correction", "corrigendum", "erratum", "addendum"}:
        return "correction"
    if token in {"retraction", "retracted", "withdrawal", "withdrawn"}:
        return "retraction"
    return ""


def _top_journal_profile_role(profile_kind: str) -> str:
    return {
        "research": "primary_evidence_candidate",
        "review": "synthesis_context_candidate",
        "editorial": "opinion_or_context_not_primary_evidence",
        "news": "secondary_news_context_not_primary_evidence",
        "correction": "forced_revision_event",
        "retraction": "forced_invalidation_event",
    }.get(profile_kind, "unknown")


def _default_relation_type(profile_kind: str) -> str:
    if profile_kind == "correction":
        return "corrects"
    if profile_kind == "retraction":
        return "retracts"
    if profile_kind in {"editorial", "news"}:
        return "discusses"
    return "original_publication"


def _prior_profile_state_index(prior_profile_state: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not isinstance(prior_profile_state, Mapping):
        return {}
    raw_items: list[Any] = []
    if isinstance(prior_profile_state.get("items"), list):
        raw_items = list(prior_profile_state["items"])
    elif prior_profile_state.get("canonical_document_id"):
        raw_items = [prior_profile_state]
    else:
        raw_items = [value for value in prior_profile_state.values() if isinstance(value, Mapping)]
    index: dict[str, Mapping[str, Any]] = {}
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        canonical_id = str(item.get("canonical_document_id") or item.get("source_id") or "")
        if canonical_id:
            index[canonical_id] = item
    return index


def _forced_event_update_from_profile(profile: Mapping[str, Any], *, prior_index: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    event_type = str(profile.get("profile_kind") or "")
    target_id = str(profile.get("target_canonical_document_id") or "")
    prior = prior_index.get(target_id, {})
    invalidating = event_type == "retraction"
    return {
        "update_id": f"forced-update:{event_type}:{_safe_id(target_id)}:{_safe_id(str(profile.get('event_id') or profile.get('source_id') or 'event'))}",
        "model_id": S2PCT04_JOURNAL_PROFILE_MODEL_ID,
        "acceptance_id": S2PCT04_ACCEPTANCE_ID,
        "task_id": S2PCT04_TASK_ID,
        "legacy_task_id": S2PCT04_LEGACY_TASK_ID,
        "event_id": str(profile.get("event_id") or profile.get("source_id") or ""),
        "event_type": event_type,
        "event_canonical_document_id": str(profile.get("canonical_document_id") or ""),
        "target_canonical_document_id": target_id,
        "prior_conclusion_state": str(prior.get("conclusion_state") or prior.get("publication_status") or "active_or_unknown"),
        "updated_conclusion_state": "invalidated" if invalidating else "requires_revision",
        "publication_status": "retracted" if invalidating else "corrected",
        "forced_review_required": True,
        "allowed_action": "remove_or_mark_invalid_before_reuse" if invalidating else "revise_existing_summary_before_reuse",
        "metadata_only": True,
        "generated_at": str(profile.get("generated_at") or ""),
    }


def _publication_relation_errors(profiles: Sequence[Mapping[str, Any]], relation_edges: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    edge_sources = {str(edge.get("source_canonical_document_id") or "") for edge in relation_edges if isinstance(edge, Mapping)}
    for profile in profiles:
        canonical_id = str(profile.get("canonical_document_id") or "")
        if canonical_id and canonical_id not in edge_sources:
            errors.append(f"{canonical_id}: missing publication relation edge")
    for edge in relation_edges:
        if not isinstance(edge, Mapping):
            errors.append("publication relation edge must be an object")
            continue
        if not edge.get("relation_type"):
            errors.append("publication relation edge missing relation_type")
        if edge.get("target_required") is True and not edge.get("target_canonical_document_id"):
            errors.append(f"{edge.get('edge_id', 'relation')}: missing required target_canonical_document_id")
        if edge.get("metadata_only") is not True:
            errors.append(f"{edge.get('edge_id', 'relation')}: relation edge must be metadata_only")
    return errors


def _forced_event_update_errors(
    event_profiles: Sequence[Mapping[str, Any]],
    forced_updates: Sequence[Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    update_keys = {
        (str(update.get("event_type") or ""), str(update.get("target_canonical_document_id") or ""))
        for update in forced_updates
        if isinstance(update, Mapping)
    }
    for profile in event_profiles:
        profile_kind = str(profile.get("profile_kind") or "")
        if profile_kind not in S2PCT04_FORCED_EVENT_TYPES:
            continue
        target_id = str(profile.get("target_canonical_document_id") or "")
        if not target_id:
            errors.append(f"{profile.get('event_id', 'forced-event')}: forced event target missing")
            continue
        if (profile_kind, target_id) not in update_keys:
            errors.append(f"{profile.get('event_id', 'forced-event')}: forced event update not generated")
    return errors


def _forced_event_kinds(updates: Sequence[Mapping[str, Any]]) -> set[str]:
    return {str(update.get("event_type") or "") for update in updates if isinstance(update, Mapping) and update.get("event_type")}


def _duplicate_values(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _profile_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _replay_gate(report: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(report, Mapping):
        return {"status": "blocked", "blocking_reasons": ["S2P1 replay gate missing 30-day terminal replay report"]}
    reasons: list[str] = []
    if report.get("status") != "pass":
        reasons.append("S2P1 replay report is not pass")
    if int(report.get("unique_date_count") or 0) < S2P1_REPLAY_REQUIRED_DATES:
        reasons.append("S2P1 replay requires 30 unique dates")
    if int(report.get("future_leakage_count") or 0) != 0:
        reasons.append("S2P1 replay future_leakage_count must be 0")
    if int(report.get("duplicate_selected_count") or 0) != 0:
        reasons.append("S2P1 replay duplicate_selected_count must be 0")
    if int(report.get("p0_p1_blocker_count") or 0) != 0:
        reasons.append("S2P1 replay P0/P1 blockers must be 0")
    return {"status": "pass" if not reasons else "blocked", "blocking_reasons": reasons}


def _shadow_gate(report: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(report, Mapping):
        return {"status": "blocked", "blocking_reasons": ["S2P1 shadow gate missing 48h shadow report"]}
    reasons: list[str] = []
    if report.get("status") != "pass":
        reasons.append("S2P1 shadow report is not pass")
    if float(report.get("shadow_hours") or 0.0) < S2P1_SHADOW_REQUIRED_HOURS:
        reasons.append("S2P1 shadow requires at least 48 hours")
    if report.get("formal_production_inclusion") is not False:
        reasons.append("S2P1 shadow must not include formal production inclusion")
    if report.get("production_affected") is not False:
        reasons.append("S2P1 shadow must not affect accepted arXiv production")
    return {"status": "pass" if not reasons else "blocked", "blocking_reasons": reasons}


def _license_gate_errors(batch: Mapping[str, Any]) -> list[str]:
    errors = []
    for item in batch.get("source_items") or []:
        if not isinstance(item, Mapping):
            continue
        license_status = str((item.get("license") or {}).get("status") if isinstance(item.get("license"), Mapping) else "")
        if not license_status or license_status == "unknown":
            errors.append(f"{item.get('source_id', 'preprint')}: license metadata missing")
    return errors


def _version_gate_errors(batch: Mapping[str, Any]) -> list[str]:
    errors = []
    for item in batch.get("source_items") or []:
        if not isinstance(item, Mapping):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
        preprint = metadata.get("preprint") if isinstance(metadata.get("preprint"), Mapping) else {}
        if not preprint.get("version"):
            errors.append(f"{item.get('source_id', 'preprint')}: version metadata missing")
    return errors


def _canonical_ids(batch: Mapping[str, Any]) -> list[str]:
    return [_canonical_document_id(item) for item in batch.get("source_items") or [] if isinstance(item, Mapping)]


def _canonical_document_id(item: Mapping[str, Any]) -> str:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
    identity = metadata.get("identity") if isinstance(metadata.get("identity"), Mapping) else {}
    return str(identity.get("canonical_document_id") or item.get("source_id") or "")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-") or "unknown"
