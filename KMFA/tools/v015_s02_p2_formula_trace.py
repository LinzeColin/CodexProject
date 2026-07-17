#!/usr/bin/env python3
"""Public-safe formula and parameter trace planning for KMFA v1.5 S02-P2.

This module reads only the public TaskPack source package.  It inventories the
v2.0 calculation definitions and their parameters/thresholds, but deliberately
does not implement or enable any product formula.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zipfile import ZipFile


SOURCE_PACKAGE_NAME = (
    "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
)
SOURCE_PACKAGE_SHA256 = (
    "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
)
DEFAULT_SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME
FORMULA_SOURCE_BASENAME = "08_KMFA_模型公式函数参数主注册表_v2_0.yaml"
FORMULA_SOURCE_SHA256 = (
    "599d741fc7da4d94d4892c65d38c4e0f7ae135b71b7f3a269f5319042b821605"
)

EXPECTED_DEFINITION_IDS = frozenset(
    {
        "AMT-NORMALIZE-001",
        "AMT-EXACT-002",
        "PROJECT-MATCH-001",
        "COST-TOTAL-001",
        "MARGIN-CONTRACT-001",
        "MARGIN-SETTLEMENT-002",
        "MARGIN-MANAGEMENT-003",
        "MARGIN-CASH-004",
        "MARGIN-RATE-005",
        "COST-COMPLETENESS-006",
        "AR-COLLECTION-001",
        "AR-AGING-002",
        "AR-PRIORITY-003",
        "CASH-RUNWAY-001",
        "CASH-GAP-002",
        "HEALTH-001",
        "ACTION-PRIORITY-001",
        "DATA-QUALITY-001",
        "FRESHNESS-001",
        "REPORT-RELEASE-001",
        "RERUN-001",
        "CROSS-SOURCE-001",
    }
)
EXPECTED_RAW_STATUS_COUNTS = {"PROPOSED": 17, "VERIFIED_REQUIRED": 5}
EXPECTED_CONTROL_KIND_COUNTS = {
    "THRESHOLD": 4,
    "WEIGHT": 20,
    "CONTROL_SWITCH": 2,
    "ROUNDING_POLICY": 1,
    "PARAMETER": 2,
    "THRESHOLD_SET": 1,
    "DEFAULT": 7,
    "INLINE_LITERAL_REQUIRES_EXTERNALIZATION": 1,
}
EXPECTED_PARAMETER_COUNT = sum(EXPECTED_CONTROL_KIND_COUNTS.values())

_STATUS_NORMALIZATION = {
    "PROPOSED": "PLANNED_NOT_ENABLED",
    # The source uses this value although it is absent from its own vocabulary.
    # It means verification is required, not that verification already passed.
    "VERIFIED_REQUIRED": "VERIFICATION_REQUIRED_NOT_ENABLED",
}

_REQUIREMENT_REFS_BY_ROOT = {
    "amount_functions": ("R012", "R014", "R026"),
    "project_identity": ("R015", "R026"),
    "project_cost": ("R012", "R026", "R029", "R030"),
    "receivables": ("R026", "R031"),
    "cash_management": ("R026", "R032"),
    "operating_health": ("R026", "R027"),
    "action_priority": ("R026", "R028"),
    "data_quality": ("R021", "R026", "R045"),
    "source_freshness": ("R021", "R026"),
    "report_release": ("R021", "R026", "R034", "R036"),
    "same_source_rerun": ("R009", "R025", "R026", "R036"),
    "cross_source_resolution": ("R010", "R026", "R036"),
}

_IMPLEMENTATION_TASK_REFS_BY_ROOT = {
    "amount_functions": ("S05P1T01", "S07P1T01", "S13P1T01", "S23P2T01"),
    "project_identity": ("S08P1T01", "S08P3T01", "S13P1T02"),
    "project_cost": ("S12P2T01", "S12P2T02", "S12P2T03", "S13P1T01"),
    "receivables": ("S18P1T01", "S18P1T02", "S13P1T01"),
    "cash_management": ("S18P2T02", "S18P2T03", "S13P1T01"),
    "operating_health": ("S13P2T01", "S13P2T02"),
    "action_priority": ("S13P3T01", "S13P3T02"),
    "data_quality": ("S11P1T01", "S11P1T03", "S13P1T02"),
    "source_freshness": ("S11P2T03", "S13P1T02"),
    "report_release": ("S21P1T01", "S21P3T01"),
    "same_source_rerun": ("S07P2T01", "S20P3T01", "S23P3T01"),
    "cross_source_resolution": ("S07P2T02", "S20P2T03", "S23P1T02"),
}

_REPORT_TASK_REFS_BY_ROOT = {
    "project_cost": ("S17P3T03", "S21P1T01"),
    "receivables": ("S18P3T03", "S21P1T01"),
    "cash_management": ("S18P3T03", "S21P1T01"),
    "operating_health": ("S16P1T01", "S21P1T01"),
    "action_priority": ("S16P1T02", "S21P1T01"),
    "data_quality": ("S21P1T03",),
    "source_freshness": ("S21P1T03",),
    "report_release": ("S21P1T01", "S21P3T01"),
}


class TraceSourceError(RuntimeError):
    """Raised when the authoritative public TaskPack source does not match."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pointer(path: Sequence[str]) -> str:
    encoded = [part.replace("~", "~0").replace("/", "~1") for part in path]
    return "/" + "/".join(encoded)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        parsed = ast.literal_eval(value)
        return str(parsed)
    return value


def _parse_inline_list(value: str) -> list[str]:
    body = value.strip()[1:-1].strip()
    if not body:
        return []
    return [_unquote(part) for part in body.split(",")]


def _parse_yaml_subset(
    text: str,
) -> tuple[dict[tuple[str, ...], str | list[str]], dict[tuple[str, ...], list[str]]]:
    """Parse the mapping/scalar subset used by the authoritative source YAML.

    Values stay as strings so decimal weights never become binary floats.
    """

    values: dict[tuple[str, ...], str | list[str]] = {}
    lists: dict[tuple[str, ...], list[str]] = {}
    stack: list[tuple[int, str]] = []
    mapping_pattern = re.compile(r"^(\s*)([^:#][^:]*):(?:\s*(.*))?$")
    list_pattern = re.compile(r"^(\s*)-\s+(.*)$")

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        list_match = list_pattern.match(raw_line)
        if list_match:
            indent = len(list_match.group(1))
            while stack and stack[-1][0] >= indent:
                stack.pop()
            path = tuple(item[1] for item in stack)
            if not path:
                raise TraceSourceError("top-level YAML list is outside supported source schema")
            lists.setdefault(path, []).append(_unquote(list_match.group(2)))
            continue

        match = mapping_pattern.match(raw_line)
        if not match:
            raise TraceSourceError(f"unsupported YAML source line: {raw_line!r}")
        indent = len(match.group(1))
        key = match.group(2).strip()
        raw_value = match.group(3).strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = tuple(item[1] for item in stack) + (key,)
        if raw_value:
            if raw_value.startswith("[") and raw_value.endswith("]"):
                values[path] = _parse_inline_list(raw_value)
            else:
                values[path] = _unquote(raw_value)
        else:
            stack.append((indent, key))
    return values, lists


def _load_source(
    source_package: str | Path,
) -> tuple[
    dict[tuple[str, ...], str | list[str]],
    dict[tuple[str, ...], list[str]],
    dict[str, str],
]:
    path = Path(source_package)
    if not path.is_file():
        raise TraceSourceError(f"source package missing: {path}")
    package_bytes = path.read_bytes()
    package_sha = _sha256_bytes(package_bytes)
    if package_sha != SOURCE_PACKAGE_SHA256:
        raise TraceSourceError(f"source package SHA256 mismatch: {package_sha}")

    with ZipFile(path) as archive:
        matches = [
            name for name in archive.namelist() if Path(name).name == FORMULA_SOURCE_BASENAME
        ]
        if len(matches) != 1:
            raise TraceSourceError(
                f"expected one {FORMULA_SOURCE_BASENAME!r} member, found {len(matches)}"
            )
        member_name = matches[0]
        member_bytes = archive.read(member_name)
    member_sha = _sha256_bytes(member_bytes)
    if member_sha != FORMULA_SOURCE_SHA256:
        raise TraceSourceError(f"formula source member SHA256 mismatch: {member_sha}")

    try:
        text = member_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TraceSourceError("formula source member is not UTF-8") from exc
    values, lists = _parse_yaml_subset(text)
    return values, lists, {
        "source_package_file": path.name,
        "source_package_sha256": package_sha,
        "source_member": member_name,
        "source_member_sha256": member_sha,
    }


def _definition_nodes(
    values: Mapping[tuple[str, ...], str | list[str]],
) -> list[tuple[tuple[str, ...], str, str]]:
    nodes: list[tuple[tuple[str, ...], str, str]] = []
    for path, value in values.items():
        if path[-1] not in {"formula_id", "model_id"}:
            continue
        if not isinstance(value, str):
            raise TraceSourceError(f"definition ID at {_pointer(path)} must be scalar")
        nodes.append((path[:-1], path[-1], value))
    ids = [item[2] for item in nodes]
    if len(ids) != len(set(ids)):
        raise TraceSourceError("duplicate formula/model IDs in source member")
    if set(ids) != EXPECTED_DEFINITION_IDS:
        missing = sorted(EXPECTED_DEFINITION_IDS - set(ids))
        extra = sorted(set(ids) - EXPECTED_DEFINITION_IDS)
        raise TraceSourceError(f"definition universe drift; missing={missing}, extra={extra}")
    return nodes


def _root_key(node_path: Sequence[str]) -> str:
    return node_path[0]


def _planned_report_refs(definition_id: str, root_key: str) -> list[str]:
    task_refs = _REPORT_TASK_REFS_BY_ROOT.get(root_key, ("S21P1T01",))
    return [
        f"report-contract://KMFA/v1.5/{definition_id}/{task_ref}"
        for task_ref in task_refs
    ]


def _source_ref(source: Mapping[str, str], pointer: str) -> str:
    return (
        "taskpack://"
        f"sha256:{source['source_package_sha256']}/"
        f"sha256:{source['source_member_sha256']}#{pointer}"
    )


def _fixture_contract_refs(identifier: str) -> list[str]:
    return [
        f"fixture-contract://KMFA/v1.5/{identifier}/positive",
        f"fixture-contract://KMFA/v1.5/{identifier}/boundary",
        f"fixture-contract://KMFA/v1.5/{identifier}/fail-closed",
    ]


def _control_id(pointer: str) -> str:
    digest = hashlib.sha256(pointer.encode("utf-8")).hexdigest()[:12].upper()
    return f"CTRL-KMFA-V15-{digest}"


def _value_type(value: str | list[str]) -> str:
    if isinstance(value, list):
        return "integer_string_list"
    if value in {"true", "false"}:
        return "boolean_string"
    if re.fullmatch(r"-?\d+", value):
        return "integer_string"
    if re.fullmatch(r"-?\d+\.\d+", value):
        return "decimal_string"
    return "string"


def _control_kind(path: Sequence[str]) -> str | None:
    key = path[-1]
    if key == "amount_tolerance_cents" or "thresholds" in path:
        return "THRESHOLD"
    if key == "weight" or key.endswith("_weight"):
        return "WEIGHT"
    if key in {"available_weight_normalization", "hard_gate_precedence"}:
        return "CONTROL_SWITCH"
    if key == "display_rounding":
        return "ROUNDING_POLICY"
    if key == "horizons_days":
        return "THRESHOLD_SET"
    if "defaults" in path:
        return "DEFAULT"
    if "parameters" in path or key == "epsilon":
        return "PARAMETER"
    return None


def _parent_definition_ids(
    path: Sequence[str], definition_by_path: Mapping[tuple[str, ...], str]
) -> list[str]:
    candidates = [
        (definition_path, definition_id)
        for definition_path, definition_id in definition_by_path.items()
        if tuple(path[: len(definition_path)]) == definition_path
    ]
    if candidates:
        return [max(candidates, key=lambda item: len(item[0]))[1]]
    if tuple(path) == ("governance", "amount_tolerance_cents"):
        return ["AMT-EXACT-002"]
    raise TraceSourceError(f"control has no calculation parent: {_pointer(path)}")


def _parameter_rows(
    values: Mapping[tuple[str, ...], str | list[str]],
    source: Mapping[str, str],
    definition_nodes: Sequence[tuple[tuple[str, ...], str, str]],
) -> list[dict[str, Any]]:
    definition_by_path = {path: definition_id for path, _, definition_id in definition_nodes}
    raw_status_by_id = {
        definition_id: str(values[path + ("status",)])
        for path, _, definition_id in definition_nodes
    }
    rows: list[dict[str, Any]] = []

    for path, value in values.items():
        kind = _control_kind(path)
        if kind is None:
            continue
        parent_ids = _parent_definition_ids(path, definition_by_path)
        pointer = _pointer(path)
        control_id = _control_id(pointer)
        parent_statuses = [raw_status_by_id[item] for item in parent_ids]
        raw_status = parent_statuses[0] if len(set(parent_statuses)) == 1 else "MIXED"
        rows.append(
            {
                "control_id": control_id,
                "parent_definition_ids": parent_ids,
                "control_kind": kind,
                "symbol": path[-1],
                "declared_value": ";".join(value) if isinstance(value, list) else value,
                "value_type": _value_type(value),
                "source_pointer": pointer,
                "source_refs": [_source_ref(source, pointer)],
                "source_package_sha256": source["source_package_sha256"],
                "source_member_sha256": source["source_member_sha256"],
                "raw_status": raw_status,
                "normalized_status": _STATUS_NORMALIZATION.get(
                    raw_status, "SOURCE_POLICY_NOT_ENABLED"
                ),
                "explicitly_declared": True,
                "unknown_parameter": False,
                "requires_confirmation": True,
                "default_usage_allowed": False,
                "planned_fixture_refs": _fixture_contract_refs(control_id),
                "executable_fixture_refs": [],
                "planned_report_refs": [
                    f"report-contract://KMFA/v1.5/{parent_ids[0]}/control/{control_id}"
                ],
                "report_artifact_refs": [],
                "fixture_status": "PLANNED_NOT_IMPLEMENTED",
                "report_status": "PLANNED_NOT_IMPLEMENTED",
                "runtime_enablement": False,
                "product_implementation_claimed": False,
                "legacy_active_status_inherited": False,
                "blocking_reasons": [
                    "NO_EXECUTABLE_FIXTURE",
                    "NO_TEST_EXECUTION_EVIDENCE",
                    "NO_REPORT_ARTIFACT",
                    "PRODUCT_IMPLEMENTATION_OUT_OF_SCOPE",
                ],
            }
        )

    # Detect anonymous numeric expression literals.  They must be externalized
    # before implementation; they are never accepted as a silent default.
    for node_path, _, definition_id in definition_nodes:
        expression = values.get(node_path + ("expression",))
        if not isinstance(expression, str):
            continue
        for index, literal in enumerate(
            re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])", expression), start=1
        ):
            pointer = f"{_pointer(node_path + ('expression',))}#numeric-literal-{index}"
            control_id = _control_id(pointer)
            rows.append(
                {
                    "control_id": control_id,
                    "parent_definition_ids": [definition_id],
                    "control_kind": "INLINE_LITERAL_REQUIRES_EXTERNALIZATION",
                    "symbol": f"inline_numeric_literal_{index}",
                    "declared_value": literal,
                    "value_type": _value_type(literal),
                    "source_pointer": pointer,
                    "source_refs": [_source_ref(source, pointer)],
                    "source_package_sha256": source["source_package_sha256"],
                    "source_member_sha256": source["source_member_sha256"],
                    "raw_status": str(values[node_path + ("status",)]),
                    "normalized_status": "BLOCKED_REQUIRES_EXTERNALIZATION",
                    "explicitly_declared": False,
                    "unknown_parameter": True,
                    "requires_confirmation": True,
                    "default_usage_allowed": False,
                    "planned_fixture_refs": _fixture_contract_refs(control_id),
                    "executable_fixture_refs": [],
                    "planned_report_refs": [
                        f"report-contract://KMFA/v1.5/{definition_id}/control/{control_id}"
                    ],
                    "report_artifact_refs": [],
                    "fixture_status": "PLANNED_NOT_IMPLEMENTED",
                    "report_status": "PLANNED_NOT_IMPLEMENTED",
                    "runtime_enablement": False,
                    "product_implementation_claimed": False,
                    "legacy_active_status_inherited": False,
                    "blocking_reasons": [
                        "UNKNOWN_INLINE_LITERAL",
                        "NO_EXECUTABLE_FIXTURE",
                        "NO_TEST_EXECUTION_EVIDENCE",
                        "NO_REPORT_ARTIFACT",
                        "PRODUCT_IMPLEMENTATION_OUT_OF_SCOPE",
                    ],
                }
            )
    return rows


def _build_traces(source_package: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    values, lists, source = _load_source(source_package)
    definition_nodes = _definition_nodes(values)
    declared_vocabulary = lists.get(("status_vocabulary", "internal"), [])
    parameter_rows = _parameter_rows(values, source, definition_nodes)
    control_ids_by_definition: dict[str, list[str]] = {
        definition_id: [] for _, _, definition_id in definition_nodes
    }
    for row in parameter_rows:
        for parent_id in row["parent_definition_ids"]:
            control_ids_by_definition[parent_id].append(row["control_id"])

    formula_rows: list[dict[str, Any]] = []
    for node_path, id_field, definition_id in definition_nodes:
        raw_status = str(values.get(node_path + ("status",), ""))
        root_key = _root_key(node_path)
        source_pointer = _pointer(node_path)
        formula_rows.append(
            {
                "definition_id": definition_id,
                "definition_kind": "FORMULA" if id_field == "formula_id" else "MODEL",
                "source_version": str(values.get(node_path + ("version",), "")),
                "raw_status": raw_status,
                "source_status_vocabulary": list(declared_vocabulary),
                "source_status_in_declared_vocabulary": raw_status in declared_vocabulary,
                "normalized_status": _STATUS_NORMALIZATION.get(
                    raw_status, "BLOCKED_UNKNOWN_SOURCE_STATUS"
                ),
                "expression": str(values.get(node_path + ("expression",), "")),
                "source_pointer": source_pointer,
                "source_refs": [_source_ref(source, source_pointer)],
                "source_package_file": source["source_package_file"],
                "source_package_sha256": source["source_package_sha256"],
                "source_member": source["source_member"],
                "source_member_sha256": source["source_member_sha256"],
                "requirement_refs": list(_REQUIREMENT_REFS_BY_ROOT[root_key]),
                "planned_implementation_task_refs": list(
                    _IMPLEMENTATION_TASK_REFS_BY_ROOT[root_key]
                ),
                "control_ids": sorted(control_ids_by_definition[definition_id]),
                "source_test_descriptions": list(lists.get(node_path + ("tests",), [])),
                "planned_fixture_refs": _fixture_contract_refs(definition_id),
                "executable_fixture_refs": [],
                "test_execution_refs": [],
                "planned_report_refs": _planned_report_refs(definition_id, root_key),
                "report_artifact_refs": [],
                "fixture_status": "PLANNED_NOT_IMPLEMENTED",
                "report_status": "PLANNED_NOT_IMPLEMENTED",
                "runtime_implementation_present": False,
                "runtime_enablement": False,
                "product_implementation_claimed": False,
                "legacy_active_status_inherited": False,
                "trace_status": "PLANNED_TRACE_LOCKED_NOT_ENABLED",
                "blocking_reasons": [
                    "NO_EXECUTABLE_FIXTURE",
                    "NO_TEST_EXECUTION_EVIDENCE",
                    "NO_REPORT_ARTIFACT",
                    "PRODUCT_IMPLEMENTATION_OUT_OF_SCOPE",
                ],
            }
        )
    return formula_rows, parameter_rows


def build_formula_trace(source_package: str | Path) -> list[dict[str, Any]]:
    """Return the exact 22-row v1.5 target calculation trace."""

    formulas, _ = _build_traces(source_package)
    return formulas


def build_parameter_trace(source_package: str | Path) -> list[dict[str, Any]]:
    """Return the source-v2 parameter, threshold, and inline-literal inventory."""

    _, parameters = _build_traces(source_package)
    return parameters


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, Mapping):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_float(item) for item in value)
    return False


_FORMULA_LIST_FIELDS = {
    "source_status_vocabulary",
    "source_refs",
    "requirement_refs",
    "planned_implementation_task_refs",
    "control_ids",
    "source_test_descriptions",
    "planned_fixture_refs",
    "executable_fixture_refs",
    "test_execution_refs",
    "planned_report_refs",
    "report_artifact_refs",
    "blocking_reasons",
}
_FORMULA_NONEMPTY_LIST_FIELDS = {
    "source_status_vocabulary",
    "source_refs",
    "requirement_refs",
    "planned_implementation_task_refs",
    "planned_fixture_refs",
    "planned_report_refs",
    "blocking_reasons",
}
_FORMULA_BOOL_FIELDS = {
    "source_status_in_declared_vocabulary",
    "runtime_implementation_present",
    "runtime_enablement",
    "product_implementation_claimed",
    "legacy_active_status_inherited",
}
_PARAMETER_LIST_FIELDS = {
    "parent_definition_ids",
    "source_refs",
    "planned_fixture_refs",
    "executable_fixture_refs",
    "planned_report_refs",
    "report_artifact_refs",
    "blocking_reasons",
}
_PARAMETER_NONEMPTY_LIST_FIELDS = {
    "parent_definition_ids",
    "source_refs",
    "planned_fixture_refs",
    "planned_report_refs",
    "blocking_reasons",
}
_PARAMETER_BOOL_FIELDS = {
    "explicitly_declared",
    "unknown_parameter",
    "requires_confirmation",
    "default_usage_allowed",
    "runtime_enablement",
    "product_implementation_claimed",
    "legacy_active_status_inherited",
}
_EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
_FORBIDDEN_PUBLIC_SUBSTRINGS = (
    "/Users/",
    "/private/",
    "/Volumes/",
    "/home/",
    "/tmp/",
    "KMFA_MetaData",
    "OWNER_NOTIFICATION_EMAIL_TOKEN@",
)


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_strings(item)


def _validate_row_schema(
    row: Mapping[str, Any],
    *,
    row_id: str,
    list_fields: set[str],
    nonempty_list_fields: set[str],
    bool_fields: set[str],
    errors: list[str],
) -> None:
    for field in sorted(list_fields):
        value = row.get(field)
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item for item in value
        ):
            errors.append(f"{row_id}: {field} must be a list[str]")
        elif field in nonempty_list_fields and not value:
            errors.append(f"{row_id}: {field} must be non-empty")
    for field in sorted(bool_fields):
        if type(row.get(field)) is not bool:
            errors.append(f"{row_id}: {field} must be bool")

    for value in _iter_strings(row):
        if _EMAIL_PATTERN.search(value):
            errors.append(f"{row_id}: public-safe email leak")
            break
        if any(token in value for token in _FORBIDDEN_PUBLIC_SUBSTRINGS):
            errors.append(f"{row_id}: public-safe path/raw token leak")
            break


def _validate_ref_schemes(
    row: Mapping[str, Any], *, row_id: str, errors: list[str]
) -> None:
    contracts = {
        "source_refs": "taskpack://",
        "planned_fixture_refs": "fixture-contract://",
        "planned_report_refs": "report-contract://",
    }
    for field, scheme in contracts.items():
        values = row.get(field)
        if isinstance(values, list) and any(
            not isinstance(value, str) or not value.startswith(scheme)
            for value in values
        ):
            errors.append(f"{row_id}: {field} contains an illegal ref scheme")


def _validate_exact_source_rows(
    actual_rows: Sequence[Mapping[str, Any]],
    expected_rows: Sequence[Mapping[str, Any]],
    *,
    id_field: str,
    label: str,
    errors: list[str],
) -> None:
    expected_by_id = {str(row[id_field]): row for row in expected_rows}
    for row in actual_rows:
        row_id = str(row.get(id_field, "<missing>"))
        expected = expected_by_id.get(row_id)
        if expected is None:
            continue
        if set(row) != set(expected):
            missing = sorted(set(expected) - set(row))
            extra = sorted(set(row) - set(expected))
            errors.append(
                f"{row_id}: {label} schema drift; missing={missing}, extra={extra}"
            )
        for field, expected_value in expected.items():
            actual_value = row.get(field)
            if type(actual_value) is not type(expected_value):
                errors.append(
                    f"{row_id}: {field} type drift; "
                    f"expected={type(expected_value).__name__}, "
                    f"actual={type(actual_value).__name__}"
                )
            elif actual_value != expected_value:
                errors.append(f"{row_id}: {field} differs from authoritative source")


def validate_formula_parameter_trace(
    formulas: Sequence[Mapping[str, Any]],
    parameters: Sequence[Mapping[str, Any]],
    source_package: str | Path = DEFAULT_SOURCE_PACKAGE,
) -> list[str]:
    """Validate trace completeness while keeping all product enablement closed."""

    errors: list[str] = []
    if len(formulas) != 22:
        errors.append(f"formula/model definition count must be 22, got {len(formulas)}")
    formula_ids = [str(row.get("definition_id", "")) for row in formulas]
    if len(formula_ids) != len(set(formula_ids)):
        errors.append("duplicate formula/model definition ID")
    if set(formula_ids) != EXPECTED_DEFINITION_IDS:
        errors.append("formula/model definition universe drift")
    raw_status_counts = Counter(str(row.get("raw_status", "")) for row in formulas)
    if dict(raw_status_counts) != EXPECTED_RAW_STATUS_COUNTS:
        errors.append(f"raw source status counts drifted: {dict(raw_status_counts)}")

    formula_by_id = {str(row.get("definition_id", "")): row for row in formulas}
    for row in formulas:
        definition_id = str(row.get("definition_id", "<missing>"))
        _validate_row_schema(
            row,
            row_id=definition_id,
            list_fields=_FORMULA_LIST_FIELDS,
            nonempty_list_fields=_FORMULA_NONEMPTY_LIST_FIELDS,
            bool_fields=_FORMULA_BOOL_FIELDS,
            errors=errors,
        )
        _validate_ref_schemes(row, row_id=definition_id, errors=errors)
        raw_status = str(row.get("raw_status", ""))
        expected_normalized = _STATUS_NORMALIZATION.get(raw_status)
        if expected_normalized is None:
            errors.append(f"{definition_id}: unknown source status {raw_status!r}")
        elif row.get("normalized_status") != expected_normalized:
            errors.append(f"{definition_id}: source status normalization mismatch")
        expected_in_vocab = raw_status == "PROPOSED"
        if row.get("source_status_in_declared_vocabulary") is not expected_in_vocab:
            errors.append(f"{definition_id}: status-vocabulary mismatch not explicit")
        if row.get("source_status_vocabulary") != [
            "PROPOSED",
            "VERIFIED",
            "DEPRECATED",
            "BLOCKED",
        ]:
            errors.append(f"{definition_id}: declared status vocabulary drift")
        if not row.get("source_refs"):
            errors.append(f"{definition_id}: source reference missing")
        if row.get("source_package_sha256") != SOURCE_PACKAGE_SHA256:
            errors.append(f"{definition_id}: source package hash mismatch")
        if row.get("source_member_sha256") != FORMULA_SOURCE_SHA256:
            errors.append(f"{definition_id}: source member hash mismatch")
        if not row.get("planned_fixture_refs"):
            errors.append(f"{definition_id}: planned fixture contract missing")
        if not row.get("planned_report_refs"):
            errors.append(f"{definition_id}: planned report contract missing")
        if row.get("fixture_status") != "PLANNED_NOT_IMPLEMENTED":
            errors.append(f"{definition_id}: fixture status must remain planned")
        if row.get("report_status") != "PLANNED_NOT_IMPLEMENTED":
            errors.append(f"{definition_id}: report status must remain planned")
        if row.get("executable_fixture_refs"):
            errors.append(f"{definition_id}: executable fixture is outside S02-P2")
        if row.get("test_execution_refs"):
            errors.append(f"{definition_id}: test execution evidence is outside S02-P2")
        if row.get("report_artifact_refs"):
            errors.append(f"{definition_id}: report artifact is outside S02-P2")
        if row.get("runtime_implementation_present") is not False:
            errors.append(f"{definition_id}: runtime implementation must remain false")
        if row.get("runtime_enablement") is not False:
            errors.append(f"{definition_id}: runtime enablement must remain false")
        if row.get("product_implementation_claimed") is not False:
            errors.append(f"{definition_id}: product implementation claim must remain false")
        if row.get("legacy_active_status_inherited") is not False:
            errors.append(f"{definition_id}: legacy active status cannot be inherited")
        descriptions = set(row.get("source_test_descriptions") or [])
        executable = set(row.get("executable_fixture_refs") or [])
        if descriptions & executable:
            errors.append(f"{definition_id}: descriptive tests misclassified as fixtures")
        if _contains_float(row):
            errors.append(f"{definition_id}: binary float found in formula trace")

    if len(parameters) != EXPECTED_PARAMETER_COUNT:
        errors.append(
            f"parameter/threshold count must be {EXPECTED_PARAMETER_COUNT}, got {len(parameters)}"
        )
    parameter_ids = [str(row.get("control_id", "")) for row in parameters]
    if len(parameter_ids) != len(set(parameter_ids)):
        errors.append("duplicate parameter/threshold control ID")
    control_counts = Counter(str(row.get("control_kind", "")) for row in parameters)
    if dict(control_counts) != EXPECTED_CONTROL_KIND_COUNTS:
        errors.append(f"parameter/threshold kind counts drifted: {dict(control_counts)}")

    expected_control_ids_by_definition: dict[str, set[str]] = {
        definition_id: set() for definition_id in formula_by_id
    }
    for row in parameters:
        control_id = str(row.get("control_id", "<missing>"))
        _validate_row_schema(
            row,
            row_id=control_id,
            list_fields=_PARAMETER_LIST_FIELDS,
            nonempty_list_fields=_PARAMETER_NONEMPTY_LIST_FIELDS,
            bool_fields=_PARAMETER_BOOL_FIELDS,
            errors=errors,
        )
        _validate_ref_schemes(row, row_id=control_id, errors=errors)
        parent_ids = [str(item) for item in row.get("parent_definition_ids") or []]
        if not parent_ids:
            errors.append(f"{control_id}: calculation parent missing")
        for parent_id in parent_ids:
            if parent_id not in formula_by_id:
                errors.append(f"{control_id}: unknown calculation parent {parent_id}")
            else:
                expected_control_ids_by_definition[parent_id].add(control_id)
        if row.get("declared_value") in {None, ""}:
            errors.append(f"{control_id}: declared value missing")
        if not row.get("source_refs"):
            errors.append(f"{control_id}: source reference missing")
        if not row.get("planned_fixture_refs"):
            errors.append(f"{control_id}: planned fixture contract missing")
        if not row.get("planned_report_refs"):
            errors.append(f"{control_id}: planned report contract missing")
        if row.get("fixture_status") != "PLANNED_NOT_IMPLEMENTED":
            errors.append(f"{control_id}: fixture status must remain planned")
        if row.get("report_status") != "PLANNED_NOT_IMPLEMENTED":
            errors.append(f"{control_id}: report status must remain planned")
        if row.get("executable_fixture_refs"):
            errors.append(f"{control_id}: executable fixture is outside S02-P2")
        if row.get("report_artifact_refs"):
            errors.append(f"{control_id}: report artifact is outside S02-P2")
        if row.get("runtime_enablement") is not False:
            errors.append(f"{control_id}: runtime enablement must remain false")
        if row.get("product_implementation_claimed") is not False:
            errors.append(f"{control_id}: product implementation claim must remain false")
        if row.get("legacy_active_status_inherited") is not False:
            errors.append(f"{control_id}: legacy active status cannot be inherited")
        if row.get("default_usage_allowed") is not False:
            errors.append(f"{control_id}: silent/default runtime use is forbidden")
        if row.get("requires_confirmation") is not True:
            errors.append(f"{control_id}: confirmation requirement missing")
        if row.get("control_kind") == "DEFAULT" and row.get("explicitly_declared") is not True:
            errors.append(f"{control_id}: source default must be explicitly declared")
        if row.get("unknown_parameter") is True:
            if row.get("control_kind") != "INLINE_LITERAL_REQUIRES_EXTERNALIZATION":
                errors.append(f"{control_id}: unknown parameter kind mismatch")
            if row.get("explicitly_declared") is not False:
                errors.append(f"{control_id}: unknown inline literal cannot be declared control")
            if "UNKNOWN_INLINE_LITERAL" not in (row.get("blocking_reasons") or []):
                errors.append(f"{control_id}: unknown inline literal blocker missing")
        elif row.get("explicitly_declared") is not True:
            errors.append(f"{control_id}: explicit source control flag missing")
        if _contains_float(row):
            errors.append(f"{control_id}: binary float found in parameter trace")

    unknown_rows = [row for row in parameters if row.get("unknown_parameter") is True]
    if len(unknown_rows) != 1:
        errors.append(f"unknown inline parameter count must be 1, got {len(unknown_rows)}")
    elif not (
        unknown_rows[0].get("parent_definition_ids") == ["CASH-RUNWAY-001"]
        and unknown_rows[0].get("declared_value") == "1"
    ):
        errors.append("cash runway inline denominator literal trace drift")

    for definition_id, row in formula_by_id.items():
        actual = set(str(item) for item in row.get("control_ids") or [])
        if actual != expected_control_ids_by_definition[definition_id]:
            errors.append(f"{definition_id}: parameter/control binding drift")

    try:
        expected_formulas, expected_parameters = _build_traces(source_package)
    except (OSError, ValueError, TraceSourceError) as exc:
        errors.append(f"authoritative formula source rebuild failed: {exc}")
    else:
        _validate_exact_source_rows(
            formulas,
            expected_formulas,
            id_field="definition_id",
            label="formula/model trace",
            errors=errors,
        )
        _validate_exact_source_rows(
            parameters,
            expected_parameters,
            id_field="control_id",
            label="parameter/control trace",
            errors=errors,
        )
    return errors


def _formula_registry_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(
        re.finditer(
            r'^  - formula_id:\s*"?([^"\n]+?)"?\s*$', text, re.MULTILINE
        )
    )
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[match.start() : end]))
    return blocks


def _block_scalar(block: str, key: str) -> str:
    match = re.search(
        rf'^    {re.escape(key)}:\s*(?:"([^"]*)"|([^\n#]+))\s*$',
        block,
        re.MULTILINE,
    )
    if not match:
        return ""
    return (match.group(1) if match.group(1) is not None else match.group(2)).strip()


_V015_S02_GOVERNANCE_ID_TOKENS = ("V015-S02-P2", "V015-S02-P3")


def _is_v015_s02_governance_id(value: str) -> bool:
    return any(token in value for token in _V015_S02_GOVERNANCE_ID_TOKENS)


def summarize_legacy_governance(repo_root: str | Path = ".") -> dict[str, Any]:
    """Summarize legacy governance coverage without inheriting product status."""

    root = Path(repo_root)
    governance = root / "KMFA" / "docs" / "governance"
    formula_text = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
    all_formula_blocks = _formula_registry_blocks(formula_text)
    # S02-P2/P3 phase-governance formulas are not part of the frozen 322-row
    # product baseline.  Exclude predecessor and successor governance-only IDs
    # so later phase registration cannot inflate historical product coverage.
    formula_blocks = [
        item for item in all_formula_blocks if not _is_v015_s02_governance_id(item[0])
    ]
    formula_ids = [item[0] for item in formula_blocks]
    formula_statuses = Counter(_block_scalar(block, "status") for _, block in formula_blocks)
    formula_fact_levels = Counter(
        _block_scalar(block, "fact_level") or "MISSING" for _, block in formula_blocks
    )
    formula_model_ids = Counter(_block_scalar(block, "model_id") for _, block in formula_blocks)

    with (governance / "parameter_registry.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        all_parameters = list(csv.DictReader(handle))
    parameters = [
        row
        for row in all_parameters
        if not _is_v015_s02_governance_id(row["formula_id"])
    ]
    with (governance / "TRACEABILITY_MATRIX.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        all_trace_rows = list(csv.DictReader(handle))
    trace_rows = [
        row
        for row in all_trace_rows
        if not _is_v015_s02_governance_id(row["formula_id"])
        and not _is_v015_s02_governance_id(row["requirement_id"])
    ]
    model_text = (governance / "model_registry.yaml").read_text(encoding="utf-8")
    all_model_ids = re.findall(
        r'^  - model_id: "([^"]+)"\s*$', model_text, re.MULTILINE
    )
    # Keep the frozen product-governance baseline independent from this
    # phase governance registrations.  Otherwise S02-P2/P3 planning models
    # would inflate the legacy 8-model cohort and could be mistaken for a
    # collision with a source-pack product definition.
    model_ids = [
        model_id
        for model_id in all_model_ids
        if not _is_v015_s02_governance_id(model_id)
    ]

    traced_formula_ids = {
        item.strip()
        for row in trace_rows
        for item in row["formula_id"].split(";")
        if item.strip()
    }
    traced_parameter_ids = {
        item.strip()
        for row in trace_rows
        for item in row["parameter_id"].split(";")
        if item.strip()
    }
    parameter_ids = {row["parameter_id"] for row in parameters}
    source_definition_overlap = EXPECTED_DEFINITION_IDS & (
        set(formula_ids) | set(model_ids)
    )
    no_report_like = 0
    for _, block in formula_blocks:
        if "/human/" not in block and "report" not in block.lower():
            no_report_like += 1

    return {
        "scope_class": "LEGACY_GOVERNANCE_EVIDENCE_ONLY",
        "current_formula_count_including_s02_p2_governance": len(all_formula_blocks),
        "formula_count": len(formula_blocks),
        "formula_status_counts": dict(formula_statuses),
        "formula_fact_level_counts": dict(formula_fact_levels),
        "formula_model_id_counts": dict(formula_model_ids),
        "formula_explicit_source_refs_count": sum(
            1 for _, block in formula_blocks if re.search(r"^    source_refs:", block, re.MULTILINE)
        ),
        "formula_explicit_fixture_refs_count": sum(
            1 for _, block in formula_blocks if re.search(r"^    fixture_refs:", block, re.MULTILINE)
        ),
        "formula_explicit_report_refs_count": sum(
            1 for _, block in formula_blocks if re.search(r"^    report_refs:", block, re.MULTILINE)
        ),
        "formula_without_report_like_evidence_count": no_report_like,
        "parameter_count": len(parameters),
        "current_parameter_count_including_s02_p2_governance": len(all_parameters),
        "parameter_status_counts": dict(Counter(row["status"] for row in parameters)),
        "parameter_fact_level_counts": dict(
            Counter(row["fact_level"] for row in parameters)
        ),
        "parameter_precommit_pending_count": sum(
            row["last_verified_commit"] == "precommit-pending" for row in parameters
        ),
        "parameter_pending_local_commit_evidence_count": sum(
            row["evidence_hash"] == "pending_local_commit" for row in parameters
        ),
        "model_count": len(model_ids),
        "current_model_count_including_s02_p2_governance": len(all_model_ids),
        "traceability_row_count": len(trace_rows),
        "current_traceability_row_count_including_s02_p2_governance": len(
            all_trace_rows
        ),
        "traceability_formula_covered_count": len(set(formula_ids) & traced_formula_ids),
        "traceability_formula_missing_count": len(set(formula_ids) - traced_formula_ids),
        "traceability_parameter_covered_count": len(parameter_ids & traced_parameter_ids),
        "traceability_parameter_missing_count": len(parameter_ids - traced_parameter_ids),
        "v15_source_definition_overlap_count": len(source_definition_overlap),
        "v15_source_definition_overlap_ids": sorted(source_definition_overlap),
        "runtime_enablement_inherited": False,
        "product_implementation_claimed": False,
    }


__all__ = [
    "EXPECTED_CONTROL_KIND_COUNTS",
    "EXPECTED_DEFINITION_IDS",
    "EXPECTED_PARAMETER_COUNT",
    "EXPECTED_RAW_STATUS_COUNTS",
    "FORMULA_SOURCE_SHA256",
    "SOURCE_PACKAGE_SHA256",
    "TraceSourceError",
    "build_formula_trace",
    "build_parameter_trace",
    "summarize_legacy_governance",
    "validate_formula_parameter_trace",
]
