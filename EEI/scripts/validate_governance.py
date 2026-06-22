#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def req(path: str) -> None:
    if not (ROOT / path).is_file():
        raise AssertionError(f"missing {path}")


def unique(items: list[dict[str, str]], key: str, label: str) -> None:
    values = [item[key] for item in items]
    if not all(values) or len(values) != len(set(values)):
        raise AssertionError(f"{label}.{key} not unique/nonblank")


def expand_task_ids(raw_value: str) -> set[str]:
    task_ids: set[str] = set()
    for raw_part in raw_value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        match = re.fullmatch(r"T(\d+)-T(\d+)", part)
        if match:
            start, end = (int(match.group(1)), int(match.group(2)))
            width = max(len(match.group(1)), len(match.group(2)))
            if end < start:
                raise AssertionError(f"invalid descending task range: {part}")
            task_ids.update(f"T{number:0{width}d}" for number in range(start, end + 1))
        else:
            task_ids.add(part)
    return task_ids


def main() -> int:
    required = [
        "GOVERNANCE_INDEX.md",
        "GITHUB_REPOSITORY_BACKUP_INDEX.md",
        "FUNCTION_CATALOG.md",
        "MODEL_MANAGEMENT.md",
        "DOMAIN_DATA_CATALOG.md",
        "DEVELOPMENT_STATUS.md",
        "RISK_AND_ACCEPTANCE.md",
        "US_Corporate_Power_Map_System_Model_Parameter_Architecture_v4.2.md",
        "US_Corporate_Power_Map_UIUX_Redesign_v4.2.md",
        "docs/INDEX.md",
        "data/content_inventory.csv",
        "data/function_catalog.csv",
        "data/model_registry.csv",
        "data/formula_registry.csv",
        "data/parameter_catalog.csv",
        "data/threshold_registry.csv",
        "data/domain_object_catalog.csv",
        "data/relationship_family_catalog.csv",
        "data/relationship_taxonomy.csv",
        "data/supply_chain_stage_taxonomy.csv",
        "data/industry_taxonomy.csv",
        "data/sector_taxonomy.csv",
        "data/business_segment_taxonomy.csv",
        "data/capital_object_taxonomy.csv",
        "data/upstream_downstream_role_catalog.csv",
        "data/company_catalog.csv",
        "data/task_backlog.csv",
        "data/development_status_ledger.csv",
        "data/resolved_unresolved_register.csv",
        "data/acceptance_matrix.csv",
        "data/acceptance_traceability.csv",
        "data/risk_register.csv",
        "data/risk_control_traceability.csv",
        "data/release_gate_catalog.csv",
        "config/model_runtime_defaults.yaml",
        "config/model_profiles/balanced-v2.json",
        "config/model_profiles/supply-chain-v3.json",
        "config/thresholds/default-v2.json",
        "CONTRIBUTING.md",
        ".github/CODEOWNERS",
        ".github/pull_request_template.md",
        ".github/workflows/governance-validation.yml",
    ]
    for path in required:
        req(path)

    functions = rows("data/function_catalog.csv")
    unique(functions, "function_id", "functions")
    if len(functions) != 17:
        raise AssertionError(f"expected 17 functions, got {len(functions)}")
    if any(
        item["priority"] == "P0"
        and (not item["task_ids"] or not item["acceptance_ids"] or not item["risk_ids"])
        for item in functions
    ):
        raise AssertionError("P0 function missing task/acceptance/risk traceability")

    models = rows("data/model_registry.csv")
    formulas = rows("data/formula_registry.csv")
    parameters = rows("data/parameter_catalog.csv")
    thresholds = rows("data/threshold_registry.csv")
    unique(models, "model_id", "models")
    unique(formulas, "formula_id", "formulas")
    unique(parameters, "parameter_key", "parameters")
    unique(thresholds, "threshold_id", "thresholds")
    formula_ids = {item["formula_id"] for item in formulas}
    parameter_keys = {item["parameter_key"] for item in parameters}
    if len(models) != 11 or len(formulas) != 11 or len(parameters) != 84 or len(thresholds) != 17:
        raise AssertionError("model/formula/parameter/threshold canonical counts invalid")
    if any(item["formula_id"] not in formula_ids for item in models):
        raise AssertionError("model references unknown formula")
    if any(item["parameter_key"] not in parameter_keys for item in thresholds):
        raise AssertionError("threshold references unknown parameter")
    for item in thresholds:
        if not item["file_edit"]:
            raise AssertionError(f"threshold missing file-edit source: {item['threshold_id']}")
        online_editable = item["online_edit"].lower() == "true"
        fixed_governance_value = item["min_value"] == item["max_value"] == item["default_value"]
        if not online_editable and not fixed_governance_value:
            raise AssertionError(
                f"non-fixed threshold must support online editing: {item['threshold_id']}"
            )

    runtime = yaml.safe_load(
        (ROOT / "config/model_runtime_defaults.yaml").read_text(encoding="utf-8")
    )
    if not math.isclose(
        sum(float(value) for value in runtime["weights"].values()),
        1.0,
        abs_tol=1e-4,
    ):
        raise AssertionError("runtime weights do not sum to 1.0")

    families = rows("data/relationship_family_catalog.csv")
    relationships = rows("data/relationship_taxonomy.csv")
    stages = rows("data/supply_chain_stage_taxonomy.csv")
    roles = rows("data/upstream_downstream_role_catalog.csv")
    industries = rows("data/industry_taxonomy.csv")
    sectors = rows("data/sector_taxonomy.csv")
    segments = rows("data/business_segment_taxonomy.csv")
    capital_objects = rows("data/capital_object_taxonomy.csv")
    domain_objects = rows("data/domain_object_catalog.csv")
    companies = rows("data/company_catalog.csv")
    if (
        len(families) != 10
        or len(relationships) != 52
        or len(stages) != 16
        or len(roles) != 24
        or len(industries) != 26
        or len(sectors) != 13
        or len(segments) != 20
        or len(capital_objects) != 30
        or len(domain_objects) != 32
        or len(companies) != 140
    ):
        raise AssertionError("domain catalog canonical counts invalid")
    if {item["family_key"] for item in families} != {item["family"] for item in relationships}:
        raise AssertionError("relationship family/type mismatch")

    tasks = rows("data/task_backlog.csv")
    acceptance = rows("data/acceptance_matrix.csv")
    risks = rows("data/risk_register.csv")
    trace = rows("data/acceptance_traceability.csv")
    gates = rows("data/release_gate_catalog.csv")
    unique(tasks, "task_id", "tasks")
    unique(acceptance, "acceptance_id", "acceptance")
    unique(risks, "risk_id", "risks")
    unique(trace, "trace_id", "acceptance trace")
    unique(gates, "gate_id", "release gates")
    if (
        len(tasks) != 130
        or len(acceptance) != 211
        or len(risks) != 53
        or len(trace) != 232
        or len(gates) != 10
    ):
        raise AssertionError("task/acceptance/risk/trace/gate canonical counts invalid")

    task_ids = {item["task_id"] for item in tasks}
    acceptance_ids = {item["acceptance_id"] for item in acceptance}
    for task in tasks:
        for dependency in filter(
            None,
            (value.strip() for value in task["depends_on"].split(",")),
        ):
            if dependency not in task_ids:
                raise AssertionError(f"{task['task_id']} missing dependency {dependency}")
        for acceptance_id in filter(
            None,
            (value.strip() for value in task["acceptance_ids"].split(",")),
        ):
            if acceptance_id not in acceptance_ids:
                raise AssertionError(f"{task['task_id']} missing acceptance {acceptance_id}")

    gate_ids = {item["gate_id"] for item in gates}
    for gate in gates:
        expected = {task["task_id"] for task in tasks if task["gate"] == gate["gate_id"]}
        actual = expand_task_ids(gate["task_ids"])
        if actual != expected:
            raise AssertionError(
                f"{gate['gate_id']} task mapping drift: "
                f"missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
            )
    orphan_gate_values = {task["gate"] for task in tasks if task["gate"].startswith("G")} - gate_ids
    if orphan_gate_values:
        raise AssertionError(f"tasks reference missing release gates: {sorted(orphan_gate_values)}")

    traced_functions = {item["requirement_or_function_id"] for item in trace}
    if any(
        item["priority"] == "P0" and item["function_id"] not in traced_functions
        for item in functions
    ):
        raise AssertionError("P0 function missing acceptance trace")

    risk_trace = rows("data/risk_control_traceability.csv")
    high_or_critical = [
        item for item in risk_trace if item["severity"].lower() in {"high", "critical"}
    ]
    if any(
        not item["control"]
        or not item["trigger"]
        or not item["owner"]
        or not item["release_gate"]
        for item in high_or_critical
    ):
        raise AssertionError("high/critical risk missing control, trigger, owner or release gate")

    html = (ROOT / "prototype/standalone.html").read_text(encoding="utf-8")
    for phrase in [
        "开发治理",
        "功能结构",
        "模型与参数",
        "数据资产",
        "商业版图",
        "全链供应链",
        "交互原型 · 示例数据",
        "全局刷新",
    ]:
        if phrase not in html:
            raise AssertionError(f"prototype missing {phrase}")
    if (
        (ROOT / "prototype/index.html").read_bytes()
        != (ROOT / "prototype/standalone.html").read_bytes()
    ):
        raise AssertionError("index and standalone must be identical")
    if html.count('data-view="governance"') != 1:
        raise AssertionError("duplicate/missing governance navigation")

    inventory = rows("data/content_inventory.csv")
    unique(inventory, "catalog_id", "content inventory")
    if len(inventory) != 27:
        raise AssertionError(f"expected 27 content inventory rows, got {len(inventory)}")

    yaml_files = [
        ".github/ISSUE_TEMPLATE/feature.yml",
        ".github/ISSUE_TEMPLATE/model_change.yml",
        ".github/ISSUE_TEMPLATE/data_scope_change.yml",
        ".github/ISSUE_TEMPLATE/data_relationship.yml",
        ".github/ISSUE_TEMPLATE/risk_control.yml",
        ".github/ISSUE_TEMPLATE/bug.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/workflows/governance-validation.yml",
    ]
    for path in yaml_files:
        yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))

    for path in [
        "config/model_profiles/balanced-v2.json",
        "config/model_profiles/supply-chain-v3.json",
        "config/thresholds/default-v2.json",
        "models/model_registry.json",
        "models/formula_registry.json",
    ]:
        json.loads((ROOT / path).read_text(encoding="utf-8"))

    print("Governance validation: PASS")
    print(
        f"  functions/models/formulas/parameters/thresholds: "
        f"{len(functions)}/{len(models)}/{len(formulas)}/{len(parameters)}/{len(thresholds)}"
    )
    print(
        f"  families/relationships/stages/roles: "
        f"{len(families)}/{len(relationships)}/{len(stages)}/{len(roles)}"
    )
    print(
        f"  industries/sectors/segments/capital/domain/companies: "
        f"{len(industries)}/{len(sectors)}/{len(segments)}/"
        f"{len(capital_objects)}/{len(domain_objects)}/{len(companies)}"
    )
    print(
        f"  tasks/acceptance/risks/trace/gates: "
        f"{len(tasks)}/{len(acceptance)}/{len(risks)}/{len(trace)}/{len(gates)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"Governance validation: FAIL - {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
