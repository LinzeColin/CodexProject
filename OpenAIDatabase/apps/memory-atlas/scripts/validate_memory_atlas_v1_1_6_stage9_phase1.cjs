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
  const product = readRepoFile("docs/product/memory_starfield_c3_spike_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_starfield_c3_spike_acceptance.md");
  assertCondition(
    hasAll(product, [
      "Memory Atlas 记忆星系 C3 隔离原型合同",
      "v1.1.6 Stage 9 Phase 1",
      "memory_starfield_c3_spike_contract",
      "MA-V116-S9P01",
      "phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review",
      "three_js_canvas",
      "particle_lod",
      "nebula_dust",
      "flow_field",
      "gravity_disk",
      "black_hole_marker",
      "proto_star_marker",
      "memory_terrain_signal",
      "hover_card",
      "smoke_status_hook",
      "No production integration",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ])
      && hasAll(acceptance, [
        "Memory Atlas 记忆星系 C3 隔离原型验收",
        "validate:v1.1.6-stage9-phase1",
        "default mid particle count at least",
        "rawPrivateDataIncluded: false",
        "plaintextSecretsIncluded: false",
        "localAbsolutePathsIncluded: false",
        "Production `src` files outside the experiment directory do not import or",
        "No Stage 9 review",
        "No Stage 10 work",
        "No GitHub main upload",
      ]),
    "stage9_phase1_contracts",
    "Stage 9 Phase 1 product and acceptance contracts define Memory Starfield C3 spike requirements and boundaries",
    "Stage 9 Phase 1 contracts are incomplete",
  );
}

function validateSpikeFiles() {
  const base = "apps/memory-atlas/src/experiments/memory-starfield-spike";
  const requiredFiles = ["README.md", "index.html", "main.ts", "fixture.ts"];
  const missing = requiredFiles.filter((file) => !fs.existsSync(path.join(repoRoot, base, file)));
  assertCondition(
    missing.length === 0,
    "stage9_phase1_spike_files",
    "Memory Starfield spike has README, index, main and fixture files",
    "Memory Starfield spike is missing required files",
    { missing },
  );

  const readme = readRepoFile(`${base}/README.md`);
  const main = readRepoFile(`${base}/main.ts`);
  const fixture = readRepoFile(`${base}/fixture.ts`);

  assertCondition(
    hasAll(readme, [
      "v1.1.6 Stage 9 Phase 1 Continuity",
      "MA-V116-S9P01",
      "validate:v1.1.6-stage9-phase1",
      "No production integration",
      "No GitHub main upload",
    ]),
    "stage9_phase1_spike_readme",
    "Memory Starfield spike README records v1.1.6 Stage 9 Phase 1 continuity and boundary",
    "Memory Starfield spike README is missing v1.1.6 Stage 9 Phase 1 continuity",
  );

  assertCondition(
    hasAll(main, [
      "import * as THREE from \"three\"",
      "__memoryStarfieldSpike",
      "high: 12000",
      "mid: 10000",
      "low: 8000",
      "createGravitationalDisk",
      "createNebulaDust",
      "findCluster(\"proto_star\")",
      "cluster.kind === \"black_hole\"",
      "reducedMotionControl",
      "hoverCard",
      "smokeStatus",
      "qualityControl",
      "raycaster",
    ]),
    "stage9_phase1_spike_main",
    "Memory Starfield spike main source exposes Three.js, LOD, nebula, gravity, markers, hover, reduced-motion and smoke hooks",
    "Memory Starfield spike main source is missing required prototype behavior",
  );

  assertCondition(
    hasAll(fixture, [
      "schemaVersion: \"memory_starfield_spike_fixture.v1\"",
      "rawPrivateDataIncluded: false",
      "plaintextSecretsIncluded: false",
      "localAbsolutePathsIncluded: false",
      "kind: \"dominant\"",
      "kind: \"rising\"",
      "kind: \"declining\"",
      "kind: \"black_hole\"",
      "kind: \"proto_star\"",
      "kind: \"terrain\"",
    ]),
    "stage9_phase1_spike_fixture",
    "Memory Starfield fixture has redacted flags and required cluster kinds",
    "Memory Starfield fixture is missing required redacted flags or cluster kinds",
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
    "stage9_phase1_fixture_privacy",
    "Memory Starfield fixture does not expose obvious secrets, raw transcript wording or local private paths",
    "Memory Starfield fixture contains forbidden private payload markers",
    { forbidden },
  );
}

function validateProductionIsolation() {
  const srcRoot = path.join(repoRoot, "apps/memory-atlas/src");
  const experimentDir = path.join(srcRoot, "experiments/memory-starfield-spike");
  const productionFiles = walkFiles(srcRoot)
    .filter((file) => !file.startsWith(experimentDir))
    .filter((file) => /\.(?:ts|tsx|js|jsx|mjs|cjs)$/.test(file));
  const references = productionFiles
    .map((file) => ({ file, source: fs.readFileSync(file, "utf8") }))
    .filter(({ source }) => source.includes("memory-starfield-spike") || source.includes("Memory Starfield Spike"))
    .map(({ file }) => path.relative(repoRoot, file));

  assertCondition(
    references.length === 0,
    "stage9_phase1_production_isolation",
    "Production src files outside the experiment do not import or reference memory-starfield-spike",
    "Production code references the Memory Starfield experiment",
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
      "Stage 9 Phase 1：Memory Starfield C3 Spike",
      "phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review",
      "MA-V116-S9P01",
      "validate:v1.1.6-stage9-phase1",
      "No production integration",
      "No GitHub main upload",
    ]),
    "delivery_record_stage9_phase1",
    "Delivery record captures Stage 9 Phase 1 scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 9 Phase 1 details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 9 Phase 1 记忆星系 C3 隔离原型参数",
      "PARAM-MA-V116-S9P01-001 stage9_phase1_contract_id",
      "PARAM-MA-V116-S9P01-002 stage9_phase1_spike_path",
      "PARAM-MA-V116-S9P01-003 stage9_phase1_required_features",
      "PARAM-MA-V116-S9P01-004 stage9_phase1_fixture_safety",
      "PARAM-MA-V116-S9P01-005 stage9_phase1_isolation_boundary",
      "PARAM-MA-V116-S9P01-006 stage9_phase1_required_validator",
    ]),
    "model_parameters_stage9_phase1",
    "Model parameters document Stage 9 Phase 1 spike path, features, fixture safety, isolation and validator",
    "Model parameters are missing Stage 9 Phase 1 details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S9P01",
      "Memory Atlas v1.1.6 Stage 9 Phase 1",
      "EVID-MA-V116-S9P01-STARFIELD-C3-CONTRACT",
      "EVID-MA-V116-S9P01-STARFIELD-C3-ACCEPTANCE",
      "validate:v1.1.6-stage9-phase1",
    ]),
    "feature_list_stage9_phase1",
    "Feature list registers Stage 9 Phase 1 feature, evidence and validation",
    "Feature list is missing Stage 9 Phase 1 details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage9_phase01",
      "MA-V116-S9：C3 隔离原型",
      "MA-V116-S9P01 Memory Starfield C3 Spike",
      "phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review",
      "validate:v1.1.6-stage9-phase1",
    ]),
    "development_record_stage9_phase1",
    "Development record captures Stage 9 Phase 1 objective, tasks, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 9 Phase 1 details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S9P01",
      "记忆星系 C3 隔离原型",
      "phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review",
      "validate:v1.1.6-stage9-phase1",
      "memory_starfield_c3_spike_no_production_import",
    ]),
    "model_index_stage9_phase1",
    "Root model parameter file records Stage 9 Phase 1 model and parameters",
    "Root model parameter file is missing Stage 9 Phase 1 details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 9 Phase 1",
      "memory_starfield_c3_spike_contract.md",
      "memory_starfield_c3_spike_acceptance.md",
      "validate:v1.1.6-stage9-phase1",
      "phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review",
      "No production integration",
      "No GitHub main upload",
    ]),
    "changelog_stage9_phase1",
    "Changelog records Stage 9 Phase 1 deliverables and non-goal boundaries",
    "Changelog is missing Stage 9 Phase 1 details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage9-phase1"'),
    "package_script_stage9_phase1",
    "Package script exposes validate:v1.1.6-stage9-phase1",
    "Package script is missing validate:v1.1.6-stage9-phase1",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase1.cjs",
    "apps/memory-atlas/src/experiments/memory-starfield-spike/README.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_starfield_c3_spike_acceptance.md",
    "docs/product/memory_starfield_c3_spike_contract.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage9_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 9 Phase 1 contracts, records, spike README, validator and package script",
    "Stage 9 Phase 1 contains out-of-scope OpenAIDatabase changes",
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
    "stage9_phase1_boundary",
    "No production runtime UI/CSS/build/app/data/writeback/deploy work is present in this phase",
    "Production runtime UI, CSS, build, app bundle, data, writeback or deploy artifact changed during Stage 9 Phase 1",
    { touchedRuntime },
  );
}

function main() {
  try {
    [
      "docs/product/memory_starfield_c3_spike_contract.md",
      "docs/acceptance/memory_starfield_c3_spike_acceptance.md",
      "apps/memory-atlas/src/experiments/memory-starfield-spike/README.md",
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
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage9-phase1", checks }, null, 2));
  } catch (error) {
    checks.push({ name: "failure", status: "FAIL", evidence: error.message, details: error.details || {} });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage9-phase1", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
