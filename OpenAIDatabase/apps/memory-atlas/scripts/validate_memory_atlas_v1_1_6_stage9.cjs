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

function validatePhaseContractSets() {
  const starfieldProduct = readRepoFile("docs/product/memory_starfield_c3_spike_contract.md");
  const starfieldAcceptance = readRepoFile("docs/acceptance/memory_starfield_c3_spike_acceptance.md");
  const starfieldValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase1.cjs");
  assertCondition(
    hasAll(starfieldProduct, [
      "Memory Atlas 记忆星系 C3 隔离原型合同",
      "v1.1.6 Stage 9 Phase 1",
      "memory_starfield_c3_spike_contract",
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
      "No GitHub main upload",
    ])
      && hasAll(starfieldAcceptance, [
      "Memory Atlas 记忆星系 C3 隔离原型验收",
      "validate:v1.1.6-stage9-phase1",
      "fixture safety",
      "Production `src`",
      "No Stage 9 review",
      ])
      && hasAll(starfieldValidator, [
        "v1.1.6-stage9-phase1",
        "stage9_phase1_contracts",
        "stage9_phase1_spike_files",
        "stage9_phase1_production_isolation",
      ]),
    "stage9_phase1_contract_set",
    "Stage 9 Phase 1 product contract, acceptance contract and phase validator are present and aligned",
    "Stage 9 Phase 1 contract set is incomplete",
  );

  const riverProduct = readRepoFile("docs/product/memory_river_c3_spike_contract.md");
  const riverAcceptance = readRepoFile("docs/acceptance/memory_river_c3_spike_acceptance.md");
  const riverValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase2.cjs");
  assertCondition(
    hasAll(riverProduct, [
      "Memory Atlas 记忆时间河 C3 隔离原型合同",
      "v1.1.6 Stage 9 Phase 2",
      "memory_river_c3_spike_contract",
      "d3_time_scale",
      "zoom_pan",
      "brush_selection",
      "theme_lanes",
      "black_hole_band",
      "proto_star_marker",
      "event_pulses",
      "hover_card",
      "smoke_status_hook",
      "No production integration",
      "No GitHub main upload",
    ])
      && hasAll(riverAcceptance, [
      "Memory Atlas 记忆时间河 C3 隔离原型验收",
      "validate:v1.1.6-stage9-phase2",
      "fixture safety",
      "Production `src`",
      "No Stage 9 review",
      ])
      && hasAll(riverValidator, [
        "v1.1.6-stage9-phase2",
        "stage9_phase2_contracts",
        "stage9_phase2_spike_files",
        "stage9_phase2_production_isolation",
      ]),
    "stage9_phase2_contract_set",
    "Stage 9 Phase 2 product contract, acceptance contract and phase validator are present and aligned",
    "Stage 9 Phase 2 contract set is incomplete",
  );

  const dataMapProduct = readRepoFile("docs/product/data_map_c3_spike_contract.md");
  const dataMapAcceptance = readRepoFile("docs/acceptance/data_map_c3_spike_acceptance.md");
  const dataMapValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase3.cjs");
  assertCondition(
    hasAll(dataMapProduct, [
      "Memory Atlas Data Map C3 隔离原型合同",
      "v1.1.6 Stage 9 Phase 3",
      "data_map_c3_spike_contract",
      "source_layer",
      "topic_layer",
      "asset_layer",
      "action_layer",
      "data_to_action_flow",
      "map_card",
      "open_inspector",
      "jump_to_search",
      "jump_to_review",
      "proposal_candidate",
      "No production integration",
      "No GitHub main upload",
    ])
      && hasAll(dataMapAcceptance, [
      "Memory Atlas Data Map C3 隔离原型验收",
      "validate:v1.1.6-stage9-phase3",
      "proposalOnly: true",
      "Production `src`",
      "No Stage 9 review",
      ])
      && hasAll(dataMapValidator, [
        "v1.1.6-stage9-phase3",
        "stage9_phase3_contracts",
        "stage9_phase3_spike_files",
        "stage9_phase3_production_isolation",
      ]),
    "stage9_phase3_contract_set",
    "Stage 9 Phase 3 product contract, acceptance contract and phase validator are present and aligned",
    "Stage 9 Phase 3 contract set is incomplete",
  );

  const universeProduct = readRepoFile("docs/product/universe_state_fixture_continuity_contract.md");
  const universeAcceptance = readRepoFile("docs/acceptance/universe_state_fixture_continuity_acceptance.md");
  const universeValidator = readRepoFile("apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase4.cjs");
  assertCondition(
    hasAll(universeProduct, [
      "Memory Atlas Universe State Fixture Continuity 合同",
      "v1.1.6 Stage 9 Phase 4",
      "universe_state_fixture_continuity_contract",
      "redacted_fixture_adapter",
      "deterministic_sample_generation",
      "schema_validation",
      "parameter_drift_gate",
      "black_hole_score",
      "proto_star_score",
      "stale_score",
      "consumer_map",
      "proposal_only_actions",
      "privacy_status",
      "No production integration",
      "No GitHub main upload",
    ])
      && hasAll(universeAcceptance, [
        "Memory Atlas Universe State Fixture Continuity 验收",
        "validate:v1.1.6-stage9-phase4",
        "validate:universe-state-spike",
        "proposal_only: true",
        "Production `src`",
        "No Stage 9 review",
      ])
      && hasAll(universeValidator, [
        "v1.1.6-stage9-phase4",
        "stage9_phase4_contracts",
        "stage9_phase4_existing_universe_validator",
        "stage9_phase4_production_isolation",
      ]),
    "stage9_phase4_contract_set",
    "Stage 9 Phase 4 product contract, acceptance contract and phase validator are present and aligned",
    "Stage 9 Phase 4 contract set is incomplete",
  );
}

function validateReviewArtifact() {
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage9_review.md");
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 9 Review",
      "stage_9_review_passed_pending_github_main_upload",
      "MA-V116-S9P01",
      "MA-V116-S9P02",
      "MA-V116-S9P03",
      "MA-V116-S9P04",
      "validate:v1.1.6-stage9",
      "validate:v1.1.6-stage9-phase1",
      "validate:v1.1.6-stage9-phase2",
      "validate:v1.1.6-stage9-phase3",
      "validate:v1.1.6-stage9-phase4",
      "validate:universe-state-spike",
      "memory_starfield_c3_spike_contract",
      "memory_river_c3_spike_contract",
      "data_map_c3_spike_contract",
      "universe_state_fixture_continuity_contract",
      "No production integration",
      "No production UI implementation",
      "No feature flag default switch",
      "No direct writeback",
      "No Stage 10 work in this review",
      "No GitHub main upload",
      "Stage 10 must start in a separate bounded run",
    ]),
    "stage9_review_artifact",
    "Stage 9 review artifact records phase coverage, validation, boundaries, risks and next gate",
    "Stage 9 review artifact is incomplete",
  );
}

function validateProductionIsolation() {
  const srcRoot = path.join(repoRoot, "apps/memory-atlas/src");
  const experimentRoots = [
    path.join(srcRoot, "experiments/memory-starfield-spike"),
    path.join(srcRoot, "experiments/memory-river-spike"),
    path.join(srcRoot, "experiments/data-map-spike"),
    path.join(srcRoot, "experiments/universe-state-generator-spike"),
  ];
  const productionFiles = walkFiles(srcRoot)
    .filter((file) => !experimentRoots.some((root) => file.startsWith(root)))
    .filter((file) => /\.(?:ts|tsx|js|jsx|mjs|cjs)$/.test(file));
  const markers = [
    "memory-starfield-spike",
    "memory-river-spike",
    "data-map-spike",
    "experiments/universe-state-generator-spike",
    "Universe State Generator Spike",
  ];
  const references = productionFiles
    .map((file) => ({ file, source: fs.readFileSync(file, "utf8") }))
    .filter(({ source }) => markers.some((marker) => source.includes(marker)))
    .map(({ file }) => path.relative(repoRoot, file));

  assertCondition(
    references.length === 0,
    "stage9_review_production_isolation",
    "Production src files outside isolated experiments do not import or reference Stage 9 spike directories",
    "Production code references Stage 9 isolated experiments",
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
      "Stage 9 整体复审",
      "stage_9_review_passed_pending_github_main_upload",
      "docs/reviews/memory_atlas_v1_1_6_stage9_review.md",
      "validate:v1.1.6-stage9",
      "MA-V116-S9-REVIEW",
      "No production integration",
      "No raw/private data read",
      "No direct writeback",
      "No Stage 10 work",
      "No GitHub main upload",
    ]),
    "delivery_record_stage9_review",
    "Delivery record captures Stage 9 review scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 9 review details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 9 整体复审门槛",
      "stage_9_review_passed_pending_github_main_upload",
      "PARAM-MA-V116-S9-REVIEW-001 stage9_required_validator",
      "PARAM-MA-V116-S9-REVIEW-002 stage9_review_status",
      "PARAM-MA-V116-S9-REVIEW-003 stage9_review_artifact",
      "PARAM-MA-V116-S9-REVIEW-004 stage9_allowed_change_scope",
      "PARAM-MA-V116-S9-REVIEW-005 stage9_next_gate",
      "PARAM-MA-V116-S9-REVIEW-006 upload_boundary",
    ]),
    "model_parameters_stage9_review",
    "Model parameters document Stage 9 review validator, status, artifact, scope and final upload gate",
    "Model parameters are missing Stage 9 review details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S9-REVIEW",
      "Memory Atlas v1.1.6 Stage 9 复审",
      "EVID-MA-V116-S9-REVIEW",
      "validate:v1.1.6-stage9",
      "stage_9_review_passed_pending_github_main_upload",
    ]),
    "feature_list_stage9_review",
    "Feature list registers Stage 9 review feature, evidence and validation",
    "Feature list is missing Stage 9 review details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage9_review",
      "MA-V116-S9-REVIEW Stage 9 Review",
      "stage_9_review_passed_pending_github_main_upload",
      "ACC-MA-V116-S9-REVIEW",
      "validate:v1.1.6-stage9",
      "memory_atlas_v1_1_6_stage9_review.md",
    ]),
    "development_record_stage9_review",
    "Development record captures Stage 9 review objective, task, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 9 review details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S9-REVIEW",
      "Stage 9 整体复审",
      "stage_9_review_passed_pending_github_main_upload",
      "validate:v1.1.6-stage9",
      "stage9_c3_review_no_production_import_no_direct_writeback",
    ]),
    "model_index_stage9_review",
    "Root model parameter file records Stage 9 review model and parameters",
    "Root model parameter file is missing Stage 9 review details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 9 Review",
      "memory_atlas_v1_1_6_stage9_review.md",
      "validate:v1.1.6-stage9",
      "stage_9_review_passed_pending_github_main_upload",
      "No production integration",
      "No production UI implementation",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage9_review",
    "Changelog records Stage 9 review artifact, validator and non-goal boundaries",
    "Changelog is missing Stage 9 review details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage9"')
      && packageJson.includes('"validate:v1.1.6-stage9-phase1"')
      && packageJson.includes('"validate:v1.1.6-stage9-phase2"')
      && packageJson.includes('"validate:v1.1.6-stage9-phase3"')
      && packageJson.includes('"validate:v1.1.6-stage9-phase4"')
      && packageJson.includes('"validate:universe-state-spike"'),
    "package_script_stage9_review",
    "Package script exposes Stage 9 review, Stage 9 phase and Universe State validators",
    "Package script is missing Stage 9 review or phase validators",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9.cjs",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/reviews/memory_atlas_v1_1_6_stage9_review.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage9_review_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 9 review, records, validator and package script",
    "Stage 9 review contains out-of-scope OpenAIDatabase changes",
    { changed, outside },
  );
}

function validateBoundary() {
  const status = run("git", ["-c", "core.quotePath=false", "status", "--short"], { cwd: worktreeRoot }).stdout;
  const touchedRuntime = status
    .split("\n")
    .filter((line) => (
      line.includes("OpenAIDatabase/apps/memory-atlas/src/")
        || line.includes("OpenAIDatabase/apps/memory-atlas/dist/")
        || line.includes("OpenAIDatabase/apps/memory-atlas/build/")
        || line.includes("OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/fixtures/universe_state")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/models/universeState.ts")
        || line.includes("OpenAIDatabase/apps/memory-atlas/src/utils/universeStateScores.ts")
        || line.includes("OpenAIDatabase/data/raw/")
        || line.includes("OpenAIDatabase/data/private/")
        || line.includes(".app")
    ));

  assertCondition(
    touchedRuntime.length === 0,
    "stage9_review_boundary",
    "No production runtime UI/CSS/build/app/data/writeback/deploy or Universe State source/sample/parameter work is present in this review",
    "Runtime UI, CSS, build, app bundle, data, writeback, deploy artifact or Universe State model/sample/parameter changed during Stage 9 review",
    { touchedRuntime },
  );
}

function main() {
  try {
    [
      "docs/product/memory_starfield_c3_spike_contract.md",
      "docs/acceptance/memory_starfield_c3_spike_acceptance.md",
      "docs/product/memory_river_c3_spike_contract.md",
      "docs/acceptance/memory_river_c3_spike_acceptance.md",
      "docs/product/data_map_c3_spike_contract.md",
      "docs/acceptance/data_map_c3_spike_acceptance.md",
      "docs/product/universe_state_fixture_continuity_contract.md",
      "docs/acceptance/universe_state_fixture_continuity_acceptance.md",
      "docs/reviews/memory_atlas_v1_1_6_stage9_review.md",
      "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
      "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
      "功能清单.md",
      "开发记录.md",
      "模型参数文件.md",
      "CHANGELOG.md",
    ].forEach(validateTextFile);
    validatePhaseContractSets();
    validateReviewArtifact();
    validateProductionIsolation();
    validateRecords();
    validateChangeScope();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage9", checks }, null, 2));
  } catch (error) {
    checks.push({ name: "failure", status: "FAIL", evidence: error.message, details: error.details || {} });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage9", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
