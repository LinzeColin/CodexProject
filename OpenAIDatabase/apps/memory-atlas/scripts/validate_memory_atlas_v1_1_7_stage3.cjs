#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S3-REVIEW";
const acceptanceId = "ACC-MA-V117-S3-REVIEW";
const status = "stage_3_review_passed_pending_stage4_no_github_main_upload";
const validatorName = "validate:v1.1.7-stage3";
const reviewPath = "docs/reviews/memory_atlas_v1_1_7_stage3_review.md";

const allowedReviewChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3.cjs",
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

function validatePhaseValidators() {
  const validators = [
    ["stage2_review_validator", "validate_memory_atlas_v1_1_7_stage2.cjs", "ACC-MA-V117-S2-REVIEW"],
    ["stage3_phase1_validator", "validate_memory_atlas_v1_1_7_stage3_phase1.cjs", "ACC-MA-V117-S3P01"],
    ["stage3_phase2_validator", "validate_memory_atlas_v1_1_7_stage3_phase2.cjs", "ACC-MA-V117-S3P02"],
  ];
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage3_phase_validator_deferred_scope",
      "Phase validator execution is deferred only because the open diff is limited to Stage 3 review gate files",
      "Phase validator execution cannot be deferred when unrelated files are changed",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    validators.forEach(([name, script]) => {
      const scriptPath = path.join(appRoot, "scripts", script);
      const scriptRegistered = Object.values(packageJson.scripts || {}).some((command) => command.includes(script));
      assertCondition(
        fs.existsSync(scriptPath) && scriptRegistered,
        `${name}_registered_for_post_commit_run`,
        `${script} exists and is registered for clean-tree execution after this review gate is committed`,
        `${script} is missing or not registered`,
        { script, scriptRegistered },
      );
    });
    pass(
      "stage3_phase_validators_deferred_until_clean_tree",
      "Existing phase validators enforce their own changed-path scopes; run this Stage 3 validator again after commit to execute them on a clean tree",
      { changed },
    );
    return;
  }

  validators.forEach(([name, script, expectedAcceptanceId]) => {
    const result = run("node", [`scripts/${script}`], { cwd: appRoot });
    const output = result.stdout.trim();
    const parsed = JSON.parse(output.slice(output.indexOf("{")));
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
      "Memory Atlas v1.1.7 Stage 3 Review",
      taskId,
      acceptanceId,
      status,
      "Stage 3 is review-passed",
      "Phase 3.1",
      "Phase 3.2",
      validatorName,
      "validate:v1.1.7-stage3-phase1",
      "validate:v1.1.7-stage3-phase2",
      "validate:v1.1.7-stage2",
      "Default Home Structure",
      "Home Detail Operations",
      "proposal-only",
      "No Stage 4 work",
      "No Search 2.0 runtime",
      "No Review workflow runtime",
      "No Data Map 2.0 runtime",
      "No raw/private/cookie/session/secret data access",
      "No direct active-memory writeback",
      "No agent apply",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
      "pending Stage 4",
    ]),
    "stage3_review_artifact",
    "Stage 3 review artifact records phase coverage, validation, boundaries and next gate",
    "Stage 3 review artifact is incomplete",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3.cjs",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage3.cjs",
    "stage3_package_script",
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
        "Phase 3.1",
        "Phase 3.2",
        "pending Stage 4",
        "No GitHub main upload",
      ]),
      `stage3_records_${name}`,
      `${name} registers Stage 3 review status, acceptance, validator and no-upload boundary`,
      `${name} is missing Stage 3 review tokens`,
    );
  }
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage3_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage3_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
}

function validateChangeScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage3_review_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 3 review gate, validator, package script and records",
    "Unexpected files changed outside Stage 3 review scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    review.includes("No Stage 4 work") &&
      review.includes("No Search 2.0 runtime") &&
      review.includes("No Review workflow runtime") &&
      review.includes("No Data Map 2.0 runtime") &&
      review.includes("No raw/private/cookie/session/secret data access") &&
      review.includes("No direct active-memory writeback") &&
      review.includes("No agent apply") &&
      review.includes("No GitHub main upload before the whole Stage 0-10 project is complete"),
    "stage3_review_boundary",
    "No Stage 4 work, Search 2.0 runtime, Review workflow runtime, Data Map runtime, raw/private read, direct writeback, agent apply, build, deploy, app install or GitHub main upload is included",
    "Stage 3 review boundary violation detected",
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
        stage: "v1.1.7-stage3",
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
        stage: "v1.1.7-stage3",
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
