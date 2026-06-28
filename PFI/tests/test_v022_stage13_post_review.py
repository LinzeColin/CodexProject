from __future__ import annotations

from pathlib import Path

from pfi_v02.stage_v022_database_governance import (
    V022_STAGE13_TASK_IDS,
    build_v022_stage13_contract,
    load_v022_parameter_catalog,
)
from pfi_v02.stage_v022_post_review import (
    STAGE13_DOWNLOADS_CLEANUP_CANDIDATES,
    STAGE13_OWNER_TRIGGER,
    STAGE13_REVIEW_SCOPE_FILES,
    build_stage13_post_review_payload,
)


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_stage13_contract_matches_triggered_roadmap_scope() -> None:
    contract = build_v022_stage13_contract()

    assert contract["stage"] == "Stage 13"
    assert contract["stage_name_zh"] == "后置触发型复核"
    assert contract["task_ids"] == V022_STAGE13_TASK_IDS
    assert contract["phases"]["Phase 13.1"] == (
        "触发型 Codex / LLM 复核",
        "S13-P1-T1",
        "S13-P1-T2",
        "S13-P1-T3",
    )
    assert contract["trigger_condition"] == STAGE13_OWNER_TRIGGER
    assert contract["review_scope_files"] == STAGE13_REVIEW_SCOPE_FILES
    assert contract["full_repo_scan_allowed"] is False
    assert contract["network_allowed"] is False
    assert "无触发条件时不得生成 Codex Review Ticket。" in contract["stop_conditions"]


def test_stage13_payload_generates_scoped_owner_specified_ticket() -> None:
    payload = build_stage13_post_review_payload(load_v022_parameter_catalog())

    assert payload["schema"] == "PFIV022Stage13PostReviewPayloadV1"
    assert payload["trigger_condition"] == STAGE13_OWNER_TRIGGER
    assert payload["ticket"]["path"] == "PFI/review_queue/codex_review_stage13_owner_specified_20260628.md"
    assert payload["ticket"]["created"] is True
    assert payload["ticket"]["scope_files"] == STAGE13_REVIEW_SCOPE_FILES
    assert payload["ticket"]["full_repo_scan_allowed"] is False
    assert payload["ticket"]["network_allowed"] is False
    assert payload["ticket"]["external_llm_allowed"] is False
    assert payload["review_result"]["development_record_updated"] is True
    assert payload["review_result"]["blocking_issue_count"] == 0
    assert payload["stage13_ready_for_goal_closeout"] is True


def test_stage13_parameter_catalog_records_post_review_and_downloads_cleanup() -> None:
    catalog = load_v022_parameter_catalog()

    assert catalog["schema"] == "PFIParametersV022Stage13"
    assert catalog["current_stage"] == "Stage 13 - 后置触发型复核"
    assert catalog["stage13_task_ids"] == list(V022_STAGE13_TASK_IDS)
    post_review = catalog["parameters"]["post_review"]
    assert post_review["trigger_condition"]["value"] == STAGE13_OWNER_TRIGGER
    assert post_review["full_repo_scan_allowed"]["value"] is False
    assert post_review["network_allowed"]["value"] is False
    assert post_review["downloads_cleanup_archive"]["value"] == "PFI/docs/pfi_v022/downloads_cleanup/PFI_V022_PRE_CANONICAL_SYNC_ARCHIVE_20260628.tar.gz"
    assert post_review["downloads_cleanup_candidates"]["value"] == list(STAGE13_DOWNLOADS_CLEANUP_CANDIDATES)


def test_stage13_docs_ticket_and_summary_are_chinese_and_traceable() -> None:
    docs = (
        "docs/pfi_v022/STAGE13_POST_REVIEW.md",
        "review_queue/codex_review_stage13_owner_specified_20260628.md",
        "docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md",
        "reports/pfi_v022_summary.md",
        "docs/pfi_v022/ROADMAP_LOCK.md",
        "模型参数文件.md",
        "功能清单.md",
        "开发记录.md",
        "HANDOFF.md",
        "README.md",
    )
    required_terms = (
        "Stage 13 - 后置触发型复核",
        "S13-P1-T1",
        "S13-P1-T2",
        "S13-P1-T3",
        "交付前人工指定",
        "Codex Review Ticket",
        "禁止全仓无差别扫描",
        "仅对异常区域进行复核",
        "问题、修复、验证、剩余风险",
        "Downloads 污染文件夹",
        "PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028",
    )
    for path in docs:
        text = read_text(path)
        for term in required_terms:
            assert term in text, f"{path} missing {term}"


def test_stage13_downloads_cleanup_removed_only_pfi_temp_dirs_and_kept_sources() -> None:
    archive = ROOT / "docs" / "pfi_v022" / "downloads_cleanup" / "PFI_V022_PRE_CANONICAL_SYNC_ARCHIVE_20260628.tar.gz"
    manifest = read_text("docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md")

    assert archive.exists()
    assert archive.stat().st_size > 0
    for candidate in STAGE13_DOWNLOADS_CLEANUP_CANDIDATES:
        assert not (DOWNLOADS / candidate).exists(), f"{candidate} should have been removed from Downloads"
        assert candidate in manifest

    assert (DOWNLOADS / "PFI.app").exists()
    assert (DOWNLOADS / "PFI_v0.2.2_Codex_Task_Pack_zh.md").exists()
    assert (DOWNLOADS / "PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md").exists()
