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
  const contract = readRepoFile("docs/product/proposal_only_adjustment_workspace_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas proposal-only 调整工作区合同",
      "v1.1.6 Stage 3 Phase 1",
      "proposal-only adjustment workspace",
      "proposal_queue",
      "target_context_panel",
      "field_editor_panel",
      "proposal_diff_preview",
      "safety_review_panel",
      "rollback_panel",
      "importance",
      "priority",
      "topic_category",
      "action_status",
      "due_window",
      "hidden_until",
      "stale_override",
      "confidence_note",
      "overview_signal",
      "suggested_action",
      "tier_asset",
      "topic_classification",
      "proposal_id",
      "parent_snapshot_id",
      "target_id",
      "field",
      "old_value",
      "proposed_value",
      "reason",
      "created_at",
      "rollback_hint",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "draft",
      "needs_review",
      "ready_for_agent_apply",
      "rejected",
      "superseded",
      "Inspector",
      "proposal-only",
      "raw/private",
      "active memory",
      "agent apply",
      "Search 2.0",
      "Data Map 2.0",
      "本 phase 不修改运行时",
    ]),
    "stage3_phase1_product_contract",
    "Proposal-only adjustment workspace contract covers workspace regions, allowed fields, targets, schema, states, safety panels, Inspector handoff and future-phase boundaries",
    "Proposal-only adjustment workspace contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/proposal_only_adjustment_workspace_acceptance.md");
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas proposal-only 调整工作区验收",
      "v1.1.6 Stage 3 Phase 1",
      "proposal_queue",
      "target_context_panel",
      "field_editor_panel",
      "proposal_diff_preview",
      "safety_review_panel",
      "rollback_panel",
      "importance",
      "priority",
      "topic_category",
      "action_status",
      "due_window",
      "hidden_until",
      "stale_override",
      "confidence_note",
      "overview_signal",
      "suggested_action",
      "tier_asset",
      "topic_classification",
      "proposal_id",
      "parent_snapshot_id",
      "target_id",
      "field",
      "old_value",
      "proposed_value",
      "reason",
      "created_at",
      "rollback_hint",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "draft",
      "needs_review",
      "ready_for_agent_apply",
      "rejected",
      "superseded",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "agent apply",
      "Search 2.0",
      "Data Map 2.0",
      "validate:v1.1.6-stage3-phase1",
      "MA-V116-S3P01",
      "No runtime UI",
    ]),
    "stage3_phase1_acceptance_contract",
    "Proposal-only adjustment workspace acceptance covers workspace regions, fields, schema, states, screenshots, safety failures and deliverables",
    "Proposal-only adjustment workspace acceptance is incomplete",
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
      "Stage 3 Phase 1",
      "Proposal-only Adjustment Workspace Contract",
      "proposal-only 调整工作区",
      "validate:v1.1.6-stage3-phase1",
      "phase_3_1_contract_created_pending_stage_review",
      "MA-V116-S3P01",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage3_phase1",
    "Delivery record captures Stage 3 Phase 1 scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 3 Phase 1 details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 3 Phase 1 proposal-only 调整工作区门槛",
      "phase_3_1_contract_created_pending_stage_review",
      "PARAM-MA-V116-S3P01-001 workspace_regions",
      "PARAM-MA-V116-S3P01-002 allowed_fields",
      "PARAM-MA-V116-S3P01-003 proposal_target_types",
      "PARAM-MA-V116-S3P01-004 proposal_required_schema_fields",
      "PARAM-MA-V116-S3P01-005 proposal_statuses",
      "PARAM-MA-V116-S3P01-006 proposal_boundary",
      "PARAM-MA-V116-S3P01-007 stage3_phase1_required_validator",
    ]),
    "model_parameters_stage3_phase1",
    "Model parameters document Stage 3 Phase 1 proposal workspace assumptions, fields, schema, statuses and validator",
    "Model parameters are missing Stage 3 Phase 1 details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S3P01",
      "Memory Atlas proposal-only 调整工作区",
      "EVID-MA-V116-S3P01-PROPOSAL-WORKSPACE-CONTRACT",
      "EVID-MA-V116-S3P01-PROPOSAL-WORKSPACE-ACCEPTANCE",
      "validate:v1.1.6-stage3-phase1",
      "phase_3_1_contract_created_pending_stage_review",
    ]),
    "feature_list_stage3_phase1",
    "Feature list registers Stage 3 Phase 1 feature, evidence and validation",
    "Feature list is missing Stage 3 Phase 1 details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage3_phase01",
      "MA-V116-S3P01 Proposal-only Adjustment Workspace Contract",
      "phase_3_1_contract_created_pending_stage_review",
      "ACC-MA-V116-S3P01",
      "validate:v1.1.6-stage3-phase1",
      "proposal_only_adjustment_workspace_contract.md",
      "proposal_only_adjustment_workspace_acceptance.md",
    ]),
    "development_record_stage3_phase1",
    "Development record captures Stage 3 Phase 1 objective, tasks, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 3 Phase 1 details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S3P01",
      "proposal-only 调整工作区",
      "proposal_queue",
      "proposal_diff_preview",
      "proposal_only_no_direct_active_memory_write",
      "validate:v1.1.6-stage3-phase1",
    ]),
    "model_index_stage3_phase1",
    "Root model parameter file records Stage 3 Phase 1 model and parameters",
    "Root model parameter file is missing Stage 3 Phase 1 details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 3 Phase 1",
      "proposal_only_adjustment_workspace_contract.md",
      "proposal_only_adjustment_workspace_acceptance.md",
      "validate:v1.1.6-stage3-phase1",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage3_phase1",
    "Changelog records Stage 3 Phase 1 deliverables and non-goal boundaries",
    "Changelog is missing Stage 3 Phase 1 details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage3-phase1"'),
    "package_script_stage3_phase1",
    "Package script exposes validate:v1.1.6-stage3-phase1",
    "Package script is missing validate:v1.1.6-stage3-phase1",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage3.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage3_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage3_phase2.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_overview_usage_acceptance.md",
    "docs/acceptance/suggested_action_detail_acceptance.md",
    "docs/acceptance/tier_asset_detail_acceptance.md",
    "docs/acceptance/topic_classification_detail_acceptance.md",
    "docs/acceptance/proposal_only_adjustment_entry_acceptance.md",
    "docs/acceptance/detail_visibility_workbench_acceptance.md",
    "docs/acceptance/suggested_action_lane_visibility_acceptance.md",
    "docs/acceptance/tier_asset_lane_visibility_acceptance.md",
    "docs/acceptance/topic_classification_lane_visibility_acceptance.md",
    "docs/acceptance/proposal_only_adjustment_workspace_acceptance.md",
    "docs/acceptance/proposal_queue_persistence_acceptance.md",
    "docs/product/memory_overview_usage_contract.md",
    "docs/product/suggested_action_detail_contract.md",
    "docs/product/tier_asset_detail_contract.md",
    "docs/product/topic_classification_detail_contract.md",
    "docs/product/proposal_only_adjustment_entry_contract.md",
    "docs/product/detail_visibility_workbench_contract.md",
    "docs/product/suggested_action_lane_visibility_contract.md",
    "docs/product/tier_asset_lane_visibility_contract.md",
    "docs/product/topic_classification_lane_visibility_contract.md",
    "docs/product/proposal_only_adjustment_workspace_contract.md",
    "docs/product/proposal_queue_persistence_contract.md",
    "docs/reviews/memory_atlas_v1_1_6_stage1_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage2_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage3_review.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowedPrefixes.some((prefix) => file === prefix || file.startsWith(prefix)));
  assertCondition(
    outside.length === 0,
    "stage3_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1, Stage 2, Stage 3 Phase 1-2, and Stage 3 review contracts, acceptance, records, reviews, validators, and package script",
    "Unexpected files changed outside Stage 3 Phase 1 bounded scope",
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
  const status = run("git", ["status", "--short", "--", "OpenAIDatabase"], { cwd: path.resolve(repoRoot, "..") }).stdout;
  const touchedForbidden = forbiddenFiles.filter((file) => status.includes(`OpenAIDatabase/apps/memory-atlas/${file}`));
  assertCondition(
    touchedForbidden.length === 0,
    "stage3_phase1_boundary",
    "No runtime UI/CSS/data/writeback/Search/Review/Data Map/agent-apply work is present in this contract phase",
    "Runtime or writeback files were modified in a contract-only phase",
    { touchedForbidden },
  );
}

try {
  [
    "docs/product/proposal_only_adjustment_workspace_contract.md",
    "docs/acceptance/proposal_only_adjustment_workspace_acceptance.md",
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

  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage3-phase1", checks }, null, 2));
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        stage: "v1.1.6-stage3-phase1",
        message: error.message,
        details: error.details || {},
        stdout: error.stdout,
        stderr: error.stderr,
        checks,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}
