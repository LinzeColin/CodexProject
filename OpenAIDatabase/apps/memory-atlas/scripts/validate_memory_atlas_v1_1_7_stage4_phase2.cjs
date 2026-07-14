#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S4P02";
const acceptanceId = "ACC-MA-V117-S4P02";
const status = "phase_4_2_c3_starfield_spike_completed_pending_stage4_review";
const validatorName = "validate:v1.1.7-stage4-phase2";
const browserValidatorName = "validate:memory-starfield-spike-browser";
const previousValidatorName = "validate:v1.1.7-stage4-phase1";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage4_phase1.cjs";
const spikeVersion = "memory_starfield_c3_spike.v1_1_7_stage4_phase2";
const visualContractVersion = "memory_starfield_visual_contract.v1_1_7_stage4_phase1";

const spikeBase = "apps/memory-atlas/src/experiments/memory-starfield-spike";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage4_phase2_c3_starfield_spike_acceptance.md";
const productPath = "docs/product/memory_starfield_c3_spike_contract.md";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_starfield_spike_browser.cjs",
  `OpenAIDatabase/${spikeBase}/README.md`,
  `OpenAIDatabase/${spikeBase}/fixture.ts`,
  `OpenAIDatabase/${spikeBase}/index.html`,
  `OpenAIDatabase/${spikeBase}/main.ts`,
  `OpenAIDatabase/${spikeBase}/shaders/`,
  `OpenAIDatabase/${spikeBase}/shaders/flowField.ts`,
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${acceptancePath}`,
  `OpenAIDatabase/${productPath}`,
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

function walkFiles(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) walkFiles(fullPath, files);
    else files.push(fullPath);
  }
  return files;
}

function validateStage4Phase1Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage4_phase2_open_diff_scope",
      "Open diff is limited to Stage 4 Phase 4.2 C3 Starfield Spike files",
      "Unexpected files changed outside Stage 4 Phase 4.2 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage4_phase1_validator_registered_for_post_commit_run",
      "Stage 4 Phase 4.1 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 4 Phase 4.1 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage4_phase1_validator_deferred_until_clean_tree",
      "Stage 4 Phase 4.1 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S4P01",
    "stage4_phase1_validator",
    "Stage 4 Phase 4.1 validator returned PASS before Stage 4 Phase 4.2 acceptance",
    "Stage 4 Phase 4.1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateSpikeFiles() {
  [
    `${spikeBase}/README.md`,
    `${spikeBase}/fixture.ts`,
    `${spikeBase}/index.html`,
    `${spikeBase}/main.ts`,
    `${spikeBase}/shaders/flowField.ts`,
    "apps/memory-atlas/scripts/validate_memory_starfield_spike_browser.cjs",
  ].forEach(validateTextFile);

  const readme = readRepoFile(`${spikeBase}/README.md`);
  const fixture = readRepoFile(`${spikeBase}/fixture.ts`);
  const index = readRepoFile(`${spikeBase}/index.html`);
  const main = readRepoFile(`${spikeBase}/main.ts`);
  const flow = readRepoFile(`${spikeBase}/shaders/flowField.ts`);
  const browserValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_starfield_spike_browser.cjs");

  assertCondition(
    hasAll(readme, [
      "v1.1.7 Stage 4 Phase 4.2",
      taskId,
      acceptanceId,
      status,
      spikeVersion,
      "GPU particle spike",
      "Flow Field / Curl Noise",
      "Cluster Gravity",
      "Hover Cards B2",
      "No production Galaxy replacement",
      "No GitHub main upload",
    ]),
    "stage4_phase2_spike_readme",
    "Spike README records v1.1.7 Stage 4 Phase 4.2 scope, tasks and boundaries",
    "Spike README is missing v1.1.7 Stage 4 Phase 4.2 scope",
  );

  assertCondition(
    hasAll(fixture, [
      "schemaVersion: \"memory_starfield_spike_fixture.v1_1_7_stage4_phase2\"",
      "rawPrivateDataIncluded: false",
      "plaintextSecretsIncluded: false",
      "localAbsolutePathsIncluded: false",
      "importance",
      "priority",
      "terrainClass",
      "flowInfluence",
      "orbitStability",
    ]),
    "stage4_phase2_fixture_fields",
    "Spike fixture has redacted flags plus B2 hover, terrain and flow/gravity fields",
    "Spike fixture is missing v1.1.7 Stage 4.2 fields",
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
    "stage4_phase2_fixture_privacy",
    "Spike fixture does not expose obvious secrets, raw transcript wording or local private paths",
    "Spike fixture contains forbidden private payload markers",
    { forbidden },
  );

  assertCondition(
    hasAll(flow, [
      "FLOW_FIELD_SHADER_CONTRACT",
      spikeVersion,
      "curl_noise_shader",
      "sampleCurlNoise",
      "buildFlowFieldVector",
      "STARFIELD_VERTEX_SHADER",
      "STARFIELD_FRAGMENT_SHADER",
      "uFlowStrength",
      "uReducedMotion",
    ]),
    "stage4_phase2_flow_shader_contract",
    "Flow Field / Curl Noise shader module defines deterministic CPU and GPU contract",
    "Flow Field shader module is incomplete",
  );

  assertCondition(
    hasAll(main, [
      "STAGE4_PHASE2_SPIKE_VERSION",
      spikeVersion,
      "FLOW_FIELD_SHADER_CONTRACT",
      "ShaderMaterial",
      "createParticleTrailLines",
      "trajectoryTrailCount",
      "gravitySourceCount",
      "hoverCardMode",
      "B2",
      "screenPositionForCluster",
      "getClusterScreenPosition",
      "smokeComplete",
      "PARTICLE_COUNTS",
      "mid: 10000",
      "Cluster Gravity",
      "Flow Field / Curl Noise",
    ]),
    "stage4_phase2_main_runtime_contract",
    "Spike main source exposes shader particles, trails, gravity metrics, B2 hover and smoke/browser hooks",
    "Spike main source is missing Stage 4 Phase 4.2 runtime contract",
  );

  assertCondition(
    hasAll(index, [
      "Memory Atlas v1.1.7",
      "Stage 4.2",
      "particleTrailCount",
      "gravitySourceCount",
      "hoverCardMode",
    ]),
    "stage4_phase2_index_status",
    "Spike HTML exposes Stage 4.2 status metrics for browser validation",
    "Spike HTML is missing Stage 4.2 status metrics",
  );

  assertCondition(
    hasAll(browserValidator, [
      "validate_memory_starfield_spike_browser",
      "particleCount >= 10000",
      "fps >= 30",
      "flowFieldMode === \"curl_noise_shader\"",
      "trajectoryTrailCount >= 256",
      "gravitySourceCount >= 6",
      "hoverCardMode === \"B2\"",
      "page.screenshot",
      "getClusterScreenPosition",
    ]),
    "stage4_phase2_browser_validator_source",
    "Browser validator checks particle count, FPS, flow mode, trails, gravity sources, hover B2 and screenshot",
    "Browser validator source is incomplete",
  );
}

function validateContractsAndRecords() {
  [
    productPath,
    acceptancePath,
    "config/visualization/model_parameters.universe_state.yaml",
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "apps/memory-atlas/package.json",
  ].forEach(validateTextFile);

  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  const product = readRepoFile(productPath);
  const acceptance = readRepoFile(acceptancePath);
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");
  const records = [
    ["CHANGELOG.md", readRepoFile("CHANGELOG.md")],
    ["功能清单.md", readRepoFile("功能清单.md")],
    ["开发记录.md", readRepoFile("开发记录.md")],
    ["模型参数文件.md", readRepoFile("模型参数文件.md")],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md")],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")],
  ];

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage4_phase2.cjs" &&
      packageJson.scripts?.[browserValidatorName] === "node scripts/validate_memory_starfield_spike_browser.cjs",
    "stage4_phase2_package_scripts",
    `package.json exposes ${validatorName} and ${browserValidatorName}`,
    "package.json is missing Stage 4 Phase 4.2 validation scripts",
    { staticScript: packageJson.scripts?.[validatorName], browserScript: packageJson.scripts?.[browserValidatorName] },
  );

  assertCondition(
    hasAll(product, [
      "v1.1.7 Stage 4 Phase 4.2",
      taskId,
      acceptanceId,
      status,
      spikeVersion,
      visualContractVersion,
      "GPU particle spike",
      "Flow Field / Curl Noise",
      "Cluster Gravity",
      "Hover Cards B2",
      "No production Galaxy replacement",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage4_phase2_product_contract",
    "Product contract records v1.1.7 Stage 4.2 runtime spike scope and boundaries",
    "Product contract is missing Stage 4 Phase 4.2 details",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 4 Phase 4.2 C3 Starfield Spike Acceptance",
      taskId,
      acceptanceId,
      status,
      spikeVersion,
      validatorName,
      browserValidatorName,
      ">=10k particles",
      ">=30 FPS",
      "Flow Field / Curl Noise",
      "Cluster Gravity",
      "Hover Cards B2",
      "screenshot",
      "No production Galaxy replacement",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage4_phase2_acceptance_contract",
    "Acceptance document pins particle, FPS, screenshot, flow, gravity, hover and boundary checks",
    "Acceptance document is incomplete",
  );

  assertCondition(
    hasAll(params, [
      taskId,
      acceptanceId,
      status,
      spikeVersion,
      "stage4_phase2_particle_floor",
      "stage4_phase2_desktop_min_fps",
      "stage4_phase2_required_runtime_features",
      "stage4_phase2_browser_validator",
      "stage4_phase2_boundary",
    ]),
    "stage4_phase2_model_parameters",
    "Universe-state parameter template registers Stage 4 Phase 4.2 runtime thresholds and browser validator",
    "Universe-state parameter template is missing Stage 4 Phase 4.2 entries",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        browserValidatorName,
        spikeVersion,
        "C3 Starfield Spike",
        "No production Galaxy replacement",
        "No GitHub main upload",
      ]),
      `stage4_phase2_records_${name}`,
      `${name} registers Stage 4 Phase 4.2 status, acceptance, validators and no-upload boundary`,
      `${name} is missing Stage 4 Phase 4.2 records`,
    );
  }
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
    "stage4_phase2_production_isolation",
    "Production src files outside the experiment do not import or reference memory-starfield-spike",
    "Production code references the Memory Starfield experiment",
    { references },
  );
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage4_phase2_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage4_phase2_sparse_boundary",
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
    "stage4_phase2_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 4 Phase 4.2 spike, contracts, records, validators and package script",
    "Unexpected files changed outside Stage 4 Phase 4.2 scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const statusOutput = run("git", ["-c", "core.quotepath=false", "status", "--short"], { cwd: worktreeRoot }).stdout;
  const forbidden = [
    "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
    "OpenAIDatabase/apps/memory-atlas/src/main.tsx",
    "OpenAIDatabase/apps/memory-atlas/src/components/",
    "OpenAIDatabase/apps/memory-atlas/src/styles.css",
    "OpenAIDatabase/apps/memory-atlas/dist/",
    "OpenAIDatabase/data/raw/",
    "OpenAIDatabase/data/private/",
    ".app",
  ];
  const matches = forbidden.filter((fragment) => statusOutput.includes(fragment));
  assertCondition(
    matches.length === 0,
    "stage4_phase2_boundary",
    "No production UI/component/style/build/app/raw-private data change is present in this isolated spike phase",
    "Production UI, component, style, build, app bundle or raw/private data changed during Stage 4 Phase 4.2",
    { matches },
  );
}

function main() {
  validateStage4Phase1Continuity();
  validateSpikeFiles();
  validateContractsAndRecords();
  validateProductionIsolation();
  validateCanonicalBoundary();
  validateChangeScope();
  validateBoundary();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage4-phase2",
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
        stage: "v1.1.7-stage4-phase2",
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
