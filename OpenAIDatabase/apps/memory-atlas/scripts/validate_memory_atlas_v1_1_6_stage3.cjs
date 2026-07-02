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

function validatePhase31() {
  const contract = readRepoFile("docs/product/proposal_only_adjustment_workspace_contract.md");
  const acceptance = readRepoFile("docs/acceptance/proposal_only_adjustment_workspace_acceptance.md");

  assertCondition(
    hasAll(contract, [
      "Memory Atlas proposal-only 调整工作区合同",
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
      "ready_for_agent_apply",
      "proposal-only",
      "raw/private",
      "本 phase 不修改运行时",
    ]),
    "phase_3_1_workspace_contract",
    "Proposal-only adjustment workspace contract covers regions, fields, targets, statuses, safety, Inspector handoff and future-phase boundary",
    "Proposal-only adjustment workspace contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas proposal-only 调整工作区验收",
      "v1.1.6 Stage 3 Phase 1",
      "proposal_queue",
      "proposal_diff_preview",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "validate:v1.1.6-stage3-phase1",
      "MA-V116-S3P01",
      "No runtime UI",
    ]),
    "phase_3_1_workspace_acceptance",
    "Proposal-only adjustment workspace acceptance covers schema, statuses, screenshots, safety failures and deliverables",
    "Proposal-only adjustment workspace acceptance is incomplete",
  );
}

function validatePhase32() {
  const contract = readRepoFile("docs/product/proposal_queue_persistence_contract.md");
  const acceptance = readRepoFile("docs/acceptance/proposal_queue_persistence_acceptance.md");

  assertCondition(
    hasAll(contract, [
      "Memory Atlas proposal queue 持久化与版本链合同",
      "v1.1.6 Stage 3 Phase 2",
      "proposal_queue_persistence",
      "memory-atlas.writeback.proposals.v1",
      "browser_local_only",
      "append_only",
      "proposal_record",
      "proposal_revision",
      "proposal_history",
      "rollback_proposal",
      "parent_proposal_id",
      "supersedes_proposal_id",
      "rollback_to_proposal_id",
      "stale_snapshot",
      "schema_mismatch",
      "forbidden_payload",
      "raw/private",
      "本 phase 不修改运行时",
    ]),
    "phase_3_2_queue_contract",
    "Proposal queue persistence contract covers storage key, browser-local scope, append-only history, revision chain, rollback and forbidden payload",
    "Proposal queue persistence contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas proposal queue 持久化与版本链验收",
      "v1.1.6 Stage 3 Phase 2",
      "proposal_queue_persistence",
      "memory-atlas.writeback.proposals.v1",
      "proposal_history",
      "rollback_proposal",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "raw/private/cookie/session/secret",
      "validate:v1.1.6-stage3-phase2",
      "MA-V116-S3P02",
      "No runtime UI",
    ]),
    "phase_3_2_queue_acceptance",
    "Proposal queue persistence acceptance covers queue schema, version chain, rollback, states, safety failures and deliverables",
    "Proposal queue persistence acceptance is incomplete",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage3_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 3 Review",
      "stage_3_review_passed_pending_stage4",
      "MA-V116-S3P01",
      "MA-V116-S3P02",
      "validate:v1.1.6-stage3",
      "validate:v1.1.6-stage3-phase1",
      "validate:v1.1.6-stage3-phase2",
      "proposal-only 调整工作区",
      "proposal queue 持久化与版本链",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
      "Stage 4",
    ]),
    "stage3_review_artifact",
    "Stage 3 review artifact records phase coverage, validation, boundaries, risks and next gate",
    "Stage 3 review artifact is incomplete",
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
      "Stage 3 整体复审",
      "stage_3_review_passed_pending_stage4",
      "docs/reviews/memory_atlas_v1_1_6_stage3_review.md",
      "validate:v1.1.6-stage3",
      "MA-V116-S3-REVIEW",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage3_review",
    "Delivery record captures Stage 3 review scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 3 review details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 3 整体复审门槛",
      "stage_3_review_passed_pending_stage4",
      "PARAM-MA-V116-S3-REVIEW-001 stage3_required_validator",
      "PARAM-MA-V116-S3-REVIEW-002 stage3_review_status",
      "PARAM-MA-V116-S3-REVIEW-003 stage3_review_artifact",
      "PARAM-MA-V116-S3-REVIEW-004 stage3_allowed_change_scope",
      "PARAM-MA-V116-S3-REVIEW-005 stage3_next_gate",
      "PARAM-MA-V116-S3-REVIEW-006 upload_boundary",
    ]),
    "model_parameters_stage3_review",
    "Model parameters document Stage 3 review validator, status, artifact, scope and next gate",
    "Model parameters are missing Stage 3 review details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S3-REVIEW",
      "Memory Atlas v1.1.6 Stage 3 复审",
      "EVID-MA-V116-S3-REVIEW",
      "validate:v1.1.6-stage3",
      "stage_3_review_passed_pending_stage4",
    ]),
    "feature_list_stage3_review",
    "Feature list registers Stage 3 review feature, evidence and validation",
    "Feature list is missing Stage 3 review details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage3_review",
      "MA-V116-S3-REVIEW Stage 3 Review",
      "stage_3_review_passed_pending_stage4",
      "ACC-MA-V116-S3-REVIEW",
      "validate:v1.1.6-stage3",
      "memory_atlas_v1_1_6_stage3_review.md",
    ]),
    "development_record_stage3_review",
    "Development record captures Stage 3 review objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 3 review details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S3-REVIEW",
      "Stage 3 整体复审",
      "stage_3_review_passed_pending_stage4",
      "validate:v1.1.6-stage3",
      "proposal_only_no_direct_active_memory_write",
    ]),
    "model_index_stage3_review",
    "Root model parameter file records Stage 3 review model and parameters",
    "Root model parameter file is missing Stage 3 review details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 3 Review",
      "memory_atlas_v1_1_6_stage3_review.md",
      "validate:v1.1.6-stage3",
      "stage_3_review_passed_pending_stage4",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage3_review",
    "Changelog records Stage 3 review artifact, validator and non-goal boundaries",
    "Changelog is missing Stage 3 review details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage3"'),
    "package_script_stage3_review",
    "Package script exposes validate:v1.1.6-stage3",
    "Package script is missing validate:v1.1.6-stage3",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage5_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage5.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/",
    "docs/product/",
    "docs/reviews/memory_atlas_v1_1_6_stage1_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage2_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage3_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage4_review.md",
    "docs/reviews/memory_atlas_v1_1_6_stage5_review.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowedPrefixes.some((prefix) => file === prefix || file.startsWith(prefix)));
  assertCondition(
    outside.length === 0,
    "stage3_review_change_scope",
    "Current OpenAIDatabase changes are limited to v1.1.6 governed contract/review work through Stage 5 review, records, validators, and package script",
    "Unexpected files changed outside Stage 3 review bounded scope",
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
    "stage3_review_boundary",
    "No runtime UI/CSS/data/writeback/Search/Review/Data Map/agent-apply work is present in this review",
    "Runtime or writeback files were modified in a contract-only review",
    { touchedForbidden },
  );
}

try {
  [
    "docs/product/proposal_only_adjustment_workspace_contract.md",
    "docs/acceptance/proposal_only_adjustment_workspace_acceptance.md",
    "docs/product/proposal_queue_persistence_contract.md",
    "docs/acceptance/proposal_queue_persistence_acceptance.md",
    "docs/reviews/memory_atlas_v1_1_6_stage3_review.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "CHANGELOG.md",
  ].forEach(validateTextFile);

  validatePhase31();
  validatePhase32();
  validateReviewArtifact();
  validateRecords();
  validateChangedPaths();
  validateBoundary();

  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage3", checks }, null, 2));
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        stage: "v1.1.6-stage3",
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
