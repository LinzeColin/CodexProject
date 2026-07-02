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
  const contract = readRepoFile("docs/product/search_2_0_workflow_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas Search 2.0 工作流合同",
      "v1.1.6 Stage 4 Phase 1",
      "search_2_0_workflow",
      "query_input",
      "result_list",
      "matched_reason",
      "jump_to_starfield",
      "jump_to_river",
      "open_inspector",
      "title",
      "summary",
      "source",
      "tier",
      "topic",
      "recency",
      "importance",
      "evidence_refs",
      "filter_state",
      "search_session_summary",
      "zero_result_recovery",
      "proposal_candidate",
      "Search 2.0",
      "Review / Summary / Iteration",
      "Data Map 2.0",
      "raw/private",
      "No runtime UI",
      "No direct writeback",
      "No GitHub main upload",
      "本 phase 不修改运行时",
    ]),
    "stage4_phase1_product_contract",
    "Search 2.0 contract covers query, result metadata, matched reason, navigation actions, recovery, proposal handoff, and future-phase boundaries",
    "Search 2.0 product contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/search_2_0_workflow_acceptance.md");
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas Search 2.0 工作流验收",
      "v1.1.6 Stage 4 Phase 1",
      "search_2_0_workflow",
      "query_input",
      "result_list",
      "matched_reason",
      "jump_to_starfield",
      "jump_to_river",
      "open_inspector",
      "title",
      "summary",
      "source",
      "tier",
      "topic",
      "recency",
      "importance",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "zero_result_recovery",
      "proposal_candidate",
      "raw/private/cookie/session/secret",
      "validate:v1.1.6-stage4-phase1",
      "MA-V116-S4P01",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "stage4_phase1_acceptance_contract",
    "Search 2.0 acceptance covers result anatomy, navigation, responsive evidence, safety failures, and deliverables",
    "Search 2.0 acceptance contract is incomplete",
  );
}

function validateRecords() {
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const featureList = readRepoFile("功能清单.md");
  const development = readRepoFile("开发记录.md");
  const modelIndex = readRepoFile("模型参数文件.md");
  const changelog = readRepoFile("CHANGELOG.md");
  const packageJson = readRepoFile("apps/memory-atlas/package.json");

  assertCondition(
    hasAll(delivery, [
      "Stage 4 Phase 1",
      "Search 2.0 Workflow Contract",
      "search_2_0_workflow",
      "validate:v1.1.6-stage4-phase1",
      "phase_4_1_contract_created_pending_stage_review",
      "MA-V116-S4P01",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage4_phase1",
    "Delivery record captures Stage 4 Phase 1 scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 4 Phase 1 details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 4 Phase 1 Search 2.0 工作流参数",
      "search_2_0_workflow",
      "phase_4_1_contract_created_pending_stage_review",
      "PARAM-MA-V116-S4P01-001",
      "PARAM-MA-V116-S4P01-002",
      "PARAM-MA-V116-S4P01-003",
      "PARAM-MA-V116-S4P01-004",
      "PARAM-MA-V116-S4P01-005",
      "PARAM-MA-V116-S4P01-006",
      "PARAM-MA-V116-S4P01-007",
    ]),
    "model_parameters_stage4_phase1",
    "Model parameters document Stage 4 Phase 1 search workflow fields, actions, safety and validator",
    "Model parameters are missing Stage 4 Phase 1 details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S4P01",
      "Memory Atlas v1.1.6 Stage 4 Phase 1",
      "Search 2.0 工作流合同",
      "EVID-MA-V116-S4P01",
      "validate:v1.1.6-stage4-phase1",
      "phase_4_1_contract_created_pending_stage_review",
    ]),
    "feature_list_stage4_phase1",
    "Feature list registers Stage 4 Phase 1 feature, evidence and validation",
    "Feature list is missing Stage 4 Phase 1 details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage4_phase01",
      "MA-V116-S4P01",
      "Search 2.0 Workflow Contract",
      "phase_4_1_contract_created_pending_stage_review",
      "ACC-MA-V116-S4P01",
      "validate:v1.1.6-stage4-phase1",
      "search_2_0_workflow_contract.md",
      "search_2_0_workflow_acceptance.md",
    ]),
    "development_record_stage4_phase1",
    "Development record captures Stage 4 Phase 1 objective, tasks, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 4 Phase 1 details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S4P01",
      "Search 2.0 工作流",
      "search_2_0_workflow",
      "phase_4_1_contract_created_pending_stage_review",
      "validate:v1.1.6-stage4-phase1",
      "search_result_no_raw_private_payload",
    ]),
    "model_index_stage4_phase1",
    "Root model parameter file records Stage 4 Phase 1 model and parameters",
    "Root model parameter file is missing Stage 4 Phase 1 details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 4 Phase 1",
      "Search 2.0 Workflow Contract",
      "search_2_0_workflow_contract.md",
      "search_2_0_workflow_acceptance.md",
      "validate:v1.1.6-stage4-phase1",
      "phase_4_1_contract_created_pending_stage_review",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage4_phase1",
    "Changelog records Stage 4 Phase 1 deliverables and non-goal boundaries",
    "Changelog is missing Stage 4 Phase 1 details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage4-phase1"'),
    "package_script_stage4_phase1",
    "Package script exposes validate:v1.1.6-stage4-phase1",
    "Package script is missing validate:v1.1.6-stage4-phase1",
  );
}

function validateChangedPaths() {
  const status = run("git", ["status", "--short", "-z", "--", "OpenAIDatabase"], { cwd: path.resolve(repoRoot, "..") }).stdout;
  const changed = status
    .split("\0")
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .map((line) => line.replace(/^OpenAIDatabase\//, ""));

  const allowedPrefixes = [
    "CHANGELOG.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage3",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage4_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage4_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage4.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/detail_visibility_workbench_acceptance.md",
    "docs/acceptance/memory_overview_usage_acceptance.md",
    "docs/acceptance/proposal_only_adjustment_entry_acceptance.md",
    "docs/acceptance/proposal_only_adjustment_workspace_acceptance.md",
    "docs/acceptance/proposal_queue_persistence_acceptance.md",
    "docs/acceptance/review_summary_iteration_workflow_acceptance.md",
    "docs/acceptance/search_2_0_workflow_acceptance.md",
    "docs/acceptance/data_map_2_0_workflow_acceptance.md",
    "docs/acceptance/suggested_action_detail_acceptance.md",
    "docs/acceptance/suggested_action_lane_visibility_acceptance.md",
    "docs/acceptance/tier_asset_detail_acceptance.md",
    "docs/acceptance/tier_asset_lane_visibility_acceptance.md",
    "docs/acceptance/topic_classification_detail_acceptance.md",
    "docs/acceptance/topic_classification_lane_visibility_acceptance.md",
    "docs/product/detail_visibility_workbench_contract.md",
    "docs/product/memory_overview_usage_contract.md",
    "docs/product/proposal_only_adjustment_entry_contract.md",
    "docs/product/proposal_only_adjustment_workspace_contract.md",
    "docs/product/proposal_queue_persistence_contract.md",
    "docs/product/review_summary_iteration_workflow_contract.md",
    "docs/product/search_2_0_workflow_contract.md",
    "docs/product/data_map_2_0_workflow_contract.md",
    "docs/product/suggested_action_detail_contract.md",
    "docs/product/suggested_action_lane_visibility_contract.md",
    "docs/product/tier_asset_detail_contract.md",
    "docs/product/tier_asset_lane_visibility_contract.md",
    "docs/product/topic_classification_detail_contract.md",
    "docs/product/topic_classification_lane_visibility_contract.md",
    "docs/reviews/memory_atlas_v1_1_6_stage1_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage2_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage3_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage4_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage5_review.md",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage5_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage5.cjs",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowedPrefixes.some((prefix) => file === prefix || file.startsWith(prefix)));
  assertCondition(
    outside.length === 0,
    "stage4_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1-5 contracts, acceptance, records, reviews, validators, and package script",
    "Unexpected files changed outside Stage 4 Phase 1 bounded scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const forbiddenFiles = [
    "src/App.tsx",
    "src/App.css",
    "src/main.tsx",
    "src/data",
    "src/lib/writeback",
  ];
  const status = run("git", ["status", "--short", "-z", "--", "OpenAIDatabase/apps/memory-atlas/src"], { cwd: path.resolve(repoRoot, "..") }).stdout;
  const touchedForbidden = status
    .split("\0")
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .map((line) => line.replace(/^OpenAIDatabase\/apps\/memory-atlas\//, ""))
    .filter((file) => forbiddenFiles.some((forbidden) => file === forbidden || file.startsWith(forbidden)));

  assertCondition(
    touchedForbidden.length === 0,
    "stage4_phase1_boundary",
    "No runtime UI/CSS/data/writeback work is present in this contract phase",
    "Stage 4 Phase 1 touched runtime files outside contract scope",
    { touchedForbidden },
  );
}

function main() {
  try {
    [
      "docs/product/search_2_0_workflow_contract.md",
      "docs/acceptance/search_2_0_workflow_acceptance.md",
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
    validateChangedPaths();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage4-phase1", checks }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({
      status: "FAIL",
      stage: "v1.1.6-stage4-phase1",
      message: error.message,
      details: error.details || {},
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
