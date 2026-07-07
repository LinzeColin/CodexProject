#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const checks = [];
const starfieldFixtureSchemaVersions = new Set([
  "memory_starfield_spike_fixture.v1",
  "memory_starfield_spike_fixture.v1_1_7_stage4_phase2",
]);
const riverFixtureSchemaVersions = new Set([
  "memory_river_spike_fixture.v1",
  "memory_river_spike_fixture.v1_1_7_stage5_phase2",
]);

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

function readAppFile(relativePath) {
  return fs.readFileSync(path.join(appRoot, relativePath), "utf8");
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || appRoot,
    env: options.env || process.env,
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

function parseJsonOutput(stdout) {
  const trimmed = stdout.trim();
  const firstBrace = trimmed.indexOf("{");
  const lastBrace = trimmed.lastIndexOf("}");
  if (firstBrace < 0 || lastBrace < firstBrace) return null;
  return JSON.parse(trimmed.slice(firstBrace, lastBrace + 1));
}

function importFixture(relativePath, exportName, expression) {
  const script = `
    import { ${exportName} } from "./${relativePath}";
    const value = (${expression})(${exportName});
    console.log(JSON.stringify(value));
  `;
  const result = run(process.execPath, ["--experimental-strip-types", "--input-type=module", "-e", script], {
    cwd: appRoot,
  });
  return JSON.parse(result.stdout);
}

function walkFiles(rootDir, skipNames = new Set()) {
  const result = [];
  for (const entry of fs.readdirSync(rootDir, { withFileTypes: true })) {
    if (skipNames.has(entry.name)) continue;
    const fullPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      result.push(...walkFiles(fullPath, skipNames));
    } else {
      result.push(fullPath);
    }
  }
  return result;
}

function validateStarfieldSpike() {
  const readme = readAppFile("src/experiments/memory-starfield-spike/README.md");
  const main = readAppFile("src/experiments/memory-starfield-spike/main.ts");
  const index = readAppFile("src/experiments/memory-starfield-spike/index.html");
  const fixtureSummary = importFixture(
    "src/experiments/memory-starfield-spike/fixture.ts",
    "memoryStarfieldFixture",
    `(fixture) => ({
      schemaVersion: fixture.schemaVersion,
      safety: {
        rawPrivateDataIncluded: fixture.rawPrivateDataIncluded,
        plaintextSecretsIncluded: fixture.plaintextSecretsIncluded,
        localAbsolutePathsIncluded: fixture.localAbsolutePathsIncluded,
      },
      kinds: [...new Set(fixture.clusters.map((cluster) => cluster.kind))].sort(),
      clusterCount: fixture.clusters.length,
      minEvidenceCount: Math.min(...fixture.clusters.map((cluster) => cluster.evidenceCount)),
    })`,
  );

  assertCondition(
    starfieldFixtureSchemaVersions.has(fixtureSummary.schemaVersion)
      && fixtureSummary.clusterCount >= 8
      && fixtureSummary.minEvidenceCount > 0
      && ["black_hole", "declining", "dominant", "proto_star", "rising", "terrain"].every((kind) => fixtureSummary.kinds.includes(kind))
      && fixtureSummary.safety.rawPrivateDataIncluded === false
      && fixtureSummary.safety.plaintextSecretsIncluded === false
      && fixtureSummary.safety.localAbsolutePathsIncluded === false,
    "part2_phase_1_1_starfield_fixture",
    "Memory Starfield fixture imports successfully with required semantic kinds and false safety flags",
    "Memory Starfield fixture is incomplete or unsafe",
    { ...fixtureSummary, allowedSchemaVersions: [...starfieldFixtureSchemaVersions] },
  );
  assertCondition(
    hasAll(readme, [
      "Task 1.1 记忆星系 Spike",
      "isolated runnable spike",
      "deep-space",
      "Flow Field",
      "gravitational disk",
      "Black Hole",
      "Proto-Star",
      "Memory Terrain",
      "reduced-motion",
      "The production app does not import this directory",
      "raw/private/session/cookie/secret",
      "## Rollback",
    ]),
    "part2_phase_1_1_starfield_readme",
    "Memory Starfield README preserves goal, isolation, semantic visual layers, acceptance, safety boundary, and rollback",
    "Memory Starfield README lacks required Part 2 evidence",
  );
  assertCondition(
    hasAll(main, [
      "import * as THREE from \"three\"",
      "high: 12000",
      "mid: 10000",
      "low: 8000",
      "createGravitationalDisk",
      "createNebulaDust",
      "updateParticles",
      "reducedMotionControl",
      "raycaster",
      "__memoryStarfieldSpike",
      "smoke",
    ]) && hasAll(index, [
      "qualityControl",
      "flowControl",
      "reducedMotionControl",
      "hoverCard",
      "smokeStatus",
    ]),
    "part2_phase_1_1_starfield_runtime_contract",
    "Memory Starfield runtime exposes Three.js canvas, 10k default particle path, LOD, flow, reduced motion, hover and smoke instrumentation",
    "Memory Starfield runtime contract is incomplete",
  );
}

function validateRiverSpike() {
  const readme = readAppFile("src/experiments/memory-river-spike/README.md");
  const main = readAppFile("src/experiments/memory-river-spike/main.ts");
  const index = readAppFile("src/experiments/memory-river-spike/index.html");
  const fixtureSummary = importFixture(
    "src/experiments/memory-river-spike/fixture.ts",
    "memoryRiverFixture",
    `(fixture) => ({
      schemaVersion: fixture.schemaVersion,
      safety: {
        rawPrivateDataIncluded: fixture.rawPrivateDataIncluded,
        plaintextSecretsIncluded: fixture.plaintextSecretsIncluded,
        localAbsolutePathsIncluded: fixture.localAbsolutePathsIncluded,
        writebackAllowed: fixture.writebackAllowed,
      },
      laneCount: fixture.lanes.length,
      eventCount: fixture.events.length,
      blackHoleBandCount: fixture.blackHoleBands.length,
      protoStarCount: fixture.protoStars.length,
      laneLevels: [...new Set(fixture.lanes.map((lane) => lane.level))].sort(),
    })`,
  );

  assertCondition(
    riverFixtureSchemaVersions.has(fixtureSummary.schemaVersion)
      && fixtureSummary.laneCount >= 5
      && fixtureSummary.eventCount >= 9
      && fixtureSummary.blackHoleBandCount >= 1
      && fixtureSummary.protoStarCount >= 1
      && ["macro", "meso", "micro"].every((level) => fixtureSummary.laneLevels.includes(level))
      && fixtureSummary.safety.rawPrivateDataIncluded === false
      && fixtureSummary.safety.plaintextSecretsIncluded === false
      && fixtureSummary.safety.localAbsolutePathsIncluded === false
      && fixtureSummary.safety.writebackAllowed === false,
    "part2_phase_1_2_river_fixture",
    "Memory River fixture imports successfully with macro/meso/micro lanes, events, risk/opportunity signals and false safety flags",
    "Memory River fixture is incomplete or unsafe",
    { ...fixtureSummary, allowedSchemaVersions: [...riverFixtureSchemaVersions] },
  );
  assertCondition(
    hasAll(readme, [
      "Task 1.2 记忆时间河 Spike",
      "isolated runnable spike",
      "dynamic time river",
      "D3 time scale",
      "zoom",
      "brush",
      "theme lanes",
      "Black Hole",
      "Proto-Star",
      "pseudo-haptic",
      "reduced motion",
      "The production app does not import this directory",
      "raw/private/session/cookie/secret",
      "writeback",
      "## Rollback",
    ]),
    "part2_phase_1_2_river_readme",
    "Memory River README preserves goal, isolation, interaction model, acceptance, safety/writeback boundary, and rollback",
    "Memory River README lacks required Part 2 evidence",
  );
  assertCondition(
    hasAll(main, [
      "import * as d3 from \"d3\"",
      "d3.scaleUtc",
      "d3.zoom",
      "brushX",
      "blackHoleBands",
      "protoStars",
      "reducedMotionControl",
      "pulseFeedback",
      "__memoryRiverSpike",
      "smoke",
    ]) && hasAll(index, [
      "modeControl",
      "reducedMotionControl",
      "resetButton",
      "hoverCard",
      "smokeStatus",
    ]),
    "part2_phase_1_2_river_runtime_contract",
    "Memory River runtime exposes D3 UTC scale, zoom, brush, lanes, risk/opportunity signals, feedback, reduced motion and smoke instrumentation",
    "Memory River runtime contract is incomplete",
  );
}

function validateUniverseStateSpike() {
  const validatorResult = run(process.execPath, ["--experimental-strip-types", "scripts/validate_universe_state_spike.mjs"], {
    cwd: appRoot,
  });
  const parsed = parseJsonOutput(validatorResult.stdout);
  assertCondition(
    parsed?.ok === true
      && parsed.weather === "black_hole_warning"
      && parsed.dominant_count >= 3
      && parsed.rising_count >= 3
      && parsed.declining_count >= 1
      && parsed.conflict_count >= 1
      && parsed.black_hole_count >= 1
      && parsed.proto_star_count >= 2
      && parsed.stale_count >= 1
      && parsed.parameter_source === "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml"
      && parsed.privacy_status?.raw_private_data_included === false
      && parsed.privacy_status?.plaintext_secrets_included === false
      && parsed.privacy_status?.local_absolute_paths_included === false
      && parsed.privacy_status?.writeback_allowed === false,
    "part2_phase_1_3_universe_state_validator",
    "Universe State validator passed with required counts, parameter source and false privacy/writeback flags",
    "Universe State validator output does not prove Part 2 acceptance",
    parsed || { stdout: validatorResult.stdout },
  );

  const readme = readAppFile("src/experiments/universe-state-generator-spike/README.md");
  const model = readAppFile("src/models/universeState.ts");
  const scores = readAppFile("src/utils/universeStateScores.ts");
  const sample = JSON.parse(readAppFile("src/fixtures/universe_state.sample.json"));
  const schema = JSON.parse(readAppFile("src/fixtures/universe_state.schema.json"));

  assertCondition(
    hasAll(readme, [
      "Task 1.3 Universe State Generator Spike",
      "isolated generator spike",
      "Adapter unit check",
      "Score unit checks",
      "Sample JSON",
      "Score formulas trace to the parameter YAML",
      "Production app does not import the spike",
      "proposal_only=true",
      "## Rollback",
    ]),
    "part2_phase_1_3_universe_readme",
    "Universe State README preserves isolated generator, adapter, scoring, sample/schema, YAML trace, proposal-only and rollback evidence",
    "Universe State README lacks required Part 2 evidence",
  );
  assertCondition(
    hasAll(model, [
      "adaptUniverseStateFixture",
      "generateUniverseStateSnapshot",
      "assertSafeSource",
      "buildMemoryWeather",
      "buildMemoryTerrain",
      "buildNextActions",
      "proposal_only: true",
      "consumer_map",
      "privacy_status",
    ]) && hasAll(scores, [
      "blackHoleScore",
      "protoStarScore",
      "staleScore",
      "selectWeatherLabel",
      "assertWeightGroups",
      "parameterSource: \"OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml\"",
    ]),
    "part2_phase_1_3_universe_source_contract",
    "Universe State source exposes adapter, deterministic generator, safe-source gate, score functions, consumer map and proposal-only actions",
    "Universe State source contract is incomplete",
  );
  assertCondition(
    sample.schema_version === "universe_state_snapshot.v1"
      && sample.state?.recommended_next_actions?.every((action) => action.proposal_only === true)
      && sample.diagnostics?.score_weight_sums?.every((group) => Math.abs(group.sum - 1) < 0.0001)
      && schema.required?.includes("source_snapshot")
      && schema.properties?.state?.required?.includes("recommended_next_actions"),
    "part2_phase_1_3_universe_sample_schema",
    "Universe State sample and schema preserve snapshot v1, proposal-only actions, normalized weight groups and required state fields",
    "Universe State sample/schema contract is incomplete",
  );
}

function validateProductionIsolation() {
  const productionFiles = walkFiles(path.join(appRoot, "src"), new Set(["experiments", "node_modules"]));
  const offendingRefs = [];
  const forbidden = [
    "memory-starfield-spike",
    "memory-river-spike",
    "universe-state-generator-spike",
    "universe_state.input.fixture",
  ];
  const allowedPromotedRuntimeRefs = [
    "src/models/universeState.ts",
    "src/utils/universeStateScores.ts",
    "src/fixtures/universe_state.sample.json",
  ];
  for (const filePath of productionFiles) {
    const relative = path.relative(appRoot, filePath);
    if (
      relative === "src/models/universeState.ts"
      || relative === "src/utils/universeStateScores.ts"
      || relative.startsWith("src/fixtures/universe_state.")
    ) {
      continue;
    }
    const source = fs.readFileSync(filePath, "utf8");
    for (const needle of forbidden) {
      if (source.includes(needle)) offendingRefs.push(`${path.relative(repoRoot, filePath)} -> ${needle}`);
    }
  }
  assertCondition(
    offendingRefs.length === 0,
    "part2_production_isolation",
    "Production src files do not import or reference isolated Stage 1 spike/generator workspaces",
    "Production source references isolated Stage 1 spikes or generator",
    { offendingRefs, allowedPromotedRuntimeRefs },
  );
}

function validateDocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part2_stage1_review.md");
  const stage1Review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage1_review.md");

  assertCondition(
    packageSource.includes('"validate:part2-stage1": "node scripts/validate_memory_atlas_part2_stage1.cjs"'),
    "part2_package_script_current",
    "Package scripts expose validate:part2-stage1",
    "Package script validate:part2-stage1 is missing",
  );
  assertCondition(
    hasAll(stage1Review, [
      "Task 1.1 Memory Starfield Spike",
      "Task 1.2 Memory River Spike",
      "Task 1.3 Universe State Generator Spike",
      "validate:universe-state-spike",
      "Production app code does not reference the isolated visual spike directories",
      "Production app code does not reference the Universe State generator spike",
    ]),
    "part2_stage1_review_source_current",
    "Existing Stage 1 review records all three Part 2 phases and production-isolation evidence",
    "Existing Stage 1 review does not cover all Part 2 phases",
  );
  assertCondition(
    hasAll(review, [
      "Part 2 is review-passed",
      "Phase 1.1",
      "Phase 1.2",
      "Phase 1.3",
      "validate:part2-stage1",
      "validate:universe-state-spike",
      "No Part 3 review",
      "No GitHub main upload",
      "No production React/Three/D3 integration was changed",
      "No raw/private/cookie/session/secret",
    ]),
    "part2_review_doc_current",
    "Part 2 review doc records phase coverage, validators, boundaries and upload non-goal",
    "Part 2 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 2 Stage 1 Review",
      "`validate:part2-stage1`",
      "Phase 1.1 / 1.2 / 1.3",
      "No Part 3 review",
      "No GitHub main upload",
    ]),
    "part2_changelog_current",
    "Changelog records Part 2 review, validator, phase coverage and non-goals",
    "Changelog does not record Part 2 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 2 复审",
      "Phase 1.1 / 1.2 / 1.3",
      "validate:part2-stage1",
      "未进入 Part 3",
      "未上传 GitHub main",
    ]),
    "part2_delivery_record_current",
    "Delivery record records Part 2 review status and next boundary",
    "Delivery record does not record Part 2 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 23. Part 2 Stage 1 复审门槛",
      "状态：`part_2_stage_1_review_passed`",
      "validate:part2-stage1",
      "Phase 1.1 Memory Starfield Spike",
      "Phase 1.2 Memory River Spike",
      "Phase 1.3 Universe State Generator Spike",
      "不进入 Part 3",
    ]),
    "part2_model_parameters_current",
    "Model parameters record Part 2 review gate, validator, phase coverage and non-goals",
    "Model parameters do not record Part 2 review gate",
  );
}

function validateBuild() {
  const tsc = path.join(appRoot, "node_modules/typescript/bin/tsc");
  const vite = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(
    fs.existsSync(tsc) && fs.existsSync(vite),
    "part2_dependencies_ready",
    "TypeScript and Vite CLIs are available in node_modules",
    "TypeScript or Vite CLI missing from app node_modules",
  );
  run(process.execPath, [tsc, "-b", "--pretty", "false"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "part2_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
}

try {
  validateStarfieldSpike();
  validateRiverSpike();
  validateUniverseStateSpike();
  validateProductionIsolation();
  validateBuild();
  validateDocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "2", phases: ["1.1", "1.2", "1.3"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part2_stage1_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "2", phases: ["1.1", "1.2", "1.3"], checks }, null, 2));
  process.exit(1);
}
