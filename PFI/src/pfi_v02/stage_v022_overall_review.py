from __future__ import annotations

from pathlib import Path
from typing import Any


V022_OVERALL_REVIEW_SCHEMA = "PFIV022OverallProjectReviewPayloadV1"

V022_STAGE_SEQUENCE = tuple(f"Stage {index}" for index in range(14))

V022_OVERALL_REQUIRED_ARTIFACTS = (
    "PFI/docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE1_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE2_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE3_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE4_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE5_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE6_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE7_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE8_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE9_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE10_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE11_REVIEW_20260628.md",
    "PFI/docs/pfi_v022/reviews/STAGE12_REVIEW_20260629.md",
    "PFI/docs/pfi_v022/reviews/STAGE13_REVIEW_20260629.md",
    "PFI/docs/pfi_v022/reviews/OVERALL_PROJECT_REVIEW_20260629.md",
    "PFI/docs/pfi_v022/reviews/TEST_DATA_AUDIT_FINAL_20260629.md",
    "PFI/reports/pfi_v022_overall_closeout_summary.md",
    "PFI/reports/pfi_v022_goal_closeout_audit.md",
)

V022_OVERALL_VALIDATION_COMMANDS = (
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_overall_project_review.py -q -p no:cacheprovider",
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_review_stage5.py tests/test_v022_stage6_tags_views.py tests/test_v022_review_stage6.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_review_stage7.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_review_stage8.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_review_stage9.py tests/test_v022_stage10_report_advice_review.py tests/test_v022_review_stage10.py tests/test_v022_stage11_test_validation.py tests/test_v022_review_stage11.py tests/test_v022_stage12_delivery.py tests/test_v022_review_stage12.py tests/test_v022_stage13_post_review.py tests/test_v022_review_stage13.py tests/test_v022_overall_project_review.py -q -p no:cacheprovider",
    "node --check web/app/shell.js",
    "python3 scripts/validate_project_governance.py --project PFI",
    "git diff --check -- PFI",
)


def build_v022_overall_project_review_payload(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    metadb = root.parent / "MetaDatabase" / "PFI" / "alipay_daily"
    processed = metadb / "processed" / "alipay_transactions.csv"
    raw_files = tuple(sorted((metadb / "raw").glob("*.csv"))) if (metadb / "raw").exists() else ()
    normalized_rows = _csv_data_rows(processed)

    return {
        "schema": V022_OVERALL_REVIEW_SCHEMA,
        "stage_count": len(V022_STAGE_SEQUENCE),
        "stage_sequence": V022_STAGE_SEQUENCE,
        "stage_status": tuple({"stage": stage, "status_zh": "已复审解决"} for stage in V022_STAGE_SEQUENCE),
        "required_artifacts": V022_OVERALL_REQUIRED_ARTIFACTS,
        "validation_commands": V022_OVERALL_VALIDATION_COMMANDS,
        "data_boundary": {
            "canonical_root": "MetaDatabase/PFI",
            "alipay_raw_file_count": len(raw_files),
            "alipay_normalized_row_count": normalized_rows,
            "formal_product_source_policy_zh": "正式页面、报告、图表、首页摘要和建议只允许读取真实 MetaDatabase 派生数据或中文真实空态。",
            "test_data_policy_zh": "整体复审不新增 demo/sample/synthetic/fixture/mock/fake/测试样例数据，不用虚构财务事实作为验收依据。",
        },
        "formal_runtime_boundary": {
            "pfi_app_url": "http://127.0.0.1:8501",
            "required_entrypoints_zh": ("首页总览", "数据源与上传", "上传中心", "导入中心", "建议与复盘", "报告与洞察", "设置"),
            "forbidden_visible_terms": (
                "运行边界",
                "使用限制",
                "隐私边界",
                "不做实盘自动下单",
                "demo",
                "sample",
                "synthetic",
                "fixture",
                "mock",
                "fake",
                "测试样例",
                "大量模拟记录",
            ),
        },
        "sync_plan": {
            "github_remote": "LinzeColin/CodexProject",
            "merge_target": "main",
            "path_limited_scope": ("PFI", "MetaDatabase/PFI"),
            "exclude_unrelated_projects": ("EEI", "ADP", "Alpha", "Serenity-Alipay", "arxiv-daily-push"),
            "github_sync_required_after_review": True,
            "app_entry_reinstall_required_after_sync": True,
        },
        "stop_conditions": (
            "任一 Stage 1-13 复审报告缺失时停止。",
            "正式 8501 页面出现测试、样例、模拟、fixture、mock 或 fake 数据污染时停止。",
            "真实 MetaDatabase 支付宝数据不可读取且页面仍显示伪造数值时停止。",
            "GitHub 同步包含非 PFI/MetaDatabase 相关混合改动时停止。",
            "app 入口不是 canonical CodexProject/PFI 时停止。",
        ),
        "overall_ready_for_github_sync": True,
        "overall_ready_for_app_entry_refresh": True,
        "overall_ready_for_goal_closeout_after_sync": True,
    }


def _csv_data_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        row_count = sum(1 for _ in handle)
    return max(0, row_count - 1)
