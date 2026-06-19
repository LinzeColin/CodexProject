#!/usr/bin/env python3
"""Validate the v4.2 machine-readable governance catalogs.

This validator intentionally checks the canonical v4.2 SSOT files. Legacy v4.0
compatibility catalogs are not treated as authoritative.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
errors: list[str] = []


def read_rows(name: str) -> list[dict[str, str]]:
    path = DATA / name
    if not path.is_file():
        errors.append(f"missing {name}")
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def require(name: str, columns: list[str], exact_rows: int | None = None, min_rows: int | None = None) -> list[dict[str, str]]:
    rows = read_rows(name)
    if not rows:
        return rows
    actual = set(rows[0])
    missing = set(columns) - actual
    if missing:
        errors.append(f"{name}: missing columns {sorted(missing)}")
    if exact_rows is not None and len(rows) != exact_rows:
        errors.append(f"{name}: expected {exact_rows} rows, got {len(rows)}")
    if min_rows is not None and len(rows) < min_rows:
        errors.append(f"{name}: expected >= {min_rows} rows, got {len(rows)}")
    return rows


def unique(rows: list[dict[str, str]], key: str, name: str) -> None:
    values = [r.get(key, "") for r in rows]
    if any(not v for v in values):
        errors.append(f"{name}: blank {key}")
    if len(values) != len(set(values)):
        errors.append(f"{name}: duplicate {key}")


functions = require(
    "function_catalog.csv",
    ["function_id", "nav_group", "name_zh", "default_visualization", "domain_objects", "data_tables", "api_paths", "priority", "task_ids", "acceptance_ids", "risk_ids"],
    exact_rows=17,
)
navigation = require("navigation_catalog.csv", ["function_id", "nav_group", "nav_order", "name_zh", "priority"], exact_rows=17)
product_navigation = require(
    "product_navigation_catalog.csv",
    ["nav_id", "nav_order", "name_zh", "name_en", "purpose", "existing_function_ids", "priority"],
    exact_rows=16,
)
models = require("model_registry.csv", ["model_id", "formula_id", "scoring_object", "status"], exact_rows=11)
formulas = require("formula_registry.csv", ["formula_id", "formula", "missing_policy", "default_threshold"], exact_rows=11)
parameters = require("parameter_catalog.csv", ["parameter_key", "default_value", "min_value", "max_value", "refresh_behavior"], exact_rows=60)
thresholds = require("threshold_registry.csv", ["threshold_id", "parameter_key", "default_value", "behavior"], exact_rows=17)
relationships = require("relationship_taxonomy.csv", ["relationship_type", "family", "direction"], exact_rows=52)
families = require("relationship_family_catalog.csv", ["family_key", "relationship_type_count"], exact_rows=10)
stages = require("supply_chain_stage_taxonomy.csv", ["stage_id", "stage_order", "name_zh"], exact_rows=16)
industries = require("industry_taxonomy.csv", ["industry_id", "name_zh", "kind"], exact_rows=26)
sectors = require("sector_taxonomy.csv", ["sector_id", "name_zh", "source_industry_id"], exact_rows=13)
segments = require("business_segment_taxonomy.csv", ["segment_id", "name_zh", "definition"], exact_rows=20)
capital = require("capital_object_taxonomy.csv", ["capital_object_id", "family", "name_zh", "amount_semantics"], exact_rows=30)
roles = require("upstream_downstream_role_catalog.csv", ["role_id", "direction", "name_zh", "recursive_pivot"], exact_rows=24)
companies = require("company_catalog.csv", ["company_id", "canonical_name", "tier", "fact_status"], exact_rows=140)
tasks = require("task_backlog.csv", ["task_id", "depends_on", "acceptance_ids"], exact_rows=120)
acceptance = require("acceptance_matrix.csv", ["acceptance_id", "priority", "criterion", "verification", "status"], exact_rows=200)
risks = require("risk_register.csv", ["risk_id", "severity", "risk", "control", "trigger", "owner", "status"], exact_rows=53)
status = require("development_status_ledger.csv", ["item_id", "spec_status", "prototype_status", "implementation_status", "unresolved", "next_action"], min_rows=30)
resolved = require("resolved_unresolved_register.csv", ["item_id", "item_type", "status", "title", "resolution_or_question"], min_rows=14)
manifest = require("data_catalog_manifest.csv", ["catalog_path", "row_count", "primary_key", "source_of_truth"], min_rows=20)

for rows_, key, label in [
    (functions, "function_id", "functions"), (navigation, "function_id", "navigation"),
    (models, "model_id", "models"), (formulas, "formula_id", "formulas"),
    (parameters, "parameter_key", "parameters"), (thresholds, "threshold_id", "thresholds"), (relationships, "relationship_type", "relationships"),
    (families, "family_key", "families"), (stages, "stage_id", "stages"),
    (industries, "industry_id", "industries"), (sectors, "sector_id", "sectors"), (segments, "segment_id", "segments"),
    (capital, "capital_object_id", "capital"), (roles, "role_id", "roles"),
    (companies, "company_id", "companies"), (tasks, "task_id", "tasks"),
    (acceptance, "acceptance_id", "acceptance"), (risks, "risk_id", "risks"),
]:
    if rows_:
        unique(rows_, key, label)

function_ids = {r["function_id"] for r in functions}
if function_ids != {r["function_id"] for r in navigation}:
    errors.append("function_catalog/navigation_catalog function IDs differ")

expected_product_nav = {
    "商业版图",
    "集团结构",
    "业务板块",
    "供应链",
    "资本网络",
    "并购交易",
    "控制关系",
    "政策环境",
    "战略信号",
    "时间演变",
    "证据中心",
    "模型中心",
    "数据中心",
    "我的关注",
    "探索记录",
    "系统状态",
}
if {r["name_zh"] for r in product_navigation} != expected_product_nav:
    errors.append("product_navigation_catalog does not match the frozen 16-module navigation")
for row in product_navigation:
    mapped_ids = {item.strip() for item in row["existing_function_ids"].split(",") if item.strip()}
    if not mapped_ids or mapped_ids - function_ids:
        errors.append(f"{row['nav_id']}: invalid function mapping {row['existing_function_ids']}")

formula_ids = {r["formula_id"] for r in formulas}
for model in models:
    if model["formula_id"] not in formula_ids:
        errors.append(f"model formula missing {model['model_id']} -> {model['formula_id']}")

family_counts: dict[str, int] = {}
for relationship in relationships:
    family_counts[relationship["family"]] = family_counts.get(relationship["family"], 0) + 1
for family in families:
    try:
        expected = int(family["relationship_type_count"])
    except ValueError:
        errors.append(f"invalid relationship_type_count for {family['family_key']}")
        continue
    if expected != family_counts.get(family["family_key"], 0):
        errors.append(f"relationship family count mismatch {family['family_key']}: {expected} vs {family_counts.get(family['family_key'], 0)}")

for parameter in parameters:
    try:
        default = float(parameter["default_value"])
        minimum = float(parameter["min_value"])
        maximum = float(parameter["max_value"])
        if not minimum <= default <= maximum:
            errors.append(f"parameter default out of range {parameter['parameter_key']}")
    except (TypeError, ValueError):
        # Some parameters are booleans/enums; their schema is checked by the full validator.
        pass

for required in [
    "GOVERNANCE_INDEX.md", "FUNCTION_CATALOG.md", "MODEL_MANAGEMENT.md", "DOMAIN_DATA_CATALOG.md",
    "DEVELOPMENT_STATUS.md", "RISK_AND_ACCEPTANCE.md", "CONTRIBUTING.md",
    "prototype/standalone.html", "prototype/index.html", "models/model_registry.json", "models/formula_registry.json",
    ".github/CODEOWNERS", ".github/pull_request_template.md", ".github/workflows/governance-validation.yml",
]:
    if not (ROOT / required).is_file():
        errors.append(f"missing required file {required}")

for json_file in ["models/model_registry.json", "models/formula_registry.json"]:
    try:
        json.loads((ROOT / json_file).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{json_file} invalid: {exc}")

html = (ROOT / "prototype/standalone.html").read_text(encoding="utf-8") if (ROOT / "prototype/standalone.html").is_file() else ""
for phrase in ["商业版图", "全链供应链", "数据资产", "模型与参数", "功能结构", "开发治理"]:
    if phrase not in html:
        errors.append(f"prototype missing navigation/visual phrase: {phrase}")

if errors:
    print("CATALOG INTEGRITY: FAIL")
    for error in errors:
        print("-", error)
    raise SystemExit(1)

print("CATALOG INTEGRITY: PASS")
print(
    f"functions={len(functions)} product_nav={len(product_navigation)} models={len(models)} formulas={len(formulas)} parameters={len(parameters)} "
    f"relationships={len(relationships)} families={len(families)} stages={len(stages)} industries={len(industries)} sectors={len(sectors)} "
    f"segments={len(segments)} capital_objects={len(capital)} roles={len(roles)} companies={len(companies)} "
    f"tasks={len(tasks)} acceptance={len(acceptance)} risks={len(risks)}"
)
