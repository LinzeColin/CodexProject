#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S4P01";
const acceptanceId = "ACC-MA-V117-S4P01";
const status = "phase_4_1_visual_contract_update_completed_pending_stage4_review";
const validatorName = "validate:v1.1.7-stage4-phase1";
const previousValidatorName = "validate:v1.1.7-stage3";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage3.cjs";
const visualContractVersion = "memory_starfield_visual_contract.v1_1_7_stage4_phase1";
const terrainContractVersion = "memory_terrain_layer.v1_1_7_stage4_phase1";

const visualContractPath = "docs/product/memory_starfield_visual_contract.md";
const terrainLayerPath = "docs/architecture/memory_terrain_layer.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage4_phase1_visual_contract_acceptance.md";

const requiredVisualPrimitives = [
  "nebula_field",
  "flow_field",
  "particle_trails",
  "gravity_sources",
  "black_hole_core",
  "proto_star_cloud",
  "memory_terrain_layer",
];

const requiredChineseVisualTerms = ["星云", "流场", "粒子轨迹", "引力源", "黑洞", "新生星云", "地形层"];

const requiredTerrainClasses = [
  "long_term_theme",
  "growth_band",
  "migration_flow",
  "relic",
  "black_hole",
  "opportunity",
];

const requiredChineseTerrainTerms = ["长期主题", "成长带", "迁移流", "遗迹", "黑洞", "机会"];

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase1.cjs",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${visualContractPath}`,
  `OpenAIDatabase/${terrainLayerPath}`,
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

function validateStage3Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage4_phase1_open_diff_scope",
      "Open diff is limited to Stage 4 Phase 4.1 visual contract files",
      "Unexpected files changed outside Stage 4 Phase 4.1 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage3_validator_registered_for_post_commit_run",
      "Stage 3 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 3 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage3_validator_deferred_until_clean_tree",
      "Stage 3 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S3-REVIEW",
    "stage3_validator",
    "Stage 3 validator returned PASS before Stage 4 Phase 4.1 acceptance",
    "Stage 3 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateProductContracts() {
  [visualContractPath, terrainLayerPath, acceptancePath, "config/visualization/model_parameters.universe_state.yaml"].forEach(
    validateTextFile,
  );

  const visual = readRepoFile(visualContractPath);
  const terrain = readRepoFile(terrainLayerPath);
  const acceptance = readRepoFile(acceptancePath);
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");

  assertCondition(
    hasAll(visual, [
      "Memory Starfield Visual Contract",
      visualContractVersion,
      terrainContractVersion,
      taskId,
      acceptanceId,
      status,
      validatorName,
      "video-grade visual acceptance",
      "not a plain node-link chart",
      "not an Obsidian-like graph",
      "C3 Starfield Spike",
      "rollback path",
      "No Phase 4.2",
      "No runtime renderer replacement",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage4_phase1_visual_contract_core",
    "Visual contract records version, status, acceptance, anti-regression rule, spike dependency and no-upload boundary",
    "Visual contract is missing required Stage 4 Phase 4.1 core tokens",
  );

  assertCondition(
    hasAll(visual, requiredVisualPrimitives) && hasAll(visual, requiredChineseVisualTerms),
    "stage4_phase1_visual_primitives",
    "Visual contract requires nebula, flow field, trails, gravity, black hole, proto-star and terrain terms",
    "Visual contract is missing required visual primitives",
    { requiredVisualPrimitives, requiredChineseVisualTerms },
  );

  assertCondition(
    hasAll(terrain, [
      "Memory Terrain Layer",
      terrainContractVersion,
      visualContractVersion,
      taskId,
      acceptanceId,
      status,
      validatorName,
      "terrain semantic registry",
      "Top 4 fallback",
      "No Phase 4.2",
      "No runtime renderer replacement",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage4_phase1_terrain_contract_core",
    "Terrain contract records version, visual-contract linkage, fallback and no-upload boundary",
    "Terrain contract is missing required Stage 4 Phase 4.1 core tokens",
  );

  assertCondition(
    hasAll(terrain, requiredTerrainClasses) && hasAll(terrain, requiredChineseTerrainTerms),
    "stage4_phase1_terrain_classes",
    "Terrain contract defines long-term theme, growth band, migration flow, relic, black hole and opportunity",
    "Terrain contract is missing required terrain classes",
    { requiredTerrainClasses, requiredChineseTerrainTerms },
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 4 Phase 4.1 Visual Contract Acceptance",
      visualContractVersion,
      terrainContractVersion,
      taskId,
      acceptanceId,
      status,
      validatorName,
      "video-grade visual acceptance",
      "nebula_field",
      "flow_field",
      "particle_trails",
      "gravity_sources",
      "black_hole_core",
      "proto_star_cloud",
      "memory_terrain_layer",
      "long_term_theme",
      "growth_band",
      "migration_flow",
      "relic",
      "opportunity",
      "C3 Starfield Spike",
      "No Phase 4.2",
      "No runtime renderer replacement",
      "No browser screenshot",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage4_phase1_acceptance_contract",
    "Acceptance document pins measurable visual primitives, terrain classes, spike handoff and boundaries",
    "Acceptance document is incomplete",
  );

  assertCondition(
    hasAll(params, [
      taskId,
      acceptanceId,
      status,
      visualContractVersion,
      terrainContractVersion,
      "stage4_phase1_required_visual_primitives",
      "stage4_phase1_required_terrain_classes",
      "stage4_phase1_forbidden_visual_regressions",
      "stage4_phase1_boundary",
    ]),
    "stage4_phase1_model_parameters",
    "Universe-state parameter template registers Stage 4 Phase 4.1 visual and terrain contracts",
    "Universe-state parameter template is missing Stage 4 Phase 4.1 entries",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase1.cjs",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage4_phase1.cjs",
    "stage4_phase1_package_script",
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
        visualContractVersion,
        terrainContractVersion,
        "Visual Contract Update",
        "No Phase 4.2",
        "No GitHub main upload",
      ]),
      `stage4_phase1_records_${name}`,
      `${name} registers Stage 4 Phase 4.1 status, acceptance, validator and no-upload boundary`,
      `${name} is missing Stage 4 Phase 4.1 records`,
    );
  }
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage4_phase1_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage4_phase1_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
}

function validateChangeScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage4_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 4 Phase 4.1 contracts, records, validator and package script",
    "Unexpected files changed outside Stage 4 Phase 4.1 scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const statusOutput = run("git", ["-c", "core.quotepath=false", "status", "--short"], { cwd: worktreeRoot }).stdout;
  const forbidden = [
    "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
    "OpenAIDatabase/apps/memory-atlas/src/styles.css",
    "OpenAIDatabase/apps/memory-atlas/src/components/",
    "OpenAIDatabase/apps/memory-atlas/src/experiments/",
    "OpenAIDatabase/data/raw/",
    "OpenAIDatabase/data/private/",
  ];
  const matches = forbidden.filter((fragment) => statusOutput.includes(fragment));
  assertCondition(
    matches.length === 0,
    "stage4_phase1_boundary",
    "No runtime UI/CSS/component/experiment/raw-private data change is present in this visual-contract phase",
    "Runtime UI, CSS, component, experiment or raw/private data changed during Stage 4 Phase 4.1",
    { matches },
  );
}

function main() {
  validateStage3Continuity();
  validateProductContracts();
  validateRecords();
  validateCanonicalBoundary();
  validateChangeScope();
  validateBoundary();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage4-phase1",
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
        stage: "v1.1.7-stage4-phase1",
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
