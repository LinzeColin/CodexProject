#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S1P01";
const acceptanceId = "ACC-MA-V117-S1P01";
const status = "phase_1_1_universe_state_schema_completed_pending_stage1_review";
const validatorName = "validate:v1.1.7-stage1-phase1";

const requiredStateFields = [
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
  "recommended_next_actions",
];

const requiredConsumers = [
  "memory_overview",
  "memory_starfield",
  "memory_river",
  "data_map_2_0",
  "search_2_0",
  "review_summary_iteration",
  "inspector",
  "roi_dashboard",
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
    `${relativePath} has no blocked mojibake characters, null bytes or trailing whitespace`,
    `${relativePath} contains blocked characters or trailing whitespace`,
    { badLines: badLines.slice(0, 20) },
  );
}

function validateUniverseStateSpike() {
  const result = run(process.execPath, ["--experimental-strip-types", "scripts/validate_universe_state_spike.mjs"], {
    cwd: appRoot,
  });
  const parsed = JSON.parse(result.stdout);
  assertCondition(
    parsed.ok === true
      && parsed.parameter_source === "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml"
      && parsed.privacy_status?.raw_private_data_included === false
      && parsed.privacy_status?.plaintext_secrets_included === false
      && parsed.privacy_status?.local_absolute_paths_included === false
      && parsed.privacy_status?.writeback_allowed === false,
    "stage1_phase1_universe_state_spike_validator",
    "Existing Universe State spike validator proves deterministic sample, parameter source and privacy flags",
    "Universe State spike validator output did not prove the required v1.1.7 safety gates",
    {
      ok: parsed.ok,
      parameter_source: parsed.parameter_source,
      privacy_status: parsed.privacy_status,
    },
  );
}

function validateArchitectureAndParameters() {
  const architecture = readRepoFile("docs/architecture/universe_state_snapshot.md");
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_v1_1_7_stage1_phase1_universe_state_acceptance.md");

  assertCondition(
    hasAll(architecture, [
      "v1.1.7 Stage 1 Phase 1 Addendum",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "data_map_2_0",
      "search_2_0",
      "review_summary_iteration",
      "recommended_next_actions",
      "proposal_only: true",
      "Phase 1.2",
      "Phase 1.3",
      "Stage 8",
      "No raw/private",
      "GitHub main upload",
    ].concat(requiredStateFields, requiredConsumers)),
    "stage1_phase1_architecture_contract",
    "Universe State architecture records v1.1.7 required fields, consumers, proposal-only boundary and phase stop",
    "Universe State architecture contract is missing v1.1.7 Stage 1 Phase 1 requirements",
  );

  assertCondition(
    hasAll(params, [
      "v1_1_7_stage1_phase1:",
      `task_id: ${taskId}`,
      `acceptance_id: ${acceptanceId}`,
      `status: ${status}`,
      `required_validator: ${validatorName}`,
      "schema_version_retained: universe_state_snapshot.v1",
      "proposal_only_required: true",
      "suggested_action_detail_runtime",
      "tier_asset_detail_model",
      "topic_classification_detail_model",
    ].concat(requiredStateFields, requiredConsumers)),
    "stage1_phase1_parameter_template",
    "Universe State parameter template records v1.1.7 schema gate, required fields, consumers and deferred work",
    "Universe State parameter template is missing v1.1.7 Stage 1 Phase 1 anchors",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 1 Phase 1 Universe State Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "Data Map 2.0",
      "Search 2.0",
      "Review / Summary / Iteration",
      "proposal_only: true",
      "recommended_next_actions",
      "No raw/private",
      "Stop after this phase",
    ].concat(requiredStateFields, requiredConsumers)),
    "stage1_phase1_acceptance_contract",
    "Acceptance contract covers evidence, fields, consumers, failure conditions, validation and stop boundary",
    "Stage 1 Phase 1 acceptance contract is incomplete",
  );
}

function validateSampleSchemaAndModel() {
  const sample = readJson("apps/memory-atlas/src/fixtures/universe_state.sample.json");
  const schema = readJson("apps/memory-atlas/src/fixtures/universe_state.schema.json");
  const model = readRepoFile("apps/memory-atlas/src/models/universeState.ts");

  const state = sample.state || {};
  const consumerMap = sample.consumer_map || {};
  const actions = Array.isArray(state.recommended_next_actions) ? state.recommended_next_actions : [];
  const schemaRequired = schema.properties?.consumer_map?.required || [];

  const missingStateFields = requiredStateFields.filter((field) => !(field in state));
  const missingSampleConsumers = requiredConsumers.filter((consumer) => !Array.isArray(consumerMap[consumer]));
  const missingSchemaConsumers = requiredConsumers.filter((consumer) => !schemaRequired.includes(consumer));
  const missingModelConsumers = requiredConsumers.filter((consumer) => !model.includes(`${consumer}: [`));

  assertCondition(
    sample.schema_version === "universe_state_snapshot.v1"
      && missingStateFields.length === 0
      && missingSampleConsumers.length === 0
      && missingSchemaConsumers.length === 0
      && missingModelConsumers.length === 0
      && actions.length >= 1
      && actions.every((action) => action.proposal_only === true)
      && sample.diagnostics?.privacy_status?.raw_private_data_included === false
      && sample.diagnostics?.privacy_status?.plaintext_secrets_included === false
      && sample.diagnostics?.privacy_status?.local_absolute_paths_included === false
      && sample.diagnostics?.privacy_status?.writeback_allowed === false,
    "stage1_phase1_sample_schema_model",
    "Universe State model, schema and deterministic sample expose required v1.1.7 fields and consumer map with proposal-only actions",
    "Universe State model, schema or sample is missing v1.1.7 Phase 1.1 requirements",
    {
      missingStateFields,
      missingSampleConsumers,
      missingSchemaConsumers,
      missingModelConsumers,
      actionCount: actions.length,
      privacy: sample.diagnostics?.privacy_status,
    },
  );
}

function validateRecords() {
  const records = [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  ];

  for (const relativePath of records) {
    const source = readRepoFile(relativePath);
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "Universe State",
        "data_map_2_0",
        "search_2_0",
        "review_summary_iteration",
      ]),
      `stage1_phase1_records_${relativePath}`,
      `${relativePath} registers Stage 1 Phase 1 task, acceptance, status, validator and consumer map`,
      `${relativePath} is missing Stage 1 Phase 1 records`,
    );
  }

  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  assertCondition(
    packageSource.includes('"validate:v1.1.7-stage1-phase1": "node scripts/validate_memory_atlas_v1_1_7_stage1_phase1.cjs"'),
    "stage1_phase1_package_script",
    "Package script exposes validate:v1.1.7-stage1-phase1",
    "Package script validate:v1.1.7-stage1-phase1 is missing",
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotePath=false", "status", "--short", "--", "OpenAIDatabase"], {
    cwd: worktreeRoot,
  });
  const changed = result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3))
    .map((line) => line.replace(/^OpenAIDatabase\//, ""))
    .map((line) => line.replace(/^\"(.+)\"$/, "$1"))
    .filter(Boolean);

  const allowed = [
    "CHANGELOG.md",
    "config/visualization/model_parameters.universe_state.yaml",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_atlas_v1_1_7_stage1_phase1_universe_state_acceptance.md",
    "docs/architecture/universe_state_snapshot.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase1.cjs",
    "apps/memory-atlas/src/fixtures/universe_state.sample.json",
    "apps/memory-atlas/src/fixtures/universe_state.schema.json",
    "apps/memory-atlas/src/models/universeState.ts",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage1_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 Phase 1 schema, fixture, validator and records",
    "Unexpected OpenAIDatabase paths changed",
    { changed, outside },
  );
}

try {
  [
    "docs/architecture/universe_state_snapshot.md",
    "config/visualization/model_parameters.universe_state.yaml",
    "docs/acceptance/memory_atlas_v1_1_7_stage1_phase1_universe_state_acceptance.md",
    "apps/memory-atlas/src/models/universeState.ts",
    "apps/memory-atlas/src/fixtures/universe_state.schema.json",
    "apps/memory-atlas/src/fixtures/universe_state.sample.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase1.cjs",
  ].forEach(validateTextFile);
  validateUniverseStateSpike();
  validateArchitectureAndParameters();
  validateSampleSchemaAndModel();
  validateRecords();
  validateChangeScope();
  pass("stage1_phase1_boundary", "No Phase 1.2, runtime UI, CSS, raw/private read, direct writeback, proposal write, build, deploy or GitHub main upload is included");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.7-stage1-phase1", acceptance_id: acceptanceId, checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.7-stage1-phase1",
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || null,
    stdout: error.stdout || undefined,
    stderr: error.stderr || undefined,
    checks,
  }, null, 2));
  process.exit(1);
}
