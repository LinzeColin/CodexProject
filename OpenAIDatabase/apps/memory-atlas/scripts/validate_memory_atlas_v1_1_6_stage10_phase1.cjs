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
  const contract = readRepoFile("docs/product/memory_atlas_final_acceptance_readiness_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas v1.1.6 Final Acceptance Readiness Contract",
      "memory_atlas_final_acceptance_readiness_contract",
      "v1.1.6 Stage 10 Phase 1",
      "MA-V116-S10P01",
      "phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review",
      "Stage 9 upload to the canonical GitHub main tree must already be verified",
      "roadmap_v2_final_acceptance_matrix",
      "validator_chain",
      "visual_evidence_matrix",
      "release_safety_matrix",
      "privacy_writeback_matrix",
      "upload_readiness_matrix",
      "governance_sync_matrix",
      "validate:v1.1.6-stage0",
      "validate:v1.1.6-stage9",
      "validate:universe-state-spike",
      "No production UI",
      "No production build",
      "No GitHub main upload",
    ]),
    "stage10_phase1_product_contract",
    "Final acceptance readiness contract covers entry condition, acceptance surfaces, evidence shape, non-goals and rollback",
    "Final acceptance readiness product contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md");
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.6 Final Acceptance Readiness Acceptance",
      "ACC-MA-V116-S10P01",
      "memory_atlas_final_acceptance_readiness_contract",
      "v1.1.6 Stage 10 Phase 1",
      "MA-V116-S10P01",
      "phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review",
      "validate:v1.1.6-stage10-phase1",
      "prior_upload_boundary",
      "changed_scope",
      "runtime_boundary",
      "This acceptance does not prove final visual quality",
      "No production UI",
      "No production build",
      "No GitHub main upload",
    ]),
    "stage10_phase1_acceptance_contract",
    "Final acceptance readiness acceptance defines phase proof, deferred proof and safety boundary",
    "Final acceptance readiness acceptance file is incomplete",
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
      "Stage 10 Phase 1 Final Acceptance Readiness",
      "phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review",
      "memory_atlas_final_acceptance_readiness_contract.md",
      "memory_atlas_final_acceptance_readiness_acceptance.md",
      "validate:v1.1.6-stage10-phase1",
      "MA-V116-S10P01",
      "No production UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage10_phase1",
    "Delivery record captures Stage 10 Phase 1 scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 10 Phase 1 details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 10 Phase 1 Final Acceptance Readiness 参数",
      "memory_atlas_final_acceptance_readiness_contract",
      "phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review",
      "PARAM-MA-V116-S10P01-001",
      "PARAM-MA-V116-S10P01-002",
      "PARAM-MA-V116-S10P01-003",
      "PARAM-MA-V116-S10P01-004",
      "PARAM-MA-V116-S10P01-005",
      "PARAM-MA-V116-S10P01-006",
      "PARAM-MA-V116-S10P01-007",
    ]),
    "model_parameters_stage10_phase1",
    "Model parameters document Stage 10 Phase 1 contract, surfaces, evidence, boundary and validator",
    "Model parameters are missing Stage 10 Phase 1 details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S10P01",
      "Memory Atlas v1.1.6 Stage 10 Phase 1",
      "EVID-MA-V116-S10P01-CONTRACT",
      "EVID-MA-V116-S10P01-ACCEPTANCE",
      "validate:v1.1.6-stage10-phase1",
      "phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review",
    ]),
    "feature_list_stage10_phase1",
    "Feature list registers Stage 10 Phase 1 feature, evidence and validation",
    "Feature list is missing Stage 10 Phase 1 details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage10_phase1_final_acceptance_readiness",
      "MA-V116-S10P01 Final Acceptance Readiness",
      "phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review",
      "ACC-MA-V116-S10P01",
      "validate:v1.1.6-stage10-phase1",
      "memory_atlas_final_acceptance_readiness_contract.md",
    ]),
    "development_record_stage10_phase1",
    "Development record captures Stage 10 Phase 1 objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 10 Phase 1 details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S10P01",
      "Final Acceptance Readiness",
      "phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review",
      "validate:v1.1.6-stage10-phase1",
      "stage10_final_acceptance_readiness_no_runtime_write",
    ]),
    "model_index_stage10_phase1",
    "Root model parameter file records Stage 10 Phase 1 model and parameters",
    "Root model parameter file is missing Stage 10 Phase 1 details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 10 Phase 1",
      "memory_atlas_final_acceptance_readiness_contract.md",
      "memory_atlas_final_acceptance_readiness_acceptance.md",
      "validate:v1.1.6-stage10-phase1",
      "phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review",
      "No production UI",
      "No production build",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage10_phase1",
    "Changelog records Stage 10 Phase 1 contract, acceptance, validator and non-goal boundaries",
    "Changelog is missing Stage 10 Phase 1 details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage10-phase1"')
      && packageJson.includes("validate_memory_atlas_v1_1_6_stage10_phase1.cjs")
      && packageJson.includes('"validate:v1.1.6-stage9"'),
    "package_script_stage10_phase1",
    "Package script exposes Stage 10 Phase 1 validator and retains Stage 9 gate",
    "Package script is missing Stage 10 Phase 1 validator",
  );
}

function validateUploadedBaseline() {
  run("git", ["rev-parse", "--verify", "origin/main"], { cwd: worktreeRoot });
  run("git", ["merge-base", "--is-ancestor", "origin/main", "HEAD"], { cwd: worktreeRoot });
  pass(
    "stage10_phase1_uploaded_baseline",
    "Current HEAD contains origin/main, so Stage 10 starts from a branch that includes the Stage 9 uploaded baseline",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage10_phase1.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md",
    "docs/product/memory_atlas_final_acceptance_readiness_contract.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage10_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 10 Phase 1 contracts, records, validator and package script",
    "Stage 10 Phase 1 contains out-of-scope OpenAIDatabase changes",
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
    "stage10_phase1_boundary",
    "No production runtime UI/CSS/build/app/data/writeback/deploy or Universe State source/sample/parameter work is present in this phase",
    "Runtime UI, CSS, build, app bundle, data, writeback, deploy artifact or Universe State model/sample/parameter changed during Stage 10 Phase 1",
    { touchedRuntime },
  );
}

function main() {
  try {
    [
      "docs/product/memory_atlas_final_acceptance_readiness_contract.md",
      "docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md",
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
    validateUploadedBaseline();
    validateChangeScope();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage10-phase1", checks }, null, 2));
  } catch (error) {
    checks.push({ name: "failure", status: "FAIL", evidence: error.message, details: error.details || {} });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage10-phase1", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
