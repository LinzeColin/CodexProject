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

function validatePhaseContract() {
  const product = readRepoFile("docs/product/memory_river_rebuild_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_river_rebuild_acceptance.md");
  const phaseValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage6_phase1.cjs");

  assertCondition(
    hasAll(product, [
      "Memory Atlas 记忆时间河重做合同",
      "v1.1.6 Stage 6 Phase 1",
      "memory_river_rebuild_contract",
      "time_river",
      "theme_bands",
      "event_pulses",
      "decision_nodes",
      "black_hole_band",
      "proto_star_marker",
      "evidence_density_lane",
      "zoom",
      "brush",
      "hover_card",
      "click_inspector",
      "keyboard_navigation",
      "reduced_motion",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ])
      && hasAll(acceptance, [
        "Memory Atlas 记忆时间河重做验收",
        "validate:v1.1.6-stage6-phase1",
        "date list",
        "static table",
        "raw/private/cookie/session/secret",
        "Desktop 1440x900",
        "Tablet 768x1024",
        "Mobile 390x844",
      ])
      && hasAll(phaseValidator, [
        "v1.1.6-stage6-phase1",
        "stage6_phase1_product_contract",
        "stage6_phase1_acceptance_contract",
        "stage6_phase1_change_scope",
        "stage6_phase1_boundary",
      ]),
    "stage6_phase1_contract_set",
    "Stage 6 Phase 1 product contract, acceptance contract and phase validator are present and aligned",
    "Stage 6 Phase 1 contract set is incomplete",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage6_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 6 Review",
      "stage_6_review_passed_pending_github_main_upload",
      "MA-V116-S6P01",
      "validate:v1.1.6-stage6",
      "validate:v1.1.6-stage6-phase1",
      "Memory River Rebuild Contract",
      "memory_river_rebuild_contract",
      "time_river",
      "theme_bands",
      "event_pulses",
      "decision_nodes",
      "black_hole_band",
      "proto_star_marker",
      "evidence_density_lane",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
      "Stage 7 must start in a separate bounded run",
    ]),
    "stage6_review_artifact",
    "Stage 6 review artifact records phase coverage, validation, boundaries, risks and next gate",
    "Stage 6 review artifact is incomplete",
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
      "Stage 6 整体复审",
      "stage_6_review_passed_pending_github_main_upload",
      "docs/reviews/memory_atlas_v1_1_6_stage6_review.md",
      "validate:v1.1.6-stage6",
      "MA-V116-S6-REVIEW",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage6_review",
    "Delivery record captures Stage 6 review scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 6 review details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 6 整体复审门槛",
      "stage_6_review_passed_pending_github_main_upload",
      "PARAM-MA-V116-S6-REVIEW-001 stage6_required_validator",
      "PARAM-MA-V116-S6-REVIEW-002 stage6_review_status",
      "PARAM-MA-V116-S6-REVIEW-003 stage6_review_artifact",
      "PARAM-MA-V116-S6-REVIEW-004 stage6_allowed_change_scope",
      "PARAM-MA-V116-S6-REVIEW-005 stage6_next_gate",
      "PARAM-MA-V116-S6-REVIEW-006 upload_boundary",
    ]),
    "model_parameters_stage6_review",
    "Model parameters document Stage 6 review validator, status, artifact, scope and final upload gate",
    "Model parameters are missing Stage 6 review details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S6-REVIEW",
      "Memory Atlas v1.1.6 Stage 6 复审",
      "EVID-MA-V116-S6-REVIEW",
      "validate:v1.1.6-stage6",
      "stage_6_review_passed_pending_github_main_upload",
    ]),
    "feature_list_stage6_review",
    "Feature list registers Stage 6 review feature, evidence and validation",
    "Feature list is missing Stage 6 review details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage6_review",
      "MA-V116-S6-REVIEW Stage 6 Review",
      "stage_6_review_passed_pending_github_main_upload",
      "ACC-MA-V116-S6-REVIEW",
      "validate:v1.1.6-stage6",
      "memory_atlas_v1_1_6_stage6_review.md",
    ]),
    "development_record_stage6_review",
    "Development record captures Stage 6 review objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 6 review details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S6-REVIEW",
      "Stage 6 整体复审",
      "stage_6_review_passed_pending_github_main_upload",
      "validate:v1.1.6-stage6",
      "memory_river_review_no_direct_active_memory_write",
    ]),
    "model_index_stage6_review",
    "Root model parameter file records Stage 6 review model and parameters",
    "Root model parameter file is missing Stage 6 review details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 6 Review",
      "memory_atlas_v1_1_6_stage6_review.md",
      "validate:v1.1.6-stage6",
      "stage_6_review_passed_pending_github_main_upload",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage6_review",
    "Changelog records Stage 6 review artifact, validator and non-goal boundaries",
    "Changelog is missing Stage 6 review details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage6"'),
    "package_script_stage6_review",
    "Package script exposes validate:v1.1.6-stage6",
    "Package script is missing validate:v1.1.6-stage6",
  );
}

function validateChangedPaths() {
  const status = run("git", ["status", "--short", "-z", "--", "OpenAIDatabase"], { cwd: worktreeRoot }).stdout;
  const changed = status
    .split("\0")
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .map((line) => line.replace(/^OpenAIDatabase\//, ""));

  const allowed = [
    "CHANGELOG.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage6_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage6.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_river_rebuild_acceptance.md",
    "docs/product/memory_river_rebuild_contract.md",
    "docs/reviews/memory_atlas_v1_1_6_stage6_review.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage6_review_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 6 contract, review, records, validators and package script",
    "Unexpected files changed outside Stage 6 review bounded scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const status = run("git", ["status", "--short", "-z", "--", "OpenAIDatabase/apps/memory-atlas/src"], { cwd: worktreeRoot }).stdout;
  const touchedRuntime = status
    .split("\0")
    .map((line) => line.slice(3).trim())
    .filter(Boolean);

  assertCondition(
    touchedRuntime.length === 0,
    "stage6_review_boundary",
    "No runtime UI/CSS/component/data/writeback work is present in this review",
    "Stage 6 review touched runtime files outside contract scope",
    { touchedRuntime },
  );
}

try {
  [
    "docs/product/memory_river_rebuild_contract.md",
    "docs/acceptance/memory_river_rebuild_acceptance.md",
    "docs/reviews/memory_atlas_v1_1_6_stage6_review.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "CHANGELOG.md",
  ].forEach(validateTextFile);

  validatePhaseContract();
  validateReviewArtifact();
  validateRecords();
  validateChangedPaths();
  validateBoundary();

  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage6", checks }, null, 2));
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        stage: "v1.1.6-stage6",
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
