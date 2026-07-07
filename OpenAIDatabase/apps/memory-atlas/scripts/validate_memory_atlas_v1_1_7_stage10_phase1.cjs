#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S10P01";
const acceptanceId = "ACC-MA-V117-S10P01";
const status = "phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review";
const validatorName = "validate:v1.1.7-stage10-phase1";
const contractId = "memory_atlas_v1_1_7_final_hardening_upload_readiness_contract";
const contractPath = "docs/product/memory_atlas_v1_1_7_final_hardening_upload_readiness_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage10_phase1_final_hardening_upload_readiness_acceptance.md";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage10_phase1.cjs",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${acceptancePath}`,
  `OpenAIDatabase/${contractPath}`,
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
];

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

function parseValidatorOutput(result) {
  const output = result.stdout.trim();
  return JSON.parse(output.slice(output.indexOf("{")));
}

function getOpenAIDatabaseChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--untracked-files=all", "--", "OpenAIDatabase"], {
    cwd: worktreeRoot,
  });
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean);
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(
    source.endsWith("\n"),
    `${relativePath}:final_newline`,
    `${relativePath} has a final newline`,
    `${relativePath} is missing a final newline`,
  );

  const blocked = [String.fromCharCode(0xfffd), String.fromCharCode(0x00c2), String.fromCharCode(0x00c3), "\u0000"];
  const badLines = [];
  source.split("\n").forEach((line, index) => {
    if (line.trimEnd() !== line) badLines.push(`${index + 1}:trailing`);
    if (blocked.some((char) => line.includes(char))) badLines.push(`${index + 1}:mojibake`);
  });
  assertCondition(
    badLines.length === 0,
    `${relativePath}:text_clean`,
    `${relativePath} has no blocked mojibake characters, null bytes or trailing whitespace`,
    `${relativePath} contains blocked characters, null bytes or trailing whitespace`,
    { badLines: badLines.slice(0, 20) },
  );
}

function validateStage9Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));

  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage10_phase1_stage9_continuity_deferred_scope",
      "Stage 9 validator execution is deferred only because the open diff is limited to Stage 10 Phase 10.1 readiness files",
      "Stage 9 continuity cannot be deferred when unrelated files are changed",
      { changed, outside },
    );
    assertCondition(
      packageJson.scripts?.["validate:v1.1.7-stage9"] === "node scripts/validate_memory_atlas_v1_1_7_stage9.cjs",
      "stage10_phase1_stage9_validator_registered_for_post_commit_run",
      "Stage 9 review validator is registered for clean-tree execution after this phase is committed",
      "Stage 9 review validator is missing from package.json",
      { registered: packageJson.scripts?.["validate:v1.1.7-stage9"] },
    );
    pass(
      "stage10_phase1_stage9_continuity_deferred_until_clean_tree",
      "Existing Stage 9 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_1_7_stage9.cjs"], { cwd: appRoot });
  const parsed = parseValidatorOutput(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S9-REVIEW",
    "stage10_phase1_stage9_continuity",
    "Stage 9 review validator returned PASS before Stage 10 Phase 10.1 clean-tree validation",
    "Stage 9 review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateContracts() {
  validateTextFile(contractPath);
  validateTextFile(acceptancePath);
  const contract = readRepoFile(contractPath);
  const acceptance = readRepoFile(acceptancePath);

  const required = [
    contractId,
    taskId,
    acceptanceId,
    status,
    validatorName,
    "v1.1.7 Stage 10 Phase 10.1",
    "Stage 9 review must be complete",
    "No intermediate GitHub upload",
    "performance_safety_accessibility_matrix",
    "release_rollback_matrix",
    "final_validation_matrix",
    "github_main_upload_matrix",
    "governance_sync_matrix",
    "new_machine_recovery_matrix",
    "desktop target 45-60 FPS",
    "reduced-motion fallback",
    "No raw/private/cookie/session/secret data access",
    "No direct active-memory writeback",
    "No proposal queue write",
    "No GitHub main upload in this phase",
    "pending Stage 10 review",
  ];

  assertCondition(
    hasAll(contract, required),
    "stage10_phase1_product_contract",
    "Stage 10 Phase 10.1 product contract records final hardening/upload readiness surfaces, evidence shape, non-goals and upload boundary",
    "Stage 10 Phase 10.1 product contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      ...required,
      "changed_scope",
      "runtime_boundary",
      "This acceptance does not prove final visual quality",
      "This acceptance does not upload GitHub main",
    ]),
    "stage10_phase1_acceptance_contract",
    "Stage 10 Phase 10.1 acceptance defines phase proof, deferred proof and safety boundary",
    "Stage 10 Phase 10.1 acceptance file is incomplete",
  );
}

function validateRecords() {
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  const records = [
    ["CHANGELOG.md", readRepoFile("CHANGELOG.md")],
    ["功能清单.md", readRepoFile("功能清单.md")],
    ["开发记录.md", readRepoFile("开发记录.md")],
    ["模型参数文件.md", readRepoFile("模型参数文件.md")],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md")],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")],
    ["config/visualization/model_parameters.universe_state.yaml", readRepoFile("config/visualization/model_parameters.universe_state.yaml")],
  ];

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage10_phase1.cjs",
    "stage10_phase1_package_script",
    "package.json exposes the Stage 10 Phase 10.1 validator",
    "package.json is missing the Stage 10 Phase 10.1 validator script",
    { script: packageJson.scripts?.[validatorName] },
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        contractId,
        "Stage 10 Phase 10.1",
        "performance_safety_accessibility_matrix",
        "release_rollback_matrix",
        "final_validation_matrix",
        "github_main_upload_matrix",
        "governance_sync_matrix",
        "new_machine_recovery_matrix",
        "pending Stage 10 review",
        "No intermediate GitHub upload",
        "No GitHub main upload in this phase",
      ]),
      `stage10_phase1_records_${name}`,
      `${name} records Stage 10 Phase 10.1 status, validator, matrices, boundaries and next gate`,
      `${name} is missing Stage 10 Phase 10.1 record fragments`,
    );
  }
}

function validateChangedScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage10_phase1_changed_scope",
    "Open diff is limited to Stage 10 Phase 10.1 contract, acceptance, validator, package script and governance records",
    "Open diff contains files outside the Stage 10 Phase 10.1 allowed scope",
    { changed, outside },
  );
}

function validateRuntimeBoundary() {
  const changed = getOpenAIDatabaseChangedPaths();
  const touchedRuntime = changed.filter((file) => (
    file.includes("OpenAIDatabase/apps/memory-atlas/src/")
      || file.includes("OpenAIDatabase/apps/memory-atlas/dist/")
      || file.includes("OpenAIDatabase/apps/memory-atlas/build/")
      || file.includes("OpenAIDatabase/apps/memory-atlas/src/fixtures/")
      || file.includes("OpenAIDatabase/data/raw/")
      || file.includes("OpenAIDatabase/data/private/")
      || file.includes(".app")
  ));
  assertCondition(
    touchedRuntime.length === 0,
    "stage10_phase1_runtime_boundary",
    "No production runtime UI/CSS/build/app/data/private/raw/deploy artifact is changed in Stage 10 Phase 10.1",
    "Stage 10 Phase 10.1 touched runtime, build, app, raw/private data or deploy artifacts",
    { touchedRuntime },
  );
}

function validateGitBoundary() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName,
    "stage10_phase1_local_branch",
    `Current branch is ${branchName}`,
    `Current branch must remain ${branchName}`,
    { branch },
  );

  run("git", ["rev-parse", "--verify", "origin/main"], { cwd: worktreeRoot });
  run("git", ["merge-base", "--is-ancestor", "origin/main", "HEAD"], { cwd: worktreeRoot });
  pass(
    "stage10_phase1_origin_main_ancestor",
    "Current HEAD contains origin/main before final upload readiness work",
  );

  const remoteBranch = spawnSync("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    encoding: "utf8",
    stdio: "pipe",
  });
  assertCondition(
    remoteBranch.status === 0 && remoteBranch.stdout.trim() === "",
    "stage10_phase1_no_remote_branch",
    "No remote Stage 0-10 development branch exists; intermediate work remains local only",
    "Remote development branch exists or could not be checked",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function main() {
  try {
    validateStage9Continuity();
    validateContracts();
    validateRecords();
    validateChangedScope();
    validateRuntimeBoundary();
    validateGitBoundary();
    console.log(JSON.stringify({
      status: "PASS",
      validator: "validate_memory_atlas_v1_1_7_stage10_phase1",
      task_id: taskId,
      acceptance_id: acceptanceId,
      checks,
    }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_1_7_stage10_phase1",
      task_id: taskId,
      acceptance_id: acceptanceId,
      error: error.message,
      details: error.details || {
        stdout: error.stdout?.slice(-6000),
        stderr: error.stderr?.slice(-6000),
      },
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
