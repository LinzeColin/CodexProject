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

function collectChangedPaths() {
  const changed = new Set();
  const commandSets = [
    ["diff", "--name-only", "HEAD"],
    ["diff", "--cached", "--name-only"],
    ["diff", "--name-only", "origin/main...HEAD"],
  ];
  commandSets.forEach((args) => {
    run("git", ["-c", "core.quotePath=false", ...args], { cwd: worktreeRoot }).stdout
      .split(/\r?\n/)
      .filter(Boolean)
      .forEach((entry) => changed.add(entry));
  });

  run("git", ["-c", "core.quotePath=false", "status", "--porcelain", "--untracked-files=all"], { cwd: worktreeRoot }).stdout
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .forEach((entry) => changed.add(entry));

  return [...changed]
    .map((entry) => entry.replace(/^"|"$/g, ""))
    .filter((entry) => entry !== ".DS_Store")
    .sort();
}

function validateContractSet() {
  const productPath = "docs/product/memory_atlas_v1_1_7_gap_remediation_upgrade_contract.md";
  const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_pre_stage0_acceptance.md";
  const reviewPath = "docs/reviews/memory_atlas_v1_1_7_pre_stage0_review.md";
  const validatorPath = "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_pre_stage0.cjs";

  [productPath, acceptancePath, reviewPath, validatorPath].forEach(validateTextFile);

  const product = readRepoFile(productPath);
  const acceptance = readRepoFile(acceptancePath);
  const review = readRepoFile(reviewPath);
  const validator = readRepoFile(validatorPath);

  assertCondition(
    hasAll(product, [
      "Memory Atlas v1.1.7 Gap Remediation Upgrade Contract",
      "memory_atlas_v1_1_7_gap_remediation_upgrade_contract",
      "v1.1.7 Pre Stage 0",
      "MA-V117-PRESTAGE0",
      "ACC-MA-V117-PRESTAGE0",
      "pre_stage_0_review_passed_pending_github_main_upload",
      "v1.1.7 Stage Map",
      "Required Acceptance Matrix",
      "One-Time Upload Gate",
      "No production UI",
      "No raw/private/cookie/session/secret data read",
    ]),
    "pre_stage0_product_contract",
    "v1.1.7 pre-stage product contract records scope, stage map, matrix, non-goals and upload gate",
    "v1.1.7 pre-stage product contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Pre Stage 0 Acceptance",
      "ACC-MA-V117-PRESTAGE0",
      "MA-V117-PRESTAGE0",
      "validate:v1.1.7-pre-stage0",
      "Runtime boundary held",
      "Upload boundary held",
      "Deferred Proof",
      "No Stage 0 implementation in this run",
      "No raw/private/cookie/session/secret data read",
    ]),
    "pre_stage0_acceptance_contract",
    "v1.1.7 pre-stage acceptance records checks, deferred proof, non-goals and pass criteria",
    "v1.1.7 pre-stage acceptance is incomplete",
  );

  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.7 Pre Stage 0 Review",
      "MA-V117-PRESTAGE0",
      "ACC-MA-V117-PRESTAGE0",
      "pre_stage_0_review_passed_pending_github_main_upload",
      "v1.1.6 Stage 10 review remains the uploaded baseline",
      "validate:v1.1.7-pre-stage0",
      "No production UI",
      "No raw/private/cookie/session/secret read",
      "No GitHub main upload in review artifact",
    ]),
    "pre_stage0_review_artifact",
    "v1.1.7 pre-stage review artifact records result, baseline, validation, risks and next gate",
    "v1.1.7 pre-stage review artifact is incomplete",
  );

  assertCondition(
    hasAll(validator, [
      "validate_memory_atlas_v1_1_7_pre_stage0",
      "pre_stage0_product_contract",
      "pre_stage0_acceptance_contract",
      "pre_stage0_review_artifact",
      "pre_stage0_changed_path_boundary",
      "pre_stage0_canonical_remote",
    ]),
    "pre_stage0_validator_self_reference",
    "Validator contains the required v1.1.7 pre-stage checks",
    "Validator is missing required self-reference checks",
  );
}

function validateBaseline() {
  const stage10Review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage10_review.md");
  assertCondition(
    hasAll(stage10Review, [
      "Memory Atlas v1.1.6 Stage 10 Review",
      "stage_10_review_passed_pending_github_main_upload",
      "validate:v1.1.6-stage10",
      "validate:whole-project",
      "No raw/private data read",
      "No GitHub main upload",
    ]),
    "pre_stage0_v116_baseline",
    "v1.1.6 Stage 10 review baseline remains present",
    "v1.1.6 Stage 10 review baseline is missing or incomplete",
  );
}

function validateRecords() {
  const packageJson = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const featureList = readRepoFile("功能清单.md");
  const development = readRepoFile("开发记录.md");
  const modelIndex = readRepoFile("模型参数文件.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");

  [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "apps/memory-atlas/package.json",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.includes('"validate:v1.1.7-pre-stage0": "node scripts/validate_memory_atlas_v1_1_7_pre_stage0.cjs"'),
    "pre_stage0_package_script",
    "package.json exposes validate:v1.1.7-pre-stage0",
    "package.json is missing validate:v1.1.7-pre-stage0",
  );

  const requiredRecordTokens = [
    "MA-V117-PRESTAGE0",
    "ACC-MA-V117-PRESTAGE0",
    "pre_stage_0_review_passed_pending_github_main_upload",
    "validate:v1.1.7-pre-stage0",
    "memory_atlas_v1_1_7_gap_remediation_upgrade_contract.md",
  ];

  [
    ["CHANGELOG.md", changelog],
    ["功能清单.md", featureList],
    ["开发记录.md", development],
    ["模型参数文件.md", modelIndex],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", delivery],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", model],
  ].forEach(([name, source]) => {
    assertCondition(
      hasAll(source, requiredRecordTokens),
      `pre_stage0_records_${name}`,
      `${name} registers MA-V117-PRESTAGE0 status, acceptance, validator and evidence`,
      `${name} is missing v1.1.7 pre-stage record tokens`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "pre_stage0_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );

  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout
    .split(/\r?\n/)
    .filter(Boolean);
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "pre_stage0_sparse_checkout",
    "Sparse checkout includes OpenAIDatabase",
    "Sparse checkout does not include OpenAIDatabase",
    { sparse },
  );

  const allowed = new Set([
    "OpenAIDatabase/docs/product/memory_atlas_v1_1_7_gap_remediation_upgrade_contract.md",
    "OpenAIDatabase/docs/acceptance/memory_atlas_v1_1_7_pre_stage0_acceptance.md",
    "OpenAIDatabase/docs/reviews/memory_atlas_v1_1_7_pre_stage0_review.md",
    "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_pre_stage0.cjs",
    "OpenAIDatabase/apps/memory-atlas/package.json",
    "OpenAIDatabase/CHANGELOG.md",
    "OpenAIDatabase/功能清单.md",
    "OpenAIDatabase/开发记录.md",
    "OpenAIDatabase/模型参数文件.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  ]);
  const changed = collectChangedPaths();
  const unexpected = changed.filter((entry) => !allowed.has(entry));
  assertCondition(
    unexpected.length === 0,
    "pre_stage0_changed_path_boundary",
    "Changed paths are limited to v1.1.7 pre-stage contracts, review, records, package script and validator",
    "Unexpected path changed in v1.1.7 pre-stage",
    { changed, unexpected },
  );
}

function main() {
  validateContractSet();
  validateBaseline();
  validateRecords();
  validateGitBoundary();

  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-pre-stage0",
        acceptance_id: "ACC-MA-V117-PRESTAGE0",
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
        stage: "v1.1.7-pre-stage0",
        error: error.message,
        details: error.details || null,
        stdout: error.stdout || null,
        stderr: error.stderr || null,
        checks,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}
