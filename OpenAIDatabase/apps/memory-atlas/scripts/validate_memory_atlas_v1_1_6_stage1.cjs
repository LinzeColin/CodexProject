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

function validatePhase01() {
  const contract = readRepoFile("docs/product/memory_overview_usage_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_overview_usage_acceptance.md");

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
      "Presentation",
      "Analysis",
      "Inspector",
      "Proposal",
      "proposal-only",
      "不直接写长期记忆",
      "本 phase 不修改运行时",
    ]),
    "phase_1_1_memory_overview_contract",
    "Memory overview contract covers homepage role, required modules, usage instructions, modes, Inspector and proposal-only boundaries",
    "Memory overview usage contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas 记忆总览与系统使用说明验收",
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
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "validate:v1.1.6-stage1-phase1",
      "MA-V116-S1P01",
    ]),
    "phase_1_1_memory_overview_acceptance",
    "Memory overview acceptance covers modules, usage path, viewport entry, safety failures and deliverables",
    "Memory overview usage acceptance is incomplete",
  );
}

function validatePhase02() {
  const contract = readRepoFile("docs/product/suggested_action_detail_contract.md");
  const acceptance = readRepoFile("docs/acceptance/suggested_action_detail_acceptance.md");

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
      "本 phase 不修改运行时",
    ]),
    "phase_1_2_suggested_action_contract",
    "Suggested action contract covers fields, action types, ROI, effort, urgency, evidence, next step, Inspector and proposal-only boundaries",
    "Suggested action detail contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas 建议动作明细验收",
      "v1.1.6 Stage 1 Phase 2",
      "action_id",
      "action_type",
      "roi_score",
      "effort_cost",
      "urgency",
      "evidence_refs",
      "next_step",
      "proposal_hint",
      "rollback_hint",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "validate:v1.1.6-stage1-phase2",
      "MA-V116-S1P02",
    ]),
    "phase_1_2_suggested_action_acceptance",
    "Suggested action acceptance covers field checks, expansion, screenshots, safety failures and deliverables",
    "Suggested action detail acceptance is incomplete",
  );
}

function validatePhase03() {
  const contract = readRepoFile("docs/product/tier_asset_detail_contract.md");
  const acceptance = readRepoFile("docs/acceptance/tier_asset_detail_acceptance.md");

  assertCondition(
    hasAll(contract, [
      "Memory Atlas 层级资产明细合同",
      "v1.1.6 Stage 1 Phase 3",
      "core_profile",
      "project",
      "decision",
      "workflow",
      "knowledge",
      "opportunity",
      "stale",
      "asset_id",
      "asset_tier",
      "importance",
      "priority",
      "confidence",
      "staleness_status",
      "evidence_count",
      "evidence_refs",
      "linked_action_ids",
      "recommended_asset_action",
      "proposal_hint",
      "rollback_hint",
      "Inspector",
      "proposal-only",
      "本 phase 不修改运行时",
    ]),
    "phase_1_3_tier_asset_contract",
    "Tier asset contract covers seven asset tiers, fields, importance, priority, confidence, staleness, evidence, Inspector and proposal-only boundaries",
    "Tier asset detail contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas 层级资产明细验收",
      "v1.1.6 Stage 1 Phase 3",
      "core_profile",
      "project",
      "decision",
      "workflow",
      "knowledge",
      "opportunity",
      "stale",
      "asset_id",
      "importance",
      "priority",
      "staleness_status",
      "evidence_refs",
      "linked_action_ids",
      "proposal_hint",
      "rollback_hint",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "validate:v1.1.6-stage1-phase3",
      "MA-V116-S1P03",
    ]),
    "phase_1_3_tier_asset_acceptance",
    "Tier asset acceptance covers asset types, fields, expansion, screenshots, safety failures and deliverables",
    "Tier asset detail acceptance is incomplete",
  );
}

function validatePhase04() {
  const contract = readRepoFile("docs/product/topic_classification_detail_contract.md");
  const acceptance = readRepoFile("docs/acceptance/topic_classification_detail_acceptance.md");

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
      "linked_asset_ids",
      "linked_action_ids",
      "linked_starfield_cluster_id",
      "linked_river_range",
      "matched_reason",
      "recommended_topic_action",
      "proposal_hint",
      "rollback_hint",
      "Inspector",
      "proposal-only",
      "本 phase 不修改运行时",
    ]),
    "phase_1_4_topic_contract",
    "Topic contract covers seven topic states, fields, trend, confidence, evidence, cross-board links, Inspector and proposal-only boundaries",
    "Topic classification detail contract is incomplete",
  );

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
      "topic_strength",
      "trend",
      "record_count",
      "evidence_count",
      "linked_asset_ids",
      "linked_action_ids",
      "linked_starfield_cluster_id",
      "linked_river_range",
      "proposal_hint",
      "rollback_hint",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "validate:v1.1.6-stage1-phase4",
      "MA-V116-S1P04",
    ]),
    "phase_1_4_topic_acceptance",
    "Topic acceptance covers states, fields, expansion, screenshots, safety failures and deliverables",
    "Topic classification detail acceptance is incomplete",
  );
}

function validatePhase05() {
  const contract = readRepoFile("docs/product/proposal_only_adjustment_entry_contract.md");
  const acceptance = readRepoFile("docs/acceptance/proposal_only_adjustment_entry_acceptance.md");

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
      "parent_snapshot_id",
      "old_value_ref",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "rollback_hint",
      "active memory",
      "raw/private",
      "完整 proposal 编辑工作区",
      "本 phase 不修改运行时",
    ]),
    "phase_1_5_proposal_entry_contract",
    "Proposal-only entry contract covers entry surfaces, targets, fields, draft schema, safety and future-phase boundaries",
    "Proposal-only adjustment entry contract is incomplete",
  );

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
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "rollback_hint",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "active memory",
      "validate:v1.1.6-stage1-phase5",
      "MA-V116-S1P05",
    ]),
    "phase_1_5_proposal_entry_acceptance",
    "Proposal-only entry acceptance covers entry surfaces, targets, fields, schema, screenshots, safety failures and deliverables",
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
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage1_review.md");
  const packageSource = readRepoFile("apps/memory-atlas/package.json");

  assertCondition(
    hasAll(delivery, [
      "Stage 1 Phase 1：Memory Overview Usage Contract",
      "Stage 1 Phase 2：Suggested Action Detail Contract",
      "Stage 1 Phase 3：Tier Asset Detail Contract",
      "Stage 1 Phase 4：Topic Classification Detail Contract",
      "Stage 1 Phase 5：Proposal-only Adjustment Entry Contract",
      "Stage 1 整体复审",
      "stage_1_review_passed_pending_stage2",
      "validate:v1.1.6-stage1",
      "不上传 GitHub main",
    ]),
    "delivery_record_stage1_review",
    "Delivery record captures all five phases, whole-stage review, validator, upload boundary, and pending-Stage-2 status",
    "Delivery record is missing Stage 1 review state",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 1 Phase 1 记忆总览使用说明门槛",
      "v1.1.6 Stage 1 Phase 2 建议动作明细门槛",
      "v1.1.6 Stage 1 Phase 3 层级资产明细门槛",
      "v1.1.6 Stage 1 Phase 4 主题分类明细门槛",
      "v1.1.6 Stage 1 Phase 5 proposal-only 调整入口门槛",
      "v1.1.6 Stage 1 整体复审门槛",
      "stage_1_review_passed_pending_stage2",
      "validate:v1.1.6-stage1",
    ]),
    "model_parameters_stage1_review",
    "Model parameters document phase gates and the Stage 1 review gate",
    "Model parameters are missing Stage 1 review gate",
  );

  assertCondition(
    hasAll(features, [
      "FEAT-MA-V116-S1P01",
      "FEAT-MA-V116-S1P02",
      "FEAT-MA-V116-S1P03",
      "FEAT-MA-V116-S1P04",
      "FEAT-MA-V116-S1P05",
      "FEAT-MA-V116-S1-REVIEW",
      "EVID-MA-V116-S1-REVIEW",
    ]),
    "feature_list_stage1_review",
    "Feature list records Phase 1.1 through Phase 1.5 and whole-stage review evidence",
    "Feature list is missing Stage 1 review evidence",
  );

  assertCondition(
    hasAll(dev, [
      "MA-V116-S1P01",
      "MA-V116-S1P02",
      "MA-V116-S1P03",
      "MA-V116-S1P04",
      "MA-V116-S1P05",
      "MA-V116-S1-REVIEW",
      "stage_1_review_passed_pending_stage2",
      "Stage 2 未进入",
      "不上传 GitHub main",
    ]),
    "development_record_stage1_review",
    "Development record captures phase completion, stage review, stop point, and next gate",
    "Development record is missing Stage 1 review stop point",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MOD-MA-V116-S1P01",
      "MOD-MA-V116-S1P02",
      "MOD-MA-V116-S1P03",
      "MOD-MA-V116-S1P04",
      "MOD-MA-V116-S1P05",
      "MOD-MA-V116-S1-REVIEW",
      "PARAM-MA-V116-S1-REVIEW-001",
    ]),
    "model_index_stage1_review",
    "Root model parameter file records Phase 1.1 through Phase 1.5 and review gates",
    "Root model parameter file is missing Stage 1 review gate",
  );

  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.6 Stage 1 Review",
      "validate:v1.1.6-stage1",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage1_review",
    "Changelog records whole-stage review and non-goal boundaries",
    "Changelog is missing Stage 1 review entry",
  );

  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 1 Review",
      "Stage 1 is review-passed",
      "Phase 1.1",
      "Phase 1.2",
      "Phase 1.3",
      "Phase 1.4",
      "Phase 1.5",
      "validate:v1.1.6-stage1",
      "No runtime UI implementation",
      "No raw/private/cookie/session/secret data access",
      "No direct frontend writeback",
      "No GitHub main upload",
      "pending Stage 2",
    ]),
    "review_doc_stage1",
    "Review document records result, phase coverage, validation, boundaries, next gate and upload gate",
    "Stage 1 review document is incomplete",
  );

  assertCondition(
    packageSource.includes('"validate:v1.1.6-stage1": "node scripts/validate_memory_atlas_v1_1_6_stage1.cjs"'),
    "package_script_stage1",
    "Package script exposes validate:v1.1.6-stage1",
    "Package script validate:v1.1.6-stage1 is missing",
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
    "stage1_change_scope",
    "Current OpenAIDatabase changes are limited to v1.1.6 governed contract/review work through Stage 5 review, records, validators, and package script",
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
    "docs/reviews/memory_atlas_v1_1_6_stage1_review.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "CHANGELOG.md",
  ].forEach(validateTextFile);
  validatePhase01();
  validatePhase02();
  validatePhase03();
  validatePhase04();
  validatePhase05();
  validateRecords();
  validateChangeScope();
  pass("stage1_boundary", "No runtime UI/CSS/raw-private/direct-writeback/complete-proposal-editor/agent-apply/search-review-data-map/upload work is required or present in this review");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage1", checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.6-stage1",
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
