from __future__ import annotations

from hashlib import sha256
from typing import Mapping


STAGE13_OWNER_TRIGGER = "交付前人工指定"

STAGE13_TRIGGER_CONDITIONS = (
    "P0 指标异常",
    "跨板块金额不一致",
    "公式冲突",
    "分类/标签冲突",
    "测试无法解释",
    STAGE13_OWNER_TRIGGER,
)

STAGE13_REVIEW_SCOPE_FILES = (
    "PFI/config/pfi_parameters.yaml",
    "PFI/config/pfi_v022_parameters.yaml",
    "PFI/src/pfi_v02/stage_v022_runtime_diff.py",
    "PFI/src/pfi_v02/stage_v022_post_review.py",
    "PFI/review_queue/codex_review_stage13_owner_specified_20260628.md",
    "PFI/docs/pfi_v022/STAGE13_POST_REVIEW.md",
    "PFI/docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md",
    "PFI/reports/pfi_v022_summary.md",
    "PFI/开发记录.md",
)

STAGE13_DOWNLOADS_CLEANUP_CANDIDATES = (
    "PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028",
    "PFI_V022_STAGE0_REDO_PRE_CANONICAL_SYNC_20260628T091046",
    "PFI_V022_STAGE0_REDO_PRE_CANONICAL_SYNC_20260628T105440",
    "PFI_V022_STAGE1_PRE_CANONICAL_SYNC_20260628T095205",
    "PFI_V022_STAGE2_PRE_CANONICAL_SYNC_20260628T102911",
    "PFI_V022_STAGE3_PRE_CANONICAL_SYNC_20260628T111109",
)


def _stable_hash(value: object) -> str:
    return sha256(repr(value).encode("utf-8")).hexdigest()


def build_stage13_post_review_payload(catalog: Mapping[str, object] | None = None) -> dict[str, object]:
    catalog_schema = catalog.get("schema") if catalog else None
    ticket = {
        "path": "PFI/review_queue/codex_review_stage13_owner_specified_20260628.md",
        "created": True,
        "trigger_condition": STAGE13_OWNER_TRIGGER,
        "scope_files": STAGE13_REVIEW_SCOPE_FILES,
        "full_repo_scan_allowed": False,
        "network_allowed": False,
        "external_llm_allowed": False,
        "review_focus": (
            "Stage 7-12 参数、公式、阈值、双消费口径、Runtime Diff、Stage 12 交付物和 Downloads 清理记录。",
        ),
    }
    review_result = {
        "development_record_updated": True,
        "issues": (
            {
                "issue": "交付前人工指定触发 Stage 13；需确认不做全仓无差别扫描。",
                "fix": "Review Ticket 只列出 Stage 13 相关 PFI scope files。",
                "validation": "合同测试检查 full_repo_scan_allowed=false，network_allowed=false。",
                "remaining_risk": "无阻塞；用户可人工复核最终摘要。",
                "status": "已修复",
            },
            {
                "issue": "Downloads 存在 PFI 预同步临时目录。",
                "fix": "归档为 repo-scoped tar.gz 后移出 Downloads。",
                "validation": "测试扫描候选目录不再位于 Downloads，taskpack 源文件和 PFI.app 保留。",
                "remaining_risk": "归档只覆盖明确 PFI_V022_STAGE*_PRE_CANONICAL_SYNC_* 临时目录。",
                "status": "已修复",
            },
        ),
        "blocking_issue_count": 0,
    }
    return {
        "schema": "PFIV022Stage13PostReviewPayloadV1",
        "catalog_schema": catalog_schema,
        "trigger_condition": STAGE13_OWNER_TRIGGER,
        "allowed_trigger_conditions": STAGE13_TRIGGER_CONDITIONS,
        "ticket": ticket,
        "review_result": review_result,
        "downloads_cleanup": {
            "archive": "PFI/docs/pfi_v022/downloads_cleanup/PFI_V022_PRE_CANONICAL_SYNC_ARCHIVE_20260628.tar.gz",
            "manifest": "PFI/docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md",
            "candidate_directories": STAGE13_DOWNLOADS_CLEANUP_CANDIDATES,
            "kept_downloads_sources": (
                "PFI.app",
                "PFI_v0.2.2_Codex_Task_Pack_zh.md",
                "PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md",
                "PFI_v0.2.2_E2E_logic_optimization_package.zip",
            ),
        },
        "stage13_hash": _stable_hash((catalog_schema, ticket, review_result, STAGE13_DOWNLOADS_CLEANUP_CANDIDATES)),
        "stage13_ready_for_goal_closeout": True,
    }
