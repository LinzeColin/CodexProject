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
    env: options.env || process.env,
    encoding: "utf8",
    stdio: "pipe",
    maxBuffer: 96 * 1024 * 1024,
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function parseJsonOutput(stdout) {
  const trimmed = stdout.trim();
  const firstBrace = trimmed.indexOf("{");
  const lastBrace = trimmed.lastIndexOf("}");
  if (firstBrace < 0 || lastBrace < firstBrace) return null;
  return JSON.parse(trimmed.slice(firstBrace, lastBrace + 1));
}

function outputTail(result) {
  return {
    stdout: result.stdout.slice(-6000),
    stderr: result.stderr.slice(-6000),
  };
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

function validatePhase1Contract() {
  const product = readRepoFile("docs/product/memory_atlas_final_acceptance_readiness_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md");
  const phaseValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage10_phase1.cjs");

  assertCondition(
    hasAll(product, [
      "Memory Atlas v1.1.6 Final Acceptance Readiness Contract",
      "memory_atlas_final_acceptance_readiness_contract",
      "v1.1.6 Stage 10 Phase 1",
      "MA-V116-S10P01",
      "roadmap_v2_final_acceptance_matrix",
      "validator_chain",
      "visual_evidence_matrix",
      "release_safety_matrix",
      "privacy_writeback_matrix",
      "upload_readiness_matrix",
      "governance_sync_matrix",
      "Stage 9 upload to the canonical GitHub main tree must already be verified",
      "No production UI",
      "No GitHub main upload",
    ])
      && hasAll(acceptance, [
        "Memory Atlas v1.1.6 Final Acceptance Readiness Acceptance",
        "ACC-MA-V116-S10P01",
        "validate:v1.1.6-stage10-phase1",
        "prior_upload_boundary",
        "changed_scope",
        "runtime_boundary",
        "This acceptance does not prove Stage 10 review completion",
        "No GitHub main upload",
      ])
      && hasAll(phaseValidator, [
        "v1.1.6-stage10-phase1",
        "stage10_phase1_product_contract",
        "stage10_phase1_acceptance_contract",
        "stage10_phase1_uploaded_baseline",
        "stage10_phase1_change_scope",
        "stage10_phase1_boundary",
      ]),
    "stage10_phase1_contract_set",
    "Stage 10 Phase 1 product contract, acceptance contract and phase validator are present and aligned",
    "Stage 10 Phase 1 contract set is incomplete",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage10_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 10 Review",
      "stage_10_review_passed_pending_github_main_upload",
      "MA-V116-S10P01",
      "validate:v1.1.6-stage10",
      "validate:v1.1.6-stage10-phase1",
      "validate:whole-project",
      "roadmap_v2_final_acceptance_matrix",
      "validator_chain",
      "visual_evidence_matrix",
      "release_safety_matrix",
      "privacy_writeback_matrix",
      "upload_readiness_matrix",
      "governance_sync_matrix",
      "No production runtime feature work",
      "No Cloudflare live deploy",
      "No Access policy change",
      "No GitHub main upload",
      "MEMORY_ATLAS_REQUIRE_LOCAL_APPS",
    ]),
    "stage10_review_artifact",
    "Stage 10 review artifact records phase coverage, whole-project validation, boundaries, risks and next gate",
    "Stage 10 review artifact is incomplete",
  );
}

function validateWholeProjectGate() {
  const result = run(process.execPath, [path.join(appRoot, "scripts", "validate_memory_atlas_whole_project.cjs")], { cwd: appRoot });
  const parsed = parseJsonOutput(result.stdout);
  assertCondition(
    parsed?.status === "PASS",
    "stage10_whole_project_gate_passed",
    "validate_memory_atlas_whole_project.cjs returned PASS",
    "validate:whole-project did not return PASS JSON",
    outputTail(result),
  );

  const names = new Set((parsed.checks || []).map((check) => check.name));
  const requiredChecks = [
    "whole_project_frontend_build_passed",
    "whole_project_unittest_discover_passed",
    "whole_project_visual_acceptance_passed",
    "whole_project_release_audit_passed",
    "whole_project_acceptance_passed",
    "whole_project_cloudflare_offline_preflight_passed",
    "whole_project_roadmap_final_acceptance_runtime_covered",
    "whole_project_roadmap_final_acceptance_audited",
    "whole_project_canonical_remote",
    "whole_project_git_upload_boundary_recorded",
    "whole_project_preview_cleanup",
  ];
  const missing = requiredChecks.filter((name) => !names.has(name));
  assertCondition(
    missing.length === 0,
    "stage10_whole_project_gate_coverage",
    "Whole-project gate covers build, tests, visual, release, acceptance, offline Cloudflare, roadmap final acceptance, remote and cleanup checks",
    "validate:whole-project result is missing required Stage 10 coverage",
    { missing },
  );

  pass("stage10_whole_project_gate_summary", "Whole-project gate completed as Stage 10 review evidence", {
    checkCount: parsed.checks?.length ?? null,
    requireLocalApps: parsed.requireLocalApps ?? null,
    scope: parsed.scope ?? null,
  });
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
      "Stage 10 整体复审",
      "stage_10_review_passed_pending_github_main_upload",
      "docs/reviews/memory_atlas_v1_1_6_stage10_review.md",
      "validate:v1.1.6-stage10",
      "validate:whole-project",
      "MA-V116-S10-REVIEW",
      "No production runtime feature work",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage10_review",
    "Delivery record captures Stage 10 review scope, validator, whole-project gate, status and no-upload boundary",
    "Delivery record is missing Stage 10 review details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 10 整体复审门槛",
      "stage_10_review_passed_pending_github_main_upload",
      "PARAM-MA-V116-S10-REVIEW-001 stage10_required_validator",
      "PARAM-MA-V116-S10-REVIEW-002 stage10_review_status",
      "PARAM-MA-V116-S10-REVIEW-003 stage10_review_artifact",
      "PARAM-MA-V116-S10-REVIEW-004 stage10_required_whole_project_gate",
      "PARAM-MA-V116-S10-REVIEW-005 stage10_allowed_change_scope",
      "PARAM-MA-V116-S10-REVIEW-006 stage10_next_gate",
      "PARAM-MA-V116-S10-REVIEW-007 upload_boundary",
    ]),
    "model_parameters_stage10_review",
    "Model parameters document Stage 10 review validator, status, artifact, whole-project gate, scope and final upload gate",
    "Model parameters are missing Stage 10 review details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S10-REVIEW",
      "Memory Atlas v1.1.6 Stage 10 复审",
      "EVID-MA-V116-S10-REVIEW",
      "validate:v1.1.6-stage10",
      "stage_10_review_passed_pending_github_main_upload",
    ]),
    "feature_list_stage10_review",
    "Feature list registers Stage 10 review feature, evidence and validation",
    "Feature list is missing Stage 10 review details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage10_review",
      "MA-V116-S10-REVIEW Stage 10 Review",
      "stage_10_review_passed_pending_github_main_upload",
      "ACC-MA-V116-S10-REVIEW",
      "validate:v1.1.6-stage10",
      "memory_atlas_v1_1_6_stage10_review.md",
    ]),
    "development_record_stage10_review",
    "Development record captures Stage 10 review objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 10 review details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S10-REVIEW",
      "Stage 10 整体复审",
      "stage_10_review_passed_pending_github_main_upload",
      "validate:v1.1.6-stage10",
      "stage10_final_review_whole_project_gate_no_upload",
    ]),
    "model_index_stage10_review",
    "Root model parameter file records Stage 10 review model and parameters",
    "Root model parameter file is missing Stage 10 review details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 10 Review",
      "memory_atlas_v1_1_6_stage10_review.md",
      "validate:v1.1.6-stage10",
      "validate:whole-project",
      "stage_10_review_passed_pending_github_main_upload",
      "No production runtime feature work",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage10_review",
    "Changelog records Stage 10 review artifact, validator, whole-project gate and non-goal boundaries",
    "Changelog is missing Stage 10 review details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage10"')
      && packageJson.includes('"validate:v1.1.6-stage10-phase1"')
      && packageJson.includes('"validate:whole-project"'),
    "package_script_stage10_review",
    "Package script exposes Stage 10 review, Phase 1 and whole-project validators",
    "Package script is missing Stage 10 review validator",
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotePath=false", "status", "--short", "--untracked-files=all", "--", "OpenAIDatabase"], { cwd: worktreeRoot });
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage10.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/reviews/memory_atlas_v1_1_6_stage10_review.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage10_review_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 10 review, records, validator and package script",
    "Stage 10 review contains out-of-scope OpenAIDatabase changes",
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
        || line.includes("OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/fixtures/universe_state")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/models/universeState.ts")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/utils/universeStateScores.ts")
        || line.includes("OpenAIDatabase/data/raw/")
        || line.includes("OpenAIDatabase/data/private/")
        || line.includes(".app")
    ));

  assertCondition(
    touchedRuntime.length === 0,
    "stage10_review_boundary",
    "No production source/build/app/data/writeback/deploy or Universe State source/sample/parameter work is present in this review",
    "Production source, build, app bundle, data, writeback, deploy artifact or Universe State source/sample/parameter changed during Stage 10 review",
    { touchedRuntime },
  );
}

function main() {
  try {
    [
      "docs/product/memory_atlas_final_acceptance_readiness_contract.md",
      "docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md",
      "docs/reviews/memory_atlas_v1_1_6_stage10_review.md",
      "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
      "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
      "功能清单.md",
      "开发记录.md",
      "模型参数文件.md",
      "CHANGELOG.md",
    ].forEach(validateTextFile);
    validatePhase1Contract();
    validateReviewArtifact();
    validateWholeProjectGate();
    validateRecords();
    validateChangeScope();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage10", checks }, null, 2));
  } catch (error) {
    checks.push({
      name: "failure",
      status: "FAIL",
      evidence: error.message,
      details: error.details || {
        stdout: error.stdout?.slice(-6000),
        stderr: error.stderr?.slice(-6000),
      },
    });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage10", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
