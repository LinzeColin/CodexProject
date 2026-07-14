#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S10-REVIEW";
const acceptanceId = "ACC-MA-V117-S10-REVIEW";
const status = "stage_10_review_passed_pending_final_github_main_upload";
const validatorName = "validate:v1.1.7-stage10";
const reviewPath = "docs/reviews/memory_atlas_v1_1_7_stage10_review.md";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const allowedReviewChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_part2_stage1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_part3_stage2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_part4_stage3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_part9_stage8.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage10.cjs",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
];

const cleanTreeValidators = [
  [
    "stage10_phase1_validator",
    "validate_memory_atlas_v1_1_7_stage10_phase1.cjs",
    "validate:v1.1.7-stage10-phase1",
    "ACC-MA-V117-S10P01",
  ],
  [
    "whole_project_validator",
    "validate_memory_atlas_whole_project.cjs",
    "validate:whole-project",
    null,
  ],
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
    maxBuffer: 128 * 1024 * 1024,
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
  const firstBrace = output.indexOf("{");
  const lastBrace = output.lastIndexOf("}");
  if (firstBrace < 0 || lastBrace < firstBrace) return null;
  return JSON.parse(output.slice(firstBrace, lastBrace + 1));
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

function validateCleanTreeValidators() {
  const changed = getOpenAIDatabaseChangedPaths();
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));

  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage10_review_clean_tree_validators_deferred_scope",
      "Clean-tree validator execution is deferred only because the open diff is limited to Stage 10 review gate files",
      "Clean-tree validator execution cannot be deferred when unrelated files are changed",
      { changed, outside },
    );

    cleanTreeValidators.forEach(([name, script, scriptName]) => {
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
      "stage10_review_clean_tree_validators_deferred_until_commit",
      "Stage 10 Phase 10.1 and whole-project validators run after this review gate is committed on a clean tree",
      { changed },
    );
    return;
  }

  const stage10Phase1 = run("node", ["scripts/validate_memory_atlas_v1_1_7_stage10_phase1.cjs"], { cwd: appRoot });
  const stage10Parsed = parseValidatorOutput(stage10Phase1);
  assertCondition(
    stage10Parsed?.status === "PASS" && stage10Parsed?.acceptance_id === "ACC-MA-V117-S10P01",
    "stage10_review_phase1_continuity",
    "Stage 10 Phase 10.1 validator returned PASS before Stage 10 review clean-tree validation",
    "Stage 10 Phase 10.1 validator did not return PASS",
    { status: stage10Parsed?.status, acceptance_id: stage10Parsed?.acceptance_id },
  );

  const wholeProject = run("node", ["scripts/validate_memory_atlas_whole_project.cjs"], { cwd: appRoot });
  const wholeParsed = parseValidatorOutput(wholeProject);
  const wholeCheckNames = new Set((wholeParsed?.checks || []).map((check) => check.name));
  const requiredWholeChecks = [
    "whole_project_part2_stage1_passed",
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
  const missingWholeChecks = requiredWholeChecks.filter((name) => !wholeCheckNames.has(name));
  assertCondition(
    wholeParsed?.status === "PASS" && missingWholeChecks.length === 0,
    "stage10_review_whole_project_validation",
    "Whole-project validator returned PASS with required final acceptance, release, safety, remote and cleanup checks",
    "Whole-project validator did not return required PASS evidence",
    {
      status: wholeParsed?.status,
      scope: wholeParsed?.scope,
      missingWholeChecks,
      checkCount: wholeParsed?.checks?.length ?? null,
    },
  );
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const review = readRepoFile(reviewPath);

  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.7 Stage 10 Review",
      taskId,
      acceptanceId,
      status,
      "Stage 10 is review-passed",
      "pending final one-time GitHub main upload",
      "Stage 10 Phase 10.1",
      "Final hardening upload readiness",
      "memory_atlas_v1_1_7_final_hardening_upload_readiness_contract",
      "performance_safety_accessibility_matrix",
      "release_rollback_matrix",
      "final_validation_matrix",
      "github_main_upload_matrix",
      "governance_sync_matrix",
      "new_machine_recovery_matrix",
      "validate:v1.1.7-stage10-phase1",
      "validate:whole-project",
      "validate:part2-stage1",
      "schema compatibility hardening",
      "legacy whole-project validator hardening",
      "Chinese-first copy hardening",
      "memory_starfield_spike_fixture.v1_1_7_stage4_phase2",
      "memory_river_spike_fixture.v1_1_7_stage5_phase2",
      "No intermediate GitHub upload",
      "No GitHub main upload in this review",
      "No remote development branch",
      "No raw/private/cookie/session/secret data access",
      "No direct active-memory writeback",
      "No proposal queue write",
    ]),
    "stage10_review_artifact",
    "Stage 10 review artifact records phase coverage, whole-project validation, schema hardening, boundaries and final upload gate",
    "Stage 10 review artifact is incomplete",
  );
}

function validatePart2SchemaCompatibility() {
  const source = fs.readFileSync(path.join(appRoot, "scripts/validate_memory_atlas_part2_stage1.cjs"), "utf8");
  assertCondition(
    hasAll(source, [
      "starfieldFixtureSchemaVersions",
      "riverFixtureSchemaVersions",
      "memory_starfield_spike_fixture.v1",
      "memory_starfield_spike_fixture.v1_1_7_stage4_phase2",
      "memory_river_spike_fixture.v1",
      "memory_river_spike_fixture.v1_1_7_stage5_phase2",
      "allowedSchemaVersions",
    ]),
    "stage10_review_part2_schema_compatibility",
    "Part 2 validator explicitly allows legacy and current v1.1.7 fixture schema versions without weakening safety checks",
    "Part 2 validator does not record explicit schema compatibility hardening",
  );
}

function validateChineseFirstCopyHardening() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  assertCondition(
    app.includes("长期记忆")
      && !app.includes("active memory")
      && !app.includes("change proposal")
      && !app.includes("versioned proposal"),
    "stage10_review_chinese_first_copy_hardening",
    "App.tsx no longer exposes forbidden English writeback copy in core UI surfaces",
    "App.tsx still contains forbidden English writeback copy",
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage10.cjs",
    "stage10_review_package_script",
    "package.json exposes the Stage 10 review validator",
    "package.json is missing the Stage 10 review validator script",
    { script: packageJson.scripts?.[validatorName] },
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "Stage 10 Review",
        "Stage 10 Phase 10.1",
        "Final hardening upload readiness",
        "validate:v1.1.7-stage10-phase1",
        "validate:whole-project",
        "validate:part2-stage1",
        "schema compatibility hardening",
        "memory_starfield_spike_fixture.v1_1_7_stage4_phase2",
        "memory_river_spike_fixture.v1_1_7_stage5_phase2",
        "pending final one-time GitHub main upload",
        "No intermediate GitHub upload",
        "No GitHub main upload in this review",
        "No remote development branch",
      ]),
      `stage10_review_records_${name}`,
      `${name} records Stage 10 review status, validators, schema hardening and final upload boundary`,
      `${name} is missing Stage 10 review record fragments`,
    );
  }
}

function validateChangedScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage10_review_changed_scope",
    "Open diff is limited to Stage 10 review artifact, validator, package script, App copy hardening, legacy validator hardening and governance records",
    "Open diff contains files outside the Stage 10 review allowed scope",
    { changed, outside },
  );
}

function validateRuntimeBoundary() {
  const changed = getOpenAIDatabaseChangedPaths();
  const allowedRuntimeCopyPaths = new Set([
    "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  ]);
  const touchedRuntime = changed.filter((file) => (
    file.includes("OpenAIDatabase/apps/memory-atlas/src/")
      || file.includes("OpenAIDatabase/apps/memory-atlas/dist/")
      || file.includes("OpenAIDatabase/apps/memory-atlas/build/")
      || file.includes("OpenAIDatabase/apps/memory-atlas/src/fixtures/")
      || file.includes("OpenAIDatabase/data/raw/")
      || file.includes("OpenAIDatabase/data/private/")
      || file.includes(".app")
  ) && !allowedRuntimeCopyPaths.has(file));
  assertCondition(
    touchedRuntime.length === 0,
    "stage10_review_runtime_boundary",
    "No production runtime logic/CSS/build/app/raw/private artifact is changed in Stage 10 review beyond App.tsx Chinese-first copy hardening",
    "Stage 10 review touched runtime, build, app, raw/private data or deploy artifacts",
    { touchedRuntime, allowedRuntimeCopyPaths: [...allowedRuntimeCopyPaths] },
  );
}

function validateGitBoundary() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName,
    "stage10_review_local_branch",
    `Current branch is ${branchName}`,
    `Current branch must remain ${branchName}`,
    { branch },
  );

  run("git", ["rev-parse", "--verify", "origin/main"], { cwd: worktreeRoot });
  run("git", ["merge-base", "--is-ancestor", "origin/main", "HEAD"], { cwd: worktreeRoot });
  pass(
    "stage10_review_origin_main_ancestor",
    "Current HEAD contains origin/main before final one-time upload work",
  );

  const remoteBranch = spawnSync("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    encoding: "utf8",
    stdio: "pipe",
  });
  assertCondition(
    remoteBranch.status === 0 && remoteBranch.stdout.trim() === "",
    "stage10_review_no_remote_branch",
    "No remote Stage 0-10 development branch exists; intermediate work remains local only",
    "Remote development branch exists or could not be checked",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function main() {
  validateCleanTreeValidators();
  validateReviewArtifact();
  validatePart2SchemaCompatibility();
  validateChineseFirstCopyHardening();
  validateRecords();
  validateChangedScope();
  validateRuntimeBoundary();
  validateGitBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_1_7_stage10",
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
    validator: "validate_memory_atlas_v1_1_7_stage10",
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
