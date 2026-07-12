#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S5P02";
const acceptanceId = "ACC-MA-V117-S5P02";
const status = "phase_5_2_c3_river_spike_completed_pending_stage5_review";
const validatorName = "validate:v1.1.7-stage5-phase2";
const browserValidatorName = "validate:memory-river-spike-browser";
const previousValidatorName = "validate:v1.1.7-stage5-phase1";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage5_phase1.cjs";
const spikeVersion = "memory_river_c3_spike.v1_1_7_stage5_phase2";
const fixtureVersion = "memory_river_spike_fixture.v1_1_7_stage5_phase2";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const spikeBase = "apps/memory-atlas/src/experiments/memory-river-spike";
const productPath = "docs/product/memory_river_c3_spike_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage5_phase2_c3_river_spike_acceptance.md";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_river_spike_browser.cjs",
  `OpenAIDatabase/${spikeBase}/README.md`,
  `OpenAIDatabase/${spikeBase}/fixture.ts`,
  `OpenAIDatabase/${spikeBase}/index.html`,
  `OpenAIDatabase/${spikeBase}/main.ts`,
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${productPath}`,
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

function validateStage5Phase1Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage5_phase2_open_diff_scope",
      "Open diff is limited to Stage 5 Phase 5.2 C3 River Spike files",
      "Unexpected files changed outside Stage 5 Phase 5.2 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage5_phase1_validator_registered_for_post_commit_run",
      "Stage 5 Phase 5.1 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 5 Phase 5.1 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage5_phase1_validator_deferred_until_clean_tree",
      "Stage 5 Phase 5.1 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S5P01",
    "stage5_phase1_validator",
    "Stage 5 Phase 5.1 validator returned PASS before Stage 5 Phase 5.2 acceptance",
    "Stage 5 Phase 5.1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateSpikeFiles() {
  [
    `${spikeBase}/README.md`,
    `${spikeBase}/fixture.ts`,
    `${spikeBase}/index.html`,
    `${spikeBase}/main.ts`,
    "apps/memory-atlas/scripts/validate_memory_river_spike_browser.cjs",
    productPath,
    acceptancePath,
  ].forEach(validateTextFile);

  const readme = readRepoFile(`${spikeBase}/README.md`);
  const fixture = readRepoFile(`${spikeBase}/fixture.ts`);
  const index = readRepoFile(`${spikeBase}/index.html`);
  const main = readRepoFile(`${spikeBase}/main.ts`);
  const browserValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_river_spike_browser.cjs");
  const product = readRepoFile(productPath);
  const acceptance = readRepoFile(acceptancePath);

  assertCondition(
    hasAll(readme, [
      "v1.1.7 Stage 5 Phase 5.2",
      taskId,
      acceptanceId,
      status,
      spikeVersion,
      "year_level",
      "month_level",
      "week_level",
      "day_level",
      "selected_range_summary",
      "trend: rising",
      "trend: declining",
      "trend: stable",
      "trend: conflict",
      "No production Timeline replacement",
      "No GitHub main upload",
    ]),
    "stage5_phase2_spike_readme",
    "Spike README records v1.1.7 Stage 5 Phase 5.2 scope, time levels, selected summary, trends and boundaries",
    "Spike README is missing v1.1.7 Stage 5 Phase 5.2 scope",
  );

  assertCondition(
    hasAll(fixture, [
      `schemaVersion: "${fixtureVersion}"`,
      "rawPrivateDataIncluded: false",
      "plaintextSecretsIncluded: false",
      "localAbsolutePathsIncluded: false",
      "writebackAllowed: false",
      "timeLevels",
      "\"year\"",
      "\"month\"",
      "\"week\"",
      "\"day\"",
      "trend: \"rising\"",
      "trend: \"declining\"",
      "trend: \"stable\"",
      "trend: \"conflict\"",
      "selectedRangeDefault",
    ]),
    "stage5_phase2_fixture_contract",
    "Spike fixture exposes safe flags, year/month/week/day levels, trend lanes and default brush range",
    "Spike fixture is missing Stage 5 Phase 5.2 fixture fields",
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
    "stage5_phase2_fixture_privacy",
    "Spike fixture does not expose obvious secrets, raw transcript wording or local private paths",
    "Spike fixture contains forbidden private payload markers",
    { forbidden },
  );

  assertCondition(
    hasAll(index, [
      "timeLevelControl",
      "selectedRangeThemes",
      "selectedRangeEvents",
      "selectedRangeSignals",
      "Memory Atlas v1.1.7 · Stage 5.2 isolated C3 spike",
    ]),
    "stage5_phase2_index_controls",
    "Spike HTML exposes time-level and selected-range summary controls",
    "Spike HTML is missing Stage 5.2 controls",
  );

  assertCondition(
    hasAll(main, [
      "STAGE5_PHASE2_SPIKE_VERSION",
      spikeVersion,
      "TIME_LEVELS",
      "year_level",
      "month_level",
      "week_level",
      "day_level",
      "type RiverTimeLevel",
      "activeTimeLevel",
      "setTimeLevel",
      "selectedRangeSummary",
      "showSelectedRangeSummary",
      "findSignalsInRange",
      "trendClass",
      "trend: rising",
      "trend: declining",
      "trend: stable",
      "trend: conflict",
      "setBrushRange",
      "getDateScreenX",
    ]),
    "stage5_phase2_main_runtime_contract",
    "Spike runtime exposes version, time levels, selected range summary, trend lanes and testable brush helpers",
    "Spike runtime is missing Stage 5.2 behavior",
  );

  assertCondition(
    hasAll(browserValidator, [
      "stage5_phase2_browser_time_levels",
      "stage5_phase2_browser_zoom",
      "stage5_phase2_browser_brush_selection",
      "stage5_phase2_browser_selected_theme_events",
      "stage5_phase2_browser_signal_positioning",
      "stage5_phase2_browser_reduced_motion",
      "stage5_phase2_browser_screenshot",
    ]),
    "stage5_phase2_browser_validator_contract",
    "Browser validator checks time levels, zoom, brush, selected summaries, signal positioning, reduced motion and screenshot evidence",
    "Browser validator is missing Stage 5.2 checks",
  );

  assertCondition(
    hasAll(product, [
      "v1.1.7 Stage 5 Phase 5.2",
      taskId,
      acceptanceId,
      status,
      spikeVersion,
      "Time Scale + Zoom",
      "Brush Selection",
      "Theme Lanes",
      "Black Hole / Proto-Star Bands",
      "No production Timeline replacement",
      "No GitHub main upload",
    ]),
    "stage5_phase2_product_contract",
    "Product contract records Stage 5 Phase 5.2 tasks, acceptance and non-goals",
    "Product contract is missing Stage 5 Phase 5.2 details",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 5 Phase 5.2 C3 River Spike Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      browserValidatorName,
      "year",
      "month",
      "week",
      "day",
      "selected range",
      "rising",
      "declining",
      "stable",
      "conflict",
      "Black Hole",
      "Proto-Star",
      "No production Timeline replacement",
      "No GitHub main upload",
    ]),
    "stage5_phase2_acceptance_contract",
    "Acceptance document pins time scale, brush, trend lanes, status bands, browser validation and no-upload boundary",
    "Stage 5 Phase 5.2 acceptance document is incomplete",
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

  [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "config/visualization/model_parameters.universe_state.yaml",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase2.cjs",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage5_phase2.cjs" &&
      packageJson.scripts?.[browserValidatorName] === "node scripts/validate_memory_river_spike_browser.cjs",
    "stage5_phase2_package_scripts",
    `package.json exposes ${validatorName} and ${browserValidatorName}`,
    "package.json is missing Stage 5 Phase 5.2 scripts",
    {
      validator: packageJson.scripts?.[validatorName],
      browserValidator: packageJson.scripts?.[browserValidatorName],
    },
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
        "Phase 5.2",
        "No production Timeline replacement",
        "No GitHub main upload",
      ]),
      `stage5_phase2_records_${name}`,
      `${name} records Stage 5 Phase 5.2 status, acceptance, validator, browser evidence and no-upload boundary`,
      `${name} is missing Stage 5 Phase 5.2 tokens`,
    );
  }
}

function validateProductionIsolation() {
  const srcRoot = path.join(repoRoot, "apps/memory-atlas/src");
  const files = [];
  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (fullPath.includes(`${path.sep}experiments${path.sep}memory-river-spike`)) continue;
        walk(fullPath);
      } else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
        files.push(fullPath);
      }
    }
  }
  walk(srcRoot);
  const offenders = files
    .filter((file) => fs.readFileSync(file, "utf8").includes("memory-river-spike"))
    .map((file) => path.relative(repoRoot, file));
  assertCondition(
    offenders.length === 0,
    "stage5_phase2_production_isolation",
    "Production src files outside the isolated experiment do not reference memory-river-spike",
    "Production code references the isolated Memory River spike",
    { offenders },
  );
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  const remoteBranch = run("git", ["ls-remote", "--heads", "origin", branchName], { cwd: worktreeRoot }).stdout.trim();

  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage5_phase2_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage5_phase2_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
  assertCondition(
    remoteBranch === "",
    "stage5_phase2_no_remote_branch",
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
    "stage5_phase2_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 5 Phase 5.2 spike, acceptance, records, validators and package scripts",
    "Unexpected files changed outside Stage 5 Phase 5.2 scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const readme = readRepoFile(`${spikeBase}/README.md`);
  assertCondition(
    hasAll(readme, [
      "No production Timeline replacement",
      "No production route or navigation change",
      "No feature flag default switch",
      "No raw/private/cookie/session/secret data read",
      "No direct active-memory writeback",
      "No agent apply",
      "No Stage 5.3",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage5_phase2_boundary",
    "No production Timeline replacement, route, raw/private read, direct writeback, agent apply, Stage 5.3 or GitHub main upload is included",
    "Stage 5 Phase 5.2 boundary violation detected",
  );
}

function main() {
  validateStage5Phase1Continuity();
  validateSpikeFiles();
  validateRecords();
  validateProductionIsolation();
  validateCanonicalBoundary();
  validateChangeScope();
  validateBoundary();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage5-phase2",
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
        stage: "v1.1.7-stage5-phase2",
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
