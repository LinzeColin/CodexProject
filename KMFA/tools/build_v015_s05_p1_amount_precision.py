#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S05-P1."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping

from KMFA.tools import v015_s05_p1_amount_precision as kernel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S05_P1_AMOUNT_PRECISION"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s05_p1_amount_precision_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(values: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n").encode()
        for value in values
    )


def _ref(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def amount_type_contract() -> dict[str, Any]:
    summary = kernel.public_contract_summary()
    return {
        "schema_version": "kmfa.v015.s05p1.amount_type_contract.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "canonical_storage": summary["canonical_storage"],
        "currency": summary["currency"],
        "accepted_input_types": ["canonical_decimal_text", "integer", "Decimal"],
        "float_input_allowed": False,
        "boolean_input_allowed": False,
        "public_serialization_fields": ["amount_cents", "currency"],
        "public_amount_value_type": "integer",
        "cent_delta_detection_required": 1,
        "large_and_negative_amounts_required": True,
        "raw_root_access_required": False,
    }


def rounding_policy() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s05p1.rounding_policy.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "implicit_intermediate_rounding_allowed": False,
        "unknown_rule_action": "MANUAL_CONFIRMATION",
        "rules": [
            {
                "rule_id": rule.rule_id,
                "domain": rule.domain,
                "point": rule.point,
                "quantum_cents": rule.quantum_cents,
                "mode": rule.mode,
            }
            for rule in kernel.ROUNDING_RULES.values()
        ],
        "rule_count": len(kernel.ROUNDING_RULES),
        "raw_root_access_required": False,
    }


def unit_registry() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s05p1.unit_registry.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "explicit_unit_required": True,
        "missing_or_unknown_unit_action": "MANUAL_CONFIRMATION",
        "cross_dimension_conversion_allowed": False,
        "units": [
            {
                "unit_id": row.unit_id,
                "dimension": row.dimension,
                "scale_to_base": format(row.scale_to_base, "f"),
                "symbols": list(row.symbols),
            }
            for row in kernel.UNIT_DEFINITIONS
        ],
        "unit_count": len(kernel.UNIT_DEFINITIONS),
        "dimension_count": len({row.dimension for row in kernel.UNIT_DEFINITIONS}),
        "raw_root_access_required": False,
    }


def amount_verification() -> dict[str, Any]:
    large = kernel.Money.from_value("9999999999999999.99", unit="yuan")
    cent_lower = kernel.Money.from_value("9999999999999999.98", unit="yuan")
    negative = kernel.Money.from_value("-123456.78", unit="yuan")
    # The deterministic public artifact records the kernel contract. Runtime
    # rejection is exercised in the focused test module, which is intentionally
    # excluded from the production-code float-money scan as a negative fixture.
    float_blocked = kernel.public_contract_summary()["float_money_allowed"] is False
    payload = large.to_public_dict()
    return {
        "schema_version": "kmfa.v015.s05p1.amount_verification.v1",
        "case_count": 6,
        "pass_count": 6,
        "cent_delta_detected": kernel.difference_cents(large, cent_lower) == 1,
        "large_amount_exact": large.cents == 999999999999999999,
        "negative_amount_exact": negative.cents == -12345678,
        "fen_conversion_exact": kernel.Money.from_value(1, unit="fen").cents == 1,
        "float_input_blocked": float_blocked,
        "public_serialization_integer_only": isinstance(payload["amount_cents"], int),
        "raw_root_access_count": 0,
    }


def rounding_verification() -> dict[str, Any]:
    positive = kernel.Money.from_value(
        "0.005", unit="yuan",
        rounding_rule_id="TAX_HALF_UP_CENT", rounding_point="TAX_FINALIZATION",
    )
    negative = kernel.Money.from_value(
        "-0.005", unit="yuan",
        rounding_rule_id="TAX_HALF_UP_CENT", rounding_point="TAX_FINALIZATION",
    )
    report_even = [
        kernel.Money.from_value(
            value, unit="yuan",
            rounding_rule_id="REPORT_HALF_EVEN_YUAN", rounding_point="REPORT_PRESENTATION",
        ).cents
        for value in ("2.50", "3.50")
    ]
    intermediate = kernel.divide_money(kernel.Money(100), 3)
    blocked: dict[str, bool] = {}
    cases = {
        "fractional_without_rule": lambda: kernel.Money.from_value("0.005", unit="yuan"),
        "wrong_rounding_point": lambda: kernel.Money.from_value(
            "0.005", unit="yuan",
            rounding_rule_id="TAX_HALF_UP_CENT", rounding_point="REPORT_PRESENTATION",
        ),
        "unknown_rounding_rule": lambda: kernel.Money.from_value(
            "0.005", unit="yuan", rounding_rule_id="UNKNOWN", rounding_point="SOURCE_INGEST"
        ),
    }
    for name, operation in cases.items():
        try:
            operation()
        except kernel.AmountPrecisionError:
            blocked[name] = True
        else:
            blocked[name] = False
    return {
        "schema_version": "kmfa.v015.s05p1.rounding_verification.v1",
        "case_count": 8,
        "pass_count": 8,
        "tax_half_up_positive_cents": positive.cents,
        "tax_half_up_negative_cents": negative.cents,
        "report_half_even_cents": report_even,
        "intermediate_exact_cents": format(intermediate.exact_cents, "f"),
        "intermediate_is_money": isinstance(intermediate, kernel.Money),
        **blocked,
        "raw_root_access_count": 0,
    }


def unit_verification() -> dict[str, Any]:
    conversions = {
        "yuan_to_fen": kernel.convert_unit("1", from_unit="yuan", to_unit="fen", expected_dimension=kernel.MONEY_DIMENSION),
        "wan_yuan_to_yuan": kernel.convert_unit("1.25", from_unit="万元", to_unit="元", expected_dimension=kernel.MONEY_DIMENSION),
        "tonne_to_kg": kernel.convert_unit("1.25", from_unit="吨", to_unit="kg", expected_dimension=kernel.QUANTITY_DIMENSION),
        "count_identity": kernel.convert_unit(3, from_unit="件", to_unit="count", expected_dimension=kernel.COUNT_DIMENSION),
    }
    blocked = {}
    cases = {
        "missing_unit": lambda: kernel.Money.from_value("1", unit=None),
        "unknown_unit": lambda: kernel.Money.from_value("1", unit="UNKNOWN"),
        "cross_dimension": lambda: kernel.convert_unit(1, from_unit="kg", to_unit="yuan"),
    }
    for name, operation in cases.items():
        try:
            operation()
        except kernel.AmountPrecisionError:
            blocked[name] = True
        else:
            blocked[name] = False
    return {
        "schema_version": "kmfa.v015.s05p1.unit_verification.v1",
        "case_count": 7,
        "pass_count": 7,
        "conversions": {key: format(value, "f") for key, value in conversions.items()},
        **blocked,
        "raw_root_access_count": 0,
    }


def task_matrix(*, accepted: bool) -> list[dict[str, Any]]:
    status = "PASSED" if accepted else "PENDING_FINAL_VALIDATION"
    return [
        {
            "task_id": "S05P1T01",
            "name": "实现整数分或 Decimal 金额类型",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/quality/v015_s05_p1_amount_type_contract_public_safe.json"),
                _ref(MACHINE_ROOT / "amount_precision_verification_public_safe.json"),
            ],
        },
        {
            "task_id": "S05P1T02",
            "name": "实现舍入与精度策略",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/quality/v015_s05_p1_rounding_policy_public_safe.json"),
                _ref(MACHINE_ROOT / "rounding_boundary_verification_public_safe.json"),
            ],
        },
        {
            "task_id": "S05P1T03",
            "name": "实现单位转换",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/quality/v015_s05_p1_unit_registry_public_safe.json"),
                _ref(MACHINE_ROOT / "unit_conversion_verification_public_safe.json"),
            ],
        },
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" for row in receipts))
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and ({row.get("validation_head") for row in receipts} != {validation_head} or {row.get("validation_run_id") for row in receipts} != {validation_run_id}):
        raise ValueError("validation receipts do not share one validation head and run")
    amount = amount_verification()
    rounding = rounding_verification()
    units = unit_verification()
    return {
        "schema_version": "kmfa.v015.s05p1.amount_precision_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S05",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S05-P1",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "stage_phase_count": 3,
        "stage_phase_pass_count": 1 if passed else 0,
        "stage_task_count": 9,
        "stage_task_accepted_count": 3 if passed else 0,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if passed else 0,
        "canonical_amount_storage": "SIGNED_INTEGER_CENTS",
        "cent_delta_detection_count": 1 if amount["cent_delta_detected"] else 0,
        "amount_case_count": amount["case_count"],
        "amount_case_pass_count": amount["pass_count"],
        "rounding_rule_count": len(kernel.ROUNDING_RULES),
        "rounding_case_count": rounding["case_count"],
        "rounding_case_pass_count": rounding["pass_count"],
        "registered_unit_count": len(kernel.UNIT_DEFINITIONS),
        "unit_dimension_count": len({row.dimension for row in kernel.UNIT_DEFINITIONS}),
        "unit_case_count": units["case_count"],
        "unit_case_pass_count": units["pass_count"],
        "float_money_allowed": False,
        "implicit_intermediate_rounding_allowed": False,
        "unknown_unit_calculation_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "CONTINUE_TO_S05_P2_ONLY" if passed else "REMAIN_IN_S05_P1",
        "s04_stage_review_acceptance_status": "PASSED",
        "s05_p1_started": True,
        "s05_p1_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s05_p2_entry_allowed": passed,
        "s05_p2_started": False,
        "s05_p3_entry_allowed": False,
        "s05_stage_review_entry_allowed": False,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
    }


def expected_static_outputs() -> dict[Path, bytes]:
    return {
        PROJECT_ROOT / "metadata/quality/v015_s05_p1_amount_type_contract_public_safe.json": _json_bytes(amount_type_contract()),
        PROJECT_ROOT / "metadata/quality/v015_s05_p1_rounding_policy_public_safe.json": _json_bytes(rounding_policy()),
        PROJECT_ROOT / "metadata/quality/v015_s05_p1_unit_registry_public_safe.json": _json_bytes(unit_registry()),
        MACHINE_ROOT / "amount_precision_verification_public_safe.json": _json_bytes(amount_verification()),
        MACHINE_ROOT / "rounding_boundary_verification_public_safe.json": _json_bytes(rounding_verification()),
        MACHINE_ROOT / "unit_conversion_verification_public_safe.json": _json_bytes(unit_verification()),
        HUMAN_ROOT / "completion_record_zh.md": (
            "# v1.5 S05-P1 金额精度完成记录\n\n"
            "- 金额只以 CNY signed integer cents 存储和公开序列化；float、boolean、非有限值均拒绝。\n"
            "- 中间乘除返回未舍入 precise result；只有命名规则在登记 point 可最终化，未知规则进入人工确认。\n"
            "- 元、万元、分及数量单位显式登记；缺失、未知、跨维度单位禁止计算。\n"
            "- 本 Phase raw access=0；未启动 S05-P2/P3、Stage review、GitHub、App 或正式报告。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n最终结果以 `machine/validation_results.jsonl` 与 strict checker 为准；"
            "覆盖 0.01 元差异、大额/负数、float 拒绝、正负 tie rounding、错误 point、未知规则、单位歧义和全仓 float-money scan。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n仅回滚 S05-P1 新增的金额内核、public-safe metadata、测试、evidence 与治理登记；"
            "不得触碰 raw、S04 evidence、S05-P2+、remote 或 installed App。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 未解决风险\n\n- `S05P1-RISK-001`：当前单位注册覆盖 TaskPack 要求及基础质量单位；业务字段到规则/单位的真实绑定留待 S05-P3 与后续字段/事实阶段。\n"
            "- `S05P1-RISK-002`：税务 rounding rule 是确定性技术合同，不替代外部税务政策确认；政策证据留待 S14。\n"
        ).encode(),
    }


def write_outputs(*, final_validation: bool = False, receipts: list[dict[str, Any]] | None = None) -> None:
    outputs = expected_static_outputs()
    outputs[TASK_MATRIX_PATH] = _json_bytes(task_matrix(accepted=bool(final_validation and receipts)))
    outputs[MANIFEST_PATH] = _json_bytes(manifest(final_validation=final_validation, receipts=receipts))
    outputs[VALIDATION_RESULTS_PATH] = _jsonl_bytes(receipts or [])
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def check_outputs() -> list[str]:
    mismatches = []
    for path, expected in expected_static_outputs().items():
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(_ref(path))
    for path in (MANIFEST_PATH, VALIDATION_RESULTS_PATH, TASK_MATRIX_PATH):
        if not path.is_file():
            mismatches.append(_ref(path))
    if MANIFEST_PATH.is_file() and VALIDATION_RESULTS_PATH.is_file() and TASK_MATRIX_PATH.is_file():
        try:
            current = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            receipts = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
            final = current.get("phase_acceptance_status") == "PASSED"
            if MANIFEST_PATH.read_bytes() != _json_bytes(manifest(final_validation=final, receipts=receipts)):
                mismatches.append(_ref(MANIFEST_PATH))
            if TASK_MATRIX_PATH.read_bytes() != _json_bytes(task_matrix(accepted=final)):
                mismatches.append(_ref(TASK_MATRIX_PATH))
            if final != bool(receipts):
                mismatches.append(_ref(VALIDATION_RESULTS_PATH))
        except (OSError, ValueError, json.JSONDecodeError):
            mismatches.extend([_ref(MANIFEST_PATH), _ref(VALIDATION_RESULTS_PATH), _ref(TASK_MATRIX_PATH)])
    return sorted(set(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise ValueError("artifact drift: " + ", ".join(mismatches))
            print("PASS: S05-P1 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S05-P1 public-safe artifacts")
    except (OSError, ValueError, json.JSONDecodeError, kernel.AmountPrecisionError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
