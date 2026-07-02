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
  const contract = readRepoFile("docs/product/proposal_only_adjustment_entry_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas proposal-only 调整入口合同",
      "v1.1.6 Stage 1 Phase 5",
      "memory_overview",
      "suggested_action_detail",
      "tier_asset_detail",
      "topic_classification_detail",
      "inspector",
      "overview_signal",
      "suggested_action",
      "tier_asset",
      "topic_classification",
      "importance",
      "priority",
      "topic_category",
      "action_status",
      "due_window",
      "hidden_until",
      "stale_override",
      "confidence_note",
      "proposal_id",
      "proposal_schema_version",
      "parent_snapshot_id",
      "entry_surface",
      "target_type",
      "target_id",
      "field",
      "old_value_ref",
      "proposed_value",
      "reason",
      "evidence_refs",
      "created_at",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "rollback_hint",
      "active memory",
      "raw/private",
      "agent/human",
      "完整 proposal 编辑工作区",
      "Search 2.0",
      "Data Map",
      "本 phase 不修改运行时",
    ]),
    "stage1_phase5_product_contract",
    "Proposal-only entry contract covers entry surfaces, targets, fields, draft schema, user copy, Inspector handoff, safety and future-phase boundaries",
    "Proposal-only adjustment entry contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/proposal_only_adjustment_entry_acceptance.md");
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas proposal-only 调整入口验收",
      "v1.1.6 Stage 1 Phase 5",
      "memory_overview",
      "suggested_action_detail",
      "tier_asset_detail",
      "topic_classification_detail",
      "inspector",
      "overview_signal",
      "suggested_action",
      "tier_asset",
      "topic_classification",
      "importance",
      "priority",
      "topic_category",
      "action_status",
      "due_window",
      "hidden_until",
      "stale_override",
      "confidence_note",
      "proposal_id",
      "proposal_schema_version",
      "parent_snapshot_id",
      "old_value_ref",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "rollback_hint",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "完整 proposal 编辑工作区",
      "validate:v1.1.6-stage1-phase5",
      "MA-V116-S1P05",
      "No runtime UI",
    ]),
    "stage1_phase5_acceptance_contract",
    "Proposal-only entry acceptance covers entry surfaces, target types, fields, schema, screenshots, safety failures, deliverables and rollback",
    "Proposal-only adjustment entry acceptance is incomplete",
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
      "Stage 1 Phase 5：Proposal-only Adjustment Entry Contract",
      "docs/product/proposal_only_adjustment_entry_contract.md",
      "docs/acceptance/proposal_only_adjustment_entry_acceptance.md",
      "Stage 1 Phase 5 状态：`phase_1_5_contract_created_pending_stage_review`",
      "Stage 1 整体复审未执行",
    ]),
    "delivery_record_stage1_phase5",
    "Delivery record captures Stage 1 Phase 5 scope, artifacts, status, boundaries, and next step",
    "Delivery record is missing Stage 1 Phase 5 state",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 1 Phase 5 proposal-only 调整入口门槛",
      "PARAM-MA-V116-S1P05-001",
      "PARAM-MA-V116-S1P05-010",
      "proposal_only_adjustment_entry_contract.md",
    ]),
    "model_parameters_stage1_phase5",
    "Model parameters record the proposal-only entry thresholds and evidence references",
    "Project model parameters are missing Stage 1 Phase 5 gates",
  );

  assertCondition(
    hasAll(features, [
      "FEAT-MA-V116-S1P05",
      "EVID-MA-V116-S1P05-PROPOSAL-ENTRY-CONTRACT",
      "EVID-MA-V116-S1P05-PROPOSAL-ENTRY-ACCEPTANCE",
      "proposal-only 调整入口",
    ]),
    "feature_list_stage1_phase5",
    "Feature list records Stage 1 Phase 5 feature and evidence",
    "Feature list is missing Stage 1 Phase 5 entries",
  );

  assertCondition(
    hasAll(dev, [
      "MA-V116-S1P05",
      "Proposal-only Adjustment Entry Contract",
      "ACC-MA-V116-S1P05",
      "phase_1_5_contract_created_pending_stage_review",
      "Stage 1 整体复审未执行",
    ]),
    "development_record_stage1_phase5",
    "Development record captures Stage 1 Phase 5 task, acceptance, status, and stop boundary",
    "Development record is missing Stage 1 Phase 5",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MOD-MA-V116-S1P05",
      "PARAM-MA-V116-S1P05-001",
      "PARAM-MA-V116-S1P05-010",
      "EVID-MA-V116-S1P05-PROPOSAL-ENTRY-CONTRACT",
    ]),
    "model_index_stage1_phase5",
    "Root model parameter file records Stage 1 Phase 5 model and parameters",
    "Root model parameter file is missing Stage 1 Phase 5",
  );

  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.6 Stage 1 Phase 5",
      "proposal_only_adjustment_entry_contract.md",
      "validate:v1.1.6-stage1-phase5",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage1_phase5",
    "Changelog records Stage 1 Phase 5 artifacts, validator and non-goal boundaries",
    "Changelog is missing Stage 1 Phase 5 entry",
  );

  assertCondition(
    packageSource.includes('"validate:v1.1.6-stage1-phase5": "node scripts/validate_memory_atlas_v1_1_6_stage1_phase5.cjs"'),
    "package_script_stage1_phase5",
    "Package script exposes validate:v1.1.6-stage1-phase5",
    "Package script validate:v1.1.6-stage1-phase5 is missing",
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
    "docs/product/proposal_only_adjustment_entry_contract.md",
    "docs/acceptance/proposal_only_adjustment_entry_acceptance.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase3.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase4.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase5.cjs",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage1_phase5_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 Phase 1-5 contracts, records, validators, and package script",
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
    "docs/product/proposal_only_adjustment_entry_contract.md",
    "docs/acceptance/proposal_only_adjustment_entry_acceptance.md",
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
  pass("stage1_phase5_boundary", "No runtime UI/CSS/raw-private/direct-writeback/proposal-editor/search-review/data-map/upload work is required or present in this phase");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage1-phase5", checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.6-stage1-phase5",
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
