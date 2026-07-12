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

const taskId = "MA-V12-S13P3";
const acceptanceId = "ACC-MA-V12-S13P3";
const status = "phase_s13_p3_apply_rollback_completed_pending_s13_review";
const validatorName = "validate:v1.2-s13-p3";
const scriptName = "validate_memory_atlas_v1_2_s13_p3.cjs";
const contractVersion = "proposal_apply.v1_2_s13_p3";
const previousValidatorName = "validate:v1.2-s13-p2";
const previousAcceptanceId = "ACC-MA-V12-S13P2";

const builderPath = "scripts/build_memory_atlas_proposal_apply.py";
const configPath = "机器治理/运行门禁/proposal_apply.v1_2_s13_p3.json";
const outputPath = "data/derived/proposals/proposal_apply_report.json";
const evidencePath = "机器治理/证据与日志/proposal_apply/proposal_apply_evidence.v1_2_s13_p3.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s13_p3_apply_rollback.md";
const humanDocPath = "人类可读/36_Apply回滚说明.md";

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const requiredFiles = [
  builderPath,
  configPath,
  outputPath,
  evidencePath,
  reviewPath,
  humanDocPath,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  "机器治理/证据与日志/README.md",
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
  `OpenAIDatabase/${evidencePath}`,
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
  "OpenAIDatabase/机器治理/证据与日志/README.md",
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

function repoPath(relativePath) {
  return path.join(repoRoot, relativePath);
}

function readRepoFile(relativePath) {
  return fs.readFileSync(repoPath(relativePath), "utf8");
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

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s13p3_package_script",
    "package.json exposes the v1.2 S13 P3 validator",
    "package.json is missing the v1.2 S13 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s13p3_open_diff_scope",
    "Open diff is limited to S13 P3 apply/rollback files and governance records",
    "S13 P3 has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validateRequiredFilesExist() {
  const missing = requiredFiles.filter((relativePath) => !fs.existsSync(repoPath(relativePath)));
  assertCondition(
    missing.length === 0,
    "s13p3_required_files_exist",
    "S13 P3 apply and rollback files exist",
    "S13 P3 is missing required apply and rollback files",
    { missing },
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

function validateConfig() {
  const config = readJson(configPath);
  const forbiddenTargets = config.apply_contract?.forbidden_target_fragments || [];
  const sample = (config.apply_contract?.proposal_fixtures || []).find((item) => item.proposal_id === "sample");
  const unauthorized = (config.apply_contract?.proposal_fixtures || []).find((item) => item.proposal_id === "sample_unauthorized");
  assertCondition(
    config.schema_version === contractVersion &&
      config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === status &&
      config.validator === validatorName &&
      config.apply_contract?.human_approval_required_before_apply === true &&
      config.apply_contract?.validation_after_apply_required === true &&
      config.apply_contract?.rollback_point_required === true &&
      config.apply_contract?.raw_archive_is_never_apply_target === true &&
      forbiddenTargets.includes("data/public_raw/") &&
      forbiddenTargets.includes("data/raw/") &&
      sample?.approval?.status === "approved_by_human" &&
      unauthorized?.approval?.status !== "approved_by_human",
    "s13p3_config",
    "S13 P3 config records human approval, validation, rollback point and raw target boundaries",
    "S13 P3 config does not satisfy the apply/rollback contract",
    { forbiddenTargets, sampleApproval: sample?.approval, unauthorizedApproval: unauthorized?.approval },
  );
}

function validateOutputAndEvidence() {
  const output = readJson(outputPath);
  const evidence = readJson(evidencePath);
  const unauthorized = output.sample_outcomes?.unauthorized_attempt || {};
  const authorized = output.sample_outcomes?.authorized_apply_dry_run || {};
  const failure = output.sample_outcomes?.validation_failure_dry_run || {};
  assertCondition(
    output.schema_version === "openai_database.proposal_apply.v1_2_s13_p3" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.summary?.unauthorized_apply_blocked === true &&
      output.summary?.authorized_apply_available === true &&
      output.summary?.validation_after_apply === true &&
      output.summary?.rollback_available === true &&
      output.summary?.raw_mutation === false &&
      output.phase_boundary?.does_not_upload_github_main === true &&
      output.phase_boundary?.does_not_push_remote === true &&
      output.phase_boundary?.next_phase === "S13 Review" &&
      unauthorized.status === "FAIL_CLOSED" &&
      unauthorized.applies_proposal === false &&
      authorized.status === "PASS" &&
      authorized.would_apply === true &&
      authorized.validation_after_apply === true &&
      authorized.rollback_point_created === true &&
      authorized.raw_mutation === false &&
      failure.rollback_available === true &&
      failure.rollback_or_needs_revision === true &&
      evidence.summary?.machine_apply_attempt_count >= 3 &&
      evidence.summary?.raw_mutation === false,
    "s13p3_output_evidence",
    "S13 P3 output proves fail-closed unauthorized apply, authorized dry-run apply, validation and rollback evidence",
    "S13 P3 output or evidence does not satisfy the apply/rollback acceptance contract",
    { unauthorized, authorized, failure, evidenceSummary: evidence.summary },
  );
}

function validateAtlasctlApplyViews() {
  const unauthorizedResult = run(
    "python3",
    ["scripts/atlasctl.py", "apply", "--proposal", "sample_unauthorized", "--dry-run"],
    { expectedStatuses: [2], cwd: repoRoot },
  );
  const unauthorized = parseJsonFromStdout(unauthorizedResult);
  const authorizedResult = run(
    "python3",
    ["scripts/atlasctl.py", "apply", "--proposal", "sample", "--dry-run"],
    { cwd: repoRoot },
  );
  const authorized = parseJsonFromStdout(authorizedResult);
  const failureResult = run(
    "python3",
    ["scripts/atlasctl.py", "apply", "--proposal", "sample", "--dry-run", "--simulate-validation-failure"],
    { expectedStatuses: [2], cwd: repoRoot },
  );
  const failure = parseJsonFromStdout(failureResult);
  assertCondition(
    unauthorized.status === "FAIL_CLOSED" &&
      unauthorized.applies_proposal === false &&
      unauthorized.writes_files === false &&
      authorized.status === "PASS" &&
      authorized.dry_run === true &&
      authorized.writes_files === false &&
      authorized.would_apply === true &&
      authorized.validation_after_apply === true &&
      authorized.raw_mutation === false &&
      failure.status === "FAIL_CLOSED" &&
      failure.rollback_available === true &&
      failure.rollback_or_needs_revision === true,
    "s13p3_atlasctl_apply_dry_runs",
    "atlasctl apply dry-runs prove unauthorized fail-closed, authorized apply path and rollback failure path",
    "atlasctl apply dry-runs do not satisfy S13 P3 behavior",
    { unauthorized, authorized, failure },
  );
}

function validateBuilderAndAtlasctlSource() {
  const builder = readRepoFile(builderPath);
  const atlasctl = readRepoFile("scripts/atlasctl.py");
  assertCondition(
    hasAll(builder, [
      "MA-V12-S13P3",
      "ACC-MA-V12-S13P3",
      "proposal_apply.v1_2_s13_p3",
      "sample_unauthorized",
      "simulate-validation-failure",
      "raw_archive_is_never_apply_target",
    ]) &&
      hasAll(atlasctl, [
        "PROPOSAL_APPLY_TASK_ID",
        "PROPOSAL_APPLY_BUILDER",
        'subparsers.add_parser("apply"',
        "run_apply",
      ]),
    "s13p3_builder_atlasctl_contract",
    "Builder and atlasctl expose S13 P3 apply/rollback contracts",
    "Builder or atlasctl is missing S13 P3 apply/rollback contract hooks",
  );
}

function validateRecords() {
  const requiredFragments = [
    "MA-V12-S13P3",
    "ACC-MA-V12-S13P3",
    status,
    validatorName,
    contractVersion,
    "S13 P3",
    "Apply 与回滚",
    "sample_unauthorized",
    "sample",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "pending S13 Review",
  ];
  for (const relativePath of [...recordFiles, reviewPath, humanDocPath]) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s13p3_records_${relativePath}`,
      `${relativePath} records S13 P3 status, apply samples, validator, boundaries and next phase`,
      `${relativePath} is missing S13 P3 record fragments`,
      { missing },
    );
  }
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  assertCondition(
    hasAll(quickEntry, ["S13 P3 已完成", "pending S13 Review", "sample_unauthorized", "sample", "No GitHub main upload"]),
    "s13p3_quick_entry",
    "Quick entry records completed S13 P3 and pending S13 Review",
    "Quick entry does not record S13 P3 state",
  );
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  assertCondition(
    hasAll(overview, ["S13 P3", "Apply 与回滚", "pending S13 Review", "No raw mutation"]),
    "s13p3_overview",
    "Human overview records S13 P3 apply/rollback and pending S13 Review",
    "Human overview does not record S13 P3 state",
  );
  const machineReadme = readRepoFile("机器治理/README.md");
  assertCondition(
    hasAll(machineReadme, ["S13 P3", "proposal_apply.v1_2_s13_p3", "pending S13 Review"]),
    "s13p3_machine_readme",
    "Machine README records S13 P3 gate and next phase",
    "Machine README does not record S13 P3",
  );
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(runGate, ["proposal_apply.v1_2_s13_p3", validatorName, "sample_unauthorized", "sample"]),
    "s13p3_run_gate",
    "Run gate README records S13 P3 artifacts, validator and samples",
    "Run gate README does not record S13 P3",
  );
  const evidenceReadme = readRepoFile("机器治理/证据与日志/README.md");
  assertCondition(
    hasAll(evidenceReadme, ["proposal_apply_evidence.v1_2_s13_p3.json", "S13 P3", "rollback"]),
    "s13p3_evidence_readme",
    "Evidence README records the S13 P3 proposal apply evidence file",
    "Evidence README does not record S13 P3 evidence",
  );
}

function validatePreviousGateIfClean() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s13p3_previous_s13p2_deferred_until_clean_tree", "S13 P2 clean-tree validator will be re-run after S13 P3 commit", { changed });
    return;
  }
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[previousValidatorName],
    "s13p3_previous_s13p2_script",
    "S13 P2 validator script is registered",
    "S13 P2 validator script is missing",
  );
  const result = run("pnpm", ["--dir", "apps/memory-atlas", "run", previousValidatorName], { cwd: repoRoot, timeout: 120000 });
  const payload = parseJsonFromStdout(result);
  assertCondition(
    payload.status === "PASS" && payload.acceptance_id === previousAcceptanceId,
    "s13p3_previous_s13p2",
    "S13 P2 validator passes before accepting S13 P3",
    "S13 P2 validator failed during S13 P3 validation",
    { status: payload.status, acceptance_id: payload.acceptance_id },
  );
}

function validateNoRawOrSecretOpenChanges() {
  const changed = getOpenChangedPaths();
  const forbidden = [
    "OpenAIDatabase/data/public_raw/",
    "OpenAIDatabase/data/raw/",
    "OpenAIDatabase/data/private_imports/",
    "OpenAIDatabase/credentials",
  ];
  const forbiddenOpenChanges = changed.filter((file) => forbidden.some((prefix) => file.startsWith(prefix)));
  const publicRawDiff = run("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw"], {
    cwd: worktreeRoot,
  }).stdout.trim();
  assertCondition(
    forbiddenOpenChanges.length === 0 && publicRawDiff.length === 0,
    "s13p3_no_raw_or_secret_open_changes",
    "S13 P3 open diff does not modify raw, private imports, credentials or secrets",
    "S13 P3 open diff modifies forbidden raw/private/credential paths",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateRequiredFilesExist();
    for (const relativePath of requiredFiles) validateTextFile(relativePath);
    validateConfig();
    validateBuilderAndAtlasctlSource();
    validateOutputAndEvidence();
    validateAtlasctlApplyViews();
    validateRecords();
    validatePreviousGateIfClean();
    validateNoRawOrSecretOpenChanges();
    console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    checks.push({
      name: "failure",
      status: "FAIL",
      evidence: error.message,
      ...(error.details ? { details: error.details } : {}),
      ...(error.stdout ? { stdout: error.stdout.slice(0, 4000) } : {}),
      ...(error.stderr ? { stderr: error.stderr.slice(0, 4000) } : {}),
    });
    console.error(JSON.stringify({ status: "FAIL", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
    process.exit(1);
  }
}

main();
