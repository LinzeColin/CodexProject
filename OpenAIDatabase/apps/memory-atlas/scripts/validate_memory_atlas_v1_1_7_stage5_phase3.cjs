#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S5P03";
const acceptanceId = "ACC-MA-V117-S5P03";
const status = "phase_5_3_timeline_integration_completed_pending_stage5_review";
const validatorName = "validate:v1.1.7-stage5-phase3";
const browserValidatorName = "validate:memory-river-integration-browser";
const previousValidatorName = "validate:v1.1.7-stage5-phase2";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage5_phase2.cjs";
const integrationVersion = "memory_river_integration.v1_1_7_stage5_phase3";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const planPath = "docs/product/memory_atlas_timeline_replacement_plan.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage5_phase3_timeline_integration_acceptance.md";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_river_integration_browser.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/config/visualFlags.ts",
  "OpenAIDatabase/config/visualization/model_parameters.memory_river.yaml",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${planPath}`,
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

function validateStage5Phase2Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage5_phase3_open_diff_scope",
      "Open diff is limited to Stage 5 Phase 5.3 Timeline integration files",
      "Unexpected files changed outside Stage 5 Phase 5.3 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage5_phase2_validator_registered_for_post_commit_run",
      "Stage 5 Phase 5.2 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 5 Phase 5.2 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage5_phase2_validator_deferred_until_clean_tree",
      "Stage 5 Phase 5.2 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S5P02",
    "stage5_phase2_validator",
    "Stage 5 Phase 5.2 validator returned PASS before Stage 5 Phase 5.3 acceptance",
    "Stage 5 Phase 5.2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateRuntimeIntegration() {
  [
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/config/visualFlags.ts",
    "apps/memory-atlas/scripts/validate_memory_river_integration_browser.cjs",
  ].forEach(validateTextFile);

  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const flags = readRepoFile("apps/memory-atlas/src/config/visualFlags.ts");
  const browser = readRepoFile("apps/memory-atlas/scripts/validate_memory_river_integration_browser.cjs");

  assertCondition(
    hasAll(flags, [
      `TIMELINE_RENDERER_FEATURE_FLAG_VERSION = "${integrationVersion}"`,
      "DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = \"memory-river\"",
      "TIMELINE_RENDERER_STORAGE_KEY = \"memory-atlas.timeline-renderer\"",
      "timelineRenderer",
      "timeline",
      "VITE_MEMORY_ATLAS_TIMELINE_RENDERER",
      "\"legacy\"",
      "\"memory-river\"",
    ]),
    "stage5_phase3_feature_flag_runtime",
    "Timeline feature flag defaults to memory-river and preserves URL/env/storage legacy rollback",
    "Timeline renderer feature flag contract is incomplete",
  );

  assertCondition(
    hasAll(app, [
      "TIMELINE_RENDERER_FEATURE_FLAG_VERSION",
      "__memoryAtlasStage5Phase3",
      "integrationVersion: TIMELINE_RENDERER_FEATURE_FLAG_VERSION",
      "defaultRendererMode: DEFAULT_TIMELINE_RENDERER_MODE",
      "legacyRollbackEnabled: true",
      "data-stage5-phase3-integration={TIMELINE_RENDERER_FEATURE_FLAG_VERSION}",
      "data-default-timeline-renderer={DEFAULT_TIMELINE_RENDERER_MODE}",
      "data-stage5-phase3-memory-river={TIMELINE_RENDERER_FEATURE_FLAG_VERSION}",
      "data-legacy-rollback=\"timelineRenderer=legacy\"",
      "data-timeline-renderer={timelineRendererMode}",
      "updateTimelineRendererMode(\"memory-river\")",
      "updateTimelineRendererMode(\"legacy\")",
      "memory-river-canvas",
      "timelineRendererMode === \"memory-river\"",
      "timelineRendererMode === \"legacy\"",
    ]),
    "stage5_phase3_app_integration_hook",
    "App Timeline exposes Stage 5.3 integration metadata, default Memory River and legacy rollback hook",
    "App Timeline integration hook is incomplete",
  );

  assertCondition(
    hasAll(app, [
      "data-evidence-layers=\"black-hole-lifecycle proto-star-lifecycle stale-deprecated roi-gradient\"",
      "data-roi-gradient=\"capability-growth\"",
      "memory-river-selected-range",
      "memory-river-brush-draft",
      "memory-river-event-card",
      "redacted derived event",
      "rawPrivateDataIncluded: false",
      "directActiveMemoryWriteback: false",
      "proposalWrite: false",
    ]),
    "stage5_phase3_memory_river_runtime",
    "Memory River runtime keeps evidence layers, brush selection, redacted event card and safe no-writeback metadata",
    "Memory River runtime is missing evidence, interaction or safety metadata",
  );

  assertCondition(
    hasAll(browser, [
      integrationVersion,
      "stage5_phase3_browser_default_memory_river",
      "stage5_phase3_browser_river_layers",
      "stage5_phase3_browser_legacy_toggle",
      "stage5_phase3_browser_memory_river_toggle",
      "stage5_phase3_browser_url_rollback",
      "stage5_phase3_browser_brush_interaction",
      "stage5_phase3_browser_screenshot",
      "stage5_phase3_browser_console",
      "timelineRenderer=legacy",
      "__memoryAtlasStage5Phase3",
    ]),
    "stage5_phase3_browser_validator_contract",
    "Browser validator checks default Memory River, legacy rollback, URL rollback, brush interaction, screenshot and console safety",
    "Browser validator is missing Stage 5 Phase 5.3 checks",
  );
}

function validateDocsAndRecords() {
  [
    planPath,
    acceptancePath,
    "config/visualization/model_parameters.memory_river.yaml",
    "config/visualization/model_parameters.universe_state.yaml",
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase3.cjs",
  ].forEach(validateTextFile);

  const plan = readRepoFile(planPath);
  const acceptance = readRepoFile(acceptancePath);
  const memoryRiverParams = readRepoFile("config/visualization/model_parameters.memory_river.yaml");
  const universeParams = readRepoFile("config/visualization/model_parameters.universe_state.yaml");
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  const records = [
    ["CHANGELOG.md", readRepoFile("CHANGELOG.md")],
    ["功能清单.md", readRepoFile("功能清单.md")],
    ["开发记录.md", readRepoFile("开发记录.md")],
    ["模型参数文件.md", readRepoFile("模型参数文件.md")],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md")],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")],
    ["config/visualization/model_parameters.universe_state.yaml", universeParams],
    ["config/visualization/model_parameters.memory_river.yaml", memoryRiverParams],
  ];

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage5_phase3.cjs" &&
      packageJson.scripts?.[browserValidatorName] === "node scripts/validate_memory_river_integration_browser.cjs",
    "stage5_phase3_package_scripts",
    `package.json exposes ${validatorName} and ${browserValidatorName}`,
    "package.json is missing Stage 5 Phase 5.3 scripts",
    {
      validator: packageJson.scripts?.[validatorName],
      browserValidator: packageJson.scripts?.[browserValidatorName],
    },
  );

  assertCondition(
    hasAll(plan, [
      "v1.1.7 Stage 5 Phase 5.3 Timeline Integration Addendum",
      taskId,
      acceptanceId,
      status,
      integrationVersion,
      "default memory-river",
      "legacy rollback",
      "timelineRenderer=legacy",
      "No Stage 5 review",
      "No GitHub main upload",
    ]),
    "stage5_phase3_plan_addendum",
    "Timeline replacement plan records the v1.1.7 Stage 5 Phase 5.3 integration addendum and boundaries",
    "Timeline replacement plan is missing the Stage 5 Phase 5.3 addendum",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 5 Phase 5.3 Timeline Integration Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      browserValidatorName,
      integrationVersion,
      "default memory-river",
      "legacy rollback",
      "timelineRenderer=legacy",
      "brush interaction",
      "old Timeline rollback available",
      "new page default enabled",
      "No Stage 5 review",
      "No GitHub main upload",
    ]),
    "stage5_phase3_acceptance_contract",
    "Acceptance document pins default renderer, rollback, browser interaction, validation and no-upload boundary",
    "Stage 5 Phase 5.3 acceptance document is incomplete",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        browserValidatorName,
        integrationVersion,
        "Phase 5.3",
        "default memory-river",
        "legacy rollback",
        "No GitHub main upload",
      ]),
      `stage5_phase3_records_${name}`,
      `${name} records Stage 5 Phase 5.3 status, acceptance, validator, browser evidence and no-upload boundary`,
      `${name} is missing Stage 5 Phase 5.3 tokens`,
    );
  }
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  const remoteBranch = run("git", ["ls-remote", "--heads", "origin", branchName], { cwd: worktreeRoot }).stdout.trim();

  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage5_phase3_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage5_phase3_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
  assertCondition(
    remoteBranch === "",
    "stage5_phase3_no_remote_branch",
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
    "stage5_phase3_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 5 Phase 5.3 Timeline integration, acceptance, records, validators and package scripts",
    "Unexpected files changed outside Stage 5 Phase 5.3 scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const boundarySources = [
    readRepoFile(planPath),
    readRepoFile(acceptancePath),
    readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md"),
  ].join("\n");
  assertCondition(
    hasAll(boundarySources, [
      "No Stage 5 review",
      "No Stage 6",
      "No raw/private data read",
      "No direct active-memory writeback",
      "No agent apply",
      "No deploy",
      "No GitHub main upload",
    ]),
    "stage5_phase3_boundary",
    "Boundary records prohibit Stage 5 review, Stage 6, raw/private reads, direct writeback, agent apply, deploy and GitHub upload",
    "Stage 5 Phase 5.3 boundary record is incomplete",
  );
}

function main() {
  validateStage5Phase2Continuity();
  validateRuntimeIntegration();
  validateDocsAndRecords();
  validateCanonicalBoundary();
  validateChangeScope();
  validateBoundary();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage5-phase3",
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
        stage: "v1.1.7-stage5-phase3",
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
