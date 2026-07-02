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
  const contract = readRepoFile("docs/product/tier_asset_lane_visibility_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas tier asset lane 可见性合同",
      "v1.1.6 Stage 2 Phase 3",
      "tier_asset_lane",
      "asset_scan_row",
      "asset_decision_row",
      "asset_evidence_drawer",
      "asset_id",
      "asset_tier",
      "title",
      "summary",
      "importance",
      "priority",
      "confidence",
      "staleness_status",
      "evidence_count",
      "evidence_refs",
      "source_scope",
      "linked_action_ids",
      "linked_theme_ids",
      "linked_time_range",
      "recommended_asset_action",
      "proposal_hint",
      "rollback_hint",
      "core_profile",
      "project",
      "decision",
      "workflow",
      "knowledge",
      "opportunity",
      "stale",
      "keep",
      "review",
      "consolidate",
      "lower_priority",
      "validate",
      "defer",
      "high_importance",
      "p0",
      "needs_review",
      "evidence_ready",
      "proposal_recommended",
      "expand asset",
      "compare assets",
      "pin asset",
      "mark reviewed",
      "jump to linked action",
      "clear temporary state",
      "Inspector",
      "proposal-only",
      "raw/private",
      "active memory",
      "Search 2.0",
      "Data Map 2.0",
      "本 phase 不修改运行时",
    ]),
    "stage2_phase3_product_contract",
    "Tier asset lane contract covers information hierarchy, fields, grouping, sorting, badges, expansion, comparison, Inspector handoff, safety and future-phase boundaries",
    "Tier asset lane visibility contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/tier_asset_lane_visibility_acceptance.md");
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas tier asset lane 可见性验收",
      "v1.1.6 Stage 2 Phase 3",
      "asset_scan_row",
      "asset_decision_row",
      "asset_evidence_drawer",
      "asset_id",
      "asset_tier",
      "title",
      "summary",
      "importance",
      "priority",
      "confidence",
      "staleness_status",
      "evidence_count",
      "evidence_refs",
      "source_scope",
      "linked_action_ids",
      "linked_theme_ids",
      "linked_time_range",
      "recommended_asset_action",
      "proposal_hint",
      "rollback_hint",
      "core_profile",
      "project",
      "decision",
      "workflow",
      "knowledge",
      "opportunity",
      "stale",
      "high_importance",
      "medium_importance",
      "low_importance",
      "p0",
      "p1",
      "p2",
      "p3",
      "watch",
      "current",
      "needs_review",
      "unknown",
      "evidence_ready",
      "evidence_thin",
      "missing_evidence",
      "proposal_recommended",
      "proposal_not_needed",
      "expand asset",
      "compare assets",
      "pin asset",
      "mark reviewed",
      "jump to linked action",
      "clear temporary state",
      "source_lane = tier_asset_lane",
      "target_type = tier_asset",
      "empty_state",
      "low_evidence_state",
      "stale_conflict_state",
      "error_state",
      "loading_state",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "Search 2.0",
      "validate:v1.1.6-stage2-phase3",
      "MA-V116-S2P03",
      "No runtime UI",
    ]),
    "stage2_phase3_acceptance_contract",
    "Tier asset lane acceptance covers hierarchy, fields, grouping, sorting, badges, interactions, Inspector handoff, states, screenshots, safety failures, deliverables and rollback",
    "Tier asset lane visibility acceptance is incomplete",
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
      "Stage 2 Phase 3：Tier Asset Lane Visibility Contract",
      "docs/product/tier_asset_lane_visibility_contract.md",
      "docs/acceptance/tier_asset_lane_visibility_acceptance.md",
      "Stage 2 Phase 3 状态：`phase_2_3_contract_created_pending_stage_review`",
      "Stage 2 整体复审未执行",
    ]),
    "delivery_record_stage2_phase3",
    "Delivery record captures Stage 2 Phase 3 scope, artifacts, status, boundaries, and next step",
    "Delivery record is missing Stage 2 Phase 3 state",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 2 Phase 3 tier asset lane 可见性门槛",
      "PARAM-MA-V116-S2P03-001",
      "PARAM-MA-V116-S2P03-010",
      "tier_asset_lane_visibility_contract.md",
    ]),
    "model_parameters_stage2_phase3",
    "Model parameters record the tier asset lane visibility thresholds and evidence references",
    "Project model parameters are missing Stage 2 Phase 3 gates",
  );

  assertCondition(
    hasAll(features, [
      "FEAT-MA-V116-S2P03",
      "EVID-MA-V116-S2P03-TIER-LANE-CONTRACT",
      "EVID-MA-V116-S2P03-TIER-LANE-ACCEPTANCE",
      "tier asset lane 可见性",
    ]),
    "feature_list_stage2_phase3",
    "Feature list records Stage 2 Phase 3 feature and evidence",
    "Feature list is missing Stage 2 Phase 3 entries",
  );

  assertCondition(
    hasAll(dev, [
      "MA-V116-S2P03",
      "Tier Asset Lane Visibility Contract",
      "ACC-MA-V116-S2P03",
      "phase_2_3_contract_created_pending_stage_review",
      "Stage 2 整体复审未执行",
    ]),
    "development_record_stage2_phase3",
    "Development record captures Stage 2 Phase 3 task, acceptance, status, and stop boundary",
    "Development record is missing Stage 2 Phase 3",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MOD-MA-V116-S2P03",
      "PARAM-MA-V116-S2P03-001",
      "PARAM-MA-V116-S2P03-010",
      "EVID-MA-V116-S2P03-TIER-LANE-CONTRACT",
    ]),
    "model_index_stage2_phase3",
    "Root model parameter file records Stage 2 Phase 3 model and parameters",
    "Root model parameter file is missing Stage 2 Phase 3",
  );

  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.6 Stage 2 Phase 3",
      "tier_asset_lane_visibility_contract.md",
      "validate:v1.1.6-stage2-phase3",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage2_phase3",
    "Changelog records Stage 2 Phase 3 artifacts, validator and non-goal boundaries",
    "Changelog is missing Stage 2 Phase 3 entry",
  );

  assertCondition(
    packageSource.includes('"validate:v1.1.6-stage2-phase3": "node scripts/validate_memory_atlas_v1_1_6_stage2_phase3.cjs"'),
    "package_script_stage2_phase3",
    "Package script exposes validate:v1.1.6-stage2-phase3",
    "Package script validate:v1.1.6-stage2-phase3 is missing",
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
    "docs/reviews/memory_atlas_v1_1_6_stage1_review.md",
    "docs/product/detail_visibility_workbench_contract.md",
    "docs/acceptance/detail_visibility_workbench_acceptance.md",
    "docs/product/suggested_action_lane_visibility_contract.md",
    "docs/acceptance/suggested_action_lane_visibility_acceptance.md",
    "docs/product/tier_asset_lane_visibility_contract.md",
    "docs/acceptance/tier_asset_lane_visibility_acceptance.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase3.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase4.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase5.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2_phase3.cjs",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage2_phase3_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 and Stage 2 Phase 1-3 contracts, acceptance, records, reviews, validators, and package script",
    "Unexpected OpenAIDatabase paths changed",
    { changed, outside },
  );
}

try {
  [
    "docs/product/tier_asset_lane_visibility_contract.md",
    "docs/acceptance/tier_asset_lane_visibility_acceptance.md",
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
  pass("stage2_phase3_boundary", "No runtime UI/CSS/raw-private/direct-writeback/search-review-data-map/proposal-editor/agent-apply/upload work is required or present in this phase");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage2-phase3", checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.6-stage2-phase3",
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
