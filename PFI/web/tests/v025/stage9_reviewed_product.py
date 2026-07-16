#!/usr/bin/env python3
"""Generate the Stage 9 reviewed analysis snapshot and public UI data."""

from __future__ import annotations

import json
from pathlib import Path

from pfi_os.application.analysis.stage9_reviewed_analysis import (
    build_stage9_reviewed_analysis_pack,
    render_model_validation_report_html,
    validate_stage9_reviewed_analysis_pack,
)


PFI_ROOT = Path(__file__).resolve().parents[3]
OBSERVED_AT = "2026-07-15T17:30:00+10:00"
SNAPSHOT_PATH = PFI_ROOT / "config/reports/v025_stage9_reviewed_analysis_snapshot.json"
DATA_PATH = PFI_ROOT / "web/app/pages/reports/stage9AnalysisData.js"
MODEL_REPORT_PATH = PFI_ROOT / "reports/pfi_v025/stage_9/whole_stage_review/model_validation_report.html"


def _data_module(pack: dict[str, object]) -> str:
    payload = {
        "schema": "PFIV025Stage9ReviewedAnalysisEmbeddedDataV1",
        "packHash": pack["pack_hash"],
        "snapshotBinding": {
            "schema": "PFIV025Stage9ReviewedSnapshotBindingV1",
            "phaseId": pack["phase_id"],
            "observedAt": pack["observed_at"],
            "packHash": pack["pack_hash"],
            "snapshotPath": "PFI/config/reports/v025_stage9_reviewed_analysis_snapshot.json",
        },
        "uiContract": pack["ui_contract"],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "(function attachPFIV025Stage9ReviewedAnalysisData(root) {\n"
        f"  const data = {encoded};\n"
        "  if (typeof module !== \"undefined\" && module.exports) module.exports = data;\n"
        "  if (root) root.PFI_V025_STAGE9_REVIEWED_ANALYSIS_DATA = data;\n"
        "})(typeof window !== \"undefined\" ? window : globalThis);\n"
    )


def main() -> int:
    pack = build_stage9_reviewed_analysis_pack(PFI_ROOT, observed_at=OBSERVED_AT)
    gate = validate_stage9_reviewed_analysis_pack(pack, pfi_root=PFI_ROOT)
    if gate["status"] != "pass":
        raise RuntimeError("reviewed analysis failed: " + "; ".join(gate["errors"]))
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    DATA_PATH.write_text(_data_module(pack), encoding="utf-8")
    MODEL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_REPORT_PATH.write_text(render_model_validation_report_html(pack), encoding="utf-8")
    print(json.dumps({"status": "pass", "pack_hash": pack["pack_hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
