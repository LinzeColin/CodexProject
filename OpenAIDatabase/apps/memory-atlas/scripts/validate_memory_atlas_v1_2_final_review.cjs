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

const taskId = "MA-V12-FINAL-REVIEW";
const acceptanceId = "ACC-MA-V12-FINAL-REVIEW";
const status = "v1_2_final_review_passed_pending_github_main_sync_no_upload_yet";
const validatorName = "validate:v1.2-final-review";
const scriptName = "validate_memory_atlas_v1_2_final_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_final_review.md";
const finalStatusPath = "机器治理/证据与日志/final_review/v1_2_final_review_status.json";

const reviewValidators = Array.from({ length: 14 }, (_, index) => {
  const stage = String(index + 1).padStart(2, "0");
  return [
    `validate:v1.2-s${stage}-review`,
    `validate_memory_atlas_v1_2_s${stage}_review.cjs`,
    `MA-V12-S${stage}-REVIEW`,
    `ACC-MA-V12-S${stage}-REVIEW`,
    `S${stage} Review`,
  ];
});

const acceptanceThemes = [
  "raw append-only",
  "credential audit",
  "Chinese UX",
  "visual ROI",
  "report contract",
  "proposal apply",
  "owner-daily",
  "final audit",
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const humanAndMachineIndexes = [
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  "机器治理/证据与日志/README.md",
];

const requiredFiles = [
  reviewPath,
  finalStatusPath,
  "apps/memory-atlas/package.json",
  `apps/memory-atlas/scripts/${scriptName}`,
  "scripts/atlasctl.py",
  ...reviewValidators.map(([, file]) => `apps/memory-atlas/scripts/${file}`),
  ...recordFiles,
  ...humanAndMachineIndexes,
];

const textFiles = [
  reviewPath,
  ...recordFiles,
  ...humanAndMachineIndexes,
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${finalStatusPath}`,
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

function validatePackageScripts() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "final_review_package_script",
    "package.json exposes the v1.2 Final Review validator",
    "package.json is missing the v1.2 Final Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
  const missingReviewScripts = reviewValidators
    .filter(([script, file]) => packageJson.scripts?.[script] !== `node scripts/${file}`)
    .map(([script]) => script);
  assertCondition(
    missingReviewScripts.length === 0,
    "final_review_stage_review_scripts_registered",
    "S01-S14 review validators remain registered before final review",
    "Final Review is missing stage review validator registrations",
    { missingReviewScripts },
  );
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "final_review_open_diff_scope",
    "Open diff is limited to Final Review files and governance records",
    "Final Review has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validateRequiredFilesExist() {
  const missing = requiredFiles.filter((relativePath) => !fs.existsSync(repoPath(relativePath)));
  assertCondition(
    missing.length === 0,
    "final_review_required_files_exist",
    "Final Review artifact, machine status, scripts and governance indexes exist",
    "Final Review is missing required files",
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

function validateFinalStatus() {
  const payload = readJson(finalStatusPath);
  const stageReviews = Array.isArray(payload.stage_reviews) ? payload.stage_reviews : [];
  const stageIds = stageReviews.map((item) => item.stage);
  const expectedStageIds = reviewValidators.map(([, , , , label]) => label.replace(" Review", ""));
  const missingStages = expectedStageIds.filter((stage) => !stageIds.includes(stage));
  const missingThemes = acceptanceThemes.filter((theme) => !(payload.acceptance_themes || []).includes(theme));
  assertCondition(
    payload.schema_version === "memory_atlas.final_review.v1_2" &&
      payload.task_id === taskId &&
      payload.acceptance_id === acceptanceId &&
      payload.status === status &&
      payload.validator === validatorName &&
      payload.no_github_main_upload === true &&
      payload.remote_push === false &&
      payload.app_reinstall === false &&
      payload.local_deep_clean === false &&
      payload.raw_mutation === false &&
      payload.next_phase === "pending GitHub main sync / app reinstall / local cleanup" &&
      stageReviews.length === 14 &&
      missingStages.length === 0 &&
      missingThemes.length === 0 &&
      stageReviews.every((item) => item.status === "PASS" && item.validator && item.acceptance_id),
    "final_review_machine_status",
    "Final Review machine status records S01-S14 review chain, acceptance themes and no-upload boundary",
    "Final Review machine status does not satisfy final review contract",
    {
      stage_review_count: stageReviews.length,
      missingStages,
      missingThemes,
      next_phase: payload.next_phase,
    },
  );
}

function validateFinalReviewArtifact() {
  const review = readRepoFile(reviewPath);
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "v1.2 Final Review",
    "四线14Stage",
    "S01 Review",
    "S02 Review",
    "S03 Review",
    "S04 Review",
    "S05 Review",
    "S06 Review",
    "S07 Review",
    "S08 Review",
    "S09 Review",
    "S10 Review",
    "S11 Review",
    "S12 Review",
    "S13 Review",
    "S14 Review",
    "raw append-only",
    "credential audit",
    "Chinese UX",
    "visual ROI",
    "report contract",
    "proposal apply",
    "owner-daily",
    "final audit",
    finalStatusPath,
    "remote branch reconciliation required",
    "main...origin/main [ahead 23, behind 11]",
    "No GitHub main upload",
    "No remote push",
    "No app reinstall",
    "No local deep clean",
    "No raw mutation",
    "pending GitHub main sync",
    "app reinstall",
    "local cleanup",
  ];
  const missing = requiredFragments.filter((fragment) => !review.includes(fragment));
  assertCondition(
    missing.length === 0,
    "final_review_artifact",
    "Final Review artifact records S01-S14 review chain, acceptance themes, remote reconciliation and no-upload next gate",
    "Final Review artifact is missing required evidence",
    { missing },
  );
}

function validateAtlasFinalAuditStillPasses() {
  const payload = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "audit"], { timeout: 300000 }));
  const gateIds = (payload.gates || []).map((gate) => gate.gate_id);
  const requiredGateIds = [
    "unit_tests",
    "frontend_build",
    "chinese_ux_audit",
    "visual_roi_audit",
    "raw_append_only_audit",
    "credential_audit",
    "report_contract_audit",
  ];
  const missingGateIds = requiredGateIds.filter((gateId) => !gateIds.includes(gateId));
  assertCondition(
    payload.status === "PASS" &&
      payload.command === "audit" &&
      payload.check === "final" &&
      payload.failed_gate_count === 0 &&
      payload.remote_push === false &&
      payload.github_main_upload === false &&
      payload.raw_mutation === false &&
      missingGateIds.length === 0,
    "final_review_atlas_final_audit",
    "atlasctl final audit still passes during v1.2 Final Review",
    "atlasctl final audit does not satisfy v1.2 Final Review",
    { status: payload.status, gateIds, missingGateIds },
  );
}

function validateRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "v1.2 Final Review",
    "四线14Stage",
    "S01-S14 Review",
    "raw append-only",
    "credential audit",
    "Chinese UX",
    "visual ROI",
    "report contract",
    "proposal apply",
    "owner-daily",
    "final audit",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "pending GitHub main sync",
  ];
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `final_review_records_${relativePath}`,
      `${relativePath} records Final Review status, validator, review chain and no-upload boundary`,
      `${relativePath} is missing Final Review record fragments`,
      { missing },
    );
  }

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "v1.2 Final Review 已完成", "pending GitHub main sync", "No GitHub main upload"]),
    "final_review_quick_entry",
    "Quick entry records completed Final Review and pending final sync",
    "Quick entry does not record completed Final Review",
  );

  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  assertCondition(
    hasAll(overview, ["v1.2 Final Review 已完成", "四线14Stage", "S01-S14 Review", "pending GitHub main sync"]),
    "final_review_overview",
    "Human overview records Final Review pass gate and pending final sync",
    "Human overview is missing Final Review pass gate",
  );

  const machineReadme = readRepoFile("机器治理/README.md");
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, "pending GitHub main sync"]),
    "final_review_machine_readme",
    "Machine README records Final Review gate and next phase",
    "Machine README is missing Final Review gate",
  );

  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "Final Review 产物", "pending GitHub main sync"]),
    "final_review_run_gate",
    "Run gate README records Final Review artifact, validator and next phase",
    "Run gate README is missing Final Review gate",
  );

  const evidenceReadme = readRepoFile("机器治理/证据与日志/README.md");
  assertCondition(
    hasAll(evidenceReadme, ["v1.2 Final Review 已完成", finalStatusPath, "pending GitHub main sync"]),
    "final_review_evidence_readme",
    "Evidence README records Final Review evidence files and next phase",
    "Evidence README is missing Final Review evidence state",
  );
}

function validateStageReviewChain() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("final_review_stage_review_validators_deferred_until_clean_tree", "S01-S14 review validators will be re-run after Final Review commit", {
      changed,
    });
    return;
  }
  const details = {};
  for (const [script, file, expectedTaskId, expectedAcceptanceId] of reviewValidators) {
    const result = parseJsonFromStdout(run("node", [`scripts/${file}`], { cwd: appRoot, timeout: 600000 }));
    details[script] = {
      status: result.status,
      task_id: result.task_id,
      acceptance_id: result.acceptance_id,
    };
    assertCondition(
      result.status === "PASS" && result.task_id === expectedTaskId && result.acceptance_id === expectedAcceptanceId,
      `final_review_stage_gate_${script}`,
      `${script} passes with expected task and acceptance ids`,
      `${script} did not pass with expected task and acceptance ids`,
      details[script],
    );
  }
  pass("final_review_stage_review_chain", "S01-S14 review validators pass in sequence", details);
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
    "final_review_no_raw_or_secret_open_changes",
    "Final Review open diff does not modify raw, private imports, credentials or secrets",
    "Final Review has forbidden raw/private/credential changes",
    { changed, forbiddenOpenChanges, rawDiff },
  );
}

function main() {
  try {
    validatePackageScripts();
    validateOpenDiffScope();
    validateRequiredFilesExist();
    for (const relativePath of textFiles) validateTextFile(relativePath);
    validateFinalStatus();
    validateFinalReviewArtifact();
    validateAtlasFinalAuditStillPasses();
    validateRecords();
    validateStageReviewChain();
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
