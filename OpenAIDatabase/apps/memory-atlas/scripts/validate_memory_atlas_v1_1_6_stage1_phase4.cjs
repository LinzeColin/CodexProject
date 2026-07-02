#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

function pass(name, evidence, details) {
  checks.push({ name, status: "PASS", evidence, ...(details ? { details } : {}) });
}

function assertCondition(condition, name, evidence, failure, details = {}) {
  if (condition) {
    pass(name, evidence, details);
    return;
  }
  const error = new Error(failure);
  error.details = details;
  throw error;
}

function readRepoFile(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(
    source.endsWith("\n"),
    `${relativePath}:final_newline`,
    `${relativePath} has a final newline`,
    `${relativePath} is missing a final newline`,
  );

  const blocked = [String.fromCharCode(0xfffd), String.fromCharCode(0x00c2), String.fromCharCode(0x00c3)];
  const badLines = [];
  source.split("\n").forEach((line, index) => {
    if (line.trimEnd() !== line) badLines.push(`${index + 1}:trailing`);
    if (blocked.some((char) => line.includes(char))) badLines.push(`${index + 1}:mojibake`);
  });
  assertCondition(
    badLines.length === 0,
    `${relativePath}:text_clean`,
    `${relativePath} has no blocked mojibake characters or trailing whitespace`,
    `${relativePath} contains blocked characters or trailing whitespace`,
    { badLines: badLines.slice(0, 20) },
  );
}

function validateProductContract() {
  const contract = readRepoFile("docs/product/topic_classification_detail_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas 主题分类明细合同",
      "v1.1.6 Stage 1 Phase 4",
      "dominant",
      "rising",
      "declining",
      "emerging",
      "conflict",
      "black_hole",
      "stale",
      "topic_id",
      "topic_label",
      "topic_state",
      "topic_strength",
      "trend",
      "confidence",
      "record_count",
      "evidence_count",
      "evidence_refs",
      "source_scope",
      "linked_asset_ids",
      "linked_action_ids",
      "linked_starfield_cluster_id",
      "linked_river_range",
      "related_topic_ids",
      "matched_reason",
      "recommended_topic_action",
      "proposal_hint",
      "rollback_hint",
      "continue",
      "review",
      "consolidate",
      "validate",
      "defer",
      "watch",
      "Inspector",
      "proposal-only",
      "raw transcript",
      "active memory",
      "Proposal-only 编辑 schema",
      "Search 2.0",
      "Data Map 2.0",
      "本 phase 不修改运行时",
    ]),
    "stage1_phase4_product_contract",
    "Topic classification contract covers seven states, required fields, Inspector handoff, proposal-only safety, privacy and future-phase boundaries",
    "Topic classification detail contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/topic_classification_detail_acceptance.md");
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas 主题分类明细验收",
      "v1.1.6 Stage 1 Phase 4",
      "dominant",
      "rising",
      "declining",
      "emerging",
      "conflict",
      "black_hole",
      "stale",
      "topic_id",
      "topic_label",
      "topic_state",
      "topic_strength",
      "trend",
      "confidence",
      "record_count",
      "evidence_count",
      "evidence_refs",
      "source_scope",
      "linked_asset_ids",
      "linked_action_ids",
      "linked_starfield_cluster_id",
      "linked_river_range",
      "related_topic_ids",
      "matched_reason",
      "recommended_topic_action",
      "proposal_hint",
      "rollback_hint",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "Data Map",
      "validate:v1.1.6-stage1-phase4",
      "MA-V116-S1P04",
      "No runtime UI",
    ]),
    "stage1_phase4_acceptance_contract",
    "Topic classification acceptance covers states, fields, expansion, screenshots, safety failures, deliverables and rollback",
    "Topic classification detail acceptance is incomplete",
  );
}

function validateRecords() {
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const features = readRepoFile("功能清单.md");
  const dev = readRepoFile("开发记录.md");
  const modelIndex = readRepoFile("模型参数文件.md");
  const changelog = readRepoFile("CHANGELOG.md");
  const packageSource = readRepoFile("apps/memory-atlas/package.json");

  assertCondition(
    hasAll(delivery, [
      "Stage 1 Phase 4：Topic Classification Detail Contract",
      "docs/product/topic_classification_detail_contract.md",
      "docs/acceptance/topic_classification_detail_acceptance.md",
      "Stage 1 Phase 4 状态：`phase_1_4_contract_created_pending_stage_review`",
      "Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入",
    ]),
    "delivery_record_stage1_phase4",
    "Delivery record captures Stage 1 Phase 4 scope, artifacts, status, boundaries, and next step",
    "Delivery record is missing Stage 1 Phase 4 state",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 1 Phase 4 主题分类明细门槛",
      "PARAM-MA-V116-S1P04-001",
      "PARAM-MA-V116-S1P04-009",
      "topic_classification_detail_contract.md",
    ]),
    "model_parameters_stage1_phase4",
    "Model parameters record the topic classification thresholds and evidence references",
    "Project model parameters are missing Stage 1 Phase 4 gates",
  );

  assertCondition(
    hasAll(features, [
      "FEAT-MA-V116-S1P04",
      "EVID-MA-V116-S1P04-TOPIC-CONTRACT",
      "EVID-MA-V116-S1P04-TOPIC-ACCEPTANCE",
      "主题分类明细",
    ]),
    "feature_list_stage1_phase4",
    "Feature list records Stage 1 Phase 4 feature and evidence",
    "Feature list is missing Stage 1 Phase 4 entries",
  );

  assertCondition(
    hasAll(dev, [
      "MA-V116-S1P04",
      "Topic Classification Detail Contract",
      "ACC-MA-V116-S1P04",
      "phase_1_4_contract_created_pending_stage_review",
      "Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入",
    ]),
    "development_record_stage1_phase4",
    "Development record captures Stage 1 Phase 4 task, acceptance, status, and stop boundary",
    "Development record is missing Stage 1 Phase 4",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MOD-MA-V116-S1P04",
      "PARAM-MA-V116-S1P04-001",
      "PARAM-MA-V116-S1P04-009",
      "EVID-MA-V116-S1P04-TOPIC-CONTRACT",
    ]),
    "model_index_stage1_phase4",
    "Root model parameter file records Stage 1 Phase 4 model and parameters",
    "Root model parameter file is missing Stage 1 Phase 4",
  );

  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.6 Stage 1 Phase 4",
      "topic_classification_detail_contract.md",
      "validate:v1.1.6-stage1-phase4",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage1_phase4",
    "Changelog records Stage 1 Phase 4 artifacts, validator and non-goal boundaries",
    "Changelog is missing Stage 1 Phase 4 entry",
  );

  assertCondition(
    packageSource.includes('"validate:v1.1.6-stage1-phase4": "node scripts/validate_memory_atlas_v1_1_6_stage1_phase4.cjs"'),
    "package_script_stage1_phase4",
    "Package script exposes validate:v1.1.6-stage1-phase4",
    "Package script validate:v1.1.6-stage1-phase4 is missing",
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotePath=false", "status", "--short", "--", "OpenAIDatabase"], { cwd: worktreeRoot });
  const changed = result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3))
    .map((line) => line.replace(/^OpenAIDatabase\//, ""))
    .map((line) => line.replace(/^\"(.+)\"$/, "$1"))
    .filter(Boolean);

  const allowed = [
    "CHANGELOG.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/product/memory_overview_usage_contract.md",
    "docs/acceptance/memory_overview_usage_acceptance.md",
    "docs/product/suggested_action_detail_contract.md",
    "docs/acceptance/suggested_action_detail_acceptance.md",
    "docs/product/tier_asset_detail_contract.md",
    "docs/acceptance/tier_asset_detail_acceptance.md",
    "docs/product/topic_classification_detail_contract.md",
    "docs/acceptance/topic_classification_detail_acceptance.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase3.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase4.cjs",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage1_phase4_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 Phase 1-4 contracts, records, validators, and package script",
    "Unexpected OpenAIDatabase paths changed",
    { changed, outside },
  );
}

try {
  [
    "docs/product/memory_overview_usage_contract.md",
    "docs/acceptance/memory_overview_usage_acceptance.md",
    "docs/product/suggested_action_detail_contract.md",
    "docs/acceptance/suggested_action_detail_acceptance.md",
    "docs/product/tier_asset_detail_contract.md",
    "docs/acceptance/tier_asset_detail_acceptance.md",
    "docs/product/topic_classification_detail_contract.md",
    "docs/acceptance/topic_classification_detail_acceptance.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "CHANGELOG.md",
  ].forEach(validateTextFile);
  validateProductContract();
  validateAcceptanceContract();
  validateRecords();
  validateChangeScope();
  pass("stage1_phase4_boundary", "No runtime UI/CSS/raw-private/direct-writeback/proposal-editor/search-review/data-map/upload work is required or present in this phase");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage1-phase4", checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.6-stage1-phase4",
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
