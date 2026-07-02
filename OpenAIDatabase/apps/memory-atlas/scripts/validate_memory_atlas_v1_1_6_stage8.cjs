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
  const product = readRepoFile("docs/product/memory_atlas_release_rollback_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_release_rollback_acceptance.md");
  const phaseValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage8_phase1.cjs");

  assertCondition(
    hasAll(product, [
      "Memory Atlas 发布、本地 App 与回滚安全合同",
      "v1.1.6 Stage 8 Phase 1",
      "memory_atlas_release_rollback_contract",
      "local_app_bundle",
      "runtime_manifest",
      "redacted_static_artifact",
      "cloudflare_preflight",
      "live_deploy_authorization_gate",
      "rollback_matrix",
      "proposal_only_writeback_gate",
      "cleanup_guard",
      "memory_starfield",
      "memory_river",
      "data_map_2_0",
      "search_review_workflows",
      "proposal_queue",
      "local_app_runtime",
      "cloudflare_release",
      "stale local app",
      "No production build in this phase",
      "No Cloudflare live deploy",
      "No Access policy change",
      "No GitHub main upload",
    ])
      && hasAll(acceptance, [
        "Memory Atlas 发布、本地 App 与回滚安全验收",
        "validate:v1.1.6-stage8-phase1",
        "Local app runtime manifest with current `HEAD`",
        "Offline Cloudflare Pages + Access preflight result",
        "No production build",
        "No Cloudflare live deploy",
        "No Access policy change",
        "No GitHub main upload",
      ])
      && hasAll(phaseValidator, [
        "v1.1.6-stage8-phase1",
        "stage8_phase1_product_contract",
        "stage8_phase1_acceptance_contract",
        "stage8_phase1_change_scope",
        "stage8_phase1_boundary",
      ]),
    "stage8_phase1_contract_set",
    "Stage 8 Phase 1 product contract, acceptance contract and phase validator are present and aligned",
    "Stage 8 Phase 1 contract set is incomplete",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage8_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 8 Review",
      "stage_8_review_passed_pending_github_main_upload",
      "MA-V116-S8P01",
      "validate:v1.1.6-stage8",
      "validate:v1.1.6-stage8-phase1",
      "Release Rollback Contract",
      "memory_atlas_release_rollback_contract",
      "local_app_bundle",
      "runtime_manifest",
      "redacted_static_artifact",
      "cloudflare_preflight",
      "live_deploy_authorization_gate",
      "rollback_matrix",
      "proposal_only_writeback_gate",
      "cleanup_guard",
      "stale local app",
      "unauthorized_cloudflare_deploy",
      "premature_github_upload",
      "No production build in this review",
      "No installer run in this review",
      "No Cloudflare live deploy",
      "No Access policy change",
      "No GitHub main upload",
      "Stage 9 must start in a separate bounded run",
    ]),
    "stage8_review_artifact",
    "Stage 8 review artifact records phase coverage, validation, boundaries, risks and next gate",
    "Stage 8 review artifact is incomplete",
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
      "Stage 8 整体复审",
      "stage_8_review_passed_pending_github_main_upload",
      "docs/reviews/memory_atlas_v1_1_6_stage8_review.md",
      "validate:v1.1.6-stage8",
      "MA-V116-S8-REVIEW",
      "No production build",
      "No Cloudflare live deploy",
      "No Access policy change",
      "No GitHub main upload",
    ]),
    "delivery_record_stage8_review",
    "Delivery record captures Stage 8 review scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 8 review details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 8 整体复审门槛",
      "stage_8_review_passed_pending_github_main_upload",
      "PARAM-MA-V116-S8-REVIEW-001 stage8_required_validator",
      "PARAM-MA-V116-S8-REVIEW-002 stage8_review_status",
      "PARAM-MA-V116-S8-REVIEW-003 stage8_review_artifact",
      "PARAM-MA-V116-S8-REVIEW-004 stage8_allowed_change_scope",
      "PARAM-MA-V116-S8-REVIEW-005 stage8_next_gate",
      "PARAM-MA-V116-S8-REVIEW-006 upload_boundary",
    ]),
    "model_parameters_stage8_review",
    "Model parameters document Stage 8 review validator, status, artifact, scope and final upload gate",
    "Model parameters are missing Stage 8 review details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S8-REVIEW",
      "Memory Atlas v1.1.6 Stage 8 复审",
      "EVID-MA-V116-S8-REVIEW",
      "validate:v1.1.6-stage8",
      "stage_8_review_passed_pending_github_main_upload",
    ]),
    "feature_list_stage8_review",
    "Feature list registers Stage 8 review feature, evidence and validation",
    "Feature list is missing Stage 8 review details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage8_review",
      "MA-V116-S8-REVIEW Stage 8 Review",
      "stage_8_review_passed_pending_github_main_upload",
      "ACC-MA-V116-S8-REVIEW",
      "validate:v1.1.6-stage8",
      "memory_atlas_v1_1_6_stage8_review.md",
    ]),
    "development_record_stage8_review",
    "Development record captures Stage 8 review objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 8 review details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S8-REVIEW",
      "Stage 8 整体复审",
      "stage_8_review_passed_pending_github_main_upload",
      "validate:v1.1.6-stage8",
      "release_rollback_review_no_build_no_deploy",
    ]),
    "model_index_stage8_review",
    "Root model parameter file records Stage 8 review model and parameters",
    "Root model parameter file is missing Stage 8 review details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 8 Review",
      "memory_atlas_v1_1_6_stage8_review.md",
      "validate:v1.1.6-stage8",
      "stage_8_review_passed_pending_github_main_upload",
      "No runtime UI implementation",
      "No production build",
      "No Cloudflare live deploy",
      "No GitHub main upload",
    ]),
    "changelog_stage8_review",
    "Changelog records Stage 8 review artifact, validator and non-goal boundaries",
    "Changelog is missing Stage 8 review details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage8"'),
    "package_script_stage8_review",
    "Package script exposes validate:v1.1.6-stage8",
    "Package script is missing validate:v1.1.6-stage8",
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
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage8_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage8.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_atlas_release_rollback_acceptance.md",
    "docs/product/memory_atlas_release_rollback_contract.md",
    "docs/reviews/memory_atlas_v1_1_6_stage8_review.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage8_review_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 8 contract, review, records, validators and package script",
    "Stage 8 review contains out-of-scope OpenAIDatabase changes",
    { changed, outside },
  );
}

function validateBoundary() {
  const status = run("git", ["-c", "core.quotePath=false", "status", "--short"], { cwd: worktreeRoot }).stdout;
  const touchedRuntime = status
    .split("\n")
    .filter((line) => (
      line.includes("OpenAIDatabase/apps/memory-atlas/src/")
        || line.includes("OpenAIDatabase/apps/memory-atlas/dist/")
        || line.includes("OpenAIDatabase/apps/memory-atlas/build/")
        || line.includes("OpenAIDatabase/data/raw/")
        || line.includes("OpenAIDatabase/data/private/")
        || line.includes(".app")
    ));

  assertCondition(
    touchedRuntime.length === 0,
    "stage8_review_boundary",
    "No runtime UI/CSS/build/app/data/writeback/deploy work is present in this review",
    "Runtime UI, CSS, build, app bundle, data, writeback or deploy artifact changed during Stage 8 review",
    { touchedRuntime },
  );
}

function main() {
  try {
    [
      "docs/product/memory_atlas_release_rollback_contract.md",
      "docs/acceptance/memory_atlas_release_rollback_acceptance.md",
      "docs/reviews/memory_atlas_v1_1_6_stage8_review.md",
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
    validateChangeScope();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage8", checks }, null, 2));
  } catch (error) {
    checks.push({ name: "failure", status: "FAIL", evidence: error.message, details: error.details || {} });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage8", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
