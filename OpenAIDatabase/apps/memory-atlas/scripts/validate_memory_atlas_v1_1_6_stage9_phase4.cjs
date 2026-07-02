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

function readJson(relativePath) {
  return JSON.parse(readRepoFile(relativePath));
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
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

function walkFiles(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkFiles(fullPath, files);
    } else {
      files.push(fullPath);
    }
  }
  return files;
}

function validateContracts() {
  const product = readRepoFile("docs/product/universe_state_fixture_continuity_contract.md");
  const acceptance = readRepoFile("docs/acceptance/universe_state_fixture_continuity_acceptance.md");
  assertCondition(
    hasAll(product, [
      "Memory Atlas Universe State Fixture Continuity 合同",
      "v1.1.6 Stage 9 Phase 4",
      "universe_state_fixture_continuity_contract",
      "MA-V116-S9P04",
      "phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review",
      "redacted_fixture_adapter",
      "deterministic_sample_generation",
      "schema_validation",
      "parameter_drift_gate",
      "black_hole_score",
      "proto_star_score",
      "stale_score",
      "memory_weather",
      "memory_terrain",
      "river_pulse",
      "mini_starfield",
      "consumer_map",
      "proposal_only_actions",
      "privacy_status",
      "validate:universe-state-spike",
      "No production integration",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ])
      && hasAll(acceptance, [
        "Memory Atlas Universe State Fixture Continuity 验收",
        "validate:v1.1.6-stage9-phase4",
        "validate:universe-state-spike",
        "raw_private_data_included: false",
        "plaintext_secrets_included: false",
        "local_absolute_paths_included: false",
        "writeback_allowed: false",
        "proposal_only: true",
        "memory_weather",
        "memory_terrain",
        "river_pulse",
        "mini_starfield",
        "consumer_map",
        "Production `src` files outside the experiment directory do not import or",
        "No Stage 9 review",
        "No Stage 10 work",
        "No GitHub main upload",
      ]),
    "stage9_phase4_contracts",
    "Stage 9 Phase 4 product and acceptance contracts define Universe State fixture continuity requirements and boundaries",
    "Stage 9 Phase 4 contracts are incomplete",
  );
}

function validateUniverseStateSpikeGate() {
  const result = run(process.execPath, ["--experimental-strip-types", "scripts/validate_universe_state_spike.mjs"], {
    cwd: appRoot,
  });
  const output = JSON.parse(result.stdout);
  assertCondition(
    output.ok === true
      && output.weather === "black_hole_warning"
      && output.black_hole_count >= 1
      && output.proto_star_count >= 1
      && output.privacy_status
      && output.privacy_status.raw_private_data_included === false
      && output.privacy_status.plaintext_secrets_included === false
      && output.privacy_status.local_absolute_paths_included === false
      && output.privacy_status.writeback_allowed === false,
    "stage9_phase4_existing_universe_validator",
    "validate_universe_state_spike confirms deterministic sample, schema, score, parameter and privacy gates",
    "validate_universe_state_spike output did not prove required continuity gates",
    { output },
  );
}

function validateUniverseFiles() {
  const requiredFiles = [
    "apps/memory-atlas/src/experiments/universe-state-generator-spike/README.md",
    "apps/memory-atlas/src/models/universeState.ts",
    "apps/memory-atlas/src/utils/universeStateScores.ts",
    "apps/memory-atlas/src/fixtures/universe_state.input.fixture.json",
    "apps/memory-atlas/src/fixtures/universe_state.sample.json",
    "apps/memory-atlas/src/fixtures/universe_state.schema.json",
    "apps/memory-atlas/scripts/validate_universe_state_spike.mjs",
    "config/visualization/model_parameters.universe_state.yaml",
  ];
  const missing = requiredFiles.filter((file) => !fs.existsSync(path.join(repoRoot, file)));
  assertCondition(
    missing.length === 0,
    "stage9_phase4_universe_files",
    "Universe State README, model, scores, fixture, sample, schema, params and validator files exist",
    "Universe State continuity is missing required files",
    { missing },
  );

  const readme = readRepoFile("apps/memory-atlas/src/experiments/universe-state-generator-spike/README.md");
  const model = readRepoFile("apps/memory-atlas/src/models/universeState.ts");
  const scores = readRepoFile("apps/memory-atlas/src/utils/universeStateScores.ts");
  const schema = readRepoFile("apps/memory-atlas/src/fixtures/universe_state.schema.json");
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");
  const validator = readRepoFile("apps/memory-atlas/scripts/validate_universe_state_spike.mjs");
  const input = readJson("apps/memory-atlas/src/fixtures/universe_state.input.fixture.json");
  const sample = readJson("apps/memory-atlas/src/fixtures/universe_state.sample.json");

  assertCondition(
    hasAll(readme, [
      "v1.1.6 Stage 9 Phase 4 Continuity",
      "MA-V116-S9P04",
      "universe_state_fixture_continuity_contract",
      "validate:v1.1.6-stage9-phase4",
      "validate:universe-state-spike",
      "No production integration",
      "No GitHub main upload",
    ]),
    "stage9_phase4_readme_continuity",
    "Universe State spike README records v1.1.6 Stage 9 Phase 4 continuity and no-upload boundary",
    "Universe State spike README is missing v1.1.6 Stage 9 Phase 4 continuity",
  );

  assertCondition(
    hasAll(model, [
      "RedactedUniverseStateInput",
      "UniverseStateSnapshot",
      "generateUniverseStateSnapshot",
      "assertSafeSource",
      "memory_weather",
      "dominant_clusters",
      "rising_clusters",
      "declining_clusters",
      "conflict_zones",
      "black_holes",
      "proto_stars",
      "stale_orbits",
      "memory_terrain",
      "river_pulse",
      "mini_starfield",
      "consumer_map",
      "proposal_only: true",
    ])
      && hasAll(scores, [
        "DEFAULT_UNIVERSE_STATE_PARAMETERS",
        "parameterSource: \"OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml\"",
        "blackHoleScore",
        "protoStarScore",
        "staleScore",
        "selectWeatherLabel",
      ]),
    "stage9_phase4_source_contract",
    "Universe State source keeps redacted input, snapshot, consumer fields, proposal-only actions and parameter-backed score functions",
    "Universe State model or score source is missing required continuity anchors",
  );

  assertCondition(
    input.schema_version === "memory_atlas_universe_state_fixture.v1"
      && input.redaction_mode === "public_redacted_read_only_visualization"
      && input.source_safety.raw_private_data_included === false
      && input.source_safety.plaintext_secrets_included === false
      && input.source_safety.local_absolute_paths_included === false
      && input.source_safety.writeback_allowed === false
      && Array.isArray(input.clusters)
      && input.clusters.length >= 5
      && Array.isArray(input.black_hole_candidates)
      && input.black_hole_candidates.length >= 1
      && Array.isArray(input.proto_star_candidates)
      && input.proto_star_candidates.length >= 1,
    "stage9_phase4_input_fixture",
    "Universe State input fixture is redacted, safe and contains clusters, Black Hole and Proto-Star candidates",
    "Universe State input fixture does not meet continuity requirements",
    { source_safety: input.source_safety },
  );

  const state = sample.state || {};
  const privacy = sample.diagnostics?.privacy_status || {};
  const consumerMap = sample.consumer_map || {};
  const actions = Array.isArray(state.recommended_next_actions) ? state.recommended_next_actions : [];
  assertCondition(
    sample.schema_version === "universe_state_snapshot.v1"
      && state.memory_weather
      && Array.isArray(state.dominant_clusters)
      && Array.isArray(state.rising_clusters)
      && Array.isArray(state.declining_clusters)
      && Array.isArray(state.conflict_zones)
      && Array.isArray(state.black_holes)
      && Array.isArray(state.proto_stars)
      && Array.isArray(state.stale_orbits)
      && Array.isArray(state.memory_terrain)
      && state.river_pulse
      && state.mini_starfield
      && actions.length >= 1
      && actions.every((action) => action.proposal_only === true)
      && ["memory_overview", "memory_starfield", "memory_river", "inspector", "roi_dashboard"].every((key) => Array.isArray(consumerMap[key]))
      && privacy.raw_private_data_included === false
      && privacy.plaintext_secrets_included === false
      && privacy.local_absolute_paths_included === false
      && privacy.writeback_allowed === false,
    "stage9_phase4_sample_snapshot",
    "Universe State sample exposes weather, clusters, Black Hole, Proto-Star, stale, terrain, river, starfield, consumer map and all-false privacy flags",
    "Universe State sample does not meet continuity requirements",
    { privacy, consumerMapKeys: Object.keys(consumerMap) },
  );

  assertCondition(
    hasAll(schema, [
      "universe_state_snapshot.v1",
      "memory_weather",
      "dominant_clusters",
      "rising_clusters",
      "declining_clusters",
      "conflict_zones",
      "black_holes",
      "proto_stars",
      "stale_orbits",
      "memory_terrain",
      "river_pulse",
      "mini_starfield",
      "consumer_map",
      "diagnostics",
    ])
      && hasAll(params, [
        "schema_version: universe_state_params.v1",
        "raw_private_data_allowed: false",
        "plaintext_secrets_allowed: false",
        "local_absolute_paths_allowed: false",
        "writeback_allowed: false",
        "black_hole:",
        "proto_star:",
        "stale:",
      ])
      && hasAll(validator, [
        "validateGeneratedMatchesSample",
        "validateParameterDrift",
        "validatePrivacy",
        "unitTestAdapter",
        "unitTestScoreFunctions",
      ]),
    "stage9_phase4_schema_params_validator",
    "Universe State schema, parameter YAML and validator preserve required continuity gates",
    "Universe State schema, params or validator are missing required continuity anchors",
  );
}

function validateProductionIsolation() {
  const srcRoot = path.join(repoRoot, "apps/memory-atlas/src");
  const experimentDir = path.join(srcRoot, "experiments/universe-state-generator-spike");
  const productionFiles = walkFiles(srcRoot)
    .filter((file) => !file.startsWith(experimentDir))
    .filter((file) => /\.(?:ts|tsx|js|jsx|mjs|cjs)$/.test(file));
  const references = productionFiles
    .map((file) => ({ file, source: fs.readFileSync(file, "utf8") }))
    .filter(({ source }) => source.includes("experiments/universe-state-generator-spike") || source.includes("Universe State Generator Spike"))
    .map(({ file }) => path.relative(repoRoot, file));

  assertCondition(
    references.length === 0,
    "stage9_phase4_production_isolation",
    "Production src files outside the experiment do not import or reference universe-state-generator-spike",
    "Production code references the Universe State generator experiment",
    { references },
  );
}

function validateRecords() {
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const featureList = readRepoFile("功能清单.md");
  const development = readRepoFile("开发记录.md");
  const modelIndex = readRepoFile("模型参数文件.md");
  const changelog = readRepoFile("CHANGELOG.md");
  const packageJson = readRepoFile("apps/memory-atlas/package.json");

  assertCondition(
    hasAll(delivery, [
      "Stage 9 Phase 4：Universe State Fixture Continuity",
      "phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review",
      "MA-V116-S9P04",
      "validate:v1.1.6-stage9-phase4",
      "validate:universe-state-spike",
      "No production integration",
      "No GitHub main upload",
    ]),
    "delivery_record_stage9_phase4",
    "Delivery record captures Stage 9 Phase 4 scope, validators, status and no-upload boundary",
    "Delivery record is missing Stage 9 Phase 4 details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 9 Phase 4 Universe State Fixture Continuity 参数",
      "PARAM-MA-V116-S9P04-001 stage9_phase4_contract_id",
      "PARAM-MA-V116-S9P04-002 stage9_phase4_fixture_surface",
      "PARAM-MA-V116-S9P04-003 stage9_phase4_required_features",
      "PARAM-MA-V116-S9P04-004 stage9_phase4_fixture_safety",
      "PARAM-MA-V116-S9P04-005 stage9_phase4_isolation_boundary",
      "PARAM-MA-V116-S9P04-006 stage9_phase4_required_validator",
    ]),
    "model_parameters_stage9_phase4",
    "Model parameters document Stage 9 Phase 4 fixture surface, features, safety, isolation and validator",
    "Model parameters are missing Stage 9 Phase 4 details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S9P04",
      "Memory Atlas v1.1.6 Stage 9 Phase 4",
      "EVID-MA-V116-S9P04-UNIVERSE-STATE-CONTRACT",
      "EVID-MA-V116-S9P04-UNIVERSE-STATE-ACCEPTANCE",
      "validate:v1.1.6-stage9-phase4",
    ]),
    "feature_list_stage9_phase4",
    "Feature list registers Stage 9 Phase 4 feature, evidence and validation",
    "Feature list is missing Stage 9 Phase 4 details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage9_phase04",
      "MA-V116-S9：C3 隔离原型",
      "MA-V116-S9P04 Universe State Fixture Continuity",
      "phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review",
      "validate:v1.1.6-stage9-phase4",
    ]),
    "development_record_stage9_phase4",
    "Development record captures Stage 9 Phase 4 objective, tasks, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 9 Phase 4 details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S9P04",
      "Universe State Fixture Continuity",
      "phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review",
      "validate:v1.1.6-stage9-phase4",
      "universe_state_fixture_continuity_no_production_import",
    ]),
    "model_index_stage9_phase4",
    "Root model parameter file records Stage 9 Phase 4 model and parameters",
    "Root model parameter file is missing Stage 9 Phase 4 details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 9 Phase 4",
      "universe_state_fixture_continuity_contract.md",
      "universe_state_fixture_continuity_acceptance.md",
      "validate:v1.1.6-stage9-phase4",
      "validate:universe-state-spike",
      "phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review",
      "No production integration",
      "No GitHub main upload",
    ]),
    "changelog_stage9_phase4",
    "Changelog records Stage 9 Phase 4 deliverables and non-goal boundaries",
    "Changelog is missing Stage 9 Phase 4 details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage9-phase4"')
      && packageJson.includes('"validate:universe-state-spike"'),
    "package_script_stage9_phase4",
    "Package script exposes validate:v1.1.6-stage9-phase4 and existing Universe State validator",
    "Package script is missing validate:v1.1.6-stage9-phase4 or validate:universe-state-spike",
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotePath=false", "status", "--short", "--untracked-files=all", "--", "OpenAIDatabase"], { cwd: worktreeRoot });
  const changed = result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3))
    .map((line) => line.replace(/^OpenAIDatabase\//, ""))
    .map((line) => line.replace(/^\"(.+)\"$/, "$1"))
    .filter(Boolean);

  const allowed = [
    "CHANGELOG.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase4.cjs",
    "apps/memory-atlas/src/experiments/universe-state-generator-spike/README.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/universe_state_fixture_continuity_acceptance.md",
    "docs/product/universe_state_fixture_continuity_contract.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage9_phase4_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 9 Phase 4 continuity docs, records, README, validator and package script",
    "Stage 9 Phase 4 contains out-of-scope OpenAIDatabase changes",
    { changed, outside },
  );
}

function validateBoundary() {
  const status = run("git", ["-c", "core.quotePath=false", "status", "--short"], { cwd: worktreeRoot }).stdout;
  const touchedRuntime = status
    .split("\n")
    .filter((line) => (
      line.includes("OpenAIDatabase/apps/memory-atlas/src/App.tsx")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/main.tsx")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/components/")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/styles")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/models/universeState.ts")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/utils/universeStateScores.ts")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/fixtures/universe_state")
        || line.includes("OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml")
        || line.includes("OpenAIDatabase/apps/memory-atlas/dist/")
        || line.includes("OpenAIDatabase/apps/memory-atlas/build/")
        || line.includes("OpenAIDatabase/data/raw/")
        || line.includes("OpenAIDatabase/data/private/")
        || line.includes(".app")
    ));

  assertCondition(
    touchedRuntime.length === 0,
    "stage9_phase4_boundary",
    "No production runtime UI/CSS/build/app/data/writeback/deploy or Universe State model/sample/parameter change is present in this continuity phase",
    "Production runtime UI, CSS, build, app bundle, data, writeback, deploy artifact or Universe State model/sample/parameter changed during Stage 9 Phase 4",
    { touchedRuntime },
  );
}

function main() {
  try {
    [
      "docs/product/universe_state_fixture_continuity_contract.md",
      "docs/acceptance/universe_state_fixture_continuity_acceptance.md",
      "apps/memory-atlas/src/experiments/universe-state-generator-spike/README.md",
      "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
      "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
      "功能清单.md",
      "开发记录.md",
      "模型参数文件.md",
      "CHANGELOG.md",
    ].forEach(validateTextFile);
    validateContracts();
    validateUniverseStateSpikeGate();
    validateUniverseFiles();
    validateProductionIsolation();
    validateRecords();
    validateChangeScope();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage9-phase4", checks }, null, 2));
  } catch (error) {
    checks.push({ name: "failure", status: "FAIL", evidence: error.message, details: error.details || {} });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage9-phase4", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
