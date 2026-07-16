#!/usr/bin/env python3
"""Generate deterministic Phase 9.3 product snapshot and embedded web assets."""

from __future__ import annotations

import json
from pathlib import Path

from pfi_os.application.decisions.decision_review import (
    assemble_phase93_decision_pack,
    build_phase93_core,
    export_assets_base64,
    render_phase93_exports,
    validate_phase93_decision_pack,
)


PFI_ROOT = Path(__file__).resolve().parents[3]
OBSERVED_AT = "2026-07-15T17:30:00+10:00"
SNAPSHOT_PATH = PFI_ROOT / "config/reports/v025_phase93_decision_snapshot.json"
DATA_PATH = PFI_ROOT / "web/app/pages/reports/stage9DecisionReviewData.js"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _data_module(pack: dict[str, object], exports: dict[str, bytes]) -> str:
    payload = {
        "schema": "PFIV025Stage9Phase93EmbeddedDataV1",
        "packHash": pack["pack_hash"],
        "uiContract": pack["ui_contract"],
        "assetsBase64": export_assets_base64(exports),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "(function attachPFIV025Stage9Phase93Data(root) {\n"
        f"  const data = {encoded};\n"
        "  if (typeof module !== \"undefined\" && module.exports) module.exports = data;\n"
        "  if (root) root.PFI_V025_STAGE9_PHASE93_DATA = data;\n"
        "})(typeof window !== \"undefined\" ? window : globalThis);\n"
    )


def main() -> int:
    core = build_phase93_core(PFI_ROOT, observed_at=OBSERVED_AT)
    exports = render_phase93_exports(core["export_snapshot"])
    pack = assemble_phase93_decision_pack(core, exports)
    gate = validate_phase93_decision_pack(
        pack, pfi_root=PFI_ROOT, expected_exports=exports
    )
    if gate["status"] != "pass":
        raise RuntimeError("generated Phase 9.3 pack failed: " + "; ".join(gate["errors"]))
    _write_json(SNAPSHOT_PATH, pack)
    DATA_PATH.write_text(_data_module(pack, exports), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": gate["status"],
                "pack_hash": pack["pack_hash"],
                "export_snapshot_hash": pack["export_snapshot_hash"],
                "decision_count": pack["decision_count"],
                "export_format_count": gate["export_format_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
