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

function validateProductContract() {
  const contract = readRepoFile("docs/product/memory_starfield_rebuild_contract.md");
  assertCondition(
    hasAll(contract, [
      "Memory Atlas 记忆星系重做合同",
      "v1.1.6 Stage 7 Phase 1",
      "memory_starfield_rebuild_contract",
      "MA-V116-S7P01",
      "phase_7_1_contract_created_pending_stage_review",
      "plain node graph",
      "Obsidian-like",
      "dots-and-lines",
      "memory_starfield",
      "nebula_field",
      "flow_field",
      "trajectory_trails",
      "gravity_sources",
      "black_hole_core",
      "proto_star_cloud",
      "memory_terrain_layer",
      "cluster_constellations",
      "ambient_depth_particles",
      "orbit_pan_zoom",
      "hover_card",
      "click_inspector",
      "focus_cluster",
      "jump_from_search",
      "jump_from_river",
      "presentation_analysis_toggle",
      "keyboard_navigation",
      "reduced_motion",
      "starfield_item_id",
      "gravity_mass",
      "orbit_radius",
      "trajectory_refs",
      "terrain_value",
      "linked_river_range",
      "inspector_link",
      "proposal_hint",
      "only dots",
      "nodes and edges",
      "generic Obsidian Graph",
      "WebGL failure",
      "redacted_summary_only",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No experiment directory import",
      "No feature flag default switch",
      "No GitHub main upload",
      "本 phase 不修改运行时",
    ]),
    "stage7_phase1_product_contract",
    "Memory Starfield rebuild contract covers visual layers, interactions, item fields, anti-regression rules and safety boundaries",
    "Memory Starfield rebuild product contract is incomplete",
  );
}

function validateAcceptanceContract() {
  const acceptance = readRepoFile("docs/acceptance/memory_starfield_rebuild_acceptance.md");
  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas 记忆星系重做验收",
      "v1.1.6 Stage 7 Phase 1",
      "memory_starfield_rebuild_contract",
      "MA-V116-S7P01",
      "phase_7_1_contract_created_pending_stage_review",
      "memory_starfield",
      "nebula_field",
      "flow_field",
      "trajectory_trails",
      "gravity_sources",
      "black_hole_core",
      "proto_star_cloud",
      "memory_terrain_layer",
      "cluster_constellations",
      "ambient_depth_particles",
      "orbit_pan_zoom",
      "hover_card",
      "click_inspector",
      "focus_cluster",
      "jump_from_search",
      "jump_from_river",
      "presentation_analysis_toggle",
      "keyboard_navigation",
      "reduced_motion",
      "starfield_item_id",
      "item_type",
      "gravity_mass",
      "trajectory_refs",
      "terrain_value",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "Nonblank WebGL canvas",
      "only points",
      "node-link edges",
      "generic Obsidian Graph",
      "validate:v1.1.6-stage7-phase1",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "stage7_phase1_acceptance_contract",
    "Memory Starfield rebuild acceptance covers required layers, interactions, data fields, responsive evidence, failure states and safety boundaries",
    "Memory Starfield rebuild acceptance contract is incomplete",
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
      "Stage 7 Phase 1",
      "Memory Starfield Rebuild Contract",
      "memory_starfield_rebuild_contract",
      "validate:v1.1.6-stage7-phase1",
      "phase_7_1_contract_created_pending_stage_review",
      "MA-V116-S7P01",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "delivery_record_stage7_phase1",
    "Delivery record captures Stage 7 Phase 1 scope, validator, status and no-upload boundary",
    "Delivery record is missing Stage 7 Phase 1 details",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 7 Phase 1 记忆星系重做参数",
      "memory_starfield_rebuild_contract",
      "phase_7_1_contract_created_pending_stage_review",
      "PARAM-MA-V116-S7P01-001",
      "PARAM-MA-V116-S7P01-002",
      "PARAM-MA-V116-S7P01-003",
      "PARAM-MA-V116-S7P01-004",
      "PARAM-MA-V116-S7P01-005",
      "PARAM-MA-V116-S7P01-006",
      "PARAM-MA-V116-S7P01-007",
    ]),
    "model_parameters_stage7_phase1",
    "Model parameters document Stage 7 Phase 1 layers, interactions, fields, anti-regression rules, safety and validator",
    "Model parameters are missing Stage 7 Phase 1 details",
  );

  assertCondition(
    hasAll(featureList, [
      "FEAT-MA-V116-S7P01",
      "Memory Atlas v1.1.6 Stage 7 Phase 1",
      "记忆星系重做合同",
      "EVID-MA-V116-S7P01",
      "validate:v1.1.6-stage7-phase1",
      "phase_7_1_contract_created_pending_stage_review",
    ]),
    "feature_list_stage7_phase1",
    "Feature list registers Stage 7 Phase 1 feature, evidence and validation",
    "Feature list is missing Stage 7 Phase 1 details",
  );

  assertCondition(
    hasAll(development, [
      "memory_atlas_v116_stage7_phase01",
      "MA-V116-S7P01",
      "Memory Starfield Rebuild Contract",
      "phase_7_1_contract_created_pending_stage_review",
      "ACC-MA-V116-S7P01",
      "validate:v1.1.6-stage7-phase1",
      "memory_starfield_rebuild_contract.md",
      "memory_starfield_rebuild_acceptance.md",
    ]),
    "development_record_stage7_phase1",
    "Development record captures Stage 7 Phase 1 objective, tasks, acceptance, evidence, risk and rollback",
    "Development record is missing Stage 7 Phase 1 details",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MA-V116-S7P01",
      "记忆星系重做",
      "memory_starfield_rebuild_contract",
      "phase_7_1_contract_created_pending_stage_review",
      "validate:v1.1.6-stage7-phase1",
      "memory_starfield_no_raw_private_payload",
    ]),
    "model_index_stage7_phase1",
    "Root model parameter file records Stage 7 Phase 1 model and parameters",
    "Root model parameter file is missing Stage 7 Phase 1 details",
  );

  assertCondition(
    hasAll(changelog, [
      "Unreleased - Memory Atlas v1.1.6 Stage 7 Phase 1",
      "Memory Starfield Rebuild Contract",
      "memory_starfield_rebuild_contract.md",
      "memory_starfield_rebuild_acceptance.md",
      "validate:v1.1.6-stage7-phase1",
      "phase_7_1_contract_created_pending_stage_review",
      "No runtime UI",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage7_phase1",
    "Changelog records Stage 7 Phase 1 deliverables and non-goal boundaries",
    "Changelog is missing Stage 7 Phase 1 details",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.6-stage7-phase1"'),
    "package_script_stage7_phase1",
    "Package script exposes validate:v1.1.6-stage7-phase1",
    "Package script validate:v1.1.6-stage7-phase1 is missing",
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
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/product/memory_starfield_rebuild_contract.md",
    "docs/acceptance/memory_starfield_rebuild_acceptance.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage7_phase1.cjs",
  ];

  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage7_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 7 Phase 1 contracts, records, validator and package script",
    "Stage 7 Phase 1 contains out-of-scope OpenAIDatabase changes",
    { changed, outside },
  );
}

function validateBoundary() {
  const status = run("git", ["-c", "core.quotePath=false", "status", "--short"], { cwd: worktreeRoot }).stdout;
  assertCondition(
    !status.includes("src/App.tsx")
      && !status.includes("src/styles.css")
      && !status.includes("src/components/")
      && !status.includes("src/experiments/")
      && !status.includes("data/processed/")
      && !status.includes("data/raw/")
      && !status.includes("data/private/"),
    "stage7_phase1_boundary",
    "No runtime UI/CSS/component/experiment/raw-private data change is present in this contract phase",
    "Runtime UI, CSS, component, experiment or raw/private data changed during Stage 7 Phase 1",
  );
}

function main() {
  try {
    [
      "docs/product/memory_starfield_rebuild_contract.md",
      "docs/acceptance/memory_starfield_rebuild_acceptance.md",
      "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
      "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
      "功能清单.md",
      "开发记录.md",
      "模型参数文件.md",
      "CHANGELOG.md",
    ].forEach(validateTextFile);
    validateProductContract();
    validateAcceptanceContract();
    validateRecords();
    validateChangeScope();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage7-phase1", checks }, null, 2));
  } catch (error) {
    checks.push({ name: "failure", status: "FAIL", evidence: error.message, details: error.details || {} });
    console.error(JSON.stringify({ status: "FAIL", stage: "v1.1.6-stage7-phase1", error: error.message, details: error.details || {}, checks }, null, 2));
    process.exit(1);
  }
}

main();
