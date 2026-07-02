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
  const product = readRepoFile("docs/product/memory_starfield_rebuild_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_starfield_rebuild_acceptance.md");
  const phaseValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage7_phase1.cjs");

  assertCondition(
    hasAll(product, [
      "Memory Atlas 记忆星系重做合同",
      "v1.1.6 Stage 7 Phase 1",
      "memory_starfield_rebuild_contract",
      "memory_starfield",
      "nebula_field",
      "flow_field",
      "trajectory_trails",
      "gravity_sources",
      "black_hole_core",
      "proto_star_cloud",
      "memory_terrain_layer",
      "cluster_constellations",
      "ambient_depth_particles",
      "orbit_pan_zoom",
      "hover_card",
      "click_inspector",
      "focus_cluster",
      "jump_from_search",
      "jump_from_river",
      "presentation_analysis_toggle",
      "keyboard_navigation",
      "reduced_motion",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No experiment directory import",
      "No feature flag default switch",
      "No GitHub main upload",
    ])
      && hasAll(acceptance, [
        "Memory Atlas 记忆星系重做验收",
        "validate:v1.1.6-stage7-phase1",
        "only points",
        "node-link edges",
        "generic Obsidian Graph",
        "Nonblank WebGL canvas",
        "Desktop 1440x900",
        "Tablet 768x1024",
        "Mobile 390x844",
      ])
      && hasAll(phaseValidator, [
        "v1.1.6-stage7-phase1",
        "stage7_phase1_product_contract",
        "stage7_phase1_acceptance_contract",
        "stage7_phase1_change_scope",
        "stage7_phase1_boundary",
      ]),
    "stage7_phase1_contract_set",
    "Stage 7 Phase 1 product contract, acceptance contract and phase validator are present and aligned",
    "Stage 7 Phase 1 contract set is incomplete",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage7_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 7 Review",
      "stage_7_review_passed_pending_github_main_upload",
      "MA-V116-S7P01",
      "validate:v1.1.6-stage7",
      "validate:v1.1.6-stage7-phase1",
      "Memory Starfield Rebuild Contract",
      "memory_starfield_rebuild_contract",
      "memory_starfield",
      "nebula_field",
      "flow_field",
      "trajectory_trails",
      "gravity_sources",
      "black_hole_core",
      "proto_star_cloud",
      "memory_terrain_layer",
      "cluster_constellations",
      "ambient_depth_particles",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No experiment directory import",
      "No feature flag default switch",
      "No GitHub main upload",
      "Stage 8 must start in a separate bounded run",
    ]),
    "stage7_review_artifact",
    "Stage 7 review artifact records phase coverage, validation, boundaries, risks and next gate",
    "Stage 7 review artifact is incomplete",
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
      "Stage 7 整体复审",
      "stage_7_review_passed_pending_github_main_upload",
      "docs/reviews/memory_atlas_v1_1_6_stage7_review.md",
      "validate:v1.1.6-stage7",
      "MA-V116-S7-REVIEW",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage7_review",
    "Delivery record captures Stage 7 review scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 7 review details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 7 整体复审门槛",
      "stage_7_review_passed_pending_github_main_upload",
      "PARAM-MA-V116-S7-REVIEW-001 stage7_required_validator",
      "PARAM-MA-V116-S7-REVIEW-002 stage7_review_status",
      "PARAM-MA-V116-S7-REVIEW-003 stage7_review_artifact",
      "PARAM-MA-V116-S7-REVIEW-004 stage7_allowed_change_scope",
      "PARAM-MA-V116-S7-REVIEW-005 stage7_next_gate",
      "PARAM-MA-V116-S7-REVIEW-006 upload_boundary",
    ]),
    "model_parameters_stage7_review",
    "Model parameters document Stage 7 review validator, status, artifact, scope and final upload gate",
    "Model parameters are missing Stage 7 review details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S7-REVIEW",
      "Memory Atlas v1.1.6 Stage 7 复审",
      "EVID-MA-V116-S7-REVIEW",
      "validate:v1.1.6-stage7",
      "stage_7_review_passed_pending_github_main_upload",
    ]),
    "feature_list_stage7_review",
    "Feature list registers Stage 7 review feature, evidence and validation",
    "Feature list is missing Stage 7 review details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage7_review",
      "MA-V116-S7-REVIEW Stage 7 Review",
      "stage_7_review_passed_pending_github_main_upload",
      "ACC-MA-V116-S7-REVIEW",
      "validate:v1.1.6-stage7",
      "memory_atlas_v1_1_6_stage7_review.md",
    ]),
    "development_record_stage7_review",
    "Development record captures Stage 7 review objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 7 review details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S7-REVIEW",
      "Stage 7 整体复审",
      "stage_7_review_passed_pending_github_main_upload",
      "validate:v1.1.6-stage7",
      "memory_starfield_review_no_direct_active_memory_write",
    ]),
    "model_index_stage7_review",
    "Root model parameter file records Stage 7 review model and parameters",
    "Root model parameter file is missing Stage 7 review details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 7 Review",
      "memory_atlas_v1_1_6_stage7_review.md",
      "validate:v1.1.6-stage7",
      "stage_7_review_passed_pending_github_main_upload",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage7_review",
    "Changelog records Stage 7 review artifact, validator and non-goal boundaries",
    "Changelog is missing Stage 7 review details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage7"'),
    "package_script_stage7_review",
    "Package script exposes validate:v1.1.6-stage7",
    "Package script is missing validate:v1.1.6-stage7",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage7_phase1.cjs",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage7.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_starfield_rebuild_acceptance.md",
    "docs/product/memory_starfield_rebuild_contract.md",
    "docs/reviews/memory_atlas_v1_1_6_stage7_review.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage7_review_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 7 contract, review, records, validators and package script",
    "Stage 7 review contains out-of-scope OpenAIDatabase changes",
    { changed, outside },
  );
}

function validateBoundary() {
  const status = run("git", ["-c", "core.quotePath=false", "status", "--short"], { cwd: worktreeRoot }).stdout;
  const touchedRuntime = status
    .split("\n")
    .filter((line) => line.includes("OpenAIDatabase/apps/memory-atlas/src/") || line.includes("OpenAIDatabase/data/raw/") || line.includes("OpenAIDatabase/data/private/"));

  assertCondition(
    touchedRuntime.length === 0,
    "stage7_review_boundary",
    "No runtime UI/CSS/component/experiment/data/writeback work is present in this review",
    "Runtime UI, CSS, component, experiment, data or writeback code changed during Stage 7 review",
    { touchedRuntime },
  );
}

function main() {
  try {
    [
      "docs/product/memory_starfield_rebuild_contract.md",
      "docs/acceptance/memory_starfield_rebuild_acceptance.md",
      "docs/reviews/memory_atlas_v1_1_6_stage7_review.md",
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
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage7", checks }, null, 2));
  } catch (error) {
    checks.push({ name: "failure", status: "FAIL", evidence: error.message, details: error.details || {} });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage7", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
