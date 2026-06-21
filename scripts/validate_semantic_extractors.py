#!/usr/bin/env python3
"""Machine-check documented governance semantics against implementation facts."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
UNKNOWN_VALUES = {"", "UNKNOWN", "NOT_APPLICABLE", "N/A", "NA", "NONE", "PENDING"}


@dataclass(frozen=True)
class SemanticIssue:
    level: str
    scope: str
    message: str


class SemanticExtractionError(ValueError):
    pass


def _load_structural_module() -> Any:
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import validate_project_governance as structural  # type: ignore

    return structural


def load_yaml(path: Path) -> Any:
    return _load_structural_module().load_yaml(path)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows: list[dict[str, str]] = []
        for row in csv.DictReader(handle):
            rows.append({str(key).lstrip("\ufeff"): value for key, value in row.items()})
        return rows


def as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_tree(path: Path) -> ast.Module:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        raise SemanticExtractionError(f"cannot parse Python AST for {path.relative_to(ROOT)}: {exc}") from exc


def selector_path(path_text: str) -> Path:
    path = ROOT / path_text
    if not path.is_file():
        raise SemanticExtractionError(f"selector path does not exist: {path_text}")
    return path


def is_unknownish(value: Any) -> bool:
    text = str(value or "").strip().upper()
    return text in UNKNOWN_VALUES or text.startswith("UNKNOWN")


def split_lookup(text: str) -> tuple[str, str]:
    if "=" not in text:
        raise SemanticExtractionError(f"lookup must use column=value syntax: {text}")
    key, value = text.split("=", 1)
    key = key.strip()
    if not key:
        raise SemanticExtractionError(f"lookup column is empty: {text}")
    return key, value


def extract_csv_row(target: str) -> dict[str, str]:
    path_text, lookup_text = target.split("::", 1)
    lookup_column, lookup_value = split_lookup(lookup_text)
    matches = [row for row in load_csv(selector_path(path_text)) if str(row.get(lookup_column) or "") == lookup_value]
    if not matches:
        raise SemanticExtractionError(f"csv_row lookup did not match: {target}")
    if len(matches) > 1:
        raise SemanticExtractionError(f"csv_row lookup matched multiple rows: {target}")
    return {key: str(matches[0].get(key) or "") for key in sorted(matches[0])}


def extract_csv_cell(target: str) -> str:
    path_text, lookup_text, value_column = target.split("::", 2)
    row = extract_csv_row(f"{path_text}::{lookup_text}")
    if value_column not in row:
        raise SemanticExtractionError(f"csv_cell value column not found: {value_column}")
    return row[value_column]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def path_parts(path_text: str) -> list[str]:
    cleaned = path_text.strip()
    if cleaned.startswith("$."):
        cleaned = cleaned[2:]
    elif cleaned.startswith("$"):
        cleaned = cleaned[1:].lstrip(".")
    return [part for part in cleaned.split(".") if part]


def extract_structural_path(data: Any, path_text: str) -> Any:
    current = data
    for part in path_parts(path_text):
        if isinstance(current, dict):
            if part not in current:
                raise SemanticExtractionError(f"structural path key not found: {part}")
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                raise SemanticExtractionError(f"structural path index out of range: {part}")
            current = current[index]
            continue
        raise SemanticExtractionError(f"structural path cannot descend through {type(current).__name__}: {part}")
    return current


def literal_value(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = literal_value(node.operand)
        if isinstance(value, (int, float)):
            return -value
    if isinstance(node, ast.Tuple):
        return tuple(literal_value(item) for item in node.elts)
    if isinstance(node, ast.List):
        return [literal_value(item) for item in node.elts]
    if isinstance(node, ast.Set):
        return {literal_value(item) for item in node.elts}
    if isinstance(node, ast.Dict):
        return {literal_value(key): literal_value(value) for key, value in zip(node.keys, node.values)}
    raise SemanticExtractionError(f"unsupported literal expression: {ast.dump(node, include_attributes=False)}")


def find_module_assignment(tree: ast.Module, name: str) -> ast.AST:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            return node.value
    raise SemanticExtractionError(f"module assignment not found: {name}")


def find_class_default(tree: ast.Module, class_name: str, attr_name: str) -> Any:
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == attr_name:
                if item.value is None:
                    raise SemanticExtractionError(f"class attribute has no default: {class_name}.{attr_name}")
                return literal_value(item.value)
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == attr_name:
                        return literal_value(item.value)
    raise SemanticExtractionError(f"class attribute default not found: {class_name}.{attr_name}")


def find_function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise SemanticExtractionError(f"function not found: {name}")


def find_function_default(tree: ast.Module, function_name: str, arg_name: str) -> Any:
    function = find_function(tree, function_name)
    args = function.args.args
    defaults = function.args.defaults
    first_default = len(args) - len(defaults)
    for index, arg in enumerate(args):
        if arg.arg != arg_name:
            continue
        default_index = index - first_default
        if default_index < 0:
            raise SemanticExtractionError(f"function argument has no default: {function_name}.{arg_name}")
        return literal_value(defaults[default_index])
    for arg, default in zip(function.args.kwonlyargs, function.args.kw_defaults):
        if arg.arg != arg_name:
            continue
        if default is None:
            raise SemanticExtractionError(f"function keyword-only argument has no default: {function_name}.{arg_name}")
        return literal_value(default)
    raise SemanticExtractionError(f"function argument not found: {function_name}.{arg_name}")


def find_method_default(tree: ast.Module, class_name: str, method_name: str, arg_name: str) -> Any:
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                args = item.args.args
                defaults = item.args.defaults
                first_default = len(args) - len(defaults)
                for index, arg in enumerate(args):
                    if arg.arg != arg_name:
                        continue
                    default_index = index - first_default
                    if default_index < 0:
                        raise SemanticExtractionError(f"method argument has no default: {class_name}.{method_name}.{arg_name}")
                    return literal_value(defaults[default_index])
                for arg, default in zip(item.args.kwonlyargs, item.args.kw_defaults):
                    if arg.arg != arg_name:
                        continue
                    if default is None:
                        raise SemanticExtractionError(f"method keyword-only argument has no default: {class_name}.{method_name}.{arg_name}")
                    return literal_value(default)
                raise SemanticExtractionError(f"method argument not found: {class_name}.{method_name}.{arg_name}")
    raise SemanticExtractionError(f"method not found: {class_name}.{method_name}")


def find_line_literal(tree: ast.Module, line_no: int, occurrence: int) -> Any:
    values: list[Any] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and getattr(node, "lineno", None) == line_no:
            values.append(node.value)
    if occurrence < 1 or occurrence > len(values):
        raise SemanticExtractionError(f"literal occurrence {occurrence} not found on line {line_no}")
    return values[occurrence - 1]


def parse_options(text: str) -> tuple[str, dict[str, str]]:
    if "|" not in text:
        return text, {}
    base, *parts = text.split("|")
    options: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            options[part] = "true"
        else:
            key, value = part.split("=", 1)
            options[key] = {"pipe": "|", "equals": "="}.get(value, value)
    return base, options


def apply_selector_options(value: Any, options: dict[str, str]) -> Any:
    if "order" in options:
        order = [item for item in options["order"].split(",") if item]
        values = {normalize_value(item) for item in value} if isinstance(value, (set, list, tuple)) else {normalize_value(value)}
        if set(order) != values:
            raise SemanticExtractionError(f"order transform values do not match extracted values: expected {sorted(values)}, got {order}")
        value = "|".join(order)
    if "subtract" not in options:
        return value
    amount = float(options["subtract"])
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise SemanticExtractionError(f"subtract transform requires numeric value, got {value!r}")
    result = float(value) - amount
    return int(result) if result.is_integer() else result


def extract_selector(selector: str) -> Any:
    selector = selector.strip()
    if not selector or selector.upper() in UNKNOWN_VALUES:
        raise SemanticExtractionError("empty or non-machine selector")
    selector, options = parse_options(selector)
    if selector.startswith("python_ast_attr:"):
        target = selector.removeprefix("python_ast_attr:")
        path_text, symbol = target.split("::", 1)
        class_name, attr_name = symbol.split(".", 1)
        return apply_selector_options(find_class_default(parse_tree(selector_path(path_text)), class_name, attr_name), options)
    if selector.startswith("python_ast_default:"):
        target = selector.removeprefix("python_ast_default:")
        path_text, symbol = target.split("::", 1)
        function_name, arg_name = symbol.split(".", 1)
        return apply_selector_options(find_function_default(parse_tree(selector_path(path_text)), function_name, arg_name), options)
    if selector.startswith("python_ast_method_default:"):
        target = selector.removeprefix("python_ast_method_default:")
        path_text, symbol = target.split("::", 1)
        class_name, method_name, arg_name = symbol.split(".", 2)
        return apply_selector_options(
            find_method_default(parse_tree(selector_path(path_text)), class_name, method_name, arg_name),
            options,
        )
    if selector.startswith("python_ast_assignment:"):
        target = selector.removeprefix("python_ast_assignment:")
        path_text, name = target.split("::", 1)
        return apply_selector_options(literal_value(find_module_assignment(parse_tree(selector_path(path_text)), name)), options)
    if selector.startswith("python_ast_literal:"):
        target = selector.removeprefix("python_ast_literal:")
        path_text, line_text, occurrence_text = target.rsplit(":", 2)
        return apply_selector_options(find_line_literal(parse_tree(selector_path(path_text)), int(line_text), int(occurrence_text)), options)
    if selector.startswith("python_ast_tuple:"):
        target = selector.removeprefix("python_ast_tuple:")
        path_text, name = target.split("::", 1)
        value = literal_value(find_module_assignment(parse_tree(selector_path(path_text)), name))
        if not isinstance(value, tuple):
            raise SemanticExtractionError(f"selector did not extract tuple: {selector}")
        joiner = options.get("join")
        extracted = joiner.join(str(item) for item in value) if joiner is not None else value
        return apply_selector_options(extracted, options)
    if selector.startswith("python_ast_dict:"):
        target = selector.removeprefix("python_ast_dict:")
        path_text, name = target.split("::", 1)
        value = literal_value(find_module_assignment(parse_tree(selector_path(path_text)), name))
        if not isinstance(value, dict):
            raise SemanticExtractionError(f"selector did not extract dict: {selector}")
        pair = options.get("pair", "=")
        sep = options.get("sep", "|")
        return apply_selector_options(sep.join(f"{key}{pair}{item}" for key, item in value.items()), options)
    if selector.startswith("text_regex:"):
        target = selector.removeprefix("text_regex:")
        path_text, pattern = target.split("::", 1)
        text = selector_path(path_text).read_text(encoding="utf-8")
        match = re.search(pattern, text, re.S)
        if not match:
            raise SemanticExtractionError(f"text_regex pattern did not match: {selector}")
        return apply_selector_options(match.group(1), options)
    if selector.startswith("csv_cell:"):
        target = selector.removeprefix("csv_cell:")
        return apply_selector_options(extract_csv_cell(target), options)
    if selector.startswith("json_path:"):
        target = selector.removeprefix("json_path:")
        path_text, path_expr = target.split("::", 1)
        return apply_selector_options(extract_structural_path(load_json(selector_path(path_text)), path_expr), options)
    if selector.startswith("yaml_path:"):
        target = selector.removeprefix("yaml_path:")
        path_text, path_expr = target.split("::", 1)
        return apply_selector_options(extract_structural_path(load_yaml(selector_path(path_text)), path_expr), options)
    raise SemanticExtractionError(f"unsupported selector: {selector}")


def normalize_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if math.isfinite(value):
            return format(value, ".12g")
        return str(value)
    if isinstance(value, dict):
        return "|".join(f"{normalize_value(key)}={normalize_value(item)}" for key, item in value.items())
    if isinstance(value, set):
        return "|".join(sorted(normalize_value(item) for item in value))
    if isinstance(value, (tuple, list)):
        return "|".join(normalize_value(item) for item in value)
    return str(value)


def values_equal(documented: Any, extracted: Any) -> bool:
    left = normalize_value(documented).strip()
    right = normalize_value(extracted).strip()
    if left.lower() in {"true", "false"} or right.lower() in {"true", "false"}:
        return left.lower() == right.lower()
    if left.lower() in {"none", "null"} or right.lower() in {"none", "null"}:
        return left.lower() in {"none", "null"} and right.lower() in {"none", "null"}
    try:
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)
    except ValueError:
        return left == right


def stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def parameter_evidence_hash(parameter_id: str, selector: str, extracted_value: Any) -> str:
    return stable_hash(
        {
            "kind": "parameter_extraction",
            "parameter_id": parameter_id,
            "source_selector": selector,
            "extracted_value": normalize_value(extracted_value),
        }
    )


def symbol_node(path_text: str, symbol: str) -> ast.AST:
    path = selector_path(path_text)
    tree = parse_tree(path)
    if "." in symbol:
        class_name, member_name = symbol.split(".", 1)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == member_name:
                        return item
        raise SemanticExtractionError(f"class member not found: {path_text}::{symbol}")
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol:
            return node
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == symbol for target in node.targets):
                return node
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == symbol:
            return node
    raise SemanticExtractionError(f"symbol not found: {path_text}::{symbol}")


def stable_ast_payload(node: Any) -> Any:
    """Return a Python-version-stable AST payload for semantic fingerprinting."""
    if isinstance(node, ast.AST):
        payload: dict[str, Any] = {"_type": node.__class__.__name__}
        for field_name in getattr(node, "_fields", ()):
            if field_name in {"type_comment", "type_params"}:
                continue
            payload[field_name] = stable_ast_payload(getattr(node, field_name, None))
        return payload
    if isinstance(node, list):
        return [stable_ast_payload(item) for item in node]
    if isinstance(node, tuple):
        return [stable_ast_payload(item) for item in node]
    return node


def implementation_ref_payload(ref: str) -> dict[str, str]:
    if ref.startswith("csv_row:"):
        target = ref.removeprefix("csv_row:")
        return {
            "ref": ref,
            "csv_row": json.dumps(extract_csv_row(target), sort_keys=True, ensure_ascii=False, separators=(",", ":")),
        }
    if ref.startswith("json_path:"):
        target = ref.removeprefix("json_path:")
        path_text, path_expr = target.split("::", 1)
        return {
            "ref": ref,
            "json_path": json.dumps(
                extract_structural_path(load_json(selector_path(path_text)), path_expr),
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
    if ref.startswith("yaml_path:"):
        target = ref.removeprefix("yaml_path:")
        path_text, path_expr = target.split("::", 1)
        return {
            "ref": ref,
            "yaml_path": json.dumps(
                extract_structural_path(load_yaml(selector_path(path_text)), path_expr),
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
    path_text, symbol = ref.split("::", 1)
    node = symbol_node(path_text, symbol)
    return {
        "ref": ref,
        "ast": json.dumps(stable_ast_payload(node), sort_keys=True, ensure_ascii=False, separators=(",", ":")),
    }


def implementation_fingerprint(refs: list[str]) -> str:
    payload: list[dict[str, str]] = []
    for ref in refs:
        payload.append(implementation_ref_payload(str(ref)))
    return stable_hash({"kind": "implementation_fingerprint", "refs": payload})


def formula_evidence_hash(formula_id: str, refs: list[str], fingerprint: str) -> str:
    return stable_hash(
        {
            "kind": "formula_implementation",
            "formula_id": formula_id,
            "implementation_refs": refs,
            "implementation_fingerprint": fingerprint,
        }
    )


def git_ref_exists(ref: str) -> bool:
    if not ref or ref.upper() in UNKNOWN_VALUES:
        return False
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.returncode == 0


def validate_verified_fields(
    issues: list[SemanticIssue],
    scope: str,
    identifier: str,
    row: dict[str, Any],
) -> None:
    commit = str(row.get("last_verified_commit") or "").strip()
    if not git_ref_exists(commit):
        issues.append(SemanticIssue("ERROR", scope, f"{identifier}: last_verified_commit is missing or not a commit: {commit or '<empty>'}"))
    verified_at = str(row.get("verified_at") or "").strip()
    try:
        datetime.fromisoformat(verified_at.replace("Z", "+00:00"))
    except ValueError:
        issues.append(SemanticIssue("ERROR", scope, f"{identifier}: verified_at is not valid ISO datetime: {verified_at or '<empty>'}"))


def validate_parameters(
    issues: list[SemanticIssue],
    scope: str,
    project_path: Path,
) -> int:
    registry = project_path / "docs" / "governance" / "parameter_registry.csv"
    if not registry.exists():
        return 0
    rows = load_csv(registry)
    if not rows or "source_selector" not in rows[0]:
        return 0
    checked = 0
    for row in rows:
        parameter_id = str(row.get("parameter_id") or "<unknown>")
        if str(row.get("status") or "") != "active":
            continue
        selector = str(row.get("source_selector") or "").strip()
        if not selector or is_unknownish(selector):
            semantic_status = str(row.get("semantic_status") or "").strip()
            review_task_ids = str(row.get("semantic_review_task_ids") or "").strip()
            if semantic_status == "HUMAN_REVIEW_REQUIRED" and review_task_ids:
                continue
            if is_unknownish(row.get("active_value")) and str(row.get("unknown_task_ids") or "").strip():
                continue
            issues.append(SemanticIssue("ERROR", scope, f"{parameter_id}: active parameter has no machine source_selector"))
            continue
        try:
            extracted = extract_selector(selector)
        except SemanticExtractionError as exc:
            issues.append(SemanticIssue("ERROR", scope, f"{parameter_id}: {exc}"))
            continue
        checked += 1
        active_value = row.get("active_value", "")
        extracted_text = normalize_value(extracted)
        if not values_equal(active_value, extracted):
            issues.append(
                SemanticIssue(
                    "ERROR",
                    scope,
                    f"{parameter_id}: active_value={active_value!r} does not match extracted_value={extracted_text!r}",
                )
            )
        stored_extracted = row.get("extracted_value", "")
        if stored_extracted and not values_equal(stored_extracted, extracted):
            issues.append(
                SemanticIssue(
                    "ERROR",
                    scope,
                    f"{parameter_id}: stored extracted_value={stored_extracted!r} does not match live extracted_value={extracted_text!r}",
                )
            )
        expected_hash = parameter_evidence_hash(parameter_id, selector, extracted)
        if str(row.get("evidence_hash") or "").strip() != expected_hash:
            issues.append(SemanticIssue("ERROR", scope, f"{parameter_id}: evidence_hash does not match live extracted value"))
        validate_verified_fields(issues, scope, parameter_id, row)
    return checked


def target_weight_maxima(candidate_counts: list[int], *, decay: float, conf_min: float, conf_var: float, score_denom: float, cap: float) -> dict[str, float]:
    maxima: dict[str, float] = {}
    confidence = max(0.0, min(1.0, 100.0 / score_denom))
    multiplier = conf_min + (conf_var * confidence)
    for count in candidate_counts:
        raw = [(decay**idx) * multiplier for idx in range(count)]
        raw_total = sum(raw)
        if raw_total <= 0:
            maxima[str(count)] = 0.0
            continue
        normalized = [value / raw_total for value in raw]
        capped = [min(value, cap) for value in normalized]
        cap_total = sum(capped)
        final = [value / cap_total for value in capped] if cap_total else []
        maxima[str(count)] = max(final) if final else 0.0
    return maxima


def target_weight_test_candidate_counts(test_path: Path) -> list[int]:
    if not test_path.exists():
        return []
    tree = parse_tree(test_path)
    counts: set[int] = set()
    for function in [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]:
        assigned_lengths: dict[str, int] = {}
        for node in ast.walk(function):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_lengths[target.id] = len(node.value.elts)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_target_weights":
                if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in assigned_lengths:
                    counts.add(assigned_lengths[node.args[0].id])
    return sorted(counts)


def validate_form008(
    issues: list[SemanticIssue],
    scope: str,
    formulas_by_id: dict[str, dict[str, Any]],
    parameters_by_symbol: dict[str, dict[str, str]],
) -> None:
    form = formulas_by_id.get("FORM-008")
    if not form:
        return
    if "observed_max_weight_by_candidate_count" not in form and "post_renormalization_cap_holds" not in form:
        return
    required = ["SERENITY_DECAY", "CONF_MULT_MIN", "CONF_MULT_VAR", "SCORE_DENOM", "TARGET_WEIGHT_CAP"]
    try:
        values = {symbol: float(parameters_by_symbol[symbol]["active_value"]) for symbol in required}
    except (KeyError, ValueError) as exc:
        issues.append(SemanticIssue("ERROR", scope, f"FORM-008: cannot compute target-weight semantic check: {exc}"))
        return
    maxima = target_weight_maxima(
        [1, 2, 3, 4, 5],
        decay=values["SERENITY_DECAY"],
        conf_min=values["CONF_MULT_MIN"],
        conf_var=values["CONF_MULT_VAR"],
        score_denom=values["SCORE_DENOM"],
        cap=values["TARGET_WEIGHT_CAP"],
    )
    documented = str(form.get("observed_max_weight_by_candidate_count") or "").strip()
    expected = "|".join(f"{key}={maxima[key]:.12g}" for key in ["1", "2", "3", "4", "5"])
    if documented != expected:
        issues.append(SemanticIssue("ERROR", scope, f"FORM-008: observed_max_weight_by_candidate_count is stale; expected {expected}"))
    invariant = all(value <= values["TARGET_WEIGHT_CAP"] + 1e-12 for value in maxima.values())
    documented_invariant = str(form.get("post_renormalization_cap_holds") or "").strip().lower()
    if documented_invariant != ("true" if invariant else "false"):
        issues.append(SemanticIssue("ERROR", scope, "FORM-008: post_renormalization_cap_holds does not match live semantic check"))
    counts = target_weight_test_candidate_counts(ROOT / "Serenity-Alipay" / "tests" / "test_pipeline_serenity_priority.py")
    documented_counts = str(form.get("existing_target_weight_test_candidate_counts") or "").strip()
    expected_counts = "|".join(str(item) for item in counts)
    if documented_counts != expected_counts:
        issues.append(SemanticIssue("ERROR", scope, f"FORM-008: existing_target_weight_test_candidate_counts is stale; expected {expected_counts}"))


def validate_formulas(
    issues: list[SemanticIssue],
    scope: str,
    project_path: Path,
    parameters: list[dict[str, str]],
) -> int:
    registry = project_path / "docs" / "governance" / "formula_registry.yaml"
    if not registry.exists():
        return 0
    data = load_yaml(registry)
    formulas = [item for item in as_list(data.get("formulas")) if isinstance(item, dict)] if isinstance(data, dict) else []
    checked = 0
    formulas_by_id = {str(item.get("formula_id")): item for item in formulas}
    parameters_by_symbol = {str(item.get("symbol")): item for item in parameters}
    for formula in formulas:
        formula_id = str(formula.get("formula_id") or "<unknown>")
        if str(formula.get("status") or "") != "active":
            continue
        refs = [str(item) for item in as_list(formula.get("implementation_refs")) if str(item).strip()]
        semantic_status = str(formula.get("semantic_status") or "").strip()
        if not refs:
            if semantic_status != "HUMAN_REVIEW_REQUIRED":
                issues.append(SemanticIssue("ERROR", scope, f"{formula_id}: active formula has no implementation_refs or HUMAN_REVIEW_REQUIRED status"))
            continue
        try:
            fingerprint = implementation_fingerprint(refs)
        except SemanticExtractionError as exc:
            issues.append(SemanticIssue("ERROR", scope, f"{formula_id}: {exc}"))
            continue
        checked += 1
        if str(formula.get("implementation_fingerprint") or "").strip() != fingerprint:
            issues.append(SemanticIssue("ERROR", scope, f"{formula_id}: implementation_fingerprint does not match live AST fingerprint"))
        expected_hash = formula_evidence_hash(formula_id, refs, fingerprint)
        if str(formula.get("evidence_hash") or "").strip() != expected_hash:
            issues.append(SemanticIssue("ERROR", scope, f"{formula_id}: evidence_hash does not match live implementation fingerprint"))
        validate_verified_fields(issues, scope, formula_id, formula)
    validate_form008(issues, scope, formulas_by_id, parameters_by_symbol)
    return checked


def validate_project_semantics(project_path: Path, scope: str) -> tuple[list[SemanticIssue], dict[str, int]]:
    issues: list[SemanticIssue] = []
    parameter_rows = load_csv(project_path / "docs" / "governance" / "parameter_registry.csv")
    checked_parameters = validate_parameters(issues, scope, project_path)
    checked_formulas = validate_formulas(issues, scope, project_path, parameter_rows)
    return issues, {"semantic_parameters_checked": checked_parameters, "semantic_formulas_checked": checked_formulas}


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) != 1:
        print("usage: validate_semantic_extractors.py <project_path>", file=sys.stderr)
        return 2
    project_path = ROOT / argv[0]
    issues, summary = validate_project_semantics(project_path, argv[0])
    for issue in issues:
        print(f"{issue.level}: {issue.scope}: {issue.message}")
    print(json.dumps(summary, sort_keys=True))
    return 1 if any(issue.level == "ERROR" for issue in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
