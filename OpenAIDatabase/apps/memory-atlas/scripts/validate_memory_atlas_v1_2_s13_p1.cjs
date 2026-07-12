#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

process.env.GIT_TERMINAL_PROMPT = process.env.GIT_TERMINAL_PROMPT || "0";
process.env.GIT_SSH_COMMAND =
  process.env.GIT_SSH_COMMAND || "ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=5 -o ServerAliveCountMax=1";

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S13P1";
const acceptanceId = "ACC-MA-V12-S13P1";
const status = "phase_s13_p1_proposal_state_machine_completed_pending_s13_p2";
const validatorName = "validate:v1.2-s13-p1";
const scriptName = "validate_memory_atlas_v1_2_s13_p1.cjs";
const contractVersion = "proposal_state_machine.v1_2_s13_p1";
const previousValidatorName = "validate:v1.2-s12-review";
const previousAcceptanceId = "ACC-MA-V12-S12-REVIEW";

const builderPath = "scripts/build_memory_atlas_proposal_state_machine.py";
const configPath = "机器治理/运行门禁/proposal_state_machine.v1_2_s13_p1.json";
const outputPath = "data/derived/proposals/proposal_state_machine_report.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s13_p1_proposal_state_machine.md";
const humanDocPath = "人类可读/34_Proposal状态机说明.md";

const requiredStates = [
  "draft",
  "pending_human_review",
  "approved_by_human",
  "applying",
  "applied",
  "validated",
  "committed",
  "failed_validation",
  "rollback_or_needs_revision",
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const textFiles = [
  builderPath,
  configPath,
  outputPath,
  reviewPath,
  humanDocPath,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  ...recordFiles,
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/scripts/atlasctl.py",
  `OpenAIDatabase/${builderPath}`,
  `OpenAIDatabase/${configPath}`,
  `OpenAIDatabase/${outputPath}`,
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanDocPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/运行门禁/README.md",
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

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
    maxBuffer: 128 * 1024 * 1024,
    timeout: options.timeout || 0,
  });
  if (result.status !== 0) {
    const reason = result.error?.code === "ETIMEDOUT" ? " timed out" : "";
    const error = new Error(`${command} ${args.join(" ")} failed${reason} with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function parseJsonFromStdout(result) {
  const stdout = result.stdout.trim();
  const start = stdout.indexOf("{");
  if (start < 0) throw new Error("stdout does not contain JSON object");
  return JSON.parse(stdout.slice(start));
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

function getOpenChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--untracked-files=all", "--", "OpenAIDatabase"], {
    cwd: worktreeRoot,
  });
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .sort();
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s13p1_open_diff_scope",
    "Open diff is limited to S13 P1 proposal state-machine files and governance records",
    "S13 P1 has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(source.endsWith("\n"), `${relativePath}:final_newline`, `${relativePath} has a final newline`, `${relativePath} is missing a final newline`);
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

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s13p1_package_script",
    "package.json exposes the v1.2 S13 P1 validator",
    "package.json is missing the v1.2 S13 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateConfig() {
  const config = readJson(configPath);
  const states = new Set(config.proposal_state_machine?.states || []);
  const missingStates = requiredStates.filter((state) => !states.has(state));
  assertCondition(
    config.schema_version === contractVersion &&
      config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === status &&
      missingStates.length === 0 &&
      config.proposal_state_machine?.human_approval_required_before_applying === true &&
      config.proposal_state_machine?.current_phase_executes_apply === false &&
      config.proposal_state_machine?.apply_execution_deferred_to === "S13 P3" &&
      config.proposal_state_machine?.diff_narrator_deferred_to === "S13 P2" &&
      config.proposal_expiry?.integrated === true &&
      Number(config.proposal_expiry?.warn_after_days || 0) > 0 &&
      Number(config.proposal_expiry?.stale_after_days || 0) > 0 &&
      Number(config.proposal_expiry?.archive_after_days || 0) > 0 &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.proposal_apply_execution === false &&
      config.scope_boundary?.github_main_upload === false &&
      config.scope_boundary?.remote_push === false,
    "s13p1_config",
    "S13 P1 config records proposal state machine, expiry integration and no-apply boundaries",
    "S13 P1 config does not satisfy proposal state-machine contract",
    { missingStates },
  );
}

function validateBuilderAndAtlasctlContract() {
  const builder = readRepoFile(builderPath);
  const atlasctl = readRepoFile("scripts/atlasctl.py");
  assertCondition(
    hasAll(builder, [
      taskId,
      acceptanceId,
      contractVersion,
      status,
      "pending_human_review",
      "approved_by_human",
      "failed_validation",
      "rollback_or_needs_revision",
      "proposal_state_machine_report.json",
      "raw_apply_target_allowed",
      "unauthorized_apply_blocked",
    ]) &&
      hasAll(atlasctl, [
        "proposals",
        taskId,
        acceptanceId,
        contractVersion,
        builderPath,
      ]),
    "s13p1_builder_atlasctl_contract",
    "Builder and atlasctl expose S13 P1 proposal state-machine contracts",
    "Builder or atlasctl is missing S13 P1 proposal state-machine contract",
  );
}

function validateOutputAndAtlasctl() {
  const output = readJson(outputPath);
  const stateSet = new Set(output.state_machine?.states || []);
  const missingStates = requiredStates.filter((state) => !stateSet.has(state));
  const proposals = Array.isArray(output.proposals) ? output.proposals : [];
  const invalid = [];
  for (const proposal of proposals) {
    const id = proposal.proposal_id || "unknown";
    const targetFiles = (proposal.target_files || []).map(String);
    if (!stateSet.has(proposal.current_state)) invalid.push(`${id}:invalid_state`);
    if (!proposal.expires_at) invalid.push(`${id}:missing_expiry`);
    if (!Array.isArray(proposal.validation_commands) || proposal.validation_commands.length === 0) invalid.push(`${id}:missing_validation`);
    if (!proposal.rollback_plan_zh) invalid.push(`${id}:missing_rollback`);
    if (proposal.apply_execution_allowed !== false) invalid.push(`${id}:apply_allowed`);
    if (proposal.raw_apply_target_allowed !== false) invalid.push(`${id}:raw_allowed`);
    if (targetFiles.some((file) => file.includes("data/public_raw/") || file.includes("data/raw/") || file.includes("credentials"))) {
      invalid.push(`${id}:forbidden_target`);
    }
  }
  assertCondition(
    output.schema_version === "openai_database.proposal_state_machine.v1_2_s13_p1" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.state_machine_version === contractVersion &&
      missingStates.length === 0 &&
      proposals.length >= 5 &&
      invalid.length === 0 &&
      output.summary?.all_proposals_have_expiry === true &&
      output.summary?.unauthorized_apply_blocked === true &&
      output.summary?.raw_apply_target_allowed === false &&
      output.summary?.current_phase_executes_apply === false &&
      output.summary?.proposal_apply_execution === false &&
      output.summary?.expiry_integrated === true &&
      output.phase_boundary?.does_not_apply_proposals === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      output.phase_boundary?.next_phase === "S13 P2",
    "s13p1_output",
    "S13 P1 output records normalized proposals, expiry, state machine and no-apply boundaries",
    "S13 P1 output does not satisfy proposal state-machine contract",
    { missingStates, proposalCount: proposals.length, invalid },
  );

  const dryRun = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "proposals", "--dry-run"], { cwd: repoRoot, timeout: 180000 }));
  assertCondition(
    dryRun.status === "PASS" &&
      dryRun.task_id === taskId &&
      dryRun.acceptance_id === acceptanceId &&
      dryRun.contract_version === contractVersion &&
      dryRun.dry_run === true &&
      dryRun.writes_files === false &&
      dryRun.applies_proposals === false &&
      dryRun.raw_mutation === false &&
      dryRun.output_contract?.report === outputPath &&
      dryRun.summary?.unauthorized_apply_blocked === true &&
      dryRun.summary?.raw_apply_target_allowed === false,
    "s13p1_atlasctl_proposals_dry_run",
    "atlasctl proposals --dry-run returns the no-write/no-apply S13 P1 state-machine contract",
    "atlasctl proposals --dry-run does not satisfy S13 P1 contract",
    dryRun,
  );
}

function validateDocsAndRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    contractVersion,
    "S13 P1",
    "Proposal 状态机",
    "draft",
    "pending_human_review",
    "approved_by_human",
    "applying",
    "applied",
    "validated",
    "committed",
    "failed_validation",
    "rollback_or_needs_revision",
    "proposal expiry",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "No proposal apply execution",
    "pending S13 P2",
  ];
  for (const relativePath of [reviewPath, humanDocPath, ...recordFiles]) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s13p1_records_${relativePath}`,
      `${relativePath} records S13 P1 status, validator, boundaries and next phase`,
      `${relativePath} is missing S13 P1 record fragments`,
      { missing },
    );
  }
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S13 P1 已完成", "Proposal 状态机", "下一步是 S13 P2", "No GitHub main upload"]),
    "s13p1_quick_entry",
    "Quick entry records completed S13 P1 and pending S13 P2",
    "Quick entry does not record completed S13 P1",
  );
  assertCondition(
    hasAll(overview, ["S13 P1 已完成", "Proposal 状态机", "pending_human_review", "approved_by_human", "下一步是 S13 P2"]),
    "s13p1_overview",
    "Human overview records S13 P1 proposal state machine and pending S13 P2",
    "Human overview is missing S13 P1 status",
  );
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, contractVersion, "S13 P2"]),
    "s13p1_machine_readme",
    "Machine README records S13 P1 gate and next phase",
    "Machine README is missing S13 P1 gate",
  );
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S13 P1 产物", "S13 P2"]),
    "s13p1_run_gate",
    "Run gate README records S13 P1 artifacts, validator and next phase",
    "Run gate README is missing S13 P1 gate",
  );
}

function validatePreviousGate() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s13p1_previous_s12_review_deferred_until_clean_tree", "S12 Review clean-tree validator will be re-run after S13 P1 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s12_review.cjs"], { cwd: appRoot, timeout: 300000 }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === previousAcceptanceId,
    "s13p1_previous_s12_review",
    "S12 Review validator passes before accepting S13 P1",
    "S12 Review validator did not pass before S13 P1",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateNoRawOrForbiddenChanges() {
  const changed = getOpenChangedPaths();
  const forbiddenOpenChanges = changed.filter(
    (file) =>
      file.includes("/data/raw/") ||
      file.includes("/data/private_imports/") ||
      file.includes("/data/raw_encrypted/") ||
      file.endsWith(".env") ||
      file.includes("secrets") ||
      file.includes("credentials"),
  );
  const publicRawDiff = run("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    forbiddenOpenChanges.length === 0 && publicRawDiff.length === 0,
    "s13p1_no_raw_or_secret_open_changes",
    "S13 P1 open diff does not modify raw, private imports, credentials or secrets",
    "S13 P1 has forbidden raw or secret changes",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    for (const file of textFiles) validateTextFile(file);
    validateConfig();
    validateBuilderAndAtlasctlContract();
    validateOutputAndAtlasctl();
    validateDocsAndRecords();
    validatePreviousGate();
    validateNoRawOrForbiddenChanges();
    console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({
      status: "FAIL",
      validator: scriptName.replace(/\.cjs$/, ""),
      task_id: taskId,
      acceptance_id: acceptanceId,
      error: error.message,
      details: error.details || {},
      stdout: error.stdout,
      stderr: error.stderr,
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
