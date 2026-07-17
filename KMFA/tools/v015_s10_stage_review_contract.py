#!/usr/bin/env python3
"""KMFA v1.5 S10 整体复审的跨部分安全衔接合同。

本模块只使用公开合成数据，补齐三个阶段内衔接缺口：
1. 任何文件适配都必须精确绑定 S10-P1 的安全检查和人工确认；
2. 未来自动入口只能生成待检查的交接信封，不能绕过 P1/P2；
3. 定时检查失败或无数据时不得误记导入成功，且始终保留手工导入。
"""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from KMFA.tools import v015_s10_p1_general_import as p1
from KMFA.tools import v015_s10_p2_source_adapters as p2
from KMFA.tools import v015_s10_p3_automatic_ingestion_reserve as p3


RUN_PHASE_ID = "V015_S10_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S10-STAGE-REVIEW-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S10-STAGE-REVIEW"
VERSION = "1.5.0-dev-s10-review"

FILE_BINDING_SCHEMA = "kmfa.v015.s10_stage_review.file_binding.v1"
CONNECTOR_ENVELOPE_SCHEMA = "kmfa.v015.s10_stage_review.connector_envelope.v1"
SCHEDULE_OUTCOME_SCHEMA = "kmfa.v015.s10_stage_review.schedule_outcome.v1"

# P3 使用平台名称，P2 使用适配器名称。这里只允许这五个明确映射。
CONNECTOR_TO_ADAPTER = {
    "REDCIRCLE": "REDCIRCLE",
    "KINGDEE": "KINGDEE",
    "WPS": "WPS",
    "BANK": "BANK",
    "TAX": "TAX_EINVOICE",
}


class StageReviewError(RuntimeError):
    """稳定、默认拒绝的 S10 跨部分错误。"""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StageReviewError("MAPPING_REQUIRED", f"{field} 必须是字段映射。")
    return copy.deepcopy(dict(value))


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageReviewError("TEXT_REQUIRED", f"{field} 不能为空。")
    return value.strip()


def _fingerprint(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def adapter_source_for_connector(connector_source_id: str) -> str:
    """把 P3 的平台名转换成唯一的 P2 适配器名。"""

    try:
        return CONNECTOR_TO_ADAPTER[connector_source_id]
    except KeyError as error:
        raise StageReviewError("CONNECTOR_SOURCE_UNMAPPED", "自动来源没有唯一的文件适配器映射。") from error


def _checked_preview_and_confirmation(
    preview: Mapping[str, Any], confirmation: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        checked_preview = p1._validate_preview(preview)
        checked_confirmation = p1._validate_confirmation(confirmation, checked_preview)
    except p1.GeneralImportError as error:
        raise StageReviewError("P1_CONFIRMATION_CHAIN_INVALID", "文件检查或人工确认不是当前有效版本。") from error
    return checked_preview, checked_confirmation


def bind_confirmed_file_adaptation(
    *,
    inspection: Mapping[str, Any],
    preview: Mapping[str, Any],
    confirmation: Mapping[str, Any],
    adaptation: Mapping[str, Any],
    source_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """只允许精确确认过的 P1 文件进入对应的 P2 适配结果。"""

    checked_inspection = _mapping(inspection, "inspection")
    checked_preview, checked_confirmation = _checked_preview_and_confirmation(preview, confirmation)
    checked_adaptation = _mapping(adaptation, "adaptation")
    binding = _mapping(source_binding, "source_binding")

    if checked_inspection.get("inspection_status") != "SAFE_TO_PREVIEW":
        raise StageReviewError("P1_SAFE_INSPECTION_REQUIRED", "文件未通过 S10-P1 安全检查。")
    if checked_preview.get("inspection_fingerprint") != checked_inspection.get("inspection_fingerprint"):
        raise StageReviewError("INSPECTION_PREVIEW_BINDING_MISMATCH", "预览不是由当前文件检查结果生成。")
    if checked_preview.get("file_hash") != checked_inspection.get("file_hash"):
        raise StageReviewError("FILE_HASH_BINDING_MISMATCH", "文件 hash 在检查与预览之间发生变化。")
    if checked_adaptation.get("file_hash") != checked_preview.get("file_hash"):
        raise StageReviewError("ADAPTATION_FILE_HASH_MISMATCH", "适配结果不是来自已确认的同一文件。")

    source_id = _text(binding.get("source_id"), "source_binding.source_id")
    adapter_source = _text(binding.get("adapter_source"), "source_binding.adapter_source")
    entity_id = _text(binding.get("entity_id"), "source_binding.entity_id")
    entity_label = _text(binding.get("entity_label"), "source_binding.entity_label")
    if checked_preview.get("source_id", {}).get("value") != source_id:
        raise StageReviewError("SOURCE_ID_BINDING_MISMATCH", "适配来源与人工确认的来源编号不一致。")
    if checked_preview.get("entity_label", {}).get("value") != entity_label:
        raise StageReviewError("ENTITY_LABEL_BINDING_MISMATCH", "适配主体与人工确认的主体不一致。")
    if checked_adaptation.get("source_system") != adapter_source:
        raise StageReviewError("ADAPTER_SOURCE_BINDING_MISMATCH", "文件被送入了错误的来源适配器。")

    period = checked_preview.get("period", {}).get("value")
    sheets = list(checked_adaptation.get("adapted_sheets") or [])
    records = list(checked_adaptation.get("records") or [])
    if not sheets or not records or checked_adaptation.get("adaptation_status") != "READY":
        raise StageReviewError("READY_ADAPTATION_REQUIRED", "存在隔离项或没有可用记录，不能继续。")
    if any(row.get("period") != period or row.get("entity_id") != entity_id for row in sheets):
        raise StageReviewError("PERIOD_ENTITY_BINDING_MISMATCH", "期间或主体在预览与适配之间发生变化。")
    if any(row.get("period") != period or row.get("entity_id") != entity_id for row in records):
        raise StageReviewError("RECORD_CONTEXT_BINDING_MISMATCH", "适配记录未继承已确认的期间和主体。")
    template_pairs = sorted({(row.get("template_id"), row.get("mapping_version")) for row in sheets})
    if any(not template_id or not mapping_version for template_id, mapping_version in template_pairs):
        raise StageReviewError("TEMPLATE_VERSION_BINDING_MISSING", "模板和字段版本必须完整保留。")

    body = {
        "schema_version": FILE_BINDING_SCHEMA,
        "inspection_fingerprint": checked_inspection["inspection_fingerprint"],
        "preview_fingerprint": checked_preview["preview_fingerprint"],
        "confirmation_fingerprint": checked_confirmation["event_fingerprint"],
        "source_id": source_id,
        "adapter_source": adapter_source,
        "file_display_name": checked_preview["file_display_name"],
        "file_hash": checked_preview["file_hash"],
        "period": period,
        "entity_id": entity_id,
        "entity_label": entity_label,
        "template_versions": [
            {"template_id": template_id, "mapping_version": mapping_version}
            for template_id, mapping_version in template_pairs
        ],
        "adapted_record_count": len(records),
        "processing_chain": ["S10-P1-SAFE-INSPECTION", "S10-P1-EXPLICIT-CONFIRMATION", "S10-P2-VERSIONED-ADAPTER"],
        "confirmation_bypass_allowed": False,
        "raw_root_access_count": 0,
        "live_connector_call_count": 0,
        "business_execution_performed": False,
    }
    body["binding_fingerprint"] = _fingerprint(body)
    return body


def build_connector_handoff_envelope(
    *,
    session: p3.ConnectorSession,
    requested_at: datetime,
    payload: bytes,
    declared_hash: str,
    cursor: int,
    idempotency_key: str,
    file_display_name: str,
    period: str,
    entity_id: str,
    entity_label: str,
    source_id: str,
    template_id: str,
    mapping_version: str,
) -> dict[str, Any]:
    """未来自动入口只能生成待 P1/P2 处理的离线交接信封。"""

    try:
        plan = p3.pull_manifest_plan(session, requested_at=requested_at)
        p3.verify_hash(payload, declared_hash)
    except p3.ConnectorContractError as error:
        raise StageReviewError("P3_CONNECTOR_CONTRACT_INVALID", "自动入口未通过授权、撤销或 hash 检查。") from error
    adapter_source = adapter_source_for_connector(session.source_id)
    try:
        template = p2.TEMPLATE_BY_ID[template_id]
    except KeyError as error:
        raise StageReviewError("TEMPLATE_NOT_REGISTERED", "自动入口引用了未登记的文件模板。") from error
    if template.source_system != adapter_source:
        raise StageReviewError("CONNECTOR_TEMPLATE_SOURCE_MISMATCH", "自动来源与文件模板不属于同一平台。")
    if template.mapping_version != mapping_version:
        raise StageReviewError("CONNECTOR_MAPPING_VERSION_MISMATCH", "自动入口必须使用已登记的明确字段版本。")
    if not isinstance(cursor, int) or isinstance(cursor, bool) or cursor <= session.last_cursor:
        raise StageReviewError("CONNECTOR_CURSOR_INVALID", "自动入口游标必须前进。")
    if not idempotency_key or len(idempotency_key) > 128:
        raise StageReviewError("CONNECTOR_IDEMPOTENCY_KEY_INVALID", "自动入口幂等编号无效。")
    body = {
        "schema_version": CONNECTOR_ENVELOPE_SCHEMA,
        "authorization_id": session.authorization_id,
        "connector_source": session.source_id,
        "adapter_source": adapter_source,
        "source_id": _text(source_id, "source_id"),
        "file_display_name": _text(file_display_name, "file_display_name"),
        "file_hash": declared_hash,
        "period": _text(period, "period"),
        "entity_id": _text(entity_id, "entity_id"),
        "entity_label": _text(entity_label, "entity_label"),
        "template_id": template_id,
        "mapping_version": mapping_version,
        "cursor": cursor,
        "idempotency_key": idempotency_key,
        "requested_at": plan["requested_at"],
        "handoff_status": "AWAITING_S10_P1_INSPECTION_CONFIRMATION_AND_S10_P2_ADAPTATION",
        "importable": False,
        "checkpoint_advanced": False,
        "required_processing_chain": ["S10-P1", "S10-P2", "PRIVATE-ATOMIC-COMMIT"],
        "network_call_performed": False,
        "live_connector_call_count": 0,
        "raw_root_access_count": 0,
        "credential_read_count": 0,
        "source_mutation_performed": False,
    }
    body["envelope_fingerprint"] = _fingerprint(body)
    return body


def authorize_connector_file_commit(
    *, envelope: Mapping[str, Any], file_binding: Mapping[str, Any]
) -> dict[str, Any]:
    """只有自动信封与完整 P1/P2 绑定一致时，才可进入私有原子提交。"""

    checked_envelope = _mapping(envelope, "envelope")
    supplied_envelope = checked_envelope.pop("envelope_fingerprint", None)
    if supplied_envelope != _fingerprint(checked_envelope):
        raise StageReviewError("CONNECTOR_ENVELOPE_TAMPERED", "自动入口交接信封已被改写。")
    checked_binding = _mapping(file_binding, "file_binding")
    supplied_binding = checked_binding.pop("binding_fingerprint", None)
    if supplied_binding != _fingerprint(checked_binding):
        raise StageReviewError("FILE_BINDING_TAMPERED", "文件检查、确认或适配绑定已被改写。")
    exact = {
        "adapter_source": "adapter_source",
        "source_id": "source_id",
        "file_display_name": "file_display_name",
        "file_hash": "file_hash",
        "period": "period",
        "entity_id": "entity_id",
        "entity_label": "entity_label",
    }
    if any(checked_envelope[left] != checked_binding[right] for left, right in exact.items()):
        raise StageReviewError("CONNECTOR_FILE_BINDING_MISMATCH", "自动信封与人工确认文件不是同一份数据。")
    expected_template = {
        "template_id": checked_envelope["template_id"],
        "mapping_version": checked_envelope["mapping_version"],
    }
    if expected_template not in checked_binding.get("template_versions", []):
        raise StageReviewError("CONNECTOR_TEMPLATE_BINDING_MISMATCH", "自动信封与实际适配模板版本不一致。")
    return {
        "schema_version": "kmfa.v015.s10_stage_review.connector_commit_authorization.v1",
        "envelope_fingerprint": supplied_envelope,
        "file_binding_fingerprint": supplied_binding,
        "authorization_status": "READY_FOR_PRIVATE_ATOMIC_COMMIT",
        "import_success_recorded": False,
        "checkpoint_advanced": False,
        "manual_confirmation_verified": True,
        "raw_root_access_count": 0,
        "live_connector_call_count": 0,
        "business_execution_performed": False,
    }


def scheduled_check_outcome(*, source_id: str, attempt: int, outcome: str) -> dict[str, Any]:
    """把定时检查与真正导入分开，防止失败或无数据被记成成功。"""

    adapter_source_for_connector(source_id)
    try:
        retry = p3.retry_decision(attempt=attempt, outcome=outcome)
    except p3.ConnectorContractError as error:
        raise StageReviewError("SCHEDULE_OUTCOME_INVALID", "定时检查结果未登记。") from error
    return {
        "schema_version": SCHEDULE_OUTCOME_SCHEMA,
        "source_id": source_id,
        "check_status": retry["status"],
        "retry": retry["retry"],
        "delay_minutes": retry["delay_minutes"],
        "manual_import_available": True,
        "manual_import_blocked": False,
        "scheduled_import_committed": False,
        "import_success_recorded": False,
        "checkpoint_advanced": False,
        "raw_root_access_count": 0,
        "live_connector_call_count": 0,
        "business_execution_performed": False,
    }


CHECK_IDS = (
    "P1_INSPECTION_BOUND_TO_PREVIEW",
    "P1_CONFIRMATION_BOUND_TO_CURRENT_PREVIEW",
    "P1_FILE_HASH_PRESERVED_IN_P2",
    "P1_SOURCE_ID_PRESERVED_IN_P2",
    "P1_PERIOD_PRESERVED_IN_P2",
    "P1_ENTITY_PRESERVED_IN_P2",
    "P2_TEMPLATE_VERSION_PRESERVED",
    "P2_READY_RECORD_REQUIRED",
    "TAMPERED_PREVIEW_REJECTED",
    "STALE_CONFIRMATION_REJECTED",
    "SWAPPED_FILE_HASH_REJECTED",
    "CHANGED_PERIOD_REJECTED",
    "CHANGED_ENTITY_REJECTED",
    "WRONG_ADAPTER_REJECTED",
    "FIVE_CONNECTOR_MAPPINGS_EXACT",
    "TAX_MAPS_TO_TAX_EINVOICE",
    "CONTRACT_LEDGER_REMAINS_FILE_ONLY",
    "CONNECTOR_AUTHORIZATION_REQUIRED",
    "REVOKED_CONNECTOR_REJECTED",
    "CONNECTOR_HASH_REQUIRED",
    "CONNECTOR_CURSOR_MUST_ADVANCE",
    "CONNECTOR_IDEMPOTENCY_REQUIRED",
    "CONNECTOR_TEMPLATE_SOURCE_BOUND",
    "CONNECTOR_MAPPING_VERSION_BOUND",
    "CONNECTOR_ENVELOPE_NOT_IMPORTABLE",
    "CONNECTOR_REQUIRES_P1_P2_CHAIN",
    "CONNECTOR_FILE_BINDING_EXACT",
    "CONNECTOR_TAMPER_REJECTED",
    "NO_DATA_NOT_IMPORT_SUCCESS",
    "NO_DATA_MANUAL_IMPORT_AVAILABLE",
    "TRANSIENT_FAILURE_NOT_IMPORT_SUCCESS",
    "PERMANENT_FAILURE_NOT_IMPORT_SUCCESS",
    "SCHEDULE_FAILURE_DOES_NOT_ADVANCE_CURSOR",
    "ONE_SOURCE_GATE_CANNOT_UNLOCK_ANOTHER",
    "RAW_AND_LIVE_ACCESS_ZERO",
    "RELEASE_AND_BUSINESS_ACTIONS_CLOSED",
)


def _raises_code(fn, code: str) -> bool:
    try:
        fn()
    except StageReviewError as error:
        return error.code == code
    return False


def _synthetic_chain() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="kmfa-s10-review-") as temporary:
        path = Path(temporary) / "synthetic_redcircle.csv"
        payload = "项目编号,项目名称,收入金额,成本金额\nP-001,公开合成项目,100,60\n".encode()
        path.write_bytes(payload)
        inspection = p1.inspect_file(path)
        preview = p1.build_import_preview(
            inspection,
            source_id="SRC-synthetic-redcircle-a1b2c3d4",
            source_label="红圈",
            entity_label="公开合成主体",
            business_segment="经营分析",
            period="2026-06",
        )
        confirmation = p1.confirm_import_preview(
            preview,
            preview_id=preview["preview_id"],
            preview_fingerprint=preview["preview_fingerprint"],
            decision="CONFIRM",
            operator_role="ROLE::FINANCE_REVIEWER",
            occurred_at="2026-07-15T22:00:00+10:00",
        )
        template = p2.TEMPLATE_BY_ID["redcircle.operating.v1"]
        sheet = p2._sample_sheet(template, context={"entity_id": "ENTITY::SYNTHETIC_A", "period": "2026-06"})
        adaptation = p2.adapt_workbook(inspection, source_system="REDCIRCLE", sheets=[sheet])
        source_binding = {
            "source_id": "SRC-synthetic-redcircle-a1b2c3d4",
            "adapter_source": "REDCIRCLE",
            "entity_id": "ENTITY::SYNTHETIC_A",
            "entity_label": "公开合成主体",
        }
        file_binding = bind_confirmed_file_adaptation(
            inspection=inspection,
            preview=preview,
            confirmation=confirmation,
            adaptation=adaptation,
            source_binding=source_binding,
        )
        session = p3.authorize(
            "REDCIRCLE",
            authorization_id="AUTH-SYNTHETIC-001",
            vault_reference="vaultref://kmfa/s10/review",
            official_authorization=True,
            read_only_scope=True,
        )
        envelope = build_connector_handoff_envelope(
            session=session,
            requested_at=datetime(2026, 7, 15, 22, 5, tzinfo=ZoneInfo(p3.DEFAULT_TIMEZONE)),
            payload=payload,
            declared_hash=inspection["file_hash"],
            cursor=1,
            idempotency_key="IDEM-S10-REVIEW-001",
            file_display_name=inspection["file_display_name"],
            period="2026-06",
            entity_id="ENTITY::SYNTHETIC_A",
            entity_label="公开合成主体",
            source_id="SRC-synthetic-redcircle-a1b2c3d4",
            template_id="redcircle.operating.v1",
            mapping_version="1.0.0",
        )
        return {
            "payload": payload,
            "inspection": inspection,
            "preview": preview,
            "confirmation": confirmation,
            "adaptation": adaptation,
            "source_binding": source_binding,
            "file_binding": file_binding,
            "session": session,
            "envelope": envelope,
        }


def public_verification() -> dict[str, Any]:
    chain = _synthetic_chain()
    binding = chain["file_binding"]
    envelope = chain["envelope"]
    commit_auth = authorize_connector_file_commit(envelope=envelope, file_binding=binding)
    no_data = scheduled_check_outcome(source_id="REDCIRCLE", attempt=1, outcome="NO_DATA")
    transient = scheduled_check_outcome(source_id="REDCIRCLE", attempt=1, outcome="TRANSIENT_FAILURE")
    permanent = scheduled_check_outcome(source_id="REDCIRCLE", attempt=1, outcome="PERMANENT_FAILURE")

    tampered_preview = copy.deepcopy(chain["preview"])
    tampered_preview["period"]["value"] = "2026-07"
    stale_confirmation = copy.deepcopy(chain["confirmation"])
    stale_confirmation["preview_fingerprint"] = "sha256:" + "0" * 64
    stale_confirmation["event_fingerprint"] = p1._fingerprint({key: value for key, value in stale_confirmation.items() if key != "event_fingerprint"})
    swapped_adaptation = copy.deepcopy(chain["adaptation"])
    swapped_adaptation["file_hash"] = "sha256:" + "0" * 64
    changed_period = copy.deepcopy(chain["adaptation"])
    changed_period["adapted_sheets"][0]["period"] = "2026-07"
    changed_entity = copy.deepcopy(chain["adaptation"])
    changed_entity["records"][0]["entity_id"] = "ENTITY::SYNTHETIC_B"
    wrong_source = {**chain["source_binding"], "adapter_source": "WPS"}
    tampered_envelope = copy.deepcopy(envelope)
    tampered_envelope["period"] = "2026-07"
    matrix = p3.activation_matrix_public_safe()
    redcircle_ready = p3.activation_gate("REDCIRCLE", {criterion: True for criterion in p3.ACTIVATION_CRITERIA})

    checks = [
        binding["inspection_fingerprint"] == chain["inspection"]["inspection_fingerprint"],
        binding["confirmation_fingerprint"] == chain["confirmation"]["event_fingerprint"],
        binding["file_hash"] == chain["inspection"]["file_hash"],
        binding["source_id"] == chain["source_binding"]["source_id"],
        binding["period"] == "2026-06",
        binding["entity_id"] == "ENTITY::SYNTHETIC_A",
        binding["template_versions"] == [{"template_id": "redcircle.operating.v1", "mapping_version": "1.0.0"}],
        binding["adapted_record_count"] == 1,
        _raises_code(lambda: bind_confirmed_file_adaptation(inspection=chain["inspection"], preview=tampered_preview, confirmation=chain["confirmation"], adaptation=chain["adaptation"], source_binding=chain["source_binding"]), "P1_CONFIRMATION_CHAIN_INVALID"),
        _raises_code(lambda: bind_confirmed_file_adaptation(inspection=chain["inspection"], preview=chain["preview"], confirmation=stale_confirmation, adaptation=chain["adaptation"], source_binding=chain["source_binding"]), "P1_CONFIRMATION_CHAIN_INVALID"),
        _raises_code(lambda: bind_confirmed_file_adaptation(inspection=chain["inspection"], preview=chain["preview"], confirmation=chain["confirmation"], adaptation=swapped_adaptation, source_binding=chain["source_binding"]), "ADAPTATION_FILE_HASH_MISMATCH"),
        _raises_code(lambda: bind_confirmed_file_adaptation(inspection=chain["inspection"], preview=chain["preview"], confirmation=chain["confirmation"], adaptation=changed_period, source_binding=chain["source_binding"]), "PERIOD_ENTITY_BINDING_MISMATCH"),
        _raises_code(lambda: bind_confirmed_file_adaptation(inspection=chain["inspection"], preview=chain["preview"], confirmation=chain["confirmation"], adaptation=changed_entity, source_binding=chain["source_binding"]), "RECORD_CONTEXT_BINDING_MISMATCH"),
        _raises_code(lambda: bind_confirmed_file_adaptation(inspection=chain["inspection"], preview=chain["preview"], confirmation=chain["confirmation"], adaptation=chain["adaptation"], source_binding=wrong_source), "ADAPTER_SOURCE_BINDING_MISMATCH"),
        CONNECTOR_TO_ADAPTER == {"REDCIRCLE": "REDCIRCLE", "KINGDEE": "KINGDEE", "WPS": "WPS", "BANK": "BANK", "TAX": "TAX_EINVOICE"},
        adapter_source_for_connector("TAX") == "TAX_EINVOICE",
        "CONTRACT_LEDGER" not in CONNECTOR_TO_ADAPTER.values() and p3.connector_contract_public_safe()["contract_ledger_mode"] == "FILE_ONLY_NOT_CONNECTOR_CANDIDATE",
        chain["session"].official_authorization and chain["session"].read_only_scope,
        _raises_code(lambda: build_connector_handoff_envelope(session=p3.revoke(chain["session"]), requested_at=datetime(2026, 7, 15, 22, 5, tzinfo=ZoneInfo(p3.DEFAULT_TIMEZONE)), payload=chain["payload"], declared_hash=chain["inspection"]["file_hash"], cursor=1, idempotency_key="IDEM-X", file_display_name="synthetic_redcircle.csv", period="2026-06", entity_id="ENTITY::SYNTHETIC_A", entity_label="公开合成主体", source_id=chain["source_binding"]["source_id"], template_id="redcircle.operating.v1", mapping_version="1.0.0"), "P3_CONNECTOR_CONTRACT_INVALID"),
        _raises_code(lambda: build_connector_handoff_envelope(session=chain["session"], requested_at=datetime(2026, 7, 15, 22, 5, tzinfo=ZoneInfo(p3.DEFAULT_TIMEZONE)), payload=chain["payload"], declared_hash="sha256:" + "0" * 64, cursor=1, idempotency_key="IDEM-X", file_display_name="synthetic_redcircle.csv", period="2026-06", entity_id="ENTITY::SYNTHETIC_A", entity_label="公开合成主体", source_id=chain["source_binding"]["source_id"], template_id="redcircle.operating.v1", mapping_version="1.0.0"), "P3_CONNECTOR_CONTRACT_INVALID"),
        _raises_code(lambda: build_connector_handoff_envelope(session=chain["session"], requested_at=datetime(2026, 7, 15, 22, 5, tzinfo=ZoneInfo(p3.DEFAULT_TIMEZONE)), payload=chain["payload"], declared_hash=chain["inspection"]["file_hash"], cursor=0, idempotency_key="IDEM-X", file_display_name="synthetic_redcircle.csv", period="2026-06", entity_id="ENTITY::SYNTHETIC_A", entity_label="公开合成主体", source_id=chain["source_binding"]["source_id"], template_id="redcircle.operating.v1", mapping_version="1.0.0"), "CONNECTOR_CURSOR_INVALID"),
        _raises_code(lambda: build_connector_handoff_envelope(session=chain["session"], requested_at=datetime(2026, 7, 15, 22, 5, tzinfo=ZoneInfo(p3.DEFAULT_TIMEZONE)), payload=chain["payload"], declared_hash=chain["inspection"]["file_hash"], cursor=1, idempotency_key="", file_display_name="synthetic_redcircle.csv", period="2026-06", entity_id="ENTITY::SYNTHETIC_A", entity_label="公开合成主体", source_id=chain["source_binding"]["source_id"], template_id="redcircle.operating.v1", mapping_version="1.0.0"), "CONNECTOR_IDEMPOTENCY_KEY_INVALID"),
        _raises_code(lambda: build_connector_handoff_envelope(session=chain["session"], requested_at=datetime(2026, 7, 15, 22, 5, tzinfo=ZoneInfo(p3.DEFAULT_TIMEZONE)), payload=chain["payload"], declared_hash=chain["inspection"]["file_hash"], cursor=1, idempotency_key="IDEM-X", file_display_name="synthetic_redcircle.csv", period="2026-06", entity_id="ENTITY::SYNTHETIC_A", entity_label="公开合成主体", source_id=chain["source_binding"]["source_id"], template_id="wps.collection.v1", mapping_version="1.0.0"), "CONNECTOR_TEMPLATE_SOURCE_MISMATCH"),
        envelope["mapping_version"] == "1.0.0",
        envelope["importable"] is False and envelope["checkpoint_advanced"] is False,
        envelope["required_processing_chain"] == ["S10-P1", "S10-P2", "PRIVATE-ATOMIC-COMMIT"],
        commit_auth["authorization_status"] == "READY_FOR_PRIVATE_ATOMIC_COMMIT" and commit_auth["manual_confirmation_verified"] is True,
        _raises_code(lambda: authorize_connector_file_commit(envelope=tampered_envelope, file_binding=binding), "CONNECTOR_ENVELOPE_TAMPERED"),
        no_data["import_success_recorded"] is False and no_data["scheduled_import_committed"] is False,
        no_data["manual_import_available"] is True and no_data["manual_import_blocked"] is False,
        transient["import_success_recorded"] is False and transient["retry"] is True,
        permanent["import_success_recorded"] is False and permanent["retry"] is False,
        all(not row["checkpoint_advanced"] for row in (no_data, transient, permanent)),
        redcircle_ready["ready_for_separate_acceptance"] and all(not row["ready_for_separate_acceptance"] for row in matrix["gates"]),
        all(value == 0 for value in (binding["raw_root_access_count"], envelope["raw_root_access_count"], envelope["live_connector_call_count"], no_data["raw_root_access_count"])),
        binding["business_execution_performed"] is False and commit_auth["import_success_recorded"] is False,
    ]
    if len(checks) != len(CHECK_IDS):
        raise StageReviewError("PUBLIC_CHECK_COUNT_DRIFT", "复审检查数量与编号不一致。")
    rows = [
        {"check_id": check_id, "status": "PASS" if passed else "FAIL"}
        for check_id, passed in zip(CHECK_IDS, checks)
    ]
    failed = sum(row["status"] == "FAIL" for row in rows)
    return {
        "schema_version": "kmfa.v015.s10_stage_review.public_verification.v1",
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed},
        "checks": rows,
        "fixed_review_finding_count": 3,
        "connector_adapter_mapping_count": 5,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_connector_call_count": 0,
        "credential_read_count": 0,
        "source_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


if __name__ == "__main__":
    print(json.dumps(public_verification(), ensure_ascii=False, indent=2, sort_keys=True))
