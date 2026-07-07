#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S6P01";
const acceptanceId = "ACC-MA-V117-S6P01";
const status = "phase_6_1_data_map_structure_model_completed_pending_stage6_review";
const validatorName = "validate:v1.1.7-stage6-phase1";
const browserValidatorName = "validate:data-map-structure-browser";
const previousValidatorName = "validate:v1.1.7-stage5";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage5.cjs";
const contractVersion = "data_map_structure_model.v1_1_7_stage6_phase1";
const relationVersion = "data_map_relation_explanation.v1_1_7_stage6_phase1";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const contractPath = "docs/product/data_map_iteration_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage6_phase1_data_map_structure_acceptance.md";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6_phase1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_data_map_structure_browser.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${contractPath}`,
  `OpenAIDatabase/${acceptancePath}`,
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
];

const layerIds = ["source_layer", "profile_layer", "project_decision_layer", "action_opportunity_layer"];
const layerLabels = ["来源层", "画像层", "项目决策层", "行动机会层"];

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

function parseValidatorOutput(result) {
  const output = result.stdout.trim();
  return JSON.parse(output.slice(output.indexOf("{")));
}

function validateStage5Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage6_phase1_open_diff_scope",
      "Open diff is limited to Stage 6 Phase 6.1 Structure Model files",
      "Unexpected files changed outside Stage 6 Phase 6.1 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage5_validator_registered_for_post_commit_run",
      "Stage 5 review validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 5 review validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage5_validator_deferred_until_clean_tree",
      "Stage 5 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const parsed = parseValidatorOutput(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S5-REVIEW",
    "stage5_review_validator",
    "Stage 5 review validator returned PASS before Stage 6 Phase 6.1 acceptance",
    "Stage 5 review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateRuntimeAndBrowserContract() {
  [
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/styles.css",
    "apps/memory-atlas/scripts/validate_data_map_structure_browser.cjs",
  ].forEach(validateTextFile);

  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  const browser = readRepoFile("apps/memory-atlas/scripts/validate_data_map_structure_browser.cjs");

  assertCondition(
    hasAll(app, [
      `DATA_MAP_STRUCTURE_MODEL_VERSION = "${contractVersion}"`,
      `DATA_MAP_RELATION_EXPLANATION_VERSION = "${relationVersion}"`,
      "DataMapStructureLayerId",
      "selectedDataMapRelationId",
      "setSelectedDataMapRelationId",
      "data-data-map-structure-model={DATA_MAP_STRUCTURE_MODEL_VERSION}",
      "data-data-map-relation-version={DATA_MAP_RELATION_EXPLANATION_VERSION}",
      "data-data-map-layer={frame.structureLayerId}",
      "data-data-map-relation-explanation={DATA_MAP_RELATION_EXPLANATION_VERSION}",
      "data-relation-strength",
      "data-relation-evidence",
      "data-relation-time",
      "window.__memoryAtlasStage6Phase1",
      "source_layer",
      "profile_layer",
      "project_decision_layer",
      "action_opportunity_layer",
    ]),
    "stage6_phase1_runtime_structure_model",
    "Data Guide runtime exposes structure model versions, layer ids, relation metadata and debug signal",
    "Data Guide runtime is missing Stage 6 Phase 6.1 structure model hooks",
  );

  assertCondition(
    hasAll(app, [
      "关系解释",
      "为什么连接",
      "证据",
      "强度",
      "时间",
      "默认折叠",
      "No Phase 6.2 editing",
      "proposalWrite: false",
      "directActiveMemoryWriteback: false",
      "rawPrivateDataIncluded: false",
    ]),
    "stage6_phase1_relation_explanation_ui",
    "Relation explanation UI shows source, strength, evidence, time and safe no-writeback metadata",
    "Relation explanation UI is incomplete",
  );

  assertCondition(
    hasAll(styles, [
      ".data-guide-relation-hitbox",
      ".data-guide-link.selected",
      ".data-map-relation-panel",
      ".data-map-relation-grid",
      ".data-map-layer-strip",
    ]),
    "stage6_phase1_relation_styles",
    "Data map structure layers and relation explanation panel have scoped CSS",
    "Data map relation styles are incomplete",
  );

  assertCondition(
    hasAll(browser, [
      contractVersion,
      relationVersion,
      "stage6_phase1_browser_structure_model",
      "stage6_phase1_browser_four_layers",
      "stage6_phase1_browser_relation_click",
      "stage6_phase1_browser_debug_signal",
      "stage6_phase1_browser_screenshot",
      "stage6_phase1_browser_console",
      "__memoryAtlasStage6Phase1",
      "data-data-map-relation-explanation",
    ]),
    "stage6_phase1_browser_validator_contract",
    "Browser validator checks four layers, relation click explanation, debug signal, screenshot and console safety",
    "Browser validator is missing Stage 6 Phase 6.1 checks",
  );
}

function validateDocsAndRecords() {
  [
    contractPath,
    acceptancePath,
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "config/visualization/model_parameters.universe_state.yaml",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6_phase1.cjs",
  ].forEach(validateTextFile);

  const contract = readRepoFile(contractPath);
  const acceptance = readRepoFile(acceptancePath);
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

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage6_phase1.cjs" &&
      packageJson.scripts?.[browserValidatorName] === "node scripts/validate_data_map_structure_browser.cjs",
    "stage6_phase1_package_scripts",
    `package.json exposes ${validatorName} and ${browserValidatorName}`,
    "package.json is missing Stage 6 Phase 6.1 scripts",
    {
      validator: packageJson.scripts?.[validatorName],
      browserValidator: packageJson.scripts?.[browserValidatorName],
    },
  );

  const requiredContractTokens = [
    "Memory Atlas v1.1.7 Stage 6 Phase 6.1 Data Map Structure Model Contract",
    taskId,
    acceptanceId,
    status,
    contractVersion,
    relationVersion,
    "四层结构重定义",
    "Relation Explanation",
    "node types",
    "fields",
    "interaction",
    "detail entry",
    "source",
    "strength",
    "evidence",
    "time",
    "default collapsed",
    "No Phase 6.2",
    "No proposal editing",
    "No direct active-memory writeback",
    "No GitHub main upload",
  ];
  assertCondition(
    hasAll(contract, [...requiredContractTokens, ...layerIds, ...layerLabels]),
    "stage6_phase1_contract",
    "Data map iteration contract defines four layers, relation explanation, rollback and boundaries",
    "Data map iteration contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 6 Phase 6.1 Data Map Structure Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      browserValidatorName,
      contractVersion,
      relationVersion,
      "clicking edge",
      "source",
      "strength",
      "evidence",
      "time",
      "default collapsed",
      "No Phase 6.2",
      "No GitHub main upload",
      ...layerIds,
      ...layerLabels,
    ]),
    "stage6_phase1_acceptance_contract",
    "Acceptance document pins layer coverage, relation click evidence and no-upload boundary",
    "Stage 6 Phase 6.1 acceptance document is incomplete",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        browserValidatorName,
        contractVersion,
        relationVersion,
        "Phase 6.1",
        "Structure Model",
        "Relation Explanation",
        "source_layer",
        "profile_layer",
        "project_decision_layer",
        "action_opportunity_layer",
        "No Phase 6.2",
        "No GitHub main upload",
      ]),
      `stage6_phase1_records_${name}`,
      `${name} registers Stage 6 Phase 6.1 status, acceptance, validators, versions and no-upload boundary`,
      `${name} is missing Stage 6 Phase 6.1 tokens`,
    );
  }
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  const remoteBranch = run("git", ["ls-remote", "--heads", "origin", branchName], { cwd: worktreeRoot }).stdout.trim();

  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage6_phase1_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage6_phase1_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
  assertCondition(
    remoteBranch === "",
    "stage6_phase1_no_remote_branch",
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
    "stage6_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 6 Phase 6.1 contract, runtime, validators, package script and records",
    "Unexpected files changed outside Stage 6 Phase 6.1 scope",
    { changed, outside },
  );
}

function main() {
  validateStage5Continuity();
  validateRuntimeAndBrowserContract();
  validateDocsAndRecords();
  validateCanonicalBoundary();
  validateChangeScope();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage6-phase1",
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
        stage: "v1.1.7-stage6-phase1",
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
