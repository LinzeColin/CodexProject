"""PFI V0.2 contracts.

The package defines product, domain, data-source, import, and reconciliation
contracts. QBVS is a separate top-level system under ``CodexProject/QBVS``;
PFI keeps its own strategy backtesting, market-feel training, and simulator
surfaces without owning QBVS.
"""

from pfi_v02.stage1_ia import (
    PRIMARY_ENTRIES,
    Stage1Entry,
    build_stage1_ia_contract,
    primary_entry_labels,
)
from pfi_v02.core_models import build_stage1_model_contract, default_stage1_sources
from pfi_v02.classification_rules import ClassificationInput, ClassificationResult, classify_transaction
from pfi_v02.stage2_contracts import build_stage2_contract_summary
from pfi_v02.stage2_import import detect_watch_folder_files, parse_alipay_bill_bytes, parse_cba_csv_bytes
from pfi_v02.stage2_registry import build_stage2_registry, build_stage2_registry_contract
from pfi_v02.stage3_read_mvp import build_stage3_read_model, build_sync_all_plan, simple_status_language
from pfi_v02.stage4_analysis_mvp import build_stage4_analysis_model
from pfi_v02.stage5_advice_report_alpha import build_stage5_delivery_model
from pfi_v02.stage6_e2e_stabilization import build_stage6_e2e_stabilization_model
from pfi_v02.stage_v021_frontend_contract import build_v021_stage0_contract
from pfi_v02.stage_v022_runtime_diff import build_dependency_hash_snapshot, build_impacted_metrics_report

__all__ = [
    "ClassificationInput",
    "ClassificationResult",
    "PRIMARY_ENTRIES",
    "Stage1Entry",
    "build_stage1_model_contract",
    "build_stage1_ia_contract",
    "build_stage2_contract_summary",
    "build_stage2_registry",
    "build_stage2_registry_contract",
    "build_stage3_read_model",
    "build_stage4_analysis_model",
    "build_stage5_delivery_model",
    "build_stage6_e2e_stabilization_model",
    "build_v021_stage0_contract",
    "build_dependency_hash_snapshot",
    "build_impacted_metrics_report",
    "build_sync_all_plan",
    "classify_transaction",
    "default_stage1_sources",
    "detect_watch_folder_files",
    "parse_alipay_bill_bytes",
    "parse_cba_csv_bytes",
    "primary_entry_labels",
    "simple_status_language",
]
