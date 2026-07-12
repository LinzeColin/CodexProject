#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S8-REVIEW";
const acceptanceId = "ACC-MA-V117-S8-REVIEW";
const status = "stage_8_review_passed_pending_stage9_no_github_main_upload";
const validatorName = "validate:v1.1.7-stage8";
const reviewPath = "docs/reviews/memory_atlas_v1_1_7_stage8_review.md";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const phaseValidators = [
  [
    "stage8_phase1_validator",
    "validate_memory_atlas_v1_1_7_stage8_phase1.cjs",
    "validate:v1.1.7-stage8-phase1",
    "ACC-MA-V117-S8P01",
  ],
];

const allowedReviewChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage8.cjs",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${reviewPath}`,
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

function validatePhaseValidators() {
  const changed = getOpenAIDatabaseChangedPaths();
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));

  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage8_review_phase_validator_deferred_scope",
      "Phase validator execution is deferred only because the open diff is limited to Stage 8 review gate files",
      "Phase validator execution cannot be deferred when unrelated files are changed",
      { changed, outside },
    );

    phaseValidators.forEach(([name, script, scriptName]) => {
      const scriptPath = path.join(appRoot, "scripts", script);
      assertCondition(
        fs.existsSync(scriptPath) && packageJson.scripts?.[scriptName] === `node scripts/${script}`,
        `${name}_registered_for_post_commit_run`,
        `${script} exists and is registered for clean-tree execution after this review gate is committed`,
        `${script} is missing or not registered`,
        { script, scriptName, registered: packageJson.scripts?.[scriptName] },
      );
    });
    pass(
      "stage8_phase_validators_deferred_until_clean_tree",
      "Existing phase validators enforce their own changed-path scopes; run this Stage 8 validator again after commit to execute them on a clean tree",
      { changed },
    );
    return;
  }

  phaseValidators.forEach(([name, script, , expectedAcceptanceId]) => {
    const result = run("node", [`scripts/${script}`], { cwd: appRoot });
    const parsed = parseValidatorOutput(result);
    assertCondition(
      parsed.status === "PASS" && parsed.acceptance_id === expectedAcceptanceId,
      name,
      `${script} returned PASS for ${expectedAcceptanceId}`,
      `${script} did not return PASS for ${expectedAcceptanceId}`,
      { status: parsed.status, acceptance_id: parsed.acceptance_id },
    );
  });
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const review = readRepoFile(reviewPath);

  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.7 Stage 8 Review",
      taskId,
      acceptanceId,
      status,
      "Stage 8 is review-passed",
      "pending Stage 9",
      "Phase 8.1",
      "Summary and iteration closure",
      "summary_iteration_closure_runtime.v1_1_7_stage8_phase1",
      "memory_atlas_summary_closure.v1_1_7_stage8_phase1",
      "memory_atlas_review_summary.v1_1_7_stage7_phase2",
      "validate:v1.1.7-stage8-phase1",
      "validate:summary-iteration-closure-browser",
      validatorName,
      "change_comparison",
      "stale_conflict_signals",
      "proposal_candidates",
      "proposal-only",
      "No Stage 9 work",
      "No raw/private/cookie/session/secret data access",
      "No direct active-memory writeback",
      "No proposal queue write",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage8_review_artifact",
    "Stage 8 review artifact records phase coverage, browser evidence, validation, boundaries and next gate",
    "Stage 8 review artifact is incomplete",
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage8.cjs",
    "stage8_review_package_script",
    "package.json exposes the Stage 8 review validator",
    "package.json is missing the Stage 8 review validator script",
    { script: packageJson.scripts?.[validatorName] },
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "Phase 8.1",
        "Summary and iteration closure",
        "summary_iteration_closure_runtime.v1_1_7_stage8_phase1",
        "memory_atlas_summary_closure.v1_1_7_stage8_phase1",
        "change_comparison",
        "stale_conflict_signals",
        "proposal_candidates",
        "pending Stage 9",
        "No Stage 9 work",
        "No GitHub main upload",
      ]),
      `stage8_review_records_${name}`,
      `${name} records Stage 8 review status, validator, boundaries and next gate`,
      `${name} is missing Stage 8 review record fragments`,
    );
  }
}

function validateGitBoundary() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName,
    "stage8_review_local_branch",
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
    "stage8_review_no_remote_branch",
    "No remote Stage 0-10 development branch exists; intermediate work remains local only",
    "Remote development branch exists or could not be checked",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function main() {
  validatePhaseValidators();
  validateReviewArtifact();
  validateRecords();
  validateGitBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_1_7_stage8",
    task_id: taskId,
    acceptance_id: acceptanceId,
    checks,
  }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_memory_atlas_v1_1_7_stage8",
    task_id: taskId,
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
