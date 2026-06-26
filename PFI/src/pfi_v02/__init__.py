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

__all__ = [
    "PRIMARY_ENTRIES",
    "Stage1Entry",
    "build_stage1_ia_contract",
    "primary_entry_labels",
]
