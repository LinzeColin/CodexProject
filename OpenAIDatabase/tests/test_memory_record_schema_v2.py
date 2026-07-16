from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = DATABASE_DIR / "config/memory.schema.json"
LEGACY_SCHEMA_PATH = DATABASE_DIR / "config/memory_schema.json"
MIGRATION_PATH = DATABASE_DIR / "config/memory.migration.v1-to-v2.json"
FIXTURE_DIR = DATABASE_DIR / "tests/fixtures/memory_record_v2"
VALID_FIXTURE_PATH = FIXTURE_DIR / "valid_records.json"
INVALID_FIXTURE_PATH = FIXTURE_DIR / "invalid_records.json"
LEGACY_ACTIVE_PATH = DATABASE_DIR / "data/memory/active/active_memory.jsonl"

SEMANTIC_REQUIRED_FIELDS = {
    "id",
    "memory_key",
    "kind",
    "statement",
    "status",
    "scope",
    "source",
    "valid_time",
    "recorded_time",
    "supersession",
    "conflict",
    "confidence",
    "importance",
    "verification",
    "aliases",
    "tags",
    "negative_triggers",
    "sensitivity",
    "hash",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_type_matches(value: Any, expected: str) -> bool:
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
    raise AssertionError(f"unsupported JSON Schema type in test validator: {expected}")


def resolve_local_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise AssertionError(f"only local refs are permitted: {ref}")
    value: Any = root_schema
    for part in ref[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(value, dict):
        raise AssertionError(f"ref does not resolve to a schema object: {ref}")
    return value


def is_rfc3339(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_schema_instance(
    instance: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "$",
) -> list[str]:
    if "$ref" in schema:
        return validate_schema_instance(instance, resolve_local_ref(root_schema, schema["$ref"]), root_schema, path)

    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(json_type_matches(instance, item) for item in allowed):
            return [f"{path}: type must be {allowed}"]

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: value must equal const")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value is outside enum")
    if "not" in schema and not validate_schema_instance(instance, schema["not"], root_schema, path):
        errors.append(f"{path}: value matches forbidden schema")

    for index, branch in enumerate(schema.get("allOf", [])):
        errors.extend(validate_schema_instance(instance, branch, root_schema, f"{path}.allOf[{index}]"))

    if "if" in schema:
        condition_matches = not validate_schema_instance(instance, schema["if"], root_schema, path)
        branch_name = "then" if condition_matches else "else"
        if branch_name in schema:
            errors.extend(validate_schema_instance(instance, schema[branch_name], root_schema, path))

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for name in required:
            if name not in instance:
                errors.append(f"{path}: missing required field {name}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for name in instance:
                if name not in properties:
                    errors.append(f"{path}: additional field {name}")
        for name, child_schema in properties.items():
            if name in instance:
                errors.extend(validate_schema_instance(instance[name], child_schema, root_schema, f"{path}.{name}"))

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: too few items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in instance]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{path}: duplicate array items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                errors.extend(validate_schema_instance(value, item_schema, root_schema, f"{path}[{index}]"))

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: string shorter than minLength")
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            errors.append(f"{path}: string does not match pattern")
        if schema.get("format") == "date-time" and not is_rfc3339(instance):
            errors.append(f"{path}: invalid RFC3339 date-time")

    return errors


def normalize_for_hash(value: Any) -> Any:
    if isinstance(value, float):
        raise ValueError("floating-point values are forbidden by openai-memory-json-v1")
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize_for_hash(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_for_hash(value[key]) for key in sorted(value)}
    return value


def record_hash(record: dict[str, Any]) -> str:
    payload = copy.deepcopy(record)
    payload.pop("hash", None)
    encoded = json.dumps(
        normalize_for_hash(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def dataset_errors(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_record_id")

    active_keys = Counter(
        (
            record["memory_key"],
            record["scope"]["type"],
            record["scope"]["key"],
        )
        for record in records
        if record["status"] == "active"
    )
    if any(count > 1 for count in active_keys.values()):
        errors.append("duplicate_active_key_scope")

    known_ids = set(ids)
    for record in records:
        refs = list(record["supersession"]["supersedes"])
        if record["supersession"]["superseded_by"]:
            refs.append(record["supersession"]["superseded_by"])
        refs.extend(record["conflict"]["with"])
        if any(ref not in known_ids for ref in refs):
            errors.append(f"unresolved_reference:{record['id']}")
    return errors


def semantic_rule_codes(record: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    if record["source"]["type"] == "model_inference" and record["status"] == "active":
        codes.add("model_inference_active")
    if record["sensitivity"]["credential_present"]:
        codes.add("credential_presence")
    if record["status"] == "active" and record["conflict"]["state"] == "unresolved":
        codes.add("unresolved_active_conflict")
    if record["status"] == "active" and record["verification"]["state"] != "verified":
        codes.add("unverified_active")
    if record["hash"]["value"] != record_hash(record):
        codes.add("hash_mismatch")
    return codes


class MemoryRecordSchemaV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.migration = load_json(MIGRATION_PATH)
        cls.valid_records = load_json(VALID_FIXTURE_PATH)
        cls.invalid_cases = load_json(INVALID_FIXTURE_PATH)

    def test_schema_has_all_required_contract_fields_and_fail_closed_rules(self) -> None:
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(set(self.schema["required"]) - {"schema_version"}, SEMANTIC_REQUIRED_FIELDS)
        self.assertEqual(len(SEMANTIC_REQUIRED_FIELDS), 19)
        self.assertEqual(
            set(self.schema["properties"]["source"]["properties"]["type"]["enum"]),
            {"explicit_user", "repository_evidence", "raw_import", "model_inference"},
        )
        self.assertEqual(self.schema["x-query-contract"]["default_status"], "active")
        self.assertEqual(
            self.schema["x-dataset-invariants"]["max_unresolved_active_per_memory_key_and_scope"],
            1,
        )
        self.assertEqual(self.schema["x-dataset-invariants"]["active_duplicate_conflict_max"], 0)
        self.assertFalse(self.schema["x-dataset-invariants"]["embedding_as_unique_decision"])
        self.assertIn("transitions", self.schema["properties"]["recorded_time"]["properties"])
        self.assertEqual(
            self.schema["x-lifecycle-contract"]["acceptance_id"],
            "ACC.OpenAIDatabase.PAM1.0010",
        )
        self.assertEqual(
            self.schema["x-forgetting-contract"]["acceptance_id"],
            "ACC.OpenAIDatabase.PAM1.0011",
        )
        self.assertEqual(
            self.schema["x-query-contract"]["include_inactive_mode"],
            "audit_only_never_answer",
        )
        self.assertFalse(self.schema["x-forgetting-contract"]["absence_inference"])

    def test_valid_fixtures_pass_schema_hash_reference_and_uniqueness_gates(self) -> None:
        self.assertEqual(len(self.valid_records), 4)
        for record in self.valid_records:
            self.assertEqual(
                validate_schema_instance(record, self.schema, self.schema),
                [],
                record["id"],
            )
            self.assertEqual(record["hash"]["value"], record_hash(record), record["id"])
        self.assertEqual(dataset_errors(self.valid_records), [])
        inferred = [record for record in self.valid_records if record["source"]["type"] == "model_inference"]
        self.assertTrue(inferred)
        self.assertTrue(all(record["status"] != "active" for record in inferred))

    def test_invalid_fixtures_are_rejected_at_the_declared_layer(self) -> None:
        self.assertEqual(len(self.invalid_cases), 6)
        for case in self.invalid_cases:
            records = case["records"]
            schema_errors = [validate_schema_instance(record, self.schema, self.schema) for record in records]
            rule_codes = set().union(*(semantic_rule_codes(record) for record in records))
            if case["expected_layer"] == "record_schema":
                self.assertTrue(any(schema_errors), case["case"])
                self.assertIn(case["expected_rule"], rule_codes, case["case"])
                self.assertNotIn("hash_mismatch", rule_codes, case["case"])
            elif case["expected_layer"] == "record_hash":
                self.assertTrue(all(not errors for errors in schema_errors), case["case"])
                self.assertEqual(rule_codes, {"hash_mismatch"}, case["case"])
            elif case["expected_layer"] == "dataset":
                self.assertTrue(all(not errors for errors in schema_errors), case["case"])
                self.assertNotIn("hash_mismatch", rule_codes, case["case"])
                self.assertIn(case["expected_rule"], dataset_errors(records), case["case"])
            else:
                self.fail(f"unknown expected layer: {case['expected_layer']}")

    def test_all_legacy_fields_have_exactly_one_disposition(self) -> None:
        legacy_schema_fields = set(load_json(LEGACY_SCHEMA_PATH)["properties"])
        active_fields: set[str] = set()
        for line in LEGACY_ACTIVE_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                active_fields.update(json.loads(line))
        legacy_fields = legacy_schema_fields | active_fields

        mappings = self.migration["legacy_field_map"]
        mapped_fields = [mapping["legacy_field"] for mapping in mappings]
        self.assertEqual(len(legacy_fields), 32)
        self.assertEqual(len(mapped_fields), len(set(mapped_fields)))
        self.assertEqual(set(mapped_fields), legacy_fields)
        self.assertTrue(all(mapping["rule"] for mapping in mappings))
        self.assertTrue(
            all(
                mapping["disposition"] in {"direct", "transform", "drop_with_evidence"}
                for mapping in mappings
            )
        )

    def test_migration_cutover_has_one_truth_and_no_database_or_service(self) -> None:
        policy = self.migration["single_truth_policy"]
        self.assertEqual(self.migration["mode"], "CUTOVER_COMPLETE_CANONICAL_RECORDS_ACTIVE")
        self.assertEqual(policy["target_editable_truth_count"], 1)
        self.assertFalse(policy["second_database_allowed"])
        self.assertFalse(policy["service_added"])
        self.assertEqual(policy["current_task_data_writes"], 2)
        self.assertEqual(policy["canonical_record_count"], 198)
        self.assertEqual(policy["canonical_shard_count"], 1)
        self.assertEqual(policy["legacy_writer_count"], 0)
        self.assertEqual(policy["dual_write_count"], 0)
        self.assertEqual(self.migration["profiling_task_id"], "TSK.OpenAIDatabase.PAM1.0003")
        self.assertEqual(self.migration["cutover_task_id"], "TSK.OpenAIDatabase.PAM1.0004")

    def test_fixtures_contain_no_credential_shaped_values(self) -> None:
        fixture_text = VALID_FIXTURE_PATH.read_text(encoding="utf-8") + INVALID_FIXTURE_PATH.read_text(encoding="utf-8")
        forbidden = [
            r"sk-[A-Za-z0-9_-]{20,}",
            r"gh[pousr]_[A-Za-z0-9]{20,}",
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        ]
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, fixture_text), pattern)


if __name__ == "__main__":
    unittest.main()
