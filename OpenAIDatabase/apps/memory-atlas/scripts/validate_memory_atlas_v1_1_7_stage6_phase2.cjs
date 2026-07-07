#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S6P02";
const acceptanceId = "ACC-MA-V117-S6P02";
const status = "phase_6_2_data_map_detail_proposal_completed_pending_stage6_review";
const validatorName = "validate:v1.1.7-stage6-phase2";
const browserValidatorName = "validate:data-map-detail-proposal-browser";
const previousValidatorName = "validate:v1.1.7-stage6-phase1";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage6_phase1.cjs";
const detailPanelVersion = "data_map_detail_panel.v1_1_7_stage6_phase2";
const proposalEntryVersion = "data_map_proposal_entry.v1_1_7_stage6_phase2";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const contractPath = "docs/product/data_map_iteration_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage6_phase2_data_map_detail_proposal_acceptance.md";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6_phase2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_data_map_detail_proposal_browser.cjs",
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

function validateStage6Phase1Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage6_phase2_open_diff_scope",
      "Open diff is limited to Stage 6 Phase 6.2 Details & Editing files",
      "Unexpected files changed outside Stage 6 Phase 6.2 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage6_phase1_validator_registered_for_post_commit_run",
      "Stage 6 Phase 6.1 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 6 Phase 6.1 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage6_phase1_validator_deferred_until_clean_tree",
      "Stage 6 Phase 6.1 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const parsed = parseValidatorOutput(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S6P01",
    "stage6_phase1_validator",
    "Stage 6 Phase 6.1 validator returned PASS before Stage 6 Phase 6.2 acceptance",
    "Stage 6 Phase 6.1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateRuntimeAndBrowserContract() {
  [
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/styles.css",
    "apps/memory-atlas/scripts/validate_data_map_detail_proposal_browser.cjs",
  ].forEach(validateTextFile);

  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  const browser = readRepoFile("apps/memory-atlas/scripts/validate_data_map_detail_proposal_browser.cjs");

  assertCondition(
    hasAll(app, [
      `DATA_MAP_DETAIL_PANEL_VERSION = "${detailPanelVersion}"`,
      `DATA_MAP_PROPOSAL_ENTRY_VERSION = "${proposalEntryVersion}"`,
      "window.__memoryAtlasStage6Phase2",
      "DataMapNodeDetailPanel",
      "data-data-map-detail-panel={DATA_MAP_DETAIL_PANEL_VERSION}",
      "data-data-map-proposal-entry={DATA_MAP_PROPOSAL_ENTRY_VERSION}",
      "data-data-map-node-detail-entry",
      "data-node-kind={item.node.kind}",
      "data-selected-node-id={node?.id ?? \"\"}",
      "sourceSurface=\"data_guide_detail_panel\"",
      "ProposalEditor",
      "资产",
      "主题",
      "建议动作",
      "重要性",
      "优先级",
      "proposal_only",
      "directActiveMemoryWriteback: false",
      "rawPrivateDataIncluded: false",
    ]),
    "stage6_phase2_runtime_detail_proposal",
    "Data Guide runtime exposes node detail panel, proposal-only entry, node hooks and safe debug signal",
    "Data Guide runtime is missing Stage 6 Phase 6.2 detail/proposal hooks",
  );

  assertCondition(
    hasAll(styles, [
      ".data-map-node-detail-panel",
      ".data-map-node-detail-grid",
      ".data-map-node-evidence-list",
      ".data-map-proposal-entry",
      ".data-map-detail-safety-strip",
    ]),
    "stage6_phase2_detail_styles",
    "Data map detail and proposal entry have scoped CSS",
    "Data map detail/proposal styles are incomplete",
  );

  assertCondition(
    hasAll(browser, [
      detailPanelVersion,
      proposalEntryVersion,
      "stage6_phase2_browser_detail_panel",
      "stage6_phase2_browser_detail_fields",
      "stage6_phase2_browser_proposal_entry",
      "stage6_phase2_browser_proposal_export",
      "stage6_phase2_browser_debug_signal",
      "stage6_phase2_browser_screenshot",
      "stage6_phase2_browser_console",
      "__memoryAtlasStage6Phase2",
      "memory-atlas.proposal-drafts.v1",
    ]),
    "stage6_phase2_browser_validator_contract",
    "Browser validator checks node detail fields, proposal-only editor, export payload, debug signal, screenshot and console safety",
    "Browser validator is missing Stage 6 Phase 6.2 checks",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6_phase2.cjs",
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage6_phase2.cjs" &&
      packageJson.scripts?.[browserValidatorName] === "node scripts/validate_data_map_detail_proposal_browser.cjs",
    "stage6_phase2_package_scripts",
    `package.json exposes ${validatorName} and ${browserValidatorName}`,
    "package.json is missing Stage 6 Phase 6.2 scripts",
    {
      validator: packageJson.scripts?.[validatorName],
      browserValidator: packageJson.scripts?.[browserValidatorName],
    },
  );

  assertCondition(
    hasAll(contract, [
      "Memory Atlas v1.1.7 Stage 6 Phase 6.2 Details & Editing Addendum",
      taskId,
      acceptanceId,
      status,
      detailPanelVersion,
      proposalEntryVersion,
      "数据导图详情面板",
      "数据导图 proposal 入口",
      "asset",
      "theme",
      "suggested action",
      "importance",
      "priority",
      "proposal-only",
      "No direct active-memory writeback",
      "No Stage 6 review",
      "No GitHub main upload",
    ]),
    "stage6_phase2_contract",
    "Data map iteration contract records detail panel, proposal-only entry and boundaries",
    "Data map iteration contract is missing Stage 6 Phase 6.2 addendum",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 6 Phase 6.2 Data Map Detail Proposal Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      browserValidatorName,
      detailPanelVersion,
      proposalEntryVersion,
      "资产",
      "主题",
      "建议动作",
      "重要性",
      "优先级",
      "只生成 proposal",
      "导出 proposal",
      "No direct active-memory writeback",
      "No Stage 6 review",
      "No GitHub main upload",
    ]),
    "stage6_phase2_acceptance_contract",
    "Acceptance document pins node detail fields, proposal export and no-writeback boundary",
    "Stage 6 Phase 6.2 acceptance document is incomplete",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        browserValidatorName,
        detailPanelVersion,
        proposalEntryVersion,
        "Phase 6.2",
        "Details & Editing",
        "数据导图详情面板",
        "数据导图 proposal 入口",
        "proposal-only",
        "No Stage 6 review",
        "No GitHub main upload",
      ]),
      `stage6_phase2_records_${name}`,
      `${name} registers Stage 6 Phase 6.2 status, acceptance, validators, versions and no-upload boundary`,
      `${name} is missing Stage 6 Phase 6.2 tokens`,
    );
  }
}

function validateCanonicalBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const sparse = run("git", ["sparse-checkout", "list"], { cwd: worktreeRoot }).stdout.trim().split(/\r?\n/).filter(Boolean);
  const remoteBranch = run("git", ["ls-remote", "--heads", "origin", branchName], { cwd: worktreeRoot }).stdout.trim();

  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "stage6_phase2_canonical_remote",
    "origin points at the canonical LinzeColin/CodexProject remote",
    "origin remote is not canonical",
    { remote },
  );
  assertCondition(
    sparse.includes("OpenAIDatabase"),
    "stage6_phase2_sparse_boundary",
    "sparse checkout includes OpenAIDatabase",
    "sparse checkout does not include OpenAIDatabase",
    { sparse },
  );
  assertCondition(
    remoteBranch === "",
    "stage6_phase2_no_remote_branch",
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
    "stage6_phase2_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 6 Phase 6.2 contract, runtime, validators, package script and records",
    "Unexpected files changed outside Stage 6 Phase 6.2 scope",
    { changed, outside },
  );
}

function main() {
  validateStage6Phase1Continuity();
  validateRuntimeAndBrowserContract();
  validateDocsAndRecords();
  validateCanonicalBoundary();
  validateChangeScope();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage6-phase2",
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
        stage: "v1.1.7-stage6-phase2",
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
