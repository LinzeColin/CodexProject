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
  const contract = readRepoFile("docs/product/suggested_action_detail_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas 建议动作明细合同",
      "v1.1.6 Stage 1 Phase 2",
      "action_id",
      "action_type",
      "reason",
      "roi_score",
      "effort_cost",
      "urgency",
      "confidence",
      "evidence_count",
      "evidence_refs",
      "source_scope",
      "linked_theme_ids",
      "next_step",
      "proposal_hint",
      "rollback_hint",
      "continue",
      "review",
      "consolidate",
      "explore",
      "defer",
      "Inspector",
      "proposal-only",
      "raw transcript",
      "active memory",
      "层级资产完整模型",
      "主题分类完整模型",
      "Proposal-only 编辑 schema",
      "Search 2.0",
      "Data Map 2.0",
      "本 phase 不修改运行时",
    ]),
    "stage1_phase2_product_contract",
    "Suggested action contract covers required fields, action types, Inspector handoff, proposal-only safety, privacy and future-phase boundaries",
    "Suggested action detail contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/suggested_action_detail_acceptance.md");
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas 建议动作明细验收",
      "v1.1.6 Stage 1 Phase 2",
      "action_id",
      "action_type",
      "reason",
      "roi_score",
      "effort_cost",
      "urgency",
      "confidence",
      "evidence_count",
      "evidence_refs",
      "source_scope",
      "linked_theme_ids",
      "next_step",
      "proposal_hint",
      "rollback_hint",
      "continue",
      "review",
      "consolidate",
      "explore",
      "defer",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "层级资产模型",
      "主题分类模型",
      "Data Map",
      "validate:v1.1.6-stage1-phase2",
      "MA-V116-S1P02",
      "No runtime UI",
    ]),
    "stage1_phase2_acceptance_contract",
    "Suggested action acceptance covers fields, action types, expansion, screenshots, safety failures, deliverables and rollback",
    "Suggested action detail acceptance is incomplete",
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
      "Stage 1 Phase 2：Suggested Action Detail Contract",
      "docs/product/suggested_action_detail_contract.md",
      "docs/acceptance/suggested_action_detail_acceptance.md",
      "Stage 1 Phase 2 状态：`phase_1_2_contract_created_pending_stage_review`",
      "层级资产和主题分类完整模型未进入",
    ]),
    "delivery_record_stage1_phase2",
    "Delivery record captures Stage 1 Phase 2 scope, artifacts, status, boundaries, and next step",
    "Delivery record is missing Stage 1 Phase 2 state",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 1 Phase 2 建议动作明细门槛",
      "PARAM-MA-V116-S1P02-001",
      "PARAM-MA-V116-S1P02-008",
      "suggested_action_detail_contract.md",
    ]),
    "model_parameters_stage1_phase2",
    "Model parameters record the suggested action thresholds and evidence references",
    "Project model parameters are missing Stage 1 Phase 2 gates",
  );

  assertCondition(
    hasAll(features, [
      "FEAT-MA-V116-S1P02",
      "EVID-MA-V116-S1P02-ACTION-CONTRACT",
      "EVID-MA-V116-S1P02-ACTION-ACCEPTANCE",
      "建议动作明细",
    ]),
    "feature_list_stage1_phase2",
    "Feature list records Stage 1 Phase 2 feature and evidence",
    "Feature list is missing Stage 1 Phase 2 entries",
  );

  assertCondition(
    hasAll(dev, [
      "MA-V116-S1P02",
      "Suggested Action Detail Contract",
      "ACC-MA-V116-S1P02",
      "phase_1_2_contract_created_pending_stage_review",
      "层级资产和主题分类完整模型未进入",
    ]),
    "development_record_stage1_phase2",
    "Development record captures Stage 1 Phase 2 task, acceptance, status, and stop boundary",
    "Development record is missing Stage 1 Phase 2",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MOD-MA-V116-S1P02",
      "PARAM-MA-V116-S1P02-001",
      "PARAM-MA-V116-S1P02-008",
      "EVID-MA-V116-S1P02-ACTION-CONTRACT",
    ]),
    "model_index_stage1_phase2",
    "Root model parameter file records Stage 1 Phase 2 model and parameters",
    "Root model parameter file is missing Stage 1 Phase 2",
  );

  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.6 Stage 1 Phase 2",
      "suggested_action_detail_contract.md",
      "validate:v1.1.6-stage1-phase2",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage1_phase2",
    "Changelog records Stage 1 Phase 2 artifacts, validator and non-goal boundaries",
    "Changelog is missing Stage 1 Phase 2 entry",
  );

  assertCondition(
    packageSource.includes('"validate:v1.1.6-stage1-phase2": "node scripts/validate_memory_atlas_v1_1_6_stage1_phase2.cjs"'),
    "package_script_stage1_phase2",
    "Package script exposes validate:v1.1.6-stage1-phase2",
    "Package script validate:v1.1.6-stage1-phase2 is missing",
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
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase2.cjs",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage1_phase2_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 Phase 1-2 contracts, records, validators, and package script",
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
  pass("stage1_phase2_boundary", "No runtime UI/CSS/raw-private/direct-writeback/layer-asset/topic-model/search-review/data-map/upload work is required or present in this phase");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage1-phase2", checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.6-stage1-phase2",
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
