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

function validatePhaseValidator() {
  const phase1 = run(process.execPath, ["scripts/validate_memory_atlas_v1_1_6_stage5_phase1.cjs"], { cwd: appRoot });
  assertCondition(
    phase1.stdout.includes('"status": "PASS"') && phase1.stdout.includes('"stage": "v1.1.6-stage5-phase1"'),
    "stage5_phase1_validator",
    "Stage 5 Phase 1 validator passes before whole-stage review",
    "Stage 5 Phase 1 validator did not report PASS",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage5_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 5 Review",
      "stage_5_review_passed_pending_stage1_5_final_upload",
      "MA-V116-S5P01",
      "validate:v1.1.6-stage5",
      "validate:v1.1.6-stage5-phase1",
      "Data Map 2.0 Workflow Contract",
      "data_map_2_0_workflow",
      "source_layer",
      "topic_layer",
      "asset_layer",
      "action_layer",
      "data_to_action_flow",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
      "Stage 1-5 final upload",
    ]),
    "stage5_review_artifact",
    "Stage 5 review artifact records phase coverage, validation, boundaries, risks and final upload gate",
    "Stage 5 review artifact is incomplete",
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
      "Stage 5 整体复审",
      "stage_5_review_passed_pending_stage1_5_final_upload",
      "docs/reviews/memory_atlas_v1_1_6_stage5_review.md",
      "validate:v1.1.6-stage5",
      "MA-V116-S5-REVIEW",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage5_review",
    "Delivery record captures Stage 5 review scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 5 review details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 5 整体复审门槛",
      "stage_5_review_passed_pending_stage1_5_final_upload",
      "PARAM-MA-V116-S5-REVIEW-001 stage5_required_validator",
      "PARAM-MA-V116-S5-REVIEW-002 stage5_review_status",
      "PARAM-MA-V116-S5-REVIEW-003 stage5_review_artifact",
      "PARAM-MA-V116-S5-REVIEW-004 stage5_allowed_change_scope",
      "PARAM-MA-V116-S5-REVIEW-005 stage5_next_gate",
      "PARAM-MA-V116-S5-REVIEW-006 upload_boundary",
    ]),
    "model_parameters_stage5_review",
    "Model parameters document Stage 5 review validator, status, artifact, scope and final upload gate",
    "Model parameters are missing Stage 5 review details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S5-REVIEW",
      "Memory Atlas v1.1.6 Stage 5 复审",
      "EVID-MA-V116-S5-REVIEW",
      "validate:v1.1.6-stage5",
      "stage_5_review_passed_pending_stage1_5_final_upload",
    ]),
    "feature_list_stage5_review",
    "Feature list registers Stage 5 review feature, evidence and validation",
    "Feature list is missing Stage 5 review details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage5_review",
      "MA-V116-S5-REVIEW Stage 5 Review",
      "stage_5_review_passed_pending_stage1_5_final_upload",
      "ACC-MA-V116-S5-REVIEW",
      "validate:v1.1.6-stage5",
      "memory_atlas_v1_1_6_stage5_review.md",
    ]),
    "development_record_stage5_review",
    "Development record captures Stage 5 review objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 5 review details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S5-REVIEW",
      "Stage 5 整体复审",
      "stage_5_review_passed_pending_stage1_5_final_upload",
      "validate:v1.1.6-stage5",
      "data_map_review_no_direct_active_memory_write",
    ]),
    "model_index_stage5_review",
    "Root model parameter file records Stage 5 review model and parameters",
    "Root model parameter file is missing Stage 5 review details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 5 Review",
      "memory_atlas_v1_1_6_stage5_review.md",
      "validate:v1.1.6-stage5",
      "stage_5_review_passed_pending_stage1_5_final_upload",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage5_review",
    "Changelog records Stage 5 review artifact, validator and non-goal boundaries",
    "Changelog is missing Stage 5 review details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage5"'),
    "package_script_stage5_review",
    "Package script exposes validate:v1.1.6-stage5",
    "Package script is missing validate:v1.1.6-stage5",
  );
}

function validateChangedPaths() {
  const status = run("git", ["status", "--short", "-z", "--", "OpenAIDatabase"], { cwd: worktreeRoot }).stdout;
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage4",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage5",
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
    "stage5_review_change_scope",
    "Current OpenAIDatabase changes are limited to v1.1.6 governed contract/review work through Stage 5 review, records, validators, and package script",
    "Unexpected files changed outside Stage 5 review bounded scope",
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
  const status = run("git", ["status", "--short", "-z", "--", "OpenAIDatabase/apps/memory-atlas/src"], { cwd: worktreeRoot }).stdout;
  const touchedForbidden = status
    .split("\0")
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .map((line) => line.replace(/^OpenAIDatabase\/apps\/memory-atlas\//, ""))
    .filter((file) => forbiddenFiles.some((forbidden) => file === forbidden || file.startsWith(forbidden)));

  assertCondition(
    touchedForbidden.length === 0,
    "stage5_review_boundary",
    "No runtime UI/CSS/data/writeback work is present in this review",
    "Stage 5 review touched runtime files outside contract scope",
    { touchedForbidden },
  );
}

try {
  [
    "docs/product/data_map_2_0_workflow_contract.md",
    "docs/acceptance/data_map_2_0_workflow_acceptance.md",
    "docs/reviews/memory_atlas_v1_1_6_stage5_review.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "CHANGELOG.md",
  ].forEach(validateTextFile);

  validatePhaseValidator();
  validateReviewArtifact();
  validateRecords();
  validateChangedPaths();
  validateBoundary();

  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage5", checks }, null, 2));
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        stage: "v1.1.6-stage5",
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
