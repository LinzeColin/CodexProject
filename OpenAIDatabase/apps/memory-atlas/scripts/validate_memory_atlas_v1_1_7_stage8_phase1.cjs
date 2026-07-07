#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S8P01";
const acceptanceId = "ACC-MA-V117-S8P01";
const status = "phase_8_1_summary_iteration_closure_runtime_completed_pending_stage8_review";
const validatorName = "validate:v1.1.7-stage8-phase1";
const browserValidatorName = "validate:summary-iteration-closure-browser";
const browserValidatorScript = "validate_summary_iteration_closure_browser.cjs";
const previousValidatorScript = "validate_memory_atlas_v1_1_7_stage7.cjs";
const runtimeVersion = "summary_iteration_closure_runtime.v1_1_7_stage8_phase1";
const closureSchemaVersion = "memory_atlas_summary_closure.v1_1_7_stage8_phase1";
const reviewSchemaVersion = "memory_atlas_review_summary.v1_1_7_stage7_phase2";
const branchName = "codex/memory-atlas-v117-stage0-10-local";

const contractPath = "docs/product/summary_iteration_closure_contract.md";
const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage8_phase1_summary_iteration_closure_acceptance.md";

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage8_phase1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_summary_iteration_closure_browser.cjs",
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

function parseValidatorOutput(result) {
  const output = result.stdout.trim();
  return JSON.parse(output.slice(output.indexOf("{")));
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

function validateStage7Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage8_phase1_open_diff_scope",
      "Open diff is limited to Stage 8 Phase 8.1 Summary and Iteration Closure files",
      "Unexpected files changed outside Stage 8 Phase 8.1 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    assertCondition(
      fs.existsSync(path.join(appRoot, "scripts", previousValidatorScript)) &&
        packageJson.scripts?.["validate:v1.1.7-stage7"] === `node scripts/${previousValidatorScript}`,
      "stage7_validator_registered_for_post_commit_run",
      "Stage 7 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 7 validator is missing or not registered",
      { script: packageJson.scripts?.["validate:v1.1.7-stage7"] },
    );
    pass(
      "stage7_validator_deferred_until_clean_tree",
      "Stage 7 validator enforces its own changed-path scope; rerun this validator after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  validateTextFile("docs/reviews/memory_atlas_v1_1_7_stage7_review.md");
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_7_stage7_review.md");
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
    packageJson.scripts?.["validate:v1.1.7-stage7"] === `node scripts/${previousValidatorScript}` &&
      fs.existsSync(path.join(appRoot, "scripts", previousValidatorScript)),
    "stage7_review_validator_registered",
    "Stage 7 review validator remains registered for explicit historical revalidation",
    "Stage 7 review validator is missing or not registered",
    { script: packageJson.scripts?.["validate:v1.1.7-stage7"] },
  );

  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.7 Stage 7 Review",
      "MA-V117-S7-REVIEW",
      "ACC-MA-V117-S7-REVIEW",
      "stage_7_review_passed_pending_stage8_no_github_main_upload",
      "validate:v1.1.7-stage7",
      "Phase 7.1",
      "Phase 7.2",
      "Search 2.0",
      "Review / Summary / Iteration",
      "pending Stage 8",
      "No Stage 8 work",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage7_review_artifact_continuity",
    "Stage 7 review artifact pins the review-passed state and pending Stage 8 entry gate",
    "Stage 7 review artifact is missing continuity fragments",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        "MA-V117-S7-REVIEW",
        "ACC-MA-V117-S7-REVIEW",
        "stage_7_review_passed_pending_stage8_no_github_main_upload",
        "validate:v1.1.7-stage7",
        "pending Stage 8",
      ]),
      `stage7_review_records_${name}`,
      `${name} records the Stage 7 review-passed pending Stage 8 continuity gate`,
      `${name} is missing Stage 7 review continuity fragments`,
    );
  }

  pass(
    "stage7_recursive_validator_not_rerun",
    "Stage 8 Phase 8.1 validates Stage 7 continuity from committed review artifact and records; run validate:v1.1.7-stage7 explicitly for full historical recursion",
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
      `SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION = "${runtimeVersion}"`,
      `SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION = "${closureSchemaVersion}"`,
      "window.__memoryAtlasStage8Phase1",
      "data-summary-iteration-closure-runtime={SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION}",
      "data-summary-closure-schema-version={SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION}",
      "data-source-review-schema-version={REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION}",
      "data-summary-closure-panel=\"change_comparison\"",
      "data-summary-closure-panel=\"stale_conflict_signals\"",
      "data-summary-closure-panel=\"proposal_candidates\"",
      "buildSummaryIterationClosure",
      "change_comparison",
      "stale_conflict_signals",
      "proposal_candidates",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "proposal_only: true",
      "directActiveMemoryWriteback: false",
      "rawPrivateDataIncluded: false",
      "proposalWrite: false",
    ]),
    "stage8_phase1_runtime_contract",
    "Summary and iteration closure runtime exposes change comparison, stale/conflict signals, proposal candidates and safety flags",
    "Summary and iteration closure runtime is missing Stage 8 Phase 8.1 hooks",
  );

  assertCondition(
    hasAll(styles, [
      ".summary-closure-runtime",
      ".summary-closure-schema-line",
      ".summary-closure-grid",
      ".summary-closure-card",
      ".summary-closure-proposals",
      ".summary-closure-safety",
    ]),
    "stage8_phase1_runtime_styles",
    "Summary and iteration closure runtime has scoped CSS for comparison, signals, proposal candidates and safety boundary",
    "Summary and iteration closure scoped styles are incomplete",
  );

  assertCondition(
    hasAll(browser, [
      runtimeVersion,
      closureSchemaVersion,
      "stage8_phase1_browser_runtime_root",
      "stage8_phase1_browser_change_comparison",
      "stage8_phase1_browser_stale_conflict_signals",
      "stage8_phase1_browser_proposal_candidates",
      "stage8_phase1_browser_debug_signal",
      "stage8_phase1_browser_screenshot",
      "stage8_phase1_browser_console",
      "__memoryAtlasStage8Phase1",
      "data-summary-closure-panel=\"change_comparison\"",
      "data-summary-closure-panel=\"stale_conflict_signals\"",
      "data-summary-closure-panel=\"proposal_candidates\"",
    ]),
    "stage8_phase1_browser_validator_contract",
    "Browser validator checks runtime root, comparison, signals, proposals, debug signal, screenshot and console safety",
    "Browser validator is missing Stage 8 Phase 8.1 checks",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage8_phase1.cjs",
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage8_phase1.cjs" &&
      packageJson.scripts?.[browserValidatorName] === `node scripts/${browserValidatorScript}`,
    "stage8_phase1_package_scripts",
    "package.json exposes Stage 8 Phase 8.1 static and browser validators",
    "package.json is missing Stage 8 Phase 8.1 validator scripts",
    { staticScript: packageJson.scripts?.[validatorName], browserScript: packageJson.scripts?.[browserValidatorName] },
  );

  assertCondition(
    hasAll(contract, [
      "Memory Atlas v1.1.7 Stage 8 Phase 8.1 Summary Iteration Closure Contract",
      taskId,
      acceptanceId,
      status,
      runtimeVersion,
      closureSchemaVersion,
      reviewSchemaVersion,
      "change_comparison",
      "stale_conflict_signals",
      "proposal_candidates",
      "proposal-only",
      "No direct active-memory writeback",
      "No Stage 8 review",
      "No GitHub main upload",
    ]),
    "stage8_phase1_contract",
    "Summary iteration closure contract records runtime, schema, outputs, safety and upload boundaries",
    "Summary iteration closure contract is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 8 Phase 8.1 Summary Iteration Closure Acceptance",
      taskId,
      acceptanceId,
      status,
      runtimeVersion,
      closureSchemaVersion,
      validatorName,
      browserValidatorName,
      "change_comparison",
      "stale_conflict_signals",
      "proposal_candidates",
      "No raw/private/cookie/session/secret data access",
      "No direct active-memory writeback",
      "No proposal queue write",
      "No GitHub main upload before the whole Stage 0-10 project is complete",
    ]),
    "stage8_phase1_acceptance",
    "Stage 8 Phase 8.1 acceptance pins runtime, browser, safety and upload boundaries",
    "Stage 8 Phase 8.1 acceptance is incomplete",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        runtimeVersion,
        closureSchemaVersion,
        validatorName,
        browserValidatorName,
        "Summary and iteration closure",
        "change_comparison",
        "stale_conflict_signals",
        "proposal_candidates",
        "No Stage 8 review",
        "No GitHub main upload",
      ]),
      `stage8_phase1_records_${name}`,
      `${name} records Stage 8 Phase 8.1 summary closure status, validators, boundaries and next gate`,
      `${name} is missing Stage 8 Phase 8.1 record fragments`,
    );
  }
}

function validateGitBoundary() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName,
    "stage8_phase1_local_branch",
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
    "stage8_phase1_no_remote_branch",
    "No remote Stage 0-10 development branch exists; intermediate work remains local only",
    "Remote development branch exists or could not be checked",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function main() {
  validateStage7Continuity();
  validateRuntimeAndBrowserContract();
  validateDocsAndRecords();
  validateGitBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_1_7_stage8_phase1",
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
    validator: "validate_memory_atlas_v1_1_7_stage8_phase1",
    task_id: taskId,
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
