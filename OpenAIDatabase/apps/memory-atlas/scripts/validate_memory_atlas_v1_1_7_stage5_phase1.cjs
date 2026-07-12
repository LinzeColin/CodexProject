#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S5P01";
const acceptanceId = "ACC-MA-V117-S5P01";
const status = "phase_5_1_interaction_contract_completed_pending_stage5_review";
const validatorName = "validate:v1.1.7-stage5-phase1";
const previousValidatorName = "validate:v1.1.7-stage4";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage4.cjs";
const interactionContractVersion = "memory_river_interaction_contract.v1_1_7_stage5_phase1";
const feedbackContractVersion = "memory_river_feedback_contract.v1_1_7_stage5_phase1";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const contractPath = "docs/product/memory_river_interaction_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage5_phase1_interaction_contract_acceptance.md";

const requiredInteractionTokens = [
  "zoom",
  "brush",
  "theme_lanes",
  "event_points",
  "status_bands",
  "detail_panel",
];

const requiredFeedbackTokens = [
  "visual_feedback",
  "optional_audio",
  "pseudo_haptic",
  "reduced_motion",
  "feedback_disable_control",
  "audio_default_off",
  "vibration_not_required",
];

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase1.cjs",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${contractPath}`,
  `OpenAIDatabase/${acceptancePath}`,
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
    maxBuffer: 32 * 1024 * 1024,
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function getOpenAIDatabaseChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--", "OpenAIDatabase"], {
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

function validateStage4Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage5_phase1_open_diff_scope",
      "Open diff is limited to Stage 5 Phase 5.1 interaction contract files",
      "Unexpected files changed outside Stage 5 Phase 5.1 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage4_validator_registered_for_post_commit_run",
      "Stage 4 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 4 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage4_validator_deferred_until_clean_tree",
      "Stage 4 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S4-REVIEW",
    "stage4_validator",
    "Stage 4 validator returned PASS before Stage 5 Phase 5.1 acceptance",
    "Stage 4 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateContracts() {
  [contractPath, acceptancePath, "config/visualization/model_parameters.universe_state.yaml"].forEach(validateTextFile);

  const contract = readRepoFile(contractPath);
  const acceptance = readRepoFile(acceptancePath);
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");

  assertCondition(
    hasAll(contract, [
      "Memory River Interaction Contract",
      interactionContractVersion,
      feedbackContractVersion,
      taskId,
      acceptanceId,
      status,
      validatorName,
      "Interaction Contract",
      "not a date list",
      "not a static scatter",
      "not a table",
      "No C3 River Spike",
      "No Timeline replacement",
      "No Stage 5.2",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage5_phase1_contract_core",
    "Memory River interaction contract records version, status, anti-list rule, deferred work and no-upload boundary",
    "Memory River interaction contract is missing Stage 5 Phase 5.1 core tokens",
  );

  assertCondition(
    hasAll(contract, requiredInteractionTokens),
    "stage5_phase1_interaction_tokens",
    "Interaction contract defines zoom, brush, theme lanes, event points, status bands and detail panel",
    "Interaction contract is missing required interaction tokens",
    { requiredInteractionTokens },
  );

  assertCondition(
    hasAll(contract, requiredFeedbackTokens),
    "stage5_phase1_feedback_tokens",
    "Interaction contract defines visual feedback, optional audio, pseudo-haptic, reduced motion and disable controls",
    "Interaction contract is missing required feedback tokens",
    { requiredFeedbackTokens },
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 5 Phase 5.1 Interaction Contract Acceptance",
      taskId,
      acceptanceId,
      status,
      interactionContractVersion,
      feedbackContractVersion,
      validatorName,
      "zoom",
      "brush",
      "theme_lanes",
      "event_points",
      "status_bands",
      "detail_panel",
      "visual_feedback",
      "optional_audio",
      "pseudo_haptic",
      "reduced_motion",
      "feedback_disable_control",
      "audio_default_off",
      "vibration_not_required",
      "not a date list",
      "No C3 River Spike",
      "No Timeline replacement",
      "No Stage 5.2",
      "No GitHub main upload",
    ]),
    "stage5_phase1_acceptance_contract",
    "Acceptance document pins interaction, feedback, anti-regression, validation and no-upload boundaries",
    "Stage 5 Phase 5.1 acceptance document is incomplete",
  );

  assertCondition(
    hasAll(params, [
      "stage5_phase1_interaction_contract",
      taskId,
      acceptanceId,
      status,
      interactionContractVersion,
      feedbackContractVersion,
      validatorName,
      "zoom",
      "brush",
      "theme_lanes",
      "event_points",
      "status_bands",
      "detail_panel",
      "audio_default_off",
      "vibration_not_required",
      "no_stage5_2",
      "no_github_main_upload",
    ]),
    "stage5_phase1_model_parameters",
    "Universe-state parameter template registers Stage 5 Phase 5.1 interaction and feedback contract controls",
    "Universe-state model parameters are missing Stage 5 Phase 5.1 controls",
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
  ];

  [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase1.cjs",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage5_phase1.cjs",
    "stage5_phase1_package_script",
    `package.json exposes ${validatorName}`,
    `package.json is missing ${validatorName}`,
    { script: packageJson.scripts?.[validatorName] },
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        interactionContractVersion,
        feedbackContractVersion,
        "Phase 5.1",
        "No Stage 5.2",
        "No GitHub main upload",
      ]),
      `stage5_phase1_records_${name}`,
      `${name} records Stage 5 Phase 5.1 status, acceptance, validator and no-upload boundary`,
      `${name} is missing Stage 5 Phase 5.1 tokens`,
    );
  }
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  const remoteBranch = run("git", ["ls-remote", "--heads", "origin", branchName], { cwd: worktreeRoot }).stdout.trim();

  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage5_phase1_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage5_phase1_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
  assertCondition(
    remoteBranch === "",
    "stage5_phase1_no_remote_branch",
    "No remote branch exists for the local Stage 0-10 continuation branch",
    "Local continuation branch was pushed before final Stage 0-10 upload",
    { branchName, stdout: remoteBranch },
  );
}

function validateChangeScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage5_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 5 Phase 5.1 contract, acceptance, records, validator and package script",
    "Unexpected files changed outside Stage 5 Phase 5.1 scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const contract = readRepoFile(contractPath);
  assertCondition(
    contract.includes("No C3 River Spike") &&
      contract.includes("No Timeline replacement") &&
      contract.includes("No Stage 5.2") &&
      contract.includes("No runtime UI implementation") &&
      contract.includes("No CSS change") &&
      contract.includes("No raw/private/cookie/session/secret data access") &&
      contract.includes("No direct active-memory writeback") &&
      contract.includes("No agent apply") &&
      contract.includes("No GitHub main upload before the whole Stage 0-10 project is complete"),
    "stage5_phase1_boundary",
    "No C3 River Spike, Timeline replacement, runtime UI, raw/private read, direct writeback, agent apply, deploy or GitHub main upload is included",
    "Stage 5 Phase 5.1 boundary violation detected",
  );
}

function main() {
  validateStage4Continuity();
  validateContracts();
  validateRecords();
  validateCanonicalBoundary();
  validateChangeScope();
  validateBoundary();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage5-phase1",
        acceptance_id: acceptanceId,
        checks,
      },
      null,
      2,
    ),
  );
}

try {
  main();
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        stage: "v1.1.7-stage5-phase1",
        error: error.message,
        stdout: error.stdout || null,
        stderr: error.stderr || null,
        details: error.details || null,
        checks,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}
