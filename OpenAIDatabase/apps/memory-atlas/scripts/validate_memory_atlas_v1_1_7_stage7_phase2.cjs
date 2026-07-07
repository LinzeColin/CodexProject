#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S7P02";
const acceptanceId = "ACC-MA-V117-S7P02";
const status = "phase_7_2_review_summary_iteration_runtime_completed_pending_stage7_review";
const validatorName = "validate:v1.1.7-stage7-phase2";
const browserValidatorName = "validate:review-summary-iteration-browser";
const browserValidatorScript = "validate_review_summary_iteration_browser.cjs";
const previousValidatorName = "validate:v1.1.7-stage7-phase1";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage7_phase1.cjs";
const runtimeVersion = "review_summary_iteration_runtime.v1_1_7_stage7_phase2";
const reviewSchemaVersion = "memory_atlas_review_summary.v1_1_7_stage7_phase2";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const contractPath = "docs/product/review_summary_iteration_workflow_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage7_phase2_review_summary_iteration_runtime_acceptance.md";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7_phase2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_review_summary_iteration_browser.cjs",
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

function validateStage7Phase1Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage7_phase2_open_diff_scope",
      "Open diff is limited to Stage 7 Phase 7.2 Review / Summary / Iteration runtime files",
      "Unexpected files changed outside Stage 7 Phase 7.2 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", previousValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[previousValidatorName] === `node scripts/${previousValidatorScript}`,
      "stage7_phase1_validator_registered_for_post_commit_run",
      "Stage 7 Phase 7.1 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 7 Phase 7.1 validator is missing or not registered",
      { script: packageJson.scripts?.[previousValidatorName] },
    );
    pass(
      "stage7_phase1_validator_deferred_until_clean_tree",
      "Stage 7 Phase 7.1 validator enforces its own changed-path scope; rerun this validator after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${previousValidatorScript}`], { cwd: appRoot });
  const parsed = parseValidatorOutput(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S7P01",
    "stage7_phase1_validator",
    "Stage 7 Phase 7.1 validator returned PASS before Stage 7 Phase 7.2 acceptance",
    "Stage 7 Phase 7.1 validator did not return PASS",
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
      `REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION = "${runtimeVersion}"`,
      `REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION = "${reviewSchemaVersion}"`,
      "window.__memoryAtlasStage7Phase2",
      "data-review-summary-iteration-runtime={REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION}",
      "data-review-schema-version={REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION}",
      "data-review-period-selector",
      "data-review-panel=\"theme_change_panel\"",
      "data-review-panel=\"opportunity_panel\"",
      "data-review-panel=\"low_value_loop_panel\"",
      "data-review-panel=\"decision_change_panel\"",
      "data-review-panel=\"next_action_panel\"",
      "data-review-panel=\"proposal_decision_panel\"",
      "data-review-panel=\"iteration_backlog\"",
      "本期主导主题是什么",
      "哪些主题增强",
      "哪些主题衰退",
      "哪些新机会出现",
      "哪些低价值循环出现",
      "哪些决策变化",
      "下一步动作是什么",
      "是否需要生成 proposal",
      "buildReviewSummaryIteration",
      "proposal_candidate",
      "evidence_refs",
      "iteration_backlog",
      "directActiveMemoryWriteback: false",
      "rawPrivateDataIncluded: false",
    ]),
    "stage7_phase2_runtime_contract",
    "Review / Summary / Iteration runtime exposes eight questions, required panels, schema output, iteration backlog and safe debug signal",
    "Review / Summary / Iteration runtime is missing Stage 7 Phase 7.2 hooks",
  );

  assertCondition(
    hasAll(styles, [
      ".review-summary-runtime",
      ".review-period-selector",
      ".review-question-grid",
      ".review-question-card",
      ".review-session-output",
      ".proposal-decision-panel",
      ".iteration-backlog",
    ]),
    "stage7_phase2_review_styles",
    "Review / Summary / Iteration runtime has scoped CSS for selector, question cards, schema output, proposal decision and backlog",
    "Review / Summary / Iteration scoped styles are incomplete",
  );

  assertCondition(
    hasAll(browser, [
      runtimeVersion,
      reviewSchemaVersion,
      "stage7_phase2_browser_runtime_root",
      "stage7_phase2_browser_eight_questions",
      "stage7_phase2_browser_schema_output",
      "stage7_phase2_browser_debug_signal",
      "stage7_phase2_browser_screenshot",
      "stage7_phase2_browser_console",
      "__memoryAtlasStage7Phase2",
      "data-review-panel=\"theme_change_panel\"",
      "data-review-panel=\"proposal_decision_panel\"",
      "data-review-panel=\"iteration_backlog\"",
    ]),
    "stage7_phase2_browser_validator_contract",
    "Browser validator checks runtime root, eight questions, schema output, debug signal, screenshot and console safety",
    "Browser validator is missing Stage 7 Phase 7.2 checks",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7_phase2.cjs",
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage7_phase2.cjs" &&
      packageJson.scripts?.[browserValidatorName] === `node scripts/${browserValidatorScript}`,
    "stage7_phase2_package_scripts",
    "package.json exposes Stage 7 Phase 7.2 static and browser validators",
    "package.json is missing Stage 7 Phase 7.2 validator scripts",
    { staticScript: packageJson.scripts?.[validatorName], browserScript: packageJson.scripts?.[browserValidatorName] },
  );

  assertCondition(
    hasAll(contract, [
      "Memory Atlas v1.1.7 Stage 7 Phase 7.2 Runtime Addendum",
      taskId,
      acceptanceId,
      status,
      runtimeVersion,
      reviewSchemaVersion,
      "review_period_selector",
      "theme_change_panel",
      "opportunity_panel",
      "low_value_loop_panel",
      "decision_change_panel",
      "next_action_panel",
      "proposal_decision_panel",
      "iteration_backlog",
      "proposal-only",
      "No Stage 8 summary closure",
      "No direct active-memory writeback",
      "No GitHub main upload",
    ]),
    "stage7_phase2_contract_addendum",
    "Review/Summary/Iteration contract has the v1.1.7 runtime addendum, boundaries and acceptance hooks",
    "Review/Summary/Iteration contract addendum is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 7 Phase 7.2 Review Summary Iteration Runtime Acceptance",
      taskId,
      acceptanceId,
      status,
      runtimeVersion,
      reviewSchemaVersion,
      validatorName,
      browserValidatorName,
      "review_period_selector",
      "theme_change_panel",
      "opportunity_panel",
      "low_value_loop_panel",
      "decision_change_panel",
      "next_action_panel",
      "proposal_decision_panel",
      "iteration_backlog",
      "No Stage 8 summary closure",
      "No raw/private/cookie/session/secret data access",
      "No direct active-memory writeback",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage7_phase2_acceptance",
    "Stage 7 Phase 7.2 acceptance pins runtime, browser, safety and upload boundaries",
    "Stage 7 Phase 7.2 acceptance is incomplete",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        runtimeVersion,
        reviewSchemaVersion,
        validatorName,
        browserValidatorName,
        "Review / Summary / Iteration",
        "proposal_candidate",
        "iteration_backlog",
        "No Stage 8 summary closure",
        "No GitHub main upload",
      ]),
      `stage7_phase2_records_${name}`,
      `${name} records Stage 7 Phase 7.2 Review/Summary/Iteration runtime status, validators, boundaries and next gate`,
      `${name} is missing Stage 7 Phase 7.2 record fragments`,
    );
  }
}

function validateGitBoundary() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName,
    "stage7_phase2_local_branch",
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
    "stage7_phase2_no_remote_branch",
    "No remote Stage 0-10 development branch exists; intermediate work remains local only",
    "Remote development branch exists or could not be checked",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function main() {
  validateStage7Phase1Continuity();
  validateRuntimeAndBrowserContract();
  validateDocsAndRecords();
  validateGitBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_1_7_stage7_phase2",
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
    validator: "validate_memory_atlas_v1_1_7_stage7_phase2",
    task_id: taskId,
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
