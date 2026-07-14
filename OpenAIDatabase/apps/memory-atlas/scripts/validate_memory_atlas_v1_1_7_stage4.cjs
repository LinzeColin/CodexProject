#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S4-REVIEW";
const acceptanceId = "ACC-MA-V117-S4-REVIEW";
const status = "stage_4_review_passed_pending_stage5_no_github_main_upload";
const validatorName = "validate:v1.1.7-stage4";
const reviewPath = "docs/reviews/memory_atlas_v1_1_7_stage4_review.md";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const phaseValidators = [
  ["stage3_review_validator", "validate_memory_atlas_v1_1_7_stage3.cjs", "validate:v1.1.7-stage3", "ACC-MA-V117-S3-REVIEW"],
  [
    "stage4_phase1_validator",
    "validate_memory_atlas_v1_1_7_stage4_phase1.cjs",
    "validate:v1.1.7-stage4-phase1",
    "ACC-MA-V117-S4P01",
  ],
  [
    "stage4_phase2_validator",
    "validate_memory_atlas_v1_1_7_stage4_phase2.cjs",
    "validate:v1.1.7-stage4-phase2",
    "ACC-MA-V117-S4P02",
  ],
  [
    "stage4_phase3_validator",
    "validate_memory_atlas_v1_1_7_stage4_phase3.cjs",
    "validate:v1.1.7-stage4-phase3",
    "ACC-MA-V117-S4P03",
  ],
];

const allowedReviewChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4.cjs",
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

function parseValidatorOutput(result) {
  const output = result.stdout.trim();
  return JSON.parse(output.slice(output.indexOf("{")));
}

function validatePhaseValidators() {
  const changed = getOpenAIDatabaseChangedPaths();
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));

  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage4_review_phase_validator_deferred_scope",
      "Phase validator execution is deferred only because the open diff is limited to Stage 4 review gate files",
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
      "stage4_phase_validators_deferred_until_clean_tree",
      "Existing phase validators enforce their own changed-path scopes; run this Stage 4 validator again after commit to execute them on a clean tree",
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
      "Memory Atlas v1.1.7 Stage 4 Review",
      taskId,
      acceptanceId,
      status,
      "Stage 4 is review-passed",
      "Phase 4.1",
      "Phase 4.2",
      "Phase 4.3",
      "Visual Contract Update",
      "C3 Starfield Spike",
      "Integration",
      validatorName,
      "validate:v1.1.7-stage4-phase1",
      "validate:v1.1.7-stage4-phase2",
      "validate:v1.1.7-stage4-phase3",
      "validate:memory-starfield-spike-browser",
      "validate:memory-starfield-integration-browser",
      "memory_starfield_visual_contract.v1_1_7_stage4_phase1",
      "memory_starfield_c3_spike.v1_1_7_stage4_phase2",
      "memory_starfield_integration.v1_1_7_stage4_phase3",
      "memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3",
      "No Stage 5 work",
      "No raw/private/cookie/session/secret data access",
      "No direct active-memory writeback",
      "No agent apply",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
      "pending Stage 5",
    ]),
    "stage4_review_artifact",
    "Stage 4 review artifact records phase coverage, browser evidence, validation, boundaries and next gate",
    "Stage 4 review artifact is incomplete",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4.cjs",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage4.cjs",
    "stage4_package_script",
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
        "Phase 4.1",
        "Phase 4.2",
        "Phase 4.3",
        "pending Stage 5",
        "No GitHub main upload",
      ]),
      `stage4_records_${name}`,
      `${name} registers Stage 4 review status, acceptance, validator and no-upload boundary`,
      `${name} is missing Stage 4 review tokens`,
    );
  }
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  const remoteBranch = run("git", ["ls-remote", "--heads", "origin", branchName], { cwd: worktreeRoot }).stdout.trim();

  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage4_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage4_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
  assertCondition(
    remoteBranch === "",
    "stage4_no_remote_branch",
    "No remote branch exists for the local Stage 0-10 continuation branch",
    "Local continuation branch was pushed before final Stage 0-10 upload",
    { branchName, stdout: remoteBranch },
  );
}

function validateChangeScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage4_review_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 4 review gate, validator, package script and records",
    "Unexpected files changed outside Stage 4 review scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    review.includes("No Stage 5 work") &&
      review.includes("No raw/private/cookie/session/secret data access") &&
      review.includes("No direct active-memory writeback") &&
      review.includes("No agent apply") &&
      review.includes("No GitHub main upload before the whole Stage 0-10 project is complete") &&
      review.includes("No Cloudflare live deploy or Access policy change"),
    "stage4_review_boundary",
    "No Stage 5 work, raw/private read, direct writeback, agent apply, deploy or GitHub main upload is included",
    "Stage 4 review boundary violation detected",
  );
}

function main() {
  validatePhaseValidators();
  validateReviewArtifact();
  validateRecords();
  validateCanonicalBoundary();
  validateChangeScope();
  validateBoundary();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage4",
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
        stage: "v1.1.7-stage4",
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
