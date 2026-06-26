"""PFI V0.2 contracts.

The package is intentionally small in Stage 1: it defines product and domain
contracts that later implementation stages can share without moving the legacy
QBVS runtime under ``PFI/大数据模拟器``.
"""

from pfi_v02.stage1_ia import (
    PRIMARY_ENTRIES,
    Stage1Entry,
    build_stage1_ia_contract,
    primary_entry_labels,
)
from pfi_v02.core_models import build_stage1_model_contract, default_stage1_sources
from pfi_v02.classification_rules import ClassificationInput, ClassificationResult, classify_transaction

__all__ = [
    "ClassificationInput",
    "ClassificationResult",
    "PRIMARY_ENTRIES",
    "Stage1Entry",
    "build_stage1_model_contract",
    "build_stage1_ia_contract",
    "classify_transaction",
    "default_stage1_sources",
    "primary_entry_labels",
]
