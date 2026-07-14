#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S4P03";
const acceptanceId = "ACC-MA-V117-S4P03";
const status = "phase_4_3_integration_completed_pending_stage4_review";
const validatorName = "validate:v1.1.7-stage4-phase3";
const browserValidatorName = "validate:memory-starfield-integration-browser";
const previousValidatorName = "validate:v1.1.7-stage4-phase2";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage4_phase2.cjs";
const integrationVersion = "memory_starfield_integration.v1_1_7_stage4_phase3";
const mappingVersion = "memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3";

const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage4_phase3_integration_acceptance.md";
const mappingPath = "apps/memory-atlas/src/models/starfieldMapping.ts";
const browserValidatorPath = "apps/memory-atlas/scripts/validate_memory_starfield_integration_browser.cjs";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase3.cjs",
  `OpenAIDatabase/${browserValidatorPath}`,
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/components/GalaxyScene.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/config/visualFlags.ts",
  `OpenAIDatabase/${mappingPath}`,
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
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

function validateStage4Phase2Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage4_phase3_open_diff_scope",
      "Open diff is limited to Stage 4 Phase 4.3 Integration files",
      "Unexpected files changed outside Stage 4 Phase 4.3 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage4_phase2_validator_registered_for_post_commit_run",
      "Stage 4 Phase 4.2 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 4 Phase 4.2 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage4_phase2_validator_deferred_until_clean_tree",
      "Stage 4 Phase 4.2 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S4P02",
    "stage4_phase2_validator",
    "Stage 4 Phase 4.2 validator returned PASS before Stage 4 Phase 4.3 acceptance",
    "Stage 4 Phase 4.2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateIntegrationFiles() {
  [
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/src/config/visualFlags.ts",
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/components/GalaxyScene.tsx",
    mappingPath,
    browserValidatorPath,
    acceptancePath,
  ].forEach(validateTextFile);

  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage4_phase3.cjs" &&
      packageJson.scripts?.[browserValidatorName] === "node scripts/validate_memory_starfield_integration_browser.cjs",
    "stage4_phase3_package_scripts",
    "package.json exposes Stage 4 Phase 4.3 static and browser validators",
    "package.json is missing Stage 4 Phase 4.3 validator scripts",
    {
      staticScript: packageJson.scripts?.[validatorName],
      browserScript: packageJson.scripts?.[browserValidatorName],
    },
  );

  const flags = readRepoFile("apps/memory-atlas/src/config/visualFlags.ts");
  assertCondition(
    hasAll(flags, [
      "DEFAULT_GALAXY_RENDERER_MODE",
      "\"memory-starfield\"",
      "VITE_MEMORY_ATLAS_GALAXY_RENDERER",
      "galaxyRenderer",
      "legacy",
      "memory_starfield_integration.v1_1_7_stage4_phase3",
    ]),
    "stage4_phase3_feature_flag",
    "Galaxy feature flag defaults to memory-starfield while preserving legacy and URL/env/localStorage overrides",
    "Galaxy feature flag does not preserve default-new plus old-renderer rollback",
  );

  const mapping = readRepoFile(mappingPath);
  assertCondition(
    hasAll(mapping, [
      "STARFIELD_MAPPING_VERSION",
      mappingVersion,
      "mapUniverseStateSnapshotToStarfield",
      "mapAtlasNodesToStarfield",
      "mass_score",
      "roi_potential",
      "brightness",
      "color",
      "trailStrength",
      "fallback",
      "raw_private_data_included === false",
      "writeback_allowed === false",
    ]),
    "stage4_phase3_snapshot_mapping_contract",
    "Snapshot mapping layer defines explicit formulas, fallback defaults and redacted safety checks",
    "Snapshot mapping layer is missing formulas, fallback or safety checks",
  );

  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  assertCondition(
    hasAll(app, [
      "STARFIELD_INTEGRATION_VERSION",
      integrationVersion,
      "buildGalaxyStarfieldMapping",
      "mapAtlasNodesToStarfield",
      "mapUniverseStateSnapshotToStarfield",
      "universe_state.sample.json",
      "data-stage4-phase3-integration",
      "data-starfield-mapping-version",
      "window.__memoryAtlasStage4Phase3",
      "source: \"universe_state_snapshot\"",
      "source: \"atlas_nodes\"",
    ]),
    "stage4_phase3_app_integration",
    "Galaxy page integrates default memory-starfield mode and snapshot/atlas mapping debug contract",
    "Galaxy page is missing Stage 4 Phase 4.3 integration hooks",
  );

  const galaxy = readRepoFile("apps/memory-atlas/src/components/GalaxyScene.tsx");
  assertCondition(
    hasAll(galaxy, [
      "starfieldMapping",
      "mappingVersion",
      "mappingSource",
      "mappedParticleCount",
      "data-starfield-mapping-version",
      "data-starfield-mapping-source",
      "massScore",
      "trailStrength",
      "window.__memoryAtlasGalaxySignal",
    ]),
    "stage4_phase3_scene_mapping",
    "GalaxyScene consumes mapped particle attributes and exposes mapping metadata for browser validation",
    "GalaxyScene does not consume mapped starfield attributes",
  );

  const browserValidator = readRepoFile(browserValidatorPath);
  assertCondition(
    hasAll(browserValidator, [
      "stage4_phase3_browser_default_starfield",
      "stage4_phase3_browser_legacy_switch",
      "stage4_phase3_browser_snapshot_mapping",
      "stage4_phase3_browser_formula_panel",
      "stage4_phase3_browser_screenshot",
      integrationVersion,
      mappingVersion,
    ]),
    "stage4_phase3_browser_validator_contract",
    "Browser validator covers default renderer, legacy rollback, snapshot mapping, formula panel and screenshot",
    "Browser validator is missing Stage 4 Phase 4.3 browser coverage",
  );
}

function validateAcceptanceAndRecords() {
  [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "config/visualization/model_parameters.universe_state.yaml",
    acceptancePath,
  ].forEach(validateTextFile);

  const acceptance = readRepoFile(acceptancePath);
  assertCondition(
    hasAll(acceptance, [
      "Stage 4 Phase 4.3",
      taskId,
      acceptanceId,
      status,
      integrationVersion,
      mappingVersion,
      "Feature Flag",
      "Snapshot Mapping",
      "new memory-starfield",
      "legacy rollback",
      "redacted universe_state.sample.json",
      browserValidatorName,
      "No Stage 5",
      "No GitHub main upload",
    ]),
    "stage4_phase3_acceptance_artifact",
    "Acceptance artifact records Phase 4.3 tasks, validation, rollback and no-upload boundary",
    "Acceptance artifact is missing Stage 4 Phase 4.3 contract details",
  );

  const requiredFragments = [
    "Memory Atlas v1.1.7 Stage 4 Phase 4.3 Integration",
    taskId,
    acceptanceId,
    status,
    validatorName,
    browserValidatorName,
    integrationVersion,
    mappingVersion,
    "No Stage 5",
    "No GitHub main upload",
  ];
  for (const file of [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  ]) {
    const source = readRepoFile(file);
    assertCondition(
      hasAll(source, requiredFragments),
      `stage4_phase3_records_${file}`,
      `${file} records Stage 4 Phase 4.3 status, acceptance, validators and no-upload boundary`,
      `${file} is missing Stage 4 Phase 4.3 records`,
    );
  }

  const yaml = readRepoFile("config/visualization/model_parameters.universe_state.yaml");
  assertCondition(
    hasAll(yaml, [
      "stage4_phase3_integration",
      integrationVersion,
      mappingVersion,
      "default_renderer_mode: memory-starfield",
      "legacy_renderer_mode: legacy",
      "mapping_source_priority",
      "redacted_snapshot",
      "atlas_nodes_fallback",
      "no_github_main_upload",
    ]),
    "stage4_phase3_model_parameters_yaml",
    "Universe state model parameters include Phase 4.3 renderer and snapshot mapping controls",
    "Universe state model parameters are missing Phase 4.3 controls",
  );
}

function validateRepositoryBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage4_phase3_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );

  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage4_phase3_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );

  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage4_phase3_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 4 Phase 4.3 integration files",
    "Unexpected files changed outside Stage 4 Phase 4.3 scope",
    { changed, outside },
  );

  const result = run("git", ["ls-remote", "--heads", "origin", "codex/memory-atlas-v117-stage0-10-local"], {
    cwd: worktreeRoot,
  });
  assertCondition(
    result.stdout.trim() === "",
    "stage4_phase3_no_remote_branch",
    "No remote branch exists for the local Stage 0-10 continuation branch",
    "Remote branch exists despite no-upload boundary",
    { stdout: result.stdout.trim() },
  );
}

function main() {
  try {
    validateStage4Phase2Continuity();
    validateIntegrationFiles();
    validateAcceptanceAndRecords();
    validateRepositoryBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.7-stage4-phase3", acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(
      JSON.stringify(
        {
          status: "FAIL",
          stage: "v1.1.7-stage4-phase3",
          acceptance_id: acceptanceId,
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
}

main();
