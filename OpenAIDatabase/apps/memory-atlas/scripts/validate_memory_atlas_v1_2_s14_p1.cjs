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

const taskId = "MA-V12-S14P1";
const acceptanceId = "ACC-MA-V12-S14P1";
const status = "phase_s14_p1_unified_cli_completed_pending_s14_p2";
const validatorName = "validate:v1.2-s14-p1";
const scriptName = "validate_memory_atlas_v1_2_s14_p1.cjs";
const contractVersion = "atlasctl_unified_cli.v1_2_s14_p1";
const ownerDailyApiVersion = "memory_atlas_owner_daily_api.v1_2_r5";
const ownerDailyResultVersion = "memory_atlas_owner_daily_result.v1_2_r5";
const maxOwnerDailyResultBytes = 64 * 1024;
const previousValidatorName = "validate:v1.2-s13-review";
const previousAcceptanceId = "ACC-MA-V12-S13-REVIEW";

const expectedCommandIds = [
  "sync",
  "analyze",
  "build-atlas",
  "audit",
  "push",
  "proposals",
  "generate-personalization-prompt",
  "deep-explore",
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/scripts/atlasctl.py",
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

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
    maxBuffer: 128 * 1024 * 1024,
    timeout: options.timeout || 0,
  });
  const expectedStatuses = options.expectedStatuses || [0];
  if (!expectedStatuses.includes(result.status)) {
    const reason = result.error?.code === "ETIMEDOUT" ? " timed out" : "";
    const error = new Error(`${command} ${args.join(" ")} failed${reason} with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    error.expectedStatuses = expectedStatuses;
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

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s14p1_package_script",
    "package.json exposes the v1.2 S14 P1 validator",
    "package.json is missing the v1.2 S14 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s14p1_open_diff_scope",
    "Open diff is limited to the S14 P1 unified CLI files",
    "S14 P1 has unrelated OpenAIDatabase changes",
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

function validatePreviousStageStillRegistered() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[previousValidatorName] === "node scripts/validate_memory_atlas_v1_2_s13_review.cjs",
    "s14p1_previous_stage_registered",
    "S13 Review validator remains registered before S14 P1",
    "S14 P1 must start after S13 Review remains registered",
    { previousValidatorName, previousAcceptanceId },
  );
}

function validateOwnerDailyProfile() {
  const result = run("python3", ["scripts/atlasctl.py", "run", "--profile", "owner-daily", "--dry-run"]);
  const payload = parseJsonFromStdout(result);
  const actualIds = (payload.commands || []).map((item) => item.command_id);
  const actualStepIds = (payload.steps || []).map((item) => item.step_id);
  const details = {
    status: payload.status,
    command: payload.command,
    profile: payload.profile,
    task_id: payload.task_id,
    acceptance_id: payload.acceptance_id,
    phase_status: payload.phase_status,
    dry_run: payload.dry_run,
    writes_files: payload.writes_files,
    remote_push: payload.remote_push,
    github_main_upload: payload.github_main_upload,
    actualIds,
    actualStepIds,
    expectedCommandIds,
    completed_count: payload.completed_count,
    failed_count: payload.failed_count,
    result_bytes: Buffer.byteLength(result.stdout, "utf8"),
  };
  assertCondition(
    payload.status === "PASS" &&
      payload.schema_version === ownerDailyResultVersion &&
      payload.api_version === ownerDailyApiVersion &&
      payload.action === "run" &&
      payload.command === "run" &&
      payload.profile === "owner-daily" &&
      payload.task_id === taskId &&
      payload.acceptance_id === acceptanceId &&
      payload.contract_version === contractVersion &&
      payload.phase_status === status &&
      payload.dry_run === true &&
      payload.writes_files === false &&
      payload.remote_push === false &&
      payload.github_main_upload === false &&
      JSON.stringify(actualIds) === JSON.stringify(expectedCommandIds) &&
      JSON.stringify(actualStepIds) === JSON.stringify(expectedCommandIds) &&
      (payload.commands || []).every((item) => item.dry_run === true && Array.isArray(item.invocation) && item.invocation.includes("--dry-run")) &&
      (payload.steps || []).every((item) => item.status === "pass" && item.retryable === false && Array.isArray(item.invocation) && item.invocation.includes("--dry-run")) &&
      payload.completed_count === expectedCommandIds.length &&
      payload.failed_count === 0 &&
      Array.isArray(payload.retryable_step_ids) &&
      payload.retryable_step_ids.length === 0 &&
      payload.safety?.writes_files === false &&
      payload.safety?.remote_push === false &&
      payload.safety?.raw_mutation === false &&
      payload.safety?.sends_to_chatgpt === false &&
      payload.safety?.proposal_apply_execution === false &&
      payload.safety?.canonical_repo_mutation === false &&
      Buffer.byteLength(result.stdout, "utf8") <= maxOwnerDailyResultBytes &&
      payload.phase_boundary?.next_phase === "S14 P2" &&
      payload.phase_boundary?.does_not_run_final_audit === true,
    "s14p1_owner_daily_profile",
    "atlasctl run --profile owner-daily --dry-run executes eight bounded no-write steps",
    "atlasctl owner-daily dry-run profile does not match S14 P1 contract",
    details,
  );
}

function validateDryRunCommand(commandId, args, checker) {
  const result = run("python3", ["scripts/atlasctl.py", ...args]);
  const payload = parseJsonFromStdout(result);
  const details = {
    args,
    status: payload.status,
    command: payload.command,
    task_id: payload.task_id,
    acceptance_id: payload.acceptance_id,
    dry_run: payload.dry_run,
    writes_files: payload.writes_files,
    remote_push: payload.remote_push,
    github_main_upload: payload.github_main_upload,
    phase_status: payload.phase_status,
  };
  assertCondition(
    checker(payload),
    `s14p1_${commandId}_dry_run`,
    `${commandId} supports an executable dry-run path`,
    `${commandId} dry-run path failed S14 P1 checks`,
    details,
  );
}

function validateDryRunCoverage() {
  validateDryRunCommand("sync", ["sync", "--source", "chatgpt", "--dry-run"], (payload) => payload.source_id === "chatgpt" && payload.dry_run === true && payload.writes_files === false);
  validateDryRunCommand(
    "analyze",
    ["analyze", "--stage", "facets", "--dry-run"],
    (payload) => payload.task_id === "MA-V12-S05P3" && payload.dry_run === true && payload.writes_files === false && payload.phase_boundary?.does_not_modify_raw === true,
  );
  validateDryRunCommand("build_atlas", ["build-atlas", "--dry-run"], (payload) => payload.command === "build-atlas" && payload.dry_run === true && payload.writes_files === false);
  validateDryRunCommand("audit", ["audit", "--dry-run"], (payload) => payload.command === "audit" && payload.dry_run === true && payload.writes_files === false);
  validateDryRunCommand("push", ["push", "--dry-run"], (payload) => payload.command === "push" && payload.dry_run === true && payload.writes_files === false && payload.remote_push === false);
  validateDryRunCommand("proposals", ["proposals", "--dry-run"], (payload) => payload.command === "proposals" && payload.dry_run === true && payload.raw_mutation === false);
  validateDryRunCommand(
    "generate_personalization_prompt",
    ["generate-personalization-prompt", "--dry-run"],
    (payload) => payload.command === "generate-personalization-prompt" && payload.dry_run === true && payload.writes_files === false && payload.sends_to_chatgpt === false,
  );
  validateDryRunCommand(
    "deep_explore",
    ["deep-explore", "--dry-run"],
    (payload) => payload.command === "deep-explore" && payload.dry_run === true && payload.writes_files === false && payload.sends_to_chatgpt === false,
  );
}

function validateAtlasctlSource() {
  const source = readRepoFile("scripts/atlasctl.py");
  for (const fragment of [
    'subparsers.add_parser("run"',
    '"owner-daily"',
    'subparsers.add_parser("deep-explore"',
    "def owner_daily_profile_contract",
    "OwnerDailyRunner",
  ]) {
    assertCondition(source.includes(fragment), `s14p1_source:${fragment}`, `atlasctl.py includes ${fragment}`, `atlasctl.py is missing ${fragment}`);
  }
  const runnerSource = readRepoFile("scripts/memory_atlas_owner_daily.py");
  for (const fragment of [
    "atlasctl_unified_cli.v1_2_s14_p1",
    ownerDailyApiVersion,
    ownerDailyResultVersion,
    "OWNER_DAILY_STEP_IDS",
    "class OwnerDailyRunner",
  ]) {
    assertCondition(
      runnerSource.includes(fragment),
      `s14p1_runner_source:${fragment}`,
      `memory_atlas_owner_daily.py includes ${fragment}`,
      `memory_atlas_owner_daily.py is missing ${fragment}`,
    );
  }
}

function validateGovernanceRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "owner-daily",
    "atlasctl_unified_cli.v1_2_s14_p1",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "pending S14 P2",
  ];
  for (const relativePath of recordFiles) {
    validateTextFile(relativePath);
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s14p1_records:${relativePath}`,
      `${relativePath} records S14 P1 unified CLI status and boundary`,
      `${relativePath} is missing S14 P1 governance fragments`,
      { missing },
    );
  }
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateTextFile(`apps/memory-atlas/scripts/${scriptName}`);
    validateTextFile("scripts/atlasctl.py");
    validateTextFile("scripts/memory_atlas_owner_daily.py");
    validatePreviousStageStillRegistered();
    validateOwnerDailyProfile();
    validateDryRunCoverage();
    validateAtlasctlSource();
    validateGovernanceRecords();
    const result = { status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks };
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    const result = {
      status: "FAIL",
      task_id: taskId,
      acceptance_id: acceptanceId,
      failed_check: error.message,
      details: error.details || {},
      stdout: error.stdout || "",
      stderr: error.stderr || "",
      checks,
    };
    console.error(JSON.stringify(result, null, 2));
    process.exit(1);
  }
}

main();
