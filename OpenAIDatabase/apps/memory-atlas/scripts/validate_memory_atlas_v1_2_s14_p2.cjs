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

const taskId = "MA-V12-S14P2";
const acceptanceId = "ACC-MA-V12-S14P2";
const status = "phase_s14_p2_final_audit_gate_completed_pending_s14_p3";
const validatorName = "validate:v1.2-s14-p2";
const scriptName = "validate_memory_atlas_v1_2_s14_p2.cjs";
const contractVersion = "atlasctl_final_audit.v1_2_s14_p2";
const previousValidatorName = "validate:v1.2-s14-p1";
const previousAcceptanceId = "ACC-MA-V12-S14P1";

const requiredGateIds = [
  "unit_tests",
  "frontend_build",
  "chinese_ux_audit",
  "visual_roi_audit",
  "raw_append_only_audit",
  "credential_audit",
  "report_contract_audit",
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
    "s14p2_package_script",
    "package.json exposes the v1.2 S14 P2 validator",
    "package.json is missing the v1.2 S14 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s14p2_open_diff_scope",
    "Open diff is limited to S14 P2 final audit files and governance records",
    "S14 P2 has unrelated OpenAIDatabase changes",
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

function validatePreviousPhaseStillRegistered() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[previousValidatorName] === "node scripts/validate_memory_atlas_v1_2_s14_p1.cjs",
    "s14p2_previous_phase_registered",
    "S14 P1 validator remains registered before S14 P2",
    "S14 P2 must start after S14 P1 remains registered",
    { previousValidatorName, previousAcceptanceId },
  );
}

function validateFinalAudit() {
  const result = run("python3", ["scripts/atlasctl.py", "audit"], { timeout: 300000 });
  const payload = parseJsonFromStdout(result);
  const gates = Array.isArray(payload.gates) ? payload.gates : [];
  const gateIds = gates.map((gate) => gate.gate_id);
  const missingGateIds = requiredGateIds.filter((gateId) => !gateIds.includes(gateId));
  const badGates = gates.filter(
    (gate) =>
      gate.status !== "PASS" ||
      !Array.isArray(gate.command) ||
      gate.command.length < 2 ||
      !hasCjk(gate.chinese_explanation) ||
      String(gate.stdout_tail || "").length > 1400 ||
      String(gate.stderr_tail || "").length > 1400,
  );
  assertCondition(
    payload.status === "PASS" &&
      payload.command === "audit" &&
      payload.check === "final" &&
      payload.task_id === taskId &&
      payload.acceptance_id === acceptanceId &&
      payload.contract_version === contractVersion &&
      payload.phase_status === status &&
      payload.writes_files === false &&
      payload.writes_tracked_files === false &&
      payload.raw_mutation === false &&
      payload.remote_push === false &&
      payload.github_main_upload === false &&
      payload.high_token_auto_summary === false &&
      payload.max_output_chars_per_gate <= 1400 &&
      payload.total_output_chars <= 12000 &&
      payload.phase_boundary?.next_phase === "S14 P3" &&
      payload.phase_boundary?.does_not_upload_github_main === true &&
      missingGateIds.length === 0 &&
      gateIds.length === requiredGateIds.length &&
      badGates.length === 0,
    "s14p2_final_audit",
    "atlasctl audit runs the S14 P2 final gate with concise Chinese explanations",
    "atlasctl audit does not satisfy the S14 P2 final gate contract",
    {
      status: payload.status,
      task_id: payload.task_id,
      acceptance_id: payload.acceptance_id,
      gateIds,
      missingGateIds,
      badGates: badGates.map((gate) => gate.gate_id),
      total_output_chars: payload.total_output_chars,
    },
  );
}

function validateDryRunSurface() {
  const payload = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "audit", "--dry-run"]));
  const plannedGateIds = (payload.gates || []).map((gate) => gate.gate_id);
  const missingGateIds = requiredGateIds.filter((gateId) => !plannedGateIds.includes(gateId));
  assertCondition(
    payload.status === "PASS" &&
      payload.command === "audit" &&
      payload.check === "final" &&
      payload.dry_run === true &&
      payload.task_id === taskId &&
      payload.acceptance_id === acceptanceId &&
      missingGateIds.length === 0 &&
      payload.writes_files === false &&
      payload.phase_boundary?.next_phase === "S14 P3" &&
      hasCjk(payload["中文说明"]),
    "s14p2_audit_dry_run_surface",
    "atlasctl audit --dry-run lists the final gate plan without running it",
    "atlasctl audit --dry-run does not expose the S14 P2 final gate plan",
    { plannedGateIds, missingGateIds },
  );
}

function validateAtlasctlSource() {
  const source = readRepoFile("scripts/atlasctl.py");
  for (const fragment of [
    "def final_audit_gate_plan",
    "def run_final_audit",
    "atlasctl_final_audit.v1_2_s14_p2",
    "unit_tests",
    "frontend_build",
    "report_contract_audit",
    "high_token_auto_summary",
  ]) {
    assertCondition(source.includes(fragment), `s14p2_source:${fragment}`, `atlasctl.py includes ${fragment}`, `atlasctl.py is missing ${fragment}`);
  }
}

function validateGovernanceRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "atlasctl_final_audit.v1_2_s14_p2",
    "unit_tests",
    "frontend_build",
    "Chinese UX",
    "visual ROI",
    "raw append-only",
    "credential audit",
    "report contract",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "pending S14 P3",
  ];
  for (const relativePath of recordFiles) {
    validateTextFile(relativePath);
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s14p2_records:${relativePath}`,
      `${relativePath} records S14 P2 final audit gate status and boundary`,
      `${relativePath} is missing S14 P2 governance fragments`,
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
    validatePreviousPhaseStillRegistered();
    validateFinalAudit();
    validateDryRunSurface();
    validateAtlasctlSource();
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
