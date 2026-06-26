from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "qbvs-quantlab-handshake-v1"
SYSTEM_NAME = "quant_behavior_validation_system"


def create_handshake_bundle(output_dir: Path | str, quantlab_root: Path | str | None = None) -> dict[str, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    qbvs_root = str(Path(__file__).resolve().parents[1])
    request = {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": "handshake_request",
        "source_system": SYSTEM_NAME,
        "target_system": "quantlab",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "qbvs_root": qbvs_root,
        "quantlab_root_hint": str(quantlab_root) if quantlab_root else "",
        "same_instruction_relay": {
            "user_instruction_cn": "写一个独立验证系统的handoff.md，并且和量化系统通话握手，做到和量化系统完全互通，我在他那边会发送完全一模一样的指令",
            "quantlab_expected_action": "Read this handshake request, read HANDOFF.md and QUANTLAB_INTEGRATION_CONTRACT.json, then write handoff/quantlab_handshake_ack.json without modifying QuantLab source or database unless the user explicitly approves it.",
            "qbvs_expected_action_after_ack": "Verify the returned ack with qbvs.cli verify-handshake, then rerun goal-readiness audit with --handshake-ack.",
        },
        "read_only_boundary": {
            "qbvs_imports_quantlab": False,
            "qbvs_writes_quantlab_source": False,
            "qbvs_writes_quantlab_database": False,
            "quantlab_consumes_qbvs_artifacts": True,
        },
        "required_quantlab_actions": [
            "Read HANDOFF.md.",
            "Read QUANTLAB_INTEGRATION_CONTRACT.json.",
            "Read HANDSHAKE_PROTOCOL.json.",
            "Optionally use handoff/quantlab_readonly_adapter_pack for read-only ingestion.",
            "Confirm which QuantLab command, page, or service will consume QBVS artifacts.",
            "Return quantlab_handshake_ack.json using the ack template.",
        ],
        "latest_recommended_artifacts": [
            "handoff/quantlab_bundle_yahoo_public_top20_finalist_200symbols_5windows",
            "handoff/promotion_candidates_yahoo_public_top20_finalist_200symbols_5windows.csv",
            "runs/yahoo_public_top20_finalist_200symbols_5windows_exact/strategy_summary.csv",
            "runs/yahoo_public_top20_finalist_200symbols_5windows_exact/validation_results.csv",
            "data_cache_moomoo_batch10/cache_index.csv",
            "runs/manifests/moomoo_batch10_top20_finalist_3windows_manifest.csv",
            "runs/moomoo_batch10_top20_finalist_3windows_exact/strategy_summary.csv",
            "runs/moomoo_batch10_top20_finalist_3windows_exact/validation_results.csv",
            "handoff/quantlab_bundle_moomoo_batch10_top20_finalist_3windows",
            "handoff/promotion_candidates_moomoo_batch10_top20_finalist_3windows.csv",
            "config/moomoo_batch30_cache_index.csv",
            "runs/manifests/moomoo_batch30_top20_finalist_3windows_manifest.csv",
            "runs/moomoo_batch30_top20_finalist_3windows_exact/strategy_summary.csv",
            "runs/moomoo_batch30_top20_finalist_3windows_exact/validation_results.csv",
            "handoff/quantlab_bundle_moomoo_batch30_top20_finalist_3windows",
            "handoff/promotion_candidates_moomoo_batch30_top20_finalist_3windows.csv",
            "config/moomoo_batch80_cache_index.csv",
            "runs/manifests/moomoo_batch80_top20_finalist_3windows_manifest.csv",
            "runs/moomoo_batch80_top20_finalist_3windows_exact/strategy_summary.csv",
            "runs/moomoo_batch80_top20_finalist_3windows_exact/validation_results.csv",
            "handoff/quantlab_bundle_moomoo_batch80_top20_finalist_3windows",
            "handoff/promotion_candidates_moomoo_batch80_top20_finalist_3windows.csv",
            "config/moomoo_batch100_cache_index.csv",
            "runs/manifests/moomoo_batch100_top20_finalist_3windows_manifest.csv",
            "runs/moomoo_batch100_top20_finalist_3windows_exact/strategy_summary.csv",
            "runs/moomoo_batch100_top20_finalist_3windows_exact/validation_results.csv",
            "handoff/quantlab_bundle_moomoo_batch100_top20_finalist_3windows",
            "handoff/promotion_candidates_moomoo_batch100_top20_finalist_3windows.csv",
        ],
        "qbvs_artifacts_for_quantlab": [
            "QUANTLAB_INTEGRATION_CONTRACT.json",
            "HANDOFF.md",
            "HANDSHAKE_PROTOCOL.json",
            "handoff/quantlab_readonly_adapter_pack/*",
            "data_cache/cache_index.csv",
            "runs/**/strategy_summary.csv",
            "runs/**/validation_results.csv",
            "runs/**/task_status.csv",
            "runs/**/Behavior_Strategy_*.pdf",
            "handoff/**/quantlab_bundle_manifest.json",
            "handoff/**/quantlab_ingestion_payload.json",
            "handoff/**/quantlab_candidate_strategies.csv",
        ],
        "accepted_ack_file": "quantlab_handshake_ack.json",
        "accepted_ack_path": str(root / "quantlab_handshake_ack.json"),
    }
    ack_template = {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": "handshake_ack",
        "source_system": "quantlab",
        "target_system": SYSTEM_NAME,
        "created_at": "",
        "quantlab_root": str(quantlab_root) if quantlab_root else "",
        "accepted": False,
        "consume_mode": "external_artifact_read",
        "accepted_artifacts": [],
        "quantlab_entrypoint": "",
        "quantlab_can_read_qbvs_root": False,
        "quantlab_will_not_write_qbvs_without_user_approval": True,
        "quantlab_will_not_write_strategy_library_without_user_approval": True,
        "notes": "",
        "blockers": [],
    }
    request_path = root / "qbvs_handshake_request.json"
    ack_path = root / "quantlab_handshake_ack_template.json"
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    ack_path.write_text(json.dumps(ack_template, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"request": request_path, "ack_template": ack_path}


def verify_handshake_ack(path: Path | str) -> dict[str, Any]:
    ack_path = Path(path)
    payload = json.loads(ack_path.read_text(encoding="utf-8"))
    required = {
        "protocol_version",
        "message_type",
        "source_system",
        "target_system",
        "accepted",
        "consume_mode",
        "quantlab_entrypoint",
    }
    missing = sorted(required - set(payload))
    errors = []
    if missing:
        errors.append(f"missing fields: {missing}")
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        errors.append("protocol_version mismatch")
    if payload.get("message_type") != "handshake_ack":
        errors.append("message_type must be handshake_ack")
    if payload.get("source_system") != "quantlab":
        errors.append("source_system must be quantlab")
    if payload.get("target_system") != SYSTEM_NAME:
        errors.append(f"target_system must be {SYSTEM_NAME}")
    if payload.get("accepted") is not True:
        errors.append("accepted must be true")
    if not payload.get("quantlab_entrypoint"):
        errors.append("quantlab_entrypoint must be provided")
    return {
        "path": str(ack_path),
        "valid": not errors,
        "errors": errors,
        "payload": payload,
    }
