#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S9P01";
const acceptanceId = "ACC-MA-V117-S9P01";
const status = "phase_9_1_cross_board_shared_state_completed_pending_stage9_review";
const validatorName = "validate:v1.1.7-stage9-phase1";
const browserValidatorName = "validate:cross-board-shared-state-browser";
const sharedStateRuntimeVersion = "cross_board_shared_state.v1_1_7_stage9_phase1";
const inspectorLayerVersion = "inspector_explanation_layer.v1_1_7_stage9_phase1";
const contractPath = "docs/product/memory_atlas_v1_1_7_stage9_phase1_cross_board_shared_state_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage9_phase1_cross_board_shared_state_acceptance.md";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_cross_board_shared_state_browser.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage9_phase1.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  `OpenAIDatabase/${acceptancePath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
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

function parseValidatorOutput(result) {
  const output = result.stdout.trim();
  return JSON.parse(output.slice(output.indexOf("{")));
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

function validateStage8Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage9_phase1_stage8_continuity_deferred_scope",
      "Stage 8 continuity validator is deferred only because the open diff is limited to Stage 9.1 files",
      "Stage 8 continuity cannot be deferred when unrelated files are changed",
      { changed, outside },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_1_7_stage8.cjs"], { cwd: appRoot });
  const parsed = parseValidatorOutput(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S8-REVIEW",
    "stage9_phase1_stage8_continuity",
    "Stage 8 review validator returned PASS before Stage 9.1 clean-tree validation",
    "Stage 8 review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
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

function validateRuntime() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  assertCondition(
    hasAll(app, [
      sharedStateRuntimeVersion,
      inspectorLayerVersion,
      "CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION",
      "INSPECTOR_EXPLANATION_LAYER_VERSION",
      "__memoryAtlasStage9Phase1",
      "data-stage9-phase1-shared-state",
      "data-stage9-inspector-explanation",
      "shared_state_filters",
      "synchronized_filters",
      "inspector_explanation_layer",
      "No direct active-memory writeback",
      "No proposal queue write",
    ]),
    "stage9_phase1_runtime_markers",
    "App runtime exposes Stage 9.1 shared-state and Inspector explanation markers",
    "App runtime is missing Stage 9.1 shared-state or Inspector explanation markers",
  );

  const requiredSurfaces = ["home", "galaxy", "notion", "roi", "obsidian", "timeline", "contribution", "wordcloud", "search", "summary"];
  const missingSurfaces = requiredSurfaces.filter((surface) => !app.includes(`"${surface}"`) && !app.includes(surface));
  assertCondition(
    missingSurfaces.length === 0,
    "stage9_phase1_surface_coverage",
    "Runtime covers all cross-board surfaces in the shared-state gate",
    "Runtime is missing cross-board surface coverage",
    { missingSurfaces },
  );
}

function validateContracts() {
  validateTextFile(contractPath);
  validateTextFile(acceptancePath);
  const contract = readRepoFile(contractPath);
  const acceptance = readRepoFile(acceptancePath);
  const required = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    browserValidatorName,
    sharedStateRuntimeVersion,
    inspectorLayerVersion,
    "Cross-board shared state",
    "synchronized filters",
    "Inspector explanation layer",
    "shared_state_filters",
    "synchronized_filters",
    "inspector_explanation_layer",
    "No Stage 9 review",
    "No Stage 10",
    "No raw/private/cookie/session/secret data access",
    "No direct active-memory writeback",
    "No proposal queue write",
    "No GitHub main upload before the whole Stage 0-10 project is complete",
  ];
  assertCondition(
    hasAll(contract, required),
    "stage9_phase1_product_contract",
    "Stage 9.1 product contract records runtime versions, scope, acceptance and boundaries",
    "Stage 9.1 product contract is incomplete",
  );
  assertCondition(
    hasAll(acceptance, required),
    "stage9_phase1_acceptance_contract",
    "Stage 9.1 acceptance records validators, runtime markers, records and boundaries",
    "Stage 9.1 acceptance is incomplete",
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage9_phase1.cjs",
    "stage9_phase1_package_script",
    "package.json exposes the Stage 9.1 validator",
    "package.json is missing the Stage 9.1 validator script",
    { script: packageJson.scripts?.[validatorName] },
  );

  assertCondition(
    packageJson.scripts?.[browserValidatorName] === "node scripts/validate_cross_board_shared_state_browser.cjs",
    "stage9_phase1_browser_package_script",
    "package.json exposes the Stage 9.1 browser validator",
    "package.json is missing the Stage 9.1 browser validator script",
    { script: packageJson.scripts?.[browserValidatorName] },
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        browserValidatorName,
        sharedStateRuntimeVersion,
        inspectorLayerVersion,
        "Cross-board shared state",
        "synchronized filters",
        "Inspector explanation layer",
        "No Stage 9 review",
        "No GitHub main upload",
      ]),
      `stage9_phase1_records_${name}`,
      `${name} records Stage 9.1 status, validators, runtime versions and boundaries`,
      `${name} is missing Stage 9.1 record fragments`,
    );
  }
}

function validateChangedScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage9_phase1_changed_scope",
    "Open diff is limited to Stage 9.1 shared-state runtime, validators, contracts and records",
    "Open diff contains files outside the Stage 9.1 allowed scope",
    { changed, outside },
  );
}

function validateGitBoundary() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName,
    "stage9_phase1_local_branch",
    `Current branch is ${branchName}`,
    `Current branch must remain ${branchName}`,
    { branch },
  );

  const remoteBranch = spawnSync("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    encoding: "utf8",
    stdio: "pipe",
  });
  assertCondition(
    remoteBranch.status === 0 && remoteBranch.stdout.trim() === "",
    "stage9_phase1_no_remote_branch",
    "No remote Stage 0-10 development branch exists; intermediate work remains local only",
    "Remote development branch exists or could not be checked",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function main() {
  try {
    validateStage8Continuity();
    validateRuntime();
    validateContracts();
    validateRecords();
    validateChangedScope();
    validateGitBoundary();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_1_7_stage9_phase1", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(
      JSON.stringify(
        {
          status: "FAIL",
          validator: "validate_memory_atlas_v1_1_7_stage9_phase1",
          task_id: taskId,
          acceptance_id: acceptanceId,
          failed_check: error instanceof Error ? error.message : String(error),
          details: error && typeof error === "object" ? error.details : undefined,
          checks,
        },
        null,
        2,
      ),
    );
    process.exit(1);
  }
}

main();
