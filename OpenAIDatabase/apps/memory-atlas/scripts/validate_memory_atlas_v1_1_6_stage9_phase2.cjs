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
  const product = readRepoFile("docs/product/memory_river_c3_spike_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_river_c3_spike_acceptance.md");
  assertCondition(
    hasAll(product, [
      "Memory Atlas 记忆时间河 C3 隔离原型合同",
      "v1.1.6 Stage 9 Phase 2",
      "memory_river_c3_spike_contract",
      "MA-V116-S9P02",
      "phase_9_2_memory_river_c3_spike_ready_pending_stage_review",
      "d3_time_scale",
      "zoom_pan",
      "brush_selection",
      "theme_lanes",
      "black_hole_band",
      "proto_star_marker",
      "event_pulses",
      "hover_card",
      "reduced_motion",
      "smoke_status_hook",
      "No production integration",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ])
      && hasAll(acceptance, [
        "Memory Atlas 记忆时间河 C3 隔离原型验收",
        "validate:v1.1.6-stage9-phase2",
        "d3.scaleUtc",
        "d3.zoom",
        "d3.brushX",
        "rawPrivateDataIncluded: false",
        "plaintextSecretsIncluded: false",
        "localAbsolutePathsIncluded: false",
        "writebackAllowed: false",
        "Production `src` files outside the experiment directory do not import or",
        "No Stage 9 review",
        "No Stage 10 work",
        "No GitHub main upload",
      ]),
    "stage9_phase2_contracts",
    "Stage 9 Phase 2 product and acceptance contracts define Memory River C3 spike requirements and boundaries",
    "Stage 9 Phase 2 contracts are incomplete",
  );
}

function validateSpikeFiles() {
  const base = "apps/memory-atlas/src/experiments/memory-river-spike";
  const requiredFiles = ["README.md", "index.html", "main.ts", "fixture.ts"];
  const missing = requiredFiles.filter((file) => !fs.existsSync(path.join(repoRoot, base, file)));
  assertCondition(
    missing.length === 0,
    "stage9_phase2_spike_files",
    "Memory River spike has README, index, main and fixture files",
    "Memory River spike is missing required files",
    { missing },
  );

  const readme = readRepoFile(`${base}/README.md`);
  const main = readRepoFile(`${base}/main.ts`);
  const fixture = readRepoFile(`${base}/fixture.ts`);

  assertCondition(
    hasAll(readme, [
      "v1.1.6 Stage 9 Phase 2 Continuity",
      "MA-V116-S9P02",
      "validate:v1.1.6-stage9-phase2",
      "No production integration",
      "No GitHub main upload",
    ]),
    "stage9_phase2_spike_readme",
    "Memory River spike README records v1.1.6 Stage 9 Phase 2 continuity and boundary",
    "Memory River spike README is missing v1.1.6 Stage 9 Phase 2 continuity",
  );

  assertCondition(
    hasAll(main, [
      "import * as d3 from \"d3\"",
      "__memoryRiverSpike",
      "d3.scaleUtc",
      "d3.zoom",
      ".brushX<unknown>()",
      "\"data-layer\", \"theme-lanes\"",
      "\"data-layer\", \"black-hole-band\"",
      "drawProtoStars",
      "drawEvents",
      "hoverCard",
      "reducedMotionControl",
      "smokeStatus",
      "selectionCrossesSignal",
    ]),
    "stage9_phase2_spike_main",
    "Memory River spike main source exposes D3 scale, zoom, brush, lanes, Black Hole, Proto-Star, events, hover, reduced-motion and smoke hooks",
    "Memory River spike main source is missing required prototype behavior",
  );

  assertCondition(
    hasAll(fixture, [
      "schemaVersion: \"memory_river_spike_fixture.v1\"",
      "rawPrivateDataIncluded: false",
      "plaintextSecretsIncluded: false",
      "localAbsolutePathsIncluded: false",
      "writebackAllowed: false",
      "lanes: [",
      "events: [",
      "blackHoleBands: [",
      "protoStars: [",
      "kind: \"decision\"",
      "sourceScope: \"redacted_summary\"",
    ]),
    "stage9_phase2_spike_fixture",
    "Memory River fixture has redacted flags and required lanes, events, Black Hole bands and Proto-Star markers",
    "Memory River fixture is missing required redacted flags or prototype fixture structures",
  );

  const forbiddenFixturePatterns = [
    /sk-[A-Za-z0-9_-]{12,}/,
    /BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY/,
    /\/Users\/[A-Za-z0-9._-]+\/(?!Documents\/Codex)/,
    /raw transcript/i,
    /cookie[:=]/i,
    /session[:=]/i,
  ];
  const forbidden = forbiddenFixturePatterns
    .map((pattern) => pattern.toString())
    .filter((_, index) => forbiddenFixturePatterns[index].test(fixture));
  assertCondition(
    forbidden.length === 0,
    "stage9_phase2_fixture_privacy",
    "Memory River fixture does not expose obvious secrets, raw transcript wording or local private paths",
    "Memory River fixture contains forbidden private payload markers",
    { forbidden },
  );
}

function validateProductionIsolation() {
  const srcRoot = path.join(repoRoot, "apps/memory-atlas/src");
  const experimentDir = path.join(srcRoot, "experiments/memory-river-spike");
  const productionFiles = walkFiles(srcRoot)
    .filter((file) => !file.startsWith(experimentDir))
    .filter((file) => /\.(?:ts|tsx|js|jsx|mjs|cjs)$/.test(file));
  const references = productionFiles
    .map((file) => ({ file, source: fs.readFileSync(file, "utf8") }))
    .filter(({ source }) => source.includes("memory-river-spike") || source.includes("Memory River Spike"))
    .map(({ file }) => path.relative(repoRoot, file));

  assertCondition(
    references.length === 0,
    "stage9_phase2_production_isolation",
    "Production src files outside the experiment do not import or reference memory-river-spike",
    "Production code references the Memory River experiment",
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
      "Stage 9 Phase 2：Memory River C3 Spike",
      "phase_9_2_memory_river_c3_spike_ready_pending_stage_review",
      "MA-V116-S9P02",
      "validate:v1.1.6-stage9-phase2",
      "No production integration",
      "No GitHub main upload",
    ]),
    "delivery_record_stage9_phase2",
    "Delivery record captures Stage 9 Phase 2 scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 9 Phase 2 details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 9 Phase 2 记忆时间河 C3 隔离原型参数",
      "PARAM-MA-V116-S9P02-001 stage9_phase2_contract_id",
      "PARAM-MA-V116-S9P02-002 stage9_phase2_spike_path",
      "PARAM-MA-V116-S9P02-003 stage9_phase2_required_features",
      "PARAM-MA-V116-S9P02-004 stage9_phase2_fixture_safety",
      "PARAM-MA-V116-S9P02-005 stage9_phase2_isolation_boundary",
      "PARAM-MA-V116-S9P02-006 stage9_phase2_required_validator",
    ]),
    "model_parameters_stage9_phase2",
    "Model parameters document Stage 9 Phase 2 spike path, features, fixture safety, isolation and validator",
    "Model parameters are missing Stage 9 Phase 2 details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S9P02",
      "Memory Atlas v1.1.6 Stage 9 Phase 2",
      "EVID-MA-V116-S9P02-RIVER-C3-CONTRACT",
      "EVID-MA-V116-S9P02-RIVER-C3-ACCEPTANCE",
      "validate:v1.1.6-stage9-phase2",
    ]),
    "feature_list_stage9_phase2",
    "Feature list registers Stage 9 Phase 2 feature, evidence and validation",
    "Feature list is missing Stage 9 Phase 2 details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage9_phase02",
      "MA-V116-S9：C3 隔离原型",
      "MA-V116-S9P02 Memory River C3 Spike",
      "phase_9_2_memory_river_c3_spike_ready_pending_stage_review",
      "validate:v1.1.6-stage9-phase2",
    ]),
    "development_record_stage9_phase2",
    "Development record captures Stage 9 Phase 2 objective, tasks, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 9 Phase 2 details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S9P02",
      "记忆时间河 C3 隔离原型",
      "phase_9_2_memory_river_c3_spike_ready_pending_stage_review",
      "validate:v1.1.6-stage9-phase2",
      "memory_river_c3_spike_no_production_import",
    ]),
    "model_index_stage9_phase2",
    "Root model parameter file records Stage 9 Phase 2 model and parameters",
    "Root model parameter file is missing Stage 9 Phase 2 details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 9 Phase 2",
      "memory_river_c3_spike_contract.md",
      "memory_river_c3_spike_acceptance.md",
      "validate:v1.1.6-stage9-phase2",
      "phase_9_2_memory_river_c3_spike_ready_pending_stage_review",
      "No production integration",
      "No GitHub main upload",
    ]),
    "changelog_stage9_phase2",
    "Changelog records Stage 9 Phase 2 deliverables and non-goal boundaries",
    "Changelog is missing Stage 9 Phase 2 details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage9-phase2"'),
    "package_script_stage9_phase2",
    "Package script exposes validate:v1.1.6-stage9-phase2",
    "Package script is missing validate:v1.1.6-stage9-phase2",
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotePath=false", "status", "--short", "--", "OpenAIDatabase"], { cwd: worktreeRoot });
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase2.cjs",
    "apps/memory-atlas/src/experiments/memory-river-spike/README.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_river_c3_spike_acceptance.md",
    "docs/product/memory_river_c3_spike_contract.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage9_phase2_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 9 Phase 2 contracts, records, spike README, validator and package script",
    "Stage 9 Phase 2 contains out-of-scope OpenAIDatabase changes",
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
        || line.includes("OpenAIDatabase/apps/memory-atlas/dist/")
        || line.includes("OpenAIDatabase/apps/memory-atlas/build/")
        || line.includes("OpenAIDatabase/data/raw/")
        || line.includes("OpenAIDatabase/data/private/")
        || line.includes(".app")
    ));

  assertCondition(
    touchedRuntime.length === 0,
    "stage9_phase2_boundary",
    "No production runtime UI/CSS/build/app/data/writeback/deploy work is present in this phase",
    "Production runtime UI, CSS, build, app bundle, data, writeback or deploy artifact changed during Stage 9 Phase 2",
    { touchedRuntime },
  );
}

function main() {
  try {
    [
      "docs/product/memory_river_c3_spike_contract.md",
      "docs/acceptance/memory_river_c3_spike_acceptance.md",
      "apps/memory-atlas/src/experiments/memory-river-spike/README.md",
      "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
      "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
      "功能清单.md",
      "开发记录.md",
      "模型参数文件.md",
      "CHANGELOG.md",
    ].forEach(validateTextFile);
    validateContracts();
    validateSpikeFiles();
    validateProductionIsolation();
    validateRecords();
    validateChangeScope();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage9-phase2", checks }, null, 2));
  } catch (error) {
    checks.push({ name: "failure", status: "FAIL", evidence: error.message, details: error.details || {} });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage9-phase2", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
