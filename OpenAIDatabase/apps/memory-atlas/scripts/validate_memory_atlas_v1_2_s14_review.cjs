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

const taskId = "MA-V12-S14-REVIEW";
const acceptanceId = "ACC-MA-V12-S14-REVIEW";
const status = "stage_s14_review_passed_pending_v1_2_final_review_no_github_main_upload";
const validatorName = "validate:v1.2-s14-review";
const scriptName = "validate_memory_atlas_v1_2_s14_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s14_review.md";
const runbookPath = "人类可读/09_验收标准与运行手册.md";
const stageStatusPath = "机器治理/证据与日志/stage_pass_gates/stage_pass_gate_status.v1_2_s14_p3.json";

const phaseValidators = [
  ["validate:v1.2-s14-p1", "validate_memory_atlas_v1_2_s14_p1.cjs", "MA-V12-S14P1", "ACC-MA-V12-S14P1"],
  ["validate:v1.2-s14-p2", "validate_memory_atlas_v1_2_s14_p2.cjs", "MA-V12-S14P2", "ACC-MA-V12-S14P2"],
  ["validate:v1.2-s14-p3", "validate_memory_atlas_v1_2_s14_p3.cjs", "MA-V12-S14P3", "ACC-MA-V12-S14P3"],
];

const requiredGateIds = [
  "unit_tests",
  "frontend_build",
  "chinese_ux_audit",
  "visual_roi_audit",
  "raw_append_only_audit",
  "credential_audit",
  "report_contract_audit",
];

const expectedOwnerDailyIds = [
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

const requiredFiles = [
  reviewPath,
  runbookPath,
  stageStatusPath,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  "机器治理/证据与日志/README.md",
  "apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s14_p1.cjs",
  "apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s14_p2.cjs",
  "apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s14_p3.cjs",
  "scripts/atlasctl.py",
  ...recordFiles,
];

const textFiles = [
  reviewPath,
  runbookPath,
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
  `OpenAIDatabase/${reviewPath}`,
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
    "s14_review_package_script",
    "package.json exposes the v1.2 S14 Review validator",
    "package.json is missing the v1.2 S14 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
  const missingPhaseScripts = phaseValidators
    .filter(([script, file]) => packageJson.scripts?.[script] !== `node scripts/${file}`)
    .map(([script]) => script);
  assertCondition(
    missingPhaseScripts.length === 0,
    "s14_review_phase_scripts_registered",
    "S14 P1/P2/P3 validators remain registered before S14 Review",
    "S14 Review is missing phase validator registrations",
    { missingPhaseScripts },
  );
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s14_review_open_diff_scope",
    "Open diff is limited to S14 Review files and governance records",
    "S14 Review has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validateRequiredFilesExist() {
  const missing = requiredFiles.filter((relativePath) => !fs.existsSync(repoPath(relativePath)));
  assertCondition(
    missing.length === 0,
    "s14_review_required_files_exist",
    "S14 Review and S14 phase evidence files exist",
    "S14 Review is missing required files",
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

function validateOwnerDailyGate() {
  const payload = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "run", "--profile", "owner-daily", "--dry-run"]));
  const actualIds = (payload.commands || []).map((item) => item.command_id);
  assertCondition(
    payload.status === "PASS" &&
      payload.command === "run" &&
      payload.profile === "owner-daily" &&
      payload.task_id === "MA-V12-S14P1" &&
      payload.acceptance_id === "ACC-MA-V12-S14P1" &&
      payload.dry_run === true &&
      payload.writes_files === false &&
      payload.remote_push === false &&
      payload.github_main_upload === false &&
      JSON.stringify(actualIds) === JSON.stringify(expectedOwnerDailyIds) &&
      (payload.commands || []).every((item) => item.dry_run === true && Array.isArray(item.invocation) && item.invocation.includes("--dry-run")),
    "s14_review_owner_daily_gate",
    "S14 P1 owner-daily dry-run remains concise, useful and no-write",
    "S14 P1 owner-daily dry-run does not satisfy S14 Review",
    { actualIds, expectedOwnerDailyIds, phase_status: payload.phase_status },
  );
}

function validateFinalAuditGate() {
  const payload = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "audit"], { timeout: 300000 }));
  const gates = Array.isArray(payload.gates) ? payload.gates : [];
  const gateIds = gates.map((gate) => gate.gate_id);
  const missingGateIds = requiredGateIds.filter((gateId) => !gateIds.includes(gateId));
  const badGates = gates.filter(
    (gate) =>
      gate.status !== "PASS" ||
      !hasCjk(gate.chinese_explanation) ||
      String(gate.stdout_tail || "").length > 1400 ||
      String(gate.stderr_tail || "").length > 1400,
  );
  assertCondition(
    payload.status === "PASS" &&
      payload.command === "audit" &&
      payload.check === "final" &&
      payload.task_id === "MA-V12-S14P2" &&
      payload.acceptance_id === "ACC-MA-V12-S14P2" &&
      payload.failed_gate_count === 0 &&
      payload.high_token_auto_summary === false &&
      payload.total_output_chars <= 12000 &&
      payload.remote_push === false &&
      payload.github_main_upload === false &&
      payload.raw_mutation === false &&
      missingGateIds.length === 0 &&
      badGates.length === 0,
    "s14_review_final_audit_gate",
    "S14 P2 final audit covers all four-line core gates with Chinese explanations and bounded output",
    "S14 P2 final audit does not satisfy S14 Review",
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

function validateDevelopmentRecordGate() {
  const evidence = readJson(stageStatusPath);
  const stages = Array.isArray(evidence.stage_pass_gates) ? evidence.stage_pass_gates : [];
  const s14 = stages.find((item) => item.stage === "S14") || {};
  const runbook = readRepoFile(runbookPath);
  const missingStages = Array.from({ length: 14 }, (_, index) => `S${String(index + 1).padStart(2, "0")}`).filter(
    (stage) => !stages.some((item) => item.stage === stage),
  );
  assertCondition(
    evidence.schema_version === "memory_atlas.stage_pass_gate_status.v1_2_s14_p3" &&
      evidence.task_id === "MA-V12-S14P3" &&
      evidence.acceptance_id === "ACC-MA-V12-S14P3" &&
      evidence.phase_status === "phase_s14_p3_development_record_completed_pending_s14_review" &&
      evidence.no_github_main_upload === true &&
      evidence.remote_push === false &&
      evidence.raw_mutation === false &&
      evidence.homepage_pollution === false &&
      evidence.maintenance_command_count <= 6 &&
      missingStages.length === 0 &&
      stages.length === 14 &&
      s14.status === "phase_s14_p3_completed_pending_s14_review" &&
      hasAll(runbook, ["开发记录中文可读", "维护命令少而清晰", "所有 stage pass gate 状态可查", "pending S14 Review"]),
    "s14_review_development_record_gate",
    "S14 P3 records are Chinese-readable, concise and machine-queryable",
    "S14 P3 development records do not satisfy S14 Review",
    {
      missingStages,
      maintenance_command_count: evidence.maintenance_command_count,
      s14,
    },
  );
}

function validateReviewArtifact() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      validatorName,
      "S14 Review",
      "S14 P1",
      "S14 P2",
      "S14 P3",
      "atlasctl_unified_cli.v1_2_s14_p1",
      "atlasctl_final_audit.v1_2_s14_p2",
      "stage_pass_gate_status.v1_2_s14_p3.json",
      "owner-daily",
      "unit_tests",
      "frontend_build",
      "Chinese UX",
      "visual ROI",
      "raw append-only",
      "credential audit",
      "report contract",
      "开发记录中文可读",
      "维护命令少而清晰",
      "所有 stage pass gate 状态可查",
      "atlasctl 命令过多且无用",
      "审计增加明显 token/运行负担",
      "中文错误解释缺失",
      "final audit 未跑却声称完成",
      "No GitHub main upload",
      "No remote push",
      "No raw mutation",
      "No app reinstall",
      "No local deep clean",
      "pending v1.2 Final Review",
    ]),
    "s14_review_artifact",
    "S14 Review artifact records phase chain, acceptance gates, stop conditions and pending final review",
    "S14 Review artifact is missing required review evidence",
  );
}

function validateRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "S14 Review",
    "S14 P1",
    "S14 P2",
    "S14 P3",
    "owner-daily",
    "atlasctl_unified_cli.v1_2_s14_p1",
    "atlasctl_final_audit.v1_2_s14_p2",
    "stage_pass_gate_status.v1_2_s14_p3.json",
    "开发记录中文可读",
    "维护命令少而清晰",
    "所有 stage pass gate 状态可查",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "pending v1.2 Final Review",
  ];
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s14_review_records_${relativePath}`,
      `${relativePath} records S14 Review status, validator, phase chain and next phase`,
      `${relativePath} is missing S14 Review record fragments`,
      { missing },
    );
  }

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S14 Review 已完成", "pending v1.2 Final Review", "No GitHub main upload"]),
    "s14_review_quick_entry",
    "Quick entry records completed S14 Review and pending final review",
    "Quick entry does not record completed S14 Review",
  );

  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  assertCondition(
    hasAll(overview, ["S14 Review 已完成", "owner-daily", "final audit", "开发记录中文可读", "pending v1.2 Final Review"]),
    "s14_review_overview",
    "Human overview records S14 Review pass gate and pending final review",
    "Human overview is missing S14 Review pass gate",
  );

  const machineReadme = readRepoFile("机器治理/README.md");
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, "pending v1.2 Final Review"]),
    "s14_review_machine_readme",
    "Machine README records S14 Review gate and next phase",
    "Machine README is missing S14 Review gate",
  );

  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S14 Review 产物", "pending v1.2 Final Review"]),
    "s14_review_run_gate",
    "Run gate README records S14 Review artifact, validator and next phase",
    "Run gate README is missing S14 Review gate",
  );

  const evidenceReadme = readRepoFile("机器治理/证据与日志/README.md");
  assertCondition(
    hasAll(evidenceReadme, ["S14 Review 已完成", stageStatusPath, "pending v1.2 Final Review"]),
    "s14_review_evidence_readme",
    "Evidence README records S14 Review evidence files and next phase",
    "Evidence README is missing S14 Review evidence state",
  );
}

function validatePhaseValidators() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s14_review_phase_validators_deferred_until_clean_tree", "S14 P1/P2/P3 clean-tree validators will be re-run after S14 Review commit", {
      changed,
    });
    return;
  }
  const details = {};
  for (const [script, file, phaseTaskId, phaseAcceptanceId] of phaseValidators) {
    const result = parseJsonFromStdout(run("node", [`scripts/${file}`], { cwd: appRoot, timeout: 300000 }));
    details[script] = {
      status: result.status,
      task_id: result.task_id,
      acceptance_id: result.acceptance_id,
    };
    assertCondition(
      result.status === "PASS" && result.task_id === phaseTaskId && result.acceptance_id === phaseAcceptanceId,
      `s14_review_phase_gate_${script}`,
      `${script} passes with expected task and acceptance ids`,
      `${script} did not pass with expected task and acceptance ids`,
      details[script],
    );
  }
  pass("s14_review_phase_validator_chain", "S14 P1/P2/P3 validators pass in sequence", details);
}

function validateNoRawOrSecretOpenChanges() {
  const changed = getOpenChangedPaths();
  const forbiddenOpenChanges = changed.filter(
    (file) =>
      file.includes("/data/raw/") ||
      file.includes("/data/public_raw/") ||
      file.includes("/data/private_imports/") ||
      file.includes("/data/raw_encrypted/") ||
      file.endsWith(".env") ||
      file.toLowerCase().includes("secret") ||
      file.toLowerCase().includes("credential"),
  );
  const rawDiff = run("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw", "OpenAIDatabase/data/private_imports"], {
    cwd: worktreeRoot,
  }).stdout.trim();
  assertCondition(
    forbiddenOpenChanges.length === 0 && rawDiff.length === 0,
    "s14_review_no_raw_or_secret_open_changes",
    "S14 Review open diff does not modify raw, private imports, credentials or secrets",
    "S14 Review has forbidden raw/private/credential changes",
    { changed, forbiddenOpenChanges, rawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateRequiredFilesExist();
    for (const relativePath of textFiles) validateTextFile(relativePath);
    validateReviewArtifact();
    validateOwnerDailyGate();
    validateFinalAuditGate();
    validateDevelopmentRecordGate();
    validateRecords();
    validatePhaseValidators();
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
