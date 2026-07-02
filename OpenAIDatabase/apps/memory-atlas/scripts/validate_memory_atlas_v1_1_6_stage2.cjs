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

function validatePhase21() {
  const contract = readRepoFile("docs/product/detail_visibility_workbench_contract.md");
  const acceptance = readRepoFile("docs/acceptance/detail_visibility_workbench_acceptance.md");

  assertCondition(
    hasAll(contract, [
      "Memory Atlas 明细可见性工作台合同",
      "v1.1.6 Stage 2 Phase 1",
      "明细可见性工作台",
      "workbench_header",
      "scope_controls",
      "density_mode",
      "suggested_action_lane",
      "tier_asset_lane",
      "topic_classification_lane",
      "collapsed summary",
      "expanded detail",
      "open_inspector",
      "jump_to_related",
      "proposal_only_entry",
      "clear filters",
      "proposal-only",
      "本 phase 不修改运行时",
    ]),
    "phase_2_1_workbench_contract",
    "Detail visibility workbench contract covers required lanes, expansion primitives, filters, Inspector handoff and proposal-only boundary",
    "Detail visibility workbench contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas 明细可见性工作台验收",
      "v1.1.6 Stage 2 Phase 1",
      "suggested_action_lane",
      "tier_asset_lane",
      "topic_classification_lane",
      "collapsed summary",
      "expanded detail",
      "open_inspector",
      "proposal_only_entry",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "validate:v1.1.6-stage2-phase1",
      "MA-V116-S2P01",
    ]),
    "phase_2_1_workbench_acceptance",
    "Detail visibility workbench acceptance covers lanes, fields, states, screenshots, safety failures and deliverables",
    "Detail visibility workbench acceptance is incomplete",
  );
}

function validatePhase22() {
  const contract = readRepoFile("docs/product/suggested_action_lane_visibility_contract.md");
  const acceptance = readRepoFile("docs/acceptance/suggested_action_lane_visibility_acceptance.md");

  assertCondition(
    hasAll(contract, [
      "Memory Atlas suggested action lane 可见性合同",
      "v1.1.6 Stage 2 Phase 2",
      "suggested_action_lane",
      "scan_row",
      "decision_row",
      "evidence_drawer",
      "roi_score",
      "effort_cost",
      "urgency",
      "evidence_refs",
      "linked_theme_ids",
      "linked_asset_ids",
      "next_step",
      "recommended_time_window",
      "expand action",
      "compare actions",
      "pin action",
      "mark reviewed",
      "clear temporary state",
      "source_lane = `suggested_action_lane`",
      "proposal-only",
      "本 phase 不修改运行时",
    ]),
    "phase_2_2_action_lane_contract",
    "Suggested action lane contract covers hierarchy, fields, grouping, interactions, Inspector handoff and proposal-only boundary",
    "Suggested action lane contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas suggested action lane 可见性验收",
      "v1.1.6 Stage 2 Phase 2",
      "scan_row",
      "decision_row",
      "evidence_drawer",
      "roi_score",
      "effort_cost",
      "urgency",
      "source_lane = suggested_action_lane",
      "target_type = suggested_action",
      "empty_state",
      "low_evidence_state",
      "error_state",
      "loading_state",
      "validate:v1.1.6-stage2-phase2",
      "MA-V116-S2P02",
      "No runtime UI",
    ]),
    "phase_2_2_action_lane_acceptance",
    "Suggested action lane acceptance covers fields, interactions, Inspector handoff, states and deliverables",
    "Suggested action lane acceptance is incomplete",
  );
}

function validatePhase23() {
  const contract = readRepoFile("docs/product/tier_asset_lane_visibility_contract.md");
  const acceptance = readRepoFile("docs/acceptance/tier_asset_lane_visibility_acceptance.md");

  assertCondition(
    hasAll(contract, [
      "Memory Atlas tier asset lane 可见性合同",
      "v1.1.6 Stage 2 Phase 3",
      "tier_asset_lane",
      "asset_scan_row",
      "asset_decision_row",
      "asset_evidence_drawer",
      "core_profile",
      "project",
      "decision",
      "workflow",
      "knowledge",
      "opportunity",
      "stale",
      "importance",
      "priority",
      "staleness_status",
      "linked_action_ids",
      "linked_theme_ids",
      "linked_time_range",
      "recommended_asset_action",
      "expand asset",
      "compare assets",
      "jump to linked action",
      "source_lane = `tier_asset_lane`",
      "proposal-only",
      "本 phase 不修改运行时",
    ]),
    "phase_2_3_tier_lane_contract",
    "Tier asset lane contract covers hierarchy, fields, asset groups, interactions, Inspector handoff and proposal-only boundary",
    "Tier asset lane contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas tier asset lane 可见性验收",
      "v1.1.6 Stage 2 Phase 3",
      "asset_scan_row",
      "asset_decision_row",
      "asset_evidence_drawer",
      "core_profile",
      "project",
      "decision",
      "workflow",
      "knowledge",
      "opportunity",
      "stale",
      "source_lane = tier_asset_lane",
      "target_type = tier_asset",
      "stale_conflict_state",
      "validate:v1.1.6-stage2-phase3",
      "MA-V116-S2P03",
      "No runtime UI",
    ]),
    "phase_2_3_tier_lane_acceptance",
    "Tier asset lane acceptance covers fields, groups, interactions, Inspector handoff, states and deliverables",
    "Tier asset lane acceptance is incomplete",
  );
}

function validatePhase24() {
  const contract = readRepoFile("docs/product/topic_classification_lane_visibility_contract.md");
  const acceptance = readRepoFile("docs/acceptance/topic_classification_lane_visibility_acceptance.md");

  assertCondition(
    hasAll(contract, [
      "Memory Atlas topic classification lane 可见性合同",
      "v1.1.6 Stage 2 Phase 4",
      "topic_classification_lane",
      "topic_scan_row",
      "topic_decision_row",
      "topic_evidence_drawer",
      "dominant",
      "rising",
      "declining",
      "emerging",
      "conflict",
      "black_hole",
      "stale",
      "topic_strength",
      "trend",
      "record_count",
      "linked_asset_ids",
      "linked_action_ids",
      "linked_starfield_cluster_id",
      "linked_river_range",
      "matched_reason",
      "recommended_topic_action",
      "jump to starfield",
      "jump to river",
      "source_lane = `topic_classification_lane`",
      "proposal-only",
      "本 phase 不修改运行时",
    ]),
    "phase_2_4_topic_lane_contract",
    "Topic classification lane contract covers hierarchy, fields, topic states, jumps, Inspector handoff and proposal-only boundary",
    "Topic classification lane contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas topic classification lane 可见性验收",
      "v1.1.6 Stage 2 Phase 4",
      "topic_scan_row",
      "topic_decision_row",
      "topic_evidence_drawer",
      "dominant",
      "rising",
      "declining",
      "emerging",
      "conflict",
      "black_hole",
      "stale",
      "source_lane = topic_classification_lane",
      "target_type = topic_classification",
      "conflict_state",
      "black_hole_state",
      "stale_state",
      "validate:v1.1.6-stage2-phase4",
      "MA-V116-S2P04",
      "No runtime UI",
    ]),
    "phase_2_4_topic_lane_acceptance",
    "Topic classification lane acceptance covers fields, groups, interactions, Inspector handoff, states and deliverables",
    "Topic classification lane acceptance is incomplete",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage2_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 2 Review",
      "Stage 2 is review-passed",
      "Phase 2.1",
      "Phase 2.2",
      "Phase 2.3",
      "Phase 2.4",
      "validate:v1.1.6-stage2",
      "stage=v1.1.6-stage2",
      "No runtime UI implementation",
      "No raw/private/cookie/session/secret data access",
      "No direct frontend writeback",
      "No Stage 3-5 work in this review",
      "No GitHub main upload in this review",
      "branch is behind `origin/main`",
      "Local `.DS_Store` is untracked",
    ]),
    "stage2_review_artifact",
    "Stage 2 review artifact records phase coverage, fix applied, validation, boundaries, risks and next gate",
    "Stage 2 review artifact is incomplete",
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
      "Stage 2 Phase 1：Detail Visibility Workbench Contract",
      "Stage 2 Phase 2：Suggested Action Lane Visibility Contract",
      "Stage 2 Phase 3：Tier Asset Lane Visibility Contract",
      "Stage 2 Phase 4：Topic Classification Lane Visibility Contract",
      "Stage 2 整体复审",
      "stage_2_review_passed_pending_stage3",
      "docs/reviews/memory_atlas_v1_1_6_stage2_review.md",
      "validate:v1.1.6-stage2",
      "不上传 GitHub main",
    ]),
    "delivery_record_stage2_review",
    "Delivery record captures all four phases, whole-stage review, validator, upload boundary, and pending-Stage-3 status",
    "Delivery record is missing Stage 2 review state",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 2 Phase 1 明细可见性工作台门槛",
      "v1.1.6 Stage 2 Phase 2 suggested action lane 可见性门槛",
      "v1.1.6 Stage 2 Phase 3 tier asset lane 可见性门槛",
      "v1.1.6 Stage 2 Phase 4 topic classification lane 可见性门槛",
      "v1.1.6 Stage 2 整体复审门槛",
      "stage_2_review_passed_pending_stage3",
      "validate:v1.1.6-stage2",
    ]),
    "model_parameters_stage2_review",
    "Model parameters document phase gates and the Stage 2 review gate",
    "Model parameters are missing Stage 2 review gate",
  );

  assertCondition(
    hasAll(features, [
      "FEAT-MA-V116-S2P01",
      "FEAT-MA-V116-S2P02",
      "FEAT-MA-V116-S2P03",
      "FEAT-MA-V116-S2P04",
      "FEAT-MA-V116-S2-REVIEW",
      "EVID-MA-V116-S2-REVIEW",
    ]),
    "feature_list_stage2_review",
    "Feature list records Phase 2.1 through Phase 2.4 and whole-stage review evidence",
    "Feature list is missing Stage 2 review evidence",
  );

  assertCondition(
    hasAll(dev, [
      "MA-V116-S2P01",
      "MA-V116-S2P02",
      "MA-V116-S2P03",
      "MA-V116-S2P04",
      "MA-V116-S2-REVIEW",
      "Stage 2 Review",
      "ACC-MA-V116-S2-REVIEW",
      "stage_2_review_passed_pending_stage3",
      "Stage 3 未进入",
      "本轮不 commit、不上传 GitHub main",
    ]),
    "development_record_stage2_review",
    "Development record captures all Stage 2 phases, review status, stop boundary and no-upload state",
    "Development record is missing Stage 2 review state",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MOD-MA-V116-S2-REVIEW",
      "PARAM-MA-V116-S2-REVIEW-001",
      "PARAM-MA-V116-S2-REVIEW-006",
      "EVID-MA-V116-S2-REVIEW",
    ]),
    "model_index_stage2_review",
    "Root model parameter file records Stage 2 review model and parameters",
    "Root model parameter file is missing Stage 2 review gate",
  );

  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.6 Stage 2 Review",
      "validate:v1.1.6-stage2",
      "memory_atlas_v1_1_6_stage2_review.md",
      "stage_2_review_passed_pending_stage3",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage2_review",
    "Changelog records Stage 2 review artifact, validator and non-goal boundaries",
    "Changelog is missing Stage 2 review entry",
  );

  assertCondition(
    packageSource.includes('"validate:v1.1.6-stage2": "node scripts/validate_memory_atlas_v1_1_6_stage2.cjs"'),
    "package_script_stage2_review",
    "Package script exposes validate:v1.1.6-stage2",
    "Package script validate:v1.1.6-stage2 is missing",
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
    "docs/product/topic_classification_lane_visibility_contract.md",
    "docs/acceptance/topic_classification_lane_visibility_acceptance.md",
    "docs/reviews/memory_atlas_v1_1_6_stage2_review.md",
    "docs/product/proposal_only_adjustment_workspace_contract.md",
    "docs/acceptance/proposal_only_adjustment_workspace_acceptance.md",
    "docs/product/proposal_queue_persistence_contract.md",
    "docs/acceptance/proposal_queue_persistence_acceptance.md",
    "docs/reviews/memory_atlas_v1_1_6_stage3_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage4_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage5_review.md",
    "docs/product/search_2_0_workflow_contract.md",
    "docs/acceptance/search_2_0_workflow_acceptance.md",
    "docs/product/review_summary_iteration_workflow_contract.md",
    "docs/acceptance/review_summary_iteration_workflow_acceptance.md",
    "docs/product/data_map_2_0_workflow_contract.md",
    "docs/acceptance/data_map_2_0_workflow_acceptance.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase3.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase4.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage1_phase5.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2_phase3.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage2_phase4.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage3.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage3_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage3_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage4_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage4_phase2.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage4.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage5_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage5.cjs",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage2_review_change_scope",
    "Current OpenAIDatabase changes are limited to v1.1.6 governed contract/review work through Stage 5 review, records, validators, and package script",
    "Unexpected OpenAIDatabase paths changed",
    { changed, outside },
  );
}

try {
  [
    "docs/product/detail_visibility_workbench_contract.md",
    "docs/acceptance/detail_visibility_workbench_acceptance.md",
    "docs/product/suggested_action_lane_visibility_contract.md",
    "docs/acceptance/suggested_action_lane_visibility_acceptance.md",
    "docs/product/tier_asset_lane_visibility_contract.md",
    "docs/acceptance/tier_asset_lane_visibility_acceptance.md",
    "docs/product/topic_classification_lane_visibility_contract.md",
    "docs/acceptance/topic_classification_lane_visibility_acceptance.md",
    "docs/reviews/memory_atlas_v1_1_6_stage2_review.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "CHANGELOG.md",
  ].forEach(validateTextFile);
  validatePhase21();
  validatePhase22();
  validatePhase23();
  validatePhase24();
  validateReviewArtifact();
  validateRecords();
  validateChangeScope();
  pass("stage2_review_boundary", "No runtime UI/CSS/raw-private/direct-writeback/search-review-data-map/proposal-editor/agent-apply/stage3/upload work is required or present in this review");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage2", checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.6-stage2",
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
