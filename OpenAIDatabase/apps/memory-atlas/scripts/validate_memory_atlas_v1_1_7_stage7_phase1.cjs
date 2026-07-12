#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S7P01";
const acceptanceId = "ACC-MA-V117-S7P01";
const status = "phase_7_1_search_2_0_runtime_completed_pending_stage7_review";
const validatorName = "validate:v1.1.7-stage7-phase1";
const browserValidatorName = "validate:search-2-0-browser";
const browserValidatorScript = "validate_search_2_0_browser.cjs";
const previousValidatorName = "validate:v1.1.7-stage6";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage6.cjs";
const runtimeVersion = "search_2_0_runtime.v1_1_7_stage7_phase1";
const sessionSummaryVersion = "search_2_0_session_summary.v1_1_7_stage7_phase1";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const contractPath = "docs/product/search_2_0_workflow_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage7_phase1_search_2_0_runtime_acceptance.md";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7_phase1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_search_2_0_browser.cjs",
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

function validateStage6Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage7_phase1_open_diff_scope",
      "Open diff is limited to Stage 7 Phase 7.1 Search 2.0 runtime files",
      "Unexpected files changed outside Stage 7 Phase 7.1 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage6_validator_registered_for_post_commit_run",
      "Stage 6 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 6 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage6_validator_deferred_until_clean_tree",
      "Stage 6 validator enforces its own changed-path scope; rerun this validator after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const parsed = parseValidatorOutput(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S6-REVIEW",
    "stage6_validator",
    "Stage 6 validator returned PASS before Stage 7 Phase 7.1 acceptance",
    "Stage 6 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateRuntimeAndBrowserContract() {
  [
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/styles.css",
    `apps/memory-atlas/scripts/${browserValidatorScript}`,
  ].forEach(validateTextFile);

  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  const browser = readRepoFile(`apps/memory-atlas/scripts/${browserValidatorScript}`);

  assertCondition(
    hasAll(app, [
      `SEARCH_2_0_RUNTIME_VERSION = "${runtimeVersion}"`,
      `SEARCH_2_0_SESSION_SUMMARY_VERSION = "${sessionSummaryVersion}"`,
      "window.__memoryAtlasStage7Phase1",
      "data-nav-view={view.key}",
      "data-search-2-0-runtime={SEARCH_2_0_RUNTIME_VERSION}",
      "data-search-session-summary={SEARCH_2_0_SESSION_SUMMARY_VERSION}",
      "data-search-query-input",
      "data-search-filter-state",
      "data-search-result",
      "data-matched-reason",
      "data-evidence-ref",
      "data-search-jump=\"starfield\"",
      "data-search-jump=\"river\"",
      "data-search-jump=\"inspector\"",
      "data-zero-result-recovery",
      "proposal_candidate",
      "buildSearch2Results",
      "buildSearch2SessionSummary",
      "directActiveMemoryWriteback: false",
      "rawPrivateDataIncluded: false",
    ]),
    "stage7_phase1_runtime_contract",
    "Search 2.0 runtime exposes query/filter/result/session/zero-result hooks, jump actions and safe debug signal",
    "Search 2.0 runtime is missing Stage 7 Phase 7.1 hooks",
  );

  assertCondition(
    hasAll(styles, [
      ".search-2-runtime",
      ".search-2-controls",
      ".search-2-filter-grid",
      ".search-2-result-card",
      ".search-2-result-actions",
      ".search-2-session-summary",
      ".search-2-zero-recovery",
    ]),
    "stage7_phase1_search_styles",
    "Search 2.0 runtime has scoped CSS for controls, results, actions, summary and zero-result recovery",
    "Search 2.0 scoped styles are incomplete",
  );

  assertCondition(
    hasAll(browser, [
      runtimeVersion,
      sessionSummaryVersion,
      "stage7_phase1_browser_runtime_root",
      "stage7_phase1_browser_result_fields",
      "stage7_phase1_browser_debug_signal",
      "stage7_phase1_browser_zero_recovery",
      "stage7_phase1_browser_jump_starfield",
      "stage7_phase1_browser_jump_river",
      "stage7_phase1_browser_open_inspector",
      "stage7_phase1_browser_screenshot",
      "stage7_phase1_browser_console",
      "__memoryAtlasStage7Phase1",
      "data-search-jump=\"starfield\"",
      "data-search-jump=\"river\"",
      "data-search-jump=\"inspector\"",
    ]),
    "stage7_phase1_browser_validator_contract",
    "Browser validator checks runtime root, result fields, debug signal, zero-result recovery, three jumps, screenshot and console safety",
    "Browser validator is missing Stage 7 Phase 7.1 checks",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7_phase1.cjs",
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage7_phase1.cjs" &&
      packageJson.scripts?.[browserValidatorName] === `node scripts/${browserValidatorScript}`,
    "stage7_phase1_package_scripts",
    "package.json exposes Stage 7 Phase 7.1 static and browser validators",
    "package.json is missing Stage 7 Phase 7.1 validator scripts",
    { staticScript: packageJson.scripts?.[validatorName], browserScript: packageJson.scripts?.[browserValidatorName] },
  );

  assertCondition(
    hasAll(contract, [
      "Memory Atlas v1.1.7 Stage 7 Phase 7.1 Runtime Addendum",
      taskId,
      acceptanceId,
      status,
      runtimeVersion,
      sessionSummaryVersion,
      "query_input",
      "filter_state",
      "result_list",
      "matched_reason",
      "evidence_refs",
      "jump_to_starfield",
      "jump_to_river",
      "open_inspector",
      "search_session_summary",
      "zero_result_recovery",
      "proposal-only",
      "No Review / Summary / Iteration runtime",
      "No direct active-memory writeback",
      "No GitHub main upload",
    ]),
    "stage7_phase1_contract_addendum",
    "Search 2.0 contract has the v1.1.7 runtime addendum, boundaries and acceptance hooks",
    "Search 2.0 contract addendum is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 7 Phase 7.1 Search 2.0 Runtime Acceptance",
      taskId,
      acceptanceId,
      status,
      runtimeVersion,
      sessionSummaryVersion,
      validatorName,
      browserValidatorName,
      "matched_reason",
      "evidence_refs",
      "jump_to_starfield",
      "jump_to_river",
      "open_inspector",
      "zero_result_recovery",
      "No Review / Summary / Iteration runtime",
      "No raw/private/cookie/session/secret data access",
      "No direct active-memory writeback",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage7_phase1_acceptance",
    "Stage 7 Phase 7.1 acceptance pins runtime, browser, safety and upload boundaries",
    "Stage 7 Phase 7.1 acceptance is incomplete",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        runtimeVersion,
        sessionSummaryVersion,
        validatorName,
        browserValidatorName,
        "Search 2.0",
        "matched_reason",
        "evidence_refs",
        "No Review / Summary / Iteration runtime",
        "No GitHub main upload",
      ]),
      `stage7_phase1_records_${name}`,
      `${name} records Stage 7 Phase 7.1 Search 2.0 runtime status, validators, boundaries and next gate`,
      `${name} is missing Stage 7 Phase 7.1 record fragments`,
    );
  }
}

function validateGitBoundary() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName,
    "stage7_phase1_local_branch",
    `Current branch is ${branchName}`,
    `Current branch must remain ${branchName}`,
    { branch },
  );

  const remoteBranch = spawnSync("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    encoding: "utf8",
    stdio: "pipe",
  });
  assertCondition(
    remoteBranch.status === 0 && remoteBranch.stdout.trim() === "",
    "stage7_phase1_no_remote_branch",
    "No remote Stage 0-10 development branch exists; intermediate work remains local only",
    "Remote development branch exists or could not be checked",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function main() {
  validateStage6Continuity();
  validateRuntimeAndBrowserContract();
  validateDocsAndRecords();
  validateGitBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_1_7_stage7_phase1",
    task_id: taskId,
    acceptance_id: acceptanceId,
    checks,
  }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_memory_atlas_v1_1_7_stage7_phase1",
    task_id: taskId,
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
