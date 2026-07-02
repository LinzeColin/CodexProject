#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
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
  const contract = readRepoFile("docs/product/memory_overview_usage_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas 记忆总览与系统使用说明合同",
      "v1.1.6 Stage 1 Phase 1",
      "今日状态",
      "Memory Weather",
      "建议动作",
      "低价值循环",
      "新生机会",
      "层级资产摘要",
      "主题分类摘要",
      "Mini 记忆星系",
      "记忆时间河脉冲",
      "系统使用说明",
      "Presentation",
      "Analysis",
      "Inspector",
      "Proposal",
      "proposal-only",
      "old value",
      "proposed value",
      "rollback hint",
      "raw transcript",
      "cookies、sessions、browser state",
      "Stage 2",
      "Stage 3",
      "Stage 4",
      "Stage 5",
      "本 phase 不修改运行时",
    ]),
    "stage1_phase1_product_contract",
    "Overview usage contract covers system entry, required modules, usage path, modes, Inspector, Proposal, privacy and future-stage boundaries",
    "Memory overview usage contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/memory_overview_usage_acceptance.md");
  const requiredRows = [
    "默认入口定位",
    "今日状态",
    "Memory Weather",
    "建议动作",
    "低价值循环",
    "新生机会",
    "层级资产摘要",
    "主题分类摘要",
    "视觉预览",
    "系统使用说明",
    "模式说明",
    "Proposal 说明",
  ];
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas 记忆总览与系统使用说明验收",
      "v1.1.6 Stage 1 Phase 1",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "Stage 2-5",
      "validate:v1.1.6-stage1-phase1",
      "MA-V116-S1P01",
      "No runtime UI",
    ].concat(requiredRows)),
    "stage1_phase1_acceptance_contract",
    "Acceptance contract covers static checks, text layout, screenshot entry, safety failures, deliverables, and rollback",
    "Memory overview usage acceptance is incomplete",
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
      "Stage 1 Phase 1：Memory Overview Usage Contract",
      "docs/product/memory_overview_usage_contract.md",
      "docs/acceptance/memory_overview_usage_acceptance.md",
      "Stage 1 Phase 1 状态：`phase_1_1_contract_created_pending_stage_review`",
      "Stage 2-5 未进入",
    ]),
    "delivery_record_stage1_phase1",
    "Delivery record captures Stage 1 Phase 1 scope, artifacts, status, boundaries, and next step",
    "Delivery record is missing Stage 1 Phase 1 state",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 1 Phase 1 记忆总览使用说明门槛",
      "PARAM-MA-V116-S1P01-001",
      "PARAM-MA-V116-S1P01-006",
      "memory_overview_usage_contract.md",
    ]),
    "model_parameters_stage1_phase1",
    "Model parameters record the overview usage thresholds and evidence references",
    "Project model parameters are missing Stage 1 Phase 1 gates",
  );

  assertCondition(
    hasAll(features, [
      "FEAT-MA-V116-S1P01",
      "EVID-MA-V116-S1P01-USAGE-CONTRACT",
      "EVID-MA-V116-S1P01-USAGE-ACCEPTANCE",
      "记忆总览与系统使用说明",
    ]),
    "feature_list_stage1_phase1",
    "Feature list records Stage 1 Phase 1 feature and evidence",
    "Feature list is missing Stage 1 Phase 1 entries",
  );

  assertCondition(
    hasAll(dev, [
      "MA-V116-S1P01",
      "Memory Overview Usage Contract",
      "ACC-MA-V116-S1P01",
      "phase_1_1_contract_created_pending_stage_review",
      "Stage 2-5 未进入",
    ]),
    "development_record_stage1_phase1",
    "Development record captures Stage 1 Phase 1 task, acceptance, status, and stop boundary",
    "Development record is missing Stage 1 Phase 1",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MOD-MA-V116-S1P01",
      "PARAM-MA-V116-S1P01-001",
      "PARAM-MA-V116-S1P01-006",
      "EVID-MA-V116-S1P01-USAGE-CONTRACT",
    ]),
    "model_index_stage1_phase1",
    "Root model parameter file records Stage 1 Phase 1 model and parameters",
    "Root model parameter file is missing Stage 1 Phase 1",
  );

  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.6 Stage 1 Phase 1",
      "memory_overview_usage_contract.md",
      "validate:v1.1.6-stage1-phase1",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage1_phase1",
    "Changelog records Stage 1 Phase 1 artifacts, validator and non-goal boundaries",
    "Changelog is missing Stage 1 Phase 1 entry",
  );

  assertCondition(
    packageSource.includes('"validate:v1.1.6-stage1-phase1": "node scripts/validate_memory_atlas_v1_1_6_stage1_phase1.cjs"'),
    "package_script_stage1_phase1",
    "Package script exposes validate:v1.1.6-stage1-phase1",
    "Package script validate:v1.1.6-stage1-phase1 is missing",
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotePath=false", "status", "--short", "--", "OpenAIDatabase"], { cwd: path.resolve(repoRoot, "..") });
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
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase1.cjs",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage1_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 Phase 1 contracts, records, validator, and package script",
    "Unexpected OpenAIDatabase paths changed",
    { changed, outside },
  );
}

try {
  [
    "docs/product/memory_overview_usage_contract.md",
    "docs/acceptance/memory_overview_usage_acceptance.md",
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
  pass("stage1_phase1_boundary", "No runtime UI/CSS/raw-private/direct-writeback/Stage2-5/upload work is required or present in this phase");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage1-phase1", checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.6-stage1-phase1",
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
