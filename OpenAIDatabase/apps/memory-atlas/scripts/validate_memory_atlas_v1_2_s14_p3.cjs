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

const taskId = "MA-V12-S14P3";
const acceptanceId = "ACC-MA-V12-S14P3";
const status = "phase_s14_p3_development_record_completed_pending_s14_review";
const validatorName = "validate:v1.2-s14-p3";
const scriptName = "validate_memory_atlas_v1_2_s14_p3.cjs";
const previousValidatorName = "validate:v1.2-s14-p2";
const previousAcceptanceId = "ACC-MA-V12-S14P2";
const evidencePath = "机器治理/证据与日志/stage_pass_gates/stage_pass_gate_status.v1_2_s14_p3.json";
const runbookPath = "人类可读/09_验收标准与运行手册.md";

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${runbookPath}`,
  "OpenAIDatabase/机器治理/证据与日志/README.md",
  `OpenAIDatabase/${evidencePath}`,
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "机器治理/证据与日志/README.md",
];

const requiredReviewValidators = Array.from({ length: 13 }, (_, index) => {
  const stage = `s${String(index + 1).padStart(2, "0")}`;
  return `validate:v1.2-${stage}-review`;
});

const requiredMaintenanceCommands = [
  "python3 scripts/atlasctl.py run --profile owner-daily --dry-run",
  "python3 scripts/atlasctl.py audit",
  "pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s14-p3",
  "npm run build --prefix apps/memory-atlas",
  "python3 -B -m unittest discover OpenAIDatabase/tests -q",
  "cat OpenAIDatabase/机器治理/证据与日志/stage_pass_gates/stage_pass_gate_status.v1_2_s14_p3.json",
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

function hasCjk(value) {
  return /[\u3400-\u9fff]/.test(String(value || ""));
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
    "s14p3_package_script",
    "package.json exposes the v1.2 S14 P3 validator",
    "package.json is missing the v1.2 S14 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
  assertCondition(
    packageJson.scripts?.[previousValidatorName] === "node scripts/validate_memory_atlas_v1_2_s14_p2.cjs",
    "s14p3_previous_phase_registered",
    "S14 P2 validator remains registered before S14 P3",
    "S14 P3 must start after S14 P2 remains registered",
    { previousValidatorName, previousAcceptanceId },
  );
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s14p3_open_diff_scope",
    "Open diff is limited to S14 P3 development-record files and governance records",
    "S14 P3 has unrelated OpenAIDatabase changes",
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

function validateRequiredFilesExist() {
  const requiredFiles = [
    runbookPath,
    evidencePath,
    "机器治理/证据与日志/README.md",
    ...recordFiles,
  ];
  const missing = requiredFiles.filter((relativePath) => !fs.existsSync(path.join(repoRoot, relativePath)));
  assertCondition(
    missing.length === 0,
    "s14p3_required_files_exist",
    "S14 P3 runbook, machine evidence and governance records exist",
    "S14 P3 is missing required runbook, evidence or governance files",
    { missing },
  );
}

function validateRunbook() {
  validateTextFile(runbookPath);
  const source = readRepoFile(runbookPath);
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    "开发记录中文可读",
    "维护命令少而清晰",
    "所有 stage pass gate 状态可查",
    evidencePath,
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "pending S14 Review",
  ];
  const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
  const commandCount = (source.match(/```bash/g) || []).length;
  const missingCommands = requiredMaintenanceCommands.filter((command) => !source.includes(command));
  assertCondition(
    hasCjk(source) && missing.length === 0 && commandCount <= 6 && missingCommands.length === 0,
    "s14p3_runbook_contract",
    "Human runbook is Chinese-readable, concise and points to machine stage status evidence",
    "S14 P3 runbook does not satisfy the development-record contract",
    { missing, commandCount, missingCommands },
  );
}

function validateMachineEvidence() {
  validateTextFile(evidencePath);
  const evidence = readJson(evidencePath);
  const stages = Array.isArray(evidence.stage_pass_gates) ? evidence.stage_pass_gates : [];
  const stageIds = stages.map((item) => item.stage);
  const missingStages = Array.from({ length: 14 }, (_, index) => `S${String(index + 1).padStart(2, "0")}`).filter((stage) => !stageIds.includes(stage));
  const s14 = stages.find((item) => item.stage === "S14") || {};
  const missingCommands = requiredMaintenanceCommands.filter((command) => !(evidence.maintenance_commands || []).includes(command));
  assertCondition(
    evidence.schema_version === "memory_atlas.stage_pass_gate_status.v1_2_s14_p3" &&
      evidence.task_id === taskId &&
      evidence.acceptance_id === acceptanceId &&
      evidence.phase_status === status &&
      evidence.no_github_main_upload === true &&
      evidence.remote_push === false &&
      evidence.raw_mutation === false &&
      evidence.homepage_pollution === false &&
      evidence.maintenance_command_count <= 6 &&
      missingCommands.length === 0 &&
      missingStages.length === 0 &&
      stages.length === 14 &&
      s14.status === "phase_s14_p3_completed_pending_s14_review" &&
      s14.next_gate === "S14 Review" &&
      Array.isArray(s14.phase_validators) &&
      s14.phase_validators.includes(validatorName),
    "s14p3_machine_evidence",
    "Machine evidence records all stage pass-gate statuses and S14 P3 boundary",
    "S14 P3 machine evidence does not satisfy the stage pass-gate status contract",
    {
      schema_version: evidence.schema_version,
      task_id: evidence.task_id,
      acceptance_id: evidence.acceptance_id,
      missingStages,
      maintenance_command_count: evidence.maintenance_command_count,
      missingCommands,
      s14,
    },
  );
}

function validateStageValidatorsRegistered() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  const missingReviewValidators = requiredReviewValidators.filter((name) => !packageJson.scripts?.[name]);
  assertCondition(
    missingReviewValidators.length === 0 && packageJson.scripts?.[validatorName],
    "s14p3_stage_review_validators_registered",
    "S01-S13 review validators and S14 P3 validator are registered for status lookup",
    "Stage pass gate validators are not all registered",
    { missingReviewValidators },
  );
}

function validateCommandSurfaces() {
  const ownerDaily = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "run", "--profile", "owner-daily", "--dry-run"]));
  assertCondition(
    ownerDaily.status === "PASS" &&
      ownerDaily.command === "run" &&
      ownerDaily.profile === "owner-daily" &&
      ownerDaily.dry_run === true &&
      ownerDaily.writes_files === false &&
      ownerDaily.remote_push === false &&
      ownerDaily.github_main_upload === false,
    "s14p3_owner_daily_dry_run",
    "owner-daily remains a concise no-write dry-run surface",
    "owner-daily dry-run no longer satisfies S14 maintenance requirements",
    ownerDaily,
  );

  const audit = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "audit"], { timeout: 300000 }));
  assertCondition(
    audit.status === "PASS" &&
      audit.command === "audit" &&
      audit.check === "final" &&
      audit.acceptance_id === previousAcceptanceId &&
      audit.failed_gate_count === 0 &&
      audit.high_token_auto_summary === false &&
      audit.total_output_chars <= 12000 &&
      audit.remote_push === false &&
      audit.github_main_upload === false &&
      audit.raw_mutation === false,
    "s14p3_final_audit_still_passes",
    "Final audit still runs before S14 P3 records claim completion",
    "S14 P3 cannot complete because final audit does not pass",
    {
      status: audit.status,
      command: audit.command,
      check: audit.check,
      task_id: audit.task_id,
      acceptance_id: audit.acceptance_id,
      failed_gate_count: audit.failed_gate_count,
      total_output_chars: audit.total_output_chars,
    },
  );
}

function validateHomepageNotPolluted() {
  validateTextFile("人类可读/00_快速入口.md");
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  assertCondition(
    !quickEntry.includes(taskId) && !quickEntry.includes(runbookPath) && !quickEntry.includes(evidencePath),
    "s14p3_homepage_not_polluted",
    "S14 P3 keeps machine evidence and runbook details out of the human homepage",
    "S14 P3 polluted the human quick entry with phase-specific evidence",
    {
      hasTaskId: quickEntry.includes(taskId),
      hasRunbookPath: quickEntry.includes(runbookPath),
      hasEvidencePath: quickEntry.includes(evidencePath),
    },
  );
}

function validateGovernanceRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    runbookPath,
    evidencePath,
    "开发记录中文可读",
    "维护命令少而清晰",
    "所有 stage pass gate 状态可查",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "pending S14 Review",
  ];
  for (const relativePath of recordFiles) {
    validateTextFile(relativePath);
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s14p3_records:${relativePath}`,
      `${relativePath} records S14 P3 development-record status and boundary`,
      `${relativePath} is missing S14 P3 governance fragments`,
      { missing },
    );
  }
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateTextFile(`apps/memory-atlas/scripts/${scriptName}`);
    validateRequiredFilesExist();
    validateRunbook();
    validateMachineEvidence();
    validateStageValidatorsRegistered();
    validateCommandSurfaces();
    validateHomepageNotPolluted();
    validateGovernanceRecords();
    console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(
      JSON.stringify(
        {
          status: "FAIL",
          task_id: taskId,
          acceptance_id: acceptanceId,
          failed_check: error.message,
          details: error.details || {},
          stdout: error.stdout || "",
          stderr: error.stderr || "",
          checks,
        },
        null,
        2,
      ),
    );
    process.exit(1);
  }
}

main();
