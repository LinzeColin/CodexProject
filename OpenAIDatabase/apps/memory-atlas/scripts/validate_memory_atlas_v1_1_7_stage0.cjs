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
    ["stage0_phase1_validator", "validate_memory_atlas_v1_1_7_stage0_phase1.cjs", "ACC-MA-V117-S0P01"],
    ["stage0_phase2_validator", "validate_memory_atlas_v1_1_7_stage0_phase2.cjs", "ACC-MA-V117-S0P02"],
    ["stage0_phase3_validator", "validate_memory_atlas_v1_1_7_stage0_phase3.cjs", "ACC-MA-V117-S0P03"],
  ];

  validators.forEach(([name, script, acceptanceId]) => {
    const result = run("node", [`scripts/${script}`], { cwd: appRoot });
    const output = result.stdout.trim();
    const parsed = JSON.parse(output.slice(output.indexOf("{")));
    assertCondition(
      parsed.status === "PASS" && parsed.acceptance_id === acceptanceId,
      name,
      `${script} returned PASS for ${acceptanceId}`,
      `${script} did not return PASS for ${acceptanceId}`,
      { status: parsed.status, acceptance_id: parsed.acceptance_id },
    );
  });
}

function validateReviewArtifact() {
  const reviewPath = "docs/reviews/memory_atlas_v1_1_7_stage0_review.md";
  validateTextFile(reviewPath);
  const review = readRepoFile(reviewPath);

  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.7 Stage 0 Review",
      "MA-V117-S0-REVIEW",
      "ACC-MA-V117-S0-REVIEW",
      "stage_0_review_passed_pending_stage1_no_github_main_upload",
      "Phase 0.1",
      "Phase 0.2",
      "Phase 0.3",
      "validate:v1.1.7-stage0",
      "validate:v1.1.7-stage0-phase1",
      "validate:v1.1.7-stage0-phase2",
      "validate:v1.1.7-stage0-phase3",
      "No Stage 1 work",
      "No raw/private/cookie/session/secret data access",
      "No direct frontend writeback",
      "No GitHub main upload before the whole Stage 0-8 project is complete",
    ]),
    "stage0_review_artifact",
    "Stage 0 review artifact records phase coverage, validation, boundaries and next gate",
    "Stage 0 review artifact is incomplete",
  );
}

function validateRecords() {
  const packageJson = readRepoFile("apps/memory-atlas/package.json");
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0.cjs",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.includes('"validate:v1.1.7-stage0": "node scripts/validate_memory_atlas_v1_1_7_stage0.cjs"'),
    "stage0_package_script",
    "package.json exposes validate:v1.1.7-stage0",
    "package.json is missing validate:v1.1.7-stage0",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        "MA-V117-S0-REVIEW",
        "ACC-MA-V117-S0-REVIEW",
        "stage_0_review_passed_pending_stage1_no_github_main_upload",
        "validate:v1.1.7-stage0",
      ]),
      `stage0_records_${name}`,
      `${name} registers Stage 0 review status, acceptance and validator`,
      `${name} is missing Stage 0 review tokens`,
    );
  }
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage0_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage0_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
}

function main() {
  validatePhaseValidators();
  validateReviewArtifact();
  validateRecords();
  validateCanonicalBoundary();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage0",
        acceptance_id: "ACC-MA-V117-S0-REVIEW",
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
        stage: "v1.1.7-stage0",
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
