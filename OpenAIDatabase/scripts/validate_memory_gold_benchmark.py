#!/usr/bin/env python3
"""Independently validate PAM1.0013 Gold schema, distribution and leak gates."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from privacy_guard import credential_exclusion_hits  # noqa: E402


DEFAULT_CONFIG = Path("config/evaluation/memory_gold_benchmark_v1.json")
FORBIDDEN_ANSWER_KEYS = {"answer", "expected_answer", "gold_answer", "answer_text"}
LOCAL_ABSOLUTE_PATH = re.compile(r"(?:^|[\s\"'])/(?:Users|home|private|tmp)/|[A-Za-z]:\\\\")
CHINESE_CHARACTER = re.compile(r"[\u3400-\u9fff]")
TECHNICAL_ENGLISH = re.compile(r"\b(?:current|record|scope|session|provenance|UNKNOWN|Agent|valid_time|update|abstain|memory|verified|authorized|conflict|retired|candidate|bridge|handoff)\b")


class BenchmarkValidationError(ValueError):
    """Raised for bounded loader failures without echoing case payloads."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise BenchmarkValidationError("duplicate_json_key")
        value[key] = item
    return value


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], Counter[str]]:
    cases: list[dict[str, Any]] = []
    errors: Counter[str] = Counter()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return cases, Counter({"dataset_unreadable": 1})
    if text and not text.endswith("\n"):
        errors["missing_terminal_newline"] += 1
    for line in text.splitlines():
        if not line.strip():
            errors["blank_jsonl_line"] += 1
            continue
        try:
            value = json.loads(line, object_pairs_hook=_strict_object)
        except (json.JSONDecodeError, BenchmarkValidationError):
            errors["invalid_jsonl_record"] += 1
            continue
        if not isinstance(value, dict):
            errors["non_object_jsonl_record"] += 1
            continue
        cases.append(value)
    return cases, errors


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise BenchmarkValidationError("external_schema_ref_forbidden")
    value: Any = root
    for part in ref[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(value, dict):
        raise BenchmarkValidationError("schema_ref_not_object")
    return value


def _is_rfc3339(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def schema_errors(
    instance: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    path: str = "$",
) -> list[str]:
    if "$ref" in schema:
        return schema_errors(instance, _resolve_ref(root, str(schema["$ref"])), root, path)
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_json_type_matches(instance, str(item)) for item in allowed):
            return [f"{path}:type"]
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}:const")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}:enum")
    if isinstance(instance, dict):
        properties = schema.get("properties") or {}
        for name in schema.get("required") or []:
            if name not in instance:
                errors.append(f"{path}:required")
        if schema.get("additionalProperties") is False:
            errors.extend(f"{path}:additional" for name in instance if name not in properties)
        for name, child in properties.items():
            if name in instance:
                errors.extend(schema_errors(instance[name], child, root, f"{path}.{name}"))
    if isinstance(instance, list):
        if len(instance) < int(schema.get("minItems", 0)):
            errors.append(f"{path}:minItems")
        if "maxItems" in schema and len(instance) > int(schema["maxItems"]):
            errors.append(f"{path}:maxItems")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in instance]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{path}:uniqueItems")
        child = schema.get("items")
        if isinstance(child, dict):
            for index, item in enumerate(instance):
                errors.extend(schema_errors(item, child, root, f"{path}[{index}]"))
    if isinstance(instance, str):
        if len(instance) < int(schema.get("minLength", 0)):
            errors.append(f"{path}:minLength")
        pattern = schema.get("pattern")
        if pattern and re.search(str(pattern), instance) is None:
            errors.append(f"{path}:pattern")
        if schema.get("format") == "date-time" and not _is_rfc3339(instance):
            errors.append(f"{path}:date-time")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}:minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}:maximum")
    return errors


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(str(key) for key in value)
        for child in value.values():
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_walk_keys(child))
    return keys


def _effective(record: dict[str, Any], as_of: str) -> bool:
    valid_time = record["valid_time"]
    return valid_time["from"] <= as_of and (valid_time["to"] is None or as_of < valid_time["to"])


def _forbidden_stale(case: dict[str, Any], records: dict[str, dict[str, Any]]) -> bool:
    as_of = case["as_of"]["valid_time"]
    return any(
        records[record_id]["status"] == "retired"
        or (
            records[record_id]["valid_time"]["to"] is not None
            and records[record_id]["valid_time"]["to"] <= as_of
        )
        for record_id in case["forbidden_ids"]
        if record_id in records
    )


def validate_cases(
    config: dict[str, Any],
    schema: dict[str, Any],
    cases: list[dict[str, Any]],
    loader_errors: Counter[str] | None = None,
) -> dict[str, Any]:
    errors = Counter(loader_errors or {})
    categories = [str(value) for value in config["categories"]]
    category_counts = Counter(str(case.get("category")) for case in cases)
    case_ids = [str(case.get("case_id")) for case in cases]
    query_signatures: list[str] = []
    payload_signatures: list[str] = []
    stale_count = 0
    abstention_count = 0
    hard_negative_complete = 0
    chinese_primary_count = 0
    technical_english_count = 0
    alias_count = 0
    noise_count = 0
    expected_source_ids = {str(row["id"]) for row in config["source_definitions"]}
    roles = config["roles"]

    if len(cases) != int(config["case_count"]):
        errors["case_count_mismatch"] += 1
    if set(category_counts) != set(categories):
        errors["category_set_mismatch"] += 1
    for category in categories:
        if category_counts[category] != int(config["cases_per_category"]):
            errors["category_distribution_mismatch"] += 1

    for case in cases:
        schema_failure_count = len(schema_errors(case, schema, schema))
        if schema_failure_count:
            errors["schema_validation_error"] += schema_failure_count
            continue
        case_id = case["case_id"]
        category = case["category"]
        if not case_id.startswith(f"gold_{category}_"):
            errors["case_id_category_mismatch"] += 1
        if case["fixed_seed"] != config["fixed_seed"]:
            errors["fixed_seed_mismatch"] += 1
        records = {record["id"]: record for record in case["state"]}
        if len(records) != len(case["state"]):
            errors["duplicate_state_id"] += 1
        known_ids = set(records)
        expected = set(case["expected_ids"])
        forbidden = set(case["forbidden_ids"])
        hard_negatives = set(case["hard_negative_ids"])
        if not expected <= known_ids or not forbidden <= known_ids:
            errors["unknown_gold_record_id"] += 1
        if expected & forbidden:
            errors["expected_forbidden_overlap"] += 1
        if not hard_negatives or not hard_negatives <= forbidden:
            errors["hard_negative_contract"] += 1
        else:
            hard_negative_complete += 1
        if case["should_abstain"] != (not expected):
            errors["abstention_label_mismatch"] += 1
        abstention_count += int(case["should_abstain"])
        if case["should_abstain"] and not any("UNKNOWN" in trait for trait in case["answer_traits"]):
            errors["abstention_trait_missing"] += 1
        for record_id in expected:
            if record_id not in records:
                continue
            record = records[record_id]
            historical_temporal = category == "temporal" and record["status"] == "retired"
            if (
                record["authorization"] != "allowed"
                or record["verification_state"] != "verified"
                or not _effective(record, case["as_of"]["valid_time"])
                or (record["status"] != "active" and not historical_temporal)
            ):
                errors["ineligible_expected_record"] += 1
        computed_stale = _forbidden_stale(case, records)
        if bool(case["stale_or_retired_trap"]) != computed_stale:
            errors["stale_trap_label_mismatch"] += 1
        stale_count += int(case["stale_or_retired_trap"])
        if not set(case["source_definition_refs"]) <= expected_source_ids:
            errors["unknown_source_definition"] += 1
        provenance = case["gold_provenance"]
        role_values = {
            provenance["author_role"],
            provenance["approval_role"],
            provenance["tested_algorithm_role"],
        }
        if len(role_values) != 3:
            errors["gold_role_separation"] += 1
        if (
            provenance["author_role"] != roles["generator"]
            or provenance["approval_role"] != roles["approver"]
            or provenance["tested_algorithm_role"] != roles["tested_algorithm"]
            or provenance["approval_mechanism"] != roles["approval_mechanism"]
            or provenance["algorithm_dependency_count"] != 0
            or provenance["human_approval_claimed"]
        ):
            errors["gold_provenance_mismatch"] += 1
        if FORBIDDEN_ANSWER_KEYS & _walk_keys(case):
            errors["literal_answer_field"] += 1
        query_payload = _canonical(case["query"])
        full_payload = _canonical(case)
        if LOCAL_ABSOLUTE_PATH.search(full_payload):
            errors["local_absolute_path_leak"] += 1
        if credential_exclusion_hits(full_payload):
            errors["credential_shape_leak"] += 1
        expected_statements = [
            records[record_id]["statement"]
            for record_id in expected
            if record_id in records
        ]
        if any(record_id in query_payload for record_id in expected) or any(
            _normalized(statement) in _normalized(query_payload) for statement in expected_statements
        ):
            errors["query_answer_leak"] += 1
        query_signatures.append(_normalized(case["query"]["text"]))
        stripped = copy.deepcopy(case)
        stripped.pop("case_id", None)
        payload_signatures.append(hashlib.sha256(_canonical(stripped).encode("utf-8")).hexdigest())
        combined_text = case["query"]["text"] + " " + " ".join(case["answer_traits"])
        chinese_primary_count += int(bool(CHINESE_CHARACTER.search(combined_text)))
        technical_english_count += int(bool(TECHNICAL_ENGLISH.search(combined_text)))
        alias_count += int(bool(case["query"]["aliases"]) and all(record["aliases"] for record in case["state"]))
        noise_count += int(bool(case["query"]["noise"].strip()))

    duplicate_case_ids = len(case_ids) - len(set(case_ids))
    duplicate_queries = len(query_signatures) - len(set(query_signatures))
    duplicate_payloads = len(payload_signatures) - len(set(payload_signatures))
    if duplicate_case_ids:
        errors["duplicate_case_id"] += duplicate_case_ids
    if duplicate_queries:
        errors["duplicate_query"] += duplicate_queries
    if duplicate_payloads:
        errors["duplicate_case_payload"] += duplicate_payloads

    denominator = len(cases) or 1
    stale_ratio = stale_count / denominator
    abstention_ratio = abstention_count / denominator
    chinese_ratio = chinese_primary_count / denominator
    alias_ratio = alias_count / denominator
    noise_ratio = noise_count / denominator
    minimums = config["minimums"]
    if stale_ratio < float(minimums["stale_or_retired_ratio"]):
        errors["stale_ratio_below_minimum"] += 1
    if abstention_ratio < float(minimums["abstention_ratio"]):
        errors["abstention_ratio_below_minimum"] += 1
    if hard_negative_complete != len(cases):
        errors["hard_negative_coverage_incomplete"] += 1
    if chinese_ratio < float(minimums["chinese_primary_ratio"]):
        errors["chinese_primary_coverage_incomplete"] += 1
    if technical_english_count != len(cases):
        errors["technical_english_coverage_incomplete"] += 1
    if alias_ratio < float(minimums["alias_coverage_ratio"]):
        errors["alias_coverage_incomplete"] += 1
    if noise_ratio < float(minimums["noise_coverage_ratio"]):
        errors["noise_coverage_incomplete"] += 1

    metrics = {
        "case_count": len(cases),
        "category_count": len(category_counts),
        "category_distribution": {category: category_counts[category] for category in categories},
        "stale_or_retired_trap_count": stale_count,
        "stale_or_retired_ratio": round(stale_ratio, 6),
        "abstention_count": abstention_count,
        "abstention_ratio": round(abstention_ratio, 6),
        "hard_negative_complete_case_count": hard_negative_complete,
        "chinese_primary_case_count": chinese_primary_count,
        "technical_english_case_count": technical_english_count,
        "alias_covered_case_count": alias_count,
        "noise_covered_case_count": noise_count,
        "duplicate_case_id_count": duplicate_case_ids,
        "duplicate_query_count": duplicate_queries,
        "duplicate_case_payload_count": duplicate_payloads,
        "schema_validation_error_count": errors["schema_validation_error"],
        "leak_error_count": sum(
            errors[code]
            for code in (
                "literal_answer_field",
                "local_absolute_path_leak",
                "credential_shape_leak",
                "query_answer_leak",
            )
        ),
        "gold_role_separation_error_count": errors["gold_role_separation"] + errors["gold_provenance_mismatch"],
    }
    return {
        "status": "PASS" if not errors else "FAIL",
        "task_id": config["task_id"],
        "acceptance_id": config["acceptance_id"],
        "metrics": metrics,
        "error_counts": dict(sorted((key, count) for key, count in errors.items() if count)),
        "writes_files": False,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=DATABASE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--schema", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    config_path = args.config if args.config.is_absolute() else database_dir / args.config
    try:
        config = load_json(config_path)
        dataset_path = args.dataset or Path(config["paths"]["dataset"])
        schema_path = args.schema or Path(config["paths"]["schema"])
        if not dataset_path.is_absolute():
            dataset_path = database_dir / dataset_path
        if not schema_path.is_absolute():
            schema_path = database_dir / schema_path
        schema = load_json(schema_path)
        cases, loader_errors = load_jsonl(dataset_path)
        result = validate_cases(config, schema, cases, loader_errors)
    except (OSError, UnicodeError, json.JSONDecodeError, BenchmarkValidationError, KeyError, TypeError) as exc:
        result = {
            "status": "FAIL",
            "task_id": "TSK.OpenAIDatabase.PAM1.0013",
            "acceptance_id": "ACC.OpenAIDatabase.PAM1.0013",
            "metrics": {},
            "error_counts": {type(exc).__name__: 1},
            "writes_files": False,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
