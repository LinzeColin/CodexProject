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

function validatePhaseValidators() {
  const phase1 = run(process.execPath, ["scripts/validate_memory_atlas_v1_1_6_stage4_phase1.cjs"], { cwd: appRoot });
  const phase2 = run(process.execPath, ["scripts/validate_memory_atlas_v1_1_6_stage4_phase2.cjs"], { cwd: appRoot });
  assertCondition(
    phase1.stdout.includes('"status": "PASS"') && phase1.stdout.includes('"stage": "v1.1.6-stage4-phase1"'),
    "stage4_phase1_validator",
    "Stage 4 Phase 1 validator passes before whole-stage review",
    "Stage 4 Phase 1 validator did not report PASS",
  );
  assertCondition(
    phase2.stdout.includes('"status": "PASS"') && phase2.stdout.includes('"stage": "v1.1.6-stage4-phase2"'),
    "stage4_phase2_validator",
    "Stage 4 Phase 2 validator passes before whole-stage review",
    "Stage 4 Phase 2 validator did not report PASS",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage4_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 4 Review",
      "stage_4_review_passed_pending_stage5",
      "MA-V116-S4P01",
      "MA-V116-S4P02",
      "validate:v1.1.6-stage4",
      "validate:v1.1.6-stage4-phase1",
      "validate:v1.1.6-stage4-phase2",
      "Search 2.0 工作流",
      "Review / Summary / Iteration 工作流",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
      "Data Map 2.0",
      "Stage 5",
    ]),
    "stage4_review_artifact",
    "Stage 4 review artifact records phase coverage, validation, boundaries, risks and next gate",
    "Stage 4 review artifact is incomplete",
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
      "Stage 4 整体复审",
      "stage_4_review_passed_pending_stage5",
      "docs/reviews/memory_atlas_v1_1_6_stage4_review.md",
      "validate:v1.1.6-stage4",
      "MA-V116-S4-REVIEW",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage4_review",
    "Delivery record captures Stage 4 review scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 4 review details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 4 整体复审门槛",
      "stage_4_review_passed_pending_stage5",
      "PARAM-MA-V116-S4-REVIEW-001 stage4_required_validator",
      "PARAM-MA-V116-S4-REVIEW-002 stage4_review_status",
      "PARAM-MA-V116-S4-REVIEW-003 stage4_review_artifact",
      "PARAM-MA-V116-S4-REVIEW-004 stage4_allowed_change_scope",
      "PARAM-MA-V116-S4-REVIEW-005 stage4_next_gate",
      "PARAM-MA-V116-S4-REVIEW-006 upload_boundary",
    ]),
    "model_parameters_stage4_review",
    "Model parameters document Stage 4 review validator, status, artifact, scope and next gate",
    "Model parameters are missing Stage 4 review details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S4-REVIEW",
      "Memory Atlas v1.1.6 Stage 4 复审",
      "EVID-MA-V116-S4-REVIEW",
      "validate:v1.1.6-stage4",
      "stage_4_review_passed_pending_stage5",
    ]),
    "feature_list_stage4_review",
    "Feature list registers Stage 4 review feature, evidence and validation",
    "Feature list is missing Stage 4 review details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage4_review",
      "MA-V116-S4-REVIEW Stage 4 Review",
      "stage_4_review_passed_pending_stage5",
      "ACC-MA-V116-S4-REVIEW",
      "validate:v1.1.6-stage4",
      "memory_atlas_v1_1_6_stage4_review.md",
    ]),
    "development_record_stage4_review",
    "Development record captures Stage 4 review objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 4 review details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S4-REVIEW",
      "Stage 4 整体复审",
      "stage_4_review_passed_pending_stage5",
      "validate:v1.1.6-stage4",
      "search_review_workflow_no_direct_active_memory_write",
    ]),
    "model_index_stage4_review",
    "Root model parameter file records Stage 4 review model and parameters",
    "Root model parameter file is missing Stage 4 review details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 4 Review",
      "memory_atlas_v1_1_6_stage4_review.md",
      "validate:v1.1.6-stage4",
      "stage_4_review_passed_pending_stage5",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage4_review",
    "Changelog records Stage 4 review artifact, validator and non-goal boundaries",
    "Changelog is missing Stage 4 review details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage4"'),
    "package_script_stage4_review",
    "Package script exposes validate:v1.1.6-stage4",
    "Package script is missing validate:v1.1.6-stage4",
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
    "stage4_review_change_scope",
    "Current OpenAIDatabase changes are limited to v1.1.6 governed contract/review work through Stage 5 review, records, validators, and package script",
    "Unexpected files changed outside Stage 4 review bounded scope",
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
    "stage4_review_boundary",
    "No runtime UI/CSS/data/writeback work is present in this review",
    "Stage 4 review touched runtime files outside contract scope",
    { touchedForbidden },
  );
}

try {
  [
    "docs/product/search_2_0_workflow_contract.md",
    "docs/acceptance/search_2_0_workflow_acceptance.md",
    "docs/product/review_summary_iteration_workflow_contract.md",
    "docs/acceptance/review_summary_iteration_workflow_acceptance.md",
    "docs/reviews/memory_atlas_v1_1_6_stage4_review.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "CHANGELOG.md",
  ].forEach(validateTextFile);

  validatePhaseValidators();
  validateReviewArtifact();
  validateRecords();
  validateChangedPaths();
  validateBoundary();

  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage4", checks }, null, 2));
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        stage: "v1.1.6-stage4",
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
